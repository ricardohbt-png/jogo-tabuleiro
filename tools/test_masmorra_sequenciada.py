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

def test_slides_na_aventura():
    print("\n[15] slides sobrevivem ao salvar a aventura")
    row = {"id": "rota_slides", "nome": "Rota", "x": 10, "y": 20, "fome": 0, "sede": 0,
           "dungeons": [{"file": "test_camp_a.json", "encadear": True,
                         "intro": {"slides": [{"text": "abre", "image": "assets/story/a.png",
                                               "fit": "contain"},
                                              {"image": "../../etc/passwd"}],
                                   "audio": "assets/story/m.mp3"},
                         "outro": "só texto"},
                        {"file": "test_camp_b.json"}]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou ({res if not ok else 'ok'})", ok is True)
        et = server.WORLD_ADVENTURES["rota_slides"]["dungeons"][0]
        check("intro continua sendo objeto", isinstance(et["intro"], dict))
        check("slide com imagem preservado",
              et["intro"]["slides"][0] == {"text": "abre", "image": "assets/story/a.png",
                                           "fit": "contain"})
        check("mídia fora de assets/story/ descartada",
              len(et["intro"]["slides"]) == 1)
        check("áudio preservado", et["intro"]["audio"] == "assets/story/m.mp3")
        check("outro em texto continua string", et["outro"] == "só texto")
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()

def _aventura_oculta(oculto, renome_min=5):
    return {"id": "test_oculto", "nome": "Ruínas Esquecidas", "x": 20, "y": 30,
            "fome": 0, "sede": 0, "renome_recompensa": 1,
            "oculto_ate_liberar": oculto,
            "requisito": {"renome_min": renome_min, "nivel_grupo_min": 0,
                          "item_id": "", "fato": "", "aventura_id": ""},
            "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
            "dungeons": [{"file": "test_camp_a.json", "encadear": False,
                          "intro": "", "outro": ""}]}

def _ids_no_mapa(r):
    return [a["id"] for a in r._city_state_payload()["world"]["adventures"]]

async def test_destino_oculto():
    print("\n[18] destino oculto no mapa-múndi")
    salvos = server.WORLD_ADVENTURES
    try:
        # oculto + requisito não cumprido → some do mapa
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(True)}
        r = setup_room(); r.renome = 0
        check("oculto e bloqueado não aparece", "test_oculto" not in _ids_no_mapa(r))
        # requisito cumprido → aparece
        r.renome = 5
        check("oculto e liberado aparece", "test_oculto" in _ids_no_mapa(r))
        # sem o flag, bloqueado continua visível (não-regressão)
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(False)}
        r2 = setup_room(); r2.renome = 0
        check("sem o flag, bloqueado continua visível", "test_oculto" in _ids_no_mapa(r2))
        # o editor enxerga o destino oculto
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(True)}
        pay = server._world_adventures_editor_payload()
        check("editor lista o destino oculto",
              any(a["id"] == "test_oculto" for a in pay["adventures"]))
        # helper direto
        r3 = setup_room(); r3.renome = 0
        check("_aventura_visivel False quando oculto e bloqueado",
              r3._aventura_visivel(server.WORLD_ADVENTURES["test_oculto"]) is False)
        r3.renome = 5
        check("_aventura_visivel True quando liberado",
              r3._aventura_visivel(server.WORLD_ADVENTURES["test_oculto"]) is True)
    finally:
        server.WORLD_ADVENTURES = salvos

def test_flag_persistida():
    print("\n[18b] o flag sobrevive ao salvar")
    row = {"id": "rota_oculta", "nome": "Rota", "x": 10, "y": 20, "fome": 0, "sede": 0,
           "oculto_ate_liberar": True,
           "requisito": {"renome_min": 3},
           "dungeons": ["test_camp_a.json"]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou ({res if not ok else 'ok'})", ok is True)
        check("flag preservado",
              server.WORLD_ADVENTURES["rota_oculta"]["oculto_ate_liberar"] is True)
        # ausente vira False (rotas antigas continuam visíveis)
        row2 = dict(row, id="rota_normal"); row2.pop("oculto_ate_liberar")
        server._save_world_adventures_upload([], [row2])
        check("ausente vira False",
              server.WORLD_ADVENTURES["rota_normal"]["oculto_ate_liberar"] is False)
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()

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

async def test_beat_abertura():
    print("\n[16] abertura da etapa ao entrar pelo mapa")
    r = setup_room(encadear=True)
    # a etapa 0 da aventura de teste não tem intro; damos um a ela
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][0]["intro"] = "ABRE-1"
    await r.handle_world_adventure("p1", "test_seq")
    beat = r._story_encadeada
    check("beat de abertura montado", beat is not None)
    check("texto da abertura",
          beat and [s.get("text") for s in beat["slides"]] == ["ABRE-1"])
    check("key identifica aventura e etapa", beat and beat["key"] == "aventura:test_seq:0")
    # etapa sem intro não emite beat
    r2 = setup_room(encadear=True)
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][0]["intro"] = ""
    await r2.handle_world_adventure("p1", "test_seq")
    check("sem intro não emite beat", r2._story_encadeada is None)

async def test_beat_encerramento():
    print("\n[17] encerramento ao concluir a etapa sem encadeamento")
    r = setup_room(encadear=False)     # etapa 0 tem outro "FECHA-1"
    await r.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r)
    check("voltou à cidade", r.phase == "city")
    beat = r._story_encadeada
    check("beat de encerramento montado", beat is not None)
    check("texto do encerramento",
          beat and [s.get("text") for s in beat["slides"]] == ["FECHA-1"])
    check("key identifica a etapa concluída", beat and beat["key"] == "fim:test_seq:0")
    check("city_state carrega o beat",
          r._city_state_payload().get("story") == beat)
    # etapa sem outro não emite beat
    r2 = setup_room(encadear=False)
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][0]["outro"] = ""
    await r2.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r2)
    check("sem outro não emite beat", r2._story_encadeada is None)

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

async def test_ausente_na_cidade():
    print("\n[8] o ausente age na cidade, a sala segue na masmorra")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    check("sala continua em playing", r.phase == "playing")
    check("_em_cidade só para quem saiu",
          r._em_cidade("p1") is True and r._em_cidade("p2") is False)
    # compra na loja estando fora
    p["gold"] = 999
    antes = len(p["bag"])
    await r.handle_shop_buy("p1", "mercador", "antidote")
    check("comprou no mercador estando fora", len(p["bag"]) > antes)
    # o companheiro dentro da masmorra NÃO compra
    q = r.players["p2"]; q["gold"] = 999; antes_q = len(q["bag"])
    await r.handle_shop_buy("p2", "mercador", "antidote")
    check("quem está na masmorra não compra", len(q["bag"]) == antes_q)
    # ações de grupo continuam bloqueadas para o ausente
    destino_antes = r.world_location
    await r.handle_world_travel("p1", "vila_charcos")
    check("ausente não viaja pelo mundo", r.world_location == destino_antes)

async def test_broadcast_separado():
    print("\n[9] game_state não chega a quem está na cidade")
    import json as _j
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    recebidos = {"p1": [], "p2": []}
    class FakeWS:
        def __init__(self, pid): self.pid = pid
        async def send(self, data): recebidos[self.pid].append(_j.loads(data)["type"])
    r.connections = {"p1": FakeWS("p1"), "p2": FakeWS("p2")}
    del r.broadcast; del r.send_to        # usa os métodos reais da classe
    await r.handle_exit_dungeon("p1")
    recebidos["p1"].clear(); recebidos["p2"].clear()
    await GameRoom.push_state(r)
    check("p1 (na cidade) não recebe game_state", "game_state" not in recebidos["p1"])
    check("p2 (na masmorra) recebe game_state", "game_state" in recebidos["p2"])
    await r.push_state_or_city()
    check("p1 recebe city_state", "city_state" in recebidos["p1"])
    check("p2 não recebe city_state", "city_state" not in recebidos["p2"])

async def test_contador_e_retorno():
    print("\n[10] contador de rodadas e retorno")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    check("espera inicial 2", p["fora_masmorra"]["rodadas_restantes"] == 2)
    await r._tick_retorno_masmorra()
    check("após 1 rodada resta 1", p["fora_masmorra"]["rodadas_restantes"] == 1)
    await r._tick_retorno_masmorra()
    check("após 2 rodadas resta 0", p["fora_masmorra"]["rodadas_restantes"] == 0)
    check("ainda está fora (rodada de tolerância)", r._ativo(p) is False)
    await r._tick_retorno_masmorra()
    check("na rodada seguinte volta sozinho", p.get("fora_masmorra") is None)
    check("voltou ativo", r._ativo(p) is True)
    check("reapareceu na escada", list(p["pos"]) == list(r.stairs_pos))
    check("com turno cheio", p["action_done"] is False and p["moves_left"] > 0)

async def test_volta_manual():
    print("\n[11] botão de voltar à masmorra")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    await r.handle_voltar_masmorra("p1")
    check("não volta antes de zerar", p.get("fora_masmorra") is not None)
    p["fora_masmorra"]["rodadas_restantes"] = 0
    await r.handle_voltar_masmorra("p1")
    check("volta ao zerar", p.get("fora_masmorra") is None)
    check("de volta ao tabuleiro", list(p["pos"]) == list(r.stairs_pos))

async def test_masmorra_esvazia():
    print("\n[12] masmorra sem ninguém volta para a cidade")
    r = setup_room()
    for pid in ("p1", "p2"):
        r.players[pid]["fome"] = 10; r.players[pid]["sede"] = 10
    await _entrar_e_posicionar_na_escada(r, "p1")
    await r.handle_exit_dungeon("p1")
    check("com 1 dentro, segue em jogo", r.phase == "playing")
    r.players["p2"]["pos"] = list(r.stairs_pos)
    r.initiative_order = [{"kind": "player", "id": "p2", "seq": 0, "initiative": 99,
                           "dex": 0, "int": 0}]
    r.initiative_index = 0
    await r.handle_exit_dungeon("p2")
    check("todos fora → sala volta à cidade", r.phase == "city")
    check("ninguém fica marcado como fora",
          all(not q.get("fora_masmorra") for q in r.players.values()))

async def test_morte_com_heroi_na_cidade():
    print("\n[13] presentes morrem com um herói na cidade")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    fim = {"chamou": False}
    async def fake_end(victory, story=None): fim["chamou"] = True
    r.end_game = fake_end
    r.players["p2"]["alive"] = False
    await r._checar_masmorra_vazia()
    check("não é game over", fim["chamou"] is False)
    check("sala volta à cidade", r.phase == "city")

async def test_recompensa_com_ausente():
    print("\n[14] o ausente participa da recompensa e da etapa encadeada")
    r = setup_room(encadear=True)
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    xp_antes = p["xp"]; ouro_antes = p["gold"]
    r.objectives = {"primary": {"type": "kill_all", "xp": 100,
                                "reward": {"gold": 100, "items": []}},
                    "secondary": []}
    r._objetivo_concluido = False
    await _concluir_etapa(r)
    check("ausente recebeu XP", p["xp"] > xp_antes)
    check("ausente recebeu ouro", p["gold"] > ouro_antes)
    check("emendou na etapa 2", r.phase == "playing" and r.world_adventure_index == 1)
    check("segue fora, com o contador de pé", p.get("fora_masmorra") is not None)

async def main():
    test_helpers_etapa()
    test_persistencia_campos()
    test_validacao_saida()
    test_slides_na_aventura()
    test_flag_persistida()
    await test_encadeamento()
    await test_sem_encadeamento()
    await test_beat_abertura()
    await test_beat_encerramento()
    await test_destino_oculto()
    await test_saida_recusada()
    await test_saida_efetiva()
    await test_ausente_na_cidade()
    await test_broadcast_separado()
    await test_contador_e_retorno()
    await test_volta_manual()
    await test_masmorra_esvazia()
    await test_morte_com_heroi_na_cidade()
    await test_recompensa_com_ausente()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
