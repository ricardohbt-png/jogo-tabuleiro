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
  var K_DIE = 4, K_BONUS = 6, K_ELEM = 5, K_2M = 4, K_POTION = 2, K_THROW = 5;
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
  var BONUS_EFFECTS = ["def_", "maxhp", "spd", "atk_bonus", "str_", "dex", "con_", "int_", "resist", "initiative"];
  var RESIST_TYPES = ["physical", "fire", "cold", "lightning", "acid", "holy", "poison", "magic", "water"];
  var POTION_EFFECTS = ["heal", "regeneration", "atk_bonus"];
  var THROW_TARGETS = ["ataque_alvo", "area"];
  var THROW_ELEMENTS = ["fogo", "frio", "eletrico", "acido", "sagrado", "explosao"];
  function filterBonuses(list) {
    return (list || []).filter(function (b) {
      if (!b || BONUS_EFFECTS.indexOf(b.effect) < 0) return false;
      if (b.effect === "resist" && RESIST_TYPES.indexOf(b.type) < 0) return false;
      return true;
    }).map(function (b) {
      return b.effect === "resist"
        ? { effect: "resist", type: b.type, value: +b.value || 0 }
        : { effect: b.effect, value: +b.value || 0 };
    });
  }
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
      bonuses: filterBonuses(d.bonuses),
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
  function serializeAccessory(d) {
    var kind = d.item_type === "boots" ? "boots" : "ring";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || (kind === "boots" ? "👢" : "💍"),
      item_type: kind, kind: kind, item_slot: kind, custom: true,
      bonuses: filterBonuses(d.bonuses),
      granted_ability: d.granted_ability || null,
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (kind === "boots") {
      var mats = [];
      var mm = d.materiais || {};
      if (mm.organic) mats.push("organic");
      if (mm.metal) mats.push("metal");
      item.corrosion_materials = mats;
      item.corrosao_resistente = Math.max(0, +d.corrosao_livres || 0);
      item.corrosao_niveis_penalidade = Math.max(1, +d.corrosao_penalidade || 2);
    }
    return item;
  }
  function validateAccessoryDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    return { ok: true };
  }
  function suggestPriceAccessory(item) {
    var p = 0;
    (item.bonuses || []).forEach(function (b) { p += KA_BONUS * Math.abs(+b.value || 0); });
    return Math.max(1, Math.round(p));
  }
  function serializePotion(d) {
    var effect = POTION_EFFECTS.indexOf(d.effect) >= 0 ? d.effect : "heal";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "🧪", item_type: "potion", item_slot: "bag", custom: true,
      effect: effect, value: Math.max(0, +d.value || 0),
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (effect === "heal") {
      var mu = Math.max(1, +d.max_uses || 1);
      if (mu > 1) { item.max_uses = mu; item.uses_left = mu; }
    }
    return item;
  }
  function validatePotionDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (POTION_EFFECTS.indexOf(d.effect) < 0) return { ok: false, msg: "efeito inválido" };
    return { ok: true };
  }
  function suggestPricePotion(item) {
    var mu = Math.max(1, +item.max_uses || 1);
    return Math.max(1, Math.round(K_POTION * (+item.value || 0) * mu));
  }
  function serializeThrowable(d) {
    var alvo = THROW_TARGETS.indexOf(d.alvo) >= 0 ? d.alvo : "ataque_alvo";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "💥", item_type: "throwable", item_slot: "bag",
      effect: "throwable", custom: true,
      alvo: alvo, alcance: Math.max(1, Math.min(12, +d.alcance || 4)),
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (d.tem_dano) {
      item.dano = buildDie(d.die_qtd, d.die_faces);
      item.elemento = THROW_ELEMENTS.indexOf(d.elemento) >= 0 ? d.elemento : "fogo";
    }
    if (alvo === "area") {
      item.area_raio = Math.max(1, Math.min(3, +d.area_raio || 1));
      if (+d.save_cd) item.save_cd = Math.max(5, Math.min(25, +d.save_cd));
    }
    if (d.em_chamas) {
      item.em_chamas = true;
      item.chamas_dur = buildDie(d.chamas_qtd, d.chamas_faces || 4);
      item.chamas_agua_apaga = d.chamas_agua_apaga !== false;
    }
    return item;
  }
  function validateThrowableDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (d.alvo && THROW_TARGETS.indexOf(d.alvo) < 0) return { ok: false, msg: "alvo inválido" };
    if (d.tem_dano && FACES.indexOf(+d.die_faces) < 0) return { ok: false, msg: "dado de dano inválido" };
    return { ok: true };
  }
  function suggestPriceThrowable(item) {
    var p = K_THROW * dieAvg(item.dano);
    if (item.alvo === "area") p *= (1 + 0.5 * Math.max(1, +item.area_raio || 1));
    if (item.em_chamas) p += 10;
    return Math.max(1, Math.round(p));
  }
  var api = { slugify: slugify, buildDie: buildDie, dieAvg: dieAvg,
              suggestPrice: suggestPrice, serializeWeapon: serializeWeapon,
              validateDraft: validateDraft, ELEM: ELEM, CATS: CATS, FACES: FACES,
              serializeArmor: serializeArmor, suggestPriceArmor: suggestPriceArmor,
              validateArmorDraft: validateArmorDraft,
              ARMOR_CATS: ARMOR_CATS, BONUS_EFFECTS: BONUS_EFFECTS, RESIST_TYPES: RESIST_TYPES,
              serializeAccessory: serializeAccessory,
              validateAccessoryDraft: validateAccessoryDraft,
              suggestPriceAccessory: suggestPriceAccessory,
              serializePotion: serializePotion,
              validatePotionDraft: validatePotionDraft,
              suggestPricePotion: suggestPricePotion,
              POTION_EFFECTS: POTION_EFFECTS,
              serializeThrowable: serializeThrowable,
              validateThrowableDraft: validateThrowableDraft,
              suggestPriceThrowable: suggestPriceThrowable,
              THROW_TARGETS: THROW_TARGETS, THROW_ELEMENTS: THROW_ELEMENTS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.EDITOR_ITEMS_LOGIC = api;
})(typeof window !== "undefined" ? window : null);
