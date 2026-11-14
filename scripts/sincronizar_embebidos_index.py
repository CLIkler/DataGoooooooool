"""Sincroniza los objetos embebidos PLAYERS y TEAM_LINEUPS en views/index.html
con los datasets 100% verificados (jugadores.csv y alineaciones.csv).
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "views" / "index.html"
JUGADORES_CSV = ROOT / "data" / "dataset" / "jugadores.csv"
ALINEACIONES_CSV = ROOT / "data" / "dataset" / "alineaciones.csv"

# 1. Cargar jugadores.csv
with open(JUGADORES_CSV, "r", encoding="utf-8") as f:
    jugadores_rows = list(csv.DictReader(f))

embedded_players = [
    {
        "id": int(r["id"]),
        "n": r["jugador"],
        "t": r["equipo"],
        "pos": r["posicion"],
        "num": int(r["dorsal"]),
        "g": int(r["goles"]),
        "a": int(r["asistencias"]),
        "rat": float(r["rating"]),
        "xg": float(r["xg"]),
        "min": int(r["minutos"]),
        "nat": r["nacionalidad"],
        "age": int(r["edad"])
    }
    for r in jugadores_rows
]

# 2. Cargar alineaciones.csv
with open(ALINEACIONES_CSV, "r", encoding="utf-8") as f:
    alineaciones_rows = list(csv.DictReader(f))

embedded_lineups = {}
for r in alineaciones_rows:
    eq = r["equipo"]
    if eq not in embedded_lineups:
        embedded_lineups[eq] = {
            "dt": r["dt"],
            "scheme": r["esquema"],
            "players": []
        }
    embedded_lineups[eq]["players"].append({
        "num": int(r["dorsal"]),
        "n": r["jugador"],
        "p": r["posicion"],
        "rat": float(r["rating"])
    })

# 3. Reemplazar en views/index.html
html = INDEX_HTML.read_text(encoding="utf-8")

# Reemplazar PLAYERS
pos_p_start = html.find("const PLAYERS = [")
pos_p_end = html.find("];", pos_p_start) + 2
players_js = "const PLAYERS = " + json.dumps(embedded_players, ensure_ascii=False, indent=2) + ";"
html = html[:pos_p_start] + players_js + html[pos_p_end:]
print("PLAYERS embebidos actualizados.")

# Reemplazar TEAM_LINEUPS
pos_l_start = html.find("const TEAM_LINEUPS = {")
pos_l_end = html.find("};", pos_l_start) + 2
lineups_js = "const TEAM_LINEUPS = " + json.dumps(embedded_lineups, ensure_ascii=False, indent=2) + ";"
html = html[:pos_l_start] + lineups_js + html[pos_l_end:]
print("TEAM_LINEUPS embebidos actualizados.")

INDEX_HTML.write_text(html, encoding="utf-8")
print("views/index.html sincronizado con éxito.")
