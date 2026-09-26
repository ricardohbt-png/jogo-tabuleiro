/* Bestiário de consulta. Os dados vêm de tools/export_catalog.py. */
(function () {
  "use strict";
  const root = document.getElementById("bestiary-view");
  let selected = null;
  let filter = "";

  const esc = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const list = () => (((window.EDITOR_CATALOG && window.EDITOR_CATALOG.monsters) || []).concat(window.EDITOR_CUSTOM_MONSTERS || []));
  const spellLibrary = () => (window.EDITOR_CATALOG && window.EDITOR_CATALOG.spells) || [];
  const mod = (score) => Math.floor((Number(score || 10) - 10) / 2);
  const visionRadius = m => Math.max(1, Number(m.movement_exception ? (m.movement != null ? m.movement : 6) : 6)
    + Number(m.vision_base != null ? m.vision_base : 0)
    + Math.floor((mod(m.dex) + mod(m.int_)) / 2));
  // Habilidades já presentes em monstros nativos que descrevem uma limitação.
  // Elas não podem ser somadas como poder ofensivo no ND.
  const NEGATIVE_ABILITIES = {
    fraqueza_magica:.12, mente_limitada:.10, mente_fraca:.12, mente_bruta:.12,
    concentracao_fragil:.08, concentracao_sombria:.08, essencia_profana:.22,
    furia_cega:.06, covardia_kobold:.06, lento_previsivel:.08,
    visao_limitada_ciclope:.06, ponto_cego_ciclope:.08,
    cercado_ciclope:.07, reflexos_lentos_ciclope:.08,
  };

  // Calibração do ND contra os seis heróis iniciais reais do servidor. Os
  // números abaixo espelham make_player + _check_level_up: equipamentos
  // iniciais, CA corrigida, Finesse, segunda adaga do Ladino e crítico 19–20
  // da espada curta do Paladino. O editor não importa server.py, portanto esta
  // é a representação declarativa compartilhada pela estimativa visual.
  const HERO_LEVELS = [1, 3, 5];
  const HERO_POWER = {
    warrior: {hp:[14,42,70], ac:12, attack:[6,8,10], die:"1d6", damage_mod:4},
    mage:    {hp:[7,21,35],   ac:12, attack:[2,4,6],   die:"1d6", damage_mod:1},
    rogue:   {hp:[9,27,45],   ac:16, attack:[5,7,9],   die:"1d4", damage_mod:4, offhand:true},
    cleric:  {hp:[10,30,50],  ac:13, attack:[1,3,5],   die:"1d6", damage_mod:0, damage_reduction:1},
    bard:    {hp:[9,27,45],   ac:14, attack:[4,6,8],   die:"1d4", damage_mod:3},
    paladin: {hp:[12,36,60],  ac:14, attack:[5,7,9],   die:"1d6", damage_mod:3, crit_min:19},
  };
  const HERO_ORDER = ["warrior", "mage", "rogue", "cleric", "bard", "paladin"];
  const HERO_GROUPS = {
    2: ["warrior", "cleric"],
    4: ["warrior", "rogue", "mage", "cleric"],
    6: HERO_ORDER,
  };
  const ENCOUNTER_ROUNDS = 3;
  // Perfil mecânico usado pelo estimador para que os vampiros não dependam
  // apenas de PV/CA. A ficha de jogo declara as mesmas regras, mas algumas
  // habilidades não possuem números no catálogo exportado.
  const VAMPIRE_PROFILES = {
    escravo_vampirico: {rd:5, regen:5, resurrection_factor:.50},
    vampiro_jovem:     {rd:5, regen:5, resurrection_factor:.50, charm_area_impact:0},
    vampiro_anciao:    {rd:5, regen:5, resurrection_factor:.50, charm_area_impact:.12, command_impact:.04},
    lorde_vampiro:     {rd:5, regen:5, resurrection_factor:.50, charm_area_impact:.16, command_impact:.06},
  };

  function vampireProfile(monster) {
    return monster && VAMPIRE_PROFILES[monster.type] || null;
  }
  function vampireWeaponReduction(monster) {
    const profile = vampireProfile(monster);
    return profile ? Number(profile.rd || 0) : 0;
  }
  function heroWeaponMitigation(monster) {
    const vampire = vampireProfile(monster);
    if (vampire) return {reduction:Number(vampire.rd || 0), multiplier:1};
    if (monster && monster.type === "lobisomem") return {reduction:0, multiplier:.5};
    return {reduction:0, multiplier:1};
  }

  function levelIndex(level) {
    const value = Number(level || 1);
    let index = 0;
    HERO_LEVELS.forEach((known, i) => { if (value >= known) index = i; });
    return index;
  }

  function diceParts(dice) {
    const match = String(dice || "").replace(/\s/g, "").match(/(\d*)d(\d+)([+-]\d+)?/i);
    return match ? {count:Number(match[1] || 1), faces:Number(match[2]), flat:Number(match[3] || 0)} : null;
  }
  function diceAverage(dice) {
    const p = diceParts(dice);
    return p ? p.count * (p.faces + 1) / 2 + p.flat : 0;
  }
  function expectedAttack(attack, ac, damage, critMin = 20, nat20Multiplier = 2) {
    let expected = 0;
    let hitProbability = 0;
    for (let roll = 1; roll <= 20; roll++) {
      const hit = roll === 20 || (roll !== 1 && roll + Number(attack || 0) >= ac);
      if (!hit) continue;
      hitProbability += 0.05;
      const critical = roll === 20 || (roll >= critMin && roll !== 1);
      const multiplier = critical ? (roll === 20 ? nat20Multiplier : 2) : 1;
      expected += damage * multiplier * 0.05;
    }
    return {dpr:expected, hitProbability};
  }
  function expectedAttackAfterReduction(attack, ac, damage, reduction = 0, critMin = 20, nat20Multiplier = 2) {
    return expectedAttackAfterMitigation(attack, ac, damage, reduction, 1, critMin, nat20Multiplier);
  }
  function expectedAttackAfterMitigation(attack, ac, damage, reduction = 0, damageMultiplier = 1, critMin = 20, nat20Multiplier = 2) {
    let expected = 0;
    let hitProbability = 0;
    const flatReduction = Math.max(0, Number(reduction || 0));
    const multiplierDamage = Math.max(0, Number(damageMultiplier || 1));
    for (let roll = 1; roll <= 20; roll++) {
      const hit = roll === 20 || (roll !== 1 && roll + Number(attack || 0) >= ac);
      if (!hit) continue;
      hitProbability += 0.05;
      const critical = roll === 20 || (roll >= critMin && roll !== 1);
      const multiplier = critical ? (roll === 20 ? nat20Multiplier : 2) : 1;
      expected += Math.max(0, damage * multiplierDamage * multiplier - flatReduction) * 0.05;
    }
    return {dpr:expected, hitProbability};
  }
  function heroAttack(hero, level, ac, bonusAttack = 0, bonusDamage = 0) {
    const damage = diceAverage(hero.die) + hero.damage_mod + bonusDamage;
    const attack = (hero.attack[levelIndex(level)] || hero.attack[0]) + Number(bonusAttack || 0);
    return expectedAttack(attack, ac,
      damage, hero.crit_min || 20, hero.nat20_multiplier || 2);
  }
  function heroWeaponAttack(hero, level, ac, monster, bonusAttack = 0, bonusDamage = 0) {
    const damage = diceAverage(hero.die) + hero.damage_mod + bonusDamage;
    const attack = (hero.attack[levelIndex(level)] || hero.attack[0]) + Number(bonusAttack || 0);
    const mitigation = heroWeaponMitigation(monster);
    const critMin = Number(monster && monster.crit_vulnerability_min_nat_roll) || hero.crit_min || 20;
    return expectedAttackAfterMitigation(attack, ac, damage, mitigation.reduction, mitigation.multiplier,
      critMin, hero.nat20_multiplier || 2);
  }
  function heroStats(id, level) {
    const hero = HERO_POWER[id];
    const index = levelIndex(level);
    const main = heroAttack(hero, level, 10);
    return {id, hero, hp:hero.hp[index] || hero.hp[0], ac:hero.ac,
      attack:hero.attack[index] || hero.attack[0], main};
  }
  function expectedReanimatedServants(level, groupSize) {
    // Reanimar os Mortos depende de haver cadáveres no mapa. Para não transformar
    // a habilidade em quatro ataques garantidos, usamos uma expectativa de
    // oportunidades por encontro e limitamos pelos slots disponíveis do mago.
    const corpseOpportunities = ({2:.5, 4:1, 6:1.25})[groupSize] || 1;
    const lowCrSaveChance = Math.min(.99, Math.max(.01,
      1 - (.25 * .20) + Math.max(1, Number(level || 1)) * .05));
    const controlSlots = 4 + Math.floor(Math.max(1, Number(level || 1)) / 2);
    return Math.min(controlSlots, corpseOpportunities * lowCrSaveChance);
  }
  function partyMetrics(level, monsterAC, includeHeroAbilities = true, groupSize = 6, monster = null) {
    const group = HERO_GROUPS[groupSize] || HERO_GROUPS[6];
    const heroes = group.map(id => heroStats(id, level));
    const songActive = includeHeroAbilities && group.includes("bard");
    let baseDpr = 0;
    let songDpr = 0;
    let burstBonus = 0;
    let totalHp = 0;
    let averageAC = 0;

    heroes.forEach(({id, hero, hp, ac, attack}) => {
      const main = heroWeaponAttack(hero, level, monsterAC, monster);
      let base = main.dpr;
      const songMain = heroWeaponAttack(hero, level, monsterAC, monster, 1, 1);
      let song = songActive ? songMain.dpr : base;
      if (hero.offhand) {
        // A segunda adaga usa o mesmo bônus de DES/Finesse e também recebe o
        // bônus de nível. No grupo inicial, só o Ladino tem arma secundária;
        // o Bardo começa com o Alaúde na mão do escudo.
        const mitigation = heroWeaponMitigation(monster);
        const off = expectedAttackAfterMitigation(attack, monsterAC, diceAverage("1d4") + 4,
          mitigation.reduction, mitigation.multiplier);
        base += off.dpr;
        const offSong = expectedAttackAfterMitigation(attack + 1, monsterAC, diceAverage("1d4") + 5,
          mitigation.reduction, mitigation.multiplier).dpr;
        song += songActive ? offSong : off.dpr;
      }
      baseDpr += base;
      songDpr += song;
      totalHp += hp;
      averageAC += ac;

      if (includeHeroAbilities && id === "warrior") {
        // Fúria concede um ataque principal extra por uma rodada.
        burstBonus += songMain.dpr;
      } else if (includeHeroAbilities && id === "rogue") {
        const sneakDice = level >= 5 ? 4 : (level >= 3 ? 3 : 2);
        burstBonus += songMain.hitProbability * sneakDice * 2.5;
      } else if (id === "paladin") {
        // Golpe Sagrado fica ativo após a ação bônus e adiciona +1d8 em cada
        // ataque enquanto houver manutenção; portanto é dano sustentado.
        if (includeHeroAbilities) {
          const holyMultiplier = vampireProfile(monster) ? 2 : 1;
          song += songMain.hitProbability * 4.5 * holyMultiplier;
        }
      } else if (includeHeroAbilities && id === "mage") {
        // Raio Congelante é a referência de alvo único e não permite save
        // contra o dano: 3d4 + 2d4 a cada dois níveis.
        const spellDice = 3 + 2 * Math.floor(level / 2);
        burstBonus += Math.max(0, spellDice * 2.5 - songMain.dpr);

        // Reanimar os Mortos: o estimador usa uma contribuição provável, não o
        // teto de quatro servos. Consideramos uma oportunidade média de cadáver
        // de baixo ND por encontro (0,5 / 1 / 1,25 para grupos de 2 / 4 / 6),
        // sucesso praticamente garantido contra esse alvo e o ataque simples
        // atualmente usado pelos servos. O mago perde um ataque na preparação.
        const expectedServants = expectedReanimatedServants(level, group.length);
        const mitigation = heroWeaponMitigation(monster);
        const servantDpr = expectedAttackAfterMitigation(2, monsterAC, diceAverage("1d4"),
          mitigation.reduction, mitigation.multiplier).dpr;
        burstBonus += Math.max(0, expectedServants * servantDpr * ENCOUNTER_ROUNDS - songMain.dpr);
      }
    });

    // A Canção Heroica com Acerto + Dano permanece ativa durante o encontro.
    // O Bardo não soma uma segunda arma porque o Alaúde ocupa a mão esquerda.
    const songDelta = Math.max(0, songDpr - baseDpr);
    const activeDpr = songDpr + burstBonus / ENCOUNTER_ROUNDS;
    return {heroes, baseDpr, songDpr, songDelta, burstBonus, activeDpr,
      totalHp, averageAC:averageAC / heroes.length};
  }
  function monsterEffectiveHp(m, metrics) {
    const profile = vampireProfile(m);
    if (!profile && m.type !== "lobisomem") return Number(m.hp || 0);
    if (m.type === "lobisomem") {
      // A magia do Mago bloqueia a regeneração depois do primeiro impacto;
      // sem uma fonte mágica no grupo, a regeneração funciona nas três rodadas.
      const regenRounds = metrics && metrics.heroes.some(h => h.id === "mage") ? 1 : ENCOUNTER_ROUNDS;
      return Number(m.hp || 0) + 2 * regenRounds;
    }
    let effectiveHp = Number(m.hp || 0);
    // A Cura Acelerada de 5 PV ocorre no início dos turnos; três rodadas é a
    // janela-base do estimador. Fogo/sagrado podem bloquear a cura, mas não
    // são garantidos no grupo de referência de quatro heróis.
    effectiveHp += Number(profile.regen || 0) * ENCOUNTER_ROUNDS;
    // Drenar Vida transforma a Mordida em sustentação. Estimamos a cura pela
    // média do ataque contra a CA média do grupo, sem criar dano adicional.
    const bite = (m.attacks || []).find(a => /mordida/i.test(String(a.name || "")));
    if (bite && metrics) {
      effectiveHp += expectedAttack(attackBonus(m, bite), metrics.averageAC,
        attackDamageAverage(m, bite)).dpr * ENCOUNTER_ROUNDS;
    }
    // A Ressurreição Vampírica acontece uma vez. O fator representa a chance
    // conservadora de a volta ocorrer dentro do encontro e não ser bloqueada
    // por fogo/luz/sagrado.
    effectiveHp += Number(m.hp || 0) * Number(profile.resurrection_factor || 0);
    return effectiveHp;
  }
  function vampireAbilityImpact(m) {
    const profile = vampireProfile(m);
    if (!profile) return 0;
    // Encantar em Área e Comandar Vampiros/Escravos são controle/suporte. A
    // ação de Encantar de alvo único já é reconhecida por specialImpact().
    return Number(profile.charm_area_impact || 0) + Number(profile.command_impact || 0);
  }
  function monsterAbilityImpact(m) {
    if (m.type === "lobisomem") return .03; // Olfato reduz o valor da furtividade do Ladino.
    return vampireAbilityImpact(m);
  }
  function attackBonus(m, a) {
    if (a.base_attack_bonus != null || m.base_attack_bonus != null)
      return Number(a.base_attack_bonus != null ? a.base_attack_bonus : m.base_attack_bonus || 0) + mod(m[(a.attack_attribute || (a.range ? "dex" : "str_"))]) + Number(m.equipment_attack_bonus || 0);
    return Number(a.atk_bonus != null ? a.atk_bonus : m.atk_bonus || 0) + Number(m.equipment_attack_bonus || 0);
  }
  function attackDamageAverage(m, a) {
    const attr = a.attack_attribute || (a.range ? "dex" : "str_");
    const damageAttr = a.damage_attribute || attr;
    return average(a.damage) + average(a.extra_damage) + average(a.fire_damage)
      + (a.apply_attribute_damage ? mod(m[damageAttr]) : 0);
  }
  function attackDamageText(m, a) {
    const attr = a.attack_attribute || (a.range ? "dex" : "str_");
    const bonus = a.apply_attribute_damage ? mod(m[a.damage_attribute || attr]) : 0;
    return `${a.damage || m.damage || "—"}${bonus ? (bonus > 0 ? "+" : "") + bonus : ""}`;
  }
  const pretty = (v) => String(v || "—").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  function equipmentPreview(monster) {
    const m = JSON.parse(JSON.stringify(monster));
    if (!m.equipment_enabled) return m;
    const catalog = new Map((((window.EDITOR_CATALOG || {}).items) || []).map(item => [item.id, item]));
    const items = (m.equipped_items || m.equipment || []).map(id => catalog.get(id)).filter(Boolean);
    const weapon = items.find(item => item.die);
    if (weapon) {
      const configuredAttack = (m.attacks || [])[0] || {};
      const attr = weapon.stat === "dex" ? "dex" : "str_";
      m.attacks = [{name:weapon.name, damage:weapon.die, attack_attribute:attr, apply_attribute_damage:true,
        base_attack_bonus:Number(m.base_attack_bonus || 0), num_attacks:1, range:Number(weapon.range || 0), categoria:weapon.categoria,
        on_hit:configuredAttack.on_hit, poison_dc:configuredAttack.poison_dc,
        extra_damage:configuredAttack.extra_damage, extra_damage_types:configuredAttack.extra_damage_types || []}];
    }
    m.ac = Number(m.ac || 10) + items.reduce((sum, item) => sum + Number(item.ac_bonus || 0) + (item.effect === "def_" ? Number(item.value || 0) : 0), 0);
    m.hp = Number(m.hp || 0) + items.reduce((sum, item) => sum + (item.effect === "maxhp" ? Number(item.value || 0) : 0), 0);
    m.movement = Number(m.movement || 0) + items.reduce((sum, item) => sum + (item.effect === "spd" ? Number(item.value || 0) : 0), 0);
    m.equipment_attack_bonus = items.reduce((sum, item) => sum + (item.effect === "atk" ? Number(item.value || 0) : 0), 0);
    return m;
  }
  function average(dice) {
    const m = String(dice || "").replace(/\s/g, "").match(/(\d*)d(\d+)([+-]\d+)?/i);
    return m ? (Number(m[1] || 1) * (Number(m[2]) + 1) / 2) + Number(m[3] || 0) : 0;
  }
  function monsterSpells(m) {
    if (Array.isArray(m.monster_spells) && m.monster_spells.length) return m.monster_spells;
    return (m.special_abilities || []).filter(a => a.action_type === "magia")
      .map(a => ({id:a.id, limit_mode:a.cooldown_turns != null ? "cooldown" : "encounter", uses_per_combat:a.uses_per_combat || 1, cooldown_turns:a.cooldown_turns || 1}));
  }
  function spellPower(m) {
    const byId = new Map(spellLibrary().map(s => [s.id, s]));
    const casterLevel = Math.max(1, Number(m.caster_level || m.level || 1));
    const base = monsterSpells(m).reduce((sum, cfg) => {
      const s = byId.get(cfg.id); if (!s) return sum;
      const circle = ({primeiro:.42, segundo:.72, terceiro:1.05})[s.circulo] || .4;
      const availability = cfg.limit_mode === "cooldown"
        ? Math.min(1.35, .55 + .18 / Math.max(1, Number(cfg.cooldown_turns || 1)))
        : Math.min(1.5, .5 + .25 * Math.max(1, Number(cfg.uses_per_combat || 1)));
      const effect = (s.save ? .10 : 0) + (s.area_raio || s.area_lado ? .16 : 0)
        + (s.dano || s.dano_base || s.dano_por_nivel ? .18 : 0)
        + (s.buff || s.debuff ? .12 : 0);
      return sum + (circle + effect) * availability;
    }, 0);
    // Nível 1 é a referência. Cada nível acima reforça as escalas reais do
    // grimório (dano, alcance e duração), sem afetar criaturas sem magias.
    return base * (1 + (casterLevel - 1) * .16);
  }
  function ndEstimateLegacy(m) {
    // Four level-1 heroes: warrior, rogue, cleric and mage, basic equipment.
    // An equal-ND encounter should take roughly 3–4 rounds and consume resources.
    const PARTY_AC = 12;
    const partyAttackers = [
      {attack:5, damage:7.5}, {attack:4, damage:11.5},
      {attack:0, damage:3.5}, {attack:-1, damage:2.5},
    ];
    const hitChance = (attack, ac) => Math.max(.05, Math.min(.95, (21 + attack - ac) / 20));
    const attacks = m.attacks && m.attacks.length ? m.attacks : [{damage:m.damage, atk_bonus:m.atk_bonus, num_attacks:1}];
    const partyDpr = partyAttackers.reduce((sum, h) => sum + h.damage * hitChance(h.attack, Number(m.ac || 10)), 0);
    const roundsToDefeat = Number(m.hp || 0) / Math.max(1, partyDpr);
    const monsterDpr = attacks.reduce((sum, a) => sum + attackDamageAverage(m, a) * Number(a.num_attacks || 1) * hitChance(attackBonus(m, a), PARTY_AC), 0);
    const durability = roundsToDefeat * .35;
    // Dano esperado contra a CA média do grupo mede a ameaça ofensiva.
    const offense = monsterDpr / 8;
    // Iniciativa tem impacto pequeno: os atributos já são refletidos em combate.
    const initiativeImpact = Math.max(-.12, Math.min(.12, (Number(m.dex || 10) + mod(m.int_)) * .03));
    // Habilidades tornam o encontro mais perigoso; vulnerabilidades reais fazem
    // o inverso. A estimativa é deliberadamente conservadora e arredondada a ¼ ND.
    const specialList = m.special_abilities || [];
    const specials = specialList.filter(a => a.action_type !== "magia" && !Object.prototype.hasOwnProperty.call(NEGATIVE_ABILITIES, a.id))
      .reduce((sum, a) => {
        const uses = Math.max(1, Number(a.uses_per_day != null ? a.uses_per_day : a.uses_per_combat || 1));
        const cooldown = Math.max(0, Number(a.cooldown_turns || 0));
        // Mais usos e recarga curta tornam o poder disponível em mais turnos.
        const availability = Math.min(1.3, .55 + uses * .14 + (cooldown ? .18 / cooldown : .12));
        const relevantPassive = a.dc || a.damage || a.effect || a.source === "heroi" || a.source === "guilda"
          || ["ataque_das_sombras","cacador_das_trevas","combo_devorador","furia","investida_brutal","resistencia_morta","agarrar","constricao","derrubar","atq_mandibula","esmagar"].includes(a.id);
        const base = a.action_type === "passiva" ? (relevantPassive ? .12 : 0) : .22;
        return sum + (base + (a.dc ? .10 : 0) + (a.damage ? .12 : 0)) * availability;
      }, 0);
    const weaknessPenalty = (m.weaknesses || []).reduce((sum, w) => {
      if (w.type === "ponto_vulneravel") return sum + Math.max(0, Number(w.nd_penalty != null ? w.nd_penalty : .25));
      if (Number(w.multiplier) > 1) return sum + .16 * (Number(w.multiplier) - 1);
      if (Number(w.bonus_flat) > 0) return sum + Math.min(.14, .04 + Number(w.bonus_flat) * .025);
      if (w.type === "save_penalty") return sum + .07;
      return sum + .04;
    }, 0);
    const resistanceBonus = (m.resistances || []).reduce((sum, r) => sum + (r.mode === "half" ? .32 : .07 * Math.max(1, Number(r.reduction || 1))), 0);
    // Uma limitação sem entrada equivalente em weaknesses recebe a penalidade
    // reduzida aqui. As que já têm fraqueza mecânica não são descontadas duas vezes.
    const explicitTypes = new Set((m.weaknesses || []).map(w => w.type));
    const implicitNegativePenalty = specialList.reduce((sum, a) => {
      const alreadyExplicit = (a.id === "essencia_profana" && explicitTypes.has("holy"))
        || (["fraqueza_magica", "mente_limitada", "mente_fraca", "mente_bruta"].includes(a.id) && explicitTypes.has("save_penalty"));
      return sum + (!alreadyExplicit && NEGATIVE_ABILITIES[a.id] ? NEGATIVE_ABILITIES[a.id] * .6 : 0);
    }, 0);
    const defenses = ((m.immunities || []).length * .07) + resistanceBonus - weaknessPenalty - implicitNegativePenalty;
    const spellImpact = spellPower(m) * .38;
    return Math.max(.25, Math.round((durability + offense + specials + spellImpact + defenses + initiativeImpact) * 4) / 4);
  }
  // Recalibração: usa a composição real de seis heróis e permite comparar
  // apenas os números básicos contra a ficha completa com habilidades.
  function monsterDprForState(m, metrics, bonusAttack = 0, bonusDamage = 0) {
    const attacks = m.attacks && m.attacks.length ? m.attacks : [{damage:m.damage, atk_bonus:m.atk_bonus, num_attacks:1}];
    return metrics.heroes.reduce((sum, hero) => {
      const targetDpr = attacks.reduce((subtotal, a) => subtotal
        + expectedAttackAfterReduction(attackBonus(m, a) + bonusAttack, hero.ac,
          attackDamageAverage(m, a) + bonusDamage, hero.hero.damage_reduction || 0).dpr
          * Number(a.num_attacks || 1), 0);
      return sum + targetDpr;
    }, 0) / Math.max(1, metrics.heroes.length);
  }
  function monsterDprAgainstParty(m, metrics) {
    const normal = monsterDprForState(m, metrics);
    if (m.type !== "lobisomem") return normal;
    // A parte final da luta ocorre com a Fúria ativa quando o monstro cai a
    // 12 PV. Uma rodada em três é uma expectativa conservadora.
    const furia = monsterDprForState(m, metrics, 2, 2);
    return normal * (2 / 3) + furia / 3;
  }
  function specialImpact(m) {
    const specialList = m.special_abilities || [];
    return specialList.filter(a => a.action_type !== "magia" && !Object.prototype.hasOwnProperty.call(NEGATIVE_ABILITIES, a.id))
      .filter(a => !(vampireProfile(m) && a.id === "reducao_vampirica"))
      .filter(a => !(m.type === "lobisomem" && ["pele_amaldicoada", "regeneracao_lobisomem", "furia_bestial_lobisomem"].includes(a.id)))
      .reduce((sum, a) => {
        const uses = Math.max(1, Number(a.uses_per_day != null ? a.uses_per_day : a.uses_per_combat || 1));
        const cooldown = Math.max(0, Number(a.cooldown_turns || 0));
        const availability = Math.min(1.3, .55 + uses * .14 + (cooldown ? .18 / cooldown : .12));
        const description = `${a.name || ""} ${a.descricao || ""} ${a.effect || ""}`.toLowerCase();
        const control = /imobil|preso|engol|paralis|lento|empurr|agarr|constr|medo|cego|petrif/.test(description);
        const area = a.radius || a.area || a.cone || a.shape || /área|cone|adjacente|todos/.test(description);
        const damage = a.damage || a.extra_damage || a.initial_dice || a.automatic_damage || /dano|d\d+/.test(description);
        const relevantPassive = a.dc || damage || control || a.effect || a.source === "heroi" || a.source === "guilda"
          || ["ataque_das_sombras","cacador_das_trevas","combo_devorador","furia","investida_brutal","resistencia_morta","agarrar","constricao","derrubar","atq_mandibula","esmagar"].includes(a.id);
        const base = a.action_type === "passiva" ? (relevantPassive ? .12 : 0) : .20;
        return sum + (base + (a.dc || a.poison_dc ? .08 : 0) + (damage ? .10 : 0)
          + (control ? .08 : 0) + (area ? .06 : 0)) * availability;
      }, 0);
  }
  function weaknessImpact(m) {
    return (m.weaknesses || []).reduce((sum, w) => {
      // A prata não faz parte do equipamento inicial; não conceda ao grupo
      // uma exploração que ele ainda não possui.
      if (m.type === "lobisomem" && w.type === "silver") return sum;
      if (m.type === "ciclope" && w.type === "ciclope_olho_unico") return sum + .28;
      if (w.type === "ponto_vulneravel") return sum + Math.max(0, Number(w.nd_penalty != null ? w.nd_penalty : .25));
      if (Number(w.multiplier) > 1) return sum + .16 * (Number(w.multiplier) - 1);
      if (Number(w.bonus_flat) > 0) return sum + Math.min(.14, .04 + Number(w.bonus_flat) * .025);
      if (w.type === "save_penalty") return sum + .07;
      return sum + .04;
    }, 0);
  }
  function defenseImpact(m) {
    // A RD física vampírica já é aplicada diretamente ao dano das armas na
    // partyMetrics(). Não a conte novamente como bônus abstrato de defesa.
    const resistanceBonus = (m.resistances || []).reduce((sum, r) => {
      if (vampireProfile(m) && r.type === "physical") return sum;
      return sum + (r.mode === "half" ? .32 : .07 * Math.max(1, Number(r.reduction || 1)));
    }, 0);
    const explicitTypes = new Set((m.weaknesses || []).map(w => w.type));
    const negativePenalty = (m.special_abilities || []).reduce((sum, a) => {
      const alreadyExplicit = (a.id === "essencia_profana" && explicitTypes.has("holy"))
        || (["fraqueza_magica", "mente_limitada", "mente_fraca", "mente_bruta"].includes(a.id) && explicitTypes.has("save_penalty"));
      return sum + (!alreadyExplicit && NEGATIVE_ABILITIES[a.id] ? NEGATIVE_ABILITIES[a.id] * .6 : 0);
    }, 0);
    return ((m.immunities || []).length * .07) + resistanceBonus - weaknessImpact(m) - negativePenalty;
  }
  function ndEstimateAtLevel(rawMonster, level = 1, mode = "abilities", groupSize = 6) {
    const m = equipmentPreview(rawMonster || {});
    const monsterAC = Number(m.ac || 10);
    const metrics = partyMetrics(level, monsterAC, mode !== "base", groupSize, m);
    const partyDpr = mode === "base" ? metrics.baseDpr : metrics.activeDpr;
    const roundsToDefeat = monsterEffectiveHp(m, metrics) / Math.max(1, partyDpr);
    const monsterDpr = monsterDprAgainstParty(m, metrics);
    // ND 1 representa aproximadamente três rodadas contra o grupo escolhido.
    const durability = roundsToDefeat / ENCOUNTER_ROUNDS;
    const offense = monsterDpr * ENCOUNTER_ROUNDS / Math.max(1, metrics.totalHp);
    const initiativeImpact = Math.max(-.12, Math.min(.12, (Number(m.dex || 10) + mod(m.int_)) * .03));
    // O modo Base remove apenas as habilidades dos heróis. As habilidades e
    // magias do próprio monstro continuam contando para o ND da criatura.
    const specials = specialImpact(m) + monsterAbilityImpact(m);
    const defenses = defenseImpact(m);
    const spellImpact = spellPower(m) * .38;
    const raw = .25 + durability * .60 + offense * .40 + specials + spellImpact + defenses + initiativeImpact;
    return Math.max(.25, Math.round(raw * 4) / 4);
  }
  function ndEstimate(m) {
    return ndEstimateAtLevel(m, 1, "abilities");
  }
  function estimateNDProfiles(m) {
    return HERO_LEVELS.map(level => ({
      level,
      groups: Object.fromEntries([2, 4, 6].map(groupSize => [groupSize, {
        base: ndEstimateAtLevel(m, level, "base", groupSize),
        abilities: ndEstimateAtLevel(m, level, "abilities", groupSize),
      }])),
    }));
  }
  function nd(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return String(v || "—");
    const whole = Math.floor(n), fraction = Math.round((n - whole) * 4) / 4;
    const suffix = ({0.25:"¼", 0.5:"½", 0.75:"¾"})[fraction] || "";
    return suffix ? `${whole || ""}${suffix}` : String(whole);
  }
  function cooldown(a) {
    const uses = a.uses_per_day != null ? `${a.uses_per_day}× por dia` : (a.uses_per_combat != null ? `${a.uses_per_combat}× por combate` : "");
    const cd = a.cooldown_turns != null ? (a.cooldown_turns ? `recarga: ${a.cooldown_turns} rod.` : "sem recarga") : (a.cooldown != null ? `recarga: ${a.cooldown}` : "");
    return [uses, cd].filter(Boolean).join(" · ") || (a.action_type === "passiva" ? "Passiva" : "Sem limite informado");
  }
  function imageBox(src, cls, fallback, alternateSrc = "") {
    // Retratos antigos podem ter sido salvos com o id da miniatura (campo
    // `image`) em vez do id interno da criatura (campo `type`). Tenta o padrão
    // oficial primeiro e, se ele não existir, usa esse nome alternativo.
    const onError = "const alt=this.dataset.alt;if(alt){this.dataset.alt='';this.src=alt}else{this.remove();this.parentElement.classList.add('empty')}";
    return `<div class="${cls}"><img src="${esc(src)}" data-alt="${esc(alternateSrc)}" alt="" onerror="${onError}"><span>${esc(fallback)}</span></div>`;
  }
  function loot(m) {
    const rows = [];
    if (Array.isArray(m.weapon_options) && m.weapon_options.length) {
      rows.push(`Armas disponíveis: ${m.weapon_options.map(w => `${w.name || w.id} (${w.damage || "dano não definido"})`).join(", ")}`);
    }
    if (m.shield_option) {
      rows.push(`${m.shield_option.name || "Escudo opcional"}: +${Number(m.shield_option.ac_bonus || 0)} CA${m.shield_option.equipped_by_default ? " (equipado)" : " (opcional)"}`);
    }
    const equipped = m.equipped_items || m.equipment;
    if (equipped && (Array.isArray(equipped) ? equipped.length : true)) rows.push(`${m.equipment_enabled ? "Equipado e ativo" : "Equipamento"}: ${Array.isArray(equipped) ? equipped.map(pretty).join(", ") : pretty(equipped)}`);
    if (m.guaranteed_loot) rows.push(`Garantido: ${Array.isArray(m.guaranteed_loot) ? m.guaranteed_loot.map(x => pretty(x.name || x.id || x)).join(", ") : pretty(m.guaranteed_loot.name || m.guaranteed_loot.id || m.guaranteed_loot)}`);
    if (m.loot_drops && m.loot_drops.length) rows.push(`Drops: ${m.loot_drops.map(d => d.kind === "gold" ? `${d.amount} ouro (${d.chance}%)` : `${pretty(d.item_id)} (${d.chance}%)`).join(", ")}`);
    if (m.gold != null) rows.push(`${m.gold} ouro`);
    if (m.loot_table) rows.push("Tesouro variável (tabela de loot)");
    return rows.length ? rows.map(esc).join("<br>") : "Nenhum tesouro definido.";
  }
  function details(m) {
    const rawMonster = m;
    m = equipmentPreview(m);
    const ndProfiles = estimateNDProfiles(rawMonster);
    const groupProfileText = mode => [2, 4, 6].map(groupSize => {
      const values = ndProfiles.map(p => `N${p.level}: ${nd(p.groups[groupSize][mode])}`).join(" · ");
      return `${groupSize} heróis: ${values}`;
    }).join(" | ");
    const profileText = groupProfileText("abilities");
    const baseProfileText = groupProfileText("base");
    const attacks = m.attacks && m.attacks.length ? m.attacks : [{name:"Ataque", atk_bonus:m.atk_bonus, damage:m.damage, num_attacks:1}];
    const abilities = (m.special_abilities || []).filter(a => a.action_type !== "magia");
    const spellsById = new Map(spellLibrary().map(s => [s.id, s]));
    const spells = monsterSpells(m).map(cfg => Object.assign({}, spellsById.get(cfg.id), cfg)).filter(s => s.id);
    const weaknesses = (m.weaknesses || []).map(w => w.descricao || `${pretty(w.categoria || w.type)} ${w.multiplier ? "×" + w.multiplier : (w.bonus_flat > 0 ? "+" : "") + (w.bonus_flat || "")}`).join(" · ") || "Nenhuma definida";
    const resistanceText = r => `${pretty(r.categoria || r.type)}${Array.isArray(r.exclude) && r.exclude.length ? ` (exceto ${r.exclude.map(pretty).join(", ")})` : ""} ${r.mode === "half" ? "(metade do dano)" : "(-" + (r.reduction || 1) + ")"}`;
    const perception = m.percepcao != null ? m.percepcao : 10 + Math.floor(visionRadius(m) / 2);
    return `<article class="best-card">
      <section class="best-media">${imageBox(`../assets/retratos/monstros/${m.portrait || m.type}.png`, "best-portrait", "Retrato\na adicionar", m.image && m.image !== (m.portrait || m.type) ? `../assets/retratos/monstros/${m.image}.png` : "")}${imageBox(`../assets/pawns/monstros/${m.image || m.type}/${m.image || m.type}.png`, "best-mini", "Miniatura\nindisponível")}</section>
      <section class="best-sheet"><header class="best-head"><div><h1>${esc(m.emoji || "") } ${esc(m.name)}</h1><p><strong>Subtipo: ${esc(({construto:"Construto",morto_vivo:"Morto-Vivo",animal:"Animal",abissal:"Abissal",vegetal:"Vegetal",raca_padrao:"Raça Padrão"})[m.subtipo || (m.undead ? "morto_vivo" : "raca_padrao")] || "Raça Padrão")}</strong></p><p>${esc(m.type)} · IA: <strong>${esc(pretty(m.ai_type))}</strong></p></div><div class="nd-pair"><span>ND definido <b>${esc(nd(m.cr != null ? m.cr : m.tier || "—"))}</b></span><span title="Estimativa contra grupos de 2, 4 e 6 heróis, considerando habilidades.">ND estimado (6 heróis) <b>${esc(nd(ndProfiles[0].groups[6].abilities))}</b><small>${esc(profileText)}</small><small title="Grupo sem habilidades próprias, mas contando as habilidades do monstro">Sem habilidades dos heróis: ${esc(baseProfileText)}</small></span></div></header>
      <div class="best-stats"><div><b>PV</b><span>${esc(m.hp || "—")}</span></div><div><b>CA total</b><span>${esc(m.ac || "—")}</span></div><div><b>Armadura natural</b><span>${esc(m.natural_armor != null ? m.natural_armor : Math.max(0, Number(m.ac || 10) - 10 - mod(m.dex)))}</span></div><div><b>Movimento</b><span>${esc(m.movement || "—")}</span></div><div><b>Raio de visão</b><span title="${m.visao_escuro || m.darkvision_range ? "Visão no escuro: objetos não bloqueiam, apenas paredes." : "Objetos altos e paredes bloqueiam a visão."}">${esc(visionRadius(m))}${m.visao_escuro || m.darkvision_range ? " 👁️" : ""}</span></div><div><b>Ataques</b><span>${attacks.reduce((n,a) => n + Number(a.num_attacks || 1), 0)}</span></div><div><b>Iniciativa</b><span>${esc(Number(m.dex || 10) + mod(m.int_))}</span></div><div><b>Percepção</b><span>${esc(perception)}</span></div></div>
      <p class="best-perception-note"><b>Percepção:</b> valor base da ficha; aliados vivos a até 3 casas podem conceder +1 durante furtividade.</p>
      <div class="best-attributes"><div><b>FOR</b>${esc(m.str_ != null ? m.str_ : "—")} <small>${m.str_ != null ? (mod(m.str_) >= 0 ? "+" : "") + mod(m.str_) : ""}</small></div><div><b>DES</b>${esc(m.dex != null ? m.dex : "—")} <small>${m.dex != null ? (mod(m.dex) >= 0 ? "+" : "") + mod(m.dex) : ""}</small></div><div><b>CON</b>${esc(m.con_ != null ? m.con_ : "—")} <small>${m.con_ != null ? (mod(m.con_) >= 0 ? "+" : "") + mod(m.con_) : ""}</small></div><div><b>INT</b>${esc(m.int_ != null ? m.int_ : "—")} <small>${m.int_ != null ? (mod(m.int_) >= 0 ? "+" : "") + mod(m.int_) : ""}</small></div></div>
      <div class="best-saves"><div><b>Fortitude</b><span>${esc(m.fort != null ? (m.fort >= 0 ? "+" : "") + m.fort : "—")}</span><small>CON</small></div><div><b>Reflexos</b><span>${esc(m.ref_ != null ? (m.ref_ >= 0 ? "+" : "") + m.ref_ : "—")}</span><small>DES</small></div><div><b>Vontade</b><span>${esc(m.will != null ? (m.will >= 0 ? "+" : "") + m.will : "—")}</span><small>INT</small></div></div>
      <div class="best-grid"><section><h2>Ataques</h2><table><thead><tr><th>Ataque</th><th>Base</th><th>Acerto</th><th>Dano</th><th>Qtd.</th></tr></thead><tbody>${attacks.map(a => { const attr=a.attack_attribute || (a.range ? "dex" : "str_"); const special=[a.extra_damage ? `+ ${a.extra_damage} ${pretty((a.extra_damage_types||[])[0])}` : "", a.on_hit ? `Veneno CD ${a.poison_dc || 10}` : ""].filter(Boolean).join(" · "); return `<tr><td>${esc(a.name || "Ataque")}${special ? `<small>${esc(special)}</small>` : ""}</td><td>${esc(attr === "dex" ? "Destreza" : "Força")}</td><td>+${esc(attackBonus(m, a))}</td><td>${esc(attackDamageText(m, a))}</td><td>${esc(a.num_attacks || 1)}</td></tr>`; }).join("")}</tbody></table></section>
      <section><h2>Habilidades especiais</h2><div class="best-abilities">${abilities.length ? abilities.map(a => `<div><strong>${esc(a.name || pretty(a.id))}</strong><small>${esc(pretty(a.action_type))} · ${esc(cooldown(a))}${a.dc ? ` · CD ${esc(a.dc)} (${esc(pretty(a.save))})` : ""}</small>${a.descricao ? `<p>${esc(a.descricao)}</p>` : ""}</div>`).join("") : "<p>Sem habilidades especiais definidas.</p>"}</div></section>
      <section><h2>Magias</h2><p><b>Nível de conjurador:</b> ${esc(m.caster_level || m.level || 1)}</p><div class="best-abilities">${spells.length ? spells.map(s => `<div><strong>${esc(s.icone || "✦")} ${esc(s.nome || pretty(s.id))}</strong><small>${esc(pretty(s.circulo))} círculo · ${s.limit_mode === "cooldown" ? `recarga: ${esc(s.cooldown_turns || 1)} rodada(s)` : `${esc(s.uses_per_combat || 1)}× por encontro`}</small>${s.descricao ? `<p>${esc(s.descricao)}</p>` : ""}</div>`).join("") : "<p>Não conhece magias.</p>"}</div></section>
      <section><h2>Defesas e fraquezas</h2><p><b>Imunidades:</b> ${esc((m.immunities || []).map(pretty).join(", ") || "Nenhuma definida")}</p><p><b>Resistências:</b> ${esc((m.resistances || []).map(resistanceText).join(", ") || "Nenhuma definida")}</p><p><b>Fraquezas:</b> ${esc(weaknesses)}</p></section>
      <section><h2>Equipamento e tesouro</h2><p>${loot(m)}</p><p class="best-note">Recompensa base: ${esc(m.xp != null ? m.xp + " XP" : "não definida")}</p></section></div>
      <footer class="best-method">ND estimado: calculado separadamente para grupos de 2, 4 e 6 heróis, nos níveis 1, 3 e 5. A primeira linha inclui as habilidades dos heróis; a segunda remove apenas essas habilidades, mantendo as habilidades e magias do monstro. Grupos de monstros devem ser avaliados como encontro combinado.</footer>
      </section></article>`;
  }
  function render() {
    // A lista é recriada ao selecionar uma criatura. Preserve a posição antes
    // de substituir o HTML; sem isso, cada clique devolve o bestiário ao topo.
    const previousList = root.querySelector(".best-list");
    const listScrollTop = previousList ? previousList.scrollTop : 0;
    const monsters = list();
    if (!selected && monsters.length) selected = monsters[0].type;
    const q = filter.trim().toLocaleLowerCase("pt-BR");
    const shown = monsters.filter(m => !q || `${m.name} ${m.type} ${m.ai_type || ""}`.toLocaleLowerCase("pt-BR").includes(q));
    const current = monsters.find(m => m.type === selected) || shown[0] || monsters[0];
    if (current) selected = current.type;
    root.innerHTML = `<div class="best-layout"><aside class="best-list"><label>Buscar criatura<input id="best-search" value="${esc(filter)}" placeholder="nome, tipo ou IA"></label><div class="best-count">${shown.length} criatura${shown.length === 1 ? "" : "s"}</div>${shown.map(m => `<button class="best-row ${m.type === selected ? "selected" : ""}" data-type="${esc(m.type)}"><span>${esc(m.emoji || "◈")}</span><span><b>${esc(m.name)}</b><small>ND ${esc(nd(m.cr != null ? m.cr : m.tier || "—"))} · ${esc(pretty(m.ai_type))}</small></span></button>`).join("") || "<p class=\"best-none\">Nenhuma criatura encontrada.</p>"}</aside><main class="best-detail">${current ? details(current) : ""}</main></div>`;
    const nextList = root.querySelector(".best-list");
    if (nextList) nextList.scrollTop = listScrollTop;
    const search = document.getElementById("best-search");
    search.oninput = () => { filter = search.value; render(); };
    root.querySelectorAll(".best-row").forEach(btn => btn.onclick = () => { selected = btn.dataset.type; render(); });
  }
  window.EDITOR_BESTIARY = {
    render,
    estimateND: ndEstimate,
    estimateNDAtLevel: ndEstimateAtLevel,
    estimateNDProfiles,
    formatND: nd,
    details,
  };
})();
