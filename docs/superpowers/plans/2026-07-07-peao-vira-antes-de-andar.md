# Peão vira antes de andar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir a ordem visual do peão do herói ao andar — hoje ele anda primeiro e só vira no final do trajeto; deve virar instantaneamente pra direção de cada passo **antes** de animar aquele passo.

**Architecture:** A animação client-side do passo (`_animarPasso`, `game.js`) nunca toca `peao.rotation.y` — só anima posição/pulinho. A rotação correta só chega quando o peão é reconstruído a partir do `game_state` autoritativo, ao final de todo o trajeto. A correção: o caminho montado em `case 'move':` já sabe o `[dx,dy]` de cada passo antes de animar — basta anexar a rotação alvo (`_facingToRotY`, já existente) em cada waypoint do caminho, e `_animarPasso` aplica essa rotação instantaneamente assim que aquele passo específico começa, antes do pulinho.

**Tech Stack:** Vanilla JS (`game.js`, Three.js r128). **Nota sobre testes:** sem harness de teste automatizado pra `game.js` (mesma situação de todos os planos anteriores desta feature — arquivo de renderização acoplado a `THREE`/`document`/canvas). Verificação: `node --check` (sintaxe) + teste manual em navegador (worktree isolado + `preview_*`).

---

### Task 1: `game.js` — vira o peão no início de cada passo, não no final do trajeto

**Files:**
- Modify: `game.js:20085` (dentro do `case 'move':`, montagem do array `caminho`)
- Modify: `game.js:13469-13471` (início de `_animarPasso`)

- [ ] **Step 1: Anexar a rotação alvo a cada waypoint do caminho**

Código atual em `game.js` (por volta da linha 20085, dentro do bloco `if(peao && myP){` do `case 'move':`):
```javascript
        for(const [dx,dy] of action.path){ cx+=dx; cy+=dy; caminho.push({x:cx, z:cy}); }
```

Novo código:
```javascript
        for(const [dx,dy] of action.path){ cx+=dx; cy+=dy; caminho.push({x:cx, z:cy, rotY:_facingToRotY([dx,dy])}); }
```

- [ ] **Step 2: Aplicar a rotação no início do passo, antes de animar o deslocamento**

Código atual em `game.js` (início da função `_animarPasso`, por volta da linha 13469):
```javascript
function _animarPasso(peao, destino, onPasso){
  const inicio = { x: peao.position.x, y: peao.position.y, z: peao.position.z };
  const destinoWorld = casaParaMundo(destino.x, destino.z);
```

Novo código:
```javascript
function _animarPasso(peao, destino, onPasso){
  if (destino.rotY !== undefined) peao.rotation.y = destino.rotY;   // vira primeiro, antes de andar
  const inicio = { x: peao.position.x, y: peao.position.y, z: peao.position.z };
  const destinoWorld = casaParaMundo(destino.x, destino.z);
```

(`_animarPasso` também é chamada por `_animarCaminhoPeao3D`, linha 13365, com
`{x: tx, z: ty}` — sem `rotY`. O guard `destino.rotY !== undefined` faz essa
chamada continuar exatamente igual a hoje, sem tocar rotação nenhuma —
prisioneiro e servos animados ficam intocados.)

- [ ] **Step 3: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída, sem erro (código de saída 0).

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "fix(peao): vira antes de andar, nao no final do trajeto"
```

---

### Task 2: Verificação visual manual — vira antes de andar, casa a casa

**Files:** nenhum (só teste manual via preview, num worktree isolado)

- [ ] **Step 1: Criar um worktree isolado**

Run (da raiz do projeto):
```bash
git worktree add .worktrees/peao-vira-antes -b worktree-peao-vira-antes
```

- [ ] **Step 2: Recriar `.claude/launch.json` dentro do worktree**

Criar `.worktrees/peao-vira-antes/.claude/launch.json` com:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "game-worktree-peao-vira-antes",
      "runtimeExecutable": "python",
      "runtimeArgs": ["-c", "import os,runpy; os.chdir('C:/Users/RICARDO/Desktop/jogo tabuleiro/.worktrees/peao-vira-antes'); runpy.run_path('server.py', run_name='__main__')"],
      "port": 8765,
      "autoPort": false
    }
  ]
}
```
Adicionar esse mesmo bloco à lista `"configurations"` do `.claude/launch.json`
da RAIZ do projeto também (é de lá que a ferramenta de preview lê o nome) —
e removê-lo de lá de novo no fim da Task 2, junto com o worktree.

- [ ] **Step 3: Subir o servidor e entrar na masmorra como Richard (paladino), modo 3D**

Usar a ferramenta de preview (`preview_start`, config
`game-worktree-peao-vira-antes`). Fluxo: navegar pra
`http://localhost:8765/index.html`, criar sala, `csfSelectHero('paladin')`
via `preview_eval`, confirmar (`#cs-btn-confirm`), iniciar (`#cs-btn-start`),
entrar na masmorra (`#btn-enter-dungeon`), ligar o modo 3D (`toggle3D()` via
`preview_eval` — a aba de preview fica em segundo plano, então o clique no
botão pode não bastar).

- [ ] **Step 4: Clicar (via código) um destino que force uma curva no meio do trajeto**

`handleTileClick(tx, ty)` (`game.js:19956`) é a função chamada por um clique
real num tile — ela resolve o caminho (`GS.resolveTileClick`) e despacha pro
mesmo `case 'move':` que anima via `moverPeaoAoCaminho`/`_animarPasso`.
Chamá-la diretamente via `preview_eval` com as coordenadas de destino
**exercita exatamente o mesmo código de um clique real**, sem precisar achar
a posição de tela do tile:

```javascript
(function(){
  const me = GS.gameState.players.find(p=>p.id===GS.myPid);
  const [px,py] = me.pos;
  // escolhe um destino 2 casas num eixo + 2 no outro (força uma curva no meio)
  const tx = px + 2, ty = py + 2;
  handleTileClick(tx, ty);
  return {from:[px,py], to:[tx,ty]};
})()
```

Ajustar `tx,ty` conforme o mapa real (confirmar chão livre nas duas pernas do
trajeto via `GS.gameState.tiles` antes de clicar, igual ao plano anterior
desta feature).

- [ ] **Step 5: Observar a ordem virar→andar em cada segmento**

Tirar screenshots em sequência rápida (ou usar `preview_eval` pra ler
`peao.rotation.y` e `peao.position.x/z` a cada poucos ms durante a
animação) e confirmar: a rotação already bate com o novo segmento assim que
ele começa (não segue a rotação do segmento anterior durante o pulinho).
Comparar com o comportamento documentado como bug ("anda com a cara do
passo anterior, só vira no fim").

- [ ] **Step 6: Confirmar que o estado final pós-animação continua correto**

Esperar a animação completar (chamada de `onConclucao` →
`renderMap3D(GS.gameState)`) e confirmar que a posição/rotação final batem
com `GS.gameState.players.find(p=>p.id===GS.myPid).pos` e `.facing` — sem
regressão na reconciliação com o estado autoritativo.

- [ ] **Step 7: Confirmar que outra classe (billboard) não regride**

Repetir um trajeto com `class_id: "warrior"` (fora de
`_GLB_ENABLED_CLASSES`) — confirmar visualmente que o andar continua
idêntico a antes (billboard sempre de frente pra câmera, sem rotação
perceptível).

- [ ] **Step 8: Limpar o worktree e o `launch.json` da raiz**

```bash
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove .worktrees/peao-vira-antes
git worktree prune
```
Remover manualmente o bloco `game-worktree-peao-vira-antes` do
`.claude/launch.json` da raiz (gitignored — não precisa de commit).

---

## Fora de escopo (não fazer neste plano)

- Peão do prisioneiro/servos animados (`_animarCaminhoPeao3D`) — inalterado.
- Classes em billboard 2D — inalteradas (rotação em Sprite não tem efeito).
- Animação suave do giro em si — continua instantâneo, só muda o momento.
- Qualquer mudança em `_facingToRotY`, `server.py`, ou na reconciliação final
  pós-trajeto (`renderMap3D`).
