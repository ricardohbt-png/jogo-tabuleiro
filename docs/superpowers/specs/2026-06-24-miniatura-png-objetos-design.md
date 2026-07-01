# Miniaturas PNG para decorações (pseudo-3D extrudado)

**Data:** 2026-06-24
**Branch:** feat/objetivos-recompensa-deletar-sala (ou nova branch dedicada)

## Objetivo

Permitir, no editor de masmorras, atribuir a cada **decoração** colocada uma
imagem PNG contida em `assets/objetos/`. No jogo, essa imagem é renderizada como
uma **miniatura pseudo-3D extrudada** (silhueta detectada pelo canal alfa), no
estilo de uma miniatura de tabuleiro. No 2D e no preview do editor, a imagem
aparece de forma plana. Decorações sem imagem mantêm o render procedural atual
(emoji no 2D, caixa/cilindro no 3D) como fallback.

Primeiro objeto de teste: a árvore (`arvore`), substituída por
`assets/objetos/arvore.png`.

## Decisões (do brainstorming)

| Pergunta | Decisão |
|---|---|
| Associação imagem↔objeto | **Por instância** no editor (campo `image` em cada decoração) |
| Onde renderizar a miniatura | Jogo **3D**, jogo **2D** e **preview do editor** |
| Técnica de extrusão | **Silhueta real**: alfa → contorno (marching squares) → `ExtrudeGeometry` |
| Como começar | **Demo HTML standalone** primeiro, depois integrar |
| Seletor no editor | **Lista automática** da pasta + **botão de upload** |
| Escopo de objetos | **Só decorações** (por enquanto) |
| Faces da miniatura | **Frente/verso com arte (PNG texturizado); laterais lisas** (cor plástica fosca derivada das bordas) |

## Estado atual (referência)

- Decorações: catálogo autoritativo `DECOR_TYPES` em `server.py` (~2121). Render
  2D = emoji; render 3D = caixas/cilindros procedurais via `DECOR_3D`
  (`game.js:240`) montados em `game.js:~12885`.
- A árvore: `DECOR_TYPES["arvore"]` (emoji 🌳, `alto=True`) e
  `DECOR_3D.arvore` (cilindro verde).
- `assets/` já é servido pelo servidor (`_STATIC_ROOTS` em `server.py:~13141`);
  logo `assets/objetos/arvore.png` já é acessível por URL.
- Editor (`tools/editor.js`) coloca decorações por `type`, painel de seleção
  existente; canvas 2D apenas (sem Three.js).
- Pipeline de upload já existente a espelhar: `_save_story_upload`
  (`server.py:~13160`) e upload de prisioneiro (`server.py:~13192`).

## Fase 0 — Demo standalone (`tools/test_miniatura.html`)

Página única, Three.js **r128** via CDN (mesma versão do jogo; r148+ removeu
`examples/js/`). Implementa e valida o pipeline antes de integrar.

Função central `pngParaMiniatura(url, opts)`:

1. Carrega o PNG; desenha num canvas offscreen **reduzido** (máx. ~128px no
   maior lado — `arvore.png` tem ~2 MB; reduzir é obrigatório para o contorno
   não travar).
2. Lê `ImageData`; monta máscara binária por limiar de alfa (configurável,
   default `alpha > 128`).
3. **Marching squares** traça o contorno externo (e buracos internos) →
   simplifica (Douglas–Peucker, tolerância configurável) → `THREE.Shape` com
   `holes`.
4. `THREE.ExtrudeGeometry` com `depth` correspondente a **5–8 mm** na escala do
   tabuleiro (constante derivada do tamanho do tile).
5. **Materiais por grupo de face:**
   - Frente/verso: `MeshStandardMaterial` com a **textura do PNG** (UV mapeado
     pelo bounding box da silhueta), `roughness` alto, `metalness` 0 (plástico
     fosco). `transparent`/`alphaTest` conforme necessário para o recorte.
   - Laterais (bevel/extrusão): cor **lisa** derivada da média dos pixels
     opacos próximos à borda da silhueta.
6. **Base oval** integrada (`CylinderGeometry` achatada ou elipse extrudada),
   cor derivada das bordas; a peça fica em pé sobre a base.
7. Geometria **centralizada na base** (translação para que a origem fique no
   centro da base, facilitando posicionar sobre o tile). Orientação: largura da
   imagem → X, altura → Y (para cima), espessura → Z.
8. Cena: `AmbientLight` + `DirectionalLight` (com `shadow`), `castShadow` e
   `receiveShadow` ativos, plano receptor de sombra, `OrbitControls`. A
   miniatura é um `Mesh` real — **gira junto com o mundo** ao orbitar a câmera,
   **sem** `sprite`/`lookAt(camera)`.

Validação: abrir `http://localhost:8765/tools/test_miniatura.html`, conferir o
visual da árvore (silhueta, faces com arte, laterais lisas, base, sombras,
rotação com o mapa). Só então prosseguir para a integração.

## Fase 1 — Modelo de dados + servidor (`server.py`)

- Decoração ganha campo **opcional** `image`: caminho relativo a `assets/`
  apontando para a pasta de objetos, ex.: `"objetos/arvore.png"`. Ausente →
  fallback procedural.
- `validar_dungeon`: aceitar e **sanitizar** `image` — deve ser string,
  terminar em `.png`, sem componentes de path traversal, e o arquivo deve
  existir sob `assets/objetos/`. Inválido → descartar o campo (degrada para
  procedural) sem rejeitar a dungeon.
- Nova mensagem WebSocket **`list_objetos`** (client→server) → resposta com a
  lista de PNGs em `assets/objetos/` (nomes/relativos). Usada pelo editor para
  popular o seletor.
- Nova mensagem **`objeto_upload`** (client→server), espelhando
  `_save_story_upload`: grava um PNG em `assets/objetos/`. Apenas `.png`,
  nome sanitizado, sem path traversal; responde com o caminho salvo.

## Fase 2 — Editor (`tools/editor.js`, `editor.html`, `editor.css`)

- Painel da decoração selecionada ganha seção **"Imagem"**:
  - Dropdown/miniaturas das opções listadas via `list_objetos`.
  - Botão **"Enviar PNG"** → `objeto_upload`; após sucesso, recarrega a lista e
    seleciona o novo arquivo.
  - Opção **"nenhuma (procedural)"** para limpar `image`.
- Selecionar uma imagem grava `image` na decoração; persiste no save da dungeon
  (`upload_dungeon`, já existente).
- **Preview 2D do editor:** quando a decoração tem `image`, desenhar o PNG
  cobrindo o footprint no lugar do emoji.
- Offline fallback: se `list_objetos`/`objeto_upload` não estiverem disponíveis
  (editor aberto sem servidor), manter o campo de digitação manual do nome do
  arquivo como degradação.

## Fase 3 — Render no jogo (`game.js`)

- Extrair o pipeline do demo para uma função reutilizável (camada de
  **renderização**, em `game.js`).
- **3D:** quando `d.image` existe, construir/cachear a miniatura extrudada
  (cache por string `image`; `dispose` de geometria/material/textura ao remover
  a decoração) e usá-la no lugar do `box`/`cyl` de `DECOR_3D`. Posicionamento,
  visibilidade e fog idênticos ao fluxo atual de `decorMeshes`.
- **2D:** quando `d.image` existe, desenhar o PNG no footprint no lugar do
  emoji.
- Sem `image` → comportamento atual 100% intacto.

## Conformidade com a arquitetura (CLAUDE.md)

- O campo `image` é **dado** (parte do conteúdo da dungeon; trafega no
  `game_state`/`gameState` quando aplicável e no JSON da dungeon). O servidor
  permanece autoritativo sobre o conteúdo.
- Todo o pipeline PNG→Mesh e o desenho 2D do PNG são **renderização** e ficam em
  `game.js`; nada de `THREE`/`canvas`/`document` em `gameState.js`.

## Testes

- `tools/test_decor_roundtrip.py`: estender para incluir `image` no round-trip
  salvar/carregar de decorações.
- Teste do servidor para `objeto_upload` e `list_objetos`: aceitar PNG válido,
  rejeitar não-PNG e tentativas de path traversal; `list_objetos` retorna apenas
  PNGs de `assets/objetos`.
- `validar_dungeon`: teste de sanitização do campo `image` (válido mantém,
  inválido degrada para procedural).
- Validação visual manual: demo standalone + in-game (árvore) em 2D e 3D.

## Não-objetivos (YAGNI)

- Imagens para monstros, baús, itens ou outros objetos (escopo só decorações).
- Edição/pintura da imagem dentro do editor.
- Animação da miniatura.
- Geração automática de base por outros formatos além de oval/circular.
