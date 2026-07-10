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

    # ── [3] Tick de fogo: 1 dano/rodada, decrementa, expira ─────────────────────
    print("\n[3] _processar_em_chamas_turno")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    m = make_monster(r, "m1", 5, 5, hp=10)
    r._aplicar_em_chamas(p, 2, True)
    r._aplicar_em_chamas(m, 2, False)
    hp_p0, hp_m0 = p["hp"], m["hp"]
    await r._processar_em_chamas_turno()
    check("herói perde 1 HP no tick", p["hp"] == hp_p0 - 1)
    check("monstro perde 1 HP no tick", m["hp"] == hp_m0 - 1)
    check("duração do herói caiu p/ 1", p["em_chamas_rodadas"] == 1)
    await r._processar_em_chamas_turno()
    check("status do herói expira (0)", p.get("em_chamas_rodadas", 0) == 0)
    hp_p1 = p["hp"]
    await r._processar_em_chamas_turno()
    check("sem status → sem dano extra", p["hp"] == hp_p1)

    # ── [4] handle_throw_item: acerto, consumo, chamas, alcance, LOS ────────────
    print("\n[4] handle_throw_item")

    # (4a) Acerto garantido (CA baixa) → dano + em chamas + item consumido
    r = setup(); random.seed(2)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    r.players["p1"] = p; p["bag"] = [throwable("frasco_oleo")]
    m = make_monster(r, "m1", 4, 6, hp=30, ac=1)   # 2 casas, LOS livre
    hp0 = m["hp"]
    await r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"})
    check("acerto causou dano", m["hp"] < hp0)
    check("alvo ficou em chamas", m.get("em_chamas_rodadas", 0) > 0)
    check("item consumido da bolsa", len(p["bag"]) == 0)
    check("ação principal gasta", p.get("action_done") is True)

    # (4b) Fora de alcance → recusa, item NÃO consumido, ação livre
    r = setup(); random.seed(2)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [0, 0]; r.players["p1"] = p
    p["bag"] = [throwable("frasco_oleo")]
    m = make_monster(r, "m1", 8, 8, ac=1)   # >4 casas
    await r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"})
    check("fora de alcance: item mantido", len(p["bag"]) == 1)
    check("fora de alcance: ação NÃO gasta", not p.get("action_done"))
    check("fora de alcance: erro enviado", any("alcance" in e.lower() for e in r._errs))

    # (4c) Parede bloqueia LOS → recusa
    r = setup(); random.seed(2)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [throwable("fogo_grego")]
    r.tiles[4][5] = WALL   # parede entre (4,4) e (4,6) na coluna? ver orientação abaixo
    r.tiles[5][4] = WALL   # bloqueia a coluna x=4 em y=5
    m = make_monster(r, "m1", 4, 6, ac=1)
    await r.handle_throw_item("p1", {"item_id": "fogo_grego", "target_id": "m1"})
    check("LOS bloqueada: item mantido", len(p["bag"]) == 1)

    # (4d) Erro (CA altíssima) → item consumido, sem dano, sem chamas, ação gasta
    r = setup(); random.seed(7)   # seed evita nat20 (que seria acerto crítico)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [throwable("frasco_oleo")]
    m = make_monster(r, "m1", 4, 6, hp=30, ac=99)   # no alcance, LOS livre, impossível acertar
    hp0 = m["hp"]
    await r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"})
    check("erro: item consumido (espatifa)", len(p["bag"]) == 0)
    check("erro: alvo NÃO sofre dano", m["hp"] == hp0)
    check("erro: alvo NÃO pega fogo", m.get("em_chamas_rodadas", 0) == 0)
    check("erro: ação principal gasta", p.get("action_done") is True)

    # ── [5] Beber água apaga chamas (ação livre); Fogo Grego ignora ─────────────
    print("\n[5] Água apaga chamas")
    from server import _TAVERN_BY_ID  # garrafa_agua vive aqui
    def agua():
        return deepcopy(_TAVERN_BY_ID["garrafa_agua"])

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [agua()]
    r._aplicar_em_chamas(p, 3, True)   # óleo → água apaga
    await r.handle_use_item("p1", "garrafa_agua")
    check("óleo: água apagou as chamas", p.get("em_chamas_rodadas", 0) == 0)
    check("óleo: garrafa consumida", len(p["bag"]) == 0)
    check("óleo: ação NÃO gasta (livre)", not p.get("action_done"))

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [agua()]
    r._aplicar_em_chamas(p, 3, False)  # Fogo Grego → água NÃO apaga
    await r.handle_use_item("p1", "garrafa_agua")
    check("grego: chamas continuam", p.get("em_chamas_rodadas", 0) == 3)
    check("grego: garrafa NÃO consumida", len(p["bag"]) == 1)
    check("grego: erro explicativo", any("água" in e.lower() or "grego" in e.lower() for e in r._errs))

    # ── [6] Apagar batendo (gasta ação principal) — funciona p/ Fogo Grego ──────
    print("\n[6] handle_apagar_chamas")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    r._aplicar_em_chamas(p, 3, False)  # Fogo Grego
    await r.handle_apagar_chamas("p1")
    check("chamas apagadas", p.get("em_chamas_rodadas", 0) == 0)
    check("ação principal gasta", p.get("action_done") is True)

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    await r.handle_apagar_chamas("p1")   # não está em chamas
    check("sem chamas: erro", any("chama" in e.lower() for e in r._errs))
    check("sem chamas: ação NÃO gasta", not p.get("action_done"))

    # ── [7] Correções de revisão ────────────────────────────────────────────────
    print("\n[7] Fixes de revisão")

    # (7a) Ressurreição limpa 'em chamas' → tick seguinte não re-mata o revivido
    r = setup()
    lewis = make_player("cle", "Lewis", "cleric", 0); lewis["pos"] = [4, 4]
    r.players["cle"] = lewis
    alvo = make_player("mor", "Morto", "warrior", 1); alvo["pos"] = [5, 4]
    alvo["alive"] = False; alvo["hp"] = 0
    r.players["mor"] = alvo
    r._aplicar_em_chamas(alvo, 3, True)   # estava em chamas ao morrer
    await r.handle_ressurreicao("cle", {"target_id": "mor"})
    check("ressurreição: revivido está vivo", alvo["alive"] is True)
    check("ressurreição: chamas zeradas", alvo.get("em_chamas_rodadas", 0) == 0)
    await r._processar_em_chamas_turno()
    check("ressurreição: tick não re-mata (segue vivo)", alvo["alive"] is True)

    # (7b) handle_use_item com item throwable → recusa sem apagar o item
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [throwable("frasco_oleo")]
    await r.handle_use_item("p1", "frasco_oleo")
    check("throwable via use_item: item NÃO apagado", len(p["bag"]) == 1)
    check("throwable via use_item: erro enviado", any("arremess" in e.lower() for e in r._errs))

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
