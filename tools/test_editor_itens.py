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

def test_save_item():
    print("\n[5] Salvar item (fluxo completo)")
    ok, item = S._save_custom_item(sample(id="teste_persist"))
    check("save retorna ok", ok)
    check("consta no arquivo JSON", any(r.get("id") == "teste_persist" for r in S._read_custom_items()))
    check("mesclado em WEAPONS", "teste_persist" in S.WEAPONS)
    recs = [r for r in S._read_custom_items() if r.get("id") != "teste_persist"]
    S._gravar_def(recs, os.path.dirname(S.CUSTOM_ITEMS_FILE), os.path.basename(S.CUSTOM_ITEMS_FILE))
    S._apply_custom_items(recs); S._regen_custom_items_index(recs)

if __name__ == "__main__":
    test_validacao(); test_merge(); test_base_intacta()
    test_upload_art(); test_save_item()
    print(f"\n{PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
