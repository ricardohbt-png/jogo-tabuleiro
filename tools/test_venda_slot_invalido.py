"""sell_item com item_slot que nao e texto nao pode virar erro interno.

`handle_shop_sell` chamava item_slot.startswith(...) e dict.get(item_slot) sem
checar o tipo: None/numero/lista estouravam AttributeError/TypeError (achado por
fuzz de campos invalidos no handler real).
Roda da raiz: python -X utf8 tools/test_venda_slot_invalido.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []
def check(c, m):
    print(("  ok   " if c else "  FALHA ") + m)
    if not c: FALHAS.append(m)

async def main():
    r = S.GameRoom("VENDA")
    env = []
    async def send(pid, msg): env.append(msg)
    async def nada(*a, **k): return None
    r.send_to = send; r.push_state = nada; r.broadcast = nada; r.gm_say = nada
    r.phase = "city"
    p = S.make_player("p1", "T", "warrior", 0)
    r.players = {"p1": p}
    ouro = p["gold"]
    for lixo in (None, 5, 1.5, [], ["bag_0"], {"a": 1}, True):
        env.clear()
        try:
            await r.handle_shop_sell("p1", lixo)
            ok = True
        except Exception as e:
            ok = False
            print("     ", type(e).__name__, e)
        check(ok, f"item_slot={lixo!r}: sem excecao")
    check(p["gold"] == ouro, "nenhum ouro mudou")
    # caminho normal continua vendendo
    p["bag"] = [{"id": "x", "name": "X", "buy_price": 30}]
    await r.handle_shop_sell("p1", "bag_0")
    check(p["gold"] == ouro + 10 and not p["bag"], "venda normal da bolsa segue funcionando")

asyncio.run(main())
sys.exit(1 if FALHAS else 0)
