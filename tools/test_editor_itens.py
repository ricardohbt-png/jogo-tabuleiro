"""Editor de Itens — Fase 1 (Armas). Roda da raiz: python tools/test_editor_itens.py"""
import sys, os, json, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sample(**over):
    base = {"id": "espada_flamejante", "name": "Espada Flamejante", "emoji": "⚔️",
            "item_type": "weapon", "die": "1d8", "stat": "str_", "categoria": "cortante",
            "damage_bonus": 1, "extra_damages": [{"die": "1d6", "type": "fire"}],
            "allowed_classes": [], "price": 40,
            "disponibilidade": {"loja": True, "baus": True, "loot_monstro": True}}
    base.update(over); return base

def test_validacao():
    print("\n[1] Validacao")
    ok, item = S._validate_custom_item(sample())
    check("aceita arma valida", ok)
    check("normaliza die", ok and item["die"] == "1d8")
    ok2, _ = S._validate_custom_item(sample(die="1d7"))
    check("rejeita dado invalido (1d7)", not ok2)
    ok3, _ = S._validate_custom_item(sample(categoria="magico"))
    check("rejeita categoria invalida", not ok3)
    ok4, _ = S._validate_custom_item(sample(extra_damages=[{"die": "1d6", "type": "trevas"}]))
    check("rejeita tipo elemental desconhecido", not ok4)
    ok5, _ = S._validate_custom_item(sample(id="longsword"))
    check("rejeita id que colide com arma nativa", not ok5)

def test_merge():
    print("\n[2] Merge nos catalogos vivos")
    ok, item = S._validate_custom_item(sample())
    S._apply_custom_items([item])
    check("entra em WEAPONS", "espada_flamejante" in S.WEAPONS)
    check("WEAPONS carrega extra_damages", S.WEAPONS["espada_flamejante"].get("extra_damages"))
    check("loja: entra em SHOP_WEAPONS", any(w["id"] == "espada_flamejante" for w in S.SHOP_WEAPONS))
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "espada_flamejante" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "espada_flamejante" in S.LOOT_POOL_PROCEDURAL)
    S._apply_custom_items([item])
    check("reaplicar nao duplica em SHOP_WEAPONS",
          sum(1 for w in S.SHOP_WEAPONS if w["id"] == "espada_flamejante") == 1)
    check("reaplicar nao duplica em LOOT_POOL_PROCEDURAL",
          S.LOOT_POOL_PROCEDURAL.count("espada_flamejante") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de WEAPONS", "espada_flamejante" not in S.WEAPONS)
    check("lista vazia remove de SHOP_WEAPONS", not any(w["id"] == "espada_flamejante" for w in S.SHOP_WEAPONS))
    check("lista vazia remove de LOOT_POOL_PROCEDURAL", "espada_flamejante" not in S.LOOT_POOL_PROCEDURAL)

def test_base_intacta():
    print("\n[3] Itens base intocados")
    antes = dict(S.WEAPONS["longsword"])
    S._apply_custom_items([S._validate_custom_item(sample(id="nova_arma"))[1]])
    check("longsword base inalterada", S.WEAPONS["longsword"] == antes)
    S._apply_custom_items([])

def test_upload_art():
    print("\n[4] Upload de arte do item")
    import base64
    PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 32).decode()
    ok, key = S._save_item_art("espada_flamejante.png", PNG)
    check("salva PNG valido", ok)
    dest = os.path.join(S.BASE_DIR, "assets", "itens", "espada_flamejante.png")
    check("gravou em assets/itens/<id>.png", ok and os.path.exists(dest))
    if ok and os.path.exists(dest):
        os.remove(dest)
    ok2, _ = S._save_item_art("x.gif", PNG)
    check("rejeita extensao nao-png", not ok2)
    ok3, _ = S._save_item_art("y.png", base64.b64encode(b"not a png").decode())
    check("rejeita conteudo nao-PNG", not ok3)
    ok4, _ = S._save_item_art("../../evil.png", PNG)
    # basename() reduz para "evil.png" e grava dentro de assets/itens — nunca fora
    fora = os.path.join(S.BASE_DIR, "evil.png")
    check("path traversal neutralizado (nao grava fora de assets/itens)", not os.path.exists(fora))
    inside = os.path.join(S.BASE_DIR, "assets", "itens", "evil.png")
    if os.path.exists(inside): os.remove(inside)

def test_save_item():
    print("\n[5] Salvar item (fluxo completo)")
    ok, item = S._save_custom_item(sample(id="teste_persist"))
    check("save retorna ok", ok)
    check("consta no arquivo JSON", any(r.get("id") == "teste_persist" for r in S._read_custom_items()))
    check("mesclado em WEAPONS", "teste_persist" in S.WEAPONS)
    recs = [r for r in S._read_custom_items() if r.get("id") != "teste_persist"]
    S._gravar_def(recs, os.path.dirname(S.CUSTOM_ITEMS_FILE), os.path.basename(S.CUSTOM_ITEMS_FILE))
    S._apply_custom_items(recs); S._regen_custom_items_index(recs)

import asyncio
from copy import deepcopy

def _room_com_alvo():
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = "playing"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["pos"] = [1, 1]; p["atk_bonus"] = 50   # garante acerto
    r.monsters["m1"] = {"id": "m1", "name": "Alvo", "type": "orc", "hp": 999, "ac": 1,
                        "pos": [2, 1], "alive": True, "special_abilities": []}
    return r, p

def _dano_de_um_ataque(weapon):
    r, p = _room_com_alvo()
    p["weapon"] = deepcopy(weapon)
    import random; random.seed(1234)
    hp0 = r.monsters["m1"]["hp"]
    asyncio.run(r.handle_attack("p1", "m1"))
    return hp0 - r.monsters["m1"]["hp"]

def test_combate_passivo():
    print("\n[6] Efeitos passivos no combate")
    plain = {"id": "wt", "name": "T", "die": "1d8", "stat": "str_", "categoria": "cortante"}
    with_elem = dict(plain, extra_damages=[{"die": "1d6", "type": "fire"}])
    with_dmg  = dict(plain, damage_bonus=5)
    check("dano elemental soma dano extra", _dano_de_um_ataque(with_elem) > _dano_de_um_ataque(plain))
    check("damage_bonus +5 soma exatamente 5", _dano_de_um_ataque(with_dmg) - _dano_de_um_ataque(plain) == 5)

    def cap_eff(bonus):
        r, p = _room_com_alvo(); p["atk_bonus"] = 0
        p["weapon"] = {"id": "wt", "name": "T", "die": "1d8", "stat": "str_",
                       "categoria": "cortante", "atk_bonus": bonus}
        cap = {}
        orig = r._rolar_ataque
        def spy(eff_atk, *a, **k):
            cap["e"] = eff_atk; return orig(eff_atk, *a, **k)
        r._rolar_ataque = spy
        asyncio.run(r.handle_attack("p1", "m1"))
        return cap["e"]
    check("atk_bonus da arma soma +7 no eff_atk", cap_eff(7) - cap_eff(0) == 7)

    def cap_offhand(bonus):
        r, p = _room_com_alvo()
        p["weapon"] = {"id": "wt", "name": "T", "die": "1d8", "stat": "str_",
                       "categoria": "cortante", "atk_bonus": bonus}
        p["gear"]["off_hand"] = {"id": "dagger", "name": "Adaga", "die": "1d4",
                                  "stat": "dex_", "categoria": "perfurante"}
        calls = []
        orig = S.d20_attack
        def spy(atk_bonus, target_ac):
            calls.append(atk_bonus); return orig(atk_bonus, target_ac)
        S.d20_attack = spy
        try:
            asyncio.run(r.handle_attack("p1", "m1"))
        finally:
            S.d20_attack = orig
        # calls[0] = ataque principal (eff_atk); calls[1] = mão secundária (offhand_atk)
        return calls[1] if len(calls) > 1 else None
    check("mão secundária NÃO herda o atk_bonus da arma principal",
          cap_offhand(0) == cap_offhand(7))

def test_compra_equipa_preserva():
    print("\n[7] Comprar+equipar preserva campos custom")
    ok_lg, lamina = S._validate_custom_item(sample(id="lamina_gelo",
        extra_damages=[{"die": "1d6", "type": "cold"}], damage_bonus=2))
    S._apply_custom_items([lamina])
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True; r.phase = "city"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["gold"] = 9999; p["bag"] = []; p["gear"]["weapon"] = None
    # A loja da cidade só vende o que está no estoque dela (city_shops.json) —
    # é o que o checkbox "Loja" do editor sincroniza.
    orig_stock, tmp_stock = _stock_sandbox()
    try:
        S._sync_custom_item_city_stock(lamina, [r.world_location])
        asyncio.run(r.handle_shop_buy("p1", "ferreiro_weapon", "lamina_gelo"))
        comprada = next((it for it in p["bag"] if it and it.get("id") == "lamina_gelo"), None)
        check("comprada foi pra bolsa", comprada is not None)
        check("bolsa preserva extra_damages", comprada and comprada.get("extra_damages"))
        check("bolsa preserva damage_bonus", comprada and comprada.get("damage_bonus") == 2)
        idx = p["bag"].index(comprada)
        asyncio.run(r._executar_equip_from_bag("p1", idx))
        check("equipar sincroniza extra_damages em p['weapon']", p["weapon"].get("extra_damages"))
    finally:
        S.CITY_SHOPS_FILE = orig_stock["file"]
        S.CITY_SHOPS.clear(); S.CITY_SHOPS.update(orig_stock["stock"])
        try: os.unlink(tmp_stock)
        except OSError: pass
    S._apply_custom_items([])

def test_corrosao():
    print("\n[8] Corrosao: niveis livres/penalidade")
    ok, item = S._validate_custom_item(sample(id="lamina_reforcada",
        corrosao_resistente=2, corrosao_niveis_penalidade=3))
    check("valida corrosao_resistente", ok and item.get("corrosao_resistente") == 2)
    check("valida corrosao_niveis_penalidade", ok and item.get("corrosao_niveis_penalidade") == 3)
    ok2, item2 = S._validate_custom_item(sample(id="arma_normal"))
    check("defaults (0 livres / 2 penalidade)",
          ok2 and item2.get("corrosao_resistente") == 0 and item2.get("corrosao_niveis_penalidade") == 2)
    S._apply_custom_items([item])
    check("WEAPONS carrega os dois campos",
          S.WEAPONS["lamina_reforcada"].get("corrosao_resistente") == 2
          and S.WEAPONS["lamina_reforcada"].get("corrosao_niveis_penalidade") == 3)
    S._apply_custom_items([])

def test_penalidade_engine():
    print("\n[9] Corrosao no motor: penalidade escala e quebra em N+M+1")
    r = S.GameRoom("TEST")
    p = S.make_player("p1", "Victor", "warrior", 0)
    # N=1 livre, M=3 penalidade → quebra no nivel 1+3+1=5; penalidade -1,-2,-3.
    p["weapon"] = {"id": "arma_t", "name": "T", "die": "1d8", "stat": "str_",
                   "categoria": "cortante", "corrosao_resistente": 1, "corrosao_niveis_penalidade": 3}
    c = p.setdefault("corrosao", {})
    def pen_no_nivel(lvl):
        c["arma_lvl"] = lvl; c["arma_destruida"] = False
        return r._corrosao_arma_pen(p)
    check("nivel 1 (livre) sem penalidade", pen_no_nivel(1) == 0)
    check("nivel 2 penalidade -1", pen_no_nivel(2) == 1)
    check("nivel 3 penalidade -2", pen_no_nivel(3) == 2)
    check("nivel 4 penalidade -3 (teto = M)", pen_no_nivel(4) == 3)
    check("nivel 5 penalidade travada em M=3", pen_no_nivel(5) == 3)
    # Arma normal (sem campos) permanece identica: -1,-2, teto 2.
    p["weapon"] = {"id": "n", "name": "N", "die": "1d6", "stat": "str_", "categoria": "cortante"}
    check("arma normal nivel 2 = -2", pen_no_nivel(2) == 2)
    check("arma normal nivel 3 travada em 2", pen_no_nivel(3) == 2)

def test_material_e_municao():
    print("\n[10] Material -> set de corrosao; municao -> RANGED_AMMO")
    madeira = S._validate_custom_item(sample(id="cajado_t", material="madeira"))[1]
    metal   = S._validate_custom_item(sample(id="espada_t", material="metal"))[1]
    arco    = S._validate_custom_item(sample(id="arco_t", range=6, ammo="flechas",
                                             disponibilidade={"loja": True, "baus": False, "loot_monstro": False}))[1]
    besta   = S._validate_custom_item(sample(id="besta_t", range=8, ammo="virotes",
                                             disponibilidade={"loja": True, "baus": False, "loot_monstro": False}))[1]
    S._apply_custom_items([madeira, metal, arco, besta])
    check("madeira entra em CORROSAO_ARMA_MADEIRA", "cajado_t" in S.CORROSAO_ARMA_MADEIRA)
    check("metal entra em CORROSAO_ARMA_METAL", "espada_t" in S.CORROSAO_ARMA_METAL)
    check("arco requer flechas (RANGED_AMMO)", "flechas" in S.RANGED_AMMO.get("arco_t", []))
    check("besta requer virotes (RANGED_AMMO)", "virotes" in S.RANGED_AMMO.get("besta_t", []))
    check("municao ignorada sem alcance", "ammo" not in S._validate_custom_item(sample(id="soco_t", ammo="flechas"))[1])
    # cleanup idempotente: lista vazia remove dos sets e do RANGED_AMMO
    S._apply_custom_items([])
    check("cleanup remove de CORROSAO_ARMA_MADEIRA", "cajado_t" not in S.CORROSAO_ARMA_MADEIRA)
    check("cleanup remove de CORROSAO_ARMA_METAL", "espada_t" not in S.CORROSAO_ARMA_METAL)
    check("cleanup remove de RANGED_AMMO", "arco_t" not in S.RANGED_AMMO)
    # bases nativas do RANGED_AMMO/sets permanecem intactas
    check("base arco_curto intacto em RANGED_AMMO", "flechas" in S.RANGED_AMMO.get("arco_curto", []))
    check("base dagger intacto em CORROSAO_ARMA_METAL", "dagger" in S.CORROSAO_ARMA_METAL)

def armor_sample(**over):
    base = {"id": "cota_teste", "name": "Cota Teste", "emoji": "🛡️", "item_type": "armor",
            "ac_bonus": 4, "armor_category": "media", "corrosion_materials": ["metal"],
            "corrosao_resistente": 0, "corrosao_niveis_penalidade": 2,
            "bonuses": [{"effect": "maxhp", "value": 5}], "allowed_classes": ["warrior"],
            "price": 120, "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def accessory_sample(**over):
    base = {"id": "anel_teste", "name": "Anel Teste", "emoji": "💍", "item_type": "ring",
            "bonuses": [{"effect": "maxhp", "value": 5}, {"effect": "atk_bonus", "value": 1}],
            "allowed_classes": [], "price": 30,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def potion_sample(**over):
    base = {"id": "pocao_teste", "name": "Poção Teste", "emoji": "🧪", "item_type": "potion",
            "effect": "heal", "value": 15, "allowed_classes": [], "price": 20,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def throwable_sample(**over):
    base = {"id": "frasco_teste", "name": "Frasco Teste", "emoji": "💥",
            "item_type": "throwable", "alvo": "ataque_alvo", "alcance": 4,
            "dano": "2d6", "elemento": "fogo", "allowed_classes": [], "price": 25,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def poison_sample(**over):
    base = {"id": "veneno_teste", "name": "Veneno Teste", "emoji": "☠️",
            "item_type": "poison", "operacao": "dano", "dano": "1d4",
            "save": "fortitude", "dificuldade": 12, "anula": True, "duracao": "1d6",
            "save_aplicacao": True, "descricao": "Dói.",
            "allowed_classes": [], "price": 20,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def test_validacao_veneno():
    print("\n[H1] Validacao de veneno")
    ok, it = S._validate_custom_item(poison_sample())
    check("aceita veneno de dano", ok)
    check("item_type/slot/effect",
          ok and it.get("item_type") == "poison" and it.get("item_slot") == "bag"
          and it.get("effect") == "coat_poison")
    check("campos comuns preservados",
          ok and it.get("save") == "fortitude" and it.get("dificuldade") == 12
          and it.get("anula") is True and it.get("duracao") == "1d6")
    check("dano + save_aplicacao", ok and it.get("dano") == "1d4" and it.get("save_aplicacao") is True)
    check("descricao preservada", ok and it.get("descricao") == "Dói.")
    okr, itr = S._validate_custom_item(poison_sample(id="veneno_red", operacao="reduzir",
        atributo="constituicao", valor="1d4"))
    check("aceita reduzir", okr and itr.get("operacao") == "reduzir"
          and itr.get("atributo") == "constituicao" and itr.get("valor") == "1d4")
    okp, itp = S._validate_custom_item(poison_sample(id="veneno_pen", operacao="penalidade",
        atributos=[["ataque", -2], ["movimento", -1], ["xpto", -9]]))
    check("penalidade filtra chave invalida",
          okp and itp.get("atributos") == [["ataque", -2], ["movimento", -1]])
    okt, itt = S._validate_custom_item(poison_sample(id="veneno_pet", operacao="petrificar",
        anula=False, duracao_falha="1d4", penalidade_falha=[["movimento", -1]]))
    check("aceita petrificar", okt and itt.get("operacao") == "petrificar"
          and itt.get("duracao_falha") == "1d4"
          and itt.get("penalidade_falha") == [["movimento", -1]])
    okc, itc = S._validate_custom_item(poison_sample(id="veneno_ceg", operacao="cegar",
        anula=False, penalidade_ataque=-4, bloqueia_distancia=True, duracao_falha="1d4"))
    check("aceita cegar", okc and itc.get("operacao") == "cegar"
          and itc.get("penalidade_ataque") == -4 and itc.get("bloqueia_distancia") is True)
    oko, _ = S._validate_custom_item(poison_sample(operacao="explodir"))
    check("rejeita operacao invalida", not oko)
    oka, _ = S._validate_custom_item(poison_sample(operacao="reduzir", atributo="carisma"))
    check("rejeita atributo invalido em reduzir", not oka)
    okv, _ = S._validate_custom_item(poison_sample(operacao="penalidade", atributos=[]))
    check("rejeita penalidade sem pares", not okv)
    okn, _ = S._validate_custom_item(poison_sample(id="veneno_fungo_acre"))
    check("rejeita id nativo de VENENOS", not okn)
    oks, its = S._validate_custom_item(poison_sample(save="carisma"))
    check("save invalido cai para fortitude", oks and its.get("save") == "fortitude")

def test_veneno_merge():
    print("\n[H2] Merge de veneno (VENENOS + lojas)")
    ok, it = S._validate_custom_item(poison_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("entra em VENENOS", "veneno_teste" in S.VENENOS)
    check("defn carrega operacao/dificuldade",
          S.VENENOS.get("veneno_teste", {}).get("operacao") == "dano"
          and S.VENENOS["veneno_teste"].get("dificuldade") == 12)
    check("defn usa 'nome' (formato nativo)", S.VENENOS.get("veneno_teste", {}).get("nome") == "Veneno Teste")
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "veneno_teste" for i in S.SHOP_MERCHANT))
    _inv = next(i for i in S.SHOP_MERCHANT if i["id"] == "veneno_teste")
    check("item aponta veneno_id", _inv.get("veneno_id") == "veneno_teste")
    check("item carrega efeito p/ tooltip",
          (_inv.get("efeito") or {}).get("dificuldade") == 12
          and (_inv.get("efeito") or {}).get("save") == "fortitude")
    check("item carrega descricao", _inv.get("descricao") == "Dói.")
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "veneno_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "veneno_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo VENENOS intacto", "veneno_fungo_acre" in S.VENENOS)
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "veneno_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de VENENOS", "veneno_teste" not in S.VENENOS)
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "veneno_teste" for i in S.SHOP_MERCHANT))
    check("nativos de VENENOS sobrevivem ao clear", "veneno_fungo_acre" in S.VENENOS)

def test_veneno_uso():
    print("\n[H3] Untar a arma e envenenar no acerto")
    ok, it = S._validate_custom_item(poison_sample(dificuldade=40))   # CD 40 → alvo sempre falha
    S._apply_custom_items([it])
    r, p = _room_com_alvo()
    p["weapon"] = {"id": "wt", "name": "Lâmina", "die": "1d8", "stat": "str_",
                   "categoria": "cortante", "poison_slots": []}
    p["bag"] = [dict(S._custom_poison_inventory_dict(it))]
    asyncio.run(r.handle_use_item("p1", "veneno_teste"))
    check("arma recebeu carga de veneno", r._weapon_poison_slots(p) == ["veneno_teste"])
    check("frasco consumido", not any(i["id"] == "veneno_teste" for i in p["bag"]))
    import random; random.seed(99)
    asyncio.run(r.handle_attack("p1", "m1"))
    efeitos = r.monsters["m1"].get("efeitos_veneno", [])
    check("alvo envenenado no acerto", any(e.get("nome") == "Veneno Teste" for e in efeitos))
    check("carga consumida", r._weapon_poison_slots(p) == [])
    S._apply_custom_items([])

def test_veneno_efeitos():
    print("\n[H4] Efeitos de reduzir e cegar")
    okr, itr = S._validate_custom_item(poison_sample(id="veneno_red", operacao="reduzir",
        atributo="forca", valor="1d4", dificuldade=40))
    S._apply_custom_items([itr])
    r, p = _room_com_alvo()
    alvo = r.monsters["m1"]
    alvo["penalidades"] = {}
    asyncio.run(r._aplicar_veneno(alvo, "veneno_red"))
    check("reduzir registra efeito", any(e.get("operacao") == "reduzir"
          for e in alvo.get("efeitos_veneno", [])))
    okc, itc = S._validate_custom_item(poison_sample(id="veneno_ceg", operacao="cegar",
        anula=False, dificuldade=40, penalidade_ataque=-4, bloqueia_distancia=True))
    S._apply_custom_items([itc])
    r2, p2 = _room_com_alvo()
    alvo2 = r2.monsters["m1"]
    alvo2["penalidades"] = {}
    asyncio.run(r2._aplicar_veneno(alvo2, "veneno_ceg"))
    check("cegar liga o status", alvo2.get("cego") is True)
    check("cegar aplica penalidade de ataque", alvo2["penalidades"].get("ataque") == -4)
    check("cegar bloqueia distancia", alvo2.get("bloqueia_distancia") is True)
    S._apply_custom_items([])

def test_veneno_msg_penalidade():
    print("\n[H5] Mensagem de penalidade reflete os valores reais")
    ok, it = S._validate_custom_item(poison_sample(id="veneno_pen2", operacao="penalidade",
        atributos=[["ataque", -3], ["ca", -2]], dificuldade=40))
    S._apply_custom_items([it])
    r, p = _room_com_alvo()
    falas = []
    async def cap(msg): falas.append(msg)
    r.gm_say = cap
    alvo = r.monsters["m1"]
    alvo["penalidades"] = {}
    asyncio.run(r._aplicar_veneno(alvo, "veneno_pen2"))
    txt = " ".join(falas)
    check("mensagem cita -3 ataque", "-3 ataque" in txt)
    check("mensagem cita -2 ca", "-2 ca" in txt)
    check("mensagem nao usa o texto fixo antigo", "-1 ataque e -1 movimento" not in txt)
    check("penalidades aplicadas de fato",
          alvo["penalidades"].get("ataque") == -3 and alvo["penalidades"].get("ca") == -2)
    S._apply_custom_items([])

def test_validacao_arremessavel():
    print("\n[G1] Validacao de arremessável")
    ok, it = S._validate_custom_item(throwable_sample())
    check("aceita arremessável mirado", ok)
    check("item_type = throwable", ok and it.get("item_type") == "throwable")
    check("item_slot = bag + effect throwable",
          ok and it.get("item_slot") == "bag" and it.get("effect") == "throwable")
    check("alvo/alcance/dano preservados",
          ok and it.get("alvo") == "ataque_alvo" and it.get("alcance") == 4 and it.get("dano") == "2d6")
    check("mirado nao grava area_raio/save", ok and "area_raio" not in it and "save" not in it)
    oka, ita = S._validate_custom_item(throwable_sample(id="bomba_teste", alvo="area",
        area_raio=2, save_cd=13, dano="3d6", elemento="explosao"))
    check("aceita área com raio", oka and ita.get("alvo") == "area" and ita.get("area_raio") == 2)
    check("área grava save reflexos+cd",
          oka and ita.get("save") == {"tipo": "reflexos", "cd": 13})
    okc, itc = S._validate_custom_item(throwable_sample(id="frasco_chamas",
        em_chamas=True, chamas_dur="1d6", chamas_agua_apaga=False))
    check("em_chamas grava duracao e agua_apaga",
          okc and itc.get("em_chamas") is True and itc.get("chamas_dur") == "1d6"
          and itc.get("chamas_agua_apaga") is False)
    oks, its = S._validate_custom_item(throwable_sample(id="frasco_seco", dano=None))
    check("sem dano nao grava dano/elemento", oks and "dano" not in its and "elemento" not in its)
    okb, _ = S._validate_custom_item(throwable_sample(alvo="parede"))
    check("rejeita alvo invalido", not okb)
    okd, _ = S._validate_custom_item(throwable_sample(dano="2d7"))
    check("rejeita dado de dano invalido", not okd)
    okn, _ = S._validate_custom_item(throwable_sample(id="frasco_oleo"))
    check("rejeita id nativo de ARREMESSAVEIS (frasco_oleo)", not okn)
    oke, _ = S._validate_custom_item(throwable_sample(id="elixir"))
    check("rejeita id nativo de loja (elixir)", not oke)

def test_arremessavel_merge():
    print("\n[G2] Merge de arremessável (ARREMESSAVEIS + lojas)")
    ok, it = S._validate_custom_item(throwable_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("entra em ARREMESSAVEIS", "frasco_teste" in S.ARREMESSAVEIS)
    check("defn carrega alvo/dano",
          S.ARREMESSAVEIS.get("frasco_teste", {}).get("alvo") == "ataque_alvo"
          and S.ARREMESSAVEIS["frasco_teste"].get("dano") == "2d6")
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "frasco_teste" for i in S.SHOP_MERCHANT))
    check("item de bolsa carrega metadados de mira",
          next(i for i in S.SHOP_MERCHANT if i["id"] == "frasco_teste").get("alvo") == "ataque_alvo")
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "frasco_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "frasco_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo ARREMESSAVEIS (frasco_oleo) intacto", "frasco_oleo" in S.ARREMESSAVEIS)
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "frasco_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de ARREMESSAVEIS", "frasco_teste" not in S.ARREMESSAVEIS)
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "frasco_teste" for i in S.SHOP_MERCHANT))
    check("lista vazia remove de _DUNGEON_ITEM_CATALOG", "frasco_teste" not in S._DUNGEON_ITEM_CATALOG)
    check("nativos de ARREMESSAVEIS sobrevivem ao clear", "frasco_oleo" in S.ARREMESSAVEIS)

def test_arremessavel_uso_alvo():
    print("\n[G3] Arremesso mirado ponta-a-ponta")
    ok, it = S._validate_custom_item(throwable_sample(dano="2d6", em_chamas=True))
    S._apply_custom_items([it])
    r, p = _room_com_alvo()          # turno forçado, LOS livre, atk_bonus 50, monstro ac 1
    p["bag"] = [dict(S._custom_throwable_inventory_dict(it))]
    hp0 = r.monsters["m1"]["hp"]
    import random; random.seed(4321)   # evita nat1 (que faria o arremesso errar)
    asyncio.run(r.handle_throw_item("p1", {"item_id": "frasco_teste", "target_id": "m1"}))
    check("alvo sofre dano", r.monsters["m1"]["hp"] < hp0)
    check("item consumido da bolsa", not any(i["id"] == "frasco_teste" for i in p["bag"]))
    check("gastou a ação principal", p.get("action_done") is True)
    check("alvo pegou fogo", r.monsters["m1"].get("em_chamas_rodadas", 0) > 0)
    S._apply_custom_items([])

def test_arremessavel_uso_area():
    print("\n[G4] Arremesso de área ponta-a-ponta")
    ok, it = S._validate_custom_item(throwable_sample(id="bomba_teste", alvo="area",
        area_raio=1, save_cd=99, dano="3d6", elemento="explosao"))   # cd 99 → save sempre falha
    S._apply_custom_items([it])
    r, p = _room_com_alvo()
    r.monsters["m1"]["pos"] = [4, 1]   # dentro do alcance (4) mas fora do raio da área (1) do herói
    p["bag"] = [dict(S._custom_throwable_inventory_dict(it))]
    hp0 = r.monsters["m1"]["hp"]
    asyncio.run(r.handle_throw_item("p1", {"item_id": "bomba_teste", "tx": 4, "ty": 1}))
    check("alvo na área sofre dano", r.monsters["m1"]["hp"] < hp0)
    check("item de área consumido", not any(i["id"] == "bomba_teste" for i in p["bag"]))
    check("herói fora do raio ileso", p["hp"] == p["max_hp"])
    S._apply_custom_items([])

def test_validacao_pocao():
    print("\n[F1] Validacao de poção")
    ok, it = S._validate_custom_item(potion_sample())
    check("aceita poção heal valida", ok)
    check("item_type = potion", ok and it.get("item_type") == "potion")
    check("item_slot = bag", ok and it.get("item_slot") == "bag")
    check("effect/value preservados", ok and it.get("effect") == "heal" and it.get("value") == 15)
    check("single-dose nao grava uses_left", ok and "uses_left" not in it)
    okd, itd = S._validate_custom_item(potion_sample(id="pocao_doses", max_uses=3))
    check("heal multi-dose grava max_uses+uses_left",
          okd and itd.get("max_uses") == 3 and itd.get("uses_left") == 3)
    okr, itr = S._validate_custom_item(potion_sample(id="pocao_regen", effect="regeneration", value=10))
    check("aceita regeneration", okr and itr.get("effect") == "regeneration")
    oka, ita = S._validate_custom_item(potion_sample(id="pocao_elixir", effect="atk_bonus", value=3, max_uses=5))
    check("atk_bonus ignora doses", oka and "max_uses" not in ita)
    okb, _ = S._validate_custom_item(potion_sample(effect="teleporte"))
    check("rejeita effect invalido", not okb)
    okn, _ = S._validate_custom_item(potion_sample(id="health_potion"))
    check("rejeita id nativo (health_potion)", not okn)
    oke, _ = S._validate_custom_item(potion_sample(id="elixir"))
    check("rejeita id nativo do mercador (elixir)", not oke)

def test_pocao_merge():
    print("\n[F2] Merge de poção no mercador/baús/loot")
    ok, it = S._validate_custom_item(potion_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "pocao_teste" for i in S.SHOP_MERCHANT))
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "pocao_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "pocao_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo SHOP_MERCHANT (elixir) intacto", any(i["id"] == "elixir" for i in S.SHOP_MERCHANT))
    check("nativo SHOP_TEMPLE (health_potion) intacto", any(i["id"] == "health_potion" for i in S.SHOP_TEMPLE))
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "pocao_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "pocao_teste" for i in S.SHOP_MERCHANT))
    check("lista vazia remove de _DUNGEON_ITEM_CATALOG", "pocao_teste" not in S._DUNGEON_ITEM_CATALOG)
    check("lista vazia remove de LOOT_POOL_PROCEDURAL", "pocao_teste" not in S.LOOT_POOL_PROCEDURAL)

def _turn_room():
    """Sala mínima com um herói cujo turno está ativo (para handle_use_item)."""
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None   # força o caminho player_order em current_pid
    return r, p

def test_pocao_uso():
    print("\n[F3] Uso ponta-a-ponta via handle_use_item")
    # Cura
    r, p = _turn_room()
    inv = S._custom_potion_inventory_dict(S._validate_custom_item(potion_sample(value=15))[1])
    p["hp"] = 1
    p["bag"] = [dict(inv)]
    asyncio.run(r.handle_use_item("p1", "pocao_teste"))
    check("cura sobe o HP", p["hp"] == min(p["max_hp"], 16))
    check("poção consumida da bolsa", not any(i["id"] == "pocao_teste" for i in p["bag"]))
    # Regeneração
    r, p = _turn_room()
    invr = S._custom_potion_inventory_dict(S._validate_custom_item(
        potion_sample(id="pocao_regen", effect="regeneration", value=10))[1])
    p["bag"] = [dict(invr)]
    pool0 = p.get("potion_regen_pool", 0)
    asyncio.run(r.handle_use_item("p1", "pocao_regen"))
    check("regeneração soma ao pool", p.get("potion_regen_pool", 0) == pool0 + 10)
    # Buff de ataque
    r, p = _turn_room()
    inva = S._custom_potion_inventory_dict(S._validate_custom_item(
        potion_sample(id="pocao_elixir", effect="atk_bonus", value=3))[1])
    p["bag"] = [dict(inva)]
    atk0 = p["atk_bonus"]
    asyncio.run(r.handle_use_item("p1", "pocao_elixir"))
    check("atk_bonus buff aplicado", p["atk_bonus"] == atk0 + 3)

def test_pocao_multidose():
    print("\n[F4] Multi-dose consome uma dose por uso")
    r, p = _turn_room()
    inv = S._custom_potion_inventory_dict(S._validate_custom_item(
        potion_sample(id="pocao_doses", value=8, max_uses=2))[1])
    p["hp"] = 1
    p["bag"] = [dict(inv)]
    asyncio.run(r.handle_use_item("p1", "pocao_doses"))
    check("dose 1: fica na bolsa", any(i["id"] == "pocao_doses" for i in p["bag"]))
    check("dose 1: uses_left = 1", next(i for i in p["bag"] if i["id"] == "pocao_doses")["uses_left"] == 1)
    p["bonus_action_used"] = False   # novo turno (libera a ação bônus)
    asyncio.run(r.handle_use_item("p1", "pocao_doses"))
    check("dose 2: sai da bolsa ao zerar", not any(i["id"] == "pocao_doses" for i in p["bag"]))

def test_validacao_acessorio():
    print("\n[E1] Validacao de anel/bota")
    ok, it = S._validate_custom_item(accessory_sample())
    check("aceita anel valido", ok)
    check("kind = ring", ok and it.get("kind") == "ring")
    check("item_slot = ring", ok and it.get("item_slot") == "ring")
    check("bonuses preservados (maxhp+atk_bonus)",
          ok and it.get("bonuses") == [{"effect": "maxhp", "value": 5}, {"effect": "atk_bonus", "value": 1}])
    check("anel nao tem corrosao", ok and "corrosion_materials" not in it)
    okb, itb = S._validate_custom_item(accessory_sample(id="botas_ferro", item_type="boots",
        emoji="👢", corrosion_materials=["metal"], corrosao_resistente=1,
        corrosao_niveis_penalidade=3, bonuses=[{"effect": "spd", "value": 1}]))
    check("aceita bota", okb and itb.get("kind") == "boots")
    check("bota item_slot = boots", okb and itb.get("item_slot") == "boots")
    check("bota mantem material e N/M", okb and itb.get("corrosion_materials") == ["metal"]
          and itb.get("corrosao_resistente") == 1 and itb.get("corrosao_niveis_penalidade") == 3)
    okr, _ = S._validate_custom_item(accessory_sample(id="ring_str"))
    check("rejeita id nativo (ring_str)", not okr)
    okt, _ = S._validate_custom_item(accessory_sample(item_type="colar"))
    check("rejeita item_type nao suportado", not okt)
    okf, itf = S._validate_custom_item(accessory_sample(bonuses=[{"effect": "atk", "value": 3}]))
    check("filtra efeito atk cru (usar atk_bonus)", okf and itf.get("bonuses") == [])
    oka, ita = S._validate_custom_item(accessory_sample(bonuses=[{"effect": "atk_bonus", "value": 2}]))
    check("aceita atk_bonus", oka and ita.get("bonuses") == [{"effect": "atk_bonus", "value": 2}])

def test_acessorio_equip_efeitos():
    print("\n[E2] Anel aplica/reverte efeitos do motor multi-efeito")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ok, it = S._validate_custom_item(accessory_sample())   # maxhp+5, atk_bonus+1
    inv = S._custom_accessory_inventory_dict(it)
    hp0, atk0 = p["max_hp"], p["atk_bonus"]
    r._apply_gear_effect(p, inv, True)
    check("equipar +5 PV máx", p["max_hp"] == hp0 + 5)
    check("equipar +1 acerto (atk_bonus)", p["atk_bonus"] == atk0 + 1)
    r._apply_gear_effect(p, inv, False)
    check("desequipar reverte PV", p["max_hp"] == hp0)
    check("desequipar reverte acerto", p["atk_bonus"] == atk0)

def test_acessorio_resist():
    print("\n[E3] Anel de resistência entra/sai de resistances")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ok, it = S._validate_custom_item(accessory_sample(id="anel_fogo",
        bonuses=[{"effect": "resist", "type": "fire", "value": 0}]))
    inv = S._custom_accessory_inventory_dict(it)
    r._apply_gear_effect(p, inv, True)
    check("resist fire adicionado", {"type": "fire", "mode": "half"} in p.get("resistances", []))
    r._apply_gear_effect(p, inv, False)
    check("resist fire removido", {"type": "fire", "mode": "half"} not in p.get("resistances", []))

def test_acessorio_botas_corrosao():
    print("\n[E4] Botas custom corroem por material (N/M)")
    S._apply_custom_items([S._validate_custom_item(accessory_sample(id="botas_metal",
        item_type="boots", emoji="👢", corrosion_materials=["metal"],
        corrosao_resistente=0, corrosao_niveis_penalidade=2,
        bonuses=[{"effect": "spd", "value": 1}]))[1]])
    r, p = _corr_setup()
    base = r._moves_base(p)
    p["gear"]["armor"] = None  # isola a corrosão nas botas
    # arma inicial do guerreiro (machado_basico) é metal e corroeria antes das
    # botas na ordem de prioridade (armor→off_hand→weapon→head→boots) — zera
    # também a arma para isolar de fato, como o teste organic (test_corrosao_botas)
    # já fazia sem precisar disso (arma inicial não é madeira).
    p["weapon"] = None
    p["gear"]["boots"] = {"id": "botas_metal", "name": "Botas de Metal",
                          "corrosion_materials": ["metal"],
                          "corrosao_resistente": 0, "corrosao_niveis_penalidade": 2}
    m = {"id": "d", "name": "Dev", "hp": 10, "max_hp": 10}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d4", "T"))
    check("botas corroídas (nível 1)", r._corr(p)["botas_lvl"] == 1)
    check("movimento cai 1 com botas corroídas", r._moves_base(p) == base - 1)
    S._apply_custom_items([])

def test_acessorio_merge():
    print("\n[E5] Merge de acessório no mercador/baús/loot")
    ok, it = S._validate_custom_item(accessory_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "anel_teste" for i in S.SHOP_MERCHANT))
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "anel_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "anel_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo SHOP_MERCHANT intacto", any(i["id"] == "ring_str" for i in S.SHOP_MERCHANT))
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "anel_teste") == 1)
    check("reaplicar nao duplica em LOOT_POOL_PROCEDURAL",
          S.LOOT_POOL_PROCEDURAL.count("anel_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "anel_teste" for i in S.SHOP_MERCHANT))
    check("lista vazia remove de _DUNGEON_ITEM_CATALOG", "anel_teste" not in S._DUNGEON_ITEM_CATALOG)
    check("lista vazia remove de LOOT_POOL_PROCEDURAL", "anel_teste" not in S.LOOT_POOL_PROCEDURAL)
    check("nativo SHOP_MERCHANT sobrevive ao clear", any(i["id"] == "ring_str" for i in S.SHOP_MERCHANT))

def test_validacao_armadura():
    print("\n[A1] Validacao de armadura/escudo")
    ok, it = S._validate_custom_item(armor_sample())
    check("aceita armadura valida", ok)
    check("kind = armor", ok and it.get("kind") == "armor")
    check("ac_bonus preservado", ok and it.get("ac_bonus") == 4)
    check("categoria preservada", ok and it.get("armor_category") == "media")
    check("materiais preservados", ok and it.get("corrosion_materials") == ["metal"])
    check("N/M preservados", ok and it.get("corrosao_resistente") == 0 and it.get("corrosao_niveis_penalidade") == 2)
    check("bonuses preservados", ok and it.get("bonuses") == [{"effect": "maxhp", "value": 5}])
    ok2, it2 = S._validate_custom_item(armor_sample(id="esc_teste", item_type="shield",
        armor_category="media", corrosion_materials=["metal"]))
    check("aceita escudo", ok2 and it2.get("kind") == "shield")
    check("escudo zera categoria", ok2 and it2.get("armor_category") is None)
    check("escudo mantem material", ok2 and it2.get("corrosion_materials") == ["metal"])
    ok3, _ = S._validate_custom_item(armor_sample(armor_category="ultra"))
    check("rejeita categoria invalida", not ok3)
    ok4, it4 = S._validate_custom_item(armor_sample(corrosion_materials=["metal", "trevas"]))
    check("filtra material desconhecido", ok4 and it4.get("corrosion_materials") == ["metal"])
    ok5, it5 = S._validate_custom_item(armor_sample(bonuses=[{"effect": "atk", "value": 3}]))
    check("filtra efeito nao permitido em bonuses", ok5 and it5.get("bonuses") == [])
    okw, _ = S._validate_custom_item(sample())
    check("arma ainda valida", okw)

def test_merge_armadura():
    print("\n[A2] Merge de armadura/escudo")
    arm = S._validate_custom_item(armor_sample(id="cota_m", corrosion_materials=["metal"]))[1]
    org = S._validate_custom_item(armor_sample(id="couro_o", corrosion_materials=["organic"]))[1]
    esc = S._validate_custom_item(armor_sample(id="esc_m", item_type="shield", corrosion_materials=["metal"]))[1]
    S._apply_custom_items([arm, org, esc])
    check("armadura entra em SHOP_ARMORS", any(a["id"] == "cota_m" for a in S.SHOP_ARMORS))
    check("escudo entra em SHOP_ARMORS", any(a["id"] == "esc_m" for a in S.SHOP_ARMORS))
    check("SHOP_ARMORS carrega ac_bonus", next(a for a in S.SHOP_ARMORS if a["id"] == "cota_m")["ac_bonus"] == 4)
    check("metal armadura -> CORROSAO_ARMADURA_METAL", "cota_m" in S.CORROSAO_ARMADURA_METAL)
    check("organic armadura -> CORROSAO_ARMADURA_ORGANICA", "couro_o" in S.CORROSAO_ARMADURA_ORGANICA)
    check("escudo metal -> CORROSAO_ARMADURA_METAL", "esc_m" in S.CORROSAO_ARMADURA_METAL)
    arm2 = S._validate_custom_item(armor_sample(id="cota_bau",
        disponibilidade={"loja": False, "baus": True, "loot_monstro": True}))[1]
    S._apply_custom_items([arm, org, esc, arm2])
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "cota_bau" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "cota_bau" in S.LOOT_POOL_PROCEDURAL)
    check("catalogo de baus e equipavel (item_slot armor + effect def_)",
          S._DUNGEON_ITEM_CATALOG["cota_bau"].get("item_slot") == "armor"
          and S._DUNGEON_ITEM_CATALOG["cota_bau"].get("effect") == "def_")
    S._apply_custom_items([])
    check("cleanup remove de SHOP_ARMORS", not any(a.get("custom") for a in S.SHOP_ARMORS))
    check("cleanup remove de CORROSAO_ARMADURA_METAL", "cota_m" not in S.CORROSAO_ARMADURA_METAL)
    check("cleanup remove de CORROSAO_ARMADURA_ORGANICA", "couro_o" not in S.CORROSAO_ARMADURA_ORGANICA)
    check("cleanup remove cota_bau (catalog-only) de CORROSAO_ARMADURA_METAL",
          "cota_bau" not in S.CORROSAO_ARMADURA_METAL)
    check("base leather intacto em SHOP_ARMORS", any(a["id"] == "leather" for a in S.SHOP_ARMORS))
    check("base leather intacto em CORROSAO_ARMADURA_ORGANICA", "leather" in S.CORROSAO_ARMADURA_ORGANICA)

def test_multi_efeito():
    print("\n[A3] Motor de multi-efeito (bonuses)")
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop; r.send_to = noop
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    hp0, spd0, ac0 = p["max_hp"], p["spd"], p["ac"]
    item = {"id": "x", "name": "X", "item_slot": "armor", "effect": "def_", "value": 3,
            "bonuses": [{"effect": "maxhp", "value": 5}, {"effect": "spd", "value": -1},
                        {"effect": "def_", "value": 1}]}
    r._apply_gear_effect(p, item, True)
    check("def_ primario aplicado (+3 CA)", p["ac"] == ac0 + 3 + 1)  # primario +3, bonus +1
    check("maxhp bonus aplicado (+5)", p["max_hp"] == hp0 + 5)
    check("spd bonus aplicado (-1)", p["spd"] == spd0 - 1)
    r._apply_gear_effect(p, item, False)
    check("desequipar reverte CA", p["ac"] == ac0)
    check("desequipar reverte maxhp", p["max_hp"] == hp0)
    check("desequipar reverte spd", p["spd"] == spd0)

def test_compra_armadura():
    print("\n[A4] Comprar armadura custom preserva campos")
    ok_ct, cota = S._validate_custom_item(armor_sample(id="cota_cmp",
        corrosion_materials=["metal"], bonuses=[{"effect": "maxhp", "value": 5}]))
    S._apply_custom_items([cota])
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True; r.phase = "city"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["gold"] = 9999; p["bag"] = []; p["gear"]["armor"] = None
    orig_stock, tmp_stock = _stock_sandbox()
    try:
        S._sync_custom_item_city_stock(cota, [r.world_location])
        asyncio.run(r.handle_shop_buy("p1", "ferreiro_armor", "cota_cmp"))
        comprada = next((it for it in p["bag"] if it and it.get("id") == "cota_cmp"), None)
        check("armadura foi pra bolsa", comprada is not None)
        check("bolsa preserva bonuses", comprada and comprada.get("bonuses"))
        check("bolsa preserva material", comprada and comprada.get("corrosion_materials") == ["metal"])
        check("bolsa preserva N/M", comprada and comprada.get("corrosao_niveis_penalidade") == 2)
    finally:
        S.CITY_SHOPS_FILE = orig_stock["file"]
        S.CITY_SHOPS.clear(); S.CITY_SHOPS.update(orig_stock["stock"])
        try: os.unlink(tmp_stock)
        except OSError: pass
    S._apply_custom_items([])

def _corr_setup():
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r._devorador_cura = noop
    p = S.make_player("p1", "Victor", "warrior", 0)
    return r, p

def test_corrosao_armadura_nm():
    print("\n[A5] Corrosão: armadura byte-idêntica + escudo + prioridade")
    # (a) armadura base (leather, sem N/M): quebra no 3º nível, penalidade 1,2
    r, p = _corr_setup()
    p["gear"]["armor"] = {"id": "leather", "name": "Couro"}
    m = {"id": "d", "name": "Devorador", "hp": 10, "max_hp": 10}
    for _ in range(2):
        asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_ORGANICA, S.CORROSAO_ARMA_MADEIRA, "1d4", "T"))
    check("armadura viva após 2 níveis", p["gear"]["armor"] is not None)
    check("penalidade de CA = 2 no nível 2", r._corrosao_ca_pen(p) == 2)
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_ORGANICA, S.CORROSAO_ARMA_MADEIRA, "1d4", "T"))
    check("armadura destruída no 3º nível", p["gear"]["armor"] is None)
    # (b) escudo custom com material metal corrói e quebra em N+M+1 (N=1,M=2 → 4)
    S._apply_custom_items([S._validate_custom_item(armor_sample(id="esc_c", item_type="shield",
        corrosion_materials=["metal"], corrosao_resistente=1, corrosao_niveis_penalidade=2))[1]])
    r, p = _corr_setup()
    p["gear"]["off_hand"] = deepcopy(next(a for a in S.SHOP_ARMORS if a["id"] == "esc_c"))
    for _ in range(3):
        asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("escudo vivo após 3 níveis (N=1,M=2)", p["gear"]["off_hand"] is not None)
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("escudo destruído no 4º nível", p["gear"]["off_hand"] is None)
    # (b2) penalidade de CA do escudo PERSISTE após a destruição, com N/M corretos
    check("escudo destruído ainda penaliza CA (persiste)", r._corrosao_ca_pen(p) == 2)
    # (c) prioridade: armadura (metal) corrói antes do escudo
    r, p = _corr_setup()
    p["gear"]["armor"] = {"id": "chainmail", "name": "Cota"}
    p["gear"]["off_hand"] = {"id": "esc_c", "name": "Esc", "kind": "shield", "corrosion_materials": ["metal"]}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("prioridade: armadura corroída antes do escudo",
          r._corr(p)["armadura_lvl"] == 1 and r._corr(p).get("escudo_lvl", 0) == 0)
    # (d) custom armor com M=4 mantém a penalidade após destruição
    S._apply_custom_items([S._validate_custom_item(armor_sample(id="cota_m4",
        corrosion_materials=["metal"], corrosao_resistente=0, corrosao_niveis_penalidade=4))[1]])
    r, p = _corr_setup()
    p["gear"]["armor"] = deepcopy(next(a for a in S.SHOP_ARMORS if a["id"] == "cota_m4"))
    for _ in range(5):
        asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("cota_m4 destruída (5º nível)", p["gear"]["armor"] is None)
    check("cota_m4 penalidade persiste em M=4", r._corrosao_ca_pen(p) == 4)
    # (e) escudo base (escudo_p) corrói pelo Devorador de Metal
    r, p = _corr_setup()
    p["gear"]["off_hand"] = {"id": "escudo_p", "name": "Escudo Pequeno", "kind": "shield"}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("escudo base corrói pelo metal", r._corr(p)["escudo_lvl"] == 1)
    S._apply_custom_items([])

def test_corrosao_botas():
    print("\n[A6] Botas custom corroem e penalizam velocidade")
    S._apply_custom_items([S._validate_custom_item(armor_sample(id="botas_c", item_type="armor",
        armor_category="leve", corrosion_materials=["organic"],
        bonuses=[{"effect": "spd", "value": 1}]))[1]])
    r, p = _corr_setup()
    base = r._moves_base(p)
    p["gear"]["armor"] = None  # isola a corrosão nas botas (armadura inicial é organic e tem prioridade)
    p["gear"]["boots"] = {"id": "botas_c", "name": "Botas", "corrosion_materials": ["organic"]}
    m = {"id": "d", "name": "Dev", "hp": 10, "max_hp": 10}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_ORGANICA, S.CORROSAO_ARMA_MADEIRA, "1d4", "T"))
    check("botas corroídas (nível 1)", r._corr(p)["botas_lvl"] == 1)
    check("movimento cai 1 com botas corroídas", r._moves_base(p) == base - 1)
    S._apply_custom_items([])

def _gear_room():
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop; r.send_to = noop
    return r

def _bonus_item(effect, value):
    return {"id": "x", "name": "X", "item_slot": "armor", "effect": "def_", "value": 0,
            "bonuses": [{"effect": effect, "value": value}]}

def test_atributo_forca():
    print("\n[B1] Bônus de Força (acerto por classe + simetria)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    atk0, str0 = p["atk_bonus"], p["str_"]
    it = _bonus_item("str_", 2)
    r._apply_gear_effect(p, it, True)
    check("str_ sobe 2", p["str_"] == str0 + 2)
    check("guerreiro: acerto sobe Δmod (+1)", p["atk_bonus"] == atk0 + 1)
    r._apply_gear_effect(p, it, False)
    check("desequipar reverte str_", p["str_"] == str0)
    check("desequipar reverte acerto", p["atk_bonus"] == atk0)
    pr = S.make_player("p2", "Luccas", "rogue", 0)
    atkr = pr["atk_bonus"]
    r._apply_gear_effect(pr, it, True)
    check("ladino: Força não muda o acerto", pr["atk_bonus"] == atkr)
    check("ladino: str_ ainda sobe (dano lê ao vivo)", pr["str_"] > 0)
    r._apply_gear_effect(pr, it, False)

def test_atributo_destreza():
    print("\n[B2] Bônus de Destreza (CA/Reflexos/acerto)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ac0, acb0, ref0, atk0 = p["ac"], p["ac_base"], p["ref_"], p["atk_bonus"]
    it = _bonus_item("dex", 2)
    r._apply_gear_effect(p, it, True)
    check("CA sobe Δmod (+1)", p["ac"] == ac0 + 1 and p["ac_base"] == acb0 + 1)
    check("Reflexos sobe (+1)", p["ref_"] == ref0 + 1)
    check("guerreiro: Destreza não muda o acerto", p["atk_bonus"] == atk0)
    r._apply_gear_effect(p, it, False)
    check("reverte CA/Reflexos", p["ac"] == ac0 and p["ref_"] == ref0)
    pr = S.make_player("p2", "Luccas", "rogue", 0)
    atkr = pr["atk_bonus"]
    r._apply_gear_effect(pr, it, True)
    check("ladino: Destreza sobe o acerto (+1)", pr["atk_bonus"] == atkr + 1)
    r._apply_gear_effect(pr, it, False)

def test_atributo_con_int():
    print("\n[B3] Constituição (PV+Fortitude) e Inteligência (Vontade)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    hp0, max0, fort0, will0 = p["hp"], p["max_hp"], p["fort"], p["will"]
    itc = _bonus_item("con_", 2)
    r._apply_gear_effect(p, itc, True)
    dcb = S.get_bonus_constituicao(16) - S.get_bonus_constituicao(14)
    check("max_hp sobe Δcb × nível", p["max_hp"] == max0 + dcb * p["level"])
    check("Fortitude sobe Δcb", p["fort"] == fort0 + dcb)
    check("HP atual sobe no equipar", p["hp"] == min(p["max_hp"], hp0 + dcb * p["level"]))
    r._apply_gear_effect(p, itc, False)
    check("reverte max_hp", p["max_hp"] == max0)
    check("reverte Fortitude", p["fort"] == fort0)
    iti = _bonus_item("int_", 2)
    r._apply_gear_effect(p, iti, True)
    check("Vontade sobe Δmod (+1)", p["will"] == will0 + 1)
    r._apply_gear_effect(p, iti, False)
    check("reverte Vontade", p["will"] == will0)

def test_atributo_empilha_e_aovivo():
    print("\n[B4] Empilhamento simétrico + visão/iniciativa ao vivo")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    atk0, str0 = p["atk_bonus"], p["str_"]
    a = _bonus_item("str_", 2); b = dict(_bonus_item("str_", 2), id="y")
    r._apply_gear_effect(p, a, True); r._apply_gear_effect(p, b, True)
    check("dois +2 FOR: str_ +4", p["str_"] == str0 + 4)
    r._apply_gear_effect(p, a, False); r._apply_gear_effect(p, b, False)
    check("remover ambos volta str_ ao inicial", p["str_"] == str0)
    check("remover ambos volta acerto ao inicial", p["atk_bonus"] == atk0)
    p2 = S.make_player("p2", "Luccas", "rogue", 0); r.players["p2"] = p2
    vis0 = r._get_raio_visao(p2); ini0 = r.initiative_value(p2)
    r._apply_gear_effect(p2, _bonus_item("dex", 2), True)
    check("visão aumenta com +Destreza (ao vivo)", r._get_raio_visao(p2) >= vis0)
    check("iniciativa aumenta com +Destreza (ao vivo)", r.initiative_value(p2) == ini0 + 2)

def test_validacao_bonus_atributo():
    print("\n[B5] Validação aceita bônus de atributo")
    ok, it = S._validate_custom_item(armor_sample(id="cota_atr",
        bonuses=[{"effect": "str_", "value": 2}, {"effect": "int_", "value": 1}]))
    check("bonuses de atributo preservados", ok and it.get("bonuses") ==
          [{"effect": "str_", "value": 2}, {"effect": "int_", "value": 1}])
    ok2, it2 = S._validate_custom_item(armor_sample(id="cota_bad",
        bonuses=[{"effect": "atk", "value": 3}]))
    check("efeito fora do allowlist ainda é filtrado", ok2 and it2.get("bonuses") == [])

def _resist_item(dtype, value):
    return {"id": "r", "name": "R", "item_slot": "armor", "effect": "def_", "value": 0,
            "bonuses": [{"effect": "resist", "type": dtype, "value": value}]}

def test_resistencia_aplica():
    print("\n[C1] Resistência: aplica/remove entrada + efeito no dano")
    r = _gear_room(); r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    it = _resist_item("fire", 0)
    r._apply_gear_effect(p, it, True)
    check("equipar adiciona resistência de metade",
          {"type": "fire", "mode": "half"} in p.get("resistances", []))
    check("dano de fogo cai pela metade", r._apply_damage_types(10, ["fire"], p) == 5)
    check("outro tipo não é reduzido", r._apply_damage_types(10, ["cold"], p) == 10)
    r._apply_gear_effect(p, it, False)
    check("desequipar remove a resistência", {"type": "fire", "mode": "half"} not in p.get("resistances", []))
    check("sem resistência, fogo volta ao cheio", r._apply_damage_types(10, ["fire"], p) == 10)
    it3 = _resist_item("cold", 3)
    r._apply_gear_effect(p, it3, True)
    check("redução fixa entra como reduction", {"type": "cold", "reduction": 3} in p.get("resistances", []))
    check("dano de frio -3", r._apply_damage_types(10, ["cold"], p) == 7)
    r._apply_gear_effect(p, it3, False)

def test_resistencia_empilha():
    print("\n[C2] Resistência: empilhamento")
    r = _gear_room(); r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    it = _resist_item("fire", 0)
    r._apply_gear_effect(p, it, True); r._apply_gear_effect(p, it, True)
    check("dois itens = duas entradas",
          sum(1 for e in p["resistances"] if e == {"type": "fire", "mode": "half"}) == 2)
    r._apply_gear_effect(p, it, False)
    check("remover um deixa uma",
          sum(1 for e in p["resistances"] if e == {"type": "fire", "mode": "half"}) == 1)
    r._apply_gear_effect(p, it, False)
    r._apply_gear_effect(p, _resist_item("trevas", 0), True)
    check("tipo desconhecido não entra em resistances",
          not any(e.get("type") == "trevas" for e in p.get("resistances", [])))

def test_validacao_resist():
    print("\n[C3] Validação de bônus resist (preserva type)")
    ok, it = S._validate_custom_item(armor_sample(id="cota_res",
        bonuses=[{"effect": "resist", "type": "fire", "value": 0},
                 {"effect": "resist", "type": "cold", "value": 3}]))
    check("resist preservado com type e value", ok and it.get("bonuses") ==
          [{"effect": "resist", "type": "fire", "value": 0},
           {"effect": "resist", "type": "cold", "value": 3}])
    ok2, it2 = S._validate_custom_item(armor_sample(id="cota_res_bad",
        bonuses=[{"effect": "resist", "type": "trevas", "value": 0}]))
    check("resist com type inválido é descartado", ok2 and it2.get("bonuses") == [])
    ok3, it3 = S._validate_custom_item(armor_sample(id="cota_res_semtipo",
        bonuses=[{"effect": "resist", "value": 0}]))
    check("resist sem type é descartado", ok3 and it3.get("bonuses") == [])
    ok4, it4 = S._validate_custom_item(armor_sample(id="cota_spd",
        bonuses=[{"effect": "spd", "value": -1}]))
    check("bônus escalar segue {effect,value}", ok4 and it4.get("bonuses") == [{"effect": "spd", "value": -1}])

def test_iniciativa_bonus():
    print("\n[D1] Bônus de iniciativa (escalar + validação)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ini0 = r.initiative_value(p)
    it = {"id": "i", "name": "I", "item_slot": "armor", "effect": "def_", "value": 0,
          "bonuses": [{"effect": "initiative", "value": 3}]}
    r._apply_gear_effect(p, it, True)
    check("equipar +3 iniciativa", r.initiative_value(p) == ini0 + 3)
    r._apply_gear_effect(p, it, True)
    check("empilhar dois = +6", r.initiative_value(p) == ini0 + 6)
    r._apply_gear_effect(p, it, False)
    check("remover um = +3", r.initiative_value(p) == ini0 + 3)
    r._apply_gear_effect(p, it, False)
    check("remover ambos volta ao inicial", r.initiative_value(p) == ini0)
    itn = {"id": "j", "name": "J", "item_slot": "armor", "effect": "def_", "value": 0,
           "bonuses": [{"effect": "initiative", "value": -2}]}
    r._apply_gear_effect(p, itn, True)
    check("valor negativo reduz", r.initiative_value(p) == ini0 - 2)
    r._apply_gear_effect(p, itn, False)
    ok, itv = S._validate_custom_item(armor_sample(id="cota_ini",
        bonuses=[{"effect": "initiative", "value": 3}]))
    check("validação preserva initiative", ok and itv.get("bonuses") == [{"effect": "initiative", "value": 3}])

def test_visao_bonus():
    print("\n[M1] Bônus de visão (escalar + validação)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    vis0 = r._get_raio_visao(p)
    it = {"id": "v", "name": "V", "item_slot": "armor", "effect": "def_", "value": 0,
          "bonuses": [{"effect": "vision", "value": 2}]}
    r._apply_gear_effect(p, it, True)
    check("equipar +2 visão", r._get_raio_visao(p) == vis0 + 2)
    r._apply_gear_effect(p, it, True)
    check("empilhar dois = +4", r._get_raio_visao(p) == vis0 + 4)
    r._apply_gear_effect(p, it, False)
    check("remover um = +2", r._get_raio_visao(p) == vis0 + 2)
    r._apply_gear_effect(p, it, False)
    check("remover ambos volta ao inicial", r._get_raio_visao(p) == vis0)
    itn = {"id": "w", "name": "W", "item_slot": "armor", "effect": "def_", "value": 0,
           "bonuses": [{"effect": "vision", "value": -2}]}
    r._apply_gear_effect(p, itn, True)
    check("valor negativo reduz", r._get_raio_visao(p) == max(1, vis0 - 2))
    r._apply_gear_effect(p, itn, False)
    itz = {"id": "z", "name": "Z", "item_slot": "armor", "effect": "def_", "value": 0,
           "bonuses": [{"effect": "vision", "value": -99}]}
    r._apply_gear_effect(p, itz, True)
    check("raio nunca desce abaixo de 1", r._get_raio_visao(p) == 1)
    r._apply_gear_effect(p, itz, False)
    check("desfazer o piso volta ao inicial", r._get_raio_visao(p) == vis0)
    ok, itv = S._validate_custom_item(armor_sample(id="cota_visao",
        bonuses=[{"effect": "vision", "value": 2}]))
    check("validação preserva vision", ok and itv.get("bonuses") == [{"effect": "vision", "value": 2}])
    ok2, ita = S._validate_custom_item(accessory_sample(id="anel_visao",
        bonuses=[{"effect": "vision", "value": 1}]))
    check("aceito também em acessório", ok2 and ita.get("bonuses") == [{"effect": "vision", "value": 1}])

def _item_com_habilidade(aid, **over):
    """Peça de gear mínima que concede uma habilidade."""
    base = {"id": "peca_hab", "name": "Peça Encantada", "granted_ability": aid}
    base.update(over); return base

def test_habilidade_concedida_helper():
    print("\n[I1] _habilidades_concedidas varre o gear equipado")
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem itens: conjunto vazio", S._habilidades_concedidas(p) == set())
    p["gear"]["weapon"] = _item_com_habilidade("guild_brutalidade")
    check("coleta da arma", S._habilidades_concedidas(p) == {"guild_brutalidade"})
    p["gear"]["ring1"] = _item_com_habilidade("guild_guerreiro_mira_3", id="anel_x")
    check("coleta de vários slots",
          S._habilidades_concedidas(p) == {"guild_brutalidade", "guild_guerreiro_mira_3"})
    p["gear"]["armor"] = {"id": "sem_hab", "name": "Cota"}
    check("ignora item sem granted_ability",
          S._habilidades_concedidas(p) == {"guild_brutalidade", "guild_guerreiro_mira_3"})
    p["gear"]["boots"] = _item_com_habilidade(None, id="bota_x")
    check("ignora granted_ability vazio",
          S._habilidades_concedidas(p) == {"guild_brutalidade", "guild_guerreiro_mira_3"})
    check("gear ausente não quebra", S._habilidades_concedidas({}) == set())

def test_portoes_concedidos():
    print("\n[I2] Portões aceitam habilidade concedida por item")
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem item: técnica não equipada", not S.tem_tecnica_equipada(p, "brutalidade"))
    check("sem item: sem especialização", not S.tem_espec(p, "guerreiro_mira_3"))
    p["gear"]["weapon"] = _item_com_habilidade("guild_brutalidade")
    check("com item: técnica liberada", S.tem_tecnica_equipada(p, "brutalidade"))
    check("item de técnica não libera especialização", not S.tem_espec(p, "guerreiro_mira_3"))
    p["gear"]["ring1"] = _item_com_habilidade("guild_guerreiro_mira_3", id="anel_x")
    check("com item: especialização liberada", S.tem_espec(p, "guerreiro_mira_3"))
    p["gear"]["weapon"] = None
    check("desequipar remove a técnica", not S.tem_tecnica_equipada(p, "brutalidade"))
    check("a outra peça continua valendo", S.tem_espec(p, "guerreiro_mira_3"))

def test_tecnica_concedida_uso():
    print("\n[I3] Técnica concedida por item é usável (efeito+custo+recarga)")
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["gear"]["weapon"] = _item_com_habilidade("guild_brutalidade")
    p["fome"], p["sede"] = 10, 10
    asyncio.run(r.handle_usar_tecnica("p1", "brutalidade"))
    # Brutalidade é `buff_turno`: fica ARMADA (technique_pending) — custo/recarga só
    # entram quando o ataque que ela modifica de fato acontece
    # (`_consumir_tecnica_apos_efeito`, espelhando o mesmo comportamento pra quem
    # possui a técnica via Guilda normal — nada muda por vir de um item).
    check("efeito aplicado (+2 dano de arma)", p.get("tecnica_buff_dano_arma") == 2)
    check("armada mas ainda sem custo", p["fome"] == 10 and p["sede"] == 10)
    check("ainda sem recarga (não consumida)", r.tecnica_restante(p, "brutalidade") == 0)
    check("marcada como pendente", p.get("technique_pending", {}).get("brutalidade") is True)
    consumida = r._consumir_tecnica_apos_efeito(p, "brutalidade")
    check("consumida ao modificar o ataque", consumida)
    check("custo debitado", p["fome"] < 10 and p["sede"] < 10)
    check("entrou em recarga", r.tecnica_restante(p, "brutalidade") > 0)
    p["tecnica_buff_dano_arma"] = 0
    asyncio.run(r.handle_usar_tecnica("p1", "brutalidade"))
    check("2ª ativação recusada pela recarga", p.get("tecnica_buff_dano_arma") == 0)

def test_espec_concedida_efeito():
    print("\n[I4] Especialização concedida altera o efeito real")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem item: Mira III não dá bônus", r._mira_dano_bonus(p) == 0)
    p["gear"]["ring1"] = _item_com_habilidade("guild_guerreiro_mira_3", id="anel_x")
    check("com item: Mira III dá +2 de dano", r._mira_dano_bonus(p) == 2)
    p["gear"]["ring1"] = None
    check("desequipar volta a 0", r._mira_dano_bonus(p) == 0)

def _turn_room_hero(cls_id="warrior"):
    """Sala com um herói da classe dada, turno ativo (para handlers de habilidade)."""
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Heroi", cls_id, 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["fome"], p["sede"] = 10, 10
    return r, p

def test_habilidades_heroi_concedidas():
    print("\n[I5] Amostra de habilidades de herói concedidas por item")
    # Detectar Armadilhas (ladino) num guerreiro
    r, p = _turn_room_hero("warrior")
    asyncio.run(r.handle_detectar_armadilhas("p1", {}))
    check("sem item: detectar recusado", not p.get("detectar_ativo"))
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    asyncio.run(r.handle_detectar_armadilhas("p1", {}))
    check("com item: detectar ativado", p.get("detectar_ativo") is True)
    # Esconder nas Sombras (ladino) num clérigo
    r2, p2 = _turn_room_hero("cleric")
    asyncio.run(r2.handle_esconder_sombras("p1", {}))
    check("sem item: esconder recusado", not p2.get("invisivel_sombras"))
    p2["gear"]["boots"] = _item_com_habilidade("hero_rogue_esconder_sombras", id="bota_e")
    asyncio.run(r2.handle_esconder_sombras("p1", {}))
    check("com item: esconder tentado (ativou ou gastou a ação bônus)",
          p2.get("invisivel_sombras") or p2.get("bonus_action_used"))
    # Imposição das Mãos (paladino) num guerreiro, curando um aliado adjacente
    r3, p3 = _turn_room_hero("warrior")
    aliado = S.make_player("p2", "Aliado", "cleric", 1)
    r3.players["p2"] = aliado
    p3["pos"] = [1, 1]; aliado["pos"] = [2, 1]
    aliado["hp"] = 1
    asyncio.run(r3.handle_imposicao_maos("p1", {"target_id": "p2"}))
    check("sem item: imposição recusada", aliado["hp"] == 1)
    p3["gear"]["armor"] = _item_com_habilidade("hero_paladin_imposicao_maos", id="cota_i")
    asyncio.run(r3.handle_imposicao_maos("p1", {"target_id": "p2"}))
    check("com item: aliado curado", aliado["hp"] > 1)

def test_mensagens_sem_richard():
    print("\n[I5b] Mensagens da Imposição não citam Richard")
    r, p = _turn_room_hero("warrior")
    erros = []
    async def se(pid, msg): erros.append(msg.get("msg", ""))
    r.send_to = se
    p["gear"]["armor"] = _item_com_habilidade("hero_paladin_imposicao_maos", id="cota_i")
    asyncio.run(r.handle_imposicao_maos("p1", {"target_id": "p1"}))   # curar a si mesmo
    check("erro de auto-cura não cita Richard",
          erros and all("Richard" not in e for e in erros))

def test_granted_hero_skills_payload():
    print("\n[I5c] push_state expõe as habilidades de herói concedidas")
    p = S.make_player("p1", "Victor", "warrior", 0)
    r = _gear_room()
    check("sem item: lista vazia", r._granted_hero_skills(p) == [])
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    skills = r._granted_hero_skills(p)
    check("com item: 1 habilidade", len(skills) == 1)
    check("traz o id real da skill", skills and skills[0].get("id") == "detectar_armadilhas")
    check("marca a classe de origem", skills and skills[0].get("granted_origem") == "rogue")
    pr = S.make_player("p2", "Luccas", "rogue", 1)
    pr["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    check("ladino não duplica a própria habilidade", r._granted_hero_skills(pr) == [])

def test_validacao_granted_ability():
    print("\n[I6] Validação de granted_ability")
    check("aceita técnica da Guilda", S._granted_ability_valida("guild_brutalidade"))
    check("aceita especialização", S._granted_ability_valida("guild_guerreiro_mira_3"))
    check("aceita habilidade de herói da amostra",
          S._granted_ability_valida("hero_rogue_detectar_armadilhas"))
    check("rejeita id desconhecido", not S._granted_ability_valida("guild_nao_existe"))
    check("rejeita herói fora da amostra",
          not S._granted_ability_valida("hero_ranger_tiro_certeiro"))
    check("rejeita None", not S._granted_ability_valida(None))
    ok, it = S._validate_custom_item(sample(id="arma_hab", granted_ability="guild_brutalidade"))
    check("arma preserva id suportado", ok and it.get("granted_ability") == "guild_brutalidade")
    ok2, it2 = S._validate_custom_item(sample(id="arma_hab2", granted_ability="xpto"))
    check("arma descarta id nao suportado", ok2 and it2.get("granted_ability") is None)
    ok3, it3 = S._validate_custom_item(armor_sample(id="cota_hab", granted_ability="guild_brutalidade"))
    check("armadura preserva id suportado", ok3 and it3.get("granted_ability") == "guild_brutalidade")
    ok4, it4 = S._validate_custom_item(armor_sample(id="cota_hab2", granted_ability="xpto"))
    check("armadura descarta id nao suportado", ok4 and it4.get("granted_ability") is None)
    ok5, it5 = S._validate_custom_item(accessory_sample(id="anel_hab",
        granted_ability="hero_paladin_imposicao_maos"))
    check("acessorio preserva id suportado",
          ok5 and it5.get("granted_ability") == "hero_paladin_imposicao_maos")
    ok6, it6 = S._validate_custom_item(accessory_sample(id="anel_hab2", granted_ability="xpto"))
    check("acessorio descarta id nao suportado", ok6 and it6.get("granted_ability") is None)

def test_helpers_hab_heroi():
    print("\n[J0] Helpers de habilidade de herói")
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("classe dona passa sem item",
          S._pode_hab_heroi(S.make_player("p2", "L", "cleric", 1), "cleric", "hero_cleric_cura"))
    check("outra classe sem item: não", not S._pode_hab_heroi(p, "cleric", "hero_cleric_cura"))
    p["gear"]["ring1"] = _item_com_habilidade("hero_cleric_cura", id="anel_c")
    check("outra classe com item: sim", S._pode_hab_heroi(p, "cleric", "hero_cleric_cura"))
    check("item de uma não libera outra",
          not S._pode_hab_heroi(p, "cleric", "hero_cleric_ressurreicao"))
    aids = {"hero_rogue_detectar_armadilhas", "hero_rogue_esconder_sombras"}
    check("conjunto: sem nenhuma concedida", not S._tem_alguma_hab_heroi(p, "rogue", aids))
    p["gear"]["boots"] = _item_com_habilidade("hero_rogue_esconder_sombras", id="bota_s")
    check("conjunto: com uma concedida", S._tem_alguma_hab_heroi(p, "rogue", aids))
    check("conjunto: classe dona passa",
          S._tem_alguma_hab_heroi(S.make_player("p3", "L", "rogue", 2), "rogue", aids))

def test_mapa_14_habilidades():
    print("\n[J0b] Mapa GRANTED_HERO_SKILLS com 14 habilidades")
    m = S.GameRoom.GRANTED_HERO_SKILLS
    check("14 entradas", len(m) == 14)
    esperados = {
        "hero_rogue_detectar_armadilhas", "hero_rogue_esconder_sombras",
        "hero_paladin_imposicao_maos",
        "hero_cleric_cura", "hero_cleric_cura_area", "hero_cleric_purificacao",
        "hero_cleric_ressurreicao",
        "hero_rogue_criar_armadilha", "hero_rogue_veneno_rapido",
        "hero_paladin_golpe_sagrado", "hero_paladin_protetor",
        "hero_paladin_regeneracao_divina", "hero_paladin_guerreiro_luz",
        "hero_bard_provocacao",
    }
    check("ids esperados", set(m.keys()) == esperados)
    check("todos validam", all(S._granted_ability_valida(a) for a in esperados))
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    p["gear"]["ring1"] = _item_com_habilidade("hero_cleric_cura", id="anel_c")
    sk = r._granted_hero_skills(p)
    check("payload traz a skill real de cura", len(sk) == 1 and sk[0].get("id") == "cura")
    check("payload marca a origem", sk and sk[0].get("granted_origem") == "cleric")

def test_hab_clerigo_concedida():
    print("\n[J1] Milagres do clérigo concedidos por item")
    # Cura: guerreiro cura um aliado ferido
    r, p = _turn_room_hero("warrior")
    aliado = S.make_player("p2", "Aliado", "rogue", 1)
    r.players["p2"] = aliado
    p["pos"] = [1, 1]; aliado["pos"] = [2, 1]; aliado["hp"] = 1
    asyncio.run(r.handle_cura("p1", {"target_id": "p2", "num_dados": 1}))
    check("sem item: cura recusada", aliado["hp"] == 1)
    p["gear"]["ring1"] = _item_com_habilidade("hero_cleric_cura", id="anel_c")
    asyncio.run(r.handle_cura("p1", {"target_id": "p2", "num_dados": 1}))
    check("com item: aliado curado", aliado["hp"] > 1)
    # Purificação: remove veneno de um aliado adjacente
    r2, p2 = _turn_room_hero("warrior")
    al2 = S.make_player("p2", "Aliado", "rogue", 1)
    r2.players["p2"] = al2
    p2["pos"] = [1, 1]; al2["pos"] = [2, 1]
    al2["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1,
                              "duracao": 3, "save": "fortitude", "dificuldade": 10}]
    asyncio.run(r2.handle_purificacao("p1", {"tipo": "veneno", "target_id": "p2"}))
    check("sem item: purificação recusada", len(al2.get("efeitos_veneno", [])) == 1)
    p2["gear"]["armor"] = _item_com_habilidade("hero_cleric_purificacao", id="cota_p")
    asyncio.run(r2.handle_purificacao("p1", {"tipo": "veneno", "target_id": "p2"}))
    check("com item: veneno removido", not al2.get("efeitos_veneno"))
    # Ressurreição: revive um aliado morto adjacente
    r3, p3 = _turn_room_hero("warrior")
    al3 = S.make_player("p2", "Morto", "rogue", 1)
    r3.players["p2"] = al3
    p3["pos"] = [1, 1]; al3["pos"] = [2, 1]
    al3["alive"] = False; al3["hp"] = 0
    p3["fome"], p3["sede"] = 30, 30
    asyncio.run(r3.handle_ressurreicao("p1", {"target_id": "p2"}))
    check("sem item: ressurreição recusada", al3["alive"] is False)
    p3["gear"]["ring2"] = _item_com_habilidade("hero_cleric_ressurreicao", id="anel_r")
    asyncio.run(r3.handle_ressurreicao("p1", {"target_id": "p2"}))
    check("com item: aliado revivido", al3["alive"] is True)
    # Cura em Área: aceita a chamada com o item (sem erro de classe)
    r4, p4 = _turn_room_hero("warrior")
    al4 = S.make_player("p2", "Aliado", "rogue", 1)
    r4.players["p2"] = al4
    p4["pos"] = [1, 1]; al4["pos"] = [2, 1]; al4["hp"] = 1
    p4["gear"]["boots"] = _item_com_habilidade("hero_cleric_cura_area", id="bota_ca")
    asyncio.run(r4.handle_cura_area("p1", {"num_dados": 1}))
    check("com item: cura em área curou alguém", al4["hp"] > 1 or p4["hp"] == p4["max_hp"])

def test_hab_ladino_concedida():
    print("\n[J2] Habilidades do ladino concedidas por item")
    # Criar armadilha (buraco é sempre liberado, sem fórmula)
    r, p = _turn_room_hero("warrior")
    r.tiles = [[S.FLOOR for _ in range(r.map_w)] for _ in range(r.map_h)]
    p["pos"] = [3, 3]
    n0 = len(r.armadilhas)
    asyncio.run(r.handle_criar_armadilha("p1", {"tipo": "buraco"}))
    check("sem item: criar armadilha recusado", len(r.armadilhas) == n0)
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_criar_armadilha", id="anel_a")
    asyncio.run(r.handle_criar_armadilha("p1", {"tipo": "buraco"}))
    check("com item: armadilha criada", len(r.armadilhas) == n0 + 1)
    # Veneno rápido: unta a arma equipada
    r2, p2 = _turn_room_hero("warrior")
    p2["weapon"] = {"id": "wt", "name": "Lâmina", "die": "1d8", "stat": "str_",
                    "categoria": "cortante", "poison_slots": []}
    p2["bag"] = [{"id": "veneno_aranha_sombria", "name": "Veneno", "emoji": "🕷️",
                  "item_slot": "bag", "effect": "coat_poison",
                  "veneno_id": "veneno_aranha_sombria"}]
    asyncio.run(r2.handle_veneno_rapido("p1", {"veneno_id": "veneno_aranha_sombria"}))
    check("sem item: veneno rápido recusado", r2._weapon_poison_slots(p2) == [])
    p2["gear"]["boots"] = _item_com_habilidade("hero_rogue_veneno_rapido", id="bota_v")
    asyncio.run(r2.handle_veneno_rapido("p1", {"veneno_id": "veneno_aranha_sombria"}))
    check("com item: arma untada", r2._weapon_poison_slots(p2) != [])

def test_hab_paladino_concedida():
    print("\n[J3] Sustentadas do paladino concedidas por item")
    # Golpe Sagrado: ativa e desativa
    r, p = _turn_room_hero("warrior")
    asyncio.run(r.handle_golpe_sagrado("p1"))
    check("sem item: golpe sagrado recusado", not p.get("golpe_sagrado_ativo"))
    p["gear"]["weapon"] = _item_com_habilidade("hero_paladin_golpe_sagrado", id="esp_g")
    asyncio.run(r.handle_golpe_sagrado("p1"))
    check("com item: golpe sagrado ativo", p.get("golpe_sagrado_ativo") is True)
    asyncio.run(r.handle_desativar_golpe_sagrado("p1"))
    check("com item: golpe sagrado desativado", not p.get("golpe_sagrado_ativo"))
    # Protetor: ativa e desativa (alvo aliado)
    r2, p2 = _turn_room_hero("warrior")
    al = S.make_player("p2", "Aliado", "rogue", 1)
    r2.players["p2"] = al
    p2["pos"] = [1, 1]; al["pos"] = [2, 1]
    asyncio.run(r2.handle_protetor("p1", {"target_id": "p2"}))
    check("sem item: protetor recusado", not p2.get("protetor_ativo"))
    p2["gear"]["armor"] = _item_com_habilidade("hero_paladin_protetor", id="cota_pr")
    asyncio.run(r2.handle_protetor("p1", {"target_id": "p2"}))
    check("com item: protetor ativo", p2.get("protetor_ativo") is True)
    asyncio.run(r2.handle_desativar_protetor("p1"))
    check("com item: protetor desativado", not p2.get("protetor_ativo"))
    # Ação livre: conceder UMA não libera a OUTRA
    r3, p3 = _turn_room_hero("warrior")
    p3["hp"] = max(1, p3["max_hp"] - 5)
    p3["gear"]["ring1"] = _item_com_habilidade("hero_paladin_regeneracao_divina", id="anel_rg")
    asyncio.run(r3.handle_acao_livre_richard("p1", {"habilidade_id": "regeneracao_divina"}))
    check("com item: regeneração ativa", p3.get("regeneracao_ativa") is True)
    asyncio.run(r3.handle_acao_livre_richard("p1", {"habilidade_id": "guerreiro_luz"}))
    check("item de regeneração NÃO libera guerreiro da luz",
          not p3.get("guerreiro_luz_ativo") and not p3.get("gdl_ativo"))

def test_hab_bardo_concedida():
    print("\n[J4] Provocação concedida por item")
    r, p = _room_com_alvo()
    p["class_id"] = "warrior"
    m = r.monsters["m1"]
    asyncio.run(r.handle_provocacao("p1", {"target_id": "m1"}))
    check("sem item: provocação recusada", not m.get("provocado_por"))
    p["gear"]["ring1"] = _item_com_habilidade("hero_bard_provocacao", id="anel_pv")
    asyncio.run(r.handle_provocacao("p1", {"target_id": "m1"}))
    check("com item: monstro provocado", m.get("provocado_por") == "p1")
    check("_provocador reconhece o não-bardo", r._provocador(m) is not None)

def test_upkeep_habilidade_concedida():
    print("\n[J5] Upkeep cobra manutenção de habilidade concedida (fix da Fase I)")
    # Ladino: Detectar Armadilhas concedida a um guerreiro passa a custar sede
    r, p = _turn_room_hero("warrior")
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    asyncio.run(r.handle_detectar_armadilhas("p1", {}))
    check("detectar ativo", p.get("detectar_ativo") is True)
    sede0 = p["sede"]
    asyncio.run(r._processar_inicio_turno_luccas(p))
    check("upkeep do ladino cobrado", p["sede"] < sede0)
    # Paladino: Regeneração Divina concedida a um guerreiro tica no upkeep
    r2, p2 = _turn_room_hero("warrior")
    p2["gear"]["ring1"] = _item_com_habilidade("hero_paladin_regeneracao_divina", id="anel_rg")
    p2["hp"] = max(1, p2["max_hp"] - 5)
    asyncio.run(r2.handle_acao_livre_richard("p1", {"habilidade_id": "regeneracao_divina"}))
    hp0 = p2["hp"]
    asyncio.run(r2._processar_manutencao_richard(p2))
    check("upkeep do paladino rodou (curou ou cobrou)",
          p2["hp"] != hp0 or p2["fome"] < 10 or p2["sede"] < 10)

def test_sincronia_editor_servidor():
    print("\n[J6] Lista do editor em sincronia com o servidor")
    import re, os
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "tools", "editor_items_editor.js")
    src = open(caminho, encoding="utf-8").read()
    bloco = re.search(r"GRANTED_HERO_IDS\s*=\s*\[(.*?)\]", src, re.S)
    check("GRANTED_HERO_IDS encontrado no editor", bool(bloco))
    ids_js = set(re.findall(r'"([^"]+)"', bloco.group(1))) if bloco else set()
    ids_py = set(S.GameRoom.GRANTED_HERO_SKILLS.keys())
    faltam = ids_py - ids_js
    sobram = ids_js - ids_py
    check(f"editor não deixa nenhuma de fora (faltam: {sorted(faltam)})", not faltam)
    check(f"editor não lista id inexistente (sobram: {sorted(sobram)})", not sobram)

def test_item_amaldicoado_editor():
    print("\n[N1] Item amaldiçoado sobrevive ao caminho do editor")
    # O formulário coletava maldicao_id/maldicao_prende, mas a serialização do
    # editor não os copiava — o item chegava aqui sem maldição nenhuma. Este
    # teste cobre o lado do servidor; o do cliente está em
    # tools/test_editor_items_logic.js.
    ok, arma = S._validate_custom_item(sample(id="lamina_maldita", name="Lâmina Maldita",
                                              maldicao_id="maos_tremulas", maldicao_prende=True))
    check("arma amaldiçoada é aceita", ok)
    check("guarda a maldição", ok and arma["maldicao_id"] == "maos_tremulas")
    check("guarda a trava", ok and arma["maldicao_prende"] is True)

    ok_i, invalida = S._validate_custom_item(sample(id="lamina_x", maldicao_id="nao_existe",
                                                    maldicao_prende=True))
    check("maldição desconhecida vira None", ok_i and invalida["maldicao_id"] is None)
    check("trava órfã é desligada", ok_i and invalida["maldicao_prende"] is False)

    anel = {"id": "anel_maldito", "name": "Anel Maldito", "emoji": "💍", "item_type": "ring",
            "bonuses": [], "allowed_classes": [], "price": 100,
            "maldicao_id": "correntes_invisiveis", "maldicao_prende": True,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    ok_a, acessorio = S._validate_custom_item(anel)
    check("acessório amaldiçoado é aceito", ok_a and acessorio["maldicao_id"] == "correntes_invisiveis")

    S._apply_custom_items([arma, acessorio])
    check("a maldição chega ao catálogo de combate",
          S.WEAPONS.get("lamina_maldita", {}).get("maldicao_id") == "maos_tremulas")
    check("a maldição chega ao inventário do acessório",
          S._DUNGEON_ITEM_CATALOG.get("anel_maldito", {}).get("maldicao_id") == "correntes_invisiveis"
          or any(i.get("id") == "anel_maldito" and i.get("maldicao_id") == "correntes_invisiveis"
                 for i in S.SHOP_MERCHANT))

    # Ponta a ponta: equipar o item de verdade amaldiçoa e liga a trava.
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    item_anel = next((dict(i) for i in S.SHOP_MERCHANT if i.get("id") == "anel_maldito"), None)
    check("anel amaldiçoado está à venda", item_anel is not None)
    if item_anel:
        mov_antes = r._moves_base(p)
        r._apply_gear_effect(p, item_anel, True)
        check("equipar aplica a maldição", r._tem_maldicao(p, "correntes_invisiveis"))
        check("a maldição tem efeito real", r._moves_base(p) == mov_antes - 3)
        p["gear"]["ring1"] = item_anel
        check("a trava reconhece o item", r._item_maldicao_vinculante(p, item_anel))
    S._apply_custom_items([])

def test_sincronia_maldicoes_editor():
    print("\n[N2] Lista de maldições do editor em sincronia com o servidor")
    import re, os
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "tools", "editor_items_logic.js")
    src = open(caminho, encoding="utf-8").read()
    bloco = re.search(r"var CURSES\s*=\s*\[(.*?)\n  \];", src, re.S)
    check("CURSES encontrado em editor_items_logic.js", bool(bloco))
    ids_js = set(re.findall(r'\["([a-z_]+)",', bloco.group(1))) if bloco else set()
    ids_py = set(S.MALDICOES.keys())
    faltam = ids_py - ids_js
    sobram = ids_js - ids_py
    check(f"editor não deixa nenhuma de fora (faltam: {sorted(faltam)})", not faltam)
    check(f"editor não lista maldição inexistente (sobram: {sorted(sobram)})", not sobram)

def test_curar_status_helpers():
    print("\n[K1] Helpers de cura de status")
    r = _gear_room()
    # Veneno: efeitos + cegueira
    p = S.make_player("p1", "Victor", "warrior", 0)
    p["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1, "duracao": 3,
                            "save": "fortitude", "dificuldade": 10}]
    p["cego"] = True; p["cego_rodadas"] = 3; p["cego_pen_ataque"] = -4
    p["penalidades"] = {"ataque": -4}
    p["bloqueia_distancia"] = True
    check("cura veneno devolve True", r._curar_veneno_status(p) is True)
    check("efeitos_veneno limpos", p["efeitos_veneno"] == [])
    check("cegueira removida", not p.get("cego") and p.get("cego_rodadas") == 0)
    check("penalidade de ataque revertida", p["penalidades"].get("ataque") == 0)
    check("volta a atacar à distância", p.get("bloqueia_distancia") is False)
    check("sem veneno devolve False", r._curar_veneno_status(p) is False)
    # Petrificação
    p2 = S.make_player("p2", "Aliado", "rogue", 1)
    p2["petrificado"] = True; p2["petrificado_rodadas"] = 3
    check("cura petrificação devolve True", r._curar_petrificacao(p2) is True)
    check("petrificado limpo", not p2.get("petrificado") and p2.get("petrificado_rodadas") == 0)
    check("sem petrificação devolve False", r._curar_petrificacao(p2) is False)

def test_purificacao_intacta():
    print("\n[K1b] Purificação do clérigo continua funcionando após a extração")
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Lewis", "cleric", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["fome"], p["sede"] = 20, 20
    alvo = S.make_player("p2", "Aliado", "rogue", 1)
    r.players["p2"] = alvo
    p["pos"] = [1, 1]; alvo["pos"] = [2, 1]
    alvo["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1, "duracao": 3,
                               "save": "fortitude", "dificuldade": 10}]
    asyncio.run(r.handle_purificacao("p1", {"tipo": "veneno", "target_id": "p2"}))
    check("purificação removeu o veneno", not alvo.get("efeitos_veneno"))
    alvo2 = S.make_player("p3", "Outro", "rogue", 2)
    r.players["p3"] = alvo2; alvo2["pos"] = [1, 2]
    alvo2["petrificado"] = True; alvo2["petrificado_rodadas"] = 2
    p["action_done"] = False
    p["guild_owned"]["especializacoes"] = ["clerigo_purif_3"]
    asyncio.run(r.handle_purificacao("p1", {"tipo": "petrificacao", "target_id": "p3"}))
    check("purificação removeu a petrificação", not alvo2.get("petrificado"))

def test_imunidade_status_helpers():
    print("\n[K2] Imunidade temporária de status")
    r = _gear_room()
    r.round_num = 5
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem imunidade", not r._imune_a_status(p, "veneno"))
    r._conceder_imunidade_status(p, "veneno", 3)
    check("imune após conceder", r._imune_a_status(p, "veneno") is True)
    check("outro status não é afetado", not r._imune_a_status(p, "doenca"))
    r.round_num = 8
    check("expira quando a rodada passa", not r._imune_a_status(p, "veneno"))

def test_imunidade_bloqueia_fontes():
    print("\n[K3] Imunidade bloqueia as 4 fontes")
    # 1) veneno
    r = _gear_room(); r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r._conceder_imunidade_status(p, "veneno", 5)
    asyncio.run(r._aplicar_veneno(p, "veneno_aranha_sombria"))
    check("veneno bloqueado pela imunidade", not p.get("efeitos_veneno"))
    # 2) petrificação por veneno (basilisco)
    r2 = _gear_room(); r2.round_num = 1
    p2 = S.make_player("p1", "Victor", "warrior", 0)
    r2.players["p1"] = p2
    p2["fort"] = -50   # garante falha no save
    r2._conceder_imunidade_status(p2, "petrificacao", 5)
    asyncio.run(r2._aplicar_veneno(p2, "veneno_basilisco"))
    check("petrificação por veneno bloqueada", not p2.get("petrificado"))
    # 3) petrificação por habilidade de monstro
    r3 = _gear_room(); r3.round_num = 1
    p3 = S.make_player("p1", "Victor", "warrior", 0)
    r3.players["p1"] = p3
    r3._conceder_imunidade_status(p3, "petrificacao", 5)
    check("helper reconhece a imunidade", r3._imune_a_status(p3, "petrificacao") is True)
    # 4) doença
    r4 = _gear_room(); r4.round_num = 1
    p4 = S.make_player("p1", "Victor", "warrior", 0)
    r4.players["p1"] = p4
    r4._conceder_imunidade_status(p4, "doenca", 5)
    asyncio.run(r4._aplicar_doenca(p4, "leve"))
    check("doença bloqueada pela imunidade", not p4.get("doente"))
    # sem imunidade, a doença aplica normalmente (prova que o teste é honesto)
    r5 = _gear_room(); r5.round_num = 1
    p5 = S.make_player("p1", "Victor", "warrior", 0)
    r5.players["p1"] = p5
    asyncio.run(r5._aplicar_doenca(p5, "leve"))
    check("sem imunidade a doença aplica", p5.get("doente") is True)

def _sala_turno_cura():
    """Sala com herói no turno + um aliado adjacente e um distante."""
    r = _gear_room()
    r.phase = "playing"; r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["pos"] = [1, 1]; p["fome"], p["sede"] = 10, 10
    perto = S.make_player("p2", "Perto", "rogue", 1)
    longe = S.make_player("p3", "Longe", "cleric", 2)
    r.players["p2"] = perto; r.players["p3"] = longe
    perto["pos"] = [2, 1]; longe["pos"] = [9, 9]
    return r, p, perto, longe

def _frasco(effect, imunidade="1d4", iid=None):
    return {"id": iid or effect, "name": "Frasco", "emoji": "🧪",
            "item_slot": "bag", "effect": effect, "value": 0,
            "imunidade_dado": imunidade}

def test_cura_status_em_si():
    print("\n[K4] Consumíveis curam o próprio herói e imunizam")
    # Veneno
    r, p, _, _ = _sala_turno_cura()
    p["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1, "duracao": 3,
                            "save": "fortitude", "dificuldade": 10}]
    p["bag"] = [_frasco("cure_poison")]
    asyncio.run(r.handle_use_item("p1", "cure_poison"))
    check("veneno curado", not p.get("efeitos_veneno"))
    check("imunidade concedida", r._imune_a_status(p, "veneno") is True)
    check("frasco consumido", not p["bag"])
    # Petrificação
    r2, p2, _, _ = _sala_turno_cura()
    p2["petrificado"] = True; p2["petrificado_rodadas"] = 3
    p2["bag"] = [_frasco("cure_petrification")]
    asyncio.run(r2.handle_use_item("p1", "cure_petrification"))
    check("petrificação curada", not p2.get("petrificado"))
    check("imune a petrificação", r2._imune_a_status(p2, "petrificacao") is True)
    # Doença
    r3, p3, _, _ = _sala_turno_cura()
    asyncio.run(r3._aplicar_doenca(p3, "leve"))
    p3["bag"] = [_frasco("cure_disease")]
    asyncio.run(r3.handle_use_item("p1", "cure_disease"))
    check("doença curada", not p3.get("doente"))
    check("imune a doença", r3._imune_a_status(p3, "doenca") is True)
    # Uso preventivo: consome mesmo sem o status
    r4, p4, _, _ = _sala_turno_cura()
    p4["bag"] = [_frasco("cure_poison")]
    asyncio.run(r4.handle_use_item("p1", "cure_poison"))
    check("uso preventivo consome o item", not p4["bag"])
    check("uso preventivo imuniza", r4._imune_a_status(p4, "veneno") is True)

def test_cura_status_em_aliado():
    print("\n[K5] Consumíveis em aliado adjacente")
    r, p, perto, longe = _sala_turno_cura()
    perto["petrificado"] = True; perto["petrificado_rodadas"] = 3
    p["bag"] = [_frasco("cure_petrification")]
    asyncio.run(r.handle_use_item("p1", "cure_petrification", "p2"))
    check("aliado adjacente curado", not perto.get("petrificado"))
    check("imunidade vai para o ALVO", r._imune_a_status(perto, "petrificacao") is True)
    check("quem usou não fica imune", not r._imune_a_status(p, "petrificacao"))
    check("frasco consumido", not p["bag"])
    # Alvo distante: recusa sem consumir
    r2, p2, _, longe2 = _sala_turno_cura()
    longe2["petrificado"] = True
    p2["bag"] = [_frasco("cure_petrification")]
    asyncio.run(r2.handle_use_item("p1", "cure_petrification", "p3"))
    check("alvo distante recusado", longe2.get("petrificado") is True)
    check("item NÃO consumido em alvo inválido", len(p2["bag"]) == 1)
    check("ação bônus NÃO gasta em alvo inválido", not p2.get("bonus_action_used"))

def test_itens_nativos_e_editor_cura():
    print("\n[K6] Itens nativos + validação no editor")
    ant = next((i for i in S.SHOP_MERCHANT if i["id"] == "antidote"), None)
    check("antídoto nativo existe", ant is not None)
    check("antídoto cura veneno de verdade", ant and ant.get("effect") == "cure_poison")
    check("antídoto tem dado de imunidade", ant and ant.get("imunidade_dado") == "1d4")
    oleo = next((i for i in S.SHOP_MERCHANT if i["id"] == "oleo_dissolvente"), None)
    check("óleo dissolvente na loja", oleo and oleo.get("effect") == "cure_petrification")
    elix = next((i for i in S.SHOP_MERCHANT if i["id"] == "elixir_depurativo"), None)
    check("elixir depurativo na loja", elix and elix.get("effect") == "cure_disease")
    # Validação de poção custom com os 3 efeitos
    for eff in ("cure_poison", "cure_petrification", "cure_disease"):
        ok, it = S._validate_custom_item(potion_sample(id=f"p_{eff}", effect=eff,
                                                       imunidade_dado="1d6"))
        check(f"aceita {eff}", ok and it.get("effect") == eff)
        check(f"{eff} preserva imunidade_dado", ok and it.get("imunidade_dado") == "1d6")
    okb, itb = S._validate_custom_item(potion_sample(id="p_bad", effect="cure_poison",
                                                     imunidade_dado="1d7"))
    check("dado de imunidade inválido é descartado", okb and "imunidade_dado" not in itb)

def _stock_sandbox():
    """Isola CITY_SHOPS + o arquivo de estoque para não sujar o city_shops.json real."""
    import copy
    orig = {"stock": copy.deepcopy(S.CITY_SHOPS), "file": S.CITY_SHOPS_FILE}
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False); tmp.close()
    S.CITY_SHOPS_FILE = tmp.name
    return orig, tmp.name

def _stock_restore(orig, tmp_path):
    S.CITY_SHOPS_FILE = orig["file"]
    S.CITY_SHOPS.clear(); S.CITY_SHOPS.update(orig["stock"])
    try: os.unlink(tmp_path)
    except OSError: pass
    S._apply_custom_items(S._read_custom_items())   # devolve os catálogos ao estado real

def test_estoque_cidade_helpers():
    print("\n[L1] Loja por cidade — mapeamento item→loja")
    check("arma → ferreiro_weapon", S._custom_item_shop_id("weapon") == "ferreiro_weapon")
    check("armadura → ferreiro_armor", S._custom_item_shop_id("armor") == "ferreiro_armor")
    check("escudo → ferreiro_armor", S._custom_item_shop_id("shield") == "ferreiro_armor")
    for t in ("ring", "boots", "potion", "throwable", "poison"):
        check(f"{t} → mercador", S._custom_item_shop_id(t) == "mercador")

def test_estoque_cidade_sincronia_editor():
    print("\n[L4] Mapa item→loja em sincronia com o editor")
    import re
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "tools", "editor_items_logic.js")
    src = open(caminho, encoding="utf-8").read()
    bloco = re.search(r"SHOP_BY_ITEM_TYPE\s*=\s*\{(.*?)\}", src, re.S)
    check("SHOP_BY_ITEM_TYPE encontrado no editor", bool(bloco))
    mapa_js = dict(re.findall(r'(\w+):\s*"([^"]+)"', bloco.group(1))) if bloco else {}
    check(f"mesmo mapa do servidor (js={mapa_js})", mapa_js == S._CUSTOM_ITEM_SHOP)

def test_estoque_cidade_sync():
    print("\n[L2] Loja por cidade — sincronismo ao salvar o item")
    orig, tmp_path = _stock_sandbox()
    try:
        cidades = list(S.CITY_SHOPS.keys())
        c1, c2 = cidades[0], cidades[1]
        ok, item = S._validate_custom_item(poison_sample(id="veneno_teste_cidade"))
        check("veneno de teste válido", ok)
        S._apply_custom_items([item])
        # Antes de estocar: está no catálogo global mas não na loja de nenhuma cidade.
        check("no catálogo global (SHOP_MERCHANT)",
              any(i["id"] == "veneno_teste_cidade" for i in S.SHOP_MERCHANT))
        check("ainda não aparece na loja da cidade",
              not any(i["id"] == "veneno_teste_cidade"
                      for i in S._city_shop_items(c1, "mercador")))
        # Estoca em c1.
        S._sync_custom_item_city_stock(item, [c1])
        check("aparece na loja de c1",
              any(i["id"] == "veneno_teste_cidade" for i in S._city_shop_items(c1, "mercador")))
        check("não aparece em c2",
              not any(i["id"] == "veneno_teste_cidade" for i in S._city_shop_items(c2, "mercador")))
        # Troca de cidade: sai de c1, entra em c2 (sem duplicar).
        S._sync_custom_item_city_stock(item, [c2])
        check("saiu de c1 ao desmarcar",
              not any(i["id"] == "veneno_teste_cidade" for i in S._city_shop_items(c1, "mercador")))
        check("entrou em c2", any(i["id"] == "veneno_teste_cidade"
                                  for i in S._city_shop_items(c2, "mercador")))
        S._sync_custom_item_city_stock(item, [c2, c2])
        check("não duplica o id na lista",
              S.CITY_SHOPS[c2]["mercador"].count("veneno_teste_cidade") == 1)
        # loja=False esvazia o estoque mesmo com cidades marcadas.
        item_sem_loja = dict(item, disponibilidade=dict(item["disponibilidade"], loja=False))
        S._sync_custom_item_city_stock(item_sem_loja, [c1, c2])
        check("loja desmarcada retira de todas as cidades",
              not any("veneno_teste_cidade" in shops.get("mercador", [])
                      for shops in S.CITY_SHOPS.values()))
        # Renomear: o id antigo sai do estoque.
        S._sync_custom_item_city_stock(item, [c1])
        novo = dict(item, id="veneno_teste_cidade2")
        S._sync_custom_item_city_stock(novo, [c1], old_id="veneno_teste_cidade")
        check("id antigo removido ao renomear",
              not any("veneno_teste_cidade" in shops.get("mercador", [])
                      for shops in S.CITY_SHOPS.values()))
        check("id novo estocado", "veneno_teste_cidade2" in S.CITY_SHOPS[c1]["mercador"])
    finally:
        _stock_restore(orig, tmp_path)

def test_estoque_cidade_persiste_no_boot():
    print("\n[L3] Loja por cidade — id custom sobrevive ao reload do boot")
    orig, tmp_path = _stock_sandbox()
    try:
        c1 = list(S.CITY_SHOPS.keys())[0]
        ok, item = S._validate_custom_item(poison_sample(id="veneno_boot_teste"))
        S._apply_custom_items([item])
        S._sync_custom_item_city_stock(item, [c1])          # grava no arquivo
        S.CITY_SHOPS[c1]["mercador"] = []                    # zera a memória
        S._load_city_shops()                                 # relê como no boot
        check("id custom preservado pelo _load_city_shops",
              "veneno_boot_teste" in S.CITY_SHOPS[c1]["mercador"])
        check("item volta a aparecer na loja",
              any(i["id"] == "veneno_boot_teste" for i in S._city_shop_items(c1, "mercador")))
    finally:
        _stock_restore(orig, tmp_path)

if __name__ == "__main__":
    test_validacao(); test_merge(); test_base_intacta()
    test_upload_art(); test_save_item(); test_combate_passivo()
    test_compra_equipa_preserva(); test_corrosao()
    test_penalidade_engine(); test_material_e_municao()
    test_validacao_armadura(); test_merge_armadura()
    test_multi_efeito(); test_compra_armadura()
    test_corrosao_armadura_nm()
    test_corrosao_botas()
    test_atributo_forca(); test_atributo_destreza()
    test_atributo_con_int(); test_atributo_empilha_e_aovivo()
    test_validacao_bonus_atributo()
    test_resistencia_aplica(); test_resistencia_empilha()
    test_validacao_resist()
    test_iniciativa_bonus(); test_visao_bonus()
    test_validacao_acessorio()
    test_acessorio_equip_efeitos(); test_acessorio_resist()
    test_acessorio_botas_corrosao(); test_acessorio_merge()
    test_validacao_pocao()
    test_pocao_merge(); test_pocao_uso(); test_pocao_multidose()
    test_validacao_arremessavel()
    test_arremessavel_merge(); test_arremessavel_uso_alvo(); test_arremessavel_uso_area()
    test_validacao_veneno()
    test_veneno_merge(); test_veneno_uso(); test_veneno_efeitos()
    test_veneno_msg_penalidade()
    test_habilidade_concedida_helper(); test_portoes_concedidos()
    test_tecnica_concedida_uso(); test_espec_concedida_efeito()
    test_habilidades_heroi_concedidas(); test_mensagens_sem_richard()
    test_granted_hero_skills_payload()
    test_validacao_granted_ability()
    test_helpers_hab_heroi(); test_mapa_14_habilidades()
    test_hab_clerigo_concedida(); test_hab_ladino_concedida()
    test_hab_paladino_concedida(); test_hab_bardo_concedida()
    test_sincronia_editor_servidor()
    test_upkeep_habilidade_concedida()
    test_curar_status_helpers(); test_purificacao_intacta()
    test_imunidade_status_helpers(); test_imunidade_bloqueia_fontes()
    test_cura_status_em_si(); test_cura_status_em_aliado()
    test_itens_nativos_e_editor_cura()
    test_estoque_cidade_helpers(); test_estoque_cidade_sincronia_editor()
    test_estoque_cidade_sync()
    test_estoque_cidade_persiste_no_boot()
    test_item_amaldicoado_editor(); test_sincronia_maldicoes_editor()
    print(f"\n{PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
