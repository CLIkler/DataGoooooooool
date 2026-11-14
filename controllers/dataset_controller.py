"""Controlador de dataset y corpus RAG."""
from models import corpus, dataset


def hibrido(qs):
    return 200, dataset.cargar()


def rag(qs):
    q = qs.get("q", [""])[0][:300]
    k = max(1, min(int(qs.get("k", ["3"])[0]), 8))
    cat = qs.get("categoria", [None])[0]
    return 200, {"consulta": q, "fragmentos": corpus.buscar(q, k, cat)}


def corpus_estado(qs):
    return 200, corpus.validar()
