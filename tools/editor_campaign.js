"use strict";
(function () {
  const DUN = window.EDITOR_DUNGEONS || [];

  // Editor de slides: mora em tools/editor_story.js (compartilhado com o mapa-múndi).
  // Os apelidos precisam vir ANTES de `C`, que chama emptyStory() na inicialização.
  const ES = window.EDITOR_STORY;
  const emptyStory        = ES.emptyStory;
  const storyFromSaved    = ES.storyFromSaved;
  const storyToSaved      = ES.storyToSaved;
  const storyCount        = ES.storyCount;
  const histButtonHTML    = ES.histButtonHTML;
  const openHistoryEditor = ES.openHistoryEditor;
  const previewStory      = ES.previewStory;

  const C = { id: "nova_campanha", name: "Nova Campanha",
              intro: emptyStory(), outro: emptyStory(), dungeons: [] };

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
    if (window.EDITOR_SAVE && window.EDITOR_SAVE.saveCampaign) {
      setCampSaveMsg("status-ok", "Salvando em campaigns/…");
      window.EDITOR_SAVE.saveCampaign(out).then((res) => {
        setCampSaveMsg("status-ok", "✓ salva em campaigns/" + res.file);
      }).catch((err) => {
        baixarCampanha(out);
        setCampSaveMsg("status-err", "⚠ servidor offline (" + err.message + ") — baixada em Downloads");
      });
    } else {
      baixarCampanha(out);
    }
  }

  function setCampSaveMsg(cls, msg) {
    const el = statusEl();
    if (el) { el.className = cls; el.textContent = msg; }
  }

  function baixarCampanha(out) {
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

  window.EDITOR_CAMPAIGN = { C, renderCampaign, dunByFile, validarCampanhaEditor, saveCampaign, loadCampaign, drawMiniMap,
                             previewStory };
})();
