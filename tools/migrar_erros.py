"""Migra as mensagens de erro de TEXTO FIXO do server.py para T("erro.…").

Roda da raiz:  python tools/migrar_erros.py

Uso ÚNICO. Depois de rodar, o server.py não tem mais o texto em português —
só a chave — então não há de onde gerar de novo, e src/lang/erros.js passa a
ser mantido à mão.

NÃO toca nas mensagens com f-string: cada uma exige batizar o parâmetro, e é
onde um script erraria em silêncio. Elas são migradas à mão depois.
"""
import io, json, os, re, sys, unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "server.py")
DICIONARIO = os.path.join(RAIZ, "src", "lang", "erros.js")

RE_MSG = re.compile(r'"msg":\s*(f?)"([^"]{2,200})"')
RE_ERR = re.compile(r'await err\((f?)"([^"]{2,200})"')


def slug(texto, limite=40):
    """Slug do texto em português. Emojis e acentos somem no encode ascii —
    são formatação, não conteúdo, e o texto restante identifica bem a frase."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    t = t[:limite].rstrip("_")
    return t or "mensagem"


def montar_chaves(textos):
    """{texto: chave}, com dedup por construção e colisão relatada.
    Mesmo texto → mesmo slug → uma chave só para todas as ocorrências."""
    por_slug = {}
    chaves = {}
    colisoes = []
    for texto in textos:
        if texto in chaves:
            continue
        base = slug(texto)
        s = base
        n = 2
        while s in por_slug and por_slug[s] != texto:
            colisoes.append((s, por_slug[s], texto))
            s = f"{base}_{n}"
            n += 1
        por_slug[s] = texto
        chaves[texto] = "erro." + s
    return chaves, colisoes


def ler_existente():
    try:
        raw = io.open(DICIONARIO, encoding="utf-8").read()
        m = re.search(r"^\s*window\.LANG_ERROS\s*=", raw, re.MULTILINE)
        return json.loads(raw[raw.index("{", m.end()):raw.rindex("}") + 1])
    except Exception:
        return {}


def escrever(dicionario):
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2, sort_keys=True)
    with io.open(DICIONARIO, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "// Mensagens de RECUSA do servidor ao jogador (etapa 4a do idioma).\n"
            "//\n"
            "// Mantido À MÃO: depois da migração o server.py não contém mais o texto\n"
            "// em português, só a chave, então não há de onde gerar de novo. A chave é\n"
            "// o slug do texto original, o que garante que a mesma recusa use sempre a\n"
            "// mesma frase.\n"
            "window.LANG_ERROS = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_ERROS);\n")


def main():
    fonte = io.open(FONTE, encoding="utf-8").read()
    fixos = [t for f, t in RE_MSG.findall(fonte) if not f]
    fixos += [t for f, t in RE_ERR.findall(fonte) if not f]
    chaves, colisoes = montar_chaves(fixos)

    def troca_msg(m):
        if m.group(1):          # f-string: fica para a migração à mão
            return m.group(0)
        return '"msg": T("%s")' % chaves[m.group(2)]

    def troca_err(m):
        if m.group(1):
            return m.group(0)
        return 'await err(T("%s")' % chaves[m.group(2)]

    novo = RE_MSG.sub(troca_msg, fonte)
    novo = RE_ERR.sub(troca_err, novo)

    dic = ler_existente()
    for texto, chave in chaves.items():
        entrada = dic.get(chave) or {}
        dic[chave] = {"pt": texto, "en": entrada.get("en", "")}

    with io.open(FONTE, "w", encoding="utf-8", newline="\n") as f:
        f.write(novo)
    escrever(dic)

    print(f"{len(fixos)} ocorrências de texto fixo → {len(chaves)} chaves distintas.")
    print(f"{sum(1 for v in dic.values() if not v['en'])} sem tradução para o inglês.")
    if colisoes:
        print(f"\n⚠️  {len(colisoes)} colisão(ões) de slug — revise à mão:")
        for s, a, b in colisoes:
            print(f"   {s}\n      {a[:60]}\n      {b[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
