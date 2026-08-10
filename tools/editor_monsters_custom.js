window.EDITOR_CUSTOM_MONSTERS = [
  {
    "type": "soldado",
    "name": "soldado",
    "emoji": "👹",
    "tier": 1,
    "cr": 1.0,
    "base_hp": 10,
    "hp": 11,
    "natural_armor": 0,
    "ac": 11,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 1,
    "caster_level": 1,
    "str_": 14,
    "dex": 12,
    "con_": 12,
    "int_": 10,
    "fort_base": 1,
    "ref_base": 1,
    "will_base": 1,
    "fort": 2,
    "ref_": 2,
    "will": 1,
    "attacks": [
      {
        "name": "Ataque",
        "damage": "1d4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 2,
        "base_attack_bonus": 0,
        "atk_bonus": 2,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
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
      }
    ],
    "monster_abilities": [
      {
        "id": "hero_warrior_mira_certeira",
        "uses_per_day": 3,
        "cooldown_turns": 4
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "acid",
        "name": "Ácido",
        "multiplier": 2
      }
    ],
    "equipment_enabled": true,
    "equipped_items": [
      "longsword",
      "chainmail",
      "escudo_p",
      "helm_iron",
      "health_potion",
      "cantil_agua",
      "caneca_cerveja",
      "rede_arremesso",
      "granada"
    ],
    "equipment": [
      "longsword",
      "chainmail",
      "escudo_p",
      "helm_iron",
      "health_potion",
      "cantil_agua",
      "caneca_cerveja",
      "rede_arremesso",
      "granada"
    ],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [
      {
        "kind": "gold",
        "amount": 15,
        "chance": 100
      }
    ],
    "gold": 0,
    "xp": 25,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "nova_criatura_customizado",
    "portrait": "nova_criatura_customizado",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "medio",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "raca_padrao",
    "boss": false
  },
  {
    "type": "sentinela_teste",
    "name": "Sentinela de Teste",
    "emoji": "👹",
    "tier": 1,
    "cr": 1.0,
    "base_hp": 10,
    "hp": 12,
    "natural_armor": 0,
    "ac": 11,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 3,
    "caster_level": 1,
    "str_": 16,
    "dex": 12,
    "con_": 14,
    "int_": 8,
    "fort_base": 1,
    "ref_base": 0,
    "will_base": 0,
    "fort": 3,
    "ref_": 1,
    "will": -1,
    "attacks": [
      {
        "name": "Martelo",
        "damage": "1d8+2",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 3,
        "base_attack_bonus": 3,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
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
        "cooldown_turns": 6
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
      }
    ],
    "monster_abilities": [
      {
        "id": "hero_warrior_mira_certeira",
        "uses_per_day": 3,
        "cooldown_turns": 6
      },
      {
        "id": "guild_brutalidade",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [],
    "equipment_enabled": true,
    "equipped_items": [
      "warhammer",
      "chainmail",
      "escudo_p"
    ],
    "equipment": [
      "warhammer",
      "chainmail",
      "escudo_p"
    ],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "armadura",
    "portrait": "armadura",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "medio",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "raca_padrao",
    "boss": false
  },
  {
    "type": "rato_gigante",
    "name": "Rato Gigante",
    "emoji": "🐭",
    "tier": 1,
    "cr": 0.125,
    "base_hp": 4,
    "hp": 4,
    "natural_armor": 1,
    "ac": 14,
    "movement": 6,
    "vision_base": 4,
    "visao_escuro": true,
    "base_attack_bonus": 0,
    "caster_level": 1,
    "str_": 10,
    "dex": 16,
    "con_": 11,
    "int_": 2,
    "fort_base": 0,
    "ref_base": 3,
    "will_base": 0,
    "fort": 0,
    "ref_": 6,
    "will": -4,
    "attacks": [
      {
        "name": "Ataque",
        "damage": "1d4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 0,
        "base_attack_bonus": 0,
        "atk_bonus": 0,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
      {
        "id": "infeccao",
        "name": "Infecção",
        "action_type": "passiva",
        "dc": 10,
        "save": "fortitude",
        "descricao": "Ao acertar: alvo testa Fortitude CD 10 ou contrai 1 sintoma leve",
        "source": "monstro",
        "uses_per_day": 20,
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
        "id": "olfato_agucado",
        "name": "Olfato Aguçado",
        "action_type": "passiva",
        "descricao": "Detecta invisíveis e impede ocultação.",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_abilities": [
      {
        "id": "infeccao",
        "uses_per_day": 20,
        "cooldown_turns": 0
      },
      {
        "id": "predador_oportunista",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "olfato_agucado",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "cacador",
    "ai_tactics": [],
    "image": "rato_gicante",
    "portrait": "rato_gicante",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "pequeno",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "animal",
    "boss": false
  },
  {
    "type": "escorpiao_de_pedra_customizado",
    "name": "Escorpião de Pedra",
    "emoji": "🦂",
    "tier": 1,
    "cr": 1.0,
    "base_hp": 11,
    "hp": 12,
    "natural_armor": 3,
    "ac": 14,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 2,
    "caster_level": 1,
    "str_": 10,
    "dex": 12,
    "con_": 12,
    "int_": 1,
    "fort_base": 3,
    "ref_base": 2,
    "will_base": 5,
    "fort": 4,
    "ref_": 3,
    "will": 0,
    "attacks": [
      {
        "name": "Pinça",
        "damage": "1d4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 2,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 0,
        "base_attack_bonus": 2,
        "atk_bonus": 2,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      },
      {
        "name": "Ferrão",
        "damage": "1d4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 0,
        "base_attack_bonus": 2,
        "atk_bonus": 2,
        "range": null,
        "on_hit": "veneno_escorpiao_pedra",
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
      {
        "id": "envenenar",
        "name": "Envenenar",
        "action_type": "passiva",
        "attack_index": 1,
        "veneno_id": "veneno_escorpiao_pedra",
        "poison_dc": 10,
        "descricao": "Vincula um veneno escolhido a um dos ataques da criatura.",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_abilities": [
      {
        "id": "envenenar",
        "uses_per_day": 1,
        "cooldown_turns": 0,
        "attack_index": 1,
        "veneno_id": "veneno_escorpiao_pedra",
        "poison_dc": 10
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "physical",
        "categoria": "contundente",
        "name": "Contundente",
        "bonus_flat": 2,
        "descricao": "Fraqueza a Contundente: recebe +1 dano"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "escorpiaodepedra",
    "portrait": "escorpiaodepedra",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "medio",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "animal",
    "boss": false
  },
  {
    "type": "urso_negro_customizado",
    "name": "Urso Negro",
    "emoji": "🐻",
    "tier": 1,
    "cr": 1.0,
    "base_hp": 16,
    "hp": 18,
    "natural_armor": 2,
    "ac": 13,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 2,
    "caster_level": 1,
    "str_": 18,
    "dex": 12,
    "con_": 14,
    "int_": 2,
    "fort_base": 3,
    "ref_base": 2,
    "will_base": 5,
    "fort": 5,
    "ref_": 3,
    "will": 1,
    "attacks": [
      {
        "name": "Mordida",
        "damage": "1d8+4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 4,
        "base_attack_bonus": 2,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      },
      {
        "name": "Garra",
        "damage": "1d6+4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 4,
        "base_attack_bonus": 2,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
      {
        "id": "furia",
        "name": "Fúria",
        "action_type": "passiva",
        "descricao": "Com HP < 50%: +2 de dano em todos os ataques",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_abilities": [
      {
        "id": "furia",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "physical",
        "categoria": "contundente",
        "name": "Contundente",
        "bonus_flat": 1,
        "descricao": "Corpo massivo: -1 dano de concussão (martelos, maças, bastões)"
      },
      {
        "type": "physical",
        "categoria": "perfurante",
        "name": "Perfurante",
        "bonus_flat": 1,
        "descricao": "Corpo massivo: +1 dano de perfuração/alcance (arcos, bestas, lanças)"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "ursoNegro",
    "portrait": "ursonegro",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "grande",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "animal",
    "boss": false
  },
  {
    "type": "esqueleto_animal_customizado",
    "name": "Esqueleto Animal",
    "emoji": "🦴",
    "tier": 1,
    "cr": 0.5,
    "base_hp": 8,
    "hp": 8,
    "natural_armor": 1,
    "ac": 13,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": true,
    "base_attack_bonus": 3,
    "caster_level": 1,
    "str_": 12,
    "dex": 14,
    "con_": 10,
    "int_": 2,
    "fort_base": 2,
    "ref_base": 2,
    "will_base": 4,
    "fort": 2,
    "ref_": 4,
    "will": 0,
    "attacks": [
      {
        "name": "Mordida",
        "damage": "1d6+2",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 1,
        "base_attack_bonus": 3,
        "atk_bonus": 4,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
      {
        "id": "movimento_erratico",
        "name": "Movimento Errático",
        "action_type": "passiva",
        "descricao": "Ignora terreno difícil — avança sem hesitar",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "sem_instinto",
        "name": "Sem Instinto",
        "action_type": "passiva",
        "descricao": "Nunca foge nem recua — avança até ser destruído",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_abilities": [
      {
        "id": "movimento_erratico",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "sem_instinto",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [
      "fraqueza_magica"
    ],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "physical",
        "categoria": "cortante",
        "name": "Cortante",
        "bonus_flat": 1,
        "descricao": "Resistência a cortante (-1 dano)"
      },
      {
        "type": "physical",
        "categoria": "contundente",
        "name": "Contundente",
        "bonus_flat": 2,
        "descricao": "Vulnerável a impacto (+2 dano)"
      },
      {
        "type": "physical",
        "categoria": "perfurante",
        "name": "Perfurante",
        "bonus_flat": 1,
        "descricao": "Resistência a perfurante (-2 dano)"
      },
      {
        "source_ability": "fraqueza_magica",
        "type": "save_penalty",
        "save": "vontade",
        "bonus_flat": -2,
        "em_magia": true,
        "descricao": "Fraqueza mágica: -2 em Vontade contra controle de mortos-vivos"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "esqueletoAnimal",
    "portrait": "esqueletoanimal",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "medio",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": true,
    "subtipo": "morto_vivo",
    "boss": false
  },
  {
    "type": "escorpiao_pequeno",
    "name": "escorpiao pequeno",
    "emoji": "👹",
    "overwrite_native": false,
    "tier": 1,
    "cr": 1.0,
    "base_hp": 1,
    "hp": 1,
    "natural_armor": 0,
    "ac": 11,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 0,
    "caster_level": 1,
    "str_": 3,
    "dex": 12,
    "con_": 8,
    "int_": 3,
    "fort_base": 0,
    "ref_base": 0,
    "will_base": 0,
    "fort": -1,
    "ref_": 1,
    "will": -4,
    "attacks": [
      {
        "name": "Ataque",
        "damage": "1",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": -4,
        "base_attack_bonus": 0,
        "atk_bonus": -4,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 12,
        "extra_damage": "1",
        "extra_damage_types": [
          "poison"
        ]
      }
    ],
    "special_abilities": [],
    "monster_abilities": [],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "emboscador",
    "ai_tactics": [],
    "image": "escorpiaodepedra_original",
    "portrait": "nova_criatura_customizado",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "minusculo",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "animal",
    "boss": false
  },
  {
    "type": "esqueleto_humano_customizado",
    "name": "Esqueleto Humano",
    "emoji": "💀",
    "overwrite_native": false,
    "tier": 1,
    "cr": 0.5,
    "base_hp": 10,
    "hp": 10,
    "natural_armor": 1,
    "ac": 12,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": true,
    "base_attack_bonus": 2,
    "caster_level": 1,
    "str_": 10,
    "dex": 12,
    "con_": 10,
    "int_": 2,
    "fort_base": 2,
    "ref_base": 2,
    "will_base": 4,
    "fort": 2,
    "ref_": 3,
    "will": 0,
    "attacks": [
      {
        "name": "Espada Curta",
        "damage": "1d6",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 0,
        "base_attack_bonus": 2,
        "atk_bonus": 2,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
      {
        "id": "sem_dor",
        "name": "Sem Dor",
        "action_type": "passiva",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "corpo_inerte",
        "name": "Corpo Inerte",
        "action_type": "passiva",
        "source": "monstro",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_abilities": [
      {
        "id": "sem_dor",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "corpo_inerte",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [
      "fraqueza_magica"
    ],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "physical",
        "categoria": "cortante",
        "name": "Cortante",
        "bonus_flat": 1,
        "descricao": "Resistência a cortante (-1 dano)"
      },
      {
        "type": "physical",
        "categoria": "contundente",
        "name": "Contundente",
        "bonus_flat": 2,
        "descricao": "Vulnerável a impacto (+2 dano)"
      },
      {
        "type": "physical",
        "categoria": "perfurante",
        "name": "Perfurante",
        "bonus_flat": 1,
        "descricao": "Resistência a perfurante (-2 dano)"
      },
      {
        "source_ability": "fraqueza_magica",
        "type": "save_penalty",
        "save": "vontade",
        "bonus_flat": -2,
        "em_magia": true,
        "descricao": "Fraqueza mágica: -2 em Vontade contra controle de mortos-vivos"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "esqueletoHumano",
    "portrait": "esqueletohumano_original",
    "size": [
      1,
      1
    ],
    "oriented": false,
    "porte": "medio",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": true,
    "subtipo": "morto_vivo",
    "boss": false
  },
  {
    "type": "grotao_customizado",
    "name": "Grotão",
    "emoji": "🦂",
    "overwrite_native": false,
    "tier": 1,
    "cr": 3.0,
    "base_hp": 33,
    "hp": 36,
    "natural_armor": 5,
    "ac": 15,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 2,
    "caster_level": 1,
    "str_": 18,
    "dex": 10,
    "con_": 16,
    "int_": 3,
    "fort_base": 3,
    "ref_base": 3,
    "will_base": 6,
    "fort": 6,
    "ref_": 3,
    "will": 2,
    "attacks": [
      {
        "name": "Mordida",
        "damage": "1d10+4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 4,
        "base_attack_bonus": 2,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      },
      {
        "name": "Garras",
        "damage": "1d8+4",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 2,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 4,
        "base_attack_bonus": 2,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
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
      }
    ],
    "monster_abilities": [
      {
        "id": "carapaca_resistente",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "cauda_varredora",
        "uses_per_day": 1,
        "cooldown_turns": 2
      },
      {
        "id": "cuspir_acido",
        "uses_per_day": 1,
        "cooldown_turns": 3,
        "damage_dice": 2,
        "damage_faces": 6,
        "range": 3,
        "dc": 13
      },
      {
        "id": "furia_bestial",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [
      "corpo_pesado"
    ],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "source_ability": "corpo_pesado",
        "type": "corpo_pesado",
        "descricao": "Corpo Pesado: ao falhar em Reflexos, recebe +1 dano daquele efeito."
      },
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
        "descricao": "Ponto Vulnerável: ataques nos quadrados selecionados ignoram a armadura natural (Destreza permanece) e reduções de dano (–0,25 ND estimado)"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {},
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "agressivo",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "grotao",
    "portrait": "grotao_customizado",
    "size": [
      2,
      2
    ],
    "oriented": false,
    "porte": "grande",
    "spawn_min": 0,
    "spawn_max": 0,
    "undead": false,
    "subtipo": "raca_padrao",
    "boss": false
  },
  {
    "type": "crocodilo_jovem",
    "name": "Crocodilo Jovem",
    "emoji": "🐊",
    "overwrite_native": true,
    "tier": 1,
    "cr": 1.0,
    "base_hp": 14,
    "hp": 16,
    "natural_armor": 3,
    "ac": 13,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 2,
    "caster_level": 1,
    "str_": 16,
    "dex": 10,
    "con_": 14,
    "int_": 2,
    "fort_base": 3,
    "ref_base": 2,
    "will_base": 5,
    "fort": 5,
    "ref_": 2,
    "will": 1,
    "attacks": [
      {
        "name": "Mordida",
        "damage": "1d8",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 3,
        "base_attack_bonus": 2,
        "atk_bonus": 5,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
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
      }
    ],
    "monster_abilities": [
      {
        "id": "agarrar"
      },
      {
        "id": "atq_mandibula"
      },
      {
        "id": "arrastar"
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "lightning",
        "multiplier": 1.5,
        "descricao": "+50% dano elétrico (dobrado na água)"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {
      "1-100": null
    },
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "crocodilo_jovem",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "crocodiloJovem",
    "portrait": "crocodilo_jovem",
    "size": [
      2,
      2
    ],
    "oriented": true,
    "porte": "medio",
    "spawn_min": 1,
    "spawn_max": 2,
    "undead": false,
    "subtipo": "animal",
    "boss": false
  },
  {
    "type": "grotao",
    "name": "Grotão",
    "emoji": "🦂",
    "overwrite_native": true,
    "tier": 1,
    "cr": 3.0,
    "base_hp": 33,
    "hp": 36,
    "natural_armor": 5,
    "ac": 15,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 2,
    "caster_level": 1,
    "str_": 18,
    "dex": 10,
    "con_": 16,
    "int_": 3,
    "fort_base": 3,
    "ref_base": 3,
    "will_base": 6,
    "fort": 6,
    "ref_": 3,
    "will": 2,
    "attacks": [
      {
        "name": "Mordida",
        "damage": "1d10",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 1,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 4,
        "base_attack_bonus": 2,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      },
      {
        "name": "Garras",
        "damage": "1d8",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 2,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 4,
        "base_attack_bonus": 2,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
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
      }
    ],
    "monster_abilities": [
      {
        "id": "carapaca_resistente",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "cauda_varredora",
        "uses_per_day": 1,
        "cooldown_turns": 2
      },
      {
        "id": "cuspir_acido",
        "uses_per_day": 1,
        "cooldown_turns": 3,
        "damage_dice": 2,
        "damage_faces": 6,
        "range": 3,
        "dc": 13
      },
      {
        "id": "furia_bestial",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [
      "corpo_pesado"
    ],
    "immunities": [],
    "resistances": [
      {
        "type": "physical",
        "reduction": 2
      }
    ],
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
        "descricao": "Ponto Vulnerável: os dois quadrados centrais ignoram a armadura natural (CA 15 → 10; Destreza permanece) e reduções de dano (–0,25 ND estimado)"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {
      "1-100": {
        "tipo": "gold",
        "valor": "2d6"
      }
    },
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "grotao",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "grotao",
    "portrait": "grotao",
    "size": [
      2,
      2
    ],
    "oriented": true,
    "porte": "grande",
    "spawn_min": 1,
    "spawn_max": 1,
    "undead": false,
    "subtipo": "raca_padrao",
    "boss": false
  },
  {
    "type": "lagarto_carniceiro",
    "name": "Lagarto Carniceiro",
    "emoji": "🦎",
    "overwrite_native": true,
    "tier": 1,
    "cr": 2.0,
    "base_hp": 22,
    "hp": 24,
    "natural_armor": 2,
    "ac": 14,
    "movement": 6,
    "vision_base": 0,
    "visao_escuro": false,
    "base_attack_bonus": 3,
    "caster_level": 1,
    "str_": 16,
    "dex": 14,
    "con_": 14,
    "int_": 6,
    "fort_base": 2,
    "ref_base": 2,
    "will_base": 3,
    "fort": 4,
    "ref_": 4,
    "will": 1,
    "attacks": [
      {
        "name": "Mordida",
        "damage": "1d8",
        "damage_types": [
          "physical"
        ],
        "num_attacks": 2,
        "attack_attribute": "str_",
        "damage_attribute": "str_",
        "apply_attribute_damage": true,
        "attribute_mod_base": 3,
        "base_attack_bonus": 3,
        "atk_bonus": 6,
        "range": null,
        "on_hit": null,
        "on_hit_effect": null,
        "poison_dc": 10,
        "extra_damage": null,
        "extra_damage_types": []
      }
    ],
    "special_abilities": [
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
        "id": "predador_oportunista",
        "name": "Predador Oportunista",
        "action_type": "passiva",
        "descricao": "+1 nas mordidas contra alvos com menos de 50% do HP",
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
      }
    ],
    "monster_abilities": [
      {
        "id": "combo_devorador",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "predador_oportunista",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "faro_carnica",
        "uses_per_day": 1,
        "cooldown_turns": 0
      },
      {
        "id": "duas_cabecas",
        "uses_per_day": 1,
        "cooldown_turns": 0
      }
    ],
    "monster_spells": [],
    "negative_ability_ids": [],
    "immunities": [],
    "resistances": [],
    "weaknesses": [
      {
        "type": "veneno_dobrado",
        "descricao": "Sensível a venenos: todos os efeitos dobrados"
      }
    ],
    "equipment_enabled": false,
    "equipped_items": [],
    "equipment": [],
    "guaranteed_loot": [],
    "loot_table": {
      "1-100": null
    },
    "loot_drops": [],
    "gold": 0,
    "xp": 0,
    "ai_type": "lagarto_carniceiro",
    "ai_profile": "agressivo",
    "ai_tactics": [],
    "image": "lagartoCarniceiro",
    "portrait": "lagarto_carniceiro",
    "size": [
      2,
      2
    ],
    "oriented": true,
    "porte": "grande",
    "spawn_min": 1,
    "spawn_max": 1,
    "undead": false,
    "subtipo": "animal",
    "boss": false,
    "garra_attack": {
      "name": "Garra",
      "atk_bonus": 5,
      "damage": "1d6+3",
      "damage_types": [
        "physical"
      ],
      "num_attacks": 1,
      "on_hit": null,
      "categoria": "cortante"
    }
  }
];
// GERADO pelo servidor ao salvar no Editor de criaturas.
