import os
import uuid
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
    """Caso de uso orquestador que coordina la descarga y transcripción."""
    
    def __init__(self, downloader: AudioDownloaderPort, transcriber: SpeechToTextPort):
        self.downloader = downloader
        self.transcriber = transcriber

    def execute(self, video_url: str) -> str:
        audio_file = None
        try:
            print("[Use Case] Iniciando descarga del audio...")
            audio_file = self.downloader.download_audio(video_url)
            
            print("[Use Case] Audio descargado. Iniciando transcripción...")
            transcription = self.transcriber.transcribe(audio_file)
            
            print("[Use Case] Proceso completado con éxito.")
            return transcription
            
        except Exception as e:
            raise RuntimeError(f"Error procesando el vídeo: {str(e)}")
            
        finally:
            # Clean Code: Siempre limpiamos los archivos temporales
            if audio_file and os.path.exists(audio_file.path):
                os.remove(audio_file.path)
                print(f"[Cleanup] Archivo temporal {audio_file.path} eliminado.")

# ==========================================
# 3. ADAPTADORES (Hexágono Exterior)
# ==========================================

class YtDlpAudioAdapter(AudioDownloaderPort):
    """Adaptador que utiliza yt-dlp para descargar extraer el audio."""
    
    def download_audio(self, video_url: str) -> AudioFile:
        # Generamos un nombre único para evitar colisiones si se ejecuta en paralelo
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
            
            # yt-dlp añade automáticamente la extensión definida en el postprocessor
            expected_output_file = f"{temp_filename}.mp3"
            
            if not os.path.exists(expected_output_file):
                raise FileNotFoundError("El archivo de audio no se generó correctamente.")
                
            return AudioFile(path=expected_output_file)
            
        except Exception as e:
            raise Exception(f"Fallo al descargar audio con yt-dlp: {str(e)}")

class WhisperSpeechToTextAdapter(SpeechToTextPort):
    """Adaptador que utiliza el modelo Whisper de OpenAI en local."""
    
    def __init__(self, model_size: str = "base"):
        # Tamaños disponibles: tiny, base, small, medium, large
        print(f"[Whisper] Cargando modelo en memoria (tamaño: {model_size})...")
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio: AudioFile) -> str:
        try:
            # fp16=False evita warnings si lo ejecutas en una CPU sin soporte
            result = self.model.transcribe(audio.path, fp16=False)
            return result["text"].strip()
        except Exception as e:
            raise Exception(f"Fallo durante la transcripción con Whisper: {str(e)}")

# ==========================================
# 4. ENTRY POINT (Inyección de dependencias)
# ==========================================

def main():
    # URL de ejemplo (puedes cambiarla por el TikTok que estés viendo)
    tiktok_url = input("Introduce la URL del vídeo de TikTok: ")
    
    # 1. Instanciar adaptadores
    audio_downloader = YtDlpAudioAdapter()
    speech_to_text = WhisperSpeechToTextAdapter(model_size="base")
    
    # 2. Inyectar dependencias en el caso de uso
    use_case = ExtractTextFromVideoUseCase(
        downloader=audio_downloader, 
        transcriber=speech_to_text
    )
    
    # 3. Ejecutar
    try:
        print("\n--- INICIANDO PROCESAMIENTO ---")
        resultado = use_case.execute(tiktok_url)
        print("\n--- TRANSCRIPCIÓN ---")
        print(resultado)
        print("---------------------\n")

        # Guardar la transcripción en un fichero de texto
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"transcripcion_{timestamp}.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(resultado)
        print(f"[Output] Transcripción guardada en: {output_filename}")
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")

if __name__ == "__main__":
    main()
