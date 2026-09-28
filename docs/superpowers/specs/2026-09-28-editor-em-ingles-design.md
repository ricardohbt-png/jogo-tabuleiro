# Editor em inglês (PT/EN) — design

Data: 2026-09-28

## Objetivo

Traduzir a interface do editor (`tools/editor.html` + os módulos `tools/*.js`) para PT/EN,
reusando o motor de idioma do jogo (`src/i18n.js` + `src/lang/*.js`). O jogo já está 100%
traduzido; o editor não carrega o motor nem tem seletor de idioma.

Tamanho medido (`js_strings`, textos de interface em português):
`editor.js` 306, `editor_monster_editor.js` 272, `editor_items_editor.js` 234,
`editor_city.js` 146, `editor_world.js` 48, `editor_items_logic.js` 40,
`editor_bestiary.js` 39, `editor_scenes.js` 37, `editor_campaign.js` 30,
`story_upload.js` 26, `editor_preview_3d.js` 19, `editor_story.js` 10 — **~1.200**.
Mais ~300 mensagens de validação/salvamento devolvidas pelo servidor.

## Decisões

1. **Fatiamento:** Fase 0 (infraestrutura) → uma aba por fase, das maiores para as menores →
   fase final das mensagens do servidor. Cada fase é commitada e testada; o editor segue
   utilizável em qualquer ponto, com o que falta em português.
2. **Nomes de catálogo** (monstros, itens, decorações, armadilhas, magias) exibidos no editor
   são traduzidos pelo id, quando existe chave `cat.*`. Conteúdo do autor (itens e monstros
   personalizados) não tem chave e mantém o nome dele.
3. **Mensagens do servidor** (validação e salvamento) ficam para a **fase final**.
4. **Troca de idioma:** `t()` nos templates + redesenho da aba ativa por `setTab(abaAtual)`,
   que já reconstrói cada aba a partir do estado do módulo (rascunhos sobrevivem, como já
   sobrevivem à troca de aba). Descartados: tudo por `data-i18n` (muita marcação, diverge do
   jogo) e recarregar a página (perde o que não foi salvo).

## Fase 0 — infraestrutura

**`src/lang/editor.js`** (novo, mantido à mão): `window.LANG_EDITOR = {…}` +
`Object.assign(window.LANG_STRINGS, window.LANG_EDITOR)`, como `interface.js`. Convenção de
chave: `ui.editor.<aba>.<slug>`; a moldura usa `ui.editor.topo.*`. Por morar em `src/lang/`,
o servidor também o carrega (`_load_lang` funde todos os `.js` da pasta) — útil na fase final.

**`tools/editor_i18n.js`** (novo) — a cola do editor com o motor, espelho do que o `game.js`
faz no jogo:
- `t(chave, params)` global (atalho para `I18N.t`);
- `_edI18nApply(raiz)`: aplica `[data-i18n]`, `[data-i18n-title]`, `[data-i18n-ph]`;
- idioma lido e gravado em `localStorage['lfh_lang']` (mesma chave do jogo; o editor é servido
  pelo mesmo servidor, em `/tools/editor.html`, logo mesma origem), com `try/catch`;
- `nomeCat(familia, id, padrao)`: devolve o nome traduzido se existir `cat.<familia>.<id>.nome`,
  senão `padrao`;
- `trocarIdioma(code)`: `I18N.setLang`, grava `lfh_lang`, reaplica `_edI18nApply(document.body)`
  e chama `setTab(abaAtual)`.

**`tools/editor.html`:** carrega `../src/lang/strings.js`, `catalogo.js`, `composto.js`,
`interface.js`, `editor.js` (dicionário), `../src/i18n.js` e `editor_i18n.js` **antes** dos
módulos, no mesmo `document.write` com cache-buster. Ganha o seletor 🌐 PT/EN na barra
superior; abas, botões do topo e `<title>` ganham `data-i18n`.

**`tools/editor.js`:** `setTab` guarda a aba atual (`window._abaAtualEditor`) para o redesenho.

**`tools/test_editor_idioma.py`** (placar do editor):
- conta, por arquivo e por função de topo, os textos em português restantes nos módulos do
  editor (reusa `js_strings.parece_portugues`; exclui gerados: `editor_catalog.js`,
  `editor_dungeons.js`, `editor_*_custom.js`, e os `test_*`);
- conjunto `FECHADAS` (arquivos/funções já traduzidos) é **cobrado**; o resto é relatado;
- acusa chave `ui.editor.*` usada em `tools/*.js`/`editor.html` e ausente do dicionário;
- paridade de `{parâmetros}` entre `pt` e `en` em `src/lang/editor.js`;
- varre `t` sombreado (`const|let|var t =` local) e `t(` num `const` de nível de módulo.

**Conferência:** abrir o editor pelo servidor em inglês (cache-buster), alternar PT↔EN numa
aba com rascunho aberto; o rascunho continua, a moldura muda, o console fica sem erro.

## Fases 1…N — uma aba por vez

Ordem: **Masmorra** (`editor.js`) → **Editor de criaturas** → **Editor de itens**
(`editor_items_editor.js` + `editor_items_logic.js`) → **Cidade** → **pequenas juntas**
(Mapa do Mundo, Campanha, Cenas, Bestiário, `editor_story.js`, `story_upload.js`,
`editor_preview_3d.js`).

Método de cada fase:
1. Antes de traduzir, procurar **lógica decidida por texto em português** (comparar rótulo de
   `<select>` em vez do valor, mapas chaveados por nome); trocar por id.
2. Texto de template → `t('ui.editor.<aba>.<slug>', {params})`; idem `alert`/`confirm`/
   `prompt`, `title`, `placeholder`.
3. Nomes de catálogo exibidos → `nomeCat`.
4. Ao fechar a aba, ela entra em `FECHADAS` no placar.
5. Conferência no navegador em inglês, varrendo o DOM da aba atrás de português restante —
   zero no placar não prova tradução completa.

**Fica em português de propósito:** conteúdo autoral (nomes de masmorras, salas, falas, NPCs,
itens e monstros criados) e todo valor gravado nos JSON (ids, enums como `"agua"`, `"visit"`)
— só o rótulo exibido muda.

## Fase final — mensagens do servidor ao editor

- `tools/story_upload.js` (conexão WebSocket do editor) passa a mandar `set_lang` ao abrir e a
  cada troca de idioma.
- As ~300 mensagens de `validar_dungeon`, `_validate_custom_*`, `_save_*_upload` e afins migram
  para `T("erro.editor.<slug>", …)` pelo método da etapa 4a (slug do texto, dedupe por
  construção), com o `en` em `src/lang/editor.js`.
- `tools/dividas.py` passa a cobrá-las.

## Riscos conhecidos

- **`t` sombreado** e **`t()` em `const` de nível de módulo** (TDZ): quebram em runtime sem
  nenhum teste pegar — o placar varre os dois.
- Servidor rodando trava a escrita de arquivos; `node --check` após escrita falha dá falso verde.
- Cache do navegador falseia a prova — sempre cache-buster e conferir que a versão nova carregou.
- `editor_catalog.js`/`editor_dungeons.js` são gerados: nunca traduzir dentro deles.
- `game.js`, `server.py` e `CLAUDE.md` estão em CRLF.

## Fora de escopo

Conteúdo autoral, nomes de cidade/aventura criados nos editores, e qualquer mudança de
comportamento do editor além da troca de texto por chave (exceto trocar lógica decidida por
texto em português por id, quando achada).
