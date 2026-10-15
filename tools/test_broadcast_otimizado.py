"""broadcast/push_state: JSON uma vez por idioma, envio em paralelo, marcadores só quando há.
Roda da raiz: python tools/test_broadcast_otimizado.py"""
import sys, os, json, asyncio, time
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0
def check(n, c):
    global PASS, FAIL
    if c: PASS += 1; print(f"  ✅ {n}")
    else: FAIL += 1; print(f"  ❌ {n}")

class WS:
    def __init__(self, atraso=0, falha=False):
        self.msgs = []; self.atraso = atraso; self.falha = falha
    async def send(self, data):
        if self.falha: raise RuntimeError("caiu")
        if self.atraso: await asyncio.sleep(self.atraso)
        self.msgs.append(data)

def sala(n=3):
    r = S.GameRoom("BRD"); r.phase = "playing"
    d = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dungeons", "Arena.json"), encoding="utf-8"))
    r.load_authored_dungeon(d)
    for i in range(n):
        r.connections[f"b{i}"] = WS()
    return r

async def main():
    print("\n[1] Um dumps por idioma")
    r = sala(4)
    chamadas = {"n": 0}
    orig = json.dumps
    def contador(*a, **k):
        chamadas["n"] += 1; return orig(*a, **k)
    S.json.dumps = contador
    try:
        await r.broadcast({"type": "x", "v": 1})
    finally:
        S.json.dumps = orig
    check("4 destinatários, mesmo idioma → 1 dumps", chamadas["n"] == 1)
    check("todos receberam o mesmo texto", len({w.msgs[0] for w in r.connections.values()}) == 1)

    print("\n[2] Identidade em personalize reaproveita; objeto novo personaliza")
    r = sala(3)
    msg = {"type": "x"}
    await r.broadcast(msg, personalize=lambda pid, m: m if pid != "b1" else {**m, "so": pid})
    got = {p: json.loads(w.msgs[0]) for p, w in r.connections.items()}
    check("b0 e b2 sem campo próprio", "so" not in got["b0"] and "so" not in got["b2"])
    check("b1 com campo próprio", got["b1"].get("so") == "b1")

    print("\n[3] Envio em paralelo: lento não atrasa o rápido")
    r = sala(0)
    r.connections["lento"] = WS(atraso=0.3); r.connections["rapido"] = WS()
    t = time.perf_counter(); marcas = {}
    orig_send = r.connections["rapido"].send
    async def rapido(data):
        await orig_send(data); marcas["rapido"] = time.perf_counter() - t
    r.connections["rapido"].send = rapido
    await r.broadcast({"type": "x"})
    check("rápido recebeu antes de o lento terminar", marcas["rapido"] < 0.1)
    check("lento também recebeu", len(r.connections["lento"].msgs) == 1)

    print("\n[4] Conexão que falha é removida; as outras recebem")
    r = sala(2); r.connections["ruim"] = WS(falha=True)
    await r.broadcast({"type": "x"})
    check("ruim removida", "ruim" not in r.connections)
    check("boas receberam", all(len(r.connections[p].msgs) == 1 for p in ("b0", "b1")))

    print("\n[5] game_state: sem marcadores não varre visão; com marcador, só quem vê")
    r = sala(2)
    for i, pid in enumerate(("b0", "b1")):
        p = S.make_player(pid, f"J{i}", "warrior", i)
        p["pos"] = [2 + i, 2]; r.players[pid] = p
    r.explored.update((x, y) for x in range(0, 6) for y in range(0, 6))
    chamou = {"n": 0}
    orig_v = r._cooperative_vision_tiles_for_pid
    def espia(pid):
        chamou["n"] += 1; return orig_v(pid)
    r._cooperative_vision_tiles_for_pid = espia
    await r.push_state()
    check("sem marcador: visão não calculada", chamou["n"] == 0)
    estados = [json.loads(w.msgs[-1]) for w in r.connections.values() if w.msgs]
    check("game_state leva cooperative_markers vazio", all(e.get("cooperative_markers") == [] for e in estados))
    r.cooperative_markers["b0"] = {"target_type": "tile", "pos": [2, 2]}
    await r.push_state()
    check("com marcador: visão calculada", chamou["n"] > 0)
    e0 = json.loads(r.connections["b0"].msgs[-1])
    check("o marcador chega ao cliente", any(m.get("owner_id") == "b0" for m in e0["cooperative_markers"]))

asyncio.run(main())
print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
