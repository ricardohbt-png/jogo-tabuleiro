"""Sombra dos objetos (penumbra) — paridade cliente × servidor.

O cliente (GS.sombraDeObjetos, src/gameState.js) marca as casas que o herói
VERIA se um objeto não tapasse a linha de visão. Esse conjunto tem de bater
casa a casa com o que o servidor deixa de revelar por causa de um objeto
(`_reveal_around` → `_tem_linha_de_visao` + `_tall_oclui_caminho`); senão a
sombra mente — escurece casa que o servidor revela, ou deixa preta uma casa
que só um objeto esconde.

Roda da raiz: python tools/test_sombra_objetos.py
"""
import json, os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from server import GameRoom, WALL, FLOOR  # noqa: E402

PASS = 0; FAIL = 0
def check(nome, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {nome}")
    else:    FAIL += 1; print(f"  ❌ {nome} {extra}")

NODE = r"""
const fs = require('fs'), vm = require('vm'), path = require('path');
const ctx = { console, setTimeout, clearTimeout };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(process.argv[1], 'src', 'gameState.js'), 'utf8'), ctx);
const GS = vm.runInContext('GS', ctx);
const { state, hero, raio } = JSON.parse(fs.readFileSync(0, 'utf8'));
const mapa = GS.sombraDeObjetos(state, hero, raio);
console.log(JSON.stringify([...mapa.values()]));
"""


def sala(w=18, h=18):
    r = GameRoom("SOMBRA")
    r.map_w, r.map_h = w, h
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.rooms = []
    r.players = {}
    r.monsters = {}
    r.decorations = []
    r.materiais = {}
    return r


def montar(r, decs, mats=None, paredes=(), trancadas=()):
    for (x, y) in paredes:
        r.tiles[y][x] = WALL
    for i, (tipo, x, y) in enumerate(decs):
        r.decorations.append({"id": f"d{i}", "type": tipo, "pos": [x, y], "facing": [0, 1]})
    r.materiais = dict(mats or {})
    r.rooms = [dict(id=i, x=x, y=y, w=w, h=h, locked=True, role="monster", doors=[])
               for i, (x, y, w, h) in enumerate(trancadas)]
    r._rebuild_decor_index()
    r._rebuild_materiais_index()


def esperado_servidor(r, hx, hy, raio):
    """Casas que um objeto esconde, pela regra do próprio servidor."""
    r.explored = set()
    r._reveal_around(hx, hy, radius=raio)
    objetos = r._decor_block_tiles | r._decor_tall_tiles | r._mat_oclui_tiles | r._mat_solid_tiles
    out = set()
    for y in range(max(0, hy - raio), min(r.map_h, hy + raio + 1)):
        for x in range(max(0, hx - raio), min(r.map_w, hx + raio + 1)):
            if (x, y) == (hx, hy) or r.tiles[y][x] == WALL or (x, y) in objetos:
                continue
            if r._tile_in_locked_room(x, y) or (x, y) in r.explored:
                continue
            if r._tem_linha_de_visao([hx, hy], [x, y], ignorar_objetos=True):
                out.add((x, y))
    return out


def cliente(r, hx, hy, raio):
    hero = {"id": "h1", "pos": [hx, hy], "alive": True, "altura": 0}
    r.players = {"h1": hero}
    state = {"tiles": r.tiles, "decorations": r._serializar_decoracoes(),
             "materiais": r._serializar_materiais(), "rooms": r.rooms,
             "revealed": [], "players": [hero], "monsters": [], "explored": []}
    res = subprocess.run(["node", "-e", NODE, RAIZ], input=json.dumps(
        {"state": state, "hero": hero, "raio": raio}), capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def comparar(nome, r, hx, hy, raio):
    exp = esperado_servidor(r, hx, hy, raio)
    got = cliente(r, hx, hy, raio)
    gset = {(c["x"], c["y"]) for c in got}
    check(f"{nome}: cliente = servidor ({len(exp)} casas)", gset == exp,
          f"só cliente={sorted(gset - exp)} só servidor={sorted(exp - gset)}")
    return got, exp


print("\n[1] coluna alta à frente do herói projeta sombra atrás dela")
r = sala()
montar(r, [("coluna", 8, 8)])
got, exp = comparar("coluna", r, 5, 8, 6)
check("há sombra atrás da coluna", (9, 8) in exp and (10, 8) in exp)
check("a própria coluna não é sombreada", (8, 8) not in {(c["x"], c["y"]) for c in got})
check("a sombra aponta a coluna como causa",
      all(c["objeto"] == {"tipo": "decor", "id": "coluna"} for c in got))

print("\n[2] objeto baixo e sólido (barril) também tapa a visão")
r = sala()
montar(r, [("barril", 7, 7)])
comparar("barril", r, 5, 5, 6)

print("\n[3] estante 1x2 + entulho + parede + sala trancada juntos")
r = sala()
montar(r, [("estante", 9, 4), ("coluna", 4, 10)],
       mats={(11, 11): "entulho"},
       paredes=[(12, y) for y in range(0, 8)],
       trancadas=[(14, 12, 4, 4)])
got, exp = comparar("cenário misto", r, 8, 8, 7)
check("atrás da parede NÃO vira sombra (é névoa normal)", (13, 3) not in exp)
check("dentro da sala trancada NÃO vira sombra", not any(x >= 14 and y >= 12 for (x, y) in exp))
check("entulho aparece como causa", any(c["objeto"] == {"tipo": "material", "id": "entulho"} for c in got))

check("toda casa sombreada tem uma causa identificada",
      all(c["objeto"] for c in got))

print("\n[4] sem objetos, não há sombra")
r = sala()
montar(r, [])
got, exp = comparar("mapa vazio", r, 5, 5, 6)
check("nenhuma casa sombreada", not got and not exp)

print("\n[5] várias posições do herói ao redor de um aglomerado")
r = sala()
montar(r, [("coluna", 8, 8), ("barril", 9, 9), ("estante", 6, 10)], mats={(10, 7): "entulho"})
for (hx, hy) in [(3, 3), (13, 13), (8, 3), (3, 12), (12, 8)]:
    comparar(f"herói em {hx},{hy}", r, hx, hy, 6)

print(f"\n{PASS} passaram, {FAIL} falharam")
sys.exit(1 if FAIL else 0)
