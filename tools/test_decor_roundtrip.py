"""Roundtrip: a masmorra de amostra com decorações valida no servidor.
Roda da raiz: python tools/test_decor_roundtrip.py"""
import sys, os, json, asyncio
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, FLOOR

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def _noop(*a, **k): pass

def _room():
    r = GameRoom("TEST")
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop; r.push_state = _noop
    r.map_w, r.map_h = 12, 12
    r.tiles = [[FLOOR] * 12 for _ in range(12)]
    r.rooms = []
    r.players = {}
    r.decorations = []
    r._rebuild_decor_index()
    return r

def _defn_base():
    return {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 12, "h": 12},
        "tiles": [[FLOOR] * 12 for _ in range(12)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12,
                   "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": None, "prisoner": None,
        "monsters": [], "chests": [], "traps": [], "decorations": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── Teste original: masmorra de amostra valida e tem 5 decorações ──
    print("\n[RT1] validação da masmorra de amostra")
    with open(os.path.join(base, "dungeons", "test_decoracoes.json"), encoding="utf-8") as f:
        d = json.load(f)
    ok, msg = server.validar_dungeon(d)
    check(f"amostra válida ({msg})", ok is True)
    check("tem 5 decorações", len(d["decorations"]) == 5)

    # ── Teste novo: round-trip preserva o campo `image` ──
    print("\n[RT2] round-trip image: salvar→carregar→serializar preserva image")
    img_name = "arvore.png"
    img_path = os.path.join(base, "assets", "objetos", img_name)
    stub_criado = False
    if not os.path.isfile(img_path):
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        open(img_path, "wb").close()
        stub_criado = True
    try:
        defn = _defn_base()
        defn["decorations"] = [
            {"type": "arvore", "pos": [3, 3], "facing": [0, 1], "loot": None, "image": img_name},
        ]
        ok, msg = server.validar_dungeon(defn)
        check(f"dungeon com image valida ({msg})", ok is True)

        r = _room()
        r.load_authored_dungeon(defn)
        check("1 decoração carregada", len(r.decorations) == 1)
        check("image preservada no load", r.decorations[0].get("image") == img_name)

        serialized = r._serializar_decoracoes()
        check("1 item serializado", len(serialized) == 1)
        check("image preservada na serialização", serialized[0].get("image") == img_name)

        # Decoração sem image não deve vazar image
        defn2 = _defn_base()
        defn2["decorations"] = [
            {"type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": None},
        ]
        r2 = _room()
        r2.load_authored_dungeon(defn2)
        serialized2 = r2._serializar_decoracoes()
        check("decoração sem image serializa image como None", serialized2[0].get("image") is None)
    finally:
        if stub_criado and os.path.isfile(img_path):
            os.remove(img_path)

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
