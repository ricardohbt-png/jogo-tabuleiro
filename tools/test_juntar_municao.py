"""Juntar pilhas de munição iguais arrastando uma sobre a outra (2026-11-01).

Duas pilhas são iguais quando têm o mesmo tipo, os mesmos bônus/efeitos de disparo
e a mesma combinação de venenos (`_ammo_stack_key`). Se a soma passa do limite da
pilha (20 na bolsa, 10 na mão secundária), o destino fica cheio e a origem guarda o que sobrou.
Pilhas diferentes não se juntam: soltar uma sobre a outra só reordena, como antes.
Roda da raiz: python -X utf8 tools/test_juntar_municao.py"""
import asyncio, os, sys
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def municao(ident, n, **extra):
    base = deepcopy(next(i for i in S.SHOP_AMMO if i["id"] == ident))
    base["ammo_count"] = n
    base.update(extra)
    return base


def sala(bag, off_hand=None):
    r = S.GameRoom("MUNI")
    p = S.make_player("p", "Luccas", "rogue", 0)
    p["bag"] = bag
    p["gear"]["off_hand"] = off_hand
    r.players = {"p": p}
    r.phase = "city"
    r.erros = []
    async def send(pid, msg):
        if msg.get("type") == "error": r.erros.append(msg)
    async def nada(*a, **k): pass
    r.send_to = send; r.push_state_or_city = nada; r.push_state = nada; r.gm_say = nada
    return r, p


def contagens(p):
    return [it.get("ammo_count") for it in p["bag"]]


async def main():
    print("\n[1] 3 + 4 virotes viram uma pilha de 7")
    r, p = sala([municao("virotes", 3), municao("virotes", 4)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("sobrou uma pilha só, com 7", contagens(p) == [7], contagens(p))

    print("\n[2] passou do limite: completa o destino e a origem fica com o resto")
    r, p = sala([municao("virotes", 18), municao("virotes", 7)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("destino 20, origem 5", contagens(p) == [5, 20], contagens(p))
    r, p = sala([municao("virotes", 5), municao("virotes", 20)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("destino já cheio: nada muda", contagens(p) == [5, 20], contagens(p))

    print("\n[3] com aljava o limite da bolsa continua 20")
    aljava = deepcopy(next(i for i in S.SHOP_AMMO if i["id"] == "aljava_pequena"))
    r, p = sala([municao("virotes", 25), municao("virotes", 28)], off_hand=aljava)
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("pilhas antigas acima de 20 permanecem intactas", contagens(p) == [25, 28], contagens(p))

    print("\n[4] envenenadas juntam só com o mesmo veneno")
    veneno = next(iter(S.VENENOS))
    outro = [v for v in S.VENENOS if v != veneno][0]
    r, p = sala([municao("virotes", 3, poison_ids=[veneno]), municao("virotes", 4, poison_ids=[veneno])])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("mesmo veneno: juntou (7)", contagens(p) == [7], contagens(p))
    check("…e continua envenenada", p["bag"][0].get("poison_ids") == [veneno])
    r, p = sala([municao("virotes", 3, poison_ids=[veneno]), municao("virotes", 4, poison_ids=[outro])])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("veneno diferente: não junta", sorted(contagens(p)) == [3, 4], contagens(p))
    r, p = sala([municao("virotes", 3, poison_ids=[veneno]), municao("virotes", 4)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("envenenada com comum: não junta", sorted(contagens(p)) == [3, 4], contagens(p))

    print("\n[5] bônus mágico ou composição diferentes não juntam")
    r, p = sala([municao("virotes", 3), municao("virotes_magicos", 4)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("comum com mágica: não junta", sorted(contagens(p)) == [3, 4], contagens(p))
    r, p = sala([municao("virotes", 3), municao("virote_incendiario", 4)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 1})
    check("comum com incendiária: não junta", sorted(contagens(p)) == [3, 4], contagens(p))
    check("pilhas diferentes: soltar uma na outra reordena, como antes",
          [it["id"] for it in p["bag"]] == ["virote_incendiario", "virotes"], [it["id"] for it in p["bag"]])

    print("\n[6] com a pilha equipada na mão secundária")
    r, p = sala([municao("virotes", 4)], off_hand=municao("virotes", 3))
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"equip": "off_hand"})
    check("da bolsa para a equipada: 7 na mão, bolsa vazia",
          p["gear"]["off_hand"]["ammo_count"] == 7 and p["bag"] == [], (p["gear"]["off_hand"], p["bag"]))
    r, p = sala([municao("virotes", 4)], off_hand=municao("virotes", 3))
    await r.handle_juntar_municao("p", {"equip": "off_hand"}, {"bolsa": 0})
    check("da equipada para a bolsa: 7 na bolsa, mão vazia",
          contagens(p) == [7] and p["gear"]["off_hand"] is None, (p["gear"]["off_hand"], p["bag"]))

    print("\n[7] origem e destino inválidos não quebram nada")
    r, p = sala([municao("virotes", 3)])
    await r.handle_juntar_municao("p", {"bolsa": 0}, {"bolsa": 0})
    await r.handle_juntar_municao("p", {"bolsa": 5}, {"bolsa": 0})
    await r.handle_juntar_municao("p", "lixo", None)
    check("nada mudou", contagens(p) == [3], contagens(p))

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
