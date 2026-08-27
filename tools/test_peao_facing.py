"""Peão vira na direção do movimento — facing do jogador.
Roda da raiz: python tools/test_peao_facing.py"""
import asyncio, sys, os, json
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
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

def forcar_turno(r, pid):
    """Posiciona a INICIATIVA no herói `pid` (sistema atual). Os turnos são
    regidos por `initiative_order`/`initiative_index` desde o Modo Mestre Fase A,
    e a iniciativa intercala MONSTROS — logo após `enter_dungeon` o `current_pid()`
    costuma ser um monstro, e `handle_move` recusaria o passo."""
    r.initiative_active = True
    if not r.initiative_order:
        r._rebuild_initiative()
    idx = next((i for i, e in enumerate(r.initiative_order)
                if e["kind"] == "player" and e["id"] == pid), None)
    if idx is not None:
        r.initiative_index = idx
    return idx

def fixture():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_fase3.json"), encoding="utf-8") as f:
        return json.load(f)

def setup_authored():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.mode = "authored"; r.dungeon_def = fixture()
    r.phase = "city"
    return r

async def main():
    print("\n[1] handle_move grava facing = [dx,dy] a cada passo")
    r = setup_authored()
    await entrar_na_masmorra(r, "p1")
    forcar_turno(r, "p1")
    p = r.players["p1"]
    check("facing ausente antes do 1º passo", "facing" not in p)

    # Posição/tiles controlados: independe do layout real da fixture.
    p["pos"] = [5, 5]
    p["moves_left"] = 6
    r.tiles[5][5] = S.FLOOR
    r.tiles[5][6] = S.FLOOR
    await r.handle_move("p1", 1, 0)
    check("posição avançou 1 casa a leste", p["pos"] == [6, 5])
    check("facing = [1,0] (leste)", p.get("facing") == [1, 0])

    r.tiles[4][6] = S.FLOOR
    await r.handle_move("p1", 0, -1)
    check("facing = [0,-1] (norte) após o passo seguinte", p.get("facing") == [0, -1])

    print("\n[2] enter_dungeon reseta facing ao (re)entrar na masmorra")
    check("facing setado antes do reset (sanity)", "facing" in p)
    r.phase = "city"                   # simula volta pra cidade
    r.dungeon_generated = True         # reentrada na MESMA masmorra (nova=False)
    await entrar_na_masmorra(r, "p1")
    check("facing limpo ao reentrar na masmorra", "facing" not in r.players["p1"])

    print(f"\n{'='*50}\nPASS={PASS} FAIL={FAIL}")
    if FAIL: sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
