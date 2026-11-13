"""Templo: "Cura Completa" cura o GRUPO inteiro, 1 moeda a cada 3 PV (arredonda para baixo).

Regras combinadas com o autor:
- soma os PV que faltam dos heróis vivos e presentes; custo = faltando // 3, mínimo 1 moeda;
- ouro insuficiente => cura parcial (3 PV por moeda), começando por quem tem MAIS PV faltando;
- ninguém ferido => recusa sem cobrar; o preço é fixo (não sofre o ágio da cidade);
- o serviço individual de 15 moedas deixou de existir.

Roda da raiz:
    python -X utf8 tools/test_templo_cura_grupo.py
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


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def sala(faltando, ouro=50, extras=None):
    """Sala na cidade com um herói por entrada de `faltando` (PV que faltam a cada um)."""
    room = S.GameRoom("TEST")
    erros = []

    async def noop(*a, **k):
        return None

    async def send_to(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            erros.append(str(msg.get("msg")))
    room.broadcast = noop
    room.push_state = noop
    room.push_state_or_city = noop
    room.gm_say = noop
    room.send_to = send_to
    room.phase = "city"
    room.round_num = 1
    classes = ["rogue", "mage", "warrior", "cleric", "paladin", "bard"]
    for i, falta in enumerate(faltando):
        h = S.make_player(f"h{i}", f"Heroi{i}", classes[i], i)
        h.update(alive=True, connected=True, max_hp=20, hp=20 - falta, gold=ouro if i == 0 else 0)
        room.players[h["id"]] = h
    room._erros = erros
    return room


def hps(room):
    return [h["hp"] for h in room.players.values()]


async def main():
    item = next((i for i in S.SHOP_TEMPLE if i["id"] == "full_heal"), None)
    check("o serviço continua com o id full_heal no Templo", item is not None)
    check("é um serviço de grupo, de preço fixo", bool(item and item.get("cura_grupo") and item.get("preco_fixo")))

    # [1] O exemplo do autor: 4 + 3 + 5 = 12 PV => 4 moedas
    room = sala([4, 3, 5], ouro=10)
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("todos ficam com a vida cheia", hps(room) == [20, 20, 20])
    check("custou 4 moedas (12 PV / 3)", room.players["h0"]["gold"] == 6)
    check("sem erro", not room._erros)

    # [2] Número quebrado arredonda para baixo
    room = sala([5, 4, 4], ouro=10)     # 13 PV => 4 moedas
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("13 PV custam 4 moedas (e curam tudo)", room.players["h0"]["gold"] == 6 and hps(room) == [20, 20, 20])

    # [3] Poucos PV faltando: mínimo de 1 moeda
    room = sala([2], ouro=10)
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("2 PV custam o mínimo de 1 moeda", room.players["h0"]["gold"] == 9 and hps(room) == [20])

    # [4] Ninguém ferido: recusa e não cobra
    room = sala([0, 0], ouro=10)
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("ninguém ferido: não cobra", room.players["h0"]["gold"] == 10)
    check("ninguém ferido: avisa", len(room._erros) == 1)

    # [5] Morto e desconectado não entram na conta nem na cura
    room = sala([3, 3, 3], ouro=10)
    room.players["h1"]["alive"] = False
    room.players["h2"]["connected"] = False
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("só o herói vivo e presente é curado", hps(room) == [20, 17, 17])
    check("a conta só considera quem foi curado (3 PV = 1 moeda)", room.players["h0"]["gold"] == 9)

    # [6] Ouro insuficiente: cura parcial, começando por quem mais precisa
    room = sala([3, 4, 5], ouro=2)       # custo 4; só 2 moedas => 6 PV
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("gastou todo o ouro", room.players["h0"]["gold"] == 0)
    check("o mais ferido (5) foi curado por inteiro", room.players["h2"]["hp"] == 20)
    check("o seguinte (4) recebeu o que sobrou (1 PV)", room.players["h1"]["hp"] == 20 - 4 + 1)
    check("o menos ferido (3) não recebeu nada", room.players["h0"]["hp"] == 17)

    # [7] Sem nenhum ouro: recusa
    room = sala([3, 4], ouro=0)
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("sem ouro: nada muda", hps(room) == [17, 16] and len(room._erros) == 1)

    # [8] O plano (pré-visualização) é puro e bate com a compra
    room = sala([3, 4, 5], ouro=2)
    plano = room._plano_cura_grupo_templo("h0")
    check("plano: custo total 4, pagável 2, parcial", plano["custo"] == 4 and plano["moedas"] == 2 and plano["parcial"])
    check("plano não altera nada", hps(room) == [17, 16, 15])
    depois = {h["id"]: d for h, a, d in plano["itens"]}
    await room.handle_shop_buy("h0", "templo", "full_heal")
    check("a compra aplica exatamente o plano", all(room.players[i]["hp"] == d for i, d in depois.items()))

    # [9] O ágio da cidade não mexe no preço (serviço de preço fixo)
    antigo = S.CITY_PRICE_MODS.get("alva_e_luz")
    S.CITY_PRICE_MODS["alva_e_luz"] = [{"fato": "agio_teste", "preco_mult": 3.0}]
    try:
        room = sala([6], ouro=10)
        room.fatos = {"agio_teste"}
        room.world_location = "alva_e_luz"
        await room.handle_shop_buy("h0", "templo", "full_heal")
        check("preço fixo: 6 PV = 2 moedas mesmo com ágio de x3", room.players["h0"]["gold"] == 8)
    finally:
        if antigo is None:
            S.CITY_PRICE_MODS.pop("alva_e_luz", None)
        else:
            S.CITY_PRICE_MODS["alva_e_luz"] = antigo


asyncio.run(main())
print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
sys.exit(1 if FAIL else 0)
