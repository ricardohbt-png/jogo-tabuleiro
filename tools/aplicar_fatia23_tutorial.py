"""Fatia 23 do tutorial: o Ladino aprende o Ataque Furtivo pelas costas, sem se esconder.

Uso (da raiz): python tools/aplicar_fatia23_tutorial.py
Cirúrgico e idempotente: acrescenta a lição `treino_furtivo_costas` logo depois de
`treino_furtivo` na trilha do Ladino e empurra em +1 a ordem das lições seguintes dele
(Veneno Rápido, golpe envenenado, Criar Armadilha e a volta ao corredor). Roda também no fim
de `aplicar_tutorial_missao.aplicar`, então o pipeline completo (`configurar_tutorial_salas.py`)
não a desfaz.

Os bonecos da sala 42 ([11,7] e [12,7]) não andam nem atacam, então olham sempre para o sul
(direção padrão): as costas deles são [11,6] e [12,6]. Eles também não morrem (alvo de sala de
classe tem `training_target`), então a lição nunca fica sem alvo.
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

LICAO = "treino_furtivo_costas"
ANTERIOR = "treino_furtivo"
MESTRE = {"nome": "Mestre de Armas", "emoji": "🎓", "retrato": "assets/portraits/mestre_de_armas.png"}
FALA = {
    "id": LICAO, "pos": [9, 7],
    "falante": dict(MESTRE),
    "texto": ("Nem sempre é preciso se esconder: o Ataque Furtivo também acontece quando você golpeia "
              "pelas costas. Os bonecos olham para o sul. Sem se esconder, vá para a casa atrás de um "
              "deles e ataque."),
    "trigger": {"tipo": "sala"},
    "classe": "rogue",
    "sala_exclusiva": True,
    "tarefa": {"tipo": "usar_habilidade", "vezes": 1,
               "texto_curto": "Acerte um Ataque Furtivo pelas costas, sem se esconder",
               "alvo": "ataque_furtivo", "requer_setor": "costas", "requer_visivel": True},
}


def _rogue(falas):
    return [f for f in falas if f.get("classe") == "rogue" and f.get("ordem") is not None]


def aplicar(d):
    falas = d.setdefault("falas", [])
    anterior = next((f for f in falas if f.get("id") == ANTERIOR), None)
    if anterior is None:
        return d
    base = anterior["ordem"]
    atual = next((f for f in falas if f.get("id") == LICAO), None)
    ja_ordenada = (atual is not None and atual.get("ordem") == base + 1 and not any(
        f is not atual and f.get("ordem") == base + 1 for f in _rogue(falas)))
    nova = deepcopy(FALA)
    if atual is not None and atual.get("guia"):
        nova["guia"] = deepcopy(atual["guia"])   # o guia é gravado por gerar_guia_comum.aplicar_guia
    if ja_ordenada:
        nova["ordem"] = base + 1
        falas[falas.index(atual)] = nova
        return d
    # Primeira vez (ou o pipeline refez as lições do Ladino): empurra as seguintes.
    if atual is not None:
        falas.remove(atual)
    for f in _rogue(falas):
        if f["ordem"] > base:
            f["ordem"] += 1
    nova["ordem"] = base + 1
    falas.insert(falas.index(anterior) + 1, nova)
    return d


def main():
    from gerar_guia_comum import aplicar_guia, render_lang, LANG_JS
    d = json.loads(JSON_CAMPO.read_text(encoding="utf-8"))
    aplicar(d)
    aplicar_guia(d)
    LANG_JS.write_text(render_lang(), encoding="utf-8", newline="\n")
    JSON_CAMPO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("ok")


if __name__ == "__main__":
    main()
