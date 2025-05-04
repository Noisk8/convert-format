#!/usr/bin/env python3
'''
Módulo principal de la aplicación Convertidor FLAC a WAV para Denon DS-1200.
Este archivo contiene la clase MainWindow que inicializa todos los componentes
y coordina la interacción entre ellos para proporcionar una interfaz gráfica
completa para la conversión de archivos de audio.
'''

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QMessageBox, QSplitter, QFileDialog,
                           QTabWidget, QLabel)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

# Importar módulos propios
from audio_converter import AudioConverter   # Maneja la conversión de audio
from audio_player import AudioPlayer         # Reproduce archivos de audio
from waveform import WaveformGenerator, WaveformWidget  # Visualización de forma de onda
from ui_components import (FileListWidget, PlayerControls, AudioInfoWidget, 
                         StatusBar)          # Componentes reutilizables de UI

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self):
        """Inicializa la ventana principal y sus componentes."""
        super().__init__()
        
        # Configurar la ventana
        self.setWindowTitle("Convertidor FLAC a WAV para Denon DS-1200")
        self.setMinimumSize(900, 700)  # Tamaño mínimo para buena usabilidad
        
        # Inicializar componentes
        self.init_components()
        
        # Crear y configurar la interfaz
        self.init_ui()
        
        # Conectar señales y slots
        self.connect_signals()
        
        # Mostrar mensaje de bienvenida
        self.status_bar.set_status("listo", "Bienvenido al Convertidor FLAC a WAV para Denon DS-1200")
        
        # Verificar si ffmpeg está instalado
        self.check_ffmpeg()
    
    def init_components(self):
        """Inicializa los componentes de la aplicación."""
        # Componentes principales
        self.audio_converter = AudioConverter()  # Motor de conversión de audio
        self.audio_player = AudioPlayer()        # Reproductor de audio
        self.waveform_generator = WaveformGenerator()  # Generador de forma de onda
        
        # Componentes de la interfaz
        self.file_list_widget = FileListWidget()  # Lista de archivos
        self.player_controls = PlayerControls()   # Controles de reproducción
        self.audio_info_widget = AudioInfoWidget()  # Información del audio
        self.waveform_widget = WaveformWidget()     # Visualización de forma de onda
        self.status_bar = StatusBar()               # Barra de estado
        
        # Variables de estado
        self.current_file = None      # Archivo actualmente seleccionado
        self.converted_file = None    # Último archivo convertido
    
    def init_ui(self):
        """Configura la interfaz de usuario."""
        # Widget central
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter principal (divide la lista de archivos del resto)
        # Permite al usuario ajustar el tamaño de cada panel
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo (lista de archivos)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(self.file_list_widget)
        left_panel.setLayout(left_layout)
        
        # Panel derecho (reproductor, forma de onda, información)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Pestañas para visualización
        tabs = QTabWidget()
        
        # Pestaña de forma de onda
        waveform_tab = QWidget()
        waveform_layout = QVBoxLayout(waveform_tab)
        waveform_layout.addWidget(self.waveform_widget)
        waveform_tab.setLayout(waveform_layout)
        
        # Pestaña de información
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.addWidget(self.audio_info_widget)
        info_tab.setLayout(info_layout)
        
        # Añadir las pestañas
        tabs.addTab(waveform_tab, "Forma de onda")
        tabs.addTab(info_tab, "Información")
        
        # Añadir el reproductor y las pestañas al panel derecho
        right_layout.addWidget(self.player_controls)
        right_layout.addWidget(tabs)
        right_panel.setLayout(right_layout)
        
        # Añadir paneles al splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # Establecer tamaños iniciales (40% para la lista, 60% para el resto)
        main_splitter.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)])
        
        # Añadir el splitter al layout principal
        main_layout.addWidget(main_splitter)
        
        # Establecer el widget central
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Añadir barra de estado
        self.setStatusBar(self.status_bar)
    
    def connect_signals(self):
        """Conecta las señales entre los componentes."""
        # Conexiones para la lista de archivos
        self.file_list_widget.file_selected.connect(self.on_file_selected)
        self.file_list_widget.batch_convert_requested.connect(self.on_batch_convert_requested)
        
        # Conexiones para el conversor de audio
        self.audio_converter.conversion_started.connect(self.on_conversion_started)
        self.audio_converter.conversion_progress.connect(self.on_conversion_progress)
        self.audio_converter.conversion_completed.connect(self.on_conversion_completed)
        self.audio_converter.conversion_error.connect(self.on_conversion_error)
        self.audio_converter.batch_completed.connect(self.on_batch_completed)
        
        # Conexiones para el reproductor de audio
        self.audio_player.position_changed.connect(self.player_controls.update_position)
        self.audio_player.duration_changed.connect(self.player_controls.update_duration)
        
        # Conexiones para los controles del reproductor
        self.player_controls.play_requested.connect(self.audio_player.play)
        self.player_controls.pause_requested.connect(self.audio_player.pause)
        self.player_controls.stop_requested.connect(self.audio_player.stop)
        self.player_controls.seek_requested.connect(self.audio_player.seek)
        self.player_controls.volume_changed.connect(self.audio_player.set_volume)
        
        # Conexiones para el generador de forma de onda
        self.waveform_generator.waveform_generated.connect(self.on_waveform_generated)
        self.waveform_generator.waveform_error.connect(self.on_waveform_error)
    
    def check_ffmpeg(self):
        """Verifica si ffmpeg está instalado."""
        if not self.audio_converter.check_ffmpeg():
            QMessageBox.critical(
                self,
                "Error - FFmpeg no encontrado",
                "No se ha encontrado FFmpeg en el sistema. Por favor, instálelo para poder usar esta aplicación."
            )
    
    def on_file_selected(self, file_path):
        """
        Maneja el evento de selección de un archivo en la lista.
        
        Args:
            file_path: Ruta al archivo seleccionado
        """
        # Actualizar el archivo actual
        self.current_file = file_path
        
        # Mostrar estado
        self.status_bar.set_status("cargando", f"Cargando {os.path.basename(file_path)}...")
        
        # Cargar el archivo en el reproductor
        if self.audio_player.load_file(file_path):
            # Actualizar información del audio
            try:
                import soundfile as sf
                info = sf.info(file_path)
                
                # Calcular duración en formato legible
                duration_seconds = info.duration
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                
                # Recopilar información básica del archivo
                audio_info = {
                    "file_name": os.path.basename(file_path),
                    "samplerate": info.samplerate,
                    "channels": info.channels,
                    "format": info.format,
                    "subtype": info.subtype,
                    "duration": f"{minutes}:{seconds:02d}",
                    "duration_seconds": duration_seconds,
                    "bit_depth": getattr(info, "bits_per_sample", "N/A")
                }
                
                # Mostrar información en el widget
                self.audio_info_widget.update_info(audio_info)
                
                # Generar y mostrar forma de onda
                self.waveform_widget.update_waveform(file_path)
                
                # Mostrar estado
                self.status_bar.set_status("listo", f"Archivo cargado: {os.path.basename(file_path)}")
            except Exception as e:
                self.status_bar.set_status("error", f"Error al cargar el archivo: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Error al cargar archivo",
                    f"No se pudo obtener información del archivo:\n{str(e)}"
                )
        else:
            self.status_bar.set_status("error", f"No se pudo cargar el archivo {os.path.basename(file_path)}")
    
    def on_batch_convert_requested(self, file_list, output_dir):
        """
        Maneja el evento de solicitud de conversión por lotes.
        
        Args:
            file_list: Lista de rutas de archivo a convertir
            output_dir: Directorio de salida para los archivos convertidos
        """
        if not file_list:
            return
            
        # Mostrar estado
        self.status_bar.set_status("convirtiendo", f"Iniciando conversión por lotes de {len(file_list)} archivos...")
        
        # Iniciar conversión por lotes
        self.audio_converter.convert_batch(file_list, output_dir)
    
    def on_conversion_started(self, file_path):
        """
        Maneja el evento de inicio de conversión de un archivo.
        
        Args:
            file_path: Ruta al archivo en conversión
        """
        # Mostrar estado
        self.status_bar.set_status("convirtiendo", f"Convirtiendo {os.path.basename(file_path)}...")
        
        # Actualizar la UI según sea necesario
        self.file_list_widget.set_file_status(file_path, "convirtiendo")
    
    def on_conversion_progress(self, file_path, progress):
        """
        Maneja el evento de progreso de conversión.
        
        Args:
            file_path: Ruta al archivo en conversión
            progress: Porcentaje de progreso (0-100)
        """
        # Actualizar barra de estado con el progreso
        self.status_bar.set_status(
            "convirtiendo", 
            f"Convirtiendo {os.path.basename(file_path)}... {progress}%"
        )
        self.status_bar.set_progress(progress)
    
    def on_conversion_completed(self, original_file, converted_file):
        """
        Maneja el evento de finalización de conversión de un archivo.
        
        Args:
            original_file: Ruta al archivo original
            converted_file: Ruta al archivo convertido
        """
        # Actualizar estado
        self.status_bar.set_status("completado", f"Conversión completada: {os.path.basename(converted_file)}")
        self.status_bar.set_progress(100)
        
        # Actualizar UI
        self.file_list_widget.set_file_status(original_file, "convertido")
        
        # Guardar referencia al archivo convertido
        self.converted_file = converted_file
        
        # Si el archivo convertido es el archivo actualmente seleccionado, actualizarlo
        if self.current_file == original_file:
            # Mostrar mensaje de confirmación
            reply = QMessageBox.question(
                self,
                "Conversión completada",
                f"El archivo ha sido convertido exitosamente a WAV.\n"
                f"Ruta: {converted_file}\n\n"
                f"¿Desea cargar el archivo convertido?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.No:
                return
                
            # Cargar el archivo convertido
            if self.audio_player.load_file(converted_file):
                # Actualizar la forma de onda y la información
                self.waveform_widget.update_waveform(converted_file)
                
                # Obtener información del archivo convertido
                try:
                    import soundfile as sf
                    info = sf.info(converted_file)
                    
                    # Calcular duración en formato legible
                    duration_seconds = info.duration
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    
                    # Recopilar información
                    audio_info = {
                        "file_name": os.path.basename(converted_file),
                        "samplerate": info.samplerate,
                        "channels": info.channels,
                        "format": info.format,
                        "subtype": info.subtype,
                        "duration": f"{minutes}:{seconds:02d}",
                        "duration_seconds": duration_seconds,
                        "bit_depth": getattr(info, "bits_per_sample", "N/A")
                    }
                    
                    self.audio_info_widget.update_info(audio_info)
                except Exception as e:
                    print(f"Error al obtener información del audio convertido: {e}")
                
                # Reproducir el archivo
                self.audio_player.play()
    
    def on_conversion_error(self, file_path, error_message):
        """
        Maneja el evento de error de conversión.
        
        Args:
            file_path: Ruta al archivo en conversión
            error_message: Mensaje de error
        """
        # Actualizar estado
        self.status_bar.set_status("error", f"Error al convertir {os.path.basename(file_path)}")
        
        # Mostrar mensaje de error
        QMessageBox.warning(
            self,
            "Error de conversión",
            f"Error al convertir {os.path.basename(file_path)}:\n{error_message}"
        )
    
    def on_batch_completed(self):
        """Maneja el evento de finalización de conversión por lotes."""
        # Actualizar estado
        self.status_bar.set_status("completado", "Conversión por lotes completada")
        
        # Mostrar mensaje de confirmación
        QMessageBox.information(
            self,
            "Conversión completada",
            "La conversión por lotes ha sido completada."
        )
    
    def on_waveform_generated(self, file_path):
        """
        Maneja el evento de generación de forma de onda.
        
        Args:
            file_path: Ruta al archivo para el que se ha generado la forma de onda
        """
        # Actualizar estado
        self.status_bar.set_status("listo", "Forma de onda generada")
    
    def on_waveform_error(self, error_message):
        """
        Maneja el evento de error de generación de forma de onda.
        
        Args:
            error_message: Mensaje de error
        """
        # Actualizar estado
        self.status_bar.set_status("error", "Error al generar la forma de onda")
        
        # Mostrar mensaje de error
        QMessageBox.warning(
            self,
            "Error de forma de onda",
            f"Error al generar la forma de onda:\n{error_message}"
        )
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la aplicación."""
        # Detener la reproducción si está activa
        if self.audio_player.is_playing():
            self.audio_player.stop()
            
        # Cancelar conversiones en progreso
        self.audio_converter.cancel_conversions()
        
        # Continuar con el cierre de la aplicación
        event.accept()


# Punto de entrada de la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Cargar y aplicar el estilo futurista global
    style_file = open(os.path.join(os.path.dirname(__file__), "style.qss"), "r")
    style = style_file.read()
    style_file.close()
    app.setStyleSheet(style)
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Iniciar el bucle de eventos de la aplicación
    sys.exit(app.exec_())
