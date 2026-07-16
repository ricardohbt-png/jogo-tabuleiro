# Camada C-b — Minimapa de CR do Mestre (em jogo) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development ou superpowers:executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Dar ao mestre, em jogo, um minimapa das salas com o CR e a faixa de dificuldade de cada uma, o CR médio (média das salas) no topo, e um seletor de 2/4/6 jogadores. Exclusivo do mestre; nunca visível aos jogadores.

**Architecture:** 100% cliente (`game.js`/`game.css`). Reusa o módulo `src/difficulty.js` (já carregado) e os dados já presentes no `game_state`: `rooms` (geometria x/y/w/h/id), `monsters[].cr`/`room_id`, `expected_party`. O ícone `#ficha-fab` (🎒 Inventário) é repurposado para 🗺️ "Mapa de CR" quando `GS.isMaster()`. O minimapa é um overlay HTML (salas como retângulos posicionados/coloridos por faixa). Nenhuma mudança no servidor (o `expected_party` já é serializado desde a Fase C-a).

**Tech Stack:** Vanilla JS (`game.js`), CSS (`game.css`), `window.Difficulty`. Sem harness de teste JS → `node --check` + verificação no navegador.

**Spec:** `docs/superpowers/specs/2026-07-15-modo-mestre-camada-c-nd-termometro-design.md` (componente 5).

**Contexto de WIP:** o usuário edita monstros em paralelo (`server.py`/`editor_*`/assets). Este plano toca APENAS `game.js` e `game.css` — commitar só esses dois. NUNCA `git add -A`.

---

## Task 1: Repurpose do `#ficha-fab` para o mestre (🎒 → 🗺️)

**Files:** Modify `game.js` (perto do hook de `gameState` ~21346; o botão `#ficha-fab` está na linha ~189 e é movido ao body em `_fichaFabSempreVisivel` ~21341)

- [ ] **Step 1: Função que ajusta o fab conforme o papel**

Adicione em `game.js` (perto de `_fichaFabSempreVisivel`, ~linha 21344) uma função e chame-a nas atualizações de estado:

```javascript
function _atualizarFichaFab(){
  const fab = document.getElementById('ficha-fab');
  if(!fab) return;
  if(GS.isMaster()){
    fab.textContent = '🗺️';
    fab.title = 'Mapa de CR (mestre)';
    fab.onclick = () => abrirMinimapaCR();
  } else {
    fab.textContent = '🎒';
    fab.title = 'Inventário (tecla I)';
    fab.onclick = () => InventoryModal.toggle(GS.myPid);
  }
}
```

- [ ] **Step 2: Chamar em cada `gameState`**

No handler `GS.on('gameState', …)` (~linha 21346), adicione `_atualizarFichaFab();` logo após `handleGameState(msg);`. (Assim o fab reflete o papel assim que o estado chega e a cada atualização.)

- [ ] **Step 3: Verificar sintaxe**

Run: `node --check game.js` → sem erro (a função `abrirMinimapaCR` é definida na Task 2; a referência dentro de um arrow só é resolvida na chamada, então `node --check` passa).

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(mestre): #ficha-fab vira Mapa de CR para o mestre"
```

---

## Task 2: Overlay do minimapa de CR

**Files:** Modify `game.js` (nova função `abrirMinimapaCR` + estado de preview; perto de `renderFichaMonstro` ~linha 10331 ou junto do HUD do mestre)

- [ ] **Step 1: Estado de preview + render**

Adicione em `game.js` (perto de `renderFichaMonstro`, que já é código só-do-mestre):

```javascript
var _minimapaPreviewHeroes = null;   // null = usa expected_party.heroes; 2/4/6 = preview

function _crPorSalaMapa(state){
  // CR (cr de monstros vivos) por room_id. Retorna {porRoom: {id:cr}, medio, total}.
  var porRoom = {};
  (state.rooms || []).forEach(function(r){ porRoom[r.id] = 0; });
  var total = 0;
  (state.monsters || []).forEach(function(m){
    var cr = window.Difficulty ? window.Difficulty.crFromEntry(m) : 0;
    total += cr;
    if(m.room_id != null && porRoom[m.room_id] != null) porRoom[m.room_id] += cr;
  });
  var ids = Object.keys(porRoom);
  var soma = ids.reduce(function(a,k){ return a + porRoom[k]; }, 0);
  var medio = ids.length ? (soma / ids.length) : 0;
  return { porRoom: porRoom, medio: medio, total: total };
}

function abrirMinimapaCR(){
  if(!GS.isMaster()) return;
  const state = GS.gameState;
  if(!state || !state.rooms){ toast('Minimapa indisponível.', 'var(--text2)'); return; }
  let host = document.getElementById('minimapa-cr');
  if(!host){ host = document.createElement('div'); host.id = 'minimapa-cr'; document.body.appendChild(host); }
  host.style.display = 'flex';
  renderMinimapaCR();
}

function renderMinimapaCR(){
  const host = document.getElementById('minimapa-cr');
  const state = GS.gameState;
  if(!host || !state || !state.rooms) return;
  const D = window.Difficulty;
  const ep = state.expected_party || { heroes: 4, level: 1 };
  const heroes = (_minimapaPreviewHeroes != null) ? _minimapaPreviewHeroes : ep.heroes;
  const pod = D ? D.poder(heroes, ep.level) : Math.max(1, heroes * ep.level);
  const nd = _crPorSalaMapa(state);
  // Bounds do mapa (para posicionar as salas em %).
  let maxX = 1, maxY = 1;
  state.rooms.forEach(r => { maxX = Math.max(maxX, r.x + r.w); maxY = Math.max(maxY, r.y + r.h); });
  const salas = state.rooms.map(r => {
    const cr = nd.porRoom[r.id] || 0;
    const f = D ? D.faixa(cr, pod) : { color: '#888', label: '' };
    const left = (r.x / maxX) * 100, top = (r.y / maxY) * 100;
    const w = (r.w / maxX) * 100, h = (r.h / maxY) * 100;
    return `<div class="mm-sala" title="${f.label} (CR ${cr.toFixed(2)})" style="left:${left}%;top:${top}%;width:${w}%;height:${h}%;background:${f.color}">` +
           `<span>${cr.toFixed(1)}</span></div>`;
  }).join('');
  const medioF = D ? D.faixa(nd.medio, pod) : { color: '#888', label: '' };
  const sel = [2,4,6].map(n => {
    const on = ((_minimapaPreviewHeroes != null ? _minimapaPreviewHeroes : ep.heroes) === n);
    return `<button data-mmprev="${n}" class="mm-prev${on ? ' on' : ''}">${n}</button>`;
  }).join('');
  host.innerHTML =
    `<div class="mm-box">` +
    `<div class="mm-head"><b>🗺️ Mapa de CR</b> — CR médio: <span style="color:${medioF.color}">${nd.medio.toFixed(2)} (${medioF.label})</span>` +
    `<button class="mm-close" title="Fechar">✕</button></div>` +
    `<div class="mm-canvas" style="aspect-ratio:${maxX}/${maxY}">${salas}</div>` +
    `<div class="mm-foot"><span>poder ${pod} · preview jogadores:</span> ${sel}</div>` +
    `</div>`;
  host.querySelector('.mm-close').onclick = () => { host.style.display = 'none'; };
  host.querySelectorAll('.mm-prev').forEach(b => {
    b.onclick = () => {
      const n = parseInt(b.dataset.mmprev, 10);
      _minimapaPreviewHeroes = (_minimapaPreviewHeroes === n) ? null : n;
      renderMinimapaCR();
    };
  });
}
```

- [ ] **Step 2: Fechar por Esc + esconder fora do jogo / para não-mestre**

No handler global de `keydown` (busque `'Escape'` em game.js), adicione junto às outras limpezas:

```javascript
  if(e.key==='Escape'){ const mm=document.getElementById('minimapa-cr'); if(mm&&mm.style.display!=='none'){ mm.style.display='none'; e.preventDefault(); return; } }
```

Em `showScreen` (onde `#hud-mestre`/`#ficha-monstro` são escondidos ao sair de `screen-game`, ~linha 325), adicione:

```javascript
    const mm2 = document.getElementById('minimapa-cr'); if(mm2) mm2.style.display = 'none';
```

- [ ] **Step 3: Verificar sintaxe**

Run: `node --check game.js` → sem erro.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(mestre): minimapa de CR (salas com faixa, CR medio, preview 2/4/6)"
```

---

## Task 3: CSS do minimapa

**Files:** Modify `game.css`

- [ ] **Step 1: Estilos**

Em `game.css` (perto dos estilos `#ficha-monstro`/`.mestre-*`), adicione:

```css
#minimapa-cr{ position:fixed; inset:0; z-index:120; display:none; align-items:center; justify-content:center; background:rgba(0,0,0,.55); }
#minimapa-cr .mm-box{ background:var(--dark-panel,rgba(20,16,12,.98)); border:1px solid var(--border,#5a4632); border-radius:12px; padding:14px 16px; width:min(560px,92vw); box-shadow:0 8px 40px rgba(0,0,0,.6); color:var(--text,#e8ddc8); }
#minimapa-cr .mm-head{ display:flex; align-items:center; gap:8px; margin-bottom:8px; }
#minimapa-cr .mm-head b{ color:var(--gold,#d9b45a); }
#minimapa-cr .mm-close{ margin-left:auto; background:none; border:none; color:var(--text2,#a89878); cursor:pointer; font-size:1rem; }
#minimapa-cr .mm-canvas{ position:relative; width:100%; background:#15100a; border:1px solid #3a2f22; border-radius:6px; }
#minimapa-cr .mm-sala{ position:absolute; border:1px solid rgba(0,0,0,.4); border-radius:3px; display:flex; align-items:center; justify-content:center; font-size:.8rem; font-weight:bold; color:#1a1206; box-sizing:border-box; overflow:hidden; }
#minimapa-cr .mm-foot{ margin-top:10px; display:flex; align-items:center; gap:6px; font-size:.85rem; }
#minimapa-cr .mm-prev{ padding:2px 9px; cursor:pointer; }
#minimapa-cr .mm-prev.on{ outline:2px solid var(--gold,#d9b45a); }
```

- [ ] **Step 2: Verificação no navegador**

Suba o servidor (do worktree/repo apropriado) e, como mestre em uma masmorra, clique no 🗺️: confirme o mapa das salas coloridas por faixa, o CR de cada sala, o CR médio no topo, e o seletor 2/4/6 recomputando as cores. Confirme que um cliente-jogador vê 🎒 (inventário) e NÃO o mapa.

- [ ] **Step 3: Commit**

```bash
git add game.css
git commit -m "feat(mestre): CSS do minimapa de CR"
```

---

## Task 4: Documentação (CLAUDE.md)

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1: Nota de arquitetura**

Após a nota "Modo Mestre — Camada B: Reforços do Mestre", adicione um parágrafo `>` descrevendo a Camada C: `cr` unificado (`monster_cr`), `expected_party`, `src/difficulty.js` (faixas compartilhadas), termômetro no editor, e o minimapa de CR do mestre em jogo (`#ficha-fab`→🗺️ só `GS.isMaster()`, `abrirMinimapaCR`/`renderMinimapaCR`, CR médio = média das salas, preview 2/4/6). Cite que é só-mestre/design-time (sem efeito em runtime) e aponte spec/planos `2026-07-15-modo-mestre-camada-c*`.

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mestre): Camada C (ND unificado + termometro + minimapa) no CLAUDE.md"
```

---

## Verificação final (Fase C-b)

1. `node --check game.js` — sem erro.
2. Verificação no navegador: como mestre, 🗺️ abre o minimapa (salas/CR/faixa/médio/2-4-6); como jogador, 🎒 abre o inventário e não há minimapa.
3. Commitar só `game.js`/`game.css`/`CLAUDE.md` (nunca o WIP de monstros do usuário).
