"""Limitador de peticiones por IP (ventana deslizante, solo biblioteca estándar).
Protege la cuota de Groq y los endpoints que llaman a APIs externas cuando el sitio es público."""
import threading
import time

_lock = threading.Lock()
_hist = {}  # (grupo, ip) -> [timestamps]


def permitido(grupo, ip, maximo, ventana_s):
    """True si la IP aún puede hacer una petición del grupo; registra la petición."""
    ahora = time.time()
    with _lock:
        if len(_hist) > 5000:  # evita crecimiento sin límite
            for k in [k for k, v in _hist.items() if not v or ahora - v[-1] > 3600]:
                _hist.pop(k, None)
        t = [x for x in _hist.get((grupo, ip), []) if ahora - x < ventana_s]
        if len(t) >= maximo:
            _hist[(grupo, ip)] = t
            return False
        t.append(ahora)
        _hist[(grupo, ip)] = t
        return True
