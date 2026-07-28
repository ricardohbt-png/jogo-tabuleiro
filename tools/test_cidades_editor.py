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

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
