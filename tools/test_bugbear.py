"""Regressão do Bugbear — Bicho-Papão das Sombras (ND 2) e da Vela da Escuridão.

Cobre os 3 lotes da feature:
  1. Ficha + 3 ataques + fraqueza fogo/sagrado ×2 + pergaminho da escuridão + loot.
  2. Habilidades de escuridão (Manto, Desaparecer/oculto, Caçador das Trevas,
     Ataque das Sombras, fraqueza de Luz).
  3. Vela da Escuridão (consumível: oculto, furtivo do ladino, vantagem, anti-stack).

Rodar da raiz:  PYTHONUTF8=1 python tools/test_bugbear.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import server as S

ok = fail = 0
def check(cond, label):
    global ok, fail
    if cond:
        ok += 1;  print(f"  ✅ {label}")
    else:
        fail += 1; print(f"  ❌ {label}")

DEF = next(m for m in S.MONSTER_DEFS if m["type"] == "bugbear_sombras")

async def _noop(*a, **k): return None

def novo_jogo(player_pos, stub_attacks=False):
    g = S.GameRoom("T")
    g.tiles = [[S.FLOOR]*S.MAP_W for _ in range(S.MAP_H)]
    g.rooms = []; g.door_rooms = {}
    g.zonas_especiais = []; g.armadilhas = []
    g.smoke = {}; g.immune = {}; g.temp_def = {}; g.taunted = None
    g.round_num = 1
    g.broadcast = _noop; g.gm_say = _noop; g.send_to = _noop
    if stub_attacks:
        g._monster_execute_attacks = _noop
        g._execute_one_monster_attack = _noop
    bug = S.make_monster(DEF, {"x":0,"y":0,"w":3,"h":3,"cx":1,"cy":1,"id":"r","role":"monster"})
    bug["pos"] = [1, 1]
    g.monsters = {bug["id"]: bug}
    player = {"id":"p1","name":"Herói","pos":list(player_pos),"alive":True,
              "hp":50,"max_hp":50,"ac":15,"visao_escuro":False}
    g.players = {"p1": player}
    return g, bug, player

def targets_de(g):
    return [{"kind":"player","obj":p} for p in g.players.values() if p["alive"]]

# ── LOTE 1: ficha / ataques / fraquezas / loot ───────────────────────────────
print("[1] Ficha, ataques, fraquezas e loot")
check(DEF["hp"]==22 and DEF["ac"]==14 and DEF["movement"]==7, "stats base (22/14/7)")
check(sum(a["num_attacks"] for a in DEF["attacks"])==3, "3 ataques/turno (2 garras + 1 mordida)")
g, bug, _ = novo_jogo([20,20])
check(g._apply_damage_types(10,[S.DMG_FIRE],bug)==20, "fraqueza fogo ×2")
check(g._apply_damage_types(10,[S.DMG_HOLY],bug)==20, "fraqueza sagrado ×2")
check(g._apply_damage_types(10,[S.DMG_PHYSICAL],bug)==10, "físico não é dobrado")
check(bug.get("ability_uses",{}).get("manto_escuridao")==1, "Manto 1x/combate preparado")
sc = S.gerar_pergaminho(magia_id="manto_escuridao")
check(sc and sc["id"]=="pergaminho_manto_escuridao", "pergaminho da escuridão gera")
cov = set()
for rng in DEF["loot_table"]:
    a,b = rng.split("-");  cov |= set(range(int(a), int(b)+1))
check(cov==set(range(1,101)), "loot table cobre 1-100 sem buracos")

# ── LOTE 2: habilidades de escuridão ─────────────────────────────────────────
print("[2] Habilidades de escuridão")
g, bug, player = novo_jogo([6,1], stub_attacks=True)
asyncio.run(g._ai_bugbear_sombras(bug, targets_de(g)))
check(bug["ability_uses"]["manto_escuridao"]==0, "Manto gasto no engajamento")
zona = next((z for z in g.zonas_especiais if z["tipo"]=="escuridao" and z["ativa"]), None)
check(zona is not None, "zona de escuridão criada")
check(DEF.get("level")==3, "bugbear é conjurador nível 3")
check(zona and zona["raio"]==S.GRIMORIO["manto_escuridao"]["area_raio"], "Manto usa o raio da magia (GRIMORIO)")
check(bug.get("oculto_sombras") is True, "Desaparecer → oculto")
check(bug["ability_cooldowns"]["desaparecer_nas_sombras"]==5, "cooldown Desaparecer = 5")
asyncio.run(g._ai_bugbear_sombras(bug, targets_de(g)))
check(not bug.get("oculto_sombras"), "oculto expira no próprio turno")
check(bug["ability_cooldowns"]["desaparecer_nas_sombras"]==4, "cooldown 5→4")

g2, b2, p2 = novo_jogo([20,20], stub_attacks=True)
b2["pos"]=[5,5]
g2.zonas_especiais.append({"id":"z","tipo":"escuridao","cx":5,"cy":5,"raio":3,"duracao":3,"ativa":True})
check(g2._cacador_trevas_ca_bonus(b2)==2, "Caçador das Trevas: +2 CA na escuridão")
check(g2._sombras_atk_bonus(b2,p2)==2, "Ataque das Sombras: +2 acerto")
check(1 <= g2._sombras_dano_bonus(b2,p2) <= 6, "Ataque das Sombras: +1d6 dano")
b2["pos"]=[25,25]
check(g2._cacador_trevas_ca_bonus(b2)==0, "sem +CA fora da escuridão")
check(g2._ataque_das_sombras_ativo(b2,p2) is False, "sombras inativo fora da escuridão")
# Gatilho: alvo cego no escuro (bugbear fora)
g5,b5,p5 = novo_jogo([2,2], stub_attacks=True)
g5.zonas_especiais.append({"id":"z2","tipo":"escuridao","cx":2,"cy":2,"raio":2,"duracao":3,"ativa":True})
b5["pos"]=[25,25]
check(g5._ataque_das_sombras_ativo(b5,p5) is True, "gatilho: alvo na escuridão sem darkvision")
p5["visao_escuro"]=True
check(g5._ataque_das_sombras_ativo(b5,p5) is False, "alvo com darkvision não ativa")
# Fraqueza de Luz
g6,b6,_ = novo_jogo([6,6], stub_attacks=True)
check(g6._luz_atk_pen(b6)==0, "fraqueza de Luz dormente sem fonte de luz")
g6.zonas_especiais.append({"id":"luz","tipo":"luz","cx":b6["pos"][0],"cy":b6["pos"][1],
                           "raio":2,"duracao":3,"ativa":True})
check(g6._luz_atk_pen(b6)==-2, "fraqueza de Luz: -2 ataque sob luz direta")

# ── LOTE 3: Vela da Escuridão ────────────────────────────────────────────────
print("[3] Vela da Escuridão")
vela = next((i for i in S.SHOP_MERCHANT if i["id"]=="vela_escuridao"), None)
check(vela and vela["effect"]=="veil_shadow", "Vela vendida no mercador")
check(vela and vela["price"]==50, "Vela custa 50 moedas")
check(DEF["loot_table"]["99-100"]=={"tipo":"item","id":"vela_escuridao"}, "drop 99-100 = Vela")
check("veil_shadow" in S.GameRoom.BONUS_ACTION_EFFECTS, "Vela é ação bônus")

def jogo_item(classe):
    g = S.GameRoom("T"); g.phase="playing"; g.player_order=["p1"]; g.turn_index=0
    g.broadcast=_noop; g.gm_say=_noop; g.send_to=_noop
    g._consumir_recursos = lambda *a, **k: None
    p = {"id":"p1","name":"H","class_id":classe,"alive":True,"pos":[5,5],
         "fome":10,"sede":10,"bag":[dict(vela)],"bonus_action_used":False}
    g.players={"p1":p}; g.monsters={}
    return g, p

g, p = jogo_item("rogue")
asyncio.run(g.handle_use_item("p1","vela_escuridao"))
check(p.get("oculto_vela") is True, "acende a vela → oculto")
check(p["bonus_action_used"] is True and all(i["id"]!="vela_escuridao" for i in p["bag"]), "gasta ação bônus + consome a vela")
check(g._verificar_ataque_furtivo(p, {"id":"m","name":"x","pos":[6,5]}) is True, "Ladino oculto → furtivo automático")
try: asyncio.run(g.handle_end_turn("p1"))
except Exception: pass
check(not p.get("oculto_vela"), "oculto expira no fim do turno")

g3, p3 = jogo_item("rogue"); p3["invisivel_sombras"]=True
asyncio.run(g3.handle_use_item("p1","vela_escuridao"))
check(p3["bonus_action_used"] is False and any(i["id"]=="vela_escuridao" for i in p3["bag"]),
      "anti-stack: bloqueia sem gastar ação nem a vela")

print(f"\n===== RESULTADO: {ok} passaram, {fail} falharam =====")
sys.exit(1 if fail else 0)
