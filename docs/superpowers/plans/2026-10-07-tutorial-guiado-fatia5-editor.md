# Tutorial guiado — fatia 5 (passos da lição no editor de masmorras) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deixar o autor criar, editar, reordenar e validar os passos guiados (`guia`) de uma lição direto no painel de fala do editor de masmorras — e, antes disso, **parar de apagar o `guia` ao salvar** uma masmorra pelo editor.

**Architecture:** Toda a lógica de passos (carregar, serializar, montar `ui`, validar) vive num módulo puro novo, `tools/editor_guia_logic.js` (`window.EDITOR_GUIA`), testável em node e sincronizado por teste com as constantes do servidor. O `tools/editor.js` só chama esse módulo: no `loadJSON`, no `buildJSON`, na validação e no painel da fala. Texto de passo digitado pelo autor é texto livre em português; passo que já vem do dicionário (`ui.tutorial.*`, gerado pelas fatias 3–4) aparece como somente leitura.

**Tech Stack:** JS puro (sem bundler), `tools/editor.html`/`editor.js`, `src/lang/editor.js` (chaves `ui.editor.*`), Python `unittest` + node para os testes.

Spec: `docs/superpowers/specs/2026-10-07-tutorial-guiado-design.md` (seção 5, fatia 5). Fatias 1–4 já estão em `master`.

## Por que o conserto vem primeiro (perda de dados real)

`buildJSON` (`tools/editor.js`, bloco `falas: S.falas.map(...)`) e `loadJSON` (bloco `S.falas = (obj.falas || []).map(...)`) copiam campo a campo e **não conhecem `guia`**. Hoje, abrir `dungeons/campo_de_treinamento.json` no editor e salvar apaga o guia das 62 lições. A Task 2 fecha isso antes de qualquer UI.

## ATENÇÃO — alterações do autor em `tools/editor.js`

O working copy tem **252 linhas não commitadas do autor** em `tools/editor.js` (um único bloco inserido perto da linha 51; `git diff -U0` mostra `@@ -50,0 +51,252 @@`). **Nunca** use `git add tools/editor.js` nem `git commit -a`: isso leva o trabalho dele. Cada commit que tocar o `editor.js` usa o script da seção "Commit só dos meus trechos" abaixo. O restante dos arquivos deste plano (`editor.html`, `src/lang/editor.js`, os testes e o módulo novo) pode ir por caminho explícito, **depois de conferir `git diff --stat <arquivo>`** (se aparecer mudança que não é sua, pare e avise).

### Commit só dos meus trechos (para `tools/editor.js`)

Salve como `%TEMP%\commit_meus_trechos.py` (fora do repositório) e rode da raiz depois de editar:

```python
"""Aplica ao índice só os trechos do `git diff` que NÃO são o bloco do autor
(`@@ -50,0 +51,252 @@`) e deixa o working copy intacto."""
import re, subprocess, sys

ARQ = "tools/editor.js"
BLOCO_AUTOR = re.compile(r"^@@ -50,0 \+51,252 @@")

diff = subprocess.run(["git", "diff", "-U0", "--", ARQ], capture_output=True, text=True,
                      encoding="utf-8", check=True).stdout
cab, *hunks = re.split(r"(?m)^(?=@@ )", diff)
meus = [h for h in hunks if not BLOCO_AUTOR.match(h)]
if len(meus) == len(hunks):
    sys.exit("o bloco do autor não apareceu no diff: confira `git diff -U0 tools/editor.js` antes de commitar")
if not meus:
    sys.exit("nenhum trecho meu no diff")
patch = cab + "".join(meus)
r = subprocess.run(["git", "apply", "--cached", "--unidiff-zero", "-"], input=patch, text=True,
                   encoding="utf-8", capture_output=True)
print(r.stdout, r.stderr)
sys.exit(r.returncode)
```

Depois: `git diff --cached --stat -- tools/editor.js` (só as suas linhas) e `git commit -m "..."` com o caminho **não** listado (o índice já está pronto). Se o autor tiver commitado o bloco dele antes, o script avisa e você usa `git add tools/editor.js` normalmente.

## Formato do guia (referência — já vigente no servidor)

`guia` = lista de 1 a 8 passos `{id?, texto, porque?, ui?, dica?[≤2], conclui_com?{tipo, alvo?}}`. `ui` casa com `GUIA_UI_RE` (`botao|habilidade|bolsa|slot|monstro|hud:<id>` ou `casa|porta:[x,y]`). `conclui_com.tipo` ∈ `LICAO_VERBOS`. O servidor valida em `validar_dungeon`. O último passo nunca avança sozinho (quem encerra é a tarefa).

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `tools/editor_guia_logic.js` | criar | `window.EDITOR_GUIA`: `carregar`, `serializar`, `lerUi`, `montarUi`, `validar`, `ehChave` |
| `tools/test_editor_guia_logic.js` | criar | testes do módulo + roundtrip com as 62 lições reais |
| `tools/test_editor_guia.py` | criar | sincronia com o servidor + fiação estática no `editor.js`/`editor.html` |
| `tools/editor.html` | modificar | carrega `editor_guia_logic.js` antes de `editor.js` |
| `tools/editor.js` | modificar | `loadJSON`/`buildJSON`, validação, painel de passos |
| `src/lang/editor.js` | modificar | chaves `ui.editor.masmorra.guia.*` e `ui.editor.masmorra.valid.guia_*` (pt + en) |
| `CLAUDE.md` | modificar | parágrafo da fatia 5 |

---

### Task 1: Módulo puro `editor_guia_logic.js` + testes

**Files:**
- Create: `tools/editor_guia_logic.js`
- Create: `tools/test_editor_guia_logic.js`
- Create: `tools/test_editor_guia.py` (só a parte de sincronia nesta task)

- [ ] **Step 1: Escrever o teste node que falha**

`tools/test_editor_guia_logic.js` (siga o estilo de `tools/test_editor_items_logic.js`: `PASS/FAIL`, `check(nome, cond)`, `require` do módulo via `vm`/`global.window = {}`; abra aquele arquivo e copie o cabeçalho que ele usa para carregar `editor_items_logic.js`):

```javascript
// Testes do módulo puro tools/editor_guia_logic.js (passos de lição no editor).
const fs = require("fs"), path = require("path");
const raiz = path.join(__dirname, "..");
global.window = {};
eval(fs.readFileSync(path.join(__dirname, "editor_guia_logic.js"), "utf8"));
const G = window.EDITOR_GUIA;
let PASS = 0, FAIL = 0;
function check(nome, cond) { if (cond) { PASS++; console.log("  ✅ " + nome); } else { FAIL++; console.log("  ❌ " + nome); } }

console.log("[1] ehChave / lerUi / montarUi");
check("chave de dicionário é reconhecida", G.ehChave("ui.tutorial.guia.fala_0.ver.texto") === true);
check("texto livre não é chave", G.ehChave("Clique no boneco.") === false);
check("lerUi botao", JSON.stringify(G.lerUi("botao:encerrar_turno")) === '{"tipo":"botao","valor":"encerrar_turno"}');
check("lerUi casa", JSON.stringify(G.lerUi("casa:[5,15]")) === '{"tipo":"casa","valor":"5,15"}');
check("lerUi vazio", JSON.stringify(G.lerUi(null)) === '{"tipo":"","valor":""}');
check("montarUi id", G.montarUi("habilidade", " mira_certeira ") === "habilidade:mira_certeira");
check("montarUi casa", G.montarUi("casa", "5, 15") === "casa:[5,15]");
check("montarUi porta", G.montarUi("porta", "13,15") === "porta:[13,15]");
check("montarUi tipo vazio = null", G.montarUi("", "x") === null);
check("montarUi valor vazio = null", G.montarUi("botao", "") === null);

console.log("[2] carregar / serializar");
const g0 = [{ id: "a", texto: "Passo um.", porque: "Porque sim.", ui: "botao:inventario", dica: ["d1", "d2"], conclui_com: { tipo: "pegar_item" } },
            { id: "b", texto: "Passo dois." }];
const c = G.carregar(g0);
check("carregar devolve 2 passos", c.length === 2);
check("carregar normaliza campos ausentes", c[1].porque === "" && c[1].ui === null && Array.isArray(c[1].dica) && c[1].dica.length === 0 && c[1].conclui_com === null);
check("serializar(carregar(x)) == x", JSON.stringify(G.serializar(c)) === JSON.stringify(g0));
check("carregar não aceita lixo", JSON.stringify(G.carregar("x")) === "[]" && JSON.stringify(G.carregar(null)) === "[]");
check("serializar descarta vazios", JSON.stringify(G.serializar([{ texto: "A", porque: "", ui: null, dica: ["", "x"], conclui_com: null }])) === '[{"texto":"A","dica":["x"]}]');
check("serializar de lista vazia = null", G.serializar([]) === null);
check("carregar clona (não alias)", (() => { const x = G.carregar(g0); x[0].texto = "Z"; return g0[0].texto === "Passo um."; })());

console.log("[3] validar");
const ok = (g) => G.validar(g).length === 0;
check("válido", ok([{ texto: "A", ui: "botao:encerrar_turno" }]));
check("mais de 8 passos", G.validar(Array.from({ length: 9 }, () => ({ texto: "x" }))).some(e => e.codigo === "guia_muitos"));
check("passo sem texto", G.validar([{ texto: "  " }]).some(e => e.codigo === "guia_sem_texto" && e.params.n === 1));
check("ui inválida", G.validar([{ texto: "A", ui: "botao:Maiúscula" }]).some(e => e.codigo === "guia_ui_invalida"));
check("mais de 2 dicas", G.validar([{ texto: "A", dica: ["1", "2", "3"] }]).some(e => e.codigo === "guia_dicas"));
check("conclui_com de verbo desconhecido", G.validar([{ texto: "A", conclui_com: { tipo: "voar" } }, { texto: "B" }]).some(e => e.codigo === "guia_conclui_invalido"));
check("último passo com conclui_com é aviso", G.validar([{ texto: "A", conclui_com: { tipo: "atacar" } }]).some(e => e.codigo === "guia_ultimo_conclui"));
check("conclui_com válido no meio", ok([{ texto: "A", conclui_com: { tipo: "atacar" } }, { texto: "B" }]));
check("passo vindo do dicionário é válido", ok([{ texto: "ui.tutorial.guia.fala_0.ver.texto" }]));

console.log("[4] roundtrip com as 62 lições reais do Campo de Treinamento");
const d = JSON.parse(fs.readFileSync(path.join(raiz, "dungeons", "campo_de_treinamento.json"), "utf8"));
const comGuia = d.falas.filter(f => f.guia);
check("há lições com guia no JSON", comGuia.length >= 62);
let iguais = 0;
for (const f of comGuia) if (JSON.stringify(G.serializar(G.carregar(f.guia))) === JSON.stringify(f.guia)) iguais++;
check("roundtrip idêntico em todas", iguais === comGuia.length);
check("nenhum guia real reprovado na validação", comGuia.every(f => G.validar(G.carregar(f.guia)).every(e => e.codigo === "guia_ultimo_conclui")));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
```

(A ordem das chaves do passo importa para o `JSON.stringify` do roundtrip: o módulo emite `id, texto, porque, ui, dica, conclui_com`, que é a ordem do gerador `tools/gerar_guia_comum.py` — `id, texto, porque, ui, dica, conclui_com`.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_guia_logic.js`
Expected: erro ao ler `editor_guia_logic.js` (arquivo inexistente).

- [ ] **Step 3: Implementar o módulo**

`tools/editor_guia_logic.js`:

```javascript
// Passos guiados da lição (campo `guia`) — lógica pura do editor, sem DOM.
// As constantes espelham o servidor (GUIA_UI_RE, GUIA_MAX_PASSOS, LICAO_VERBOS);
// tools/test_editor_guia.py cobra a sincronia.
(function () {
  const MAX_PASSOS = 8;
  const MAX_DICAS = 2;
  const UI_RE_FONTE = "^(?:(?:botao|habilidade|bolsa|slot|monstro|hud):[a-z0-9_]+|(?:casa|porta):\\[\\d+,\\d+\\])$";
  const UI_RE = new RegExp(UI_RE_FONTE);
  const TIPOS_ID = ["botao", "habilidade", "bolsa", "slot", "monstro", "hud"];
  const TIPOS_CASA = ["casa", "porta"];
  const TIPOS_UI = TIPOS_ID.concat(TIPOS_CASA);
  // Mesma lista de LICAO_VERBOS do servidor (server.py).
  const VERBOS = ["mover_ate", "abrir_porta", "atacar", "matar", "pegar_item", "equipar", "encerrar_turno",
    "usar_item", "usar_magia", "usar_habilidade", "usar_tecnica", "usar_instrumento", "desarmar_armadilha"];

  const ehChave = (s) => typeof s === "string" && /^ui\.tutorial\.[a-z0-9_.]+$/.test(s);

  function lerUi(ui) {
    if (typeof ui !== "string" || !ui.includes(":")) return { tipo: "", valor: "" };
    const i = ui.indexOf(":");
    const tipo = ui.slice(0, i), resto = ui.slice(i + 1);
    if (TIPOS_CASA.includes(tipo)) {
      const m = /^\[(\d+),(\d+)\]$/.exec(resto);
      return m ? { tipo, valor: m[1] + "," + m[2] } : { tipo, valor: "" };
    }
    return { tipo, valor: resto };
  }

  function montarUi(tipo, valor) {
    const v = String(valor == null ? "" : valor).trim();
    if (!TIPOS_UI.includes(tipo) || !v) return null;
    if (TIPOS_CASA.includes(tipo)) {
      const m = /^(\d+)\s*,\s*(\d+)$/.exec(v);
      return m ? tipo + ":[" + m[1] + "," + m[2] + "]" : null;
    }
    return tipo + ":" + v;
  }

  function carregar(guia) {
    if (!Array.isArray(guia)) return [];
    return guia.filter(p => p && typeof p === "object").map(p => ({
      ...(p.id != null ? { id: String(p.id) } : {}),
      texto: typeof p.texto === "string" ? p.texto : "",
      porque: typeof p.porque === "string" ? p.porque : "",
      ui: typeof p.ui === "string" && p.ui ? p.ui : null,
      dica: Array.isArray(p.dica) ? p.dica.filter(d => typeof d === "string").slice() : [],
      conclui_com: p.conclui_com && typeof p.conclui_com === "object" && p.conclui_com.tipo
        ? JSON.parse(JSON.stringify(p.conclui_com)) : null,
    }));
  }

  // Ordem das chaves = a do gerador (id, texto, porque, ui, dica, conclui_com).
  function serializar(passos) {
    if (!Array.isArray(passos)) return null;
    const out = passos.map(p => {
      const o = {};
      if (p.id != null && p.id !== "") o.id = p.id;
      o.texto = p.texto || "";
      if (p.porque) o.porque = p.porque;
      if (p.ui) o.ui = p.ui;
      const dica = (p.dica || []).filter(d => typeof d === "string" && d.trim() !== "");
      if (dica.length) o.dica = dica;
      if (p.conclui_com && p.conclui_com.tipo) o.conclui_com = JSON.parse(JSON.stringify(p.conclui_com));
      return o;
    });
    return out.length ? out : null;
  }

  // [{codigo, params}] — o editor traduz com V(codigo, params). `n` é o número do passo (1-based).
  function validar(passos) {
    const e = [];
    if (!Array.isArray(passos) || !passos.length) return e;
    if (passos.length > MAX_PASSOS) e.push({ codigo: "guia_muitos", params: { max: MAX_PASSOS } });
    passos.forEach((p, i) => {
      const n = i + 1;
      if (!String(p.texto || "").trim()) e.push({ codigo: "guia_sem_texto", params: { n } });
      if (p.ui && !UI_RE.test(p.ui)) e.push({ codigo: "guia_ui_invalida", params: { n, ui: p.ui } });
      if ((p.dica || []).length > MAX_DICAS) e.push({ codigo: "guia_dicas", params: { n, max: MAX_DICAS } });
      const cc = p.conclui_com;
      if (cc) {
        if (!VERBOS.includes(cc.tipo)) e.push({ codigo: "guia_conclui_invalido", params: { n, tipo: cc.tipo } });
        else if (i === passos.length - 1) e.push({ codigo: "guia_ultimo_conclui", params: { n } });
      }
    });
    return e;
  }

  window.EDITOR_GUIA = { MAX_PASSOS, MAX_DICAS, UI_RE_FONTE, TIPOS_ID, TIPOS_CASA, TIPOS_UI, VERBOS,
    ehChave, lerUi, montarUi, carregar, serializar, validar };
})();
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_editor_guia_logic.js`
Expected: `… ok, 0 falha(s)`. Se `roundtrip idêntico` falhar, compare `JSON.stringify` de um guia real com a saída e ajuste a ordem das chaves em `serializar`.

- [ ] **Step 5: Teste de sincronia com o servidor**

`tools/test_editor_guia.py`:

```python
"""Sincronia do módulo do editor com o servidor + fiação estática no editor."""
import json, re, subprocess, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S

JS = (RAIZ / "tools" / "editor_guia_logic.js").read_text(encoding="utf-8")


def const_js(nome):
    m = re.search(r"const %s = (.+?);\n" % re.escape(nome), JS)
    assert m, nome
    return m.group(1)


class SincroniaTests(unittest.TestCase):
    def test_regex_de_ui_igual_ao_servidor(self):
        fonte_js = json.loads(const_js("UI_RE_FONTE"))
        self.assertEqual(fonte_js, S.GUIA_UI_RE.pattern)

    def test_limites_iguais_ao_servidor(self):
        self.assertEqual(int(const_js("MAX_PASSOS")), S.GUIA_MAX_PASSOS)

    def test_verbos_iguais_ao_servidor(self):
        verbos_js = json.loads(const_js("VERBOS").replace("\n", " "))
        self.assertEqual(sorted(verbos_js), sorted(S.LICAO_VERBOS))


if __name__ == "__main__":
    unittest.main()
```

Run: `python tools/test_editor_guia.py`
Expected: `OK`. Se `test_verbos_iguais_ao_servidor` falhar, copie a lista **exata** de `LICAO_VERBOS` (`server.py`, perto da linha 44) para `VERBOS` no módulo (a lista do plano é uma amostra; o servidor manda).

- [ ] **Step 6: Commit**

```bash
git add tools/editor_guia_logic.js tools/test_editor_guia_logic.js tools/test_editor_guia.py
git commit -m "feat(editor): módulo puro dos passos guiados (carregar, serializar, validar) com roundtrip das 62 lições" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Preservar o `guia` ao abrir e salvar (conserto da perda de dados)

**Files:**
- Modify: `tools/editor.html` (script novo antes de `editor.js`)
- Modify: `tools/editor.js` (`loadJSON` ~linha 4490 e `buildJSON` ~linha 4018 — **use o script de commit parcial**)
- Test: `tools/test_editor_guia.py` (fiação estática)

- [ ] **Step 1: Escrever o teste de fiação que falha**

Acrescente em `tools/test_editor_guia.py`, antes do `if __name__`:

```python
EDITOR_JS = (RAIZ / "tools" / "editor.js").read_text(encoding="utf-8")
EDITOR_HTML = (RAIZ / "tools" / "editor.html").read_text(encoding="utf-8")


class FiacaoTests(unittest.TestCase):
    def test_html_carrega_o_modulo_antes_do_editor(self):
        i = EDITOR_HTML.find("editor_guia_logic.js")
        j = EDITOR_HTML.find('"editor.js"')
        self.assertTrue(0 <= i < j, "editor_guia_logic.js deve vir antes de editor.js em editor.html")

    def test_load_e_build_conhecem_o_guia(self):
        self.assertIn("EDITOR_GUIA.carregar(", EDITOR_JS)
        self.assertIn("EDITOR_GUIA.serializar(", EDITOR_JS)

    def test_build_escreve_guia_so_quando_ha_passos(self):
        # o campo só entra no JSON se serializar() devolveu lista (null = sem guia)
        self.assertRegex(EDITOR_JS, r"const\s+guia\s*=\s*EDITOR_GUIA\.serializar\(f\.guia\)")
        self.assertRegex(EDITOR_JS, r"if\s*\(guia\)\s*out\.guia\s*=\s*guia")
```

Run: `python tools/test_editor_guia.py`
Expected: falham os 3 testes novos.

- [ ] **Step 2: Carregar o módulo no `editor.html`**

Na lista `s=[...]` do `<script>` de `tools/editor.html`, insira `"editor_guia_logic.js"` **imediatamente antes** de `"editor.js"`.

- [ ] **Step 3: `loadJSON` mantém o guia**

Em `tools/editor.js`, no `S.falas = (obj.falas || []).map(...)`, dentro do objeto devolvido (depois de `efeito: ...`), acrescente `guia: EDITOR_GUIA.carregar(f.guia)`:

```javascript
               efeito: (f.efeito && typeof f.efeito === "object") ? { ...f.efeito } : null,
               guia: EDITOR_GUIA.carregar(f.guia) };
```

- [ ] **Step 4: `buildJSON` escreve o guia**

No `falas: S.falas.map(f => {...})`, antes do `return out;` do bloco (depois do `if (Object.keys(ef).length) out.efeito = ef;`):

```javascript
        const guia = EDITOR_GUIA.serializar(f.guia);
        if (guia) out.guia = guia;
```

Nova fala criada no editor (`case "fala":`, ~linha 1968) ganha `guia: []` no objeto literal (para o painel nunca receber `undefined`): acrescente `, guia: []` depois de `tarefa: null`.

- [ ] **Step 5: Rodar e ver passar + prova de que nada se perde**

Run: `python tools/test_editor_guia.py && node tools/test_editor_guia_logic.js && node --check tools/editor.js`
Expected: tudo passa.

Prova de roundtrip no JSON real (rode no console do navegador na Task 5, ou aqui por node simulando o corpo de `loadJSON`/`buildJSON` só para o campo): o teste node da Task 1 `[4]` já garante que `serializar(carregar(guia))` é idêntico para as 62 lições; este step garante a ligação no `editor.js`.

- [ ] **Step 6: Commit (editor.js só nos meus trechos)**

```bash
git add tools/editor.html tools/test_editor_guia.py
python "$TEMP/commit_meus_trechos.py"
git diff --cached --stat
git commit -m "fix(editor): preserva o guia das lições ao abrir e salvar a masmorra" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

`git diff --cached --stat` deve listar `tools/editor.html`, `tools/editor.js` (poucas linhas, nunca ~250) e o teste. Se `editor.js` mostrar centenas de linhas, **não commite**: `git reset -q tools/editor.js` e refaça com o script.

---

### Task 3: Validação dos passos no editor

**Files:**
- Modify: `tools/editor.js` (bloco de validação das falas, ~linha 4250 — **commit parcial**)
- Modify: `src/lang/editor.js` (chaves `ui.editor.masmorra.valid.guia_*`)
- Test: `tools/test_editor_guia.py`, `tools/test_editor_idioma.py` (placar)

- [ ] **Step 1: Baseline do placar de idioma do editor**

Run: `python tools/test_editor_idioma.py 2>&1 | tail -5`
Anote o resultado **antes** de editar (o trabalho do autor em `editor.js` pode já deixá-lo vermelho; se estiver vermelho por texto que não é seu, não corrija o dele — só garanta que **você** não acrescenta literais em português fora de `t()`).

- [ ] **Step 2: Teste que falha**

Em `tools/test_editor_guia.py`, classe `FiacaoTests`:

```python
    def test_validacao_usa_o_modulo(self):
        self.assertRegex(EDITOR_JS, r"EDITOR_GUIA\.validar\(f\.guia\)")

    def test_chaves_de_validacao_existem_em_pt_e_en(self):
        lang = (RAIZ / "src" / "lang" / "editor.js").read_text(encoding="utf-8")
        for cod in ("guia_muitos", "guia_sem_texto", "guia_ui_invalida", "guia_dicas",
                    "guia_conclui_invalido", "guia_ultimo_conclui"):
            self.assertIn(f'"ui.editor.masmorra.valid.{cod}"', lang, cod)
```

Run: `python tools/test_editor_guia.py` — Expected: falha nos 2 testes novos.

- [ ] **Step 3: Chaves de idioma**

Em `src/lang/editor.js`, junto das outras `ui.editor.masmorra.valid.*` (abra o arquivo, ache `licao_sem_texto_curto` e siga o **formato exato** das chaves vizinhas, inclusive `{id}`/`{pos}`), acrescente:

```javascript
  "ui.editor.masmorra.valid.guia_muitos": { "pt": "Lição {id}: o guia aceita no máximo {max} passos.", "en": "Lesson {id}: the guide accepts at most {max} steps." },
  "ui.editor.masmorra.valid.guia_sem_texto": { "pt": "Lição {id}: o passo {n} do guia está sem texto.", "en": "Lesson {id}: guide step {n} has no text." },
  "ui.editor.masmorra.valid.guia_ui_invalida": { "pt": "Lição {id}: o passo {n} aponta para um elemento inválido ({ui}).", "en": "Lesson {id}: step {n} points to an invalid element ({ui})." },
  "ui.editor.masmorra.valid.guia_dicas": { "pt": "Lição {id}: o passo {n} tem mais de {max} dicas.", "en": "Lesson {id}: step {n} has more than {max} hints." },
  "ui.editor.masmorra.valid.guia_conclui_invalido": { "pt": "Lição {id}: o passo {n} conclui com uma ação desconhecida ({tipo}).", "en": "Lesson {id}: step {n} completes on an unknown action ({tipo})." },
  "ui.editor.masmorra.valid.guia_ultimo_conclui": { "pt": "Lição {id}: o último passo ({n}) não deve concluir por ação — quem encerra a lição é a tarefa.", "en": "Lesson {id}: the last step ({n}) should not complete on an action — the task ends the lesson." },
```

Confira se `V(codigo, params)` em `editor.js` já monta a chave `ui.editor.masmorra.valid.<codigo>` (veja como `V("licao_sem_texto_curto", {...})` resolve; copie o padrão).

- [ ] **Step 4: Ligar a validação**

No laço `for (const f of S.falas)` da validação, dentro do ramo que roda quando `ehLicao` (depois do bloco `if (f.tarefa) { ... }`), acrescente:

```javascript
      for (const er of EDITOR_GUIA.validar(f.guia)) e.push(V(er.codigo, { id: f.id, ...er.params }));
```

- [ ] **Step 5: Rodar**

Run: `python tools/test_editor_guia.py && python tools/test_editor_idioma.py 2>&1 | tail -3 && python tools/test_idioma.py | tail -2 && node --check tools/editor.js`
Expected: passam; o placar do editor **não piora** em relação ao baseline do Step 1. `test_idioma.py` confere a paridade de `{parâmetros}` pt/en das 6 chaves novas.

- [ ] **Step 6: Commit**

```bash
git add tools/test_editor_guia.py src/lang/editor.js
python "$TEMP/commit_meus_trechos.py"
git diff --cached --stat
git commit -m "feat(editor): valida os passos guiados da lição (limites, ui, dicas, conclui_com)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Painel de passos na fala

**Files:**
- Modify: `tools/editor.js` (painel da fala, bloco `k === "fala"` ~linha 3070 — **commit parcial**)
- Modify: `src/lang/editor.js` (chaves `ui.editor.masmorra.guia.*`)
- Test: `tools/test_editor_guia.py`

O painel acrescenta, dentro do bloco "🎓 lição" (depois do campo de efeito de fome/sede, antes do texto "dispara uma vez"), a seção **🧭 Passos guiados**. Cada passo é um cartão com: número + botões ↑ ↓ ✕; **texto**; **porquê**; **destacar** (tipo + valor); **dicas** (até 2); **conclui com** (verbo + alvo opcional). Passo cujo `texto` é chave do dicionário (`EDITOR_GUIA.ehChave`) aparece **somente leitura** com o texto resolvido por `t(chave)` e o botão "Converter em texto livre". Limite de 8 passos (o botão "+ Passo" some).

- [ ] **Step 1: Teste que falha**

Em `FiacaoTests`:

```python
    def test_painel_tem_a_secao_de_passos(self):
        self.assertIn("ui.editor.masmorra.guia.titulo", EDITOR_JS)
        self.assertIn("renderGuiaPassos(", EDITOR_JS)

    def test_chaves_do_painel_em_pt_e_en(self):
        lang = (RAIZ / "src" / "lang" / "editor.js").read_text(encoding="utf-8")
        for k in ("titulo", "dica_secao", "passo_n", "texto", "porque", "destacar", "destacar_nenhum",
                  "valor_id", "valor_casa", "dica_n", "conclui_com", "conclui_nenhum", "alvo_opcional",
                  "adicionar", "subir", "descer", "remover", "do_dicionario", "converter", "limite"):
            self.assertIn(f'"ui.editor.masmorra.guia.{k}"', lang, k)

    def test_painel_nunca_escreve_chave_de_dicionario(self):
        # passo vindo do dicionário é somente leitura: o painel não monta <textarea> para ele
        self.assertIn("EDITOR_GUIA.ehChave(", EDITOR_JS)
```

Run: `python tools/test_editor_guia.py` — Expected: falha nos 3 novos.

- [ ] **Step 2: Chaves de idioma do painel**

Em `src/lang/editor.js`, antes do `};` final do objeto (ou junto do bloco `ui.editor.masmorra.painel.*`, no mesmo formato das chaves vizinhas):

```javascript
  "ui.editor.masmorra.guia.titulo": { "pt": "Passos guiados", "en": "Guided steps" },
  "ui.editor.masmorra.guia.dica_secao": { "pt": "Cada passo aparece na janela da lição, com um destaque na tela. O último passo é encerrado pela tarefa.", "en": "Each step shows in the lesson window with a highlight on screen. The task ends the last step." },
  "ui.editor.masmorra.guia.passo_n": { "pt": "Passo {n}", "en": "Step {n}" },
  "ui.editor.masmorra.guia.texto": { "pt": "Instrução (até 15 palavras)", "en": "Instruction (up to 15 words)" },
  "ui.editor.masmorra.guia.porque": { "pt": "Por quê (opcional)", "en": "Why (optional)" },
  "ui.editor.masmorra.guia.destacar": { "pt": "Destacar na tela", "en": "Highlight on screen" },
  "ui.editor.masmorra.guia.destacar_nenhum": { "pt": "Nada", "en": "Nothing" },
  "ui.editor.masmorra.guia.valor_id": { "pt": "id (ex.: mira_certeira)", "en": "id (e.g. mira_certeira)" },
  "ui.editor.masmorra.guia.valor_casa": { "pt": "x,y (ex.: 5,15)", "en": "x,y (e.g. 5,15)" },
  "ui.editor.masmorra.guia.dica_n": { "pt": "Dica {n} (aparece se o jogador demora)", "en": "Hint {n} (shows if the player stalls)" },
  "ui.editor.masmorra.guia.conclui_com": { "pt": "Avança sozinho quando o jogador…", "en": "Advances by itself when the player…" },
  "ui.editor.masmorra.guia.conclui_nenhum": { "pt": "(botão \"Entendi\")", "en": "(\"Got it\" button)" },
  "ui.editor.masmorra.guia.alvo_opcional": { "pt": "alvo (opcional)", "en": "target (optional)" },
  "ui.editor.masmorra.guia.adicionar": { "pt": "+ Passo", "en": "+ Step" },
  "ui.editor.masmorra.guia.subir": { "pt": "Subir passo", "en": "Move step up" },
  "ui.editor.masmorra.guia.descer": { "pt": "Descer passo", "en": "Move step down" },
  "ui.editor.masmorra.guia.remover": { "pt": "Remover passo", "en": "Remove step" },
  "ui.editor.masmorra.guia.do_dicionario": { "pt": "🔑 Texto do dicionário do jogo (gerado). Para editar, converta em texto livre:", "en": "🔑 Text from the game dictionary (generated). To edit it, convert it to free text:" },
  "ui.editor.masmorra.guia.converter": { "pt": "Converter em texto livre", "en": "Convert to free text" },
  "ui.editor.masmorra.guia.limite": { "pt": "Limite de {max} passos.", "en": "Limit of {max} steps." },
```

- [ ] **Step 3: A função `renderGuiaPassos`**

Em `tools/editor.js`, **dentro** do escopo de `renderPanel` (onde `ref`, `panel` e `renderPanel` existem), logo antes do `panel.innerHTML = ...` do ramo `k === "fala"`, defina o HTML dos passos; e depois de ligar os demais `onchange` da fala, ligue os eventos. Use `t()` em **todo** texto visível (o placar de idioma do `editor.js` é cobrado) e nenhum `t` local (o placar [5] acusa sombreamento).

HTML (função local, devolve string):

```javascript
      const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
      const renderGuiaPassos = () => {
        const passos = ref.guia || (ref.guia = []);
        const cartoes = passos.map((p, i) => {
          const ui = EDITOR_GUIA.lerUi(p.ui);
          if (!ui.tipo && p._uiTipo) ui.tipo = p._uiTipo;     // tipo escolhido, valor ainda vazio
          const cc = p.conclui_com || { tipo: "" };
          const dica = [p.dica[0] || "", p.dica[1] || ""];
          const doDicionario = EDITOR_GUIA.ehChave(p.texto);
          const topo = `<div style="display:flex;gap:4px;align-items:center"><b style="flex:1">${t("ui.editor.masmorra.guia.passo_n", { n: i + 1 })}</b>
              <button data-g="sobe" data-i="${i}" title="${t("ui.editor.masmorra.guia.subir")}"${i === 0 ? " disabled" : ""}>↑</button>
              <button data-g="desce" data-i="${i}" title="${t("ui.editor.masmorra.guia.descer")}"${i === passos.length - 1 ? " disabled" : ""}>↓</button>
              <button data-g="remove" data-i="${i}" title="${t("ui.editor.masmorra.guia.remover")}">✕</button></div>`;
          if (doDicionario) {
            return `<div class="guia-passo" style="border:1px solid #4a3a2a;padding:6px;margin:6px 0">${topo}
              <small style="color:#8a7a5a">${t("ui.editor.masmorra.guia.do_dicionario")}</small>
              <div style="margin:4px 0;color:#d8d0b8">${esc(t(p.texto))}</div>
              <button data-g="converte" data-i="${i}">${t("ui.editor.masmorra.guia.converter")}</button></div>`;
          }
          const opcoesUi = ["", ...EDITOR_GUIA.TIPOS_UI].map(tp =>
            `<option value="${tp}"${ui.tipo === tp ? " selected" : ""}>${tp === "" ? t("ui.editor.masmorra.guia.destacar_nenhum") : tp}</option>`).join("");
          const opcoesCc = [""].concat(EDITOR_GUIA.VERBOS).map(v =>
            `<option value="${v}"${cc.tipo === v ? " selected" : ""}>${v === "" ? t("ui.editor.masmorra.guia.conclui_nenhum") : t("ui.editor.masmorra.licao." + v)}</option>`).join("");
          const ehCasaUi = EDITOR_GUIA.TIPOS_CASA.includes(ui.tipo);
          return `<div class="guia-passo" style="border:1px solid #4a3a2a;padding:6px;margin:6px 0">${topo}
            <label>${t("ui.editor.masmorra.guia.texto")}</label><textarea data-g="texto" data-i="${i}" rows="2" style="width:100%">${esc(p.texto)}</textarea>
            <label>${t("ui.editor.masmorra.guia.porque")}</label><input data-g="porque" data-i="${i}" value="${esc(p.porque)}" style="width:100%">
            <label>${t("ui.editor.masmorra.guia.destacar")}</label>
            <select data-g="ui_tipo" data-i="${i}">${opcoesUi}</select>
            ${ui.tipo ? `<input data-g="ui_valor" data-i="${i}" value="${esc(ui.valor)}" placeholder="${ehCasaUi ? t("ui.editor.masmorra.guia.valor_casa") : t("ui.editor.masmorra.guia.valor_id")}" style="width:55%">` : ""}
            <label>${t("ui.editor.masmorra.guia.dica_n", { n: 1 })}</label><input data-g="dica0" data-i="${i}" value="${esc(dica[0])}" style="width:100%">
            <label>${t("ui.editor.masmorra.guia.dica_n", { n: 2 })}</label><input data-g="dica1" data-i="${i}" value="${esc(dica[1])}" style="width:100%">
            <label>${t("ui.editor.masmorra.guia.conclui_com")}</label>
            <select data-g="cc_tipo" data-i="${i}">${opcoesCc}</select>
            ${cc.tipo ? `<input data-g="cc_alvo" data-i="${i}" value="${esc(cc.alvo == null ? "" : (Array.isArray(cc.alvo) ? cc.alvo.join(",") : cc.alvo))}" placeholder="${t("ui.editor.masmorra.guia.alvo_opcional")}" style="width:55%">` : ""}
          </div>`;
        }).join("");
        const podeMais = passos.length < EDITOR_GUIA.MAX_PASSOS;
        return `<div id="guia-secao" style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>🧭 ${t("ui.editor.masmorra.guia.titulo")}</b>
          <small style="display:block;color:#8a7a5a">${t("ui.editor.masmorra.guia.dica_secao")}</small>
          ${cartoes}
          ${podeMais ? `<button data-g="novo">${t("ui.editor.masmorra.guia.adicionar")}</button>` : `<small style="color:#d8a0a0">${t("ui.editor.masmorra.guia.limite", { max: EDITOR_GUIA.MAX_PASSOS })}</small>`}
        </div>`;
      };
```

Insira `${renderGuiaPassos()}` no template do painel, logo depois do `</div>` que fecha o bloco `🎓` e antes do `<div ...>dispara_uma_vez_hint</div>`.

Eventos (depois do último `document.getElementById("f-...").onchange` da fala): **um único** manipulador delegado no contêiner, que atualiza o estado e só redesenha o painel quando a estrutura muda (adicionar/remover/mover/converter/tipo de ui/tipo de conclui) — **nunca** em cada tecla, senão o campo perde o foco:

```javascript
      const secao = document.getElementById("guia-secao");
      if (secao) {
        const passo = (el) => ref.guia[Number(el.dataset.i)];
        secao.onchange = (ev) => {
          const el = ev.target, g = el.dataset.g;
          if (!g || g === "novo") return;
          const p = passo(el); if (!p) return;
          if (g === "texto") p.texto = el.value;
          else if (g === "porque") p.porque = el.value;
          else if (g === "dica0" || g === "dica1") {
            const d = [p.dica[0] || "", p.dica[1] || ""]; d[g === "dica0" ? 0 : 1] = el.value;
            p.dica = d.filter(x => x.trim() !== "");
          } else if (g === "ui_tipo") { p._uiTipo = el.value; p.ui = EDITOR_GUIA.montarUi(el.value, EDITOR_GUIA.lerUi(p.ui).valor); renderPanel(); }
          else if (g === "ui_valor") { p.ui = EDITOR_GUIA.montarUi(p._uiTipo || EDITOR_GUIA.lerUi(p.ui).tipo, el.value); }
          else if (g === "cc_tipo") { p.conclui_com = el.value ? { tipo: el.value } : null; renderPanel(); }
          else if (g === "cc_alvo") { if (p.conclui_com) { const v = el.value.trim(); if (!v) delete p.conclui_com.alvo; else p.conclui_com.alvo = /^\d+\s*,\s*\d+$/.test(v) ? v.split(",").map(n => parseInt(n, 10)) : v; } }
        };
        secao.onclick = (ev) => {
          const el = ev.target.closest("button[data-g]"); if (!el) return;
          const g = el.dataset.g, i = Number(el.dataset.i);
          const l = ref.guia;
          if (g === "novo" && l.length < EDITOR_GUIA.MAX_PASSOS) l.push({ texto: "", porque: "", ui: null, dica: [], conclui_com: null });
          else if (g === "remove") l.splice(i, 1);
          else if (g === "sobe" && i > 0) [l[i - 1], l[i]] = [l[i], l[i - 1]];
          else if (g === "desce" && i < l.length - 1) [l[i + 1], l[i]] = [l[i], l[i + 1]];
          else if (g === "converte") { l[i].texto = t(l[i].texto); if (l[i].porque && EDITOR_GUIA.ehChave(l[i].porque)) l[i].porque = t(l[i].porque); l[i].dica = l[i].dica.map(d => EDITOR_GUIA.ehChave(d) ? t(d) : d); }
          else return;
          renderPanel();
        };
      }
```

Sobre `p._uiTipo`: escolher um tipo de destaque antes de digitar o valor deixa `p.ui = null`, então o painel guarda o tipo escolhido num campo de trabalho `_uiTipo` para o campo de valor aparecer. `carregar` não o copia e `serializar` só emite os campos conhecidos, então ele nunca vai para o JSON.

`t("ui.editor.masmorra.licao.<verbo>")` já existe para os verbos de tarefa (usado no select de tarefa do mesmo painel); se faltar algum dos 13 verbos de `VERBOS`, o painel mostraria a própria chave — o teste do Step 4 cobra.

- [ ] **Step 4: Cobrir os rótulos dos verbos**

Em `tools/test_editor_guia.py`:

```python
    def test_todo_verbo_de_conclusao_tem_rotulo_no_editor(self):
        lang = (RAIZ / "src" / "lang" / "editor.js").read_text(encoding="utf-8")
        for v in S.LICAO_VERBOS:
            self.assertIn(f'"ui.editor.masmorra.licao.{v}"', lang, v)
```

(Se o servidor tiver verbos sem rótulo no editor, o teste acusa: acrescente a chave pt/en no mesmo formato das vizinhas.)

- [ ] **Step 5: Rodar**

Run: `python tools/test_editor_guia.py && python tools/test_editor_idioma.py 2>&1 | tail -3 && python tools/test_idioma.py | tail -2 && node --check tools/editor.js`
Expected: passam, placar do editor sem piorar.

- [ ] **Step 6: Commit**

```bash
git add tools/test_editor_guia.py src/lang/editor.js
python "$TEMP/commit_meus_trechos.py"
git diff --cached --stat
git commit -m "feat(editor): lista de passos guiados no painel da fala (editar, reordenar, destacar, dicas, conclui_com)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Prova no navegador, documentação e fechamento

**Files:** Modify `CLAUDE.md` (CRLF — usar Edit)

- [ ] **Step 1: Servidor isolado e abertura do editor**

Copie o projeto para `%TEMP%\lfh_guia5` (sem `.git`, `.worktrees`, `savegames`, `accounts`, `groups`, `savegame_points`), suba com `LFH_PORT=8793` e abra `http://[::1]:8793/tools/editor.html` no navegador do app (pelo servidor, não por `file://`: o editor usa o mesmo `localStorage` e o servidor de upload). Não grave nada em `dungeons/` do projeto real: o servidor isolado grava na cópia.

- [ ] **Step 2: Conferir em tela**

1. Carregue `campo_de_treinamento.json` no editor. Selecione a fala `fala_0`: a seção **🧭 Passos guiados** mostra 2 passos, ambos com o aviso "🔑 Texto do dicionário…" e o texto resolvido ("Veja seu movimento…").
2. Clique **Converter em texto livre** no passo 1: o texto vira editável, em português; edite uma palavra; confira que o painel **não** perde o foco ao digitar (só redesenha em estrutura).
3. **Prova do conserto:** no console do editor, rode `JSON.parse(JSON.stringify(EDITOR.buildJSON())).falas.filter(f => f.guia).length` → deve dar **62** (antes do conserto daria 0). Confira também que a fala editada saiu com o texto novo.
4. Crie uma fala nova com `classe` e tarefa, adicione 2 passos (um com `ui` = `botao`/`encerrar_turno`, outro com `ui` = `casa`/`5,15`), salve na cópia, recarregue e confirme que os passos voltam.
5. Provoque os erros: deixe um passo sem texto e um `ui` inválido (`botao` com valor `Maiúscula`) → a validação lista os avisos `guia_sem_texto` e `guia_ui_invalida`; troque para inglês (🌐) e confira as mensagens em inglês.
6. `read_console_messages` com `onlyErrors`: nenhum erro.
7. **Fim a fim opcional:** abra a masmorra salva na cópia pelo jogo (`GS.worldAdventure('treinamento')` com o Campo de Treinamento editado) e veja o passo novo na janela da lição.

- [ ] **Step 3: Documentar em `CLAUDE.md`**

No parágrafo do tutorial guiado, troque "Falta a fatia 5 (editor de masmorras com a lista de passos no painel de fala)." por: **Fatia 5:** o editor de masmorras agora **preserva** o `guia` ao abrir/salvar (antes `loadJSON`/`buildJSON` o apagavam — salvar o Campo de Treinamento pelo editor zerava os guias das 62 lições) e edita os passos no painel da fala (`renderGuiaPassos`; ↑ ↓ ✕, `ui` por tipo+valor, até 2 dicas, `conclui_com`); a lógica é o módulo puro `tools/editor_guia_logic.js` (`EDITOR_GUIA`), sincronizado com `GUIA_UI_RE`/`GUIA_MAX_PASSOS`/`LICAO_VERBOS` do servidor por `tools/test_editor_guia.py`; passo com texto de dicionário (`ui.tutorial.*`, gerado por `gerar_guia_comum.py`) é somente leitura até "Converter em texto livre"; texto digitado é conteúdo autoral em português (sem campo por idioma). Testes: `tools/test_editor_guia_logic.js`, `tools/test_editor_guia.py`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia5-editor.md`. Fora de escopo: escolher o `ui` clicando no mapa e campo de texto por idioma.

- [ ] **Step 4: Suítes finais e limpeza**

Run: `python tools/test_editor_guia.py`, `node tools/test_editor_guia_logic.js`, `python tools/test_editor_idioma.py`, `python tools/test_editor_itens.py`, `python tools/test_tutorial_guia.py`, `python tools/test_tutorial_conteudo.py`, `python tools/test_tutorial_classes.py`, `python tools/test_tutorial_modelos.py`, `python tools/test_idioma.py`, `python tools/test_interface.py`, `python tools/dividas.py`, `node tools/test_editor_settab.js`, `node tools/test_editor_i18n.js`. Todos devem passar (o placar do editor, no máximo igual ao baseline). Pare o servidor da 8793 e apague `%TEMP%\lfh_guia5`.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia5-editor.md
git commit -m "docs: guia do tutorial (fatia 5, editor) no CLAUDE.md" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

Não fazer push sem o usuário pedir.

---

## Auto-revisão

- **Cobertura do spec (seção 5, fatia 5 — "editor de masmorras: lista de passos no painel de fala (texto, porquê, `ui`, dicas)"):** painel completo (Task 4) + validação espelhando o servidor (Task 3) + conserto da perda de dados que a spec não previa (Task 2). `conclui_com` entrou no painel porque faz parte do formato do passo; sem ele o editor apagaria esse campo dos guias que já o usam.
- **Risco 1 — perda de dados:** coberto por `[4]` do teste node (roundtrip das 62 lições reais) + `test_load_e_build_conhecem_o_guia` + prova do Step 2.3 no navegador.
- **Risco 2 — trabalho não commitado do autor em `editor.js`:** o script de commit parcial exclui o bloco `@@ -50,0 +51,252 @@` e aborta se ele não aparecer; cada commit confere `git diff --cached --stat`.
- **Risco 3 — texto de dicionário editado por engano:** passo com `ui.tutorial.*` é somente leitura; "converter" copia o texto resolvido no idioma atual do editor. Se o autor converter em inglês, o texto livre fica em inglês (decisão do autor; o jogo mostra texto autoral sem tradução).
- **Risco 4 — placar de idioma do editor** (`test_editor_idioma.py`, `editor.js` está em `FECHADAS`): todo texto visível novo passa por `t()`; nenhum `t` local novo (o placar [5] acusa sombreamento); a Task 3 Step 1 registra o baseline para não culpar o trabalho do autor.
- **Consistência de nomes:** `EDITOR_GUIA`, `carregar`, `serializar`, `validar`, `lerUi`, `montarUi`, `ehChave`, `MAX_PASSOS`, `TIPOS_UI`, `renderGuiaPassos`, `f.guia` aparecem com a mesma grafia em todas as tasks.
- **Pendências conhecidas (fora de escopo, de propósito):** escolher a casa do `ui` clicando no mapa; campo de texto por idioma para o conteúdo autoral; ordem das chaves de `id`.
