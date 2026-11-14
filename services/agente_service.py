"""Agente de DataBotIA: el modelo decide qué herramientas usar (datos locales, web, momios/resultados) en un ciclo acotado."""
import json

import config
from models import corpus, dataset, momio, partido
from models import equipo as eq
from services import groq_service, odds_service, web_service

_P = lambda props, req: {"type": "object", "properties": props, "required": req}
_S = lambda d: {"type": "string", "description": d}
TOOLS = [
    {"type": "function", "function": {"name": "buscar_web", "description": "Busca información actual en internet (noticias, lesiones, fichajes, resultados, historia, estadísticas de cualquier liga).",
        "parameters": _P({"consulta": _S("consulta corta y específica, ej. 'Cruz Azul lesionados jornada 17'"),
                          "tipo": {"type": "string", "enum": ["noticias", "general"], "description": "noticias = actualidad; general = datos, historia, perfiles"}}, ["consulta"])}},
    {"type": "function", "function": {"name": "leer_pagina", "description": "Lee el texto de una URL devuelta por buscar_web cuando el resumen no basta.",
        "parameters": _P({"url": _S("URL http(s) completa")}, ["url"])}},
    {"type": "function", "function": {"name": "consultar_dataset", "description": "Consulta los datos locales verificados de la Liga MX Apertura 2026.",
        "parameters": _P({"tipo": {"type": "string", "enum": ["tabla", "goleadores", "equipo", "jugador", "h2h", "corpus"]},
                          "consulta": _S("equipo, jugador o texto de búsqueda (vacío para tabla)"),
                          "consulta2": _S("segundo equipo (solo h2h)")}, ["tipo"])}},
    {"type": "function", "function": {"name": "momios_y_resultados", "description": "The Odds API: mejores cuotas 1X2 próximas o marcadores recientes (últimos 3 días) de una liga.",
        "parameters": _P({"liga": {"type": "string", "enum": list(odds_service.LIGAS)}, "dato": {"type": "string", "enum": ["momios", "resultados"]}}, ["liga", "dato"])}},
]


def _dataset(tipo, q="", q2=""):
    db = dataset.cargar()
    nom = {k: v["n"] for k, v in db["equipos"].items()}
    if tipo == "tabla":
        t = sorted(db["equipos"].items(), key=lambda kv: (-kv[1]["pts"], -kv[1]["dg"]))
        return [f"{i}. {v['n']} {v['pts']} pts DG {v['dg']:+d} racha {v['form']}" for i, (k, v) in enumerate(t, 1)]
    if tipo == "goleadores":  # rankings de anotadores: solo delanteros y mediocampistas
        js = sorted((j for j in db["jugadores"] if j["pos"] in ("DEL", "MED")), key=lambda j: (-j["g"], -j["xg"]))[:10]
        return [f"{i}. {j['n']} ({nom.get(j['t'], j['t'])}, {j['pos']}) {j['g']} goles, {j['a']} asist., xG {j['xg']}" for i, j in enumerate(js, 1)]
    if tipo == "corpus":
        return corpus.buscar(q, 4) or "Sin coincidencias en el corpus"
    if tipo == "jugador":
        toks = [t for t in eq._norm(q).split() if len(t) > 2]
        js = [j for j in db["jugadores"] if toks and all(t in eq._norm(j["n"]) for t in toks)] or \
             [j for j in db["jugadores"] if any(t in eq._norm(j["n"]) for t in toks)]
        return [f"{j['n']} | {nom.get(j['t'], j['t'])} #{j['num']} {j['pos']} | {j['nat']} {j['age']} años | {j['g']} G {j['a']} A | {j['min']} min | rating {j['rat']} | xG {j['xg']}"
                for j in js[:5]] or "Jugador sin registro verificado en el dataset"
    if tipo == "h2h":
        a, b = eq.detectar(q), eq.detectar(q2)
        return partido.h2h(a[0], b[0]) if a and b else "Equipos no reconocidos"
    c = eq.detectar(q)
    if not c:
        return "Equipo sin registro en el dataset"
    c = c[0]
    ali = db["alineaciones"].get(c)
    return {"equipo": nom[c], "tabla": db["equipos"][c], "rendimiento": partido.rendimiento(c),
            "ultimos_5": [f"{u['fecha']} {u['local']} {u['goles_local']}-{u['goles_visitante']} {u['visitante']}" for u in partido.por_equipo(c, limite=5)],
            "alineacion_verificada": ali and {"dt": ali["dt"], "esquema": ali["scheme"], "once": [f"{p['n']} ({p['p']})" for p in ali["players"]]},
            "momios": [f"{m['casa']} {m['mercado']} {m['seleccion']} @{m['cuota']}" for m in momio.ultimos() if c in (m["local"], m["visitante"])][:8]}


def ejecutar(nombre, a):
    """Devuelve (resultado, fuentes[], descripcion_del_paso)."""
    if nombre == "buscar_web":
        r = web_service.buscar(str(a.get("consulta", ""))[:200], a.get("tipo", "general"))
        return (r or "Sin resultados; prueba otra consulta"), [{"titulo": x["titulo"], "url": x["url"]} for x in r], a.get("consulta", "")
    if nombre == "leer_pagina":
        try:
            r = web_service.leer(str(a.get("url", "")))
            return r, [{"titulo": r["titulo"], "url": r["url"]}], a.get("url", "")
        except Exception as e:
            return f"No se pudo leer la página: {e}", [], a.get("url", "")
    if nombre == "consultar_dataset":
        return _dataset(a.get("tipo"), str(a.get("consulta", "")), str(a.get("consulta2", ""))), [], f"{a.get('tipo')}: {a.get('consulta', '')}".strip(": ")
    if nombre == "momios_y_resultados":
        f = odds_service.momios_liga if a.get("dato") == "momios" else odds_service.resultados_recientes
        return f(a.get("liga", "ligamx")), [], f"{a.get('dato')} · {a.get('liga')}"
    return "Herramienta desconocida", [], ""


def responder(pregunta, contexto, historial=None):
    msgs, pasos, fuentes = groq_service.mensajes(pregunta, contexto, historial), [], []
    for i in range(config.AGENTE_MAX_PASOS + 1):
        usar = TOOLS if i < config.AGENTE_MAX_PASOS else None  # la última vuelta obliga a responder
        r = groq_service.completar(msgs, usar)
        if "error" in r and usar:  # el modelo falló generando herramientas: reintenta sin ellas
            r = groq_service.completar(msgs, None)
        if "error" in r:
            return r
        m = r["message"]
        if not m.get("tool_calls"):
            vistos = set()
            fu = [f for f in fuentes if f["url"] and not (f["url"] in vistos or vistos.add(f["url"]))][:8]
            return {"respuesta": m.get("content") or "No pude generar una respuesta.", "modelo": config.GROQ_MODEL, "pasos": pasos, "fuentes": fu}
        msgs.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": m["tool_calls"]})
        for tc in m["tool_calls"][:3]:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except ValueError:
                args = {}
            try:
                res, fu, det = ejecutar(tc["function"]["name"], args)
            except Exception as e:
                res, fu, det = f"Error en la herramienta: {e}", [], ""
            pasos.append({"herramienta": tc["function"]["name"], "detalle": str(det)[:120]})
            fuentes += fu
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(res, ensure_ascii=False, default=str)[:3500]})
    return {"error": "El agente no terminó"}
