"""Fatia 11 do tutorial: o Bardo pega a Harpa Velha de um baú, usa Nota Cortante no boneco,
volta ao Alaúde e vê a Sinfonia Heroica reforçar a Canção.

Uso (da raiz): python tools/aplicar_fatia11_tutorial.py
Grava o JSON da masmorra sem reordenar nenhuma chave existente. Acrescenta o baú da sala 43 e
as lições `treino_harpa`, `treino_nota_cortante`, `treino_alaude` (antes de `treino_cancao`),
remove o genérico `treino_instrumento` e renumera as ordens do Bardo. Idempotente. O
`configurar_tutorial_salas.py` usa as mesmas constantes.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

BAU_POS = [10, 22]                 # chão da sala 43 (x9..14, y21..26), livre de boneco/aprendiz/marcador
BAU_ITENS = [{"id": "instrumento_harpa_velho"}]
ORDEM = {"treino_harpa": 4, "treino_nota_cortante": 5, "treino_alaude": 6, "treino_cancao": 7,
         "treino_cancao_manter": 8, "treino_cancao_parar": 9, "treino_provocar": 10, "volta_bard": 11}
LICOES = [  # (id, texto, texto_curto, verbo, alvo)
    ("treino_harpa",
     "Abra o baú e pegue a Harpa Velha; depois equipe-a na mão do escudo. O Alaúde vai para a bolsa.",
     "Pegue a Harpa Velha e equipe-a", "equipar", "instrumento_harpa_velho"),
    ("treino_nota_cortante",
     "Fique na mesma linha ou coluna do boneco, a até 3 casas. Toque a Harpa e escolha a direção: a Nota Cortante atinge a linha toda.",
     "Use a Nota Cortante no boneco", "usar_instrumento", "harpa"),
    ("treino_alaude",
     "Equipe o Alaúde Velho de volta na mão do escudo. Ele é passivo: não tem botão, mas reforça a Canção Heroica.",
     "Equipe o Alaúde de volta", "equipar", "instrumento"),
]
CANCAO_TEXTO = ("Ative a Canção Heroica marcando Acerto. A Sinfonia Heroica do Alaúde soma +1 extra: "
                "o acerto sobe de +1 para +2. Confira no registro.")
CANCAO_CURTO = "Ative a Canção com Acerto e o Alaúde"


def aplicar(d):
    falas = d["falas"]
    if not any(c["pos"] == BAU_POS for c in d["chests"]):
        d["chests"].append({"pos": list(BAU_POS), "gold": 0, "items": [dict(i) for i in BAU_ITENS],
                            "key_objective": False})
    cancao = next(f for f in falas if f["id"] == "treino_cancao")
    if not any(f["id"] == "treino_harpa" for f in falas):
        idx = falas.index(cancao)
        for k, (fid, texto, curto, verbo, alvo) in enumerate(LICOES):
            falas.insert(idx + k, {
                "id": fid, "pos": list(cancao["pos"]), "falante": dict(cancao["falante"]), "texto": texto,
                "trigger": {"tipo": "sala"}, "classe": "bard", "sala_exclusiva": True, "ordem": ORDEM[fid],
                "tarefa": {"tipo": verbo, "vezes": 1, "texto_curto": curto, "alvo": alvo}})
    falas[:] = [f for f in falas if f["id"] != "treino_instrumento"]
    cancao["texto"] = CANCAO_TEXTO
    cancao["tarefa"]["texto_curto"] = CANCAO_CURTO
    cancao["tarefa"]["requer_sinfonia"] = True
    for f in falas:
        if f["id"] in ORDEM:
            f["ordem"] = ORDEM[f["id"]]
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
