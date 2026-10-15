"""game_state: campos grandes/estáticos só viajam quando mudam (ESTADO_DIFERIVEL).
Simula o cliente (merge por `diferidos`) e exige estado reconstruído == payload completo.
Roda da raiz: python tools/test_estado_diferido.py"""
import sys, os, json, asyncio
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
    """WS falso + o mesmo merge do gameState.js (_completarDiferidos)."""
    def __init__(self): self.estado = None; self.msgs = []; self.pedidos = 0; self.crus = []; self.chaves = []
    async def send(self, data):
        m = json.loads(data); self.msgs.append(m); self.crus.append(len(data)); self.chaves.append(set(m))
        if m.get("type") != "game_state": return
        for k in m.get("diferidos") or []:
            if not self.estado or k not in self.estado: self.pedidos += 1; return
            m[k] = self.estado[k]
        self.estado = m

def sala(n=2):
    r = S.GameRoom("DIF"); r.phase = "playing"
    d = json.load(open(os.path.join(RAIZ, "dungeons", "calabouco_morte.json"), encoding="utf-8"))
    r.load_authored_dungeon(d)
    for i in range(n):
        pid = f"d{i}"; p = S.make_player(pid, f"J{i}", "warrior", i)
        p["pos"] = [d["entrance"]["x"] + i, d["entrance"]["y"]]; r.players[pid] = p
        r.connections[pid] = Cliente()
    return r

def completo(r, pid):
    """O que o cliente veria se nada fosse omitido (mesmo json do idioma)."""
    base = r._game_state_payload(); base["cooperative_markers"] = []
    return json.loads(json.dumps(base, default=lambda o: S._t_render(o, S._lang_de(pid))))

def igual(r, pid, extra_ignorar=("diferidos",)):
    a = {k: v for k, v in r.connections[pid].estado.items() if k not in extra_ignorar}
    b = {k: v for k, v in completo(r, pid).items() if k not in extra_ignorar}
    return a == b

async def main():
    r = sala(2)
    print("\n[1] Primeiro envio é completo")
    await r.push_state()
    c0, c1 = r.connections["d0"], r.connections["d1"]
    check("sem lista de omitidos", not c0.msgs[-1].get("diferidos"))
    check("traz materiais e tiles", "materiais" in c0.msgs[-1] and "tiles" in c0.msgs[-1])

    print("\n[2] Segundo envio omite o que não mudou")
    r.players["d0"]["pos"][0] += 1
    await r.push_state()
    m = c0.msgs[-1]
    omit = set(m.get("diferidos") or [])
    check("omite os campos estáticos", {"tiles", "materiais", "decorations", "rooms"} <= omit)
    check("não traz o conteúdo omitido", not (omit & c0.chaves[-1]))
    check("players continua indo", "players" in m and "monsters" in m)
    check("cliente reconstruído == payload completo (d0)", igual(r, "d0"))
    check("cliente reconstruído == payload completo (d1)", igual(r, "d1"))
    tam_cheio = c0.crus[0]; tam = c0.crus[-1]
    print(f"      (cheio {tam_cheio/1024:.0f} KB -> {tam/1024:.0f} KB)")
    check("redução relevante de tamanho", tam < tam_cheio * 0.75)

    print("\n[3] Mudança de conteúdo reenvia só aquele campo")
    r.decorations[0]["charges"] = 7 if r.decorations else None
    if not r.decorations: r.decorations.append({"id": "x"})
    await r.push_state()
    m = c0.msgs[-1]
    check("decorations voltou", "decorations" in m and "decorations" not in (m.get("diferidos") or []))
    check("materiais continua omitido", "materiais" in (m.get("diferidos") or []))
    check("reconstruído == completo", igual(r, "d0") and igual(r, "d1"))

    print("\n[4] Conexão nova recebe tudo (rejoin)")
    novo = Cliente(); r.connections["d1"] = novo
    await r.push_state()
    check("novo cliente sem omitidos", not novo.msgs[-1].get("diferidos"))
    check("o antigo continua recebendo omitidos", "materiais" in (c0.msgs[-1].get("diferidos") or []))
    check("novo cliente reconstrói certo", igual(r, "d1"))

    print("\n[5] Troca de idioma reenvia")
    S.LANG_BY_PID["d0"] = "en"
    await r.push_state()
    check("d0 em inglês recebe tudo de novo", not c0.msgs[-1].get("diferidos"))
    check("d1 (pt) segue omitindo", "materiais" in (novo.msgs[-1].get("diferidos") or []))
    S.LANG_BY_PID.pop("d0", None)

    print("\n[6] Quem saiu da masmorra volta recebendo tudo")
    r.players["d0"]["fora_masmorra"] = {"rodadas_restantes": 1}
    await r.push_state()
    n_antes = len(c0.msgs)
    check("d0 fora: sem game_state", len(c0.msgs) == n_antes)
    check("cache dele descartado", r.connections["d0"] not in r._diferidos_enviados)
    r.players["d0"]["fora_masmorra"] = None; r.players["d0"].pop("fora_masmorra")
    await r.push_state()
    check("ao voltar recebe completo", not c0.msgs[-1].get("diferidos"))

    print("\n[7] Cidade zera o cache; pedido de estado completo")
    await r.broadcast_city_state()
    check("cache limpo na cidade", not r._diferidos_enviados)
    r.phase = "playing"
    await r.push_state()
    check("depois da cidade, todos completos", all(not r.connections[p].msgs[-1].get("diferidos") for p in ("d0", "d1")))
    await r.push_state()
    ws = r.connections["d0"]; r._diferidos_enviados.pop(ws, None)   # o que o handler faz no pedido
    await r.push_state()
    check("após pedido, d0 completo e d1 ainda omite", not ws.msgs[-1].get("diferidos") and "materiais" in (r.connections["d1"].msgs[-1].get("diferidos") or []))

    print("\n[8] Preview do editor nunca omite")
    check("_game_state_payload não traz 'diferidos'", "diferidos" not in r._game_state_payload())

asyncio.run(main())
print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
