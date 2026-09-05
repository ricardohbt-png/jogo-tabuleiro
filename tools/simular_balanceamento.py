"""Simulador pequeno e reproduzível para o balanceamento da IA dos monstros.

O simulador usa as definições reais de ``server.py`` e executa ``gm_phase``
para que movimento, escolha de alvo, ataques, venenos, controle e Olhar
Petrificante sejam avaliados pelo mesmo motor da partida.

O diagnóstico oferece dois modos: ``basico`` (um ataque básico por rodada) e
``habilidades`` (uma política simples que usa as habilidades disponíveis do
guerreiro, mago, clérigo e ladino). A segunda política não tenta jogar como um
humano perfeito; ela serve para medir o ganho real da cooperação. O script não
altera fichas, ND ou arquivos do jogo.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import server as S


HERO_CLASSES = ("warrior", "mage", "cleric", "rogue")
SIMULATION_MODES = ("basico", "habilidades")

# Encontros de referência. Os tipos são os mesmos usados pelo catálogo
# autoritativo do servidor; a ferramenta também valida isso ao iniciar.
SCENARIOS = {
    "goblins": [
        "goblin_combatente", "goblin_combatente",
        "goblin_arqueiro", "goblin_xama",
    ],
    "kobolds": [
        "kobold_lanceiro", "kobold_lanceiro", "kobold_besteiro",
    ],
    "mortos_vivos": [
        "esqueleto_humano", "zumbi_infectado", "necromante",
    ],
    "grande_medusa": ["grande_medusa"],
    "grande_gorgona": ["grande_gorgona"],
}

# Encontros mistos de teste: aqui o orçamento é a SOMA direta dos NDs. Não
# recebem a multiplicação usada na tabela de encontros fracionários, porque a
# intenção é comparar composições com teto explícito de ND 1,5 para quatro
# heróis de nível 1.
MIXED_SCENARIOS = {
    "patrulha_mista": [
        "goblin_combatente", "goblin_combatente",
        "goblin_arqueiro", "kobold_besteiro",                 # ND 1,00
    ],
    "linha_kobold": [
        "kobold_lanceiro", "kobold_lanceiro",
        "kobold_besteiro", "aranha_sombria",                 # ND 1,00
    ],
    "guarda_esqueleto": [
        "esqueleto_humano", "goblin_combatente",
        "goblin_arqueiro", "kobold_lanceiro",                 # ND 1,25
    ],
    "xama_e_escolta": [
        "goblin_xama", "goblin_combatente", "kobold_lanceiro", # ND 1,50
    ],
    "zumbi_e_escolta": [
        "zumbi_infectado", "kobold_lanceiro", "goblin_arqueiro", # ND 1,50
    ],
    "aranha_e_esqueleto": [
        "aranha_sombria", "esqueleto_humano",
        "kobold_lanceiro", "kobold_besteiro",                  # ND 1,25
    ],
}


def _monster_defs_by_type():
    return {definition["type"]: definition for definition in S.MONSTER_DEFS}


def _scaled_encounter(monster_types, defs):
    """Expande ND fracionário e define o nível de referência do grupo.

    A regra solicitada é por criatura: ND 1/4 aparece quatro vezes e ND 1/2
    aparece duas vezes. Para encontros mistos, o nível dos heróis acompanha o
    maior ND do encontro, com nível mínimo 1.
    """
    expanded = []
    multipliers = {}
    nds = []
    for monster_type in monster_types:
        nd = float(S.monster_cr(defs[monster_type]))
        nds.append(nd)
        if nd <= 0.25:
            multiplier = 4
        elif nd <= 0.5:
            multiplier = 2
        else:
            multiplier = 1
        multipliers[monster_type] = multiplier
        expanded.extend([monster_type] * multiplier)
    hero_level = max(1, int(math.ceil(max(nds, default=1))))
    return expanded, hero_level, multipliers, max(nds, default=1), sum(nds)


def _new_room(width=24, height=24):
    """Monta uma sala plana e aberta, adequada para o teste de combate."""
    room = S.GameRoom("SIMULACAO")
    room.phase = "playing"
    room.map_w = width
    room.map_h = height
    room.tiles = [[S.FLOOR for _ in range(width)] for _ in range(height)]
    room.rooms = [{
        "id": 1, "x": 0, "y": 0, "w": width, "h": height,
        "cx": width // 2, "cy": height // 2, "locked": False,
        "doors": [],
    }]
    room.explored = {(x, y) for y in range(height) for x in range(width)}
    room.dungeon_generated = True
    room.selected_dungeon = None
    room.dungeon_def = None
    room.master_pid = None
    room.connections = {}
    return room


async def _noop(*_args, **_kwargs):
    """Evita rede/cliente sem substituir a lógica do combate."""


def _install_simulation_hooks(room):
    # O motor continua resolvendo todos os efeitos; só silenciamos o transporte.
    room.broadcast = _noop
    room.send_to = _noop
    room.gm_say = _noop
    room.push_state = _noop
    # A partida real aguarda a interpolação visual de cada passo; o diagnóstico
    # mede regras e decisões, então remove somente essa espera de apresentação.
    room._emit_entity_step = _noop

    async def simulation_player_dies(pid):
        player = room.players.get(pid)
        if player:
            player["alive"] = False
            player["hp"] = 0

    room._player_dies = simulation_player_dies


def _occupied_by_living_entity(room, pos, own_id=None):
    for player in room.players.values():
        if player.get("id") != own_id and player.get("alive") and player.get("pos") == list(pos):
            return True
    for monster in room.monsters.values():
        if monster.get("id") != own_id and monster.get("hp", 0) > 0 \
                and list(monster.get("pos", [])) == list(pos):
            return True
    return False


def _hero_step_toward(room, hero, target):
    """Move uma casa cardinal em direção ao monstro mais próximo."""
    hx, hy = hero["pos"]
    tx, ty = target["pos"]
    dx = 0 if hx == tx else (1 if tx > hx else -1)
    dy = 0 if hy == ty else (1 if ty > hy else -1)
    candidates = [(dx, 0), (0, dy), (0, -dy), (-dx, 0)]
    for sx, sy in candidates:
        if not (sx or sy):
            continue
        nx, ny = hx + sx, hy + sy
        if not (0 <= nx < room.map_w and 0 <= ny < room.map_h):
            continue
        if room._blocks_tile(nx, ny) or _occupied_by_living_entity(room, [nx, ny], hero["id"]):
            continue
        hero["pos"] = [nx, ny]
        return True
    return False


def _distance_to_monster(hero, monster):
    hx, hy = hero["pos"]
    return min(max(abs(hx - x), abs(hy - y))
               for x, y in monster_tiles_fallback(monster))


def monster_tiles_fallback(monster):
    """Footprint suficiente para escolher alvos sem duplicar regras do motor."""
    x, y = monster.get("pos", [0, 0])
    size = monster.get("size", [1, 1])
    try:
        width, height = max(1, int(size[0])), max(1, int(size[1]))
    except (TypeError, ValueError, IndexError):
        width, height = 1, 1
    return [(x + ox, y + oy) for oy in range(height) for ox in range(width)]


def _nearest_living_monster(room, hero):
    monsters = [m for m in room.monsters.values() if m.get("hp", 0) > 0]
    return min(monsters, key=lambda m: (_distance_to_monster(hero, m), str(m.get("id", ""))),
               default=None)


def _hero_can_attack(room, hero, monster):
    # A linha de base usa apenas ataques corpo a corpo. O cajado conserva o
    # alcance adjacente do jogo, inclusive para casas diagonais.
    return room._is_adjacent_to_monster(hero["pos"], monster)


def _hero_basic_attack(room, hero, monster, metrics=None):
    weapon = hero.get("weapon") or {}
    attack_bonus = (S._hero_attack_bonus_with_weapon(hero, weapon)
                    + int(hero.get("skill_bonus_acerto", 0) or 0))
    hit, roll, _total, critical = S.d20_attack(attack_bonus, int(monster.get("ac", 10)))
    if not hit:
        return 0
    sneak_damage = 0
    if hero.get("class_id") == "rogue" and room._verificar_ataque_furtivo(hero, monster):
        sneak_damage = S.roll_dice(f"{room._dados_furtivo(hero.get('level', 1))}d4")
    damage, _name, _detail, _raw, _die = room._resolver_dano_ataque_basico(
        hero, monster, critical, roll, target_pos=monster.get("pos"),
        bonus_extra=sneak_damage, attacker_id=hero.get("id"))
    monster["hp"] = max(0, int(monster.get("hp", 0)) - max(0, int(damage)))
    if metrics is not None:
        metrics["sneak_damage"] += sneak_damage
    return max(0, int(damage))


async def _hero_use_mage_spell(room, hero, target, metrics):
    """Usa o Raio Congelante real do grimório, sem passar pela rede."""
    magia = S.GRIMORIO["raio_congelante"]
    if max(abs(hero["pos"][0] - target["pos"][0]),
           abs(hero["pos"][1] - target["pos"][1])) > magia.get("alcance_base", 3):
        return False
    if not room._tem_linha_de_visao(hero["pos"], target["pos"]):
        return False
    hp_before = target.get("hp", 0)
    await room._executar_magia_grimorio(hero, magia, {"target_id": target["id"]})
    if target.get("hp", 0) < hp_before:
        metrics["spells"] += 1
        return True
    return False


def _hero_heal_lowest(room, cleric, metrics):
    """Cura individual com os mesmos valores-base de handle_cura."""
    allies = [p for p in room.players.values()
              if p.get("alive") and p.get("hp", 0) < p.get("max_hp", 0)]
    if not allies:
        return False
    target = min(allies, key=lambda p: p.get("hp", 0) / max(1, p.get("max_hp", 1)))
    if max(abs(cleric["pos"][0] - target["pos"][0]),
           abs(cleric["pos"][1] - target["pos"][1])) > 7:
        return False
    cura = max(1, S.roll_dice("1d8") + S.mod(cleric.get("int_", 10)))
    real = room._curar_hp(target, cura, "Cura")
    if real <= 0:
        return False
    metrics["healing"] += real
    metrics["skills"] += 1
    return True


def _arm_warrior_skill(room, hero, target, metrics):
    """Escolhe uma única habilidade armada, como no teto base do guerreiro."""
    living = sum(1 for m in room.monsters.values() if m.get("hp", 0) > 0)
    if living > 1:
        hero["skill_ataques_extras"] = 1
        metrics["skills"] += 1
        return "furia"
    if target.get("ac", 10) >= 14:
        hero["skill_bonus_acerto"] = 2
        metrics["skills"] += 1
        return "mira"
    hero["skill_dobrar_dano"] = True
    metrics["skills"] += 1
    return "golpe"


async def _hero_turn(room, hero, mode, metrics):
    """Executa uma política de herói deliberadamente simples e auditável."""
    if not room._ativo(hero) or hero.get("petrificado"):
        return
    await room._processar_olhar_petrificante_inicio(hero)
    if not room._ativo(hero) or hero.get("petrificado"):
        return
    target = _nearest_living_monster(room, hero)
    if not target:
        return
    if not _hero_can_attack(room, hero, target):
        _hero_step_toward(room, hero, target)
    if not room._ativo(hero):
        return

    # O mago lança uma magia de alvo quando a posição permite; caso contrário
    # cai para o ataque básico. Isso mede uma decisão útil sem pressupor que ele
    # conheça ou gaste todas as magias do jogo.
    if mode == "habilidades" and hero.get("class_id") == "mage":
        if await _hero_use_mage_spell(room, hero, target, metrics):
            return

    # Cura ocupa a ação principal. O clérigo só a usa quando há um aliado
    # ferido; assim a política não transforma o grupo em um esquadrão de cura.
    if mode == "habilidades" and hero.get("class_id") == "cleric":
        if _hero_heal_lowest(room, hero, metrics):
            return

    if mode == "habilidades" and hero.get("class_id") == "warrior":
        _arm_warrior_skill(room, hero, target, metrics)
    elif mode == "habilidades" and hero.get("class_id") == "rogue":
        # Esconder nas Sombras é ação bônus e permite atacar na mesma rodada.
        hero["invisivel_sombras"] = True
        metrics["skills"] += 1

    if _hero_can_attack(room, hero, target):
        _hero_basic_attack(room, hero, target, metrics)
        if hero.get("class_id") == "warrior" and hero.get("skill_ataques_extras", 0) > 0 \
                and target.get("hp", 0) > 0:
            hero["skill_ataques_extras"] -= 1
            metrics["extra_attacks"] += 1
            _hero_basic_attack(room, hero, target, metrics)

    # Flags de habilidade são de turno, exatamente como no servidor.
    for key, value in (("skill_bonus_acerto", 0), ("skill_bonus_dano", 0),
                       ("skill_dobrar_dano", False), ("skill_ataques_extras", 0),
                       ("invisivel_sombras", False)):
        hero[key] = value


def _scale_player_level(player, level):
    """Aplica a progressão autoritativa até o nível do encontro."""
    level = max(1, int(level))
    regra = S.LEVEL_PROGRESSAO[player["class_id"]]
    for current_level in range(2, level + 1):
        ganho_hp = regra["hp"] + S.get_bonus_constituicao(player["con_"])
        player["max_hp"] += ganho_hp
        player["hp"] = player["max_hp"]
        player["atk_bonus"] += 1
        player["base_atk_bonus"] += 1
        if current_level >= 3 and current_level % 2 == 1:
            for save in regra["saves_2"]:
                player[save] += 1
        if current_level >= 4 and (current_level - 1) % 3 == 0:
            for save in regra["saves_3"]:
                player[save] += 1
        player["fome_max_base"] += regra["fome"]
        player["sede_max_base"] += regra["sede"]
    player["level"] = level
    player["level_bonus"] = level
    S._recalcular_maximos_sobrevivencia(player)
    player["fome"] = player["fome_max"]
    player["sede"] = player["sede_max"]


def _place_party(room, level):
    center = room.map_h // 2
    positions = ([2, center - 1], [2, center], [3, center - 1], [3, center])
    for index, class_id in enumerate(HERO_CLASSES):
        player = S.make_player(f"hero_{index}", class_id.title(), class_id, index)
        _scale_player_level(player, level)
        player["pos"] = list(positions[index])
        player["connected"] = True
        player["fora_masmorra"] = False
        player["alive"] = True
        room.players[player["id"]] = player
    room.player_order = list(room.players)


def _place_monsters(room, monster_types, defs):
    # Os encontros escalados podem ter até 16 criaturas. A formação em duas
    # colunas mantém uma casa livre por criatura e deixa a IA formar o cerco.
    center = room.map_h // 2
    positions = []
    for index in range(len(monster_types)):
        column, row = divmod(index, 8)
        positions.append([room.map_w - 5 - column * 2, center - 4 + row])
    for index, monster_type in enumerate(monster_types):
        monster = S.make_monster(defs[monster_type], room.rooms[0])
        monster["pos"] = list(positions[index])
        monster["room_id"] = 1
        room.monsters[monster["id"]] = monster


async def _run_one(monster_types, seed, max_rounds, mode, hero_level):
    random.seed(seed)
    room = _new_room()
    _install_simulation_hooks(room)
    defs = _monster_defs_by_type()
    _place_party(room, hero_level)
    _place_monsters(room, monster_types, defs)

    damage_taken_total = 0
    retreat_count = 0
    petrified_count = 0
    boss_phase_seen = False
    metrics = Counter({"skills": 0, "spells": 0, "healing": 0,
                       "sneak_damage": 0, "extra_attacks": 0})
    rounds = 0

    for rounds in range(1, max_rounds + 1):
        room.round_num = rounds
        alive_heroes = [p for p in room.players.values() if room._ativo(p)]
        alive_monsters = [m for m in room.monsters.values() if m.get("hp", 0) > 0]
        if not alive_heroes or not alive_monsters:
            break

        # O olhar e as ações passam pelo mesmo fluxo de estado usado em jogo;
        # apenas a ordem de iniciativa foi reduzida a uma rodada controlada.
        for hero in list(alive_heroes):
            await _hero_turn(room, hero, mode, metrics)

        if not any(m.get("hp", 0) > 0 for m in room.monsters.values()):
            break
        if not any(room._ativo(p) for p in room.players.values()):
            break

        hp_before = sum(max(0, int(p.get("hp", 0))) for p in room.players.values())
        retreat_before = sum(1 for m in room.monsters.values() if m.get("ai_retreat_round") == rounds)
        await room.gm_phase()
        hp_after = sum(max(0, int(p.get("hp", 0))) for p in room.players.values())
        # A cura entre duas fases não pode virar "dano negativo" no relatório.
        damage_taken_total += max(0, hp_before - hp_after)
        retreat_after = sum(1 for m in room.monsters.values() if m.get("ai_retreat_round") == rounds)
        retreat_count += max(0, retreat_after - retreat_before)
        boss_phase_seen = boss_phase_seen or any(m.get("ai_boss_phase", 1) >= 2
                                                 for m in room.monsters.values())
        petrified_count = sum(1 for p in room.players.values() if p.get("petrificado"))

    survivors = sum(1 for p in room.players.values() if room._ativo(p))
    hero_deaths = sum(1 for p in room.players.values() if not p.get("alive"))
    party_wipe = survivors == 0
    monsters_remaining = sum(1 for m in room.monsters.values() if m.get("hp", 0) > 0)
    if monsters_remaining == 0:
        outcome = "herois_vencem"
    elif party_wipe:
        outcome = "grupo_derrotado"
    else:
        outcome = "limite_de_rodadas"
    return {
        "outcome": outcome,
        "rounds": rounds,
        "damage_taken": damage_taken_total,
        "hero_deaths": hero_deaths,
        "survivors": survivors,
        "monsters_remaining": monsters_remaining,
        "petrified": petrified_count,
        "retreats": retreat_count,
        "boss_phase_seen": boss_phase_seen,
        "skills": metrics["skills"],
        "spells": metrics["spells"],
        "healing": metrics["healing"],
        "sneak_damage": metrics["sneak_damage"],
        "extra_attacks": metrics["extra_attacks"],
    }


async def simulate(runs, seed, max_rounds, modes=None, scenarios=None,
                   scale_fractional=True, hero_level_override=None):
    scenarios = scenarios or SCENARIOS
    defs = _monster_defs_by_type()
    missing = sorted({t for encounter in scenarios.values() for t in encounter if t not in defs})
    if missing:
        raise RuntimeError(f"Tipos ausentes no catálogo do servidor: {', '.join(missing)}")

    reports = {}
    modes = tuple(modes or SIMULATION_MODES)
    invalid_modes = sorted(set(modes) - set(SIMULATION_MODES))
    if invalid_modes:
        raise ValueError(f"Modo(s) inválido(s): {', '.join(invalid_modes)}")
    for mode in modes:
        for name, monster_types in scenarios.items():
            if scale_fractional:
                expanded_types, hero_level, multipliers, encounter_nd, nd_total = _scaled_encounter(monster_types, defs)
            else:
                expanded_types = list(monster_types)
                nd_values = [float(S.monster_cr(defs[t])) for t in monster_types]
                encounter_nd = max(nd_values, default=1)
                nd_total = sum(nd_values)
                hero_level = max(1, int(hero_level_override or math.ceil(encounter_nd)))
                multipliers = {t: 1 for t in dict.fromkeys(monster_types)}
            results = [await _run_one(expanded_types, seed + index, max_rounds, mode, hero_level)
                       for index in range(runs)]
            key = f"{name}:{mode}"
            outcomes = Counter(row["outcome"] for row in results)
            reports[key] = {
                "encontro": name,
                "modo": mode,
                "monstros": monster_types,
                "monstros_apos_escala": expanded_types,
                "multiplicadores_nd": multipliers,
                "nd_maximo": encounter_nd,
                "nd_total": nd_total,
                "nivel_herois": hero_level,
                "vitorias_herois_pct": round(100 * outcomes["herois_vencem"] / runs, 1),
                "derrotas_grupo_pct": round(100 * outcomes["grupo_derrotado"] / runs, 1),
                "limite_pct": round(100 * outcomes["limite_de_rodadas"] / runs, 1),
                "rodadas_medias": round(sum(r["rounds"] for r in results) / runs, 2),
                "dano_medio_herois": round(sum(r["damage_taken"] for r in results) / runs, 2),
                "mortes_herois_medias": round(sum(r["hero_deaths"] for r in results) / runs, 2),
                "sobreviventes_medios": round(sum(r["survivors"] for r in results) / runs, 2),
                "monstros_restantes_medios": round(sum(r["monsters_remaining"] for r in results) / runs, 2),
                "petrificados_medios": round(sum(r["petrified"] for r in results) / runs, 2),
                "recuos_medios": round(sum(r["retreats"] for r in results) / runs, 2),
                "fase_2_boss_pct": round(100 * sum(r["boss_phase_seen"] for r in results) / runs, 1),
                "habilidades_medias": round(sum(r["skills"] for r in results) / runs, 2),
                "magias_medias": round(sum(r["spells"] for r in results) / runs, 2),
                "cura_media": round(sum(r["healing"] for r in results) / runs, 2),
                "dano_furtivo_medio": round(sum(r["sneak_damage"] for r in results) / runs, 2),
                "ataques_extras_medios": round(sum(r["extra_attacks"] for r in results) / runs, 2),
            }
    return reports


def _print_table(reports, runs, max_rounds):
    print(f"Simulação de balanceamento — {runs} execuções por encontro; máximo {max_rounds} rodadas")
    print("basico = ataques básicos; habilidades = política simples usando Fúria/Mira/Golpe, Raio Congelante, Cura, Esconder e Ataque Furtivo.")
    print("Os heróis usam o nível do maior ND do encontro; os encontros mistos usam a soma direta dos NDs.")
    print()
    columns = ("Encontro", "Modo", "ND total", "Nv", "Vitória", "Derrota", "Limite", "Rodadas", "Dano", "Mortes", "Sobrev.")
    print(" | ".join(f"{column:>12}" for column in columns))
    print("-" * 130)
    for _key, row in reports.items():
        print(" | ".join((
            f"{row['encontro']:>12}", f"{row['modo']:>12}", f"{row['nd_total']:>12.2f}",
            f"{row['nivel_herois']:>12}",
            f"{row['vitorias_herois_pct']:>10.1f}%",
            f"{row['derrotas_grupo_pct']:>10.1f}%", f"{row['limite_pct']:>10.1f}%",
            f"{row['rodadas_medias']:>12.2f}", f"{row['dano_medio_herois']:>12.2f}",
            f"{row['mortes_herois_medias']:>12.2f}", f"{row['sobreviventes_medios']:>12.2f}",
        )))
    print()
    print("Os dados são referência para ajuste; o script não altera ND, PV, CA ou regras.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=100, help="execuções por encontro (padrão: 100)")
    parser.add_argument("--seed", type=int, default=20260904, help="semente determinística")
    parser.add_argument("--max-rounds", type=int, default=40, help="limite de rodadas por combate")
    parser.add_argument("--mode", choices=("basico", "habilidades", "ambos"), default="ambos",
                        help="linha de simulação; padrão: ambos")
    parser.add_argument("--encounters", choices=("referencia", "mistos"), default="referencia",
                        help="conjunto de encontros; 'mistos' usa teto de ND 1,5")
    parser.add_argument("--json", action="store_true", help="imprime o relatório em JSON")
    args = parser.parse_args()
    if args.runs < 1 or args.max_rounds < 1:
        parser.error("--runs e --max-rounds devem ser positivos")
    modes = SIMULATION_MODES if args.mode == "ambos" else (args.mode,)
    if args.encounters == "mistos":
        scenarios = MIXED_SCENARIOS
        scale_fractional = False
        hero_level_override = 1
    else:
        scenarios = SCENARIOS
        scale_fractional = True
        hero_level_override = None
    reports = asyncio.run(simulate(
        args.runs, args.seed, args.max_rounds, modes=modes,
        scenarios=scenarios, scale_fractional=scale_fractional,
        hero_level_override=hero_level_override))
    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        _print_table(reports, args.runs, args.max_rounds)


if __name__ == "__main__":
    main()
