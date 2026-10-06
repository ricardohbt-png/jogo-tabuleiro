"""Mestre fora da mesa: um jogador é o anfitrião substituto; o Mestre reassume
ao voltar. Pelo laço de conexão REAL (server.handler).

Roda da raiz:  python tools/test_mestre_substituto.py

  [1] 1º dia: Mestre cria e inicia com 2 jogadores; cai na cidade -> o
      anfitrião passa a um jogador; volta pelo Continuar -> reassume.
  [2] Outro dia, sem o Mestre: um jogador abre o jogo e inicia; o Mestre
      chega na cidade e assume Mestre e anfitrião (com o pid no game_start).
  [3] Mesmo sem o Mestre, na masmorra: ele chega, assume; cai de novo ->
      o anfitrião volta a um jogador e os monstros ficam na IA.
  [4] Mestre que chega ao lobby aberto pelos jogadores senta como Mestre.
  [5] Encerrar: um jogador abre o capítulo seguinte; o Mestre volta e reassume.
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
    """Conexão falsa: dict = mensagem; callable = passo (pode ser async)."""
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
    def narrou(self, trecho):
        return any(trecho in str(d.get("text", "")) for d in self.msgs("gm_narration"))


SENHA = "senha longa 1"
def login(nome): return {"type": "login", "username": nome, "password": SENHA}

async def esperar(cond, timeout=8.0):
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        try:
            if cond(): return True
        except Exception:
            pass
        await asyncio.sleep(0.03)
    return False

def sala(sid):
    return next((r for r in S.rooms.values() if r.savegame_id == sid and r.connections), None) \
        or next((r for r in S.rooms.values() if r.savegame_id == sid), None)

def heroi_da_conta(r, conta):
    return next((p for p in r.players.values() if r.account_by_pid.get(p["id"]) == conta), None)

def conta_do_anfitriao(r):
    return r.account_by_pid.get(r.host_pid)

def limpar_salas():
    for k in list(S.rooms):
        S.rooms.pop(k, None)
    S.SAVEGAMES_IN_USE.clear()

def sem_erro_interno(*wss):
    return not any("Internal error" in e or "Erro interno" in e for w in wss for e in w.erros())


async def cenario_primeiro_dia():
    print("\n[1] 1º dia: o Mestre cai na cidade e volta")
    caixa = {}
    def criado():
        sg = next((d["savegame"] for d in mestre.msgs("savegame_created")), None)
        caixa["sid"] = sg and sg["id"]
        return {"type": "load_savegame", "id": caixa["sid"]}
    async def esperar_sala():
        await esperar(lambda: caixa.get("sid") and sala(caixa["sid"]))
    def codigo(nome):
        return lambda: {"type": "join_room", "name": nome, "code": sala(caixa["sid"]).code}
    async def esperar_herois():
        await esperar(lambda: all((heroi_da_conta(sala(caixa["sid"]), c) or {}).get("class_id")
                                  for c in ("ana", "bia")))
    async def esperar_cidade():
        await esperar(lambda: sala(caixa["sid"]).phase == "city")
        await asyncio.sleep(0.05)
    async def mestre_saiu():
        await esperar(lambda: caixa.get("saiu"))
    async def anotar_saida():
        r = sala(caixa["sid"])
        caixa["mestre_pid"] = r.master_pid
        caixa["saiu"] = True
    async def esperar_substituto():
        r = sala(caixa["sid"])
        await esperar(lambda: r.master_pid not in r.connections and r.host_pid != r.master_pid)
        caixa["host_sem_mestre"] = conta_do_anfitriao(r)
        caixa["voltar"] = True
    async def esperar_volta():
        await esperar(lambda: caixa.get("voltou"))
    mestre = FakeWS([login("mestre"),
                     {"type": "create_savegame", "name": "Mesa", "mode": "procedural", "has_master": True,
                      "rules": {"entry_mode": "automatic"}},
                     lambda: asyncio.sleep(0.05), criado,
                     esperar_herois, {"type": "start_game"}, esperar_cidade, anotar_saida])
    ana = FakeWS([login("ana"), esperar_sala, codigo("ana"),
                  {"type": "select_class", "class_id": "warrior"}, esperar_cidade,
                  mestre_saiu, esperar_substituto, esperar_volta])
    bia = FakeWS([login("bia"), esperar_sala, codigo("bia"),
                  {"type": "select_class", "class_id": "rogue"}, esperar_cidade,
                  mestre_saiu, esperar_volta])
    async def volta_do_mestre():
        await esperar(lambda: caixa.get("voltar"), timeout=15)
        def recordar():
            r = sala(caixa["sid"])
            caixa["host_volta"] = r.host_pid
            caixa["mestre_volta"] = r.master_pid
            caixa["voltou"] = True
        m2 = FakeWS([login("mestre"), {"type": "load_savegame", "id": caixa["sid"]},
                     lambda: esperar(lambda: sala(caixa["sid"]).master_pid in sala(caixa["sid"]).connections),
                     recordar])
        await S.handler(m2)
        return m2
    _, _, _, m2 = await asyncio.gather(S.handler(mestre), S.handler(ana), S.handler(bia), volta_do_mestre())
    check("cidade com o Mestre como anfitrião no início",
          caixa.get("mestre_pid") and S.load_savegame(caixa["sid"])["has_master"])
    check("Mestre caiu: o anfitrião passou a um jogador", caixa.get("host_sem_mestre") in ("ana", "bia"),
          caixa.get("host_sem_mestre"))
    check("narração avisa quem é o anfitrião", ana.narrou("anfitrião até ele voltar"))
    check("Mestre voltou com a mesma identidade", caixa.get("mestre_volta") == caixa.get("mestre_pid"))
    check("e reassumiu o anfitrião", caixa.get("host_volta") == caixa.get("mestre_pid"))
    check("game_start leva o pid do Mestre",
          any(d.get("pid") == caixa.get("mestre_pid") for d in m2.msgs("game_start")))
    check("sem erro interno", sem_erro_interno(mestre, ana, bia, m2))
    limpar_salas()
    return caixa["sid"]


async def cenario_sem_mestre(sid):
    print("\n[2]/[3] Outro dia sem o Mestre: os jogadores abrem; ele chega na cidade e na masmorra")
    caixa = {}
    async def esperar_sala():
        await esperar(lambda: sala(sid) and heroi_da_conta(sala(sid), "ana"))
    async def esperar_bia():
        await esperar(lambda: heroi_da_conta(sala(sid), "bia"))
    async def esperar_cidade():
        await esperar(lambda: sala(sid).phase == "city")
        await asyncio.sleep(0.05)
        r = sala(sid)
        caixa["host_cidade"] = conta_do_anfitriao(r)
        caixa["mestre_cidade"] = r.master_pid
        caixa["cidade"] = True
    async def esperar_mestre_cidade():
        await esperar(lambda: caixa.get("mestre_chegou"), timeout=15)
    async def entrar_masmorra_depois():
        await esperar(lambda: caixa.get("mestre_saiu_cidade"), timeout=15)
        return {"type": "enter_dungeon"}
    async def liberar_intro():
        r = sala(sid)
        await esperar(lambda: r.phase == "playing")
        await r._liberar_intro_masmorra(True)
        caixa["masmorra"] = True
    async def fim():
        await esperar(lambda: caixa.get("fim"), timeout=20)
    ana = FakeWS([login("ana"), {"type": "load_savegame", "id": sid}, esperar_bia,
                  {"type": "start_game"}, esperar_cidade, esperar_mestre_cidade,
                  entrar_masmorra_depois, liberar_intro, fim])
    bia = FakeWS([login("bia"), esperar_sala, {"type": "load_savegame", "id": sid}, fim])

    async def mestre_na_cidade():
        await esperar(lambda: caixa.get("cidade"), timeout=15)
        def anotar():
            r = sala(sid)
            caixa["m_cidade_pid"] = r.master_pid
            caixa["m_cidade_host"] = r.host_pid
            caixa["mestre_chegou"] = True
        m = FakeWS([login("mestre"), {"type": "load_savegame", "id": sid},
                    lambda: esperar(lambda: sala(sid).master_pid), anotar])
        await S.handler(m)
        r = sala(sid)
        await esperar(lambda: r.host_pid != r.master_pid)
        caixa["host_apos_saida_cidade"] = conta_do_anfitriao(r)
        caixa["mestre_saiu_cidade"] = True
        # [3] na masmorra
        await esperar(lambda: caixa.get("masmorra"), timeout=15)
        def anotar2():
            caixa["m_mas_host"] = r.host_pid
            caixa["m_mas_pid"] = r.master_pid
            caixa["ativo"] = r._mestre_ativo()
        m2 = FakeWS([login("mestre"), {"type": "load_savegame", "id": sid},
                     lambda: esperar(lambda: r.master_pid in r.connections), anotar2])
        await S.handler(m2)
        await esperar(lambda: r.host_pid != r.master_pid)
        caixa["host_apos_saida_mas"] = conta_do_anfitriao(r)
        caixa["ativo_depois"] = r._mestre_ativo()
        caixa["fim"] = True
        return m, m2
    _, _, (m, m2) = await asyncio.gather(S.handler(ana), S.handler(bia), mestre_na_cidade())
    check("[2] jogadora abriu o jogo com Mestre sem ele", caixa.get("host_cidade") == "ana",
          ana.erros())
    check("[2] cidade sem Mestre na sala", caixa.get("mestre_cidade") is None)
    check("[2] Mestre chegou na cidade e virou o Mestre",
          caixa.get("m_cidade_pid") and caixa.get("m_cidade_host") == caixa.get("m_cidade_pid"))
    check("[2] game_start leva o pid dele",
          any(d.get("pid") == caixa.get("m_cidade_pid") for d in m.msgs("game_start")))
    check("[2] recebeu o city_state", bool(m.msgs("city_state")))
    check("[2] narração da chegada", ana.narrou("chegou e assume a mesa"))
    check("[2] ao sair, o anfitrião volta a um jogador", caixa.get("host_apos_saida_cidade") in ("ana", "bia"))
    check("[3] na masmorra ele reassume (mesma identidade)",
          caixa.get("m_mas_pid") == caixa.get("m_cidade_pid") and caixa.get("m_mas_host") == caixa.get("m_mas_pid"))
    check("[3] com ele conectado o Mestre está ativo", caixa.get("ativo") is True)
    check("[3] entra na masmorra (enter_dungeon)", bool(m2.msgs("enter_dungeon")))
    check("[3] caiu: anfitrião a um jogador e monstros na IA",
          caixa.get("host_apos_saida_mas") in ("ana", "bia") and caixa.get("ativo_depois") is False)
    check("sem erro interno", sem_erro_interno(ana, bia, m, m2))
    limpar_salas()


async def cenario_lobby(sid):
    print("\n[4] Mestre chega ao lobby aberto pelos jogadores")
    caixa = {}
    async def fim():
        await esperar(lambda: caixa.get("fim"), timeout=15)
    ana = FakeWS([login("ana"), {"type": "load_savegame", "id": sid}, fim])
    async def mestre():
        await esperar(lambda: sala(sid) and heroi_da_conta(sala(sid), "ana"))
        def anotar():
            r = sala(sid)
            mp = r.master_pid
            caixa["ok"] = bool(mp) and r.players.get(mp, {}).get("is_master") and r.host_pid == mp
            caixa["fim"] = True
        m = FakeWS([login("mestre"), {"type": "load_savegame", "id": sid},
                    lambda: esperar(lambda: sala(sid).master_pid), anotar])
        await S.handler(m)
        return m
    _, m = await asyncio.gather(S.handler(ana), mestre())
    check("Mestre sentou como Mestre e anfitrião no lobby", caixa.get("ok"), m.erros())
    check("sem erro interno", sem_erro_interno(ana, m))
    limpar_salas()


async def cenario_encerrar(sid):
    print("\n[5] Encerrar: jogador abre o capítulo; o Mestre volta e reassume")
    ok, e = S.abandon_master_campaign(sid, "mestre")
    check("Mestre encerrou", ok, e)
    ok, e = S.try_novo_capitulo("bia", sid, "Sem ele", None)
    sg = S.load_savegame(sid)
    check("bia abriu o capítulo seguinte; o jogo segue do Mestre",
          ok and sg["status"] == "active" and sg["master_account"] == "mestre" and sg["has_master"], e)
    await cenario_lobby(sid)


async def main():
    tmp = tempfile.mkdtemp()
    velha = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        for conta in ("mestre", "ana", "bia"):
            acc, e = await S.create_account(conta, SENHA)
            assert acc, e
        sid = await cenario_primeiro_dia()
        await cenario_sem_mestre(sid)
        await cenario_lobby(sid)
        await cenario_encerrar(sid)
    finally:
        limpar_salas()
        S.LOJA = velha
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 62); print("  MESTRE FORA: ANFITRIÃO SUBSTITUTO"); print("=" * 62)
    asyncio.run(main())
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)
