"""Testes do encerramento antecipado das zonas mágicas persistentes.

Roda da raiz: python -X utf8 tools/test_encerrar_magias_zona.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup(classe="cleric"):
    room = S.GameRoom("TEST")
    events = []

    async def noop(*args, **kwargs):
        return None

    async def broadcast(msg, *args, **kwargs):
        events.append(msg)

    room.broadcast = broadcast
    room.push_state = noop
    room.gm_say = noop
    room.send_to = noop
    room.phase = "playing"
    room.round_num = 2
    room.players["c"] = S.make_player("c", "Caster", classe, 0)
    room.players["c"].update(pos=[1, 1], alive=True, level=5)
    room.player_order = ["c"]
    room.initiative_active = True
    room._rebuild_initiative()
    room.events = events
    room.decorations = []
    room._rebuild_decor_index()
    room.materiais = {}
    room._rebuild_materiais_index()
    return room


async def main():
    room = setup()
    base = (4, 4)
    room.materiais[base] = "pedra_cinza"
    room._aplicar_camadas_terreno_inverno([[4, 4]], "piso_congelado", "winter-1", expira_em=9)
    winter = {"id": "winter-1", "tipo": "chamado_inverno", "caster": "c",
              "ativa": True, "permanente": False, "tiles": [[4, 4]]}
    room.zonas_especiais = [winter]
    await room.handle_encerrar_magia_zona("c", "winter-1")
    check("Chamado temporário restaura o terreno-base imediatamente",
          not winter["ativa"] and room.materiais.get(base) == "pedra_cinza"
          and base not in room._terrenos_inverno)

    permanent = {"id": "winter-perm", "tipo": "chamado_inverno", "caster": "c",
                 "ativa": True, "permanente": True, "tiles": [[4, 4]]}
    room.zonas_especiais = [permanent]
    room.materiais[base] = "planicie_nevada"
    await room.handle_encerrar_magia_zona("c", "winter-perm")
    check("Chamado permanente não é encerrado pelo comando temporário",
          permanent["ativa"] and room.materiais.get(base) == "planicie_nevada")

    water = {"id": "water-1", "tipo": "senhor_das_aguas", "caster": "c",
             "ativa": True, "tiles": [[4, 4]], "redemoinhos": [[4, 4]]}
    room.zonas_especiais = [water]
    room._aplicar_camadas_terreno_inverno([[4, 4]], "agua", "water-1", expira_em=9)
    room._aplicar_camadas_terreno_inverno([[4, 4]], "rodamoinho", "water-1", expira_em=9)
    room.players["c"].update(pos=[4, 4], rodamoinho_preso=True,
                              _rodamoinho_bloqueado_turno=True)
    await room.handle_encerrar_magia_zona("c", "water-1")
    check("Senhor das Águas remove redemoinho, restaura terreno e libera criatura",
          not water["ativa"] and room.materiais.get(base) == "planicie_nevada"
          and not room.players["c"].get("rodamoinho_preso")
          and not room.players["c"].get("_rodamoinho_bloqueado_turno"))

    lava = {"id": "lava-1", "tipo": "ira_rocha_ardente", "caster": "c",
            "ativa": True, "tiles": [[4, 4]]}
    room.zonas_especiais = [lava]
    room._aplicar_camadas_terreno_inverno([[4, 4]], "lava", "lava-1", expira_em=9)
    room.decorations = [{"id": "lava-1-flame", "type": "chama_viva",
                         "pos": [4, 4], "ira_rocha_ardente_id": "lava-1"}]
    room._rebuild_decor_index()
    await room.handle_encerrar_magia_zona("c", "lava-1")
    check("Ira da Rocha remove lava e Chamas Vivas vinculadas",
          not lava["ativa"] and room.materiais.get(base) == "planicie_nevada"
          and not room.decorations)

    storm = {"id": "storm-1", "tipo": "tempestade_ciclones", "caster": "c",
             "ativa": True, "ciclones": [{"id": 1, "pos": [4, 4]}]}
    room.zonas_especiais = [storm]
    room.players["c"]["tempestade_ciclones_presos"] = {"storm-1": 1, "storm-other": 2}
    await room.handle_encerrar_magia_zona("c", "storm-1")
    check("Tempestade limpa somente seu vínculo de prisão e manda dissipar",
          not storm["ativa"] and room.players["c"].get("tempestade_ciclones_presos") == {"storm-other": 2}
          and any(e.get("spell_id") == "tempestade_ciclones" and e.get("phase") == "expire"
                  and e.get("animation_id") == "storm-1" for e in room.events))

    pending = {"id": "storm-pending", "tipo": "tempestade_ciclones", "caster": "c",
               "ativa": True, "ciclones_pendentes": 2}
    room.zonas_especiais = [pending]
    await room.handle_encerrar_magia_zona("c", "storm-pending")
    check("Tempestade não pode ser encerrada antes da confirmação dos ciclones",
          pending["ativa"])

    room = setup("mage")
    foreign = {"id": "foreign", "tipo": "senhor_das_aguas", "caster": "other", "ativa": True}
    room.zonas_especiais = [foreign]
    await room.handle_encerrar_magia_zona("c", "foreign")
    check("não encerra zona de outro conjurador nem fora da classe permitida",
          foreign["ativa"])

    room = setup("mage")
    fire_wall = {"id": "fire-1", "tipo": "prisao_chamas", "caster": "c", "ativa": True}
    room.zonas_especiais = [fire_wall]
    await room.handle_encerrar_magia_zona("c", "fire-1")
    check("Prisão de Chamas também usa o encerramento por ID",
          not fire_wall["ativa"])

    room = setup("mage")
    legacy_fire_wall = {"id": "fire-legacy", "tipo": "prisao_chamas", "caster": "c", "ativa": True}
    room.zonas_especiais = [legacy_fire_wall]
    await room.handle_encerrar_prisao_chamas("c")
    check("comando antigo da Prisão continua compatível",
          not legacy_fire_wall["ativa"])

    print(f"\nResultado: {PASS} passou, {FAIL} falhou")
    return FAIL == 0


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(main()) else 1)
