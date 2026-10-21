"""Raízes do Brejo — a loja e a cena de conversa da Zumbra, na Vila dos Charcos.

Roda da raiz:  python -X utf8 tools/test_zumbra_charcos.py
          e:   node tools/test_zumbra_titulo_cliente.js

REGRA
  • Loja do tipo Mercador, na cabana isolada da borda oeste, com título próprio
    (`titulo_loja`) "Raízes do Brejo". Vende grimórios, Ignus Fatus, Fata Morgana,
    poções mágicas e os pergaminhos do mercador.
  • As poções moram no Templo; a fonte do Mercador as recebe também (mesmos
    dicts), sem mexer no estoque das outras cidades.
  • Cena `raizes_do_brejo` com a Zumbra: conversas que reagem aos fatos da campanha.
"""
import asyncio, copy, json, os, sys, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))

CID = "vila_dos_charcos"
CENA = "raizes_do_brejo"
POCOES = ["pocao_invisibilidade", "pocao_velocidade", "pocao_voo", "pocao_manto_escuridao",
          "pocao_resistencia_fogo", "pocao_resistencia_gelo", "pocao_resistencia_eletricidade",
          "pocao_resistencia_acido", "pocao_resistencia_agua", "pocao_resistencia_sagrado",
          "pocao_barreira_arcana", "elixir_cavalo_ferro", "regeneration_potion"]
CONVERSAS = ["zumbra_chegada", "zumbra_criancas", "zumbra_ferrao", "zumbra_ferrao_morto",
             "zumbra_confia", "zumbra_luto", "zumbra_rumor"]


def sala(fatos=(), concluidas=()):
    r = S.GameRoom("ZUMBRA")
    r.players["p1"] = S.make_player("p1", "Ana", "warrior", 0)
    r.host_pid = "p1"; r.phase = "city"; r.world_location = CID
    r.fatos = set(fatos)
    r.world_adventure_progress = {a: 99 for a in concluidas}
    r.enviados = []
    async def send_to(pid, msg): r.enviados.append(msg)
    async def broadcast(msg, skip=None, personalize=None): pass
    async def push_state_or_city(): pass
    r.send_to = send_to; r.broadcast = broadcast; r.push_state_or_city = push_state_or_city
    r._checkpoint_savegame = lambda: None
    return r


def ids_conversas(r):
    cena = r._city_state_payload()["scenes"].get(CENA) or {}
    return [c["id"] for s in cena.get("slots", []) for c in s.get("conversations", [])]


async def main():
    print("\n[1] Fonte do Mercador recebe as poções mágicas")
    ids_merc = [i["id"] for i in S.SHOP_MERCHANT]
    ids_temp = {i["id"] for i in S.SHOP_TEMPLE}
    check("todas as poções estão na fonte do Mercador", all(p in ids_merc for p in POCOES),
          [p for p in POCOES if p not in ids_merc])
    check("e continuam no Templo", all(p in ids_temp for p in POCOES))
    check("sem id repetido na fonte do Mercador", len(ids_merc) == len(set(ids_merc)))
    check("a poção é o MESMO item nos dois catálogos (preço igual)", all(
        next(i for i in S.SHOP_MERCHANT if i["id"] == p)["price"] == next(i for i in S.SHOP_TEMPLE if i["id"] == p)["price"]
        for p in POCOES))
    check("o estoque das outras cidades não mudou (lista explícita de Alva e Luz)",
          len(S.CITY_SHOPS["alva_e_luz"]["mercador"]) == 92
          and not any(p in S.CITY_SHOPS["alva_e_luz"]["mercador"] for p in POCOES))

    print("\n[2] Estoque da Raízes do Brejo")
    est = S.CITY_SHOPS[CID].get("mercador") or []
    grimorios = [i for i in ids_merc if i.startswith("grimorio_")]
    check("todos os grimórios", grimorios and all(g in est for g in grimorios))
    check("Ignus Fatus e Fata Morgana", "ignus_fatus" in est and "fata_morgana" in est)
    check("todas as poções mágicas", all(p in est for p in POCOES))
    check("nada de armas, armaduras ou munição na lista do mercador",
          not any(i in est for i in ("dagger", "longsword", "escudo_p", "flechas", "plate")))
    r = sala()
    merc = [i["id"] for i in r._city_state_payload()["shops"]["mercador"]]
    check("o estoque chega ao jogador no city_state (loja + pergaminhos do mercador)",
          "grimorio_bola_fogo" in merc and "pocao_invisibilidade" in merc and "ignus_fatus" in merc)
    check("compra de poção pelo Mercador funciona", await _compra(r, "pocao_invisibilidade"))

    print("\n[3] Ponto no mapa da vila")
    pts = S.CITY_MAP_POINTS[CID]
    ponto = next((p for p in pts.values() if p.get("scene") == CENA), None)
    check("existe um ponto ligado à cena", ponto is not None)
    check("é do tipo Mercador, com título próprio", ponto and ponto.get("type") == "mercador"
          and ponto.get("name") == "Raízes do Brejo" and ponto.get("titulo_loja") == "Raízes do Brejo", ponto)
    check("fica na periferia (borda oeste), longe do centro", ponto and ponto["x"] < 35 and 20 <= ponto["y"] <= 45, ponto)
    check("o ponto chega ao cliente", any(p.get("titulo_loja") == "Raízes do Brejo"
          for p in r._city_state_payload()["city_map_points"][CID].values()))
    check("a taverna e a caravana seguem lá", {p.get("type") for p in pts.values()} >= {"taverna", "caravana", "mercador"})

    print("\n[4] titulo_loja sobrevive a salvar e carregar")
    guard = (copy.deepcopy(S.CITY_MAP_POINTS), S._save_city_shops, S._save_city_scenes, S._save_city_map_points)
    S._save_city_shops = S._save_city_scenes = S._save_city_map_points = lambda *a, **k: None
    try:
        S._save_city_shops_upload({}, raw_city_points={CID: {
            "bruxa": {"x": 20.5, "y": 30.2, "type": "mercador", "name": "X", "titulo_loja": "  Lojinha da Teste  "}}})
        salvo = S.CITY_MAP_POINTS[CID].get("bruxa", {})
        check("o save do editor preserva o título (aparado)", salvo.get("titulo_loja") == "Lojinha da Teste", salvo)
        S._save_city_shops_upload({}, raw_city_points={CID: {
            "bruxa": {"x": 20.5, "y": 30.2, "type": "mercador", "titulo_loja": "A" * 200}}})
        check("limite de tamanho no título", len(S.CITY_MAP_POINTS[CID]["bruxa"].get("titulo_loja", "")) <= 60)
        antes_arq = S.CITY_MAP_POINTS_FILE
        with tempfile.TemporaryDirectory() as d:
            arq = os.path.join(d, "pontos.json")
            json.dump({CID: {"bruxa": {"x": 10, "y": 10, "type": "mercador", "titulo_loja": "Do arquivo"}}},
                      open(arq, "w", encoding="utf-8"))
            S.CITY_MAP_POINTS_FILE = arq
            S.CITY_MAP_POINTS[CID] = {}
            S._load_city_map_points()
            check("o carregador preserva o título", S.CITY_MAP_POINTS[CID].get("bruxa", {}).get("titulo_loja") == "Do arquivo")
            S.CITY_MAP_POINTS_FILE = antes_arq
    finally:
        S.CITY_MAP_POINTS.clear(); S.CITY_MAP_POINTS.update(guard[0])
        S._save_city_shops, S._save_city_scenes, S._save_city_map_points = guard[1:]

    print("\n[5] Cena e conversas da Zumbra")
    cena = S.CITY_SCENES[CID].get(CENA)
    check("a cena existe, com nome e fundo", bool(cena) and cena.get("nome") and cena.get("background"))
    slots = (cena or {}).get("slots", [])
    zumbra = next((s for s in slots if s.get("name") == "Zumbra"), None)
    check("há o NPC Zumbra com retrato", zumbra is not None and zumbra.get("image"))
    convs = (zumbra or {}).get("conversations", [])
    check("as sete conversas, sem repetir id", [c["id"] for c in convs] == CONVERSAS, [c["id"] for c in convs])
    check("toda fala tem texto e passa na limpeza do servidor",
          all(c.get("texto") and len(c["texto"]) > 40 for c in convs)
          and len(S._clean_scene_conversations(convs, "")) == len(convs))
    check("os requisitos citam aventuras que existem",
          all((c["requisito"].get("aventura_id") in S.WORLD_ADVENTURES) or not c["requisito"].get("aventura_id") for c in convs))
    check("recompensa em item existe no catálogo",
          all((not c["efeito"].get("item_id")) or c["efeito"]["item_id"] in S._DUNGEON_ITEM_CATALOG for c in convs))

    print("\n[6] A cena reage à campanha (jogo real)")
    r = sala()
    check("sem fatos: chegada e rumor", set(ids_conversas(r)) == {"zumbra_chegada", "zumbra_rumor"}, ids_conversas(r))
    r = sala(fatos={"charcos_criancas_sumidas"})
    check("com o gancho aceito: dica das crianças", "zumbra_criancas" in ids_conversas(r), ids_conversas(r))
    check("com o gancho aceito: dica do Ferrão (antes da expedição; não há volta no meio)", "zumbra_ferrao" in ids_conversas(r), ids_conversas(r))
    r = sala(fatos={"charcos_ferrao_morto"})
    check("Ferrão morto: reação dela", "zumbra_ferrao_morto" in ids_conversas(r), ids_conversas(r))
    r = sala(fatos={"charcos_criancas_mortas"})
    ids = ids_conversas(r)
    check("crianças mortas: luto, e sem a apresentação", "zumbra_luto" in ids and "zumbra_chegada" not in ids, ids)
    r = sala()
    await r.handle_scene_npc("p1", CENA, zumbra["id"], "zumbra_chegada")
    check("a apresentação dá o fato e some depois de usada", "zumbra_conhecida" in r.fatos
          and "zumbra_chegada" not in ids_conversas(r), (r.fatos, ids_conversas(r)))
    await r.handle_scene_npc("p1", CENA, zumbra["id"], "zumbra_chegada")
    check("repetir a apresentação é recusado", any(m.get("type") == "error" for m in r.enviados))
    r = sala(fatos={"charcos_ferrao_morto"})
    await r.handle_scene_npc("p1", CENA, zumbra["id"], "zumbra_ferrao_morto")
    check("a reação ao Ferrão dá o fato de confiança", "zumbra_confia" in r.fatos, r.fatos)
    check("e depois libera a fala de confiança", "zumbra_confia" in ids_conversas(r), ids_conversas(r))

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


async def _compra(r, item_id):
    r.players["p1"]["gold"] = 1000
    await r.handle_shop_buy("p1", "mercador", item_id)
    return not any(m.get("type") == "error" for m in r.enviados) and any(
        (b.get("id") == item_id) for b in r.players["p1"].get("bag", []) if isinstance(b, dict))


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
