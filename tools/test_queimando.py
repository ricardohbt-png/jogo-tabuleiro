"""Chamas vivas no peão para TODO fogo contínuo: campo `queimando` do game_state.
Roda da raiz: python tools/test_queimando.py
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


def cena():
    """Sala 12×8 de chão, um herói em [4,4] e um orc em [8,4]."""
    r = S.GameRoom("QUEIMA")
    async def noop(*a, **k):
        pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 9):
        for x in range(1, 13):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 12, "h": 8, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    h = S.make_player("h", "Richard", "paladin", 0)
    h["pos"] = [4, 4]
    r.players = {"h": h}
    orc = next(d for d in S.MONSTER_DEFS if d["type"] == "orc")
    m = S.make_monster(orc, {"id": 0, "cx": 8, "cy": 4})
    m["pos"] = [8, 4]
    r.monsters = {m["id"]: m}
    return r, h, m


def queimando(r, ent):
    """Lê o campo como o cliente lê: do payload do game_state."""
    pay = r._game_state_payload()
    lista = pay["players"] if ent.get("class_id") else pay["monsters"]
    return next(x for x in lista if x["id"] == ent["id"]).get("queimando")


async def secao_estados():
    print("\n[1] Cada fonte de fogo contínuo liga o `queimando` (herói e monstro)")
    r, h, m = cena()
    check("sem fogo: herói não queima", queimando(r, h) is False)
    check("sem fogo: monstro não queima", queimando(r, m) is False)

    h["em_chamas_rodadas"] = 2
    m["em_chamas_rodadas"] = 2
    check("status em chamas: herói queima", queimando(r, h) is True)
    check("status em chamas: monstro queima", queimando(r, m) is True)

    r, h, m = cena()
    r.armadilhas = [{"id": "a1", "tipo": "armadilha_incendiaria", "pos": [4, 4],
                     "efeitos_ativos": [{"alvo_id": "h", "valor": "1d4", "elemento": "fogo",
                                         "rodadas_restantes": 2}]}]
    check("Armadilha Incendiária ticando: herói queima", queimando(r, h) is True)
    r.armadilhas[0]["efeitos_ativos"][0]["rodadas_restantes"] = 0
    check("efeito da armadilha acabou: não queima mais", queimando(r, h) is False)

    r, h, m = cena()
    r.materiais = {(4, 4): "lava"}
    check("em cima de lava: herói queima", queimando(r, h) is True)
    h["pos"] = [5, 4]
    check("saiu da lava: não queima", queimando(r, h) is False)

    r, h, m = cena()
    r.zonas_especiais = [{"tipo": "prisao_chamas", "ativa": True, "flame_tiles": [[4, 4]],
                          "tiles": [[5, 4]]}]
    check("na parede da Prisão de Chamas: queima", queimando(r, h) is True)
    h["pos"] = [5, 4]
    check("só no calor ao lado da parede: não queima", queimando(r, h) is False)

    r, h, m = cena()
    r.zonas_especiais = [{"tipo": "bola_fogo", "ativa": True, "cx": 8, "cy": 4, "raio": 1}]
    check("chamas da Bola de Fogo sob o monstro: queima", queimando(r, m) is True)
    check("herói fora da área da Bola de Fogo: não queima", queimando(r, h) is False)
    r.zonas_especiais[0]["ativa"] = False
    check("zona apagada: não queima", queimando(r, m) is False)

    r, h, m = cena()
    r.zonas_especiais = [{"tipo": "molochus_chamas", "ativa": True, "cx": 4, "cy": 4, "raio": 1}]
    check("chamas do Molochus: herói queima", queimando(r, h) is True)


async def secao_bomba_do_soldado():
    print("\n[2] Bomba Incendiária arremessada por monstro deixa em chamas (antes só dava dano)")
    r, h, m = cena()
    h["pos"] = [8, 5]                                   # ao lado do orc, dentro do raio 1
    item = dict(S.ARREMESSAVEIS["bomba_incendiaria"])
    orig = S.random.randint
    S.random.randint = lambda a, b: 1                   # falha no save e dano mínimo
    try:
        await r._monster_throw_item(m, {"kind": "player", "obj": h}, item)
    finally:
        S.random.randint = orig
    check("herói atingido ficou em chamas", int(h.get("em_chamas_rodadas", 0)) > 0)
    check("e o `queimando` liga", queimando(r, h) is True)


def secao_cliente():
    print("\n[3] O cliente desenha as chamas pelo `queimando`, no 2D e no 3D")
    js = open(os.path.join(os.path.dirname(S.__file__), "game.js"), encoding="utf-8").read()
    check("helper único _queimando(x) no cliente", "function _queimando(" in js)
    check("2D do monstro usa o helper", "if(_queimando(m))" in js)
    check("2D do herói usa o helper", "if(_queimando(p) && !_invisP)" in js)
    check("3D: o fig do herói e o do monstro recebem o helper",
          js.count("_queimando(p),") >= 2 and js.count("_queimando(m),") >= 2)


async def main():
    await secao_estados()
    await secao_bomba_do_soldado()
    secao_cliente()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
