"""Testes de masmorra sequenciada + saída individual pela escada.
Roda da raiz: python tools/test_masmorra_sequenciada.py"""
import asyncio, sys, os
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

def test_helpers_etapa():
    print("\n[1] helpers de etapa e espera")
    check("_etapa_file de string", server._etapa_file("a.json") == "a.json")
    check("_etapa_file de objeto", server._etapa_file({"file": "b.json"}) == "b.json")
    check("_etapa_file de lixo", server._etapa_file(7) is None)
    check("_etapa_obj normaliza string",
          server._etapa_obj("a.json") == {"file": "a.json", "encadear": False,
                                          "intro": "", "outro": ""})
    check("_etapa_obj preserva encadear",
          server._etapa_obj({"file": "b.json", "encadear": True})["encadear"] is True)
    check("_etapa_obj preserva intro/outro",
          server._etapa_obj({"file": "b.json", "intro": "abre", "outro": "fecha"})["intro"] == "abre")
    # espera
    check("espera default é fixa 0",
          server._clean_espera(None) == {"modo": "fixa", "rodadas": 0, "dados": ""})
    check("espera fixa preserva rodadas",
          server._clean_espera({"modo": "fixa", "rodadas": 3})["rodadas"] == 3)
    check("espera fixa faz clamp em 99",
          server._clean_espera({"modo": "fixa", "rodadas": 500})["rodadas"] == 99)
    check("espera com dados válidos",
          server._clean_espera({"modo": "dados", "dados": "1d4"})["dados"] == "1d4")
    check("dados inválidos caem para fixa",
          server._clean_espera({"modo": "dados", "dados": "muito"})["modo"] == "fixa")
    check("_rolar_espera fixa devolve o valor",
          server._rolar_espera({"modo": "fixa", "rodadas": 2}) == 2)
    check("_rolar_espera dados fica na faixa",
          1 <= server._rolar_espera({"modo": "dados", "dados": "1d4"}) <= 4)

def test_persistencia_campos():
    print("\n[2] persistência dos campos novos")
    row = {"id": "rota_teste", "nome": "Rota", "x": 10, "y": 20, "fome": 2, "sede": 3,
           "espera_retorno": {"modo": "dados", "dados": "1d4"},
           "dungeons": [{"file": "test_camp_a.json", "encadear": True, "outro": "fecha-1"},
                        "test_camp_b.json"]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou a aventura ({res if not ok else 'ok'})", ok is True)
        a = server.WORLD_ADVENTURES["rota_teste"]
        check("etapa 1 virou objeto com encadear",
              a["dungeons"][0] == {"file": "test_camp_a.json", "encadear": True,
                                   "intro": "", "outro": "fecha-1"})
        check("etapa 2 (string legada) normalizada",
              a["dungeons"][1]["file"] == "test_camp_b.json"
              and a["dungeons"][1]["encadear"] is False)
        check("espera_retorno preservada",
              a["espera_retorno"] == {"modo": "dados", "rodadas": 0, "dados": "1d4"})
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()

def test_validacao_saida():
    print("\n[3] validar_dungeon aceita saida_permitida")
    defn = server.carregar_dungeon("test_camp_a.json")
    defn["saida_permitida"] = False
    check("saida_permitida False é válida", server.validar_dungeon(defn)[0] is True)
    defn["saida_permitida"] = "talvez"
    check("saida_permitida não-booleana recusa", server.validar_dungeon(defn)[0] is False)
    defn.pop("saida_permitida")
    check("ausente continua válida", server.validar_dungeon(defn)[0] is True)

def _aventura(encadear):
    return {"id": "test_seq", "nome": "Rota Encadeada", "x": 10, "y": 10,
            "fome": 1, "sede": 1, "renome_recompensa": 1,
            "requisito": {"renome_min": 0, "nivel_grupo_min": 0,
                          "item_id": "", "fato": "", "aventura_id": ""},
            "espera_retorno": {"modo": "fixa", "rodadas": 2, "dados": ""},
            "dungeons": [{"file": "test_camp_a.json", "encadear": encadear,
                          "intro": "", "outro": "FECHA-1"},
                         {"file": "test_camp_b.json", "encadear": False,
                          "intro": "ABRE-2", "outro": ""}]}

def setup_room(encadear=True):
    """Sala de 2 heróis parada na cidade, com a aventura de teste instalada."""
    server.WORLD_ADVENTURES["test_seq"] = _aventura(encadear)
    r = GameRoom("SEQ")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop; r.broadcast_lobby = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys()); r.host_pid = "p1"
    r.phase = "city"
    return r

async def _concluir_etapa(r):
    """Mata tudo, recalcula objetivos e encerra a missão pelo host."""
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    await r.handle_encerrar_missao("p1")

async def test_encadeamento():
    print("\n[4] etapa encadeada começa imediatamente")
    r = setup_room(encadear=True)
    await r.handle_world_adventure("p1", "test_seq")
    check("entrou na etapa 1 (10×8)", r.map_w == 10 and r.map_h == 8)
    p1 = r.players["p1"]
    p1["hp"] = max(1, p1["hp"] - 4); hp_antes = p1["hp"]
    p1["technique_cooldowns"] = {"brutalidade": 99}
    p1["fome"] = 7; p1["sede"] = 5
    await _concluir_etapa(r)
    check("NÃO passou pela cidade", r.phase == "playing")
    check("carregou a etapa 2 (12×8)", r.map_w == 12 and r.map_h == 8)
    check("índice avançou", r.world_adventure_index == 1)
    check("progresso gravado", r.world_adventure_progress.get("test_seq") == 1)
    check("segue na mesma aventura", r.world_adventure_id == "test_seq")
    check("HP não se recupera", r.players["p1"]["hp"] == hp_antes)
    check("recarga de técnica não se recupera",
          r.players["p1"]["technique_cooldowns"] == {"brutalidade": 99})
    check("fome/sede não se recuperam e não são cobradas de novo",
          r.players["p1"]["fome"] == 7 and r.players["p1"]["sede"] == 5)
    check("beat de história encadeada montado",
          r._story_encadeada and [s.get("text") for s in r._story_encadeada["slides"]]
          == ["FECHA-1", "ABRE-2"])
    # última etapa: sem próxima, encerra normalmente pela cidade
    await _concluir_etapa(r)
    check("última etapa volta à cidade", r.phase == "city")
    check("aventura encerrada", r.world_adventure_id is None)

async def test_sem_encadeamento():
    print("\n[5] sem o flag, continua voltando à cidade (não-regressão)")
    r = setup_room(encadear=False)
    await r.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r)
    check("voltou à cidade", r.phase == "city")
    check("aventura liberada", r.world_adventure_id is None)
    check("progresso gravado mesmo assim", r.world_adventure_progress.get("test_seq") == 1)

async def _entrar_e_posicionar_na_escada(r, pid="p1"):
    await r.handle_world_adventure("p1", "test_seq")
    r.players[pid]["pos"] = list(r.stairs_pos)
    r.initiative_order = [{"kind": "player", "id": pid, "seq": 0, "initiative": 99,
                           "dex": 0, "int": 0}]
    r.initiative_index = 0; r.initiative_active = True
    return r.players[pid]

async def test_saida_recusada():
    print("\n[6] saída pela escada — recusas")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 50; p["sede"] = 50
    # longe da escada
    p["pos"] = [r.stairs_pos[0] + 2, r.stairs_pos[1]]
    await r.handle_exit_dungeon("p1")
    check("longe da escada não sai", p.get("fora_masmorra") is None)
    check("recusa não leva o grupo à cidade", r.phase == "playing")
    p["pos"] = list(r.stairs_pos)
    # fora do turno
    r.initiative_order[0]["id"] = "p2"
    await r.handle_exit_dungeon("p1")
    check("fora do turno não sai", p.get("fora_masmorra") is None)
    r.initiative_order[0]["id"] = "p1"
    # sem provisões para ida e volta (custo da aventura é 1/1 → precisa de 2/2)
    p["fome"] = 1; p["sede"] = 50
    await r.handle_exit_dungeon("p1")
    check("sem fome para ida+volta não sai", p.get("fora_masmorra") is None)
    p["fome"] = 50; p["sede"] = 1
    await r.handle_exit_dungeon("p1")
    check("sem sede para ida+volta não sai", p.get("fora_masmorra") is None)
    # masmorra sem saída
    p["fome"] = 50; p["sede"] = 50; r.saida_permitida = False
    await r.handle_exit_dungeon("p1")
    check("masmorra sem saída não deixa sair", p.get("fora_masmorra") is None)

async def test_saida_efetiva():
    print("\n[7] saída pela escada — efeito")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    check("marcado como fora", isinstance(p.get("fora_masmorra"), dict))
    check("espera fixa de 2 rodadas", p["fora_masmorra"]["rodadas_restantes"] == 2)
    check("cobrou ida e volta (2×1 fome)", p["fome"] == 8)
    check("cobrou ida e volta (2×1 sede)", p["sede"] == 8)
    check("peão saiu do tabuleiro", p["pos"] == [-1, -1])
    check("_ativo passa a ser falso", r._ativo(p) is False)
    check("companheiro segue ativo", r._ativo(r.players["p2"]) is True)
    check("a sala continua na masmorra", r.phase == "playing")
    await r.handle_exit_dungeon("p1")
    check("não sai duas vezes (não cobra de novo)", p["fome"] == 8)

async def main():
    test_helpers_etapa()
    test_persistencia_campos()
    test_validacao_saida()
    await test_encadeamento()
    await test_sem_encadeamento()
    await test_saida_recusada()
    await test_saida_efetiva()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
