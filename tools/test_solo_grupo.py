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


async def main():
    tmp = tempfile.mkdtemp()
    velha = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        for conta in ("solo1", "solo2", "solo3", "solo4", "solo5", "solo6", "intruso", "multi"):
            acc, e = await S.create_account(conta, SENHA)
            assert acc, e
        await secao_helpers()
    finally:
        limpar_salas()
        S.LOJA = velha
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 62); print("  SOLO COM GRUPO — servidor"); print("=" * 62)
    asyncio.run(main())
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)
