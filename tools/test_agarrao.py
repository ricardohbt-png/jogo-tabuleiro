"""Agarrão de criatura (Crocodilo/Cobra Constritora) nos DOIS caminhos de ataque:
IA (gm_phase) e controle Manual do Mestre. Roda da raiz: python tools/test_agarrao.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, make_monster

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala(com_mestre=False):
    r = GameRoom("TEST")
    r._falas = []
    async def noop(*a, **k): pass
    async def say(msg, *a, **k): r._falas.append(msg)
    r._errs = []
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r._errs.append(msg.get("msg", ""))
    r.gm_say = say; r.broadcast = noop; r.push_state = noop
    r.broadcast_lobby = noop; r.broadcast_city_state = noop; r.send_to = cap_send
    r.phase = "playing"
    r.map_w = 14; r.map_h = 14
    r.tiles = [[S.FLOOR]*14 for _ in range(14)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 14, "h": 14, "cx": 7, "cy": 7, "locked": False}]
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    if com_mestre:
        r.master_pid = "m1"; r.master_name = "Mestre"
        r.connections["m1"] = object()
    return r

def bicho(r, tipo, pos, mid="b1"):
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == tipo)
    m = make_monster(mdef, r.rooms[0])
    m["id"] = mid; m["pos"] = list(pos); m["room_id"] = "r0"; m["alertado"] = True
    r.monsters[mid] = m
    return m

def heroi(r, pos, *, acerta=True, falha_save=True, pid="h1"):
    p = make_player(pid, "Victor", "warrior", 0)
    p["pos"] = list(pos); p["alive"] = True; p["connected"] = True
    p["hp"] = 500; p["max_hp"] = 500
    p["ac"] = 1 if acerta else 99
    p["ac_base"] = p["ac"]
    p["fort"] = -50 if falha_save else 50
    p["ref_"] = -50 if falha_save else 50
    r.players[pid] = p
    r.connections[pid] = object()
    return p

def abrir_janela_manual(r, m):
    """Mesmo preparo da janela do Mestre, sem o Event/timer da iniciativa."""
    r.master_manual_mid = m["id"]
    r._preparar_janela_controle_monstro(m)
    m["master_moves_left"] = int(m.get("movement", 6) or 6)
    m["control_mode"] = "manual"

def conta_saves(r):
    """Envolve _testar_save para contar quantas vezes é rolado."""
    orig = r._testar_save
    box = {"n": 0}
    def wrapper(*a, **k):
        box["n"] += 1
        return orig(*a, **k)
    r._testar_save = wrapper
    return box

async def main():
    print("\n[1] IA (sem mestre): mordida que acerta agarra o herói")
    r = sala()
    m = bicho(r, "crocodilo_jovem", [7, 5]); p = heroi(r, [5, 5])
    saves = conta_saves(r)
    await r.gm_phase(m)
    check("herói preso", p.get("preso") is True)
    check("preso_por é o crocodilo", p.get("preso_por") == "b1")
    check("save rolado uma única vez (sem duplicar)", saves["n"] == 1)

    print("\n[2] IA (sem mestre): save bem-sucedido não prende")
    r = sala()
    m = bicho(r, "crocodilo_jovem", [7, 5]); p = heroi(r, [5, 5], falha_save=False)
    await r.gm_phase(m)
    check("herói livre", not p.get("preso"))
    check("narrou a resistência", any("resist" in f.lower() for f in r._falas))

    print("\n[3] Mestre em Manual: mordida que acerta agarra o herói")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5])
    abrir_janela_manual(r, m)
    await r.handle_mestre_atacar_monstro("m1", "b1", "h1", 0)
    check("herói preso pelo croc do mestre", p.get("preso") is True)
    check("preso_por é o crocodilo", p.get("preso_por") == "b1")

    print("\n[4] Mestre em Manual: Cobra Constritora também constringe")
    r = sala(com_mestre=True)
    m = bicho(r, "cobra_constritora", [6, 5]); p = heroi(r, [5, 5])
    abrir_janela_manual(r, m)
    await r.handle_mestre_atacar_monstro("m1", "b1", "h1", 0)
    check("herói enrolado pela cobra", p.get("preso") is True)

    print("\n[5] Mestre em Manual: erro no ataque não agarra")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5], acerta=False)
    abrir_janela_manual(r, m)
    saves = conta_saves(r)
    await r.handle_mestre_atacar_monstro("m1", "b1", "h1", 0)
    check("herói livre após erro", not p.get("preso"))
    check("nenhum save rolado", saves["n"] == 0)

    print("\n[6] Alvo já preso não rola o save de novo")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5])
    p["preso"] = True; p["preso_por"] = "b1"
    abrir_janela_manual(r, m)
    saves = conta_saves(r)
    await r.handle_mestre_atacar_monstro("m1", "b1", "h1", 0)
    check("nenhum save extra", saves["n"] == 0)

    print("\n[7] Ataque de Mandíbula é ativável pelo mestre e fere o preso")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5])
    p["preso"] = True; p["preso_por"] = "b1"
    ab = r._habilidade_monstro(m, "atq_mandibula")
    check("marcada como ativável na ficha", r._habilidade_ativavel_manual(ab) is True)
    abrir_janela_manual(r, m)
    hp0 = p["hp"]
    await r.handle_mestre_usar_habilidade("m1", "b1", "atq_mandibula", "h1")
    check("preso levou dano automático", p["hp"] < hp0)
    check("consumiu a ação principal", m.get("_master_acted") is True)

    print("\n[7b] Mandíbula sem preso adjacente é recusada")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5])
    abrir_janela_manual(r, m)
    hp0 = p["hp"]
    await r.handle_mestre_usar_habilidade("m1", "b1", "atq_mandibula", "h1")
    check("sem dano", p["hp"] == hp0)
    check("erro explicado ao mestre", any("agarrad" in e.lower() for e in r._errs))
    check("ação principal preservada", not m.get("_master_acted"))

    print("\n[7c] Esmagar da cobra também é ativável")
    r = sala(com_mestre=True)
    m = bicho(r, "cobra_constritora", [6, 5]); p = heroi(r, [5, 5])
    p["preso"] = True; p["preso_por"] = "b1"
    abrir_janela_manual(r, m)
    hp0 = p["hp"]
    await r.handle_mestre_usar_habilidade("m1", "b1", "esmagar", "h1")
    check("preso levou dano da constrição", p["hp"] < hp0)

    print("\n[8] Arrastar: o preso acompanha o monstro que o mestre move")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5])
    p["preso"] = True; p["preso_por"] = "b1"
    abrir_janela_manual(r, m)
    await r.handle_mestre_mover_monstro_para("m1", "b1", 10, 5)
    check("croc andou", m["pos"] != [6, 5])
    check("preso foi arrastado junto", p["pos"] != [5, 5])
    check("preso continua adjacente ao croc", r._is_adjacent_to_monster(p["pos"], m))
    check("preso não ficou por cima do croc",
          [p["pos"][0], p["pos"][1]] not in [list(t) for t in r._monster_tiles(m)])

    print("\n[8b] Arrastar só vale para quem tem a habilidade")
    r = sala(com_mestre=True)
    m = bicho(r, "cobra_constritora", [6, 5]); p = heroi(r, [5, 5])
    p["preso"] = True; p["preso_por"] = "b1"
    abrir_janela_manual(r, m)
    await r.handle_mestre_mover_monstro_para("m1", "b1", 10, 5)
    check("preso ficou para trás (cobra não arrasta)", p["pos"] == [5, 5])

    print("\n[9] Regressão: Onda Envolvente segue prendendo sem save")
    r = sala(com_mestre=True)
    m = bicho(r, "elemental_agua", [6, 5]) if any(
        d.get("type") == "elemental_agua" for d in S.MONSTER_DEFS) else None
    if m:
        p = heroi(r, [5, 5], falha_save=False)   # mesmo passando no save, prende
        abrir_janela_manual(r, m)
        await r.handle_mestre_atacar_monstro("m1", "b1", "h1", 0)
        check("onda envolvente prende sem teste", p.get("preso") is True)
    else:
        check("elemental_agua existe no bestiário", False)

    print("\n[10] Regressão: escape no início do turno continua funcionando")
    r = sala()
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5], falha_save=False)
    p["preso"] = True; p["preso_por"] = "b1"
    await r._processar_escape_agarrar(p)
    check("herói se soltou", not p.get("preso"))

    # ── Agarrão contra MONSTRO ────────────────────────────────────────────────
    # É o caso da mesa livre do editor ("🧪 Testar como Mestre"), que não tem
    # heróis: lá o único alvo possível é outra criatura.
    def alvo_monstro(r, pos, *, falha_save=True, mid="alvo1"):
        o = bicho(r, "escorpiao_pedra", pos, mid=mid)
        o["hp"] = 500; o["max_hp"] = 500
        o["ac"] = 1
        o["fort"] = -50 if falha_save else 50
        o["ref_"] = -50 if falha_save else 50
        return o

    print("\n[11] Mesa livre: croc morde outro monstro e o agarra")
    r = sala(com_mestre=True)
    r.test_mode = True          # mesa livre do editor: alvo-monstro é legítimo
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    abrir_janela_manual(r, m)
    await r.handle_mestre_atacar_monstro("m1", "b1", "alvo1", 0)
    check("monstro preso", alvo.get("preso") is True)
    check("preso_por é o crocodilo", alvo.get("preso_por") == "b1")

    print("\n[11b] Monstro que passa no save não é agarrado")
    r = sala(com_mestre=True)
    r.test_mode = True
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5], falha_save=False)
    abrir_janela_manual(r, m)
    await r.handle_mestre_atacar_monstro("m1", "b1", "alvo1", 0)
    check("monstro livre", not alvo.get("preso"))

    print("\n[12] Monstro agarrado não se move")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    abrir_janela_manual(r, alvo)
    await r.handle_mestre_mover_monstro_para("m1", "alvo1", 1, 5)
    check("ficou parado", alvo["pos"] == [5, 5])
    check("mestre avisado", any("agarrad" in e.lower() or "preso" in e.lower() for e in r._errs))

    print("\n[13] Escape do monstro no prólogo do turno")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5], falha_save=False)
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    pode = await r._upkeep_inicio_turno_monstro(alvo, [alvo])
    check("se soltou com save alto", not alvo.get("preso"))
    check("segue podendo agir", pode is True)

    print("\n[13b] Falha no escape mantém preso e zera o movimento")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    alvo["master_moves_left"] = 6; alvo["_water_moves_left"] = 6
    await r._upkeep_inicio_turno_monstro(alvo, [alvo])
    check("continua preso", alvo.get("preso") is True)
    check("movimento zerado", alvo.get("master_moves_left") == 0 and alvo.get("_water_moves_left") == 0)

    print("\n[14] Mandíbula do mestre atinge o monstro agarrado")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    abrir_janela_manual(r, m)
    hp0 = alvo["hp"]
    await r.handle_mestre_usar_habilidade("m1", "b1", "atq_mandibula", None)
    check("monstro preso levou dano", alvo["hp"] < hp0)

    print("\n[15] Morte do captor solta o monstro agarrado")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    m["hp"] = 0
    await r._monster_dies(m, None)
    check("solto ao morrer o predador", not alvo.get("preso"))

    print("\n[16] Arrastar leva o monstro agarrado junto")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    abrir_janela_manual(r, m)
    await r.handle_mestre_mover_monstro_para("m1", "b1", 10, 5)
    check("croc andou", m["pos"] != [6, 5])
    check("monstro preso foi junto", alvo["pos"] != [5, 5])
    check("continua adjacente", r._is_adjacent_to_monster(alvo["pos"], m))

    # ── Escape: uma tentativa NOVA a cada turno do agarrado ───────────────────
    def conta_escapes(r):
        orig = r._processar_escape_agarrar
        box = {"n": 0}
        async def wrapper(alvo):
            box["n"] += 1
            return await orig(alvo)
        r._processar_escape_agarrar = wrapper
        return box

    print("\n[17] Herói agarrado tenta escapar em TODO turno dele")
    r = sala()
    m = bicho(r, "crocodilo_jovem", [6, 5]); p = heroi(r, [5, 5], falha_save=True)
    p["preso"] = True; p["preso_por"] = "b1"
    esc = conta_escapes(r)
    for rodada in (1, 2, 3):
        r.round_num = rodada
        await r._start_initiative_player_turn(p)
        check(f"rodada {rodada}: tentou escapar", esc["n"] == rodada)
        check(f"rodada {rodada}: falhou e segue preso", p.get("preso") is True)
        check(f"rodada {rodada}: sem movimento enquanto preso", p["moves_left"] == 0)
    p["fort"] = 50; p["ref_"] = 50           # agora o save passa
    await r._start_initiative_player_turn(p)
    check("4ª tentativa liberta", not p.get("preso"))
    check("movimento volta ao normal", p["moves_left"] > 0)

    print("\n[17b] Croc dá DOIS saves de escape (FOR ou REF); cobra dá um")
    r = sala()
    bicho(r, "crocodilo_jovem", [6, 5], mid="croc")
    bicho(r, "cobra_constritora", [9, 9], mid="cobra")
    p = heroi(r, [5, 5], falha_save=True)
    saves = conta_saves(r)
    p["preso"] = True; p["preso_por"] = "croc"
    await r._processar_escape_agarrar(p)
    n_croc = saves["n"]
    p["preso"] = True; p["preso_por"] = "cobra"
    await r._processar_escape_agarrar(p)
    check("crocodilo: 2 saves (FOR e REF)", n_croc == 2)
    check("cobra: 1 save (escape_saves da ficha)", saves["n"] - n_croc == 1)

    print("\n[18] Monstro agarrado tenta escapar em TODO turno dele")
    r = sala(com_mestre=True)
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    esc = conta_escapes(r)
    for rodada in (1, 2, 3):
        r.round_num = rodada
        alvo["master_moves_left"] = 6; alvo["_water_moves_left"] = 6
        pode = await r._upkeep_inicio_turno_monstro(alvo, [alvo])
        check(f"rodada {rodada}: tentou escapar", esc["n"] == rodada)
        check(f"rodada {rodada}: preso e sem movimento", alvo.get("preso") is True
              and alvo["master_moves_left"] == 0)
        check(f"rodada {rodada}: ainda pode agir (atacar)", pode is True)
    alvo["fort"] = 50; alvo["ref_"] = 50
    await r._upkeep_inicio_turno_monstro(alvo, [alvo])
    check("4ª tentativa liberta o monstro", not alvo.get("preso"))

    print("\n[18b] Escape do monstro vale também sob a IA (gm_phase)")
    r = sala()
    m = bicho(r, "crocodilo_jovem", [6, 5]); alvo = alvo_monstro(r, [5, 5])
    p = heroi(r, [12, 12])          # gm_phase exige ao menos um herói ativo
    alvo["preso"] = True; alvo["preso_por"] = "b1"
    esc = conta_escapes(r)
    await r.gm_phase(alvo)
    check("IA também rolou o escape", esc["n"] == 1)

    print(f"\n{'='*46}\n  {PASS} passaram · {FAIL} falharam\n{'='*46}")
    return 1 if FAIL else 0

sys.exit(asyncio.run(main()))
