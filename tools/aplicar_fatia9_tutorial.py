"""Fatia 9 do tutorial: guiar o refém do Paladino até uma casa e dispensá-lo.

Uso (da raiz): python tools/aplicar_fatia9_tutorial.py
Grava o JSON da masmorra sem reordenar nenhuma chave existente; só ACRESCENTA a lição
`treino_guiar_refem` (logo depois de `treino_maos`) e empurra +1 a `ordem` das lições
seguintes do Paladino. Idempotente. Também é chamado pelo `configurar_tutorial_salas.py`,
mas lá a lição já nasce pelo `lesson()`: aqui nada muda se ela existir.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

ID = "treino_guiar_refem"
DEPOIS_DE = "treino_maos"
# Chão da sala 38 (x32..38, y23..27) encostado na porta [31,25] e fora da casa do refém [35,25]
# e do herói [33,25]: fica a 3 casas do refém e perto da saída da sala, sem decoração nem baú.
ALVO = [32, 24]
TEXTO = ("Agora guie o refém até a casa marcada. Encerre seu turno para abrir a vez dele, "
         "depois clique na casa. Ao chegar, ele se retira e você não precisa mais controlá-lo.")
CURTO = "Guie o refém até a casa marcada"


def aplicar(d):
    falas = d["falas"]
    if any(f["id"] == ID for f in falas):
        return d
    base = next(f for f in falas if f["id"] == DEPOIS_DE)
    ordem = base["ordem"] + 1
    for f in falas:
        if f.get("classe") == "paladin" and f.get("ordem") is not None and f["ordem"] >= ordem:
            f["ordem"] += 1
    nova = {"id": ID, "pos": list(base["pos"]), "falante": dict(base["falante"]), "texto": TEXTO,
            "trigger": {"tipo": "sala"}, "classe": "paladin", "ordem": ordem, "sala_exclusiva": True,
            "tarefa": {"tipo": "guiar_refem", "vezes": 1, "texto_curto": CURTO, "alvo": list(ALVO)}}
    falas.insert(falas.index(base) + 1, nova)
    return d


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gerar_guia_comum import aplicar_guia, render_lang, LANG_JS
    d = json.loads(JSON_CAMPO.read_text(encoding="utf-8"))
    aplicar(d)
    aplicar_guia(d)
    LANG_JS.write_text(render_lang(), encoding="utf-8", newline="\n")
    JSON_CAMPO.write_text(json.dumps(d, ensure_ascii=False, indent=2).replace("\n", "\r\n"),
                          encoding="utf-8", newline="")
    print("ok")


if __name__ == "__main__":
    main()
