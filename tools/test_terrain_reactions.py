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
check("tabela tem as 5 reações ativas + gelo desligada",
      ids == ["choque_na_poca", "incendiar_piche", "congelar_agua", "crosta_de_lava", "explodir_gas", "derreter_gelo"]
      and [l["ativa"] for l in TR.REACOES] == [True, True, True, True, True, False])

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
real = next(l for l in TR.REACOES if l["id"] == "incendiar_piche")
try:
    TR.REACOES.append({"id": "teste", "elemento": TR.RX_FIRE, "estado": "piche", "efeito": "_rx_teste_cadeia", "ativa": True})
    # desliga a linha real de incendiar para isolar o teste de cadeia
    real["ativa"] = False
    async def cadeia():
        async with r.evento_elemental({"tipo": "teste", "caster_id": "x"}):
            await r._rx_registrar(TR.RX_FIRE, [(5, 5)])
    roda(cadeia())
finally:
    TR.REACOES[:] = [l for l in TR.REACOES if l["id"] != "teste"]
    real["ativa"] = True
    del S.GameRoom._rx_teste_cadeia
check("cadeia respeita a profundidade máxima 2 (prof 0,1,2)", conta == [0, 1, 2])


print("[6] piche em chamas")
r = sala()
pinta(r, "piche", [(5, 5), (6, 5), (7, 5), (12, 9)])      # (12,9) é outra mancha, não conectada
no_piche = heroi(r, "a", "Ana", "warrior", [6, 5])
fora = heroi(r, "b", "Bia", "warrior", [10, 10])
async def fogo():
    async with r.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(5, 5)])           # casa sem ninguém
roda(fogo())
zonas = [z for z in r.zonas_especiais if z.get("tipo") == "chamas_piche" and z.get("ativa")]
check("cria UMA zona de chamas de piche", len(zonas) == 1)
check("a zona cobre a mancha conectada e não a outra",
      sorted(map(tuple, zonas[0]["tiles"])) == [(5, 5), (6, 5), (7, 5)])
check("a casa atingida (5,5) estava vazia: a fonte sem criatura incendiou mesmo assim",
      (5, 5) in {tuple(t) for t in zonas[0]["tiles"]} and no_piche["pos"] != [5, 5])
check("quem estava na mancha sofre na ignição", no_piche["hp"] < no_piche["max_hp"])
check("quem estava fora não sofre", fora["hp"] == fora["max_hp"])
check("quem estava na mancha fica em chamas", no_piche.get("em_chamas_rodadas", 0) > 0)
async def fogo2():
    async with r.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(6, 5)])
roda(fogo2())
check("fogo de novo na mancha já em chamas: não cria outra zona",
      len([z for z in r.zonas_especiais if z.get("tipo") == "chamas_piche" and z.get("ativa")]) == 1)

# início do turno e entrada
hp0 = no_piche["hp"]
roda(r._processar_zona_molochus_inicio_turno(no_piche))
check("início do turno na mancha em chamas causa dano", no_piche["hp"] < hp0)
entra = heroi(r, "c", "Cris", "warrior", [3, 5])
hp0 = entra["hp"]
roda(r._verificar_entrada_zona_molochus(entra, 5, 5))
check("entrar na mancha em chamas causa dano", entra["hp"] < hp0)

# voador não é atingido
r2 = sala()
pinta(r2, "piche", [(5, 5), (6, 5)])
voa = heroi(r2, "v", "Vera", "warrior", [5, 5]); voa["voo"] = True; voa["altura"] = 3
async def fogo3():
    async with r2.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": "x"}):
        await r2._rx_registrar(S.DMG_FIRE, [(5, 5)])
roda(fogo3())
check("voador sobre a mancha não é atingido", voa["hp"] == voa["max_hp"])

# fim das chamas: piche autoral vira pedra_negra; mancha temporária volta ao material original
r.round_num = 4
roda(r._processar_zonas_turno())
check("a zona acaba na rodada 4", not any(z.get("ativa") for z in r.zonas_especiais if z.get("tipo") == "chamas_piche"))
check("piche autoral consumido vira pedra_negra", r.materiais[(5, 5)] == "pedra_negra")
check("a outra mancha segue intacta", r.materiais[(12, 9)] == "piche")

r = sala()
pinta(r, "terra", [(5, 5), (6, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5), (6, 5)], "piche", "frasco_1", permanente=False, expira_em=5)
async def fogo4():
    async with r.evento_elemental({"tipo": "item", "id": "bomba_incendiaria", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(5, 5)])
roda(fogo4())
r.round_num = 4
roda(r._processar_zonas_turno())
check("mancha temporária consumida volta ao material original", r.materiais[(5, 5)] == "terra" and r.materiais[(6, 5)] == "terra")

# gancho: criatura em chamas entra no piche
r = sala()
pinta(r, "piche", [(5, 5), (6, 5)])
g = heroi(r, "g", "Gus", "warrior", [5, 5]); g["em_chamas_rodadas"] = 2
roda(r._aplicar_lava_se_pisar(g))
check("criatura em chamas sobre piche incendeia a mancha",
      any(z.get("tipo") == "chamas_piche" and z.get("ativa") for z in r.zonas_especiais))
r = sala()
pinta(r, "piche", [(5, 5), (6, 5)])
g = heroi(r, "g", "Gus", "warrior", [5, 5])
roda(r._aplicar_lava_se_pisar(g))
check("criatura que NÃO está em chamas não incendeia", not r.zonas_especiais)

print("[7] frasco de piche")
d = S.ARREMESSAVEIS["frasco_piche"]
check("frasco de piche: área, sem dano, terreno piche por 4 rodadas",
      d["alvo"] == "area" and not d.get("dano") and d["terreno"] == {"material": "piche", "duracao": 4})
r = sala()
pinta(r, "lava", [(9, 9)])
pinta(r, "agua", [(9, 8)])
h = heroi(r, "a", "Ana", "warrior", [8, 7]); h["bag"] = [{"id": "frasco_piche", "name": "Frasco de Piche", "emoji": "🛢️"}]
h["action_done"] = False
roda(r._throw_item_area(h, d, h["bag"][0], 8, 9, None))
pintadas = [t for t, m in r.materiais.items() if m == "piche"]
check("pinta o 3x3 em volta (9 casas), menos a lava e a água (7 casas)",
      (7, 8) in pintadas and (8, 9) in pintadas
      and (9, 9) not in pintadas and (9, 8) not in pintadas and len(pintadas) == 7)
r.round_num = 5
r._expirar_terrenos_inverno()
check("o piche do frasco some depois de 4 rodadas", not any(m == "piche" for m in r.materiais.values()))

print("[8] reação que falha não aborta a ação")
r = sala()
pinta(r, "piche", [(5, 5)])
ordem = []
async def _rx_teste_explode(self, tiles, origem, pend, prof):
    ordem.append("explode")
    raise RuntimeError("falha de teste")
async def _rx_teste_depois(self, tiles, origem, pend, prof):
    ordem.append("depois")
S.GameRoom._rx_teste_explode = _rx_teste_explode
S.GameRoom._rx_teste_depois = _rx_teste_depois
real = next(l for l in TR.REACOES if l["id"] == "incendiar_piche")
_saved = list(TR.REACOES)
try:
    real["ativa"] = False
    TR.REACOES.append({"id": "t1", "elemento": TR.RX_FIRE, "estado": "piche", "efeito": "_rx_teste_explode", "ativa": True})
    TR.REACOES.append({"id": "t2", "elemento": TR.RX_FIRE, "estado": "piche", "efeito": "_rx_teste_depois", "ativa": True})
    erro = None
    async def falha():
        async with r.evento_elemental({"tipo": "teste", "caster_id": "x"}):
            await r._rx_registrar(TR.RX_FIRE, [(5, 5)])
    try:
        roda(falha())
    except Exception as e:  # noqa: BLE001
        erro = e
finally:
    TR.REACOES[:] = _saved
    real["ativa"] = True
    del S.GameRoom._rx_teste_explode
    del S.GameRoom._rx_teste_depois
check("efeito que lança não propaga a exceção", erro is None)
check("as linhas seguintes ainda rodam", ordem == ["explode", "depois"])
check("a flag de reação foi restaurada", r._rx_em_reacao is False)

print("[9] fontes de magia e item")
import ast
_fonte = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
_arvore = ast.parse(_fonte)


def corpo(nome):
    for n in ast.walk(_arvore):
        if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef)) and n.name == nome:
            return ast.get_source_segment(_fonte, n)
    return None


for nome, elem in TR.FONTES_COM_REGISTRO.items():
    if nome == "_throw_item_area":      # wrapper do escopo do Fogo Grego: o corpo mora no _impl
        nome_check, nome = nome, nome + "_impl"
    else:
        nome_check = nome
    seg = corpo(nome)
    no = next((n for n in ast.walk(_arvore) if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef)) and n.name == nome), None)
    chamadas = [c for c in ast.walk(no) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "_rx_registrar"] if no is not None else []
    check(f"{nome_check} existe e chama _rx_registrar (AST)", bool(chamadas))
check("funil _aplicar_dano_alvo notifica o motor", "_rx_registrar_alvo" in (corpo("_aplicar_dano_alvo") or ""))
check("funil _dano_em_alvo notifica o motor", "_rx_registrar_alvo" in (corpo("_dano_em_alvo") or ""))
check("magias rodam dentro de um escopo elemental",
      "evento_elemental" in (corpo("_executar_magia_grimorio") or "")
      or "evento_elemental" in (corpo("handle_magia") or ""))
check("arremesso roda dentro de um escopo elemental", "evento_elemental" in (corpo("handle_throw_item") or ""))

r = sala()
pinta(r, "piche", [(8, 5), (9, 5)])
mago = heroi(r, "m", "Pedro", "mage", [3, 5])
mago["known_spells"] = ["bola_fogo"]
roda(r._executar_magia_grimorio(mago, S.GRIMORIO["bola_fogo"], {"tx": 8, "ty": 5}))
check("Bola de Fogo em piche vazio incendeia a mancha",
      any(z.get("tipo") == "chamas_piche" and z.get("ativa") for z in r.zonas_especiais))

r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 9)])
mago = heroi(r, "m", "Pedro", "mage", [3, 5])
alvo_na_poca = heroi(r, "b", "Bia", "warrior", [8, 5])
roda(r._executar_magia_grimorio(mago, S.GRIMORIO["relampago"], {"dir": [1, 0]}))
check("Relâmpago sobre a poça dispara o choque",
      any(m.get("tipo") == "choque" for m in r.msgs))

r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 9)])
mago = heroi(r, "m", "Pedro", "mage", [3, 5])
roda(r._executar_magia_grimorio(mago, S.GRIMORIO["relampago"], {"dir": [1, 0]}))
check("Relâmpago sobre poça VAZIA (sem criatura) também dispara o choque",
      any(m.get("tipo") == "choque" for m in r.msgs))

r = sala()
pinta(r, "agua", [(8, 5)])
mago = heroi(r, "m", "Pedro", "mage", [5, 5])
gob = monstro(r, "goblin", [8, 5])
roda(r._executar_magia_grimorio(mago, S.GRIMORIO["raio_congelante"], {"target_id": gob["id"]}))
check("Raio Congelante sobre a água a congela", r.materiais.get((8, 5)) == "piso_congelado")

r = sala()
pinta(r, "piche", [(8, 5)])
a = heroi(r, "a", "Ana", "warrior", [5, 5])
item = {"id": "bomba_incendiaria", "name": "Bomba Incendiária", "emoji": "💣"}
a["bag"] = [item]; a["action_done"] = False
roda(r._throw_item_area(a, S.ARREMESSAVEIS["bomba_incendiaria"], item, 8, 5, None))
check("Bomba Incendiária em piche incendeia (via _throw_item_area)",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

r = sala()
pinta(r, "piche", [(8, 5)])
a = heroi(r, "a", "Ana", "warrior", [5, 5])
a["bag"] = [dict(item)]; a["action_done"] = False
r.current_turn = "a"; r.initiative_active = False
roda(r.handle_throw_item("a", {"item_id": "bomba_incendiaria", "tx": 8, "ty": 5}))
check("Bomba Incendiária via handle_throw_item incendeia",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

r = sala()
pinta(r, "piche", [(8, 5), (9, 5)])
mago = heroi(r, "m", "Pedro", "mage", [5, 5])
roda(r._executar_prisao_chamas(mago, S.GRIMORIO["prisao_chamas"], {"tx": 8, "ty": 5, "lado": 3}))
check("Prisão de Chamas sobre piche vazio incendeia",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

r = sala()
pinta(r, "piche", [(8, 5)])
zona = {"id": "z1", "tipo": "bola_fogo", "cx": 8, "cy": 5, "raio": 1, "area_lado": None,
        "dano_r2": 4, "rodada_atual": 2, "rodadas_max": 3, "criado_em": 1, "expira_em": 9,
        "save_dif": 12, "ativa": True, "caster": "x"}
roda(r._processar_zona_bola_fogo(zona))
check("fogo residual da Bola de Fogo acende o piche que surge",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

r = sala()
pinta(r, "piche", [(8, 5)])
gob = monstro(r, "goblin", [8, 5])
roda(r._aplicar_dano_alvo(gob, 3, "fogo", "x"))
check("_aplicar_dano_alvo com fogo sobre piche incendeia", any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))
r = sala()
pinta(r, "piche", [(8, 5)])
gob = monstro(r, "goblin", [8, 5])
roda(r._dano_em_alvo(gob, 3, "fogo", "x"))
check("_dano_em_alvo com fogo sobre piche incendeia", any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

# re-entrada: o choque fere vários pelo funil e mesmo assim é UM choque, sem segunda onda
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
v1 = heroi(r, "v1", "Vi", "warrior", [6, 5]); v2 = heroi(r, "v2", "Vo", "warrior", [7, 5])
reg = []; choques = []
_orig_reg = S.GameRoom._rx_registrar; _orig_ch = S.GameRoom._rx_choque
async def _reg(self, elemento, casas, **kw):
    reg.append((elemento, self._rx_em_reacao))
    return await _orig_reg(self, elemento, casas, **kw)
async def _ch(self, *a):
    choques.append(1)
    return await _orig_ch(self, *a)
S.GameRoom._rx_registrar = _reg; S.GameRoom._rx_choque = _ch
try:
    async def choque_funil():
        async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
            await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
    roda(choque_funil())
finally:
    S.GameRoom._rx_registrar = _orig_reg; S.GameRoom._rx_choque = _orig_ch
check("dois feridos pelo choque pelo funil: um choque só", len(choques) == 1)
check("nenhum registro novo durante a reação (guarda _rx_em_reacao)",
      sum(1 for e, em in reg if em) == 0 and len(reg) == 1)
check("as duas vítimas foram feridas", v1["hp"] < v1["max_hp"] and v2["hp"] < v2["max_hp"])

# Protetor ativo: a transferência recursiva não repete a reação (cena IMPLÍCITA, sem evento_elemental)
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
ana = heroi(r, "a", "Ana", "warrior", [6, 5])
ric = heroi(r, "r", "Richard", "paladin", [6, 6])
ric["protetor_ativo"] = True; ric["protetor_alvo"] = "a"
outro = heroi(r, "o", "Otto", "warrior", [8, 5])
roda(r._dano_em_alvo(ana, 30, "eletricidade", "x"))
check("Protetor ativo: um dano elétrico na poça gera UM choque",
      sum(1 for m in r.msgs if m.get("type") == "reacao_elemental" and m.get("tipo") == "choque") == 1)
check("o Protetor realmente dividiu o dano", ric["hp"] < ric["max_hp"])

r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
ana = heroi(r, "a", "Ana", "warrior", [6, 5])
roda(r._dano_em_alvo(ana, 0, "eletricidade", "x"))
check("dano 0 elétrico na poça não reage", not any(m.get("tipo") == "choque" for m in r.msgs))

print("[9] armadilhas, armas e monstros")
for nome in ("_disparar_armadilha", "handle_attack", "_execute_one_monster_attack", "_elemental_raio_atacar"):
    check(f"{nome} roda dentro de um escopo elemental",
          "evento_elemental" in (corpo(nome) or ""))
check("armadilha incendiária registra fogo", "_rx_registrar" in (corpo("_disparar_armadilha_impl") or ""))

r = sala()
pinta(r, "piche", [(5, 5)])
r.armadilhas = [{"id": "t1", "tipo": "armadilha_incendiaria", "pos": [5, 5], "ativada": False,
                 "visivel": True, "aliada": False, "criador": None}]
pisa = heroi(r, "a", "Ana", "warrior", [5, 5])
roda(r._disparar_armadilha(pisa, r.armadilhas[0]))
check("armadilha incendiária sobre piche incendeia",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

_rd = S.random.randint
r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 10)])
ele = monstro(r, "elemental_eletrico", [4, 5])
alvo = heroi(r, "a", "Ana", "warrior", [5, 5])
vitima = heroi(r, "b", "Bia", "warrior", [9, 5])
S.random.randint = lambda a, b: b          # acerto garantido
try:
    roda(r._execute_one_monster_attack(ele, ele["attacks"][0], {"kind": "player", "obj": alvo}))
finally:
    S.random.randint = _rd
check("ataque elétrico de monstro dentro d'água choca quem está na poça",
      vitima["hp"] < vitima["max_hp"] or any(m.get("tipo") == "choque" for m in r.msgs))

r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 12)])
ele = monstro(r, "elemental_eletrico", [3, 5])
vitima = heroi(r, "b", "Bia", "warrior", [11, 5])
roda(r._elemental_raio_atacar(ele, [(4, 5), (5, 5), (6, 5)], []))
check("raio do Elemental Elétrico anuncia choque na poça da linha",
      any(m.get("tipo") == "choque" for m in r.msgs))

r = sala()
pinta(r, "piche", [(5, 5)])
ana = heroi(r, "a", "Ana", "warrior", [4, 5])
alvo_m = monstro(r, "goblin", [5, 5])
alvo_m["hp"] = alvo_m["max_hp"] = 500
alvo_m["ac"] = 1
ana["weapon"] = dict(ana.get("weapon") or {}, extra_damages=[{"die": "1d4", "type": "fire"}])
r._intro_masmorra_bloqueada = lambda: False
r._is_turn = lambda pid: True
S.random.randint = lambda a, b: b
try:
    roda(r.handle_attack("a", alvo_m["id"]))
finally:
    S.random.randint = _rd
check("arma com dano extra de fogo sobre piche incendeia",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))


print("[10] payload terrenos_temp")
r = sala()
pinta(r, "lava", [(8, 5)])
r._aplicar_camadas_terreno_inverno([(8, 5)], "lava_solidificada", "rx_1", permanente=False, expira_em=7)
pl = r._game_state_payload()
check("terrenos_temp expõe a expiração da camada", pl.get("terrenos_temp", {}).get("8,5") == 7)

print("[11] foto da masmorra")
r = sala()
pinta(r, "terra", [(5, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5)], "piche", "frasco_9", permanente=False, expira_em=9)
r.zonas_especiais.append({"id": "z1", "tipo": "chamas_piche", "tiles": [[5, 5]], "expira_em": 6, "ativa": True, "caster": None})
pacote = S.foto_empacotar({"_terrenos_inverno": r._terrenos_inverno, "zonas_especiais": r.zonas_especiais, "materiais": r.materiais})
volta = S.foto_desempacotar(pacote)
check("a camada temporária de piche sobrevive à foto", volta["_terrenos_inverno"][(5, 5)]["camadas"][0]["material"] == "piche")
check("a zona de chamas sobrevive à foto", volta["zonas_especiais"][0]["tipo"] == "chamas_piche")
check("o material sobrevive à foto", volta["materiais"][(5, 5)] == "piche")
check("categorias da foto", all(S.FOTO_SALA_CATEGORIAS.get(k) == "foto" for k in ("_terrenos_inverno", "zonas_especiais", "materiais")))
r2 = sala()
r2.materiais = volta["materiais"]; r2._terrenos_inverno = volta["_terrenos_inverno"]
r2._rebuild_materiais_index()
r2.round_num = 9
r2._expirar_terrenos_inverno()
check("após a foto, a camada ainda expira e restaura o material base",
      r2.materiais.get((5, 5)) == "terra" and (5, 5) not in r2._terrenos_inverno)

print("[12] onda de correções da revisão final")
# I1: relâmpago sobre água sem criatura na linha fere quem está na poça
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 8)] + [(5, 6)])
mago = heroi(r, "m", "Pedro", "mage", [2, 5])
fora_linha = heroi(r, "f", "Fora", "warrior", [5, 6])
async def i1():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "m"}):
        await r._executar_relampago(mago, S.GRIMORIO["relampago"], {"dir": [1, 0]}, 1.0)
roda(i1())
check("I1 relâmpago sem acerto: quem está na poça fora da linha toma o choque",
      fora_linha["hp"] < fora_linha["max_hp"])

r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 12)])
ele = monstro(r, "elemental_eletrico", [3, 5])
vitima = heroi(r, "b", "Bia", "warrior", [11, 5])
roda(r._elemental_raio_atacar(ele, [(4, 5), (5, 5), (6, 5)], []))
check("I1 raio sem acerto: a poça fere", vitima["hp"] < vitima["max_hp"])

# I2: congelar água grava a flag que os prólogos consomem
r = sala()
pinta(r, "agua", [(5, 5), (6, 5)])
mon = monstro(r, "goblin", [5, 5])
bia = heroi(r, "b", "Bia", "warrior", [6, 5])
async def i2():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x", "cd": 99}):
        await r._rx_registrar(S.DMG_COLD, [(5, 5), (6, 5)])
roda(i2())
check("I2 monstro congelado leva turbilhao_perde_movimento", mon.get("turbilhao_perde_movimento") is True)
check("I2 herói congelado leva turbilhao_perde_movimento", bia.get("turbilhao_perde_movimento") is True)

# I3: criatura em chamas que entra em piche leva o dano UMA vez
r = sala()
pinta(r, "piche", [(5, 5), (6, 5)])
g = heroi(r, "g", "Gus", "warrior", [5, 5]); g["em_chamas_rodadas"] = 2
roda(r._aplicar_lava_se_pisar(g))
hp_ign = g["hp"]
roda(r._verificar_entrada_zona_molochus(g, 5, 5))
check("I3 ignição fere", hp_ign < g["max_hp"])
check("I3 entrada no mesmo passo não fere de novo", g["hp"] == hp_ign)

# I4: descarga da tempestade num escopo só: um choque para a poça toda
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
a = heroi(r, "a", "Ana", "warrior", [4, 5]); b = heroi(r, "b", "Bia", "warrior", [5, 5])
c = heroi(r, "c", "Cris", "warrior", [8, 5])
zt = {"id": "t1", "tipo": "tempestade_ciclones", "ativa": True, "cx": 4, "cy": 5, "lado": 2,
      "tiles": [[4, 5], [5, 5]], "ciclones": [], "dano_raio": "1d8", "save_dif": 12, "dmg_mult": 1,
      "caster": "x"}
r.zonas_especiais.append(zt)
roda(r._tempestade_descarga(zt))
check("I4 descarga: um choque só para a poça",
      sum(1 for m in r.msgs if m.get("tipo") == "choque") == 1)
check("I4 descarga: o não atingido na poça foi ferido", c["hp"] < c["max_hp"])

# I5: _queimando reconhece a mancha de piche em chamas
r = sala()
pinta(r, "piche", [(5, 5), (6, 5)])
q = heroi(r, "q", "Quê", "warrior", [5, 5])
r.zonas_especiais.append({"id": "z9", "tipo": "chamas_piche", "tiles": [[5, 5], [6, 5]], "ativa": True,
                          "expira_em": 9, "caster": None})
check("I5 _queimando: em cima de piche em chamas", r._queimando(q) is True)
q["pos"] = [9, 9]
check("I5 _queimando: fora da mancha não", r._queimando(q) is False)
voa = heroi(r, "vv", "Vo", "warrior", [5, 5]); voa["voo"] = True; voa["altura"] = 3
check("I5 _queimando: voador sobre a mancha não", r._queimando(voa) is False)

# T3(b): a camada de piche vive até o fim da zona de chamas
r = sala()
pinta(r, "terra", [(5, 5), (6, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5), (6, 5)], "piche", "frasco_1", permanente=False, expira_em=5)
r.round_num = 4
async def t3():
    async with r.evento_elemental({"tipo": "item", "id": "bomba_incendiaria", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(5, 5)])
roda(t3())
zona = next(z for z in r.zonas_especiais if z.get("tipo") == "chamas_piche")
check("T3b a camada de piche é estendida até o fim da zona",
      all(c["expira_em"] >= zona["expira_em"] for t in ((5, 5), (6, 5))
          for c in r._terrenos_inverno[t]["camadas"] if c["material"] == "piche"))
r.round_num = 6
r._expirar_terrenos_inverno()
check("T3b rodada 6: o piche ainda está lá (zona ativa)", r.materiais[(5, 5)] == "piche")
r.round_num = zona["expira_em"]
roda(r._processar_zonas_turno())
check("T3b fim da zona: volta a terra", r.materiais[(5, 5)] == "terra")

# M1: Chamado do Inverno permanente guarda o material BASE, não a camada temporária
r = sala()
pinta(r, "terra", [(5, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5)], "piche", "frasco_2", permanente=False, expira_em=9)
cler = heroi(r, "cl", "Lewis", "cleric", [2, 2])
pre = {"terreno": "piso_congelado", "permanente": True, "nivel": 1, "dist": 3,
       "cx": 5, "cy": 5, "lado": 1, "tiles": [(5, 5)]}
roda(r._executar_chamado_inverno(cler, S.GRIMORIO["chamado_inverno"], {"_chamado_inverno_preflight": pre}, 0))
zi = next(z for z in r.zonas_especiais if z.get("tipo") == "chamado_inverno")
check("M1 material_bases usa o material base da casa", zi["material_bases"]["5,5"] == "terra")

# M2: terrenos_temp usa a camada do topo
r = sala()
pinta(r, "agua", [(5, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5)], "lava", "ira", permanente=False, expira_em=9)
r._aplicar_camadas_terreno_inverno([(5, 5)], "lava_solidificada", "rx", permanente=False, expira_em=5)
check("M2 terrenos_temp = expiração da camada do topo", r._serializar_terrenos_temp().get("5,5") == 5)

# M3: alvo morto em cascata não leva dano nem congelamento
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
vivo_h = heroi(r, "v", "Vivo", "warrior", [6, 5])
morto = monstro(r, "goblin", [7, 5]); morto["hp"] = 0
r._alvos_no_inverno = lambda tiles: [morto, vivo_h]
chamados = []
_od, _os = r._dano_em_alvo, r._save_mostrado
async def _dano_esp(alvo, *a, **k):
    chamados.append(("dano", alvo.get("id")))
    return await _od(alvo, *a, **k)
async def _save_esp(alvo, *a, **k):
    chamados.append(("save", alvo.get("id")))
    return await _os(alvo, *a, **k)
r._dano_em_alvo = _dano_esp; r._save_mostrado = _save_esp
async def m3():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(m3())
async def m3b():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_COLD, [(3, 5)])
roda(m3b())
check("M3 alvo morto não é salvo nem ferido", not any(i == morto["id"] for _, i in chamados))
check("M3 alvo vivo continua sendo tratado", any(i == "v" for _, i in chamados))

# M4: entrada em chamas de piche considera o footprint inteiro
r = sala()
pinta(r, "piche", [(5, 6)])
grande = monstro(r, "goblin", [4, 5]); grande["size"] = [2, 2]
r.zonas_especiais.append({"id": "z8", "tipo": "chamas_piche", "tiles": [[5, 6]], "ativa": True,
                          "expira_em": 9, "caster": None})
hp0 = grande["hp"]
roda(r._verificar_entrada_zona_molochus(grande, 4, 5))
check("M4 criatura grande com a casa de trás na mancha sofre na entrada", grande["hp"] < hp0)

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
