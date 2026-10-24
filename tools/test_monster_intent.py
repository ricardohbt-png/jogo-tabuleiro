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
m = monstro(r, "urso_negro", [8, 5])   # IA modular: anda E ataca no mesmo turno
monta(r)
antes =(copy.deepcopy(r.monsters), copy.deepcopy(r.players),
         r.__dict__.get("_monster_ai_focus_target_id", "AUSENTE"),
         r.__dict__.get("_monster_ai_reserved_tiles", "AUSENTE"))
itens = r._prever_intencoes("a")
check("um item para o urso", len(itens) == 1 and itens[0]["monstro_id"] == m["id"])
check("alvo é a Ana", itens and itens[0]["alvo_id"] == "a" and itens[0]["alvo_tipo"] == "heroi")
check("alvo_pos é a casa da Ana", itens and itens[0]["alvo_pos"] == [5, 5])
check("urso a 3 casas alcança (movimento 6)",itens and itens[0]["alcanca"] is True)
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

print("[6c] paridade com a IA REAL (gm_phase por monstro, na ordem da iniciativa)")
import random as _random


def roda_ia_real(r):
    """Roda a IA real como a iniciativa a roda (um gm_phase(m) por monstro).
    Devolve (escolha, ataque): o último alvo que a IA escolheu por monstro e o
    alvo contra o qual ele de fato rolou ataque. Dados: semente fixa e todo
    ataque erra (só o ALVO importa; nada de dano/morte no meio)."""
    _random.seed(7)
    escolha, ataque = {}, {}
    cur = {"mid": None}
    og = r._get_monster_primary_target
    def wrap(m_, targets):
        res = og(m_, targets)
        if res:
            escolha[m_["id"]] = res["obj"].get("id")
        return res
    r._get_monster_primary_target = wrap
    oe = r._execute_one_monster_attack
    async def ex(m_, atk_def, target_obj, **kw):
        ataque.setdefault(m_["id"], (target_obj.get("obj") or {}).get("id"))
        return await oe(m_, atk_def, target_obj, **kw)
    r._execute_one_monster_attack = ex
    od = S.d20_attack
    def d20(*a_, **k_):
        if cur["mid"] and cur["mid"] not in ataque:
            ataque[cur["mid"]] = escolha.get(cur["mid"])
        return (False, 1, 1, False)
    S.d20_attack = d20
    r._rolar_ataque = lambda *a_, **k_: d20() + (None,)
    try:
        for e in list(r.initiative_order):
            if e["kind"] != "monster" or e["id"] not in r.monsters:
                continue
            cur["mid"] = e["id"]
            asyncio.run(r.gm_phase(r.monsters[e["id"]]))
    finally:
        S.d20_attack = od
        del r._get_monster_primary_target, r._execute_one_monster_attack, r._rolar_ataque
    return escolha, ataque


def paridade(nome, r, pid="a"):
    prev = r._prever_intencoes(pid)          # previsão ANTES da IA rodar
    pmap = {i["monstro_id"]: i for i in prev}
    escolha, ataque = roda_ia_real(r)
    ok = True
    for mid, it in pmap.items():
        if escolha.get(mid) != it["alvo_id"]:
            ok = False
        if (ataque.get(mid) == it["alvo_id"]) != bool(it["alcanca"]):
            ok = False
    for mid in ataque:
        if mid not in pmap:
            ok = False
    check(f"{nome}: previsão {[(i['monstro_id'], i['alvo_id'], i['alcanca']) for i in prev]}"
          f" = IA real escolha={escolha} ataque={ataque}", ok)
    return prev, escolha, ataque


# (a) foco é por monstro: cada orc ataca o herói ao lado dele
r = sala()
heroi(r, "a", "Ana", "warrior", [3, 5]); heroi(r, "b", "Bia", "warrior", [8, 5])
monstro(r, "orc", [4, 5]); monstro(r, "orc", [7, 5]); monta(r)
prev, _, _ = paridade("(a) dois orcs, um herói ao lado de cada", r)
check("(a) os dois orcs alcançam (seta no modo grupo)", len(prev) == 2 and all(i["alcanca"] for i in prev))

# (a2) orc sem ai_type (caminho legado) longe: anda 1 casa e NÃO ataca no mesmo turno
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5])
monstro(r, "orc", [8, 5]); monta(r)
paridade("(a2) orc legado a 3 casas", r)

# (b) prefere o ferido (IA modular: urso)
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5]); heroi(r, "b", "Bia", "warrior", [5, 8], hp=3)
monstro(r, "urso_negro", [9, 6]); monta(r)
prev, _, _ = paridade("(b) urso escolhe a Bia ferida", r)
check("(b) alvo previsto é a Bia", prev and prev[0]["alvo_id"] == "b")

# (c) provocação vence a presa ferida
r = sala()
heroi(r, "a", "Ana", "warrior", [6, 3]); heroi(r, "b", "Bia", "warrior", [8, 7], hp=3)
lb = monstro(r, "urso_negro", [9, 5]); monta(r)
lb["provocado"] = True; lb["provocado_turnos"] = 2; lb["provocado_por"] = "a"
prev, _, _ = paridade("(c) urso provocado pela Ana", r)
check("(c) alvo previsto é a Ana, firme", prev and prev[0]["alvo_id"] == "a" and prev[0]["certeza"] == "firme")

# (d) atirador com orçamento de movimento velho (o do turno passado)
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5])
kb = monstro(r, "kobold_besteiro", [10, 5]); monta(r)
kb["_water_moves_left"] = 0
prev, _, _ = paridade("(d) kobold besteiro a 5 casas, _water_moves_left velho=0", r)
check("(d) previsão alcança com casa de tiro", prev and prev[0]["alcanca"] and prev[0]["casa_ataque"])

# (f) dois ursos longe do mesmo herói: as casas reservadas acumuladas (o 1º
# fica com o flanco) batem com a IA real, que ocupa o flanco de verdade
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5])
monstro(r, "urso_negro", [9, 5]); monstro(r, "urso_negro", [9, 6]); monta(r)
prev, _, _ = paridade("(f) dois ursos convergindo na Ana", r)
check("(f) casas de ataque distintas",
      len(prev) == 2 and prev[0]["casa_ataque"] != prev[1]["casa_ataque"])

# (e) dormindo / comandado / com medo: não age, sem previsão
for flag, extra in (("dormindo", {"dormindo_rodadas": 2}), ("comandado", {}),
                    ("com_medo", {"medo_rodadas": 2}), ("perde_turno", {}),
                    # petrificado: o despacho da iniciativa pula o monstro antes
                    # da gm_phase; aqui rodamos a gm_phase direto, então a
                    # petrificação precisa durar (permanente) para os dois
                    # caminhos concordarem.
                    ("petrificado", {"petrificado_permanente": True})):
    r = sala()
    heroi(r, "a", "Ana", "warrior", [5, 5])
    mm = monstro(r, "urso_negro", [6, 5]); monta(r)
    mm[flag] = True; mm.update(extra)
    prev, _, ataque = paridade(f"(e) urso {flag}", r)
    check(f"(e) {flag}: sem previsão e sem ataque real", prev == [] and ataque == {})
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5])
mm = monstro(r, "urso_negro", [6, 5]); monta(r)
mm["dormindo"] = True; mm["dormindo_rodadas"] = 0
check("(e) sono que expira neste turno: ainda há previsão (ele acorda e age)",
      len(r._prever_intencoes("a")) == 1)
mm.pop("dormindo"); mm["comando_pendente_pid"] = "a"
check("(e) Comando pendente: sem previsão", r._prever_intencoes("a") == [])

print("[6d] orçamento de movimento da previsão")
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5])
kb = monstro(r, "kobold_besteiro", [10, 5]); monta(r)
kb["_water_moves_left"] = 0
r._prever_intencoes("a")
check("_water_moves_left restaurado (0)", kb["_water_moves_left"] == 0)
kb.pop("_water_moves_left")
itn = r._prever_intencoes("a")
check("_water_moves_left ausente continua ausente", "_water_moves_left" not in kb)
check("ausente também alcança", itn and itn[0]["alcanca"])
lb = None
r = sala()
heroi(r, "a", "Ana", "warrior", [5, 5])
lb = monstro(r, "urso_negro", [8, 5]); monta(r)
lb["turbilhao_perde_movimento"] = True
itn = r._prever_intencoes("a")
check("perdeu o movimento (Tempestade): não alcança movendo", itn and itn[0]["alcanca"] is False)
check("flag de perda de movimento preservada", lb.get("turbilhao_perde_movimento") is True)

print("[6e] cache: invisibilidade do herói e sono do monstro invalidam")
r = sala()
a = heroi(r, "a", "Ana", "rogue", [5, 5])
m = monstro(r, "urso_negro", [8, 5]); monta(r)
r.send_to = captura
chamadas = []
orig = r._prever_intencoes
def conta3(pid):
    chamadas.append(pid)
    return orig(pid)
r._prever_intencoes = conta3
def pede3():
    r._intent_ultimo["a"] = _time.monotonic() - 1.0
    n = len(chamadas)
    asyncio.run(r.handle_prever_intencoes("a"))
    return len(chamadas) > n
pede3()
check("base: cache", pede3() is False)
a["invisivel_sombras"] = True
check("herói se escondeu (sem andar) invalida", pede3())
m["dormindo"] = True; m["dormindo_rodadas"] = 2
check("monstro dormiu invalida", pede3())
a["derrubado"] = True
check("herói derrubado invalida", pede3())
a["altura"] = 4
check("altura do herói invalida", pede3())
r.zonas_especiais.append({"tipo": "escuridao", "pos": [6, 5], "duracao": 2})
check("zona especial nova invalida", pede3())
enviados.clear()
r._intent_ultimo["a"] = _time.monotonic() - 1.0
r.initiative_active = True
asyncio.run(r.handle_prever_intencoes("a"))
check("resposta traz `vez` (pid da vez atual)", enviados and enviados[-1][1].get("vez") == r.current_pid())

print("[7] caminho real: server.handler despacha prever_intencoes")
import json as _json
src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
check("ramo de despacho existe no handler", 'elif t == "prever_intencoes"' in src)


class _FakeWS:
    def __init__(self, roteiro):
        self.roteiro = list(roteiro); self.sent = []
    def __aiter__(self): return self
    async def __anext__(self):
        while self.roteiro:
            item = self.roteiro.pop(0)
            if callable(item):
                r_ = item()
                if asyncio.iscoroutine(r_): r_ = await r_
                if isinstance(r_, dict): return _json.dumps(r_)
                continue
            return _json.dumps(item)
        raise StopAsyncIteration
    async def send(self, data): self.sent.append(data)
    async def close(self, *a, **k): pass


def _sala_h():
    for rr in S.rooms.values():
        for pid_, pp in rr.players.items():
            if pp.get("name") == "Intento": return rr, pid_
    return None, None


async def _cenario_real():
    cx = {}
    async def prepara():
        rr, pid_ = _sala_h()
        await rr._liberar_intro_masmorra(True)
        h = rr.players[pid_]; x, y = h["pos"]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if rr._blocks_tile(nx, ny): continue
            if any(list(mm["pos"]) == [nx, ny] for mm in rr.monsters.values()): continue
            d = next(d for d in S.MONSTER_DEFS if d["type"] == "orc")
            mm = S.make_monster(d, {"id": 0, "cx": nx, "cy": ny})
            mm["pos"] = [nx, ny]; mm["alertado"] = True
            rr.monsters[mm["id"]] = mm
            cx["mid"] = mm["id"]
            break
    ws = _FakeWS([
        {"type": "create_room", "name": "Intento"},
        {"type": "select_class", "class_id": "warrior"},
        {"type": "start_game"},
        {"type": "enter_dungeon"},
        prepara,
        {"type": "prever_intencoes"},
        lambda: asyncio.sleep(0.2),
    ])
    await S.handler(ws)
    return ws, cx


ws_real, cx_real = asyncio.run(_cenario_real())
recebidas = [_json.loads(x) for x in ws_real.sent if '"intencoes_monstros"' in x]
check("monstro injetado ao lado do herói", "mid" in cx_real)
check("uma resposta intencoes_monstros chegou ao socket do herói", len(recebidas) == 1)
rm = recebidas[0] if recebidas else {}
check("resposta traz rodada", isinstance(rm.get("rodada"), int))
its = rm.get("itens") or []
check("itens não vazio", len(its) >= 1)
chaves = {"monstro_id", "alvo_id", "alvo_tipo", "alvo_pos", "acao", "alcanca", "casa_ataque", "certeza"}
check("primeiro item tem as chaves documentadas", bool(its) and chaves <= set(its[0]))
check("sem Internal error", not any("Internal error" in x for x in ws_real.sent))
for k_ in [k_ for k_, v_ in S.rooms.items() if any(pp.get("name") == "Intento" for pp in v_.players.values())]:
    S.rooms.pop(k_, None)

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
