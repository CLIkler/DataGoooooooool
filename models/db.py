"""Modelo base: conexión SQLite y esquema (partidos, momios, log de errores)."""
import sqlite3

import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    torneo TEXT NOT NULL,
    jornada INTEGER NOT NULL CHECK (jornada BETWEEN 1 AND 17),
    fecha TEXT NOT NULL,
    local TEXT NOT NULL,
    visitante TEXT NOT NULL,
    goles_local INTEGER NOT NULL CHECK (goles_local >= 0),
    goles_visitante INTEGER NOT NULL CHECK (goles_visitante >= 0),
    fuente TEXT NOT NULL,
    CHECK (local <> visitante),
    UNIQUE (torneo, jornada, local, visitante)
);
CREATE INDEX IF NOT EXISTS ix_partidos_local ON partidos (local);
CREATE INDEX IF NOT EXISTS ix_partidos_visitante ON partidos (visitante);
CREATE INDEX IF NOT EXISTS ix_partidos_jornada ON partidos (torneo, jornada);

CREATE TABLE IF NOT EXISTS momios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_partido TEXT NOT NULL,
    local TEXT NOT NULL,
    visitante TEXT NOT NULL,
    casa TEXT NOT NULL,
    mercado TEXT NOT NULL CHECK (mercado IN ('1X2', 'BTTS', 'TOTAL')),
    seleccion TEXT NOT NULL,
    linea REAL NOT NULL DEFAULT 0,
    cuota REAL NOT NULL CHECK (cuota > 1),
    capturado_en TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_momios_partido ON momios (local, visitante, fecha_partido);

CREATE TABLE IF NOT EXISTS log_errores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    origen TEXT NOT NULL,
    detalle TEXT NOT NULL
);
"""


def conectar():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def iniciar():
    c = conectar()
    c.executescript(ESQUEMA)
    c.commit()
    c.close()
