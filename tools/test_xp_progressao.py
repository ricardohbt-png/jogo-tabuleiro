"""Progressão de XP no modelo D&D 3.5. Roda da raiz: python tools/test_xp_progressao.py
Spec: docs/superpowers/specs/2026-09-26-progressao-xp-dnd35-design.md
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S                       # noqa: E402
from server import GameRoom, make_player  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    r = GameRoom("XP")
    async def noop(*a, **k):
        pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.phase = "playing"
    return r


# ─── [1] Regras puras ───────────────────────────────────────────────────────
def secao_regras():
    print("\n[1] Regras puras — xp_premio / xp_limiar / nivel_por_xp")
    check("nível 1 × ND 1 = 300", S.xp_premio(1, 1) == 300)
    check("ND igual ao nível = 300 × nível", all(S.xp_premio(n, n) == 300 * n for n in range(1, 21)))
    check("nível 1 × ND 3 = 2× o ND 1 (dobra a cada 2 NDs)", S.xp_premio(1, 3) == 600)
    check("ND fracionário = fração do ND 1 (goblin ¼ no nível 1 → 75)", S.xp_premio(1, 0.25) == 75)
    check("ND fracionário segue o nível (¼ no nível 5 → 94)", S.xp_premio(5, 0.25) == 94)
    check("ND 0 não rende", S.xp_premio(1, 0) == 0)
    check("8 NDs abaixo não rende (nível 9 × ND 1)", S.xp_premio(9, 1) == 0)
    check("7 NDs abaixo ainda rende (nível 8 × ND 1)", S.xp_premio(8, 1) > 0)
    check("teto em nível + 7 (ND 20 no nível 1 = ND 8)", S.xp_premio(1, 20) == S.xp_premio(1, 8) == 3394)
    check("nível acima de 20 usa a linha do 20", S.xp_premio(38, 20) == S.xp_premio(20, 20))
    check("ND inválido não rende", S.xp_premio(1, "abc") == 0)
    check("parte por herói divide pelos vivos", S.xp_por_heroi(1, 1, 4) == 75)
    check("parte por herói tem mínimo 1", S.xp_por_heroi(1, 0.01, 6) == 1)
    check("parte sem prêmio é 0", S.xp_por_heroi(9, 1, 4) == 0)
    check("limiares 0/1000/3000/6000/10000",
          [S.xp_limiar(n) for n in range(1, 6)] == [0, 1000, 3000, 6000, 10000])
    check("limiar do nível 20 = 190000", S.xp_limiar(20) == 190000)
    check("nivel_por_xp nas bordas",
          [S.nivel_por_xp(x) for x in (0, 999, 1000, 2999, 3000)] == [1, 1, 2, 2, 3])
    check("nivel_por_xp tem teto 20", S.nivel_por_xp(10 ** 9) == S.XP_NIVEL_MAX == 20)
    check("xp_proximo_nivel", S.xp_proximo_nivel(1) == 1000 and S.xp_proximo_nivel(20) is None)
    check("migração: nível 2 com 30/60 → 2000", S.xp_migrado(2, 30) == 2000)
    check("migração: sobra acima do limiar antigo trava em 100%", S.xp_migrado(1, 999) == 1000)
    check("migração: nível 20+ fica no limiar do 20", S.xp_migrado(38, 5) == S.xp_limiar(20))


async def main():
    secao_regras()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
