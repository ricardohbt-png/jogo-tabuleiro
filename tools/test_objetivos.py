"""Testes da Fase 3: objetivos, prisioneiro e saída (só masmorra autorada).
Roda da raiz: python tools/test_objetivos.py"""
import asyncio, sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def fixture():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_fase3.json"), encoding="utf-8") as f:
        return json.load(f)

def setup_authored(defn=None):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.mode = "authored"; r.dungeon_def = defn or fixture()
    r.phase = "city"
    return r

async def test_instanciar():
    print("\n[1] carregador instancia exit/prisoner/objectives")
    r = setup_authored()
    await r.enter_dungeon("p1")
    check("exit_pos do arquivo", r.exit_pos == [14, 4])
    check("objectives carregados", r.objectives and r.objectives["primary"]["type"] == "rescue_prisoner")
    check("prisioneiro instanciado (cativo, vivo)",
          r.prisoner and r.prisoner["pos"] == [14, 1]
          and r.prisoner["freed"] is False and r.prisoner["alive"] is True)
    check("prisioneiro com 7 HP", r.prisoner["hp"] == 7 and r.prisoner["max_hp"] == 7)
    check("prisioneiro com CA 10", r.prisoner["ac"] == 10)
    check("prisioneiro com movimento 6", r.prisoner["move"] == 6)
    check("prisioneiro com campo image", "image" in r.prisoner)
    check("prisioneiro com rescuer_pid None", r.prisoner["rescuer_pid"] is None)
    check("bau-chave marcado",
          any(c.get("key_objective") for c in r.chests.values()))
    check("rescue_failed comeca False", r.rescue_failed is False)

async def test_conclusao_simples():
    print("\n[2] cumprir o principal NAO encerra: liga mission_complete_pending")

    async def cenario(primary_type, prep):
        r = setup_authored()
        d = r.dungeon_def
        d["objectives"] = {"primary": {"type": primary_type}, "secondary": []}
        await r.enter_dungeon("p1")
        vit = {"chamado": False, "victory": None}
        async def fake_end(victory, story=None): vit["chamado"] = True; vit["victory"] = victory
        r.end_game = fake_end
        await prep(r)
        await r._check_objectives()
        return r, vit

    async def mata_todos(r):
        for m in r.monsters.values(): m["hp"] = 0
    r, vit = await cenario("kill_all", mata_todos)
    check("kill_all -> missao pode ser encerrada", r.mission_complete_pending is True)
    check("kill_all NAO encerra automaticamente", vit["chamado"] is False)

    r2 = setup_authored(); r2.dungeon_def["objectives"] = {"primary": {"type": "kill_all"}, "secondary": []}
    await r2.enter_dungeon("p1")
    await r2._check_objectives()
    check("kill_all com monstros vivos nao libera encerramento", r2.mission_complete_pending is False)

    async def mata_alvo(r):
        for m in r.monsters.values():
            if m.get("authored_target"): m["hp"] = 0
    r, vit = await cenario("kill_target", mata_alvo)
    check("kill_target -> missao pode ser encerrada", r.mission_complete_pending is True)

    async def poe_na_saida(r):
        list(r.players.values())[0]["pos"] = list(r.exit_pos)
    r, vit = await cenario("reach_exit", poe_na_saida)
    check("reach_exit -> missao pode ser encerrada", r.mission_complete_pending is True)

    async def abre_chave(r):
        r.key_chest_opened = True
    r, vit = await cenario("open_key_chest", abre_chave)
    check("open_key_chest -> missao pode ser encerrada", r.mission_complete_pending is True)

async def test_prisioneiro():
    print("\n[3] prisioneiro: libertar, seguir, escolta, morte")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]
    # herói adjacente ao prisioneiro cativo
    p1["pos"] = [r.prisoner["pos"][0] - 1, r.prisoner["pos"][1]]
    p1["action_done"] = False
    r.turn_index = r.player_order.index("p1")
    await r.handle_libertar_prisioneiro("p1")
    check("prisioneiro libertado por herói adjacente", r.prisoner["freed"] is True)
    check("libertar registra o resgatador", r.prisoner["rescuer_pid"] == "p1")
    check("libertar gastou a ação", p1["action_done"] is True)

    # escolta: prisioneiro junto da saída → rescue cumprido
    r.prisoner["pos"] = [r.exit_pos[0], r.exit_pos[1]]
    check("rescue cumprido perto da saída",
          r._objetivo_cumprido(r.objectives["primary"]) is True)

    # morte do prisioneiro → falha, sem encerrar. Força o ataque a ACERTAR (d20=20).
    r2 = setup_authored()
    r2.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r2.enter_dungeon("p1")
    r2.prisoner["freed"] = True; r2.prisoner["hp"] = 1
    vit = {"c": False}
    async def fe(victory, story=None): vit["c"] = True
    r2.end_game = fe
    orig_attack = server.d20_attack
    server.d20_attack = lambda atk, ac: (True, 20, 20 + atk, True)   # sempre acerta
    try:
        m = next(iter(r2.monsters.values()))
        m["hp"] = 10; m["pos"] = [r2.prisoner["pos"][0] + 1, r2.prisoner["pos"][1]]   # adjacente
        await r2._processar_prisioneiro_turno()
    finally:
        server.d20_attack = orig_attack
    check("prisioneiro morto marca rescue_failed", r2.rescue_failed is True)
    check("morte do prisioneiro NÃO encerra a partida", vit["c"] is False)
    check("status do resgate = failed",
          r2._objetivo_status(r2.objectives["primary"]) == "failed")

    # CA 10 protege: ataque que ERRA (d20=1) não tira HP.
    r3 = setup_authored()
    r3.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r3.enter_dungeon("p1")
    r3.prisoner["freed"] = True; r3.prisoner["hp"] = 5
    server.d20_attack = lambda atk, ac: (False, 1, 1 + atk, False)   # sempre erra
    try:
        m3 = next(iter(r3.monsters.values()))
        m3["hp"] = 10; m3["pos"] = [r3.prisoner["pos"][0] + 1, r3.prisoner["pos"][1]]
        await r3._processar_prisioneiro_turno()
    finally:
        server.d20_attack = orig_attack
    check("CA 10 protege: erro não tira HP", r3.prisoner["hp"] == 5)

async def test_bonus_secundario():
    print("\n[4] secundario cumprido concede bonus ao cumprir o principal (ainda sem encerrar)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "kill_all"},
                                   "secondary": [{"type": "open_key_chest"}]}
    await r.enter_dungeon("p1")
    vit = {"c": False}
    async def fe(victory=True, story=None): vit["c"] = True
    r.end_game = fe
    p1 = r.players["p1"]
    xp0, ouro0 = p1["xp"], p1["gold"]
    for m in r.monsters.values(): m["hp"] = 0
    r.key_chest_opened = True
    await r._check_objectives()
    check("XP do grupo subiu pelo secundario", p1["xp"] > xp0)
    check("ouro do grupo subiu pelo secundario", p1["gold"] > ouro0)
    check("nao encerrou automaticamente", vit["c"] is False)
    check("mission_complete_pending ligado", r.mission_complete_pending is True)

async def test_serializacao():
    print("\n[5] push_state expõe objectives/exit_pos/prisoner")
    r = setup_authored()
    capturado = {}
    async def cap(msg):
        if msg.get("type") == "game_state": capturado.update(msg)
    r.broadcast = cap
    await r.enter_dungeon("p1")
    await GameRoom.push_state(r)   # usa o push_state real (não o stub do setup)
    check("game_state traz exit_pos", capturado.get("exit_pos") == [14, 4])
    check("game_state traz prisoner", capturado.get("prisoner") is not None)
    check("game_state traz objectives", capturado.get("objectives") is not None)

async def test_upload_prisioneiro():
    print("\n[7] upload de imagem do prisioneiro grava em assets/pawns/prisioneiros/")
    import base64 as _b64
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # PNG 1x1 transparente válido.
    png = _b64.b64encode(_b64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")).decode()
    ok, name = server._save_prisoner_upload("captiva.png", png)
    check("upload ok devolve nome", ok and name == "captiva.png")
    dest = os.path.join(base, "assets", "pawns", "prisioneiros", "captiva.png")
    check("arquivo gravado em assets/pawns/prisioneiros/", os.path.exists(dest))
    if os.path.exists(dest): os.remove(dest)
    okx, _ = server._save_prisoner_upload("ruim.txt", png)
    check("rejeita extensão não-imagem", okx is False)


async def test_prisioneiro_controle():
    print("\n[6] prisioneiro liberto é controlado manualmente (janela pós-turno)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    # Tira os monstros do caminho para isolar o movimento.
    for m in r.monsters.values(): m["hp"] = 0
    pr = r.prisoner
    pr["freed"] = True; pr["alive"] = True; pr["rescuer_pid"] = "p1"
    for x in range(2, 11):
        r.tiles[8][x] = server.FLOOR
    pr["pos"] = [5, 8]
    r.players["p1"]["pos"] = [2, 8]; r.players["p1"]["alive"] = True
    r.players["p2"]["pos"] = [9, 8]; r.players["p2"]["alive"] = True

    # 1) encerrar o turno do resgatador ABRE a janela de controle e dá 6 de movimento
    r.turn_index = r.player_order.index("p1")
    await r.handle_end_turn("p1")
    check("janela de controle abre p/ o resgatador", r.animados_phase_pid == "p1")
    check("prisioneiro recebe 6 de movimento", r.prisoner["moves_left"] == 6)

    # 2) handle_mover_prisioneiro move 1 casa e gasta 1 de movimento
    antes = list(pr["pos"])
    await r.handle_mover_prisioneiro("p1", 1, 0)
    check("prisioneiro andou 1 casa", pr["pos"] == [antes[0] + 1, antes[1]])
    check("gastou 1 de movimento", pr["moves_left"] == 5)

    # 3) quem não é o controlador não move o prisioneiro
    fixo = list(pr["pos"])
    await r.handle_mover_prisioneiro("p2", 1, 0)
    check("não-controlador não move o prisioneiro", pr["pos"] == fixo)

    # 4) resgatador morto → controle transfere ao herói vivo mais próximo
    r.animados_phase_pid = None
    r.players["p1"]["alive"] = False
    r.turn_index = r.player_order.index("p2")
    await r.handle_end_turn("p2")
    check("controle transfere ao herói vivo mais próximo",
          r.prisoner["rescuer_pid"] == "p2" and r.animados_phase_pid == "p2"
          and r.prisoner["moves_left"] == 6)


async def test_prisioneiro_armadilha():
    print("\n[9] prisioneiro sofre armadilhas (save +0 em reflexos/fortitude)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    for m in r.monsters.values(): m["hp"] = 0
    pr = r.prisoner
    pr["freed"] = True; pr["alive"] = True; pr["rescuer_pid"] = "p1"; pr["moves_left"] = 6

    # +0 de bônus nos saves de reflexos e fortitude
    _, _, sb_ref, _ = r._testar_save(pr, "reflexos", 99)
    _, _, sb_fort, _ = r._testar_save(pr, "fortitude", 99)
    check("save de reflexos com +0", sb_ref == 0)
    check("save de fortitude com +0", sb_fort == 0)

    # pisa numa armadilha (fosso com estacas) → falha o save → toma dano
    for x in range(2, 7): r.tiles[8][x] = server.FLOOR
    pr["pos"] = [2, 8]
    r.players["p1"]["pos"] = [2, 8]; r.players["p1"]["alive"] = True
    r.armadilhas.append({"id": "tr1", "tipo": "fosso_estacas", "pos": [3, 8],
                         "criador": None, "visivel": True})
    r.animados_phase_pid = "p1"
    r.turn_index = r.player_order.index("p1")
    orig = r._testar_save
    r._testar_save = lambda alvo, s, d, extra_mod=0: (False, 1, 0, 1)   # sempre falha
    try:
        hp0 = pr["hp"]
        await r.handle_mover_prisioneiro("p1", 1, 0)   # [2,8] → [3,8] (a armadilha)
        check("prisioneiro pisou na armadilha", pr["pos"] == [3, 8])
        check("sofreu dano da armadilha", pr["hp"] < hp0)

        # morte por armadilha → rescue_failed
        pr["hp"] = 1; pr["alive"] = True; pr["moves_left"] = 6; pr["pos"] = [4, 8]
        r.armadilhas.append({"id": "tr2", "tipo": "fosso_estacas", "pos": [5, 8],
                             "criador": None, "visivel": True})
        await r.handle_mover_prisioneiro("p1", 1, 0)   # [4,8] → [5,8]
    finally:
        r._testar_save = orig
    check("morte por armadilha marca rescue_failed",
          (pr["alive"] is False) and (r.rescue_failed is True))


async def test_prisioneiro_armadilha_progressiva():
    print("\n[10] prisioneiro sofre dano progressivo de armadilha (incendiária)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    for m in r.monsters.values(): m["hp"] = 0
    pr = r.prisoner
    pr["freed"] = True; pr["alive"] = True; pr["rescuer_pid"] = "p1"; pr["moves_left"] = 6
    pr["hp"] = 30; pr["max_hp"] = 30
    for x in range(2, 5): r.tiles[8][x] = server.FLOOR
    pr["pos"] = [2, 8]; r.players["p1"]["pos"] = [2, 8]; r.players["p1"]["alive"] = True
    r.armadilhas.append({"id": "inc1", "tipo": "armadilha_incendiaria", "pos": [3, 8], "criador": None})
    r.animados_phase_pid = "p1"; r.turn_index = r.player_order.index("p1")
    orig = r._testar_save
    r._testar_save = lambda alvo, s, d, extra_mod=0: (False, 1, 0, 1)   # falha o save
    try:
        await r.handle_mover_prisioneiro("p1", 1, 0)   # pisa na incendiária
    finally:
        r._testar_save = orig
    hp_imediato = pr["hp"]
    check("dano imediato da incendiária", hp_imediato < 30)
    check("dano progressivo agendado p/ o prisioneiro",
          any(e.get("alvo_id") == "__prisioneiro__"
              for a in r.armadilhas for e in a.get("efeitos_ativos", [])))
    await r._processar_efeitos_armadilha_turno()   # tica a(s) rodada(s) seguinte(s)
    check("dano progressivo atinge o prisioneiro", pr["hp"] < hp_imediato)


async def test_reward_dividido():
    print("\n[11] recompensa de objetivo: XP e ouro divididos entre os vivos + itens acumulados")
    r = setup_authored()
    # xp=40 -> 20 por heroi (abaixo do limiar de level-up, p/ asserir XP exato);
    # gold=80 -> 40 por heroi.
    r.dungeon_def["objectives"] = {
        "primary": {"type": "kill_all",
                    "xp": 40, "reward": {"gold": 80, "items": [{"id": "magic_sword"}]}},
        "secondary": []}
    await r.enter_dungeon("p1")
    p1, p2 = r.players["p1"], r.players["p2"]
    xp1, xp2, ouro1 = p1["xp"], p2["xp"], p1["gold"]
    loot = []
    obj = r.objectives["primary"]
    await r._conceder_objetivo_reward(obj, is_primary=True, loot_acc=loot)
    # 2 herois vivos: 40 XP -> 20 cada; 80 ouro -> 40 cada
    check("XP dividido entre os vivos (20)", p1["xp"] == xp1 + 20 and p2["xp"] == xp2 + 20)
    check("ouro dividido entre os vivos (40)", p1["gold"] == ouro1 + 40)
    check("item de recompensa acumulado", any(i.get("id") == "magic_sword" for i in loot))


async def test_reward_default_secundario():
    print("\n[12] secundario sem xp/reward usa o padrao (50/25)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "kill_all"},
                                   "secondary": [{"type": "open_key_chest"}]}
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]; xp0, ouro0 = p1["xp"], p1["gold"]
    loot = []
    await r._conceder_objetivo_reward(r.objectives["secondary"][0], is_primary=False, loot_acc=loot)
    check("XP padrao do secundario (max(1,50//2)=25)", p1["xp"] == xp0 + 25)
    check("ouro padrao do secundario (25//2=12)", p1["gold"] == ouro0 + 12)


async def test_encerrar_missao():
    print("\n[13] encerrar_missao faz a transicao e larga bau de recompensa")
    r = setup_authored()
    r.dungeon_def["objectives"] = {
        "primary": {"type": "kill_all", "xp": 60, "reward": {"items": [{"id": "magic_sword"}]}},
        "secondary": []}
    await r.enter_dungeon("p1")
    vit = {"c": False, "v": None}
    async def fe(victory, story=None): vit["c"] = True; vit["v"] = victory
    r.end_game = fe
    chests0 = set(r.chests.keys())
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    novos = [cid for cid in r.chests if cid not in chests0]
    check("bau de recompensa largado", len(novos) == 1)
    # Assere o conteúdo SÓ do baú recém-criado (não dos pré-existentes da fixture).
    check("bau contem o item de recompensa",
          bool(novos) and any(i.get("id") == "magic_sword" for i in r.chests[novos[0]]["items"]))
    check("ainda nao encerrou (espera o botao)", vit["c"] is False)
    await r.handle_encerrar_missao("p1")
    check("encerrar_missao chama end_game(victory)", vit["c"] is True and vit["v"] is True)


async def main():
    await test_instanciar()
    await test_conclusao_simples()
    await test_prisioneiro()
    await test_bonus_secundario()
    await test_serializacao()
    await test_prisioneiro_controle()
    await test_upload_prisioneiro()
    await test_prisioneiro_armadilha()
    await test_prisioneiro_armadilha_progressiva()
    await test_reward_dividido()
    await test_reward_default_secundario()
    await test_encerrar_missao()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
