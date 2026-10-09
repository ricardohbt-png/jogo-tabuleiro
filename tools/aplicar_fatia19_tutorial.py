"""Inclui a apresentação inicial do Campo de Treinamento sem reescrever o mapa."""
import json
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO = RAIZ / "dungeons" / "campo_de_treinamento.json"

FALA_INTRO = {
    "id": "fala_intro",
    "pos": [3, 15],
    "falante": {"nome": "Mestre de Armas", "emoji": "🛡️"},
    "texto": "Antes de partir, conheça seu herói e o pedido desta missão.",
    "trigger": {"tipo": "proximidade", "raio": 9},
    "ordem": -1,
    "tarefa": {"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "Conheça seu herói e a missão"},
}


def aplicar(definicao):
    """Garante uma única introdução e a coloca imediatamente antes da câmera."""
    falas = definicao.setdefault("falas", [])
    falas[:] = [fala for fala in falas if fala.get("id") != "fala_intro"]
    pos_camera = next((i for i, fala in enumerate(falas) if fala.get("id") == "fala_camera"), 0)
    falas.insert(pos_camera, deepcopy(FALA_INTRO))
    return definicao


def main():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gerar_guia_comum import aplicar_guia
    definicao = json.loads(CAMINHO.read_text(encoding="utf-8"))
    aplicar(definicao)
    aplicar_guia(definicao)
    CAMINHO.write_text(json.dumps(definicao, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("ok: fala_intro antes de fala_camera")


if __name__ == "__main__":
    main()
