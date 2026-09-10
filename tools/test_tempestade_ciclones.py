"""Teste rápido da Tempestade de Ciclones em modo de protótipo."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0
def check(label, value):
    global PASS, FAIL
    if value: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")

def setup(level=5):
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    async def send_to(*a, **k): pass
    r.broadcast = noop; r.push_state = noop; r.gm_say = noop; r._broadcast_dado = noop; r.send_to = send_to
    r._tem_linha_de_visao = lambda *a, **k: True
    r._alcance_com_altura = lambda *a, **k: True
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.explored = {(x, y) for y in range(12) for x in range(12)}
    r.phase = "playing"; r.round_num = 1; r.monsters = {}; r.decorations = []
    r._rebuild_decor_index(); r.materiais = {}; r._rebuild_materiais_index()
    p = S.make_player("c", "Lewis", "cleric", 0)
    p.update(level=level, pos=[5, 5], alive=True, hp=100, max_hp=100,
             fome=50, sede=50, action_done=False, moves_left=6)
    p["magias_conhecidas"] = ["tempestade_ciclones"]
    r.players["c"] = p; r.player_order = ["c"]; r.initiative_active = True; r._rebuild_initiative()
    return r, p

async def main():
    r, p = setup(5)
    await r.handle_magia("c", {"magia_id":"tempestade_ciclones", "tx":5, "ty":5})
    z = next((z for z in r.zonas_especiais if z.get("tipo")=="tempestade_ciclones"), None)
    check("zona criada no nível 5", bool(z))
    check("área 4x4 no nível 5", z and z.get("lado") == 4 and len(z.get("tiles", [])) == 16)
    check("um ciclone no nível 5", z and len(z.get("ciclones", [])) == 1)
    check("ciclone ocupa 2x2", z and len(r._tempestade_ciclone_tiles(z["ciclones"][0])) == 4)
    check("vento custa 2", r._water_step_cost(p, 5, 6, [5, 5]) == 2)
    r.round_num = 2
    old = list(z["ciclones"][0]["pos"])
    await r.handle_tempestade_ciclones_mover("c", z["id"], 1, [old[0] + 1, old[1]])
    check("ciclone pode mover 2 casas", z["ciclones"][0]["pos"] != old)
    r.round_num = 3
    await r._processar_zonas_turno()
    check("raio periódico agendado para a rodada 3", z.get("proxima_descarga") == 5)
    print(f"\n{PASS} passaram, {FAIL} falharam")
    return 1 if FAIL else 0

sys.exit(asyncio.run(main()))
