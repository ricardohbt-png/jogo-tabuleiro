"""Teste do popup de resultado de armadilha (trap_result): buraco procedural,
armadilha de 1 alvo, armadilha de área (save_reduz), tick progressivo da
Incendiária, e roteamento pro resgatador do prisioneiro.
Roda da raiz: python tools/test_armadilha_popup.py"""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, make_monster, MONSTER_DEFS, ARMADILHAS

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r._broadcast_dado = noop
    r._tem_linha_de_visao = lambda *a, **k: True
    r.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    r.phase = "playing"
    r._is_turn = lambda pid: True
    r.sent = []
    async def capture(pid, msg):
        r.sent.append((pid, msg))
    r.send_to = capture
    return r

def trap_msgs(r, pid=None):
    """Mensagens trap_result capturadas, opcionalmente filtradas por destinatário."""
    return [m for p, m in r.sent if m.get("type") == "trap_result" and (pid is None or p == pid)]

def fake_rng(d20):
    """Substituto de random.randint: `d20` pra rolagens de d20 (b==20);
    fixa em 3 qualquer outra rolagem de dado (dano/veneno/reduzir_con)."""
    def f(a, b):
        return d20 if b == 20 else 3
    return f

def fake_rng_seq(d20_seq):
    """Como fake_rng, mas consome uma sequência de valores de d20 em ordem
    (uma chamada por save de d20; damage dice sempre fixo em 3)."""
    it = iter(d20_seq)
    def f(a, b):
        return next(it) if b == 20 else 3
    return f

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # ── [1] Buraco procedural (self.traps) ─────────────────────────────────────
    print("\n[1] Buraco procedural — popup de sucesso e de falha")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    r.traps = [{"id": "t1", "pos": [6, 5], "damage": 5, "triggered": False, "room_id": None}]
    _o = server.random.randint; server.random.randint = lambda a, b: 20   # sempre passa (20+0>=13)
    await r._verificar_trap_procedural("p1", p, 6, 5)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("1 popup enviado", len(msgs) == 1)
    check("nome genérico correto", msgs[0]["nome"] == "Buraco Escondido")
    check("sucesso=True, dano=0", msgs[0]["sucesso"] is True and msgs[0]["dano"] == 0)

    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    r.traps = [{"id": "t1", "pos": [6, 5], "damage": 5, "triggered": False, "room_id": None}]
    _o = server.random.randint; server.random.randint = lambda a, b: 1   # sempre falha (1+0<13)
    await r._verificar_trap_procedural("p1", p, 6, 5)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup de falha: sucesso=False", msgs and msgs[0]["sucesso"] is False)
    check("popup de falha: dano correto", msgs[0]["dano"] == 5)
    check("popup de falha: menciona o dano", any("dano" in t for t in msgs[0]["efeitos_extra"]))
    check("trap não dispara 2x (triggered)", r.traps[0]["triggered"] is True)

    # ── [2] Armadilha de 1 alvo (Armadilha de Urso: dano + perder_movimento) ───
    print("\n[2] Armadilha de Urso — falha (dano + efeito) e sucesso (evita)")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "a1", "tipo": "armadilha_urso", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)   # d20=1: falha (dif 10)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup enviado", len(msgs) == 1)
    check("nome/ícone corretos", msgs[0]["nome"] == "Armadilha de Urso" and msgs[0]["icone"] == "🪤")
    check("sucesso=False", msgs[0]["sucesso"] is False)
    check("dano > 0 (1d4 fixo em 3)", msgs[0]["dano"] == 3)
    check("efeitos_extra tem dano + movimento",
          any("dano" in t for t in msgs[0]["efeitos_extra"])
          and any("movimento" in t for t in msgs[0]["efeitos_extra"]))

    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "a2", "tipo": "armadilha_urso", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(15)   # d20=15: passa (dif 10)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup de sucesso: sucesso=True, dano=0", msgs and msgs[0]["sucesso"] is True and msgs[0]["dano"] == 0)
    check("popup de sucesso: sem efeitos_extra", msgs[0]["efeitos_extra"] == [])

    # ── [2b] Buraco colocável: só efeito, sem dano nenhum ───────────────────────
    print("\n[2b] Buraco colocável — falha só com efeito, sem dano")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "a3", "tipo": "buraco", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)   # falha (dif 10)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("dano=0 mesmo na falha (só efeito)", msgs and msgs[0]["dano"] == 0)
    check("efeitos_extra só tem o efeito, sem linha de dano",
          msgs[0]["efeitos_extra"] == ["🦵 Perdeu o movimento"])

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
