"""Teste da rota estática (server._serve_static), foco em nomes de arquivo com
espaços/caracteres especiais que o browser envia percent-encoded (%20, etc.).
Rodar da raiz: python tools/test_static_serve.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server  # noqa: E402


class FakeReq:
    """Além do path, o servidor lê os cabeçalhos condicionais
    (If-None-Match / If-Modified-Since) e o Upgrade do WebSocket."""
    def __init__(self, path, headers=None):
        self.path = path
        self.headers = headers or {}


def run():
    fails = []

    def check(cond, label):
        print(("OK   " if cond else "FAIL ") + label)
        if not cond:
            fails.append(label)

    story_dir = server.STORY_DIR
    os.makedirs(story_dir, exist_ok=True)

    # arquivo com espaços e parênteses (como os nomes "WhatsApp Image ... (4).jpeg")
    nome = "zz Teste Imagem (4).jpeg"
    caminho = os.path.join(story_dir, nome)
    with open(caminho, "wb") as f:
        f.write(b"IMG-BYTES")

    try:
        # o browser pede com %20 no lugar dos espaços
        req = FakeReq("/assets/story/zz%20Teste%20Imagem%20(4).jpeg")
        resp = server._serve_static(req)
        check(resp.status_code == 200,
              f"serve imagem com espacos (status {resp.status_code}, esperado 200)")
        check(resp.body == b"IMG-BYTES", "corpo da imagem correto")

        # cache-buster ?v= não deve atrapalhar
        req2 = FakeReq("/assets/story/zz%20Teste%20Imagem%20(4).jpeg?v=123")
        check(server._serve_static(req2).status_code == 200,
              "serve mesmo com query ?v=")

        # nome limpo continua funcionando
        limpo = os.path.join(story_dir, "zz_audio_limpo.mp3")
        with open(limpo, "wb") as f:
            f.write(b"MP3")
        check(server._serve_static(FakeReq("/assets/story/zz_audio_limpo.mp3")).status_code == 200,
              "serve nome limpo (audio)")
        os.remove(limpo)

        # arquivos soltos permitidos continuam servidos (regressão da allow-list)
        check(server._serve_static(FakeReq("/index.html")).status_code == 200,
              "serve index.html")
        check(server._serve_static(FakeReq("/")).status_code == 200,
              "serve raiz / como index.html")
        check(server._serve_static(FakeReq("/game.js")).status_code == 200,
              "serve game.js")

        # path traversal codificado (%2e%2e%2f = ../) deve ser bloqueado mesmo após decode
        trav = server._serve_static(FakeReq("/assets/%2e%2e%2fserver.py"))
        check(trav.status_code in (403, 404),
              f"bloqueia traversal codificado p/ raiz (status {trav.status_code})")
        # traversal mais profundo a partir de uma subpasta de assets
        trav2 = server._serve_static(FakeReq("/assets/story/%2e%2e%2f%2e%2e%2fserver.py"))
        check(trav2.status_code in (403, 404),
              f"bloqueia traversal profundo (status {trav2.status_code})")
        # tentativa de servir um arquivo da raiz não-permitido diretamente
        check(server._serve_static(FakeReq("/server.py")).status_code == 404,
              "nao serve server.py direto")
    finally:
        if os.path.isfile(caminho):
            os.remove(caminho)

    print()
    if fails:
        print(f"{len(fails)} FALHA(S)")
        sys.exit(1)
    print("TODOS OS TESTES PASSARAM")


if __name__ == "__main__":
    run()
