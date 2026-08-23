/* Editor de Itens — Fase 1: Armas. Espelha editor_monster_editor.js. */
(function () {
  "use strict";
  var root = document.getElementById("items-editor-view");
  var L = window.EDITOR_ITEMS_LOGIC;
  var esc = function (v) { return String(v == null ? "" : v).replace(/[&<>"']/g,
    function (c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];}); };
  var TYPES = [["armas","Armas",true],["armaduras","Armaduras",true],["escudos","Escudos",true],
    ["aneis","Anéis",true],["botas","Botas",true],["pocoes","Poções",true],
    ["arremessaveis","Arremessáveis",true],["venenos","Venenos",true]];
  var CLASSES = [["warrior","Guerreiro"],["mage","Mago"],["rogue","Ladino"],
    ["cleric","Clérigo"],["ranger","Patrulheiro"],["paladin","Paladino"],["bard","Bardo"]];

  var activeType = "armas";
  var draft = null, artFile = null, artURL = null;
  var previewFn = function () {};
  function novoDraft() {
    return { name:"", emoji:"⚔️", die_qtd:1, die_faces:8, categoria:"cortante",
      stat:"str_", finesse:false, manejo:"corpo", range:4, throw_range:3, ammo:"", two_handed:false,
      atk_bonus:0, damage_bonus:0, corrosao_livres:0, corrosao_penalidade:2, material:"metal",
      extra_damages:[], granted_ability:"", maldicao_id:"", maldicao_prende:false, allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftArmor(kind) {
    return { name:"", emoji:"🛡️", item_type:(kind === "escudos" ? "shield" : "armor"),
      ac_bonus: 2, armor_category:"leve",
      materiais:{organic:false, metal:true}, corrosao_livres:0, corrosao_penalidade:2,
      bonuses:[], granted_ability:"", maldicao_id:"", maldicao_prende:false, allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftAccessory(kind) {
    return { name:"", emoji:(kind === "botas" ? "👢" : "💍"),
      item_type:(kind === "botas" ? "boots" : "ring"),
      bonuses:[], materiais:{organic:false, metal:true}, corrosao_livres:0, corrosao_penalidade:2,
      granted_ability:"", maldicao_id:"", maldicao_prende:false, allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftPotion() {
    return { name:"", emoji:"🧪", item_type:"potion", effect:"heal", value:10, max_uses:1,
      imun_qtd:1, imun_faces:4,
      allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftThrowable() {
    return { name:"", emoji:"💥", item_type:"throwable", alvo:"ataque_alvo", alcance:4,
      area_raio:1, save_cd:12, tem_dano:true, die_qtd:2, die_faces:6, elemento:"fogo",
      em_chamas:false, chamas_qtd:1, chamas_faces:4, chamas_agua_apaga:true,
      allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftPoison() {
    return { name:"", emoji:"☠️", item_type:"poison", operacao:"dano", descricao:"",
      save:"fortitude", dificuldade:12, anula:true, dur_qtd:1, dur_faces:6,
      dano_fixo:false, dano_valor:1, dano_qtd:1, dano_faces:4, modelo_save:"aplicacao",
      atributo:"forca", val_qtd:1, val_faces:4,
      atributos:[{chave:"ataque", valor:1}],
      durfalha_qtd:1, durfalha_faces:4, penalidade_falha:[{chave:"movimento", valor:1}],
      penalidade_ataque:4, bloqueia_distancia:false,
      allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftFor(type) {
    if (type === "armaduras" || type === "escudos") return novoDraftArmor(type);
    if (type === "aneis" || type === "botas") return novoDraftAccessory(type);
    if (type === "pocoes") return novoDraftPotion();
    if (type === "arremessaveis") return novoDraftThrowable();
    if (type === "venenos") return novoDraftPoison();
    return novoDraft();
  }

  function baseWeapons() {
    return ((window.EDITOR_CATALOG || {}).items || []).filter(function (i) { return i.die && i.stat; });
  }
  // Fase I: só habilidades que o motor realmente concede — técnicas e
  // especializações da Guilda, e a amostra de habilidades de herói.
  // Mantida em sincronia com GameRoom.GRANTED_HERO_SKILLS (server.py) — há um
  // teste que compara as duas listas (test_editor_itens.py, seção [J6]).
  var GRANTED_HERO_IDS = ["hero_rogue_detectar_armadilhas",
                          "hero_rogue_esconder_sombras",
                          "hero_paladin_imposicao_maos",
                          "hero_cleric_cura", "hero_cleric_cura_area",
                          "hero_cleric_purificacao", "hero_cleric_ressurreicao",
                          "hero_rogue_criar_armadilha", "hero_rogue_veneno_rapido",
                          "hero_paladin_golpe_sagrado", "hero_paladin_protetor",
                          "hero_paladin_regeneracao_divina", "hero_paladin_guerreiro_luz",
                          "hero_bard_provocacao", "hero_rogue_desarmar_armadilha"];
  function abilityGroups() {
    var libs = (window.EDITOR_CATALOG || {}).monster_abilities || [];
    var tec = [], esp = [], her = [], armas = [];
    libs.forEach(function (a) {
      if (a.source === "guilda" && a.guild_category === "tecnica") tec.push(a);
      else if (a.source === "guilda" && a.guild_category === "especializacao") esp.push(a);
      else if (a.source === "heroi" && GRANTED_HERO_IDS.indexOf(a.id) >= 0) her.push(a);
      else if (a.source === "arma" || (a.id === "causar_sangramento" && activeType === "armas")) armas.push(a);
    });
    return [["Técnicas da Guilda", tec], ["Especializações da Guilda", esp],
            ["Habilidades de Herói", her], ["Habilidades de Armas", armas]];
  }
  // Campo reusado pelos 5 formulários de item equipável.
  function campoHabilidade() {
    var grupos = abilityGroups().map(function (g) {
      if (!g[1].length) return "";
      return '<optgroup label="' + esc(g[0]) + '">' + g[1].map(function (a) {
        return '<option value="' + esc(a.id) + '"' +
          (a.id === draft.granted_ability ? " selected" : "") + '>' + esc(a.name) + '</option>';
      }).join("") + '</optgroup>';
    }).join("");
    return campo("Habilidade", '<select id="ie-abil"><option value=""' +
      (draft.granted_ability ? "" : " selected") + '>— nenhuma —</option>' + grupos + '</select>');
  }
  function campoMaldicao() {
    // A lista mora em editor_items_logic.js (CURSES), que é quem também valida
    // o id na serialização — duas cópias dos mesmos 25 ids divergiriam.
    var curses = L.CURSES;
    return seccao("Item amaldiçoado", campo("Maldição ao equipar", '<select id="ie-maldicao"><option value="">— nenhuma —</option>' + curses.map(function(x){return '<option value="'+x[0]+'"'+(draft.maldicao_id===x[0]?' selected':'')+'>'+x[1]+'</option>';}).join('')) + '<label class="ie-field"><input id="ie-maldicao-prende" type="checkbox"'+(draft.maldicao_prende?' checked':'')+'> Prende ao equipar até a maldição ser curada <small>Purificação: +5 fome/+5 sede. Templo: +100 ouro.</small></label>');
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
    d.granted_ability = item.granted_ability || "";
    if (item.throw_range) { d.manejo = "arremessavel"; d.throw_range = item.throw_range; }
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
        citySel = null;   // volta ao padrão de cidades do novo tipo de item
        artFile = null;
        if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
        render();
      };
    });
    renderForm();
  }

  function renderForm() {
    renderFormBody();
    ensureCities();          // 1ª vez: preenche o bloco de cidades quando chegar
    aplicarEstadoCidades();
  }

  function renderFormBody() {
    var f = root.querySelector("#ie-form");
    if (activeType === "armaduras" || activeType === "escudos") {
      renderArmorForm(f);
      return;
    }
    if (activeType === "aneis" || activeType === "botas") {
      renderAccessoryForm(f, activeType === "botas" ? "boots" : "ring");
      return;
    }
    if (activeType === "pocoes") { renderPotionForm(f); return; }
    if (activeType === "arremessaveis") { renderThrowableForm(f); return; }
    if (activeType === "venenos") { renderPoisonForm(f); return; }
    var elemTypes = L.ELEM.map(function (e) { return '<option value="' + e + '">' + e + '</option>'; }).join("");
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
        campo("Acuidade (usa Força ou Destreza no acerto e dano)", chk("ie-finesse", draft.finesse)) +
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
      seccao("Habilidade concedida (ativa ao equipar)", campoHabilidade()),
      campoMaldicao(),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Ferreiro)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro) +
        dispCidades()),
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
        abonusTemplate()),
      seccao("Durabilidade (corrosão)",
        campo("Níveis sem penalidade", numInput("ie-corrlivre", draft.corrosao_livres, 0, 12)) +
        campo("Níveis com penalidade", numInput("ie-corrpen", draft.corrosao_penalidade, 1, 12)) +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-organic"' + (draft.materiais.organic ? " checked" : "") + '> Orgânico (Devorador Orgânico)</label>' +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-metal"' + (draft.materiais.metal ? " checked" : "") + '> Metal (Devorador de Metal)</label>' +
        '<span class="ie-hint">Sem material marcado, a peça não corrói. Quebra em N+M+1.</span>'),
      seccao("Habilidade concedida (ativa ao equipar)", campoHabilidade()),
      campoMaldicao(),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Ferreiro)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro) +
        dispCidades()),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar peça</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderArmorPreview;
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
    var ab = g("ie-abil"); if (ab) draft.granted_ability = ab.value;
    draft.maldicao_id = g("ie-maldicao") ? g("ie-maldicao").value : "";
    draft.maldicao_prende = !!g("ie-maldicao-prende")?.checked && !!draft.maldicao_id;
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
    node.querySelector(".ie-abonus-del").onclick = function () { node.remove(); previewFn(); };
    node.querySelectorAll("input,select").forEach(function (el) { el.onchange = previewFn; });
    effSel.addEventListener("change", syncType);
    syncType();
    root.querySelector("#ie-abonus").appendChild(node);
  }

  // Rótulos dos "bônus adicionais" (motor de multi-efeito) — compartilhado
  // pelos previews de armadura/escudo e de anel/bota.
  var BONUS_LBL = { def_:"CA extra", maxhp:"PV máx", spd:"velocidade", atk_bonus:"acerto",
    str_:"Força", dex:"Destreza", con_:"CON", int_:"INT", initiative:"iniciativa",
    vision:"visão" };
  function bonusLabel(b) {
    if (b.effect === "resist") return "resist " + (b.type || "");
    return BONUS_LBL[b.effect] || b.effect;
  }

  function renderArmorPreview() {
    currentArmorDraftFromForm();
    var item = L.serializeArmor(draft);
    var sug = L.suggestPriceArmor(item);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + sug + " 🪙";
    var parts = ["+" + item.ac_bonus + " CA"];
    if (item.armor_category) parts.push(item.armor_category);
    (item.bonuses || []).forEach(function (b) {
      parts.push((b.value >= 0 ? "+" : "") + b.value + " " + bonusLabel(b));
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
      var saved = await window.EDITOR_SAVE.saveCustomItem(item, cidadesSelecionadas());
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  function renderAccessoryForm(f, kind) {
    var isBoots = kind === "boots";
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Bônus (motor de efeitos)",
        '<div id="ie-abonus"></div><button id="ie-add-abonus">+ bônus</button>' +
        abonusTemplate()),
      isBoots ? seccao("Durabilidade (corrosão)",
        campo("Níveis sem penalidade", numInput("ie-corrlivre", draft.corrosao_livres, 0, 12)) +
        campo("Níveis com penalidade", numInput("ie-corrpen", draft.corrosao_penalidade, 1, 12)) +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-organic"' + (draft.materiais.organic ? " checked" : "") + '> Orgânico (Devorador Orgânico)</label>' +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-metal"' + (draft.materiais.metal ? " checked" : "") + '> Metal (Devorador de Metal)</label>' +
        '<span class="ie-hint">Sem material marcado, a peça não corrói. Quebra em N+M+1.</span>') : "",
      seccao("Habilidade concedida (ativa ao equipar)", campoHabilidade()),
      campoMaldicao(),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Mercador)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro) +
        dispCidades()),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar ' + (isBoots ? "botas" : "anel") + '</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderAccessoryPreview;
    bindAccessoryForm();
    renderArmorBonuses();          // popula #ie-abonus a partir de draft.bonuses (genérico)
    renderAccessoryPreview();
  }

  function currentAccessoryDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    draft.bonuses = Array.prototype.map.call(root.querySelectorAll("#ie-abonus .ie-elem-row"), function (r) {
      var eff = r.querySelector(".ie-abonus-eff").value;
      var o = { effect: eff, value: +r.querySelector("input[type=number]").value || 0 };
      if (eff === "resist") { var t = r.querySelector(".ie-abonus-type"); o.type = t ? t.value : "fire"; }
      return o; });
    if (draft.item_type === "boots") {
      draft.corrosao_livres = Math.max(0, +g("ie-corrlivre").value || 0);
      draft.corrosao_penalidade = Math.max(1, +g("ie-corrpen").value || 2);
      draft.materiais = { organic: g("ie-mat-organic").checked, metal: g("ie-mat-metal").checked };
    }
    var ab = g("ie-abil"); if (ab) draft.granted_ability = ab.value;
    draft.maldicao_id = g("ie-maldicao") ? g("ie-maldicao").value : "";
    draft.maldicao_prende = !!g("ie-maldicao-prende")?.checked && !!draft.maldicao_id;
    return draft;
  }

  function renderAccessoryPreview() {
    currentAccessoryDraftFromForm();
    var item = L.serializeAccessory(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPriceAccessory(item) + " 🪙";
    var parts = [];
    (item.bonuses || []).forEach(function (b) {
      parts.push((b.value >= 0 ? "+" : "") + b.value + " " + bonusLabel(b));
    });
    if (item.corrosion_materials) {
      var matsLabel = item.corrosion_materials.length ? item.corrosion_materials.join("+") : "nenhum";
      parts.push("🛡️ corrosão " + (item.corrosao_resistente || 0) + "+" + (item.corrosao_niveis_penalidade || 2) + " (" + matsLabel + ")");
    }
    if (!parts.length) parts.push("(sem bônus)");
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindAccessoryForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderAccessoryPreview; el.oninput = renderAccessoryPreview;
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-add-abonus").onclick = function () { addArmorBonusRow(null); renderAccessoryPreview(); };
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderAccessoryPreview();
    };
    root.querySelector("#ie-save").onclick = onSaveAccessory;
  }

  async function onSaveAccessory() {
    currentAccessoryDraftFromForm();
    var v = L.validateAccessoryDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeAccessory(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item, cidadesSelecionadas());
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  var POTION_LABELS = { heal:"Cura (+HP)", regeneration:"Regeneração (pool +1/rodada)", atk_bonus:"Elixir (+ataque no turno)",
    cure_poison:"Antídoto (cura veneno)", cure_petrification:"Óleo (cura petrificação)",
    cure_disease:"Elixir (cura doença)" };

  function renderPotionForm(f) {
    var isHeal = draft.effect === "heal";
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Efeito",
        campo("Tipo", '<select id="ie-effect">' + (L.POTION_EFFECTS || ["heal","regeneration","atk_bonus"]).map(function (e) {
          return '<option value="' + e + '"' + (e === draft.effect ? " selected" : "") + '>' + esc(POTION_LABELS[e] || e) + '</option>'; }).join("") + '</select>') +
        (draft.effect.indexOf("cure_") === 0
          ? campo("Imunidade (quantidade)", numInput("ie-imunq", draft.imun_qtd, 1, 10)) +
            campo("Imunidade (dado)", '<select id="ie-imunf">' + [4,6,8,10,12].map(function (x) {
              return '<option' + (x === draft.imun_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>') +
            '<span class="ie-hint">Cura o status e imuniza pelo número de rodadas rolado.</span>'
          : campo("Valor", numInput("ie-value", draft.value, 0, 999)) +
            (isHeal ? campo("Doses (garrafa)", numInput("ie-maxuses", draft.max_uses, 1, 20)) :
              '<span class="ie-hint">Doses só se aplicam a poções de Cura.</span>'))),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Mercador)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro) +
        dispCidades()),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar poção</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderPotionPreview;
    bindPotionForm();
    renderPotionPreview();
  }

  function currentPotionDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.effect = g("ie-effect").value;
    var vv = g("ie-value"); if (vv) draft.value = Math.max(0, +vv.value || 0);
    var iq = g("ie-imunq"); if (iq) draft.imun_qtd = Math.max(1, +iq.value || 1);
    var ifa = g("ie-imunf"); if (ifa) draft.imun_faces = +ifa.value || 4;
    var mu = g("ie-maxuses"); if (mu) draft.max_uses = Math.max(1, +mu.value || 1);
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    return draft;
  }

  function renderPotionPreview() {
    currentPotionDraftFromForm();
    var item = L.serializePotion(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPricePotion(item) + " 🪙";
    var parts = [POTION_LABELS[item.effect] || item.effect, "valor " + item.value];
    if (item.max_uses) parts.push(item.max_uses + " doses");
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindPotionForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderPotionPreview; el.oninput = renderPotionPreview;
    });
    // Trocar o efeito troca o form (o campo Doses só existe para Cura).
    root.querySelector("#ie-effect").onchange = function () { currentPotionDraftFromForm(); renderPotionForm(root.querySelector("#ie-form")); };
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderPotionPreview();
    };
    root.querySelector("#ie-save").onclick = onSavePotion;
  }

  async function onSavePotion() {
    currentPotionDraftFromForm();
    var v = L.validatePotionDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializePotion(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item, cidadesSelecionadas());
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  var THROW_ALVO_LABELS = { ataque_alvo:"Mirado (teste de ataque por Destreza)", area:"Área (save de Reflexos)" };
  var THROW_ELEM_LABELS = { fogo:"Fogo", frio:"Frio", eletrico:"Elétrico", acido:"Ácido", sagrado:"Sagrado", explosao:"Explosão" };

  function renderThrowableForm(f) {
    var isArea = draft.alvo === "area";
    var faces = [4,6,8,10,12];
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Mira",
        campo("Alvo", '<select id="ie-alvo">' + (L.THROW_TARGETS || ["ataque_alvo","area"]).map(function (a) {
          return '<option value="' + a + '"' + (a === draft.alvo ? " selected" : "") + '>' + esc(THROW_ALVO_LABELS[a] || a) + '</option>'; }).join("") + '</select>') +
        campo("Alcance (quadrados)", numInput("ie-alcance", draft.alcance, 1, 12)) +
        (isArea ? campo("Raio da área", numInput("ie-raio", draft.area_raio, 1, 3)) +
                  campo("CD do save (0 = sem save)", numInput("ie-savecd", draft.save_cd, 0, 25)) : "")),
      seccao("Dano",
        campo("Causa dano", chk("ie-temdano", draft.tem_dano)) +
        (draft.tem_dano ?
          campo("Quantidade", numInput("ie-dieq", draft.die_qtd, 1, 10)) +
          campo("Dado", '<select id="ie-dief">' + faces.map(function (x) {
            return '<option' + (x === draft.die_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>') +
          campo("Elemento", '<select id="ie-elemento">' + (L.THROW_ELEMENTS || ["fogo"]).map(function (e) {
            return '<option value="' + e + '"' + (e === draft.elemento ? " selected" : "") + '>' + esc(THROW_ELEM_LABELS[e] || e) + '</option>'; }).join("") + '</select>')
          : '<span class="ie-hint">Sem dano: use para itens de efeito puro.</span>')),
      seccao("Incêndio",
        campo("Coloca o alvo em chamas", chk("ie-chamas", draft.em_chamas)) +
        (draft.em_chamas ?
          campo("Duração (quantidade)", numInput("ie-chamasq", draft.chamas_qtd, 1, 5)) +
          campo("Duração (dado)", '<select id="ie-chamasf">' + faces.map(function (x) {
            return '<option' + (x === draft.chamas_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>') +
          campo("Água apaga", chk("ie-chamasagua", draft.chamas_agua_apaga))
          : '<span class="ie-hint">Marque para aplicar o status "em chamas" no acerto.</span>')),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Mercador)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro) +
        dispCidades()),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar arremessável</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderThrowablePreview;
    bindThrowableForm();
    renderThrowablePreview();
  }

  function currentThrowableDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.alvo = g("ie-alvo").value;
    draft.alcance = Math.max(1, Math.min(12, +g("ie-alcance").value || 4));
    var raio = g("ie-raio"); if (raio) draft.area_raio = Math.max(1, Math.min(3, +raio.value || 1));
    var scd = g("ie-savecd"); if (scd) draft.save_cd = Math.max(0, +scd.value || 0);
    draft.tem_dano = g("ie-temdano").checked;
    var dq = g("ie-dieq"); if (dq) draft.die_qtd = Math.max(1, +dq.value || 1);
    var df = g("ie-dief"); if (df) draft.die_faces = +df.value || 6;
    var el = g("ie-elemento"); if (el) draft.elemento = el.value;
    draft.em_chamas = g("ie-chamas").checked;
    var cq = g("ie-chamasq"); if (cq) draft.chamas_qtd = Math.max(1, +cq.value || 1);
    var cf = g("ie-chamasf"); if (cf) draft.chamas_faces = +cf.value || 4;
    var ca = g("ie-chamasagua"); if (ca) draft.chamas_agua_apaga = ca.checked;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    return draft;
  }

  function renderThrowablePreview() {
    currentThrowableDraftFromForm();
    var item = L.serializeThrowable(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPriceThrowable(item) + " 🪙";
    var parts = [item.alvo === "area" ? ("área raio " + item.area_raio) : "mirado",
                 "alcance " + item.alcance];
    if (item.dano) parts.push(item.dano + " " + (THROW_ELEM_LABELS[item.elemento] || item.elemento));
    if (item.save_cd) parts.push("Reflexos CD " + item.save_cd);
    if (item.em_chamas) parts.push("🔥 chamas " + item.chamas_dur + (item.chamas_agua_apaga ? "" : " (água não apaga)"));
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindThrowableForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderThrowablePreview; el.oninput = renderThrowablePreview;
    });
    // Alvo/dano/chamas mudam QUAIS campos existem — re-renderiza o form (padrão do ie-manejo).
    ["ie-alvo", "ie-temdano", "ie-chamas"].forEach(function (id) {
      var el = root.querySelector("#" + id);
      if (el) el.onchange = function () { currentThrowableDraftFromForm(); renderThrowableForm(root.querySelector("#ie-form")); };
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderThrowablePreview();
    };
    root.querySelector("#ie-save").onclick = onSaveThrowable;
  }

  async function onSaveThrowable() {
    currentThrowableDraftFromForm();
    var v = L.validateThrowableDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeThrowable(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item, cidadesSelecionadas());
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  var POISON_OP_LABELS = { dano:"Dano por rodada", reduzir:"Reduzir atributo",
    penalidade:"Penalidade (ataque/movimento/…)", petrificar:"Petrificar", cegar:"Cegar" };
  var POISON_ATTR_LABELS = { forca:"Força", constituicao:"Constituição",
    destreza:"Destreza", inteligencia:"Inteligência" };
  var POISON_PEN_LABELS = { ataque:"Ataque", movimento:"Movimento", dano:"Dano",
    ca:"CA", percepcao:"Percepção" };

  // Linhas dinâmicas de penalidade (chave + valor). `cls` separa as duas listas
  // (penalidade da operação × penalidade do save parcial) no mesmo formulário.
  function penRowsHTML(cls, lista) {
    var opts = (L.POISON_PENS || []).map(function (k) {
      return '<option value="' + k + '">' + esc(POISON_PEN_LABELS[k] || k) + '</option>'; }).join("");
    var linhas = (lista || []).map(function (o) {
      return '<span class="ie-elem-row ' + cls + '-row">' +
        '<select class="' + cls + '-k">' + opts + '</select> −' +
        '<input type="number" class="' + cls + '-v" value="' + (Math.abs(+o.valor) || 1) + '" min="1" max="20">' +
        ' <button class="' + cls + '-del">✕</button></span>'; }).join("");
    return '<div class="' + cls + '-box">' + linhas + '</div>' +
      '<button class="' + cls + '-add">+ penalidade</button>';
  }

  function renderPoisonForm(f) {
    var op = draft.operacao;
    var faces = [4,6,8,10,12];
    var dieSel = function (id, sel) {
      return '<select id="' + id + '">' + faces.map(function (x) {
        return '<option' + (x === sel ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>'; };
    var blocos = "";
    if (op === "dano") {
      blocos = seccao("Dano por rodada",
        campo("Valor fixo (em vez de dado)", chk("ie-danofixo", draft.dano_fixo)) +
        (draft.dano_fixo ? campo("Dano", numInput("ie-danoval", draft.dano_valor, 1, 99))
          : campo("Quantidade", numInput("ie-danoq", draft.dano_qtd, 1, 10)) +
            campo("Dado", dieSel("ie-danof", draft.dano_faces))) +
        campo("Modelo de resistência", '<select id="ie-modelosave">' +
          '<option value="aplicacao"' + (draft.modelo_save === "rodada" ? "" : " selected") + '>Testa 1× ao aplicar</option>' +
          '<option value="rodada"' + (draft.modelo_save === "rodada" ? " selected" : "") + '>Testa a cada rodada (neutraliza)</option></select>'));
    } else if (op === "reduzir") {
      blocos = seccao("Redução de atributo",
        campo("Atributo", '<select id="ie-patributo">' + (L.POISON_ATTRS || []).map(function (a) {
          return '<option value="' + a + '"' + (a === draft.atributo ? " selected" : "") + '>' + esc(POISON_ATTR_LABELS[a] || a) + '</option>'; }).join("") + '</select>') +
        campo("Quantidade", numInput("ie-valq", draft.val_qtd, 1, 10)) +
        campo("Dado", dieSel("ie-valf", draft.val_faces)) +
        '<span class="ie-hint">Constituição recalcula PV máximo e Fortitude automaticamente.</span>');
    } else if (op === "penalidade") {
      blocos = seccao("Penalidades", penRowsHTML("iepen", draft.atributos));
    } else {
      blocos = seccao("Sucesso parcial (save bem-sucedido)",
        campo("Duração (quantidade)", numInput("ie-durfq", draft.durfalha_qtd, 1, 10)) +
        campo("Duração (dado)", dieSel("ie-durff", draft.durfalha_faces)) +
        penRowsHTML("iepf", draft.penalidade_falha)) +
        (op === "cegar" ? seccao("Cegueira",
          campo("Penalidade de ataque (−)", numInput("ie-penatk", draft.penalidade_ataque, 1, 20)) +
          campo("Bloqueia ataques à distância", chk("ie-bloqdist", draft.bloqueia_distancia))) : "");
    }
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Ícone", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">') +
        campo("Descrição (tooltip)", '<input id="ie-desc" value="' + esc(draft.descricao) + '">')),
      seccao("Efeito",
        campo("Tipo", '<select id="ie-pop">' + (L.POISON_OPS || []).map(function (o) {
          return '<option value="' + o + '"' + (o === op ? " selected" : "") + '>' + esc(POISON_OP_LABELS[o] || o) + '</option>'; }).join("") + '</select>')),
      seccao("Resistência",
        campo("Save", '<select id="ie-psave">' + (L.POISON_SAVES || []).map(function (s) {
          return '<option value="' + s + '"' + (s === draft.save ? " selected" : "") + '>' + esc(s) + '</option>'; }).join("") + '</select>') +
        campo("CD", numInput("ie-pcd", draft.dificuldade, 1, 40)) +
        campo("Sucesso anula o efeito", chk("ie-panula", draft.anula))),
      seccao("Duração",
        campo("Quantidade", numInput("ie-durq", draft.dur_qtd, 1, 10)) +
        campo("Dado", dieSel("ie-durf", draft.dur_faces))),
      blocos,
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Mercador)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro) +
        dispCidades()),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar veneno</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    // Restaura os selects de chave das linhas de penalidade (o HTML não os marca).
    ["iepen", "iepf"].forEach(function (cls) {
      var fonte = cls === "iepen" ? draft.atributos : draft.penalidade_falha;
      root.querySelectorAll("." + cls + "-row").forEach(function (row, i) {
        var sel = row.querySelector("." + cls + "-k");
        if (sel && fonte && fonte[i]) sel.value = fonte[i].chave;
      });
    });
    previewFn = renderPoisonPreview;
    bindPoisonForm();
    renderPoisonPreview();
  }

  function lerPenRows(cls) {
    return Array.prototype.map.call(root.querySelectorAll("." + cls + "-row"), function (row) {
      return { chave: row.querySelector("." + cls + "-k").value,
               valor: Math.abs(+row.querySelector("." + cls + "-v").value || 1) };
    });
  }

  function currentPoisonDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.descricao = g("ie-desc").value;
    draft.operacao = g("ie-pop").value;
    draft.save = g("ie-psave").value;
    draft.dificuldade = Math.max(1, Math.min(40, +g("ie-pcd").value || 10));
    draft.anula = g("ie-panula").checked;
    draft.dur_qtd = Math.max(1, +g("ie-durq").value || 1);
    draft.dur_faces = +g("ie-durf").value || 4;
    var df = g("ie-danofixo"); if (df) draft.dano_fixo = df.checked;
    var dv = g("ie-danoval"); if (dv) draft.dano_valor = Math.max(1, +dv.value || 1);
    var dq = g("ie-danoq"); if (dq) draft.dano_qtd = Math.max(1, +dq.value || 1);
    var dfa = g("ie-danof"); if (dfa) draft.dano_faces = +dfa.value || 4;
    var ms = g("ie-modelosave"); if (ms) draft.modelo_save = ms.value;
    var at = g("ie-patributo"); if (at) draft.atributo = at.value;
    var vq = g("ie-valq"); if (vq) draft.val_qtd = Math.max(1, +vq.value || 1);
    var vf = g("ie-valf"); if (vf) draft.val_faces = +vf.value || 4;
    if (root.querySelector(".iepen-box")) draft.atributos = lerPenRows("iepen");
    if (root.querySelector(".iepf-box")) draft.penalidade_falha = lerPenRows("iepf");
    var dfq = g("ie-durfq"); if (dfq) draft.durfalha_qtd = Math.max(1, +dfq.value || 1);
    var dff = g("ie-durff"); if (dff) draft.durfalha_faces = +dff.value || 4;
    var pa = g("ie-penatk"); if (pa) draft.penalidade_ataque = Math.max(1, +pa.value || 4);
    var bd = g("ie-bloqdist"); if (bd) draft.bloqueia_distancia = bd.checked;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    return draft;
  }

  function renderPoisonPreview() {
    currentPoisonDraftFromForm();
    var item = L.serializePoison(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPricePoison(item) + " 🪙";
    var parts = [POISON_OP_LABELS[item.operacao] || item.operacao,
                 item.save + " CD " + item.dificuldade + (item.anula ? " (anula)" : " (parcial)"),
                 "dura " + item.duracao];
    if (item.dano) parts.push("dano " + item.dano);
    if (item.atributo) parts.push("−" + item.valor + " " + (POISON_ATTR_LABELS[item.atributo] || item.atributo));
    if (item.atributos && item.atributos.length)
      parts.push(item.atributos.map(function (p) { return p[1] + " " + p[0]; }).join(", "));
    if (item.penalidade_ataque) parts.push(item.penalidade_ataque + " ataque (cego)");
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindPoisonForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderPoisonPreview; el.oninput = renderPoisonPreview;
    });
    // Trocar a operação (ou o modo do dano) troca QUAIS campos existem.
    ["ie-pop", "ie-danofixo"].forEach(function (id) {
      var el = root.querySelector("#" + id);
      if (el) el.onchange = function () { currentPoisonDraftFromForm(); renderPoisonForm(root.querySelector("#ie-form")); };
    });
    // Linhas de penalidade: adicionar/remover re-renderiza o form.
    ["iepen", "iepf"].forEach(function (cls) {
      var add = root.querySelector("." + cls + "-add");
      if (add) add.onclick = function () {
        currentPoisonDraftFromForm();
        var alvo = cls === "iepen" ? "atributos" : "penalidade_falha";
        draft[alvo] = (draft[alvo] || []).concat([{ chave: "ataque", valor: 1 }]);
        renderPoisonForm(root.querySelector("#ie-form"));
      };
      root.querySelectorAll("." + cls + "-del").forEach(function (btn, i) {
        btn.onclick = function () {
          currentPoisonDraftFromForm();
          var alvo = cls === "iepen" ? "atributos" : "penalidade_falha";
          draft[alvo] = (draft[alvo] || []).filter(function (_, j) { return j !== i; });
          renderPoisonForm(root.querySelector("#ie-form"));
        };
      });
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderPoisonPreview();
    };
    root.querySelector("#ie-save").onclick = onSavePoison;
  }

  async function onSavePoison() {
    currentPoisonDraftFromForm();
    var v = L.validatePoisonDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializePoison(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item, cidadesSelecionadas());
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  function abonusTemplate() {
    return '<template id="ie-abonus-tpl"><span class="ie-elem-row">' +
      '<select class="ie-abonus-eff"><option value="def_">CA extra</option>' +
      '<option value="maxhp">PV máx</option><option value="spd">Velocidade</option>' +
      '<option value="atk_bonus">Bônus de acerto</option>' +
      '<option value="str_">Força</option><option value="dex">Destreza</option>' +
      '<option value="con_">Constituição</option><option value="int_">Inteligência</option>' +
      '<option value="initiative">Iniciativa</option>' +
      '<option value="vision">Visão (quadrados)</option>' +
      '<option value="resist">Resistência</option></select> ' +
      '<select class="ie-abonus-type" style="display:none"><option value="physical">Físico</option>' +
      '<option value="fire">Fogo</option><option value="cold">Frio</option><option value="lightning">Elétrico</option>' +
      '<option value="acid">Ácido</option><option value="holy">Sagrado</option><option value="poison">Veneno</option>' +
      '<option value="magic">Mágico</option><option value="water">Água</option></select> ' +
      numInput("", 0, -10, 20) + ' <button class="ie-abonus-del">✕</button></span></template>';
  }
  // ── Estoque por cidade ──────────────────────────────────────────────────────
  // Marcar "Loja" só coloca o item no catálogo global; quem vende é a allow-list
  // de cada cidade (city_shops.json). Sem escolher a cidade aqui, o item existe
  // mas não aparece em loja nenhuma no jogo. O servidor grava a escolha ao salvar.
  var cityCfg = null, cityLoading = null, citySel = null;
  function ensureCities() {
    if (cityCfg || cityLoading) return;
    if (!window.EDITOR_SAVE || !window.EDITOR_SAVE.loadCityShops) return;
    cityLoading = window.EDITOR_SAVE.loadCityShops().then(function (c) {
      cityCfg = c; cityLoading = null; patchCidades();
    }, function () { cityLoading = null; });
  }
  // Cidades que já estocam este id (quando se salva de novo um item existente).
  function cidadesDoItem(itemId) {
    if (!cityCfg || !itemId) return null;
    var shop = L.shopIdForItemType(draft.item_type || "weapon");
    var out = Object.keys(cityCfg.stock || {}).filter(function (cid) {
      return ((cityCfg.stock[cid] || {})[shop] || []).indexOf(itemId) >= 0;
    });
    return out.length ? out : null;
  }
  function cidadesHTML() {
    if (!cityCfg) return '<span class="ie-hint" id="ie-cidades">carregando cidades…</span>';
    var cidades = cityCfg.cities || [];
    if (!cidades.length) return '<span class="ie-hint" id="ie-cidades">nenhuma cidade cadastrada</span>';
    var sel = citySel || cidadesDoItem(L.slugify(draft.id || draft.name || "")) || [cidades[0].id];
    return '<div id="ie-cidades">' + cidades.map(function (c) {
      return '<label class="ie-cls"><input type="checkbox" class="ie-city" value="' + esc(c.id) + '"' +
        (sel.indexOf(c.id) >= 0 ? " checked" : "") + '> ' + esc(c.name || c.id) + '</label>';
    }).join("") + '<span class="ie-hint">A loja de cada cidade vende só o que estiver marcado aqui.</span></div>';
  }
  function dispCidades() { return '<span class="ie-hint">Cidades que vendem:</span>' + cidadesHTML(); }
  function patchCidades() {
    var el = root.querySelector("#ie-cidades");
    if (el) { el.outerHTML = cidadesHTML(); aplicarEstadoCidades(); }
  }
  function aplicarEstadoCidades() {
    var loja = root.querySelector("#ie-disp-loja");
    var on = !loja || loja.checked;
    root.querySelectorAll(".ie-city").forEach(function (el) { el.disabled = !on; });
  }
  // null = cidades ainda não carregadas → o servidor não mexe no estoque.
  function cidadesSelecionadas() {
    if (!cityCfg) return null;
    return Array.prototype.map.call(root.querySelectorAll(".ie-city:checked"),
      function (el) { return el.value; });
  }
  root.addEventListener("change", function (e) {
    var t = e.target;
    if (!t) return;
    if (t.id === "ie-disp-loja") aplicarEstadoCidades();
    else if (t.classList && t.classList.contains("ie-city")) citySel = cidadesSelecionadas();
  });

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
    draft.maldicao_id = g("ie-maldicao") ? g("ie-maldicao").value : "";
    draft.maldicao_prende = !!g("ie-maldicao-prende")?.checked && !!draft.maldicao_id;
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
      var saved = await window.EDITOR_SAVE.saveCustomItem(item, cidadesSelecionadas());
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  window.EDITOR_ITEMS_EDITOR = { render: render };
})();
