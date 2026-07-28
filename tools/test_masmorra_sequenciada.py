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

async def main():
    test_helpers_etapa()
    test_persistencia_campos()
    test_validacao_saida()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
