"""Controlador de DataBotIA: asistente de futbol (Liga MX Apertura 2026 y más).
Arma el contexto local verificado (API-Football, tabla, H2H, momios, RAG) y delega en el agente,
que además puede investigar en la web y consultar The Odds API.
"""
import unicodedata
import re
from models import corpus, dataset, momio, partido
from models import equipo as eq
import config
from services import agente_service, groq_service


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def _contexto(pregunta):
    db = dataset.cargar()
    nombres = {k: v["n"] for k, v in db["equipos"].items()}
    tabla = sorted(db["equipos"].items(), key=lambda kv: (-kv[1]["pts"], -kv[1]["dg"]))

    partes = [
        "TABLA GENERAL APERTURA 2026 (16 Jornadas):\n" +
        "\n".join(f"{i}. {v['n']} ({k.upper()}) | {v['pts']} pts | DG {v['dg']:+d} | Racha: {v['form']}"
                  for i, (k, v) in enumerate(tabla, 1))
    ]

    partes.append(
        "CALENDARIO JORNADA 17 (Cierre de Fase Regular):\n" +
        "\n".join(f"- {p['d']}: {nombres.get(p['h'], p['h'])} vs {nombres.get(p['a'], p['a'])} en {p['st']}"
                  for p in db["jornada"])
    )

    claves = eq.detectar(pregunta)
    q_norm = _norm(pregunta)

    # Detección de equipos y agregado de sus ONCES TITULARES 100% VERIFICADOS EN API-FOOTBALL
    for c in (claves[:2] if claves else []):
        t_nombre = nombres.get(c, c.upper())
        ali = db.get("alineaciones", {}).get(c)
        if ali:
            titulares_str = ", ".join(f"{p['n']} (#{p['num']}, {p['p']})" for p in ali["players"])
            partes.append(
                f"ALINEACIÓN OFICIAL 100% VERIFICADA API-FOOTBALL — {t_nombre} ({c.upper()}):\n"
                f"- Director Técnico: {ali['dt']}\n"
                f"- Esquema Táctico: {ali['scheme']}\n"
                f"- Once Titular Activo: {titulares_str}"
            )

        r = partido.rendimiento(c)
        if r["local"]["pj"] or r["visitante"]["pj"]:
            partes.append(f"RENDIMIENTO {t_nombre} (BD Histórica): local {r['local']}, visitante {r['visitante']}")

        ult = partido.por_equipo(c, limite=5)
        if ult:
            partes.append(
                f"ÚLTIMOS 5 PARTIDOS {t_nombre}: " +
                "; ".join(f"{u['fecha']} {nombres.get(u['local'], u['local'])} {u['goles_local']}-{u['goles_visitante']} {nombres.get(u['visitante'], u['visitante'])}"
                          for u in ult)
            )

        mom = [m for m in momio.ultimos() if c in (m["local"], m["visitante"])][:8]
        if mom:
            partes.append(
                f"MOMIOS VIGENTES {t_nombre}: " +
                "; ".join(f"{m['casa']} {m['mercado']} {m['seleccion']} @{m['cuota']}" for m in mom)
            )

    if len(claves) >= 2:
        h = partido.h2h(claves[0], claves[1])
        if h["partidos"]:
            partes.append(
                f"HISTORIAL H2H {nombres.get(claves[0])} vs {nombres.get(claves[1])}: {h['partidos']} partidos, "
                f"{h['victorias_a']} victorias {nombres.get(claves[0])}, {h['empates']} empates, "
                f"{h['victorias_b']} victorias {nombres.get(claves[1])}. Goles: {h['goles_a']}-{h['goles_b']}"
            )

    # Detección de jugadores en la consulta o consulta general de jugadores
    jugadores_db = db.get("jugadores", [])
    jugadores_mencionados = []
    for j in jugadores_db:
        j_tokens = [t for t in _norm(j["n"]).split() if len(t) > 2]
        if any(tok in q_norm for tok in j_tokens):
            jugadores_mencionados.append(j)

    if jugadores_mencionados:
        partes.append(
            "FICHAS DE JUGADORES VERIFICADOS EN API-FOOTBALL (CONSULTADOS):\n" +
            "\n".join(
                f"• {j['n']} | Club Actual: {nombres.get(j['t'], j['t'])} (#{j['num']}) | Demarcación: {j['pos']} | "
                f"Nacionalidad: {j['nat']} ({j['age']} años) | Goles: {j['g']} | Asistencias: {j['a']} | "
                f"Minutos: {j['min']} | Rating: {j['rat']} | xG: {j['xg']}"
                for j in jugadores_mencionados[:5]
            )
        )
    elif any(k in q_norm for k in ["goleador", "goleadores", "jugador", "jugadores", "estrellas", "top 5"]):
        # Agregar top 5 goleadores oficiales
        top_goleadores = sorted((x for x in jugadores_db if x["pos"] in ("DEL", "MED")), key=lambda x: -x["g"])[:5]
        partes.append(
            "TOP GOLEADORES LIGA MX (APERTURA 2026 - API-FOOTBALL, solo delanteros y mediocampistas):\n" +
            "\n".join(
                f"{i}. {j['n']} ({nombres.get(j['t'], j['t'])}, #{j['num']}) — {j['g']} goles | {j['a']} asistencias | xG: {j['xg']} | Rating: {j['rat']}"
                for i, j in enumerate(top_goleadores, 1)
            )
        )

    # Documentos del corpus procesado (RAG)
    frags = corpus.buscar(pregunta, 4)
    if frags:
        partes.append(
            "EVIDENCIA DEL CORPUS VERIFICADO (RAG):\n" +
            "\n".join(f"- {f['texto']} (Fuente: {f['fuente']})" for f in frags)
        )

    return "\n\n".join(partes)


def chat(body):
    q = str(body.get("pregunta", "")).strip()
    if not q:
        return 400, {"error": "Pregunta vacía"}
    r = agente_service.responder(q, _contexto(q), body.get("historial"))
    return (502 if "error" in r else 200), r


def estado(_q=None):
    """Diagnóstico: abre http://127.0.0.1:5000/api/chat/estado en el navegador (hace una llamada real mínima a Groq)."""
    k = config.GROQ_API_KEY
    info = {"groq_key_cargada": bool(k), "groq_key_longitud": len(k),
            "modelo": config.GROQ_MODEL, "env_existe": (config.ROOT / ".env").exists()}
    r = groq_service.completar([{"role": "user", "content": "Responde solo: ok"}], None, 200)
    info["groq_ok"] = "error" not in r
    info["detalle"] = r.get("error") or (r["message"].get("content") or "(respuesta recibida)")
    return 200, info
