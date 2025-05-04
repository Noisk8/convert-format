"""
Pruebas básicas para la aplicación de conversión FLAC a WAV.
Estas pruebas verifican la funcionalidad básica sin depender de la GUI.
"""

import os
import sys
import unittest

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos a probar
from audio_converter import get_ffmpeg_binary
from platform_utils import get_platform

class TestBasicFunctionality(unittest.TestCase):
    """Pruebas básicas de funcionalidad."""
    
    def test_platform_detection(self):
        """Verificar que la detección de plataforma funciona correctamente."""
        # Verificar que get_platform devuelve uno de los valores esperados
        platform = get_platform()
        self.assertIn(platform, ['windows', 'macos', 'linux'], 
                     "La plataforma detectada debe ser una de: windows, macos, linux")
    
    def test_ffmpeg_binary_path(self):
        """Verificar que se puede obtener una ruta para ffmpeg."""
        ffmpeg_path = get_ffmpeg_binary()
        self.assertIsNotNone(ffmpeg_path, "Se debe encontrar una ruta para ffmpeg")
        self.assertIsInstance(ffmpeg_path, str, "La ruta debe ser una cadena")
        
if __name__ == '__main__':
    unittest.main()
