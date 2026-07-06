"""Técnicas da Guilda — Recarga Curta (Fase 2a). Roda: python tools/test_tecnicas_espec.py"""
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
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r.round_num = 1
    return r

def hero(cls="warrior", tid=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    if tid:
        p["guild_owned"]["tecnicas"] = [tid]
        p["guild_equip"]["tecnica"] = tid
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo — Recarga Curta")
    for tid in ["tecnica_mira_perfeita","tecnica_espirito_indomavel","tecnica_grito_guerra","tecnica_pressa"]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 3", it and it["recarga_rodadas"] == 3)
        check(f"{tid} preco 100", it and it["preco"] == 100)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("pressa custa 4/4", S.guild_item("tecnica_pressa")["custo_fome"] == 4
          and S.guild_item("tecnica_pressa")["custo_sede"] == 4)
    check("mira custa 2/2", S.guild_item("tecnica_mira_perfeita")["custo_fome"] == 2)

    # [2] Pressa
    print("\n[2] Pressa")
    r = setup()
    p = hero("warrior", "tecnica_pressa"); r.players["h"] = p
    r.current_pid = lambda: "h"
    spd = p["spd"]; p["moves_left"] = spd; f0, s0 = p["fome"], p["sede"]
    await r.handle_usar_tecnica("h", "tecnica_pressa")
    check("pressa: +spd de movimento", p["moves_left"] == spd + spd)
    check("pressa: custo 4/4", p["fome"] == f0 - 4 and p["sede"] == s0 - 4)
    check("pressa: recarga setada", r.tecnica_restante(p, "tecnica_pressa") > 0)

    # [3] Grito de Guerra
    print("\n[3] Grito de Guerra")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_grito_guerra"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1,1]
    ally["moves_left"] = ally["spd"]; r.players["a"] = ally
    p["moves_left"] = p["spd"]
    await r.handle_usar_tecnica("h", "tecnica_grito_guerra")
    check("grito: usuário +2 movimento", p["moves_left"] == p["spd"] + 2)
    check("grito: aliado +2 movimento", ally["moves_left"] == ally["spd"] + 2)
    check("grito: buff transitório setado", p["mov_bonus_ate"] == r.round_num + 1)
    # O buff DEVE fluir pelo cálculo autoritativo de movimento (_moves_base),
    # que é o que roda no reset de início de turno (senão o buff é descartado).
    check("grito: _moves_base do aliado inclui +2", r._moves_base(ally) == ally["spd"] + 2)
    check("grito: _grito_mov_bonus = 2 na janela", r._grito_mov_bonus(ally) == 2)
    # mov_bonus_ate = round_num+1 → cobre a rodada seguinte (o turno do aliado nela)
    r.round_num += 1
    check("grito: ainda ativo na rodada seguinte (o 'por 1 rodada')", r._grito_mov_bonus(ally) == 2)
    r.round_num += 1   # 2 rodadas após ativar → expira
    check("grito: expira 2 rodadas após ativar", r._grito_mov_bonus(ally) == 0)
    check("grito: _moves_base volta ao spd após expirar", r._moves_base(ally) == ally["spd"])

    # [4] Espírito Indomável
    print("\n[4] Espírito Indomável")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_espirito_indomavel"); r.players["h"] = p
    # Lentidão real usa os campos "lento"/"lento_rodadas"/"lento_pulou" (o campo
    # "lentidao" é só o id da magia — nunca um status na entidade).
    p["com_medo"] = True; p["medo_rodadas"] = 3; p["perde_turno"] = True
    p["lento"] = True; p["lento_rodadas"] = 2; p["lento_pulou"] = True
    await r.handle_usar_tecnica("h", "tecnica_espirito_indomavel")
    check("indomável: remove medo", not p.get("com_medo"))
    check("indomável: remove atordoamento", not p.get("perde_turno"))
    check("indomável: remove lentidão", not p.get("lento") and not p.get("lento_rodadas"))
    check("indomável: imunidade a silêncio setada", p["imune_silencio_ate"] == r.round_num + 1)
    # _em_silencio respeita a imunidade mesmo dentro de zona
    r._zonas_ativas = lambda tipo: [{"cx":0,"cy":0,"raio":3}] if tipo == "silencio" else []
    r._em_zona_quadrada = lambda x,y,z: True
    check("indomável: imune a silêncio ativo", r._em_silencio(p) is False)

    # [5] Mira Perfeita
    print("\n[5] Mira Perfeita")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_mira_perfeita"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_mira_perfeita")
    check("mira: flag armada", p.get("tecnica_mira_perfeita") is True)
    check("mira: recarga setada", r.tecnica_restante(p, "tecnica_mira_perfeita") > 0)
    # Integração: um ataque à distância consome a flag e passa vantagem ao rolar;
    # um ataque corpo a corpo NÃO consome (aguarda um ataque à distância).
    def _mk_attack_room(w_range):
        rr = setup(); rr.current_pid = lambda: "h"; rr._is_turn = lambda pid: True
        hh = hero("warrior"); hh["tecnica_mira_perfeita"] = True; hh["pos"] = [0,0]
        hh["weapon"] = {"id":"arco","name":"Arco","die":"1d6","stat":"dex","range":w_range} if w_range else \
                       {"id":"machado","name":"Machado","die":"1d6","stat":"str_"}
        rr.players["h"] = hh
        rr.monsters = {"m1": {"id":"m1","name":"Alvo","nome":"Alvo","pos":[0,1] if not w_range else [0,3],
                              "hp":30,"max_hp":30,"ac":10,"ca":10}}
        cap = {}
        def fake_rolar(atk, ac, vant=False, desv=False):
            cap["vant"] = vant; return (False, 5, 8, False, 3)   # erra (não precisa resolver dano)
        rr._rolar_ataque = fake_rolar
        rr._tem_linha_de_visao = lambda *a, **k: True
        rr._alcance_escuridao = lambda p_, t_, w_: w_
        return rr, hh, cap
    import asyncio as _a
    rr, hh, cap = _mk_attack_room(5)          # arco (à distância)
    await rr.handle_attack("h", "m1")
    check("mira: vantagem no ataque à distância", cap.get("vant") is True)
    check("mira: flag consumida após ataque à distância", hh.get("tecnica_mira_perfeita") is False)
    rr2, hh2, cap2 = _mk_attack_room(None)    # machado (corpo a corpo)
    await rr2.handle_attack("h", "m1")
    check("mira: flag NÃO consumida no corpo a corpo", hh2.get("tecnica_mira_perfeita") is True)

    # [6] Catálogo — Recarga Média (2b)
    print("\n[6] Catálogo — Recarga Média")
    for tid in ["tecnica_investida","tecnica_defesa_impecavel","tecnica_pressao_constante",
                "tecnica_tatica_defensiva","tecnica_passo_fantasma"]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 5", it and it["recarga_rodadas"] == 5)
        check(f"{tid} preco 180", it and it["preco"] == 180)
        check(f"{tid} custo 4/4", it and it["custo_fome"] == 4 and it["custo_sede"] == 4)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("pressao exige alvo monstro adjacente",
          S.guild_item("tecnica_pressao_constante").get("alvo") == "monstro_adjacente")
    check("tatica exige alvo aliado",
          S.guild_item("tecnica_tatica_defensiva").get("alvo") == "aliado_raio4")

    # [7] Pressão Constante
    print("\n[7] Pressão Constante")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_pressao_constante"); p["pos"] = [0,0]; r.players["h"] = p
    mob = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":14,"ca":14}
    r.monsters = {"m1": mob}
    await r.handle_usar_tecnica("h", "tecnica_pressao_constante", "m1")
    check("pressao: -2 CA marcado no alvo", mob.get("pressao_ca_val") == 2 and mob["pressao_ca_ate"] == r.round_num + 2)
    check("pressao: helper _pressao_ca_pen = 2 na janela", r._pressao_ca_pen(mob) == 2)
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 1
    p2 = hero("warrior", "tecnica_pressao_constante"); p2["pos"] = [0,0]; r2.players["h"] = p2
    far = {"id":"m2","name":"Orc","nome":"Orc","pos":[5,5],"hp":20,"max_hp":20,"ac":14,"ca":14}
    r2.monsters = {"m2": far}
    await r2.handle_usar_tecnica("h", "tecnica_pressao_constante", "m2")
    check("pressao: recusa alvo não-adjacente", far.get("pressao_ca_val") is None and any("adjacente" in e.lower() for e in r2._errs))
    r.round_num += 3
    check("pressao: expira", r._pressao_ca_pen(mob) == 0)

    # [8] Defesa Impecável
    print("\n[8] Defesa Impecável")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_defesa_impecavel"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_defesa_impecavel")
    check("defesa: janela setada", p["defesa_impecavel_ate"] == r.round_num + 1)
    check("defesa: _defesa_impecavel_ativa True", r._defesa_impecavel_ativa(p) is True)
    luccas = hero("rogue"); luccas["invisivel_sombras"] = True
    check("defesa: imune a furtivo", r._verificar_ataque_furtivo(luccas, p) is False)
    r.round_num += 2
    check("defesa: expira", r._defesa_impecavel_ativa(p) is False)

    # [9] Tática Defensiva
    print("\n[9] Tática Defensiva")
    import random as _rnd; _rnd.seed(3)
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    r._no_raio = lambda a,b,raio,*x,**k: max(abs(a["pos"][0]-b["pos"][0]), abs(a["pos"][1]-b["pos"][1])) <= raio
    p = hero("warrior", "tecnica_tatica_defensiva"); p["pos"] = [0,0]; p["hp"] = 20; p["max_hp"] = 20; r.players["h"] = p
    ally = make_player("a","Ana","cleric",1); ally["alive"]=True; ally["pos"]=[1,1]; ally["hp"]=20; ally["max_hp"]=20; r.players["a"]=ally
    await r.handle_usar_tecnica("h", "tecnica_tatica_defensiva", "a")
    check("tatica: alvo gravado no usuário", p["tatica_alvo"] == "a")
    check("tatica: janela 1d4 setada", p["tatica_ate"] >= r.round_num + 1 and p["tatica_ate"] <= r.round_num + 4)
    dano_alvo, transfer = await r._processar_dano_protetor("a", 10)
    check("tatica: aliado recebe metade", dano_alvo == 5)
    check("tatica: usuário recebe a outra metade", transfer is not None and transfer[0]["id"] == "h" and transfer[1] == 5)
    r3 = setup(); r3.current_pid = lambda: "h"; r3.round_num = 1; r3._no_raio = r._no_raio
    p3 = hero("warrior","tecnica_tatica_defensiva"); p3["pos"]=[0,0]; r3.players["h"]=p3
    far = make_player("a","Ana","cleric",1); far["alive"]=True; far["pos"]=[9,9]; r3.players["a"]=far
    await r3.handle_usar_tecnica("h","tecnica_tatica_defensiva","a")
    check("tatica: recusa aliado fora do raio 4", p3.get("tatica_alvo") is None)

    # [10] Passo Fantasma
    print("\n[10] Passo Fantasma")
    import random as _rnd2; _rnd2.seed(5)
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_passo_fantasma"); p["moves_left"] = p["spd"]; r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_passo_fantasma")
    check("passo: +2 movimento imediato", p["moves_left"] == p["spd"] + 2)
    check("passo: buff de mov transitório", p["mov_bonus_ate"] == r.round_num + 1 and p.get("mov_bonus_val") == 2)
    check("passo: janela 1d4 setada", p["passo_fantasma_ate"] >= r.round_num + 1 and p["passo_fantasma_ate"] <= r.round_num + 4)
    check("passo: _passo_fantasma_ativo True", r._passo_fantasma_ativo(p) is True)
    r.round_num += 5
    check("passo: expira", r._passo_fantasma_ativo(p) is False)

    # [11] Investida Heroica
    print("\n[11] Investida Heroica")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_investida"); p["pos"] = [0,0]; p["moves_left"] = p["spd"]; r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_investida")
    check("investida: dobra movimento", p["moves_left"] == p["spd"] + p["spd"])
    check("investida: armada + origem", p["investida_armada"] is True and p["investida_origem"] == [0,0])
    p["pos"] = [0,3]   # andou 3 em linha reta (coluna)
    check("investida: reto ≥2 melee → 2", r._investida_tecnica_bonus(p, is_ranged=False) == 2)
    check("investida: ranged → 0", r._investida_tecnica_bonus(p, is_ranged=True) == 0)
    p["pos"] = [1,1]   # L (dx=1,dy=1) → não é reto
    check("investida: L → 0", r._investida_tecnica_bonus(p, is_ranged=False) == 0)
    p["pos"] = [0,1]   # reto mas só 1
    check("investida: reto <2 → 0", r._investida_tecnica_bonus(p, is_ranged=False) == 0)
    p2 = hero("warrior"); p2["pos"] = [0,5]
    check("investida: sem flag → 0", r._investida_tecnica_bonus(p2, is_ranged=False) == 0)

    # [12] Catálogo — Reações (2c)
    print("\n[12] Catálogo — Reações")
    for tid, rec, preco, cf in [("tecnica_ataque_coordenado",5,180,4),("tecnica_sangue_frio",5,180,2),
                                ("tecnica_resistencia_absoluta",5,180,4),("tecnica_contra_ataque",8,280,6)]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga {rec}", it and it["recarga_rodadas"] == rec)
        check(f"{tid} preco {preco}", it and it["preco"] == preco)
        check(f"{tid} custo {cf}/{cf}", it and it["custo_fome"] == cf and it["custo_sede"] == cf)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("coordenado exige alvo aliado", S.guild_item("tecnica_ataque_coordenado").get("alvo") == "aliado")

    # [13] _ataque_basico_reativo (fundação)
    print("\n[13] _ataque_basico_reativo")
    r = setup()
    async def _mdies(*a, **k): return None
    r._monster_dies = _mdies
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 18, 20, False, 3)
    atacante = hero("warrior"); atacante["atk_bonus"] = 3
    atacante["weapon"] = {"id":"machado_basico","name":"Machado","die":"1d6","stat":"str_"}
    alvo = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":10,"ca":10}
    r.monsters = {"m1": alvo}
    hp0 = alvo["hp"]
    await r._ataque_basico_reativo(atacante, alvo)
    check("reativo: aplica dano no acerto", alvo["hp"] < hp0)
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 4, False, 1)
    alvo2 = {"id":"m2","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":10,"ca":10}
    hp2 = alvo2["hp"]
    await r._ataque_basico_reativo(atacante, alvo2)
    check("reativo: erro não aplica dano", alvo2["hp"] == hp2)
    alvo3 = {"id":"m3","name":"Orc","nome":"Orc","pos":[0,1],"hp":0,"max_hp":20,"ac":10,"ca":10}
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 18, 20, False, 3)
    await r._ataque_basico_reativo(atacante, alvo3)
    check("reativo: ignora alvo morto", alvo3["hp"] == 0)

    # [14] Resistência Absoluta
    print("\n[14] Resistência Absoluta")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_resistencia_absoluta"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_resistencia_absoluta")
    check("resist: janela 2 rodadas", p["resistencia_saves_ate"] == r.round_num + 2 and p["resistencia_saves_val"] == 2)
    check("resist: helper = 2 na janela", r._resistencia_saves_bonus(p) == 2)
    janela_ate = p["resistencia_saves_ate"]
    _, _d, sb_yes, _t = r._testar_save(p, "fortitude", 99)
    p["resistencia_saves_ate"] = 0  # desliga a janela p/ isolar a diferença
    _, _d2, sb_no, _t2 = r._testar_save(p, "fortitude", 99)
    check("resist: _testar_save soma +2", sb_yes - sb_no == 2)
    p["resistencia_saves_ate"] = janela_ate  # restaura p/ testar expiração natural
    r.round_num += 3
    check("resist: expira", r._resistencia_saves_bonus(p) == 0)

    # [15] Sangue Frio
    print("\n[15] Sangue Frio")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_sangue_frio"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_sangue_frio")
    check("sangue frio: armado", p.get("sangue_frio_armado") is True)
    check("sangue frio: consome e retorna True quando armado", r._sangue_frio_consumir(p) is True)
    check("sangue frio: desarmado após consumir", p.get("sangue_frio_armado") is False)
    check("sangue frio: sem re-roll se desarmado", r._sangue_frio_consumir(p) is False)

    # [16] Ataque Coordenado
    print("\n[16] Ataque Coordenado")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1; r.turn_index = 0
    r._alvo_no_alcance_arma = lambda p_, t_: True
    p = hero("warrior", "tecnica_ataque_coordenado"); p["pos"] = [0,0]; r.players["h"] = p
    ally = make_player("a","Ana","warrior",1); ally["alive"]=True; ally["pos"]=[1,0]
    ally["atk_bonus"]=3; ally["weapon"]={"id":"machado_basico","die":"1d6","stat":"str_"}; r.players["a"]=ally
    await r.handle_usar_tecnica("h", "tecnica_ataque_coordenado", "a")
    check("coord: par gravado", p["coordenado_alvo"] == "a" and p["coordenado_turno"] == r.turn_index)
    alvo = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":10,"ca":10}
    r.monsters = {"m1": alvo}; r._rolar_ataque = lambda a,b,v=False,d=False:(True,18,20,False,3)
    async def _mdies(*a,**k): return None
    r._monster_dies = _mdies
    hp0 = alvo["hp"]
    await r._reacao_ataque_coordenado(p, alvo)
    check("coord: par atacou o alvo", alvo["hp"] < hp0)
    check("coord: consumiu no turno", p["coordenado_alvo"] is None)
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 1
    p2 = hero("warrior","tecnica_ataque_coordenado"); r2.players["h"]=p2
    await r2.handle_usar_tecnica("h","tecnica_ataque_coordenado", None)
    check("coord: recusa sem aliado", p2.get("coordenado_alvo") is None)

    # [17] Contra-Ataque
    print("\n[17] Contra-Ataque")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_contra_ataque"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_contra_ataque")
    check("contra: janela até próximo turno", p["contra_ataque_ate"] == r.round_num + 1)
    def _w(wid, extra=None):
        pp = hero("warrior"); pp["weapon"] = {"id": wid, **(extra or {})}; return pp
    check("contra: machado (melee) elegível", r._arma_contra_ataque_ok(_w("machado_basico")) is True)
    check("contra: lança elegível", r._arma_contra_ataque_ok(_w("lanca", {"reach":"lanca"})) is True)
    check("contra: chicote elegível", r._arma_contra_ataque_ok(_w("chicote", {"range":2})) is True)
    check("contra: besta de mão elegível", r._arma_contra_ataque_ok(_w("hand_crossbow", {"range":4})) is True)
    check("contra: arco NÃO elegível", r._arma_contra_ataque_ok(_w("arco_curto", {"range":8})) is False)
    check("contra: besta pesada NÃO elegível", r._arma_contra_ataque_ok(_w("besta", {"range":10})) is False)
    # alcance por tipo de arma
    mob = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":9,"max_hp":9,"ac":10,"ca":10}
    melee = _w("machado_basico"); melee["pos"] = [0,0]
    r._is_adjacent_to_monster = lambda pos, t: max(abs(pos[0]-t["pos"][0]),abs(pos[1]-t["pos"][1]))<=1
    r._monster_tiles = lambda m: [m["pos"]]
    check("contra: melee adjacente no alcance", r._alvo_no_alcance_arma(melee, mob) is True)
    far = _w("machado_basico"); far["pos"] = [0,5]
    check("contra: melee longe fora do alcance", r._alvo_no_alcance_arma(far, mob) is False)
    hx = _w("hand_crossbow", {"range":4}); hx["pos"] = [0,0]
    check("contra: besta de mão alcança 4", r._alvo_no_alcance_arma(hx, {"id":"m2","pos":[0,4],"hp":9}) is True)

    # [18] Catálogo — Oportunidade (2d)
    print("\n[18] Catálogo — Oportunidade")
    it = S.guild_item("tecnica_oportunidade")
    check("existe tecnica_oportunidade", it is not None)
    check("oportunidade recarga 10", it and it["recarga_rodadas"] == 10)
    check("oportunidade preco 350", it and it["preco"] == 350)
    check("oportunidade custo 6/6", it and it["custo_fome"] == 6 and it["custo_sede"] == 6)
    check("oportunidade classe None", it and it["classe"] is None)
    check("oportunidade exige alvo aliado", it and it.get("alvo") == "aliado")
    p_tmpl = hero("warrior")
    check("template: oportunidade_credito default False", p_tmpl["oportunidade_credito"] is False)
    check("template: oportunidade_round default 0", p_tmpl["oportunidade_round"] == 0)

    # [19] _acao_bloqueada — crédito de Oportunidade
    print("\n[19] _acao_bloqueada — crédito de Oportunidade")
    r = setup(); r.round_num = 5
    p = hero("warrior"); p["action_done"] = True
    check("sem crédito: continua bloqueado", r._acao_bloqueada(p) is True)
    p["oportunidade_credito"] = True; p["oportunidade_round"] = 5
    check("com crédito válido (round bate): libera", r._acao_bloqueada(p) is False)
    check("libera: action_done volta a False", p["action_done"] is False)
    check("libera: crédito consumido", p["oportunidade_credito"] is False)
    # Crédito de rodada anterior (expirado) não libera
    p2 = hero("warrior"); p2["action_done"] = True
    p2["oportunidade_credito"] = True; p2["oportunidade_round"] = 3   # round atual é 5
    check("crédito de rodada anterior: expirado, continua bloqueado", r._acao_bloqueada(p2) is True)
    # Coexistência com Velocidade: os dois créditos não interferem entre si
    p3 = hero("warrior"); p3["action_done"] = True
    p3["velocidade_rodadas"] = 2; p3["velocidade_extra_usada"] = False
    p3["oportunidade_credito"] = True; p3["oportunidade_round"] = 5
    check("velocidade consumida primeiro", r._acao_bloqueada(p3) is False)
    check("velocidade: extra usada marcada", p3["velocidade_extra_usada"] is True)
    check("velocidade consumida NÃO gasta o crédito de Oportunidade", p3["oportunidade_credito"] is True)
    p3["action_done"] = True   # agiu de novo
    check("2ª ação extra: agora usa o crédito de Oportunidade", r._acao_bloqueada(p3) is False)
    check("crédito de Oportunidade agora consumido", p3["oportunidade_credito"] is False)
    p3["action_done"] = True   # agiu uma 3ª vez, sem mais créditos disponíveis
    check("3ª tentativa: sem mais créditos, bloqueado", r._acao_bloqueada(p3) is True)

    # [20] Oportunidade — concessão (handle_usar_tecnica)
    print("\n[20] Oportunidade — concessão")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 7
    p = hero("warrior", "tecnica_oportunidade"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1, 1]
    r.players["a"] = ally
    await r.handle_usar_tecnica("h", "tecnica_oportunidade", "a")
    check("concessão: crédito no aliado", ally["oportunidade_credito"] is True)
    check("concessão: round gravado", ally["oportunidade_round"] == 7)
    check("concessão: recarga setada no ativador", r.tecnica_restante(p, "tecnica_oportunidade") > 0)
    check("concessão: custo 6/6 debitado", p["fome"] == 20 - 6 and p["sede"] == 20 - 6)
    # Recusa: não pode escolher a si mesmo
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 7
    p2 = hero("warrior", "tecnica_oportunidade"); r2.players["h"] = p2
    await r2.handle_usar_tecnica("h", "tecnica_oportunidade", "h")
    check("concessão: recusa auto-alvo", p2.get("oportunidade_credito") is False
          and any("não pode ser você" in e.lower() for e in r2._errs))
    # Recusa: aliado morto
    r3 = setup(); r3.current_pid = lambda: "h"; r3.round_num = 7
    p3 = hero("warrior", "tecnica_oportunidade"); r3.players["h"] = p3
    morto = make_player("m", "Morto", "cleric", 1); morto["alive"] = False; r3.players["m"] = morto
    await r3.handle_usar_tecnica("h", "tecnica_oportunidade", "m")
    check("concessão: recusa aliado morto", morto.get("oportunidade_credito") is False)

    # [21] Oportunidade — via movimento
    print("\n[21] Oportunidade — via movimento")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 7
    p = hero("warrior"); p["moves_left"] = p["spd"]
    p["oportunidade_credito"] = True; p["oportunidade_round"] = 7
    r.players["h"] = p
    await r.handle_usar_oportunidade_movimento("h")
    check("movimento: +spd em moves_left", p["moves_left"] == p["spd"] + p["spd"])
    check("movimento: crédito consumido", p["oportunidade_credito"] is False)
    # Sem crédito válido: recusa e não mexe no movimento
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 7
    p2 = hero("warrior"); p2["moves_left"] = p2["spd"]; r2.players["h"] = p2
    await r2.handle_usar_oportunidade_movimento("h")
    check("movimento: recusa sem crédito", p2["moves_left"] == p2["spd"]
          and any("oportunidade" in e.lower() for e in r2._errs))
    # Crédito de rodada anterior (expirado): recusa
    r3 = setup(); r3.current_pid = lambda: "h"; r3.round_num = 8
    p3 = hero("warrior"); p3["moves_left"] = p3["spd"]
    p3["oportunidade_credito"] = True; p3["oportunidade_round"] = 7   # round atual é 8
    r3.players["h"] = p3
    await r3.handle_usar_oportunidade_movimento("h")
    check("movimento: recusa crédito expirado", p3["moves_left"] == p3["spd"])
    # Fora do próprio turno: recusa
    r4 = setup(); r4.current_pid = lambda: "outro"; r4.round_num = 7
    p4 = hero("warrior"); p4["moves_left"] = p4["spd"]
    p4["oportunidade_credito"] = True; p4["oportunidade_round"] = 7
    r4.players["h"] = p4
    await r4.handle_usar_oportunidade_movimento("h")
    check("movimento: recusa fora do próprio turno", p4["moves_left"] == p4["spd"])

    # [22] Handlers migrados para _acao_bloqueada (Oportunidade cobre todas as ações principais)
    print("\n[22] Handlers migrados para _acao_bloqueada")
    # Regressão: sem crédito, action_done=True continua bloqueando cada handler
    # exatamente como antes (mesma mensagem de erro, nenhuma mudança de estado).

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("mage"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_animar_mortos("h", {})
    check("animar_mortos: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_cura("h", {})
    check("cura: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_cura_area("h", {})
    check("cura_area: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_purificacao("h", {})
    check("purificacao: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_ressurreicao("h", {})
    check("ressurreicao: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("paladin"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_imposicao_maos("h", {})
    check("imposicao_maos: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("rogue"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_criar_armadilha("h", {})
    check("criar_armadilha: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("rogue"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_desarmar_armadilha("h", {})
    check("desarmar_armadilha: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    # libertar_prisioneiro: assinatura diferente (sem `data`), retorno silencioso
    # (sem mensagem de erro) — a checagem é `p.get("action_done")` embutida no `if`.
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior"); p["pos"] = [0, 0]; p["action_done"] = True
    r.players["h"] = p
    r.prisoner = {"pos": [0, 1], "alive": True, "freed": False}
    await r.handle_libertar_prisioneiro("h")
    check("libertar_prisioneiro: bloqueado sem crédito (regressão)", r.prisoner["freed"] is False)

    # Integração: COM crédito válido, libertar_prisioneiro (o mais simples dos 9) passa
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 3
    p2 = hero("warrior"); p2["pos"] = [0, 0]; p2["action_done"] = True
    p2["oportunidade_credito"] = True; p2["oportunidade_round"] = 3
    r2.players["h"] = p2
    r2.prisoner = {"pos": [0, 1], "alive": True, "freed": False}
    await r2.handle_libertar_prisioneiro("h")
    check("libertar_prisioneiro: crédito de Oportunidade libera a ação", r2.prisoner["freed"] is True)
    check("libertar_prisioneiro: crédito consumido", p2["oportunidade_credito"] is False)

    # [23] Catálogo — Recarga Longa (Fase 2e)
    print("\n[23] Catálogo — Recarga Longa (2e)")
    for tid, cf in [("tecnica_instinto_sobrevivencia", 6), ("tecnica_ultimo_esforco", 6),
                    ("tecnica_golpe_decisivo", 6), ("tecnica_sorte", 2)]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 10", it and it["recarga_rodadas"] == 10)
        check(f"{tid} preco 350", it and it["preco"] == 350)
        check(f"{tid} custo {cf}/{cf}", it and it["custo_fome"] == cf and it["custo_sede"] == cf)
        check(f"{tid} classe None", it and it["classe"] is None)

    # [24] Instinto de Sobrevivência
    print("\n[24] Instinto de Sobrevivência")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 5
    p = hero("warrior", "tecnica_instinto_sobrevivencia"); p["hp"] = 10; p["alive"] = True
    r.players["h"] = p
    await r._player_dies("h")
    check("instinto: sobrevive com 1 HP", p["hp"] == 1 and p["alive"] is True)
    check("instinto: recarga ativada", r.tecnica_restante(p, "tecnica_instinto_sobrevivencia") == 10)
    # Dentro da recarga, um novo "zerou o HP" mata normalmente.
    p["hp"] = 0
    await r._player_dies("h")
    check("instinto: morre normalmente dentro da recarga", p["alive"] is False)

    # Prioridade: Regeneração do Paladino (já existente) vence se ambos disponíveis.
    r2 = setup(); r2.current_pid = lambda: "h2"; r2.round_num = 1
    p2 = hero("paladin", "tecnica_instinto_sobrevivencia")
    p2["hp"] = 10; p2["alive"] = True; p2["regen_ressurge"] = True; p2["regen_pool"] = 5
    r2.players["h2"] = p2
    await r2._player_dies("h2")
    check("instinto: Regeneração do Paladino tem prioridade", p2["hp"] == 1 and p2["alive"] is True
          and r2.tecnica_restante(p2, "tecnica_instinto_sobrevivencia") == 0)

    # [25] Golpe Decisivo
    print("\n[25] Golpe Decisivo")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1; r._is_turn = lambda pid: True
    p = hero("warrior", "tecnica_golpe_decisivo"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_golpe_decisivo")
    check("golpe: flag armada", p.get("tecnica_golpe_decisivo_armado") is True)
    check("golpe: recarga setada", r.tecnica_restante(p, "tecnica_golpe_decisivo") == 10)

    # Integração: acerto SEM nat20 vira crítico (×2); acerto COM nat20 vira ×3.
    def _mk_room_golpe(natural20):
        rr = setup(); rr.current_pid = lambda: "h"; rr._is_turn = lambda pid: True
        hh = hero("warrior"); hh["tecnica_golpe_decisivo_armado"] = True; hh["pos"] = [0, 0]
        hh["atk_bonus"] = 0
        hh["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
        rr.players["h"] = hh
        rr.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                              "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
        roll = 20 if natural20 else 12
        rr._rolar_ataque = lambda atk, ac, v=False, d=False: (True, roll, roll + atk, roll == 20, None)
        rr._golpe_raw = lambda p_, raw: raw   # sem especialização do guerreiro interferindo
        return rr, hh
    rr1, hh1 = _mk_room_golpe(False)
    hp0 = rr1.monsters["m1"]["hp"]
    await rr1.handle_attack("h", "m1")
    dmg1 = hp0 - rr1.monsters["m1"]["hp"]
    check("golpe: acerto sem nat20 vira crítico (dobrado)", dmg1 >= 2)   # 1d6(min1)+0, dobrado >=2
    check("golpe: flag consumida após o ataque", hh1.get("tecnica_golpe_decisivo_armado") is False)

    rr2, hh2 = _mk_room_golpe(True)
    hp0b = rr2.monsters["m1"]["hp"]
    await rr2.handle_attack("h", "m1")
    dmg2 = hp0b - rr2.monsters["m1"]["hp"]
    check("golpe: nat20 enquanto armado triplica", dmg2 >= 3)

    # Regressão: SEM a técnica armada (nem Último Esforço), nat20 continua ×2 — não ×3.
    # Stub 1d6 sempre 4 (raw) + stat_bonus=mod(STR 18)=4 (guerreiro-padrão, sem _golpe_raw
    # multiplicando) → dano previsível: ×2 = 16, ×3 = 24 (discrimina claramente).
    rr_reg = setup(); rr_reg.current_pid = lambda: "h"; rr_reg._is_turn = lambda pid: True
    hh_reg = hero("warrior"); hh_reg["pos"] = [0, 0]; hh_reg["atk_bonus"] = 0
    hh_reg["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
    rr_reg.players["h"] = hh_reg
    rr_reg.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                              "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    rr_reg._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 20, 20 + atk, True, None)
    rr_reg._golpe_raw = lambda p_, raw: raw
    orig_roll_dice = S.roll_dice
    S.roll_dice = lambda die_str: 4
    try:
        hp0c = rr_reg.monsters["m1"]["hp"]
        await rr_reg.handle_attack("h", "m1")
        dmg_reg = hp0c - rr_reg.monsters["m1"]["hp"]
    finally:
        S.roll_dice = orig_roll_dice
    check("golpe: nat20 SEM técnica armada permanece ×2 (não ×3)", dmg_reg == 16)
    check("golpe: flag não estava setada (controle)", hh_reg.get("tecnica_golpe_decisivo_armado") is not True
          and hh_reg.get("ultimo_esforco_ativo") is not True)

    # Consumida mesmo em erro.
    rr3, hh3 = _mk_room_golpe(False)
    rr3._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 2, False, None)
    await rr3.handle_attack("h", "m1")
    check("golpe: consumida mesmo errando", hh3.get("tecnica_golpe_decisivo_armado") is False)

    # Expira no fim do turno sem uso.
    r4 = setup(); r4.current_pid = lambda: "h"
    p4 = hero("warrior"); p4["tecnica_golpe_decisivo_armado"] = True; p4["moves_left"] = p4["spd"]
    r4.players["h"] = p4
    r4.player_order = ["h"]; r4.turn_index = 0
    await r4.handle_end_turn("h")
    check("golpe: expira no fim do turno sem uso", p4.get("tecnica_golpe_decisivo_armado") is False)

    # [26] Sorte
    print("\n[26] Sorte")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1; r._is_turn = lambda pid: True
    p = hero("warrior", "tecnica_sorte"); p["pos"] = [0, 0]
    p["atk_bonus"] = 0
    p["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
    r.players["h"] = p
    r.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                         "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 2, False, None)   # erra
    await r.handle_attack("h", "m1")
    check("sorte: erro guarda ultimo_ataque_perdido", p.get("ultimo_ataque_perdido") is not None)
    check("sorte: alvo guardado é o m1", p["ultimo_ataque_perdido"]["target_id"] == "m1")

    async def _mdies(*a, **k): return None
    r._monster_dies = _mdies
    r._golpe_raw = lambda p_, raw: raw
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 15, 15, False, None)   # reroll acerta
    hp0 = r.monsters["m1"]["hp"]
    await r.handle_usar_tecnica("h", "tecnica_sorte")
    check("sorte: reroll acerta e aplica dano", r.monsters["m1"]["hp"] < hp0)
    check("sorte: limpa ultimo_ataque_perdido após usar", p.get("ultimo_ataque_perdido") is None)
    check("sorte: recarga setada", r.tecnica_restante(p, "tecnica_sorte") == 10)

    # Prova stored-vs-live: o reroll TEM que usar o eff_atk CONGELADO no momento
    # do erro original, e não recomputar a partir do atk_bonus atual do jogador.
    # Fluxo: erra um ataque de verdade via handle_attack (eff_atk calculado com
    # atk_bonus=0 → guardado em ultimo_ataque_perdido["eff_atk"]); DEPOIS mudamos
    # p["atk_bonus"] para um valor bem diferente (99) — se o código relesse o
    # estado ao vivo em vez do dict congelado, o reroll enxergaria esse 99. Em
    # vez de mockar _rolar_ataque com um valor de retorno fixo (o que mascararia
    # a diferença), capturamos o argumento `atk` recebido e comparamos com o
    # eff_atk que foi de fato gravado no dict — provando que usar_tecnica lê
    # perdido["eff_atk"] (congelado) e não toca p["atk_bonus"] de novo.
    rs = setup(); rs.current_pid = lambda: "h"; rs.round_num = 1; rs._is_turn = lambda pid: True
    ps = hero("warrior", "tecnica_sorte"); ps["pos"] = [0, 0]
    ps["atk_bonus"] = 0
    ps["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
    rs.players["h"] = ps
    rs.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                          "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    rs._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 2 + atk, False, None)   # erra
    await rs.handle_attack("h", "m1")
    eff_atk_congelado = ps["ultimo_ataque_perdido"]["eff_atk"]
    check("sorte(stored-vs-live): eff_atk foi congelado no miss", eff_atk_congelado == 0)

    # Muda o stat AO VIVO depois do erro — se o reroll recomputasse, usaria 99.
    ps["atk_bonus"] = 99

    atk_capturado = {}
    def _rolar_captura(atk, ac, v=False, d=False):
        atk_capturado["atk"] = atk
        return (True, 15, 15 + atk, False, None)
    rs._rolar_ataque = _rolar_captura
    rs._monster_dies = _mdies
    rs._golpe_raw = lambda p_, raw: raw
    await rs.handle_usar_tecnica("h", "tecnica_sorte")
    check("sorte(stored-vs-live): reroll usa o eff_atk CONGELADO, não o atk_bonus ao vivo",
          atk_capturado.get("atk") == eff_atk_congelado and atk_capturado.get("atk") != 99)

    # Sem erro recente: recusa educadamente.
    r2 = setup(); r2.current_pid = lambda: "h"; r2._is_turn = lambda pid: True
    p2 = hero("warrior", "tecnica_sorte"); r2.players["h"] = p2
    await r2.handle_usar_tecnica("h", "tecnica_sorte")
    check("sorte: recusa sem ataque recente", "Nenhum ataque recente" in (r2._errs[-1] if r2._errs else ""))

    # Limpo no fim do turno.
    r3 = setup(); r3.current_pid = lambda: "h"
    p3 = hero("warrior"); p3["ultimo_ataque_perdido"] = {"target_id": "m1"}; p3["moves_left"] = p3["spd"]
    r3.players["h"] = p3; r3.player_order = ["h"]; r3.turn_index = 0
    await r3.handle_end_turn("h")
    check("sorte: ultimo_ataque_perdido limpo no fim do turno", p3.get("ultimo_ataque_perdido") is None)

    # [27] Último Esforço — abertura da sub-fase
    print("\n[27] Último Esforço — abertura")
    r = setup(); r.current_pid = lambda: "outro"; r.round_num = 3
    p = hero("warrior", "tecnica_ultimo_esforco"); p["hp"] = 10; p["alive"] = True; p["spd"] = 6
    r.players["h"] = p
    r.players["outro"] = hero("cleric"); r.players["outro"]["id"] = "outro"
    r.player_order = ["h", "outro"]

    # Não sobrescrevemos _abrir_ultimo_esforco — deixamos rodar de verdade, mas
    # fechamos a janela "de fora" via uma task concorrente logo após ela abrir.
    # IMPORTANTE: hp=1/ativo=True só valem ENQUANTO a janela está aberta — uma
    # vez que ela fecha (aqui, via este stub; na Task 6, via handle_end_turn de
    # verdade), _player_dies cai no fluxo normal de morte (hp=0/alive=False).
    # Por isso o check de "HP=1" precisa rodar DENTRO da task concorrente, no
    # momento em que a janela está detectada aberta — não depois que
    # _player_dies() já retornou (nesse ponto a morte já foi finalizada).
    async def _fechar_logo():
        while r.last_stand_pid != "h":
            await asyncio.sleep(0)
        check("último esforço: HP=1 enquanto a janela está aberta", p["hp"] == 1)
        check("último esforço: ainda vivo durante a janela", p["alive"] is True)
        check("último esforço: flag ativa durante a janela", p.get("ultimo_esforco_ativo") is True)
        r.players["h"]["ultimo_esforco_turnos_restantes"] = 0
        r.last_stand_pid = None
        r.last_stand_event.set()
    asyncio.create_task(_fechar_logo())
    await r._player_dies("h")
    check("último esforço: morte finalizada após a janela fechar", p["alive"] is False)
    check("último esforço: flag ativa desligada ao fechar", p.get("ultimo_esforco_ativo") is False)
    check("último esforço: recarga setada", r.tecnica_restante(p, "tecnica_ultimo_esforco") == 10)

    # _is_turn aceita o pid em último esforço mesmo sem ser current_pid()
    r2 = setup(); r2.current_pid = lambda: "outro"
    r2.last_stand_pid = "h"
    check("último esforço: _is_turn aceita last_stand_pid", r2._is_turn("h") is True)
    check("último esforço: _is_turn normal p/ outros", r2._is_turn("ninguem") is False)

    # Não sobrepõe uma janela já aberta de OUTRO herói (2 mortes na mesma fase).
    r3 = setup(); r3.current_pid = lambda: "z"; r3.round_num = 1
    r3.last_stand_pid = "outro_heroi"   # janela já ativa de outro jogador
    p3 = hero("warrior", "tecnica_ultimo_esforco"); p3["hp"] = 0; p3["alive"] = True
    r3.players["h"] = p3
    await r3._player_dies("h")
    check("último esforço: 2ª morte simultânea não abre 2ª janela", p3["alive"] is False and p3["hp"] == 0)
    check("último esforço: janela original preservada", r3.last_stand_pid == "outro_heroi")
    check("último esforço: recarga NÃO consumida (técnica não disparou)",
          r3.tecnica_restante(p3, "tecnica_ultimo_esforco") == 0)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
