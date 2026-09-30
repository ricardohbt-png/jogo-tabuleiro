"""Catálogo da Metamorfose sob pedido (fora do game_state).

Roda da raiz:  python tools/test_metamorfose_catalogo.py

POR QUE ESTE TESTE EXISTE
  O `metamorfose_catalog` viajava dentro de TODO `game_state` — ~96 KB de um
  pacote de ~115 KB, a cada passo de cada herói, para todos os jogadores. Era a
  maior causa de travadas no multiplayer quando outro jogador andava. Agora o
  cliente pede o catálogo (`pedir_metamorfose_catalog`) ao abrir a janela de
  formas e só quem pediu recebe (`metamorfose_catalog`).

O QUE ELE COBRA
  • o game_state não carrega mais o catálogo (e ficou pequeno)
  • o pedido responde só a quem pediu, com as formas válidas
  • o handler despacha a mensagem nova
  • o cliente pede ao abrir a janela e lê do cache do GS, não do game_state
"""
import asyncio, json, os, re, sys
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


async def main():
    r = S.GameRoom("CATMETA")
    enviados = []
    async def noop(*a, **k): pass
    async def send_to(pid, msg): enviados.append((pid, msg))
    r.broadcast = noop
    r.send_to = send_to
    for pid, nome, cls in (("p1", "Pedro", "mage"), ("p2", "Gimli", "warrior")):
        r.players[pid] = S.make_player(pid, nome, cls, len(r.players))
    r.phase = "city"; r.host_pid = "p1"
    await r.enter_dungeon("p1")

    print("\n[1] game_state sem o catálogo")
    d = r._game_state_payload()
    check("chave metamorfose_catalog ausente", "metamorfose_catalog" not in d)
    tam = len(json.dumps(d, default=lambda o: S._t_render(o, "pt")))
    cat = len(json.dumps(r._metamorfose_catalog()))
    check(f"game_state ({tam // 1024} KB) menor que o catálogo sozinho ({cat // 1024} KB)",
          tam < cat, f"{tam} >= {cat}")

    print("\n[2] Pedido responde só a quem pediu")
    enviados.clear()
    await r.handle_pedir_metamorfose_catalog("p1")
    check("uma única mensagem", len(enviados) == 1, str(len(enviados)))
    pid, msg = enviados[0] if enviados else (None, {})
    check("destinatário é quem pediu", pid == "p1")
    check("tipo metamorfose_catalog", msg.get("type") == "metamorfose_catalog")
    formas = msg.get("formas") or []
    tipos = {f.get("type") for f in formas}
    check("traz as formas iniciais (pombo, rato, gato, ovelha)",
          {"pombo", "rato", "gato", "ovelha"} <= tipos, str(sorted(tipos))[:200])
    check("não traz chefes nem mortos-vivos",
          not any(f.get("subtipo") in {"morto_vivo", "construto", "licantropo"} for f in formas))
    check("cada forma traz type/name/cr", all("type" in f and "name" in f for f in formas))

    print("\n[3] Fiação: handler, cliente")
    srv = ler("server.py")
    check("handler despacha pedir_metamorfose_catalog",
          'elif t == "pedir_metamorfose_catalog"' in srv
          and "handle_pedir_metamorfose_catalog(pid)" in srv)
    gs = ler("src/gameState.js")
    check("gameState.js trata a resposta", "case 'metamorfose_catalog':" in gs)
    check("gameState.js expõe pedirMetamorfoseCatalog e o getter",
          "pedirMetamorfoseCatalog," in gs and "get metamorfoseCatalog()" in gs)
    gj = ler("game.js")
    check("game.js não lê mais o catálogo do game_state", "state.metamorfose_catalog" not in gj)
    abrir = re.search(r"function _abrirPickerMetamorfose\(\)\{.*?\n\}", gj, re.S)
    check("a janela pede o catálogo ao abrir",
          bool(abrir) and "GS.pedirMetamorfoseCatalog()" in abrir.group(0))
    check("a lista de formas redesenha quando o catálogo chega",
          "GS.on('metamorfoseCatalog'" in gj)


asyncio.run(main())
print(f"\n{'=' * 62}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 62}")
sys.exit(1 if FAIL else 0)
