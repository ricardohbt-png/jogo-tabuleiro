"""Editor de cidades — criar, editar e excluir cidades pelo editor.
  • _aplicar_estado_cidades monta WORLD_LOCATIONS a partir das originais + edições.
  • Cidade nova nasce vazia (sem lojas, sem pontos de mapa, sem NPCs de taverna).
  • Rota sem custo definido = viagem grátis; par com custo debita o valor.
  • Excluir limpa os subsistemas derivados; Alva e Luz nunca é excluída.
Roda da raiz: python tools/test_cidades_editor.py"""
import asyncio, json, os, sys, tempfile
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

def reset_mundo():
    """Volta o mundo às 4 cidades originais, sem nenhuma edição do editor."""
    S._aplicar_estado_cidades([], {}, [], None)
    S._sincronizar_cidades_derivadas()

def main():
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
        ok, payload = S._save_world_cities_upload([CIDADE_NOVA], {}, [], [])
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
            S._save_world_cities_upload([], {}, [], [])
            check("sala em cidade excluída volta para Alva e Luz",
                  sala2.world_location == "alva_e_luz")
        finally:
            S.rooms.pop("TEST2", None)
    finally:
        S.WORLD_CITIES_FILE = original_file
        if os.path.exists(tmp2): os.remove(tmp2)
        reset_mundo()

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
