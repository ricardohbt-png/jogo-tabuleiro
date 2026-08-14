"""Interface do cliente (etapa 5) — placar por função.
Roda da raiz: python tools/test_interface.py

Enquanto uma função não é traduzida, este teste RELATA quantos literais em
português ela ainda tem. Quando um lote fecha, acrescente os nomes das funções
a FECHADAS e o teste passa a falhar se algum literal voltar. É o mesmo padrão da
seção [3] do test_narracao.py, que começou como relatório e virou cobrança.

POR QUE POR FUNÇÃO, E NÃO POR TELA: a primeira versão deste arquivo classificava
por FAIXA DE LINHAS entre marcos de render, assumindo que o game.js fosse
organizado por tela. Não é — são 26 mil linhas e 172 funções com literais, e as
funções de telas diferentes se intercalam. Pior: as maiores são COMPARTILHADAS
(`_itemDesc` descreve item na ficha, na loja e no baú; `gerarConteudoTooltip`
serve qualquer tela), então os literais não particionam por tela. A medição por
faixa dizia "seleção de herói: 58" quando o número real é 5."""
import io, os, re, sys, collections
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
from js_strings import texto_de_interface

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

GAME = io.open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()
LINHAS = GAME.split("\n")
RE_FN = re.compile(
    r"^\s*(?:async\s+)?function\s+(\w+)"
    r"|^\s*(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(?[\w,\s]*\)?\s*=>")

# Funções cujo lote já fechou. Acrescente os nomes ao terminar cada lote.
FECHADAS = set()


def _por_funcao():
    """{nome_da_funcao: n_textos_em_portugues}.

    A contagem vem do tokenizador (tools/js_strings.py), NÃO de regex por linha:
    regex ignora template literal multilinha, e são 75 deles no game.js — um com
    13 KB. A medição por linha dizia 636 quando o número real é 707."""
    dono, atual = {}, None
    for i, l in enumerate(LINHAS):
        m = RE_FN.match(l)
        if m: atual = m.group(1) or m.group(2)
        dono[i + 1] = atual
    cont = collections.Counter()
    for linha, _txt in texto_de_interface(GAME):
        cont[dono.get(linha) or "@topo_do_arquivo"] += 1
    return cont


def _rodar_verificacoes():
    print("\n[1] Placar por função")
    cont = _por_funcao()
    total = sum(cont.values())
    print(f"     {len(cont)} funções com literal em português | total {total}")
    print("     as 15 maiores:")
    for fn, n in cont.most_common(15):
        marca = " (FECHADA)" if fn in FECHADAS else ""
        print(f"       {n:>4}  {fn}{marca}")
    check("placar emitido", True)

    print("\n[2] Funções já traduzidas continuam limpas")
    if not FECHADAS:
        check("nenhum lote fechado ainda (fundação)", True)
    sujas = sorted((fn, cont[fn]) for fn in FECHADAS if cont.get(fn))
    check(f"nenhuma função fechada regrediu ({len(FECHADAS)} fechadas)", not sujas)
    for fn, n in sujas[:8]:
        print(f"     REGREDIU: {fn} tem {n} literal(is)")

    print("\n[3] A fiação da fundação existe")
    # `MutationObserver in GAME` sozinho passa pelo motivo ERRADO: já havia um
    # observador para os ícones de habilidade antes desta etapa. O que se
    # verifica é que ele também aplica o i18n.
    check("o observador do body também aplica _i18nApply",
          bool(re.search(r"new MutationObserver\([\s\S]{0,600}?_i18nApply", GAME)))
    check("continua havendo UM observador do body, não dois",
          len(re.findall(r"observe\(\s*document\.body", GAME)) == 1)
    check("o ícone de habilidade é achado por data-ability-id",
          "data-ability-id" in GAME and "dataset.abilityId" in GAME)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Interface do cliente (etapa 5)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
