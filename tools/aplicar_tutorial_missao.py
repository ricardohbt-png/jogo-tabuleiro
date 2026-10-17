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


def _configurar_ala_final(definicao):
    """Conecta aula de dano, corredor de armadilhas e sala de retirada."""
    grid = definicao.setdefault("grid", {})
    tiles = definicao.setdefault("tiles", [])
    w, h = int(grid.get("w", 0)), int(grid.get("h", 0))
    if w < 56 or h < 27 or len(tiles) < h:
        raise ValueError("O Campo de Treinamento precisa de um grid de ao menos 56x27.")
    for y, row in enumerate(tiles):
        if len(row) < w:
            row.extend([0] * (w - len(row)))
    altura_final = max(h, 32)
    tiles.extend([[0] * w for _ in range(altura_final - len(tiles))])
    grid["h"] = altura_final

    salas = definicao.setdefault("rooms", [])
    sala_aula = next((r for r in salas if r.get("id") == 48), None)
    if sala_aula is None:
        raise ValueError("A sala 48 da lição de dano não existe.")
    sala_aula.update({"x": 48, "y": 12, "w": 8, "h": 7})
    portas_aula = [list(p) for p in sala_aula.get("doors", []) if p != [51, 19]]
    portas_aula.append([51, 19])
    sala_aula["doors"] = portas_aula

    sala_saida = next((r for r in salas if r.get("id") == 49), None)
    if sala_saida is None:
        sala_saida = {"id": 49}
        salas.append(sala_saida)
    sala_saida.update({"x": 48, "y": 26, "w": 6, "h": 6,
                       "role": "empty", "locked": True, "doors": [[51, 25]]})

    sala_armadilhas = next((r for r in salas if r.get("id") == 50), None)
    if sala_armadilhas is None:
        sala_armadilhas = {"id": 50}
        salas.append(sala_armadilhas)
    sala_armadilhas.update({"x": 50, "y": 21, "w": 3, "h": 4,
                            "role": "empty", "locked": True,
                            "doors": [[51, 20], [51, 25]]})

    # Reorganiza a saída para que o corredor de armadilhas fique entre as aulas
    # de dano e a conclusão; a aplicação repetida do patch mantém o mesmo piso.
    for y in range(21, 27):
        for x in range(48, 54):
            tiles[y][x] = 0
    for y in range(12, 19):
        for x in range(48, 56):
            tiles[y][x] = 1
    tiles[19][51] = 2
    tiles[20][51] = 2
    for y in range(21, 25):
        for x in range(50, 53):
            tiles[y][x] = 1
    tiles[25][51] = 2
    for y in range(26, 32):
        for x in range(48, 54):
            tiles[y][x] = 1

    definicao["exit"] = {"x": 51, "y": 29}

    posicoes_antigas = {(42, 15), (49, 15)}
    traps_tutorial = [
        {"id": "trap_tutorial_dardos_1", "tipo": "armadilha_dardos_envenenados",
         "pos": [50, 21], "dificuldade": 14, "dano": "1",
         "veneno_id": "veneno_escorpiao_pedra"},
        {"id": "trap_tutorial_dardos_2", "tipo": "armadilha_dardos_envenenados",
         "pos": [52, 21], "dificuldade": 14, "dano": "1",
         "veneno_id": "veneno_escorpiao_pedra"},
        {"id": "trap_tutorial_buraco_1", "tipo": "buraco", "pos": [50, 22]},
        {"id": "trap_tutorial_buraco_2", "tipo": "buraco", "pos": [52, 22]},
        {"id": "trap_tutorial_fosso_1", "tipo": "fosso", "pos": [50, 23]},
        {"id": "trap_tutorial_fosso_2", "tipo": "fosso", "pos": [52, 23]},
        {"id": "trap_tutorial_urso_1", "tipo": "armadilha_urso", "pos": [50, 24]},
        {"id": "trap_tutorial_urso_2", "tipo": "armadilha_urso", "pos": [52, 24]},
        {"id": "trap_tutorial_rede_1", "tipo": "rede", "pos": [51, 21]},
        {"id": "trap_tutorial_rede_2", "tipo": "rede", "pos": [51, 22]},
        {"id": "trap_tutorial_teleporte", "tipo": "armadilha_teletransporte",
         "pos": [51, 23], "saida": [3, 15]},
    ]
    ids_armadilhas_tutorial = {t["id"] for t in traps_tutorial}
    definicao["traps"] = [
        t for t in definicao.get("traps", [])
        if t.get("id") not in ids_armadilhas_tutorial
        and tuple(t.get("pos") or ()) not in posicoes_antigas
        and tuple(t.get("pos") or ()) not in {tuple(x["pos"]) for x in traps_tutorial}
    ] + traps_tutorial


def aplicar(definicao):
    """Atualiza a missão sem remover falas avançadas ou lições de classe."""
    _configurar_ala_final(definicao)
    falas = definicao.setdefault("falas", [])
    # O menu H agora é ensinado como preâmbulo das salas exclusivas de classe.
    falas[:] = [fala for fala in falas if fala.get("id") not in {"fala_menu_habilidades", "fala_menu_magias"}]
    por_id = {fala.get("id"): fala for fala in falas}

    # A arte-base acompanha as falas comuns e as lições conduzidas pelo Mestre.
    # Retratos/clipes explícitos de outros falantes são preservados.
    for fala in falas:
        if not fala.get("classe"):
            falante = dict(MESTRE)
            falante.update(fala.get("falante") or {})
            falante["nome"] = "Mestre de Armas"
            falante["retrato"] = MESTRE["retrato"]
            fala["falante"] = falante
        elif (fala.get("falante") or {}).get("nome") == "Mestre de Armas":
            falante = dict(fala["falante"])
            falante.setdefault("retrato", MESTRE["retrato"])
            fala["falante"] = falante

    config = {
        "fala_intro": {
            "ordem": -1, "pos": [3, 15],
            "texto": "Bem-vindo! Esta é sua primeira missão no Campo de Treinamento. A Guilda perdeu contato com a ala de treino. Confirme o que aconteceu e volte com o grupo.",
            "falante": {**MESTRE, "retrato": "assets/portraits/mestre_de_armas_briefing.png",
                        "cena": "assets/tela de transição/tutorial/briefing_guilda.png"},
        },
        "fala_camera": {
            "ordem": 0, "pos": [3, 15],
            "texto": "Antes de partir, ajuste a visão do tabuleiro e pratique a câmera.",
        },
        "fala_0": {
            "ordem": 3, "pos": [3, 15],
            "texto": "Vamos nos aproximar do baú de armas. Ande até a casa marcada.",
            "tarefa": {"tipo": "mover_ate", "alvo": [5, 15], "vezes": 1,
                       "texto_curto": "Aproxime-se do baú de armas"},
        },
        "fala_1": {
            "ordem": 4, "pos": [5, 16],
            "texto": "O baú contém armas para praticar. Pegue uma compatível com seu herói.",
            "tarefa": {"tipo": "pegar_item", "vezes": 1, "texto_curto": "Pegue uma arma do baú"},
        },
        "fala_2": {
            "ordem": 5, "pos": [5, 16],
            "texto": "Abra a bolsa e equipe a arma que pegou. Equipar é uma ação livre.",
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
            "ordem": 32, "pos": [50, 17],
            "trigger": {"tipo": "sala"},
            "continua_sem": ["fala_atalhos"],
            "continua_sem_ativas": ["fala_atalhos"],
            "texto": "O boneco de treino reduz em 5 o dano cortante. Acerte-o com uma espada e observe o número azul com RESISTIDO.",
            "falante": {**MESTRE, "cena": "assets/tela de transição/tutorial/mestre_resistencia_vulnerabilidade.png"},
            "tarefa": {"tipo": "atacar", "alvo": "boneco_treino", "vezes": 1,
                       "requer_categoria_arma": "cortante", "requer_sala_alvo": 48,
                       "texto_curto": "Acerte o boneco com uma arma cortante"},
        },
        "fala_vuln": {
            "ordem": 33, "pos": [51, 15],
            "trigger": {"tipo": "proximidade", "raio": 1},
            "continua_sem": ["fala_res"],
            "texto": "Agora pegue e equipe o Cajado de Madeira no baú. Ele causa dano contundente: o boneco é vulnerável e recebe +2. Acerte-o e observe o número vermelho com VULNERÁVEL.",
            "falante": {**MESTRE, "cena": "assets/tela de transição/tutorial/mestre_resistencia_vulnerabilidade.png"},
            "tarefa": {"tipo": "atacar", "alvo": "boneco_treino", "vezes": 1,
                       "requer_categoria_arma": "contundente", "requer_sala_alvo": 48,
                       "texto_curto": "Acerte o boneco com o cajado"},
        },
        "fala_armadilhas": {
            "id": "fala_armadilhas", "ordem": 35, "pos": [51, 19],
            "falante": {**MESTRE, "cena": "assets/tela de transição/tutorial/mestre_aula_armadilhas.png"},
            "texto": "Esta passagem parece estranha. Avance com cuidado e observe cada armadilha.",
            "trigger": {"tipo": "proximidade", "raio": 1},
            "continua_sem": ["fala_res", "fala_vuln", "fala_atalhos"],
            "tarefa": {"tipo": "mover_ate", "alvo": [51, 24], "vezes": 1,
                       "texto_curto": "Atravesse o corredor de armadilhas"},
        },
        "fala_retirada": {
            "id": "fala_retirada", "ordem": 36, "pos": [51, 29],
            "falante": {**MESTRE, "retrato": "assets/portraits/mestre_de_armas_conclusao.png",
                        "cena": "assets/tela de transição/tutorial/retorno_guilda.png"},
            "texto": "A ameaça está confirmada. Retire-se com o grupo e reúna todos na saída.",
            "trigger": {"tipo": "proximidade", "raio": 1},
            "continua_sem": ["fala_res", "fala_vuln", "fala_atalhos"],
            "tarefa": {"tipo": "mover_ate", "alvo": [51, 29], "vezes": 1,
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

    # A mesma ilustração acompanha toda a sequência prática de consumíveis:
    # óleo arremessável, veneno aplicado à arma e poção de cura.
    cena_consumiveis = "assets/tela de transição/tutorial/mestre_aula_consumiveis.png"
    for ident in ("fala_29", "fala_30", "fala_31", "fala_32", "fala_33"):
        fala = _fala(definicao, ident)
        if fala is not None:
            fala.setdefault("falante", {})["cena"] = cena_consumiveis

    for ident, valores in config.items():
        atual = _fala(definicao, ident)
        if atual is None:
            valores = {"id": ident, **valores}
            _upsert(definicao, valores)
        else:
            atual.update(valores)

    provisoes = {
        "fala_18": (
            "Cada herói tem dois Banquetes de Viagem e uma Ração de Viagem no baú. "
            "Use os três; comida pode ser usada livremente no seu turno.",
            ["banquete_viagem", "racao_viagem"], 3,
            "Use dois banquetes e uma ração"),
        "fala_19": (
            "Agora use o Cantil de Água pessoal. Com ele, os medidores voltam a 100.",
            "cantil_agua", 1, "Use o Cantil de Água"),
    }
    for ident, (texto, alvos, vezes, texto_curto) in provisoes.items():
        fala = _fala(definicao, ident)
        if fala:
            fala["texto"] = texto
            tarefa = fala.setdefault("tarefa", {})
            tarefa.update({"tipo": "usar_item", "vezes": vezes,
                           "texto_curto": texto_curto})
            if isinstance(alvos, list):
                tarefa.pop("alvo", None)
                tarefa["alvos"] = alvos
            else:
                tarefa.pop("alvos", None)
                tarefa["alvo"] = alvos

    fala_fome_sede = _fala(definicao, "fala_17")
    if fala_fome_sede:
        fala_fome_sede.setdefault("efeito", {}).update({"fome": 0, "sede": 0})

    definicao.setdefault("objectives", {}).setdefault("primary", {})["type"] = "all_heroes_at_exit"
    # A ala final acima fixa a saída e a retirada da época; a fatia 20 (sala das reações de
    # terreno) as move para baixo. Aplicada aqui, nenhum caminho do pipeline a desfaz.
    from aplicar_fatia20_tutorial import aplicar as _aplicar_fatia20
    _aplicar_fatia20(definicao)
    return definicao
