/* Logica pura do Editor de Itens (sem DOM). Carregavel no browser (window) e no
   Node (module.exports) para teste. */
(function (root) {
  "use strict";
  var ELEM = ["fire", "cold", "lightning", "acid", "holy"];
  var CATS = ["cortante", "contundente", "perfurante"];
  var FACES = [4, 6, 8, 10, 12];

  function slugify(v) {
    return String(v || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "arma";
  }
  function buildDie(qtd, faces) { return Math.max(1, +qtd || 1) + "d" + (+faces || 6); }
  function dieAvg(txt) {
    var m = /^(\d+)d(\d+)$/.exec(String(txt || "")); if (!m) return 0;
    return (+m[1]) * ((+m[2]) + 1) / 2;
  }
  // Preco sugerido: transparente e recalibravel (constantes no topo).
  var K_DIE = 4, K_BONUS = 6, K_ELEM = 5, K_2M = 4;
  function suggestPrice(item) {
    var p = K_DIE * dieAvg(item.die);
    p += K_BONUS * (Math.abs(+item.atk_bonus || 0) + Math.abs(+item.damage_bonus || 0));
    (item.extra_damages || []).forEach(function (x) { p += K_ELEM * dieAvg(x.die); });
    if (item.two_handed) p += K_2M;
    return Math.max(1, Math.round(p));
  }
  function serializeWeapon(d) {
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "⚔️", item_type: "weapon", custom: true,
      die: buildDie(d.die_qtd, d.die_faces),
      stat: d.stat === "dex" ? "dex" : "str_",
      categoria: CATS.indexOf(d.categoria) >= 0 ? d.categoria : "cortante",
      finesse: !!d.finesse, two_handed: !!d.two_handed,
      atk_bonus: +d.atk_bonus || 0, damage_bonus: +d.damage_bonus || 0,
      extra_damages: (d.extra_damages || []).filter(function (x) {
        return x && /^\d+d\d+$/.test(x.die) && ELEM.indexOf(x.type) >= 0;
      }).map(function (x) { return { die: x.die, type: x.type }; }),
      granted_ability: d.granted_ability || null,
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      // Corrosão em dois eixos: N níveis SEM penalidade (corrosao_resistente) +
      // M níveis COM penalidade (corrosao_niveis_penalidade, escala -1/nível);
      // quebra no golpe N+M+1. Material define qual Devorador a corrói.
      corrosao_resistente: Math.max(0, +d.corrosao_livres || 0),
      corrosao_niveis_penalidade: Math.max(1, +d.corrosao_penalidade || 2),
      material: d.material === "madeira" ? "madeira" : "metal",
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (d.manejo === "lanca") item.reach = "lanca";
    else if (d.manejo === "cajado") item.reach = "cajado";
    else if (d.manejo === "distancia") {
      item.range = Math.max(1, +d.range || 4);
      if (d.ammo === "flechas" || d.ammo === "virotes") item.ammo = d.ammo;
    }
    if (d.manejo === "arremessavel" || d.throw_range) item.throw_range = Math.max(1, +d.throw_range || 3);
    return item;
  }
  function validateDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (FACES.indexOf(+d.die_faces) < 0) return { ok: false, msg: "dado invalido" };
    if (CATS.indexOf(d.categoria) < 0) return { ok: false, msg: "categoria invalida" };
    return { ok: true };
  }
  var ARMOR_CATS = ["leve", "media", "pesada"];
  var BONUS_EFFECTS = ["def_", "maxhp", "spd", "str_", "dex", "con_", "int_"];
  function serializeArmor(d) {
    var kind = d.item_type === "shield" ? "shield" : "armor";
    var mats = [];
    var mm = d.materiais || {};
    if (mm.organic) mats.push("organic");
    if (mm.metal) mats.push("metal");
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "🛡️", item_type: kind, kind: kind, custom: true,
      ac_bonus: Math.max(0, +d.ac_bonus || 0),
      armor_category: (kind === "armor" && ARMOR_CATS.indexOf(d.armor_category) >= 0) ? d.armor_category : null,
      corrosion_materials: mats,
      corrosao_resistente: Math.max(0, +d.corrosao_livres || 0),
      corrosao_niveis_penalidade: Math.max(1, +d.corrosao_penalidade || 2),
      bonuses: (d.bonuses || []).filter(function (b) {
        return b && BONUS_EFFECTS.indexOf(b.effect) >= 0;
      }).map(function (b) { return { effect: b.effect, value: +b.value || 0 }; }),
      granted_ability: d.granted_ability || null,
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    return item;
  }
  var KA_CA = 20, KA_BONUS = 6;
  function suggestPriceArmor(item) {
    var p = KA_CA * (+item.ac_bonus || 0);
    (item.bonuses || []).forEach(function (b) { p += KA_BONUS * Math.abs(+b.value || 0); });
    return Math.max(1, Math.round(p));
  }
  function validateArmorDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if ((+d.ac_bonus || 0) < 0) return { ok: false, msg: "CA inválida" };
    return { ok: true };
  }
  var api = { slugify: slugify, buildDie: buildDie, dieAvg: dieAvg,
              suggestPrice: suggestPrice, serializeWeapon: serializeWeapon,
              validateDraft: validateDraft, ELEM: ELEM, CATS: CATS, FACES: FACES,
              serializeArmor: serializeArmor, suggestPriceArmor: suggestPriceArmor,
              validateArmorDraft: validateArmorDraft,
              ARMOR_CATS: ARMOR_CATS, BONUS_EFFECTS: BONUS_EFFECTS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.EDITOR_ITEMS_LOGIC = api;
})(typeof window !== "undefined" ? window : null);
