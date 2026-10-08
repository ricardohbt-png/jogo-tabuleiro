"""Fatia 15 do tutorial: na sala do Mago as magias não gastam slots; os textos explicam a regra.

Uso (da raiz): python tools/aplicar_fatia15_tutorial.py
Troca só o `texto` (e o `texto_curto` de `treino_slots`) de `porta_mage`, `treino_magia` e
`treino_slots` e regrava o `guia` e o `src/lang/tutorial_guia.js` (os textos do guia moram em
`tutorial_guia_mago.py`). Não muda ordens nem tarefas. Idempotente. Os valores moram aqui e
alimentam também o `configurar_tutorial_salas.py`.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

PORTA_MAGE = ("Muito bem! Agora vá até a porta marcada: ela leva à sala exclusiva do seu herói. "
              "Lá dentro suas magias não gastam slots, para você testar tudo. Abra-a e entre.")
MAGIA = ("Abra o Grimório e lance uma magia conhecida. Nesta sala suas magias não gastam slots: "
         "teste todas as que você conhece, no boneco para dano ou em você para um benefício. "
         "É uma magia por turno; encerre o turno para lançar a próxima.")
SLOTS = ("Encerre o turno para continuar. Aqui na sala suas magias não gastam slots e você pode testar "
         "todas as que conhece. Fora dela, cada magia gasta um slot do círculo, que volta com o tempo.")
SLOTS_CURTO = "Encerre o turno para continuar"


def aplicar(d):
    por_id = {f["id"]: f for f in d["falas"]}
    por_id["porta_mage"]["texto"] = PORTA_MAGE
    por_id["treino_magia"]["texto"] = MAGIA
    por_id["treino_slots"]["texto"] = SLOTS
    por_id["treino_slots"]["tarefa"]["texto_curto"] = SLOTS_CURTO
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
