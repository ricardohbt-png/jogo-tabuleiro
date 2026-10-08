"""Fatia 8 do tutorial, aplicada de forma idempotente e cirúrgica (não reordena nada que já existe).

Uso (da raiz): python tools/aplicar_fatia8_tutorial.py
Também é chamado pelo `configurar_tutorial_salas.py`, para os dois caminhos darem o mesmo mapa.

O que faz:
- boneco de palha com 24 PV: o óleo (x2 de fogo) não o derruba no primeiro frasco, e é só assim
  que o jogador VÊ o número vermelho com VULNERÁVEL (o golpe que mata tira o alvo do game_state);
- tipo novo `boneco_treino_veneno` (sensível a veneno x2, sem a imunidade de construto, Fortitude
  muito baixa para o Fungo Acre sempre pegar), que ocupa o lugar dos `boneco_treino` da sala 22;
- fala_30 e fala_32: textos mandam olhar o número vermelho; fala_32 passa a exigir o boneco novo.
Também reescreve o espelho `tools/editor_monsters_custom.js`, no formato que o servidor grava.
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"
JSON_MONSTROS = RAIZ / "monstros_personalizados.json"
JS_MONSTROS = RAIZ / "tools" / "editor_monsters_custom.js"

SALA_ITENS = 22
TIPO_VENENO = "boneco_treino_veneno"
PALHA_PV = 24

TEXTO_OLEO = ("O Frasco de Óleo Incendiário 🔥 se arremessa: abra a bolsa, clique com o botão direito no frasco e "
              "depois clique no boneco de palha. Ele é vulnerável a fogo, então o dano sai maior: repare no "
              "número vermelho com VULNERÁVEL. Você rola destreza contra a Armadura do alvo; se acertar, ele pega fogo.")
TEXTO_VENENO = ("O veneno só age quando o golpe ACERTA: errar desperdiça o turno, não a dose. Acerte um boneco "
                "sensível a veneno agora e veja a peçonha entrar: a cada rodada ela tira vida, e como o boneco é "
                "vulnerável a veneno o número sai dobrado, em vermelho com VULNERÁVEL.")
CURTO_VENENO = "Acerte um boneco sensível a veneno com a arma untada"


def novo_boneco_veneno(treino):
    m = deepcopy(treino)
    m.update({
        "type": TIPO_VENENO,
        "name": "Boneco Sensível a Veneno",
        "emoji": "☠️",
        "cr": 0.05,
        "base_hp": 20,
        "hp": 20,
        "fort_base": -20,
        "fort": -20,
        "subtipo": "raca_padrao",        # construto é imune a veneno; este aqui é de carne e palha
        "immunities": [],
        "weaknesses": [{"type": "poison", "multiplier": 2,
                        "descricao": "Veneno causa 2× de dano (boneco encharcado de seiva)."}],
    })
    return m


def aplicar_monstros(lista):
    for m in lista:
        if m["type"] == "boneco_palha":
            m["base_hp"] = PALHA_PV
            m["hp"] = PALHA_PV
        elif m["type"] == TIPO_VENENO:
            m["base_hp"] = m["hp"] = 20
    if not any(m["type"] == TIPO_VENENO for m in lista):
        treino = next(m for m in lista if m["type"] == "boneco_treino")
        i = lista.index(treino)
        lista.insert(i + 1, novo_boneco_veneno(treino))
    return lista


def aplicar(d):
    for m in d["monsters"]:
        if m["type"] == "boneco_treino" and m.get("room_id") == SALA_ITENS:
            m["type"] = TIPO_VENENO
    for f in d["falas"]:
        if f["id"] == "fala_30":
            f["texto"] = TEXTO_OLEO
        elif f["id"] == "fala_32":
            f["texto"] = TEXTO_VENENO
            f["tarefa"]["alvo"] = TIPO_VENENO
            f["tarefa"]["texto_curto"] = CURTO_VENENO
    return d


def gravar_monstros(lista):
    JSON_MONSTROS.write_text(json.dumps(lista, ensure_ascii=False, indent=2).replace("\n", "\r\n") + "\r\n",
                             encoding="utf-8", newline="")
    espelho = ("window.EDITOR_CUSTOM_MONSTERS = " + json.dumps(lista, ensure_ascii=False, indent=2) + ";\n"
               "// GERADO pelo servidor ao salvar no Editor de criaturas.\n")
    JS_MONSTROS.write_text(espelho.replace("\n", "\r\n"), encoding="utf-8", newline="")


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gerar_guia_comum import aplicar_guia, render_lang, LANG_JS
    gravar_monstros(aplicar_monstros(json.loads(JSON_MONSTROS.read_text(encoding="utf-8"))))
    d = json.loads(JSON_CAMPO.read_text(encoding="utf-8"))
    aplicar(d)
    aplicar_guia(d)
    LANG_JS.write_text(render_lang(), encoding="utf-8", newline="\n")
    # o arquivo versionado usa CRLF e não tem \n final
    JSON_CAMPO.write_text(json.dumps(d, ensure_ascii=False, indent=2).replace("\n", "\r\n"),
                          encoding="utf-8", newline="")
    print("ok")


if __name__ == "__main__":
    main()
