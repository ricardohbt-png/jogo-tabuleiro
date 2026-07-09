"""Testes dos arremessáveis de fogo (Sub-projeto A).
Roda da raiz: python tools/test_arremessaveis.py
Stuba a rede do GameRoom e monta um mapa de chão manualmente."""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, WALL, ARREMESSAVEIS, SHOP_MERCHANT

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=9, h=9):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda x, y: False
    r._errs = errs
    return r

def throwable(iid):
    return deepcopy(next(i for i in SHOP_MERCHANT if i["id"] == iid))

def make_monster(r, mid, x, y, hp=30, ac=1):
    m = {"id": mid, "name": "Alvo", "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True}
    r.monsters[mid] = m
    return m

async def main():
    random.seed(1)

    # ── [1] Catálogo e itens de loja ───────────────────────────────────────────
    print("\n[1] Catálogo ARREMESSAVEIS + loja")
    check("frasco_oleo no catálogo", "frasco_oleo" in ARREMESSAVEIS)
    check("fogo_grego no catálogo", "fogo_grego" in ARREMESSAVEIS)
    oleo = ARREMESSAVEIS["frasco_oleo"]
    check("óleo: alcance 4", oleo["alcance"] == 4)
    check("óleo: dano 1d6", oleo["dano"] == "1d6")
    check("óleo: água apaga", oleo["chamas_agua_apaga"] is True)
    grego = ARREMESSAVEIS["fogo_grego"]
    check("grego: dano 2d6", grego["dano"] == "2d6")
    check("grego: água NÃO apaga", grego["chamas_agua_apaga"] is False)
    check("óleo vendável na loja", any(i["id"] == "frasco_oleo" for i in SHOP_MERCHANT))
    check("loja: óleo effect=throwable",
          throwable("frasco_oleo")["effect"] == "throwable")

    # ── [2] Status em chamas: aplicar e refresh (max, não soma) ─────────────────
    print("\n[2] _aplicar_em_chamas")
    r = setup()
    m = make_monster(r, "m1", 4, 4)
    r._aplicar_em_chamas(m, 3, True)
    check("aplicou 3 rodadas", m.get("em_chamas_rodadas") == 3)
    check("gravou flag de água", m.get("chamas_agua_apaga") is True)
    r._aplicar_em_chamas(m, 2, True)   # menor → não reduz
    check("refresh usa o MAIOR (não reduz p/ 2)", m["em_chamas_rodadas"] == 3)
    r._aplicar_em_chamas(m, 5, False)  # maior → sobe e troca a flag
    check("refresh sobe p/ 5", m["em_chamas_rodadas"] == 5)
    check("flag de água atualizada p/ False", m["chamas_agua_apaga"] is False)

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
