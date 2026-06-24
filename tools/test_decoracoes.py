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

def test_fonte():
    print("\n[A6] fonte → garrafa de água")
    async def run():
        r = _room()
        r.decorations = [{"id": "d0", "type": "fonte", "pos": [5, 5], "facing": [0, 1], "loot": None, "tem_loot": False, "charges": 2}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0); p["pos"] = [4, 5]; p["bag"] = []; p["bag_size"] = 6; p["alive"] = True
        r.players = {"p1": p}
        await r.handle_interagir_decor("p1", "d0")
        check("ganhou garrafa de água", any(i["id"] == "garrafa_agua" for i in p["bag"]))
        check("carga decrementou p/ 1", r.decorations[0]["charges"] == 1)
        await r.handle_interagir_decor("p1", "d0")
        await r.handle_interagir_decor("p1", "d0")   # 3ª vez: sem cargas
        check("não passou de 2 garrafas", sum(1 for i in p["bag"] if i["id"] == "garrafa_agua") == 2)
        check("cargas zeradas", r.decorations[0]["charges"] == 0)
    asyncio.run(run())

def test_container():
    print("\n[A7] container de loot")
    async def run():
        r = _room()
        loot = {"gold": 7, "items": server.hidratar_itens_bau([{"id": "health_potion"}])}
        r.decorations = [{"id": "d0", "type": "barril", "pos": [5, 5], "facing": [0, 1], "loot": loot, "tem_loot": True}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0); p["pos"] = [4, 5]; p["gold"] = 0; p["bag"] = []; p["bag_size"] = 6; p["alive"] = True
        r.players = {"p1": p}
        await r.handle_take_from_decor("p1", "d0", "gold", 0)
        check("pegou 7 de ouro", p["gold"] == 7 and r.decorations[0]["loot"]["gold"] == 0)
        await r.handle_take_from_decor("p1", "d0", "item", 0)
        check("pegou o item", any(i["id"] == "health_potion" for i in p["bag"]))
        check("loot esvaziado → tem_loot False", r.decorations[0]["tem_loot"] is False)
    asyncio.run(run())

def test_visao():
    print("\n[A8] oclusão de visão dos altos")
    r = _room()
    # coluna (alta) em (4,2); herói em (2,2) revelando raio 3
    r.decorations = [{"id": "d0", "type": "coluna", "pos": [4, 2], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    r.explored = set()
    r._reveal_around(2, 2, radius=3)
    check("a própria coluna é revelada", (4, 2) in r.explored)
    check("casa atrás da coluna fica oculta", (5, 2) not in r.explored)
    check("casa ao lado (não ocluída) é revelada", (2, 4) in r.explored)

def test_serial():
    print("\n[A9] serialização game_state")
    r = _room()
    r.decorations = [{"id": "d0", "type": "estante", "pos": [3, 3], "facing": [1, 0],
                      "loot": {"gold": 0, "items": []}, "tem_loot": False}]
    r._rebuild_decor_index()
    payload = r._serializar_decoracoes()
    check("1 item serializado", len(payload) == 1)
    d0 = payload[0]
    check("tem type/pos/facing/tiles/tem_loot/alto/pisavel",
          all(k in d0 for k in ("id", "type", "pos", "facing", "tiles", "tem_loot", "alto", "pisavel", "special")))
    check("tiles resolvidos (2 casas, horizontal)", sorted(map(tuple, d0["tiles"])) == [(3, 3), (4, 3)])
    check("não vaza loot detalhado", "loot" not in d0)

def main():
    test_catalog()
    test_footprint()
    test_carga()
    test_bloqueio()
    test_fogueira()
    test_fonte()
    test_container()
    test_visao()
    test_serial()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
