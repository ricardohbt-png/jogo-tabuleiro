// Roda da raiz: node tools/test_editor_items_logic.js
const L = require("./editor_items_logic.js");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

check("slugify remove acentos e espacos", L.slugify("Espada Flamejante!") === "espada_flamejante");
check("buildDie monta NdX", L.buildDie(2, 6) === "2d6");
check("suggestPrice cresce com o dado", L.suggestPrice({die:"1d10"}) > L.suggestPrice({die:"1d4"}));
check("suggestPrice soma dano elemental",
      L.suggestPrice({die:"1d6", extra_damages:[{die:"1d6",type:"fire"}]}) > L.suggestPrice({die:"1d6"}));

const draft = {name:"Espada Flamejante", emoji:"⚔️", die_qtd:1, die_faces:8,
               categoria:"cortante", stat:"str_", manejo:"corpo",
               damage_bonus:1, extra_damages:[{die:"1d6", type:"fire"}],
               allowed_classes:[], disponibilidade:{loja:true,baus:true,loot_monstro:false}, price:40};
const item = L.serializeWeapon(draft);
check("serializeWeapon gera id", item.id === "espada_flamejante");
check("serializeWeapon monta die", item.die === "1d8");
check("serializeWeapon marca item_type weapon", item.item_type === "weapon");
check("validateDraft aceita valido", L.validateDraft(draft).ok);
check("validateDraft rejeita sem nome", !L.validateDraft(Object.assign({}, draft, {name:""})).ok);

// atk_bonus e damage_bonus são independentes (podem coexistir)
const doisBonus = L.serializeWeapon(Object.assign({}, draft, {atk_bonus:2, damage_bonus:3}));
check("serializeWeapon mantem atk_bonus e damage_bonus juntos", doisBonus.atk_bonus === 2 && doisBonus.damage_bonus === 3);
// corrosão em dois eixos: níveis livres (N) + níveis com penalidade (M)
const corr = L.serializeWeapon(Object.assign({}, draft, {corrosao_livres:2, corrosao_penalidade:3}));
check("corrosao_livres => corrosao_resistente", corr.corrosao_resistente === 2);
check("corrosao_penalidade => corrosao_niveis_penalidade", corr.corrosao_niveis_penalidade === 3);
check("defaults de corrosao (0 livres, 2 penalidade)",
      L.serializeWeapon(draft).corrosao_resistente === 0 && L.serializeWeapon(draft).corrosao_niveis_penalidade === 2);
// material: metal por padrão, madeira quando escolhido
check("material default metal", L.serializeWeapon(draft).material === "metal");
check("material madeira", L.serializeWeapon(Object.assign({}, draft, {material:"madeira"})).material === "madeira");
// alcance editável + munição só em arma à distância
const rng = L.serializeWeapon(Object.assign({}, draft, {manejo:"distancia", range:7, ammo:"flechas"}));
check("alcance à distância editável", rng.range === 7);
check("munição gravada em arma à distância", rng.ammo === "flechas");
check("munição ignorada em arma corpo a corpo",
      L.serializeWeapon(Object.assign({}, draft, {manejo:"corpo", ammo:"flechas"})).ammo === undefined);

// ── Armadura/Escudo ──
const adraft = {name:"Cota Teste", emoji:"🛡️", item_type:"armor", ac_bonus:4,
  armor_category:"media", materiais:{organic:false, metal:true},
  corrosao_livres:0, corrosao_penalidade:2,
  bonuses:[{effect:"maxhp", value:5}], allowed_classes:[],
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:120};
const aitem = L.serializeArmor(adraft);
check("serializeArmor gera id", aitem.id === "cota_teste");
check("serializeArmor item_type armor", aitem.item_type === "armor");
check("serializeArmor ac_bonus", aitem.ac_bonus === 4);
check("serializeArmor materiais lista", JSON.stringify(aitem.corrosion_materials) === JSON.stringify(["metal"]));
check("serializeArmor N/M", aitem.corrosao_resistente === 0 && aitem.corrosao_niveis_penalidade === 2);
check("serializeArmor bonuses", aitem.bonuses.length === 1 && aitem.bonuses[0].effect === "maxhp");
const sdraft = Object.assign({}, adraft, {name:"Escudo T", item_type:"shield", armor_category:"media"});
const sitem = L.serializeArmor(sdraft);
check("escudo item_type shield", sitem.item_type === "shield");
check("escudo zera categoria", sitem.armor_category == null);
check("escudo mantém material", JSON.stringify(sitem.corrosion_materials) === JSON.stringify(["metal"]));
check("validateArmorDraft aceita válido", L.validateArmorDraft(adraft).ok);
check("validateArmorDraft rejeita sem nome", !L.validateArmorDraft(Object.assign({}, adraft, {name:""})).ok);
check("suggestPriceArmor cresce com CA", L.suggestPriceArmor({ac_bonus:6}) > L.suggestPriceArmor({ac_bonus:2}));
// bônus de atributo passam por serializeArmor (Fase B)
const aitem2 = L.serializeArmor(Object.assign({}, adraft, {
  bonuses:[{effect:"str_", value:2}, {effect:"con_", value:1}, {effect:"atk", value:9}]}));
check("serializeArmor mantém bônus de atributo", aitem2.bonuses.length === 2
  && aitem2.bonuses[0].effect === "str_" && aitem2.bonuses[1].effect === "con_");
check("serializeArmor filtra efeito não permitido", !aitem2.bonuses.some(function(b){return b.effect==="atk";}));

// bônus resist preserva type; type inválido descartado (Fase C)
const aitemR = L.serializeArmor(Object.assign({}, adraft, {bonuses:[
  {effect:"resist", type:"fire", value:0},
  {effect:"resist", type:"cold", value:3},
  {effect:"resist", type:"trevas", value:0},
  {effect:"spd", value:-1}]}));
check("serializeArmor mantém resist com type/value",
  JSON.stringify(aitemR.bonuses.filter(function(b){return b.effect==="resist";}))
  === JSON.stringify([{effect:"resist",type:"fire",value:0},{effect:"resist",type:"cold",value:3}]));
check("serializeArmor descarta resist de tipo inválido",
  !aitemR.bonuses.some(function(b){return b.type==="trevas";}));
check("serializeArmor mantém bônus escalar junto do resist",
  aitemR.bonuses.some(function(b){return b.effect==="spd" && b.value===-1;}));

// bônus escalar initiative passa por serializeArmor (Fase D)
const aitemI = L.serializeArmor(Object.assign({}, adraft, {bonuses:[{effect:"initiative", value:3}]}));
check("serializeArmor mantém initiative", aitemI.bonuses.length === 1
  && aitemI.bonuses[0].effect === "initiative" && aitemI.bonuses[0].value === 3);

// Fase E — acessórios (anéis + botas)
check("BONUS_EFFECTS inclui atk_bonus", L.BONUS_EFFECTS.indexOf("atk_bonus") >= 0);
const ring = L.serializeAccessory({name:"Anel de Vigor", item_type:"ring",
  bonuses:[{effect:"maxhp",value:5},{effect:"atk_bonus",value:1},{effect:"atk",value:9}],
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:30});
check("serializeAccessory gera id+slot ring",
  ring.id === "anel_de_vigor" && ring.item_slot === "ring" && ring.kind === "ring");
check("serializeAccessory mantém atk_bonus",
  ring.bonuses.some(function(b){return b.effect==="atk_bonus"&&b.value===1;}));
check("serializeAccessory filtra efeito atk cru",
  !ring.bonuses.some(function(b){return b.effect==="atk";}));
check("anel não tem corrosão", ring.corrosion_materials === undefined);
const boot = L.serializeAccessory({name:"Botas de Ferro", item_type:"boots",
  bonuses:[{effect:"spd",value:1}], materiais:{metal:true,organic:false},
  corrosao_livres:1, corrosao_penalidade:3,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:20});
check("botas slot boots + material metal",
  boot.item_slot === "boots" && boot.corrosion_materials.indexOf("metal") >= 0);
check("botas N/M gravados",
  boot.corrosao_resistente === 1 && boot.corrosao_niveis_penalidade === 3);
check("botas emoji default 👢", boot.emoji === "👢");
check("validateAccessoryDraft aceita com nome", L.validateAccessoryDraft({name:"X"}).ok);
check("validateAccessoryDraft rejeita sem nome", !L.validateAccessoryDraft({name:""}).ok);
check("suggestPriceAccessory soma bonuses",
  L.suggestPriceAccessory({bonuses:[{value:2},{value:3}]}) > 0);

// Fase F — poções
check("POTION_EFFECTS tem os 3 efeitos",
  L.POTION_EFFECTS.indexOf("heal") >= 0 && L.POTION_EFFECTS.indexOf("regeneration") >= 0
  && L.POTION_EFFECTS.indexOf("atk_bonus") >= 0);
const potHeal = L.serializePotion({name:"Poção Robusta", item_type:"potion",
  effect:"heal", value:25, max_uses:3,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:30});
check("serializePotion gera id + item_slot bag + item_type potion",
  potHeal.id === "pocao_robusta" && potHeal.item_slot === "bag" && potHeal.item_type === "potion");
check("serializePotion heal grava value", potHeal.value === 25);
check("serializePotion heal multi-dose grava max_uses+uses_left",
  potHeal.max_uses === 3 && potHeal.uses_left === 3);
check("serializePotion emoji default 🧪", L.serializePotion({name:"X",effect:"heal"}).emoji === "🧪");
const potRegen = L.serializePotion({name:"Regen", item_type:"potion", effect:"regeneration", value:10,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:16});
check("serializePotion regen sem doses", potRegen.effect === "regeneration" && potRegen.max_uses === undefined);
const potElix = L.serializePotion({name:"Elixir", item_type:"potion", effect:"atk_bonus", value:3, max_uses:5,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:12});
check("serializePotion não-heal ignora doses", potElix.max_uses === undefined && potElix.uses_left === undefined);
const potBad = L.serializePotion({name:"Ruim", item_type:"potion", effect:"teleporte", value:1,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:1});
check("serializePotion normaliza efeito inválido p/ heal", potBad.effect === "heal");
check("validatePotionDraft aceita heal", L.validatePotionDraft({name:"X", effect:"heal"}).ok);
check("validatePotionDraft rejeita sem nome", !L.validatePotionDraft({name:"", effect:"heal"}).ok);
check("validatePotionDraft rejeita efeito inválido", !L.validatePotionDraft({name:"X", effect:"voar"}).ok);
check("suggestPricePotion cresce com value", L.suggestPricePotion({value:20,max_uses:1}) > L.suggestPricePotion({value:5,max_uses:1}));
check("suggestPricePotion cresce com doses", L.suggestPricePotion({value:10,max_uses:3}) > L.suggestPricePotion({value:10,max_uses:1}));

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
