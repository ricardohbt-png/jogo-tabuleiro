"""Simulador do editor ("Testar como Mestre") — prólogo de turno, virada de
rodada e habilidades no controle manual. Roda da raiz:
    python tools/test_simulador_turno.py

Dirige a sala descartável REAL (`_criar_sala_teste_masmorra`) com heróis de
teste e a fila `test_combat`, sem navegador. Cada seção reproduz um defeito
encontrado em 2026-09-15: o simulador pulava `_upkeep_inicio_turno_monstro`,
`_start_initiative_player_turn`, o reset do `handle_end_turn` e a virada de
rodada — então recargas, ticks, regeneração e controle de multidão congelavam.
"""
import asyncio, copy, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

W = H = 14
MASTER = "MASTER"

def _dungeon(monsters):
    base = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       "dungeons", "Arena.json"), encoding="utf-8"))
    d = copy.deepcopy(base)
    d["grid"] = {"w": W, "h": H}
    d["tiles"] = [[S.FLOOR] * W for _ in range(H)]
    for x in range(W): d["tiles"][0][x] = S.WALL; d["tiles"][H - 1][x] = S.WALL
    for y in range(H): d["tiles"][y][0] = S.WALL; d["tiles"][y][W - 1] = S.WALL
    d["rooms"] = [{"id": 0, "x": 1, "y": 1, "w": W - 2, "h": H - 2, "role": "entrance", "locked": False, "doors": []}]
    d["entrance"] = {"x": 2, "y": 2}
    d["hero_spawns"] = []
    d["monsters"] = [dict({"room_id": 0, "boss": False, "target": False}, **m) for m in monsters]
    for k in ("chests", "traps", "decorations", "secret_passages", "falas", "master_reinforcements"):
        d[k] = []
    d["prisoner"] = None; d["materiais"] = {}; d["door_conditions"] = {}
    d["objectives"] = {"primary": {"type": "kill_all"}, "secondary": []}
    return d

def sala(monsters):
    """Sala de teste real com o Mestre conectado e as mensagens capturadas."""
    room, err, _token = S._criar_sala_teste_masmorra(_dungeon(monsters))
    assert room, err
    room.master_pid = MASTER; room.master_name = "Mestre"
    room.connections[MASTER] = object()
    room._errs = []; room._narr = []
    async def send_to(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            room._errs.append(str(msg.get("msg", "")))
    async def broadcast(msg, *a, **k): pass
    async def gm_say(txt, *a, **k): room._narr.append(str(txt))
    async def push_state(*a, **k): pass
    room.send_to = send_to; room.broadcast = broadcast; room.gm_say = gm_say; room.push_state = push_state
    return room

async def heroi(room, cls, x, y):
    await room.handle_mestre_adicionar_heroi_teste(MASTER, cls, x, y)
    return room.players[f"test_hero_{cls}"]

def monstro(room, tipo=None):
    return next(m for m in room.monsters.values() if tipo is None or m["type"] == tipo)

async def iniciar(room):
    await room.handle_teste_iniciar_combate(MASTER)

def ator(room):
    return room._teste_combate_ator()

async def ir_para(room, kind, id_):
    """Avança a fila (encerrando vezes) até o ator pedido abrir o turno."""
    for _ in range(20):
        a = ator(room)
        if a and a["kind"] == kind and a["id"] == id_:
            return True
        await room.handle_teste_encerrar_vez(MASTER)
        if not room.test_combat.get("active"):
            return False
    return False

async def proxima_vez(room, kind, id_):
    """Encerra a vez atual e avança até o ator pedido (garante 1 troca)."""
    await room.handle_teste_encerrar_vez(MASTER)
    return await ir_para(room, kind, id_)

def acerta_sempre(room):
    room._rolar_ataque = lambda *a, **k: (True, 15, 15, False, None)


async def main():
    print("\n[1] Recarga de habilidade do monstro anda a cada rodada")
    r = sala([{"type": "molochus_adulto", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 4, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"])
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "explosao_vapor", h["id"])
    check("Explosão de Vapor entra em recarga 6", m.get("ability_cooldowns", {}).get("explosao_vapor") == 6)
    await proxima_vez(r, "monster", m["id"])
    check("uma rodada depois a recarga caiu para 5", m["ability_cooldowns"].get("explosao_vapor") == 5)

    print("\n[2] Regeneração no início do turno do monstro")
    for tipo in ("troll", "lobisomem"):
        r = sala([{"type": tipo, "pos": [6, 6]}])
        h = await heroi(r, "warrior", 4, 6); h["hp"] = h["max_hp"] = 500
        await iniciar(r); m = monstro(r)
        m["hp"] = max(1, m["max_hp"] // 3); hp0 = m["hp"]
        await ir_para(r, "monster", m["id"])
        await proxima_vez(r, "monster", m["id"])
        check(f"{tipo} regenera ao abrir o turno seguinte", m["hp"] > hp0)

    print("\n[3] Troll a 0 HP continua na fila e regenera (a simulação não encerra)")
    r = sala([{"type": "troll", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "hero", h["id"])
    acerta_sempre(r); m["hp"] = 1
    await r.handle_teste_acao_heroi(MASTER, h["id"], "attack", {"target_id": m["id"], "target_pos": m["pos"], "buffs": []})
    check("troll caiu e ficou regenerando", m["hp"] <= 0 and m.get("troll_regenerando"))
    check("a simulação continua ativa", r.test_combat.get("active") is True)
    chegou = await ir_para(r, "monster", m["id"])
    check("o troll recebe o turno com 0 HP", chegou)
    check("e volta com HP positivo", m["hp"] > 0)

    print("\n[4] Estado que consome o turno pula o monstro na fila")
    r = sala([{"type": "goblin", "pos": [6, 6]}, {"type": "goblin", "pos": [8, 8]}])
    h = await heroi(r, "warrior", 4, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    m["perde_turno"] = True
    await ir_para(r, "hero", h["id"])
    await r.handle_teste_encerrar_vez(MASTER)
    a = ator(r)
    check("o goblin com perde_turno não recebeu a vez", not (a and a["kind"] == "monster" and a["id"] == m["id"]))
    check("a flag foi consumida", not m.get("perde_turno"))

    print("\n[5] Flags de turno do herói expiram ao encerrar a vez")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r); m["hp"] = m["max_hp"] = 1000
    await ir_para(r, "hero", h["id"]); acerta_sempre(r)
    await r.handle_teste_acao_heroi(MASTER, h["id"], "attack", {"target_id": m["id"], "target_pos": m["pos"], "buffs": ["golpe_devastador"]})
    check("Golpe Devastador armado neste turno", h.get("skill_dobrar_dano") is True)
    await proxima_vez(r, "hero", h["id"])
    check("no turno seguinte o Golpe Devastador expirou", h.get("skill_dobrar_dano") is False)
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    h = await heroi(r, "mage", 4, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); await ir_para(r, "hero", h["id"])
    await r.handle_teste_acao_heroi(MASTER, h["id"], "hero_skill", {"skill_id": "fortalecer_magia"})
    check("Fortalecer armado", h.get("fortalecer_ativo") is True)
    await proxima_vez(r, "hero", h["id"])
    check("Fortalecer expirou no turno seguinte", h.get("fortalecer_ativo") is False)

    print("\n[6] Veneno no herói tica e expira")
    r = sala([{"type": "escorpiao_pedra", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500; h["ac"] = 0; h["fort"] = -50
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"])
    for _ in range(6):
        m["_master_acted"] = False; m["master_attack_charges"] = {0: 2, 1: 1}
        await r.handle_mestre_atacar_monstro(MASTER, m["id"], h["id"], 1)
        if h.get("efeitos_veneno"): break
    check("herói envenenado pelo Ferrão", bool(h.get("efeitos_veneno")))
    dur0 = h["efeitos_veneno"][0]["duracao"]
    await proxima_vez(r, "hero", h["id"])
    dur1 = (h.get("efeitos_veneno") or [{"duracao": 0}])[0]["duracao"]
    check("a duração do veneno diminuiu no turno do herói", dur1 < dur0)

    print("\n[7] Em chamas tica na virada de rodada")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 4, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); h["em_chamas_rodadas"] = 3; hp0 = h["hp"]
    await ir_para(r, "hero", h["id"]); await proxima_vez(r, "hero", h["id"])
    check("o herói em chamas perdeu HP", h["hp"] < hp0)
    check("e o contador de chamas caiu", h.get("em_chamas_rodadas", 3) < 3)

    print("\n[8] Regeneração Divina cura no início do turno de Richard")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    h = await heroi(r, "paladin", 4, 6)
    await iniciar(r); await ir_para(r, "hero", h["id"]); h["hp"] = 3
    await r.handle_teste_acao_heroi(MASTER, h["id"], "hero_skill", {"skill_id": "regeneracao_divina"})
    check("Regeneração ativada", h.get("regeneracao_ativa") is True)
    await proxima_vez(r, "hero", h["id"])
    check("Richard curou ao abrir o turno seguinte", h["hp"] > 3)

    print("\n[9] Lobo no controle manual: Caça em Bando e Derrubar")
    r = sala([{"type": "lobo_cinzento", "pos": [6, 6]}, {"type": "lobo_cinzento", "pos": [5, 7]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500; h["ac"] = 0; h["ref_"] = -50
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"]); acerta_sempre(r)
    n = len(r._narr); h["moves_left"] = 6
    await r.handle_mestre_atacar_monstro(MASTER, m["id"], h["id"], 0)
    falas = " ".join(r._narr[n:])
    check("Caça em Bando anunciada (+2) com outro lobo adjacente ao alvo", "bando" in falas.lower())
    check("Derrubar: herói perde o movimento ao falhar o save", h.get("moves_left") == 0 and "derrubad" in falas.lower())

    print("\n[10] Troll no controle manual: técnicas armadas pelo Mestre")
    r = sala([{"type": "troll", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"])
    r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "golpe_devastador_troll", None)
    check("Golpe Devastador arma o próximo golpe", m.get("_troll_devastador_ataque") is True and not r._errs)
    check("Golpe Devastador entra em recarga 4", m.get("ability_cooldowns", {}).get("golpe_devastador_troll") == 4)
    m["_master_bonus_acted"] = False; r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "pressao_constante_troll", h["id"])
    check("só uma técnica de combate por turno (como na IA)", bool(r._errs) and not h.get("troll_pressao_ca"))
    r = sala([{"type": "troll", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"]); r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "pressao_constante_troll", h["id"])
    check("Pressão Constante reduz a CA do alvo adjacente", h.get("troll_pressao_ca") == 2 and not r._errs)
    r = sala([{"type": "troll", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 2, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"])
    await r.handle_mestre_mover_monstro_para(MASTER, m["id"], 3, 6)
    r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "investida_brutal_troll", None)
    check("Investida Brutal após andar 3+ casas", m.get("_troll_investida_ataque") is True and not r._errs)

    print("\n[11] Orc: Fúria Cega liga ao abrir o turno após sofrer dano")
    r = sala([{"type": "orc_guerreiro", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"])
    check("sem dano, sem fúria", not m.get("furia_cega"))
    m["hp"] -= 3
    await proxima_vez(r, "monster", m["id"])
    check("com dano desde o turno anterior, enfurece", m.get("furia_cega") is True)

    print("\n[12] Goblin Combatente: Arremesso manual como ação bônus")
    r = sala([{"type": "goblin_combatente", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 8, 6); h["hp"] = h["max_hp"] = 500; h["ac"] = 0
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"]); r._errs.clear()
    n = len(r._narr)
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "arremesso", h["id"])
    check("arremessou a adaga no herói a 2 casas", not r._errs and any("adaga" in f.lower() for f in r._narr[n:]))
    check("gastou a ação bônus, não a principal", m.get("_master_bonus_acted") is True and not m.get("_master_acted"))

    print("\n[13] Devorador de Metal: Mordida Corrosiva no acerto manual")
    r = sala([{"type": "devorador_metal", "pos": [6, 6]}])
    h = await heroi(r, "paladin", 5, 6); h["hp"] = h["max_hp"] = 500; h["ac"] = 0
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"]); acerta_sempre(r)
    n = len(r._narr)
    await r.handle_mestre_atacar_monstro(MASTER, m["id"], h["id"], 0)
    check("a cota de malha do paladino foi corroída", any("corro" in f.lower() for f in r._narr[n:]))

    print("\n[14] Necromante: Concentração Sombria no prólogo do turno")
    r = sala([{"type": "necromante", "pos": [6, 6]}])
    h = await heroi(r, "warrior", 5, 6); h["hp"] = h["max_hp"] = 500
    await iniciar(r); m = monstro(r)
    await ir_para(r, "monster", m["id"])
    m["hp"] -= 2; m["will"] = -50
    n = len(r._narr)
    await proxima_vez(r, "monster", m["id"])
    check("perdeu a concentração ao sofrer dano (Vontade falhou)", any("concentra" in f.lower() for f in r._narr[n:]))
    r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, m["id"], "bola_fogo", h["id"])
    check("sem magia neste turno", bool(r._errs))

    print("\n[15] Mago/Clérigo de teste nascem com as magias implementadas da classe")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    mago = await heroi(r, "mage", 4, 6); cler = await heroi(r, "cleric", 4, 7)
    check("mago conhece Bola de Fogo", "bola_fogo" in (mago.get("magias_conhecidas") or []))
    check("clérigo conhece Abençoar", "abencoar" in (cler.get("magias_conhecidas") or []))
    check("só magias implementadas e da própria classe",
          all(mid in S.GRIMORIO_IMPLEMENTADAS and "mage" in S.GRIMORIO[mid].get("classe", [])
              for mid in mago["magias_conhecidas"]))
    await iniciar(r); await ir_para(r, "hero", mago["id"]); r._errs.clear()
    g = monstro(r)
    await r.handle_teste_acao_heroi(MASTER, mago["id"], "magia", {"magia_id": "bola_fogo", "tx": g["pos"][0], "ty": g["pos"][1]})
    check("Bola de Fogo lança sem erro", not r._errs)

    print("\n[16] Purificação sem `tipo`: a ponte infere o efeito do alvo")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    cler = await heroi(r, "cleric", 4, 6); ali = await heroi(r, "warrior", 4, 7)
    await iniciar(r); await ir_para(r, "hero", cler["id"]); r._errs.clear()
    ali["efeitos_veneno"] = [{"veneno_id": "veneno_escorpiao_pedra", "nome": "Veneno", "operacao": "penalidade",
                             "atributos": [("ataque", -1)], "duracao": 2}]
    await r.handle_teste_acao_heroi(MASTER, cler["id"], "hero_skill", {"skill_id": "purificacao", "target_id": ali["id"]})
    check("purificou o veneno do aliado sem `tipo` no payload", not r._errs and not ali.get("efeitos_veneno"))

    print("\n[17] Guerreiro da Luz sem `bonus`: a ponte usa um preset")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    pal = await heroi(r, "paladin", 4, 6)
    await iniciar(r); await ir_para(r, "hero", pal["id"]); r._errs.clear()
    await r.handle_teste_acao_heroi(MASTER, pal["id"], "hero_skill", {"skill_id": "guerreiro_luz"})
    check("Guerreiro da Luz ativou com preset", not r._errs and pal.get("guerreiro_luz_ativo") is True)

    print("\n[18] Ladino de teste nasce com um frasco de veneno para o Veneno Rápido")
    r = sala([{"type": "goblin", "pos": [6, 6]}])
    lad = await heroi(r, "rogue", 4, 6)
    frasco = next((i for i in lad.get("bag", []) if i.get("effect") == "coat_poison"), None)
    check("há um frasco na bolsa", frasco is not None)
    await iniciar(r); await ir_para(r, "hero", lad["id"]); r._errs.clear()
    await r.handle_teste_acao_heroi(MASTER, lad["id"], "hero_skill", {"skill_id": "veneno_rapido", "veneno_id": (frasco or {}).get("veneno_id")})
    check("Veneno Rápido untou a arma", not r._errs and bool(r._weapon_poison_slots(lad)))

    print("\n[19] Fúria Berserker do Gigante no Manual aceita criatura adjacente (mesa livre)")
    # O simulador exige um herói na fila, mas o alvo da Fúria é OUTRA criatura:
    # o ramo recusava tudo que não fosse herói com "Alvo fora do alcance".
    r = sala([{"type": "gigante_guerra", "pos": [6, 6]}, {"type": "goblin", "pos": [5, 6]}])
    h = await heroi(r, "warrior", 11, 11); h["hp"] = h["max_hp"] = 500
    await iniciar(r); g = monstro(r, "gigante_guerra"); gob = monstro(r, "goblin")
    gob["hp"] = gob["max_hp"] = 500
    await ir_para(r, "monster", g["id"]); r._errs.clear(); acerta_sempre(r)
    golpes = []
    _orig = r._execute_one_monster_attack
    async def _conta(m, atk, tobj, *a, **k):
        golpes.append(tobj["obj"].get("id")); return await _orig(m, atk, tobj, *a, **k)
    r._execute_one_monster_attack = _conta
    await r.handle_mestre_usar_habilidade(MASTER, g["id"], "furia_berserker", gob["id"])
    check("sem erro de alcance contra o goblin adjacente", not r._errs)
    check("dois golpes no goblin (ataque + adicional)", golpes == [gob["id"]] * 2)
    check("goblin sofreu dano", gob["hp"] < 500)

    print("\n[19b] Fúria contra criatura 2×2 adjacente pela casa que não é a âncora")
    r = sala([{"type": "gigante_guerra", "pos": [6, 6]}, {"type": "gigante_guerra", "pos": [8, 5]}])
    h = await heroi(r, "warrior", 11, 11); h["hp"] = h["max_hp"] = 500
    await iniciar(r)
    gs = [m for m in r.monsters.values() if m["type"] == "gigante_guerra"]
    g = next(m for m in gs if m["pos"] == [6, 6]); alvo = next(m for m in gs if m["pos"] == [8, 5])
    await ir_para(r, "monster", g["id"]); r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, g["id"], "furia_berserker", alvo["id"])
    check("o footprint do alvo conta, não só a âncora", not r._errs)

    print("\n[19c] Pressão Constante do Troll no Manual aceita criatura adjacente e a penaliza")
    r = sala([{"type": "troll", "pos": [6, 6]}, {"type": "goblin", "pos": [7, 6]}])
    h = await heroi(r, "warrior", 11, 11); h["hp"] = h["max_hp"] = 500
    await iniciar(r); tr = monstro(r, "troll"); gob = monstro(r, "goblin")
    gob["hp"] = gob["max_hp"] = 500
    await ir_para(r, "monster", tr["id"]); r._errs.clear()
    await r.handle_mestre_usar_habilidade(MASTER, tr["id"], "pressao_constante_troll", gob["id"])
    check("sem erro de alcance contra o goblin adjacente", not r._errs)
    check("goblin ficou sob pressão", gob.get("troll_pressao_ca_ate", 0) >= r.round_num)
    # A penalidade precisa valer quando OUTRO monstro ataca o goblin pressionado.
    cas = []
    _orig_d20 = S.d20_attack
    def _espiao(atk, ac, *a, **k):
        cas.append(ac); return _orig_d20(atk, ac, *a, **k)
    S.d20_attack = _espiao
    try:
        await r._execute_one_monster_attack(tr, dict(tr["attacks"][0]), {"kind": "monster", "obj": gob})
    finally:
        S.d20_attack = _orig_d20
    ca_base = gob.get("ac", 10) + r._cancao_monstro_bonus(gob, "ca")
    check("a CA do goblin pressionado caiu 2 no ataque de monstro", cas and cas[-1] == ca_base - 2)

    print("\n[19d] Arremesso do Goblin no Manual aceita criatura a até 3 casas")
    r = sala([{"type": "goblin_combatente", "pos": [6, 6]}, {"type": "troll", "pos": [8, 6]}])
    h = await heroi(r, "warrior", 11, 11); h["hp"] = h["max_hp"] = 500
    await iniciar(r); gob = monstro(r, "goblin_combatente"); tr = monstro(r, "troll")
    tr["hp"] = tr["max_hp"] = 500
    await ir_para(r, "monster", gob["id"]); r._errs.clear()
    import random as _rnd
    _orig_randint = _rnd.randint
    _rnd.randint = lambda a, b: 20 if (a, b) == (1, 20) else _orig_randint(a, b)
    try:
        await r.handle_mestre_usar_habilidade(MASTER, gob["id"], "arremesso", tr["id"])
    finally:
        _rnd.randint = _orig_randint
    check("sem erro de alcance contra o troll a 2 casas", not r._errs)
    check("o troll sofreu o dano da adaga", tr["hp"] < 500)

    print(f"\n{PASS} passaram, {FAIL} falharam")
    if FAIL: sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
