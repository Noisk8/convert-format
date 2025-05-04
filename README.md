# Convertidor FLAC a WAV 

Una aplicación profesional para DJs que permite convertir archivos de audio FLAC a formato WAV compatible con el equipo Denon DS-1200 y otros reproductores profesionales.

## Características principales

- Conversión optimizada de FLAC a WAV de 24 bits (alta calidad)
- Procesamiento por lotes de múltiples archivos
- Visualización de forma de onda y espectrograma
- Reproductor integrado para preescuchar los archivos
- Información detallada de los archivos de audio
- Interfaz moderna y fácil de usar

## Requisitos

- Python 3.6+
- FFmpeg (instalado en el sistema)
- Dependencias Python listadas en requirements.txt

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/Noisk8/convert-format.git
   cd convert-format
   ```

2. Crear un entorno virtual (recomendado):
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Asegurarse de tener FFmpeg instalado:
   - En Ubuntu/Debian: `sudo apt install ffmpeg`
   - En macOS: `brew install ffmpeg`
   - En Windows: Descargar desde [ffmpeg.org](https://ffmpeg.org/download.html) y añadir al PATH

## Uso

Ejecutar la aplicación:
```
python main.py
```

### Flujo de trabajo típico:
1. Seleccionar archivos FLAC desde el panel izquierdo
2. Previsualizar la forma de onda del archivo
3. Escuchar el archivo original
4. Iniciar la conversión individual o por lotes
5. Comprobar los archivos WAV generados

## Arquitectura del software

El proyecto sigue una arquitectura modular con los siguientes componentes principales:

- `main.py`: Ventana principal y punto de entrada
- `audio_converter.py`: Lógica para convertir archivos de audio
- `audio_player.py`: Reproductor integrado
- `waveform.py`: Generación y visualización de formas de onda
- `spectrogram.py`: Visualización espectral
- `ui_components.py`: Componentes de interfaz reutilizables
- `platform_utils.py`: Utilidades específicas de la plataforma
- `style.qss`: Estilos de la interfaz

## Contribuciones

Las contribuciones son bienvenidas. Por favor, siga estos pasos:

1. Hacer fork del repositorio
2. Crear una rama para su característica (`git checkout -b feature/nueva-caracteristica`)
3. Hacer commit de sus cambios (`git commit -am 'Añadir nueva característica'`)
4. Hacer push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear un Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).