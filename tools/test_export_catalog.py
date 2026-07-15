"""Teste do gerador de catálogo do editor (Fase 2).
Roda da raiz: python tools/test_export_catalog.py"""
import sys, os, json, re
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
import tools.export_catalog as ec

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    print("\n[1] build_catalog")
    cat = ec.build_catalog()
    tipos_srv = {m["type"] for m in server.MONSTER_DEFS}
    ids_srv   = set(server._DUNGEON_ITEM_CATALOG)
    check("todo monstro exportado existe no servidor",
          all(m["type"] in tipos_srv for m in cat["monsters"]))
    check("exporta todos os monstros nativos", len(cat["monsters"]) ==
          sum(1 for m in server.MONSTER_DEFS if not m.get("_personalizado")))
    check("monstro tem type/name/emoji",
          all(all(k in m for k in ("type", "name", "emoji")) for m in cat["monsters"]))
    check("dragon marcado como boss",
          any(m["type"] == "dragon" and m.get("boss") for m in cat["monsters"]))
    check("todo item exportado existe no servidor",
          all(i["id"] in ids_srv for i in cat["items"]))
    lojas = (server.SHOP_WEAPONS + server.SHOP_ARMORS + server.SHOP_AMMO + server.SHOP_MERCHANT
             + server.SHOP_TAVERN + server.SHOP_TEMPLE)
    check("itens portáteis das lojas entram no loot",
          all(i["id"] in ids_srv for i in lojas if i.get("item_slot") or i.get("die") or i.get("kind")))
    check("toda armadilha exportada existe no servidor",
          all(t["tipo"] in server.ARMADILHAS for t in cat["traps"]))
    check("fosso_envenenado precisa_veneno=True",
          any(t["tipo"] == "fosso_envenenado" and t["precisa_veneno"] for t in cat["traps"]))
    check("todo veneno exportado existe no servidor",
          all(v["id"] in server.VENENOS for v in cat["venoms"]))
    check("veneno tem name", all(v.get("name") for v in cat["venoms"]))

    print("\n[2] write_catalog_js")
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_catalog.js")
    ec.write_catalog_js(destino)
    with open(destino, encoding="utf-8") as f:
        txt = f.read()
    check("arquivo começa com a atribuição global",
          txt.lstrip().startswith("window.EDITOR_CATALOG"))
    m = re.search(r"window\.EDITOR_CATALOG\s*=\s*(\{.*\});", txt, re.S)
    check("payload é JSON válido", bool(m) and isinstance(json.loads(m.group(1)), dict))

    print("\n[decor] decorações exportadas")
    check("catálogo tem 'decorations'", "decorations" in cat)
    check("todas as decorações", len(cat.get("decorations", [])) == len(server.DECOR_TYPES))
    check("toda decoração tem type/nome/emoji/size/gira/alto/pisavel/loot_capaz/special",
          all(set(("type", "nome", "emoji", "size", "gira", "alto", "pisavel", "loot_capaz", "special")) <= set(d)
              for d in cat.get("decorations", [])))
    check("fonte exportada como fountain",
          any(d["type"] == "fonte" and d["special"] == "fountain" for d in cat.get("decorations", [])))

    test_dungeons_index()

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

def test_dungeons_index():
    print("\n[3] índice de masmorras")
    idx = ec.build_dungeons_index()
    check("inclui test_camp_a.json", any(d["file"] == "test_camp_a.json" for d in idx))
    check("itens têm file/id/name/defn",
          all(all(k in d for k in ("file", "id", "name", "defn")) for d in idx))
    check("defn é a masmorra (tem grid/tiles)",
          all("grid" in d["defn"] and "tiles" in d["defn"] for d in idx))
    # só válidas
    for d in idx:
        ok, _ = server.validar_dungeon(d["defn"]);
        if not ok: check("masmorra do índice válida", False); break
    else:
        check("todas do índice são válidas", True)
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_dungeons.js")
    ec.write_dungeons_js(destino)
    with open(destino, encoding="utf-8") as f: txt = f.read()
    check("começa com window.EDITOR_DUNGEONS",
          txt.lstrip().startswith("window.EDITOR_DUNGEONS"))
    m = re.search(r"window\.EDITOR_DUNGEONS\s*=\s*(\[.*\]);", txt, re.S)
    check("payload é JSON válido", bool(m) and isinstance(json.loads(m.group(1)), list))

if __name__ == "__main__":
    main()
