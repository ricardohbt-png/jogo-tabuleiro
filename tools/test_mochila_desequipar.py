"""Desequipar item que dá espaços na bolsa não pode deixar a bolsa acima da capacidade.

Mochilas, alforjes e Maravilhas do Aventureiro somam espaços (`effect: bagslots`,
`value` = espaços). Ao desequipar, a bolsa perde esses espaços E ganha o próprio
item; se o que sobra não cabe, o servidor recusa. Antes só os alforjes e as
Maravilhas tinham a trava: desequipar a Mochila de Carga com 11 itens deixava
12 itens numa bolsa de 6.
"""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


async def desequipar(item_id, n_itens):
    r = S.GameRoom("MOCHILA")

    async def nada(*a, **k):
        return None
    r.push_state = nada
    r.broadcast = nada
    r.gm_say = nada
    erros = []

    async def send_to(pid, msg, **k):
        if msg.get("type") == "error":
            erros.append(msg)
    r.send_to = send_to
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.phase = "city"
    item = copy.deepcopy(next(i for i in S.SHOP_MERCHANT if i["id"] == item_id))
    item.pop("price", None)
    p["bag"] = [item]
    await r.handle_equip_from_bag("p1", 0)
    slot = next(k for k, v in p["gear"].items() if v and v.get("id") == item_id)
    leite = next(i for i in S.SHOP_TAVERN if i["id"] == "leite")
    p["bag"] = [copy.deepcopy(leite) for _ in range(n_itens(p["bag_size"], item["value"]))]
    await r.handle_unequip("p1", slot)
    return p, slot, erros


async def main():
    ids = [i["id"] for i in S.SHOP_MERCHANT if i.get("effect") == "bagslots"]
    check(len(ids) >= 6, f"há itens de espaço extra no mercador ({len(ids)})")
    for item_id in ids:
        # Bolsa quase cheia: depois de perder os espaços, o item não cabe.
        p, slot, erros = await desequipar(item_id, lambda tam, extra: tam - 1)
        check(bool(erros) and p["gear"].get(slot),
              f"{item_id}: recusa quando os itens não caberiam")
        check(len(p["bag"]) <= p["bag_size"],
              f"{item_id}: a bolsa nunca passa da capacidade ({len(p['bag'])}/{p['bag_size']})")
        # Cabe com folga: sobra lugar mesmo sem os espaços extras.
        p, slot, erros = await desequipar(item_id, lambda tam, extra: max(0, tam - extra - 1))
        check(not erros and not p["gear"].get(slot),
              f"{item_id}: desequipa quando tudo cabe")
        check(len(p["bag"]) <= p["bag_size"], f"{item_id}: cabe certinho ({len(p['bag'])}/{p['bag_size']})")


async def outros_caminhos():
    """Largar a mochila no chão direto do equipamento e trocá-la por outro
    item também tiram os espaços extras: a mesma trava vale."""
    print("[2] largar no chão e trocar por outro item")

    async def montar():
        r = S.GameRoom("MOCHILA2")

        async def nada(*a, **k):
            return None
        r.push_state = nada
        r.broadcast = nada
        r.gm_say = nada
        erros = []

        async def send_to(pid, msg, **k):
            if msg.get("type") == "error":
                erros.append(msg)
        r.send_to = send_to
        p = S.make_player("p1", "Ana", "warrior", 0)
        r.players["p1"] = p
        r.phase = "playing"
        r.map_w = r.map_h = 5
        r.tiles = [[S.FLOOR] * 5 for _ in range(5)]
        r._decor_block_tiles = set()
        p["pos"] = [2, 2]
        item = copy.deepcopy(next(i for i in S.SHOP_MERCHANT if i["id"] == "mochila_carga"))
        item.pop("price", None)
        p["bag"] = [item]
        await r.handle_equip_from_bag("p1", 0)
        slot = next(k for k, v in p["gear"].items() if v and v.get("id") == "mochila_carga")
        leite = next(i for i in S.SHOP_TAVERN if i["id"] == "leite")
        p["bag"] = [copy.deepcopy(leite) for _ in range(p["bag_size"] - 1)]
        return r, p, slot, erros

    r, p, slot, erros = await montar()
    await r.handle_drop_item("p1", "gear", slot_key=slot)
    check(bool(erros) and p["gear"].get(slot) and len(p["bag"]) <= p["bag_size"],
          f"largar no chão: recusa e a bolsa segue dentro da capacidade ({len(p['bag'])}/{p['bag_size']})")

    r, p, slot, erros = await montar()
    outro = copy.deepcopy(next(i for i in S.SHOP_MERCHANT if i["id"] == "ultimo_suspiro"))
    outro.pop("price", None)
    p["bag"][-1] = outro
    other = "item2" if slot == "item1" else "item1"
    p["gear"][other] = {"id": "x", "name": "x", "item_slot": "item"}
    await r.handle_equip_from_bag("p1", len(p["bag"]) - 1)
    check(len(p["bag"]) <= p["bag_size"],
          f"trocar a mochila por outro item: a bolsa segue dentro da capacidade ({len(p['bag'])}/{p['bag_size']})")


asyncio.run(main())
asyncio.run(outros_caminhos())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
