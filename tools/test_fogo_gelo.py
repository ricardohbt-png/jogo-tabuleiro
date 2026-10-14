"""Reação elemental Fogo + gelo (derretimento). Roda da raiz: python -X utf8 tools/test_fogo_gelo.py
Regra (design aprovado em chat): fogo atingindo gelo (`piso_congelado`) ou neve (`planicie_nevada`)
derrete o gelo CONECTADO (raio 4 do ponto atingido, teto 24 casas), sem dano. Camada temporária volta ao
que havia embaixo; gelo permanente/do mapa vira ÁGUA RASA permanente. Quem estava em chamas na região
derretida é apagado (já virou água).
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
import terrain_reactions as TR  # noqa: E402

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
    r = S.GameRoom("GELO")
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
    for y in range(1, 20):
        for x in range(1, 30):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 29, "h": 19, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def heroi(r, pid, nome, classe, pos):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    h["hp"] = h["max_hp"] = 60
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def pinta(r, material, tiles):
    for t in tiles:
        r.materiais[tuple(t)] = material
    r._rebuild_materiais_index()


def roda(coro):
    return asyncio.run(coro)


async def fogo_em(r, casas, caster="x"):
    async with r.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": caster}):
        await r._rx_registrar(S.DMG_FIRE, casas, dano=5)


def mat(r, x, y):
    return r.materiais.get((x, y))


print("[1] tabela")
linha = next((l for l in TR.REACOES if l["id"] == "derreter_gelo"), None)
check("derreter_gelo ativa, fogo, estado gelo, efeito _rx_derreter_gelo",
      linha and linha["ativa"] and linha["elemento"] == TR.RX_FIRE and linha["estado"] == "gelo"
      and linha["efeito"] == "_rx_derreter_gelo")
check("constantes: raio 4 e teto 24", TR.RX_DERRETER_RAIO == 4 and TR.RX_DERRETER_TETO == 24)

print("[2] gelo permanente/do mapa vira água rasa permanente")
r = sala()
pinta(r, "piso_congelado", [(x, 5) for x in range(5, 10)])      # fileira de 5 (dentro do raio 4)
roda(fogo_em(r, [(5, 5)]))
check("a fileira conectada inteira virou água", all(mat(r, x, 5) == "agua" for x in range(5, 10)))
check("água rasa de verdade (_water_tile_kind)", r._water_tile_kind(7, 5) == "agua")
check("não é camada temporária (nada para expirar)", not r._terrenos_inverno)
ex = [m for m in r.msgs if m.get("type") == "reacao_elemental" and m.get("tipo") == "derreter"]
check("um broadcast derreter com as 5 casas", len(ex) == 1 and len(ex[0]["casas"]) == 5)
check("narração do derretimento", any("derreter" in t or "derret" in t.lower() for t in r.narr))
r.round_num = 50
r._expirar_terrenos_inverno()
check("a água permanece depois de muitas rodadas", mat(r, 7, 5) == "agua")

print("[3] raio 4 e conectividade")
r = sala()
pinta(r, "piso_congelado", [(x, 5) for x in range(2, 20)])      # fileira longa
roda(fogo_em(r, [(10, 5)]))
check("até 4 casas do impacto derrete", all(mat(r, x, 5) == "agua" for x in range(6, 15)))
check("mais longe que 4 continua gelo", mat(r, 5, 5) == "piso_congelado" and mat(r, 15, 5) == "piso_congelado")
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5), (9, 5), (10, 5)])   # dois trechos separados
roda(fogo_em(r, [(5, 5)]))
check("trecho desconectado não derrete", mat(r, 6, 5) == "agua" and mat(r, 9, 5) == "piso_congelado")

print("[4] teto de 24 casas")
r = sala()
pinta(r, "piso_congelado", [(x, y) for x in range(5, 14) for y in range(5, 14)])   # 9x9 = 81
roda(fogo_em(r, [(9, 9)]))
derretidas = sum(1 for x in range(5, 14) for y in range(5, 14) if mat(r, x, y) == "agua")
check("no máximo 24 casas derretem", 0 < derretidas <= 24)

print("[5] neve também derrete")
r = sala()
pinta(r, "planicie_nevada", [(4, 4), (5, 4), (4, 5)])
roda(fogo_em(r, [(4, 4)]))
check("planície nevada vira água", all(mat(r, x, y) == "agua" for x, y in ((4, 4), (5, 4), (4, 5))))

print("[6] gelo temporário volta ao que havia embaixo")
r = sala()
pinta(r, "agua", [(x, 7) for x in range(5, 9)])
r._aplicar_camadas_terreno_inverno([(x, 7) for x in range(5, 9)], "piso_congelado", "gelo1",
                                   permanente=False, expira_em=r.round_num + 3)
check("pré-condição: está congelado", all(mat(r, x, 7) == "piso_congelado" for x in range(5, 9)))
roda(fogo_em(r, [(5, 7)]))
check("poça congelada derrete de volta à água (a base)", all(mat(r, x, 7) == "agua" for x in range(5, 9)))
check("a camada temporária foi removida", not r._terrenos_inverno)
r = sala()
r._aplicar_camadas_terreno_inverno([(6, 6)], "piso_congelado", "gelo2", permanente=False, expira_em=r.round_num + 3)
roda(fogo_em(r, [(6, 6)]))
check("gelo temporário sobre chão comum volta a chão (sem água)", mat(r, 6, 6) is None)
r = sala()
pinta(r, "planicie_nevada", [(6, 6)])
r._aplicar_camadas_terreno_inverno([(6, 6)], "piso_congelado", "gelo3", permanente=False, expira_em=r.round_num + 3)
roda(fogo_em(r, [(6, 6)]))
check("gelo temporário sobre neve do mapa: a base também é gelo, então vira água", mat(r, 6, 6) == "agua")
check("sem registro pendente", (6, 6) not in r._terrenos_inverno)

print("[7] só fogo derrete")
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5)])

async def frio_e_raio():
    async with r.evento_elemental({"tipo": "magia", "id": "x", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_COLD, [(5, 5)], dano=5)
        await r._rx_registrar(S.DMG_LIGHTNING, [(5, 5)], dano=5)
roda(frio_e_raio())
check("frio e raio não derretem", mat(r, 5, 5) == "piso_congelado" and mat(r, 6, 5) == "piso_congelado")

print("[8] fogo em casa sem gelo não faz nada")
r = sala()
pinta(r, "piso_congelado", [(5, 5)])
roda(fogo_em(r, [(15, 15)]))
check("gelo longe do impacto intacto e sem broadcast", mat(r, 5, 5) == "piso_congelado"
      and not any(m.get("tipo") == "derreter" for m in r.msgs))

print("[9] ponte: casa sob ponte é ignorada")
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5)])
r.pontes = [{"id": "p1", "tiles": [[6, 5]]}] if hasattr(r, "pontes") else None
sob = r._ponte_em(6, 5)
roda(fogo_em(r, [(5, 5)]))
check("casa fora da ponte derrete", mat(r, 5, 5) == "agua")
check("casa sob a ponte (se houver) não vira água", (not sob) or mat(r, 6, 5) == "piso_congelado")

print("[10] quem está em chamas na região derretida é apagado")
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5)])
h = heroi(r, "a", "Ana", "warrior", [6, 5])
h["em_chamas_rodadas"] = 3
h["chamas_agua_apaga"] = True
roda(fogo_em(r, [(5, 5)]))
check("chamas apagadas na água recém-derretida", h.get("em_chamas_rodadas", 0) == 0)
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5)])
g = heroi(r, "g", "Gus", "warrior", [6, 5])
g["em_chamas_rodadas"] = 3
g["chamas_agua_apaga"] = False       # Fogo Grego não se apaga
roda(fogo_em(r, [(5, 5)]))
check("Fogo Grego continua queimando", g.get("em_chamas_rodadas", 0) == 3)

print("[11] fogo comum pelo funil de dano também derrete")
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5)])
h = heroi(r, "a", "Ana", "warrior", [5, 5])
roda(r._dano_em_alvo(h, 3, "fire"))
check("o fogo no herói em cima do gelo derreteu a região", mat(r, 5, 5) == "agua" and mat(r, 6, 5) == "agua")

print("[12] sem dano a quem estava no gelo")
r = sala()
pinta(r, "piso_congelado", [(5, 5), (6, 5)])
h = heroi(r, "a", "Ana", "warrior", [6, 5])
hp0 = h["hp"]
roda(fogo_em(r, [(5, 5)]))
check("a reação em si não causa dano", h["hp"] == hp0)

print("[13] cliente e idiomas")
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(*p):
    with open(os.path.join(raiz, *p), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")
re_js = ler("src", "reacoesElementais.js")
game = ler("game.js")
narr = ler("src", "lang", "narracao.js")
itf = ler("src", "lang", "interface.js")
check("estilo derreter no módulo do cliente", "derreter:" in re_js)
check("som reaproveitado (fumaca_chiado) na reação", "tipo === 'derreter') sfx('fumaca_chiado'" in game)
check("desenho 2D próprio do derretimento", "a.tipo === 'derreter'" in game)
check("narração PT/EN", '"narracao.reacao.derreter"' in narr
      and '"en"' in narr.split('"narracao.reacao.derreter"')[1].split("}")[0]
      and '"pt"' in narr.split('"narracao.reacao.derreter"')[1].split("}")[0])
check("tooltip da casa de gelo PT/EN", '"ui.reacao.casa.gelo"' in itf
      and '"en"' in itf.split('"ui.reacao.casa.gelo"')[1].split("}")[0])

print("\n" + "=" * 62)
print(f"  {PASS} passaram, {FAIL} falharam")
print("=" * 62)
sys.exit(1 if FAIL else 0)
