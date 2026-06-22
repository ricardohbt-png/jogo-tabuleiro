"""Teste do upload de mídia da história (server._save_story_upload).
Rodar da raiz: python tools/test_story_upload.py"""
import os
import sys
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server  # noqa: E402


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def run():
    fails = []

    def check(cond, label):
        print(("OK   " if cond else "FAIL ") + label)
        if not cond:
            fails.append(label)

    story_dir = server.STORY_DIR

    # caso feliz
    ok, res = server._save_story_upload("teste_upload.png", _b64(b"conteudo-img"))
    check(ok and res == "teste_upload.png", "grava imagem valida (ok + basename)")
    p = os.path.join(story_dir, "teste_upload.png")
    check(os.path.isfile(p) and open(p, "rb").read() == b"conteudo-img",
          "arquivo no disco com conteudo certo")

    # sobrescrita
    ok2, _ = server._save_story_upload("teste_upload.png", _b64(b"novo"))
    check(ok2 and open(p, "rb").read() == b"novo", "sobrescreve com novo conteudo")

    # extensao proibida
    ok3, err3 = server._save_story_upload("malware.exe", _b64(b"x"))
    check((not ok3) and err3 == "extensão não permitida", "rejeita extensao proibida")

    # path traversal -> reduz a basename (grava dentro de story/)
    ok4, res4 = server._save_story_upload("../../hack.png", _b64(b"x"))
    check(ok4 and res4 == "hack.png", "reduz ../ a basename")
    check(os.path.isfile(os.path.join(story_dir, "hack.png")),
          "grava dentro de assets/story")

    # base64 invalido
    ok5, err5 = server._save_story_upload("foto.png", "@@@nao-base64@@@")
    check((not ok5) and err5 == "dados inválidos", "rejeita base64 invalido")

    # nome vazio
    ok6, err6 = server._save_story_upload("", _b64(b"x"))
    check((not ok6) and err6 == "nome inválido", "rejeita nome vazio")

    # grande demais (rebaixa o limite temporariamente)
    saved_max = server.STORY_UPLOAD_MAX
    server.STORY_UPLOAD_MAX = 100
    try:
        ok7, err7 = server._save_story_upload("grande.png", _b64(b"x" * 400))
        check((not ok7) and err7 == "arquivo grande demais",
              "rejeita arquivo grande demais")
    finally:
        server.STORY_UPLOAD_MAX = saved_max

    # limpeza
    for n in ("teste_upload.png", "hack.png"):
        fp = os.path.join(story_dir, n)
        if os.path.isfile(fp):
            os.remove(fp)

    print()
    if fails:
        print(f"{len(fails)} FALHA(S)")
        sys.exit(1)
    print("TODOS OS TESTES PASSARAM")


if __name__ == "__main__":
    run()
