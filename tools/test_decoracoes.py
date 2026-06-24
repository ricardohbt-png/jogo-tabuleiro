"""Testes das decorações de masmorra.
Roda da raiz: python tools/test_decoracoes.py"""
import sys, os, asyncio, copy
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, WALL, FLOOR, DOOR

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def test_catalog():
    print("\n[A1] DECOR_TYPES")
    d = server.DECOR_TYPES
    check("22 tipos", len(d) == 22)
    check("ids esperados presentes", all(k in d for k in (
        "cama", "lareira", "fonte", "fogueira", "tumba", "mesa_cadeiras",
        "estante", "carroca", "coluna", "barril", "arca_tesouros", "cama_casal",
        "estante_livros", "altar", "trono", "gaiola", "grades_prisao",
        "estante_armas", "mesa_tortura", "mesa_quimica", "arvore", "arvore_grande")))
    check("fonte é fountain", d["fonte"]["special"] == "fountain")
    check("fogueira é campfire e pisável", d["fogueira"]["special"] == "campfire" and d["fogueira"]["pisavel"])
    check("fonte size 2x2", d["fonte"]["size"] == [2, 2])
    check("cama size 1x2", d["cama"]["size"] == [1, 2])
    check("coluna alta", d["coluna"]["alto"] is True)
    check("grades não-alta", d["grades_prisao"]["alto"] is False)
    check("todo tipo tem emoji/nome/gira/loot_capaz", all(
        set(("nome", "emoji", "size", "gira", "alto", "pisavel", "loot_capaz", "special")) <= set(v)
        for v in d.values()))
    check("só fogueira é pisável", [k for k, v in d.items() if v["pisavel"]] == ["fogueira"])

def main():
    test_catalog()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
