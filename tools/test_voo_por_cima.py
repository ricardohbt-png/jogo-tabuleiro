"""Voar por cima de criaturas e objetos, conforme o porte de quem está embaixo.

Roda da raiz:  python tools/test_voo_por_cima.py

REGRA (2 pontos de altura = 1 quadrado)
  • criatura minúscula/pequena/média (herói e porte ausente contam como médio)
    e objeto BAIXO: voar 1 quadrado (2 pontos) acima já passa por cima;
  • criatura grande e objeto ALTO: 2 quadrados (4 pontos);
  • criatura enorme: 3 quadrados (6 pontos).
  A diferença é medida contra a altura de quem está embaixo (se também voa).
  Quem passa por cima também pode PARAR em cima; e descer de altura sobre algo
  que ficaria "dentro" da criatura é recusado.
  Parede, porta e escombros só se atravessam com "ignora obstáculos em voo".

A tabela dos casos é a MESMA de tools/test_voo_por_cima_cliente.js — o cliente
espelha a regra nas casas azuis e no caminho do clique.
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


async def montar():
    """Sala real com o herói voador em (1,1) num corredor aberto 5×3."""
    r = S.GameRoom("VOO_POR_CIMA")
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop
    r.players["p1"] = S.make_player("p1", "Asa", "warrior", 0)
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
    r.send_to = send_to; r.push_state = push_state
    # Arena: 5×3 de chão, sem decoração nem material.
    r.map_w, r.map_h = 5, 3
    r.tiles = [[S.FLOOR] * 5 for _ in range(3)]
    r.decorations = []
    r._decor_block_tiles = set(); r._decor_tall_tiles = set(); r._decor_low_tiles = set()
    r._mat_solid_tiles = set()
    r.materiais = {} if hasattr(r, "materiais") else None
    r.traps = []; r.armadilhas = []
    p = r.players["p1"]
    p.update({"pos": [1, 1], "voo": True, "altura": 0, "altura_max": 10,
              "pode_alterar_altura": True, "custo_mov_altura": 1,
              "moves_left": 20, "ignora_obstaculos_voo": False})
    return r


def monstro(porte=None, **extra):
    m = {"id": "m1", "type": "goblin", "name": "Alvo", "hp": 10, "max_hp": 10,
         "pos": [2, 1], "size": [1, 1], "alive": True}
    if porte: m["porte"] = porte
    m.update(extra)
    return m


async def tenta_passo(r, altura):
    """Herói em (1,1) na altura dada tenta entrar em (2,1). True se entrou."""
    p = r.players["p1"]
    p["pos"] = [1, 1]; p["altura"] = altura; p["moves_left"] = 20
    p.pop("moved_this_turn", None)
    r.erros.clear()
    await r.handle_move("p1", 1, 0, _push=False)
    return p["pos"] == [2, 1]


CASOS = [
    # rótulo, preparo(sala), altura mínima em pontos
    ("monstro minúsculo", lambda r: r.monsters.update(m1=monstro("minusculo")), 2),
    ("monstro pequeno",   lambda r: r.monsters.update(m1=monstro("pequeno")), 2),
    ("monstro médio",     lambda r: r.monsters.update(m1=monstro("medio")), 2),
    ("monstro sem porte (médio)", lambda r: r.monsters.update(m1=monstro()), 2),
    ("monstro grande",    lambda r: r.monsters.update(m1=monstro("grande")), 4),
    ("monstro enorme",    lambda r: r.monsters.update(m1=monstro("enorme")), 6),
    ("outro herói (médio)", lambda r: r.players.update(p2=dict(
        S.make_player("p2", "Chão", "rogue", 1), pos=[2, 1])), 2),
    ("servo animado",     lambda r: r.players["p1"].__setitem__("animados", [
        {"id": "a1", "pos": [2, 1], "vida_atual": 5, "porte": "medio"}]), 2),
    ("servo animado grande", lambda r: r.players["p1"].__setitem__("animados", [
        {"id": "a1", "pos": [2, 1], "vida_atual": 5, "porte": "grande"}]), 4),
    ("objeto baixo",      lambda r: r._decor_block_tiles.add((2, 1)), 2),
    ("objeto alto",       lambda r: (r._decor_block_tiles.add((2, 1)),
                                     r._decor_tall_tiles.add((2, 1))), 4),
]


async def main():
    print("\n[1] Herói: uma altura abaixo bloqueia, a mínima passa e pode parar em cima")
    for rotulo, preparo, minimo in CASOS:
        r = await montar(); preparo(r)
        check(f"{rotulo}: altura {minimo - 1} não passa", not await tenta_passo(r, minimo - 1),
              r.erros)
        check(f"{rotulo}: altura {minimo} passa e para em cima", await tenta_passo(r, minimo),
              r.erros)

    print("\n[2] Monstro voador (`_monster_can_occupy`) segue a mesma tabela")
    for porte, minimo in (("medio", 2), ("grande", 4), ("enorme", 6)):
        r = await montar()
        r.players["p1"].update({"pos": [2, 1], "voo": False, "altura": 0, "porte": porte})
        voador = monstro(None, id="v1", pos=[1, 1], voo=True, altura=minimo - 1)
        r.monsters["v1"] = voador
        check(f"sobre herói {porte}: altura {minimo - 1} bloqueia",
              not r._monster_can_occupy(voador, 2, 1))
        voador["altura"] = minimo
        check(f"sobre herói {porte}: altura {minimo} passa", r._monster_can_occupy(voador, 2, 1))
    for rotulo, alto, minimo in (("objeto baixo", False, 2), ("objeto alto", True, 4)):
        r = await montar()
        r._decor_block_tiles.add((2, 1))
        if alto: r._decor_tall_tiles.add((2, 1))
        voador = monstro(None, id="v1", pos=[1, 1], voo=True, altura=minimo - 1)
        r.monsters["v1"] = voador
        check(f"monstro sobre {rotulo}: altura {minimo - 1} bloqueia",
              not r._monster_can_occupy(voador, 2, 1))
        voador["altura"] = minimo
        check(f"monstro sobre {rotulo}: altura {minimo} passa", r._monster_can_occupy(voador, 2, 1))

    print("\n[3] Quem está embaixo também voa: vale a diferença de altura")
    r = await montar()
    r.monsters["m1"] = monstro("medio", voo=True, altura=2)
    check("médio voando a 2, herói a 3: não passa", not await tenta_passo(r, 3))
    check("médio voando a 2, herói a 4: passa", await tenta_passo(r, 4))

    print("\n[4] Parede, porta e escombros continuam bloqueando sem a opção")
    r = await montar(); r.tiles[1][2] = S.WALL
    check("parede bloqueia mesmo a altura 10", not await tenta_passo(r, 10))
    r = await montar(); r._mat_solid_tiles.add((2, 1))
    check("escombros bloqueiam mesmo a altura 10", not await tenta_passo(r, 10))
    r = await montar(); r._decor_block_tiles.add((2, 1))
    check("no chão (altura 0) o objeto baixo bloqueia", not await tenta_passo(r, 0))

    print("\n[5] Descer sobre algo é recusado; descer em casa livre funciona")
    r = await montar()
    r.monsters["m1"] = monstro("grande")
    p = r.players["p1"]
    await tenta_passo(r, 4)
    check("parado sobre o grande a altura 4", p["pos"] == [2, 1] and p["altura"] == 4)
    r.erros.clear()
    await r.handle_alterar_altura("p1", -1)
    check("descer para 3 sobre o grande é recusado", p["altura"] == 4 and r.erros, r.erros)
    await r.handle_alterar_altura("p1", 1)
    check("subir continua livre", p["altura"] == 5)
    r = await montar(); r._decor_block_tiles.add((2, 1))
    p = r.players["p1"]
    await tenta_passo(r, 2)
    r.erros.clear()
    await r.handle_alterar_altura("p1", -1)
    check("pousar sobre o objeto baixo é recusado", p["altura"] == 2 and r.erros, r.erros)
    p["pos"] = [0, 1]
    await r.handle_alterar_altura("p1", -1)
    check("descer em casa livre funciona", p["altura"] == 1)
    r = await montar()
    m = monstro("medio", voo=True, altura=6, altura_max=10, pos=[2, 1],
                pode_alterar_altura=True, custo_mov_altura=1, master_moves_left=5)
    r.monsters["m1"] = m
    r.players["p1"].update({"pos": [2, 1], "voo": False, "altura": 0})
    r.master_pid = "mestre"; r.master_manual_mid = "m1"
    r._manual_control_kind = lambda pid, mid: "mestre"
    await r.handle_alterar_altura("mestre", -1, "m1")
    await r.handle_alterar_altura("mestre", -1, "m1")
    await r.handle_alterar_altura("mestre", -1, "m1")
    await r.handle_alterar_altura("mestre", -1, "m1")
    await r.handle_alterar_altura("mestre", -1, "m1")   # 2 -> 1 sobre médio: recusado
    check("monstro (mestre) desce até 2 sobre o herói e para ali", m["altura"] == 2,
          f"altura={m['altura']}")

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
