"""Gera tools/editor_catalog.js a partir dos catálogos autoritativos do server.py.
Rode da raiz quando os catálogos do servidor mudarem:  python tools/export_catalog.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def build_catalog():
    """Extrai só os campos que o editor precisa. Retorna dict serializável."""
    monsters = []
    for m in server.MONSTER_DEFS:
        entry = {"type": m["type"], "name": m["name"], "emoji": m.get("emoji", "")}
        if m.get("boss"):
            entry["boss"] = True
        monsters.append(entry)
    items = [{"id": i["id"], "name": i["name"], "emoji": i.get("emoji", "")}
             for i in server.CHEST_ITEMS]
    traps = []
    for tipo, meta in server.ARMADILHAS.items():
        traps.append({
            "tipo": tipo, "nome": meta["nome"], "icone": meta.get("icone", ""),
            "precisa_veneno": tipo == "fosso_envenenado" or bool(meta.get("custo_veneno")),
        })
    venoms = [{"id": vid, "name": meta["nome"]} for vid, meta in server.VENENOS.items()]
    decorations = []
    for dtype, meta in server.DECOR_TYPES.items():
        decorations.append({
            "type": dtype, "nome": meta["nome"], "emoji": meta["emoji"],
            "size": meta["size"], "gira": meta["gira"], "alto": meta["alto"],
            "pisavel": meta["pisavel"], "loot_capaz": meta["loot_capaz"],
            "special": meta["special"],
        })
    return {"monsters": monsters, "items": items, "traps": traps,
            "venoms": venoms, "decorations": decorations}

def write_catalog_js(destino):
    """Escreve o catálogo como atribuição JS (carregável via <script> em file://)."""
    cat = build_catalog()
    payload = json.dumps(cat, ensure_ascii=False, indent=2)
    txt = ("window.EDITOR_CATALOG = " + payload + ";\n"
           "// GERADO por tools/export_catalog.py — não editar à mão.\n"
           "// Rode `python tools/export_catalog.py` para regenerar.\n")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(txt)
    return destino

def build_dungeons_index():
    """Lista as masmorras válidas de dungeons/ com o defn completo embutido."""
    out = []
    for d in server.listar_dungeons():   # [{id,name,file}] já só de válidas
        defn = server.carregar_dungeon(d["file"])
        if defn is None:
            continue
        out.append({"file": d["file"], "id": d["id"], "name": d["name"], "defn": defn})
    return out

def write_dungeons_js(destino):
    payload = json.dumps(build_dungeons_index(), ensure_ascii=False, indent=2)
    txt = ("window.EDITOR_DUNGEONS = " + payload + ";\n"
           "// GERADO por tools/export_catalog.py — não editar à mão.\n")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(txt)
    return destino

if __name__ == "__main__":
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_catalog.js")
    write_catalog_js(destino)
    print(f"editor_catalog.js gerado em {destino}")
    idx_dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_dungeons.js")
    write_dungeons_js(idx_dest)
    print(f"editor_dungeons.js gerado em {idx_dest}")
