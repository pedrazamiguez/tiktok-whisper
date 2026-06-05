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

El punto de entrada principal (`main.py`) soporta dos modos de ejecución:

### 1. Modo Manual / Interactivo (Consola)
Si ejecutas el script sin argumentos o con el flag `-m`/`--manual`, te solicitará la URL de forma interactiva:

```bash
# Ejecución por defecto (interactiva)
python main.py

# O explícitamente con el flag manual
python main.py --manual
```

El script te pedirá por consola que introduzcas la URL del vídeo de TikTok:
```text
Introduce la URL del vídeo de TikTok:
```

### 2. Modo Automático (Argumentos)
Ideal para scripts, wrappers u otros agentes que deseen automatizar el proceso pasándole la URL directamente por argumento posicional:

```bash
python main.py "https://vm.tiktok.com/XXXXXXXXX/"
```

En este modo, al completarse con éxito, se imprimirá la transcripción limpia envuelta en etiquetas claras de inicio y fin:
```text
--- TRANSCRIPCION_INICIO ---
[Contenido de la transcripción...]
--- TRANSCRIPCION_FIN ---
```

---

## 🔌 Integración como Servidor MCP (Model Context Protocol)

El proyecto incluye un servidor MCP (`mcp_server.py`) listo para integrarse con clientes compatibles con MCP (como **Antigravity**, Claude Desktop, Roo-Code, etc.). Esto permite a los asistentes de IA llamar directamente a la herramienta `transcribir_tiktok` de manera estructurada.

### Configuración en Antigravity
Para registrar este servidor en tu cliente Antigravity, debes crear o editar el archivo de configuración en tu Mac:

Ruta del archivo: `~/.gemini/antigravity/mcp_config.json`

Contenido del archivo:
```json
{
  "mcpServers": {
    "tiktok-whisper": {
      "command": "/Users/<tu_usuario>/Projects/tiktok-whisper/venv/bin/python",
      "args": [
        "/Users/<tu_usuario>/Projects/tiktok-whisper/mcp_server.py"
      ]
    }
  }
}
```

---

## 💾 Guía de Restauración (En caso de formatear/resetear el Mac)

Si reseteas tu máquina, puedes volver a dejar el sistema idéntico siguiendo estos sencillos pasos:

1. **Instalar dependencias del sistema**:
   Asegúrate de reinstalar `ffmpeg` (necesario para el procesamiento de audio):
   ```bash
   brew install ffmpeg
   ```
2. **Clonar e instalar dependencias del proyecto**:
   Clona tu repositorio en la ruta `/Users/<tu_usuario>/Projects/tiktok-whisper` y recrea el entorno virtual:
   ```bash
   cd /Users/<tu_usuario>/Projects/tiktok-whisper
   python3 -m venv venv
   ./venv/bin/pip install yt-dlp openai-whisper mcp
   ```
3. **Registrar el servidor MCP**:
   Crea el directorio si no existe y escribe el archivo `mcp_config.json`:
   ```bash
   mkdir -p ~/.gemini/antigravity
   ```
   Crea el archivo `~/.gemini/antigravity/mcp_config.json` con el JSON de configuración indicado arriba.
4. **Actualizar el Agente**:
   Coloca tu archivo `planificador_viajes.agent.md` en la carpeta de agentes y asegúrate de que contiene la descripción del uso de la tool `transcribir_tiktok`.

---

## 🏗️ Arquitectura

El código está estructurado para maximizar la mantenibilidad:

- **Dominio/Casos de Uso:** `ExtractTextFromVideoUseCase` dicta las reglas de la aplicación sin conocer detalles técnicos.
- **Puertos:** Interfaces abstractas (`AudioDownloaderPort`, `SpeechToTextPort`).
- **Adaptadores:** Implementaciones específicas (`YtDlpAudioAdapter`, `WhisperSpeechToTextAdapter`) que pueden ser sustituidas fácilmente (ej. cambiar a una API de transcripción en la nube) sin afectar al núcleo del programa.

