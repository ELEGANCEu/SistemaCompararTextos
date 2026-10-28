import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from similarity import CompararTexto, CompararMultiplos

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_BODY = 5 * 1024 * 1024  # 5 MB


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload, content_type="application/json; charset=utf-8"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(BASE_DIR, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/sobre.html":
            with open(os.path.join(BASE_DIR, "sobre.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/style.css":
            with open(os.path.join(BASE_DIR, "style.css"), "rb") as f:
                self._send(200, f.read(), "text/css; charset=utf-8")
        elif self.path == "/script.js":
            with open(os.path.join(BASE_DIR, "script.js"), "rb") as f:
                self._send(
            200,
            f.read(),
            "application/javascript; charset=utf-8"
        )
        else:
            self._send(404, {"error": "Não encontrado"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY:
                return self._send(413, {"error": "Conteúdo muito grande (máx. 5 MB)."})
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"error": "JSON inválido."})

        opts = data.get("options", {})

        if self.path == "/api/compare":
            a, b = data.get("text_a", "").strip(), data.get("text_b", "").strip()
            if not a or not b:
                return self._send(400, {"error": "Informe os dois textos."})
            return self._send(200, CompararTexto(a, b, opts))

        if self.path == "/api/compare-many":
            texts = [t.strip() for t in data.get("texts", []) if isinstance(t, str) and t.strip()]
            if len(texts) < 2:
                return self._send(400, {"error": "Informe ao menos 2 textos."})
            if len(texts) > 30:
                return self._send(400, {"error": "Máximo de 30 textos."})
            return self._send(200, CompararMultiplos(texts, opts))

        self._send(404, {"error": "Rota não encontrada"})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Servidor rodando em http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
