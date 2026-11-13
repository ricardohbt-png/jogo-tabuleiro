"""Executor único da bateria de testes (usado localmente e no GitHub Actions).

Descobre tools/test_*.py e tools/test_*.js, roda cada um num processo próprio
(da raiz do projeto, com tempo limite) e resume o resultado. Um teste falha
quando: sai com código != 0, estoura o tempo, ou imprime um placar com falhas
("3 falharam", "2 FALHAS") ou o marcador ❌ — vários testes antigos só relatam
no texto, e um laço que olhasse só o código de saída os daria como verdes.

Testes que dependem de algo fora do repositório (servidor já ligado na 8765,
navegador, rede) ficam em tools/testes_ignorados.txt, um por linha, com o
motivo depois de "#". Nada é ignorado em silêncio: o resumo lista cada um.

Uso (da raiz):
    python -X utf8 tools/rodar_testes.py                 # tudo
    python -X utf8 tools/rodar_testes.py -k veneno       # só nomes que contêm "veneno"
    python -X utf8 tools/rodar_testes.py -j 1            # sem paralelismo
    python -X utf8 tools/rodar_testes.py --lote 1/4      # fatia 1 de 4 (matriz do CI)
"""
import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(RAIZ, "tools")
IGNORADOS = os.path.join(TOOLS, "testes_ignorados.txt")
# Só linhas de PLACAR contam ("54 passaram, 2 falharam", "=== 3 OK / 1 FALHAS ==="):
# uma linha de teste que passa pode dizer "CD 15 falhou" sem ser falha do teste.
RE_PLACAR = re.compile(
    r"(?:passaram|passou|passed|OK|ok)\b[^\n]*?[,/]\s*([1-9]\d*)\s+(?:falharam|falhou|FALHAS|failed)\b")


def descobrir():
    return sorted(f for f in os.listdir(TOOLS)
                  if f.startswith("test_") and f.endswith((".py", ".js")))


def carregar_ignorados():
    ign = {}
    if os.path.exists(IGNORADOS):
        for linha in open(IGNORADOS, encoding="utf8"):
            nome, _, motivo = linha.partition("#")
            if nome.strip():
                ign[nome.strip()] = motivo.strip()
    return ign


def rodar_uma(nome, limite):
    cmd = ([sys.executable, "-X", "utf8", os.path.join("tools", nome)]
           if nome.endswith(".py") else ["node", os.path.join("tools", nome)])
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, timeout=limite, env=env)
        saida = (r.stdout + b"\n" + r.stderr).decode("utf8", "replace")
        motivo = None
        if r.returncode != 0:
            motivo = f"código de saída {r.returncode}"
        elif RE_PLACAR.search(saida) or "❌" in saida:
            motivo = "o próprio teste relatou falhas no texto"
        return nome, motivo, saida, time.time() - t0
    except subprocess.TimeoutExpired as e:
        saida = ((e.stdout or b"") + b"\n" + (e.stderr or b"")).decode("utf8", "replace")
        return nome, f"estourou {limite}s", saida, time.time() - t0


def rodar(nome, limite, tentativas):
    """Roda o teste; se falhar, tenta de novo até `tentativas` vezes no total.
    Passou só na repetição = "instável" (o resumo lista; não derruba a bateria)."""
    for n in range(1, tentativas + 1):
        nome_, motivo, saida, dur = rodar_uma(nome, limite)
        if not motivo:
            return nome_, None, saida, dur, (n > 1)
    return nome_, motivo, saida, dur, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="", help="só testes cujo nome contém este texto")
    ap.add_argument("-j", type=int, default=max(1, min(4, (os.cpu_count() or 2))))
    ap.add_argument("--limite", type=int, default=300, help="segundos por teste")
    ap.add_argument("--lote", default="", help="N/M: roda só a fatia N de M")
    ap.add_argument("--tentativas", type=int, default=2, help="vezes que um teste vermelho é rodado antes de valer")
    ap.add_argument("--cauda", type=int, default=25, help="linhas finais mostradas por falha")
    a = ap.parse_args()

    ign = carregar_ignorados()
    todos = [n for n in descobrir() if a.k in n]
    if a.lote:
        n, m = (int(x) for x in a.lote.split("/"))
        todos = [t for i, t in enumerate(todos) if i % m == n - 1]
    pular = [t for t in todos if t in ign]
    fila = [t for t in todos if t not in ign]
    print(f"{len(fila)} testes a rodar, {len(pular)} ignorados, {a.j} em paralelo\n", flush=True)

    falhas, lentos, instaveis, t0 = [], [], [], time.time()
    with cf.ThreadPoolExecutor(max_workers=a.j) as ex:
        for nome, motivo, saida, dur, instavel in ex.map(lambda t: rodar(t, a.limite, a.tentativas), fila):
            lentos.append((dur, nome))
            if motivo:
                falhas.append(nome)
                print(f"FALHOU {nome} — {motivo} ({dur:.0f}s)")
                print("   " + "\n   ".join(saida.strip().splitlines()[-a.cauda:]) + "\n", flush=True)
            else:
                if instavel:
                    instaveis.append(nome)
                print(f"{'INSTAVEL' if instavel else 'ok      '} {nome} ({dur:.0f}s)", flush=True)

    print(f"\n=== {len(fila) - len(falhas)} passaram, {len(falhas)} falharam, "
          f"{len(pular)} ignorados, {time.time() - t0:.0f}s ===")
    for t in pular:
        print(f"  ignorado: {t} # {ign[t]}")
    if instaveis:
        print("INSTAVEIS (falharam e passaram na repetição; vale consertar):\n  " + "\n  ".join(instaveis))
    print("mais lentos:", ", ".join(f"{n} {d:.0f}s" for d, n in sorted(lentos, reverse=True)[:5]))
    if falhas:
        print("\nFALHARAM:\n  " + "\n  ".join(falhas))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
