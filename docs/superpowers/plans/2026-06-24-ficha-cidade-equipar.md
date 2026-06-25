# Ficha do personagem na cidade (equipar compras) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir abrir a ficha do personagem (atributos + equipamento) na tela da cidade clicando no próprio card de herói, e equipar/desequipar/usar os itens comprados na loja.

**Architecture:** Mudança **somente client-side** em `game.js` (render). A lógica de equipar já vive em `gameState.js` (`GS.equiparItemComprado` / `GS.desequiparItemComprado` / `GS.aplicarConsumivel`). O overlay reaproveita `renderConteudoAtributosFichaJogo` (atributos) e o padrão de `renderPurchasedItems` (slots de equipamento). Sem mudanças em `server.py` nem no protocolo.

**Tech Stack:** Vanilla JS (sem bundler), DOM puro, padrões existentes de `game.js`.

**Spec:** `docs/superpowers/specs/2026-06-24-ficha-cidade-equipar-design.md`

**Verificação:** Não há harness de teste unitário para `game.js`. Cada task valida sintaxe com `node --check game.js` (gate automático) e a Task 4 faz verificação manual no app.

---

### Task 1: Render do equipamento da ficha da cidade

Cria as duas funções de render do bloco de equipamento (equipado + comprados), reaproveitando as constantes/helpers já definidos logo acima (`_TIPO_ITEM_EMOJI`, `_TIPO_ITEM_LABEL`, `_EQUIPADO_SLOTS`, `aplicarTooltipAoItem`) e os métodos de `GS`. Ainda não é alcançável pela UI (a Task 3 liga o clique).

**Files:**
- Modify: `game.js` — inserir **logo após** a função `desequiparComprado` (atualmente termina em game.js:9640, antes de `let _openChestId = null;`)

- [ ] **Step 1: Inserir as funções de render do equipamento**

Inserir este bloco imediatamente após o fechamento de `function desequiparComprado(slot){ ... }` (linha ~9640) e antes de `let _openChestId = null;`:

```js
// ── Ficha do personagem na CIDADE: bloco de EQUIPAMENTO ───────────────────────
// Reaproveita o padrão de renderPurchasedItems (equipado + comprados) mas escreve
// num container próprio (id="ficha-cidade-equip") e se auto-atualiza via
// _refreshFichaCidade — pois renderMyPanel(GS.gameState) não existe na cidade
// (GS.gameState é null). Equipar é client-side (GS.getHeroiAtivo), igual à masmorra.
function _renderFichaCidadeEquip(container){
  container.innerHTML = '';
  const heroi = GS.getHeroiAtivo ? GS.getHeroiAtivo() : null;
  if(!heroi){ container.textContent = 'Sem dados do herói.'; return; }

  // ── Equipado ──
  const tEq = document.createElement('div');
  tEq.className = 'section-title';
  tEq.textContent = 'Equipado';
  container.appendChild(tEq);

  const equipados = _EQUIPADO_SLOTS
    .map(s => ({ ...s, it: heroi.equipado && heroi.equipado[s.key] }))
    .filter(x => x.it);
  if(equipados.length){
    const g = document.createElement('div');
    g.className = 'bag-grid';
    for(const {key, label, it} of equipados){
      const slot = document.createElement('div');
      slot.className = 'bag-slot filled';
      slot.title = it.nome;
      slot.innerHTML = `
        <div class="bag-slot-num" style="font-size:.5rem;opacity:.7">${label}</div>
        <div class="bag-slot-emoji">${_TIPO_ITEM_EMOJI[it.tipo] || '📦'}</div>
        <div class="bag-slot-name">${it.nome}</div>`;
      aplicarTooltipAoItem(slot, it.id);
      const btn = document.createElement('button');
      btn.className = 'bag-slot-btn';
      btn.textContent = '✕ Remover';
      btn.onclick = () => { if(GS.desequiparItemComprado(key)) _refreshFichaCidade(); };
      slot.appendChild(btn);
      g.appendChild(slot);
    }
    container.appendChild(g);
  } else {
    const none = document.createElement('div');
    none.style.cssText = 'color:#8a7a5a;font-size:11px;padding:2px 0 6px;';
    none.textContent = 'Nada equipado.';
    container.appendChild(none);
  }

  // ── Comprados na Loja ──
  const comprados = Array.isArray(heroi.inventario)
    ? heroi.inventario.map((it,idx)=>({it,idx})).filter(x=>x.it)
    : [];
  const tComp = document.createElement('div');
  tComp.className = 'section-title';
  tComp.textContent = `Comprados na Loja (${comprados.length})`;
  container.appendChild(tComp);

  if(!comprados.length){
    const none = document.createElement('div');
    none.style.cssText = 'color:#8a7a5a;font-size:11px;padding:2px 0;';
    none.textContent = 'Compre itens nas lojas para equipar.';
    container.appendChild(none);
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'bag-grid';
  for(const {it, idx} of comprados){
    const slot = document.createElement('div');
    slot.className = 'bag-slot filled';
    slot.title = it.nome;
    slot.innerHTML = `
      <div class="bag-slot-emoji">${_TIPO_ITEM_EMOJI[it.tipo] || '📦'}</div>
      <div class="bag-slot-name">${it.nome}</div>
      <div class="bag-slot-type">${_TIPO_ITEM_LABEL[it.tipo] || '📦 Item'}</div>`;
    aplicarTooltipAoItem(slot, it.id);
    if(it.tipo === 'consumivel'){
      const btn = document.createElement('button');
      btn.className = 'bag-slot-btn use';
      btn.textContent = '▶ Usar';
      btn.title = 'Recupera fome/sede';
      btn.onclick = () => {
        GS.aplicarConsumivel(it);
        heroi.inventario[idx] = null;
        _refreshFichaCidade();
        toast(`Usou ${it.nome}`, 'var(--gold)');
      };
      slot.appendChild(btn);
    } else if(it.tipo !== 'municao'){
      const btn = document.createElement('button');
      btn.className = 'bag-slot-btn equip';
      btn.textContent = '⚙ Equipar';
      btn.onclick = () => { if(GS.equiparItemComprado(idx)) _refreshFichaCidade(); };
      slot.appendChild(btn);
    }
    grid.appendChild(slot);
  }
  container.appendChild(grid);
}

// Re-renderiza apenas o bloco de equipamento do overlay da ficha da cidade.
function _refreshFichaCidade(){
  const c = document.getElementById('ficha-cidade-equip');
  if(c) _renderFichaCidadeEquip(c);
}
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída (exit 0). Qualquer erro de sintaxe é falha.

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(ficha-cidade): render do bloco de equipamento (equipar/remover/usar)"
```

---

### Task 2: Overlay `abrirFichaCidade()`

Cria o modal que compõe cabeçalho + atributos (função reusada) + o bloco de equipamento da Task 1. Ainda não alcançável pela UI.

**Files:**
- Modify: `game.js` — inserir **logo após** `_refreshFichaCidade` (criada na Task 1)

**Dependências já existentes (confirmadas):** `_classIdParaHeroiKey` (game.js:6651), `renderConteudoAtributosFichaJogo` (game.js:2296), `HERO_DATA` / `GS.HERO_DATA`, `GS.cityState`, `toast`. O registro de jogador de `GS.cityState.players` traz `name`, `class_name`, `class_id`, `level`, `hp`, `max_hp`, `str_`, `dex`, `con_`, `int_` (server.py:3367 envia o dict completo).

- [ ] **Step 1: Inserir a função do overlay**

Inserir este bloco imediatamente após `function _refreshFichaCidade(){ ... }`:

```js
// Abre o overlay da ficha do herói LOCAL na cidade: cabeçalho + atributos
// (renderConteudoAtributosFichaJogo, alimentado pelo registro de cityState) +
// equipamento (_renderFichaCidadeEquip). Só o próprio herói (ver _updateCityHeroBar).
function abrirFichaCidade(){
  const anterior = document.getElementById('ficha-cidade-overlay');
  if(anterior) anterior.remove();

  const cityP = (GS.cityState && GS.cityState.players)
    ? GS.cityState.players.find(p => p.id === GS.myPid)
    : null;
  if(!cityP){ toast('Ficha indisponível.', 'var(--gold)'); return; }

  const heroiKey = _classIdParaHeroiKey(cityP.class_id || cityP.cls || cityP.key);
  const heroi = (typeof HERO_DATA !== 'undefined' && HERO_DATA[heroiKey])
    || (GS.HERO_DATA && GS.HERO_DATA[heroiKey]);
  if(!heroi){ toast('Ficha indisponível.', 'var(--gold)'); return; }

  const overlay = document.createElement('div');
  overlay.id = 'ficha-cidade-overlay';
  overlay.style.cssText = `position:fixed; inset:0; background:rgba(0,0,0,0.80);
    z-index:300; display:flex; align-items:center; justify-content:center;
    opacity:0; transition:opacity 0.3s ease;`;

  const container = document.createElement('div');
  container.style.cssText = `width:340px; max-height:88vh; overflow-y:auto;
    background:rgba(10,8,5,0.98); border:1px solid #c8a951; position:relative;`;

  // Cabeçalho — retrato, nome, classe, nível (do registro de cityState)
  const cab = document.createElement('div');
  cab.style.cssText = `padding:16px 20px 12px; border-bottom:1px solid #c8a95133;
    display:flex; align-items:center; gap:12px;`;
  cab.innerHTML = `
    <img src="${heroi.portrait || ''}"
         style="width:52px;height:52px;object-fit:cover;object-position:top;border:1px solid #c8a95166;"
         onerror="this.style.display='none'"/>
    <div style="flex:1;">
      <div style="font-family:'Cinzel Decorative',serif;color:#c8a951;font-size:14px;">${cityP.name || heroi.name || heroi.nome || 'Herói'}</div>
      <div style="color:#8a7a5a;font-size:10px;letter-spacing:3px;margin-top:2px;">${cityP.class_name || heroi.class || heroi.classeSelecao || ''}</div>
      <div style="color:#c8b89a;font-size:10px;margin-top:4px;">NÍVEL ${cityP.level || heroi.nivel || 1}</div>
    </div>
    <button onclick="document.getElementById('ficha-cidade-overlay').remove()"
            style="background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:11px;padding:4px 10px;cursor:pointer;align-self:flex-start;">✕</button>`;

  // Conteúdo — atributos (reusado) + bloco de equipamento
  const conteudo = document.createElement('div');
  conteudo.style.cssText = 'padding:16px 20px;';
  conteudo.innerHTML = renderConteudoAtributosFichaJogo(heroi, cityP);

  const equipWrap = document.createElement('div');
  equipWrap.id = 'ficha-cidade-equip';
  equipWrap.style.cssText = 'margin-top:16px;border-top:1px solid #c8a95133;padding-top:12px;';
  conteudo.appendChild(equipWrap);

  container.appendChild(cab);
  container.appendChild(conteudo);
  overlay.appendChild(container);
  document.body.appendChild(overlay);

  _renderFichaCidadeEquip(equipWrap);

  // Clicar fora fecha
  overlay.onclick = (e) => { if(e.target === overlay) overlay.remove(); };
  requestAnimationFrame(() => { overlay.style.opacity = '1'; });
}
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída (exit 0).

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(ficha-cidade): overlay da ficha (cabeçalho + atributos + equipamento)"
```

---

### Task 3: Ponto de entrada — card de herói clicável

Torna **apenas** o card do próprio jogador clicável na barra de heróis da cidade, abrindo a ficha. Cards dos outros permanecem inalterados. Após esta task, a feature funciona ponta-a-ponta.

**Files:**
- Modify: `game.js` — função `_updateCityHeroBar` (game.js:918-931)

- [ ] **Step 1: Substituir o corpo de `_updateCityHeroBar`**

Substituir exatamente este trecho (game.js:918-931):

```js
function _updateCityHeroBar(msg){
  const bar=document.getElementById('city-hero-bar'); if(!bar||!msg) return;
  const gold=msg.players.reduce((s,p)=>s+(p.gold||0),0);
  bar.innerHTML=msg.players.map(p=>{
    const isMe=p.id===GS.myPid;
    const hpPct=p.max_hp>0?p.hp/p.max_hp*100:0;
    const st=p.hp<=0?'dead':(hpPct<40?'wounded':'');
    return `<div class="city-hcard${isMe?' me':''}">
      <span style="font-size:18px;line-height:1">${p.emoji}</span>
      <div><div class="city-hcard-name">${p.name}</div>
           <div class="city-hcard-hp ${st}">${p.hp}/${p.max_hp} HP</div></div>
    </div>`;
  }).join('')+`<div class="city-gold-badge">💰 ${gold} Ouro</div>`;
}
```

por:

```js
function _updateCityHeroBar(msg){
  const bar=document.getElementById('city-hero-bar'); if(!bar||!msg) return;
  const gold=msg.players.reduce((s,p)=>s+(p.gold||0),0);
  bar.innerHTML=msg.players.map(p=>{
    const isMe=p.id===GS.myPid;
    const hpPct=p.max_hp>0?p.hp/p.max_hp*100:0;
    const st=p.hp<=0?'dead':(hpPct<40?'wounded':'');
    // Só o card do próprio jogador é clicável (abre a ficha p/ equipar compras).
    const meAttrs=isMe?' id="city-hcard-me" title="Clique para abrir sua ficha" style="cursor:pointer"':'';
    return `<div class="city-hcard${isMe?' me':''}"${meAttrs}>
      <span style="font-size:18px;line-height:1">${p.emoji}</span>
      <div><div class="city-hcard-name">${p.name}${isMe?' 🎒':''}</div>
           <div class="city-hcard-hp ${st}">${p.hp}/${p.max_hp} HP</div></div>
    </div>`;
  }).join('')+`<div class="city-gold-badge">💰 ${gold} Ouro</div>`;
  const meCard=document.getElementById('city-hcard-me');
  if(meCard) meCard.onclick=()=>abrirFichaCidade();
}
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída (exit 0).

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(ficha-cidade): abrir ficha ao clicar no próprio card de herói"
```

---

### Task 4: Verificação manual no app + nota de documentação

Valida o fluxo real no navegador e registra a feature no CLAUDE.md.

**Files:**
- Modify: `CLAUDE.md` — seção de protocolo/estado (nota breve)

- [ ] **Step 1: Subir o servidor**

Run: `python server.py` (ou `iniciar.bat`)
Abrir `http://localhost:8765/index.html`, criar sala, selecionar classe, iniciar e chegar à cidade (ou, em campanha, voltar à cidade).

- [ ] **Step 2: Verificar o fluxo manualmente**

1. Comprar um equipamento numa loja (ex.: Ferreiro → uma arma).
2. Clicar no **próprio** card de herói (barra do topo, com 🎒) → a ficha abre com atributos (HP/CA/atributos) + seções "Equipado" e "Comprados na Loja".
3. Clicar **⚙ Equipar** num item comprado → ele migra para "Equipado" (overlay atualiza sozinho).
4. Clicar **✕ Remover** → volta para "Comprados".
5. Comprar/usar um consumível → **▶ Usar** some o item da lista.
6. Clicar no card de **outro** herói → nada acontece (não clicável).
7. Entrar na masmorra → o item equipado na cidade continua equipado no painel lateral (mesmo modelo `GS.getHeroiAtivo`).

Expected: todos os passos conforme descrito; sem erros no console do navegador.

- [ ] **Step 3: Registrar no CLAUDE.md**

Adicionar, na seção `Server → Client` (perto da nota de `city_state`) ou na seção "Estado do Projeto", a linha:

```markdown
> **Ficha na cidade:** clicar no próprio card de herói (barra do topo de
> `screen-city`) abre `abrirFichaCidade()` — overlay com atributos
> (`renderConteudoAtributosFichaJogo`) + equipamento (`_renderFichaCidadeEquip`)
> para equipar/desequipar/usar itens comprados na loja. Equipar é client-side
> (`GS.equiparItemComprado`/`desequiparItemComprado`), sem mudança de protocolo.
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(ficha-cidade): documentar a ficha acessível na cidade"
```

---

## Notas de verificação cruzada (spec → plano)

- **Acesso por clique no próprio card** → Task 3.
- **Conteúdo: atributos + equipamento** → Task 2 (atributos reusados) + Task 1 (equipamento).
- **Escopo: só o meu herói** → Task 3 (só o card `isMe` recebe `onclick`).
- **Sem mudanças no servidor/protocolo** → nenhuma task toca `server.py`.
- **Refresh isolado (não usa `renderMyPanel`)** → `_refreshFichaCidade` na Task 1.
- **Equipar continua client-side** → todas as ações chamam métodos de `GS`.
