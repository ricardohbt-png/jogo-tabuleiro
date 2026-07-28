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

// Fase G — arremessáveis
check("THROW_TARGETS tem os 2 modos",
  L.THROW_TARGETS.indexOf("ataque_alvo") >= 0 && L.THROW_TARGETS.indexOf("area") >= 0);
check("THROW_ELEMENTS tem fogo e acido",
  L.THROW_ELEMENTS.indexOf("fogo") >= 0 && L.THROW_ELEMENTS.indexOf("acido") >= 0);
const thAlvo = L.serializeThrowable({name:"Frasco Ardente", alvo:"ataque_alvo", alcance:5,
  tem_dano:true, die_qtd:2, die_faces:6, elemento:"fogo",
  em_chamas:true, chamas_qtd:1, chamas_faces:4, chamas_agua_apaga:true,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:25});
check("serializeThrowable id/slot/effect",
  thAlvo.id === "frasco_ardente" && thAlvo.item_slot === "bag"
  && thAlvo.effect === "throwable" && thAlvo.item_type === "throwable");
check("serializeThrowable alvo/alcance", thAlvo.alvo === "ataque_alvo" && thAlvo.alcance === 5);
check("serializeThrowable dano/elemento", thAlvo.dano === "2d6" && thAlvo.elemento === "fogo");
check("serializeThrowable em chamas", thAlvo.em_chamas === true
  && thAlvo.chamas_dur === "1d4" && thAlvo.chamas_agua_apaga === true);
check("single-target não grava area_raio/save_cd",
  thAlvo.area_raio === undefined && thAlvo.save_cd === undefined);
const thArea = L.serializeThrowable({name:"Bomba X", alvo:"area", alcance:4, area_raio:2, save_cd:13,
  tem_dano:true, die_qtd:3, die_faces:6, elemento:"explosao",
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:60});
check("area grava raio e save_cd", thArea.alvo === "area" && thArea.area_raio === 2 && thArea.save_cd === 13);
check("area sem chamas nao grava chamas_dur", thArea.chamas_dur === undefined);
const thSemDano = L.serializeThrowable({name:"Frasco Vazio", alvo:"ataque_alvo",
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:5});
check("sem dano nao grava dano/elemento",
  thSemDano.dano === undefined && thSemDano.elemento === undefined);
check("alcance default 4", thSemDano.alcance === 4);
check("emoji default 💥", thSemDano.emoji === "💥");
check("alvo invalido normaliza p/ ataque_alvo",
  L.serializeThrowable({name:"Y", alvo:"parede"}).alvo === "ataque_alvo");
check("alcance clampado em 12", L.serializeThrowable({name:"Y", alcance:99}).alcance === 12);
check("validateThrowableDraft aceita valido",
  L.validateThrowableDraft({name:"X", alvo:"area", tem_dano:true, die_faces:6}).ok);
check("validateThrowableDraft rejeita sem nome",
  !L.validateThrowableDraft({name:"", alvo:"area"}).ok);
check("validateThrowableDraft rejeita dado invalido",
  !L.validateThrowableDraft({name:"X", alvo:"area", tem_dano:true, die_faces:7}).ok);
check("suggestPriceThrowable cresce com o dado",
  L.suggestPriceThrowable({dano:"3d6"}) > L.suggestPriceThrowable({dano:"1d6"}));
check("suggestPriceThrowable cresce com area",
  L.suggestPriceThrowable({dano:"2d6", alvo:"area", area_raio:2}) > L.suggestPriceThrowable({dano:"2d6"}));

// Fase H — venenos
check("POISON_OPS tem as 5 operações",
  L.POISON_OPS.length === 5 && L.POISON_OPS.indexOf("dano") >= 0
  && L.POISON_OPS.indexOf("petrificar") >= 0 && L.POISON_OPS.indexOf("cegar") >= 0);
check("POISON_ATTRS / POISON_PENS / POISON_SAVES",
  L.POISON_ATTRS.indexOf("forca") >= 0 && L.POISON_PENS.indexOf("ataque") >= 0
  && L.POISON_SAVES.indexOf("fortitude") >= 0);
const pDano = L.serializePoison({name:"Bile Ácida", operacao:"dano", save:"fortitude",
  dificuldade:12, anula:true, dur_qtd:1, dur_faces:6,
  dano_fixo:false, dano_qtd:1, dano_faces:4, modelo_save:"aplicacao",
  descricao:"Corrói por dentro.",
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:20});
check("serializePoison id/slot/effect/veneno_id",
  pDano.id === "bile_acida" && pDano.item_slot === "bag"
  && pDano.effect === "coat_poison" && pDano.item_type === "poison");
check("serializePoison dano por dado", pDano.operacao === "dano" && pDano.dano === "1d4");
check("serializePoison duracao", pDano.duracao === "1d6");
check("serializePoison save_aplicacao", pDano.save_aplicacao === true
  && pDano.save_neutraliza_por_rodada === undefined);
check("serializePoison guarda descricao", pDano.descricao === "Corrói por dentro.");
const pRodada = L.serializePoison({name:"X", operacao:"dano", dano_fixo:true, dano_valor:2,
  modelo_save:"rodada", dur_qtd:1, dur_faces:4});
check("dano fixo vira número", pRodada.dano === 2);
check("modelo rodada grava save_neutraliza_por_rodada",
  pRodada.save_neutraliza_por_rodada === true && pRodada.save_aplicacao === undefined);
const pRed = L.serializePoison({name:"Y", operacao:"reduzir", atributo:"constituicao",
  val_qtd:1, val_faces:4, dur_qtd:1, dur_faces:6});
check("reduzir grava atributo e valor",
  pRed.operacao === "reduzir" && pRed.atributo === "constituicao" && pRed.valor === "1d4");
const pPen = L.serializePoison({name:"Z", operacao:"penalidade",
  atributos:[{chave:"ataque", valor:2},{chave:"movimento", valor:1},{chave:"xpto", valor:9}],
  dur_qtd:1, dur_faces:6});
check("penalidade normaliza pares negativos",
  JSON.stringify(pPen.atributos) === JSON.stringify([["ataque",-2],["movimento",-1]]));
const pPet = L.serializePoison({name:"W", operacao:"petrificar", dur_qtd:1, dur_faces:4,
  durfalha_qtd:1, durfalha_faces:4, penalidade_falha:[{chave:"movimento", valor:1}]});
check("petrificar grava duracao_falha e penalidade_falha",
  pPet.duracao_falha === "1d4"
  && JSON.stringify(pPet.penalidade_falha) === JSON.stringify([["movimento",-1]]));
const pCeg = L.serializePoison({name:"V", operacao:"cegar", dur_qtd:1, dur_faces:4,
  penalidade_ataque:4, bloqueia_distancia:true});
check("cegar grava penalidade_ataque negativa e bloqueio",
  pCeg.penalidade_ataque === -4 && pCeg.bloqueia_distancia === true);
check("icone default ☠️", L.serializePoison({name:"Q", operacao:"dano"}).emoji === "☠️");
check("validatePoisonDraft aceita valido",
  L.validatePoisonDraft({name:"X", operacao:"dano"}).ok);
check("validatePoisonDraft rejeita sem nome",
  !L.validatePoisonDraft({name:"", operacao:"dano"}).ok);
check("validatePoisonDraft rejeita operacao invalida",
  !L.validatePoisonDraft({name:"X", operacao:"explodir"}).ok);
check("validatePoisonDraft rejeita reduzir sem atributo valido",
  !L.validatePoisonDraft({name:"X", operacao:"reduzir", atributo:"carisma"}).ok);
check("validatePoisonDraft rejeita penalidade sem pares",
  !L.validatePoisonDraft({name:"X", operacao:"penalidade", atributos:[]}).ok);
check("suggestPricePoison cresce com a CD",
  L.suggestPricePoison({dificuldade:16}) > L.suggestPricePoison({dificuldade:8}));

// Antídotos — efeitos de cura de status com dado de imunidade
check("POTION_EFFECTS inclui os 3 efeitos de cura",
  L.POTION_EFFECTS.indexOf("cure_poison") >= 0
  && L.POTION_EFFECTS.indexOf("cure_petrification") >= 0
  && L.POTION_EFFECTS.indexOf("cure_disease") >= 0);
const cura = L.serializePotion({name:"Antídoto Forte", effect:"cure_poison",
  imun_qtd:2, imun_faces:6,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:30});
check("serializePotion cura grava effect", cura.effect === "cure_poison");
check("serializePotion cura grava imunidade_dado", cura.imunidade_dado === "2d6");
check("cura não grava doses", cura.max_uses === undefined);
const heal = L.serializePotion({name:"Cura", effect:"heal", value:10});
check("heal não grava imunidade_dado", heal.imunidade_dado === undefined);

// Estoque por cidade — qual loja recebe cada tipo de item
check("arma vai para o ferreiro", L.shopIdForItemType("weapon") === "ferreiro_weapon");
check("armadura e escudo vão para o ferreiro",
  L.shopIdForItemType("armor") === "ferreiro_armor"
  && L.shopIdForItemType("shield") === "ferreiro_armor");
check("consumíveis e acessórios vão para o mercador",
  ["ring","boots","potion","throwable","poison"].every(t => L.shopIdForItemType(t) === "mercador"));
check("tipo desconhecido cai no mercador", L.shopIdForItemType("xpto") === "mercador");
check("sem tipo assume arma", L.shopIdForItemType() === "ferreiro_weapon");
check("slugify exportado", L.slugify("Ensaio sobre a Cegueira") === "ensaio_sobre_a_cegueira");

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
