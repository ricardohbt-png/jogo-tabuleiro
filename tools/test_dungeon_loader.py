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

async def main():
    test_validacao()
    test_helpers()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
