"""Marca com `data-i18n` o texto do MARKUP gerado em JS (fase 2 da migracao).

Roda da raiz:  python tools/migrar_interface_markup.py [--aplicar]

POR QUE data-i18n E NAO ${t(...)}
  Dois motivos. (1) 71 dos 95 literais de markup pendentes estao em ASPAS, nao
  em template: enfiar `${}` ali exigiria trocar o delimitador da string, que e
  arriscado quando o conteudo tem crase ou `${`. (2) O projeto ja resolveu isso
  na etapa 5.0 — o MutationObserver de `document.body` traduz qualquer no
  inserido que traga `[data-i18n]`, entao markup gerado em JS se conserta
  sozinho. O portugues fica no arquivo como FONTE, igual ao index.html.

A TRAVA QUE IMPORTA
  `_i18nApply` usa `textContent`, que APAGA os filhos do elemento. So marca-se
  elemento cujo conteudo inteiro seja texto — `<div ...>texto</div>` sem
  nenhuma tag dentro. Elemento que mistura markup e texto fica de fora (o
  projeto tem `data-i18n-html` para isso, mas ele so vale para texto NOSSO e
  deve ser usado com intencao, nao em lote).
"""
import io, json, os, re, sys, time, unicodedata

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
GAME = os.path.join(RAIZ, "game.js")
DICIONARIO = os.path.join(RAIZ, "src", "lang", "interface.js")

from migrar_interface import (area_de, donos, slug, ler_dicionario, gravar)

# <tag atributos>texto</tag> — sem nenhuma tag no meio do texto.
RE_ELEMENTO = re.compile(r"<([a-zA-Z][\w-]*)((?:[^<>]|\\\"|\\')*?)>([^<>]+)</\1>")
# title="texto" — o texto de tooltip e interface como qualquer outro, e o
# _i18nApply ja varre [data-i18n-title].
RE_TITLE = re.compile(r'title="([^"$]{3,120})"')
# Texto solto ENTRE tags: `</i> alcance</span>`. Marcar o pai apagaria o irmao
# (_i18nApply usa textContent), entao o texto e envolvido num <span> proprio.
#
# O grupo 1 tem de ser uma TAG INTEIRA, nunca um `>` solto. A primeira versao
# aceitava qualquer `>` e casou a expressao JS `nx>=0&&ny><W`, embrulhando um
# pedaco de codigo em <span> e quebrando o arquivo. Um `>` no JavaScript e
# operador com muito mais frequencia do que fim de tag.
RE_TEXTO_SOLTO = re.compile(
    r"(</?[a-zA-Z][\w-]*(?:\s[^<>]*)?/?>)([^<>${}]*[A-Za-zÀ-ÿ]{2,}[^<>${}]*)(<)")
RE_LETRA = re.compile(r"[A-Za-zÀ-ÿ]{2,}")
RE_ACENTO = re.compile(r"[ãáàâçéêíóõôúÃÁÀÂÇÉÊÍÓÕÔÚ]")


def marcavel(texto):
    """Texto que vale a pena marcar.

    Mede LETRA, nao acento. Foi a mesma correcao que a secao [7] do
    test_interface ja tinha precisado: dentro de markup, `Criar redemoinhos`,
    `Fechar` e `Iniciar Jogo` sao texto de interface como qualquer outro, e
    exigir acento perdia a maioria deles em silencio."""
    t = texto.strip()
    if len(t) < 3 or "${" in t:
        return False
    return bool(RE_LETRA.search(t))


COM_SOLTOS = False


def main(aplicar):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ti", os.path.join(RAIZ, "tools", "test_interface.py"))
    ti = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(ti)
    except SystemExit: pass

    src = io.open(GAME, encoding="utf-8").read()
    linhas = src.split("\n")
    dono = donos(linhas)
    # Fora dos blocos de catalogo: ali quem traduz e `I18N.aplicarCatalogo`,
    # que troca o campo INTEIRO pela chave `ui.magia.<id>.desc`. Marcar um <b>
    # solto no meio do card so dessincroniza o `pt` do dicionario — ja
    # aconteceu uma vez, com protecao_energia.
    pend = [(l, t) for l, t in ti._literais_pendentes()
            if "<" in t and ">" in t
            and not any(a <= l <= b for a, b in ti.FAIXAS_NAO_PENDENTES)]

    raw, dini, dfim, dic = ler_dicionario()
    usadas = set(dic)
    # pt -> chave ja existente, para o mesmo texto reusar a mesma chave
    por_texto = {}
    for k, v in dic.items():
        por_texto.setdefault(v.get("pt"), k)

    novas, edicoes, sem_alvo = {}, [], 0

    def chave_de(alvo, fn):
        k = por_texto.get(alvo)
        if k:
            return k
        base = "ui.%s.%s" % (area_de(fn), slug(alvo))
        k, n = base, 2
        while k in usadas:
            k = "%s_%d" % (base, n); n += 1
        usadas.add(k)
        por_texto[alvo] = k
        novas[k] = alvo
        return k

    for linha, bloco in pend:
        fn = dono[min(linha, len(dono)) - 1]
        # elemento cujo conteudo inteiro e texto
        elementos = [m.group(3) for m in RE_ELEMENTO.finditer(bloco)
                     if marcavel(m.group(3))]
        # atributo title
        titulos = [m.group(1) for m in RE_TITLE.finditer(bloco)
                   if marcavel(m.group(1))]
        # texto solto ao lado de outra tag (nao coberto pelos dois acima)
        cobertos = set(e.strip() for e in elementos)
        soltos = [m.group(2) for m in RE_TEXTO_SOLTO.finditer(bloco)
                  if marcavel(m.group(2)) and m.group(2).strip() not in cobertos]

        if not (elementos or titulos or soltos):
            sem_alvo += 1
            continue
        for texto in elementos:
            edicoes.append(("elemento", linha, texto, chave_de(texto.strip(), fn)))
        for texto in titulos:
            edicoes.append(("title", linha, texto, chave_de(texto.strip(), fn)))
        # "solto" ENVOLVE o texto num <span> novo: e mudanca de estrutura, nao
        # so de atributo, e a troca roda sobre o ARQUIVO INTEIRO — ou seja,
        # atravessa a fronteira do literal. Ja embrulhou um comentario JS que
        # estava entre dois pedacos de uma concatenacao de strings. Por isso
        # fica atras de --soltos e EXIGE revisao do diff a cada uso.
        if COM_SOLTOS:
            for texto in soltos:
                edicoes.append(("solto", linha, texto, chave_de(texto.strip(), fn)))

    print("blocos de markup pendentes: %d" % len(pend))
    print("  sem elemento marcavel:    %d" % sem_alvo)
    print("textos a marcar:            %d" % len(edicoes))
    print("chaves novas:               %d" % len(novas))
    if not aplicar:
        print("\n(dry-run — passe --aplicar para gravar)")
        return 0

    # A edicao e feita sobre o FONTE INTEIRO, casando o elemento completo. Cada
    # ocorrencia e trocada uma vez; um mesmo texto em dois elementos gera duas
    # edicoes e as duas sao aplicadas, na ordem.
    novo = src
    aplicadas = 0
    for tipo, _linha, texto, chave in edicoes:
        antes = novo
        if tipo == "elemento":
            def troca(m):
                if m.group(3) != texto or "data-i18n" in m.group(2):
                    return m.group(0)
                return "<%s%s data-i18n=\"%s\">%s</%s>" % (
                    m.group(1), m.group(2), chave, m.group(3), m.group(1))
            novo = RE_ELEMENTO.sub(troca, novo)
        elif tipo == "title":
            alvo = 'title="%s"' % texto
            if alvo in novo and 'data-i18n-title="%s"' % chave not in novo:
                novo = novo.replace(alvo, '%s data-i18n-title="%s"' % (alvo, chave))
        else:  # solto — envolve num <span> proprio, sem tocar nos irmaos
            def troca_solto(m):
                if m.group(2) != texto:
                    return m.group(0)
                miolo = m.group(2)
                esq = miolo[:len(miolo) - len(miolo.lstrip())]
                dir_ = miolo[len(miolo.rstrip()):]
                return "%s%s<span data-i18n=\"%s\">%s</span>%s%s" % (
                    m.group(1), esq, chave, miolo.strip(), dir_, m.group(3))
            novo = RE_TEXTO_SOLTO.sub(troca_solto, novo)
        if novo != antes:
            aplicadas += 1

    for chave, txt in novas.items():
        dic.setdefault(chave, {"pt": txt, "en": ""})
    corpo = json.dumps(dic, ensure_ascii=False, indent=2, sort_keys=True)

    if not gravar(GAME, novo): raise SystemExit("nao gravou game.js")
    if not gravar(DICIONARIO, raw[:dini] + corpo + raw[dfim:]):
        raise SystemExit("nao gravou interface.js")
    print("\naplicado (%d textos)." % aplicadas)
    return 0


if __name__ == "__main__":
    COM_SOLTOS = "--soltos" in sys.argv
    sys.exit(main("--aplicar" in sys.argv))
