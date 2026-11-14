import os

def index():
    # Obtiene la ruta absoluta de la carpeta actual y sube al directorio base si es necesario
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_html = os.path.join(base_dir, "views", "index.html")
    
    try:
        with open(ruta_html, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: No se encontró la vista index.html</h1>", 404
