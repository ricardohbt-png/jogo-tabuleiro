"""Testes dos arremessáveis TÁTICOS (Sub-projeto D: Cola e Rede).
Roda da raiz: python tools/test_arremessaveis_tatico.py"""
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

def make_monster(r, mid, x, y, hp=40, ac=1, movement=6):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True, "movement": movement}
    r.monsters[mid] = m
    return m

# Save determinístico: substitui _save_mostrado por um que sempre passa/falha.
def _mk_save(passou):
    async def _s(alvo, tipo, cd, *a, **k):
        return (passou, 1, 0, 1)   # (passou, d20, bonus, total)
    return _s

# d20 fixo no arremesso; dados de dano usam o RNG real.
_REAL_RANDINT = random.randint
def _fixed_d20(value):
    def fake(a, b):
        return value if (a, b) == (1, 20) else _REAL_RANDINT(a, b)
    return fake

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo tático + loja")
    for iid in ("cola_alquimica", "rede_arremesso"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=ataque_alvo", ARREMESSAVEIS.get(iid, {}).get("alvo") == "ataque_alvo")
        check(f"{iid} sem dano", "dano" not in ARREMESSAVEIS.get(iid, {}))
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    cola = ARREMESSAVEIS["cola_alquimica"]["controle"]
    check("cola: mov_reduzido", cola["tipo"] == "mov_reduzido")
    check("cola: resist Reflexos CD12", cola["resist_save"] == {"tipo": "reflexos", "cd": 12})
    check("cola: duracao 2", cola["duracao"] == 2)
    rede = ARREMESSAVEIS["rede_arremesso"]["controle"]
    check("rede: enredado", rede["tipo"] == "enredado")
    check("rede: escape Fortitude CD12", rede["escape_save"] == {"tipo": "fortitude", "cd": 12})

    # ── [2] _aplicar_controle_arremesso ────────────────────────────────────────
    print("\n[2] _aplicar_controle_arremesso")
    cola_ctrl = ARREMESSAVEIS["cola_alquimica"]["controle"]
    rede_ctrl = ARREMESSAVEIS["rede_arremesso"]["controle"]

    # cola: falha no Reflexos → corta movimento à metade
    r = setup(); r._save_mostrado = _mk_save(False)
    m = make_monster(r, "m1", 4, 4, movement=6)
    await r._aplicar_controle_arremesso(m, cola_ctrl)
    check("cola: movement 6→3", m["movement"] == 3)
    check("cola: mov_reduzido_rodadas=2", m.get("mov_reduzido_rodadas") == 2)
    check("cola: guardou original 6", m.get("mov_reduzido_orig") == 6)

    # cola: sucesso no Reflexos → sem efeito
    r._save_mostrado = _mk_save(True)
    m2 = make_monster(r, "m2", 5, 5, movement=6)
    await r._aplicar_controle_arremesso(m2, cola_ctrl)
    check("cola resist: movement intacto", m2["movement"] == 6 and not m2.get("mov_reduzido_rodadas"))

    # cola: reaplicar renova duração sem cortar de novo
    r._save_mostrado = _mk_save(False)
    m["mov_reduzido_rodadas"] = 1
    await r._aplicar_controle_arremesso(m, cola_ctrl)
    check("cola reaplicar: movement fica 3 (não corta de novo)", m["movement"] == 3)
    check("cola reaplicar: renova p/ 2", m["mov_reduzido_rodadas"] == 2)

    # rede: marca enredado + guarda o save de escape
    r = setup()
    m3 = make_monster(r, "m3", 6, 6)
    await r._aplicar_controle_arremesso(m3, rede_ctrl)
    check("rede: enredado", m3.get("enredado") is True)
    check("rede: enredado_save fortitude", m3.get("enredado_save") == "fortitude")
    check("rede: enredado_cd 12", m3.get("enredado_cd") == 12)

    # ── [3] mov_reduzido tica e expira (restaura movement) ─────────────────────
    print("\n[3] tick de mov_reduzido em _status_monstro_turno")
    r = setup()
    m = make_monster(r, "m1", 4, 4, movement=6)
    m["movement"] = 3; m["mov_reduzido_orig"] = 6; m["mov_reduzido_rodadas"] = 2
    res = await r._status_monstro_turno(m, [m])
    check("mov_reduzido não pula o turno", res != "pulou")
    check("tica p/ 1", m["mov_reduzido_rodadas"] == 1)
    check("ainda reduzido (3)", m["movement"] == 3)
    await r._status_monstro_turno(m, [m])
    check("expira: movement restaurado p/ 6", m["movement"] == 6)
    check("flag e backup limpos", m.get("mov_reduzido_rodadas", 0) == 0 and "mov_reduzido_orig" not in m)

    # ── [4] _processar_enredado_turno (escape) ─────────────────────────────────
    print("\n[4] _processar_enredado_turno")
    r = setup()
    m = make_monster(r, "m1", 4, 4)
    m["enredado"] = True; m["enredado_save"] = "fortitude"; m["enredado_cd"] = 12

    r._save_mostrado = _mk_save(False)   # falha → continua preso, turno gasto
    consumiu = await r._processar_enredado_turno(m)
    check("falha: turno consumido", consumiu is True)
    check("falha: continua preso", m.get("enredado") is True)

    r._save_mostrado = _mk_save(True)    # sucesso → solta, turno gasto
    consumiu = await r._processar_enredado_turno(m)
    check("sucesso: turno consumido", consumiu is True)
    check("sucesso: soltou", not m.get("enredado"))
    check("sucesso: limpou save/cd", "enredado_cd" not in m and "enredado_save" not in m)

    m2 = make_monster(r, "m2", 5, 5)     # não enredado → não consome
    check("não enredado → False", (await r._processar_enredado_turno(m2)) is False)

    # ── [5] Arremesso da Cola e da Rede (acerto) ───────────────────────────────
    print("\n[5] handle_throw_item (cola/rede) — acerto")
    S.random.randint = _fixed_d20(15)   # acerto não-crítico, não-nat1

    r = setup(); r._save_mostrado = _mk_save(False)   # falha no Reflexos → cola pega
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica")]
    m = make_monster(r, "m1", 4, 6, ac=1, movement=6)
    await r.handle_throw_item("p1", {"item_id": "cola_alquimica", "target_id": "m1"})
    check("cola: movement reduzido (6→3)", m["movement"] == 3)
    check("cola: mov_reduzido_rodadas=2", m.get("mov_reduzido_rodadas") == 2)
    check("cola: item consumido", len(p["bag"]) == 0)
    check("cola: sem dano (hp intacto)", m["hp"] == 40)

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("rede_arremesso")]
    m = make_monster(r, "m1", 4, 6, ac=1)
    await r.handle_throw_item("p1", {"item_id": "rede_arremesso", "target_id": "m1"})
    check("rede: enredado", m.get("enredado") is True)
    check("rede: item consumido", len(p["bag"]) == 0)

    # ── [6] Erro: item consumido, sem efeito ───────────────────────────────────
    print("\n[6] handle_throw_item (tático) — erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica")]
    m = make_monster(r, "m1", 4, 6, ac=99, movement=6)   # 15+5 < 99 → erro
    await r.handle_throw_item("p1", {"item_id": "cola_alquimica", "target_id": "m1"})
    check("erro: movement intacto", m["movement"] == 6)
    check("erro: sem mov_reduzido", not m.get("mov_reduzido_rodadas"))
    check("erro: item consumido", len(p["bag"]) == 0)
    S.random.randint = _REAL_RANDINT

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
