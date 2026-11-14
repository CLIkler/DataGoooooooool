"""Punto de entrada DATAGOOL (MVC): servidor HTTP, inicialización de BD y programador de momios."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config
from controllers import router
from models import db, log, partido
from services import limitador, odds_service

# Rutas protegidas: chat (consume Groq) y administrativas (llaman APIs externas / escriben en la BD)
RUTAS_CHAT = {"/api/chat", "/api/chat/estado"}
RUTAS_ADMIN = {"/api/momios/actualizar", "/api/historial/importar", "/api/tabla/actualizar"}


class Handler(BaseHTTPRequestHandler):
    def _enviar(self, status, ctype, body):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _ip(self):
        # Detrás del proxy del hosting la IP real viene en X-Forwarded-For
        return (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()

    def _json(self, status, data):
        self._enviar(status, "application/json; charset=utf-8", json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _bloqueado(self, ruta):
        """Devuelve True (y responde) si la petición excede el límite o no está autorizada."""
        if ruta in RUTAS_ADMIN:
            if config.ADMIN_TOKEN and self.headers.get("X-Admin-Token") != config.ADMIN_TOKEN:
                self._json(401, {"error": "No autorizado"})
                return True
            grupo, (maximo, ventana) = "admin", config.LIMITE_ADMIN
        elif ruta in RUTAS_CHAT:
            grupo, (maximo, ventana) = "chat", config.LIMITE_CHAT
        else:
            return False
        if not limitador.permitido(grupo, self._ip(), maximo, ventana):
            self._json(429, {"error": f"Límite de {maximo} consultas por hora alcanzado. Inténtalo más tarde."})
            return True
        return False

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/health":  # comprobación de salud para el hosting
            return self._json(200, {"status": "ok"})
        if self._bloqueado(ruta):
            return
        self._enviar(*router.manejar_get(self.path))

    def do_POST(self):
        ruta = self.path.split("?")[0]
        if self._bloqueado(ruta):
            return
        try:
            n = min(int(self.headers.get("Content-Length") or 0), 500_000)
        except ValueError:
            n = 0
        self._enviar(*router.manejar_post(self.path, self.rfile.read(n)))

    def log_message(self, *a):
        pass


def main():
    db.iniciar()
    r = partido.importar_csv_dir(config.HISTORICO_DIR)
    print(f"Histórico: +{r['insertados']} partidos ({r['duplicados']} ya existían, {r['invalidos']} inválidos)")
    if odds_service.iniciar_programador():
        print(f"Momios: actualización automática cada {config.ODDS_INTERVALO_HORAS} h")
    srv = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    print(f"DATAGOOL en http://{config.HOST}:{config.PORT}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()


if __name__ == "__main__":
    main()
