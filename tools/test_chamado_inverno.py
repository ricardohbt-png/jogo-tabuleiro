"""Testes da magia Chamado do Inverno (conjuração e caminhos de movimento).

Roda da raiz:
    python -X utf8 tools/test_chamado_inverno.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup(lado=14, real_los=False):
    r = S.GameRoom("TEST"); errs = []

    async def noop(*a, **k):
        pass

    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(str(msg.get("msg", "")))
    r.broadcast = noop; r.push_state = noop; r.gm_say = noop; r.send_to = cap
    if not real_los:
        r._tem_linha_de_visao = lambda *a, **k: True
        r._alcance_com_altura = lambda *a, **k: True
    r.phase = "playing"; r.round_num = 1; r._errs = errs
    r.map_w = r.map_h = lado
    r.tiles = [[S.FLOOR] * lado for _ in range(lado)]
    r.explored = {(x, y) for y in range(lado) for x in range(lado)}
    r.monsters = {}; r.decorations = []; r._rebuild_decor_index()
    r.materiais = {}; r._rebuild_materiais_index()
    return r


def lewis(r, nivel=5, pos=(1, 1)):
    p = S.make_player("c", "Lewis", "cleric", 0)
    p.update(level=nivel, pos=list(pos), alive=True, hp=50, max_hp=50,
             fome=40, sede=40, action_done=False)
    p["magias_conhecidas"] = ["chamado_inverno"]
    r.players["c"] = p; r.player_order = ["c"]
    r.initiative_active = True; r._rebuild_initiative()
    return p


async def main():
    print("\n[1] Mira inválida não cobra slot, 🍖/💧 nem ação (preflight)")
    # Só terreno e custo do permanente eram pré-validados; alcance/parede/chão
    # ficavam no executor, depois de handle_magia cobrar tudo.
    r = setup(real_los=True); c = lewis(r, nivel=5, pos=(1, 1))

    def recursos(p):
        return (r._slots_disponiveis(p, "segundo"), p["fome"], p["sede"], p["action_done"])

    async def tenta(dados):
        r._errs.clear()
        await r.handle_magia("c", {"magia_id": "chamado_inverno", "terreno": "piso_congelado", **dados})
        return list(r._errs)

    antes = recursos(c)
    check("fora do alcance: erro", bool(await tenta({"tx": 13, "ty": 13})))          # dist 12 > 11
    check("fora do alcance: recursos intactos", recursos(c) == antes)
    for y in range(14):
        r.tiles[y][4] = S.WALL
    check("parede no caminho: erro", bool(await tenta({"tx": 8, "ty": 1})))
    check("parede no caminho: recursos intactos", recursos(c) == antes)
    r.tiles = [[S.WALL] * 14 for _ in range(14)]; r.tiles[1][1] = S.FLOOR
    check("sem chão na área: erro", bool(await tenta({"tx": 1, "ty": 4})))
    check("sem chão na área: recursos intactos", recursos(c) == antes)
    r.tiles = [[S.FLOOR] * 14 for _ in range(14)]
    check("terreno inválido: erro", bool(await tenta({"tx": 1, "ty": 6, "terreno": "lava"})))
    check("terreno inválido: recursos intactos", recursos(c) == antes)
    c["fome"] = c["sede"] = 15
    check("permanente sem 🍖/💧: erro", bool(await tenta({"tx": 1, "ty": 6, "permanente": True})))
    check("permanente sem 🍖/💧: recursos intactos", recursos(c) == (antes[0], 15, 15, False))
    c["fome"] = c["sede"] = 40
    check("mira válida: slot e ação gastos",
          not await tenta({"tx": 1, "ty": 6}) and recursos(c) != antes)
    check("gelo aplicado", r.materiais.get((1, 6)) == "piso_congelado")

    print("\n[2] O prisioneiro também testa Reflexos ao entrar no gelo")
    # handle_mover_prisioneiro aplicava a neve mas não o gelo — único caminho
    # de movimento sem _aplicar_piso_congelado_se_pisar.
    r = setup(); c = lewis(r, nivel=5, pos=(1, 1))
    await r.handle_magia("c", {"magia_id": "chamado_inverno", "terreno": "piso_congelado", "tx": 6, "ty": 6})
    check("gelo em (6,9) e chão em (6,10)", r.materiais.get((6, 9)) == "piso_congelado" and r.materiais.get((6, 10)) is None)
    r.prisoner = {"name": "Prisioneiro", "freed": True, "alive": True, "rescuer_pid": "c",
                  "moves_left": 6, "pos": [6, 11], "hp": 7, "max_hp": 7, "fort": 0, "ref_": 0, "will": 0}
    r.animados_phase_pid = "c"
    testes = []

    async def save(alvo, *a, **k):
        testes.append(alvo.get("name"))
        return (False, 1, 0, 0)
    r._save_mostrado = save
    await r.handle_mover_prisioneiro("c", 0, -1)     # (6,10): chão
    await r.handle_mover_prisioneiro("c", 0, -1)     # (6,9): gelo → Reflexos
    check("entrou no gelo", r.prisoner["pos"] == [6, 9])
    check("fez o teste de Reflexos", testes == ["Prisioneiro"])
    check("falhou: movimento zerado", r.prisoner["moves_left"] == 0)
    await r.handle_mover_prisioneiro("c", 0, -1)
    check("sem movimento, não anda mais", r.prisoner["pos"] == [6, 9])

    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    return 1 if FAIL else 0


sys.exit(asyncio.run(main()))
