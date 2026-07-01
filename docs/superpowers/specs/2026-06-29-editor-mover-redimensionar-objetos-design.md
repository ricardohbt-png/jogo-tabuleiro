# Editor de Dungeons — Mover (arrastar) e Redimensionar objetos no "selecionar"

**Data:** 2026-06-29
**Escopo de arquivos:** apenas `tools/editor.js` (+ os campos novos no JSON que ele gera).
**NÃO toca:** `server.py`, `game.js`, `src/`.

## Objetivo

Estender a ferramenta **selecionar** do editor de dungeons para:

1. **Arrastar** qualquer entidade selecionável para uma nova casa do mapa
   (segurar o botão esquerdo após clicar e mover).
2. **Redimensionar** uma decoração (objeto) selecionada por dois eixos
   independentes:
   - **Footprint em casas** (quantos quadrados ocupa — inteiro).
   - **Tamanho visual** (deixar a imagem maior/mais alta sem mudar a ocupação).
3. Mostrar uma **referência visual** (contorno + rótulo `W×H`) de quantos
   quadrados o objeto ocupa.

## Decisões (do brainstorming)

- **Escopo "só editor + JSON":** os novos campos são gravados no `.json`, mas o
  servidor não os aplica. O jogo continua usando o tamanho do catálogo
  (`DECOR_TYPES`) até uma implementação futura do lado do servidor.
- **Arrastar vale para todas as entidades selecionáveis** (entrada, saída,
  prisioneiro, monstro, baú, armadilha, decoração). **Sala fica de fora** — já
  tem a ferramenta "sala"; mover a região é outra feature.
- **Tamanho = mistura de dois conceitos** (ambos por-objeto):
  - footprint em casas (inteiros, mín. 1);
  - escala visual independente em **largura e altura**.
- **Aumento visual transborda para cima** (altura ancorada na base) e centralizado
  na largura — sem ocupar casas vizinhas.
- **Colisão = bloquear:** soltar/redimensionar em local inválido reverte para o
  estado anterior.
- **Referência = contorno realçado + rótulo `W×H`** sobre o objeto selecionado.

## Verificação do servidor (já feita, read-only)

- `server.py` linha ~3744: o carregador de decorações monta um dict com chaves
  fixas e **ignora campos extras** (`size`, `vscale`) → não quebra o carregamento
  no jogo.
- `server.py` linha ~10120 e ~1801: render/colisão e `validar_dungeon` usam
  `DECOR_TYPES[type]["size"]` (catálogo). Logo o redimensionamento é puramente
  visual/editorial.
- **Limitação conhecida (aceita):** como `validar_dungeon` usa o tamanho do
  catálogo, *encolher* um objeto abaixo do footprint de catálogo pode fazer o
  servidor validar contra o tamanho maior. *Crescer* é seguro. Documentar no
  painel/commit, não tratar.

## Modelo de dados (em `S.decorations[i]`)

Dois campos novos, **opcionais**, só gravados quando diferentes do padrão:

- `size: [w, h]` — override do footprint em casas (default = catálogo do tipo).
- `vscale: [sx, sy]` — escala visual (default = `[1, 1]`).

`facing` continua trocando `w↔h` quando horizontal — o override entra **antes** da
troca por facing (o override descreve o tamanho "natural", e a rotação aplica em
cima, igual ao catálogo).

## Mudanças em `tools/editor.js`

### 1. Tamanho efetivo com override

- Novo helper `baseSizeOf(d)` → `d.size` se presente, senão `decorMeta(d.type).size`.
- `decorEffSize` ganha variante por-decoração: `decorEffSizeOf(d)` que usa
  `baseSizeOf(d)` e aplica a troca por `facing`.
- `decorTiles(d)` passa a derivar as casas de `decorEffSizeOf(d)` (não mais só do
  catálogo). `decorTilesAt(type,…)` continua existindo para o preview de colocação
  (objetos novos = tamanho de catálogo).

### 2. Checagem de encaixe genérica

- `decorWouldFit(d, newPos, newSize, newFacing)` → calcula as casas a partir de
  `newPos/newSize/newFacing` e valida: dentro do grid, todas em `FLOOR`, sem
  sobrepor outra decoração (ignorando o próprio `d`).
- Usada tanto pelo arrasto (novo pos) quanto pelo resize de footprint (novo size).

### 3. Arrastar (drag-to-move)

Estado novo: `drag = { sel, offset:[ox,oy], origin:{…}, candidate:[x,y]|null, valid }`.

- **mousedown (tool `select`):** seleciona a entidade (como hoje). Se houver
  entidade (não-sala) sob o cursor, inicia `drag` com `offset = clicked - anchorPos`
  (para decoração multi-casa manter o ponto de pega; 1 casa → `[0,0]`). Guarda a
  posição original para reverter.
- **mousemove:** se `drag` ativo, calcula `candidate = cell - offset`, marca
  `valid` (decoração → `decorWouldFit`; demais → em grid e tile `!== WALL`),
  e redesenha com um **retângulo de preview** verde (válido) / vermelho (inválido)
  no footprint de destino.
- **mouseup:** se houve movimento e `valid`, comita (`moveSel(candidate)`); senão
  reverte (sem mover). Clique sem arrastar = só seleção (comportamento atual).
- `moveSel(pos)` aplica a nova posição conforme o `kind`:
  `entrance{x,y}` / `exit{x,y}` / `prisoner.pos` / `monster.pos` / `chest.pos` /
  `trap.pos` / `decor.pos`.
- Não interfere no fluxo de `painting`/`roomDrag` (ferramentas diferentes).

### 4. Painel de decoração — controles de tamanho

No bloco `k === "decor"` do `renderPanel`, adicionar uma seção "Tamanho":

- **Footprint (casas):** `largura` e `altura` — `<input type="number" min="1">`,
  valor atual = `baseSizeOf(ref)`. `onchange`:
  - monta `newSize`; se `decorWouldFit(ref, ref.pos, newSize, ref.facing)` →
    aplica `ref.size = newSize` (ou remove `ref.size` se voltar ao catálogo);
  - senão **reverte** o input e mostra aviso curto.
- **Tamanho visual:** `escala largura` e `escala altura` —
  `<input type="number" min="0.2" max="4" step="0.1">`, valor = `ref.vscale||[1,1]`.
  `onchange` aplica `ref.vscale` (remove se `[1,1]`), `render()`. Sem bloqueio.

### 5. Render — escala visual + referência

- **Escala visual** ao desenhar o PNG (e o emoji) da decoração:
  - `drawW = pw * sx`, `drawH = ph * sy`;
  - âncora base/centro: `drawX = centerX - drawW/2`, `drawY = (py+ph) - drawH`
    (cresce para cima e para os lados, transbordando sem ocupar casas).
  - Emoji: `font-size` escalado por `sy`, ancorado na base-centro.
- **Referência (contorno + rótulo):** para a decoração **selecionada**, desenhar
  o contorno do footprint realçado (linha mais forte, alinhada à grade) e o texto
  `"{ew}×{eh}"` (casas efetivas) sobre o objeto.

### 6. Persistência (round-trip)

- `buildJSON` (mapeamento de `decorations`): incluir `size` se `d.size` definido e
  `vscale` se `d.vscale` definido e `!= [1,1]`.
- `loadJSON` (mapeamento de `decorations`): ler `d.size`/`d.vscale` quando
  presentes (validando que são arrays de 2 números).

## Não-objetivos (YAGNI)

- Nenhuma mudança em `server.py`/`game.js`/3D.
- Sala não é arrastável nem redimensionável por aqui.
- Sem "handles" de redimensionar arrastando a borda — o resize é por campos
  numéricos no painel (decisão do brainstorming).

## Verificação manual (no editor, escopo determinado)

1. Selecionar e arrastar cada tipo de entidade; soltar em casa válida move; em
   parede/fora/sobreposição reverte.
2. Decoração 1×1 → mudar footprint para 2×1 e 2×2; ver o contorno + rótulo;
   tentar crescer sobre parede → bloqueia.
3. Mudar escala visual de altura → imagem cresce para cima sem ocupar casas.
4. Salvar e recarregar o `.json` → `size`/`vscale` preservados (round-trip).
5. Abrir a dungeon no jogo → carrega sem erro (campos extras ignorados).
