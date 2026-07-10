"""Testes dos arremessáveis de ÁCIDO (Sub-projeto C).
Roda da raiz: python tools/test_arremessaveis_acido.py"""
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

def make_monster(r, mid, x, y, hp=40, ac=1):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True}
    r.monsters[mid] = m
    return m

# Força o d20 do arremesso a um valor fixo (para acerto/erro determinístico),
# deixando os dados de DANO (roll_dice) usarem o RNG real.
_REAL_RANDINT = random.randint
def _fixed_d20(value):
    def fake(a, b):
        return value if (a, b) == (1, 20) else _REAL_RANDINT(a, b)
    return fake

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo de ácido + loja")
    for iid in ("frasco_acido", "vidro_acido_grande"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=ataque_alvo", ARREMESSAVEIS.get(iid, {}).get("alvo") == "ataque_alvo")
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    check("frasco: 1d6", ARREMESSAVEIS["frasco_acido"]["dano"] == "1d6")
    check("frasco: residual", ARREMESSAVEIS["frasco_acido"]["residual"] is True)
    check("frasco: corrosao 1", ARREMESSAVEIS["frasco_acido"]["corrosao_ac"] == 1)
    check("grande: 2d6", ARREMESSAVEIS["vidro_acido_grande"]["dano"] == "2d6")
    check("grande: corrosao 2", ARREMESSAVEIS["vidro_acido_grande"]["corrosao_ac"] == 2)
    check("elemento acido", ARREMESSAVEIS["frasco_acido"]["elemento"] == "acido")

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
