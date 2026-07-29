window.EDITOR_CUSTOM_ITEMS = [
  {
    "id": "ensaio_sobre_a_cegueira",
    "name": "Ensaio sobre a Cegueira",
    "emoji": "☠️",
    "item_type": "poison",
    "item_slot": "bag",
    "effect": "coat_poison",
    "custom": true,
    "operacao": "cegar",
    "save": "fortitude",
    "dificuldade": 14,
    "anula": false,
    "duracao": "1d4",
    "allowed_classes": [],
    "price": 40,
    "disponibilidade": {
      "loja": true,
      "baus": true,
      "loot_monstro": true
    },
    "descricao": "Forte veneno a base da seiva leitosa de plantas venenosas provoca cegueira.",
    "duracao_falha": "1d4",
    "penalidade_falha": [
      [
        "percepcao",
        -1
      ],
      [
        "percepcao",
        -4
      ]
    ],
    "penalidade_ataque": -4,
    "bloqueia_distancia": true
  },
  {
    "id": "bota_dos_passos_largos",
    "name": "Bota dos passos largos",
    "emoji": "👢",
    "item_type": "boots",
    "kind": "boots",
    "item_slot": "boots",
    "custom": true,
    "bonuses": [
      {
        "effect": "spd",
        "value": 2
      }
    ],
    "granted_ability": "guild_tecnica_pressa",
    "allowed_classes": [],
    "price": 1,
    "disponibilidade": {
      "loja": true,
      "baus": false,
      "loot_monstro": false
    },
    "corrosion_materials": [
      "metal"
    ],
    "corrosao_resistente": 0,
    "corrosao_niveis_penalidade": 2
  }
];
// GERADO pelo servidor ao salvar no Editor de itens.
