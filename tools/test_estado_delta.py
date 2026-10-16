"""Deltas do game_state (monsters/players/chests/... por entidade; explored por casa nova):
o gameState.js REAL reconstrói, a cada passo, o mesmo estado do payload completo.
Roda da raiz: python tools/test_estado_delta.py"""
import sys, os, json, asyncio, subprocess, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(n, c):
    global PASS, FAIL
    if c: PASS += 1; print(f"  ✅ {n}")
    else: FAIL += 1; print(f"  ❌ {n}")

class Cliente:
    def __init__(self): self.msgs = []; self.crus = []
    async def send(self, data): self.msgs.append(json.loads(data)); self.crus.append(len(data))

def sala(n=2):
    r = S.GameRoom("DLT"); r.phase = "playing"
    d = json.load(open(os.path.join(RAIZ, "dungeons", "calabouco_morte.json"), encoding="utf-8"))
    r.load_authored_dungeon(d)
    for i in range(n):
        pid = f"d{i}"; p = S.make_player(pid, f"J{i}", ["warrior", "mage", "rogue"][i % 3], i)
        p["pos"] = [d["entrance"]["x"] + i, d["entrance"]["y"]]; r.players[pid] = p
        r.connections[pid] = Cliente()
    return r

def norm(estado):
    e = json.loads(json.dumps(estado))
    for k in ("diferidos", "deltas", "cooperative_markers"): e.pop(k, None)
    if "explored" in e: e["explored"] = sorted(map(tuple, e["explored"]))
    return e

def completo(r, pid):
    base = r._game_state_payload(); base["cooperative_markers"] = []
    return norm(json.loads(json.dumps(base, default=lambda o: S._t_render(o, S._lang_de(pid)))))

def reconstruir(msgs):
    """Passa as mensagens do servidor pelo gameState.js real; devolve a lista de (pediu, estado)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(msgs, f); nome = f.name
    try:
        out = subprocess.run(["node", os.path.join(RAIZ, "tools", "_estado_delta_node.js"), nome],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        assert out.returncode == 0, out.stderr[-500:]
        return json.loads(out.stdout)
    finally:
        os.unlink(nome)

async def main():
    r = sala(2)
    for y in range(0, 30):
        for x in range(0, 30): r.explored.add((x, y))
    mids = list(r.monsters)[:]
    passos = []   # (nome, lambda que muda o estado)
    def andar():     r.players["d0"]["pos"] = [r.players["d0"]["pos"][0] + 1, r.players["d0"]["pos"][1]]
    def ferir():     m = r.monsters[mids[0]]; m["hp"] = max(1, m["hp"] - 1)
    def explorar():  r.explored.update((x, 40) for x in range(10))
    def matar():     r.monsters[mids[1]]["hp"] = 0
    def reforco():
        novo = S.make_monster(mids and r.monsters[mids[2]]["type"], r.monsters[mids[2]]["pos"][0], r.monsters[mids[2]]["pos"][1]) \
            if False else None
    def encolher():  r.explored.discard((0, 0))
    seq = [("completo inicial", lambda: None), ("passo do d0", andar), ("monstro ferido", ferir),
           ("casas exploradas", explorar), ("monstro morto sai da lista", matar),
           ("nada muda", lambda: None), ("explored encolhe (envio completo)", encolher)]
    resultados = []
    for nome, mudar in seq:
        mudar(); await r.push_state()
        resultados.append((nome, completo(r, "d0"), completo(r, "d1")))
    for pid, idx in (("d0", 1), ("d1", 2)):
        cli = r.connections[pid]
        rec = reconstruir(cli.msgs)
        print(f"\n[{pid}] {len(cli.msgs)} mensagens")
        for (nome, _), esperado, got, cru in zip(seq, [x[idx] for x in resultados], rec, cli.crus):
            ok = (not got["pediu"]) and got["estado"] is not None and norm(got["estado"]) == esperado
            check(f"{nome}: reconstruído == completo ({cru/1024:.0f} KB)", ok)
    c0 = r.connections["d0"]
    print("\n[tamanhos]")
    check("passo do d0 pesa bem menos que o completo", c0.crus[1] < c0.crus[0] * 0.5)
    check("'nada muda' é minúsculo", c0.crus[5] < c0.crus[0] * 0.2)
    m1 = c0.msgs[1]
    check("monsters foi como delta (sem lista cheia)", "monsters" not in m1 and "monsters" in m1["deltas"])
    check("delta de monsters sem alteração leva 0 entradas", m1["deltas"]["monsters"]["mudou"] == [])
    check("players: só o d0 mudou", [e["id"] for e in m1["deltas"]["players"]["mudou"]] == ["d0"])
    check("explored vira só as casas novas", "explored" not in c0.msgs[3] and len(c0.msgs[3]["deltas"]["explored"]["add"]) == 10)
    check("explored que encolhe vai inteiro", "explored" in c0.msgs[6] and "explored" not in (c0.msgs[6].get("deltas") or {}))

    print("\n[conexão nova e idioma]")
    r2 = sala(2)
    await r2.push_state(); r2.players["d0"]["pos"][0] += 1; await r2.push_state()
    novo = Cliente(); r2.connections["d1"] = novo
    await r2.push_state()
    check("conexão nova recebe tudo", "deltas" not in novo.msgs[0] and not novo.msgs[0].get("diferidos"))
    S.LANG_BY_PID["d0"] = "en"
    await r2.push_state()
    m_en = r2.connections["d0"].msgs[-1]
    check("troca de idioma reenvia listas e campos diferidos inteiros",
          "monsters" in m_en and "players" in m_en and "materiais" in m_en and not m_en.get("diferidos"))
    check("explored (sem texto) segue como delta", "explored" in (m_en.get("deltas") or {}))
    S.LANG_BY_PID.pop("d0", None)

    print("\n[ids repetidos não viram delta]")
    r3 = sala(2); await r3.push_state()
    mon = list(r3.monsters.values())
    if len(mon) >= 4:
        ids_orig = [m["id"] for m in mon[:2]]
        mon[1]["id"] = mon[0]["id"]   # força repetição
        r3.players["d0"]["pos"][0] += 1
        await r3.push_state()
        check("monsters segue inteiro quando há id repetido", "monsters" in r3.connections["d0"].msgs[-1])

asyncio.run(main())
print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
