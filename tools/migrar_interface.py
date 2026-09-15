"""Migra para t("ui.…") os literais de TEXTO SIMPLES do game.js.

Roda da raiz:  python tools/migrar_interface.py [--aplicar]

O QUE FAZ E O QUE NAO FAZ
  Trata so o grupo seguro: literal em ASPAS (simples ou duplas) cujo conteudo e
  texto puro — sem markup e sem interpolacao. Markup vai por `data-i18n` (o
  portugues fica no arquivo como fonte) e interpolacao exige batizar parametro:
  os dois sao feitos a parte.

DE ONDE VEM O TEXTO
  Do PLACAR (`test_interface._literais_pendentes`), nunca de heuristica propria.
  A primeira versao do migrador da cauda do Lote 3 escolhia "o maior literal da
  linha" e, em 6 de 72 linhas, trocou um ID ou uma cor CSS por uma chamada de
  traducao — `node --check` passa e o estrago e silencioso.

COMO SUBSTITUI — e por que NAO por offset do tokenizador
  A primeira versao usava os offsets de um tokenizador com estado. Nao funciona:
  o `js_strings` (e esta copia dele) NAO trata literal de expressao regular, que
  nao da para distinguir de divisao sem analise sintatica. Uma aspa dentro de um
  /regex/ abre uma string fantasma e, dali para a frente, TODO offset esta
  deslocado — o migrador chegou a escrever `t('...')` no meio do seletor
  `document.querySelector('[id^="painel-"]')`, quebrando o arquivo.
  Para CONTAR isso e inofensivo (o placar so soma trechos com acento); para
  SUBSTITUIR e fatal.

  Entao a troca e LOCALIZADA: na linha que o placar aponta, procura o literal
  com seus delimitadores (`'txt'` ou `"txt"`) e so troca se ele aparecer
  EXATAMENTE UMA VEZ. Sem estado global, sem offset acumulado. Literal que nao
  casa — ou casa duas vezes — e relatado e fica para a mao.
"""
import io, json, os, re, sys, time, unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
GAME = os.path.join(RAIZ, "game.js")
DICIONARIO = os.path.join(RAIZ, "src", "lang", "interface.js")


# ── tokenizador com offsets ───────────────────────────────────────────────
def literais_pos(src, base=0, linha0=1):
    """[(linha, aspa, texto, ini, fim)] — ini/fim delimitam o LITERAL INTEIRO
    (com as aspas). Espelha `js_strings.literais`, guardando posicoes."""
    out, i, n, linha = [], 0, len(src), linha0
    while i < n:
        c = src[i]
        if c == "\n":
            linha += 1; i += 1; continue
        if c == "/" and i + 1 < n:
            if src[i + 1] == "/":
                j = src.find("\n", i); i = n if j < 0 else j; continue
            if src[i + 1] == "*":
                j = src.find("*/", i + 2)
                trecho = src[i:(n if j < 0 else j + 2)]
                linha += trecho.count("\n"); i = n if j < 0 else j + 2; continue
        if c in "'\"":
            ini_lit, ini, buf, i = i, linha, [], i + 1
            while i < n:
                d = src[i]
                if d == "\\": buf.append(src[i:i + 2]); i += 2; continue
                if d == c: i += 1; break
                if d == "\n": linha += 1
                buf.append(d); i += 1
            out.append((ini, c, "".join(buf), base + ini_lit, base + i))
            continue
        if c == "`":
            ini_lit, ini, buf, i = i, linha, [], i + 1
            while i < n:
                d = src[i]
                if d == "\\": buf.append(src[i:i + 2]); i += 2; continue
                if d == "`": i += 1; break
                if d == "$" and i + 1 < n and src[i + 1] == "{":
                    prof, aspa, i = 0, None, i + 1
                    ini_expr, linha_expr = i + 1, linha
                    while i < n:
                        e = src[i]
                        if aspa:
                            if e == "\\": i += 2; continue
                            if e == aspa: aspa = None
                            elif e == "\n": linha += 1
                        elif e in "'\"`": aspa = e
                        elif e == "{": prof += 1
                        elif e == "}":
                            prof -= 1
                            if prof == 0: break
                        elif e == "\n": linha += 1
                        i += 1
                    out.extend(literais_pos(src[ini_expr:i], base + ini_expr, linha_expr))
                    i += 1; buf.append("${}"); continue
                if d == "\n": linha += 1
                buf.append(d); i += 1
            out.append((ini, "`", "".join(buf), base + ini_lit, base + i))
            continue
        i += 1
    return out


# ── area da chave, por funcao dona ────────────────────────────────────────
RE_FN = re.compile(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"
                   r"|^const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")

# Prefixo/nome da funcao -> area da chave. As areas sao as que ja existem no
# interface.js; assim as chaves novas caem ao lado das antigas.
AREA_POR_FUNCAO = [
    ("_modificadoresTemporariosStatus", "status"),
    ("_audioPanel", "audio"), ("_audio", "audio"),
    ("SenhorDasAguas", "magia"), ("ChamadoInverno", "magia"),
    ("Metamorfose", "magia"), ("metamorfose", "magia"),
    ("Elemental", "elemental"), ("Magia", "magia"), ("magia", "magia"),
    ("_mageSkillBtn", "magia"),
    ("Instrumento", "instrumento"), ("instrumento", "instrumento"),
    ("Mestre", "mestre"), ("_mp", "mestre"), ("Master", "mestre"),
    ("Armadilha", "armadilha"), ("armadilha", "armadilha"),
    ("Animado", "animar"), ("AnimarMortos", "animar"), ("Animar", "animar"),
    ("Throw", "arremesso"), ("Arremesso", "arremesso"), ("_weapon", "arremesso"),
    ("Bau", "bau"), ("Loot", "bau"),
    ("Gamepad", "joystick"), ("gamepad", "joystick"),
    ("_cPaladin", "paladino"), ("_paladin", "paladino"),
    ("_rogue", "ladino"), ("_cleric", "clerigo"), ("_bard", "bardo"),
    ("_aim", "mira"), ("Mira", "mira"), ("mira", "mira"),
    ("init3D", "tabuleiro"), ("on3D", "tabuleiro"), ("_setup2D", "tabuleiro"),
    ("_draw", "tabuleiro"), ("_makeBillboard", "tabuleiro"),
    ("cs", "selecao"), ("_cs", "selecao"),
    ("Cidade", "cidade"), ("city", "cidade"), ("City", "cidade"),
    ("_item", "item"), ("Item", "item"),
    ("Ficha", "ficha"), ("ficha", "ficha"),
    ("Shop", "loja"), ("Loja", "loja"),
]
AREA_PADRAO = "hud"


def area_de(fn):
    for prefixo, area in AREA_POR_FUNCAO:
        if fn == prefixo or prefixo in fn:
            return area
    return AREA_PADRAO


RE_FECHA_TOPO = re.compile(r"^[}\]]")   # `}` / `};` / `})` na coluna 0 fecha o bloco de topo


def donos(src_linhas):
    """Funcao de topo dona de cada linha. Um `}` na coluna 0 devolve ao nivel
    de modulo — sem isso, um `const X = {...}` depois de uma funcao ficava
    atribuido a ela e o migrador poria `t()` num objeto de nivel de modulo."""
    out, atual = [], "topo"
    for l in src_linhas:
        m = RE_FN.match(l)
        if m: atual = m.group(1) or m.group(2)
        elif RE_FECHA_TOPO.match(l): atual = "topo"
        out.append(atual)
    return out


RE_T_LOCAL = re.compile(r"\b(?:const|let|var)\s+t\s*=|\bfunction\b[^(]*\([^)]*\bt\b[^)]*\)")


def funcoes_com_t_local(src_linhas, dono):
    """Funcoes de topo que declaram um `t` proprio (ex.: `const t = $('toast')`).
    Dentro delas `t('chave')` e TypeError em runtime — o Lote 3 pagou isso 5
    vezes. Ali a troca usa `I18N.t(...)`, o global sem sombra."""
    out = set()
    for l, fn in zip(src_linhas, dono):
        if fn != "topo" and RE_T_LOCAL.search(l):
            out.add(fn)
    return out


def slug(texto, limite=42):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    return t[:limite].rstrip("_") or "texto"


# ── dicionario ────────────────────────────────────────────────────────────
def ler_dicionario():
    raw = io.open(DICIONARIO, encoding="utf-8").read()
    m = re.search(r"^\s*window\.LANG_INTERFACE\s*=", raw, re.M)
    ini = raw.index("{", m.end()); fim = raw.rindex("}") + 1
    return raw, ini, fim, json.loads(raw[ini:fim])


def gravar(caminho, conteudo, nl="\n"):
    for _ in range(6):
        try:
            io.open(caminho, "w", encoding="utf-8", newline=nl).write(conteudo)
            return True
        except OSError as e:
            print("  trava transitoria em %s (%s)..." % (os.path.basename(caminho), e))
            time.sleep(1.5)
    return False


def main(aplicar):
    import importlib.util
    spec = importlib.util.spec_from_file_location("ti", os.path.join(RAIZ, "tools", "test_interface.py"))
    ti = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(ti)
    except SystemExit: pass

    src = io.open(GAME, encoding="utf-8").read()
    linhas = src.split("\n")
    pend = list(ti._literais_pendentes())
    dono = donos(linhas)

    raw, dini, dfim, dic = ler_dicionario()
    usadas = set(dic)
    novas, trocas, pulados = {}, [], []
    com_t_local = funcoes_com_t_local(linhas, dono)

    for linha, txt in pend:
        if "<" in txt and ">" in txt:
            pulados.append((linha, "markup", txt)); continue
        if "${}" in txt:
            pulados.append((linha, "interpolacao", txt)); continue
        if "\n" in txt:
            pulados.append((linha, "multilinha", txt)); continue
        if linha > len(linhas):
            pulados.append((linha, "linha fora do arquivo", txt)); continue
        corpo_linha = linhas[linha - 1]
        # O literal precisa estar inteiro na linha, com um dos delimitadores, e
        # so uma vez: duas ocorrencias na mesma linha sao ambiguas.
        formas = [a + txt + a for a in ("'", '"') if (a + txt + a) in corpo_linha]
        if len(formas) != 1 or corpo_linha.count(formas[0]) != 1:
            pulados.append((linha, "ambiguo/nao casou", txt)); continue

        # Posicao onde uma CHAMADA nao vale: chave de objeto (`'txt': v`) e
        # `case 'txt':`. Cuidado com o falso positivo do ternario, cujo `:`
        # tambem segue o literal — ali a troca e perfeitamente segura.
        pos = corpo_linha.index(formas[0])
        antes = corpo_linha[:pos].rstrip()
        depois = corpo_linha[pos + len(formas[0]):].lstrip()
        if depois.startswith(":") and not antes.endswith("?"):
            pulados.append((linha, "chave de objeto", txt)); continue
        if re.search(r"\bcase$", antes):
            pulados.append((linha, "case", txt)); continue

        fn = dono[linha - 1]
        # Nivel de modulo: um `t()` num `const` de topo roda no CARREGAMENTO e
        # aborta o game.js (TDZ) — vira funcao, a mao.
        if fn == "topo":
            pulados.append((linha, "nivel de modulo", txt)); continue
        chamada = "I18N.t" if fn in com_t_local else "t"
        base = "ui.%s.%s" % (area_de(fn), slug(txt))
        chave, n = base, 2
        while (chave in usadas and dic.get(chave, {}).get("pt") != txt) or \
              (chave in novas and novas[chave] != txt):
            chave = "%s_%d" % (base, n); n += 1
        if chave not in dic:
            novas[chave] = txt
        usadas.add(chave)
        trocas.append((linha, formas[0], chave, txt, chamada))

    print("literais trocaveis: %d" % len(trocas))
    print("chaves novas: %d" % len(novas))
    print("pulados: %d" % len(pulados))
    for tipo in ("markup", "interpolacao", "multilinha", "ambiguo/nao casou",
                 "chave de objeto", "case", "linha fora do arquivo", "nivel de modulo"):
        n = sum(1 for _, t, _ in pulados if t == tipo)
        if n: print("   %-22s %d" % (tipo, n))
    if not aplicar:
        for l, t, txt in pulados:
            if t in ("ambiguo/nao casou", "nivel de modulo"):
                print("   ! linha %s %s: %r" % (l, t, txt[:70]))
        print("   funcoes com `t` local (usam I18N.t): %d" % len(com_t_local))
        print("\n(dry-run — passe --aplicar para gravar)")
        return 0

    for linha, forma, chave, _txt, chamada in trocas:
        linhas[linha - 1] = linhas[linha - 1].replace(forma, "%s('%s')" % (chamada, chave), 1)

    for chave, txt in novas.items():
        dic[chave] = {"pt": txt, "en": ""}
    corpo = json.dumps(dic, ensure_ascii=False, indent=2, sort_keys=True)

    if not gravar(GAME, "\n".join(linhas)): raise SystemExit("nao gravou game.js")
    if not gravar(DICIONARIO, raw[:dini] + corpo + raw[dfim:]):
        raise SystemExit("nao gravou interface.js")
    print("\naplicado. sem `en`: %d" % sum(1 for v in dic.values() if not v.get("en")))
    return 0


if __name__ == "__main__":
    sys.exit(main("--aplicar" in sys.argv))
