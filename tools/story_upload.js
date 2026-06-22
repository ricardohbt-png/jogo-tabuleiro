"use strict";
// Cliente de upload de mídia da história. Abre uma WebSocket sob demanda com o
// servidor (ws://localhost:8765 — o editor roda como file://) e envia o arquivo
// em base64. window.STORY_UPLOAD.upload(file) -> Promise<basename> | rejeita.
(function () {
  const IMG = [".jpg", ".jpeg", ".png", ".webp", ".gif"];
  const AUD = [".mp3", ".ogg", ".wav", ".m4a"];
  const OK_EXT = IMG.concat(AUD);
  const MAX = 25 * 1024 * 1024;   // limite por arquivo; abaixo do max_size do servidor (34MB) de propósito

  let ws = null;
  let connecting = null;       // Promise da conexão em andamento (evita corrida entre uploads)
  let nextId = 1;
  const pending = new Map();   // upload_id -> {resolve, reject}

  function serverUrl() { return "ws://localhost:8765"; }

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return Promise.resolve(ws);
    if (connecting) return connecting;
    connecting = new Promise((resolve, reject) => {
      const sock = new WebSocket(serverUrl());
      ws = sock;
      sock.onopen = () => { connecting = null; resolve(sock); };
      sock.onerror = () => {
        connecting = null;
        reject(new Error("não foi possível enviar — o servidor está rodando?"));
      };
      sock.onmessage = (ev) => {
        let m;
        try { m = JSON.parse(ev.data); } catch (e) { return; }
        if (m.type !== "upload_result") return;
        const p = pending.get(m.upload_id);
        if (!p) return;
        pending.delete(m.upload_id);
        if (m.ok) p.resolve(m.name);
        else p.reject(new Error(m.error || "falha no upload"));
      };
      sock.onclose = () => {
        connecting = null;
        for (const p of pending.values()) p.reject(new Error("conexão fechada"));
        pending.clear();
        if (ws === sock) ws = null;
      };
    });
    return connecting;
  }

  function extOf(name) {
    const i = name.lastIndexOf(".");
    return i < 0 ? "" : name.slice(i).toLowerCase();
  }

  function toBase64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => {
        const s = String(r.result);
        const c = s.indexOf(",");           // tira o prefixo "data:...;base64,"
        resolve(c < 0 ? s : s.slice(c + 1));
      };
      r.onerror = () => reject(new Error("falha ao ler arquivo"));
      r.readAsDataURL(file);
    });
  }

  async function upload(file) {
    if (OK_EXT.indexOf(extOf(file.name)) < 0)
      throw new Error("extensão não permitida");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const sock = await connect();
    const data = await toBase64(file);
    const id = nextId++;
    return new Promise((resolve, reject) => {
      const to = setTimeout(() => {
        if (pending.has(id)) { pending.delete(id); reject(new Error("tempo esgotado")); }
      }, 30000);
      pending.set(id, {
        resolve: (v) => { clearTimeout(to); resolve(v); },
        reject: (e) => { clearTimeout(to); reject(e); },
      });
      try {
        sock.send(JSON.stringify({ type: "upload_story", upload_id: id,
                                   name: file.name, data: data }));
      } catch (e) {
        clearTimeout(to); pending.delete(id);
        reject(new Error("falha ao enviar"));
      }
    });
  }

  window.STORY_UPLOAD = { upload: upload };
})();
