"""Atravessar aliados — opção da sala (só o anfitrião liga).

Roda da raiz:  python tools/test_atravessar_aliados.py

REGRA
  • Desligada (padrão): nada muda — herói, servo e prisioneiro bloqueiam.
  • Ligada: um CAMINHO (move_path / mover_animado_caminho /
    mover_prisioneiro_caminho) pode passar pela casa de um herói, servo
    animado ou prisioneiro liberto, mas o destino final precisa estar livre.
  • Passo isolado (setas) para dentro de um aliado continua recusado.
  • Caminho interrompido em cima de alguém volta à última casa livre.
  • Monstros e o prisioneiro ainda preso continuam bloqueando sempre.
  • O prisioneiro passa a ocupar a casa também para os heróis (antes um herói
    podia parar em cima dele).
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


async def montar(ligada=False, classe="warrior"):
    """Corredor aberto 6×3; herói p1 em (1,1); p2 parado longe, em (5,0)."""
    r = S.GameRoom("ATRAVESSAR")
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop
    r.players["p1"] = S.make_player("p1", "Ana", classe, 0)
    r.players["p2"] = S.make_player("p2", "Bia", "rogue", 1)
    r.phase = "city"; r.host_pid = "p1"
    await r.enter_dungeon("p1")
    r.monsters.clear()
    r.dungeon_intro_active = False
    r._intro_masmorra_bloqueada = lambda: False
    r._is_turn = lambda pid: pid == "p1"
    r.erros = []
    async def send_to(pid, msg):
        if msg.get("type") == "error": r.erros.append(str(msg.get("msg")))
    async def push_state(): pass
    async def broadcast(msg, skip=None): pass
    r.send_to = send_to; r.push_state = push_state; r.broadcast = broadcast
    r.map_w, r.map_h = 6, 3
    r.tiles = [[S.FLOOR] * 6 for _ in range(3)]
    r.decorations = []
    r._decor_block_tiles = set(); r._decor_tall_tiles = set(); r._decor_low_tiles = set()
    r._mat_solid_tiles = set()
    r.traps = []; r.armadilhas = []
    r.prisoner = None
    r.atravessar_aliados = ligada
    p1, p2 = r.players["p1"], r.players["p2"]
    p1.update({"pos": [1, 1], "moves_left": 20, "facing": [1, 0]})
    p2.update({"pos": [5, 0], "moves_left": 20})
    return r


def servo(r, dono, pos, **extra):
    a = {"id": "a1", "owner": dono, "pos": list(pos), "vida_atual": 8, "vida_max": 8,
         "moves_left": 6, "movimento": 6, "tipo": "skeleton", "nome": "Esqueleto",
         "porte": "medio", "acted": False}
    a.update(extra)
    r.players[dono].setdefault("animados", []).append(a)
    return a


def prisioneiro(r, pos, freed=True):
    r.prisoner = {"pos": list(pos), "alive": True, "freed": freed, "rescuer_pid": "p1",
                  "hp": 7, "max_hp": 7, "ac": 10, "moves_left": 6}
    return r.prisoner


async def main():
    print("\n[1] Opção desligada: nada muda")
    r = await montar(False); r.players["p2"]["pos"] = [2, 1]
    await r.handle_move_path("p1", [[1, 0], [1, 0]])
    check("herói no caminho bloqueia o caminho", r.players["p1"]["pos"] == [1, 1], r.erros)

    print("\n[2] Opção ligada: atravessa herói, servo e prisioneiro liberto")
    for rotulo, prep in (
        ("herói", lambda r: r.players["p2"].__setitem__("pos", [2, 1])),
        ("servo animado", lambda r: servo(r, "p2", [2, 1])),
        ("prisioneiro liberto", lambda r: prisioneiro(r, [2, 1], True)),
    ):
        r = await montar(True); prep(r)
        await r.handle_move_path("p1", [[1, 0], [1, 0]])
        check(f"atravessa {rotulo} e chega à casa livre", r.players["p1"]["pos"] == [3, 1], r.erros)
        r = await montar(True); prep(r)
        await r.handle_move_path("p1", [[1, 0]])
        check(f"caminho que TERMINA no {rotulo} é recusado sem andar",
              r.players["p1"]["pos"] == [1, 1] and r.erros, r.erros)
        r = await montar(True); prep(r)
        await r.handle_move("p1", 1, 0)
        check(f"passo isolado para dentro do {rotulo} é recusado", r.players["p1"]["pos"] == [1, 1])

    print("\n[3] O que continua bloqueando com a opção ligada")
    r = await montar(True)
    r.monsters["m1"] = {"id": "m1", "type": "goblin", "name": "Goblin", "hp": 5, "max_hp": 5,
                        "pos": [2, 1], "size": [1, 1], "ac": 10}
    await r.handle_move_path("p1", [[1, 0], [1, 0]])
    check("monstro bloqueia", r.players["p1"]["pos"] == [1, 1])
    r = await montar(True); prisioneiro(r, [2, 1], freed=False)
    await r.handle_move_path("p1", [[1, 0], [1, 0]])
    check("prisioneiro ainda preso bloqueia", r.players["p1"]["pos"] == [1, 1])

    print("\n[4] O prisioneiro ocupa a casa também com a opção desligada")
    r = await montar(False); prisioneiro(r, [2, 1], True)
    await r.handle_move("p1", 1, 0)
    check("herói não para em cima do prisioneiro", r.players["p1"]["pos"] == [1, 1], r.erros)

    print("\n[5] Caminho interrompido em cima de um aliado volta à última casa livre")
    r = await montar(True); r.players["p2"]["pos"] = [2, 1]
    r.players["p1"]["moves_left"] = 1
    await r.handle_move_path("p1", [[1, 0], [1, 0]])
    check("sem movimento para sair: recua para (1,1)", r.players["p1"]["pos"] == [1, 1],
          r.players["p1"]["pos"])
    r = await montar(True); r.players["p2"]["pos"] = [3, 1]
    r.players["p1"]["moves_left"] = 2
    await r.handle_move_path("p1", [[1, 0], [1, 0], [1, 0]])
    check("recua para a ÚLTIMA casa livre do caminho, (2,1)", r.players["p1"]["pos"] == [2, 1],
          r.players["p1"]["pos"])

    print("\n[6] Servo e prisioneiro: caminho numa mensagem só")
    r = await montar(True); r.animados_phase_pid = "p1"
    a = servo(r, "p1", [0, 1])
    await r.handle_mover_animado_caminho("p1", "a1", [[1, 0], [1, 0], [1, 0]])
    check("servo atravessa o herói e chega a (3,1)", a["pos"] == [3, 1], r.erros)
    r = await montar(False); r.animados_phase_pid = "p1"
    a = servo(r, "p1", [0, 1])
    await r.handle_mover_animado_caminho("p1", "a1", [[1, 0], [1, 0]])
    check("desligada: o servo para antes do herói", a["pos"] == [0, 1], a["pos"])
    r = await montar(True); r.animados_phase_pid = "p1"
    a = servo(r, "p1", [0, 1], moves_left=1)
    await r.handle_mover_animado_caminho("p1", "a1", [[1, 0], [1, 0]])
    check("servo sem movimento para sair recua", a["pos"] == [0, 1], a["pos"])
    r = await montar(True); r.animados_phase_pid = "p1"
    pr = prisioneiro(r, [0, 1], True)
    await r.handle_mover_prisioneiro_caminho("p1", [[1, 0], [1, 0], [1, 0]])
    check("prisioneiro atravessa o herói e chega a (3,1)", pr["pos"] == [3, 1], r.erros)
    r = await montar(True); r.animados_phase_pid = "p1"
    pr = prisioneiro(r, [0, 1], True)
    await r.handle_mover_prisioneiro_caminho("p1", [[1, 0]])
    check("prisioneiro não termina em cima do herói", pr["pos"] == [0, 1] and r.erros, r.erros)

    print("\n[7] Comandar servos (automático) atravessa e nunca termina em cima")
    for ligada, esperado in ((True, [3, 1]), (False, [0, 1])):
        r = await montar(ligada, classe="mage"); r.animados_phase_pid = "p1"
        r.players["p1"]["pos"] = [0, 0]
        r.players["p2"]["pos"] = [1, 1]
        a = servo(r, "p1", [0, 1], moves_left=3, movimento=3)
        r.monsters["m1"] = {"id": "m1", "type": "goblin", "name": "Goblin", "hp": 50, "max_hp": 50,
                            "pos": [4, 1], "size": [1, 1], "ac": 30}
        await r.handle_comandar_animados("p1")
        check(f"{'ligada' if ligada else 'desligada'}: servo termina em {esperado}",
              a["pos"] == esperado, a["pos"])
    r = await montar(True, classe="mage"); r.animados_phase_pid = "p1"
    r.players["p1"]["pos"] = [0, 0]; r.players["p2"]["pos"] = [1, 1]
    a = servo(r, "p1", [0, 1], moves_left=2, movimento=2)
    r.monsters["m1"] = {"id": "m1", "type": "goblin", "name": "Goblin", "hp": 50, "max_hp": 50,
                        "pos": [4, 1], "size": [1, 1], "ac": 30}
    await r.handle_comandar_animados("p1")
    check("com 2 de movimento atravessa até (2,1), fora do aliado", a["pos"] == [2, 1], a["pos"])

    print("\n[8] Só o anfitrião muda; vai no estado e no jogo salvo")
    r = await montar(False)
    await r.handle_set_atravessar_aliados("p2", True)
    check("jogador comum é recusado", r.atravessar_aliados is False and r.erros, r.erros)
    r.phase = "playing"
    await r.handle_set_atravessar_aliados("p1", True)
    check("anfitrião liga", r.atravessar_aliados is True)
    check("vai no game_state", r._game_state_payload().get("atravessar_aliados") is True)
    r.savegame = {}
    r._checkpoint_savegame()
    check("vai para o jogo salvo", r.savegame.get("atravessar_aliados") is True)
    check("padrão de sala nova é desligado", S.GameRoom("X").atravessar_aliados is False)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
