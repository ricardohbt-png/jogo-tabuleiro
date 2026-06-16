"""Testa o tratamento de desconexão/saída no meio da partida e o timer de turno.

Regras:
- Jogador que cai/sai durante a partida: personagem deixa a masmorra (pos fora
  do tabuleiro), `connected=False`, é PULADO na ordem de turnos; se era a vez
  dele, o turno avança — os outros continuam.
- Reconexão: `connected=True`, personagem reentra (volta à ordem de turnos).
- Timer de 30s por turno: ao esgotar, o turno encerra automaticamente.

Roda da raiz: python tools/test_turnos_desconexao.py
Stuba a camada de rede do GameRoom."""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup(n=3, limit=999):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    r.TURN_LIMIT_S = limit   # evita o timer real disparar durante o teste
    for i in range(n):
        pid = f"p{i+1}"
        r.players[pid] = make_player(pid, f"Hero{i+1}", "warrior", 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.phase = "city"
    return r

async def main():
    print("\n[1] enter_dungeon inicia o timer do turno")
    r = setup()
    await r.enter_dungeon("p1")
    check("timer iniciado (started_ms definido)", r.turn_timer_started_ms is not None)
    check("tarefa de timer criada", r.turn_timer_task is not None)
    check("current = primeiro da ordem", r.current_pid() == "p1")

    print("\n[2] Desconexão de jogador que NÃO é a vez → é pulado")
    r = setup()
    await r.enter_dungeon("p1")                  # vez de p1
    await r.handle_disconnect_em_jogo("p2")      # p2 cai (não é a vez)
    check("p2 marcado desconectado", r.players["p2"]["connected"] is False)
    check("p2 saiu do tabuleiro (pos -1,-1)", r.players["p2"]["pos"] == [-1, -1])
    check("ainda é a vez de p1 (não mudou)", r.current_pid() == "p1")
    await r.handle_end_turn("p1")                # p1 encerra → deve pular p2
    check("turno pulou p2 e foi para p3", r.current_pid() == "p3")

    print("\n[3] Desconexão de QUEM é a vez → turno avança sozinho")
    r = setup()
    await r.enter_dungeon("p1")
    check("pré: vez de p1", r.current_pid() == "p1")
    await r.handle_disconnect_em_jogo("p1")      # cai no próprio turno
    check("p1 desconectado", r.players["p1"]["connected"] is False)
    check("turno avançou para p2 (outros continuam)", r.current_pid() == "p2")
    check("host migrou de p1 para um conectado", r.host_pid != "p1" and r.players[r.host_pid]["connected"])

    print("\n[4] Reconexão → volta à ordem de turnos")
    # p1 reconecta: replica o efeito do handler de rejoin
    ent = next(rm for rm in r.rooms if rm["role"] == "entrance")
    r.players["p1"]["connected"] = True
    r.players["p1"]["pos"] = [ent["cx"], ent["cy"]]
    check("p1 reconectado e reposicionado na entrada",
          r.players["p1"]["connected"] and r.players["p1"]["pos"] == [ent["cx"], ent["cy"]])
    # agora a ordem não deve mais pular p1
    r.turn_index = 0
    while not r._ativo(r.players[r.current_pid()]):
        r.turn_index += 1
    # dá uma volta completa e confirma que p1 aparece como vez novamente
    vistos = set()
    for _ in range(6):
        await r.handle_end_turn(r.current_pid())
        vistos.add(r.current_pid())
    check("p1 volta a entrar na ordem de turnos", "p1" in vistos)

    print("\n[5] _forcar_fim_turno encerra igual ao end_turn manual")
    r = setup()
    await r.enter_dungeon("p1")
    antes = r.current_pid()
    await r._forcar_fim_turno(antes)
    check("forçar fim avança o turno", r.current_pid() != antes)
    check("forçar fim em quem não é a vez não faz nada",
          await _no_change(r))

    print("\n[6] Timer de 30s esgota → encerra o turno automaticamente")
    r = setup(limit=0.05)                        # 50ms p/ não esperar
    await r.enter_dungeon("p1")
    antes = r.current_pid()
    r._iniciar_timer_turno()
    await r.turn_timer_task                       # aguarda UMA expiração (determinístico)
    r._cancelar_timer_turno()                     # impede o re-disparo encadeado do limite minúsculo
    check("turno encerrou sozinho ao esgotar o tempo", r.current_pid() != antes)

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

async def _no_change(r):
    cur = r.current_pid()
    nao_vez = next(p for p in r.player_order if p != cur)
    await r._forcar_fim_turno(nao_vez)   # não é a vez dele → no-op
    return r.current_pid() == cur

if __name__ == "__main__":
    asyncio.run(main())
