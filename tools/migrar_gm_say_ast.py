"""Migra para T("narracao.…") os gm_say que a etapa 4b-i deixou de fora:
multilinha, f-string que atravessa a linha e concatenação.

Roda da raiz:  python tools/migrar_gm_say_ast.py

Uso ÚNICO (etapa 4b-ii).

POR QUE `ast` E NÃO REGEX: a etapa 4c provou o limite do regex — um `[^)]*`
para o default de um `.get` aninhado deixou o arquivo sem parsear. Para o `ast`,
f-string multilinha, f-string de uma linha e concatenação implícita são a MESMA
árvore (`JoinedStr`), então as três formas saem pela mesma máquina, sem adivinhar
onde a string começa nem como os fragmentos se juntam.

ARMADILHA DE POSIÇÃO: o `ast` reporta `col_offset` em BYTES UTF-8, não em
caracteres. O server.py é cheio de emoji e acento, então fatiar por índice de
caractere corromperia o arquivo em silêncio. Todo o corte é feito em bytes.

A reescrita é de trás para frente, para os offsets anteriores não invalidarem, e
toca só o span do argumento — todo o resto fica byte-idêntico.
"""
import ast, io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
from migrar_narracao import slug, nome_param, escrever, ler_existente

FONTE = os.path.join(RAIZ, "server.py")
RE_INTERP = re.compile(r"\{([^{}]+)\}")


def _partes(no, src):
    """(texto_lógico, [(nome_param, expressão)]) de um JoinedStr/Constant/BinOp.

    Devolve None para qualquer forma que não seja só texto + interpolação — o
    script prefere pular e relatar a adivinhar."""
    if isinstance(no, ast.Constant) and isinstance(no.value, str):
        return no.value, []
    if isinstance(no, ast.BinOp) and isinstance(no.op, ast.Add):
        e = _partes(no.left, src)
        d = _partes(no.right, src)
        if e is None or d is None:
            return None
        return e[0] + d[0], e[1] + d[1]
    if not isinstance(no, ast.JoinedStr):
        return None
    texto, pares, usados = "", [], {}
    for v in no.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            texto += v.value
        elif isinstance(v, ast.FormattedValue):
            expr = ast.get_source_segment(src, v.value)
            # !r e format_spec mudam o texto de um jeito que a chave não captura.
            if expr is None or v.format_spec is not None or v.conversion not in (-1,):
                return None
            n = nome_param(expr)
            base, i = n, 2
            while n in usados and usados[n] != expr:
                n = f"{base}_{i}"; i += 1
            usados[n] = expr
            texto += "{" + n + "}"
            pares.append((n, expr))
        else:
            return None
    return texto, list(dict.fromkeys(pares))


def coletar(src):
    """[(l1, c1, l2, c2, texto, pares)] de cada gm_say migrável, e os pulados."""
    achados, pulados = [], []
    for no in ast.walk(ast.parse(src)):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                and no.func.attr == "gm_say" and len(no.args) == 1):
            continue
        arg = no.args[0]
        # Já migrado (T(...)), vindo do pool gm(...) ou de variável: fora.
        if isinstance(arg, (ast.Name, ast.Call, ast.Attribute, ast.Subscript)):
            continue
        r = _partes(arg, src)
        if r is None:
            seg = ast.get_source_segment(src, arg) or "?"
            pulados.append(seg.replace("\n", " ")[:70]); continue
        achados.append((arg.lineno, arg.col_offset, arg.end_lineno,
                        arg.end_col_offset, r[0], r[1]))
    return achados, pulados


def main():
    src = io.open(FONTE, encoding="utf-8").read()
    achados, pulados = coletar(src)

    dic = ler_existente()
    por_chave = {k: v["pt"] for k, v in dic.items()}
    trocas = []
    for l1, c1, l2, c2, texto, pares in achados:
        ch = "narracao." + slug(RE_INTERP.sub("", texto))
        if ch in por_chave and por_chave[ch] != texto:
            base, i = ch, 2
            while f"{base}_{i}" in por_chave and por_chave[f"{base}_{i}"] != texto:
                i += 1
            ch = f"{base}_{i}"
        por_chave[ch] = texto
        dic[ch] = {"pt": texto, "en": dic.get(ch, {}).get("en", "")}
        args = ", ".join(f"{n}={e}" for n, e in pares)
        trocas.append((l1, c1, l2, c2,
                       f'T("{ch}"{", " + args if args else ""})'))

    # ── corte em BYTES (col_offset do ast é byte UTF-8) ──────────────────────
    linhas_b = [l.encode("utf-8") for l in src.split("\n")]
    pref = [0]
    for lb in linhas_b:
        pref.append(pref[-1] + len(lb) + 1)          # +1 pelo \n
    def off(l, c):
        return pref[l - 1] + c

    saida_b = src.encode("utf-8")
    for l1, c1, l2, c2, novo in sorted(trocas, key=lambda t: (t[0], t[1]), reverse=True):
        saida_b = saida_b[:off(l1, c1)] + novo.encode("utf-8") + saida_b[off(l2, c2):]
    saida = saida_b.decode("utf-8")

    try:
        ast.parse(saida)
    except SyntaxError as e:
        print(f"❌ o resultado NÃO parseia ({e}) — nada foi escrito.")
        return 1

    io.open(FONTE, "w", encoding="utf-8", newline="\n").write(saida)
    escrever(dic)

    print(f"{len(trocas)} sites migrados → {len(set(por_chave))} chaves no dicionário.")
    print(f"{sum(1 for v in dic.values() if not v['en'])} chaves sem tradução.")
    if pulados:
        print(f"\n⚠️  {len(pulados)} forma(s) não reconhecida(s) — revise à mão:")
        for p in sorted(set(pulados))[:12]:
            print("   ", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
