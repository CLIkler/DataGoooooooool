"""Modelo Dataset: equipos, jugadores, alineaciones y jornada en la forma que consume la interfaz."""
import csv

import config


def _csv(nombre):
    with (config.DATASET_DIR / nombre).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _opt(v):
    return int(v) if v not in ("", None) else None


def cargar():
    equipos = {
        r["clave"]: {
            "n": r["equipo"], "s": r["siglas"], "city": r["ciudad"], "stad": r["estadio"],
            "alt": int(r["altitud_m"]), "xgf": float(r["xg_favor"]), "xga": float(r["xg_contra"]),
            "pos": float(r["posesion_pct"]), "sot": float(r["tiros_puerta"]), "form": r["racha_ultimos_5"],
            "pts": int(r["puntos"]), "gf": _opt(r["goles_favor"]), "gc": _opt(r["goles_contra"]), "dg": int(r["dg"]),
        } for r in _csv("equipos.csv")
    }
    jugadores = [
        {"id": int(r["id"]), "n": r["jugador"], "t": r["equipo"], "pos": r["posicion"], "num": int(r["dorsal"]),
         "g": int(r["goles"]), "a": int(r["asistencias"]), "rat": float(r["rating"]), "xg": float(r["xg"]),
         "min": int(r["minutos"]), "nat": r["nacionalidad"], "age": int(r["edad"])}
        for r in _csv("jugadores.csv")
    ]
    alineaciones = {}
    for r in _csv("alineaciones.csv"):
        a = alineaciones.setdefault(r["equipo"], {"dt": r["dt"], "scheme": r["esquema"], "players": []})
        a["players"].append({"num": int(r["dorsal"]), "n": r["jugador"], "p": r["posicion"], "rat": float(r["rating"])})
    jornada = [{"h": r["local"], "a": r["visitante"], "d": r["fecha_hora"], "st": r["estadio"], "matchDate": r["fecha"]}
               for r in _csv("jornada17.csv")]
    return {"equipos": equipos, "jugadores": jugadores, "alineaciones": alineaciones, "jornada": jornada}
