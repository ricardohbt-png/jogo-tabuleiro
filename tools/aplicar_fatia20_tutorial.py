"""Fatia 20 do tutorial: a Sala das Reações de Terreno (gás + ilha de água, piche + fogo).

Uso (da raiz): python tools/aplicar_fatia20_tutorial.py
Cirúrgico e idempotente: só acrescenta/ajusta a ala final do Campo de Treinamento (a sala 49
vira a sala do gás; a saída desce para uma sala 51 nova, atrás de uma porta que só abre quando o
gás explode). Roda também no fim de `aplicar_tutorial_missao.aplicar`, que fixaria a saída
antiga, e portanto cobre o `configurar_tutorial_salas.py`. Spec:
docs/superpowers/specs/2026-10-16-sala-reacoes-terreno-design.md.
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"

GRID_H = 40
SALA_GAS = 49
SALA_PICHE = 51
PORTA = [51, 32]
SAIDA = [51, 36]
LAGO = [[x, y] for y in (28, 29) for x in (50, 51, 52)]
BAU_GAS = [51, 29]            # na água, dentro do gás
BAU_PICHE = [49, 33]          # primeira fileira da sala 51
BONECO = [53, 37]             # a ≤4 casas do baú; o piche (3×3) não alcança a saída
ZONA_GAS = "gas_tutorial"
MESTRE = {"nome": "Mestre de Armas", "emoji": "🛡️", "retrato": "assets/portraits/mestre_de_armas.png"}
CONTINUA_SEM = ["fala_res", "fala_vuln", "fala_atalhos"]

FALA_GAS = {
    "id": "fala_gas", "ordem": 36, "pos": [51, 25],
    "falante": dict(MESTRE),
    "texto": "Este gás é inflamável e selou a porta de baixo. Pegue o óleo na ilha de água e detone-o com fogo.",
    "trigger": {"tipo": "proximidade", "raio": 2},
    "continua_sem": list(CONTINUA_SEM),
    "tarefa": {"tipo": "explodir_gas", "alvo": ZONA_GAS, "vezes": 1,
               "texto_curto": "Detone o gás com fogo"},
}
FALA_PICHE = {
    "id": "fala_piche", "ordem": 37, "pos": [51, 33],
    "falante": dict(MESTRE),
    "texto": "Piche e fogo combinam muito bem. Jogue o piche no boneco e acenda-o com o óleo.",
    "trigger": {"tipo": "proximidade", "raio": 2},
    "continua_sem": list(CONTINUA_SEM),
    "tarefa": {"tipo": "incendiar_piche", "vezes": 1, "texto_curto": "Acenda o piche com o óleo"},
}


def _upsert_por_id(lista, item, depois_de=None):
    """Troca o item de mesmo id no lugar; se não existe, entra logo depois de `depois_de`."""
    for i, atual in enumerate(lista):
        if atual.get("id") == item["id"]:
            lista[i] = deepcopy(item)
            return
    alvo = next((i for i, x in enumerate(lista) if x.get("id") == depois_de), len(lista) - 1)
    lista.insert(alvo + 1, deepcopy(item))


def _sala(d, ident):
    salas = d.setdefault("rooms", [])
    sala = next((r for r in salas if r.get("id") == ident), None)
    if sala is None:
        sala = {"id": ident}
        salas.append(sala)
    return sala


def _mapa(d):
    grid, tiles = d["grid"], d["tiles"]
    w = int(grid["w"])
    tiles.extend([[0] * w for _ in range(GRID_H - len(tiles))])
    grid["h"] = GRID_H
    for y in range(33, 39):
        for x in range(48, 54):
            tiles[y][x] = 1
    tiles[PORTA[1]][PORTA[0]] = 2
    gas = _sala(d, SALA_GAS)
    gas.update({"x": 48, "y": 26, "w": 6, "h": 6, "role": "empty", "locked": True,
                "doors": [[51, 25], list(PORTA)]})
    _sala(d, SALA_PICHE).update({"x": 48, "y": 33, "w": 6, "h": 6, "role": "empty", "locked": True,
                                 "doors": [list(PORTA)]})
    for x, y in LAGO:
        d.setdefault("materiais", {})[f"{x},{y}"] = "agua"
    d["exit"] = {"x": SAIDA[0], "y": SAIDA[1]}
    d.setdefault("door_conditions", {})[f"{PORTA[0]},{PORTA[1]}"] = {"type": "gas", "zona_id": ZONA_GAS}


def _conteudo(d):
    novos = [
        {"pos": list(BAU_GAS), "gold": 0, "key_objective": False,
         "items": [{"id": "frasco_oleo"} for _ in range(3)]},
        {"pos": list(BAU_PICHE), "gold": 0, "key_objective": False,
         "items": [{"id": "frasco_piche"}, {"id": "frasco_piche"},
                   {"id": "frasco_oleo"}, {"id": "frasco_oleo"}]},
    ]
    posicoes = {tuple(c["pos"]) for c in novos}
    d["chests"] = [c for c in d.get("chests", []) if tuple(c.get("pos") or ()) not in posicoes] + novos
    boneco = {"type": "boneco_treino", "pos": list(BONECO), "room_id": SALA_PICHE,
              "boss": False, "target": False, "source_id": "mob_reacoes_boneco"}
    d["monsters"] = [m for m in d.get("monsters", []) if m.get("source_id") != boneco["source_id"]] + [boneco]


def _licoes(d):
    falas = d.setdefault("falas", [])
    _upsert_por_id(falas, FALA_GAS, depois_de="fala_armadilhas")
    _upsert_por_id(falas, FALA_PICHE, depois_de="fala_gas")
    retirada = next(f for f in falas if f["id"] == "fala_retirada")
    retirada["ordem"] = 38
    retirada["pos"] = list(SAIDA)
    retirada["tarefa"]["alvo"] = list(SAIDA)
    if "fala_piche" not in retirada.setdefault("continua_sem", []):
        retirada["continua_sem"].append("fala_piche")


def aplicar(d):
    _mapa(d)
    _conteudo(d)
    _licoes(d)
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
