"""Valida a configuração autoral de Voo do editor.

Roda da raiz: python tools/test_voo_editor.py
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def ficha(**extra):
    base = {
        "type": "criatura_voadora_teste",
        "name": "Criatura Voadora de Teste",
        "special_abilities": [],
        "attacks": [{"name": "Garra", "damage": "1d4", "num_attacks": 1}],
    }
    base.update(extra)
    return base


def main():
    print("=== TESTE — Configuração de Voo no editor ===")

    ok, result = server._validate_custom_monster(ficha(
        voo=True,
        altura_inicial=4,
        altura_max=9,
        pode_alterar_altura=False,
        custo_mov_altura=2,
        ignora_obstaculos_voo=True,
    ))
    check("ficha voadora é aceita", ok)
    check("altura inicial preservada", ok and result["altura_inicial"] == 4)
    check("altura máxima preservada", ok and result["altura_max"] == 9)
    check("pode_alterar_altura preservado", ok and result["pode_alterar_altura"] is False)
    check("custo de altura preservado", ok and result["custo_mov_altura"] == 2)
    check("ignora obstáculos preservado", ok and result["ignora_obstaculos_voo"] is True)

    ok, result = server._validate_custom_monster(ficha())
    check("ficha sem Voo fica no chão", ok and result["voo"] is False)
    check("ficha sem Voo normaliza altura para zero", ok and result["altura_inicial"] == 0 and result["altura_max"] == 0)
    check("ficha sem Voo não altera altura", ok and result["pode_alterar_altura"] is False)

    ok, _ = server._validate_custom_monster(ficha(voo=True, altura_inicial=8, altura_max=3))
    check("altura máxima menor que a inicial é recusada", not ok)

    editor_path = os.path.join(os.path.dirname(__file__), "editor_monster_editor.js")
    with open(editor_path, encoding="utf-8") as handle:
        editor = handle.read()
    for control in ("me-voo", "me-altura-inicial", "me-altura-max",
                    "me-pode-alterar-altura", "me-custo-mov-altura",
                    "me-ignora-obstaculos-voo"):
        check(f"editor possui controle {control}", f'id="{control}"' in editor)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
