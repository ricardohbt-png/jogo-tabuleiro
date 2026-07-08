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
      if(item && !blocked) _wireTooltip(slot, item.id, null);
      if(_selected && _selected.kind === 'gear' && _selected.slotKey === cfg.key) slot.classList.add('selected');
      if(!_readOnly) slot.onclick = () => _onGearSlotClick(cfg.key, blocked);
      if(!_readOnly && !blocked){
        if(item){
          slot.draggable = true;
          slot.addEventListener('dragstart', (e) => {
            _selected = { kind: 'gear', slotKey: cfg.key };
            e.dataTransfer.setData('text/plain', '');
            e.dataTransfer.effectAllowed = 'move';
          });
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
      grid.appendChild(slot);
    }
  }

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
      if(item){
        const equipped = _equippedCounterpart(player, item);
        _wireTooltip(slot, item.id, equipped ? equipped.id : null);
      }
      if(_selected && _selected.kind === 'bag' && _selected.index === i) slot.classList.add('selected');
      if(!_readOnly) slot.onclick = () => _onBagSlotClick(i);
      if(!_readOnly){
        if(item){
          slot.draggable = true;
          slot.addEventListener('dragstart', (e) => {
            _selected = { kind: 'bag', index: i };
            e.dataTransfer.setData('text/plain', '');
            e.dataTransfer.effectAllowed = 'move';
          });
        }
        slot.addEventListener('dragover', (e) => { if(_selected){ e.preventDefault(); slot.classList.add('drop-hover'); } });
        slot.addEventListener('dragleave', () => slot.classList.remove('drop-hover'));
        slot.addEventListener('drop', (e) => {
          e.preventDefault();
          slot.classList.remove('drop-hover');
          _attemptMoveToBag(i);
        });
      }
      bar.appendChild(slot);
    }
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
    _renderGear(overlay, player);
    _renderBag(overlay, player);
  }

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

  function _updateDropFeedback(slot, slotKey){
    const player = _currentPlayer();
    if(!player || !_selected || _selected.kind !== 'bag'){ slot.classList.add('drop-invalid'); return; }
    const item = (player.bag || [])[_selected.index];
    const ok = !!item && GS.canPlaceItem(item, slotKey, player.gear || {});
    slot.classList.toggle('drop-invalid', !ok);
  }

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

  return { open, close, toggle, isOpen, refresh };
})();
