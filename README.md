# TikTok Whisper 🎙️

Herramienta de línea de comandos para descargar vídeos de TikTok y extraer su transcripción de audio a texto utilizando el modelo Whisper de OpenAI.

El proyecto está diseñado siguiendo los principios de la **Arquitectura Hexagonal (Puertos y Adaptadores)** para desacoplar la lógica de negocio (orquestación) de las implementaciones concretas (yt-dlp para la descarga y Whisper para la transcripción).

## 📋 Requisitos Previos

Antes de instalar las dependencias de Python, necesitas tener instalada la herramienta de procesamiento multimedia `ffmpeg` en tu sistema operativo, ya que `yt-dlp` la requiere para extraer el audio.

**En macOS (vía Homebrew):**

```bash
brew install ffmpeg
```

**En Ubuntu/Debian:**

```bash
sudo apt update && sudo apt install ffmpeg
```

**En Windows (vía winget):**

```bash
winget install ffmpeg
```

O bien descarga el instalador oficial desde [ffmpeg.org/download.html](https://ffmpeg.org/download.html) y añade la carpeta `bin` a la variable de entorno `PATH`.

## 🛠️ Instalación y Configuración

Se recomienda encarecidamente utilizar un entorno virtual para aislar las dependencias del proyecto.

1. **Clona el repositorio y accede a la carpeta:**

   ```bash
   git clone <tu-repositorio>
   cd tiktok-whisper
   ```

2. **Crea el entorno virtual:**

   ```bash
   python3 -m venv venv
   ```

3. **Activa el entorno virtual:**
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - En Windows:
     ```bash
     .\venv\Scripts\activate
     ```

4. **Instala las dependencias del proyecto:**
   ```bash
   pip install yt-dlp openai-whisper
   ```

## 🚀 Uso

Con el entorno virtual activado, ejecuta el punto de entrada principal de la aplicación:

```bash
python main.py
```

El script te pedirá por consola que introduzcas la URL del vídeo de TikTok:

```text
Introduce la URL del vídeo de TikTok:
```

El proceso consta de tres fases automatizadas:

1. Descarga del archivo de vídeo/audio.
2. Carga del modelo Whisper en memoria y procesamiento de la transcripción.
3. Limpieza de archivos temporales (MP3).

## 🏗️ Arquitectura

El código está estructurado para maximizar la mantenibilidad:

- **Dominio/Casos de Uso:** `ExtractTextFromVideoUseCase` dicta las reglas de la aplicación sin conocer detalles técnicos.
- **Puertos:** Interfaces abstractas (`AudioDownloaderPort`, `SpeechToTextPort`).
- **Adaptadores:** Implementaciones específicas (`YtDlpAudioAdapter`, `WhisperSpeechToTextAdapter`) que pueden ser sustituidas fácilmente (ej. cambiar a una API de transcripción en la nube) sin afectar al núcleo del programa.
