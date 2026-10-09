"""Aplica a trilha curta da missão introdutória ao Campo de Treinamento."""

MESTRE = {
    "nome": "Mestre de Armas",
    "emoji": "🛡️",
    "retrato": "assets/portraits/mestre_de_armas.png",
}


def _fala(definicao, id):
    return next((fala for fala in definicao.get("falas", []) if fala.get("id") == id), None)


def _upsert(definicao, fala):
    atual = _fala(definicao, fala["id"])
    if atual is None:
        definicao.setdefault("falas", []).append(fala)
    else:
        atual.update(fala)


def aplicar(definicao):
    """Atualiza a missão sem remover falas avançadas ou lições de classe."""
    falas = definicao.setdefault("falas", [])
    por_id = {fala.get("id"): fala for fala in falas}

    # A mesma arte-base acompanha os passos comuns. As cenas maiores aparecem
    # só nos três marcos narrativos para manter o tabuleiro livre nas ações.
    for fala in falas:
        if not fala.get("classe"):
            falante = dict(MESTRE)
            falante.update(fala.get("falante") or {})
            falante["nome"] = "Mestre de Armas"
            falante["retrato"] = MESTRE["retrato"]
            fala["falante"] = falante

    config = {
        "fala_intro": {
            "ordem": -1, "pos": [3, 15],
            "texto": "A Guilda perdeu contato com a ala de treino. Confirme o que aconteceu e volte com o grupo.",
            "falante": {**MESTRE, "retrato": "assets/portraits/mestre_de_armas_briefing.png",
                        "cena": "assets/tela de transição/tutorial/briefing_guilda.png"},
        },
        "fala_camera": {
            "ordem": 0, "pos": [3, 15],
            "texto": "Antes de partir, ajuste a visão do tabuleiro e pratique a câmera.",
        },
        "fala_0": {
            "ordem": 1, "pos": [3, 15],
            "texto": "Vamos nos aproximar do baú de armas. Ande até a casa marcada.",
            "tarefa": {"tipo": "mover_ate", "alvo": [5, 15], "vezes": 1,
                       "texto_curto": "Aproxime-se do baú de armas"},
        },
        "fala_1": {
            "ordem": 2, "pos": [5, 16],
            "texto": "O baú contém armas para praticar. Pegue uma compatível com seu herói.",
            "tarefa": {"tipo": "pegar_item", "vezes": 1, "texto_curto": "Pegue uma arma do baú"},
        },
        "fala_2": {
            "ordem": 3, "pos": [5, 16],
            "texto": "Abra a bolsa e equipe a arma que pegou. Equipar é uma ação livre.",
        },
        "fala_menu_habilidades": {
            "id": "fala_menu_habilidades", "ordem": 4, "pos": [6, 15],
            "falante": dict(MESTRE),
            "texto": "Antes do combate, conheça as habilidades do seu herói.",
            "trigger": {"tipo": "proximidade", "raio": 4},
            "tarefa": {"tipo": "encerrar_turno", "vezes": 1,
                       "texto_curto": "Conheça o menu de habilidades"},
        },
        "fala_menu_magias": {
            "id": "fala_menu_magias", "ordem": 5, "pos": [6, 15],
            "falante": dict(MESTRE),
            "texto": "Confira também as magias que seu herói conhece.",
            "trigger": {"tipo": "proximidade", "raio": 4},
            "requisitos": {"magia_tipo": "qualquer"},
            "tarefa": {"tipo": "encerrar_turno", "vezes": 1,
                       "texto_curto": "Conheça o grimório"},
        },
        "fala_3": {
            "ordem": 6, "pos": [6, 15],
            "texto": "Os bonecos de treino esperam na próxima sala. Encerre o turno quando estiver pronto.",
        },
        "fala_4": {
            "ordem": 7, "pos": [11, 15],
            "texto": "Atravesse a porta para a ala de treino. A Guilda perdeu contato com esta área.",
            "tarefa": {"tipo": "mover_ate", "alvo": [13, 15], "vezes": 1,
                       "texto_curto": "Entre na ala de treino"},
        },
        "fala_primeiro_combate": {
            "id": "fala_primeiro_combate", "ordem": 8, "pos": [16, 15],
            "falante": dict(MESTRE), "texto": "Os bonecos não reagem. Faça um ataque para conferir seu equipamento.",
            "trigger": {"tipo": "sala", "raio": 2},
            "tarefa": {"tipo": "atacar", "alvo": "boneco_treino", "vezes": 1,
                       "texto_curto": "Ataque um boneco de treino"},
        },
        "fala_res": {
            "ordem": 9, "pos": [50, 17],
            "texto": "A ameaça é real: os esqueletos resistem a lâminas. Ataque um com espada ou adaga e compare o dano.",
            "falante": {**MESTRE, "retrato": "assets/portraits/mestre_de_armas_alerta.png",
                        "cena": "assets/tela de transição/tutorial/ameaca_esqueletos.png"},
            "tarefa": {"tipo": "atacar", "alvo": "esqueleto_humano", "vezes": 1,
                       "texto_curto": "Confirme a resistência dos esqueletos"},
        },
        "fala_vuln": {
            "ordem": 10, "pos": [50, 17],
            "texto": "A maça causa dano de impacto, ao qual o esqueleto é vulnerável. Pegue-a no baú, equipe e ataque.",
            "falante": {**MESTRE, "retrato": "assets/portraits/mestre_de_armas_alerta.png",
                        "cena": "assets/tela de transição/tutorial/ameaca_esqueletos.png"},
            "tarefa": {"tipo": "atacar", "alvo": "esqueleto_humano", "vezes": 1,
                       "texto_curto": "Explore a vulnerabilidade do esqueleto"},
        },
        "fala_retirada": {
            "id": "fala_retirada", "ordem": 11, "pos": [50, 16],
            "falante": {**MESTRE, "retrato": "assets/portraits/mestre_de_armas_conclusao.png",
                        "cena": "assets/tela de transição/tutorial/retorno_guilda.png"},
            "texto": "A ameaça está confirmada. Retire-se com o grupo e reúna todos na saída.",
            "trigger": {"tipo": "proximidade", "raio": 4},
            "tarefa": {"tipo": "mover_ate", "alvo": [53, 15], "vezes": 1,
                       "texto_curto": "Reúna o grupo na saída"},
        },
    }

    # Falas úteis que ficam no mapa, mas não interrompem a missão principal.
    ordens_opcionais = {
        "fala_17": 20, "fala_18": 21, "fala_19": 22, "fala_20": 23,
        "fala_hostilidade": 24, "fala_29": 25, "fala_30": 26,
        "fala_31": 27, "fala_32": 28, "fala_33": 29, "fala_34": 30,
        "fala_atalhos": 31,
    }
    for ident, ordem in ordens_opcionais.items():
        if ident in por_id:
            por_id[ident]["ordem"] = ordem

    for ident, valores in config.items():
        atual = _fala(definicao, ident)
        if atual is None:
            valores = {"id": ident, **valores}
            _upsert(definicao, valores)
        else:
            atual.update(valores)

    definicao.setdefault("objectives", {}).setdefault("primary", {})["type"] = "all_heroes_at_exit"
    return definicao
