"""Editor de cidades — criar, editar e excluir cidades pelo editor.
  • _aplicar_estado_cidades monta WORLD_LOCATIONS a partir das originais + edições.
  • Cidade nova nasce vazia (sem lojas, sem pontos de mapa, sem NPCs de taverna).
  • Rota sem custo definido = viagem grátis; par com custo debita o valor.
  • Excluir limpa os subsistemas derivados; Alva e Luz nunca é excluída.
Roda da raiz: python tools/test_cidades_editor.py"""
import asyncio, json, os, shutil, sys, tempfile
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

CIDADE_NOVA = {"id": "porto_negro", "nome": "Porto Negro", "tipo": "cidade",
               "imagem": "assets/city/porto_negro.png", "x": 60.1, "y": 44.0}

def isolar_arquivos():
    """O teste mexe nos dicionários globais e chama handlers que gravam em disco.
    Redireciona TODOS os arquivos para uma pasta temporária — nunca toca nos dados
    reais do usuário — e devolve um restaurador do estado inicial do processo."""
    tmpdir = tempfile.mkdtemp(prefix="cidades_teste_")
    arquivos = ("WORLD_CITIES_FILE", "CITY_SHOPS_FILE", "CITY_SCENES_FILE", "CITY_MAP_POINTS_FILE")
    originais = {nome: getattr(S, nome) for nome in arquivos}
    for nome in arquivos:
        setattr(S, nome, os.path.join(tmpdir, nome.lower() + ".json"))
    inicial = {"shops": deepcopy(S.CITY_SHOPS), "points": deepcopy(S.CITY_MAP_POINTS),
               "scenes": deepcopy(S.CITY_SCENES), "cities": deepcopy(S.WORLD_CITIES),
               "locations": deepcopy(S.WORLD_LOCATIONS), "routes": dict(S.WORLD_ROUTES)}

    def restaurar():
        for nome, valor in originais.items():
            setattr(S, nome, valor)
        for alvo, copia in ((S.CITY_SHOPS, inicial["shops"]), (S.CITY_MAP_POINTS, inicial["points"]),
                            (S.CITY_SCENES, inicial["scenes"]), (S.WORLD_LOCATIONS, inicial["locations"]),
                            (S.WORLD_ROUTES, inicial["routes"])):
            alvo.clear(); alvo.update(copia)
        S.WORLD_CITIES = inicial["cities"]
        shutil.rmtree(tmpdir, ignore_errors=True)
    return restaurar

def reset_mundo():
    """Volta o mundo às 4 cidades originais, sem nenhuma edição do editor."""
    S._aplicar_estado_cidades([], {}, [], None)
    S._sincronizar_cidades_derivadas()

def _rodar_verificacoes():
    print("\n[1] Criar cidade")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    check("cidade nova entra no mundo", "porto_negro" in S.WORLD_LOCATIONS)
    check("nome preservado", S.WORLD_LOCATIONS["porto_negro"]["nome"] == "Porto Negro")
    check("coordenadas preservadas", S.WORLD_LOCATIONS["porto_negro"]["x"] == 60.1)
    check("as 4 originais continuam", all(c in S.WORLD_LOCATIONS for c in
          ("alva_e_luz", "vila_riacho", "vila_corvin", "graciero")))

    print("\n[2] Editar cidade original (override)")
    reset_mundo()
    S._aplicar_estado_cidades([], {"graciero": {"nome": "Graciero Velho", "tipo": "vila",
                                                "imagem": "assets/city/novo.png"}}, [], None)
    check("nome editado", S.WORLD_LOCATIONS["graciero"]["nome"] == "Graciero Velho")
    check("tipo editado", S.WORLD_LOCATIONS["graciero"]["tipo"] == "vila")
    check("imagem editada", S.WORLD_LOCATIONS["graciero"]["imagem"] == "assets/city/novo.png")
    check("rota antiga intacta",
          S.WORLD_ROUTES[frozenset(("alva_e_luz", "graciero"))]["fome"] == 14)

    print("\n[3] Excluir cidade")
    reset_mundo()
    S._aplicar_estado_cidades([], {}, ["vila_corvin"], None)
    check("cidade removida do mundo", "vila_corvin" not in S.WORLD_LOCATIONS)
    check("rotas dela sumiram",
          not any("vila_corvin" in par for par in S.WORLD_ROUTES))
    reset_mundo()
    S._aplicar_estado_cidades([], {}, ["alva_e_luz"], None)
    check("Alva e Luz não pode ser excluída", "alva_e_luz" in S.WORLD_LOCATIONS)

    print("\n[4] Validação recusa entrada inválida")
    reset_mundo()
    S._aplicar_estado_cidades([{"id": "sem nome", "nome": "", "x": 10, "y": 10}], {}, [], None)
    check("id/nome inválidos recusados", len(S.WORLD_LOCATIONS) == 4)
    S._aplicar_estado_cidades([dict(CIDADE_NOVA, x=180)], {}, [], None)
    check("coordenada fora do mapa recusada", "porto_negro" not in S.WORLD_LOCATIONS)
    S._aplicar_estado_cidades([dict(CIDADE_NOVA, id="alva_e_luz")], {}, [], None)
    check("id duplicado não sobrescreve original",
          S.WORLD_LOCATIONS["alva_e_luz"]["nome"] == "Alva e Luz")

    print("\n[5] Round-trip pelo arquivo")
    reset_mundo()
    tmp = os.path.join(tempfile.gettempdir(), "cidades_teste.json")
    original_file = S.WORLD_CITIES_FILE
    S.WORLD_CITIES_FILE = tmp
    try:
        S._aplicar_estado_cidades([CIDADE_NOVA], {"graciero": {"nome": "Graciero Velho"}},
                                  ["vila_corvin"],
                                  [{"from": "porto_negro", "to": "alva_e_luz", "fome": 8, "sede": 8}])
        S._save_world_cities()
        reset_mundo()
        check("reset limpou a cidade nova", "porto_negro" not in S.WORLD_LOCATIONS)
        S._load_world_cities()
        check("cidade nova voltou do arquivo", "porto_negro" in S.WORLD_LOCATIONS)
        check("override voltou do arquivo", S.WORLD_LOCATIONS["graciero"]["nome"] == "Graciero Velho")
        check("exclusão voltou do arquivo", "vila_corvin" not in S.WORLD_LOCATIONS)
        check("rota voltou do arquivo",
              S.WORLD_ROUTES[frozenset(("porto_negro", "alva_e_luz"))]["sede"] == 8)
    finally:
        S.WORLD_CITIES_FILE = original_file
        if os.path.exists(tmp): os.remove(tmp)
        reset_mundo()

    print("\n[6] Cidade nova nasce vazia; excluir limpa os derivados")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    S._sincronizar_cidades_derivadas()
    check("sem lojas", S.CITY_SHOPS.get("porto_negro") == {})
    # Sem lojas, o único ponto implícito é a Caravana de Viagem — ela precisa
    # existir como ponto editável, senão o cliente a desenharia num lugar fixo
    # que o editor não lista nem reposiciona.
    pontos = S.CITY_MAP_POINTS.get("porto_negro") or {}
    check("só a Caravana no mapa da cidade nova", list(pontos) == ["caravana"])
    check("Caravana implícita tem tipo", (pontos.get("caravana") or {}).get("type") == "caravana")
    # Cidade criada no editor nasce sem nenhuma cena de conversa — as cenas são
    # criadas uma a uma na aba "Cenas e NPCs".
    check("cidade nova nasce sem cenas", S.CITY_SCENES.get("porto_negro") == {})
    check("Alva e Luz mantém a cena da taverna com seus NPCs",
          len(((S.CITY_SCENES.get("alva_e_luz") or {}).get("taverna") or {}).get("slots") or []) >= 8)
    S._aplicar_estado_cidades([], {}, [], None)
    S._sincronizar_cidades_derivadas()
    check("excluir limpa lojas", "porto_negro" not in S.CITY_SHOPS)
    check("excluir limpa pontos", "porto_negro" not in S.CITY_MAP_POINTS)
    check("excluir limpa cenas", "porto_negro" not in S.CITY_SCENES)

    print("\n[7] Rota ausente = viagem grátis")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], [])   # tabela de custos vazia
    S._sincronizar_cidades_derivadas()
    sala = S.GameRoom("TEST")
    enviados = []
    async def noop(*a, **k): pass
    async def cap_broadcast(msg, *a, **k): enviados.append(msg)
    sala.gm_say = noop; sala.broadcast = cap_broadcast; sala.send_to = noop
    sala._checkpoint_savegame = lambda *a, **k: None
    sala.phase = "city"; sala.host_pid = "p1"; sala.world_location = "alva_e_luz"
    heroi = S.make_player("p1", "Victor", "warrior", 0)
    heroi["fome"], heroi["sede"] = 20, 20
    sala.players["p1"] = heroi
    asyncio.run(sala.handle_world_travel("p1", "porto_negro"))
    check("viajou para a cidade nova", sala.world_location == "porto_negro")
    check("não gastou fome", heroi["fome"] == 20)
    check("não gastou sede", heroi["sede"] == 20)

    print("\n[8] Rota com custo debita; payload cobre todos os pares")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [],
                              [{"from": "alva_e_luz", "to": "porto_negro", "fome": 5, "sede": 3}])
    S._sincronizar_cidades_derivadas()
    sala.world_location = "alva_e_luz"; heroi["fome"], heroi["sede"] = 20, 20
    asyncio.run(sala.handle_world_travel("p1", "porto_negro"))
    check("custo de fome debitado", heroi["fome"] == 15)
    check("custo de sede debitado", heroi["sede"] == 17)
    enviados.clear()
    asyncio.run(sala.broadcast_city_state())
    rotas = (enviados[-1].get("world") or {}).get("routes") or []
    n_cidades = len(S.WORLD_LOCATIONS)
    check("payload traz todos os pares", len(rotas) == n_cidades * (n_cidades - 1) // 2)
    par = next((r for r in rotas if {r["from"], r["to"]} == {"porto_negro", "vila_riacho"}), None)
    check("par sem custo vai como 0/0", par is not None and par["fome"] == 0 and par["sede"] == 0)
    reset_mundo()

    print("\n[9] Handler de save do editor")
    reset_mundo()
    tmp2 = os.path.join(tempfile.gettempdir(), "cidades_teste2.json")
    original_file = S.WORLD_CITIES_FILE
    S.WORLD_CITIES_FILE = tmp2
    try:
        ok, payload = S._save_world_cities_upload([CIDADE_NOVA], {}, [],
                                                  [{"from": "alva_e_luz", "to": "porto_negro", "fome": 5, "sede": 3}])
        check("save aceito", ok is True)
        check("payload devolve a cidade nova",
              any(c["id"] == "porto_negro" for c in (payload or {}).get("cities", [])))
        check("payload traz a tabela de rotas", isinstance((payload or {}).get("routes"), list))
        check("payload informa a cidade inicial", (payload or {}).get("city_inicial") == "alva_e_luz")
        check("arquivo gravado", os.path.exists(tmp2))
        with open(tmp2, encoding="utf-8") as f: gravado = json.load(f)
        check("arquivo contém a cidade", gravado["cities"][0]["id"] == "porto_negro")
        check("derivados sincronizados pelo handler", S.CITY_SHOPS.get("porto_negro") == {})

        ok2, erro = S._save_world_cities_upload("não é lista", {}, [], [])
        check("payload inválido recusado", ok2 is False and isinstance(erro, str))

        sala2 = S.GameRoom("TEST2")
        sala2.phase = "city"; sala2.world_location = "porto_negro"
        S.rooms["TEST2"] = sala2
        try:
            S._save_world_cities_upload([], {}, [], [{"from": "alva_e_luz", "to": "graciero", "fome": 14, "sede": 14}])
            check("sala em cidade excluída volta para Alva e Luz",
                  sala2.world_location == "alva_e_luz")
        finally:
            S.rooms.pop("TEST2", None)
    finally:
        S.WORLD_CITIES_FILE = original_file
        if os.path.exists(tmp2): os.remove(tmp2)
        reset_mundo()

    print("\n[10] Upload da ilustração da cidade")
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()
    ok, caminho = S._save_city_art_upload("porto negro.png", png)
    check("upload aceito", ok is True)
    check("caminho em assets/city", str(caminho).startswith("assets/city/"))
    arquivo = os.path.join(S.BASE_DIR, str(caminho).replace("/", os.sep))
    check("arquivo gravado no disco", os.path.exists(arquivo))
    if os.path.exists(arquivo): os.remove(arquivo)
    ok2, _ = S._save_city_art_upload("mapa.exe", png)
    check("extensão inválida recusada", ok2 is False)
    ok3, caminho3 = S._save_city_art_upload("../fuga.png", png)
    check("path traversal neutralizado",
          ok3 is False or ".." not in str(caminho3))
    if ok3:
        arquivo3 = os.path.join(S.BASE_DIR, str(caminho3).replace("/", os.sep))
        if os.path.exists(arquivo3): os.remove(arquivo3)
    ok4, _ = S._save_city_art_upload("grande.png", "A" * (S.STORY_UPLOAD_MAX * 2))
    check("arquivo grande demais recusado", ok4 is False)

    print("\n[12] Pontos implícitos são editáveis (Caravana e prédio de cada loja)")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    S._sincronizar_cidades_derivadas()
    # Abrir a loja da taverna na cidade tem de materializar o ponto do prédio:
    # antes ele era desenhado só pelo cliente, num lugar fixo e invisível ao editor.
    ok_stock, payload = S._save_city_shops_upload({"porto_negro": {"taverna": []}})
    pontos = S.CITY_MAP_POINTS.get("porto_negro") or {}
    check("estoque salvo", ok_stock is True)
    check("prédio da loja virou ponto editável", pontos.get("taverna", {}).get("type") == "taverna")
    check("ponto implícito vai para o editor",
          "taverna" in (payload["city_points"].get("porto_negro") or {}))
    # Ponto autoral do mesmo tipo (id diferente) não ganha um segundo ponto implícito.
    S.CITY_MAP_POINTS["porto_negro"]["ponto_1"] = {"x": 10.0, "y": 20.0, "type": "mercador"}
    S._save_city_shops_upload({"porto_negro": {"mercador": []}})
    tipos = [p.get("type") for p in (S.CITY_MAP_POINTS.get("porto_negro") or {}).values()]
    check("sem ponto duplicado do mesmo tipo", tipos.count("mercador") == 1)
    check("ponto autoral preservado", S.CITY_MAP_POINTS["porto_negro"]["ponto_1"]["x"] == 10.0)
    # O posicionamento dos pontos virou EXCLUSIVO do Editor: `handle_city_map_points`
    # recusa qualquer ajuste em jogo (o cliente também não desenha mais o botão
    # "📍 Ajustar pontos"). O ponto autoral tem de sair intacto da tentativa.
    S.CITY_MAP_POINTS["porto_negro"]["ponto_1"]["name"] = "Feira"
    sala = S.GameRoom("PONTO")
    sala.phase = "city"; sala.host_pid = "h1"; sala.world_location = "porto_negro"
    sala.connections = {}
    recusas = []
    async def _cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": recusas.append(msg.get("msg", ""))
    sala.send_to = _cap
    asyncio.run(sala.handle_city_map_points("h1", "porto_negro", {"ponto_1": {"x": 70.0, "y": 30.0}}))
    movido = S.CITY_MAP_POINTS["porto_negro"]["ponto_1"]
    check("ajuste em jogo é recusado (só o Editor posiciona)",
          any("Editor" in m for m in recusas))
    check("ponto não se move pela tentativa em jogo", (movido["x"], movido["y"]) == (10.0, 20.0))
    check("tipo e nome preservados",
          movido.get("type") == "mercador" and movido.get("name") == "Feira")
    reset_mundo()

    print("\n[13] Ponto de masmorra vinculado a um destino")
    reset_mundo()
    S.WORLD_ADVENTURES["destino_teste"] = {
        "id": "destino_teste", "nome": "Cripta de Teste", "x": 50.0, "y": 50.0,
        "fome": 2, "sede": 2, "dungeons": [{"file": "a.json"}],
        "oculto_ate_liberar": False, "revisitavel": False,
        "requisito": {"renome_min": 0, "nivel_grupo_min": 0, "item_id": "",
                      "fato": "", "aventura_id": ""},
    }
    # _save_city_shops_upload SUBSTITUI o dict inteiro de pontos de alva_e_luz;
    # reset_mundo() não desfaz isso (só poda cidades que deixaram de existir).
    # Sem restaurar aqui, "cripta"/"fantasma" vazariam para as seções seguintes.
    antes_pontos = deepcopy(S.CITY_MAP_POINTS["alva_e_luz"])
    try:
        enviados = {"alva_e_luz": {
            "cripta": {"x": 40.0, "y": 55.0, "type": "dungeon", "name": "Cripta",
                       "emoji": "🚪", "aventura": "destino_teste"},
            "fantasma": {"x": 10.0, "y": 10.0, "type": "dungeon", "name": "Sem destino",
                         "aventura": "nao_existe"},
        }}
        ok_save, _ = S._save_city_shops_upload({}, None, enviados)
        salvos = S.CITY_MAP_POINTS["alva_e_luz"]
        check("save do editor aceito", ok_save is True)
        check("tipo dungeon preservado", salvos["cripta"].get("type") == "dungeon")
        check("vínculo válido preservado", salvos["cripta"].get("aventura") == "destino_teste")
        check("emoji do ponto preservado", salvos["cripta"].get("emoji") == "🚪")
        check("vínculo inexistente é descartado", "aventura" not in salvos["fantasma"])
        check("ponto sem vínculo continua salvo", "fantasma" in salvos)
        # Round-trip pelo arquivo: o vínculo tem de sobreviver ao boot.
        S._save_city_map_points()
        S.CITY_MAP_POINTS["alva_e_luz"].pop("cripta")
        S._load_city_map_points()
        check("vínculo sobrevive ao boot",
              S.CITY_MAP_POINTS["alva_e_luz"].get("cripta", {}).get("aventura") == "destino_teste")
        check("emoji sobrevive ao boot",
              S.CITY_MAP_POINTS["alva_e_luz"].get("cripta", {}).get("emoji") == "🚪")
        # O boot só checa FORMATO: sem WORLD_ADVENTURES carregado (arquivo ausente
        # ou corrompido) o vínculo não pode ser apagado da memória, senão o próximo
        # save do editor gravaria a perda em disco.
        guardado = dict(S.WORLD_ADVENTURES)
        S.WORLD_ADVENTURES.clear()
        S.CITY_MAP_POINTS["alva_e_luz"].pop("cripta")
        S._load_city_map_points()
        check("boot sem catálogo de destinos não apaga o vínculo",
              S.CITY_MAP_POINTS["alva_e_luz"].get("cripta", {}).get("aventura") == "destino_teste")
        S.WORLD_ADVENTURES.update(guardado)
        # Formato inválido (caractere fora do padrão, ou acima de 48) é descartado
        # no boot mesmo com WORLD_ADVENTURES carregado — cobre o regex em si.
        S.CITY_MAP_POINTS["alva_e_luz"]["invalido1"] = {"x": 5.0, "y": 5.0, "type": "dungeon",
                                                          "aventura": "NÃO VALE!"}
        S.CITY_MAP_POINTS["alva_e_luz"]["invalido2"] = {"x": 6.0, "y": 6.0, "type": "dungeon",
                                                          "aventura": "a" * 60}
        S._save_city_map_points()
        S._load_city_map_points()
        check("aventura com caractere inválido é descartada no boot",
              "aventura" not in S.CITY_MAP_POINTS["alva_e_luz"].get("invalido1", {}))
        check("aventura acima de 48 chars (teto real dos ids) é descartada no boot",
              "aventura" not in S.CITY_MAP_POINTS["alva_e_luz"].get("invalido2", {}))
    finally:
        S.WORLD_ADVENTURES.pop("destino_teste", None)
        S.CITY_MAP_POINTS["alva_e_luz"] = antes_pontos
    reset_mundo()

    print("\n[14] Destino oculto não vaza no payload da cidade")
    reset_mundo()
    base_req = {"renome_min": 0, "nivel_grupo_min": 0, "item_id": "", "fato": "", "aventura_id": ""}
    S.WORLD_ADVENTURES["oculto_teste"] = {
        "id": "oculto_teste", "nome": "Cripta Secreta", "x": 10.0, "y": 10.0,
        "fome": 0, "sede": 0, "dungeons": [{"file": "a.json"}],
        "oculto_ate_liberar": True, "revisitavel": False,
        "requisito": dict(base_req, renome_min=50)}
    S.WORLD_ADVENTURES["bloqueado_teste"] = {
        "id": "bloqueado_teste", "nome": "Torre Fechada", "x": 20.0, "y": 20.0,
        "fome": 0, "sede": 0, "dungeons": [{"file": "a.json"}],
        "oculto_ate_liberar": False, "revisitavel": False,
        "requisito": dict(base_req, renome_min=50)}
    # Mutação direta no dict global (não passa por _save_city_shops_upload) —
    # também precisa ser restaurada, senão vaza para as seções seguintes.
    antes_pontos = deepcopy(S.CITY_MAP_POINTS["alva_e_luz"])
    try:
        pontos_cidade = S.CITY_MAP_POINTS["alva_e_luz"]
        pontos_cidade["cripta_secreta"] = {"x": 40.0, "y": 55.0, "type": "dungeon",
                                           "aventura": "oculto_teste"}
        pontos_cidade["torre"] = {"x": 45.0, "y": 55.0, "type": "dungeon",
                                  "aventura": "bloqueado_teste"}
        pontos_cidade["solto"] = {"x": 46.0, "y": 56.0, "type": "dungeon"}
        pontos_cidade["sem_tipo"] = {"x": 47.0, "y": 57.0, "aventura": "bloqueado_teste"}
        sala = S.GameRoom("PAYLOAD")
        sala.phase = "city"; sala.world_location = "alva_e_luz"; sala.renome = 0
        visiveis = sala._city_points_payload()["alva_e_luz"]
        check("ponto de destino oculto some do payload", "cripta_secreta" not in visiveis)
        check("ponto de destino bloqueado (visível) permanece", "torre" in visiveis)
        check("ponto de masmorra sem vínculo some do payload", "solto" not in visiveis)
        check("ponto de loja não é afetado", "mercador" in visiveis)
        check("ponto sem type não é filtrado (filtro só vale para type=dungeon)",
              "sem_tipo" in visiveis)
        sala.renome = 99
        check("ponto aparece quando o requisito é cumprido",
              "cripta_secreta" in sala._city_points_payload()["alva_e_luz"])
        check("dicionário global não é mutado",
              "cripta_secreta" in S.CITY_MAP_POINTS["alva_e_luz"])
        check("outras cidades continuam no payload",
              "vila_riacho" in sala._city_points_payload())
    finally:
        S.WORLD_ADVENTURES.pop("oculto_teste", None)
        S.WORLD_ADVENTURES.pop("bloqueado_teste", None)
        S.CITY_MAP_POINTS["alva_e_luz"] = antes_pontos
    reset_mundo()

    print("\n[15] Editor recebe os destinos para vincular")
    reset_mundo()
    S.WORLD_ADVENTURES["destino_editor"] = {
        "id": "destino_editor", "nome": "Cripta do Editor", "x": 1.0, "y": 1.0,
        "fome": 0, "sede": 0, "dungeons": [{"file": "a.json"}, {"file": "b.json"}],
        "oculto_ate_liberar": True, "revisitavel": False,
        "requisito": {"renome_min": 99, "nivel_grupo_min": 0, "item_id": "",
                      "fato": "", "aventura_id": ""}}
    S.WORLD_ADVENTURES["destino_vazio"] = {
        "id": "destino_vazio", "nome": "Rascunho", "x": 2.0, "y": 2.0,
        "fome": 0, "sede": 0, "dungeons": [], "oculto_ate_liberar": False,
        "revisitavel": False, "requisito": {}}
    antes_pontos = deepcopy(S.CITY_MAP_POINTS["alva_e_luz"])
    try:
        payload = S._city_shops_editor_payload()
        destinos = {a["id"]: a for a in payload.get("adventures", [])}
        check("destino chega ao editor", "destino_editor" in destinos)
        check("nome do destino", destinos.get("destino_editor", {}).get("nome") == "Cripta do Editor")
        check("nº de masmorras do destino", destinos.get("destino_editor", {}).get("dungeons") == 2)
        check("destino sem masmorra aparece com contagem 0",
              destinos.get("destino_vazio", {}).get("dungeons") == 0)
        # Contraste real: o payload do EDITOR não filtra ocultos (o autor precisa
        # ver o que criou), mas o payload de JOGO (_city_points_payload) filtra —
        # a mesma checagem que a asserção duplicada acima só fingia fazer.
        S.CITY_MAP_POINTS["alva_e_luz"]["ponto_editor"] = {"x": 15.0, "y": 15.0,
                                                             "type": "dungeon", "aventura": "destino_editor"}
        sala = S.GameRoom("PAYLOAD2")
        sala.phase = "city"; sala.world_location = "alva_e_luz"; sala.renome = 0
        check("destino oculto aparece para o autor no payload do editor (não filtrado)",
              "destino_editor" in destinos)
        check("mesmo destino oculto some do payload de jogo (filtrado)",
              "ponto_editor" not in sala._city_points_payload()["alva_e_luz"])
    finally:
        S.WORLD_ADVENTURES.pop("destino_editor", None)
        S.WORLD_ADVENTURES.pop("destino_vazio", None)
        S.CITY_MAP_POINTS["alva_e_luz"] = antes_pontos
    reset_mundo()

    print("\n[11] Regressões apontadas na revisão")
    reset_mundo()
    # x/y de cidade criada é editável (o painel do editor expõe o campo)
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    S._aplicar_estado_cidades([dict(CIDADE_NOVA, x=88.0, y=12.0)], {}, [], None)
    check("x/y de cidade criada podem ser editados", S.WORLD_LOCATIONS["porto_negro"]["x"] == 88.0)
    # arraste no mapa-múndi das originais continua preservado no rebuild
    reset_mundo()
    S.WORLD_LOCATIONS["graciero"]["x"] = 33.3
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    check("arraste das originais preservado", S.WORLD_LOCATIONS["graciero"]["x"] == 33.3)
    # tabela de rotas vazia é recusada pelo handler (zeraria os custos originais)
    reset_mundo()
    ok_vazio, msg_vazio = S._save_world_cities_upload([], {}, [], [])
    check("tabela de rotas vazia recusada", ok_vazio is False and isinstance(msg_vazio, str))
    check("custos originais sobreviveram",
          S.WORLD_ROUTES[frozenset(("alva_e_luz", "graciero"))]["fome"] == 14)
    # arquivo ilegível bloqueia o save em vez de gravar a perda
    reset_mundo()
    with open(S.WORLD_CITIES_FILE, "w", encoding="utf-8") as f: f.write("{isto não é json")
    S._load_world_cities()
    check("arquivo corrompido marca o estado como não-carregado", S.WORLD_CITIES_OK is False)
    ok_bloq, msg_bloq = S._save_world_cities_upload([CIDADE_NOVA], {}, [],
                                                    [{"from": "alva_e_luz", "to": "porto_negro", "fome": 1, "sede": 1}])
    check("save bloqueado com arquivo corrompido", ok_bloq is False)
    S.WORLD_CITIES_OK = True
    os.remove(S.WORLD_CITIES_FILE)
    reset_mundo()

def main():
    restaurar = isolar_arquivos()
    try:
        _rodar_verificacoes()
    finally:
        restaurar()
    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
