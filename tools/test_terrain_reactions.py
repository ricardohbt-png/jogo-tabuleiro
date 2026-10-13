"""Reações elementais (terreno x elemento). Roda da raiz: python -X utf8 tools/test_terrain_reactions.py
Spec: docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    """Sala 20x12 de chão, fase 'playing', sem rede; captura broadcasts e narração."""
    r = S.GameRoom("REACOES")
    r.msgs = []
    r.narr = []
    async def noop(*a, **k):
        pass
    async def bc(msg, *a, **k):
        r.msgs.append(msg)
    async def say(txt, *a, **k):
        r.narr.append(str(txt))
    r.gm_say = say; r.broadcast = bc; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 13):
        for x in range(1, 21):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 20, "h": 12, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def heroi(r, pid, nome, classe, pos):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    r.monsters[m["id"]] = m
    return m


def pinta(r, material, tiles):
    for t in tiles:
        r.materiais[tuple(t)] = material
    r._rebuild_materiais_index()


def roda(coro):
    return asyncio.run(coro)


print("[1] materiais novos")
check("piche é piso com terreno piche",
      S.MATERIAIS["piche"]["categoria"] == "piso" and S.MATERIAIS["piche"]["terreno"] == "piche")
check("lava_solidificada é piso transitável",
      S.MATERIAIS["lava_solidificada"]["categoria"] == "piso"
      and not S.MATERIAIS["lava_solidificada"]["solido"])
r = sala()
h = heroi(r, "a", "Ana", "warrior", [2, 2])
pinta(r, "piche", [(5, 5)])
pinta(r, "lava_solidificada", [(6, 5)])
pinta(r, "lava", [(7, 5)])
check("entrar no piche custa 2", r._water_step_cost(h, 5, 5) == 2)
check("entrar na crosta custa 1", r._water_step_cost(h, 6, 5) == 1)
check("entrar na lava custa 2", r._water_step_cost(h, 7, 5) == 2)
check("a crosta não é lava", not r._is_lava_tile(6, 5) and r._is_lava_tile(7, 5))

import terrain_reactions as TR

print("[2] constantes e tabela")
check("elementos canônicos iguais aos do servidor",
      (TR.RX_FIRE, TR.RX_COLD, TR.RX_LIGHTNING) == (S.DMG_FIRE, S.DMG_COLD, S.DMG_LIGHTNING))
ids = [l["id"] for l in TR.REACOES]
check("tabela tem as 4 reações ativas + gelo desligada",
      ids == ["choque_na_poca", "incendiar_piche", "congelar_agua", "crosta_de_lava", "derreter_gelo"]
      and [l["ativa"] for l in TR.REACOES] == [True, True, True, True, False])

print("[3] choque na poça")
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
a = heroi(r, "a", "Ana", "mage", [3, 5])      # já atingida pelo raio
b = heroi(r, "b", "Bia", "warrior", [8, 5])    # na poça, não atingida
c = heroi(r, "c", "Cris", "warrior", [8, 8])   # fora da poça

async def raio_na_poca():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "a", "cd": 12}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10, atingidos={"a"})
roda(raio_na_poca())
check("quem estava na poça e não foi atingido toma o choque", b["hp"] < b["max_hp"])
check("quem já foi atingido não toma o choque", a["hp"] == a["max_hp"])
check("quem está fora da poça não toma", c["hp"] == c["max_hp"])
check("um broadcast de choque com as casas da poça",
      sum(1 for m in r.msgs if m.get("type") == "reacao_elemental" and m.get("tipo") == "choque") == 1)

r = sala()
pinta(r, "agua", [(x, 5) for x in range(1, 21)])           # poça comprida
longe = heroi(r, "l", "Longe", "warrior", [14, 5])          # a 11 do impacto
perto = heroi(r, "p", "Perto", "warrior", [8, 5])           # a 5 do impacto
async def raio2():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(raio2())
check("raio 6: perto toma, longe não", perto["hp"] < perto["max_hp"] and longe["hp"] == longe["max_hp"])

r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5])
v = heroi(r, "v", "Vera", "warrior", [7, 5])
v["voo"] = True; v["altura"] = 3
async def raio3():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(raio3())
check("voador sobre a poça não toma o choque", v["hp"] == v["max_hp"] and b["hp"] < b["max_hp"])

r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5]); d = heroi(r, "d", "Davi", "warrior", [7, 5])
async def raio4():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
        await r._rx_registrar(S.DMG_LIGHTNING, [(4, 5)], dano=10)   # segunda criatura atingida na mesma ação
roda(raio4())
check("duas notificações na mesma ação: um choque só",
      sum(1 for m in r.msgs if m.get("tipo") == "choque") == 1)

r = sala()
pinta(r, "agua_profunda", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5])
async def raio5():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(raio5())
check("água profunda não conduz (v1)", b["hp"] == b["max_hp"])

print("[4] frio: congelar água e crosta de lava")
r = sala()
pinta(r, "agua", [(5, 5), (6, 5)])
b = heroi(r, "b", "Bia", "warrior", [5, 5]); b["moves_left"] = 6
async def frio():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x", "cd": 99}):
        await r._rx_registrar(S.DMG_COLD, [(5, 5), (6, 5)])
roda(frio())
check("água vira piso congelado", r.materiais[(5, 5)] == "piso_congelado" and r.materiais[(6, 5)] == "piso_congelado")
check("quem falha no Reflexos perde o movimento (CD 99)", b["moves_left"] == 0 and b.get("movimento_perdido"))
r.round_num = 3
r._expirar_terrenos_inverno()
check("ainda congelada na rodada 3", r.materiais[(5, 5)] == "piso_congelado")
r.round_num = 4
r._expirar_terrenos_inverno()
check("volta a ser água na rodada 4 (3 rodadas)", r.materiais[(5, 5)] == "agua")

r = sala()
pinta(r, "lava", [(8, 5)])
async def frio2():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_COLD, [(8, 5)])
roda(frio2())
check("lava vira lava_solidificada", r.materiais[(8, 5)] == "lava_solidificada" and not r._is_lava_tile(8, 5))
r.round_num = 4
r._expirar_terrenos_inverno()
check("a lava volta depois de 3 rodadas", r._is_lava_tile(8, 5))

r = sala()
pinta(r, "lava", [(8, 5)])
r._aplicar_camadas_terreno_inverno([(8, 5)], "lava", "ira_1", permanente=False, expira_em=10)   # lava da Ira
async def frio3():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_COLD, [(8, 5)])
roda(frio3())
check("lava da Ira também vira crosta", r.materiais[(8, 5)] == "lava_solidificada")
r.round_num = 4
r._expirar_terrenos_inverno()
check("ao acabar a crosta, a lava da Ira (ainda ativa) volta", r._is_lava_tile(8, 5))

print("[5] travas")
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5])
vezes = []
orig = S.GameRoom._rx_choque
async def espiao(self, tiles, origem, pend, prof):
    vezes.append(1)
    return await orig(self, tiles, origem, pend, prof)
S.GameRoom._rx_choque = espiao
async def reentrada():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(reentrada())
S.GameRoom._rx_choque = orig
check("o dano do choque não reentra no motor (um choque, não um por vítima)", len(vezes) == 1)

# cadeia: linha de teste fogo->fogo que se encadeia sempre; o limite é profundidade 2
r = sala()
pinta(r, "piche", [(5, 5)])
conta = []
async def _rx_teste_cadeia(self, tiles, origem, pend, prof):
    conta.append(prof)
    await self._rx_encadear(TR.RX_FIRE, tiles, {"origem": origem, "pend": {}}, prof)
S.GameRoom._rx_teste_cadeia = _rx_teste_cadeia
TR.REACOES.append({"id": "teste", "elemento": TR.RX_FIRE, "estado": "piche", "efeito": "_rx_teste_cadeia", "ativa": True})
# desliga a linha real de incendiar para isolar o teste de cadeia
real = next(l for l in TR.REACOES if l["id"] == "incendiar_piche")
real["ativa"] = False
async def cadeia():
    async with r.evento_elemental({"tipo": "teste", "caster_id": "x"}):
        await r._rx_registrar(TR.RX_FIRE, [(5, 5)])
roda(cadeia())
TR.REACOES[:] = [l for l in TR.REACOES if l["id"] != "teste"]
real["ativa"] = True
check("cadeia respeita a profundidade máxima 2 (prof 0,1,2)", conta == [0, 1, 2])

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
