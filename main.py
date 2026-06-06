import os
import uuid
import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import yt_dlp
import whisper

# ==========================================
# 1. DOMINIO Y PUERTOS (Hexágono Interior)
# ==========================================

@dataclass
class AudioFile:
    path: str

class SubtitleExtractorPort(ABC):
    """Puerto para intentar extraer subtítulos directamente."""
    @abstractmethod
    def extract_subtitles(self, video_url: str) -> str | None:
        pass

class AudioDownloaderPort(ABC):
    """Puerto para descargar el audio de una URL."""
    @abstractmethod
    def download_audio(self, video_url: str) -> AudioFile:
        pass

class SpeechToTextPort(ABC):
    """Puerto para convertir un archivo de audio a texto."""
    @abstractmethod
    def transcribe(self, audio: AudioFile) -> str:
        pass

# ==========================================
# 2. CASOS DE USO (Lógica de negocio)
# ==========================================

class ExtractTextFromVideoUseCase:
    """Caso de uso orquestador con patrón de resiliencia (Subtítulos -> Fallback a IA)."""
    
    def __init__(
        self, 
        subtitle_extractor: SubtitleExtractorPort,
        downloader: AudioDownloaderPort, 
        transcriber: SpeechToTextPort
    ):
        self.subtitle_extractor = subtitle_extractor
        self.downloader = downloader
        self.transcriber = transcriber

    def execute(self, video_url: str) -> str:
        # FASE 1: Intentar la vía rápida (Extraer subtítulos nativos)
        print("[Use Case] Fase 1: Intentando extraer subtítulos nativos...")
        subtitles = self.subtitle_extractor.extract_subtitles(video_url)
        
        if subtitles:
            print("[Use Case] Éxito: Subtítulos nativos encontrados. Omitiendo proceso de IA.")
            return subtitles
            
        print("[Use Case] Subtítulos no disponibles o inaccesibles. Iniciando Fase 2 (Fallback a Whisper)...")
        
        # FASE 2: Vía pesada (Descargar audio y transcribir con IA)
        audio_file = None
        try:
            print("[Use Case] Iniciando descarga del audio...")
            audio_file = self.downloader.download_audio(video_url)
            
            print("[Use Case] Audio descargado. Iniciando transcripción con Whisper...")
            transcription = self.transcriber.transcribe(audio_file)
            
            print("[Use Case] Proceso completado con éxito.")
            return transcription
            
        except Exception as e:
            raise RuntimeError(f"Error procesando el vídeo: {str(e)}")
            
        finally:
            if audio_file and os.path.exists(audio_file.path):
                os.remove(audio_file.path)
                print(f"[Cleanup] Archivo temporal {audio_file.path} eliminado.")

# ==========================================
# 3. ADAPTADORES (Hexágono Exterior)
# ==========================================

class YtDlpSubtitleAdapter(SubtitleExtractorPort):
    """Adaptador para extraer subtítulos usando yt-dlp."""
    
    def extract_subtitles(self, video_url: str) -> str | None:
        temp_filename = f"temp_subs_{uuid.uuid4().hex}"
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            # Añadimos los idiomas más probables para los vídeos que estás procesando
            'subtitleslangs': ['es', 'en', 'zh', 'zh-Hans', 'zh-Hant'],
            'outtmpl': temp_filename,
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)
                
            # yt-dlp añade extensiones como .en.vtt al final del nombre
            downloaded_subs = [f for f in os.listdir('.') if f.startswith(temp_filename) and f.endswith('.vtt')]
            
            if not downloaded_subs:
                return None
                
            # Procesamos el primer archivo de subtítulos encontrado
            sub_file = downloaded_subs[0]
            with open(sub_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            os.remove(sub_file)
            
            # Parseo básico de VTT a texto plano para eliminar marcas de tiempo
            lines = content.split('\n')
            clean_text = []
            for line in lines:
                stripped = line.strip()
                # Ignorar líneas vacías, marcas de tiempo y cabeceras VTT
                if not stripped or '-->' in stripped or stripped.startswith('WEBVTT') or ':' in stripped[:10]:
                    continue
                clean_text.append(stripped)
                
            final_text = " ".join(clean_text)
            return final_text if final_text else None
            
        except Exception as e:
            print(f"[Adapter Warning] Error al buscar subtítulos nativos: {str(e)}")
            return None

class YtDlpAudioAdapter(AudioDownloaderPort):
    """Adaptador que utiliza yt-dlp para extraer el audio."""
    
    def download_audio(self, video_url: str) -> AudioFile:
        temp_filename = f"temp_audio_{uuid.uuid4().hex}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': temp_filename,
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            expected_output_file = f"{temp_filename}.mp3"
            
            if not os.path.exists(expected_output_file):
                raise FileNotFoundError("El archivo de audio no se generó correctamente.")
                
            return AudioFile(path=expected_output_file)
            
        except Exception as e:
            raise Exception(f"Fallo al descargar audio con yt-dlp: {str(e)}")

class WhisperSpeechToTextAdapter(SpeechToTextPort):
    """Adaptador que utiliza el modelo Whisper de OpenAI en local."""
    
    def __init__(self, model_size: str = "base"):
        print(f"[Whisper] Cargando modelo en memoria (tamaño: {model_size})...")
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio: AudioFile) -> str:
        try:
            result = self.model.transcribe(audio.path, fp16=False)
            return result["text"].strip()
        except Exception as e:
            raise Exception(f"Fallo durante la transcripción con Whisper: {str(e)}")

# ==========================================
# 4. ENTRY POINT (Inyección de dependencias)
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Extrae transcripciones de TikTok.")
    parser.add_argument("url", type=str, nargs="?", help="La URL del vídeo de TikTok (opcional)")
    parser.add_argument("-m", "--manual", action="store_true", help="Activar modo interactivo/manual para introducir la URL por consola")
    args = parser.parse_args()
    
    # Decidir el origen de la URL
    tiktok_url = args.url
    if args.manual or not tiktok_url:
        try:
            tiktok_url = input("Introduce la URL del vídeo de TikTok: ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada por el usuario.", file=sys.stderr)
            sys.exit(1)
            
    if not tiktok_url or tiktok_url.strip() == "":
        print("ERROR_CRITICO: No se proporcionó ninguna URL de TikTok.", file=sys.stderr)
        sys.exit(1)
        
    # 1. Instanciar adaptadores
    subtitle_extractor = YtDlpSubtitleAdapter()
    audio_downloader = YtDlpAudioAdapter()
    speech_to_text = WhisperSpeechToTextAdapter(model_size="base")
    
    # 2. Inyectar dependencias en el caso de uso
    use_case = ExtractTextFromVideoUseCase(
        subtitle_extractor=subtitle_extractor,
        downloader=audio_downloader, 
        transcriber=speech_to_text
    )
    
    # 3. Ejecutar
    try:
        resultado = use_case.execute(tiktok_url)
        
        # Guardar en fichero
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("transcripciones", exist_ok=True)
        output_filename = os.path.join("transcripciones", f"transcripcion_{timestamp}.txt")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(resultado)
            
        print(f"--- TRANSCRIPCION_INICIO ---\n{resultado}\n--- TRANSCRIPCION_FIN ---")
        
    except Exception as e:
        print(f"ERROR_CRITICO: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

