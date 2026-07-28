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
    arquivos = ("WORLD_CITIES_FILE", "CITY_SHOPS_FILE", "TAVERN_SCENES_FILE", "CITY_MAP_POINTS_FILE")
    originais = {nome: getattr(S, nome) for nome in arquivos}
    for nome in arquivos:
        setattr(S, nome, os.path.join(tmpdir, nome.lower() + ".json"))
    inicial = {"shops": deepcopy(S.CITY_SHOPS), "points": deepcopy(S.CITY_MAP_POINTS),
               "taverns": deepcopy(S.TAVERN_SCENES), "cities": deepcopy(S.WORLD_CITIES),
               "locations": deepcopy(S.WORLD_LOCATIONS), "routes": dict(S.WORLD_ROUTES)}

    def restaurar():
        for nome, valor in originais.items():
            setattr(S, nome, valor)
        for alvo, copia in ((S.CITY_SHOPS, inicial["shops"]), (S.CITY_MAP_POINTS, inicial["points"]),
                            (S.TAVERN_SCENES, inicial["taverns"]), (S.WORLD_LOCATIONS, inicial["locations"]),
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
    check("sem pontos no mapa da cidade", S.CITY_MAP_POINTS.get("porto_negro") == {})
    cena = S.TAVERN_SCENES.get("porto_negro") or {}
    check("cena de taverna existe", isinstance(cena.get("slots"), list))
    check("taverna sem NPCs copiados de Alva e Luz", cena.get("slots") == [])
    check("taverna sem fundo", not cena.get("background"))
    check("Alva e Luz mantém seus NPCs",
          len((S.TAVERN_SCENES.get("alva_e_luz") or {}).get("slots") or []) >= 8)
    S._aplicar_estado_cidades([], {}, [], None)
    S._sincronizar_cidades_derivadas()
    check("excluir limpa lojas", "porto_negro" not in S.CITY_SHOPS)
    check("excluir limpa pontos", "porto_negro" not in S.CITY_MAP_POINTS)
    check("excluir limpa taverna", "porto_negro" not in S.TAVERN_SCENES)

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
