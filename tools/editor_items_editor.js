/* Editor de Itens — Fase 1: Armas. Espelha editor_monster_editor.js. */
(function () {
  "use strict";
  var root = document.getElementById("items-editor-view");
  var L = window.EDITOR_ITEMS_LOGIC;
  var esc = function (v) { return String(v == null ? "" : v).replace(/[&<>"']/g,
    function (c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];}); };
  var TYPES = [["armas","Armas",true],["armaduras","Armaduras",true],["escudos","Escudos",true],
    ["aneis","Anéis",false],["botas","Botas",false],["pocoes","Poções",false],
    ["arremessaveis","Arremessáveis",false],["venenos","Venenos",false]];
  var CLASSES = [["warrior","Guerreiro"],["mage","Mago"],["rogue","Ladino"],
    ["cleric","Clérigo"],["ranger","Patrulheiro"],["paladin","Paladino"],["bard","Bardo"]];

  var activeType = "armas";
  var draft = null, artFile = null, artURL = null;
  function novoDraft() {
    return { name:"", emoji:"⚔️", die_qtd:1, die_faces:8, categoria:"cortante",
      stat:"str_", finesse:false, manejo:"corpo", range:4, throw_range:3, ammo:"", two_handed:false,
      atk_bonus:0, damage_bonus:0, corrosao_livres:0, corrosao_penalidade:2, material:"metal",
      extra_damages:[], granted_ability:"", allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftArmor(kind) {
    return { name:"", emoji:"🛡️", item_type:(kind === "escudos" ? "shield" : "armor"),
      ac_bonus: 2, armor_category:"leve",
      materiais:{organic:false, metal:true}, corrosao_livres:0, corrosao_penalidade:2,
      bonuses:[], granted_ability:"", allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftFor(type) {
    return (type === "armaduras" || type === "escudos") ? novoDraftArmor(type) : novoDraft();
  }

  function baseWeapons() {
    return ((window.EDITOR_CATALOG || {}).items || []).filter(function (i) { return i.die && i.stat; });
  }
  function abilityOptions() {
    var libs = ((window.EDITOR_CATALOG || {}).monster_abilities || [])
      .filter(function (a) { return a.source === "heroi" || a.source === "guilda"; });
    return libs.map(function (a) { return { id: a.id, name: a.name }; });
  }

  function fromBase(item) {
    // "Basear em" empresta só os stats de combate da base (dado/nome/categoria/
    // atributo/finesse/duas mãos/manejo/alcance) — bônus, elemental, disponibilidade
    // e preço ficam nos valores padrão do rascunho, de propósito.
    var d = novoDraft();
    var m = /^(\d+)d(\d+)$/.exec(item.die || "1d6");
    if (m) { d.die_qtd = +m[1]; d.die_faces = +m[2]; }
    d.name = (item.name || "") + " (cópia)";
    d.categoria = item.categoria || "cortante";
    d.stat = item.stat === "dex" ? "dex" : "str_";
    d.finesse = !!item.finesse; d.two_handed = !!item.two_handed;
    if (item.reach === "lanca" || item.reach === "cajado") d.manejo = item.reach;
    else if (item.range) { d.manejo = "distancia"; d.range = item.range; }
    d.corrosao_livres = item.corrosao_resistente || 0;
    d.corrosao_penalidade = item.corrosao_niveis_penalidade || 2;
    return d;
  }

  function render() {
    if (!draft) draft = novoDraftFor(activeType);
    var subtabs = TYPES.map(function (t) {
      return '<button class="ie-subtab' + (t[0] === activeType ? " active" : "") + '"' +
        (t[2] ? "" : " disabled title='em breve'") + ' data-type="' + t[0] + '">' +
        esc(t[1]) + (t[2] ? "" : " 🔒") + "</button>";
    }).join("");
    root.innerHTML =
      '<div class="ie-subtabs">' + subtabs + '</div>' +
      '<div class="ie-body"><div class="ie-form" id="ie-form"></div>' +
      '<aside class="ie-preview" id="ie-preview"></aside></div>';
    root.querySelectorAll(".ie-subtab").forEach(function (b) {
      if (!b.disabled) b.onclick = function () {
        var type = b.dataset.type;
        if (type === activeType) return;
        activeType = type;
        draft = novoDraftFor(activeType);
        artFile = null;
        if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
        render();
      };
    });
    renderForm();
  }

  function renderForm() {
    var f = root.querySelector("#ie-form");
    if (activeType === "armaduras" || activeType === "escudos") {
      renderArmorForm(f);
      return;
    }
    var elemTypes = L.ELEM.map(function (e) { return '<option value="' + e + '">' + e + '</option>'; }).join("");
    var abil = abilityOptions();
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">') +
        campo("Basear em", selectBase())),
      seccao("Dano base",
        campo("Quantidade", numInput("ie-dieq", draft.die_qtd, 1, 10)) +
        campo("Dado", selectFaces()) +
        campo("Categoria", selectOpts("ie-cat", L.CATS, draft.categoria))),
      seccao("Atributo / manejo / alcance",
        campo("Atributo", selectOpts("ie-stat", ["str_","dex"], draft.stat)) +
        campo("Acuidade (usa Força ou Destreza no dano)", chk("ie-finesse", draft.finesse)) +
        campo("Manejo", selectOpts("ie-manejo",
          ["corpo","lanca","cajado","distancia","arremessavel"], draft.manejo)) +
        campo("Duas mãos", chk("ie-2m", draft.two_handed)) +
        manejoControls()),
      seccao("Bônus fixo (independentes)",
        campo("Bônus de acerto", numInput("ie-atkbonus", draft.atk_bonus, -5, 10)) +
        campo("Bônus de dano", numInput("ie-dmgbonus", draft.damage_bonus, -5, 10))),
      seccao("Durabilidade (corrosão)",
        campo("Níveis sem penalidade", numInput("ie-corrlivre", draft.corrosao_livres, 0, 12)) +
        campo("Níveis com penalidade", numInput("ie-corrpen", draft.corrosao_penalidade, 1, 12)) +
        campo("Material", '<select id="ie-material">' +
          '<option value="metal"' + (draft.material === "madeira" ? "" : " selected") + '>Metal (Devorador de Metal)</option>' +
          '<option value="madeira"' + (draft.material === "madeira" ? " selected" : "") + '>Madeira / orgânico (Devorador Orgânico)</option></select>') +
        '<span class="ie-hint">Aguenta N+M golpes de ácido e quebra no seguinte; a penalidade escala −1 por nível (até −M). O material define qual Devorador a corrói.</span>'),
      seccao("Dano elemental adicional",
        '<div id="ie-elems"></div><button id="ie-add-elem">+ linha</button>' +
        '<template id="ie-elem-tpl"><span class="ie-elem-row">' +
        numInput("", 1, 1, 10) + ' d' +
        '<select class="ie-elem-faces">' + [4,6,8,10,12].map(function(x){return "<option>"+x+"</option>";}).join("") + '</select>' +
        ' <select class="ie-elem-type">' + elemTypes + '</select>' +
        ' <button class="ie-elem-del">✕</button></span></template>'),
      seccao("Habilidade concedida (liga em fase futura)",
        campo("Habilidade", '<select id="ie-abil"><option value=""' + (draft.granted_ability ? "" : " selected") + '>— nenhuma —</option>' +
          abil.map(function (a) { return '<option value="' + esc(a.id) + '"' + (a.id === draft.granted_ability ? " selected" : "") + '>' + esc(a.name) + '</option>'; }).join("") + '</select>')),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Ferreiro)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro)),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar arma</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    bindForm();
    renderElems();
    renderPreview();
  }

  function renderArmorForm(f) {
    var isShield = activeType === "escudos";
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Defesa",
        campo("Bônus de CA", numInput("ie-ac", draft.ac_bonus, 0, 20)) +
        (isShield ? "" : campo("Categoria", selectOpts("ie-cat", L.ARMOR_CATS, draft.armor_category)))),
      seccao("Bônus adicionais",
        '<div id="ie-abonus"></div><button id="ie-add-abonus">+ bônus</button>' +
        '<template id="ie-abonus-tpl"><span class="ie-elem-row">' +
        '<select class="ie-abonus-eff"><option value="def_">CA extra</option>' +
        '<option value="maxhp">PV máx</option><option value="spd">Velocidade</option>' +
        '<option value="str_">Força</option><option value="dex">Destreza</option>' +
        '<option value="con_">Constituição</option><option value="int_">Inteligência</option>' +
        '<option value="initiative">Iniciativa</option>' +
        '<option value="resist">Resistência</option></select> ' +
        '<select class="ie-abonus-type" style="display:none"><option value="physical">Físico</option>' +
        '<option value="fire">Fogo</option><option value="cold">Frio</option><option value="lightning">Elétrico</option>' +
        '<option value="acid">Ácido</option><option value="holy">Sagrado</option><option value="poison">Veneno</option>' +
        '<option value="magic">Mágico</option><option value="water">Água</option></select> ' +
        numInput("", 0, -10, 20) + ' <button class="ie-abonus-del">✕</button></span></template>'),
      seccao("Durabilidade (corrosão)",
        campo("Níveis sem penalidade", numInput("ie-corrlivre", draft.corrosao_livres, 0, 12)) +
        campo("Níveis com penalidade", numInput("ie-corrpen", draft.corrosao_penalidade, 1, 12)) +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-organic"' + (draft.materiais.organic ? " checked" : "") + '> Orgânico (Devorador Orgânico)</label>' +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-metal"' + (draft.materiais.metal ? " checked" : "") + '> Metal (Devorador de Metal)</label>' +
        '<span class="ie-hint">Sem material marcado, a peça não corrói. Quebra em N+M+1.</span>'),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Ferreiro)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro)),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar peça</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    bindArmorForm();
    renderArmorBonuses();
    renderArmorPreview();
  }

  function currentArmorDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.ac_bonus = Math.max(0, +g("ie-ac").value || 0);
    var catEl = g("ie-cat"); if (catEl) draft.armor_category = catEl.value;
    draft.corrosao_livres = Math.max(0, +g("ie-corrlivre").value || 0);
    draft.corrosao_penalidade = Math.max(1, +g("ie-corrpen").value || 2);
    draft.materiais = { organic: g("ie-mat-organic").checked, metal: g("ie-mat-metal").checked };
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    draft.bonuses = Array.prototype.map.call(root.querySelectorAll("#ie-abonus .ie-elem-row"), function (r) {
      var eff = r.querySelector(".ie-abonus-eff").value;
      var o = { effect: eff, value: +r.querySelector("input[type=number]").value || 0 };
      if (eff === "resist") { var t = r.querySelector(".ie-abonus-type"); o.type = t ? t.value : "fire"; }
      return o; });
    return draft;
  }

  function renderArmorBonuses() {
    var box = root.querySelector("#ie-abonus"); box.innerHTML = "";
    (draft.bonuses || []).forEach(function (b) { addArmorBonusRow(b); });
  }
  function addArmorBonusRow(b) {
    var tpl = root.querySelector("#ie-abonus-tpl");
    var node = tpl.content.firstElementChild.cloneNode(true);
    var effSel = node.querySelector(".ie-abonus-eff");
    var typeSel = node.querySelector(".ie-abonus-type");
    function syncType() { typeSel.style.display = (effSel.value === "resist") ? "" : "none"; }
    if (b) {
      effSel.value = b.effect || "def_";
      node.querySelector("input[type=number]").value = (b.value == null ? 0 : b.value);
      if (b.effect === "resist" && b.type) typeSel.value = b.type;
    }
    node.querySelector(".ie-abonus-del").onclick = function () { node.remove(); renderArmorPreview(); };
    node.querySelectorAll("input,select").forEach(function (el) { el.onchange = renderArmorPreview; });
    effSel.addEventListener("change", syncType);
    syncType();
    root.querySelector("#ie-abonus").appendChild(node);
  }

  function renderArmorPreview() {
    currentArmorDraftFromForm();
    var item = L.serializeArmor(draft);
    var sug = L.suggestPriceArmor(item);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + sug + " 🪙";
    var parts = ["+" + item.ac_bonus + " CA"];
    if (item.armor_category) parts.push(item.armor_category);
    (item.bonuses || []).forEach(function (b) {
      var lbl = b.effect === "def_" ? "CA extra" : (b.effect === "maxhp" ? "PV máx" : "Velocidade");
      parts.push((b.value >= 0 ? "+" : "") + b.value + " " + lbl);
    });
    var matsLabel = (item.corrosion_materials || []).length ? item.corrosion_materials.join("+") : "nenhum";
    parts.push("🛡️ corrosão " + (item.corrosao_resistente || 0) + "+" + (item.corrosao_niveis_penalidade || 2) + " (" + matsLabel + ")");
    var topo = artURL
      ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindArmorForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderArmorPreview; el.oninput = renderArmorPreview;
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-add-abonus").onclick = function () { addArmorBonusRow(null); renderArmorPreview(); };
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderArmorPreview();
    };
    root.querySelector("#ie-save").onclick = onSaveArmor;
  }

  async function onSaveArmor() {
    currentArmorDraftFromForm();
    var v = L.validateArmorDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeArmor(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item);
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  function seccao(t, body) { return '<fieldset class="ie-sec"><legend>' + esc(t) + '</legend>' + body + '</fieldset>'; }
  function campo(l, ctrl) { return '<label class="ie-field"><span>' + esc(l) + '</span>' + ctrl + '</label>'; }
  function numInput(id, v, lo, hi) { return '<input type="number"' + (id ? ' id="' + id + '"' : ' class="ie-num"') +
    ' value="' + (+v || 0) + '" min="' + lo + '" max="' + hi + '">'; }
  function chk(id, on) { return '<input type="checkbox" id="' + id + '"' + (on ? " checked" : "") + '>'; }
  function chkLbl(id, l, on) { return '<label class="ie-field">' + chk(id, on) + ' ' + esc(l) + '</label>'; }
  function selectOpts(id, arr, sel) {
    return '<select id="' + id + '">' + arr.map(function (o) {
      return '<option value="' + esc(o) + '"' + (o === sel ? " selected" : "") + '>' + esc(o) + '</option>'; }).join("") + '</select>'; }
  function selectFaces() { return '<select id="ie-dief">' + [4,6,8,10,12].map(function (x) {
      return '<option' + (x === draft.die_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>'; }
  function selectBase() {
    return '<select id="ie-base"><option value="">— do zero —</option>' + baseWeapons().map(function (w) {
      return '<option value="' + esc(w.id) + '">' + esc(w.name) + '</option>'; }).join("") + '</select>'; }
  // Controles que dependem do manejo (alcance em quadrados + munição à distância).
  function manejoControls() {
    if (draft.manejo === "distancia") {
      return campo("Alcance (quadrados)", numInput("ie-range", draft.range, 1, 20)) +
        campo("Munição", '<select id="ie-ammo">' +
          '<option value=""' + (draft.ammo ? "" : " selected") + '>nenhuma</option>' +
          '<option value="flechas"' + (draft.ammo === "flechas" ? " selected" : "") + '>flechas</option>' +
          '<option value="virotes"' + (draft.ammo === "virotes" ? " selected" : "") + '>virotes</option></select>');
    }
    if (draft.manejo === "arremessavel")
      return campo("Alcance de arremesso (quadrados)", numInput("ie-throw", draft.throw_range, 1, 20));
    if (draft.manejo === "lanca" || draft.manejo === "cajado")
      return '<span class="ie-hint">Alcance estendido: 2 quadrados (' + esc(draft.manejo) + ').</span>';
    return '<span class="ie-hint">Corpo a corpo: alcance 1 (adjacente).</span>';
  }

  function currentDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.die_qtd = +g("ie-dieq").value; draft.die_faces = +g("ie-dief").value;
    draft.categoria = g("ie-cat").value; draft.stat = g("ie-stat").value;
    draft.finesse = g("ie-finesse").checked; draft.manejo = g("ie-manejo").value;
    draft.two_handed = g("ie-2m").checked;
    draft.atk_bonus = +g("ie-atkbonus").value || 0;
    draft.damage_bonus = +g("ie-dmgbonus").value || 0;
    draft.corrosao_livres = Math.max(0, +g("ie-corrlivre").value || 0);
    draft.corrosao_penalidade = Math.max(1, +g("ie-corrpen").value || 2);
    draft.material = g("ie-material").value;
    var rEl = g("ie-range"); if (rEl) draft.range = Math.max(1, +rEl.value || 4);
    var tEl = g("ie-throw"); if (tEl) draft.throw_range = Math.max(1, +tEl.value || 3);
    var aEl = g("ie-ammo"); if (aEl) draft.ammo = aEl.value;
    draft.granted_ability = g("ie-abil").value;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    draft.extra_damages = Array.prototype.map.call(root.querySelectorAll("#ie-elems .ie-elem-row"), function (r) {
      return { die: r.querySelector(".ie-num").value + "d" + r.querySelector(".ie-elem-faces").value, type: r.querySelector(".ie-elem-type").value }; });
    return draft;
  }

  function renderElems() {
    var box = root.querySelector("#ie-elems"); box.innerHTML = "";
    (draft.extra_damages || []).forEach(function (xd) { addElemRow(xd); });
  }
  function addElemRow(xd) {
    var tpl = root.querySelector("#ie-elem-tpl");
    var node = tpl.content.firstElementChild.cloneNode(true);
    if (xd) { var m = /^(\d+)d(\d+)$/.exec(xd.die || "1d6");
      if (m) { node.querySelector(".ie-num").value = m[1]; node.querySelector(".ie-elem-faces").value = m[2]; }
      node.querySelector(".ie-elem-type").value = xd.type || "fire"; }
    node.querySelector(".ie-elem-del").onclick = function () { node.remove(); renderPreview(); };
    node.querySelectorAll("input,select").forEach(function (el) { el.onchange = renderPreview; });
    root.querySelector("#ie-elems").appendChild(node);
  }

  function renderPreview() {
    currentDraftFromForm();
    var item = L.serializeWeapon(draft);
    var sug = L.suggestPrice(item);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + sug + " 🪙";
    var parts = [item.die + " " + item.categoria];
    (item.extra_damages || []).forEach(function (x) { parts.push("+" + x.die + " " + x.type); });
    if (item.damage_bonus) parts.push("+" + item.damage_bonus + " dano");
    if (item.atk_bonus) parts.push("+" + item.atk_bonus + " acerto");
    if (item.range) parts.push("🎯 alcance " + item.range);
    if (item.ammo) parts.push("🏹 " + item.ammo);
    if (item.throw_range) parts.push("↗️ arremesso " + item.throw_range);
    parts.push("🛡️ corrosão " + (item.corrosao_resistente || 0) + "+" + (item.corrosao_niveis_penalidade || 2) + " (" + (item.material || "metal") + ")");
    var topo = artURL
      ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindForm() {
    root.querySelector("#ie-base").onchange = function () {
      var id = this.value;
      var w = baseWeapons().filter(function (x) { return x.id === id; })[0];
      if (w) { draft = fromBase(w); renderForm(); }
    };
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-base" || el.id === "ie-art") return;
      el.onchange = renderPreview; el.oninput = renderPreview;
    });
    // Trocar o manejo muda quais controles de alcance/munição aparecem.
    root.querySelector("#ie-manejo").onchange = function () { currentDraftFromForm(); renderForm(); };
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-add-elem").onclick = function () { addElemRow(null); renderPreview(); };
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderPreview();
    };
    root.querySelector("#ie-save").onclick = onSave;
  }

  async function onSave() {
    currentDraftFromForm();
    var v = L.validateDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeWeapon(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item);
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  window.EDITOR_ITEMS_EDITOR = { render: render };
})();
