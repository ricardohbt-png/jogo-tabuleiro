# História em slides nas aventuras — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cada etapa de uma aventura do mapa-múndi ganha abertura e encerramento em slides (imagem + texto + áudio) editáveis no editor, os três beats passam a aparecer em jogo, e ao voltar da masmorra o grupo cai na ilustração da cidade em vez do mapa-múndi.

**Architecture:** O editor de slides já existe dentro do IIFE de `tools/editor_campaign.js`; ele é extraído para um módulo compartilhado `tools/editor_story.js` (`window.EDITOR_STORY`) e passa a ser usado também pelo editor de mapa-múndi. No servidor, o runtime de história já aceita slides (`_story_norm`) — o que falta é preservar o objeto ao salvar a aventura (`_clean_story_field`) e emitir os beats de abertura e de encerramento. No cliente, uma linha esconde o overlay do mapa-múndi ao entrar na masmorra.

**Tech Stack:** Python 3 + `websockets` (servidor autoritativo), JS vanilla sem bundler (`game.js`, `src/gameState.js`, `tools/editor*.js`), testes em scripts `asyncio` (`tools/test_*.py`).

**Spec:** `docs/superpowers/specs/2026-07-28-historia-em-slides-nas-aventuras-design.md`

---

## Contexto que o implementador precisa

**Rodar um teste:** da raiz, `python tools/test_masmorra_sequenciada.py`. Imprime `=== N passou, M falhou ===`. Não há pytest — cada suíte é um script com `check(nome, condição)`.

**O sistema de história (já existente):**
- `_story_norm(val)` (server.py) aceita string, `{slides:[{text,image,fit}], audio}` ou vazio, e devolve `{'slides': [...], 'audio': str|None}`.
- `_story_beat(key, parts)` concatena vários campos num beat `{key, slides, audio}`; devolve `None` se tudo for vazio.
- O cliente já consome sem mudança: `_captarStory` (`src/gameState.js:1717`) lê `msg.story` de **qualquer** mensagem e deduplica por `beat.key`; `renderStory` (`game.js`) desenha o slideshow.
- `self._story_encadeada` (server.py) já é enviado em `game_state.story` e limpo em `_voltar_para_cidade`.

**Upload de mídia (já existente):** `window.STORY_UPLOAD.upload(file)` (`tools/story_upload.js`) manda o arquivo por WebSocket e o servidor grava em `assets/story/`. O editor guarda no slide o caminho `assets/story/<nome>`.

**Convenção de commit:** mensagens em português, prefixo `feat(...)`/`test(...)`/`docs(...)`. **Faça `git add` só dos arquivos que você tocou** — nunca `git add -A`.

**Estado do repositório:** `master` e `feat/instrumentos-bardo-fase5` apontam para o mesmo commit. Trabalhe na branch atual.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta feature |
|---|---|
| `tools/editor_story.js` | **Criar** — editor de slides compartilhado (`window.EDITOR_STORY`) |
| `tools/editor_campaign.js` | Passa a consumir o módulo; perde as funções extraídas |
| `tools/editor.html` | Carrega `editor_story.js` antes de quem o usa |
| `tools/editor_world.js` | Botões 📖 abertura / 📖 encerramento por etapa |
| `server.py` | `_clean_story_field`, beat de abertura, beat de encerramento, `story` no `city_state` |
| `game.js` | `hideWorldMap()` ao entrar na masmorra |
| `tools/test_masmorra_sequenciada.py` | Seções [15]–[17] |

---

### Task 1: Extrair o editor de slides para um módulo compartilhado

Refactor puro: nenhuma mudança de comportamento. A verificação é a aba Campanha continuar idêntica.

**Files:**
- Create: `tools/editor_story.js`
- Modify: `tools/editor_campaign.js` (remove as funções extraídas; passa a chamar `EDITOR_STORY`)
- Modify: `tools/editor.html:65` (lista de scripts)

- [ ] **Step 1: Criar o módulo com as funções movidas**

Crie `tools/editor_story.js` com o conteúdo abaixo. As funções são **cópia literal** de `tools/editor_campaign.js` (linhas 7, 10-18, 20-35, 36, 93-96, 98-104, 106-191 e 310-342), com **uma** mudança: dentro de `openHistoryEditor`, a chamada `window.EDITOR_CAMPAIGN.previewStory(st)` passa a ser `previewStory(st)` (a função agora mora aqui).

```javascript
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
           <span class="op-up">▲</span><span class="op-down">▼</span><span class="op-del">✕</span>
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
```

- [ ] **Step 2: Carregar o módulo no editor**

Em `tools/editor.html:65`, na lista de scripts, INSIRA `"editor_story.js"` **antes** de `"editor_campaign.js"`. A lista fica:

```javascript
var s=["../src/difficulty.js","editor_items_logic.js","editor_items_custom.js","editor_catalog.js","editor_monsters_custom.js","editor_dungeons.js","editor.js","editor_bestiary.js","editor_monster_editor.js","story_upload.js","editor_story.js","editor_campaign.js","editor_items_editor.js","editor_city.js","editor_world.js"];
```

- [ ] **Step 3: A campanha passa a consumir o módulo**

Em `tools/editor_campaign.js`, APAGUE as definições que foram movidas — `emptyStory` (linha 7), `storyFromSaved` (9-18), `storyToSaved` (19-35), `storyCount` (36), o bloco `histButtonHTML`/`pickFile`/`openHistoryEditor` (92-191, do comentário `// ── Botão de história + painel de slides ──` até o `}` que fecha `openHistoryEditor`) e `previewStory` (310-342) — e, no lugar de `emptyStory` (linha 7), INSIRA os apelidos locais:

```javascript
  // Editor de slides: mora em tools/editor_story.js (compartilhado com o mapa-múndi).
  const ES = window.EDITOR_STORY;
  const emptyStory       = ES.emptyStory;
  const storyFromSaved   = ES.storyFromSaved;
  const storyToSaved     = ES.storyToSaved;
  const storyCount       = ES.storyCount;
  const histButtonHTML   = ES.histButtonHTML;
  const openHistoryEditor = ES.openHistoryEditor;
  const previewStory     = ES.previewStory;
```

**Atenção:** `const C = {...}` na linha 4 chama `emptyStory()` na inicialização. Como `const` não sofre hoisting de valor, o bloco de apelidos acima precisa vir **antes** da declaração de `C`. Mova a declaração de `C` para depois do bloco.

A linha 345 (`window.EDITOR_CAMPAIGN = { ..., previewStory };`) fica como está — segue exportando, agora delegando ao módulo.

- [ ] **Step 4: Verificar que a aba Campanha não mudou**

Com o servidor no ar (`python server.py`), abra `http://localhost:8765/tools/editor.html`, vá à aba **Campanha** e confirme:

```
- o botão "📖 abertura" abre o painel de slides
- "＋ adicionar slide" cria um slide; "escolher imagem" abre o seletor
- "▶ pré-visualizar" roda o slideshow
- nenhum erro no console
```

No console do navegador, confirme também:

```javascript
Object.keys(window.EDITOR_STORY).length
```

Expected: `8`

- [ ] **Step 5: Commit**

```bash
git add tools/editor_story.js tools/editor_campaign.js tools/editor.html
git commit -m "refactor(editor): extrai o editor de slides para editor_story.js"
```

---

### Task 2: Preservar os slides ao salvar a aventura

Hoje `_save_world_adventures_upload` faz `str(et["intro"] or "")[:2000]`, o que transformaria um objeto de slides na sua representação textual (`"{'slides': ...}"`).

**Files:**
- Modify: `server.py` (helper novo perto de `_story_norm`; uso em `_save_world_adventures_upload`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_masmorra_sequenciada.py`, ADICIONE antes de `async def main()`:

```python
def test_slides_na_aventura():
    print("\n[15] slides sobrevivem ao salvar a aventura")
    row = {"id": "rota_slides", "nome": "Rota", "x": 10, "y": 20, "fome": 0, "sede": 0,
           "dungeons": [{"file": "test_camp_a.json", "encadear": True,
                         "intro": {"slides": [{"text": "abre", "image": "assets/story/a.png",
                                               "fit": "contain"},
                                              {"image": "../../etc/passwd"}],
                                   "audio": "assets/story/m.mp3"},
                         "outro": "só texto"},
                        {"file": "test_camp_b.json"}]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou ({res if not ok else 'ok'})", ok is True)
        et = server.WORLD_ADVENTURES["rota_slides"]["dungeons"][0]
        check("intro continua sendo objeto", isinstance(et["intro"], dict))
        check("slide com imagem preservado",
              et["intro"]["slides"][0] == {"text": "abre", "image": "assets/story/a.png",
                                           "fit": "contain"})
        check("mídia fora de assets/story/ descartada",
              len(et["intro"]["slides"]) == 1)
        check("áudio preservado", et["intro"]["audio"] == "assets/story/m.mp3")
        check("outro em texto continua string", et["outro"] == "só texto")
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()
```

E em `main()`, chame logo após `test_validacao_saida()`:

```python
    test_slides_na_aventura()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "intro continua sendo objeto" (hoje vira a string `"{'slides': ...}"`).

- [ ] **Step 3: Implementar o helper**

Em `server.py`, LOGO APÓS a função `_story_norm` (antes de `def _story_beat`), INSIRA:

```python
_STORY_MEDIA_PREFIX = "assets/story/"

def _story_media_ok(caminho):
    """Mídia de história vem do cliente e é servida como arquivo estático:
    só vale caminho dentro de assets/story/, sem subir de diretório."""
    return (isinstance(caminho, str) and caminho.startswith(_STORY_MEDIA_PREFIX)
            and ".." not in caminho)

def _clean_story_field(raw):
    """Normaliza um campo de história do editor para persistência.
    Aceita string (legado/1 slide de texto) ou {'slides':[...], 'audio':...};
    devolve string, {'slides':[...], 'audio'?} ou "" quando não sobra nada."""
    if isinstance(raw, str):
        return raw.strip()[:2000]
    norm = _story_norm(raw)
    slides = []
    for s in norm["slides"][:20]:
        slide = {}
        if s.get("text"):
            slide["text"] = s["text"][:2000]
        if _story_media_ok(s.get("image")):
            slide["image"] = s["image"]
        if not slide:
            continue
        if s.get("fit") == "contain":
            slide["fit"] = "contain"
        slides.append(slide)
    if not slides:
        return ""
    out = {"slides": slides}
    if _story_media_ok(norm.get("audio")):
        out["audio"] = norm["audio"]
    return out
```

- [ ] **Step 4: Usar o helper ao salvar**

Em `_save_world_adventures_upload`, SUBSTITUA:

```python
                etapas.append({"file": et["file"], "encadear": et["encadear"],
                               "intro": str(et["intro"] or "")[:2000],
                               "outro": str(et["outro"] or "")[:2000]})
```

por:

```python
                etapas.append({"file": et["file"], "encadear": et["encadear"],
                               "intro": _clean_story_field(et["intro"]),
                               "outro": _clean_story_field(et["outro"])})
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 85 passou, 0 falhou ===`

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(aventuras): preserva slides de historia ao salvar a aventura"
```

---

### Task 3: Beat de abertura ao entrar numa etapa

**Files:**
- Modify: `server.py` (`handle_world_adventure`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

ADICIONE em `tools/test_masmorra_sequenciada.py`:

```python
async def test_beat_abertura():
    print("\n[16] abertura da etapa ao entrar pelo mapa")
    r = setup_room(encadear=True)
    # a etapa 0 da aventura de teste não tem intro; damos um a ela
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][0]["intro"] = "ABRE-1"
    await r.handle_world_adventure("p1", "test_seq")
    beat = r._story_encadeada
    check("beat de abertura montado", beat is not None)
    check("texto da abertura",
          beat and [s.get("text") for s in beat["slides"]] == ["ABRE-1"])
    check("key identifica aventura e etapa", beat and beat["key"] == "aventura:test_seq:0")
    # etapa sem intro não emite beat
    r2 = setup_room(encadear=True)
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][0]["intro"] = ""
    await r2.handle_world_adventure("p1", "test_seq")
    check("sem intro não emite beat", r2._story_encadeada is None)
```

E em `main()`:

```python
    await test_beat_abertura()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "beat de abertura montado" (`_story_encadeada` é `None`).

- [ ] **Step 3: Implementar**

Em `server.py`, dentro de `handle_world_adventure`, LOGO APÓS a linha:

```python
        self.world_adventure_index = stage_index
```

INSIRA:

```python
        # Abertura da etapa (slides autorados no editor de mapa-múndi). Vale para
        # toda etapa iniciada pelo mapa, não só a primeira.
        self._story_encadeada = _story_beat(
            f"aventura:{adventure['id']}:{stage_index}",
            [_etapa_obj(stages[stage_index]).get("intro")])
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 89 passou, 0 falhou ===`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(aventuras): exibe a abertura da etapa ao entrar pelo mapa-mundi"
```

---

### Task 4: Beat de encerramento ao voltar para a cidade

`_voltar_para_cidade` limpa `self._story_encadeada` e **logo em seguida** faz o broadcast do `city_state`. Gravar o beat antes da chamada não funcionaria — por isso ele passa a receber o beat por parâmetro.

**Files:**
- Modify: `server.py` (`_voltar_para_cidade`, `_city_state_payload`, ramo não-encadeado de `handle_encerrar_missao`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

ADICIONE em `tools/test_masmorra_sequenciada.py`:

```python
async def test_beat_encerramento():
    print("\n[17] encerramento ao concluir a etapa sem encadeamento")
    r = setup_room(encadear=False)     # etapa 0 tem outro "FECHA-1"
    await r.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r)
    check("voltou à cidade", r.phase == "city")
    beat = r._story_encadeada
    check("beat de encerramento montado", beat is not None)
    check("texto do encerramento",
          beat and [s.get("text") for s in beat["slides"]] == ["FECHA-1"])
    check("key identifica a etapa concluída", beat and beat["key"] == "fim:test_seq:0")
    check("city_state carrega o beat",
          r._city_state_payload().get("story") == beat)
    # etapa sem outro não emite beat
    r2 = setup_room(encadear=False)
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][0]["outro"] = ""
    await r2.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r2)
    check("sem outro não emite beat", r2._story_encadeada is None)
```

E em `main()`:

```python
    await test_beat_encerramento()
```

**Atenção:** `setup_room` reinstala a aventura de teste a cada chamada (`server.WORLD_ADVENTURES["test_seq"] = _aventura(...)`), então o `outro` zerado no fim deste teste não vaza para os outros.

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "beat de encerramento montado".

- [ ] **Step 3: `_voltar_para_cidade` aceita um beat**

Em `server.py`, SUBSTITUA as duas primeiras linhas de `_voltar_para_cidade`:

```python
    async def _voltar_para_cidade(self):
        """Transição masmorra→cidade reusável (saída pela escada e avanço de fase)."""
        self._cancelar_timer_turno()   # fora da masmorra não há timer de turno
        self.phase = "city"
        self._story_encadeada = None   # a emenda não sobrevive à volta para a cidade
```

por:

```python
    async def _voltar_para_cidade(self, story=None):
        """Transição masmorra→cidade reusável (saída pela escada e avanço de fase).
        `story` é o beat de encerramento a exibir na cidade — gravado DEPOIS da
        limpeza, já que o broadcast do city_state acontece aqui dentro."""
        self._cancelar_timer_turno()   # fora da masmorra não há timer de turno
        self.phase = "city"
        self._story_encadeada = story   # limpa a emenda; instala o encerramento, se houver
```

- [ ] **Step 4: `city_state` carrega o beat**

Em `_city_state_payload`, LOGO APÓS a linha `"campaign": self._campaign_payload(),`, INSIRA:

```python
            "story": self._story_encadeada,   # encerramento da etapa; de-dup por key no cliente
```

- [ ] **Step 5: Montar o beat no ramo não-encadeado**

Em `handle_encerrar_missao`, no ramo `if self.world_adventure_id:`, SUBSTITUA:

```python
            self.world_adventure_id = None
            self.world_adventure_index = None
            self.dungeon_generated = False
            self._objetivo_concluido = False
            await self.gm_say(f"🏁 **{adventure_name}** concluída! O grupo retorna gratuitamente à cidade." + (f" Renome {reward:+d}." if reward else ""))
            await self._voltar_para_cidade()
            return
```

por:

```python
            # Encerramento da etapa concluída (última da rota ou intermediária sem
            # encadeamento): nos dois casos o grupo volta à cidade e vê este beat.
            fim = _story_beat(f"fim:{adventure_id}:{completed_index}",
                              [etapa.get("outro")])
            self.world_adventure_id = None
            self.world_adventure_index = None
            self.dungeon_generated = False
            self._objetivo_concluido = False
            await self.gm_say(f"🏁 **{adventure_name}** concluída! O grupo retorna gratuitamente à cidade." + (f" Renome {reward:+d}." if reward else ""))
            await self._voltar_para_cidade(story=fim)
            return
```

`etapa` já existe algumas linhas acima (`etapa = _etapa_obj(stages[completed_index]) if ... else {"encadear": False}`); como `.get("outro")` devolve `None` no ramo de fallback, o beat sai `None` e nada é exibido.

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 95 passou, 0 falhou ===`

Não-regressão (os dois exercitam `_voltar_para_cidade`):
Run: `python tools/test_campanha.py` → `0 falhou`
Run: `python tools/test_persistencia_masmorra.py` → `0 falhou`

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(aventuras): exibe o encerramento da etapa ao voltar para a cidade"
```

---

### Task 5: Botões de história por etapa no editor de mapa-múndi

**Files:**
- Modify: `tools/editor_world.js` (normalização das etapas, linhas da sequência, handlers, envio ao salvar)

- [ ] **Step 1: Normalizar a história de cada etapa em memória**

Em `tools/editor_world.js`, na função `form`, SUBSTITUA a linha que normaliza as etapas:

```javascript
    a.dungeons=a.dungeons.map(d=>typeof d==='string'?{file:d,encadear:false,intro:'',outro:''}:{file:d.file,encadear:!!d.encadear,intro:d.intro||'',outro:d.outro||''});
```

por:

```javascript
    // Etapa: string (formato antigo) ou {file,encadear,intro,outro}. `intro`/`outro`
    // viram objetos de slides em memória (_introSt/_outroSt) e voltam à forma
    // mínima no salvar, via EDITOR_STORY.
    const ES=window.EDITOR_STORY;
    a.dungeons=a.dungeons.map(d=>{
      const st=(typeof d==='string')?{file:d,encadear:false,intro:'',outro:''}
                                    :{file:d.file,encadear:!!d.encadear,intro:d.intro||'',outro:d.outro||''};
      if(!st._introSt) st._introSt=ES.storyFromSaved(st.intro);
      if(!st._outroSt) st._outroSt=ES.storyFromSaved(st.outro);
      return st;
    });
```

- [ ] **Step 2: Trocar as textareas por botões de história**

Na mesma função, SUBSTITUA as duas linhas de textarea dentro de `sequence`:

```javascript
      +'<label>Encerramento<textarea data-stage-outro="'+index+'" rows="2">'+esc(stage.outro||'')+'</textarea></label>'
      +'<label>Abertura<textarea data-stage-intro="'+index+'" rows="2">'+esc(stage.intro||'')+'</textarea></label>'
```

por:

```javascript
      +'<span class="worlded-stage-hist">'
      +  ES.histButtonHTML('stage-intro-'+index, stage._introSt).replace('história','abertura')
      +  ES.histButtonHTML('stage-outro-'+index, stage._outroSt).replace('história','encerramento')
      +'</span>'
```

- [ ] **Step 3: Ligar os botões ao painel de slides**

SUBSTITUA os três handlers de textarea/checkbox que ficam após `data-stage-remove`:

```javascript
    host.querySelectorAll('[data-stage-chain]').forEach(cb=>cb.onchange=()=>{a.dungeons[Number(cb.dataset.stageChain)].encadear=cb.checked;});
    host.querySelectorAll('[data-stage-intro]').forEach(ta=>ta.oninput=()=>{a.dungeons[Number(ta.dataset.stageIntro)].intro=ta.value;});
    host.querySelectorAll('[data-stage-outro]').forEach(ta=>ta.oninput=()=>{a.dungeons[Number(ta.dataset.stageOutro)].outro=ta.value;});
```

por:

```javascript
    host.querySelectorAll('[data-stage-chain]').forEach(cb=>cb.onchange=()=>{a.dungeons[Number(cb.dataset.stageChain)].encadear=cb.checked;});
    a.dungeons.forEach((stage,index)=>{
      const bi=host.querySelector('.stage-intro-'+index), bo=host.querySelector('.stage-outro-'+index);
      if(bi) bi.onclick=()=>ES.openHistoryEditor(stage._introSt, 'abertura da etapa '+(index+1), render);
      if(bo) bo.onclick=()=>ES.openHistoryEditor(stage._outroSt, 'encerramento da etapa '+(index+1), render);
    });
```

`render` é a função de render do módulo (já usada pelos botões ↑/↓/×); passá-la como `onChange` atualiza o contador de slides do botão ao fechar o painel.

- [ ] **Step 4: Serializar a história ao salvar**

SUBSTITUA o handler de salvar (`$('#worlded-save',root).onclick=...`) por uma versão que converte a história antes de enviar:

```javascript
    $('#worlded-save',root).onclick=async()=>{const status=$('#worlded-status',root);if(!window.EDITOR_SAVE||!window.EDITOR_SAVE.saveWorldAdventures){status.textContent='Ligue o servidor para salvar.';return;}status.textContent='Salvando…';
      const ES=window.EDITOR_STORY;
      // Envia a forma mínima da história (string quando é 1 slide só-texto).
      const aventuras=config.adventures.map(av=>Object.assign({},av,{dungeons:(av.dungeons||[]).map(s=>{
        if(typeof s==='string') return s;
        const o={file:s.file,encadear:!!s.encadear};
        const i=s._introSt?ES.storyToSaved(s._introSt):s.intro;
        const u=s._outroSt?ES.storyToSaved(s._outroSt):s.outro;
        if(i) o.intro=i; if(u) o.outro=u;
        return o;
      })}));
      try{config=await window.EDITOR_SAVE.saveWorldAdventures(config.locations,aventuras);status.textContent='✓ Mapa salvo.';render();}catch(e){status.textContent='Erro ao salvar: '+e.message;}};
```

- [ ] **Step 5: Verificar no editor real**

Com `python server.py` no ar, abra `http://localhost:8765/tools/editor.html` → aba **Mapa do Mundo** → selecione um destino com pelo menos uma etapa. Confirme:

```
- cada etapa mostra "📖 abertura" e "📖 encerramento"
- clicar abre o painel de slides; "＋ adicionar slide" e "escolher imagem" funcionam
- ao fechar o painel, o contador aparece no botão (ex.: "📖 abertura (2)")
- "Salvar mapa do mundo" grava; recarregar a página traz os slides de volta
- nenhum erro no console
```

- [ ] **Step 6: Commit**

```bash
git add tools/editor_world.js
git commit -m "feat(editor): historia em slides por etapa no mapa-mundi"
```

---

### Task 6: Voltar da masmorra cai na cidade, não no mapa-múndi

**Files:**
- Modify: `game.js` (handler de `enterDungeon`)

- [ ] **Step 1: Esconder o overlay ao entrar na masmorra**

Em `game.js`, no handler `GS.on('enterDungeon', () => {`, LOGO APÓS `fecharFichaCidade();`, INSIRA:

```javascript
  // O mapa-múndi é um overlay sobre screen-city e só some quando a cidade MUDA.
  // Entrar numa aventura não muda a cidade, então sem isto o jogador voltaria da
  // masmorra para o mapa-múndi em vez da ilustração da cidade.
  hideWorldMap();
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída (sucesso)

- [ ] **Step 3: Verificar no navegador**

Com o servidor no ar, abra `http://localhost:8765/index.html` e, no console:

```javascript
(()=>{ showWorldMap ? null : null;
  const el = document.getElementById('worldmap-overlay');
  return typeof hideWorldMap; })()
```

Expected: `"function"` — e nenhum erro no console ao carregar a página.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "fix(cliente): esconde o mapa-mundi ao entrar na masmorra"
```

---

## Verificação final

- [ ] `python tools/test_masmorra_sequenciada.py` → `0 falhou`
- [ ] `python tools/test_campanha.py` → `0 falhou`
- [ ] `python tools/test_persistencia_masmorra.py` → `0 falhou`
- [ ] `python tools/test_objetivos.py` → `0 falhou`
- [ ] `python tools/test_cidades_editor.py` → `0 falharam`
- [ ] Aba **Campanha** do editor conferida no navegador (não-regressão da extração)
- [ ] Aba **Mapa do Mundo** conferida: slides salvam e recarregam
- [ ] Em jogo: entrar numa aventura com abertura autorada mostra o slideshow; concluir mostra o encerramento e a tela fica na cidade
- [ ] Atualizar o bloco da feature no `CLAUDE.md`: `intro`/`outro` de etapa aceitam slides, os três beats e o `story` no `city_state`
