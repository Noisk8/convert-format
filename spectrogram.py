import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtCore import pyqtSignal, QObject, QThread, pyqtSlot
import soundfile as sf
import os

class SpectrogramWorker(QThread):
    """Clase trabajadora para generar espectrogramas en un hilo separado."""
    
    finished = pyqtSignal(object)  # Canvas o None en caso de error
    error = pyqtSignal(str)
    
    def __init__(self, file_path, n_fft=2048, hop_length=1024, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.n_fft = n_fft
        self.hop_length = hop_length
        
    def run(self):
        try:
            # Cargar el archivo de audio de manera eficiente usando una muestra reducida
            # Reducir la tasa de muestreo para acelerar el procesamiento
            y, sr = librosa.load(self.file_path, sr=22050, duration=30, res_type='kaiser_fast')
            
            # Crear la figura con un tamaño más pequeño para acelerar el rendering
            fig, ax = plt.subplots(figsize=(8, 3), dpi=80)
            
            # Usar un spectrograma de menor resolución para acelerar el cálculo
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=self.n_fft, 
                                                          hop_length=self.hop_length)), 
                                      ref=np.max)
            
            # Mostrar el espectrograma con menos detalles para mayor velocidad
            img = librosa.display.specshow(D, y_axis='log', x_axis='time', sr=sr, 
                                         hop_length=self.hop_length, ax=ax)
            
            # Barra de color simplificada
            fig.colorbar(img, ax=ax, format='%+2.0f dB')
            
            # Título simplificado
            ax.set_title(os.path.basename(self.file_path))
            
            # Crear el canvas para Qt
            canvas = FigureCanvasQTAgg(fig)
            
            # Emitir el canvas
            self.finished.emit(canvas)
            
        except Exception as e:
            self.error.emit(str(e))


class SpectrogramGenerator(QObject):
    """Clase para generar espectrogramas a partir de archivos de audio."""
    
    generation_complete = pyqtSignal(object)  # emite el canvas con el espectrograma
    generation_error = pyqtSignal(str)  # emite mensaje de error
    
    def __init__(self):
        super().__init__()
        self.worker = None
    
    def generate_spectrogram(self, file_path, n_fft=2048, hop_length=1024):
        """
        Genera un espectrograma a partir de un archivo de audio de manera asíncrona.
        
        Args:
            file_path: Ruta al archivo de audio
            n_fft: Tamaño de la ventana FFT
            hop_length: Número de muestras entre tramas sucesivas
        """
        # Cancelar el trabajador anterior si existe
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        # Crear y configurar el nuevo trabajador
        self.worker = SpectrogramWorker(file_path, n_fft, hop_length)
        self.worker.finished.connect(self.generation_complete.emit)
        self.worker.error.connect(self.generation_error.emit)
        
        # Iniciar el hilo
        self.worker.start()
    
    def get_audio_info(self, file_path):
        """
        Obtiene información básica del archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            Un diccionario con información del audio
        """
        try:
            # Cargar metadatos sin cargar todo el audio
            info = sf.info(file_path)
            
            # Calcular duración en formato legible
            duration_seconds = info.duration
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            
            # Recopilar información
            audio_info = {
                "samplerate": info.samplerate,
                "channels": info.channels,
                "format": info.format,
                "subtype": info.subtype,
                "duration": f"{minutes}:{seconds:02d}",
                "duration_seconds": duration_seconds,
                "bit_depth": getattr(info, "bits_per_sample", "N/A")
            }
            
            return audio_info
            
        except Exception as e:
            return {"error": str(e)}


class SpectrogramCanvas(FigureCanvasQTAgg):
    """Widget personalizado para mostrar el espectrograma en la interfaz Qt."""
    
    def __init__(self, parent=None, width=8, height=3, dpi=80):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Configurar el gráfico para que sea ligero
        self.fig.tight_layout()
        
    def update_spectrogram(self, audio_path, n_fft=2048, hop_length=1024):
        """
        Actualiza el espectrograma con un nuevo archivo de audio.
        
        Args:
            audio_path: Ruta al archivo de audio
            n_fft: Tamaño de la ventana FFT
            hop_length: Número de muestras entre tramas sucesivas
        """
        # Crear un generador y conectar su señal a esta instancia
        self.generator = SpectrogramGenerator()
        self.generator.generation_complete.connect(self._update_from_canvas)
        self.generator.generation_error.connect(self._handle_error)
        
        # Generar espectrograma en un hilo separado
        self.generator.generate_spectrogram(audio_path, n_fft, hop_length)
        
        return True
    
    @pyqtSlot(object)
    def _update_from_canvas(self, canvas):
        """Actualiza este canvas con la figura de otro canvas."""
        if canvas:
            # Transferir la figura del canvas generado a este canvas
            self.fig.clf()
            for ax in canvas.figure.get_axes():
                self.fig.add_axes(ax)
            self.fig.canvas.draw_idle()
    
    @pyqtSlot(str)
    def _handle_error(self, error_message):
        """Maneja errores de generación."""
        print(f"Error al generar el espectrograma: {error_message}")
        # Limpiar el canvas actual
        self.ax.clear()
        self.ax.set_title("Error al generar el espectrograma")
        self.fig.canvas.draw_idle()
