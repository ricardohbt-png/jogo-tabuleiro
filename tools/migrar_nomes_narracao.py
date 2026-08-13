"""Troca, dentro dos T("narracao.…"), a passagem CRUA de nome de catálogo pelo
helper que o resolve no idioma de quem lê (etapa 4c do idioma).

Roda da raiz:  python tools/migrar_nomes_narracao.py

Uso ÚNICO. Cobre só o acesso DIRETO a dict — `m['name']`, `item['name']`,
`alvo.get('name')`, `alvo.get('name', 'Alvo')`, `a['nome']`… Os que chegam por
variável local ficam de fora de propósito: cada um exige olhar a atribuição, e é
a Task 6 do plano.

Nome de JOGADOR não entra: é escolhido pelo jogador e sai cru, que é o certo.

POR QUE NÃO É REGEX PURO: há `.get` ANINHADO no fonte —
`target.get('name', target.get('nome', 'Alvo'))` — e um `[^)]*` para o default
para no primeiro `)`, deixando `, 'Alvo'))` solto e o arquivo sem parsear. A
varredura conta parênteses e ignora os que estão dentro de aspas, do mesmo jeito
que o conferidor de diff da etapa 4b-i.

Três travas, porque o script reescreve o arquivo central do jogo:
  1. expressão COMPOSTA (`x.get('name') or y['nome']`) é pulada e relatada —
     migrar só o primeiro pedaço deixaria a frase meio traduzida;
  2. expressão que não seja EXATAMENTE um acesso de nome fica intocada;
  3. o resultado passa por ast.parse ANTES de ir para o disco.
"""
import ast, io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "server.py")

# Variáveis que guardam um JOGADOR — o nome sai cru.
JOGADOR = {"p", "caster", "next_p", "bardo", "richard", "jogador", "rescuer",
           "dono", "curador", "heroi"}
# Variáveis que guardam um ITEM.
ITEM = {"item", "defn", "scroll", "elixir", "potion", "it", "gi", "arma",
        "weapon", "off", "peca", "pot"}
# O resto de quem tem ['name']/['nome'] é criatura: m, alvo, target, t, c,
# monstro, atacante, ator, extra, obj, tgt, a, animado, criatura, preso…
# O `nome_criatura` despacha pela FORMA do dict, então monstro, servo animado e
# até um HERÓI que caia no mesmo parâmetro entram por aqui sem o script precisar
# distingui-los — é justamente o ponto do despacho em runtime.

RE_SUB = re.compile(r"""^(\w+)\[['"](?:name|nome)['"]\]$""")
RE_GET = re.compile(r"""^(\w+)\.get\(['"](?:name|nome)['"]""")


def _fim_da_chamada(texto, i):
    """Índice logo após o ')' que fecha o '(' em texto[i]. Ignora parênteses
    dentro de aspas."""
    prof, aspas, k = 0, None, i
    while k < len(texto):
        c = texto[k]
        if aspas:
            if c == "\\":
                k += 2; continue
            if c == aspas:
                aspas = None
        elif c in "'\"":
            aspas = c
        elif c == "(":
            prof += 1
        elif c == ")":
            prof -= 1
            if prof == 0:
                return k + 1
        k += 1
    return -1


def _args_de(corpo):
    """Fatia o corpo de uma chamada nos argumentos de PRIMEIRO nível.
    Devolve [(inicio, fim)] relativos ao corpo."""
    fatias, prof, aspas, ini = [], 0, None, 0
    for k, c in enumerate(corpo):
        if aspas:
            if c == "\\":
                continue
            if c == aspas:
                aspas = None
        elif c in "'\"":
            aspas = c
        elif c in "([{":
            prof += 1
        elif c in ")]}":
            prof -= 1
        elif c == "," and prof == 0:
            fatias.append((ini, k)); ini = k + 1
    fatias.append((ini, len(corpo)))
    return fatias


def helper_para(var):
    """Qual helper resolve o nome desta variável. None = deixa cru."""
    if var in JOGADOR:
        return None
    if var in ITEM:
        return "nome_item"
    return "nome_criatura"


def main():
    fonte = io.open(FONTE, encoding="utf-8").read()
    trocas, pulados, compostas = 0, [], []
    saida, pos = [], 0

    for mt in re.finditer(r'T\(\s*"narracao\.[^"]+"', fonte):
        abre = fonte.index("(", mt.start())
        fim = _fim_da_chamada(fonte, abre)
        if fim < 0:
            continue
        corpo = fonte[abre + 1:fim - 1]
        novo_corpo, ult = [], 0
        for ini, f in _args_de(corpo):
            arg = corpo[ini:f]
            nome_param, _, expr = arg.partition("=")
            e = expr.strip()
            if not _ or "=" not in arg:
                continue
            if " or " in e:
                compostas.append(e[:70]); continue
            m1 = RE_SUB.match(e) or RE_GET.match(e)
            if not m1:
                continue
            # Um .get(...) só vale se a expressão INTEIRA for a chamada.
            if RE_GET.match(e) and _fim_da_chamada(e, e.index("(")) != len(e):
                compostas.append(e[:70]); continue
            var = m1.group(1)
            h = helper_para(var)
            if h is None:
                pulados.append(var); continue
            novo_corpo.append(corpo[ult:ini])
            novo_corpo.append(f"{arg[:len(nome_param)]}={h}({var})")
            ult = f
            trocas += 1
        if ult:
            novo_corpo.append(corpo[ult:])
            saida.append(fonte[pos:abre + 1]); saida.append("".join(novo_corpo))
            saida.append(")"); pos = fim

    saida.append(fonte[pos:])
    novo = "".join(saida)

    try:
        ast.parse(novo)
    except SyntaxError as e:
        print(f"❌ o resultado NÃO parseia ({e}) — nada foi escrito.")
        return 1

    io.open(FONTE, "w", encoding="utf-8", newline="\n").write(novo)
    print(f"{trocas} parâmetros trocados.")
    print(f"{len(pulados)} deixados crus (jogador): {', '.join(sorted(set(pulados)))}")
    if compostas:
        print(f"\n⚠️  {len(compostas)} expressão(ões) composta(s)/aninhada(s) pulada(s) "
              f"— revise à mão:")
        for c in sorted(set(compostas))[:12]:
            print("   ", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
