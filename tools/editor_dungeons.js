window.EDITOR_DUNGEONS = [
  {
    "file": "Arena.json",
    "id": "Arena",
    "name": "Arena",
    "defn": {
      "schema_version": 1,
      "id": "Arena",
      "name": "Arena",
      "ambiente": "masmorra",
      "grid": {
        "w": 16,
        "h": 16
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 6,
          "y": 12,
          "w": 4,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 1,
          "x": 1,
          "y": 1,
          "w": 14,
          "h": 10,
          "role": "monster",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 7,
        "y": 13
      },
      "exit": null,
      "monsters": [
        {
          "type": "escorpiao_pedra",
          "pos": [
            7,
            5
          ],
          "room_id": 1,
          "boss": false,
          "target": false
        }
      ],
      "chests": [],
      "traps": [],
      "decorations": [
        {
          "id": "decor_0",
          "type": "coluna",
          "pos": [
            3,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_1",
          "type": "coluna",
          "pos": [
            3,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_2",
          "type": "coluna",
          "pos": [
            12,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_3",
          "type": "coluna",
          "pos": [
            12,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        }
      ],
      "secret_passages": [],
      "falas": [
        {
          "id": "fala_2",
          "pos": [
            7,
            5
          ],
          "falante": {
            "nome": "Claudionor",
            "emoji": "🧙"
          },
          "texto": "vem me enfrentar, bundão!",
          "trigger": {
            "tipo": "proximidade",
            "raio": 3
          }
        }
      ],
      "master_reinforcements": [],
      "expected_party": {
        "heroes": 4,
        "level": 1
      },
      "prisoner": null,
      "materiais": {
        "1,2": "terra",
        "2,2": "terra",
        "2,3": "terra",
        "2,4": "terra",
        "3,4": "terra",
        "3,5": "terra",
        "4,6": "terra",
        "4,7": "terra",
        "5,7": "terra",
        "6,7": "terra",
        "6,8": "terra",
        "7,8": "terra",
        "8,8": "terra",
        "8,9": "terra",
        "9,9": "terra",
        "10,9": "terra",
        "11,10": "terra",
        "12,10": "terra",
        "13,10": "terra",
        "13,9": "terra",
        "14,9": "terra",
        "14,10": "terra",
        "14,8": "terra",
        "14,7": "terra",
        "14,6": "terra",
        "14,5": "terra",
        "14,4": "terra",
        "14,3": "terra",
        "14,2": "terra",
        "14,1": "terra",
        "13,1": "terra",
        "12,1": "terra",
        "11,1": "terra",
        "10,1": "terra",
        "9,1": "terra",
        "8,1": "terra",
        "7,1": "terra",
        "6,1": "terra",
        "5,1": "terra",
        "4,1": "terra",
        "3,1": "terra",
        "2,1": "terra",
        "1,3": "terra",
        "1,4": "terra",
        "1,5": "terra",
        "1,6": "terra",
        "1,7": "terra",
        "1,8": "terra",
        "1,9": "terra",
        "1,10": "terra",
        "2,10": "terra",
        "3,10": "terra",
        "4,10": "terra",
        "5,10": "terra",
        "6,10": "terra",
        "7,10": "terra",
        "8,10": "terra",
        "9,10": "terra",
        "10,10": "terra",
        "12,9": "terra",
        "7,9": "terra",
        "6,9": "terra",
        "5,9": "terra",
        "4,9": "terra",
        "3,9": "terra",
        "2,9": "terra",
        "2,8": "terra",
        "2,7": "terra",
        "2,6": "terra",
        "2,5": "terra",
        "3,6": "terra",
        "3,7": "terra",
        "3,8": "terra",
        "4,8": "terra",
        "5,8": "terra",
        "9,8": "terra",
        "10,8": "terra",
        "11,8": "terra",
        "12,8": "terra",
        "13,8": "terra",
        "13,7": "terra",
        "13,6": "terra",
        "13,5": "terra",
        "13,4": "terra",
        "13,3": "terra",
        "13,2": "terra",
        "12,2": "terra",
        "11,2": "terra",
        "10,2": "terra",
        "9,2": "terra",
        "8,2": "terra",
        "7,2": "terra",
        "6,2": "terra",
        "5,2": "terra",
        "4,2": "terra",
        "3,2": "terra",
        "3,3": "terra",
        "4,3": "terra",
        "5,3": "terra",
        "6,3": "terra",
        "7,3": "terra",
        "8,3": "terra",
        "9,3": "terra",
        "10,3": "terra",
        "11,3": "terra",
        "12,3": "terra",
        "12,4": "terra",
        "12,5": "terra",
        "12,6": "terra",
        "12,7": "terra",
        "11,7": "terra",
        "10,7": "terra",
        "9,7": "terra",
        "8,7": "terra",
        "7,7": "terra",
        "7,6": "terra",
        "8,6": "terra",
        "9,6": "terra",
        "10,5": "terra",
        "11,6": "terra",
        "11,5": "terra",
        "11,4": "terra",
        "10,4": "terra",
        "9,4": "terra",
        "8,4": "terra",
        "6,4": "terra",
        "5,4": "terra",
        "4,4": "terra",
        "4,5": "terra",
        "5,5": "terra",
        "6,5": "terra",
        "8,5": "terra",
        "9,5": "terra",
        "6,6": "terra",
        "5,6": "terra",
        "7,11": "terra",
        "8,11": "terra",
        "7,12": "terra",
        "8,12": "terra",
        "6,13": "terra",
        "6,14": "terra",
        "7,14": "terra",
        "8,14": "terra",
        "9,14": "terra",
        "9,13": "terra",
        "9,12": "terra",
        "6,12": "terra",
        "7,13": "terra",
        "8,13": "terra",
        "6,11": "terra",
        "9,11": "terra",
        "10,6": "terra",
        "11,9": "terra",
        "0,0": "enegrecida",
        "0,2": "enegrecida",
        "0,1": "enegrecida",
        "0,3": "enegrecida",
        "0,4": "enegrecida",
        "0,5": "enegrecida",
        "0,6": "enegrecida",
        "0,7": "enegrecida",
        "0,8": "enegrecida",
        "0,9": "enegrecida",
        "0,10": "enegrecida",
        "0,11": "enegrecida",
        "1,11": "enegrecida",
        "2,11": "enegrecida",
        "3,11": "enegrecida",
        "4,11": "enegrecida",
        "5,11": "enegrecida",
        "5,12": "enegrecida",
        "5,13": "enegrecida",
        "5,14": "enegrecida",
        "5,15": "enegrecida",
        "6,15": "enegrecida",
        "7,15": "enegrecida",
        "8,15": "enegrecida",
        "9,15": "enegrecida",
        "10,15": "enegrecida",
        "10,14": "enegrecida",
        "10,13": "enegrecida",
        "10,12": "enegrecida",
        "10,11": "enegrecida",
        "11,11": "enegrecida",
        "12,11": "enegrecida",
        "13,11": "enegrecida",
        "14,11": "enegrecida",
        "15,11": "enegrecida",
        "15,9": "enegrecida",
        "15,10": "enegrecida",
        "15,8": "enegrecida",
        "15,7": "enegrecida",
        "15,6": "enegrecida",
        "15,5": "enegrecida",
        "15,4": "enegrecida",
        "15,3": "enegrecida",
        "15,2": "enegrecida",
        "15,1": "enegrecida",
        "15,0": "enegrecida",
        "14,0": "enegrecida",
        "13,0": "enegrecida",
        "12,0": "enegrecida",
        "11,0": "enegrecida",
        "10,0": "enegrecida",
        "9,0": "enegrecida",
        "8,0": "enegrecida",
        "7,0": "enegrecida",
        "6,0": "enegrecida",
        "5,0": "enegrecida",
        "4,0": "enegrecida",
        "3,0": "enegrecida",
        "2,0": "enegrecida",
        "1,0": "enegrecida",
        "4,12": "enegrecida",
        "4,13": "enegrecida",
        "4,14": "enegrecida",
        "4,15": "enegrecida",
        "11,12": "enegrecida",
        "11,13": "enegrecida",
        "11,14": "enegrecida",
        "11,15": "enegrecida",
        "12,15": "enegrecida",
        "13,15": "enegrecida",
        "14,15": "enegrecida",
        "15,15": "enegrecida",
        "15,14": "enegrecida",
        "15,13": "enegrecida",
        "15,12": "enegrecida",
        "14,12": "enegrecida",
        "13,12": "enegrecida",
        "12,12": "enegrecida",
        "12,13": "enegrecida",
        "12,14": "enegrecida",
        "13,13": "enegrecida",
        "13,14": "enegrecida",
        "14,14": "enegrecida",
        "14,13": "enegrecida",
        "3,12": "enegrecida",
        "3,13": "enegrecida",
        "3,14": "enegrecida",
        "3,15": "enegrecida",
        "0,15": "enegrecida",
        "1,15": "enegrecida",
        "2,15": "enegrecida",
        "2,14": "enegrecida",
        "2,13": "enegrecida",
        "2,12": "enegrecida",
        "1,12": "enegrecida",
        "0,12": "enegrecida",
        "0,13": "enegrecida",
        "0,14": "enegrecida",
        "1,14": "enegrecida",
        "1,13": "enegrecida",
        "1,1": "terra",
        "7,4": "terra",
        "7,5": "terra"
      },
      "objectives": {
        "primary": {
          "type": "kill_all",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "_teste_materiais.json",
    "id": "_teste_materiais",
    "name": "Teste Materiais",
    "defn": {
      "schema_version": 1,
      "id": "_teste_materiais",
      "name": "Teste Materiais",
      "grid": {
        "w": 8,
        "h": 5
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 6,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 1,
        "y": 2
      },
      "materiais": {
        "2,1": "grama",
        "3,1": "grama",
        "4,1": "terra",
        "5,1": "pedra_negra",
        "4,2": "entulho",
        "0,2": "enegrecida",
        "7,2": "desmoronada",
        "0,0": "pedra_caverna"
      }
    }
  },
  {
    "file": "amostra.json",
    "id": "amostra",
    "name": "Amostra",
    "defn": {
      "schema_version": 1,
      "id": "amostra",
      "name": "Amostra",
      "grid": {
        "w": 8,
        "h": 6
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          2,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 4,
          "h": 4,
          "role": "entrance",
          "locked": false,
          "doors": [
            [
              5,
              2
            ]
          ]
        }
      ],
      "entrance": {
        "x": 2,
        "y": 2
      },
      "exit": {
        "x": 6,
        "y": 2
      },
      "monsters": [
        {
          "type": "goblin",
          "pos": [
            3,
            3
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            2,
            3
          ],
          "gold": 20,
          "items": [
            {
              "id": "health_potion"
            }
          ],
          "key_objective": false
        }
      ],
      "traps": [
        {
          "tipo": "fosso_estacas",
          "pos": [
            4,
            1
          ]
        }
      ],
      "prisoner": {
        "pos": [
          4,
          4
        ],
        "room_id": 0
      },
      "objectives": {
        "primary": {
          "type": "kill_all"
        },
        "secondary": []
      }
    }
  },
  {
    "file": "casa_secreta.json",
    "id": "casa_secreta",
    "name": "casa_secreta",
    "defn": {
      "schema_version": 1,
      "id": "casa_secreta",
      "name": "casa_secreta",
      "ambiente": "masmorra",
      "grid": {
        "w": 11,
        "h": 16
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 1,
          "x": 7,
          "y": 12,
          "w": 3,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 8,
        "y": 14
      },
      "exit": {
        "x": 4,
        "y": 2
      },
      "monsters": [],
      "chests": [],
      "traps": [],
      "decorations": [
        {
          "id": "decor_0",
          "type": "cama",
          "pos": [
            6,
            6
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "key_objective": true
        },
        {
          "id": "decor_1",
          "type": "estante",
          "pos": [
            9,
            7
          ],
          "facing": [
            0,
            -1
          ],
          "loot": null,
          "key_objective": true
        },
        {
          "id": "decor_2",
          "type": "lareira",
          "pos": [
            1,
            11
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "key_objective": false,
          "size": [
            1,
            1
          ]
        },
        {
          "id": "decor_3",
          "type": "mesa_cadeiras",
          "pos": [
            3,
            11
          ],
          "facing": [
            0,
            -1
          ],
          "loot": null,
          "key_objective": false,
          "size": [
            2,
            2
          ]
        },
        {
          "id": "decor_4",
          "type": "estante_livros",
          "pos": [
            4,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "size": [
            1,
            1
          ]
        },
        {
          "id": "decor_5",
          "type": "barril",
          "pos": [
            1,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_6",
          "type": "barril",
          "pos": [
            2,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_7",
          "type": "barril",
          "pos": [
            1,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_8",
          "type": "gaiola",
          "pos": [
            9,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": true
        },
        {
          "id": "decor_9",
          "type": "arca_tesouros",
          "pos": [
            9,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "key_objective": false,
          "chest_trap_monster_type": "goblin_dual"
        },
        {
          "id": "decor_10",
          "type": "chao",
          "pos": [
            6,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "chaotapete1.png",
          "vscale": [
            4,
            3.2
          ]
        }
      ],
      "secret_passages": [
        {
          "id": "passage_0",
          "type": "mechanism",
          "pos": [
            8,
            5
          ],
          "key_decor_ids": [
            "decor_1"
          ],
          "keys_mode": "any"
        },
        {
          "id": "passage_1",
          "type": "mechanism",
          "pos": [
            9,
            5
          ],
          "key_decor_ids": [
            "decor_1"
          ],
          "keys_mode": "any"
        },
        {
          "id": "passage_2",
          "type": "mechanism",
          "pos": [
            8,
            4
          ],
          "key_decor_ids": [
            "decor_0"
          ],
          "keys_mode": "any"
        },
        {
          "id": "passage_3",
          "type": "mechanism",
          "pos": [
            9,
            4
          ],
          "key_decor_ids": [
            "decor_0",
            "decor_1"
          ],
          "keys_mode": "all"
        }
      ],
      "falas": [],
      "master_reinforcements": [],
      "expected_party": {
        "heroes": 4,
        "level": 1
      },
      "prisoner": null,
      "materiais": {
        "0,15": "enegrecida",
        "1,15": "enegrecida",
        "2,15": "enegrecida",
        "3,15": "enegrecida",
        "4,15": "enegrecida",
        "5,15": "enegrecida",
        "6,15": "enegrecida",
        "7,15": "enegrecida",
        "8,15": "enegrecida",
        "9,15": "enegrecida",
        "10,15": "enegrecida",
        "10,14": "enegrecida",
        "10,13": "enegrecida",
        "10,12": "enegrecida",
        "10,11": "enegrecida",
        "10,10": "enegrecida",
        "0,14": "enegrecida",
        "0,13": "enegrecida",
        "0,12": "enegrecida",
        "0,11": "enegrecida",
        "0,10": "enegrecida",
        "0,9": "enegrecida",
        "0,8": "enegrecida",
        "0,7": "enegrecida",
        "0,6": "enegrecida",
        "0,5": "enegrecida",
        "1,5": "enegrecida",
        "2,5": "enegrecida",
        "3,5": "enegrecida",
        "4,5": "enegrecida",
        "5,5": "enegrecida",
        "6,5": "enegrecida",
        "7,5": "enegrecida",
        "10,5": "enegrecida",
        "10,6": "enegrecida",
        "10,7": "enegrecida",
        "10,8": "enegrecida",
        "10,9": "enegrecida",
        "3,4": "enegrecida",
        "3,3": "enegrecida",
        "3,2": "enegrecida",
        "3,1": "enegrecida",
        "3,0": "enegrecida",
        "2,0": "enegrecida",
        "1,0": "enegrecida",
        "0,0": "enegrecida",
        "0,3": "enegrecida",
        "0,4": "enegrecida",
        "0,2": "enegrecida",
        "0,1": "enegrecida",
        "1,1": "enegrecida",
        "2,1": "enegrecida",
        "2,2": "enegrecida",
        "2,3": "enegrecida",
        "2,4": "enegrecida",
        "1,4": "enegrecida",
        "1,3": "enegrecida",
        "1,2": "enegrecida",
        "4,0": "enegrecida",
        "5,0": "enegrecida",
        "6,0": "enegrecida",
        "7,0": "enegrecida",
        "8,0": "enegrecida",
        "9,0": "enegrecida",
        "10,0": "enegrecida",
        "10,1": "enegrecida",
        "10,2": "enegrecida",
        "10,3": "enegrecida",
        "10,4": "enegrecida",
        "8,5": "enegrecida",
        "9,5": "enegrecida",
        "7,4": "enegrecida",
        "6,4": "enegrecida",
        "5,4": "enegrecida",
        "4,4": "enegrecida",
        "7,3": "enegrecida",
        "6,3": "enegrecida",
        "5,3": "enegrecida",
        "4,3": "enegrecida",
        "8,4": "enegrecida",
        "9,4": "enegrecida",
        "9,9": "enegrecida",
        "8,9": "enegrecida",
        "7,9": "enegrecida",
        "6,9": "enegrecida",
        "5,9": "enegrecida",
        "5,6": "enegrecida",
        "5,7": "enegrecida"
      },
      "objectives": {
        "primary": {
          "type": "reach_exit",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "caverna.json",
    "id": "caverna",
    "name": "caverna",
    "defn": {
      "schema_version": 1,
      "id": "caverna",
      "name": "caverna",
      "ambiente": "masmorra",
      "grid": {
        "w": 16,
        "h": 60
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 3,
          "y": 53,
          "w": 6,
          "h": 5,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 1,
          "x": 10,
          "y": 1,
          "w": 4,
          "h": 5,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 2,
          "x": 9,
          "y": 8,
          "w": 6,
          "h": 3,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 3,
          "x": 10,
          "y": 15,
          "w": 4,
          "h": 3,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 4,
          "x": 5,
          "y": 18,
          "w": 3,
          "h": 5,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 5,
          "x": 6,
          "y": 48,
          "w": 4,
          "h": 4,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 6,
          "x": 6,
          "y": 27,
          "w": 3,
          "h": 4,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 7,
          "x": 1,
          "y": 23,
          "w": 3,
          "h": 3,
          "role": "monster",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 6,
        "y": 56
      },
      "exit": null,
      "monsters": [
        {
          "type": "zumbi_infectado",
          "pos": [
            7,
            49
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "esqueleto_animal",
          "pos": [
            9,
            51
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "crocodilo_jovem",
          "pos": [
            7,
            29
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "grotao",
          "pos": [
            12,
            10
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "lagarto_carniceiro",
          "pos": [
            11,
            16
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "lobisomem",
          "pos": [
            12,
            2
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            10,
            5
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "lobo_cinzento",
          "pos": [
            2,
            24
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            12,
            10
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            13,
            5
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            2,
            24
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            7,
            19
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            5,
            21
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            7,
            21
          ],
          "room_id": null,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            6,
            40
          ],
          "gold": 0,
          "items": [
            {
              "id": "granada_superior"
            },
            {
              "id": "fogo_grego"
            },
            {
              "id": "granada"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            13,
            57
          ],
          "gold": 23,
          "items": [
            {
              "id": "regeneration_potion"
            },
            {
              "id": "agua_benta"
            },
            {
              "id": "agua_benta"
            },
            {
              "id": "sword"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            3,
            20
          ],
          "gold": 0,
          "items": [
            {
              "id": "racao_viagem"
            },
            {
              "id": "health_potion_concentrated"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            7,
            16
          ],
          "gold": 0,
          "items": [
            {
              "id": "ring_vita"
            },
            {
              "id": "boots"
            }
          ],
          "key_objective": false
        }
      ],
      "traps": [],
      "decorations": [],
      "secret_passages": [],
      "falas": [],
      "master_reinforcements": [],
      "expected_party": {
        "heroes": 4,
        "level": 1
      },
      "prisoner": null,
      "materiais": {
        "10,10": "terra",
        "10,9": "terra",
        "10,8": "terra",
        "10,7": "terra",
        "10,6": "terra",
        "10,5": "terra",
        "10,4": "terra",
        "10,3": "terra",
        "10,2": "terra",
        "10,1": "terra",
        "10,0": "pedra_caverna",
        "9,0": "pedra_caverna",
        "8,0": "pedra_caverna",
        "8,1": "pedra_caverna",
        "8,2": "pedra_caverna",
        "8,3": "terra",
        "8,4": "terra",
        "8,5": "terra",
        "8,6": "terra",
        "8,7": "terra",
        "8,8": "terra",
        "8,9": "pedra_caverna",
        "8,10": "pedra_caverna",
        "8,11": "pedra_caverna",
        "8,12": "pedra_caverna",
        "8,13": "pedra_caverna",
        "8,14": "pedra_caverna",
        "8,15": "terra",
        "8,16": "terra",
        "8,17": "terra",
        "8,18": "terra",
        "8,19": "terra",
        "8,20": "pedra_caverna",
        "8,21": "terra",
        "8,22": "terra",
        "8,23": "terra",
        "8,24": "terra",
        "8,25": "agua",
        "8,26": "agua",
        "8,27": "agua",
        "7,27": "agua",
        "6,27": "agua",
        "6,26": "agua",
        "6,25": "agua",
        "6,24": "terra",
        "6,23": "terra",
        "6,22": "terra",
        "6,21": "terra",
        "6,20": "terra",
        "6,19": "terra",
        "6,18": "terra",
        "6,17": "terra",
        "6,16": "terra",
        "6,15": "pedra_caverna",
        "6,14": "pedra_caverna",
        "6,13": "pedra_caverna",
        "6,12": "pedra_caverna",
        "6,11": "pedra_caverna",
        "6,10": "pedra_caverna",
        "6,9": "pedra_caverna",
        "6,8": "terra",
        "6,7": "terra",
        "6,6": "terra",
        "6,5": "terra",
        "6,4": "pedra_caverna",
        "6,3": "pedra_caverna",
        "6,2": "pedra_caverna",
        "6,1": "pedra_caverna",
        "6,0": "pedra_caverna",
        "5,0": "pedra_caverna",
        "4,0": "pedra_caverna",
        "4,1": "pedra_caverna",
        "4,2": "pedra_caverna",
        "4,3": "pedra_caverna",
        "4,4": "pedra_caverna",
        "4,5": "pedra_caverna",
        "4,6": "terra",
        "4,7": "terra",
        "4,8": "terra",
        "4,9": "terra",
        "4,10": "pedra_caverna",
        "4,11": "pedra_caverna",
        "4,12": "pedra_caverna",
        "4,13": "pedra_caverna",
        "4,14": "pedra_caverna",
        "4,15": "pedra_caverna",
        "4,16": "pedra_caverna",
        "4,17": "terra",
        "4,18": "terra",
        "4,19": "terra",
        "4,20": "terra",
        "4,21": "terra",
        "4,22": "terra",
        "4,23": "terra",
        "4,24": "terra",
        "4,25": "pedra_caverna",
        "4,26": "pedra_caverna",
        "4,27": "pedra_caverna",
        "3,27": "pedra_caverna",
        "2,27": "pedra_caverna",
        "2,26": "pedra_caverna",
        "2,25": "terra",
        "2,24": "terra",
        "2,23": "terra",
        "2,22": "terra",
        "2,21": "terra",
        "2,20": "terra",
        "2,19": "terra",
        "2,18": "terra",
        "2,17": "terra",
        "2,16": "pedra_caverna",
        "2,15": "pedra_caverna",
        "2,14": "pedra_caverna",
        "2,13": "pedra_caverna",
        "2,12": "pedra_caverna",
        "2,11": "pedra_caverna",
        "2,10": "pedra_caverna",
        "2,9": "pedra_caverna",
        "2,8": "pedra_caverna",
        "2,7": "pedra_caverna",
        "2,6": "pedra_caverna",
        "2,5": "pedra_caverna",
        "2,4": "pedra_caverna",
        "2,3": "pedra_caverna",
        "2,2": "pedra_caverna",
        "2,1": "pedra_caverna",
        "2,0": "pedra_caverna",
        "1,0": "pedra_caverna",
        "0,0": "pedra_caverna",
        "0,1": "pedra_caverna",
        "0,2": "pedra_caverna",
        "0,3": "pedra_caverna",
        "0,4": "pedra_caverna",
        "0,5": "pedra_caverna",
        "0,6": "pedra_caverna",
        "0,7": "pedra_caverna",
        "0,8": "pedra_caverna",
        "0,9": "pedra_caverna",
        "0,10": "pedra_caverna",
        "0,11": "pedra_caverna",
        "0,12": "pedra_caverna",
        "0,13": "pedra_caverna",
        "0,14": "pedra_caverna",
        "0,15": "pedra_caverna",
        "0,16": "pedra_caverna",
        "0,17": "pedra_caverna",
        "0,18": "pedra_caverna",
        "0,19": "pedra_caverna",
        "0,20": "pedra_caverna",
        "0,21": "pedra_caverna",
        "0,22": "pedra_caverna",
        "0,23": "pedra_caverna",
        "0,24": "pedra_caverna",
        "0,25": "pedra_caverna",
        "0,26": "pedra_caverna",
        "0,27": "pedra_caverna",
        "1,1": "pedra_caverna",
        "1,2": "pedra_caverna",
        "1,3": "pedra_caverna",
        "1,4": "pedra_caverna",
        "1,5": "pedra_caverna",
        "1,6": "pedra_caverna",
        "1,7": "pedra_caverna",
        "1,8": "pedra_caverna",
        "1,9": "pedra_caverna",
        "1,10": "pedra_caverna",
        "1,11": "pedra_caverna",
        "1,12": "pedra_caverna",
        "1,13": "pedra_caverna",
        "1,14": "pedra_caverna",
        "1,15": "pedra_caverna",
        "1,16": "pedra_caverna",
        "1,17": "pedra_caverna",
        "1,18": "terra",
        "1,19": "terra",
        "1,20": "terra",
        "1,21": "terra",
        "1,22": "terra",
        "1,23": "terra",
        "1,24": "terra",
        "1,25": "terra",
        "1,26": "pedra_caverna",
        "1,27": "pedra_caverna",
        "3,26": "pedra_caverna",
        "3,25": "terra",
        "3,24": "terra",
        "3,23": "terra",
        "3,22": "entulho",
        "3,21": "entulho",
        "3,20": "terra",
        "3,19": "terra",
        "3,18": "terra",
        "3,17": "terra",
        "3,16": "pedra_caverna",
        "3,15": "pedra_caverna",
        "3,14": "pedra_caverna",
        "3,13": "pedra_caverna",
        "3,12": "pedra_caverna",
        "3,11": "pedra_caverna",
        "3,10": "pedra_caverna",
        "3,9": "terra",
        "3,8": "terra",
        "3,7": "terra",
        "3,6": "pedra_caverna",
        "3,5": "pedra_caverna",
        "3,4": "pedra_caverna",
        "3,3": "pedra_caverna",
        "3,2": "pedra_caverna",
        "3,1": "pedra_caverna",
        "3,0": "pedra_caverna",
        "5,1": "pedra_caverna",
        "5,2": "pedra_caverna",
        "5,3": "pedra_caverna",
        "5,4": "pedra_caverna",
        "5,5": "pedra_caverna",
        "5,6": "terra",
        "5,7": "terra",
        "5,8": "terra",
        "5,9": "pedra_caverna",
        "5,10": "pedra_caverna",
        "5,11": "pedra_caverna",
        "5,12": "pedra_caverna",
        "5,13": "pedra_caverna",
        "5,14": "pedra_caverna",
        "5,15": "pedra_caverna",
        "5,16": "terra",
        "5,17": "terra",
        "5,18": "terra",
        "5,19": "terra",
        "5,20": "terra",
        "5,21": "terra",
        "5,22": "terra",
        "5,23": "terra",
        "5,24": "terra",
        "5,25": "pedra_caverna",
        "5,26": "pedra_caverna",
        "5,27": "pedra_caverna",
        "9,27": "pedra_caverna",
        "10,27": "pedra_caverna",
        "10,26": "pedra_caverna",
        "10,25": "pedra_caverna",
        "10,24": "pedra_caverna",
        "10,23": "pedra_caverna",
        "10,22": "pedra_caverna",
        "10,21": "pedra_caverna",
        "10,20": "pedra_caverna",
        "10,19": "terra",
        "10,18": "terra",
        "10,17": "terra",
        "10,16": "terra",
        "10,15": "terra",
        "10,14": "pedra_caverna",
        "10,13": "pedra_caverna",
        "10,12": "pedra_caverna",
        "11,12": "pedra_caverna",
        "11,11": "terra",
        "12,11": "terra",
        "12,10": "terra",
        "12,9": "terra",
        "12,8": "terra",
        "12,7": "terra",
        "12,6": "terra",
        "12,5": "terra",
        "12,4": "terra",
        "12,3": "terra",
        "12,2": "terra",
        "12,1": "terra",
        "12,0": "pedra_caverna",
        "13,0": "pedra_caverna",
        "14,0": "pedra_caverna",
        "14,1": "pedra_caverna",
        "14,2": "terra",
        "14,3": "terra",
        "14,4": "terra",
        "14,5": "terra",
        "14,6": "pedra_caverna",
        "14,7": "pedra_caverna",
        "14,8": "terra",
        "14,9": "terra",
        "14,10": "terra",
        "14,11": "terra",
        "14,12": "terra",
        "14,13": "terra",
        "14,14": "terra",
        "14,15": "terra",
        "14,16": "pedra_caverna",
        "14,17": "pedra_caverna",
        "14,18": "pedra_caverna",
        "14,19": "pedra_caverna",
        "14,20": "pedra_caverna",
        "14,21": "pedra_caverna",
        "14,22": "pedra_caverna",
        "14,23": "pedra_caverna",
        "14,24": "pedra_caverna",
        "14,25": "pedra_caverna",
        "14,26": "pedra_caverna",
        "14,27": "pedra_caverna",
        "13,27": "pedra_caverna",
        "12,27": "pedra_caverna",
        "12,26": "pedra_caverna",
        "12,25": "pedra_caverna",
        "12,24": "pedra_caverna",
        "12,23": "pedra_caverna",
        "12,22": "pedra_caverna",
        "12,21": "pedra_caverna",
        "12,20": "pedra_caverna",
        "12,19": "terra",
        "12,18": "terra",
        "12,17": "terra",
        "12,16": "terra",
        "12,15": "terra",
        "12,14": "terra",
        "12,13": "terra",
        "15,27": "pedra_caverna",
        "13,26": "pedra_caverna",
        "15,26": "pedra_caverna",
        "13,25": "pedra_caverna",
        "15,25": "pedra_caverna",
        "13,24": "pedra_caverna",
        "15,24": "pedra_caverna",
        "13,23": "pedra_caverna",
        "15,23": "pedra_caverna",
        "13,22": "pedra_caverna",
        "15,22": "pedra_caverna",
        "13,21": "pedra_caverna",
        "15,21": "pedra_caverna",
        "13,20": "pedra_caverna",
        "15,20": "pedra_caverna",
        "13,19": "terra",
        "15,19": "pedra_caverna",
        "13,18": "terra",
        "15,18": "pedra_caverna",
        "13,17": "terra",
        "15,17": "pedra_caverna",
        "13,16": "terra",
        "15,16": "pedra_caverna",
        "13,15": "terra",
        "15,15": "pedra_caverna",
        "13,14": "terra",
        "15,14": "pedra_caverna",
        "13,13": "terra",
        "15,13": "pedra_caverna",
        "13,12": "terra",
        "15,12": "pedra_caverna",
        "15,11": "pedra_caverna",
        "15,10": "pedra_caverna",
        "15,9": "pedra_caverna",
        "15,8": "pedra_caverna",
        "15,7": "pedra_caverna",
        "15,6": "pedra_caverna",
        "15,5": "pedra_caverna",
        "15,4": "pedra_caverna",
        "15,3": "pedra_caverna",
        "15,2": "pedra_caverna",
        "15,1": "pedra_caverna",
        "15,0": "pedra_caverna",
        "13,1": "terra",
        "13,2": "terra",
        "13,3": "terra",
        "13,4": "terra",
        "13,5": "terra",
        "13,6": "terra",
        "13,7": "terra",
        "13,8": "terra",
        "13,9": "terra",
        "13,10": "terra",
        "13,11": "terra",
        "12,12": "terra",
        "11,13": "pedra_caverna",
        "11,14": "terra",
        "11,15": "terra",
        "11,16": "terra",
        "11,17": "terra",
        "11,18": "terra",
        "11,19": "terra",
        "11,20": "pedra_caverna",
        "11,21": "pedra_caverna",
        "11,22": "pedra_caverna",
        "11,23": "pedra_caverna",
        "11,24": "pedra_caverna",
        "11,25": "pedra_caverna",
        "11,26": "pedra_caverna",
        "11,27": "pedra_caverna",
        "7,26": "agua",
        "9,26": "pedra_caverna",
        "7,25": "agua",
        "9,25": "pedra_caverna",
        "7,24": "agua",
        "9,24": "pedra_caverna",
        "7,23": "terra",
        "9,23": "pedra_caverna",
        "7,22": "terra",
        "9,22": "pedra_caverna",
        "7,21": "terra",
        "9,21": "pedra_caverna",
        "7,20": "terra",
        "9,20": "pedra_caverna",
        "7,19": "terra",
        "9,19": "terra",
        "7,18": "terra",
        "9,18": "terra",
        "7,17": "terra",
        "9,17": "terra",
        "7,16": "terra",
        "9,16": "terra",
        "7,15": "pedra_caverna",
        "9,15": "terra",
        "7,14": "pedra_caverna",
        "9,14": "pedra_caverna",
        "7,13": "pedra_caverna",
        "9,13": "pedra_caverna",
        "7,12": "pedra_caverna",
        "9,12": "pedra_caverna",
        "7,11": "pedra_caverna",
        "9,11": "pedra_caverna",
        "7,10": "pedra_caverna",
        "7,9": "pedra_caverna",
        "7,8": "terra",
        "7,7": "terra",
        "7,6": "terra",
        "7,5": "terra",
        "7,4": "terra",
        "7,3": "terra",
        "7,2": "pedra_caverna",
        "7,1": "pedra_caverna",
        "7,0": "pedra_caverna",
        "11,0": "pedra_caverna",
        "9,1": "pedra_caverna",
        "11,1": "terra",
        "9,2": "terra",
        "11,2": "terra",
        "9,3": "terra",
        "11,3": "terra",
        "9,4": "terra",
        "11,4": "terra",
        "9,5": "terra",
        "11,5": "terra",
        "9,6": "terra",
        "11,6": "terra",
        "9,7": "terra",
        "11,7": "terra",
        "9,8": "terra",
        "11,8": "terra",
        "9,9": "terra",
        "11,9": "terra",
        "10,11": "terra",
        "9,10": "terra",
        "11,10": "terra",
        "8,28": "agua_profunda",
        "7,28": "agua_profunda",
        "7,29": "agua_profunda",
        "6,28": "agua_profunda",
        "6,29": "agua_profunda",
        "6,30": "agua_profunda",
        "7,30": "agua_profunda",
        "8,29": "agua_profunda",
        "8,30": "agua_profunda",
        "3,34": "terra",
        "3,35": "terra",
        "3,36": "terra",
        "3,37": "terra",
        "4,37": "terra",
        "4,38": "terra",
        "5,38": "terra",
        "6,38": "terra",
        "7,38": "terra",
        "8,38": "terra",
        "8,39": "terra",
        "9,39": "terra",
        "10,39": "terra",
        "11,39": "terra",
        "12,39": "terra",
        "12,38": "terra",
        "13,38": "terra",
        "13,37": "terra",
        "13,36": "terra",
        "13,35": "terra",
        "12,35": "terra",
        "12,34": "terra",
        "11,34": "agua",
        "10,34": "agua",
        "10,33": "agua",
        "10,32": "agua",
        "9,32": "agua",
        "8,32": "agua",
        "8,31": "agua",
        "7,31": "agua",
        "6,31": "agua",
        "5,31": "agua",
        "5,32": "agua",
        "4,32": "agua",
        "4,33": "agua",
        "3,33": "terra",
        "7,39": "terra",
        "7,40": "terra",
        "6,40": "terra",
        "6,41": "terra",
        "6,42": "terra",
        "5,42": "terra",
        "5,43": "terra",
        "5,44": "terra",
        "6,44": "terra",
        "7,44": "terra",
        "8,44": "terra",
        "9,44": "terra",
        "10,44": "terra",
        "11,43": "terra",
        "11,42": "terra",
        "12,42": "terra",
        "12,41": "terra",
        "12,40": "terra",
        "11,40": "terra",
        "10,40": "terra",
        "7,34": "agua",
        "7,33": "agua",
        "7,32": "agua",
        "6,32": "agua",
        "6,33": "agua",
        "5,33": "agua",
        "5,34": "agua",
        "5,35": "terra",
        "5,36": "terra",
        "5,37": "terra",
        "6,37": "terra",
        "7,37": "terra",
        "7,36": "terra",
        "8,36": "terra",
        "8,35": "agua",
        "9,35": "agua",
        "9,34": "agua",
        "9,33": "agua",
        "10,35": "agua",
        "10,36": "terra",
        "10,37": "terra",
        "10,38": "terra",
        "9,38": "terra",
        "11,38": "terra",
        "9,37": "terra",
        "11,37": "terra",
        "12,37": "terra",
        "12,36": "terra",
        "11,36": "terra",
        "11,35": "terra",
        "9,36": "terra",
        "8,37": "terra",
        "4,36": "terra",
        "6,36": "terra",
        "4,35": "terra",
        "6,35": "terra",
        "4,34": "terra",
        "8,33": "agua",
        "7,35": "agua",
        "6,34": "agua",
        "8,34": "agua",
        "8,41": "terra",
        "8,40": "terra",
        "9,40": "terra",
        "8,42": "terra",
        "8,43": "terra",
        "7,43": "terra",
        "6,43": "terra",
        "9,43": "terra",
        "10,43": "terra",
        "10,42": "terra",
        "10,41": "terra",
        "11,41": "terra",
        "7,42": "terra",
        "9,42": "terra",
        "7,41": "terra",
        "9,41": "terra",
        "14,30": "pedra_caverna",
        "14,29": "pedra_caverna",
        "14,28": "pedra_caverna",
        "0,28": "pedra_caverna",
        "0,29": "pedra_caverna",
        "0,30": "pedra_caverna",
        "0,31": "pedra_caverna",
        "0,32": "pedra_caverna",
        "0,33": "pedra_caverna",
        "0,34": "pedra_caverna",
        "0,35": "pedra_caverna",
        "0,36": "pedra_caverna",
        "0,37": "pedra_caverna",
        "0,38": "pedra_caverna",
        "0,39": "pedra_caverna",
        "0,40": "pedra_caverna",
        "0,41": "pedra_caverna",
        "0,42": "pedra_caverna",
        "0,43": "pedra_caverna",
        "0,44": "pedra_caverna",
        "0,45": "pedra_caverna",
        "1,45": "pedra_caverna",
        "2,45": "pedra_caverna",
        "2,44": "pedra_caverna",
        "2,43": "pedra_caverna",
        "2,42": "pedra_caverna",
        "2,41": "pedra_caverna",
        "2,40": "pedra_caverna",
        "2,39": "pedra_caverna",
        "2,38": "pedra_caverna",
        "2,37": "pedra_caverna",
        "2,36": "pedra_caverna",
        "2,35": "pedra_caverna",
        "2,34": "pedra_caverna",
        "2,33": "pedra_caverna",
        "2,32": "pedra_caverna",
        "2,31": "pedra_caverna",
        "2,30": "pedra_caverna",
        "2,29": "pedra_caverna",
        "2,28": "pedra_caverna",
        "4,28": "pedra_caverna",
        "4,29": "pedra_caverna",
        "4,30": "pedra_caverna",
        "4,31": "pedra_caverna",
        "5,30": "pedra_caverna",
        "5,29": "pedra_caverna",
        "5,28": "pedra_caverna",
        "3,28": "pedra_caverna",
        "3,29": "pedra_caverna",
        "3,30": "pedra_caverna",
        "3,31": "pedra_caverna",
        "3,32": "pedra_caverna",
        "3,38": "pedra_caverna",
        "3,39": "pedra_caverna",
        "4,39": "pedra_caverna",
        "4,40": "pedra_caverna",
        "4,41": "pedra_caverna",
        "4,42": "pedra_caverna",
        "4,43": "pedra_caverna",
        "4,44": "pedra_caverna",
        "4,45": "pedra_caverna",
        "5,45": "pedra_caverna",
        "6,45": "terra",
        "7,45": "terra",
        "8,45": "terra",
        "9,45": "terra",
        "10,45": "pedra_caverna",
        "11,45": "pedra_caverna",
        "11,44": "pedra_caverna",
        "12,44": "pedra_caverna",
        "12,43": "pedra_caverna",
        "13,43": "pedra_caverna",
        "13,42": "pedra_caverna",
        "13,41": "pedra_caverna",
        "13,40": "pedra_caverna",
        "13,39": "pedra_caverna",
        "14,39": "pedra_caverna",
        "14,38": "pedra_caverna",
        "14,37": "pedra_caverna",
        "14,36": "pedra_caverna",
        "14,35": "pedra_caverna",
        "14,34": "pedra_caverna",
        "14,33": "pedra_caverna",
        "14,32": "pedra_caverna",
        "13,32": "pedra_caverna",
        "13,31": "pedra_caverna",
        "12,31": "pedra_caverna",
        "12,30": "pedra_caverna",
        "12,29": "pedra_caverna",
        "12,28": "pedra_caverna",
        "10,28": "pedra_caverna",
        "10,29": "pedra_caverna",
        "10,30": "pedra_caverna",
        "10,31": "pedra_caverna",
        "9,31": "pedra_caverna",
        "9,30": "pedra_caverna",
        "9,29": "pedra_caverna",
        "9,28": "pedra_caverna",
        "11,28": "pedra_caverna",
        "11,29": "pedra_caverna",
        "11,30": "pedra_caverna",
        "11,31": "pedra_caverna",
        "11,32": "pedra_caverna",
        "11,33": "pedra_caverna",
        "12,33": "pedra_caverna",
        "12,32": "pedra_caverna",
        "15,32": "pedra_caverna",
        "15,31": "pedra_caverna",
        "13,33": "pedra_caverna",
        "15,33": "pedra_caverna",
        "13,34": "pedra_caverna",
        "15,34": "pedra_caverna",
        "15,35": "pedra_caverna",
        "15,36": "pedra_caverna",
        "15,37": "pedra_caverna",
        "15,38": "pedra_caverna",
        "15,39": "pedra_caverna",
        "15,40": "pedra_caverna",
        "15,41": "pedra_caverna",
        "15,42": "pedra_caverna",
        "15,43": "pedra_caverna",
        "15,44": "pedra_caverna",
        "15,45": "pedra_caverna",
        "14,45": "pedra_caverna",
        "13,45": "pedra_caverna",
        "14,44": "pedra_caverna",
        "14,40": "pedra_caverna",
        "14,41": "pedra_caverna",
        "14,42": "pedra_caverna",
        "14,43": "pedra_caverna",
        "13,44": "pedra_caverna",
        "12,45": "pedra_caverna",
        "5,41": "pedra_caverna",
        "5,40": "pedra_caverna",
        "5,39": "pedra_caverna",
        "6,39": "pedra_caverna",
        "3,40": "pedra_caverna",
        "3,41": "pedra_caverna",
        "3,42": "pedra_caverna",
        "3,43": "pedra_caverna",
        "3,44": "pedra_caverna",
        "3,45": "pedra_caverna",
        "1,44": "pedra_caverna",
        "1,43": "pedra_caverna",
        "1,42": "pedra_caverna",
        "1,41": "pedra_caverna",
        "1,40": "pedra_caverna",
        "1,39": "pedra_caverna",
        "1,38": "pedra_caverna",
        "1,37": "pedra_caverna",
        "1,36": "pedra_caverna",
        "1,35": "pedra_caverna",
        "1,34": "pedra_caverna",
        "1,33": "pedra_caverna",
        "1,32": "pedra_caverna",
        "1,31": "pedra_caverna",
        "1,30": "pedra_caverna",
        "1,29": "pedra_caverna",
        "1,28": "pedra_caverna",
        "13,28": "pedra_caverna",
        "15,28": "pedra_caverna",
        "13,29": "pedra_caverna",
        "15,29": "pedra_caverna",
        "14,31": "pedra_caverna",
        "13,30": "pedra_caverna",
        "15,30": "pedra_caverna",
        "1,51": "pedra_caverna",
        "1,50": "pedra_caverna",
        "1,49": "pedra_caverna",
        "1,48": "pedra_caverna",
        "1,47": "pedra_caverna",
        "1,46": "pedra_caverna",
        "15,46": "pedra_caverna",
        "15,47": "pedra_caverna",
        "15,48": "pedra_caverna",
        "15,49": "pedra_caverna",
        "15,50": "pedra_caverna",
        "15,51": "pedra_caverna",
        "15,52": "pedra_caverna",
        "15,53": "pedra_caverna",
        "15,54": "pedra_caverna",
        "15,55": "pedra_caverna",
        "15,56": "pedra_caverna",
        "15,57": "pedra_caverna",
        "15,58": "pedra_caverna",
        "15,59": "pedra_caverna",
        "14,59": "pedra_caverna",
        "13,59": "pedra_caverna",
        "13,58": "pedra_caverna",
        "13,57": "terra",
        "13,56": "terra",
        "13,55": "terra",
        "13,54": "terra",
        "13,53": "terra",
        "13,52": "pedra_caverna",
        "13,51": "pedra_caverna",
        "13,50": "pedra_caverna",
        "13,49": "pedra_caverna",
        "13,48": "pedra_caverna",
        "13,47": "pedra_caverna",
        "13,46": "pedra_caverna",
        "11,46": "pedra_caverna",
        "11,47": "pedra_caverna",
        "11,48": "pedra_caverna",
        "11,49": "pedra_caverna",
        "11,50": "pedra_caverna",
        "11,51": "terra",
        "11,52": "terra",
        "11,53": "terra",
        "11,54": "terra",
        "11,55": "terra",
        "11,56": "terra",
        "11,57": "terra",
        "11,58": "terra",
        "11,59": "pedra_caverna",
        "10,59": "pedra_caverna",
        "9,59": "pedra_caverna",
        "9,58": "terra",
        "9,57": "terra",
        "9,56": "terra",
        "9,55": "entulho",
        "9,54": "entulho",
        "9,53": "terra",
        "9,52": "terra",
        "9,51": "terra",
        "9,50": "terra",
        "9,49": "terra",
        "9,48": "terra",
        "9,47": "terra",
        "9,46": "terra",
        "7,46": "terra",
        "7,47": "terra",
        "7,48": "terra",
        "7,49": "terra",
        "7,50": "terra",
        "7,51": "terra",
        "7,52": "terra",
        "7,53": "terra",
        "7,54": "terra",
        "7,55": "terra",
        "7,56": "terra",
        "7,57": "terra",
        "7,58": "terra",
        "7,59": "pedra_caverna",
        "6,59": "pedra_caverna",
        "5,59": "pedra_caverna",
        "5,58": "terra",
        "5,57": "terra",
        "5,56": "terra",
        "5,55": "terra",
        "5,54": "terra",
        "5,53": "terra",
        "5,52": "pedra_caverna",
        "5,51": "terra",
        "5,50": "terra",
        "5,49": "terra",
        "5,48": "pedra_caverna",
        "5,47": "pedra_caverna",
        "5,46": "pedra_caverna",
        "3,46": "pedra_caverna",
        "3,47": "pedra_caverna",
        "3,48": "pedra_caverna",
        "3,49": "pedra_caverna",
        "3,50": "pedra_caverna",
        "3,51": "pedra_caverna",
        "3,52": "pedra_caverna",
        "3,53": "terra",
        "3,54": "terra",
        "3,55": "terra",
        "3,56": "terra",
        "3,57": "terra",
        "3,58": "pedra_caverna",
        "3,59": "pedra_caverna",
        "2,59": "pedra_caverna",
        "1,59": "pedra_caverna",
        "1,58": "pedra_caverna",
        "1,57": "pedra_caverna",
        "1,56": "pedra_caverna",
        "1,55": "pedra_caverna",
        "1,54": "pedra_caverna",
        "1,53": "pedra_caverna",
        "0,53": "pedra_caverna",
        "0,52": "pedra_caverna",
        "0,54": "pedra_caverna",
        "0,55": "pedra_caverna",
        "0,56": "pedra_caverna",
        "0,57": "pedra_caverna",
        "0,58": "pedra_caverna",
        "0,59": "pedra_caverna",
        "2,58": "pedra_caverna",
        "2,57": "terra",
        "2,56": "terra",
        "2,55": "terra",
        "2,54": "pedra_caverna",
        "2,53": "pedra_caverna",
        "2,52": "pedra_caverna",
        "4,46": "pedra_caverna",
        "4,47": "pedra_caverna",
        "4,48": "pedra_caverna",
        "4,49": "pedra_caverna",
        "4,50": "pedra_caverna",
        "4,51": "pedra_caverna",
        "4,52": "pedra_caverna",
        "4,53": "terra",
        "4,54": "terra",
        "4,55": "terra",
        "4,56": "terra",
        "4,57": "terra",
        "4,58": "terra",
        "4,59": "pedra_caverna",
        "6,58": "terra",
        "6,57": "terra",
        "6,56": "terra",
        "6,55": "terra",
        "6,54": "terra",
        "6,53": "terra",
        "6,52": "terra",
        "6,51": "terra",
        "6,50": "terra",
        "6,49": "terra",
        "6,48": "terra",
        "6,47": "pedra_caverna",
        "6,46": "pedra_caverna",
        "8,46": "terra",
        "8,47": "terra",
        "8,48": "terra",
        "8,49": "terra",
        "8,50": "terra",
        "8,51": "terra",
        "8,52": "terra",
        "8,53": "terra",
        "8,54": "terra",
        "8,55": "terra",
        "8,56": "terra",
        "8,57": "terra",
        "8,58": "terra",
        "8,59": "pedra_caverna",
        "10,58": "terra",
        "10,57": "terra",
        "10,56": "terra",
        "10,55": "entulho",
        "10,54": "entulho",
        "10,53": "terra",
        "10,52": "terra",
        "10,51": "terra",
        "10,50": "terra",
        "10,49": "pedra_caverna",
        "10,48": "pedra_caverna",
        "10,47": "pedra_caverna",
        "10,46": "pedra_caverna",
        "12,46": "pedra_caverna",
        "12,47": "pedra_caverna",
        "12,48": "pedra_caverna",
        "12,49": "pedra_caverna",
        "12,50": "pedra_caverna",
        "12,51": "pedra_caverna",
        "12,52": "terra",
        "12,53": "terra",
        "12,54": "terra",
        "12,55": "terra",
        "12,56": "terra",
        "12,57": "terra",
        "12,58": "terra",
        "12,59": "pedra_caverna",
        "14,58": "pedra_caverna",
        "14,57": "pedra_caverna",
        "14,56": "terra",
        "14,55": "terra",
        "14,54": "pedra_caverna",
        "14,53": "pedra_caverna",
        "14,52": "pedra_caverna",
        "14,51": "pedra_caverna",
        "14,50": "pedra_caverna",
        "14,49": "pedra_caverna",
        "14,48": "pedra_caverna",
        "14,47": "pedra_caverna",
        "14,46": "pedra_caverna",
        "0,46": "pedra_caverna",
        "2,46": "pedra_caverna",
        "0,47": "pedra_caverna",
        "2,47": "pedra_caverna",
        "0,48": "pedra_caverna",
        "2,48": "pedra_caverna",
        "0,49": "pedra_caverna",
        "2,49": "pedra_caverna",
        "0,50": "pedra_caverna",
        "2,50": "pedra_caverna",
        "1,52": "pedra_caverna",
        "0,51": "pedra_caverna",
        "2,51": "pedra_caverna"
      },
      "objectives": {
        "primary": {
          "type": "kill_all",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "floresta.json",
    "id": "floresta",
    "name": "floresta",
    "defn": {
      "schema_version": 1,
      "id": "floresta",
      "name": "floresta",
      "ambiente": "ar_livre",
      "grid": {
        "w": 16,
        "h": 12
      },
      "tiles": [
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 2,
          "y": 8,
          "w": 4,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 4,
        "y": 9
      },
      "exit": null,
      "monsters": [
        {
          "type": "goblin",
          "pos": [
            6,
            4
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "soldado",
          "pos": [
            3,
            5
          ],
          "room_id": null,
          "boss": false,
          "target": false
        }
      ],
      "chests": [],
      "traps": [],
      "decorations": [
        {
          "id": "decor_0",
          "type": "arvore",
          "pos": [
            0,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.5,
            1.9
          ]
        },
        {
          "id": "decor_1",
          "type": "arvore",
          "pos": [
            0,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1,
            2
          ]
        },
        {
          "id": "decor_2",
          "type": "arvore",
          "pos": [
            0,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            0.7,
            1.7
          ]
        },
        {
          "id": "decor_3",
          "type": "arvore",
          "pos": [
            8,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_4",
          "type": "arvore",
          "pos": [
            8,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_5",
          "type": "arvore",
          "pos": [
            8,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_6",
          "type": "arvore",
          "pos": [
            8,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_7",
          "type": "arvore",
          "pos": [
            9,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_8",
          "type": "arvore",
          "pos": [
            9,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_9",
          "type": "arvore",
          "pos": [
            9,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_10",
          "type": "arvore",
          "pos": [
            9,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_11",
          "type": "arvore",
          "pos": [
            5,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1,
            1.5
          ]
        },
        {
          "id": "decor_12",
          "type": "arvore",
          "pos": [
            4,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_13",
          "type": "arvore",
          "pos": [
            2,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1,
            1.7
          ]
        },
        {
          "id": "decor_14",
          "type": "arvore",
          "pos": [
            1,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1,
            1.7
          ]
        },
        {
          "id": "decor_15",
          "type": "arvore",
          "pos": [
            3,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.2,
            1.5
          ]
        },
        {
          "id": "decor_16",
          "type": "arvore",
          "pos": [
            6,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "size": [
            2,
            2
          ]
        },
        {
          "id": "decor_17",
          "type": "arvore",
          "pos": [
            6,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_18",
          "type": "arvore",
          "pos": [
            7,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_19",
          "type": "arvore",
          "pos": [
            6,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_20",
          "type": "arvore",
          "pos": [
            7,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_21",
          "type": "arvore",
          "pos": [
            8,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_22",
          "type": "arvore",
          "pos": [
            9,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_23",
          "type": "arvore",
          "pos": [
            10,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_24",
          "type": "arvore",
          "pos": [
            11,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_25",
          "type": "arvore",
          "pos": [
            12,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_26",
          "type": "arvore",
          "pos": [
            13,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_27",
          "type": "arvore",
          "pos": [
            14,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_28",
          "type": "arvore",
          "pos": [
            15,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_29",
          "type": "arvore",
          "pos": [
            15,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_30",
          "type": "arvore",
          "pos": [
            15,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_31",
          "type": "arvore",
          "pos": [
            15,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_32",
          "type": "arvore",
          "pos": [
            15,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_33",
          "type": "arvore",
          "pos": [
            15,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_34",
          "type": "arvore",
          "pos": [
            15,
            5
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_35",
          "type": "arvore",
          "pos": [
            15,
            4
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_36",
          "type": "arvore",
          "pos": [
            15,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_37",
          "type": "arvore",
          "pos": [
            15,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_38",
          "type": "arvore",
          "pos": [
            15,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_39",
          "type": "arvore",
          "pos": [
            15,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_40",
          "type": "arvore",
          "pos": [
            14,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_41",
          "type": "arvore",
          "pos": [
            13,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_42",
          "type": "arvore",
          "pos": [
            11,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_43",
          "type": "arvore",
          "pos": [
            12,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_44",
          "type": "arvore",
          "pos": [
            10,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_45",
          "type": "arvore",
          "pos": [
            9,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_46",
          "type": "arvore",
          "pos": [
            9,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_47",
          "type": "arvore",
          "pos": [
            8,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_48",
          "type": "arvore",
          "pos": [
            7,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_49",
          "type": "arvore",
          "pos": [
            6,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_50",
          "type": "arvore",
          "pos": [
            5,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_51",
          "type": "arvore",
          "pos": [
            4,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_52",
          "type": "arvore",
          "pos": [
            3,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_53",
          "type": "arvore",
          "pos": [
            3,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_54",
          "type": "arvore",
          "pos": [
            2,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_55",
          "type": "arvore",
          "pos": [
            1,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_56",
          "type": "arvore",
          "pos": [
            0,
            0
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_57",
          "type": "arvore",
          "pos": [
            0,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_58",
          "type": "arvore",
          "pos": [
            0,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_59",
          "type": "arvore",
          "pos": [
            0,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_60",
          "type": "arvore",
          "pos": [
            0,
            4
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_61",
          "type": "arvore",
          "pos": [
            0,
            5
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_62",
          "type": "arvore",
          "pos": [
            0,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_63",
          "type": "arvore",
          "pos": [
            0,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_64",
          "type": "arvore",
          "pos": [
            0,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_65",
          "type": "arvore",
          "pos": [
            7,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_66",
          "type": "arvore",
          "pos": [
            7,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_67",
          "type": "arvore",
          "pos": [
            7,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_68",
          "type": "arvore",
          "pos": [
            7,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_69",
          "type": "arvore",
          "pos": [
            8,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_70",
          "type": "arvore",
          "pos": [
            9,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_71",
          "type": "arvore",
          "pos": [
            10,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_72",
          "type": "arvore",
          "pos": [
            10,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_73",
          "type": "arvore",
          "pos": [
            10,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_74",
          "type": "arvore",
          "pos": [
            10,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_75",
          "type": "arvore",
          "pos": [
            10,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "vscale": [
            1.3,
            1.9
          ]
        },
        {
          "id": "decor_76",
          "type": "chao",
          "pos": [
            5,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "chaograma1.png",
          "size": [
            2,
            2
          ]
        },
        {
          "id": "decor_77",
          "type": "chao",
          "pos": [
            12,
            6
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "chãoagua.png",
          "size": [
            2,
            3
          ]
        },
        {
          "id": "decor_78",
          "type": "chao",
          "pos": [
            1,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "chaograma1.png",
          "size": [
            2,
            2
          ]
        }
      ],
      "secret_passages": [],
      "falas": [],
      "master_reinforcements": [],
      "expected_party": {
        "heroes": 4,
        "level": 1
      },
      "prisoner": null,
      "materiais": {
        "0,9": "grama",
        "0,10": "grama",
        "1,10": "grama",
        "1,11": "grama",
        "0,11": "grama",
        "2,11": "grama",
        "3,11": "grama",
        "4,11": "grama",
        "11,6": "grama",
        "11,5": "grama",
        "11,4": "terra",
        "11,3": "terra",
        "11,2": "grama",
        "11,1": "grama",
        "10,1": "grama",
        "9,1": "grama",
        "9,2": "grama",
        "9,3": "terra",
        "9,4": "terra",
        "9,5": "grama",
        "9,6": "grama",
        "9,7": "grama",
        "9,8": "grama",
        "9,9": "grama",
        "9,10": "grama",
        "8,10": "grama",
        "7,10": "grama",
        "7,9": "grama",
        "7,8": "grama",
        "7,7": "grama",
        "7,6": "grama",
        "7,5": "grama",
        "7,4": "terra",
        "7,3": "terra",
        "7,2": "grama",
        "7,1": "grama",
        "6,1": "grama",
        "5,1": "grama",
        "5,2": "grama",
        "5,3": "terra",
        "5,4": "terra",
        "5,5": "grama",
        "5,6": "grama",
        "5,7": "grama",
        "5,8": "grama",
        "5,9": "grama",
        "4,10": "terra",
        "3,10": "terra",
        "3,9": "terra",
        "3,8": "terra",
        "3,7": "terra",
        "3,6": "terra",
        "3,5": "terra",
        "3,4": "terra",
        "3,3": "terra",
        "3,2": "grama",
        "3,1": "grama",
        "2,1": "grama",
        "2,2": "grama",
        "1,5": "grama",
        "1,6": "grama",
        "1,7": "grama",
        "1,8": "grama",
        "1,9": "grama",
        "2,3": "grama",
        "2,4": "grama",
        "2,5": "grama",
        "2,6": "grama",
        "2,7": "grama",
        "2,8": "grama",
        "2,9": "grama",
        "2,10": "grama",
        "4,9": "terra",
        "4,8": "terra",
        "4,7": "terra",
        "4,6": "terra",
        "4,5": "terra",
        "4,4": "terra",
        "4,3": "terra",
        "4,2": "grama",
        "4,1": "grama",
        "6,2": "grama",
        "6,3": "terra",
        "6,4": "terra",
        "6,5": "grama",
        "6,6": "grama",
        "6,7": "grama",
        "6,8": "grama",
        "6,9": "grama",
        "6,10": "grama",
        "10,10": "grama",
        "11,10": "grama",
        "11,9": "grama",
        "11,8": "grama",
        "12,8": "agua",
        "12,7": "agua",
        "13,7": "agua",
        "13,6": "agua",
        "13,5": "terra",
        "13,4": "terra",
        "13,3": "terra",
        "13,2": "grama",
        "13,1": "grama",
        "14,1": "grama",
        "14,2": "grama",
        "14,3": "terra",
        "14,4": "terra",
        "14,5": "terra",
        "14,6": "terra",
        "14,7": "terra",
        "14,8": "terra",
        "14,9": "terra",
        "14,10": "terra",
        "13,10": "terra",
        "13,9": "terra",
        "13,8": "agua",
        "12,9": "grama",
        "12,10": "grama",
        "8,9": "grama",
        "10,9": "grama",
        "8,8": "grama",
        "10,8": "grama",
        "8,7": "grama",
        "10,7": "grama",
        "8,6": "grama",
        "8,5": "grama",
        "8,4": "terra",
        "8,3": "terra",
        "8,2": "grama",
        "8,1": "grama",
        "12,1": "grama",
        "10,2": "grama",
        "12,2": "grama",
        "10,3": "terra",
        "12,3": "terra",
        "10,4": "terra",
        "12,4": "terra",
        "10,5": "grama",
        "12,5": "grama",
        "11,7": "grama",
        "10,6": "grama",
        "12,6": "agua",
        "5,10": "grama",
        "5,11": "grama",
        "15,3": "grama",
        "15,2": "grama",
        "15,1": "grama",
        "15,0": "grama",
        "14,0": "grama",
        "13,0": "grama",
        "12,0": "grama",
        "11,0": "grama",
        "10,0": "grama",
        "9,0": "grama",
        "8,0": "grama",
        "7,0": "grama",
        "6,0": "grama",
        "5,0": "grama",
        "4,0": "grama",
        "3,0": "grama",
        "2,0": "grama",
        "1,0": "grama",
        "1,1": "grama",
        "1,2": "grama",
        "1,3": "grama",
        "1,4": "grama",
        "0,4": "grama",
        "0,5": "grama",
        "0,6": "grama",
        "0,7": "grama",
        "0,8": "grama",
        "0,3": "grama",
        "0,2": "grama",
        "0,1": "grama",
        "0,0": "grama",
        "15,4": "grama",
        "15,5": "grama",
        "15,6": "grama",
        "15,7": "grama",
        "15,8": "grama",
        "15,9": "grama",
        "15,10": "grama",
        "15,11": "grama",
        "14,11": "grama",
        "13,11": "grama",
        "12,11": "grama",
        "11,11": "grama",
        "10,11": "grama",
        "9,11": "grama",
        "8,11": "grama",
        "7,11": "grama",
        "6,11": "grama"
      },
      "objectives": {
        "primary": {
          "type": "kill_all",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "gustavo.json",
    "id": "gustavo",
    "name": "gustavo",
    "defn": {
      "schema_version": 1,
      "id": "gustavo",
      "name": "gustavo",
      "ambiente": "masmorra",
      "grid": {
        "w": 17,
        "h": 13
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          2,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          2,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 8,
          "w": 3,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 1,
          "x": 8,
          "y": 8,
          "w": 7,
          "h": 3,
          "role": "monster",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 2,
        "y": 9
      },
      "exit": null,
      "monsters": [
        {
          "type": "necromante",
          "pos": [
            9,
            9
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "devorador_organico",
          "pos": [
            12,
            9
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "ogro_clava",
          "pos": [
            14,
            9
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "escorpiao_pequeno",
          "pos": [
            2,
            6
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "escorpiao_pedra",
          "pos": [
            2,
            2
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "kobold_lanceiro",
          "pos": [
            10,
            3
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "kobold_besteiro",
          "pos": [
            11,
            1
          ],
          "room_id": null,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            1,
            6
          ],
          "gold": 50,
          "items": [],
          "key_objective": false
        }
      ],
      "traps": [],
      "decorations": [
        {
          "id": "decor_0",
          "type": "cama",
          "pos": [
            14,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_1",
          "type": "arvore",
          "pos": [
            6,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_2",
          "type": "lareira",
          "pos": [
            1,
            10
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "key_objective": true,
          "vscale": [
            1.5,
            2
          ]
        },
        {
          "id": "decor_3",
          "type": "altar",
          "pos": [
            3,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": [
              {
                "id": "racao_viagem"
              }
            ]
          },
          "key_objective": false,
          "chest_trap_monster_type": "esqueleto_humano"
        }
      ],
      "secret_passages": [
        {
          "id": "passage_0",
          "type": "mechanism",
          "pos": [
            4,
            9
          ],
          "key_decor_ids": [
            "decor_2"
          ],
          "keys_mode": "any"
        },
        {
          "id": "passage_1",
          "type": "mechanism",
          "pos": [
            5,
            9
          ],
          "key_decor_ids": [
            "decor_2"
          ],
          "keys_mode": "any"
        },
        {
          "id": "passage_2",
          "type": "mechanism",
          "pos": [
            6,
            9
          ],
          "key_decor_ids": [
            "decor_2"
          ],
          "keys_mode": "any"
        },
        {
          "id": "passage_3",
          "type": "mechanism",
          "pos": [
            7,
            9
          ],
          "key_decor_ids": [
            "decor_2"
          ],
          "keys_mode": "any"
        }
      ],
      "falas": [],
      "master_reinforcements": [],
      "expected_party": {
        "heroes": 4,
        "level": 1
      },
      "prisoner": null,
      "materiais": {},
      "objectives": {
        "primary": {
          "type": "kill_all",
          "xp": 500,
          "reward": {
            "gold": 200,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "mapaga_grande.json",
    "id": "resgate de elara",
    "name": "Resgate de Elara",
    "defn": {
      "schema_version": 1,
      "id": "resgate de elara",
      "name": "Resgate de Elara",
      "ambiente": "masmorra",
      "grid": {
        "w": 44,
        "h": 40
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 35,
          "w": 5,
          "h": 4,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 1,
          "x": 2,
          "y": 26,
          "w": 2,
          "h": 9,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 2,
          "x": 2,
          "y": 22,
          "w": 7,
          "h": 4,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              9,
              23
            ],
            [
              9,
              24
            ],
            [
              4,
              21
            ],
            [
              5,
              21
            ],
            [
              6,
              21
            ]
          ]
        },
        {
          "id": 3,
          "x": 4,
          "y": 15,
          "w": 3,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              4,
              21
            ],
            [
              5,
              21
            ],
            [
              6,
              21
            ]
          ]
        },
        {
          "id": 4,
          "x": 9,
          "y": 23,
          "w": 9,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              9,
              23
            ],
            [
              9,
              24
            ],
            [
              15,
              25
            ],
            [
              16,
              25
            ],
            [
              17,
              25
            ]
          ]
        },
        {
          "id": 5,
          "x": 1,
          "y": 8,
          "w": 9,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 6,
          "x": 4,
          "y": 5,
          "w": 3,
          "h": 3,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 7,
          "x": 4,
          "y": 1,
          "w": 14,
          "h": 4,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 8,
          "x": 14,
          "y": 7,
          "w": 11,
          "h": 10,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              25,
              11
            ],
            [
              25,
              12
            ],
            [
              25,
              13
            ],
            [
              13,
              10
            ],
            [
              13,
              11
            ],
            [
              16,
              17
            ],
            [
              17,
              17
            ]
          ]
        },
        {
          "id": 9,
          "x": 9,
          "y": 10,
          "w": 5,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              13,
              10
            ],
            [
              13,
              11
            ]
          ]
        },
        {
          "id": 10,
          "x": 31,
          "y": 1,
          "w": 8,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              30,
              2
            ],
            [
              30,
              3
            ],
            [
              32,
              8
            ],
            [
              33,
              8
            ]
          ]
        },
        {
          "id": 11,
          "x": 21,
          "y": 0,
          "w": 9,
          "h": 6,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              20,
              2
            ],
            [
              20,
              3
            ],
            [
              30,
              2
            ],
            [
              30,
              3
            ]
          ]
        },
        {
          "id": 12,
          "x": 18,
          "y": 2,
          "w": 3,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              20,
              2
            ],
            [
              20,
              3
            ]
          ]
        },
        {
          "id": 13,
          "x": 30,
          "y": 2,
          "w": 2,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              30,
              2
            ],
            [
              30,
              3
            ]
          ]
        },
        {
          "id": 14,
          "x": 26,
          "y": 8,
          "w": 11,
          "h": 9,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              32,
              8
            ],
            [
              33,
              8
            ],
            [
              25,
              11
            ],
            [
              25,
              12
            ],
            [
              25,
              13
            ]
          ]
        },
        {
          "id": 15,
          "x": 15,
          "y": 25,
          "w": 3,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              15,
              25
            ],
            [
              16,
              25
            ],
            [
              17,
              25
            ],
            [
              15,
              31
            ],
            [
              16,
              31
            ],
            [
              17,
              31
            ]
          ]
        },
        {
          "id": 16,
          "x": 9,
          "y": 32,
          "w": 12,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              15,
              31
            ],
            [
              16,
              31
            ],
            [
              17,
              31
            ]
          ]
        },
        {
          "id": 17,
          "x": 19,
          "y": 19,
          "w": 13,
          "h": 8,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              27,
              18
            ],
            [
              28,
              18
            ],
            [
              18,
              19
            ],
            [
              18,
              20
            ],
            [
              18,
              21
            ],
            [
              18,
              22
            ]
          ]
        },
        {
          "id": 18,
          "x": 26,
          "y": 29,
          "w": 12,
          "h": 9,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              29,
              28
            ],
            [
              30,
              28
            ]
          ]
        },
        {
          "id": 19,
          "x": 13,
          "y": 17,
          "w": 6,
          "h": 6,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              16,
              17
            ],
            [
              17,
              17
            ],
            [
              18,
              19
            ],
            [
              18,
              20
            ],
            [
              18,
              21
            ],
            [
              18,
              22
            ]
          ]
        }
      ],
      "entrance": {
        "x": 2,
        "y": 37
      },
      "exit": {
        "x": 3,
        "y": 37
      },
      "monsters": [
        {
          "type": "dark_mage",
          "pos": [
            29,
            11
          ],
          "room_id": 14,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            29,
            11
          ],
          "room_id": 14,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            32,
            37
          ],
          "gold": 0,
          "items": [
            {
              "id": "health_potion"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            5,
            35
          ],
          "gold": 5000,
          "items": [
            {
              "id": "health_potion"
            },
            {
              "id": "sword"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            5,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            2,
            30
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            2,
            32
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            2,
            32
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            12,
            34
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            12,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            12,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            14,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            14,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            15,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            15,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        }
      ],
      "traps": [
        {
          "tipo": "armadilha_incendiaria",
          "pos": [
            10,
            10
          ]
        },
        {
          "tipo": "armadilha_incendiaria",
          "pos": [
            10,
            11
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            3,
            24
          ],
          "image": "fossocomestacascima.png"
        },
        {
          "tipo": "rede",
          "pos": [
            29,
            12
          ]
        },
        {
          "tipo": "fosso_estacas",
          "pos": [
            18,
            12
          ]
        },
        {
          "tipo": "nuvem_gas",
          "pos": [
            35,
            4
          ]
        },
        {
          "tipo": "mina_terrestre",
          "pos": [
            24,
            3
          ]
        },
        {
          "tipo": "mina_terrestre",
          "pos": [
            9,
            3
          ],
          "image": "armadilhamina.png"
        },
        {
          "tipo": "fosso_estacas",
          "pos": [
            8,
            3
          ],
          "image": "armadilhafococomespeinhos.png"
        },
        {
          "tipo": "buraco",
          "pos": [
            9,
            3
          ]
        },
        {
          "tipo": "armadilha_urso",
          "pos": [
            7,
            24
          ],
          "image": "armadilhaurso.png"
        },
        {
          "tipo": "armadilha_urso",
          "pos": [
            3,
            31
          ],
          "image": "armadilhaursoporcima.png"
        },
        {
          "tipo": "buraco",
          "pos": [
            6,
            11
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            3,
            30
          ],
          "image": "fossocomestacascima.png"
        },
        {
          "tipo": "buraco",
          "pos": [
            3,
            30
          ]
        }
      ],
      "decorations": [
        {
          "type": "fogueira",
          "pos": [
            2,
            28
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "fogueiracircular.png",
          "vscale": [
            0.6,
            1.4
          ]
        },
        {
          "type": "tumba",
          "pos": [
            6,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "image": "sarcofagocima.png",
          "vscale": [
            1,
            1.2
          ]
        },
        {
          "type": "tumba",
          "pos": [
            1,
            10
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "image": "mesaalquimia.png",
          "size": [
            1,
            1
          ]
        },
        {
          "type": "mesa_cadeiras",
          "pos": [
            5,
            2
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "image": "bancada.png",
          "vscale": [
            0.7,
            0.8
          ]
        },
        {
          "type": "trono",
          "pos": [
            11,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "trono.png",
          "vscale": [
            1,
            1.8
          ]
        },
        {
          "type": "cama_casal",
          "pos": [
            26,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "camacasal.png",
          "vscale": [
            0.8,
            0.8
          ]
        },
        {
          "type": "arvore_grande",
          "pos": [
            17,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "arvore.png",
          "size": [
            2,
            3
          ],
          "vscale": [
            1,
            1.4
          ]
        },
        {
          "type": "estante_armas",
          "pos": [
            14,
            14
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "barril",
          "pos": [
            24,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "barril.png"
        },
        {
          "type": "barril",
          "pos": [
            23,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "barril.png"
        },
        {
          "type": "barril",
          "pos": [
            24,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "barril.png"
        },
        {
          "type": "coluna",
          "pos": [
            34,
            12
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "coluna",
          "pos": [
            31,
            12
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "coluna.png",
          "vscale": [
            1,
            1.6
          ]
        },
        {
          "type": "coluna",
          "pos": [
            31,
            14
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "coluna",
          "pos": [
            34,
            14
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "arca_tesouros",
          "pos": [
            24,
            16
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "image": "bau.png"
        },
        {
          "type": "arca_tesouros",
          "pos": [
            23,
            16
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "image": "bau.png"
        },
        {
          "type": "altar",
          "pos": [
            36,
            5
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "altar.png"
        },
        {
          "type": "gaiola",
          "pos": [
            27,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "jaulaalta.png",
          "vscale": [
            1,
            1.4
          ]
        },
        {
          "type": "grades_prisao",
          "pos": [
            34,
            9
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "image": "grade.png",
          "vscale": [
            1.6,
            1.3
          ]
        },
        {
          "type": "grades_prisao",
          "pos": [
            34,
            10
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "image": "grade.png",
          "vscale": [
            1.5,
            1.3
          ]
        },
        {
          "type": "grades_prisao",
          "pos": [
            35,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "grade.png",
          "vscale": [
            1.6,
            1.3
          ]
        },
        {
          "type": "grades_prisao",
          "pos": [
            36,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "grade.png",
          "vscale": [
            1.6,
            1.3
          ]
        },
        {
          "type": "arvore",
          "pos": [
            2,
            13
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "arvore_cutout.png",
          "vscale": [
            1.5,
            2
          ]
        },
        {
          "type": "arvore",
          "pos": [
            5,
            19
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "arvore_cutout.png",
          "vscale": [
            0.6,
            1.5
          ]
        },
        {
          "type": "fonte",
          "pos": [
            15,
            20
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "charges": 3,
          "image": "fontecircular.png",
          "vscale": [
            0.7,
            1
          ]
        },
        {
          "type": "fonte",
          "pos": [
            19,
            23
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "charges": 3,
          "image": "fontedecanto.png",
          "size": [
            1,
            1
          ],
          "vscale": [
            1,
            1.2
          ]
        },
        {
          "type": "chao",
          "pos": [
            2,
            22
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaograma1.png",
          "size": [
            7,
            4
          ]
        },
        {
          "type": "cortina_vermelha",
          "pos": [
            6,
            36
          ],
          "facing": [
            -1,
            0
          ],
          "loot": null,
          "image": "cortina_vermelha.png"
        },
        {
          "type": "cortina_vermelha",
          "pos": [
            6,
            37
          ],
          "facing": [
            -1,
            0
          ],
          "loot": null,
          "image": "cortina_vermelha.png"
        },
        {
          "type": "cortina_vermelha",
          "pos": [
            0,
            35
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "image": "cortina_vermelha.png",
          "vscale": [
            2,
            1
          ]
        },
        {
          "type": "brasao_leao",
          "pos": [
            4,
            34
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "brasao_leao.png"
        },
        {
          "type": "arca_tesouros",
          "pos": [
            5,
            38
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          }
        }
      ],
      "prisoner": {
        "pos": [
          27,
          37
        ],
        "room_id": 18,
        "image": "elara.png"
      },
      "materiais": {
        "2,22": "grama",
        "2,23": "grama",
        "2,24": "grama",
        "2,25": "grama",
        "3,25": "grama",
        "4,25": "grama",
        "5,25": "grama",
        "6,25": "grama",
        "7,25": "grama",
        "8,25": "grama",
        "8,24": "grama",
        "9,24": "grama",
        "9,23": "grama",
        "8,23": "grama",
        "8,22": "grama",
        "7,22": "grama",
        "6,22": "grama",
        "5,22": "grama",
        "4,22": "grama",
        "3,22": "grama",
        "3,23": "grama",
        "3,24": "grama",
        "4,24": "grama",
        "5,24": "grama",
        "6,24": "grama",
        "7,24": "grama",
        "7,23": "grama",
        "6,23": "grama",
        "5,23": "grama",
        "4,23": "grama",
        "4,20": "pedra_negra",
        "5,20": "pedra_negra",
        "6,20": "pedra_negra",
        "6,19": "pedra_negra",
        "5,19": "pedra_negra",
        "4,19": "pedra_negra",
        "4,18": "desmoronada",
        "4,17": "desmoronada",
        "4,16": "pedra_negra",
        "4,15": "pedra_negra",
        "5,15": "pedra_negra",
        "6,15": "pedra_negra",
        "6,16": "pedra_negra",
        "6,17": "pedra_negra",
        "6,18": "pedra_negra",
        "5,18": "pedra_negra",
        "5,17": "pedra_negra",
        "5,16": "pedra_negra",
        "2,26": "terra",
        "3,26": "terra",
        "3,27": "terra",
        "2,27": "terra",
        "2,28": "terra",
        "2,29": "terra",
        "2,30": "terra",
        "3,29": "terra",
        "3,28": "terra",
        "3,30": "terra",
        "3,31": "terra",
        "2,31": "terra",
        "2,32": "terra",
        "2,33": "terra",
        "2,34": "terra",
        "3,34": "terra",
        "3,33": "terra",
        "3,32": "terra",
        "19,25": "desmoronada",
        "18,25": "desmoronada",
        "18,24": "desmoronada",
        "18,23": "desmoronada",
        "18,26": "desmoronada",
        "18,27": "desmoronada",
        "18,28": "desmoronada",
        "18,29": "desmoronada",
        "18,30": "desmoronada",
        "18,31": "desmoronada",
        "19,31": "desmoronada",
        "20,31": "desmoronada",
        "20,30": "desmoronada",
        "20,29": "desmoronada",
        "20,28": "desmoronada",
        "20,27": "desmoronada",
        "21,27": "desmoronada",
        "22,27": "desmoronada",
        "22,28": "desmoronada",
        "22,29": "desmoronada",
        "22,30": "desmoronada",
        "22,31": "desmoronada",
        "22,32": "desmoronada",
        "22,33": "desmoronada",
        "22,34": "desmoronada",
        "22,35": "desmoronada",
        "22,36": "desmoronada",
        "22,37": "desmoronada",
        "22,38": "desmoronada",
        "22,39": "desmoronada",
        "21,39": "desmoronada",
        "20,39": "desmoronada",
        "19,39": "desmoronada",
        "18,39": "desmoronada",
        "17,39": "desmoronada",
        "16,39": "desmoronada",
        "15,39": "desmoronada",
        "14,39": "desmoronada",
        "13,39": "desmoronada",
        "12,39": "desmoronada",
        "11,39": "desmoronada",
        "10,39": "desmoronada",
        "9,39": "desmoronada",
        "8,39": "desmoronada",
        "8,38": "desmoronada",
        "8,37": "desmoronada",
        "8,36": "desmoronada",
        "8,35": "desmoronada",
        "8,34": "desmoronada",
        "8,33": "desmoronada",
        "8,32": "desmoronada",
        "8,31": "desmoronada",
        "8,30": "desmoronada",
        "8,29": "desmoronada",
        "8,28": "desmoronada",
        "8,27": "desmoronada",
        "8,26": "desmoronada",
        "7,26": "desmoronada",
        "6,26": "pedra_caverna",
        "6,27": "pedra_caverna",
        "6,28": "pedra_caverna",
        "6,29": "pedra_caverna",
        "6,30": "pedra_caverna",
        "6,31": "pedra_caverna",
        "6,32": "pedra_caverna",
        "6,33": "pedra_caverna",
        "6,34": "pedra_caverna",
        "6,35": "pedra_caverna",
        "6,36": "pedra_caverna",
        "6,37": "pedra_caverna",
        "6,38": "pedra_caverna",
        "6,39": "pedra_caverna",
        "5,39": "pedra_caverna",
        "4,39": "pedra_caverna",
        "3,39": "pedra_caverna",
        "2,39": "pedra_caverna",
        "1,39": "pedra_caverna",
        "0,39": "pedra_caverna",
        "0,38": "pedra_caverna",
        "0,37": "pedra_caverna",
        "0,36": "pedra_caverna",
        "0,35": "pedra_caverna",
        "0,34": "pedra_caverna",
        "0,33": "pedra_caverna",
        "0,32": "pedra_caverna",
        "0,31": "pedra_caverna",
        "0,30": "pedra_caverna",
        "0,29": "pedra_caverna",
        "0,28": "pedra_caverna",
        "0,27": "pedra_caverna",
        "0,26": "pedra_caverna",
        "0,25": "desmoronada",
        "0,24": "desmoronada",
        "0,23": "desmoronada",
        "0,22": "desmoronada",
        "0,21": "desmoronada",
        "0,20": "desmoronada",
        "0,19": "desmoronada",
        "0,18": "desmoronada",
        "0,17": "desmoronada",
        "0,16": "desmoronada",
        "0,15": "desmoronada",
        "0,14": "desmoronada",
        "0,13": "desmoronada",
        "0,12": "desmoronada",
        "0,11": "desmoronada",
        "0,10": "desmoronada",
        "0,9": "desmoronada",
        "0,8": "desmoronada",
        "4,0": "enegrecida",
        "5,0": "enegrecida",
        "6,0": "enegrecida",
        "7,0": "enegrecida",
        "8,0": "enegrecida",
        "9,0": "enegrecida",
        "10,0": "enegrecida",
        "11,0": "enegrecida",
        "12,0": "enegrecida",
        "13,0": "enegrecida",
        "14,0": "enegrecida",
        "15,0": "enegrecida",
        "16,0": "enegrecida",
        "17,0": "enegrecida",
        "18,0": "enegrecida",
        "18,1": "enegrecida",
        "19,1": "enegrecida",
        "20,1": "enegrecida",
        "20,0": "enegrecida",
        "19,0": "enegrecida",
        "1,15": "desmoronada",
        "2,15": "desmoronada",
        "2,16": "desmoronada",
        "2,17": "desmoronada",
        "2,18": "desmoronada",
        "2,19": "desmoronada",
        "2,20": "desmoronada",
        "2,21": "desmoronada",
        "3,21": "desmoronada",
        "3,20": "desmoronada",
        "3,19": "desmoronada",
        "3,18": "desmoronada",
        "3,17": "desmoronada",
        "3,16": "desmoronada",
        "3,15": "desmoronada",
        "1,16": "desmoronada",
        "1,17": "desmoronada",
        "1,18": "desmoronada",
        "1,19": "desmoronada",
        "1,20": "desmoronada",
        "1,21": "desmoronada",
        "1,22": "desmoronada",
        "1,23": "desmoronada",
        "1,24": "desmoronada",
        "1,25": "desmoronada",
        "1,26": "pedra_caverna",
        "1,27": "pedra_caverna",
        "1,28": "pedra_caverna",
        "1,29": "pedra_caverna",
        "1,30": "pedra_caverna",
        "1,31": "pedra_caverna",
        "1,32": "pedra_caverna",
        "1,33": "pedra_caverna",
        "1,34": "pedra_caverna",
        "5,34": "pedra_caverna",
        "4,34": "pedra_caverna",
        "4,33": "pedra_caverna",
        "4,32": "pedra_caverna",
        "4,31": "pedra_caverna",
        "4,30": "pedra_caverna",
        "4,29": "pedra_caverna",
        "4,28": "pedra_caverna",
        "4,27": "pedra_caverna",
        "4,26": "pedra_caverna",
        "5,33": "pedra_caverna",
        "5,32": "pedra_caverna",
        "5,31": "pedra_caverna",
        "5,30": "pedra_caverna",
        "5,29": "pedra_caverna",
        "5,28": "pedra_caverna",
        "5,27": "pedra_caverna",
        "5,26": "pedra_caverna",
        "9,26": "desmoronada",
        "9,25": "desmoronada",
        "10,25": "desmoronada",
        "11,25": "desmoronada",
        "11,26": "desmoronada",
        "11,27": "desmoronada",
        "11,28": "desmoronada",
        "11,29": "desmoronada",
        "11,30": "desmoronada",
        "11,31": "desmoronada",
        "10,31": "desmoronada",
        "12,31": "desmoronada",
        "13,31": "desmoronada",
        "13,30": "desmoronada",
        "13,29": "desmoronada",
        "13,28": "desmoronada",
        "13,27": "desmoronada",
        "13,26": "desmoronada",
        "13,25": "desmoronada",
        "14,25": "desmoronada",
        "14,26": "desmoronada",
        "14,27": "desmoronada",
        "14,28": "desmoronada",
        "14,29": "desmoronada",
        "14,30": "desmoronada",
        "14,31": "desmoronada",
        "10,30": "desmoronada",
        "12,30": "desmoronada",
        "10,29": "desmoronada",
        "12,29": "desmoronada",
        "10,28": "desmoronada",
        "12,28": "desmoronada",
        "10,27": "desmoronada",
        "12,27": "desmoronada",
        "12,26": "desmoronada",
        "12,25": "desmoronada",
        "10,26": "desmoronada",
        "7,27": "desmoronada",
        "9,27": "desmoronada",
        "7,28": "desmoronada",
        "9,28": "desmoronada",
        "7,29": "desmoronada",
        "9,29": "desmoronada",
        "7,30": "desmoronada",
        "9,30": "desmoronada",
        "7,31": "desmoronada",
        "9,31": "desmoronada",
        "7,32": "desmoronada",
        "7,33": "desmoronada",
        "7,34": "desmoronada",
        "7,35": "desmoronada",
        "7,36": "desmoronada",
        "7,37": "desmoronada",
        "7,38": "desmoronada",
        "7,39": "desmoronada",
        "23,39": "desmoronada",
        "24,39": "desmoronada",
        "24,38": "desmoronada",
        "24,37": "desmoronada",
        "24,36": "desmoronada",
        "24,35": "desmoronada",
        "24,34": "desmoronada",
        "24,33": "desmoronada",
        "24,32": "desmoronada",
        "24,31": "desmoronada",
        "24,30": "desmoronada",
        "24,29": "desmoronada",
        "24,28": "desmoronada",
        "24,27": "desmoronada",
        "25,27": "desmoronada",
        "26,27": "desmoronada",
        "26,28": "desmoronada",
        "27,28": "desmoronada",
        "28,28": "desmoronada",
        "28,27": "desmoronada",
        "27,27": "desmoronada",
        "25,28": "desmoronada",
        "25,29": "desmoronada",
        "25,30": "desmoronada",
        "25,31": "desmoronada",
        "25,32": "desmoronada",
        "25,33": "desmoronada",
        "25,34": "desmoronada",
        "25,35": "desmoronada",
        "25,36": "desmoronada",
        "25,37": "desmoronada",
        "25,38": "desmoronada",
        "26,38": "desmoronada",
        "26,39": "desmoronada",
        "27,39": "desmoronada",
        "28,39": "desmoronada",
        "28,38": "desmoronada",
        "29,38": "desmoronada",
        "30,38": "desmoronada",
        "30,39": "desmoronada",
        "31,39": "desmoronada",
        "32,39": "desmoronada",
        "32,38": "desmoronada",
        "33,38": "desmoronada",
        "34,38": "desmoronada",
        "34,39": "desmoronada",
        "35,39": "desmoronada",
        "36,39": "desmoronada",
        "36,38": "desmoronada",
        "37,38": "desmoronada",
        "38,38": "desmoronada",
        "38,37": "desmoronada",
        "38,36": "desmoronada",
        "38,35": "desmoronada",
        "38,34": "desmoronada",
        "38,33": "desmoronada",
        "38,32": "desmoronada",
        "38,31": "desmoronada",
        "38,30": "desmoronada",
        "38,29": "desmoronada",
        "38,28": "desmoronada",
        "38,27": "desmoronada",
        "38,26": "desmoronada",
        "38,25": "desmoronada",
        "38,24": "desmoronada",
        "38,23": "desmoronada",
        "38,22": "desmoronada",
        "38,21": "desmoronada",
        "38,20": "desmoronada",
        "38,19": "desmoronada",
        "38,18": "desmoronada",
        "38,17": "desmoronada",
        "38,16": "desmoronada",
        "38,15": "desmoronada",
        "38,14": "desmoronada",
        "38,13": "desmoronada",
        "38,12": "desmoronada",
        "38,11": "desmoronada",
        "38,10": "desmoronada",
        "38,9": "desmoronada",
        "38,8": "desmoronada",
        "37,8": "desmoronada",
        "36,8": "desmoronada",
        "35,8": "desmoronada",
        "34,8": "desmoronada",
        "39,8": "desmoronada",
        "39,7": "desmoronada",
        "39,6": "desmoronada",
        "39,5": "desmoronada",
        "39,4": "desmoronada",
        "39,3": "desmoronada",
        "39,2": "desmoronada",
        "39,1": "desmoronada",
        "39,0": "desmoronada",
        "38,0": "desmoronada",
        "37,0": "desmoronada",
        "36,0": "desmoronada",
        "35,0": "desmoronada",
        "34,0": "desmoronada",
        "33,0": "desmoronada",
        "32,0": "desmoronada",
        "31,0": "desmoronada",
        "30,0": "enegrecida",
        "30,1": "enegrecida",
        "40,0": "desmoronada",
        "41,0": "desmoronada",
        "41,1": "desmoronada",
        "41,2": "desmoronada",
        "41,3": "desmoronada",
        "41,4": "desmoronada",
        "41,5": "desmoronada",
        "41,6": "desmoronada",
        "41,7": "desmoronada",
        "41,8": "desmoronada",
        "41,9": "desmoronada",
        "41,10": "desmoronada",
        "41,11": "desmoronada",
        "41,12": "desmoronada",
        "41,13": "desmoronada",
        "41,14": "desmoronada",
        "41,15": "desmoronada",
        "41,16": "desmoronada",
        "41,17": "desmoronada",
        "41,18": "desmoronada",
        "41,19": "desmoronada",
        "41,20": "desmoronada",
        "41,21": "desmoronada",
        "41,22": "desmoronada",
        "41,23": "desmoronada",
        "41,24": "desmoronada",
        "41,25": "desmoronada",
        "41,26": "desmoronada",
        "41,27": "desmoronada",
        "41,28": "desmoronada",
        "41,29": "desmoronada",
        "41,30": "desmoronada",
        "41,31": "desmoronada",
        "41,32": "desmoronada",
        "41,33": "desmoronada",
        "41,34": "desmoronada",
        "41,35": "desmoronada",
        "41,36": "desmoronada",
        "41,37": "desmoronada",
        "41,38": "desmoronada",
        "41,39": "desmoronada",
        "40,39": "desmoronada",
        "39,39": "desmoronada",
        "42,39": "desmoronada",
        "43,39": "desmoronada",
        "43,38": "desmoronada",
        "43,37": "desmoronada",
        "43,36": "desmoronada",
        "43,35": "desmoronada",
        "43,34": "desmoronada",
        "43,33": "desmoronada",
        "43,32": "desmoronada",
        "43,31": "desmoronada",
        "43,30": "desmoronada",
        "43,29": "desmoronada",
        "43,28": "desmoronada",
        "43,27": "desmoronada",
        "43,26": "desmoronada",
        "43,25": "desmoronada",
        "43,24": "desmoronada",
        "43,23": "desmoronada",
        "43,22": "desmoronada",
        "43,21": "desmoronada",
        "43,20": "desmoronada",
        "43,19": "desmoronada",
        "43,18": "desmoronada",
        "43,17": "desmoronada",
        "43,16": "desmoronada",
        "43,15": "desmoronada",
        "43,14": "desmoronada",
        "43,13": "desmoronada",
        "43,12": "desmoronada",
        "43,11": "desmoronada",
        "43,10": "desmoronada",
        "43,9": "desmoronada",
        "43,8": "desmoronada",
        "43,7": "desmoronada",
        "43,6": "desmoronada",
        "43,5": "desmoronada",
        "43,4": "desmoronada",
        "43,3": "desmoronada",
        "43,2": "desmoronada",
        "43,1": "desmoronada",
        "43,0": "desmoronada",
        "40,38": "desmoronada",
        "42,38": "desmoronada",
        "40,37": "desmoronada",
        "42,37": "desmoronada",
        "40,36": "desmoronada",
        "42,36": "desmoronada",
        "40,35": "desmoronada",
        "42,35": "desmoronada",
        "40,34": "desmoronada",
        "42,34": "desmoronada",
        "40,33": "desmoronada",
        "42,33": "desmoronada",
        "40,32": "desmoronada",
        "42,32": "desmoronada",
        "40,31": "desmoronada",
        "42,31": "desmoronada",
        "40,30": "desmoronada",
        "42,30": "desmoronada",
        "40,29": "desmoronada",
        "42,29": "desmoronada",
        "40,28": "desmoronada",
        "42,28": "desmoronada",
        "40,27": "desmoronada",
        "42,27": "desmoronada",
        "40,26": "desmoronada",
        "42,26": "desmoronada",
        "40,25": "desmoronada",
        "42,25": "desmoronada",
        "40,24": "desmoronada",
        "42,24": "desmoronada",
        "40,23": "desmoronada",
        "42,23": "desmoronada",
        "40,22": "desmoronada",
        "42,22": "desmoronada",
        "40,21": "desmoronada",
        "42,21": "desmoronada",
        "40,20": "desmoronada",
        "42,20": "desmoronada",
        "40,19": "desmoronada",
        "42,19": "desmoronada",
        "40,18": "desmoronada",
        "42,18": "desmoronada",
        "40,17": "desmoronada",
        "42,17": "desmoronada",
        "40,16": "desmoronada",
        "42,16": "desmoronada",
        "40,15": "desmoronada",
        "42,15": "desmoronada",
        "40,14": "desmoronada",
        "42,14": "desmoronada",
        "40,13": "desmoronada",
        "42,13": "desmoronada",
        "40,12": "desmoronada",
        "42,12": "desmoronada",
        "40,11": "desmoronada",
        "42,11": "desmoronada",
        "40,10": "desmoronada",
        "42,10": "desmoronada",
        "40,9": "desmoronada",
        "42,9": "desmoronada",
        "42,8": "desmoronada",
        "42,7": "desmoronada",
        "42,6": "desmoronada",
        "42,5": "desmoronada",
        "42,4": "desmoronada",
        "42,3": "desmoronada",
        "42,2": "desmoronada",
        "42,1": "desmoronada",
        "42,0": "desmoronada",
        "40,1": "desmoronada",
        "40,2": "desmoronada",
        "40,3": "desmoronada",
        "40,4": "desmoronada",
        "40,5": "desmoronada",
        "40,6": "desmoronada",
        "40,7": "desmoronada",
        "40,8": "desmoronada",
        "37,9": "desmoronada",
        "39,9": "desmoronada",
        "37,10": "desmoronada",
        "39,10": "desmoronada",
        "37,11": "desmoronada",
        "39,11": "desmoronada",
        "37,12": "desmoronada",
        "39,12": "desmoronada",
        "37,13": "desmoronada",
        "39,13": "desmoronada",
        "37,14": "desmoronada",
        "39,14": "desmoronada",
        "37,15": "desmoronada",
        "39,15": "desmoronada",
        "37,16": "desmoronada",
        "39,16": "desmoronada",
        "37,17": "desmoronada",
        "36,17": "desmoronada",
        "36,18": "desmoronada",
        "36,19": "desmoronada",
        "36,20": "desmoronada",
        "36,21": "desmoronada",
        "36,22": "desmoronada",
        "36,23": "desmoronada",
        "36,24": "desmoronada",
        "36,25": "desmoronada",
        "36,26": "desmoronada",
        "36,27": "desmoronada",
        "36,28": "desmoronada",
        "35,28": "desmoronada",
        "34,28": "desmoronada",
        "34,27": "desmoronada",
        "34,26": "desmoronada",
        "34,25": "desmoronada",
        "34,24": "desmoronada",
        "34,23": "desmoronada",
        "34,22": "desmoronada",
        "34,21": "desmoronada",
        "34,20": "desmoronada",
        "34,19": "desmoronada",
        "34,18": "desmoronada",
        "34,17": "desmoronada",
        "33,17": "desmoronada",
        "32,17": "desmoronada",
        "32,18": "desmoronada",
        "32,19": "desmoronada",
        "32,20": "desmoronada",
        "32,21": "desmoronada",
        "32,22": "desmoronada",
        "32,23": "desmoronada",
        "32,24": "desmoronada",
        "32,25": "desmoronada",
        "32,26": "desmoronada",
        "32,27": "desmoronada",
        "32,28": "desmoronada",
        "31,28": "desmoronada",
        "31,27": "desmoronada",
        "31,18": "desmoronada",
        "30,18": "desmoronada",
        "30,17": "desmoronada",
        "29,17": "desmoronada",
        "29,18": "desmoronada",
        "31,17": "desmoronada",
        "33,18": "desmoronada",
        "33,19": "desmoronada",
        "33,20": "desmoronada",
        "33,21": "desmoronada",
        "33,22": "desmoronada",
        "33,23": "desmoronada",
        "33,24": "desmoronada",
        "33,25": "desmoronada",
        "33,26": "desmoronada",
        "33,27": "desmoronada",
        "33,28": "desmoronada",
        "35,27": "desmoronada",
        "35,26": "desmoronada",
        "35,25": "desmoronada",
        "35,24": "desmoronada",
        "35,23": "desmoronada",
        "35,22": "desmoronada",
        "35,21": "desmoronada",
        "35,20": "desmoronada",
        "35,19": "desmoronada",
        "35,18": "desmoronada",
        "35,17": "desmoronada",
        "39,17": "desmoronada",
        "37,18": "desmoronada",
        "39,18": "desmoronada",
        "37,19": "desmoronada",
        "39,19": "desmoronada",
        "37,20": "desmoronada",
        "39,20": "desmoronada",
        "37,21": "desmoronada",
        "39,21": "desmoronada",
        "37,22": "desmoronada",
        "39,22": "desmoronada",
        "37,23": "desmoronada",
        "39,23": "desmoronada",
        "37,24": "desmoronada",
        "39,24": "desmoronada",
        "37,25": "desmoronada",
        "39,25": "desmoronada",
        "37,26": "desmoronada",
        "39,26": "desmoronada",
        "37,27": "desmoronada",
        "39,27": "desmoronada",
        "37,28": "desmoronada",
        "39,28": "desmoronada",
        "39,29": "desmoronada",
        "39,30": "desmoronada",
        "39,31": "desmoronada",
        "39,32": "desmoronada",
        "39,33": "desmoronada",
        "39,34": "desmoronada",
        "39,35": "desmoronada",
        "39,36": "desmoronada",
        "39,37": "desmoronada",
        "38,39": "desmoronada",
        "39,38": "desmoronada",
        "37,39": "desmoronada",
        "35,38": "desmoronada",
        "33,39": "desmoronada",
        "31,38": "desmoronada",
        "29,39": "desmoronada",
        "27,38": "desmoronada",
        "25,39": "desmoronada",
        "21,38": "desmoronada",
        "23,38": "desmoronada",
        "21,37": "desmoronada",
        "23,37": "desmoronada",
        "21,36": "desmoronada",
        "23,36": "desmoronada",
        "21,35": "desmoronada",
        "23,35": "desmoronada",
        "21,34": "desmoronada",
        "23,34": "desmoronada",
        "21,33": "desmoronada",
        "23,33": "desmoronada",
        "21,32": "desmoronada",
        "23,32": "desmoronada",
        "23,31": "desmoronada",
        "23,30": "desmoronada",
        "23,29": "desmoronada",
        "23,28": "desmoronada",
        "23,27": "desmoronada",
        "21,28": "desmoronada",
        "21,29": "desmoronada",
        "21,30": "desmoronada",
        "21,31": "desmoronada",
        "19,30": "desmoronada",
        "19,29": "desmoronada",
        "19,28": "desmoronada",
        "19,27": "desmoronada",
        "10,16": "pedra_caverna",
        "10,15": "pedra_caverna",
        "10,14": "pedra_caverna",
        "10,13": "pedra_caverna",
        "10,12": "pedra_caverna",
        "11,12": "pedra_caverna",
        "12,12": "pedra_caverna",
        "12,13": "pedra_caverna",
        "12,14": "pedra_caverna",
        "12,15": "pedra_caverna",
        "12,16": "pedra_caverna",
        "12,17": "pedra_caverna",
        "12,18": "pedra_caverna",
        "12,19": "pedra_caverna",
        "12,20": "pedra_caverna",
        "12,21": "pedra_caverna",
        "12,22": "pedra_caverna",
        "11,22": "pedra_caverna",
        "10,22": "pedra_caverna",
        "10,21": "pedra_caverna",
        "10,20": "pedra_caverna",
        "10,19": "pedra_caverna",
        "10,18": "pedra_caverna",
        "9,18": "pedra_caverna",
        "9,17": "pedra_caverna",
        "8,17": "desmoronada",
        "8,16": "desmoronada",
        "8,15": "desmoronada",
        "7,15": "desmoronada",
        "7,16": "desmoronada",
        "7,17": "desmoronada",
        "7,18": "desmoronada",
        "7,19": "desmoronada",
        "7,20": "desmoronada",
        "7,21": "desmoronada",
        "8,21": "desmoronada",
        "8,20": "desmoronada",
        "8,19": "desmoronada",
        "8,18": "desmoronada",
        "9,19": "pedra_caverna",
        "9,20": "pedra_caverna",
        "9,21": "pedra_caverna",
        "9,22": "pedra_caverna",
        "11,21": "pedra_caverna",
        "11,20": "pedra_caverna",
        "11,19": "pedra_caverna",
        "11,18": "pedra_caverna",
        "11,17": "pedra_caverna",
        "13,17": "pedra_caverna",
        "14,17": "pedra_caverna",
        "15,17": "pedra_caverna",
        "13,16": "enegrecida",
        "13,15": "enegrecida",
        "13,14": "enegrecida",
        "13,13": "enegrecida",
        "13,12": "enegrecida",
        "11,13": "pedra_caverna",
        "11,14": "pedra_caverna",
        "9,15": "pedra_caverna",
        "11,15": "pedra_caverna",
        "10,17": "pedra_caverna",
        "9,16": "pedra_caverna",
        "11,16": "pedra_caverna",
        "12,6": "enegrecida",
        "12,5": "enegrecida",
        "11,5": "enegrecida",
        "10,5": "enegrecida",
        "10,6": "enegrecida",
        "10,7": "enegrecida",
        "10,8": "enegrecida",
        "10,9": "enegrecida",
        "11,9": "enegrecida",
        "12,9": "enegrecida",
        "12,8": "enegrecida",
        "13,8": "enegrecida",
        "13,7": "enegrecida",
        "13,9": "enegrecida",
        "11,8": "enegrecida",
        "9,7": "enegrecida",
        "8,7": "enegrecida",
        "8,6": "enegrecida",
        "8,5": "enegrecida",
        "7,5": "enegrecida",
        "7,6": "enegrecida",
        "7,7": "enegrecida",
        "11,7": "enegrecida",
        "9,6": "enegrecida",
        "9,5": "enegrecida",
        "13,5": "enegrecida",
        "14,5": "enegrecida",
        "14,6": "enegrecida",
        "15,6": "enegrecida",
        "16,6": "enegrecida",
        "16,5": "enegrecida",
        "17,5": "enegrecida",
        "18,5": "enegrecida",
        "18,4": "enegrecida",
        "19,4": "enegrecida",
        "20,4": "enegrecida",
        "20,5": "enegrecida",
        "20,6": "enegrecida",
        "19,6": "enegrecida",
        "21,6": "enegrecida",
        "22,6": "enegrecida",
        "23,6": "enegrecida",
        "24,6": "enegrecida",
        "25,6": "enegrecida",
        "25,7": "enegrecida",
        "25,8": "enegrecida",
        "25,9": "enegrecida",
        "25,10": "enegrecida",
        "26,8": "pedra_caverna",
        "27,8": "pedra_caverna",
        "27,7": "enegrecida",
        "27,6": "enegrecida",
        "28,6": "enegrecida",
        "29,6": "enegrecida",
        "29,7": "enegrecida",
        "29,8": "pedra_caverna",
        "30,8": "pedra_caverna",
        "31,8": "pedra_caverna",
        "30,7": "enegrecida",
        "30,6": "enegrecida",
        "30,5": "enegrecida",
        "30,4": "enegrecida",
        "28,7": "enegrecida",
        "28,8": "pedra_caverna",
        "26,7": "enegrecida",
        "26,6": "enegrecida",
        "18,6": "enegrecida",
        "19,5": "enegrecida",
        "17,6": "enegrecida",
        "15,5": "enegrecida",
        "12,7": "enegrecida",
        "11,6": "enegrecida",
        "13,6": "enegrecida",
        "25,18": "enegrecida",
        "25,17": "enegrecida",
        "25,16": "enegrecida",
        "25,15": "enegrecida",
        "25,14": "enegrecida",
        "24,17": "enegrecida",
        "23,17": "enegrecida",
        "23,18": "enegrecida",
        "22,18": "enegrecida",
        "21,18": "enegrecida",
        "21,17": "enegrecida",
        "20,17": "enegrecida",
        "19,17": "enegrecida",
        "19,18": "enegrecida",
        "18,17": "pedra_caverna",
        "20,18": "enegrecida",
        "22,17": "enegrecida",
        "26,17": "pedra_caverna",
        "24,18": "enegrecida",
        "26,18": "pedra_caverna",
        "20,22": "desmoronada",
        "21,22": "desmoronada",
        "2,8": "pedra_negra",
        "1,8": "pedra_negra",
        "1,9": "pedra_negra",
        "2,9": "pedra_negra",
        "3,9": "pedra_negra",
        "4,9": "pedra_negra",
        "6,9": "pedra_negra",
        "7,9": "pedra_negra",
        "8,9": "pedra_negra",
        "9,9": "pedra_negra",
        "9,8": "pedra_negra",
        "8,8": "pedra_negra",
        "7,8": "pedra_negra",
        "6,8": "pedra_negra",
        "4,8": "pedra_negra",
        "3,8": "pedra_negra",
        "5,8": "pedra_negra",
        "5,9": "pedra_negra",
        "5,10": "pedra_negra",
        "4,10": "pedra_negra",
        "3,10": "pedra_negra",
        "2,10": "pedra_negra",
        "7,10": "pedra_negra",
        "8,10": "pedra_negra",
        "9,10": "pedra_negra"
      },
      "objectives": {
        "primary": {
          "type": "rescue_prisoner",
          "xp": 100,
          "reward": {
            "gold": 150,
            "items": []
          }
        },
        "secondary": [
          {
            "type": "rescue_prisoner",
            "xp": 50,
            "reward": {
              "gold": 25,
              "items": []
            }
          },
          {
            "type": "reach_exit",
            "xp": 50,
            "reward": {
              "gold": 25,
              "items": []
            }
          }
        ]
      }
    }
  },
  {
    "file": "passagens_secreta.json",
    "id": "gustavo",
    "name": "gustavo",
    "defn": {
      "schema_version": 1,
      "id": "gustavo",
      "name": "gustavo",
      "grid": {
        "w": 17,
        "h": 13
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 8,
          "w": 3,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 1,
          "x": 8,
          "y": 8,
          "w": 7,
          "h": 3,
          "role": "monster",
          "locked": true,
          "doors": []
        }
      ],
      "entrance": {
        "x": 2,
        "y": 9
      },
      "exit": null,
      "monsters": [
        {
          "type": "necromante",
          "pos": [
            9,
            9
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "devorador_organico",
          "pos": [
            12,
            9
          ],
          "room_id": null,
          "boss": false,
          "target": false
        },
        {
          "type": "ogro_clava",
          "pos": [
            14,
            9
          ],
          "room_id": null,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            1,
            6
          ],
          "gold": 50,
          "items": [],
          "key_objective": false
        }
      ],
      "traps": [],
      "decorations": [
        {
          "type": "cama",
          "pos": [
            4,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "arvore",
          "pos": [
            6,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        }
      ],
      "prisoner": null,
      "objectives": {
        "primary": {
          "type": "kill_all",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "resgate de elara.json",
    "id": "resgate de elara",
    "name": "Resgate de Elara",
    "defn": {
      "schema_version": 1,
      "id": "resgate de elara",
      "name": "Resgate de Elara",
      "ambiente": "masmorra",
      "grid": {
        "w": 44,
        "h": 40
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 35,
          "w": 5,
          "h": 4,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 1,
          "x": 2,
          "y": 26,
          "w": 2,
          "h": 9,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 2,
          "x": 2,
          "y": 22,
          "w": 7,
          "h": 4,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              9,
              23
            ],
            [
              9,
              24
            ],
            [
              4,
              21
            ],
            [
              5,
              21
            ],
            [
              6,
              21
            ]
          ]
        },
        {
          "id": 3,
          "x": 4,
          "y": 15,
          "w": 3,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              4,
              21
            ],
            [
              5,
              21
            ],
            [
              6,
              21
            ]
          ]
        },
        {
          "id": 4,
          "x": 9,
          "y": 23,
          "w": 9,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              9,
              23
            ],
            [
              9,
              24
            ],
            [
              15,
              25
            ],
            [
              16,
              25
            ],
            [
              17,
              25
            ]
          ]
        },
        {
          "id": 5,
          "x": 1,
          "y": 8,
          "w": 9,
          "h": 7,
          "role": "monster",
          "locked": false,
          "doors": []
        },
        {
          "id": 6,
          "x": 4,
          "y": 5,
          "w": 3,
          "h": 3,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 7,
          "x": 4,
          "y": 1,
          "w": 14,
          "h": 4,
          "role": "monster",
          "locked": true,
          "doors": []
        },
        {
          "id": 8,
          "x": 14,
          "y": 7,
          "w": 11,
          "h": 10,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              25,
              11
            ],
            [
              25,
              12
            ],
            [
              25,
              13
            ],
            [
              13,
              10
            ],
            [
              13,
              11
            ],
            [
              16,
              17
            ],
            [
              17,
              17
            ]
          ]
        },
        {
          "id": 9,
          "x": 9,
          "y": 10,
          "w": 5,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              13,
              10
            ],
            [
              13,
              11
            ]
          ]
        },
        {
          "id": 10,
          "x": 31,
          "y": 1,
          "w": 8,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              30,
              2
            ],
            [
              30,
              3
            ],
            [
              32,
              8
            ],
            [
              33,
              8
            ]
          ]
        },
        {
          "id": 11,
          "x": 21,
          "y": 0,
          "w": 9,
          "h": 6,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              20,
              2
            ],
            [
              20,
              3
            ],
            [
              30,
              2
            ],
            [
              30,
              3
            ]
          ]
        },
        {
          "id": 12,
          "x": 18,
          "y": 2,
          "w": 3,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              20,
              2
            ],
            [
              20,
              3
            ]
          ]
        },
        {
          "id": 13,
          "x": 30,
          "y": 2,
          "w": 2,
          "h": 2,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              30,
              2
            ],
            [
              30,
              3
            ]
          ]
        },
        {
          "id": 14,
          "x": 26,
          "y": 8,
          "w": 11,
          "h": 9,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              32,
              8
            ],
            [
              33,
              8
            ],
            [
              25,
              11
            ],
            [
              25,
              12
            ],
            [
              25,
              13
            ]
          ]
        },
        {
          "id": 15,
          "x": 15,
          "y": 25,
          "w": 3,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              15,
              25
            ],
            [
              16,
              25
            ],
            [
              17,
              25
            ],
            [
              15,
              31
            ],
            [
              16,
              31
            ],
            [
              17,
              31
            ]
          ]
        },
        {
          "id": 16,
          "x": 9,
          "y": 32,
          "w": 12,
          "h": 7,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              15,
              31
            ],
            [
              16,
              31
            ],
            [
              17,
              31
            ]
          ]
        },
        {
          "id": 17,
          "x": 19,
          "y": 19,
          "w": 13,
          "h": 8,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              27,
              18
            ],
            [
              28,
              18
            ],
            [
              18,
              19
            ],
            [
              18,
              20
            ],
            [
              18,
              21
            ],
            [
              18,
              22
            ]
          ]
        },
        {
          "id": 18,
          "x": 26,
          "y": 29,
          "w": 12,
          "h": 9,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              29,
              28
            ],
            [
              30,
              28
            ]
          ]
        },
        {
          "id": 19,
          "x": 13,
          "y": 17,
          "w": 6,
          "h": 6,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              16,
              17
            ],
            [
              17,
              17
            ],
            [
              18,
              19
            ],
            [
              18,
              20
            ],
            [
              18,
              21
            ],
            [
              18,
              22
            ]
          ]
        }
      ],
      "entrance": {
        "x": 2,
        "y": 37
      },
      "exit": {
        "x": 3,
        "y": 37
      },
      "monsters": [
        {
          "type": "dark_mage",
          "pos": [
            29,
            11
          ],
          "room_id": 14,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            29,
            11
          ],
          "room_id": 14,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            32,
            37
          ],
          "gold": 0,
          "items": [
            {
              "id": "health_potion"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            5,
            35
          ],
          "gold": 5000,
          "items": [
            {
              "id": "health_potion"
            },
            {
              "id": "sword"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            5,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            2,
            30
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            2,
            32
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            2,
            32
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            12,
            34
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            12,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            12,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            14,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            14,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            15,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            15,
            35
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        }
      ],
      "traps": [
        {
          "tipo": "armadilha_incendiaria",
          "pos": [
            10,
            10
          ]
        },
        {
          "tipo": "armadilha_incendiaria",
          "pos": [
            10,
            11
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            3,
            24
          ],
          "image": "fossocomestacascima.png"
        },
        {
          "tipo": "rede",
          "pos": [
            29,
            12
          ]
        },
        {
          "tipo": "fosso_estacas",
          "pos": [
            18,
            12
          ]
        },
        {
          "tipo": "nuvem_gas",
          "pos": [
            35,
            4
          ]
        },
        {
          "tipo": "mina_terrestre",
          "pos": [
            24,
            3
          ]
        },
        {
          "tipo": "mina_terrestre",
          "pos": [
            9,
            3
          ],
          "image": "armadilhamina.png"
        },
        {
          "tipo": "fosso_estacas",
          "pos": [
            8,
            3
          ],
          "image": "armadilhafococomespeinhos.png"
        },
        {
          "tipo": "buraco",
          "pos": [
            9,
            3
          ]
        },
        {
          "tipo": "armadilha_urso",
          "pos": [
            7,
            24
          ],
          "image": "armadilhaurso.png"
        },
        {
          "tipo": "armadilha_urso",
          "pos": [
            3,
            31
          ],
          "image": "armadilhaursoporcima.png"
        },
        {
          "tipo": "buraco",
          "pos": [
            6,
            11
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            3,
            30
          ],
          "image": "fossocomestacascima.png"
        },
        {
          "tipo": "buraco",
          "pos": [
            3,
            30
          ]
        }
      ],
      "decorations": [
        {
          "id": "decor_0",
          "type": "fogueira",
          "pos": [
            2,
            28
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "fogueiracircular.png",
          "vscale": [
            0.6,
            1.4
          ]
        },
        {
          "id": "decor_1",
          "type": "tumba",
          "pos": [
            6,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "key_objective": false,
          "image": "sarcofagocima.png",
          "vscale": [
            1,
            1.2
          ]
        },
        {
          "id": "decor_3",
          "type": "mesa_cadeiras",
          "pos": [
            5,
            2
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "key_objective": false,
          "image": "bancada.png",
          "vscale": [
            0.7,
            0.8
          ]
        },
        {
          "id": "decor_4",
          "type": "trono",
          "pos": [
            11,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "trono.png",
          "vscale": [
            1,
            1.8
          ]
        },
        {
          "id": "decor_5",
          "type": "cama_casal",
          "pos": [
            26,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "camacasal.png",
          "vscale": [
            0.8,
            0.8
          ]
        },
        {
          "id": "decor_6",
          "type": "arvore_grande",
          "pos": [
            17,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "arvore.png",
          "size": [
            2,
            3
          ],
          "vscale": [
            1,
            1.4
          ]
        },
        {
          "id": "decor_7",
          "type": "estante_armas",
          "pos": [
            14,
            14
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_8",
          "type": "barril",
          "pos": [
            24,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "barril.png"
        },
        {
          "id": "decor_9",
          "type": "barril",
          "pos": [
            23,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "barril.png"
        },
        {
          "id": "decor_10",
          "type": "barril",
          "pos": [
            24,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "barril.png"
        },
        {
          "id": "decor_12",
          "type": "coluna",
          "pos": [
            31,
            12
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "coluna.png",
          "vscale": [
            1,
            1.6
          ]
        },
        {
          "id": "decor_15",
          "type": "arca_tesouros",
          "pos": [
            24,
            16
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "key_objective": false,
          "image": "bau.png"
        },
        {
          "id": "decor_16",
          "type": "arca_tesouros",
          "pos": [
            23,
            16
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "key_objective": false,
          "image": "bau.png"
        },
        {
          "id": "decor_17",
          "type": "altar",
          "pos": [
            36,
            5
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "altar.png"
        },
        {
          "id": "decor_18",
          "type": "gaiola",
          "pos": [
            27,
            11
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "jaulaalta.png",
          "vscale": [
            1,
            1.4
          ]
        },
        {
          "id": "decor_23",
          "type": "arvore",
          "pos": [
            2,
            13
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "arvore_cutout.png",
          "vscale": [
            1.5,
            2
          ]
        },
        {
          "id": "decor_24",
          "type": "arvore",
          "pos": [
            5,
            19
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "arvore_cutout.png",
          "vscale": [
            0.6,
            1.5
          ]
        },
        {
          "id": "decor_25",
          "type": "fonte",
          "pos": [
            15,
            20
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "charges": 3,
          "image": "fontecircular.png",
          "vscale": [
            0.7,
            1
          ]
        },
        {
          "id": "decor_26",
          "type": "fonte",
          "pos": [
            19,
            23
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "charges": 3,
          "image": "fontedecanto.png",
          "size": [
            1,
            1
          ],
          "vscale": [
            1,
            1.2
          ]
        },
        {
          "id": "decor_27",
          "type": "chao",
          "pos": [
            2,
            22
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "chaograma1.png",
          "size": [
            7,
            4
          ]
        },
        {
          "id": "decor_28",
          "type": "cortina_vermelha",
          "pos": [
            6,
            36
          ],
          "facing": [
            -1,
            0
          ],
          "loot": null,
          "key_objective": false,
          "image": "cortina_vermelha.png"
        },
        {
          "id": "decor_29",
          "type": "cortina_vermelha",
          "pos": [
            6,
            37
          ],
          "facing": [
            -1,
            0
          ],
          "loot": null,
          "key_objective": false,
          "image": "cortina_vermelha.png"
        },
        {
          "id": "decor_30",
          "type": "cortina_vermelha",
          "pos": [
            0,
            35
          ],
          "facing": [
            1,
            0
          ],
          "loot": null,
          "key_objective": false,
          "image": "cortina_vermelha.png",
          "vscale": [
            2,
            1
          ]
        },
        {
          "id": "decor_31",
          "type": "brasao_leao",
          "pos": [
            4,
            34
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "brasao_leao.png"
        },
        {
          "id": "decor_32",
          "type": "arca_tesouros",
          "pos": [
            5,
            38
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 0,
            "items": []
          },
          "key_objective": false
        },
        {
          "id": "decor_34",
          "type": "mesa_quimica",
          "pos": [
            3,
            10
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_35",
          "type": "coluna",
          "pos": [
            34,
            12
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false,
          "image": "coluna.png",
          "vscale": [
            1,
            1.6
          ]
        },
        {
          "id": "decor_36",
          "type": "coluna",
          "pos": [
            31,
            15
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        },
        {
          "id": "decor_37",
          "type": "coluna",
          "pos": [
            34,
            15
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "key_objective": false
        }
      ],
      "secret_passages": [],
      "falas": [],
      "master_reinforcements": [],
      "expected_party": {
        "heroes": 4,
        "level": 1
      },
      "prisoner": {
        "pos": [
          27,
          37
        ],
        "room_id": 18,
        "image": "elara.png"
      },
      "materiais": {
        "2,22": "grama",
        "2,23": "grama",
        "2,24": "grama",
        "2,25": "grama",
        "3,25": "grama",
        "4,25": "grama",
        "5,25": "grama",
        "6,25": "grama",
        "7,25": "grama",
        "8,25": "grama",
        "8,24": "grama",
        "9,24": "grama",
        "9,23": "grama",
        "8,23": "grama",
        "8,22": "grama",
        "7,22": "grama",
        "6,22": "grama",
        "5,22": "grama",
        "4,22": "grama",
        "3,22": "grama",
        "3,23": "grama",
        "3,24": "grama",
        "4,24": "grama",
        "5,24": "grama",
        "6,24": "grama",
        "7,24": "grama",
        "7,23": "grama",
        "6,23": "grama",
        "5,23": "grama",
        "4,23": "grama",
        "4,20": "pedra_negra",
        "5,20": "pedra_negra",
        "6,20": "pedra_negra",
        "6,19": "pedra_negra",
        "5,19": "pedra_negra",
        "4,19": "pedra_negra",
        "4,18": "desmoronada",
        "4,17": "desmoronada",
        "4,16": "pedra_negra",
        "4,15": "pedra_negra",
        "5,15": "pedra_negra",
        "6,15": "pedra_negra",
        "6,16": "pedra_negra",
        "6,17": "pedra_negra",
        "6,18": "pedra_negra",
        "5,18": "pedra_negra",
        "5,17": "pedra_negra",
        "5,16": "pedra_negra",
        "2,26": "terra",
        "3,26": "terra",
        "3,27": "terra",
        "2,27": "terra",
        "2,28": "terra",
        "2,29": "terra",
        "2,30": "terra",
        "3,29": "terra",
        "3,28": "terra",
        "3,30": "terra",
        "3,31": "terra",
        "2,31": "terra",
        "2,32": "terra",
        "2,33": "terra",
        "2,34": "terra",
        "3,34": "terra",
        "3,33": "terra",
        "3,32": "terra",
        "19,25": "desmoronada",
        "18,25": "desmoronada",
        "18,24": "desmoronada",
        "18,23": "desmoronada",
        "18,26": "desmoronada",
        "18,27": "desmoronada",
        "18,28": "desmoronada",
        "18,29": "desmoronada",
        "18,30": "desmoronada",
        "18,31": "desmoronada",
        "19,31": "desmoronada",
        "20,31": "desmoronada",
        "20,30": "desmoronada",
        "20,29": "desmoronada",
        "20,28": "desmoronada",
        "20,27": "desmoronada",
        "21,27": "desmoronada",
        "22,27": "desmoronada",
        "22,28": "desmoronada",
        "22,29": "desmoronada",
        "22,30": "desmoronada",
        "22,31": "desmoronada",
        "22,32": "desmoronada",
        "22,33": "desmoronada",
        "22,34": "desmoronada",
        "22,35": "desmoronada",
        "22,36": "desmoronada",
        "22,37": "desmoronada",
        "22,38": "desmoronada",
        "22,39": "desmoronada",
        "21,39": "desmoronada",
        "20,39": "desmoronada",
        "19,39": "desmoronada",
        "18,39": "desmoronada",
        "17,39": "desmoronada",
        "16,39": "desmoronada",
        "15,39": "desmoronada",
        "14,39": "desmoronada",
        "13,39": "desmoronada",
        "12,39": "desmoronada",
        "11,39": "desmoronada",
        "10,39": "desmoronada",
        "9,39": "desmoronada",
        "8,39": "desmoronada",
        "8,38": "desmoronada",
        "8,37": "desmoronada",
        "8,36": "desmoronada",
        "8,35": "desmoronada",
        "8,34": "desmoronada",
        "8,33": "desmoronada",
        "8,32": "desmoronada",
        "8,31": "desmoronada",
        "8,30": "desmoronada",
        "8,29": "desmoronada",
        "8,28": "desmoronada",
        "8,27": "desmoronada",
        "8,26": "desmoronada",
        "7,26": "desmoronada",
        "6,26": "pedra_caverna",
        "6,27": "pedra_caverna",
        "6,28": "pedra_caverna",
        "6,29": "pedra_caverna",
        "6,30": "pedra_caverna",
        "6,31": "pedra_caverna",
        "6,32": "pedra_caverna",
        "6,33": "pedra_caverna",
        "6,34": "pedra_caverna",
        "6,35": "pedra_caverna",
        "6,36": "pedra_caverna",
        "6,37": "pedra_caverna",
        "6,38": "pedra_caverna",
        "6,39": "pedra_caverna",
        "5,39": "pedra_caverna",
        "4,39": "pedra_caverna",
        "3,39": "pedra_caverna",
        "2,39": "pedra_caverna",
        "1,39": "pedra_caverna",
        "0,39": "pedra_caverna",
        "0,38": "pedra_caverna",
        "0,37": "pedra_caverna",
        "0,36": "pedra_caverna",
        "0,35": "pedra_caverna",
        "0,34": "pedra_caverna",
        "0,33": "pedra_caverna",
        "0,32": "pedra_caverna",
        "0,31": "pedra_caverna",
        "0,30": "pedra_caverna",
        "0,29": "pedra_caverna",
        "0,28": "pedra_caverna",
        "0,27": "pedra_caverna",
        "0,26": "pedra_caverna",
        "0,25": "desmoronada",
        "0,24": "desmoronada",
        "0,23": "desmoronada",
        "0,22": "desmoronada",
        "0,21": "desmoronada",
        "0,20": "desmoronada",
        "0,19": "desmoronada",
        "0,18": "desmoronada",
        "0,17": "desmoronada",
        "0,16": "desmoronada",
        "0,15": "desmoronada",
        "0,14": "desmoronada",
        "0,13": "desmoronada",
        "0,12": "desmoronada",
        "0,11": "desmoronada",
        "0,10": "desmoronada",
        "0,9": "desmoronada",
        "0,8": "desmoronada",
        "4,0": "enegrecida",
        "5,0": "enegrecida",
        "6,0": "enegrecida",
        "7,0": "enegrecida",
        "8,0": "enegrecida",
        "9,0": "enegrecida",
        "10,0": "enegrecida",
        "11,0": "enegrecida",
        "12,0": "enegrecida",
        "13,0": "enegrecida",
        "14,0": "enegrecida",
        "15,0": "enegrecida",
        "16,0": "enegrecida",
        "17,0": "enegrecida",
        "18,0": "enegrecida",
        "18,1": "enegrecida",
        "19,1": "enegrecida",
        "20,1": "enegrecida",
        "20,0": "enegrecida",
        "19,0": "enegrecida",
        "1,15": "desmoronada",
        "2,15": "desmoronada",
        "2,16": "desmoronada",
        "2,17": "desmoronada",
        "2,18": "desmoronada",
        "2,19": "desmoronada",
        "2,20": "desmoronada",
        "2,21": "desmoronada",
        "3,21": "desmoronada",
        "3,20": "desmoronada",
        "3,19": "desmoronada",
        "3,18": "desmoronada",
        "3,17": "desmoronada",
        "3,16": "desmoronada",
        "3,15": "desmoronada",
        "1,16": "desmoronada",
        "1,17": "desmoronada",
        "1,18": "desmoronada",
        "1,19": "desmoronada",
        "1,20": "desmoronada",
        "1,21": "desmoronada",
        "1,22": "desmoronada",
        "1,23": "desmoronada",
        "1,24": "desmoronada",
        "1,25": "desmoronada",
        "1,26": "pedra_caverna",
        "1,27": "pedra_caverna",
        "1,28": "pedra_caverna",
        "1,29": "pedra_caverna",
        "1,30": "pedra_caverna",
        "1,31": "pedra_caverna",
        "1,32": "pedra_caverna",
        "1,33": "pedra_caverna",
        "1,34": "pedra_caverna",
        "5,34": "pedra_caverna",
        "4,34": "pedra_caverna",
        "4,33": "pedra_caverna",
        "4,32": "pedra_caverna",
        "4,31": "pedra_caverna",
        "4,30": "pedra_caverna",
        "4,29": "pedra_caverna",
        "4,28": "pedra_caverna",
        "4,27": "pedra_caverna",
        "4,26": "pedra_caverna",
        "5,33": "pedra_caverna",
        "5,32": "pedra_caverna",
        "5,31": "pedra_caverna",
        "5,30": "pedra_caverna",
        "5,29": "pedra_caverna",
        "5,28": "pedra_caverna",
        "5,27": "pedra_caverna",
        "5,26": "pedra_caverna",
        "9,26": "desmoronada",
        "9,25": "desmoronada",
        "10,25": "desmoronada",
        "11,25": "desmoronada",
        "11,26": "desmoronada",
        "11,27": "desmoronada",
        "11,28": "desmoronada",
        "11,29": "desmoronada",
        "11,30": "desmoronada",
        "11,31": "desmoronada",
        "10,31": "desmoronada",
        "12,31": "desmoronada",
        "13,31": "desmoronada",
        "13,30": "desmoronada",
        "13,29": "desmoronada",
        "13,28": "desmoronada",
        "13,27": "desmoronada",
        "13,26": "desmoronada",
        "13,25": "desmoronada",
        "14,25": "desmoronada",
        "14,26": "desmoronada",
        "14,27": "desmoronada",
        "14,28": "desmoronada",
        "14,29": "desmoronada",
        "14,30": "desmoronada",
        "14,31": "desmoronada",
        "10,30": "desmoronada",
        "12,30": "desmoronada",
        "10,29": "desmoronada",
        "12,29": "desmoronada",
        "10,28": "desmoronada",
        "12,28": "desmoronada",
        "10,27": "desmoronada",
        "12,27": "desmoronada",
        "12,26": "desmoronada",
        "12,25": "desmoronada",
        "10,26": "desmoronada",
        "7,27": "desmoronada",
        "9,27": "desmoronada",
        "7,28": "desmoronada",
        "9,28": "desmoronada",
        "7,29": "desmoronada",
        "9,29": "desmoronada",
        "7,30": "desmoronada",
        "9,30": "desmoronada",
        "7,31": "desmoronada",
        "9,31": "desmoronada",
        "7,32": "desmoronada",
        "7,33": "desmoronada",
        "7,34": "desmoronada",
        "7,35": "desmoronada",
        "7,36": "desmoronada",
        "7,37": "desmoronada",
        "7,38": "desmoronada",
        "7,39": "desmoronada",
        "23,39": "desmoronada",
        "24,39": "desmoronada",
        "24,38": "desmoronada",
        "24,37": "desmoronada",
        "24,36": "desmoronada",
        "24,35": "desmoronada",
        "24,34": "desmoronada",
        "24,33": "desmoronada",
        "24,32": "desmoronada",
        "24,31": "desmoronada",
        "24,30": "desmoronada",
        "24,29": "desmoronada",
        "24,28": "desmoronada",
        "24,27": "desmoronada",
        "25,27": "desmoronada",
        "26,27": "desmoronada",
        "26,28": "desmoronada",
        "27,28": "desmoronada",
        "28,28": "desmoronada",
        "28,27": "desmoronada",
        "27,27": "desmoronada",
        "25,28": "desmoronada",
        "25,29": "desmoronada",
        "25,30": "desmoronada",
        "25,31": "desmoronada",
        "25,32": "desmoronada",
        "25,33": "desmoronada",
        "25,34": "desmoronada",
        "25,35": "desmoronada",
        "25,36": "desmoronada",
        "25,37": "desmoronada",
        "25,38": "desmoronada",
        "26,38": "desmoronada",
        "26,39": "desmoronada",
        "27,39": "desmoronada",
        "28,39": "desmoronada",
        "28,38": "desmoronada",
        "29,38": "desmoronada",
        "30,38": "desmoronada",
        "30,39": "desmoronada",
        "31,39": "desmoronada",
        "32,39": "desmoronada",
        "32,38": "desmoronada",
        "33,38": "desmoronada",
        "34,38": "desmoronada",
        "34,39": "desmoronada",
        "35,39": "desmoronada",
        "36,39": "desmoronada",
        "36,38": "desmoronada",
        "37,38": "desmoronada",
        "38,38": "desmoronada",
        "38,37": "desmoronada",
        "38,36": "desmoronada",
        "38,35": "desmoronada",
        "38,34": "desmoronada",
        "38,33": "desmoronada",
        "38,32": "desmoronada",
        "38,31": "desmoronada",
        "38,30": "desmoronada",
        "38,29": "desmoronada",
        "38,28": "desmoronada",
        "38,27": "desmoronada",
        "38,26": "desmoronada",
        "38,25": "desmoronada",
        "38,24": "desmoronada",
        "38,23": "desmoronada",
        "38,22": "desmoronada",
        "38,21": "desmoronada",
        "38,20": "desmoronada",
        "38,19": "desmoronada",
        "38,18": "desmoronada",
        "38,17": "desmoronada",
        "38,16": "desmoronada",
        "38,15": "desmoronada",
        "38,14": "desmoronada",
        "38,13": "desmoronada",
        "38,12": "desmoronada",
        "38,11": "desmoronada",
        "38,10": "desmoronada",
        "38,9": "desmoronada",
        "38,8": "desmoronada",
        "37,8": "desmoronada",
        "36,8": "desmoronada",
        "35,8": "desmoronada",
        "34,8": "desmoronada",
        "39,8": "desmoronada",
        "39,7": "desmoronada",
        "39,6": "desmoronada",
        "39,5": "desmoronada",
        "39,4": "desmoronada",
        "39,3": "desmoronada",
        "39,2": "desmoronada",
        "39,1": "desmoronada",
        "39,0": "desmoronada",
        "38,0": "desmoronada",
        "37,0": "desmoronada",
        "36,0": "desmoronada",
        "35,0": "desmoronada",
        "34,0": "desmoronada",
        "33,0": "desmoronada",
        "32,0": "desmoronada",
        "31,0": "desmoronada",
        "30,0": "enegrecida",
        "30,1": "enegrecida",
        "40,0": "desmoronada",
        "41,0": "desmoronada",
        "41,1": "desmoronada",
        "41,2": "desmoronada",
        "41,3": "desmoronada",
        "41,4": "desmoronada",
        "41,5": "desmoronada",
        "41,6": "desmoronada",
        "41,7": "desmoronada",
        "41,8": "desmoronada",
        "41,9": "desmoronada",
        "41,10": "desmoronada",
        "41,11": "desmoronada",
        "41,12": "desmoronada",
        "41,13": "desmoronada",
        "41,14": "desmoronada",
        "41,15": "desmoronada",
        "41,16": "desmoronada",
        "41,17": "desmoronada",
        "41,18": "desmoronada",
        "41,19": "desmoronada",
        "41,20": "desmoronada",
        "41,21": "desmoronada",
        "41,22": "desmoronada",
        "41,23": "desmoronada",
        "41,24": "desmoronada",
        "41,25": "desmoronada",
        "41,26": "desmoronada",
        "41,27": "desmoronada",
        "41,28": "desmoronada",
        "41,29": "desmoronada",
        "41,30": "desmoronada",
        "41,31": "desmoronada",
        "41,32": "desmoronada",
        "41,33": "desmoronada",
        "41,34": "desmoronada",
        "41,35": "desmoronada",
        "41,36": "desmoronada",
        "41,37": "desmoronada",
        "41,38": "desmoronada",
        "41,39": "desmoronada",
        "40,39": "desmoronada",
        "39,39": "desmoronada",
        "42,39": "desmoronada",
        "43,39": "desmoronada",
        "43,38": "desmoronada",
        "43,37": "desmoronada",
        "43,36": "desmoronada",
        "43,35": "desmoronada",
        "43,34": "desmoronada",
        "43,33": "desmoronada",
        "43,32": "desmoronada",
        "43,31": "desmoronada",
        "43,30": "desmoronada",
        "43,29": "desmoronada",
        "43,28": "desmoronada",
        "43,27": "desmoronada",
        "43,26": "desmoronada",
        "43,25": "desmoronada",
        "43,24": "desmoronada",
        "43,23": "desmoronada",
        "43,22": "desmoronada",
        "43,21": "desmoronada",
        "43,20": "desmoronada",
        "43,19": "desmoronada",
        "43,18": "desmoronada",
        "43,17": "desmoronada",
        "43,16": "desmoronada",
        "43,15": "desmoronada",
        "43,14": "desmoronada",
        "43,13": "desmoronada",
        "43,12": "desmoronada",
        "43,11": "desmoronada",
        "43,10": "desmoronada",
        "43,9": "desmoronada",
        "43,8": "desmoronada",
        "43,7": "desmoronada",
        "43,6": "desmoronada",
        "43,5": "desmoronada",
        "43,4": "desmoronada",
        "43,3": "desmoronada",
        "43,2": "desmoronada",
        "43,1": "desmoronada",
        "43,0": "desmoronada",
        "40,38": "desmoronada",
        "42,38": "desmoronada",
        "40,37": "desmoronada",
        "42,37": "desmoronada",
        "40,36": "desmoronada",
        "42,36": "desmoronada",
        "40,35": "desmoronada",
        "42,35": "desmoronada",
        "40,34": "desmoronada",
        "42,34": "desmoronada",
        "40,33": "desmoronada",
        "42,33": "desmoronada",
        "40,32": "desmoronada",
        "42,32": "desmoronada",
        "40,31": "desmoronada",
        "42,31": "desmoronada",
        "40,30": "desmoronada",
        "42,30": "desmoronada",
        "40,29": "desmoronada",
        "42,29": "desmoronada",
        "40,28": "desmoronada",
        "42,28": "desmoronada",
        "40,27": "desmoronada",
        "42,27": "desmoronada",
        "40,26": "desmoronada",
        "42,26": "desmoronada",
        "40,25": "desmoronada",
        "42,25": "desmoronada",
        "40,24": "desmoronada",
        "42,24": "desmoronada",
        "40,23": "desmoronada",
        "42,23": "desmoronada",
        "40,22": "desmoronada",
        "42,22": "desmoronada",
        "40,21": "desmoronada",
        "42,21": "desmoronada",
        "40,20": "desmoronada",
        "42,20": "desmoronada",
        "40,19": "desmoronada",
        "42,19": "desmoronada",
        "40,18": "desmoronada",
        "42,18": "desmoronada",
        "40,17": "desmoronada",
        "42,17": "desmoronada",
        "40,16": "desmoronada",
        "42,16": "desmoronada",
        "40,15": "desmoronada",
        "42,15": "desmoronada",
        "40,14": "desmoronada",
        "42,14": "desmoronada",
        "40,13": "desmoronada",
        "42,13": "desmoronada",
        "40,12": "desmoronada",
        "42,12": "desmoronada",
        "40,11": "desmoronada",
        "42,11": "desmoronada",
        "40,10": "desmoronada",
        "42,10": "desmoronada",
        "40,9": "desmoronada",
        "42,9": "desmoronada",
        "42,8": "desmoronada",
        "42,7": "desmoronada",
        "42,6": "desmoronada",
        "42,5": "desmoronada",
        "42,4": "desmoronada",
        "42,3": "desmoronada",
        "42,2": "desmoronada",
        "42,1": "desmoronada",
        "42,0": "desmoronada",
        "40,1": "desmoronada",
        "40,2": "desmoronada",
        "40,3": "desmoronada",
        "40,4": "desmoronada",
        "40,5": "desmoronada",
        "40,6": "desmoronada",
        "40,7": "desmoronada",
        "40,8": "desmoronada",
        "37,9": "desmoronada",
        "39,9": "desmoronada",
        "37,10": "desmoronada",
        "39,10": "desmoronada",
        "37,11": "desmoronada",
        "39,11": "desmoronada",
        "37,12": "desmoronada",
        "39,12": "desmoronada",
        "37,13": "desmoronada",
        "39,13": "desmoronada",
        "37,14": "desmoronada",
        "39,14": "desmoronada",
        "37,15": "desmoronada",
        "39,15": "desmoronada",
        "37,16": "desmoronada",
        "39,16": "desmoronada",
        "37,17": "desmoronada",
        "36,17": "desmoronada",
        "36,18": "desmoronada",
        "36,19": "desmoronada",
        "36,20": "desmoronada",
        "36,21": "desmoronada",
        "36,22": "desmoronada",
        "36,23": "desmoronada",
        "36,24": "desmoronada",
        "36,25": "desmoronada",
        "36,26": "desmoronada",
        "36,27": "desmoronada",
        "36,28": "desmoronada",
        "35,28": "desmoronada",
        "34,28": "desmoronada",
        "34,27": "desmoronada",
        "34,26": "desmoronada",
        "34,25": "desmoronada",
        "34,24": "desmoronada",
        "34,23": "desmoronada",
        "34,22": "desmoronada",
        "34,21": "desmoronada",
        "34,20": "desmoronada",
        "34,19": "desmoronada",
        "34,18": "desmoronada",
        "34,17": "desmoronada",
        "33,17": "desmoronada",
        "32,17": "desmoronada",
        "32,18": "desmoronada",
        "32,19": "desmoronada",
        "32,20": "desmoronada",
        "32,21": "desmoronada",
        "32,22": "desmoronada",
        "32,23": "desmoronada",
        "32,24": "desmoronada",
        "32,25": "desmoronada",
        "32,26": "desmoronada",
        "32,27": "desmoronada",
        "32,28": "desmoronada",
        "31,28": "desmoronada",
        "31,27": "desmoronada",
        "31,18": "desmoronada",
        "30,18": "desmoronada",
        "30,17": "desmoronada",
        "29,17": "desmoronada",
        "29,18": "desmoronada",
        "31,17": "desmoronada",
        "33,18": "desmoronada",
        "33,19": "desmoronada",
        "33,20": "desmoronada",
        "33,21": "desmoronada",
        "33,22": "desmoronada",
        "33,23": "desmoronada",
        "33,24": "desmoronada",
        "33,25": "desmoronada",
        "33,26": "desmoronada",
        "33,27": "desmoronada",
        "33,28": "desmoronada",
        "35,27": "desmoronada",
        "35,26": "desmoronada",
        "35,25": "desmoronada",
        "35,24": "desmoronada",
        "35,23": "desmoronada",
        "35,22": "desmoronada",
        "35,21": "desmoronada",
        "35,20": "desmoronada",
        "35,19": "desmoronada",
        "35,18": "desmoronada",
        "35,17": "desmoronada",
        "39,17": "desmoronada",
        "37,18": "desmoronada",
        "39,18": "desmoronada",
        "37,19": "desmoronada",
        "39,19": "desmoronada",
        "37,20": "desmoronada",
        "39,20": "desmoronada",
        "37,21": "desmoronada",
        "39,21": "desmoronada",
        "37,22": "desmoronada",
        "39,22": "desmoronada",
        "37,23": "desmoronada",
        "39,23": "desmoronada",
        "37,24": "desmoronada",
        "39,24": "desmoronada",
        "37,25": "desmoronada",
        "39,25": "desmoronada",
        "37,26": "desmoronada",
        "39,26": "desmoronada",
        "37,27": "desmoronada",
        "39,27": "desmoronada",
        "37,28": "desmoronada",
        "39,28": "desmoronada",
        "39,29": "desmoronada",
        "39,30": "desmoronada",
        "39,31": "desmoronada",
        "39,32": "desmoronada",
        "39,33": "desmoronada",
        "39,34": "desmoronada",
        "39,35": "desmoronada",
        "39,36": "desmoronada",
        "39,37": "desmoronada",
        "38,39": "desmoronada",
        "39,38": "desmoronada",
        "37,39": "desmoronada",
        "35,38": "desmoronada",
        "33,39": "desmoronada",
        "31,38": "desmoronada",
        "29,39": "desmoronada",
        "27,38": "desmoronada",
        "25,39": "desmoronada",
        "21,38": "desmoronada",
        "23,38": "desmoronada",
        "21,37": "desmoronada",
        "23,37": "desmoronada",
        "21,36": "desmoronada",
        "23,36": "desmoronada",
        "21,35": "desmoronada",
        "23,35": "desmoronada",
        "21,34": "desmoronada",
        "23,34": "desmoronada",
        "21,33": "desmoronada",
        "23,33": "desmoronada",
        "21,32": "desmoronada",
        "23,32": "desmoronada",
        "23,31": "desmoronada",
        "23,30": "desmoronada",
        "23,29": "desmoronada",
        "23,28": "desmoronada",
        "23,27": "desmoronada",
        "21,28": "desmoronada",
        "21,29": "desmoronada",
        "21,30": "desmoronada",
        "21,31": "desmoronada",
        "19,30": "desmoronada",
        "19,29": "desmoronada",
        "19,28": "desmoronada",
        "19,27": "desmoronada",
        "10,16": "pedra_caverna",
        "10,15": "pedra_caverna",
        "10,14": "pedra_caverna",
        "10,13": "pedra_caverna",
        "10,12": "pedra_caverna",
        "11,12": "pedra_caverna",
        "12,12": "pedra_caverna",
        "12,13": "pedra_caverna",
        "12,14": "pedra_caverna",
        "12,15": "pedra_caverna",
        "12,16": "pedra_caverna",
        "12,17": "pedra_caverna",
        "12,18": "pedra_caverna",
        "12,19": "pedra_caverna",
        "12,20": "pedra_caverna",
        "12,21": "pedra_caverna",
        "12,22": "pedra_caverna",
        "11,22": "pedra_caverna",
        "10,22": "pedra_caverna",
        "10,21": "pedra_caverna",
        "10,20": "pedra_caverna",
        "10,19": "pedra_caverna",
        "10,18": "pedra_caverna",
        "9,18": "pedra_caverna",
        "9,17": "pedra_caverna",
        "8,17": "desmoronada",
        "8,16": "desmoronada",
        "8,15": "desmoronada",
        "7,15": "desmoronada",
        "7,16": "desmoronada",
        "7,17": "desmoronada",
        "7,18": "desmoronada",
        "7,19": "desmoronada",
        "7,20": "desmoronada",
        "7,21": "desmoronada",
        "8,21": "desmoronada",
        "8,20": "desmoronada",
        "8,19": "desmoronada",
        "8,18": "desmoronada",
        "9,19": "pedra_caverna",
        "9,20": "pedra_caverna",
        "9,21": "pedra_caverna",
        "9,22": "pedra_caverna",
        "11,21": "pedra_caverna",
        "11,20": "pedra_caverna",
        "11,19": "pedra_caverna",
        "11,18": "pedra_caverna",
        "11,17": "pedra_caverna",
        "13,17": "pedra_caverna",
        "14,17": "pedra_caverna",
        "15,17": "pedra_caverna",
        "13,16": "enegrecida",
        "13,15": "enegrecida",
        "13,14": "enegrecida",
        "13,13": "enegrecida",
        "13,12": "enegrecida",
        "11,13": "pedra_caverna",
        "11,14": "pedra_caverna",
        "9,15": "pedra_caverna",
        "11,15": "pedra_caverna",
        "10,17": "pedra_caverna",
        "9,16": "pedra_caverna",
        "11,16": "pedra_caverna",
        "12,6": "enegrecida",
        "12,5": "enegrecida",
        "11,5": "enegrecida",
        "10,5": "enegrecida",
        "10,6": "enegrecida",
        "10,7": "enegrecida",
        "10,8": "enegrecida",
        "10,9": "enegrecida",
        "11,9": "enegrecida",
        "12,9": "enegrecida",
        "12,8": "enegrecida",
        "13,8": "enegrecida",
        "13,7": "enegrecida",
        "13,9": "enegrecida",
        "11,8": "enegrecida",
        "9,7": "enegrecida",
        "8,7": "enegrecida",
        "8,6": "enegrecida",
        "8,5": "enegrecida",
        "7,5": "enegrecida",
        "7,6": "enegrecida",
        "7,7": "enegrecida",
        "11,7": "enegrecida",
        "9,6": "enegrecida",
        "9,5": "enegrecida",
        "13,5": "enegrecida",
        "14,5": "enegrecida",
        "14,6": "enegrecida",
        "15,6": "enegrecida",
        "16,6": "enegrecida",
        "16,5": "enegrecida",
        "17,5": "enegrecida",
        "18,5": "enegrecida",
        "18,4": "enegrecida",
        "19,4": "enegrecida",
        "20,4": "enegrecida",
        "20,5": "enegrecida",
        "20,6": "enegrecida",
        "19,6": "enegrecida",
        "21,6": "enegrecida",
        "22,6": "enegrecida",
        "23,6": "enegrecida",
        "24,6": "enegrecida",
        "25,6": "enegrecida",
        "25,7": "enegrecida",
        "25,8": "enegrecida",
        "25,9": "enegrecida",
        "25,10": "enegrecida",
        "26,8": "pedra_caverna",
        "27,8": "pedra_caverna",
        "27,7": "enegrecida",
        "27,6": "enegrecida",
        "28,6": "enegrecida",
        "29,6": "enegrecida",
        "29,7": "enegrecida",
        "29,8": "pedra_caverna",
        "30,8": "pedra_caverna",
        "31,8": "pedra_caverna",
        "30,7": "enegrecida",
        "30,6": "enegrecida",
        "30,5": "enegrecida",
        "30,4": "enegrecida",
        "28,7": "enegrecida",
        "28,8": "pedra_caverna",
        "26,7": "enegrecida",
        "26,6": "enegrecida",
        "18,6": "enegrecida",
        "19,5": "enegrecida",
        "17,6": "enegrecida",
        "15,5": "enegrecida",
        "12,7": "enegrecida",
        "11,6": "enegrecida",
        "13,6": "enegrecida",
        "25,18": "enegrecida",
        "25,17": "enegrecida",
        "25,16": "enegrecida",
        "25,15": "enegrecida",
        "25,14": "enegrecida",
        "24,17": "enegrecida",
        "23,17": "enegrecida",
        "23,18": "enegrecida",
        "22,18": "enegrecida",
        "21,18": "enegrecida",
        "21,17": "enegrecida",
        "20,17": "enegrecida",
        "19,17": "enegrecida",
        "19,18": "enegrecida",
        "18,17": "pedra_caverna",
        "20,18": "enegrecida",
        "22,17": "enegrecida",
        "26,17": "pedra_caverna",
        "24,18": "enegrecida",
        "26,18": "pedra_caverna",
        "20,22": "desmoronada",
        "21,22": "desmoronada",
        "2,8": "pedra_negra",
        "1,8": "pedra_negra",
        "1,9": "pedra_negra",
        "2,9": "pedra_negra",
        "3,9": "pedra_negra",
        "4,9": "pedra_negra",
        "6,9": "pedra_negra",
        "7,9": "pedra_negra",
        "8,9": "pedra_negra",
        "9,9": "pedra_negra",
        "9,8": "pedra_negra",
        "8,8": "pedra_negra",
        "7,8": "pedra_negra",
        "6,8": "pedra_negra",
        "4,8": "pedra_negra",
        "3,8": "pedra_negra",
        "5,8": "pedra_negra",
        "5,9": "pedra_negra",
        "5,10": "pedra_negra",
        "4,10": "pedra_negra",
        "3,10": "pedra_negra",
        "2,10": "pedra_negra",
        "7,10": "pedra_negra",
        "8,10": "pedra_negra",
        "9,10": "pedra_negra"
      },
      "objectives": {
        "primary": {
          "type": "rescue_prisoner",
          "xp": 100,
          "reward": {
            "gold": 150,
            "items": []
          }
        },
        "secondary": [
          {
            "type": "rescue_prisoner",
            "xp": 50,
            "reward": {
              "gold": 25,
              "items": []
            }
          },
          {
            "type": "reach_exit",
            "xp": 50,
            "reward": {
              "gold": 25,
              "items": []
            }
          }
        ]
      }
    }
  },
  {
    "file": "resgate_prisioneiro.json",
    "id": "resgate_prisioneiro",
    "name": "resgate_prisioneiro",
    "defn": {
      "schema_version": 1,
      "id": "resgate_prisioneiro",
      "name": "resgate_prisioneiro",
      "grid": {
        "w": 16,
        "h": 12
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          2,
          2,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 4,
          "y": 0,
          "w": 5,
          "h": 3,
          "role": "trap",
          "locked": false,
          "doors": [
            [
              4,
              2
            ],
            [
              5,
              2
            ],
            [
              7,
              2
            ],
            [
              8,
              2
            ],
            [
              5,
              0
            ],
            [
              4,
              0
            ]
          ]
        },
        {
          "id": 1,
          "x": 4,
          "y": 9,
          "w": 5,
          "h": 3,
          "role": "entrance",
          "locked": true,
          "doors": []
        }
      ],
      "entrance": {
        "x": 6,
        "y": 10
      },
      "exit": null,
      "monsters": [],
      "chests": [],
      "traps": [
        {
          "tipo": "buraco",
          "pos": [
            4,
            4
          ]
        },
        {
          "tipo": "rede",
          "pos": [
            5,
            4
          ]
        },
        {
          "tipo": "nuvem_gas",
          "pos": [
            6,
            4
          ]
        },
        {
          "tipo": "fosso_envenenado",
          "pos": [
            7,
            4
          ],
          "veneno_id": "veneno_polvo_abissal"
        },
        {
          "tipo": "buraco",
          "pos": [
            6,
            4
          ]
        },
        {
          "tipo": "mina_terrestre",
          "pos": [
            8,
            4
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            6,
            4
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            7,
            4
          ]
        },
        {
          "tipo": "buraco",
          "pos": [
            6,
            6
          ]
        }
      ],
      "prisoner": {
        "pos": [
          6,
          0
        ],
        "room_id": 0
      },
      "objectives": {
        "primary": {
          "type": "rescue_prisoner"
        },
        "secondary": []
      }
    }
  },
  {
    "file": "terrenos.json",
    "id": "terrenos",
    "name": "terrenos",
    "defn": {
      "schema_version": 1,
      "id": "terrenos",
      "name": "terrenos",
      "ambiente": "ar_livre",
      "grid": {
        "w": 16,
        "h": 12
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 2,
          "y": 2,
          "w": 3,
          "h": 8,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 3,
        "y": 6
      },
      "exit": null,
      "monsters": [],
      "chests": [],
      "traps": [],
      "decorations": [
        {
          "type": "chao",
          "pos": [
            12,
            4
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chãoagua.png",
          "size": [
            3,
            4
          ]
        },
        {
          "type": "chao",
          "pos": [
            12,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaoaguarasa.png",
          "size": [
            3,
            1
          ]
        },
        {
          "type": "chao",
          "pos": [
            12,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaoaguarasa.png",
          "size": [
            3,
            1
          ]
        },
        {
          "type": "chao",
          "pos": [
            11,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaoaguarasa.png",
          "size": [
            1,
            6
          ]
        },
        {
          "type": "chao",
          "pos": [
            11,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaoterra.png",
          "size": [
            4,
            1
          ]
        },
        {
          "type": "chao",
          "pos": [
            10,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaoterra.png",
          "size": [
            1,
            8
          ]
        },
        {
          "type": "chao",
          "pos": [
            11,
            9
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaoterra.png",
          "size": [
            4,
            1
          ]
        },
        {
          "type": "chao",
          "pos": [
            8,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaopantano.png",
          "size": [
            2,
            8
          ]
        },
        {
          "type": "chao",
          "pos": [
            4,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "chaopedranegra.png",
          "size": [
            4,
            8
          ]
        }
      ],
      "prisoner": null,
      "materiais": {},
      "objectives": {
        "primary": {
          "type": "kill_all",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "test_camp_a.json",
    "id": "test_camp_a",
    "name": "Campanha A",
    "defn": {
      "schema_version": 1,
      "id": "test_camp_a",
      "name": "Campanha A",
      "grid": {
        "w": 10,
        "h": 8
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 8,
          "h": 6,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 2,
        "y": 2
      },
      "exit": null,
      "monsters": [
        {
          "type": "goblin",
          "pos": [
            5,
            3
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        }
      ],
      "chests": [],
      "traps": [],
      "prisoner": null,
      "objectives": {
        "primary": {
          "type": "kill_all"
        },
        "secondary": []
      }
    }
  },
  {
    "file": "test_camp_b.json",
    "id": "test_camp_b",
    "name": "Campanha B",
    "defn": {
      "schema_version": 1,
      "id": "test_camp_b",
      "name": "Campanha B",
      "grid": {
        "w": 12,
        "h": 8
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 10,
          "h": 6,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 2,
        "y": 2
      },
      "exit": null,
      "monsters": [
        {
          "type": "skeleton",
          "pos": [
            5,
            3
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        }
      ],
      "chests": [],
      "traps": [],
      "prisoner": null,
      "objectives": {
        "primary": {
          "type": "kill_all"
        },
        "secondary": []
      }
    }
  },
  {
    "file": "test_decoracoes.json",
    "id": "test_decoracoes",
    "name": "Teste de Decorações",
    "defn": {
      "schema_version": 1,
      "id": "test_decoracoes",
      "name": "Teste de Decorações",
      "grid": {
        "w": 12,
        "h": 12
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 10,
          "h": 10,
          "role": "entrance",
          "locked": false,
          "doors": []
        }
      ],
      "entrance": {
        "x": 1,
        "y": 1
      },
      "exit": null,
      "prisoner": null,
      "monsters": [],
      "chests": [],
      "traps": [],
      "decorations": [
        {
          "type": "cama",
          "pos": [
            2,
            2
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "fonte",
          "pos": [
            5,
            5
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "charges": 3
        },
        {
          "type": "fogueira",
          "pos": [
            8,
            3
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        },
        {
          "type": "arca_tesouros",
          "pos": [
            3,
            8
          ],
          "facing": [
            0,
            1
          ],
          "loot": {
            "gold": 20,
            "items": [
              {
                "id": "health_potion"
              }
            ]
          }
        },
        {
          "type": "coluna",
          "pos": [
            7,
            7
          ],
          "facing": [
            0,
            1
          ],
          "loot": null
        }
      ],
      "objectives": {
        "primary": {
          "type": "kill_all"
        },
        "secondary": []
      }
    }
  },
  {
    "file": "test_fase1.json",
    "id": "test_fase1",
    "name": "Teste Fase 1 — Duas Salas",
    "defn": {
      "schema_version": 1,
      "id": "test_fase1",
      "name": "Teste Fase 1 — Duas Salas",
      "grid": {
        "w": 16,
        "h": 12
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 5,
          "h": 4,
          "role": "entrance",
          "locked": false,
          "doors": [
            [
              6,
              3
            ]
          ]
        },
        {
          "id": 1,
          "x": 10,
          "y": 1,
          "w": 5,
          "h": 4,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              9,
              3
            ]
          ]
        }
      ],
      "entrance": {
        "x": 3,
        "y": 2
      },
      "exit": {
        "x": 12,
        "y": 2
      },
      "monsters": [
        {
          "type": "goblin",
          "pos": [
            12,
            2
          ],
          "room_id": 1,
          "boss": false,
          "target": false
        },
        {
          "type": "skeleton",
          "pos": [
            13,
            3
          ],
          "room_id": 1,
          "boss": false,
          "target": false
        },
        {
          "type": "lagarto_carniceiro",
          "pos": [
            11,
            2
          ],
          "room_id": 1,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            11,
            4
          ],
          "gold": 25,
          "items": [
            {
              "id": "health_potion"
            },
            {
              "id": "shortsword"
            }
          ],
          "key_objective": false
        }
      ],
      "traps": [
        {
          "tipo": "fosso_estacas",
          "pos": [
            7,
            3
          ]
        }
      ],
      "prisoner": {
        "pos": [
          14,
          4
        ],
        "room_id": 1
      },
      "objectives": {
        "primary": {
          "type": "kill_all"
        },
        "secondary": [
          {
            "type": "rescue_prisoner"
          }
        ]
      }
    }
  },
  {
    "file": "test_fase3.json",
    "id": "test_fase3",
    "name": "Teste Fase 3 — Objetivos",
    "defn": {
      "schema_version": 1,
      "id": "test_fase3",
      "name": "Teste Fase 3 — Objetivos",
      "grid": {
        "w": 16,
        "h": 12
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          2,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 5,
          "h": 4,
          "role": "entrance",
          "locked": false,
          "doors": [
            [
              6,
              3
            ]
          ]
        },
        {
          "id": 1,
          "x": 10,
          "y": 1,
          "w": 5,
          "h": 4,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              9,
              3
            ]
          ]
        }
      ],
      "entrance": {
        "x": 3,
        "y": 2
      },
      "exit": {
        "x": 14,
        "y": 4
      },
      "monsters": [
        {
          "type": "goblin",
          "pos": [
            12,
            2
          ],
          "room_id": 1,
          "boss": false,
          "target": true
        },
        {
          "type": "skeleton",
          "pos": [
            13,
            3
          ],
          "room_id": 1,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            11,
            4
          ],
          "gold": 20,
          "items": [
            {
              "id": "health_potion"
            }
          ],
          "key_objective": true
        }
      ],
      "traps": [],
      "prisoner": {
        "pos": [
          14,
          1
        ],
        "room_id": 1
      },
      "objectives": {
        "primary": {
          "type": "rescue_prisoner"
        },
        "secondary": [
          {
            "type": "kill_all"
          },
          {
            "type": "open_key_chest"
          }
        ]
      }
    }
  },
  {
    "file": "teste_arvore.json",
    "id": "teste_arvore",
    "name": "Teste Arvore",
    "defn": {
      "schema_version": 1,
      "id": "teste_arvore",
      "name": "Teste Arvore",
      "grid": {
        "w": 8,
        "h": 6
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          2,
          1,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 1,
          "y": 1,
          "w": 4,
          "h": 4,
          "role": "entrance",
          "locked": false,
          "doors": [
            [
              5,
              2
            ]
          ]
        }
      ],
      "entrance": {
        "x": 1,
        "y": 3
      },
      "exit": {
        "x": 6,
        "y": 2
      },
      "monsters": [],
      "chests": [],
      "traps": [],
      "decorations": [
        {
          "type": "arvore",
          "pos": [
            2,
            1
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "arvore_cutout.png",
          "size": [
            1,
            2
          ],
          "vscale": [
            1,
            2.6
          ]
        },
        {
          "type": "arvore",
          "pos": [
            3,
            4
          ],
          "facing": [
            0,
            1
          ],
          "loot": null,
          "image": "arvore_cutout.png",
          "vscale": [
            1,
            3.2
          ]
        }
      ],
      "prisoner": null,
      "objectives": {
        "primary": {
          "type": "reach_exit",
          "xp": 0,
          "reward": {
            "gold": 0,
            "items": []
          }
        },
        "secondary": []
      }
    }
  },
  {
    "file": "teste_basico.json",
    "id": "teste_basico",
    "name": "teste_basico",
    "defn": {
      "schema_version": 1,
      "id": "teste_basico",
      "name": "teste_basico",
      "grid": {
        "w": 16,
        "h": 12
      },
      "tiles": [
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          2,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          0,
          0,
          0,
          0,
          0,
          2,
          2,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "rooms": [
        {
          "id": 0,
          "x": 9,
          "y": 0,
          "w": 7,
          "h": 6,
          "role": "monster",
          "locked": true,
          "doors": [
            [
              8,
              1
            ],
            [
              8,
              2
            ]
          ]
        },
        {
          "id": 1,
          "x": 4,
          "y": 8,
          "w": 4,
          "h": 3,
          "role": "entrance",
          "locked": false,
          "doors": []
        },
        {
          "id": 2,
          "x": 5,
          "y": 1,
          "w": 4,
          "h": 2,
          "role": "trap",
          "locked": false,
          "doors": [
            [
              8,
              1
            ],
            [
              8,
              2
            ],
            [
              5,
              3
            ],
            [
              6,
              3
            ]
          ]
        },
        {
          "id": 3,
          "x": 5,
          "y": 3,
          "w": 2,
          "h": 5,
          "role": "trap",
          "locked": false,
          "doors": [
            [
              5,
              3
            ],
            [
              6,
              3
            ]
          ]
        }
      ],
      "entrance": {
        "x": 5,
        "y": 9
      },
      "exit": {
        "x": 7,
        "y": 10
      },
      "monsters": [
        {
          "type": "goblin_dual",
          "pos": [
            11,
            2
          ],
          "room_id": 0,
          "boss": true,
          "target": true
        },
        {
          "type": "goblin_combatente",
          "pos": [
            13,
            1
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            13,
            1
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin_combatente",
          "pos": [
            11,
            4
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        },
        {
          "type": "goblin",
          "pos": [
            14,
            1
          ],
          "room_id": 0,
          "boss": false,
          "target": false
        }
      ],
      "chests": [
        {
          "pos": [
            5,
            5
          ],
          "gold": 1000,
          "items": [
            {
              "id": "escudo_p"
            },
            {
              "id": "leather"
            }
          ],
          "key_objective": false
        },
        {
          "pos": [
            6,
            4
          ],
          "gold": 20,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            7,
            8
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            15,
            0
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            7,
            8
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        },
        {
          "pos": [
            15,
            5
          ],
          "gold": 0,
          "items": [],
          "key_objective": false
        }
      ],
      "traps": [
        {
          "tipo": "armadilha_urso",
          "pos": [
            5,
            6
          ]
        },
        {
          "tipo": "fosso_envenenado",
          "pos": [
            6,
            5
          ],
          "veneno_id": "veneno_cobra_cuspidora"
        },
        {
          "tipo": "nuvem_gas",
          "pos": [
            6,
            2
          ]
        },
        {
          "tipo": "armadilha_incendiaria",
          "pos": [
            6,
            1
          ]
        }
      ],
      "prisoner": {
        "pos": [
          15,
          5
        ],
        "room_id": 0
      },
      "objectives": {
        "primary": {
          "type": "kill_target"
        },
        "secondary": [
          {
            "type": "rescue_prisoner"
          },
          {
            "type": "rescue_prisoner"
          }
        ]
      }
    }
  }
];
// GERADO por tools/export_catalog.py — não editar à mão.
