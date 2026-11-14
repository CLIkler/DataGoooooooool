"""Auditoría y comparación estricta de plantillas y alineaciones contra API-Football.
Genera reportes comparativos numéricos reales de jugadores activos vs no activos.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / "historico" / "api_squads_cache.json"
JUGADORES_FILE = ROOT / "data" / "dataset" / "jugadores.csv"
ALINEACIONES_FILE = ROOT / "data" / "dataset" / "alineaciones.csv"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def cargar_api_squads():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        squads = json.load(f)
    api_by_team = {}
    for team, plist in squads.items():
        api_by_team[team] = []
        for p in plist:
            api_by_team[team].append({
                "id": p.get("id"),
                "name": p.get("name") or "",
                "norm": norm(p.get("name") or ""),
                "number": p.get("number"),
                "position": p.get("position") or "",
                "age": p.get("age")
            })
    return api_by_team


def buscar_jugador(nombre, dorsal, equipo, api_by_team):
    players = api_by_team.get(equipo, [])
    n_nombre = norm(nombre)
    tokens_busq = [t for t in n_nombre.split() if len(t) > 2]

    # 1. Match exacto por dorsal si coincide algún token de nombre
    if dorsal:
        try:
            d_int = int(dorsal)
            for p in players:
                if p["number"] == d_int:
                    p_tokens = set(p["norm"].split())
                    if any(t in p_tokens or any(tok in t for tok in p_tokens) for t in tokens_busq):
                        return p, "match_dorsal_y_nombre"
        except (ValueError, TypeError):
            pass

    # 2. Match de apellido o nombre completo
    for p in players:
        p_tokens = set(p["norm"].split())
        # Si todos los tokens de búsqueda están contenidos
        if set(tokens_busq).issubset(p_tokens) and len(tokens_busq) >= 1:
            return p, "match_tokens_completos"
        # Si el apellido coincide exactamente
        if len(tokens_busq) >= 1 and tokens_busq[-1] in p_tokens:
            return p, "match_apellido"
        if len(tokens_busq) >= 1 and tokens_busq[0] in p_tokens:
            return p, "match_nombre"

    return None, "no_encontrado"


def auditar():
    api_by_team = cargar_api_squads()

    print("==================================================")
    print("REPORTE DE AUDITORÍA: DATASET JUGADORES VS API-FOOTBALL")
    print("==================================================")
    with open(JUGADORES_FILE, "r", encoding="utf-8") as f:
        jugadores = list(csv.DictReader(f))

    validados_jug = []
    descartados_jug = []

    for j in jugadores:
        match, razon = buscar_jugador(j["jugador"], j.get("dorsal"), j["equipo"], api_by_team)
        if match:
            validados_jug.append((j, match, razon))
            print(f"[ACTIVO VERIFICADO] {j['jugador']} ({j['equipo']}, #{j['dorsal']}) -> API: {match['name']} (#{match['number']})")
        else:
            descartados_jug.append(j)
            print(f"[DESCARTADO - NO JUEGA EN CLUB] {j['jugador']} ({j['equipo']}, #{j['dorsal']}) -> No activo en la plantilla oficial de la API")

    print("\n--------------------------------------------------")
    print(f"Total jugadores iniciales: {len(jugadores)}")
    print(f"Total validados en API: {len(validados_jug)} ({len(validados_jug)/len(jugadores)*100:.1f}%)")
    print(f"Total descartados (no juegan en club/retirados): {len(descartados_jug)} ({len(descartados_jug)/len(jugadores)*100:.1f}%)")
    print("--------------------------------------------------\n")

    print("==================================================")
    print("REPORTE DE AUDITORÍA: ALINEACIONES VS API-FOOTBALL")
    print("==================================================")
    with open(ALINEACIONES_FILE, "r", encoding="utf-8") as f:
        alineaciones = list(csv.DictReader(f))

    validados_ali = []
    descartados_ali = []

    for a in alineaciones:
        match, razon = buscar_jugador(a["jugador"], a.get("dorsal"), a["equipo"], api_by_team)
        if match:
            validados_ali.append((a, match, razon))
        else:
            descartados_ali.append(a)
            print(f"[ALINEACIÓN DESCARTADA] {a['equipo']}: {a['jugador']} (#{a['dorsal']}) no figura en la plantilla oficial")

    print("\n--------------------------------------------------")
    print(f"Total registros alineaciones iniciales: {len(alineaciones)}")
    print(f"Total validados en API: {len(validados_ali)} ({len(validados_ali)/len(alineaciones)*100:.1f}%)")
    print(f"Total descartados (no activos/salieron del club): {len(descartados_ali)} ({len(descartados_ali)/len(alineaciones)*100:.1f}%)")
    print("--------------------------------------------------\n")


if __name__ == "__main__":
    auditar()
