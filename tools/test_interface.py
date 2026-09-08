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
# SÓ declarações de TOPO (coluna 0). A atribuição é pela declaração anterior mais
# próxima, então um helper indentado — `const L = (txt) => …` dentro de um render —
# virava dono dos literais da função que o contém. Medido: L/add/mkSelect/_wToggle
# levavam 51 literais que não são deles. Com a âncora, o dono é sempre a função de
# topo, que é o que o conjunto FECHADAS precisa para significar algo.
RE_FN = re.compile(
    r"^(?:async\s+)?function\s+(\w+)"
    r"|^(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(?[\w,\s]*\)?\s*=>")

# Funções cujo lote já fechou. Acrescente os nomes ao terminar cada task.
# Só funciona porque a RE_FN acima ancora na coluna 0: antes disso o "dono" podia
# ser um helper interno, e marcar `L` como fechada não impediria regressão nenhuma.
FECHADAS = {
    # Lote 2, Task 2 — tooltip, descrição e loja de item
    "gerarConteudoTooltip", "_itemDesc", "_renderShopItems",
    # Lote 2, Task 3 — ficha do herói e banners do HUD
    "renderConteudoAtributosFichaJogo", "_modificadoresTemporariosStatus",
    "renderMyPanel",
    # Lote 2, Task 4 — botões de habilidade (e as descrições de ARMADILHAS_LUCCAS,
    # que o placar atribui a _paladinSkillBtn por ser um `const` array)
    "gerarHabilidadesEspeciais", "_paladinSkillBtn", "_rogueSkillBtn",
    # Lote 2, Task 5 — popup de armadilha (handleTileClick fica de fora: sobrou
    # 1 literal que e CHAVE DE LOGICA sobre o texto de erro do servidor)
    "_showTrapResult",
    # Lote 3, Task 1 — a faixa 5-9: mapa-múndi, cenas de conversa, tooltip de
    # pergaminho, metamagia, baú/loot, ficha da cidade e modos de arremesso.
    "showWorldLocationPreview", "_adventureInfo", "showWorldMap",
    "_renderCenaConversas", "_showCenaDialogo", "renderDescricaoItem",
    "_tooltipPergaminhoHTML", "iniciarProvocacao", "_mageSkillBtn",
    "_iniciarModoMagia", "_renderChestWindow", "abrirPainelLoot",
    "renderFichaCidadeBody", "ativarHabilidadeDoMenu",
    "iniciarModoArremessoAdagaPrincipal", "iniciarModoArremessoLanca",
    # Lote 3, Task 2 — a faixa 3-4: cidade, refúgio, loja, painéis de classe,
    # mira de magia/arremesso, painel do mestre, menus, fim de jogo.
    "startGame", "_renderRefugioPainel", "_refreshCityLocation", "handleCityState",
    "openShop", "_renderSellItems", "renderConteudoAtributosPedro", "comprarItem",
    "_tooltipInstrumentoHTML", "renderMap", "renderBotoesAcaoBonus",
    "iniciarModoImposicaoMaos", "abrirPainelCriarArmadilha", "abrirPainelVenenoRapido",
    "_aliadosMortosNoRaioCleric", "iniciarModoPurificacao", "castarMagia",
    "_specAlvoMagia", "_iniciarMiraArremesso", "_mpAbaAtivo", "_mpAbaMestre",
    "abrirMenuStatus", "renderSlotsMenuMagias", "abrirMenuMagias",
    "ativarTecnicaGuildaDoMenu", "handleGameOver", "toggle3D", "_csfShowPanel",
    "_renderBannerForaMasmorra", "replaceAbilityEmoji", "_audioPanelEnsure",
    "_makeBillboardSprite",
}


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


# Um literal que CONTÉM `data-i18n` é markup, e ali o português é a FONTE que o
# _i18nApply substitui — exatamente como o GRIMORIO_CLIENT é a fonte do
# aplicarCatalogo. Não é dívida, e cobrá-lo é impossível: o dia em que o markup
# estiver 100% marcado o texto continua no arquivo. São dois casos no game.js —
# o `document.body.innerHTML` (13 KB, UM literal só) e o painel ⚙️. A garantia de
# que a exclusão não esconde trabalho real é a seção [6], que varre esses mesmos
# literais atrás de texto acentuado FORA de um elemento com data-i18n.
RE_MARKUP_I18N = re.compile(r"data-i18n")

# `console.log/warn/error` é diagnóstico para o desenvolvedor — o jogador nunca
# vê, e traduzi-lo tornaria a saída de depuração dependente do idioma. Mesma
# posição que o plano do Lote 3 registra para o gameState.js.
#
# A faixa é a CHAMADA INTEIRA, achada por parênteses casados, e não a linha do
# `console.` — a primeira versão olhava só a linha de abertura e deixava passar
# as continuações de um console.warn de 5 linhas (dois literais em
# _makeBillboardSprite). Mesma lição do tokenizador: texto dentro de código
# precisa de varredura com estado.
RE_CONSOLE = re.compile(r"console\.(?:log|warn|error|info|debug)\s*\(")


def _faixas_console():
    """[(linha_ini, linha_fim)] de cada chamada console.* do game.js."""
    faixas = []
    for m in RE_CONSOLE.finditer(GAME):
        i = GAME.index("(", m.start())
        prof, k, aspa = 0, i, None
        while k < len(GAME):
            c = GAME[k]
            if aspa:
                if c == "\\":
                    k += 2; continue
                if c == aspa:
                    aspa = None
            elif c in "'\"`":
                aspa = c
            elif c == "(":
                prof += 1
            elif c == ")":
                prof -= 1
                if prof == 0:
                    break
            k += 1
        faixas.append((GAME[:i].count("\n") + 1, GAME[:k].count("\n") + 1))
    return faixas


FAIXAS_CONSOLE = _faixas_console()


def _e_arg_de_console(linha, _txt=None):
    return any(a <= linha <= b for a, b in FAIXAS_CONSOLE)


# Literais que NUNCA se traduzem, por decisão de conteúdo — não por dívida.
# Hoje só o seletor de idioma: o nome de cada língua fica sempre na própria
# língua, e é isso que permite achá-la sem já saber ler a interface.
LITERAIS_INTENCIONAIS = {
    '<option value="pt">Português</option><option value="en">English</option>',
}


def _pendente(linha, txt):
    """A decisão, isolada para poder ser testada com entrada sintética.

    Estava embutida no laço, e o teste da regra dupla dependia de uma FRASE do
    game.js ("Personagem já escolhido") continuar sem tradução — quando o Lote 3
    a traduziu, o teste virou vermelho sem que nada estivesse errado. Um teste de
    regra não pode depender do conteúdo que a regra mede."""
    dentro = any(a <= linha <= b for a, b in FAIXAS_NAO_PENDENTES)
    if dentro and (txt in _PT_DICIONARIZADO or txt.strip() in _PT_DICIONARIZADO):
        return False
    if RE_MARKUP_I18N.search(txt):
        return False
    if txt in LITERAIS_INTENCIONAIS:
        return False
    if _e_arg_de_console(linha):
        return False
    return True


def _literais_pendentes():
    """(linha, texto) de cada literal em português que AINDA não tem tradução."""
    for linha, txt in texto_de_interface(GAME):
        if _pendente(linha, txt):
            yield linha, txt


def _literais_de_markup():
    """Os literais que a regra do data-i18n tira do placar."""
    return [(l, t) for l, t in texto_de_interface(GAME) if RE_MARKUP_I18N.search(t)]


# Texto entre tags, ignorando comentário HTML e o buraco ${} do tokenizador.
RE_NO_TEXTO = re.compile(r"<([a-zA-Z][^<>]*)>([^<>]+)")
RE_COMENT_HTML = re.compile(r"<!--.*?-->", re.S)
RE_ACENTO = re.compile(r"[ãáàâçéêíóõôúÃÁÀÂÇÉÊÍÓÕÔÚ]")
# Dentro de markup medimos LETRA, não acento — ver a nota na varredura.
RE_LETRA = re.compile(r"[A-Za-zÀ-ÿ]{2,}")


# Nome próprio do jogo — não se traduz, e aparece em duas telas.
MARKUP_INTENCIONAL = {"LEGENDS FOR HIRE"}


def _sem_blocos_html(txt):
    """Remove o elemento marcado com data-i18n-html JUNTO COM seu conteúdo.

    Nesse marcador a chave carrega o markup inteiro, então o texto de dentro é
    a FONTE — varrê-lo acusaria `Como jogar:` e `iniciar.bat` do #hint-host como
    dívida. O corte é por tag balanceada, não por regex guloso."""
    while True:
        m = re.search(r"<(\w+)[^<>]*data-i18n-html=", txt)
        if not m:
            return txt
        tag, i = m.group(1), m.start()
        prof, j = 0, i
        while j < len(txt):
            if txt.startswith("<" + tag, j):
                prof += 1
            elif txt.startswith("</" + tag, j):
                prof -= 1
                if prof == 0:
                    j = txt.find(">", j) + 1
                    break
            j += 1
        txt = txt[:i] + " " + txt[j if j > i else i + 1:]


def _markup_sem_marcador():
    """Texto acentuado dentro de markup que NÃO está sob data-i18n.

    É o contrapeso da RE_MARKUP_I18N: sem isto, bastaria um data-i18n solto num
    template para o resto dele sumir do placar."""
    fora = []
    for _linha, txt in _literais_de_markup():
        limpo = _sem_blocos_html(RE_COMENT_HTML.sub(" ", txt)).replace("${}", " ")
        for attrs, texto in RE_NO_TEXTO.findall(limpo):
            t = texto.strip()
            # ACENTO NÃO É CRITÉRIO aqui: 'Iniciar Jogo', 'Encerrar Turno',
            # 'Aventureiros', 'SALA' e 'Fechar' não têm nenhum — e todos ficaram
            # sem data-i18n até o autor relatá-los. Dentro de markup, qualquer
            # texto com letra é dívida; símbolo/número puro não é.
            if len(t) < 3 or not RE_LETRA.search(t):
                continue
            if "data-i18n" in attrs or t in MARKUP_INTENCIONAL:
                continue
            fora.append(t)
    return fora


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
    # A etapa 5 fechou: o relatório virou COBRANÇA. O único literal que
    # continua no game.js é o `'não encontrada'` de handleTileClick, que NÃO é
    # texto de tela — é chave de lógica sobre a resposta do servidor
    # (server.py:1856 devolve essa recusa como string crua, fora do T()).
    # Traduzi-la quebraria o ramo que oferece criar conta, em silêncio. O
    # conserto certo é um código de erro no payload, e é trabalho próprio.
    # A sobra que existia — o `'não encontrada'` de handleTileClick — deixou de
    # existir: o servidor passou a mandar `error_code` ("sem_conta", de
    # ERRO_LOGIN_SEM_CONTA) e o cliente decide o ramo pelo CÓDIGO, não pela
    # frase. Era o conserto que este comentário apontava como "trabalho
    # próprio"; feito, o conjunto tem de ficar VAZIO.
    SOBRA_PROPOSITAL = set()
    restantes = {txt for _l, txt in _literais_pendentes()}
    check(f"nenhum literal em português restou no game.js ({total})",
          restantes <= SOBRA_PROPOSITAL)
    check(f"nenhuma sobra proposital ({sorted(restantes) or 'ok'})",
          restantes == SOBRA_PROPOSITAL)
    # Helper interno (arrow de uma linha DENTRO de outra função) não pode virar
    # dono de literal: a atribuição é pela declaração anterior mais próxima, e
    # `L`/`add`/`mkSelect`/`_wToggle` roubavam 51 literais das funções que os
    # contêm. Sem isto o conjunto FECHADAS não significa nada — marcar `L` como
    # fechada não impede regressão nenhuma.
    internos = [fn for fn in ("L", "add", "mkSelect", "_wToggle") if fn in cont]
    check(f"nenhum helper interno é dono de literal ({internos or 'ok'})",
          not internos)

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
    # A regra é DUPLA (dicionário E faixa), e o teste dela usa entrada
    # SINTÉTICA: a versão anterior cravava uma frase do game.js que ainda não
    # tinha tradução, e ficou vermelha sozinha quando o Lote 3 a traduziu.
    _dentro = FAIXAS_NAO_PENDENTES[0][0]
    _fora = max(b for _a, b in FAIXAS_NAO_PENDENTES) + 1
    _traduzido = next(iter(_PT_DICIONARIZADO))
    check("dicionarizado FORA da faixa continua contando",
          _pendente(_fora, _traduzido))
    check("NÃO dicionarizado DENTRO da faixa continua contando",
          _pendente(_dentro, "Texto inventado que não existe no dicionário"))
    check("dicionarizado DENTRO da faixa não conta",
          not _pendente(_dentro, _traduzido))
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
    # A arte do popup de armadilha e escolhida por msg.tipo_id. Se um id do mapa
    # do cliente nao existir no ARMADILHAS do servidor, aquela armadilha aparece
    # SEM imagem — e nada acusa: nao ha erro no console e nenhum teste olha arte.
    # Foi exatamente o erro cometido ao reescrever o mapa (chutei
    # "teletransporte" onde o servidor usa "armadilha_teletransporte").
    SRV = io.open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
    _i = SRV.index("ARMADILHAS = {")
    _bloco_srv = SRV[_i:SRV.index("\n}\n", _i)]
    ids_srv = set(re.findall(r"""\n    ["'](\w+)["']\s*:\s*\{""", _bloco_srv))
    _j = GAME.index("const trapImages = {")
    _bloco_cli = GAME[_j:GAME.index("\n  };", _j)]
    ids_cli = set(re.findall(r"\n    (\w+):", _bloco_cli))
    # A tabela deixou de ser so de armadilhas: o mesmo popup serve condicoes,
    # queda, "engolido" e habilidade de monstro, e o id dessas fontes nao vive
    # em ARMADILHAS. O que a checagem protege continua sendo o id INVENTADO —
    # entao a fonte nao-armadilha vale, desde que exista no server.py.
    NAO_SAO_ARMADILHA = {
        "buraco_escondido",   # buraco procedural de sala
        "bau_armadilha",      # bau
        "sopro_dragao",       # habilidade de monstro (_usar_sopro_dragao)
    }
    for _id in NAO_SAO_ARMADILHA - {"buraco_escondido", "bau_armadilha"}:
        check(f"a fonte nao-armadilha {_id} existe no server.py",
              f'"{_id}"' in SRV or f"'{_id}'" in SRV)
    orfaos = ids_cli - ids_srv - NAO_SAO_ARMADILHA
    check(f"todo id de trapImages existe no servidor ({sorted(orfaos) or 'ok'})",
          not orfaos)
    check("o popup escolhe a arte por tipo_id, nao pelo nome",
          "trapImages[msg.tipo_id]" in GAME and "trapImages[msg.nome]" not in GAME)

    check("a chamada do GRIMORIO_CLIENT usa soNome=false",
          bool(re.search(r"aplicarCatalogo\(GRIMORIO_CLIENT,\s*false\)", GAME)))

    print("\n[6] Nenhuma chamada de t() no nível de módulo (TDZ)")
    # BUG REAL, e FATAL: um `const` de módulo inicializado com t(...) roda no
    # CARREGAMENTO, antes de `const t = …` existir — ReferenceError de temporal
    # dead zone que ABORTA o resto do game.js. Nenhuma suíte pegou: o placar
    # ficou zerado, `node --check` passou (é sintaxe válida) e o jogo simplesmente
    # não carregava. Só o console do navegador acusou. Aconteceu com o
    # GUERREIRO_LUZ_BONUS_CLIENT no Lote 3.
    # A varredura é ancorada na COLUNA 0 — a mesma premissa da RE_FN e do
    # placar: uma declaração de módulo começa ali. Uma primeira versão contava
    # chaves para achar "profundidade 0" e derivou no meio do arquivo (template
    # literal com `${}` aninhado); regra simples e ancorada erra menos.
    RE_DECL = re.compile(r"^(?:const|let|var)\s")
    RE_CHAMA_T = re.compile(r"(?<![\w$.])t\(\s*['\"]")
    ini_t = next((i for i, l in enumerate(LINHAS, 1)
                  if l.startswith("const t = (chave")), None)
    check("o `const t` do tradutor foi encontrado", ini_t is not None)
    cedo, i = [], 0
    while i < len(LINHAS):
        if RE_DECL.match(LINHAS[i]):
            j, trecho = i, [LINHAS[i]]
            # A declaração segue até a próxima linha que abre coluna 0 de novo.
            while j + 1 < len(LINHAS) and not LINHAS[j + 1][:1].strip():
                j += 1; trecho.append(LINHAS[j])
            texto = "\n".join(trecho)
            if RE_CHAMA_T.search(texto) and (ini_t is None or i + 1 < ini_t):
                cedo.append(i + 1)
            i = j
        i += 1
    check(f"nenhum t() de módulo antes da declaração (linhas {cedo or 'ok'})", not cedo)

    # A varredura acima só olha DECLARAÇÃO (`const|let|var` na coluna 0), e foi
    # por esse buraco que o bug passou a segunda vez: a chamada estava dentro de
    # um IIFE de topo — `(function(){ … })();` —, que não casa com RE_DECL.
    # Pior, o corpo era guardado por `if(!s || !s.code) return;`, então só
    # quebrava DEPOIS da primeira partida (com sessão salva no localStorage): a
    # tela inicial desenhava, nenhum handler existia e o jogo travava na
    # seleção de herói, sem erro visível para quem não abre o console.
    #
    # Em vez de ensinar a varredura a entender IIFE, aninhamento e callback —
    # regra cada vez mais frágil —, o invariante virou ESTRUTURAL: o `const t`
    # mora no topo do arquivo, antes de qualquer código de módulo. Assim nenhuma
    # chamada pode precedê-lo, e a checagem não depende de adivinhar o que roda
    # no carregamento. Este teste guarda essa posição.
    primeiro_codigo = next(
        (i for i, l in enumerate(LINHAS, 1)
         # Primeira linha de topo que não é comentário, diretiva ou vazia.
         if l[:1].strip()
         and not l.startswith(("//", "/*", " ", "*", "'use strict'"))),
        None)
    check("o `const t` é a PRIMEIRA linha de código do módulo "
          f"(t={ini_t}, 1º código={primeiro_codigo})",
          ini_t is not None and ini_t == primeiro_codigo)

    print("\n[7] O markup com data-i18n está TODO marcado")
    # Contrapeso da RE_MARKUP_I18N: aquele filtro tira do placar o literal que
    # contém data-i18n, e o `document.body.innerHTML` é UM literal de 13 KB —
    # sem esta varredura, um único marcador esconderia o template inteiro.
    markup = _literais_de_markup()
    check(f"os literais de markup foram encontrados ({len(markup)})", len(markup) >= 2)
    fora = _markup_sem_marcador()
    check(f"nenhum texto acentuado fora de data-i18n ({fora[:4] or 'ok'})", not fora)
    # E a exclusão do console não pode virar porta dos fundos: as faixas são as
    # chamadas em si, então uma linha de render qualquer não pode cair nelas.
    check(f"as faixas de console foram achadas ({len(FAIXAS_CONSOLE)})",
          len(FAIXAS_CONSOLE) > 5)
    check("nenhuma faixa de console engole uma função inteira",
          all(b - a < 12 for a, b in FAIXAS_CONSOLE))
    check("a linha 1 do arquivo não é console", not _e_arg_de_console(1))
    check(f"os literais intencionais ainda existem no game.js",
          all(x in GAME for x in LITERAIS_INTENCIONAIS))


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Interface do cliente (etapa 5)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
