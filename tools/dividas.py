"""Placar ÚNICO das dívidas de idioma — servidor + cliente + dicionário.

Roda da raiz:  python tools/dividas.py [--json] [--strict]

  (sem flag)  relatório legível, agrupado por arquivo e função; sai com 0
  --json      a mesma lista em JSON (para outra ferramenta ou para diff)
  --strict    sai com 1 se houver QUALQUER dívida (uso em pre-commit / CI)

POR QUE ISTO EXISTE
  As sobras de tradução viviam espalhadas em três suítes vermelhas
  (test_erros [4], test_narracao [3], test_interface [1]) que só CONTAVAM.
  Quem fechava uma feature não tinha onde olhar "o que ficou em português
  nesta área?" — e a dívida acumulava até alguém rodar o jogo em inglês.
  Este script junta tudo numa lista só, com linha e função, para traduzir ao
  fechar cada feature em vez de num lote de 500 (2026-09-14).

DE ONDE VÊM OS NÚMEROS — sempre dos mesmos instrumentos das suítes, nunca de
uma heurística própria (o Lote 3 pagou caro por um migrador com heurística):
  • server.py, erros ........ RE_MSG / RE_ERR de test_erros (texto fixo em
                               `"msg": "…"` e `await err("…")`, inclusive f-string)
  • server.py, narração ..... varredura por `ast` de test_narracao (gm_say sem T/gm)
  • server.py, dados ........ `"label": "…"` cru num contexto de `dice_roll`
  • server.py, órfãs ........ T("x") sem a chave no dicionário fundido
  • game.js, interface ...... test_interface._literais_pendentes (js_strings +
                               vocabulário) atribuído à função de topo
  • dicionário .............. chave sem `en` ou com {parâmetros} diferentes
"""
import ast, io, json, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import test_erros as TE
import test_narracao as TN
import test_interface as TI

FONTE = io.open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
LINHAS_SRV = FONTE.split("\n")


def _linha_de(pos):
    return FONTE.count("\n", 0, pos) + 1


def _funcao_servidor(linha):
    """Nome do método/função que contém a linha (o `def` mais próximo acima)."""
    for i in range(linha - 1, -1, -1):
        m = re.match(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", LINHAS_SRV[i])
        if m: return m.group(1)
    return "módulo"


def erros_servidor():
    out = []
    for rx in (TE.RE_MSG, TE.RE_ERR):
        for m in rx.finditer(FONTE):
            l = _linha_de(m.start())
            out.append({"onde": "server.py", "tipo": "erro", "linha": l,
                        "funcao": _funcao_servidor(l), "texto": m.group(2)})
    return out


def _tardio(n):
    """Texto TARDIO (traduzido na hora de serializar): T(...), gm(...), variável,
    ou um `T(...) if x else T(...)`."""
    if isinstance(n, ast.Name): return True
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("T", "gm"): return True
    if isinstance(n, ast.IfExp): return _tardio(n.body) and _tardio(n.orelse)
    return False


def narracao_servidor():
    out = []
    for no in ast.walk(ast.parse(FONTE)):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                and no.func.attr == "gm_say" and len(no.args) == 1):
            continue
        a = no.args[0]
        if _tardio(a): continue
        txt = (ast.get_source_segment(FONTE, a) or "?").replace("\n", " ")
        out.append({"onde": "server.py", "tipo": "narracao", "linha": no.lineno,
                    "funcao": _funcao_servidor(no.lineno), "texto": txt})
    return out


RE_LABEL_CRU = re.compile(r'"label":\s*f?"([^"]{2,120})"')


def dados_servidor():
    """Rótulo de `dice_roll` ainda em texto cru (os 42 originais viraram T("dado.…"))."""
    out = []
    for i, l in enumerate(LINHAS_SRV):
        m = RE_LABEL_CRU.search(l)
        if not m: continue
        ctx = "\n".join(LINHAS_SRV[max(0, i - 3):i + 1])
        if "dice_roll" not in ctx: continue
        out.append({"onde": "server.py", "tipo": "dado", "linha": i + 1,
                    "funcao": _funcao_servidor(i + 1), "texto": m.group(1)})
    return out


def orfas_servidor():
    usadas = set(re.findall(r'\bT\(\s*"([^"]+)"', FONTE))
    usadas = {k for k in usadas if not k.endswith(".")}
    out = []
    for k in sorted(k for k in usadas if k not in S.LANG_STRINGS):
        pos = FONTE.find('T("%s"' % k)
        out.append({"onde": "server.py", "tipo": "chave_orfa", "linha": _linha_de(pos) if pos >= 0 else 0,
                    "funcao": _funcao_servidor(_linha_de(pos)) if pos >= 0 else "?", "texto": k})
    return out


def interface_cliente():
    dono, atual = {}, "topo"
    donos = []
    for l in TI.LINHAS:
        m = TI.RE_FN.match(l)
        if m: atual = m.group(1) or m.group(2)
        elif re.match(r"^[}\]]", l): atual = "topo"
        donos.append(atual)
    out = []
    for linha, txt in TI._literais_pendentes():
        fn = donos[min(linha, len(donos)) - 1]
        out.append({"onde": "game.js", "tipo": "interface", "linha": linha,
                    "funcao": fn, "texto": txt.replace("\n", "⏎")[:110]})
    return out


def dicionario():
    out = []
    for k, v in S.LANG_STRINGS.items():
        pt, en = (v or {}).get("pt", ""), (v or {}).get("en", "")
        if not en:
            out.append({"onde": "src/lang", "tipo": "sem_en", "linha": 0, "funcao": k.split(".")[0], "texto": f"{k} = {pt[:70]!r}"})
            continue
        if set(re.findall(r"\{(\w+)\}", pt)) != set(re.findall(r"\{(\w+)\}", en)):
            out.append({"onde": "src/lang", "tipo": "params", "linha": 0, "funcao": k.split(".")[0], "texto": k})
    return out


def coletar():
    return (erros_servidor() + narracao_servidor() + dados_servidor() + orfas_servidor()
            + interface_cliente() + dicionario())


TITULO = {"erro": "erros do servidor (msg/err cru)", "narracao": "narração do servidor (gm_say cru)",
          "dado": "rótulos de dado (dice_roll cru)", "chave_orfa": "chaves T(…) sem entrada no dicionário",
          "interface": "interface do cliente (game.js)", "sem_en": "chaves sem tradução `en`",
          "params": "chaves com {parâmetros} diferentes entre pt e en"}


def relatorio(itens):
    print("=" * 66); print("  DÍVIDAS DE IDIOMA — o que ainda sai em português"); print("=" * 66)
    if not itens:
        print("\n  nada pendente. 🎉"); return
    por_tipo = {}
    for it in itens: por_tipo.setdefault(it["tipo"], []).append(it)
    for tipo in ("erro", "narracao", "dado", "chave_orfa", "interface", "sem_en", "params"):
        lst = por_tipo.get(tipo)
        if not lst: continue
        print(f"\n▶ {TITULO[tipo]} — {len(lst)}")
        por_fn = {}
        for it in lst: por_fn.setdefault(it["funcao"], []).append(it)
        for fn, grupo in sorted(por_fn.items(), key=lambda kv: -len(kv[1])):
            print(f"   {fn}  ({len(grupo)})")
            for it in sorted(grupo, key=lambda x: x["linha"]):
                loc = f"L{it['linha']}" if it["linha"] else "—"
                print(f"      {loc:>7}  {it['texto']}")
    print("\n" + "-" * 66)
    resumo = ", ".join(f"{len(v)} {k}" for k, v in por_tipo.items())
    print(f"  TOTAL: {len(itens)}  ({resumo})")
    print("  Para traduzir em lote: python tools/migrar_interface.py --aplicar  (texto puro do game.js)")


if __name__ == "__main__":
    itens = coletar()
    if "--json" in sys.argv:
        print(json.dumps(itens, ensure_ascii=False, indent=1))
    else:
        relatorio(itens)
    sys.exit(1 if ("--strict" in sys.argv and itens) else 0)
