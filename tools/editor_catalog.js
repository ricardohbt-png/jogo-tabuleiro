window.EDITOR_CATALOG = {
  "monsters": [
    {
      "type": "goblin",
      "name": "Goblin",
      "emoji": "👺",
      "tier": 1,
      "cr": 0.25,
      "hp": 8,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "atk_bonus": 2,
      "damage": "1d4",
      "gold": 5,
      "xp": 10,
      "subtipo": "raca_padrao"
    },
    {
      "type": "skeleton",
      "name": "Esqueleto",
      "emoji": "💀",
      "tier": 1,
      "cr": 0.5,
      "hp": 10,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "atk_bonus": 3,
      "damage": "1d6",
      "gold": 8,
      "xp": 15,
      "undead": true,
      "subtipo": "morto_vivo"
    },
    {
      "type": "orc",
      "name": "Orc",
      "emoji": "👹",
      "tier": 2,
      "cr": 0.75,
      "hp": 16,
      "ac": 14,
      "movement": 6,
      "vision_base": 0,
      "atk_bonus": 5,
      "damage": "1d8",
      "gold": 12,
      "xp": 25,
      "subtipo": "raca_padrao"
    },
    {
      "type": "dark_mage",
      "name": "Mago das Trevas",
      "emoji": "🧟",
      "tier": 2,
      "cr": 0.5,
      "hp": 12,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "atk_bonus": 4,
      "damage": "1d6",
      "gold": 20,
      "xp": 30,
      "subtipo": "raca_padrao"
    },
    {
      "type": "troll",
      "name": "Troll",
      "emoji": "🗿",
      "tier": 3,
      "cr": 1.5,
      "hp": 22,
      "ac": 16,
      "movement": 6,
      "vision_base": 0,
      "atk_bonus": 7,
      "damage": "1d10",
      "gold": 25,
      "xp": 40,
      "subtipo": "raca_padrao"
    },
    {
      "type": "dragon",
      "name": "Dragão Ancião",
      "emoji": "🐉",
      "boss": true,
      "tier": 4,
      "cr": 5.0,
      "hp": 60,
      "ac": 20,
      "movement": 6,
      "vision_base": 0,
      "atk_bonus": 12,
      "damage": "2d8",
      "gold": 100,
      "xp": 200,
      "subtipo": "raca_padrao"
    },
    {
      "type": "aranha_sombria",
      "name": "Aranha Sombria",
      "emoji": "🕷️",
      "boss": false,
      "tier": 1,
      "cr": 0.25,
      "hp": 8,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "aranhasombria",
      "str_": 8,
      "dex": 16,
      "con_": 10,
      "int_": 2,
      "fort": 2,
      "ref_": 5,
      "will": -4,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 1,
          "damage": "1d4-1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": "veneno_aranha_sombria"
        }
      ],
      "special_abilities": [
        {
          "id": "disparo_teia",
          "name": "Disparo de Teia",
          "action_type": "acao",
          "uses_per_combat": 1,
          "range": 4,
          "target": "single",
          "dc": 11,
          "save": "reflexos",
          "damage": null,
          "damage_types": [],
          "effect": "perde_turno",
          "effect_duration": 1
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2
        }
      ],
      "loot_table": {
        "1-50": null,
        "51-100": {
          "tipo": "item",
          "id": "veneno_aranha_sombria"
        }
      },
      "ai_type": "emboscador",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "escorpiao_pedra",
      "name": "Escorpião de Pedra",
      "emoji": "🦂",
      "boss": false,
      "tier": 1,
      "cr": 0.5,
      "hp": 12,
      "ac": 14,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "escorpiaodepedra",
      "str_": 10,
      "dex": 12,
      "con_": 12,
      "int_": 1,
      "fort": 4,
      "ref_": 3,
      "will": 0,
      "attacks": [
        {
          "name": "Pinça",
          "atk_bonus": 2,
          "damage": "1d4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "on_hit": null
        },
        {
          "name": "Ferrão",
          "atk_bonus": 2,
          "damage": "1d4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": "veneno_escorpiao_pedra"
        }
      ],
      "special_abilities": [
        {
          "id": "envenenar",
          "name": "Envenenar",
          "action_type": "passiva",
          "attack_index": 1,
          "veneno_id": "veneno_escorpiao_pedra",
          "poison_dc": 9,
          "descricao": "Vincula um veneno escolhido a um dos ataques da criatura."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2
        }
      ],
      "loot_table": {
        "1-60": {
          "tipo": "item",
          "id": "veneno_escorpiao_pedra"
        },
        "61-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "esqueleto_humano",
      "name": "Esqueleto Humano",
      "emoji": "💀",
      "boss": false,
      "tier": 1,
      "cr": 0.5,
      "hp": 10,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "esqueletoHumano",
      "str_": 10,
      "dex": 12,
      "con_": 10,
      "int_": 2,
      "fort": 2,
      "ref_": 3,
      "will": 0,
      "attacks": [
        {
          "name": "Espada Curta",
          "atk_bonus": 2,
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "cortante"
        }
      ],
      "special_abilities": [
        {
          "id": "sem_dor",
          "name": "Sem Dor",
          "action_type": "passiva"
        },
        {
          "id": "corpo_inerte",
          "name": "Corpo Inerte",
          "action_type": "passiva"
        },
        {
          "id": "fraqueza_magica",
          "name": "Fraqueza Mágica",
          "action_type": "passiva",
          "descricao": "-2 em testes contra magias que controlam mortos-vivos"
        }
      ],
      "immunities": [
        "veneno",
        "controle_mental"
      ],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "perfurante",
          "bonus_flat": -2,
          "descricao": "Resistência a perfurante (-2 dano)"
        },
        {
          "type": "physical",
          "categoria": "cortante",
          "bonus_flat": -1,
          "descricao": "Resistência a cortante (-1 dano)"
        },
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2,
          "descricao": "Vulnerável a impacto (+2 dano)"
        },
        {
          "type": "sagrado",
          "multiplier": 2,
          "descricao": "Dano sagrado dobrado"
        }
      ],
      "loot_table": {
        "1-70": null,
        "71-90": {
          "tipo": "gold",
          "valor": 2
        },
        "91-100": {
          "tipo": "gold",
          "valor": 4
        }
      },
      "ai_type": "esqueleto_humano",
      "undead": true,
      "subtipo": "morto_vivo",
      "darkvision_range": 4
    },
    {
      "type": "esqueleto_animal",
      "name": "Esqueleto Animal",
      "emoji": "🦴",
      "boss": false,
      "tier": 1,
      "cr": 0.5,
      "hp": 8,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "esqueletoAnimal",
      "str_": 12,
      "dex": 14,
      "con_": 10,
      "int_": 2,
      "fort": 2,
      "ref_": 4,
      "will": 0,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "movimento_erratico",
          "name": "Movimento Errático",
          "action_type": "passiva",
          "descricao": "Ignora penalidades de movimento de Água e Água Profunda"
        },
        {
          "id": "sem_instinto",
          "name": "Sem Instinto",
          "action_type": "passiva",
          "descricao": "Nunca foge nem recua — avança até ser destruído"
        },
        {
          "id": "fraqueza_magica",
          "name": "Fraqueza Mágica",
          "action_type": "passiva",
          "descricao": "-2 em testes contra magias que controlam mortos-vivos"
        }
      ],
      "immunities": [
        "veneno",
        "controle_mental"
      ],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "perfurante",
          "bonus_flat": -2,
          "descricao": "Resistência a perfurante (-2 dano)"
        },
        {
          "type": "physical",
          "categoria": "cortante",
          "bonus_flat": -1,
          "descricao": "Resistência a cortante (-1 dano)"
        },
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2,
          "descricao": "Vulnerável a impacto (+2 dano)"
        },
        {
          "type": "sagrado",
          "multiplier": 2,
          "descricao": "Dano sagrado dobrado"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "esqueleto_animal",
      "undead": true,
      "subtipo": "morto_vivo",
      "darkvision_range": 8
    },
    {
      "type": "lobo_cinzento",
      "name": "Lobo Cinzento",
      "emoji": "🐺",
      "boss": false,
      "tier": 1,
      "cr": 0.5,
      "hp": 16,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "loboCinzento",
      "str_": 14,
      "dex": 14,
      "con_": 12,
      "int_": 2,
      "fort": 4,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null
        }
      ],
      "special_abilities": [
        {
          "id": "caca_em_bando",
          "name": "Caça em Bando",
          "action_type": "passiva"
        },
        {
          "id": "derrubar",
          "name": "Derrubar",
          "action_type": "passiva",
          "dc": 11,
          "save": "reflexos"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "fortitude",
          "bonus_flat": -2,
          "descricao": "Sensível a venenos — -2 Fort vs venenos"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "lobo_cinzento",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "cobra_constritora",
      "name": "Cobra Constritora",
      "emoji": "🐍",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 14,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "cobraConstritora",
      "str_": 14,
      "dex": 14,
      "con_": 12,
      "int_": 1,
      "fort": 4,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "constricao",
          "name": "Constrição",
          "action_type": "passiva",
          "dc": 11,
          "save": "fortitude",
          "escape_saves": [
            "fortitude"
          ],
          "descricao": "Ao acertar, alvo testa FOR CD 11 — falha: preso"
        },
        {
          "id": "esmagar",
          "name": "Esmagar",
          "action_type": "passiva",
          "descricao": "Enquanto preso e adjacente: 1d6 dano automático por turno"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "cortante",
          "bonus_flat": 2,
          "descricao": "Corpo vulnerável a corte (+2 dano cortante)"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "cobra_constritora",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "cobra_venenosa",
      "name": "Cobra Venenosa",
      "emoji": "🐍",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 14,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "cobraVenenosa",
      "str_": 10,
      "dex": 14,
      "con_": 12,
      "int_": 1,
      "fort": 3,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": "veneno_cobra_cuspidora",
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "veneno",
          "name": "Veneno",
          "action_type": "passiva",
          "descricao": "Ao acertar a mordida, aplica veneno (doença leve)"
        },
        {
          "id": "ataque_rapido",
          "name": "Ataque Rápido",
          "action_type": "passiva",
          "descricao": "Se não se mover no turno: +1 no ataque"
        },
        {
          "id": "camuflagem_natural",
          "name": "Camuflagem Natural",
          "action_type": "passiva",
          "descricao": "+2 CA contra o primeiro ataque em terreno natural"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 1,
          "descricao": "Corpo frágil (+1 dano de concussão)"
        }
      ],
      "loot_table": {
        "1-90": null,
        "91-100": {
          "tipo": "item",
          "id": "veneno_cobra_cuspidora"
        }
      },
      "ai_type": "cobra_venenosa",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "devorador_organico",
      "name": "Devorador Orgânico",
      "emoji": "🟢",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 16,
      "ac": 11,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "devoradorOrganico",
      "str_": 12,
      "dex": 10,
      "con_": 12,
      "int_": 2,
      "fort": 3,
      "ref_": 2,
      "will": 1,
      "attacks": [
        {
          "name": "Toque Corrosivo",
          "atk_bonus": 3,
          "damage": "1d6+1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "contundente"
        }
      ],
      "special_abilities": [
        {
          "id": "toque_putrefato",
          "name": "Toque Putrefato",
          "action_type": "passiva",
          "descricao": "Ao acertar: +1 nível de dano em equipamento orgânico do alvo (couro/madeira/tecido)"
        },
        {
          "id": "corrosao_viva",
          "name": "Corrosão Viva",
          "action_type": "passiva",
          "descricao": "Alvo sem armadura: 1 dano/turno por 2 turnos (acumula a cada acerto)"
        },
        {
          "id": "absorver_materia",
          "name": "Absorver Matéria",
          "action_type": "passiva",
          "descricao": "Quando destrói um item orgânico: recupera 1d4 HP"
        }
      ],
      "immunities": [
        "cegueira",
        "escuridao"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 2,
          "descricao": "Combustão rápida (dano de fogo dobrado)"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-80": {
          "tipo": "gold",
          "valor": "1d2"
        },
        "81-100": {
          "tipo": "gold",
          "valor": "1d6"
        }
      },
      "ai_type": "devorador_organico",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "urso_negro",
      "name": "Urso Negro",
      "emoji": "🐻",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 18,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ursoNegro",
      "str_": 18,
      "dex": 12,
      "con_": 14,
      "int_": 2,
      "fort": 5,
      "ref_": 3,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 6,
          "damage": "1d8+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        },
        {
          "name": "Garra",
          "atk_bonus": 6,
          "damage": "1d6+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "cortante"
        }
      ],
      "special_abilities": [
        {
          "id": "furia",
          "name": "Fúria",
          "action_type": "passiva",
          "descricao": "Com HP < 50%: +2 de dano em todos os ataques"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "perfurante",
          "bonus_flat": 1,
          "descricao": "Corpo massivo: +1 dano de perfuração/alcance (arcos, bestas, lanças)"
        },
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": -1,
          "descricao": "Corpo massivo: -1 dano de concussão (martelos, maças, bastões)"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "orc_guerreiro",
      "name": "Orc Guerreiro",
      "emoji": "👹",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 17,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "orcGuerreiro",
      "str_": 16,
      "dex": 12,
      "con_": 14,
      "int_": 8,
      "fort": 5,
      "ref_": 3,
      "will": 1,
      "attacks": [
        {
          "name": "Machado",
          "atk_bonus": 5,
          "damage": "1d10+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "cortante"
        }
      ],
      "special_abilities": [
        {
          "id": "investida_brutal",
          "name": "Investida Brutal",
          "action_type": "passiva",
          "descricao": "Se mover antes de atacar: +2 de dano"
        },
        {
          "id": "furia_cega",
          "name": "Fúria Cega",
          "action_type": "passiva",
          "descricao": "Se sofreu dano na rodada anterior: +1 de dano, mas -1 CA"
        },
        {
          "id": "mente_limitada",
          "name": "Mente Limitada",
          "action_type": "passiva",
          "descricao": "-1 em testes de Vontade contra efeitos mentais"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -1,
          "em_magia": true,
          "descricao": "Mente limitada: -1 em Vontade contra efeitos mentais"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 4
        },
        "91-100": {
          "tipo": "gold",
          "valor": 6
        }
      },
      "guaranteed_loot": [
        "machado_orc"
      ],
      "ai_type": "orc_guerreiro",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "goblin_arqueiro",
      "name": "Goblin Arqueiro",
      "emoji": "👺",
      "boss": false,
      "tier": 1,
      "cr": 0.25,
      "hp": 9,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "pequeno",
      "image": "goblinArqueiro",
      "str_": 10,
      "dex": 14,
      "con_": 10,
      "int_": 10,
      "fort": 2,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Arco Curto",
          "atk_bonus": 4,
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "range": 8,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "mente_fraca",
          "name": "Mente Fraca",
          "action_type": "passiva",
          "descricao": "-2 em testes de Vontade contra magias de controle mental"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -2,
          "em_magia": true,
          "descricao": "Mente fraca: -2 em Vontade contra controle mental"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 2
        },
        "91-100": {
          "tipo": "gold",
          "valor": 3
        }
      },
      "guaranteed_loot": [
        "arco_curto"
      ],
      "ai_type": "goblin_arqueiro",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "goblin_combatente",
      "name": "Goblin Combatente",
      "emoji": "👺",
      "boss": false,
      "tier": 1,
      "cr": 0.25,
      "hp": 9,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "pequeno",
      "image": "goblinCombatente",
      "str_": 10,
      "dex": 14,
      "con_": 10,
      "int_": 10,
      "fort": 2,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Adaga",
          "atk_bonus": 4,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "arremesso",
          "name": "Arremesso",
          "action_type": "acao_bonus",
          "descricao": "Arremesso 1d4+2 (alcance 3) como ação bônus; 1 natural quebra a arma"
        },
        {
          "id": "mente_fraca",
          "name": "Mente Fraca",
          "action_type": "passiva",
          "descricao": "-2 em testes de Vontade contra magias de controle mental"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -2,
          "em_magia": true,
          "descricao": "Mente fraca: -2 em Vontade contra controle mental"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 2
        },
        "91-100": {
          "tipo": "gold",
          "valor": 3
        }
      },
      "guaranteed_loot": [
        "dagger"
      ],
      "ai_type": "goblin_melee",
      "undead": false,
      "subtipo": "vegetal"
    },
    {
      "type": "goblin_dual",
      "name": "Goblin Dual",
      "emoji": "👺",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 9,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "goblinDual",
      "str_": 10,
      "dex": 14,
      "con_": 10,
      "int_": 10,
      "fort": 2,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Espada Curta",
          "atk_bonus": 2,
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "cortante"
        },
        {
          "name": "Adaga",
          "atk_bonus": 4,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "arremesso",
          "name": "Arremesso",
          "action_type": "acao_bonus",
          "descricao": "Arremesso 1d4+2 (alcance 3) como ação bônus; 1 natural quebra a arma"
        },
        {
          "id": "mente_fraca",
          "name": "Mente Fraca",
          "action_type": "passiva",
          "descricao": "-2 em testes de Vontade contra magias de controle mental"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -2,
          "em_magia": true,
          "descricao": "Mente fraca: -2 em Vontade contra controle mental"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 2
        },
        "91-100": {
          "tipo": "gold",
          "valor": 3
        }
      },
      "guaranteed_loot": [
        "shortsword",
        "dagger"
      ],
      "ai_type": "goblin_melee",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "goblin_xama",
      "name": "Xamã Goblin",
      "emoji": "👺",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 10,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "pequeno",
      "image": "xamaGoblin",
      "str_": 8,
      "dex": 14,
      "con_": 10,
      "int_": 12,
      "fort": 2,
      "ref_": 4,
      "will": 3,
      "attacks": [
        {
          "name": "Cajado",
          "atk_bonus": 3,
          "damage": "1d6-1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "contundente"
        }
      ],
      "special_abilities": [
        {
          "id": "silencio",
          "name": "Silêncio",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 2,
          "descricao": "Cria área de Silêncio (some se o xamã morrer)"
        },
        {
          "id": "amaldicoar",
          "name": "Amaldiçoar",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1,
          "descricao": "Debuff -1 em ataque/dano/CA/resistência nos heróis"
        },
        {
          "id": "abencoar",
          "name": "Abençoar",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1,
          "descricao": "Buff +1 em ataque/dano/CA/resistência nos goblins aliados"
        },
        {
          "id": "concentracao_fragil",
          "name": "Concentração Frágil",
          "action_type": "passiva",
          "descricao": "Se sofrer dano, não pode usar magia no próximo turno"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -2,
          "em_magia": true,
          "descricao": "Mente fraca: -2 em Vontade contra controle mental"
        }
      ],
      "loot_table": {
        "1-20": null,
        "21-40": {
          "tipo": "item",
          "id": "garrafa_vinho"
        },
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 4
        },
        "91-98": {
          "tipo": "gold",
          "valor": 6
        },
        "99-100": {
          "tipo": "raro_xama"
        }
      },
      "ai_type": "goblin_xama",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "kobold_lanceiro",
      "name": "Kobold Lanceiro",
      "emoji": "🐊",
      "boss": false,
      "tier": 1,
      "cr": 0.25,
      "hp": 7,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "pequeno",
      "image": "koboldlanceiro",
      "str_": 8,
      "dex": 14,
      "con_": 10,
      "int_": 12,
      "fort": 2,
      "ref_": 4,
      "will": 2,
      "attacks": [
        {
          "name": "Lança Curta",
          "atk_bonus": 1,
          "damage": "1d6-1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null
        }
      ],
      "special_abilities": [
        {
          "id": "envenenar_arma",
          "name": "Envenenar Arma",
          "action_type": "passiva",
          "descricao": "Usa um veneno da bolsa para envenenar a arma como ação livre"
        },
        {
          "id": "covardia_kobold",
          "name": "Covardia Instintiva",
          "action_type": "passiva",
          "dc": 10,
          "save": "vontade",
          "effect": "medo_kobold",
          "effect_duration": 2
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 1
        },
        "71-90": {
          "tipo": "gold",
          "valor": 2
        },
        "91-100": {
          "tipo": "item",
          "id": "veneno_aranha_sombria"
        }
      },
      "ai_type": "kobold_lanceiro",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "kobold_besteiro",
      "name": "Kobold Besteiro",
      "emoji": "🐊",
      "boss": false,
      "tier": 1,
      "cr": 0.25,
      "hp": 7,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "pequeno",
      "image": "koboldbesteiro",
      "str_": 8,
      "dex": 14,
      "con_": 10,
      "int_": 12,
      "fort": 2,
      "ref_": 4,
      "will": 2,
      "attacks": [
        {
          "name": "Besta de Mão",
          "atk_bonus": 4,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "range": 4
        }
      ],
      "special_abilities": [
        {
          "id": "covardia_kobold",
          "name": "Covardia Instintiva",
          "action_type": "passiva",
          "dc": 10,
          "save": "vontade",
          "effect": "medo_kobold",
          "effect_duration": 2
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 1
        },
        "71-90": {
          "tipo": "gold",
          "valor": 2
        },
        "91-95": {
          "tipo": "item",
          "id": "veneno_aranha_sombria"
        },
        "96-100": {
          "tipo": "item",
          "id": "virote_incendiario",
          "qtd": "1d6"
        }
      },
      "ai_type": "kobold_besteiro",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "necromante",
      "name": "Necromante",
      "emoji": "🧙",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 16,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "necromante",
      "str_": 8,
      "dex": 12,
      "con_": 12,
      "int_": 16,
      "fort": 4,
      "ref_": 4,
      "will": 6,
      "attacks": [
        {
          "name": "Adaga",
          "atk_bonus": 4,
          "damage": "1d4+1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "bola_fogo",
          "name": "Bola de Fogo",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1
        },
        {
          "id": "medo",
          "name": "Medo",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1
        },
        {
          "id": "amaldicoar",
          "name": "Amaldiçoar",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1
        },
        {
          "id": "dominar_morto_vivo",
          "name": "Dominar Morto-Vivo",
          "action_type": "acao",
          "range": 4,
          "circulo": 3
        },
        {
          "id": "mestre_dos_mortos",
          "name": "Mestre dos Mortos",
          "action_type": "acao",
          "uses_per_combat": 1,
          "descricao": "Na primeira ação, conjura 2 esqueletos humanos ou animais à escolha do Mestre"
        },
        {
          "id": "concentracao_sombria",
          "name": "Concentração Sombria",
          "action_type": "passiva",
          "descricao": "Ao sofrer dano: Vontade CD 10 ou perde a ação de magia no turno"
        },
        {
          "id": "essencia_profana",
          "name": "Essência Profana",
          "action_type": "passiva",
          "descricao": "Sofre dano dobrado de efeitos sagrados/luz"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "holy",
          "multiplier": 2,
          "descricao": "Essência profana: dano sagrado/luz dobrado"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "necromante",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "zumbi_infectado",
      "name": "Zumbi Infectado",
      "emoji": "🧟",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 22,
      "ac": 10,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "zumbi",
      "str_": 14,
      "dex": 6,
      "con_": 16,
      "int_": 3,
      "fort": 5,
      "ref_": 0,
      "will": 1,
      "attacks": [
        {
          "name": "Golpe",
          "atk_bonus": 4,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "contundente"
        }
      ],
      "special_abilities": [
        {
          "id": "resistencia_morta",
          "name": "Resistência Morta",
          "action_type": "passiva",
          "dc": 10,
          "save": "fortitude",
          "descricao": "A 0 HP: Fortitude CD 10 + metade do dano excedente (arredonda para cima) → fica com 1 HP (dano sagrado/luz ignora e destrói de vez)"
        },
        {
          "id": "infeccao",
          "name": "Infecção",
          "action_type": "passiva",
          "dc": 10,
          "save": "fortitude",
          "disease_severity": "leve",
          "descricao": "Ao acertar: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve"
        },
        {
          "id": "lento_incansavel",
          "name": "Lento e Incansável",
          "action_type": "passiva",
          "descricao": "Não corre nem foge — avança sem parar"
        },
        {
          "id": "corpo_morto",
          "name": "Corpo Morto",
          "action_type": "passiva",
          "descricao": "Não come, bebe nem respira"
        }
      ],
      "immunities": [
        "veneno",
        "controle_mental"
      ],
      "weaknesses": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "zumbi",
      "undead": true,
      "subtipo": "morto_vivo",
      "darkvision_range": 8
    },
    {
      "type": "devorador_metal",
      "name": "Devorador de Metal",
      "emoji": "🔩",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 22,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "devoradordemetal",
      "str_": 14,
      "dex": 10,
      "con_": 14,
      "int_": 3,
      "fort": 4,
      "ref_": 2,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1d8+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "mordida_corrosiva",
          "name": "Mordida Corrosiva",
          "action_type": "passiva",
          "descricao": "Ao acertar: +1 nível de dano na arma OU armadura metálica do alvo"
        },
        {
          "id": "devorar_metal",
          "name": "Devorar Metal",
          "action_type": "passiva",
          "descricao": "Item a 3 níveis é destruído e o Devorador recupera 1d6 HP"
        },
        {
          "id": "alimentacao_metalica",
          "name": "Alimentação Metálica",
          "action_type": "passiva",
          "descricao": "Gasta a ação para consumir item metálico no chão e recuperar 1d6 HP"
        }
      ],
      "immunities": [
        "cegueira",
        "escuridao"
      ],
      "weaknesses": [
        {
          "type": "lightning",
          "bonus_flat": 2,
          "descricao": "Corpo condutor: +2 de dano de eletricidade"
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "1d6"
        }
      },
      "ai_type": "devorador_metal",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "bugbear_sombras",
      "name": "Bugbear — Bicho-Papão das Sombras",
      "emoji": "😈",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 22,
      "ac": 14,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "bugbear",
      "str_": 16,
      "dex": 16,
      "con_": 12,
      "int_": 8,
      "fort": 4,
      "ref_": 5,
      "will": 2,
      "attacks": [
        {
          "name": "Garras",
          "atk_bonus": 6,
          "damage": "1d6+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "on_hit": null,
          "categoria": "cortante"
        },
        {
          "name": "Mordida",
          "atk_bonus": 6,
          "damage": "1d8+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "manto_escuridao",
          "name": "Manto de Escuridão",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1,
          "descricao": "Cria uma área de escuridão centrada em si (1x por combate)"
        },
        {
          "id": "ataque_das_sombras",
          "name": "Ataque das Sombras",
          "action_type": "passiva",
          "descricao": "Se o alvo não o enxerga (bugbear oculto OU alvo na escuridão sem visão no escuro): +2 ataque e +1d6 de dano em TODOS os ataques"
        },
        {
          "id": "cacador_das_trevas",
          "name": "Caçador das Trevas",
          "action_type": "passiva",
          "descricao": "Em área escura: +2 CA, +1 ataque e sempre pode usar Ataque das Sombras"
        },
        {
          "id": "desaparecer_nas_sombras",
          "name": "Desaparecer nas Sombras",
          "action_type": "acao_livre",
          "cooldown_turns": 5,
          "descricao": "Só na escuridão (após Manto): fica oculto (imune a ataques à distância; corpo a corpo -4), move até 3, até o início do próximo turno"
        },
        {
          "id": "visao_perfeita_escuro",
          "name": "Visão no Escuro",
          "action_type": "passiva",
          "descricao": "Enxerga perfeitamente no escuro — não sofre penalidades nas trevas"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 2,
          "descricao": "Criatura das sombras: sofre dano dobrado de fogo"
        },
        {
          "type": "holy",
          "multiplier": 2,
          "descricao": "Criatura das sombras: sofre dano dobrado de efeitos sagrados/luz"
        },
        {
          "type": "luz_direta",
          "atk_penalty": -2,
          "descricao": "Sob luz direta: -2 em ataques"
        }
      ],
      "loot_table": {
        "1-57": null,
        "58-60": {
          "tipo": "instrumento_aleatorio"
        },
        "61-85": {
          "tipo": "gold",
          "valor": 2
        },
        "86-95": {
          "tipo": "gold",
          "valor": 4
        },
        "96-98": {
          "tipo": "scroll",
          "magia_id": "manto_escuridao"
        },
        "99-100": {
          "tipo": "item",
          "id": "vela_escuridao"
        }
      },
      "ai_type": "bugbear_sombras",
      "undead": false,
      "subtipo": "raca_padrao",
      "darkvision_range": 99
    },
    {
      "type": "ogro_clava",
      "name": "Ogro de Clava",
      "emoji": "🧌",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 32,
      "ac": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ogroClava",
      "str_": 18,
      "dex": 8,
      "con_": 17,
      "int_": 6,
      "fort": 5,
      "ref_": 1,
      "will": 0,
      "attacks": [
        {
          "name": "Clava Pesada",
          "atk_bonus": 6,
          "damage": "1d12+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "contundente"
        }
      ],
      "special_abilities": [
        {
          "id": "golpe_brutal",
          "name": "Golpe Brutal",
          "action_type": "ataque",
          "cooldown_turns": 3,
          "descricao": "+2 de dano ao ataque (recarga 3 rodadas); usado para finalizar"
        },
        {
          "id": "forca_descomunal",
          "name": "Força Descomunal",
          "action_type": "ataque",
          "cooldown_turns": 4,
          "save": "fortitude",
          "dc": 10,
          "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a próxima rodada). Recarga 4 rodadas"
        },
        {
          "id": "mente_bruta",
          "name": "Mente Bruta",
          "action_type": "passiva",
          "descricao": "-2 em Vontade contra controle mental"
        },
        {
          "id": "lento_previsivel",
          "name": "Lento e Previsível",
          "action_type": "passiva",
          "descricao": "Se errar um ataque: -2 de CA até o próximo turno"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -2,
          "em_magia": true,
          "descricao": "Mente Bruta: -2 em Vontade contra controle mental"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 4
        },
        "91-100": {
          "tipo": "comida"
        }
      },
      "ai_type": "ogro",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "ogro_lanca",
      "name": "Ogro de Lança",
      "emoji": "🧌",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 32,
      "ac": 14,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ogroLanca",
      "str_": 18,
      "dex": 8,
      "con_": 17,
      "int_": 6,
      "fort": 5,
      "ref_": 1,
      "will": 0,
      "attacks": [
        {
          "name": "Lança Grande",
          "atk_bonus": 6,
          "damage": "1d10+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "golpe_brutal",
          "name": "Golpe Brutal",
          "action_type": "ataque",
          "cooldown_turns": 3,
          "descricao": "+2 de dano ao ataque (recarga 3 rodadas); usado para finalizar"
        },
        {
          "id": "forca_descomunal",
          "name": "Força Descomunal",
          "action_type": "ataque",
          "cooldown_turns": 4,
          "save": "fortitude",
          "dc": 10,
          "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a próxima rodada). Recarga 4 rodadas"
        },
        {
          "id": "mente_bruta",
          "name": "Mente Bruta",
          "action_type": "passiva",
          "descricao": "-2 em Vontade contra controle mental"
        },
        {
          "id": "lento_previsivel",
          "name": "Lento e Previsível",
          "action_type": "passiva",
          "descricao": "Se errar um ataque: -2 de CA até o próximo turno"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "save": "vontade",
          "bonus_flat": -2,
          "em_magia": true,
          "descricao": "Mente Bruta: -2 em Vontade contra controle mental"
        }
      ],
      "loot_table": {
        "1-40": null,
        "41-70": {
          "tipo": "gold",
          "valor": 2
        },
        "71-90": {
          "tipo": "gold",
          "valor": 4
        },
        "91-100": {
          "tipo": "comida"
        }
      },
      "ai_type": "ogro",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "elemental_fogo",
      "name": "Elemental de Fogo",
      "emoji": "🔥",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 28,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_fogo",
      "str_": 14,
      "dex": 14,
      "con_": 14,
      "int_": 2,
      "fort": 4,
      "ref_": 4,
      "will": -4,
      "attacks": [
        {
          "name": "Chama",
          "atk_bonus": 5,
          "damage": "1d10+3",
          "damage_types": [
            "fire"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "fogo",
          "ignora_resistencia_leve_fogo": true
        }
      ],
      "special_abilities": [
        {
          "id": "corpo_energetico",
          "name": "Corpo Energético",
          "action_type": "passiva",
          "damage": "1d4",
          "damage_types": [
            "fire"
          ],
          "descricao": "Pode atravessar um quadrado ocupado, causa 1d4 de fogo ao ocupante e termina em uma casa livre."
        },
        {
          "id": "corpo_em_chamas",
          "name": "Corpo em Chamas",
          "action_type": "passiva",
          "damage": "1d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Quem o acerta com um ataque corpo a corpo sofre 1d6 de dano de fogo."
        },
        {
          "id": "explosao_final",
          "name": "Explosão Final",
          "action_type": "passiva",
          "damage": "6d6",
          "damage_types": [
            "fire"
          ],
          "radius": 1,
          "save": "reflexos",
          "dc": 13,
          "descricao": "Ao morrer, explode em 1 quadrado: 6d6 de fogo; Reflexos CD 13 reduz à metade."
        },
        {
          "id": "intensidade",
          "name": "Intensidade",
          "action_type": "passiva",
          "descricao": "As chamas ignoram reduções leves de dano de fogo (não ignora resistência à metade)."
        }
      ],
      "immunities": [
        "fire"
      ],
      "weaknesses": [
        {
          "type": "cold",
          "multiplier": 1.5,
          "descricao": "Gelo causa 1,5× de dano."
        }
      ],
      "loot_table": {
        "1-55": null,
        "56-85": {
          "tipo": "gold",
          "valor": 3
        },
        "86-100": {
          "tipo": "gold",
          "valor": 6
        }
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto"
    },
    {
      "type": "elemental_gelo",
      "name": "Elemental de Gelo",
      "emoji": "❄️",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 36,
      "ac": 14,
      "natural_armor": 4,
      "movement": 5,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_gelo",
      "str_": 16,
      "dex": 10,
      "con_": 18,
      "int_": 2,
      "fort": 4,
      "ref_": 0,
      "will": -4,
      "attacks": [
        {
          "name": "Garra Congelante",
          "atk_bonus": 5,
          "damage": "1d10",
          "damage_types": [
            "cold"
          ],
          "num_attacks": 1,
          "attack_attribute": "str_",
          "apply_attribute_damage": true,
          "attribute_mod_base": 3,
          "base_attack_bonus": 2,
          "on_hit": null,
          "on_hit_effect": "congelamento_progressivo"
        }
      ],
      "special_abilities": [
        {
          "id": "congelamento_progressivo",
          "name": "Congelamento Progressivo",
          "action_type": "passiva",
          "descricao": "Ao acertar, reduz o movimento em 1 por 2 turnos; acumula até –3 e renova a duração."
        },
        {
          "id": "nucleo_frio",
          "name": "Núcleo Frio",
          "action_type": "passiva",
          "descricao": "Reduz em 2 todo dano recebido, exceto fogo."
        }
      ],
      "immunities": [
        "cold"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 1.5,
          "descricao": "Fogo causa 1,5× de dano."
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 1
        },
        {
          "type": "all_except",
          "exclude": [
            "fire"
          ],
          "reduction": 2
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "2d6"
        }
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto"
    },
    {
      "type": "elemental_pedra",
      "name": "Elemental de Pedra",
      "emoji": "🪨",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 44,
      "ac": 16,
      "natural_armor": 7,
      "movement": 4,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_pedra",
      "str_": 18,
      "dex": 8,
      "con_": 20,
      "int_": 1,
      "fort": 5,
      "ref_": -1,
      "will": -5,
      "attacks": [
        {
          "name": "Golpe de Rocha",
          "atk_bonus": 6,
          "damage": "1d12",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "attack_attribute": "str_",
          "apply_attribute_damage": true,
          "attribute_mod_base": 4,
          "base_attack_bonus": 2,
          "on_hit": null
        }
      ],
      "special_abilities": [
        {
          "id": "impacto_devastador",
          "name": "Impacto Devastador",
          "action_type": "passiva",
          "descricao": "Se não se mover no turno, causa +4 de dano."
        },
        {
          "id": "inabalavel",
          "name": "Inabalável",
          "action_type": "passiva",
          "descricao": "Não pode ser imobilizado por redes, cola ou efeitos equivalentes."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2,
          "ignora_reducao": true,
          "descricao": "Dano contundente ignora reduções e causa +2 de dano."
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 4
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "2d6"
        }
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto"
    },
    {
      "type": "elemental_eletrico",
      "name": "Elemental Elétrico",
      "emoji": "⚡",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 24,
      "ac": 14,
      "natural_armor": 0,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_eletrico",
      "str_": 10,
      "dex": 18,
      "con_": 12,
      "int_": 3,
      "fort": 1,
      "ref_": 4,
      "will": -4,
      "attacks": [
        {
          "name": "Raio",
          "atk_bonus": 6,
          "damage": "1d10",
          "damage_types": [
            "lightning"
          ],
          "num_attacks": 1,
          "range": 3,
          "attack_attribute": "dex",
          "apply_attribute_damage": true,
          "attribute_mod_base": 4,
          "base_attack_bonus": 2,
          "on_hit": null
        }
      ],
      "special_abilities": [
        {
          "id": "corpo_energetico",
          "name": "Corpo Energético",
          "action_type": "passiva",
          "damage": "1d4",
          "damage_types": [
            "lightning"
          ],
          "descricao": "Pode atravessar um quadrado ocupado, causa 1d4 de eletricidade ao ocupante e termina em uma casa livre."
        },
        {
          "id": "sobrecarga",
          "name": "Sobrecarga",
          "action_type": "passiva",
          "descricao": "Ao acertar o mesmo alvo na rodada seguinte, causa +1d4 de eletricidade."
        },
        {
          "id": "salto_eletrico",
          "name": "Condução Elétrica",
          "action_type": "passiva",
          "descricao": "Ignora a CA concedida por armaduras de metal."
        }
      ],
      "immunities": [
        "lightning"
      ],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 4,
          "descricao": "Pedra (dano contundente) causa +4 de dano."
        },
        {
          "type": "cold",
          "bonus_flat": 2,
          "descricao": "Água (tratada como frio) causa +2 de dano."
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "2d6"
        }
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto"
    },
    {
      "type": "elemental_ar",
      "name": "Elemental de Ar",
      "emoji": "🌪️",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 22,
      "ac": 15,
      "natural_armor": 0,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_ar",
      "str_": 10,
      "dex": 20,
      "con_": 12,
      "int_": 3,
      "fort": 1,
      "ref_": 5,
      "will": -4,
      "attacks": [
        {
          "name": "Rajada de Vento",
          "atk_bonus": 6,
          "damage": "1d8",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "range": 2,
          "attack_attribute": "dex",
          "apply_attribute_damage": true,
          "attribute_mod_base": 5,
          "base_attack_bonus": 1,
          "on_hit": null,
          "on_hit_effect": "golpe_vento"
        }
      ],
      "special_abilities": [
        {
          "id": "corpo_intangivel",
          "name": "Corpo Intangível",
          "action_type": "passiva",
          "descricao": "Não sofre dano de armas físicas."
        },
        {
          "id": "golpe_vento",
          "name": "Golpe de Vento",
          "action_type": "passiva",
          "descricao": "Ao acertar, empurra o alvo em 1 quadrado."
        },
        {
          "id": "velocidade_vento",
          "name": "Velocidade do Vento",
          "action_type": "passiva",
          "descricao": "Atravessa quadrados ocupados, mas deve terminar o movimento em uma casa livre."
        },
        {
          "id": "turbilhao",
          "name": "Turbilhão",
          "action_type": "acao",
          "cooldown_turns": 2,
          "damage": "1d8",
          "radius": 1,
          "dc": 13,
          "save": "reflexos",
          "descricao": "Área de 1 quadrado: 1d8; Reflexos CD 13. Falha perde a próxima ação; sucesso perde o movimento."
        }
      ],
      "immunities": [
        "physical",
        "paralisia",
        "agarramento",
        "poison"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 2,
          "descricao": "Fogo causa dano dobrado."
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "2d6"
        }
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto"
    },
    {
      "type": "elemental_agua",
      "name": "Elemental de Água",
      "emoji": "🌊",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 32,
      "ac": 14,
      "natural_armor": 3,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_agua",
      "str_": 14,
      "dex": 12,
      "con_": 16,
      "int_": 2,
      "fort": 3,
      "ref_": 1,
      "will": -4,
      "attacks": [
        {
          "name": "Golpe de Água",
          "atk_bonus": 5,
          "damage": "1d10",
          "damage_types": [
            "water"
          ],
          "num_attacks": 1,
          "attack_attribute": "str_",
          "apply_attribute_damage": true,
          "attribute_mod_base": 2,
          "base_attack_bonus": 3,
          "on_hit": null
        }
      ],
      "special_abilities": [
        {
          "id": "corpo_fluido",
          "name": "Corpo Fluido",
          "action_type": "passiva",
          "descricao": "Sofre metade do dano de armas físicas."
        },
        {
          "id": "onda_envolvente",
          "name": "Onda Envolvente / Afogar",
          "action_type": "passiva",
          "damage": "1d6",
          "dc": 12,
          "escape_saves": [
            "fortitude"
          ],
          "descricao": "Ao acertar, prende uma criatura média; presa sofre 1d6 de água por rodada e testa FOR CD 12 para escapar. Sobre Água/Água Profunda, sofre +1d6 por rodada."
        },
        {
          "id": "mare_viva",
          "name": "Maré Viva",
          "action_type": "passiva",
          "descricao": "No início do turno, recupera 1d6 HP se estiver sobre ou adjacente a Água/Água Profunda."
        },
        {
          "id": "solidificar_frio",
          "name": "Solidificar",
          "action_type": "passiva",
          "descricao": "Frio em 2 rodadas consecutivas remove a resistência física por 2 rodadas."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "lightning",
          "multiplier": 2,
          "descricao": "Eletricidade causa dano dobrado."
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "mode": "half"
        },
        {
          "type": "fire",
          "mode": "half"
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "2d6"
        }
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto"
    },
    {
      "type": "lobisomem",
      "name": "Lobisomem",
      "emoji": "🐺",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 24,
      "ac": 17,
      "natural_armor": 4,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "lobisomem",
      "str_": 18,
      "dex": 16,
      "con_": 16,
      "int_": 10,
      "fort": 6,
      "ref_": 5,
      "will": 3,
      "attacks": [
        {
          "name": "Garras",
          "atk_bonus": 6,
          "damage": "1d4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "attack_attribute": "str_",
          "apply_attribute_damage": true,
          "attribute_mod_base": 4,
          "base_attack_bonus": 2,
          "on_hit": null
        },
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "attack_attribute": "str_",
          "apply_attribute_damage": true,
          "attribute_mod_base": 4,
          "base_attack_bonus": 0,
          "on_hit": null
        }
      ],
      "special_abilities": [
        {
          "id": "olfato_agucado",
          "name": "Olfato Aguçado",
          "action_type": "passiva",
          "descricao": "Detecta invisíveis e impede ocultação."
        },
        {
          "id": "pele_amaldicoada",
          "name": "Pele Amaldiçoada",
          "action_type": "passiva",
          "descricao": "Armas não mágicas e sem prata causam metade do dano."
        },
        {
          "id": "regeneracao_lobisomem",
          "name": "Regeneração",
          "action_type": "passiva",
          "descricao": "Recupera 2 HP no início do turno, exceto após dano mágico ou de prata."
        },
        {
          "id": "furia_bestial_lobisomem",
          "name": "Fúria Bestial",
          "action_type": "passiva",
          "descricao": "Com 12 HP ou menos: +2 ataque e dano."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "silver",
          "multiplier": 2,
          "descricao": "Prata causa dano dobrado e bloqueia regeneração."
        }
      ],
      "resistances": [],
      "loot_table": {},
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "escravo_vampirico",
      "name": "Escravo Vampírico",
      "emoji": "🧛",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 18,
      "ac": 15,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "cria_vampirica",
      "str_": 14,
      "dex": 14,
      "con_": 10,
      "int_": 6,
      "fort": 2,
      "ref_": 4,
      "will": 4,
      "attacks": [
        {
          "name": "Espada Curta",
          "atk_bonus": 4,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 3,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "reducao_vampirica",
          "name": "Redução de Dano 5",
          "action_type": "passiva",
          "descricao": "Armas comuns sofrem –5; prata, magia e magias ignoram."
        },
        {
          "id": "cura_acelerada_vampirica",
          "name": "Cura Acelerada",
          "action_type": "passiva",
          "descricao": "Recupera 5 HP; sagrado/luz e fogo bloqueiam."
        },
        {
          "id": "drenar_vida",
          "name": "Drenar Vida",
          "action_type": "passiva",
          "descricao": "A mordida cura o dano causado."
        },
        {
          "id": "ressurreicao_vampirica",
          "name": "Ressurreição Vampírica",
          "action_type": "passiva",
          "descricao": "Retorna uma vez após 1d4 rodadas, salvo dano sagrado/luz suficiente."
        }
      ],
      "immunities": [
        "poison",
        "sono"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 1.5
        },
        {
          "type": "holy",
          "multiplier": 2
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 5
        }
      ],
      "ai_type": "agressivo",
      "undead": true,
      "subtipo": "morto_vivo"
    },
    {
      "type": "vampiro_jovem",
      "name": "Vampiro Jovem",
      "emoji": "🧛",
      "boss": false,
      "tier": 5,
      "cr": 5,
      "hp": 28,
      "ac": 17,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "vampiro",
      "str_": 16,
      "dex": 18,
      "con_": 10,
      "int_": 12,
      "fort": 4,
      "ref_": 6,
      "will": 5,
      "attacks": [
        {
          "name": "Espada Longa",
          "atk_bonus": 6,
          "damage": "1d8+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 5,
          "damage": "1d6+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "reducao_vampirica",
          "name": "Redução de Dano 5",
          "action_type": "passiva"
        },
        {
          "id": "cura_acelerada_vampirica",
          "name": "Cura Acelerada",
          "action_type": "passiva"
        },
        {
          "id": "drenar_vida",
          "name": "Drenar Vida",
          "action_type": "passiva"
        },
        {
          "id": "encantar_vampirico",
          "name": "Encantar",
          "action_type": "acao",
          "dc": 12,
          "cooldown_turns": 3
        },
        {
          "id": "ressurreicao_vampirica",
          "name": "Ressurreição Vampírica",
          "action_type": "passiva"
        }
      ],
      "immunities": [
        "poison",
        "sono"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 1.5
        },
        {
          "type": "holy",
          "multiplier": 2
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 5
        }
      ],
      "ai_type": "agressivo",
      "undead": true,
      "subtipo": "morto_vivo"
    },
    {
      "type": "vampiro_anciao",
      "name": "Vampiro Ancião",
      "emoji": "🧛",
      "boss": false,
      "tier": 7,
      "cr": 7,
      "hp": 42,
      "ac": 19,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "mestre_vampiro",
      "str_": 18,
      "dex": 20,
      "con_": 10,
      "int_": 16,
      "fort": 6,
      "ref_": 8,
      "will": 8,
      "attacks": [
        {
          "name": "Espada Bastarda",
          "atk_bonus": 9,
          "damage": "1d10+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 8,
          "damage": "1d8+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "reducao_vampirica",
          "name": "Redução de Dano 5",
          "action_type": "passiva"
        },
        {
          "id": "cura_acelerada_vampirica",
          "name": "Cura Acelerada",
          "action_type": "passiva"
        },
        {
          "id": "drenar_vida",
          "name": "Drenar Vida",
          "action_type": "passiva"
        },
        {
          "id": "encantar_area_vampirico",
          "name": "Encantar em Área",
          "action_type": "acao",
          "dc": 13,
          "range": 4,
          "cooldown_turns": 2
        },
        {
          "id": "comandar_escravos",
          "name": "Comandar Escravos",
          "action_type": "passiva"
        },
        {
          "id": "ressurreicao_vampirica",
          "name": "Ressurreição Vampírica",
          "action_type": "passiva"
        }
      ],
      "immunities": [
        "poison",
        "sono"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 1.5
        },
        {
          "type": "holy",
          "multiplier": 2
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 5
        }
      ],
      "ai_type": "agressivo",
      "undead": true,
      "subtipo": "morto_vivo"
    },
    {
      "type": "lorde_vampiro",
      "name": "Lorde Vampiro",
      "emoji": "👑🧛",
      "boss": true,
      "tier": 9,
      "cr": 9,
      "hp": 60,
      "ac": 21,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "lorde_vampiro",
      "str_": 20,
      "dex": 22,
      "con_": 10,
      "int_": 18,
      "fort": 8,
      "ref_": 10,
      "will": 10,
      "attacks": [
        {
          "name": "Espada Longa Mágica",
          "atk_bonus": 12,
          "damage": "1d8+7",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 11,
          "damage": "1d8+7",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "reducao_vampirica",
          "name": "Redução de Dano 5",
          "action_type": "passiva"
        },
        {
          "id": "cura_acelerada_vampirica",
          "name": "Cura Acelerada",
          "action_type": "passiva"
        },
        {
          "id": "drenar_vida",
          "name": "Drenar Vida",
          "action_type": "passiva"
        },
        {
          "id": "encantar_supremo_vampirico",
          "name": "Encantar Supremo em Área",
          "action_type": "acao",
          "dc": 14,
          "range": 6,
          "cooldown_turns": 2
        },
        {
          "id": "comandar_vampiros",
          "name": "Comandar Vampiros",
          "action_type": "passiva"
        },
        {
          "id": "ressurreicao_vampirica",
          "name": "Ressurreição Vampírica",
          "action_type": "passiva"
        }
      ],
      "immunities": [
        "poison",
        "sono"
      ],
      "weaknesses": [
        {
          "type": "fire",
          "multiplier": 1.5
        },
        {
          "type": "holy",
          "multiplier": 2
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 5
        }
      ],
      "ai_type": "agressivo",
      "undead": true,
      "subtipo": "morto_vivo"
    }
  ],
  "monster_abilities": [
    {
      "id": "amaldicoar_monstro",
      "source": "monstro",
      "name": "Amaldiçoar",
      "icon": "☠️",
      "action_type": "acao",
      "range": 4,
      "save": "vontade",
      "dc": 13,
      "curse_mode": "aleatoria",
      "curse_category": "leve",
      "descricao": "Amaldiçoa um alvo: configure a maldição específica ou uma aleatória por gravidade."
    },
    {
      "id": "disparo_teia",
      "name": "Disparo de Teia",
      "action_type": "acao",
      "uses_per_combat": 1,
      "range": 4,
      "target": "single",
      "dc": 11,
      "save": "reflexos",
      "damage": null,
      "damage_types": [],
      "effect": "perde_turno",
      "effect_duration": 1,
      "source": "monstro"
    },
    {
      "id": "envenenar",
      "name": "Envenenar",
      "action_type": "passiva",
      "attack_index": 1,
      "veneno_id": "veneno_escorpiao_pedra",
      "poison_dc": 9,
      "descricao": "Vincula um veneno escolhido a um dos ataques da criatura.",
      "source": "monstro"
    },
    {
      "id": "sem_dor",
      "name": "Sem Dor",
      "action_type": "passiva",
      "source": "monstro"
    },
    {
      "id": "corpo_inerte",
      "name": "Corpo Inerte",
      "action_type": "passiva",
      "source": "monstro"
    },
    {
      "id": "fraqueza_magica",
      "name": "Fraqueza Mágica",
      "action_type": "passiva",
      "descricao": "-2 em testes contra magias que controlam mortos-vivos",
      "source": "monstro"
    },
    {
      "id": "movimento_erratico",
      "name": "Movimento Errático",
      "action_type": "passiva",
      "descricao": "Ignora penalidades de movimento de Água e Água Profunda",
      "source": "monstro"
    },
    {
      "id": "sem_instinto",
      "name": "Sem Instinto",
      "action_type": "passiva",
      "descricao": "Nunca foge nem recua — avança até ser destruído",
      "source": "monstro"
    },
    {
      "id": "caca_em_bando",
      "name": "Caça em Bando",
      "action_type": "passiva",
      "source": "monstro"
    },
    {
      "id": "derrubar",
      "name": "Derrubar",
      "action_type": "passiva",
      "dc": 11,
      "save": "reflexos",
      "source": "monstro"
    },
    {
      "id": "constricao",
      "name": "Constrição",
      "action_type": "passiva",
      "dc": 11,
      "save": "fortitude",
      "escape_saves": [
        "fortitude"
      ],
      "descricao": "Ao acertar, alvo testa FOR CD 11 — falha: preso",
      "source": "monstro"
    },
    {
      "id": "esmagar",
      "name": "Esmagar",
      "action_type": "passiva",
      "descricao": "Enquanto preso e adjacente: 1d6 dano automático por turno",
      "source": "monstro"
    },
    {
      "id": "veneno",
      "name": "Veneno",
      "action_type": "passiva",
      "descricao": "Ao acertar a mordida, aplica veneno (doença leve)",
      "source": "monstro"
    },
    {
      "id": "ataque_rapido",
      "name": "Ataque Rápido",
      "action_type": "passiva",
      "descricao": "Se não se mover no turno: +1 no ataque",
      "source": "monstro"
    },
    {
      "id": "camuflagem_natural",
      "name": "Camuflagem Natural",
      "action_type": "passiva",
      "descricao": "+2 CA contra o primeiro ataque em terreno natural",
      "source": "monstro"
    },
    {
      "id": "toque_putrefato",
      "name": "Toque Putrefato",
      "action_type": "passiva",
      "descricao": "Ao acertar: +1 nível de dano em equipamento orgânico do alvo (couro/madeira/tecido)",
      "source": "monstro"
    },
    {
      "id": "corrosao_viva",
      "name": "Corrosão Viva",
      "action_type": "passiva",
      "descricao": "Alvo sem armadura: 1 dano/turno por 2 turnos (acumula a cada acerto)",
      "source": "monstro"
    },
    {
      "id": "absorver_materia",
      "name": "Absorver Matéria",
      "action_type": "passiva",
      "descricao": "Quando destrói um item orgânico: recupera 1d4 HP",
      "source": "monstro"
    },
    {
      "id": "furia",
      "name": "Fúria",
      "action_type": "passiva",
      "descricao": "Com HP < 50%: +2 de dano em todos os ataques",
      "source": "monstro"
    },
    {
      "id": "investida_brutal",
      "name": "Investida Brutal",
      "action_type": "passiva",
      "descricao": "Se mover antes de atacar: +2 de dano",
      "source": "monstro"
    },
    {
      "id": "furia_cega",
      "name": "Fúria Cega",
      "action_type": "passiva",
      "descricao": "Se sofreu dano na rodada anterior: +1 de dano, mas -1 CA",
      "source": "monstro"
    },
    {
      "id": "mente_limitada",
      "name": "Mente Limitada",
      "action_type": "passiva",
      "descricao": "-1 em testes de Vontade contra efeitos mentais",
      "source": "monstro"
    },
    {
      "id": "mente_fraca",
      "name": "Mente Fraca",
      "action_type": "passiva",
      "descricao": "-2 em testes de Vontade contra magias de controle mental",
      "source": "monstro"
    },
    {
      "id": "arremesso",
      "name": "Arremesso",
      "action_type": "acao_bonus",
      "descricao": "Arremesso 1d4+2 (alcance 3) como ação bônus; 1 natural quebra a arma",
      "source": "monstro"
    },
    {
      "id": "silencio",
      "name": "Silêncio",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 2,
      "descricao": "Cria área de Silêncio (some se o xamã morrer)",
      "source": "monstro"
    },
    {
      "id": "amaldicoar",
      "name": "Amaldiçoar",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "descricao": "Debuff -1 em ataque/dano/CA/resistência nos heróis",
      "source": "monstro"
    },
    {
      "id": "abencoar",
      "name": "Abençoar",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "descricao": "Buff +1 em ataque/dano/CA/resistência nos goblins aliados",
      "source": "monstro"
    },
    {
      "id": "concentracao_fragil",
      "name": "Concentração Frágil",
      "action_type": "passiva",
      "descricao": "Se sofrer dano, não pode usar magia no próximo turno",
      "source": "monstro"
    },
    {
      "id": "envenenar_arma",
      "name": "Envenenar Arma",
      "action_type": "passiva",
      "descricao": "Usa um veneno da bolsa para envenenar a arma como ação livre",
      "source": "monstro"
    },
    {
      "id": "covardia_kobold",
      "name": "Covardia Instintiva",
      "action_type": "passiva",
      "dc": 10,
      "save": "vontade",
      "effect": "medo_kobold",
      "effect_duration": 2,
      "source": "monstro"
    },
    {
      "id": "bola_fogo",
      "name": "Bola de Fogo",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "source": "monstro"
    },
    {
      "id": "medo",
      "name": "Medo",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "source": "monstro"
    },
    {
      "id": "dominar_morto_vivo",
      "name": "Dominar Morto-Vivo",
      "action_type": "acao",
      "range": 4,
      "circulo": 3,
      "source": "monstro"
    },
    {
      "id": "mestre_dos_mortos",
      "name": "Mestre dos Mortos",
      "action_type": "acao",
      "uses_per_combat": 1,
      "descricao": "Na primeira ação, conjura 2 esqueletos humanos ou animais à escolha do Mestre",
      "source": "monstro"
    },
    {
      "id": "concentracao_sombria",
      "name": "Concentração Sombria",
      "action_type": "passiva",
      "descricao": "Ao sofrer dano: Vontade CD 10 ou perde a ação de magia no turno",
      "source": "monstro"
    },
    {
      "id": "essencia_profana",
      "name": "Essência Profana",
      "action_type": "passiva",
      "descricao": "Sofre dano dobrado de efeitos sagrados/luz",
      "source": "monstro"
    },
    {
      "id": "resistencia_morta",
      "name": "Resistência Morta",
      "action_type": "passiva",
      "dc": 10,
      "save": "fortitude",
      "descricao": "A 0 HP: Fortitude CD 10 + metade do dano excedente (arredonda para cima) → fica com 1 HP (dano sagrado/luz ignora e destrói de vez)",
      "source": "monstro"
    },
    {
      "id": "infeccao",
      "name": "Infecção",
      "action_type": "passiva",
      "dc": 10,
      "save": "fortitude",
      "disease_severity": "leve",
      "descricao": "Ao acertar: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve",
      "source": "monstro"
    },
    {
      "id": "lento_incansavel",
      "name": "Lento e Incansável",
      "action_type": "passiva",
      "descricao": "Não corre nem foge — avança sem parar",
      "source": "monstro"
    },
    {
      "id": "corpo_morto",
      "name": "Corpo Morto",
      "action_type": "passiva",
      "descricao": "Não come, bebe nem respira",
      "source": "monstro"
    },
    {
      "id": "mordida_corrosiva",
      "name": "Mordida Corrosiva",
      "action_type": "passiva",
      "descricao": "Ao acertar: +1 nível de dano na arma OU armadura metálica do alvo",
      "source": "monstro"
    },
    {
      "id": "devorar_metal",
      "name": "Devorar Metal",
      "action_type": "passiva",
      "descricao": "Item a 3 níveis é destruído e o Devorador recupera 1d6 HP",
      "source": "monstro"
    },
    {
      "id": "alimentacao_metalica",
      "name": "Alimentação Metálica",
      "action_type": "passiva",
      "descricao": "Gasta a ação para consumir item metálico no chão e recuperar 1d6 HP",
      "source": "monstro"
    },
    {
      "id": "manto_escuridao",
      "name": "Manto de Escuridão",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "descricao": "Cria uma área de escuridão centrada em si (1x por combate)",
      "source": "monstro"
    },
    {
      "id": "ataque_das_sombras",
      "name": "Ataque das Sombras",
      "action_type": "passiva",
      "descricao": "Se o alvo não o enxerga (bugbear oculto OU alvo na escuridão sem visão no escuro): +2 ataque e +1d6 de dano em TODOS os ataques",
      "source": "monstro"
    },
    {
      "id": "cacador_das_trevas",
      "name": "Caçador das Trevas",
      "action_type": "passiva",
      "descricao": "Em área escura: +2 CA, +1 ataque e sempre pode usar Ataque das Sombras",
      "source": "monstro"
    },
    {
      "id": "desaparecer_nas_sombras",
      "name": "Desaparecer nas Sombras",
      "action_type": "acao_livre",
      "cooldown_turns": 5,
      "descricao": "Só na escuridão (após Manto): fica oculto (imune a ataques à distância; corpo a corpo -4), move até 3, até o início do próximo turno",
      "source": "monstro"
    },
    {
      "id": "visao_perfeita_escuro",
      "name": "Visão no Escuro",
      "action_type": "passiva",
      "descricao": "Enxerga perfeitamente no escuro — não sofre penalidades nas trevas",
      "source": "monstro"
    },
    {
      "id": "golpe_brutal",
      "name": "Golpe Brutal",
      "action_type": "ataque",
      "cooldown_turns": 3,
      "descricao": "+2 de dano ao ataque (recarga 3 rodadas); usado para finalizar",
      "source": "monstro"
    },
    {
      "id": "forca_descomunal",
      "name": "Força Descomunal",
      "action_type": "ataque",
      "cooldown_turns": 4,
      "save": "fortitude",
      "dc": 10,
      "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a próxima rodada). Recarga 4 rodadas",
      "source": "monstro"
    },
    {
      "id": "mente_bruta",
      "name": "Mente Bruta",
      "action_type": "passiva",
      "descricao": "-2 em Vontade contra controle mental",
      "source": "monstro"
    },
    {
      "id": "lento_previsivel",
      "name": "Lento e Previsível",
      "action_type": "passiva",
      "descricao": "Se errar um ataque: -2 de CA até o próximo turno",
      "source": "monstro"
    },
    {
      "id": "corpo_energetico",
      "name": "Corpo Energético",
      "action_type": "passiva",
      "damage": "1d4",
      "damage_types": [
        "fire"
      ],
      "descricao": "Pode atravessar um quadrado ocupado, causa 1d4 de fogo ao ocupante e termina em uma casa livre.",
      "source": "monstro"
    },
    {
      "id": "corpo_em_chamas",
      "name": "Corpo em Chamas",
      "action_type": "passiva",
      "damage": "1d6",
      "damage_types": [
        "fire"
      ],
      "descricao": "Quem o acerta com um ataque corpo a corpo sofre 1d6 de dano de fogo.",
      "source": "monstro"
    },
    {
      "id": "explosao_final",
      "name": "Explosão Final",
      "action_type": "passiva",
      "damage": "6d6",
      "damage_types": [
        "fire"
      ],
      "radius": 1,
      "save": "reflexos",
      "dc": 13,
      "descricao": "Ao morrer, explode em 1 quadrado: 6d6 de fogo; Reflexos CD 13 reduz à metade.",
      "source": "monstro"
    },
    {
      "id": "intensidade",
      "name": "Intensidade",
      "action_type": "passiva",
      "descricao": "As chamas ignoram reduções leves de dano de fogo (não ignora resistência à metade).",
      "source": "monstro"
    },
    {
      "id": "congelamento_progressivo",
      "name": "Congelamento Progressivo",
      "action_type": "passiva",
      "descricao": "Ao acertar, reduz o movimento em 1 por 2 turnos; acumula até –3 e renova a duração.",
      "source": "monstro"
    },
    {
      "id": "nucleo_frio",
      "name": "Núcleo Frio",
      "action_type": "passiva",
      "descricao": "Reduz em 2 todo dano recebido, exceto fogo.",
      "source": "monstro"
    },
    {
      "id": "impacto_devastador",
      "name": "Impacto Devastador",
      "action_type": "passiva",
      "descricao": "Se não se mover no turno, causa +4 de dano.",
      "source": "monstro"
    },
    {
      "id": "inabalavel",
      "name": "Inabalável",
      "action_type": "passiva",
      "descricao": "Não pode ser imobilizado por redes, cola ou efeitos equivalentes.",
      "source": "monstro"
    },
    {
      "id": "sobrecarga",
      "name": "Sobrecarga",
      "action_type": "passiva",
      "descricao": "Ao acertar o mesmo alvo na rodada seguinte, causa +1d4 de eletricidade.",
      "source": "monstro"
    },
    {
      "id": "salto_eletrico",
      "name": "Condução Elétrica",
      "action_type": "passiva",
      "descricao": "Ignora a CA concedida por armaduras de metal.",
      "source": "monstro"
    },
    {
      "id": "corpo_intangivel",
      "name": "Corpo Intangível",
      "action_type": "passiva",
      "descricao": "Não sofre dano de armas físicas.",
      "source": "monstro"
    },
    {
      "id": "golpe_vento",
      "name": "Golpe de Vento",
      "action_type": "passiva",
      "descricao": "Ao acertar, empurra o alvo em 1 quadrado.",
      "source": "monstro"
    },
    {
      "id": "velocidade_vento",
      "name": "Velocidade do Vento",
      "action_type": "passiva",
      "descricao": "Atravessa quadrados ocupados, mas deve terminar o movimento em uma casa livre.",
      "source": "monstro"
    },
    {
      "id": "turbilhao",
      "name": "Turbilhão",
      "action_type": "acao",
      "cooldown_turns": 2,
      "damage": "1d8",
      "radius": 1,
      "dc": 13,
      "save": "reflexos",
      "descricao": "Área de 1 quadrado: 1d8; Reflexos CD 13. Falha perde a próxima ação; sucesso perde o movimento.",
      "source": "monstro"
    },
    {
      "id": "corpo_fluido",
      "name": "Corpo Fluido",
      "action_type": "passiva",
      "descricao": "Sofre metade do dano de armas físicas.",
      "source": "monstro"
    },
    {
      "id": "onda_envolvente",
      "name": "Onda Envolvente / Afogar",
      "action_type": "passiva",
      "damage": "1d6",
      "dc": 12,
      "escape_saves": [
        "fortitude"
      ],
      "descricao": "Ao acertar, prende uma criatura média; presa sofre 1d6 de água por rodada e testa FOR CD 12 para escapar. Sobre Água/Água Profunda, sofre +1d6 por rodada.",
      "source": "monstro"
    },
    {
      "id": "mare_viva",
      "name": "Maré Viva",
      "action_type": "passiva",
      "descricao": "No início do turno, recupera 1d6 HP se estiver sobre ou adjacente a Água/Água Profunda.",
      "source": "monstro"
    },
    {
      "id": "solidificar_frio",
      "name": "Solidificar",
      "action_type": "passiva",
      "descricao": "Frio em 2 rodadas consecutivas remove a resistência física por 2 rodadas.",
      "source": "monstro"
    },
    {
      "id": "olfato_agucado",
      "name": "Olfato Aguçado",
      "action_type": "passiva",
      "descricao": "Detecta invisíveis e impede ocultação.",
      "source": "monstro"
    },
    {
      "id": "pele_amaldicoada",
      "name": "Pele Amaldiçoada",
      "action_type": "passiva",
      "descricao": "Armas não mágicas e sem prata causam metade do dano.",
      "source": "monstro"
    },
    {
      "id": "regeneracao_lobisomem",
      "name": "Regeneração",
      "action_type": "passiva",
      "descricao": "Recupera 2 HP no início do turno, exceto após dano mágico ou de prata.",
      "source": "monstro"
    },
    {
      "id": "furia_bestial_lobisomem",
      "name": "Fúria Bestial",
      "action_type": "passiva",
      "descricao": "Com 12 HP ou menos: +2 ataque e dano.",
      "source": "monstro"
    },
    {
      "id": "reducao_vampirica",
      "name": "Redução de Dano 5",
      "action_type": "passiva",
      "descricao": "Armas comuns sofrem –5; prata, magia e magias ignoram.",
      "source": "monstro"
    },
    {
      "id": "cura_acelerada_vampirica",
      "name": "Cura Acelerada",
      "action_type": "passiva",
      "descricao": "Recupera 5 HP; sagrado/luz e fogo bloqueiam.",
      "source": "monstro"
    },
    {
      "id": "drenar_vida",
      "name": "Drenar Vida",
      "action_type": "passiva",
      "descricao": "A mordida cura o dano causado.",
      "source": "monstro"
    },
    {
      "id": "ressurreicao_vampirica",
      "name": "Ressurreição Vampírica",
      "action_type": "passiva",
      "descricao": "Retorna uma vez após 1d4 rodadas, salvo dano sagrado/luz suficiente.",
      "source": "monstro"
    },
    {
      "id": "encantar_vampirico",
      "name": "Encantar",
      "action_type": "acao",
      "dc": 12,
      "cooldown_turns": 3,
      "source": "monstro"
    },
    {
      "id": "encantar_area_vampirico",
      "name": "Encantar em Área",
      "action_type": "acao",
      "dc": 13,
      "range": 4,
      "cooldown_turns": 2,
      "source": "monstro"
    },
    {
      "id": "comandar_escravos",
      "name": "Comandar Escravos",
      "action_type": "passiva",
      "source": "monstro"
    },
    {
      "id": "encantar_supremo_vampirico",
      "name": "Encantar Supremo em Área",
      "action_type": "acao",
      "dc": 14,
      "range": 6,
      "cooldown_turns": 2,
      "source": "monstro"
    },
    {
      "id": "comandar_vampiros",
      "name": "Comandar Vampiros",
      "action_type": "passiva",
      "source": "monstro"
    },
    {
      "id": "hero_warrior_mira_certeira",
      "source": "heroi",
      "source_id": "mira_certeira",
      "source_class": "warrior",
      "name": "Mira Certeira",
      "icon": "⚔️",
      "descricao": "+2 no dado de acerto neste turno",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "uses_per_day": 3,
      "cooldown_turns": 4
    },
    {
      "id": "guild_brutalidade",
      "source": "guilda",
      "source_id": "brutalidade",
      "name": "Brutalidade",
      "icon": "✦",
      "descricao": "Até o fim do turno, ataques físicos com arma causam +2 de dano.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "predador_oportunista",
      "name": "Predador Oportunista",
      "action_type": "passiva",
      "descricao": "+1 nas mordidas contra alvos com menos de 50% do HP",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "carapaca_resistente",
      "name": "Carapaça Resistente",
      "action_type": "passiva",
      "descricao": "Reduz todo dano físico em 2",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "cauda_varredora",
      "name": "Cauda Varredora",
      "action_type": "acao",
      "cooldown_turns": 2,
      "atk_bonus": 5,
      "damage": "1d8+3",
      "save": "reflexos",
      "dc": 12,
      "descricao": "Atinge todos atrás: +5, 1d8+3; falha derruba",
      "source": "monstro",
      "uses_per_day": 1
    },
    {
      "id": "cuspir_acido",
      "name": "Cuspir Ácido",
      "action_type": "acao",
      "cooldown_turns": 3,
      "range": 3,
      "damage": "2d6",
      "save": "reflexos",
      "dc": 13,
      "descricao": "Alvo a até 3 quadrado(s): 2d6 de ácido; Reflexos CD 13 reduz à metade. Falha corrói equipamentos conforme as regras de corrosão por ácido.",
      "source": "monstro",
      "uses_per_day": 1
    },
    {
      "id": "furia_bestial",
      "name": "Fúria Bestial",
      "action_type": "passiva",
      "descricao": "Mordida e ao menos uma garra acertam: +1d6 dano",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "agarrar",
      "name": "Agarrar",
      "action_type": "passiva",
      "dc": 12,
      "save": "fortitude",
      "descricao": "Ao acertar, alvo testa FOR ou REF CD 12 — falha: preso",
      "source": "monstro"
    },
    {
      "id": "atq_mandibula",
      "name": "Ataque de Mandíbula",
      "action_type": "passiva",
      "descricao": "Se alvo preso e adjacente: 1d8+3 dano direto (sem rolagem de acerto)",
      "source": "monstro"
    },
    {
      "id": "arrastar",
      "name": "Arrastar",
      "action_type": "passiva",
      "descricao": "Move alvo preso junto ao se deslocar",
      "source": "monstro"
    },
    {
      "id": "combo_devorador",
      "name": "Combo Devorador",
      "action_type": "passiva",
      "descricao": "Se as 2 mordidas acertarem no turno: 2 ataques de Garra imediatos",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "faro_carnica",
      "name": "Faro da Presa Fácil",
      "action_type": "passiva",
      "descricao": "Prioriza sempre o alvo com menor HP",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "duas_cabecas",
      "name": "Duas Cabeças",
      "action_type": "passiva",
      "descricao": "+2 no raio de visão; ataques furtivos contra a criatura sofrem -2 no acerto.",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "hero_warrior_golpe_devastador",
      "source": "heroi",
      "source_id": "golpe_devastador",
      "source_class": "warrior",
      "name": "Golpe Devastador",
      "icon": "💥",
      "descricao": "Dobra cada dado de dano neste turno",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_warrior_furia_berserker",
      "source": "heroi",
      "source_id": "furia_berserker",
      "source_class": "warrior",
      "name": "Fúria Berserker",
      "icon": "🔥",
      "descricao": "Ataque extra neste turno com habilidades ativas",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_mage_aprimorar_magia",
      "source": "heroi",
      "source_id": "aprimorar_magia",
      "source_class": "mage",
      "name": "Aprimorar Magia",
      "icon": "🎯",
      "descricao": "Ação livre. +1 na dificuldade (CD) do teste de resistência da magia. 🍖-3 ao lançar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_mage_estender_magia",
      "source": "heroi",
      "source_id": "estender_magia",
      "source_class": "mage",
      "name": "Estender Magia",
      "icon": "⏱️",
      "descricao": "Ação livre. +1 turno na duração da magia. 🍖-3 💧-3 ao lançar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_mage_fortalecer_magia",
      "source": "heroi",
      "source_id": "fortalecer_magia",
      "source_class": "mage",
      "name": "Fortalecer Magia",
      "icon": "💥",
      "descricao": "Ação livre. Multiplica o dano da magia por 1,5. 🍖-6 💧-6 ao lançar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_ataque_furtivo",
      "source": "heroi",
      "source_id": "ataque_furtivo",
      "source_class": "rogue",
      "name": "Ataque Furtivo",
      "icon": "🗡️",
      "descricao": "Passiva. +2d4 dano extra quando há aliado adjacente ao alvo (ou se estiver invisível). +1d4 por faixa de nível.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate"
    },
    {
      "id": "hero_rogue_detectar_armadilhas",
      "source": "heroi",
      "source_id": "detectar_armadilhas",
      "source_class": "rogue",
      "name": "Detectar Armadilhas",
      "icon": "🔍",
      "descricao": "Ação bônus (alternável). Revela armadilhas próximas e não dispara as da masmorra. Manutenção 💧-1/turno.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_esconder_sombras",
      "source": "heroi",
      "source_id": "esconder_sombras",
      "source_class": "rogue",
      "name": "Esconder nas Sombras",
      "icon": "🌑",
      "descricao": "Ação bônus. d20+DES vs percepção dos monstros. Invisível (não é alvo) enquanto ativo. Manutenção 🍖-1 💧-1/turno.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_veneno_rapido",
      "source": "heroi",
      "source_id": "veneno_rapido",
      "source_class": "rogue",
      "name": "Veneno Rápido",
      "icon": "☠️",
      "descricao": "Ação livre. Unta um veneno da bolsa na arma — os próximos golpes certeiros envenenam o alvo.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_criar_armadilha",
      "source": "heroi",
      "source_id": "criar_armadilha",
      "source_class": "rogue",
      "name": "Criar Armadilha",
      "icon": "🪤",
      "descricao": "Ação principal. Coloca uma armadilha na própria casa ou adjacente. Custa fome/sede + ouro.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_desarmar_armadilha",
      "source": "heroi",
      "source_id": "desarmar_armadilha",
      "source_class": "rogue",
      "name": "Desarmar Armadilha",
      "icon": "🔧",
      "descricao": "Ação principal. Selecione uma casa adjacente para tentar desarmar a armadilha. Falha crítica a dispara em você.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_cura",
      "source": "heroi",
      "source_id": "cura",
      "source_class": "cleric",
      "name": "Cura",
      "icon": "🙌",
      "descricao": "1d8 a 3d8 + INT em um aliado. 💧-1 por dado. Alcance estendível com 🍖.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_cura_area",
      "source": "heroi",
      "source_id": "cura_area",
      "source_class": "cleric",
      "name": "Cura em Área",
      "icon": "🌟",
      "descricao": "1d8 a 3d8 + INT em todos os aliados no raio 5. 🍖-4 💧-4 por dado.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_purificacao",
      "source": "heroi",
      "source_id": "purificacao",
      "source_class": "cleric",
      "name": "Purificação",
      "icon": "✨",
      "descricao": "Remove veneno, doença, maldição ou petrificação de um aliado adjacente.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_ressurreicao",
      "source": "heroi",
      "source_id": "ressurreicao",
      "source_class": "cleric",
      "name": "Ressurreição",
      "icon": "💫",
      "descricao": "Traz um aliado morto adjacente de volta com 1 HP. 🍖-10 💧-10.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_bard_cancao_heroica",
      "source": "heroi",
      "source_id": "cancao_heroica",
      "source_class": "bard",
      "name": "Canção Heroica",
      "icon": "🎵",
      "descricao": "Ativa buffs musicais para aliados em raio de 5 quadrados",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_bard_provocacao",
      "source": "heroi",
      "source_id": "provocacao",
      "source_class": "bard",
      "name": "Provocação",
      "icon": "😤",
      "descricao": "Impõe desvantagem ao inimigo e o força a atacar Henrique por 3 turnos",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_imposicao_maos",
      "source": "heroi",
      "source_id": "imposicao_maos",
      "source_class": "paladin",
      "name": "Imposição das Mãos",
      "icon": "🙏",
      "descricao": "Cura 1d6 + bônus Força em aliado adjacente",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_golpe_sagrado",
      "source": "heroi",
      "source_id": "golpe_sagrado",
      "source_class": "paladin",
      "name": "Golpe Sagrado",
      "icon": "⚔️",
      "descricao": "+1d8 dano sagrado. Dobrado contra mortos-vivos e demônios",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_protetor",
      "source": "heroi",
      "source_id": "protetor",
      "source_class": "paladin",
      "name": "Protetor",
      "icon": "🛡️",
      "descricao": "Aliado recebe metade do dano. A outra metade vai para Richard",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_regeneracao_divina",
      "source": "heroi",
      "source_id": "regeneracao_divina",
      "source_class": "paladin",
      "name": "Regeneração Divina",
      "icon": "✨",
      "descricao": "Recupera 1 HP por turno até HP máximo",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_guerreiro_luz",
      "source": "heroi",
      "source_id": "guerreiro_luz",
      "source_class": "paladin",
      "name": "Guerreiro da Luz",
      "icon": "💡",
      "descricao": "+1/+2 em Visão, Ataque, Dano e CA. Apenas Richard",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "guild_sorrateiro",
      "source": "guilda",
      "source_id": "sorrateiro",
      "name": "Sorrateiro",
      "icon": "✦",
      "descricao": "Enquanto equipada, revela o círculo de alcance da visão de cada monstro visível.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_mira_perfeita",
      "source": "guilda",
      "source_id": "tecnica_mira_perfeita",
      "name": "Mira Perfeita",
      "icon": "✦",
      "descricao": "Próximo ataque à distância recebe vantagem; se acertar, +2 de dano.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_espirito_indomavel",
      "source": "guilda",
      "source_id": "tecnica_espirito_indomavel",
      "name": "Espírito Indomável",
      "icon": "✦",
      "descricao": "Ação livre. Remove Medo, Atordoamento e Lentidão; 1 rodada imune a Silêncio.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_grito_guerra",
      "source": "guilda",
      "source_id": "tecnica_grito_guerra",
      "name": "Grito de Guerra",
      "icon": "✦",
      "descricao": "Todos os aliados recebem +2 de movimento por 1 rodada.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_pressa",
      "source": "guilda",
      "source_id": "tecnica_pressa",
      "name": "Pressa",
      "icon": "✦",
      "descricao": "O seu movimento é dobrado nesta rodada.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_investida",
      "source": "guilda",
      "source_id": "tecnica_investida",
      "name": "Investida Heroica",
      "icon": "✦",
      "descricao": "Dobra o movimento; se andar ≥2 casas em linha reta, o próximo ataque corpo a corpo tem vantagem +2 dano.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_defesa_impecavel",
      "source": "guilda",
      "source_id": "tecnica_defesa_impecavel",
      "name": "Defesa Impecável",
      "icon": "✦",
      "descricao": "Até o próximo turno, ataques contra você têm desvantagem e você fica imune a Ataque Furtivo.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_pressao_constante",
      "source": "guilda",
      "source_id": "tecnica_pressao_constante",
      "name": "Pressão Constante",
      "icon": "✦",
      "descricao": "Um inimigo adjacente sofre -2 de CA por 2 rodadas.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_tatica_defensiva",
      "source": "guilda",
      "source_id": "tecnica_tatica_defensiva",
      "name": "Tática Defensiva",
      "icon": "✦",
      "descricao": "Escolha um aliado em até 4 casas; por 1d4 rodadas, metade do dano dele é transferida a você.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_passo_fantasma",
      "source": "guilda",
      "source_id": "tecnica_passo_fantasma",
      "name": "Passo Fantasma",
      "icon": "✦",
      "descricao": "Por 1d4 rodadas: +2 de movimento e você atravessa casas ocupadas por objetos (não paredes nem criaturas).",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_ataque_coordenado",
      "source": "guilda",
      "source_id": "tecnica_ataque_coordenado",
      "name": "Ataque Coordenado",
      "icon": "✦",
      "descricao": "Escolha um aliado; neste turno, quando você atacar um inimigo, o aliado também o ataca.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_sangue_frio",
      "source": "guilda",
      "source_id": "tecnica_sangue_frio",
      "name": "Sangue Frio",
      "icon": "✦",
      "descricao": "A primeira vez que errar um ataque, você pode rolá-lo novamente.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_resistencia_absoluta",
      "source": "guilda",
      "source_id": "tecnica_resistencia_absoluta",
      "name": "Resistência Absoluta",
      "icon": "✦",
      "descricao": "Recebe +2 em todos os testes de resistência por 2 rodadas.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_contra_ataque",
      "source": "guilda",
      "source_id": "tecnica_contra_ataque",
      "name": "Contra-Ataque",
      "icon": "✦",
      "descricao": "Até o próximo turno, quando um inimigo errar você (arma corpo a corpo/alcance ou besta de mão, e ele no alcance), você o ataca de volta.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_oportunidade",
      "source": "guilda",
      "source_id": "tecnica_oportunidade",
      "name": "Oportunidade",
      "icon": "✦",
      "descricao": "Escolha um aliado (não pode ser você); no PRÓPRIO turno dele, ganha uma ação extra — mover mais, atacar de novo, usar a habilidade de classe de novo, ou lançar mais uma magia. Expira no fim desta rodada se não for usada.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_instinto_sobrevivencia",
      "source": "guilda",
      "source_id": "tecnica_instinto_sobrevivencia",
      "name": "Instinto de Sobrevivência",
      "icon": "✦",
      "descricao": "Automática. Se um dano zeraria seu HP, você fica com 1 em vez de morrer. Depois disso, entra em recarga.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_ultimo_esforco",
      "source": "guilda",
      "source_id": "tecnica_ultimo_esforco",
      "name": "Último Esforço",
      "icon": "✦",
      "descricao": "Automática. Se um dano zeraria seu HP, você fica com 1 e ganha 2 turnos seguidos: todo ataque tem vantagem e todo acerto é crítico (nat20 → dano TRIPLICADO). Não pode se curar. Ao final, cai como se tivesse morrido normalmente (pode ser reerguido por Ressurreição).",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_golpe_decisivo",
      "source": "guilda",
      "source_id": "tecnica_golpe_decisivo",
      "name": "Golpe Decisivo",
      "icon": "✦",
      "descricao": "Arma o próximo ataque básico (corpo a corpo ou à distância): se acertar, é crítico automático (dano dobrado); num natural 20 enquanto armado, o dano é TRIPLICADO. Consumida no próximo ataque, acerte ou erre.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_sorte",
      "source": "guilda",
      "source_id": "tecnica_sorte",
      "name": "Sorte",
      "icon": "✦",
      "descricao": "Depois de errar um ataque, você pode gastar esta técnica para rolá-lo novamente contra o mesmo alvo. Independente do Sangue Frio.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_guerreiro_combinar_2",
      "source": "guilda",
      "source_id": "guerreiro_combinar_2",
      "name": "Combinar Duas",
      "icon": "✦",
      "descricao": "Permite armar DUAS habilidades no mesmo turno.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_mestre_combate",
      "source": "guilda",
      "source_id": "guerreiro_mestre_combate",
      "name": "Mestre de Combate",
      "icon": "✦",
      "descricao": "Permite armar as TRÊS habilidades no mesmo turno.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_mira_3",
      "source": "guilda",
      "source_id": "guerreiro_mira_3",
      "name": "Mira Certeira III",
      "icon": "✦",
      "descricao": "Mira Certeira também concede +2 de dano (além do +2 de acerto).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_golpe_3",
      "source": "guilda",
      "source_id": "guerreiro_golpe_3",
      "name": "Golpe Devastador III",
      "icon": "✦",
      "descricao": "Golpe Devastador passa a multiplicar os dados de dano por 2 (era ×1,5).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_furia_3",
      "source": "guilda",
      "source_id": "guerreiro_furia_3",
      "name": "Fúria Berserker III",
      "icon": "✦",
      "descricao": "Fúria Berserker concede 2 ataques extras (3 ataques no total).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_acerto",
      "source": "guilda",
      "source_id": "bardo_cancao_acerto",
      "name": "Canção: Acerto +1",
      "icon": "✦",
      "descricao": "O bônus de Acerto da Canção Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_dano",
      "source": "guilda",
      "source_id": "bardo_cancao_dano",
      "name": "Canção: Dano +1",
      "icon": "✦",
      "descricao": "O bônus de Dano da Canção Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_ca",
      "source": "guilda",
      "source_id": "bardo_cancao_ca",
      "name": "Canção: Armadura +1",
      "icon": "✦",
      "descricao": "O bônus de Armadura da Canção Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_movimento",
      "source": "guilda",
      "source_id": "bardo_cancao_movimento",
      "name": "Canção: Movimento +1",
      "icon": "✦",
      "descricao": "O bônus de Movimento da Canção Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_resistencia",
      "source": "guilda",
      "source_id": "bardo_cancao_resistencia",
      "name": "Canção: Resistência +1",
      "icon": "✦",
      "descricao": "O bônus de Resistência da Canção Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_suprema",
      "source": "guilda",
      "source_id": "bardo_cancao_suprema",
      "name": "Canção Heroica Suprema",
      "icon": "✦",
      "descricao": "A manutenção da Canção Heroica custa -1🍖 e -1💧 (mínimo 0).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_provocacao_2",
      "source": "guilda",
      "source_id": "bardo_provocacao_2",
      "name": "Provocação II",
      "icon": "✦",
      "descricao": "A desvantagem dura toda a provocação; Henrique ganha +2 CA e ataca o alvo com vantagem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_provocacao_3",
      "source": "guilda",
      "source_id": "bardo_provocacao_3",
      "name": "Provocação III",
      "icon": "✦",
      "descricao": "Todos os aliados atacam o alvo provocado com vantagem por 1 rodada.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_lendas_supremas",
      "source": "guilda",
      "source_id": "bardo_lendas_supremas",
      "name": "Lendas Supremas",
      "icon": "✦",
      "descricao": "Todos os bônus de Lenda passam a beneficiar o grupo inteiro (enquanto Henrique vivo).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_tecelagem_2",
      "source": "guilda",
      "source_id": "mago_tecelagem_2",
      "name": "Tecelagem Arcana II",
      "icon": "✦",
      "descricao": "Permite empilhar 2 metamagias no mesmo lançamento.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_tecelagem_3",
      "source": "guilda",
      "source_id": "mago_tecelagem_3",
      "name": "Tecelagem Arcana III",
      "icon": "✦",
      "descricao": "Permite empilhar as 3 metamagias no mesmo lançamento.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_fortalecer_2",
      "source": "guilda",
      "source_id": "mago_fortalecer_2",
      "name": "Fortalecer II",
      "icon": "✦",
      "descricao": "Fortalecer Magia multiplica o dano por 1,5 (era ×1,25).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_fortalecer_3",
      "source": "guilda",
      "source_id": "mago_fortalecer_3",
      "name": "Fortalecer III",
      "icon": "✦",
      "descricao": "Fortalecer Magia multiplica o dano por 2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_aprimorar_2",
      "source": "guilda",
      "source_id": "mago_aprimorar_2",
      "name": "Aprimorar II",
      "icon": "✦",
      "descricao": "Aprimorar Magia dá +2 na CD do save (era +1).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_aprimorar_3",
      "source": "guilda",
      "source_id": "mago_aprimorar_3",
      "name": "Aprimorar III",
      "icon": "✦",
      "descricao": "Aprimorar Magia dá +3 na CD do save.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_estender_2",
      "source": "guilda",
      "source_id": "mago_estender_2",
      "name": "Estender II",
      "icon": "✦",
      "descricao": "Estender Magia dá +2 rodadas de duração (era +1).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_estender_3",
      "source": "guilda",
      "source_id": "mago_estender_3",
      "name": "Estender III",
      "icon": "✦",
      "descricao": "Estender Magia dá +3 rodadas de duração.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_reviver_2",
      "source": "guilda",
      "source_id": "mago_reviver_2",
      "name": "Reviver os Mortos II",
      "icon": "✦",
      "descricao": "Criaturas passam a ocupar Slots de Controle iguais ao ND (fracionário incluso). Chance de sucesso: 100% − ND×15%.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_reviver_3",
      "source": "guilda",
      "source_id": "mago_reviver_3",
      "name": "Reviver os Mortos III",
      "icon": "✦",
      "descricao": "+2 Slots de Controle. Chance de sucesso: 100% − ND×10%.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_cura_2",
      "source": "guilda",
      "source_id": "clerigo_cura_2",
      "name": "Cura II",
      "icon": "✦",
      "descricao": "Cura pode usar até 2d8 + INT.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_cura_3",
      "source": "guilda",
      "source_id": "clerigo_cura_3",
      "name": "Cura III",
      "icon": "✦",
      "descricao": "Cura pode usar até 3d8 + INT.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_massa_2",
      "source": "guilda",
      "source_id": "clerigo_massa_2",
      "name": "Cura em Massa II",
      "icon": "✦",
      "descricao": "Cura em Massa: até 2d8 + INT, raio 4.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_massa_3",
      "source": "guilda",
      "source_id": "clerigo_massa_3",
      "name": "Cura em Massa III",
      "icon": "✦",
      "descricao": "Cura em Massa: até 3d8 + INT, raio 6.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_purif_2",
      "source": "guilda",
      "source_id": "clerigo_purif_2",
      "name": "Purificação II",
      "icon": "✦",
      "descricao": "Purificação também remove doenças.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_purif_3",
      "source": "guilda",
      "source_id": "clerigo_purif_3",
      "name": "Purificação III",
      "icon": "✦",
      "descricao": "Purificação também remove maldições e petrificação.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_ressur_2",
      "source": "guilda",
      "source_id": "clerigo_ressur_2",
      "name": "Ressurreição II",
      "icon": "✦",
      "descricao": "Ressurreição traz o aliado com metade dos PV (🍖15 💧15).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_ressur_3",
      "source": "guilda",
      "source_id": "clerigo_ressur_3",
      "name": "Ressurreição III",
      "icon": "✦",
      "descricao": "Ressurreição traz o aliado com PV cheio (🍖20 💧20).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_cura_maos_2",
      "source": "guilda",
      "source_id": "paladino_cura_maos_2",
      "name": "Cura pelas Mãos II",
      "icon": "✦",
      "descricao": "Imposição das Mãos cura 2d6 + FOR.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_cura_maos_3",
      "source": "guilda",
      "source_id": "paladino_cura_maos_3",
      "name": "Cura pelas Mãos III",
      "icon": "✦",
      "descricao": "Pode gastar +2🍖/+2💧 por +1d6 de cura (até 3×).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_ataque_sagrado_2",
      "source": "guilda",
      "source_id": "paladino_ataque_sagrado_2",
      "name": "Ataque Sagrado II",
      "icon": "✦",
      "descricao": "Golpe Sagrado causa +2d8 de dano sagrado por ataque.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_luz_2",
      "source": "guilda",
      "source_id": "paladino_luz_2",
      "name": "Guerreiro da Luz II",
      "icon": "✦",
      "descricao": "Mantém 3 atributos ativos; com Visão, detecta armadilhas em raio 2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_luz_3",
      "source": "guilda",
      "source_id": "paladino_luz_3",
      "name": "Guerreiro da Luz III",
      "icon": "✦",
      "descricao": "Mantém 4 atributos ativos; com Visão, detecta armadilhas em raio 3.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_defensor_2",
      "source": "guilda",
      "source_id": "paladino_defensor_2",
      "name": "Defensor II",
      "icon": "✦",
      "descricao": "O alcance da proteção aumenta para 5 quadrados.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_defensor_3",
      "source": "guilda",
      "source_id": "paladino_defensor_3",
      "name": "Defensor III",
      "icon": "✦",
      "descricao": "O dano dividido cai para 40%/40% (20% é mitigado).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_regen_2",
      "source": "guilda",
      "source_id": "paladino_regen_2",
      "name": "Regeneração II",
      "icon": "✦",
      "descricao": "Regeneração Divina também cura +1 HP dos aliados adjacentes.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_regen_3",
      "source": "guilda",
      "source_id": "paladino_regen_3",
      "name": "Regeneração III",
      "icon": "✦",
      "descricao": "A Regeneração Divina alcança aliados em raio 2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_furtivo_2",
      "source": "guilda",
      "source_id": "ladino_furtivo_2",
      "name": "Ataque Furtivo II",
      "icon": "✦",
      "descricao": "Ataque Furtivo também dispara se há aliado adjacente ao alvo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_furtivo_3",
      "source": "guilda",
      "source_id": "ladino_furtivo_3",
      "name": "Ataque Furtivo Supremo",
      "icon": "✦",
      "descricao": "1×/inimigo/rodada: quando um aliado acerta um inimigo, Luccas reage com um Ataque Furtivo nele.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_desarme_2",
      "source": "guilda",
      "source_id": "ladino_desarme_2",
      "name": "Desarme II",
      "icon": "✦",
      "descricao": "+2 na chance de desarmar armadilhas.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_desarme_3",
      "source": "guilda",
      "source_id": "ladino_desarme_3",
      "name": "Desarme III",
      "icon": "✦",
      "descricao": "Chance extra de recuperar o ouro da armadilha desarmada.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_veneno_2",
      "source": "guilda",
      "source_id": "ladino_veneno_2",
      "name": "Veneno Rápido II",
      "icon": "✦",
      "descricao": "O veneno na arma (corpo a corpo) dura 2 golpes certeiros.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_veneno_3",
      "source": "guilda",
      "source_id": "ladino_veneno_3",
      "name": "Veneno Rápido III",
      "icon": "✦",
      "descricao": "Pode manter 2 venenos diferentes na arma ao mesmo tempo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_esconder_2",
      "source": "guilda",
      "source_id": "ladino_esconder_2",
      "name": "Esconder nas Sombras II",
      "icon": "✦",
      "descricao": "+2 na chance de se esconder nas sombras.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_esconder_3",
      "source": "guilda",
      "source_id": "ladino_esconder_3",
      "name": "Esconder nas Sombras III",
      "icon": "✦",
      "descricao": "Ativar não gasta mais a ação bônus. Ao ser revelado, +2 de CA por 1 rodada.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_armadilha_urso",
      "source": "guilda",
      "source_id": "ladino_armadilha_urso",
      "name": "Fórmula: Armadilha de Urso",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Armadilha de Urso.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_fosso_estacas",
      "source": "guilda",
      "source_id": "ladino_fosso_estacas",
      "name": "Fórmula: Fosso com Estacas",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Fosso com Estacas.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_rede",
      "source": "guilda",
      "source_id": "ladino_rede",
      "name": "Fórmula: Rede",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Rede.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_armadilha_incendiaria",
      "source": "guilda",
      "source_id": "ladino_armadilha_incendiaria",
      "name": "Fórmula: Armadilha Incendiária",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Armadilha Incendiária.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_mina_terrestre",
      "source": "guilda",
      "source_id": "ladino_mina_terrestre",
      "name": "Fórmula: Mina Terrestre",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Mina Terrestre.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_fosso_envenenado",
      "source": "guilda",
      "source_id": "ladino_fosso_envenenado",
      "name": "Fórmula: Fosso com Estacas Envenenadas",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Fosso com Estacas Envenenadas.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_lamina_escondida",
      "source": "guilda",
      "source_id": "ladino_lamina_escondida",
      "name": "Fórmula: Lâmina Escondida",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Lâmina Escondida.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_lamina_pendulo",
      "source": "guilda",
      "source_id": "ladino_lamina_pendulo",
      "name": "Fórmula: Lâmina Pêndulo",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Lâmina Pêndulo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_nuvem_gas",
      "source": "guilda",
      "source_id": "ladino_nuvem_gas",
      "name": "Fórmula: Nuvem de Gás",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Nuvem de Gás.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin",
      "source": "guilda",
      "source_id": "lenda_goblin",
      "name": "Lenda: Goblin",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Goblin.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_skeleton",
      "source": "guilda",
      "source_id": "lenda_skeleton",
      "name": "Lenda: Esqueleto",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Esqueleto.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_orc",
      "source": "guilda",
      "source_id": "lenda_orc",
      "name": "Lenda: Orc",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Orc.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_dark_mage",
      "source": "guilda",
      "source_id": "lenda_dark_mage",
      "name": "Lenda: Mago das Trevas",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Mago das Trevas.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_troll",
      "source": "guilda",
      "source_id": "lenda_troll",
      "name": "Lenda: Troll",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Troll.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_dragon",
      "source": "guilda",
      "source_id": "lenda_dragon",
      "name": "Lenda: Dragão Ancião",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Dragão Ancião.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_aranha_sombria",
      "source": "guilda",
      "source_id": "lenda_aranha_sombria",
      "name": "Lenda: Aranha Sombria",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Aranha Sombria.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_escorpiao_pedra",
      "source": "guilda",
      "source_id": "lenda_escorpiao_pedra",
      "name": "Lenda: Escorpião de Pedra",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Escorpião de Pedra.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_esqueleto_humano",
      "source": "guilda",
      "source_id": "lenda_esqueleto_humano",
      "name": "Lenda: Esqueleto Humano",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Esqueleto Humano.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_esqueleto_animal",
      "source": "guilda",
      "source_id": "lenda_esqueleto_animal",
      "name": "Lenda: Esqueleto Animal",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Esqueleto Animal.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lobo_cinzento",
      "source": "guilda",
      "source_id": "lenda_lobo_cinzento",
      "name": "Lenda: Lobo Cinzento",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lobo Cinzento.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_crocodilo_jovem",
      "source": "guilda",
      "source_id": "lenda_crocodilo_jovem",
      "name": "Lenda: Crocodilo Jovem",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Crocodilo Jovem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_cobra_constritora",
      "source": "guilda",
      "source_id": "lenda_cobra_constritora",
      "name": "Lenda: Cobra Constritora",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Cobra Constritora.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_cobra_venenosa",
      "source": "guilda",
      "source_id": "lenda_cobra_venenosa",
      "name": "Lenda: Cobra Venenosa",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Cobra Venenosa.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_devorador_organico",
      "source": "guilda",
      "source_id": "lenda_devorador_organico",
      "name": "Lenda: Devorador Orgânico",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Devorador Orgânico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_urso_negro",
      "source": "guilda",
      "source_id": "lenda_urso_negro",
      "name": "Lenda: Urso Negro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Urso Negro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_orc_guerreiro",
      "source": "guilda",
      "source_id": "lenda_orc_guerreiro",
      "name": "Lenda: Orc Guerreiro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Orc Guerreiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin_arqueiro",
      "source": "guilda",
      "source_id": "lenda_goblin_arqueiro",
      "name": "Lenda: Goblin Arqueiro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Goblin Arqueiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin_combatente",
      "source": "guilda",
      "source_id": "lenda_goblin_combatente",
      "name": "Lenda: Goblin Combatente",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Goblin Combatente.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin_dual",
      "source": "guilda",
      "source_id": "lenda_goblin_dual",
      "name": "Lenda: Goblin Dual",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Goblin Dual.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin_xama",
      "source": "guilda",
      "source_id": "lenda_goblin_xama",
      "name": "Lenda: Xamã Goblin",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Xamã Goblin.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_kobold_lanceiro",
      "source": "guilda",
      "source_id": "lenda_kobold_lanceiro",
      "name": "Lenda: Kobold Lanceiro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Kobold Lanceiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_kobold_besteiro",
      "source": "guilda",
      "source_id": "lenda_kobold_besteiro",
      "name": "Lenda: Kobold Besteiro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Kobold Besteiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_necromante",
      "source": "guilda",
      "source_id": "lenda_necromante",
      "name": "Lenda: Necromante",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Necromante.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_zumbi_infectado",
      "source": "guilda",
      "source_id": "lenda_zumbi_infectado",
      "name": "Lenda: Zumbi Infectado",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Zumbi Infectado.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lagarto_carniceiro",
      "source": "guilda",
      "source_id": "lenda_lagarto_carniceiro",
      "name": "Lenda: Lagarto Carniceiro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lagarto Carniceiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_devorador_metal",
      "source": "guilda",
      "source_id": "lenda_devorador_metal",
      "name": "Lenda: Devorador de Metal",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Devorador de Metal.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_bugbear_sombras",
      "source": "guilda",
      "source_id": "lenda_bugbear_sombras",
      "name": "Lenda: Bugbear — Bicho-Papão das Sombras",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Bugbear — Bicho-Papão das Sombras.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ogro_clava",
      "source": "guilda",
      "source_id": "lenda_ogro_clava",
      "name": "Lenda: Ogro de Clava",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ogro de Clava.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ogro_lanca",
      "source": "guilda",
      "source_id": "lenda_ogro_lanca",
      "name": "Lenda: Ogro de Lança",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ogro de Lança.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_grotao",
      "source": "guilda",
      "source_id": "lenda_grotao",
      "name": "Lenda: Grotão",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Grotão.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_fogo",
      "source": "guilda",
      "source_id": "lenda_elemental_fogo",
      "name": "Lenda: Elemental de Fogo",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Fogo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_gelo",
      "source": "guilda",
      "source_id": "lenda_elemental_gelo",
      "name": "Lenda: Elemental de Gelo",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Gelo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_pedra",
      "source": "guilda",
      "source_id": "lenda_elemental_pedra",
      "name": "Lenda: Elemental de Pedra",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Pedra.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_eletrico",
      "source": "guilda",
      "source_id": "lenda_elemental_eletrico",
      "name": "Lenda: Elemental Elétrico",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental Elétrico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_ar",
      "source": "guilda",
      "source_id": "lenda_elemental_ar",
      "name": "Lenda: Elemental de Ar",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Ar.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_agua",
      "source": "guilda",
      "source_id": "lenda_elemental_agua",
      "name": "Lenda: Elemental de Água",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Água.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lobisomem",
      "source": "guilda",
      "source_id": "lenda_lobisomem",
      "name": "Lenda: Lobisomem",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lobisomem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_escravo_vampirico",
      "source": "guilda",
      "source_id": "lenda_escravo_vampirico",
      "name": "Lenda: Escravo Vampírico",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Escravo Vampírico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_vampiro_jovem",
      "source": "guilda",
      "source_id": "lenda_vampiro_jovem",
      "name": "Lenda: Vampiro Jovem",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Vampiro Jovem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_vampiro_anciao",
      "source": "guilda",
      "source_id": "lenda_vampiro_anciao",
      "name": "Lenda: Vampiro Ancião",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Vampiro Ancião.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lorde_vampiro",
      "source": "guilda",
      "source_id": "lenda_lorde_vampiro",
      "name": "Lenda: Lorde Vampiro",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lorde Vampiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "sopro_dragao",
      "source": "monstro",
      "name": "Sopro de Dragão",
      "icon": "🐉",
      "action_type": "acao",
      "range": 4,
      "damage": "2d6",
      "damage_types": [
        "fire"
      ],
      "save": "reflexos",
      "dc": 13,
      "shape": "linha",
      "target_mode": "todos",
      "success_effect": "metade",
      "descricao": "Expele energia em linha ou cone. Configure o elemento, alcance, dano, teste de resistência e se o sopro atinge um ou todos os alvos da área."
    }
  ],
  "spells": [
    {
      "id": "bola_fogo",
      "nome": "Bola de Fogo",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "🔥",
      "tipo": "area_persistente",
      "descricao": "Alcance 5. Área 3x3; 1d6/nível e fogo residual decrescente por 3 rodadas.",
      "save": "reflexos",
      "dano_por_nivel": "1d6",
      "area_raio": 1,
      "alcance_base": 5
    },
    {
      "id": "relampago",
      "nome": "Relâmpago",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "⚡",
      "tipo": "linha_reflexiva",
      "descricao": "1d6/nível por impacto. Linha reta de 4 casas (+1/nível) + ricochete de volta (casas atingidas 2x). Pedro só é ferido na volta.",
      "save": "reflexos",
      "dano_por_nivel": "1d6",
      "alcance_base": 4
    },
    {
      "id": "raio_congelante",
      "nome": "Raio Congelante",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "❄️",
      "tipo": "alvo",
      "descricao": "3d4+2d4/2níveis sem save. Fortitude ou paralisado 1-2 rodadas.",
      "save": "fortitude",
      "dano_base": "3d4",
      "alcance_base": 3
    },
    {
      "id": "sono",
      "nome": "Sono",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "🌙",
      "tipo": "area",
      "descricao": "Área. Vontade ou dorme 1d4+1. Primeiro ataque = crítico. Acorda com dano.",
      "save": "vontade",
      "area_raio": 2,
      "alcance": 5,
      "duracao": "1d4+1"
    },
    {
      "id": "comando",
      "nome": "Comando",
      "circulo": "primeiro",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🗣️",
      "tipo": "alvo",
      "descricao": "Só em monstros. Vontade ou o conjurador dirige o próximo turno do alvo — movimento, ação principal, habilidades e itens.",
      "save": "vontade",
      "alcance": 4,
      "duracao": 1
    },
    {
      "id": "medo",
      "nome": "Medo",
      "circulo": "primeiro",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "😱",
      "tipo": "area",
      "descricao": "Área. Vontade ou foge 1d4+1 rodadas. -1 ataque. Não se aproxima.",
      "save": "vontade",
      "area_raio": 2,
      "alcance": 5,
      "duracao": "1d4+1"
    },
    {
      "id": "clarividencia",
      "nome": "Clarividência",
      "circulo": "primeiro",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🔮",
      "tipo": "area_fixa",
      "descricao": "Remove névoa em área 4x4 (+escala por nível). Dura 2 rodadas.",
      "duracao": 2
    },
    {
      "id": "barreira_arcana",
      "nome": "Barreira Arcana",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "🛡️",
      "tipo": "buff_self",
      "descricao": "Reduz 5 de todo dano recebido por 1d6 + 1 rodada por nível. Estender aumenta a duração; Fortalecer reduz 7.",
      "duracao": "1d6"
    },
    {
      "id": "contramagica",
      "nome": "Contramágica",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "🛑",
      "tipo": "reacao",
      "descricao": "Reação. Teste oposto vs magia inimiga. Sucesso: cancela + inimigo perde ação.",
      "save": "teste_oposto"
    },
    {
      "id": "abencoar",
      "nome": "Abençoar",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "✨",
      "tipo": "area",
      "descricao": "Área 6x6. +1 ataque/dano/CA/resistência. Dura 1d4+1 rodadas.",
      "area_raio": 3,
      "alcance": 0,
      "duracao": "1d4+1",
      "buff": {
        "ataque": 1,
        "dano": 1,
        "ca": 1,
        "resistencia": 1
      }
    },
    {
      "id": "amaldicoar",
      "nome": "Amaldiçoar",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "☠️",
      "tipo": "area",
      "descricao": "Área 3x3. -1 ataque/dano/CA/resistência. Dura 1d4+1 rodadas.",
      "area_raio": 1,
      "alcance": 5,
      "duracao": "1d4+1",
      "debuff": {
        "ataque": -1,
        "dano": -1,
        "ca": -1,
        "resistencia": -1
      }
    },
    {
      "id": "abencoar_arma",
      "nome": "Abençoar Arma",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "⚔️",
      "tipo": "alvo_aliado",
      "descricao": "+1 ataque e dano na arma de aliado. Dura 1d6+2 rodadas.",
      "alcance": 6,
      "duracao": "1d6+2",
      "buff": {
        "ataque": 1,
        "dano": 1,
        "arma_ignora_resistencia": true
      }
    },
    {
      "id": "saciar",
      "nome": "Saciar",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "💧",
      "tipo": "toque",
      "descricao": "Toque. +20 fome +20 sede em 1 aliado.",
      "alcance": 1
    },
    {
      "id": "silencio",
      "nome": "Silêncio",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🔇",
      "tipo": "area_fixa",
      "descricao": "Área 4x4. Sem magias nem bônus de Canção Heroica dentro. Dura 1d4 rodadas.",
      "area_lado": 4,
      "alcance_base": 5,
      "duracao": "1d4"
    },
    {
      "id": "manto_escuridao",
      "nome": "Manto de Escuridão",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🌑",
      "tipo": "area_centrada",
      "descricao": "Raio 3. Escuridão — sem visão noturna: desvantagem. Com visão noturna: vantagem.",
      "area_raio": 3,
      "duracao": "1d4"
    },
    {
      "id": "criar_alimentos",
      "nome": "Criar Alimentos",
      "circulo": "segundo",
      "classe": [
        "cleric"
      ],
      "icone": "🍞",
      "tipo": "posicionar_bau",
      "descricao": "Cria em uma casa adjacente um baú com 1d4+2 alimentos aleatórios da taverna.",
      "alcance": 1
    },
    {
      "id": "regeneracao_magica",
      "nome": "Regeneração",
      "circulo": "segundo",
      "classe": [
        "cleric"
      ],
      "icone": "🌿",
      "tipo": "buff_aliado",
      "descricao": "Pool 2d6+2. +1 HP/rodada. Se morrer: volta com 1 HP -3 fome/sede.",
      "alcance": 6
    },
    {
      "id": "protecao_energia",
      "nome": "Proteção contra Energia",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🛡️",
      "tipo": "buff_self",
      "descricao": "Absorve 10 dano/rodada de fogo, gelo, eletricidade, ácido, água ou sagrado. Dura 1d6+1.",
      "duracao": "1d6+1"
    },
    {
      "id": "invisibilidade",
      "nome": "Invisibilidade",
      "circulo": "segundo",
      "classe": [
        "mage"
      ],
      "icone": "🫥",
      "tipo": "buff_self",
      "descricao": "Inimigos não atacam. Ataque com vantagem + furtivo. Quebra ao atacar/lançar.",
      "duracao": "1d6+1"
    },
    {
      "id": "visao_escuro",
      "nome": "Visão no Escuro",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "👁️",
      "tipo": "buff_aliado",
      "descricao": "Aliado ignora escuridão completamente até o fim da missão.",
      "alcance": 6
    },
    {
      "id": "jato_ar",
      "nome": "Jato de Ar",
      "circulo": "segundo",
      "classe": [
        "mage"
      ],
      "icone": "🌪️",
      "tipo": "cone",
      "descricao": "Cone 4q. 1d6 por nível. Falha: empurra 1d6q. Colisão com parede: +1d4.",
      "save": "reflexos",
      "dano_por_nivel": "1d6"
    },
    {
      "id": "velocidade",
      "nome": "Velocidade",
      "circulo": "terceiro",
      "classe": [
        "mage"
      ],
      "icone": "⚡",
      "tipo": "buff_self",
      "descricao": "Dobra todas as ações no turno. Custo normal por ação. Dura 1d4 rodadas.",
      "duracao": "1d4"
    },
    {
      "id": "lentidao",
      "nome": "Lentidão",
      "circulo": "terceiro",
      "classe": [
        "mage"
      ],
      "icone": "🐌",
      "tipo": "area",
      "descricao": "Área 3x3. Falha: 1 ação/rodada, -1 CA, sem reação. Sucesso: mov/2, -1 ataque.",
      "save": "vontade",
      "area_raio": 1,
      "alcance": 5,
      "duracao": "1d4"
    },
    {
      "id": "dominar_mente",
      "nome": "Dominar Mente",
      "circulo": "terceiro",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🧠",
      "tipo": "alvo",
      "descricao": "Vontade ou o conjurador dirige o alvo a cada turno dele por 1d4+1 rodadas. A cada dano sofrido, faz novo teste de Vontade com +2 cumulativo; passar rompe o controle.",
      "save": "vontade",
      "alcance": 5,
      "duracao": "1d4+1"
    },
    {
      "id": "dominar_morto_vivo",
      "nome": "Dominar Morto-Vivo",
      "circulo": "terceiro",
      "classe": [
        "mage"
      ],
      "icone": "💀",
      "tipo": "alvo",
      "descricao": "Morto-vivo testa Vontade (bônus = ND) ao ser lançada e a cada rodada na fase dos servos. Passar quebra o controle (volta hostil); 3 falhas seguidas = controle permanente. Slot único. Não conta para Animar Mortos.",
      "save": "vontade",
      "alcance": 4
    },
    {
      "id": "conjurar_elemental",
      "nome": "Conjurar Elemental",
      "circulo": "terceiro",
      "classe": [
        "cleric"
      ],
      "icone": "🌪️",
      "tipo": "invocacao",
      "descricao": "Invoca elemental controlado. Age após Lewis. Movimento 6q."
    },
    {
      "id": "raio_divino",
      "nome": "Raio Divino",
      "circulo": "terceiro",
      "classe": [
        "cleric"
      ],
      "icone": "✨",
      "tipo": "alvo",
      "descricao": "1d6+1 por nível. Reflexos: metade. Dobrado vs mortos-vivos e demônios.",
      "save": "reflexos",
      "dano_por_nivel": "1d6+1",
      "alcance": 6
    }
  ],
  "items": [
    {
      "id": "sword",
      "name": "Espada Curta de Ferro Serrilhado",
      "emoji": "⚔️",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante",
      "item_slot": "weapon"
    },
    {
      "id": "dagger",
      "name": "Adaga",
      "emoji": "🗡️",
      "die": "1d4",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "chicote",
      "name": "Chicote",
      "emoji": "🪢",
      "die": "1d4",
      "stat": "dex",
      "range": 2,
      "categoria": "cortante"
    },
    {
      "id": "hand_crossbow",
      "name": "Besta de Mão",
      "emoji": "🏹",
      "die": "1d4",
      "stat": "dex",
      "range": 4,
      "categoria": "perfurante"
    },
    {
      "id": "lanca_curta",
      "name": "Lança Curta",
      "emoji": "🔱",
      "die": "1d6",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "bordao",
      "name": "Bordão",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "cajado_madeira",
      "name": "Cajado de Madeira",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "reach": "cajado",
      "categoria": "contundente"
    },
    {
      "id": "staff",
      "name": "Cajado Arcano",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "reach": "cajado",
      "categoria": "contundente"
    },
    {
      "id": "maca",
      "name": "Maça",
      "emoji": "🔨",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "shortsword",
      "name": "Espada Curta",
      "emoji": "⚔️",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_basico",
      "name": "Machado de Ferro",
      "emoji": "🪓",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "arco_curto",
      "name": "Arco Curto",
      "emoji": "🏹",
      "die": "1d6",
      "stat": "dex",
      "range": 6,
      "categoria": "perfurante"
    },
    {
      "id": "lanca",
      "name": "Lança",
      "emoji": "🔱",
      "die": "1d8",
      "stat": "str_",
      "reach": "lanca",
      "categoria": "perfurante"
    },
    {
      "id": "longsword",
      "name": "Espada Longa",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "longbow",
      "name": "Arco Longo",
      "emoji": "🏹",
      "die": "1d8",
      "stat": "dex",
      "range": 10,
      "categoria": "perfurante"
    },
    {
      "id": "warhammer",
      "name": "Martelo de Guerra",
      "emoji": "🔨",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "besta",
      "name": "Besta",
      "emoji": "🏹",
      "die": "1d8",
      "stat": "dex",
      "range": 8,
      "categoria": "perfurante"
    },
    {
      "id": "mangual",
      "name": "Mangual",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "machado_duplo",
      "name": "Machado Duplo",
      "emoji": "🪓",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "bastsword",
      "name": "Espada Bastarda",
      "emoji": "⚔️",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_orc",
      "name": "Machado de Guerra Órquico",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "alabarda",
      "name": "Alabarda",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "range": 2,
      "categoria": "perfurante"
    },
    {
      "id": "espada2m",
      "name": "Espada de 2 Mãos",
      "emoji": "⚔️",
      "die": "2d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "dagger_prata",
      "name": "Adaga de Prata",
      "emoji": "🗡️",
      "die": "1d4",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "chicote_prata",
      "name": "Chicote de Prata",
      "emoji": "🪢",
      "die": "1d4",
      "stat": "dex",
      "range": 2,
      "categoria": "cortante"
    },
    {
      "id": "lanca_curta_prata",
      "name": "Lança Curta de Prata",
      "emoji": "🔱",
      "die": "1d6",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "bordao_prata",
      "name": "Bordão de Prata",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "maca_prata",
      "name": "Maça de Prata",
      "emoji": "🔨",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "shortsword_prata",
      "name": "Espada Curta de Prata",
      "emoji": "⚔️",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_basico_prata",
      "name": "Machado de Ferro de Prata",
      "emoji": "🪓",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "lanca_prata",
      "name": "Lança de Prata",
      "emoji": "🔱",
      "die": "1d8",
      "stat": "str_",
      "reach": "lanca",
      "categoria": "perfurante"
    },
    {
      "id": "longsword_prata",
      "name": "Espada Longa de Prata",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "warhammer_prata",
      "name": "Martelo de Guerra de Prata",
      "emoji": "🔨",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "mangual_prata",
      "name": "Mangual de Prata",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "machado_duplo_prata",
      "name": "Machado Duplo de Prata",
      "emoji": "🪓",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "bastsword_prata",
      "name": "Espada Bastarda de Prata",
      "emoji": "⚔️",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_orc_prata",
      "name": "Machado de Guerra Órquico de Prata",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "alabarda_prata",
      "name": "Alabarda de Prata",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "range": 2,
      "categoria": "perfurante"
    },
    {
      "id": "espada2m_prata",
      "name": "Espada de 2 Mãos de Prata",
      "emoji": "⚔️",
      "die": "2d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "escudo_p",
      "name": "Escudo Pequeno",
      "emoji": "🛡️",
      "kind": "shield",
      "ac_bonus": 1
    },
    {
      "id": "escudo_g",
      "name": "Escudo Grande",
      "emoji": "🛡️",
      "kind": "shield",
      "ac_bonus": 2
    },
    {
      "id": "cloak",
      "name": "Manto",
      "emoji": "🧣",
      "kind": "armor",
      "ac_bonus": 1
    },
    {
      "id": "leather",
      "name": "Armadura de Couro",
      "emoji": "🥋",
      "kind": "armor",
      "ac_bonus": 2
    },
    {
      "id": "leather_plate",
      "name": "Armadura de Couro e Placas",
      "emoji": "🥋",
      "kind": "armor",
      "ac_bonus": 3
    },
    {
      "id": "chainmail",
      "name": "Cota de Malha",
      "emoji": "🪖",
      "kind": "armor",
      "ac_bonus": 4
    },
    {
      "id": "bronze_armor",
      "name": "Armadura de Bronze",
      "emoji": "🪖",
      "kind": "armor",
      "ac_bonus": 5
    },
    {
      "id": "leather_mail",
      "name": "Armadura de Couro Revestido com Malha",
      "emoji": "🪖",
      "kind": "armor",
      "ac_bonus": 6
    },
    {
      "id": "plate",
      "name": "Armadura de Placas",
      "emoji": "🛡️",
      "kind": "armor",
      "ac_bonus": 6
    },
    {
      "id": "monster_leather_plate",
      "name": "Armadura de Couro de Monstro e Placas",
      "emoji": "🛡️",
      "kind": "armor",
      "ac_bonus": 7
    },
    {
      "id": "fullplate",
      "name": "Armadura Completa",
      "emoji": "🛡️",
      "kind": "armor",
      "ac_bonus": 8
    },
    {
      "id": "flechas",
      "name": "Flechas (×10)",
      "emoji": "🏹",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "flechas",
      "ammo_count": 10
    },
    {
      "id": "virotes",
      "name": "Virotes (×10)",
      "emoji": "🏹",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "virotes",
      "ammo_count": 10
    },
    {
      "id": "flechas_prata",
      "name": "Flechas de Prata (×10)",
      "emoji": "🏹",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "flechas_prata",
      "ammo_count": 10
    },
    {
      "id": "virotes_prata",
      "name": "Virotes de Prata (×10)",
      "emoji": "🏹",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "virotes_prata",
      "ammo_count": 10
    },
    {
      "id": "virote_incendiario",
      "name": "Virote Incendiário",
      "emoji": "🔥",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "virotes_incendiarios",
      "ammo_count": 1,
      "extra_damage": "1d4",
      "extra_damage_types": [
        "fire"
      ]
    },
    {
      "id": "flecha_incendiaria",
      "name": "Flecha Incendiária",
      "emoji": "🔥",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "flechas_incendiarias",
      "ammo_count": 1,
      "extra_damage": "1d4",
      "extra_damage_types": [
        "fire"
      ]
    },
    {
      "id": "veneno_fungo_acre",
      "name": "Fungo Acre",
      "emoji": "🍄",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_fungo_acre"
    },
    {
      "id": "veneno_dor_escarlate",
      "name": "Dor Escarlate",
      "emoji": "🩸",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_dor_escarlate"
    },
    {
      "id": "veneno_ardonia_negra",
      "name": "Ardonia Negra",
      "emoji": "🕷️",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_ardonia_negra"
    },
    {
      "id": "elixir",
      "name": "Elixir da Força",
      "emoji": "⚗️",
      "item_slot": "bag",
      "effect": "atk_bonus",
      "value": 3
    },
    {
      "id": "antidote",
      "name": "Antídoto",
      "emoji": "💚",
      "item_slot": "bag",
      "effect": "cure_poison",
      "value": 0
    },
    {
      "id": "oleo_dissolvente",
      "name": "Óleo Dissolvente",
      "emoji": "🫗",
      "item_slot": "bag",
      "effect": "cure_petrification",
      "value": 0
    },
    {
      "id": "elixir_depurativo",
      "name": "Elixir Depurativo",
      "emoji": "🧴",
      "item_slot": "bag",
      "effect": "cure_disease",
      "value": 0
    },
    {
      "id": "vela_escuridao",
      "name": "Vela da Escuridão",
      "emoji": "🕯️",
      "item_slot": "bag",
      "effect": "veil_shadow",
      "value": 0
    },
    {
      "id": "ring_str",
      "name": "Anel de Força",
      "emoji": "💍",
      "item_slot": "ring",
      "effect": "atk",
      "value": 1
    },
    {
      "id": "ring_vita",
      "name": "Anel da Vitalidade",
      "emoji": "💍",
      "item_slot": "ring",
      "effect": "maxhp",
      "value": 5
    },
    {
      "id": "helm_iron",
      "name": "Elmo de Ferro",
      "emoji": "⛑️",
      "item_slot": "head",
      "effect": "def_",
      "value": 1
    },
    {
      "id": "circlet",
      "name": "Tiara Arcana",
      "emoji": "👑",
      "item_slot": "head",
      "effect": "maxhp",
      "value": 4
    },
    {
      "id": "boots",
      "name": "Botas Velozes",
      "emoji": "👢",
      "item_slot": "item",
      "effect": "spd",
      "value": 1
    },
    {
      "id": "amulet",
      "name": "Amuleto da Sorte",
      "emoji": "📿",
      "item_slot": "item",
      "effect": "maxhp",
      "value": 5
    },
    {
      "id": "backpack",
      "name": "Mochila de Couro",
      "emoji": "🎒",
      "item_slot": "item",
      "effect": "bagslots",
      "value": 3
    },
    {
      "id": "veneno_aranha_sombria",
      "name": "Veneno da Aranha Sombria",
      "emoji": "🕷️",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_aranha_sombria"
    },
    {
      "id": "veneno_escorpiao_pedra",
      "name": "Veneno do Escorpião Pedra",
      "emoji": "🦂",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_escorpiao_pedra"
    },
    {
      "id": "veneno_cobra_cuspidora",
      "name": "Veneno de Cobra Cuspidora",
      "emoji": "🐍",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_cobra_cuspidora"
    },
    {
      "id": "veneno_basilisco",
      "name": "Peçonha do Basilisco",
      "emoji": "🦎",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_basilisco"
    },
    {
      "id": "veneno_polvo_abissal",
      "name": "Tinta do Polvo Abissal",
      "emoji": "🐙",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_polvo_abissal"
    },
    {
      "id": "veneno_agonia_sufocante",
      "name": "Agonia Sufocante",
      "emoji": "💀",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_agonia_sufocante"
    },
    {
      "id": "frasco_oleo",
      "name": "Frasco de Óleo Incendiário",
      "emoji": "🔥",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "fogo_grego",
      "name": "Fogo Grego",
      "emoji": "🟢",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "bomba_incendiaria",
      "name": "Bomba Incendiária",
      "emoji": "💣",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "granada",
      "name": "Granada Explosiva",
      "emoji": "💣",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "granada_superior",
      "name": "Granada Superior",
      "emoji": "💥",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "bomba_fumaca",
      "name": "Bomba de Fumaça",
      "emoji": "💨",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "frasco_acido",
      "name": "Frasco de Ácido",
      "emoji": "🧪",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "vidro_acido_grande",
      "name": "Vidro de Ácido Grande",
      "emoji": "🫙",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "cola_alquimica",
      "name": "Cola Alquímica",
      "emoji": "🍯",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "rede_arremesso",
      "name": "Rede",
      "emoji": "🕸️",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "instrumento_harpa_velho",
      "name": "Harpa Velha",
      "emoji": "🎵",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_rustico",
      "name": "Harpa Rústica",
      "emoji": "🎵",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_padrao",
      "name": "Harpa Padrão",
      "emoji": "🎵",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_tambor_rustico",
      "name": "Tambor de Guerra Rústico",
      "emoji": "🥁",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_tambor_padrao",
      "name": "Tambor de Guerra Padrão",
      "emoji": "🥁",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_rustico",
      "name": "Sino Rústico",
      "emoji": "🔔",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_padrao",
      "name": "Sino Padrão",
      "emoji": "🔔",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_alaude_rustico",
      "name": "Alaúde Rústico",
      "emoji": "🪕",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_alaude_padrao",
      "name": "Alaúde Padrão",
      "emoji": "🪕",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_refinado",
      "name": "Harpa Refinada",
      "emoji": "🎵",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_rustico",
      "name": "Trompa de Guerra Rústica",
      "emoji": "📯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_padrao",
      "name": "Trompa de Guerra Padrão",
      "emoji": "📯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_rustico",
      "name": "Lira Rústica",
      "emoji": "🎼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_padrao",
      "name": "Lira Padrão",
      "emoji": "🎼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_flauta_rustico",
      "name": "Flauta Rústica",
      "emoji": "🎶",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_flauta_padrao",
      "name": "Flauta Padrão",
      "emoji": "🎶",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_rustico",
      "name": "Violino Rústico",
      "emoji": "🎻",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_padrao",
      "name": "Violino Padrão",
      "emoji": "🎻",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_padrao_elfica",
      "name": "Harpa Padrão Élfica",
      "emoji": "🎵",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_padrao_elfica",
      "name": "Trompa de Guerra Padrão Élfica",
      "emoji": "📯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_padrao_elfica",
      "name": "Sino Padrão Élfico",
      "emoji": "🔔",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_tambor_padrao_ana",
      "name": "Tambor de Guerra Padrão Anão",
      "emoji": "🥁",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_padrao_ana",
      "name": "Lira Padrão Anã",
      "emoji": "🎼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_padrao_ana",
      "name": "Violino Padrão Anão",
      "emoji": "🎻",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_padrao_runico",
      "name": "Sino Padrão Rúnico",
      "emoji": "🔔",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_flauta_padrao_runico",
      "name": "Flauta Padrão Rúnica",
      "emoji": "🎶",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_padrao_runico",
      "name": "Trompa de Guerra Padrão Rúnica",
      "emoji": "📯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_padrao_runico",
      "name": "Violino Padrão Rúnico",
      "emoji": "🎻",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_padrao_runico",
      "name": "Lira Padrão Rúnica",
      "emoji": "🎼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_refinado_elfica_runico",
      "name": "Harpa Lendária Élfica",
      "emoji": "🎵",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_velho",
      "name": "Gaita Velha",
      "emoji": "🪗",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_rustico",
      "name": "Gaita Rústica",
      "emoji": "🪗",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_padrao",
      "name": "Gaita Padrão",
      "emoji": "🪗",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_refinado",
      "name": "Gaita Refinada",
      "emoji": "🪗",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_padrao_runico",
      "name": "Gaita Padrão Rúnica",
      "emoji": "🪗",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_refinado_ana_runico",
      "name": "Gaita Lendária Anã",
      "emoji": "🪗",
      "item_slot": "instrumento"
    },
    {
      "id": "pao",
      "name": "Pão",
      "emoji": "🥖",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "garrafa_agua",
      "name": "Garrafa de Água",
      "emoji": "💧",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "suco_fruta",
      "name": "Suco de Fruta",
      "emoji": "🧃",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "caneca_cerveja",
      "name": "Caneca de Cerveja",
      "emoji": "🍺",
      "item_slot": "bag",
      "effect": "ale",
      "value": 10
    },
    {
      "id": "garrafa_vinho",
      "name": "Garrafa de Vinho",
      "emoji": "🍷",
      "item_slot": "bag",
      "effect": "wine",
      "value": 15
    },
    {
      "id": "racao_viagem",
      "name": "Ração de Viagem",
      "emoji": "🥩",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "cantil_agua",
      "name": "Cantil de Água",
      "emoji": "🧴",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "agua_benta",
      "name": "Água Benta",
      "emoji": "💧✝️",
      "item_slot": "bag",
      "effect": "throwable"
    },
    {
      "id": "health_potion",
      "name": "Poção de Cura",
      "emoji": "🧪",
      "item_slot": "bag",
      "effect": "heal",
      "value": 10
    },
    {
      "id": "health_potion_small",
      "name": "Poção de Cura Pequena",
      "emoji": "🧪",
      "item_slot": "bag",
      "effect": "heal",
      "value": 5
    },
    {
      "id": "health_potion_concentrated",
      "name": "Poção de Cura Concentrada",
      "emoji": "🧪",
      "item_slot": "bag",
      "effect": "heal",
      "value": 10
    },
    {
      "id": "health_potion_improved",
      "name": "Poção de Cura Aprimorada",
      "emoji": "🧪",
      "item_slot": "bag",
      "effect": "heal",
      "value": 20
    },
    {
      "id": "regeneration_potion",
      "name": "Poção de Regeneração",
      "emoji": "🌿",
      "item_slot": "bag",
      "effect": "regeneration",
      "value": 10
    },
    {
      "id": "ensaio_sobre_a_cegueira",
      "name": "Ensaio sobre a Cegueira",
      "emoji": "☠️",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "ensaio_sobre_a_cegueira"
    }
  ],
  "traps": [
    {
      "tipo": "buraco",
      "nome": "Buraco",
      "icone": "🕳️",
      "cr": 0.1,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_urso",
      "nome": "Armadilha de Urso",
      "icone": "🪤",
      "cr": 0.25,
      "precisa_veneno": false
    },
    {
      "tipo": "fosso_estacas",
      "nome": "Fosso com Estacas",
      "icone": "⛏️",
      "cr": 0.35,
      "precisa_veneno": false
    },
    {
      "tipo": "rede",
      "nome": "Rede",
      "icone": "🕸️",
      "cr": 0.15,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_incendiaria",
      "nome": "Armadilha Incendiária",
      "icone": "🔥",
      "cr": 0.5,
      "precisa_veneno": false
    },
    {
      "tipo": "mina_terrestre",
      "nome": "Mina Terrestre",
      "icone": "💣",
      "cr": 0.75,
      "precisa_veneno": false
    },
    {
      "tipo": "fosso_envenenado",
      "nome": "Fosso com Estacas Envenenadas",
      "icone": "☠️",
      "cr": 0.5,
      "precisa_veneno": true
    },
    {
      "tipo": "lamina_escondida",
      "nome": "Lâmina Escondida",
      "icone": "🗡️",
      "cr": 0.55,
      "precisa_veneno": false,
      "permite_veneno": true
    },
    {
      "tipo": "lamina_pendulo",
      "nome": "Lâmina Pêndulo",
      "icone": "🗡️",
      "cr": 0.7,
      "precisa_veneno": false
    },
    {
      "tipo": "nuvem_gas",
      "nome": "Nuvem de Gás",
      "icone": "🌫️",
      "cr": 0.4,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_teletransporte",
      "nome": "Armadilha de Teletransporte",
      "icone": "🌀",
      "cr": 0.4,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_dardos_envenenados",
      "nome": "Armadilha de Dardos Envenenados",
      "icone": "🎯",
      "cr": 0.4,
      "precisa_veneno": true
    },
    {
      "tipo": "armadilha_maldicao",
      "nome": "Armadilha de Maldição",
      "icone": "☠️",
      "cr": 0.75,
      "precisa_veneno": false
    }
  ],
  "venoms": [
    {
      "id": "veneno_aranha_sombria",
      "name": "Veneno da Aranha Sombria"
    },
    {
      "id": "veneno_escorpiao_pedra",
      "name": "Veneno do Escorpião Pedra"
    },
    {
      "id": "veneno_cobra_cuspidora",
      "name": "Veneno de Cobra Cuspidora"
    },
    {
      "id": "veneno_basilisco",
      "name": "Peçonha do Basilisco"
    },
    {
      "id": "veneno_polvo_abissal",
      "name": "Tinta do Polvo Abissal"
    },
    {
      "id": "veneno_agonia_sufocante",
      "name": "Agonia Sufocante"
    },
    {
      "id": "veneno_fungo_acre",
      "name": "Fungo Acre"
    },
    {
      "id": "veneno_dor_escarlate",
      "name": "Dor Escarlate"
    },
    {
      "id": "veneno_ardonia_negra",
      "name": "Ardonia Negra"
    },
    {
      "id": "ensaio_sobre_a_cegueira",
      "name": "Ensaio sobre a Cegueira"
    }
  ],
  "decorations": [
    {
      "type": "cama",
      "nome": "Cama",
      "emoji": "🛏️",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "lareira",
      "nome": "Lareira",
      "emoji": "🪵",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "fonte",
      "nome": "Fonte",
      "emoji": "⛲",
      "size": [
        2,
        2
      ],
      "gira": false,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": "fountain",
      "image": null
    },
    {
      "type": "fogueira",
      "nome": "Fogueira",
      "emoji": "🔥",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "campfire",
      "image": null
    },
    {
      "type": "tumba",
      "nome": "Tumba",
      "emoji": "⚰️",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "mesa_cadeiras",
      "nome": "Mesa com cadeiras",
      "emoji": "🪑",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "estante",
      "nome": "Estante",
      "emoji": "🗄️",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "carroca",
      "nome": "Carroça",
      "emoji": "🛒",
      "size": [
        2,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "coluna",
      "nome": "Coluna de pedra",
      "emoji": "🏛️",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "barril",
      "nome": "Barril",
      "emoji": "🛢️",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "arca_tesouros",
      "nome": "Arca de tesouros",
      "emoji": "💰",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "cama_casal",
      "nome": "Cama de casal",
      "emoji": "🛌",
      "size": [
        2,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "estante_livros",
      "nome": "Estante de livros",
      "emoji": "📚",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "altar",
      "nome": "Altar ritualístico",
      "emoji": "🛐",
      "size": [
        2,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "trono",
      "nome": "Trono de rei",
      "emoji": "👑",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "gaiola",
      "nome": "Gaiola com esqueleto",
      "emoji": "⛓️",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "grades_prisao",
      "nome": "Grades de prisão",
      "emoji": "🚧",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "estante_armas",
      "nome": "Estante de armas",
      "emoji": "⚔️",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "mesa_tortura",
      "nome": "Mesa de tortura",
      "emoji": "🔪",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "mesa_quimica",
      "nome": "Mesa de química",
      "emoji": "🧪",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": false,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "arvore",
      "nome": "Árvore",
      "emoji": "🌳",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "arvore_grande",
      "nome": "Árvore grande",
      "emoji": "🌲",
      "size": [
        2,
        2
      ],
      "gira": false,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": null
    },
    {
      "type": "arvore_seca",
      "nome": "Árvore seca",
      "emoji": "🪵",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": true,
      "pisavel": false,
      "loot_capaz": true,
      "special": null,
      "image": "arvore_seca.png"
    },
    {
      "type": "caverna",
      "nome": "Caverna",
      "emoji": "🕳️",
      "size": [
        2,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "caverna.png"
    },
    {
      "type": "chao",
      "nome": "Chão (grama)",
      "emoji": "🌿",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "floor",
      "image": null
    },
    {
      "type": "brasao_leao",
      "nome": "Brasão do Leão",
      "emoji": "🦁",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "wall",
      "image": "brasao_leao.png"
    },
    {
      "type": "cortina_vermelha",
      "nome": "Cortina vermelha",
      "emoji": "🔴",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "wall",
      "image": "cortina_vermelha.png"
    },
    {
      "type": "cortina_branca",
      "nome": "Cortina branca",
      "emoji": "⚪",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "wall",
      "image": "cortina_branca.png"
    }
  ],
  "materiais": [
    {
      "id": "pedra_cinza",
      "nome": "Pedra cinza",
      "categoria": "piso",
      "cor": "#6f6f78",
      "solido": false,
      "oclui": false
    },
    {
      "id": "terra",
      "nome": "Terra",
      "categoria": "piso",
      "cor": "#75451f",
      "solido": false,
      "oclui": false
    },
    {
      "id": "grama",
      "nome": "Grama",
      "categoria": "piso",
      "cor": "#287322",
      "solido": false,
      "oclui": false
    },
    {
      "id": "agua",
      "nome": "Água",
      "categoria": "piso",
      "cor": "#126da1",
      "solido": false,
      "oclui": false
    },
    {
      "id": "agua_profunda",
      "nome": "Água profunda",
      "categoria": "piso",
      "cor": "#06173f",
      "solido": false,
      "oclui": false
    },
    {
      "id": "pedra_negra",
      "nome": "Pedra negra",
      "categoria": "piso",
      "cor": "#23232a",
      "solido": false,
      "oclui": false
    },
    {
      "id": "madeira_escura",
      "nome": "Piso de tábuas escuras",
      "categoria": "piso",
      "cor": "#3b200f",
      "solido": false,
      "oclui": false
    },
    {
      "id": "entulho",
      "nome": "Entulho",
      "categoria": "piso",
      "cor": "#4a4640",
      "solido": true,
      "oclui": true
    },
    {
      "id": "pedra_normal",
      "nome": "Pedra normal",
      "categoria": "parede",
      "cor": "#5a5a6a",
      "solido": false,
      "oclui": false
    },
    {
      "id": "enegrecida",
      "nome": "Pedra enegrecida",
      "categoria": "parede",
      "cor": "#2c2b30",
      "solido": false,
      "oclui": false
    },
    {
      "id": "pedra_caverna",
      "nome": "Pedra de caverna",
      "categoria": "parede",
      "cor": "#4d4338",
      "solido": false,
      "oclui": false
    },
    {
      "id": "desmoronada",
      "nome": "Parede desmoronada",
      "categoria": "parede",
      "cor": "#534b40",
      "solido": false,
      "oclui": false
    },
    {
      "id": "madeira",
      "nome": "Parede de madeira envernizada",
      "categoria": "parede",
      "cor": "#4a270f",
      "solido": false,
      "oclui": false
    }
  ]
};
// GERADO por tools/export_catalog.py — não editar à mão.
// Rode `python tools/export_catalog.py` para regenerar.
