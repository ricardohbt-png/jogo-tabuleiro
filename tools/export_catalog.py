"""Gera tools/editor_catalog.js a partir dos catálogos autoritativos do server.py.
Rode da raiz quando os catálogos do servidor mudarem:  python tools/export_catalog.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def build_catalog():
    """Extrai só os campos que o editor precisa. Retorna dict serializável."""
    monsters = []
    for m in server.MONSTER_DEFS:
        if m.get("_personalizado"):
            continue  # carregados separadamente por editor_monsters_custom.js
        # A ficha do Bestiário é somente consulta, mas precisa dos dados completos
        # já definidos no servidor. Mantemos o catálogo em JSON, sem estado de jogo.
        fields = (
            "type", "name", "emoji", "boss", "tier", "cr", "hp", "ac", "natural_armor",
            "movement", "movement_exception", "vision_base", "size", "porte", "image", "atk_bonus", "damage",
            "base_attack_bonus", "base_hp", "caster_level", "str_", "dex", "con_", "int_",
            "fort", "ref_", "will", "fort_base", "ref_base", "will_base",
            "attacks", "special_abilities", "monster_spells", "immunities", "weaknesses",
            "resistances",
            "loot_table", "guaranteed_loot", "equipment", "equipment_enabled", "equipped_items", "gold", "xp",
            "ai_type", "undead", "subtipo", "darkvision_range",
        )
        entry = {key: m[key] for key in fields if key in m}
        monsters.append(entry)
    items = [{key: i[key] for key in (
                "id", "name", "emoji", "die", "stat", "range", "reach", "categoria",
                "kind", "ac_bonus", "item_slot", "effect", "value", "veneno_id",
                "ammo_type", "ammo_count", "extra_damage", "extra_damage_types"
             ) if key in i}
             for i in server._DUNGEON_ITEM_CATALOG.values()]
    traps = []
    for tipo, meta in server.ARMADILHAS.items():
        traps.append({
            "tipo": tipo, "nome": meta["nome"], "icone": meta.get("icone", ""),
            "cr": server.trap_cr(meta),
            "precisa_veneno": bool(meta.get("precisa_veneno") or meta.get("custo_veneno")),
        })
    venoms = [{"id": vid, "name": meta["nome"]} for vid, meta in server.VENENOS.items()]
    decorations = []
    for dtype, meta in server.DECOR_TYPES.items():
        decorations.append({
            "type": dtype, "nome": meta["nome"], "emoji": meta["emoji"],
            "size": meta["size"], "gira": meta["gira"], "alto": meta["alto"],
            "pisavel": meta["pisavel"], "loot_capaz": meta["loot_capaz"],
            "special": meta["special"], "image": meta.get("image"),
        })
    materiais = []
    for mid, meta in server.MATERIAIS.items():
        materiais.append({
            "id": mid, "nome": meta["nome"], "categoria": meta["categoria"],
            "cor": meta["cor"], "solido": meta["solido"], "oclui": meta["oclui"],
        })
    spells = []
    for spell in server.GRIMORIO.values():
        # O editor precisa de uma descrição completa o suficiente para explicar a
        # magia e de seus metadados para estimar o impacto no ND.
        spells.append({key: spell[key] for key in (
            "id", "nome", "circulo", "classe", "icone", "tipo", "descricao",
            "save", "dano", "dano_base", "dano_por_nivel", "area_raio",
            "area_lado", "alcance", "alcance_base", "duracao", "buff", "debuff",
        ) if key in spell})
    monster_abilities = list(server._base_ability_library().values())
    return {"monsters": monsters, "monster_abilities": monster_abilities,
            "spells": spells, "items": items, "traps": traps,
            "venoms": venoms, "decorations": decorations, "materiais": materiais}

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
