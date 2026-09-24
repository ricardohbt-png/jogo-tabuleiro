"""Regressão do Redemoinho Profundo e do popup de afogamento.
Roda da raiz: python tools/test_afogamento.py"""
import asyncio
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print("OK:", label)
    else:
        FAIL += 1
        print("FAIL:", label)


async def main():
    print("\n[1] Entrada do redemoinho profundo usa Reflexos CD 15")
    room = object.__new__(S.GameRoom)
    room._voo_imune_terreno = lambda _creature: False
    room._ignora_rodamoinho_profundo = lambda _creature: False
    room._rodamoinho_profundo_tiles_of = lambda _creature: [(2, 2)]
    room.gm_say = lambda *_args, **_kwargs: asyncio.sleep(0)
    saves = []

    async def save_entry(_creature, save, dc):
        saves.append((save, dc))
        return True, 20, 0, 20

    room._save_mostrado = save_entry
    entry_popups = []

    async def capture_entry_popup(*args, **kwargs):
        entry_popups.append((args, kwargs))

    room._enviar_trap_result = capture_entry_popup
    creature = {
        "id": "p1", "hp": 20, "pos": [2, 2],
        "_rodamoinho_profundo_ultima_pos": [1, 2],
    }
    await S.GameRoom._aplicar_rodamoinho_profundo_se_pisar(room, creature)
    check("save de entrada é Reflexos", saves == [("reflexos", 15)])

    async def fail_entry(_creature, save, dc):
        saves.append((save, dc))
        return False, 1, 0, 1

    room._save_mostrado = fail_entry
    creature["_rodamoinho_profundo_ultima_pos"] = [1, 2]
    await S.GameRoom._aplicar_rodamoinho_profundo_se_pisar(room, creature)
    check("captura envia popup de redemoinho profundo", entry_popups[-1][1].get("tipo_id") == "rodamoinho_profundo")
    check("popup de captura vem antes do afogamento", not entry_popups[-1][1].get("tipo_id") == "afogamento")

    room._ignora_rodamoinho = lambda _creature: False
    room._rodamoinho_tiles_of = lambda _creature: [(2, 2)]
    room._save_mostrado = fail_entry
    creature.pop("rodamoinho_profundo_preso", None)
    creature.pop("_rodamoinho_profundo_bloqueado_turno", None)
    creature["_rodamoinho_ultima_pos"] = [1, 2]
    await S.GameRoom._aplicar_rodamoinho_se_pisar(room, creature)
    check("captura envia popup de redemoinho normal", entry_popups[-1][1].get("tipo_id") == "rodamoinho")

    print("\n[2] Dano de afogamento envia trap_result com arte própria")
    room = object.__new__(S.GameRoom)
    room.round_num = 1
    room.players = {"p1": creature}
    room.monsters = {}
    room.prisoner = None
    room._ignora_rodamoinho_profundo = lambda _creature: False
    # O cenário representa a criatura ainda presa em um redemoinho ativo;
    # sem tiles, o código atual corretamente a libera sem afogamento.
    room._rodamoinho_profundo_tiles_of = lambda _creature: [(2, 2)]
    room._imune_afogamento = lambda _creature: False
    room._save_mostrado = lambda *_args, **_kwargs: asyncio.sleep(0)
    saves = iter([(False, 1, 0, 1), (False, 1, 0, 1)])

    async def save_damage(*_args, **_kwargs):
        return next(saves)

    room._save_mostrado = save_damage
    room.broadcast = lambda *_args, **_kwargs: asyncio.sleep(0)
    room.gm_say = lambda *_args, **_kwargs: asyncio.sleep(0)
    popup = []

    async def capture_popup(*args, **kwargs):
        popup.append((args, kwargs))

    room._enviar_trap_result = capture_popup
    creature.update({
        "name": "Herói", "hp": 20, "fome": 5, "sede": 5,
        "rodamoinho_profundo_preso": True,
    })
    with patch.object(S, "roll_dice", return_value=4):
        await S.GameRoom._testar_rodamoinho_profundo_inicio_turno(room, creature)
    check("sofreu 1d6 de afogamento", creature["hp"] == 16)
    check("perdeu fome e sede", creature["fome"] == 4 and creature["sede"] == 4)
    check("popup enviado", len(popup) == 1)
    if popup:
        args, kwargs = popup[0]
        check("tipo_id do popup", kwargs.get("tipo_id") == "afogamento")
        check("imagem e dano no payload", kwargs.get("dano") == 4 and kwargs.get("tick") is True)
        check("CD de dano no payload", kwargs.get("fortitude_dc") == 18)

    print(f"\n{PASS} passaram, {FAIL} falharam")
    return 1 if FAIL else 0


sys.exit(asyncio.run(main()))
