"""Dano mínimo em magias que causam metade no sucesso do teste de resistência."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, GRIMORIO, MONSTER_DEFS, make_monster, make_player


def setup():
    room = GameRoom("TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.send_to = noop
    room._broadcast_dado = noop
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    room.phase = "playing"
    return room


def successful_save(room):
    async def save(*args, **kwargs):
        return True, 20, 0, 20

    room._save_mostrado = save


def damage_roll_one(room):
    async def roll(*args, **kwargs):
        return 1

    room._rolar_dano_mostrado = roll


def record_damage(room):
    hits = []

    async def apply(target, damage, element, *args, **kwargs):
        hits.append((target["id"], damage, element))
        if "hp" in target:
            target["hp"] = max(0, target["hp"] - damage)

    room._aplicar_dano_alvo = apply
    return hits


def make_target(room, pos):
    definition = next(monster for monster in MONSTER_DEFS if monster["type"] == "urso_negro")
    target = make_monster(definition, {"id": 41, "cx": pos[0], "cy": pos[1]})
    target["pos"] = list(pos)
    target["hp"] = target["max_hp"] = 50
    room.monsters[target["id"]] = target
    return target


def make_caster(room):
    caster = make_player("caster", "Conjurador", "cleric", 1)
    caster["pos"] = [3, 3]
    room.players[caster["id"]] = caster
    return caster


async def main():
    checks = []

    # Lançamento integrado do Necromante: o próprio nível 2 determina 2d6;
    # com os dados mínimos (1+1) e save bem-sucedido, o alvo perde 1 HP.
    room = setup()
    necro_definition = next(monster for monster in MONSTER_DEFS
                            if monster["type"] == "necromante")
    necromancer = make_monster(necro_definition, {"id": 7, "cx": 5, "cy": 5})
    necromancer["pos"] = [5, 5]
    room.monsters[necromancer["id"]] = necromancer
    target = make_target(room, [7, 5])
    successful_save(room)
    save_count = 0
    real_save = room._save_mostrado

    async def count_successful_save(*args, **kwargs):
        nonlocal save_count
        save_count += 1
        return await real_save(*args, **kwargs)

    room._save_mostrado = count_successful_save
    rolls = []

    async def minimum_dice_roll(n, faces, *args, **kwargs):
        rolls.append((n, faces))
        return n  # representa o mínimo: 1 em cada dado

    room._rolar_dano_mostrado = minimum_dice_roll
    hp_before = target["hp"]
    cast = await room._necro_cast(necromancer, "bola_fogo", [7, 5])
    checks.append(("Necromante: 2d6 e save causa 1", cast
                   and rolls == [(2, 6)] and save_count == 1
                   and hp_before - target["hp"] == 1))

    # Bola de Fogo: um dano bruto de 1 e save bem-sucedido não pode virar zero.
    room = setup()
    target = make_target(room, [5, 5])
    successful_save(room)
    hits = record_damage(room)
    await room._aplicar_dano_area_fogo("caster", 5, 5, 1, 1, 12, "Bola de Fogo")
    checks.append(("Bola de Fogo", hits == [(target["id"], 1, "fogo")]))

    # Relâmpago: força o caminho sobre o alvo e o dado mínimo, mantendo o save real.
    room = setup()
    caster = make_caster(room)
    target = make_target(room, [4, 3])
    successful_save(room)
    damage_roll_one(room)
    hits = record_damage(room)
    room._caminho_relampago_detalhado = lambda *args: ([(4, 3)], [], [])
    await room._executar_relampago(caster, GRIMORIO["relampago"], {"dir": [1, 0]}, 1)
    checks.append(("Relâmpago", hits == [(target["id"], 1, "eletricidade")]))

    # Raio Divino: 1d6+nível resulta em 2; o save reduz à metade, mínimo 1.
    room = setup()
    caster = make_caster(room)
    target = make_target(room, [4, 3])
    successful_save(room)
    damage_roll_one(room)
    hp_before = target["hp"]
    await room._executar_raio_divino(
        caster, GRIMORIO["raio_divino"], {"target_id": target["id"]}, 1)
    checks.append(("Raio Divino", hp_before - target["hp"] == 1))

    for name, passed in checks:
        print(f"{'✅' if passed else '❌'} {name}: save com dano mínimo 1")
    if any(not passed for _, passed in checks):
        print(f"Detalhes dos resultados: {checks}")
    failed = [name for name, passed in checks if not passed]
    print(f"Resultado: {len(checks) - len(failed)} passaram, {len(failed)} falharam")
    return bool(failed)


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
