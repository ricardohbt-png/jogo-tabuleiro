"""Reação elemental Fogo + gás (explosão). Roda da raiz: python -X utf8 tools/test_fogo_gas.py
Regra: fogo atingindo casas cobertas por uma zona de gás ativa (Câmara de Gás ou Nuvem de Gás)
explode a zona inteira: 2d6 de fogo em quem estiver nas casas, Reflexos CD 17 para metade.
O gás é consumido. Spec (design aprovado em chat): docs/superpowers/specs/2026-10-14-fogo-gas-design.md
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
    """Duas salas de chão lado a lado (0: x1-10, 1: x11-20), 'playing', sem rede."""
    r = S.GameRoom("GAS")
    r.msgs = []
    r.narr = []
    r.saves = []

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
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 10, "h": 12, "locked": False},
               {"id": 1, "x": 11, "y": 1, "w": 10, "h": 12, "locked": False}]
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


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    m["hp"] = m["max_hp"] = 60
    r.monsters[m["id"]] = m
    return m


def camara(r, sala_id=0, duracao=4):
    z = {"id": f"camara_gas_t{sala_id}", "tipo": "camara_gas", "room_id": sala_id,
         "duracao": duracao, "ativa": True, "created_round": r.round_num}
    r.zonas_especiais.append(z)
    return z


def fixa(r, dado=8, passa=False):
    """Dado fixo e resultado do save fixo; registra a CD pedida em r.saves."""
    r._rolar_dado = lambda expr: dado

    async def save(alvo, tipo, cd, *a, **k):
        r.saves.append((tipo, cd))
        return passa, 10, 0, 10
    r._save_mostrado = save


def roda(coro):
    return asyncio.run(coro)


async def fogo_em(r, casas, caster="x"):
    async with r.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": caster}):
        await r._rx_registrar(S.DMG_FIRE, casas, dano=5)


print("[1] tabela e constantes")
ids = [l["id"] for l in TR.REACOES]
check("explodir_gas está na tabela, ativa, para fogo",
      any(l["id"] == "explodir_gas" and l["ativa"] and l["elemento"] == TR.RX_FIRE
          and l["estado"] == "gas" and l["efeito"] == "_rx_explodir_gas" for l in TR.REACOES))
check("dano 2d6 e CD 17", TR.RX_GAS_DANO == "2d6" and TR.RX_GAS_CD == 17)
check("tiles de piso espelham FLOOR/DOOR do servidor", tuple(TR.RX_PISO) == (S.FLOOR, S.DOOR))

print("[2] Câmara de Gás explode a sala inteira")
r = sala()
fixa(r, dado=8, passa=False)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
b = heroi(r, "b", "Bia", "warrior", [9, 9])
fora = heroi(r, "f", "Fora", "warrior", [15, 5])        # na sala 1, sem gás
m = monstro(r, "goblin", [6, 6])
z = camara(r)
roda(fogo_em(r, [(3, 3)]))
check("quem está na sala com gás sofre 8 de fogo (falhou no save)",
      a["hp"] == 52 and b["hp"] == 52 and m["hp"] == 52)
check("quem está na outra sala não sofre", fora["hp"] == 60)
check("save de Reflexos com CD 17", r.saves and all(s == ("reflexos", 17) for s in r.saves))
check("a zona de gás foi consumida", z["ativa"] is False)
ex = [mm for mm in r.msgs if mm.get("type") == "reacao_elemental" and mm.get("tipo") == "explosao_gas"]
check("um broadcast explosao_gas com as casas da sala", len(ex) == 1 and len(ex[0]["casas"]) == 10 * 12)
check("narração da explosão", any("reacao.explosao_gas" in t or "xplo" in t for t in r.narr))

print("[3] save bem-sucedido = metade")
r = sala()
fixa(r, dado=9, passa=True)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
camara(r)
roda(fogo_em(r, [(3, 3)]))
check("9 de dano vira 4 (metade, arredondada para baixo)", a["hp"] == 56)

print("[4] fogo fora das casas do gás não explode")
r = sala()
fixa(r)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
z = camara(r)
roda(fogo_em(r, [(15, 5)]))           # casa da sala 1, sem gás
check("zona continua ativa e ninguém se feriu", z["ativa"] and a["hp"] == 60)
check("nenhum broadcast de explosão", not any(mm.get("tipo") == "explosao_gas" for mm in r.msgs))
r = sala()
fixa(r)
heroi(r, "a", "Ana", "warrior", [3, 3])
z = camara(r)
z["ativa"] = False                      # gás já dissipado
roda(fogo_em(r, [(3, 3)]))
check("gás inativo não explode", not any(mm.get("tipo") == "explosao_gas" for mm in r.msgs))

print("[5] só fogo detona (frio e raio não)")
r = sala()
fixa(r)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
z = camara(r)

async def raio_e_gelo():
    async with r.evento_elemental({"tipo": "magia", "id": "x", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 3)], dano=5)
        await r._rx_registrar(S.DMG_COLD, [(3, 3)], dano=5)
roda(raio_e_gelo())
check("gás intacto sob raio e gelo", z["ativa"] and a["hp"] == 60)

print("[6] dano comum de fogo (funil) também detona")
r = sala()
fixa(r)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
z = camara(r)
roda(r._dano_em_alvo(a, 3, "fire"))
check("a explosão veio do fogo no herói; ele toma o 3 do golpe + 8 do gás",
      z["ativa"] is False and a["hp"] == 60 - 3 - 8)

print("[7] a água protege do fogo também na explosão")
r = sala()
fixa(r, dado=8, passa=False)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
for x in range(2, 5):
    r.materiais[(x, 3)] = "agua"
r._rebuild_materiais_index()
camara(r)
roda(fogo_em(r, [(9, 9)]))
check("na água, 8 de fogo vira 4", a["hp"] == 56)

print("[8] morrer na explosão não quebra a cascata")
r = sala()
fixa(r, dado=12, passa=False)
a = heroi(r, "a", "Ana", "warrior", [3, 3])
a["hp"] = 5
b = heroi(r, "b", "Bia", "warrior", [4, 4])
camara(r)
roda(fogo_em(r, [(3, 3)]))
check("Ana morreu e Bia sofreu normalmente", a["hp"] <= 0 and b["hp"] == 48)

print("[9] explosão detona piche na sala (encadeia)")
r = sala()
fixa(r)
heroi(r, "a", "Ana", "warrior", [3, 3])
r.materiais[(7, 7)] = "piche"
r._rebuild_materiais_index()
camara(r)
roda(fogo_em(r, [(3, 3)]))
check("o piche da sala pegou fogo",
      any(z.get("tipo") == "chamas_piche" and z.get("ativa") for z in r.zonas_especiais))

print("[10] Nuvem de Gás cria zona e explode só o raio 1")
r = sala()
fixa(r)
a = heroi(r, "a", "Ana", "warrior", [5, 5])
longe = heroi(r, "l", "Longe", "warrior", [9, 9])
arm = {"id": "n1", "tipo": "nuvem_gas", "pos": [5, 5], "ativada": False}
roda(r._aplicar_armadilha_area(arm, S.ARMADILHAS["nuvem_gas"]))
nuvens = [z for z in r.zonas_especiais if z.get("tipo") == "nuvem_gas"]
check("uma zona nuvem_gas de 3 rodadas, 9 casas",
      len(nuvens) == 1 and nuvens[0]["duracao"] == 3 and nuvens[0]["ativa"]
      and len(nuvens[0]["tiles"]) == 9)
hp_a = a["hp"]
roda(fogo_em(r, [(6, 6)]))
check("fogo numa casa da nuvem explode", nuvens[0]["ativa"] is False and a["hp"] == hp_a - 8)
check("quem está fora das 9 casas não sofre", longe["hp"] == 60)
ex = [mm for mm in r.msgs if mm.get("tipo") == "explosao_gas"]
check("explosão anunciou 9 casas", len(ex) == 1 and len(ex[0]["casas"]) == 9)

print("[11] duração: a nuvem se dissipa após 3 rodadas, a câmara segue a regra dela")
r = sala()
fixa(r)
heroi(r, "a", "Ana", "warrior", [5, 5])
arm = {"id": "n2", "tipo": "nuvem_gas", "pos": [5, 5], "ativada": False}
roda(r._aplicar_armadilha_area(arm, S.ARMADILHAS["nuvem_gas"]))
n = next(z for z in r.zonas_especiais if z.get("tipo") == "nuvem_gas")
for _ in range(3):
    roda(r._processar_zonas_turno()) if hasattr(r, "_processar_zonas_turno") else None
check("nuvem inativa depois de 3 ticks", hasattr(r, "_processar_zonas_turno") and n["ativa"] is False)

print("[12] cliente e idiomas")
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(*p):
    with open(os.path.join(raiz, *p), encoding="utf-8") as f:
        return f.read()
re_js = ler("src", "reacoesElementais.js")
game = ler("game.js").replace("\r\n", "\n")
narr = ler("src", "lang", "narracao.js")
check("estilo explosao_gas no módulo do cliente", "explosao_gas:" in re_js)
check("som da explosão tocado na reação", "tipo === 'explosao_gas') sfx('explosao'" in game)
check("narração PT/EN", '"narracao.reacao.explosao_gas"' in narr
      and '"en"' in narr.split('"narracao.reacao.explosao_gas"')[1].split("}")[0]
      and '"pt"' in narr.split('"narracao.reacao.explosao_gas"')[1].split("}")[0])
check("nuvem_gas é zona de fumaça no cliente", "z.tipo === 'nuvem_gas'" in game.split("function _ehZonaFumaca")[1][:300])

print("\n" + "=" * 62)
print(f"  {PASS} passaram, {FAIL} falharam")
print("=" * 62)
sys.exit(1 if FAIL else 0)
