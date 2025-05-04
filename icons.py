"""
Iconos SVG incrustados para los controles del reproductor.
Usando iconos vectoriales SVG para garantizar alta calidad en todas las resoluciones
y plataformas (Windows, macOS, Linux).
"""

# Icono de reproducción (play)
PLAY_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M8 5v14l11-7z"/>
</svg>
"""

# Icono de pausa
PAUSE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
</svg>
"""

# Icono de detener (stop)
STOP_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M6 6h12v12H6z"/>
</svg>
"""

# Icono de añadir archivos
ADD_FILES_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</svg>
"""

# Icono de eliminar archivo
REMOVE_FILE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
</svg>
"""

# Icono de limpiar lista
CLEAR_LIST_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M15 16h4v2h-4zm0-8h7v2h-7zm0 4h6v2h-6zM3 18c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2V8H3v10zM14 5h-3l-1-1H6L5 5H2v2h12z"/>
</svg>
"""

# Icono de convertir
CONVERT_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-2-5.5l6-4.5-6-4.5v9z"/>
</svg>
"""

# Icono de convertir todo
CONVERT_ALL_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
</svg>
"""

# Icono para visualización de audio
WAVE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#00FFFF" d="M3 12h2v2H3zm16 0h2v2h-2zm2-7h-2v2h2zm0 14h-2v-2h2zM5 5H3v2h2zm14 0h2v2h-2zM7 12h2v2H7zm4-7h2v2h-2zM7 5h2v2H7zm4 14h2v2h-2zm0-7h2v2h-2zm-4 7h2v2H7zm10-7h2v2h-2zm0 7h2v2h-2zm-4-7h2v2h-2z"/>
</svg>
"""

def get_icon_svg_base64(svg_content):
    """
    Convierte un SVG a base64 para usar en CSS.
    
    Args:
        svg_content: Contenido SVG del icono
        
    Returns:
        Cadena base64 del SVG
    """
    import base64
    svg_bytes = svg_content.strip().encode('utf-8')
    return base64.b64encode(svg_bytes).decode('utf-8')

def get_icon_stylesheet(svg_content, size=24, hover_color="#FFFFFF"):
    """
    Convierte un SVG en un estilo CSS para un botón Qt.
    
    Args:
        svg_content: Contenido SVG del icono
        size: Tamaño del icono (ancho y alto)
        hover_color: Color del icono al pasar el cursor encima
        
    Returns:
        Cadena de estilo CSS para usar en un QPushButton
    """
    # Codificar el SVG a base64 para usar en el estilo CSS
    svg_base64 = get_icon_svg_base64(svg_content)
    
    # Crear el SVG con el color hover cambiado
    hover_svg = svg_content.replace('#00FFFF', hover_color)
    hover_svg_base64 = get_icon_svg_base64(hover_svg)
    
    # Crear el estilo CSS
    stylesheet = f"""
    QPushButton {{
        border: 2px solid #00AACC;
        border-radius: {size//2}px;
        background-color: #1A1A1A;
        min-width: {size}px;
        min-height: {size}px;
        padding: 5px;
        background-image: url(data:image/svg+xml;base64,{svg_base64});
        background-repeat: no-repeat;
        background-position: center;
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #252525, stop:1 #1A1A1A);
    }}
    QPushButton:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3A3A3A, stop:1 #2A2A2A);
        border: 2px solid #00FFFF;
        background-image: url(data:image/svg+xml;base64,{hover_svg_base64});
    }}
    QPushButton:pressed {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005577, stop:1 #007799);
        border: 2px solid #00FFFF;
    }}
    """
    
    return stylesheet
