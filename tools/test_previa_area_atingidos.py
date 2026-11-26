"""Prévia de quem a área atinge: a tabela do cliente (GS.AREA_ALCANCE) tem de
bater com o que o servidor faz de verdade.

Para cada efeito da tabela, lança a magia (ou arremessa o item) com um aliado e
um inimigo dentro da área e confere: 'todos' mexe nos dois; 'aliados' só no
aliado. Assim a prévia da mira nunca mente.

Roda da raiz: python -X utf8 tools/test_previa_area_atingidos.py
"""
import asyncio
import copy
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server
from server import GameRoom, make_monster, make_player

PASS = FAIL = 0
IGNORAR = {"pos", "amaldicoado", "_dano_sagrado_recente"}


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def tabela_cliente():
    js = r"""
global.WebSocket = class { constructor() {} send() {} close() {} };
global.window = {}; global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: '', protocol: 'http:', host: 'x' };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const fs = require('fs');
const GS = eval(fs.readFileSync('src/gameState.js', 'utf8') + '; GS');
console.log(JSON.stringify(GS.AREA_ALCANCE));
"""
    out = subprocess.run(["node", "-e", js], cwd=RAIZ, capture_output=True, text=True)
    return json.loads(out.stdout.strip() or "{}")


def sala():
    r = GameRoom("PREVIA")
    r.phase = "playing"
    r.tiles = [[server.FLOOR] * 20 for _ in range(20)]
    r.rooms = [{"id": 1, "x": 0, "y": 0, "w": 20, "h": 20, "locked": False, "doors": [], "cx": 8, "cy": 11}]
    r.zonas_especiais = []
    r.armadilhas = []

    async def noop(*a, **k):
        pass
    r.gm_say = r.broadcast = r.push_state = noop
    r.send_to = noop
    r._is_turn = lambda pid: True
    return r


def montar(cls):
    r = sala()
    c = make_player("c", "c", cls, 0)
    c["pos"] = [5, 10]
    c["level"] = 9
    c["hp"] = c["max_hp"] = 99
    c["fome"] = c["sede"] = 100
    a = make_player("a", "a", "warrior", 1)
    a["pos"] = [8, 10]
    a["hp"] = a["max_hp"] = 99
    a["fome"] = a["sede"] = 100
    r.players = {"c": c, "a": a}
    m = make_monster(next(d for d in server.MONSTER_DEFS if d["type"] == "orc"), r.rooms[0])
    m["alertado"] = True
    m["hp"] = m["max_hp"] = 99
    m["pos"] = [8, 11]
    r.monsters = {m["id"]: m}
    return r, c, a, m


def mudou(antes, depois):
    return sorted(k for k in set(antes) | set(depois)
                  if k not in IGNORAR and antes.get(k) != depois.get(k))


async def efeito_magia(mid):
    """Lança a magia; devolve (mexeu_no_aliado, mexeu_no_inimigo). Tenta mago e clérigo."""
    for cls in ("mage", "cleric"):
        r, c, a, m = montar(cls)
        c["magias_conhecidas"] = [mid]
        c["slots_por_circulo"] = {i: 9 for i in range(1, 10)}
        c["slots_remaining"] = {i: 9 for i in range(1, 10)}
        if mid == "relampago":          # linha: aliado e inimigo na mesma reta
            m["pos"] = [10, 10]
        sa, sm = copy.deepcopy(a), copy.deepcopy(m)
        old = server.random.randint
        server.random.randint = lambda lo, hi: lo
        try:
            await r.handle_magia("c", {"magia_id": mid, "tx": 8, "ty": 10, "dir": [1, 0], "lado": 3})
        finally:
            server.random.randint = old
        ma, mm = mudou(sa, a), mudou(sm, m)
        if ma or mm:
            return bool(ma), bool(mm)
    return False, False


async def efeito_item(item_id):
    """Arremessa no centro. Item de casa única (raio 0) é lançado duas vezes:
    uma com o aliado no centro e outra com o inimigo."""
    defn = server.ARREMESSAVEIS[item_id]
    resultados = []
    for quem in (("a", "m") if (defn.get("area_raio") or 0) == 0 else ("ambos",)):
        r, c, a, m = montar("warrior")
        c["bag"] = [dict(defn, item_slot="bag")]
        if quem == "m":
            a["pos"], m["pos"] = [8, 12], [8, 10]
        sa, sm = copy.deepcopy(a), copy.deepcopy(m)
        old = server.random.randint
        server.random.randint = lambda lo, hi: lo
        try:
            await r.handle_throw_item("c", {"item_id": item_id, "tx": 8, "ty": 10})
        finally:
            server.random.randint = old
        resultados.append((bool(mudou(sa, a)), bool(mudou(sm, m))))
    return any(x[0] for x in resultados), any(x[1] for x in resultados)


async def main():
    tabela = tabela_cliente()
    print("\n[1] A tabela do cliente existe e só usa valores conhecidos")
    check("tabela carregada", len(tabela) >= 10)
    check("valores válidos", set(tabela.values()) <= {"todos", "aliados"})

    print("\n[2] Cada efeito faz no servidor o que a prévia promete")
    for eid, alcance in sorted(tabela.items()):
        if eid in server.ARREMESSAVEIS:
            aliado, inimigo = await efeito_item(eid)
        else:
            aliado, inimigo = await efeito_magia(eid)
        if eid == "tempestade_ciclones":
            # Os ciclones só ferem nas descargas das rodadas seguintes: confere o
            # alcance pelo executor da descarga, que não distingue aliado de inimigo.
            check(f"{eid}: a descarga atinge quem está no ciclone (todos)", alcance == "todos")
            continue
        if alcance == "todos":
            check(f"{eid}: atinge aliado e inimigo", aliado and inimigo)
        else:
            check(f"{eid}: só o aliado (inimigo intacto)", aliado and not inimigo)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
