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

    print("\n[6] handle_usar_tecnica arma cada uma das 7 técnicas")
    for tid, flag, custo in [
        ("tec_ex_aprimorar_magia", "tec_ex_aprimorar_armado", (2, 2)),
        ("tec_ex_estender_magia", "tec_ex_estender_armado", (2, 2)),
        ("tec_ex_canalizacao_arcana", "tec_ex_canalizacao_armado", (4, 4)),
        ("tec_ex_empoderar_magia", "tec_ex_empoderar_armado", (4, 4)),
        ("tec_ex_canalizacao_perfeita", "tec_ex_canalizacao_perfeita_armado", (4, 4)),
        ("tec_ex_magia_acelerada", "tec_ex_acelerada_armado", (6, 6)),
    ]:
        r = setup(); r.current_pid = lambda: "h"
        p = caster("mage", tid_ex=tid); r.players["h"] = p
        f0, s0 = p["fome"], p["sede"]
        await r.handle_usar_tecnica("h", tid)
        check(f"{tid}: flag {flag} armada", p[flag] is True)
        # Estas 7 técnicas só ARMAM a próxima magia: entram em `efeitos_adiados`,
        # então custo e recarga só começam quando o efeito é realmente aplicado
        # (em handle_magia, via _consumir_tecnica_apos_efeito). Ativar e não
        # lançar não deve cobrar nada.
        check(f"{tid}: ativar não cobra fome/sede ainda",
              p["fome"] == f0 and p["sede"] == s0)
        check(f"{tid}: ativar não inicia a recarga ainda",
              r.tecnica_restante(p, tid) == 0)
        check(f"{tid}: fica pendente até o efeito",
              p.get("technique_pending", {}).get(tid) is True)
        # E o custo/recarga do catálogo é o esperado quando a hora chegar.
        _it = S.guild_item(tid)
        check(f"{tid}: catálogo declara custo {custo}",
              (_it["custo_fome"], _it["custo_sede"]) == custo)

    print("\n[6b] Magia Geminada — validação de alvo na ativação")
    r = setup(); r.current_pid = lambda: "h"
    p = caster("mage", tid_ex="tec_ex_magia_geminada"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1, 1]
    r.players["a"] = ally
    r._errs.clear()
    await r.handle_usar_tecnica("h", "tec_ex_magia_geminada", "h")
    check("geminada: recusa a si mesmo", any("você" in e.lower() for e in r._errs))
    check("geminada: flag não setada ao recusar", p["tec_ex_geminada_alvo2_id"] is None)
    r._errs.clear()
    dead = make_player("d", "Dan", "warrior", 2); dead["alive"] = False; dead["pos"] = [1, 1]
    r.players["d"] = dead
    await r.handle_usar_tecnica("h", "tec_ex_magia_geminada", "d")
    check("geminada: recusa alvo morto", any("vivo" in e.lower() for e in r._errs))
    await r.handle_usar_tecnica("h", "tec_ex_magia_geminada", "a")
    check("geminada: aceita aliado vivo", p["tec_ex_geminada_alvo2_id"] == "a")

    print("\n[7] handle_magia: integração das 7 técnicas exclusivas")

    def _mk_caster_room(tid_ex, cls="mage"):
        rr = setup(); rr.current_pid = lambda: "h"; rr._is_turn = lambda pid: pid == "h"
        pp = caster(cls, tid_ex=tid_ex); pp["pos"] = [0, 0]; pp["action_done"] = False
        rr.players["h"] = pp
        return rr, pp

    async def _fixed_dano(n, d, *_a, **_k):
        return n * d   # cada dado no valor máximo — determinístico

    # [7a] Aprimorar Magia: soma +1 no _mm_dc_bonus lido por _dif_magia
    rr, pp = _mk_caster_room("tec_ex_aprimorar_magia")
    await rr.handle_usar_tecnica("h", "tec_ex_aprimorar_magia")
    rr.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    dc_vistos = []
    orig_dif = rr._dif_magia
    rr._dif_magia = lambda c, m: (dc_vistos.append(c.get("_mm_dc_bonus")), orig_dif(c, m))[1]
    await rr.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("aprimorar: _mm_dc_bonus=1 no momento do save", dc_vistos and dc_vistos[0] == 1)
    check("aprimorar: flag consumida após lançar", pp["tec_ex_aprimorar_armado"] is False)

    # [7a2] Empilha com a Metamagia do 1f (Mago): +1 (1f) + 1 (Fase 3) = 2
    rr2, pp2 = _mk_caster_room("tec_ex_aprimorar_magia")
    pp2["aprimorar_ativo"] = True
    await rr2.handle_usar_tecnica("h", "tec_ex_aprimorar_magia")
    rr2.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    dc_vistos2 = []
    orig_dif2 = rr2._dif_magia
    rr2._dif_magia = lambda c, m: (dc_vistos2.append(c.get("_mm_dc_bonus")), orig_dif2(c, m))[1]
    await rr2.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("aprimorar: empilha com Metamagia do 1f (1+1=2)", dc_vistos2 and dc_vistos2[0] == 2)

    # [7b] Estender Magia — caminho de duração (Manto de Escuridão, círculo 2 → nível 3)
    # Usa o Manto e NÃO a Visão no Escuro: esta última passou a durar a missão
    # inteira (`visao_escuro_missao`) e nem declara `duracao`, então cai no ramo
    # de ALCANCE do Estender — quem exercita o ramo de duração é o Manto.
    rr3, pp3 = _mk_caster_room("tec_ex_estender_magia")
    pp3["level"] = 3
    rr3._rolar_dado = lambda spec: 5
    await rr3.handle_usar_tecnica("h", "tec_ex_estender_magia")
    await rr3.handle_magia("h", {"magia_id": "manto_escuridao"})
    check("estender: duração 5(base)+1(técnica)=6", pp3["visao_escuro_rodadas"] == 6)

    # Visão no Escuro dura a missão inteira e ignora bônus de duração.
    rr3b, pp3b = _mk_caster_room("tec_ex_estender_magia")
    pp3b["level"] = 3                      # círculo 2 precisa de nível 3
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1, 0]
    rr3b.players["a"] = ally
    await rr3b.handle_magia("h", {"magia_id": "visao_escuro", "target_id": "a"})
    check("visão no escuro: vale a missão toda", ally.get("visao_escuro_missao") is True)
    check("visão no escuro: sem contador de rodadas", "visao_escuro_rodadas" not in ally)

    # [7c] Estender Magia — caminho de alcance (Raio Congelante 1 casa além do alcance base)
    rr4, pp4 = _mk_caster_room("tec_ex_estender_magia")
    rr4.monsters = {"m1": {"id": "m1", "name": "Longe", "pos": [4, 0], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    await rr4.handle_usar_tecnica("h", "tec_ex_estender_magia")
    await rr4.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("estender: alcance+1 alcança alvo antes fora de alcance", rr4.monsters["m1"]["hp"] < 30)

    # [7d] Empoderar Magia — ×1,5 no dano
    rr5, pp5 = _mk_caster_room("tec_ex_empoderar_magia")
    rr5.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10}}
    rr5._rolar_dano_mostrado = _fixed_dano
    await rr5.handle_usar_tecnica("h", "tec_ex_empoderar_magia")
    await rr5.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    dano5 = 1000 - rr5.monsters["m1"]["hp"]
    rr6, pp6 = _mk_caster_room(None)
    rr6.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10}}
    rr6._rolar_dano_mostrado = _fixed_dano
    await rr6.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    dano6 = 1000 - rr6.monsters["m1"]["hp"]
    check("empoderar: dano ×1,5 vs sem técnica", dano5 == int(dano6 * 1.5 + 0.5))

    # [7e] Canalização Arcana — ignora Silêncio
    rr7, pp7 = _mk_caster_room("tec_ex_canalizacao_arcana")
    rr7._em_silencio = lambda pl: True
    rr7.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    rr7._errs.clear()
    await rr7.handle_usar_tecnica("h", "tec_ex_canalizacao_arcana")
    await rr7.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("canalização arcana: lança normalmente sob Silêncio",
          not any("silêncio" in e.lower() for e in rr7._errs))
    check("canalização arcana: dano aplicado", rr7.monsters["m1"]["hp"] < 30)

    rr8, pp8 = _mk_caster_room("tec_ex_canalizacao_arcana")
    rr8._em_silencio = lambda pl: True
    rr8.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    rr8._errs.clear()
    await rr8.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("sem canalização arcana: Silêncio bloqueia normalmente",
          any("silêncio" in e.lower() for e in rr8._errs))

    # [7f] Canalização Perfeita — desvantagem chega ao _save_mostrado
    rr9, pp9 = _mk_caster_room("tec_ex_canalizacao_perfeita")
    rr9.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    vistos_desv = []
    orig_save = rr9._save_mostrado
    async def spy_save(alvo, tipo, dif, extra_mod=0, desvantagem=False):
        vistos_desv.append(desvantagem)
        return await orig_save(alvo, tipo, dif, extra_mod=extra_mod, desvantagem=desvantagem)
    rr9._save_mostrado = spy_save
    await rr9.handle_usar_tecnica("h", "tec_ex_canalizacao_perfeita")
    await rr9.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("canalização perfeita: save do alvo pedido com desvantagem",
          vistos_desv and vistos_desv[0] is True)

    # [7g] Magia Geminada — aplica no 2º alvo também
    rr10, pp10 = _mk_caster_room("tec_ex_magia_geminada")
    rr10.monsters = {
        "m1": {"id": "m1", "name": "Alvo1", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10},
        "m2": {"id": "m2", "name": "Alvo2", "pos": [0, 2], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10},
    }
    await rr10.handle_usar_tecnica("h", "tec_ex_magia_geminada", "m2")
    await rr10.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("geminada: 1º alvo sofre dano", rr10.monsters["m1"]["hp"] < 30)
    check("geminada: 2º alvo também sofre dano", rr10.monsters["m2"]["hp"] < 30)
    check("geminada: flag consumida", pp10["tec_ex_geminada_alvo2_id"] is None)

    # [7h] Magia Acelerada — não consome a ação principal
    rr11, pp11 = _mk_caster_room("tec_ex_magia_acelerada")
    rr11.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    await rr11.handle_usar_tecnica("h", "tec_ex_magia_acelerada")
    await rr11.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("acelerada: action_done continua False", pp11["action_done"] is False)
    check("acelerada: flag consumida", pp11["tec_ex_acelerada_armado"] is False)
    rr12, pp12 = _mk_caster_room(None)
    rr12.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    await rr12.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("sem acelerada: action_done vira True normalmente", pp12["action_done"] is True)

    # [7i] Fortalecer Magia (Metamagia 1f, NÃO ocupa o slot exclusivo) + Magia
    # Geminada (Fase 3, slot exclusivo) juntas — ×1,25 (base, sem espec.
    # mago_fortalecer_2/3) aplica nos DOIS alvos. Nota: Empoderar Magia (Fase 3)
    # NÃO pode coexistir com Geminada no mesmo personagem — ambas são
    # "exclusiva":True e disputam o ÚNICO slot tecnica_exclusiva (handle_guild_equip
    # só permite 1 lá); Fortalecer, ao contrário, é a Metamagia do Mago (1f), que
    # não usa slot nenhum, então É uma combinação real alcançável em jogo.
    rr13, pp13 = _mk_caster_room("tec_ex_magia_geminada")
    pp13["fortalecer_ativo"] = True
    rr13.monsters = {
        "m1": {"id": "m1", "name": "Alvo1", "pos": [0, 1], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10},
        "m2": {"id": "m2", "name": "Alvo2", "pos": [0, 2], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10},
    }
    rr13._rolar_dano_mostrado = _fixed_dano
    await rr13.handle_usar_tecnica("h", "tec_ex_magia_geminada", "m2")
    await rr13.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    dano_m1 = 1000 - rr13.monsters["m1"]["hp"]
    dano_m2 = 1000 - rr13.monsters["m2"]["hp"]

    rr14, pp14 = _mk_caster_room(None)
    rr14.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10}}
    rr14._rolar_dano_mostrado = _fixed_dano
    await rr14.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    dano_base = 1000 - rr14.monsters["m1"]["hp"]
    dano_esperado = int(dano_base * 1.25 + 0.5)

    check("fortalecer+geminada: 1º alvo recebe ×1,25", dano_m1 == dano_esperado)
    check("fortalecer+geminada: 2º alvo (geminada) TAMBÉM recebe ×1,25", dano_m2 == dano_esperado)
    check("fortalecer+geminada: flag geminada consumida", pp13["tec_ex_geminada_alvo2_id"] is None)

    print("\n[8] handle_usar_tecnica funciona durante o Último Esforço (last stand)")
    r = setup(); r.current_pid = lambda: "outro"   # current_pid aponta p/ OUTRO jogador
    r.last_stand_pid = "h"                          # "h" está em Último Esforço
    p = caster("mage", tid_ex="tec_ex_aprimorar_magia"); r.players["h"] = p
    r._errs.clear()
    await r.handle_usar_tecnica("h", "tec_ex_aprimorar_magia")
    check("last stand: técnica exclusiva ativa normalmente", p["tec_ex_aprimorar_armado"] is True)
    check("last stand: sem erro de 'não é seu turno'", not any("turno" in e.lower() for e in r._errs))

    r2 = setup(); r2.current_pid = lambda: "outro"
    r2.last_stand_pid = "h"
    p2 = caster("warrior"); r2.players["h"] = p2
    p2["guild_owned"]["tecnicas"] = ["tecnica_mira_perfeita"]
    p2["guild_equip"]["tecnica"] = "tecnica_mira_perfeita"
    r2._errs.clear()
    await r2.handle_usar_tecnica("h", "tecnica_mira_perfeita")
    check("last stand: técnica genérica (Fase 2a) também funciona", p2["tecnica_mira_perfeita"] is True)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
