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
    check("38 tipos", len(d) == 38)
    check("ids esperados presentes", all(k in d for k in (
        "cama", "lareira", "fonte", "fogueira", "tumba", "tumba_lapide", "mesa_cadeiras",
        "estante", "carroca", "coluna", "barril", "arca_tesouros", "cama_casal",
        "estante_livros", "altar", "trono", "gaiola", "prisao", "grades_prisao",
        "estante_armas", "mesa_tortura", "mesa_quimica", "arvore", "arvore_grande", "arvore_seca", "caverna", "casa",
        "chao", "brasao_leao", "cortina_vermelha", "cortina_branca", "lapide", "cripta",
        "fonte_de_parede", "armadura", "brasa_chao", "chama_viva", "placa")))
    check("chão é floor, pisável, 1x1", d["chao"]["special"] == "floor"
          and d["chao"]["pisavel"] and d["chao"]["size"] == [1, 1])
    check("fonte é fountain", d["fonte"]["special"] == "fountain")
    check("fogueira é campfire e pisável", d["fogueira"]["special"] == "campfire" and d["fogueira"]["pisavel"])
    check("placa é informativa, 1x1 e pisável", d["placa"]["special"] == "plaque"
          and d["placa"]["size"] == [1, 1] and d["placa"]["pisavel"]
          and not d["placa"]["loot_capaz"])
    check("placa usa PNG/GLB", d["placa"]["image"] == "placa_fincada.png"
          and server.DECOR_MODEL3D["placa"].endswith("placa_fincada.glb"))
    check("chama viva usa GLB, é pisável e causa 2d4", d["chama_viva"]["special"] == "living_flame"
          and d["chama_viva"]["pisavel"] and not d["chama_viva"]["loot_capaz"]
          and d["chama_viva"]["size"] == [1, 1]
          and server.DECOR_MODEL3D["chama_viva"].endswith("chama_viva.glb"))
    check("fonte size 2x2", d["fonte"]["size"] == [2, 2])
    check("cama size 1x2", d["cama"]["size"] == [1, 2])
    check("estante usa a nova arte PNG/GLB", d["estante"]["image"] == "estante_armas_cranios.png"
          and server.DECOR_MODEL3D["estante"].endswith("estante_armas_cranios.glb"))
    check("coluna alta", d["coluna"]["alto"] is True)
    check("caverna é alta, sólida e usa sua arte", d["caverna"]["alto"] is True
          and not d["caverna"]["pisavel"] and not d["caverna"]["loot_capaz"]
          and d["caverna"]["image"] == "caverna.png")
    check("casa é alta, 3x3, sólida e usa suas artes", d["casa"]["alto"] is True
          and d["casa"]["size"] == [3, 3] and not d["casa"]["pisavel"]
          and not d["casa"]["loot_capaz"] and d["casa"]["image"] == "casa.png")
    check("tumba com lápide usa PNG/GLB e ocupa 1x2", d["tumba_lapide"]["size"] == [1, 2]
          and d["tumba_lapide"]["gira"] and d["tumba_lapide"]["alto"]
          and not d["tumba_lapide"]["pisavel"] and not d["tumba_lapide"]["loot_capaz"]
          and d["tumba_lapide"]["image"] == "tumba_lapide.png"
          and server.DECOR_MODEL3D["tumba_lapide"].endswith("tumba_lapide.glb"))
    check("carroça usa PNG/GLB e ocupa 2x2", d["carroca"]["size"] == [2, 2]
          and d["carroca"]["gira"] and d["carroca"]["image"] == "carroca.png"
          and server.DECOR_MODEL3D["carroca"].endswith("carroca.glb"))
    check("lápide usa a miniatura correta", d["lapide"]["size"] == [1, 1]
          and not d["lapide"]["loot_capaz"] and d["lapide"]["image"] == "lapide.png"
          and server.DECOR_MODEL3D["lapide"].endswith("lapide.glb"))
    check("cripta ocupa 2x2 e usa suas artes", d["cripta"]["size"] == [2, 2]
          and d["cripta"]["alto"] and not d["cripta"]["loot_capaz"]
          and d["cripta"]["image"] == "cripta.png"
          and server.DECOR_MODEL3D["cripta"].endswith("cripta.glb"))
    check("fonte de parede usa suas artes", d["fonte_de_parede"]["size"] == [1, 1]
          # fonte de parede FORNECE agua (ate 2 garrafas), como a fonte circular,
          and d["fonte_de_parede"]["special"] == "fountain"
          and d["fonte_de_parede"]["charges"] == 2
          and d["fonte_de_parede"]["alto"]
          and not d["fonte_de_parede"]["pisavel"]
          and not d["fonte_de_parede"]["loot_capaz"]
          and d["fonte_de_parede"]["image"] == "fonte_de_parede.png"
          and server.DECOR_MODEL3D["fonte_de_parede"].endswith("fonte_de_parede.glb"))
    check("armadura usa suas artes", d["armadura"]["size"] == [1, 1]
          and d["armadura"]["alto"]
          and not d["armadura"]["pisavel"]
          and not d["armadura"]["loot_capaz"]
          and d["armadura"]["image"] == "armadura.png"
          and server.DECOR_MODEL3D["armadura"].endswith("armadura.glb"))
    check("grades não-alta", d["grades_prisao"]["alto"] is False)
    check("prisão ocupa 4 casas e pode girar", d["prisao"]["size"] == [2, 2]
          and d["prisao"]["gira"] and d["prisao"]["alto"]
          and not d["prisao"]["pisavel"])
    check("mesa de tortura usa PNG/GLB e ocupa 1x2", d["mesa_tortura"]["size"] == [1, 2]
          and d["mesa_tortura"]["gira"] and d["mesa_tortura"]["alto"]
          and not d["mesa_tortura"]["pisavel"] and not d["mesa_tortura"]["loot_capaz"]
          and d["mesa_tortura"]["image"] == "mesa_tortura.png"
          and server.DECOR_MODEL3D["mesa_tortura"].endswith("mesa_tortura.glb"))
    check("brasa usa PNG/GLB, é 1x1 e pisável", d["brasa_chao"]["size"] == [1, 1]
          and d["brasa_chao"]["pisavel"] and not d["brasa_chao"]["loot_capaz"]
          and d["brasa_chao"]["special"] == "floor_ember"
          and d["brasa_chao"]["image"] == "brasa_chao.png"
          and server.DECOR_MODEL3D["brasa_chao"].endswith("brasa_chao_animada.glb"))
    check("cortina vermelha usa PNG/GLB", d["cortina_vermelha"]["image"] == "cortina_vermelha.png"
          and server.DECOR_MODEL3D["cortina_vermelha"].endswith("cortina_vermelha.glb"))
    check("brasão usa PNG/GLB", d["brasao_leao"]["image"] == "brasao_leao.png"
          and server.DECOR_MODEL3D["brasao_leao"].endswith("brasao_leao.glb"))
    check("todo tipo tem emoji/nome/gira/loot_capaz", all(
        set(("nome", "emoji", "size", "gira", "alto", "pisavel", "loot_capaz", "special")) <= set(v)
        for v in d.values()))
    check("pisáveis: chão, fogueira, brasa, chama viva e placa", sorted(k for k, v in d.items() if v["pisavel"]) == [
        "brasa_chao", "brasao_leao", "chama_viva", "chao", "cortina_branca", "cortina_vermelha", "fogueira", "placa"])

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
    t = r._decor_tiles_at("prisao", 6, 3, [0, 1])
    check("prisão 2x2 na orientação frontal", sorted(map(tuple, t)) == [
        (6, 3), (6, 4), (7, 3), (7, 4)])
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
    # chão é pisável → não bloqueia; objeto sólido EMPILHADO sobre o chão → bloqueia
    r.decorations = [{"id": "c0", "type": "chao", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    check("chão não bloqueia (pisável)", r._blocks_tile(4, 4) is False)
    r.decorations = [
        {"id": "c1", "type": "chao",   "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False},
        {"id": "b1", "type": "barril", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False},
    ]
    r._rebuild_decor_index()
    check("barril sobre chão bloqueia", r._blocks_tile(4, 4) is True)

def test_objeto_chave():
    print("\n[A4b] objeto-chave em decoração")
    async def run():
        r = _room()
        r.decorations = [{"id": "d-chave", "type": "altar", "pos": [5, 5], "facing": [0, 1],
                          "loot": None, "tem_loot": False, "key_objective": True}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0); p["pos"] = [4, 5]; p["alive"] = True
        r.players = {"p1": p}
        await r.handle_interagir_decor("p1", "d-chave")
        check("interagir com decoração-chave conclui a chave", r.key_chest_opened is True)
        check("objetivo abrir baú-chave reconhece decoração", r._objetivo_cumprido({"type": "open_key_chest"}) is True)
        check("estado do cliente recebe marca de chave", r._serializar_decoracoes()[0].get("key_objective") is True)
    asyncio.run(run())

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

def test_chama_viva():
    print("\n[A5b] chama viva 2d4")
    async def run():
        r = _room()
        r.decorations = [{"id": "d0", "type": "chama_viva", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0)
        p["pos"] = [4, 4]; p["hp"] = 20; p["max_hp"] = 20; p["alive"] = True
        await r._aplicar_fogueira_se_pisar(p)
        check("herói perdeu entre 2 e 8 HP", 12 <= p["hp"] <= 18)
        p["pos"] = [0, 0]; hp0 = p["hp"]
        await r._aplicar_fogueira_se_pisar(p)
        check("sem dano fora da chama viva", p["hp"] == hp0)
        m = {"name": "Monstro de teste", "type": "goblin", "pos": [4, 4],
             "hp": 20, "max_hp": 20, "alive": True}
        await r._aplicar_fogueira_se_pisar(m)
        check("monstro também perdeu entre 2 e 8 HP", 12 <= m["hp"] <= 18)
    asyncio.run(run())

def test_brasa_chao():
    print("\n[A5c] brasa no chão 1 dano")
    async def run():
        r = _room()
        r.decorations = [{"id": "d0", "type": "brasa_chao", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0)
        p["pos"] = [4, 4]; p["hp"] = 20; p["max_hp"] = 20; p["alive"] = True
        await r._aplicar_fogueira_se_pisar(p)
        check("brasa causa exatamente 1 de dano", p["hp"] == 19)
    asyncio.run(run())

def test_fogo_imunidade_resistencia():
    print("\n[A5d] fogo: imunidade e resistência")
    async def run():
        r = _room()
        p = make_player("p1", "Herói", "warrior", 0)
        p["pos"] = [4, 4]; p["hp"] = 20; p["max_hp"] = 20; p["alive"] = True
        r.players = {"p1": p}
        antigo = server.roll_dice
        server.roll_dice = lambda expr: {"1d4": 4, "2d4": 8, "2d6": 6}.get(str(expr), antigo(expr))
        try:
            r.decorations = [{"id": "f", "type": "chama_viva", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
            r._rebuild_decor_index()
            p["immunities"] = [server.DMG_FIRE]; p["resistances"] = []
            await r._aplicar_fogueira_se_pisar(p)
            check("imunidade a fogo zera a Chama Viva", p["hp"] == 20)
            p["immunities"] = []; p["resistances"] = [{"type": server.DMG_FIRE, "mode": "half"}]
            await r._aplicar_fogueira_se_pisar(p)
            check("resistência reduz o fogo da Chama Viva pela metade", p["hp"] == 16)
            r.decorations = [{"id": "b", "type": "brasa_chao", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
            r._rebuild_decor_index(); p["resistances"] = [{"type": server.DMG_FIRE, "reduction": 1}]; p["hp"] = 20
            await r._aplicar_fogueira_se_pisar(p)
            check("resistência fixa também vale para a brasa", p["hp"] == 20)
            r.decorations = []; r.materiais = {(4, 4): "lava"}; p["resistances"] = [{"type": server.DMG_FIRE, "mode": "half"}]; p["hp"] = 20
            await r._aplicar_lava_se_pisar(p)
            check("resistência reduz o dano de lava", p["hp"] == 17)
        finally:
            server.roll_dice = antigo
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

def test_container_refresh():
    print("\n[A7b] container de loot — re-envio de decor_loot após take")
    async def run():
        r = _room()
        loot = {"gold": 10, "items": server.hidratar_itens_bau([{"id": "health_potion"}])}
        r.decorations = [{"id": "d0", "type": "barril", "pos": [5, 5], "facing": [0, 1], "loot": loot, "tem_loot": True}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0); p["pos"] = [4, 5]; p["gold"] = 0; p["bag"] = []; p["bag_size"] = 6; p["alive"] = True
        r.players = {"p1": p}

        sent = []
        async def _capture_send_to(pid, msg):
            sent.append((pid, msg))
        r.send_to = _capture_send_to

        # Pegar ouro → deve re-enviar decor_loot com gold zerado
        await r.handle_take_from_decor("p1", "d0", "gold", 0)
        decor_msgs = [m for pid, m in sent if m.get("type") == "decor_loot"]
        check("re-enviou decor_loot após pegar ouro", len(decor_msgs) == 1)
        check("decor_loot reflete gold zerado", decor_msgs[0]["gold"] == 0)
        check("decor_loot tem decor_id correto", decor_msgs[0]["decor_id"] == "d0")
        check("decor_loot ainda tem o item", len(decor_msgs[0]["items"]) == 1)

        # Pegar item → deve re-enviar decor_loot com items vazio
        sent.clear()
        await r.handle_take_from_decor("p1", "d0", "item", 0)
        decor_msgs2 = [m for pid, m in sent if m.get("type") == "decor_loot"]
        check("re-enviou decor_loot após pegar item", len(decor_msgs2) == 1)
        check("decor_loot reflete items vazio", decor_msgs2[0]["items"] == [])
        check("decor_loot gold ainda 0", decor_msgs2[0]["gold"] == 0)
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

def test_armadilha_decoracao():
    print("\n[A9b] armadilha em decoração")
    r = _room()
    r.traps, r.armadilhas = [], []
    r.decorations = [{"id": "d-trap", "type": "barril", "pos": [4, 4], "facing": [0, 1],
                      "loot": None, "tem_loot": False, "trap": {"tipo": "buraco"},
                      "trap_triggered": False, "trap_disarmed": False, "trap_revealed": False}]
    r._rebuild_decor_index()
    p = make_player("p1", "Luccas", "rogue", 0); p["pos"] = [2, 4]; p["alive"] = True
    found = r._revelar_armadilhas_raio(p, 3)
    payload = r._serializar_decoracoes()[0]
    check("Encontrar Armadilhas revela a decoração", found == 1 and r.decorations[0]["trap_revealed"])
    check("cliente recebe perigo revelado, sem configuração interna", payload.get("trap") is True and payload.get("trap_revealed") is True and "veneno_id" not in payload)

def test_bau_armadilha_ladino():
    print("\n[A9c] baú-armadilha: detecção e desarme do Ladino")
    r = _room()
    r._is_turn = lambda pid: True
    r.traps, r.armadilhas = [], []
    r.decorations = [{"id": "d-chest", "type": "arca_tesouros", "pos": [4, 4], "facing": [0, 1],
                      "loot": {"gold": 10, "items": []}, "tem_loot": True,
                      "key_objective": False, "chest_trap_monster_type": "goblin_combatente",
                      "chest_trap_triggered": False, "chest_trap_disarmed": False,
                      "trap": None, "trap_triggered": False, "trap_disarmed": False,
                      "trap_revealed": False}]
    r._rebuild_decor_index()
    p = make_player("p1", "Luccas", "rogue", 0); p["pos"] = [3, 4]; p["alive"] = True
    r.players[p["id"]] = p

    found = r._revelar_armadilhas_raio(p, 3)
    payload = r._serializar_decoracoes()[0]
    check("Detectar Armadilhas revela o baú", found == 1 and payload.get("chest_trap") is True
          and payload.get("trap_revealed") is True)

    original_randint = server.random.randint
    server.random.randint = lambda a, b: 20
    try:
        asyncio.run(r.handle_desarmar_armadilha("p1", {"tx": 4, "ty": 4}))
    finally:
        server.random.randint = original_randint
    check("desarme bem-sucedido impede o monstro", r.decorations[0]["chest_trap_disarmed"]
          and len(r.monsters) == 0)

    mensagens = []
    async def capturar(pid, msg): mensagens.append(msg)
    r.send_to = capturar
    asyncio.run(r.handle_interagir_decor("p1", "d-chest"))
    check("baú desarmado abre o loot", any(m.get("type") == "decor_loot" for m in mensagens))

def test_placa():
    print("\n[A9d] placa informativa")
    r = _room()
    r.decorations = [{"id": "d-placa", "type": "placa", "pos": [5, 5], "facing": [0, 1],
                      "texto": "Fraqueza: fogo.\nEvite a mordida.", "loot": None,
                      "tem_loot": False, "key_objective": False}]
    r._rebuild_decor_index()
    p = make_player("p1", "Pedro", "mage", 0); p["pos"] = [4, 5]; p["alive"] = True
    r.players[p["id"]] = p
    mensagens = []
    async def capturar(pid, msg): mensagens.append((pid, msg))
    r.send_to = capturar
    asyncio.run(r.handle_interagir_decor("p1", "d-placa"))
    msg = mensagens[0][1] if mensagens else {}
    check("interação envia a mensagem da placa", mensagens and mensagens[0][0] == "p1"
          and msg.get("type") == "decor_message")
    check("mensagem preserva quebras de linha", msg.get("texto") == "Fraqueza: fogo.\nEvite a mordida.")

def _defn_base():
    return {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 12, "h": 12},
        "tiles": [[FLOOR] * 12 for _ in range(12)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": None, "prisoner": None,
        "monsters": [], "chests": [], "traps": [], "decorations": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }

def test_validacao():
    print("\n[A10] validação")
    d = _defn_base()
    d["decorations"] = [{"type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": None}]
    ok, msg = server.validar_dungeon(d)
    check(f"válida com cama em chão ({msg})", ok is True)
    # tipo inválido
    d["decorations"] = [{"type": "xyz", "pos": [3, 3], "facing": [0, 1]}]
    ok, _ = server.validar_dungeon(d); check("rejeita tipo desconhecido", ok is False)
    # footprint em parede
    d2 = _defn_base()
    d2["tiles"][4][3] = WALL
    d2["decorations"] = [{"type": "cama", "pos": [3, 3], "facing": [0, 1]}]  # ocupa (3,3) e (3,4)→parede
    ok, _ = server.validar_dungeon(d2); check("rejeita footprint sobre parede", ok is False)
    # sobreposição entre decorações
    d3 = _defn_base()
    d3["decorations"] = [{"type": "barril", "pos": [5, 5], "facing": [0, 1]},
                         {"type": "barril", "pos": [5, 5], "facing": [0, 1]}]
    ok, _ = server.validar_dungeon(d3); check("rejeita sobreposição", ok is False)
    # chão (floor) é piso → pode coexistir com outro objeto na mesma casa
    d3b = _defn_base()
    d3b["decorations"] = [{"type": "chao", "pos": [5, 5], "facing": [0, 1]},
                          {"type": "barril", "pos": [5, 5], "facing": [0, 1]}]
    ok, _ = server.validar_dungeon(d3b); check("chão coexiste com objeto sólido", ok is True)
    # item de loot inválido
    d4 = _defn_base()
    d4["decorations"] = [{"type": "barril", "pos": [5, 5], "facing": [0, 1], "loot": {"gold": 0, "items": [{"id": "nope"}]}}]
    ok, _ = server.validar_dungeon(d4); check("rejeita item de loot inválido", ok is False)
    # fora do grid
    d5 = _defn_base()
    d5["decorations"] = [{"type": "fonte", "pos": [11, 11], "facing": [0, 1]}]  # 2x2 sai do grid
    ok, _ = server.validar_dungeon(d5); check("rejeita footprint fora do grid", ok is False)
    # pos não-int não pode levantar exceção (trust boundary)
    d6 = _defn_base()
    d6["decorations"] = [{"type": "cama", "pos": ["a", "b"]}]
    try:
        res = server.validar_dungeon(d6)
        raised = False
    except Exception:
        res = None; raised = True
    check("pos não-int não levanta exceção", raised is False and isinstance(res, tuple))
    check("rejeita pos não-int", (not raised) and res[0] is False)
    # gold de loot negativo
    d7 = _defn_base()
    d7["decorations"] = [{"type": "barril", "pos": [5, 5], "facing": [0, 1], "loot": {"gold": -5, "items": []}}]
    ok, _ = server.validar_dungeon(d7); check("rejeita gold de loot negativo", ok is False)
    # facing malformado
    d8 = _defn_base()
    d8["decorations"] = [{"type": "cama", "pos": [3, 3], "facing": "xx"}]
    ok, _ = server.validar_dungeon(d8); check("rejeita facing malformado", ok is False)
    # armadilha embutida válida e configuração obrigatória de veneno
    d9 = _defn_base()
    d9["decorations"] = [{"type": "barril", "pos": [5, 5], "facing": [0, 1], "trap": {"tipo": "buraco"}}]
    ok, _ = server.validar_dungeon(d9); check("aceita armadilha em decoração", ok is True)
    d9["decorations"][0]["trap"] = {"tipo": "fosso_envenenado"}
    ok, _ = server.validar_dungeon(d9); check("rejeita armadilha de decoração sem veneno", ok is False)
    d10 = _defn_base()
    d10["decorations"] = [{"type": "placa", "pos": [5, 5], "facing": [0, 1]}]
    ok, _ = server.validar_dungeon(d10); check("rejeita placa sem mensagem", ok is False)
    d10["decorations"][0]["texto"] = "Leia antes de entrar."
    ok, _ = server.validar_dungeon(d10); check("aceita placa com mensagem", ok is True)

def main():
    test_catalog()
    test_footprint()
    test_carga()
    test_bloqueio()
    test_objeto_chave()
    test_fogueira()
    test_chama_viva()
    test_brasa_chao()
    test_fogo_imunidade_resistencia()
    test_fonte()
    test_container()
    test_container_refresh()
    test_visao()
    test_serial()
    test_armadilha_decoracao()
    test_bau_armadilha_ladino()
    test_placa()
    test_validacao()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
