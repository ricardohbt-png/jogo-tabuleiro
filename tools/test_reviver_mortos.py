"""Reviver os Mortos — tabela de Slots/Chance por Nível I/II/III (Guilda do Mago).
Roda da raiz: python tools/test_reviver_mortos.py"""
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
    r._is_turn = lambda pid: True
    r.phase = phase; r._errs = errs
    return r

def mage(**owned):
    p = make_player("m", "Pedro", "mage", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]; p["alive"] = True
    p["level"] = owned.get("level", 1)
    p["int_"] = owned.get("int_", 18)  # mod(18) = +4
    return p

def corpse(cr, pos=(1, 0)):
    return {"id": "c1", "nome": "Zumbi", "icone": "💀", "tipo": "zombie",
            "tier": 1, "nivel": max(1, round(cr)), "nd": cr,
            "ca": 10, "vida_max": 10, "dano": "1d4", "movimento": 3,
            "pos": list(pos), "room_id": None}

async def main():
    # [1] Catálogo do Mago
    print("\n[1] Catálogo — Reviver os Mortos")
    ids = [i["id"] for i in S.guild_items_for_class("mage")]
    check("catálogo tem mago_reviver_2", "mago_reviver_2" in ids)
    check("catálogo tem mago_reviver_3", "mago_reviver_3" in ids)
    check("reviver_2 = 200", S.guild_item("mago_reviver_2")["preco"] == 200)
    check("reviver_3 = 300", S.guild_item("mago_reviver_3")["preco"] == 300)
    check("reviver_3 requer reviver_2", S.guild_item("mago_reviver_3")["requer"] == "mago_reviver_2")
    check("reviver_2 sem requer", S.guild_item("mago_reviver_2")["requer"] is None)

    # [2] Nível possuído
    print("\n[2] _reviver_nivel")
    r = setup()
    check("base = 1", r._reviver_nivel(mage()) == 1)
    check("reviver_2 = 2", r._reviver_nivel(mage(esp=["mago_reviver_2"])) == 2)
    check("reviver_3 = 3", r._reviver_nivel(mage(esp=["mago_reviver_3"])) == 3)

    # [3] Slots de Controle totais (mod(INT) + nível÷2, mín 1; +2 no III)
    print("\n[3] _reviver_slots_max")
    p = mage(int_=18, level=1)  # mod=4, level//2=0 → 4
    check("nível1 int18 lvl1 = 4", r._reviver_slots_max(p) == 4)
    p3 = mage(esp=["mago_reviver_3"], int_=18, level=1)
    check("nível3 soma +2 = 6", r._reviver_slots_max(p3) == 6)
    p_low = mage(int_=8, level=1)  # mod(8) = -1 → max(1, -1+0) = 1
    check("mín 1 slot mesmo com INT baixo", r._reviver_slots_max(p_low) == 1)

    # [4] Custo de slot por criatura
    print("\n[4] _reviver_slot_custo")
    p1 = mage()
    check("Nível I: sempre 1 slot (ND 3)", r._reviver_slot_custo(p1, 3) == 1)
    check("Nível I: sempre 1 slot (ND 0.25)", r._reviver_slot_custo(p1, 0.25) == 1)
    p2 = mage(esp=["mago_reviver_2"])
    check("Nível II: ocupa ND exato (ND 2)", r._reviver_slot_custo(p2, 2) == 2)
    check("Nível II: ND fracionário (0.5)", r._reviver_slot_custo(p2, 0.5) == 0.5)
    check("Nível II: piso 0.25 (ND 0.25)", r._reviver_slot_custo(p2, 0.25) == 0.25)

    # [5] Chance de sucesso por Nível/ND (todas com Pedro nível 1 → +5%)
    print("\n[5] _reviver_chance")
    check("N.I ND1 = 80%+5% = 85%", r._reviver_chance(mage(), 1) == 85)
    check("N.I ND2 = 60%+5% = 65%", r._reviver_chance(mage(), 2) == 65)
    check("N.I ND5 = 0%+5% = 5%", r._reviver_chance(mage(), 5) == 5)
    p2 = mage(esp=["mago_reviver_2"])
    check("N.II ND1 = 85%+5% = 90%", r._reviver_chance(p2, 1) == 90)
    check("N.II ND3 = 55%+5% = 60%", r._reviver_chance(p2, 3) == 60)
    check("N.II ND0.25 ≈ 96%+5% → clamp 99%", r._reviver_chance(p2, 0.25) == 99)
    p3 = mage(esp=["mago_reviver_3"])
    check("N.III ND1 = 90%+5% = 95%", r._reviver_chance(p3, 1) == 95)
    check("N.III ND5 = 50%+5% = 55%", r._reviver_chance(p3, 5) == 55)

    # [5b] Bônus de nível de Pedro (+5%/nível), independente do Nível da Guilda
    print("\n[5b] _reviver_chance — bônus por nível de Pedro")
    check("nível1: +5%", r._reviver_chance(mage(level=1), 1) == 85)
    check("nível3: +15%", r._reviver_chance(mage(level=3), 1) == 95)
    check("nível5: +25% → clamp 99%", r._reviver_chance(mage(level=5), 1) == 99)
    check("nível5 ND5: 0%+25% = 25%", r._reviver_chance(mage(level=5), 5) == 25)

    # [6] Fluxo completo — sucesso ocupa o slot certo (Nível II)
    print("\n[6] handle_animar_mortos — fim a fim")
    r = setup()
    p = mage(esp=["mago_reviver_2"], int_=18, level=1)
    r.players = {"m": p}
    r.corpses = {"c1": corpse(2.0)}
    r.monsters = {"c1": {"id": "c1", "hp": 0, "max_hp": 10}}
    orig_randint = S.random.randint
    calls = iter([0, 1])  # dezena=0, unidade=1 → d100=1 (sucesso garantido)
    S.random.randint = lambda a, b: next(calls)
    try:
        await r.handle_animar_mortos("m", {"cadaver_id": "c1"})
    finally:
        S.random.randint = orig_randint
    check("nenhum erro de slot", r._errs == [])
    check("cadáver consumido", "c1" not in r.corpses)

    # [7] Slots insuficientes rejeita a ação (Nível I, monstro ND alto mas custo=1 sempre)
    r = setup()
    p = mage(int_=8, level=1)  # slots_max = 1
    p["animados"] = [{"id": "prev", "slots": 1}]  # já ocupado
    r.players = {"m": p}
    r.corpses = {"c1": corpse(1.0)}
    await r.handle_animar_mortos("m", {"cadaver_id": "c1"})
    check("rejeita por slots insuficientes", any("Slots insuficientes" in e for e in r._errs))

    # ── Helpers da fila de servos (Tasks 1–4) ────────────────────────────────
    def servo(sid, dex, pos=(1, 0), **extra):
        a = {"id": sid, "nome": f"Servo {sid}", "tipo": "zombie",
             "pos": list(pos), "vida_atual": 8, "vida_max": 8,
             "movimento": 3, "moves_left": 3, "acted": False,
             "dex": dex, "int_": 10, "ca": 10}
        a.update(extra)
        return a

    def sala_com_servos(*servos):
        """Sala com o mago já DENTRO da janela dos servos."""
        r = setup()
        p = mage()
        p["animados"] = list(servos)
        r.players = {"m": p}
        r.animados_phase_pid = "m"
        for a in servos:
            a["initiative"] = r.initiative_value(a)
        ordenados = sorted(servos, key=lambda a: (-a["initiative"], -a["dex"], a["id"]))
        r.animados_order = [a["id"] for a in ordenados]
        r.animados_done = set()
        r.prisioneiro_done = False
        return r, p

    # [8] O servo da vez é o de maior iniciativa
    print("\n[8] animados_atual — ordem por iniciativa")
    r, p = sala_com_servos(servo("s_lento", 8), servo("s_rapido", 18), servo("s_medio", 12))
    check("fila começa no de maior iniciativa",
          r._animados_atual("m") == "s_rapido")
    check("ordem completa por iniciativa",
          r.animados_order == ["s_rapido", "s_medio", "s_lento"])

    # [9] Servo encerrado sai da vez
    print("\n[9] animados_done tira o servo da vez")
    r.animados_done.add("s_rapido")
    check("passa ao segundo da ordem", r._animados_atual("m") == "s_medio")
    r.animados_done.add("s_medio")
    r.animados_done.add("s_lento")
    check("fila vazia devolve None", r._animados_atual("m") is None)

    # [10] Fila só existe dentro da janela deste jogador
    print("\n[10] animados_atual fora da janela")
    r2, _ = sala_com_servos(servo("s1", 14))
    r2.animados_phase_pid = None
    check("sem janela aberta devolve None", r2._animados_atual("m") is None)
    r2.animados_phase_pid = "outro"
    check("janela de outro jogador devolve None", r2._animados_atual("m") is None)

    # [11] encerrar_animado avança a fila
    print("\n[11] handle_encerrar_animado — avanço")
    r, p = sala_com_servos(servo("s_rapido", 18), servo("s_medio", 12))
    fechou = []
    async def fake_end_turn(pid): fechou.append(pid)
    r.handle_end_turn = fake_end_turn
    await r.handle_encerrar_animado("m", "s_rapido")
    check("primeiro servo marcado como encerrado", "s_rapido" in r.animados_done)
    check("fila passa ao segundo", r._animados_atual("m") == "s_medio")
    check("janela NÃO fechou ainda", fechou == [])
    await r.handle_encerrar_animado("m", "s_medio")
    check("fila vazia delega a handle_end_turn", fechou == ["m"])

    # [12] Recusas
    print("\n[12] handle_encerrar_animado — recusas")
    r, p = sala_com_servos(servo("s1", 14))
    r.handle_end_turn = fake_end_turn
    r.animados_phase_pid = None
    r._errs.clear()
    await r.handle_encerrar_animado("m", "s1")
    check("recusa fora da janela", len(r._errs) == 1)
    check("não marcou nada", r.animados_done == set())

    r, p = sala_com_servos(servo("s1", 14))
    r.handle_end_turn = fake_end_turn
    r._errs.clear()
    await r.handle_encerrar_animado("m", "id_que_nao_existe")
    check("recusa id fora da fila", len(r._errs) == 1)

    r, p = sala_com_servos(servo("s1", 14), servo("s2", 10))
    r.handle_end_turn = fake_end_turn
    r._errs.clear()
    await r.handle_encerrar_animado("m", "s1")
    await r.handle_encerrar_animado("m", "s1")
    check("recusa encerrar o mesmo servo duas vezes", len(r._errs) == 1)
    check("a vez do seguinte foi preservada", r._animados_atual("m") == "s2")

    # [12b] Guarda de fase: _voltar_para_cidade muda phase sem limpar
    # animados_phase_pid, entao um encerrar_animado atrasado nao pode agir.
    print("\n[12b] handle_encerrar_animado — fora da fase de jogo")
    r, p = sala_com_servos(servo("s1", 14), servo("s2", 10))
    r.handle_end_turn = fake_end_turn
    del r._is_turn                       # volta ao _is_turn real da classe
    r.phase = "city"                     # o grupo voltou pra cidade
    avisos = []
    async def cap_aviso(pid): avisos.append(pid)
    r._avisar_controle_de_monstro = cap_aviso
    await r.handle_encerrar_animado("m", "s1")
    check("recusa fora da fase playing", avisos == ["m"])
    check("nao mexeu na fila", r.animados_done == set())

    # [13] end_turn continua fechando tudo de uma vez (rede do timer anti-AFK)
    print("\n[13] end_turn na janela fecha tudo")
    r, p = sala_com_servos(servo("s1", 14), servo("s2", 10))
    avancou = []
    async def fake_advance(): avancou.append(True)
    r._advance_initiative = fake_advance
    r.initiative_active = True
    await r.handle_end_turn("m")
    check("janela fechada", r.animados_phase_pid is None)
    check("fila limpa", r.animados_order == [] and r.animados_done == set())
    check("iniciativa avançou", avancou == [True])

    # [14] Servo travado é pulado com narração
    print("\n[14] saltos de servo travado")
    r, p = sala_com_servos(servo("s_rapido", 18),
                           servo("s_dorme", 14, dormindo=True),
                           servo("s_medio", 12))
    ditos = []
    async def cap_say(msg): ditos.append(msg)
    r.gm_say = cap_say
    async def fake_end_turn_3(pid): pass
    r.handle_end_turn = fake_end_turn_3
    check("dormindo não pode agir", r._animado_pode_agir(p["animados"][1]) is False)
    await r.handle_encerrar_animado("m", "s_rapido")
    check("pulou o adormecido", r._animados_atual("m") == "s_medio")
    check("adormecido marcado como encerrado", "s_dorme" in r.animados_done)
    check("narrou o salto", len(ditos) == 1)

    # [15] Servo que morre no meio da janela sai da fila
    print("\n[15] servo morto sai da fila")
    r, p = sala_com_servos(servo("s_a", 18), servo("s_b", 14), servo("s_c", 10))
    r.gm_say = cap_say
    r.handle_end_turn = fake_end_turn_3
    p["animados"][1]["vida_atual"] = 0     # s_b morreu por lava/retaliação
    await r.handle_encerrar_animado("m", "s_a")
    check("morto é pulado", r._animados_atual("m") == "s_c")

    # [16] Servo dominado por necromante não obedece
    print("\n[16] servo dominado sai da fila")
    r, p = sala_com_servos(servo("s_a", 18), servo("s_b", 14, dominado_por_monstro="mX"))
    r.gm_say = cap_say
    r.handle_end_turn = fake_end_turn_3
    await r.handle_encerrar_animado("m", "s_a")
    check("dominado não entra na vez", r._animados_atual("m") is None)

    # [16b] O consumo roda DEPOIS do upkeep da abertura. O laco de upkeep
    # decrementa dormindo_rodadas e ACORDA o servo; consumir antes dele leria o
    # flag da rodada passada e faria o servo perder a vez sem motivo.
    print("\n[16b] abertura da janela — sono que expira nao perde a vez")
    r = setup()
    pm = mage()
    pm["spd"] = 5
    dorminhoco = servo("s_acorda", 18, dormindo=True, dormindo_rodadas=1)
    acordado   = servo("s_ok", 12)
    pm["animados"] = [dorminhoco, acordado]
    r.players = {"m": pm}
    r.animados_phase_pid = None          # janela AINDA fechada: vamos abri-la
    ditos_ab = []
    async def cap_say_ab(msg): ditos_ab.append(msg)
    r.gm_say = cap_say_ab
    await r.handle_end_turn("m")
    check("a janela abriu", r.animados_phase_pid == "m")
    check("o sono expirou no upkeep", not dorminhoco.get("dormindo"))
    check("quem acordou NAO foi consumido", "s_acorda" not in r.animados_done)
    check("e e ele o servo da vez", r._animados_atual("m") == "s_acorda")

    # [17] Prisioneiro e o ultimo da fila
    print("\n[17] prisioneiro no fim da fila")
    r, p = sala_com_servos(servo("s_a", 18), servo("s_b", 12))
    r.prisoner = {"freed": True, "alive": True, "rescuer_pid": "m",
                  "pos": [2, 2], "moves_left": 6}
    fechou_pr = []
    async def fake_end_turn_pr(pid): fechou_pr.append(pid)
    r.handle_end_turn = fake_end_turn_pr
    await r.handle_encerrar_animado("m", "s_a")
    check("ainda em servo", r._animados_atual("m") == "s_b")
    await r.handle_encerrar_animado("m", "s_b")
    check("servos esgotados -> prisioneiro", r._animados_atual("m") == "prisoner")
    check("janela ainda aberta", fechou_pr == [])
    await r.handle_encerrar_animado("m", "prisoner")
    check("prisioneiro encerrado fecha a janela", fechou_pr == ["m"])

    # [18] Prisioneiro de OUTRO resgatador nao entra na minha fila
    print("\n[18] prisioneiro alheio")
    r, p = sala_com_servos(servo("s_a", 18))
    r.prisoner = {"freed": True, "alive": True, "rescuer_pid": "outro",
                  "pos": [2, 2], "moves_left": 6}
    r.handle_end_turn = fake_end_turn_pr
    r._errs.clear()
    r.animados_done.add("s_a")
    check("nao aparece na minha vez", r._animados_atual("m") is None)
    await r.handle_encerrar_animado("m", "prisoner")
    check("recusa encerrar prisioneiro alheio", len(r._errs) == 1)

    # [19] Prisioneiro morto no meio da janela nao trava o fechamento
    print("\n[19] prisioneiro morto")
    r, p = sala_com_servos(servo("s_a", 18))
    r.prisoner = {"freed": True, "alive": False, "rescuer_pid": "m",
                  "pos": [2, 2], "moves_left": 6}
    fechou2 = []
    async def fake_end_turn2(pid): fechou2.append(pid)
    r.handle_end_turn = fake_end_turn2
    await r.handle_encerrar_animado("m", "s_a")
    check("prisioneiro morto nao segura a janela", fechou2 == ["m"])

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
