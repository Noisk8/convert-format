import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import os

# Hacer librosa opcional
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

class WaveformWorker(QThread):
    """Trabajador para generar la forma de onda en un hilo separado."""
    
    finished = pyqtSignal(object, object)  # Emite (datos de forma de onda, tasa de muestreo)
    error = pyqtSignal(str)
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
    def run(self):
        try:
            # Usar soundfile en lugar de librosa para cargar audio (mucho más rápido)
            data, sr = sf.read(self.file_path, dtype='float32')
            
            # Si es estéreo, convertir a mono para la visualización
            if len(data.shape) > 1 and data.shape[1] > 1:
                data = np.mean(data, axis=1)
                
            # Reducir datos para visualización más rápida (submuestreo)
            # Solo tomar 1 de cada N muestras para acelerar el rendering
            if len(data) > 100000:
                # Calcular factor de reducción más agresivo para archivos grandes
                target_samples = 10000  # Número ideal de muestras para visualización fluida
                reduction_factor = max(1, len(data) // target_samples)
                data = data[::reduction_factor]
                sr = sr // reduction_factor
            
            self.finished.emit(data, sr)
        except Exception as e:
            self.error.emit(str(e))


class WaveformGenerator(QObject):
    """Clase para generar la forma de onda del audio."""
    
    generation_complete = pyqtSignal(object, object)  # Emite (datos de forma de onda, tasa de muestreo)
    generation_error = pyqtSignal(str)
    waveform_generated = pyqtSignal(object, object)  # Señal que será usada por la UI
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.generation_complete.connect(self.waveform_generated.emit)
    
    def generate_waveform(self, file_path):
        """
        Genera la forma de onda del archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio
        """
        # Cancelar el trabajador anterior si existe
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        # Crear y configurar el nuevo trabajador
        self.worker = WaveformWorker(file_path)
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


class WaveformCanvas(FigureCanvasQTAgg):
    """Widget personalizado para mostrar la forma de onda en la interfaz Qt."""
    
    def __init__(self, parent=None):
        # Crear figura con un tamaño adecuado
        self.fig, self.ax = plt.subplots(figsize=(8, 2), dpi=100, facecolor='#212121')
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Variables de estado
        self.audio_data = None
        self.sr = None
        self.current_position = 0
        self.position_line = None
        self.audio_path = None
        
        # Configurar estilo futurista para el gráfico
        self.ax.set_facecolor('#212121')  # Fondo oscuro moderno
        self.ax.tick_params(axis='x', colors='#00FFFF')  # Marcas de eje X en cian
        self.ax.tick_params(axis='y', colors='#00FFFF')  # Marcas de eje Y en cian
        self.ax.spines['bottom'].set_color('#444444')    # Bordes del gráfico en gris oscuro
        self.ax.spines['top'].set_color('#444444')
        self.ax.spines['left'].set_color('#444444')
        self.ax.spines['right'].set_color('#444444')
        
        # Configurar ejes
        self.ax.set_xlabel('Tiempo (s)', color='#00FFFF')
        self.ax.set_ylabel('Amplitud', color='#00FFFF')
        self.ax.grid(True, alpha=0.2, color='#00FFFF')
        
        self.fig.tight_layout()
    
    def update_waveform(self, audio_path):
        """
        Actualiza la forma de onda con un nuevo archivo de audio.
        
        Args:
            audio_path: Ruta al archivo de audio
        """
        # Guardar la ruta del audio para la detección de BPM
        self.audio_path = audio_path
        
        # Cancelar generación previa si existe
        if hasattr(self, 'generator') and self.generator:
            if hasattr(self.generator, 'worker') and self.generator.worker and self.generator.worker.isRunning():
                self.generator.worker.terminate()
                self.generator.worker.wait()
        
        # Inicializar el generador si no existe
        if not hasattr(self, 'generator') or not self.generator:
            self.generator = WaveformGenerator()
            self.generator.generation_complete.connect(self._update_plot)
            self.generator.generation_error.connect(self._handle_error)
        
        # Generar la forma de onda
        self.generator.generate_waveform(audio_path)
        
        # Limpiar la línea de posición
        self.current_position = 0
        if self.position_line:
            self.position_line.remove()
            self.position_line = None
        
        # Actualizar título
        self.ax.set_title(os.path.basename(audio_path), color='#00FFFF')
        self.draw()
        
        return True
    
    @pyqtSlot(object, object)
    def _update_plot(self, audio_data, sr):
        """Actualiza el gráfico con los datos de audio."""
        # Guardar tasa de muestreo para cálculos posteriores
        self.sr = sr
        
        # Duración total en segundos
        duration = len(audio_data) / sr
        
        # Limpiar el gráfico anterior
        self.ax.clear()
        
        # Convertir a decibeles para el eje Y
        # Añadimos pequeño valor para evitar log(0)
        eps = 1e-10
        audio_data_abs = np.abs(audio_data) + eps
        # Convertir a dB: 20 * log10(|x|)
        audio_db = 20 * np.log10(audio_data_abs / np.max(audio_data_abs))
        
        # Crear array de tiempo
        time = np.linspace(0, duration, len(audio_data))
        
        # Usar LineCollection para renderizado más eficiente
        points = np.array([time, audio_db]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # Configurar escala de color (más eficiente con menos puntos en el gradiente)
        norm = plt.Normalize(-60, 0)  # Rango típico para dB: -60dB a 0dB
        cmap = LinearSegmentedColormap.from_list("", ["#0088FF", "#00FFFF"])
        lc = LineCollection(segments, cmap=cmap, norm=norm)
        lc.set_array(audio_db)
        lc.set_linewidth(1.5)
        
        # Añadir al gráfico
        line = self.ax.add_collection(lc)
        
        # Configurar límites
        self.ax.set_xlim(0, duration)
        self.ax.set_ylim(-60, 5)  # Rango de dB con pequeño margen positivo
        
        # Etiquetas de los ejes
        self.ax.set_ylabel("Amplitud (dB)", color='#00FFFF', fontsize=10)
        self.ax.set_xlabel("Tiempo (s)", color='#00FFFF', fontsize=10)
        
        # Añadir línea de posición actual
        self.position_line = self.ax.axvline(x=0, color='#FF00FF', linewidth=1.0)
        
        # Obtener BPM para mostrar marcadores de tiempo
        bpm = get_song_bpm(self.audio_path)
        
        # Simplificar las marcas de tiempo para mejorar el rendimiento
        if duration > 60:  # Solo para archivos largos
            self.ax.set_xticks(np.linspace(0, duration, min(10, int(duration/10)+1)))
        else:
            # Duración de un beat en segundos (60 segundos / BPM)
            beat_duration = 60 / bpm
            
            # Para archivos cortos, mostrar menos compases para mejor rendimiento
            # Mostrar solo compases principales (cada 4 beats)
            total_measures = int(duration / (4 * beat_duration))
            if total_measures > 10:  # Si hay muchos compases, mostrar solo algunos
                measure_interval = max(1, total_measures // 10)
                measures = np.arange(0, total_measures + 1, measure_interval) * 4 * beat_duration
                measure_labels = [f"{int(i/measure_interval)+1}" for i in range(0, len(measures))]
                self.ax.set_xticks(measures)
                self.ax.set_xticklabels(measure_labels)
        
        # Configurar estilo del gráfico
        self.ax.set_facecolor('#212121')
        self.ax.tick_params(axis='x', colors='#00FFFF')
        self.ax.tick_params(axis='y', colors='#00FFFF')
        self.ax.spines['bottom'].set_color('#444444')
        self.ax.spines['top'].set_color('#444444')
        self.ax.spines['left'].set_color('#444444')
        self.ax.spines['right'].set_color('#444444')
        
        # BPM más visible - crear una caja destacada en la esquina
        bpm_text = f"BPM: {bpm}"
        bpm_bbox = dict(
            boxstyle="round,pad=0.5",
            fc="#FF00FF",
            ec="#FFFFFF",
            alpha=0.8
        )
        self.ax.text(
            0.98, 0.95, bpm_text, 
            transform=self.ax.transAxes, 
            ha='right', va='top',
            color='white', 
            fontsize=14, 
            fontweight='bold',
            bbox=bpm_bbox
        )
        
        # Actualizar figura (optimizado)
        self.fig.set_facecolor('#212121')
        self.fig.tight_layout()
        
        # Usar draw_idle para mejorar rendimiento en vez de draw completo
        self.draw_idle()
    
    @pyqtSlot(str)
    def _handle_error(self, error_message):
        """Maneja errores de generación."""
        print(f"Error al generar la forma de onda: {error_message}")
        self.ax.clear()
        self.ax.set_title("Error al generar la forma de onda", color='#FF3333')
        self.fig.tight_layout()
        self.draw()
    
    def update_position(self, position_ms):
        """
        Actualiza la posición del cursor de reproducción.
        
        Args:
            position_ms: Posición actual en milisegundos
        """
        if self.sr is None or self.position_line is None:
            return
        
        # Convertir de milisegundos a segundos
        position_s = position_ms / 1000.0
        
        # Actualizar la posición de la línea (matplotlib requiere una secuencia para xdata)
        self.position_line.set_xdata([position_s, position_s])
        self.current_position = position_s
        
        # Redibujar solo la línea para mayor eficiencia
        self.draw_idle()


class WaveformWidget(QWidget):
    """Widget que contiene el canvas de forma de onda."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Crear layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes para un aspecto más moderno
        
        # Crear canvas de forma de onda
        self.canvas = WaveformCanvas()
        layout.addWidget(self.canvas)
        
        # Establecer layout
        self.setLayout(layout)
        
        # Establecer estilo
        self.setStyleSheet("""
            WaveformWidget {
                background-color: #212121;
                border: none;
            }
        """)
    
    def update_waveform(self, audio_path):
        """
        Actualiza la forma de onda con un nuevo archivo de audio.
        
        Args:
            audio_path: Ruta al archivo de audio
        """
        return self.canvas.update_waveform(audio_path)
    
    def update_position(self, position_ms):
        """
        Actualiza la posición del cursor de reproducción.
        
        Args:
            position_ms: Posición actual en milisegundos
        """
        self.canvas.update_position(position_ms)


def get_bpm_from_metadata(audio_path):
    """
    Intenta obtener el BPM desde los metadatos del archivo de audio.
    
    Args:
        audio_path: Ruta al archivo de audio
        
    Returns:
        BPM si se encuentra en los metadatos, None en caso contrario
    """
    try:
        file_ext = os.path.splitext(audio_path)[1].lower()
        
        if file_ext == '.flac':
            audio = FLAC(audio_path)
            if 'BPM' in audio:
                return float(audio['BPM'][0])
            
        elif file_ext == '.mp3':
            audio = MP3(audio_path)
            if 'TBPM' in audio:
                return float(audio['TBPM'].text[0])
                
        elif file_ext == '.wav':
            # WAVE no suele tener metadatos BPM en el formato estándar
            pass
            
    except Exception as e:
        print(f"Error al leer metadatos BPM: {e}")
        
    return None
    
def detect_bpm_with_librosa(audio_path):
    """
    Detecta el BPM usando librosa (análisis de audio).
    
    Args:
        audio_path: Ruta al archivo de audio
        
    Returns:
        BPM detectado o None si hay un error
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Cargar solo los primeros 60 segundos para análisis más rápido
        y, sr = librosa.load(audio_path, sr=None, duration=60)
        
        # Detectar el tempo (BPM)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        return tempo
    except Exception as e:
        print(f"Error al detectar BPM con librosa: {e}")
        return None
        
_bpm_cache = {}

def get_song_bpm(audio_path):
    """
    Obtiene el BPM de una canción usando una combinación de métodos.
    Primero intenta leer de caché, luego metadatos, finalmente análisis de audio.
    
    Args:
        audio_path: Ruta al archivo de audio
        
    Returns:
        BPM detectado o valor predeterminado (120) si no se puede detectar
    """
    # No necesitamos declarar global _bpm_cache porque solo
    # estamos accediendo y modificando su contenido, no reasignando
    # la variable en sí
    
    # Verificar si ya está en caché
    if audio_path in _bpm_cache:
        return _bpm_cache[audio_path]
    
    # Intentar obtener de metadatos (más rápido)
    bpm = get_bpm_from_metadata(audio_path)
    if bpm:
        _bpm_cache[audio_path] = bpm
        return bpm
        
    # Si no hay metadatos, intentar con análisis de audio
    # Solo usar librosa si está disponible y solo como último recurso
    if LIBROSA_AVAILABLE:
        bpm = detect_bpm_with_librosa(audio_path)
        if bpm:
            _bpm_cache[audio_path] = bpm
            return bpm
        
    # Valor predeterminado si no se puede detectar
    _bpm_cache[audio_path] = 120  # BPM estándar para muchos géneros musicales
    return 120
