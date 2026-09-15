"""Extrai literais de string de um fonte JavaScript, com estado.

Roda o autoteste da raiz:  python tools/js_strings.py

POR QUE ISTO EXISTE: medir texto em JS com regex falhou três vezes seguidas na
etapa 5 — contagem por faixa de linhas, atribuição por função, e por fim a
contagem por linha, que ignora template literal multilinha e por isso reportava
636 quando o número é maior. É a mesma lição que o servidor já tinha aprendido
na 4b-ii, quando o migrador trocou regex por `ast`: **texto dentro de código
precisa de varredura com estado, não de padrão**.

Não é um parser: é um tokenizador que sabe onde COMEÇA e onde TERMINA cada
string, e o que é comentário. Isso basta para contar e localizar texto, e não
custa dependência nenhuma — o projeto é vanilla, sem bundler.

O que trata:
  • 'aspas simples' e "duplas", com escape (\\' \\" \\\\)
  • `template`, inclusive MULTILINHA
  • ${...} dentro de template: a expressão é código, não texto — o conteúdo é
    pulado (com aninhamento), e o texto ao redor continua sendo string
  • // linha e /* bloco */
O que NÃO trata: literal de expressão regular (/.../), que pode ser confundido
com divisão sem análise sintática. Na prática não gera falso positivo aqui
porque só se conta trecho COM ACENTO, e regex acentuada não existe no game.js.
"""
import io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass


# Um `/` começa uma EXPRESSÃO REGULAR quando o último token significativo antes
# dele não pode terminar um valor. Depois de identificador, número, `)`, `]` ou
# `++/--`, o `/` é divisão. É a heurística clássica, e basta aqui: o que precisa
# ser acertado é só onde a regex TERMINA, para as aspas de dentro não abrirem
# uma string fantasma.
_ANTES_DE_REGEX = set("(,=:[!&|?{};+-*%~^<>") | {""}
_PALAVRAS_ANTES_DE_REGEX = {
    "return", "typeof", "instanceof", "in", "of", "new", "delete", "void",
    "case", "do", "else", "yield", "await", "throw",
}


def _inicia_regex(src, i):
    """True se o `/` em `src[i]` abre um literal de regex, não uma divisão."""
    j = i - 1
    while j >= 0 and src[j] in " \t\r\n":
        j -= 1
    if j < 0:
        return True
    c = src[j]
    if c in _ANTES_DE_REGEX:
        return True
    if c.isalnum() or c in "_$)]":
        # pode ser palavra-chave (return /re/) ou fim de valor (a / b)
        k = j
        while k >= 0 and (src[k].isalnum() or src[k] in "_$"):
            k -= 1
        return src[k + 1:j + 1] in _PALAVRAS_ANTES_DE_REGEX
    return False


def _fim_regex(src, i):
    """Índice logo após o literal de regex que começa em `src[i]` (com as
    flags), ou None se o trecho não fecha como regex nesta linha."""
    n = len(src)
    j, classe = i + 1, False
    while j < n:
        d = src[j]
        if d == "\\": j += 2; continue
        if d == "\n": return None          # regex não atravessa linha
        if d == "[": classe = True
        elif d == "]": classe = False
        elif d == "/" and not classe:
            j += 1
            while j < n and src[j].isalpha(): j += 1   # flags
            return j if j > i + 1 else None
        j += 1
    return None


def _fim_string(src, i):
    """Índice logo após a string simples que abre em `src[i]` (' ou ")."""
    q, n, j = src[i], len(src), i + 1
    while j < n:
        if src[j] == "\\": j += 2; continue
        if src[j] == q: return j + 1
        j += 1
    return n


def _fim_template(src, i):
    """Índice logo após o template que abre em `src[i]` (crase), pulando os
    `${}` de dentro com `_fim_expr` — que por sua vez pula templates aninhados."""
    n, j = len(src), i + 1
    while j < n:
        d = src[j]
        if d == "\\": j += 2; continue
        if d == "`": return j + 1
        if d == "$" and j + 1 < n and src[j + 1] == "{":
            j = _fim_expr(src, j + 1); continue
        j += 1
    return n


def _fim_expr(src, i):
    """`src[i]` é o `{` de um `${`; devolve o índice logo após o `}` que o
    fecha, ciente de string, template aninhado, regex e chaves aninhadas."""
    n, prof, j = len(src), 0, i
    while j < n:
        e = src[j]
        if e in "'\"": j = _fim_string(src, j); continue
        if e == "`": j = _fim_template(src, j); continue
        if e == "/" and _inicia_regex(src, j):
            fim = _fim_regex(src, j)
            if fim is not None: j = fim; continue
        if e == "{": prof += 1
        elif e == "}":
            prof -= 1
            if prof == 0: return j + 1
        j += 1
    return n


def literais(src, _linha0=1):
    """[(linha_1based, aspa, texto)] de cada literal de string do fonte.

    Em template com ${}, devolve só os PEDAÇOS de texto — a expressão fica de
    fora, que é o certo: `Turno ${n}` tem o texto "Turno " e não o `n`."""
    out, i, n, linha = [], 0, len(src), _linha0
    while i < n:
        c = src[i]
        if c == "\n":
            linha += 1; i += 1; continue
        # comentários
        if c == "/" and i + 1 < n:
            if src[i + 1] == "/":
                j = src.find("\n", i)
                i = n if j < 0 else j
                continue
            if src[i + 1] == "*":
                j = src.find("*/", i + 2)
                trecho = src[i:(n if j < 0 else j + 2)]
                linha += trecho.count("\n")
                i = n if j < 0 else j + 2
                continue
            # Literal de regex. Sem tratá-lo, `/[&<>"']/g` abria uma string
            # fantasma na aspa de dentro e TUDO a partir dali saía deslocado —
            # o placar passou a contar pedaços de comentário e de código como
            # se fossem texto de interface, e um migrador chegou a escrever
            # dentro de um seletor por causa disso.
            if _inicia_regex(src, i):
                j = _fim_regex(src, i)
                if j is not None:
                    i = j
                    continue
        # string simples
        if c in "'\"":
            ini, buf, i = linha, [], i + 1
            while i < n:
                d = src[i]
                if d == "\\": buf.append(src[i:i + 2]); i += 2; continue
                if d == c: i += 1; break
                if d == "\n": linha += 1
                buf.append(d); i += 1
            out.append((ini, c, "".join(buf)))
            continue
        # template literal
        if c == "`":
            ini, buf, i = linha, [], i + 1
            while i < n:
                d = src[i]
                if d == "\\": buf.append(src[i:i + 2]); i += 2; continue
                if d == "`": i += 1; break
                if d == "$" and i + 1 < n and src[i + 1] == "{":
                    # A expressão é código: pula contando chaves, mas CIENTE DE
                    # ASPAS — `${x + '{'}` tem uma chave dentro de uma string, e
                    # contá-la faria a profundidade nunca fechar, engolindo o
                    # resto do arquivo. É a mesma armadilha do `.get` aninhado
                    # que quebrou o regex da etapa 4c.
                    #
                    # MAS a expressao nao e SO codigo: uma IIFE dentro do ${}
                    # devolve TEMPLATE, e esse markup o jogador le. Pular o
                    # conteudo inteiro escondia 31 textos do game.js do placar
                    # da etapa 5 -- entre eles os banners SACIADO/EXAUSTAO do
                    # HUD, que ficaram em portugues com o placar cravando zero.
                    # Por isso RECURSA: o buraco segue marcado como ${} no texto
                    # de fora, e o que houver de string DENTRO vira literal.
                    # Um trecho aninhado (`${a ? `x ${b}` : 'y'}`) tem template
                    # dentro de template: o fim do buraco é achado por um
                    # scanner que sabe pular string, template aninhado e regex
                    # (`.replace(/'/g, ...)` tem aspa dentro do literal).
                    ini_expr, linha_expr = i + 2, linha
                    fim = _fim_expr(src, i + 1)
                    linha += src.count("\n", i, fim)
                    out.extend(literais(src[ini_expr:fim - 1], linha_expr))
                    i = fim
                    buf.append("${}")     # marca o buraco, sem o conteúdo
                    continue
                if d == "\n": linha += 1
                buf.append(d); i += 1
            out.append((ini, "`", "".join(buf)))
            continue
        i += 1
    return out


ACENTO = re.compile(r"[ãáàâçéêíóõôúÃÁÀÂÇÉÊÍÓÕÔÚ]")
# Caminho de arquivo, seletor e chave de dicionário não são texto de interface.
IGNORAR = re.compile(r"\.(js|png|jpe?g|glb|css|html)$|^assets/|^#[\w-]+$|^[\w.]+\.[\w.]+$")


# Comentário HTML dentro de um template NÃO é texto de interface: ele vai para o
# DOM, mas o jogador nunca o vê. Como um template multilinha inteiro conta como UM
# literal, um `<!-- FOME E SEDE -->` no meio dele mantinha a função inteira no
# placar mesmo com todos os rótulos já traduzidos. São 4 casos no game.js.
COMENTARIO_HTML = re.compile(r"<!--.*?-->", re.S)


# ── Português SEM acento ─────────────────────────────────────────────────
# Até 2026-09-14 o placar só contava literal COM ACENTO, e `Rodada`, `SUA VEZ`,
# `Aguardando`, `Continuar`, `FALHOU`, `Ouro insuficiente` ficaram em português
# no HUD em inglês com o placar cravando zero. A segunda rede é um VOCABULÁRIO
# derivado do próprio dicionário: toda palavra (≥3 letras) que aparece nos
# textos `pt` de src/lang/*.js e em NENHUM texto `en` é palavra portuguesa. Um
# literal conta quando tem uma dessas palavras FORA de tag HTML — e não parece
# identificador (`cena-npc`, `mira_certeira`), seletor CSS ou valor todo em
# minúsculas de uma palavra só (`'ataque'` é id de tipo, não rótulo).
PALAVRA = re.compile(r"[A-Za-zÀ-ÿ]{3,}")
_TAG = re.compile(r"<[^<>]*>")
_TAG_ABERTA = re.compile(r"<[a-zA-Z][^<>]*$")
_PARAM = re.compile(r"\{[^{}]*\}")
_SELETOR = re.compile(r"^[.#\[]|:not\(|^[\w\s.#>,:\[\]=\"'()\-]*[.#]\w")
_VOCAB_PT = None


def _vocabulario_pt():
    """Palavras que só existem no lado `pt` do dicionário (cacheado)."""
    global _VOCAB_PT
    if _VOCAB_PT is not None:
        return _VOCAB_PT
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pt, en = set(), set()
    val = r'"%s":\s*"((?:[^"\\]|\\.)*)"'
    import glob
    for f in glob.glob(os.path.join(raiz, "src", "lang", "*.js")):
        txt = io.open(f, encoding="utf-8").read()
        # Os {parâmetros} têm nome em português nos DOIS lados ({rodadas}):
        # saem antes, senão apagariam a palavra do vocabulário.
        for m in re.finditer(val % "pt", txt):
            pt.update(w.lower() for w in PALAVRA.findall(_PARAM.sub(" ", m.group(1))))
        for m in re.finditer(val % "en", txt):
            en.update(w.lower() for w in PALAVRA.findall(_PARAM.sub(" ", m.group(1))))
    _VOCAB_PT = pt - en
    return _VOCAB_PT


def parece_portugues(limpo, vocab=None):
    """True se o literal (já sem espaços nas pontas) parece texto em português
    para o jogador — por acento OU por vocabulário."""
    sem_coment = COMENTARIO_HTML.sub(" ", limpo)
    if ACENTO.search(sem_coment):
        return True
    vocab = _vocabulario_pt() if vocab is None else vocab
    if not vocab:
        return False
    # tag inteira E fragmento de tag sem fechar (`<img class="x" style="`):
    # o que está dentro de atributo nunca é texto para o jogador
    texto = _TAG_ABERTA.sub(" ", _TAG.sub(" ", sem_coment)).replace("${}", " ")
    palavras = PALAVRA.findall(texto)
    if not any(w.lower() in vocab for w in palavras):
        return False
    # identificador: uma "palavra" só (sem espaço no LITERAL — o buraco ${}
    # não conta como espaço), com _ - : ou toda minúscula; ou colado a um ${}
    if not re.search(r"\s", limpo) and (re.search(r"[_\-:]", limpo) or limpo == limpo.lower()
                                        or limpo.startswith("${}") or limpo.endswith("${}")):
        return False
    if "<" not in limpo and _SELETOR.search(limpo):
        return False
    # frase (2+ palavras) ou rótulo com inicial maiúscula (`Rodada`, `FALHOU`)
    return len(palavras) >= 2 or palavras[0][0].isupper()


def texto_de_interface(src):
    """[(linha, texto)] dos literais que parecem texto para o jogador."""
    out = []
    vocab = _vocabulario_pt()
    for linha, _aspa, t in literais(src):
        limpo = t.strip()
        if len(limpo) < 3: continue
        if IGNORAR.search(limpo): continue
        if not parece_portugues(limpo, vocab): continue
        out.append((linha, limpo))
    return out


def _autoteste():
    ok = fail = 0
    def check(nome, cond):
        nonlocal ok, fail
        if cond: ok += 1; print(f"  ✅ {nome}")
        else:    fail += 1; print(f"  ❌ {nome}")

    src = """
const a = 'olá';            // comentário com açúcar
const b = "com \\" escape e ã";
const c = `linha um ção
linha dois ${x + '{'} fim`;
/* bloco com ó
   em duas linhas */
const d = 'depois';
"""
    ls = literais(src)
    txt = [t for _, _, t in ls]
    check("acha string simples", "olá" in txt)
    check("escape não encerra a string", any('com \\" escape e ã' == t for t in txt))
    check("template MULTILINHA vira um literal só",
          any("linha um ção" in t and "linha dois" in t for t in txt))
    check("a expressão de ${} é pulada",
          any("${}" in t and "x + " not in t for t in txt))
    check("comentário de linha não vira texto", not any("comentário" in t for t in txt))
    check("comentário de bloco não vira texto", not any("bloco com" in t for t in txt))
    check("continua lendo depois do bloco", "depois" in txt)

    # Comentário HTML não é texto de interface — o jogador nunca o vê.
    so_comentario = "const e = `<!-- SEÇÃO -->\n  <div>ok</div>`;"
    check("template cujo único acento está em comentário HTML não conta",
          not texto_de_interface(so_comentario))
    com_rotulo = "const f = `<!-- SEÇÃO -->\n  <div>Força</div>`;"
    check("mas o rótulo acentuado FORA do comentário ainda conta",
          len(texto_de_interface(com_rotulo)) == 1)

    # Português SEM acento: entra por vocabulário; identificador e seletor, não.
    v = {"rodada", "aguardando", "vez", "sua", "cena", "mira", "certeira", "ataque"}
    check("rótulo sem acento com inicial maiúscula conta", parece_portugues("Rodada ${}", v))
    check("frase sem acento conta", parece_portugues("SUA VEZ — ${}", v))
    check("identificador com hífen não conta", not parece_portugues("cena-npc", v))
    check("identificador com underscore não conta", not parece_portugues("mira_certeira", v))
    check("valor minúsculo de uma palavra não conta", not parece_portugues("ataque", v))
    check("id com buraco de template não conta", not parece_portugues("ira-rocha:${}:impact", v)
          and not parece_portugues("${}Dir", {"dir"}))
    check("seletor CSS não conta", not parece_portugues("#shop-modal .cena-npc", v))
    check("palavra portuguesa só dentro de atributo de tag não conta",
          not parece_portugues('<div class="cena-npc"></div>', v))
    check("texto português entre tags conta", parece_portugues("<b>Rodada</b> ${}", v))
    check("fragmento de tag sem fechar não conta", not parece_portugues('<img class="cena-mask" style="', v))
    check("inglês puro não conta", not parece_portugues("Round ${}", v))
    check("o vocabulário real tem centenas de palavras", len(_vocabulario_pt()) > 500)
    check("`rodada` está no vocabulário real e `round` não",
          "rodada" in _vocabulario_pt() and "round" not in _vocabulario_pt())

    # A linha reportada tem de ser a do INÍCIO do literal.
    linhas = {t: l for l, _, t in ls}
    check("linha do template é a de abertura",
          any(l == 4 for t, l in linhas.items() if "linha um ção" in t))
    return ok, fail


if __name__ == "__main__":
    print("=" * 62); print("  AUTOTESTE — tokenizador de strings JS"); print("=" * 62)
    ok, fail = _autoteste()
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = io.open(os.path.join(raiz, "game.js"), encoding="utf-8").read()
    achados = texto_de_interface(src)
    print(f"\n  game.js: {len(literais(src))} literais no total, "
          f"{len(achados)} com texto de interface em português")
    print("\n" + "=" * 62)
    print(f"  {ok} passaram, {fail} falharam")
    print("=" * 62)
    sys.exit(1 if fail else 0)
