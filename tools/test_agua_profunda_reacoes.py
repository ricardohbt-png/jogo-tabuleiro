"""Reações elementais na água PROFUNDA e no redemoinho. Roda da raiz: python -X utf8 tools/test_agua_profunda_reacoes.py
Regra (design aprovado em chat): eletricidade conduz por TODO o corpo d'água conectado (rasa, profunda,
redemoinho e redemoinho profundo); o frio congela água profunda e redemoinho como a rasa (piso_congelado,
3 rodadas, Reflexos), e congelar um redemoinho LIBERTA quem estava preso.
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
    r = S.GameRoom("PROFUNDA")
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


async def golpe(r, elemento, casas, dano=10, caster="x", atingidos=()):
    async with r.evento_elemental({"tipo": "magia", "id": "m", "caster_id": caster}):
        await r._rx_registrar(elemento, casas, dano=dano, atingidos=set(atingidos))


def fixa_save(r, passa):
    async def save(alvo, tipo, cd, *a, **k):
        return passa, 10, 0, 10
    r._save_mostrado = save


def mat(r, x, y):
    return r.materiais.get((x, y))


print("[1] tabela")
choque = next(l for l in TR.REACOES if l["id"] == "choque_na_poca")
congelar = next(l for l in TR.REACOES if l["id"] == "congelar_agua")
check("choque e congelar agem sobre qualquer água (estado agua)",
      choque["estado"] == "agua" and congelar["estado"] == "agua")

print("[2] choque corre por TODO o corpo d'água")
r = sala()
fixa_save(r, False)
pinta(r, "agua", [(3, 5), (4, 5)])
pinta(r, "agua_profunda", [(5, 5), (6, 5)])
pinta(r, "rodamoinho", [(7, 5)])
pinta(r, "rodamoinho_profundo", [(8, 5)])
a = heroi(r, "a", "Ana", "mage", [3, 5])         # atingida na rasa
b = heroi(r, "b", "Bia", "warrior", [6, 5])       # na profunda
c = heroi(r, "c", "Cris", "warrior", [7, 5])      # no redemoinho
d = heroi(r, "d", "Duda", "warrior", [8, 5])      # no redemoinho profundo
e = heroi(r, "e", "Edu", "warrior", [8, 9])       # fora d'água
roda(golpe(r, S.DMG_LIGHTNING, [(3, 5)], dano=12, atingidos={"a"}))
check("na água profunda toma o choque", b["hp"] < 60)
check("no redemoinho toma o choque", c["hp"] < 60)
check("no redemoinho profundo toma o choque", d["hp"] < 60)
check("fora d'água não toma", e["hp"] == 60)
check("quem levou o golpe não repete", a["hp"] == 60)
ex = [m for m in r.msgs if m.get("type") == "reacao_elemental" and m.get("tipo") == "choque"]
check("um choque com as 6 casas d'água", len(ex) == 1 and len(ex[0]["casas"]) == 6)

print("[3] raio que só cai na água profunda também conduz")
r = sala()
fixa_save(r, False)
pinta(r, "agua_profunda", [(x, 5) for x in range(4, 9)])
f = heroi(r, "f", "Fabi", "warrior", [8, 5])
roda(golpe(r, S.DMG_LIGHTNING, [(4, 5)], dano=12))
check("criatura na outra ponta da profunda toma o choque", f["hp"] < 60)

print("[4] frio congela água profunda e redemoinho")
for material in ("agua_profunda", "rodamoinho", "rodamoinho_profundo"):
    r = sala()
    fixa_save(r, True)
    pinta(r, material, [(6, 6)])
    roda(golpe(r, S.DMG_COLD, [(6, 6)], dano=8))
    check(f"{material} congela em piso_congelado", mat(r, 6, 6) == "piso_congelado")
    check(f"{material}: camada temporária guarda o material de baixo",
          r._terrenos_inverno.get((6, 6), {}).get("base") == material)
    r.round_num += TR.RX_DURACAO_GELO
    r._expirar_terrenos_inverno()
    check(f"{material} volta ao fim de {TR.RX_DURACAO_GELO} rodadas", mat(r, 6, 6) == material)

print("[5] Reflexos: quem falha perde o movimento")
r = sala()
fixa_save(r, False)
pinta(r, "agua_profunda", [(6, 6)])
g = heroi(r, "g", "Gabi", "warrior", [6, 6])
g["moves_left"] = 6
roda(golpe(r, S.DMG_COLD, [(6, 6)], dano=8))
check("falhou no Reflexos: movimento zerado", g["moves_left"] == 0 and g.get("movimento_perdido"))
r = sala()
fixa_save(r, True)
pinta(r, "agua_profunda", [(6, 6)])
g = heroi(r, "g", "Gabi", "warrior", [6, 6])
g["moves_left"] = 6
roda(golpe(r, S.DMG_COLD, [(6, 6)], dano=8))
check("passou no Reflexos: segue com o movimento", g["moves_left"] == 6)

print("[6] congelar o redemoinho LIBERTA quem estava preso")
r = sala()
fixa_save(r, True)
pinta(r, "rodamoinho", [(6, 6)])
pinta(r, "rodamoinho_profundo", [(9, 6)])
p1 = heroi(r, "p1", "Pri", "warrior", [6, 6])
p1["rodamoinho_preso"] = True
p2 = heroi(r, "p2", "Pru", "warrior", [9, 6])
p2["rodamoinho_profundo_preso"] = True
roda(golpe(r, S.DMG_COLD, [(6, 6), (9, 6)], dano=8))
check("preso no redemoinho foi solto", not p1.get("rodamoinho_preso"))
check("preso no redemoinho profundo foi solto", not p2.get("rodamoinho_profundo_preso"))

print("[7] fogo derrete o gelo de volta à água profunda")
r = sala()
fixa_save(r, True)
pinta(r, "agua_profunda", [(6, 6), (7, 6)])
roda(golpe(r, S.DMG_COLD, [(6, 6), (7, 6)], dano=8))
check("pré-condição: congelado", mat(r, 6, 6) == "piso_congelado")
roda(golpe(r, S.DMG_FIRE, [(6, 6)], dano=5))
check("derreteu de volta à água profunda (a base)", mat(r, 6, 6) == "agua_profunda" and mat(r, 7, 6) == "agua_profunda")

print("[8] a água rasa continua igual")
r = sala()
fixa_save(r, True)
pinta(r, "agua", [(6, 6)])
roda(golpe(r, S.DMG_COLD, [(6, 6)], dano=8))
check("rasa congela como antes", mat(r, 6, 6) == "piso_congelado")

print("[9] cliente e idiomas")
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(*p):
    with open(os.path.join(raiz, *p), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")
re_js = ler("src", "reacoesElementais.js")
itf = ler("src", "lang", "interface.js")
check("tooltip: água profunda e redemoinho usam o mesmo texto da água",
      "agua_profunda" in re_js and "ui.reacao.casa.agua_fogo" not in re_js)
chave = itf.split('"ui.reacao.casa.agua"')[1].split("}")[0]
check("texto da água cita eletricidade e congelamento (PT/EN)",
      "conduz" in chave and "congela" in chave and "conducts" in chave and "freezes" in chave)

print("\n" + "=" * 62)
print(f"  {PASS} passaram, {FAIL} falharam")
print("=" * 62)
sys.exit(1 if FAIL else 0)
