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

sys.path.insert(0, RAIZ)
import server as S   # só pelo LANG_STRINGS: é ele que sabe fundir os src/lang/*.js

GAME = io.open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()
LINHAS = GAME.split("\n")
RE_FN = re.compile(
    r"^\s*(?:async\s+)?function\s+(\w+)"
    r"|^\s*(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(?[\w,\s]*\)?\s*=>")

# Funções cujo lote já fechou. Acrescente os nomes ao terminar cada lote.
FECHADAS = set()


# Blocos cujo literal em português NÃO é trabalho pendente:
#   • GRIMORIO_CLIENT / ARMADILHAS_LUCCAS — catálogos ESTÁTICOS do cliente,
#     traduzidos EM CIMA pelo I18N.aplicarCatalogo (que muta o objeto). A string
#     em português tem de continuar aqui para haver o que trocar: é a FONTE.
#   • ABILITY_NAME_TO_ID — chave de LÓGICA, que o plano registra como
#     intraduzível; a etapa 5.0 já a tornou dispensável para o ícone.
BLOCOS_NAO_PENDENTES = ("GRIMORIO_CLIENT", "ARMADILHAS_LUCCAS", "ABILITY_NAME_TO_ID")


def _faixas_nao_pendentes():
    """[(linha_ini, linha_fim)] dos blocos acima, por casamento de chaves."""
    faixas = []
    for nome in BLOCOS_NAO_PENDENTES:
        i = GAME.find("const " + nome)
        if i < 0:
            continue
        # ARMADILHAS_LUCCAS é um ARRAY e os outros dois são objetos: casar só
        # `{` pegava o primeiro elemento do array e fechava na mesma linha.
        cand = [p for p in (GAME.find("{", i), GAME.find("[", i)) if p >= 0]
        a = min(cand)
        abre, fecha = ("[", "]") if GAME[a] == "[" else ("{", "}")
        prof, k = 0, a
        while k < len(GAME):
            if GAME[k] == abre:
                prof += 1
            elif GAME[k] == fecha:
                prof -= 1
                if prof == 0:
                    break
            k += 1
        faixas.append((GAME[:a].count("\n") + 1, GAME[:k].count("\n") + 1))
    return faixas


FAIXAS_NAO_PENDENTES = _faixas_nao_pendentes()


def _pt_dicionarizado():
    """Os `pt` das chaves cat.* e ui.* — o texto que JÁ tem tradução.

    POR QUE ISTO EXISTE: o aplicarCatalogo traduz MUTANDO o objeto, então a
    string em português precisa continuar no game.js para haver o que trocar.
    Ela é a FONTE, não é dívida — mas o tokenizador não distingue as duas
    coisas, e contava 38 textos do GRIMORIO_CLIENT já traduzidos desde a etapa
    3. Sem isto, o lote 1 tem um teto que nada fura.

    RESTRITO A `cat.` E `ui.` de propósito — as duas famílias que o
    aplicarCatalogo e o _rotulo usam. Incluir `erro.`/`narracao.` faria uma
    frase do cliente que por acaso coincida com uma do servidor sumir do placar,
    mascarando trabalho real dos lotes 2 e 3.

    E NÃO BASTA o texto estar no dicionário: ele também precisa estar num dos
    BLOCOS_NAO_PENDENTES. A primeira versão desta regra exigia só o casamento de
    texto e produziu falsos positivos MEDIDOS — o item `cat.item.cleanse.nome`
    ("Purificação") apagava do placar a HABILIDADE de mesmo nome, e as chaves
    ui.selecao.skill.* apagavam ocorrências fora do _CSD que são trabalho dos
    lotes 2 e 3. Exigir os dois é o que separa "já traduzido" de "coincidência".

    A exigência dupla também protege o futuro: um campo novo, ainda sem chave,
    acrescentado DENTRO de um desses blocos continua contando."""
    out = set()
    for chave, val in S.LANG_STRINGS.items():
        if not (chave.startswith("cat.") or chave.startswith("ui.")):
            continue
        pt = (val or {}).get("pt")
        if isinstance(pt, str) and pt:
            out.add(pt)
            out.add(pt.strip())
    return out


_PT_DICIONARIZADO = _pt_dicionarizado()


def _literais_pendentes():
    """(linha, texto) de cada literal em português que AINDA não tem tradução."""
    for linha, txt in texto_de_interface(GAME):
        dentro = any(a <= linha <= b for a, b in FAIXAS_NAO_PENDENTES)
        if dentro and (txt in _PT_DICIONARIZADO or txt.strip() in _PT_DICIONARIZADO):
            continue
        yield linha, txt


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
    for linha, _txt in _literais_pendentes():
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

    print("\n[4] O placar não conta o pt que o aplicarCatalogo já traduz")
    # O aplicarCatalogo traduz MUTANDO o objeto: para haver o que trocar, a
    # string em português tem de continuar no game.js. Ela é a FONTE, não é
    # dívida — mas o tokenizador não sabe disso. 'Bola de Fogo' é o caso
    # canônico: está em cat.magia.bola_fogo.nome e é traduzido desde a etapa 3.
    contados = {txt for _l, txt in _literais_pendentes()}
    check("o dicionário foi carregado", len(_PT_DICIONARIZADO) > 100)
    check("um nome já traduzido não conta ('Bola de Fogo')",
          "Bola de Fogo" not in contados)
    check("texto NÃO dicionarizado continua contando",
          any("Personagem já escolhido" in t for t in contados))
    # Uma faixa que não fecha direito FALHA EM SILÊNCIO: vira uma linha só e o
    # bloco volta a contar inteiro, sem erro nenhum. Já aconteceu —
    # ARMADILHAS_LUCCAS é um ARRAY, e o casador que só via `{` fechava no
    # primeiro elemento.
    check(f"as {len(BLOCOS_NAO_PENDENTES)} faixas foram encontradas",
          len(FAIXAS_NAO_PENDENTES) == len(BLOCOS_NAO_PENDENTES))
    check("nenhuma faixa degenerou para uma linha",
          all(b - a >= 5 for a, b in FAIXAS_NAO_PENDENTES))
    # Não dá para provar isso por TEXTO: vários desses nomes aparecem também
    # fora do bloco, e essas ocorrências contam com razão (são dos lotes 2 e 3).
    # O que prova é a faixa estar excluindo alguma coisa — faixa degenerada
    # exclui zero.
    pend = collections.Counter(_literais_pendentes())
    todos = collections.Counter(texto_de_interface(GAME))
    excluidos = todos - pend          # multiconjunto: exato, não por linha
    for nome, (a, b) in zip(BLOCOS_NAO_PENDENTES, FAIXAS_NAO_PENDENTES):
        n = sum(c for (l, _t), c in excluidos.items() if a <= l <= b)
        check(f"a faixa de {nome} exclui {n} literal(is)", n > 0)

    print("\n[5] As estruturas do Lote 1 continuam sem texto")
    # POR QUE NÃO É `FECHADAS`: aquele conjunto guarda FUNÇÕES, e funcionava
    # enquanto um lote fechasse funções inteiras. O Lote 1 foi escopado por
    # ESTRUTURA — tirado o texto dos catálogos, o que sobra nos mesmos buckets é
    # render dos lotes 2 e 3 (`_mageSkillBtn` ainda tem 7, `_csfShowPanel` 3).
    # A invariante que este lote de fato estabeleceu é estrutural, e é essa que
    # se guarda aqui.
    for mapa in ("_OBJ_LABELS", "_TIPO_ITEM_LABEL", "_MP_CUSTO_LBL",
                 "_ELEMENTAL_HABILIDADES_LEWIS"):
        check(f"o mapa {mapa} não voltou", ("const " + mapa) not in GAME)

    def _bloco(nome):
        i = GAME.find("const " + nome)
        if i < 0:
            return ""
        cand = [p for p in (GAME.find("{", i), GAME.find("[", i)) if p >= 0]
        a = min(cand)
        abre, fecha = ("[", "]") if GAME[a] == "[" else ("{", "}")
        prof, k = 0, a
        while k < len(GAME):
            if GAME[k] == abre:
                prof += 1
            elif GAME[k] == fecha:
                prof -= 1
                if prof == 0:
                    break
            k += 1
        return GAME[a:k + 1]

    csd = _bloco("_CSD")
    check("o _CSD não tem texto solto",
          bool(csd) and not re.search(r"(?:name|nome|cls|desc):\s*'", csd))
    # O `bool(bloco)` em cada uma NÃO é decoração: sem ele, um _bloco() que não
    # achasse a estrutura devolveria "" e a checagem passaria À TOA — a mesma
    # armadilha do `indexOf` de algo ausente ser -1.
    grim = _bloco("GRIMORIO_CLIENT")
    check("o GRIMORIO_CLIENT não tem `resumo` (campo morto)",
          bool(grim) and "resumo:" not in grim)
    hero = _bloco("HERO_DATA")
    check("o HERO_DATA não tem `class` nem texto em habilidadeClasse",
          bool(hero) and "class:" not in hero
          and not re.search(r"(?:alcance|descricao):\s*'", hero))
    check("a chamada do GRIMORIO_CLIENT usa soNome=false",
          bool(re.search(r"aplicarCatalogo\(GRIMORIO_CLIENT,\s*false\)", GAME)))


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Interface do cliente (etapa 5)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
