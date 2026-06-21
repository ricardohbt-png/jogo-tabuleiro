# Editor de Masmorras — Fase 4b: Aba de Campanha + História

**Data:** 2026-06-17
**Projeto:** Legends for Hire (RPG de tabuleiro multiplayer)
**Status:** Aprovado — pronto para plano de implementação

---

## Contexto

Última peça do editor de masmorras (ver [[editor-masmorras-fases]]). A **Fase 4a**
implementou o runtime de campanha (`campaigns/*.json` = sequência de masmorras; seleção
no lobby; avanço de fase; progressão). Esta **Fase 4b** entrega:

- **(a) Editor** — uma **aba de campanha** no editor visual (Fase 2) para montar/ordenar
  campanhas e escrever os textos de história, sem editar JSON à mão.
- **(b) Formato** — `campaign.json` ganha **textos de história** (abertura/encerramento da
  campanha e de cada fase), de forma **retrocompatível**.
- **(c) Runtime** — exibir as **telas de história** nos momentos certos (estende a 4a,
  já mergeada).

### Decisões de produto (aprovadas no brainstorm)

- Adicionar fases por **dropdown** das masmorras existentes (índice **gerado** com o `defn`
  completo embutido → dropdown, mini-mapa e "abrir no editor" funcionam offline).
- Aba **Campanha** no mesmo `editor.html`; lógica num `editor_campaign.js` separado.
- Extras da lista: **mini-mapa** por fase; **abrir a fase** no editor de masmorra;
  **reordenar arrastando** (+ ↑/↓); **validar** (bloqueia salvar).
- **História:** **por fase** (abertura antes do mapa + encerramento ao concluir) **e da
  campanha** (abertura geral antes da 1ª fase + final após a última).
- **Apresentação:** **tela/painel de história** sobreposto com botão **"Continuar"**.
- **Multiplayer:** **cada jogador fecha a sua** tela; a história **não trava** o jogo
  (o tabuleiro já está atrás).

---

## Arquitetura atual relevante

- Editor (Fase 2): `tools/editor.html` (topbar + `#toolbar` + `#workspace` + `#statusbar`)
  inclui `editor_catalog.js` (gerado) e `editor.js` (IIFE com estado `S`, `render`,
  `loadJSON`, `save`, validação; expõe `window.EDITOR`).
- Gerador (Fase 2): `tools/export_catalog.py` → `editor_catalog.js`. Helpers no `server.py`:
  `listar_dungeons`, `carregar_dungeon`, `validar_dungeon`, `DUNGEONS_DIR`.
- Runtime de campanha (Fase 4a): `validar_campanha`, `carregar_campanha`, `listar_campanhas`,
  `CAMPAIGNS_DIR`; `self.mode=="campaign"`, `self.campaign`, `self.campaign_phase`,
  `self.selected_campaign`. `enter_dungeon` carrega a fase via
  `self.campaign["dungeons"][self.campaign_phase]`. Avanço em `_check_objectives`:
  principal cumprido → `_voltar_para_cidade()` (próxima fase) ou `end_game(victory)` (última).
  `_campaign_payload()` em `push_state`/`broadcast_city_state` → `{name, phase, total}`.
- Cliente: `GS.campaign` (getter), `GS.lobbyCampaigns`, `GS.selectCampaign`; HUD "Fase N de M".
- Scripts simples (sem ES modules) por `file://` — globais
  (`window.EDITOR_DUNGEONS`, `window.EDITOR`, `window.EDITOR_CAMPAIGN`).

---

## 1. Formato `campaign.json` (com história, retrocompatível)

```jsonc
{
  "schema_version": 1, "id": "campanha_cripta", "name": "A Cripta dos Sussurros",
  "intro": "Abertura da campanha (antes da 1ª fase). Opcional.",
  "outro": "Final da campanha (após a última fase). Opcional.",
  "dungeons": [
    { "file": "fase1.json", "intro": "Texto antes da fase 1.", "outro": "Texto ao concluir a fase 1." },
    "fase2.json"
  ]
}
```

- Cada item de `dungeons` é **string** (formato 4a) **OU objeto** `{file, intro?, outro?}`.
- `intro`/`outro` (campanha e fase) são strings opcionais.
- **Normalização** (server e editor): `_fase_obj(item)` → `{file, intro, outro}` (string →
  `{file:item, intro:"", outro:""}`).

### Mudanças no runtime 4a (retrocompat)

- `validar_campanha`: para cada item, se string → valida como hoje (file existe + válido);
  se dict → exige `file` (string) válido; `intro`/`outro`, se presentes, devem ser string.
  Caso contrário, recusa apontando a fase.
- Helper `_fase_file(self, i)` (e/ou módulo) → o `file` da fase i (string|objeto).
- `enter_dungeon`: usa `_fase_file(self.campaign_phase)` no lugar do índice direto.

---

## 2. Runtime da história (exibição)

Tudo client-side de apresentação; o servidor só fornece o texto certo em cada transição.
A história **nunca bloqueia** o servidor (cada cliente exibe e fecha localmente).

### Server — o que enviar e quando

`_campaign_payload()` (usado em `game_state` e `city_state`) passa a incluir `story` (ou
`null`): um "beat" `{ "key": <id único>, "text": <texto> }`.

- **Abertura da fase (no `game_state`, fase `playing`):** `story` = beat de abertura da
  fase atual: `key = f"intro:{campaign_phase}"`, `text` = (abertura da campanha + "\n\n",
  só na fase 0 e se houver) + abertura da fase. Se não houver texto → `story = null`.
  Fica estável durante a fase; o cliente de-duplica por `key`.
- **Encerramento da fase (no `city_state`, após concluir):** transiente
  `self._campaign_outro` `{key,text}`, setado no avanço de `_check_objectives` **antes** de
  `_voltar_para_cidade()` com `key=f"outro:{fase_concluida}"`, `text` = encerramento da fase
  concluída. `_campaign_payload` o expõe como `story` enquanto na cidade; limpo na próxima
  `enter_dungeon`. A saída pela escada (sem concluir) **não** seta outro.
- **Final da campanha (no `game_over`):** ao concluir a última fase, antes de
  `end_game(victory=True)`, montar o texto final = encerramento da última fase + "\n\n" +
  final da campanha (se houver) e enviá-lo no `game_over` (campo `story`). `end_game` ganha
  um parâmetro opcional `story=None` incluído no broadcast `game_over`.

### Cliente — exibir e fechar

- `gameState.js`: getter `campaignStory()` que devolve o beat atual de
  `gameState.campaign.story` / `cityState.campaign.story` / o `story` do `game_over`; um
  conjunto `_storyShown` (Set de `key`) marcando os já vistos; `marcarStoryVista(key)`.
- `game.js`: quando chega um beat com `key` não vista, abre uma **tela de história**
  (overlay) com o `text` e um botão **"Continuar"**; ao fechar, `marcarStoryVista(key)`.
  Overlay puramente local (cada jogador o seu); o jogo segue atrás. Segue estado-vs-render
  do CLAUDE.md.

---

## 3. Índice de masmorras gerado (`tools/editor_dungeons.js`)

Estender `tools/export_catalog.py` para também escrever:

```javascript
window.EDITOR_DUNGEONS = [
  { "file": "fase1.json", "id": "...", "name": "...", "defn": { /* masmorra completa */ } },
  ...
];
```

- `build_dungeons_index()`: varre `DUNGEONS_DIR`, inclui só masmorras **válidas**
  (`validar_dungeon`), com `file`/`id`/`name`/`defn` (defn = dict carregado).
- `write_dungeons_js(destino)`: atribuição global (como `editor_catalog.js`).
- O `__main__` de `export_catalog.py` escreve os **dois** (catálogo + índice). Rodar ao
  criar/editar masmorras.
- O `defn` embutido habilita dropdown, mini-mapa e "abrir no editor" **offline**.

---

## 4. Abas no `editor.html`

Seletor de abas no topo (sempre visível): **Masmorra | Campanha**. Mostrar/esconder blocos
por aba:
- **Masmorra** (atual): `#dungeon-controls` (id/nome/grid/resize/carregar/salvar) +
  `#toolbar` + `#workspace`.
- **Campanha**: `#campaign-controls` (id/nome + abertura/final da campanha + Carregar/Salvar) +
  `#campaign-add` (dropdown "+ adicionar fase" + botão) + `#campaign-list`.
- `#statusbar` compartilhado (status da aba ativa).

Includes: `editor_dungeons.js` (gerado) e `editor_campaign.js` após os atuais.
`setTab('masmorra'|'campanha')` alterna visibilidade e status; coordenação por globais
(`window.EDITOR`, `window.EDITOR_CAMPAIGN`, `window.setTab`).

---

## 5. Lógica da campanha (`tools/editor_campaign.js`)

Estado: `C = { id, name, intro:"", outro:"", dungeons:[ {file,intro,outro}, … ] }`.
`DUN = window.EDITOR_DUNGEONS || []`.

Expostas em `window.EDITOR_CAMPAIGN`:
- `dunByFile(file)` → entrada do índice ou null.
- `renderCampaign()` — `#campaign-controls` (id/nome + textareas abertura/final da campanha,
  ligados a `C`); dropdown de adicionar (de `DUN`, `name — file`); `#campaign-list`: por
  fase, um cartão com handle de arrastar, índice, **mini-mapa** (canvas), `name`/`file`
  (ou `file` + "(não encontrada)"), **textareas abertura/encerramento da fase**, e botões
  **abrir** / **↑** / **↓** / **remover**.
- `drawMiniMap(canvas, defn)` — tiles (WALL/FLOOR/DOOR) escalados + um ponto por entidade.
- `addPhase(file)` / `removePhase(i)` / `movePhase(i, dir)` + drag-and-drop → mutam
  `C.dungeons` e re-render.
- `openInEditor(file)` — `EDITOR.loadJSON(dunByFile(file).defn)` + `setTab('masmorra')`.
- `validarCampanhaEditor()` → `{ok, erros}`: id/nome não vazios; `≥1` fase; todo `file`
  existe em `DUN`. `updateCampaignStatus()` mostra status e **bloqueia salvar**.
- `saveCampaign()` — valida; monta `{schema_version:1, id, name, intro, outro,
  dungeons:[{file,intro,outro}, …]}` (omitindo intro/outro vazios é opcional), download
  `<id>.json` (mover para `campaigns/`).
- `loadCampaign()` — upload de `campaign.json` → normaliza itens (string|objeto) para
  `{file,intro,outro}`, repovoa `C`; re-render (nome/mini-mapa do índice ao casar `file`).

---

## 6. Estilos (`tools/editor.css`)

Abas (ativo/inativo); `#campaign-controls`/`#campaign-add`; cartões de `#campaign-list`
(mini-mapa + texto + textareas + botões); estado "arrastando"; a **tela de história**
(`#story-overlay`) em `game.css` (overlay centralizado, texto, botão Continuar). Seguem os
temas existentes (editor escuro; jogo).

---

## 7. Arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | `validar_campanha`/`enter_dungeon` aceitam string\|objeto; `_fase_file`; `_campaign_payload` com `story`; outro em `_check_objectives`; `end_game(story=...)` no `game_over` |
| `src/gameState.js` | Modificar | `campaignStory()`/`_storyShown`/`marcarStoryVista` |
| `game.js` | Modificar | tela de história (overlay + Continuar) |
| `game.css` | Modificar | estilo do `#story-overlay` |
| `tools/export_catalog.py` | Modificar | também gerar `editor_dungeons.js` |
| `tools/editor_dungeons.js` | Gerado | `window.EDITOR_DUNGEONS` |
| `tools/editor.html` | Modificar | abas + blocos de campanha + includes |
| `tools/editor.css` | Modificar | abas + lista de campanha |
| `tools/editor_campaign.js` | Criar | estado/render/validação/IO/drag/história da campanha |
| `tools/editor.js` | Modificar (mínimo) | `setTab` / cooperação de abas |
| `tools/test_export_catalog.py` | Modificar | cobrir o índice de masmorras |
| `tools/test_campanha.py` | Modificar | história no runtime + schema string\|objeto |

---

## 8. Teste

- **Schema retrocompat (server):** `validar_campanha` aceita item string e objeto;
  recusa objeto sem `file` válido; campanha 4a antiga (lista de strings) continua válida.
- **Runtime da história:** entrar na fase → `game_state.campaign.story` traz a abertura
  (fase 0 inclui a abertura da campanha); concluir fase não-final → `city_state.campaign.story`
  traz o encerramento; concluir a última → `end_game` chamado com `story` (encerramento da
  fase + final da campanha). Saída pela escada (sem concluir) → sem outro. (Headless.)
- **Gerador do índice (Python):** `build_dungeons_index` inclui só válidas com
  `file/id/name/defn`; `editor_dungeons.js` começa com `window.EDITOR_DUNGEONS =` e o payload
  é JSON válido.
- **Round-trip:** `campaign.json` com história (formato do editor) passa em `validar_campanha`.
- **Editor (navegador, `python -m http.server 8077`):** aba Campanha → adicionar 2 fases,
  ver mini-mapas, escrever aberturas/encerramentos (campanha + fases), reordenar (↑/↓ e
  arrastar), validar (verde), salvar (baixa `campaign.json` válido), recarregar, "abrir no
  editor" (carrega a masmorra). Jogo: a tela de história aparece na abertura da fase e no
  encerramento, cada jogador fecha a sua, sem travar. Console sem erros.

---

## 9. Fora de escopo

Ramificações de fase; servir/escrever em `campaigns/`/`dungeons/` por endpoint (continua
download/upload); formatação rica nos textos de história (texto simples, quebras de linha).

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Mudar o schema quebrar campanhas 4a existentes | Itens string continuam aceitos; `validar_campanha`/`enter_dungeon` normalizam; teste com campanha antiga. |
| História repetir a cada `game_state` | Beats têm `key`; cliente de-duplica em `_storyShown`. |
| Outro aparecer em saída normal pela escada | `_campaign_outro` só é setado no avanço por conclusão; limpo na próxima `enter_dungeon`. |
| Índice desatualizado vs. masmorras criadas | Gerador é a fonte; rodar `export_catalog.py` ao criar/editar; aba mostra "(não encontrada)". |
| `editor_dungeons.js` grande (defn por masmorra) | Aceitável (ferramenta DEV local); não vai para o jogo. |
| Acoplar `editor.js` ↔ `editor_campaign.js` | Interface mínima por globais; `editor.js` segue focado na masmorra. |
| Tela de história travar o jogo | Overlay local, não-bloqueante; servidor nunca espera; cada jogador fecha a sua. |
