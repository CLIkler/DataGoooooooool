"""HU-2: extrae momios (1X2, ambos anotan, más/menos 2.5) de The Odds API, con reintento y registro de errores."""
import threading
import time
from urllib.parse import quote

import config
from models import equipo, log, momio
from services import http_cliente

BASE = "https://api.the-odds-api.com/v4/sports/" + config.ODDS_SPORT


def _filas_evento(ev, mercados):
    local, visita = equipo.clave(ev["home_team"]), equipo.clave(ev["away_team"])
    if not local or not visita:
        log.registrar_error("odds", f"equipo no reconocido: {ev['home_team']} / {ev['away_team']}")
        return []
    filas = []
    for b in ev.get("bookmakers", []):
        for m in b.get("markets", []):
            for o in m.get("outcomes", []):
                base = {"fecha_partido": ev["commence_time"], "local": local, "visitante": visita, "casa": b["title"], "cuota": o["price"]}
                if m["key"] == "h2h":
                    sel = "LOCAL" if o["name"] == ev["home_team"] else "VISITANTE" if o["name"] == ev["away_team"] else "EMPATE"
                    filas.append(base | {"mercado": "1X2", "seleccion": sel})
                elif m["key"] == "totals" and o.get("point") == 2.5:
                    filas.append(base | {"mercado": "TOTAL", "seleccion": o["name"].upper(), "linea": 2.5})
                elif m["key"] == "btts":
                    filas.append(base | {"mercado": "BTTS", "seleccion": "SI" if o["name"].lower() == "yes" else "NO"})
    return [f for f in filas if f["cuota"] > 1]


def actualizar():
    """Descarga y guarda las cuotas actuales de todos los partidos próximos."""
    if not config.ODDS_API_KEY:
        return {"error": "Falta ODDS_API_KEY en .env"}
    k = quote(config.ODDS_API_KEY)
    eventos = http_cliente.get_json(f"{BASE}/odds?apiKey={k}&regions=us,eu,uk&markets=h2h,totals&oddsFormat=decimal", origen="odds")
    if eventos is None:
        return {"error": "The Odds API no respondió tras los reintentos (ver log_errores)"}
    filas = []
    for ev in eventos:
        filas += _filas_evento(ev, None)
        # 'ambos anotan' se pide por evento (mercado adicional)
        extra = http_cliente.get_json(f"{BASE}/events/{ev['id']}/odds?apiKey={k}&regions=us,eu,uk&markets=btts&oddsFormat=decimal", origen="odds-btts")
        if extra:
            filas += [f for f in _filas_evento(extra, None) if f["mercado"] == "BTTS"]
    n = momio.guardar_lote(filas) if filas else 0
    return {"partidos": len(eventos), "cuotas_guardadas": n}


_stop = threading.Event()


def iniciar_programador():
    """Actualiza cada ODDS_INTERVALO_HORAS (por defecto 6 h) para tener captura >24 h antes de cada partido."""
    if not config.ODDS_API_KEY:
        return None

    def ciclo():
        while not _stop.is_set():
            try:
                actualizar()
            except Exception as e:
                log.registrar_error("odds", f"ciclo: {e}")
            _stop.wait(config.ODDS_INTERVALO_HORAS * 3600)

    t = threading.Thread(target=ciclo, daemon=True, name="odds-programador")
    t.start()
    return t


# ── Consultas bajo demanda para el chat (con caché para cuidar la cuota de The Odds API) ──
LIGAS = {"ligamx": "soccer_mexico_ligamx", "premier": "soccer_epl", "laliga": "soccer_spain_la_liga", "seriea": "soccer_italy_serie_a",
         "bundesliga": "soccer_germany_bundesliga", "ligue1": "soccer_france_ligue_one", "champions": "soccer_uefa_champs_league",
         "mls": "soccer_usa_mls", "libertadores": "soccer_conmebol_copa_libertadores"}
_cache_chat = {}


def _api(ruta, liga, ttl):
    if not config.ODDS_API_KEY:
        return None
    sport = LIGAS.get(liga, config.ODDS_SPORT)
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/{ruta}&apiKey={quote(config.ODDS_API_KEY)}"
    t = _cache_chat.get(url)
    if t and time.time() - t[0] < ttl:
        return t[1]
    d = http_cliente.get_json(url, origen="odds-chat", intentos=1)
    if d is not None:
        _cache_chat[url] = (time.time(), d)
    return d


def resultados_recientes(liga="ligamx", dias=3):
    d = _api(f"scores/?daysFrom={max(1, min(int(dias), 3))}", liga, 600)
    if d is None:
        return {"error": "The Odds API no disponible o sin ODDS_API_KEY"}
    out = []
    for e in d:
        sc = {x["name"]: x["score"] for x in (e.get("scores") or [])}
        out.append({"partido": f"{e['home_team']} vs {e['away_team']}", "inicio": e["commence_time"],
                    "estado": "finalizado" if e.get("completed") else ("en juego/sin cerrar" if sc else "programado"),
                    "marcador": f"{sc.get(e['home_team'], '-')}-{sc.get(e['away_team'], '-')}" if sc else None})
    return out[:15]


def momios_liga(liga="ligamx", limite=8):
    d = _api("odds/?regions=us,eu,uk&markets=h2h&oddsFormat=decimal", liga, 900)
    if d is None:
        return {"error": "The Odds API no disponible o sin ODDS_API_KEY"}
    out = []
    for e in d[:limite]:
        mejor = {}
        for b in e.get("bookmakers", []):
            for m in b.get("markets", []):
                for o in m.get("outcomes", []):
                    if o["price"] > mejor.get(o["name"], (0, ""))[0]:
                        mejor[o["name"]] = (o["price"], b["title"])
        out.append({"partido": f"{e['home_team']} vs {e['away_team']}", "inicio": e["commence_time"],
                    "mejores_cuotas_1X2": {k: f"{v[0]} ({v[1]}) → prob. implícita {1 / v[0]:.0%}" for k, v in mejor.items()}})
    return out
