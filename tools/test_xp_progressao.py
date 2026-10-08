"""Progressão de XP por ND: 13 inimigos equivalentes por herói.

Roda da raiz: python -X utf8 tools/test_xp_progressao.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def room(level, heroes=4):
    r = S.GameRoom("XP-TEST")
    r.players = {
        f"h{i}": {"id": f"h{i}", "alive": True, "level": level}
        for i in range(heroes)
    }
    return r


def award(level, cr, heroes=4):
    return room(level, heroes)._calc_monster_xp({"cr": cr})[0]


print("\n[1] Meta: 13 inimigos de ND igual ao nível por herói")
for level in (1, 2, 3, 5, 10):
    ganho = award(level, level)
    necessario = level * S.XP_POR_NIVEL
    check(f"nível {level}: 52 inimigos para 4 heróis", ganho * 52 == necessario)

print("\n[2] Ajuste por diferença de ND")
check("ND 1 contra grupo nível 2: -10% (18 XP por herói)", award(2, 1) == 18)
check("ND 0.5 contra grupo nível 1: -5% (10 XP por herói)", award(1, .5) == 10)
check("ND 3 contra grupo nível 2: +10% sobre a base do ND 3 (66 XP por herói)", award(2, 3) == 66)
check("ND 10 abaixo do grupo não dá XP", award(10, 0) == 0)

print("\n[3] Base fixa pelo ND, sem multiplicador oculto de nível")
check("ND 1: total base é 80 XP antes da divisão", award(1, 1) * 4 == S.XP_MONSTRO_POR_ND)
check("ND 2 em grupo nível 2: 40 XP por herói", award(2, 2) == 40)
check("fallback de tier mantém ND unificado", room(1)._calc_monster_xp({"tier": 2})[0] == 20)

print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
sys.exit(1 if FAIL else 0)
