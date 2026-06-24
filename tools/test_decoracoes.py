"""Testes das decorações de masmorra.
Roda da raiz: python tools/test_decoracoes.py"""
import sys, os, asyncio, copy
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, WALL, FLOOR, DOOR

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def test_catalog():
    print("\n[A1] DECOR_TYPES")
    d = server.DECOR_TYPES
    check("22 tipos", len(d) == 22)
    check("ids esperados presentes", all(k in d for k in (
        "cama", "lareira", "fonte", "fogueira", "tumba", "mesa_cadeiras",
        "estante", "carroca", "coluna", "barril", "arca_tesouros", "cama_casal",
        "estante_livros", "altar", "trono", "gaiola", "grades_prisao",
        "estante_armas", "mesa_tortura", "mesa_quimica", "arvore", "arvore_grande")))
    check("fonte é fountain", d["fonte"]["special"] == "fountain")
    check("fogueira é campfire e pisável", d["fogueira"]["special"] == "campfire" and d["fogueira"]["pisavel"])
    check("fonte size 2x2", d["fonte"]["size"] == [2, 2])
    check("cama size 1x2", d["cama"]["size"] == [1, 2])
    check("coluna alta", d["coluna"]["alto"] is True)
    check("grades não-alta", d["grades_prisao"]["alto"] is False)
    check("todo tipo tem emoji/nome/gira/loot_capaz", all(
        set(("nome", "emoji", "size", "gira", "alto", "pisavel", "loot_capaz", "special")) <= set(v)
        for v in d.values()))
    check("só fogueira é pisável", [k for k, v in d.items() if v["pisavel"]] == ["fogueira"])

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

def test_footprint():
    print("\n[A2] footprint/rotação")
    r = _room()
    # cama 1x2 vertical (facing default [0,1]) ancorada em (3,3)
    t = r._decor_tiles_at("cama", 3, 3, [0, 1])
    check("cama vertical ocupa (3,3) e (3,4)", sorted(map(tuple, t)) == [(3, 3), (3, 4)])
    # cama girada 90° (facing horizontal) ocupa 2x1
    t = r._decor_tiles_at("cama", 3, 3, [1, 0])
    check("cama horizontal ocupa (3,3) e (4,3)", sorted(map(tuple, t)) == [(3, 3), (4, 3)])
    # fonte 2x2 é igual em qualquer facing
    t = r._decor_tiles_at("fonte", 5, 5, [1, 0])
    check("fonte 2x2", sorted(map(tuple, t)) == [(5, 5), (5, 6), (6, 5), (6, 6)])
    # 1x1
    t = r._decor_tiles_at("coluna", 2, 2, [1, 0])
    check("coluna 1x1", sorted(map(tuple, t)) == [(2, 2)])

def test_carga():
    print("\n[A3] carga de decorações")
    r = _room()
    defn = {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 12, "h": 12},
        "tiles": [[FLOOR] * 12 for _ in range(12)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": None, "prisoner": None,
        "monsters": [], "chests": [], "traps": [],
        "decorations": [
            {"type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": {"gold": 5, "items": [{"id": "health_potion"}]}},
            {"type": "fonte", "pos": [6, 6], "facing": [0, 1], "loot": None, "charges": 3},
        ],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }
    r.load_authored_dungeon(defn)
    check("2 decorações carregadas", len(r.decorations) == 2)
    check("loot da cama hidratado (item tem name)", r.decorations[0]["loot"]["items"][0].get("name") is not None)
    check("fonte com charges", r.decorations[1]["charges"] == 3)
    check("índice de bloqueio inclui (3,4)", (3, 4) in r._decor_block_tiles)

def test_bloqueio():
    print("\n[A4] bloqueio de movimento")
    r = _room()
    r.decorations = [{"id": "d0", "type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    check("casa da cama bloqueia", r._blocks_tile(3, 3) is True)
    check("casa vizinha da cama bloqueia", r._blocks_tile(3, 4) is True)
    check("casa livre não bloqueia", r._blocks_tile(0, 0) is False)
    # fogueira é pisável → não bloqueia
    r.decorations = [{"id": "d1", "type": "fogueira", "pos": [2, 2], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    check("fogueira não bloqueia (pisável)", r._blocks_tile(2, 2) is False)

def test_fogueira():
    print("\n[A5] fogueira 1d4")
    async def run():
        r = _room()
        r.decorations = [{"id": "d0", "type": "fogueira", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0)
        p["pos"] = [4, 4]; p["hp"] = 20; p["max_hp"] = 20; p["alive"] = True
        await r._aplicar_fogueira_se_pisar(p)
        check("herói perdeu entre 1 e 4 HP", 16 <= p["hp"] <= 19)
        # fora da fogueira: sem dano
        p["pos"] = [0, 0]; hp0 = p["hp"]
        await r._aplicar_fogueira_se_pisar(p)
        check("sem dano fora da fogueira", p["hp"] == hp0)
    asyncio.run(run())

def main():
    test_catalog()
    test_footprint()
    test_carga()
    test_bloqueio()
    test_fogueira()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
