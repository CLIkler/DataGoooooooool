"""Registro de errores de fuentes externas (consola + tabla log_errores)."""
import logging
from datetime import datetime, timezone

from models import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def registrar_error(origen, detalle):
    logging.error("[%s] %s", origen, detalle)
    try:
        with db.conectar() as c:
            c.execute("INSERT INTO log_errores (fecha, origen, detalle) VALUES (?,?,?)",
                      (datetime.now(timezone.utc).isoformat(timespec="seconds"), origen, str(detalle)[:500]))
    except Exception as e:  # el log nunca debe tumbar el servidor
        logging.error("No se pudo guardar el error en BD: %s", e)


def ultimos(n=20):
    with db.conectar() as c:
        return [dict(r) for r in c.execute("SELECT fecha, origen, detalle FROM log_errores ORDER BY id DESC LIMIT ?", (n,))]
