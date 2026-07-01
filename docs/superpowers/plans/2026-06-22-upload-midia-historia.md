# Upload de mídia da história (imagens/áudio) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quando o usuário escolhe imagem/áudio no editor de história, o arquivo é enviado pela WebSocket e gravado em `assets/story/`, para que o jogo encontre a mídia (hoje só o caminho é salvo, e o arquivo nunca é copiado).

**Architecture:** O servidor (`server.py`) ganha um handler de mensagem WebSocket `upload_story` que valida e grava o arquivo em `assets/story/`. Um módulo novo no editor (`tools/story_upload.js`) abre uma WebSocket sob demanda, envia o arquivo em base64 e devolve uma Promise. O `tools/editor_campaign.js` chama esse módulo nos handlers de escolher imagem/áudio e mostra o status no card. O formato do JSON salvo não muda.

**Tech Stack:** Python 3 + `websockets` 16.0 (servidor), Vanilla JS + WebSocket/FileReader (editor). Sem framework de testes — teste de servidor é um script Python standalone; o editor é verificado rodando o app.

**Spec:** `docs/superpowers/specs/2026-06-22-upload-midia-historia-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade | Ação |
|---|---|---|
| `server.py` | `_save_story_upload()` (validação+gravação) + constantes + handler `upload_story` + `max_size` + MIME | Modificar |
| `tools/story_upload.js` | Cliente WebSocket de upload (`window.STORY_UPLOAD.upload`) | Criar |
| `tools/editor.html` | Carregar `story_upload.js` antes de `editor_campaign.js` | Modificar |
| `tools/editor_campaign.js` | Disparar upload nos handlers de imagem/áudio + status no card | Modificar |
| `tools/test_story_upload.py` | Teste do `_save_story_upload` do servidor | Criar |

---

## Task 1: Servidor — `_save_story_upload()` + constantes (TDD)

**Files:**
- Test: `tools/test_story_upload.py` (criar)
- Modify: `server.py` (imports no topo, ~linha 10-21; novas constantes/função perto de `_serve_static`, ~linha 12648)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_story_upload.py`:

```python
"""Teste do upload de mídia da história (server._save_story_upload).
Rodar da raiz: python tools/test_story_upload.py"""
import os
import sys
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server  # noqa: E402


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def run():
    fails = []

    def check(cond, label):
        print(("OK   " if cond else "FAIL ") + label)
        if not cond:
            fails.append(label)

    story_dir = server.STORY_DIR

    # caso feliz
    ok, res = server._save_story_upload("teste_upload.png", _b64(b"conteudo-img"))
    check(ok and res == "teste_upload.png", "grava imagem valida (ok + basename)")
    p = os.path.join(story_dir, "teste_upload.png")
    check(os.path.isfile(p) and open(p, "rb").read() == b"conteudo-img",
          "arquivo no disco com conteudo certo")

    # sobrescrita
    ok2, _ = server._save_story_upload("teste_upload.png", _b64(b"novo"))
    check(ok2 and open(p, "rb").read() == b"novo", "sobrescreve com novo conteudo")

    # extensao proibida
    ok3, err3 = server._save_story_upload("malware.exe", _b64(b"x"))
    check((not ok3) and err3 == "extensão não permitida", "rejeita extensao proibida")

    # path traversal -> reduz a basename (grava dentro de story/)
    ok4, res4 = server._save_story_upload("../../hack.png", _b64(b"x"))
    check(ok4 and res4 == "hack.png", "reduz ../ a basename")
    check(os.path.isfile(os.path.join(story_dir, "hack.png")),
          "grava dentro de assets/story")

    # base64 invalido
    ok5, err5 = server._save_story_upload("foto.png", "@@@nao-base64@@@")
    check((not ok5) and err5 == "dados inválidos", "rejeita base64 invalido")

    # nome vazio
    ok6, err6 = server._save_story_upload("", _b64(b"x"))
    check((not ok6) and err6 == "nome inválido", "rejeita nome vazio")

    # grande demais (rebaixa o limite temporariamente)
    saved_max = server.STORY_UPLOAD_MAX
    server.STORY_UPLOAD_MAX = 100
    try:
        ok7, err7 = server._save_story_upload("grande.png", _b64(b"x" * 400))
        check((not ok7) and err7 == "arquivo grande demais",
              "rejeita arquivo grande demais")
    finally:
        server.STORY_UPLOAD_MAX = saved_max

    # limpeza
    for n in ("teste_upload.png", "hack.png"):
        fp = os.path.join(story_dir, n)
        if os.path.isfile(fp):
            os.remove(fp)

    print()
    if fails:
        print(f"{len(fails)} FALHA(S)")
        sys.exit(1)
    print("TODOS OS TESTES PASSARAM")


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_story_upload.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'STORY_DIR'` (ou `_save_story_upload`).

- [ ] **Step 3: Adicionar `import base64` aos imports do topo**

Em `server.py`, junto dos imports (entre `import asyncio` na linha 10 e `from copy import deepcopy` na linha 20), adicionar:

```python
import base64
```

(inserir em ordem alfabética, logo após `import asyncio`)

- [ ] **Step 4: Adicionar constantes + função antes de `_serve_static`**

Em `server.py`, imediatamente antes de `def _serve_static(request):` (linha 12648), inserir:

```python
# ─── Upload de mídia da história (editor → assets/story/) ─────────────────────
STORY_DIR = os.path.join(BASE_DIR, "assets", "story")
STORY_UPLOAD_MAX = 25 * 1024 * 1024            # 25 MB por arquivo
_STORY_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_STORY_AUDIO_EXT = {".mp3", ".ogg", ".wav", ".m4a"}
_STORY_OK_EXT = _STORY_IMG_EXT | _STORY_AUDIO_EXT

def _save_story_upload(name, data_b64):
    """Grava uma mídia de história em assets/story/. Sobrescreve se já existir.
    Retorna (ok: bool, basename_salvo | mensagem_de_erro)."""
    base = os.path.basename(name or "")        # bloqueia ../ e caminhos absolutos
    if not base:
        return False, "nome inválido"
    ext = os.path.splitext(base)[1].lower()
    if ext not in _STORY_OK_EXT:
        return False, "extensão não permitida"
    if not isinstance(data_b64, str) or not data_b64:
        return False, "dados inválidos"
    # rejeita cedo pelo tamanho aproximado do base64 (evita decodificar gigante)
    if (len(data_b64) * 3) // 4 > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        raw = base64.b64decode(data_b64, validate=True)
    except Exception:
        return False, "dados inválidos"
    if len(raw) > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        os.makedirs(STORY_DIR, exist_ok=True)
        with open(os.path.join(STORY_DIR, base), "wb") as f:
            f.write(raw)
    except OSError:
        return False, "falha ao gravar"
    return True, base

```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `python tools/test_story_upload.py`
Expected: PASS — todas as linhas `OK` e `TODOS OS TESTES PASSARAM`.

- [ ] **Step 6: Commit**

```bash
git add tools/test_story_upload.py server.py
git commit -m "feat(historia): _save_story_upload no servidor (grava midia em assets/story)"
```

---

## Task 2: Servidor — handler `upload_story` + `max_size` + MIME

**Files:**
- Modify: `server.py` (handler ~linha 12373; `serve()` ~linha 12707; MIME ~linha 12625)

- [ ] **Step 1: Adicionar o branch `upload_story` no handler**

Em `server.py`, dentro de `async def handler(ws)`, logo após `try:` (linha 12373) e **antes** de `if t == "create_room":` (linha 12374), inserir:

```python
                if t == "upload_story":
                    ok, res = _save_story_upload(msg.get("name"), msg.get("data"))
                    payload = {"type": "upload_result",
                               "upload_id": msg.get("upload_id"), "ok": ok}
                    if ok:
                        payload["name"] = res
                    else:
                        payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue

```

(O `continue` sai do loop sem tocar na lógica de sala; `upload_story` não precisa de room nem player.)

- [ ] **Step 2: Aumentar `max_size` no `serve()`**

Em `server.py`, na chamada `websockets.serve(...)` (linhas 12707-12708), trocar:

```python
    async with websockets.serve(handler, "0.0.0.0", 8765,
                                process_request=process_request):
```

por:

```python
    async with websockets.serve(handler, "0.0.0.0", 8765,
                                process_request=process_request,
                                max_size=34 * 1024 * 1024):
```

- [ ] **Step 3: Adicionar MIME types da história**

Em `server.py`, no laço de `mimetypes.add_type` (linhas 12625-12632), dentro da tupla, após a linha `(".webp", "image/webp"), (".ico", "image/x-icon"),` adicionar uma nova linha:

```python
    (".jpeg", "image/jpeg"), (".gif", "image/gif"),
    (".mp3", "audio/mpeg"), (".ogg", "audio/ogg"),
    (".wav", "audio/wav"), (".m4a", "audio/mp4"),
```

- [ ] **Step 4: Verificar que o servidor importa sem erro de sintaxe**

Run: `python -c "import server; print('import ok')"`
Expected: `import ok` (sem traceback).

- [ ] **Step 5: Re-rodar o teste do servidor (garante que nada quebrou)**

Run: `python tools/test_story_upload.py`
Expected: PASS — `TODOS OS TESTES PASSARAM`.

- [ ] **Step 6: Commit**

```bash
git add server.py
git commit -m "feat(historia): handler upload_story + max_size 34MB + MIME jpeg/gif/mp3/ogg/wav/m4a"
```

---

## Task 3: Editor — módulo cliente de upload (`tools/story_upload.js`)

**Files:**
- Create: `tools/story_upload.js`

- [ ] **Step 1: Criar `tools/story_upload.js`**

```javascript
"use strict";
// Cliente de upload de mídia da história. Abre uma WebSocket sob demanda com o
// servidor (ws://localhost:8765 — o editor roda como file://) e envia o arquivo
// em base64. window.STORY_UPLOAD.upload(file) -> Promise<basename> | rejeita.
(function () {
  const IMG = [".jpg", ".jpeg", ".png", ".webp", ".gif"];
  const AUD = [".mp3", ".ogg", ".wav", ".m4a"];
  const OK_EXT = IMG.concat(AUD);
  const MAX = 25 * 1024 * 1024;

  let ws = null;
  let nextId = 1;
  const pending = new Map();   // upload_id -> {resolve, reject}

  function serverUrl() { return "ws://localhost:8765"; }

  function connect() {
    return new Promise((resolve, reject) => {
      if (ws && ws.readyState === WebSocket.OPEN) { resolve(ws); return; }
      if (ws && ws.readyState === WebSocket.CONNECTING) {
        ws.addEventListener("open", () => resolve(ws), { once: true });
        ws.addEventListener("error",
          () => reject(new Error("não foi possível enviar — o servidor está rodando?")),
          { once: true });
        return;
      }
      ws = new WebSocket(serverUrl());
      ws.onopen = () => resolve(ws);
      ws.onerror = () =>
        reject(new Error("não foi possível enviar — o servidor está rodando?"));
      ws.onmessage = (ev) => {
        let m;
        try { m = JSON.parse(ev.data); } catch (e) { return; }
        if (m.type !== "upload_result") return;
        const p = pending.get(m.upload_id);
        if (!p) return;
        pending.delete(m.upload_id);
        if (m.ok) p.resolve(m.name);
        else p.reject(new Error(m.error || "falha no upload"));
      };
      ws.onclose = () => {
        for (const p of pending.values()) p.reject(new Error("conexão fechada"));
        pending.clear();
        ws = null;
      };
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
```

- [ ] **Step 2: Verificar sintaxe com node (se disponível)**

Run: `node --check tools/story_upload.js`
Expected: sem saída (sai 0). Se `node` não existir, pular — a verificação real é no Task 6.

- [ ] **Step 3: Commit**

```bash
git add tools/story_upload.js
git commit -m "feat(historia): modulo cliente de upload por WebSocket (story_upload.js)"
```

---

## Task 4: Editor — carregar `story_upload.js` no `editor.html`

**Files:**
- Modify: `tools/editor.html` (bloco de `<script>`, linhas 44-47)

- [ ] **Step 1: Adicionar o `<script>` antes de `editor_campaign.js`**

Em `tools/editor.html`, trocar:

```html
  <script src="editor_catalog.js"></script>
  <script src="editor_dungeons.js"></script>
  <script src="editor.js"></script>
  <script src="editor_campaign.js"></script>
```

por:

```html
  <script src="editor_catalog.js"></script>
  <script src="editor_dungeons.js"></script>
  <script src="editor.js"></script>
  <script src="story_upload.js"></script>
  <script src="editor_campaign.js"></script>
```

- [ ] **Step 2: Commit**

```bash
git add tools/editor.html
git commit -m "chore(historia): carregar story_upload.js no editor"
```

---

## Task 5: Editor — disparar upload nos handlers de imagem/áudio + status

**Files:**
- Modify: `tools/editor_campaign.js` (handler de áudio ~linhas 137-141; HTML do áudio ~linhas 119-124; handler de imagem ~linhas 168-172; HTML do card ~linhas 152-154)

- [ ] **Step 1: Disparar upload ao escolher o áudio**

Em `tools/editor_campaign.js`, trocar o handler (linhas 137-141):

```javascript
      ov.querySelector(".hist-audio-pick").onclick = () => pickFile("audio/*", f => {
        if (st._audioUrl) URL.revokeObjectURL(st._audioUrl);
        st._audioUrl = URL.createObjectURL(f); st._audioFile = f.name;
        st.audio = "assets/story/" + f.name; render();
      });
```

por:

```javascript
      ov.querySelector(".hist-audio-pick").onclick = () => pickFile("audio/*", f => {
        if (st._audioUrl) URL.revokeObjectURL(st._audioUrl);
        st._audioUrl = URL.createObjectURL(f); st._audioFile = f.name;
        st.audio = "assets/story/" + f.name;
        st._audioStatus = "enviando…"; render();
        window.STORY_UPLOAD.upload(f)
          .then(() => { st._audioStatus = "✓ enviado"; render(); })
          .catch(err => { st._audioStatus = "✗ " + err.message; render(); });
      });
```

- [ ] **Step 2: Mostrar o status do áudio no HTML**

Em `tools/editor_campaign.js`, no bloco do áudio (linhas 119-124), trocar:

```javascript
           <div class="hist-audio">
             🎵 áudio (loop)
             <button class="hist-audio-pick">${audioName ? "trocar" : "escolher"}</button>
             ${audioName ? `<span class="hist-audio-name">${audioName}</span><span class="hist-audio-x">✕</span>` : ""}
             <span class="hist-audio-hint">toca em loop durante a história</span>
           </div>
```

por:

```javascript
           <div class="hist-audio">
             🎵 áudio (loop)
             <button class="hist-audio-pick">${audioName ? "trocar" : "escolher"}</button>
             ${audioName ? `<span class="hist-audio-name">${audioName}</span><span class="hist-audio-x">✕</span>` : ""}
             ${st._audioStatus ? `<span class="hist-up-status">${st._audioStatus}</span>` : ""}
             <span class="hist-audio-hint">toca em loop durante a história</span>
           </div>
```

- [ ] **Step 3: Disparar upload ao escolher a imagem do slide**

Em `tools/editor_campaign.js`, trocar o handler (linhas 168-172):

```javascript
      card.querySelector(".hist-img-pick").onclick = () => pickFile("image/*", f => {
        if (s._url) URL.revokeObjectURL(s._url);
        s._url = URL.createObjectURL(f); s._imgFile = f.name;
        s.image = "assets/story/" + f.name; render();
      });
```

por:

```javascript
      card.querySelector(".hist-img-pick").onclick = () => pickFile("image/*", f => {
        if (s._url) URL.revokeObjectURL(s._url);
        s._url = URL.createObjectURL(f); s._imgFile = f.name;
        s.image = "assets/story/" + f.name;
        s._upStatus = "enviando…"; render();
        window.STORY_UPLOAD.upload(f)
          .then(() => { s._upStatus = "✓ enviado"; render(); })
          .catch(err => { s._upStatus = "✗ " + err.message; render(); });
      });
```

- [ ] **Step 4: Mostrar o status da imagem no card**

Em `tools/editor_campaign.js`, no `innerHTML` do card (linhas 152-154), trocar:

```javascript
        `<div class="hist-thumb">${(s._url || s.image)
            ? `<img src="${s._url || s.image}" alt="">` : `<span class="hist-noimg">sem imagem</span>`}
           <div class="hist-imgname">${imgName || ""}</div></div>
```

por:

```javascript
        `<div class="hist-thumb">${(s._url || s.image)
            ? `<img src="${s._url || s.image}" alt="">` : `<span class="hist-noimg">sem imagem</span>`}
           <div class="hist-imgname">${imgName || ""}</div>
           ${s._upStatus ? `<div class="hist-up-status">${s._upStatus}</div>` : ""}</div>
```

- [ ] **Step 5: Verificar sintaxe com node (se disponível)**

Run: `node --check tools/editor_campaign.js`
Expected: sem saída (sai 0). Se `node` não existir, pular — a verificação real é no Task 6.

- [ ] **Step 6: Commit**

```bash
git add tools/editor_campaign.js
git commit -m "feat(historia): editor envia imagem/audio ao escolher + status no card"
```

> Nota: os campos `_upStatus`/`_audioStatus` são runtime-only (prefixo `_`) e
> não entram no JSON — `storyToSaved` (linhas 20-35) só copia text/image/fit/audio,
> igual ao padrão já usado por `_url`/`_audioUrl`/`_imgFile`.

---

## Task 6: Verificação ponta a ponta (manual)

**Files:** nenhum (só execução).

- [ ] **Step 1: Subir o servidor**

Run: `python server.py` (deixar rodando) — ou `iniciar.bat`.
Expected: imprime `Local: http://localhost:8765/index.html` sem erro.

- [ ] **Step 2: Abrir o editor e montar uma história**

Abrir `tools/editor.html` no browser (duplo-clique = `file://`). Ir na aba de
campanha → abrir a história da abertura → escolher uma imagem pequena e um áudio.
Expected: aparece "✓ enviado" no card da imagem e no áudio (não "✗ ...").

- [ ] **Step 3: Confirmar os arquivos no disco**

Run: `ls assets/story/`
Expected: os arquivos escolhidos aparecem na pasta (além do `.gitkeep`).

- [ ] **Step 4: Confirmar que o servidor serve a mídia**

Run (substituir `<NOME>` pelo arquivo de imagem, com `%20` no lugar de espaços):
`curl -s -o /dev/null -w "%{http_code} %{content_type}\n" "http://localhost:8765/assets/story/<NOME>"`
Expected: `200 image/jpeg` (ou `image/png`). Repetir para o áudio → `200 audio/mpeg`.

- [ ] **Step 5: Salvar a campanha e rodá-la no jogo**

No editor: Salvar (baixa o JSON) → mover o `.json` para `campaigns/` (e o `.json`
da masmorra para `dungeons/` se aplicável). Abrir `http://localhost:8765/index.html`,
criar sala, selecionar a campanha e iniciar.
Expected: o slideshow de abertura mostra a imagem de fundo e toca o áudio em loop —
o bug original (mídia some no jogo) está resolvido.

- [ ] **Step 6: Teste de erro (servidor desligado)**

Parar o servidor. No editor, escolher outra imagem.
Expected: o card mostra "✗ não foi possível enviar — o servidor está rodando?"
e o editor continua funcionando (a pré-visualização via blob ainda mostra a imagem).

---

## Notas de execução

- Não há framework de testes JS; Tasks 3 e 5 dependem da verificação manual do Task 6.
- O `node --check` é só um lint de sintaxe opcional — se `node` não estiver
  instalado, pular esses passos.
- **NUNCA editar `game.js` via PowerShell** (memória do projeto). Aqui não tocamos
  em `game.js`, mas vale para qualquer ajuste futuro.
