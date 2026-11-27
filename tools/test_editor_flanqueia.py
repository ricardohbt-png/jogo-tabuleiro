"""Campo `flanqueia` no editor de criaturas (2026-11-26).

O motor já lia `flanqueia` na ficha (True liga, False desliga, ausente = padrão da espécie
e do perfil de IA); o validador do editor o descartava ao salvar. Roda:
python -X utf8 tools/test_editor_flanqueia.py
"""
from copy import deepcopy
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S  # noqa: E402

FALHAS = []


def check(nome, cond):
    print(("  ✅ " if cond else "  ❌ ") + nome)
    if not cond:
        FALHAS.append(nome)


def ficha_nova(**extra):
    raw = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "goblin"))
    for k in ("overwrite_native", "original_type", "_personalizado"):
        raw.pop(k, None)
    raw.update({"type": "teste_flanqueia", "name": "Teste Flanqueia", "ai_type": "agressivo"})
    raw.update(extra)
    return raw


def sobrescrita_bandido(**extra):
    raw = deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "bandido"))
    raw.pop("_personalizado", None)
    raw.update({"overwrite_native": True, "original_type": "bandido"})
    raw.update(extra)
    return raw


def flanqueia_em_jogo(ficha):
    sala = S.GameRoom("FLQ")
    m = S.make_monster(dict(ficha, _personalizado=True), {"id": 0, "x": 0, "y": 0, "w": 5, "h": 5, "cx": 2, "cy": 2})
    return sala._monster_flanqueia(m)


def main():
    print("\n[1] O validador preserva o campo")
    ok, f = S._validate_custom_monster(ficha_nova(flanqueia=True))
    check("Sim: aceito e gravado como True", ok and f.get("flanqueia") is True)
    ok, f = S._validate_custom_monster(ficha_nova(flanqueia=False))
    check("Não: aceito e gravado como False", ok and f.get("flanqueia") is False)
    ok, f = S._validate_custom_monster(ficha_nova())
    check("Padrão: o campo não é gravado (fichas antigas ficam idênticas)", ok and "flanqueia" not in f)
    ok, f = S._validate_custom_monster(ficha_nova(flanqueia="sim"))
    check("valor que não é verdadeiro/falso é descartado", ok and "flanqueia" not in f)

    print("\n[2] No motor")
    _, f = S._validate_custom_monster(ficha_nova(flanqueia=True))
    check("ficha com Sim flanqueia em jogo", flanqueia_em_jogo(f) is True)
    _, f = S._validate_custom_monster(ficha_nova())
    check("ficha agressiva no Padrão não flanqueia", flanqueia_em_jogo(f) is False)
    _, f = S._validate_custom_monster(ficha_nova(ai_profile="tatico"))
    check("perfil tático no Padrão segue flanqueando", flanqueia_em_jogo(f) is True)
    _, f = S._validate_custom_monster(ficha_nova(ai_profile="tatico", flanqueia=False))
    check("perfil tático com Não deixa de flanquear", flanqueia_em_jogo(f) is False)
    for perfil in ("emboscador", "cacador"):
        _, f = S._validate_custom_monster(ficha_nova(ai_profile=perfil))
        check(f"perfil {perfil} no Padrão flanqueia (o editor grava o perfil em ai_profile)",
              flanqueia_em_jogo(f) is True)
    _, f = S._validate_custom_monster(ficha_nova(ai_profile="sentinela"))
    check("perfil sentinela no Padrão não flanqueia", flanqueia_em_jogo(f) is False)

    print("\n[3] Sobrescrever um nativo (bandido, que flanqueia pela espécie)")
    ok, f = S._validate_custom_monster(sobrescrita_bandido(flanqueia=False))
    check("Não grava False na sobrescrita", ok and f.get("flanqueia") is False)
    check("e o bandido deixa de flanquear", ok and flanqueia_em_jogo(f) is False)
    ok, f = S._validate_custom_monster(sobrescrita_bandido())
    check("Padrão não grava o campo na sobrescrita", ok and "flanqueia" not in f)
    check("e o bandido segue flanqueando pela espécie", ok and flanqueia_em_jogo(f) is True)

    print("\n[4] O editor tem o seletor e o salva")
    js = open(os.path.join(RAIZ, "tools", "editor_monster_editor.js"), encoding="utf-8").read()
    check("seletor #me-flanqueia com Padrão, Sim e Não",
          'id="me-flanqueia"' in js and all(f'value="{v}"' in js for v in ("", "sim", "nao")))
    check("a leitura grava True/False e apaga no Padrão",
          bool(re.search(r"out\.flanqueia = true", js)) and bool(re.search(r"out\.flanqueia = false", js))
          and "delete out.flanqueia" in js)
    check("o seletor mostra o valor salvo da ficha",
          bool(re.search(r"draft\.flanqueia === true", js)) and bool(re.search(r"draft\.flanqueia === false", js)))
    check("o seletor é ancorado no perfil de IA onde ele está (não só nos campos de identidade)",
          'root.querySelector("#me-ai_profile")?.closest("label")' in js
          and 'identityFields.querySelector("#me-ai_profile")' not in js)

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)


main()
