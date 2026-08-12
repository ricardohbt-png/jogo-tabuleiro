"""Migra os gm_say MECÂNICOS do server.py para T("narracao.…").

Roda da raiz:  python tools/migrar_narracao.py

Uso ÚNICO. Cobre só as duas formas de UMA LINHA: gm_say("…") e gm_say(f"…").
Multilinha, concatenação, variável e o pool gm(...) ficam de fora de propósito
— são a etapa 4b-ii, e cada um pede um tratamento próprio.

Depois de rodar, o server.py não tem mais o texto em português, só a chave, e
src/lang/narracao.js passa a ser mantido à mão.
"""
import io, json, os, re, sys, unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
from migrar_erros import slug          # mesma regra de slug da etapa 4a

FONTE = os.path.join(RAIZ, "server.py")
DICIONARIO = os.path.join(RAIZ, "src", "lang", "narracao.js")

RE_UMA_LINHA = re.compile(r'gm_say\((f?)"([^"]*)"\)')
RE_INTERP = re.compile(r"\{([^{}]+)\}")
RE_SUBSCRITO_NOME = re.compile(r"""^(\w+)\[['"]name['"]\]$""")

# Só os dois nomes opacos e mais frequentes (231 das 764 interpolações). O resto
# já é legível pela regra: alvo['name'] vira {alvo}, item['name'] vira {item}.
APELIDOS = {"p": "heroi", "m": "monstro"}


def nome_param(expr):
    """Batismo determinístico, em três degraus."""
    e = expr.strip()
    if re.fullmatch(r"\w+", e):
        return APELIDOS.get(e, e)
    m = RE_SUBSCRITO_NOME.match(e)
    if m:
        return APELIDOS.get(m.group(1), m.group(1))
    return slug(e, 24) or "valor"


def preparar(texto):
    """Devolve (texto_com_nomes, [(nome, expressao)], colisoes).
    O texto sai com {expressao} trocado por {nome}, pronto para o dicionário."""
    exprs = RE_INTERP.findall(texto)
    usados = {}      # nome -> expressao
    nomes = []
    colisoes = []
    for e in exprs:
        n = nome_param(e)
        if n in usados and usados[n] != e:
            base, i = n, 2
            while f"{base}_{i}" in usados and usados[f"{base}_{i}"] != e:
                i += 1
            colisoes.append((base, usados[base], e))
            n = f"{base}_{i}"
        usados[n] = e
        nomes.append(n)
    it = iter(nomes)
    novo = RE_INTERP.sub(lambda m: "{" + next(it) + "}", texto)
    # dict.fromkeys preserva a ordem e remove o par repetido (mesma expressão
    # usada duas vezes na frase entra uma vez só na chamada).
    pares = list(dict.fromkeys(zip(nomes, exprs)))
    return novo, pares, colisoes


def chave_de(texto_sem_interp):
    return "narracao." + slug(texto_sem_interp)


def ler_existente():
    try:
        raw = io.open(DICIONARIO, encoding="utf-8").read()
        m = re.search(r"^\s*window\.LANG_NARRACAO\s*=", raw, re.MULTILINE)
        return json.loads(raw[raw.index("{", m.end()):raw.rindex("}") + 1])
    except Exception:
        return {}


def escrever(dicionario):
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2, sort_keys=True)
    with io.open(DICIONARIO, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "// NARRAÇÃO do mestre — o log que conta o que acontece na partida\n"
            "// (etapa 4b-i do idioma).\n"
            "//\n"
            "// Mantido À MÃO: depois da migração o server.py não contém mais o texto\n"
            "// em português, só a chave. A chave é o slug do texto SEM as interpolações.\n"
            "window.LANG_NARRACAO = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_NARRACAO);\n")


def main():
    fonte = io.open(FONTE, encoding="utf-8").read()
    dic = ler_existente()
    por_chave = {}          # chave -> texto_pt (para detectar colisão de chave)
    colisoes_param = []
    colisoes_chave = []
    sites = [0]

    def troca(m):
        texto = m.group(2)
        novo_texto, pares, col = preparar(texto)
        colisoes_param.extend(col)
        # A chave vem do texto SEM as interpolações: mais legível.
        sem_interp = RE_INTERP.sub("", texto)
        ch = chave_de(sem_interp)
        if ch in por_chave and por_chave[ch] != novo_texto:
            colisoes_chave.append((ch, por_chave[ch], novo_texto))
            base, i = ch, 2
            while f"{base}_{i}" in por_chave and por_chave[f"{base}_{i}"] != novo_texto:
                i += 1
            ch = f"{base}_{i}"
        por_chave[ch] = novo_texto
        entrada = dic.get(ch) or {}
        dic[ch] = {"pt": novo_texto, "en": entrada.get("en", "")}
        sites[0] += 1
        args = ", ".join(f"{n}={e}" for n, e in pares)
        return f'gm_say(T("{ch}"{", " + args if args else ""}))'

    novo = RE_UMA_LINHA.sub(troca, fonte)
    with io.open(FONTE, "w", encoding="utf-8", newline="\n") as f:
        f.write(novo)
    escrever(dic)

    print(f"{sites[0]} sites migrados → {len(por_chave)} chaves distintas.")
    print(f"{sum(1 for v in dic.values() if not v['en'])} sem tradução para o inglês.")
    if colisoes_param:
        print(f"\n⚠️  {len(colisoes_param)} colisão(ões) de PARÂMETRO dentro de uma frase:")
        for b, a, c in colisoes_param[:10]:
            print(f"   {b}: {a}  ×  {c}")
    if colisoes_chave:
        print(f"\n⚠️  {len(colisoes_chave)} colisão(ões) de CHAVE — revise:")
        for ch, a, b in colisoes_chave[:10]:
            print(f"   {ch}\n      {a[:64]}\n      {b[:64]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
