"""Fatia 16 do tutorial: o Clérigo aprende a lançar magias do Grimório; na sala dele elas não gastam slots.

Uso (da raiz): python tools/aplicar_fatia16_tutorial.py
Acrescenta as lições `treino_grimorio` (lançar uma magia conhecida) e `treino_grimorio_turno`
(encerrar o turno: lançar gasta a ação principal) logo depois da ponte `porta_cleric`, antes das
habilidades de classe, e renumera as ordens do Clérigo (estritas e únicas). Troca o texto de
`porta_cleric`. Regrava o `guia` e o `src/lang/tutorial_guia.js` (textos em `tutorial_guia_clerigo.py`).
Idempotente. Os valores moram aqui e alimentam também o `configurar_tutorial_salas.py`.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

PORTA_CLERIC = ("Muito bem! Agora vá até a porta marcada: ela leva à sala exclusiva do seu herói. "
                "Lá dentro suas magias não gastam slots, para você testar tudo. Abra-a e entre.")
GRIMORIO = ("Abra a aba ✨ Magias do seu painel (no celular, o botão ✨), escolha uma magia que você conhece e lance-a. "
            "Magia de aliado: clique em você ou num aprendiz. Magia de área: clique numa casa livre. "
            "Comando e Maldição do Corpo Pesado pedem inimigo ou outro herói, e aqui não há. "
            "Nesta sala suas magias não gastam slots; fora dela cada magia gasta um slot do círculo. "
            "Lançar usa sua ação principal.")
GRIMORIO_CURTO = "Lance uma magia conhecida"
TURNO = ("Encerre o turno para continuar: lançar a magia usou sua ação principal, e as habilidades "
         "de Clérigo a seguir também precisam dela. Aqui na sala suas magias não gastam slots; fora dela "
         "cada magia gasta um, que volta com o tempo.")
TURNO_CURTO = "Encerre o turno para continuar"
# ordem final do Clérigo (a ponte `porta_cleric` é a 3)
ORDEM = {"treino_grimorio": 4, "treino_grimorio_turno": 5, "treino_cura": 6, "treino_cura_area": 7,
         "treino_purificar": 8, "treino_ressuscitar": 9, "volta_cleric": 10}


def aplicar(d):
    falas = d["falas"]
    por_id = {f["id"]: f for f in falas}
    por_id["porta_cleric"]["texto"] = PORTA_CLERIC
    if "treino_grimorio" not in por_id:
        cura = por_id["treino_cura"]
        idx = falas.index(cura)
        base = {"pos": list(cura["pos"]), "falante": dict(cura["falante"]), "trigger": {"tipo": "sala"},
                "classe": "cleric", "sala_exclusiva": True}
        falas.insert(idx, {"id": "treino_grimorio", **base, "texto": GRIMORIO,
                           "requisitos": {"magia_tipo": "qualquer"},
                           "tarefa": {"tipo": "usar_magia", "vezes": 1, "texto_curto": GRIMORIO_CURTO}})
        falas.insert(idx + 1, {"id": "treino_grimorio_turno", **base, "texto": TURNO,
                               "tarefa": {"tipo": "encerrar_turno", "vezes": 1, "texto_curto": TURNO_CURTO}})
    for f in falas:
        if f["id"] in ORDEM:
            f["ordem"] = ORDEM[f["id"]]
        if f["id"] == "treino_grimorio":
            f["texto"] = GRIMORIO
        if f["id"] == "treino_grimorio_turno":
            f["texto"] = TURNO
    return d


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gerar_guia_comum import aplicar_guia, render_lang, LANG_JS
    d = json.loads(JSON_CAMPO.read_text(encoding="utf-8"))
    aplicar(d)
    aplicar_guia(d)
    LANG_JS.write_text(render_lang(), encoding="utf-8", newline="\n")
    JSON_CAMPO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("ok")


if __name__ == "__main__":
    main()
