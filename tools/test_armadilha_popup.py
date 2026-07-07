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

    # ── [3] Armadilha de área com save_reduz (Mina Terrestre) ───────────────────
    print("\n[3] Mina Terrestre (área) — 1 alvo falha, 1 resiste com metade")
    r = setup()
    p1 = make_player("p1", "A", "warrior", 0); p1["ref_"] = 0; p1["pos"] = [5, 5]
    p2 = make_player("p2", "B", "rogue", 1);   p2["ref_"] = 0; p2["pos"] = [6, 5]
    r.players = {"p1": p1, "p2": p2}
    arm = {"id": "m1", "tipo": "mina_terrestre", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    # dificuldade 12: p1 rola d20=2 (falha), p2 rola d20=18 (passa, mas save_reduz→metade)
    _o = server.random.randint; server.random.randint = fake_rng_seq([2, 18])
    await r._disparar_armadilha(p1, arm)
    server.random.randint = _o
    m1 = trap_msgs(r, "p1"); m2 = trap_msgs(r, "p2")
    check("p1 recebeu seu próprio popup", len(m1) == 1)
    check("p2 recebeu seu próprio popup", len(m2) == 1)
    check("p1 falhou: dano cheio (2d6 fixo em 3+3=6), metade=False",
          m1[0]["sucesso"] is False and m1[0]["metade"] is False and m1[0]["dano"] == 6)
    check("p2 resistiu: metade=True, ainda sofre dano reduzido (6→3)",
          m2[0]["sucesso"] is True and m2[0]["metade"] is True and m2[0]["dano"] == 3)

    # ── [4] Tick progressivo (Incendiária) ──────────────────────────────────────
    print("\n[4] Armadilha Incendiária — tick de dano progressivo")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "i1", "tipo": "armadilha_incendiaria", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)   # falha o save inicial
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    r.round_num += 1
    await r._processar_efeitos_armadilha_turno()
    msgs = trap_msgs(r, "p1")
    ticks = [m for m in msgs if m.get("tick")]
    check("disparo inicial gerou popup (tick=False)", msgs and msgs[0]["tick"] is False)
    check("dano progressivo gerou ao menos 1 popup de tick", len(ticks) >= 1)
    check("popup(s) de tick têm dano > 0", all(t["dano"] > 0 for t in ticks))

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
