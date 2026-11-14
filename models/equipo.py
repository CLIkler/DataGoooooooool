"""Modelo Equipo: normalización de nombres a la clave interna y lectura de equipos.csv."""
import csv
import re
import unicodedata

import config

ALIAS = {
    "ame": ["america", "club america"], "tig": ["tigres", "tigres uanl", "uanl"], "tol": ["toluca"],
    "pac": ["pachuca"], "cru": ["cruz azul"], "gua": ["guadalajara", "chivas"], "atl": ["atlas"],
    "atn": ["atlante"], "leo": ["leon", "club leon"], "mty": ["monterrey", "rayados"], "nec": ["necaxa"],
    "pum": ["pumas", "unam", "pumas unam", "unam pumas"], "pue": ["puebla"], "que": ["queretaro", "gallos"],
    "san": ["santos", "santos laguna"], "asl": ["atletico san luis", "atletico de san luis", "san luis"],
    "tij": ["tijuana", "xolos", "club tijuana"], "jua": ["juarez", "fc juarez", "bravos"],
}
_PARES = sorted(((a, k) for k, v in ALIAS.items() for a in v), key=lambda x: -len(x[0]))


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def clave(nombre):
    """'Club América' -> 'ame'. None si no se reconoce."""
    n = f" {_norm(nombre)} "
    for alias, k in _PARES:
        if f" {alias} " in n:
            return k
    return None


def detectar(texto):
    """Claves de equipos mencionados en un texto, en orden de aparición."""
    n = f" {_norm(texto)} "
    hallados = {}
    for alias, k in _PARES:
        pos = n.find(f" {alias} ")
        if pos >= 0:
            hallados[k] = min(pos, hallados.get(k, pos))
    return sorted(hallados, key=hallados.get)


def todos():
    with (config.DATASET_DIR / "equipos.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
