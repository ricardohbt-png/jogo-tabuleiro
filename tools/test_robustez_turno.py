"""Robustez da cadeia de turnos: uma falha isolada NAO pode congelar a partida.

Contexto: a cadeia de iniciativa roda em tasks soltas (asyncio.create_task) cujo
unico elo de continuidade e o `_advance_initiative()` no fim de `monster_step`.
Sem protecao, qualquer excecao na IA de um monstro (ou num processador de virada
de rodada) mata a cadeia: ninguem mais recebe turno, o processo segue vivo
servindo HTTP e nada e impresso -- porque a task fica presa em
`self.initiative_task` e o aviso do Python nunca e emitido.

Roda da raiz: python tools/test_robustez_turno.py
"""
import asyncio, io, os, sys
from contextlib import redirect_stderr

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, make_monster, MONSTER_DEFS

OK = FAIL = 0
def check(rotulo, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print("  OK  ", rotulo)
    else:    FAIL += 1; print("  XX  ", rotulo, extra)

async def noop(*a, **k): pass

def montar(com_monstro=True):
    r = GameRoom("ROBUSTEZ")
    r.phase = "playing"
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r.rooms = []; r.door_rooms = {}; r.zonas_especiais = []; r.armadilhas = []
    p = make_player("p1", "Heroi", "warrior", 0)
    p["pos"] = [1, 1]; p["alive"] = True; p["connected"] = True
    r.players = {"p1": p}; r.player_order = ["p1"]
    if com_monstro:
        m = make_monster(MONSTER_DEFS[0], {"id": "r", "cx": 3, "cy": 3})
        m["id"] = "m1"; m["pos"] = [3, 3]; m["hp"] = 10
        r.monsters = {"m1": m}
    else:
        r.monsters = {}
    r.initiative_active = True
    r._rebuild_initiative()
    return r, p

def vez_do_monstro(r):
    i = next(k for k, e in enumerate(r.initiative_order) if e["kind"] == "monster")
    r.initiative_index = i

async def main():
    print("[1] A IA de um monstro estoura -- a vez tem de seguir adiante")
    r, p = montar()
    vez_do_monstro(r)
    antes = r.initiative_index
    async def ia_quebrada(monster):
        raise KeyError("bug qualquer dentro da IA")
    r.gm_phase = ia_quebrada
    erro = io.StringIO()
    with redirect_stderr(erro):
        await r._activate_initiative_actor()
        await r.initiative_task   # aguarda a task, em vez de dormir um tempo fixo
    check("a iniciativa avancou apesar da excecao", r.initiative_index != antes,
          f"(indice preso em {antes})")
    check("alguem recebeu a vez", r.current_pid() == "p1", f"(current_pid={r.current_pid()})")
    check("a task do turno nao morreu carregando a excecao",
          r.initiative_task.done() and r.initiative_task.exception() is None)
    texto = erro.getvalue()
    check("o traceback foi impresso (a falha nao e silenciosa)",
          "KeyError" in texto and "Traceback" in texto, f"(stderr={texto[:80]!r})")

    print()
    print("[2] Um processador de virada de rodada estoura -- a rodada tem de virar")
    r, p = montar()
    r.initiative_index = len(r.initiative_order) - 1
    rodada0 = r.round_num
    chamou_depois = []
    async def chamas_quebrada():
        raise NameError("name 'arm' is not defined")
    async def acido_ok():
        chamou_depois.append("acido")
    r._processar_em_chamas_turno = chamas_quebrada
    r._processar_acido_residual_turno = acido_ok
    r.gm_phase = noop
    with redirect_stderr(io.StringIO()):
        await r._advance_initiative()
        await asyncio.sleep(0.05)
    check("a rodada avancou", r.round_num == rodada0 + 1, f"(round={r.round_num})")
    check("os processadores seguintes ainda rodaram", chamou_depois == ["acido"])
    check("a vez foi entregue a alguem", r.current_actor() is not None)

    print()
    print("[3] O timeout da janela Manual estoura -- a janela tem de fechar")
    r, p = montar()
    m = r.monsters["m1"]
    r.master_manual_mid = m["id"]
    r.master_manual_event = asyncio.Event()
    r.master_manual_deadline = S.time.monotonic() - 1   # ja vencido
    async def ia_quebrada2(monster):
        raise ValueError("estouro dentro da IA do timeout")
    r.gm_phase = ia_quebrada2
    with redirect_stderr(io.StringIO()):
        await r._master_manual_timeout(m["id"])
    check("o evento foi liberado (a janela nao ficou travada)",
          r.master_manual_event.is_set())

    print()
    print("[4] O turno licantropo estoura -- a cadeia tem de seguir adiante")
    # Aqui o invariante e "o elo da cadeia foi acionado", nao "o indice mudou":
    # com todos os atores automatizados a cadeia CICLA (lobo falha -> avanca ->
    # monstro age -> avanca -> lobo falha...), entao o indice e alvo movel.
    r, p = montar(com_monstro=False)
    p["licantropia_transformado"] = True
    r._rebuild_initiative()
    r.initiative_index = 0
    chamou = []
    async def advance_espiao():
        chamou.append(True)
    r._advance_initiative = advance_espiao
    async def lobo_quebrado(alvo):
        raise RuntimeError("estouro no turno do lobo")
    r._turno_licantropo = lobo_quebrado
    with redirect_stderr(io.StringIO()):
        await r._activate_initiative_actor()
        await r.initiative_task
    check("a cadeia seguiu apesar da excecao", chamou == [True], f"(chamou={chamou})")
    print()
    print("[5] _isolar NAO pode engolir CancelledError")
    # Se alguem trocar o `except Exception` por `except BaseException`, o
    # cancelamento dos timers (_cancelar_timer_turno e irmaos) para de
    # funcionar em silencio: a task cancelada seguiria rodando ate o fim.
    r, p = montar()
    async def dorme_muito():
        await asyncio.sleep(30)
    tarefa = asyncio.create_task(r._isolar(dorme_muito(), "teste de cancelamento"))
    await asyncio.sleep(0.01)
    tarefa.cancel()
    cancelou = False
    try:
        await tarefa
    except asyncio.CancelledError:
        cancelou = True
    check("o cancelamento atravessa o _isolar", cancelou)

    print()
    print(f"===== {OK} OK / {FAIL} FALHAS =====")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
