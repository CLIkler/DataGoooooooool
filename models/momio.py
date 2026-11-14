"""Modelo Momio (HU-2): almacenamiento de cuotas 1X2, ambos anotan y más/menos 2.5 goles."""
from datetime import datetime, timedelta, timezone

from models import db


def guardar_lote(filas, capturado_en=None):
    ts = capturado_en or datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db.conectar() as c:
        c.executemany("INSERT INTO momios (fecha_partido, local, visitante, casa, mercado, seleccion, linea, cuota, capturado_en) VALUES (?,?,?,?,?,?,?,?,?)",
                      [(f["fecha_partido"], f["local"], f["visitante"], f["casa"], f["mercado"], f["seleccion"], f.get("linea", 0), f["cuota"], ts) for f in filas])
    return len(filas)


def ultimos(local=None, visitante=None):
    """Última cuota capturada por casa/mercado/selección de cada partido."""
    q = """SELECT m.* FROM momios m JOIN (
             SELECT local, visitante, fecha_partido, casa, mercado, seleccion, linea, MAX(capturado_en) mx
             FROM momios GROUP BY local, visitante, fecha_partido, casa, mercado, seleccion, linea) u
           ON m.local=u.local AND m.visitante=u.visitante AND m.fecha_partido=u.fecha_partido AND m.casa=u.casa
          AND m.mercado=u.mercado AND m.seleccion=u.seleccion AND m.linea=u.linea AND m.capturado_en=u.mx WHERE 1=1"""
    p = []
    if local:
        q += " AND m.local=?"
        p.append(local)
    if visitante:
        q += " AND m.visitante=?"
        p.append(visitante)
    q += " ORDER BY m.fecha_partido, m.local, m.mercado, m.seleccion, m.cuota DESC"
    with db.conectar() as c:
        return [dict(r) | {"prob_implicita": round(1 / r["cuota"], 4)} for r in c.execute(q, p)]


def cobertura_24h():
    """Por partido: ¿hay una captura hecha al menos 24 h antes del inicio?"""
    with db.conectar() as c:
        filas = c.execute("SELECT local, visitante, fecha_partido, MIN(capturado_en) primera FROM momios GROUP BY local, visitante, fecha_partido").fetchall()
    out = []
    for r in filas:
        try:
            inicio = datetime.fromisoformat(r["fecha_partido"].replace("Z", "+00:00"))
            primera = datetime.fromisoformat(r["primera"])
            ok = primera <= inicio - timedelta(hours=24)
        except ValueError:
            ok = False
        out.append({"local": r["local"], "visitante": r["visitante"], "fecha_partido": r["fecha_partido"], "captura_24h_antes": ok})
    return out


def valor_esperado(prob_estimada, cuota):
    """EV por unidad apostada: p*cuota - 1 (>0 indica valor)."""
    return round(prob_estimada * cuota - 1, 4)
