"""Caminho inteiro numa mensagem (`move_path`).

Roda da raiz:  python tools/test_move_path.py

POR QUE ESTE TESTE EXISTE
  O cliente mandava um `move` por casa, e cada um virava um `game_state`
  completo para TODOS os jogadores. Num caminho de 6 casas eram 6 estados em
  rajada: quem assistia via o peão do outro saltar e o jogo engasgava. Agora o
  caminho vai numa mensagem: cada passo passa pelo mesmo `handle_move`, sai um
  `entity_step` por casa (o peão desliza para quem assiste) e UM `game_state`
  no fim.

O QUE ELE COBRA
  • caminho válido: anda tudo, gasta o movimento, 1 push_state, 1 entity_step
    por casa com from/to certos
  • passo recusado no meio: para ali, avisa quem andou, sem passos fantasmas
  • primeiro passo recusado: nada anda e nenhum estado é enviado
  • fora da vez: nada acontece
  • entrada malformada (diagonal, lixo, excesso) é descartada
  • fiação: despacho no handler, GS.movePath, cliente anima herói por entity_step
"""
import asyncio, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))

def ler(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as f: return f.read()


async def montar():
    r = S.GameRoom("MPATH")
    r.broadcast = None
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop
    for pid, nome, cls in (("p1", "Andante", "warrior"), ("p2", "Olheiro", "rogue")):
        r.players[pid] = S.make_player(pid, nome, cls, len(r.players))
    r.phase = "city"; r.host_pid = "p1"
    await r.enter_dungeon("p1")
    r.monsters.clear()                      # sem interferência de monstros/avistamento
    r.dungeon_intro_active = False
    r._intro_masmorra_bloqueada = lambda: False
    r._is_turn = lambda pid: pid == "p1"
    # Registro do que sai para a rede.
    r.log = {"push": 0, "bcast": [], "priv": []}
    async def push_state(): r.log["push"] += 1
    async def broadcast(msg, skip=None): r.log["bcast"].append(msg)
    async def send_to(pid, msg): r.log["priv"].append((pid, msg))
    r.push_state = push_state; r.broadcast = broadcast; r.send_to = send_to
    return r


def livre(r, x, y, ocupados):
    return (0 <= y < len(r.tiles) and 0 <= x < len(r.tiles[0])
            and r.tiles[y][x] == S.FLOOR and not r._blocks_tile(x, y)
            and (x, y) not in ocupados)


def caminho_livre(r, pid, n):
    """Caminho simples (com curvas) de até n casas de chão livre a partir do
    herói — o mapa é procedural, nem sempre há um trecho reto longo."""
    p = r.players[pid]; x0, y0 = p["pos"]
    ocup = {tuple(q["pos"]) for q in r.players.values() if q is not p}
    melhor = []
    def dfs(x, y, passos, vistos):
        nonlocal melhor
        if len(passos) > len(melhor): melhor = list(passos)
        if len(passos) >= n: return
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in vistos or not livre(r, nx, ny, ocup): continue
            vistos.add((nx, ny)); passos.append([dx, dy])
            dfs(nx, ny, passos, vistos)
            passos.pop(); vistos.discard((nx, ny))
            if len(melhor) >= n: return
    dfs(x0, y0, [], {(x0, y0)})
    return melhor


def casas(ini, path):
    out, x, y = [], ini[0], ini[1]
    for dx, dy in path:
        x += dx; y += dy; out.append([x, y])
    return out


def steps(r):
    return [m for m in r.log["bcast"] if m.get("type") == "entity_step"]


async def main():
    print("\n[1] Caminho válido")
    r = await montar()
    p = r.players["p1"]; p["moves_left"] = 10
    path = caminho_livre(r, "p1", 4)
    check(f"há um trecho reto de chão para testar ({len(path)} casas)", len(path) >= 3, str(p["pos"]))
    if len(path) < 3: return
    ini = list(p["pos"]); mv0 = p["moves_left"]
    await r.handle_move_path("p1", path)
    fim = casas(ini, path)[-1]
    check("chegou ao fim do caminho", p["pos"] == fim, f"{p['pos']} != {fim}")
    check("gastou uma casa de movimento por passo", mv0 - p["moves_left"] == len(path),
          f"{mv0} → {p['moves_left']}")
    check("UM game_state no fim (não um por casa)", r.log["push"] == 1, str(r.log["push"]))
    st = steps(r)
    check("um entity_step por casa", len(st) == len(path), str(len(st)))
    pos, ok = list(ini), True
    for s_, d in zip(st, path):
        nxt = [pos[0] + d[0], pos[1] + d[1]]
        ok &= (s_["from"] == pos and s_["to"] == nxt and s_["id"] == "p1" and s_["kind"] == "player")
        pos = nxt
    check("from/to encadeados casa a casa, kind=player", ok, str(st[:2]))
    check("facing do último passo", p.get("facing") == list(path[-1]))

    print("\n[2] Passo recusado no meio do caminho")
    r = await montar()
    p = r.players["p1"]; p["moves_left"] = 10
    path = caminho_livre(r, "p1", 4)
    ini = list(p["pos"])
    # O Olheiro fica na 3ª casa: os dois primeiros passos andam, o 3º é recusado.
    r.players["p2"]["pos"] = casas(ini, path)[2]
    await r.handle_move_path("p1", path)
    esperado = casas(ini, path)[1]
    check("parou antes do bloqueio", p["pos"] == esperado, f"{p['pos']} != {esperado}")
    check("só os passos aceitos viraram entity_step", len(steps(r)) == 2, str(len(steps(r))))
    check("avisou quem andou", any(pid == "p1" and m.get("type") == "error" for pid, m in r.log["priv"]))
    check("um game_state com o que andou", r.log["push"] == 1)

    print("\n[3] Primeiro passo recusado")
    r = await montar()
    p = r.players["p1"]; p["moves_left"] = 10
    path = caminho_livre(r, "p1", 2)
    ini = list(p["pos"])
    r.players["p2"]["pos"] = [ini[0] + path[0][0], ini[1] + path[0][1]]
    await r.handle_move_path("p1", path)
    check("não andou", p["pos"] == ini)
    check("nenhum estado nem entity_step", r.log["push"] == 0 and not steps(r))

    print("\n[4] Fora da vez / entrada malformada")
    r = await montar()
    p2 = r.players["p2"]; p2["moves_left"] = 10; ini2 = list(p2["pos"])
    await r.handle_move_path("p2", [[1, 0], [1, 0]])
    check("fora da vez: nada anda", p2["pos"] == ini2 and r.log["push"] == 0 and not steps(r))
    p = r.players["p1"]; p["moves_left"] = 10; ini = list(p["pos"])
    await r.handle_move_path("p1", [[1, 1], [1, 0]])
    check("diagonal é descartada (para no 1º passo inválido)", p["pos"] == ini and not steps(r))
    await r.handle_move_path("p1", ["lixo", 3])
    check("lixo é ignorado sem exceção", p["pos"] == ini)
    await r.handle_move_path("p1", None)
    check("path ausente é ignorado", p["pos"] == ini)
    check("teto de passos por mensagem", S.GameRoom.MAX_PASSOS_CAMINHO <= 60)

    print("\n[5] Fiação")
    srv = ler("server.py")
    check("handler despacha move_path", 'elif t == "move_path"' in srv
          and "await room.handle_move_path(pid, path)" in srv)
    check("handle_move não faz push_state por passo dentro do caminho",
          "await self._push_se(_push)" in srv
          and "await self.handle_move(pid, dx, dy, _push=False)" in srv)
    gs = ler("src/gameState.js")
    check("GS.movePath exportado", "function movePath(path)" in gs and "    movePath," in gs)
    gj = ler("game.js")
    check("o clique de caminho usa GS.movePath (não um move por casa)",
          gj.count("GS.movePath(action.path)") == 2
          and "for(const [dx,dy] of action.path) GS.move(dx, dy);" not in gj)
    check("3D desliza peão de herói por entity_step", "getAnimadoMesh(id) || getPeaoMesh(id)" in gj)
    check("2D desliza herói por entity_step", "const _pStep = _serverStepPos(p.id);" in gj)
    check("herói anda no ritmo local (DURACAO_PASSO_MS)",
          re.search(r"msg\.kind === 'player' \? DURACAO_PASSO_MS", gj) is not None)
    check("o próprio passo é ignorado durante a animação local",
          "String(id) === String(GS.myPid) && estadoMovimento.emMovimento" in gj)


asyncio.run(main())
print(f"\n{'=' * 62}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 62}")
sys.exit(1 if FAIL else 0)
