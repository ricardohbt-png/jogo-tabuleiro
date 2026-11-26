"""Fatia 22 do tutorial: a lição da direção (costas, flanco e a bússola de fim de turno).

Uso (da raiz): python tools/aplicar_fatia22_tutorial.py
Cirúrgico e idempotente: só acrescenta a lição `fala_direcao` (ordem 34, entre a vulnerabilidade
e o corredor de armadilhas) ao Campo de Treinamento e a registra em `continua_sem` das lições
que já listam `fala_vuln`. Roda também no fim de `aplicar_tutorial_missao.aplicar`, então o
pipeline completo (`configurar_tutorial_salas.py`) não a desfaz.
Spec: docs/superpowers/specs/2026-11-25-ensino-direcao-intencao-design.md.
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

MESTRE = {"nome": "Mestre de Armas", "emoji": "🛡️", "retrato": "assets/portraits/mestre_de_armas.png"}
# O boneco imóvel da sala 48 está em [51,15] e olha para o sul (direção padrão): as costas dele
# são a casa do norte, [51,14].
FALA_DIRECAO = {
    "id": "fala_direcao", "ordem": 34, "pos": [51, 15],
    "falante": dict(MESTRE),
    "texto": ("Onde você fica em relação ao inimigo importa. Pelo flanco você acerta com +1, pelas "
              "costas com +2. Dê a volta no boneco, ataque por trás e depois escolha para onde olhar."),
    "trigger": {"tipo": "proximidade", "raio": 1},
    "continua_sem": ["fala_res", "fala_vuln"],
    "tarefa": {"tipo": "escolher_direcao", "vezes": 1,
               "texto_curto": "Encerre o turno escolhendo para onde olhar"},
}


def _upsert_por_id(lista, item, depois_de=None):
    for i, atual in enumerate(lista):
        if atual.get("id") == item["id"]:
            lista[i] = deepcopy(item)
            return
    alvo = next((i for i, x in enumerate(lista) if x.get("id") == depois_de), len(lista) - 1)
    lista.insert(alvo + 1, deepcopy(item))


def aplicar(d):
    falas = d.setdefault("falas", [])
    _upsert_por_id(falas, FALA_DIRECAO, depois_de="fala_vuln")
    # Quem já podia pular a vulnerabilidade também pode pular a direção (sem prêmio).
    for f in falas:
        cont = f.get("continua_sem")
        if (f.get("id") != "fala_direcao" and isinstance(cont, list)
                and "fala_vuln" in cont and "fala_direcao" not in cont):
            cont.append("fala_direcao")
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
