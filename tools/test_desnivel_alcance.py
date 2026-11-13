"""Desnível do terreno no alcance, na linha de visão e no corpo a corpo.

Regra (2026-11-08): cada nível de terreno de diferença soma 1 quadrado à
distância. Herói em nível 0 adjacente a um inimigo em nível 1 está a 2
quadrados: corpo a corpo comum não alcança; lança (alcance 2) e armas à
distância sim. O voo continua com 2 pontos de altura = 1 quadrado, e 1 ponto
de voo segue tolerado no corpo a corpo.

Também cobre a linha de visão: a borda de um platô de 1 nível não pode
esconder o que está em cima dele (era o "clique recusado" do ataque à
distância).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


def sala(platos=None):
    r = server.GameRoom("DESNIVEL")
    r.map_w, r.map_h = 9, 3
    r.tiles = [[server.FLOOR] * r.map_w for _ in range(r.map_h)]
    r._decor_block_tiles = set()
    r._decor_tall_tiles = set()
    r.elevacoes = dict(platos or {})
    return r


def plato(x0, x1, nivel):
    return {(x, y): nivel for x in range(x0, x1 + 1) for y in range(3)}


def heroi(r, pos, arma):
    p = {"id": "p1", "pos": list(pos), "altura": 0, "hp": 10, "weapon": dict(arma)}
    r.players["p1"] = p
    return p


def monstro(r, pos, **extra):
    m = {"id": "m1", "pos": list(pos), "hp": 10, "size": [1, 1], "altura": 0}
    m.update(extra)
    r.monsters = {"m1": m}
    return m


print("[1] linha de visão por cima de um platô de 1 nível")
r = sala(plato(3, 8, 1))
for tx in (3, 4, 6, 8):
    monstro(r, (tx, 1))
    check(r._tem_linha_de_visao([1, 1], [tx, 1]), f"do chão vê o alvo em cima do platô (x={tx})")
    check(r._tem_linha_de_visao([tx, 1], [1, 1]), f"de cima do platô vê o alvo no chão (x={tx})")
r = sala({(4, y): 2 for y in range(3)})
monstro(r, (7, 1))
check(not r._tem_linha_de_visao([1, 1], [7, 1]),
      "um paredão de 2 níveis entre dois alvos no chão ainda tapa a visão")

print("[2] custo vertical: 1 nível = 1 quadrado")
r = sala(plato(3, 8, 1))
p = heroi(r, (1, 1), {"id": "arco_curto", "range": 6})
m = monstro(r, (3, 1))
check(r._custo_vertical_terreno(p, [3, 1], destino=m) == 1, "1 nível de diferença custa 1 quadrado")
r = sala(plato(3, 8, 2))
p = heroi(r, (1, 1), {"id": "arco_curto", "range": 6})
m = monstro(r, (3, 1))
check(r._custo_vertical_terreno(p, [3, 1], destino=m) == 2, "2 níveis de diferença custam 2 quadrados")
r = sala()
p = heroi(r, (1, 1), {"id": "arco_curto", "range": 6})
m = monstro(r, (3, 1), voo=True, altura=2)
check(r._custo_vertical_terreno(p, [3, 1], destino=m) == 1, "voo continua: 2 pontos = 1 quadrado")

print("[3] alcance de arma à distância desconta a subida")
r = sala(plato(3, 8, 1))
p = heroi(r, (1, 1), {"id": "arco_curto", "range": 3})
check(r._tile_no_alcance_arma_distancia(p, [3, 1], 3), "alcance 3: alvo a 2 + 1 de subida está dentro")
check(not r._tile_no_alcance_arma_distancia(p, [4, 1], 3), "alcance 3: alvo a 3 + 1 de subida fica fora")

print("[4] corpo a corpo do herói")
r = sala(plato(2, 8, 1))
p = heroi(r, (1, 1), {"id": "shortsword"})
m = monstro(r, (2, 1))
check(not r._alvo_no_alcance_arma(p, m), "espada: adjacente e 1 nível acima não alcança (2 quadrados)")
p["weapon"] = {"id": "lanca", "reach": "lanca"}
check(r._alvo_no_alcance_arma(p, m), "lança (alcance 2): adjacente e 1 nível acima alcança")
m["pos"] = [3, 1]
check(not r._alvo_no_alcance_arma(p, m), "lança: 2 casas + 1 de subida = 3, não alcança")
r = sala(plato(2, 8, 2))
p = heroi(r, (1, 1), {"id": "lanca", "reach": "lanca"})
m = monstro(r, (2, 1))
check(not r._alvo_no_alcance_arma(p, m), "lança: adjacente e 2 níveis acima (3 quadrados) não alcança")
r = sala()
p = heroi(r, (1, 1), {"id": "shortsword"})
m = monstro(r, (2, 1), voo=True, altura=1)
check(r._alvo_no_alcance_arma(p, m), "voo baixo (1 ponto) segue alcançável corpo a corpo")
m["altura"] = 2
check(not r._alvo_no_alcance_arma(p, m), "voo a 2 pontos (1 quadrado) já tira do corpo a corpo comum")

print("[5] corpo a corpo do monstro")
r = sala(plato(2, 8, 1))
heroi(r, (1, 1), {"id": "shortsword"})
m = monstro(r, (2, 1))
check(not r._monster_attack_in_range(m, [1, 1], {"reach": 1}),
      "monstro em cima do platô não morde o herói adjacente embaixo")
check(r._monster_attack_in_range(m, [1, 1], {"reach": 2}),
      "monstro com alcance 2 alcança o herói adjacente 1 nível abaixo")
check(r._monster_attack_in_range(m, [1, 1], {"range": 3}),
      "ataque à distância do monstro alcança (1 + 1 de subida ≤ 3)")
p = r.players["p1"]
check(not r._monster_attack_height_ok(m, p, {"reach": 1}), "guarda vertical do executor recusa o golpe")
check(r._monster_attack_height_ok(m, p, {"range": 3}), "guarda vertical aceita o tiro")

print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
