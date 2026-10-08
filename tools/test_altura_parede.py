"""Altura manual de parede (`alturas_parede`, só visual).
Roda da raiz: python tools/test_altura_parede.py"""
import sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S
from server import GameRoom

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def dungeon(alturas=None, elevacoes=None):
    """Masmorra 6x5: borda de parede, miolo de chão."""
    tiles = [[S.FLOOR] * 6 for _ in range(5)]
    for x in range(6):
        tiles[0][x] = S.WALL; tiles[4][x] = S.WALL
    for y in range(5):
        tiles[y][0] = S.WALL; tiles[y][5] = S.WALL
    d = {
        "schema_version": 1, "id": "alt", "name": "Altura",
        "grid": {"w": 6, "h": 5}, "tiles": tiles,
        "entrance": {"x": 1, "y": 1},
        "rooms": [{"id": "r1", "x": 1, "y": 1, "w": 4, "h": 3,
                   "role": "entrance", "doors": []}],
        "monsters": [], "decorations": [], "chests": [], "traps": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }
    if alturas is not None: d["alturas_parede"] = alturas
    if elevacoes is not None: d["elevacoes"] = elevacoes
    return d

print("\n[1] Validação")
ok, msg = S.validar_dungeon(dungeon({"0,0": 3, "5,2": 0, "2,4": 10}))
check("parede com 0, 3 e 10 é aceita", ok is True)
ok, msg = S.validar_dungeon(dungeon())
check("sem o campo continua válido", ok is True)
ok, msg = S.validar_dungeon(dungeon({"2,2": 3}))
check("altura em casa de chão é recusada", ok is False and "parede" in msg)
ok, msg = S.validar_dungeon(dungeon({"0,0": S.ELEVACAO_TERRENO_MAX + 1}))
check("acima do teto de elevação é recusada", ok is False)
ok, msg = S.validar_dungeon(dungeon({"0,0": -1}))
check("negativo é recusado (−1 só existe no editor, para voltar ao automático)", ok is False)
ok, msg = S.validar_dungeon(dungeon({"0,0": True}))
check("booleano é recusado", ok is False)
ok, msg = S.validar_dungeon(dungeon({"9,9": 2}))
check("fora do grid é recusado", ok is False)
ok, msg = S.validar_dungeon(dungeon({"a,b": 2}))
check("chave malformada é recusada", ok is False)
ok, msg = S.validar_dungeon(dungeon([1, 2]))
check("lista no lugar do mapa é recusada", ok is False)

print("\n[2] Carga e payload")
r = GameRoom("ALT")
r.phase = "playing"
r.load_authored_dungeon(dungeon({"0,0": 3, "5,2": 0}, {"2,2": 4}))
check("carga guarda as alturas por casa", r.alturas_parede == {(0, 0): 3, (5, 2): 0})
check("altura de parede não vira elevação de terreno",
      r.elevacoes == {(2, 2): 4} and r._elevacao_terreno(0, 0) == 0)
p = r._game_state_payload()
check("game_state leva alturas_parede", p.get("alturas_parede") == {"0,0": 3, "5,2": 0})
check("o 0 vai no payload (trava a parede ao lado de um platô)", p["alturas_parede"].get("5,2") == 0)
r2 = GameRoom("ALT2"); r2.phase = "playing"
r2.load_authored_dungeon(dungeon())
check("masmorra sem o campo carrega vazio", r2.alturas_parede == {}
      and r2._game_state_payload().get("alturas_parede") == {})

print("\n[3] Foto e prévia")
check("alturas_parede está em FOTO_SALA_CATEGORIAS como foto",
      S.FOTO_SALA_CATEGORIAS.get("alturas_parede") == "foto")
ok, st, avisos = S._preview_dungeon_state(dungeon({"0,0": 5}))
check("a prévia do editor leva o campo", ok and st.get("alturas_parede") == {"0,0": 5})

print("\n[4] Editor grava e lê o campo")
ed = open(os.path.join(RAIZ, "tools", "editor.js"), encoding="utf-8").read()
check("buildJSON grava alturas_parede", "alturas_parede: Object.fromEntries(Object.entries(S.alturasParede)" in ed)
check("loadJSON lê alturas_parede", "obj.alturas_parede" in ed)
check("a ferramenta de altura pinta parede", "S.alturasParede[key] = value" in ed)

print(f"\n{PASS} ok, {FAIL} falha(s)")
sys.exit(1 if FAIL else 0)
