"""Controlador de vistas: entrega la interfaz HTML."""
import config


def index():
    return (config.VISTAS_DIR / "index.html").read_bytes()
