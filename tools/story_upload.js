"use strict";
// Cliente de upload do editor. Abre uma WebSocket sob demanda com o servidor
// (ws://localhost:8765 — o editor roda como file://) e troca mensagens:
//   • mídia da história  -> window.STORY_UPLOAD.upload(file) -> Promise<basename>
//   • masmorra (JSON)     -> window.EDITOR_SAVE.saveDungeon(defn) -> Promise<{file,entry}>
//   • campanha (JSON)     -> window.EDITOR_SAVE.saveCampaign(defn) -> Promise<{file}>
// Todas rejeitam se o servidor não estiver no ar (o chamador pode cair no
// fallback de download).
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

  // Endereço do CLIENTE DO JOGO (prévia 3D e teste como mestre) visto do editor.
  //
  // Com o editor aberto como arquivo local (file://), um caminho relativo faz o
  // jogo abrir também em file:// — e aí o GLTFLoader, que usa XHR, é bloqueado
  // pelo navegador em TODA requisição de arquivo local: os .glb falham com
  // status 0 ("conexão falhou") e cada criatura cai no peão genérico, cada
  // objeto na caixa procedural. Como a WebSocket é absoluta, o resto do editor
  // parece funcionar e o defeito fica parecendo bug de render. Apontando para o
  // servidor HTTP, a prévia e o teste carregam a arte igual ao jogo.
  function clienteURL(query) {
    const base = (location.protocol === "file:") ? "http://localhost:8765/" : "../";
    return base + "index.html" + (query || "");
  }
  function editorEmArquivoLocal() { return location.protocol === "file:"; }

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
        if (m.type !== "upload_result" && m.type !== "objetos_list" && m.type !== "preview_state" && m.type !== "test_dungeon_created") return;
        const p = pending.get(m.upload_id);
        if (!p) return;
        pending.delete(m.upload_id);
        if (m.type === "objetos_list") { p.resolve(m.objetos || []); return; }
        if (m.ok) p.resolve(m);                       // mensagem completa (name/file/entry)
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

  // Envia uma mensagem `{type, upload_id, ...fields}` e resolve com a resposta
  // `upload_result` correspondente (ou rejeita em erro/timeout/desconexão).
  async function request(type, fields) {
    const sock = await connect();
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
        sock.send(JSON.stringify(Object.assign({ type: type, upload_id: id }, fields)));
      } catch (e) {
        clearTimeout(to); pending.delete(id);
        reject(new Error("falha ao enviar"));
      }
    });
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
    const data = await toBase64(file);
    const m = await request("upload_story", { name: file.name, data: data });
    return m.name;
  }

  async function uploadPrisoner(file) {
    if (IMG.indexOf(extOf(file.name)) < 0)
      throw new Error("envie uma imagem (png/jpg/webp/gif)");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    const m = await request("upload_prisoner", { name: file.name, data: data });
    return m.name;
  }

  // Grava a masmorra em dungeons/. Resolve com { file, entry } (entry = item do
  // catálogo window.EDITOR_DUNGEONS, para injeção ao vivo na aba de campanha).
  function saveDungeon(defn) {
    return request("upload_dungeon", { defn: defn })
      .then((m) => ({ file: m.file, entry: m.entry }));
  }

  // Monta a prévia da masmorra atual SEM gravar nada em disco. Resolve com
  // { state, avisos } — `state` é o game_state que o cliente do jogo renderiza.
  function previewDungeon(defn) {
    return request("preview_dungeon", { defn: defn })
      .then((m) => ({ state: m.state, avisos: m.avisos || [] }));
  }

  // Grava a campanha em campaigns/. Resolve com { file }.
  function saveCampaign(defn) {
    return request("upload_campaign", { defn: defn })
      .then((m) => ({ file: m.file }));
  }
  function createTestDungeon(defn) {
    return request("create_test_dungeon", { defn: defn })
      .then((m) => ({ code: m.code, token: m.token }));
  }
  async function uploadSceneMedia(file, kind) {
    const imageKind = ["background", "character", "illustration"].includes(kind);
    if ((imageKind ? IMG : AUD).indexOf(extOf(file.name)) < 0)
      throw new Error(imageKind ? "envie uma imagem válida" : "envie um áudio válido");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const m = await request("upload_scene_media", { kind: kind, name: file.name, data: await toBase64(file) });
    return m.path;
  }
  function loadScenes() { return request("load_scenes", {}).then((m) => m.scenes); }
  function saveScenes(scenes) { return request("save_scenes", { scenes: scenes }).then((m) => m.scenes); }

  // Salva uma cópia personalizada sem tocar nas definições nativas do servidor.
  function saveCustomMonster(monster) {
    return request("upload_custom_monster", { monster: monster })
      .then((m) => m.monster);
  }

  async function uploadMonsterArt(file, kind) {
    if (extOf(file.name) !== ".png")
      throw new Error("envie um arquivo .png");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    const m = await request("upload_monster_art", { kind: kind, name: file.name, data: data });
    return m.key;
  }

  // cidades: ids das cidades cuja loja vende o item (o servidor grava no
  // city_shops.json). Omitir mantém o estoque atual intocado.
  function saveCustomItem(item, cidades) {
    const msg = { item: item };
    if (Array.isArray(cidades)) msg.cidades_loja = cidades;
    return request("upload_custom_item", msg).then((m) => m.item);
  }
  function loadCityShops() { return request("load_city_shops", {}).then((m) => m.config); }
  function saveCityShops(stock, scenes, cityPoints) { return request("save_city_shops", { stock: stock, scenes: scenes, city_points: cityPoints }).then((m) => m.config); }
  function loadWorldAdventures() { return request("load_world_adventures", {}).then((m) => m.config); }
  function saveWorldAdventures(locations, adventures) { return request("save_world_adventures", { locations: locations, adventures: adventures }).then((m) => m.config); }
  async function uploadItemArt(file, itemId) {
    if (extOf(file.name) !== ".png") throw new Error("envie um arquivo .png");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    const m = await request("upload_item_art", { name: itemId + ".png", data: data });
    return m.name;
  }
  async function uploadTavernArt(file) {
    if (IMG.indexOf(extOf(file.name)) < 0) throw new Error("envie uma imagem PNG, JPG, WebP ou GIF");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const m = await request("upload_tavern_art", { name: file.name, data: await toBase64(file) });
    return m.path;
  }

  async function uploadCityArt(file) {
    if (IMG.indexOf(extOf(file.name)) < 0) throw new Error("envie uma imagem PNG, JPG, WebP ou GIF");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const m = await request("upload_city_art", { name: file.name, data: await toBase64(file) });
    return m.path;
  }
  async function uploadRefugioArt(file) {
    if (IMG.indexOf(extOf(file.name)) < 0) throw new Error("envie uma imagem PNG, JPG, WebP ou GIF");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const m = await request("upload_refugio_art", { name: file.name, data: await toBase64(file) });
    return m.path;
  }

  // Envia o conjunto completo de cidades: criadas, edições nas originais,
  // exclusões e a tabela de custos de viagem. Resolve com a config atualizada.
  function saveWorldCities(cities, overrides, deleted, routes) {
    return request("save_world_cities", {
      cities: cities, overrides: overrides, deleted: deleted, routes: routes,
    }).then((m) => m.config);
  }

  async function uploadObjeto(file) {
    if (extOf(file.name) !== ".png")
      throw new Error("envie um arquivo .png");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    const m = await request("objeto_upload", { name: file.name, data: data });
    return m.name;
  }

  // Lista os PNGs de assets/objetos. Resolve com array de basenames (ou rejeita
  // se o servidor estiver fora — chamador cai no fallback de digitação).
  async function listObjetos() {
    const sock = await connect();
    const id = nextId++;
    return new Promise((resolve, reject) => {
      const to = setTimeout(() => { pending.delete(id); reject(new Error("tempo esgotado")); }, 15000);
      pending.set(id, {
        resolve: (v) => { clearTimeout(to); resolve(v); },
        reject: (e) => { clearTimeout(to); reject(e); },
      });
      try {
        sock.send(JSON.stringify({ type: "list_objetos", upload_id: id }));
      } catch (e) { clearTimeout(to); pending.delete(id); reject(new Error("falha ao enviar")); }
    });
  }

  window.STORY_UPLOAD = { upload: upload };
  window.PRISONER_UPLOAD = { upload: uploadPrisoner };
  window.EDITOR_SAVE = { saveDungeon: saveDungeon, previewDungeon: previewDungeon, createTestDungeon: createTestDungeon, saveCampaign: saveCampaign, loadScenes: loadScenes, saveScenes: saveScenes, uploadSceneMedia: uploadSceneMedia, saveCustomMonster: saveCustomMonster, saveCustomItem: saveCustomItem, uploadMonsterArt: uploadMonsterArt, uploadItemArt: uploadItemArt, uploadTavernArt: uploadTavernArt, uploadCityArt: uploadCityArt, uploadRefugioArt: uploadRefugioArt, loadCityShops: loadCityShops, saveCityShops: saveCityShops, saveWorldCities: saveWorldCities, loadWorldAdventures: loadWorldAdventures, saveWorldAdventures: saveWorldAdventures };
  window.EDITOR_CLIENTE = { url: clienteURL, emArquivoLocal: editorEmArquivoLocal };

  // Aviso fixo quando o editor foi aberto por duplo clique no arquivo. A prévia
  // e o teste já são redirecionados para o servidor, mas em file:// o navegador
  // bloqueia leitura de arquivo local em geral — é melhor o autor saber do que
  // descobrir por um sintoma torto mais adiante.
  if (editorEmArquivoLocal()) {
    const mostrar = () => {
      if (!document.body || document.getElementById("editor-aviso-file")) return;
      const a = document.createElement("div");
      a.id = "editor-aviso-file";
      a.style.cssText = "position:fixed;left:0;right:0;bottom:0;z-index:99999;padding:8px 14px;"
        + "background:#7a2020;color:#fff;font:600 12px/1.4 system-ui,sans-serif;text-align:center";
      a.innerHTML = 'Editor aberto como arquivo local (file://) — o navegador bloqueia a leitura '
        + 'de modelos 3D. Prefira abrir por '
        + '<a href="http://localhost:8765/tools/editor.html" style="color:#ffd166">'
        + 'http://localhost:8765/tools/editor.html</a> com o servidor no ar.';
      document.body.appendChild(a);
    };
    if (document.readyState === "loading")
      document.addEventListener("DOMContentLoaded", mostrar);
    else mostrar();
  }
  window.OBJETO_UPLOAD = { upload: uploadObjeto, list: listObjetos };
})();
