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
// pontos de corrosão → corrosao_resistente = pontos - 3 (3 normal → 0, 5 prata → 2)
check("corrosao 3 pontos => resistente 0", L.serializeWeapon(Object.assign({}, draft, {corrosao_pontos:3})).corrosao_resistente === 0);
check("corrosao 5 pontos => resistente 2 (prata)", L.serializeWeapon(Object.assign({}, draft, {corrosao_pontos:5})).corrosao_resistente === 2);
check("corrosao ausente => resistente 0 (default 3 pts)", L.serializeWeapon(draft).corrosao_resistente === 0);

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
