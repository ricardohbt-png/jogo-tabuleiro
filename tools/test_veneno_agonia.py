"""Testes do veneno Agonia Sufocante (Sub-projeto E).
Roda da raiz: python tools/test_veneno_agonia.py"""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, VENENOS, SHOP_MERCHANT

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=9, h=9):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    async def cap_send(pid, msg, *a, **k): pass
    r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    return r

def make_monster(r, mid, x, y, hp=40):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": 12, "alive": True, "tier": 1}
    r.monsters[mid] = m
    return m

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo do veneno + loja")
    check("veneno no catálogo", "veneno_agonia_sufocante" in VENENOS)
    v = VENENOS.get("veneno_agonia_sufocante", {})
    check("operacao dano", v.get("operacao") == "dano")
    check("dano 1d4", v.get("dano") == "1d4")
    check("duracao 1d4", v.get("duracao") == "1d4")
    check("Fortitude CD 14", v.get("save") == "fortitude" and v.get("dificuldade") == 14)
    check("save por rodada", v.get("save_neutraliza_por_rodada") is True)
    shop = next((i for i in SHOP_MERCHANT if i["id"] == "veneno_agonia_sufocante"), None)
    check("vendável (coat_poison)", shop is not None and shop["effect"] == "coat_poison")
    check("aponta pro veneno", shop and shop.get("veneno_id") == "veneno_agonia_sufocante")

    # ── [2] Aplicação registra efeito de dano (sem save de aplicação) ──────────
    print("\n[2] _aplicar_veneno (dano)")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    await r._aplicar_veneno(m, "veneno_agonia_sufocante")
    efs = [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"]
    check("efeito de dano registrado", len(efs) == 1)
    check("dano 1d4", efs and efs[0]["dano"] == "1d4")
    check("duracao entre 1 e 4", efs and 1 <= efs[0]["duracao"] <= 4)
    check("save por rodada gravado", efs and efs[0]["save_neutraliza_por_rodada"] is True)

    # morto-vivo é imune (não registra efeito)
    mu = make_monster(r, "m2", 5, 5, hp=30); mu["undead"] = True
    await r._aplicar_veneno(mu, "veneno_agonia_sufocante")
    check("morto-vivo imune (sem efeito)", not mu.get("efeitos_veneno"))

    # ── [3] Tick — falha no save: sofre 1d4 e continua ─────────────────────────
    print("\n[3] tick — falha")
    def _efeito_dano(dur=3):
        return {"nome": "Agonia Sufocante", "operacao": "dano", "dano": "1d4",
                "duracao": dur, "save": "fortitude", "dificuldade": 14,
                "save_neutraliza_por_rodada": True}
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    m["efeitos_veneno"] = [_efeito_dano(3)]
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)   # falha
    hp0 = m["hp"]
    await r._processar_venenos_turno(m)
    check("falha: sofreu 1..4 de dano", 1 <= (hp0 - m["hp"]) <= 4)
    ef = [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"]
    check("falha: efeito continua", len(ef) == 1)
    check("falha: duracao decrementou p/ 2", ef and ef[0]["duracao"] == 2)

    # ── [4] Tick — sucesso no save: neutraliza sem dano ────────────────────────
    print("\n[4] tick — sucesso")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    m["efeitos_veneno"] = [_efeito_dano(3)]
    r._testar_save = lambda *a, **k: (True, 20, 0, 20)   # sucesso
    hp0 = m["hp"]
    await r._processar_venenos_turno(m)
    check("sucesso: sem dano", m["hp"] == hp0)
    check("sucesso: efeito removido", not [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"])

    # ── [5] Duração: expira em `duracao` rodadas falhando sempre ───────────────
    print("\n[5] duração expira")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=100)
    m["efeitos_veneno"] = [_efeito_dano(2)]
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)   # falha sempre
    await r._processar_venenos_turno(m)   # duracao 2→1
    await r._processar_venenos_turno(m)   # duracao 1→0 (expira)
    check("expira após `duracao` rodadas", not [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"])

    # ── [6] Regressão: veneno de atributo (reduzir) ainda funciona ─────────────
    print("\n[6] regressão: veneno de atributo")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); r.players["p1"] = p
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)   # falha no save → aplica
    str0 = p.get("str_", 10)
    await r._aplicar_veneno(p, "veneno_aranha_sombria")   # operacao 'reduzir' (forca)
    check("aranha ainda reduz Força", p.get("str_", 10) < str0)

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
