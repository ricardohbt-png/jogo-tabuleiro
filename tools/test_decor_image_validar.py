import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def _base_dungeon(decor):
    return {
        "schema_version": 1,
        "id": "t", "name": "t",
        "grid": {"w": 6, "h": 6},
        "tiles": [[1]*6 for _ in range(6)],   # tudo chão (FLOOR=1)
        "entrance": {"x": 0, "y": 0},
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 6, "h": 6,
                   "role": "entrance", "locked": False, "doors": []}],
        "monsters": [], "chests": [], "traps": [],
        "decorations": [decor],
        "objectives": {"primary": {"type": "matar_todos"}, "secondary": []},
    }

def test_image_existente_passa(tmp_png="arvore.png"):
    p = os.path.join(server.OBJETOS_DIR, tmp_png)
    os.makedirs(server.OBJETOS_DIR, exist_ok=True)
    novo = not os.path.exists(p)
    if novo: open(p, "wb").close()
    try:
        d = _base_dungeon({"type": "arvore", "pos": [1, 1], "facing": [0, 1], "image": tmp_png})
        ok, msg = server.validar_dungeon(d)
        assert ok, msg
    finally:
        if novo: os.remove(p)

def test_image_traversal_rejeitada():
    d = _base_dungeon({"type": "arvore", "pos": [1, 1], "facing": [0, 1],
                       "image": "../../server.py"})
    ok, _ = server.validar_dungeon(d)
    assert not ok

if __name__ == "__main__":
    test_image_existente_passa(); test_image_traversal_rejeitada()
    print("test_decor_image_validar OK")
