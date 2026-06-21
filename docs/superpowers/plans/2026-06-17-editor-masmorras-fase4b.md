# Editor de Masmorras — Fase 4b (Aba de Campanha + História) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aba de campanha no editor (montar/ordenar/validar/salvar com mini-mapa e abrir-no-editor) + sistema de história (textos de abertura/encerramento da campanha e por fase, exibidos em telas no jogo), com `campaign.json` retrocompatível.

**Architecture:** Sequenciado — primeiro o formato+runtime no `server.py`/cliente, depois a aba do editor. `campaign.json` aceita fases como string (4a) ou objeto `{file,intro,outro}`. O servidor expõe um "beat" de história em `game_state`/`city_state`/`game_over`; o cliente mostra um overlay que cada jogador fecha (não bloqueia). O editor ganha abas Masmorra|Campanha e um `editor_campaign.js`, alimentado por um índice de masmorras gerado (`editor_dungeons.js`).

**Tech Stack:** Python (`server.py`, autoritativo) + Vanilla JS (`src/gameState.js`, `game.js`, editor em `tools/`). Testes Python = scripts `tools/test_*.py` com `check()`; cliente verificado no navegador.

**Spec:** `docs/superpowers/specs/2026-06-17-editor-masmorras-fase4b-design.md`

---

## Notas de design (ler antes de começar)

- **Convenção de teste:** `tools/test_campanha.py` / `tools/test_export_catalog.py` (estilo `check()`, NÃO pytest; `sys.stdout.reconfigure(encoding="utf-8")` no topo). Rodar com `PYTHONIOENCODING=utf-8` no Windows.
- **Retrocompat:** fases em `campaign.json` podem ser string OU `{file,intro,outro}`. Helpers de módulo `_fase_file(item)` e `_fase_obj(item)` normalizam.
- **História não bloqueia:** o servidor só fornece o texto; o cliente exibe/fecha localmente (de-dup por `key`).
- **Anchors (linhas aprox. — localizar por texto):** `validar_campanha` (módulo); `enter_dungeon` `self.dungeon_def = carregar_dungeon(self.campaign["dungeons"][self.campaign_phase])` (~3548); `_check_objectives` advance branch (~12000-12009); `end_game(self, victory)` (~12065); `_campaign_payload` (~12105); `export_catalog.py` `__main__` (~37).
- **Scripts do editor sem ES modules** (file://): globais `window.EDITOR_DUNGEONS`, `window.EDITOR`, `window.EDITOR_CAMPAIGN`, `window.setTab`.
- **Commits:** cada task termina com `git add <arquivos exatos>` (nunca `git add -A`).

---

## Estrutura de arquivos

(ver tabela na §7 do spec) — `server.py`, `src/gameState.js`, `game.js`, `game.css`, `tools/export_catalog.py`, `tools/editor_dungeons.js` (gerado), `tools/editor.html`, `tools/editor.css`, `tools/editor_campaign.js`, `tools/editor.js`, `tools/test_campanha.py`, `tools/test_export_catalog.py`.

---

## Task 1: Schema retrocompatível (string | objeto)

**Files:** Modify `server.py`; Test `tools/test_campanha.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
async def test_schema_objeto():
    print("\n[7] schema retrocompat (string | objeto)")
    base = {"schema_version": 1, "id": "c", "name": "C"}
    # objeto com file válido + intro/outro
    d = dict(base, dungeons=[{"file": "test_camp_a.json", "intro": "oi", "outro": "tchau"}])
    ok, msg = server.validar_campanha(d); check(f"objeto válido passa ({msg})", ok is True)
    # string ainda válida (4a)
    d = dict(base, dungeons=["test_camp_a.json"])
    check("string (4a) ainda válida", server.validar_campanha(d)[0] is True)
    # objeto sem file recusa
    d = dict(base, dungeons=[{"intro": "x"}])
    check("objeto sem file recusa", server.validar_campanha(d)[0] is False)
    # intro não-string recusa
    d = dict(base, dungeons=[{"file": "test_camp_a.json", "intro": 5}])
    check("intro não-texto recusa", server.validar_campanha(d)[0] is False)
    # helpers
    check("_fase_file de string", server._fase_file("a.json") == "a.json")
    check("_fase_file de objeto", server._fase_file({"file": "b.json"}) == "b.json")
    check("_fase_obj normaliza string",
          server._fase_obj("a.json") == {"file": "a.json", "intro": "", "outro": ""})

async def test_entrada_objeto():
    print("\n[8] enter_dungeon com fase em objeto")
    r = setup_room(); r.phase = "lobby"
    # injeta uma campanha com fase em objeto direto
    r.mode = "campaign"; r.campaign = {"schema_version": 1, "id": "c", "name": "C",
        "dungeons": [{"file": "test_camp_a.json", "intro": "abre", "outro": "fecha"}]}
    r.campaign_phase = 0; r.phase = "city"
    await r.enter_dungeon("p1")
    check("carregou a fase do objeto (10×8)", r.map_w == 10 and r.map_h == 8)
```

E em `main()`: `await test_schema_objeto()` e `await test_entrada_objeto()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_campanha.py` → FAIL no `[7]` (`server._fase_file` inexistente).

- [ ] **Step 3: Implementar helpers + validação + enter**

Em `server.py`, logo ANTES de `def validar_campanha(defn):`, inserir:

```python
def _fase_file(item):
    """O nome do arquivo de uma fase de campanha (string ou objeto {file,...})."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("file")
    return None

def _fase_obj(item):
    """Normaliza uma fase para {file, intro, outro}."""
    if isinstance(item, str):
        return {"file": item, "intro": "", "outro": ""}
    if isinstance(item, dict):
        return {"file": item.get("file"), "intro": item.get("intro", ""), "outro": item.get("outro", "")}
    return {"file": None, "intro": "", "outro": ""}
```

SUBSTITUIR o corpo de validação (`dungeons`) em `validar_campanha` — trocar o laço `for i, file in enumerate(dungeons):` por:

```python
    for k in ("intro", "outro"):
        if k in defn and not isinstance(defn[k], str):
            return False, f"campanha: '{k}' deve ser texto."
    for i, item in enumerate(dungeons):
        file = _fase_file(item)
        if not isinstance(file, str) or not file:
            return False, f"fase {i+1}: precisa de um 'file' (string)."
        if isinstance(item, dict):
            for k in ("intro", "outro"):
                if k in item and not isinstance(item[k], str):
                    return False, f"fase {i+1}: '{k}' deve ser texto."
        d = carregar_dungeon(file)
        if d is None:
            return False, f"fase {i+1}: masmorra '{file}' não encontrada."
        ok, msg = validar_dungeon(d)
        if not ok:
            return False, f"fase {i+1} ('{file}'): {msg}"
    return True, "ok"
```

Em `enter_dungeon`, SUBSTITUIR a linha (~3548):

```python
            self.dungeon_def = carregar_dungeon(self.campaign["dungeons"][self.campaign_phase])
```
por:
```python
            self.dungeon_def = carregar_dungeon(_fase_file(self.campaign["dungeons"][self.campaign_phase]))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_campanha.py` → blocos `[7]`/`[8]` verdes, `0 falhou`.

- [ ] **Step 5: Regressão**

Run: `python tools/test_campanha.py` (todos), `python -c "import server"`. A campanha 4a (`test_campanha.json`, lista de strings) continua válida (coberto no `[1]`).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat: campaign.json aceita fase string|objeto {file,intro,outro} (Fase 4b)"
```

---

## Task 2: Runtime da história (server)

**Files:** Modify `server.py`; Test `tools/test_campanha.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
def _camp_hist():
    return {"schema_version": 1, "id": "ch", "name": "Hist",
            "intro": "ABERTURA-CAMP", "outro": "FINAL-CAMP",
            "dungeons": [
                {"file": "test_camp_a.json", "intro": "ABRE-1", "outro": "FECHA-1"},
                {"file": "test_camp_b.json", "intro": "ABRE-2", "outro": "FECHA-2"}]}

async def test_historia_runtime():
    print("\n[9] runtime da história")
    r = setup_room(); r.mode = "campaign"; r.campaign = _camp_hist(); r.campaign_phase = 0; r.phase = "city"
    await r.enter_dungeon("p1")
    pay = r._campaign_payload()
    check("abertura da fase 0 inclui abertura da campanha",
          pay["story"] and "ABERTURA-CAMP" in pay["story"]["text"] and "ABRE-1" in pay["story"]["text"])
    check("key de abertura", pay["story"]["key"] == "intro:0")
    # conclui a fase 0 → cidade com encerramento
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("foi para a cidade", r.phase == "city")
    payc = r._campaign_payload()
    check("encerramento da fase 0 na cidade",
          payc["story"] and payc["story"]["text"] == "FECHA-1" and payc["story"]["key"] == "outro:0")
    # entra na fase 1: outro é limpo; abertura da fase 1 (sem abertura da campanha)
    await r.enter_dungeon("p1")
    pay1 = r._campaign_payload()
    check("abertura da fase 1 (sem abertura da campanha)",
          pay1["story"] and pay1["story"]["text"] == "ABRE-2")
    # conclui a última → end_game com story final
    cap = {}
    async def fake_end(victory, story=None): cap["victory"] = victory; cap["story"] = story
    r.end_game = fake_end
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("última fase → end_game com story final",
          cap.get("victory") is True and cap.get("story")
          and "FECHA-2" in cap["story"]["text"] and "FINAL-CAMP" in cap["story"]["text"])
```

E em `main()`: `await test_historia_runtime()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_campanha.py` → FAIL no `[9]` (`_campaign_payload` não tem `story`; `end_game` não aceita `story`).

- [ ] **Step 3: `__init__` default + `_campaign_payload` com story**

Em `server.py`, no `GameRoom.__init__`, após `self.selected_campaign = None`, inserir:

```python
        self._campaign_outro = None   # beat de encerramento pendente (cidade), ou None
```

SUBSTITUIR `_campaign_payload` por:

```python
    def _campaign_payload(self):
        if not (self.mode == "campaign" and self.campaign):
            return None
        pay = {"name": self.campaign.get("name"),
               "phase": self.campaign_phase + 1,
               "total": len(self.campaign["dungeons"]),
               "story": None}
        if self.phase == "playing":
            fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
            texto = ""
            if self.campaign_phase == 0 and self.campaign.get("intro"):
                texto = self.campaign["intro"]
            if fase.get("intro"):
                texto += ("\n\n" if texto else "") + fase["intro"]
            if texto:
                pay["story"] = {"key": f"intro:{self.campaign_phase}", "text": texto}
        elif self.phase == "city" and self._campaign_outro:
            pay["story"] = self._campaign_outro
        return pay
```

- [ ] **Step 4: Encerramento no avanço + final no end_game**

Em `server.py`, no `_check_objectives`, SUBSTITUIR o bloco do avanço (~12000-12009) por:

```python
            if (self.mode == "campaign" and self.campaign
                    and self.campaign_phase < len(self.campaign["dungeons"]) - 1):
                # Encerramento da fase concluída (mostrado na cidade).
                fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                self._campaign_outro = ({"key": f"outro:{self.campaign_phase}", "text": fase["outro"]}
                                        if fase.get("outro") else None)
                self.campaign_phase += 1
                self.dungeon_generated = False
                self._objetivo_concluido = False
                await self.gm_say("🏆 Fase concluída! Retornem à cidade antes da próxima masmorra.")
                await self._voltar_para_cidade()
            else:
                story = None
                if self.mode == "campaign" and self.campaign:
                    fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                    partes = [p for p in (fase.get("outro"), self.campaign.get("outro")) if p]
                    if partes:
                        story = {"key": f"final:{self.campaign_phase}", "text": "\n\n".join(partes)}
                await self.end_game(victory=True, story=story)
```

SUBSTITUIR a assinatura/corpo de `end_game` por:

```python
    async def end_game(self, victory, story=None):
        self.phase = "ended"
        self._cancelar_timer_turno()
        if victory:
            self.dungeon_generated = False
        text = gm("victory") if victory else gm("defeat")
        await self.gm_say(text)
        await self.broadcast({"type": "game_over", "victory": victory, "story": story})
```

> Os outros `await self.end_game(victory=True)` / `end_game(victory=False)` existentes continuam válidos (`story` tem default `None`).

- [ ] **Step 5: Limpar `_campaign_outro` ao entrar na próxima fase**

Em `enter_dungeon`, junto da linha que carrega a fase da campanha (a que você ajustou na Task 1, dentro do `if self.mode == "campaign" and self.campaign and nova:`), adicionar logo após o carregamento:

```python
            self._campaign_outro = None   # a nova fase não mostra o encerramento da anterior
```

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_campanha.py` → bloco `[9]` verde, `0 falhou`.

- [ ] **Step 7: Regressão**

Run: `python tools/test_objetivos.py` → `0 falhou` (modo não-campanha: `end_game(victory=True)` sem story; `_campaign_payload` → None). `python tools/test_persistencia_masmorra.py` → `0 falhou`.

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat: runtime da historia da campanha (abertura/encerramento/final) (Fase 4b)"
```

---

## Task 3: Tela de história no cliente

**Files:** Modify `src/gameState.js`, `game.js`, `game.css`

> Verificado no navegador (Task 7). Servidor já envia `story` (Task 2).

- [ ] **Step 1: `gameState.js` — beat pendente + de-dup**

Localizar onde `gameState`/`cityState` são atribuídos e o handler de `game_over`:
`python -c "[print(i+1,l.rstrip()) for i,l in enumerate(open('src/gameState.js',encoding='utf-8')) if 'game_over' in l or 'gameState = msg' in l or 'cityState = msg' in l][:12]"`

Adicionar estado privado e funções (perto dos getters de campanha):

```javascript
  const _storyShown = new Set();
  let _lastStory = null;   // beat mais recente recebido (game_state/city_state/game_over)
  function _captarStory(msg) {
    const beat = (msg && msg.campaign && msg.campaign.story) || (msg && msg.story) || null;
    if (beat && beat.key) _lastStory = beat;
  }
  function pendingStory() {
    return (_lastStory && !_storyShown.has(_lastStory.key)) ? _lastStory : null;
  }
  function marcarStoryVista(key) { if (key) _storyShown.add(key); }
```

No handler de `game_state` e no de `city_state` (onde `gameState = msg` / `cityState = msg`), chamar `_captarStory(msg);`. No handler de `game_over`, chamar `_captarStory(msg);` também. Expor `pendingStory`/`marcarStoryVista` em `GS`.

- [ ] **Step 2: `game.js` — overlay + Continuar**

Localizar a render reativa (onde `handleGameState`/`handleCityState`/`game_over` atualizam a UI):
`python -c "[print(i+1,l.rstrip()) for i,l in enumerate(open('game.js',encoding='utf-8')) if 'handleGameState' in l or 'handleCityState' in l or 'game_over' in l or 'renderObjectivesHUD' in l][:15]"`

Adicionar um overlay no DOM (criar uma vez) e uma função `renderStory()` chamada após cada atualização de estado (game_state, city_state, game_over):

```javascript
function renderStory() {
  const beat = GS.pendingStory && GS.pendingStory();
  let ov = document.getElementById('story-overlay');
  if (!beat) { if (ov) ov.style.display = 'none'; return; }
  if (!ov) {
    ov = document.createElement('div'); ov.id = 'story-overlay';
    ov.innerHTML = '<div id="story-box"><div id="story-text"></div>'
      + '<button id="story-continue">Continuar</button></div>';
    document.body.appendChild(ov);
    ov.querySelector('#story-continue').onclick = () => {
      const b = GS.pendingStory && GS.pendingStory();
      if (b) GS.marcarStoryVista(b.key);
      ov.style.display = 'none';
    };
  }
  ov.querySelector('#story-text').textContent = beat.text;
  ov.style.display = 'flex';
}
```

Chamar `renderStory()` ao fim de `handleGameState`, `handleCityState` e do handler de `game_over` (a tela de história aparece sobre o tabuleiro/cidade; não bloqueia). Garantir que o botão usa a `key` do beat atual.

- [ ] **Step 3: `game.css` — estilo do overlay**

```css
#story-overlay { position: fixed; inset: 0; background: rgba(10,8,5,0.78);
  display: flex; align-items: center; justify-content: center; z-index: 9000; }
#story-box { max-width: 560px; margin: 16px; background: #1d1812; color: #e8dcc0;
  border: 1px solid #5a4830; border-radius: 10px; padding: 22px 24px;
  font-size: 16px; line-height: 1.6; white-space: pre-wrap; }
#story-continue { margin-top: 18px; display: block; background: #d9b061; color: #1d1812;
  border: none; border-radius: 6px; padding: 9px 18px; font-weight: bold; cursor: pointer; }
```

- [ ] **Step 4: Verificação rápida (servida)**

`python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8077/game.js').status)"` → 200 (subir `python -m http.server 8077` se preciso). Releitura: getters em `GS`, `renderStory` chamado nos 3 handlers, sem erro de sintaxe. (E2e completo na Task 7.)

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js game.js game.css
git commit -m "feat: tela de historia da campanha no cliente (overlay + continuar) (Fase 4b)"
```

---

## Task 4: Índice de masmorras gerado

**Files:** Modify `tools/export_catalog.py`; Gera `tools/editor_dungeons.js`; Test `tools/test_export_catalog.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_export_catalog.py` (e chamar em `main()`):

```python
def test_dungeons_index():
    print("\n[3] índice de masmorras")
    idx = ec.build_dungeons_index()
    check("inclui test_camp_a.json", any(d["file"] == "test_camp_a.json" for d in idx))
    check("itens têm file/id/name/defn",
          all(all(k in d for k in ("file", "id", "name", "defn")) for d in idx))
    check("defn é a masmorra (tem grid/tiles)",
          all("grid" in d["defn"] and "tiles" in d["defn"] for d in idx))
    # só válidas
    for d in idx:
        ok, _ = server.validar_dungeon(d["defn"]); 
        if not ok: check("masmorra do índice válida", False); break
    else:
        check("todas do índice são válidas", True)
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_dungeons.js")
    ec.write_dungeons_js(destino)
    with open(destino, encoding="utf-8") as f: txt = f.read()
    check("começa com window.EDITOR_DUNGEONS",
          txt.lstrip().startswith("window.EDITOR_DUNGEONS"))
    m = re.search(r"window\.EDITOR_DUNGEONS\s*=\s*(\[.*\]);", txt, re.S)
    check("payload é JSON válido", bool(m) and isinstance(json.loads(m.group(1)), list))
```

E em `main()`: `test_dungeons_index()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_export_catalog.py` → FAIL (`build_dungeons_index` inexistente).

- [ ] **Step 3: Implementar no `export_catalog.py`**

Inserir, após `write_catalog_js`:

```python
def build_dungeons_index():
    """Lista as masmorras válidas de dungeons/ com o defn completo embutido."""
    out = []
    for d in server.listar_dungeons():   # [{id,name,file}] já só de válidas
        defn = server.carregar_dungeon(d["file"])
        if defn is None:
            continue
        out.append({"file": d["file"], "id": d["id"], "name": d["name"], "defn": defn})
    return out

def write_dungeons_js(destino):
    payload = json.dumps(build_dungeons_index(), ensure_ascii=False, indent=2)
    txt = ("window.EDITOR_DUNGEONS = " + payload + ";\n"
           "// GERADO por tools/export_catalog.py — não editar à mão.\n")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(txt)
    return destino
```

E no `__main__`, após gerar o catálogo, gerar o índice:

```python
    idx_dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_dungeons.js")
    write_dungeons_js(idx_dest)
    print(f"editor_dungeons.js gerado em {idx_dest}")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_export_catalog.py` → bloco `[3]` verde, `0 falhou`. Confirmar `tools/editor_dungeons.js` criado.

- [ ] **Step 5: Commit**

```bash
git add tools/export_catalog.py tools/test_export_catalog.py tools/editor_dungeons.js
git commit -m "feat: gerador do indice de masmorras (editor_dungeons.js) (Fase 4b)"
```

---

## Task 5: Abas Masmorra | Campanha no editor

**Files:** Modify `tools/editor.html`, `tools/editor.css`, `tools/editor.js`

- [ ] **Step 1: `editor.html` — abas + blocos + includes**

Reestruturar o `<body>`: agrupar os controles de masmorra atuais num `#dungeon-controls`, adicionar a barra de abas, e os blocos de campanha. Substituir o conteúdo do `<body>` (mantendo os ids existentes do editor de masmorra) por:

```html
  <header id="topbar">
    <span class="brand">🗺️ Editor</span>
    <span id="tabs">
      <button id="tab-masmorra" class="tab active">Masmorra</button>
      <button id="tab-campanha" class="tab">Campanha</button>
    </span>
    <span id="dungeon-controls">
      <label>id <input id="m-id" value="nova_masmorra" size="12"></label>
      <label>nome <input id="m-name" value="Nova Masmorra" size="14"></label>
      <label>grid
        <input id="g-w" type="number" min="1" max="60" value="16" style="width:46px">×
        <input id="g-h" type="number" min="1" max="60" value="12" style="width:46px">
      </label>
      <button id="btn-resize">Aplicar grid</button>
      <button id="btn-load">Carregar</button>
      <input id="file-input" type="file" accept="application/json,.json" hidden>
      <button id="btn-save">Salvar</button>
    </span>
    <span id="campaign-controls" style="display:none"></span>
  </header>

  <div id="toolbar"></div>
  <main id="workspace">
    <div id="canvas-wrap"><canvas id="board" width="448" height="336"></canvas></div>
    <aside id="panel"><em>Selecione uma ferramenta e desenhe.</em></aside>
  </main>

  <div id="campaign-view" style="display:none">
    <div id="campaign-add"></div>
    <div id="campaign-list"></div>
  </div>

  <footer id="statusbar"><span id="status"></span></footer>

  <script src="editor_catalog.js"></script>
  <script src="editor_dungeons.js"></script>
  <script src="editor.js"></script>
  <script src="editor_campaign.js"></script>
```

- [ ] **Step 2: `editor.js` — `setTab` (mínimo)**

No fim do IIFE de `editor.js` (antes de fechar), adicionar e expor `setTab`:

```javascript
  function setTab(tab) {
    const dung = tab !== "campanha";
    document.getElementById("dungeon-controls").style.display = dung ? "" : "none";
    document.getElementById("toolbar").style.display = dung ? "" : "none";
    document.getElementById("workspace").style.display = dung ? "" : "none";
    document.getElementById("campaign-controls").style.display = dung ? "none" : "";
    document.getElementById("campaign-view").style.display = dung ? "none" : "";
    document.getElementById("tab-masmorra").classList.toggle("active", dung);
    document.getElementById("tab-campanha").classList.toggle("active", !dung);
    if (dung) { render(); renderPanel(); }
    else if (window.EDITOR_CAMPAIGN) window.EDITOR_CAMPAIGN.renderCampaign();
  }
  window.setTab = setTab;
  document.getElementById("tab-masmorra").onclick = () => setTab("masmorra");
  document.getElementById("tab-campanha").onclick = () => setTab("campanha");
```

> Inclua `setTab` também no objeto `window.EDITOR = {...}` se preferir; o acesso por `window.setTab` basta.

- [ ] **Step 3: `editor.css` — abas**

```css
#tabs { display:inline-flex; gap:4px; margin-right:10px; }
.tab { background:#33291c; color:#b9a87f; border:1px solid #5a4830; border-radius:5px; padding:5px 12px; cursor:pointer; }
.tab.active { background:#d9b061; color:#1d1812; border-color:#d9b061; }
#campaign-view { padding:12px; }
```

- [ ] **Step 4: Verificar no navegador**

Subir `python -m http.server 8077`; abrir `http://localhost:8077/tools/editor.html`. Clicar "Campanha" → some o grid/toolbar/controles de masmorra, aparece `#campaign-view` (vazio por ora). Clicar "Masmorra" → volta o editor. Console sem erros (`editor_campaign.js` ainda não tem lógica — um 404 não deve ocorrer pois o arquivo será criado na Task 6; se ainda não existe, crie-o vazio agora para evitar 404, ou faça a Task 6 antes de verificar). `window.EDITOR_DUNGEONS` definido.

- [ ] **Step 5: Commit**

```bash
git add tools/editor.html tools/editor.css tools/editor.js
git commit -m "feat: abas Masmorra|Campanha no editor (Fase 4b)"
```

---

## Task 6: Lógica da aba de campanha (com história)

**Files:** Create `tools/editor_campaign.js`

- [ ] **Step 1: Criar `tools/editor_campaign.js`**

```javascript
"use strict";
(function () {
  const DUN = window.EDITOR_DUNGEONS || [];
  const C = { id: "nova_campanha", name: "Nova Campanha", intro: "", outro: "", dungeons: [] };

  function dunByFile(file) { return DUN.find(d => d.file === file) || null; }

  function faseObj(item) {
    if (typeof item === "string") return { file: item, intro: "", outro: "" };
    return { file: item.file, intro: item.intro || "", outro: item.outro || "" };
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

  function addPhase(file) { if (file) { C.dungeons.push({ file, intro: "", outro: "" }); renderCampaign(); } }
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
      `<label>abertura <textarea id="c-intro" rows="1" style="vertical-align:middle"></textarea></label>` +
      `<label>final <textarea id="c-outro" rows="1" style="vertical-align:middle"></textarea></label>` +
      `<button id="c-load">Carregar</button><input id="c-file" type="file" accept=".json,application/json" hidden>` +
      `<button id="c-save">Salvar</button>`;
    host.querySelector("#c-id").value = C.id;
    host.querySelector("#c-name").value = C.name;
    host.querySelector("#c-intro").value = C.intro;
    host.querySelector("#c-outro").value = C.outro;
    host.querySelector("#c-id").oninput = e => { C.id = e.target.value; updateCampaignStatus(); };
    host.querySelector("#c-name").oninput = e => { C.name = e.target.value; updateCampaignStatus(); };
    host.querySelector("#c-intro").oninput = e => { C.intro = e.target.value; };
    host.querySelector("#c-outro").oninput = e => { C.outro = e.target.value; };
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
      const fo = faseObj(item); const d = dunByFile(fo.file);
      const row = document.createElement("div"); row.className = "camp-row"; row.draggable = true; row.dataset.i = i;
      row.innerHTML =
        `<span class="camp-grip">⠿</span><span class="camp-i">${i + 1}</span>` +
        `<canvas class="camp-mini" width="56" height="42"></canvas>` +
        `<div class="camp-meta"><div class="camp-name">${d ? d.name : fo.file + " (não encontrada)"}</div>` +
        `<div class="camp-file">${fo.file}</div>` +
        `<textarea class="camp-intro" rows="1" placeholder="abertura da fase"></textarea>` +
        `<textarea class="camp-outro" rows="1" placeholder="encerramento da fase"></textarea></div>` +
        `<button class="camp-open" title="abrir no editor">✎</button>` +
        `<button class="camp-up">↑</button><button class="camp-down">↓</button><button class="camp-del">✕</button>`;
      host.appendChild(row);
      if (d) drawMiniMap(row.querySelector(".camp-mini"), d.defn);
      const ti = row.querySelector(".camp-intro"), to = row.querySelector(".camp-outro");
      ti.value = fo.intro; to.value = fo.outro;
      ti.oninput = e => { C.dungeons[i] = { ...faseObj(C.dungeons[i]), intro: e.target.value }; };
      to.oninput = e => { C.dungeons[i] = { ...faseObj(C.dungeons[i]), outro: e.target.value }; };
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
    if (C.intro.trim()) out.intro = C.intro;
    if (C.outro.trim()) out.outro = C.outro;
    out.dungeons = C.dungeons.map(f => {
      const o = faseObj(f), e = { file: o.file };
      if (o.intro) e.intro = o.intro; if (o.outro) e.outro = o.outro; return e;
    });
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = (C.id.trim() || "campanha") + ".json";
    document.body.appendChild(a); a.click(); a.remove();
  }

  function loadCampaign(obj) {
    C.id = obj.id || "campanha"; C.name = obj.name || "Campanha";
    C.intro = obj.intro || ""; C.outro = obj.outro || "";
    C.dungeons = (obj.dungeons || []).map(faseObj);
    renderCampaign();
  }

  window.EDITOR_CAMPAIGN = { C, renderCampaign, dunByFile, validarCampanhaEditor, saveCampaign, loadCampaign, drawMiniMap };
})();
```

- [ ] **Step 2: `editor.css` — lista de campanha**

```css
#campaign-controls textarea { width:160px; height:26px; resize:vertical; background:#33291c; color:#e8dcc0; border:1px solid #4a3c28; border-radius:4px; }
#campaign-add { margin-bottom:10px; }
.camp-row { display:flex; align-items:flex-start; gap:8px; background:#1d1812; border:1px solid #4a3c28; border-radius:6px; padding:8px; margin-bottom:8px; }
.camp-grip { cursor:grab; color:#8a7a5a; } .camp-i { color:#8a7a5a; width:16px; }
.camp-mini { border:1px solid #4a3c28; border-radius:3px; }
.camp-meta { flex:1; display:flex; flex-direction:column; gap:3px; }
.camp-name { font-weight:bold; color:#d9b061; } .camp-file { font-size:11px; color:#8a7a5a; }
.camp-meta textarea { width:100%; height:26px; resize:vertical; background:#33291c; color:#e8dcc0; border:1px solid #4a3c28; border-radius:4px; }
.camp-row button { background:#33291c; color:#e8dcc0; border:1px solid #5a4830; border-radius:4px; cursor:pointer; }
```

- [ ] **Step 3: Verificar no navegador**

Recarregar `http://localhost:8077/tools/editor.html`, aba Campanha: o dropdown lista as masmorras (de `EDITOR_DUNGEONS`); adicionar 2 fases → aparecem com mini-mapa; escrever id/nome + aberturas/encerramentos (campanha e fases); reordenar por ↑/↓ e arrastando; status verde; "abrir no editor" (✎) carrega a masmorra na aba Masmorra. Console sem erros. No console: `EDITOR_CAMPAIGN.validarCampanhaEditor()`.

- [ ] **Step 4: Commit**

```bash
git add tools/editor_campaign.js tools/editor.css
git commit -m "feat: aba de campanha do editor (lista/minimapa/reordenar/historia/IO) (Fase 4b)"
```

---

## Task 7: Verificação ponta-a-ponta + round-trip

**Files:** Modify `tools/test_campanha.py` (round-trip); verificação no navegador.

- [ ] **Step 1: Round-trip do formato do editor (Python)**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
async def test_roundtrip_editor_campanha():
    print("\n[10] round-trip: campaign do editor passa em validar_campanha")
    # formato que o editor salva (objetos com história)
    obj = {"schema_version": 1, "id": "rt", "name": "RT", "intro": "abre", "outro": "fim",
           "dungeons": [{"file": "test_camp_a.json", "intro": "i1", "outro": "o1"},
                        {"file": "test_camp_b.json"}]}
    ok, msg = server.validar_campanha(obj)
    check(f"campanha do editor é válida ({msg})", ok is True)
```

E em `main()`: `await test_roundtrip_editor_campanha()`. Rodar: `python tools/test_campanha.py` → `0 falhou`.

- [ ] **Step 2: Commit do teste**

```bash
git add tools/test_campanha.py
git commit -m "test: round-trip do campaign.json do editor (Fase 4b)"
```

- [ ] **Step 3: E2e no navegador (editor + jogo)**

1. `python tools/export_catalog.py` (gera catálogo + índice de masmorras).
2. Servir: `python -m http.server 8077` (editor) e `python server.py` (jogo, 8765).
3. **Editor:** `http://localhost:8077/tools/editor.html` → aba Campanha → adicionar `test_camp_a.json` e `test_camp_b.json`, escrever abertura/final da campanha e abertura/encerramento de cada fase, validar (verde), **Salvar** → mover o `<id>.json` para `campaigns/`.
4. **Jogo:** `http://localhost:8765/index.html` → criar sala → selecionar a campanha → entrar: confirmar a **tela de história de abertura** (campanha + fase 1), fechável com "Continuar", sem travar; concluir a fase → **tela de encerramento** na cidade; entrar na fase 2; concluir → **tela final** (encerramento fase 2 + final da campanha) no game over. Console sem erros (editor e jogo). Screenshots.

- [ ] **Step 4: Regressão**

`python tools/test_campanha.py`, `tools/test_objetivos.py`, `tools/test_dungeon_loader.py`, `tools/test_export_catalog.py`, `tools/test_persistencia_masmorra.py` → todos `0 falhou`. Procedural/masmorra única/campanha sem história intactos.

- [ ] **Step 5: Parar os servidores e relatar evidências.**

---

## Self-Review (cobertura do spec)

- **Schema retrocompat (string|objeto) + campos de campanha** → Task 1 (`_fase_file`/`_fase_obj`/`validar_campanha`/`enter_dungeon`).
- **Runtime da história (abertura/encerramento/final, não bloqueante)** → Task 2 (`_campaign_payload` story, `_campaign_outro`, `end_game(story=)`) + Task 3 (overlay cliente, de-dup).
- **Índice gerado com defn** → Task 4 (`build_dungeons_index`/`write_dungeons_js`).
- **Abas Masmorra|Campanha** → Task 5. **Aba de campanha (lista/minimapa/abrir/reordenar/validar/IO + autoria da história)** → Task 6.
- **Testes (schema, runtime, índice, round-trip) + e2e** → Tasks 1,2,4,7.
- **Retrocompat 4a / não bloquear / procedural** → guardas + regressão (Tasks 2,7).

**Sem placeholders:** servidor e `editor_campaign.js` com código completo; HTML/CSS concretos; pontos de inserção em `game.js`/`gameState.js`/`editor.js` com greps de localização.

**Consistência de nomes:** `_fase_file`/`_fase_obj`, `_campaign_outro`, `_campaign_payload.story` `{key,text}`, `end_game(victory, story=None)`, `game_over.story`; cliente `pendingStory`/`marcarStoryVista`/`_storyShown`/`renderStory`; editor `EDITOR_DUNGEONS`, `EDITOR_CAMPAIGN`, `setTab`, `renderCampaign`/`saveCampaign`/`loadCampaign`/`drawMiniMap`/`openInEditor`.
