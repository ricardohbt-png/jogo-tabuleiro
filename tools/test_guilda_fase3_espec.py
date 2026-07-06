"""Guilda dos Heróis — Fase 3: Técnicas Exclusivas (Mago/Clérigo).
Roda da raiz: python tools/test_guilda_fase3_espec.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup(phase="playing"):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r.round_num = 1
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r._tem_linha_de_visao = lambda *a, **k: True
    return r

def caster(cls="mage", tid_ex=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    p["magias_conhecidas"] = list(S.GRIMORIO_IMPLEMENTADAS)
    if tid_ex:
        p["guild_owned"]["tecnicas"] = [tid_ex]
        p["guild_equip"]["tecnica_exclusiva"] = tid_ex
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    print("\n[1] classe como lista — compra, catálogo, restrição")
    r = setup(phase="city")
    mago = caster("mage"); r.players["h"] = mago
    clerigo = caster("cleric"); r.players["c"] = clerigo
    guerreiro = caster("warrior"); r.players["w"] = guerreiro
    for pid_ in ("h", "c", "w"): r.players[pid_]["gold"] = 1000
    r._errs.clear()
    await r.handle_guild_buy("h", "tec_ex_aprimorar_magia")
    check("mago compra técnica exclusiva", "tec_ex_aprimorar_magia" in mago["guild_owned"]["tecnicas"])
    r._errs.clear()
    await r.handle_guild_buy("c", "tec_ex_aprimorar_magia")
    check("clérigo compra a mesma técnica", "tec_ex_aprimorar_magia" in clerigo["guild_owned"]["tecnicas"])
    r._errs.clear()
    await r.handle_guild_buy("w", "tec_ex_aprimorar_magia")
    check("guerreiro é recusado", "tec_ex_aprimorar_magia" not in guerreiro["guild_owned"]["tecnicas"])
    check("guerreiro recebe erro de classe", any("classe" in e.lower() for e in r._errs))
    ids_mage = [i["id"] for i in S.guild_items_for_class("mage")]
    ids_warr = [i["id"] for i in S.guild_items_for_class("warrior")]
    check("catálogo do mago inclui as 7 exclusivas",
          all(f"tec_ex_{n}" in ids_mage for n in
              ["aprimorar_magia", "estender_magia", "canalizacao_arcana", "empoderar_magia",
               "magia_geminada", "canalizacao_perfeita", "magia_acelerada"]))
    check("catálogo do guerreiro NÃO inclui nenhuma exclusiva",
          not any(i.startswith("tec_ex_") for i in ids_warr))

    print("\n[2] _testar_save: desvantagem rola 2d20 e usa o pior")
    r = setup()
    alvo = caster("mage")
    seq = iter([18, 5])
    orig_randint = S.random.randint
    S.random.randint = lambda a, b: next(seq)
    try:
        passou, d20, bonus, total = r._testar_save(alvo, "vontade", 10, desvantagem=True)
    finally:
        S.random.randint = orig_randint
    check("desvantagem usa o menor dos 2 rolls (5, não 18)", d20 == 5)

    seq2 = iter([18, 5])
    S.random.randint = lambda a, b: next(seq2)
    try:
        passou2, d20b, bonus2, total2 = r._testar_save(alvo, "vontade", 10)
    finally:
        S.random.randint = orig_randint
    check("sem desvantagem usa só a 1ª rolagem (18)", d20b == 18)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
