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

async def entrar_na_masmorra(r, pid="p1", nova=False):
    """Entra na masmorra E libera a transição autoritativa de 3 s.

    Desde que o `enter_dungeon` passou a abrir a janela `dungeon_intro_active`,
    o `current_pid()` devolve None enquanto ela está de pé e TODA ação é
    recusada — é a transição que o jogador vê. O teste não pode dormir 3 s nem
    mexer nos flags na mão: chama a mesma liberação que o jogo chama, que
    também inicia o turno (`_activate_initiative_actor`)."""
    await r.enter_dungeon(pid)
    await r._liberar_intro_masmorra(nova)

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

def iniciativa_jogadores(r):
    """Isola a rotação de turnos entre os HERÓIS. O sistema atual
    (`initiative_order`, Modo Mestre Fase A) intercala monstros na iniciativa,
    então logo após `enter_dungeon` o ator da vez costuma ser um monstro e
    `current_pid()` é None. Aqui neutralizamos os monstros e reconstruímos a
    iniciativa só com jogadores — que, sendo idênticos, mantêm a ordem
    p1→p2→p3 pelo desempate de sequência (equivale ao antigo turn_index). Testa
    exatamente o alvo desta suíte: desconexão/pulo/avanço entre heróis."""
    if r.initiative_task and not r.initiative_task.done():
        r.initiative_task.cancel()
    r.initiative_task = None
    r.monsters.clear()
    r._rebuild_initiative()
    r.initiative_index = 0
    # Reinicia o timer do herói da vez. Sem isso, se um MONSTRO tivesse a maior
    # iniciativa em enter_dungeon (ramo de monstro cancela o timer), o estado do
    # timer ficaria None — flaky. É o mesmo passo final de _start_initiative_player_turn.
    r._iniciar_timer_turno()

async def main():
    print("\n[1] enter_dungeon inicia o timer do turno")
    r = setup()
    await entrar_na_masmorra(r, "p1")
    iniciativa_jogadores(r)
    check("timer iniciado (started_ms definido)", r.turn_timer_started_ms is not None)
    check("tarefa de timer criada", r.turn_timer_task is not None)
    check("current = primeiro da ordem", r.current_pid() == "p1")

    print("\n[2] Desconexão de jogador que NÃO é a vez → é pulado")
    r = setup()
    await entrar_na_masmorra(r, "p1")            # vez de p1
    iniciativa_jogadores(r)
    await r.handle_disconnect_em_jogo("p2")      # p2 cai (não é a vez)
    check("p2 marcado desconectado", r.players["p2"]["connected"] is False)
    check("p2 saiu do tabuleiro (pos -1,-1)", r.players["p2"]["pos"] == [-1, -1])
    check("ainda é a vez de p1 (não mudou)", r.current_pid() == "p1")
    await r.handle_end_turn("p1")                # p1 encerra → deve pular p2
    check("turno pulou p2 e foi para p3", r.current_pid() == "p3")

    print("\n[3] Desconexão de QUEM é a vez → turno avança sozinho")
    r = setup()
    await entrar_na_masmorra(r, "p1")
    iniciativa_jogadores(r)
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
    # agora a ordem não deve mais pular p1 — reconstrói a iniciativa (só heróis)
    # com p1 novamente ativo, começando por ele.
    iniciativa_jogadores(r)
    # dá uma volta completa e confirma que p1 aparece como vez novamente
    vistos = set()
    for _ in range(6):
        await r.handle_end_turn(r.current_pid())
        vistos.add(r.current_pid())
    check("p1 volta a entrar na ordem de turnos", "p1" in vistos)

    print("\n[5] _forcar_fim_turno encerra igual ao end_turn manual")
    r = setup()
    await entrar_na_masmorra(r, "p1")
    iniciativa_jogadores(r)
    antes = r.current_pid()
    await r._forcar_fim_turno(antes)
    check("forçar fim avança o turno", r.current_pid() != antes)
    check("forçar fim em quem não é a vez não faz nada",
          await _no_change(r))

    print("\n[6] Timer de 30s esgota → encerra o turno automaticamente")
    r = setup(limit=0.05)                        # 50ms p/ não esperar
    await entrar_na_masmorra(r, "p1")
    iniciativa_jogadores(r)
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
