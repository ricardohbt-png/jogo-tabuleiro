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


class RecWS:
    """WebSocket falso que guarda o JSON cru enviado — é ele que prova que os
    dois jogadores receberam a MESMA mensagem em idiomas diferentes."""
    def __init__(self): self.sent = []
    async def send(self, data): self.sent.append(data)

def _sala_dois_idiomas():
    """Sala com dois jogadores conectados: p1 em português, p2 em inglês."""
    r = S.GameRoom("TEST")
    ws_pt, ws_en = RecWS(), RecWS()
    r.connections = {"pid_pt": ws_pt, "pid_en": ws_en}
    S.LANG_BY_PID["pid_pt"] = "pt"
    S.LANG_BY_PID["pid_en"] = "en"
    return r, ws_pt, ws_en

def _limpar_idiomas():
    for pid in ("pid_pt", "pid_en"):
        S.LANG_BY_PID.pop(pid, None)


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

    # Comentário com chaves literais antes da atribuição não pode confundir o
    # recorte — na etapa 2 este arquivo ganha comentários de seção.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        falso = os.path.join(tmp, "strings.js")
        with open(falso, "w", encoding="utf-8") as f:
            f.write('// cabeçalho com { e } literais\nwindow.LANG_STRINGS = {"a.b": {"pt": "ok"}};\n')
        original2 = S.LANG_FILE
        S.LANG_FILE = falso
        try:
            check("chave literal no comentário não confunde o recorte",
                  S._load_lang() == {"a.b": {"pt": "ok"}})
        finally:
            S.LANG_FILE = original2

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

    print("\n[5] broadcast traduz por conexão")
    sala, ws_pt, ws_en = _sala_dois_idiomas()
    asyncio.run(sala.gm_say(S.T("narracao.abre_porta", nome="Thorin")))
    texto_pt = json.loads(ws_pt.sent[-1])["text"]
    texto_en = json.loads(ws_en.sent[-1])["text"]
    check("jogador em pt recebe português", texto_pt == "🚪 **Thorin** abre uma porta!")
    check("jogador em en recebe inglês",   texto_en == "🚪 **Thorin** opens a door!")
    check("a MESMA narração chegou nos dois idiomas", texto_pt != texto_en)

    print("\n[6] send_to traduz para um jogador só")
    asyncio.run(sala.send_to("pid_en", {"type": "error", "msg": S.T("erro.porta_longe")}))
    check("erro sai em inglês para quem está em inglês",
          json.loads(ws_en.sent[-1])["msg"] == "Get closer to the door to open it.")

    print("\n[7] Sem set_lang → português")
    sala2 = S.GameRoom("TEST2")
    ws_mudo = RecWS()
    sala2.connections = {"pid_sem_lang": ws_mudo}
    asyncio.run(sala2.gm_say(S.T("narracao.abre_porta", nome="Anon")))
    check("conexão que nunca mandou set_lang recebe português",
          json.loads(ws_mudo.sent[-1])["text"] == "🚪 **Anon** abre uma porta!")

    print("\n[8] String crua continua saindo igual")
    asyncio.run(sala.gm_say("texto legado sem chave"))
    check("string crua sai idêntica em pt", json.loads(ws_pt.sent[-1])["text"] == "texto legado sem chave")
    check("string crua sai idêntica em en", json.loads(ws_en.sent[-1])["text"] == "texto legado sem chave")
    _limpar_idiomas()

    print("\n[9] Validação do idioma recebido")
    check("idioma suportado é aceito", S._lang_valido("en") == "en")
    check("idioma desconhecido vira português", S._lang_valido("klingon") == "pt")
    check("valor não-string vira português", S._lang_valido(42) == "pt")
    check("None vira português", S._lang_valido(None) == "pt")

    print("\n[10] Varredura estática: toda chave usada em T(...) existe no dicionário")
    fonte = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "server.py"), encoding="utf-8").read()
    usadas = set(re.findall(r'\bT\(\s*"([^"]+)"', fonte))
    faltando = sorted(k for k in usadas if k not in S.LANG_STRINGS)
    check(f"nenhuma chave órfã em server.py (usadas: {len(usadas)})", not faltando)
    if faltando: print("     órfãs:", ", ".join(faltando))

    print("\n[11] Amostra migrada de verdade")
    check("a narração da porta usa T", 'T("narracao.abre_porta"' in fonte)
    check("o erro da porta usa T", 'T("erro.porta_longe")' in fonte)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Motor de idioma (PT/EN)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
