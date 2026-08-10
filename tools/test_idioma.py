"""Motor de idioma (PT/EN) — dicionário único, objeto T e tradução por conexão.
Roda da raiz: python tools/test_idioma.py"""
import asyncio, json, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")


def _rodar_verificacoes():
    print("\n[1] Carregamento do dicionário")
    check("LANG_STRINGS carregou do disco", isinstance(S.LANG_STRINGS, dict) and len(S.LANG_STRINGS) > 0)
    check("chave da amostra existe", "narracao.abre_porta" in S.LANG_STRINGS)
    check("chave tem pt e en",
          set(S.LANG_STRINGS["narracao.abre_porta"]) >= {"pt", "en"})
    # Dicionário ilegível não pode impedir o servidor de subir: o jogo segue
    # inteiro em português, que é exatamente o estado de hoje.
    original = S.LANG_FILE
    S.LANG_FILE = os.path.join(os.path.dirname(original), "_nao_existe_.js")
    try:
        vazio = S._load_lang()
        check("arquivo ausente devolve dicionário vazio em vez de estourar", vazio == {})
    finally:
        S.LANG_FILE = original
    check("recarregar do arquivo real volta a funcionar",
          "narracao.abre_porta" in S._load_lang())

    print("\n[2] t() — tradução, fallback e chave ausente")
    check("t() devolve português", S.t("erro.porta_longe", "pt") == "Aproxime-se da porta para abri-la.")
    check("t() devolve inglês", S.t("erro.porta_longe", "en") == "Get closer to the door to open it.")
    S.LANG_STRINGS["_teste.so_pt"] = {"pt": "só em português"}
    check("falta 'en' → cai no português", S.t("_teste.so_pt", "en") == "só em português")
    check("chave inexistente devolve a própria chave", S.t("_teste.nao_existe", "en") == "_teste.nao_existe")
    check("idioma desconhecido cai no português", S.t("erro.porta_longe", "xx") == "Aproxime-se da porta para abri-la.")
    S.LANG_STRINGS.pop("_teste.so_pt", None)

    print("\n[3] Parâmetros {nome}")
    check("substitui por nome (pt)",
          S.t("narracao.abre_porta", "pt", nome="Thorin") == "🚪 **Thorin** abre uma porta!")
    check("substitui por nome (en)",
          S.t("narracao.abre_porta", "en", nome="Thorin") == "🚪 **Thorin** opens a door!")
    check("parâmetro que falta fica visível e não estoura",
          S.t("narracao.abre_porta", "pt") == "🚪 **{nome}** abre uma porta!")

    print("\n[4] Objeto T")
    marcado = S.T("narracao.abre_porta", nome="Lyra")
    check("T guarda a chave", marcado.key == "narracao.abre_porta")
    check("T guarda os parâmetros", marcado.params == {"nome": "Lyra"})
    check("T rende no idioma pedido", S._t_render(marcado, "en") == "🚪 **Lyra** opens a door!")


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Motor de idioma (PT/EN)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
