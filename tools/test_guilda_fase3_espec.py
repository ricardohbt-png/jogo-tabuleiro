"""Guilda dos Heróis — Fase 3: Técnicas Exclusivas (Mago/Clérigo).
Roda da raiz: python tools/test_guilda_fase3_espec.py"""
import asyncio, sys, os
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

def setup(phase="playing"):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r.round_num = 1
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r._tem_linha_de_visao = lambda *a, **k: True
    return r

def caster(cls="mage", tid_ex=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    p["magias_conhecidas"] = list(S.GRIMORIO_IMPLEMENTADAS)
    if tid_ex:
        p["guild_owned"]["tecnicas"] = [tid_ex]
        p["guild_equip"]["tecnica_exclusiva"] = tid_ex
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    print("\n[1] classe como lista — compra, catálogo, restrição")
    r = setup(phase="city")
    mago = caster("mage"); r.players["h"] = mago
    clerigo = caster("cleric"); r.players["c"] = clerigo
    guerreiro = caster("warrior"); r.players["w"] = guerreiro
    for pid_ in ("h", "c", "w"): r.players[pid_]["gold"] = 1000
    r._errs.clear()
    await r.handle_guild_buy("h", "tec_ex_aprimorar_magia")
    check("mago compra técnica exclusiva", "tec_ex_aprimorar_magia" in mago["guild_owned"]["tecnicas"])
    r._errs.clear()
    await r.handle_guild_buy("c", "tec_ex_aprimorar_magia")
    check("clérigo compra a mesma técnica", "tec_ex_aprimorar_magia" in clerigo["guild_owned"]["tecnicas"])
    r._errs.clear()
    await r.handle_guild_buy("w", "tec_ex_aprimorar_magia")
    check("guerreiro é recusado", "tec_ex_aprimorar_magia" not in guerreiro["guild_owned"]["tecnicas"])
    check("guerreiro recebe erro de classe", any("classe" in e.lower() for e in r._errs))
    ids_mage = [i["id"] for i in S.guild_items_for_class("mage")]
    ids_warr = [i["id"] for i in S.guild_items_for_class("warrior")]
    check("catálogo do mago inclui as 7 exclusivas",
          all(f"tec_ex_{n}" in ids_mage for n in
              ["aprimorar_magia", "estender_magia", "canalizacao_arcana", "empoderar_magia",
               "magia_geminada", "canalizacao_perfeita", "magia_acelerada"]))
    check("catálogo do guerreiro NÃO inclui nenhuma exclusiva",
          not any(i.startswith("tec_ex_") for i in ids_warr))

    print("\n[2] _testar_save: desvantagem rola 2d20 e usa o pior")
    r = setup()
    alvo = caster("mage")
    seq = iter([18, 5])
    orig_randint = S.random.randint
    S.random.randint = lambda a, b: next(seq)
    try:
        passou, d20, bonus, total = r._testar_save(alvo, "vontade", 10, desvantagem=True)
    finally:
        S.random.randint = orig_randint
    check("desvantagem usa o menor dos 2 rolls (5, não 18)", d20 == 5)

    seq2 = iter([18, 5])
    S.random.randint = lambda a, b: next(seq2)
    try:
        passou2, d20b, bonus2, total2 = r._testar_save(alvo, "vontade", 10)
    finally:
        S.random.randint = orig_randint
    check("sem desvantagem usa só a 1ª rolagem (18)", d20b == 18)

    print("\n[3] alcance_bonus chega aos 3 executores (Raio Congelante)")
    r = setup()
    p = caster("mage"); p["pos"] = [0, 0]; r.players["h"] = p
    r.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [4, 0], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    magia = S.GRIMORIO["raio_congelante"]
    r._errs.clear()
    await r._executar_raio_congelante(p, magia, {"target_id": "m1"}, 1, 0, 0)
    check("sem alcance_bonus: fora do alcance recusado", any("alcance" in e.lower() for e in r._errs))
    check("sem alcance_bonus: HP intacto", r.monsters["m1"]["hp"] == 30)
    r._errs.clear()
    await r._executar_raio_congelante(p, magia, {"target_id": "m1"}, 1, 0, 1)
    check("com alcance_bonus=1: alcance suficiente, dano aplicado", r.monsters["m1"]["hp"] < 30)

    print("\n[4] Catálogo completo das 7 técnicas + flags iniciais do jogador")
    especificacao = {
        "tec_ex_aprimorar_magia":      (5, 180, 2, 2),
        "tec_ex_estender_magia":       (5, 180, 2, 2),
        "tec_ex_canalizacao_arcana":   (5, 180, 4, 4),
        "tec_ex_empoderar_magia":      (8, 280, 4, 4),
        "tec_ex_magia_geminada":       (8, 280, 6, 6),
        "tec_ex_canalizacao_perfeita": (8, 280, 4, 4),
        "tec_ex_magia_acelerada":      (10, 350, 6, 6),
    }
    for tid, (rec, preco, cf, cs) in especificacao.items():
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga {rec}", it and it["recarga_rodadas"] == rec)
        check(f"{tid} preco {preco}", it and it["preco"] == preco)
        check(f"{tid} custo {cf}/{cs}", it and it["custo_fome"] == cf and it["custo_sede"] == cs)
        check(f"{tid} classe = [mage, cleric]", it and set(it["classe"]) == {"mage", "cleric"})
        check(f"{tid} exclusiva=True", it and it["exclusiva"] is True)
    check("magia_geminada tem alvo qualquer_vivo",
          S.guild_item("tec_ex_magia_geminada").get("alvo") == "qualquer_vivo")
    p0 = caster("mage")
    for flag in ["tec_ex_aprimorar_armado", "tec_ex_estender_armado", "tec_ex_canalizacao_armado",
                 "tec_ex_empoderar_armado", "tec_ex_canalizacao_perfeita_armado", "tec_ex_acelerada_armado"]:
        check(f"flag inicial {flag} = False", p0[flag] is False)
    check("flag inicial tec_ex_geminada_alvo2_id = None", p0["tec_ex_geminada_alvo2_id"] is None)

    print("\n[5] Helpers puros da Fase 3")
    r = setup()
    magia_save = {"id": "x", "save": "vontade"}
    magia_sem_save = {"id": "y"}
    p = caster("mage")
    check("dc_bonus=0 sem armar", r._tec_ex_dc_bonus(p, magia_save) == 0)
    p["tec_ex_aprimorar_armado"] = True
    check("dc_bonus=1 armado + magia com save", r._tec_ex_dc_bonus(p, magia_save) == 1)
    check("dc_bonus=0 armado + magia sem save", r._tec_ex_dc_bonus(p, magia_sem_save) == 0)

    magia_dur = {"id": "z", "duracao": "1d4"}
    magia_sem_dur = {"id": "w", "alcance_base": 3, "alcance_escala": 1}
    p2 = caster("mage"); p2["tec_ex_estender_armado"] = True
    check("estender: +1 duração quando a magia tem duracao",
          r._tec_ex_dur_alcance_bonus(p2, magia_dur) == (1, 0))
    check("estender: +1 alcance quando a magia NÃO tem duracao",
          r._tec_ex_dur_alcance_bonus(p2, magia_sem_dur) == (0, 1))
    p3 = caster("mage")
    check("estender: (0,0) sem armar", r._tec_ex_dur_alcance_bonus(p3, magia_dur) == (0, 0))

    magia_dano = {"id": "k", "dano_por_nivel": "1d6"}
    p4 = caster("mage"); p4["tec_ex_empoderar_armado"] = True
    check("empoderar: ×1.5 em magia com dano", r._tec_ex_dmg_mult(p4, magia_dano) == 1.5)
    check("empoderar: ×1 em magia sem dano", r._tec_ex_dmg_mult(p4, magia_sem_dur) == 1)
    p5 = caster("mage")
    check("empoderar: ×1 sem armar", r._tec_ex_dmg_mult(p5, magia_dano) == 1)

    print("\n[5b] _geminada_alvo2_valido")
    r2 = setup()
    pc = caster("mage"); pc["pos"] = [0, 0]
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [2, 0]
    dead_ally = make_player("d", "Dan", "warrior", 2); dead_ally["alive"] = False; dead_ally["pos"] = [1, 0]
    r2.players["a"] = ally
    r2.players["d"] = dead_ally
    monster = {"id": "m1", "name": "Alvo", "pos": [3, 0], "hp": 10, "max_hp": 10}
    dead_monster = {"id": "m2", "name": "Morto", "pos": [1, 0], "hp": 0, "max_hp": 10}
    magia_alvo_ofensiva = {"id": "raio_congelante", "tipo": "alvo", "alcance_base": 3, "alcance_escala": 1}
    magia_buff = {"id": "visao_escuro", "tipo": "buff_aliado", "alcance": 6}
    check("geminada: monstro vivo no alcance de magia ofensiva → válido",
          r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, monster))
    check("geminada: monstro morto → inválido",
          not r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, dead_monster))
    check("geminada: aliado num alvo ofensivo → inválido (tipo errado)",
          not r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, ally))
    check("geminada: aliado vivo no alcance de magia de buff → válido",
          r2._geminada_alvo2_valido(pc, magia_buff, ally))
    check("geminada: monstro num buff → inválido (tipo errado)",
          not r2._geminada_alvo2_valido(pc, magia_buff, monster))
    check("geminada: aliado morto → inválido",
          not r2._geminada_alvo2_valido(pc, magia_buff, dead_ally))
    far_monster = {"id": "m3", "name": "Longe", "pos": [10, 0], "hp": 10, "max_hp": 10}
    check("geminada: fora do alcance → inválido",
          not r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, far_monster))

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
