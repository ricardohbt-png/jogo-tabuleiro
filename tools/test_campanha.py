"""Testes da Fase 4a: runtime de campanha.
Roda da raiz: python tools/test_campanha.py"""
import asyncio, sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, carregar_campanha, validar_campanha, listar_campanhas

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup_room():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop; r.broadcast_lobby = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys()); r.host_pid = "p1"
    return r

def test_validacao():
    print("\n[1] validar/listar campanha")
    defn = carregar_campanha("test_campanha.json")
    check("carrega o arquivo", defn is not None)
    ok, msg = validar_campanha(defn)
    check(f"campanha válida ({msg})", ok is True)
    check("aparece em listar_campanhas",
          any(c["file"] == "test_campanha.json" for c in listar_campanhas()))
    check("lista vazia recusa", validar_campanha({"schema_version": 1, "dungeons": []})[0] is False)
    check("fase inexistente recusa",
          validar_campanha({"schema_version": 1, "dungeons": ["nao_existe.json"]})[0] is False)
    check("path traversal recusado", carregar_campanha("../server.py") is None)

async def test_selecao():
    print("\n[2] seleção de campanha no lobby")
    r = setup_room(); r.phase = "lobby"
    check("defaults: campaign None, phase 0",
          getattr(r, "campaign", "x") is None and getattr(r, "campaign_phase", -1) == 0)
    await r.handle_select_campaign("p1", "test_campanha.json")
    check("modo vira campaign", r.mode == "campaign")
    check("campaign carregado", r.campaign and r.campaign["id"] == "test_campanha")
    check("campaign_phase = 0", r.campaign_phase == 0)
    # inválida não muda estado
    await r.handle_select_campaign("p1", "nao_existe.json")
    check("campanha inválida mantém a seleção", r.mode == "campaign")
    # null volta para procedural
    await r.handle_select_campaign("p1", None)
    check("None volta para procedural", r.mode == "procedural" and r.campaign is None)
    # selecionar masmorra avulsa limpa a campanha
    await r.handle_select_campaign("p1", "test_campanha.json")
    await r.handle_select_dungeon("p1", "test_camp_a.json")
    check("select_dungeon limpa a campanha", r.campaign is None and r.mode == "authored")
    # não-host é ignorado
    r.mode = "procedural"
    await r.handle_select_campaign("p2", "test_campanha.json")
    check("não-host ignorado", r.mode == "procedural")

async def test_entrada_fase0():
    print("\n[3] enter_dungeon carrega a fase atual da campanha")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    r.phase = "city"
    await r.enter_dungeon("p1")
    check("carregou a fase 0 (grid 10×8 de camp_a)", r.map_w == 10 and r.map_h == 8)
    check("monstro da fase 0 (goblin)",
          sorted(m["type"] for m in r.monsters.values()) == ["goblin"])
    check("dungeon_def aponta a fase atual", r.dungeon_def is not None
          and r.dungeon_def.get("id") == "test_camp_a")
    check("objetivos da fase carregados", r.objectives
          and r.objectives["primary"]["type"] == "kill_all")

async def test_avanco_e_vitoria():
    print("\n[4] avanço de fase, preservação e vitória final")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    r.phase = "city"
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]
    p1["gold"] = 99; p1["hp"] = max(1, p1["hp"] - 3); hp_antes = p1["hp"]
    # cumpre o objetivo da fase 0 (kill_all)
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("após concluir fase 0 → cidade", r.phase == "city")
    check("avançou para a fase 1", r.campaign_phase == 1)
    check("dungeon_generated zerado p/ carregar a próxima", r.dungeon_generated is False)
    check("HP preservado entre fases", r.players["p1"]["hp"] == hp_antes)
    check("ouro preservado entre fases", r.players["p1"]["gold"] == 99)

    # entra na fase 1
    await r.enter_dungeon("p1")
    check("fase 1 carregada (grid 12×8 de camp_b)", r.map_w == 12 and r.map_h == 8)
    check("monstro da fase 1 (skeleton)",
          sorted(m["type"] for m in r.monsters.values()) == ["skeleton"])

    # cumpre o objetivo da última fase → vitória da campanha
    vit = {"c": False, "v": None}
    async def fake_end(victory): vit["c"] = True; vit["v"] = victory
    r.end_game = fake_end
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("última fase concluída → end_game(victory)", vit["c"] and vit["v"] is True)

async def test_retomar_mesma_fase():
    print("\n[5] sair sem concluir retoma a mesma fase")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    r.phase = "city"
    await r.enter_dungeon("p1")
    await r.handle_exit_dungeon("p1")     # sai sem concluir
    check("voltou à cidade", r.phase == "city")
    check("fase não avançou", r.campaign_phase == 0)
    await r.enter_dungeon("p1")
    check("retomou a fase 0 (10×8)", r.map_w == 10 and r.map_h == 8)

async def test_serializacao():
    print("\n[6] push_state expõe campaign")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    cap = {}
    async def capb(msg):
        if msg.get("type") == "game_state": cap.update(msg)
    r.broadcast = capb
    r.phase = "city"; await r.enter_dungeon("p1")
    await GameRoom.push_state(r)
    check("game_state traz campaign", cap.get("campaign") is not None)
    check("campaign phase/total corretos",
          cap["campaign"]["phase"] == 1 and cap["campaign"]["total"] == 2)

async def test_schema_objeto():
    print("\n[7] schema retrocompat (string | objeto)")
    base = {"schema_version": 1, "id": "c", "name": "C"}
    # objeto com file válido + intro/outro
    d = dict(base, dungeons=[{"file": "test_camp_a.json", "intro": "oi", "outro": "tchau"}])
    ok, msg = server.validar_campanha(d); check(f"objeto válido passa ({msg})", ok is True)
    # string ainda válida (4a)
    d = dict(base, dungeons=["test_camp_a.json"])
    check("string (4a) ainda válida", server.validar_campanha(d)[0] is True)
    # objeto sem file recusa
    d = dict(base, dungeons=[{"intro": "x"}])
    check("objeto sem file recusa", server.validar_campanha(d)[0] is False)
    # intro não-string recusa
    d = dict(base, dungeons=[{"file": "test_camp_a.json", "intro": 5}])
    check("intro não-texto recusa", server.validar_campanha(d)[0] is False)
    # helpers
    check("_fase_file de string", server._fase_file("a.json") == "a.json")
    check("_fase_file de objeto", server._fase_file({"file": "b.json"}) == "b.json")
    check("_fase_obj normaliza string",
          server._fase_obj("a.json") == {"file": "a.json", "intro": "", "outro": ""})

async def test_entrada_objeto():
    print("\n[8] enter_dungeon com fase em objeto")
    r = setup_room(); r.phase = "lobby"
    # injeta uma campanha com fase em objeto direto
    r.mode = "campaign"; r.campaign = {"schema_version": 1, "id": "c", "name": "C",
        "dungeons": [{"file": "test_camp_a.json", "intro": "abre", "outro": "fecha"}]}
    r.campaign_phase = 0; r.phase = "city"
    await r.enter_dungeon("p1")
    check("carregou a fase do objeto (10×8)", r.map_w == 10 and r.map_h == 8)

async def main():
    test_validacao()
    await test_selecao()
    await test_entrada_fase0()
    await test_avanco_e_vitoria()
    await test_retomar_mesma_fase()
    await test_serializacao()
    await test_schema_objeto()
    await test_entrada_objeto()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
