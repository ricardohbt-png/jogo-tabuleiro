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


def literais(src):
    """[(linha_1based, aspa, texto)] de cada literal de string do fonte.

    Em template com ${}, devolve só os PEDAÇOS de texto — a expressão fica de
    fora, que é o certo: `Turno ${n}` tem o texto "Turno " e não o `n`."""
    out, i, n, linha = [], 0, len(src), 1
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
                    prof, aspa, i = 0, None, i + 1
                    while i < n:
                        e = src[i]
                        if aspa:
                            if e == "\\": i += 2; continue
                            if e == aspa: aspa = None
                            elif e == "\n": linha += 1
                        elif e in "'\"`":
                            aspa = e
                        elif e == "{": prof += 1
                        elif e == "}":
                            prof -= 1
                            if prof == 0: i += 1; break
                        elif e == "\n": linha += 1
                        i += 1
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


def texto_de_interface(src):
    """[(linha, texto)] dos literais que parecem texto para o jogador."""
    out = []
    for linha, _aspa, t in literais(src):
        limpo = t.strip()
        if len(limpo) < 3 or not ACENTO.search(limpo): continue
        if IGNORAR.search(limpo): continue
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
