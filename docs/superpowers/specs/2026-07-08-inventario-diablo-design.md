# Inventário estilo Diablo — design

## Contexto

Hoje o equipamento/inventário do jogador vive em dois lugares separados e
duplicados:

- **Cidade**: `#ficha-cidade-panel` (`game.js`) — painel lateral deslizante
  com retrato/atributos/equipamento/inventário/técnicas da guilda, aberto
  clicando no retrato do herói na `#city-hero-bar`.
- **Masmorra**: `#side-panel` → `#my-panel` (`game.js`) — painel sempre
  visível com Ações/Habilidades/Equipamento/Inventário/Encerrar Turno,
  aberto no celular via FAB `🎒` (`#ficha-fab`, hoje mobile-only).

Ambos renderizam os mesmos 8 slots de equipamento (`EQ_SLOTS`) e a mesma
bolsa (`bag`) com lógica de drag-and-drop quase idêntica, mas duplicada.

Este projeto substitui as duas telas de Equipamento+Inventário por um
**modal único, estilo Diablo II/III**, reutilizado em cidade e masmorra,
mantendo intactas as partes que não são equipamento (atributos/guilda na
cidade; Ações/Habilidades/Encerrar Turno na masmorra).

## Escopo

**Dentro do escopo:**
- Modal de inventário/equipamento (paperdoll + bolsa + ouro).
- Novo slot de equipamento "Bota" (infraestrutura apenas — sem itens novos).
- Interação por clique-clique (tap-to-select) + drag nativo HTML5 como bônus
  no mouse.
- Tooltip com comparação de atributos (setas ↑/↓) ao equipar.
- Bloqueio visual de slot incompatível e de escudo quando há arma de duas
  mãos equipada.
- Abertura por ícone fixo de canto + tecla `I`; fechamento por X, clique
  fora, ou `Esc`.
- Visual ornamentado (mármore, borda dourada estilo pergaminho queimado,
  logotipo do jogo, slots em proporção retrato).

**Fora do escopo (explicitamente adiado):**
- Criar itens de bota novos no catálogo (só o slot fica pronto, vazio).
- Gerar arte/ícones PNG novos para os itens existentes (cada item ganha um
  campo `icon` opcional; sem ele, cai no emoji atual — arte fica pra um
  projeto separado).
- Mudar a capacidade base do inventário (`bag_size` continua 6; a lógica de
  aumento genérico via efeito `bagslots` já existe e é reaproveitada como
  está).
- Mover Atributos/Técnicas da Guilda pra dentro do modal novo (continuam no
  painel deslizante `#ficha-cidade-panel`, que encolhe pra conter só essas
  duas seções).

## Arquitetura

- **Novo arquivo `src/ui/inventoryModal.js`** — toda a renderização do modal
  (DOM/CSS puro, sem lógica de jogo), no mesmo espírito de `src/ui/theme.js`.
  Isola esse subsistema do resto de `game.js` (hoje com mais de 19 mil
  linhas) por tamanho/manutenção, mas continua sendo "renderer" na acepção
  do CLAUDE.md — `game.js` só importa e invoca `InventoryModal.open(pid,
  {readOnly})` / `InventoryModal.close()`.
- **`src/gameState.js`** — ganha duas funções puras novas:
  - `canPlaceItem(item, slotKey, gearSnapshot)`: checagem client-side de
    compatibilidade (pra feedback visual instantâneo). Espelha as regras do
    servidor (match de `item_slot`, categorias genéricas `ring`/`item`,
    conflito de duas mãos) mas **não é autoritativa** — o servidor sempre
    revalida.
  - `compareItemStats(newItem, equippedItem)`: calcula o diff de atributos
    pra tooltip (usado só quando há item equipado no mesmo slot).
  - Nenhuma mensagem de protocolo nova: reaproveita `GS.equipFromBag`,
    `GS.unequip`, `GS.reorderBag` já existentes.
- **`server.py`**:
  - `GEAR_SLOTS` ganha `"boots"`: `("weapon", "off_hand", "armor", "head",
    "boots", "ring1", "ring2", "item1", "item2")`.
  - Inicialização de `player["gear"]` ganha `"boots": None`.
  - Migração: personagens carregados de save antigo (`load_guild_save` /
    `apply_guild_save`) que não têm a chave `boots` em `gear` recebem
    `None` automaticamente ao carregar (chave ausente tratada como vazia
    nos pontos que já fazem `gear.get(key)`).
  - Nenhuma mudança nos handlers de equipar/desequipar além de reconhecer o
    slot novo — a validação de classe/duas-mãos já é genérica por slot.
- **`game.js`**:
  - Remove o bloco de Equipamento+Inventário de `renderFichaCidadeBody`
    (cidade) e de `renderMyPanel`/`#my-panel` (masmorra); ambos passam a
    chamar `InventoryModal.open(pid, {readOnly})`.
  - Ações/Habilidades/Encerrar Turno continuam exatamente como estão hoje,
    sempre visíveis no HUD da masmorra — o modal não os esconde nem
    substitui.
  - Novo listener de teclado pra tecla `I` (mesmo padrão do listener de
    `Escape` já existente), que abre/fecha o modal do próprio jogador.
  - Novo ícone fixo de canto (reaproveita/estende o `#ficha-fab` atual,
    hoje mobile-only, pra aparecer sempre — cidade e masmorra, desktop e
    mobile).

## Dados

- **9 slots de equipamento**: `weapon`, `off_hand`, `armor`, `head`,
  `boots`, `ring1`, `ring2`, `item1`, `item2`. `ring1`/`ring2` aceitam
  qualquer item com `item_slot:"ring"`; `item1`/`item2` aceitam qualquer
  item com `item_slot:"item"` (já genérico hoje — a mochila é só o primeiro
  exemplo desse tipo de efeito, o sistema lê `effect:"bagslots"` de
  qualquer item equipado, sem hardcode).
- **Capacidade do inventário**: `player.bag_size` (padrão 6, cresce via
  `bagslots`). Sem mudança de valor — só de apresentação.
- **Ouro**: `player.gold`, exibido sempre no topo do modal.
- **Arma de duas mãos**: `gear.weapon.two_handed === true` bloqueia
  visualmente o slot `off_hand` (a regra em si, `_conflito_duas_maos`, já
  existe no servidor e continua autoritativa).
- **Campo `icon` opcional por item**: caminho de imagem (ex.:
  `assets/items/espada_longa.png`). Ausente → cai no emoji atual
  (`item.emoji`). Não populado nesta entrega.

## Interação

- **Clique-clique universal (tap-to-select)**: clicar num item da bolsa ou
  de um slot equipado seleciona/destaca; clicar num slot de destino tenta
  mover. Funciona idêntico em mouse, touch e iOS/Capacitor.
- **Drag nativo HTML5** ativo em paralelo, só reage a mouse (touch/Capacitor
  ignoram o atributo `draggable`, então não há conflito).
- **Feedback de incompatibilidade**: ao selecionar/arrastar um item sobre um
  slot incompatível, `canPlaceItem` pinta o slot de vermelho/cruzado em
  tempo real. Rejeição real (quando o cliente erra a previsão) vira toast
  via mensagem `error` já existente do servidor.
- **Bloqueio visual do off-hand**: quando há arma 2H equipada, o slot
  `off_hand` renderiza cruzado/desabilitado, sem aceitar clique ou drop.

## Tooltip com comparação

- Reaproveita `aplicarTooltipAoItem`, estendido: ao passar o mouse
  (ou segurar, em touch — "long press" substitui "hover") sobre um item da
  bolsa que tem equivalente já equipado no mesmo slot, mostra as duas
  listas de atributos lado a lado com setas ↑ (verde, melhora) / ↓
  (vermelho, piora) nos atributos que mudam, via `compareItemStats`.

## Visual

Referência: `assets/capa.png` (arte da caixa do jogo) e `assets/logotipo.png`
(logotipo já recortado, fundo transparente, fornecido pelo usuário).

- **Fundo do painel**: textura de mármore/rocha acinzentada (veios finos
  diagonais + manchas suaves via gradientes CSS em camadas), sobre o mundo
  3D real desfocado atrás (`backdrop-filter: blur(6px) saturate(105%)`
  aplicado sobre o canvas Three.js — sem fallback de performance; ajusta-se
  depois com dados reais de dispositivo, se necessário). **Risco técnico a
  verificar cedo na implementação**: `backdrop-filter` precisa conseguir
  ler o conteúdo pintado por um canvas WebGL por trás do overlay HTML —
  funciona nos browsers desktop/mobile modernos, mas vale confirmar cedo
  no webview do Capacitor/iOS-alvo antes de depender disso pro resto do
  visual (se não funcionar ali, o painel cai pra um fundo sólido sem o
  "mundo borrado atrás", sem quebrar o resto do design).
- **Contorno irregular** ("pergaminho rasgado"): `clip-path: polygon(...)`
  com pequenas reentrâncias ao longo de todo o perímetro (jitter de até
  ~1,1% da dimensão, mais sutil que a primeira tentativa). O contorno é
  desenhado em 3 camadas de SVG sobre o mesmo path (mesmos pontos do
  `clip-path`, em `viewBox="0 0 100 100" preserveAspectRatio="none"`):
  1. `glow` — brilho âmbar difuso (`stroke:#ff9d3d`, blur, opacity .55).
  2. `char` — linha de "carvão" escura (`stroke:#1a0f05`).
  3. `gold` — linha dourada nítida por cima (`stroke:#f4d78a`,
     `stroke-width:1.15`, drop-shadow sutil).
  Sem moldura grossa, rebites, ou friso de losangos (testados e
  descartados — a capa real do jogo não tem uma moldura ornamentada
  reaproveitável; é só linha fina + vinheta, o que essa versão recria).
- **Logotipo do jogo**: `assets/logotipo.png` (real, fornecido pelo
  usuário — sem recorte manual nem máscara CSS), exibido a 300px de
  largura (altura proporcional, ~121px, mantendo a razão original
  1097:443). Posicionado saindo do topo do painel: o "dente" das letras
  L/S do logo (medido nos pixels reais do arquivo: protrusão local em
  ~y=220–228 de 443, ou seja ~50,6% da altura da imagem) deve alinhar
  exatamente com a linha da borda superior do painel, mais ~9px de folga
  extra pra cima. Valor verificado nos mockups pra exibição a 300px de
  largura: `top: -70px` (regra geral, se a largura de exibição mudar:
  `top = -(altura_exibida × 0,506) − 9px`). Estruturalmente, o logo é
  **irmão** do painel (não filho) — fica fora do `clip-path` da borda
  rasgada, senão seria cortado (bug real encontrado e corrigido durante o
  brainstorming).
- **Slots de equipamento em proporção retrato 3:4**: 72×96px pros 5 slots
  "grandes" (arma, escudo, elmo, armadura, bota) — mesma razão dos
  retratos de herói já usados no jogo. Prontos pra receber fotos de
  equipamento no futuro via `item.icon` sem distorcer.
- **Anéis e itens mágicos a 80%**: `ring1`, `ring2`, `item1`, `item2`
  renderizam a 58×77px (80% de 72×96, mesma razão 3:4), centralizados na
  linha do grid via `align-items:center`.
- **Layout do paperdoll** (grid 3×3, `justify-items:center`,
  `align-items:center`):
  ```
  [item mágico 1]   [elmo]   [item mágico 2]
  [arma]          [armadura] [escudo]
  [anel 1]          [bota]    [anel 2]
  ```
- **Slots de item mágico** com borda roxa de destaque (`#c9a6ff`),
  diferenciando raridade dos demais.
- **Bolsa (itens não equipados)**: grade compacta abaixo do paperdoll,
  slots quadrados 42×42px (mantém o padrão atual — não usa a proporção
  3:4 do paperdoll, por ser uma grade utilitária menor; pode ser
  revisitado se necessário quando a arte de itens existir).
- **Ícones de item**: emoji por enquanto (fallback automático via
  `item.icon` ausente). Slot com moldura colorida por tipo reforça a
  identidade visual mesmo sem arte custom.

## Abertura/fechamento

- Ícone fixo `🎒` num canto da tela (reaproveita/estende `#ficha-fab`),
  sempre visível — cidade e masmorra, desktop e mobile.
- Tecla `I` abre/fecha (mesmo padrão de listener do `Escape` já existente).
- Fecha com X, clique fora do modal, ou `Esc`.
- Clique no retrato de outro herói na cidade abre o modal em modo
  **somente-leitura** (preserva o comportamento atual da ficha): mostra
  paperdoll, bolsa, ouro e tooltips normalmente, mas clique/drag em
  qualquer slot não dispara `equipFromBag`/`unequip`/`reorderBag` — vira
  no-op visual (sem toast de erro, já que não é uma tentativa inválida, é
  simplesmente uma visualização).

## Testes

- `tools/test_boots_slot.py` (novo, servidor): equipar/desequipar bota,
  migração de personagem existente sem a chave `boots`, conflito de duas
  mãos continua intacto com 9 slots (não regressão dos 8 slots antigos).
- Verificação manual via preview do navegador: abrir/fechar modal (ícone +
  tecla `I` + X + clique fora), equipar/trocar item por clique-clique e por
  drag nativo (mouse), bloqueio visual de slot incompatível, bloqueio do
  slot de escudo com arma 2H equipada, tooltip com comparação (setas
  ↑/↓), crescimento da grade da bolsa ao equipar item com `bagslots`,
  modo somente-leitura ao abrir o inventário de outro herói.
