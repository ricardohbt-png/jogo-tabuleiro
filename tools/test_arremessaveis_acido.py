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

    # ── [2] _acido_corroer: reduz CA, cumulativo, com piso ─────────────────────
    print("\n[2] _acido_corroer")
    r = setup()
    m = make_monster(r, "m1", 4, 4, ac=15)
    await r._acido_corroer(m, 1)
    check("CA cai 1 (15→14)", m["ac"] == 14)
    check("ac_corroida acumula", m.get("ac_corroida") == 1)
    await r._acido_corroer(m, 2)
    check("CA cai +2 (14→12)", m["ac"] == 12)
    check("ac_corroida total 3", m.get("ac_corroida") == 3)
    # piso 5: uma CA baixa não desce abaixo de 5
    m2 = make_monster(r, "m2", 5, 5, ac=6)
    await r._acido_corroer(m2, 2)
    check("piso: CA 6 → 5 (não 4)", m2["ac"] == 5)
    await r._acido_corroer(m2, 2)
    check("piso: já em 5, permanece 5", m2["ac"] == 5)

    # ── [3] _processar_acido_residual_turno: aplica metade e limpa ─────────────
    print("\n[3] tick residual")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    m["acido_residual"] = 3
    await r._processar_acido_residual_turno()
    check("residual aplicou 3 de dano", m["hp"] == 37)
    check("residual limpo após o tick", m.get("acido_residual", 0) == 0)
    await r._processar_acido_residual_turno()
    check("sem residual → sem dano extra", m["hp"] == 37)
    # não tica em alvo morto
    m2 = make_monster(r, "m2", 5, 5, hp=0); m2["alive"] = False
    m2["acido_residual"] = 5
    await r._processar_acido_residual_turno()
    check("alvo morto: residual limpo sem dano", m2.get("acido_residual", 0) == 0 and m2["hp"] == 0)

    # ── [4] Acerto: dano + residual guardado + CA corroída ─────────────────────
    # d20 fixo em 15 (acerto não-crítico, não-nat1); atk_bonus alto garante o acerto.
    # CAs acima do piso 5 para que a corrosão registre.
    print("\n[4] handle_throw_item (ácido) — acerto")
    S.random.randint = _fixed_d20(15)
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("frasco_acido")]
    m = make_monster(r, "m1", 4, 6, hp=40, ac=15)   # 15+5 ≥ 15 → acerto
    await r.handle_throw_item("p1", {"item_id": "frasco_acido", "target_id": "m1"})
    check("dano de ácido aplicado", m["hp"] < 40)
    dano_inicial = 40 - m["hp"]
    check("residual guardado = dano//2", m.get("acido_residual", 0) == dano_inicial // 2)
    check("CA corroída -1 (15→14)", m["ac"] == 14)
    check("item consumido", len(p["bag"]) == 0)

    # Vidro Grande: -2 CA (15→13)
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("vidro_acido_grande")]
    m = make_monster(r, "m1", 4, 6, hp=60, ac=15)
    await r.handle_throw_item("p1", {"item_id": "vidro_acido_grande", "target_id": "m1"})
    check("Vidro Grande corrói -2 CA (15→13)", m["ac"] == 13)

    # ── [5] Erro: sem dano/residual/corrosão, item consumido ───────────────────
    # d20 fixo em 15, mas CA 99 → 15+5 < 99 → erro determinístico.
    print("\n[5] handle_throw_item (ácido) — erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("frasco_acido")]
    m = make_monster(r, "m1", 4, 6, hp=40, ac=99)
    await r.handle_throw_item("p1", {"item_id": "frasco_acido", "target_id": "m1"})
    check("erro: sem dano", m["hp"] == 40)
    check("erro: sem residual", m.get("acido_residual", 0) == 0)
    check("erro: CA intacta", m["ac"] == 99)
    check("erro: item consumido", len(p["bag"]) == 0)

    # residual usa max (não soma): residual grande pré-existente não regride
    S.random.randint = _fixed_d20(15)
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("frasco_acido")]
    m = make_monster(r, "m1", 4, 6, hp=40, ac=12)
    m["acido_residual"] = 100
    await r.handle_throw_item("p1", {"item_id": "frasco_acido", "target_id": "m1"})
    check("residual usa max (mantém 100)", m["acido_residual"] == 100)
    S.random.randint = _REAL_RANDINT   # restaura o RNG

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
