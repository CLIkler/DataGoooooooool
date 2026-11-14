"""Controlador del historial (HU-1): consultas por equipo, jornada, H2H y validación."""
from models import equipo, partido


def _clave(v):
    c = equipo.clave(v or "")
    if not c:
        raise ValueError(f"equipo no reconocido: {v}")
    return c


def partidos(qs):
    g = lambda k: qs.get(k, [None])[0]
    if g("equipo"):
        return 200, partido.por_equipo(_clave(g("equipo")), g("torneo"), g("limite") or 20)
    if g("torneo") and g("jornada"):
        return 200, partido.por_jornada(g("torneo"), g("jornada"))
    return 400, {"error": "Usa ?equipo=... o ?torneo=...&jornada=..."}


def h2h(qs):
    return 200, partido.h2h(_clave(qs.get("a", [None])[0]), _clave(qs.get("b", [None])[0]))


def rendimiento(qs):
    return 200, partido.rendimiento(_clave(qs.get("equipo", [None])[0]))


def validar(qs):
    return 200, partido.validar()


def importar(body):
    from services import apifootball_service
    return 200, apifootball_service.importar()


def actualizar_tabla(body):
    from services import apifootball_service
    return 200, apifootball_service.actualizar_tabla(int(body.get("temporada", 2026)))
