window.EDITOR_DUNGEONS = [
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
              "id": "magic_sword"
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
              "id": "shield"
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
