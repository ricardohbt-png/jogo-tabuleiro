"""Regressão do Ogro (ND 2) — variantes Clava (ofensivo) e Lança (defensivo).

Cobre: fichas/ataques, alcance da lança (2 reto / 1 diagonal), Golpe Brutal (+2,
finalizar), Força Descomunal (atordoa via Fortitude CD 10), Lento e Previsível
(-2 CA ao errar), Mente Bruta (-2 Vontade) e loot de comida (mix).

Rodar da raiz:  PYTHONUTF8=1 python tools/test_ogro.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

ok = fail = 0
def check(cond, label):
    global ok, fail
    if cond: ok += 1;  print(f"  ✅ {label}")
    else:    fail += 1; print(f"  ❌ {label}")

CLAVA = next(m for m in S.MONSTER_DEFS if m["type"] == "ogro_clava")
LANCA = next(m for m in S.MONSTER_DEFS if m["type"] == "ogro_lanca")

async def _noop(*a, **k): return None

def jogo(defm, player_pos, hit=True, save_fail=True):
    g = S.GameRoom("T")
    g.tiles = [[S.FLOOR]*S.MAP_W for _ in range(S.MAP_H)]
    g.rooms = []; g.door_rooms = {}; g.zonas_especiais = []; g.armadilhas = []
    g.smoke = {}; g.immune = {}; g.temp_def = {}; g.taunted = None; g.round_num = 1
    g.broadcast = _noop; g.gm_say = _noop; g.send_to = _noop
    chamadas = []
    async def _exec(m, atk, tobj):
        chamadas.append({"gb": m.get("_golpe_brutal_ativo"), "atk": atk["name"]})
        return hit
    g._exec_calls = chamadas
    g._execute_one_monster_attack = _exec
    g._testar_save = lambda alvo, t, dc, extra_mod=0: (not save_fail, 5, 0, 5)
    ogro = S.make_monster(defm, {"x":0,"y":0,"w":4,"h":4,"cx":1,"cy":1,"id":"r","role":"monster"})
    ogro["pos"] = [1, 1]
    g.monsters = {ogro["id"]: ogro}
    player = {"id":"p1","name":"H","pos":list(player_pos),"alive":True,"hp":40,"max_hp":40,"ac":15}
    g.players = {"p1": player}
    return g, ogro, player

def targets(g):
    return [{"kind":"player","obj":p} for p in g.players.values() if p["alive"]]

# ── 1) Fichas ────────────────────────────────────────────────────────────────
print("[1] Fichas Clava/Lança")
check(CLAVA["hp"]==32 and CLAVA["ac"]==12 and CLAVA["size"]==[2,2] and CLAVA["movement"]==5, "Clava: 32/CA12/2x2/Mov5")
check(LANCA["ac"]==14 and LANCA.get("reach_lanca") is True, "Lança: CA14 + alcance estendido")
check(CLAVA["attacks"][0]["damage"]=="1d12+4", "Clava 1d12+4")
check(LANCA["attacks"][0]["damage"]=="1d10+4", "Lança 1d10+4")
check(any(w.get("save")=="vontade" and w.get("bonus_flat")==-2 for w in CLAVA["weaknesses"]), "Mente Bruta: -2 Vontade")

# ── 2) Alcance da lança ──────────────────────────────────────────────────────
print("[2] Alcance da lança (2 reto / 1 diagonal)")
g, ogro, _ = jogo(LANCA, [4,1])
# footprint [1,1],[2,1],[1,2],[2,2]
check(g._lanca_no_alcance(ogro, [4,1]) is True,  "2 em linha reta (de [2,1] → [4,1])")
check(g._lanca_no_alcance(ogro, [3,3]) is True,  "1 na diagonal (de [2,2] → [3,3])")
check(g._lanca_no_alcance(ogro, [5,1]) is False, "3 reto = fora")
check(g._lanca_no_alcance(ogro, [4,4]) is False, "2 na diagonal = fora")
# parede no meio bloqueia o alcance 2
g.tiles[1][3] = S.WALL
check(g._lanca_no_alcance(ogro, [4,1]) is False, "parede no meio bloqueia o alcance 2")
# Clava usa adjacência simples
gc, oc, _ = jogo(CLAVA, [3,1])
check(gc._em_alcance_ogro(oc, [3,1]) is True,  "Clava: adjacente a [2,1] → alcance")
check(gc._em_alcance_ogro(oc, [4,1]) is False, "Clava: 2 de distância → fora")

# ── 3) Golpe Brutal: finaliza alvo enfraquecido (+2) ─────────────────────────
print("[3] Golpe Brutal (finalizar)")
g, ogro, p = jogo(CLAVA, [3,1], hit=True)
p["hp"] = 10                              # alvo enfraquecido (<=12)
asyncio.run(g._ai_ogro(ogro, targets(g)))
check(g._exec_calls and g._exec_calls[-1]["gb"] is True, "usou Golpe Brutal (+2) no alvo fraco")
check(ogro["ability_cooldowns"]["golpe_brutal"]==3, "recarga Golpe Brutal = 3")
check(g._golpe_brutal_bonus({"_golpe_brutal_ativo":True})==2, "bônus de dano do Golpe Brutal = +2")

# ── 4) Força Descomunal: atordoa quem falha em Fortitude ─────────────────────
print("[4] Força Descomunal (atordoar)")
g, ogro, p = jogo(CLAVA, [3,1], hit=True, save_fail=True)
p["hp"] = 40                              # alvo cheio → não usa Golpe Brutal
asyncio.run(g._ai_ogro(ogro, targets(g)))
check(ogro["ability_cooldowns"]["forca_descomunal"]==4, "recarga Força Descomunal = 4")
check(p.get("perde_turno") is True, "alvo falhou Fortitude → atordoado (perde turno)")
# Se passar no save, não atordoa
g2, ogro2, p2 = jogo(CLAVA, [3,1], hit=True, save_fail=False); p2["hp"]=40
asyncio.run(g2._ai_ogro(ogro2, targets(g2)))
check(not p2.get("perde_turno"), "passou no Fortitude → não atordoa")

# ── 5) Lento e Previsível: -2 CA ao errar ────────────────────────────────────
print("[5] Lento e Previsível")
g, ogro, p = jogo(CLAVA, [3,1], hit=False); p["hp"]=40
asyncio.run(g._ai_ogro(ogro, targets(g)))
check(ogro.get("lento_previsivel_ativo") is True, "errou → flag de -2 CA")
check(g._lento_previsivel_ca_pen(ogro)==2, "penalidade de -2 CA aplicada")
# Limpa no início do próprio turno (turno seguinte com acerto não re-seta a flag)
async def _hit(m, atk, tobj): return True
g._execute_one_monster_attack = _hit
asyncio.run(g._ai_ogro(ogro, targets(g)))
check(not ogro.get("lento_previsivel_ativo"), "flag limpa no início do turno seguinte")

# ── 6) Loot de comida (mix) ──────────────────────────────────────────────────
print("[6] Loot de comida (mix)")
check(CLAVA["loot_table"]["91-100"]=={"tipo":"comida"}, "loot 91-100 = comida")
g = S.GameRoom("T")
ids = set()
for _ in range(40):
    it = g._loot_comida()
    ids.add(it["id"]);
    if it.get("effect") in ("ration","wine"):
        assert it["item_slot"]=="bag"
check("racao" in ids or "garrafa_vinho" in ids, "pode dropar comida de fome/sede")
check(all(g._loot_comida().get("item_slot")=="bag" for _ in range(10)), "todo item de comida vai p/ a bag")

print(f"\n===== RESULTADO: {ok} passaram, {fail} falharam =====")
sys.exit(1 if fail else 0)
