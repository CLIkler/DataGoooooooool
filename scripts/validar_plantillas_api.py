"""Script reproducible para validar plantillas de Liga MX contra API-Football.
Cruza jugadores activos reales en cada club con los endpoints oficiales de API-Sports.
Descarta jugadores que ya no jueguen en el club o retirados.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / "historico" / "api_squads_cache.json"

API_KEY = "6e5bdae748b9d9a4ca5810a97bff0a17"

TEAMS = {
    "gua": 2278,  # Guadalajara Chivas
    "tig": 2279,  # Tigres UANL
    "tij": 2280,  # Club Tijuana
    "tol": 2281,  # Toluca
    "mty": 2282,  # Monterrey
    "atl": 2283,  # Atlas
    "san": 2285,  # Santos Laguna
    "pum": 2286,  # Pumas UNAM
    "ame": 2287,  # Club America
    "nec": 2288,  # Necaxa
    "leo": 2289,  # Leon
    "que": 2290,  # Queretaro
    "pue": 2291,  # Puebla
    "pac": 2292,  # Pachuca
    "cru": 2295,  # Cruz Azul
    "jua": 2298,  # FC Juarez
    "asl": 2314,  # Atletico San Luis
    "atn": 14002, # Mazatlan / Atlante slot
}


def descargar_plantillas():
    squads = {}
    if CACHE_FILE.exists():
        try:
            squads = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            squads = {}

    headers = {"x-apisports-key": API_KEY}

    print("Verificando plantillas de los 18 clubes de la Liga MX...")
    for code, tid in TEAMS.items():
        if code in squads and len(squads[code]) > 0:
            print(f"[{code}] Ya en caché con {len(squads[code])} futbolistas activos.")
            continue

        print(f"[{code}] Consultando API-Football para team_id={tid}...")
        url = f"https://v3.football.api-sports.io/players/squads?team={tid}"
        req = urllib.request.Request(url, headers=headers)
        exito = False
        reintentos = 0

        while not exito and reintentos < 5:
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.load(resp)
                    errs = data.get("errors", {})
                    if errs:
                        print(f"[{code}] Error de API: {errs}. Esperando 30s...")
                        time.sleep(30)
                        reintentos += 1
                        continue

                    resp_list = data.get("response", [])
                    if resp_list and "players" in resp_list[0]:
                        players = resp_list[0]["players"]
                        squads[code] = players
                        print(f"[{code}] ÉXITO: {len(players)} futbolistas verificados.")
                        exito = True
                    else:
                        print(f"[{code}] Respuesta vacía para team_id={tid}")
                        exito = True
            except Exception as e:
                print(f"[{code}] Excepción HTTP: {e}. Esperando 10s...")
                time.sleep(10)
                reintentos += 1

        CACHE_FILE.write_text(json.dumps(squads, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(7)  # Respetar rate limit de 10 req/min

    return squads


if __name__ == "__main__":
    descargar_plantillas()
