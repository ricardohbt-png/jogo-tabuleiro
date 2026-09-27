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
    # Só quem tapa a visão: objeto alto e material opaco (o baixo não conta).
    objetos = r._decor_tall_tiles | r._mat_oclui_tiles | r._mat_solid_tiles
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

print("\n[2] objeto baixo (barril, mesa) NÃO tapa a visão — não faz sombra")
r = sala()
montar(r, [("barril", 7, 7), ("mesa_cadeiras", 9, 4), ("mesa_tortura", 4, 9)])
got, exp = comparar("objetos baixos", r, 5, 5, 6)
check("nenhuma sombra atrás de objeto baixo", not got and not exp)
check("o servidor vê por cima do barril", r._tem_linha_de_visao([5, 5], [9, 9]))
check("o barril continua barrando o passo", r._blocks_tile(7, 7))

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


# ── Meia cobertura ───────────────────────────────────────────────────────────
NODE_COB = r"""
const fs = require('fs'), vm = require('vm'), path = require('path');
const ctx = { console, setTimeout, clearTimeout };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(process.argv[1], 'src', 'gameState.js'), 'utf8'), ctx);
const GS = vm.runInContext('GS', ctx);
const { state, casos } = JSON.parse(fs.readFileSync(0, 'utf8'));
console.log(JSON.stringify(casos.map(([a, b]) => GS.coberturaBaixa(state, a, b))));
"""

def cobertura_cliente(r, casos):
    state = {"tiles": r.tiles, "decorations": r._serializar_decoracoes(),
             "materiais": r._serializar_materiais()}
    res = subprocess.run(["node", "-e", NODE_COB, RAIZ], input=json.dumps(
        {"state": state, "casos": casos}), capture_output=True, text=True, check=True)
    return json.loads(res.stdout)

print("\n[6] meia cobertura: cliente = servidor")
r = sala()
montar(r, [("barril", 8, 8), ("mesa_cadeiras", 4, 12), ("coluna", 12, 4), ("fogueira", 10, 10)])
casos = []
for ax, ay in [(3, 8), (8, 3), (3, 3), (13, 13), (5, 12), (8, 7), (2, 12)]:
    for bx, by in [(12, 8), (8, 13), (11, 11), (8, 9), (4, 14), (9, 8), (1, 14)]:
        if (ax, ay) != (bx, by):
            casos.append([{"pos": [ax, ay]}, {"pos": [bx, by]}])
srv = [r._cobertura_baixa_bonus(a, b) for a, b in casos]
cli = cobertura_cliente(r, casos)
check(f"{len(casos)} linhas: mesmas coberturas", srv == cli,
      str([(c[0]["pos"], c[1]["pos"], s1, c1) for c, s1, c1 in zip(casos, srv, cli) if s1 != c1][:5]))
check("há linhas com e sem cobertura no conjunto", 2 in srv and 0 in srv)
check("tiro por cima do barril: +2", r._cobertura_baixa_bonus({"pos": [3, 8]}, {"pos": [12, 8]}) == 2)
check("colado ao barril mas atacante adjacente ao alvo: sem cobertura",
      r._cobertura_baixa_bonus({"pos": [8, 9]}, {"pos": [8, 10]}) == 0)
check("o próprio alvo em cima do objeto não conta", r._cobertura_baixa_bonus({"pos": [3, 8]}, {"pos": [8, 8]}) == 0)
check("fogueira (pisável) não dá cobertura", r._cobertura_baixa_bonus({"pos": [7, 10]}, {"pos": [13, 10]}) == 0)
check("coluna (alta) não é cobertura — ela bloqueia a visão",
      r._cobertura_baixa_bonus({"pos": [12, 1]}, {"pos": [12, 7]}) == 0
      and not r._tem_linha_de_visao([12, 1], [12, 7]))
check("atacante no ar ignora a cobertura",
      r._cobertura_baixa_bonus({"pos": [3, 8], "altura": 2}, {"pos": [12, 8]}) == 0)
check("cliente: atacante no ar ignora",
      cobertura_cliente(r, [[{"pos": [3, 8], "altura": 2}, {"pos": [12, 8]}]]) == [0])

print("\n[7] ataques reais passam por cima e aplicam a cobertura")
import asyncio, random
import server as S

def sala_combate():
    r = sala(14, 14)
    r._falas = []
    async def fala(msg, *a, **k): r._falas.append(getattr(msg, "key", str(msg)))
    async def noop(*a, **k): pass
    r.gm_say = fala; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    r._is_turn = lambda pid: True
    r.phase = "playing"
    montar(r, [("barril", 4, 1)])   # antes da sala: montar() zera r.rooms
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 14, "h": 14, "cx": 7, "cy": 7, "locked": False}]
    r.chests = {}; r.ground_items = {}
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["pos"] = [1, 1]; p["atk_bonus"] = 50; p["alive"] = True; p["connected"] = True
    r.connections["p1"] = object()
    r.monsters["m1"] = {"id": "m1", "name": "Alvo", "type": "orc", "hp": 999, "ac": 1,
                        "pos": [7, 1], "alive": True, "special_abilities": [],
                        "alertado": True, "room_id": "r0"}
    return r, p

r, p = sala_combate()
p["weapon"] = {"id": "arco_curto", "name": "Arco Curto", "die": "1d6", "stat": "dex", "range": 8, "categoria": "perfurante"}
p["gear"]["off_hand"] = {"id": "flechas", "name": "Flechas", "effect": "ammo", "ammo_type": "flechas", "ammo_count": 10}
random.seed(5)
asyncio.run(r.handle_attack("p1", "m1"))
check("herói atira por cima do barril (há linha de visão)", p.get("action_done"))
check("narra a meia cobertura do alvo", "narracao.cobertura_baixa" in r._falas)

r, p = sala_combate()
r.monsters["m1"]["pos"] = [2, 1]
p["weapon"] = {"id": "espada", "name": "Espada", "die": "1d8", "stat": "str_", "categoria": "cortante"}
asyncio.run(r.handle_attack("p1", "m1"))
check("corpo a corpo adjacente: sem cobertura", "narracao.cobertura_baixa" not in r._falas)

r, p = sala_combate()
mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "goblin_arqueiro")
m = S.make_monster(mdef, r.rooms[0]); m["id"] = "g1"; m["pos"] = [7, 1]; m["room_id"] = "r0"; m["alertado"] = True
r.monsters = {"g1": m}
asyncio.run(r._execute_one_monster_attack(m, dict(m["attacks"][0]), {"kind": "player", "obj": p}))
check("arqueiro inimigo: o herói atrás do barril ganha a cobertura", "narracao.cobertura_baixa" in r._falas)

print("\n[8] reclassificação dos objetos")
check("mesa de tortura é baixa", S.DECOR_TYPES["mesa_tortura"]["alto"] is False)
check("lareira é alta", S.DECOR_TYPES["lareira"]["alto"] is True)
check("carroça é alta", S.DECOR_TYPES["carroca"]["alto"] is True)

print(f"\n{PASS} passaram, {FAIL} falharam")
sys.exit(1 if FAIL else 0)
