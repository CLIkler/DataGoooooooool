"""Modelo Corpus RAG (HU-10): documentos con fuente y categoría obligatorias + búsqueda TF-IDF."""
import json
import math
import re
import unicodedata
from collections import Counter

import config

CATEGORIAS = {"reglamento", "tacticas", "estadisticas", "noticias", "equipos", "jugadores", "partidos", "alineaciones", "metodologia"}
_STOP = set("de la el en y a los las del un una que con por para es al se lo su sus como mas o e este esta son sobre entre vs".split())


def _tokens(t):
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w[:-1] if len(w) > 4 and w.endswith("s") else w for w in re.findall(r"[a-z0-9]+", t) if w not in _STOP and len(w) >= 2]


def cargar_docs():
    with config.CORPUS_PATH.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def validar():
    """Criterios HU-10: toda entrada con fuente y categoría válida."""
    docs = cargar_docs()
    return {"total": len(docs),
            "por_categoria": dict(Counter(d.get("categoria") for d in docs)),
            "sin_fuente": [d["id"] for d in docs if not str(d.get("fuente", "")).strip()],
            "categoria_invalida": [d["id"] for d in docs if d.get("categoria") not in CATEGORIAS],
            "no_verificados": [d["id"] for d in docs if d.get("verificado") is False]}


class _Indice:
    def __init__(self):
        self.docs = cargar_docs()
        self.tf = [Counter(_tokens(d["texto"] + " " + " ".join(str(v) for v in d.get("meta", {}).values()))) for d in self.docs]
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        self.idf = {t: math.log(1 + len(self.docs) / v) for t, v in df.items()}
        self.norm = [math.sqrt(sum((c[t] * self.idf[t]) ** 2 for t in c)) or 1.0 for c in self.tf]

    def buscar(self, consulta, k=3, categoria=None):
        q = Counter(_tokens(consulta))
        if not q:
            return []
        qn = math.sqrt(sum((q[t] * self.idf.get(t, 0)) ** 2 for t in q)) or 1.0
        res = []
        for i, d in enumerate(self.docs):
            if categoria and d.get("categoria") != categoria:
                continue
            dot = sum(q[t] * self.idf.get(t, 0) * self.tf[i][t] * self.idf.get(t, 0) for t in q if t in self.tf[i])
            if dot:
                res.append((dot / (qn * self.norm[i]), d))
        res.sort(key=lambda x: x[0], reverse=True)
        return [{"id": d["id"], "tipo": d.get("tipo", d.get("categoria")), "categoria": d.get("categoria"), "texto": d["texto"],
                 "fuente": d.get("fuente"), "score": round(s, 3)} for s, d in res[:k]]


_indice = None


def buscar(consulta, k=3, categoria=None):
    global _indice
    if _indice is None:
        _indice = _Indice()
    return _indice.buscar(consulta, k, categoria)
