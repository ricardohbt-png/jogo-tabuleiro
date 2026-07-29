# Prévia 3D fiel do editor — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o renderer paralelo da prévia do editor por um iframe do cliente real do jogo, alimentado por um `game_state` montado pelo carregador real do servidor.

**Architecture:** O editor manda a masmorra atual (`buildJSON()`, sem gravar) pelo WebSocket; o servidor monta um `GameRoom` descartável com `load_authored_dungeon` e devolve o payload de `game_state`; o editor injeta esse payload num `<iframe src="../index.html?preview=1">`, que renderiza pelo `init3D` normal. Névoa desligada pelo mecanismo já existente do Modo Mestre (`master_pid == myPid`).

**Tech Stack:** Python 3 + `websockets` (servidor), JS vanilla + Three.js r128 (cliente e editor).

**Spec:** `docs/superpowers/specs/2026-07-28-previa-3d-fiel-editor-design.md`

---

### Task 1: Extrair `_game_state_payload()` da `push_state`

**Files:**
- Modify: `server.py:21693-21770` (`push_state`)
- Test: `tools/test_preview_editor.py` (criar)

- [ ] **Step 1: Escrever o teste de regressão**

Criar `tools/test_preview_editor.py`:

```python
"""Prévia 3D do editor. Roda da raiz: python tools/test_preview_editor.py"""
import asyncio, sys, os, json
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def dungeon_min():
    """Masmorra 6x5 válida: 1 sala, 1 monstro, 1 decoração sem image própria."""
    tiles = [[S.FLOOR]*6 for _ in range(5)]
    for x in range(6): tiles[0][x] = S.WALL; tiles[4][x] = S.WALL
    for y in range(5): tiles[y][0] = S.WALL; tiles[y][5] = S.WALL
    return {
        "schema_version": 1, "id": "prev", "name": "Prévia",
        "grid": {"w": 6, "h": 5}, "tiles": tiles,
        "entrance": {"x": 1, "y": 1},
        "rooms": [{"id": "r1", "x": 1, "y": 1, "w": 4, "h": 3,
                   "role": "entrance", "doors": []}],
        "monsters": [{"type": "goblin", "pos": [3, 2], "room_id": "r1"}],
        "decorations": [{"type": "barril", "pos": [2, 2], "facing": [0, 1]}],
        "chests": [], "traps": [], "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }

async def main():
    print("\n[1] _game_state_payload é equivalente ao dict que push_state envia")
    r = GameRoom("PREV")
    r.phase = "playing"
    r.load_authored_dungeon(dungeon_min())
    enviados = []
    async def cap(msg, *a, **k): enviados.append(msg)
    r.broadcast = cap
    await r.push_state()
    check("push_state enviou um game_state", len(enviados) == 1
          and enviados[0].get("type") == "game_state")
    check("payload direto é igual ao enviado", r._game_state_payload() == enviados[0])

    print(f"\n{'='*46}\n  {PASS} passaram, {FAIL} falharam\n{'='*46}")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_preview_editor.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_game_state_payload'`

- [ ] **Step 3: Dividir a `push_state`**

Em `server.py`, renomear o corpo atual de `push_state` (da linha do `players_state = [...]` até o fechamento do dict `msg_state`) para um método síncrono novo, e deixar a `push_state` só com o `await`:

```python
    def _game_state_payload(self):
        """Dict de `game_state` da sala. Puro: não faz await nem broadcast.
        Espelha o par _city_state_payload/broadcast_city_state. A prévia do
        editor consome este payload sem passar por nenhum jogador."""
        for p in self.players.values():
            for circulo in SLOT_REGEN:
                self._slot_prune(p, circulo)
        players_state = [ ... ]          # corpo atual, sem alteração
        ...
        return msg_state

    async def push_state(self):
        await self._check_objectives()
        msg_state = self._game_state_payload()
        # Quem está na cidade (fora_masmorra) não recebe game_state: o cliente
        # prefere gameState a cityState e mostraria o paperdoll da masmorra.
        await self.broadcast(msg_state, skip=self._pids_fora())
```

Atenção: o laço de `_slot_prune` move junto para `_game_state_payload`; o `await self._check_objectives()` **fica** na `push_state`.

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_preview_editor.py`
Expected: 2 passaram, 0 falharam

- [ ] **Step 5: Rodar as suítes que exercitam `push_state` para provar que nada regrediu**

Run: `python tools/test_modo_mestre.py` e `python tools/test_masmorra_sequenciada.py`
Expected: mesmos números de antes da mudança (0 falhas).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_preview_editor.py
git commit -m "refactor(server): extrai _game_state_payload da push_state"
```

---

### Task 2: Handler `preview_dungeon` no servidor

**Files:**
- Modify: `server.py` (função nova antes de `handler`; despacho junto de `upload_dungeon` em ~21886)
- Test: `tools/test_preview_editor.py`

- [ ] **Step 1: Escrever os testes**

Acrescentar a `main()` em `tools/test_preview_editor.py`:

```python
    print("\n[2] prévia monta o estado a partir da masmorra do editor")
    ok, st, avisos = S._preview_dungeon_state(dungeon_min())
    check("ok", ok is True)
    check("sem avisos", avisos == [])
    check("tipo game_state", st["type"] == "game_state")
    check("sem heróis", st["players"] == [])
    check("sem turno", st["current_turn"] is None)
    check("master_pid preenchido", st["master_pid"] == S.PREVIEW_PID)
    check("mapa todo explorado", len(st["explored"]) == 6 * 5)
    check("1 monstro", len(st["monsters"]) == 1 and st["monsters"][0]["type"] == "goblin")
    dec = st["decorations"][0]
    check("decoração com image do DECOR_TYPES",
          dec["image"] == S.DECOR_TYPES["barril"].get("image"))

    print("\n[3] masmorra incompleta gera aviso, não erro")
    d = dungeon_min(); d.pop("entrance")
    ok, st, avisos = S._preview_dungeon_state(d)
    check("ainda monta", ok is True)
    check("avisou", any("entrada" in a.lower() for a in avisos))
    check("entrada suprida", st["stairs_pos"] is not None)

    print("\n[3b] monstro de tipo desconhecido é descartado com aviso")
    d = dungeon_min(); d["monsters"] = [{"type": "nao_existe", "pos": [3, 2], "room_id": "r1"}]
    ok, st, avisos = S._preview_dungeon_state(d)
    check("ainda monta", ok is True)
    check("sem monstros", st["monsters"] == [])
    check("avisou do tipo", any("nao_existe" in a for a in avisos))

    print("\n[4] masmorra irrecuperável devolve erro")
    ok, res, avisos = S._preview_dungeon_state({"schema_version": 1})
    check("não ok", ok is False)
    check("erro é texto", isinstance(res, str) and res)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_preview_editor.py`
Expected: `AttributeError: module 'server' has no attribute '_preview_dungeon_state'`

- [ ] **Step 3: Implementar**

Em `server.py`, logo antes de `def process_request(`:

```python
PREVIEW_PID = "preview"   # pid falso da prévia do editor (nunca entra numa sala real)

def _preview_dungeon_state(defn):
    """Monta o game_state da prévia do editor a partir do dict cru da masmorra.

    Reusa o mesmo load_authored_dungeon do jogo, então objetos, monstros,
    materiais e imagens saem idênticos ao que o jogador verá. Tolerante: uma
    masmorra ainda em construção rende avisos, não recusa.
    Retorna (ok, payload_ou_mensagem_de_erro, avisos)."""
    if not isinstance(defn, dict):
        return False, "Masmorra não é um objeto JSON.", []
    defn = deepcopy(defn)
    avisos = []
    ok, msg = validar_dungeon(defn)
    if not ok:
        avisos.append(msg)

    grid = defn.get("grid") or {}
    if not (isinstance(grid.get("w"), int) and isinstance(grid.get("h"), int)):
        return False, "Grid ausente ou inválido — nada a mostrar.", avisos
    if not isinstance(defn.get("tiles"), list) or not defn["tiles"]:
        return False, "Tiles ausentes — nada a mostrar.", avisos

    # Entrada é obrigatória para load_authored_dungeon. Enquanto o autor desenha
    # ela costuma faltar: supre com a primeira casa de chão.
    ent = defn.get("entrance")
    if not (isinstance(ent, dict) and isinstance(ent.get("x"), int) and isinstance(ent.get("y"), int)):
        achou = None
        for y, linha in enumerate(defn["tiles"]):
            for x, t in enumerate(linha):
                if t != WALL:
                    achou = {"x": x, "y": y}; break
            if achou: break
        defn["entrance"] = achou or {"x": 0, "y": 0}
        avisos.append("Sem entrada definida — usei uma casa de chão só para a prévia.")

    # Sala é obrigatória (os monstros caem em self.rooms[0]).
    if not defn.get("rooms"):
        defn["rooms"] = [{"id": "_preview", "x": 0, "y": 0,
                          "w": grid["w"], "h": grid["h"], "role": "entrance", "doors": []}]
        avisos.append("Sem salas definidas — usei o tabuleiro inteiro como sala.")

    tipos = {d["type"] for d in MONSTER_DEFS}
    monstros = []
    for mo in (defn.get("monsters") or []):
        if mo.get("type") in tipos:
            monstros.append(mo)
        else:
            avisos.append(f"Monstro de tipo desconhecido ignorado: {mo.get('type')!r}")
    defn["monsters"] = monstros

    room = GameRoom("PREVIEW")
    room.phase = "playing"
    try:
        room.load_authored_dungeon(defn)
    except Exception as e:
        return False, f"Não foi possível montar a prévia: {e}", avisos

    # Mapa inteiro à vista: mesma visão sem névoa do Modo Mestre, sem caminho novo.
    room.master_pid = PREVIEW_PID
    room.explored = {(x, y) for y in range(room.map_h) for x in range(room.map_w)}
    return True, room._game_state_payload(), avisos
```

E no `handler`, junto do bloco de `upload_dungeon`:

```python
                if t == "preview_dungeon":
                    ok, res, avisos = _preview_dungeon_state(msg.get("defn"))
                    payload = {"type": "preview_state", "upload_id": msg.get("upload_id"),
                               "ok": ok, "avisos": avisos}
                    if ok: payload["state"] = res
                    else:  payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_preview_editor.py`
Expected: 16 passaram, 0 falharam

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_preview_editor.py
git commit -m "feat(server): monta o game_state da previa do editor"
```

---

### Task 3: Modo prévia no cliente do jogo

**Files:**
- Modify: `src/gameState.js` (`send`, exports)
- Modify: `game.js` (boot)
- Modify: `game.css` (esconder HUD)

- [ ] **Step 1: `src/gameState.js` — detectar o modo e neutralizar o envio**

No topo do módulo (junto das outras constantes):

```js
  // Prévia do editor: a página roda sem servidor, alimentada por postMessage.
  const PREVIEW = typeof location !== 'undefined' && /[?&]preview=1/.test(location.search);
```

Em `send`:

```js
  function send(obj) {
    if (PREVIEW) return false;           // prévia é só leitura: nada sai daqui
    if (!ws || ws.readyState !== 1) return false;
    ws.send(JSON.stringify(obj));
    return true;
  }
```

Função nova, ao lado de `isMaster`:

```js
  // Injeta um game_state vindo da prévia do editor pelo MESMO caminho de um
  // estado recebido do servidor — sem socket, sem duplicar normalização.
  function injectPreviewState(msg) {
    myPid = msg.master_pid;          // liga isMaster() → visão sem névoa
    myName = 'Prévia';
    _handleMessage(msg);
  }
```

(`_handleMessage` é o nome da função que contém o `switch (msg.type)`; usar o nome real encontrado no arquivo.)

Exportar `injectPreviewState` e `PREVIEW` (como `isPreview`) no objeto final.

- [ ] **Step 2: `game.js` — entrar direto na masmorra em 3D**

No fim do arquivo, depois do bloco de listeners:

```js
// ── Modo prévia do editor (index.html?preview=1) ────────────────────────────
// Sem login, sem lobby, sem socket: o editor injeta o game_state por
// postMessage e o renderer 3D normal desenha a masmorra.
if (GS.isPreview) {
  document.body.classList.add('preview-mode');
  mode3D = true;
  showScreen('screen-game');
  window.addEventListener('message', ev => {
    const d = ev.data;
    if (!d || d.type !== 'preview_state' || !d.state) return;
    GS.injectPreviewState(d.state);
  });
  window.parent?.postMessage({ type: 'preview_ready' }, '*');
}
```

- [ ] **Step 3: `game.css` — esconder o HUD na prévia**

```css
/* Prévia do editor: só o tabuleiro. */
body.preview-mode #side-panel,
body.preview-mode #gm-log,
body.preview-mode #dice-canvas,
body.preview-mode #turn-badge,
body.preview-mode #round-badge,
body.preview-mode #turn-timer-badge,
body.preview-mode #objectives-hud,
body.preview-mode #btn-libertar,
body.preview-mode #ficha-fab { display: none !important; }
body.preview-mode #map-panel { width: 100%; }
```

- [ ] **Step 4: Commit**

```bash
git add src/gameState.js game.js game.css
git commit -m "feat(cliente): modo previa sem lobby nem socket"
```

---

### Task 4: `previewDungeon` no cliente WebSocket do editor

**Files:**
- Modify: `tools/story_upload.js`

- [ ] **Step 1: Aceitar a resposta `preview_state`**

No `sock.onmessage`, trocar o filtro:

```js
        if (m.type !== "upload_result" && m.type !== "objetos_list" && m.type !== "preview_state") return;
        const p = pending.get(m.upload_id);
        if (!p) return;
        pending.delete(m.upload_id);
        if (m.type === "objetos_list") { p.resolve(m.objetos || []); return; }
        if (m.ok) p.resolve(m);
        else p.reject(new Error(m.error || "falha no upload"));
```

- [ ] **Step 2: Expor a função**

```js
  // Monta a prévia da masmorra atual SEM gravar nada. Resolve com
  // { state, avisos } — o game_state que o cliente do jogo renderiza.
  function previewDungeon(defn) {
    return request("preview_dungeon", { defn: defn })
      .then((m) => ({ state: m.state, avisos: m.avisos || [] }));
  }
```

Adicionar `previewDungeon: previewDungeon` ao objeto `window.EDITOR_SAVE`.

- [ ] **Step 3: Commit**

```bash
git add tools/story_upload.js
git commit -m "feat(editor): pede a previa da masmorra ao servidor"
```

---

### Task 5: Reescrever `tools/editor_preview_3d.js`

**Files:**
- Rewrite: `tools/editor_preview_3d.js`
- Modify: `tools/editor.css` (estilos do overlay, se necessário)

- [ ] **Step 1: Substituir o arquivo inteiro**

```js
/* Prévia da masmorra do editor.
 * Não desenha nada: hospeda o cliente REAL do jogo (index.html?preview=1) e
 * injeta nele o game_state que o servidor monta com o mesmo carregador de
 * masmorra usado em partida. Assim a prévia não pode divergir do jogo.
 */
(function () {
  "use strict";
  let active = null;

  function close() {
    if (!active) return;
    window.removeEventListener("message", active.onMessage);
    active.el.remove();
    active = null;
  }

  function setStatus(texto, erro) {
    if (!active) return;
    const bar = active.el.querySelector(".ed3d-status");
    bar.textContent = texto || "";
    bar.classList.toggle("erro", !!erro);
  }

  async function enviarEstado() {
    const editor = window.EDITOR;
    let defn;
    try { defn = editor.buildJSON(); }
    catch (e) { setStatus("Não consegui ler a masmorra atual: " + e.message, true); return; }
    setStatus("Montando a prévia…");
    try {
      const { state, avisos } = await window.EDITOR_SAVE.previewDungeon(defn);
      if (!active) return;
      active.frame.contentWindow.postMessage({ type: "preview_state", state }, "*");
      setStatus(avisos.length ? "⚠️ " + avisos.join(" · ") : "");
    } catch (e) {
      setStatus("Falha ao montar a prévia: " + e.message + " (o servidor está rodando?)", true);
    }
  }

  function open() {
    if (active) { close(); return; }
    const el = document.createElement("div");
    el.className = "ed3d-overlay";
    el.innerHTML =
      '<div class="ed3d-head"><b>◈ Prévia — masmorra atual</b>' +
      '<span class="ed3d-hint">Mesma aparência do jogo · esq: orbitar · roda: zoom · dir: mover</span>' +
      '<button type="button" id="ed3d-close">← Voltar ao editor</button></div>' +
      '<div class="ed3d-status"></div>' +
      '<div class="ed3d-view"><iframe class="ed3d-frame" src="../index.html?preview=1"></iframe></div>';
    document.body.appendChild(el);

    const frame = el.querySelector(".ed3d-frame");
    // O cliente avisa quando terminou de montar a tela; só então o estado vai.
    const onMessage = (ev) => {
      if (ev.data && ev.data.type === "preview_ready") enviarEstado();
    };
    window.addEventListener("message", onMessage);
    active = { el, frame, onMessage };
    setStatus("Carregando o jogo…");

    el.querySelector("#ed3d-close").onclick = close;
    el.tabIndex = -1;
    el.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    el.focus();
  }

  const button = document.getElementById("btn-preview-3d");
  if (button) button.onclick = open;
  window.EDITOR_3D_PREVIEW = { open, close };
})();
```

- [ ] **Step 2: Ajustar o CSS do overlay**

Em `tools/editor.css`, garantir que o iframe preencha a área e que a barra de status apareça:

```css
.ed3d-frame { width: 100%; height: 100%; border: 0; display: block; }
.ed3d-status { padding: 4px 10px; font-size: 12px; color: #f0d39a; background: #1a1209; min-height: 20px; }
.ed3d-status.erro { color: #ffb0a0; background: #3a1410; }
```

- [ ] **Step 3: Commit**

```bash
git add tools/editor_preview_3d.js tools/editor.css
git commit -m "feat(editor): previa passa a rodar o cliente real do jogo"
```

---

### Task 6: Verificação in-app

**Files:** nenhum (verificação)

- [ ] **Step 1: Subir o servidor e abrir o editor**

Run: `python server.py`, depois abrir `http://localhost:8765/tools/editor.html`.

- [ ] **Step 2: Carregar `dungeons/floresta.json` e abrir a prévia**

Esperado: chão de grama e objetos de parede aparecem com seus PNGs (não caixas), as árvores aparecem como no jogo, sem névoa de guerra e sem HUD.

- [ ] **Step 3: Carregar `dungeons/gustavo.json` e abrir a prévia**

Esperado: o `altar` aparece como o GLB do jogo (não caixa cinza) e os 7 monstros aparecem com o mesmo visual do jogo.

- [ ] **Step 4: Desenhar uma masmorra nova sem entrada e abrir a prévia**

Esperado: a cena aparece e a barra de status mostra o aviso da entrada suprida.

- [ ] **Step 5: Rodar a suíte inteira e commitar o que faltar**

Run: `python tools/test_preview_editor.py`, `python tools/test_modo_mestre.py`, `python tools/test_masmorra_sequenciada.py`
