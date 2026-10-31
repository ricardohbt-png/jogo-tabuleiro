"""Objeto que abre passagem secreta (ou porta com condição) precisa ser clicável.

O cliente só deixa clicar numa decoração marcada (loot, armadilha, objeto-chave,
`interactive`...). A estante da Casa do Tomé abre o porão, mas não é objeto-chave
(senão acioná-la cumpriria o objetivo da carta) — e ficava impossível de acionar.
Roda da raiz: python -X utf8 tools/test_mecanismo_clicavel.py"""
import asyncio, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")


def casa_do_tome():
    r = S.GameRoom("TOME")
    with open(os.path.join(RAIZ, "dungeons", "elara_riacho_casa.json"), encoding="utf-8") as f:
        r.load_authored_dungeon(json.load(f))
    p = S.make_player("p0", "Ana", "warrior", 0)
    r.players["p0"] = p
    r.enviados = []
    async def send_to(pid, msg): r.enviados.append(msg)
    async def nada(*a, **k): pass
    r.send_to = send_to; r.broadcast = nada; r.push_state = nada; r.gm_say = nada
    return r, p


def decor(r, did):
    return next(d for d in r._serializar_decoracoes() if d["id"] == did)


print("\n[1] A estante do porão vai ao cliente como clicável")
r, p = casa_do_tome()
est = decor(r, "casa_estante")
check("estante não é objeto-chave (não cumpre o objetivo da carta)", est["key_objective"] is False)
check("estante marcada como interativa", est.get("interactive") is True)

print("\n[2] Objeto sem mecanismo continua sem a marca")
check("estante comum não fica interativa", not decor(r, "casa_estante_6").get("interactive"))

print("\n[3] Clicar e acionar abre o porão")
p["pos"] = [20, 4]
asyncio.run(r.handle_interagir_decor("p0", "casa_estante"))
check("o clique oferece o mecanismo", any(m.get("type") == "decor_mechanism" for m in r.enviados))
asyncio.run(r.handle_activate_decor_mechanism("p0", "casa_estante"))
check("passagem (22,6) virou chão", r.tiles[6][22] == S.FLOOR)
check("passagem (22,7) virou chão", r.tiles[7][22] == S.FLOOR)
check("objetivo da carta não foi cumprido pela estante", not r.key_chest_opened)

print("\n[4] Depois de aberta, a estante deixa de ser clicável")
check("sem marca após abrir", not decor(r, "casa_estante").get("interactive"))

print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
sys.exit(1 if FAIL else 0)
