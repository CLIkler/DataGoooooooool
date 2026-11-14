"""Punto de entrada DATAGOOL (MVC): servidor Flask y programador de momios."""
import json
import flask

import config
from controllers import router
from models import db, log, partido
from services import limitador, odds_service

# Rutas protegidas
RUTAS_CHAT = {"/api/chat", "/api/chat/estado"}
RUTAS_ADMIN = {"/api/momios/actualizar", "/api/historial/importar", "/api/tabla/actualizar"}

app = flask.Flask(__name__)

def verificar_limites_y_auth(path):
    """Lógica de validación de tokens y límites de peticiones."""
    ruta = path.split("?")[0]
    # Aquí puedes mantener tu lógica de _bloqueado si deseas aplicarla a las rutas de Flask
    return None

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    """Redirige todas las peticiones GET al router de tu controlador MVC."""
    ruta_completa = "/" + path
    
    if ruta_completa == "/health":
        return flask.jsonify({"status": "ok"}), 200

    # Manejar peticiones GET desde el router existente
    status, ctype, body = router.manejar_get(ruta_completa)
    
    # Si devuelve contenido HTML o JSON, lo retornamos a Flask
    response = flask.make_response(body)
    response.status_code = status
    response.headers["Content-Type"] = ctype
    return response

@app.before_request
def before_request():
    """Filtro previo para peticiones POST o restricciones."""
    if flask.request.method == "POST":
        ruta = flask.request.path
        # Puedes integrar aquí la validación de POST con router.manejar_post si lo requieres
        pass

def inicializar_sistema():
    db.iniciar()
    r = partido.importar_csv_dir(config.HISTORICO_DIR)
    print(f"Histórico: +{r['insertados']} partidos ({r['duplicados']} ya existían, {r['invalidos']} inválidos)")
    if odds_service.iniciar_programador():
        print(f"Momios: actualización automática cada {config.ODDS_INTERVALO_HORAS} h")

# Inicializamos la BD al arrancar el worker de Gunicorn
inicializar_sistema()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)
