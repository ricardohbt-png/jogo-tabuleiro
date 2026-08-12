"""Narração do servidor (etapa 4b-i) — migração para T() e tradução.
Roda da raiz: python tools/test_narracao.py"""
import io, json, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

FONTE = io.open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
# EXATAMENTE o mesmo padrão que o script de migração reconhece. Se o teste
# cobrisse mais do que o script sabe fazer, ficaria vermelho por trabalho que
# ninguém combinou.
RE_UMA_LINHA = re.compile(r'gm_say\((f?)"([^"]*)"\)')


def _rodar_verificacoes():
    print("\n[1] Dicionário de narração carregado")
    check("existe src/lang/narracao.js",
          os.path.isfile(os.path.join(RAIZ, "src", "lang", "narracao.js")))
    check("o servidor funde as chaves de narração",
          any(k.startswith("narracao.") for k in S.LANG_STRINGS))

    print("\n[2] Migração do lote mecânico")
    restantes = RE_UMA_LINHA.findall(FONTE)
    check(f"nenhum gm_say de uma linha com literal sobrou ({len(restantes)})",
          not restantes)
    for _, t in restantes[:6]:
        print("     sobrou:", t[:70])

    print("\n[3] Fora de escopo — contagem, não cobrança")
    # Estes seguem em português de propósito; são a etapa 4b-ii. O teste os
    # RELATA para o placar ficar visível, e nunca falha por causa deles.
    linhas = FONTE.split("\n")
    multi = sum(1 for l in linhas
                if l.strip().endswith("gm_say(") and "async def" not in l)
    pool = len(re.findall(r"gm_say\(gm\(", FONTE))
    conc = sum(1 for l in linhas if "gm_say(" in l and "+" in l
               and not re.search(r'gm_say\((f?"|T\()', l) and "async def" not in l)
    print(f"     multilinha: {multi} | pool gm(): {pool} | concatenação: {conc}")
    check("relatório de fora-de-escopo emitido", True)

    print("\n[4] Chaves usadas e chaves sem uso")
    usadas = set(re.findall(r'T\(\s*"(narracao\.[^"]+)"', FONTE))
    faltando = sorted(k for k in usadas if k not in S.LANG_STRINGS)
    check(f"nenhuma chave de narração órfã (usadas: {len(usadas)})", not faltando)
    if faltando:
        print("     órfãs:", ", ".join(faltando[:8]))
    no_dic = {k for k in S.LANG_STRINGS if k.startswith("narracao.")}
    sem_uso = sorted(no_dic - usadas)
    check(f"relatório de chaves sem uso emitido ({len(sem_uso)})", True)
    if sem_uso:
        print("     sem uso:", ", ".join(sem_uso[:8]))

    print("\n[5] Uma narração migrada chega em dois idiomas, pelo broadcast real")
    import asyncio

    class RecWS:
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    chave = next((k for k, v in S.LANG_STRINGS.items()
                  if k.startswith("narracao.") and v.get("en")), None)
    if not chave:
        check("há ao menos uma narração traduzida para provar", False)
    else:
        sala = S.GameRoom("TESTE_NARR")
        ws_pt, ws_en = RecWS(), RecWS()
        sala.connections = {"n_pt": ws_pt, "n_en": ws_en}
        S.LANG_BY_PID["n_pt"] = "pt"
        S.LANG_BY_PID["n_en"] = "en"
        asyncio.run(sala.gm_say(S.T(chave)))
        pt = json.loads(ws_pt.sent[-1])["text"]
        en = json.loads(ws_en.sent[-1])["text"]
        check("sai em português para quem está em pt", pt == S.LANG_STRINGS[chave]["pt"])
        check("sai em inglês para quem está em en", en == S.LANG_STRINGS[chave]["en"])
        for pid in ("n_pt", "n_en"):
            S.LANG_BY_PID.pop(pid, None)

    print("\n[6] Nomes de catálogo dentro da frase")

    def _r(x, lang):
        """Renderiza como o json.dumps faria para uma conexão naquele idioma."""
        return S.t(x.key, lang, **x.params) if isinstance(x, S.T) else str(x)

    # Monstro NATIVO: traduz.
    orc_pt = S.LANG_STRINGS["cat.monstro.orc.nome"]["pt"]
    orc = {"type": "orc", "name": orc_pt}
    check("monstro nativo usa o en do catálogo",
          _r(S.nome_criatura(orc), "en") == S.LANG_STRINGS["cat.monstro.orc.nome"]["en"])
    check("monstro nativo em pt continua igual", _r(S.nome_criatura(orc), "pt") == orc_pt)

    # Monstro AUTORAL: sem chave → sai cru, nos dois idiomas.
    autoral = {"type": "soldado_do_autor", "name": "Soldado do Autor"}
    check("monstro autoral sai cru", _r(S.nome_criatura(autoral), "en") == "Soldado do Autor")

    # Nativo RENOMEADO no editor: tem chave, mas o nome não bate → sai cru.
    renomeado = {"type": "orc", "name": "Orc Veterano de Khaz"}
    check("nativo renomeado preserva o nome do autor",
          _r(S.nome_criatura(renomeado), "en") == "Orc Veterano de Khaz")

    # Jogador: nunca traduz, mesmo com nome igual ao de um monstro.
    check("nome de jogador nunca é traduzido",
          _r(S.nome_criatura({"class_id": "warrior", "name": orc_pt}), "en") == orc_pt)

    # Item nativo. Sem `if`: se o id sumir do catálogo, o teste tem de ficar
    # vermelho — um `if item:` silencioso já deixou esta checagem sem rodar.
    antid = next(i for i in S.SHOP_MERCHANT if i["id"] == "antidote")
    check("item nativo traduz",
          _r(S.nome_item(dict(antid)), "en") == S.LANG_STRINGS["cat.item.antidote.nome"]["en"])
    # Item autoral (id que não existe no catálogo) sai cru.
    check("item autoral sai cru",
          _r(S.nome_item({"id": "espada_do_autor", "name": "Espada do Autor"}), "en")
          == "Espada do Autor")


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Narração do servidor (etapa 4b-i)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
