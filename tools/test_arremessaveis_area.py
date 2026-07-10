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

def _mk_save(passou):
    async def _s(alvo, tipo, cd, *a, **k):
        return (passou, 1, 0, 1)   # (passou, d20, bonus, total)
    return _s

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

    # ── [2] _aplicar_escuridao com centro explícito ────────────────────────────
    print("\n[2] _aplicar_escuridao(pos=...)")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    r.zonas_especiais = []
    await r._aplicar_escuridao(p, raio=1, duracao=2, pos=[5, 6])
    z = r.zonas_especiais[-1]
    check("zona criada no centro escolhido", z["cx"] == 5 and z["cy"] == 6)
    check("zona tipo escuridao", z["tipo"] == "escuridao")
    check("zona duracao 2", z["duracao"] == 2)
    # Sem pos → cai na casa do caster (compatibilidade com o Manto de Escuridão)
    await r._aplicar_escuridao(p, raio=1, duracao=1)
    check("sem pos usa a casa do caster", r.zonas_especiais[-1]["cx"] == 1)

    # ── [3] Dano de área a TODOS (fogo amigo), save = metade ────────────────────
    print("\n[3] Granada: dano de área + fogo amigo + save")
    r = setup(); random.seed(3)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    ally = make_player("p2", "A", "cleric", 0); ally["pos"] = [5, 5]; r.players["p2"] = ally
    m = make_monster(r, "m1", 5, 6, hp=40)   # adjacente ao centro (5,5)
    # saves sempre falham → dano cheio (patch determinístico)
    r._save_mostrado = _mk_save(False)
    hp_ally0, hp_m0 = ally["hp"], m["hp"]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 5, "ty": 5})
    check("monstro no raio sofreu dano", m["hp"] < hp_m0)
    check("ALIADO no raio sofreu dano (fogo amigo)", ally["hp"] < hp_ally0)
    check("item consumido", len(p["bag"]) == 0)
    check("ação principal gasta", p.get("action_done") is True)

    # save com sucesso → metade EXATA do dano rolado (monstro sem resistências)
    r = setup(); random.seed(3)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    m = make_monster(r, "m1", 5, 5, hp=40)
    r._save_mostrado = _mk_save(True)
    rolls = []
    async def cap_bcast(msg, *a, **k):
        if isinstance(msg, dict) and msg.get("die", "").startswith("d") and "Dano" in str(msg.get("label", "")):
            rolls.append(msg["value"])
    r.broadcast = cap_bcast
    hp0 = m["hp"]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 5, "ty": 5})
    dano_meio = hp0 - m["hp"]
    check("save reduz o dano à metade exata", len(rolls) == 1 and dano_meio == rolls[0] // 2,
          f"dano_meio={dano_meio} rolls={rolls}")

    # ── [4] Bomba Incendiária: quem sofre dano fica em chamas ───────────────────
    print("\n[4] Incendiária: em chamas nos atingidos")
    r = setup(); random.seed(4)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("bomba_incendiaria")]
    m = make_monster(r, "m1", 5, 5, hp=40)
    r._save_mostrado = _mk_save(False)
    await r.handle_throw_item("p1", {"item_id": "bomba_incendiaria", "tx": 5, "ty": 5})
    check("atingido ficou em chamas", m.get("em_chamas_rodadas", 0) > 0)
    check("chamas apagáveis por água", m.get("chamas_agua_apaga") is True)

    # ── [5] Granada Superior: 3d6 / CD 15 aplicados ─────────────────────────────
    print("\n[5] Granada Superior")
    r = setup(); random.seed(5)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("granada_superior")]
    m = make_monster(r, "m1", 5, 5, hp=60)
    saves = []
    async def cap_save(alvo, tipo, cd, *a, **k):
        saves.append(cd); return (False, 1, 0, 1)
    r._save_mostrado = cap_save
    await r.handle_throw_item("p1", {"item_id": "granada_superior", "tx": 5, "ty": 5})
    check("save usou CD 15", 15 in saves)
    check("dano de 3d6 aplicado (>0)", m["hp"] < 60)

    # ── [6] Bomba de Fumaça: zona de escuridão que expira em 2 rodadas ──────────
    print("\n[6] Fumaça")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [2, 2]; r.players["p1"] = p
    p["bag"] = [throwable("bomba_fumaca")]
    r.zonas_especiais = []
    await r.handle_throw_item("p1", {"item_id": "bomba_fumaca", "tx": 6, "ty": 6})
    z = [z for z in r.zonas_especiais if z.get("tipo") == "escuridao"]
    check("criou zona de escuridão no tile", len(z) == 1 and z[0]["cx"] == 6 and z[0]["cy"] == 6)
    check("fumaça consumida", len(p["bag"]) == 0)
    await r._processar_zonas_turno(); await r._processar_zonas_turno()
    check("zona expira após 2 rodadas",
          not any(z.get("tipo") == "escuridao" and z.get("ativa") for z in r.zonas_especiais))

    # ── [7] Alcance / LOS até o centro ──────────────────────────────────────────
    print("\n[7] Alcance/LOS")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [0, 0]; r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 9, "ty": 9})  # >4
    check("fora de alcance: item mantido", len(p["bag"]) == 1)
    check("fora de alcance: ação não gasta", not p.get("action_done"))

    # ── [8] Fogo amigo no PRÓPRIO arremessador ─────────────────────────────────
    print("\n[8] Auto fogo amigo")
    r = setup(); random.seed(8)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [5, 5]; p["hp"] = 999; p["max_hp"] = 999
    r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    r._save_mostrado = _mk_save(False)
    hp_self0 = p["hp"]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 5, "ty": 5})
    check("arremessador dentro da explosão sofre o próprio dano", p["hp"] < hp_self0)
    check("arremessador segue vivo (hp alto)", p["alive"] is True)

    # ── [9] Sombra de parede: alvo atrás de parede NÃO é atingido ───────────────
    # Chamada direta a _throw_item_area com raio 2 (os itens reais são raio 1, onde
    # todo tile atingido é adjacente ao centro e a sombra nunca ocorre).
    print("\n[9] Sombra de parede")
    r = setup(); random.seed(9)
    # Arremessador em (7,5): LOS horizontal ao centro (5,5) sem tocar a parede.
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [7, 5]; r.players["p1"] = p
    it = throwable("granada"); p["bag"] = [it]
    defn = dict(ARREMESSAVEIS["granada"]); defn["area_raio"] = 2
    # Centro (5,5), raio 2 → cobre y 3..7. Parede em (5,4) faz sombra sobre (5,3).
    r.tiles[4][5] = WALL
    m_hit = make_monster(r, "m_hit", 5, 6, hp=40)       # adjacente, iluminado
    m_shadow = make_monster(r, "m_shadow", 5, 3, hp=40)  # atrás da parede (5,4)
    r._save_mostrado = _mk_save(False)
    hp_hit0, hp_sh0 = m_hit["hp"], m_shadow["hp"]
    await r._throw_item_area(p, defn, it, 5, 5)
    check("alvo iluminado sofre dano", m_hit["hp"] < hp_hit0)
    check("alvo na sombra de parede NÃO sofre dano", m_shadow["hp"] == hp_sh0)

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
