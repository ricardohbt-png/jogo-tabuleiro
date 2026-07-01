# Ficha do personagem na cidade (v2: fotos + painel + drag-drop) — Plano

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar a foto (rosto, 3:4) de cada herói nos cards da cidade; clicar abre a ficha completa num painel lateral esquerdo deslizante (atributos + equipamento + bolsa), com equipar/desequipar e organização da bolsa por arrastar-e-soltar usando o modelo autoritativo do servidor; ficha de outros heróis em só-leitura.

**Architecture:** Servidor autoritativo (`player.gear`/`player.bag`). Pequena mudança em `server.py` (broadcast ciente da fase + novo `reorder_bag`); o grosso é cliente (`game.js` + `game.css`). Substitui a v1 cosmética.

**Tech Stack:** Python `asyncio`/`websockets` (servidor), Vanilla JS + DOM + HTML5 Drag-and-Drop (cliente), CSS.

**Spec:** `docs/superpowers/specs/2026-06-24-ficha-cidade-equipar-design.md`

**Verificação:** Servidor tem harness `tools/test_*.py` (asyncio) → Task 1 é TDD de verdade. Cliente não tem harness unitário → Task 5 valida sintaxe carregando a página + exercício manual. (Node não está instalado nesta máquina; o gate de sintaxe do cliente é carregar `index.html` pelo próprio servidor e checar o console.)

---

### Task 1: Servidor — broadcast ciente da fase + `reorder_bag`

**Files:**
- Create: `tools/test_ficha_cidade.py`
- Modify: `server.py` — adicionar `push_state_or_city`; trocar a chamada final em `handle_equip_from_bag` (server.py:6514), `handle_equip_offhand` (~6588) e `handle_unequip` (server.py:6631); adicionar `handle_reorder_bag`; rotear `reorder_bag` (após server.py:13045).

- [ ] **Step 1: Escrever o teste falhando**

Criar `tools/test_ficha_cidade.py`:

```python
"""Ficha na cidade — equipar/desequipar/reordenar com broadcast ciente da fase.
  • Equipar na fase 'city' move bag→gear e emite city_state (não game_state).
  • Desequipar na cidade devolve à bolsa e emite city_state.
  • reorder_bag reordena a bolsa (com clamp de índices fora do intervalo).
  • Equipar na masmorra ('playing') continua emitindo game_state (não regrediu).
Roda da raiz: python tools/test_ficha_cidade.py"""
import asyncio, sys, os
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, SHOP_WEAPONS

def shop_w(wid):
    return deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == wid))

def setup(phase="city"):
    r = GameRoom("TEST")
    calls = {"push_state": 0, "city": 0}
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    async def cap_push(*a, **k): calls["push_state"] += 1
    async def cap_city(*a, **k): calls["city"] += 1
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.push_state = cap_push; r.broadcast_city_state = cap_city
    r.send_to = cap_send
    r.phase = phase
    r._calls = calls; r._errs = errs
    return r

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # [1] Equipar na cidade → city_state, item em gear
    print("\n[1] Equipar na fase city")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = [shop_w("longsword")]
    await r.handle_equip_from_bag("p1", 0)
    check("equipou (gear.weapon=longsword)", (w["gear"].get("weapon") or {}).get("id") == "longsword")
    check("emitiu city_state", r._calls["city"] >= 1)
    check("NÃO emitiu game_state", r._calls["push_state"] == 0)

    # [2] Desequipar na cidade → volta p/ bolsa
    print("\n[2] Desequipar na fase city")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = []
    w["gear"]["head"] = {"id": "helm", "name": "Elmo", "emoji": "⛑", "item_slot": "head"}
    await r.handle_unequip("p1", "head")
    check("head vazio após desequipar", w["gear"].get("head") is None)
    check("item voltou p/ bolsa", any((it or {}).get("id") == "helm" for it in w["bag"]))
    check("emitiu city_state", r._calls["city"] >= 1 and r._calls["push_state"] == 0)

    # [3] reorder_bag (incl. clamp)
    print("\n[3] reorder_bag")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    a = {"id": "a"}; b = {"id": "b"}; c = {"id": "c"}
    w["bag"] = [a, b, c]
    await r.handle_reorder_bag("p1", 0, 2)
    check("moveu A para o fim", [it["id"] for it in w["bag"]] == ["b", "c", "a"])
    await r.handle_reorder_bag("p1", 2, 0)
    check("voltou A p/ início", [it["id"] for it in w["bag"]] == ["a", "b", "c"])
    await r.handle_reorder_bag("p1", 10, 0)
    check("from inválido = no-op", [it["id"] for it in w["bag"]] == ["a", "b", "c"])
    await r.handle_reorder_bag("p1", 0, 99)
    check("to clampa p/ o fim", [it["id"] for it in w["bag"]] == ["b", "c", "a"])
    check("emitiu city_state", r._calls["city"] >= 1)

    # [4] Não-regressão: equipar na masmorra → game_state
    print("\n[4] Equipar na fase playing (não-regressão)")
    r = setup("playing")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = [shop_w("longsword")]
    await r.handle_equip_from_bag("p1", 0)
    check("equipou na masmorra", (w["gear"].get("weapon") or {}).get("id") == "longsword")
    check("emitiu game_state", r._calls["push_state"] >= 1)
    check("NÃO emitiu city_state", r._calls["city"] == 0)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `python tools/test_ficha_cidade.py`
Expected: FALHA — `AttributeError: 'GameRoom' object has no attribute 'handle_reorder_bag'` (e/ou checks de city_state falhando, pois os handlers ainda chamam `push_state`).

- [ ] **Step 3: Implementar no `server.py`**

(3a) Adicionar o helper logo **antes** de `async def handle_equip_from_bag` (server.py:6504). Procure a linha `    async def handle_equip_from_bag(self, pid, slot_index):` e insira antes:

```python
    async def push_state_or_city(self):
        """Broadcast ciente da fase: na cidade os clientes estão em screen-city e
        usam city_state; na masmorra usam game_state (push_state)."""
        if self.phase == "city":
            await self.broadcast_city_state()
        else:
            await self.push_state()

    async def handle_reorder_bag(self, pid, from_index, to_index):
        """Reordena a bolsa do jogador (organização por arrastar-e-soltar).
        Clampa índices fora do intervalo; from inválido é no-op."""
        p = self.players.get(pid)
        if not p:
            return
        bag = p["bag"]
        if from_index < 0 or from_index >= len(bag):
            return
        item = bag.pop(from_index)
        to_index = max(0, min(to_index, len(bag)))
        bag.insert(to_index, item)
        await self.push_state_or_city()

```

(3b) Trocar a chamada final dos 3 handlers de `await self.push_state()` para `await self.push_state_or_city()`. São 3 ocorrências, cada uma é a ÚLTIMA linha do respectivo handler:
- em `handle_equip_from_bag` (server.py:6514),
- em `handle_equip_offhand` (procure a linha final `await self.push_state()` dentro dela, ~6588+),
- em `handle_unequip` (server.py:6631).

⚠️ NÃO faça replace-all cego de `await self.push_state()` no arquivo (há muitas outras chamadas legítimas em outros métodos). Edite APENAS dentro desses três handlers — confira que o método que você está editando é um dos três. Cada edição:

```python
        await self.push_state_or_city()
```
no lugar de:
```python
        await self.push_state()
```

(3c) Rotear `reorder_bag`. Após o bloco `unequip` (server.py:13044-13045):

```python
                elif t == "unequip":
                    if room: await room.handle_unequip(pid, msg.get("slot_key"))
```
inserir:
```python

                elif t == "reorder_bag":
                    if room: await room.handle_reorder_bag(
                        pid, int(msg.get("from_index", -1)), int(msg.get("to_index", 0)))
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `python tools/test_ficha_cidade.py`
Expected: `===== RESULTADO: 14 passaram, 0 falharam =====` (exit 0).

Rodar também a não-regressão de equipar:
Run: `python tools/test_equipar.py`
Expected: todos ✅ (exit 0).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_ficha_cidade.py
git commit -m "feat(ficha-cidade): equipar/reordenar na cidade (broadcast ciente da fase + reorder_bag)"
```

---

### Task 2: Cliente — remover a v1 e adicionar o sender `reorderBag`

Volta a cidade ao estado limpo (sem a ficha cosmética) e adiciona o sender que faltava. Após esta task, NÃO há acesso à ficha na cidade (baseline limpo) — o painel novo entra na Task 3/4.

**Files:**
- Modify: `game.js` — remover o bloco v1 (game.js:9646-9813, do comentário `// ── Ficha do personagem na CIDADE: bloco de EQUIPAMENTO` até o fim de `abrirFichaCidade`, antes de `let _openChestId = null;`); reverter `_updateCityHeroBar` (game.js:918) ao original; adicionar `reorderBag` perto de `unequipSlot` (game.js:10087).

- [ ] **Step 1: Remover as funções da v1**

Apagar TODO o bloco que vai do comentário:
```js
// ── Ficha do personagem na CIDADE: bloco de EQUIPAMENTO ───────────────────────
```
(linha ~9646) até o fechamento de `function abrirFichaCidade(){ … }` (linha ~9813), inclusive a linha em branco seguinte — parando imediatamente antes de:
```js
let _openChestId = null;   // currently-open chest id (for auto-refresh)
```
São removidas: `_renderFichaCidadeEquip`, `_refreshFichaCidade` e `abrirFichaCidade` (versão modal da v1).

- [ ] **Step 2: Reverter `_updateCityHeroBar` ao original**

Substituir a função atual (com `meAttrs`/🎒/onclick da v1) por esta versão original:

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

- [ ] **Step 3: Adicionar o sender `reorderBag`**

Após `unequipSlot` (game.js:10087-10089, termina em `}`), inserir:

```js
function reorderBag(fromIndex, toIndex){
  send({type:'reorder_bag', from_index: fromIndex, to_index: toIndex});
}
```

- [ ] **Step 4: Validar sintaxe carregando a página**

Subir o servidor (`python server.py`) e abrir `http://localhost:8765/index.html`. No console do navegador, conferir que NÃO há erro de parse e que os senders existem:
Run (no console / via ferramenta de preview): `typeof reorderBag === 'function' && typeof _updateCityHeroBar === 'function' && typeof abrirFichaCidade === 'undefined'`
Expected: `true` (abrirFichaCidade ainda não existe nesta task; reentra na Task 3).

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "refactor(ficha-cidade): remover v1 cosmética e adicionar sender reorderBag"
```

---

### Task 3: Cliente — painel lateral + render da ficha + drag-and-drop

Sistema completo do painel (CSS + DOM + render do corpo + drag-and-drop + abrir/fechar/refresh). Ainda NÃO ligado aos cards (Task 4 liga). Define `abrirFichaCidade(pid)`.

**Files:**
- Modify: `game.css` — adicionar estilos do painel (no fim do arquivo).
- Modify: `game.js` — inserir o sistema do painel logo após `reorderBag` (criado na Task 2).

- [ ] **Step 1: CSS do painel**

Adicionar ao FINAL de `game.css`:

```css
/* ── Ficha do personagem na cidade: painel lateral esquerdo ─────────────────── */
#ficha-cidade-backdrop{ position:fixed; inset:0; background:rgba(0,0,0,.5);
  z-index:299; opacity:0; pointer-events:none; transition:opacity .26s ease; }
#ficha-cidade-backdrop.open{ opacity:1; pointer-events:auto; }
#ficha-cidade-panel{ position:fixed; left:0; top:0; height:100vh; width:300px;
  max-width:90vw; background:rgba(10,8,5,.98); border-right:1px solid #c8a951;
  z-index:300; transform:translateX(-100%); transition:transform .26s ease;
  display:flex; flex-direction:column; }
#ficha-cidade-panel.open{ transform:translateX(0); }
#ficha-cidade-close{ position:absolute; top:8px; right:8px; background:transparent;
  border:1px solid #4a4a4a; color:#8a7a5a; font-size:13px; padding:2px 9px;
  cursor:pointer; z-index:1; }
.fc-head{ padding:14px 16px 10px; border-bottom:1px solid #c8a95133;
  display:flex; gap:12px; align-items:center; }
.fc-head-photo{ width:54px; aspect-ratio:3/4; object-fit:cover;
  object-position:top center; border:1px solid #c8a95166; flex-shrink:0; }
.fc-head-name{ font-family:'Cinzel Decorative',serif; color:#c8a951; font-size:14px; }
.fc-head-class{ color:#8a7a5a; font-size:10px; letter-spacing:2px; margin-top:2px; }
.fc-head-lvl{ color:#c8b89a; font-size:10px; margin-top:3px; }
.fc-body{ padding:14px 16px; overflow-y:auto; flex:1; }
#ficha-cidade-panel .eq-slot.drop-target,
#ficha-cidade-panel .bag-slot.drop-target{ outline:2px dashed #c8a951;
  outline-offset:-2px; }
#ficha-cidade-panel [draggable="true"]{ cursor:grab; }
```

- [ ] **Step 2: Sistema do painel em `game.js`**

Inserir logo após a função `reorderBag` (da Task 2):

```js
// ── Ficha do personagem na CIDADE (v2): painel lateral autoritativo ──────────
// Lê player.gear/player.bag do city_state (modelo autoritativo do servidor).
// Meu herói: equipar/desequipar (botão/clique) + arrastar-e-soltar (reordenar a
// bolsa e equipar/desequipar). Outros heróis: só leitura.
const FC_EQ_SLOTS = [
  {key:'weapon',   label:'Mão Direita', empty:'✊'},
  {key:'off_hand', label:'Mão Esquerda',empty:'🤚'},
  {key:'armor',    label:'Corpo',       empty:'👕'},
  {key:'head',     label:'Cabeça',      empty:'🧢'},
  {key:'ring1',    label:'Anel 1',      empty:'💍'},
  {key:'ring2',    label:'Anel 2',      empty:'💍'},
  {key:'item1',    label:'Item 1',      empty:'📦'},
  {key:'item2',    label:'Item 2',      empty:'📦'},
];
let _fcPanelPid = null;   // pid mostrado no painel (null = fechado)
let _fcDrag = null;       // origem do arraste: {kind:'bag',index} | {kind:'gear',slotKey}

function _fcPlayerAtual(){
  return (GS.cityState && GS.cityState.players)
    ? GS.cityState.players.find(p => p.id === _fcPanelPid) : null;
}

function _fcEhAdaga(item){
  return !!item && (item.id === 'dagger' || /adaga/i.test(item.name || '')) && !!item.die;
}

function abrirFichaCidade(pid){
  _fcPanelPid = pid;
  let panel = document.getElementById('ficha-cidade-panel');
  let back  = document.getElementById('ficha-cidade-backdrop');
  if(!back){
    back = document.createElement('div');
    back.id = 'ficha-cidade-backdrop';
    back.onclick = fecharFichaCidade;
    document.body.appendChild(back);
  }
  if(!panel){
    panel = document.createElement('div');
    panel.id = 'ficha-cidade-panel';
    document.body.appendChild(panel);
  }
  _refreshFichaCidadePanel();
  requestAnimationFrame(() => { panel.classList.add('open'); back.classList.add('open'); });
}

function fecharFichaCidade(){
  _fcPanelPid = null;
  _fcDrag = null;
  const panel = document.getElementById('ficha-cidade-panel');
  const back  = document.getElementById('ficha-cidade-backdrop');
  if(panel) panel.classList.remove('open');
  if(back)  back.classList.remove('open');
}

// Re-renderiza o corpo do painel com o player atual do city_state.
function _refreshFichaCidadePanel(){
  if(_fcPanelPid == null) return;
  const panel = document.getElementById('ficha-cidade-panel');
  if(!panel) return;
  const player = _fcPlayerAtual();
  if(!player){ fecharFichaCidade(); return; }
  panel.innerHTML = '';
  const closeBtn = document.createElement('button');
  closeBtn.id = 'ficha-cidade-close';
  closeBtn.textContent = '✕';
  closeBtn.title = 'Fechar';
  closeBtn.onclick = fecharFichaCidade;
  panel.appendChild(closeBtn);
  renderFichaCidadeBody(panel, player, player.id === GS.myPid);
}

function renderFichaCidadeBody(panel, player, editable){
  // Cabeçalho (foto + nome/classe/nível)
  const heroiKey    = _classIdParaHeroiKey(player.class_id);
  const heroiStatic = (typeof HERO_DATA !== 'undefined' && HERO_DATA[heroiKey])
    || (GS.HERO_DATA && GS.HERO_DATA[heroiKey]) || {};
  const portrait = HERO_PORTRAIT_PATHS[player.class_id] || heroiStatic.portrait || '';
  const head = document.createElement('div');
  head.className = 'fc-head';
  head.innerHTML = `
    <img class="fc-head-photo" src="${portrait}" alt="" onerror="this.style.display='none'"/>
    <div class="fc-head-info">
      <div class="fc-head-name">${player.name || ''}</div>
      <div class="fc-head-class">${player.class_name || ''}${editable ? '' : ' · só leitura'}</div>
      <div class="fc-head-lvl">NÍVEL ${player.level || 1}</div>
    </div>`;
  panel.appendChild(head);

  const body = document.createElement('div');
  body.className = 'fc-body';
  panel.appendChild(body);

  // Atributos (reuso)
  const attr = document.createElement('div');
  attr.innerHTML = renderConteudoAtributosFichaJogo(heroiStatic, player);
  body.appendChild(attr);

  // Equipamento (paper-doll dos 8 slots)
  const gear = player.gear || {};
  const eqTitle = document.createElement('div');
  eqTitle.className = 'section-title'; eqTitle.style.marginTop = '4px';
  eqTitle.textContent = 'Equipamento';
  body.appendChild(eqTitle);
  const eqGrid = document.createElement('div');
  eqGrid.className = 'equip-grid';
  for(const {key, label, empty} of FC_EQ_SLOTS){
    const item = gear[key];
    const slot = document.createElement('div');
    slot.className = 'eq-slot' + (item ? ' filled' : '');
    slot.title = item ? (editable ? `${item.name} — clique/arraste p/ desequipar` : item.name) : label;
    slot.innerHTML = `
      <div class="eq-slot-label">${label}</div>
      <div class="eq-slot-emoji">${item ? item.emoji : `<span style="opacity:.35">${empty}</span>`}</div>
      <div class="eq-slot-name">${item ? item.name : '—'}</div>`;
    if(item) aplicarTooltipAoItem(slot, item.id);
    if(editable && item){
      slot.appendChild(Object.assign(document.createElement('div'),
        {className:'eq-slot-x', textContent:'⤓', title:'Desequipar'}));
      slot.onclick = () => unequipSlot(key);
      slot.draggable = true;
      slot.addEventListener('dragstart', e => { _fcDrag = {kind:'gear', slotKey:key}; e.dataTransfer.effectAllowed = 'move'; });
    }
    if(editable){
      slot.addEventListener('dragover',  e => { if(_fcDrag){ e.preventDefault(); slot.classList.add('drop-target'); } });
      slot.addEventListener('dragleave', () => slot.classList.remove('drop-target'));
      slot.addEventListener('drop',      e => { e.preventDefault(); slot.classList.remove('drop-target'); _fcDropOnGear(key); });
    }
    eqGrid.appendChild(slot);
  }
  body.appendChild(eqGrid);

  // Inventário (bag_size slots)
  const bag     = player.bag || [];
  const bagSize = player.bag_size || 6;
  const bagTitle = document.createElement('div');
  bagTitle.className = 'section-title';
  bagTitle.textContent = `Inventário (${bag.length}/${bagSize})`;
  body.appendChild(bagTitle);
  const bagGrid = document.createElement('div');
  bagGrid.className = 'bag-grid';
  for(let i = 0; i < bagSize; i++){
    const item = bag[i];
    const slot = document.createElement('div');
    if(item){
      const isEquippable = !!(item.item_slot && item.item_slot !== 'bag') || !!item.die;
      const typeLabel = item.die ? '⚔ Arma'
        : item.effect === 'ammo' ? `🏹 Munição (×${item.ammo_count ?? 0})`
        : ({weapon:'⚔ Arma', shield:'🛡 Escudo', armor:'🛡 Armadura', head:'⛑ Cabeça',
            ring:'💍 Anel', item:'🎒 Item', accessory:'📿 Acessório', bag:'🧪 Consumível'}[item.item_slot] || '📦 Item');
      slot.className = 'bag-slot filled';
      slot.title = item.name;
      slot.innerHTML = `
        <div class="bag-slot-num">${i+1}</div>
        <div class="bag-slot-emoji">${item.emoji}</div>
        <div class="bag-slot-name">${item.name}</div>
        <div class="bag-slot-type">${typeLabel}</div>`;
      aplicarTooltipAoItem(slot, item.id);
      if(editable){
        slot.draggable = true;
        slot.addEventListener('dragstart', e => { _fcDrag = {kind:'bag', index:i}; e.dataTransfer.effectAllowed = 'move'; });
        if(isEquippable){
          const allowed = item.allowed_classes;
          const classRestricted = allowed && player.class_id && !allowed.includes(player.class_id);
          const btn = document.createElement('button');
          btn.className = 'bag-slot-btn equip' + (classRestricted ? ' disabled' : '');
          btn.textContent = classRestricted ? '🚫 Classe' : '⚙ Equipar';
          btn.disabled = !!classRestricted;
          btn.title = classRestricted ? `Apenas: ${allowed.join(', ')}` : '';
          if(!classRestricted) btn.onclick = () => equipFromBag(i);
          slot.appendChild(btn);
          if(_fcEhAdaga(item) && !classRestricted){
            const b2 = document.createElement('button');
            b2.className = 'bag-slot-btn equip';
            b2.textContent = '🗡️ 2ª arma';
            b2.title = 'Empunhar na mão esquerda (2ª arma)';
            b2.onclick = () => equipOffhand(i);
            slot.appendChild(b2);
          }
        }
      }
    } else {
      slot.className = 'bag-slot empty-slot';
      slot.innerHTML = `
        <div class="bag-slot-num" style="opacity:.5">${i+1}</div>
        <div class="bag-slot-emoji" style="font-size:1rem;opacity:.4">◻</div>
        <div class="bag-slot-type" style="font-size:.52rem">vazio</div>`;
    }
    if(editable){
      slot.addEventListener('dragover',  e => { if(_fcDrag){ e.preventDefault(); slot.classList.add('drop-target'); } });
      slot.addEventListener('dragleave', () => slot.classList.remove('drop-target'));
      slot.addEventListener('drop',      e => { e.preventDefault(); slot.classList.remove('drop-target'); _fcDropOnBag(i); });
    }
    bagGrid.appendChild(slot);
  }
  body.appendChild(bagGrid);
}

// Drop num slot de EQUIPAMENTO: vindo da bolsa → equipar (off_hand p/ adaga/escudo).
function _fcDropOnGear(slotKey){
  const d = _fcDrag; _fcDrag = null;
  if(!d || d.kind !== 'bag') return;   // gear→gear: ignora
  const player = _fcPlayerAtual();
  const item = player && player.bag ? player.bag[d.index] : null;
  if(!item) return;
  const ehOffhand = slotKey === 'off_hand'
    && (_fcEhAdaga(item) || item.item_slot === 'shield' || item.kind === 'shield');
  if(ehOffhand) equipOffhand(d.index);
  else          equipFromBag(d.index);
}

// Drop num slot da BOLSA: vindo da bolsa → reordenar; vindo do gear → desequipar.
function _fcDropOnBag(toIndex){
  const d = _fcDrag; _fcDrag = null;
  if(!d) return;
  if(d.kind === 'bag'){
    if(d.index === toIndex) return;
    reorderBag(d.index, toIndex);
  } else if(d.kind === 'gear'){
    unequipSlot(d.slotKey);
  }
}
```

- [ ] **Step 3: Validar sintaxe carregando a página**

Subir o servidor e abrir `index.html`. No console, conferir:
Run: `typeof abrirFichaCidade === 'function' && typeof renderFichaCidadeBody === 'function' && typeof _fcDropOnBag === 'function'`
Expected: `true`, sem erros de parse no console.

- [ ] **Step 4: Commit**

```bash
git add game.js game.css
git commit -m "feat(ficha-cidade): painel lateral autoritativo + drag-and-drop (gear/bag)"
```

---

### Task 4: Cliente — fotos nos cards + ligar clique + refresh ao vivo

Liga tudo: fotos 3:4 nos cards, clique abre o painel, e o painel se atualiza quando chega `city_state`. Fecha o painel ao entrar na masmorra.

**Files:**
- Modify: `game.css` — estilo da foto no card (no fim do arquivo).
- Modify: `game.js` — `_updateCityHeroBar` (fotos + onclick); handler `GS.on('cityState', …)` (game.js:18781) p/ refresh; handler `GS.on('enterDungeon', …)` (game.js:18801) p/ fechar.

- [ ] **Step 1: CSS da foto no card**

Adicionar ao FINAL de `game.css`:

```css
/* Foto (rosto, 3:4) nos cards de herói da cidade */
.city-hcard-face{ width:34px; aspect-ratio:3/4; object-fit:cover;
  object-position:top center; border:1px solid #c8a95155; border-radius:3px; flex-shrink:0; }
.city-hcard-face-fallback{ width:34px; aspect-ratio:3/4; display:flex;
  align-items:center; justify-content:center; font-size:18px; background:#0e0c18;
  border:1px solid #2a2848; border-radius:3px; flex-shrink:0; }
```

- [ ] **Step 2: `_updateCityHeroBar` com fotos + clique (todos os cards)**

Substituir a função (revertida na Task 2) por:

```js
function _updateCityHeroBar(msg){
  const bar=document.getElementById('city-hero-bar'); if(!bar||!msg) return;
  const gold=msg.players.reduce((s,p)=>s+(p.gold||0),0);
  bar.innerHTML=msg.players.map(p=>{
    const isMe=p.id===GS.myPid;
    const hpPct=p.max_hp>0?p.hp/p.max_hp*100:0;
    const st=p.hp<=0?'dead':(hpPct<40?'wounded':'');
    const foto=HERO_PORTRAIT_PATHS[p.class_id]||'';
    // Foto 3:4 recortada no rosto; cai para emoji se faltar/erro de carregamento.
    const face = foto
      ? `<img class="city-hcard-face" src="${foto}" alt=""
            onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"/>
         <span class="city-hcard-face-fallback" style="display:none">${p.emoji}</span>`
      : `<span class="city-hcard-face-fallback">${p.emoji}</span>`;
    return `<div class="city-hcard${isMe?' me':''}" data-pid="${p.id}"
                 title="Clique para ver a ficha" style="cursor:pointer">
      ${face}
      <div><div class="city-hcard-name">${p.name}</div>
           <div class="city-hcard-hp ${st}">${p.hp}/${p.max_hp} HP</div></div>
    </div>`;
  }).join('')+`<div class="city-gold-badge">💰 ${gold} Ouro</div>`;
  bar.querySelectorAll('.city-hcard[data-pid]').forEach(card => {
    card.onclick = () => abrirFichaCidade(card.getAttribute('data-pid'));
  });
}
```

- [ ] **Step 3: Refresh ao vivo no handler de `cityState`**

No handler `GS.on('cityState', msg => { … })` (game.js:18781), adicionar como ÚLTIMA linha dentro do callback (logo após `if(window._comprando …){ … }`), antes do `})`:

```js
  // Painel da ficha aberto → re-renderiza com o estado novo (equipar/reordenar).
  if(_fcPanelPid != null) _refreshFichaCidadePanel();
```

- [ ] **Step 4: Fechar o painel ao entrar na masmorra**

No handler `GS.on('enterDungeon', () => { … })` (game.js:18801), adicionar como primeira linha do callback:

```js
  fecharFichaCidade();
```

- [ ] **Step 5: Validar carregando a página**

Subir o servidor e abrir `index.html`. Confirmar no console que não há erro de parse e:
Run: `typeof _updateCityHeroBar === 'function'`
Expected: `true`.

- [ ] **Step 6: Commit**

```bash
git add game.js game.css
git commit -m "feat(ficha-cidade): fotos 3:4 nos cards, clique abre painel, refresh ao vivo"
```

---

### Task 5: Verificação manual no app + documentação

**Files:**
- Modify: `CLAUDE.md` — atualizar a nota da ficha na cidade (substituir a da v1 se existir, ou adicionar).

- [ ] **Step 1: Subir e exercitar o fluxo**

Run: `python server.py` → abrir `http://localhost:8765/index.html`. Criar sala, selecionar classe, iniciar e chegar à cidade (idealmente com 2 jogadores p/ testar o modo só-leitura; com 1 jogador dá p/ testar o próprio).

Verificar:
1. Cada card de herói mostra a **foto do rosto** (3:4). Se a imagem faltar, mostra o emoji.
2. Comprar um equipamento na loja (ex.: Ferreiro → arma).
3. Clicar na **minha** foto → painel desliza da **esquerda** com atributos + equipamento + inventário.
4. Clicar **⚙ Equipar** num item → vai para o slot de equipamento (painel atualiza).
5. Clicar no slot equipado (⤓) → volta para a bolsa.
6. **Arrastar** um item da bolsa para outro slot da bolsa → reordena.
7. **Arrastar** um item da bolsa para um slot de equipamento → equipa; arrastar de volta → desequipa.
8. Clicar na foto de **outro** herói → painel em só-leitura (sem botões/arraste).
9. Entrar na masmorra → o equipamento equipado na cidade persiste no painel lateral do jogo (mesmo `gear`/`bag` do servidor).

Expected: todos os passos conforme descrito; sem erros no console.

- [ ] **Step 2: Atualizar `CLAUDE.md`**

Localizar a nota da ficha na cidade (se a v1 foi documentada, substituí-la). Caso não exista, adicionar na seção "Estado do Projeto", após `- Sistema de cidade e loja de itens entre dungeons`:

```markdown
> **Ficha na cidade (autoritativa):** cada card de herói em `screen-city` mostra a
> foto do rosto (3:4). Clicar abre `abrirFichaCidade(pid)` — painel lateral
> ESQUERDO deslizante com atributos (`renderConteudoAtributosFichaJogo`) +
> equipamento (8 slots de `player.gear`) + inventário (`player.bag`). O próprio
> herói equipa/desequipa (botão/clique) e organiza a bolsa por arrastar-e-soltar
> (reordenar; arrastar p/ um slot equipa; arrastar do slot p/ a bolsa desequipa);
> outros heróis abrem em só-leitura. Usa o modelo AUTORITATIVO do servidor:
> `equip_from_bag`/`equip_offhand`/`unequip`/`reorder_bag`, com broadcast ciente da
> fase (`push_state_or_city` → `broadcast_city_state` na cidade). Cliente:
> `_updateCityHeroBar` (fotos), `renderFichaCidadeBody`, `_refreshFichaCidadePanel`.
```

Se houver uma nota antiga da v1 (`abrirFichaCidade()` modal central / `_renderFichaCidadeEquip`), removê-la.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(ficha-cidade): documentar a ficha autoritativa na cidade (v2)"
```

---

## Verificação cruzada (spec → plano)

- **Fotos 3:4 em todos os cards** → Task 4 (CSS + `_updateCityHeroBar`).
- **Painel lateral esquerdo deslizante** → Task 3 (CSS `#ficha-cidade-panel` + chrome).
- **Atributos + equipamento + bolsa** → Task 3 (`renderFichaCidadeBody`).
- **Equipar/desequipar de verdade na cidade** → Task 1 (broadcast ciente da fase) + Task 3 (botões/clique chamam `equipFromBag`/`unequipSlot`/`equipOffhand`).
- **Drag-and-drop (reordenar + equipar/desequipar)** → Task 3 (handlers `_fcDropOnGear`/`_fcDropOnBag`) + Task 1 (`reorder_bag`).
- **Outros heróis em só-leitura** → Task 3 (`editable = pid===myPid`).
- **Consumíveis só na bolsa (sem usar)** → Task 3 (sem botão "Usar").
- **Refresh ao vivo** → Task 4 (`_refreshFichaCidadePanel` no `cityState`).
- **Remover a v1** → Task 2.
- **Não-regressão da masmorra** → Task 1 (teste [4]).
```
