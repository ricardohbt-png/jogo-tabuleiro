# História em slides com imagens e áudio — Design

**Data:** 2026-06-22
**Branch sugerida:** `feat/historia-slides-imagens-audio`

## Objetivo

Hoje os campos de história da campanha (`intro`/`outro` da campanha e de cada fase)
são apenas texto puro, exibidos num overlay simples (`renderStory` em `game.js`).

Queremos permitir, no editor de campanhas, montar uma **sequência de slides**, cada um
com **texto e/ou imagem de fundo**, e uma **música curta em loop** tocando ao fundo
enquanto a história aparece — para contar a abertura/encerramento como uma história
ilustrada. Inclui um **botão de pré-visualização** no editor.

Decisões já tomadas com o usuário:

- **Layout do slide em jogo:** imagem ocupa a tela inteira, texto sobreposto na parte
  de baixo sobre um escurecido (layout "A", cinematográfico).
- **Origem das imagens/áudios:** arquivos numa pasta servida pelo jogo (`assets/story/`),
  referenciados por caminho relativo. Nada de base64 embutido (evita peso no broadcast,
  que reenvia a história a cada atualização de estado — ver `_campaign_payload`).
- **Escopo:** os 4 campos de história ganham slides — `intro`/`outro` da campanha e
  `intro`/`outro` de cada fase.
- **Conteúdo do slide:** texto e imagem são **independentes** (slide pode ter só texto,
  só imagem, ou os dois).
- **Ajuste da imagem:** configurável **por slide** — `cover` (cobrir, padrão) ou
  `contain` (imagem inteira, fundo escuro nas sobras).
- **Áudio:** propriedade **da sequência** (não do slide); toca em loop com fade enquanto
  a história está aberta; botão 🔊/🔇 no overlay.

## Modelo de dados (arquivo de campanha `.json`)

Cada campo de história (`campaign.intro`, `campaign.outro`, `dungeons[i].intro`,
`dungeons[i].outro`) passa a aceitar **dois formatos**:

1. **String** (legado) — exatamente como hoje; equivale a um único slide só de texto,
   sem áudio. Campanhas existentes continuam válidas.
2. **Objeto rico:**
   ```json
   {
     "slides": [
       { "text": "A névoa engole a cripta...", "image": "assets/story/cripta.png", "fit": "cover" },
       { "text": "Só uma narração, sem imagem." },
       { "image": "assets/story/mapa.png", "fit": "contain" }
     ],
     "audio": "assets/story/tema_cripta.mp3"
   }
   ```
   - `slides`: lista (≥1). Cada slide: `text` (str, opcional), `image` (str, opcional,
     caminho relativo dentro de `assets/`), `fit` (`"cover"` | `"contain"`, default
     `"cover"`). Pelo menos um de `text`/`image` deve estar presente.
   - `audio`: str opcional (caminho relativo dentro de `assets/`).

`schema_version` continua `1`.

### Pasta de assets

Nova pasta `assets/story/` para imagens (png/jpg/webp) e áudios (mp3/ogg). Já é servida
pelo servidor — `_STATIC_ROOTS = ("src", "assets")` em `server.py` cobre subpastas
recursivamente, então **não há mudança no servidor de estáticos**. Criar a pasta com um
`.gitkeep`.

## Servidor (`server.py`)

### Normalização

Hoje `_fase_obj`/`_fase_file` (linhas ~1859) normalizam fase para `{file, intro, outro}`
com `intro`/`outro` como string. Introduzir um normalizador de história:

```python
def _story_norm(val):
    """Normaliza um campo de história para {'slides': [...], 'audio': str|None}.
    Aceita string (legado) ou objeto {'slides', 'audio'}. Retorna estrutura vazia
    se val for falsy."""
```

- string `s` (não vazia) → `{"slides": [{"text": s}], "audio": None}`
- string vazia / `None` → `{"slides": [], "audio": None}`
- objeto → slides saneados (cada slide com `text`/`image`/`fit`, `fit` default `cover`)
  + `audio`.

### Montagem do "beat" (`_campaign_payload` ~12219 e bloco de vitória ~12117)

A lógica atual concatena texto (`campaign.intro` + fase 0 `intro`; no final, fase
`outro` + `campaign.outro`). Passa a concatenar **listas de slides**, mantendo a mesma
ordem:

- **Abertura** (`phase == "playing"`): slides = `_story_norm(campaign.intro).slides`
  (só na fase 0) **+** `_story_norm(fase.intro).slides`.
- **Encerramento de fase** (cidade, `_campaign_outro`): slides de `_story_norm(fase.outro)`.
- **Final da campanha** (`game_over`): slides de `_story_norm(fase.outro)` **+**
  `_story_norm(campaign.outro).slides`.

O **áudio** do beat = primeiro `audio` não-nulo entre as partes, **na ordem da
concatenação** (abertura: campanha antes da fase; final: fase antes da campanha).

O beat enviado passa de `{key, text}` para:
```python
{"key": "...", "slides": [...], "audio": "assets/story/..."|None}
```
Beats só são incluídos quando há ao menos 1 slide (mantém `story: None` caso contrário).

### Validação (`validar_campanha` ~1866)

Para cada campo de história (campanha e fase): aceitar string **ou** objeto. Se objeto:

- `slides` deve ser lista; cada item objeto com `text`/`image` strings (se presentes),
  `fit` em `{"cover","contain"}` (se presente), e ao menos um de `text`/`image`.
- `audio`, se presente, deve ser string.

Mensagens de erro no padrão das existentes (em português, indicando campanha/fase).
Não valida existência do arquivo de imagem/áudio em disco (igual ao resto: caminho solto;
se faltar, o cliente degrada — ver abaixo).

## Editor de campanhas (`tools/editor_campaign.js`, `tools/editor.html`, `tools/editor.css`)

### Estado interno

`C.intro`/`C.outro` e cada fase em `C.dungeons[i]` (`intro`/`outro`) passam a guardar a
**estrutura normalizada** `{slides:[...], audio:null}` em memória (helpers de
conversão de/para o formato salvo). `faseObj` é estendido para normalizar história.

### UI

Substituir os `<textarea>` minúsculos de `abertura`/`final` (em `renderControls` para a
campanha e em `renderList` para cada fase) por um **botão** `📖 história (N)` (N = nº de
slides; some/zera quando vazio). São 4 botões no total (campanha intro/outro + por fase
intro/outro).

Clicar abre um **painel editor de história** (modal/overlay dentro do editor):

- **Cabeçalho:** título do contexto (ex.: "abertura da fase 1"), contador de slides e
  botão **▶ pré-visualizar**.
- **Faixa de áudio:** rótulo 🎵 `áudio (loop)`, botão `escolher`, nome do arquivo
  selecionado e `✕` para remover.
- **Lista de slides:** cada slide num cartão com: botão de imagem + miniatura + nome do
  arquivo, alternador `cobrir`/`inteira`, `<textarea>` de texto, e ↑ ↓ ✕.
- **+ adicionar slide.**
- **Rodapé:** botão `fechar`.
- **Aviso:** "imagens e áudios precisam estar na pasta `assets/story/` do jogo."

### Seleção de arquivo (imagem/áudio)

`<input type="file">` (browser puro). Ao escolher:

- Guarda o caminho salvo como `assets/story/<file.name>`.
- Mantém em memória uma **URL de objeto** (`URL.createObjectURL`) do arquivo escolhido,
  usada **só para preview no editor** (miniatura e pré-visualização), nunca salva no JSON.
- Campo de caminho editável também é aceito (caso o arquivo já esteja na pasta e o usuário
  prefira digitar o nome).

### Salvar (`saveCampaign`)

Para cada campo de história:

- Sequência vazia → omite o campo.
- 1 slide, só `text`, sem `audio` → grava **string** (mantém JSON enxuto e compatível).
- Caso contrário → grava objeto `{slides:[...], audio?}` com apenas os campos não-vazios
  por slide (`fit` omitido quando `cover`).

Os caminhos salvos são sempre os `assets/story/...` (as URLs de objeto de preview são
descartadas).

### Carregar (`loadCampaign`)

Normaliza string/objeto para a estrutura interna. Imagens/áudios carregados de um JSON
existente **não têm blob em memória**: a miniatura/preview tenta carregar pelo caminho
relativo (funciona se o editor estiver sendo servido junto dos assets; senão mostra
"imagem na pasta assets/story/" como fallback, sem quebrar).

### Pré-visualização (no editor)

Um slideshow **autossuficiente no editor** (o editor não carrega `game.js`), reproduzindo
o layout A: camada de imagem (cover/contain) + escurecido + texto embaixo + pontinhos +
`Continuar` (avança) / `‹ voltar` / último slide fecha. Toca o áudio em loop (do blob, se
escolhido na sessão). Fonte das imagens: blob em memória quando disponível, senão o
caminho relativo. É uma função pequena e isolada (`previewStory(seq)`); duplicação
consciente da lógica de jogo, aceitável para uma ferramenta de DEV.

## Cliente em jogo

### `src/gameState.js`

`_captarStory`/`pendingStory`/`marcarStoryVista` (linhas ~1145) já tratam um beat
`{key,...}` com de-dup por `key`. Ajuste: o beat agora carrega `slides` e `audio` (em vez
de `text`). `pendingStory()` devolve o beat com `slides`/`audio`. Sem outra mudança de
lógica (continua local por cliente — cada jogador navega seus próprios slides).

### `game.js` — `renderStory` (~971)

Vira um **slideshow** (layout A):

- Overlay full-screen; índice do slide atual em estado de UI local.
- **Camada de imagem:** `background-image` do `slide.image` (resolvido para a URL servida
  pelo mesmo host); `background-size: cover` ou `contain` conforme `slide.fit`;
  `background-position: center`. Se não houver imagem (ou falhar ao carregar), fundo
  escuro liso.
- **Escurecido** por cima da imagem; **texto** (via `textContent`, sem HTML) na parte de
  baixo. Slide sem texto → sem caixa.
- **Controles:** pontinhos (slide atual destacado), `Continuar` (avança; no último,
  marca o beat visto via `marcarStoryVista` e fecha), `‹ voltar` (recua, oculto no
  primeiro), e **🔊/🔇** (mudo).
- **Áudio:** ao abrir, se `beat.audio`, cria/usa um `<audio loop>` apontando para o
  caminho, com fade-in suave (volume modesto); ao fechar, fade-out e pausa. Autoplay:
  como o overlay surge após interações do jogador, normalmente toca; se bloqueado, começa
  no primeiro clique. Estado de mudo persiste durante a sessão.
- **Pré-carregamento:** pré-carrega as imagens dos slides ao abrir (evita flash ao
  avançar). Transição entre slides: fade simples.

### `game.css` (~741)

Estender os estilos de `#story-overlay`/`#story-box` para o layout A: camada de imagem,
escurecido, posicionamento do texto na base, pontinhos, botões (Continuar/voltar/mudo).

## Degradação e segurança

- Imagem/áudio ausente na pasta → não quebra: imagem falha silenciosamente (fundo
  escuro), áudio simplesmente não toca. O texto sempre aparece.
- Texto sempre inserido via `textContent` (sem injeção de HTML).
- Caminhos referenciam apenas `assets/...`, que o servidor já protege contra path
  traversal (`_serve_static`).

## Fora de escopo (YAGNI)

- Vídeo, narração por palavra, transições elaboradas, múltiplas faixas/cross-fade entre
  fases, upload automático dos arquivos para `assets/story/` (o usuário copia os arquivos
  manualmente).

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `assets/story/.gitkeep` | nova pasta para imagens/áudios |
| `server.py` | `_story_norm`; `_campaign_payload` e bloco de vitória montam slides+audio; `validar_campanha` aceita string/objeto |
| `tools/editor_campaign.js` | estado normalizado, botões `📖 história`, painel editor de slides, seleção de arquivo, áudio, preview, save/load |
| `tools/editor.html` / `tools/editor.css` | markup/estilos do painel e do preview |
| `src/gameState.js` | beat carrega `slides`/`audio` |
| `game.js` | `renderStory` vira slideshow layout A + áudio + controles |
| `game.css` | estilos do slideshow (imagem, escurecido, pontinhos, botões) |

## Critérios de aceitação

1. Campanha antiga (com `intro`/`outro` em string) continua válida e roda como 1 slide
   só-texto.
2. No editor, é possível montar uma sequência de slides com imagem+texto, alternar
   cobrir/inteira, reordenar/remover, escolher um áudio de loop e pré-visualizar.
3. Ao salvar, o JSON usa string para slide único só-texto e objeto `{slides, audio}` caso
   contrário; só grava caminhos `assets/story/...`.
4. Em jogo, abertura/encerramento aparecem como slideshow (layout A), com áudio em loop e
   botão de mudo; navegar avança/recua; o último "Continuar" fecha e não reaparece.
5. Imagem/áudio ausente degrada sem quebrar; texto sempre visível.
