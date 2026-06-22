"use strict";
(function () {
  const DUN = window.EDITOR_DUNGEONS || [];
  const C = { id: "nova_campanha", name: "Nova Campanha",
              intro: emptyStory(), outro: emptyStory(), dungeons: [] };

  function emptyStory() { return { slides: [], audio: null, _audioUrl: null }; }

  // string | objeto | undefined -> {slides:[{text,image,fit}], audio, _audioUrl}
  function storyFromSaved(val) {
    if (!val) return emptyStory();
    if (typeof val === "string")
      return { slides: [{ text: val, image: "", fit: "cover" }], audio: null, _audioUrl: null };
    const slides = (val.slides || []).map(s => ({
      text: s.text || "", image: s.image || "",
      fit: s.fit === "contain" ? "contain" : "cover", _url: "" }));
    return { slides, audio: val.audio || null, _audioUrl: null };
  }
  // -> string (1 slide só-texto, sem áudio) | objeto | undefined (vazio)
  function storyToSaved(st) {
    const slides = (st.slides || []).filter(s => (s.text && s.text.trim()) || s.image);
    if (!slides.length) return undefined;
    if (slides.length === 1 && slides[0].text && slides[0].text.trim()
        && !slides[0].image && !st.audio)
      return slides[0].text;
    const out = { slides: slides.map(s => {
      const o = {};
      if (s.text && s.text.trim()) o.text = s.text;
      if (s.image) o.image = s.image;
      if (s.fit === "contain") o.fit = "contain";
      return o;
    }) };
    if (st.audio) out.audio = st.audio;
    return out;
  }
  function storyCount(st) { return (st.slides || []).filter(s => (s.text && s.text.trim()) || s.image).length; }

  function dunByFile(file) { return DUN.find(d => d.file === file) || null; }

  function faseObj(item) {
    if (typeof item === "string")
      return { file: item, intro: emptyStory(), outro: emptyStory() };
    if (item && item.intro && item.intro.slides)   // já normalizado em memória
      return item;
    return { file: item.file, intro: storyFromSaved(item.intro), outro: storyFromSaved(item.outro) };
  }

  function drawMiniMap(canvas, defn) {
    const ctx = canvas.getContext("2d");
    const W = (defn.grid && defn.grid.w) || 1, H = (defn.grid && defn.grid.h) || 1;
    const cw = canvas.width / W, ch = canvas.height / H;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const t = defn.tiles[y][x];
      ctx.fillStyle = t === 0 ? "#1d1812" : (t === 2 ? "#c8841f" : "#5a4a32");
      ctx.fillRect(x * cw, y * ch, Math.ceil(cw), Math.ceil(ch));
    }
    const dot = (p, col) => { if (p) { ctx.fillStyle = col; ctx.fillRect(p[0] * cw, p[1] * ch, Math.max(2, cw), Math.max(2, ch)); } };
    if (defn.entrance) dot([defn.entrance.x, defn.entrance.y], "#7ec86a");
    if (defn.exit) dot([defn.exit.x, defn.exit.y], "#6ab0ff");
    (defn.monsters || []).forEach(m => dot(m.pos, "#e06a6a"));
  }

  function statusEl() { return document.getElementById("status"); }

  function validarCampanhaEditor() {
    const e = [];
    if (!C.id.trim()) e.push("id vazio");
    if (!C.name.trim()) e.push("nome vazio");
    if (C.dungeons.length < 1) e.push("sem fases");
    for (const f of C.dungeons) if (!dunByFile(faseObj(f).file)) e.push("fase não encontrada: " + faseObj(f).file);
    return { ok: e.length === 0, erros: e };
  }
  function updateCampaignStatus() {
    const v = validarCampanhaEditor(), el = statusEl();
    if (!el) return v;
    if (v.ok) { el.className = "status-ok"; el.textContent = "✓ campanha válida — " + C.dungeons.length + " fase(s)"; }
    else { el.className = "status-err"; el.textContent = "✗ " + v.erros.join("; "); }
    return v;
  }

  function addPhase(file) { if (file) { C.dungeons.push(faseObj(file)); renderCampaign(); } }
  function removePhase(i) { C.dungeons.splice(i, 1); renderCampaign(); }
  function movePhase(i, dir) {
    const j = i + dir; if (j < 0 || j >= C.dungeons.length) return;
    const t = C.dungeons[i]; C.dungeons[i] = C.dungeons[j]; C.dungeons[j] = t; renderCampaign();
  }
  function openInEditor(file) {
    const d = dunByFile(file);
    if (d && window.EDITOR && window.EDITOR.loadJSON) { window.EDITOR.loadJSON(JSON.parse(JSON.stringify(d.defn))); window.setTab("masmorra"); }
  }

  // ── Botão de história + painel de slides ─────────────────────────────────
  function histButtonHTML(cls, st) {
    const n = storyCount(st);
    return `<button class="hist-btn ${cls}">📖 história${n ? " (" + n + ")" : ""}</button>`;
  }

  function pickFile(accept, cb) {
    const inp = document.createElement("input");
    inp.type = "file"; inp.accept = accept;
    inp.onchange = () => { const f = inp.files[0]; if (f) cb(f); };
    inp.click();
  }

  function openHistoryEditor(st, ctxLabel, onChange) {
    const ov = document.createElement("div"); ov.className = "hist-overlay";
    function close() { ov.remove(); onChange(); }
    function render() {
      const n = storyCount(st);
      const audioName = st._audioFile || (st.audio ? st.audio.split("/").pop() : "");
      ov.innerHTML =
        `<div class="hist-panel">
           <div class="hist-head">
             <span class="hist-title">📖 História — ${ctxLabel}</span>
             <span class="hist-spacer"></span>
             <span class="hist-count">${n} slide${n === 1 ? "" : "s"}</span>
             <button class="hist-preview">▶ pré-visualizar</button>
           </div>
           <div class="hist-audio">
             🎵 áudio (loop)
             <button class="hist-audio-pick">${audioName ? "trocar" : "escolher"}</button>
             ${audioName ? `<span class="hist-audio-name">${audioName}</span><span class="hist-audio-x">✕</span>` : ""}
             <span class="hist-audio-hint">toca em loop durante a história</span>
           </div>
           <div class="hist-slides"></div>
           <button class="hist-add">＋ adicionar slide</button>
           <div class="hist-foot">
             <span class="hist-note">imagens e áudios precisam estar na pasta <code>assets/story/</code></span>
             <button class="hist-close">fechar</button>
           </div>
         </div>`;
      const slidesHost = ov.querySelector(".hist-slides");
      st.slides.forEach((s, i) => slidesHost.appendChild(slideCard(s, i)));
      ov.querySelector(".hist-add").onclick = () => { st.slides.push({ text: "", image: "", fit: "cover", _url: "" }); render(); };
      ov.querySelector(".hist-close").onclick = close;
      ov.querySelector(".hist-preview").onclick = () => window.EDITOR_CAMPAIGN.previewStory(st);
      ov.querySelector(".hist-audio-pick").onclick = () => pickFile("audio/*", f => {
        if (st._audioUrl) URL.revokeObjectURL(st._audioUrl);
        st._audioUrl = URL.createObjectURL(f); st._audioFile = f.name;
        st.audio = "assets/story/" + f.name; render();
      });
      const ax = ov.querySelector(".hist-audio-x");
      if (ax) ax.onclick = () => {
        if (st._audioUrl) URL.revokeObjectURL(st._audioUrl);
        st._audioUrl = null; st._audioFile = ""; st.audio = null; render();
      };
    }
    function slideCard(s, i) {
      const card = document.createElement("div"); card.className = "hist-slide";
      const imgName = s._imgFile || (s.image ? s.image.split("/").pop() : "");
      card.innerHTML =
        `<div class="hist-thumb">${(s._url || s.image)
            ? `<img src="${s._url || s.image}" alt="">` : `<span class="hist-noimg">sem imagem</span>`}
           <div class="hist-imgname">${imgName || ""}</div></div>
         <div class="hist-fields">
           <div class="hist-row1">
             <button class="hist-img-pick">${imgName ? "trocar imagem" : "escolher imagem"}</button>
             <span class="hist-fit">
               <span class="fit-opt ${s.fit !== "contain" ? "on" : ""}" data-fit="cover">cobrir</span>
               <span class="fit-opt ${s.fit === "contain" ? "on" : ""}" data-fit="contain">inteira</span>
             </span>
           </div>
           <textarea class="hist-text" placeholder="texto do slide">${s.text || ""}</textarea>
         </div>
         <div class="hist-ops">
           <span class="op-up">▲</span><span class="op-down">▼</span><span class="op-del">✕</span>
         </div>`;
      card.querySelector(".hist-img-pick").onclick = () => pickFile("image/*", f => {
        if (s._url) URL.revokeObjectURL(s._url);
        s._url = URL.createObjectURL(f); s._imgFile = f.name;
        s.image = "assets/story/" + f.name; render();
      });
      card.querySelectorAll(".fit-opt").forEach(el => el.onclick = () => { s.fit = el.dataset.fit; render(); });
      card.querySelector(".hist-text").oninput = e => { s.text = e.target.value; };
      card.querySelector(".op-up").onclick = () => { if (i > 0) { st.slides.splice(i - 1, 0, st.slides.splice(i, 1)[0]); render(); } };
      card.querySelector(".op-down").onclick = () => { if (i < st.slides.length - 1) { st.slides.splice(i + 1, 0, st.slides.splice(i, 1)[0]); render(); } };
      card.querySelector(".op-del").onclick = () => { if (s._url) URL.revokeObjectURL(s._url); st.slides.splice(i, 1); render(); };
      return card;
    }
    render();
    document.body.appendChild(ov);
  }

  function renderControls() {
    const host = document.getElementById("campaign-controls");
    host.innerHTML =
      `<label>id <input id="c-id" size="12"></label>` +
      `<label>nome <input id="c-name" size="14"></label>` +
      histButtonHTML("c-intro-hist", C.intro).replace("história", "abertura") +
      histButtonHTML("c-outro-hist", C.outro).replace("história", "final") +
      `<button id="c-load">Carregar</button><input id="c-file" type="file" accept=".json,application/json" hidden>` +
      `<button id="c-save">Salvar</button>`;
    host.querySelector("#c-id").value = C.id;
    host.querySelector("#c-name").value = C.name;
    host.querySelector("#c-id").oninput = e => { C.id = e.target.value; updateCampaignStatus(); };
    host.querySelector("#c-name").oninput = e => { C.name = e.target.value; updateCampaignStatus(); };
    host.querySelector(".c-intro-hist").onclick = () => openHistoryEditor(C.intro, "abertura da campanha", renderControls);
    host.querySelector(".c-outro-hist").onclick = () => openHistoryEditor(C.outro, "final da campanha", renderControls);
    host.querySelector("#c-save").onclick = saveCampaign;
    host.querySelector("#c-load").onclick = () => host.querySelector("#c-file").click();
    host.querySelector("#c-file").onchange = ev => {
      const f = ev.target.files[0]; if (!f) return;
      const fr = new FileReader();
      fr.onload = () => { try { loadCampaign(JSON.parse(fr.result)); } catch (e) { alert("JSON inválido: " + e.message); } };
      fr.readAsText(f); ev.target.value = "";
    };
  }

  function renderAdd() {
    const host = document.getElementById("campaign-add");
    const opts = DUN.map(d => `<option value="${d.file}">${d.name} — ${d.file}</option>`).join("");
    host.innerHTML = `+ adicionar fase <select id="c-add-sel">${opts}</select> <button id="c-add-btn">adicionar</button>`;
    host.querySelector("#c-add-btn").onclick = () => addPhase(host.querySelector("#c-add-sel").value);
  }

  function renderList() {
    const host = document.getElementById("campaign-list");
    host.innerHTML = "";
    C.dungeons.forEach((item, i) => {
      const fo = faseObj(item); C.dungeons[i] = fo; const d = dunByFile(fo.file);
      const row = document.createElement("div"); row.className = "camp-row"; row.draggable = true; row.dataset.i = i;
      row.innerHTML =
        `<span class="camp-grip">⠿</span><span class="camp-i">${i + 1}</span>` +
        `<canvas class="camp-mini" width="56" height="42"></canvas>` +
        `<div class="camp-meta"><div class="camp-name">${d ? d.name : fo.file + " (não encontrada)"}</div>` +
        `<div class="camp-file">${fo.file}</div>` +
        `<div class="camp-hist-row">` +
          histButtonHTML("camp-intro-hist", fo.intro).replace("história", "abertura") +
          histButtonHTML("camp-outro-hist", fo.outro).replace("história", "final") +
        `</div></div>` +
        `<button class="camp-open" title="abrir no editor">✎</button>` +
        `<button class="camp-up">↑</button><button class="camp-down">↓</button><button class="camp-del">✕</button>`;
      host.appendChild(row);
      if (d) drawMiniMap(row.querySelector(".camp-mini"), d.defn);
      row.querySelector(".camp-intro-hist").onclick = () => openHistoryEditor(fo.intro, `abertura da fase ${i + 1}`, renderList);
      row.querySelector(".camp-outro-hist").onclick = () => openHistoryEditor(fo.outro, `final da fase ${i + 1}`, renderList);
      row.querySelector(".camp-open").onclick = () => openInEditor(fo.file);
      row.querySelector(".camp-up").onclick = () => movePhase(i, -1);
      row.querySelector(".camp-down").onclick = () => movePhase(i, 1);
      row.querySelector(".camp-del").onclick = () => removePhase(i);
      row.addEventListener("dragstart", ev => ev.dataTransfer.setData("text/plain", String(i)));
      row.addEventListener("dragover", ev => ev.preventDefault());
      row.addEventListener("drop", ev => {
        ev.preventDefault();
        const from = Number(ev.dataTransfer.getData("text/plain")), to2 = i;
        if (from === to2) return;
        const moved = C.dungeons.splice(from, 1)[0];
        C.dungeons.splice(to2, 0, moved); renderCampaign();
      });
    });
  }

  function renderCampaign() { renderControls(); renderAdd(); renderList(); updateCampaignStatus(); }

  function saveCampaign() {
    const v = updateCampaignStatus();
    if (!v.ok) { alert("Campanha inválida:\n- " + v.erros.join("\n- ")); return; }
    const out = { schema_version: 1, id: C.id.trim(), name: C.name.trim() };
    const ci = storyToSaved(C.intro); if (ci !== undefined) out.intro = ci;
    const co = storyToSaved(C.outro); if (co !== undefined) out.outro = co;
    out.dungeons = C.dungeons.map(f => {
      const o = faseObj(f), e = { file: o.file };
      const i = storyToSaved(o.intro); if (i !== undefined) e.intro = i;
      const u = storyToSaved(o.outro); if (u !== undefined) e.outro = u;
      return e;
    });
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = (C.id.trim() || "campanha") + ".json";
    document.body.appendChild(a); a.click(); a.remove();
  }

  function loadCampaign(obj) {
    C.id = obj.id || "campanha"; C.name = obj.name || "Campanha";
    C.intro = storyFromSaved(obj.intro); C.outro = storyFromSaved(obj.outro);
    C.dungeons = (obj.dungeons || []).map(faseObj);
    renderCampaign();
  }

  // Pré-visualização autossuficiente (o editor não carrega game.js): replica o
  // layout A usando blobs em memória quando disponíveis, senão o caminho salvo.
  function previewStory(st) {
    const slides = (st.slides || []).filter(s => (s.text && s.text.trim()) || s.image);
    if (!slides.length) { alert("Adicione ao menos um slide com texto ou imagem."); return; }
    let idx = 0, muted = false, audioEl = null;
    const ov = document.createElement("div"); ov.className = "spv-overlay";
    ov.innerHTML =
      `<div class="spv-img"></div><div class="spv-scrim"></div>
       <button class="spv-mute">🔊</button>
       <div class="spv-box"><div class="spv-text"></div>
         <div class="spv-nav"><button class="spv-prev">‹ Voltar</button>
           <div class="spv-dots"></div>
           <button class="spv-next">Continuar →</button></div></div>`;
    function stop() { if (audioEl) { try { audioEl.pause(); } catch (e) {} audioEl = null; } }
    function paint() {
      const s = slides[idx] || {};
      const img = ov.querySelector(".spv-img");
      const src = s._url || s.image;
      if (src) { img.style.backgroundImage = `url("${src}")`; img.style.backgroundSize = s.fit === "contain" ? "contain" : "cover"; }
      else { img.style.backgroundImage = "none"; }
      const t = ov.querySelector(".spv-text"); t.textContent = s.text || ""; t.style.display = s.text ? "block" : "none";
      const dots = ov.querySelector(".spv-dots"); dots.innerHTML = "";
      slides.forEach((_, i) => { const d = document.createElement("span"); d.className = "spv-dot" + (i === idx ? " on" : ""); dots.appendChild(d); });
      ov.querySelector(".spv-prev").style.visibility = idx > 0 ? "visible" : "hidden";
      ov.querySelector(".spv-next").textContent = idx < slides.length - 1 ? "Continuar →" : "Fechar";
      ov.querySelector(".spv-mute").textContent = muted ? "🔇" : "🔊";
    }
    ov.querySelector(".spv-prev").onclick = () => { if (idx > 0) { idx--; paint(); } };
    ov.querySelector(".spv-next").onclick = () => { if (idx < slides.length - 1) { idx++; paint(); } else { stop(); ov.remove(); } };
    ov.querySelector(".spv-mute").onclick = () => { muted = !muted; if (audioEl) audioEl.muted = muted; paint(); };
    const asrc = st._audioUrl || st.audio;
    if (asrc) { audioEl = new Audio(asrc); audioEl.loop = true; audioEl.volume = 0.6; audioEl.play().catch(() => {}); }
    document.body.appendChild(ov); paint();
  }

  window.EDITOR_CAMPAIGN = { C, renderCampaign, dunByFile, validarCampanhaEditor, saveCampaign, loadCampaign, drawMiniMap,
                             previewStory };
})();
