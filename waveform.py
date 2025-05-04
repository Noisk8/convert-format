import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import os
import librosa
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
                # Calcular factor de reducción
                reduction_factor = len(data) // 50000
                data = data[::reduction_factor]
                sr = sr // reduction_factor
                
            self.finished.emit(data, sr)
        except Exception as e:
            self.error.emit(str(e))


class WaveformGenerator(QObject):
    """Clase para generar la forma de onda del audio."""
    
    generation_complete = pyqtSignal(object, object)  # Emite (datos de forma de onda, tasa de muestreo)
    generation_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None
    
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
        
        # Crear array de tiempo
        time = np.linspace(0, duration, len(audio_data))
        
        # Crear segmentos para la forma de onda
        segments = []
        for i in range(len(time) - 1):
            segments.append(((time[i], audio_data[i]), (time[i+1], audio_data[i+1])))
        
        # Crear mapa de colores con degradado
        cmap = LinearSegmentedColormap.from_list('BlueToTurquoise', ['#0080FF', '#00FFFF'])
        
        # Normalizar colores basados en posición horizontal
        norm = plt.Normalize(time.min(), time.max())
        
        # Crear colección de líneas con colores gradientes
        lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=1.2, alpha=0.8)
        lc.set_array(time)
        line = self.ax.add_collection(lc)
        
        # Añadir línea para la posición actual (efecto neón)
        self.position_line = self.ax.axvline(x=0, color='#FF00FF', linestyle='-', linewidth=2, alpha=0.9)
        
        # Configurar límites
        self.ax.set_xlim(0, duration)
        self.ax.set_ylim(-1.1, 1.1)
        
        # Calcular marcas para el eje X basadas en estándar DJ
        # Asumimos 128 BPM como estándar (ajustable según metadatos, si estuvieran disponibles)
        bpm = get_song_bpm(self.audio_path)
        
        # Duración de un beat en segundos (60 segundos / BPM)
        beat_duration = 60 / bpm
        
        # Número total de beats en la pista
        total_beats = int(duration / beat_duration)
        
        # Generar marcas para compases (cada 4 beats)
        measures = np.arange(0, total_beats + 1, 4) * beat_duration
        measure_labels = [f"{int(i/4)+1}.1" for i in range(0, total_beats + 1, 4)]
        
        # Generar marcas para beats
        beats = np.arange(0, total_beats + 1) * beat_duration
        beat_labels = []
        for i in range(0, total_beats + 1):
            measure = int(i / 4) + 1
            beat_in_measure = (i % 4) + 1
            beat_labels.append(f"{measure}.{beat_in_measure}")
            
        # Configurar marcas para el eje X
        if duration <= 30:  # Para duraciones cortas, mostrar todos los beats
            self.ax.set_xticks(beats)
            self.ax.set_xticklabels(beat_labels, rotation=45, fontsize=8)
        else:  # Para duraciones largas, mostrar solo los compases
            self.ax.set_xticks(measures)
            self.ax.set_xticklabels(measure_labels, rotation=45, fontsize=8)
        
        # Añadir líneas verticales para los compases (más prominentes)
        for measure in measures:
            self.ax.axvline(x=measure, color='#00FFFF', linestyle='-', linewidth=0.8, alpha=0.3)
            
        # Añadir líneas verticales más sutiles para los beats que no son inicio de compás
        for beat in beats:
            if beat not in measures:  # Si no es inicio de compás
                self.ax.axvline(x=beat, color='#00FFFF', linestyle=':', linewidth=0.5, alpha=0.2)
        
        # Configurar etiquetas y estilo
        self.ax.set_xlabel('Compás.Beat', color='#00FFFF')
        self.ax.set_ylabel('Amplitud', color='#00FFFF')
        self.ax.grid(False)  # Desactivamos el grid predeterminado ya que tenemos nuestras propias líneas
        
        # Configurar estilo para ejes
        self.ax.tick_params(axis='x', colors='#00FFFF')
        self.ax.tick_params(axis='y', colors='#00FFFF')
        self.ax.spines['bottom'].set_color('#444444')
        self.ax.spines['top'].set_color('#444444')
        self.ax.spines['left'].set_color('#444444')
        self.ax.spines['right'].set_color('#444444')
        
        # Etiqueta informativa sobre los beats
        bpm_text = f"BPM: {bpm}"
        self.ax.text(0.98, 0.9, bpm_text, transform=self.ax.transAxes, ha='right', 
                    color='#00FFFF', fontsize=10, fontweight='bold', alpha=0.7,
                    bbox=dict(facecolor='#212121', edgecolor='#00FFFF', boxstyle='round,pad=0.5', alpha=0.7))
        
        # Actualizamos la figura
        self.fig.set_facecolor('#212121')
        self.fig.tight_layout()
        self.draw()
    
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
        
def get_song_bpm(audio_path):
    """
    Obtiene el BPM de una canción usando una combinación de métodos.
    Primero intenta leer metadatos, luego realiza análisis de audio si es necesario.
    
    Args:
        audio_path: Ruta al archivo de audio
        
    Returns:
        BPM detectado o valor predeterminado (120) si no se puede detectar
    """
    # Intentar obtener de metadatos (más rápido)
    bpm = get_bpm_from_metadata(audio_path)
    if bpm:
        return bpm
        
    # Si no hay metadatos, intentar con análisis de audio
    bpm = detect_bpm_with_librosa(audio_path)
    if bpm:
        return bpm
        
    # Valor predeterminado si no se puede detectar
    return 120  # BPM estándar para muchos géneros musicales
