# Editor de Masmorras — Fase 4b: Aba de Campanha no Editor

**Data:** 2026-06-17
**Projeto:** Legends for Hire (RPG de tabuleiro multiplayer)
**Status:** Aprovado — pronto para plano de implementação

---

## Contexto

Última peça do editor de masmorras (ver [[editor-masmorras-fases]]). A **Fase 4a**
implementou o runtime de campanha (`campaigns/*.json` = sequência de masmorras; seleção
no lobby; avanço de fase; progressão). Esta **Fase 4b** dá ao editor visual (Fase 2) uma
**aba de campanha** para montar/ordenar campanhas sem escrever `campaign.json` à mão.

O formato de `campaign.json` **não muda** (continua `{schema_version, id, name,
dungeons:[arquivo, …]}` da 4a) — então o runtime da 4a **não é tocado**. Tudo aqui é
client-side no editor (`tools/`), exceto a extensão do gerador (Python).

### Decisões de produto (aprovadas no brainstorm)

- Adicionar fases por **dropdown** das masmorras existentes (índice **gerado**, com o
  `defn` completo embutido → prévia e edição funcionam offline).
- Aba **Campanha** no mesmo `editor.html` (seletor "Masmorra | Campanha"); lógica num
  `editor_campaign.js` separado.
- Extras: **mini-mapa** por fase; **abrir a fase** no editor de masmorra; **reordenar
  arrastando** (+ ↑/↓); **validar** na aba (bloqueia salvar).

---

## Arquitetura atual relevante

- Editor (Fase 2): `tools/editor.html` (topbar + `#toolbar` + `#workspace`[`#board` canvas
  + `#panel`] + `#statusbar`) inclui `editor_catalog.js` (gerado) e `editor.js` (IIFE com
  estado `S`, ferramentas, `render`, `loadJSON`, `save`, validação; expõe `window.EDITOR`).
- Gerador (Fase 2): `tools/export_catalog.py` → `tools/editor_catalog.js`
  (`window.EDITOR_CATALOG`). Helpers de masmorra no `server.py`: `listar_dungeons`,
  `carregar_dungeon`, `validar_dungeon`, `DUNGEONS_DIR`.
- Runtime de campanha (Fase 4a): formato `campaign.json`; `validar_campanha` no `server.py`
  (referência para o teste de round-trip).
- Scripts simples (sem ES modules) por causa de `file://` — usar globais
  (`window.EDITOR_DUNGEONS`, `window.EDITOR`, `window.EDITOR_CAMPAIGN`).

---

## 1. Índice de masmorras gerado (`tools/editor_dungeons.js`)

Estender `tools/export_catalog.py`: além de `editor_catalog.js`, escrever
`tools/editor_dungeons.js`:

```javascript
// GERADO por tools/export_catalog.py — não editar à mão.
window.EDITOR_DUNGEONS = [
  { "file": "test_fase1.json", "id": "test_fase1", "name": "Cripta dos Sussurros",
    "defn": { /* masmorra completa, idêntica ao arquivo */ } },
  ...
];
```

- Nova função `build_dungeons_index()` em `export_catalog.py`: varre `DUNGEONS_DIR`
  (`os.listdir`, `*.json`), carrega cada um (`carregar_dungeon`), inclui só os **válidos**
  (`validar_dungeon`), com `file`/`id`/`name`/`defn` (defn = o dict carregado).
- Nova função `write_dungeons_js(destino)` escreve a atribuição global (como `editor_catalog.js`).
- O `__main__` de `export_catalog.py` passa a escrever **os dois** arquivos (catálogo +
  índice). Você roda `python tools/export_catalog.py` ao criar/editar masmorras.
- O `defn` embutido permite dropdown, mini-mapa e "abrir no editor" **sem fetch** (offline).

---

## 2. Abas no `editor.html`

Adicionar um seletor de abas no topo (sempre visível): **Masmorra** | **Campanha**.
Estrutura por aba (mostrar/esconder ao alternar):

- **Masmorra** (atual): controles de masmorra (id/nome/grid/resize/carregar/salvar) +
  `#toolbar` + `#workspace`.
- **Campanha** (nova): `#campaign-controls` (id/nome da campanha + Carregar/Salvar) +
  `#campaign-add` (dropdown "+ adicionar fase" + botão) + `#campaign-list` (lista ordenada).
- `#statusbar` é compartilhado; cada aba escreve seu próprio status.

Incluir os scripts: `editor_dungeons.js` (gerado) e `editor_campaign.js`, depois de
`editor_catalog.js`/`editor.js`. Os controles de masmorra existentes ficam num contêiner
`#dungeon-controls` para poder esconder na aba de campanha.

Mecânica de aba: uma função `setTab('masmorra'|'campanha')` (em `editor.js` ou um pequeno
script no HTML) alterna a classe/visibilidade dos blocos e atualiza o status. `editor.js`
e `editor_campaign.js` coordenam via globais (`window.EDITOR`, `window.EDITOR_CAMPAIGN`,
`window.setTab`).

---

## 3. Lógica da campanha (`tools/editor_campaign.js`)

Estado: `C = { id: "nova_campanha", name: "Nova Campanha", dungeons: [] }` (lista de
nomes de arquivo). Constantes: `DUN = window.EDITOR_DUNGEONS || []`.

Funções (expostas em `window.EDITOR_CAMPAIGN`):
- `dunByFile(file)` → entrada do índice (ou null).
- `renderCampaign()` — desenha `#campaign-controls` (id/nome ligados a `C`), o dropdown de
  adicionar (opções de `DUN`: `name — file`), e `#campaign-list`: para cada `file` em
  `C.dungeons`, um item com: handle de arrastar, índice, **mini-mapa** (canvas pequeno),
  `name`/`file` (ou `file` + "(não encontrada)" se ausente do índice), botões **abrir** /
  **↑** / **↓** / **remover**.
- `drawMiniMap(canvas, defn)` — desenha tiles (WALL/FLOOR/DOOR) escalados ao tamanho do
  canvas + um ponto por entidade (entrada/saída/monstro/baú/armadilha/prisioneiro).
- `addPhase(file)` / `removePhase(i)` / `movePhase(i, dir)` — mutam `C.dungeons` + re-render.
- Drag-and-drop: handlers `dragstart`/`dragover`/`drop` nos itens reordenam `C.dungeons`.
- `openInEditor(file)` — `EDITOR.loadJSON(dunByFile(file).defn)` e `setTab('masmorra')`.
- `validarCampanhaEditor()` → `{ok, erros}`: id e nome não vazios; `C.dungeons.length >= 1`;
  todo `file` existe em `DUN` (índice só tem válidas). `updateCampaignStatus()` mostra
  verde/erros no `#statusbar` e bloqueia salvar.
- `saveCampaign()` — valida; se ok, monta `{schema_version:1, id:C.id, name:C.name,
  dungeons:[...C.dungeons]}`, `JSON.stringify(…, null, 2)`, dispara download `<id>.json`
  (você move para `campaigns/`).
- `loadCampaign()` — `<input type=file>` → `JSON.parse` → repovoa `C` (id/name/dungeons);
  re-render (mini-mapas/nomes vêm do índice ao casar `file`).

---

## 4. Estilos (`tools/editor.css`)

Abas (estado ativo/inativo), `#campaign-controls`/`#campaign-add` (linha de controles),
itens de `#campaign-list` (cartão com mini-mapa + texto + botões), aparência de "arrastando"
(opacidade/realce de drop). Segue o tema escuro existente do editor.

---

## 5. Teste

- **Gerador (Python, TDD):** estender `tools/test_export_catalog.py` (ou novo
  `tools/test_export_dungeons.py`): `build_dungeons_index()` inclui só masmorras válidas,
  cada item tem `file`/`id`/`name`/`defn`; `write_dungeons_js` escreve arquivo começando
  com `window.EDITOR_DUNGEONS =` e cujo payload é JSON válido; todo `file` do índice ∈
  `dungeons/` e passa em `validar_dungeon`.
- **Round-trip de formato (Python):** um `campaign.json` no formato que o editor produz
  (`{schema_version:1,id,name,dungeons:[...]}`) passa em `server.validar_campanha`
  (reaproveitar `campaigns/test_campanha.json` como referência).
- **Aba (JS):** verificação no navegador (servir `python -m http.server 8077`): abrir
  `editor.html`, alternar para **Campanha**, adicionar 2 fases pelo dropdown, ver os
  mini-mapas, reordenar (↑/↓ e arrastar), validar (verde), **salvar** (baixa `campaign.json`
  válido), recarregar (`loadCampaign`), e **abrir no editor** (carrega a masmorra na aba
  Masmorra). Console sem erros. Sem harness JS automatizado (consistente com o projeto);
  a lógica pura é exercida via `window.EDITOR_CAMPAIGN.*` no console.

---

## 6. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Índice desatualizado vs. masmorras criadas | Gerador é a fonte; rodar `export_catalog.py` ao criar/editar masmorras (mesmo passo do catálogo). A aba mostra "(não encontrada)" se um `file` do campaign.json não estiver no índice. |
| `editor_dungeons.js` grande (defn completo de cada masmorra) | Aceitável para um punhado de masmorras locais; é arquivo de ferramenta DEV, não vai para o jogo. |
| Acoplamento entre `editor.js` e `editor_campaign.js` (abas, abrir-no-editor) | Interface mínima por globais (`window.EDITOR.loadJSON`, `window.setTab`); `editor.js` permanece focado na masmorra. |
| `campaign.json` referenciar masmorra inexistente | Validação na aba (existe no índice) + `validar_campanha` do servidor ao jogar (autoridade). |
| Quebrar o editor de masmorra existente ao adicionar abas | As abas só mostram/escondem blocos; o caminho da masmorra fica intacto. Verificação no navegador cobre ambas as abas. |

---

## 7. Arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `tools/export_catalog.py` | Modificar | Também gerar `editor_dungeons.js` (índice com `defn`) |
| `tools/editor_dungeons.js` | Gerado | `window.EDITOR_DUNGEONS` |
| `tools/editor.html` | Modificar | Abas Masmorra/Campanha + blocos da campanha + includes |
| `tools/editor.css` | Modificar | Estilos de abas + lista de campanha |
| `tools/editor_campaign.js` | Criar | Estado/render/validação/IO/drag da campanha |
| `tools/editor.js` | Modificar (mínimo) | `setTab` / cooperação de abas (esconder workspace na aba campanha) |
| `tools/test_export_catalog.py` | Modificar | Cobrir o índice de masmorras |
