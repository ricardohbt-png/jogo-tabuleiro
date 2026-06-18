"""Testes da Fase 4a: runtime de campanha.
Roda da raiz: python tools/test_campanha.py"""
import asyncio, sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, carregar_campanha, validar_campanha, listar_campanhas

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup_room():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop; r.broadcast_lobby = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys()); r.host_pid = "p1"
    return r

def test_validacao():
    print("\n[1] validar/listar campanha")
    defn = carregar_campanha("test_campanha.json")
    check("carrega o arquivo", defn is not None)
    ok, msg = validar_campanha(defn)
    check(f"campanha válida ({msg})", ok is True)
    check("aparece em listar_campanhas",
          any(c["file"] == "test_campanha.json" for c in listar_campanhas()))
    check("lista vazia recusa", validar_campanha({"schema_version": 1, "dungeons": []})[0] is False)
    check("fase inexistente recusa",
          validar_campanha({"schema_version": 1, "dungeons": ["nao_existe.json"]})[0] is False)
    check("path traversal recusado", carregar_campanha("../server.py") is None)

async def main():
    test_validacao()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
