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
  const visionRadius = m => Math.max(0, Number(m.vision_base != null ? m.vision_base : 3)
    + Math.floor((mod(m.dex) + mod(m.int_)) / 2));
  // Habilidades já presentes em monstros nativos que descrevem uma limitação.
  // Elas não podem ser somadas como poder ofensivo no ND.
  const NEGATIVE_ABILITIES = {
    fraqueza_magica:.12, mente_limitada:.10, mente_fraca:.12, mente_bruta:.12,
    concentracao_fragil:.08, concentracao_sombria:.08, essencia_profana:.22,
    furia_cega:.06, covardia_kobold:.06, lento_previsivel:.08,
  };
  function attackBonus(m, a) {
    if (a.base_attack_bonus != null || m.base_attack_bonus != null)
      return Number(a.base_attack_bonus != null ? a.base_attack_bonus : m.base_attack_bonus || 0) + mod(m[(a.attack_attribute || (a.range ? "dex" : "str_"))]);
    return Number(a.atk_bonus != null ? a.atk_bonus : m.atk_bonus || 0);
  }
  function attackDamageAverage(m, a) {
    const attr = a.attack_attribute || (a.range ? "dex" : "str_");
    return average(a.damage) + (a.apply_attribute_damage ? mod(m[attr]) : 0);
  }
  function attackDamageText(m, a) {
    const attr = a.attack_attribute || (a.range ? "dex" : "str_");
    const bonus = a.apply_attribute_damage ? mod(m[attr]) : 0;
    return `${a.damage || m.damage || "—"}${bonus ? (bonus > 0 ? "+" : "") + bonus : ""}`;
  }
  const pretty = (v) => String(v || "—").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
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
  function ndEstimate(m) {
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
    const initiativeImpact = Math.max(-.12, Math.min(.12, (mod(m.dex) + mod(m.int_)) * .03));
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
  function imageBox(src, cls, fallback) {
    return `<div class="${cls}"><img src="${esc(src)}" alt="" onerror="this.remove();this.parentElement.classList.add('empty')"><span>${esc(fallback)}</span></div>`;
  }
  function loot(m) {
    const rows = [];
    if (m.equipment) rows.push(`Equipamento: ${Array.isArray(m.equipment) ? m.equipment.map(pretty).join(", ") : pretty(m.equipment)}`);
    if (m.guaranteed_loot) rows.push(`Garantido: ${Array.isArray(m.guaranteed_loot) ? m.guaranteed_loot.map(x => pretty(x.name || x.id || x)).join(", ") : pretty(m.guaranteed_loot.name || m.guaranteed_loot.id || m.guaranteed_loot)}`);
    if (m.gold != null) rows.push(`${m.gold} ouro`);
    if (m.loot_table) rows.push("Tesouro variável (tabela de loot)");
    return rows.length ? rows.map(esc).join("<br>") : "Nenhum tesouro definido.";
  }
  function details(m) {
    const attacks = m.attacks && m.attacks.length ? m.attacks : [{name:"Ataque", atk_bonus:m.atk_bonus, damage:m.damage, num_attacks:1}];
    const abilities = (m.special_abilities || []).filter(a => a.action_type !== "magia");
    const spellsById = new Map(spellLibrary().map(s => [s.id, s]));
    const spells = monsterSpells(m).map(cfg => Object.assign({}, spellsById.get(cfg.id), cfg)).filter(s => s.id);
    const weaknesses = (m.weaknesses || []).map(w => w.descricao || `${pretty(w.categoria || w.type)} ${w.multiplier ? "×" + w.multiplier : (w.bonus_flat > 0 ? "+" : "") + (w.bonus_flat || "")}`).join(" · ") || "Nenhuma definida";
    return `<article class="best-card">
      <section class="best-media">${imageBox(`../assets/retratos/monstros/${m.type}.png`, "best-portrait", "Retrato\na adicionar")}${imageBox(`../assets/pawns/monstros/${m.image || m.type}/${m.image || m.type}.png`, "best-mini", "Miniatura\nindisponível")}</section>
      <section class="best-sheet"><header class="best-head"><div><h1>${esc(m.emoji || "") } ${esc(m.name)}</h1><p>${esc(m.type)} · IA: <strong>${esc(pretty(m.ai_type))}</strong></p></div><div class="nd-pair"><span>ND definido <b>${esc(nd(m.cr != null ? m.cr : m.tier || "—"))}</b></span><span title="Estimativa de consulta baseada em defesa, dano, ataques e habilidades.">ND estimado <b>${esc(nd(ndEstimate(m)))}</b></span></div></header>
      <div class="best-stats"><div><b>PV</b><span>${esc(m.hp || "—")}</span></div><div><b>CA total</b><span>${esc(m.ac || "—")}</span></div><div><b>Armadura natural</b><span>${esc(m.natural_armor != null ? m.natural_armor : Math.max(0, Number(m.ac || 10) - 10 - mod(m.dex)))}</span></div><div><b>Movimento</b><span>${esc(m.movement || "—")}</span></div><div><b>Raio de visão</b><span title="${m.visao_escuro || m.darkvision_range ? "Visão no escuro: objetos não bloqueiam, apenas paredes." : "Objetos altos e paredes bloqueiam a visão."}">${esc(visionRadius(m))}${m.visao_escuro || m.darkvision_range ? " 👁️" : ""}</span></div><div><b>Ataques</b><span>${attacks.reduce((n,a) => n + Number(a.num_attacks || 1), 0)}</span></div><div><b>Iniciativa</b><span>${esc((mod(m.dex) + mod(m.int_)) >= 0 ? "+" + (mod(m.dex) + mod(m.int_)) : mod(m.dex) + mod(m.int_))}</span></div></div>
      <div class="best-attributes"><div><b>FOR</b>${esc(m.str_ != null ? m.str_ : "—")} <small>${m.str_ != null ? (mod(m.str_) >= 0 ? "+" : "") + mod(m.str_) : ""}</small></div><div><b>DES</b>${esc(m.dex != null ? m.dex : "—")} <small>${m.dex != null ? (mod(m.dex) >= 0 ? "+" : "") + mod(m.dex) : ""}</small></div><div><b>CON</b>${esc(m.con_ != null ? m.con_ : "—")} <small>${m.con_ != null ? (mod(m.con_) >= 0 ? "+" : "") + mod(m.con_) : ""}</small></div><div><b>INT</b>${esc(m.int_ != null ? m.int_ : "—")} <small>${m.int_ != null ? (mod(m.int_) >= 0 ? "+" : "") + mod(m.int_) : ""}</small></div></div>
      <div class="best-saves"><div><b>Fortitude</b><span>${esc(m.fort != null ? (m.fort >= 0 ? "+" : "") + m.fort : "—")}</span><small>CON</small></div><div><b>Reflexos</b><span>${esc(m.ref_ != null ? (m.ref_ >= 0 ? "+" : "") + m.ref_ : "—")}</span><small>DES</small></div><div><b>Vontade</b><span>${esc(m.will != null ? (m.will >= 0 ? "+" : "") + m.will : "—")}</span><small>INT</small></div></div>
      <div class="best-grid"><section><h2>Ataques</h2><table><thead><tr><th>Ataque</th><th>Base</th><th>Acerto</th><th>Dano</th><th>Qtd.</th></tr></thead><tbody>${attacks.map(a => { const attr=a.attack_attribute || (a.range ? "dex" : "str_"); return `<tr><td>${esc(a.name || "Ataque")}</td><td>${esc(attr === "dex" ? "Destreza" : "Força")}</td><td>+${esc(attackBonus(m, a))}</td><td>${esc(attackDamageText(m, a))}</td><td>${esc(a.num_attacks || 1)}</td></tr>`; }).join("")}</tbody></table></section>
      <section><h2>Habilidades especiais</h2><div class="best-abilities">${abilities.length ? abilities.map(a => `<div><strong>${esc(a.name || pretty(a.id))}</strong><small>${esc(pretty(a.action_type))} · ${esc(cooldown(a))}${a.dc ? ` · CD ${esc(a.dc)} (${esc(pretty(a.save))})` : ""}</small>${a.descricao ? `<p>${esc(a.descricao)}</p>` : ""}</div>`).join("") : "<p>Sem habilidades especiais definidas.</p>"}</div></section>
      <section><h2>Magias</h2><p><b>Nível de conjurador:</b> ${esc(m.caster_level || m.level || 1)}</p><div class="best-abilities">${spells.length ? spells.map(s => `<div><strong>${esc(s.icone || "✦")} ${esc(s.nome || pretty(s.id))}</strong><small>${esc(pretty(s.circulo))} círculo · ${s.limit_mode === "cooldown" ? `recarga: ${esc(s.cooldown_turns || 1)} rodada(s)` : `${esc(s.uses_per_combat || 1)}× por encontro`}</small>${s.descricao ? `<p>${esc(s.descricao)}</p>` : ""}</div>`).join("") : "<p>Não conhece magias.</p>"}</div></section>
      <section><h2>Defesas e fraquezas</h2><p><b>Imunidades:</b> ${esc((m.immunities || []).map(pretty).join(", ") || "Nenhuma definida")}</p><p><b>Resistências:</b> ${esc((m.resistances || []).map(r => `${pretty(r.categoria || r.type)} ${r.mode === "half" ? "(metade do dano)" : "(-" + (r.reduction || 1) + ")"}`).join(", ") || "Nenhuma definida")}</p><p><b>Fraquezas:</b> ${esc(weaknesses)}</p></section>
      <section><h2>Equipamento e tesouro</h2><p>${loot(m)}</p><p class="best-note">Recompensa base: ${esc(m.xp != null ? m.xp + " XP" : "não definida")}</p></section></div>
      <footer class="best-method">ND estimado: calibrado contra um grupo inicial de quatro heróis. Mede sobrevivência contra o grupo, dano esperado, controle, magias, habilidades e defesas; grupos de monstros devem ser avaliados como encontro combinado.</footer>
      </section></article>`;
  }
  function render() {
    const monsters = list();
    if (!selected && monsters.length) selected = monsters[0].type;
    const q = filter.trim().toLocaleLowerCase("pt-BR");
    const shown = monsters.filter(m => !q || `${m.name} ${m.type} ${m.ai_type || ""}`.toLocaleLowerCase("pt-BR").includes(q));
    const current = monsters.find(m => m.type === selected) || shown[0] || monsters[0];
    if (current) selected = current.type;
    root.innerHTML = `<div class="best-layout"><aside class="best-list"><label>Buscar criatura<input id="best-search" value="${esc(filter)}" placeholder="nome, tipo ou IA"></label><div class="best-count">${shown.length} criatura${shown.length === 1 ? "" : "s"}</div>${shown.map(m => `<button class="best-row ${m.type === selected ? "selected" : ""}" data-type="${esc(m.type)}"><span>${esc(m.emoji || "◈")}</span><span><b>${esc(m.name)}</b><small>ND ${esc(nd(m.cr != null ? m.cr : m.tier || "—"))} · ${esc(pretty(m.ai_type))}</small></span></button>`).join("") || "<p class=\"best-none\">Nenhuma criatura encontrada.</p>"}</aside><main class="best-detail">${current ? details(current) : ""}</main></div>`;
    const search = document.getElementById("best-search");
    search.oninput = () => { filter = search.value; render(); };
    root.querySelectorAll(".best-row").forEach(btn => btn.onclick = () => { selected = btn.dataset.type; render(); });
  }
  window.EDITOR_BESTIARY = { render, estimateND: ndEstimate };
})();
