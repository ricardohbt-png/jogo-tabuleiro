'use strict';
// src/ui/inventoryModal.js — Legends for Hire
//
// Modal de Equipamento/Inventário estilo Diablo II/III. Renderer puro
// (DOM/CSS), ZERO lógica de jogo — lê GS.gameState/GS.cityState e chama
// GS.equipFromBag/GS.unequip/GS.reorderBag/GS.equipOffhand. Usado tanto na
// cidade quanto na masmorra (substitui os blocos de Equipamento+Inventário
// que existiam duplicados em renderMyPanel/renderFichaCidadeBody, em
// game.js). Ações/Habilidades/Encerrar Turno (masmorra) e Atributos/Guilda
// (cidade) continuam nos painéis antigos — este modal cuida de paperdoll,
// bolsa, ouro, estatísticas e atalhos.
//
// Carregado DEPOIS de game.js (ver index.html) — reaproveita funções
// globais de tooltip já existentes lá (gerarConteudoTooltip, corBordaPorPreco,
// esconderTooltip, _initItemTooltip) em vez de duplicá-las.

const InventoryModal = (() => {
  let _openPid  = null;   // pid cujo inventário está aberto (null = fechado)
  let _readOnly = false;
  let _storageCtx = null;
  let _selected = null;   // item selecionado (tap-to-select): {kind:'bag',index} | {kind:'gear',slotKey}
  const PANEL_PREFS_KEY = 'lfh_inventory_panel_preferences_v1';
  let _panelPrefs = _loadPanelPrefs();

  function _loadPanelPrefs(){
    const defaults = { statsHidden:false, shortcutsHidden:false };
    try{
      const saved = JSON.parse(localStorage.getItem(PANEL_PREFS_KEY) || '{}');
      return {
        statsHidden: saved.statsHidden === true,
        shortcutsHidden: saved.shortcutsHidden === true,
      };
    }catch(_){ return defaults; }
  }

  function _savePanelPrefs(){
    try{ localStorage.setItem(PANEL_PREFS_KEY, JSON.stringify(_panelPrefs)); }catch(_){ /* storage indisponível */ }
  }

  function _setPanelHidden(panel, hidden){
    if(panel !== 'stats' && panel !== 'shortcuts') return;
    _panelPrefs[panel === 'stats' ? 'statsHidden' : 'shortcutsHidden'] = !!hidden;
    _savePanelPrefs();
    refresh();
  }

  // Layout do paperdoll (3×3): posição visual de cada um dos 9 slots.
  // O rótulo do slot vem de ui.inv.slot.<key>, resolvido no RENDER: um `label`
  // aqui congelaria o idioma do carregamento (este arquivo é avaliado uma vez).
  const GEAR_LAYOUT = [
    { key: 'item1',    small: true,  magic: true,  empty: '📦' },
    { key: 'head',     small: false, magic: false, empty: '🪖' },
    { key: 'item2',    small: true,  magic: true,  empty: '📦' },
    { key: 'weapon',   small: false, magic: false, empty: '✊' },
    { key: 'armor',    small: false, magic: false, empty: '👕' },
    { key: 'off_hand', small: false, magic: false, empty: '🤚' },
    { key: 'ring1',    small: true,  magic: false, empty: '💍' },
    { key: 'boots',    small: false, magic: false, empty: '👢' },
    { key: 'ring2',    small: true,  magic: false, empty: '💍' },
  ];
  // `t` e `_rotulo` são globais de game.js, carregado ANTES deste arquivo.
  const _slotLabel = key => _rotulo(key, 'ui.inv.slot', key);

  // Instrumentos do Bardo (Fase 1): o instrumento vive na MÃO DO ESCUDO (o slot
  // off_hand do GEAR_LAYOUT), não em um slot próprio — não há 10º slot.

  const EDGE_D =
    'M0,.5 8,0 16,1 24,.25 32,.75 40,0 48,1 56,.4 64,.9 72,.15 80,1.1 88,.3 96,.7 100,0 ' +
    '100,8 99.5,16 100,24 99.25,32 100,40 99.5,48 100,56 99,64 100,72 99.6,80 100,88 99.25,96 100,100 ' +
    '92,99.5 84,99.25 76,100 68,99.5 60,100 52,99.4 44,100 36,99.65 28,100 20,99.35 12,100 4,100 0,100 ' +
    '.5,92 0,84 .75,76 0,68 .5,60 0,52 .6,44 0,36 .4,28 0,20 .75,12 0,4 0,0 Z';

  const CSS_TEXT = `
#inv-modal-overlay{position:fixed;inset:0;z-index:1100;display:flex;align-items:center;justify-content:center;
  background:rgba(0,0,0,.55);opacity:0;pointer-events:none;transition:opacity .18s ease;}
#inv-modal-overlay.open{opacity:1;pointer-events:auto;}
.inv-frame{position:relative;width:min(620px,94vw);max-width:94vw;}
.inv-frame.inv-combined-frame{width:min(1120px,96vw);}
.inv-frame.inv-combined-frame.stats-hidden,.inv-frame.inv-combined-frame.shortcuts-hidden,
.inv-frame.inv-combined-frame.stats-hidden.shortcuts-hidden{width:max-content;max-width:96vw;}
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
.inv-normal-body{display:grid;grid-template-columns:minmax(0,1fr) 96px;gap:12px;align-items:start;}
.inv-combined-body{display:grid;grid-template-columns:minmax(225px,280px) minmax(350px,1fr) 96px;gap:14px;align-items:start;}
.inv-combined-body.stats-hidden{grid-template-columns:max-content 96px;}
.inv-combined-body.shortcuts-hidden{grid-template-columns:max-content max-content;}
.inv-combined-body.stats-hidden.shortcuts-hidden{grid-template-columns:max-content;}
.inv-combined-body.stats-hidden .inv-main,.inv-combined-body.shortcuts-hidden .inv-main,
.inv-combined-body.stats-hidden.shortcuts-hidden .inv-main{width:max-content;max-width:100%;}
.inv-stats-panel{min-width:0;max-height:calc(100vh - 90px);overflow-y:auto;margin-top:40px;padding:0;
  border:1px solid #c8a95188;border-radius:8px;background:linear-gradient(145deg,#15110a,#090806);
  box-shadow:0 12px 35px rgba(0,0,0,.72),0 0 14px rgba(200,169,81,.14);}
.inv-stats-toolbar{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;
  color:#f0d98a;font:700 9px/1 'Cinzel',serif;letter-spacing:1.5px;border-bottom:1px solid #c8a95155;}
.inv-stats-toolbar button,.inv-panel-toggle{border:1px solid #9c783a;border-radius:4px;background:#2a1a0d;color:#ffe5a4;
  cursor:pointer;font:700 12px/1 Georgia,serif;min-width:24px;height:22px;padding:2px 6px;}
.inv-stats-toolbar button:hover,.inv-panel-toggle:hover{background:#543516;color:#fff1bf;}
.inv-stats-content{padding:0 8px 8px;}
.inv-stats-content .menu-status{width:auto;max-width:none;max-height:none;overflow:visible;background:transparent;border:0;border-radius:0;box-shadow:none;}
.inv-stats-content .st-header{display:none;}
.inv-stats-content .st-body{padding:4px 2px 8px;}
.inv-header-actions{display:flex;align-items:center;gap:6px;}
.inv-header-actions .inv-panel-toggle{font-size:11px;}
.inv-main{min-width:0;}
.inv-shortcuts{min-width:0;max-height:calc(100vh - 90px);overflow-y:auto;margin-top:40px;padding:12px 8px 14px;
  border:1px solid #c8a95188;border-radius:8px;background:linear-gradient(145deg,#15110a,#090806);
  box-shadow:0 12px 35px rgba(0,0,0,.72),0 0 14px rgba(200,169,81,.14);font-family:'Cinzel',serif;}
.inv-shortcuts-heading{color:#f0d98a;font-size:9px;letter-spacing:1.5px;text-align:center;padding:0 0 8px;
  border-bottom:1px solid #c8a95155;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;gap:4px;}
.inv-shortcuts-heading span{flex:1;text-align:center;}
.inv-shortcuts-heading .inv-panel-toggle{flex:0 0 auto;}
.inv-header{display:flex;justify-content:space-between;align-items:center;margin:40px 0 16px;}
.inv-title{color:#f4ecd8;font-family:Georgia,serif;font-weight:bold;letter-spacing:1px;
  text-shadow:0 0 10px rgba(244,220,140,.4);font-size:.95rem;}
.inv-title-icon{width:20px;height:20px;object-fit:contain;vertical-align:middle;margin:-3px 5px 0 0;}
.inv-close{color:#e8cf7e;cursor:pointer;font-size:1.1rem;opacity:.8;}
.inv-close:hover{opacity:1;}
.inv-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;align-items:center;justify-items:center;
  margin:0 auto 20px;max-width:320px;}
.inv-slot{width:72px;height:96px;border-radius:8px;display:flex;align-items:center;justify-content:center;position:relative;
  font-size:1.8rem;cursor:pointer;background:linear-gradient(160deg,rgba(20,20,22,.55),rgba(6,6,8,.7));
  border:1px solid #d4b968;box-shadow:inset 0 2px 5px rgba(0,0,0,.7),0 1px 0 rgba(244,220,140,.16);}
.inv-slot.instrumento-slot{border-color:#4db8ff;}
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
.inv-slot-emoji,.inv-bagslot-emoji{display:flex;align-items:center;justify-content:center;width:100%;height:100%;}
.inv-slot-emoji img,.inv-bagslot-emoji img{width:90%;height:90%;object-fit:contain;display:block;}
.inv-ammo-count{position:absolute;right:-5px;bottom:-5px;z-index:5;min-width:19px;height:19px;padding:0 4px;
  display:flex;align-items:center;justify-content:center;box-sizing:border-box;border:1px solid #ffe29a;border-radius:10px;
  background:#3b2410;color:#fff0bd;font:700 11px/1 Georgia,serif;box-shadow:0 1px 4px rgba(0,0,0,.9);pointer-events:none;}
.inv-gold{display:flex;align-items:center;justify-content:center;gap:6px;color:#ffcf7a;font-weight:bold;
  text-shadow:0 0 8px rgba(255,180,60,.6);font-family:Georgia,serif;margin-bottom:14px;}
.inv-bagbar{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;
  border-top:1px solid rgba(244,220,140,.3);padding-top:14px;}
.inv-bagslot{width:42px;height:42px;border-radius:6px;background:rgba(6,6,8,.55);
  border:1px solid rgba(244,220,140,.35);display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;cursor:pointer;}
.inv-bagslot.selected{outline:2px solid #ffe08a;outline-offset:2px;}
.inv-bagslot.usable{border-color:#2ecc40;box-shadow:inset 0 0 4px rgba(46,204,64,.4),0 0 6px rgba(46,204,64,.35);}
.inv-bagslot.drop-hover{outline:2px dashed #8fe08a;outline-offset:2px;}
.poison-charge-drops{position:absolute;z-index:4;top:4px;left:4px;display:flex;flex-wrap:wrap;gap:2px;
  width:30px;pointer-events:none;filter:drop-shadow(0 1px 2px rgba(0,0,0,.9));}
.poison-charge-drop{width:8px;height:11px;display:block;background:linear-gradient(135deg,#d38cff,#7134c7);
  clip-path:polygon(50% 0,92% 43%,80% 84%,50% 100%,20% 84%,8% 43%);border:1px solid #edc6ff;box-sizing:border-box;}
`;

  // Ícone do item: delega ao helper global de game.js (assets/itens/<id>.png,
  // com fallback pro emoji se o PNG não existir).
  // Baú do Refúgio: duas metades lado a lado — herói à ESQUERDA, baú à DIREITA.
  const STORAGE_CSS = `
.storage-modal{width:min(1080px,96vw)!important;max-width:96vw!important;}
.storage-modal .inv-modal{box-sizing:border-box;max-width:100%;}
.storage-modal .inv-header{margin-top:14px;}
.storage-columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start;}
.storage-column{min-width:0;display:flex;flex-direction:column;}
.storage-column h3{color:#f4ecd8;font-family:Georgia,serif;font-size:.85rem;letter-spacing:1px;text-align:center;margin:0 0 10px;}
.storage-column .inv-grid{width:100%;max-width:100%;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:14px;}
.storage-column .inv-slot{width:100%;max-width:72px;box-sizing:border-box;}
.storage-column .inv-bagbar{max-width:100%;justify-content:center;}
.storage-hint{color:#9c8a68;font-size:10px;text-align:center;margin:12px 0 0;line-height:1.4;}
.storage-room-link{margin-left:auto;margin-right:14px;padding:4px 10px;font-size:11px;cursor:pointer;
  color:#ffe5a4;background:#2a1a0d;border:1px solid #9c783a;border-radius:4px;font-family:Georgia,serif;}
.storage-room-link:hover{background:#543516;}
.storage-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;padding:10px;
  background:#110d0acc;border:1px solid #9c783a;border-radius:8px;max-height:52vh;overflow-y:auto;}
.storage-slot{position:relative;box-sizing:border-box;min-height:74px;padding:4px;border-radius:6px;
  border:1px solid #74572e;background:#291b0e;color:#f4ecd8;cursor:pointer;overflow:hidden;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;}
.storage-slot.empty{opacity:.5;}
.storage-slot:hover{border-color:#ffe08a;background:#4a3218;}
.storage-slot.selected{outline:2px solid #ffe08a;outline-offset:2px;}
.storage-slot.drop-hover{outline:2px dashed #8fe08a;outline-offset:2px;}
.storage-slot small{font-size:9px;line-height:1.1;text-align:center;overflow-wrap:anywhere;opacity:.85;}
.storage-slot-icon{display:flex;align-items:center;justify-content:center;width:30px;height:30px;font-size:1.3rem;}
.storage-slot-icon img{width:100%;height:100%;object-fit:contain;display:block;}
.storage-slot-plus{font-size:1.1rem;opacity:.45;}
.storage-gold{display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;margin-top:12px;
  color:#ffcf7a;font-family:Georgia,serif;}
.storage-gold input{width:76px;padding:3px 6px;background:#1a1208;color:#ffe5a4;
  border:1px solid #9c783a;border-radius:4px;}
.storage-gold button{padding:4px 9px;font-size:11px;cursor:pointer;color:#ffe5a4;
  background:#2a1a0d;border:1px solid #9c783a;border-radius:4px;}
.storage-gold button:hover{background:#543516;}
@media(max-width:760px){.storage-columns{grid-template-columns:minmax(0,1fr);}}
@media(max-width:900px){.inv-combined-body{grid-template-columns:minmax(190px,240px) minmax(270px,1fr) 82px;gap:9px;}.inv-combined-body.shortcuts-hidden{grid-template-columns:minmax(190px,240px) minmax(270px,1fr);}.inv-shortcuts{padding-left:4px;padding-right:4px;}}
@media(max-width:680px){.inv-frame.inv-combined-frame{width:min(620px,94vw);}.inv-combined-body,.inv-combined-body.stats-hidden,.inv-combined-body.shortcuts-hidden,.inv-combined-body.stats-hidden.shortcuts-hidden{display:flex;flex-direction:column;align-items:stretch;}.inv-stats-panel{order:0;margin-top:40px;}.inv-main{order:1;}.inv-shortcuts{order:2;margin-top:0;max-height:none;}.inv-combined-body.stats-hidden .inv-main{order:0;}.inv-combined-body.shortcuts-hidden .inv-main{order:1;}}
`;
  function _itemIconHTML(item, fallbackEmoji){
    return (typeof itemIconHTML === 'function') ? itemIconHTML(item, fallbackEmoji)
         : (item && item.emoji) || fallbackEmoji || '';
  }

  function _ammoCountBadgeHTML(item){
    if(!item || item.effect !== 'ammo') return '';
    const count = Math.max(0, Number(item.ammo_count) || 0);
    return `<span class="inv-ammo-count" aria-label="${t('ui.inv.municao_aria', {n:count})}">${count}</span>`;
  }

  function _injectStyles(){
    if(document.getElementById('inventory-modal-styles')) return;
    const style = document.createElement('style');
    style.id = 'inventory-modal-styles';
    style.textContent = CSS_TEXT + STORAGE_CSS;
    document.head.appendChild(style);
  }

  function _ensureDom(){
    if(document.getElementById('inv-modal-overlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'inv-modal-overlay';
    overlay.addEventListener('click', (e) => { if(e.target === overlay) close(); });
    // Largar no chão: arrastar um item e soltar FORA do frame do modal (no backdrop),
    // durante a masmorra, larga o item na casa adjacente (servidor escolhe).
    overlay.addEventListener('dragover', (e) => { if(_selected && e.target === overlay) e.preventDefault(); });
    overlay.addEventListener('drop', (e) => {
      if(!_selected || e.target !== overlay) return;   // só quando solto no backdrop
      e.preventDefault();
      const sel = _selected; _selected = null;
      const gsNow = (typeof GS !== 'undefined') ? GS.gameState : null;
      if(_readOnly || !gsNow || gsNow.phase !== 'playing'){ refresh(); return; }  // só na masmorra, não em só-leitura
      if(sel.kind === 'bag') GS.dropItem('bag', sel.index);
      else                   GS.dropItem('gear', sel.slotKey);
      close();
    });
    document.body.appendChild(overlay);
  }

  // O inventário continua sendo uma interface contextual: Esc/voltar fecha o
  // modal antes que o atalho global de configuração possa abrir outro painel.
  document.addEventListener('keydown', (e) => {
    if(e.key !== 'Escape' || !isOpen()) return;
    close();
    e.preventDefault();
    e.stopImmediatePropagation();
  }, true);

  function open(pid, opts){
    opts = opts || {};
    if(typeof window.fecharMenuHabilidades === 'function') window.fecharMenuHabilidades();
    if(typeof window.fecharMenuMagias === 'function') window.fecharMenuMagias();
    if(typeof window.fecharMenuStatus === 'function') window.fecharMenuStatus();
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
    _storageCtx = null;
    _selected = null;
    if(typeof window._ocultarAtalhosNoMenu === 'function') window._ocultarAtalhosNoMenu();
    const overlay = document.getElementById('inv-modal-overlay');
    if(overlay) overlay.classList.remove('open');
  }

  function toggle(pid, opts){
    if(isOpen()) close(); else open(pid, opts);
  }

  function isOpen(){ return _openPid != null || !!_storageCtx; }

  function refresh(){
    // Vale nos dois modos. No modo baú o conteúdo do baú vem SEMPRE de
    // `_storageCtx.payload` (só `updateStorage` o troca), então um `city_state`
    // que chegue no meio repinta a metade do herói sem poder ressuscitar uma
    // cópia velha do baú.
    if(_openPid != null || _storageCtx) _render();
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
    const twoHanded = GS.offHandBlockedByTwoHanded(gear);
    for(const cfg of GEAR_LAYOUT){
      const item = gear[cfg.key];
      const blocked = cfg.key === 'off_hand' && twoHanded && !item;
      const slot = document.createElement('div');
      slot.className = 'inv-slot'
        + (cfg.small ? ' small' : '')
        + (cfg.magic ? ' magic' : '')
        + (item && item.tipo_item === 'instrumento' ? ' instrumento-slot' : '')
        + (item ? ' filled' : ' empty')
        + (blocked ? ' blocked' : '');
      slot.dataset.slotKey = cfg.key;
      slot.title = blocked ? t('ui.inv.bloqueado_duas_maos')
                 : item ? item.name : _slotLabel(cfg.key);
      slot.innerHTML = blocked
        ? `<span class="inv-slot-blocked-x">✕</span>`
        : item ? `<span class="inv-slot-emoji">${_itemIconHTML(item, cfg.empty)}</span>${_ammoCountBadgeHTML(item)}`
               : `<span class="inv-slot-emoji inv-slot-empty-icon">${cfg.empty}</span>`;
      if(item && cfg.key === 'weapon' && typeof _poisonChargeDropsHTML === 'function')
        slot.insertAdjacentHTML('beforeend', _poisonChargeDropsHTML(player));
      if(item && !blocked){
        if(item.tipo_item === 'instrumento' && typeof aplicarTooltipInstrumento === 'function')
          aplicarTooltipInstrumento(slot, item);   // quadro próprio (não está em CATALOGO_ITENS)
        else
          _wireTooltip(slot, item.id, null, item);
      }
      if(_selected && _selected.kind === 'gear' && _selected.slotKey === cfg.key) slot.classList.add('selected');
      if(!_readOnly) slot.onclick = () => _onGearSlotClick(cfg.key, blocked);
      if(!_readOnly && !blocked){
        if(item){
          slot.draggable = true;
          slot.addEventListener('dragstart', (e) => {
            _selected = { kind: 'gear', slotKey: cfg.key };
            e.dataTransfer.setData('text/plain', JSON.stringify({kind:'gear',slotKey:cfg.key}));
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
      slot.innerHTML = item ? `<span class="inv-bagslot-emoji">${_itemIconHTML(item, '📦')}</span>${_ammoCountBadgeHTML(item)}` : '';
      const isScroll = !!item && item.effect === 'scroll';
      const isConsumable = !!item && !item.die && (item.item_slot === 'bag' || item.effect === 'heal' || item.effect === 'atk_bonus');
      const ehCaster = player.class_id === 'mage' || player.class_id === 'cleric';
      const gsNow = (typeof GS !== 'undefined') ? GS.gameState : null;
      const isMyOwnDungeonTurn = !_readOnly && player.id === GS.myPid && gsNow && gsNow.phase === 'playing'
        && GS.isMyTurn && player.alive && !player.action_done;
      const bonusBloqueado = !!item && typeof BONUS_ACTION_EFFECTS !== 'undefined'
        && BONUS_ACTION_EFFECTS.has(item.effect) && !!player.bonus_action_used;
      const podeUsar = isMyOwnDungeonTurn && isConsumable && !bonusBloqueado;
      const podeConjurar = isMyOwnDungeonTurn && isScroll && ehCaster;
      // Arremessáveis de bolsa (frasco_oleo/fogo_grego): clique direito abre a mira.
      const catDef = (typeof GS !== 'undefined' && GS.CATALOGO_ITENS)
        ? GS.CATALOGO_ITENS[item && item.id] : null;
      const isArremessavel = !!(catDef && catDef.arremessavel);
      const isShortcutItem = !!item && (isConsumable || isScroll || isArremessavel);
      const podeArremessar = isMyOwnDungeonTurn && isArremessavel && !player.action_done;
      if(isShortcutItem){
        slot.dataset.shortcutKind = 'item';
        slot.dataset.shortcutId = item.id;
      }
      if(item){
        if(podeUsar || podeConjurar || podeArremessar) slot.classList.add('usable');
        if(item.tipo_item === 'instrumento' && typeof aplicarTooltipInstrumento === 'function'){
          aplicarTooltipInstrumento(slot, item);   // quadro próprio (instrumento não está em CATALOGO_ITENS)
        } else if(isScroll && typeof aplicarTooltipPergaminho === 'function'){
          aplicarTooltipPergaminho(slot, item);   // tooltip específico de pergaminho — substitui o genérico abaixo
        } else {
          const equipped = _equippedCounterpart(player, item);
          _wireTooltip(slot, item.id, equipped ? equipped.id : null, item);
        }
      }
      if(_selected && _selected.kind === 'bag' && _selected.index === i) slot.classList.add('selected');
      if(!_readOnly){
        // Esquerdo: só seleciona/move (arrastar continua abaixo).
        slot.onclick = () => { _onBagSlotClick(i); };
        // Direito: usar/ativar (regra única). preventDefault tira o menu do browser.
        slot.addEventListener('contextmenu', (e) => {
          e.preventDefault();
          if(!item) return;
          if(podeArremessar && typeof window._iniciarMiraArremesso === 'function'){
            close(); window._iniciarMiraArremesso(item, player); return;
          }
          if(podeConjurar){ close(); castarPergaminho(item); return; }
          if(podeUsar){ useItem(item.id); return; }
        });
      }
      if(!_readOnly){
        if(item){
          slot.draggable = true;
          slot.addEventListener('dragstart', (e) => {
            _selected = { kind: 'bag', index: i };
            e.dataTransfer.setData('text/plain', JSON.stringify({kind:'bag',index:i}));
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

  function _statusPanelMarkup(player){
    if(typeof window._renderStatusPanelHTML === 'function')
      return window._renderStatusPanelHTML(player);
    return `<p class="st-empty">Estatísticas indisponíveis.</p>`;
  }

  function _shortcutPanelMarkup(){
    return `<aside class="inv-shortcuts" data-panel="shortcuts" aria-label="Atalhos">
      <div class="inv-shortcuts-heading"><span>ATALHOS</span><button type="button" class="inv-panel-toggle" data-inv-toggle="shortcuts" aria-label="Ocultar atalhos">▶</button></div>
      <div id="shortcut-bar" aria-label="Slots de atalho" hidden></div>
    </aside>`;
  }

  function _statsPanelMarkup(player){
    return `<aside class="inv-stats-panel" data-panel="stats" aria-label="Estatísticas">
      <div class="inv-stats-toolbar"><span>${t('ui.status.titulo')}</span><button type="button" data-inv-toggle="stats" aria-label="Ocultar estatísticas">◀</button></div>
      <div class="inv-stats-content">${_statusPanelMarkup(player)}</div>
    </aside>`;
  }

  function _wirePanelToggles(overlay){
    overlay.querySelectorAll('[data-inv-toggle]').forEach(btn => {
      btn.onclick = e => {
        e.preventDefault();
        e.stopPropagation();
        const panel = btn.dataset.invToggle;
        const hidden = panel === 'stats' ? _panelPrefs.statsHidden : _panelPrefs.shortcutsHidden;
        _setPanelHidden(panel, !hidden);
      };
    });
  }

  function _applyPanelPrefs(overlay){
    const body = overlay.querySelector('.inv-combined-body');
    if(!body) return;
    const frame = overlay.querySelector('.inv-combined-frame');
    body.classList.toggle('stats-hidden', _panelPrefs.statsHidden);
    body.classList.toggle('shortcuts-hidden', _panelPrefs.shortcutsHidden);
    if(frame){
      frame.classList.toggle('stats-hidden', _panelPrefs.statsHidden);
      frame.classList.toggle('shortcuts-hidden', _panelPrefs.shortcutsHidden);
    }
    const stats = overlay.querySelector('[data-panel="stats"]');
    const shortcuts = overlay.querySelector('[data-panel="shortcuts"]');
    if(stats) stats.hidden = _panelPrefs.statsHidden;
    if(shortcuts) shortcuts.hidden = _panelPrefs.shortcutsHidden;
    overlay.querySelectorAll('[data-inv-toggle="stats"]').forEach(btn => {
      btn.textContent = _panelPrefs.statsHidden ? '▶' : '◀';
      btn.title = _panelPrefs.statsHidden ? 'Mostrar estatísticas' : 'Ocultar estatísticas';
      btn.setAttribute('aria-label', btn.title);
    });
    overlay.querySelectorAll('[data-inv-toggle="shortcuts"]').forEach(btn => {
      btn.textContent = _panelPrefs.shortcutsHidden ? '◀' : '▶';
      btn.title = _panelPrefs.shortcutsHidden ? 'Mostrar atalhos' : 'Ocultar atalhos';
      btn.setAttribute('aria-label', btn.title);
    });
  }

  function _render(){
    const overlay = document.getElementById('inv-modal-overlay');
    if(!overlay) return;
    const player = _currentPlayer();
    if(!player){ close(); return; }
    if(_storageCtx){ _renderStorage(overlay, player); return; }
    overlay.innerHTML = `
      <div class="inv-frame inv-combined-frame">
        <div class="inv-modal">
          <svg class="inv-edge" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path class="glow" d="${EDGE_D}"/>
            <path class="char" d="${EDGE_D}"/>
            <path class="gold" d="${EDGE_D}"/>
          </svg>
          <div class="inv-body inv-normal-body inv-combined-body">
            ${_statsPanelMarkup(player)}
            <div class="inv-main">
              <div class="inv-header">
                <div class="inv-title"><img class="inv-title-icon" src="assets/inventario.png" alt="" aria-hidden="true"> ${t('ui.inv.titulo')} — ${player.name || ''}${_readOnly ? ' ' + t('ui.inv.somente_leitura') : ''}</div>
                <div class="inv-header-actions"><button type="button" class="inv-panel-toggle" data-inv-toggle="stats" title="Estatísticas">◀</button><button type="button" class="inv-panel-toggle" data-inv-toggle="shortcuts" title="Atalhos">▶</button><div class="inv-close" title="Fechar">✕</div></div>
              </div>
              <div class="inv-grid"></div>
              <div class="inv-gold">🪙 <span></span></div>
              <div class="inv-bagbar"></div>
            </div>
            ${_shortcutPanelMarkup()}
          </div>
        </div>
        <div class="inv-logo-wrap"><img src="assets/logotipo.png" alt="Legends for Hire"></div>
      </div>`;
    overlay.querySelector('.inv-close').onclick = close;
    overlay.querySelector('.inv-gold span').textContent = player.gold ?? 0;
    _renderGear(overlay, player);
    _renderBag(overlay, player);
    if(typeof window._mostrarAtalhosNoMenu === 'function') window._mostrarAtalhosNoMenu();
    _wirePanelToggles(overlay);
    _applyPanelPrefs(overlay);
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
    // Soltar um item do baú no paperdoll é a mesma retirada de sempre: quem escolhe
    // o encaixe é o servidor, que já manda o item para o slot livre compatível.
    // (Cuidado: `sel.index` é índice DO BAÚ — tratá-lo como índice da bolsa
    // equiparia outro item.)
    if(sel.kind === 'stash'){ GS.refugioTake(_storageCtx.scope, sel.index); return; }
    const player = _currentPlayer();
    const item = player && player.bag ? player.bag[sel.index] : null;
    if(!item || !GS.canPlaceItem(item, slotKey, player.gear || {})){ refresh(); return; }
    const ehOffhand = slotKey === 'off_hand' && GS.isOffhandWeapon(item);
    if(ehOffhand) GS.equipOffhand(sel.index);
    else          GS.equipFromBag(sel.index);
  }

  function _attemptMoveToBag(toIndex){
    const sel = _selected; _selected = null;
    if(!sel){ refresh(); return; }
    if(sel.kind === 'stash'){ GS.refugioTake(_storageCtx.scope, sel.index); return; }
    if(sel.kind === 'bag'){
      if(sel.index !== toIndex) GS.reorderBag(sel.index, toIndex);
      else refresh();
      return;
    }
    GS.unequip(sel.slotKey);   // sel.kind === 'gear'
  }

  function _updateDropFeedback(slot, slotKey){
    const player = _currentPlayer();
    if(!player || !_selected){ slot.classList.add('drop-invalid'); return; }
    if(_selected.kind === 'stash'){
      const doBau = _storageStash().items[_selected.index];
      slot.classList.toggle('drop-invalid', !doBau || !GS.canPlaceItem(doBau, slotKey, player.gear || {}));
      return;
    }
    if(_selected.kind !== 'bag'){ slot.classList.add('drop-invalid'); return; }
    const item = (player.bag || [])[_selected.index];
    const ok = !!item && GS.canPlaceItem(item, slotKey, player.gear || {});
    slot.classList.toggle('drop-invalid', !ok);
  }

  // Acha, entre os 9 slots do paperdoll, qual (se algum) aceitaria este item —
  // usado pra saber contra qual item equipado comparar no tooltip.
  function _equippedCounterpart(player, bagItem){
    const gear = player.gear || {};
    for(const cfg of GEAR_LAYOUT){
      if(gear[cfg.key] && GS.canPlaceItem(bagItem, cfg.key, gear)) return gear[cfg.key];
    }
    return null;
  }

  function _showInventoryTooltip(itemId, comparisonItemId, touchPos, itemInstance){
    if(typeof GS === 'undefined' || !GS.CATALOGO_ITENS) return;
    const bruto = itemInstance || GS.CATALOGO_ITENS[itemId];
    const item = (typeof normalizarItemTooltip === 'function')
      ? normalizarItemTooltip(bruto) : bruto;
    if(!item || typeof _initItemTooltip !== 'function' || typeof gerarConteudoTooltip !== 'function') return;
    _initItemTooltip();
    const t = document.getElementById('item-tooltip');
    if(!t) return;
    // O catálogo do cliente não guarda o número de doses da instância na
    // mochila. Para poções de cura, o quadro usa a cópia enviada pelo servidor.
    const atual = itemInstance || item;
    let html;
    if(atual.effect === 'heal' || atual.effect === 'regeneration'){
      const maxUses = Number(atual.max_uses || 1);
      const usesLeft = Number(atual.uses_left == null ? maxUses : atual.uses_left);
      const doses = maxUses > 1
        ? renderLinhaTooltip('🧪', t('ui.inv.doses_restantes'), `${usesLeft}/${maxUses}`)
        : '';
      const regeneracao = atual.effect === 'regeneration';
      html = `
        <div style="padding:10px 14px 8px; border-bottom:1px solid #c8a95133;">
          <div style="font-family:'Cinzel Decorative',serif; color:#2ecc40; font-size:13px; margin-bottom:2px;">${atual.name || item.name}</div>
          <div style="color:#2ecc4088; font-size:9px; letter-spacing:3px;">${t('ui.item.tipo_label.consumivel')}</div>
        </div>
        <div style="padding:10px 14px;">
          ${regeneracao
            ? renderLinhaTooltip('🌿', 'Reserva', `${atual.value || 0} HP; +1 HP por rodada`)
            : renderLinhaTooltip('❤️', 'Cura por uso', `+${atual.value || 0} HP`)}
          ${renderLinhaTooltip('⚡', 'Uso', 'Ação bônus')}
          ${doses}
        </div>`;
    } else {
      html = gerarConteudoTooltip(item);
    }
    const equipped = comparisonItemId ? GS.CATALOGO_ITENS[comparisonItemId] : null;
    if(equipped){
      const rows = GS.compareItemStats(item, equipped);
      if(rows.length){
        html += `<div style="padding:8px 14px;border-top:1px solid #c8a95133;">
          <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:6px;">${t('ui.inv.comparado')}</div>
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

  function _wireTooltip(el, itemId, comparisonItemId, itemInstance){
    if(!itemId) return;
    let pressTimer = null;
    el.addEventListener('mouseenter', (e) => {
      _showInventoryTooltip(itemId, comparisonItemId, null, itemInstance);
      const tooltip = document.getElementById('item-tooltip');
      if(tooltip && typeof posicionarTooltipAbaixo === 'function') posicionarTooltipAbaixo(tooltip, e.currentTarget);
    });
    el.addEventListener('mouseleave', () => { if(typeof esconderTooltip === 'function') esconderTooltip(); });
    el.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      pressTimer = setTimeout(() => _showInventoryTooltip(itemId, comparisonItemId, { x: touch.clientX, y: touch.clientY }, itemInstance), 350);
    }, { passive: true });
    el.addEventListener('touchmove', () => clearTimeout(pressTimer), { passive: true });
    el.addEventListener('touchend', () => {
      clearTimeout(pressTimer);
      if(typeof esconderTooltip === 'function') esconderTooltip();
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Baú do Refúgio dos Heróis (compartilhado ou do quarto privado).
  //
  // Mesma janela do inventário, em duas metades: à ESQUERDA o inventário do
  // herói (o MESMO paperdoll + bolsa do modo normal, via _renderGear/_renderBag)
  // e à DIREITA os espaços do baú. Transferir é o gesto principal — clicar num
  // item do baú manda pra bolsa; selecionar um item da bolsa/paperdoll e clicar
  // num espaço do baú guarda. Arrastar faz o mesmo nos dois sentidos.
  //
  // O renderer é PURO: quem move item é o servidor (refugio_store/refugio_take),
  // e a janela só se redesenha quando o novo estado do baú volta em
  // `updateStorage`. Por isso `_openPid` é preenchido com o próprio jogador —
  // `_currentPlayer()`, os cliques e o `refresh()` da metade esquerda dependem
  // dele (com `_openPid = null` a metade do herói fica inerte).

  function _storageStash(){
    const scope = _storageCtx.scope, payload = _storageCtx.payload || {};
    const s = (scope === 'shared') ? (payload.shared || {}) : payload;
    return {
      items: s.items || [],
      gold : Number(s.gold || 0),
      limit: Math.max(1, Number(s.slot_limit) || (scope === 'shared' ? 10 : 3)),
    };
  }

  function _storageStore(sel){
    if(!sel || !_storageCtx) return;
    if(sel.kind === 'bag') GS.refugioStore(_storageCtx.scope, 'bag',  sel.index);
    else                   GS.refugioStore(_storageCtx.scope, 'gear', sel.slotKey);
  }

  function _renderStashGrid(overlay){
    const grid  = overlay.querySelector('[data-storage="stash"]');
    const stash = _storageStash();
    grid.innerHTML = '';
    for(let i = 0; i < stash.limit; i++){
      const item = stash.items[i];
      const slot = document.createElement('div');
      slot.className = 'storage-slot' + (item ? ' filled' : ' empty');
      slot.dataset.index = String(i);
      slot.title = item ? (item.name || item.id || t('ui.bau.slot.padrao')) : t('ui.inv.espaco_vazio');
      slot.innerHTML = item
        ? `<span class="storage-slot-icon">${_itemIconHTML(item, '📦')}</span>${_ammoCountBadgeHTML(item)}<small></small>`
        : '<span class="storage-slot-plus">+</span>';
      if(item){
        slot.querySelector('small').textContent = item.name || item.id || 'Item';
        _wireTooltip(slot, item.id, null, item);
        slot.draggable = true;
        slot.addEventListener('dragstart', (e) => {
          _selected = { kind: 'stash', index: i };
          e.dataTransfer.setData('text/plain', JSON.stringify({kind:'stash',index:i}));
          e.dataTransfer.effectAllowed = 'move';
        });
      }
      if(_selected && _selected.kind === 'stash' && _selected.index === i) slot.classList.add('selected');
      slot.onclick = () => {
        const sel = _selected;
        if(sel && sel.kind !== 'stash'){ _selected = null; _storageStore(sel); return; }
        if(sel && sel.kind === 'stash'){ _selected = null; refresh(); return; }
        if(item) GS.refugioTake(_storageCtx.scope, i);
      };
      // Espaço vazio TAMBÉM é alvo de drop (é o caso comum: baú vazio). Por isso
      // o slot é uma div e não um <button disabled>, que não dispara drag.
      slot.addEventListener('dragover', (e) => {
        if(!_selected || _selected.kind === 'stash') return;
        e.preventDefault();
        slot.classList.add('drop-hover');
      });
      slot.addEventListener('dragleave', () => slot.classList.remove('drop-hover'));
      slot.addEventListener('drop', (e) => {
        e.preventDefault();
        slot.classList.remove('drop-hover');
        const sel = _selected; _selected = null;
        if(!sel || sel.kind === 'stash'){ refresh(); return; }
        _storageStore(sel);
      });
      grid.appendChild(slot);
    }
  }

  function _renderStorage(overlay, player){
    const scope  = _storageCtx.scope;
    const shared = scope === 'shared';
    const stash  = _storageStash();
    overlay.innerHTML = `
      <div class="inv-frame storage-modal inv-combined-frame">
        <div class="inv-modal">
          <svg class="inv-edge" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path class="glow" d="${EDGE_D}"/>
            <path class="char" d="${EDGE_D}"/>
            <path class="gold" d="${EDGE_D}"/>
          </svg>
          <div class="inv-body inv-combined-body">
            ${_statsPanelMarkup(player)}
            <div class="inv-main storage-main">
              <div class="inv-header">
                <div class="inv-title">🧰 ${t(shared ? 'ui.inv.bau_compartilhado_caixa' : 'ui.inv.bau_heroi_caixa')}</div>
                <div class="inv-header-actions"><button type="button" class="inv-panel-toggle" data-inv-toggle="stats" title="Estatísticas">◀</button><button type="button" class="inv-panel-toggle" data-inv-toggle="shortcuts" title="Atalhos">▶</button>${shared ? '' : `<button type="button" class="storage-room-link">${t('ui.inv.decorar_quarto')}</button>`}<div class="inv-close" title="${t('ui.geral.fechar')}">✕</div></div>
              </div>
              <div class="storage-columns">
              <section class="storage-column storage-stash">
                <h3>${t(shared ? 'ui.refugio.bau_compartilhado' : 'ui.inv.bau_heroi')} (${stash.items.length}/${stash.limit})</h3>
                <div class="storage-grid" data-storage="stash"></div>
                <div class="storage-gold">
                  🪙 <b class="storage-gold-total"></b>
                  <input class="storage-gold-input" type="number" min="0" step="1" value="0" aria-label="${t('ui.inv.quantidade_ouro')}">
                  <button type="button" data-gold="deposit">${t('ui.inv.depositar')}</button>
                  <button type="button" data-gold="withdraw">${t('ui.refugio.retirar')}</button>
                </div>
                <p class="storage-hint">${t('ui.inv.dica_do_bau')}</p>
              </section>
              <section class="storage-column storage-hero">
                <h3>${t('ui.inv.inventario')} — <span class="storage-hero-name"></span></h3>
                <div class="inv-grid"></div>
                <div class="inv-gold">🪙 <span></span></div>
                <div class="inv-bagbar"></div>
                <p class="storage-hint">${t('ui.inv.dica_para_o_bau')}</p>
              </section>
              </div>
            </div>
            ${_shortcutPanelMarkup()}
          </div>
        </div>
      </div>`;
    overlay.querySelector('.storage-hero-name').textContent = player.name || '';
    overlay.querySelector('.inv-gold span').textContent     = player.gold ?? 0;
    overlay.querySelector('.storage-gold-total').textContent = stash.gold;
    overlay.querySelector('.inv-close').onclick = close;
    // Troféus e fundo do quarto seguem no painel próprio. Fechar ANTES de pedir
    // é o que faz o estado voltar como painel em vez de repintar este baú.
    const linkQuarto = overlay.querySelector('.storage-room-link');
    if(linkQuarto) linkQuarto.onclick = () => { close(); GS.openQuarto(); };
    _renderGear(overlay, player);
    _renderBag(overlay, player);
    _renderStashGrid(overlay);
    if(typeof window._mostrarAtalhosNoMenu === 'function') window._mostrarAtalhosNoMenu();
    _wirePanelToggles(overlay);
    _applyPanelPrefs(overlay);
    // Soltar em qualquer ponto vazio da metade do herói também retira do baú.
    // Os slots da bolsa já tratam o próprio drop (e zeram `_selected`), então
    // o evento que borbulha até aqui não repete a retirada.
    const hero = overlay.querySelector('.storage-hero');
    hero.addEventListener('dragover', (e) => { if(_selected && _selected.kind === 'stash') e.preventDefault(); });
    hero.addEventListener('drop', (e) => {
      const sel = _selected;
      if(!sel || sel.kind !== 'stash') return;
      e.preventDefault();
      _selected = null;
      GS.refugioTake(scope, sel.index);
    });
    overlay.querySelectorAll('[data-gold]').forEach(btn => btn.onclick = () => {
      const n = Math.max(0, Number(overlay.querySelector('.storage-gold-input').value) || 0);
      if(n > 0) GS.refugioGold(scope, btn.dataset.gold, n);
    });
  }

  function openStorage(scope, payload){
    if(typeof window.fecharMenuStatus === 'function') window.fecharMenuStatus();
    _injectStyles();
    _ensureDom();
    _storageCtx = { scope, payload: payload || {} };
    _openPid  = (typeof GS !== 'undefined') ? GS.myPid : null;
    _readOnly = false;
    _selected = null;
    _render();
    requestAnimationFrame(() => {
      const overlay = document.getElementById('inv-modal-overlay');
      if(overlay) overlay.classList.add('open');
    });
  }

  // Só o estado do MESMO baú que está aberto repinta a janela — um
  // `quarto_state` que chegue com o baú compartilhado aberto (ou vice-versa)
  // trocaria o baú debaixo da mão do jogador.
  function updateStorage(scope, payload){
    if(!_storageCtx || _storageCtx.scope !== scope) return;
    _storageCtx = { scope, payload: payload || {} };
    _selected = null;
    _render();
  }

  function storageScope(){ return _storageCtx ? _storageCtx.scope : null; }

  return { open, close, toggle, isOpen, refresh, openStorage, updateStorage, storageScope };
})();
