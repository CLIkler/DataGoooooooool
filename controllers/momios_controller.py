"""Controlador de momios (HU-2)."""
from models import equipo, log, momio
from services import odds_service


def listar(qs):
    l, v = qs.get("local", [None])[0], qs.get("visitante", [None])[0]
    return 200, momio.ultimos(equipo.clave(l) if l else None, equipo.clave(v) if v else None)


def estado(qs):
    return 200, {"cobertura_24h": momio.cobertura_24h(), "errores_recientes": log.ultimos(10)}


def actualizar(body):
    r = odds_service.actualizar()
    return (502 if "error" in r else 200), r
