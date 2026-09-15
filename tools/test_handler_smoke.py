"""Fumaça do laço de conexão REAL (`server.handler`) — ponta a ponta.

Roda da raiz:  python tools/test_handler_smoke.py

POR QUE ESTE TESTE EXISTE
  As ~137 suítes chamam métodos do `GameRoom` diretamente. Nenhuma passava pelo
  `async for raw in ws` do `handler`, e foi ALI que morou o bug do idioma no
  rejoin (2026-09-14): `set_lang` chega antes do `rejoin`, grava LANG_BY_PID
  sob o pid da conexão nova, e o rejoin troca `pid` pela identidade antiga.
  Tudo que vive no handler — pid reatribuído, LANG_BY_PID, ACCOUNTS_ONLINE, o
  `finally` da desconexão — só é exercitado por um teste que dirige o handler.

O QUE ELE FAZ
  Um WebSocket falso (async iterator) entrega mensagens ao handler exatamente
  como a lib faria. O roteiro é o ciclo de um jogador em inglês:
    criar sala → escolher classe → iniciar → entrar na masmorra → esperar a vez
    → andar → (atacar se houver alvo) → encerrar turno → CAIR (fim do iterador
    = desconexão) → RELIGAR noutra conexão → agir de novo.
  Passos podem ser funções (sync ou async) que leem `S.rooms` — é assim que o
  teste escolhe uma direção livre e espera a iniciativa chegar ao herói.

O QUE ELE COBRA
  • nenhuma resposta "Internal error" em NENHUMA das duas conexões
  • os payloads de fase chegam (lobby_state, city_state, enter_dungeon, game_state)
  • a desconexão em jogo mantém o jogador em `players` e o tira de `connections`
  • o rejoin devolve o herói ao tabuleiro, narra em INGLÊS, e uma ação seguinte
    é aceita (o pid religado continua sendo a identidade que o jogo conhece)
  • `LANG_BY_PID` fica limpo depois que as duas conexões terminam
"""
import asyncio, json, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


class FakeWS:
    """Conexão falsa. Itens da lista: dict (mensagem JSON) ou callable (passo do
    roteiro — pode ser async; se devolver dict, esse dict é enviado)."""
    def __init__(self, roteiro):
        self.roteiro = list(roteiro); self.sent = []
    def __aiter__(self): return self
    async def __anext__(self):
        while self.roteiro:
            item = self.roteiro.pop(0)
            if callable(item):
                r = item()
                if asyncio.iscoroutine(r): r = await r
                if isinstance(r, dict): return json.dumps(r)
                continue
            return json.dumps(item)
        raise StopAsyncIteration
    async def send(self, data): self.sent.append(data)
    async def close(self, *a, **k): pass

    def msgs(self, tipo=None):
        out = []
        for raw in self.sent:
            try: d = json.loads(raw)
            except Exception: continue
            if tipo is None or d.get("type") == tipo: out.append(d)
        return out
    def erros(self): return [d.get("msg", "") for d in self.msgs("error")]


def _sala_e_pid(nome):
    for code, r in S.rooms.items():
        for pid, p in r.players.items():
            if p.get("name") == nome: return r, pid
    return None, None


async def _esperar_vez(nome, timeout=8.0):
    """Espera a iniciativa chegar ao herói (monstros podem agir antes)."""
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        r, pid = _sala_e_pid(nome)
        if r and r.phase == "playing" and r.current_pid() == pid: return True
        await asyncio.sleep(0.05)
    return False


def _direcao_livre(r, pid):
    p = r.players[pid]; x, y = p["pos"]
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        nx, ny = x + dx, y + dy
        if not (0 <= ny < len(r.tiles) and 0 <= nx < len(r.tiles[0])): continue
        if r._blocks_tile(nx, ny): continue
        if any(m.get("hp", 0) > 0 and list(m["pos"]) == [nx, ny] for m in r.monsters.values()): continue
        if any(q is not p and q.get("alive", True) and list(q.get("pos", [-1, -1])) == [nx, ny] for q in r.players.values()): continue
        return dx, dy
    return None


def _monstro_adjacente(r, pid):
    x, y = r.players[pid]["pos"]
    for m in r.monsters.values():
        if m.get("hp", 0) > 0 and max(abs(m["pos"][0] - x), abs(m["pos"][1] - y)) <= 1:
            return m
    return None


async def cenario():
    NOME = "Fumaca"
    registro = {}

    # ── 1ª conexão: ciclo completo até cair ───────────────────────────────
    async def liberar_intro():
        r, _ = _sala_e_pid(NOME)
        # Mesmo caminho do jogo, sem os 3 s de transição.
        await r._liberar_intro_masmorra(True)
        registro["pos_inicial"] = list(r.players[_sala_e_pid(NOME)[1]]["pos"])

    async def passo_mover():
        if not await _esperar_vez(NOME):
            registro["sem_vez_1"] = True; return None
        r, pid = _sala_e_pid(NOME)
        d = _direcao_livre(r, pid)
        if not d: registro["sem_direcao"] = True; return None
        registro["dir"] = d
        return {"type": "move", "dx": d[0], "dy": d[1]}

    async def passo_atacar():
        r, pid = _sala_e_pid(NOME)
        m = _monstro_adjacente(r, pid)
        if not m: return None
        registro["atacou"] = m["id"]
        return {"type": "attack", "target_id": m["id"]}

    async def passo_encerrar():
        r, pid = _sala_e_pid(NOME)
        # Lido AQUI, não depois do handler: a queda em jogo tira o peão do
        # tabuleiro (pos → [-1,-1], como um desconectado) — ver _ativo().
        registro["pos_apos_mover"] = list(r.players[pid]["pos"])
        registro["round_antes"] = r.round_num
        return {"type": "end_turn"}

    ws1 = FakeWS([
        {"type": "set_lang", "lang": "en"},
        {"type": "create_room", "name": NOME},
        {"type": "select_class", "class_id": "warrior"},
        {"type": "start_game"},
        {"type": "enter_dungeon"},
        liberar_intro,
        passo_mover,
        passo_atacar,
        passo_encerrar,
        lambda: asyncio.sleep(0.3),          # deixa a fase dos monstros assentar
    ])
    await S.handler(ws1)

    print("\n[1] Primeira conexão: criar → cidade → masmorra → agir → cair")
    check("nenhum 'Internal error' na 1ª conexão",
          not any("Internal error" in e for e in ws1.erros()), ws1.erros()[:3])
    check("lobby_state chegou", bool(ws1.msgs("lobby_state")))
    check("city_state chegou depois do start_game", bool(ws1.msgs("city_state")))
    check("enter_dungeon + game_state chegaram", bool(ws1.msgs("enter_dungeon")) and bool(ws1.msgs("game_state")))
    r, pid = _sala_e_pid(NOME)
    check("a sala e o jogador existem depois da queda", r is not None and pid is not None)
    if not r: return
    code = next(k for k, v in S.rooms.items() if v is r)
    check("o jogador ficou em players mas saiu de connections",
          pid in r.players and pid not in r.connections)
    check("connected=False depois da queda", r.players[pid].get("connected") is False)
    check("a iniciativa chegou ao herói (não travou na intro)", not registro.get("sem_vez_1"))
    if "dir" in registro:
        esperado = [registro["pos_inicial"][0] + registro["dir"][0], registro["pos_inicial"][1] + registro["dir"][1]]
        check(f"o move foi aceito (pos {registro['pos_inicial']} → {esperado})",
              registro.get("pos_apos_mover") == esperado)
    else:
        check("havia direção livre para andar", False, str(registro))
    check("a queda tirou o peão do tabuleiro (pos [-1,-1], como um desconectado)",
          list(r.players[pid]["pos"]) == [-1, -1])
    check("o jogador segue vivo e único na sala", r.players[pid].get("alive", True) and len(r.players) == 1)
    print(f"     (atacou: {registro.get('atacou') or 'nenhum monstro adjacente — pulado'})")

    # ── 2ª conexão: religar em inglês e agir ──────────────────────────────
    async def passo_mover_2():
        if not await _esperar_vez(NOME):
            registro["sem_vez_2"] = True; return None
        r, pid = _sala_e_pid(NOME)
        d = _direcao_livre(r, pid)
        if not d: return None
        registro["pos_antes_2"] = list(r.players[pid]["pos"]); registro["dir_2"] = d
        return {"type": "move", "dx": d[0], "dy": d[1]}

    async def registrar_pos_2():
        r, pid = _sala_e_pid(NOME)
        registro["pos_apos_mover_2"] = list(r.players[pid]["pos"])

    ws2 = FakeWS([
        {"type": "set_lang", "lang": "en"},
        {"type": "rejoin", "code": code, "name": NOME},
        passo_mover_2,
        registrar_pos_2,
        {"type": "attack", "target_id": "nao_existe"},   # recusa esperada → erro em inglês
    ])
    await S.handler(ws2)

    print("\n[2] Segunda conexão: rejoin → agir → erro traduzido")
    check("nenhum 'Internal error' na 2ª conexão",
          not any("Internal error" in e for e in ws2.erros()), ws2.erros()[:3])
    check("rejoin reenviou game_start + enter_dungeon + game_state",
          bool(ws2.msgs("game_start")) and bool(ws2.msgs("enter_dungeon")) and bool(ws2.msgs("game_state")))
    narr = [d.get("text", "") for d in ws2.msgs("gm_narration")]
    esperado = S.t("narracao.reconectou_se_e_voltou_a_masmorra", "en", name=NOME)
    check("a narração da reconexão saiu em inglês", esperado in narr, narr[:3])
    r, pid2 = _sala_e_pid(NOME)
    check("o rejoin religou a MESMA identidade (pid inalterado)", pid2 == pid)
    gs = ws2.msgs("game_state")[-1] if ws2.msgs("game_state") else {}
    check("o herói está no game_state recebido pela nova conexão",
          any(p.get("id") == pid for p in gs.get("players", [])))
    check("a iniciativa voltou ao herói depois do rejoin", not registro.get("sem_vez_2"))
    if "dir_2" in registro:
        esp = [registro["pos_antes_2"][0] + registro["dir_2"][0], registro["pos_antes_2"][1] + registro["dir_2"][1]]
        check("o move depois do rejoin foi aceito", registro.get("pos_apos_mover_2") == esp)
    erros2 = ws2.erros()
    check("a recusa do ataque inválido chegou", bool(erros2), erros2)
    check("a recusa saiu em inglês (sem acento português)",
          erros2 and not re.search(r"[ãõçáéíóú]", erros2[-1]), erros2[-1:] )

    print("\n[3] Higiene depois das duas conexões")
    check("LANG_BY_PID não guarda nada destas conexões", pid not in S.LANG_BY_PID and len(S.LANG_BY_PID) == 0)
    check("o jogador segue em players após a 2ª queda (partida em andamento)", pid in r.players)
    S.rooms.pop(code, None)


async def _esperar(cond, timeout=8.0):
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        try:
            if cond(): return True
        except Exception:
            pass
        await asyncio.sleep(0.05)
    return False


async def cenario_mestre():
    """Duas conexões SIMULTÂNEAS (mestre em inglês + herói em português), o
    mestre cai e religa. Cobre o ramo do mestre no rejoin — que teve o mesmo
    bug de idioma do herói — e prova que a mesma narração sai em DOIS idiomas
    para duas conexões da mesma sala."""
    MESTRE, HEROI = "Narrador", "Escudeiro"
    caixa = {}

    def sala():
        return next((r for r in S.rooms.values() if r.master_name == MESTRE or
                     any(p.get("name") == HEROI for p in r.players.values())), None)

    async def esperar_heroi_pronto():
        ok = await _esperar(lambda: any(p.get("name") == HEROI and p.get("class_id") for p in sala().players.values()))
        caixa["heroi_pronto"] = ok
    async def esperar_sala():
        ok = await _esperar(lambda: sala() is not None and sala().phase == "lobby")
        caixa["sala"] = ok
        return {"type": "join_room", "name": HEROI, "code": next(k for k, v in S.rooms.items() if v is sala())}
    async def liberar_intro():
        r = sala(); await r._liberar_intro_masmorra(True)
    async def esperar_mestre_cair():
        # o herói fica na sala até o mestre cair E religar, para receber a narração em PT
        ok = await _esperar(lambda: caixa.get("mestre_religou"), timeout=15.0)
        caixa["heroi_viu_religar"] = ok
    async def marcar_religou():
        caixa["mestre_religou"] = True
        await asyncio.sleep(0.3)

    ws_m = FakeWS([
        {"type": "set_lang", "lang": "en"},
        {"type": "create_room", "name": MESTRE},
        {"type": "claim_role", "role": "master"},
        esperar_heroi_pronto,
        {"type": "start_game"},
        {"type": "enter_dungeon"},
        liberar_intro,
        lambda: asyncio.sleep(0.3),
    ])
    ws_h = FakeWS([
        {"type": "set_lang", "lang": "pt"},
        esperar_sala,
        {"type": "select_class", "class_id": "warrior"},
        esperar_mestre_cair,
    ])

    async def mestre_cai_e_religa():
        await S.handler(ws_m)                      # 1ª conexão do mestre termina = queda
        r = sala(); caixa["mestre_ativo_apos_queda"] = r._mestre_ativo() if r else None
        caixa["master_pid_antes"] = r.master_pid if r else None
        code = next(k for k, v in S.rooms.items() if v is r)
        ws_m2 = FakeWS([
            {"type": "set_lang", "lang": "en"},
            {"type": "rejoin", "code": code, "name": MESTRE},
            marcar_religou,
        ])
        caixa["ws_m2"] = ws_m2
        await S.handler(ws_m2)

    await asyncio.gather(mestre_cai_e_religa(), S.handler(ws_h))

    print("\n[4] Mestre em inglês + herói em português, mestre cai e religa")
    r = sala()
    check("a sala existe e chegou à masmorra", r is not None and r.phase == "playing")
    if not r: return
    check("o herói entrou e escolheu classe a tempo", caixa.get("sala") and caixa.get("heroi_pronto"))
    ws_m2 = caixa.get("ws_m2")
    todos = ws_m.erros() + ws_h.erros() + (ws_m2.erros() if ws_m2 else [])
    check("nenhum 'Internal error' nas três conexões", not any("Internal error" in e for e in todos), todos[:3])
    check("sem mestre conectado, _mestre_ativo() é False", caixa.get("mestre_ativo_apos_queda") is False)
    check("o rejoin manteve o master_pid", r.master_pid == caixa.get("master_pid_antes") and r.master_pid)
    en = S.t("narracao.o_mestre_reconectou_se", "en", name=MESTRE)
    pt = S.t("narracao.o_mestre_reconectou_se", "pt", name=MESTRE)
    narr_m = [d.get("text") for d in (ws_m2.msgs("gm_narration") if ws_m2 else [])]
    narr_h = [d.get("text") for d in ws_h.msgs("gm_narration")]
    check("o mestre leu a própria reconexão em inglês", en in narr_m, narr_m[-2:])
    check("o herói leu a MESMA narração em português", pt in narr_h, narr_h[-2:])
    check("o herói recebeu o game_state da masmorra", bool(ws_h.msgs("game_state")))
    check("LANG_BY_PID limpo depois das três conexões", len(S.LANG_BY_PID) == 0)
    for k, v in list(S.rooms.items()):
        if v is r: S.rooms.pop(k, None)


if __name__ == "__main__":
    print("=" * 62); print("  FUMAÇA — handler real, ciclo do jogador em inglês"); print("=" * 62)
    try:
        asyncio.run(cenario())
        asyncio.run(cenario_mestre())
    except Exception as e:
        import traceback; traceback.print_exc()
        check(f"o cenário rodou sem exceção ({type(e).__name__}: {e})", False)
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
