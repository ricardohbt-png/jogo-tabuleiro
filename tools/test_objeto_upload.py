import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

def test_aceita_png():
    b64 = base64.b64encode(PNG_1x1).decode()
    ok, res = server._save_objeto_upload("teste_obj.png", b64)
    assert ok, res
    assert res == "teste_obj.png"
    p = os.path.join(server._OBJETOS_DIR, "teste_obj.png")
    assert os.path.isfile(p)
    os.remove(p)

def test_rejeita_nao_png():
    b64 = base64.b64encode(PNG_1x1).decode()
    ok, _ = server._save_objeto_upload("x.jpg", b64)
    assert not ok

def test_path_traversal():
    b64 = base64.b64encode(PNG_1x1).decode()
    ok, res = server._save_objeto_upload("../server.py", b64)
    # basename neutraliza o diretório; resultado deve ser "server.py" mas .py é rejeitado
    assert not ok

if __name__ == "__main__":
    test_aceita_png(); test_rejeita_nao_png(); test_path_traversal()
    print("test_objeto_upload OK")
