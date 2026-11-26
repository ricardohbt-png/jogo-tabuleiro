"""Câmara de Gás numa área sem sala autorada (casa da viela, Resgate de Elara).

A Câmara enche a SALA da armadilha. Quando o autor não desenhou uma sala ali,
o gás ocupa a área de chão fechada em volta da armadilha (paredes e portas
limitam). Antes o disparo não achava sala e não fazia nada.

Roda da raiz: python -X utf8 tools/test_camara_gas_sem_sala.py
"""
import asyncio
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
from server import GameRoom, make_player

PASS = FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def sala_casa():
    defn = json.load(open(os.path.join(RAIZ, "dungeons", "casa_secreta.json"), encoding="utf-8"))
    room = GameRoom("GAS")
    room.load_authored_dungeon(defn)
    room.phase = "playing"
    room.sent = []

    async def noop(*a, **k):
        pass

    async def capture(pid, msg):
        room.sent.append((pid, msg))

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = capture
    return room


def heroi(pid, cls, pos, slot):
    p = make_player(pid, pid, cls, slot)
    p["pos"] = list(pos)
    p["hp"] = p["max_hp"] = 40
    return p


def falhar_sempre():
    old = server.random.randint
    server.random.randint = lambda a, b: 1 if b == 20 else 3
    return old


async def main():
    print("\n[1] O mapa real: a armadilha fica fora de qualquer sala desenhada")
    room = sala_casa()
    gas = next(a for a in room.armadilhas if a.get("tipo") == "camara_gas")
    check("armadilha de gás carregada em [6,8]", list(gas["pos"]) == [6, 8])
    check("nenhuma sala contém a armadilha", room._room_containing_point(gas["pos"]) is None)

    print("\n[2] Pisar na armadilha enche o quarto e afeta quem está nele")
    a = heroi("a", "warrior", gas["pos"], 0)
    b = heroi("b", "mage", [8, 7], 1)
    c = heroi("c", "cleric", [8, 13], 2)      # sala de entrada, do outro lado da porta
    room.players = {"a": a, "b": b, "c": c}
    old = falhar_sempre()
    try:
        await room._disparar_armadilha(a, gas)
    finally:
        server.random.randint = old
    zonas = [z for z in room.zonas_especiais if z.get("tipo") == "camara_gas"]
    check("a zona de gás foi criada", len(zonas) == 1)
    zona = zonas[0] if zonas else {}
    casas = {tuple(t) for t in zona.get("tiles", [])}
    quarto = {(x, y) for x in range(6, 10) for y in range(6, 9)}
    check("o gás cobre o quarto fechado (x6–9, y6–8)", casas == quarto)
    check("o gás não passa pela porta [5,8]", (5, 8) not in casas)
    check("quem pisou sofre o gás", a["hp"] == 37)
    check("quem está no mesmo quarto sofre o gás", b["hp"] == 37)
    check("quem está do outro lado da porta não sofre", c["hp"] == 40)

    print("\n[3] Início do turno: o tick vale dentro do quarto, não fora")
    b["pos"] = [9, 6]
    c["pos"] = [8, 13]
    old = falhar_sempre()
    try:
        await room._processar_camara_gas_inicio_turno(b)
        await room._processar_camara_gas_inicio_turno(c)
    finally:
        server.random.randint = old
    check("tick dentro do quarto", b["hp"] == 34)
    check("tick fora do quarto não acontece", c["hp"] == 40)

    print("\n[4] Fogo no quarto detona o gás (a reação conhece as casas)")
    check("as casas do gás são as do quarto", room._rx_gas_tiles(zona) == quarto)

    print("\n[5] A lareira desliga a armadilha antes do disparo")
    room = sala_casa()
    lareira = next(d for d in room.decorations if d.get("type") == "lareira")
    check("a lareira desliga a armadilha de gás",
          "trap_4" in (lareira.get("disable_trap_ids") or []))

    print("\n[6] Sala desenhada continua igual (sem casas próprias)")
    room = GameRoom("SALA")
    room.phase = "playing"
    room.rooms = [{"id": "r1", "x": 0, "y": 0, "w": 5, "h": 5, "locked": False, "doors": []}]
    room.tiles = [[1] * 6 for _ in range(6)]
    room.zonas_especiais = []
    room.gm_say = room.broadcast = room.push_state = room.send_to = (lambda *a, **k: asyncio.sleep(0))
    p = heroi("p", "warrior", [2, 2], 0)
    room.players = {"p": p}
    arm = {"id": "g", "tipo": "camara_gas", "pos": [2, 2], "ativada": False}
    room.armadilhas = [arm]
    old = falhar_sempre()
    try:
        await room._disparar_armadilha(p, arm)
    finally:
        server.random.randint = old
    z = room.zonas_especiais[0] if room.zonas_especiais else {}
    check("com sala, a zona usa a sala (room_id) e não grava casas",
          z.get("room_id") == "r1" and not z.get("tiles"))

    print("\n[7] Cliente: o gás sem sala usa as casas da zona")
    js = r"""
global.window = {};
require('./src/reacoesElementais.js');
const R = window.ReacoesElementais;
const tiles = []; for (let y = 0; y < 10; y++) tiles.push(new Array(12).fill(1));
const st = { tiles, rooms: [], materiais: {}, zonas_especiais: [
  { ativa: true, tipo: 'camara_gas', room_id: null, tiles: [[6,6],[7,6],[6,7]] } ] };
const r = R.preverReacoes(st, 'fire', [[6,6]]);
console.log(JSON.stringify(r.gas || []));
"""
    out = subprocess.run(["node", "-e", js], cwd=RAIZ, capture_output=True, text=True)
    check("a mira prevê a explosão nas casas do gás", out.stdout.strip() == "[[6,6],[7,6],[6,7]]")
    game = open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()
    check("a nuvem de fumaça usa as casas da zona quando não há sala",
          "_fumacaTilesGas(state,z)" in game)
    check("o realce verde usa as casas da zona quando não há sala",
          "for (const c of (z.tiles || []))" in game)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
