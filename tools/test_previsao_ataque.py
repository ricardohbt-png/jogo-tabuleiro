"""Prévia de acerto do tooltip (prever_ataque). Roda da raiz: python tools/test_previsao_ataque.py"""
import asyncio, sys, os, random
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, make_monster, chance_acerto_d20

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")


def sala(tipo_monstro="goblin", classe="warrior"):
    """Herói em (2,2) e um monstro adjacente em (3,2), sala 'playing' sem ruído."""
    r = GameRoom("PREV")
    enviados = []
    async def _noop(*a, **k): pass
    async def _cap(pid, msg, *a, **k): enviados.append((pid, msg))
    r.gm_say = _noop; r.push_state = _noop; r.broadcast = _noop; r._broadcast_dado = _noop
    r.send_to = _cap
    r.phase = "playing"
    r.map_w = r.map_h = 8
    r.tiles = [[S.FLOOR] * 8 for _ in range(8)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 8, "h": 8, "cx": 3, "cy": 2, "locked": False, "doors": []}]
    r._is_turn = lambda pid: True
    p = make_player("h1", "Heroi", classe, 0)
    p["pos"] = [2, 2]; p["alive"] = True
    r.players["h1"] = p
    mdef = next(m for m in S.MONSTER_DEFS if m["type"] == tipo_monstro)
    m = make_monster(mdef, r.rooms[0])
    m["id"] = "m1"; m["pos"] = [3, 2]; m["hp"] = m["max_hp"] = 9999
    r.monsters = {"m1": m}
    r._enviados = enviados
    return r, p, m


async def prever(r, buffs=None):
    r._enviados.clear()
    await r.handle_prever_ataque("h1", {"target_id": "m1", "target_pos": [3, 2],
                                        "buffs": buffs or [], "chave": "k"})
    msgs = [m for pid, m in r._enviados if m.get("type") == "previsao_ataque"]
    return msgs[0] if msgs else None


async def main():
    print("\n[1] Chance pura (espelha d20_attack: 20 sempre acerta, 1 não erra sozinho)")
    check("+5 contra CA 15 → 55%", chance_acerto_d20(5, 15) == 55)
    check("vantagem: 1-(0,45)² → 80%", chance_acerto_d20(5, 15, True, False) == 80)
    check("desvantagem: 0,55² → 30%", chance_acerto_d20(5, 15, False, True) == 30)
    check("as duas se anulam", chance_acerto_d20(5, 15, True, True) == 55)
    check("CA impossível ainda acerta no 20 → 5%", chance_acerto_d20(0, 40) == 5)
    check("CA trivial → 100%", chance_acerto_d20(20, 5) == 100)

    print("\n[2] A prévia responde só a quem pediu e traz o que o tooltip mostra")
    r, p, m = sala()
    prev = await prever(r)
    check("responde", prev is not None)
    check("ecoa a chave do pedido", prev and prev["chave"] == "k")
    check("vai só para quem pediu", all(pid == "h1" for pid, _ in r._enviados))
    check("traz dado e bônus fixo da arma", prev and prev["dano_dado"] == (p.get("weapon") or {}).get("die"))
    check("chance entre 0 e 100", prev and 0 <= prev["chance"] <= 100)

    print("\n[3] A prévia não gasta nada")
    antes = {k: p.get(k) for k in ("fome", "sede", "action_done", "bonus_action_used", "hp")}
    for _ in range(5): await prever(r, ["mira_certeira", "golpe_devastador"])
    depois = {k: p.get(k) for k in antes}
    check("fome, sede, ação e HP intactos", antes == depois)
    check("nem arma as habilidades do guerreiro", not p.get("skill_bonus_acerto") and not p.get("skill_dobrar_dano"))

    print("\n[4] A prévia bate com o ataque real (medido)")
    random.seed(7)
    r, p, m = sala()
    prev = await prever(r)
    N = 1500; acertos = 0
    fome0, sede0 = p["fome"], p["sede"]
    for _ in range(N):
        antes_hp = m["hp"]
        # Cada ataque gasta fome/sede: sem repor, o herói sai de Saciado (+1)
        # e o teste mediria um herói cada vez mais faminto, não o da prévia.
        p["action_done"] = False; p["fome"], p["sede"] = fome0, sede0
        await r.handle_attack("h1", "m1")
        if m["hp"] < antes_hp: acertos += 1
        m["hp"] = 9999
    real = 100 * acertos / N
    check(f"prévia {prev['chance']}% ≈ real {real:.1f}% (±4)", abs(real - prev["chance"]) <= 4)

    print("\n[5] Habilidades armadas no cliente entram na conta")
    r, p, m = sala()
    sem = await prever(r)
    com = await prever(r, ["mira_certeira"])
    check("Mira Certeira sobe a chance", com["chance"] > sem["chance"] or sem["chance"] == 100)
    check("sem Mira III, o dano não muda", com["dano_fixo"] == sem["dano_fixo"])
    p.setdefault("guild_owned", {}).setdefault("especializacoes", []).append("guerreiro_mira_3")
    com3 = await prever(r, ["mira_certeira"])
    check("com Mira III, +2 no dano", com3["dano_fixo"] == sem["dano_fixo"] + 2)
    gol = await prever(r, ["golpe_devastador"])
    check("Golpe Devastador multiplica o dado (×1,5 sem a especialização)", gol["golpe_mult"] == 1.5)
    check("sem armar, multiplicador 1", sem["golpe_mult"] == 1)

    print("\n[6] Camuflagem Natural: a prévia vê o +2 sem gastá-lo")
    r, p, m = sala("cobra_venenosa")
    c1 = await prever(r)
    c2 = await prever(r)
    check("a cobra continua camuflada depois de dois hovers", not m.get("camuflagem_usada"))
    check("as duas prévias são iguais", c1["chance"] == c2["chance"])
    m["camuflagem_usada"] = True
    c3 = await prever(r)
    check("gasta a camuflagem, a chance sobe", c3["chance"] >= c1["chance"] and c3["chance"] != c1["chance"] or c1["chance"] == 100)
    m["camuflagem_usada"] = False
    p["action_done"] = False
    await r.handle_attack("h1", "m1")
    check("o ataque REAL continua gastando a camuflagem", m.get("camuflagem_usada") is True)

    print("\n[7] Recusa silenciosa")
    r, p, m = sala()
    m["hp"] = 0
    check("monstro morto: sem resposta", await prever(r) is None)
    m["hp"] = 10; r.phase = "city"
    check("fora da masmorra: sem resposta", await prever(r) is None)
    r.phase = "playing"; p["alive"] = False
    check("herói morto: sem resposta", await prever(r) is None)

    print("\n[8] Fiação")
    fonte = open(S.__file__, encoding="utf-8").read()
    check("o despacho conhece prever_ataque", 'elif t == "prever_ataque":' in fonte)
    check("handle_attack usa o MESMO helper da prévia",
          "_mods = self._modificadores_ataque_heroi(p, target, target_tile, w_range, attacker_id=pid)" in fonte)

    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
