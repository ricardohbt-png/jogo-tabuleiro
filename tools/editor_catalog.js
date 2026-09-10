window.EDITOR_CATALOG = {
  "monsters": [
    {
      "type": "pombo",
      "name": "Pombo",
      "emoji": "🕊️",
      "boss": false,
      "tier": 0,
      "cr": 0,
      "hp": 1,
      "ac": 17,
      "movement": 9,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "minusculo",
      "str_": 2,
      "dex": 17,
      "con_": 10,
      "int_": 2,
      "fort": 2,
      "ref_": 5,
      "will": 2,
      "attacks": [],
      "special_abilities": [],
      "undead": false,
      "subtipo": "animal",
      "voo": true,
      "altura_inicial": 2,
      "altura_max": 10,
      "percepcao": 14
    },
    {
      "type": "rato",
      "name": "Rato",
      "emoji": "🐀",
      "boss": false,
      "tier": 0,
      "cr": 0,
      "hp": 1,
      "ac": 14,
      "natural_armor": 2,
      "movement": 4,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "minusculo",
      "str_": 2,
      "dex": 15,
      "con_": 10,
      "int_": 2,
      "fort": 2,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 4,
          "damage": "1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [],
      "undead": false,
      "subtipo": "animal",
      "percepcao": 11
    },
    {
      "type": "gato",
      "name": "Gato",
      "emoji": "🐈",
      "boss": false,
      "tier": 0,
      "cr": 0,
      "hp": 2,
      "ac": 14,
      "natural_armor": 2,
      "movement": 8,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "pequeno",
      "str_": 3,
      "dex": 15,
      "con_": 10,
      "int_": 2,
      "fort": 2,
      "ref_": 4,
      "will": 1,
      "attacks": [
        {
          "name": "Garras",
          "atk_bonus": 4,
          "damage": "1",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        }
      ],
      "special_abilities": [],
      "undead": false,
      "subtipo": "animal",
      "darkvision_range": 8,
      "percepcao": 13
    },
    {
      "type": "ovelha",
      "name": "Ovelha",
      "emoji": "🐑",
      "boss": false,
      "tier": 0,
      "cr": 0,
      "hp": 6,
      "ac": 10,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "str_": 11,
      "dex": 10,
      "con_": 15,
      "int_": 2,
      "fort": 4,
      "ref_": 2,
      "will": 1,
      "attacks": [
        {
          "name": "Cabeçada",
          "atk_bonus": 1,
          "damage": "1d4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [],
      "undead": false,
      "subtipo": "animal",
      "percepcao": 12
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
      "subtipo": "morto_vivo",
      "percepcao": 13
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
      "subtipo": "raca_padrao",
      "percepcao": 13
    },
    {
      "type": "troll",
      "name": "Troll",
      "emoji": "🗿",
      "boss": false,
      "tier": 4,
      "cr": 4,
      "hp": 60,
      "ac": 16,
      "movement": 6,
      "vision_base": 0,
      "percepcao": 12,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "troll",
      "str_": 20,
      "dex": 10,
      "con_": 18,
      "int_": 6,
      "fort": 5,
      "will": 1,
      "save_bonuses": {
        "fortitude": 3
      },
      "attacks": [
        {
          "name": "Clava Pesada",
          "atk_bonus": 6,
          "damage": "1d12+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2,
          "on_hit": null,
          "categoria": "contundente"
        }
      ],
      "special_abilities": [
        {
          "id": "regeneracao_troll",
          "name": "Regeneração Troll",
          "action_type": "passiva",
          "amount": 4,
          "descricao": "Recupera 4 PV no início do turno; ácido bloqueia a regeneração. Se chegar a 0 PV, retorna com 1 PV no próximo turno, exceto se o dano final tiver sido fogo ou se a regeneração estiver bloqueada por ácido."
        },
        {
          "id": "golpe_devastador_troll",
          "name": "Golpe Devastador",
          "action_type": "acao_bonus",
          "cooldown_turns": 4,
          "descricao": "No próximo ataque de clava, dobra os dados de dano. Recarga: 4 rodadas."
        },
        {
          "id": "pressao_constante_troll",
          "name": "Pressão Constante",
          "action_type": "acao_bonus",
          "cooldown_turns": 4,
          "range": 1,
          "ca_penalty": 2,
          "duration_rounds": 2,
          "descricao": "Um herói adjacente sofre -2 CA por 2 rodadas. Recarga: 4 rodadas."
        },
        {
          "id": "investida_brutal_troll",
          "name": "Investida Brutal",
          "action_type": "passiva",
          "cooldown_turns": 5,
          "move_required": 3,
          "damage": "2d6",
          "push": 1,
          "descricao": "Após mover pelo menos 3 casas antes do ataque, acrescenta 2d6 de dano e empurra 1 casa. Recarga: 5 rodadas."
        },
        {
          "id": "vigor_colossal",
          "name": "Vigor Colossal",
          "action_type": "passiva",
          "save_bonus": {
            "fortitude": 3
          },
          "descricao": "+3 em todos os testes de Fortitude."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "acid",
          "multiplier": 2,
          "descricao": "Vulnerabilidade: dano de ácido é dobrado e bloqueia a regeneração."
        }
      ],
      "resistances": [],
      "loot_table": {
        "1-50": null,
        "51-80": {
          "tipo": "gold",
          "valor": 8
        },
        "81-100": {
          "tipo": "item",
          "id": "pocao_cura"
        }
      },
      "ai_type": "troll",
      "undead": false,
      "subtipo": "raca_padrao",
      "darkvision_range": 8
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
      "subtipo": "animal",
      "percepcao": 12
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
      "subtipo": "animal",
      "percepcao": 12
    },
    {
      "type": "lacralion_filhote",
      "name": "Lacralion Filhote",
      "emoji": "🦂",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 28,
      "ac": 16,
      "natural_armor": 4,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "lacralion",
      "str_": 14,
      "dex": 14,
      "con_": 14,
      "int_": 2,
      "fort": 4,
      "ref_": 4,
      "will": -4,
      "attacks": [
        {
          "name": "Pinça",
          "atk_bonus": 5,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 5,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Ferrão",
          "atk_bonus": 4,
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "veneno_lacralion",
          "name": "Veneno do Lacralion",
          "action_type": "passiva",
          "attack_index": 2,
          "poison_dc": 14,
          "extra_damage": "1d4",
          "descricao": "Ao acertar o Ferrão, Fortitude CD 14; falha: 1d4 de dano adicional e Sangramento."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "animal",
      "percepcao": 12
    },
    {
      "type": "lacralion_adulto",
      "name": "Lacralion Adulto",
      "emoji": "🦂",
      "boss": false,
      "tier": 4,
      "cr": 4,
      "hp": 58,
      "ac": 19,
      "natural_armor": 7,
      "movement": 5,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "lacralion",
      "str_": 18,
      "dex": 14,
      "con_": 16,
      "int_": 2,
      "fort": 7,
      "ref_": 4,
      "will": -4,
      "attacks": [
        {
          "name": "Pinça",
          "atk_bonus": 8,
          "damage": "1d8+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 8,
          "damage": "1d6+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Ferrão",
          "atk_bonus": 8,
          "damage": "1d8+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "agarrar_lacralion",
          "name": "Agarrão",
          "action_type": "passiva",
          "attack_index": 0,
          "dc": 16,
          "save": "fortitude",
          "escape_saves": [
            "fortitude"
          ],
          "max_targets": 1,
          "descricao": "Quando a Pinça acerta, o alvo fica Imobilizado. Escape: Fortitude CD 16."
        },
        {
          "id": "veneno_lacralion",
          "name": "Veneno do Lacralion",
          "action_type": "passiva",
          "attack_index": 2,
          "poison_dc": 16,
          "extra_damage": "1d6",
          "descricao": "Ao acertar o Ferrão, Fortitude CD 16; falha: 1d6 de dano adicional e Sangramento."
        },
        {
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "1d4",
          "damage_types": [
            "physical"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d4 de dano físico."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "animal",
      "percepcao": 12
    },
    {
      "type": "lacralion_anciao",
      "name": "Lacralion Ancião",
      "emoji": "🦂",
      "boss": false,
      "tier": 7,
      "cr": 7,
      "hp": 102,
      "ac": 23,
      "natural_armor": 10,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "lacralion",
      "str_": 22,
      "dex": 16,
      "con_": 20,
      "int_": 2,
      "fort": 10,
      "ref_": 6,
      "will": -4,
      "attacks": [
        {
          "name": "Pinça",
          "atk_bonus": 11,
          "damage": "2d6+7",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Mordida",
          "atk_bonus": 11,
          "damage": "2d6+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Ferrão",
          "atk_bonus": 11,
          "damage": "2d6+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "agarrar_lacralion",
          "name": "Agarrão",
          "action_type": "passiva",
          "attack_index": 0,
          "dc": 16,
          "save": "fortitude",
          "escape_saves": [
            "fortitude"
          ],
          "max_targets": 2,
          "descricao": "Quando a Pinça acerta, o alvo fica Imobilizado. Escape: Fortitude CD 16."
        },
        {
          "id": "veneno_lacralion",
          "name": "Veneno do Lacralion",
          "action_type": "passiva",
          "attack_index": 2,
          "poison_dc": 16,
          "extra_damage": "1d6",
          "descricao": "Ao acertar o Ferrão, Fortitude CD 16; falha: 1d6 de dano adicional e Sangramento."
        },
        {
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d6 de dano físico."
        },
        {
          "id": "predador_implacavel",
          "name": "Predador Implacável",
          "action_type": "passiva",
          "descricao": "Pode manter dois inimigos Imobilizados ao mesmo tempo."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "animal",
      "percepcao": 12
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
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
        },
        {
          "type": "save_penalty",
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
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
      "darkvision_range": 4,
      "percepcao": 12
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
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
        },
        {
          "type": "save_penalty",
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "esqueleto_animal",
      "undead": true,
      "subtipo": "morto_vivo",
      "darkvision_range": 8,
      "percepcao": 12
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
      "subtipo": "animal",
      "percepcao": 12
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
          "categoria": "perfurante",
          "disease_severity": "leve",
          "disease_dc": 10,
          "disease_save": "fortitude"
        }
      ],
      "special_abilities": [
        {
          "id": "contagiar",
          "name": "Contagiar",
          "action_type": "passiva",
          "attack_index": 0,
          "dc": 10,
          "save": "fortitude",
          "disease_severity": "leve",
          "descricao": "Ao acertar a mordida, alvo testa Fortitude CD 10 ou contrai doença leve"
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
      "subtipo": "animal",
      "percepcao": 12
    },
    {
      "type": "devorador_organico",
      "name": "Devorador Orgânico",
      "emoji": "🟢",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 22,
      "ac": 12,
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
      "resistances": [
        {
          "type": "physical",
          "reduction": 2
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
      "subtipo": "raca_padrao",
      "percepcao": 12
    },
    {
      "type": "urso_negro",
      "name": "Urso Negro",
      "emoji": "🐻",
      "boss": false,
      "tier": 1,
      "cr": 1,
      "hp": 30,
      "ac": 13,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ursoNegro",
      "str_": 20,
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
      "subtipo": "animal",
      "percepcao": 12
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 1,
          "descricao": "-1 em testes de Vontade"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "saves": [
            "vontade"
          ],
          "bonus_flat": -1,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -1 em testes de Vontade"
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
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
      "subtipo": "vegetal",
      "percepcao": 13
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "save_penalty",
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
      "subtipo": "raca_padrao",
      "percepcao": 13
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
      "subtipo": "raca_padrao",
      "percepcao": 14
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
          "attack_index": 0,
          "dc": 10,
          "save": "fortitude",
          "disease_severity": "leve",
          "descricao": "Ao acertar o ataque selecionado: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve"
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
      "darkvision_range": 8,
      "percepcao": 11
    },
    {
      "type": "devorador_metal",
      "name": "Devorador de Metal",
      "emoji": "🔩",
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
      "resistances": [
        {
          "type": "physical",
          "reduction": 2
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
      "subtipo": "raca_padrao",
      "percepcao": 12
    },
    {
      "type": "bugbear_sombras",
      "name": "Bugbear — Bicho-Papão das Sombras",
      "emoji": "😈",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 30,
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
      "darkvision_range": 99,
      "percepcao": 13
    },
    {
      "type": "ogro_clava",
      "name": "Ogro de Clava",
      "emoji": "🧌",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 41,
      "ac": 14,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ogroClava",
      "str_": 20,
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
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
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
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
      "subtipo": "raca_padrao",
      "percepcao": 12
    },
    {
      "type": "ogro_lanca",
      "name": "Ogro de Lança",
      "emoji": "🧌",
      "boss": false,
      "tier": 2,
      "cr": 2,
      "hp": 38,
      "ac": 16,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ogroLanca",
      "str_": 19,
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
          "id": "vulnerabilidade",
          "name": "Vulnerabilidade",
          "action_type": "passiva",
          "saves": [
            "vontade"
          ],
          "penalty": 2,
          "descricao": "-2 em testes de Vontade"
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
          "saves": [
            "vontade"
          ],
          "bonus_flat": -2,
          "vulnerabilidade": true,
          "descricao": "Vulnerabilidade: -2 em testes de Vontade"
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 2
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
      "subtipo": "raca_padrao",
      "percepcao": 12
    },
    {
      "type": "elemental_fogo",
      "name": "Elemental de Fogo",
      "emoji": "🔥",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 32,
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
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "1d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d6 de dano de fogo."
        },
        {
          "id": "morte_explosiva",
          "name": "Morte Explosiva",
          "action_type": "passiva",
          "damage": "4d6",
          "damage_types": [
            "fire"
          ],
          "radius": 1,
          "save": "reflexos",
          "dc": 13,
          "duration": 2,
          "tick_damage": "1d6",
          "descricao": "Ao morrer, explode em raio 1: 4d6 de fogo; Reflexos CD 13 reduz a metade. Chamas persistem por 2 rodadas."
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
      "subtipo": "construto",
      "percepcao": 12
    },
    {
      "type": "elemental_gelo",
      "name": "Elemental de Gelo",
      "emoji": "❄️",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 36,
      "ac": 16,
      "natural_armor": 6,
      "movement": 5,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_gelo",
      "caster_level": 2,
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
        },
        {
          "id": "raio_congelante",
          "name": "Raio Congelante",
          "action_type": "magia",
          "cooldown_turns": 6,
          "circulo": 1,
          "descricao": "Conjurador nível 2. Dano de 3d4 sem teste de resistência; Fortitude apenas para evitar a paralisia. Recarga 6 rodadas."
        }
      ],
      "monster_spells": [
        {
          "id": "raio_congelante",
          "limit_mode": "cooldown",
          "cooldown_turns": 6
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
          "reduction": 3
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
      "subtipo": "construto",
      "percepcao": 11
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
      "subtipo": "construto",
      "percepcao": 10
    },
    {
      "type": "elemental_eletrico",
      "name": "Elemental Elétrico",
      "emoji": "⚡",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 32,
      "ac": 15,
      "natural_armor": 0,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "elemental_eletrico",
      "caster_level": 3,
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
          "range": 4,
          "range_shape": "orthogonal",
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
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "1d8",
          "damage_types": [
            "lightning"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d8 de dano de eletricidade."
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
        },
        {
          "id": "relampago",
          "name": "Relâmpago",
          "action_type": "magia",
          "cooldown_turns": 6,
          "circulo": 1,
          "descricao": "Conjurador nível 3. Linha reta de 6 casas, 3d6 por impacto; Reflexos reduz à metade e a descarga ricocheteia de volta. Recarga 6 rodadas."
        }
      ],
      "monster_spells": [
        {
          "id": "relampago",
          "limit_mode": "cooldown",
          "cooldown_turns": 6
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
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "construto",
      "percepcao": 13
    },
    {
      "type": "elemental_ar",
      "name": "Elemental de Ar",
      "emoji": "🌪️",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 32,
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
          "id": "voo",
          "name": "Voo",
          "action_type": "passiva",
          "descricao": "Move-se no ar na altura 2; ataques à distância consideram a diferença vertical."
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
      "subtipo": "construto",
      "voo": true,
      "altura_inicial": 2,
      "altura_max": 10,
      "pode_alterar_altura": true,
      "custo_mov_altura": 1,
      "ignora_obstaculos_voo": false,
      "percepcao": 13
    },
    {
      "type": "elemental_agua",
      "name": "Elemental de Água",
      "emoji": "🌊",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 42,
      "ac": 15,
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
      "subtipo": "construto",
      "percepcao": 12
    },
    {
      "type": "lobisomem",
      "name": "Lobisomem",
      "emoji": "🐺",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 31,
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
      "loot_drops": [
        {
          "kind": "gold",
          "amount": 10,
          "chance": 30
        },
        {
          "kind": "gold",
          "amount": 15,
          "chance": 30
        },
        {
          "kind": "gold",
          "amount": 20,
          "chance": 25
        },
        {
          "kind": "gold",
          "amount": 35,
          "chance": 15
        },
        {
          "kind": "gold",
          "amount": 50,
          "chance": 5
        }
      ],
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "raca_padrao",
      "percepcao": 13
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
      "loot_drops": [
        {
          "kind": "item",
          "item_id": "pocao_cura",
          "chance": 25
        }
      ],
      "ai_type": "agressivo",
      "undead": true,
      "subtipo": "morto_vivo",
      "percepcao": 13
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
      "subtipo": "morto_vivo",
      "percepcao": 14
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
      "subtipo": "morto_vivo",
      "percepcao": 15
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
      "subtipo": "morto_vivo",
      "percepcao": 15
    },
    {
      "type": "ferrao_charcos_jovem",
      "name": "Ferrão dos Charcos Jovem",
      "emoji": "🦂",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 46,
      "ac": 18,
      "natural_armor": 5,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ferrao_do_lamacal",
      "str_": 16,
      "dex": 16,
      "con_": 16,
      "int_": 2,
      "fort": 6,
      "ref_": 5,
      "will": -4,
      "attacks": [
        {
          "name": "Garras",
          "atk_bonus": 6,
          "damage": "1d6+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Tentáculos",
          "atk_bonus": 6,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Mordida",
          "atk_bonus": 6,
          "damage": "1d8+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Ferrão",
          "atk_bonus": 5,
          "damage": "1d6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "movimento_aquatico",
          "name": "Movimento Aquático",
          "action_type": "passiva",
          "descricao": "Move 6 quadrados normalmente em terra, água e água profunda."
        },
        {
          "id": "veneno_charcos",
          "name": "Veneno",
          "action_type": "passiva",
          "attack_index": 3,
          "poison_dc": 15,
          "effect": "perde_movimento",
          "descricao": "Ao acertar o Ferrão, Fortitude CD 15; falha: perde a ação de movimento no próximo turno."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "aberracao",
      "percepcao": 12
    },
    {
      "type": "ferrao_charcos_adulto",
      "name": "Ferrão dos Charcos Adulto",
      "emoji": "🦂",
      "boss": false,
      "tier": 5,
      "cr": 5,
      "hp": 74,
      "ac": 20,
      "natural_armor": 7,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ferrao_do_lamacal",
      "str_": 18,
      "dex": 16,
      "con_": 18,
      "int_": 2,
      "fort": 8,
      "ref_": 5,
      "will": -4,
      "attacks": [
        {
          "name": "Garras",
          "atk_bonus": 9,
          "damage": "1d8+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Tentáculos",
          "atk_bonus": 9,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 4
        },
        {
          "name": "Mordida",
          "atk_bonus": 9,
          "damage": "2d6+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Ferrão",
          "atk_bonus": 9,
          "damage": "1d6+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "movimento_aquatico",
          "name": "Movimento Aquático",
          "action_type": "passiva",
          "descricao": "Move 6 quadrados normalmente em terra, água e água profunda."
        },
        {
          "id": "tentaculos_imobilizar",
          "name": "Tentáculos",
          "action_type": "passiva",
          "attack_index": 1,
          "hits_needed": 2,
          "dc": 17,
          "save": "fortitude",
          "escape_saves": [
            "fortitude"
          ],
          "max_targets": 1,
          "descricao": "Se dois Tentáculos acertarem o mesmo alvo, ele fica Imobilizado. Escape: Fortitude CD 17."
        },
        {
          "id": "constricao_charcos",
          "name": "Constrição",
          "action_type": "passiva",
          "damage": "1d6+5",
          "damage_types": [
            "physical"
          ],
          "descricao": "No início do turno, criaturas Imobilizadas sofrem 1d6+5. Enquanto presas, não podem se afastar."
        },
        {
          "id": "ferrao_paralitico",
          "name": "Ferrão Paralítico",
          "action_type": "passiva",
          "attack_index": 3,
          "dc": 17,
          "save": "fortitude",
          "effect": "perde_movimento",
          "descricao": "Ao acertar o Ferrão, Fortitude CD 17; falha: perde a ação de movimento no próximo turno."
        },
        {
          "id": "nuvem_acida",
          "name": "Nuvem Ácida",
          "action_type": "acao",
          "cooldown_turns": 4,
          "range": 4,
          "radius": 1,
          "duration": 2,
          "initial_damage": "2d6",
          "tick_damage": "1d6",
          "damage_types": [
            "acid"
          ],
          "descricao": "Recarga 4 rodadas. Centro no alvo; raio 1. Causa 2d6 ao surgir e 1d6 no turno de cada criatura dentro da área."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "aberracao",
      "percepcao": 12
    },
    {
      "type": "ferrao_charcos_anciao",
      "name": "Ferrão dos Charcos Ancião",
      "emoji": "🦂",
      "boss": false,
      "tier": 8,
      "cr": 8,
      "hp": 130,
      "ac": 24,
      "natural_armor": 10,
      "movement": 6,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "grande",
      "image": "ferrao_do_lamacal",
      "str_": 22,
      "dex": 18,
      "con_": 22,
      "int_": 2,
      "fort": 11,
      "ref_": 7,
      "will": -4,
      "attacks": [
        {
          "name": "Garras",
          "atk_bonus": 12,
          "damage": "2d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Tentáculos",
          "atk_bonus": 12,
          "damage": "1d8+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 6
        },
        {
          "name": "Mordida",
          "atk_bonus": 12,
          "damage": "3d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Ferrões",
          "atk_bonus": 12,
          "damage": "2d6+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        }
      ],
      "special_abilities": [
        {
          "id": "movimento_aquatico",
          "name": "Movimento Aquático",
          "action_type": "passiva",
          "descricao": "Move 6 quadrados normalmente em terra, água e água profunda."
        },
        {
          "id": "tentaculos_imobilizar",
          "name": "Tentáculos",
          "action_type": "passiva",
          "attack_index": 1,
          "hits_needed": 2,
          "dc": 17,
          "save": "fortitude",
          "escape_saves": [
            "fortitude"
          ],
          "max_targets": 2,
          "descricao": "Se dois Tentáculos acertarem o mesmo alvo, ele fica Imobilizado. Pode manter dois alvos. Escape: Fortitude CD 17."
        },
        {
          "id": "constricao_charcos",
          "name": "Constrição",
          "action_type": "passiva",
          "damage": "2d6+8",
          "damage_types": [
            "physical"
          ],
          "descricao": "No início do turno, criaturas Imobilizadas sofrem 2d6+8. Enquanto presas, não podem se afastar."
        },
        {
          "id": "ferrao_paralitico",
          "name": "Ferrão Paralítico",
          "action_type": "passiva",
          "attack_index": 3,
          "dc": 17,
          "save": "fortitude",
          "effect": "perde_movimento",
          "descricao": "Ao acertar o Ferrão, Fortitude CD 17; falha: perde a ação de movimento no próximo turno."
        },
        {
          "id": "nuvem_acida",
          "name": "Nuvem Ácida",
          "action_type": "acao",
          "cooldown_turns": 4,
          "range": 4,
          "radius": 1,
          "duration": 2,
          "initial_damage": "4d6",
          "tick_damage": "1d6",
          "damage_types": [
            "acid"
          ],
          "descricao": "Recarga 4 rodadas. Centro no alvo; raio 1. Causa 4d6 ao surgir e 1d6 no turno de cada criatura dentro da área."
        },
        {
          "id": "predador_implacavel",
          "name": "Predador Implacável",
          "action_type": "passiva",
          "max_targets": 2,
          "descricao": "Pode manter dois inimigos Imobilizados ao mesmo tempo."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "aberracao",
      "percepcao": 13
    },
    {
      "type": "tirano_da_mata",
      "name": "Tirano da Mata",
      "emoji": "🦖",
      "boss": false,
      "tier": 7,
      "cr": 7,
      "hp": 120,
      "ac": 22,
      "natural_armor": 9,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        2
      ],
      "porte": "grande",
      "image": "tirano_da_mata",
      "str_": 24,
      "dex": 16,
      "con_": 22,
      "int_": 3,
      "fort": 11,
      "ref_": 5,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 14,
          "damage": "2d10+10",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 14,
          "damage": "2d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Cauda",
          "atk_bonus": 14,
          "damage": "2d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "mandibulas_colossais",
          "name": "Mandíbulas Colossais",
          "action_type": "passiva",
          "attack_index": 0,
          "dc": 18,
          "save": "fortitude",
          "escape_saves": [
            "forca",
            "fortitude"
          ],
          "automatic_damage": "2d10+10",
          "max_targets": 1,
          "descricao": "Ao acertar a Mordida, Fortitude CD 18 ou fica Preso. O alvo acompanha o Tirano e sofre a Mordida no início do turno dele."
        },
        {
          "id": "arrastar",
          "name": "Arrastar",
          "action_type": "passiva",
          "descricao": "Uma criatura Presa acompanha todos os movimentos do Tirano, permanecendo adjacente."
        },
        {
          "id": "sacudida_brutal",
          "name": "Sacudida Brutal",
          "action_type": "acao",
          "cooldown_turns": 5,
          "damage": "4d6",
          "damage_types": [
            "physical"
          ],
          "throw_distance": 2,
          "descricao": "Recarga fixa de 5 rodadas. Uma criatura Presa sofre 4d6 e é arremessada 2 quadrados; depois deixa de estar Presa."
        },
        {
          "id": "investida_brutal",
          "name": "Investida Brutal",
          "action_type": "passiva",
          "attack_index": 0,
          "move_required": 3,
          "damage": "2d6",
          "damage_types": [
            "physical"
          ],
          "push": 1,
          "descricao": "Se mover pelo menos 3 quadrados antes da Mordida, causa +2d6 e empurra 1 quadrado."
        },
        {
          "id": "couro_espesso",
          "name": "Couro Espesso",
          "action_type": "passiva",
          "descricao": "RD 4 contra armas comuns."
        },
        {
          "id": "metabolismo_vulneravel",
          "name": "Metabolismo Vulnerável",
          "action_type": "passiva",
          "poison_save_penalty": -2,
          "poison_multiplier": 2,
          "descricao": "-2 em Fortitude contra venenos; dano de veneno dobrado; veneno ignora a RD."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "poison",
          "multiplier": 2,
          "descricao": "Metabolismo Vulnerável: dano de veneno dobrado."
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 4,
          "common_weapon_only": true
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "tirano_da_mata",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 12
    },
    {
      "type": "tirano_ancestral",
      "name": "Tirano Ancestral",
      "emoji": "🦖",
      "boss": false,
      "tier": 10,
      "cr": 10,
      "hp": 200,
      "ac": 26,
      "natural_armor": 12,
      "movement": 7,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        2,
        3
      ],
      "oriented": true,
      "porte": "grande",
      "image": "tirano_da_mata",
      "str_": 28,
      "dex": 18,
      "con_": 26,
      "int_": 3,
      "fort": 15,
      "ref_": 7,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 17,
          "damage": "3d10+12",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 17,
          "damage": "2d8+8",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Cauda",
          "atk_bonus": 17,
          "damage": "3d6+8",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "mandibulas_colossais",
          "name": "Mandíbulas Colossais",
          "action_type": "passiva",
          "attack_index": 0,
          "dc": 22,
          "save": "fortitude",
          "escape_saves": [
            "forca",
            "fortitude"
          ],
          "automatic_damage": "3d10+12",
          "max_targets": 1,
          "descricao": "Ao acertar a Mordida, Fortitude CD 22 ou fica Preso e sofre 3d10+12 no início do turno do Tirano."
        },
        {
          "id": "arrastar",
          "name": "Arrastar",
          "action_type": "passiva",
          "descricao": "Uma criatura Presa acompanha todos os movimentos do Tirano, permanecendo adjacente."
        },
        {
          "id": "sacudida_brutal",
          "name": "Sacudida Brutal",
          "action_type": "acao",
          "cooldown_turns": 4,
          "damage": "6d6",
          "damage_types": [
            "physical"
          ],
          "throw_distance": 3,
          "descricao": "Recarga fixa de 4 rodadas. Uma criatura Presa sofre 6d6 e é arremessada 3 quadrados; depois deixa de estar Presa."
        },
        {
          "id": "investida_brutal",
          "name": "Investida Brutal",
          "action_type": "passiva",
          "attack_index": 0,
          "move_required": 3,
          "damage": "2d6",
          "damage_types": [
            "physical"
          ],
          "push": 1,
          "descricao": "Se mover pelo menos 3 quadrados antes da Mordida, causa +2d6 e empurra 1 quadrado."
        },
        {
          "id": "engolir",
          "name": "Engolir",
          "action_type": "acao",
          "dc": 22,
          "save": "fortitude",
          "acid_damage": "3d6",
          "stomach_hp": 20,
          "escape_dc": 22,
          "descricao": "No início do turno, tenta engolir uma criatura Presa. Fortitude CD 22; falha: Engolida. O alvo sofre 3d6 ácido por turno e fica invisível para o exterior."
        },
        {
          "id": "abrir_caminho",
          "name": "Abrir Caminho",
          "action_type": "passiva",
          "damage_threshold": 20,
          "internal_damage": "2d6",
          "uses_per_combat": 1,
          "descricao": "A criatura Engolida pode atacar o estômago. Ao causar 20 dano interno, é cuspida; o monstro sofre 2d6 e perde o próximo ataque."
        },
        {
          "id": "passo_devastador",
          "name": "Passo Devastador",
          "action_type": "passiva",
          "move_required": 4,
          "damage": "3d6",
          "damage_types": [
            "physical"
          ],
          "push": 1,
          "descricao": "Após mover 4 ou mais quadrados, todas as criaturas adjacentes ao destino sofrem 3d6 e são empurradas 1 quadrado, inclusive aliados."
        },
        {
          "id": "couro_titanico",
          "name": "Couro Titânico",
          "action_type": "passiva",
          "descricao": "RD 7 contra armas comuns."
        },
        {
          "id": "metabolismo_instavel",
          "name": "Metabolismo Instável",
          "action_type": "passiva",
          "poison_save_penalty": -2,
          "poison_multiplier": 2,
          "descricao": "-2 em Fortitude contra venenos; dano de veneno dobrado; falha contra veneno também causa Lento por 1 rodada."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "poison",
          "multiplier": 2,
          "descricao": "Metabolismo Instável: dano de veneno dobrado."
        }
      ],
      "resistances": [
        {
          "type": "physical",
          "reduction": 7,
          "common_weapon_only": true
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "tirano_ancestral",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "ciclope",
      "name": "Ciclope",
      "emoji": "👁️",
      "boss": false,
      "tier": 5,
      "cr": 5,
      "hp": 86,
      "ac": 15,
      "natural_armor": 5,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "percepcao": 12,
      "size": [
        2,
        2
      ],
      "porte": "enorme",
      "image": "ciclope",
      "str_": 24,
      "dex": 10,
      "con_": 18,
      "int_": 6,
      "fort": 8,
      "ref_": 0,
      "will": 3,
      "save_bonuses": {
        "fortitude": 3
      },
      "save_penalties": {
        "reflexos": -2
      },
      "crit_vulnerability_min_nat_roll": 19,
      "attacks": [
        {
          "name": "Clava Gigante",
          "atk_bonus": 8,
          "damage": "2d6+7",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "melee": true,
          "reach": 2,
          "ciclope_melee": true
        }
      ],
      "special_abilities": [
        {
          "id": "alcance_enorme",
          "name": "Alcance Enorme",
          "action_type": "passiva",
          "reach": 2,
          "descricao": "Ataques corpo a corpo atingem alvos a até 2 quadrados."
        },
        {
          "id": "arremesso_colossal",
          "name": "Arremesso Colossal",
          "action_type": "acao",
          "range": 8,
          "attack_bonus": 1,
          "attack_attribute": "dex",
          "damage": "2d6",
          "damage_attribute": "str_",
          "apply_attribute_damage": true,
          "attribute_mod_base": 0,
          "descricao": "Arremessa um objeto a até 8 quadrados; usa DES no ataque e o bônus de FOR no dano."
        },
        {
          "id": "golpe_esmagador",
          "name": "Golpe Esmagador",
          "action_type": "passiva",
          "attack_index": 0,
          "dc": 17,
          "save": "fortitude",
          "effect": "perde_movimento",
          "descricao": "Ao acertar a Clava Gigante, Fortitude CD 17; falha: perde a próxima ação de movimento."
        },
        {
          "id": "investida_colossal",
          "name": "Investida Colossal",
          "action_type": "passiva",
          "attack_index": 0,
          "move_required": 3,
          "straight": true,
          "attack_bonus": 2,
          "damage_bonus": 4,
          "descricao": "Após mover 3 ou mais quadrados em linha reta antes da Clava: +2 no ataque e +4 no dano."
        },
        {
          "id": "pisoteio_colossal",
          "name": "Pisoteio Colossal",
          "action_type": "passiva",
          "move_required": 4,
          "straight": true,
          "damage": "2d6",
          "damage_attribute": "str_",
          "descricao": "Após mover 4 ou mais quadrados em linha reta, personagens atravessados sofrem 2d6 + FOR."
        },
        {
          "id": "vigor_colossal",
          "name": "Vigor Colossal",
          "action_type": "passiva",
          "save_bonus": {
            "fortitude": 3
          },
          "descricao": "+3 em todos os testes de Fortitude."
        },
        {
          "id": "presenca_aterradora",
          "name": "Presença Aterradora",
          "action_type": "passiva",
          "radius": 4,
          "dc": 13,
          "save": "vontade",
          "attack_penalty": -1,
          "duration_rounds": 1,
          "descricao": "No início do combate, heróis em até 4 quadrados testam Vontade; falha: -1 no ataque na primeira rodada."
        },
        {
          "id": "furia_selvagem_ciclope",
          "name": "Fúria Selvagem",
          "action_type": "passiva",
          "threshold": 0.5,
          "attack_bonus": 2,
          "damage_bonus": 4,
          "ac_penalty": -4,
          "descricao": "Com metade dos PV ou menos: +2 no ataque, +4 no dano e -4 na CA."
        },
        {
          "id": "visao_limitada_ciclope",
          "name": "Visão Limitada",
          "action_type": "passiva",
          "hide_bonus": 2,
          "descricao": "Personagens usando Esconder-se recebem +2 no teste contra o Ciclope."
        },
        {
          "id": "ponto_cego_ciclope",
          "name": "Ponto Cego",
          "action_type": "passiva",
          "crit_min_nat_roll": 19,
          "descricao": "Resultados naturais 19 ou 20 contra o Ciclope são ameaças de crítico."
        },
        {
          "id": "cercado_ciclope",
          "name": "Cercado",
          "action_type": "passiva",
          "attack_bonus": 2,
          "min_attackers": 2,
          "descricao": "Quando dois ou mais heróis o atacam, todos recebem +2 no ataque contra ele."
        },
        {
          "id": "reflexos_lentos_ciclope",
          "name": "Reflexos Lentos",
          "action_type": "passiva",
          "save_penalty": {
            "reflexos": -2
          },
          "descricao": "Sofre -2 em todos os testes de Reflexos."
        }
      ],
      "immunities": [],
      "weaknesses": [
        {
          "type": "ciclope_olho_unico",
          "nd_penalty": 0.28,
          "descricao": "Olho Único: furtividade +2, críticos naturais 19–20, Reflexos -2 e vulnerável quando cercado."
        }
      ],
      "resistances": [],
      "loot_table": {
        "1-50": {
          "tipo": "item",
          "id": "espada2m"
        },
        "51-75": {
          "tipo": "item",
          "id": "joia"
        },
        "76-100": null
      },
      "ai_type": "ciclope",
      "undead": false,
      "subtipo": "besta_magica"
    },
    {
      "type": "gigante_guerra",
      "name": "Gigante da Guerra",
      "emoji": "🗿",
      "boss": false,
      "tier": 7,
      "cr": 7,
      "hp": 60,
      "ac": 17,
      "natural_armor": 5,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "percepcao": 13,
      "size": [
        2,
        2
      ],
      "porte": "enorme",
      "image": "gigante_guerreiro",
      "str_": 22,
      "dex": 14,
      "con_": 20,
      "int_": 12,
      "fort": 10,
      "ref_": 4,
      "will": 5,
      "save_bonuses": {
        "fortitude": 3
      },
      "weapon_options": [
        {
          "id": "espada_longa_colossal",
          "name": "Espada Longa Colossal",
          "damage": "2d8+6",
          "reach": 2,
          "two_handed": false,
          "shield_compatible": true
        },
        {
          "id": "machado_orc_colossal",
          "name": "Machado Orc Colossal",
          "damage": "2d10+6",
          "reach": 2,
          "two_handed": true,
          "shield_compatible": false
        },
        {
          "id": "lanca_longa_colossal",
          "name": "Lança Longa Colossal",
          "damage": "2d8+6",
          "reach_straight": 4,
          "reach_diagonal": 2,
          "adjacent": true,
          "two_handed": false,
          "shield_compatible": true
        },
        {
          "id": "alabarda_colossal",
          "name": "Alabarda Colossal",
          "damage": "2d10+6",
          "reach_straight": 4,
          "reach_diagonal": 2,
          "two_handed": true,
          "shield_compatible": false
        }
      ],
      "shield_option": {
        "id": "escudo_gigante",
        "name": "Escudo Gigante",
        "ac_bonus": 2,
        "equipped_by_default": false
      },
      "attacks": [
        {
          "name": "Espada Longa Colossal",
          "atk_bonus": 9,
          "damage": "2d8+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "attack_attribute": "str_",
          "apply_attribute_damage": false,
          "melee": true,
          "reach": 2,
          "ciclope_melee": true
        }
      ],
      "special_abilities": [
        {
          "id": "alcance_enorme",
          "name": "Alcance Enorme",
          "action_type": "passiva",
          "reach": 2,
          "descricao": "Ataques corpo a corpo atingem alvos a até 2 quadrados."
        },
        {
          "id": "arremesso_colossal",
          "name": "Arremesso Colossal",
          "action_type": "acao",
          "range": 8,
          "attack_bonus": 7,
          "attack_attribute": "dex",
          "damage": "2d6",
          "damage_attribute": "str_",
          "apply_attribute_damage": true,
          "descricao": "Arremessa um objeto a até 8 quadrados; usa DES no ataque e FOR no dano."
        },
        {
          "id": "investida_colossal",
          "name": "Investida Colossal",
          "action_type": "passiva",
          "move_required": 3,
          "straight": true,
          "attack_bonus": 2,
          "damage_bonus": 4,
          "descricao": "Após mover 3 ou mais quadrados em linha reta antes do ataque: +2 no ataque e +4 no dano."
        },
        {
          "id": "pisoteio_colossal",
          "name": "Pisoteio Colossal",
          "action_type": "passiva",
          "move_required": 4,
          "straight": true,
          "damage": "2d6",
          "damage_attribute": "str_",
          "descricao": "Após mover 4 ou mais quadrados em linha reta, personagens atravessados sofrem 2d6 + FOR."
        },
        {
          "id": "vigor_colossal",
          "name": "Vigor Colossal",
          "action_type": "passiva",
          "save_bonus": {
            "fortitude": 3
          },
          "descricao": "+3 em todos os testes de Fortitude."
        },
        {
          "id": "presenca_aterradora",
          "name": "Presença Aterradora",
          "action_type": "passiva",
          "radius": 4,
          "dc": 13,
          "save": "vontade",
          "attack_penalty": -1,
          "duration_rounds": 1,
          "descricao": "No início do combate, heróis em até 4 quadrados testam Vontade; falha: -1 no ataque na primeira rodada."
        },
        {
          "id": "mira_certeira",
          "name": "Mira Certeira",
          "action_type": "acao_bonus",
          "cooldown_turns": 3,
          "attack_bonus": 2,
          "descricao": "Recarga 3 rodadas. Recebe +2 na próxima jogada de ataque."
        },
        {
          "id": "furia_berserker",
          "name": "Fúria Berserker",
          "action_type": "acao",
          "cooldown_turns": 8,
          "extra_attacks": 1,
          "descricao": "Recarga 8 rodadas. Realiza um ataque adicional nesta rodada."
        },
        {
          "id": "investida_heroica",
          "name": "Investida Heroica",
          "action_type": "acao_bonus",
          "cooldown_turns": 5,
          "movement_multiplier": 2,
          "damage_bonus": 2,
          "descricao": "Recarga 5 rodadas. Dobra o deslocamento nesta rodada e recebe +2 no dano do próximo ataque. Pode combinar com Investida e Pisoteio Colossais."
        },
        {
          "id": "arsenal_colossal",
          "name": "Arsenal Colossal",
          "action_type": "passiva",
          "descricao": "Pode usar Espada Longa Colossal, Machado Orc Colossal, Lança Longa Colossal ou Alabarda Colossal. Armas de duas mãos não podem usar o Escudo Gigante."
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "resistances": [],
      "loot_table": {
        "1-25": {
          "tipo": "item",
          "id": "espada_longa_colossal"
        },
        "26-50": {
          "tipo": "item",
          "id": "machado_orc_colossal"
        },
        "51-75": {
          "tipo": "item",
          "id": "lanca_longa_colossal"
        },
        "76-100": {
          "tipo": "item",
          "id": "alabarda_colossal"
        }
      },
      "loot_drops": [
        {
          "kind": "item",
          "item_id": "armadura_pesada_gigante",
          "chance": 50
        },
        {
          "kind": "item",
          "item_id": "joia",
          "chance": 25
        }
      ],
      "ai_type": "gigante_guerra",
      "undead": false,
      "subtipo": "raca_padrao"
    },
    {
      "type": "gigante_runico",
      "name": "Gigante Rúnico",
      "emoji": "🗿",
      "boss": false,
      "tier": 8,
      "cr": 8,
      "hp": 70,
      "ac": 19,
      "natural_armor": 8,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "percepcao": 13,
      "size": [
        2,
        2
      ],
      "porte": "enorme",
      "image": "gigante_runas",
      "caster_level": 6,
      "str_": 20,
      "dex": 12,
      "con_": 22,
      "int_": 15,
      "fort": 11,
      "ref_": 3,
      "will": 8,
      "attacks": [
        {
          "name": "Martelo Rúnico Colossal",
          "atk_bonus": 10,
          "damage": "2d8+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "attack_attribute": "str_",
          "apply_attribute_damage": false,
          "melee": true,
          "reach": 2,
          "ciclope_melee": true
        }
      ],
      "special_abilities": [
        {
          "id": "alcance_enorme",
          "name": "Alcance Enorme",
          "action_type": "passiva",
          "reach": 2,
          "descricao": "Ataques corpo a corpo atingem alvos a até 2 quadrados."
        },
        {
          "id": "investida_colossal",
          "name": "Investida Colossal",
          "action_type": "passiva",
          "move_required": 3,
          "straight": true,
          "attack_bonus": 2,
          "damage_bonus": 4,
          "descricao": "Após mover 3 ou mais quadrados em linha reta antes do ataque: +2 no ataque e +4 no dano."
        },
        {
          "id": "vigor_colossal",
          "name": "Vigor Colossal",
          "action_type": "passiva",
          "save_bonus": {
            "fortitude": 3
          },
          "descricao": "+3 em todos os testes de Fortitude."
        },
        {
          "id": "presenca_aterradora",
          "name": "Presença Aterradora",
          "action_type": "passiva",
          "radius": 4,
          "dc": 16,
          "save": "vontade",
          "attack_penalty": -1,
          "duration_rounds": 1,
          "descricao": "No início do combate, heróis em até 4 quadrados testam Vontade; falha: -1 no ataque na primeira rodada."
        },
        {
          "id": "regeneracao_runica",
          "name": "Regeneração Rúnica",
          "action_type": "acao_bonus",
          "cooldown_turns": 6,
          "heal": 2,
          "duration_dice": "1d4+2",
          "descricao": "Recarga 6 rodadas. Recupera 2 HP no início de cada turno durante 1d4+2 rodadas."
        },
        {
          "id": "passo_fantasma_runico",
          "name": "Passo Fantasma",
          "action_type": "acao_bonus",
          "cooldown_turns": 5,
          "bonus_mov": 2,
          "duration_dice": "1d4",
          "descricao": "Recarga 5 rodadas. Como o Passo Fantasma do Guerreiro: +2 movimento nesta rodada e atravessa obstáculos baixos durante a janela."
        },
        {
          "id": "provocacao_runica",
          "name": "Provocação",
          "action_type": "acao_bonus",
          "cooldown_turns": 6,
          "range": 4,
          "duration_rounds": 3,
          "descricao": "Recarga 6 rodadas. Provoca um herói a até 4 quadrados, forçando-o a enfrentar o Gigante Rúnico por 3 rodadas."
        },
        {
          "id": "medo",
          "name": "Medo",
          "action_type": "magia",
          "uses_per_combat": 1,
          "descricao": "Igual à magia Medo; 1 vez por encontro."
        },
        {
          "id": "amaldicoar",
          "name": "Amaldiçoar",
          "action_type": "magia",
          "uses_per_combat": 1,
          "descricao": "Igual à magia Amaldiçoar; 1 vez por encontro."
        },
        {
          "id": "bola_fogo",
          "name": "Bola de Fogo",
          "action_type": "magia",
          "uses_per_combat": 1,
          "descricao": "Igual à magia Bola de Fogo, conjurador de 6º nível; 1 vez por encontro."
        }
      ],
      "monster_spells": [
        {
          "id": "medo",
          "limit_mode": "encounter",
          "uses_per_combat": 1
        },
        {
          "id": "amaldicoar",
          "limit_mode": "encounter",
          "uses_per_combat": 1
        },
        {
          "id": "bola_fogo",
          "limit_mode": "encounter",
          "uses_per_combat": 1
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "resistances": [],
      "loot_table": {
        "1-100": {
          "tipo": "item",
          "id": "martelo_runico_colossal"
        }
      },
      "loot_drops": [
        {
          "kind": "item",
          "item_id": "armadura_runica",
          "chance": 50
        },
        {
          "kind": "item",
          "item_id": "runa_ancestral",
          "chance": 50
        },
        {
          "kind": "item",
          "item_id": "joia",
          "chance": 25
        }
      ],
      "ai_type": "gigante_runico",
      "undead": false,
      "subtipo": "besta_magica"
    },
    {
      "type": "garaloux_jovem",
      "name": "Garaloux Jovem",
      "emoji": "🦁",
      "boss": false,
      "tier": 3,
      "cr": 3,
      "hp": 50,
      "ac": 18,
      "natural_armor": 5,
      "movement": 7,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "oriented": true,
      "porte": "grande",
      "image": "garaloux",
      "str_": 16,
      "dex": 16,
      "con_": 16,
      "int_": 4,
      "fort": 6,
      "ref_": 5,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 6,
          "damage": "1d8+4",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 6,
          "damage": "1d6+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Chifres",
          "atk_bonus": 6,
          "damage": "1d6+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "salto_selvagem",
          "name": "Salto Selvagem",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "reflex_dc": 14,
          "escape_dc": 14,
          "save": "reflexos",
          "escape_saves": [
            "forca"
          ],
          "effect": "imobilizado",
          "collision_damage": "1d6",
          "descricao": "Se mover 3 quadrados antes da Chifrada, o alvo testa Reflexos CD 14 ou fica Imobilizado; escapa com Força CD 14. Se estiver contra uma parede, sofre +1d6 de colisão."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "garaloux_adulto",
      "name": "Garaloux Adulto",
      "emoji": "🦁",
      "boss": false,
      "tier": 5,
      "cr": 5,
      "hp": 82,
      "ac": 21,
      "natural_armor": 8,
      "movement": 7,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "oriented": true,
      "porte": "grande",
      "image": "garaloux",
      "str_": 18,
      "dex": 16,
      "con_": 18,
      "int_": 4,
      "fort": 8,
      "ref_": 5,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 9,
          "damage": "2d6+7",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 9,
          "damage": "1d8+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Chifres",
          "atk_bonus": 9,
          "damage": "1d8+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "salto_selvagem",
          "name": "Salto Selvagem",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "reflex_dc": 16,
          "escape_dc": 16,
          "save": "reflexos",
          "escape_saves": [
            "forca"
          ],
          "effect": "imobilizado",
          "collision_damage": "1d6",
          "descricao": "Se mover 3 quadrados antes da Chifrada, o alvo testa Reflexos CD 16 ou fica Imobilizado; escapa com Força CD 16. Se estiver contra uma parede, sofre +1d6 de colisão."
        },
        {
          "id": "dilacerar",
          "name": "Dilacerar",
          "action_type": "passiva",
          "attack_index": 1,
          "hits_needed": 2,
          "damage": "2d6",
          "damage_types": [
            "physical"
          ],
          "causa_sangramento": true,
          "descricao": "Se as duas Garras acertarem o mesmo alvo no turno, ele sofre 2d6 de dano extra uma vez e começa a Sangrar."
        },
        {
          "id": "investida_brutal",
          "name": "Investida Brutal",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "damage": "2d6",
          "push": 1,
          "descricao": "Se mover 3 quadrados antes da Chifrada, causa +2d6 e empurra o alvo 1 quadrado."
        },
        {
          "id": "furia_garaloux",
          "name": "Frenesi",
          "action_type": "passiva",
          "threshold": 0.5,
          "attack_bonus": 2,
          "damage_bonus": 2,
          "descricao": "Ao atingir metade da Vida ou menos, recebe +2 no ataque e +2 no dano."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "garaloux_alfa",
      "name": "Garaloux Alfa",
      "emoji": "🦁",
      "boss": false,
      "tier": 8,
      "cr": 8,
      "hp": 145,
      "ac": 25,
      "natural_armor": 11,
      "movement": 7,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "oriented": true,
      "porte": "grande",
      "image": "garaloux",
      "str_": 22,
      "dex": 18,
      "con_": 22,
      "int_": 4,
      "fort": 11,
      "ref_": 7,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 12,
          "damage": "3d6+9",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 12,
          "damage": "2d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 2
        },
        {
          "name": "Chifres",
          "atk_bonus": 12,
          "damage": "2d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "salto_selvagem",
          "name": "Salto Selvagem",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "reflex_dc": 18,
          "escape_dc": 18,
          "save": "reflexos",
          "escape_saves": [
            "forca"
          ],
          "effect": "imobilizado",
          "collision_damage": "1d6",
          "descricao": "Se mover 3 quadrados antes da Chifrada, o alvo testa Reflexos CD 18 ou fica Imobilizado; escapa com Força CD 18. Se estiver contra uma parede, sofre +1d6 de colisão."
        },
        {
          "id": "dilacerar",
          "name": "Dilacerar",
          "action_type": "passiva",
          "attack_index": 1,
          "hits_needed": 2,
          "damage": "2d6",
          "damage_types": [
            "physical"
          ],
          "causa_sangramento": true,
          "descricao": "Se as duas Garras acertarem o mesmo alvo no turno, ele sofre 2d6 de dano extra uma vez e começa a Sangrar."
        },
        {
          "id": "investida_brutal",
          "name": "Investida Brutal",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "damage": "4d6",
          "push": 1,
          "descricao": "Se mover 3 quadrados antes da Chifrada, causa +4d6, aplica Hemorragia e empurra o alvo 1 quadrado."
        },
        {
          "id": "furia_garaloux",
          "name": "Frenesi",
          "action_type": "passiva",
          "threshold": 0.5,
          "attack_bonus": 2,
          "damage_bonus": 2,
          "descricao": "Ao atingir metade da Vida ou menos, recebe +2 no ataque e +2 no dano."
        },
        {
          "id": "causar_hemorragia",
          "name": "Causar Hemorragia",
          "action_type": "passiva",
          "attack_index": 2,
          "cooldown_turns": 4,
          "requires_investida": true,
          "descricao": "A Investida Brutal da Chifrada aplica Hemorragia ao acertar; recarga de 4 rodadas."
        },
        {
          "id": "predador_supremo",
          "name": "Predador Supremo",
          "action_type": "passiva",
          "trigger": "kill",
          "attack_index": 0,
          "chain": false,
          "descricao": "Sempre que eliminar uma criatura, realiza imediatamente uma Mordida adicional. A Mordida adicional não gera outra reação."
        }
      ],
      "immunities": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "molochus_jovem",
      "name": "Molochus Jovem",
      "emoji": "🔥",
      "boss": false,
      "tier": 4,
      "cr": 4,
      "hp": 64,
      "ac": 20,
      "natural_armor": 7,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "oriented": true,
      "porte": "grande",
      "image": "molochos",
      "str_": 18,
      "dex": 16,
      "con_": 18,
      "int_": 4,
      "fort": 8,
      "ref_": 5,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 8,
          "damage": "2d6+5",
          "damage_types": [
            "physical"
          ],
          "fire_damage": "1d4",
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 8,
          "damage": "1d6+3",
          "damage_types": [
            "physical"
          ],
          "fire_damage": "1d4",
          "num_attacks": 2
        },
        {
          "name": "Chifrada",
          "atk_bonus": 8,
          "damage": "1d8+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "aura_escaldante",
          "name": "Aura Escaldante",
          "action_type": "passiva",
          "radius": 1,
          "damage": "1d4",
          "damage_types": [
            "fire"
          ],
          "descricao": "Criaturas adjacentes sofrem 1d4 de fogo no início do próprio turno."
        },
        {
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "1d4",
          "damage_types": [
            "fire"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d4 de dano de fogo."
        }
      ],
      "immunities": [
        "fire"
      ],
      "weaknesses": [
        {
          "type": "cold",
          "multiplier": 2,
          "descricao": "Gelo causa dano dobrado."
        },
        {
          "type": "water",
          "multiplier": 2,
          "descricao": "Água causa dano dobrado."
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "molochus_adulto",
      "name": "Molochus Adulto",
      "emoji": "🔥",
      "boss": false,
      "tier": 6,
      "cr": 6,
      "hp": 96,
      "ac": 22,
      "natural_armor": 9,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "oriented": true,
      "porte": "grande",
      "image": "molochos",
      "str_": 20,
      "dex": 16,
      "con_": 20,
      "int_": 4,
      "fort": 10,
      "ref_": 5,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 11,
          "damage": "2d8+8",
          "damage_types": [
            "physical"
          ],
          "fire_damage": "1d6",
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 11,
          "damage": "1d8+5",
          "damage_types": [
            "physical"
          ],
          "fire_damage": "1d6",
          "num_attacks": 2
        },
        {
          "name": "Chifrada",
          "atk_bonus": 11,
          "damage": "2d6+5",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "aura_escaldante",
          "name": "Aura Escaldante",
          "action_type": "passiva",
          "radius": 1,
          "damage": "1d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Criaturas adjacentes sofrem 1d6 de fogo no início do próprio turno."
        },
        {
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "1d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d6 de dano de fogo."
        },
        {
          "id": "investida_flamejante",
          "name": "Investida Flamejante",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "damage": "2d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Após mover 3 quadrados, a Chifrada causa +2d6 de fogo."
        },
        {
          "id": "explosao_vapor",
          "name": "Explosão de Vapor",
          "action_type": "acao",
          "cooldown_turns": 6,
          "range": 3,
          "shape": "cone",
          "damage": "4d6",
          "damage_types": [
            "fire"
          ],
          "save": "reflexos",
          "dc": 16,
          "success_effect": "metade",
          "descricao": "Recarga fixa de 6 rodadas. Cone de 3 quadrados; Reflexos CD 16 reduz 4d6 de fogo à metade."
        },
        {
          "id": "morte_explosiva",
          "name": "Morte Explosiva",
          "action_type": "passiva",
          "radius": 2,
          "damage": "4d6",
          "damage_types": [
            "fire"
          ],
          "save": "reflexos",
          "dc": 16,
          "duration": 2,
          "tick_damage": "1d6",
          "descricao": "Ao morrer, explode em raio 2. Reflexos CD 16 reduz 4d6 à metade; o chão fica em chamas por 2 rodadas."
        }
      ],
      "immunities": [
        "fire"
      ],
      "weaknesses": [
        {
          "type": "cold",
          "multiplier": 2,
          "descricao": "Gelo causa dano dobrado."
        },
        {
          "type": "water",
          "multiplier": 2,
          "descricao": "Água causa dano dobrado."
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "molochus_anciao",
      "name": "Molochus Ancião",
      "emoji": "🔥",
      "boss": false,
      "tier": 10,
      "cr": 10,
      "hp": 170,
      "ac": 26,
      "natural_armor": 12,
      "movement": 6,
      "vision_base": 0,
      "size": [
        2,
        1
      ],
      "oriented": true,
      "porte": "grande",
      "image": "molochos",
      "str_": 24,
      "dex": 18,
      "con_": 24,
      "int_": 4,
      "fort": 13,
      "ref_": 7,
      "will": -2,
      "attacks": [
        {
          "name": "Mordida",
          "atk_bonus": 15,
          "damage": "3d8+10",
          "damage_types": [
            "physical"
          ],
          "fire_damage": "2d6",
          "num_attacks": 1
        },
        {
          "name": "Garras",
          "atk_bonus": 15,
          "damage": "2d6+6",
          "damage_types": [
            "physical"
          ],
          "fire_damage": "2d6",
          "num_attacks": 2
        },
        {
          "name": "Chifrada",
          "atk_bonus": 15,
          "damage": "3d6+6",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1
        }
      ],
      "special_abilities": [
        {
          "id": "aura_escaldante",
          "name": "Aura Escaldante",
          "action_type": "passiva",
          "radius": 1,
          "damage": "2d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Criaturas adjacentes sofrem 2d6 de fogo no início do próprio turno."
        },
        {
          "id": "dano_retaliacao",
          "name": "Dano de Retaliação",
          "action_type": "passiva",
          "damage": "2d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 2d6 de dano de fogo."
        },
        {
          "id": "investida_flamejante",
          "name": "Investida Flamejante",
          "action_type": "passiva",
          "attack_index": 2,
          "move_required": 3,
          "damage": "2d6",
          "damage_types": [
            "fire"
          ],
          "descricao": "Após mover 3 quadrados, a Chifrada causa +2d6 de fogo."
        },
        {
          "id": "explosao_vapor",
          "name": "Explosão de Vapor",
          "action_type": "acao",
          "cooldown_turns": 6,
          "range": 3,
          "shape": "cone",
          "damage": "8d6",
          "damage_types": [
            "fire"
          ],
          "save": "reflexos",
          "dc": 18,
          "success_effect": "metade",
          "descricao": "Recarga fixa de 6 rodadas. Cone de 3 quadrados; Reflexos CD 18 reduz 8d6 de fogo à metade."
        },
        {
          "id": "morte_explosiva",
          "name": "Morte Explosiva",
          "action_type": "passiva",
          "radius": 3,
          "damage": "8d6",
          "damage_types": [
            "fire"
          ],
          "save": "reflexos",
          "dc": 18,
          "duration": 3,
          "tick_damage": "1d6",
          "descricao": "Ao morrer, explode em raio 3. Reflexos CD 18 reduz 8d6 à metade; o chão fica em chamas por 3 rodadas."
        }
      ],
      "immunities": [
        "fire"
      ],
      "weaknesses": [
        {
          "type": "cold",
          "multiplier": 2,
          "descricao": "Gelo causa dano dobrado."
        },
        {
          "type": "water",
          "multiplier": 2,
          "descricao": "Água causa dano dobrado."
        }
      ],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "agressivo",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "medusa",
      "name": "Medusa",
      "emoji": "🐍",
      "boss": false,
      "tier": 5,
      "cr": 5,
      "hp": 43,
      "ac": 15,
      "natural_armor": 3,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "medusa",
      "str_": 10,
      "dex": 15,
      "con_": 16,
      "int_": 12,
      "fort": 5,
      "ref_": 4,
      "will": 4,
      "attacks": [
        {
          "name": "Arco Longo",
          "atk_bonus": 5,
          "damage": "1d8+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "range": 10,
          "categoria": "perfurante",
          "on_hit": "veneno_medusa",
          "poison_dc": 15
        },
        {
          "name": "Adaga",
          "atk_bonus": 5,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "categoria": "perfurante",
          "on_hit": null
        },
        {
          "name": "Cobras do Cabelo",
          "atk_bonus": 5,
          "damage": "1d4+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "categoria": "perfurante",
          "on_hit": "veneno_medusa",
          "poison_dc": 15
        }
      ],
      "special_abilities": [
        {
          "id": "olhar_petrificante",
          "name": "Olhar Petrificante",
          "action_type": "passiva",
          "save": "vontade",
          "dc": 15,
          "descricao": "Sempre ativo. Uma criatura que veja a Medusa testa Vontade; falha gera uma marca de Petrificação e sucesso uma marca de Resistência. Três marcas de Petrificação petrificam; três de Resistência encerram o efeito."
        },
        {
          "id": "veneno_medusa",
          "name": "Veneno da Medusa",
          "action_type": "passiva",
          "poison_dc": 15,
          "descricao": "Fortitude CD 15; falha: +2d4 de veneno e -2 FOR/-2 CON por 1d6 rodadas; sucesso: +2 de veneno. O efeito não acumula e reinicia sua duração."
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "medusa",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "grande_medusa",
      "name": "Grande Medusa",
      "emoji": "🐍",
      "boss": false,
      "tier": 7,
      "cr": 7,
      "hp": 72,
      "ac": 15,
      "natural_armor": 3,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "medusa",
      "str_": 10,
      "dex": 15,
      "con_": 16,
      "int_": 12,
      "fort": 5,
      "ref_": 4,
      "will": 4,
      "attacks": [
        {
          "name": "Arco Longo",
          "atk_bonus": 5,
          "damage": "1d8+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "range": 10,
          "categoria": "perfurante",
          "on_hit": "veneno_medusa",
          "poison_dc": 15
        },
        {
          "name": "Adaga",
          "atk_bonus": 5,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "categoria": "perfurante",
          "on_hit": null
        },
        {
          "name": "Cobras do Cabelo",
          "atk_bonus": 5,
          "damage": "1d4+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "categoria": "perfurante",
          "on_hit": "veneno_medusa",
          "poison_dc": 15
        }
      ],
      "special_abilities": [
        {
          "id": "olhar_petrificante",
          "name": "Olhar Petrificante",
          "action_type": "passiva",
          "save": "vontade",
          "dc": 15,
          "descricao": "Sempre ativo; acumula marcas de Petrificação ou Resistência enquanto a criatura vê a Medusa."
        },
        {
          "id": "veneno_medusa",
          "name": "Veneno da Medusa",
          "action_type": "passiva",
          "poison_dc": 15,
          "descricao": "Fortitude CD 15; falha: +2d4 de veneno e -2 FOR/-2 CON por 1d6 rodadas; sucesso: +2 de veneno."
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "medusa",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    },
    {
      "type": "grande_gorgona",
      "name": "Grande Gorgona",
      "emoji": "🐍",
      "boss": false,
      "tier": 9,
      "cr": 9,
      "hp": 127,
      "ac": 15,
      "natural_armor": 3,
      "movement": 6,
      "movement_exception": true,
      "vision_base": 0,
      "size": [
        1,
        1
      ],
      "porte": "medio",
      "image": "medusa",
      "str_": 10,
      "dex": 15,
      "con_": 16,
      "int_": 12,
      "fort": 5,
      "ref_": 4,
      "will": 4,
      "attacks": [
        {
          "name": "Arco Longo",
          "atk_bonus": 5,
          "damage": "1d8+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "range": 10,
          "categoria": "perfurante",
          "on_hit": "veneno_medusa",
          "poison_dc": 15
        },
        {
          "name": "Adaga",
          "atk_bonus": 5,
          "damage": "1d4+2",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "categoria": "perfurante",
          "on_hit": null
        },
        {
          "name": "Cobras do Cabelo",
          "atk_bonus": 5,
          "damage": "1d4+3",
          "damage_types": [
            "physical"
          ],
          "num_attacks": 1,
          "categoria": "perfurante",
          "on_hit": "veneno_medusa",
          "poison_dc": 15
        }
      ],
      "special_abilities": [
        {
          "id": "olhar_petrificante",
          "name": "Olhar Petrificante",
          "action_type": "passiva",
          "save": "vontade",
          "dc": 16,
          "descricao": "Sempre ativo; CD 16. Acumula marcas de Petrificação ou Resistência enquanto a criatura vê a Gorgona."
        },
        {
          "id": "veneno_medusa",
          "name": "Veneno da Medusa",
          "action_type": "passiva",
          "poison_dc": 15,
          "descricao": "Fortitude CD 15; falha: +2d4 de veneno e -2 FOR/-2 CON por 1d6 rodadas; sucesso: +2 de veneno."
        }
      ],
      "immunities": [],
      "weaknesses": [],
      "loot_table": {
        "1-100": null
      },
      "ai_type": "medusa",
      "undead": false,
      "subtipo": "besta_magica",
      "percepcao": 13
    }
  ],
  "monster_abilities": [
    {
      "id": "agarrar_aereo",
      "source": "monstro",
      "name": "Agarrão Aéreo",
      "icon": "🦅",
      "action_type": "passiva",
      "dc": 14,
      "save": "forca",
      "escape_saves": [
        "forca"
      ],
      "max_targets": 1,
      "automatic_damage": "1d4+2",
      "damage_types": [
        "physical"
      ],
      "damage_threshold": 5,
      "height_loss_per_threshold": 1,
      "descricao": "Ao acertar uma garra, Força CD 14 ou fica preso. A presa acompanha a Harpia horizontal e verticalmente; sofre 1d4+2 automático no início do turno dela. Cada 5 dano recebido pela Harpia reduz sua altura em 1. Escapar ou ser solto provoca queda."
    },
    {
      "id": "soltar_presa",
      "source": "monstro",
      "name": "Soltar Presa",
      "icon": "🪶",
      "action_type": "acao_livre",
      "ai_release_height": 4,
      "descricao": "Ação livre. Solta a criatura agarrada; ela sofre dano de queda conforme a altura atual."
    },
    {
      "id": "investida_poderosa_minotauro",
      "source": "monstro",
      "name": "Investida Poderosa",
      "icon": "🐂",
      "action_type": "passiva",
      "move_required": 3,
      "damage": "4d6+6",
      "attack_bonus": 4,
      "descricao": "Após mover pelo menos 3 casas, faz um único ataque de chifres (4d6+6) e não realiza outros ataques no turno."
    },
    {
      "id": "faro_implacavel_minotauro",
      "source": "monstro",
      "name": "Faro Implacável",
      "icon": "👃",
      "action_type": "passiva",
      "descricao": "Heróis não conseguem se esconder do minotauro com invisibilidade ou habilidades de furtividade do Ladino."
    },
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
      "id": "causar_sangramento",
      "source": "monstro",
      "name": "Causar Sangramento",
      "icon": "🩸",
      "action_type": "passiva",
      "descricao": "Ataques que acertam aplicam Sangramento; acertos críticos também aplicam Hemorragia."
    },
    {
      "id": "causar_hemorragia",
      "source": "monstro",
      "name": "Causar Hemorragia",
      "icon": "🩸",
      "action_type": "passiva",
      "attack_index": 0,
      "cooldown_turns": 4,
      "descricao": "O ataque selecionado aplica Hemorragia ao acertar e entra em recarga."
    },
    {
      "id": "regeneracao_troll",
      "name": "Regeneração Troll",
      "action_type": "passiva",
      "amount": 4,
      "descricao": "Recupera 4 PV no início do turno; ácido bloqueia a regeneração. Se chegar a 0 PV, retorna com 1 PV no próximo turno, exceto se o dano final tiver sido fogo ou se a regeneração estiver bloqueada por ácido.",
      "source": "monstro"
    },
    {
      "id": "golpe_devastador_troll",
      "name": "Golpe Devastador",
      "action_type": "acao_bonus",
      "cooldown_turns": 4,
      "descricao": "No próximo ataque de clava, dobra os dados de dano. Recarga: 4 rodadas.",
      "source": "monstro"
    },
    {
      "id": "pressao_constante_troll",
      "name": "Pressão Constante",
      "action_type": "acao_bonus",
      "cooldown_turns": 4,
      "range": 1,
      "ca_penalty": 2,
      "duration_rounds": 2,
      "descricao": "Um herói adjacente sofre -2 CA por 2 rodadas. Recarga: 4 rodadas.",
      "source": "monstro"
    },
    {
      "id": "investida_brutal_troll",
      "name": "Investida Brutal",
      "action_type": "passiva",
      "cooldown_turns": 5,
      "move_required": 3,
      "damage": "2d6",
      "push": 1,
      "descricao": "Após mover pelo menos 3 casas antes do ataque, acrescenta 2d6 de dano e empurra 1 casa. Recarga: 5 rodadas.",
      "source": "monstro"
    },
    {
      "id": "vigor_colossal",
      "name": "Vigor Colossal",
      "action_type": "passiva",
      "save_bonus": {
        "fortitude": 3
      },
      "descricao": "+3 em todos os testes de Fortitude.",
      "source": "monstro"
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
      "id": "veneno_lacralion",
      "name": "Veneno do Lacralion",
      "action_type": "passiva",
      "attack_index": 2,
      "poison_dc": 14,
      "extra_damage": "1d4",
      "descricao": "Ao acertar o Ferrão, Fortitude CD 14; falha: 1d4 de dano adicional e Sangramento.",
      "source": "monstro"
    },
    {
      "id": "agarrar_lacralion",
      "name": "Agarrão",
      "action_type": "passiva",
      "attack_index": 0,
      "dc": 16,
      "save": "fortitude",
      "escape_saves": [
        "fortitude"
      ],
      "max_targets": 1,
      "descricao": "Quando a Pinça acerta, o alvo fica Imobilizado. Escape: Fortitude CD 16.",
      "source": "monstro"
    },
    {
      "id": "dano_retaliacao",
      "name": "Dano de Retaliação",
      "action_type": "passiva",
      "damage": "1d4",
      "damage_types": [
        "physical"
      ],
      "descricao": "Quem acertar a criatura com um ataque corpo a corpo sofre 1d4 de dano físico.",
      "source": "monstro"
    },
    {
      "id": "predador_implacavel",
      "name": "Predador Implacável",
      "action_type": "passiva",
      "descricao": "Pode manter dois inimigos Imobilizados ao mesmo tempo.",
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
      "id": "vulnerabilidade",
      "name": "Vulnerabilidade",
      "action_type": "passiva",
      "saves": [
        "vontade"
      ],
      "penalty": 2,
      "descricao": "-2 em testes de Vontade",
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
      "id": "contagiar",
      "name": "Contagiar",
      "action_type": "passiva",
      "attack_index": 0,
      "dc": 10,
      "save": "fortitude",
      "disease_severity": "leve",
      "descricao": "Ao acertar a mordida, alvo testa Fortitude CD 10 ou contrai doença leve",
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
      "id": "arremesso",
      "name": "Arremesso",
      "action_type": "acao_bonus",
      "descricao": "Arremesso 1d4+2 (alcance 3) como ação bônus; 1 natural quebra a arma",
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
      "id": "amaldicoar",
      "name": "Amaldiçoar",
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
      "attack_index": 0,
      "dc": 10,
      "save": "fortitude",
      "disease_severity": "leve",
      "descricao": "Ao acertar o ataque selecionado: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve",
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
      "id": "morte_explosiva",
      "name": "Morte Explosiva",
      "action_type": "passiva",
      "damage": "4d6",
      "damage_types": [
        "fire"
      ],
      "radius": 1,
      "save": "reflexos",
      "dc": 13,
      "duration": 2,
      "tick_damage": "1d6",
      "descricao": "Ao morrer, explode em raio 1: 4d6 de fogo; Reflexos CD 13 reduz a metade. Chamas persistem por 2 rodadas.",
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
      "id": "raio_congelante",
      "name": "Raio Congelante",
      "action_type": "magia",
      "cooldown_turns": 6,
      "circulo": 1,
      "descricao": "Conjurador nível 2. Dano de 3d4 sem teste de resistência; Fortitude apenas para evitar a paralisia. Recarga 6 rodadas.",
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
      "id": "relampago",
      "name": "Relâmpago",
      "action_type": "magia",
      "cooldown_turns": 6,
      "circulo": 1,
      "descricao": "Conjurador nível 3. Linha reta de 6 casas, 3d6 por impacto; Reflexos reduz à metade e a descarga ricocheteia de volta. Recarga 6 rodadas.",
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
      "id": "voo",
      "name": "Voo",
      "action_type": "passiva",
      "descricao": "Move-se no ar na altura 2; ataques à distância consideram a diferença vertical.",
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
      "id": "movimento_aquatico",
      "name": "Movimento Aquático",
      "action_type": "passiva",
      "descricao": "Move 6 quadrados normalmente em terra, água e água profunda.",
      "source": "monstro"
    },
    {
      "id": "veneno_charcos",
      "name": "Veneno",
      "action_type": "passiva",
      "attack_index": 3,
      "poison_dc": 15,
      "effect": "perde_movimento",
      "descricao": "Ao acertar o Ferrão, Fortitude CD 15; falha: perde a ação de movimento no próximo turno.",
      "source": "monstro"
    },
    {
      "id": "tentaculos_imobilizar",
      "name": "Tentáculos",
      "action_type": "passiva",
      "attack_index": 1,
      "hits_needed": 2,
      "dc": 17,
      "save": "fortitude",
      "escape_saves": [
        "fortitude"
      ],
      "max_targets": 1,
      "descricao": "Se dois Tentáculos acertarem o mesmo alvo, ele fica Imobilizado. Escape: Fortitude CD 17.",
      "source": "monstro"
    },
    {
      "id": "constricao_charcos",
      "name": "Constrição",
      "action_type": "passiva",
      "damage": "1d6+5",
      "damage_types": [
        "physical"
      ],
      "descricao": "No início do turno, criaturas Imobilizadas sofrem 1d6+5. Enquanto presas, não podem se afastar.",
      "source": "monstro"
    },
    {
      "id": "ferrao_paralitico",
      "name": "Ferrão Paralítico",
      "action_type": "passiva",
      "attack_index": 3,
      "dc": 17,
      "save": "fortitude",
      "effect": "perde_movimento",
      "descricao": "Ao acertar o Ferrão, Fortitude CD 17; falha: perde a ação de movimento no próximo turno.",
      "source": "monstro"
    },
    {
      "id": "nuvem_acida",
      "name": "Nuvem Ácida",
      "action_type": "acao",
      "cooldown_turns": 4,
      "range": 4,
      "radius": 1,
      "duration": 2,
      "initial_damage": "2d6",
      "tick_damage": "1d6",
      "damage_types": [
        "acid"
      ],
      "descricao": "Recarga 4 rodadas. Centro no alvo; raio 1. Causa 2d6 ao surgir e 1d6 no turno de cada criatura dentro da área.",
      "source": "monstro"
    },
    {
      "id": "mandibulas_colossais",
      "name": "Mandíbulas Colossais",
      "action_type": "passiva",
      "attack_index": 0,
      "dc": 18,
      "save": "fortitude",
      "escape_saves": [
        "forca",
        "fortitude"
      ],
      "automatic_damage": "2d10+10",
      "max_targets": 1,
      "descricao": "Ao acertar a Mordida, Fortitude CD 18 ou fica Preso. O alvo acompanha o Tirano e sofre a Mordida no início do turno dele.",
      "source": "monstro"
    },
    {
      "id": "arrastar",
      "name": "Arrastar",
      "action_type": "passiva",
      "descricao": "Uma criatura Presa acompanha todos os movimentos do Tirano, permanecendo adjacente.",
      "source": "monstro"
    },
    {
      "id": "sacudida_brutal",
      "name": "Sacudida Brutal",
      "action_type": "acao",
      "cooldown_turns": 5,
      "damage": "4d6",
      "damage_types": [
        "physical"
      ],
      "throw_distance": 2,
      "descricao": "Recarga fixa de 5 rodadas. Uma criatura Presa sofre 4d6 e é arremessada 2 quadrados; depois deixa de estar Presa.",
      "source": "monstro"
    },
    {
      "id": "couro_espesso",
      "name": "Couro Espesso",
      "action_type": "passiva",
      "descricao": "RD 4 contra armas comuns.",
      "source": "monstro"
    },
    {
      "id": "metabolismo_vulneravel",
      "name": "Metabolismo Vulnerável",
      "action_type": "passiva",
      "poison_save_penalty": -2,
      "poison_multiplier": 2,
      "descricao": "-2 em Fortitude contra venenos; dano de veneno dobrado; veneno ignora a RD.",
      "source": "monstro"
    },
    {
      "id": "engolir",
      "name": "Engolir",
      "action_type": "acao",
      "dc": 22,
      "save": "fortitude",
      "acid_damage": "3d6",
      "stomach_hp": 20,
      "escape_dc": 22,
      "descricao": "No início do turno, tenta engolir uma criatura Presa. Fortitude CD 22; falha: Engolida. O alvo sofre 3d6 ácido por turno e fica invisível para o exterior.",
      "source": "monstro"
    },
    {
      "id": "abrir_caminho",
      "name": "Abrir Caminho",
      "action_type": "passiva",
      "damage_threshold": 20,
      "internal_damage": "2d6",
      "uses_per_combat": 1,
      "descricao": "A criatura Engolida pode atacar o estômago. Ao causar 20 dano interno, é cuspida; o monstro sofre 2d6 e perde o próximo ataque.",
      "source": "monstro"
    },
    {
      "id": "passo_devastador",
      "name": "Passo Devastador",
      "action_type": "passiva",
      "move_required": 4,
      "damage": "3d6",
      "damage_types": [
        "physical"
      ],
      "push": 1,
      "descricao": "Após mover 4 ou mais quadrados, todas as criaturas adjacentes ao destino sofrem 3d6 e são empurradas 1 quadrado, inclusive aliados.",
      "source": "monstro"
    },
    {
      "id": "couro_titanico",
      "name": "Couro Titânico",
      "action_type": "passiva",
      "descricao": "RD 7 contra armas comuns.",
      "source": "monstro"
    },
    {
      "id": "metabolismo_instavel",
      "name": "Metabolismo Instável",
      "action_type": "passiva",
      "poison_save_penalty": -2,
      "poison_multiplier": 2,
      "descricao": "-2 em Fortitude contra venenos; dano de veneno dobrado; falha contra veneno também causa Lento por 1 rodada.",
      "source": "monstro"
    },
    {
      "id": "alcance_enorme",
      "name": "Alcance Enorme",
      "action_type": "passiva",
      "reach": 2,
      "descricao": "Ataques corpo a corpo atingem alvos a até 2 quadrados.",
      "source": "monstro"
    },
    {
      "id": "arremesso_colossal",
      "name": "Arremesso Colossal",
      "action_type": "acao",
      "range": 8,
      "attack_bonus": 1,
      "attack_attribute": "dex",
      "damage": "2d6",
      "damage_attribute": "str_",
      "apply_attribute_damage": true,
      "attribute_mod_base": 0,
      "descricao": "Arremessa um objeto a até 8 quadrados; usa DES no ataque e o bônus de FOR no dano.",
      "source": "monstro"
    },
    {
      "id": "golpe_esmagador",
      "name": "Golpe Esmagador",
      "action_type": "passiva",
      "attack_index": 0,
      "dc": 17,
      "save": "fortitude",
      "effect": "perde_movimento",
      "descricao": "Ao acertar a Clava Gigante, Fortitude CD 17; falha: perde a próxima ação de movimento.",
      "source": "monstro"
    },
    {
      "id": "investida_colossal",
      "name": "Investida Colossal",
      "action_type": "passiva",
      "attack_index": 0,
      "move_required": 3,
      "straight": true,
      "attack_bonus": 2,
      "damage_bonus": 4,
      "descricao": "Após mover 3 ou mais quadrados em linha reta antes da Clava: +2 no ataque e +4 no dano.",
      "source": "monstro"
    },
    {
      "id": "pisoteio_colossal",
      "name": "Pisoteio Colossal",
      "action_type": "passiva",
      "move_required": 4,
      "straight": true,
      "damage": "2d6",
      "damage_attribute": "str_",
      "descricao": "Após mover 4 ou mais quadrados em linha reta, personagens atravessados sofrem 2d6 + FOR.",
      "source": "monstro"
    },
    {
      "id": "presenca_aterradora",
      "name": "Presença Aterradora",
      "action_type": "passiva",
      "radius": 4,
      "dc": 13,
      "save": "vontade",
      "attack_penalty": -1,
      "duration_rounds": 1,
      "descricao": "No início do combate, heróis em até 4 quadrados testam Vontade; falha: -1 no ataque na primeira rodada.",
      "source": "monstro"
    },
    {
      "id": "furia_selvagem_ciclope",
      "name": "Fúria Selvagem",
      "action_type": "passiva",
      "threshold": 0.5,
      "attack_bonus": 2,
      "damage_bonus": 4,
      "ac_penalty": -4,
      "descricao": "Com metade dos PV ou menos: +2 no ataque, +4 no dano e -4 na CA.",
      "source": "monstro"
    },
    {
      "id": "visao_limitada_ciclope",
      "name": "Visão Limitada",
      "action_type": "passiva",
      "hide_bonus": 2,
      "descricao": "Personagens usando Esconder-se recebem +2 no teste contra o Ciclope.",
      "source": "monstro"
    },
    {
      "id": "ponto_cego_ciclope",
      "name": "Ponto Cego",
      "action_type": "passiva",
      "crit_min_nat_roll": 19,
      "descricao": "Resultados naturais 19 ou 20 contra o Ciclope são ameaças de crítico.",
      "source": "monstro"
    },
    {
      "id": "cercado_ciclope",
      "name": "Cercado",
      "action_type": "passiva",
      "attack_bonus": 2,
      "min_attackers": 2,
      "descricao": "Quando dois ou mais heróis o atacam, todos recebem +2 no ataque contra ele.",
      "source": "monstro"
    },
    {
      "id": "reflexos_lentos_ciclope",
      "name": "Reflexos Lentos",
      "action_type": "passiva",
      "save_penalty": {
        "reflexos": -2
      },
      "descricao": "Sofre -2 em todos os testes de Reflexos.",
      "source": "monstro"
    },
    {
      "id": "mira_certeira",
      "name": "Mira Certeira",
      "action_type": "acao_bonus",
      "cooldown_turns": 3,
      "attack_bonus": 2,
      "descricao": "Recarga 3 rodadas. Recebe +2 na próxima jogada de ataque.",
      "source": "monstro"
    },
    {
      "id": "furia_berserker",
      "name": "Fúria Berserker",
      "action_type": "acao",
      "cooldown_turns": 8,
      "extra_attacks": 1,
      "descricao": "Recarga 8 rodadas. Realiza um ataque adicional nesta rodada.",
      "source": "monstro"
    },
    {
      "id": "investida_heroica",
      "name": "Investida Heroica",
      "action_type": "acao_bonus",
      "cooldown_turns": 5,
      "movement_multiplier": 2,
      "damage_bonus": 2,
      "descricao": "Recarga 5 rodadas. Dobra o deslocamento nesta rodada e recebe +2 no dano do próximo ataque. Pode combinar com Investida e Pisoteio Colossais.",
      "source": "monstro"
    },
    {
      "id": "arsenal_colossal",
      "name": "Arsenal Colossal",
      "action_type": "passiva",
      "descricao": "Pode usar Espada Longa Colossal, Machado Orc Colossal, Lança Longa Colossal ou Alabarda Colossal. Armas de duas mãos não podem usar o Escudo Gigante.",
      "source": "monstro"
    },
    {
      "id": "regeneracao_runica",
      "name": "Regeneração Rúnica",
      "action_type": "acao_bonus",
      "cooldown_turns": 6,
      "heal": 2,
      "duration_dice": "1d4+2",
      "descricao": "Recarga 6 rodadas. Recupera 2 HP no início de cada turno durante 1d4+2 rodadas.",
      "source": "monstro"
    },
    {
      "id": "passo_fantasma_runico",
      "name": "Passo Fantasma",
      "action_type": "acao_bonus",
      "cooldown_turns": 5,
      "bonus_mov": 2,
      "duration_dice": "1d4",
      "descricao": "Recarga 5 rodadas. Como o Passo Fantasma do Guerreiro: +2 movimento nesta rodada e atravessa obstáculos baixos durante a janela.",
      "source": "monstro"
    },
    {
      "id": "provocacao_runica",
      "name": "Provocação",
      "action_type": "acao_bonus",
      "cooldown_turns": 6,
      "range": 4,
      "duration_rounds": 3,
      "descricao": "Recarga 6 rodadas. Provoca um herói a até 4 quadrados, forçando-o a enfrentar o Gigante Rúnico por 3 rodadas.",
      "source": "monstro"
    },
    {
      "id": "salto_selvagem",
      "name": "Salto Selvagem",
      "action_type": "passiva",
      "attack_index": 2,
      "move_required": 3,
      "reflex_dc": 14,
      "escape_dc": 14,
      "save": "reflexos",
      "escape_saves": [
        "forca"
      ],
      "effect": "imobilizado",
      "collision_damage": "1d6",
      "descricao": "Se mover 3 quadrados antes da Chifrada, o alvo testa Reflexos CD 14 ou fica Imobilizado; escapa com Força CD 14. Se estiver contra uma parede, sofre +1d6 de colisão.",
      "source": "monstro"
    },
    {
      "id": "dilacerar",
      "name": "Dilacerar",
      "action_type": "passiva",
      "attack_index": 1,
      "hits_needed": 2,
      "damage": "2d6",
      "damage_types": [
        "physical"
      ],
      "causa_sangramento": true,
      "descricao": "Se as duas Garras acertarem o mesmo alvo no turno, ele sofre 2d6 de dano extra uma vez e começa a Sangrar.",
      "source": "monstro"
    },
    {
      "id": "furia_garaloux",
      "name": "Frenesi",
      "action_type": "passiva",
      "threshold": 0.5,
      "attack_bonus": 2,
      "damage_bonus": 2,
      "descricao": "Ao atingir metade da Vida ou menos, recebe +2 no ataque e +2 no dano.",
      "source": "monstro"
    },
    {
      "id": "predador_supremo",
      "name": "Predador Supremo",
      "action_type": "passiva",
      "trigger": "kill",
      "attack_index": 0,
      "chain": false,
      "descricao": "Sempre que eliminar uma criatura, realiza imediatamente uma Mordida adicional. A Mordida adicional não gera outra reação.",
      "source": "monstro"
    },
    {
      "id": "aura_escaldante",
      "name": "Aura Escaldante",
      "action_type": "passiva",
      "radius": 1,
      "damage": "1d4",
      "damage_types": [
        "fire"
      ],
      "descricao": "Criaturas adjacentes sofrem 1d4 de fogo no início do próprio turno.",
      "source": "monstro"
    },
    {
      "id": "investida_flamejante",
      "name": "Investida Flamejante",
      "action_type": "passiva",
      "attack_index": 2,
      "move_required": 3,
      "damage": "2d6",
      "damage_types": [
        "fire"
      ],
      "descricao": "Após mover 3 quadrados, a Chifrada causa +2d6 de fogo.",
      "source": "monstro"
    },
    {
      "id": "explosao_vapor",
      "name": "Explosão de Vapor",
      "action_type": "acao",
      "cooldown_turns": 6,
      "range": 3,
      "shape": "cone",
      "damage": "4d6",
      "damage_types": [
        "fire"
      ],
      "save": "reflexos",
      "dc": 16,
      "success_effect": "metade",
      "descricao": "Recarga fixa de 6 rodadas. Cone de 3 quadrados; Reflexos CD 16 reduz 4d6 de fogo à metade.",
      "source": "monstro"
    },
    {
      "id": "olhar_petrificante",
      "name": "Olhar Petrificante",
      "action_type": "passiva",
      "save": "vontade",
      "dc": 15,
      "descricao": "Sempre ativo. Uma criatura que veja a Medusa testa Vontade; falha gera uma marca de Petrificação e sucesso uma marca de Resistência. Três marcas de Petrificação petrificam; três de Resistência encerram o efeito.",
      "source": "monstro"
    },
    {
      "id": "veneno_medusa",
      "name": "Veneno da Medusa",
      "action_type": "passiva",
      "poison_dc": 15,
      "descricao": "Fortitude CD 15; falha: +2d4 de veneno e -2 FOR/-2 CON por 1d6 rodadas; sucesso: +2 de veneno. O efeito não acumula e reinicia sua duração.",
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
      "guild_progressions": [
        {
          "id": "guerreiro_mira_3",
          "level": 3,
          "requires": "guerreiro_combinar_2",
          "name": "Mira Certeira III",
          "icon": "🎯",
          "description": "Mira Certeira também concede +2 de dano (além do +2 de acerto)."
        }
      ]
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
      "descricao": "Reduz todo dano físico em 3 fora do ponto vulnerável",
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
      "action_type": "acao_livre",
      "cooldown_turns": 5,
      "range": 6,
      "damage": "3d6",
      "save": "reflexos",
      "dc": 13,
      "descricao": "Ação livre extra. Alvo único em linha reta dentro do alcance configurado: 3d6 de ácido. Reflexos CD 13 reduz o dano à metade; em caso de falha, metade do dano é repetida na rodada seguinte e equipamentos podem ser danificados.",
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
      "id": "hero_warrior_golpe_devastador",
      "source": "heroi",
      "source_id": "golpe_devastador",
      "source_class": "warrior",
      "name": "Golpe Devastador",
      "icon": "💥",
      "descricao": "Dobra cada dado de dano neste turno",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "guerreiro_golpe_3",
          "level": 3,
          "requires": "guerreiro_combinar_2",
          "name": "Golpe Devastador III",
          "icon": "💥",
          "description": "Golpe Devastador passa a multiplicar os dados de dano por 2 (era ×1,5)."
        }
      ]
    },
    {
      "id": "sopro_dragao",
      "source": "monstro",
      "name": "Sopro de Dragão",
      "icon": "🐉",
      "action_type": "acao",
      "range": 4,
      "damage": "3d6",
      "damage_types": [
        "fire"
      ],
      "save": "reflexos",
      "dc": 15,
      "shape": "cone",
      "target_mode": "todos",
      "success_effect": "metade",
      "descricao": "3d6 de fogo em cone de 4 casas; todos na área. Reflexos CD 15: sucesso reduz o dano à metade.",
      "uses_per_day": 1,
      "cooldown_turns": 6
    },
    {
      "id": "agarrar",
      "name": "Agarrar",
      "action_type": "passiva",
      "dc": 12,
      "save": "fortitude",
      "descricao": "Ao acertar, alvo testa FOR ou REF CD 12 — falha: preso",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "atq_mandibula",
      "name": "Ataque de Mandíbula",
      "action_type": "passiva",
      "descricao": "Se alvo preso e adjacente: 1d8+3 dano direto (sem rolagem de acerto)",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "caca_em_bando",
      "name": "Caça em Bando",
      "action_type": "passiva",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "derrubar",
      "name": "Derrubar",
      "action_type": "passiva",
      "dc": 11,
      "save": "reflexos",
      "source": "monstro",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "combo_devorador",
      "name": "Combo Devorador",
      "action_type": "passiva",
      "descricao": "Se as 2 Mordidas acertarem no turno: 2 ataques de Garra imediatos, cada um causando 1d6+3 de dano, e Sangramento.",
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
      "id": "hero_mage_aprimorar_magia",
      "source": "heroi",
      "source_id": "aprimorar_magia",
      "source_class": "mage",
      "name": "Aprimorar Magia",
      "icon": "🎯",
      "descricao": "Ação livre. +1 na dificuldade (CD) do teste de resistência da magia. 🍖-3 ao lançar.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "mago_aprimorar_2",
          "level": 2,
          "requires": null,
          "name": "Aprimorar II",
          "icon": "🎯",
          "description": "Aprimorar Magia dá +2 na CD do save (era +1)."
        },
        {
          "id": "mago_aprimorar_3",
          "level": 3,
          "requires": "mago_aprimorar_2",
          "name": "Aprimorar III",
          "icon": "🎯",
          "description": "Aprimorar Magia dá +3 na CD do save."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "mago_estender_2",
          "level": 2,
          "requires": null,
          "name": "Estender II",
          "icon": "⏱️",
          "description": "Estender Magia dá +2 rodadas de duração (era +1)."
        },
        {
          "id": "mago_estender_3",
          "level": 3,
          "requires": "mago_estender_2",
          "name": "Estender III",
          "icon": "⏱️",
          "description": "Estender Magia dá +3 rodadas de duração."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true
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
      "guild_category": "tecnica",
      "uses_per_day": 1,
      "cooldown_turns": 0
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
      "guild_category": "especializacao",
      "uses_per_day": 1,
      "cooldown_turns": 0
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
      "guild_category": "especializacao",
      "uses_per_day": 1,
      "cooldown_turns": 0
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
      "guild_category": "especializacao",
      "uses_per_day": 1,
      "cooldown_turns": 0
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
      "guild_category": "especializacao",
      "uses_per_day": 1,
      "cooldown_turns": 0
    },
    {
      "id": "guild_tecnica_investida",
      "source": "guilda",
      "source_id": "tecnica_investida",
      "name": "Investida Heroica",
      "icon": "⚡",
      "action_type": "acao",
      "monster_effect": "investida_heroica_minotauro",
      "movement_multiplier": 2,
      "damage_bonus": 2,
      "uses_per_day": null,
      "cooldown_turns": 2,
      "descricao": "Dobra o deslocamento do turno e concede +2 de dano ao próximo ataque."
    },
    {
      "id": "guild_tecnica_pressao_constante",
      "source": "guilda",
      "source_id": "tecnica_pressao_constante",
      "name": "Pressão Constante",
      "icon": "😖",
      "action_type": "acao",
      "monster_effect": "pressao_constante_minotauro",
      "ca_penalty": 2,
      "duration_rounds": 2,
      "uses_per_day": null,
      "cooldown_turns": 4,
      "descricao": "Um herói adjacente sofre -2 de CA por 2 rodadas."
    },
    {
      "id": "guild_tecnica_instinto_sobrevivencia",
      "source": "guilda",
      "source_id": "tecnica_instinto_sobrevivencia",
      "name": "Instinto de Sobrevivência",
      "icon": "🍀",
      "action_type": "passiva",
      "monster_effect": "instinto_sobrevivencia_minotauro",
      "uses_per_day": null,
      "cooldown_turns": 10,
      "descricao": "Quando um dano reduziria o minotauro a 0 PV, ele permanece com 1 PV."
    },
    {
      "id": "guild_tecnica_ultimo_esforco",
      "source": "guilda",
      "source_id": "tecnica_ultimo_esforco",
      "name": "Último Esforço",
      "icon": "🔥",
      "action_type": "passiva",
      "monster_effect": "ultimo_esforco_minotauro",
      "uses_per_day": null,
      "cooldown_turns": 10,
      "descricao": "Quando um dano reduziria o minotauro a 0 PV, ele permanece com 1 PV por 2 turnos; nesse período tem vantagem e todo acerto é crítico, não pode ser curado e depois morre."
    },
    {
      "id": "comando",
      "source": "monstro",
      "name": "Comando",
      "icon": "🗣️",
      "action_type": "magia",
      "uses_per_combat": 3,
      "descricao": "Magia de controle mental; 3 usos por encontro."
    },
    {
      "id": "sono",
      "source": "monstro",
      "name": "Sono",
      "icon": "💤",
      "action_type": "magia",
      "uses_per_combat": 1,
      "descricao": "Magia de área; 1 uso por encontro."
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "guerreiro_furia_3",
          "level": 3,
          "requires": "guerreiro_combinar_2",
          "name": "Fúria Berserker III",
          "icon": "🔥",
          "description": "Fúria Berserker concede 2 ataques extras (3 ataques no total)."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "mago_fortalecer_2",
          "level": 2,
          "requires": null,
          "name": "Fortalecer II",
          "icon": "💥",
          "description": "Fortalecer Magia multiplica o dano por 1,5 (era ×1,25)."
        },
        {
          "id": "mago_fortalecer_3",
          "level": 3,
          "requires": "mago_fortalecer_2",
          "name": "Fortalecer III",
          "icon": "💥",
          "description": "Fortalecer Magia multiplica o dano por 2."
        }
      ]
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
      "monster_effect": "passiva_combate",
      "guild_progressions": [
        {
          "id": "ladino_furtivo_2",
          "level": 2,
          "requires": null,
          "name": "Ataque Furtivo II",
          "icon": "🗡️",
          "description": "Ataque Furtivo também dispara se há aliado adjacente ao alvo."
        },
        {
          "id": "ladino_furtivo_3",
          "level": 3,
          "requires": "ladino_furtivo_2",
          "name": "Ataque Furtivo Supremo",
          "icon": "🗡️",
          "description": "1×/inimigo/rodada: quando um aliado acerta um inimigo, Luccas reage com um Ataque Furtivo nele."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true
    },
    {
      "id": "hero_rogue_esconder_sombras",
      "source": "heroi",
      "source_id": "esconder_sombras",
      "source_class": "rogue",
      "name": "Esconder nas Sombras",
      "icon": "🌑",
      "descricao": "Ação bônus. d20+DES vs percepção dos monstros. Pode atacar na mesma rodada usando a ação principal. Invisível (não é alvo) enquanto ativo. Manutenção 🍖-1 💧-1/turno.",
      "action_type": "acao",
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true,
      "guild_progressions": [
        {
          "id": "ladino_esconder_2",
          "level": 2,
          "requires": null,
          "name": "Esconder nas Sombras II",
          "icon": "🌑",
          "description": "+2 na chance de se esconder nas sombras."
        },
        {
          "id": "ladino_esconder_3",
          "level": 3,
          "requires": "ladino_esconder_2",
          "name": "Esconder nas Sombras III",
          "icon": "🌑",
          "description": "Ao ser revelado, +2 de CA por 1 rodada."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "ladino_veneno_2",
          "level": 2,
          "requires": null,
          "name": "Veneno Rápido II",
          "icon": "☠️",
          "description": "O veneno na arma (corpo a corpo) dura 2 golpes certeiros."
        },
        {
          "id": "ladino_veneno_3",
          "level": 3,
          "requires": "ladino_veneno_2",
          "name": "Veneno Rápido III",
          "icon": "☠️",
          "description": "Pode manter 2 venenos diferentes na arma ao mesmo tempo."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "ladino_desarme_2",
          "level": 2,
          "requires": null,
          "name": "Desarme II",
          "icon": "🔧",
          "description": "+2 na chance de desarmar armadilhas."
        },
        {
          "id": "ladino_desarme_3",
          "level": 3,
          "requires": "ladino_desarme_2",
          "name": "Desarme III",
          "icon": "🔧",
          "description": "Chance extra de recuperar o ouro da armadilha desarmada."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "clerigo_cura_2",
          "level": 2,
          "requires": null,
          "name": "Cura II",
          "icon": "🙌",
          "description": "Cura pode usar até 2d8 + INT."
        },
        {
          "id": "clerigo_cura_3",
          "level": 3,
          "requires": "clerigo_cura_2",
          "name": "Cura III",
          "icon": "🙌",
          "description": "Cura pode usar até 3d8 + INT."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "clerigo_massa_2",
          "level": 2,
          "requires": null,
          "name": "Cura em Massa II",
          "icon": "🌟",
          "description": "Cura em Massa: até 2d8 + INT, raio 4."
        },
        {
          "id": "clerigo_massa_3",
          "level": 3,
          "requires": "clerigo_massa_2",
          "name": "Cura em Massa III",
          "icon": "🌟",
          "description": "Cura em Massa: até 3d8 + INT, raio 6."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "clerigo_purif_2",
          "level": 2,
          "requires": null,
          "name": "Purificação II",
          "icon": "✨",
          "description": "Purificação também remove doenças."
        },
        {
          "id": "clerigo_purif_3",
          "level": 3,
          "requires": "clerigo_purif_2",
          "name": "Purificação III",
          "icon": "✨",
          "description": "Purificação também remove maldições e petrificação."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "clerigo_ressur_2",
          "level": 2,
          "requires": null,
          "name": "Ressurreição II",
          "icon": "💫",
          "description": "Ressurreição traz o aliado com metade dos PV (🍖15 💧15)."
        },
        {
          "id": "clerigo_ressur_3",
          "level": 3,
          "requires": "clerigo_ressur_2",
          "name": "Ressurreição III",
          "icon": "💫",
          "description": "Ressurreição traz o aliado com PV cheio (🍖20 💧20)."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "guild_progressions": [
        {
          "id": "paladino_cura_maos_2",
          "level": 2,
          "requires": null,
          "name": "Cura pelas Mãos II",
          "icon": "🙏",
          "description": "Imposição das Mãos cura 2d6 + FOR."
        },
        {
          "id": "paladino_cura_maos_3",
          "level": 3,
          "requires": "paladino_cura_maos_2",
          "name": "Cura pelas Mãos III",
          "icon": "🙏",
          "description": "Pode gastar +2🍖/+2💧 por +1d6 de cura (até 3×)."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true,
      "guild_progressions": [
        {
          "id": "paladino_ataque_sagrado_2",
          "level": 2,
          "requires": null,
          "name": "Ataque Sagrado II",
          "icon": "⚔️",
          "description": "Golpe Sagrado causa +2d8 de dano sagrado por ataque."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true,
      "guild_progressions": [
        {
          "id": "paladino_defensor_2",
          "level": 2,
          "requires": null,
          "name": "Defensor II",
          "icon": "🛡️",
          "description": "O alcance da proteção aumenta para 5 quadrados."
        },
        {
          "id": "paladino_defensor_3",
          "level": 3,
          "requires": "paladino_defensor_2",
          "name": "Defensor III",
          "icon": "🛡️",
          "description": "O dano dividido cai para 40%/40% (20% é mitigado)."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true,
      "guild_progressions": [
        {
          "id": "paladino_regen_2",
          "level": 2,
          "requires": null,
          "name": "Regeneração II",
          "icon": "✨",
          "description": "Regeneração Divina também cura +1 HP dos aliados adjacentes."
        },
        {
          "id": "paladino_regen_3",
          "level": 3,
          "requires": "paladino_regen_2",
          "name": "Regeneração III",
          "icon": "✨",
          "description": "A Regeneração Divina alcança aliados em raio 2."
        }
      ]
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
      "monster_effect": "vantagem_combate",
      "monster_maintenance": true,
      "guild_progressions": [
        {
          "id": "paladino_luz_2",
          "level": 2,
          "requires": null,
          "name": "Guerreiro da Luz II",
          "icon": "💡",
          "description": "Mantém 3 atributos ativos; com Visão, detecta armadilhas em raio 2."
        },
        {
          "id": "paladino_luz_3",
          "level": 3,
          "requires": "paladino_luz_2",
          "name": "Guerreiro da Luz III",
          "icon": "💡",
          "description": "Mantém 4 atributos ativos; com Visão, detecta armadilhas em raio 3."
        }
      ]
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
      "id": "guild_mago_reviver_4",
      "source": "guilda",
      "source_id": "mago_reviver_4",
      "name": "Senhor da Morte",
      "icon": "✦",
      "descricao": "Versão alternativa de Animar os Mortos: preserva a ficha completa da criatura, custa ND+2 slots, −20 pontos de sucesso e +10 pontos de hostilidade.",
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
      "descricao": "Ao ser revelado, +2 de CA por 1 rodada.",
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
      "id": "guild_ladino_camara_gas",
      "source": "guilda",
      "source_id": "ladino_camara_gas",
      "name": "Fórmula: Câmara de Gás",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Câmara de Gás.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_jato_acido",
      "source": "guilda",
      "source_id": "ladino_jato_acido",
      "name": "Fórmula: Jato de Ácido",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Jato de Ácido.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_armadilha_raio_congelante",
      "source": "guilda",
      "source_id": "ladino_armadilha_raio_congelante",
      "name": "Fórmula: Armadilha de Raio Congelante",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Armadilha de Raio Congelante.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_teto_esmagador",
      "source": "guilda",
      "source_id": "ladino_teto_esmagador",
      "name": "Fórmula: Teto Esmagador",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Teto Esmagador.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_bau_engolidor",
      "source": "guilda",
      "source_id": "ladino_bau_engolidor",
      "name": "Fórmula: Baú Engolidor",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Baú Engolidor.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_guilhotina",
      "source": "guilda",
      "source_id": "ladino_guilhotina",
      "name": "Fórmula: Guilhotina",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Guilhotina.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_ladino_fosso",
      "source": "guilda",
      "source_id": "ladino_fosso",
      "name": "Fórmula: Fosso",
      "icon": "✦",
      "descricao": "Desbloqueia permanentemente a fabricação de Fosso.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_pombo",
      "source": "guilda",
      "source_id": "lenda_pombo",
      "name": "Lenda: Pombo",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Pombo.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_rato",
      "source": "guilda",
      "source_id": "lenda_rato",
      "name": "Lenda: Rato",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Rato.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_gato",
      "source": "guilda",
      "source_id": "lenda_gato",
      "name": "Lenda: Gato",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Gato.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ovelha",
      "source": "guilda",
      "source_id": "lenda_ovelha",
      "name": "Lenda: Ovelha",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ovelha.",
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
      "id": "guild_lenda_lacralion_filhote",
      "source": "guilda",
      "source_id": "lenda_lacralion_filhote",
      "name": "Lenda: Lacralion Filhote",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lacralion Filhote.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lacralion_adulto",
      "source": "guilda",
      "source_id": "lenda_lacralion_adulto",
      "name": "Lenda: Lacralion Adulto",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lacralion Adulto.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_lacralion_anciao",
      "source": "guilda",
      "source_id": "lenda_lacralion_anciao",
      "name": "Lenda: Lacralion Ancião",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Lacralion Ancião.",
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
      "id": "guild_lenda_ferrao_charcos_jovem",
      "source": "guilda",
      "source_id": "lenda_ferrao_charcos_jovem",
      "name": "Lenda: Ferrão dos Charcos Jovem",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ferrão dos Charcos Jovem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ferrao_charcos_adulto",
      "source": "guilda",
      "source_id": "lenda_ferrao_charcos_adulto",
      "name": "Lenda: Ferrão dos Charcos Adulto",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ferrão dos Charcos Adulto.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ferrao_charcos_anciao",
      "source": "guilda",
      "source_id": "lenda_ferrao_charcos_anciao",
      "name": "Lenda: Ferrão dos Charcos Ancião",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ferrão dos Charcos Ancião.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_tirano_da_mata",
      "source": "guilda",
      "source_id": "lenda_tirano_da_mata",
      "name": "Lenda: Tirano da Mata",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Tirano da Mata.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_tirano_ancestral",
      "source": "guilda",
      "source_id": "lenda_tirano_ancestral",
      "name": "Lenda: Tirano Ancestral",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Tirano Ancestral.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_ciclope",
      "source": "guilda",
      "source_id": "lenda_ciclope",
      "name": "Lenda: Ciclope",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Ciclope.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_gigante_guerra",
      "source": "guilda",
      "source_id": "lenda_gigante_guerra",
      "name": "Lenda: Gigante da Guerra",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Gigante da Guerra.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_gigante_runico",
      "source": "guilda",
      "source_id": "lenda_gigante_runico",
      "name": "Lenda: Gigante Rúnico",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Gigante Rúnico.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_garaloux_jovem",
      "source": "guilda",
      "source_id": "lenda_garaloux_jovem",
      "name": "Lenda: Garaloux Jovem",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Garaloux Jovem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_garaloux_adulto",
      "source": "guilda",
      "source_id": "lenda_garaloux_adulto",
      "name": "Lenda: Garaloux Adulto",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Garaloux Adulto.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_garaloux_alfa",
      "source": "guilda",
      "source_id": "lenda_garaloux_alfa",
      "name": "Lenda: Garaloux Alfa",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Garaloux Alfa.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_molochus_jovem",
      "source": "guilda",
      "source_id": "lenda_molochus_jovem",
      "name": "Lenda: Molochus Jovem",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Molochus Jovem.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_molochus_adulto",
      "source": "guilda",
      "source_id": "lenda_molochus_adulto",
      "name": "Lenda: Molochus Adulto",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Molochus Adulto.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_molochus_anciao",
      "source": "guilda",
      "source_id": "lenda_molochus_anciao",
      "name": "Lenda: Molochus Ancião",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Molochus Ancião.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_medusa",
      "source": "guilda",
      "source_id": "lenda_medusa",
      "name": "Lenda: Medusa",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Medusa.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_grande_medusa",
      "source": "guilda",
      "source_id": "lenda_grande_medusa",
      "name": "Lenda: Grande Medusa",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Grande Medusa.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "guild_lenda_grande_gorgona",
      "source": "guilda",
      "source_id": "lenda_grande_gorgona",
      "name": "Lenda: Grande Gorgona",
      "icon": "✦",
      "descricao": "+1 de ataque e +1 nos saves contra Grande Gorgona.",
      "action_type": "passiva",
      "monster_effect": "passiva_combate",
      "guild_category": "especializacao"
    },
    {
      "id": "arremesso_bruto",
      "source": "arma",
      "name": "Arremesso Bruto",
      "icon": "🪓",
      "action_type": "passiva",
      "descricao": "O arremesso desta arma usa o modificador de Força no acerto e no dano."
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
      "id": "voo",
      "nome": "Voo",
      "circulo": "primeiro",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "🪽",
      "tipo": "alvo_aliado",
      "descricao": "Ativa Voo em um aliado: alcance 3 quadrados +1 a cada 3 níveis de conjurador; altura inicial 2, máxima 10.",
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
      "descricao": "Toque. +25 fome +25 sede em 1 aliado.",
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
      "id": "chamado_inverno",
      "nome": "Chamado do Inverno",
      "circulo": "segundo",
      "classe": [
        "cleric"
      ],
      "icone": "❄️",
      "tipo": "area_fixa",
      "descricao": "Área 4x4 (+1 casa a cada 2 níveis). Transforma o chão em Piso congelado ou Planície nevada por 1d4 + nível rodadas. Permanente: +20 Fome e +20 Sede.",
      "save": "reflexos",
      "area_lado": 4,
      "alcance_base": 7,
      "duracao": "1d4"
    },
    {
      "id": "senhor_das_aguas",
      "nome": "Senhor das Águas",
      "circulo": "terceiro",
      "classe": [
        "cleric"
      ],
      "icone": "🌊",
      "tipo": "area_fixa",
      "descricao": "Transforma uma área em Água ou Água profunda por 1d4 + nível rodadas. A partir da segunda rodada, e em qualquer rodada seguinte enquanto a magia durar, pode marcar casas da área como redemoinho por ação livre, até somar metade do nível do clérigo no total. A cota é acumulada (dá para marcar poucas casas por vez) e os redemoinhos permanecem até o fim da magia.",
      "area_lado": 4,
      "alcance_base": 5,
      "duracao": "1d4"
    },
    {
      "id": "ira_rocha_ardente",
      "nome": "Ira da Rocha Ardente",
      "circulo": "quarto",
      "classe": [
        "cleric"
      ],
      "icone": "🌋",
      "tipo": "area_fixa",
      "descricao": "Área de lava 3x3 (+1 casa a cada 3 níveis), alcance 4 (+1 a cada 2 níveis). Todos na área sofrem 2d6 de fogo e os efeitos da lava. Dura 1d4 +1 rodada a cada 3 níveis (mínimo 2). A partir da segunda rodada, cria 2d4 Chamas Vivas escolhidas pelo clérigo em uma área 1x1 maior que a lava.",
      "area_lado": 3,
      "alcance_base": 4,
      "duracao": "1d4"
    },
    {
      "id": "teleporte",
      "nome": "Teleporte",
      "circulo": "quarto",
      "classe": [
        "mage"
      ],
      "icone": "🌀",
      "tipo": "teleporte",
      "descricao": "Teletransporta você, um monstro ou outro jogador visível para uma casa livre do mapa a até 15 quadrados +1 por nível. Alvos involuntários fazem Vontade contra CD 8 + INT + 4; o jogador pode falhar voluntariamente.",
      "save": "vontade",
      "alcance_base": 15
    },
    {
      "id": "prisao_chamas",
      "nome": "Prisão de Chamas",
      "circulo": "quarto",
      "classe": [
        "mage"
      ],
      "icone": "🔥",
      "tipo": "area_fixa",
      "descricao": "Cria uma prisão quadrada de chamas de 2x2, 3x3 ou 4x4. Apenas as bordas têm chamas e casas de parede são ignoradas. Criaturas adjacentes sofrem 2d4 ao surgir e no início de seus turnos; quem ocupa ou atravessa as chamas sofre 2d8. Dura 10 rodadas e pode ser encerrada pelo mago como ação livre.",
      "alcance_base": 4,
      "duracao": 10
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
    },
    {
      "id": "olhar_petrificante",
      "nome": "Olhar Petrificante",
      "circulo": "quarto",
      "classe": [
        "mage",
        "cleric"
      ],
      "icone": "👁️",
      "tipo": "buff_self",
      "descricao": "O alvo que tiver o conjurador em sua visão testa Vontade. Faz um teste inicial, dois por turno enquanto o conjurador permanecer visível e até cinco testes finais após perdê-lo de vista. Três falhas petrificam permanentemente; três sucessos encerram o efeito.",
      "save": "vontade",
      "duracao": "1d4"
    },
    {
      "id": "metamorfose",
      "nome": "Metamorfose",
      "circulo": "quarto",
      "classe": [
        "mage"
      ],
      "icone": "🦋",
      "tipo": "transformacao",
      "descricao": "Transforma uma criatura viva em uma forma desbloqueada do bestiário. A forma mantém seus atributos, ataques, defesa, movimento e habilidades; a manutenção custa 1 Fome e 1 Sede por rodada.",
      "save": "vontade"
    }
  ],
  "items": [
    {
      "id": "carta",
      "name": "Carta",
      "emoji": "✉️",
      "item_slot": "bag",
      "effect": "letter",
      "value": 0,
      "loot_only": true,
      "descricao": "Ao ler, abre a mensagem escrita sem consumir a carta.",
      "texto": "Esta carta não contém nenhuma mensagem."
    },
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
      "id": "espada_longa_colossal",
      "name": "Espada Longa Colossal",
      "emoji": "⚔️",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Arma de proporções gigantescas: 2d8+6, alcance de 2 quadrados."
    },
    {
      "id": "machado_orc_colossal",
      "name": "Machado Orc Colossal",
      "emoji": "🪓",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Arma de duas mãos: 2d10+6, alcance de 2 quadrados."
    },
    {
      "id": "lanca_longa_colossal",
      "name": "Lança Longa Colossal",
      "emoji": "🔱",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Alcance de 4 quadrados em linha reta, 2 na diagonal e ataques adjacentes; dano 2d8+6."
    },
    {
      "id": "alabarda_colossal",
      "name": "Alabarda Colossal",
      "emoji": "🪓",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Arma de duas mãos: alcance de 4 quadrados em linha reta e 2 na diagonal; dano 2d10+6."
    },
    {
      "id": "armadura_pesada_gigante",
      "name": "Armadura Pesada de Gigante",
      "emoji": "🛡️",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Armadura pesada de proporções gigantescas."
    },
    {
      "id": "martelo_runico_colossal",
      "name": "Martelo Rúnico Colossal",
      "emoji": "🔨",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Martelo colossal gravado com runas: dano 2d8+5 e alcance de 2 quadrados."
    },
    {
      "id": "armadura_runica",
      "name": "Armadura Rúnica",
      "emoji": "🛡️",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Armadura rúnica obtida do Gigante Rúnico; item especial para uso futuro."
    },
    {
      "id": "runa_ancestral",
      "name": "Runa Ancestral",
      "emoji": "✨",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0,
      "loot_only": true,
      "descricao": "Runa ancestral de poder mágico; item especial para uso futuro."
    },
    {
      "id": "joia",
      "name": "Joia",
      "emoji": "💎",
      "item_slot": "bag",
      "effect": "treasure",
      "value": 0
    },
    {
      "id": "dagger",
      "name": "Adaga",
      "emoji": "🗡️",
      "die": "1d4",
      "stat": "str_",
      "finesse": true,
      "off_hand_weapon": true,
      "throw_range": 3,
      "categoria": "perfurante",
      "descricao": "Adaga: 1d4 de dano perfurante, usando Força ou Destreza. Também pode ser arremessada até 3 casas. Pode ser usada na mão secundária para um ataque extra, substituindo o escudo."
    },
    {
      "id": "chicote",
      "name": "Chicote",
      "emoji": "🪢",
      "die": "1d4",
      "stat": "dex",
      "off_hand_weapon": true,
      "range": 2,
      "categoria": "cortante",
      "descricao": "Chicote: 1d4 de dano cortante, usando Destreza. Alcance: 2 casas em linha reta. Pode ser usada na mão secundária para um ataque extra, substituindo o escudo."
    },
    {
      "id": "hand_crossbow",
      "name": "Besta de Mão",
      "emoji": "🏹",
      "die": "1d4",
      "stat": "dex",
      "range": 4,
      "categoria": "perfurante",
      "descricao": "Besta de Mão: 1d4 de dano perfurante, usando Destreza. Alcance: 4 casas em linha reta."
    },
    {
      "id": "lanca_curta",
      "name": "Lança Curta",
      "emoji": "🔱",
      "die": "1d6",
      "stat": "str_",
      "throw_range": 4,
      "categoria": "perfurante",
      "descricao": "Lança Curta: 1d6 de dano perfurante, usando Força. Também pode ser arremessada até 4 casas."
    },
    {
      "id": "bordao",
      "name": "Bordão",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "finesse": true,
      "categoria": "contundente",
      "descricao": "Bordão: 1d6 de dano contundente, usando Força ou Destreza. No 20 natural, o alvo testa Fortitude ou fica tonto."
    },
    {
      "id": "cajado_madeira",
      "name": "Cajado de Madeira",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "finesse": true,
      "reach": "cajado",
      "categoria": "contundente",
      "descricao": "Cajado de Madeira: 1d6 de dano contundente, usando Força ou Destreza. Alcance: qualquer casa adjacente."
    },
    {
      "id": "staff",
      "name": "Cajado Arcano",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "finesse": true,
      "reach": "cajado",
      "categoria": "contundente",
      "descricao": "Cajado Arcano: 1d6 de dano contundente, usando Força ou Destreza. Alcance: qualquer casa adjacente."
    },
    {
      "id": "maca",
      "name": "Maça",
      "emoji": "🔨",
      "die": "1d6",
      "stat": "str_",
      "crit_nat20_multiplier": 3,
      "categoria": "contundente",
      "descricao": "Maça: 1d6 de dano contundente, usando Força. 20 natural: dano multiplicado por 3."
    },
    {
      "id": "shortsword",
      "name": "Espada Curta",
      "emoji": "⚔️",
      "die": "1d6",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada Curta: 1d6 de dano cortante, usando Força. Crítico natural com 19–20."
    },
    {
      "id": "machado_basico",
      "name": "Machado de Ferro",
      "emoji": "🪓",
      "die": "1d6",
      "stat": "str_",
      "throw_range": 2,
      "categoria": "cortante",
      "granted_ability": "arremesso_bruto",
      "descricao": "Machado de Ferro: 1d6 de dano cortante, usando Força. Também pode ser arremessada até 2 casas."
    },
    {
      "id": "arco_curto",
      "name": "Arco Curto",
      "emoji": "🏹",
      "die": "1d6",
      "stat": "dex",
      "range": 6,
      "categoria": "perfurante",
      "descricao": "Arco Curto: 1d6 de dano perfurante, usando Destreza. Alcance: 6 casas em linha reta ou 3 na diagonal."
    },
    {
      "id": "lanca",
      "name": "Lança",
      "emoji": "🔱",
      "die": "1d8",
      "stat": "str_",
      "reach": "lanca",
      "throw_range": 4,
      "categoria": "perfurante",
      "descricao": "Lança: 1d8 de dano perfurante, usando Força. Alcance: 2 casas ortogonais à frente ou 1 casa diagonal adjacente. Também pode ser arremessada até 4 casas."
    },
    {
      "id": "longsword",
      "name": "Espada Longa",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada Longa: 1d8 de dano cortante, usando Força. Crítico natural com 19–20."
    },
    {
      "id": "longbow",
      "name": "Arco Longo",
      "emoji": "🏹",
      "die": "1d8",
      "stat": "dex",
      "range": 10,
      "categoria": "perfurante",
      "descricao": "Arco Longo: 1d8 de dano perfurante, usando Destreza. Alcance: 10 casas em linha reta ou 5 na diagonal."
    },
    {
      "id": "warhammer",
      "name": "Martelo de Guerra",
      "emoji": "🔨",
      "die": "1d8",
      "stat": "str_",
      "crit_nat20_multiplier": 3,
      "categoria": "contundente",
      "descricao": "Martelo de Guerra: 1d8 de dano contundente, usando Força. 20 natural: dano multiplicado por 3."
    },
    {
      "id": "besta",
      "name": "Besta",
      "emoji": "🏹",
      "die": "1d8",
      "stat": "dex",
      "range": 8,
      "categoria": "perfurante",
      "descricao": "Besta: 1d8 de dano perfurante, usando Destreza. Alcance: 8 casas em linha reta."
    },
    {
      "id": "mangual",
      "name": "Mangual",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "crit_nat20_multiplier": 2.5,
      "reach": "mangual",
      "categoria": "contundente",
      "descricao": "Mangual: 1d8 de dano contundente, usando Força. Alcance: qualquer uma das 8 casas adjacentes, incluindo diagonais. 20 natural: dano multiplicado por 2.5."
    },
    {
      "id": "machado_duplo",
      "name": "Machado Duplo",
      "emoji": "🪓",
      "die": "1d8",
      "stat": "str_",
      "extra_attack_on_crit_min_nat": 19,
      "categoria": "cortante",
      "descricao": "Machado Duplo: 1d8 de dano cortante, usando Força. 19 natural: faz um ataque adicional."
    },
    {
      "id": "bastsword",
      "name": "Espada Bastarda",
      "emoji": "⚔️",
      "die": "1d10",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada Bastarda: 1d10 de dano cortante, usando Força. Crítico natural com 19–20."
    },
    {
      "id": "machado_orc",
      "name": "Machado de Guerra Órquico",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "crit_nat20_multiplier": 3,
      "categoria": "cortante",
      "descricao": "Machado de Guerra Órquico: 1d10 de dano cortante, usando Força. Requer as duas mãos. 20 natural: dano multiplicado por 3."
    },
    {
      "id": "alabarda",
      "name": "Alabarda",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "range": 2,
      "categoria": "perfurante",
      "descricao": "Alabarda: 1d10 de dano perfurante, usando Força. Alcance: 2 casas em linha reta. Requer as duas mãos."
    },
    {
      "id": "espada2m",
      "name": "Espada de 2 Mãos",
      "emoji": "⚔️",
      "die": "2d6",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada de 2 Mãos: 2d6 de dano cortante, usando Força. Requer as duas mãos. Crítico natural com 19–20."
    },
    {
      "id": "dagger_prata",
      "name": "Adaga de Prata",
      "emoji": "🗡️",
      "die": "1d4",
      "stat": "str_",
      "finesse": true,
      "off_hand_weapon": true,
      "throw_range": 3,
      "categoria": "perfurante",
      "descricao": "Adaga de Prata: 1d4 de dano perfurante, usando Força ou Destreza. Também pode ser arremessada até 3 casas. Pode ser usada na mão secundária para um ataque extra, substituindo o escudo. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "chicote_prata",
      "name": "Chicote de Prata",
      "emoji": "🪢",
      "die": "1d4",
      "stat": "dex",
      "off_hand_weapon": true,
      "range": 2,
      "categoria": "cortante",
      "descricao": "Chicote de Prata: 1d4 de dano cortante, usando Destreza. Alcance: 2 casas em linha reta. Pode ser usada na mão secundária para um ataque extra, substituindo o escudo. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "lanca_curta_prata",
      "name": "Lança Curta de Prata",
      "emoji": "🔱",
      "die": "1d6",
      "stat": "str_",
      "throw_range": 4,
      "categoria": "perfurante",
      "descricao": "Lança Curta de Prata: 1d6 de dano perfurante, usando Força. Também pode ser arremessada até 4 casas. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "bordao_prata",
      "name": "Bordão de Prata",
      "emoji": "🪄",
      "die": "1d6",
      "stat": "str_",
      "finesse": true,
      "categoria": "contundente",
      "descricao": "Bordão de Prata: 1d6 de dano contundente, usando Força ou Destreza. No 20 natural, o alvo testa Fortitude ou fica tonto. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "maca_prata",
      "name": "Maça de Prata",
      "emoji": "🔨",
      "die": "1d6",
      "stat": "str_",
      "crit_nat20_multiplier": 3,
      "categoria": "contundente",
      "descricao": "Maça de Prata: 1d6 de dano contundente, usando Força. 20 natural: dano multiplicado por 3. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "shortsword_prata",
      "name": "Espada Curta de Prata",
      "emoji": "⚔️",
      "die": "1d6",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada Curta de Prata: 1d6 de dano cortante, usando Força. Crítico natural com 19–20. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "machado_basico_prata",
      "name": "Machado de Ferro de Prata",
      "emoji": "🪓",
      "die": "1d6",
      "stat": "str_",
      "throw_range": 2,
      "categoria": "cortante",
      "granted_ability": "arremesso_bruto",
      "descricao": "Machado de Ferro de Prata: 1d6 de dano cortante, usando Força. Também pode ser arremessada até 2 casas. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "lanca_prata",
      "name": "Lança de Prata",
      "emoji": "🔱",
      "die": "1d8",
      "stat": "str_",
      "reach": "lanca",
      "throw_range": 4,
      "categoria": "perfurante",
      "descricao": "Lança de Prata: 1d8 de dano perfurante, usando Força. Alcance: 2 casas ortogonais à frente ou 1 casa diagonal adjacente. Também pode ser arremessada até 4 casas. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "longsword_prata",
      "name": "Espada Longa de Prata",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada Longa de Prata: 1d8 de dano cortante, usando Força. Crítico natural com 19–20. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "warhammer_prata",
      "name": "Martelo de Guerra de Prata",
      "emoji": "🔨",
      "die": "1d8",
      "stat": "str_",
      "crit_nat20_multiplier": 3,
      "categoria": "contundente",
      "descricao": "Martelo de Guerra de Prata: 1d8 de dano contundente, usando Força. 20 natural: dano multiplicado por 3. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "mangual_prata",
      "name": "Mangual de Prata",
      "emoji": "⚔️",
      "die": "1d8",
      "stat": "str_",
      "crit_nat20_multiplier": 2.5,
      "reach": "mangual",
      "categoria": "contundente",
      "descricao": "Mangual de Prata: 1d8 de dano contundente, usando Força. Alcance: qualquer uma das 8 casas adjacentes, incluindo diagonais. 20 natural: dano multiplicado por 2.5. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "machado_duplo_prata",
      "name": "Machado Duplo de Prata",
      "emoji": "🪓",
      "die": "1d8",
      "stat": "str_",
      "extra_attack_on_crit_min_nat": 19,
      "categoria": "cortante",
      "descricao": "Machado Duplo de Prata: 1d8 de dano cortante, usando Força. 19 natural: faz um ataque adicional. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "bastsword_prata",
      "name": "Espada Bastarda de Prata",
      "emoji": "⚔️",
      "die": "1d10",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada Bastarda de Prata: 1d10 de dano cortante, usando Força. Crítico natural com 19–20. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "machado_orc_prata",
      "name": "Machado de Guerra Órquico de Prata",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "crit_nat20_multiplier": 3,
      "categoria": "cortante",
      "descricao": "Machado de Guerra Órquico de Prata: 1d10 de dano cortante, usando Força. Requer as duas mãos. 20 natural: dano multiplicado por 3. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "alabarda_prata",
      "name": "Alabarda de Prata",
      "emoji": "🪓",
      "die": "1d10",
      "stat": "str_",
      "range": 2,
      "categoria": "perfurante",
      "descricao": "Alabarda de Prata: 1d10 de dano perfurante, usando Força. Alcance: 2 casas em linha reta. Requer as duas mãos. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "espada2m_prata",
      "name": "Espada de 2 Mãos de Prata",
      "emoji": "⚔️",
      "die": "2d6",
      "stat": "str_",
      "crit_min_nat_roll": 19,
      "categoria": "cortante",
      "descricao": "Espada de 2 Mãos de Prata: 2d6 de dano cortante, usando Força. Requer as duas mãos. Crítico natural com 19–20. Prata: suporta 5 níveis de corrosão, com os 2 primeiros sem penalidade, e pode causar dano a inimigos resistentes a armas normais."
    },
    {
      "id": "escudo_p",
      "name": "Escudo Pequeno",
      "emoji": "🛡️",
      "kind": "shield",
      "ac_bonus": 1,
      "damage_reduction": 1,
      "descricao": "Bônus de CA +1. Reduz em 1 o dano de cada ataque ou efeito de dano recebido, sem limite por rodada. Também reduz dano de magias e armadilhas; quando um sucesso em Reflexos reduzir o dano à metade, aplique primeiro a metade e depois esta redução."
    },
    {
      "id": "escudo_g",
      "name": "Escudo Grande",
      "emoji": "🛡️",
      "kind": "shield",
      "ac_bonus": 2,
      "damage_reduction": 2,
      "descricao": "Bônus de CA +2. Reduz em 2 o dano de cada ataque ou efeito de dano recebido, sem limite por rodada. Também reduz dano de magias e armadilhas; quando um sucesso em Reflexos reduzir o dano à metade, aplique primeiro a metade e depois esta redução."
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
      "veneno_id": "veneno_fungo_acre",
      "descricao": "Fortitude CD 10 anula. Se falhar: 1 dano por rodada durante 1d4 rodadas."
    },
    {
      "id": "veneno_dor_escarlate",
      "name": "Dor Escarlate",
      "emoji": "🩸",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_dor_escarlate",
      "descricao": "Fortitude CD 12 anula. Se falhar: 1 dano por rodada durante 1d6 rodadas."
    },
    {
      "id": "veneno_ardonia_negra",
      "name": "Ardonia Negra",
      "emoji": "🕷️",
      "item_slot": "bag",
      "effect": "coat_poison",
      "value": 0,
      "veneno_id": "veneno_ardonia_negra",
      "descricao": "Fortitude CD 14 anula. Se falhar: 1 dano por rodada durante 2d4 rodadas."
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
      "value": 0,
      "descricao": "Neutraliza venenos e protege contra novos por 1d4 rodadas."
    },
    {
      "id": "oleo_dissolvente",
      "name": "Óleo Dissolvente",
      "emoji": "🫗",
      "item_slot": "bag",
      "effect": "cure_petrification",
      "value": 0,
      "descricao": "Dissolve a pedra: cura petrificação e protege por 1d4 rodadas."
    },
    {
      "id": "elixir_depurativo",
      "name": "Elixir Depurativo",
      "emoji": "🧴",
      "item_slot": "bag",
      "effect": "cure_disease",
      "value": 0,
      "descricao": "Purga doenças do corpo e protege por 1d4 rodadas."
    },
    {
      "id": "vela_escuridao",
      "name": "Vela da Escuridão",
      "emoji": "🕯️",
      "item_slot": "bag",
      "effect": "veil_shadow",
      "value": 0,
      "descricao": "Ação bônus. Fica oculto até o fim do turno; o próximo ataque tem vantagem. Para o Ladino, o próximo ataque ativa automaticamente o Ataque Furtivo."
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
      "id": "bota_alada",
      "name": "Bota Alada",
      "emoji": "🪽",
      "kind": "boots",
      "item_slot": "boots",
      "effect": "voo",
      "value": 0,
      "descricao": "Enquanto equipada, permite Voo por tempo indeterminado, com altura máxima 3."
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
      "veneno_id": "veneno_polvo_abissal",
      "descricao": "Fortitude CD 11. Falha: cegueira por 1d4 rodadas, visão 1 quadrado, -5 percepção, -4 ataques e sem ataques à distância. Sucesso: percepção -2 por 1d4 rodadas."
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
      "veneno_id": "ensaio_sobre_a_cegueira",
      "descricao": "Fortitude CD 14. Falha: cego por 1d4+2 rodadas, visão 1 quadrado, -5 percepção, -4 ataques e sem ataques à distância. Sucesso: visão -2 quadrados e -3 percepção por 1d4 rodadas; ao final, novo Fortitude CD 14. Falha: cegueira por 1d2 rodadas."
    },
    {
      "id": "maca_treino",
      "name": "Maça de Treino",
      "emoji": "🔨",
      "die": "1d6",
      "stat": "str_",
      "finesse": true,
      "categoria": "contundente",
      "granted_ability": null,
      "item_slot": "weapon",
      "effect": "atk",
      "value": 0,
      "descricao": "Maça de Treino: 1d6 de dano contundente, usando Força ou Destreza."
    }
  ],
  "traps": [
    {
      "tipo": "buraco",
      "nome": "Buraco",
      "icone": "🕳️",
      "cr": 0.1,
      "descricao": "Reflexos dif 10 ou perde o movimento. Permanece ativa.",
      "dificuldade": 10,
      "save": "reflexos",
      "custo_ouro": 0,
      "persiste": true,
      "visivel_apos": true,
      "efeitos": [
        {
          "tipo": "perder_movimento"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_urso",
      "nome": "Armadilha de Urso",
      "icone": "🪤",
      "cr": 0.25,
      "descricao": "1d4 de dano + perde movimento. Some após ativar.",
      "dificuldade": 10,
      "save": "reflexos",
      "custo_ouro": 1,
      "persiste": false,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "1d4",
          "elemento": "fisico"
        },
        {
          "tipo": "perder_movimento"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "fosso_estacas",
      "nome": "Fosso com Estacas",
      "icone": "⛏️",
      "cr": 0.35,
      "descricao": "1d6 de dano + perde movimento. Fica visível após ativar.",
      "dificuldade": 10,
      "save": "reflexos",
      "custo_ouro": 2,
      "persiste": true,
      "visivel_apos": true,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "1d6",
          "elemento": "fisico"
        },
        {
          "tipo": "perder_movimento"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "rede",
      "nome": "Rede",
      "icone": "🕸️",
      "cr": 0.15,
      "descricao": "Perde a rodada inteira. Some após ativar.",
      "dificuldade": 11,
      "save": "reflexos",
      "custo_ouro": 4,
      "persiste": false,
      "efeitos": [
        {
          "tipo": "perder_rodada"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_incendiaria",
      "nome": "Armadilha Incendiária",
      "icone": "🔥",
      "cr": 0.5,
      "descricao": "Dano de fogo progressivo: 1d6 + 1d4 + 1 em 3 rodadas.",
      "dificuldade": 12,
      "save": "reflexos",
      "custo_ouro": 10,
      "persiste": false,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "1d6",
          "elemento": "fogo",
          "rodada": 1
        },
        {
          "tipo": "dano",
          "valor": "1d4",
          "elemento": "fogo",
          "rodada": 2
        },
        {
          "tipo": "dano",
          "valor": "1",
          "elemento": "fogo",
          "rodada": 3
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "mina_terrestre",
      "nome": "Mina Terrestre",
      "icone": "💣",
      "cr": 0.75,
      "descricao": "2d6 de dano em área de 1 quadrado. Save reduz à metade.",
      "dificuldade": 12,
      "save": "reflexos",
      "save_reduz": true,
      "custo_ouro": 20,
      "persiste": false,
      "area": 1,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "2d6",
          "elemento": "explosao",
          "area": true
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "fosso_envenenado",
      "nome": "Fosso com Estacas Envenenadas",
      "icone": "☠️",
      "cr": 0.5,
      "descricao": "1d6 de dano + efeito do veneno usado. Fica visível após ativar.",
      "dificuldade": 10,
      "save": "reflexos",
      "custo_ouro": 2,
      "persiste": true,
      "visivel_apos": true,
      "custo_veneno": true,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "1d6",
          "elemento": "fisico"
        },
        {
          "tipo": "veneno"
        }
      ],
      "precisa_veneno": true
    },
    {
      "tipo": "lamina_escondida",
      "nome": "Lâmina Escondida",
      "icone": "🗡️",
      "cr": 0.55,
      "descricao": "Reflexos CD 15 evita a lâmina. Na falha, sofre 1d8 de dano e o veneno combinado.",
      "dificuldade": 15,
      "save": "reflexos",
      "custo_ouro": 8,
      "persiste": false,
      "permite_veneno": true,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "1d8",
          "elemento": "fisico"
        },
        {
          "tipo": "veneno"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "lamina_pendulo",
      "nome": "Lâmina Pêndulo",
      "icone": "🗡️",
      "cr": 0.7,
      "descricao": "Reflexos CD 14 evita a lâmina. Na falha, sofre 2d6 de dano. Após ativar, permanece perigosa por 3 rodadas.",
      "dificuldade": 14,
      "save": "reflexos",
      "custo_ouro": 12,
      "persiste": true,
      "visivel_apos": true,
      "duracao_rodadas": 3,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "2d6",
          "elemento": "fisico"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "nuvem_gas",
      "nome": "Nuvem de Gás",
      "icone": "🌫️",
      "cr": 0.4,
      "descricao": "-1d6 CON por 3 rodadas em área. Recalcula HP.",
      "dificuldade": 13,
      "save": "fortitude",
      "custo_ouro": 25,
      "persiste": false,
      "area": 1,
      "efeitos": [
        {
          "tipo": "reduzir_con",
          "valor": "1d6",
          "duracao": 3,
          "area": true
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "camara_gas",
      "nome": "Câmara de Gás",
      "icone": "☠️",
      "cr": 0.9,
      "descricao": "Ao entrar no quadrado, libera gás pela sala. Fortitude CD 13 a cada turno; na falha, sofre 1d6 de dano. Permanece ativa por 1d6+1 rodadas.",
      "dificuldade": 13,
      "save": "fortitude",
      "custo_ouro": 30,
      "dano": "1d6",
      "persiste": false,
      "special": "camara_gas",
      "precisa_veneno": false
    },
    {
      "tipo": "jato_acido",
      "nome": "Jato de Ácido",
      "icone": "🧪",
      "cr": 0.8,
      "descricao": "Reflexos CD 18 evita o jato. Na falha, sofre 2d6 de dano, uma peça equipada sofre 1 nível de corrosão e metade do dano volta na rodada seguinte.",
      "dificuldade": 18,
      "save": "reflexos",
      "custo_ouro": 15,
      "dano": "2d6",
      "persiste": false,
      "special": "jato_acido",
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_raio_congelante",
      "nome": "Armadilha de Raio Congelante",
      "icone": "❄️",
      "cr": 0.8,
      "descricao": "Dispara um raio congelante: causa 3d4 de dano. Fortitude CD 15 evita a paralisia; na falha, escapa com Força CD 16.",
      "dificuldade": 15,
      "save": "fortitude",
      "custo_ouro": 25,
      "dano": "3d4",
      "persiste": false,
      "special": "raio_congelante",
      "escape_save": "forca",
      "escape_dificuldade": 16,
      "precisa_veneno": false
    },
    {
      "tipo": "teto_esmagador",
      "nome": "Teto Esmagador",
      "icone": "🪨",
      "cr": 1.0,
      "descricao": "Ao ser ativado, o teto desaba sobre toda a sala. Reflexos CD 20 evita; na falha, sofre 4d6 de dano.",
      "dificuldade": 20,
      "save": "reflexos",
      "custo_ouro": 30,
      "dano": "4d6",
      "persiste": false,
      "area_sala": true,
      "special": "teto_esmagador",
      "precisa_veneno": false
    },
    {
      "tipo": "bau_engolidor",
      "nome": "Baú Engolidor",
      "icone": "📦",
      "cr": 1.0,
      "descricao": "Reflexos CD 20 evita. Na falha, fica preso dentro do objeto e só escapa com Força CD 20.",
      "dificuldade": 20,
      "save": "reflexos",
      "custo_ouro": 35,
      "persiste": false,
      "special": "bau_engolidor",
      "escape_save": "forca",
      "escape_dificuldade": 20,
      "apenas_objeto": true,
      "precisa_veneno": false
    },
    {
      "tipo": "guilhotina",
      "nome": "Guilhotina",
      "icone": "🪓",
      "cr": 0.8,
      "descricao": "Reflexos CD 14 evita a lâmina. Na falha, sofre 3d6 de dano.",
      "dificuldade": 14,
      "save": "reflexos",
      "custo_ouro": 18,
      "persiste": false,
      "efeitos": [
        {
          "tipo": "dano",
          "valor": "3d6",
          "elemento": "fisico"
        }
      ],
      "precisa_veneno": false
    },
    {
      "tipo": "fosso",
      "nome": "Fosso",
      "icone": "🕳️",
      "cr": 0.45,
      "descricao": "Reflexos CD 15 evita. Na falha, sofre 1d6 de dano, perde o movimento e a próxima rodada; fica oculto e protegido enquanto estiver no fosso.",
      "dificuldade": 15,
      "save": "reflexos",
      "custo_ouro": 8,
      "dano": "1d6",
      "persiste": false,
      "special": "fosso",
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_teletransporte",
      "nome": "Armadilha de Teletransporte",
      "icone": "🌀",
      "cr": 0.4,
      "descricao": "Vontade CD 12 ou é teleportado para a saída configurada.",
      "dificuldade": 12,
      "save": "vontade",
      "persiste": false,
      "special": "teletransporte",
      "precisa_veneno": false
    },
    {
      "tipo": "armadilha_dardos_envenenados",
      "nome": "Armadilha de Dardos Envenenados",
      "icone": "🎯",
      "cr": 0.4,
      "descricao": "Sofre 1d4 perfurante e testa Fortitude contra o veneno escolhido.",
      "dificuldade": 0,
      "save": "fortitude",
      "dano": "1d4",
      "persiste": false,
      "special": "dardos_envenenados",
      "precisa_veneno": true
    },
    {
      "tipo": "armadilha_maldicao",
      "nome": "Armadilha de Maldição",
      "icone": "☠️",
      "cr": 0.75,
      "descricao": "Vontade CD configurada ou recebe uma maldição específica ou aleatória.",
      "dificuldade": 13,
      "save": "vontade",
      "persiste": false,
      "special": "maldicao",
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
      "id": "veneno_medusa",
      "name": "Veneno da Medusa"
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
  "curses": [
    {
      "id": "maos_tremulas",
      "name": "Mãos Trêmulas",
      "category": "leve",
      "description": "-2 em ataques",
      "progressive": false
    },
    {
      "id": "olhos_escuridao",
      "name": "Olhos da Escuridão",
      "category": "leve",
      "description": "-2 alcance de visão",
      "progressive": false
    },
    {
      "id": "passos_pesados",
      "name": "Passos Pesados",
      "category": "leve",
      "description": "mover custa +1 sede",
      "progressive": false
    },
    {
      "id": "lamina_enferrujada",
      "name": "Lâmina Enferrujada",
      "category": "leve",
      "description": "-2 dano físico",
      "progressive": false
    },
    {
      "id": "fraqueza_arcana",
      "name": "Fraqueza Arcana",
      "category": "leve",
      "description": "magias causam metade do dano",
      "progressive": false
    },
    {
      "id": "fortuna_roubada",
      "name": "Fortuna Roubada",
      "category": "leve",
      "description": "recebe metade do ouro",
      "progressive": false
    },
    {
      "id": "azar_sobrenatural",
      "name": "Azar Sobrenatural",
      "category": "leve",
      "description": "primeiro 20 natural não crita",
      "progressive": false
    },
    {
      "id": "marca_cacador",
      "name": "Marca do Caçador",
      "category": "leve",
      "description": "inimigos recebem +1 contra você",
      "progressive": false
    },
    {
      "id": "corpo_exausto",
      "name": "Corpo Exausto",
      "category": "media",
      "description": "ações custam +1 fome e sede",
      "progressive": false
    },
    {
      "id": "carne_fragil",
      "name": "Carne Frágil",
      "category": "media",
      "description": "+2 dano recebido",
      "progressive": false
    },
    {
      "id": "sangramento_profano",
      "name": "Sangramento Profano",
      "category": "media",
      "description": "1 dano no início do turno após sofrer dano",
      "progressive": false
    },
    {
      "id": "correntes_invisiveis",
      "name": "Correntes Invisíveis",
      "category": "media",
      "description": "-3 movimento",
      "progressive": false
    },
    {
      "id": "dor_constante",
      "name": "Dor Constante",
      "category": "media",
      "description": "ações causam 1 dano",
      "progressive": false
    },
    {
      "id": "alma_quebrada",
      "name": "Alma Quebrada",
      "category": "media",
      "description": "não recebe bônus de aliados",
      "progressive": false
    },
    {
      "id": "aura_profana",
      "name": "Aura Profana",
      "category": "media",
      "description": "aliados adjacentes: -1 ataque",
      "progressive": false
    },
    {
      "id": "maldicao_ferrugem",
      "name": "Maldição da Ferrugem",
      "category": "media",
      "description": "equipamento degrada após combate",
      "progressive": false
    },
    {
      "id": "fome_eterna",
      "name": "Fome Eterna",
      "category": "grave",
      "description": "consumo sobrenatural de fome",
      "progressive": true
    },
    {
      "id": "sede_infinita",
      "name": "Sede Infinita",
      "category": "grave",
      "description": "consumo sobrenatural de sede",
      "progressive": true
    },
    {
      "id": "tocado_morte",
      "name": "Tocado pela Morte",
      "category": "grave",
      "description": "recuperação cada vez menos eficaz",
      "progressive": true
    },
    {
      "id": "licantropia",
      "name": "Licantropia",
      "category": "grave",
      "description": "transformação bestial",
      "progressive": true
    },
    {
      "id": "silencio_deuses",
      "name": "Silêncio dos Deuses",
      "category": "grave",
      "description": "não lança magias",
      "progressive": false
    },
    {
      "id": "voz_quebrada",
      "name": "Voz Quebrada",
      "category": "grave",
      "description": "bardo não usa Canções",
      "progressive": false
    },
    {
      "id": "espirito_covarde",
      "name": "Espírito Covarde",
      "category": "grave",
      "description": "-2 Vontade; falha contra medo",
      "progressive": false
    },
    {
      "id": "eco_morte",
      "name": "Eco da Morte",
      "category": "grave",
      "description": "aliado morto causa 10 dano",
      "progressive": false
    },
    {
      "id": "corrupcao_crescente",
      "name": "Corrupção Crescente",
      "category": "grave",
      "description": "gera doenças e maldições",
      "progressive": true
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
      "type": "placa",
      "nome": "Placa",
      "emoji": "🪧",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "plaque",
      "image": "placa_fincada.png"
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
      "type": "chama_viva",
      "nome": "Chama viva",
      "emoji": "🔥",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "living_flame",
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
      "type": "tumba_lapide",
      "nome": "Tumba com lápide",
      "emoji": "⚰️",
      "size": [
        1,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "tumba_lapide.png"
    },
    {
      "type": "lapide",
      "nome": "Lápide",
      "emoji": "🪦",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "lapide.png"
    },
    {
      "type": "cripta",
      "nome": "Cripta",
      "emoji": "⚰️",
      "size": [
        2,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "cripta.png"
    },
    {
      "type": "fonte_de_parede",
      "nome": "Fonte de parede",
      "emoji": "⛲",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": "fountain",
      "image": "fonte_de_parede.png",
      "charges": 2
    },
    {
      "type": "armadura",
      "nome": "Armadura",
      "emoji": "🛡️",
      "size": [
        1,
        1
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "armadura.png"
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
      "image": "estante_armas_cranios.png"
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
      "image": "carroca.png"
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
      "type": "prisao",
      "nome": "Prisão",
      "emoji": "⛓️",
      "size": [
        2,
        2
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
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
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "mesa_tortura.png"
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
      "type": "casa",
      "nome": "Casa",
      "emoji": "🏠",
      "size": [
        3,
        3
      ],
      "gira": true,
      "alto": true,
      "pisavel": false,
      "loot_capaz": false,
      "special": null,
      "image": "casa.png"
    },
    {
      "type": "brasa_chao",
      "nome": "Brasa no chão",
      "emoji": "🔥",
      "size": [
        1,
        1
      ],
      "gira": false,
      "alto": false,
      "pisavel": true,
      "loot_capaz": false,
      "special": "floor_ember",
      "image": "brasa_chao.png"
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
      "id": "rodamoinho",
      "nome": "Rodamoinho",
      "categoria": "piso",
      "cor": "#126da1",
      "solido": false,
      "oclui": false
    },
    {
      "id": "rodamoinho_profundo",
      "nome": "Rodamoinho profundo",
      "categoria": "piso",
      "cor": "#06173f",
      "solido": false,
      "oclui": false
    },
    {
      "id": "piso_congelado",
      "nome": "Piso congelado",
      "categoria": "piso",
      "cor": "#78c8e2",
      "solido": false,
      "oclui": false
    },
    {
      "id": "planicie_nevada",
      "nome": "Planície nevada",
      "categoria": "piso",
      "cor": "#d8edf2",
      "solido": false,
      "oclui": false
    },
    {
      "id": "lava",
      "nome": "Lava",
      "categoria": "piso",
      "cor": "#d63b13",
      "solido": false,
      "oclui": false,
      "custo_mov": 2
    },
    {
      "id": "pantano",
      "nome": "Pântano",
      "categoria": "piso",
      "cor": "#354e31",
      "solido": false,
      "oclui": false,
      "custo_mov": 1
    },
    {
      "id": "areia_deserto",
      "nome": "Areia do deserto",
      "categoria": "piso",
      "cor": "#c49a58",
      "solido": false,
      "oclui": false,
      "custo_mov": 2
    },
    {
      "id": "duna_deserto",
      "nome": "Duna do deserto",
      "categoria": "parede",
      "cor": "#b9823f",
      "solido": false,
      "oclui": false
    },
    {
      "id": "caverna_congelada",
      "nome": "Parede de caverna congelada",
      "categoria": "parede",
      "cor": "#4b8fa8",
      "solido": false,
      "oclui": false
    },
    {
      "id": "duna_neve",
      "nome": "Duna de neve",
      "categoria": "parede",
      "cor": "#c9e5ef",
      "solido": false,
      "oclui": false
    },
    {
      "id": "rocha",
      "nome": "Rocha",
      "categoria": "parede",
      "cor": "#4a4746",
      "solido": false,
      "oclui": false
    },
    {
      "id": "rocha_marrom",
      "nome": "Rocha marrom",
      "categoria": "parede",
      "cor": "#754b32",
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
