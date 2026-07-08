# Inventário estilo Diablo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir as duas telas de Equipamento+Inventário duplicadas (cidade e masmorra) por um único modal estilo Diablo II/III, reutilizado nos dois contextos, com paperdoll de 9 slots, bolsa expansível, tooltip com comparação, interação clique-clique + drag, e o visual final aprovado (mármore, borda dourada estilo pergaminho queimado, logotipo real).

**Architecture:** Novo arquivo `src/ui/inventoryModal.js` (renderer isolado, zero lógica de jogo) chamado por `game.js`; duas funções puras novas em `src/gameState.js` (`canPlaceItem`, `compareItemStats`, `isDagger`) + dois novos action-senders (`reorderBag`, `equipOffhand`); um slot novo (`boots`) no servidor. Os dois blocos de renderização antigos (`renderMyPanel`, `renderFichaCidadeBody`) perdem só a parte de Equipamento+Bolsa — o resto (Ações/Habilidades/Encerrar Turno na masmorra; Atributos/Guilda na cidade) fica intacto.

**Tech Stack:** Python 3 (servidor, `websockets`), Vanilla JS (cliente, sem bundler), CSS puro com SVG inline. Testes: `tools/test_*.py` (harness próprio, sem pytest) para o servidor; verificação manual via preview do navegador pro cliente (não existe framework de teste JS neste projeto — ver nota na Task 3).

**Referência:** spec completa em [`docs/superpowers/specs/2026-07-08-inventario-diablo-design.md`](../specs/2026-07-08-inventario-diablo-design.md).

---

## Antes de começar

Confirme que o servidor sobe normalmente antes de mexer em qualquer coisa:

```bash
python server.py
```

Abra `http://localhost:8765/index.html`, crie uma sala, escolha uma classe e confirme que o jogo carrega até a cidade. Deixe o servidor rodando em segundo plano — você vai usá-lo pra verificação manual em várias tasks.

---

### Task 1: Servidor — slot de equipamento "Bota" (TDD)

**Files:**
- Modify: `server.py:3453` (`GEAR_SLOTS`)
- Modify: `server.py:3531-3540` (`make_player`, dict de `gear`)
- Modify: `server.py:8189-8213` (`_slot_category_for_item`)
- Modify: `server.py:8305-8328` (`_executar_equip_from_bag`, dispatch por categoria)
- Test: `tools/test_boots_slot.py`

- [ ] **Step 1: Escreva o teste (vai falhar — o slot ainda não existe)**

Crie `tools/test_boots_slot.py`:

```python
"""Slot de bota (9º slot de equipamento) — infraestrutura apenas, sem itens novos.
  • GEAR_SLOTS inclui "boots"; make_player já nasce com gear["boots"]=None.
  • Equipar um item item_slot="boots" da bolsa vai para gear["boots"].
  • Desequipar bota devolve à bolsa (mesmo fluxo de handle_unequip).
  • Trocar a bota equipada por outra devolve a antiga à bolsa.
  • Conflito de arma de 2 mãos continua intacto com o slot novo (não-regressão).
Roda da raiz: python tools/test_boots_slot.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, GEAR_SLOTS

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
    print("\n[1] GEAR_SLOTS inclui boots")
    check("9 slots ao todo", len(GEAR_SLOTS) == 9)
    check("boots está em GEAR_SLOTS", "boots" in GEAR_SLOTS)

    print("\n[2] make_player nasce com boots vazio")
    p = make_player("p1", "Richard", "paladin", 0)
    check("gear tem a chave boots", "boots" in p["gear"])
    check("boots começa vazio", p["gear"]["boots"] is None)

    print("\n[3] Equipar bota")
    r = setup("city")
    w = make_player("p1", "Richard", "paladin", 0); r.players["p1"] = w
    bota = {"id": "boots_leather", "name": "Botas de Couro", "emoji": "👢",
            "item_slot": "boots", "ac_bonus": 1}
    w["bag"] = [bota]
    await r.handle_equip_from_bag("p1", 0)
    check("equipou (gear.boots=boots_leather)", (w["gear"].get("boots") or {}).get("id") == "boots_leather")
    check("saiu da bolsa", len(w["bag"]) == 0)
    check("sem erro", len(r._errs) == 0)

    print("\n[4] Desequipar bota")
    await r.handle_unequip("p1", "boots")
    check("boots vazio após desequipar", w["gear"].get("boots") is None)
    check("item voltou p/ bolsa", any((it or {}).get("id") == "boots_leather" for it in w["bag"]))

    print("\n[5] Trocar bota equipada por outra")
    r = setup("city")
    w = make_player("p1", "Richard", "paladin", 0); r.players["p1"] = w
    bota1 = {"id": "boots_leather", "name": "Botas de Couro", "emoji": "👢", "item_slot": "boots", "ac_bonus": 1}
    bota2 = {"id": "boots_ferro", "name": "Botas de Ferro", "emoji": "👢", "item_slot": "boots", "ac_bonus": 2}
    w["gear"]["boots"] = bota1
    w["bag"] = [bota2]
    await r.handle_equip_from_bag("p1", 0)
    check("bota nova equipada", (w["gear"].get("boots") or {}).get("id") == "boots_ferro")
    check("bota antiga voltou p/ bolsa", any((it or {}).get("id") == "boots_leather" for it in w["bag"]))

    print("\n[6] Não-regressão: arma de 2 mãos x escudo continua bloqueando")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gear"]["off_hand"] = {"id": "shield1", "name": "Escudo", "kind": "shield", "item_slot": "off_hand"}
    arma2m = {"id": "espada2m", "name": "Espada de Duas Mãos", "die": "2d6",
              "item_slot": "weapon", "two_handed": True}
    w["bag"] = [arma2m]
    await r.handle_equip_from_bag("p1", 0)
    check("bloqueou (weapon não mudou)", (w["gear"].get("weapon") or {}).get("id") != "espada2m")
    check("erro de 2 mãos enviado", any("2 mãos" in e for e in r._errs))

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rode o teste e confirme que falha**

Run: `python tools/test_boots_slot.py`
Expected: FAIL nos checks `[1]`, `[2]`, `[3]` (o slot "boots" ainda não existe em `GEAR_SLOTS` nem em `make_player`, e `_slot_category_for_item` cairia no fallback `"bag"`, rejeitando o equip com "Este item é consumível").

- [ ] **Step 3: Adicione o slot em `GEAR_SLOTS`**

Em `server.py:3453`, troque:

```python
GEAR_SLOTS = ("weapon", "off_hand", "armor", "head", "ring1", "ring2", "item1", "item2")
```

por:

```python
GEAR_SLOTS = ("weapon", "off_hand", "armor", "head", "boots", "ring1", "ring2", "item1", "item2")
```

- [ ] **Step 4: Inicialize `gear["boots"]` em `make_player`**

Em `server.py`, dentro do dict `"gear": {...}` (por volta da linha 3531-3540), adicione a chave `"boots"` logo depois de `"head"`:

```python
        "gear": {
            "weapon":   starting_weapon_item,  # mão direita (arma principal)
            "off_hand": deepcopy(_STARTING_OFFHAND.get(cls_id)),  # mão esquerda: arma 2ª / escudo (dual-wield inicial)
            "armor":    starting_armor_item,   # corpo
            "head":     None,                  # elmo / tiara / capuz
            "boots":    None,                  # bota (sem itens no catálogo ainda)
            "ring1":    None,                  # anel
            "ring2":    None,                  # anel
            "item1":    None,                  # item ativo (mochila/luvas/cinto)
            "item2":    None,                  # item ativo
        },
```

- [ ] **Step 5: Ensine `_slot_category_for_item` a reconhecer bota**

Em `server.py`, dentro de `_slot_category_for_item` (por volta da linha 8201), logo depois do bloco `if s == "head" or ...`, adicione:

```python
        if s == "head" or k == "head" or any(w in nm for w in ("elmo", "capuz", "tiara", "capacete")):
            return "head"
        if s == "boots" or k == "boots" or any(w in nm for w in ("bota", "botas", "sapato")):
            return "boots"
```

- [ ] **Step 6: Adicione o branch de despacho em `_executar_equip_from_bag`**

Em `server.py`, dentro de `_executar_equip_from_bag` (por volta da linha 8325), troque:

```python
        elif cat == "armor":    log = self._equip_into_slot(p, item, "armor",    "🛡️")
        elif cat == "head":     log = self._equip_into_slot(p, item, "head",     "⛑️")
        elif cat == "ring":     log = self._equip_into_pair(p, item, ("ring1","ring2"), "💍")
        else:                   log = self._equip_into_pair(p, item, ("item1","item2"), "🎒")
```

por:

```python
        elif cat == "armor":    log = self._equip_into_slot(p, item, "armor",    "🛡️")
        elif cat == "head":     log = self._equip_into_slot(p, item, "head",     "⛑️")
        elif cat == "boots":    log = self._equip_into_slot(p, item, "boots",    "👢")
        elif cat == "ring":     log = self._equip_into_pair(p, item, ("ring1","ring2"), "💍")
        else:                   log = self._equip_into_pair(p, item, ("item1","item2"), "🎒")
```

- [ ] **Step 7: Rode o teste de novo e confirme que passa**

Run: `python tools/test_boots_slot.py`
Expected: `===== RESULTADO: N passaram, 0 falharam =====` e exit code 0.

- [ ] **Step 8: Rode a suíte de equipamento existente pra confirmar não-regressão**

Run: `python tools/test_ficha_cidade.py`
Expected: todos os checks passam (mesmo comportamento de antes — só adicionamos um slot novo, não mudamos nenhum existente).

- [ ] **Step 9: Commit**

```bash
git add server.py tools/test_boots_slot.py
git commit -m "feat(inventario): adiciona slot de equipamento Bota (infraestrutura)"
```

---

### Task 2: `gameState.js` — helpers puros e novos action-senders

**Files:**
- Modify: `src/gameState.js:1090-1091` (perto dos senders `equipFromBag`/`unequip`)
- Modify: `src/gameState.js` (novo bloco de funções puras, antes do `return { ... }` final)
- Modify: `src/gameState.js:1686-1688` (lista de exports)

Este projeto não tem framework de teste JS (nenhum `package.json`, nenhum `tools/test_*.js` — só `tools/test_*.py` testando `server.py`). `gameState.js` é DOM-free por regra do projeto (CLAUDE.md), mas não há harness pra rodá-lo isolado em Node. Verificação destas funções é manual, via console do navegador, na Task 9 (checklist final). TDD fica reservado pra Task 1 (Python, onde já existe convenção de teste).

- [ ] **Step 1: Adicione os dois novos action-senders**

Em `src/gameState.js`, logo depois da linha `function unequip(key) { send({ type: 'unequip', slot_key: key }); }` (linha 1091), adicione:

```js
  function reorderBag(fromIndex, toIndex) { send({ type: 'reorder_bag', from_index: fromIndex, to_index: toIndex }); }
  function equipOffhand(i)                { send({ type: 'equip_offhand',   slot_index: i }); }
```

- [ ] **Step 2: Adicione os helpers puros (categoria de slot, dagger, compatibilidade, comparação)**

Em `src/gameState.js`, ache o bloco de helpers internos (perto de onde `MATERIAIS_SOLIDOS`/`MATERIAIS_OPACOS` são declarados, topo do arquivo) e adicione, em qualquer ponto antes do `return { ... }` final:

```js
  // ── Inventário estilo Diablo — helpers puros (paperdoll/bolsa) ─────────────
  // Espelha server._slot_category_for_item (server.py) — client-side, só p/
  // feedback visual instantâneo. O servidor continua autoritativo: qualquer
  // rejeição real chega via mensagem `error`, o preview client-side é só uma
  // previsão.
  function _slotCategoryForItem(item){
    const s   = (item.item_slot || '').toLowerCase();
    const k   = (item.kind || '').toLowerCase();
    const iid = (item.id || '').toLowerCase();
    const nm  = (item.name || '').toLowerCase();
    if(s === 'weapon' || k === 'weapon') return 'weapon';
    if(s === 'shield' || s === 'off_hand' || k === 'shield' || iid.includes('shield') || nm.includes('escudo')) return 'off_hand';
    if(s === 'ammo' || item.effect === 'ammo') return 'off_hand';
    if(s === 'head' || k === 'head' || ['elmo','capuz','tiara','capacete'].some(w => nm.includes(w))) return 'head';
    if(s === 'boots' || k === 'boots' || ['bota','botas','sapato'].some(w => nm.includes(w))) return 'boots';
    if(s === 'ring' || k === 'ring' || nm.includes('anel')) return 'ring';
    if(['accessory','belt','gloves','backpack','item'].includes(s) ||
       ['accessory','belt','gloves','backpack'].includes(k) ||
       ['mochila','alforje','luva','cinto'].some(w => nm.includes(w))) return 'item';
    if(s === 'armor' || k === 'armor') return 'armor';
    if(item.die) return 'weapon';
    return 'bag';
  }

  // Adaga usável como 2ª arma (dual-wield) — mesma heurística já usada 2x em
  // game.js (_fcEhAdaga/ehAdaga), centralizada aqui p/ o modal novo não duplicar.
  function isDagger(item){
    if(!item) return false;
    const iid = (item.id || '').toLowerCase();
    const nm  = (item.name || '').toLowerCase();
    return (iid === 'dagger' || nm.includes('adaga')) && !!item.die;
  }

  // gearSnapshot = objeto gear atual (p/ checar conflito de arma de 2 mãos).
  function canPlaceItem(item, slotKey, gearSnapshot){
    if(!item || !slotKey) return false;
    const cat = _slotCategoryForItem(item);
    if(cat === 'bag') return false;   // consumível não equipa em slot nenhum
    const gear = gearSnapshot || {};
    if(slotKey === 'weapon'){
      if(cat !== 'weapon') return false;
      if(item.two_handed){
        const off = gear.off_hand;
        const offOcupaMao = !!off && (off.kind === 'shield' || off.item_slot === 'shield' || !!off.die);
        if(offOcupaMao) return false;
      }
      return true;
    }
    if(slotKey === 'off_hand'){
      const isOffhandCat = cat === 'off_hand';
      if(!isOffhandCat && !isDagger(item)) return false;
      const weapon = gear.weapon;
      if(weapon && weapon.two_handed) return false;
      return true;
    }
    if(slotKey === 'armor') return cat === 'armor';
    if(slotKey === 'head')  return cat === 'head';
    if(slotKey === 'boots') return cat === 'boots';
    if(slotKey === 'ring1' || slotKey === 'ring2') return cat === 'ring';
    if(slotKey === 'item1' || slotKey === 'item2') return cat === 'item';
    return false;
  }

  // Compara dois itens no formato de GS.CATALOGO_ITENS (bonusCA numérico,
  // dano em notação de dado tipo "1d8") pra tooltip com setas ↑/↓. Só compara
  // campos presentes em pelo menos um dos dois lados.
  function _diceAverage(diceStr){
    if(!diceStr) return null;
    const m = /^(\d+)d(\d+)$/.exec(String(diceStr).trim());
    if(!m) return null;
    const n = Number(m[1]), sides = Number(m[2]);
    return n * (sides + 1) / 2;
  }
  function compareItemStats(newItem, equippedItem){
    if(!newItem) return [];
    const fields = [
      { key: 'bonusCA', label: 'CA',   fmt: v => `+${v}` },
      { key: 'dano',    label: 'Dano', fmt: v => v, numeric: _diceAverage },
    ];
    const rows = [];
    for(const f of fields){
      const hasNew = newItem[f.key] != null;
      const hasOld = !!equippedItem && equippedItem[f.key] != null;
      if(!hasNew && !hasOld) continue;
      const newVal = hasNew ? (f.numeric ? f.numeric(newItem[f.key]) : newItem[f.key]) : null;
      const oldVal = hasOld ? (f.numeric ? f.numeric(equippedItem[f.key]) : equippedItem[f.key]) : null;
      let arrow = null;
      if(newVal != null && oldVal != null){
        if(newVal > oldVal) arrow = 'up';
        else if(newVal < oldVal) arrow = 'down';
      }
      rows.push({
        label: f.label,
        newDisplay: hasNew ? f.fmt(newItem[f.key]) : '—',
        oldDisplay: hasOld ? f.fmt(equippedItem[f.key]) : '—',
        arrow,
      });
    }
    return rows;
  }
```

- [ ] **Step 3: Exponha tudo na API pública de `GS`**

Em `src/gameState.js`, no bloco `return { ... }` final, logo depois de `unequip,` (perto da linha 1687), adicione:

```js
    equipFromBag,
    unequip,
    reorderBag,
    equipOffhand,
    canPlaceItem,
    compareItemStats,
    isDagger,
```

(troque a linha existente `equipFromBag,\n    unequip,` pela versão com as 5 linhas novas incluídas.)

- [ ] **Step 4: Verificação manual rápida no console do navegador**

Com o servidor rodando e uma partida aberta (`python server.py`, entre numa sala, escolha uma classe), abra o console do navegador (F12) e rode:

```js
GS.canPlaceItem({item_slot:'head'}, 'head', {})        // true
GS.canPlaceItem({item_slot:'head'}, 'boots', {})        // false
GS.canPlaceItem({id:'dagger', die:'1d4'}, 'off_hand', {weapon:{two_handed:false}})  // true
GS.canPlaceItem({item_slot:'weapon', two_handed:true}, 'weapon', {off_hand:{kind:'shield'}})  // false
GS.compareItemStats({bonusCA:3}, {bonusCA:1})           // [{label:'CA', arrow:'up', ...}]
```

Confirme que os retornos batem com os comentários acima antes de seguir.

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js
git commit -m "feat(inventario): helpers puros canPlaceItem/compareItemStats + reorderBag/equipOffhand"
```

---

### Task 3: `src/ui/inventoryModal.js` — esqueleto, CSS e abrir/fechar

**Files:**
- Create: `src/ui/inventoryModal.js`
- Modify: `index.html:23` (adiciona o script novo à cadeia de carregamento)

Este é o novo arquivo de renderização do modal — auto-contido, injeta seu próprio `<style>`, e só se comunica com o resto do jogo via `GS.*`. Ele é carregado DEPOIS de `game.js` de propósito: a Task 8 (tooltip) reaproveita funções globais que só existem depois de `game.js` rodar (`gerarConteudoTooltip`, `esconderTooltip`, `corBordaPorPreco`, `_initItemTooltip`).

- [ ] **Step 1: Crie o arquivo com o esqueleto do módulo + CSS injetado**

Crie `src/ui/inventoryModal.js`:

```js
'use strict';
// src/ui/inventoryModal.js — Legends for Hire
//
// Modal de Equipamento/Inventário estilo Diablo II/III. Renderer puro
// (DOM/CSS), ZERO lógica de jogo — lê GS.gameState/GS.cityState e chama
// GS.equipFromBag/GS.unequip/GS.reorderBag/GS.equipOffhand. Usado tanto na
// cidade quanto na masmorra (substitui os blocos de Equipamento+Inventário
// que existiam duplicados em renderMyPanel/renderFichaCidadeBody, em
// game.js). Ações/Habilidades/Encerrar Turno (masmorra) e Atributos/Guilda
// (cidade) continuam nos painéis antigos — este modal cuida só de
// paperdoll + bolsa + ouro.
//
// Carregado DEPOIS de game.js (ver index.html) — reaproveita funções
// globais de tooltip já existentes lá (gerarConteudoTooltip, corBordaPorPreco,
// esconderTooltip, _initItemTooltip) em vez de duplicá-las.

const InventoryModal = (() => {
  let _openPid  = null;   // pid cujo inventário está aberto (null = fechado)
  let _readOnly = false;
  let _selected = null;   // item selecionado (tap-to-select): {kind:'bag',index} | {kind:'gear',slotKey}

  // Layout do paperdoll (3×3): posição visual de cada um dos 9 slots.
  const GEAR_LAYOUT = [
    { key: 'item1',    small: true,  magic: true,  label: 'Item Mágico 1', empty: '📦' },
    { key: 'head',     small: false, magic: false, label: 'Elmo',          empty: '🪖' },
    { key: 'item2',    small: true,  magic: true,  label: 'Item Mágico 2', empty: '📦' },
    { key: 'weapon',   small: false, magic: false, label: 'Arma',         empty: '✊' },
    { key: 'armor',    small: false, magic: false, label: 'Armadura',     empty: '👕' },
    { key: 'off_hand', small: false, magic: false, label: 'Escudo',       empty: '🤚' },
    { key: 'ring1',    small: true,  magic: false, label: 'Anel 1',       empty: '💍' },
    { key: 'boots',    small: false, magic: false, label: 'Bota',         empty: '👢' },
    { key: 'ring2',    small: true,  magic: false, label: 'Anel 2',       empty: '💍' },
  ];

  const EDGE_D =
    'M0,.5 8,0 16,1 24,.25 32,.75 40,0 48,1 56,.4 64,.9 72,.15 80,1.1 88,.3 96,.7 100,0 ' +
    '100,8 99.5,16 100,24 99.25,32 100,40 99.5,48 100,56 99,64 100,72 99.6,80 100,88 99.25,96 100,100 ' +
    '92,99.5 84,99.25 76,100 68,99.5 60,100 52,99.4 44,100 36,99.65 28,100 20,99.35 12,100 4,100 0,100 ' +
    '.5,92 0,84 .75,76 0,68 .5,60 0,52 .6,44 0,36 .4,28 0,20 .75,12 0,4 0,0 Z';

  const CSS_TEXT = `
#inv-modal-overlay{position:fixed;inset:0;z-index:500;display:flex;align-items:center;justify-content:center;
  background:rgba(0,0,0,.55);opacity:0;pointer-events:none;transition:opacity .18s ease;}
#inv-modal-overlay.open{opacity:1;pointer-events:auto;}
.inv-frame{position:relative;width:460px;max-width:92vw;}
.inv-modal{position:relative;padding:26px 26px 26px;
  background:
    repeating-linear-gradient(115deg, rgba(255,255,255,.05) 0 1px, transparent 1px 34px),
    repeating-linear-gradient(25deg, rgba(0,0,0,.18) 0 1px, transparent 1px 46px),
    radial-gradient(circle at 25% 15%, rgba(255,255,255,.06) 0%, transparent 35%),
    radial-gradient(circle at 80% 80%, rgba(0,0,0,.3) 0%, transparent 50%),
    linear-gradient(160deg, #4a4d52, #2c2e32 55%, #202226 100%);
  backdrop-filter:blur(6px) saturate(105%);-webkit-backdrop-filter:blur(6px) saturate(105%);
  box-shadow:0 20px 60px rgba(0,0,0,.8);
  clip-path:polygon(
    0% .5%, 8% 0%, 16% 1%, 24% .25%, 32% .75%, 40% 0%, 48% 1%, 56% .4%, 64% .9%, 72% .15%, 80% 1.1%, 88% .3%, 96% .7%, 100% 0%,
    100% 8%, 99.5% 16%, 100% 24%, 99.25% 32%, 100% 40%, 99.5% 48%, 100% 56%, 99% 64%, 100% 72%, 99.6% 80%, 100% 88%, 99.25% 96%, 100% 100%,
    92% 99.5%, 84% 99.25%, 76% 100%, 68% 99.5%, 60% 100%, 52% 99.4%, 44% 100%, 36% 99.65%, 28% 100%, 20% 99.35%, 12% 100%, 4% 100%, 0% 100%,
    .5% 92%, 0% 84%, .75% 76%, 0% 68%, .5% 60%, 0% 52%, .6% 44%, 0% 36%, .4% 28%, 0% 20%, .75% 12%, 0% 4%, 0% 0%
  );}
.inv-edge{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:2;}
.inv-edge .glow{fill:none;stroke:#ff9d3d;stroke-width:3.2;opacity:.55;filter:blur(2.5px);vector-effect:non-scaling-stroke;}
.inv-edge .char{fill:none;stroke:#1a0f05;stroke-width:1.8;opacity:.9;vector-effect:non-scaling-stroke;}
.inv-edge .gold{fill:none;stroke:#f4d78a;stroke-width:1.15;vector-effect:non-scaling-stroke;filter:drop-shadow(0 0 3px rgba(244,215,138,.9));}
.inv-logo-wrap{position:absolute;top:-70px;left:50%;transform:translateX(-50%);z-index:3;width:300px;pointer-events:none;}
.inv-logo-wrap img{width:100%;height:auto;display:block;filter:drop-shadow(0 6px 10px rgba(0,0,0,.7));}
.inv-body{position:relative;z-index:2;}
.inv-header{display:flex;justify-content:space-between;align-items:center;margin:40px 0 16px;}
.inv-title{color:#f4ecd8;font-family:Georgia,serif;font-weight:bold;letter-spacing:1px;
  text-shadow:0 0 10px rgba(244,220,140,.4);font-size:.95rem;}
.inv-close{color:#e8cf7e;cursor:pointer;font-size:1.1rem;opacity:.8;}
.inv-close:hover{opacity:1;}
.inv-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;align-items:center;justify-items:center;
  margin:0 auto 20px;max-width:320px;}
.inv-slot{width:72px;height:96px;border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-size:1.8rem;cursor:pointer;background:linear-gradient(160deg,rgba(20,20,22,.55),rgba(6,6,8,.7));
  border:1px solid #d4b968;box-shadow:inset 0 2px 5px rgba(0,0,0,.7),0 1px 0 rgba(244,220,140,.16);}
.inv-slot.small{width:58px;height:77px;font-size:1.4rem;}
.inv-slot.magic{border-color:#c9a6ff;box-shadow:inset 0 2px 5px rgba(0,0,0,.7),0 0 12px #c9a6ff55;}
.inv-slot.empty{opacity:.55;}
.inv-slot.selected{outline:2px solid #ffe08a;outline-offset:2px;}
.inv-slot.drop-hover{outline:2px dashed #8fe08a;outline-offset:2px;}
.inv-slot.drop-invalid{outline:2px dashed #ff4136;outline-offset:2px;}
.inv-slot.blocked{opacity:.35;cursor:not-allowed;
  background:repeating-linear-gradient(45deg, rgba(255,65,54,.12) 0 6px, transparent 6px 12px);}
.inv-slot-blocked-x{color:#ff4136;font-size:1.6rem;}
.inv-slot-empty-icon{opacity:.35;}
.inv-slot-emoji img,.inv-bagslot-emoji img{width:70%;height:70%;object-fit:contain;display:block;}
.inv-gold{display:flex;align-items:center;justify-content:center;gap:6px;color:#ffcf7a;font-weight:bold;
  text-shadow:0 0 8px rgba(255,180,60,.6);font-family:Georgia,serif;margin-bottom:14px;}
.inv-bagbar{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;
  border-top:1px solid rgba(244,220,140,.3);padding-top:14px;}
.inv-bagslot{width:42px;height:42px;border-radius:6px;background:rgba(6,6,8,.55);
  border:1px solid rgba(244,220,140,.35);display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;cursor:pointer;}
.inv-bagslot.selected{outline:2px solid #ffe08a;outline-offset:2px;}
.inv-bagslot.drop-hover{outline:2px dashed #8fe08a;outline-offset:2px;}
`;

  // Ícone do item: usa item.icon (caminho de PNG) se presente; senão cai no
  // emoji (item.emoji ou o placeholder do slot). Nenhum item usa `icon` hoje
  // — este é só o ponto de extensão pra quando a arte existir (fora de escopo
  // aqui, ver spec).
  function _itemIconHTML(item, fallbackEmoji){
    if(item && item.icon) return `<img src="${item.icon}" alt="">`;
    return (item && item.emoji) || fallbackEmoji || '';
  }

  function _injectStyles(){
    if(document.getElementById('inventory-modal-styles')) return;
    const style = document.createElement('style');
    style.id = 'inventory-modal-styles';
    style.textContent = CSS_TEXT;
    document.head.appendChild(style);
  }

  function _ensureDom(){
    if(document.getElementById('inv-modal-overlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'inv-modal-overlay';
    overlay.addEventListener('click', (e) => { if(e.target === overlay) close(); });
    document.body.appendChild(overlay);
  }

  function open(pid, opts){
    opts = opts || {};
    _openPid  = pid;
    _readOnly = !!opts.readOnly;
    _selected = null;
    _injectStyles();
    _ensureDom();
    _render();
    requestAnimationFrame(() => {
      const overlay = document.getElementById('inv-modal-overlay');
      if(overlay) overlay.classList.add('open');
    });
  }

  function close(){
    _openPid  = null;
    _selected = null;
    const overlay = document.getElementById('inv-modal-overlay');
    if(overlay) overlay.classList.remove('open');
  }

  function toggle(pid, opts){
    if(_openPid != null) close(); else open(pid, opts);
  }

  function isOpen(){ return _openPid != null; }

  function refresh(){
    if(_openPid != null) _render();
  }

  function _currentPlayer(){
    if(_openPid == null) return null;
    const gs = (typeof GS !== 'undefined') ? GS.gameState : null;
    if(gs && gs.players){
      const p = gs.players.find(pl => pl.id === _openPid);
      if(p) return p;
    }
    const cs = (typeof GS !== 'undefined') ? GS.cityState : null;
    if(cs && cs.players) return cs.players.find(pl => pl.id === _openPid) || null;
    return null;
  }

  function _render(){
    const overlay = document.getElementById('inv-modal-overlay');
    if(!overlay) return;
    const player = _currentPlayer();
    if(!player){ close(); return; }
    overlay.innerHTML = `
      <div class="inv-frame">
        <div class="inv-modal">
          <svg class="inv-edge" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path class="glow" d="${EDGE_D}"/>
            <path class="char" d="${EDGE_D}"/>
            <path class="gold" d="${EDGE_D}"/>
          </svg>
          <div class="inv-body">
            <div class="inv-header">
              <div class="inv-title">⚔️ INVENTÁRIO — ${player.name || ''}${_readOnly ? ' (somente leitura)' : ''}</div>
              <div class="inv-close" title="Fechar">✕</div>
            </div>
            <div class="inv-grid"></div>
            <div class="inv-gold">🪙 <span></span></div>
            <div class="inv-bagbar"></div>
          </div>
        </div>
        <div class="inv-logo-wrap"><img src="assets/logotipo.png" alt="Legends for Hire"></div>
      </div>`;
    overlay.querySelector('.inv-close').onclick = close;
    overlay.querySelector('.inv-gold span').textContent = player.gold ?? 0;
    // _renderGear/_renderBag chegam nas próximas tasks.
  }

  return { open, close, toggle, isOpen, refresh };
})();
```

- [ ] **Step 2: Registre o script em `index.html`**

Em `index.html:23`, troque:

```html
<script>(function(){var v=Date.now();document.write('<script src="src/gameState.js?v='+v+'"><\/script>');document.write('<script src="src/main.js?v='+v+'"><\/script>');document.write('<script src="src/miniatura3d.js?v='+v+'"><\/script>');document.write('<script src="game.js?v='+v+'"><\/script>');})();</script>
```

por:

```html
<script>(function(){var v=Date.now();document.write('<script src="src/gameState.js?v='+v+'"><\/script>');document.write('<script src="src/main.js?v='+v+'"><\/script>');document.write('<script src="src/miniatura3d.js?v='+v+'"><\/script>');document.write('<script src="game.js?v='+v+'"><\/script>');document.write('<script src="src/ui/inventoryModal.js?v='+v+'"><\/script>');})();</script>
```

- [ ] **Step 3: Verificação manual — abrir/fechar o modal vazio**

Com `python server.py` rodando, abra o jogo no navegador, entre numa partida até a cidade. Abra o console (F12) e rode:

```js
InventoryModal.open(GS.myPid)
```

Expected: um overlay escuro cobre a tela com um painel de mármore cinza, borda dourada rasgada, logotipo saindo do topo, título "⚔️ INVENTÁRIO — <seu nome>", botão "✕", e o contador de ouro (grid e bolsa ainda vazios — chegam nas próximas tasks). Rode `InventoryModal.close()` e confirme que o overlay some. Rode `InventoryModal.open(GS.myPid)` de novo e clique fora do painel (na área escura) — confirme que fecha sozinho.

- [ ] **Step 4: Commit**

```bash
git add src/ui/inventoryModal.js index.html
git commit -m "feat(inventario): esqueleto do modal (CSS, abrir/fechar, overlay)"
```

---

### Task 4: Paperdoll — renderizar os 9 slots de equipamento

**Files:**
- Modify: `src/ui/inventoryModal.js`

- [ ] **Step 1: Adicione `_renderGear` e ligue no `_render`**

Em `src/ui/inventoryModal.js`, adicione esta função (antes do `return { ... }` final):

```js
  function _renderGear(overlay, player){
    const grid = overlay.querySelector('.inv-grid');
    grid.innerHTML = '';
    const gear = player.gear || {};
    const twoHanded = !!(gear.weapon && gear.weapon.two_handed);
    for(const cfg of GEAR_LAYOUT){
      const item = gear[cfg.key];
      const blocked = cfg.key === 'off_hand' && twoHanded && !item;
      const slot = document.createElement('div');
      slot.className = 'inv-slot'
        + (cfg.small ? ' small' : '')
        + (cfg.magic ? ' magic' : '')
        + (item ? ' filled' : ' empty')
        + (blocked ? ' blocked' : '');
      slot.dataset.slotKey = cfg.key;
      slot.title = blocked ? 'Bloqueado — arma de duas mãos equipada'
                 : item ? item.name : cfg.label;
      slot.innerHTML = blocked
        ? `<span class="inv-slot-blocked-x">✕</span>`
        : item ? `<span class="inv-slot-emoji">${_itemIconHTML(item, cfg.empty)}</span>`
               : `<span class="inv-slot-emoji inv-slot-empty-icon">${cfg.empty}</span>`;
      grid.appendChild(slot);
    }
  }
```

- [ ] **Step 2: Chame `_renderGear` dentro de `_render`**

Em `_render`, troque o comentário `// _renderGear/_renderBag chegam nas próximas tasks.` por:

```js
    _renderGear(overlay, player);
```

- [ ] **Step 3: Verificação manual**

Recarregue a página (`Ctrl+F5`), na cidade equipe uma arma/armadura pela ficha antiga (ainda funcional nesta task) e rode `InventoryModal.open(GS.myPid)` no console. Confirme:
- Os 9 slots aparecem no layout: linha 1 = item mágico / elmo / item mágico; linha 2 = arma / armadura / escudo; linha 3 = anel / bota / anel.
- Os slots `item1`, `item2`, `ring1`, `ring2` são visivelmente menores (80% dos outros).
- O slot de arma equipada mostra o emoji do item; os vazios mostram o emoji "fantasma" (opacidade baixa).

- [ ] **Step 4: Verificação manual — bloqueio visual de arma de duas mãos**

Equipe uma arma com `two_handed: true` (ex.: espada de duas mãos, disponível na loja da cidade) pela ficha antiga. Abra o modal de novo. Confirme que o slot `off_hand` aparece com um `✕` vermelho sobre um padrão hachurado, em vez do emoji de mão vazia.

- [ ] **Step 5: Commit**

```bash
git add src/ui/inventoryModal.js
git commit -m "feat(inventario): renderiza paperdoll (9 slots, proporção 3:4, bloqueio 2H)"
```

---

### Task 5: Bolsa e ouro

**Files:**
- Modify: `src/ui/inventoryModal.js`

- [ ] **Step 1: Adicione `_renderBag` e ligue no `_render`**

```js
  function _renderBag(overlay, player){
    const bar = overlay.querySelector('.inv-bagbar');
    bar.innerHTML = '';
    const bag = player.bag || [];
    const bagSize = player.bag_size || 6;
    for(let i = 0; i < bagSize; i++){
      const item = bag[i];
      const slot = document.createElement('div');
      slot.className = 'inv-bagslot' + (item ? ' filled' : ' empty');
      slot.dataset.bagIndex = String(i);
      slot.title = item ? item.name : 'Vazio';
      slot.innerHTML = item ? `<span class="inv-bagslot-emoji">${_itemIconHTML(item, '📦')}</span>` : '';
      bar.appendChild(slot);
    }
  }
```

Em `_render`, logo depois de `_renderGear(overlay, player);`, adicione:

```js
    _renderBag(overlay, player);
```

- [ ] **Step 2: Verificação manual**

Com itens na bolsa (compre algo na loja da cidade), abra o modal. Confirme que a grade de baixo mostra `bag_size` slots (padrão 6), preenchidos com o emoji dos itens que estão na bolsa e vazios pros demais. Confirme que o número de ouro no meio bate com o que aparece na barra de heróis da cidade.

- [ ] **Step 3: Verificação manual — bolsa expansível**

Equipe um item com efeito `bagslots` (ex.: "Mochila de Couro", item da loja) num dos slots `item1`/`item2`. Abra o modal de novo — confirme que a grade da bolsa cresceu (mais de 6 slots).

- [ ] **Step 4: Commit**

```bash
git add src/ui/inventoryModal.js
git commit -m "feat(inventario): renderiza bolsa expansivel e ouro"
```

---

### Task 6: Interação — clique-clique (equipar/desequipar/reordenar)

**Files:**
- Modify: `src/ui/inventoryModal.js`

- [ ] **Step 1: Adicione o estado de seleção visual em `_renderGear`/`_renderBag`**

Em `_renderGear`, dentro do loop `for(const cfg of GEAR_LAYOUT)`, logo antes de `grid.appendChild(slot);`, adicione:

```js
      if(_selected && _selected.kind === 'gear' && _selected.slotKey === cfg.key) slot.classList.add('selected');
```

Em `_renderBag`, dentro do loop `for(let i = 0; ...)`, logo antes de `bar.appendChild(slot);`, adicione:

```js
      if(_selected && _selected.kind === 'bag' && _selected.index === i) slot.classList.add('selected');
```

- [ ] **Step 2: Adicione os handlers de clique e as funções de movimento**

Adicione estas funções (antes do `return { ... }` final):

```js
  function _onGearSlotClick(slotKey, blocked){
    if(_readOnly || blocked) return;
    if(_selected == null){
      const player = _currentPlayer();
      if(player && player.gear && player.gear[slotKey]) _selected = { kind: 'gear', slotKey };
      refresh();
      return;
    }
    if(_selected.kind === 'gear' && _selected.slotKey === slotKey){ _selected = null; refresh(); return; }
    _attemptMoveToGear(slotKey);
  }

  function _onBagSlotClick(index){
    if(_readOnly) return;
    if(_selected == null){
      const player = _currentPlayer();
      if(player && player.bag && player.bag[index]) _selected = { kind: 'bag', index };
      refresh();
      return;
    }
    if(_selected.kind === 'bag' && _selected.index === index){ _selected = null; refresh(); return; }
    _attemptMoveToBag(index);
  }

  function _attemptMoveToGear(slotKey){
    const sel = _selected; _selected = null;
    if(!sel || sel.kind === 'gear'){ refresh(); return; }   // gear→gear: sem suporte, ignora
    const player = _currentPlayer();
    const item = player && player.bag ? player.bag[sel.index] : null;
    if(!item || !GS.canPlaceItem(item, slotKey, player.gear || {})){ refresh(); return; }
    const ehOffhand = slotKey === 'off_hand' && GS.isDagger(item);
    if(ehOffhand) GS.equipOffhand(sel.index);
    else          GS.equipFromBag(sel.index);
  }

  function _attemptMoveToBag(toIndex){
    const sel = _selected; _selected = null;
    if(!sel){ refresh(); return; }
    if(sel.kind === 'bag'){
      if(sel.index !== toIndex) GS.reorderBag(sel.index, toIndex);
      else refresh();
      return;
    }
    GS.unequip(sel.slotKey);   // sel.kind === 'gear'
  }
```

- [ ] **Step 3: Ligue os handlers de clique nos slots renderizados**

Em `_renderGear`, dentro do loop, logo depois de montar `slot.innerHTML = ...`, adicione:

```js
      if(!_readOnly) slot.onclick = () => _onGearSlotClick(cfg.key, blocked);
```

Em `_renderBag`, dentro do loop, logo depois de montar `slot.innerHTML = ...`, adicione:

```js
      if(!_readOnly) slot.onclick = () => _onBagSlotClick(i);
```

- [ ] **Step 4: Verificação manual — equipar por clique-clique**

Abra o modal (`InventoryModal.open(GS.myPid)`), clique num item da bolsa (deve ganhar um contorno dourado — "selecionado"), depois clique num slot de equipamento compatível. Confirme que o item se move da bolsa pro paperdoll e o servidor confirma (o painel se atualiza sozinho — se ainda não atualizar automaticamente, rode `InventoryModal.refresh()` manualmente por enquanto; a atualização automática entra na Task 9).

- [ ] **Step 5: Verificação manual — desequipar e reordenar**

Clique num item equipado (seleciona), depois clique num slot vazio da bolsa — confirme que desequipa. Clique num item da bolsa, depois em OUTRO slot da bolsa (com ou sem item) — confirme que reordena.

- [ ] **Step 6: Verificação manual — clicar de novo no mesmo item cancela a seleção**

Clique num item pra selecionar, clique nele de novo — confirme que o contorno dourado some (seleção cancelada) sem mover nada.

- [ ] **Step 7: Commit**

```bash
git add src/ui/inventoryModal.js
git commit -m "feat(inventario): interacao clique-clique (equipar/desequipar/reordenar)"
```

---

### Task 7: Interação — drag nativo (bônus de mouse) + feedback de slot inválido

**Files:**
- Modify: `src/ui/inventoryModal.js`

- [ ] **Step 1: Adicione `_updateDropFeedback` e ligue `draggable` + eventos de drag nos slots de equipamento**

Adicione a função (antes do `return { ... }` final):

```js
  function _updateDropFeedback(slot, slotKey){
    const player = _currentPlayer();
    if(!player || !_selected || _selected.kind !== 'bag'){ slot.classList.add('drop-invalid'); return; }
    const item = (player.bag || [])[_selected.index];
    const ok = !!item && GS.canPlaceItem(item, slotKey, player.gear || {});
    slot.classList.toggle('drop-invalid', !ok);
  }
```

Em `_renderGear`, dentro do loop, depois de ligar `slot.onclick`, adicione:

```js
      if(!_readOnly && !blocked){
        if(item){
          slot.draggable = true;
          slot.addEventListener('dragstart', () => { _selected = { kind: 'gear', slotKey: cfg.key }; });
        }
        slot.addEventListener('dragover', (e) => {
          if(!_selected) return;
          e.preventDefault();
          slot.classList.add('drop-hover');
          _updateDropFeedback(slot, cfg.key);
        });
        slot.addEventListener('dragleave', () => slot.classList.remove('drop-hover', 'drop-invalid'));
        slot.addEventListener('drop', (e) => {
          e.preventDefault();
          slot.classList.remove('drop-hover', 'drop-invalid');
          _attemptMoveToGear(cfg.key);
        });
      }
```

- [ ] **Step 2: Ligue `draggable` + eventos de drag nos slots da bolsa**

Em `_renderBag`, dentro do loop, depois de ligar `slot.onclick`, adicione:

```js
      if(!_readOnly){
        if(item){
          slot.draggable = true;
          slot.addEventListener('dragstart', () => { _selected = { kind: 'bag', index: i }; });
        }
        slot.addEventListener('dragover', (e) => { if(_selected){ e.preventDefault(); slot.classList.add('drop-hover'); } });
        slot.addEventListener('dragleave', () => slot.classList.remove('drop-hover'));
        slot.addEventListener('drop', (e) => {
          e.preventDefault();
          slot.classList.remove('drop-hover');
          _attemptMoveToBag(i);
        });
      }
```

- [ ] **Step 3: Verificação manual — arrastar com o mouse**

No desktop, abra o modal, arraste um item da bolsa até um slot de equipamento compatível — confirme que equipa (mesmo resultado do clique-clique, via drag nativo). Arraste um item sobre um slot INCOMPATÍVEL (ex.: uma poção sobre o slot de bota) — confirme que o slot pisca vermelho tracejado (`drop-invalid`) durante o arraste, e que soltar ali não faz nada.

- [ ] **Step 4: Verificação manual — touch não quebra**

Num dispositivo touch (ou emulação de touch do DevTools), confirme que tocar nos itens continua funcionando via clique-clique (o atributo `draggable` é ignorado por navegadores touch, então não deve haver conflito).

- [ ] **Step 5: Commit**

```bash
git add src/ui/inventoryModal.js
git commit -m "feat(inventario): drag nativo (mouse) + feedback visual de slot invalido"
```

---

### Task 8: Tooltip com comparação de atributos

**Files:**
- Modify: `src/ui/inventoryModal.js`

- [ ] **Step 1: Adicione `_equippedCounterpart`, `_showInventoryTooltip` e `_wireTooltip`**

```js
  // Acha, entre os 9 slots do paperdoll, qual (se algum) aceitaria este item
  // — usado pra saber contra qual item equipado comparar no tooltip.
  function _equippedCounterpart(player, bagItem){
    const gear = player.gear || {};
    for(const cfg of GEAR_LAYOUT){
      if(gear[cfg.key] && GS.canPlaceItem(bagItem, cfg.key, gear)) return gear[cfg.key];
    }
    return null;
  }

  function _showInventoryTooltip(itemId, comparisonItemId, touchPos){
    if(typeof GS === 'undefined' || !GS.CATALOGO_ITENS) return;
    const item = GS.CATALOGO_ITENS[itemId];
    if(!item || typeof _initItemTooltip !== 'function' || typeof gerarConteudoTooltip !== 'function') return;
    _initItemTooltip();
    const t = document.getElementById('item-tooltip');
    if(!t) return;
    let html = gerarConteudoTooltip(item);
    const equipped = comparisonItemId ? GS.CATALOGO_ITENS[comparisonItemId] : null;
    if(equipped){
      const rows = GS.compareItemStats(item, equipped);
      if(rows.length){
        html += `<div style="padding:8px 14px;border-top:1px solid #c8a95133;">
          <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:6px;">COMPARADO AO EQUIPADO</div>
          ${rows.map(r => `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
              <span style="color:#8a7a5a;font-size:10px;">${r.label}</span>
              <span style="font-size:10px;">
                <span style="color:#666;">${r.oldDisplay}</span> →
                <span style="color:#c8b89a;">${r.newDisplay}</span>
                ${r.arrow === 'up'   ? ' <span style="color:#2ecc40;">▲</span>' : ''}
                ${r.arrow === 'down' ? ' <span style="color:#ff4136;">▼</span>' : ''}
              </span>
            </div>`).join('')}
        </div>`;
      }
    }
    t.innerHTML = html;
    t.style.borderColor = (typeof corBordaPorPreco === 'function') ? corBordaPorPreco(item.preco) : '#c8a951';
    t.style.opacity = '1';
    if(touchPos){
      const margin = 16;
      const rect = t.getBoundingClientRect();
      let x = touchPos.x + margin;
      if(x + rect.width > window.innerWidth) x = touchPos.x - rect.width - margin;
      let y = touchPos.y - rect.height - margin;   // acima do dedo, não cobre o item tocado
      if(y < 0) y = touchPos.y + margin;
      t.style.left = x + 'px';
      t.style.top  = y + 'px';
    }
  }

  function _wireTooltip(el, itemId, comparisonItemId){
    if(!itemId) return;
    let pressTimer = null;
    el.addEventListener('mouseenter', () => _showInventoryTooltip(itemId, comparisonItemId));
    el.addEventListener('mouseleave', () => { if(typeof esconderTooltip === 'function') esconderTooltip(); });
    el.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      pressTimer = setTimeout(() => _showInventoryTooltip(itemId, comparisonItemId, { x: touch.clientX, y: touch.clientY }), 350);
    }, { passive: true });
    el.addEventListener('touchmove', () => clearTimeout(pressTimer), { passive: true });
    el.addEventListener('touchend', () => {
      clearTimeout(pressTimer);
      if(typeof esconderTooltip === 'function') esconderTooltip();
    });
  }
```

- [ ] **Step 2: Ligue o tooltip nos slots de equipamento (sem comparação — já é o item equipado)**

Em `_renderGear`, dentro do loop, logo depois de `slot.innerHTML = ...`, adicione:

```js
      if(item && !blocked) _wireTooltip(slot, item.id, null);
```

- [ ] **Step 3: Ligue o tooltip nos slots da bolsa (com comparação contra o equipado no mesmo slot)**

Em `_renderBag`, dentro do loop, logo depois de `slot.innerHTML = ...`, adicione:

```js
      if(item){
        const equipped = _equippedCounterpart(player, item);
        _wireTooltip(slot, item.id, equipped ? equipped.id : null);
      }
```

(isso exige que `_renderBag` receba `player` — já recebe, é o 2º parâmetro da função definida na Task 5.)

- [ ] **Step 4: Verificação manual — tooltip simples**

Passe o mouse sobre um item equipado no paperdoll. Confirme que o tooltip já existente do jogo (`#item-tooltip`) aparece com as informações do item.

- [ ] **Step 5: Verificação manual — tooltip com comparação**

Tenha um item equipado num slot (ex.: um anel) e um item DIFERENTE do mesmo tipo na bolsa. Passe o mouse sobre o item da bolsa. Confirme que o tooltip mostra uma seção extra "COMPARADO AO EQUIPADO" com os valores lado a lado e uma seta ▲ (verde) ou ▼ (vermelha) nos atributos que mudam. Repita com um item que representa PIORA (ex.: CA menor) e confirme a seta vermelha.

- [ ] **Step 6: Verificação manual — touch (segurar)**

Em modo touch (emulação do DevTools), segure o dedo sobre um item por mais de 350ms — confirme que o tooltip aparece acima do ponto tocado. Solte — confirme que some.

- [ ] **Step 7: Commit**

```bash
git add src/ui/inventoryModal.js
git commit -m "feat(inventario): tooltip com comparacao de atributos (setas up/down)"
```

---

### Task 9: `game.js` — remove os blocos antigos, liga os gatilhos de abertura

**Files:**
- Modify: `game.js:10074-10223` (dentro de `renderMyPanel`)
- Modify: `game.js:10836-10932` (dentro de `renderFichaCidadeBody`)
- Modify: `game.js:184` (template do HTML — `#ficha-fab` + novo `#actions-fab`)
- Modify: `game.js` (novo listener de teclado pra tecla `I`)
- Modify: `game.js:3165-3178` (`handleGameState`) e `game.js:20133-20154` (callback `GS.on('cityState', ...)`)
- Modify: `game.css` (reposiciona `#ficha-fab`, novo `#actions-fab`)

O `#ficha-fab` (🎒) hoje abre a GAVETA INTEIRA da masmorra no celular (Ações + Habilidades + Equipamento + Encerrar Turno). Repurpose-lo só pro inventário faria o celular perder o único jeito de abrir Ações/Habilidades — por isso este task ADICIONA um botão novo (`#actions-fab`) que assume esse papel, preservando o comportamento atual, enquanto `#ficha-fab` vira o botão do inventário (agora visível sempre, não só no celular).

- [ ] **Step 1: Remova o bloco de Equipamento+Bolsa de `renderMyPanel`**

Em `game.js`, dentro de `renderMyPanel`, ache o comentário `// ── Inventory ──` (por volta da linha 10074). A partir dali, até a linha `inv.appendChild(bagGrid);` (inclusive — por volta da linha 10223), há um bloco de ~150 linhas que constrói `EQ_SLOTS`, `eqGrid` e `bagGrid` na mão. Confirme os limites antes de apagar:

- **Primeira linha do bloco** (mantenha esta, é só as duas seguintes que somem primeiro): `  // ── Inventory ──`
- **Linha seguinte a manter**: `  const inv = $('inventory-list'); inv.innerHTML = '';`
- **Última linha do bloco a apagar**: `  inv.appendChild(bagGrid);`
- **Linha imediatamente DEPOIS do bloco (não mexer nela)**: `  // ── Itens comprados na loja (modelo client-side GS.getHeroiAtivo) ──`

Apague tudo a partir de `const gear = me.gear || {};` (linha logo após `inv.innerHTML = '';`) até `inv.appendChild(bagGrid);` (inclusive). O resultado final deve ficar assim:

```js
  // ── Inventory: Equipamento+Bolsa agora vivem no InventoryModal (tecla I /
  // ícone de canto) — ver src/ui/inventoryModal.js. Este bloco cuida só do
  // que sobrou aqui: itens comprados na loja (legado) + ouro + fim de turno.
  const inv = $('inventory-list'); inv.innerHTML = '';

  // ── Itens comprados na loja (modelo client-side GS.getHeroiAtivo) ──────────
  renderPurchasedItems(inv, canAct);
```

(As duas últimas linhas acima — o comentário e `renderPurchasedItems(inv, canAct);` — já existiam logo depois do bloco removido; não recrie, só confirme que ficaram encostadas na nova versão de `const inv = ...`.)

Confira com `grep -n "EQ_SLOTS\|eqGrid\|bagGrid" game.js` — nenhuma ocorrência deve sobrar dentro de `renderMyPanel` (a busca ainda vai achar `FC_EQ_SLOTS`/`eqGrid`/`bagGrid` dentro de `renderFichaCidadeBody`, removidos no próximo Step).

- [ ] **Step 2: Remova o bloco de Equipamento+Bolsa de `renderFichaCidadeBody`**

Em `game.js`, dentro de `renderFichaCidadeBody`, ache o comentário `  // Equipamento (paper-doll dos 8 slots)` (por volta da linha 10835). A partir dali até a linha `  body.appendChild(bagGrid);` (inclusive — por volta da linha 10932), apague o bloco inteiro:

- **Primeira linha a apagar**: `  // Equipamento (paper-doll dos 8 slots)`
- **Última linha a apagar**: `  body.appendChild(bagGrid);`
- **Linha imediatamente ANTES do bloco (não mexer)**: `  body.appendChild(attr);` (fim da seção de Atributos)
- **Linha imediatamente DEPOIS do bloco (não mexer)**: `  // ── Técnica da Guilda (Fase 0) — equipar no 4º slot (só o próprio herói, na cidade) ──`

No lugar do bloco apagado, adicione um botão pra abrir o inventário deste jogador (funciona pro próprio jogador e, em somente-leitura, pra colegas):

```js
  // Botão pra abrir o inventário (equipamento+bolsa) deste jogador — o
  // InventoryModal cuida disso agora; este painel só mostra atributos+guilda.
  const invBtn = document.createElement('button');
  invBtn.className = 'section-title';
  invBtn.style.cssText = 'width:100%;text-align:left;cursor:pointer;background:none;border:none;color:var(--gold);';
  invBtn.textContent = '🎒 Ver inventário';
  invBtn.onclick = () => InventoryModal.open(player.id, { readOnly: !editable });
  body.appendChild(invBtn);
```

O resultado final deve ficar: `... body.appendChild(attr);` seguido do bloco `invBtn` acima, seguido de `// ── Técnica da Guilda (Fase 0) ...`.

Adicione, no lugar, um botão pra abrir o inventário deste jogador (funciona pro próprio jogador e, em somente-leitura, pra colegas):

```js
  // Botão pra abrir o inventário (equipamento+bolsa) deste jogador — o
  // InventoryModal cuida disso agora; este painel só mostra atributos+guilda.
  const invBtn = document.createElement('button');
  invBtn.className = 'section-title';
  invBtn.style.cssText = 'width:100%;text-align:left;cursor:pointer;background:none;border:none;color:var(--gold);';
  invBtn.textContent = '🎒 Ver inventário';
  invBtn.onclick = () => InventoryModal.open(player.id, { readOnly: !editable });
  body.appendChild(invBtn);
```

- [ ] **Step 3: Verifique que `FC_EQ_SLOTS` e as funções de drag antigas (`_fcDropOnGear`/`_fcDropOnBag`) ficaram órfãs**

Rode:

```bash
grep -n "FC_EQ_SLOTS\|_fcDropOnGear\|_fcDropOnBag\|_fcDrag" game.js
```

Expected: `FC_EQ_SLOTS` só aparece na própria declaração (não é mais usada) — apague a declaração (linhas 10742-10751, o array `const FC_EQ_SLOTS = [...]`). `_fcDropOnGear`/`_fcDropOnBag`/`_fcDrag` também ficam sem uso — apague as duas funções (linhas ~10980-11003) e a declaração `let _fcDrag = null;` (linha 10753). Mantenha `_fcEhAdaga` só se algo mais além do bloco removido ainda a usa (rode `grep -n "_fcEhAdaga" game.js` pra conferir — se só aparecer na própria declaração, apague-a também).

- [ ] **Step 4: Adicione o botão `#actions-fab` no template HTML e repurpose `#ficha-fab`**

Em `game.js`, ache o trecho (por volta da linha 182-184):

```js
  <!-- Celular: fundo escuro + botão flutuante que abrem/fecham a ficha (gaveta) -->
  <div id="ficha-backdrop" onclick="toggleFichaDrawer(false)"></div>
  <button id="ficha-fab" onclick="toggleFichaDrawer(true)" title="Ficha do personagem">🎒</button>
```

Troque por:

```js
  <!-- Celular: fundo escuro + botão flutuante que abre/fecha Ações/Habilidades (gaveta) -->
  <div id="ficha-backdrop" onclick="toggleFichaDrawer(false)"></div>
  <button id="actions-fab" onclick="toggleFichaDrawer(true)" title="Ações e habilidades">⚔️</button>
  <!-- Ícone de abrir o Inventário — sempre visível (cidade+masmorra, desktop+mobile) -->
  <button id="ficha-fab" onclick="InventoryModal.toggle(GS.myPid)" title="Inventário (tecla I)">🎒</button>
```

- [ ] **Step 5: Ajuste o CSS — `#ficha-fab` sempre visível, `#actions-fab` só no celular**

Em `game.css:796`, troque:

```css
#ficha-fab, #ficha-backdrop, #ficha-close-btn { display: none; }
```

por:

```css
#actions-fab, #ficha-backdrop, #ficha-close-btn { display: none; }
#ficha-fab {
  display: flex; position: fixed; right: 14px; bottom: 16px; z-index: 340;
  width: 56px; height: 56px; border-radius: 50%;
  align-items: center; justify-content: center; font-size: 24px;
  background: var(--gold); color: #000; border: none; cursor: pointer;
  box-shadow: 0 4px 14px rgba(0,0,0,.55);
}
```

Em `game.css:824-832` (bloco dentro de `@media (max-width: 820px)`), troque:

```css
  /* Botão flutuante (abre a ficha) + botão de fechar + fundo escuro */
  #ficha-fab {
    display: flex; position: fixed; right: 14px; bottom: 16px; z-index: 300;
    width: 56px; height: 56px; border-radius: 50%;
    align-items: center; justify-content: center; font-size: 24px;
    background: var(--gold); color: #000; border: none;
    box-shadow: 0 4px 14px rgba(0,0,0,.55);
  }
  body.drawer-open #ficha-fab { display: none; }
```

por:

```css
  /* Botão flutuante (abre Ações/Habilidades) + botão de fechar + fundo escuro */
  #actions-fab {
    display: flex; position: fixed; right: 82px; bottom: 16px; z-index: 300;
    width: 56px; height: 56px; border-radius: 50%;
    align-items: center; justify-content: center; font-size: 22px;
    background: var(--bg3); color: var(--gold); border: 1px solid var(--gold);
    box-shadow: 0 4px 14px rgba(0,0,0,.55);
  }
  body.drawer-open #actions-fab { display: none; }
```

- [ ] **Step 6: Adicione o atalho de teclado "I"**

Em `game.js`, ache o listener de `Escape` mais próximo do fim do arquivo (procure `document.addEventListener('keydown'` — há vários; use qualquer um já existente perto do final como referência de local) e adicione um novo listener global, próximo de onde `GS.on('gameState', ...)` é registrado (por volta da linha 20176):

```js
document.addEventListener('keydown', (e) => {
  if(e.key !== 'i' && e.key !== 'I') return;
  const tag = (document.activeElement && document.activeElement.tagName) || '';
  if(tag === 'INPUT' || tag === 'TEXTAREA') return;   // não interfere em campos de texto
  if(!GS.myPid) return;
  InventoryModal.toggle(GS.myPid);
});
```

- [ ] **Step 7: Auto-atualize o modal quando `game_state`/`city_state` chegam**

Em `game.js`, dentro de `handleGameState` (linha 3165-3178), logo antes do `}` de fechamento, adicione:

```js
  if(typeof InventoryModal !== 'undefined') InventoryModal.refresh();
```

Em `game.js`, dentro do callback `GS.on('cityState', msg => { ... })` (por volta da linha 20150), logo depois de `if(_fcPanelPid != null) _refreshFichaCidadePanel();`, adicione:

```js
  if(typeof InventoryModal !== 'undefined') InventoryModal.refresh();
```

- [ ] **Step 8: Verificação manual — ciclo completo**

Recarregue a página (`Ctrl+F5`). Confirme:
- O ícone 🎒 aparece sempre no canto inferior direito, na cidade E na masmorra, em qualquer tamanho de tela.
- Clicar nele abre o `InventoryModal` do seu próprio personagem (não somente-leitura).
- A tecla `I` abre/fecha o mesmo modal.
- No celular (ou emulação de viewport estreito no DevTools), o botão ⚔️ (novo `#actions-fab`) abre a gaveta de Ações/Habilidades/Encerrar Turno como antes — nada quebrou aí.
- Na cidade, clicar no retrato de um herói abre o painel de atributos (agora sem a seção de equipamento) com um botão "🎒 Ver inventário" que abre o `InventoryModal` — em modo somente-leitura se for outro jogador, editável se for você.
- Equipar um item pelo modal novo e depois abrir a ficha antiga (atributos) confirma que os dados batem (mesmo `player.gear`/`bag` autoritativo).

- [ ] **Step 9: Commit**

```bash
git add game.js game.css
git commit -m "refactor(inventario): remove telas antigas duplicadas, liga InventoryModal"
```

---

### Task 10: Verificação final (checklist completo da spec)

**Files:** nenhum arquivo novo — só verificação manual via preview do navegador.

- [ ] **Step 1: Rode a suíte de testes do servidor inteira**

```bash
python tools/test_boots_slot.py
python tools/test_ficha_cidade.py
```

Expected: ambos terminam com `0 falharam`.

- [ ] **Step 2: Percorra o checklist manual da spec**

Com `python server.py` rodando e uma partida em andamento (2 jogadores, se possível, pra testar o modo somente-leitura), confirme cada item:

- [ ] Abrir/fechar: ícone de canto, tecla `I`, botão `✕`, clique fora do modal.
- [ ] Equipar/trocar item por clique-clique.
- [ ] Equipar/trocar item por drag nativo (mouse).
- [ ] Bloqueio visual de slot incompatível durante o drag (ex.: poção sobre slot de bota).
- [ ] Bloqueio visual do slot de escudo quando há arma de duas mãos equipada.
- [ ] Tooltip simples (hover num item equipado).
- [ ] Tooltip com comparação (hover num item da bolsa com equivalente equipado) — setas ▲/▼ corretas.
- [ ] Crescimento da grade da bolsa ao equipar item com efeito `bagslots`.
- [ ] Modo somente-leitura ao abrir o inventário de outro jogador (via botão "🎒 Ver inventário" na ficha dele) — nenhuma ação de clique/drag deve mudar o estado dele.
- [ ] Ações/Habilidades/Encerrar Turno continuam sempre visíveis e funcionando na masmorra, sem precisar fechar o modal.
- [ ] No celular (viewport estreito), o botão ⚔️ ainda abre Ações/Habilidades normalmente.

- [ ] **Step 3: Commit final (se algum ajuste foi necessário nesta verificação)**

```bash
git add -A
git commit -m "fix(inventario): ajustes finais da verificacao manual"
```

(Pule este commit se nenhum ajuste foi necessário.)
