"""Testes da magia Ira da Rocha Ardente.

Roda da raiz:
    python -X utf8 tools/test_ira_rocha_ardente.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


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


def setup():
    room = S.GameRoom("TEST")
    messages = []

    async def noop(*args, **kwargs):
        return None

    async def send_to(pid, msg, *args, **kwargs):
        messages.append((pid, msg))

    room.broadcast = noop
    room.push_state = noop
    room.gm_say = noop
    room._broadcast_dado = noop
    room.send_to = send_to
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room._alcance_com_altura = lambda *args, **kwargs: True
    room.map_w = room.map_h = 10
    room.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    room.explored = {(x, y) for y in range(10) for x in range(10)}
    room.phase = "playing"
    room.monsters = {}
    room.decorations = []
    room._rebuild_decor_index()
    room.materiais = {}
    room._rebuild_materiais_index()
    room.round_num = 1
    return room, messages


def add_cleric(room, level=6, pos=(4, 4)):
    cleric = S.make_player("c", "Lewis", "cleric", 0)
    cleric.update(level=level, pos=list(pos), alive=True, hp=50, max_hp=50,
                  fome=40, sede=40, action_done=False)
    cleric["magias_conhecidas"] = ["ira_rocha_ardente"]
    room.players["c"] = cleric
    room.player_order = ["c"]
    room.initiative_active = True
    room._rebuild_initiative()
    return cleric


async def cast(room, messages, center=(4, 4)):
    old_roll = S.roll_dice

    def fixed_roll(expr):
        expr = str(expr)
        if expr == "1d4":
            return 3
        if expr == "2d4":
            return 4
        if expr == "2d6":
            return 7
        return old_roll(expr)

    S.roll_dice = fixed_roll
    try:
        await room.handle_magia("c", {
            "magia_id": "ira_rocha_ardente",
            "tx": center[0],
            "ty": center[1],
        })
    finally:
        S.roll_dice = old_roll
    return next(z for z in room.zonas_especiais
                if z.get("tipo") == "ira_rocha_ardente")


async def cast_dur_minima(room, messages, center=(4, 4)):
    """Lança forçando o PIOR 1d4 (=1), o caso que zerava a janela das Chamas."""
    old_roll = S.roll_dice

    def fixed_roll(expr):
        expr = str(expr)
        if expr == "1d4":
            return 1
        if expr == "2d4":
            return 4
        if expr == "2d6":
            return 7
        return old_roll(expr)

    S.roll_dice = fixed_roll
    try:
        await room.handle_magia("c", {
            "magia_id": "ira_rocha_ardente",
            "tx": center[0],
            "ty": center[1],
        })
    finally:
        S.roll_dice = old_roll
    return next(z for z in room.zonas_especiais
                if z.get("tipo") == "ira_rocha_ardente")


async def main():
    print("\n[1] Escala, duração, alcance e dano inicial")
    room, messages = setup()
    cleric = add_cleric(room, level=6)
    zone = await cast(room, messages)
    check("área 5x5 no nível 6", zone["lado"] == 5 and len(zone["tiles"]) == 25)
    check("duração 5 no nível 6", zone["duracao"] == 5)
    check("lava aplicada às casas", all(room.materiais.get(tuple(tile)) == "lava" for tile in zone["tiles"]))
    check("dano inicial de lava aplicado", cleric["hp"] == 44)
    check("chamas ficam disponíveis só na 2ª rodada",
          zone["disponivel_em"] == room.round_num + 1)
    check("área das chamas é 1x1 maior que a lava",
          len(zone["chamas_permitidas"]) > len(zone["tiles"])
          and [2, 2] in zone["chamas_permitidas"])

    print("\n[2] Escolha manual cria Chamas Vivas e causa dano imediato")
    permitidos = zone["chamas_permitidas"]
    escolhidos = [[4, 4]] + [pos for pos in permitidos if pos != [4, 4]][:3]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], escolhidos)
    check("escolha na 1ª rodada foi recusada", not room.decorations)
    room.round_num = zone["disponivel_em"]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], escolhidos)
    flames = [d for d in room.decorations if d.get("type") == "chama_viva"]
    check("quatro decorações foram criadas", len(flames) == 4)
    check("posições escolhidas foram respeitadas",
          {tuple(d["pos"]) for d in flames} == {tuple(p) for p in escolhidos})
    check("chamas ficam indexadas como 2d4",
          all(room._fire_damage_tiles.get(tuple(p)) == "2d4" for p in escolhidos))
    check("dano da chama soma ao dano da lava", cleric["hp"] < 44)

    print("\n[3] A área expira e restaura o mapa")
    base_tile = tuple(zone["tiles"][0])
    room.round_num = zone["expira_em"]
    await room._processar_zonas_turno()
    check("zona ficou inativa", not zone["ativa"])
    check("lava foi removida", room.materiais.get(base_tile) != "lava")
    check("Chamas Vivas foram removidas", not any(
        d.get("ira_rocha_ardente_id") == zone["id"] for d in room.decorations))

    print("\n[4] Validação rejeita escolha incompleta")
    room, messages = setup()
    add_cleric(room, level=6)
    zone = await cast(room, messages)
    room.round_num = zone["disponivel_em"]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], zone["chamas_permitidas"][:1])
    check("escolha incompleta foi recusada", not room.decorations)
    check("erro foi enviado", any(msg.get("type") == "error" for _, msg in messages))

    print("\n[5] A janela para colocar as Chamas Vivas nunca é vazia")
    # As chamas liberam em `disponivel_em` = rodada+1 e a lava morre em
    # `expira_em` = rodada+duração. Com 1d4=1 no nível 1 os dois coincidiam: a
    # zona expirava exatamente na rodada em que as chamas liberariam, então o
    # slot de 4º círculo era gasto e as Chamas Vivas eram IMPOSSÍVEIS.
    room, messages = setup()
    cleric = add_cleric(room, level=1)
    zone = await cast_dur_minima(room, messages)
    check("duração mínima 2 (piso) mesmo com 1d4=1", zone["duracao"] == 2)
    check("sobra ao menos 1 rodada para colocar",
          zone["expira_em"] > zone["disponivel_em"])
    # E a colocação funciona de verdade nessa única rodada. O avanço passa
    # por _processar_zonas_turno, como no jogo: era ELE que desativava a zona
    # antes de o clérigo ter qualquer chance de escolher as casas.
    room.round_num = zone["disponivel_em"]
    await room._processar_zonas_turno()
    escolhidos = zone["chamas_permitidas"][:zone["chamas_pendentes"]]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], escolhidos)
    check("as chamas realmente entram nessa rodada",
          len([d for d in room.decorations if d.get("type") == "chama_viva"]) == len(escolhidos))
    check("a zona ainda estava ativa quando as chamas entraram", zone["ativa"])

    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    return 1 if FAIL else 0


sys.exit(asyncio.run(main()))
