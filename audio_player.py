'''
Módulo de reproducción de audio para la aplicación Convertidor FLAC a WAV.
Este archivo contiene la clase AudioPlayer que proporciona las funcionalidades
de reproducción de audio para previsualizar archivos originales y convertidos.
Utiliza el sistema QMediaPlayer de PyQt5 para proporcionar una experiencia de
reproducción eficiente y de alta calidad.
'''

import os
from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class AudioPlayer(QObject):
    """Clase para reproducir archivos de audio en la aplicación."""
    
    # Señales para notificar a otros componentes sobre el estado del reproductor
    playback_started = pyqtSignal()         # Emitida cuando comienza la reproducción
    playback_stopped = pyqtSignal()         # Emitida cuando se detiene la reproducción
    playback_paused = pyqtSignal()          # Emitida cuando se pausa la reproducción
    position_changed = pyqtSignal(int)      # Posición actual en milisegundos
    duration_changed = pyqtSignal(int)      # Duración total en milisegundos
    media_status_changed = pyqtSignal(str)  # Estado actual del medio (cargando, listo, etc.)
    
    def __init__(self):
        """Inicializa el reproductor de audio."""
        super().__init__()
        self.player = QMediaPlayer()        # Instancia del reproductor multimedia de Qt
        self.current_file = None            # Ruta al archivo actualmente cargado
        
        # Conectar señales internas del reproductor a los manejadores
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.stateChanged.connect(self._on_state_changed)
    
    def load_file(self, file_path):
        """
        Carga un archivo de audio para reproducción.
        
        Args:
            file_path: Ruta absoluta al archivo de audio
            
        Returns:
            bool: True si el archivo se cargó correctamente, False en caso contrario
        """
        # Verificar que el archivo exista
        if not os.path.exists(file_path):
            return False
            
        # Guardar referencia al archivo actual
        self.current_file = file_path
        
        # Convertir la ruta a un QUrl para el reproductor
        url = QUrl.fromLocalFile(file_path)
        media_content = QMediaContent(url)
        
        # Cargar el contenido en el reproductor
        self.player.setMedia(media_content)
        return True
    
    def play(self):
        """
        Inicia o reanuda la reproducción.
        Si el reproductor estaba pausado, continúa desde esa posición.
        """
        if self.player.state() != QMediaPlayer.PlayingState:
            self.player.play()
            self.playback_started.emit()
    
    def pause(self):
        """
        Pausa la reproducción.
        Mantiene la posición actual para poder reanudar después.
        """
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.playback_paused.emit()
    
    def stop(self):
        """
        Detiene la reproducción.
        Reinicia la posición al principio del archivo.
        """
        self.player.stop()
        self.playback_stopped.emit()
    
    def seek(self, position):
        """
        Salta a una posición específica en milisegundos.
        
        Args:
            position: Posición en milisegundos a la que saltar
        """
        self.player.setPosition(position)
    
    def set_volume(self, volume):
        """
        Establece el volumen de reproducción.
        
        Args:
            volume: Nivel de volumen (0-100)
        """
        self.player.setVolume(volume)
    
    def get_position(self):
        """
        Obtiene la posición actual en milisegundos.
        
        Returns:
            int: Posición actual en milisegundos
        """
        return self.player.position()
    
    def get_duration(self):
        """
        Obtiene la duración total en milisegundos.
        
        Returns:
            int: Duración total en milisegundos
        """
        return self.player.duration()
    
    def is_playing(self):
        """
        Verifica si el reproductor está en modo de reproducción.
        
        Returns:
            bool: True si está reproduciendo, False en caso contrario
        """
        return self.player.state() == QMediaPlayer.PlayingState
    
    def _on_position_changed(self, position):
        """
        Manejador para cambios en la posición de reproducción.
        
        Args:
            position: Nueva posición en milisegundos
        """
        self.position_changed.emit(position)
    
    def _on_duration_changed(self, duration):
        """
        Manejador para cambios en la duración del medio.
        
        Args:
            duration: Nueva duración en milisegundos
        """
        self.duration_changed.emit(duration)
    
    def _on_media_status_changed(self, status):
        """
        Manejador para cambios en el estado del medio.
        Convierte los estados internos de Qt a cadenas descriptivas.
        
        Args:
            status: Estado del medio (valor de QMediaPlayer.MediaStatus)
        """
        # Mapeo de códigos de estado a texto descriptivo
        status_map = {
            QMediaPlayer.UnknownMediaStatus: "Desconocido",
            QMediaPlayer.NoMedia: "Sin medio",
            QMediaPlayer.LoadingMedia: "Cargando",
            QMediaPlayer.LoadedMedia: "Cargado",
            QMediaPlayer.StalledMedia: "Detenido",
            QMediaPlayer.BufferingMedia: "Almacenando en búfer",
            QMediaPlayer.BufferedMedia: "En búfer",
            QMediaPlayer.EndOfMedia: "Fin del medio",
            QMediaPlayer.InvalidMedia: "Medio inválido"
        }
        status_text = status_map.get(status, "Estado desconocido")
        self.media_status_changed.emit(status_text)
    
    def _on_state_changed(self, state):
        """
        Manejador para cambios en el estado del reproductor.
        
        Args:
            state: Estado del reproductor (valor de QMediaPlayer.State)
        """
        # Emitir la señal correspondiente según el estado
        if state == QMediaPlayer.StoppedState:
            self.playback_stopped.emit()
        elif state == QMediaPlayer.PlayingState:
            self.playback_started.emit()
        elif state == QMediaPlayer.PausedState:
            self.playback_paused.emit()
