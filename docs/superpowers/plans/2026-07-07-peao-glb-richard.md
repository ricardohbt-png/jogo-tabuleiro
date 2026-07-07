# Peão GLB 3D do Richard (paladino) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reativar o peão 3D real (GLB) na masmorra só para a classe `paladin` (Richard), com fallback automático pro billboard 2D se o modelo falhar — as outras 5 classes continuam em billboard 2D, sem mudança.

**Architecture:** `game.js` já tem `_loadHeroGLB`/`_makeCharacterPawn3D` (código morto desde que o GLB 3D foi desativado em 2026-06-13). Vamos: (1) trocar o arquivo `assets/models3d/paladin.glb` pelo modelo novo do usuário; (2) dar a `_makeCharacterPawn3D` um callback de fallback (`onMissing`) pro caso de erro de carga; (3) fazer `_makeCharacterPawn` (a função realmente chamada pelo construtor de peões 3D) decidir GLB-vs-billboard por classe via um `Set` (`_GLB_ENABLED_CLASSES`).

**Tech Stack:** Vanilla JS (`game.js`), Three.js r128 (`GLTFLoader`), sem bundler. **Nota sobre testes:** `game.js` é renderização pura acoplada a `THREE`/`document`/canvas (ver `CLAUDE.md` — regra de arquitetura #1) e não é importável via `node`/`require` como `src/miniatura3d.js` (que tem `tools/test_miniatura3d.test.js`). Não existe harness de teste automatizado pra esse tipo de código no repo. A verificação desta feature é **manual, via preview no navegador** (servidor real + Three.js), como o próprio `CLAUDE.md` prescreve para mudanças de UI/renderização — não TDD com asserts.

---

### Task 1: Substituir o modelo GLB do paladino

**Files:**
- Modify (binário): `assets/models3d/paladin.glb`

- [ ] **Step 1: Conferir que o arquivo novo existe em Downloads**

Run: `ls -la "$USERPROFILE/Downloads/richard.glb"`
Expected: arquivo existe (deve aparecer com ~3.6MB, mesmo tamanho já visto antes).

- [ ] **Step 2: Sobrescrever o modelo antigo**

Run:
```bash
cp "$USERPROFILE/Downloads/richard.glb" "assets/models3d/paladin.glb"
```

- [ ] **Step 3: Confirmar que o git detectou a mudança**

Run: `git status --short assets/models3d/paladin.glb`
Expected: ` M assets/models3d/paladin.glb`

- [ ] **Step 4: Commit**

```bash
git add assets/models3d/paladin.glb
git commit -m "feat(peao): novo modelo GLB do Richard (paladino)"
```

---

### Task 2: `_makeCharacterPawn3D` ganha fallback (`onMissing`)

**Files:**
- Modify: `game.js:14424-14460` (função `_makeCharacterPawn3D`)

Hoje, se o GLB não carregar (erro de rede/parse, ou já cacheado como
`'erro'`), a função simplesmente não desenha nada — peão fica invisível.
Vamos adicionar um parâmetro `onMissing` (callback sem argumentos) chamado
nesse caso.

- [ ] **Step 1: Editar a função para aceitar e chamar `onMissing`**

Código atual em `game.js:14424-14460` (função inteira, para localizar o
trecho exato):
```javascript
function _makeCharacterPawn3D(T, grp, classId, Y0, rotY, altura) {
  const montar = tpl => {
    if (!tpl) return;
    const inst = tpl.clone();
    // Limite de 1 quadrado: a peça nunca ultrapassa o tile (1.0) no chão.
    const box = new T.Box3().setFromObject(inst);
    const tam = box.getSize(new T.Vector3());
    const FOOT = 0.97;
    const s = Math.min(
      altura / Math.max(tam.y, 1e-3),
      FOOT   / Math.max(tam.x, 1e-3),
      FOOT   / Math.max(tam.z, 1e-3)
    );
    // recentra o footprint e apoia os pés no chão (offset em espaço local)
    inst.position.set(
      -(box.min.x + box.max.x) / 2,
      -box.min.y,
      -(box.min.z + box.max.z) / 2
    );
    const wrap = new T.Group();
    wrap.add(inst);
    wrap.scale.setScalar(s);
    wrap.rotation.y = rotY;
    wrap.position.y = Y0;
    // isGroundDecal (dungeon) + noOL (class-select): fora do passe de outline —
    // a malha já é a silhueta exata; um shell BackSide ficaria errado.
    // isGLB: clone compartilha geometria/material/texturas com o template em
    // cache (_heroGLBCache) — o descarte do peão NUNCA pode liberar esses recursos.
    inst.traverse(o => { if (o.isMesh) { o.userData.isGroundDecal = true; o.userData.noOL = true; o.userData.isGLB = true; } });
    grp.add(wrap);
  };
  const cached = _heroGLBCache[classId];
  if (cached && cached !== 'erro') { montar(cached); return true; }
  if (cached === 'erro') return false;
  _loadHeroGLB(T, classId, montar);
  return true;   // virá async — não desenhar fallback por cima
}
```

Novo código (substitui a função inteira acima):
```javascript
function _makeCharacterPawn3D(T, grp, classId, Y0, rotY, altura, onMissing) {
  const montar = tpl => {
    if (!tpl) { if (onMissing) onMissing(); return; }
    const inst = tpl.clone();
    // Limite de 1 quadrado: a peça nunca ultrapassa o tile (1.0) no chão.
    const box = new T.Box3().setFromObject(inst);
    const tam = box.getSize(new T.Vector3());
    const FOOT = 0.97;
    const s = Math.min(
      altura / Math.max(tam.y, 1e-3),
      FOOT   / Math.max(tam.x, 1e-3),
      FOOT   / Math.max(tam.z, 1e-3)
    );
    // recentra o footprint e apoia os pés no chão (offset em espaço local)
    inst.position.set(
      -(box.min.x + box.max.x) / 2,
      -box.min.y,
      -(box.min.z + box.max.z) / 2
    );
    const wrap = new T.Group();
    wrap.add(inst);
    wrap.scale.setScalar(s);
    wrap.rotation.y = rotY;
    wrap.position.y = Y0;
    // isGroundDecal (dungeon) + noOL (class-select): fora do passe de outline —
    // a malha já é a silhueta exata; um shell BackSide ficaria errado.
    // isGLB: clone compartilha geometria/material/texturas com o template em
    // cache (_heroGLBCache) — o descarte do peão NUNCA pode liberar esses recursos.
    inst.traverse(o => { if (o.isMesh) { o.userData.isGroundDecal = true; o.userData.noOL = true; o.userData.isGLB = true; } });
    grp.add(wrap);
  };
  const cached = _heroGLBCache[classId];
  if (cached && cached !== 'erro') { montar(cached); return true; }
  if (cached === 'erro') { if (onMissing) onMissing(); return false; }
  _loadHeroGLB(T, classId, montar);
  return true;   // virá async — não desenhar fallback por cima
}
```

(Só 3 linhas mudam: a assinatura da função ganha `onMissing`; a linha
`if (!tpl) return;` vira `if (!tpl) { if (onMissing) onMissing(); return; }`;
e a linha `if (cached === 'erro') return false;` vira
`if (cached === 'erro') { if (onMissing) onMissing(); return false; }`.)

- [ ] **Step 2: Commit**

```bash
git add game.js
git commit -m "feat(peao): _makeCharacterPawn3D aceita callback onMissing"
```

---

### Task 3: `_makeCharacterPawn` decide GLB-vs-billboard por classe

**Files:**
- Modify: `game.js:14462-14472` (função `_makeCharacterPawn`, incluindo o
  comentário acima dela)

- [ ] **Step 1: Substituir a função e o comentário**

Código atual:
```javascript
// ── Character pawn — billboard 2D (Sprite) voltado para a câmera.
// A figura sempre aparece de frente e em pé na tela (mesma dinâmica dos
// monstros, via _makeBillboardSprite). Usa apenas frente.png.
function _makeCharacterPawn(T, grp, classId, clr, Y0) {
  // Billboard 2D (Sprite) — sempre de frente para a câmera e em pé, em qualquer
  // rotação. Mesma dinâmica dos monstros. GLB 3D desativado a pedido: o visual
  // 2D (frente.png) é o oficial.
  const cacheKey = classId || 'generic';
  _makeBillboardSprite(T, grp, `assets/pawns/${cacheKey}/frente.png`,
                       '__spr_' + cacheKey, Y0);
}
```

Novo código:
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

Nota: `_BB_H_ALVO` (constante `2.05`, já existente em `game.js:14514`) fica
usada aqui ANTES de ser declarada no arquivo (linha 14462 vs 14514) — isso é
seguro em JS porque `const` no escopo de módulo/script é resolvida em tempo
de chamada (a função só executa depois que o arquivo inteiro carregou), não
em tempo de definição. Não precisa mover a constante.

- [ ] **Step 2: Commit**

```bash
git add game.js
git commit -m "feat(peao): paladino usa peao GLB 3D com fallback pra billboard"
```

---

### Task 4: Verificação visual manual — peão do Richard em 3D

**Files:** nenhum (só teste manual via preview)

- [ ] **Step 1: Subir o servidor**

Usar a ferramenta de preview (`preview_start`, config `"game"` já existe em
`.claude/launch.json` — `python server.py`, porta 8765).

- [ ] **Step 2: Abrir o jogo, criar uma sala, escolher a classe Paladino (Richard)**

Navegar pra `http://localhost:8765/index.html` (via preview_eval /
navegação), criar sala, `select_class` com `class_id: "paladin"`,
`start_game`, `enter_dungeon`.

- [ ] **Step 3: Alternar para o modo 3D e conferir o peão**

Usar o botão/tecla de alternância 3D já existente no HUD. Tirar um
`preview_screenshot`. Conferir:
- O peão aparece (não fica invisível).
- Tamanho consistente com os outros peões da mesa (não deve estourar o
  tile nem ficar minúsculo — o clamp de footprint em
  `_makeCharacterPawn3D` já limita a 0.97 do tile).
- Orientação: se o modelo aparecer de costas ou de lado de forma
  incorreta, ajustar o `0` (quarto argumento, `rotY`) na chamada feita no
  Task 3 — valores em radianos (`Math.PI` = 180°, `Math.PI/2` = 90°) — e
  repetir este step até ficar correto.

- [ ] **Step 4: Registrar o valor final de `rotY` (se mudou)**

Se `rotY` precisou mudar, commitar a mudança:
```bash
git add game.js
git commit -m "fix(peao): ajusta orientacao (rotY) do peao GLB do paladino"
```
Se não precisou mudar (permanece `0`), pular este commit.

---

### Task 5: Verificação de regressão — outras classes continuam em billboard

**Files:** nenhum (só teste manual via preview)

- [ ] **Step 1: Repetir o fluxo do Task 4 com outra classe**

Escolher `class_id: "warrior"` (ou qualquer classe fora de
`_GLB_ENABLED_CLASSES`), entrar na masmorra, modo 3D, `preview_screenshot`.
Expected: peão continua billboard 2D (foto plana sempre de frente pra
câmera), igual antes da mudança — sem diferença visual.

---

### Task 6: Verificação de fallback — GLB quebrado cai no billboard

**Files:** nenhum (só teste manual, sem mudança permanente)

- [ ] **Step 1: Forçar erro de carga temporariamente**

Run:
```bash
mv assets/models3d/paladin.glb assets/models3d/paladin.glb.bak
```

- [ ] **Step 2: Repetir o fluxo do Task 4 com o Paladino**

Expected: sem erro fatal no console (`preview_console_logs` sem exceptions
não tratadas); o `console.warn('[GLB] falha ao carregar ...')` já existente
em `_loadHeroGLB` pode aparecer (é esperado); o peão do Richard aparece
como **billboard 2D** (fallback funcionando) em vez de ficar invisível.

- [ ] **Step 3: Restaurar o arquivo**

Run:
```bash
mv assets/models3d/paladin.glb.bak assets/models3d/paladin.glb
git status --short assets/models3d/paladin.glb
```
Expected: `git status` não mostra diferença (arquivo restaurado é
byte-idêntico ao commitado no Task 1).

---

## Fora de escopo (não fazer neste plano)

- Tela de seleção de personagem (`_cHeroPNG`) — continua 2D.
- Modelos GLB novos para as outras 5 classes.
- Reativar preload de GLB (foi removido deliberadamente antes).
