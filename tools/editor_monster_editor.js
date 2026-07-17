/* Editor de criaturas: cria cópias independentes e monstros novos. */
(function () {
  "use strict";
  const root = document.getElementById("monster-editor-view");
  let draft = null, idManual = false, summaryRenderer = null;
  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const copy = v => JSON.parse(JSON.stringify(v));
  const slug = v => String(v || "monstro").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "monstro";
  const mod = v => Math.floor((Number(v || 10) - 10) / 2);
  const n = (v, fallback=0) => Number.isFinite(Number(v)) ? Number(v) : fallback;
  const all = () => (((window.EDITOR_CATALOG || {}).monsters || []).concat(window.EDITOR_CUSTOM_MONSTERS || []));
  const customTypes = () => new Set((window.EDITOR_CUSTOM_MONSTERS || []).map(m => m.type));
  const options = (items, value, label) => items.map(x => `<option value="${esc(x.value)}"${x.value === value ? " selected" : ""}>${esc(label(x))}</option>`).join("");
  const DAMAGE_TRAITS = [
    {type:"physical",categoria:"cortante",name:"Cortante"}, {type:"physical",categoria:"contundente",name:"Contundente"}, {type:"physical",categoria:"perfurante",name:"Perfurante"},
    {type:"fire",name:"Fogo"}, {type:"cold",name:"Frio / gelo"}, {type:"lightning",name:"Eletricidade"}, {type:"poison",name:"Veneno"}, {type:"holy",name:"Sagrado / luz"}, {type:"magic",name:"Mágico"}, {type:"acid",name:"Ácido"},
  ];
  const ATTACK_DAMAGE_TYPES = [
    {value:"physical", name:"Físico"}, {value:"fire", name:"Fogo"},
    {value:"cold", name:"Frio / gelo"}, {value:"lightning", name:"Eletricidade"},
    {value:"poison", name:"Veneno"}, {value:"holy", name:"Sagrado / luz"},
    {value:"magic", name:"Mágico"}, {value:"acid", name:"Ácido"}, {value:"water", name:"Água"},
  ];
  const AI_PROFILES = [
    {id:"agressivo", name:"Agressivo", desc:"Foca um alvo, persegue quem foge e usa sua ação ofensiva mais forte."},
    {id:"tatico", name:"Tático", desc:"Prioriza inimigos vulneráveis e prefere atacar à distância quando possível."},
    {id:"cacador", name:"Caçador", desc:"Busca alvos feridos para finalizar."},
    {id:"conjurador", name:"Conjurador", desc:"Prioriza magias e mantém a pressão à distância."},
    {id:"emboscador", name:"Emboscador", desc:"Tenta atacar com surpresa e aproveitar ocultação."},
    {id:"protetor", name:"Protetor", desc:"Combate próximo aos aliados e responde a ameaças."},
    {id:"covarde", name:"Covarde", desc:"Evita riscos quando está muito ferido."},
    {id:"irracional", name:"Irracional", desc:"Ataca sem planejamento o alvo disponível."},
    {id:"sentinela", name:"Sentinela", desc:"Só reage a inimigos dentro de sua área de guarda."},
  ];
  const AI_TACTICS = [
    ["focar_feridos","Focar feridos"], ["perseguir_fugitivos","Perseguir fugitivos"],
    ["manter_distancia","Manter distância"], ["usar_habilidades_fortes","Usar habilidades fortes"],
    ["usar_veneno","Usar veneno"], ["usar_bombas","Usar bombas"],
    ["proteger_aliados","Proteger aliados"], ["recuar_pouca_vida","Recuar com pouca vida"],
    ["ocultar_se","Ocultar-se quando possível"], ["prender_alvo","Prender alvo"],
  ];
  const SUBTIPOS = [
    {id:"construto", nome:"Construto", desc:"Imune a paralisia, petrificação, controle mental, medo, necrótico, veneno, gases, doença e sono."},
    {id:"morto_vivo", nome:"Morto-Vivo", desc:"Imune a veneno, gases, necrótico, doença, sono, encantamento e medo; sagrado dobrado."},
    {id:"animal", nome:"Animal", desc:"Sem particularidades gerais."},
    {id:"abissal", nome:"Abissal", desc:"Imune a veneno; metade de fogo, frio e eletricidade; sagrado dobrado."},
    {id:"vegetal", nome:"Vegetal", desc:"Dano de fogo ×1,5."},
    {id:"raca_padrao", nome:"Raça Padrão", desc:"Sem particularidades gerais."},
  ];
  const traitKey = t => `${t.type}|${t.categoria || ""}`;
  // Efeitos negativos não entram como poder ofensivo: viram fraquezas mecânicas.
  const NEGATIVE_ABILITY_WEAKNESSES = {
    fraqueza_magica: {type:"save_penalty",save:"vontade",bonus_flat:-2,em_magia:true,descricao:"Fraqueza mágica: -2 em Vontade contra controle de mortos-vivos"},
    mente_limitada: {type:"save_penalty",save:"vontade",bonus_flat:-1,em_magia:true,descricao:"Mente limitada: -1 em Vontade contra efeitos mentais"},
    mente_fraca: {type:"save_penalty",save:"vontade",bonus_flat:-2,em_magia:true,descricao:"Mente fraca: -2 em Vontade contra controle mental"},
    mente_bruta: {type:"save_penalty",save:"vontade",bonus_flat:-2,em_magia:true,descricao:"Mente bruta: -2 em Vontade contra controle mental"},
    concentracao_fragil: {type:"concentracao_fragil",descricao:"Concentração frágil: ao sofrer dano, pode perder a próxima magia"},
    concentracao_sombria: {type:"concentracao_fragil",descricao:"Concentração sombria: ao sofrer dano, testa Vontade ou perde a magia"},
    essencia_profana: {type:"holy",multiplier:2,descricao:"Essência profana: dano sagrado/luz dobrado"},
    furia_cega: {type:"ca_condicional",bonus_flat:-1,descricao:"Fúria cega: após sofrer dano, ganha dano mas perde 1 CA"},
    covardia_kobold: {type:"moral_fragil",descricao:"Covardia instintiva: pode entrar em medo sob pressão"},
    corpo_pesado: {type:"corpo_pesado",descricao:"Corpo Pesado: ao falhar em Reflexos, recebe +1 dano daquele efeito."},
    lento_previsivel: {type:"ca_condicional",bonus_flat:-2,descricao:"Lento e Previsível: ao errar um ataque, perde 2 CA até o próximo turno."},
  };
  const negativeAbility = id => Object.prototype.hasOwnProperty.call(NEGATIVE_ABILITY_WEAKNESSES, id);
  const mechanicsFor = ids => (ids || []).filter(negativeAbility).map(id => Object.assign({source_ability:id}, NEGATIVE_ABILITY_WEAKNESSES[id]));
  const sameWeakness = (a,b) => a.type === b.type && a.categoria === b.categoria && Number(a.bonus_flat || 0) === Number(b.bonus_flat || 0) && Number(a.multiplier || 0) === Number(b.multiplier || 0) && a.save === b.save;
  function abilityLibrary() {
    const map = new Map();
    // Catálogo completo: habilidades não mágicas dos heróis, da Guilda e do
    // bestiário. Magias continuam exclusivamente na aba Magias.
    ((window.EDITOR_CATALOG || {}).monster_abilities || []).forEach(a => {
      if (a.id && a.id !== "ponto_vulneravel" && a.action_type !== "magia" && !map.has(a.id)) map.set(a.id, a);
    });
    // Magias possuem sua própria aba; não devem parecer habilidades genéricas.
    ((window.EDITOR_CATALOG || {}).monsters || []).forEach(m => (m.special_abilities || []).forEach(a => { if (a.id && a.id !== "ponto_vulneravel" && a.action_type !== "magia" && !map.has(a.id)) map.set(a.id, a); }));
    return [...map.values()];
  }
  const spellLibrary = () => ((window.EDITOR_CATALOG || {}).spells || []);
  function inheritedSpells(m) {
    if (Array.isArray(m.monster_spells) && m.monster_spells.length) return copy(m.monster_spells);
    // Compatibilidade com as fichas antigas: a migração ocorre sem apagar a
    // regra de IA específica que ainda consulta special_abilities.
    return (m.special_abilities || []).filter(a => a.action_type === "magia")
      .map(a => ({id:a.id, limit_mode:a.cooldown_turns != null ? "cooldown" : "encounter",
        uses_per_combat:Math.max(1, n(a.uses_per_combat, 1)), cooldown_turns:Math.max(1, n(a.cooldown_turns, 1))}));
  }
  function aiOptions() {
    return [...new Set(((window.EDITOR_CATALOG || {}).monsters || []).map(m => m.ai_type).filter(Boolean))].sort();
  }
  function abilityHint(a) {
    const parts = [a.descricao || a.description];
    if (a.action_type) parts.push(a.action_type === "passiva" ? "Passiva." : "Ação ativa.");
    if (a.uses_per_combat != null) parts.push(`${a.uses_per_combat} uso(s) por combate.`);
    if (a.cooldown != null) parts.push(`Recarga: ${a.cooldown}.`);
    if (a.range != null) parts.push(`Alcance ${a.range}.`);
    if (a.damage) parts.push(`Dano: ${a.damage}.`);
    if (a.dc) parts.push(`CD ${a.dc}${a.save ? ` (${a.save})` : ""}.`);
    if (a.effect) parts.push(`Efeito: ${String(a.effect).replace(/_/g, " ")}.`);
    return parts.filter(Boolean).join(" ") || "A habilidade não possui uma descrição adicional cadastrada.";
  }
  function weaknessHint(w) {
    if (w.descricao) return w.descricao;
    const kind = String(w.categoria || w.type || "dano").replace(/_/g, " ");
    if (Number(w.multiplier) > 1) return `Recebe ${w.multiplier}× dano de ${kind}.`;
    if (Number(w.bonus_flat) > 0) return `Recebe +${w.bonus_flat} de dano de ${kind}.`;
    if (w.type === "save_penalty") return `Sofre penalidade em testes de ${w.save || "resistência"}.`;
    return `Possui vulnerabilidade a ${kind}.`;
  }
  function weaknessLibrary() {
    return DAMAGE_TRAITS.map(t => Object.assign({}, t, {bonus_flat:1, descricao:`Fraqueza a ${t.name}: recebe +1 dano`}));
  }
  const weaknessKey = w => `${w.type || ""}|${w.categoria || ""}|${w.save || ""}`;
  function attackBonus(a, m) {
    const attr = a.attack_attribute === "dex" ? "dex" : "str_";
    return n(a.base_attack_bonus, n(m.base_attack_bonus, 0)) + mod(m[attr]) + n(m.equipment_attack_bonus, 0);
  }
  function attackDamage(a, m) {
    const attr = a.attack_attribute === "dex" ? "dex" : "str_";
    const bonus = a.apply_attribute_damage === false ? 0 : mod(m[attr]);
    return `${a.damage || "1d4"}${bonus ? (bonus > 0 ? "+" : "") + bonus : ""}`;
  }
  const visionRadius = m => Math.max(1, 6 + n(m.vision_base, 0) + Math.floor((mod(m.dex) + mod(m.int_)) / 2));
  function equipmentPreview(monster) {
    const m = copy(monster);
    if (!m.equipment_enabled) return m;
    const catalog = new Map(((window.EDITOR_CATALOG || {}).items || []).map(item => [item.id, item]));
    const items = (m.equipped_items || []).map(id => catalog.get(id)).filter(Boolean);
    const weapon = items.find(item => item.die);
    if (weapon) {
      const configuredAttack = (m.attacks || [])[0] || {};
      const attr = weapon.stat === "dex" ? "dex" : "str_";
      m.attacks = [{name:weapon.name, damage:weapon.die, damage_types:["physical"], attack_attribute:attr,
        apply_attribute_damage:true, base_attack_bonus:n(m.base_attack_bonus, 0), num_attacks:1,
        range:n(weapon.range, 0), categoria:weapon.categoria, on_hit:configuredAttack.on_hit,
        on_hit_effect:configuredAttack.on_hit_effect,
        poison_dc:configuredAttack.poison_dc, extra_damage:configuredAttack.extra_damage,
        extra_damage_types:configuredAttack.extra_damage_types || []}];
    }
    m.ac += items.reduce((sum, item) => sum + n(item.ac_bonus, 0) + (item.effect === "def_" ? n(item.value, 0) : 0), 0);
    m.hp += items.reduce((sum, item) => sum + (item.effect === "maxhp" ? n(item.value, 0) : 0), 0);
    m.movement += items.reduce((sum, item) => sum + (item.effect === "spd" ? n(item.value, 0) : 0), 0);
    m.equipment_attack_bonus = items.reduce((sum, item) => sum + (item.effect === "atk" ? n(item.value, 0) : 0), 0);
    return m;
  }
  function normalize(m, isCustom) {
    const out = copy(m || {});
    out.original_type = isCustom ? out.type : "";
    out.type = isCustom ? out.type : `${slug(out.name || "monstro")}_customizado`;
    out.image = String(out.image || out.type).trim();
    out.portrait = String(out.portrait || out.type).trim();
    out.str_ = n(out.str_, 10); out.dex = n(out.dex, 10); out.con_ = n(out.con_, 10); out.int_ = n(out.int_, 10);
    out.movement = out.movement_exception ? n(out.movement, 6) : 6;
    out.vision_base = Math.max(-30, Math.min(30, n(out.vision_base, 0)));
    out.visao_escuro = !!(out.visao_escuro || out.darkvision_range);
    out.caster_level = Math.max(1, n(out.caster_level, 1));
    out.natural_armor = Math.max(0, n(out.natural_armor, n(out.ac, 10) - 10 - mod(out.dex)));
    out.base_hp = out.base_hp != null ? n(out.base_hp) : Math.max(1, n(out.hp, 10) - mod(out.con_));
    out.fort_base = out.fort_base != null ? n(out.fort_base) : n(out.fort, 0) - mod(out.con_);
    out.ref_base = out.ref_base != null ? n(out.ref_base) : n(out.ref_, 0) - mod(out.dex);
    out.will_base = out.will_base != null ? n(out.will_base) : n(out.will, 0) - mod(out.int_);
    out.hp = Math.max(1, out.base_hp + mod(out.con_));
    out.fort = out.fort_base + mod(out.con_); out.ref_ = out.ref_base + mod(out.dex); out.will = out.will_base + mod(out.int_);
    out.ac = Math.max(1, 10 + mod(out.dex) + out.natural_armor);
    const rawSize = Array.isArray(out.size) ? out.size : [1, 1];
    out.size = [Math.max(1, Math.min(4, n(rawSize[0], 1))), Math.max(1, Math.min(4, n(rawSize[1], 1)))];
    out.oriented = !!out.oriented && out.size[0] * out.size[1] > 1;
    const base = out.base_attack_bonus != null ? n(out.base_attack_bonus) : n(((out.attacks || [])[0] || {}).atk_bonus, n(out.atk_bonus));
    const first = (out.attacks || [])[0] || {};
    out.base_attack_bonus = out.base_attack_bonus != null ? n(out.base_attack_bonus) : base - mod(first.range ? out.dex : out.str_);
    out.attacks = (out.attacks && out.attacks.length ? out.attacks : [{name:"Ataque", damage:out.damage || "1d4", num_attacks:1}]).map(a => Object.assign({}, a, { attack_attribute:a.attack_attribute || (a.range ? "dex" : "str_"), apply_attribute_damage:a.apply_attribute_damage !== false, base_attack_bonus:a.base_attack_bonus != null ? n(a.base_attack_bonus) : out.base_attack_bonus, damage_types:Array.isArray(a.damage_types) && a.damage_types.length ? a.damage_types : ["physical"] }));
    out.monster_spells = inheritedSpells(out);
    const allAbilityIds = (out.special_abilities || []).filter(a => a.action_type !== "magia").map(a => a.id).filter(Boolean);
    out.monster_abilities = Array.isArray(out.monster_abilities) ? out.monster_abilities
      : (out.special_abilities || []).filter(a => a.action_type !== "magia" && a.id)
        .map(a => Object.assign({id:a.id, uses_per_day:Math.max(1, n(a.uses_per_day, 1)), cooldown_turns:Math.max(0, n(a.cooldown_turns, 0))}, a.id === "corpo_energetico" ? {damage:a.damage || "1d4", damage_type:(a.damage_types || ["lightning"])[0]} : {}));
    out.negative_ability_ids = (out.negative_ability_ids || allAbilityIds.filter(negativeAbility)).filter(negativeAbility);
    out.ability_ids = out.monster_abilities.map(a => a.id).filter(id => !negativeAbility(id));
    // A ficha salva traz as fraquezas mecânicas; o formulário as reconstrói a
    // partir da seleção negativa para que desmarcá-las as remova corretamente.
    const autoWeaknesses = mechanicsFor(out.negative_ability_ids);
    out.weaknesses = (out.weaknesses || []).filter(w => !autoWeaknesses.some(auto => sameWeakness(w, auto)));
    out.immunities = out.immunities || [];
    out.subtipo = out.subtipo || (out.undead ? "morto_vivo" : "raca_padrao");
    out.resistances = out.resistances || [];
    out.equipment = out.equipment || []; out.equipped_items = out.equipped_items || out.equipment || [];
    out.equipment_enabled = !!out.equipment_enabled;
    out.ai_profile = AI_PROFILES.some(p => p.id === out.ai_profile) ? out.ai_profile : "agressivo";
    out.ai_tactics = Array.isArray(out.ai_tactics) ? out.ai_tactics : [];
    out.guaranteed_loot = out.guaranteed_loot || [];
    out.loot_table = out.loot_table || {}; out.loot_drops = Array.isArray(out.loot_drops) ? out.loot_drops : [];
    out.ai_type = out.ai_type || "agressivo";
    return out;
  }
  function blank() { const m = normalize({ name:"Nova Criatura", hp:10, ac:10, movement:6, tier:1, cr:1, str_:10, dex:10, con_:10, int_:10, base_attack_bonus:0, attacks:[{name:"Ataque", damage:"1d4", num_attacks:1, attack_attribute:"str_", base_attack_bonus:0}] }, false); m.type = "nova_criatura"; m.original_type = ""; return m; }
  function weaknessText(list) { return (list || []).map(w => `${w.type || "physical"}|${w.categoria || ""}|${w.bonus_flat || ""}|${w.multiplier || ""}|${w.descricao || ""}`).join("\n"); }
  function parseWeaknesses(text) { return String(text || "").split("\n").map(row => row.trim()).filter(Boolean).map(row => { const [type,categoria,flat,mult,descricao] = row.split("|").map(x => x.trim()); const w={type:type || "physical"}; if(categoria) w.categoria=categoria; if(flat !== "" && Number.isFinite(Number(flat))) w.bonus_flat=Number(flat); if(mult !== "" && Number.isFinite(Number(mult))) w.multiplier=Number(mult); if(descricao) w.descricao=descricao; return w; }); }
  function read() {
    const get = id => document.getElementById(id);
    const val = id => get(id).value;
    const nums = ["tier","cr","base_hp","natural_armor","movement","vision_base","base_attack_bonus","caster_level","str_","dex","con_","int_","fort_base","ref_base","will_base","gold","xp"];
    const out = Object.assign({}, draft);
    ["name","type","emoji","image","portrait","porte"].forEach(k => out[k] = val("me-" + k).trim());
    // Na primeira montagem o resumo é calculado antes de o seletor visual de
    // perfil substituir o campo legado; use o rascunho nesse curto intervalo.
    out.ai_profile = get("me-ai_profile")?.value || draft.ai_profile || "agressivo";
    out.ai_tactics = [...root.querySelectorAll(".me-ai-tactic:checked")].map(el => el.value);
    out.ai_type = "agressivo";
    nums.forEach(k => out[k] = n(get("me-" + k)?.value, 0));
    out.movement = draft.movement_exception ? n(draft.movement, 6) : 6;
    out.hp = Math.max(1, out.base_hp + mod(out.con_));
    out.fort = out.fort_base + mod(out.con_);
    out.ref_ = out.ref_base + mod(out.dex);
    out.will = out.will_base + mod(out.int_);
    out.ac = Math.max(1, 10 + mod(out.dex) + out.natural_armor);
    out.boss = get("me-boss").checked;
    out.subtipo = val("me-subtipo") || "raca_padrao";
    out.undead = out.subtipo === "morto_vivo";
    out.visao_escuro = get("me-visao_escuro").checked;
    out.size = [Math.max(1, n(val("me-size-w"), 1)), Math.max(1, n(val("me-size-h"), 1))];
    out.oriented = get("me-oriented").checked && out.size[0] * out.size[1] > 1;
    out.immunities = [...root.querySelectorAll(".me-immunity:checked")].map(el => el.value);
    out.equipment_enabled = get("me-equipment-enabled").checked;
    out.equipped_items = [...root.querySelectorAll(".me-equipped-item")]
      .flatMap(el => el.multiple ? [...el.selectedOptions].map(o => o.value) : [el.value])
      .filter(Boolean);
    out.equipment = out.equipped_items.slice();
    out.guaranteed_loot = [];
    out.loot_drops = [...root.querySelectorAll(".me-loot-row")].map(row => {
      const selected = row.querySelector(".me-loot-id").value;
      return selected === "__gold__"
        ? {kind:"gold", amount:Math.max(1, n(row.querySelector(".me-loot-amount").value, 1)), chance:Math.max(0, Math.min(100, n(row.querySelector(".me-loot-chance").value, 100)))}
        : {kind:"item", item_id:selected, chance:Math.max(0, Math.min(100, n(row.querySelector(".me-loot-chance").value, 100)))};
    }).filter(drop => drop.kind === "gold" || drop.item_id);
    out.negative_ability_ids = [...root.querySelectorAll(".me-negative-ability:checked")].map(el => el.value);
    const knownWeaknesses = weaknessLibrary();
    out.weaknesses = [...root.querySelectorAll(".me-weakness:checked")]
      .map(el => { const trait=knownWeaknesses[Number(el.dataset.i)], existing=(draft.weaknesses || []).find(w => traitKey(w) === traitKey(trait)); return Object.assign(copy(trait), {bonus_flat:Math.max(1, n(root.querySelector(`.me-weakness-level[data-i="${el.dataset.i}"]`).value, 1)), descricao:existing?.descricao || trait.descricao}, existing?.ignora_reducao ? {ignora_reducao:true} : {}); })
      .concat([...root.querySelectorAll(".me-vulnerability:checked")].map(el => Object.assign({}, DAMAGE_TRAITS[Number(el.dataset.i)], {multiplier:2})))
      .concat(mechanicsFor(out.negative_ability_ids));
    if (get("me-ponto-vulneravel").checked && out.size[0] * out.size[1] > 1) {
      const tiles = [...get("me-ponto-vulneravel-tile").selectedOptions]
        .map(option => option.value.split(",").map(v => n(v, 0)));
      if (tiles.length) out.weaknesses.push({type:"ponto_vulneravel", nd_penalty:.25, tiles, descricao:"Ponto Vulnerável: ataques nos quadrados selecionados ignoram a armadura natural e reduções de dano (–0,25 ND estimado)"});
    }
    out.resistances = [...root.querySelectorAll(".me-resistance:checked")]
      .map(el => Object.assign({}, DAMAGE_TRAITS[Number(el.dataset.i)], {reduction:Math.max(1, n(root.querySelector(`.me-resistance-level[data-i="${el.dataset.i}"]`).value, 1))}))
      .concat([...root.querySelectorAll(".me-half-resistance:checked")].map(el => Object.assign({}, DAMAGE_TRAITS[Number(el.dataset.i)], {mode:"half"})));
    out.loot_table = {};
    out.monster_abilities = [...root.querySelectorAll(".me-ability:checked")].map(el => {
      const card = el.closest(".me-ability-card");
      const config = {id:el.value,
        uses_per_day:Math.max(1, n(card.querySelector(".me-ability-uses").value, 1)),
        cooldown_turns:Math.max(0, n(card.querySelector(".me-ability-cooldown").value, 0))};
      if (el.value === "corpo_energetico") {
        config.damage = card.querySelector(".me-energy-damage").value;
        config.damage_type = card.querySelector(".me-energy-type").value;
      }
      return config;
    });
    out.ability_ids = out.monster_abilities.map(a => a.id);
    out.monster_spells = [...root.querySelectorAll(".me-spell:checked")].map(el => {
      const card = el.closest(".me-spell-card"); const mode = card.querySelector(".me-spell-mode").value;
      const value = Math.max(1, n(card.querySelector(".me-spell-limit").value, 1));
      return mode === "cooldown" ? {id:el.value, limit_mode:mode, cooldown_turns:value} : {id:el.value, limit_mode:mode, uses_per_combat:value};
    });
    out.attacks = [...root.querySelectorAll(".me-attack")].map(row => ({ name:row.querySelector(".ma-name").value.trim(), damage:row.querySelector(".ma-damage").value.trim(), damage_types:[row.querySelector(".ma-type").value], attack_attribute:row.querySelector(".ma-attr").value, apply_attribute_damage:true, base_attack_bonus:n(row.querySelector(".ma-bab").value), num_attacks:n(row.querySelector(".ma-count").value, 1), range:n(row.querySelector(".ma-range").value), on_hit:row.querySelector(".ma-poison")?.value || null, on_hit_effect:row.querySelector(".ma-on-hit-effect")?.value || null, poison_dc:n(row.querySelector(".ma-poison-dc")?.value, 10), extra_damage:row.querySelector(".ma-extra-damage")?.value.trim() || null, extra_damage_types:row.querySelector(".ma-extra-type")?.value ? [row.querySelector(".ma-extra-type").value] : [] }));
    return out;
  }
  function estimate(m) {
    return window.EDITOR_BESTIARY ? window.EDITOR_BESTIARY.estimateND(m) : "—";
  }
  function updateCalculated() {
    const m = equipmentPreview(read());
    root.querySelectorAll(".me-attack").forEach((row, i) => { const target=row.querySelector(".ma-final"), attack=m.attacks[i] || m.attacks[0]; target.textContent = `Acerto: +${attackBonus(m, attack)} · Dano: ${attackDamage(attack, m)}${attack.range ? ` · Alcance ${attack.range}` : ""}`; });
    const initiative = n(m.dex, 10) + mod(m.int_);
    const final = { "me-hp-final":m.hp, "me-ac-final":m.ac, "me-vision-final":visionRadius(m), "me-fort-final":m.fort >= 0 ? "+" + m.fort : m.fort, "me-ref-final":m.ref_ >= 0 ? "+" + m.ref_ : m.ref_, "me-will-final":m.will >= 0 ? "+" + m.will : m.will, "me-init-final":initiative >= 0 ? "+" + initiative : initiative };
    Object.entries(final).forEach(([id, value]) => { const el=document.getElementById(id); if(el) el.textContent=value; });
    const spellDc = root.querySelector("#me-spell-dc-final");
    if (spellDc) spellDc.innerHTML = `1º: ${8 + mod(m.int_) + 1} · 2º: ${8 + mod(m.int_) + 2} · 3º: ${8 + mod(m.int_) + 3}`;
    const pv = root.querySelector("#me-nd-estimate"); if (pv) pv.textContent = estimate(m);
    const known = root.querySelector("#me-spell-known-count"); if (known) known.textContent = `${m.monster_spells.length} conhecida${m.monster_spells.length === 1 ? "" : "s"}`;
    const summary = root.querySelector(".me-tab-panel[data-tab=\"Resumo\"]");
    if (summary && summaryRenderer) summary.innerHTML = summaryRenderer(read());
  }
  function render() {
    if (!draft) draft = blank();
    const monsters = all(), custom = customTypes();
    const abilities = abilityLibrary(), weaknesses = weaknessLibrary(), ai = aiOptions();
    const positiveAbilities = abilities.filter(a => !negativeAbility(a.id));
    const negativeAbilities = abilities.filter(a => negativeAbility(a.id));
    const configuredAbilities = new Map((draft.monster_abilities || []).map(a => [a.id, a]));
    const selectedAbilities = new Set(configuredAbilities.keys());
    const selectedNegativeAbilities = new Set(draft.negative_ability_ids || []);
    const pontoVulneravel = (draft.weaknesses || []).find(w => w.type === "ponto_vulneravel");
    const selectedPontoTiles = new Set(((pontoVulneravel || {}).tiles || []).map(tile => `${tile[0]},${tile[1]}`));
    const selectedWeaknesses = new Set((draft.weaknesses || []).map(weaknessKey));
    const selectedVulnerabilities = new Set((draft.weaknesses || []).filter(w => Number(w.multiplier) > 1).map(traitKey));
    const selectedResistances = new Set((draft.resistances || []).filter(r => r.mode !== "half").map(traitKey));
    const selectedHalfResistances = new Set((draft.resistances || []).filter(r => r.mode === "half").map(traitKey));
    const weaknessLevel = t => Math.max(1, n(((draft.weaknesses || []).find(w => traitKey(w) === traitKey(t)) || {}).bonus_flat, 1));
    const resistanceLevel = t => Math.max(1, n(((draft.resistances || []).find(r => traitKey(r) === traitKey(t) && r.mode !== "half") || {}).reduction, 1));
    const configuredSpells = new Map((draft.monster_spells || []).map(s => [s.id, s]));
    const shopItems = ((window.EDITOR_CATALOG || {}).items || []);
    const equipped = new Set(draft.equipped_items || draft.equipment || []);
    const itemBy = predicate => shopItems.filter(predicate);
    const selectEquipment = (id, label, items, multiple=false, max=1) => `<label>${label}<select id="${id}" class="me-equipped-item"${multiple ? ` multiple size="${Math.min(max, 6)}"` : ""}><option value="">— nenhum —</option>${items.map(item => `<option value="${esc(item.id)}"${equipped.has(item.id) ? " selected" : ""}>${esc(item.emoji || "")}${esc(item.name)}</option>`).join("")}</select></label>`;
    const weapons = itemBy(i => i.die);
    const armors = itemBy(i => i.kind === "armor");
    const shields = itemBy(i => i.kind === "shield");
    const heads = itemBy(i => i.item_slot === "head");
    const rings = itemBy(i => i.item_slot === "ring");
    const accessories = itemBy(i => i.item_slot === "item" || i.item_slot === "instrumento");
    const bagItems = itemBy(i => i.item_slot === "bag" || i.item_slot === "ammo");
    const circleName = {primeiro:"1º círculo", segundo:"2º círculo", terceiro:"3º círculo"};
    const spellCards = ["primeiro", "segundo", "terceiro"].map(circle => {
      const cards = spellLibrary().filter(s => s.circulo === circle).map(s => {
        const cfg = configuredSpells.get(s.id) || {limit_mode:"encounter", uses_per_combat:1};
        const selected = configuredSpells.has(s.id);
        const limit = cfg.limit_mode === "cooldown" ? cfg.cooldown_turns : cfg.uses_per_combat;
        const classes = (s.classe || []).map(c => c === "mage" ? "Mago" : "Clérigo").join(" / ");
        const hint = `${s.descricao || "Sem descrição cadastrada."} ${s.save ? `Teste: ${s.save}.` : ""}`;
        return `<div class="me-spell-card me-tip" data-circle="${circle}" data-tip="${esc(hint)}"><input class="me-spell" type="checkbox" value="${esc(s.id)}"${selected ? " checked" : ""}><span><b>${esc(s.icone || "✦")} ${esc(s.nome)}</b><small>${esc(classes)} · ${esc(s.tipo || "magia")}</small></span><select class="me-spell-mode"><option value="encounter"${cfg.limit_mode !== "cooldown" ? " selected" : ""}>por encontro</option><option value="cooldown"${cfg.limit_mode === "cooldown" ? " selected" : ""}>recarga</option></select><label><input class="me-spell-limit" type="number" min="1" max="20" value="${esc(limit || 1)}"><small class="me-spell-limit-label">${cfg.limit_mode === "cooldown" ? "rodadas" : "lançamentos"}</small></label></div>`;
      }).join("") || "<p>Nenhuma magia cadastrada neste círculo.</p>";
      return `<div class="me-spell-panel" data-circle="${circle}"><h3>${circleName[circle]}</h3><div class="me-spell-grid">${cards}</div></div>`;
    }).join("");
    const abilitySources = [
      {id:"heroi", label:"Heróis", filter:a => a.source === "heroi"},
      {id:"guilda", label:"Guilda", filter:a => a.source === "guilda"},
      {id:"monstro", label:"Bestiário", filter:a => a.source !== "heroi" && a.source !== "guilda"},
    ];
    const abilityCards = abilitySources.map(source => {
      const cards = positiveAbilities.filter(source.filter).map(a => {
        const cfg = configuredAbilities.get(a.id) || {uses_per_day:1, cooldown_turns:0};
        const selected = selectedAbilities.has(a.id);
        const energyConfig = a.id === "corpo_energetico" ? `<span class="me-ability-limit">dano<select class="me-energy-damage">${["1d4","1d6","1d8","1d10","1d12"].map(v=>`<option value="${v}"${(cfg.damage || a.damage || "1d4") === v ? " selected" : ""}>${v}</option>`).join("")}</select></span><span class="me-ability-limit">elemento<select class="me-energy-type">${ATTACK_DAMAGE_TYPES.filter(t=>t.value!=="physical").map(t=>`<option value="${t.value}"${(cfg.damage_type || (a.damage_types||["lightning"])[0]) === t.value ? " selected" : ""}>${t.name}</option>`).join("")}</select></span>` : "";
        return `<div class="me-ability-card me-tip" data-source="${source.id}" data-tip="${esc(abilityHint(a))}"><input class="me-ability" type="checkbox" value="${esc(a.id)}"${selected ? " checked" : ""}><span><b>${esc(a.icon || "✦")} ${esc(a.name)}</b><small>${esc(a.action_type || "ação")}</small></span><span class="me-ability-limit">usos/dia<input class="me-ability-uses" type="number" min="1" max="20" value="${esc(cfg.uses_per_day || 1)}"></span><span class="me-ability-limit">recarga<input class="me-ability-cooldown" type="number" min="0" max="20" value="${esc(cfg.cooldown_turns || 0)}"><small>rodadas</small></span>${energyConfig}</div>`;
      }).join("") || "Nenhuma habilidade cadastrada nesta origem.";
      return `<div class="me-ability-panel" data-source="${source.id}"><h3>${source.label}</h3><div class="me-ability-grid">${cards}</div></div>`;
    }).join("");
    root.innerHTML = `<div class="me-layout"><aside class="me-sidebar"><button id="me-new">+ Nova criatura</button><label>Modelo ou criatura existente<select id="me-template"><option value="">Selecione…</option>${monsters.map(m => `<option value="${esc(m.type)}">${esc(m.name)}${custom.has(m.type) ? " (personalizado)" : " (modelo)"}</option>`).join("")}</select></label><p>Os modelos nativos são sempre copiados. A edição de uma criatura personalizada atualiza somente sua própria ficha.</p></aside><main class="me-form"><header><div><h1>Editor de criaturas</h1><p>${draft.original_type ? "Editando criatura personalizada" : "Criando uma nova cópia independente"}</p></div><div class="me-nd">ND estimado <b id="me-nd-estimate">${estimate(draft)}</b></div></header>
      <section><h2>Arte da criatura</h2><p class="me-hint">Escolha imagens PNG. Ao selecionar, o arquivo é enviado ao projeto, a prévia é atualizada e a referência é salva com a ficha.</p><input id="me-image" type="hidden" value="${esc(draft.image || draft.type)}"><input id="me-portrait" type="hidden" value="${esc(draft.portrait || draft.type)}"><div style="display:flex;gap:18px;flex-wrap:wrap"><label style="display:grid;grid-template-columns:92px 1fr;gap:10px;align-items:center;min-width:250px"><img id="me-mini-preview" src="../assets/pawns/monstros/${esc(draft.image || draft.type)}/${esc(draft.image || draft.type)}.png" style="width:86px;height:86px;object-fit:contain;background:#10131a;border:1px solid #556070"><span><b>Miniatura do peão</b><small>Usada no mapa 2D e 3D.</small><input id="me-mini-file" type="file" accept="image/png,.png"></span></label><label style="display:grid;grid-template-columns:92px 1fr;gap:10px;align-items:center;min-width:250px"><img id="me-portrait-preview" src="../assets/retratos/monstros/${esc(draft.portrait || draft.type)}.png" style="width:86px;height:86px;object-fit:cover;background:#10131a;border:1px solid #556070"><span><b>Retrato do Bestiário</b><small>Usado no quadro superior do Bestiário.</small><input id="me-portrait-file" type="file" accept="image/png,.png"></span></label></div></section>
      <section><h2>Identidade e combate</h2><div class="me-fields cols-4"><label>Nome<input id="me-name" value="${esc(draft.name)}"></label><label>ID técnico<input id="me-type" value="${esc(draft.type)}"><small>letras, números e _</small></label><label>Ícone<input id="me-emoji" value="${esc(draft.emoji || "👹")}"></label><label>ND definido<input id="me-cr" type="number" step="0.25" min="0.125" value="${esc(draft.cr || 1)}"></label><label>PV base<input id="me-base_hp" type="number" min="1" value="${esc(draft.base_hp)}"></label><div class="me-calculated"><b>PV final</b><span id="me-hp-final">${esc(draft.hp)}</span></div><label>Armadura natural<input id="me-natural_armor" type="number" min="0" value="${esc(draft.natural_armor)}"><small>somada ao modificador de DES</small></label><div class="me-calculated"><b>CA total</b><span id="me-ac-final">${esc(draft.ac)}</span></div><div class="me-calculated"><b>Movimento básico</b><span>6</span></div><label>Bônus base de ataque<input id="me-base_attack_bonus" type="number" value="${esc(draft.base_attack_bonus || 0)}"></label></div></section>
      <section><h2>Atributos e resistências</h2><div class="me-fields cols-4"><label>Força<input id="me-str_" type="number" min="1" value="${esc(draft.str_)}"></label><label>Destreza<input id="me-dex" type="number" min="1" value="${esc(draft.dex)}"></label><label>Constituição<input id="me-con_" type="number" min="1" value="${esc(draft.con_)}"></label><label>Inteligência<input id="me-int_" type="number" min="1" value="${esc(draft.int_)}"></label><div class="me-calculated"><b>Iniciativa (DES + mod. INT)</b><span id="me-init-final">${esc(n(draft.dex,10)+mod(draft.int_))}</span></div><label>Base Fortitude<input id="me-fort_base" type="number" value="${esc(draft.fort_base)}"></label><div class="me-calculated"><b>Fortitude final</b><span id="me-fort-final">${esc(draft.fort >= 0 ? "+" + draft.fort : draft.fort)}</span></div><label>Base Reflexos<input id="me-ref_base" type="number" value="${esc(draft.ref_base)}"></label><div class="me-calculated"><b>Reflexos final</b><span id="me-ref-final">${esc(draft.ref_ >= 0 ? "+" + draft.ref_ : draft.ref_)}</span></div><label>Base Vontade<input id="me-will_base" type="number" value="${esc(draft.will_base)}"></label><div class="me-calculated"><b>Vontade final</b><span id="me-will-final">${esc(draft.will >= 0 ? "+" + draft.will : draft.will)}</span></div></div></section>
      <section><h2>Ataques</h2><div id="me-attacks">${draft.attacks.map((a,i) => `<div class="me-attack"><label>Nome<input class="ma-name" value="${esc(a.name)}"></label><label>Dano base<input class="ma-damage" value="${esc(a.damage)}"></label><label>Tipo<select class="ma-type">${ATTACK_DAMAGE_TYPES.map(t => `<option value="${t.value}"${(a.damage_types || ["physical"])[0] === t.value ? " selected" : ""}>${t.name}</option>`).join("")}</select></label><label>Atributo<select class="ma-attr"><option value="str_"${a.attack_attribute !== "dex" ? " selected" : ""}>Força (corpo a corpo)</option><option value="dex"${a.attack_attribute === "dex" ? " selected" : ""}>Destreza (à distância)</option></select></label><label>Bônus base<input class="ma-bab" type="number" value="${esc(a.base_attack_bonus != null ? a.base_attack_bonus : draft.base_attack_bonus)}"></label><label>Nº ataques<input class="ma-count" type="number" min="1" value="${esc(a.num_attacks || 1)}"></label><label>Alcance<input class="ma-range" type="number" min="0" value="${esc(a.range || 0)}"></label><strong class="ma-final">Acerto: +${attackBonus(draft,a)} · Dano: ${attackDamage(a,draft)}</strong><button class="me-remove-attack" data-i="${i}" title="remover">×</button></div>`).join("")}</div><button id="me-add-attack">+ ataque</button></section>
      <section class="me-spells"><header><div><h2>Magias</h2><p>Grimório compartilhado com heróis. A IA escolhe automaticamente a magia disponível; seus efeitos de área também podem atingir aliados do monstro.</p></div><b id="me-spell-known-count">${(draft.monster_spells || []).length} conhecida${(draft.monster_spells || []).length === 1 ? "" : "s"}</b></header><div class="me-spell-caster"><label>Nível de conjurador<input id="me-caster_level" type="number" min="1" max="20" value="${esc(draft.caster_level)}"></label><p>Eleva dano, alcance, duração e demais escalas previstas em cada magia. Também aumenta o ND quando a criatura conhece magias.</p></div><div class="me-spell-tabs"><button type="button" class="active" data-circle="primeiro">1º círculo</button><button type="button" data-circle="segundo">2º círculo</button><button type="button" data-circle="terceiro">3º círculo</button></div>${spellCards}<p class="me-hint">Marque as magias conhecidas. Para cada uma, defina lançamentos por encontro ou sua recarga em rodadas. Passe o mouse para ler a regra.</p></section>
      <section class="me-editor-abilities"><header><div><h2>Habilidades</h2><p>Selecione quantas quiser. Cada habilidade respeita simultaneamente o número de usos por dia e sua recarga em rodadas; a IA a ativa para obter vantagem e derrotar os heróis.</p></div></header><div class="me-ability-tabs"><button type="button" class="active" data-source="heroi">Heróis</button><button type="button" data-source="guilda">Guilda</button><button type="button" data-source="monstro">Bestiário</button></div>${abilityCards}<p class="me-hint">Recarga 0 significa que a habilidade só é limitada pelos usos por dia. Passe o mouse sobre ela para ler a descrição.</p></section>
      <section><h2>Resistências a dano</h2><div class="me-resistance-grid">${DAMAGE_TRAITS.map((t,i) => `<label class="me-tip" data-tip="${esc(`Reduz ${t.name} em ${resistanceLevel(t)} ponto(s). Cada ponto aumenta o ND.`)}"><input class="me-resistance" type="checkbox" data-i="${i}"${selectedResistances.has(traitKey(t)) ? " checked" : ""}><b>${esc(t.name)}</b><small>Reduz <input class="me-resistance-level" data-i="${i}" type="number" min="1" max="20" value="${resistanceLevel(t)}"> dano</small></label>`).join("")}</div><p class="me-hint">Resistência fixa começa em 1 e pode ser elevada. Ela aumenta o ND.</p></section>
      <section><h2>Resistência pela metade</h2><div class="me-resistance-grid me-half-grid">${DAMAGE_TRAITS.map((t,i) => `<label class="me-tip" data-tip="${esc(`O monstro sofre apenas metade do dano de ${t.name}.`)}"><input class="me-half-resistance" type="checkbox" data-i="${i}"${selectedHalfResistances.has(traitKey(t)) ? " checked" : ""}><b>${esc(t.name)}</b><small>½ dano recebido</small></label>`).join("")}</div></section>
      <section><h2>Fraquezas a dano</h2><div class="me-weakness-grid"><small>Começam em +1 dano recebido e podem ser aumentadas. Quanto maior, menor o ND.</small><div class="me-abilities">${weaknesses.map((w,i) => { const trait=DAMAGE_TRAITS[i], level=weaknessLevel(trait); return `<label class="me-tip" data-tip="${esc(`Recebe +${level} dano de ${trait.name}.`)}"><input class="me-weakness" type="checkbox" data-i="${i}"${selectedWeaknesses.has(weaknessKey(w)) ? " checked" : ""}><b>${esc(trait.name)}</b><small>Recebe +<input class="me-weakness-level" data-i="${i}" type="number" min="1" max="20" value="${level}"> dano</small></label>`; }).join("")}</div></div></section>
      <section><h2>Vulnerabilidade a dano dobrado</h2><div class="me-vulnerability-grid">${DAMAGE_TRAITS.map((t,i) => `<label class="me-tip" data-tip="${esc(`A criatura sofre o dobro do dano de ${t.name}.`)}"><input class="me-vulnerability" type="checkbox" data-i="${i}"${selectedVulnerabilities.has(traitKey(t)) ? " checked" : ""}><b>${esc(t.name)}</b><small>Recebe 2× dano</small></label>`).join("")}</div></section>
      <section><h2>Fraquezas especiais</h2><div class="me-abilities me-negative-abilities">${negativeAbilities.map(a => `<label class="me-tip" data-tip="${esc(abilityHint(a) + " Ao selecionar, incorpora automaticamente a mecânica correspondente.")}"><input class="me-negative-ability" type="checkbox" value="${esc(a.id)}"${selectedNegativeAbilities.has(a.id) ? " checked" : ""}><b>${esc(a.name)}</b><small>Reduz o ND · mecânica automática</small></label>`).join("") || "Nenhuma fraqueza especial cadastrada."}</div><p class="me-hint">Efeitos mistos ficam aqui e causam apenas uma redução moderada no ND.</p></section>
      <section><h2>Comportamento, defesas e tesouro</h2><div class="me-fields cols-3"><label>IA<select id="me-ai_type">${options(ai.map(v => ({value:v})), draft.ai_type, x => x.value.replace(/_/g," "))}</select></label><label>Imagem da miniatura<input id="me-image" value="${esc(draft.image || draft.type)}"></label><label>Porte<select id="me-porte">${options(["minusculo","pequeno","medio","grande","enorme"].map(value=>({value})), draft.porte || "medio", x=>x.value)}</select></label><label>Imunidades (separadas por vírgula)<input id="me-immunities" value="${esc(draft.immunities.join(", "))}"></label><label>Loot garantido (IDs, vírgula)<input id="me-guaranteed-loot" value="${esc(draft.guaranteed_loot.join(", "))}"></label><label>Ouro<input id="me-gold" type="number" min="0" value="${esc(draft.gold || 0)}"></label><label>XP<input id="me-xp" type="number" min="0" value="${esc(draft.xp || 0)}"></label><label>Tier<input id="me-tier" type="number" min="1" value="${esc(draft.tier || 1)}"></label></div><label>Loot variável (JSON opcional)<textarea id="me-loot-table">${esc(JSON.stringify(draft.loot_table || {}, null, 2))}</textarea></label><div class="me-checks"><label><input id="me-undead" type="checkbox"${draft.undead ? " checked" : ""}> morto-vivo</label><label><input id="me-boss" type="checkbox"${draft.boss ? " checked" : ""}> chefe</label></div></section>
      <footer><span id="me-status">O ID é gerado pelo nome e pode ser alterado.</span><button id="me-save" class="me-save">Salvar criatura personalizada</button></footer></main></div>`;
    const behaviorSection = root.querySelector("#me-ai_type")?.closest("section");
    if (behaviorSection) behaviorSection.insertAdjacentHTML("afterend", `<section class="me-equipment"><h2>Inventário e equipamentos</h2><p class="me-hint">Marque a permissão e escolha os itens ativos. Raça Padrão e Abissais podem usar equipamentos; um Morto-Vivo só poderá fazê-lo quando esta opção for marcada na ficha. Construtos, animais e vegetais não podem usar equipamentos.</p><div class="me-checks"><label><input id="me-equipment-enabled" type="checkbox"${draft.equipment_enabled ? " checked" : ""}> usar itens e equipamentos</label></div><fieldset id="me-equipment-inventory"${draft.equipment_enabled ? "" : " disabled"}><div class="me-fields cols-3">${selectEquipment("me-equip-weapon", "Arma equipada", weapons)}${selectEquipment("me-equip-armor", "Armadura", armors)}${selectEquipment("me-equip-shield", "Escudo", shields)}${selectEquipment("me-equip-head", "Cabeça", heads)}${selectEquipment("me-equip-ring-1", "Anel 1", rings)}${selectEquipment("me-equip-ring-2", "Anel 2", rings)}${selectEquipment("me-equip-item-1", "Item mágico 1", accessories)}${selectEquipment("me-equip-item-2", "Item mágico 2", accessories)}${Array.from({length:6}, (_, i) => selectEquipment(`me-equip-bag-${i+1}`, `Bolsa ${i+1}`, bagItems)).join("")}</div></fieldset><p class="me-hint">Seis espaços de bolsa para itens não equipados. A IA usa poções, elixires, venenos e arremessáveis quando a situação permitir.</p></section>`);
    // O campo de texto antigo é mantido no HTML por compatibilidade com fichas
    // já abertas, mas a escolha agora é feita exclusivamente pelos seletores.
    const legacyImage = root.querySelectorAll("#me-image")[1];
    if (legacyImage) legacyImage.closest("label")?.remove();
    const attrFields = root.querySelector("#me-str_")?.closest(".me-fields");
    if (attrFields) attrFields.insertAdjacentHTML("beforeend", `<label>Bônus em visão<input id="me-vision_base" type="number" min="-30" max="30" value="${esc(draft.vision_base)}"><small>somado ao movimento 6 + metade dos bônus de DES + INT</small></label><div class="me-calculated"><b>Raio de visão</b><span id="me-vision-final">${esc(visionRadius(draft))}</span></div><label>Largura ocupada<input id="me-size-w" type="number" min="1" max="4" value="${draft.size[0]}"><small>quadrados</small></label><label>Comprimento ocupado<input id="me-size-h" type="number" min="1" max="4" value="${draft.size[1]}"><small>quadrados</small></label><label><input id="me-oriented" type="checkbox"${draft.oriented ? " checked" : ""}${draft.size[0]*draft.size[1]>1 ? "" : " disabled"}> criatura orientada</label>`);
    const checks = root.querySelector("#me-undead")?.closest(".me-checks");
    if (checks) checks.insertAdjacentHTML("beforeend", `<label>Subtipo<select id="me-subtipo">${SUBTIPOS.map(s => `<option value="${s.id}"${(draft.subtipo || (draft.undead ? "morto_vivo" : "raca_padrao")) === s.id ? " selected" : ""}>${s.nome}</option>`).join("")}</select><small id="me-subtipo-desc"></small></label><label><input id="me-visao_escuro" type="checkbox"${draft.visao_escuro ? " checked" : ""}> visão no escuro</label>`);
    const subtipoSel = root.querySelector("#me-subtipo");
    if (subtipoSel) {
      const showSubtype = () => { const s = SUBTIPOS.find(x => x.id === subtipoSel.value); root.querySelector("#me-subtipo-desc").textContent = s ? s.desc : ""; };
      subtipoSel.onchange = showSubtype; showSubtype();
    }
    const behavior = root.querySelector("#me-ai_type")?.closest("section");
    if (behavior) {
      const cells = [];
      const [depth, width] = draft.oriented ? [draft.size[1], draft.size[0]] : [draft.size[0], draft.size[1]];
      for (let y=0; y<width; y++) for (let x=0; x<depth; x++) cells.push([x,y]);
      const labels = cells.map(([x,y]) => {
        const rear = draft.oriented ? (x === 0 ? " (frente)" : (x === depth-1 ? " (traseiro)" : " (meio)")) : "";
        const value = `${x},${y}`;
        return `<option value="${value}"${selectedPontoTiles.has(value) ? " selected" : ""}>quadrado ${x+1},${y+1}${rear}</option>`;
      }).join("");
      behavior.insertAdjacentHTML("afterbegin", `<div class="me-checks"><label class="me-tip" data-tip="Ataques contra os quadrados selecionados ignoram somente a armadura natural — a Destreza ainda conta na CA — e também ignoram reduções de dano da criatura."><input id="me-ponto-vulneravel" type="checkbox"${pontoVulneravel && draft.size[0]*draft.size[1]>1 ? " checked" : ""}${draft.size[0]*draft.size[1]>1 ? "" : " disabled"}> Ponto Vulnerável</label><label>Quadrados vulneráveis<select id="me-ponto-vulneravel-tile" multiple size="${Math.min(6, Math.max(2, cells.length))}"${draft.size[0]*draft.size[1]>1 ? "" : " disabled"}>${labels}</select></label></div><p class="me-hint">Disponível somente para criaturas que ocupam mais de uma casa. Use Ctrl (ou ⌘ no Mac) para selecionar mais de um quadrado.</p>`);
    }
    // Controles estruturados adicionados sobre a ficha legada: mantêm os
    // mesmos campos de persistência e deixam a edição legível por abas.
    const poisonOptions = ((window.EDITOR_CATALOG || {}).venoms || []).map(v => ({id:v.id, name:v.nome || v.id})).filter(v => v.id);
    root.querySelectorAll(".me-attack").forEach((row, i) => {
      const a = draft.attacks[i] || {};
      row.insertAdjacentHTML("beforeend", `<div class="me-attack-special"><b>Especial ao acertar</b><label>Veneno<select class="ma-poison"><option value="">— nenhum —</option>${poisonOptions.map(v => `<option value="${esc(v.id)}"${a.on_hit === v.id ? " selected" : ""}>${esc(v.name)}</option>`).join("")}</select></label><label>CD do veneno<input class="ma-poison-dc" type="number" min="1" max="40" value="${esc(a.poison_dc || 10)}"></label><label>Efeito<select class="ma-on-hit-effect"><option value="">— nenhum —</option><option value="congelamento_progressivo"${a.on_hit_effect === "congelamento_progressivo" ? " selected" : ""}>Congelamento Progressivo</option><option value="golpe_vento"${a.on_hit_effect === "golpe_vento" ? " selected" : ""}>Golpe de Vento (empurra)</option></select></label><label>Dano extra<select class="ma-extra-type"><option value="">— nenhum —</option>${ATTACK_DAMAGE_TYPES.filter(t=>t.value!=="physical").map(t=>`<option value="${t.value}"${(a.extra_damage_types||[])[0]===t.value ? " selected" : ""}>${t.name}</option>`).join("")}</select></label><label>Dados extras<input class="ma-extra-damage" placeholder="ex.: 2d6" value="${esc(a.extra_damage || "")}"></label></div>`);
    });
    const casterBox = root.querySelector(".me-spell-caster");
    if (casterBox) casterBox.insertAdjacentHTML("beforeend", `<div class="me-calculated me-spell-dc"><b>CD de resistência</b><span id="me-spell-dc-final">8 + INT + círculo</span><small>1º: ${8 + mod(draft.int_) + 1} · 2º: ${8 + mod(draft.int_) + 2} · 3º: ${8 + mod(draft.int_) + 3}</small></div>`);
    const behaviorPanel = root.querySelector("#me-ai_type")?.closest("section");
    if (behaviorPanel) {
      const legacyImmunities = behaviorPanel.querySelector("#me-immunities")?.closest("label");
      const legacyGuaranteed = behaviorPanel.querySelector("#me-guaranteed-loot")?.closest("label");
      const legacyTable = behaviorPanel.querySelector("#me-loot-table")?.closest("label");
      const legacyGold = behaviorPanel.querySelector("#me-gold")?.closest("label");
      [legacyImmunities, legacyGuaranteed, legacyTable, legacyGold].forEach(el => el?.remove());
      const immunityChoices = [["fire","Fogo"],["cold","Gelo"],["acid","Ácido"],["lightning","Elétrico"],["poison","Veneno"],["holy","Sagrado / luz"],["encantamento","Encantamento"],["sono","Sono"],["paralisia","Paralisia"]];
      const drops = draft.loot_drops || (draft.guaranteed_loot || []).map(item_id => ({kind:"item",item_id,chance:100}));
      const itemOptions = shopItems.map(item => `<option value="${esc(item.id)}">${esc(item.emoji || "")} ${esc(item.name)}</option>`).join("");
      behaviorPanel.insertAdjacentHTML("beforeend", `<div class="me-defense-loot"><h3>Imunidades</h3><div class="me-immunity-grid">${immunityChoices.map(([id,label])=>`<label><input class="me-immunity" type="checkbox" value="${id}"${draft.immunities.includes(id)?" checked":""}> ${label}</label>`).join("")}</div><h3>Tesouro deixado</h3><p class="me-hint">Cada item é rolado separadamente; vários itens podem cair.</p><div id="me-loot-rows">${(drops.length?drops:[{item_id:"",chance:100}]).map(drop=>`<div class="me-loot-row"><select class="me-loot-id"><option value="">— selecione um item —</option>${shopItems.map(item=>`<option value="${esc(item.id)}"${drop.item_id===item.id?" selected":""}>${esc(item.emoji || "")} ${esc(item.name)}</option>`).join("")}</select><label>Chance %<input class="me-loot-chance" type="number" min="0" max="100" value="${esc(drop.chance)}"></label><button type="button" class="me-remove-loot">×</button></div>`).join("")}</div><button type="button" id="me-add-loot">+ item no loot</button></div>`);
      behaviorPanel.querySelector("#me-add-loot").onclick = () => { const box=behaviorPanel.querySelector("#me-loot-rows"); box.insertAdjacentHTML("beforeend", `<div class="me-loot-row"><select class="me-loot-id"><option value="">— selecione um item —</option>${itemOptions}</select><label>Chance %<input class="me-loot-chance" type="number" min="0" max="100" value="100"></label><button type="button" class="me-remove-loot">×</button></div>`); box.lastElementChild.querySelector(".me-remove-loot").onclick = e => e.currentTarget.closest(".me-loot-row").remove(); };
      behaviorPanel.querySelectorAll(".me-remove-loot").forEach(btn => btn.onclick = e => e.currentTarget.closest(".me-loot-row").remove());
      // Ouro é um drop independente como qualquer item: quantidade e chance
      // ficam na própria linha (ex.: 10 moedas / 30%).
      const makeLootRow = drop => `<div class="me-loot-row"><select class="me-loot-id"><option value="">— selecione um item —</option><option value="__gold__"${drop.kind === "gold" ? " selected" : ""}>🪙 Moedas de ouro</option>${shopItems.map(item => `<option value="${esc(item.id)}"${drop.item_id === item.id ? " selected" : ""}>${esc(item.emoji || "")} ${esc(item.name)}</option>`).join("")}</select><label>Quantidade<input class="me-loot-amount" type="number" min="1" value="${esc(drop.amount || 1)}"></label><label>Chance %<input class="me-loot-chance" type="number" min="0" max="100" value="${esc(drop.chance || 100)}"></label><button type="button" class="me-remove-loot">×</button></div>`;
      const lootRows = behaviorPanel.querySelector("#me-loot-rows");
      if (lootRows) {
        const savedDrops = drops.length ? drops : [{kind:"item",item_id:"",chance:100}];
        lootRows.innerHTML = savedDrops.map(makeLootRow).join("");
        const bindLootRemove = row => row.querySelector(".me-remove-loot").onclick = () => row.remove();
        [...lootRows.children].forEach(bindLootRemove);
        behaviorPanel.querySelector("#me-add-loot").onclick = () => {
          lootRows.insertAdjacentHTML("beforeend", makeLootRow({kind:"item",item_id:"",chance:100}));
          bindLootRemove(lootRows.lastElementChild);
        };
      }
    }
    const makeSummary = m => window.EDITOR_BESTIARY?.details ? window.EDITOR_BESTIARY.details(m) : `<article class="me-summary"><h2>${esc(m.emoji||"")} ${esc(m.name)}</h2></article>`; summaryRenderer=makeSummary;
    const form = root.querySelector(".me-form"), footer = form.querySelector("footer");
    const groups = [["Resumo", []], ["Identidade", ["Arte da criatura","Identidade e combate","Atributos e resistências"]], ["Ataques", ["Ataques","Inventário e equipamentos"]], ["Habilidades", ["Habilidades"]], ["Magias", ["Magias"]], ["Resistências", ["Resistências a dano","Resistência pela metade","Fraquezas a dano","Vulnerabilidade a dano dobrado","Fraquezas especiais"]], ["Comportamento e tesouro", ["Comportamento, defesas e tesouro"]]];
    const nav = document.createElement("nav"); nav.className="me-main-tabs";
    groups.forEach(([name]) => nav.insertAdjacentHTML("beforeend", `<button type="button" data-tab="${esc(name)}">${esc(name)}</button>`));
    form.insertBefore(nav, form.querySelector("section"));
    groups.forEach(([name, heads]) => { const panel=document.createElement("div"); panel.className="me-tab-panel"; panel.dataset.tab=name; if(name==="Resumo") panel.innerHTML=makeSummary(read()); else [...form.querySelectorAll(":scope > section")].filter(s=>heads.includes(s.querySelector("h2")?.textContent)).forEach(s=>panel.appendChild(s)); form.insertBefore(panel, footer); });
    const switchTab = name => { root.querySelectorAll(".me-tab-panel").forEach(p=>p.hidden=p.dataset.tab!==name); root.querySelectorAll(".me-main-tabs button").forEach(b=>b.classList.toggle("active",b.dataset.tab===name)); };
    // Ponto Vulnerável é uma desvantagem, não uma habilidade ofensiva: o
    // controle especializado fica junto às demais fraquezas.
    const vulnerableControl = root.querySelector("#me-ponto-vulneravel")?.closest(".me-checks");
    const resistancePanel = root.querySelector('.me-tab-panel[data-tab="Resistências"]');
    if (vulnerableControl && resistancePanel) {
      const hint = vulnerableControl.nextElementSibling;
      resistancePanel.appendChild(vulnerableControl);
      if (hint?.classList.contains("me-hint")) resistancePanel.appendChild(hint);
    }
    // O subtipo é a identidade da criatura. O antigo checkbox "morto-vivo"
    // duplicava essa escolha, portanto fica somente o seletor na ficha base.
    root.querySelector("#me-undead")?.closest("label")?.remove();
    const subtypeControl = root.querySelector("#me-subtipo")?.closest("label");
    const identityFields = root.querySelector("#me-name")?.closest(".me-fields");
    if (subtypeControl && identityFields) identityFields.appendChild(subtypeControl);
    const aiControl = root.querySelector("#me-ai_type")?.closest("label");
    if (aiControl && identityFields) {
      const selectedTactics = new Set(draft.ai_tactics || []);
      aiControl.outerHTML = `<label>Perfil de IA<select id="me-ai_profile">${AI_PROFILES.map(p => `<option value="${p.id}"${draft.ai_profile === p.id ? " selected" : ""}>${p.name}</option>`).join("")}</select><small id="me-ai-profile-desc"></small></label>`;
      const profileControl = identityFields.querySelector("#me-ai_profile")?.closest("label");
      profileControl?.insertAdjacentHTML("afterend", `<div class="me-ai-tactics"><b>Táticas especiais</b><small>Refinam como o perfil toma decisões.</small><div>${AI_TACTICS.map(([id,label]) => `<label><input class="me-ai-tactic" type="checkbox" value="${id}"${selectedTactics.has(id) ? " checked" : ""}> ${label}</label>`).join("")}</div></div>`);
      const profileSelect = identityFields.querySelector("#me-ai_profile");
      const showProfile = () => { const p=AI_PROFILES.find(x=>x.id===profileSelect.value); const e=identityFields.querySelector("#me-ai-profile-desc"); if(e) e.textContent=p?.desc || ""; };
      if (profileSelect) { profileSelect.onchange=showProfile; showProfile(); }
    }
    root.querySelector("#me-tier")?.closest("label")?.remove();
    root.querySelectorAll(".me-main-tabs button").forEach(btn=>btn.onclick=()=>switchTab(btn.dataset.tab)); switchTab("Resumo");
    const equipmentToggle = document.getElementById("me-equipment-enabled");
    const equipmentInventory = document.getElementById("me-equipment-inventory");
    if (equipmentToggle && equipmentInventory) equipmentToggle.onchange = () => {
      equipmentInventory.disabled = !equipmentToggle.checked;
      updateCalculated();
    };
    document.getElementById("me-new").onclick = () => { draft = blank(); idManual = false; render(); };
    document.getElementById("me-template").onchange = e => { const m=monsters.find(x=>x.type===e.target.value); if(!m) return; draft=normalize(m, custom.has(m.type)); idManual=custom.has(m.type); render(); };
    document.getElementById("me-name").oninput = e => { if (!idManual) document.getElementById("me-type").value = slug(e.target.value); updateCalculated(); };
    document.getElementById("me-type").oninput = () => { idManual = true; };
    root.querySelectorAll("input, select, textarea").forEach(el => { if (!el.id || !["me-name","me-type"].includes(el.id)) el.addEventListener("input", updateCalculated); el.addEventListener("change", updateCalculated); });
    ["me-size-w", "me-size-h", "me-oriented"].forEach(id => document.getElementById(id)?.addEventListener("change", () => { draft = read(); render(); }));
    root.querySelectorAll(".me-spell-tabs button").forEach(btn => btn.onclick = () => {
      const circle = btn.dataset.circle;
      root.querySelectorAll(".me-spell-tabs button").forEach(b => b.classList.toggle("active", b === btn));
      root.querySelectorAll(".me-spell-panel").forEach(panel => panel.hidden = panel.dataset.circle !== circle);
    });
    root.querySelectorAll(".me-spell-mode").forEach(select => select.onchange = () => {
      const card = select.closest(".me-spell-card");
      card.querySelector(".me-spell-limit-label").textContent = select.value === "cooldown" ? "rodadas" : "lançamentos";
      updateCalculated();
    });
    root.querySelectorAll('.me-spell-panel:not([data-circle="primeiro"])').forEach(panel => panel.hidden = true);
    root.querySelectorAll(".me-ability-tabs button").forEach(btn => btn.onclick = () => {
      const source = btn.dataset.source;
      root.querySelectorAll(".me-ability-tabs button").forEach(b => b.classList.toggle("active", b === btn));
      root.querySelectorAll(".me-ability-panel").forEach(panel => panel.hidden = panel.dataset.source !== source);
    });
    root.querySelectorAll('.me-ability-panel:not([data-source="heroi"])').forEach(panel => panel.hidden = true);
    // A escolha já envia a arte para os diretórios corretos. O campo oculto
    // mantém somente a chave estável do arquivo na ficha personalizada.
    const bindArtPicker = (inputId, kind, field, previewId) => {
      const input = document.getElementById(inputId);
      if (!input) return;
      input.onchange = async () => {
        const file = input.files && input.files[0];
        const status = document.getElementById("me-status");
        if (!file) return;
        if (!window.EDITOR_SAVE || !window.EDITOR_SAVE.uploadMonsterArt) {
          status.textContent = "Inicie o servidor para enviar a imagem."; status.className="me-error"; return;
        }
        status.textContent = "Enviando imagem…"; status.className = "";
        try {
          const key = await window.EDITOR_SAVE.uploadMonsterArt(file, kind);
          draft = read(); draft[field] = key;
          const preview = document.getElementById(previewId);
          if (preview) preview.src = kind === "miniature"
            ? `../assets/pawns/monstros/${key}/${key}.png?v=${Date.now()}`
            : `../assets/retratos/monstros/${key}.png?v=${Date.now()}`;
          // Há um campo legado de miniatura em fichas antigas: mantê-lo
          // sincronizado evita que uma edição posterior apague a escolha.
          root.querySelectorAll("#me-image").forEach(el => { if (field === "image") el.value = key; });
          document.getElementById("me-portrait").value = draft.portrait || draft.type;
          status.textContent = "✓ Imagem enviada. Salve a criatura para vincular a escolha."; status.className="me-ok";
        } catch (err) { status.textContent = "Não foi possível enviar a imagem: " + err.message; status.className="me-error"; }
      };
    };
    bindArtPicker("me-mini-file", "miniature", "image", "me-mini-preview");
    bindArtPicker("me-portrait-file", "portrait", "portrait", "me-portrait-preview");
    document.getElementById("me-add-attack").onclick = () => { draft = read(); draft.attacks.push({name:"Ataque",damage:"1d4",attack_attribute:"str_",base_attack_bonus:draft.base_attack_bonus,num_attacks:1}); render(); };
    root.querySelectorAll(".me-remove-attack").forEach(btn => btn.onclick = () => { draft=read(); if(draft.attacks.length > 1) draft.attacks.splice(Number(btn.dataset.i),1); render(); });
    document.getElementById("me-save").onclick = async () => {
      const monster = read(); const status = document.getElementById("me-status");
      if (monster.loot_table === null) { status.textContent = "Corrija o JSON do loot variável antes de salvar."; status.className="me-error"; return; }
      if (!window.EDITOR_SAVE || !window.EDITOR_SAVE.saveCustomMonster) { status.textContent = "Inicie o servidor para salvar a ficha."; status.className="me-error"; return; }
      status.textContent = "Salvando…"; status.className="";
      try { const saved = await window.EDITOR_SAVE.saveCustomMonster(monster); const arr=window.EDITOR_CUSTOM_MONSTERS || (window.EDITOR_CUSTOM_MONSTERS=[]); const old=arr.findIndex(x=>x.type===monster.original_type || x.type===saved.type); if(old>=0) arr.splice(old,1,saved); else arr.push(saved); if(window.EDITOR && window.EDITOR.catalog) { const c=window.EDITOR.catalog.monsters, ci=c.findIndex(x=>x.type===monster.original_type || x.type===saved.type); if(ci>=0)c.splice(ci,1,saved); else c.push(saved); } draft=normalize(saved,true); idManual=true; status.textContent="✓ Criatura salva e disponível no Bestiário e no editor de masmorras."; status.className="me-ok"; } catch (err) { status.textContent="Não foi possível salvar: " + err.message; status.className="me-error"; }
    };
    updateCalculated();
  }
  window.EDITOR_MONSTER_EDITOR = { render };
})();
