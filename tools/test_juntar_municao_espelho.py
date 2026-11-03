"""Paridade: `GS.mesmaPilhaMunicao` (cliente) decide igual a `_ammo_stack_key` (servidor).

O inventário usa o espelho para escolher entre juntar e equipar/reordenar; se ele
discordar do servidor, soltar uma pilha sobre a pilha equipada trocaria em vez de
juntar (ou o contrário). Roda da raiz: python -X utf8 tools/test_juntar_municao_espelho.py"""
import json, os, subprocess, sys
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def m(ident, n=3, **extra):
    it = deepcopy(next(i for i in S.SHOP_AMMO if i["id"] == ident))
    it["ammo_count"] = n
    it.update(extra)
    return it

v1, v2 = list(S.VENENOS)[:2]
PARES = [
    ("mesmo tipo, quantidades diferentes", m("virotes", 3), m("virotes", 7)),
    ("comum × mágica", m("virotes"), m("virotes_magicos")),
    ("mágica +1 × mágica +2", m("virotes_magicos"), m("virotes_magicos_mais_2")),
    ("comum × incendiária", m("virotes"), m("virote_incendiario")),
    ("comum × prata", m("virotes"), m("virotes_prata")),
    ("flechas × virotes", m("flechas"), m("virotes")),
    ("mesmo veneno", m("virotes", poison_ids=[v1]), m("virotes", poison_ids=[v1])),
    ("venenos diferentes", m("virotes", poison_ids=[v1]), m("virotes", poison_ids=[v2])),
    ("dois venenos em ordens diferentes", m("virotes", poison_ids=[v1, v2]), m("virotes", poison_ids=[v2, v1])),
    ("envenenada × comum", m("virotes", poison_ids=[v1]), m("virotes")),
    ("munição × item que não é munição", m("virotes"), {"id": "dagger", "item_slot": "weapon"}),
]


def main():
    js = """
    const fs = require('fs'), path = require('path');
    global.window = {};
    const GS = eval(fs.readFileSync(path.join(process.argv[1], 'src', 'gameState.js'), 'utf8') + '; GS');
    const pares = JSON.parse(fs.readFileSync(0, 'utf8'));
    process.stdout.write(JSON.stringify(pares.map(([a, b]) => GS.mesmaPilhaMunicao(a, b))));
    """
    entrada = json.dumps([[a, b] for _, a, b in PARES])
    out = subprocess.run(["node", "-e", js, RAIZ], input=entrada, capture_output=True,
                         text=True, encoding="utf-8")
    if out.returncode != 0:
        check("node rodou o espelho", False, out.stderr[-800:])
        return
    cliente = json.loads(out.stdout)
    for (rotulo, a, b), c in zip(PARES, cliente):
        ka = S._ammo_stack_key(a)
        servidor = ka is not None and ka == S._ammo_stack_key(b)
        check(f"{rotulo}: servidor={servidor} cliente={c}", servidor == c)


main()
print(f"\n=== {PASS} passou, {FAIL} falhou ===")
sys.exit(1 if FAIL else 0)
