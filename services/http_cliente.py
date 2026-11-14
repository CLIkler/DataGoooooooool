"""Cliente HTTP con reintento automático (backoff) y registro de errores."""
import json
import time
import urllib.request

import config
from models import log


def get_json(url, headers=None, origen="http", intentos=None, espera=None, abrir=urllib.request.urlopen):
    intentos = intentos or config.HTTP_REINTENTOS
    espera = config.HTTP_ESPERA_BASE if espera is None else espera
    for i in range(1, intentos + 1):
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with abrir(req, timeout=20) as r:
                return json.load(r)
        except Exception as e:
            log.registrar_error(origen, f"intento {i}/{intentos}: {e}")
            if i < intentos:
                time.sleep(espera * 2 ** (i - 1))
    return None
