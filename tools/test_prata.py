"""Testes das VARIANTES DE PRATA (armas + munição) e da IA de granada do Soldado.

Cobre três frentes do WIP de prata/soldado:
  • Fraqueza do Lobisomem a prata (dano ×2 + bloqueia regeneração) e a
    metade-de-dano de armas comuns não-mágicas.
  • Munição de prata: bônus fixo de dano, empresta a propriedade `silver` ao
    disparo SEM pratear a arma equipada, e prioridade de consumo (equipada vence;
    na bolsa, básico antes de especial).
  • Exclusões de prata na loja (arcos/bestas/cajados de madeira não pratam).
  • IA de granada do Soldado (_soldado_try_granada) e o dano em área que atinge
    o próprio monstro sem KeyError (o `else` que antes tratava monstro como animado).

Roda da raiz: python tools/test_prata.py
Stuba a rede do GameRoom e monta o mapa manualmente."""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import (GameRoom, make_player, make_monster, MONSTER_DEFS,
                    FLOOR, WALL, DMG_PHYSICAL, DMG_MAGIC,
                    SHOP_WEAPONS, SHOP_AMMO, ARREMESSAVEIS,
                    SILVER_WEAPON_EXCLUSIONS, RANGED_AMMO)

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=13, h=13):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    r.send_to = cap_send
    r._tem_linha_de_visao = lambda *a, **k: True
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda x, y: False
    r._errs = errs
    return r

def shop_w(wid):
    return deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == wid))

def ammo(aid):
    return deepcopy(next(a for a in SHOP_AMMO if a["id"] == aid))

def werewolf(r, mid, x, y, hp=30):
    lob = next(d for d in MONSTER_DEFS if d.get("type") == "lobisomem")
    m = make_monster(lob, {"id": 1, "cx": x, "cy": y})
    m["id"] = mid; m["pos"] = [x, y]; m["hp"] = hp; m["max_hp"] = hp
    m["alive"] = True
    r.monsters[mid] = m
    return m

def goblin(r, mid, x, y):
    g = next(d for d in MONSTER_DEFS if d.get("type") == "goblin")
    m = make_monster(g, {"id": 1, "cx": x, "cy": y})
    m["id"] = mid; m["pos"] = [x, y]; m["hp"] = 30; m["max_hp"] = 30
    m["alive"] = True
    r.monsters[mid] = m
    return m


async def main():
    random.seed(7)

    # ── [1] Lobisomem: dano físico de prata ×2 + bloqueia regeneração ──────────
    print("\n[1] Lobisomem — fraqueza a prata (via _apply_damage_types)")
    r = setup()
    lob = werewolf(r, "L1", 6, 6)
    d = r._apply_damage_types(10, [DMG_PHYSICAL], lob, {"silver": True})
    check("prata dobra o dano físico (10→20)", d == 20, f"deu {d}")
    check("prata bloqueia a regeneração", lob.get("regeneracao_bloqueada") is True)

    lob2 = werewolf(r, "L2", 6, 8)
    d = r._apply_damage_types(10, [DMG_PHYSICAL], lob2, {})
    check("arma comum (não-mágica) causa metade (10→5)", d == 5, f"deu {d}")
    check("arma comum NÃO bloqueia regeneração", not lob2.get("regeneracao_bloqueada"))

    lob3 = werewolf(r, "L3", 8, 6)
    d = r._apply_damage_types(10, [DMG_PHYSICAL], lob3, {"magical": True})
    check("arma mágica causa dano cheio (10→10)", d == 10, f"deu {d}")
    d = r._apply_damage_types(10, [DMG_PHYSICAL], lob3, {"id": "magic_sword"})
    check("arma com 'magic' no id causa dano cheio", d == 10, f"deu {d}")

    lob4 = werewolf(r, "L4", 8, 8)
    d = r._apply_damage_types(10, [DMG_MAGIC], lob4, None)
    check("dano mágico bloqueia a regeneração", lob4.get("regeneracao_bloqueada") is True)

    # ── [2] Munição de prata: propriedade emprestada + bônus, arma não muda ─────
    print("\n[2] Munição de prata via handle_attack (arco vs lobisomem)")
    r = setup()
    p = make_player("p1", "Luccas", "rogue", 0); r.players["p1"] = p
    p["pos"] = [6, 6]; p["alive"] = True; p["action_done"] = False
    arco = shop_w("arco_curto")
    p["gear"]["weapon"] = arco; p["weapon"] = arco
    p["gear"]["off_hand"] = ammo("flechas_prata")
    lob = werewolf(r, "L1", 8, 6, hp=60)
    await r.handle_attack("p1", "L1")
    check("disparo de prata bloqueou a regeneração do lobisomem",
          lob.get("regeneracao_bloqueada") is True)
    check("a arma equipada NÃO virou prata permanentemente",
          not (p.get("weapon") or {}).get("silver"))
    check("a flecha de prata foi consumida (10→9)",
          p["gear"]["off_hand"]["ammo_count"] == 9)

    # Munição comum NÃO empresta prata (lobisomem regenera → metade de dano)
    r = setup()
    p = make_player("p1", "Luccas", "rogue", 0); r.players["p1"] = p
    p["pos"] = [6, 6]; p["alive"] = True; p["action_done"] = False
    arco = shop_w("arco_curto")
    p["gear"]["weapon"] = arco; p["weapon"] = arco
    p["gear"]["off_hand"] = ammo("flechas")
    lob = werewolf(r, "L1", 8, 6, hp=60)
    await r.handle_attack("p1", "L1")
    check("flecha comum NÃO bloqueia a regeneração",
          not lob.get("regeneracao_bloqueada"))

    # ── [3] Prioridade de consumo de munição (besta) ───────────────────────────
    print("\n[3] Prioridade de munição (besta)")
    def cenario_besta():
        rr = setup()
        pp = make_player("p1", "Luccas", "rogue", 0); rr.players["p1"] = pp
        pp["pos"] = [6, 6]; pp["alive"] = True; pp["action_done"] = False
        besta = shop_w("besta")
        pp["gear"]["weapon"] = besta; pp["weapon"] = besta
        pp["gear"]["off_hand"] = None
        goblin(rr, "g1", 8, 6)
        return rr, pp

    r, p = cenario_besta()
    p["bag"] = [ammo("virotes_prata"), ammo("virotes")]
    await r.handle_attack("p1", "g1")
    basico = next(i for i in p["bag"] if i["id"] == "virotes")
    prata = next(i for i in p["bag"] if i["id"] == "virotes_prata")
    check("na bolsa, o virote BÁSICO é gasto antes da prata", basico["ammo_count"] == 9)
    check("a prata da bolsa fica intacta", prata["ammo_count"] == 10)

    r, p = cenario_besta()
    p["gear"]["off_hand"] = ammo("virotes_prata")
    p["bag"] = [ammo("virotes")]
    await r.handle_attack("p1", "g1")
    check("munição EQUIPADA na mão esquerda tem prioridade sobre a bolsa",
          p["gear"]["off_hand"]["ammo_count"] == 9)
    check("o básico da bolsa fica intacto quando há prata equipada",
          next(i for i in p["bag"] if i["id"] == "virotes")["ammo_count"] == 10)

    r, p = cenario_besta()
    p["bag"] = []
    await r.handle_attack("p1", "g1")
    check("sem munição → erro enviado", len(r._errs) > 0)
    check("a mensagem de erro cita prata", any("prata" in e for e in r._errs))

    # ── [4] Exclusões de prata na loja ─────────────────────────────────────────
    print("\n[4] Exclusões de prata na loja")
    ids = {w["id"] for w in SHOP_WEAPONS}
    for excl in ("arco_curto", "longbow", "besta", "hand_crossbow", "cajado_madeira", "staff"):
        check(f"'{excl}' NÃO tem variante de prata", f"{excl}_prata" not in ids)
    check("arma corpo a corpo (longsword) TEM variante de prata", "longsword_prata" in ids)
    check("flechas_prata aceitas por arco_curto", "flechas_prata" in RANGED_AMMO["arco_curto"])
    check("virotes_prata aceitos pela besta", "virotes_prata" in RANGED_AMMO["besta"])

    # ── [5] IA de granada do Soldado ───────────────────────────────────────────
    print("\n[5] IA de granada do Soldado")

    def soldado(r, x, y, hp=40, granada="granada"):
        m = {"id": "sol", "type": "soldado", "name": "Soldado", "pos": [x, y],
             "hp": hp, "max_hp": 40, "ac": 15, "alive": True,
             "dex": 12, "base_attack_bonus": 3,
             "equipment_consumables": [{"id": granada, "effect": "throwable"}]}
        r.monsters["sol"] = m
        return m

    # Saudável, herói distante e isolado → lança sem se incluir na explosão
    r = setup()
    s = soldado(r, 2, 2)
    hero = make_player("h1", "Victor", "warrior", 0); r.players["h1"] = hero
    hero["pos"] = [5, 2]; hero["alive"] = True; hero["hp"] = 20
    jogou = await r._soldado_try_granada(s)
    check("saudável: lança a granada num herói distante", jogou is True)
    check("a granada foi consumida da bolsa",
          not any(i["id"] == "granada" for i in s["equipment_consumables"]))

    # Saudável, herói só adjacente → NÃO lança (não arrisca a própria pele)
    r = setup()
    s = soldado(r, 2, 2)
    hero = make_player("h1", "Victor", "warrior", 0); r.players["h1"] = hero
    hero["pos"] = [3, 2]; hero["alive"] = True; hero["hp"] = 20
    jogou = await r._soldado_try_granada(s)
    check("saudável + herói adjacente: NÃO lança (evita autodano)", jogou is False)
    check("a granada permanece na bolsa", any(i["id"] == "granada" for i in s["equipment_consumables"]))

    # Desesperado (<30% HP), herói adjacente → aceita o risco e lança
    r = setup()
    s = soldado(r, 2, 2, hp=10)   # 10/40 = 25% < 30%
    hero = make_player("h1", "Victor", "warrior", 0); r.players["h1"] = hero
    hero["pos"] = [3, 2]; hero["alive"] = True; hero["hp"] = 20
    jogou = await r._soldado_try_granada(s)
    check("desesperado + herói adjacente: lança mesmo se arriscar autodano", jogou is True)

    # Prioriza o alvo que concentra mais heróis no raio (todos no alcance 4)
    r = setup()
    s = soldado(r, 4, 4)
    # cluster de 2 heróis (7,4)+(7,5) + 1 herói isolado (4,8) — todos a dist ≤4
    for i, (hx, hy) in enumerate([(7, 4), (7, 5), (4, 8)]):
        h = make_player(f"h{i}", f"H{i}", "warrior", 0); r.players[f"h{i}"] = h
        h["pos"] = [hx, hy]; h["alive"] = True; h["hp"] = 20
    r._na_area = lambda obj, tx, ty, raio: max(abs(obj["pos"][0]-tx), abs(obj["pos"][1]-ty)) <= raio
    # captura o alvo escolhido
    escolhido = {}
    orig = r._monster_throw_item
    async def spy(m, target_obj, item):
        escolhido["alvo"] = target_obj["obj"]["pos"]
        return await orig(m, target_obj, item)
    r._monster_throw_item = spy
    await r._soldado_try_granada(s)
    check("mira o agrupamento (2 heróis) e não o herói isolado",
          escolhido.get("alvo") in ([7, 4], [7, 5]), f"mirou {escolhido.get('alvo')}")

    # ── [6] Explosão que atinge o próprio monstro usa `hp` (sem KeyError) ───────
    print("\n[6] Explosão de área atinge monstro sem KeyError")
    r = setup()
    s = soldado(r, 2, 2, hp=10)   # desesperado → topa explodir adjacente
    # herói adjacente ao soldado: o alvo cai perto o bastante para o soldado
    # entrar no raio 1 da explosão
    hero = make_player("h1", "Victor", "warrior", 0); r.players["h1"] = hero
    hero["pos"] = [3, 2]; hero["alive"] = True; hero["hp"] = 20
    # outro monstro colado no alvo, também dentro do raio
    outro = goblin(r, "g2", 4, 2)
    r._na_area = lambda obj, tx, ty, raio: max(abs(obj["pos"][0]-tx), abs(obj["pos"][1]-ty)) <= raio
    hp_soldado_antes = s["hp"]; hp_goblin_antes = outro["hp"]
    erro = None
    try:
        await r._soldado_try_granada(s)
    except KeyError as e:
        erro = e
    check("nenhum KeyError ao explodir com monstros no raio", erro is None, str(erro))
    check("o próprio soldado sofreu dano da explosão (usa hp)", s["hp"] < hp_soldado_antes)
    check("o goblin no raio sofreu dano da explosão (usa hp)", outro["hp"] < hp_goblin_antes)

    print(f"\n===== {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
