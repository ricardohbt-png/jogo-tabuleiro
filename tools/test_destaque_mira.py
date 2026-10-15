"""Destaque de mira das reações elementais: paridade SERVIDOR x CLIENTE.
Roda da raiz: python -X utf8 tools/test_destaque_mira.py

`ReacoesElementais.preverReacoes` (src/reacoesElementais.js) espelha as regras de terrain_reactions.py. Aqui os MESMOS
cenários rodam no motor real (quem emite `reacao_elemental`) e no módulo JS (via node) e as casas precisam bater,
inclusive nos tetos de casas, onde a ordem de visita do BFS decide quais entram.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
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
    r = S.GameRoom("MIRA")
    r.msgs = []

    async def noop(*a, **k):
        pass

    async def bc(msg, *a, **k):
        r.msgs.append(msg)
    r.gm_say = noop; r.broadcast = bc; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 20):
        for x in range(1, 30):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 10, "h": 19, "locked": False},
               {"id": 1, "x": 11, "y": 1, "w": 19, "h": 19, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def pinta(r, material, tiles):
    for t in tiles:
        r.materiais[tuple(t)] = material
    r._rebuild_materiais_index()


ELEM = {"fire": S.DMG_FIRE, "cold": S.DMG_COLD, "lightning": S.DMG_LIGHTNING}
TIPO_SERVIDOR = {"choque": "choque", "incendio": "ignicao", "congelar": "congelar", "crosta": "congelar",
                 "explosao_gas": "gas", "derreter": "derreter"}


def estado(r):
    return {"materiais": {f"{x},{y}": m for (x, y), m in r.materiais.items()},
            "zonas_especiais": r.zonas_especiais, "rooms": r.rooms, "tiles": r.tiles,
            "pontes": [], "players": [], "monsters": []}


def servidor(r, elemento, casas):
    r.msgs.clear()

    async def golpe():
        async with r.evento_elemental({"tipo": "magia", "id": "m", "caster_id": "x"}):
            await r._rx_registrar(ELEM[elemento], casas, dano=5)
    asyncio.run(golpe())
    out = {}
    for m in r.msgs:
        if m.get("type") == "reacao_elemental" and m.get("tipo") in TIPO_SERVIDOR:
            out.setdefault(TIPO_SERVIDOR[m["tipo"]], set()).update(tuple(c) for c in m["casas"])
    return out


def camara(r, sala_id):
    r.zonas_especiais.append({"id": f"camara_{sala_id}", "tipo": "camara_gas", "room_id": sala_id,
                              "duracao": 4, "ativa": True, "created_round": 1})


def nuvem(r, cx, cy):
    tiles = [list(t) for t in r._rx_tiles_area(cx, cy, raio=1)]
    r.zonas_especiais.append({"id": f"nuvem_{cx}_{cy}", "tipo": "nuvem_gas", "cx": cx, "cy": cy,
                              "tiles": tiles, "duracao": 3, "ativa": True, "created_round": 1})


def quadro(x0, y0, w, h):
    return [(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)]


CENARIOS = []


def cenario(nome, elemento, casas, prep):
    r = sala()
    prep(r)
    CENARIOS.append({"nome": nome, "elemento": elemento, "casas": [list(c) for c in casas],
                     "estado": estado(r), "r": r})


# ⚡ choque
def _p1(r):
    pinta(r, "agua", [(3, 5), (4, 5)]); pinta(r, "agua_profunda", [(5, 5), (6, 5)])
    pinta(r, "rodamoinho", [(7, 5)]); pinta(r, "rodamoinho_profundo", [(8, 5)])
cenario("choque: corpo d'água misto", "lightning", [(3, 5)], _p1)
cenario("choque: teto de 24 casas (poça 9x9)", "lightning", [(9, 9)], lambda r: pinta(r, "agua", quadro(5, 5, 9, 9)))
cenario("choque: raio 6 numa fileira longa", "lightning", [(4, 5)], lambda r: pinta(r, "agua", [(x, 5) for x in range(2, 25)]))
cenario("choque: linha de raio sobre duas poças separadas", "lightning", [(3, 5), (4, 5), (5, 5), (6, 5)],
        lambda r: (pinta(r, "agua", [(3, 5), (6, 5)]), pinta(r, "agua", [(6, 6), (7, 6)])))
cenario("choque: sem água", "lightning", [(3, 5)], lambda r: None)
# 🔥 piche
cenario("piche: mancha 3x3", "fire", [(6, 5)], lambda r: pinta(r, "piche", quadro(5, 4, 3, 3)))
cenario("piche: teto de 40 casas (8x8)", "fire", [(8, 8)], lambda r: pinta(r, "piche", quadro(5, 5, 8, 8)))


def _p2(r):
    pinta(r, "piche", quadro(5, 4, 3, 3))
    r.zonas_especiais.append({"id": "z1", "tipo": "chamas_piche", "tiles": [[5, 4], [6, 4], [7, 4]], "ativa": True,
                              "expira_em": 9})
cenario("piche: parte da mancha já está em chamas", "fire", [(6, 5)], _p2)
# 💥 gás
cenario("gás: câmara explode a sala toda", "fire", [(3, 3)], lambda r: camara(r, 0))
cenario("gás: fogo fora da sala da câmara", "fire", [(15, 5)], lambda r: camara(r, 0))
cenario("gás: nuvem de raio 1", "fire", [(6, 6)], lambda r: nuvem(r, 5, 5))
cenario("gás: fogo fora da nuvem", "fire", [(9, 9)], lambda r: nuvem(r, 5, 5))
# 🔥 gelo
cenario("gelo: fileira dentro do raio 4", "fire", [(5, 5)], lambda r: pinta(r, "piso_congelado", [(x, 5) for x in range(5, 10)]))
cenario("gelo: raio 4 numa fileira longa", "fire", [(10, 5)], lambda r: pinta(r, "piso_congelado", [(x, 5) for x in range(2, 20)]))
cenario("gelo: teto de 24 casas (plaza 9x9)", "fire", [(9, 9)], lambda r: pinta(r, "piso_congelado", quadro(5, 5, 9, 9)))
cenario("gelo + neve", "fire", [(4, 4)], lambda r: (pinta(r, "planicie_nevada", [(4, 4), (5, 4)]), pinta(r, "piso_congelado", [(4, 5)])))
# ❄️ frio
cenario("frio: água rasa, profunda e redemoinho", "cold", [(5, 5), (6, 5), (7, 5), (9, 9)],
        lambda r: (pinta(r, "agua", [(5, 5)]), pinta(r, "agua_profunda", [(6, 5)]), pinta(r, "rodamoinho", [(7, 5)])))
cenario("frio: lava vira crosta", "cold", [(5, 5), (6, 5)], lambda r: pinta(r, "lava", [(5, 5), (6, 5)]))
cenario("frio: casa seca", "cold", [(5, 5)], lambda r: None)
# fogo sem nada reagível
cenario("fogo: terreno comum", "fire", [(5, 5)], lambda r: None)
# mistura: fogo atinge piche e gelo ao mesmo tempo
cenario("fogo: piche e gelo juntos", "fire", [(5, 5), (9, 5)],
        lambda r: (pinta(r, "piche", [(5, 5), (6, 5)]), pinta(r, "piso_congelado", [(9, 5), (10, 5)])))

print("[1] servidor x cliente, mesmos cenários")
casos = [{"estado": c["estado"], "elemento": c["elemento"], "casas": c["casas"]} for c in CENARIOS]
with tempfile.TemporaryDirectory() as tmp:
    arq = os.path.join(tmp, "casos.json")
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(casos, f)
    runner = os.path.join(tmp, "runner.js")
    with open(runner, "w", encoding="utf-8") as f:
        f.write("const fs=require('fs');global.window={};\n"
                "eval(fs.readFileSync(process.argv[2],'utf8')+';');\n"
                "const casos=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));\n"
                "const out=casos.map(c=>{const p=window.ReacoesElementais.preverReacoes(c.estado,c.elemento,c.casas);\n"
                "  const o={};for(const k of Object.keys(p)) o[k]=p[k];return o;});\n"
                "console.log(JSON.stringify(out));\n")
    res = subprocess.run(["node", runner, os.path.join(RAIZ, "src", "reacoesElementais.js"), arq],
                         capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(res.stderr)
    cliente = json.loads(res.stdout) if res.returncode == 0 else [None] * len(CENARIOS)

for c, cli in zip(CENARIOS, cliente):
    srv = servidor(c["r"], c["elemento"], [tuple(x) for x in c["casas"]])
    srv = {k: sorted(v, key=lambda t: (t[1], t[0])) for k, v in srv.items()}
    cli = {k: sorted((tuple(t) for t in v), key=lambda t: (t[1], t[0])) for k, v in (cli or {}).items()}
    check(f"{c['nome']}  (servidor {sum(len(v) for v in srv.values())} casas)", srv == cli)

print("\n" + "=" * 62)
print(f"  {PASS} passaram, {FAIL} falharam")
print("=" * 62)
sys.exit(1 if FAIL else 0)
