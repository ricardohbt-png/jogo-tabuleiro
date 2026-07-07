# Peão vira antes de andar (corrige ordem visual) — Design

## Contexto

A feature anterior (peão vira na direção do movimento, ver
`docs/superpowers/specs/2026-07-07-peao-facing-movimento-design.md`) já grava
`player.facing` no servidor e converte pra rotação no cliente
(`_facingToRotY`, `game.js`). Mas visualmente o efeito aparece invertido: o
peão **anda primeiro** (com a rotação antiga) e só **vira no final** do
trajeto.

**Causa raiz:** o peão do herói usa uma animação client-side de "passo"
(`_animarPasso`, `game.js:13469-13521`) que faz o pulinho/deslizamento visual
casa a casa, chamada por `moverPeaoAoCaminho`/`_executarProximoPasso`
(`game.js:13444-13467`). Essa animação **nunca toca em `peao.rotation.y`** —
só anima `position.x/y/z`, `rotation.x` (tilt do pulinho) e `scale`
(esmagamento no pouso). A rotação correta só é aplicada quando o `game_state`
autoritativo do servidor chega e o peão é **reconstruído** por `obterFig`
(que inclui `p.facing` na chave de cache) — isso só acontece depois que
`onConclucao` dispara ao final de TODO o trajeto animado
(`game.js:20093-20095`, `renderMap3D(GS.gameState)`). Resultado: a rotação
"salta" pra correta só no fim, depois de o peão já ter caminhado com a cara
virada pro lado errado.

## Escopo

Só o peão do **herói local** (`GS.myPid`), no caminho de movimento por clique
(`case 'move':`, `game.js:20078-20101`) — é o único fluxo que usa
`moverPeaoAoCaminho`/`_animarPasso` E tem uma classe com peão GLB real
(`paladin`, hoje a única em `_GLB_ENABLED_CLASSES`).

**Fora de escopo (não tocar):**
- Peão do prisioneiro e dos servos animados/minions — reusam a mesma função
  `_animarPasso` (via `_animarCaminhoPeao3D`), mas nunca carregam rotação
  hoje; devem continuar exatamente assim.
- Classes em billboard 2D (Sprite) — rotação em `Sprite` não tem efeito
  visual (billboard sempre encara a câmera); nada muda pra elas, e não
  precisam de tratamento especial no código.
- Qualquer mudança na lógica de `_facingToRotY`, no servidor
  (`handle_move`/`enter_dungeon`), ou no fallback pós-animação
  (`renderMap3D` continua sendo chamado ao final, sem mudanças).
- Animação suave do giro em si — a rotação continua **instantânea** (mesmo
  estilo já usado em todo o resto do sistema); só muda **o momento** em que
  ela é aplicada (início do passo, não fim do trajeto).

## Mudanças

### 1. `game.js` — `case 'move':` (por volta da linha 20078-20099)

Ao montar o array `caminho` (hoje só `{x, z}` por casa), incluir a rotação
alvo daquele passo específico, calculada com o helper já existente
`_facingToRotY`:

```javascript
for(const [dx,dy] of action.path){
  cx+=dx; cy+=dy;
  caminho.push({x:cx, z:cy, rotY:_facingToRotY([dx,dy])});
}
```

Isso significa que cada casa do trajeto carrega consigo a direção em que o
peão deve estar olhando ao chegar (ou melhor, ao **começar**) aquele passo
específico — permitindo que um trajeto com curva vire o peão a cada mudança
de direção, casa a casa, não só uma vez no início do trajeto inteiro.

### 2. `game.js` — `_animarPasso` (por volta da linha 13469)

Aplicar essa rotação **antes** de iniciar a animação de deslocamento daquele
passo (a primeira linha de código útil da função):

```javascript
function _animarPasso(peao, destino, onPasso){
  if (destino.rotY !== undefined) peao.rotation.y = destino.rotY;
  const inicio = { x: peao.position.x, y: peao.position.y, z: peao.position.z };
  // ... resto da função inalterado
```

Como `_animarPasso` é reaproveitada por `_animarCaminhoPeao3D` (prisioneiro/
minions), que chama com `{x: tx, z: ty}` sem o campo `rotY`, o guard
`destino.rotY !== undefined` garante que esses fluxos continuam
byte-idênticos ao comportamento atual (nenhuma rotação é tocada).

## Resultado esperado

Ao clicar num destino e o herói (paladino) andar até lá: a cada casa do
trajeto, o peão vira instantaneamente pra encarar a direção daquele passo
**antes** do pulinho/deslizamento visual daquele passo começar — não mais
"anda e só depois vira".

## Teste manual

1. Worktree isolado, servidor rodando, Richard (paladino) na masmorra, modo
   3D.
2. Clicar um destino a 2+ casas de distância que exija pelo menos uma
   mudança de direção no meio do trajeto (ex: 2 casas pra leste, depois 2
   pra norte).
3. Observar: o peão vira pra leste ANTES do primeiro pulinho, anda 2 casas,
   vira pra norte ANTES do próximo pulinho (não no meio/depois dele), anda
   mais 2 casas. Nunca deve aparecer "andando de lado" com a rotação da
   direção anterior.
4. Confirmar que o comportamento final (pós-`onConclucao`, `renderMap3D`)
   continua idêntico a antes — sem regressão na reconciliação com o estado
   autoritativo.
5. Confirmar, com outra classe (ex: warrior, billboard), que o trajeto
   continua andando normalmente, sem nenhuma mudança visual perceptível
   (billboard sempre de frente pra câmera).
