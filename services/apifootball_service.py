"""HU-1: importa partidos terminados de la Liga MX desde API-Football (api-sports.io).
Requiere APIFOOTBALL_KEY. La temporada 2025 de la API incluye Apertura 2025 y Clausura 2026;
la 2024, Apertura 2024 y Clausura 2025. Tu plan debe tener acceso a esas temporadas."""
import re

import config
from models import log, partido
from services import http_cliente

URL = "https://v3.football.api-sports.io/fixtures?league={liga}&season={temp}"


def importar(temporadas=(2024, 2025)):
    if not config.APIFOOTBALL_KEY:
        return {"error": "Falta APIFOOTBALL_KEY en .env"}
    total = {"insertados": 0, "duplicados": 0, "invalidos": 0, "temporadas": {}}
    for temp in temporadas:
        j = http_cliente.get_json(URL.format(liga=config.APIFOOTBALL_LIGA_ID, temp=temp),
                                  {"x-apisports-key": config.APIFOOTBALL_KEY}, origen="apifootball")
        if not j or not isinstance(j.get("response"), list):
            log.registrar_error("apifootball", f"respuesta inválida temporada {temp}: {(j or {}).get('errors')}")
            total["temporadas"][temp] = "error"
            continue
        filas = []
        for f in j["response"]:
            m = re.search(r"(Apertura|Clausura)\D*(\d+)", f["league"].get("round", ""))
            g = f["goals"]
            if not m or f["fixture"]["status"]["short"] != "FT" or g["home"] is None or g["away"] is None:
                continue  # liguilla, pendientes o suspendidos
            fecha = f["fixture"]["date"][:10]
            filas.append({"torneo": f"{m.group(1)} {fecha[:4]}", "jornada": int(m.group(2)), "fecha": fecha,
                          "local": f["teams"]["home"]["name"], "visitante": f["teams"]["away"]["name"],
                          "goles_local": g["home"], "goles_visitante": g["away"], "fuente": "API-Football"})
        r = partido.insertar_lote(filas)
        total["temporadas"][temp] = len(filas)
        for k in ("insertados", "duplicados", "invalidos"):
            total[k] += r[k]
    return total


def actualizar_tabla(temporada=2026):
    """Actualiza puntos, goles a favor/contra, DG y PJ de equipos.csv con la tabla de API-Football."""
    import csv
    from models import equipo
    if not config.APIFOOTBALL_KEY:
        return {"error": "Falta APIFOOTBALL_KEY en .env"}
    j = http_cliente.get_json(f"https://v3.football.api-sports.io/standings?league={config.APIFOOTBALL_LIGA_ID}&season={temporada}",
                              {"x-apisports-key": config.APIFOOTBALL_KEY}, origen="apifootball-tabla")
    try:
        grupos = j["response"][0]["league"]["standings"]
    except (TypeError, KeyError, IndexError):
        log.registrar_error("apifootball-tabla", f"respuesta inválida: {(j or {}).get('errors')}")
        return {"error": "Respuesta inválida de API-Football (ver log_errores)"}
    grupo = next((g for g in grupos if g and "apertura" in str(g[0].get("group", "")).lower()), grupos[0])
    datos = {}
    for f in grupo:
        k = equipo.clave(f["team"]["name"])
        if k:
            datos[k] = f
    ruta = config.DATASET_DIR / "equipos.csv"
    with ruta.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    campos = list(filas[0].keys())
    n = 0
    for r in filas:
        f = datos.get(r["clave"])
        if f:
            g = f["all"]["goals"]
            r.update(puntos=f["points"], goles_favor=g["for"], goles_contra=g["against"], dg=f["goalsDiff"],
                     pj=f["all"]["played"], actualizado=config.CORTE_DATOS)
            n += 1
    filas.sort(key=lambda r: (-int(r["puntos"]), -int(r["dg"])))
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return {"equipos_actualizados": n, "sin_mapear": [f["team"]["name"] for f in grupo if not equipo.clave(f["team"]["name"])]}
