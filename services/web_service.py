"""Investigación web para DataBotIA (solo biblioteca estándar).
Noticias (Google News RSS), búsqueda general (DuckDuckGo), Wikipedia y lectura de páginas.
Las URLs se validan para no acceder a redes internas (SSRF), incluso tras redirecciones."""
import html
import ipaddress
import json
import re
import socket
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from models import log

UA = {"User-Agent": "Mozilla/5.0 (compatible; DataGoolBot/1.0)", "Accept-Language": "es-MX,es;q=0.9,en;q=0.5"}
MAX_BYTES = 400_000
_CACHE, _TTL = {}, 600


def url_segura(url):
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return False
    try:
        return all(ipaddress.ip_address(i[4][0]).is_global for i in socket.getaddrinfo(u.hostname, None))
    except Exception:
        return False


class _Redir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not url_segura(newurl):
            raise urllib.error.URLError("redirección bloqueada")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _get(url, timeout=12):
    if not url_segura(url):
        raise ValueError("URL no permitida")
    with urllib.request.build_opener(_Redir).open(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        raw = r.read(MAX_BYTES)
        return raw.decode(r.headers.get_content_charset() or "utf-8", "ignore")


def _txt(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header|aside|form)\b.*?</\1>", " ", h)
    h = re.sub(r"(?i)</(p|li|h\d|div|tr)>|<br\s*/?>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t\r\f]+", " ", h)).strip()


def _cache(clave, fn):
    t = _CACHE.get(clave)
    if t and time.time() - t[0] < _TTL:
        return t[1]
    try:
        v = fn()
    except Exception as e:
        log.registrar_error("web", f"{clave[0]}: {e}")
        return []
    if v:
        _CACHE[clave] = (time.time(), v)
    return v


def noticias(q, n=6):
    def f():
        x = _get("https://news.google.com/rss/search?hl=es-419&gl=MX&ceid=MX:es-419&q=" + urllib.parse.quote(q))
        out = []
        for it in ET.fromstring(x).iter("item"):
            try:
                fecha = parsedate_to_datetime(it.findtext("pubDate")).strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                fecha = ""
            out.append({"titulo": html.unescape(it.findtext("title") or ""), "url": it.findtext("link"),
                        "fuente": it.findtext("source") or "Google News", "fecha": fecha, "resumen": ""})
        return out[:n]
    return _cache(("noticias", q), f)


def ddg(q, n=6):
    def f():
        h = _get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
        out = []
        for b in h.split('class="result__a"')[1:]:
            href = re.search(r'href="([^"]+)"', b)
            tit = re.search(r">(.*?)</a>", b, re.S)
            sn = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', b, re.S)
            if not (href and tit):
                continue
            u = href.group(1)
            if "uddg=" in u:
                u = urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("uddg", [u])[0]
            out.append({"titulo": _txt(tit.group(1)), "url": u, "fuente": urllib.parse.urlparse(u).netloc,
                        "fecha": "", "resumen": _txt(sn.group(1)) if sn else ""})
        return out[:n]
    return _cache(("ddg", q), f)


def wikipedia(q):
    def f():
        j = json.loads(_get("https://es.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=2&srsearch=" + urllib.parse.quote(q)))
        out = []
        for s in j["query"]["search"]:
            t = s["title"]
            r = json.loads(_get("https://es.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(t.replace(" ", "_"))))
            out.append({"titulo": t + " (Wikipedia)", "url": r["content_urls"]["desktop"]["page"], "fuente": "es.wikipedia.org",
                        "fecha": "", "resumen": r.get("extract", "")[:500]})
        return out
    return _cache(("wiki", q), f)


def buscar(consulta, tipo="general"):
    """tipo='noticias' prioriza actualidad; 'general' mezcla web y Wikipedia. Si una fuente falla usa la otra."""
    orden = [noticias, ddg] if tipo == "noticias" else [ddg, wikipedia, noticias]
    res = []
    for fn in orden:
        res += fn(consulta)
        if len(res) >= 6:
            break
    return res[:8]


def leer(url, max_chars=5000):
    h = _get(url)
    t = re.search(r"(?is)<title[^>]*>(.*?)</title>", h)
    return {"titulo": _txt(t.group(1)) if t else url, "url": url, "texto": _txt(h)[:max_chars]}
