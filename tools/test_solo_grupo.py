"""Solo com grupo (1 a 6 heróis numa conexão) — servidor.

Roda da raiz:  python tools/test_solo_grupo.py

Seções:
  [0] helpers de procuração (GameRoom direto, sem handler)
  [1] select_party no lobby
  [2] início: vínculo no jogo salvo, magias por herói, XP dividido
  [3] masmorra: a vez passa entre os heróis; ação alheia/fora da vez recusada
  [4] escada: herói fora só espera enquanto o grupo está dentro
  [5] queda e volta religam todos os heróis
  [6] Continuar na cidade recria o grupo
  [7] Continuar com foto da masmorra recria o grupo dentro dela
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
    """Conexão falsa (modelo de test_handler_smoke). Itens do roteiro: dict
    (mensagem) ou callable (passo; pode ser async e devolver um dict)."""
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

def txt(chave, lang="pt"):
    """Texto de uma chave de idioma, como o cliente recebe."""
    return S._t_render(S.T(chave), lang)

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

def limpar_salas():
    for k in list(S.rooms):
        S.rooms.pop(k, None)
    S.SAVEGAMES_IN_USE.clear()

def duas_magias(cls):
    return [k for k, m in S.GRIMORIO.items()
            if cls in m.get("classe", []) and m.get("circulo") == "primeiro"][:2]

def casca(sid, cls):
    r = sala_do_jogo(sid)
    return next((p["id"] for p in r.players.values() if p.get("class_id") == cls), None)


class WSFalso:
    """Só para a seção [0]: guarda o que o send_to entregou."""
    def __init__(self): self.sent = []
    async def send(self, data): self.sent.append(json.loads(data))


async def secao_helpers():
    print("\n[0] helpers de procuração")
    r = S.GameRoom("TESTE0")
    r.players = {
        "c1": {"id": "c1", "name": "Ana", "class_id": "warrior"},
        "x1": {"id": "x1", "name": "Pedro", "class_id": "mage", "controlador": "c1"},
        "x2": {"id": "x2", "name": "Luccas", "class_id": "rogue", "controlador": "c1"},
        "c2": {"id": "c2", "name": "Bia", "class_id": "cleric"},
    }
    r.host_pid = "c1"
    check("_conexao_de: extra → controlador", r._conexao_de("x1") == "c1")
    check("_conexao_de: principal → ele mesmo", r._conexao_de("c1") == "c1")
    check("_herois_da_conexao: extras primeiro, principal por último",
          r._herois_da_conexao("c1") == ["x1", "x2", "c1"], r._herois_da_conexao("c1"))
    check("_herois_da_conexao: jogador sem grupo", r._herois_da_conexao("c2") == ["c2"])
    check("_eh_anfitriao: extra do anfitrião conta como anfitrião", r._eh_anfitriao("x1"))
    check("_eh_anfitriao: outro jogador não", not r._eh_anfitriao("c2"))
    check("heroi_da_acao: `heroi` próprio é aceito", r.heroi_da_acao("c1", {"heroi": "x2"}) == "x2")
    check("heroi_da_acao: `heroi` de outro controlador é recusado",
          r.heroi_da_acao("c2", {"heroi": "x1"}) is None)
    check("heroi_da_acao: `heroi` inexistente é recusado",
          r.heroi_da_acao("c1", {"heroi": "id_999999"}) is None)
    check("heroi_da_acao: sem `heroi` fora da masmorra → a própria conexão",
          r.heroi_da_acao("c1", {}) == "c1")
    r.phase = "playing"
    r.current_pid = lambda: "x2"   # simula a vez do herói extra
    check("heroi_da_acao: sem `heroi`, na vez de um extra meu → o extra",
          r.heroi_da_acao("c1", {}) == "x2")
    check("heroi_da_acao: a vez de um extra alheio não vale para outra conexão",
          r.heroi_da_acao("c2", {}) == "c2")
    casca_nova = r._casca_extra("c1", "paladin", ["x"])
    check("_casca_extra: controlador, nome do herói e magias",
          casca_nova["controlador"] == "c1" and casca_nova["name"] == "Richard"
          and casca_nova["magias_conhecidas"] == ["x"] and casca_nova["class_id"] == "paladin")

    ws_ana = WSFalso()
    r.connections = {"c1": ws_ana}
    S.LANG_BY_PID["c1"] = "en"
    await r.send_to("x1", {"type": "error", "msg": S.T("erro.nao_e_o_seu_turno")})
    check("send_to(extra) chega na conexão do controlador", len(ws_ana.sent) == 1)
    check("…no idioma do controlador",
          ws_ana.sent and ws_ana.sent[0]["msg"] == txt("erro.nao_e_o_seu_turno", "en"),
          ws_ana.sent)
    S.LANG_BY_PID.pop("c1", None)


async def criar_solo(conta, nome_jogo, passos, play_mode="solo"):
    """Cria um jogo salvo, abre o lobby e roda `passos(caixa)` (lista de
    itens de roteiro) na MESMA conexão. Devolve (sid, ws)."""
    caixa = {}
    def criado():
        sg = next((d["savegame"] for d in caixa["ws"].msgs("savegame_created")), None)
        caixa["sid"] = sg and sg["id"]
        return {"type": "load_savegame", "id": caixa["sid"]}
    async def esperar_lobby():
        await esperar(lambda: caixa.get("sid") and sala_do_jogo(caixa["sid"]))
    roteiro = [login(conta),
               {"type": "create_savegame", "name": nome_jogo, "mode": "procedural",
                "play_mode": play_mode},
               lambda: asyncio.sleep(0.05), criado, esperar_lobby]
    caixa["ws"] = FakeWS(roteiro)
    caixa["ws"].roteiro.extend(passos(caixa))
    await S.handler(caixa["ws"])
    return caixa["sid"], caixa["ws"]

def pausa():
    return lambda: asyncio.sleep(0.03)


async def secao_lobby():
    print("\n[1] select_party monta o grupo no lobby")
    obs = {}
    def foto(rotulo):
        def f(caixa):
            r = sala_do_jogo(caixa["sid"])
            obs[rotulo] = {p["id"]: dict(p) for p in r.players.values()}
            obs[rotulo + "_lobby"] = caixa["ws"].msgs("lobby_state")[-1]
            obs["conexao"] = next(p["id"] for p in r.players.values() if not p.get("controlador"))
        return f
    sid, ws = await criar_solo("solo1", "Grupo", lambda c: [
        lambda: foto("antes")(c),
        {"type": "select_party", "classes": ["warrior", "mage", "rogue"]}, pausa(),
        lambda: foto("tres")(c),
        {"type": "select_party", "classes": ["warrior", "rogue"]}, pausa(),
        lambda: foto("dois")(c),
        {"type": "select_party", "classes": []}, pausa(),
        {"type": "select_party", "classes": ["dragao"]}, pausa(),
    ])
    check("lobby_state avisa que dá para montar grupo (grupo_solo)",
          obs["antes_lobby"].get("grupo_solo") is True, obs["antes_lobby"].get("grupo_solo"))
    tres = obs["tres"]
    extras = [p for p in tres.values() if p.get("controlador")]
    check("3 heróis no lobby, 2 extras", len(tres) == 3 and len(extras) == 2, list(tres.values()))
    check("extras controlados pela conexão",
          all(p["controlador"] == obs["conexao"] for p in extras))
    check("extras com nome do herói (Pedro, Luccas)",
          sorted(p["name"] for p in extras) == ["Luccas", "Pedro"])
    check("o lobby_state leva o `controlador`",
          sum(1 for p in obs["tres_lobby"]["players"] if p.get("controlador")) == 2)
    dois = obs["dois"]
    check("tirar o mago remove a casca dele",
          sorted(p.get("class_id") for p in dois.values()) == ["rogue", "warrior"])
    rogue_antes = next(q for q, p in tres.items() if p.get("class_id") == "rogue")
    check("o ladino continua com o mesmo pid", rogue_antes in dois)
    check("lista vazia é recusada", txt("erro.grupo_de_1_a_6_herois") in ws.erros(), ws.erros())
    check("classe inexistente sozinha também", ws.erros().count(txt("erro.grupo_de_1_a_6_herois")) == 2)
    check("a conexão do lobby caiu: os extras saíram junto",
          not sala_do_jogo(sid) or not any(p.get("controlador")
                                           for p in sala_do_jogo(sid).players.values()))
    limpar_salas()

    print("\n[1b] Multiplayer não monta grupo")
    _, ws_m = await criar_solo("multi", "Mesa", lambda c: [
        {"type": "select_party", "classes": ["warrior", "mage"]}, pausa()],
        play_mode="multiplayer")
    check("select_party recusado no Multiplayer",
          txt("erro.grupo_so_no_solo") in ws_m.erros(), ws_m.erros())
    limpar_salas()

    print("\n[1c] Solo com grupo é fechado para outra conta")
    caixa_dono = {}
    async def intruso_entra():
        await esperar(lambda: caixa_dono.get("pronto"))
        r = sala_do_jogo(caixa_dono["sid"])
        return {"type": "join_room", "name": "intruso", "code": r.code}
    async def dono_espera_intruso():
        caixa_dono["pronto"] = True
        await esperar(lambda: ws_intruso.msgs("error"), timeout=3)
    ws_intruso = FakeWS([login("intruso"), intruso_entra, pausa()])
    def passos_dono(c):
        caixa_dono.update(c)
        return [{"type": "select_party", "classes": ["warrior", "cleric"]}, pausa(),
                lambda: caixa_dono.update(sid=c["sid"]), dono_espera_intruso]
    await asyncio.gather(criar_solo("solo2", "Fechado", passos_dono), S.handler(ws_intruso))
    check("outra conta é recusada",
          txt("erro.jogo_solo_com_grupo_fechado") in ws_intruso.erros(), ws_intruso.erros())
    limpar_salas()


def esperar_fase(caixa, fase):
    async def f():
        await esperar(lambda: sala_do_jogo(caixa["sid"]).phase == fase)
        await asyncio.sleep(0.05)
    return f

def montar_e_iniciar(classes, depois=lambda c: []):
    """Passos: monta o grupo, escolhe magias de mago/clérigo e inicia."""
    def passos(c):
        p = [{"type": "select_party", "classes": classes}, pausa()]
        for cls in classes:
            if cls in ("mage", "cleric"):
                p.append(lambda cls=cls: {"type": "set_known_spells", "ids": duas_magias(cls),
                                          "heroi": casca(c["sid"], cls)})
                p.append(pausa())
        p += [{"type": "start_game"}, esperar_fase(c, "city")]
        return p + depois(c)
    return passos


async def secao_inicio():
    print("\n[2] início: vínculo, magias por herói, XP dividido")
    obs = {}
    def antes_das_magias(c):
        return [{"type": "select_party", "classes": ["warrior", "mage", "rogue"]}, pausa(),
                {"type": "start_game"}, pausa()]
    _, ws0 = await criar_solo("solo3", "SemMagia", antes_das_magias)
    check("iniciar sem as magias do mago é recusado",
          txt("erro.magos_e_clerigos_devem_escolher_2_magias") in ws0.erros(), ws0.erros())
    limpar_salas()

    def olhar(c):
        def f():
            r = sala_do_jogo(c["sid"])
            obs["players"] = {p["id"]: dict(p) for p in r.players.values()}
            obs["xp"] = r._calc_monster_xp({"cr": 1})
        return [f]
    sid, ws = await criar_solo("solo4", "Trio", montar_e_iniciar(["warrior", "mage", "rogue"], olhar))
    ps = obs["players"]
    mago = next(p for p in ps.values() if p.get("class_id") == "mage")
    principal = next(p for p in ps.values() if not p.get("controlador"))
    check("3 heróis na cidade", len(ps) == 3, list(ps))
    check("o mago (extra) tem as magias escolhidas para ele",
          set(duas_magias("mage")) <= set(mago.get("magias_conhecidas") or []),
          mago.get("magias_conhecidas"))
    check("os extras guardam o controlador após o start_game",
          sum(1 for p in ps.values() if p.get("controlador") == principal["id"]) == 2)
    check("city_state leva os 3 heróis", len(ws.msgs("city_state")[-1]["players"]) == 3)
    check("XP de monstro dividido por 3", obs["xp"][1] == 3, obs["xp"])
    sg = S.load_savegame(sid)
    m = sg["members"]["solo4"]
    check("jogo salvo: class_id é o principal", m.get("class_id") == "warrior", m)
    check("jogo salvo: class_ids guarda o grupo", m.get("class_ids") == ["warrior", "mage", "rogue"], m)
    check("jogo salvo: uma ficha por classe",
          all(c in sg.get("characters", {}) for c in ("warrior", "mage", "rogue")))
    check("jogo salvo: a ficha do mago tem as magias",
          set(duas_magias("mage")) <= set(sg["characters"]["mage"].get("magias_conhecidas") or []))
    limpar_salas()
    return sid


async def main():
    tmp = tempfile.mkdtemp()
    velha = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        for conta in ("solo1", "solo2", "solo3", "solo4", "solo5", "solo6", "intruso", "multi"):
            acc, e = await S.create_account(conta, SENHA)
            assert acc, e
        await secao_helpers()
        await secao_lobby()
        sid_trio = await secao_inicio()
    finally:
        limpar_salas()
        S.LOJA = velha
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 62); print("  SOLO COM GRUPO — servidor"); print("=" * 62)
    asyncio.run(main())
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)
