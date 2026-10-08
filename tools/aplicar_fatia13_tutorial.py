"""Fatia 13 do tutorial: o refém do Paladino anda até a casa à FRENTE da porta.

Uso (da raiz): python tools/aplicar_fatia13_tutorial.py
Troca só o `alvo` e o `texto` de `treino_guiar_refem` (de [32,24], diagonal à porta, para
[32,25], ortogonal) e regrava o `guia` (o `ui casa:[x,y]` e os textos vêm de
`tutorial_guia_paladino.py`) e o `src/lang/tutorial_guia.js`. Mantém a ordem das chaves e a
convenção do arquivo (LF, sem \n final). Idempotente. Os valores moram em `aplicar_fatia9_tutorial`
(que também alimenta o `configurar_tutorial_salas.py`).
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"
ID = "treino_guiar_refem"


def aplicar(d):
    import aplicar_fatia9_tutorial as F9
    f = next(x for x in d["falas"] if x["id"] == ID)
    f["tarefa"]["alvo"] = list(F9.ALVO)
    f["texto"] = F9.TEXTO
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
