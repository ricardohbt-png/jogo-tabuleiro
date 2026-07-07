# Peão vira na direção do movimento Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** O peão GLB 3D do paladino (Richard) vira em incrementos de 90° pra sempre encarar a direção do último passo dado, em vez de ficar sempre com `rotY=0` fixo.

**Architecture:** `server.py` grava `p["facing"] = [dx, dy]` a cada passo válido em `handle_move` (mesmo padrão já usado pros monstros orientados, `m["facing"]`) e reseta esse campo sempre que o jogador é reposicionado na entrada de uma masmorra. O campo já viaja automaticamente no `game_state` (o servidor serializa o dicionário inteiro do jogador). `game.js` converte esse vetor num ângulo de rotação Y via um novo helper puro `_facingToRotY`, e repassa esse ângulo pro `_makeCharacterPawn3D` através da mesma cadeia de chamadas que já existe (`build3DFig` → `_makeCharacterPawn`), reaproveitando o parâmetro `mFacing` que hoje só serve pra monstros orientados (crocodilo/lagarto).

**Tech Stack:** Python (`server.py`, testes em `tools/test_*.py`, sem framework — script com contador `PASS`/`FAIL`, roda com `python tools/<arquivo>.py`) + vanilla JS (`game.js`, Three.js r128). **Nota sobre testes de `game.js`:** como no plano anterior desta mesma feature (peão GLB do paladino), não existe harness de teste automatizado pra esse arquivo (renderização acoplada a `THREE`/`document`/canvas — ver `CLAUDE.md`, regra de arquitetura #1). A verificação do lado cliente é `node --check game.js` (sintaxe) + teste manual em navegador (worktree isolado + `preview_*`), não testes unitários.

---

### Task 1: `server.py` — `handle_move` grava `facing`

**Files:**
- Modify: `server.py:5623-5624`
- Create: `tools/test_peao_facing.py`

- [ ] **Step 1: Escrever o teste (seção [1] apenas)**

Criar `tools/test_peao_facing.py` com este conteúdo exato:

```python
"""Peão vira na direção do movimento — facing do jogador.
Roda da raiz: python tools/test_peao_facing.py"""
import asyncio, sys, os, json
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def fixture():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_fase3.json"), encoding="utf-8") as f:
        return json.load(f)

def setup_authored():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.mode = "authored"; r.dungeon_def = fixture()
    r.phase = "city"
    return r

async def main():
    print("\n[1] handle_move grava facing = [dx,dy] a cada passo")
    r = setup_authored()
    await r.enter_dungeon("p1")
    p = r.players["p1"]
    check("facing ausente antes do 1º passo", "facing" not in p)

    # Posição/tiles controlados: independe do layout real da fixture.
    p["pos"] = [5, 5]
    r.tiles[5][5] = S.FLOOR
    r.tiles[5][6] = S.FLOOR
    await r.handle_move("p1", 1, 0)
    check("posição avançou 1 casa a leste", p["pos"] == [6, 5])
    check("facing = [1,0] (leste)", p.get("facing") == [1, 0])

    r.tiles[4][6] = S.FLOOR
    await r.handle_move("p1", 0, -1)
    check("facing = [0,-1] (norte) após o passo seguinte", p.get("facing") == [0, -1])

    print(f"\n{'='*50}\nPASS={PASS} FAIL={FAIL}")
    if FAIL: sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e confirmar que falha do jeito certo**

Run: `python tools/test_peao_facing.py`
Expected: as 2 linhas `facing = [1,0]...` e `facing = [0,-1]...` aparecem com `❌` (ainda não implementado — `p.get("facing")` retorna `None`); a linha `posição avançou...` aparece com `✅` (movimento em si já funciona, não é o que estamos testando). Termina com `PASS=2 FAIL=2` e sai com código de erro (por causa do `sys.exit(1)`).

- [ ] **Step 3: Implementar**

Código atual em `server.py` (dentro de `handle_move`, por volta da linha 5623):
```python
        p["pos"] = [nx, ny]
        p["moves_left"] -= 1
```

Novo código:
```python
        p["pos"] = [nx, ny]
        p["facing"] = [dx, dy]
        p["moves_left"] -= 1
```

- [ ] **Step 4: Rodar o teste de novo e confirmar que passa**

Run: `python tools/test_peao_facing.py`
Expected: todas as linhas da seção `[1]` com `✅`. Termina com `PASS=4 FAIL=0`, sem erro de saída.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_peao_facing.py
git commit -m "feat(peao): handle_move grava p[\"facing\"] a cada passo"
```

---

### Task 2: `server.py` — `enter_dungeon` reseta `facing`

**Files:**
- Modify: `server.py:5225-5233`
- Modify: `tools/test_peao_facing.py` (adiciona seção [2])

- [ ] **Step 1: Adicionar a seção [2] ao teste (falhando)**

Editar `tools/test_peao_facing.py`: inserir este bloco em `main()`, **depois** da seção `[1]` (depois da linha `check("facing = [0,-1] (norte) após o passo seguinte", ...)`) e **antes** do `print(f"\n{'='*50}...")` final:

```python
    print("\n[2] enter_dungeon reseta facing ao (re)entrar na masmorra")
    check("facing setado antes do reset (sanity)", "facing" in p)
    r.phase = "city"                   # simula volta pra cidade
    r.dungeon_generated = True         # reentrada na MESMA masmorra (nova=False)
    await r.enter_dungeon("p1")
    check("facing limpo ao reentrar na masmorra", "facing" not in r.players["p1"])
```

- [ ] **Step 2: Rodar o teste e confirmar que a seção [2] falha**

Run: `python tools/test_peao_facing.py`
Expected: seção `[1]` toda `✅` (implementada na Task 1). Seção `[2]`: `facing setado antes do reset (sanity)` com `✅` (ainda tem o facing do passo anterior), `facing limpo ao reentrar na masmorra` com `❌` (ainda não implementado). Termina com `FAIL=1` e sai com erro.

- [ ] **Step 3: Implementar**

Código atual em `server.py` (dentro de `enter_dungeon`, por volta da linha 5225):
```python
        for i, pid2 in enumerate(pids):
            if spawn_tiles is not None:
                self.players[pid2]["pos"] = list(spawn_tiles[i % len(spawn_tiles)])
            else:
                ox, oy = offsets[i % len(offsets)]
                self.players[pid2]["pos"] = [entrance["cx"] + ox, entrance["cy"] + oy]
            self.players[pid2]["moves_left"]       = self.players[pid2]["spd"]
            self.players[pid2]["action_done"]      = False
            self.players[pid2]["bonus_action_used"] = False
```

Novo código:
```python
        for i, pid2 in enumerate(pids):
            if spawn_tiles is not None:
                self.players[pid2]["pos"] = list(spawn_tiles[i % len(spawn_tiles)])
            else:
                ox, oy = offsets[i % len(offsets)]
                self.players[pid2]["pos"] = [entrance["cx"] + ox, entrance["cy"] + oy]
            self.players[pid2].pop("facing", None)
            self.players[pid2]["moves_left"]       = self.players[pid2]["spd"]
            self.players[pid2]["action_done"]      = False
            self.players[pid2]["bonus_action_used"] = False
```

- [ ] **Step 4: Rodar o teste de novo e confirmar que passa**

Run: `python tools/test_peao_facing.py`
Expected: as duas seções `[1]` e `[2]` inteiras com `✅`. Termina com `PASS=6 FAIL=0`, sem erro de saída.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_peao_facing.py
git commit -m "feat(peao): enter_dungeon reseta facing ao (re)posicionar o jogador"
```

---

### Task 3: `game.js` — `_facingToRotY` + `_makeCharacterPawn` ganha `rotY`

**Files:**
- Modify: `game.js:14460-14474`

- [ ] **Step 1: Editar**

Código atual (`game.js`, por volta da linha 14460):
```javascript
// ── Character pawn — GLB 3D real para classes em _GLB_ENABLED_CLASSES,
// billboard 2D (Sprite, frente.png) para as demais. Fallback automático pro
// billboard se o GLB falhar ao carregar (onMissing).
const _GLB_ENABLED_CLASSES = new Set(['paladin']);

function _makeCharacterPawn(T, grp, classId, clr, Y0) {
  const cacheKey = classId || 'generic';
  const billboard = () => _makeBillboardSprite(T, grp,
    `assets/pawns/${cacheKey}/frente.png`, '__spr_' + cacheKey, Y0);
  if (_GLB_ENABLED_CLASSES.has(classId)) {
    _makeCharacterPawn3D(T, grp, classId, Y0, 0, _BB_H_ALVO, billboard);
    return;
  }
  billboard();
}
```

Novo código (substitui o trecho acima inteiro):
```javascript
// ── Character pawn — GLB 3D real para classes em _GLB_ENABLED_CLASSES,
// billboard 2D (Sprite, frente.png) para as demais. Fallback automático pro
// billboard se o GLB falhar ao carregar (onMissing).
const _GLB_ENABLED_CLASSES = new Set(['paladin']);

// Converte a direção do último passo ([dx,dy], grid — vem de player.facing)
// num ângulo de rotação Y (radianos) pro peão GLB encarar aquele lado. Sem
// direção conhecida (herói ainda não andou) cai no padrão Sul — mesmo valor
// que rotY=0 já produzia antes desta feature (sem mudança visual pra quem
// nunca se moveu). Valores calibrados visualmente na Task 5 deste plano —
// se algum lado aparecer errado no teste manual, ajustar as constantes
// abaixo (múltiplos de Math.PI/2) até bater.
function _facingToRotY(facing) {
  if (!facing) return 0;                // Sul (padrão)
  const [fx, fy] = facing;
  if (fy > 0) return 0;                 // Sul  (+gy)
  if (fy < 0) return Math.PI;           // Norte (-gy)
  if (fx > 0) return -Math.PI / 2;      // Leste (+gx)
  return Math.PI / 2;                   // Oeste (-gx)
}

function _makeCharacterPawn(T, grp, classId, clr, Y0, rotY) {
  const cacheKey = classId || 'generic';
  const billboard = () => _makeBillboardSprite(T, grp,
    `assets/pawns/${cacheKey}/frente.png`, '__spr_' + cacheKey, Y0);
  if (_GLB_ENABLED_CLASSES.has(classId)) {
    _makeCharacterPawn3D(T, grp, classId, Y0, rotY || 0, _BB_H_ALVO, billboard);
    return;
  }
  billboard();
}
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída, sem erro (código de saída 0).

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(peao): _facingToRotY + _makeCharacterPawn aceita rotY"
```

---

### Task 4: `game.js` — `build3DFig` repassa a direção pro peão de herói

**Files:**
- Modify: `game.js:14001-14014` (loop de jogadores)
- Modify: `game.js:14674` (comentário de cabeçalho)
- Modify: `game.js:14789` (chamada de `_makeCharacterPawn` dentro de `build3DFig`)

`build3DFig` já recebe um parâmetro `mFacing` (usado hoje só pros monstros
"orientados" — crocodilo/lagarto — que retornam **antes** de chegar no
trecho que desenha peões de herói). Como nenhum herói é "monstro orientado",
esse parâmetro está livre pra ser reaproveitado como a direção do peão de
herói, sem precisar adicionar um parâmetro novo na função.

- [ ] **Step 1: Atualizar o comentário de cabeçalho da função**

Código atual (`game.js`, por volta da linha 14674):
```javascript
// mOriented/mFacing — monstro de 2 casas em pé cobrindo as 2 casas (croc/lagarto)
```

Novo código:
```javascript
// mOriented/mFacing — monstro de 2 casas em pé cobrindo as 2 casas (croc/lagarto).
// mFacing também é reaproveitado pro peão GLB de herói (direção do último passo).
```

- [ ] **Step 2: Passar `mFacing` pro `_makeCharacterPawn` dentro de `build3DFig`**

Código atual (`game.js`, por volta da linha 14789):
```javascript
  } else {
    _makeCharacterPawn(T, grp, classId, clr, Y0);
  }
```

Novo código:
```javascript
  } else {
    _makeCharacterPawn(T, grp, classId, clr, Y0, _facingToRotY(mFacing));
  }
```

- [ ] **Step 3: Loop de jogadores — incluir `p.facing` na chamada e na chave de cache**

Código atual (`game.js`, por volta da linha 14008):
```javascript
    obterFig(`pl:${p.id}`,
      JSON.stringify([p.color, p.class_id, p.id===GS.myPid, isCur, !!pSel]),
      () => {
        const f = build3DFig(p.color, false, p.id===GS.myPid, isCur, px, py, p.class_id, null, pSel);
        f.userData.pid = p.id;          // permite getPeaoMesh(pid) p/ animação
        return f;
      }, px, py);
```

Novo código:
```javascript
    obterFig(`pl:${p.id}`,
      JSON.stringify([p.color, p.class_id, p.id===GS.myPid, isCur, !!pSel, p.facing]),
      () => {
        const f = build3DFig(p.color, false, p.id===GS.myPid, isCur, px, py, p.class_id, null, pSel,
          undefined, undefined, undefined, p.facing);
        f.userData.pid = p.id;          // permite getPeaoMesh(pid) p/ animação
        return f;
      }, px, py);
```

(`undefined, undefined, undefined` preenche os parâmetros `mImage`,
`mPorte`, `mOriented` — irrelevantes pra jogadores — só pra `p.facing` cair
na posição certa do `mFacing`, o 13º e último parâmetro de `build3DFig`.
Incluir `p.facing` na string de cache do `obterFig` é o que já faz os
monstros orientados reconstruírem a malha quando a direção muda — ver a
linha equivalente pros monstros logo abaixo neste mesmo arquivo, que já usa
exatamente esse padrão com `m.facing`.)

- [ ] **Step 4: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída, sem erro (código de saída 0).

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(peao): build3DFig repassa a direcao do passo pro peao de heroi"
```

---

### Task 5: Verificação visual manual — peão vira nas 4 direções

**Files:** nenhum (só teste manual via preview, num worktree isolado)

- [ ] **Step 1: Criar um worktree isolado**

Run (da raiz do projeto):
```bash
git worktree add .worktrees/peao-facing -b worktree-peao-facing
```

- [ ] **Step 2: Recriar `.claude/launch.json` dentro do worktree**

O arquivo `.claude/` é gitignored, não vem no worktree. Criar
`.worktrees/peao-facing/.claude/launch.json` com:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "game-worktree-peao-facing",
      "runtimeExecutable": "python",
      "runtimeArgs": ["-c", "import os,runpy; os.chdir('C:/Users/RICARDO/Desktop/jogo tabuleiro/.worktrees/peao-facing'); runpy.run_path('server.py', run_name='__main__')"],
      "port": 8765,
      "autoPort": false
    }
  ]
}
```
(Adicionar esse bloco à lista `"configurations"` do `.claude/launch.json` da
RAIZ do projeto também — é de lá que a ferramenta de preview lê o nome —, e
removê-lo de lá de novo no fim da Task 6, junto com o worktree.)

- [ ] **Step 3: Subir o servidor e abrir o jogo**

Usar a ferramenta de preview (`preview_start`, config
`game-worktree-peao-facing`). Navegar pra
`http://localhost:8765/index.html`, criar sala, `select_class` com
`class_id: "paladin"`, `start_game`, `enter_dungeon`, ligar o modo 3D
(`toggle3D()` via `preview_eval` se o clique no botão `#btn-3d-toggle` não
alternar por causa da aba estar em segundo plano — mesma situação já
enfrentada no plano anterior desta feature).

- [ ] **Step 4: Mover nas 4 direções e conferir a rotação**

Via `preview_eval`, chamar a função global `move(dx,dy)` (que só chama
`GS.move(dx,dy)` — é o que as teclas de seta/WASD já acionam,
`game.js:11116-11119`) pra cada direção, uma de cada vez. Depois de cada
chamada, forçar um render síncrono e tirar um screenshot (a aba de preview
fica em segundo plano — sem isso o canvas não atualiza; mesma técnica do
plano anterior):

```javascript
move(0, 1);  // Sul
g3.renderer.render(g3.scene, g3.camera);
```

Repetir pra `move(0, -1)` (Norte), `move(-1, 0)` (Oeste), `move(1, 0)`
(Leste) — sempre voltando pra uma casa livre entre uma chamada e outra se
necessário (o Richard pode ficar preso contra parede; usar o mapa
explorado na tela pra escolher passos válidos). Comparar cada screenshot:
a "frente" do modelo (peito/rosto) deve apontar pro lado que ele andou.

- [ ] **Step 5: Corrigir as constantes se alguma direção estiver errada**

Se algum lado aparecer de costas ou de perfil errado, editar as constantes
de `_facingToRotY` (Task 3, `game.js`) — trocar o sinal ou o valor daquele
`case` (`0`, `Math.PI`, `Math.PI/2`, `-Math.PI/2`) até bater. Repetir o
Step 4 pra confirmar. Se precisou mudar, commitar:
```bash
git add game.js
git commit -m "fix(peao): ajusta constantes de _facingToRotY apos teste visual"
```
Se não precisou mudar, pular este commit.

---

### Task 6: Verificação de reset e regressão

**Files:** nenhum (só teste manual via preview, mesmo worktree da Task 5)

- [ ] **Step 1: Confirmar o padrão Sul antes do 1º passo**

Ainda no worktree/preview da Task 5: recarregar a página, criar uma sala
nova, entrar como Richard, modo 3D, **sem mover ainda**. Screenshot.
Esperado: peão olhando pro Sul (mesma orientação de antes desta feature —
`rotY=0`).

- [ ] **Step 2: Confirmar o reset ao reentrar na masmorra**

Mover o Richard em qualquer direção que não seja Sul (ex: Norte), voltar
pra cidade (`GS.send({type:'end_turn'})` até liberar isso, ou o fluxo
normal de fim de missão — o que for mais rápido no estado atual da sala de
teste), reentrar na masmorra (`enter_dungeon`). Screenshot. Esperado: peão
de volta olhando pro Sul, mesmo tendo terminado a masmorra anterior
olhando pra outro lado.

- [ ] **Step 3: Confirmar que outras classes continuam sem rotação (billboard)**

Repetir o fluxo com `class_id: "warrior"` (fora de `_GLB_ENABLED_CLASSES`),
mover em qualquer direção, comparar screenshot antes/depois do passo.
Esperado: nenhuma mudança visual — billboard 2D sempre de frente pra
câmera, como já era antes desta feature.

- [ ] **Step 4: Rodar o teste automatizado do servidor uma última vez**

Run: `python tools/test_peao_facing.py`
Expected: `PASS=6 FAIL=0` (ou mais, se algo foi ajustado), sem erro de
saída.

- [ ] **Step 5: Limpar o worktree e o `launch.json` da raiz**

```bash
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove .worktrees/peao-facing
git worktree prune
```
Remover manualmente o bloco `game-worktree-peao-facing` adicionado ao
`.claude/launch.json` da raiz no Step 2 da Task 5 (esse arquivo é
gitignored — não precisa de commit, só editar de volta).

---

### Task 7: Documentar no `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Adicionar um parágrafo na seção "Estado do Projeto"**

Inserir, logo após o parágrafo mais recente da seção "Estado do Projeto"
(o do peão GLB do Richard, se já estiver documentado — senão, ao final da
seção), o seguinte bloco (estilo `>` igual aos demais parágrafos da seção):

```markdown
> **Peão vira na direção do movimento:** o peão GLB 3D (hoje só `paladin`)
> agora encara o lado do último passo dado, em incrementos de 90°. Servidor:
> `handle_move` grava `p["facing"] = [dx, dy]` a cada passo válido (mesmo
> formato/mecanismo que `m["facing"]` já usava pros monstros orientados —
> crocodilo/lagarto); `enter_dungeon` limpa esse campo ao (re)posicionar os
> jogadores na entrada, então toda masmorra começa com o peão olhando pro
> Sul. Vai automaticamente no `game_state` (serialização crua do dicionário
> do jogador, sem view filtrada). Cliente: `_facingToRotY` (`game.js`)
> converte o vetor num ângulo múltiplo de 90°; `build3DFig` reaproveita o
> parâmetro `mFacing` (já existente pros monstros orientados) pra também
> carregar a direção do peão de herói, já que nenhum herói passa pelo ramo
> de monstro orientado. Sem animação — a rotação encaixa instantaneamente a
> cada passo confirmado. Teste: `tools/test_peao_facing.py`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: documenta o giro do peao na direcao do movimento"
```
