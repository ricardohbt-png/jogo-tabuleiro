"""Teste de largar/pegar itens no chão — Sub-projeto C.
Roda da raiz: python tools/test_ground_items.py
Stuba a rede do GameRoom e monta um mapa de chão manualmente."""
import asyncio, sys, os
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, WALL, WEAPONS, SHOP_ARMORS

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=7, h=7):
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
    # mapa: tudo chão
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda x, y: False
    r._errs = errs
    return r

def armor_item(iid):
    return deepcopy(next(a for a in SHOP_ARMORS if a["id"] == iid))

async def main():
    # ── [1] _free_drop_tile_near acha casa livre / respeita ocupação ────────────
    print("\n[1] _free_drop_tile_near")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    tile = r._free_drop_tile_near([3, 3])
    check("achou uma casa adjacente livre", tile is not None and max(abs(tile[0]-3), abs(tile[1]-3)) == 1)
    check("ground_items inicia vazio", r.ground_items == {})
    # cerca o jogador de paredes → sem casa livre
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                r.tiles[3+dy][3+dx] = WALL
    check("sem casa livre → None", r._free_drop_tile_near([3, 3]) is None)

    # ── [2] Largar da BOLSA ─────────────────────────────────────────────────────
    print("\n[2] Largar item da bolsa")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    p["bag"] = [armor_item("leather")]
    await r.handle_drop_item("p1", "bag", 0, None)
    check("item saiu da bolsa", len(p["bag"]) == 0)
    check("item apareceu no chão", len(r.ground_items) == 1)
    gi = list(r.ground_items.values())[0]
    check("item no chão é a leather", gi["item"]["id"] == "leather")
    check("casa do item é adjacente ao jogador", max(abs(gi["pos"][0]-3), abs(gi["pos"][1]-3)) == 1)

    # ── [3] Largar de um SLOT EQUIPADO (arma) → desequipa ───────────────────────
    print("\n[3] Largar arma equipada → desequipa e cai no chão")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    arma0 = p["gear"]["weapon"]["id"]
    await r.handle_drop_item("p1", "gear", None, "weapon")
    check("slot de arma ficou vazio", p["gear"].get("weapon") is None)
    check("p['weapon'] voltou a desarmado", p["weapon"]["id"] == "unarmed")
    check("arma foi para o chão", any(g["item"]["id"] == arma0 for g in r.ground_items.values()))

    # ── [4] Sem casa livre → recusa, item permanece ─────────────────────────────
    print("\n[4] Sem casa adjacente livre → recusa")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    p["bag"] = [armor_item("leather")]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy: r.tiles[3+dy][3+dx] = WALL
    await r.handle_drop_item("p1", "bag", 0, None)
    check("item permanece na bolsa", len(p["bag"]) == 1)
    check("nada no chão", len(r.ground_items) == 0)
    check("erro enviado", any("espaço" in e.lower() for e in r._errs))

    # ── [5] Pegar por OUTRO jogador adjacente → vai pro inventário ──────────────
    print("\n[5] Pegar item por outro jogador adjacente")
    r = setup()
    p1 = make_player("p1", "V", "warrior", 0); p1["pos"] = [3, 3]; r.players["p1"] = p1
    p2 = make_player("p2", "L", "rogue", 1);   p2["pos"] = [5, 5]; r.players["p2"] = p2
    gid = "g1"; r.ground_items[gid] = {"id": gid, "item": armor_item("leather"), "pos": [5, 4]}
    await r.handle_pickup_item("p2", gid)   # p2 em [5,5], item em [5,4] → adjacente
    check("item saiu do chão", gid not in r.ground_items)
    check("item entrou na bolsa do p2", any((it or {}).get("id") == "leather" for it in p2["bag"]))

    # ── [6] Pegar LONGE → erro, item permanece ─────────────────────────────────
    print("\n[6] Pegar longe → erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    gid = "g1"; r.ground_items[gid] = {"id": gid, "item": armor_item("leather"), "pos": [5, 5]}
    await r.handle_pickup_item("p1", gid)
    check("item permanece no chão", gid in r.ground_items)
    check("erro de longe", any("longe" in e.lower() for e in r._errs))

    # ── [7] Bolsa cheia + slot ocupado → recusa (fica no chão) ──────────────────
    print("\n[7] Bolsa cheia + slot ocupado → recusa")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    p["bag"] = [armor_item("leather") for _ in range(6)]   # bolsa cheia
    p["gear"]["armor"] = armor_item("leather")             # slot de armadura ocupado
    gid = "g1"; r.ground_items[gid] = {"id": gid, "item": armor_item("plate"), "pos": [3, 4]}
    await r.handle_pickup_item("p1", gid)
    check("item permanece no chão (recusado)", gid in r.ground_items)
    check("erro de cheio", any("cheio" in e.lower() for e in r._errs))

    # ── [8] Persistência: some ao gerar masmorra nova, fica ao voltar da cidade ──
    print("\n[8] Persistência dos itens no chão")
    r2 = GameRoom("TEST2")
    async def noop(*a, **k): pass
    r2.gm_say = noop; r2.broadcast = noop; r2.push_state = noop
    r2.send_to = noop; r2.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "V", "warrior"), ("p2", "P", "mage")):
        r2.players[pid] = make_player(pid, nome, cls, 0)
    r2.player_order = list(r2.players.keys()); r2.host_pid = "p1"; r2.phase = "city"
    await r2.enter_dungeon("p1")                 # 1ª entrada: nova=True
    check("ground_items vazio na masmorra nova", r2.ground_items == {})
    # larga um item manualmente
    r2.ground_items["gX"] = {"id": "gX", "item": armor_item("leather"), "pos": list(r2.players["p1"]["pos"])}
    await r2._voltar_para_cidade()               # sai pela escada
    check("item persiste ao ir pra cidade", "gX" in r2.ground_items)
    await r2.enter_dungeon("p1")                  # reentra a MESMA masmorra: nova=False
    check("item persiste ao reentrar (mesmo lugar)", "gX" in r2.ground_items)
    # encerrar a missão = dungeon_generated False + volta pra cidade (espelha handle_encerrar_missao)
    await r2._voltar_para_cidade()
    r2.dungeon_generated = False                  # força masmorra nova na próxima entrada
    await r2.enter_dungeon("p1")
    check("item some ao gerar masmorra nova", "gX" not in r2.ground_items)

    print(f"\n===== GROUND ITEMS: {PASS} OK, {FAIL} XX =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
