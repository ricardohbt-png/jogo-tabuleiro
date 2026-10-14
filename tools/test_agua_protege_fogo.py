"""Água protege do fogo. Roda da raiz: python -X utf8 tools/test_agua_protege_fogo.py
Spec: docs/superpowers/specs/2026-10-13-agua-protege-fogo-design.md
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    """Sala 20x12 de chão, fase 'playing', sem rede; captura broadcasts e narração."""
    r = S.GameRoom("AGUAFOGO")
    r.msgs = []
    r.narr = []
    async def noop(*a, **k):
        pass
    async def bc(msg, *a, **k):
        r.msgs.append(msg)
    async def say(txt, *a, **k):
        r.narr.append(str(txt))
    r.gm_say = say; r.broadcast = bc; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 13):
        for x in range(1, 21):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 20, "h": 12, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def heroi(r, pid, nome, classe, pos):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    r.monsters[m["id"]] = m
    return m


def pinta(r, material, tiles):
    for t in tiles:
        r.materiais[tuple(t)] = material
    r._rebuild_materiais_index()


def roda(coro):
    return asyncio.run(coro)


print("[1] metade do dano de fogo")
r = sala()
h = heroi(r, "h1", "Ana", "mage", (5, 5))
check("fora da água: dano cheio", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
pinta(r, "agua", [(5, 5)])
check("na água rasa: metade", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
check("na água: dano 1 fica exatamente 1", r._apply_damage_types(1, [S.DMG_FIRE], h) == 1)
check("na água: dano 0 não estoura", r._apply_damage_types(0, [S.DMG_FIRE], h) == 0)
check("na água: outro elemento intacto", r._apply_damage_types(8, [S.DMG_COLD], h) == 8)
for mat in ("agua_profunda", "rodamoinho", "rodamoinho_profundo"):
    pinta(r, mat, [(5, 5)])
    check(f"{mat} conta", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
pinta(r, "pantano", [(5, 5)])
check("pântano NÃO dá metade do dano", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
pinta(r, "agua", [(5, 5)])
h["altura"] = 3; h["voo"] = True
check("voador não conta", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
h["altura"] = 0; h["voo"] = False

print("[2] footprint e soma com resistências")
r = sala()
grande = None
for d in S.MONSTER_DEFS:
    m = monstro(r, d["type"], (6, 6))
    if len(r._monster_tiles(m)) == 4:
        grande = m
        break
    del r.monsters[m["id"]]
check("existe monstro 2x2 para o teste", grande is not None)
tiles = r._monster_tiles(grande)
grande["immunities"] = []; grande["resistances"] = []; grande["weaknesses"] = []
pinta(r, "agua", tiles[:3])
check("2x2 com uma casa fora: sem proteção", r._apply_damage_types(8, [S.DMG_FIRE], grande) == 8)
check("2x2 com uma casa fora: pega fogo", r._aplicar_em_chamas(grande, 3, True) is True)
grande["em_chamas_rodadas"] = 0
pinta(r, "agua", tiles)
check("2x2 todo na água: metade", r._apply_damage_types(8, [S.DMG_FIRE], grande) == 4)
check("2x2 todo na água: não pega fogo", r._aplicar_em_chamas(grande, 3, True) is False)
g2 = heroi(r, "h2", "Bia", "warrior", (9, 9))
pinta(r, "agua", [(9, 9)])
g2["resistances"] = [{"type": S.DMG_FIRE, "mode": "half"}]
check("resistência existente + água = quarto", r._apply_damage_types(8, [S.DMG_FIRE], g2) == 2)
g2["resistances"] = []; g2["immunities"] = [S.DMG_FIRE]
check("imune a fogo na água segue 0", r._apply_damage_types(8, [S.DMG_FIRE], g2) == 0)

print("[3] imunidade a pegar fogo")
r = sala()
h = heroi(r, "h1", "Ana", "warrior", (5, 5))
check("fora da água: pega fogo", r._aplicar_em_chamas(h, 3, True) is True and h["em_chamas_rodadas"] == 3)
h["em_chamas_rodadas"] = 0
pinta(r, "agua", [(5, 5)])
check("na água: não pega fogo", r._aplicar_em_chamas(h, 3, True) is False and h.get("em_chamas_rodadas", 0) == 0)
pinta(r, "pantano", [(5, 5)])
check("no pântano: não pega fogo", r._aplicar_em_chamas(h, 3, True) is False)
pinta(r, "agua", [(5, 5)])
check("Fogo Grego pega mesmo na água", r._aplicar_em_chamas(h, 3, False) is True and h["em_chamas_rodadas"] == 3)

print("[4] água apaga")
r = sala()
h = heroi(r, "h1", "Ana", "warrior", (5, 5))
pinta(r, "agua", [(6, 5)])
h["em_chamas_rodadas"] = 3; h["chamas_agua_apaga"] = True
roda(r._apagar_chamas_na_agua(h))
check("fora da água não apaga", h["em_chamas_rodadas"] == 3)
h["pos"] = [6, 5]
roda(r._aplicar_lava_se_pisar(h))
check("passo na água apaga (gancho de movimento)", h["em_chamas_rodadas"] == 0)
check("narra o apagar", any("água" in n.lower() or "water" in n.lower() for n in r.narr))
n0 = len(r.narr)
roda(r._aplicar_lava_se_pisar(h))
check("não narra de novo", len(r.narr) == n0)
h["em_chamas_rodadas"] = 3; h["chamas_agua_apaga"] = True
hp0 = h["hp"]
roda(r._processar_em_chamas_turno())
check("rede de segurança no tick apaga sem dano", h["em_chamas_rodadas"] == 0 and h["hp"] == hp0)
h["pos"] = [5, 5]
roda(r._processar_em_chamas_turno())
check("sair da água não reacende (nem tica dano de chama)", h["em_chamas_rodadas"] == 0 and h["hp"] == hp0)
h["pos"] = [6, 5]; h["em_chamas_rodadas"] = 3; h["chamas_agua_apaga"] = False
roda(r._aplicar_lava_se_pisar(h))
check("Fogo Grego não é apagado pela água", h["em_chamas_rodadas"] == 3)

print("[5] Fogo Grego: dano cheio e escopo")
r = sala()
h = heroi(r, "h1", "Ana", "warrior", (5, 5))
pinta(r, "agua", [(5, 5)])
with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
    check("escopo ligado: dano cheio", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
check("escopo desligado ao sair", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
try:
    with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
        raise RuntimeError("x")
except RuntimeError:
    pass
check("escopo desligado após exceção", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
with r._escopo_fogo_grego({"chamas_agua_apaga": True}):
    check("óleo comum não liga o escopo", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
h["em_chamas_rodadas"] = 2; h["chamas_agua_apaga"] = False
check("tick de Fogo Grego em chamas: dano cheio", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)

print("[6] arremesso real (handler)")


def arremessa(item_id, na_agua):
    r = sala()
    p = heroi(r, "h1", "Ana", "rogue", (5, 5))
    gob = monstro(r, "goblin", (7, 5))
    gob["hp"] = gob["max_hp"] = 100
    gob["ac"] = 0
    gob["immunities"] = []; gob["resistances"] = []; gob["weaknesses"] = []
    if na_agua:
        pinta(r, "agua", r._monster_tiles(gob))
    defn = S.ARREMESSAVEIS[item_id]
    item = {"id": item_id, "name": item_id}
    p.setdefault("bag", []).append(item)
    orig = S.random.randint
    S.random.randint = lambda a, b: b      # d20 = 20, dados no máximo: acerta sempre
    try:
        roda(r._throw_item_alvo(p, defn, item, gob["id"]))
    finally:
        S.random.randint = orig
    return r, gob, 100 - gob["hp"]


try:
    _, g_dry, d_dry = arremessa("frasco_oleo", False)
    r_w, g_wet, d_wet = arremessa("frasco_oleo", True)
    check("óleo seco: pega fogo", g_dry.get("em_chamas_rodadas", 0) > 0)
    check("óleo na água: não pega fogo", g_wet.get("em_chamas_rodadas", 0) == 0)
    check(f"óleo na água: dano reduzido ({d_wet} vs {d_dry})", 0 < d_wet < d_dry)
    _, g_fg, d_fg = arremessa("fogo_grego", True)
    _, g_fg_dry, d_fg_dry = arremessa("fogo_grego", False)
    check("fogo grego na água: pega fogo", g_fg.get("em_chamas_rodadas", 0) > 0)
    check(f"fogo grego na água: dano cheio ({d_fg} vs {d_fg_dry})", d_fg == d_fg_dry and d_fg > 0)
    check("escopo não vaza após os arremessos", r_w._fogo_ignora_agua is False)
except Exception as e:
    import traceback
    traceback.print_exc()
    check(f"arremesso real executou ({e})", False)

print("[7] Bola de Fogo real (funil de dano) e congelar")


def dano_bola(na_agua):
    """Bola de Fogo (_aplicar_dano_area_fogo -> _aplicar_dano_alvo) em um monstro."""
    r = sala()
    m = monstro(r, "goblin", (8, 5))
    m["hp"] = m["max_hp"] = 200
    m["immunities"] = []; m["resistances"] = []; m["weaknesses"] = []
    if na_agua:
        pinta(r, "agua", r._monster_tiles(m))
    roda(r._aplicar_dano_area_fogo("x", 8, 5, 1, 12, 99, "R1", com_save=False))
    return r, m, 200 - m["hp"]


try:
    _, _, d_seco = dano_bola(False)
    r_b, m_b, d_agua = dano_bola(True)
    check(f"Bola de Fogo seca: dano cheio ({d_seco})", d_seco > 0)
    check(f"Bola de Fogo (monstro) na água: ~metade ({d_agua} vs {d_seco})",
          abs(d_agua * 2 - d_seco) <= 1 and d_agua < d_seco)
    # congelar a casa remove a proteção
    r_b._aplicar_camadas_terreno_inverno(list(r_b._monster_tiles(m_b)), "piso_congelado", "z1",
                                         permanente=False, expira_em=r_b.round_num + 5)
    check("casa congelada: _agua_protege False", r_b._agua_protege(m_b) is False)
    m_b["hp"] = 200

    async def _bola_em_escopo():
        # como no jogo: a magia roda dentro de evento_elemental, então a reação (fogo derrete o gelo
        # e a casa vira água) só resolve DEPOIS do dano — o golpe da própria explosão sai cheio.
        async with r_b.evento_elemental({"tipo": "magia", "caster_id": "x"}):
            await r_b._aplicar_dano_area_fogo("x", 8, 5, 1, 12, 99, "R1", com_save=False)
    roda(_bola_em_escopo())
    check(f"casa congelada: dano de fogo volta cheio ({200 - m_b['hp']})", 200 - m_b["hp"] == d_seco)
except Exception as e:
    import traceback
    traceback.print_exc()
    check(f"Bola de Fogo/congelar executou ({e})", False)

print("[8] prisioneiro e servo animado")
r = sala()
r.prisoner = {"pos": [5, 5], "alive": True, "freed": True, "rescuer_pid": "p1",
              "hp": 7, "max_hp": 7, "ac": 10, "moves_left": 6}
pinta(r, "agua", [(5, 5)])
check("prisioneiro na água: _agua_protege", r._agua_protege(r.prisoner) is True)
check("prisioneiro na água: não pega fogo", r._aplicar_em_chamas(r.prisoner, 3, True) is False)
# Servo animado: `_agua_protege` e o apagar valem, mas o dano de fogo do servo passa por
# `_ajustar_dano_elemental` (fora de `_apply_damage_types`), então NÃO recebe a metade
# do dano nesses caminhos. Limite conhecido, documentado no CLAUDE.md.
servo = {"id": "a1", "pos": [5, 5], "vida_atual": 10, "vida_max": 10, "tipo": "esqueleto",
         "nome": "Servo", "name": "Servo"}
check("servo na água: _agua_protege", r._agua_protege(servo) is True)
servo["em_chamas_rodadas"] = 3; servo["chamas_agua_apaga"] = True
check("servo na água: apaga as chamas", roda(r._apagar_chamas_na_agua(servo)) is True
      and servo["em_chamas_rodadas"] == 0)

print("[9] arremesso de monstro (_monster_throw_item)")


def monstro_arremessa(item_id, na_agua):
    r = sala()
    h = heroi(r, "h1", "Ana", "warrior", (7, 5))
    h["hp"] = h["max_hp"] = 200
    h["resistances"] = []; h["immunities"] = []
    h["ac_base"] = h["ac"] = 0
    sold = monstro(r, "goblin", (5, 5))
    if na_agua:
        pinta(r, "agua", [(7, 5)])
    item = {"id": item_id, "name": item_id}
    orig = S.random.randint
    S.random.randint = lambda a, b: b
    try:
        roda(r._monster_throw_item(sold, {"kind": "player", "obj": h}, item))
    finally:
        S.random.randint = orig
    return r, h, 200 - h["hp"]


try:
    _, h_s, d_s = monstro_arremessa("frasco_oleo", False)
    r_w, h_w, d_w = monstro_arremessa("frasco_oleo", True)
    check("óleo seco (monstro): pega fogo", h_s.get("em_chamas_rodadas", 0) > 0)
    check("óleo na água (monstro): não pega fogo", h_w.get("em_chamas_rodadas", 0) == 0)
    check(f"óleo na água (monstro): ~metade ({d_w} vs {d_s})", 0 < d_w < d_s)
    _, h_fs, d_fs = monstro_arremessa("fogo_grego", False)
    r_fg, h_fg, d_fg = monstro_arremessa("fogo_grego", True)
    check("fogo grego na água (monstro): pega fogo", h_fg.get("em_chamas_rodadas", 0) > 0)
    check(f"fogo grego na água (monstro): dano cheio ({d_fg} vs {d_fs})", d_fg == d_fs and d_fg > 0)
    check("escopo não vaza (monstro)", r_fg._fogo_ignora_agua is False)
except Exception as e:
    import traceback
    traceback.print_exc()
    check(f"arremesso de monstro executou ({e})", False)


print("[10] fontes de fogo contra HERÓI e prisioneiro (exatamente uma metade)")


def hp_perdido(h):
    return h["max_hp"] - h["hp"]


def heroi_alvo(r, na_agua, pos=(8, 5), pid="h1"):
    h = heroi(r, pid, "Ana", "warrior", pos)
    h["hp"] = h["max_hp"] = 500
    h["resistances"] = []; h["immunities"] = []
    if na_agua:
        pinta(r, "agua", [pos])
    return h


def bola_heroi(na_agua):
    r = sala()
    h = heroi_alvo(r, na_agua)
    roda(r._aplicar_dano_area_fogo("x", 8, 5, 1, 12, 99, "R1", com_save=False))
    return hp_perdido(h)


b_seco, b_agua = bola_heroi(False), bola_heroi(True)
check(f"Bola de Fogo contra herói seco: cheio ({b_seco})", b_seco == 12)
check(f"Bola de Fogo contra herói na água: metade exata ({b_agua})", b_agua == 6)
r = sala(); h = heroi_alvo(r, True)
m = monstro(r, "goblin", (9, 5)); m["hp"] = m["max_hp"] = 200
m["immunities"] = []; m["resistances"] = []; m["weaknesses"] = []
pinta(r, "agua", r._monster_tiles(m))
roda(r._aplicar_dano_area_fogo("x", 8, 5, 1, 12, 99, "R1", com_save=False))
check(f"mesma Bola de Fogo: herói e monstro na água perdem o mesmo ({hp_perdido(h)} vs {200 - m['hp']})",
      hp_perdido(h) == 200 - m["hp"] == 6)


def zona_heroi(na_agua):
    r = sala()
    h = heroi_alvo(r, na_agua)
    r.zonas_especiais.append({"tipo": "bola_fogo", "ativa": True, "cx": 8, "cy": 5, "raio": 1,
                              "rodada_atual": 2, "dano_r2": 10, "dano_r3": 10, "caster": "x"})
    roda(r._verificar_entrada_zona_fogo(h, 8, 5))
    return hp_perdido(h)


z_seco, z_agua = zona_heroi(False), zona_heroi(True)
check(f"zona residual (pisar) seca/água: {z_seco}/{z_agua}", z_seco == 10 and z_agua == 5)
r = sala(); h = heroi_alvo(r, True)
roda(r._aplicar_dano_area_fogo("x", 8, 5, 1, 10, 99, "R2", com_save=False, apenas_no_chao=True))
check("zona residual (início de turno) na água: metade", hp_perdido(h) == 5)

r = sala()
r.prisoner = {"pos": [8, 5], "alive": True, "freed": True, "rescuer_pid": "p1",
              "hp": 100, "max_hp": 100, "ac": 10, "moves_left": 6}
pinta(r, "agua", [(8, 5)])
roda(r._aplicar_dano_area_fogo("x", 8, 5, 1, 12, 99, "R1", com_save=False))
check(f"Bola de Fogo contra prisioneiro na água: metade ({100 - r.prisoner['hp']})",
      100 - r.prisoner["hp"] == 6)


def explosao(na_agua):
    r = sala()
    h = heroi_alvo(r, na_agua, (6, 5))
    r.prisoner = {"pos": [6, 6], "alive": True, "freed": True, "rescuer_pid": "h1",
                  "hp": 100, "max_hp": 100, "ac": 10}
    if na_agua:
        pinta(r, "agua", [(6, 6)])
    elem = {"id": "e1", "pos": [5, 5], "vida_atual": 5, "tipo": "elemental_fogo", "owner": "h1"}
    orig_r = S.random.randint

    async def sem_save(*a, **k):
        return False, 1, 0, 1
    S.random.randint = lambda a, b: b
    r._save_mostrado = sem_save
    try:
        roda(r._explosao_elemental(elem, "h1"))
    finally:
        S.random.randint = orig_r
    return hp_perdido(h), 100 - r.prisoner["hp"]


e_seco, e_agua = explosao(False), explosao(True)
check(f"explosão do elemental seca: cheio {e_seco}", e_seco == (36, 36))
check(f"explosão do elemental na água (herói e prisioneiro): metade {e_agua}", e_agua == (18, 18))


def armadilha(na_agua):
    r = sala()
    h = heroi_alvo(r, na_agua)
    arm = {"id": "t1", "tipo": "armadilha_incendiaria", "pos": [8, 5], "criador": "x"}
    r.armadilhas.append(arm)
    roda(r._aplicar_efeito_armadilha(h, {"tipo": "dano", "valor": "10", "elemento": "fogo", "rodada": 1}, arm))
    impacto = hp_perdido(h)
    arm["efeitos_ativos"] = [{"alvo_id": h["id"], "valor": "10", "elemento": "fogo", "rodadas_restantes": 1}]
    roda(r._processar_efeitos_armadilha_turno())
    return impacto, hp_perdido(h) - impacto


a_seco, a_agua = armadilha(False), armadilha(True)
check(f"armadilha incendiária (impacto, tick) seca: {a_seco}", a_seco == (10, 10))
check(f"armadilha incendiária (impacto, tick) na água: {a_agua}", a_agua == (5, 5))

r = sala()
p = heroi(r, "h0", "Rex", "rogue", (3, 5))
aliado = heroi_alvo(r, True, (8, 5), "h2")
item = {"id": "granada", "name": "granada"}
defn = dict(S.ARREMESSAVEIS["granada"])
defn["elemento"] = "fogo"; defn["dano"] = "1d1+9"; defn["save"] = {}
defn["alcance"] = 12
p.setdefault("bag", []).append(item)
roda(r._throw_item_area(p, defn, item, 8, 5))
check(f"arremesso de área de fogo em aliado na água: metade ({hp_perdido(aliado)})", hp_perdido(aliado) == 5)

r = sala(); h = heroi_alvo(r, True)
h["resistances"] = [{"type": S.DMG_FIRE, "mode": "half"}]
check("resistente a fogo na água: um quarto (não um oitavo)",
      r._apply_damage_types(16, [S.DMG_FIRE], h) == 4)
check("helper não reduz elemento não-fogo", r._dano_fogo_na_agua(h, 10, "gelo") == 10)
r2 = sala()
check("helper não reduz fora da água", r2._dano_fogo_na_agua(heroi_alvo(r2, False), 10, "fogo") == 10)


print("[11] óleo de ÁREA, mortes dentro do escopo do Fogo Grego, explosão contra monstro, narração")

# Óleo pelo caminho de área (defn construído à mão: não depende do raio do catálogo).
defn_area = dict(S.ARREMESSAVEIS["frasco_oleo"])
defn_area.update({"alvo": "area", "area_raio": 1, "dano": "1d1+9", "save": {}, "alcance": 12})


def oleo_area(na_agua):
    r = sala()
    p = heroi(r, "h0", "Rex", "rogue", (3, 5))
    h = heroi_alvo(r, na_agua, (8, 5), "h2")
    m = monstro(r, "goblin", (9, 5)); m["hp"] = m["max_hp"] = 200
    m["immunities"] = []; m["resistances"] = []; m["weaknesses"] = []
    if na_agua:
        pinta(r, "agua", r._monster_tiles(m))
    item = {"id": "frasco_oleo", "name": "frasco_oleo"}
    p.setdefault("bag", []).append(item)
    roda(r._throw_item_area(p, defn_area, item, 8, 5))
    return r, h, m


r_s, h_s, m_s = oleo_area(False)
r_w, h_w, m_w = oleo_area(True)
check(f"óleo de área seco: herói cheio ({hp_perdido(h_s)}) e pega fogo",
      hp_perdido(h_s) == 10 and h_s.get("em_chamas_rodadas", 0) > 0)
check(f"óleo de área na água: herói metade ({hp_perdido(h_w)}), não pega fogo",
      hp_perdido(h_w) == 5 and h_w.get("em_chamas_rodadas", 0) == 0)
check(f"óleo de área na água: monstro metade ({200 - m_w['hp']} vs {200 - m_s['hp']}), não pega fogo",
      200 - m_w["hp"] == 5 and 200 - m_s["hp"] == 10 and m_w.get("em_chamas_rodadas", 0) == 0)
check("narração da área mostra o dano aplicado ao monstro na água",
      any(" 5 " in n for n in r_w.narr) and not any(" 10 " in n for n in r_w.narr))


# (A) Fogo Grego mata monstro com morte_explosiva: a explosão dele NÃO ignora a água.
def morte_com_fogo_grego(no_escopo):
    r = sala()
    h = heroi_alvo(r, True, (8, 5))
    m = monstro(r, "goblin", (9, 5)); m["hp"] = 0
    m.setdefault("special_abilities", []).append(
        {"id": "morte_explosiva", "name": "Morte Explosiva", "action_type": "passiva",
         "damage": "4d1+20", "damage_types": ["fire"], "radius": 1, "dc": 99, "duration": 0})
    orig = S.random.randint
    S.random.randint = lambda a, b: a
    try:
        if no_escopo:
            async def go():
                with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
                    await r._monster_dies(m, "h1")
            roda(go())
        else:
            roda(r._monster_dies(m, "h1"))
    finally:
        S.random.randint = orig
    return hp_perdido(h), r


d_normal, _ = morte_com_fogo_grego(False)
d_escopo, r_esc = morte_com_fogo_grego(True)
check(f"(A) explosão de morte dentro do escopo recebe a metade ({d_escopo} vs {d_normal})",
      d_normal > 0 and d_escopo == d_normal)
check("(A) a explosão da morte na água é a metade da seca",
      d_normal == 12)
check("(A) flag restaurada depois", r_esc._fogo_ignora_agua is False)


# (B) servo elemental de fogo e (C) Último Esforço: flag desligada lá dentro.
async def flag_em_animado_morre():
    r = sala()
    visto = {}

    async def esp(elem, killer=None):
        visto["flag"] = r._fogo_ignora_agua
    r._explosao_elemental = esp
    with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
        await r._animado_morre({"id": "a1", "pos": [5, 5], "vida_atual": 0, "tipo": "elemental_fogo",
                                "especial": "explosao_6d6"}, "h1")
        depois = r._fogo_ignora_agua
    return visto.get("flag"), depois, r._fogo_ignora_agua


f_b, depois_b, final_b = roda(flag_em_animado_morre())
check("(B) _animado_morre: flag False dentro, True restaurada no escopo, False no fim",
      f_b is False and depois_b is True and final_b is False)


async def flag_em_ultimo_esforco():
    r = sala()
    h = heroi(r, "h1", "Ana", "warrior", (5, 5))
    visto = {}

    async def abre(p):
        visto["flag"] = r._fogo_ignora_agua
    r._abrir_ultimo_esforco = abre
    r.tecnica_restante = lambda p, t: 0
    orig = S.tem_tecnica_equipada
    S.tem_tecnica_equipada = lambda p, t: t == "tecnica_ultimo_esforco"
    try:
        h.setdefault("technique_cooldowns", {})
        with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
            await r._player_dies("h1")
            depois = r._fogo_ignora_agua
    finally:
        S.tem_tecnica_equipada = orig
    return visto.get("flag"), depois


f_c, depois_c = roda(flag_em_ultimo_esforco())
check("(C) Último Esforço aberto de dentro do escopo: flag False lá, True restaurada depois",
      f_c is False and depois_c is True)


# M2/M3: explosão do elemental (6d6) contra monstro e herói na água.
def explosao_alvos(na_agua):
    r = sala()
    h = heroi_alvo(r, na_agua, (6, 5))
    m = monstro(r, "goblin", (4, 5)); m["hp"] = m["max_hp"] = 200
    m["immunities"] = []; m["resistances"] = []; m["weaknesses"] = []
    if na_agua:
        pinta(r, "agua", r._monster_tiles(m))
    elem = {"id": "e1", "pos": [5, 5], "vida_atual": 5, "tipo": "elemental_fogo", "owner": "h1"}

    async def sem_save(*a, **k):
        return False, 1, 0, 1
    r._save_mostrado = sem_save
    orig = S.random.randint
    S.random.randint = lambda a, b: b
    try:
        roda(r._explosao_elemental(elem, "h1"))
    finally:
        S.random.randint = orig
    return r, hp_perdido(h), 200 - m["hp"]


r_es, h_es, m_es = explosao_alvos(False)
r_ew, h_ew, m_ew = explosao_alvos(True)
check(f"explosão do elemental: monstro seco/água {m_es}/{m_ew}", m_es == 36 and m_ew == 18)
check(f"explosão do elemental: herói seco/água {h_es}/{h_ew}", h_es == 36 and h_ew == 18)
check("narracao do heroi na agua cita o dano ja cortado (18 de dano), nao o cheio",
      any("Ana" in n and "18 de dano" in n for n in r_ew.narr)
      and not any("Ana" in n and "36 de dano" in n for n in r_ew.narr))

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
