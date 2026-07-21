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
    S._apply_custom_items([S._validate_custom_item(sample(id="lamina_gelo",
        extra_damages=[{"die": "1d6", "type": "cold"}], damage_bonus=2))[1]])
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True; r.phase = "city"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["gold"] = 9999; p["bag"] = []; p["gear"]["weapon"] = None
    asyncio.run(r.handle_shop_buy("p1", "ferreiro_weapon", "lamina_gelo"))
    comprada = next((it for it in p["bag"] if it and it.get("id") == "lamina_gelo"), None)
    check("comprada foi pra bolsa", comprada is not None)
    check("bolsa preserva extra_damages", comprada and comprada.get("extra_damages"))
    check("bolsa preserva damage_bonus", comprada and comprada.get("damage_bonus") == 2)
    idx = p["bag"].index(comprada)
    asyncio.run(r._executar_equip_from_bag("p1", idx))
    check("equipar sincroniza extra_damages em p['weapon']", p["weapon"].get("extra_damages"))
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

if __name__ == "__main__":
    test_validacao(); test_merge(); test_base_intacta()
    test_upload_art(); test_save_item(); test_combate_passivo()
    test_compra_equipa_preserva(); test_corrosao()
    test_penalidade_engine(); test_material_e_municao()
    test_validacao_armadura(); test_merge_armadura()
    test_multi_efeito()
    print(f"\n{PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
