'''
Módulo de conversión de audio para la aplicación Convertidor FLAC a WAV.
Este archivo contiene la clase AudioConverter que se encarga de convertir
archivos FLAC a formato WAV de alta calidad compatible con equipos de DJ
como el Denon DS-1200, manteniendo la calidad óptima del audio.
'''

import os
import subprocess
import threading
import concurrent.futures  # Para procesamiento paralelo de múltiples archivos

# Hacer psutil opcional
try:
    import psutil              # Para determinar recursos del sistema
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    import multiprocessing     # Alternativa a psutil

from PyQt5.QtCore import QObject, pyqtSignal
from platform_utils import get_ffmpeg_binary  # Utilidad para encontrar ffmpeg en diferentes sistemas

class AudioConverter(QObject):
    """Clase para convertir archivos FLAC a WAV usando ffmpeg."""
    
    # Señales para comunicar el progreso a la interfaz gráfica
    conversion_started = pyqtSignal(str)                # Emitida cuando inicia una conversión
    conversion_progress = pyqtSignal(str, int)          # archivo, porcentaje
    conversion_completed = pyqtSignal(str, str)         # archivo original, archivo convertido
    conversion_error = pyqtSignal(str, str)             # archivo, mensaje de error
    batch_completed = pyqtSignal()                      # Emitida cuando se completa un lote
    
    def __init__(self):
        """Inicializa el conversor de audio."""
        super().__init__()
        self._cancel_conversion = False                 # Flag para cancelar conversiones
        self._current_conversions = {}                  # Diccionario: archivo -> proceso
        self._ffmpeg_path = get_ffmpeg_binary()         # Ruta a ffmpeg según la plataforma
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._get_optimal_thread_count()  # Optimizar número de hilos
        )
        
    def _get_optimal_thread_count(self):
        """Determina el número óptimo de hilos para la conversión basado en CPU y memoria."""
        # Obtener el número real de núcleos físicos (no virtuales)
        if PSUTIL_AVAILABLE:
            cpu_count = psutil.cpu_count(logical=False) or 2
        else:
            cpu_count = multiprocessing.cpu_count()
        
        # Obtener la memoria total del sistema en GB
        if PSUTIL_AVAILABLE:
            memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
        else:
            # No hay forma directa de obtener memoria total con multiprocessing
            # Se asume un valor razonable para sistemas modernos
            memory_gb = 8
        
        # Limitar hilos basado en memoria disponible
        if memory_gb < 4:
            return max(1, cpu_count - 1)  # Sistemas con poca memoria
        elif memory_gb < 8:
            return max(2, cpu_count)      # Sistemas con memoria media
        else:
            return max(2, cpu_count + 2)  # Sistemas con mucha memoria
        
    def check_ffmpeg(self):
        """Verifica si ffmpeg está instalado en el sistema."""
        try:
            # Intentar ejecutar ffmpeg -version para verificar su existencia
            subprocess.run([self._ffmpeg_path, '-version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            # Si ocurre un error, ffmpeg no está disponible
            return False
    
    def convert_file(self, input_file, output_dir=None, output_file=None):
        """
        Convierte un archivo FLAC a WAV manteniendo la calidad original.
        
        Args:
            input_file: Ruta al archivo FLAC de entrada
            output_dir: Directorio de salida (opcional)
            output_file: Nombre del archivo de salida (opcional)
            
        Returns:
            La ruta del archivo WAV creado
        """
        # Verificar que el archivo exista
        if not os.path.exists(input_file):
            self.conversion_error.emit(input_file, "El archivo no existe")
            return None
            
        # Si no se especifica un directorio de salida, usar el mismo del archivo de entrada
        if not output_dir:
            output_dir = os.path.dirname(input_file)
            
        # Siempre derivar nombre del archivo a partir del original y cambiar la extensión a .wav
        base_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(base_name)[0]
        
        # Si se proporciona un nombre personalizado, usar ese nombre pero asegurar que tenga extensión .wav
        if output_file:
            output_name = os.path.splitext(output_file)[0]
            output_file = f"{output_name}.wav"
        else:
            output_file = f"{name_without_ext}.wav"
            
        output_path = os.path.join(output_dir, output_file)
        
        # Asegurar que el directorio de salida exista
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Parámetros para mantener la mayor calidad posible y maximizar rendimiento
            cmd = [
                self._ffmpeg_path,
                '-i', input_file,           # Archivo de entrada
                '-c:a', 'pcm_s24le',        # Codec de alta calidad (24 bits)
                '-y',                        # Sobrescribir archivos sin preguntar
                '-loglevel', 'error',        # Minimizar salida para mejor rendimiento
                '-threads', '2',             # Usar 2 hilos por conversión
                output_path
            ]
            
            # Emitir señal de inicio de conversión
            self.conversion_started.emit(input_file)
            
            # Crear el proceso de ffmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # Línea por línea
            )
            
            # Guardar referencia al proceso actual
            self._current_conversions[input_file] = process
            
            # Capturar la salida en tiempo real y actualizar el progreso
            while True:
                # Si se solicita cancelar, terminar el proceso
                if self._cancel_conversion:
                    process.terminate()
                    if input_file in self._current_conversions:
                        del self._current_conversions[input_file]
                    return None
                
                # Leer una línea de la salida estándar
                line = process.stdout.readline()
                
                # Si no hay más líneas y el proceso ha terminado, salir del bucle
                if not line and process.poll() is not None:
                    break
            
            # Limpiar la referencia al proceso
            if input_file in self._current_conversions:
                del self._current_conversions[input_file]
            
            # Verificar si la conversión fue exitosa
            if process.returncode == 0 and os.path.exists(output_path):
                # Emitir señal de conversión completa
                self.conversion_completed.emit(input_file, output_path)
                return output_path
            else:
                # Capturar el error si la conversión falló
                stderr = process.stderr.read()
                self.conversion_error.emit(input_file, f"Error de ffmpeg: {stderr}")
                return None
                
        except Exception as e:
            # Manejar cualquier excepción durante la conversión
            self.conversion_error.emit(input_file, str(e))
            return None
            
    def _convert_single_file_for_batch(self, file_path, output_dir, total_files, current_index):
        """Convierte un solo archivo como parte de un lote."""
        # Verificar si se ha solicitado cancelar la conversión
        if self._cancel_conversion:
            return None
            
        # Calcular y emitir el progreso
        progress = int((current_index / total_files) * 100)
        self.conversion_progress.emit(file_path, progress)
        
        try:
            # Derivar el nombre del archivo de salida (mismo nombre, extensión .wav)
            base_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_file = f"{name_without_ext}.wav"
            output_path = os.path.join(output_dir, output_file)
            
            # Asegurar que el directorio de salida exista
            os.makedirs(output_dir, exist_ok=True)
            
            # Usar un comando ffmpeg directo para mayor velocidad
            cmd = [
                self._ffmpeg_path,
                '-i', file_path,             # Archivo de entrada
                '-c:a', 'pcm_s24le',         # Codec de alta calidad (24 bits)
                '-y',                         # Sobrescribir archivos sin preguntar
                '-loglevel', 'error',         # Minimizar salida
                '-threads', '2',              # Optimizar para hilos
                output_path
            ]
            
            # Emitir señal de inicio de conversión
            self.conversion_started.emit(file_path)
            
            # Usar subprocess.run para mayor simplicidad y menos sobrecarga
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Verificar si la conversión fue exitosa
            if process.returncode == 0 and os.path.exists(output_path):
                self.conversion_completed.emit(file_path, output_path)
                return output_path
            else:
                self.conversion_error.emit(file_path, f"Error en la conversión: {process.stderr}")
                return None
        except Exception as e:
            self.conversion_error.emit(file_path, str(e))
            return None
    
    def convert_batch(self, file_list, output_dir=None):
        """
        Convierte un lote de archivos FLAC a WAV de manera optimizada.
        
        Args:
            file_list: Lista de rutas a archivos FLAC
            output_dir: Directorio de salida (opcional)
        """
        # Resetear el flag de cancelación
        self._cancel_conversion = False
        converted_files = []
        
        def convert_thread():
            """Función interna para manejar la conversión en un hilo separado."""
            total_files = len(file_list)
            
            # Usar un pool de hilos para conversión en paralelo con límite óptimo
            futures = []
            for i, file_path in enumerate(file_list):
                # Verificar si se ha solicitado cancelar
                if self._cancel_conversion:
                    break
                    
                # Enviar la tarea de conversión al pool de hilos
                future = self._thread_pool.submit(
                    self._convert_single_file_for_batch,
                    file_path, 
                    output_dir, 
                    total_files,
                    i + 1
                )
                futures.append(future)
                
            # Esperar a que terminen todas las conversiones
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    converted_files.append(future.result())
                if self._cancel_conversion:
                    # Cancelar todas las tareas pendientes
                    for f in futures:
                        f.cancel()
                    break
            
            # Emitir señal de finalización del lote
            self.batch_completed.emit()
        
        # Iniciar la conversión en un hilo separado para no bloquear la interfaz
        threading.Thread(target=convert_thread, daemon=True).start()
        
    def cancel_conversions(self):
        """Cancela todas las conversiones en curso."""
        self._cancel_conversion = True
        
        # Terminar todos los procesos activos
        for file_path, process in self._current_conversions.items():
            try:
                process.terminate()
            except:
                pass
                
        # Limpiar la lista de conversiones
        self._current_conversions.clear()
