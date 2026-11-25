"""Mais esconderijos nos mapas das campanhas: itens mágicos, especiais e comida.

Complementa `tools/esconder_tesouros.py` (que fixa, à mão, 1 ou 2 achados por mapa):
aqui o script SORTEIA, entre os objetos que podem guardar conteúdo (barris, sacos,
caixas, estantes, mesas, camas, carroças, árvores...), alguns objetos por mapa e
esconde neles um achado de um de três tipos: mágico/especial, comida e bebida, ou
um pouco dos dois. O herói precisa notar o objeto (teste de Percepção contra
`cd_busca`) antes de poder abri-lo; ver `_procurar_esconderijos` no server.py.

O sorteio usa uma semente por mapa, então a escolha é reproduzível. Ela também é
gravada em `tools/.esconderijos_aleatorios.json`: rodar de novo reaplica o MESMO
resultado (idempotente) em vez de sortear outra vez. Uma variante de mapa que
copia outro (Praça dos Escorpiões, Casa do Leonel alerta) usa o mesmo sorteio do
original, para os dois caminhos exclusivos terem o mesmo achado.

Objetos que já têm conteúdo, que são chave de objetivo, que levam armadilha ou
que são decoração de parede nunca são tocados. Se um gerador de campanha
reescrever um mapa (com --forcar), rode este script de novo.

    python -X utf8 tools/esconder_aleatorios.py             # grava
    python -X utf8 tools/esconder_aleatorios.py --simular   # só relata
    python -X utf8 tools/esconder_aleatorios.py --refazer   # descarta o sorteio gravado e sorteia de novo
"""
import argparse
import json
import os
import random
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

LEDGER = os.path.join(RAIZ, "tools", ".esconderijos_aleatorios.json")

# Mapa → (nível da etapa, mapa que dá a semente). Só os mapas das campanhas.
MAPAS = {
    "floresta": (1, None),
    "floresta_2": (1, None),
    "casa_secreta": (1, None),
    "fazenda": (1, None),
    "elara_riacho_casa": (2, None),
    "elara_riacho_celeiro": (2, None),
    "elara_adhadal_1": (2, None),
    "elara_adhadal_2": (2, None),
    "elara_corvin_cacada": (3, None),
    "elara_corvin_gilo": (3, None),
    "elara_graciero_beco": (3, None),
    "elara_graciero_cais": (3, None),
    "elara_graciero_praca_viva": (3, "elara_graciero_praca_viva"),
    "elara_graciero_praca_morta": (3, "elara_graciero_praca_viva"),
    "elara_graciero_praca_pedra": (3, "elara_graciero_praca_viva"),
    "elara_leonel_1": (3, None),
    "elara_leonel_1_alerta": (3, "elara_leonel_1"),
    "elara_leonel_2": (3, None),
    "elara_montanha_1": (3, None),
    "elara_montanha_2": (3, None),
    "elara_montanha_3": (3, None),
    "sombras_1_vau": (1, None),
    "sombras_2_minas": (1, None),
    "sombras_3a_saloes": (2, None),
    "sombras_3b_trono": (2, None),
    "charcos_1_bordas": (2, None),
    "charcos_2_palafitas": (2, None),
    "charcos_3_travessia": (3, None),
    "charcos_4a_arredores": (3, None),
    "charcos_4b_aldeia": (3, None),
}

# Objetos que aceitam conteúdo (`loot_capaz` em DECOR_TYPES) e fazem sentido como esconderijo.
TIPOS = {"barril", "barril_cerveja", "saco_grao", "caixa_ferramentas", "estante", "estante_livros",
         "estante_armas", "mesa_cadeiras", "mesa_banquete_luxo", "cama", "cama_casal", "arvore",
         "arvore_seca", "arvore_grande", "carroca", "lareira", "mesa_quimica"}

# Árvores comuns são centenas nos mapas de floresta: pesam pouco no sorteio.
PESO_TIPO = {"arvore": 0.25, "arvore_seca": 1.0, "arvore_grande": 1.0}

MAGICOS = {
    1: ["anel_protecao", "anel_vigia", "anel_impacto", "ring_str", "boina_batedor", "boina_alerta",
        "chapeu_cacador", "chapeu_explorador", "pocao_velocidade", "pocao_invisibilidade",
        "moeda_da_sorte", "solucao_mecanismo", "mira_do_falcao", "bote_da_serpente",
        "essencia_vento_favoravel", "flechas_magicas", "virotes_magicos", "kit_reparo_campo",
        "health_potion_improved"],
    2: ["espada_magica", "anel_aguia", "anel_negro_corvo", "anel_tigre", "mochila_dimensional",
        "pocao_voo", "pocao_barreira_arcana", "pocao_resistencia_fogo", "pocao_resistencia_gelo",
        "pocao_resistencia_acido", "gole_do_gigante", "elixir_cavalo_ferro", "sabedoria_liquida",
        "chapeu_bruxo", "flechas_magicas_mais_2", "virotes_magicos_mais_2", "calice_eter",
        "lagrima_ultima_luz", "amulet", "ring_vita", "manto_linho_engomado", "botas_passo_felino",
        "chapeu_aventureiro", "alforge_explorador_aprimorado", "aljava_grande"],
    3: ["espada_magica_mais_2", "lamina_trovejante", "punhal_assassino", "anel_urso_cinzento",
        "anel_supremacia", "chapeu_conjurador", "bracelete_guarda_reflexa", "espada_sangramento_longa",
        "ultimo_suspiro", "tiara_expansao_arcana", "amulet_alcance_arcano", "chicote_fogo",
        "anel_touro_ferro", "anel_danca_vento", "anel_bastiao_basalto", "anel_olho_esfinge",
        "chapeu_arquimago", "mochila_aljava_dimensional", "veste_egide_arcana", "alabarda_vendaval"],
}
COMIDA = ["pao", "carne_bovina", "pernil", "leite", "caldo_revigorante", "fermentado_raizes",
          "fruto_de_lumen", "racao_viagem", "racao_completa", "banquete_viagem", "suco_fruta"]
BEBIDA = ["hidromel", "rum", "absinto", "cerveja_ana", "caneca_cerveja", "garrafa_vinho", "cantil_agua"]
CURA = ["health_potion_small", "health_potion_improved"]


# Faixa de preço (moedas) dos itens mágicos que entram automaticamente em cada nível, além da
# lista curada acima. Fora daqui: pergaminhos, grimórios e relíquias lendárias.
FAIXA_PRECO = {1: (0, 400), 2: (400, 1600), 3: (1600, 5000)}


# Variantes de material (+1 mágicas dos monstros) ficam fora: já caem no saque deles.
_MATERIAL_RE = re.compile(r"_(aco_damasco|obsidiana_ferro|liga_titanio|prata|freixo_negro|cedro_rubro|cerne_tita)(_magica)?$")


def montar_pools(catalogo):
    """Lista de mágicos por nível: a curada + os itens `magical` do catálogo na faixa de preço."""
    pools = {n: [i for i in lst if i in catalogo] for n, lst in MAGICOS.items()}
    curados = {i for lst in pools.values() for i in lst}
    for iid in sorted(catalogo):
        it = catalogo[iid]
        if (iid in curados or not it.get("magical") or it.get("effect") in ("scroll", "grimoire")
                or _MATERIAL_RE.search(iid)):
            continue
        preco = it.get("price") or it.get("buy_price") or 0
        for n, (lo, hi) in FAIXA_PRECO.items():
            if lo < preco <= hi:
                pools[n].append(iid)
                break
    return pools


def _ler_ledger():
    try:
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _candidatos(defn, meta):
    """Objetos livres para esconder algo: nada de conteúdo, chave, armadilha ou parede."""
    saida = []
    for d in defn.get("decorations", []):
        if d.get("type") not in TIPOS or not meta.get(d["type"], {}).get("loot_capaz"):
            continue
        if d.get("loot") or d.get("escondido") or d.get("key_objective") or d.get("trap"):
            continue
        saida.append(d)
    return saida


def _alvo_quantidade(total_candidatos, existentes, area=None):
    """Quantos esconderijos o mapa deve ter no total (os já gravados contam). Mapa pequeno
    não ganha mais que 1 achado por ~90 casas, para não ficar abarrotado."""
    meta = max(3, min(9, round(2.5 + total_candidatos / 14)))
    if area:
        meta = min(meta, max(3, area // 90))
    return max(0, meta - existentes)


def _escolher_objetos(rng, cands, n):
    """Sorteia n objetos, espalhados (distância mínima entre eles) e com peso por tipo."""
    pool = list(cands)
    escolhidos = []
    for dist in (5, 3, 0):               # relaxa o espaçamento se faltar objeto
        while pool and len(escolhidos) < n:
            pesos = [PESO_TIPO.get(o["type"], 1.0) for o in pool]
            o = rng.choices(pool, weights=pesos)[0]
            pool.remove(o)
            if all(max(abs(o["pos"][0] - e["pos"][0]), abs(o["pos"][1] - e["pos"][1])) >= dist
                   for e in escolhidos):
                escolhidos.append(o)
        if len(escolhidos) >= n:
            break
        pool = [o for o in cands if o not in escolhidos]
    return escolhidos


def _conteudo(rng, nivel, usados, catalogo, magicos_usados, pools):
    """Um achado: mágico, comida ou um pouco dos dois. `usados` evita repetir item no mapa;
    `magicos_usados` evita repetir item mágico em toda a campanha (comida pode repetir)."""
    todos_magicos = {i for lst in pools.values() for i in lst}

    def pegar(lista, k=1):
        livres = [i for i in lista if i in catalogo and i not in usados
                  and not (i in todos_magicos and i in magicos_usados)]
        rng.shuffle(livres)
        achados = livres[:k]
        usados.update(achados)
        magicos_usados.update(i for i in achados if i in todos_magicos)
        return achados

    magicos = pools[nivel] + (pools[nivel - 1] if nivel > 1 else [])

    def magico():
        """Um mágico do nível; se a lista do nível acabou, desce (ou sobe) de nível."""
        for n in sorted(pools, key=lambda n: (abs(n - nivel), -n)):
            achado = pegar(pools[n])
            if achado:
                return achado
        return []

    tipo = rng.choices(["magico", "comida", "misto"], weights=[45, 35, 20])[0]
    itens, ouro = [], 0
    if tipo == "magico":
        itens = magico()
        if rng.random() < 0.25:
            itens += pegar(COMIDA + BEBIDA)
        ouro = rng.choice([0, 0, 15, 25, 40])
    elif tipo == "comida":
        itens = pegar(COMIDA, rng.choice([1, 2])) + pegar(BEBIDA, 1)
        if rng.random() < 0.4:
            itens += pegar(CURA)
        ouro = rng.choice([0, 5, 10])
    else:
        itens = (pegar(magicos) or magico()) + pegar(COMIDA) + pegar(BEBIDA)
        ouro = rng.choice([0, 10, 20])
    if not itens:                       # nunca esconde um objeto vazio
        itens = pegar(COMIDA) or pegar(BEBIDA)
    return tipo, ouro, [{"id": i} for i in itens]


def _limpar(defn, plano):
    """Desfaz um sorteio anterior: tira conteúdo e esconderijo dos objetos que ele escolheu."""
    for d in defn.get("decorations", []):
        if d.get("id") in plano:
            d["loot"] = None
            d.pop("escondido", None)
            d.pop("cd_busca", None)


def aplicar(simular=False, pasta=None, refazer=False, ledger=None, anterior=None):
    """`anterior`: sorteio gravado a desfazer quando `refazer` (padrão: o arquivo de ledger)."""
    import server as S
    pasta = pasta or S.DUNGEONS_DIR
    anterior = anterior if anterior is not None else _ler_ledger()
    gravado = {} if refazer else (ledger if ledger is not None else _ler_ledger())
    novo_ledger = {}
    relatorio = []
    pools = montar_pools(S._DUNGEON_ITEM_CATALOG)
    todos_magicos = {i for lst in pools.values() for i in lst}
    magicos_usados = set()      # já escondidos à mão ou sorteados antes, em qualquer mapa
    for mapa in MAPAS:
        with open(os.path.join(pasta, f"{mapa}.json"), encoding="utf-8") as f:
            defn0 = json.load(f)
            if refazer:
                _limpar(defn0, anterior.get(MAPAS[mapa][1] or mapa) or {})
            for d in defn0.get("decorations", []):
                for it in (d.get("loot") or {}).get("items", []):
                    if it.get("id") in todos_magicos:
                        magicos_usados.add(it["id"])
    for chave_p in (gravado or {}).values():       # o sorteio gravado conta como usado também
        for p in chave_p.values():
            magicos_usados.update(i["id"] for i in p["itens"] if i["id"] in todos_magicos)
    for mapa, (nivel, base) in MAPAS.items():
        caminho = os.path.join(pasta, f"{mapa}.json")
        with open(caminho, encoding="utf-8") as f:
            defn = json.load(f)
        if refazer:
            _limpar(defn, anterior.get(base or mapa) or {})
        decs = {d.get("id"): d for d in defn.get("decorations", [])}
        existentes = sum(1 for d in decs.values() if d.get("escondido")
                         and d.get("id") not in (gravado.get(base or mapa) or {}))
        chave = base or mapa
        if chave in novo_ledger:
            plano = novo_ledger[chave]
        elif chave in gravado:
            plano = gravado[chave]
        else:
            if base:                    # a variante lê o plano do original (mesmo arquivo de ledger)
                plano = novo_ledger.get(chave) or gravado.get(chave) or {}
            else:
                plano = {}
            if not plano:
                rng = random.Random(f"esconderijos:{chave}")
                cands = _candidatos(defn, S.DECOR_TYPES)
                n = _alvo_quantidade(len(cands) + existentes, existentes, defn["grid"]["w"] * defn["grid"]["h"])
                usados = {i["id"] for d in defn.get("decorations", []) for i in (d.get("loot") or {}).get("items", [])}
                plano = {}
                for o in _escolher_objetos(rng, cands, n):
                    tipo, ouro, itens = _conteudo(rng, nivel, usados, S._DUNGEON_ITEM_CATALOG, magicos_usados, pools)
                    plano[o["id"]] = {"tipo": o["type"], "cd": rng.choice([11, 12, 13, 14, 15][max(0, nivel - 1):nivel + 3]),
                                      "achado": tipo, "ouro": ouro, "itens": itens}
        novo_ledger[chave] = plano
        for did, p in plano.items():
            d = decs.get(did)
            if d is None or d.get("type") != p["tipo"]:
                relatorio.append(f"{mapa}: AVISO objeto {did} ({p['tipo']}) não existe mais; sorteie de novo com --refazer")
                continue
            for it in p["itens"]:
                if it["id"] not in S._DUNGEON_ITEM_CATALOG:
                    raise ValueError(f"{mapa}: item desconhecido {it['id']}")
            d["loot"] = {"gold": p["ouro"], "items": [dict(i) for i in p["itens"]]}
            d["escondido"] = True
            d["cd_busca"] = p["cd"]
            relatorio.append(f"{mapa}: {did} ({p['tipo']}, CD {p['cd']}, {p['achado']}) → "
                             + ", ".join(i["id"] for i in p["itens"]) + (f" + {p['ouro']} ouro" if p["ouro"] else ""))
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{mapa}: {msg}")
        if not simular:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(defn, f, ensure_ascii=False, indent=2)
    if not simular and ledger is None:
        with open(LEDGER, "w", encoding="utf-8") as f:
            json.dump(novo_ledger, f, ensure_ascii=False, indent=1, sort_keys=True)
    return relatorio


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--refazer", action="store_true")
    args = ap.parse_args(argv)
    for linha in aplicar(simular=args.simular, refazer=args.refazer):
        print(linha)
    print("(simulação: nada foi gravado)" if args.simular else "pronto.")


if __name__ == "__main__":
    main()
