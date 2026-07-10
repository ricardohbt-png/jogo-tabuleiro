"""Testes dos arremessáveis de ÁREA (Sub-projeto B).
Roda da raiz: python tools/test_arremessaveis_area.py
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

def setup(w=11, h=11):
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
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True}
    r.monsters[mid] = m
    return m

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo de área + loja")
    for iid in ("bomba_incendiaria", "granada", "granada_superior", "bomba_fumaca"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=area", ARREMESSAVEIS.get(iid, {}).get("alvo") == "area")
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    check("incendiária: 2d6", ARREMESSAVEIS["bomba_incendiaria"]["dano"] == "2d6")
    check("incendiária: CD 12", ARREMESSAVEIS["bomba_incendiaria"]["save"]["cd"] == 12)
    check("incendiária: em_chamas", ARREMESSAVEIS["bomba_incendiaria"]["em_chamas"] is True)
    check("superior: 3d6", ARREMESSAVEIS["granada_superior"]["dano"] == "3d6")
    check("superior: CD 15", ARREMESSAVEIS["granada_superior"]["save"]["cd"] == 15)
    check("fumaça: zona escuridao", ARREMESSAVEIS["bomba_fumaca"]["zona"]["tipo"] == "escuridao")
    check("fumaça: sem dano", "dano" not in ARREMESSAVEIS["bomba_fumaca"])

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
