# História em slides com imagens e áudio — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que abertura/encerramento da campanha e de cada fase sejam uma sequência de slides (imagem de fundo + texto, layout cinematográfico) com música de fundo em loop, montados no editor de campanhas com pré-visualização.

**Architecture:** O servidor normaliza cada campo de história (string legada ou objeto `{slides, audio}`), concatena as sequências (campanha+fase) e envia um "beat" `{key, slides, audio}`. O cliente em jogo (`game.js`) renderiza um slideshow full-screen com áudio. O editor (`tools/editor_campaign.js`) ganha um painel para montar slides + áudio + preview. Imagens/áudios são arquivos em `assets/story/` referenciados por caminho (nada de base64 no broadcast).

**Tech Stack:** Python (`server.py`, asyncio, sem framework de teste — usa o harness `check()` de `tools/test_campanha.py`), JS vanilla (`game.js`, `src/gameState.js`, `tools/editor_campaign.js`), CSS (`game.css`, `tools/editor.css`).

**Spec:** `docs/superpowers/specs/2026-06-22-historia-slides-imagens-audio-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `assets/story/.gitkeep` | nova pasta para imagens/áudios da história |
| `server.py` | `_story_norm`, `_story_beat`, `_validar_story`; usar slides+audio em `_campaign_payload`, encerramento e final |
| `tools/test_campanha.py` | atualizar teste de história (slides) + novos testes (objeto, áudio, validação) |
| `src/gameState.js` | sem mudança de lógica (beat passa por intacto) — só verificação |
| `game.js` | `renderStory` vira slideshow + áudio + controles |
| `game.css` | estilos do slideshow |
| `tools/editor_campaign.js` | modelo normalizado, botões de história, painel de slides, áudio, file-pick, save/load, preview |
| `tools/editor.css` | estilos do painel e do preview |
| `CLAUDE.md` | nota no protocolo (beat agora carrega slides/audio) |

---

## Task 1: Servidor — normalização da história (`_story_norm`, `_story_beat`)

**Files:**
- Modify: `server.py` (perto de `_fase_obj`, ~linha 1859)
- Test: `tools/test_campanha.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione esta função em `tools/test_campanha.py` (antes de `async def main`):

```python
def test_story_norm():
    print("\n[11] _story_norm / _story_beat")
    # string vira 1 slide de texto
    n = server._story_norm("oi")
    check("string -> 1 slide texto", n == {"slides": [{"text": "oi"}], "audio": None})
    # vazio -> sem slides
    check("vazio -> sem slides", server._story_norm("")["slides"] == [])
    check("None -> sem slides", server._story_norm(None)["slides"] == [])
    # objeto: slides + audio, fit default cover, slide vazio descartado
    obj = {"slides": [
        {"text": "a", "image": "assets/story/x.png", "fit": "contain"},
        {"image": "assets/story/y.png"},
        {"text": "", "image": ""},      # descartado
        {"text": "c"},
    ], "audio": "assets/story/m.mp3"}
    n = server._story_norm(obj)
    check("audio preservado", n["audio"] == "assets/story/m.mp3")
    check("3 slides válidos", len(n["slides"]) == 3)
    check("fit contain mantido", n["slides"][0]["fit"] == "contain")
    check("fit default cover", n["slides"][1]["fit"] == "cover")
    check("slide sem image perde a chave image", "image" not in n["slides"][2])
    # _story_beat concatena na ordem e pega o 1º áudio
    beat = server._story_beat("k", ["abre", {"slides": [{"text": "b"}], "audio": "assets/story/t.ogg"}])
    check("beat concatena", [s.get("text") for s in beat["slides"]] == ["abre", "b"])
    check("beat 1º áudio", beat["audio"] == "assets/story/t.ogg")
    check("beat vazio -> None", server._story_beat("k", ["", None]) is None)
```

E registre a chamada em `main`, logo após `await test_roundtrip_editor_campanha()`:

```python
    test_story_norm()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute '_story_norm'`

- [ ] **Step 3: Implementar `_story_norm` e `_story_beat`**

Em `server.py`, logo após a função `_fase_obj` (~linha 1864), adicione:

```python
def _story_norm(val):
    """Normaliza um campo de história para {'slides': [...], 'audio': str|None}.
    Aceita string (legado = 1 slide de texto), objeto {'slides','audio'} ou vazio.
    Slides sem text nem image são descartados; fit default 'cover'."""
    if not val:
        return {"slides": [], "audio": None}
    if isinstance(val, str):
        return {"slides": [{"text": val}], "audio": None}
    if isinstance(val, dict):
        out = []
        for s in (val.get("slides") or []):
            if not isinstance(s, dict):
                continue
            slide = {}
            if isinstance(s.get("text"), str) and s["text"]:
                slide["text"] = s["text"]
            if isinstance(s.get("image"), str) and s["image"]:
                slide["image"] = s["image"]
            if not slide:
                continue
            slide["fit"] = "contain" if s.get("fit") == "contain" else "cover"
            out.append(slide)
        audio = val.get("audio")
        audio = audio if (isinstance(audio, str) and audio) else None
        return {"slides": out, "audio": audio}
    return {"slides": [], "audio": None}


def _story_beat(key, parts):
    """parts: lista de campos de história (string|objeto) na ORDEM de exibição.
    Retorna {'key','slides','audio'} ou None se não houver slides. O áudio é o
    primeiro não-nulo encontrado na ordem das partes."""
    slides, audio = [], None
    for p in parts:
        n = _story_norm(p)
        slides.extend(n["slides"])
        if audio is None and n["audio"]:
            audio = n["audio"]
    if not slides:
        return None
    return {"key": key, "slides": slides, "audio": audio}
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_campanha.py`
Expected: o bloco `[11]` passa. (O bloco `[9]` ainda pode falhar — será corrigido na Task 2.)

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat(historia): _story_norm/_story_beat normalizam slides+audio"
```

---

## Task 2: Servidor — beat com slides/audio em payload, encerramento e final

**Files:**
- Modify: `server.py` — `_campaign_payload` (~12219), bloco de conclusão de fase (~12108-12122)
- Test: `tools/test_campanha.py` (atualizar `test_historia_runtime`, novo `test_historia_audio`)

- [ ] **Step 1: Atualizar o teste existente para slides + novo teste de áudio**

Em `tools/test_campanha.py`, **substitua** o corpo de `test_historia_runtime` (bloco `[9]`) por:

```python
async def test_historia_runtime():
    print("\n[9] runtime da história (slides)")
    def textos(beat): return [s.get("text") for s in beat["slides"]]
    r = setup_room(); r.mode = "campaign"; r.campaign = _camp_hist(); r.campaign_phase = 0; r.phase = "city"
    await r.enter_dungeon("p1")
    pay = r._campaign_payload()
    check("abertura da fase 0 inclui abertura da campanha",
          pay["story"] and textos(pay["story"]) == ["ABERTURA-CAMP", "ABRE-1"])
    check("key de abertura", pay["story"]["key"] == "intro:0")
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("foi para a cidade", r.phase == "city")
    payc = r._campaign_payload()
    check("encerramento da fase 0 na cidade",
          payc["story"] and textos(payc["story"]) == ["FECHA-1"] and payc["story"]["key"] == "outro:0")
    await r.enter_dungeon("p1")
    pay1 = r._campaign_payload()
    check("abertura da fase 1 (sem abertura da campanha)",
          pay1["story"] and textos(pay1["story"]) == ["ABRE-2"])
    cap = {}
    async def fake_end(victory, story=None): cap["victory"] = victory; cap["story"] = story
    r.end_game = fake_end
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("última fase → end_game com story final",
          cap.get("victory") is True and cap.get("story")
          and textos(cap["story"]) == ["FECHA-2", "FINAL-CAMP"])


async def test_historia_audio():
    print("\n[12] precedência do áudio na junção")
    camp = {"schema_version": 1, "id": "ca", "name": "CA",
            "intro": {"slides": [{"text": "ic"}], "audio": "assets/story/camp.mp3"},
            "dungeons": [{"file": "test_camp_a.json",
                          "intro": {"slides": [{"text": "if"}], "audio": "assets/story/fase.mp3"},
                          "outro": {"slides": [{"text": "of"}], "audio": "assets/story/of.mp3"}},
                         {"file": "test_camp_b.json"}]}
    r = setup_room(); r.mode = "campaign"; r.campaign = camp; r.campaign_phase = 0; r.phase = "city"
    await r.enter_dungeon("p1")
    pay = r._campaign_payload()
    check("abertura: áudio da campanha vem antes (precede a fase)",
          pay["story"]["audio"] == "assets/story/camp.mp3")
    check("abertura junta os 2 slides",
          [s["text"] for s in pay["story"]["slides"]] == ["ic", "if"])
```

E registre o novo teste em `main`, após `test_story_norm()`:

```python
    await test_historia_audio()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL nos blocos `[9]`/`[12]` — `KeyError: 'slides'` (o payload ainda usa `text`).

- [ ] **Step 3: Trocar a montagem do beat para slides/audio**

Em `server.py`, no `_campaign_payload` (~12226-12236), **substitua** o trecho do `if self.phase == "playing":` até o `elif ... self._campaign_outro` por:

```python
        if self.phase == "playing":
            fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
            parts = []
            if self.campaign_phase == 0:
                parts.append(self.campaign.get("intro"))
            parts.append(fase.get("intro"))
            pay["story"] = _story_beat(f"intro:{self.campaign_phase}", parts)
        elif self.phase == "city" and self._campaign_outro:
            pay["story"] = self._campaign_outro
```

No bloco de conclusão de fase (~12108-12110), **substitua**:

```python
                fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                self._campaign_outro = ({"key": f"outro:{self.campaign_phase}", "text": fase["outro"]}
                                        if fase.get("outro") else None)
```

por:

```python
                fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                self._campaign_outro = _story_beat(f"outro:{self.campaign_phase}", [fase.get("outro")])
```

No bloco do final da campanha (~12117-12122), **substitua**:

```python
                story = None
                if self.mode == "campaign" and self.campaign:
                    fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                    partes = [p for p in (fase.get("outro"), self.campaign.get("outro")) if p]
                    if partes:
                        story = {"key": f"final:{self.campaign_phase}", "text": "\n\n".join(partes)}
                await self.end_game(victory=True, story=story)
```

por:

```python
                story = None
                if self.mode == "campaign" and self.campaign:
                    fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                    story = _story_beat(f"final:{self.campaign_phase}",
                                        [fase.get("outro"), self.campaign.get("outro")])
                await self.end_game(victory=True, story=story)
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_campanha.py`
Expected: blocos `[9]` e `[12]` passam; os demais continuam passando.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat(historia): payload/encerramento/final enviam beat com slides+audio"
```

---

## Task 3: Servidor — validação aceita string ou objeto de história

**Files:**
- Modify: `server.py` — `validar_campanha` (~1866-1893), nova `_validar_story`
- Test: `tools/test_campanha.py` (`test_validacao_story`)

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_campanha.py`, adicione:

```python
def test_validacao_story():
    print("\n[13] validação de história (string|objeto)")
    base = {"schema_version": 1, "id": "c", "name": "C"}
    ok = lambda d: server.validar_campanha(d)[0]
    # string ainda válida
    check("intro string ok", ok(dict(base, intro="oi", dungeons=["test_camp_a.json"])) is True)
    # objeto de slides válido
    d = dict(base, dungeons=[{"file": "test_camp_a.json",
        "intro": {"slides": [{"text": "a", "image": "assets/story/x.png", "fit": "cover"}],
                  "audio": "assets/story/m.mp3"}}])
    check("objeto slides ok", ok(d) is True)
    # slide sem text nem image recusa
    d = dict(base, dungeons=[{"file": "test_camp_a.json", "intro": {"slides": [{}]}}])
    check("slide vazio recusa", ok(d) is False)
    # fit inválido recusa
    d = dict(base, dungeons=[{"file": "test_camp_a.json",
        "intro": {"slides": [{"text": "a", "fit": "zoom"}]}}])
    check("fit inválido recusa", ok(d) is False)
    # slides não-lista recusa
    d = dict(base, intro={"slides": "x"}, dungeons=["test_camp_a.json"])
    check("slides não-lista recusa", ok(d) is False)
    # audio não-string recusa
    d = dict(base, intro={"slides": [{"text": "a"}], "audio": 5}, dungeons=["test_camp_a.json"])
    check("audio não-string recusa", ok(d) is False)
```

Registre em `main`, após `test_validacao()` (é síncrono):

```python
    test_validacao_story()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL no bloco `[13]` — "objeto slides ok" recusado (validação atual exige string).

- [ ] **Step 3: Implementar `_validar_story` e usá-la em `validar_campanha`**

Em `server.py`, logo antes de `def validar_campanha` (~1866), adicione:

```python
def _validar_story(val, rotulo):
    """(ok, msg) — aceita string (legado) ou objeto {'slides':[...], 'audio'?}."""
    if isinstance(val, str):
        return True, "ok"
    if not isinstance(val, dict):
        return False, f"{rotulo}: deve ser texto ou objeto de história."
    slides = val.get("slides")
    if not isinstance(slides, list):
        return False, f"{rotulo}: 'slides' deve ser uma lista."
    for j, s in enumerate(slides):
        if not isinstance(s, dict):
            return False, f"{rotulo}: slide {j+1} deve ser um objeto."
        if "text" in s and not isinstance(s["text"], str):
            return False, f"{rotulo}: slide {j+1} 'text' deve ser texto."
        if "image" in s and not isinstance(s["image"], str):
            return False, f"{rotulo}: slide {j+1} 'image' deve ser texto."
        if "fit" in s and s["fit"] not in ("cover", "contain"):
            return False, f"{rotulo}: slide {j+1} 'fit' deve ser 'cover' ou 'contain'."
        if not (s.get("text") or s.get("image")):
            return False, f"{rotulo}: slide {j+1} precisa de texto ou imagem."
    if "audio" in val and not isinstance(val["audio"], str):
        return False, f"{rotulo}: 'audio' deve ser texto."
    return True, "ok"
```

Em `validar_campanha`, **substitua** o laço de nível-campanha (~1876-1878):

```python
    for k in ("intro", "outro"):
        if k in defn and not isinstance(defn[k], str):
            return False, f"campanha: '{k}' deve ser texto."
```

por:

```python
    for k in ("intro", "outro"):
        if k in defn:
            ok, msg = _validar_story(defn[k], f"campanha '{k}'")
            if not ok:
                return False, msg
```

E **substitua** o laço por-fase (~1883-1886):

```python
        if isinstance(item, dict):
            for k in ("intro", "outro"):
                if k in item and not isinstance(item[k], str):
                    return False, f"fase {i+1}: '{k}' deve ser texto."
```

por:

```python
        if isinstance(item, dict):
            for k in ("intro", "outro"):
                if k in item:
                    ok, msg = _validar_story(item[k], f"fase {i+1} '{k}'")
                    if not ok:
                        return False, msg
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_campanha.py`
Expected: todos os blocos passam (`=== N passou, 0 falhou ===`).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat(historia): validar_campanha aceita string ou objeto de slides"
```

---

## Task 4: Cliente em jogo — slideshow no `renderStory` + áudio + CSS

**Files:**
- Modify: `game.js` — `renderStory` (~971-990)
- Modify: `game.css` — bloco `#story-*` (~741-747)
- Verify: `src/gameState.js` (`_captarStory`/`pendingStory` já passam o beat intacto — sem mudança)

> Sem harness de teste JS no projeto: verificação é manual, rodando o jogo.

- [ ] **Step 1: Substituir `renderStory` por um slideshow**

Em `game.js`, **substitua** toda a função `renderStory` (linhas ~971-990) por:

```javascript
// Slideshow de história (layout A): imagem de fundo + texto sobreposto + áudio
// em loop. Cada cliente navega seus próprios slides; "Continuar" no último marca
// o beat como visto (de-dup por key em gameState.js).
let _storyIdx = 0;
let _storyMuted = false;
let _storyAudioEl = null;

function _storyAudioStop() {
  if (_storyAudioEl) { try { _storyAudioEl.pause(); } catch (e) {} _storyAudioEl.src = ''; _storyAudioEl = null; }
}

function _storyPaintMute() {
  const ov = document.getElementById('story-overlay');
  if (ov) ov.querySelector('#story-mute').textContent = _storyMuted ? '🔇' : '🔊';
}

function _storyPaint() {
  const beat = GS.pendingStory && GS.pendingStory();
  const ov = document.getElementById('story-overlay');
  if (!beat || !ov) return;
  const slide = beat.slides[_storyIdx] || {};
  const img = ov.querySelector('#story-img');
  if (slide.image) {
    img.style.backgroundImage = 'url("' + slide.image + '")';
    img.style.backgroundSize = (slide.fit === 'contain') ? 'contain' : 'cover';
  } else {
    img.style.backgroundImage = 'none';
  }
  const txtEl = ov.querySelector('#story-text');
  txtEl.textContent = slide.text || '';
  txtEl.style.display = slide.text ? 'block' : 'none';
  const dots = ov.querySelector('#story-dots');
  dots.innerHTML = '';
  beat.slides.forEach((_, i) => {
    const d = document.createElement('span');
    d.className = 'story-dot' + (i === _storyIdx ? ' on' : '');
    dots.appendChild(d);
  });
  ov.querySelector('#story-prev').style.visibility = _storyIdx > 0 ? 'visible' : 'hidden';
  ov.querySelector('#story-continue').textContent =
    (_storyIdx < beat.slides.length - 1) ? 'Continuar →' : 'Concluir';
  _storyPaintMute();
}

function renderStory() {
  const beat = GS.pendingStory && GS.pendingStory();
  let ov = document.getElementById('story-overlay');
  if (!beat || !beat.slides || !beat.slides.length) {
    if (ov) ov.style.display = 'none';
    _storyAudioStop();
    return;
  }
  if (!ov) {
    ov = document.createElement('div'); ov.id = 'story-overlay';
    ov.innerHTML =
      '<div id="story-img"></div>'
      + '<div id="story-scrim"></div>'
      + '<button id="story-mute" title="Som">🔊</button>'
      + '<div id="story-box">'
      +   '<div id="story-text"></div>'
      +   '<div id="story-nav">'
      +     '<button id="story-prev">‹ Voltar</button>'
      +     '<div id="story-dots"></div>'
      +     '<button id="story-continue">Continuar →</button>'
      +   '</div>'
      + '</div>';
    document.body.appendChild(ov);
    ov.querySelector('#story-prev').onclick = () => {
      if (_storyIdx > 0) { _storyIdx--; _storyPaint(); }
    };
    ov.querySelector('#story-continue').onclick = () => {
      const b = GS.pendingStory && GS.pendingStory();
      if (!b) return;
      if (_storyIdx < b.slides.length - 1) { _storyIdx++; _storyPaint(); }
      else { GS.marcarStoryVista(b.key); _storyAudioStop(); ov.style.display = 'none'; }
    };
    ov.querySelector('#story-mute').onclick = () => {
      _storyMuted = !_storyMuted;
      if (_storyAudioEl) _storyAudioEl.muted = _storyMuted;
      _storyPaintMute();
    };
  }
  // (Re)inicializa só quando o beat muda — evita resetar o índice/áudio a cada
  // broadcast de game_state (que reenvia a história enquanto ela está aberta).
  if (ov.dataset.key !== beat.key) {
    ov.dataset.key = beat.key;
    _storyIdx = 0;
    beat.slides.forEach(s => { if (s.image) { const im = new Image(); im.src = s.image; } });
    _storyAudioStop();
    if (beat.audio) {
      _storyAudioEl = new Audio(beat.audio);
      _storyAudioEl.loop = true; _storyAudioEl.muted = _storyMuted; _storyAudioEl.volume = 0.6;
      _storyAudioEl.play().catch(() => {});
    }
  }
  ov.style.display = 'block';
  _storyPaint();
}
```

- [ ] **Step 2: Substituir o CSS do overlay**

Em `game.css`, **substitua** as linhas do bloco `#story-overlay`/`#story-box`/`#story-continue` (~741-747) por:

```css
#story-overlay { position: fixed; inset: 0; z-index: 9000; background: #0a0805; overflow: hidden; }
#story-img { position: absolute; inset: 0; background-position: center; background-repeat: no-repeat; background-color: #0a0805; }
#story-scrim { position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(to bottom, rgba(8,5,3,0.10) 35%, rgba(8,5,3,0.88) 100%); }
#story-mute { position: absolute; top: 16px; right: 16px; z-index: 2; cursor: pointer;
  background: rgba(0,0,0,0.45); color: #e8dcc0; border: 1px solid #5a4830; border-radius: 6px;
  padding: 6px 11px; font-size: 16px; }
#story-box { position: absolute; left: 0; right: 0; bottom: 0; z-index: 2;
  max-width: 820px; margin: 0 auto; padding: 22px 28px 26px; }
#story-text { color: #ece4f5; font-size: 18px; line-height: 1.6; white-space: pre-wrap;
  margin-bottom: 16px; text-shadow: 0 1px 4px rgba(0,0,0,0.85); }
#story-nav { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
#story-dots { display: flex; gap: 6px; flex: 1; justify-content: center; }
.story-dot { width: 8px; height: 8px; border-radius: 50%; background: #5a4d6b; }
.story-dot.on { background: #d9b061; }
#story-prev { background: transparent; color: #d9b061; border: 1px solid #5a4830;
  border-radius: 6px; padding: 9px 16px; font-weight: bold; cursor: pointer; }
#story-continue { background: #d9b061; color: #1d1812; border: none;
  border-radius: 6px; padding: 9px 18px; font-weight: bold; cursor: pointer; }
```

- [ ] **Step 3: Verificação manual (campanha de texto — retrocompat)**

```bash
python server.py
```
Abra `http://localhost:8765/index.html`, crie sala, escolha a campanha `test_campanha.json` (só texto), inicie e entre na fase.
Expected: o overlay aparece como 1 slide de texto, com 1 pontinho e "Concluir"; clicar fecha e não reaparece. Confirme que o jogo segue normal (sem erro no console).

- [ ] **Step 4: Verificação manual (slides + imagem + áudio)**

Crie `dungeons/_storytest_a.json` copiando `dungeons/test_camp_a.json` e crie `campaigns/_storytest.json`:

```json
{
  "schema_version": 1, "id": "_storytest", "name": "Teste História",
  "intro": { "slides": [
      { "text": "Slide 1 com imagem (cover).", "image": "assets/story/_demo.png", "fit": "cover" },
      { "text": "Slide 2 só texto." }
    ], "audio": "assets/story/_demo.mp3" },
  "dungeons": [ { "file": "test_camp_a.json" } ]
}
```
Coloque um PNG qualquer em `assets/story/_demo.png` e um mp3 curto em `assets/story/_demo.mp3`.
Recarregue, selecione "Teste História", entre na fase.
Expected: slide 1 mostra a imagem cobrindo a tela + texto embaixo + 2 pontinhos + música em loop; "Continuar" vai ao slide 2 (fundo escuro, só texto); "‹ Voltar" volta; 🔊/🔇 muta; "Concluir" fecha e para a música. Sem erros no console.

- [ ] **Step 5: Commit**

```bash
git add game.js game.css
git commit -m "feat(historia): slideshow em jogo (imagem de fundo, texto, audio em loop)"
```

---

## Task 5: Editor — modelo normalizado, botões de história, painel de slides, save/load

**Files:**
- Modify: `tools/editor_campaign.js` (reescrita)
- Modify: `tools/editor.css` (estilos do painel)

> Verificação manual abrindo `tools/editor.html` no navegador.

- [ ] **Step 1: Reescrever `tools/editor_campaign.js`**

Substitua **todo** o conteúdo de `tools/editor_campaign.js` por:

```javascript
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

  window.EDITOR_CAMPAIGN = { C, renderCampaign, dunByFile, validarCampanhaEditor, saveCampaign, loadCampaign, drawMiniMap,
                             previewStory: function () { alert("preview na próxima task"); } };
})();
```

- [ ] **Step 2: Adicionar estilos do painel em `tools/editor.css`**

Acrescente ao final de `tools/editor.css`:

```css
.hist-btn { background:#2a2230; color:#e8dcc0; border:1px solid #5a4830; border-radius:4px; padding:3px 8px; cursor:pointer; font-size:12px; }
.camp-hist-row { display:flex; gap:6px; margin-top:6px; }
.hist-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.55); z-index:5000; display:flex; align-items:center; justify-content:center; }
.hist-panel { width:680px; max-width:94vw; max-height:90vh; overflow:auto; background:#1d1812; border:1px solid #5a4830; border-radius:10px; color:#e8dcc0; }
.hist-head { display:flex; align-items:center; gap:10px; padding:12px 16px; border-bottom:1px solid #4a3c28; }
.hist-title { font-weight:bold; } .hist-spacer { flex:1; } .hist-count { color:#b7a98c; font-size:13px; }
.hist-preview { background:#3a5a8a; color:#fff; border:none; border-radius:5px; padding:6px 12px; cursor:pointer; }
.hist-audio { display:flex; align-items:center; gap:8px; padding:10px 16px; background:#241d15; border-bottom:1px solid #4a3c28; font-size:13px; }
.hist-audio-pick, .hist-img-pick { background:#33291c; color:#e8dcc0; border:1px solid #5a4830; border-radius:4px; padding:3px 10px; cursor:pointer; font-size:12px; }
.hist-audio-name { background:#1d1812; border:1px solid #4a3c28; border-radius:4px; padding:3px 8px; }
.hist-audio-x, .op-up, .op-down, .op-del { cursor:pointer; color:#c9a; user-select:none; }
.op-del, .hist-audio-x { color:#e06a6a; }
.hist-audio-hint { margin-left:auto; color:#8a7e6a; font-size:11px; }
.hist-slides { padding:12px 16px; display:flex; flex-direction:column; gap:10px; }
.hist-slide { display:flex; gap:12px; border:1px solid #4a3c28; border-radius:6px; padding:10px; }
.hist-thumb { width:96px; flex:0 0 96px; }
.hist-thumb img { width:96px; height:64px; object-fit:cover; border-radius:4px; display:block; }
.hist-noimg { display:flex; width:96px; height:64px; align-items:center; justify-content:center; border:1px dashed #5a4830; border-radius:4px; color:#8a7e6a; font-size:11px; text-align:center; }
.hist-imgname { font-size:11px; color:#8a7e6a; text-align:center; margin-top:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.hist-fields { flex:1; display:flex; flex-direction:column; gap:8px; }
.hist-row1 { display:flex; align-items:center; gap:8px; }
.hist-fit { display:inline-flex; border:1px solid #5a4830; border-radius:4px; overflow:hidden; font-size:12px; }
.fit-opt { padding:3px 10px; cursor:pointer; color:#b7a98c; }
.fit-opt.on { background:#3a5a8a; color:#fff; }
.hist-text { width:100%; min-height:46px; resize:vertical; background:#15110c; color:#e8dcc0; border:1px solid #4a3c28; border-radius:4px; font-size:13px; }
.hist-ops { display:flex; flex-direction:column; gap:6px; }
.hist-add { margin:0 16px 12px; background:#33291c; color:#e8dcc0; border:1px solid #5a4830; border-radius:4px; padding:6px 12px; cursor:pointer; }
.hist-foot { display:flex; align-items:center; gap:10px; padding:12px 16px; border-top:1px solid #4a3c28; }
.hist-note { flex:1; color:#8a7e6a; font-size:12px; } .hist-note code { color:#d9b061; }
.hist-close { background:#33291c; color:#e8dcc0; border:1px solid #5a4830; border-radius:4px; padding:6px 14px; cursor:pointer; }
```

- [ ] **Step 3: Verificação manual (montar e salvar)**

Abra `tools/editor.html` no navegador → aba **Campanha**.
- Clique em **📖 abertura** (campanha): o painel abre. Adicione 2 slides, escolha uma imagem em um (vê a miniatura), alterne cobrir/inteira, escolha um áudio, edite textos, feche.
- O botão deve mostrar **📖 abertura (2)**.
- Adicione uma fase; repita em **📖 abertura** da fase.
- Clique **Salvar** e abra o `.json` baixado.
Expected: campos `intro` com `{slides:[...], audio:"assets/story/..."}`; um campo com 1 slide só-texto sem áudio aparece como **string**; `fit:"contain"` só aparece quando escolhido "inteira".

- [ ] **Step 4: Verificação manual (round-trip)**

No editor, **Carregar** o `.json` que você salvou.
Expected: contadores dos botões corretos; reabrir um painel mostra os textos/fit/áudio; **Salvar** de novo produz o mesmo JSON (caminhos `assets/story/...`). Sem erros no console.

- [ ] **Step 5: Commit**

```bash
git add tools/editor_campaign.js tools/editor.css
git commit -m "feat(historia): editor monta slides+audio por campo (save/load string|objeto)"
```

---

## Task 6: Editor — pré-visualização do slideshow

**Files:**
- Modify: `tools/editor_campaign.js` (`previewStory`)
- Modify: `tools/editor.css` (estilos do preview — reusa o visual do jogo)

- [ ] **Step 1: Implementar `previewStory`**

Em `tools/editor_campaign.js`, **substitua** a linha do export:

```javascript
                             previewStory: function () { alert("preview na próxima task"); } };
```

por uma referência à função e a definição dela logo antes do `window.EDITOR_CAMPAIGN = {...}`:

```javascript
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
```

E no objeto exportado, troque o stub por:

```javascript
                             previewStory };
```

- [ ] **Step 2: Estilos do preview em `tools/editor.css`**

Acrescente ao final de `tools/editor.css`:

```css
.spv-overlay { position:fixed; inset:0; z-index:6000; background:#0a0805; overflow:hidden; }
.spv-img { position:absolute; inset:0; background-position:center; background-repeat:no-repeat; background-color:#0a0805; }
.spv-scrim { position:absolute; inset:0; pointer-events:none; background:linear-gradient(to bottom, rgba(8,5,3,0.10) 35%, rgba(8,5,3,0.88) 100%); }
.spv-mute { position:absolute; top:16px; right:16px; z-index:2; cursor:pointer; background:rgba(0,0,0,0.45); color:#e8dcc0; border:1px solid #5a4830; border-radius:6px; padding:6px 11px; font-size:16px; }
.spv-box { position:absolute; left:0; right:0; bottom:0; z-index:2; max-width:820px; margin:0 auto; padding:22px 28px 26px; }
.spv-text { color:#ece4f5; font-size:18px; line-height:1.6; white-space:pre-wrap; margin-bottom:16px; text-shadow:0 1px 4px rgba(0,0,0,0.85); }
.spv-nav { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.spv-dots { display:flex; gap:6px; flex:1; justify-content:center; }
.spv-dot { width:8px; height:8px; border-radius:50%; background:#5a4d6b; }
.spv-dot.on { background:#d9b061; }
.spv-prev { background:transparent; color:#d9b061; border:1px solid #5a4830; border-radius:6px; padding:9px 16px; font-weight:bold; cursor:pointer; }
.spv-next { background:#d9b061; color:#1d1812; border:none; border-radius:6px; padding:9px 18px; font-weight:bold; cursor:pointer; }
```

- [ ] **Step 3: Verificação manual**

No editor, abra um painel de história com ≥2 slides (com imagem e áudio escolhidos na sessão) e clique **▶ pré-visualizar**.
Expected: overlay full-screen com a imagem de fundo (cover/contain conforme o slide), texto embaixo, pontinhos, Voltar/Continuar navegando, 🔊/🔇 mutando, áudio em loop; "Fechar" no último slide encerra e para o áudio.

- [ ] **Step 4: Commit**

```bash
git add tools/editor_campaign.js tools/editor.css
git commit -m "feat(historia): pré-visualização do slideshow no editor"
```

---

## Task 7: Pasta de assets, doc do protocolo e fechamento

**Files:**
- Create: `assets/story/.gitkeep`
- Modify: `CLAUDE.md` (nota no protocolo)

- [ ] **Step 1: Criar a pasta servida**

```bash
mkdir -p assets/story
printf "# imagens/áudios das histórias de campanha (referenciados por assets/story/...)\n" > assets/story/.gitkeep
```

- [ ] **Step 2: Documentar o novo formato do beat no `CLAUDE.md`**

Na seção **Server → Client** do `CLAUDE.md`, na linha que descreve `game_state`/`story`, acrescente esta observação (após a linha que começa com `> game_state inclui ...`):

```markdown
> **História (slides):** os campos `intro`/`outro` da campanha e de cada fase
> aceitam string (legado) **ou** objeto `{slides:[{text?,image?,fit}], audio?}`.
> O servidor normaliza (`_story_norm`/`_story_beat`) e envia o beat
> `{key, slides, audio}` em `game_state.campaign.story` (abertura),
> `city_state.campaign.story` (encerramento) e `game_over.story` (final).
> Imagens/áudios ficam em `assets/story/` (servida) e são referenciados por
> caminho. Cliente: `renderStory` (slideshow layout A + áudio em loop).
```

- [ ] **Step 3: Rodar a suíte do servidor inteira**

Run: `python tools/test_campanha.py`
Expected: `=== N passou, 0 falhou ===`.

- [ ] **Step 4: Smoke test ponta-a-ponta**

```bash
python server.py
```
Crie a campanha de teste com slides+imagem+áudio (do Task 4, Step 4) pelo **editor**, salve em `campaigns/`, jogue do início ao fim e confira: abertura (slideshow + áudio), encerramento de fase na cidade, e final da campanha. Remova os arquivos `_storytest*`/`_demo*` de teste ao terminar.

- [ ] **Step 5: Commit**

```bash
git add assets/story/.gitkeep CLAUDE.md
git commit -m "chore(historia): pasta assets/story + nota do protocolo no CLAUDE.md"
```

---

## Self-review (cobertura do spec)

- Modelo string|objeto `{slides,audio}`: Tasks 1, 3, 5. ✓
- Pasta `assets/story/` servida (sem mudança no servidor de estáticos): Task 7. ✓
- Escopo 4 campos (campanha intro/outro + fase intro/outro): Tasks 2, 5. ✓
- Slide com text/image independentes + fit por slide (cover/contain): Tasks 1, 4, 5. ✓
- Áudio de sequência, loop, precedência na junção, mudo: Tasks 1, 2, 4, 5. ✓
- Concatenação campanha+fase preservando ordem: Task 2. ✓
- Editor: botões 📖, painel, file-pick, save string-ou-objeto, load: Task 5. ✓
- Pré-visualização no editor: Task 6. ✓
- Slideshow em jogo (layout A) + degradação (imagem/áudio ausente) + textContent: Task 4. ✓
- Validação retrocompatível: Task 3. ✓
- Doc do protocolo: Task 7. ✓
