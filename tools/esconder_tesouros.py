"""Esconderijos com itens mágicos nos mapas das campanhas.

Cada entrada liga um objeto que JÁ EXISTE no mapa (pelo id da decoração) a um
conteúdo escondido: o objeto não mostra o 💰 nem pode ser aberto até um herói o
notar ao passar ao lado dele (teste de Percepção contra `cd_busca`, ver
`_procurar_esconderijos` no server.py).

Reexecutável e idempotente: só mexe nos objetos listados aqui e regrava `loot`,
`escondido` e `cd_busca` deles. Se um gerador de campanha reescrever um mapa
(com --forcar), rode este script de novo.

    python -X utf8 tools/esconder_tesouros.py            # grava
    python -X utf8 tools/esconder_tesouros.py --simular  # só relata
"""
import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# (mapa, id da decoração, tipo esperado, CD, ouro, itens)
# A raridade acompanha o nível esperado do grupo em cada etapa.
ESCONDERIJOS = [
    # O Resgate de Elara — Parte 1 (Alva e Luz)
    ("casa_secreta", "decor_5", "barril", 12, 15, ["pocao_invisibilidade", "moeda_da_sorte"]),
    ("fazenda", "decor_92", "carroca", 13, 0, ["espada_magica"]),
    # Ramo A — Vila do Riacho
    ("elara_riacho_casa", "casa_cama_8", "cama", 13, 20, ["botas_passo_felino"]),
    ("elara_riacho_celeiro", "decor_65", "estante", 12, 0,
     ["flechas_magicas", "virotes_magicos", "pocao_velocidade"]),
    # Ramo B — Adhadal e Corvin
    ("elara_adhadal_2", "decor_555", "arvore_seca", 13, 0, ["amulet_alcance_arcano", "pocao_barreira_arcana"]),
    ("elara_corvin_cacada", "decor_41", "arvore_grande", 14, 0, ["lamina_trovejante"]),
    ("elara_corvin_gilo", "decor_6", "mesa_quimica", 15, 0, ["punhal_assassino"]),
    # Graciero
    ("elara_graciero_beco", "decor_42", "arvore_grande", 14, 0, ["bracelete_guarda_reflexa"]),
    ("elara_graciero_cais", "decor_227", "carroca", 14, 40, ["chicote_fogo"]),
    ("elara_leonel_1", "casa_barril_1", "barril", 14, 0, ["tiara_expansao_arcana"]),
    ("elara_leonel_1_alerta", "casa_barril_1", "barril", 14, 0, ["tiara_expansao_arcana"]),
    ("elara_leonel_2", "mansao_lareira_1", "lareira", 15, 0, ["anel_touro_ferro"]),
    ("elara_leonel_2", "decor_71", "mesa_cadeiras", 15, 30, ["calice_eter", "ultimo_suspiro"]),
    # Rota do Olho
    ("elara_montanha_3", "carav_barril_11", "barril", 16, 0, ["cinzas_ardentes"]),
    # Sombras sob Alva e Luz
    ("sombras_1_vau", "vau_carroca", "carroca", 12, 0, ["lampada_vigilia_arcana", "pocao_voo"]),
    ("sombras_3a_saloes", "decor_14", "estante_armas", 14, 0, ["ferroada"]),
    # A Maré do Charco
    ("charcos_1_bordas", "decor_18", "arvore_seca", 13, 0, ["flechas_magicas", "pocao_barreira_arcana"]),
    ("charcos_2_palafitas", "palafitas_barril_25", "barril", 15, 0, ["maca_zero_absoluto"]),
]


def _caminho(mapa, pasta):
    return os.path.join(pasta, f"{mapa}.json")


def aplicar(simular=False, pasta=None):
    import server as S
    pasta = pasta or S.DUNGEONS_DIR
    por_mapa = {}
    for mapa, did, tipo, cd, ouro, itens in ESCONDERIJOS:
        por_mapa.setdefault(mapa, []).append((did, tipo, cd, ouro, itens))
    relatorio = []
    for mapa, entradas in por_mapa.items():
        caminho = _caminho(mapa, pasta)
        with open(caminho, encoding="utf-8") as f:
            defn = json.load(f)
        decs = {d.get("id"): d for d in defn.get("decorations", [])}
        for did, tipo, cd, ouro, itens in entradas:
            d = decs.get(did)
            if d is None or d.get("type") != tipo:
                raise ValueError(f"{mapa}: objeto {did} ({tipo}) não existe mais no mapa")
            for it in itens:
                if it not in S._DUNGEON_ITEM_CATALOG:
                    raise ValueError(f"{mapa}: item desconhecido {it}")
            d["loot"] = {"gold": ouro, "items": [{"id": it} for it in itens]}
            d["escondido"] = True
            d["cd_busca"] = cd
            relatorio.append(f"{mapa}: {did} ({tipo}, CD {cd}) → {', '.join(itens)}"
                             + (f" + {ouro} ouro" if ouro else ""))
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{mapa}: {msg}")
        if not simular:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(defn, f, ensure_ascii=False, indent=2)
    return relatorio


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    args = ap.parse_args(argv)
    for linha in aplicar(simular=args.simular):
        print(linha)
    print("(simulação: nada foi gravado)" if args.simular else "pronto.")


if __name__ == "__main__":
    main()
