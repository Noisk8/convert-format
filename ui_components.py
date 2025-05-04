from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                         QListWidget, QProgressBar, QFileDialog, QSlider, QListWidgetItem,
                         QMessageBox, QSplitter, QFrame, QTabWidget, QScrollArea, QStatusBar)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QSize, QMimeData
from PyQt5.QtGui import QDrag, QIcon, QColor, QPalette, QFont, QPixmap

class DragDropListWidget(QListWidget):
    """Lista personalizada que admite arrastrar y soltar archivos."""
    
    files_dropped = pyqtSignal(list)  # Lista de rutas de archivo
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setMinimumHeight(100)
        
        # Permitir que elementos sean arrastrados (reordenamiento)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.InternalMove)
        
    def dragEnterEvent(self, event):
        """Procesa el evento cuando un elemento es arrastrado sobre la lista."""
        # Aceptar archivos arrastrables
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """Procesa el evento cuando un elemento es movido sobre la lista."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """Procesa el evento cuando un elemento es soltado en la lista."""
        if event.mimeData().hasUrls():
            # Extraer las URLs como rutas de archivo
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                # Solo admitir archivos con extensión .flac
                if file_path.lower().endswith('.flac'):
                    file_paths.append(file_path)
                    
                    # Añadir archivo a la lista
                    item = QListWidgetItem(file_path.split('/')[-1])
                    item.setData(Qt.UserRole, file_path)
                    self.addItem(item)
            
            if file_paths:
                self.files_dropped.emit(file_paths)
            
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    def get_selected_files(self):
        """Obtiene las rutas de archivo de los elementos seleccionados."""
        selected_files = []
        for item in self.selectedItems():
            file_path = item.data(Qt.UserRole)
            selected_files.append(file_path)
        return selected_files
    
    def get_all_files(self):
        """Obtiene las rutas de archivo de todos los elementos."""
        all_files = []
        for i in range(self.count()):
            item = self.item(i)
            file_path = item.data(Qt.UserRole)
            all_files.append(file_path)
        return all_files
    
    def remove_selected_items(self):
        """Elimina los elementos seleccionados de la lista."""
        for item in self.selectedItems():
            row = self.row(item)
            self.takeItem(row)


class CustomProgressBar(QProgressBar):
    """Barra de progreso personalizada con mejor estilo visual."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        
        # Personalizar apariencia con estilo futurista
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00AACC;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #212121;
                color: #FFFFFF;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00AACC, stop:1 #00FFFF);
                width: 10px;
                border-radius: 3px;
            }
        """)


class FileListWidget(QWidget):
    """Widget para mostrar y gestionar la lista de archivos a convertir."""
    
    file_selected = pyqtSignal(str)  # Ruta del archivo seleccionado
    batch_convert_requested = pyqtSignal(list, str)  # Lista de archivos, directorio de salida
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Crear layout principal
        layout = QVBoxLayout(self)
        
        # Título de la sección
        title_label = QLabel("Archivos a Convertir")
        title_label.setProperty("title", "true")  # Para estilizar con CSS
        title_label.setStyleSheet("color: #00FFFF; font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Instrucciones
        instruction_label = QLabel("Arrastra archivos FLAC aquí o usa el botón 'Añadir'")
        instruction_label.setStyleSheet("font-style: italic; color: #AAAAAA;")
        layout.addWidget(instruction_label)
        
        # Lista de archivos
        self.file_list = DragDropListWidget()
        self.file_list.currentItemChanged.connect(self._on_item_selected)
        layout.addWidget(self.file_list)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Añadir")
        self.add_button.clicked.connect(self._on_add_clicked)
        
        self.remove_button = QPushButton("Eliminar")
        self.remove_button.clicked.connect(self._on_remove_clicked)
        
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # Botones de conversión
        convert_layout = QHBoxLayout()
        
        self.convert_selected_button = QPushButton("Convertir Seleccionados")
        self.convert_selected_button.clicked.connect(self._on_convert_selected_clicked)
        
        self.convert_all_button = QPushButton("Convertir Todos")
        self.convert_all_button.clicked.connect(self._on_convert_all_clicked)
        
        convert_layout.addWidget(self.convert_selected_button)
        convert_layout.addWidget(self.convert_all_button)
        
        layout.addLayout(convert_layout)
        
        # Barra de progreso
        self.progress_bar = CustomProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Establecer layout
        self.setLayout(layout)
    
    def _on_item_selected(self, current, previous):
        """Maneja el evento de selección de un elemento en la lista."""
        if current:
            file_path = current.data(Qt.UserRole)
            self.file_selected.emit(file_path)
    
    def _on_add_clicked(self):
        """Maneja el evento de clic en el botón Añadir."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Archivos FLAC (*.flac)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            
            for file_path in file_paths:
                # Verificar si el archivo ya está en la lista
                found = False
                for i in range(self.file_list.count()):
                    if self.file_list.item(i).data(Qt.UserRole) == file_path:
                        found = True
                        break
                
                if not found:
                    item = QListWidgetItem(file_path.split('/')[-1])
                    item.setData(Qt.UserRole, file_path)
                    self.file_list.addItem(item)
    
    def _on_remove_clicked(self):
        """Maneja el evento de clic en el botón Eliminar."""
        self.file_list.remove_selected_items()
    
    def _on_clear_clicked(self):
        """Maneja el evento de clic en el botón Limpiar."""
        self.file_list.clear()
    
    def _on_convert_selected_clicked(self):
        """Maneja el evento de clic en el botón Convertir Seleccionados."""
        selected_files = self.file_list.get_selected_files()
        
        if not selected_files:
            QMessageBox.warning(self, "Advertencia", "No hay archivos seleccionados para convertir.")
            return
            
        self._request_conversion(selected_files)
    
    def _on_convert_all_clicked(self):
        """Maneja el evento de clic en el botón Convertir Todos."""
        all_files = self.file_list.get_all_files()
        
        if not all_files:
            QMessageBox.warning(self, "Advertencia", "No hay archivos en la lista para convertir.")
            return
            
        self._request_conversion(all_files)
    
    def _request_conversion(self, file_list):
        """Solicita la conversión del lote de archivos."""
        # Seleccionar directorio de salida
        output_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio de Salida")
            
        if output_dir:
            self.batch_convert_requested.emit(file_list, output_dir)
    
    def update_progress(self, file_path, progress):
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(progress)
        
    def reset_progress(self):
        """Reinicia la barra de progreso."""
        self.progress_bar.setValue(0)


class PlayerControls(QWidget):
    """Widget de controles de reproducción de audio."""
    
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Crear layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 5)
        
        # Controles de reproducción
        controls_layout = QHBoxLayout()
        
        # Botón de reproducción con icono SVG
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(45, 45)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1A;
                color: #00FFFF;
                border: 2px solid #00AACC;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border: 2px solid #00FFFF;
            }
            QPushButton:pressed {
                background-color: #00AACC;
                color: #000000;
            }
        """)
        self.play_button.clicked.connect(self.play_clicked.emit)
        
        # Botón de pausa con icono SVG
        self.pause_button = QPushButton("⏸")
        self.pause_button.setFixedSize(45, 45)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1A;
                color: #00FFFF;
                border: 2px solid #00AACC;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border: 2px solid #00FFFF;
            }
            QPushButton:pressed {
                background-color: #00AACC;
                color: #000000;
            }
        """)
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        
        # Botón de detener con icono SVG
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(45, 45)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1A;
                color: #00FFFF;
                border: 2px solid #00AACC;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border: 2px solid #00FFFF;
            }
            QPushButton:pressed {
                background-color: #00AACC;
                color: #000000;
            }
        """)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        
        # Información de tiempo
        time_layout = QHBoxLayout()
        
        self.position_label = QLabel("0:00")
        self.position_label.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Slider de posición
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #00AACC;
                height: 8px;
                background: #1A1A1A;
                margin: 2px 0;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00AACC, stop:1 #00FFFF);
                border: 1px solid #00FFFF;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0088AA, stop:1 #00AACC);
                border: 1px solid #00AACC;
                height: 8px;
                border-radius: 4px;
            }
        """)
        self.position_slider.sliderMoved.connect(self.on_slider_moved)
        
        time_layout.addWidget(self.position_label)
        time_layout.addWidget(self.position_slider)
        time_layout.addWidget(self.duration_label)
        
        # Añadir layouts al layout principal
        layout.addLayout(controls_layout)
        layout.addLayout(time_layout)
        
        # Establecer layout
        self.setLayout(layout)
        
        # Establecer estilo global
        self.setStyleSheet("""
            PlayerControls {
                background-color: #212121;
                border-top: 1px solid #333333;
            }
        """)
    
    def on_slider_moved(self, position):
        """Maneja el evento de movimiento del slider."""
        self.position_changed.emit(position)
    
    def update_position(self, position):
        """Actualiza la posición mostrada en el slider y la etiqueta."""
        self.position_slider.setValue(position)
        
        # Actualizar etiqueta de posición (convertir a minutos:segundos)
        position_minutes = position // 60000
        position_seconds = (position % 60000) // 1000
        self.position_label.setText(f"{position_minutes}:{position_seconds:02d}")
    
    def update_duration(self, duration):
        """Actualiza la duración mostrada y ajusta el rango del slider."""
        self.position_slider.setRange(0, duration)
        
        # Actualizar etiqueta de duración (convertir a minutos:segundos)
        duration_minutes = duration // 60000
        duration_seconds = (duration % 60000) // 1000
        self.duration_label.setText(f"{duration_minutes}:{duration_seconds:02d}")
    
    def reset(self):
        """Reinicia los controles."""
        self.position_slider.setValue(0)
        self.position_slider.setRange(0, 0)
        self.position_label.setText("0:00")
        self.duration_label.setText("0:00")


class AudioInfoWidget(QWidget):
    """Widget para mostrar información del archivo de audio."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Crear layout
        layout = QVBoxLayout(self)
        
        # Título de la sección
        title_label = QLabel("Información del Audio")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Campo para nombre de archivo
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Archivo:"))
        self.file_name_label = QLabel("")
        file_layout.addWidget(self.file_name_label)
        layout.addLayout(file_layout)
        
        # Campo para formato
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Formato:"))
        self.format_label = QLabel("")
        format_layout.addWidget(self.format_label)
        layout.addLayout(format_layout)
        
        # Campo para frecuencia de muestreo
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Frecuencia de muestreo:"))
        self.sample_rate_label = QLabel("")
        sample_rate_layout.addWidget(self.sample_rate_label)
        layout.addLayout(sample_rate_layout)
        
        # Campo para canales
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(QLabel("Canales:"))
        self.channels_label = QLabel("")
        channels_layout.addWidget(self.channels_label)
        layout.addLayout(channels_layout)
        
        # Campo para duración
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duración:"))
        self.duration_label = QLabel("")
        duration_layout.addWidget(self.duration_label)
        layout.addLayout(duration_layout)
        
        # Campo para profundidad de bits
        bit_depth_layout = QHBoxLayout()
        bit_depth_layout.addWidget(QLabel("Profundidad de bits:"))
        self.bit_depth_label = QLabel("")
        bit_depth_layout.addWidget(self.bit_depth_label)
        layout.addLayout(bit_depth_layout)
        
        # Establecer layout
        self.setLayout(layout)
        
        # Añadir algo de estilo
        self.setStyleSheet("""
            QLabel {
                margin: 2px;
                min-width: 100px;
            }
        """)
    
    def update_info(self, audio_info):
        """Actualiza la información mostrada con los datos del archivo de audio."""
        if "error" in audio_info:
            self.clear_info()
            return
            
        self.file_name_label.setText(audio_info.get("file_name", ""))
        self.format_label.setText(audio_info.get("format", ""))
        self.sample_rate_label.setText(f"{audio_info.get('samplerate', '')} Hz")
        self.channels_label.setText(str(audio_info.get("channels", "")))
        self.duration_label.setText(audio_info.get("duration", ""))
        
        bit_depth = audio_info.get("bit_depth", "")
        if bit_depth != "N/A":
            self.bit_depth_label.setText(f"{bit_depth} bits")
        else:
            self.bit_depth_label.setText("Desconocido")
    
    def clear_info(self):
        """Limpia la información mostrada."""
        self.file_name_label.setText("")
        self.format_label.setText("")
        self.sample_rate_label.setText("")
        self.channels_label.setText("")
        self.duration_label.setText("")
        self.bit_depth_label.setText("")


class StatusBar(QStatusBar):
    """Barra de estado para mostrar mensajes y estado general de la aplicación."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Icono de estado
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self.addWidget(self.status_icon)
        
        # Texto de estado
        self.status_text = QLabel("Listo")
        self.addWidget(self.status_text)
        
        # Aplicar estilo
        self.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #dcdcdc;
            }
        """)
        
        # Inicializar estado
        self.set_status("listo")
    
    def set_status(self, status, message=None):
        """
        Establece el estado actual.
        
        Args:
            status: Estado actual ('listo', 'procesando', 'error', 'completado')
            message: Mensaje opcional a mostrar
        """
        icon_map = {
            "listo": "🟢", # verde
            "procesando": "🟡", # amarillo
            "error": "🔴",  # rojo
            "completado": "✅" # marca de verificación
        }
        
        icon = icon_map.get(status.lower(), "🟢")
        
        self.status_icon.setText(icon)
        
        if message:
            self.status_text.setText(message)
        else:
            default_messages = {
                "listo": "Listo",
                "procesando": "Procesando...",
                "error": "Error",
                "completado": "Completado"
            }
            self.status_text.setText(default_messages.get(status.lower(), "Listo"))
