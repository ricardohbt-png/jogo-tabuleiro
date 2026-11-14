"""Lâminas de Riposta: receber lâminas nunca descarta o excedente de 10.

Regressão: _route_acquired_item somava com min(10, ...) e as lâminas além do
teto sumiam, devolvendo 'bag' (sucesso).
Roda da raiz: python -X utf8 tools/test_laminas_empilhar.py"""
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(nome, ok):
    print(("  ok   " if ok else "  FALHA ") + nome)
    if not ok:
        FALHAS.append(nome)


BASE = next(i for i in S.SHOP_MERCHANT if i["id"] == "laminas_riposta")


def lamina(n, veneno=None):
    it = deepcopy(BASE)
    it["counter_blade_count"] = n
    if veneno:
        it["poison_ids"] = [veneno]
    return it


def total(p, veneno=None):
    return sum(i.get("counter_blade_count", 1) for i in p["bag"]
               if i.get("id") == "laminas_riposta"
               and (i.get("poison_ids") or [None])[0] == veneno)


def jogador(bag, tamanho=6):
    p = S.make_player("p1", "Lad", "rogue", 0)
    p["bag"] = bag
    p["bag_size"] = tamanho
    return p


r = S.GameRoom("T")

print("[1] cabe tudo na pilha existente")
p = jogador([lamina(4)])
check("devolve bag", r._route_acquired_item(p, lamina(3)) == "bag")
check("uma pilha de 7", [i["counter_blade_count"] for i in p["bag"]] == [7])

print("[2] excedente vira nova pilha (nada se perde)")
p = jogador([lamina(8)])
check("devolve bag", r._route_acquired_item(p, lamina(5)) == "bag")
check("total 13 na bolsa", total(p) == 13)
check("nenhuma pilha passa de 10", all(i["counter_blade_count"] <= 10 for i in p["bag"]))
check("pilhas 10 e 3", sorted(i["counter_blade_count"] for i in p["bag"]) == [3, 10])

print("[3] pilha cheia: tudo vai para nova pilha")
p = jogador([lamina(10)])
r._route_acquired_item(p, lamina(4))
check("total 14", total(p) == 14)

print("[4] excedente reparte entre duas pilhas incompletas")
p = jogador([lamina(9), lamina(9)])
r._route_acquired_item(p, lamina(5))
check("total 23", total(p) == 23)
check("nenhuma pilha passa de 10", all(i["counter_blade_count"] <= 10 for i in p["bag"]))

print("[5] bolsa cheia: o excedente nao e descartado em silencio")
p = jogador([lamina(8), {"id": "x", "name": "x", "item_slot": "bag"}], tamanho=2)
res = r._route_acquired_item(p, lamina(5))
check("nao devolve bag como se tudo coubesse (res=%s, total=%d)" % (res, total(p)),
      res != "bag" or total(p) == 13)

print("[6] venenos diferentes nao se misturam")
p = jogador([lamina(8, "veneno_fungo_acre")])
r._route_acquired_item(p, lamina(5))
check("sem veneno ficou separado", total(p) == 5 and total(p, "veneno_fungo_acre") == 8)

print("\n=== %d falharam ===" % len(FALHAS))
sys.exit(1 if FALHAS else 0)
