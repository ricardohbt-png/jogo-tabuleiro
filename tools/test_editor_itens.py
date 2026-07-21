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
    native = {w["id"] for w in S.SHOP_WEAPONS}
    ok5, _ = S._validate_custom_item(sample(id="longsword"))
    check("rejeita id que colide com arma nativa", (not ok5) or ("longsword" not in native))

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
    S._apply_custom_items([])
    check("lista vazia remove de WEAPONS", "espada_flamejante" not in S.WEAPONS)
    check("lista vazia remove de SHOP_WEAPONS", not any(w["id"] == "espada_flamejante" for w in S.SHOP_WEAPONS))

def test_base_intacta():
    print("\n[3] Itens base intocados")
    antes = dict(S.WEAPONS["longsword"])
    S._apply_custom_items([S._validate_custom_item(sample(id="nova_arma"))[1]])
    check("longsword base inalterada", S.WEAPONS["longsword"] == antes)
    S._apply_custom_items([])

if __name__ == "__main__":
    test_validacao(); test_merge(); test_base_intacta()
    print(f"\n{PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
