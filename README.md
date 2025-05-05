# 🎧 Convertidor FLAC a WAV para DJs 🎵

¡Convierte tus archivos de música FLAC a WAV en segundos! Especialmente diseñado para ser compatible con equipos Denon DS-1200 y otros reproductores profesionales para DJs.

![Banner del Convertidor](https://via.placeholder.com/800x200/0088ff/ffffff?text=Convertidor+FLAC+a+WAV)

## ✨ ¿Qué hace esta aplicación?

¿Tienes archivos FLAC que no puedes usar en tu equipo de DJ? ¡Esta app soluciona ese problema!

- 🔄 **Convierte** archivos FLAC a WAV ultra-compatible con equipos Denon DS-1200
- 📦 **Procesa** múltiples archivos a la vez - ¡ahorra tiempo!
- 📊 **Visualiza** las formas de onda con medición en decibeles (dB)
- 🎵 **Escucha** los archivos antes y después de convertirlos
- 🔍 **Examina** información detallada como BPM, duración y más
- 🎛️ **Interfaz** moderna y fácil de usar, incluso si no eres técnico

## 🚀 Guía Rápida de Uso

1. 📂 **Abre la aplicación** y selecciona tus archivos FLAC
2. 👁️ **Mira la forma de onda** para verificar que el audio es correcto
3. 🎧 **Escucha** el audio si quieres comprobar cómo suena
4. 🔄 **Convierte** pulsando el botón de convertir
5. ✅ **¡Listo!** Tus archivos WAV compatibles aparecerán en la misma carpeta

## 📋 Lo que necesitas para empezar

- 💻 **Python 3.6 o superior** - El "motor" que ejecuta la aplicación
- 🎬 **FFmpeg** - Una herramienta que hace la magia de la conversión
- 📚 **Algunas librerías de Python** - No te preocupes, te explicamos cómo instalarlas

## 📥 Instalación para principiantes

### En Windows:

1. 📥 **Descarga** este repositorio usando el botón verde "Code" y luego "Download ZIP"
2. 📂 **Extrae** la carpeta donde quieras
3. 🐍 **Instala Python** desde [python.org](https://www.python.org/downloads/) si no lo tienes
4. 🎬 **Descarga FFmpeg** desde [ffmpeg.org](https://ffmpeg.org/download.html) y añádelo al PATH
5. 📟 **Abre la línea de comandos** (busca "cmd" en el menú inicio)
6. 📂 **Navega a la carpeta** donde extrajiste el programa (`cd ruta\a\la\carpeta`)
7. 🧪 **Crea un entorno virtual**:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
8. 📚 **Instala las dependencias**:
   ```
   pip install -r requirements.txt
   ```
9. 🚀 **¡Ejecuta la aplicación!**:
   ```
   python main.py
   ```

### En macOS/Linux:

1. 📥 **Clona el repositorio** o descárgalo:
   ```
   git clone https://github.com/Noisk8/convert-format.git
   cd convert-format
   ```
2. 🧪 **Crea un entorno virtual**:
   ```
   python -m venv venv
   source venv/bin/activate
   ```
3. 📚 **Instala dependencias**:
   ```
   pip install -r requirements.txt
   ```
4. 🎬 **Instala FFmpeg** si no lo tienes:
   - En macOS: `brew install ffmpeg`
   - En Ubuntu/Debian: `sudo apt install ffmpeg`
5. 🚀 **¡Ejecuta la aplicación!**:
   ```
   python main.py
   ```

## 🔎 Solución de problemas comunes

- ❓ **"No puedo ver la forma de onda"** - Asegúrate de tener todas las dependencias instaladas
- ❓ **"La conversión no funciona"** - Verifica que FFmpeg esté correctamente instalado
- ❓ **"El archivo convertido no se reproduce en mi equipo DJ"** - Esta versión ha sido optimizada para máxima compatibilidad con equipos Denon DS-1200

## 💡 Consejos Pro

- 🧠 Para archivos muy largos, la aplicación podría tardar un poco más - ¡ten paciencia!
- 🚀 Selecciona varios archivos a la vez para conversión por lotes - es mucho más rápido
- 🎛️ El BPM se muestra claramente en el espectrograma para ayudarte a organizar tu música
- 📊 La visualización en decibeles (dB) te da una mejor idea de los niveles de volumen

## 🤝 ¿Quieres colaborar?

¡Tus contribuciones son bienvenidas! Así puedes ayudar:

1. 🍴 Haz un "fork" del repositorio
2. 🌿 Crea una rama para tu función (`git checkout -b nueva-funcion`)
3. 💾 Guarda tus cambios (`git commit -am 'He añadido esta función genial'`)
4. 📤 Sube tus cambios (`git push origin nueva-funcion`)
5. 📩 Crea un Pull Request para que revisemos tus cambios

## 📜 Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE) - ¡úsalo libremente en tus proyectos!

---

Hecho con ❤️ para la comunidad DJ | [Reportar un problema](https://github.com/Noisk8/convert-format/issues)