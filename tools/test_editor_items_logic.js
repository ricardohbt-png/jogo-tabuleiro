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

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
