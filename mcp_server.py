from mcp.server.fastmcp import FastMCP
import sys
import os

# Crear el servidor MCP
mcp = FastMCP("tiktok-whisper")

@mcp.tool()
def transcribir_tiktok(url: str) -> str:
    """Descarga el audio de un vídeo de TikTok y extrae su transcripción de audio a texto
    utilizando el modelo Whisper en local.

    Args:
        url: La URL del vídeo de TikTok (por ejemplo, https://vm.tiktok.com/...)
    """
    # Obtener el directorio del script de forma dinámica
    project_dir = os.path.dirname(os.path.abspath(__file__))
    original_cwd = os.getcwd()
    
    try:
        os.chdir(project_dir)
        # Aseguramos que el path del proyecto esté en sys.path para poder importar main
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
            
        from main import YtDlpAudioAdapter, WhisperSpeechToTextAdapter, ExtractTextFromVideoUseCase
        
        # 1. Instanciar adaptadores
        audio_downloader = YtDlpAudioAdapter()
        speech_to_text = WhisperSpeechToTextAdapter(model_size="base")
        
        # 2. Inyectar dependencias en el caso de uso
        use_case = ExtractTextFromVideoUseCase(
            downloader=audio_downloader, 
            transcriber=speech_to_text
        )
        
        # 3. Ejecutar
        resultado = use_case.execute(url)
        
        # Guardar en fichero
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("transcripciones", exist_ok=True)
        output_filename = os.path.join("transcripciones", f"transcripcion_{timestamp}.txt")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(resultado)
            
        return resultado
        
    except Exception as e:
        return f"ERROR: {str(e)}"
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    mcp.run()
