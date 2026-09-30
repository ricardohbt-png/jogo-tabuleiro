"""Hostilidade entre monstros configurada no Bestiário.
Roda da raiz: python tools/test_monster_hostility.py
"""
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def make_room():
    room = S.GameRoom("HOSTILITY")
    room.round_num = 4
    room.tiles = [[S.FLOOR for _ in range(12)] for _ in range(12)]
    room.rooms = [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "locked": False}]
    orc_def = next(m for m in S.MONSTER_DEFS if m["type"] == "orc")
    goblin_def = next(m for m in S.MONSTER_DEFS if m["type"] == "goblin")
    orc = S.make_monster(orc_def, {"id": 0, "cx": 3, "cy": 3})
    goblin = S.make_monster(goblin_def, {"id": 0, "cx": 6, "cy": 3})
    orc["pos"] = [3, 3]
    goblin["pos"] = [6, 3]
    room.monsters = {orc["id"]: orc, goblin["id"]: goblin}
    room._alvos_visiveis_para_monstro = lambda _m, targets: targets
    return room, orc, goblin


def secao_config():
    print("\n[1] Validação e combinação OU do Bestiário")
    config = {
        "orc": {"all_monsters": False, "subtypes": ["morto_vivo"], "types": ["goblin"]},
        "goblin": {"all_monsters": True, "subtypes": [], "types": []},
    }
    ok, normalized = S._validate_monster_hostility(config)
    check("aceita seleções de subtipo e tipo pelo id", ok and normalized == config)
    room, orc, goblin = make_room()
    legacy_attacks = room._monster_hostility_attacks(orc)
    check("fichas legadas sem lista de ataques mantêm o ataque básico",
          len(legacy_attacks) == 1 and legacy_attacks[0]["damage"] == orc["damage"])
    S.MONSTER_HOSTILITY = {"orc": config["orc"]}
    check("a criatura escolhida pelo nome é hostil", room._monster_hostility_matches(orc, goblin))
    undead = dict(goblin, type="esqueleto_humano", subtipo="morto_vivo")
    check("o subtipo selecionado também ativa a hostilidade", room._monster_hostility_matches(orc, undead))
    animal = dict(goblin, type="lobo_cinzento", subtipo="animal")
    check("alvos fora dos filtros não são hostis", not room._monster_hostility_matches(orc, animal))
    check("recusa ids de criatura desconhecidos", not S._validate_monster_hostility({
        "orc": {"all_monsters": False, "subtypes": [], "types": ["criatura_inexistente"]}})[0])
    S.MONSTER_HOSTILITY = {}


def secao_override_por_instancia():
    print("\n[2] Hostilidade por colocação na masmorra")
    room, orc, goblin = make_room()
    bestiary_rule = {"all_monsters": True, "subtypes": [], "types": []}
    S.MONSTER_HOSTILITY = {"orc": bestiary_rule}
    check("override none desativa a regra herdada",
          S._validate_monster_hostility_override("orc", {"mode": "none"})
          == (True, {"mode": "none"}))
    check("override custom aceita filtros desta colocação",
          S._validate_monster_hostility_override("orc", {
              "mode": "custom", "rules": {
                  "all_monsters": False, "subtypes": [], "types": ["goblin"]
              }
          }) == (True, {"mode": "custom", "rules": {
              "all_monsters": False, "subtypes": [], "types": ["goblin"]
          }}))
    check("override custom recusa tipo inexistente",
          not S._validate_monster_hostility_override("orc", {
              "mode": "custom", "rules": {
                  "all_monsters": False, "subtypes": [], "types": ["nao_existe"]
              }
          })[0])
    check("sem override, a colocação herda a hostilidade do Bestiário",
          room._monster_hostility_matches(orc, goblin))
    orc["hostility_override"] = {"mode": "none"}
    check("none afeta apenas a colocação que carrega o override",
          not room._monster_hostility_matches(orc, goblin))
    orc["hostility_override"] = {"mode": "custom", "rules": {
        "all_monsters": False, "subtypes": [], "types": ["goblin"]
    }}
    check("custom restringe a hostilidade ao alvo escolhido",
          room._monster_hostility_matches(orc, goblin)
          and not room._monster_hostility_matches(orc, dict(goblin, type="lobo_cinzento")))
    S.MONSTER_HOSTILITY = {}


def secao_persistencia():
    print("\n[3] Persistência isolada")
    original_path = S.MONSTER_HOSTILITY_FILE
    original_config = S.MONSTER_HOSTILITY
    try:
        with tempfile.TemporaryDirectory() as tmp:
            S.MONSTER_HOSTILITY_FILE = os.path.join(tmp, "monster_hostility.json")
            ok, saved = S._save_monster_hostility({
                "orc": {"all_monsters": True, "subtypes": [], "types": []}})
            check("salva configuração validada", ok and saved["orc"]["all_monsters"])
            check("arquivo pode ser recarregado", S._read_monster_hostility() == saved)
            check("configuração ativa é atualizada", S.MONSTER_HOSTILITY == saved)
    finally:
        S.MONSTER_HOSTILITY_FILE = original_path
        S.MONSTER_HOSTILITY = original_config


def secao_retaliacao():
    print("\n[4] Retaliação e turno de combate")
    room, orc, goblin = make_room()
    check("ataque direto registra o agressor", room._monster_register_retaliation(orc, goblin)
          and goblin["_monster_retaliation"]["target_id"] == orc["id"])
    check("retaliação dura até três rodadas", goblin["_monster_retaliation"]["until_round"] == 7)
    check("memória só aponta para agressor vivo e na sala", room._monster_retaliation_target(goblin) is orc)

    executed = []
    async def execute(_monster, target_obj):
        executed.append(target_obj["obj"])
    room._monster_execute_attacks = execute
    room._monster_attack_in_range = lambda *_args: True
    import asyncio
    did_act = asyncio.run(room._monster_try_hostility_turn(goblin, []))
    check("alvo de retaliação é escolhido mesmo sem regra geral", did_act and executed == [orc])

    room.round_num = 7
    check("retaliação expira após três rodadas", room._monster_retaliation_target(goblin) is None
          and "_monster_retaliation" not in goblin)
    room._monster_register_retaliation(orc, goblin)
    orc["hp"] = 0
    check("monstro morto não permanece como alvo de retaliação",
          room._monster_retaliation_target(goblin) is None)


def secao_turno_autonomo():
    print("\n[5] Turno automático sem heróis no tabuleiro")
    room, orc, goblin = make_room()
    S.MONSTER_HOSTILITY = {"goblin": {"all_monsters": True, "subtypes": [], "types": []}}
    acted = []

    async def noop(*_args, **_kwargs):
        pass

    async def upkeep(*_args, **_kwargs):
        return True

    async def execute(_monster, target_obj):
        acted.append(target_obj["obj"])

    room.gm_say = noop
    room.broadcast = noop
    room._testar_rodamoinho_profundo_inicio_turno = noop
    room._testar_rodamoinho_inicio_turno = noop
    room._upkeep_inicio_turno_monstro = upkeep
    room._monstro_ativo_em_combate = lambda _m: True
    room._encerrar_ultimo_esforco_monstro_turno = noop
    room._monster_attack_in_range = lambda *_args: True
    room._monster_execute_attacks = execute
    import asyncio
    asyncio.run(room.gm_phase(only_monster=goblin))
    check("a fase individual encontra o alvo fora da lista de iniciativa", acted == [orc])
    S.MONSTER_HOSTILITY = {}


if __name__ == "__main__":
    secao_config()
    secao_override_por_instancia()
    secao_persistencia()
    secao_retaliacao()
    secao_turno_autonomo()
    print(f"\nResultado: {PASS} passaram; {FAIL} falharam.")
    raise SystemExit(1 if FAIL else 0)
