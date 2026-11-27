"""Lição do Ladino: Ataque Furtivo pelas costas, sem se esconder (fatia 23 do tutorial).

Roda: python -X utf8 tools/test_furtivo_costas_licao.py
"""
import asyncio
import copy
import json
import os
import sys
from unittest.mock import patch

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S  # noqa: E402

FALHAS = []
LIC = "treino_furtivo_costas"


def check(nome, cond):
    print(("  ✅ " if cond else "  ❌ ") + nome)
    if not cond:
        FALHAS.append(nome)


def carregar():
    return json.load(open(os.path.join(RAIZ, "dungeons", "campo_de_treinamento.json"), encoding="utf-8"))


def trilha_ladino(d):
    return sorted((f for f in d["falas"] if f.get("classe") == "rogue" and f.get("ordem") is not None),
                  key=lambda f: f["ordem"])


async def ataque(lic_id, pos, escondido=False, passo=None):
    """Põe o Ladino na lição `lic_id` dentro da sala 42 e ataca o boneco de [11,7]
    (olha para o sul: costas = [11,6], frente = [11,8]). Devolve (herói, mensagens)."""
    from test_tutorial_salas import room, lesson
    r, p = room("rogue")
    for sala in r.rooms:
        sala["locked"] = False        # no jogo o Ladino já abriu a porta da sala
    await lesson(r, p, lic_id)
    if passo is not None:
        p["licao_passo"] = passo
    boneco = next(m for m in r.monsters.values() if list(m["pos"]) == [11, 7])
    p["pos"] = list(pos)
    p["action_done"] = False
    p["bonus_action_used"] = False
    if escondido:
        p["invisivel_sombras"] = True
    r.messages.clear()
    S._GUIA_DICA_ULTIMA.clear()      # o limite de 1 dica a cada 5 s é global por id de herói
    with patch.object(S.random, "randint", return_value=20), patch.object(S, "roll_dice", return_value=1):
        await r.handle_attack(p["id"], boneco["id"])
    return p, r.messages


def dicas(msgs):
    return [m.get("motivo") for m in msgs if m.get("type") == "licao_dica"]


def main():
    d = carregar()

    print("\n[1] A lição no Campo de Treinamento")
    trilha = trilha_ladino(d)
    ids = [f["id"] for f in trilha]
    lic = next((f for f in trilha if f["id"] == LIC), None)
    check("a lição existe na trilha do Ladino", lic is not None)
    check("vem logo depois do Ataque Furtivo escondido",
          LIC in ids and ids.index(LIC) == ids.index("treino_furtivo") + 1)
    check("o Veneno Rápido vem depois dela", LIC in ids and ids.index("treino_veneno") == ids.index(LIC) + 1)
    check("a volta ao corredor continua sendo a última", ids[-1] == "volta_rogue")
    ordens = [f["ordem"] for f in trilha]
    check("nenhuma ordem repetida na trilha do Ladino", len(ordens) == len(set(ordens)))
    tar = (lic or {}).get("tarefa") or {}
    check("tarefa: Ataque Furtivo pelas costas, visível",
          tar.get("tipo") == "usar_habilidade" and tar.get("alvo") == "ataque_furtivo"
          and tar.get("requer_setor") == "costas" and tar.get("requer_visivel") is True)
    guia = (lic or {}).get("guia") or []
    check("guia com 2 passos e a casa atrás do boneco marcada",
          len(guia) == 2 and guia[-1].get("ui") == "casa:[11,6]")
    check("mesma sala e falante das outras lições do Ladino",
          lic is not None and lic.get("pos") == [9, 7] and lic.get("sala_exclusiva") is True
          and lic.get("trigger", {}).get("tipo") == "sala")
    ok, msg = S.validar_dungeon(d)
    check(f"a masmorra continua válida ({msg if not ok else 'ok'})", ok)

    print("\n[2] O script é idempotente")
    import aplicar_fatia23_tutorial as F23
    from gerar_guia_comum import aplicar_guia
    dois = aplicar_guia(F23.aplicar(F23.aplicar(copy.deepcopy(d))))
    check("aplicar de novo sobre o arquivo não muda nada", dois == d)
    sem = copy.deepcopy(d)
    sem["falas"] = [f for f in sem["falas"] if f["id"] != LIC]
    for f in sem["falas"]:
        if f.get("classe") == "rogue" and f.get("ordem", 0) > lic["ordem"]:
            f["ordem"] -= 1
    check("aplicar sobre a versão antiga reproduz o arquivo", aplicar_guia(F23.aplicar(sem)) == d)

    print("\n[3] No motor, só o furtivo pelas costas e visível conclui")
    p, msgs = asyncio.run(ataque(LIC, (11, 8), passo=1))
    check("pela frente: não conclui", LIC not in p.get("licoes_feitas", []))
    check("pela frente: dica de setor errado", "setor_errado" in dicas(msgs))
    p, msgs = asyncio.run(ataque(LIC, (11, 6), escondido=True, passo=1))
    check("escondido pelas costas: não conclui", LIC not in p.get("licoes_feitas", []))
    check("escondido: dica de que precisa estar visível", "furtivo_escondido" in dicas(msgs))
    p, msgs = asyncio.run(ataque(LIC, (11, 6), passo=1))
    check("visível pelas costas: conclui", LIC in p.get("licoes_feitas", []))
    check("visível pelas costas: entra no histórico (recompensa paga)", LIC in p.get("tutorial_history", []))
    check("o Veneno Rápido vira a próxima lição", p.get("licao_atual") == "treino_veneno")
    p, msgs = asyncio.run(ataque(LIC, (10, 7), passo=1))
    check("pelo flanco: não conclui", LIC not in p.get("licoes_feitas", []))

    print("\n[4] As outras lições não mudam")
    p, msgs = asyncio.run(ataque("treino_furtivo", (11, 8), escondido=True))
    check("Ataque Furtivo escondido de frente ainda conclui a lição anterior",
          "treino_furtivo" in p.get("licoes_feitas", []))
    check("e não gera dica de setor", "setor_errado" not in dicas(msgs))
    p, msgs = asyncio.run(ataque("treino_furtivo", (11, 8)))
    check("atacar de frente sem furtivo na lição anterior: não conclui e sem dica de setor",
          "treino_furtivo" not in p.get("licoes_feitas", []) and "setor_errado" not in dicas(msgs))

    print("\n[5] Textos")
    lang = open(os.path.join(RAIZ, "src", "lang", "tutorial.js"), encoding="utf-8").read()
    check("dica nova traduzida", "ui.tutorial.dica_erro.furtivo_escondido" in lang)
    guia_js = open(os.path.join(RAIZ, "src", "lang", "tutorial_guia.js"), encoding="utf-8").read()
    check("passos do guia no dicionário", f"ui.tutorial.guia.{LIC}." in guia_js)

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)


main()
