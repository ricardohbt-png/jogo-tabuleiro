"""Fatia 18 do tutorial: a lição de hostilidade nasce ANTES da porta, na sala vizinha.

Uso (da raiz): python tools/aplicar_fatia18_tutorial.py
Causa: lição plantada dentro de uma sala só dispara com o herói dentro dela (`_licao_no_lugar`).
A `fala_hostilidade` estava em [35,15], dentro da sala 46, cujo 1º passo manda ABRIR a porta
[33,15]: ela só aparecia depois da porta aberta e o passo (`conclui_com abrir_porta`) nunca
recebia o evento. Agora o marcador fica em [32,15], na sala 21, a uma casa da porta.
Grava o JSON sem reordenar chaves e preserva o fim de arquivo. Idempotente.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"
ID = "fala_hostilidade"
POS = [32, 15]
CONTINUA_SEM = ["fala_18", "fala_19"]


def aplicar(d):
    for f in d["falas"]:
        if f["id"] == ID:
            f["pos"] = list(POS)
            # Comida e água moram na mesma sala 21: sem isto, ficar com elas pendentes
            # segurava a hostilidade para sempre (o herói precisa estar na sala 21 para
            # disparar, e nela as duas nunca saem da zona para serem puladas).
            f["continua_sem"] = list(CONTINUA_SEM)
            f["continua_sem_ativas"] = list(CONTINUA_SEM)
    return d


if __name__ == "__main__":
    bruto = JSON_CAMPO.read_text(encoding="utf-8")
    d = aplicar(json.loads(bruto))
    saida = json.dumps(d, ensure_ascii=False, indent=2) + ("\n" if bruto.endswith("\n") else "")
    if saida != bruto:
        JSON_CAMPO.write_text(saida, encoding="utf-8", newline="\n")
    print("ok")
