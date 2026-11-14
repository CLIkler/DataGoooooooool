"""Enrutador: asocia URL -> controlador."""
import json
import urllib.parse

from controllers import chat_controller, dataset_controller, historial_controller, momios_controller, vista_controller

GET = {
    "/api/hibrido": dataset_controller.hibrido,
    "/api/rag": dataset_controller.rag,
    "/api/corpus/estado": dataset_controller.corpus_estado,
    "/api/partidos": historial_controller.partidos,
    "/api/h2h": historial_controller.h2h,
    "/api/rendimiento": historial_controller.rendimiento,
    "/api/historial/validar": historial_controller.validar,
    "/api/momios": momios_controller.listar,
    "/api/momios/estado": momios_controller.estado,
    "/api/chat/estado": chat_controller.estado,
}
POST = {
    "/api/chat": chat_controller.chat,
    "/api/momios/actualizar": momios_controller.actualizar,
    "/api/historial/importar": historial_controller.importar,
    "/api/tabla/actualizar": historial_controller.actualizar_tabla,
}


def _json(status, data):
    return status, "application/json; charset=utf-8", json.dumps(data, ensure_ascii=False).encode("utf-8")


def manejar_get(ruta):
    u = urllib.parse.urlparse(ruta)
    if u.path in ("/", "/index.html"):
        return 200, "text/html; charset=utf-8", vista_controller.index()
    f = GET.get(u.path)
    if not f:
        return _json(404, {"error": "Ruta no encontrada"})
    try:
        return _json(*f(urllib.parse.parse_qs(u.query)))
    except ValueError as e:
        return _json(400, {"error": str(e)})
    except Exception as e:
        return _json(500, {"error": str(e)})


def manejar_post(ruta, cuerpo):
    f = POST.get(urllib.parse.urlparse(ruta).path)
    if not f:
        return _json(404, {"error": "Ruta no encontrada"})
    try:
        return _json(*f(json.loads(cuerpo or b"{}")))
    except Exception as e:
        return _json(500, {"error": str(e)})
