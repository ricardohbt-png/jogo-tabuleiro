"""Teste de persistência da masmorra entre idas à cidade.

Bug original: enter_dungeon regenerava o mapa em TODA entrada e nunca limpava
self.monsters/traps/armadilhas/explored — então, ao voltar da cidade, a masmorra
mudava e monstros antigos reapareciam sobre paredes do novo mapa.

Regra correta: ao sair pela escada e voltar, a masmorra deve permanecer
EXATAMENTE igual. Só gera nova na 1ª entrada ou após concluída (boss → end_game).

Roda da raiz: python tools/test_persistencia_masmorra.py
Stuba a camada de rede do GameRoom para testar a lógica isoladamente."""
import asyncio, copy, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, WALL

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    # dois heróis
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.phase = "city"
    return r

def monstros_em_parede(r):
    return [m for m in r.monsters.values()
            if r.tiles[m["pos"][1]][m["pos"][0]] == WALL]

async def main():
    print("\n[1] Primeira entrada gera a masmorra")
    r = setup()
    await r.enter_dungeon("p1")
    check("dungeon_generated = True após gerar", r.dungeon_generated is True)
    check("mapa gerado", r.tiles is not None)
    check("monstros spawnados", len(r.monsters) > 0)
    check("nenhum monstro em parede ao gerar", monstros_em_parede(r) == [])

    # ── Simula jogo: mata 1 monstro, move outro, revela névoa, abre baú/porta ──
    print("\n[2] Simula progresso na masmorra")
    ids = list(r.monsters.keys())
    morto_id = ids[0]
    del r.monsters[morto_id]                       # monstro derrotado
    vivo = r.monsters[ids[1]]
    # move o vivo 1 casa para uma casa de chão livre adjacente, se houver
    vx, vy = vivo["pos"]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = vx+dx, vy+dy
        if 0 <= ny < len(r.tiles) and 0 <= nx < len(r.tiles[0]) and r.tiles[ny][nx] != WALL:
            vivo["pos"] = [nx, ny]; break
    r.explored.add((0, 0))                          # revela uma casa "manualmente"
    r.chests["c_test"] = {"id": "c_test", "pos": [vivo["pos"][0], vivo["pos"][1]], "aberto": False}
    if r.rooms:
        r.rooms[-1]["locked"] = False               # "abriu" uma porta/sala

    snap_tiles    = copy.deepcopy(r.tiles)
    snap_rooms    = copy.deepcopy(r.rooms)
    snap_monsters = copy.deepcopy(r.monsters)
    snap_explored = set(r.explored)
    snap_chests   = copy.deepcopy(r.chests)

    print("\n[3] Sai para a cidade e retorna")
    await r.handle_exit_dungeon("p1")
    check("phase volta para city ao sair", r.phase == "city")
    await r.enter_dungeon("p1")
    check("phase volta para playing ao reentrar", r.phase == "playing")

    print("\n[4] Masmorra permanece EXATAMENTE igual")
    check("mapa idêntico", r.tiles == snap_tiles)
    check("salas idênticas (portas abertas preservadas)", r.rooms == snap_rooms)
    check("monstros idênticos (mortos continuam mortos, posições preservadas)",
          r.monsters == snap_monsters)
    check("monstro derrotado não ressuscitou", morto_id not in r.monsters)
    check("névoa (explored) preservada", snap_explored.issubset(r.explored))
    check("baús preservados", r.chests == snap_chests)
    check("NENHUM monstro em parede após reentrar", monstros_em_parede(r) == [])
    check("não regenerou (dungeon_generated segue True)", r.dungeon_generated is True)

    print("\n[5] Concluir a masmorra (boss) libera uma nova")
    await r.end_game(victory=True)
    check("dungeon_generated = False após vitória", r.dungeon_generated is False)
    r.phase = "city"
    tiles_antigo = copy.deepcopy(r.tiles)
    await r.enter_dungeon("p1")
    check("nova masmorra é gerada após concluída", r.tiles != tiles_antigo or len(r.monsters) > 0)
    check("nenhum monstro em parede na nova masmorra", monstros_em_parede(r) == [])

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
