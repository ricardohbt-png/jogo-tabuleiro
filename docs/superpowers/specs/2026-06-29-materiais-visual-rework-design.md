# Materiais — rework visual + UX do editor — Design

**Data:** 2026-06-29
**Branch:** `worktree-feat+materiais-piso-parede` (continuação; já mesclada uma vez em `feat/miniatura-png-objetos`)
**Status:** aprovado para escrever o plano

## Contexto

A camada de materiais (chão/parede pintável por casa) já existe e foi mesclada.
Ao testar, o usuário apontou:
1. Grama e terra aparecem como **pedra recolorida** (lajota + tint leve), não como
   grama/terra de verdade.
2. A escolha do material deve acontecer **junto** da ferramenta chão/parede (não numa
   ferramenta "material" separada).
3. Parede de caverna deve ter **pedra irregular**; parede enegrecida deve ser **tijolo
   preto**.

Esta entrega é **100% client-side**: `game.js` (render 2D e 3D), possivelmente
`src/visualConfig.js`, e `tools/editor.js` (UX). **Sem mudanças no servidor, no
protocolo, no modelo de dados ou nos ids de material** — as masmorras existentes
continuam válidas e renderizam com o novo visual.

## Decisões (confirmadas com o usuário)

- **Vistas:** refazer o visual no **jogo 2D e 3D**. A prévia do editor mantém a cor
  chapada do swatch (não é refeita agora).
- **Abordagem:** **procedural** (canvas no 2D; texturas de canvas geradas e cacheadas
  no 3D). Sem assets PNG externos — coerente com o resto do jogo, que é todo
  procedural. (Alternativa de PNGs descartada: exige arte inexistente e quebra a
  consistência.)
- **UX do editor:** a ferramenta **"material" é removida**. A ferramenta **chão**
  ganha um dropdown de pisos; a **parede** ganha um dropdown de paredes **+ entulho**.
  Pintar já coloca com o material escolhido. **Balde** mantido nas duas.
- **Direção de arte (aprovada na prévia):** grama = gramado verde com tufos (sem grade
  de pedra); terra = solo marrom mosqueado com seixos; pedra negra = lajota escura;
  pedra de caverna = pedras irregulares; enegrecida = tijolo preto; desmoronada =
  escombros; pedra cinza/normal = lajota/tijolo atuais (referência).

## Render 2D (`game.js`)

Hoje `drawFloor3D`/`drawWallTop3D`/`drawWallSouthFace` recebem `matId` e só trocam a
cor base. Passam a **despachar por estilo** do material:

- **Pisos** (`drawFloor3D` por estilo, lido de `MAT_PALETTE_2D[matId].accent`):
  - `stone` (pedra_cinza, pedra_negra): lajota atual, só muda a cor base.
  - `grass` (grama): **novo** — base verde (gradiente vertical), manchas tonais e
    ~150 lâminas de grama curtas em verdes variados; **sem grade de pedra**.
  - `dirt` (terra): **novo** — base marrom, manchas mosqueadas claras/escuras, seixos
    com sombra; **sem grade**.
  - `rubble` (entulho): base de lajota + monte de escombros (já existe `drawEntulho2D`).
- **Paredes** (`drawWallTop3D`/`drawWallSouthFace` por estilo):
  - `brick` (pedra_normal, enegrecida): fileiras de tijolos com argamassa; a cor base
    define cinza vs **tijolo preto** (enegrecida ~quase preto com argamassa legível e
    leve realce no topo de cada tijolo).
  - `cave` (pedra_caverna): **novo** — pedras **irregulares** (blocos poligonais
    orgânicos com gaps escuros e realce de tocha), não fileiras.
  - `rubble` (desmoronada): escombros.

Implementação: funções de desenho focadas por estilo (ex.: `drawFloorGrass2D`,
`drawFloorDirt2D`, `drawWallBrick2D`, `drawWallCave2D`, `drawWallRubble2D`),
despachadas pelos passes de render conforme o `accent` do material. `MAT_PALETTE_2D`
ganha os campos necessários (base + accent + cor de argamassa/gaps por estilo).

## Render 3D (`game.js` + `VC`)

Hoje o 3D só tinge a textura de pedra compartilhada com `VC.materiais[id].color`.
Passa a usar **uma textura de canvas por material, gerada e cacheada**:

- `makeMaterialTex(matId)` retorna um `THREE.CanvasTexture` (cache por id) desenhado
  com os **mesmos algoritmos** do 2D (grama, terra, lajota, tijolo, tijolo preto,
  pedra de caverna, escombros). Tamanho 256–512, `RepeatWrapping`.
- No laço de construção dos tiles 3D: o mesh de chão usa `floorBaseMat.clone()` com
  `map = makeMaterialTex(mid)` (cor neutra, a aparência vem da textura); idem parede.
  O entulho (bloco) usa a textura de escombros.
- Contagem de luzes/materiais-base permanece estável (clones por casa já existem); só
  o `map` muda por material. Texturas são compartilhadas via cache (uma por id).
- `VC.materiais[id].color` continua como **fallback/tonalização** se quisermos um
  multiplicador, mas a identidade visual passa a vir da textura.

## Editor (`tools/editor.js`)

- **Remover** a ferramenta `material` de `TOOLS`.
- Estado: `S.matFloor` (material do chão atual) e `S.matWall` (material da parede
  atual), em vez do `S.matId` único. `S.matFill` (balde) mantido.
- `buildToolbar`: quando `S.tool==='floor'`, mostra dropdown de pisos
  (`pedra_cinza`/`terra`/`grama`/`pedra_negra`) + botão balde; quando
  `S.tool==='wall'`, dropdown de paredes (`pedra_normal`/`enegrecida`/`pedra_caverna`/
  `desmoronada`/`entulho`) + balde.
- Pintura:
  - chão com material M (piso, ≠ entulho): `tiles=FLOOR`; material = M (ou limpa se M
    for o default `pedra_cinza`).
  - parede com material M (parede): `tiles=WALL`; material = M (ou limpa se default
    `pedra_normal`).
  - **parede com `entulho`** (caso especial): `tiles=FLOOR`; material = `entulho`
    (bloqueia mov+visão, mas estruturalmente é chão).
  - porta: inalterada (`DOOR`, sem material → default).
- **Balde**: preenche a região 4-conexa de mesma estrutura aplicando o material do
  tool (reusa a lógica de flood atual).
- Validação (`validarEditor`): inalterada na essência (piso só em chão/porta, parede só
  em parede; entulho é piso e válido em chão). A serialização/`buildJSON`/`loadJSON`
  do campo `materiais` **não muda**.

## Compatibilidade

- Modelo de dados e ids de material **inalterados** → masmorras existentes (incl.
  `dungeons/_teste_materiais.json`) continuam válidas e ganham o novo visual.
- Sem mudanças em `server.py`, protocolo ou testes de servidor (40/40 seguem válidos).

## Testes / verificação

- **Servidor:** nenhum (sem mudança). Rodar `tools/test_materiais.py` só para garantir
  que nada quebrou (deve seguir 40/40).
- **2D:** verificação visual via preview, renderizando cada material num canvas de
  showcase e conferindo por amostragem de pixels + screenshot (como já feito).
- **3D:** como o worktree não tem o bloco `ambientes` (está só na WIP do usuário), a
  cena 3D completa não roda aqui. Verifico as **texturas geradas** diretamente:
  desenho o `.image` (canvas) de cada `makeMaterialTex(id)` num showcase + screenshot +
  amostragem de pixels — independe da cena/iluminação. No setup mesclado do usuário (com
  `ambientes`) a vista 3D completa funciona.
- **Editor:** abrir o editor, confirmar que chão/parede têm dropdown, que pintar coloca
  o material, que entulho via parede vira chão-bloqueante, balde funciona, e save/load
  preservam `materiais`.

## Riscos

- **Perf 3D:** gerar textura por material **uma vez** (cache por id), nunca por casa.
- **Coerência 2D/3D:** os mesmos algoritmos alimentam os dois (extrair para funções
  reutilizáveis evita divergência de aparência).
- **Entulho no dropdown de parede** é o único caso cruzado de categoria — isolar o
  caso especial na pintura para não confundir estrutura (chão) com a UI (parede).
