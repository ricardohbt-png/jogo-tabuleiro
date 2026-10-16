"""Sala das Reações de Terreno (Campo de Treinamento): gás permanente, porta `gas`,
verbos de lição, frasco de socorro e criação do gás. Roda da raiz:
python -X utf8 tools/test_sala_reacoes_tutorial.py
Spec: docs/superpowers/specs/2026-10-16-sala-reacoes-terreno-design.md"""
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


def roda(coro):
    return asyncio.run(coro)


def sala():
    """Duas salas de chão lado a lado (0: x1-10, 1: x11-20), 'playing', sem rede."""
    r = S.GameRoom("SRT")
    r.msgs = []
    r.narr = []
    r.saves = []
    r.dados = []

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


def heroi(r, pid, nome, classe, pos, hp=60):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    h["hp"] = h["max_hp"] = hp
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def camara(r, sala_id=0, duracao=4, **extra):
    z = {"id": f"camara_gas_t{sala_id}", "tipo": "camara_gas", "room_id": sala_id,
         "duracao": duracao, "ativa": True, "created_round": r.round_num}
    z.update(extra)
    r.zonas_especiais.append(z)
    return z


def fixa(r, dado=8, passa=False):
    """Dado fixo (registra a expressão pedida em r.dados) e save fixo."""
    def rolar(expr):
        r.dados.append(expr)
        return dado
    r._rolar_dado = rolar

    async def save(alvo, tipo, cd, *a, **k):
        r.saves.append((tipo, cd))
        return passa, 10, 0, 10
    r._save_mostrado = save


async def fogo_em(r, casas, caster="x", origem=None):
    async with r.evento_elemental(origem or {"tipo": "item", "id": "frasco_oleo", "caster_id": caster}):
        await r._rx_registrar(S.DMG_FIRE, casas, dano=1)


def secao_1():
    print("[1] gás permanente e dano de explosão por zona")
    r = sala()
    z = camara(r, duracao=2, permanente=True)
    for _ in range(5):
        roda(r._processar_zonas_turno_impl())
    check("zona permanente não dissipa em 5 rodadas", z["ativa"] is True)
    r = sala()
    z = camara(r, duracao=2)
    for _ in range(2):
        roda(r._processar_zonas_turno_impl())
    check("sem a marca a câmara ainda dissipa", z["ativa"] is False)
    r = sala()
    z = camara(r, permanente=True)
    n = camara(r, sala_id=1, permanente=True)
    n.update(id="nuvem_t", tipo="nuvem_gas", tiles=[[12, 3]])
    for _ in range(6):
        roda(r._processar_zonas_turno_impl())
    check("nuvem de gás permanente também não dissipa", n["ativa"] is True)
    r = sala()
    fixa(r, dado=3)
    heroi(r, "a", "Ana", "warrior", [3, 3])
    camara(r, dano_explosao="1d4")
    roda(fogo_em(r, [(3, 3)]))
    check("dano_explosao da zona é a expressão rolada", "1d4" in r.dados and "2d6" not in r.dados)
    r = sala()
    fixa(r, dado=3)
    heroi(r, "a", "Ana", "warrior", [3, 3])
    camara(r)
    roda(fogo_em(r, [(3, 3)]))
    check("sem o campo a explosão continua 2d6", "2d6" in r.dados)


if __name__ == "__main__":
    secao_1()
    print(f"\n{PASS} ok, {FAIL} falhas")
    sys.exit(1 if FAIL else 0)
