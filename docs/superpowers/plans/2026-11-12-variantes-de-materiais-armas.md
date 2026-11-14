# Variantes de Materiais para Armas — Implementation Plan

> **For agentic workers:** Execute sequentially and preserve unrelated pending work.

**Goal:** Add 15 weapons each for Aço Damasco, Obsidiana de Ferro, and Liga de Titânio, plus 11 bows/crossbows each for Freixo Negro, Cedro Rubro, and Cerne de Titã, to all five blacksmiths.

**Architecture:** Clone each existing weapon's combat and store profile, then override its stable ID, name, image, material, bonus, corrosion tolerance, and price. Keep the weapons mundane. Generate the editor catalog from `server.py` and retain city stock as the source of availability.

**Tech Stack:** Python catalogs, JSON city stocks, JavaScript localized vocabulary, generated editor catalog.

**Spec:** Aço Damasco (15 melee) and Freixo Negro (5 bows, 6 crossbows) get +1 attack; Obsidiana de Ferro (15 melee) and Cedro Rubro (5 bows, 6 crossbows) get +1 damage. These four are mundane, tolerate one corrosion level without penalties (then two penalized levels), and cost 20 coins above base. Liga de Titânio (15 melee) and Cerne de Titã (5 bows, 6 crossbows) have no attack/damage bonus, use N=2/M=3 corrosion (same corrosion capacity as silver), remain non-silver, and cost 30 coins above base.

## Global Constraints

- Keep the original weapon profile, class restrictions, ammunition rules, and range.
- Use only the matching image under `assets/itens/`.
- Stock all 26 variants at all five blacksmiths.
- Do not alter the existing weapon definitions or unrelated pending changes.

## Review Focus

- Purchase/equip retains image and material combat metadata.
- Metal variants corrode only from the metal source; wood variants only from organic corrosion.
- All city stocks refer to valid catalog IDs.

### Task 1: Register material variants

**Files:** `server.py`, `tools/export_catalog.py`, `city_shops.json`, `src/lang/catalogo.js`, `tools/editor_catalog.js`, `CLAUDE.md`.

- [x] Add declarative variants derived from each base weapon, with the agreed price and combat/corrosion fields.
- [x] Add the material families to matching corrosion sets, preserve material metadata, and carry ranged ammo/dual-crossbow behavior through each clone.
- [x] Add all 78 variant IDs to every `ferreiro_weapon` stock.
- [x] Add Portuguese and English names/descriptions and regenerate the editor vocabulary/catalog.
- [x] Document the material rules and prices.
