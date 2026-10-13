"""Intenção dos monstros: previsão só de leitura, fiel à IA real.
Roda da raiz: python tools/test_monster_intent.py
Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
"""
import asyncio
import copy
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
    """Sala 18×10 vazia, fase 'playing', sem rede."""
    r = S.GameRoom("INTENT")
    async def noop(*a, **k):
        pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 11):
        for x in range(1, 19):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 18, "h": 10, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    return r


def heroi(r, pid, nome, classe, pos, hp=None):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    if hp is not None:
        h["hp"] = hp
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    r.monsters[m["id"]] = m
    return m


def monta(r):
    r._rebuild_initiative()


print("[1] herói à vista é o alvo; sem efeito colateral")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
monta(r)
antes = (copy.deepcopy(r.monsters), copy.deepcopy(r.players),
         r.__dict__.get("_monster_ai_focus_target_id", "AUSENTE"),
         r.__dict__.get("_monster_ai_reserved_tiles", "AUSENTE"))
itens = r._prever_intencoes("a")
check("um item para o orc", len(itens) == 1 and itens[0]["monstro_id"] == m["id"])
check("alvo é a Ana", itens and itens[0]["alvo_id"] == "a" and itens[0]["alvo_tipo"] == "heroi")
check("alvo_pos é a casa da Ana", itens and itens[0]["alvo_pos"] == [5, 5])
check("orc a 3 casas alcança (movimento 4+)", itens and itens[0]["alcanca"] is True)
check("casa_ataque é adjacente ao herói",
      itens and itens[0]["casa_ataque"] is not None
      and max(abs(itens[0]["casa_ataque"][0] - 5), abs(itens[0]["casa_ataque"][1] - 5)) == 1)
check("ação corpo a corpo", itens and itens[0]["acao"] == "corpo")
depois = (r.monsters, r.players,
          r.__dict__.get("_monster_ai_focus_target_id", "AUSENTE"),
          r.__dict__.get("_monster_ai_reserved_tiles", "AUSENTE"))
# a IA real normaliza (idempotente) os campos derivados de maldição ao ler;
# eles não contam como mutação de estado de jogo
def _sem_derivados(d):
    return {k: {c: v for c, v in h.items() if c not in ("amaldicoado", "maldicao_tipo")}
            for k, h in d.items()}
check("monstros e jogadores idênticos",
      antes[0] == depois[0] and _sem_derivados(antes[1]) == _sem_derivados(depois[1]))
check("foco e casas reservadas restaurados (inclusive ausentes)",
      antes[2] == depois[2] and antes[3] == depois[3])

print("[2] paridade com a IA real: escolhe o mais ferido")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
b = heroi(r, "b", "Bia", "warrior", [5, 7], hp=3)
m = monstro(r, "orc", [8, 6])
monta(r)
alvo_real = r._get_monster_primary_target(
    m, r._alvos_visiveis_para_monstro(m, r._alvos_hostis_para_monstros()))
r._monster_ai_focus_target_id = None
itens = r._prever_intencoes("a")
check("previsão = alvo que a IA escolheria",
      itens and itens[0]["alvo_id"] == alvo_real["obj"]["id"] == "b")

print("[3] exclusões")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
m["invisivel_sombras"] = True
monta(r)
check("monstro escondido nunca aparece", r._prever_intencoes("a") == [])
m.pop("invisivel_sombras")
m["hp"] = 0
check("monstro morto não aparece", r._prever_intencoes("a") == [])
m["hp"] = m["max_hp"]
r.rooms[0]["locked"] = True
check("sala trancada (dormente) não aparece", r._prever_intencoes("a") == [])
r.rooms[0]["locked"] = False
r.tiles[5][6] = S.WALL; r.tiles[4][6] = S.WALL; r.tiles[6][6] = S.WALL
r.tiles[3][6] = S.WALL; r.tiles[7][6] = S.WALL; r.tiles[2][6] = S.WALL
r.tiles[8][6] = S.WALL; r.tiles[1][6] = S.WALL; r.tiles[9][6] = S.WALL; r.tiles[10][6] = S.WALL
check("monstro atrás de parede (fora da visão do herói) não aparece",
      r._prever_intencoes("a") == [])
check("herói inexistente: lista vazia", r._prever_intencoes("zzz") == [])

print("[4] Mestre: Manual sem previsão, Semi com alvo forçado")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
b = heroi(r, "b", "Bia", "warrior", [5, 7])
m = monstro(r, "orc", [8, 6])
monta(r)
r.master_pid = "mestre"
r.connections = {"mestre": object(), "a": object(), "b": object()}
m["alertado"] = True
m["control_mode"] = "manual"
check("Manual: sem previsão", r._prever_intencoes("a") == [])
m["control_mode"] = "semi"
m["master_target_id"] = "b"
itens = r._prever_intencoes("a")
check("Semi: alvo forçado é a Bia", itens and itens[0]["alvo_id"] == "b")
check("Semi: certeza firme", itens and itens[0]["certeza"] == "firme")

print("[5] exceção interna vira lista vazia e restaura o estado")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
monta(r)
r._monster_ai_focus_target_id = "marca"
orig = r._get_monster_primary_target
def quebra(*args, **kw):
    raise RuntimeError("boom")
r._get_monster_primary_target = quebra
check("exceção -> []", r._prever_intencoes("a") == [])
r._get_monster_primary_target = orig
check("foco restaurado mesmo após exceção", r._monster_ai_focus_target_id == "marca")

print("[6] handler: resposta privada, taxa e cache")
import time as _time
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
monta(r)
enviados = []
async def captura(pid, msg, *a_, **k_):
    enviados.append((pid, msg))
r.send_to = captura
asyncio.run(r.handle_prever_intencoes("a"))
check("uma resposta ao solicitante", len(enviados) == 1 and enviados[0][0] == "a")
msg = enviados[0][1] if enviados else {}
check("tipo e rodada", msg.get("type") == "intencoes_monstros" and msg.get("rodada") == 1)
check("itens com o orc", len(msg.get("itens", [])) == 1)
enviados.clear()
asyncio.run(r.handle_prever_intencoes("a"))
check("segundo pedido imediato: limitado pela taxa", enviados == [])
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("depois do intervalo responde de novo", len(enviados) == 1)
chamadas = []
orig = r._prever_intencoes
def conta(pid):
    chamadas.append(pid)
    return orig(pid)
r._prever_intencoes = conta
enviados.clear()
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("mesma configuração: usa o cache (não recalcula)", chamadas == [] and len(enviados) == 1)
m["pos"] = [9, 5]
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("monstro andou: cache invalidado e recalcula", chamadas == ["a"])
enviados.clear()
a["alive"] = False
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("herói morto: sem resposta", enviados == [])
a["alive"] = True
r.phase = "city"
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("fora de 'playing': sem resposta", enviados == [])

print("[6b] assinatura do cache cobre todas as entradas")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
b = heroi(r, "b", "Bia", "warrior", [5, 7])
m = monstro(r, "orc", [8, 6])
monta(r)
r.master_pid = "mestre"
r.connections = {"mestre": object(), "a": object(), "b": object()}
m["alertado"] = True
r.send_to = captura
chamadas = []
orig = r._prever_intencoes
def conta2(pid):
    chamadas.append(pid)
    return orig(pid)
r._prever_intencoes = conta2
def pede():
    r._intent_ultimo["a"] = _time.monotonic() - 1.0
    n = len(chamadas)
    asyncio.run(r.handle_prever_intencoes("a"))
    return len(chamadas) > n
pede()
check("base: segundo pedido usa cache", pede() is False)
a["pos"] = [5, 6]
check("herói andou invalida", pede())
a["hp"] = a["hp"] - 1
check("hp do herói invalida", pede())
m["control_mode"] = "semi"; m["master_target_id"] = "b"
pede()
m["master_target_id"] = "a"
check("master_target_id invalida", pede())
m["provocado"] = True; m["provocado_turnos"] = 2
pede()
m["provocado_turnos"] = 1
check("provocado_turnos invalida", pede())
pede()
r.rooms[0]["locked"] = True
check("sala trancada/destrancada invalida", pede())
pede()
r.connections.pop("mestre")
check("mestre desconectado invalida", pede())
a["alive"] = False
ant = r._intent_ultimo["a"]
asyncio.run(r.handle_prever_intencoes("a"))
check("herói morto não toca _intent_ultimo", r._intent_ultimo["a"] == ant)

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
