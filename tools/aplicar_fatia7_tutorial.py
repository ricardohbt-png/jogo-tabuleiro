"""Fatia 7 do tutorial (feedback do Lucas), aplicada de forma idempotente e cirúrgica.

Uso (da raiz): python tools/aplicar_fatia7_tutorial.py
Grava o JSON da masmorra sem reordenar nenhuma chave existente (o `configurar_tutorial_salas.py`
por inteiro reordena e apaga edições do editor; este script só ACRESCENTA ou ajusta o que é seu).
Também é chamado pelo `configurar_tutorial_salas.py`, para os dois caminhos darem o mesmo mapa.

O que faz:
- sala 22: dois `boneco_palha` (alvo do óleo, 2 PV, vulnerável a fogo) e um `boneco_treino` a mais
  (folga para o veneno: a lição seguinte nunca fica sem alvo);
- fala_30: texto e tarefa falam do boneco de palha;
- uma lição `volta_<classe>` depois da última lição de cada trilha, levando de volta ao corredor.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

SALA_ITENS = 22
PALHA = ([38, 17], [38, 18])
TREINO_EXTRA = ([36, 18],)
PROXIMA_SALA = [28, 15]            # onde a trilha comum (fala_18) recomeça
CLASSES = ("warrior", "mage", "rogue", "cleric", "bard", "paladin")

TEXTO_OLEO = ("O Frasco de Óleo Incendiário 🔥 se arremessa: abra a bolsa, clique com o botão direito no frasco e "
              "depois clique no boneco de palha. Ele é vulnerável a fogo, então o dano sai maior. "
              "Você rola destreza contra a Armadura do alvo; se acertar, ele pega fogo.")
CURTO_OLEO = "Arremesse o óleo no boneco de palha"
TEXTO_VOLTA = ("Treino da classe concluído! Agora volte ao corredor e siga para a próxima sala: "
               "saia pela porta e ande até a casa marcada, onde o Mestre de Armas espera.")


def aplicar(d):
    for pos in PALHA:
        if not any(m["pos"] == pos for m in d["monsters"]):
            d["monsters"].append({"type": "boneco_palha", "pos": list(pos), "room_id": SALA_ITENS,
                                  "boss": False, "target": False})
    for pos in TREINO_EXTRA:
        if not any(m["pos"] == pos for m in d["monsters"]):
            d["monsters"].append({"type": "boneco_treino", "pos": list(pos), "room_id": SALA_ITENS,
                                  "boss": False, "target": False})
    for f in d["falas"]:
        if f["id"] == "fala_30":
            f["texto"] = TEXTO_OLEO
            f["tarefa"]["texto_curto"] = CURTO_OLEO
    for cls in CLASSES:
        fid = "volta_" + cls
        if any(f["id"] == fid for f in d["falas"]):
            continue
        real = max((f for f in d["falas"] if f.get("classe") == cls and f.get("sala_exclusiva")),
                   key=lambda f: f["ordem"])
        d["falas"].append({"id": fid, "pos": list(real["pos"]), "falante": dict(real["falante"]),
                           "texto": TEXTO_VOLTA, "trigger": {"tipo": "sala"}, "classe": cls,
                           "ordem": real["ordem"] + 1,
                           "tarefa": {"tipo": "mover_ate", "alvo": list(PROXIMA_SALA), "vezes": 1,
                                      "texto_curto": "Volte ao corredor e siga para a próxima sala"}})
    return d


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gerar_guia_comum import aplicar_guia, render_lang, LANG_JS
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
