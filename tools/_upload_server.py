#!/usr/bin/env python3
"""Mini servidor de upload p/ capturas do visualizador 3D (uso em dev apenas)."""
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DESTINO = Path(r"C:\Users\RICARDO\Desktop\jogo tabuleiro\_capturas")
DESTINO.mkdir(exist_ok=True)


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        nome = self.path.strip('/').replace('..', '').replace('/', '_') or 'shot'
        tam = int(self.headers.get('Content-Length', 0))
        dados = self.rfile.read(tam).decode()
        if ',' in dados:
            dados = dados.split(',', 1)[1]
        (DESTINO / f"{nome}.jpg").write_bytes(base64.b64decode(dados))
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'ok')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 8078), H).serve_forever()
