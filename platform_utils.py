import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path

def get_platform():
    """Identifica la plataforma en la que se está ejecutando la aplicación."""
    if sys.platform.startswith('darwin'):
        return 'macos'
    elif sys.platform.startswith('win'):
        return 'windows'
    else:
        return 'linux'

def get_ffmpeg_binary():
    """
    Obtiene la ruta del binario ffmpeg según la plataforma.
    Para sistemas operativos donde no se encuentra instalado, intentará usar
    una versión empaquetada en la carpeta 'bin' de la aplicación.
    """
    platform_name = get_platform()
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Intentar encontrar ffmpeg en el PATH
    ffmpeg_path = shutil.which('ffmpeg')
    
    if ffmpeg_path:
        return ffmpeg_path
    
    # Si no se encuentra en el PATH, usar la versión empaquetada
    if platform_name == 'windows':
        return os.path.join(app_dir, 'bin', 'ffmpeg.exe')
    elif platform_name == 'macos':
        return os.path.join(app_dir, 'bin', 'ffmpeg')
    else:  # linux
        return os.path.join(app_dir, 'bin', 'ffmpeg')

def get_home_directory():
    """Obtiene el directorio principal del usuario según la plataforma."""
    return str(Path.home())

def get_documents_directory():
    """Obtiene el directorio de documentos del usuario según la plataforma."""
    home = get_home_directory()
    platform_name = get_platform()
    
    if platform_name == 'windows':
        return os.path.join(home, 'Documents')
    elif platform_name == 'macos':
        return os.path.join(home, 'Documents')
    else:  # linux
        # Intentar obtener el directorio XDG_DOCUMENTS_DIR
        try:
            result = subprocess.run(['xdg-user-dir', 'DOCUMENTS'], 
                                   capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
        # Si falla, usar la carpeta Documents en home
        documents = os.path.join(home, 'Documents')
        if os.path.exists(documents):
            return documents
        else:
            return home

def get_temp_directory():
    """Obtiene un directorio temporal según la plataforma."""
    import tempfile
    return tempfile.gettempdir()

def get_app_data_directory():
    """Obtiene el directorio para guardar datos de la aplicación según la plataforma."""
    app_name = 'FlacToWavConverter'
    platform_name = get_platform()
    
    if platform_name == 'windows':
        return os.path.join(os.environ.get('APPDATA', ''), app_name)
    elif platform_name == 'macos':
        return os.path.join(get_home_directory(), 'Library', 'Application Support', app_name)
    else:  # linux
        return os.path.join(get_home_directory(), '.config', app_name)

def get_gui_scaling_factor():
    """Obtiene el factor de escala para la GUI según la plataforma."""
    platform_name = get_platform()
    scaling = 1.0
    
    if platform_name == 'macos':
        scaling = 1.0  # macOS maneja la escala automáticamente
    elif platform_name == 'windows':
        import ctypes
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            scaling = user32.GetDpiForSystem() / 96.0
        except:
            scaling = 1.0
    
    return scaling

def ensure_directory_exists(directory):
    """Asegura que un directorio exista, creándolo si es necesario."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory
