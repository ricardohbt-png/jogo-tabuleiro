"""Testes da Fase 1 do editor de masmorras: validação + carregador + seleção.
Roda da raiz: python tools/test_dungeon_loader.py"""
import asyncio, copy, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, WALL, FLOOR, DOOR, validar_dungeon
from server import (hidratar_itens_bau, make_authored_trap,
                    listar_dungeons, carregar_dungeon)

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sample_dungeon():
    """Masmorra mínima 8×6: 1 sala 'entrance' (4×4) com 1 porta.
    Layout (x→, y↓), 0=WALL 1=FLOOR 2=DOOR:
      linha 0: 0 0 0 0 0 0 0 0
      linha 1: 0 1 1 1 1 0 0 0
      linha 2: 0 1 1 1 1 2 1 0
      linha 3: 0 1 1 1 1 0 0 0
      linha 4: 0 1 1 1 1 0 0 0
      linha 5: 0 0 0 0 0 0 0 0
    """
    W, H = 8, 6
    tiles = [[0]*W for _ in range(H)]
    for y in range(1, 5):
        for x in range(1, 5):
            tiles[y][x] = FLOOR
    tiles[2][5] = DOOR
    tiles[2][6] = FLOOR
    return {
        "schema_version": 1, "id": "amostra", "name": "Amostra",
        "grid": {"w": W, "h": H}, "tiles": tiles,
        "rooms": [{"id": 0, "x": 1, "y": 1, "w": 4, "h": 4,
                   "role": "entrance", "locked": False, "doors": [[5, 2]]}],
        "entrance": {"x": 2, "y": 2},
        "exit": {"x": 6, "y": 2},
        "monsters": [{"type": "goblin", "pos": [3, 3], "room_id": 0,
                      "boss": False, "target": False}],
        "chests": [{"pos": [2, 3], "gold": 20,
                    "items": [{"id": "health_potion"}], "key_objective": False}],
        "traps": [{"tipo": "fosso_estacas", "pos": [4, 1]}],
        "prisoner": {"pos": [4, 4], "room_id": 0},
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }

def test_validacao():
    print("\n[1] validar_dungeon")
    ok, msg = validar_dungeon(sample_dungeon())
    check("masmorra válida passa", ok is True)

    d = sample_dungeon(); d["schema_version"] = 99
    ok, _ = validar_dungeon(d); check("schema_version inválido recusa", ok is False)

    d = sample_dungeon(); d["monsters"][0]["type"] = "inexistente"
    ok, _ = validar_dungeon(d); check("monstro tipo desconhecido recusa", ok is False)

    d = sample_dungeon(); d["monsters"][0]["pos"] = [0, 0]   # WALL
    ok, _ = validar_dungeon(d); check("monstro em parede recusa", ok is False)

    d = sample_dungeon(); d["monsters"][0]["room_id"] = 99
    ok, _ = validar_dungeon(d); check("room_id inexistente recusa", ok is False)

    d = sample_dungeon(); d["chests"][0]["items"][0]["id"] = "naoexiste"
    ok, _ = validar_dungeon(d); check("item de baú desconhecido recusa", ok is False)

    d = sample_dungeon(); d["rooms"][0]["doors"] = [[1, 1]]   # FLOOR, não DOOR
    ok, _ = validar_dungeon(d); check("porta que não é DOOR recusa", ok is False)

    d = sample_dungeon(); d["traps"][0] = {"tipo": "fosso_envenenado", "pos": [4, 1]}
    ok, _ = validar_dungeon(d); check("fosso_envenenado sem veneno_id recusa", ok is False)

    d = sample_dungeon(); d["tiles"] = d["tiles"][:-1]   # 5 linhas, grid.h=6
    ok, _ = validar_dungeon(d); check("tiles com nº de linhas errado recusa", ok is False)

    # ── Robustez: JSON malformado deve recusar SEM levantar exceção ──
    def recusa_sem_crashar(nome, d):
        try:
            ok, _ = validar_dungeon(d)
            check(nome, ok is False)
        except Exception as e:
            check(f"{nome} (levantou {type(e).__name__})", False)

    def nao_crasha(nome, d):
        # null onde se espera lista é tratado como vazio (válido) — só não pode crashar
        try:
            validar_dungeon(d); check(nome, True)
        except Exception as e:
            check(f"{nome} (levantou {type(e).__name__})", False)

    d = sample_dungeon(); d["rooms"] = ["x"]
    recusa_sem_crashar("sala não-dict recusa sem crashar", d)
    d = sample_dungeon(); d["monsters"] = ["x"]
    recusa_sem_crashar("monstro não-dict recusa sem crashar", d)
    d = sample_dungeon(); d["chests"][0]["gold"] = "abc"
    recusa_sem_crashar("gold não-numérico recusa sem crashar", d)
    d = sample_dungeon(); d["prisoner"] = "x"
    recusa_sem_crashar("prisoner não-dict recusa sem crashar", d)
    d = sample_dungeon(); d["chests"][0]["items"] = None
    nao_crasha("items=None tratado como vazio sem crashar", d)
    d = sample_dungeon(); d["rooms"][0]["doors"] = None
    nao_crasha("doors=None tratado como vazio sem crashar", d)

def test_helpers():
    print("\n[2] helpers (hidratação / trap / arquivos)")
    itens = hidratar_itens_bau([{"id": "health_potion"}])
    check("hidratação devolve dict completo", itens and itens[0]["name"] == "Poção de Vida")
    check("hidratação ignora id inexistente", hidratar_itens_bau([{"id": "x"}]) == [])

    arm = make_authored_trap({"tipo": "fosso_estacas", "pos": [4, 1]})
    check("trap autorada: tipo certo", arm["tipo"] == "fosso_estacas")
    check("trap autorada: hostil e oculta",
          arm["aliada"] is False and arm["visivel"] is False
          and arm["ativada"] is False and arm["so_luccas"] is False)
    arm2 = make_authored_trap({"tipo": "fosso_envenenado", "pos": [4, 1],
                               "veneno_id": "veneno_aranha_sombria"})
    check("trap envenenada guarda veneno_id", arm2.get("veneno_id") == "veneno_aranha_sombria")

def setup_room(cls_list=(("p1", "Victor", "warrior"), ("p2", "Pedro", "mage"))):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in cls_list:
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"; r.phase = "city"
    return r

def monstros_em_parede(r):
    return [m for m in r.monsters.values()
            if r.tiles[m["pos"][1]][m["pos"][0]] == WALL]

async def test_grid_procedural():
    print("\n[3] grid dinâmico — regressão procedural")
    r = setup_room()
    check("default map_w/map_h = 30",
          getattr(r, "map_w", None) == 30 and getattr(r, "map_h", None) == 30)
    check("modo default = procedural", getattr(r, "mode", None) == "procedural")
    check("selected_dungeon/dungeon_def default = None",
          getattr(r, "selected_dungeon", "x") is None and getattr(r, "dungeon_def", "x") is None)
    await r.enter_dungeon("p1")
    check("procedural não altera o modo", r.mode == "procedural")
    check("procedural ainda gera 30×30",
          len(r.tiles) == 30 and len(r.tiles[0]) == 30)
    check("map_w/map_h batem com tiles após procedural",
          r.map_w == len(r.tiles[0]) and r.map_h == len(r.tiles))
    check("procedural: nenhum monstro em parede", monstros_em_parede(r) == [])

async def test_load_authored():
    print("\n[4] load_authored_dungeon")
    r = setup_room()
    r.mode = "authored"
    r.dungeon_def = sample_dungeon()      # injeta direto (Task 5 faz via arquivo)
    r.selected_dungeon = "amostra.json"
    # patch: enter_dungeon usará r.dungeon_def quando authored (ver Step 3)
    await r.enter_dungeon("p1")

    check("grid autorado aplicado (8×6)", r.map_w == 8 and r.map_h == 6)
    check("tiles têm as dimensões do grid",
          len(r.tiles) == 6 and len(r.tiles[0]) == 8)
    check("1 monstro carregado", len(r.monsters) == 1)
    m = next(iter(r.monsters.values()))
    check("monstro na casa exata autorada", m["pos"] == [3, 3])
    check("monstro vinculado à sala 0", m["room_id"] == 0)
    check("authored_boss inerte (m['boss'] falsy)", not m.get("boss"))
    check("1 baú carregado com item hidratado",
          len(r.chests) == 1 and
          next(iter(r.chests.values()))["items"][0]["name"] == "Poção de Vida")
    check("baú com ouro exato", next(iter(r.chests.values()))["gold"] == 20)
    check("1 armadilha carregada", len(r.armadilhas) == 1 and
          r.armadilhas[0]["tipo"] == "fosso_estacas")
    check("nenhum monstro em parede", monstros_em_parede(r) == [])
    # heróis: todos em casas de chão (não parede), próximos à entrada
    casas = [tuple(p["pos"]) for p in r.players.values()]
    check("heróis em casas de chão", all(r.tiles[y][x] != WALL for x, y in casas))
    check("stairs na entrada", r.stairs_pos == [2, 2])
    check("dungeon_def guardado p/ Fase 3", r.dungeon_def is not None
          and r.dungeon_def.get("prisoner") is not None)
    check("entrada revelada (névoa)", (2, 2) in r.explored)

async def test_select_dungeon():
    print("\n[5] handle_select_dungeon")
    r = setup_room(); r.phase = "lobby"
    captura = {}
    async def cap_lobby(): captura["called"] = True
    r.broadcast_lobby = cap_lobby

    await r.handle_select_dungeon("p1", "amostra.json")
    check("modo vira authored", r.mode == "authored")
    check("arquivo selecionado guardado", r.selected_dungeon == "amostra.json")
    check("rebroadcast do lobby", captura.get("called") is True)

    await r.handle_select_dungeon("p1", None)
    check("None volta para procedural", r.mode == "procedural" and r.selected_dungeon is None)

    # não-host não altera
    r.mode = "procedural"
    await r.handle_select_dungeon("p2", "amostra.json")
    check("não-host é ignorado", r.mode == "procedural")

async def test_arquivo_disco():
    print("\n[6] integração via arquivo em dungeons/")
    listadas = listar_dungeons()
    check("test_fase1.json aparece em listar_dungeons",
          any(d["file"] == "test_fase1.json" for d in listadas))
    defn = carregar_dungeon("test_fase1.json")
    check("carrega o arquivo", defn is not None)
    ok, msg = validar_dungeon(defn)
    check(f"arquivo é válido ({msg})", ok is True)
    # path traversal é barrado
    check("path traversal recusado", carregar_dungeon("../server.py") is None)

    r = setup_room(); r.mode = "authored"; r.dungeon_def = defn
    r.selected_dungeon = "test_fase1.json"
    await r.enter_dungeon("p1")
    check("grid do arquivo aplicado",
          r.map_w == defn["grid"]["w"] and r.map_h == defn["grid"]["h"])
    check("nenhum monstro em parede (arquivo)", monstros_em_parede(r) == [])

async def main():
    test_validacao()
    test_helpers()
    await test_grid_procedural()
    await test_load_authored()
    await test_select_dungeon()
    await test_arquivo_disco()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
