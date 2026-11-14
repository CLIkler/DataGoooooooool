"""Modelo Partido (HU-1): histórico normalizado, H2H, rendimiento local/visitante y validación."""
import csv
from datetime import date

from models import db, equipo

CAMPOS = ("torneo", "jornada", "fecha", "local", "visitante", "goles_local", "goles_visitante", "fuente")
PARTIDOS_POR_TORNEO = 153  # 18 equipos x 17 jornadas / 2


def _normalizar(r):
    for c in CAMPOS:
        if r.get(c) is None or str(r.get(c)).strip() == "":
            raise ValueError(f"campo vacío: {c}")
    l, v = equipo.clave(r["local"]), equipo.clave(r["visitante"])
    if not l or not v:
        raise ValueError(f"equipo no reconocido: {r['local']} / {r['visitante']}")
    if l == v:
        raise ValueError("local y visitante iguales")
    f = date.fromisoformat(str(r["fecha"])[:10]).isoformat()
    return (str(r["torneo"]).strip(), int(r["jornada"]), f, l, v, int(r["goles_local"]), int(r["goles_visitante"]), str(r["fuente"]).strip())


def insertar_lote(filas):
    """Inserta validando; los duplicados (mismo torneo/jornada/local/visitante) se ignoran."""
    res = {"insertados": 0, "duplicados": 0, "invalidos": 0, "errores": []}
    with db.conectar() as c:
        for r in filas:
            try:
                t = _normalizar(r)
            except Exception as e:
                res["invalidos"] += 1
                res["errores"].append(str(e))
                continue
            cur = c.execute("INSERT OR IGNORE INTO partidos (torneo, jornada, fecha, local, visitante, goles_local, goles_visitante, fuente) VALUES (?,?,?,?,?,?,?,?)", t)
            res["insertados" if cur.rowcount else "duplicados"] += 1
    return res


def por_equipo(clave, torneo=None, limite=20):
    q, p = "SELECT * FROM partidos WHERE (local=? OR visitante=?)", [clave, clave]
    if torneo:
        q += " AND torneo=?"
        p.append(torneo)
    q += " ORDER BY fecha DESC LIMIT ?"
    p.append(max(1, min(int(limite), 200)))
    with db.conectar() as c:
        return [dict(r) for r in c.execute(q, p)]


def por_jornada(torneo, jornada):
    with db.conectar() as c:
        return [dict(r) for r in c.execute("SELECT * FROM partidos WHERE torneo=? AND jornada=? ORDER BY fecha, local", (torneo, int(jornada)))]


def h2h(a, b):
    with db.conectar() as c:
        filas = [dict(r) for r in c.execute(
            "SELECT * FROM partidos WHERE (local=? AND visitante=?) OR (local=? AND visitante=?) ORDER BY fecha DESC", (a, b, b, a))]
    r = {"a": a, "b": b, "partidos": len(filas), "victorias_a": 0, "victorias_b": 0, "empates": 0, "goles_a": 0, "goles_b": 0, "ultimos": filas[:5]}
    for p in filas:
        ga, gb = (p["goles_local"], p["goles_visitante"]) if p["local"] == a else (p["goles_visitante"], p["goles_local"])
        r["goles_a"] += ga
        r["goles_b"] += gb
        r["victorias_a" if ga > gb else "victorias_b" if gb > ga else "empates"] += 1
    return r


def rendimiento(clave):
    """PJ, G, E, P, GF, GC como local y como visitante."""
    out = {}
    with db.conectar() as c:
        for rol, cf, cc in (("local", "goles_local", "goles_visitante"), ("visitante", "goles_visitante", "goles_local")):
            r = c.execute(f"""SELECT COUNT(*) pj, COALESCE(SUM({cf}>{cc}),0) g, COALESCE(SUM({cf}={cc}),0) e,
                              COALESCE(SUM({cf}<{cc}),0) p, COALESCE(SUM({cf}),0) gf, COALESCE(SUM({cc}),0) gc
                              FROM partidos WHERE {rol}=?""", (clave,)).fetchone()
            out[rol] = dict(r)
    return out


def validar():
    """Criterios HU-1: al menos 3 torneos completos, sin nulos ni duplicados."""
    with db.conectar() as c:
        torneos = [dict(r) for r in c.execute("SELECT torneo, COUNT(*) partidos FROM partidos GROUP BY torneo ORDER BY MIN(fecha)")]
        nulos = sum(c.execute(f"SELECT COUNT(*) FROM partidos WHERE {col} IS NULL OR TRIM({col})=''").fetchone()[0] for col in CAMPOS)
        dup = c.execute("""SELECT COUNT(*) FROM (SELECT 1 FROM partidos GROUP BY torneo, jornada,
                           MIN(local, visitante), MAX(local, visitante) HAVING COUNT(*) > 1)""").fetchone()[0]
    completos = [t["torneo"] for t in torneos if t["partidos"] >= PARTIDOS_POR_TORNEO]
    return {"torneos": torneos, "torneos_completos": completos, "cumple_3_torneos": len(completos) >= 3,
            "nulos": nulos, "duplicados": dup}


def importar_csv_dir(carpeta):
    total = {"insertados": 0, "duplicados": 0, "invalidos": 0, "errores": []}
    for f in sorted(carpeta.glob("*.csv")):
        with f.open(encoding="utf-8", newline="") as fh:
            r = insertar_lote(list(csv.DictReader(fh)))
        for k in ("insertados", "duplicados", "invalidos"):
            total[k] += r[k]
        total["errores"] += r["errores"]
    return total
