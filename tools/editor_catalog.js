window.EDITOR_CATALOG = {
  "monsters": [
    {
      "type": "goblin",
      "name": "Goblin",
      "emoji": "ðŸ‘º",
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
      "emoji": "ðŸ’€",
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
      "emoji": "ðŸ‘¹",
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
      "emoji": "ðŸ§Ÿ",
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
      "emoji": "ðŸ—¿",
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
      "name": "DragÃ£o AnciÃ£o",
      "emoji": "ðŸ‰",
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
      "emoji": "ðŸ•·ï¸",
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
      "name": "EscorpiÃ£o de Pedra",
      "emoji": "ðŸ¦‚",
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
          "name": "PinÃ§a",
          "atk_bonus": 2,
          "damage": "1d4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "on_hit": null
        },
        {
          "name": "FerrÃ£o",
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
          "id": "veneno_ferrao",
          "name": "Veneno do FerrÃ£o",
          "action_type": "passiva",
          "dc": 9,
          "save": "fortitude",
          "effect": "penalidade_ataque_movimento"
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
      "emoji": "ðŸ’€",
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
          "name": "Fraqueza MÃ¡gica",
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
          "descricao": "ResistÃªncia a perfurante (-2 dano)"
        },
        {
          "type": "physical",
          "categoria": "cortante",
          "bonus_flat": -1,
          "descricao": "ResistÃªncia a cortante (-1 dano)"
        },
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2,
          "descricao": "VulnerÃ¡vel a impacto (+2 dano)"
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
      "emoji": "ðŸ¦´",
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
          "name": "Movimento ErrÃ¡tico",
          "action_type": "passiva",
          "descricao": "Ignora terreno difÃ­cil â€” avanÃ§a sem hesitar"
        },
        {
          "id": "sem_instinto",
          "name": "Sem Instinto",
          "action_type": "passiva",
          "descricao": "Nunca foge nem recua â€” avanÃ§a atÃ© ser destruÃ­do"
        },
        {
          "id": "fraqueza_magica",
          "name": "Fraqueza MÃ¡gica",
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
          "descricao": "ResistÃªncia a perfurante (-2 dano)"
        },
        {
          "type": "physical",
          "categoria": "cortante",
          "bonus_flat": -1,
          "descricao": "ResistÃªncia a cortante (-1 dano)"
        },
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2,
          "descricao": "VulnerÃ¡vel a impacto (+2 dano)"
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
      "emoji": "ðŸº",
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
          "name": "CaÃ§a em Bando",
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
          "descricao": "SensÃ­vel a venenos â€” -2 Fort vs venenos"
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
      "type": "crocodilo_jovem",
      "name": "Crocodilo Jovem",
      "emoji": "ðŸŠ",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 16,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "porte": "medio",
      "image": "crocodiloJovem",
      "str_": 16,
      "dex": 10,
      "con_": 14,
      "int_": 2,
      "fort": 5,
      "ref_": 2,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 5,
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
          "id": "agarrar",
          "name": "Agarrar",
          "action_type": "passiva",
          "dc": 12,
          "save": "fortitude",
          "descricao": "Ao acertar, alvo testa FOR ou REF CD 12 â€” falha: preso"
        },
        {
          "id": "atq_mandibula",
          "name": "Ataque de MandÃ­bula",
          "action_type": "passiva",
          "descricao": "Se alvo preso e adjacente: 1d8+3 dano direto (sem rolagem de acerto)"
        },
        {
          "id": "arrastar",
          "name": "Arrastar",
          "action_type": "passiva",
          "descricao": "Move alvo preso junto ao se deslocar"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "lightning",
          "multiplier": 1.5,
          "descricao": "+50% dano elÃ©trico (dobrado na Ã¡gua)"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "crocodilo_jovem",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "cobra_constritora",
      "name": "Cobra Constritora",
      "emoji": "ðŸ",
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
          "name": "ConstriÃ§Ã£o",
          "action_type": "passiva",
          "dc": 11,
          "save": "fortitude",
          "escape_saves": [
            "fortitude"
          ],
          "descricao": "Ao acertar, alvo testa FOR CD 11 â€” falha: preso"
        },
        {
          "id": "esmagar",
          "name": "Esmagar",
          "action_type": "passiva",
          "descricao": "Enquanto preso e adjacente: 1d6 dano automÃ¡tico por turno"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "cortante",
          "bonus_flat": 2,
          "descricao": "Corpo vulnerÃ¡vel a corte (+2 dano cortante)"
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
      "emoji": "ðŸ",
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
          "descricao": "Ao acertar a mordida, aplica veneno (doenÃ§a leve)"
        },
        {
          "id": "ataque_rapido",
          "name": "Ataque RÃ¡pido",
          "action_type": "passiva",
          "descricao": "Se nÃ£o se mover no turno: +1 no ataque"
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
          "descricao": "Corpo frÃ¡gil (+1 dano de concussÃ£o)"
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
      "name": "Devorador OrgÃ¢nico",
      "emoji": "ðŸŸ¢",
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
          "descricao": "Ao acertar: +1 nÃ­vel de dano em equipamento orgÃ¢nico do alvo (couro/madeira/tecido)"
        },
        {
          "id": "corrosao_viva",
          "name": "CorrosÃ£o Viva",
          "action_type": "passiva",
          "descricao": "Alvo sem armadura: 1 dano/turno por 2 turnos (acumula a cada acerto)"
        },
        {
          "id": "absorver_materia",
          "name": "Absorver MatÃ©ria",
          "action_type": "passiva",
          "descricao": "Quando destrÃ³i um item orgÃ¢nico: recupera 1d4 HP"
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
          "descricao": "CombustÃ£o rÃ¡pida (dano de fogo dobrado)"
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
      "emoji": "ðŸ»",
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
          "name": "FÃºria",
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
          "descricao": "Corpo massivo: +1 dano de perfuraÃ§Ã£o/alcance (arcos, bestas, lanÃ§as)"
        },
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": -1,
          "descricao": "Corpo massivo: -1 dano de concussÃ£o (martelos, maÃ§as, bastÃµes)"
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
      "emoji": "ðŸ‘¹",
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
          "name": "FÃºria Cega",
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
      "emoji": "ðŸ‘º",
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
      "emoji": "ðŸ‘º",
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
          "descricao": "Arremesso 1d4+2 (alcance 3) como aÃ§Ã£o bÃ´nus; 1 natural quebra a arma"
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
      "emoji": "ðŸ‘º",
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
          "descricao": "Arremesso 1d4+2 (alcance 3) como aÃ§Ã£o bÃ´nus; 1 natural quebra a arma"
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
      "name": "XamÃ£ Goblin",
      "emoji": "ðŸ‘º",
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
          "name": "SilÃªncio",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 2,
          "descricao": "Cria Ã¡rea de SilÃªncio (some se o xamÃ£ morrer)"
        },
        {
          "id": "amaldicoar",
          "name": "AmaldiÃ§oar",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1,
          "descricao": "Debuff -1 em ataque/dano/CA/resistÃªncia nos herÃ³is"
        },
        {
          "id": "abencoar",
          "name": "AbenÃ§oar",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1,
          "descricao": "Buff +1 em ataque/dano/CA/resistÃªncia nos goblins aliados"
        },
        {
          "id": "concentracao_fragil",
          "name": "ConcentraÃ§Ã£o FrÃ¡gil",
          "action_type": "passiva",
          "descricao": "Se sofrer dano, nÃ£o pode usar magia no prÃ³ximo turno"
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
      "emoji": "ðŸŠ",
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
          "name": "LanÃ§a Curta",
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
          "id": "veneno_lanca",
          "name": "LanÃ§a Envenenada",
          "action_type": "acao_livre",
          "dc": 8,
          "save": "fortitude",
          "effect": "veneno_aranha_sombria"
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
      "emoji": "ðŸŠ",
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
          "name": "Besta de MÃ£o",
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
      "emoji": "ðŸ§™",
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
          "name": "AmaldiÃ§oar",
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
          "action_type": "passiva",
          "descricao": "Inicia com 2 esqueletos; mortos-vivos prÃ³ximos recebem +1 em Vontade"
        },
        {
          "id": "concentracao_sombria",
          "name": "ConcentraÃ§Ã£o Sombria",
          "action_type": "passiva",
          "descricao": "Ao sofrer dano: Vontade CD 10 ou perde a aÃ§Ã£o de magia no turno"
        },
        {
          "id": "essencia_profana",
          "name": "EssÃªncia Profana",
          "action_type": "passiva",
          "descricao": "Sofre dano dobrado de efeitos sagrados/luz"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "holy",
          "multiplier": 2,
          "descricao": "EssÃªncia profana: dano sagrado/luz dobrado"
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
      "emoji": "ðŸ§Ÿ",
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
          "name": "ResistÃªncia Morta",
          "action_type": "passiva",
          "dc": 10,
          "save": "fortitude",
          "descricao": "A 0 HP: Fortitude CD 10 â†’ fica com 1 HP (dano sagrado/luz ignora e destrÃ³i de vez)"
        },
        {
          "id": "infeccao",
          "name": "InfecÃ§Ã£o",
          "action_type": "passiva",
          "dc": 10,
          "save": "fortitude",
          "descricao": "Ao acertar: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve"
        },
        {
          "id": "lento_incansavel",
          "name": "Lento e IncansÃ¡vel",
          "action_type": "passiva",
          "descricao": "NÃ£o corre nem foge â€” avanÃ§a sem parar"
        },
        {
          "id": "corpo_morto",
          "name": "Corpo Morto",
          "action_type": "passiva",
          "descricao": "NÃ£o come, bebe nem respira"
        }
      ],
      "immunities": [
        "veneno",
        "controle_mental"
      ],
      "weaknesses": [
        {
          "type": "holy",
          "multiplier": 2,
          "descricao": "Consagrado Ã  destruiÃ§Ã£o: dano sagrado/luz dobrado (morte sagrada = destruiÃ§Ã£o total)"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "zumbi",
      "undead": true,
      "subtipo": "morto_vivo",
      "darkvision_range": 8
    },
    {
      "type": "lagarto_carniceiro",
      "name": "Lagarto Carniceiro",
      "emoji": "ðŸ¦Ž",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 24,
      "ac": 14,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "porte": "grande",
      "image": "lagartoCarniceiro",
      "str_": 16,
      "dex": 14,
      "con_": 14,
      "int_": 6,
      "fort": 4,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 6,
          "damage": "1d8+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "on_hit": null,
          "categoria": "perfurante"
        }
      ],
      "special_abilities": [
        {
          "id": "combo_devorador",
          "name": "Combo Devorador",
          "action_type": "passiva",
          "descricao": "Se as 2 mordidas acertarem no turno: 2 ataques de Garra imediatos"
        },
        {
          "id": "predador_oportunista",
          "name": "Predador Oportunista",
          "action_type": "passiva",
          "descricao": "+1 nas mordidas contra alvos com menos de 50% do HP"
        },
        {
          "id": "faro_carnica",
          "name": "Faro de CarniÃ§a",
          "action_type": "passiva",
          "descricao": "Prioriza sempre o alvo com menor HP"
        },
        {
          "id": "duas_cabecas",
          "name": "Duas CabeÃ§as",
          "action_type": "passiva",
          "descricao": "+1 em percepÃ§Ã£o; difÃ­cil de surpreender (flavor)"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "veneno_dobrado",
          "descricao": "SensÃ­vel a venenos: todos os efeitos dobrados"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "lagarto_carniceiro",
      "undead": false,
      "subtipo": "animal"
    },
    {
      "type": "devorador_metal",
      "name": "Devorador de Metal",
      "emoji": "ðŸ”©",
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
          "descricao": "Ao acertar: +1 nÃ­vel de dano na arma OU armadura metÃ¡lica do alvo"
        },
        {
          "id": "devorar_metal",
          "name": "Devorar Metal",
          "action_type": "passiva",
          "descricao": "Item a 3 nÃ­veis Ã© destruÃ­do e o Devorador recupera 1d6 HP"
        },
        {
          "id": "alimentacao_metalica",
          "name": "AlimentaÃ§Ã£o MetÃ¡lica",
          "action_type": "passiva",
          "descricao": "Gasta a aÃ§Ã£o para consumir item metÃ¡lico no chÃ£o e recuperar 1d6 HP"
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
      "name": "Bugbear â€” Bicho-PapÃ£o das Sombras",
      "emoji": "ðŸ˜ˆ",
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
          "name": "Manto de EscuridÃ£o",
          "action_type": "magia",
          "uses_per_combat": 1,
          "circulo": 1,
          "descricao": "Cria uma Ã¡rea de escuridÃ£o centrada em si (1x por combate)"
        },
        {
          "id": "ataque_das_sombras",
          "name": "Ataque das Sombras",
          "action_type": "passiva",
          "descricao": "Se o alvo nÃ£o o enxerga (bugbear oculto OU alvo na escuridÃ£o sem visÃ£o no escuro): +2 ataque e +1d6 de dano em TODOS os ataques"
        },
        {
          "id": "cacador_das_trevas",
          "name": "CaÃ§ador das Trevas",
          "action_type": "passiva",
          "descricao": "Em Ã¡rea escura: +2 CA, +1 ataque e sempre pode usar Ataque das Sombras"
        },
        {
          "id": "desaparecer_nas_sombras",
          "name": "Desaparecer nas Sombras",
          "action_type": "acao_livre",
          "cooldown_turns": 5,
          "descricao": "SÃ³ na escuridÃ£o (apÃ³s Manto): fica oculto (imune a ataques Ã  distÃ¢ncia; corpo a corpo -4), move atÃ© 3, atÃ© o inÃ­cio do prÃ³ximo turno"
        },
        {
          "id": "visao_perfeita_escuro",
          "name": "VisÃ£o no Escuro",
          "action_type": "passiva",
          "descricao": "Enxerga perfeitamente no escuro â€” nÃ£o sofre penalidades nas trevas"
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
      "emoji": "ðŸ§Œ",
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
          "name": "ForÃ§a Descomunal",
          "action_type": "ataque",
          "cooldown_turns": 4,
          "save": "fortitude",
          "dc": 10,
          "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a prÃ³xima rodada). Recarga 4 rodadas"
        },
        {
          "id": "mente_bruta",
          "name": "Mente Bruta",
          "action_type": "passiva",
          "descricao": "-2 em Vontade contra controle mental"
        },
        {
          "id": "lento_previsivel",
          "name": "Lento e PrevisÃ­vel",
          "action_type": "passiva",
          "descricao": "Se errar um ataque: -2 de CA atÃ© o prÃ³ximo turno"
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
      "name": "Ogro de LanÃ§a",
      "emoji": "ðŸ§Œ",
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
          "name": "LanÃ§a Grande",
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
          "name": "ForÃ§a Descomunal",
          "action_type": "ataque",
          "cooldown_turns": 4,
          "save": "fortitude",
          "dc": 10,
          "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a prÃ³xima rodada). Recarga 4 rodadas"
        },
        {
          "id": "mente_bruta",
          "name": "Mente Bruta",
          "action_type": "passiva",
          "descricao": "-2 em Vontade contra controle mental"
        },
        {
          "id": "lento_previsivel",
          "name": "Lento e PrevisÃ­vel",
          "action_type": "passiva",
          "descricao": "Se errar um ataque: -2 de CA atÃ© o prÃ³ximo turno"
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
      "type": "grotao",
      "name": "GrotÃ£o",
      "emoji": "ðŸ¦‚",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 36,
      "ac": 15,
      "natural_armor": 5,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        3
      ],
      "porte": "grande",
      "image": "grotao",
      "str_": 18,
      "dex": 10,
      "con_": 16,
      "int_": 3,
      "fort": 6,
      "ref_": 3,
      "will": 2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 6,
          "damage": "1d10+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "on_hit": null,
          "categoria": "perfurante"
        },
        {
          "name": "Garras",
          "atk_bonus": 6,
          "damage": "1d8+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "on_hit": null,
          "categoria": "cortante"
        }
      ],
      "special_abilities": [
        {
          "id": "carapaca_resistente",
          "name": "CarapaÃ§a Resistente",
          "action_type": "passiva",
          "descricao": "Reduz todo dano fÃ­sico em 2"
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
          "descricao": "Atinge todos atrÃ¡s: +5, 1d8+3; falha derruba"
        },
        {
          "id": "cuspir_acido",
          "name": "Cuspir Ãcido",
          "action_type": "acao",
          "cooldown_turns": 3,
          "range": 3,
          "damage": "2d6",
          "save": "reflexos",
          "dc": 13,
          "descricao": "Alvo Ãºnico: 2d6 Ã¡cido, Reflexos metade e corrÃ³i um equipamento"
        },
        {
          "id": "furia_bestial",
          "name": "FÃºria Bestial",
          "action_type": "passiva",
          "descricao": "Mordida e ao menos uma garra acertam: +1d6 dano"
        },
        {
          "id": "ponto_vulneravel",
          "name": "Ponto VulnerÃ¡vel",
          "action_type": "passiva",
          "nd_penalty": 0.25,
          "descricao": "Os dois quadrados centrais ignoram a armadura natural (CA 15 â†’ 10; Destreza permanece) e reduÃ§Ãµes de dano; reduz o ND estimado em 0,25",
          "tiles": [
            [
              1,
              0
            ],
            [
              1,
              1
            ]
          ]
        },
        {
          "id": "corpo_pesado",
          "name": "Corpo Pesado",
          "action_type": "passiva",
          "descricao": "Falha em Reflexos: +1 dano daquele efeito"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "ponto_vulneravel",
          "nd_penalty": 0.25,
          "tiles": [
            [
              1,
              0
            ],
            [
              1,
              1
            ]
          ],
          "descricao": "Ponto VulnerÃ¡vel: os dois quadrados centrais ignoram a armadura natural (CA 15 â†’ 10; Destreza permanece) e reduÃ§Ãµes de dano (â€“0,25 ND estimado)"
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 2
        }
      ],
      "loot_table": {
        "1-100": {
          "tipo": "gold",
          "valor": "2d6"
        }
      },
      "ai_type": "grotao",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "elemental_fogo",
      "name": "Elemental de Fogo",
      "emoji": "ðŸ”¥",
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
          "name": "Corpo EnergÃ©tico",
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
          "name": "ExplosÃ£o Final",
          "action_type": "passiva",
          "damage": "6d6",
          "damage_types": [
            "fire"
          ],
          "radius": 1,
          "save": "reflexos",
          "dc": 13,
          "descricao": "Ao morrer, explode em 1 quadrado: 6d6 de fogo; Reflexos CD 13 reduz Ã  metade."
        },
        {
          "id": "intensidade",
          "name": "Intensidade",
          "action_type": "passiva",
          "descricao": "As chamas ignoram reduÃ§Ãµes leves de dano de fogo (nÃ£o ignora resistÃªncia Ã  metade)."
        }
      ],
      "immunities": [
        "fire"
      ],
      "weaknesses": [
        {
          "type": "cold",
          "multiplier": 1.5,
          "descricao": "Gelo causa 1,5Ã— de dano."
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
      "emoji": "â„ï¸",
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
          "id": "corpo_congelado",
          "name": "Corpo Congelado",
          "action_type": "passiva",
          "descricao": "Ataques fÃ­sicos sofrem â€“1 de dano."
        },
        {
          "id": "congelamento_progressivo",
          "name": "Congelamento Progressivo",
          "action_type": "passiva",
          "descricao": "Ao acertar, reduz o movimento em 1 por 2 turnos; acumula atÃ© â€“3 e renova a duraÃ§Ã£o."
        },
        {
          "id": "nucleo_frio",
          "name": "NÃºcleo Frio",
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
          "descricao": "Fogo causa 1,5Ã— de dano."
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
      "emoji": "ðŸª¨",
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
          "id": "corpo_rochoso",
          "name": "Corpo Rochoso",
          "action_type": "passiva",
          "descricao": "Reduz dano fÃ­sico em 4."
        },
        {
          "id": "impacto_devastador",
          "name": "Impacto Devastador",
          "action_type": "passiva",
          "descricao": "Se nÃ£o se mover no turno, causa +4 de dano."
        },
        {
          "id": "inabalavel",
          "name": "InabalÃ¡vel",
          "action_type": "passiva",
          "descricao": "NÃ£o pode ser imobilizado por redes, cola ou efeitos equivalentes."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "physical",
          "categoria": "contundente",
          "bonus_flat": 2,
          "ignora_reducao": true,
          "descricao": "Dano contundente ignora reduÃ§Ãµes e causa +2 de dano."
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
      "name": "Elemental ElÃ©trico",
      "emoji": "âš¡",
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
          "name": "Corpo EnergÃ©tico",
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
          "name": "Salto ElÃ©trico",
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
          "descricao": "Ãgua (tratada como frio) causa +2 de dano."
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
      "emoji": "ðŸŒªï¸",
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
          "name": "Corpo IntangÃ­vel",
          "action_type": "passiva",
          "descricao": "NÃ£o sofre dano de armas fÃ­sicas."
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
          "name": "TurbilhÃ£o",
          "action_type": "acao",
          "cooldown_turns": 2,
          "damage": "1d8",
          "radius": 1,
          "dc": 13,
          "save": "reflexos",
          "descricao": "Ãrea de 1 quadrado: 1d8; Reflexos CD 13. Falha perde a prÃ³xima aÃ§Ã£o; sucesso perde o movimento."
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
      "name": "Elemental de Ãgua",
      "emoji": "ðŸŒŠ",
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
          "name": "Golpe de Ãgua",
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
          "descricao": "Sofre metade do dano de armas fÃ­sicas."
        },
        {
          "id": "onda_envolvente",
          "name": "Onda Envolvente / Afogar",
          "action_type": "passiva",
          "damage": "1d6",
          "descricao": "Ao acertar, pode prender uma criatura mÃ©dia; presa sofre 1d6 por rodada e testa FOR para escapar."
        },
        {
          "id": "mare_viva",
          "name": "MarÃ© Viva",
          "action_type": "passiva",
          "descricao": "Perto de fonte ou piso de Ã¡gua, recupera 1d6 HP."
        },
        {
          "id": "solidificar_frio",
          "name": "Solidificar",
          "action_type": "passiva",
          "descricao": "Frio em 2 rodadas consecutivas remove a resistÃªncia fÃ­sica por 2 rodadas."
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
      "emoji": "ðŸº",
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
          "name": "Olfato AguÃ§ado",
          "action_type": "passiva",
          "descricao": "Detecta invisÃ­veis e impede ocultaÃ§Ã£o."
        },
        {
          "id": "pele_amaldicoada",
          "name": "Pele AmaldiÃ§oada",
          "action_type": "passiva",
          "descricao": "Armas nÃ£o mÃ¡gicas e sem prata causam metade do dano."
        },
        {
          "id": "regeneracao_lobisomem",
          "name": "RegeneraÃ§Ã£o",
          "action_type": "passiva",
          "descricao": "Recupera 2 HP no inÃ­cio do turno, exceto apÃ³s dano mÃ¡gico ou de prata."
        },
        {
          "id": "furia_bestial_lobisomem",
          "name": "FÃºria Bestial",
          "action_type": "passiva",
          "descricao": "Com 12 HP ou menos: +2 ataque e dano."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "silver",
          "multiplier": 2,
          "descricao": "Prata causa dano dobrado e bloqueia regeneraÃ§Ã£o."
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
      "name": "Escravo VampÃ­rico",
      "emoji": "ðŸ§›",
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
          "name": "ReduÃ§Ã£o de Dano 5",
          "action_type": "passiva",
          "descricao": "Armas comuns sofrem â€“5; prata, magia e magias ignoram."
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
          "name": "RessurreiÃ§Ã£o VampÃ­rica",
          "action_type": "passiva",
          "descricao": "Retorna uma vez apÃ³s 1d4 rodadas, salvo dano sagrado/luz suficiente."
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
      "emoji": "ðŸ§›",
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
          "name": "ReduÃ§Ã£o de Dano 5",
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
          "name": "RessurreiÃ§Ã£o VampÃ­rica",
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
      "name": "Vampiro AnciÃ£o",
      "emoji": "ðŸ§›",
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
          "name": "ReduÃ§Ã£o de Dano 5",
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
          "name": "Encantar em Ãrea",
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
          "name": "RessurreiÃ§Ã£o VampÃ­rica",
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
      "emoji": "ðŸ‘‘ðŸ§›",
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
      "image": "lorde_vampirico",
      "str_": 20,
      "dex": 22,
      "con_": 10,
      "int_": 18,
      "fort": 8,
      "ref_": 10,
      "will": 10,
      "attacks": [
        {
          "name": "Espada Longa MÃ¡gica",
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
          "name": "ReduÃ§Ã£o de Dano 5",
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
          "name": "Encantar Supremo em Ãrea",
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
          "name": "RessurreiÃ§Ã£o VampÃ­rica",
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
      "id": "veneno_ferrao",
      "name": "Veneno do FerrÃ£o",
      "action_type": "passiva",
      "dc": 9,
      "save": "fortitude",
      "effect": "penalidade_ataque_movimento",
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
      "name": "Fraqueza MÃ¡gica",
      "action_type": "passiva",
      "descricao": "-2 em testes contra magias que controlam mortos-vivos",
      "source": "monstro"
    },
    {
      "id": "movimento_erratico",
      "name": "Movimento ErrÃ¡tico",
      "action_type": "passiva",
      "descricao": "Ignora terreno difÃ­cil â€” avanÃ§a sem hesitar",
      "source": "monstro"
    },
    {
      "id": "sem_instinto",
      "name": "Sem Instinto",
      "action_type": "passiva",
      "descricao": "Nunca foge nem recua â€” avanÃ§a atÃ© ser destruÃ­do",
      "source": "monstro"
    },
    {
      "id": "caca_em_bando",
      "name": "CaÃ§a em Bando",
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
      "id": "agarrar",
      "name": "Agarrar",
      "action_type": "passiva",
      "dc": 12,
      "save": "fortitude",
      "descricao": "Ao acertar, alvo testa FOR ou REF CD 12 â€” falha: preso",
      "source": "monstro"
    },
    {
      "id": "atq_mandibula",
      "name": "Ataque de MandÃ­bula",
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
      "id": "constricao",
      "name": "ConstriÃ§Ã£o",
      "action_type": "passiva",
      "dc": 11,
      "save": "fortitude",
      "escape_saves": [
        "fortitude"
      ],
      "descricao": "Ao acertar, alvo testa FOR CD 11 â€” falha: preso",
      "source": "monstro"
    },
    {
      "id": "esmagar",
      "name": "Esmagar",
      "action_type": "passiva",
      "descricao": "Enquanto preso e adjacente: 1d6 dano automÃ¡tico por turno",
      "source": "monstro"
    },
    {
      "id": "veneno",
      "name": "Veneno",
      "action_type": "passiva",
      "descricao": "Ao acertar a mordida, aplica veneno (doenÃ§a leve)",
      "source": "monstro"
    },
    {
      "id": "ataque_rapido",
      "name": "Ataque RÃ¡pido",
      "action_type": "passiva",
      "descricao": "Se nÃ£o se mover no turno: +1 no ataque",
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
      "descricao": "Ao acertar: +1 nÃ­vel de dano em equipamento orgÃ¢nico do alvo (couro/madeira/tecido)",
      "source": "monstro"
    },
    {
      "id": "corrosao_viva",
      "name": "CorrosÃ£o Viva",
      "action_type": "passiva",
      "descricao": "Alvo sem armadura: 1 dano/turno por 2 turnos (acumula a cada acerto)",
      "source": "monstro"
    },
    {
      "id": "absorver_materia",
      "name": "Absorver MatÃ©ria",
      "action_type": "passiva",
      "descricao": "Quando destrÃ³i um item orgÃ¢nico: recupera 1d4 HP",
      "source": "monstro"
    },
    {
      "id": "furia",
      "name": "FÃºria",
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
      "name": "FÃºria Cega",
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
      "descricao": "Arremesso 1d4+2 (alcance 3) como aÃ§Ã£o bÃ´nus; 1 natural quebra a arma",
      "source": "monstro"
    },
    {
      "id": "silencio",
      "name": "SilÃªncio",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 2,
      "descricao": "Cria Ã¡rea de SilÃªncio (some se o xamÃ£ morrer)",
      "source": "monstro"
    },
    {
      "id": "amaldicoar",
      "name": "AmaldiÃ§oar",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "descricao": "Debuff -1 em ataque/dano/CA/resistÃªncia nos herÃ³is",
      "source": "monstro"
    },
    {
      "id": "abencoar",
      "name": "AbenÃ§oar",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "descricao": "Buff +1 em ataque/dano/CA/resistÃªncia nos goblins aliados",
      "source": "monstro"
    },
    {
      "id": "concentracao_fragil",
      "name": "ConcentraÃ§Ã£o FrÃ¡gil",
      "action_type": "passiva",
      "descricao": "Se sofrer dano, nÃ£o pode usar magia no prÃ³ximo turno",
      "source": "monstro"
    },
    {
      "id": "veneno_lanca",
      "name": "LanÃ§a Envenenada",
      "action_type": "acao_livre",
      "dc": 8,
      "save": "fortitude",
      "effect": "veneno_aranha_sombria",
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
      "action_type": "passiva",
      "descricao": "Inicia com 2 esqueletos; mortos-vivos prÃ³ximos recebem +1 em Vontade",
      "source": "monstro"
    },
    {
      "id": "concentracao_sombria",
      "name": "ConcentraÃ§Ã£o Sombria",
      "action_type": "passiva",
      "descricao": "Ao sofrer dano: Vontade CD 10 ou perde a aÃ§Ã£o de magia no turno",
      "source": "monstro"
    },
    {
      "id": "essencia_profana",
      "name": "EssÃªncia Profana",
      "action_type": "passiva",
      "descricao": "Sofre dano dobrado de efeitos sagrados/luz",
      "source": "monstro"
    },
    {
      "id": "resistencia_morta",
      "name": "ResistÃªncia Morta",
      "action_type": "passiva",
      "dc": 10,
      "save": "fortitude",
      "descricao": "A 0 HP: Fortitude CD 10 â†’ fica com 1 HP (dano sagrado/luz ignora e destrÃ³i de vez)",
      "source": "monstro"
    },
    {
      "id": "infeccao",
      "name": "InfecÃ§Ã£o",
      "action_type": "passiva",
      "dc": 10,
      "save": "fortitude",
      "descricao": "Ao acertar: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve",
      "source": "monstro"
    },
    {
      "id": "lento_incansavel",
      "name": "Lento e IncansÃ¡vel",
      "action_type": "passiva",
      "descricao": "NÃ£o corre nem foge â€” avanÃ§a sem parar",
      "source": "monstro"
    },
    {
      "id": "corpo_morto",
      "name": "Corpo Morto",
      "action_type": "passiva",
      "descricao": "NÃ£o come, bebe nem respira",
      "source": "monstro"
    },
    {
      "id": "combo_devorador",
      "name": "Combo Devorador",
      "action_type": "passiva",
      "descricao": "Se as 2 mordidas acertarem no turno: 2 ataques de Garra imediatos",
      "source": "monstro"
    },
    {
      "id": "predador_oportunista",
      "name": "Predador Oportunista",
      "action_type": "passiva",
      "descricao": "+1 nas mordidas contra alvos com menos de 50% do HP",
      "source": "monstro"
    },
    {
      "id": "faro_carnica",
      "name": "Faro de CarniÃ§a",
      "action_type": "passiva",
      "descricao": "Prioriza sempre o alvo com menor HP",
      "source": "monstro"
    },
    {
      "id": "duas_cabecas",
      "name": "Duas CabeÃ§as",
      "action_type": "passiva",
      "descricao": "+1 em percepÃ§Ã£o; difÃ­cil de surpreender (flavor)",
      "source": "monstro"
    },
    {
      "id": "mordida_corrosiva",
      "name": "Mordida Corrosiva",
      "action_type": "passiva",
      "descricao": "Ao acertar: +1 nÃ­vel de dano na arma OU armadura metÃ¡lica do alvo",
      "source": "monstro"
    },
    {
      "id": "devorar_metal",
      "name": "Devorar Metal",
      "action_type": "passiva",
      "descricao": "Item a 3 nÃ­veis Ã© destruÃ­do e o Devorador recupera 1d6 HP",
      "source": "monstro"
    },
    {
      "id": "alimentacao_metalica",
      "name": "AlimentaÃ§Ã£o MetÃ¡lica",
      "action_type": "passiva",
      "descricao": "Gasta a aÃ§Ã£o para consumir item metÃ¡lico no chÃ£o e recuperar 1d6 HP",
      "source": "monstro"
    },
    {
      "id": "manto_escuridao",
      "name": "Manto de EscuridÃ£o",
      "action_type": "magia",
      "uses_per_combat": 1,
      "circulo": 1,
      "descricao": "Cria uma Ã¡rea de escuridÃ£o centrada em si (1x por combate)",
      "source": "monstro"
    },
    {
      "id": "ataque_das_sombras",
      "name": "Ataque das Sombras",
      "action_type": "passiva",
      "descricao": "Se o alvo nÃ£o o enxerga (bugbear oculto OU alvo na escuridÃ£o sem visÃ£o no escuro): +2 ataque e +1d6 de dano em TODOS os ataques",
      "source": "monstro"
    },
    {
      "id": "cacador_das_trevas",
      "name": "CaÃ§ador das Trevas",
      "action_type": "passiva",
      "descricao": "Em Ã¡rea escura: +2 CA, +1 ataque e sempre pode usar Ataque das Sombras",
      "source": "monstro"
    },
    {
      "id": "desaparecer_nas_sombras",
      "name": "Desaparecer nas Sombras",
      "action_type": "acao_livre",
      "cooldown_turns": 5,
      "descricao": "SÃ³ na escuridÃ£o (apÃ³s Manto): fica oculto (imune a ataques Ã  distÃ¢ncia; corpo a corpo -4), move atÃ© 3, atÃ© o inÃ­cio do prÃ³ximo turno",
      "source": "monstro"
    },
    {
      "id": "visao_perfeita_escuro",
      "name": "VisÃ£o no Escuro",
      "action_type": "passiva",
      "descricao": "Enxerga perfeitamente no escuro â€” nÃ£o sofre penalidades nas trevas",
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
      "name": "ForÃ§a Descomunal",
      "action_type": "ataque",
      "cooldown_turns": 4,
      "save": "fortitude",
      "dc": 10,
      "descricao": "Ataque normal; se acertar, Fortitude CD 10 ou atordoado (perde a prÃ³xima rodada). Recarga 4 rodadas",
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
      "name": "Lento e PrevisÃ­vel",
      "action_type": "passiva",
      "descricao": "Se errar um ataque: -2 de CA atÃ© o prÃ³ximo turno",
      "source": "monstro"
    },
    {
      "id": "carapaca_resistente",
      "name": "CarapaÃ§a Resistente",
      "action_type": "passiva",
      "descricao": "Reduz todo dano fÃ­sico em 2",
      "source": "monstro"
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
      "descricao": "Atinge todos atrÃ¡s: +5, 1d8+3; falha derruba",
      "source": "monstro"
    },
    {
      "id": "cuspir_acido",
      "name": "Cuspir Ãcido",
      "action_type": "acao",
      "cooldown_turns": 3,
      "range": 3,
      "damage": "2d6",
      "save": "reflexos",
      "dc": 13,
      "descricao": "Alvo Ãºnico: 2d6 Ã¡cido, Reflexos metade e corrÃ³i um equipamento",
      "source": "monstro"
    },
    {
      "id": "furia_bestial",
      "name": "FÃºria Bestial",
      "action_type": "passiva",
      "descricao": "Mordida e ao menos uma garra acertam: +1d6 dano",
      "source": "monstro"
    },
    {
      "id": "ponto_vulneravel",
      "name": "Ponto VulnerÃ¡vel",
      "action_type": "passiva",
      "nd_penalty": 0.25,
      "descricao": "Os dois quadrados centrais ignoram a armadura natural (CA 15 â†’ 10; Destreza permanece) e reduÃ§Ãµes de dano; reduz o ND estimado em 0,25",
      "tiles": [
        [
          1,
          0
        ],
        [
          1,
          1
        ]
      ],
      "source": "monstro"
    },
    {
      "id": "corpo_pesado",
      "name": "Corpo Pesado",
      "action_type": "passiva",
      "descricao": "Falha em Reflexos: +1 dano daquele efeito",
      "source": "monstro"
    },
    {
      "id": "corpo_energetico",
      "name": "Corpo EnergÃ©tico",
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
      "name": "ExplosÃ£o Final",
      "action_type": "passiva",
      "damage": "6d6",
      "damage_types": [
        "fire"
      ],
      "radius": 1,
      "save": "reflexos",
      "dc": 13,
      "descricao": "Ao morrer, explode em 1 quadrado: 6d6 de fogo; Reflexos CD 13 reduz Ã  metade.",
      "source": "monstro"
    },
    {
      "id": "intensidade",
      "name": "Intensidade",
      "action_type": "passiva",
      "descricao": "As chamas ignoram reduÃ§Ãµes leves de dano de fogo (nÃ£o ignora resistÃªncia Ã  metade).",
      "source": "monstro"
    },
    {
      "id": "corpo_congelado",
      "name": "Corpo Congelado",
      "action_type": "passiva",
      "descricao": "Ataques fÃ­sicos sofrem â€“1 de dano.",
      "source": "monstro"
    },
    {
      "id": "congelamento_progressivo",
      "name": "Congelamento Progressivo",
      "action_type": "passiva",
      "descricao": "Ao acertar, reduz o movimento em 1 por 2 turnos; acumula atÃ© â€“3 e renova a duraÃ§Ã£o.",
      "source": "monstro"
    },
    {
      "id": "nucleo_frio",
      "name": "NÃºcleo Frio",
      "action_type": "passiva",
      "descricao": "Reduz em 2 todo dano recebido, exceto fogo.",
      "source": "monstro"
    },
    {
      "id": "corpo_rochoso",
      "name": "Corpo Rochoso",
      "action_type": "passiva",
      "descricao": "Reduz dano fÃ­sico em 4.",
      "source": "monstro"
    },
    {
      "id": "impacto_devastador",
      "name": "Impacto Devastador",
      "action_type": "passiva",
      "descricao": "Se nÃ£o se mover no turno, causa +4 de dano.",
      "source": "monstro"
    },
    {
      "id": "inabalavel",
      "name": "InabalÃ¡vel",
      "action_type": "passiva",
      "descricao": "NÃ£o pode ser imobilizado por redes, cola ou efeitos equivalentes.",
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
      "name": "Salto ElÃ©trico",
      "action_type": "passiva",
      "descricao": "Ignora a CA concedida por armaduras de metal.",
      "source": "monstro"
    },
    {
      "id": "corpo_intangivel",
      "name": "Corpo IntangÃ­vel",
      "action_type": "passiva",
      "descricao": "NÃ£o sofre dano de armas fÃ­sicas.",
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
      "name": "TurbilhÃ£o",
      "action_type": "acao",
      "cooldown_turns": 2,
      "damage": "1d8",
      "radius": 1,
      "dc": 13,
      "save": "reflexos",
      "descricao": "Ãrea de 1 quadrado: 1d8; Reflexos CD 13. Falha perde a prÃ³xima aÃ§Ã£o; sucesso perde o movimento.",
      "source": "monstro"
    },
    {
      "id": "corpo_fluido",
      "name": "Corpo Fluido",
      "action_type": "passiva",
      "descricao": "Sofre metade do dano de armas fÃ­sicas.",
      "source": "monstro"
    },
    {
      "id": "onda_envolvente",
      "name": "Onda Envolvente / Afogar",
      "action_type": "passiva",
      "damage": "1d6",
      "descricao": "Ao acertar, pode prender uma criatura mÃ©dia; presa sofre 1d6 por rodada e testa FOR para escapar.",
      "source": "monstro"
    },
    {
      "id": "mare_viva",
      "name": "MarÃ© Viva",
      "action_type": "passiva",
      "descricao": "Perto de fonte ou piso de Ã¡gua, recupera 1d6 HP.",
      "source": "monstro"
    },
    {
      "id": "solidificar_frio",
      "name": "Solidificar",
      "action_type": "passiva",
      "descricao": "Frio em 2 rodadas consecutivas remove a resistÃªncia fÃ­sica por 2 rodadas.",
      "source": "monstro"
    },
    {
      "id": "olfato_agucado",
      "name": "Olfato AguÃ§ado",
      "action_type": "passiva",
      "descricao": "Detecta invisÃ­veis e impede ocultaÃ§Ã£o.",
      "source": "monstro"
    },
    {
      "id": "pele_amaldicoada",
      "name": "Pele AmaldiÃ§oada",
      "action_type": "passiva",
      "descricao": "Armas nÃ£o mÃ¡gicas e sem prata causam metade do dano.",
      "source": "monstro"
    },
    {
      "id": "regeneracao_lobisomem",
      "name": "RegeneraÃ§Ã£o",
      "action_type": "passiva",
      "descricao": "Recupera 2 HP no inÃ­cio do turno, exceto apÃ³s dano mÃ¡gico ou de prata.",
      "source": "monstro"
    },
    {
      "id": "furia_bestial_lobisomem",
      "name": "FÃºria Bestial",
      "action_type": "passiva",
      "descricao": "Com 12 HP ou menos: +2 ataque e dano.",
      "source": "monstro"
    },
    {
      "id": "reducao_vampirica",
      "name": "ReduÃ§Ã£o de Dano 5",
      "action_type": "passiva",
      "descricao": "Armas comuns sofrem â€“5; prata, magia e magias ignoram.",
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
      "name": "RessurreiÃ§Ã£o VampÃ­rica",
      "action_type": "passiva",
      "descricao": "Retorna uma vez apÃ³s 1d4 rodadas, salvo dano sagrado/luz suficiente.",
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
      "name": "Encantar em Ãrea",
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
      "name": "Encantar Supremo em Ãrea",
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
      "icon": "âš”ï¸",
      "descricao": "+2 no dado de acerto neste turno",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_warrior_golpe_devastador",
      "source": "heroi",
      "source_id": "golpe_devastador",
      "source_class": "warrior",
      "name": "Golpe Devastador",
      "icon": "ðŸ’¥",
      "descricao": "Dobra cada dado de dano neste turno",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_warrior_furia_berserker",
      "source": "heroi",
      "source_id": "furia_berserker",
      "source_class": "warrior",
      "name": "FÃºria Berserker",
      "icon": "ðŸ”¥",
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
      "icon": "ðŸŽ¯",
      "descricao": "AÃ§Ã£o livre. +1 na dificuldade (CD) do teste de resistÃªncia da magia. ðŸ–-3 ao lanÃ§ar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_mage_estender_magia",
      "source": "heroi",
      "source_id": "estender_magia",
      "source_class": "mage",
      "name": "Estender Magia",
      "icon": "â±ï¸",
      "descricao": "AÃ§Ã£o livre. +1 turno na duraÃ§Ã£o da magia. ðŸ–-3 ðŸ’§-3 ao lanÃ§ar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_mage_fortalecer_magia",
      "source": "heroi",
      "source_id": "fortalecer_magia",
      "source_class": "mage",
      "name": "Fortalecer Magia",
      "icon": "ðŸ’¥",
      "descricao": "AÃ§Ã£o livre. Multiplica o dano da magia por 1,5. ðŸ–-6 ðŸ’§-6 ao lanÃ§ar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_ataque_furtivo",
      "source": "heroi",
      "source_id": "ataque_furtivo",
      "source_class": "rogue",
      "name": "Ataque Furtivo",
      "icon": "ðŸ—¡ï¸",
      "descricao": "Passiva. +2d4 dano extra quando hÃ¡ aliado adjacente ao alvo (ou se estiver invisÃ­vel). +1d4 por faixa de nÃ­vel.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate"
    },
    {
      "id": "hero_rogue_detectar_armadilhas",
      "source": "heroi",
      "source_id": "detectar_armadilhas",
      "source_class": "rogue",
      "name": "Detectar Armadilhas",
      "icon": "ðŸ”",
      "descricao": "AÃ§Ã£o bÃ´nus (alternÃ¡vel). Revela armadilhas prÃ³ximas e nÃ£o dispara as da masmorra. ManutenÃ§Ã£o ðŸ’§-1/turno.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_esconder_sombras",
      "source": "heroi",
      "source_id": "esconder_sombras",
      "source_class": "rogue",
      "name": "Esconder nas Sombras",
      "icon": "ðŸŒ‘",
      "descricao": "AÃ§Ã£o bÃ´nus. d20+DES vs percepÃ§Ã£o dos monstros. InvisÃ­vel (nÃ£o Ã© alvo) enquanto ativo. ManutenÃ§Ã£o ðŸ–-1 ðŸ’§-1/turno.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_veneno_rapido",
      "source": "heroi",
      "source_id": "veneno_rapido",
      "source_class": "rogue",
      "name": "Veneno RÃ¡pido",
      "icon": "â˜ ï¸",
      "descricao": "AÃ§Ã£o livre. Unta um veneno da bolsa na arma â€” os prÃ³ximos golpes certeiros envenenam o alvo.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_rogue_criar_armadilha",
      "source": "heroi",
      "source_id": "criar_armadilha",
      "source_class": "rogue",
      "name": "Criar Armadilha",
      "icon": "ðŸª¤",
      "descricao": "AÃ§Ã£o principal. Coloca uma armadilha na prÃ³pria casa ou adjacente. Custa fome/sede + ouro.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_cura",
      "source": "heroi",
      "source_id": "cura",
      "source_class": "cleric",
      "name": "Cura",
      "icon": "ðŸ™Œ",
      "descricao": "1d8 a 3d8 + INT em um aliado. ðŸ’§-1 por dado. Alcance estendÃ­vel com ðŸ–.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_cura_area",
      "source": "heroi",
      "source_id": "cura_area",
      "source_class": "cleric",
      "name": "Cura em Ãrea",
      "icon": "ðŸŒŸ",
      "descricao": "1d8 a 3d8 + INT em todos os aliados no raio 5. ðŸ–-4 ðŸ’§-4 por dado.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_purificacao",
      "source": "heroi",
      "source_id": "purificacao",
      "source_class": "cleric",
      "name": "PurificaÃ§Ã£o",
      "icon": "âœ¨",
      "descricao": "Remove veneno, doenÃ§a, maldiÃ§Ã£o ou petrificaÃ§Ã£o de um aliado adjacente.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_cleric_ressurreicao",
      "source": "heroi",
      "source_id": "ressurreicao",
      "source_class": "cleric",
      "name": "RessurreiÃ§Ã£o",
      "icon": "ðŸ’«",
      "descricao": "Traz um aliado morto adjacente de volta com 1 HP. ðŸ–-10 ðŸ’§-10.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_bard_cancao_heroica",
      "source": "heroi",
      "source_id": "cancao_heroica",
      "source_class": "bard",
      "name": "CanÃ§Ã£o Heroica",
      "icon": "ðŸŽµ",
      "descricao": "Ativa buffs musicais para aliados em raio de 5 quadrados",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_bard_provocacao",
      "source": "heroi",
      "source_id": "provocacao",
      "source_class": "bard",
      "name": "ProvocaÃ§Ã£o",
      "icon": "ðŸ˜¤",
      "descricao": "ImpÃµe desvantagem ao inimigo e o forÃ§a a atacar Henrique por 3 turnos",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_imposicao_maos",
      "source": "heroi",
      "source_id": "imposicao_maos",
      "source_class": "paladin",
      "name": "ImposiÃ§Ã£o das MÃ£os",
      "icon": "ðŸ™",
      "descricao": "Cura 1d6 + bÃ´nus ForÃ§a em aliado adjacente",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_golpe_sagrado",
      "source": "heroi",
      "source_id": "golpe_sagrado",
      "source_class": "paladin",
      "name": "Golpe Sagrado",
      "icon": "âš”ï¸",
      "descricao": "+1d8 dano sagrado. Dobrado contra mortos-vivos e demÃ´nios",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_protetor",
      "source": "heroi",
      "source_id": "protetor",
      "source_class": "paladin",
      "name": "Protetor",
      "icon": "ðŸ›¡ï¸",
      "descricao": "Aliado recebe metade do dano. A outra metade vai para Richard",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_regeneracao_divina",
      "source": "heroi",
      "source_id": "regeneracao_divina",
      "source_class": "paladin",
      "name": "RegeneraÃ§Ã£o Divina",
      "icon": "âœ¨",
      "descricao": "Recupera 1 HP por turno atÃ© HP mÃ¡ximo",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "hero_paladin_guerreiro_luz",
      "source": "heroi",
      "source_id": "guerreiro_luz",
      "source_class": "paladin",
      "name": "Guerreiro da Luz",
      "icon": "ðŸ’¡",
      "descricao": "+1/+2 em VisÃ£o, Ataque, Dano e CA. Apenas Richard",
      "action_type": "acao",
      "monster_effect": "vantagem_combate"
    },
    {
      "id": "guild_brutalidade",
      "source": "guilda",
      "source_id": "brutalidade",
      "name": "Brutalidade",
      "icon": "âœ¦",
      "descricao": "AtÃ© o fim do turno, ataques fÃ­sicos com arma causam +2 de dano.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_mira_perfeita",
      "source": "guilda",
      "source_id": "tecnica_mira_perfeita",
      "name": "Mira Perfeita",
      "icon": "âœ¦",
      "descricao": "PrÃ³ximo ataque Ã  distÃ¢ncia recebe vantagem; se acertar, +2 de dano.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_espirito_indomavel",
      "source": "guilda",
      "source_id": "tecnica_espirito_indomavel",
      "name": "EspÃ­rito IndomÃ¡vel",
      "icon": "âœ¦",
      "descricao": "AÃ§Ã£o livre. Remove Medo, Atordoamento e LentidÃ£o; 1 rodada imune a SilÃªncio.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_grito_guerra",
      "source": "guilda",
      "source_id": "tecnica_grito_guerra",
      "name": "Grito de Guerra",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "O seu movimento Ã© dobrado nesta rodada.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_investida",
      "source": "guilda",
      "source_id": "tecnica_investida",
      "name": "Investida Heroica",
      "icon": "âœ¦",
      "descricao": "Dobra o movimento; se andar â‰¥2 casas em linha reta, o prÃ³ximo ataque corpo a corpo tem vantagem +2 dano.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_defesa_impecavel",
      "source": "guilda",
      "source_id": "tecnica_defesa_impecavel",
      "name": "Defesa ImpecÃ¡vel",
      "icon": "âœ¦",
      "descricao": "AtÃ© o prÃ³ximo turno, ataques contra vocÃª tÃªm desvantagem e vocÃª fica imune a Ataque Furtivo.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_pressao_constante",
      "source": "guilda",
      "source_id": "tecnica_pressao_constante",
      "name": "PressÃ£o Constante",
      "icon": "âœ¦",
      "descricao": "Um inimigo adjacente sofre -2 de CA por 2 rodadas.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_tatica_defensiva",
      "source": "guilda",
      "source_id": "tecnica_tatica_defensiva",
      "name": "TÃ¡tica Defensiva",
      "icon": "âœ¦",
      "descricao": "Escolha um aliado em atÃ© 4 casas; por 1d4 rodadas, metade do dano dele Ã© transferida a vocÃª.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_passo_fantasma",
      "source": "guilda",
      "source_id": "tecnica_passo_fantasma",
      "name": "Passo Fantasma",
      "icon": "âœ¦",
      "descricao": "Por 1d4 rodadas: +2 de movimento e vocÃª atravessa casas ocupadas por objetos (nÃ£o paredes nem criaturas).",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_ataque_coordenado",
      "source": "guilda",
      "source_id": "tecnica_ataque_coordenado",
      "name": "Ataque Coordenado",
      "icon": "âœ¦",
      "descricao": "Escolha um aliado; neste turno, quando vocÃª atacar um inimigo, o aliado tambÃ©m o ataca.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_sangue_frio",
      "source": "guilda",
      "source_id": "tecnica_sangue_frio",
      "name": "Sangue Frio",
      "icon": "âœ¦",
      "descricao": "A primeira vez que errar um ataque, vocÃª pode rolÃ¡-lo novamente.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_resistencia_absoluta",
      "source": "guilda",
      "source_id": "tecnica_resistencia_absoluta",
      "name": "ResistÃªncia Absoluta",
      "icon": "âœ¦",
      "descricao": "Recebe +2 em todos os testes de resistÃªncia por 2 rodadas.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_contra_ataque",
      "source": "guilda",
      "source_id": "tecnica_contra_ataque",
      "name": "Contra-Ataque",
      "icon": "âœ¦",
      "descricao": "AtÃ© o prÃ³ximo turno, quando um inimigo errar vocÃª (arma corpo a corpo/alcance ou besta de mÃ£o, e ele no alcance), vocÃª o ataca de volta.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_oportunidade",
      "source": "guilda",
      "source_id": "tecnica_oportunidade",
      "name": "Oportunidade",
      "icon": "âœ¦",
      "descricao": "Escolha um aliado (nÃ£o pode ser vocÃª); no PRÃ“PRIO turno dele, ganha uma aÃ§Ã£o extra â€” mover mais, atacar de novo, usar a habilidade de classe de novo, ou lanÃ§ar mais uma magia. Expira no fim desta rodada se nÃ£o for usada.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_instinto_sobrevivencia",
      "source": "guilda",
      "source_id": "tecnica_instinto_sobrevivencia",
      "name": "Instinto de SobrevivÃªncia",
      "icon": "âœ¦",
      "descricao": "AutomÃ¡tica. Se um dano zeraria seu HP, vocÃª fica com 1 em vez de morrer. Depois disso, entra em recarga.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_ultimo_esforco",
      "source": "guilda",
      "source_id": "tecnica_ultimo_esforco",
      "name": "Ãšltimo EsforÃ§o",
      "icon": "âœ¦",
      "descricao": "AutomÃ¡tica. Se um dano zeraria seu HP, vocÃª fica com 1 e ganha 2 turnos seguidos: todo ataque tem vantagem e todo acerto Ã© crÃ­tico (nat20 â†’ dano TRIPLICADO). NÃ£o pode se curar. Ao final, cai como se tivesse morrido normalmente (pode ser reerguido por RessurreiÃ§Ã£o).",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_golpe_decisivo",
      "source": "guilda",
      "source_id": "tecnica_golpe_decisivo",
      "name": "Golpe Decisivo",
      "icon": "âœ¦",
      "descricao": "Arma o prÃ³ximo ataque bÃ¡sico (corpo a corpo ou Ã  distÃ¢ncia): se acertar, Ã© crÃ­tico automÃ¡tico (dano dobrado); num natural 20 enquanto armado, o dano Ã© TRIPLICADO. Consumida no prÃ³ximo ataque, acerte ou erre.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_tecnica_sorte",
      "source": "guilda",
      "source_id": "tecnica_sorte",
      "name": "Sorte",
      "icon": "âœ¦",
      "descricao": "Depois de errar um ataque, vocÃª pode gastar esta tÃ©cnica para rolÃ¡-lo novamente contra o mesmo alvo. Independente do Sangue Frio.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_category": "tecnica"
    },
    {
      "id": "guild_guerreiro_combinar_2",
      "source": "guilda",
      "source_id": "guerreiro_combinar_2",
      "name": "Combinar Duas",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "Permite armar as TRÃŠS habilidades no mesmo turno.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_mira_3",
      "source": "guilda",
      "source_id": "guerreiro_mira_3",
      "name": "Mira Certeira III",
      "icon": "âœ¦",
      "descricao": "Mira Certeira tambÃ©m concede +2 de dano (alÃ©m do +2 de acerto).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_golpe_3",
      "source": "guilda",
      "source_id": "guerreiro_golpe_3",
      "name": "Golpe Devastador III",
      "icon": "âœ¦",
      "descricao": "Golpe Devastador passa a multiplicar os dados de dano por 2 (era Ã—1,5).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_guerreiro_furia_3",
      "source": "guilda",
      "source_id": "guerreiro_furia_3",
      "name": "FÃºria Berserker III",
      "icon": "âœ¦",
      "descricao": "FÃºria Berserker concede 2 ataques extras (3 ataques no total).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_acerto",
      "source": "guilda",
      "source_id": "bardo_cancao_acerto",
      "name": "CanÃ§Ã£o: Acerto +1",
      "icon": "âœ¦",
      "descricao": "O bÃ´nus de Acerto da CanÃ§Ã£o Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_dano",
      "source": "guilda",
      "source_id": "bardo_cancao_dano",
      "name": "CanÃ§Ã£o: Dano +1",
      "icon": "âœ¦",
      "descricao": "O bÃ´nus de Dano da CanÃ§Ã£o Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_ca",
      "source": "guilda",
      "source_id": "bardo_cancao_ca",
      "name": "CanÃ§Ã£o: Armadura +1",
      "icon": "âœ¦",
      "descricao": "O bÃ´nus de Armadura da CanÃ§Ã£o Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_movimento",
      "source": "guilda",
      "source_id": "bardo_cancao_movimento",
      "name": "CanÃ§Ã£o: Movimento +1",
      "icon": "âœ¦",
      "descricao": "O bÃ´nus de Movimento da CanÃ§Ã£o Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_resistencia",
      "source": "guilda",
      "source_id": "bardo_cancao_resistencia",
      "name": "CanÃ§Ã£o: ResistÃªncia +1",
      "icon": "âœ¦",
      "descricao": "O bÃ´nus de ResistÃªncia da CanÃ§Ã£o Heroica sobe de +1 para +2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_cancao_suprema",
      "source": "guilda",
      "source_id": "bardo_cancao_suprema",
      "name": "CanÃ§Ã£o Heroica Suprema",
      "icon": "âœ¦",
      "descricao": "A manutenÃ§Ã£o da CanÃ§Ã£o Heroica custa -1ðŸ– e -1ðŸ’§ (mÃ­nimo 0).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_provocacao_2",
      "source": "guilda",
      "source_id": "bardo_provocacao_2",
      "name": "ProvocaÃ§Ã£o II",
      "icon": "âœ¦",
      "descricao": "A desvantagem dura toda a provocaÃ§Ã£o; Henrique ganha +2 CA e ataca o alvo com vantagem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_bardo_provocacao_3",
      "source": "guilda",
      "source_id": "bardo_provocacao_3",
      "name": "ProvocaÃ§Ã£o III",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "Todos os bÃ´nus de Lenda passam a beneficiar o grupo inteiro (enquanto Henrique vivo).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_tecelagem_2",
      "source": "guilda",
      "source_id": "mago_tecelagem_2",
      "name": "Tecelagem Arcana II",
      "icon": "âœ¦",
      "descricao": "Permite empilhar 2 metamagias no mesmo lanÃ§amento.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_tecelagem_3",
      "source": "guilda",
      "source_id": "mago_tecelagem_3",
      "name": "Tecelagem Arcana III",
      "icon": "âœ¦",
      "descricao": "Permite empilhar as 3 metamagias no mesmo lanÃ§amento.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_fortalecer_2",
      "source": "guilda",
      "source_id": "mago_fortalecer_2",
      "name": "Fortalecer II",
      "icon": "âœ¦",
      "descricao": "Fortalecer Magia multiplica o dano por 1,5 (era Ã—1,25).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_fortalecer_3",
      "source": "guilda",
      "source_id": "mago_fortalecer_3",
      "name": "Fortalecer III",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "Aprimorar Magia dÃ¡ +2 na CD do save (era +1).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_aprimorar_3",
      "source": "guilda",
      "source_id": "mago_aprimorar_3",
      "name": "Aprimorar III",
      "icon": "âœ¦",
      "descricao": "Aprimorar Magia dÃ¡ +3 na CD do save.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_estender_2",
      "source": "guilda",
      "source_id": "mago_estender_2",
      "name": "Estender II",
      "icon": "âœ¦",
      "descricao": "Estender Magia dÃ¡ +2 rodadas de duraÃ§Ã£o (era +1).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_estender_3",
      "source": "guilda",
      "source_id": "mago_estender_3",
      "name": "Estender III",
      "icon": "âœ¦",
      "descricao": "Estender Magia dÃ¡ +3 rodadas de duraÃ§Ã£o.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_reviver_2",
      "source": "guilda",
      "source_id": "mago_reviver_2",
      "name": "Reviver os Mortos II",
      "icon": "âœ¦",
      "descricao": "Criaturas passam a ocupar Slots de Controle iguais ao ND (fracionÃ¡rio incluso). Chance de sucesso: 100% âˆ’ NDÃ—15%.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_mago_reviver_3",
      "source": "guilda",
      "source_id": "mago_reviver_3",
      "name": "Reviver os Mortos III",
      "icon": "âœ¦",
      "descricao": "+2 Slots de Controle. Chance de sucesso: 100% âˆ’ NDÃ—10%.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_cura_2",
      "source": "guilda",
      "source_id": "clerigo_cura_2",
      "name": "Cura II",
      "icon": "âœ¦",
      "descricao": "Cura pode usar atÃ© 2d8 + INT.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_cura_3",
      "source": "guilda",
      "source_id": "clerigo_cura_3",
      "name": "Cura III",
      "icon": "âœ¦",
      "descricao": "Cura pode usar atÃ© 3d8 + INT.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_massa_2",
      "source": "guilda",
      "source_id": "clerigo_massa_2",
      "name": "Cura em Massa II",
      "icon": "âœ¦",
      "descricao": "Cura em Massa: atÃ© 2d8 + INT, raio 4.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_massa_3",
      "source": "guilda",
      "source_id": "clerigo_massa_3",
      "name": "Cura em Massa III",
      "icon": "âœ¦",
      "descricao": "Cura em Massa: atÃ© 3d8 + INT, raio 6.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_purif_2",
      "source": "guilda",
      "source_id": "clerigo_purif_2",
      "name": "PurificaÃ§Ã£o II",
      "icon": "âœ¦",
      "descricao": "PurificaÃ§Ã£o tambÃ©m remove doenÃ§as.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_purif_3",
      "source": "guilda",
      "source_id": "clerigo_purif_3",
      "name": "PurificaÃ§Ã£o III",
      "icon": "âœ¦",
      "descricao": "PurificaÃ§Ã£o tambÃ©m remove maldiÃ§Ãµes e petrificaÃ§Ã£o.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_ressur_2",
      "source": "guilda",
      "source_id": "clerigo_ressur_2",
      "name": "RessurreiÃ§Ã£o II",
      "icon": "âœ¦",
      "descricao": "RessurreiÃ§Ã£o traz o aliado com metade dos PV (ðŸ–15 ðŸ’§15).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_clerigo_ressur_3",
      "source": "guilda",
      "source_id": "clerigo_ressur_3",
      "name": "RessurreiÃ§Ã£o III",
      "icon": "âœ¦",
      "descricao": "RessurreiÃ§Ã£o traz o aliado com PV cheio (ðŸ–20 ðŸ’§20).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_cura_maos_2",
      "source": "guilda",
      "source_id": "paladino_cura_maos_2",
      "name": "Cura pelas MÃ£os II",
      "icon": "âœ¦",
      "descricao": "ImposiÃ§Ã£o das MÃ£os cura 2d6 + FOR.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_cura_maos_3",
      "source": "guilda",
      "source_id": "paladino_cura_maos_3",
      "name": "Cura pelas MÃ£os III",
      "icon": "âœ¦",
      "descricao": "Pode gastar +2ðŸ–/+2ðŸ’§ por +1d6 de cura (atÃ© 3Ã—).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_ataque_sagrado_2",
      "source": "guilda",
      "source_id": "paladino_ataque_sagrado_2",
      "name": "Ataque Sagrado II",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "MantÃ©m 3 atributos ativos; com VisÃ£o, detecta armadilhas em raio 2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_luz_3",
      "source": "guilda",
      "source_id": "paladino_luz_3",
      "name": "Guerreiro da Luz III",
      "icon": "âœ¦",
      "descricao": "MantÃ©m 4 atributos ativos; com VisÃ£o, detecta armadilhas em raio 3.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_defensor_2",
      "source": "guilda",
      "source_id": "paladino_defensor_2",
      "name": "Defensor II",
      "icon": "âœ¦",
      "descricao": "O alcance da proteÃ§Ã£o aumenta para 5 quadrados.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_defensor_3",
      "source": "guilda",
      "source_id": "paladino_defensor_3",
      "name": "Defensor III",
      "icon": "âœ¦",
      "descricao": "O dano dividido cai para 40%/40% (20% Ã© mitigado).",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_regen_2",
      "source": "guilda",
      "source_id": "paladino_regen_2",
      "name": "RegeneraÃ§Ã£o II",
      "icon": "âœ¦",
      "descricao": "RegeneraÃ§Ã£o Divina tambÃ©m cura +1 HP dos aliados adjacentes.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_paladino_regen_3",
      "source": "guilda",
      "source_id": "paladino_regen_3",
      "name": "RegeneraÃ§Ã£o III",
      "icon": "âœ¦",
      "descricao": "A RegeneraÃ§Ã£o Divina alcanÃ§a aliados em raio 2.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_furtivo_2",
      "source": "guilda",
      "source_id": "ladino_furtivo_2",
      "name": "Ataque Furtivo II",
      "icon": "âœ¦",
      "descricao": "Ataque Furtivo tambÃ©m dispara se hÃ¡ aliado adjacente ao alvo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_furtivo_3",
      "source": "guilda",
      "source_id": "ladino_furtivo_3",
      "name": "Ataque Furtivo Supremo",
      "icon": "âœ¦",
      "descricao": "1Ã—/inimigo/rodada: quando um aliado acerta um inimigo, Luccas reage com um Ataque Furtivo nele.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_desarme_2",
      "source": "guilda",
      "source_id": "ladino_desarme_2",
      "name": "Desarme II",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "Chance extra de recuperar o ouro da armadilha desarmada.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_veneno_2",
      "source": "guilda",
      "source_id": "ladino_veneno_2",
      "name": "Veneno RÃ¡pido II",
      "icon": "âœ¦",
      "descricao": "O veneno na arma (corpo a corpo) dura 2 golpes certeiros.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_veneno_3",
      "source": "guilda",
      "source_id": "ladino_veneno_3",
      "name": "Veneno RÃ¡pido III",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "Ativar nÃ£o gasta mais a aÃ§Ã£o bÃ´nus. Ao ser revelado, +2 de CA por 1 rodada.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_armadilha_urso",
      "source": "guilda",
      "source_id": "ladino_armadilha_urso",
      "name": "FÃ³rmula: Armadilha de Urso",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Armadilha de Urso.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_fosso_estacas",
      "source": "guilda",
      "source_id": "ladino_fosso_estacas",
      "name": "FÃ³rmula: Fosso com Estacas",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Fosso com Estacas.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_rede",
      "source": "guilda",
      "source_id": "ladino_rede",
      "name": "FÃ³rmula: Rede",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Rede.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_armadilha_incendiaria",
      "source": "guilda",
      "source_id": "ladino_armadilha_incendiaria",
      "name": "FÃ³rmula: Armadilha IncendiÃ¡ria",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Armadilha IncendiÃ¡ria.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_mina_terrestre",
      "source": "guilda",
      "source_id": "ladino_mina_terrestre",
      "name": "FÃ³rmula: Mina Terrestre",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Mina Terrestre.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_fosso_envenenado",
      "source": "guilda",
      "source_id": "ladino_fosso_envenenado",
      "name": "FÃ³rmula: Fosso com Estacas Envenenadas",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Fosso com Estacas Envenenadas.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_nuvem_gas",
      "source": "guilda",
      "source_id": "ladino_nuvem_gas",
      "name": "FÃ³rmula: Nuvem de GÃ¡s",
      "icon": "âœ¦",
      "descricao": "Desbloqueia permanentemente a fabricaÃ§Ã£o de Nuvem de GÃ¡s.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin",
      "source": "guilda",
      "source_id": "lenda_goblin",
      "name": "Lenda: Goblin",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Troll.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_dragon",
      "source": "guilda",
      "source_id": "lenda_dragon",
      "name": "Lenda: DragÃ£o AnciÃ£o",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra DragÃ£o AnciÃ£o.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_aranha_sombria",
      "source": "guilda",
      "source_id": "lenda_aranha_sombria",
      "name": "Lenda: Aranha Sombria",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Aranha Sombria.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_escorpiao_pedra",
      "source": "guilda",
      "source_id": "lenda_escorpiao_pedra",
      "name": "Lenda: EscorpiÃ£o de Pedra",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra EscorpiÃ£o de Pedra.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_esqueleto_humano",
      "source": "guilda",
      "source_id": "lenda_esqueleto_humano",
      "name": "Lenda: Esqueleto Humano",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Cobra Venenosa.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_devorador_organico",
      "source": "guilda",
      "source_id": "lenda_devorador_organico",
      "name": "Lenda: Devorador OrgÃ¢nico",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Devorador OrgÃ¢nico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_urso_negro",
      "source": "guilda",
      "source_id": "lenda_urso_negro",
      "name": "Lenda: Urso Negro",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Goblin Dual.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_goblin_xama",
      "source": "guilda",
      "source_id": "lenda_goblin_xama",
      "name": "Lenda: XamÃ£ Goblin",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra XamÃ£ Goblin.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_kobold_lanceiro",
      "source": "guilda",
      "source_id": "lenda_kobold_lanceiro",
      "name": "Lenda: Kobold Lanceiro",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Devorador de Metal.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_bugbear_sombras",
      "source": "guilda",
      "source_id": "lenda_bugbear_sombras",
      "name": "Lenda: Bugbear â€” Bicho-PapÃ£o das Sombras",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Bugbear â€” Bicho-PapÃ£o das Sombras.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ogro_clava",
      "source": "guilda",
      "source_id": "lenda_ogro_clava",
      "name": "Lenda: Ogro de Clava",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Ogro de Clava.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ogro_lanca",
      "source": "guilda",
      "source_id": "lenda_ogro_lanca",
      "name": "Lenda: Ogro de LanÃ§a",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Ogro de LanÃ§a.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_grotao",
      "source": "guilda",
      "source_id": "lenda_grotao",
      "name": "Lenda: GrotÃ£o",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra GrotÃ£o.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_fogo",
      "source": "guilda",
      "source_id": "lenda_elemental_fogo",
      "name": "Lenda: Elemental de Fogo",
      "icon": "âœ¦",
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
      "icon": "âœ¦",
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
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Pedra.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_eletrico",
      "source": "guilda",
      "source_id": "lenda_elemental_eletrico",
      "name": "Lenda: Elemental ElÃ©trico",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental ElÃ©trico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_ar",
      "source": "guilda",
      "source_id": "lenda_elemental_ar",
      "name": "Lenda: Elemental de Ar",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Ar.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_elemental_agua",
      "source": "guilda",
      "source_id": "lenda_elemental_agua",
      "name": "Lenda: Elemental de Ãgua",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Elemental de Ãgua.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lobisomem",
      "source": "guilda",
      "source_id": "lenda_lobisomem",
      "name": "Lenda: Lobisomem",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Lobisomem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_escravo_vampirico",
      "source": "guilda",
      "source_id": "lenda_escravo_vampirico",
      "name": "Lenda: Escravo VampÃ­rico",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Escravo VampÃ­rico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_vampiro_jovem",
      "source": "guilda",
      "source_id": "lenda_vampiro_jovem",
      "name": "Lenda: Vampiro Jovem",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Vampiro Jovem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_vampiro_anciao",
      "source": "guilda",
      "source_id": "lenda_vampiro_anciao",
      "name": "Lenda: Vampiro AnciÃ£o",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Vampiro AnciÃ£o.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lorde_vampiro",
      "source": "guilda",
      "source_id": "lenda_lorde_vampiro",
      "name": "Lenda: Lorde Vampiro",
      "icon": "âœ¦",
      "descricao": "+1 de ataque e +1 nos saves contra Lorde Vampiro.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
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
      "icone": "ðŸ”¥",
      "tipo": "area_persistente",
      "descricao": "1d6/nÃ­vel. Ãrea persiste 3 rodadas com dano decaindo.",
      "save": "reflexos",
      "dano_por_nivel": "1d6",
      "area_raio": 2,
      "alcance_base": 5
    },
    {
      "id": "relampago",
      "nome": "RelÃ¢mpago",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "âš¡",
      "tipo": "linha_reflexiva",
      "descricao": "1d6/nÃ­vel por impacto. Linha reta de 7 casas + ricochete de volta (casas atingidas 2x). Pedro sÃ³ Ã© ferido na volta.",
      "save": "reflexos",
      "dano_por_nivel": "1d6",
      "alcance_base": 7
    },
    {
      "id": "raio_congelante",
      "nome": "Raio Congelante",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "â„ï¸",
      "tipo": "alvo",
      "descricao": "3d4+2d4/2nÃ­veis sem save. Fortitude ou paralisado 1-2 rodadas.",
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
      "icone": "ðŸŒ™",
      "tipo": "area",
      "descricao": "Ãrea. Vontade ou dorme 1d4+1. Primeiro ataque = crÃ­tico. Acorda com dano.",
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
      "icone": "ðŸ—£ï¸",
      "tipo": "alvo",
      "descricao": "Vontade ou controla 1 aÃ§Ã£o do alvo. Sem habilidades especiais.",
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
      "icone": "ðŸ˜±",
      "tipo": "area",
      "descricao": "Ãrea. Vontade ou foge 1d4+1 rodadas. -1 ataque. NÃ£o se aproxima.",
      "save": "vontade",
      "area_raio": 2,
      "alcance": 5,
      "duracao": "1d4+1"
    },
    {
      "id": "clarividencia",
      "nome": "ClarividÃªncia",
      "circulo": "primeiro",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "ðŸ”®",
      "tipo": "area_fixa",
      "descricao": "Remove nÃ©voa em Ã¡rea 4x4 (+escala por nÃ­vel). Dura 2 rodadas.",
      "duracao": 2
    },
    {
      "id": "barreira_arcana",
      "nome": "Barreira Arcana",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "ðŸ›¡ï¸",
      "tipo": "buff_self",
      "descricao": "Cancela 1 magia recebida. Slot consumido ao absorver. Dura atÃ© ativar.",
      "duracao": "ate_absorver"
    },
    {
      "id": "contramagica",
      "nome": "ContramÃ¡gica",
      "circulo": "primeiro",
      "classe": [
        "mage"
      ],
      "icone": "ðŸ›‘",
      "tipo": "reacao",
      "descricao": "ReaÃ§Ã£o. Teste oposto vs magia inimiga. Sucesso: cancela + inimigo perde aÃ§Ã£o.",
      "save": "teste_oposto"
    },
    {
      "id": "abencoar",
      "nome": "AbenÃ§oar",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "âœ¨",
      "tipo": "area",
      "descricao": "Ãrea 6x6. +1 ataque/dano/CA/resistÃªncia. Dura 1d4+1 rodadas.",
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
      "nome": "AmaldiÃ§oar",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "â˜ ï¸",
      "tipo": "area",
      "descricao": "Ãrea 3x3. -1 ataque/dano/CA/resistÃªncia. Dura 1d4+1 rodadas.",
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
      "nome": "AbenÃ§oar Arma",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "âš”ï¸",
      "tipo": "alvo_aliado",
      "descricao": "+1 ataque e dano na arma de aliado. Dura 1d6+2 rodadas.",
      "alcance": 6,
      "duracao": "1d6+2",
      "buff": {
        "ataque": 1,
        "dano": 1
      }
    },
    {
      "id": "saciar",
      "nome": "Saciar",
      "circulo": "primeiro",
      "classe": [
        "cleric"
      ],
      "icone": "ðŸ’§",
      "tipo": "toque",
      "descricao": "Toque. +10 fome +10 sede em 1 aliado.",
      "alcance": 1
    },
    {
      "id": "silencio",
      "nome": "SilÃªncio",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "ðŸ”‡",
      "tipo": "area_fixa",
      "descricao": "Ãrea 4x4. Sem magias nem bÃ´nus de CanÃ§Ã£o Heroica dentro. Dura 1d4 rodadas.",
      "area_lado": 4,
      "alcance_base": 5,
      "duracao": "1d4"
    },
    {
      "id": "manto_escuridao",
      "nome": "Manto de EscuridÃ£o",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "ðŸŒ‘",
      "tipo": "area_centrada",
      "descricao": "Raio 3. EscuridÃ£o â€” sem visÃ£o noturna: desvantagem. Com visÃ£o noturna: vantagem.",
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
      "icone": "ðŸž",
      "tipo": "utilidade",
      "descricao": "Cria 1d6+1 Ã¡gua e 1d6+2 pÃ£o. Lewis distribui para o grupo."
    },
    {
      "id": "regeneracao_magica",
      "nome": "RegeneraÃ§Ã£o",
      "circulo": "segundo",
      "classe": [
        "cleric"
      ],
      "icone": "ðŸŒ¿",
      "tipo": "buff_aliado",
      "descricao": "Pool 2d6+2. +1 HP/rodada. Se morrer: volta com 1 HP -3 fome/sede.",
      "alcance": 6
    },
    {
      "id": "protecao_energia",
      "nome": "ProteÃ§Ã£o contra Energia",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "ðŸ›¡ï¸",
      "tipo": "buff_self",
      "descricao": "Absorve 10 dano/rodada de fogo, gelo ou eletricidade. Dura 1d6+1.",
      "duracao": "1d6+1"
    },
    {
      "id": "invisibilidade",
      "nome": "Invisibilidade",
      "circulo": "segundo",
      "classe": [
        "mage"
      ],
      "icone": "ðŸ«¥",
      "tipo": "buff_self",
      "descricao": "Inimigos nÃ£o atacam. Ataque com vantagem + furtivo. Quebra ao atacar/lanÃ§ar.",
      "duracao": "1d6+1"
    },
    {
      "id": "visao_escuro",
      "nome": "VisÃ£o no Escuro",
      "circulo": "segundo",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "ðŸ‘ï¸",
      "tipo": "buff_aliado",
      "descricao": "Aliado ignora escuridÃ£o completamente. Dura 1d6+2 rodadas.",
      "alcance": 6,
      "duracao": "1d6+2"
    },
    {
      "id": "jato_ar",
      "nome": "Jato de Ar",
      "circulo": "segundo",
      "classe": [
        "mage"
      ],
      "icone": "ðŸŒªï¸",
      "tipo": "cone",
      "descricao": "Cone 4q. 1d6 dano. Falha: empurra 1d6q. ColisÃ£o com parede: +1d4.",
      "save": "reflexos",
      "dano": "1d6"
    },
    {
      "id": "velocidade",
      "nome": "Velocidade",
      "circulo": "terceiro",
      "classe": [
        "mage"
      ],
      "icone": "âš¡",
      "tipo": "buff_self",
      "descricao": "Dobra todas as aÃ§Ãµes no turno. Custo normal por aÃ§Ã£o. Dura 1d4 rodadas.",
      "duracao": "1d4"
    },
    {
      "id": "lentidao",
      "nome": "LentidÃ£o",
      "circulo": "terceiro",
      "classe": [
        "mage"
      ],
      "icone": "ðŸŒ",
      "tipo": "area",
      "descricao": "Ãrea 3x3. Falha: 1 aÃ§Ã£o/rodada, -1 CA, sem reaÃ§Ã£o. Sucesso: mov/2, -1 ataque.",
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
      "icone": "ðŸ§ ",
      "tipo": "alvo",
      "descricao": "Vontade ou dominado 1d4 rodadas. Novo teste ao sofrer dano.",
      "save": "vontade",
      "alcance": 5,
      "duracao": "1d4"
    },
    {
      "id": "dominar_morto_vivo",
      "nome": "Dominar Morto-Vivo",
      "circulo": "terceiro",
      "classe": [
        "mage"
      ],
      "icone": "ðŸ’€",
      "tipo": "alvo",
      "descricao": "Morto-vivo testa Vontade (bÃ´nus = ND) ao ser lanÃ§ada e a cada rodada na fase dos servos. Passar quebra o controle (volta hostil); 3 falhas seguidas = controle permanente. Slot Ãºnico. NÃ£o conta para Animar Mortos.",
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
      "icone": "ðŸŒªï¸",
      "tipo": "invocacao",
      "descricao": "Invoca elemental controlado. Age apÃ³s Lewis. Movimento 6q."
    },
    {
      "id": "raio_divino",
      "nome": "Raio Divino",
      "circulo": "terceiro",
      "classe": [
        "cleric"
      ],
      "icone": "âœ¨",
      "tipo": "alvo",
      "descricao": "1d6+1 por nÃ­vel. Reflexos: metade. Dobrado vs mortos-vivos e demÃ´nios.",
      "save": "reflexos",
      "dano_por_nivel": "1d6+1",
      "alcance": 6
    }
  ],
  "items": [
    {
      "id": "health_potion",
      "name": "PoÃ§Ã£o de Cura",
      "emoji": "ðŸ§ª",
      "item_slot": "bag",
      "effect": "heal",
      "value": 10
    },
    {
      "id": "elixir",
      "name": "Elixir da ForÃ§a",
      "emoji": "âš—ï¸",
      "item_slot": "bag",
      "effect": "atk_bonus",
      "value": 3
    },
    {
      "id": "antidote",
      "name": "AntÃ­doto",
      "emoji": "ðŸ’š",
      "item_slot": "bag",
      "effect": "heal",
      "value": 6
    },
    {
      "id": "garrafa_vinho",
      "name": "Garrafa de Vinho",
      "emoji": "ðŸ·",
      "item_slot": "bag",
      "effect": "wine",
      "value": 15
    },
    {
      "id": "racao",
      "name": "RaÃ§Ã£o (PÃ£o e Ãgua)",
      "emoji": "ðŸ¥–",
      "item_slot": "bag",
      "effect": "ration",
      "value": 15
    },
    {
      "id": "sword",
      "name": "Espada Curta de Ferro Serrilhado",
      "emoji": "âš”ï¸",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante",
      "item_slot": "weapon"
    },
    {
      "id": "magic_sword",
      "name": "Espada MÃ¡gica",
      "emoji": "ðŸ—¡ï¸",
      "item_slot": "weapon",
      "effect": "atk",
      "value": 4
    },
    {
      "id": "bow",
      "name": "Arco Ã‰lfico",
      "emoji": "ðŸ¹",
      "item_slot": "weapon",
      "effect": "atk",
      "value": 3
    },
    {
      "id": "staff",
      "name": "Cajado Arcano",
      "emoji": "ðŸª„",
      "die": "1d6",
      "stat": "str_",
      "reach": "cajado",
      "categoria": "contundente"
    },
    {
      "id": "shield",
      "name": "Escudo de Madeira",
      "emoji": "ðŸ›¡ï¸",
      "item_slot": "armor",
      "effect": "def_",
      "value": 2
    },
    {
      "id": "chainmail",
      "name": "Cota de Malha",
      "emoji": "ðŸª–",
      "kind": "armor",
      "ac_bonus": 4
    },
    {
      "id": "leather",
      "name": "Armadura de Couro",
      "emoji": "ðŸ¥‹",
      "kind": "armor",
      "ac_bonus": 2
    },
    {
      "id": "amulet",
      "name": "Amuleto da Sorte",
      "emoji": "ðŸ“¿",
      "item_slot": "item",
      "effect": "maxhp",
      "value": 5
    },
    {
      "id": "boots",
      "name": "Botas Velozes",
      "emoji": "ðŸ‘¢",
      "item_slot": "item",
      "effect": "spd",
      "value": 1
    },
    {
      "id": "ring",
      "name": "Anel de ForÃ§a",
      "emoji": "ðŸ’",
      "item_slot": "accessory",
      "effect": "atk",
      "value": 1
    },
    {
      "id": "cloak",
      "name": "Manto",
      "emoji": "ðŸ§£",
      "kind": "armor",
      "ac_bonus": 1
    },
    {
      "id": "dagger",
      "name": "Adaga",
      "emoji": "ðŸ—¡ï¸",
      "die": "1d4",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "chicote",
      "name": "Chicote",
      "emoji": "ðŸª¢",
      "die": "1d4",
      "stat": "dex",
      "range": 2,
      "categoria": "cortante"
    },
    {
      "id": "hand_crossbow",
      "name": "Besta de MÃ£o",
      "emoji": "ðŸ¹",
      "die": "1d4",
      "stat": "dex",
      "range": 4,
      "categoria": "perfurante"
    },
    {
      "id": "lanca_curta",
      "name": "LanÃ§a Curta",
      "emoji": "ðŸ”±",
      "die": "1d6",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "bordao",
      "name": "BordÃ£o",
      "emoji": "ðŸª„",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "cajado_madeira",
      "name": "Cajado de Madeira",
      "emoji": "ðŸª„",
      "die": "1d6",
      "stat": "str_",
      "reach": "cajado",
      "categoria": "contundente"
    },
    {
      "id": "maca",
      "name": "MaÃ§a",
      "emoji": "ðŸ”¨",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "shortsword",
      "name": "Espada Curta",
      "emoji": "âš”ï¸",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_basico",
      "name": "Machado de Ferro",
      "emoji": "ðŸª“",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "arco_curto",
      "name": "Arco Curto",
      "emoji": "ðŸ¹",
      "die": "1d6",
      "stat": "dex",
      "range": 8,
      "categoria": "perfurante"
    },
    {
      "id": "lanca",
      "name": "LanÃ§a",
      "emoji": "ðŸ”±",
      "die": "1d8",
      "stat": "str_",
      "reach": "lanca",
      "categoria": "perfurante"
    },
    {
      "id": "longsword",
      "name": "Espada Longa",
      "emoji": "âš”ï¸",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "longbow",
      "name": "Arco Longo",
      "emoji": "ðŸ¹",
      "die": "1d8",
      "stat": "dex",
      "range": 12,
      "categoria": "perfurante"
    },
    {
      "id": "warhammer",
      "name": "Martelo de Guerra",
      "emoji": "ðŸ”¨",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "besta",
      "name": "Besta",
      "emoji": "ðŸ¹",
      "die": "1d8",
      "stat": "dex",
      "range": 10,
      "categoria": "perfurante"
    },
    {
      "id": "mangual",
      "name": "Mangual",
      "emoji": "âš”ï¸",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "machado_duplo",
      "name": "Machado Duplo",
      "emoji": "ðŸª“",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "bastsword",
      "name": "Espada Bastarda",
      "emoji": "âš”ï¸",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_orc",
      "name": "Machado de Guerra Ã“rquico",
      "emoji": "ðŸª“",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "alabarda",
      "name": "Alabarda",
      "emoji": "ðŸª“",
      "die": "1d10",
      "stat": "str_",
      "range": 2,
      "categoria": "perfurante"
    },
    {
      "id": "espada2m",
      "name": "Espada de 2 MÃ£os",
      "emoji": "âš”ï¸",
      "die": "2d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "dagger_prata",
      "name": "Adaga de Prata",
      "emoji": "ðŸ—¡ï¸",
      "die": "1d4",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "chicote_prata",
      "name": "Chicote de Prata",
      "emoji": "ðŸª¢",
      "die": "1d4",
      "stat": "dex",
      "range": 2,
      "categoria": "cortante"
    },
    {
      "id": "hand_crossbow_prata",
      "name": "Besta de MÃ£o de Prata",
      "emoji": "ðŸ¹",
      "die": "1d4",
      "stat": "dex",
      "range": 4,
      "categoria": "perfurante"
    },
    {
      "id": "lanca_curta_prata",
      "name": "LanÃ§a Curta de Prata",
      "emoji": "ðŸ”±",
      "die": "1d6",
      "stat": "str_",
      "categoria": "perfurante"
    },
    {
      "id": "bordao_prata",
      "name": "BordÃ£o de Prata",
      "emoji": "ðŸª„",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "cajado_madeira_prata",
      "name": "Cajado de Madeira de Prata",
      "emoji": "ðŸª„",
      "die": "1d6",
      "stat": "str_",
      "reach": "cajado",
      "categoria": "contundente"
    },
    {
      "id": "staff_prata",
      "name": "Cajado Arcano de Prata",
      "emoji": "ðŸª„",
      "die": "1d6",
      "stat": "str_",
      "reach": "cajado",
      "categoria": "contundente"
    },
    {
      "id": "maca_prata",
      "name": "MaÃ§a de Prata",
      "emoji": "ðŸ”¨",
      "die": "1d6",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "shortsword_prata",
      "name": "Espada Curta de Prata",
      "emoji": "âš”ï¸",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_basico_prata",
      "name": "Machado de Ferro de Prata",
      "emoji": "ðŸª“",
      "die": "1d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "arco_curto_prata",
      "name": "Arco Curto de Prata",
      "emoji": "ðŸ¹",
      "die": "1d6",
      "stat": "dex",
      "range": 8,
      "categoria": "perfurante"
    },
    {
      "id": "lanca_prata",
      "name": "LanÃ§a de Prata",
      "emoji": "ðŸ”±",
      "die": "1d8",
      "stat": "str_",
      "reach": "lanca",
      "categoria": "perfurante"
    },
    {
      "id": "longsword_prata",
      "name": "Espada Longa de Prata",
      "emoji": "âš”ï¸",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "longbow_prata",
      "name": "Arco Longo de Prata",
      "emoji": "ðŸ¹",
      "die": "1d8",
      "stat": "dex",
      "range": 12,
      "categoria": "perfurante"
    },
    {
      "id": "warhammer_prata",
      "name": "Martelo de Guerra de Prata",
      "emoji": "ðŸ”¨",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "besta_prata",
      "name": "Besta de Prata",
      "emoji": "ðŸ¹",
      "die": "1d8",
      "stat": "dex",
      "range": 10,
      "categoria": "perfurante"
    },
    {
      "id": "mangual_prata",
      "name": "Mangual de Prata",
      "emoji": "âš”ï¸",
      "die": "1d8",
      "stat": "str_",
      "categoria": "contundente"
    },
    {
      "id": "machado_duplo_prata",
      "name": "Machado Duplo de Prata",
      "emoji": "ðŸª“",
      "die": "1d8",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "bastsword_prata",
      "name": "Espada Bastarda de Prata",
      "emoji": "âš”ï¸",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "machado_orc_prata",
      "name": "Machado de Guerra Ã“rquico de Prata",
      "emoji": "ðŸª“",
      "die": "1d10",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "alabarda_prata",
      "name": "Alabarda de Prata",
      "emoji": "ðŸª“",
      "die": "1d10",
      "stat": "str_",
      "range": 2,
      "categoria": "perfurante"
    },
    {
      "id": "espada2m_prata",
      "name": "Espada de 2 MÃ£os de Prata",
      "emoji": "âš”ï¸",
      "die": "2d6",
      "stat": "str_",
      "categoria": "cortante"
    },
    {
      "id": "escudo_p",
      "name": "Escudo Pequeno",
      "emoji": "ðŸ›¡ï¸",
      "kind": "shield",
      "ac_bonus": 1
    },
    {
      "id": "escudo_g",
      "name": "Escudo Grande",
      "emoji": "ðŸ›¡ï¸",
      "kind": "shield",
      "ac_bonus": 2
    },
    {
      "id": "leather_plate",
      "name": "Armadura de Couro e Placas",
      "emoji": "ðŸ¥‹",
      "kind": "armor",
      "ac_bonus": 3
    },
    {
      "id": "bronze_armor",
      "name": "Armadura de Bronze",
      "emoji": "ðŸª–",
      "kind": "armor",
      "ac_bonus": 5
    },
    {
      "id": "leather_mail",
      "name": "Armadura de Couro Revestido com Malha",
      "emoji": "ðŸª–",
      "kind": "armor",
      "ac_bonus": 6
    },
    {
      "id": "plate",
      "name": "Armadura de Placas",
      "emoji": "ðŸ›¡ï¸",
      "kind": "armor",
      "ac_bonus": 6
    },
    {
      "id": "monster_leather_plate",
      "name": "Armadura de Couro de Monstro e Placas",
      "emoji": "ðŸ›¡ï¸",
      "kind": "armor",
      "ac_bonus": 7
    },
    {
      "id": "fullplate",
      "name": "Armadura Completa",
      "emoji": "ðŸ›¡ï¸",
      "kind": "armor",
      "ac_bonus": 8
    },
    {
      "id": "flechas",
      "name": "Flechas (Ã—10)",
      "emoji": "ðŸ¹",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "flechas",
      "ammo_count": 10
    },
    {
      "id": "virotes",
      "name": "Virotes (Ã—10)",
      "emoji": "ðŸ¹",
      "item_slot": "ammo",
      "effect": "ammo",
      "ammo_type": "virotes",
      "ammo_count": 10
    },
    {
      "id": "virote_incendiario",
      "name": "Virote IncendiÃ¡rio",
      "emoji": "ðŸ”¥",
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
      "name": "Flecha IncendiÃ¡ria",
      "emoji": "ðŸ”¥",
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
      "emoji": "ðŸ„",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_fungo_acre"
    },
    {
      "id": "veneno_dor_escarlate",
      "name": "Dor Escarlate",
      "emoji": "ðŸ©¸",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_dor_escarlate"
    },
    {
      "id": "veneno_ardonia_negra",
      "name": "Ardonia Negra",
      "emoji": "ðŸ•·ï¸",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_ardonia_negra"
    },
    {
      "id": "vela_escuridao",
      "name": "Vela da EscuridÃ£o",
      "emoji": "ðŸ•¯ï¸",
      "item_slot": "bag",
      "effect": "veil_shadow",
      "value": 0
    },
    {
      "id": "ring_str",
      "name": "Anel de ForÃ§a",
      "emoji": "ðŸ’",
      "item_slot": "ring",
      "effect": "atk",
      "value": 1
    },
    {
      "id": "ring_vita",
      "name": "Anel da Vitalidade",
      "emoji": "ðŸ’",
      "item_slot": "ring",
      "effect": "maxhp",
      "value": 5
    },
    {
      "id": "helm_iron",
      "name": "Elmo de Ferro",
      "emoji": "â›‘ï¸",
      "item_slot": "head",
      "effect": "def_",
      "value": 1
    },
    {
      "id": "circlet",
      "name": "Tiara Arcana",
      "emoji": "ðŸ‘‘",
      "item_slot": "head",
      "effect": "maxhp",
      "value": 4
    },
    {
      "id": "backpack",
      "name": "Mochila de Couro",
      "emoji": "ðŸŽ’",
      "item_slot": "item",
      "effect": "bagslots",
      "value": 3
    },
    {
      "id": "veneno_aranha_sombria",
      "name": "Veneno da Aranha Sombria",
      "emoji": "ðŸ•·ï¸",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_aranha_sombria"
    },
    {
      "id": "veneno_escorpiao_pedra",
      "name": "Veneno do EscorpiÃ£o Pedra",
      "emoji": "ðŸ¦‚",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_escorpiao_pedra"
    },
    {
      "id": "veneno_cobra_cuspidora",
      "name": "Veneno de Cobra Cuspidora",
      "emoji": "ðŸ",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_cobra_cuspidora"
    },
    {
      "id": "veneno_basilisco",
      "name": "PeÃ§onha do Basilisco",
      "emoji": "ðŸ¦Ž",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_basilisco"
    },
    {
      "id": "veneno_polvo_abissal",
      "name": "Tinta do Polvo Abissal",
      "emoji": "ðŸ™",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_polvo_abissal"
    },
    {
      "id": "veneno_agonia_sufocante",
      "name": "Agonia Sufocante",
      "emoji": "ðŸ’€",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_agonia_sufocante"
    },
    {
      "id": "frasco_oleo",
      "name": "Frasco de Ã“leo IncendiÃ¡rio",
      "emoji": "ðŸ”¥",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "fogo_grego",
      "name": "Fogo Grego",
      "emoji": "ðŸŸ¢",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "bomba_incendiaria",
      "name": "Bomba IncendiÃ¡ria",
      "emoji": "ðŸ’£",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "granada",
      "name": "Granada Explosiva",
      "emoji": "ðŸ’£",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "granada_superior",
      "name": "Granada Superior",
      "emoji": "ðŸ’¥",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "bomba_fumaca",
      "name": "Bomba de FumaÃ§a",
      "emoji": "ðŸ’¨",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "frasco_acido",
      "name": "Frasco de Ãcido",
      "emoji": "ðŸ§ª",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "vidro_acido_grande",
      "name": "Vidro de Ãcido Grande",
      "emoji": "ðŸ«™",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "cola_alquimica",
      "name": "Cola AlquÃ­mica",
      "emoji": "ðŸ¯",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "rede_arremesso",
      "name": "Rede",
      "emoji": "ðŸ•¸ï¸",
      "item_slot": "bag",
      "effect": "throwable",
      "value": 0
    },
    {
      "id": "instrumento_harpa_velho",
      "name": "Harpa Velha",
      "emoji": "ðŸŽµ",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_rustico",
      "name": "Harpa RÃºstica",
      "emoji": "ðŸŽµ",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_padrao",
      "name": "Harpa PadrÃ£o",
      "emoji": "ðŸŽµ",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_tambor_rustico",
      "name": "Tambor de Guerra RÃºstico",
      "emoji": "ðŸ¥",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_tambor_padrao",
      "name": "Tambor de Guerra PadrÃ£o",
      "emoji": "ðŸ¥",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_rustico",
      "name": "Sino RÃºstico",
      "emoji": "ðŸ””",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_padrao",
      "name": "Sino PadrÃ£o",
      "emoji": "ðŸ””",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_alaude_rustico",
      "name": "AlaÃºde RÃºstico",
      "emoji": "ðŸª•",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_alaude_padrao",
      "name": "AlaÃºde PadrÃ£o",
      "emoji": "ðŸª•",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_refinado",
      "name": "Harpa Refinada",
      "emoji": "ðŸŽµ",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_rustico",
      "name": "Trompa de Guerra RÃºstica",
      "emoji": "ðŸ“¯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_padrao",
      "name": "Trompa de Guerra PadrÃ£o",
      "emoji": "ðŸ“¯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_rustico",
      "name": "Lira RÃºstica",
      "emoji": "ðŸŽ¼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_padrao",
      "name": "Lira PadrÃ£o",
      "emoji": "ðŸŽ¼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_flauta_rustico",
      "name": "Flauta RÃºstica",
      "emoji": "ðŸŽ¶",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_flauta_padrao",
      "name": "Flauta PadrÃ£o",
      "emoji": "ðŸŽ¶",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_rustico",
      "name": "Violino RÃºstico",
      "emoji": "ðŸŽ»",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_padrao",
      "name": "Violino PadrÃ£o",
      "emoji": "ðŸŽ»",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_padrao_elfica",
      "name": "Harpa PadrÃ£o Ã‰lfica",
      "emoji": "ðŸŽµ",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_padrao_elfica",
      "name": "Trompa de Guerra PadrÃ£o Ã‰lfica",
      "emoji": "ðŸ“¯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_padrao_elfica",
      "name": "Sino PadrÃ£o Ã‰lfico",
      "emoji": "ðŸ””",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_tambor_padrao_ana",
      "name": "Tambor de Guerra PadrÃ£o AnÃ£o",
      "emoji": "ðŸ¥",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_padrao_ana",
      "name": "Lira PadrÃ£o AnÃ£",
      "emoji": "ðŸŽ¼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_padrao_ana",
      "name": "Violino PadrÃ£o AnÃ£o",
      "emoji": "ðŸŽ»",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_sino_padrao_runico",
      "name": "Sino PadrÃ£o RÃºnico",
      "emoji": "ðŸ””",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_flauta_padrao_runico",
      "name": "Flauta PadrÃ£o RÃºnica",
      "emoji": "ðŸŽ¶",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_trompa_padrao_runico",
      "name": "Trompa de Guerra PadrÃ£o RÃºnica",
      "emoji": "ðŸ“¯",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_violino_padrao_runico",
      "name": "Violino PadrÃ£o RÃºnico",
      "emoji": "ðŸŽ»",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_lira_padrao_runico",
      "name": "Lira PadrÃ£o RÃºnica",
      "emoji": "ðŸŽ¼",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_harpa_refinado_elfica_runico",
      "name": "Harpa LendÃ¡ria Ã‰lfica",
      "emoji": "ðŸŽµ",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_velho",
      "name": "Gaita Velha",
      "emoji": "ðŸª—",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_rustico",
      "name": "Gaita RÃºstica",
      "emoji": "ðŸª—",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_padrao",
      "name": "Gaita PadrÃ£o",
      "emoji": "ðŸª—",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_refinado",
      "name": "Gaita Refinada",
      "emoji": "ðŸª—",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_padrao_runico",
      "name": "Gaita PadrÃ£o RÃºnica",
      "emoji": "ðŸª—",
      "item_slot": "instrumento"
    },
    {
      "id": "instrumento_gaita_refinado_ana_runico",
      "name": "Gaita LendÃ¡ria AnÃ£",
      "emoji": "ðŸª—",
      "item_slot": "instrumento"
    },
    {
      "id": "pao",
      "name": "PÃ£o",
      "emoji": "ðŸ¥–",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "garrafa_agua",
      "name": "Garrafa de Ãgua",
      "emoji": "ðŸ’§",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "suco_fruta",
      "name": "Suco de Fruta",
      "emoji": "ðŸ§ƒ",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "caneca_cerveja",
      "name": "Caneca de Cerveja",
      "emoji": "ðŸº",
      "item_slot": "bag",
      "effect": "ale",
      "value": 10
    },
    {
      "id": "racao_viagem",
      "name": "RaÃ§Ã£o de Viagem",
      "emoji": "ðŸ¥©",
      "item_slot": "bag",
      "effect": "food"
    },
    {
      "id": "cantil_agua",
      "name": "Cantil de Ãgua",
      "emoji": "ðŸ§´",
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
      "id": "health_potion_small",
      "name": "PoÃ§Ã£o de Cura Pequena",
      "emoji": "ðŸ§ª",
      "item_slot": "bag",
      "effect": "heal",
      "value": 5
    },
    {
      "id": "health_potion_concentrated",
      "name": "PoÃ§Ã£o de Cura Concentrada",
      "emoji": "ðŸ§ª",
      "item_slot": "bag",
      "effect": "heal",
      "value": 10
    },
    {
      "id": "health_potion_improved",
      "name": "PoÃ§Ã£o de Cura Aprimorada",
      "emoji": "ðŸ§ª",
      "item_slot": "bag",
      "effect": "heal",
      "value": 20
    },
    {
      "id": "regeneration_potion",
      "name": "PoÃ§Ã£o de RegeneraÃ§Ã£o",
      "emoji": "ðŸŒ¿",
      "item_slot": "bag",
      "effect": "regeneration",
      "value": 10
    }
  ],
  "traps": [
    {
      "tipo": "buraco",
      "nome": "Buraco",
      "icone": "ðŸ•³ï¸",
      "cr": 0.1,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_urso",
      "nome": "Armadilha de Urso",
      "icone": "ðŸª¤",
      "cr": 0.25,
      "precisa_veneno": false
    },
    {
      "tipo": "fosso_estacas",
      "nome": "Fosso com Estacas",
      "icone": "â›ï¸",
      "cr": 0.35,
      "precisa_veneno": false
    },
    {
      "tipo": "rede",
      "nome": "Rede",
      "icone": "ðŸ•¸ï¸",
      "cr": 0.15,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_incendiaria",
      "nome": "Armadilha IncendiÃ¡ria",
      "icone": "ðŸ”¥",
      "cr": 0.5,
      "precisa_veneno": false
    },
    {
      "tipo": "mina_terrestre",
      "nome": "Mina Terrestre",
      "icone": "ðŸ’£",
      "cr": 0.75,
      "precisa_veneno": false
    },
    {
      "tipo": "fosso_envenenado",
      "nome": "Fosso com Estacas Envenenadas",
      "icone": "â˜ ï¸",
      "cr": 0.5,
      "precisa_veneno": true
    },
    {
      "tipo": "nuvem_gas",
      "nome": "Nuvem de GÃ¡s",
      "icone": "ðŸŒ«ï¸",
      "cr": 0.4,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_teletransporte",
      "nome": "Armadilha de Teletransporte",
      "icone": "ðŸŒ€",
      "cr": 0.4,
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_dardos_envenenados",
      "nome": "Armadilha de Dardos Envenenados",
      "icone": "ðŸŽ¯",
      "cr": 0.4,
      "precisa_veneno": true
    }
  ],
  "venoms": [
    {
      "id": "veneno_aranha_sombria",
      "name": "Veneno da Aranha Sombria"
    },
    {
      "id": "veneno_escorpiao_pedra",
      "name": "Veneno do EscorpiÃ£o Pedra"
    },
    {
      "id": "veneno_cobra_cuspidora",
      "name": "Veneno de Cobra Cuspidora"
    },
    {
      "id": "veneno_basilisco",
      "name": "PeÃ§onha do Basilisco"
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
    }
  ],
  "decorations": [
    {
      "type": "cama",
      "nome": "Cama",
      "emoji": "ðŸ›ï¸",
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
      "emoji": "ðŸªµ",
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
      "emoji": "â›²",
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
      "emoji": "ðŸ”¥",
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
      "emoji": "âš°ï¸",
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
      "emoji": "ðŸª‘",
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
      "emoji": "ðŸ—„ï¸",
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
      "nome": "CarroÃ§a",
      "emoji": "ðŸ›’",
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
      "emoji": "ðŸ›ï¸",
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
      "emoji": "ðŸ›¢ï¸",
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
      "emoji": "ðŸ’°",
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
      "emoji": "ðŸ›Œ",
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
      "emoji": "ðŸ“š",
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
      "nome": "Altar ritualÃ­stico",
      "emoji": "ðŸ›",
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
      "emoji": "ðŸ‘‘",
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
      "emoji": "â›“ï¸",
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
      "nome": "Grades de prisÃ£o",
      "emoji": "ðŸš§",
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
      "emoji": "âš”ï¸",
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
      "emoji": "ðŸ”ª",
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
      "nome": "Mesa de quÃ­mica",
      "emoji": "ðŸ§ª",
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
      "nome": "Ãrvore",
      "emoji": "ðŸŒ³",
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
      "nome": "Ãrvore grande",
      "emoji": "ðŸŒ²",
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
      "type": "chao",
      "nome": "ChÃ£o (grama)",
      "emoji": "ðŸŒ¿",
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
      "nome": "BrasÃ£o do LeÃ£o",
      "emoji": "ðŸ¦",
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
      "emoji": "ðŸ”´",
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
      "emoji": "âšª",
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
      "nome": "Ãgua",
      "categoria": "piso",
      "cor": "#126da1",
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
    }
  ]
};
// GERADO por tools/export_catalog.py — não editar à mão.
// Rode `python tools/export_catalog.py` para regenerar.
