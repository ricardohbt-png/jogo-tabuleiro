"use strict";
// Editor de história em slides — compartilhado pela aba Campanha e pelo editor
// de mapa-múndi. Extraído de editor_campaign.js sem mudança de comportamento.
// O upload de mídia continua sendo window.STORY_UPLOAD (tools/story_upload.js).
(function () {

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
             ${st._audioStatus ? `<span class="hist-up-status">${st._audioStatus}</span>` : ""}
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
      ov.querySelector(".hist-preview").onclick = () => previewStory(st);
      ov.querySelector(".hist-audio-pick").onclick = () => pickFile("audio/*", f => {
        if (st._audioUrl) URL.revokeObjectURL(st._audioUrl);
        st._audioUrl = URL.createObjectURL(f); st._audioFile = f.name;
        st.audio = "assets/story/" + f.name;
        st._audioStatus = "enviando…"; render();
        window.STORY_UPLOAD.upload(f)
          .then(() => { st._audioStatus = "✓ enviado"; render(); })
          .catch(err => { st._audioStatus = "✗ " + err.message; render(); });
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
           <div class="hist-imgname">${imgName || ""}</div>
           ${s._upStatus ? `<div class="hist-up-status">${s._upStatus}</div>` : ""}</div>
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
           <span class="op-up">▲</span><span class="op-down">▼</span><span class="op-dup" title="Duplicar como próximo slide">⧉</span><span class="op-del">✕</span>
         </div>`;
      card.querySelector(".hist-img-pick").onclick = () => pickFile("image/*", f => {
        if (s._url) URL.revokeObjectURL(s._url);
        s._url = URL.createObjectURL(f); s._imgFile = f.name;
        s.image = "assets/story/" + f.name;
        s._upStatus = "enviando…"; render();
        window.STORY_UPLOAD.upload(f)
          .then(() => { s._upStatus = "✓ enviado"; render(); })
          .catch(err => { s._upStatus = "✗ " + err.message; render(); });
      });
      card.querySelectorAll(".fit-opt").forEach(el => el.onclick = () => { s.fit = el.dataset.fit; render(); });
      card.querySelector(".hist-text").oninput = e => { s.text = e.target.value; };
      card.querySelector(".op-up").onclick = () => { if (i > 0) { st.slides.splice(i - 1, 0, st.slides.splice(i, 1)[0]); render(); } };
      card.querySelector(".op-down").onclick = () => { if (i < st.slides.length - 1) { st.slides.splice(i + 1, 0, st.slides.splice(i, 1)[0]); render(); } };
      card.querySelector(".op-dup").onclick = () => {
        // A cópia usa o mesmo arquivo de imagem, sem novo upload. Não copiamos
        // _url (Object URL temporária), pois ele pertence ao card original e
        // poderia ser revogado ao excluir um dos dois slides.
        st.slides.splice(i + 1, 0, {
          text: s.text || "", image: s.image || "", fit: s.fit === "contain" ? "contain" : "cover",
          _url: "", _imgFile: s._imgFile || ""
        });
        render();
      };
      card.querySelector(".op-del").onclick = () => { if (s._url) URL.revokeObjectURL(s._url); st.slides.splice(i, 1); render(); };
      return card;
    }
    render();
    document.body.appendChild(ov);
  }

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

  window.EDITOR_STORY = { emptyStory, storyFromSaved, storyToSaved, storyCount,
                          histButtonHTML, pickFile, openHistoryEditor, previewStory };
})();
