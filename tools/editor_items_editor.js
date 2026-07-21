/* Editor de Itens — Fase 1: Armas. Espelha editor_monster_editor.js. */
(function () {
  "use strict";
  var root = document.getElementById("items-editor-view");
  var L = window.EDITOR_ITEMS_LOGIC;
  var esc = function (v) { return String(v == null ? "" : v).replace(/[&<>"']/g,
    function (c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];}); };
  var TYPES = [["armas","Armas",true],["armaduras","Armaduras",false],["escudos","Escudos",false],
    ["aneis","Anéis",false],["botas","Botas",false],["pocoes","Poções",false],
    ["arremessaveis","Arremessáveis",false],["venenos","Venenos",false]];
  var CLASSES = [["warrior","Guerreiro"],["mage","Mago"],["rogue","Ladino"],
    ["cleric","Clérigo"],["ranger","Patrulheiro"],["paladin","Paladino"],["bard","Bardo"]];

  var draft = null, artFile = null;
  function novoDraft() {
    return { name:"", emoji:"⚔️", die_qtd:1, die_faces:8, categoria:"cortante",
      stat:"str_", finesse:false, manejo:"corpo", range:4, throw_range:3, two_handed:false,
      atk_bonus:0, damage_bonus:0, bonus_alvo:"dano", extra_damages:[],
      granted_ability:"", allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
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
    var d = novoDraft();
    var m = /^(\d+)d(\d+)$/.exec(item.die || "1d6");
    if (m) { d.die_qtd = +m[1]; d.die_faces = +m[2]; }
    d.name = (item.name || "") + " (cópia)";
    d.categoria = item.categoria || "cortante";
    d.stat = item.stat === "dex" ? "dex" : "str_";
    d.finesse = !!item.finesse; d.two_handed = !!item.two_handed;
    if (item.reach === "lanca" || item.reach === "cajado") d.manejo = item.reach;
    else if (item.range) { d.manejo = "distancia"; d.range = item.range; }
    return d;
  }

  function render() {
    if (!draft) draft = novoDraft();
    var subtabs = TYPES.map(function (t) {
      return '<button class="ie-subtab' + (t[0] === "armas" ? " active" : "") + '"' +
        (t[2] ? "" : " disabled title='em breve'") + ' data-type="' + t[0] + '">' +
        esc(t[1]) + (t[2] ? "" : " 🔒") + "</button>";
    }).join("");
    root.innerHTML =
      '<div class="ie-subtabs">' + subtabs + '</div>' +
      '<div class="ie-body"><div class="ie-form" id="ie-form"></div>' +
      '<aside class="ie-preview" id="ie-preview"></aside></div>';
    root.querySelectorAll(".ie-subtab").forEach(function (b) {
      if (!b.disabled) b.onclick = function () { renderForm(); };
    });
    renderForm();
  }

  function renderForm() {
    var f = root.querySelector("#ie-form");
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
      seccao("Atributo / manejo",
        campo("Atributo", selectOpts("ie-stat", ["str_","dex"], draft.stat)) +
        campo("Acuidade (finesse)", chk("ie-finesse", draft.finesse)) +
        campo("Manejo", selectOpts("ie-manejo",
          ["corpo","lanca","cajado","distancia","arremessavel"], draft.manejo)) +
        campo("Duas mãos", chk("ie-2m", draft.two_handed))),
      seccao("Bônus fixo",
        campo("Aplica em", selectOpts("ie-bonusalvo", ["ataque","dano"], draft.bonus_alvo)) +
        campo("Valor", numInput("ie-bonusval", 0, -5, 10))),
      seccao("Dano elemental adicional",
        '<div id="ie-elems"></div><button id="ie-add-elem">+ linha</button>' +
        '<template id="ie-elem-tpl"><span class="ie-elem-row">' +
        numInput("", 1, 1, 10) + ' d' +
        '<select class="ie-elem-faces">' + [4,6,8,10,12].map(function(x){return "<option>"+x+"</option>";}).join("") + '</select>' +
        ' <select class="ie-elem-type">' + elemTypes + '</select>' +
        ' <button class="ie-elem-del">✕</button></span></template>'),
      seccao("Habilidade concedida (liga em fase futura)",
        campo("Habilidade", '<select id="ie-abil"><option value="">— nenhuma —</option>' +
          abil.map(function (a) { return '<option value="' + esc(a.id) + '">' + esc(a.name) + '</option>'; }).join("") + '</select>')),
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

  function currentDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.die_qtd = +g("ie-dieq").value; draft.die_faces = +g("ie-dief").value;
    draft.categoria = g("ie-cat").value; draft.stat = g("ie-stat").value;
    draft.finesse = g("ie-finesse").checked; draft.manejo = g("ie-manejo").value;
    draft.two_handed = g("ie-2m").checked;
    draft.bonus_alvo = g("ie-bonusalvo").value;
    var bv = +g("ie-bonusval").value || 0;
    draft.atk_bonus = draft.bonus_alvo === "ataque" ? bv : 0;
    draft.damage_bonus = draft.bonus_alvo === "dano" ? bv : 0;
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
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card"><div class="ie-card-emoji">' + esc(item.emoji) + '</div>' +
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
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-add-elem").onclick = function () { addElemRow(null); renderPreview(); };
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
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
