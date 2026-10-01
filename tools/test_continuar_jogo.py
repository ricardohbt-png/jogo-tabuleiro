"""Continuar um jogo salvo — solo e em grupo, pelo laço de conexão REAL.

Roda da raiz:  python tools/test_continuar_jogo.py

O que cobre (decisões do autor em 2026-10-01):
  [1] Solo: ao continuar, a escolha de herói é pulada e o jogo cai direto na
      cidade, com a ficha salva (só lobby_state com `auto_start`).
  [2] Grupo, outro dia: QUALQUER membro abre o jogo e vira anfitrião; o outro
      clica em Continuar no mesmo jogo e entra na sala dele (sem "em uso"),
      com o personagem já marcado.
  [3] Amigo que chega depois do início: entra na cidade com a ficha salva; se
      o grupo está na masmorra, chega como quem subiu a escada (fora_masmorra).
  [4] Quem cai e volta pelo Continuar religa a MESMA identidade, e a reserva
      da conta é liberada ao sair (senão a conta ficaria "em uso" para sempre).
  [5] Só o progresso da CIDADE é salvo: dentro da masmorra a ficha de quem está
      lá não é gravada; a de quem subiu pela escada é.
  [6] Uma sala velha do mesmo jogo, sem ninguém, para de gravar no jogo salvo.
  [7] Jogador NOVO entra pelo código num jogo solo já na cidade: escolhe o
      herói numa tela só dele e entra; o dono não é jogado de volta ao lobby.
  [8] Mago novo com o grupo na masmorra: só entra depois das 2 magias, e
      chega pela escada (fora_masmorra).
  [9] Entrada por votação com a partida em andamento: o membro vota pela
      caixa de confirmação e o candidato entra quando aprovado.
  [10] Classe de membro ausente aparece ocupada e é recusada.
  [11] Quem desiste no meio da escolha sai da sala de espera.
"""
import asyncio, json, os, sys, tempfile, shutil
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
    """Conexão falsa (mesmo modelo de test_handler_smoke). Itens do roteiro:
    dict (mensagem) ou callable (passo; pode ser async e devolver um dict)."""
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
    def erros(self): return [str(d.get("msg", "")) for d in self.msgs("error")]


SENHA = "senha longa 1"

def login(nome):
    return {"type": "login", "username": nome, "password": SENHA}

async def esperar(cond, timeout=8.0):
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        try:
            if cond(): return True
        except Exception:
            pass
        await asyncio.sleep(0.03)
    return False

def sala_do_jogo(sid):
    return next((r for r in S.rooms.values() if r.savegame_id == sid), None)

def heroi_da_conta(r, conta):
    return next((p for p in r.players.values() if r.account_by_pid.get(p["id"]) == conta), None)

def sem_erro_interno(*wss):
    return not any("Internal error" in e or "Erro interno" in e for w in wss for e in w.erros())

def limpar_salas():
    for k in list(S.rooms):
        S.rooms.pop(k, None)
    S.SAVEGAMES_IN_USE.clear()


async def criar_jogo(conta, nome_jogo, classe, amigos=(), entrada="automatic"):
    """1º dia: cria o jogo, escolhe a classe no lobby e inicia. `amigos`:
    [(conta, classe)] que entram pelo código antes do início."""
    caixa = {}
    async def esperar_lobby():
        await esperar(lambda: caixa.get("sid") and sala_do_jogo(caixa["sid"]))
    def criado():
        sg = next((d["savegame"] for d in dono.msgs("savegame_created")), None)
        caixa["sid"] = sg and sg["id"]
        return {"type": "load_savegame", "id": caixa["sid"]}
    async def esperar_amigos():
        await esperar(lambda: all(heroi_da_conta(sala_do_jogo(caixa["sid"]), a) and
                                  heroi_da_conta(sala_do_jogo(caixa["sid"]), a).get("class_id")
                                  for a, _ in amigos))
    async def esperar_cidade():
        await esperar(lambda: sala_do_jogo(caixa["sid"]).phase == "city")
        await asyncio.sleep(0.05)
    dono = FakeWS([login(conta),
                   {"type": "create_savegame", "name": nome_jogo, "mode": "procedural",
                    "rules": {"entry_mode": entrada}},
                   lambda: asyncio.sleep(0.05), criado,
                   {"type": "select_class", "class_id": classe},
                   esperar_amigos, {"type": "start_game"}, esperar_cidade])
    outros = []
    for a, cls in amigos:
        def entrar_codigo():
            r = sala_do_jogo(caixa["sid"])
            return {"type": "join_room", "name": a_nome, "code": r.code}
        a_nome = a
        async def esperar_sala():
            await esperar(lambda: caixa.get("sid") and sala_do_jogo(caixa["sid"]))
        outros.append(FakeWS([login(a), esperar_sala, entrar_codigo,
                              {"type": "select_class", "class_id": cls}, esperar_cidade]))
    await asyncio.gather(S.handler(dono), *[S.handler(w) for w in outros])
    return caixa["sid"], dono, outros


async def cenario_solo():
    print("\n[1] Solo: continuar pula a escolha de herói")
    sid, ws1, _ = await criar_jogo("solitario", "Jornada", "warrior")
    sg = S.load_savegame(sid)
    check("1º dia: o personagem ficou vinculado à conta",
          (sg["members"].get("solitario") or {}).get("class_id") == "warrior")
    sg["characters"]["warrior"]["gold"] = 321
    S.write_savegame(sg)
    limpar_salas()

    async def esperar_cidade():
        await esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == "city")
    ws2 = FakeWS([login("solitario"), {"type": "load_savegame", "id": sid}, esperar_cidade])
    await S.handler(ws2)
    lobbies = ws2.msgs("lobby_state")
    check("só chegou lobby_state com auto_start (a tela de herói não é desenhada)",
          lobbies and all(l.get("auto_start") for l in lobbies), [l.get("auto_start") for l in lobbies])
    check("o lobby_state traz o código da sala (reconexão)", lobbies and lobbies[0].get("code"))
    cs = ws2.msgs("city_state")
    check("caiu direto na cidade", bool(cs) and bool(ws2.msgs("game_start")))
    eu = next((p for p in (cs[-1].get("players") if cs else []) if p.get("name") == "solitario"), {})
    check("com a ficha salva (ouro 321)", eu.get("gold") == 321, eu.get("gold"))
    check("o city_state traz o código da sala", cs and cs[-1].get("code"))
    check("sem erro interno", sem_erro_interno(ws1, ws2), ws2.erros())
    check("a conta foi liberada ao sair", "solitario" not in S.ACCOUNTS_ONLINE)
    limpar_salas()


async def cenario_grupo():
    print("\n[2] Grupo, outro dia: qualquer membro abre; o outro entra pelo Continuar")
    sid, _, _ = await criar_jogo("ana", "Companhia", "warrior", amigos=[("bia", "rogue")])
    sg = S.load_savegame(sid)
    check("1º dia: os dois personagens ficaram vinculados",
          sg["members"]["ana"]["class_id"] == "warrior" and sg["members"]["bia"]["class_id"] == "rogue")
    limpar_salas()

    caixa = {}
    async def esperar_ana_no_lobby():
        await esperar(lambda: sala_do_jogo(sid) and heroi_da_conta(sala_do_jogo(sid), "ana"))
        r = sala_do_jogo(sid)
        caixa["lobby"] = {p["name"]: p.get("class_id") for p in r.players.values()}
        caixa["host_conta"] = r.account_by_pid.get(r.host_pid)
    async def esperar_cidade():
        await esperar(lambda: sala_do_jogo(sid).phase == "city")
        await asyncio.sleep(0.05)
    async def esperar_bia_abrir():
        await esperar(lambda: sala_do_jogo(sid) is not None)
    # Bia (não foi quem criou) abre primeiro e vira anfitriã.
    ws_bia = FakeWS([login("bia"), {"type": "load_savegame", "id": sid},
                     esperar_ana_no_lobby, {"type": "start_game"}, esperar_cidade])
    ws_ana = FakeWS([login("ana"), esperar_bia_abrir, {"type": "load_savegame", "id": sid},
                     esperar_cidade])
    await asyncio.gather(S.handler(ws_bia), S.handler(ws_ana))
    check("quem abriu primeiro (bia, não a criadora) virou anfitriã", caixa.get("host_conta") == "bia")
    check("os dois entraram com o personagem já marcado",
          caixa.get("lobby") == {"bia": "rogue", "ana": "warrior"}, caixa.get("lobby"))
    check("ana NÃO recebeu 'jogo em uso'",
          not any("uso" in e.lower() or "use" in e.lower() for e in ws_ana.erros()), ws_ana.erros())
    check("em grupo o lobby aparece (sem auto_start)",
          ws_bia.msgs("lobby_state") and not any(l.get("auto_start") for l in ws_bia.msgs("lobby_state")))
    check("os dois chegaram à cidade", bool(ws_bia.msgs("city_state")) and bool(ws_ana.msgs("city_state")))
    check("sem erro interno", sem_erro_interno(ws_bia, ws_ana), ws_bia.erros() + ws_ana.erros())
    limpar_salas()
    return sid


async def cenario_atrasado(sid):
    print("\n[3] Amigo que chega depois do início: cidade e masmorra")
    sg = S.load_savegame(sid); sg["characters"]["warrior"]["gold"] = 444; S.write_savegame(sg)
    caixa = {}
    async def esperar_cidade():
        await esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == "city")
    async def esperar_ana_entrar():
        await esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "ana") is not None)
        a = heroi_da_conta(sala_do_jogo(sid), "ana")
        caixa["ana_ouro"] = a.get("gold")
        caixa["ana_ativa"] = a.get("connected", True)
    async def esperar_ana_sair():
        await esperar(lambda: not heroi_da_conta(sala_do_jogo(sid), "ana").get("connected", True))
    # bia abre (2 membros → lobby) e inicia SOZINHA; ana chega com a cidade aberta.
    ws_bia = FakeWS([login("bia"), {"type": "load_savegame", "id": sid},
                     lambda: esperar(lambda: sala_do_jogo(sid) and heroi_da_conta(sala_do_jogo(sid), "bia")),
                     {"type": "start_game"}, lambda: asyncio.sleep(0.05),
                     esperar_ana_entrar, esperar_ana_sair])
    ws_ana = FakeWS([login("ana"), {"type": "load_savegame", "id": sid}, lambda: asyncio.sleep(0.1)])
    async def ana_depois():
        await esperar_cidade()
        await S.handler(ws_ana)
    await asyncio.gather(S.handler(ws_bia), ana_depois())
    check("ana entrou com a partida já na cidade", caixa.get("ana_ouro") is not None)
    check("com a ficha salva (ouro 444)", caixa.get("ana_ouro") == 444, caixa.get("ana_ouro"))
    check("ana recebeu game_start + city_state", bool(ws_ana.msgs("game_start")) and bool(ws_ana.msgs("city_state")))
    check("ana não recebeu lobby (não escolhe herói)", not ws_ana.msgs("lobby_state"))
    check("sem erro interno (cidade)", sem_erro_interno(ws_bia, ws_ana), ws_bia.erros() + ws_ana.erros())
    limpar_salas()

    # Masmorra: bia entra; ana chega e vira 'fora_masmorra' com espera zero.
    caixa = {}
    async def liberar_intro():
        await esperar(lambda: sala_do_jogo(sid).phase == "playing")
        await sala_do_jogo(sid)._liberar_intro_masmorra(True)
    async def esperar_ana_e_olhar():
        await esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "ana") is not None)
        a = heroi_da_conta(sala_do_jogo(sid), "ana")
        caixa["fora"] = dict(a.get("fora_masmorra") or {})
        caixa["pos"] = list(a.get("pos") or [])
        caixa["ativo"] = sala_do_jogo(sid)._ativo(a)
        await esperar(lambda: not heroi_da_conta(sala_do_jogo(sid), "ana").get("connected", True))
    ws_bia = FakeWS([login("bia"), {"type": "load_savegame", "id": sid},
                     lambda: esperar(lambda: sala_do_jogo(sid) and heroi_da_conta(sala_do_jogo(sid), "bia")),
                     {"type": "start_game"}, lambda: asyncio.sleep(0.05),
                     {"type": "enter_dungeon"}, liberar_intro, esperar_ana_e_olhar])
    ws_ana = FakeWS([login("ana"), {"type": "load_savegame", "id": sid}, lambda: asyncio.sleep(0.1)])
    async def ana_na_masmorra():
        await esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == "playing"
                      and not sala_do_jogo(sid).dungeon_intro_active)
        await S.handler(ws_ana)
    await asyncio.gather(S.handler(ws_bia), ana_na_masmorra())
    check("ana chegou como quem está na cidade (fora_masmorra, espera 0)",
          caixa.get("fora") == {"rodadas_restantes": 0}, caixa.get("fora"))
    check("fora do tabuleiro e fora dos turnos", caixa.get("pos") == [-1, -1] and caixa.get("ativo") is False)
    check("ana viu a cidade, não a masmorra",
          bool(ws_ana.msgs("city_state")) and not ws_ana.msgs("game_state"))
    check("sem erro interno (masmorra)", sem_erro_interno(ws_bia, ws_ana), ws_bia.erros() + ws_ana.erros())
    limpar_salas()


async def cenario_religar(sid):
    print("\n[4] Cair e voltar pelo Continuar religa a mesma identidade")
    caixa = {}
    async def esperar_ana_cair():
        await esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "ana") is not None)
        a = heroi_da_conta(sala_do_jogo(sid), "ana"); caixa["pid1"] = a["id"]
        await esperar(lambda: not a.get("connected", True))
        caixa["caiu"] = True
        await esperar(lambda: a.get("connected", True) and caixa.get("voltou"), timeout=10)
        caixa["pid2"] = heroi_da_conta(sala_do_jogo(sid), "ana")["id"]
        caixa["n_ana"] = sum(1 for p in sala_do_jogo(sid).players.values()
                             if sala_do_jogo(sid).account_by_pid.get(p["id"]) == "ana")
        caixa["online_durante"] = S.ACCOUNTS_ONLINE.get("ana")
        caixa["voltou_ok"] = True
        await asyncio.sleep(0.1)
    ws_bia = FakeWS([login("bia"), {"type": "load_savegame", "id": sid},
                     lambda: esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "ana")),
                     {"type": "start_game"}, esperar_ana_cair])
    ws_ana1 = FakeWS([login("ana"),
                      lambda: esperar(lambda: sala_do_jogo(sid) is not None),
                      {"type": "load_savegame", "id": sid},
                      lambda: esperar(lambda: sala_do_jogo(sid).phase == "city")])
    async def marcar(): caixa["voltou"] = True; await asyncio.sleep(0.2)
    ws_ana2 = FakeWS([login("ana"), {"type": "load_savegame", "id": sid}, marcar])
    async def ana():
        await S.handler(ws_ana1)
        await esperar(lambda: caixa.get("caiu"))
        await S.handler(ws_ana2)
    await asyncio.gather(S.handler(ws_bia), ana())
    check("ana voltou e a sala reconheceu", caixa.get("voltou_ok"))
    check("religou a MESMA identidade (pid igual)", caixa.get("pid1") and caixa.get("pid1") == caixa.get("pid2"))
    check("sem herói duplicado", caixa.get("n_ana") == 1, caixa.get("n_ana"))
    check("a reserva da conta seguiu o pid religado", caixa.get("online_durante") == caixa.get("pid1"))
    check("ao sair, a conta foi liberada", "ana" not in S.ACCOUNTS_ONLINE and "bia" not in S.ACCOUNTS_ONLINE,
          dict(S.ACCOUNTS_ONLINE))
    check("religar trouxe game_start + city_state", bool(ws_ana2.msgs("game_start")) and bool(ws_ana2.msgs("city_state")))
    check("sem erro interno", sem_erro_interno(ws_bia, ws_ana1, ws_ana2),
          ws_bia.erros() + ws_ana1.erros() + ws_ana2.erros())
    limpar_salas()


def cenario_so_cidade():
    print("\n[5] Só o progresso da cidade é salvo")
    sg = S.create_savegame("Cofre", "dono", "procedural", None, False)
    sg["members"]["dono"] = {"class_id": "warrior", "status": "active"}
    sg["members"]["outro"] = {"class_id": "mage", "status": "active"}
    sg["characters"]["warrior"] = S.snapshot_character(S.make_player("x", "x", "warrior", 0))
    sg["characters"]["mage"] = S.snapshot_character(S.make_player("y", "y", "mage", 0))
    sg["characters"]["warrior"]["gold"] = 10; sg["characters"]["mage"]["gold"] = 20
    S.write_savegame(sg)
    r = S.GameRoom("COFR"); r.savegame_id = sg["id"]; r.savegame = sg
    w = S.make_player("w", "dono", "warrior", 0); m = S.make_player("m", "outro", "mage", 1)
    r.players = {"w": w, "m": m}
    r.phase = "playing"
    w["gold"] = 999; m["gold"] = 888
    m["fora_masmorra"] = {"rodadas_restantes": 1}
    r.renome = 7
    r._checkpoint_savegame()
    d = S.load_savegame(sg["id"])
    check("na masmorra, quem está lá dentro NÃO é gravado", d["characters"]["warrior"]["gold"] == 10)
    check("quem subiu pela escada (na cidade) é gravado", d["characters"]["mage"]["gold"] == 888)
    check("o estado da sala (renome) segue sendo gravado", d.get("renome") == 7)
    r.phase = "city"; r._checkpoint_savegame()
    d = S.load_savegame(sg["id"])
    check("na cidade, todos são gravados", d["characters"]["warrior"]["gold"] == 999)


def cenario_sala_velha():
    print("\n[6] Sala velha do mesmo jogo para de gravar")
    sg = S.create_savegame("Velho", "dono", "procedural", None, False)
    salas = {}
    r1, e = S.try_open_savegame_room("dono", sg["id"], salas)
    S.SAVEGAMES_IN_USE.pop(sg["id"], None)   # todos saíram (o finally faz isto)
    check("sem ninguém conectado, não há sala aberta para entrar",
          S.sala_aberta_do_jogo_salvo(sg["id"], salas) is None)
    r2, e2 = S.try_open_savegame_room("dono", sg["id"], salas)
    check("abre uma sala nova", r2 is not None and r2 is not r1, e2)
    check("a velha foi desligada do jogo salvo", r1.savegame is None and r1.savegame_id is None)
    check("e saiu da lista de salas", r1.code not in salas)
    S.SAVEGAMES_IN_USE.clear()


async def jogo_aberto_por(conta, sid, extra=()):
    """Roteiro do dono: abre o jogo salvo (solo → direto na cidade) e fica
    conectado executando `extra` (passos que esperam o outro jogador)."""
    return FakeWS([login(conta), {"type": "load_savegame", "id": sid},
                   lambda: esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase in ("city", "lobby"))]
                  + list(extra))


async def cenario_novo_no_solo():
    print("\n[7] Jogador novo entra num jogo solo já na cidade")
    sid, _, _ = await criar_jogo("gil", "Solo do Gil", "warrior")
    limpar_salas()
    caixa = {}
    async def esperar_hana_entrar():
        await esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "hana") is not None, timeout=10)
        caixa["hana"] = heroi_da_conta(sala_do_jogo(sid), "hana")
        await esperar(lambda: not caixa["hana"].get("connected", True) or caixa.get("fim"), timeout=5)
    ws_gil = await jogo_aberto_por("gil", sid, [esperar_hana_entrar])
    def entrar_codigo():
        return {"type": "join_room", "name": "hana", "code": sala_do_jogo(sid).code}
    async def olhar_espera():
        r = sala_do_jogo(sid)
        caixa["esperando"] = list(r.aguardando)
        caixa["em_players"] = heroi_da_conta(r, "hana") is not None
        caixa["recebeu_city_antes"] = bool(ws_hana.msgs("city_state"))
    async def fim(): caixa["fim"] = True; await asyncio.sleep(0.05)
    ws_hana = FakeWS([login("hana"),
                      lambda: esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == "city"),
                      entrar_codigo, lambda: asyncio.sleep(0.05), olhar_espera,
                      {"type": "select_class", "class_id": "rogue"},
                      lambda: esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "hana") is not None), fim])
    await asyncio.gather(S.handler(ws_gil), S.handler(ws_hana))
    lob = ws_hana.msgs("lobby_state")
    check("hana recebeu a escolha de herói marcada como entrada tardia",
          bool(lob) and lob[0].get("entrada_tardia") is True and lob[0].get("host") is None)
    check("o herói do dono aparece ocupado", lob and "warrior" in (lob[0].get("taken_classes") or []))
    check("enquanto escolhe, fica na sala de espera (fora de players)",
          len(caixa.get("esperando") or []) == 1 and caixa.get("em_players") is False)
    check("e não recebe o estado da cidade antes de escolher", caixa.get("recebeu_city_antes") is False)
    h = caixa.get("hana") or {}
    check("depois de escolher, entra como ladina", h.get("class_id") == "rogue")
    check("recebeu game_start + city_state", bool(ws_hana.msgs("game_start")) and bool(ws_hana.msgs("city_state")))
    sg = S.load_savegame(sid)
    check("ficou vinculada ao jogo salvo", (sg["members"].get("hana") or {}).get("class_id") == "rogue")
    check("o dono NÃO recebeu lobby_state depois de já estar na cidade",
          all(l.get("auto_start") for l in ws_gil.msgs("lobby_state")), [l.get("auto_start") for l in ws_gil.msgs("lobby_state")])
    narr = [str(d.get("text")) for d in ws_gil.msgs("gm_narration")]
    check("o dono viu a narração da chegada", any("hana" in n for n in narr), narr[-3:])
    check("sem erro interno", sem_erro_interno(ws_gil, ws_hana), ws_gil.erros() + ws_hana.erros())
    limpar_salas()
    return sid


async def cenario_mago_novo_na_masmorra(sid):
    print("\n[8] Mago novo com o grupo na masmorra")
    caixa = {}
    async def liberar_intro():
        await esperar(lambda: sala_do_jogo(sid).phase == "playing")
        await sala_do_jogo(sid)._liberar_intro_masmorra(True)
    async def esperar_ivo():
        await esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "ivo") is not None, timeout=10)
        i = heroi_da_conta(sala_do_jogo(sid), "ivo") or {}
        caixa["ivo"] = {"class_id": i.get("class_id"), "fora": i.get("fora_masmorra"),
                        "magias": list(i.get("magias_conhecidas") or [])}
        await asyncio.sleep(0.1)
    # Abre o jogo (gil + hana são membros → lobby); gil inicia sozinho e entra.
    ws_gil = FakeWS([login("gil"), {"type": "load_savegame", "id": sid},
                     lambda: esperar(lambda: sala_do_jogo(sid) and heroi_da_conta(sala_do_jogo(sid), "gil")),
                     {"type": "start_game"}, lambda: asyncio.sleep(0.05),
                     {"type": "enter_dungeon"}, liberar_intro, esperar_ivo])
    def entrar_codigo():
        return {"type": "join_room", "name": "ivo", "code": sala_do_jogo(sid).code}
    async def olhar_antes_magias():
        caixa["antes"] = heroi_da_conta(sala_do_jogo(sid), "ivo") is None and len(sala_do_jogo(sid).aguardando) == 1
    magias = [m for m, d in S.GRIMORIO.items() if "mage" in d.get("classe", []) and d.get("circulo") == "primeiro"][:2]
    ws_ivo = FakeWS([login("ivo"),
                     lambda: esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == "playing"
                                     and not sala_do_jogo(sid).dungeon_intro_active),
                     entrar_codigo, {"type": "select_class", "class_id": "mage"},
                     lambda: asyncio.sleep(0.05), olhar_antes_magias,
                     {"type": "set_known_spells", "ids": magias},
                     lambda: esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "ivo") is not None),
                     lambda: asyncio.sleep(0.15)])
    await asyncio.gather(S.handler(ws_gil), S.handler(ws_ivo))
    check("escolher mago sem as magias ainda não entra", caixa.get("antes") is True)
    iv = caixa.get("ivo") or {}
    check("entrou como mago depois das magias", iv.get("class_id") == "mage")
    check("com as 2 magias escolhidas", all(m in iv.get("magias", []) for m in magias), iv.get("magias"))
    check("chegou pela escada (fora_masmorra, espera 0)", iv.get("fora") == {"rodadas_restantes": 0}, iv.get("fora"))
    check("viu a cidade, não a masmorra", bool(ws_ivo.msgs("city_state")) and not ws_ivo.msgs("game_state"))
    check("sem erro interno", sem_erro_interno(ws_gil, ws_ivo), ws_gil.erros() + ws_ivo.erros())
    limpar_salas()


async def cenario_votacao():
    print("\n[9] Entrada por votação com a partida em andamento")
    sid, _, _ = await criar_jogo("julia", "Mesa da Julia", "paladin", entrada="vote")
    limpar_salas()
    caixa = {}
    async def votar_sim():
        await esperar(lambda: ws_julia.msgs("campaign_vote_opened"), timeout=10)
        await esperar(lambda: "pendente" in caixa, timeout=5)   # só vota depois da checagem
        v = ws_julia.msgs("campaign_vote_opened")[-1]["vote"]
        caixa["voto"] = v
        return {"type": "campaign_vote", "vote_id": v["id"], "approve": True}
    async def esperar_kai():
        await esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "kai") is not None)
        await asyncio.sleep(0.1)
    ws_julia = await jogo_aberto_por("julia", sid, [votar_sim, esperar_kai])
    def entrar_codigo():
        return {"type": "join_room", "name": "kai", "code": sala_do_jogo(sid).code}
    async def olhar_pendente():
        caixa["pendente"] = (heroi_da_conta(sala_do_jogo(sid), "kai") is None
                             and len(sala_do_jogo(sid).aguardando) == 1)
    ws_kai = FakeWS([login("kai"),
                     lambda: esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == "city"),
                     entrar_codigo, {"type": "select_class", "class_id": "ranger" if "ranger" in S.CLASSES else "bard"},
                     lambda: asyncio.sleep(0.05), olhar_pendente,
                     lambda: esperar(lambda: heroi_da_conta(sala_do_jogo(sid), "kai") is not None),
                     lambda: asyncio.sleep(0.1)])
    await asyncio.gather(S.handler(ws_julia), S.handler(ws_kai))
    check("o pedido abriu votação para a dona", bool(caixa.get("voto")) and caixa["voto"].get("candidate") == "kai")
    check("enquanto a votação está aberta, kai espera", caixa.get("pendente") is True)
    check("aprovado, kai entrou na partida", bool(ws_kai.msgs("city_state")))
    check("a dona NÃO foi jogada para a tela de heróis pela votação",
          all(l.get("auto_start") for l in ws_julia.msgs("lobby_state")))
    check("sem erro interno", sem_erro_interno(ws_julia, ws_kai), ws_julia.erros() + ws_kai.erros())
    limpar_salas()


async def cenario_classe_de_ausente(sid_grupo):
    print("\n[10] Classe de membro ausente é recusada; [11] desistir limpa a espera")
    caixa = {}
    async def esperar_lu_sair():
        await esperar(lambda: caixa.get("tentou"), timeout=10)
        await esperar(lambda: not sala_do_jogo(sid_grupo).aguardando, timeout=5)
        caixa["espera_vazia"] = not sala_do_jogo(sid_grupo).aguardando
        caixa["conta_fora"] = "lu" not in sala_do_jogo(sid_grupo).account_by_pid.values()
    # bia abre (ana ausente) e inicia sozinha
    ws_bia = FakeWS([login("bia"), {"type": "load_savegame", "id": sid_grupo},
                     lambda: esperar(lambda: sala_do_jogo(sid_grupo) and heroi_da_conta(sala_do_jogo(sid_grupo), "bia")),
                     {"type": "start_game"}, esperar_lu_sair])
    def entrar_codigo():
        return {"type": "join_room", "name": "lu", "code": sala_do_jogo(sid_grupo).code}
    async def marcar(): caixa["tentou"] = True
    ws_lu = FakeWS([login("lu"),
                    lambda: esperar(lambda: sala_do_jogo(sid_grupo) and sala_do_jogo(sid_grupo).phase == "city"),
                    entrar_codigo, {"type": "select_class", "class_id": "warrior"},
                    lambda: asyncio.sleep(0.05), marcar])
    await asyncio.gather(S.handler(ws_bia), S.handler(ws_lu))
    lob = ws_lu.msgs("lobby_state")
    check("o guerreiro da ana (ausente) aparece ocupado", lob and "warrior" in (lob[0].get("taken_classes") or []))
    check("escolher o personagem da ana é recusado", any(ws_lu.erros()) and not ws_lu.msgs("city_state"), ws_lu.erros())
    check("ao desistir, a sala de espera fica vazia", caixa.get("espera_vazia") is True)
    check("e a conta sai da sala", caixa.get("conta_fora") is True)
    check("a conta foi liberada", "lu" not in S.ACCOUNTS_ONLINE)
    check("sem erro interno", sem_erro_interno(ws_bia, ws_lu), ws_bia.erros() + ws_lu.erros())
    limpar_salas()


async def main():
    tmp = tempfile.mkdtemp()
    velha = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        for conta in ("solitario", "ana", "bia", "gil", "hana", "ivo", "julia", "kai", "lu"):
            acc, e = await S.create_account(conta, SENHA)
            assert acc, e
        await cenario_solo()
        sid = await cenario_grupo()
        await cenario_atrasado(sid)
        await cenario_religar(sid)
        sid_gil = await cenario_novo_no_solo()
        await cenario_mago_novo_na_masmorra(sid_gil)
        await cenario_votacao()
        await cenario_classe_de_ausente(sid)
        cenario_so_cidade()
        cenario_sala_velha()
    finally:
        limpar_salas()
        S.LOJA = velha
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 62); print("  CONTINUAR JOGO SALVO — solo e grupo"); print("=" * 62)
    asyncio.run(main())
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)
