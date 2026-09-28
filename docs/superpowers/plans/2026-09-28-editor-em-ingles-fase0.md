# Editor em inglês — Fase 0 (infraestrutura) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** O editor (`tools/editor.html`) passa a carregar o motor de idioma do jogo, ganha um seletor PT/EN que troca a moldura na hora e redesenha a aba ativa, e um placar que mede o que falta traduzir nos módulos do editor.

**Architecture:** Dicionário à mão em `src/lang/editor.js` (fundido em `LANG_STRINGS`, como `interface.js`). Cola do editor com o motor em `tools/editor_i18n.js` (`t`, `nomeCat`, aplicar `data-i18n`, persistir `lfh_lang`, `trocarIdioma` → `setTab(abaAtual)`). `editor.html` carrega os arquivos de idioma antes dos módulos e marca a moldura com `data-i18n`. Placar em `tools/test_editor_idioma.py`, reusando `tools/js_strings.py`.

**Tech Stack:** JavaScript vanilla (sem bundler), Python 3 para o placar, Node para o teste da cola.

**Spec:** `docs/superpowers/specs/2026-09-28-editor-em-ingles-design.md`

---

## Fatos do código que este plano assume (conferidos em 2026-09-28)

- `src/i18n.js` expõe `window.I18N = {t, tem, setLang, on, lang (getter), aplicarCatalogo, …}`. `DICT` é uma **referência** a `window.LANG_STRINGS` capturada no carregamento — os arquivos de idioma precisam vir **antes** do `i18n.js`, mas um `Object.assign` posterior no mesmo objeto também vale.
- `src/lang/strings.js` cria `window.LANG_STRINGS`; cada outro arquivo faz `window.LANG_<X> = {…}` + `Object.assign(window.LANG_STRINGS, window.LANG_<X>)`. O servidor (`_load_lang_arquivo`) acha a linha `^\s*window\.LANG_\w+\s*=` e faz `json.loads` do objeto — **JSON estrito dentro das chaves** (aspas duplas, sem vírgula sobrando, sem comentário dentro).
- O jogo guarda o idioma em `localStorage["lfh_lang"]`. O editor é servido pelo mesmo `server.py` em `http://localhost:8765/tools/editor.html` → mesma origem → mesma chave.
- Os módulos do editor são IIFEs: as funções de "topo" de cada módulo ficam com **2 espaços** de indentação (`^  function x(`), não na coluna 0 como no `game.js`.
- `tools/editor.js:3784` tem `function setTab(tab)`, exposto em `window.setTab` (linha ~3821). Ele redesenha a aba a partir do estado do módulo.
- `t` já é nome de variável local em vários módulos (ex.: `editor.js:849`, `editor_items_editor.js:295`, `editor_scenes.js:51`, `editor_story.js:169`). Com o `window.t` global novo, isso só importa quando o arquivo for migrado — o placar **relata** e só **cobra** nos arquivos fechados.
- `game.js`, `server.py`, `CLAUDE.md` estão em CRLF; `tools/editor.html` e os `tools/*.js` também podem estar — use a ferramenta Edit (não `replace` com `\n` em script).
- Servidor rodando na porta 8765 pode travar escrita de arquivo: se um Write falhar com `OSError: Errno 22`, pare o servidor e repita.

## Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/lang/editor.js` | criar | dicionário do editor (`ui.editor.*`) |
| `tools/editor_i18n.js` | criar | cola do editor com o motor |
| `tools/test_editor_i18n.js` | criar | teste node da cola |
| `tools/test_editor_idioma.py` | criar | placar + checagens do editor |
| `tools/editor.html` | modificar | carregar idioma, seletor, `data-i18n` na moldura |
| `tools/editor.js` | modificar | `setTab` guarda a aba atual |
| `CLAUDE.md` | modificar | registrar a Fase 0 |

---

### Task 1: Dicionário `src/lang/editor.js`

**Files:**
- Create: `src/lang/editor.js`
- Create: `tools/test_editor_idioma.py`

- [ ] **Step 1: Escrever o teste (seção [1]) que falha**

Criar `tools/test_editor_idioma.py`:

```python
"""Placar e checagens do EDITOR em PT/EN.

Roda da raiz:  python -X utf8 tools/test_editor_idioma.py

Seções:
  [1] dicionário src/lang/editor.js (carrega no servidor, tem en, paridade de {params})
  [2] editor.html: ordem dos scripts, seletor, moldura marcada com data-i18n
  [3] chaves ui.editor.* usadas nos tools/*.js e no editor.html existem
  [4] placar por arquivo/função (relata) + FECHADAS (cobra)
  [5] `t` sombreado: relata por arquivo, cobra nos FECHADOS
"""
import io, os, re, sys, collections
from html.parser import HTMLParser
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(RAIZ, "tools")
sys.path.insert(0, TOOLS)
sys.path.insert(0, RAIZ)
from js_strings import texto_de_interface, parece_portugues
import server as S   # funde todos os src/lang/*.js em S.LANG_STRINGS

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def ler(*partes):
    return io.open(os.path.join(RAIZ, *partes), encoding="utf-8").read()

PARAM = re.compile(r"\{(\w+)\}")
EDITOR_DICT = S._load_lang_arquivo(os.path.join(RAIZ, "src", "lang", "editor.js"))


def secao_dicionario():
    print("\n[1] Dicionário src/lang/editor.js")
    check("arquivo carrega e tem chaves", len(EDITOR_DICT) > 0)
    check("toda chave é ui.editor.*", all(k.startswith("ui.editor.") for k in EDITOR_DICT))
    check("o servidor fundiu o dicionário do editor",
          all(k in S.LANG_STRINGS for k in EDITOR_DICT))
    sem_en = [k for k, v in EDITOR_DICT.items() if not v.get("en")]
    check(f"toda chave tem en ({len(sem_en)} sem)", not sem_en)
    ruins = [k for k, v in EDITOR_DICT.items()
             if set(PARAM.findall(v.get("pt", ""))) != set(PARAM.findall(v.get("en", "")))]
    check(f"paridade de {{parâmetros}} pt×en ({ruins[:3]})", not ruins)


if __name__ == "__main__":
    secao_dicionario()
    print(f"\n  {PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -X utf8 tools/test_editor_idioma.py`
Expected: FAIL — `FileNotFoundError` (ou erro de import) porque `src/lang/editor.js` não existe.

- [ ] **Step 3: Criar `src/lang/editor.js`**

```js
// EDITOR (tools/editor.html e tools/*.js) — rótulos, botões e mensagens do editor.
//
// Separado do interface.js porque o editor é outra aplicação, carregada por outra
// página. Mantido À MÃO, como o interface.js/erros.js. Convenção de chave:
// ui.editor.<aba>.<slug>; a moldura (topo, abas, rodapé) usa ui.editor.topo.*.
// O servidor também funde este arquivo (_load_lang lê todo src/lang/*.js).
//
// REGRAS: JSON estrito DENTRO do objeto (aspas duplas, sem vírgula sobrando,
// sem comentário lá dentro). Parâmetros {nome}, iguais nos dois idiomas.
window.LANG_EDITOR = {
  "ui.editor.topo.titulo": {
    "en": "Dungeon Editor — Legends for Hire",
    "pt": "Editor de Masmorras — Legends for Hire"
  },
  "ui.editor.topo.idioma": {
    "en": "Language",
    "pt": "Idioma"
  },
  "ui.editor.topo.aba.masmorra": {
    "en": "Dungeon",
    "pt": "Masmorra"
  },
  "ui.editor.topo.aba.bestiario": {
    "en": "Bestiary",
    "pt": "Bestiário"
  },
  "ui.editor.topo.aba.editor_monstros": {
    "en": "Creature editor",
    "pt": "Editor de criaturas"
  },
  "ui.editor.topo.aba.editor_itens": {
    "en": "Item editor",
    "pt": "Editor de itens"
  },
  "ui.editor.topo.aba.cidade": {
    "en": "City",
    "pt": "Cidade"
  },
  "ui.editor.topo.aba.mapa_mundi": {
    "en": "World Map",
    "pt": "Mapa do Mundo"
  },
  "ui.editor.topo.aba.campanha": {
    "en": "Campaign",
    "pt": "Campanha"
  },
  "ui.editor.topo.aba.cenas": {
    "en": "Scenes",
    "pt": "Cenas"
  },
  "ui.editor.topo.nome": {
    "en": "name",
    "pt": "nome"
  },
  "ui.editor.topo.ambiente": {
    "en": "environment",
    "pt": "ambiente"
  },
  "ui.editor.topo.ambiente.masmorra": {
    "en": "Dungeon",
    "pt": "Masmorra"
  },
  "ui.editor.topo.ambiente.penumbra": {
    "en": "Dim (dark)",
    "pt": "Penumbra (escuro)"
  },
  "ui.editor.topo.ambiente.ar_livre": {
    "en": "Open air (bright)",
    "pt": "Ar livre (claro)"
  },
  "ui.editor.topo.saida_escada": {
    "en": "🚪 exit by the stairs",
    "pt": "🚪 saída pela escada"
  },
  "ui.editor.topo.saida_escada_dica": {
    "en": "If unchecked, heroes cannot leave the dungeon through the entrance stairs",
    "pt": "Se desmarcado, os heróis não podem deixar a masmorra pela escada de entrada"
  },
  "ui.editor.topo.aplicar_grid": {
    "en": "Apply grid",
    "pt": "Aplicar grid"
  },
  "ui.editor.topo.carregar": {
    "en": "Load",
    "pt": "Carregar"
  },
  "ui.editor.topo.salvar": {
    "en": "Save",
    "pt": "Salvar"
  },
  "ui.editor.topo.visualizar_3d": {
    "en": "◈ Preview in 3D",
    "pt": "◈ Visualizar em 3D"
  },
  "ui.editor.topo.visualizar_3d_dica": {
    "en": "Previews the current dungeon without saving",
    "pt": "Visualiza a masmorra atual sem salvar"
  },
  "ui.editor.topo.testar_mestre": {
    "en": "🧪 Test as Game Master",
    "pt": "🧪 Testar como Mestre"
  },
  "ui.editor.topo.testar_mestre_dica": {
    "en": "Opens a temporary session to test monsters and abilities",
    "pt": "Abre uma sessão temporária para testar monstros e habilidades"
  },
  "ui.editor.topo.painel_vazio": {
    "en": "Select a tool and draw.",
    "pt": "Selecione uma ferramenta e desenhe."
  },
  "ui.editor.topo.coordenadas_dica": {
    "en": "Square under the cursor: (x = column, y = row), counting from 0 at the top-left corner",
    "pt": "Casa sob o cursor: (x = coluna, y = linha), contando de 0 no canto superior esquerdo"
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_EDITOR);
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -X utf8 tools/test_editor_idioma.py`
Expected: `[1]` com 5 ✅ e `5 passaram, 0 falharam`.

- [ ] **Step 5: Garantir que as suítes de idioma do jogo seguem verdes**

Run: `python -X utf8 tools/test_idioma.py` e `python -X utf8 tools/dividas.py`
Expected: `test_idioma` sem ❌; `dividas.py` com "nada pendente".

- [ ] **Step 6: Commit**

```bash
git add src/lang/editor.js tools/test_editor_idioma.py
git commit -m "feat(editor-idioma): dicionário do editor (ui.editor.topo.*) e placar [1]"
```

---

### Task 2: A cola `tools/editor_i18n.js`

**Files:**
- Create: `tools/editor_i18n.js`
- Create: `tools/test_editor_i18n.js`

- [ ] **Step 1: Escrever o teste node que falha**

Criar `tools/test_editor_i18n.js`:

```js
// Cola do editor com o motor de idioma — roda da raiz: node tools/test_editor_i18n.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// ── Ambiente falso: window, localStorage e um DOM mínimo ──────────────────────
function elemento(attrs) {
  return { dataset: Object.assign({}, attrs), textContent: "", title: "", placeholder: "", value: "" };
}
const ELS = {
  titulo: elemento({ i18n: "ui.editor.topo.titulo" }),
  aba:    elemento({ i18n: "ui.editor.topo.aba.cidade" }),
  dica:   elemento({ i18nTitle: "ui.editor.topo.visualizar_3d_dica" }),
  seletor: elemento({}),
};
const loja = {};
global.window = {
  localStorage: {
    getItem: k => (k in loja ? loja[k] : null),
    setItem: (k, v) => { loja[k] = String(v); },
  },
};
global.document = {
  documentElement: { lang: "pt-BR" },
  querySelectorAll(sel) {
    if (sel === "[data-i18n]") return [ELS.titulo, ELS.aba];
    if (sel === "[data-i18n-title]") return [ELS.dica];
    return [];
  },
  getElementById(id) { return id === "ed-lang" ? ELS.seletor : null; },
};
loja["lfh_lang"] = "en";                       // o jogo já estava em inglês

for (const f of ["strings", "catalogo", "composto", "interface", "erros", "narracao", "editor"])
  eval(fs.readFileSync(path.join(raiz, "src", "lang", f + ".js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
let abaRedesenhada = null;
window.setTab = tab => { abaRedesenhada = tab; };
eval(fs.readFileSync(path.join(raiz, "tools", "editor_i18n.js"), "utf8"));

console.log("\n[1] Início: lê o idioma do jogo e aplica a moldura");
check("adota lfh_lang do jogo", window.I18N.lang === "en");
check("aplicou data-i18n", ELS.aba.textContent === "City");
check("aplicou data-i18n-title", ELS.dica.title === "Previews the current dungeon without saving");
check("seletor mostra o idioma atual", ELS.seletor.value === "en");
check("t global", typeof window.t === "function" && window.t("ui.editor.topo.aba.cidade") === "City");

console.log("\n[2] nomeCat");
check("traduz nome de catálogo pelo id",
      window.nomeCat("monstro", "goblin", "Goblin X") === window.I18N.t("cat.monstro.goblin.nome"));
check("sem chave devolve o padrão (conteúdo do autor)",
      window.nomeCat("monstro", "monstro_do_autor_xyz", "Meu Bicho") === "Meu Bicho");

console.log("\n[3] trocarIdioma");
window._abaAtualEditor = "cidade";
window.EDITOR_I18N.trocarIdioma("pt");
check("troca o idioma", window.I18N.lang === "pt");
check("grava lfh_lang", loja["lfh_lang"] === "pt");
check("reaplica a moldura", ELS.aba.textContent === "Cidade");
check("redesenha a aba ativa", abaRedesenhada === "cidade");
check("atualiza lang do documento", document.documentElement.lang === "pt-BR");
window.EDITOR_I18N.trocarIdioma("en");
check("volta ao inglês", ELS.aba.textContent === "City" && document.documentElement.lang === "en");
abaRedesenhada = null;
window.EDITOR_I18N.trocarIdioma("xx");
check("idioma inválido não muda nada nem redesenha", window.I18N.lang === "en" && abaRedesenhada === null);

console.log("\n[4] localStorage indisponível não derruba");
window.localStorage.getItem = () => { throw new Error("bloqueado"); };
window.localStorage.setItem = () => { throw new Error("bloqueado"); };
let ok = true;
try { window.EDITOR_I18N.trocarIdioma("pt"); } catch (e) { ok = false; }
check("trocarIdioma sobrevive a localStorage que lança", ok && window.I18N.lang === "pt");

console.log(`\n  ${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_i18n.js`
Expected: FAIL — `ENOENT` ao ler `tools/editor_i18n.js`.

- [ ] **Step 3: Criar `tools/editor_i18n.js`**

```js
"use strict";
// Cola do EDITOR com o motor de idioma (src/i18n.js). É o que o game.js faz para
// o jogo — t(), aplicar data-i18n, persistir a escolha —, em versão do editor.
//
// Carregado DEPOIS de src/lang/*.js e src/i18n.js e ANTES dos módulos do editor
// (tools/editor.html), por isso já roda no carregamento: o primeiro render dos
// módulos sai no idioma certo.
//
// • t(chave, params): global (window.t). Os módulos são IIFEs; um `t` local
//   (const t = …, (t) => …) SOMBREIA este — renomeie o local antes de migrar o
//   arquivo (o placar tools/test_editor_idioma.py [5] aponta onde há).
// • nomeCat(família, id, padrão): nome de catálogo traduzido pelo id; sem chave
//   (item/monstro criado pelo autor) devolve o padrão — o nome do autor.
// • Idioma em localStorage["lfh_lang"], a MESMA chave do jogo: o editor é
//   servido pelo mesmo servidor (/tools/editor.html), logo mesma origem.
// • trocarIdioma: reaplica a moldura (data-i18n) e redesenha a aba ativa por
//   setTab(abaAtual), que reconstrói a aba a partir do estado do módulo.
(function () {
  const CHAVE = "lfh_lang";
  const LANG_HTML = { pt: "pt-BR", en: "en" };

  function lerIdioma() {
    try { return window.localStorage.getItem(CHAVE) || window.I18N.PADRAO; }
    catch (e) { return window.I18N.PADRAO; }
  }
  function gravarIdioma(code) {
    try { window.localStorage.setItem(CHAVE, code); } catch (e) { /* aba privada */ }
  }

  function t(chave, params) { return window.I18N.t(chave, params); }

  function nomeCat(familia, id, padrao) {
    const k = "cat." + familia + "." + id + ".nome";
    return window.I18N.tem(k) ? window.I18N.t(k) : padrao;
  }

  // Só para elemento cujo conteúdo INTEIRO é o texto: textContent apaga filhos.
  // Rótulo com <input> dentro leva o texto num <span data-i18n>.
  function aplicar(raiz) {
    const alvo = raiz || document;
    alvo.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
    alvo.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = t(el.dataset.i18nTitle); });
    alvo.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  }

  function sincronizar() {
    const sel = document.getElementById("ed-lang");
    if (sel) sel.value = window.I18N.lang;
    document.documentElement.lang = LANG_HTML[window.I18N.lang] || window.I18N.lang;
  }

  function trocarIdioma(code) {
    if (window.I18N.SUPORTADOS.indexOf(code) < 0 || code === window.I18N.lang) return;
    window.I18N.setLang(code);
    gravarIdioma(code);
    aplicar(document);
    sincronizar();
    if (typeof window.setTab === "function" && window._abaAtualEditor)
      window.setTab(window._abaAtualEditor);
  }

  function iniciar() {
    window.I18N.setLang(lerIdioma());
    aplicar(document);
    sincronizar();
    const sel = document.getElementById("ed-lang");
    if (sel) sel.onchange = () => trocarIdioma(sel.value);
  }

  window.t = t;
  window.nomeCat = nomeCat;
  window.EDITOR_I18N = { t, nomeCat, aplicar, trocarIdioma, iniciar };
  iniciar();
})();
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_editor_i18n.js`
Expected: `15 passaram, 0 falharam`.

Se `nomeCat("monstro", "goblin", …)` falhar, conferir o id real de um monstro com chave: `node -e "global.window={};require('./src/lang/strings.js');require('./src/lang/catalogo.js');console.log(Object.keys(window.LANG_STRINGS).filter(k=>k.startsWith('cat.monstro.')).slice(0,3))"` e trocar `goblin` por um id listado.

- [ ] **Step 5: Commit**

```bash
git add tools/editor_i18n.js tools/test_editor_i18n.js
git commit -m "feat(editor-idioma): cola editor_i18n.js (t, nomeCat, trocarIdioma) + teste node"
```

---

### Task 3: `setTab` guarda a aba atual

**Files:**
- Modify: `tools/editor.js:3784` (início de `setTab`) e `:3821` (`window.setTab = setTab;`)
- Test: `tools/test_editor_idioma.py` (seção [2], parte 1)

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_idioma.py`, acrescentar antes do `if __name__`:

```python
def secao_editor_js():
    print("\n[2a] editor.js lembra a aba atual para o redesenho")
    src = ler("tools", "editor.js")
    i = src.index("function setTab(tab) {")
    corpo = src[i:i + 200]
    check("setTab grava window._abaAtualEditor logo no início",
          "window._abaAtualEditor = tab;" in corpo)
    check("aba inicial registrada junto do window.setTab",
          re.search(r"window\.setTab = setTab;\s*\n\s*window\._abaAtualEditor = window\._abaAtualEditor \|\| \"masmorra\";",
                    src) is not None)
```

E no bloco `__main__`, chamar `secao_editor_js()` depois de `secao_dicionario()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -X utf8 tools/test_editor_idioma.py`
Expected: os 2 checks de `[2a]` com ❌.

- [ ] **Step 3: Editar `tools/editor.js`**

Trocar

```js
  function setTab(tab) {
    const dung = tab === "masmorra";
```

por

```js
  function setTab(tab) {
    window._abaAtualEditor = tab;   // trocarIdioma (editor_i18n.js) redesenha esta aba
    const dung = tab === "masmorra";
```

E trocar

```js
  window.setTab = setTab;
```

por

```js
  window.setTab = setTab;
  window._abaAtualEditor = window._abaAtualEditor || "masmorra";
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -X utf8 tools/test_editor_idioma.py` → `[2a]` verde. E `node --check tools/editor.js` sem saída.

- [ ] **Step 5: Commit**

```bash
git add tools/editor.js tools/test_editor_idioma.py
git commit -m "feat(editor-idioma): setTab guarda a aba atual para o redesenho"
```

---

### Task 4: `editor.html` — carregar o idioma, seletor e moldura marcada

**Files:**
- Modify: `tools/editor.html`
- Test: `tools/test_editor_idioma.py` (seções [2b] e [3])

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_idioma.py`, acrescentar antes do `if __name__`:

```python
# Texto que fica sempre na própria língua (as opções do seletor de idioma).
HTML_INTENCIONAIS = {"Português", "English"}


class _Moldura(HTMLParser):
    """Texto e atributos de interface do editor.html que ficaram SEM marcador."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []          # [(tag, attrs)]
        self.sem_marca = []      # textos pt sem data-i18n no elemento pai
        self.attr_sem_marca = [] # title/placeholder pt sem data-i18n-title/-ph
        self.chaves = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("data-i18n", "data-i18n-title", "data-i18n-ph"):
            if a.get(k): self.chaves.add(a[k])
        for attr, marca in (("title", "data-i18n-title"), ("placeholder", "data-i18n-ph")):
            v = (a.get(attr) or "").strip()
            if v and parece_portugues(v) and not a.get(marca):
                self.attr_sem_marca.append(f"<{tag} {attr}={v!r}>")
        if tag not in ("input", "meta", "link", "br", "img"):
            self.pilha.append((tag, a))
    def handle_endtag(self, tag):
        while self.pilha:
            t_, _ = self.pilha.pop()
            if t_ == tag: break
    def handle_data(self, data):
        txt = data.strip()
        if not txt or not self.pilha: return
        tag, a = self.pilha[-1]
        if tag in ("script", "style"): return
        if txt in HTML_INTENCIONAIS: return
        if parece_portugues(txt) and not a.get("data-i18n"):
            self.sem_marca.append(txt)


def secao_html():
    print("\n[2b] editor.html: scripts, seletor e moldura")
    html = ler("tools", "editor.html")
    ordem = ["../src/lang/strings.js", "../src/lang/catalogo.js", "../src/lang/composto.js",
             "../src/lang/interface.js", "../src/lang/editor.js", "../src/i18n.js",
             "editor_i18n.js", "editor.js"]
    pos = [html.find('"' + s + '"') for s in ordem]
    check("carrega idioma → motor → cola → módulos, nessa ordem",
          all(p >= 0 for p in pos) and pos == sorted(pos))
    check("seletor de idioma #ed-lang com pt e en",
          re.search(r'<select id="ed-lang"[^>]*>\s*<option value="pt">Português</option>\s*'
                    r'<option value="en">English</option>\s*</select>', html) is not None)
    p = _Moldura(); p.feed(html)
    check(f"nenhum texto da moldura sem data-i18n ({p.sem_marca[:4]})", not p.sem_marca)
    check(f"nenhum title/placeholder sem marcador ({p.attr_sem_marca[:3]})", not p.attr_sem_marca)
    faltam = sorted(k for k in p.chaves if k not in S.LANG_STRINGS)
    check(f"toda chave data-i18n do editor.html existe ({faltam[:4]})", not faltam)
```

E no `__main__`, chamar `secao_html()` depois de `secao_editor_js()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -X utf8 tools/test_editor_idioma.py`
Expected: `[2b]` com ❌ na ordem dos scripts, no seletor e nos textos sem marcador.

- [ ] **Step 3: Editar `tools/editor.html`**

Substituir o `<title>` por:

```html
<title data-i18n="ui.editor.topo.titulo">Editor de Masmorras — Legends for Hire</title>
```

Substituir o bloco `<span id="tabs"> … </span>` por:

```html
    <span id="tabs">
      <button id="tab-masmorra" class="tab active" data-i18n="ui.editor.topo.aba.masmorra">Masmorra</button>
      <button id="tab-bestiario" class="tab" data-i18n="ui.editor.topo.aba.bestiario">Bestiário</button>
      <button id="tab-editor-monstros" class="tab" data-i18n="ui.editor.topo.aba.editor_monstros">Editor de criaturas</button>
      <button id="tab-editor-itens" class="tab" data-i18n="ui.editor.topo.aba.editor_itens">Editor de itens</button>
      <button id="tab-cidade" class="tab" data-i18n="ui.editor.topo.aba.cidade">Cidade</button>
      <button id="tab-mapa-mundi" class="tab" data-i18n="ui.editor.topo.aba.mapa_mundi">Mapa do Mundo</button>
      <button id="tab-campanha" class="tab" data-i18n="ui.editor.topo.aba.campanha">Campanha</button>
      <button id="tab-cenas" class="tab" data-i18n="ui.editor.topo.aba.cenas">Cenas</button>
    </span>
```

Substituir o bloco `<span id="dungeon-controls"> … </span>` por (o texto de cada `<label>` que contém um campo vai num `<span data-i18n>`, senão o `textContent` apagaria o campo):

```html
    <span id="dungeon-controls">
      <label>id <input id="m-id" value="nova_masmorra" size="12"></label>
      <label><span data-i18n="ui.editor.topo.nome">nome</span> <input id="m-name" value="Nova Masmorra" size="14"></label>
      <label><span data-i18n="ui.editor.topo.ambiente">ambiente</span>
        <select id="m-ambiente">
          <option value="masmorra" data-i18n="ui.editor.topo.ambiente.masmorra">Masmorra</option>
          <option value="penumbra" data-i18n="ui.editor.topo.ambiente.penumbra">Penumbra (escuro)</option>
          <option value="ar_livre" data-i18n="ui.editor.topo.ambiente.ar_livre">Ar livre (claro)</option>
        </select>
      </label>
      <label title="Se desmarcado, os heróis não podem deixar a masmorra pela escada de entrada" data-i18n-title="ui.editor.topo.saida_escada_dica">
        <input type="checkbox" id="m-saida" checked> <span data-i18n="ui.editor.topo.saida_escada">🚪 saída pela escada</span>
      </label>
      <label>grid
        <input id="g-w" type="number" min="1" max="60" value="16" style="width:46px">×
        <input id="g-h" type="number" min="1" max="60" value="12" style="width:46px">
      </label>
      <button id="btn-resize" data-i18n="ui.editor.topo.aplicar_grid">Aplicar grid</button>
      <button id="btn-load" data-i18n="ui.editor.topo.carregar">Carregar</button>
      <input id="file-input" type="file" accept="application/json,.json" hidden>
      <button id="btn-save" data-i18n="ui.editor.topo.salvar">Salvar</button>
      <button id="btn-preview-3d" title="Visualiza a masmorra atual sem salvar" data-i18n="ui.editor.topo.visualizar_3d" data-i18n-title="ui.editor.topo.visualizar_3d_dica">◈ Visualizar em 3D</button>
      <button id="btn-test-dungeon" title="Abre uma sessão temporária para testar monstros e habilidades" data-i18n="ui.editor.topo.testar_mestre" data-i18n-title="ui.editor.topo.testar_mestre_dica">🧪 Testar como Mestre</button>
    </span>
    <span id="campaign-controls" style="display:none"></span>
    <label id="ed-lang-wrap" title="Idioma" data-i18n-title="ui.editor.topo.idioma">🌐
      <select id="ed-lang">
        <option value="pt">Português</option>
        <option value="en">English</option>
      </select>
    </label>
```

(o `<span id="campaign-controls" …></span>` original é substituído pela mesma linha acima — não duplicar.)

Substituir o painel vazio:

```html
    <aside id="panel"><em data-i18n="ui.editor.topo.painel_vazio">Selecione uma ferramenta e desenhe.</em></aside>
```

Substituir o rodapé:

```html
  <footer id="statusbar"><span id="cursor-coords" title="Casa sob o cursor: (x = coluna, y = linha), contando de 0 no canto superior esquerdo" data-i18n-title="ui.editor.topo.coordenadas_dica"></span><span id="status"></span></footer>
```

Substituir a lista de scripts do cache-buster (a linha com `var s=[…]`) por:

```html
  <script>(function(){var v=Date.now();var s=["../src/lang/strings.js","../src/lang/catalogo.js","../src/lang/composto.js","../src/lang/interface.js","../src/lang/editor.js","../src/i18n.js","editor_i18n.js","../src/difficulty.js","editor_items_logic.js","editor_items_custom.js","editor_catalog.js","editor_monsters_custom.js","editor_dungeons.js","editor.js","editor_preview_3d.js","editor_bestiary.js","editor_monster_editor.js","story_upload.js","editor_story.js","editor_campaign.js","editor_items_editor.js","editor_city.js","editor_world.js","editor_scenes.js"];for(var i=0;i<s.length;i++)document.write('<script src="'+s[i]+'?v='+v+'"><\/script>');})();</script>
```

Em `tools/editor.css`, acrescentar ao fim (empurra o seletor para a direita da barra):

```css
#ed-lang-wrap { margin-left: auto; white-space: nowrap; }
```

- [ ] **Step 4: Acrescentar a seção [3] (chaves usadas nos .js existem) e rodar**

Em `tools/test_editor_idioma.py`, antes do `if __name__`:

```python
# Arquivos do editor medidos pelo placar. Gerados e testes ficam de fora.
MODULOS = ["editor.js", "editor_monster_editor.js", "editor_items_editor.js",
           "editor_items_logic.js", "editor_city.js", "editor_world.js",
           "editor_bestiary.js", "editor_scenes.js", "editor_campaign.js",
           "story_upload.js", "editor_preview_3d.js", "editor_story.js"]
RE_CHAVE_USADA = re.compile(r"""\bt\(\s*['"`](ui\.editor\.[\w.]+)['"`]""")


def secao_chaves_usadas():
    print("\n[3] Chaves ui.editor.* usadas nos módulos existem")
    usadas = set()
    for f in MODULOS + ["editor_i18n.js"]:
        usadas |= set(RE_CHAVE_USADA.findall(ler("tools", f)))
    faltam = sorted(k for k in usadas if not k.endswith(".") and k not in S.LANG_STRINGS)
    check(f"toda chave usada existe ({len(usadas)} usadas; faltam {faltam[:4]})", not faltam)
```

E chamar `secao_chaves_usadas()` no `__main__` depois de `secao_html()`.

Run: `python -X utf8 tools/test_editor_idioma.py`
Expected: `[1]`, `[2a]`, `[2b]`, `[3]` todos verdes.

- [ ] **Step 5: Commit**

```bash
git add tools/editor.html tools/editor.css tools/test_editor_idioma.py
git commit -m "feat(editor-idioma): editor.html carrega o idioma, seletor PT/EN e moldura marcada"
```

---

### Task 5: Placar por arquivo/função e `t` sombreado

**Files:**
- Modify: `tools/test_editor_idioma.py` (seções [4] e [5])

- [ ] **Step 1: Escrever as seções**

Em `tools/test_editor_idioma.py`, antes do `if __name__`:

```python
# Funções de "topo" dos módulos do editor: os módulos são IIFEs, então o topo
# fica a 2 espaços (`  function x(` / `  const x = (…) =>`). Arquivos sem IIFE
# (story_upload.js, editor_story.js) têm topo na coluna 0 — o 2º ramo cobre.
RE_FN_ED = re.compile(
    r"^(?:  )?(?:async\s+)?function\s+(\w+)"
    r"|^(?:  )?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:function\b|\(?[\w,\s]*\)?\s*=>)")

# Arquivos (ou "arquivo:função") já traduzidos: o placar COBRA zero neles. Cada
# fase acrescenta os seus ao fechar. Fase 0 não fecha módulo nenhum — a moldura
# (editor.html) é cobrada pela seção [2b].
FECHADAS = set()

# Um `t` local SOMBREIA o window.t global dentro do módulo (IIFE): t('chave') ali
# vira TypeError em runtime. Renomeie o local antes de migrar o arquivo.
RE_T_SOMBREADO = re.compile(
    r"\b(?:const|let|var)\s+t\s*[=,;]"      # const t = …
    r"|\(\s*t\s*[,)]"                       # (t) => / function (t, …)
    r"|(?<![\w$.])t\s*=>")                  # t => …


def _pendentes_por_funcao(arquivo):
    src = ler("tools", arquivo)
    dono, atual = {}, "@topo"
    for i, l in enumerate(src.split("\n")):
        m = RE_FN_ED.match(l)
        if m: atual = m.group(1) or m.group(2)
        dono[i + 1] = atual
    cont = collections.Counter()
    for linha, _txt in texto_de_interface(src):
        cont[dono.get(linha, "@topo")] += 1
    return cont


def secao_placar():
    print("\n[4] Placar: textos em português restantes nos módulos do editor")
    total = 0
    por_arquivo = {}
    for f in MODULOS:
        c = _pendentes_por_funcao(f)
        por_arquivo[f] = c
        total += sum(c.values())
    for f, c in sorted(por_arquivo.items(), key=lambda x: -sum(x[1].values())):
        n = sum(c.values())
        if n:
            print(f"     {n:4d}  {f}" + ("  (FECHADO)" if f in FECHADAS else ""))
    print(f"     total: {total}")
    regrediu = []
    for alvo in FECHADAS:
        f, _, fn = alvo.partition(":")
        c = por_arquivo.get(f, collections.Counter())
        n = c.get(fn, 0) if fn else sum(c.values())
        if n: regrediu.append(f"{alvo} ({n})")
    check(f"nenhum arquivo/função fechado regrediu ({len(FECHADAS)} fechados; {regrediu[:4]})",
          not regrediu)


def secao_sombreado():
    print("\n[5] `t` local que sombreia o t() global")
    achados = {}
    for f in MODULOS:
        linhas = [i + 1 for i, l in enumerate(ler("tools", f).split("\n"))
                  if RE_T_SOMBREADO.search(l)]
        if linhas: achados[f] = linhas
    for f, ls in sorted(achados.items()):
        print(f"     {f}: linhas {ls[:8]}{' …' if len(ls) > 8 else ''}")
    fechados_com_t = [f for f in achados if f in {a.partition(':')[0] for a in FECHADAS}]
    check(f"nenhum arquivo fechado tem `t` sombreado ({fechados_com_t})", not fechados_com_t)
```

E chamar `secao_placar()` e `secao_sombreado()` no `__main__` depois de `secao_chaves_usadas()`.

- [ ] **Step 2: Rodar**

Run: `python -X utf8 tools/test_editor_idioma.py`
Expected: todas as seções verdes. `[4]` imprime o placar por arquivo com um total perto de **1.200** (a medição do spec); `[5]` lista os `t` locais de `editor.js`, `editor_items_editor.js`, `editor_scenes.js`, `editor_story.js`, entre outros.

- [ ] **Step 3: Conferir que o placar enxerga texto de verdade (teste negativo)**

Criar temporariamente uma linha com texto em português num módulo e ver o placar subir, depois desfazer:

```bash
cp tools/editor_story.js tools/editor_story.js.sonda.bak
printf '\nconst _sonda = "Texto de teste em português";\n' >> tools/editor_story.js
python -X utf8 tools/test_editor_idioma.py | grep "editor_story.js"
cp tools/editor_story.js.sonda.bak tools/editor_story.js
rm tools/editor_story.js.sonda.bak
```

Expected: a linha de `editor_story.js` no placar mostra 1 a mais do que sem a sonda. Depois de restaurar, `git diff --stat tools/editor_story.js` sem mudanças.

- [ ] **Step 4: Commit**

```bash
git add tools/test_editor_idioma.py
git commit -m "test(editor-idioma): placar por arquivo/função e varredura de t sombreado"
```

---

### Task 6: Conferência no navegador e registro no CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (acrescentar um bloco ao fim)

- [ ] **Step 1: Abrir o editor pelo servidor, em inglês**

Com o servidor do jogo rodando (`python server.py`, ou o que já estiver na 8765), abrir `http://localhost:8765/tools/editor.html?v=fase0` e, no console do navegador:

```js
[typeof window.t, window.I18N.lang, document.title,
 document.getElementById('tab-cidade').textContent,
 document.getElementById('ed-lang').value]
```

Depois trocar pelo seletor 🌐 para English e repetir. Expected em EN: `['function','en','Dungeon Editor — Legends for Hire','City','en']`. Nenhum erro no console.

- [ ] **Step 2: Rascunho sobrevive à troca de idioma**

Na aba Masmorra, mudar o campo "nome" para `Teste idioma` e desenhar uma parede; trocar EN→PT→EN pelo seletor. Expected: o nome continua `Teste idioma`, a parede continua no mapa, os rótulos da moldura mudam de língua, console sem erro.

Na aba Editor de itens (ou Cidade), trocar o idioma e confirmar que a aba é redesenhada (continua visível, sem erro).

- [ ] **Step 3: O jogo e o editor compartilham o idioma**

Abrir `http://localhost:8765/index.html?v=fase0` na mesma aba de navegador depois de deixar o editor em English. Expected: o jogo abre em inglês (mesmo `lfh_lang`).

- [ ] **Step 4: Rodar todas as checagens de idioma**

```bash
python -X utf8 tools/test_editor_idioma.py
node tools/test_editor_i18n.js
python -X utf8 tools/test_idioma.py
node tools/test_idioma_cliente.js
python -X utf8 tools/dividas.py
```

Expected: tudo verde; `dividas.py` "nada pendente".

- [ ] **Step 5: Registrar no CLAUDE.md**

Acrescentar ao fim do `CLAUDE.md`:

```markdown
> **Editor em inglês — Fase 0 (infraestrutura, 2026-09-28):** o editor (`tools/editor.html`)
> carrega o motor de idioma do jogo (`src/lang/*.js` + `src/i18n.js`) e a cola
> **`tools/editor_i18n.js`**: `t()` global, `nomeCat(família, id, padrão)` (nome de catálogo
> pelo id; sem chave → nome do autor), `data-i18n`/`-title`/`-ph` na moldura, idioma em
> `localStorage["lfh_lang"]` (a MESMA chave do jogo — mesma origem) e `trocarIdioma`, que
> reaplica a moldura e chama `setTab(window._abaAtualEditor)` para redesenhar a aba ativa a
> partir do estado. Seletor 🌐 `#ed-lang` na barra. Dicionário à mão **`src/lang/editor.js`**
> (`ui.editor.<aba>.<slug>`; moldura em `ui.editor.topo.*`). Rótulo com campo dentro leva o
> texto num `<span data-i18n>`. **Placar:** `tools/test_editor_idioma.py` ([4] por
> arquivo/função, com `FECHADAS` cobradas; [5] `t` local que sombreia o global — renomeie
> antes de migrar o arquivo). Cola testada em `tools/test_editor_i18n.js`. Próximas fases, uma
> aba por vez: Masmorra → Criaturas → Itens → Cidade → pequenas; por último as mensagens do
> servidor ao editor. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-09-28-editor-em-ingles*`.
```

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: registra a Fase 0 do editor em inglês"
```

---

## Notas para as fases seguintes (não fazem parte desta)

- A aba Masmorra monta a barra de ferramentas uma vez (`buildToolbar()` em `editor.js`); o `setTab("masmorra")` não a remonta. A Fase 1 precisa fazer o `trocarIdioma` (ou o `setTab`) chamar `buildToolbar()` também, senão a barra fica no idioma antigo.
- Ao fechar uma aba, acrescentar o arquivo em `FECHADAS` no `tools/test_editor_idioma.py`.
