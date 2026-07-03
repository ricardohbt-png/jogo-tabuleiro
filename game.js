'use strict';
// ===========================================================================
// game.js — Legends for Hire (todo o JavaScript do jogo)
// A estrutura HTML do <body> foi movida para cá e é injetada ANTES de
// qualquer código que acesse o DOM, preservando 100% o comportamento.
// ===========================================================================

// Verifica se o catálogo está acessível (exposto em window por main.js).
if (typeof CATALOGO_ITENS === 'undefined') {
  console.error('❌ CATALOGO_ITENS não encontrado — verifique a ordem dos scripts');
} else {
  console.log('✅ CATALOGO_ITENS carregado:', Object.keys(CATALOGO_ITENS).length, 'itens');
}

document.body.innerHTML = `
<!-- ══ VINHETA DE SOBREVIVÊNCIA (efeito de pressão de fome/sede) ══ -->
<div id="vinheta-sobrevivencia" style="position:fixed; inset:0; pointer-events:none; z-index:50; transition:box-shadow 1s ease;"></div>
<!-- ══ CONNECT ══ -->
<div id="screen-connect" class="screen active">
  <!-- Capa do jogo: aparece em tela cheia no boot; após o 1º clique recua para fundo sutil (ver .dismissed em game.css) -->
  <div id="cover-splash">
    <div id="cover-hint">Clique para começar</div>
  </div>
  <div class="logo">
    <h1>LEGENDS FOR HIRE</h1>
    <p>RPG de Tabuleiro Online — até 6 jogadores</p>
  </div>
  <div class="connect-panel">
    <h2>Entrar na Aventura</h2>
    <div id="hint-host" style="background:#0d1a0d;border:1px solid #2a4a2a;border-radius:6px;padding:8px 12px;font-size:.75rem;color:#8ab88a;line-height:1.5;">
      ⚙️ <b style="color:#6fc96f;">Como jogar:</b> Clique duas vezes em <code style="background:#1a2a1a;padding:1px 5px;border-radius:3px;color:#a0e0a0;">iniciar.bat</code> para iniciar o servidor e abrir o jogo automaticamente.
    </div>
    <div class="field">
      <label>Seu nome de herói</label>
      <input id="input-name" type="text" maxlength="20" placeholder="Ex: Thorin" value="">
    </div>
    <div class="field" id="field-server">
      <label>Endereço do servidor</label>
      <input id="input-server" type="text" placeholder="ws://localhost:8765" value="ws://localhost:8765">
    </div>
    <button class="btn-primary" onclick="createRoom()">⚔ Criar Nova Sala</button>
    <div class="divider">ou</div>
    <div class="field">
      <label>Código da sala</label>
      <div class="join-row">
        <input id="input-code" type="text" maxlength="4" placeholder="ABCD">
        <button class="btn-secondary btn-sm" onclick="joinRoom()">Entrar</button>
      </div>
    </div>
    <!-- Reaparece (via JS) quando há uma sessão salva — volta à partida após F5/queda -->
    <button id="btn-rejoin" class="btn-secondary" style="display:none;margin-top:10px;width:100%;"
            onclick="rejoinSaved()">🔌 Reconectar à última partida</button>
  </div>
</div>

<!-- ══ CLASS SELECT ══ -->
<div id="screen-class-select" class="screen">
  <div id="cs-sky"></div>
  <canvas id="cs-canvas"></canvas>
  <div id="cs-panel">
    <div class="cs-pn" id="cs-pane-inner">
      <!-- Portrait photo — visible only when the class has a portrait defined -->
      <div id="cs-portrait-frame">
        <img id="cs-portrait-img" src="" alt="" />
      </div>
      <div id="cs-hero-name"></div>
      <div id="cs-hero-cls"></div>
      <div id="cs-divider"></div>
      <div id="cs-desc"></div>
      <div id="cs-hp"></div>
      <div id="cs-stats" class="cs-stats"></div>
      <div id="cs-skills" class="cs-skills"></div>
    </div>
  </div>
  <div id="cs-lobby-bar">
    <span id="cs-room-lbl">SALA</span>
    <div id="cs-room-code" onclick="copyCode()" title="Clique para copiar">----</div>
    <div id="cs-players-row"></div>
    <div id="cs-dungeon-picker"></div>
    <button id="cs-btn-start" onclick="startGame()" style="display:none">▶ Iniciar Jogo</button>
  </div>
  <div id="cs-confirm-wrap">
    <div id="cs-progress-wrap"><div id="cs-progress-fill"></div></div>
    <button id="cs-btn-confirm" onclick="csConfirmClass()">⚔ Partir para a Aventura</button>
  </div>
  <div id="cs-hint">Escolha seu herói</div>
  <!-- Celular: fundo + botão flutuante para abrir/fechar a aba de características -->
  <div id="cs-info-backdrop" onclick="toggleCsInfo(false)"></div>
  <button id="cs-info-btn" onclick="toggleCsInfo()" title="Ver características do herói">ℹ️ Características</button>
</div>


<!-- ══ CITY ══ -->
<div id="screen-city" class="screen">
  <canvas id="city-3d-canvas"></canvas>
  <div id="city-time-badge">⏳ Carregando…</div>
  <div id="city-bldg-tooltip" style="display:none"></div>
  <div id="city-hero-bar"></div>
  <div id="city-dungeon-bar">
    <span id="city-host-hint"></span>
    <button class="btn-enter-dungeon" id="btn-enter-dungeon"
            onclick="triggerDungeonEntrance()">⚔ Entrar na Masmorra</button>
  </div>
  <!-- Legacy IDs kept for shop/compat -->
  <div id="city-players-bar" style="display:none"></div>
</div>

<!-- Shop Modal -->
<div id="shop-modal">
  <div class="shop-box">
    <h3 id="shop-title">Loja</h3>
    <div class="shop-subtitle" id="shop-subtitle"></div>
    <div class="shop-tabs" id="shop-tabs"></div>
    <div class="shop-items" id="shop-items-list"></div>
    <div class="shop-footer">
      <div class="shop-gold-disp">💰 Ouro: <span id="shop-gold-val">0</span></div>
      <button class="btn-cancel" onclick="closeShop()">← Voltar ao Mapa</button>
    </div>
  </div>
</div>

<!-- ══ GAME ══ -->
<div id="screen-game" class="screen">
  <div id="map-panel">
    <div id="map-header">
      <h2>LEGENDS FOR HIRE</h2>
      <span class="round-badge" id="round-badge">Turno 1</span>
      <span class="turn-badge" id="turn-badge">—</span>
      <span class="turn-badge" id="turn-timer-badge" style="display:none">⏳ 30s</span>
      <div id="view-3d-ctrls">
        <span id="orbit-hint">🖱 esq: orbitar &nbsp;·&nbsp; dir: pan &nbsp;·&nbsp; scroll: zoom</span>
        <button id="btn-cam-reset" onclick="resetCamera3D()" title="Visão isométrica padrão (R)">⌂ Reset</button>
        <button id="btn-3d-toggle" onclick="toggle3D()" title="Alternar visão 3D / 2D">🎲 3D</button>
        <button id="btn-ajuda" onclick="toggleAjuda()" title="Como jogar">❓</button>
      </div>
    </div>
    <div id="map-wrap">
      <canvas id="dungeon-canvas"></canvas>
      <!-- Fase 3: HUD de objetivos + botão Libertar (só em masmorra autorada) -->
      <div id="objectives-hud" style="display:none"></div>
      <button id="btn-libertar" style="display:none" onclick="GS.libertarPrisioneiro()">🔓 Libertar prisioneiro</button>
    </div>
    <canvas id="dice-canvas"></canvas>
    <div id="gm-log">
      <div id="gm-log-header">
        <span>📖 MESTRE DO JOGO</span>
      </div>
      <!-- Histórico das últimas rolagens — os dados 3D somem em 3 s; aqui ficam -->
      <div id="dice-history"></div>
      <div id="gm-log-body"></div>
    </div>
  </div>

  <div id="side-panel">
    <button id="ficha-close-btn" onclick="toggleFichaDrawer(false)">✕ Fechar ficha</button>
    <div id="players-panel">
      <div class="ph">Aventureiros</div>
      <div id="player-cards"></div>
    </div>
    <div id="my-panel">
      <div id="my-panel-inner">
        <!-- Hero portrait — shown at top of character sheet when available -->
        <div id="my-hero-portrait">
          <img id="my-hero-portrait-img" src="" alt="" />
        </div>
        <div class="section-title">Meu Personagem</div>
        <div id="my-stats"></div>
        <div class="section-title">Ações</div>
        <div class="actions-grid" id="action-btns"></div>
        <div class="section-title">Habilidades</div>
        <div class="skills-list" id="skills-list"></div>
        <div class="section-title">Inventário</div>
        <div class="inventory" id="inventory-list"></div>
      </div>
      <div style="padding:6px 8px;border-top:1px solid var(--border);flex-shrink:0;">
        <button class="btn-end-turn" id="btn-end-turn" onclick="endTurn()" disabled>
          ⏭ Encerrar Turno
        </button>
      </div>
    </div>
  </div>
  <!-- Celular: fundo escuro + botão flutuante que abrem/fecham a ficha (gaveta) -->
  <div id="ficha-backdrop" onclick="toggleFichaDrawer(false)"></div>
  <button id="ficha-fab" onclick="toggleFichaDrawer(true)" title="Ficha do personagem">🎒</button>
</div>

<!-- ══ END SCREEN ══ -->
<div id="screen-end" class="screen">
  <h1 id="end-title"></h1>
  <p id="end-msg"></p>
  <button class="btn-primary" style="width:200px;" onclick="location.reload()">Jogar Novamente</button>
</div>

<!-- Target Modal -->
<div id="target-modal">
  <div class="target-box">
    <h3 id="target-title">Selecionar Alvo</h3>
    <div class="target-list" id="target-list"></div>
    <button class="btn-cancel" onclick="closeTargetModal()">Cancelar</button>
  </div>
</div>

<!-- Chest Loot Window -->
<div id="chest-overlay">
  <div class="chest-box">
    <h3 id="chest-title">🎁 Baú de Tesouro</h3>
    <div class="chest-subtitle" id="chest-subtitle">Aproxime-se do baú para coletar</div>
    <div id="chest-items-list"></div>
    <button class="btn-cancel" style="margin-top:10px" onclick="closeChestWindow()">Fechar</button>
  </div>
</div>

<div id="tooltip"></div>
<div id="toast"></div>
`;

// All mutable game state is owned by GS (gameState.js):
//   GS.ws, GS.myPid, GS.myName, GS.gameState, GS.lobbyState, GS.cityState,
//   GS.isMyTurn, GS.pendingSkill, GS.pendingAction,
//   GS.activeShop, GS.shopTabIdx, GS.pendingShopOpen
//
// Rendering-only constants and helpers stay here:

// Verificar se GS foi carregado corretamente
if (typeof GS === 'undefined') {
  console.error('ERRO CRÍTICO: gameState.js não foi carregado!');
  document.body.innerHTML = '<h1>Erro ao carregar jogo</h1><p>Feche o navegador e tente novamente via: python start.py</p>';
  throw new Error('GS is not defined');
}

const TILE_WALL=GS.TILE_WALL, TILE_FLOOR=GS.TILE_FLOOR, TILE_DOOR=GS.TILE_DOOR;
const CELL=64; // px per tile (CSS pixels × devicePixelRatio)
const SPR_SCALE=CELL/48; // sprite scale factor (sprites designed for CELL=48)
// Cache-buster das texturas de peão (frente.png): garante que imagens trocadas
// no disco apareçam (uma busca fresca por sessão; cacheado dentro da sessão).
const _ASSET_VER = Date.now();
function _assetURL(path){ return path + (path.includes('?') ? '&' : '?') + 'v=' + _ASSET_VER; }

// Tamanho da miniatura PNG extrudada por casa de footprint (maior = miniatura
// maior/mais alta no 3D). 1 casa de árvore → ~1.8 unidades de largura.
const DECOR_MINI_ESCALA = 2.0;

// ── Decoration 3D spec — shape/height/color per type (procedural render) ──────
const DECOR_3D = {
  cama:           { shape: 'box', h: 0.5,  color: 0x8a5a3c },
  lareira:        { shape: 'box', h: 0.8,  color: 0x6b6b6b },
  fonte:          { shape: 'cyl', h: 0.6,  color: 0x5a8fb0 },
  fogueira:       { shape: 'cyl', h: 0.25, color: 0xd2691e },
  tumba:          { shape: 'box', h: 0.6,  color: 0x777777 },
  mesa_cadeiras:  { shape: 'box', h: 0.6,  color: 0x9a6b3c },
  estante:        { shape: 'box', h: 1.6,  color: 0x6b4a2a },
  carroca:        { shape: 'box', h: 0.7,  color: 0x7a5230 },
  coluna:         { shape: 'cyl', h: 1.8,  color: 0xaaaaaa },
  barril:         { shape: 'cyl', h: 0.8,  color: 0x8a5a2a },
  arca_tesouros:  { shape: 'box', h: 0.6,  color: 0xc8a23a },
  cama_casal:     { shape: 'box', h: 0.5,  color: 0x8a5a3c },
  estante_livros: { shape: 'box', h: 1.6,  color: 0x5a3a1a },
  altar:          { shape: 'box', h: 0.9,  color: 0x9a9aae },
  trono:          { shape: 'box', h: 1.2,  color: 0xc8a23a },
  gaiola:         { shape: 'box', h: 1.5,  color: 0x555555 },
  grades_prisao:  { shape: 'box', h: 1.5,  color: 0x555555 },
  estante_armas:  { shape: 'box', h: 1.6,  color: 0x6b4a2a },
  mesa_tortura:   { shape: 'box', h: 0.6,  color: 0x7a4a4a },
  mesa_quimica:   { shape: 'box', h: 0.7,  color: 0x4a7a6a },
  arvore:         { shape: 'cyl', h: 1.8,  color: 0x2e7d32 },
  arvore_grande:  { shape: 'cyl', h: 2.6,  color: 0x1b5e20 },
};

// ── Hi-DPI helper — call at start of every renderMap / dice frame ──
function applyDPR(canvas, cssW, cssH){
  const dpr=window.devicePixelRatio||1;
  const pw=Math.round(cssW*dpr), ph=Math.round(cssH*dpr);
  if(canvas.width!==pw||canvas.height!==ph){
    canvas.width=pw; canvas.height=ph;
    canvas.style.width=cssW+'px'; canvas.style.height=cssH+'px';
  }
  canvas.getContext('2d').setTransform(dpr,0,0,dpr,0,0);
  return dpr;
}

// ── Thin send wrapper so existing call sites need no change ────────────────
function send(obj){ GS.send(obj); }

function $(id){ return document.getElementById(id); }

function showScreen(id){
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  $(id).classList.add('active');
  if (typeof _menuMusicOnScreen === 'function') _menuMusicOnScreen(id);
}

function toast(msg, color='var(--red)'){
  const t=$('toast'); t.textContent=msg; t.style.background=color;
  t.style.display='block';
  clearTimeout(t._t); t._t=setTimeout(()=>t.style.display='none',3000);
}

function formatGMText(text){
  return text
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>');
}

function getName(){
  const n=$('input-name').value.trim();
  if(!n){ toast('Digite um nome de herói.'); return null; }
  return n;
}

// Endereço do servidor inferido de ONDE a página foi aberta:
//  • localhost / arquivo local → servidor local na porta 8765 (host jogando no PC)
//  • domínio real (túnel https) → MESMO domínio via wss (amigos pelo link único).
// Assim ninguém precisa digitar endereço: o cliente fala com quem o serviu.
function defaultServerUrl(){
  const loc = window.location;
  const host = loc.hostname;
  if(loc.protocol==='file:' || !host || host==='localhost' || host==='127.0.0.1'){
    return 'ws://localhost:8765';
  }
  return (loc.protocol==='https:' ? 'wss:' : 'ws:') + '//' + loc.host;
}
// Página aberta via link de túnel (domínio real) → amigo entrando: o endereço é
// automático, então esconde o campo de servidor e a dica de iniciar.bat (do host).
function serverIsAutoDetected(){
  const h = window.location.hostname;
  return !!h && h!=='localhost' && h!=='127.0.0.1' && window.location.protocol!=='file:';
}

function createRoom(){
  const name=getName(); if(!name) return;
  const url=$('input-server').value.trim()||defaultServerUrl();
  GS.connect(url, name, 'create');
}

// Reconexão manual a partir da sessão salva (botão da tela inicial).
function rejoinSaved(){
  if(!GS.rejoin()){
    toast('Nenhuma partida salva para reconectar.', 'var(--orange)');
    const b=$('btn-rejoin'); if(b) b.style.display='none';
  }
}

// Pré-preenche o endereço do servidor com o detectado automaticamente. Para
// amigos entrando pelo link do túnel, esconde o campo de endereço e a dica de
// iniciar.bat (instruções só fazem sentido para o host na própria máquina).
(function(){
  const si = $('input-server');
  if(si) si.value = defaultServerUrl();
  if(serverIsAutoDetected()){
    const fs = $('field-server'); if(fs) fs.style.display = 'none';
    const hh = $('hint-host');    if(hh) hh.style.display = 'none';
  }
})();

// Mostra o botão de reconexão na tela inicial quando há sessão salva e
// pré-preenche o nome do herói da última partida.
(function(){
  const s = GS.savedSession && GS.savedSession();
  if(!s || !s.code) return;
  const b = $('btn-rejoin');
  if(b){
    b.style.display = 'block';
    b.textContent = `🔌 Reconectar à sala ${s.code} como ${s.name}`;
  }
  const ni = $('input-name');
  if(ni && !ni.value) ni.value = s.name;
  const si = $('input-server');
  if(si && s.url) si.value = s.url;
})();

function joinRoom(){
  const name=getName(); if(!name) return;
  const code=$('input-code').value.trim().toUpperCase();
  if(code.length!==4){ toast('Código deve ter 4 letras.'); return; }
  const url=$('input-server').value.trim()||defaultServerUrl();
  GS.connect(url, name, 'join', code);
}

function copyCode(){
  const code=($('cs-room-code')||{}).textContent||'';
  navigator.clipboard.writeText(code).then(()=>toast('Código copiado!','var(--green)'));
}

// ── MESSAGE HANDLER (delegated to GS — callbacks registered at bottom) ────

function handleLobby(msg){
  // GS._handle já atualizou GS.lobbyState e GS.myPid antes deste callback.
  // Tudo é exibido na tela de seleção full-screen (csf); o lobby antigo foi removido.
  showScreen('screen-class-select');
  csUpdateLobbyBar(msg);
  if(!csf && window.THREE) initClassSelectFull();
  if(csf){
    csf.selectedId = msg.players.find(p=>p.id===GS.myPid)?.class_id ?? csf.selectedId;
    // Classes escolhidas por OUTROS jogadores ficam indisponíveis.
    csf.takenIds = new Set(
      msg.players.filter(p => p.id !== GS.myPid && p.class_id).map(p => p.class_id));
    _csfApplyTaken();
  }
}

// Aplica o visual de "indisponível" (esmaecido) aos heróis já escolhidos por
// outros jogadores; restaura a opacidade original dos disponíveis.
function _csfApplyTaken(){
  if(!csf) return;
  for(const [id, pg] of Object.entries(csf.heroGroups)){
    const taken = csf.takenIds.has(id);
    pg.traverse(o => {
      if(!o.isMesh || !o.material) return;
      const m = o.material;
      if(m.userData._origOpacity === undefined){
        m.userData._origOpacity     = m.opacity;
        m.userData._origTransparent = m.transparent;
      }
      if(taken){ m.transparent = true; m.opacity = 0.16; }
      else     { m.transparent = m.userData._origTransparent; m.opacity = m.userData._origOpacity; }
    });
  }
}

function startGame(){ send({type:'start_game'}); }

// ■  CITY SCREEN — Three.js 3D isometric hub

// 'image' = cidade ilustrada com hotspots (padrão). '3d' = cena Three.js antiga (fallback).
const CITY_MODE = 'image';
let _cityImg = null;   // estado do overlay de imagem (espelha _city3)
let _city3 = null;
let _cityTOD = 0.78; // time-of-day: 0=midnight, 0.25=dawn, 0.5=noon, 0.75=dusk

const _CTY_BLDGS = [
  {id:'taverna',  name:'Taverna',            emoji:'🍺',action:'Comer e beber — recuperar fome e sede',
   x:-5.5,z:-4,  w:3.2,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x7a3a10,roofHex:0x4a2208,winHex:0xffcc44,
   hx:32, hy:46, hero:false},
  {id:'templo',   name:'Templo',             emoji:'⛪',action:'Bênçãos e curas divinas',
   x:0,  z:-7.5, w:4.0,d:3.2,wallH:3.0,roofH:2.2, wallHex:0x283088,roofHex:0x181858,winHex:0x88aaff,
   hx:67, hy:35, hero:true},
  {id:'ferreiro', name:'Ferraria',           emoji:'⚒',action:'Comprar equipamentos',
   x:5.5,z:-4,   w:3.2,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x5a2810,roofHex:0x3a1808,winHex:0xff8822,
   hx:83, hy:38, hero:false},
  {id:'guilda',   name:'Guilda dos Heróis',  emoji:'⚔',action:'Comprar especializações e técnicas',
   x:-5.5,z:2,   w:3.0,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x5a4a10,roofHex:0x3a3008,winHex:0xffee88,
   hx:52, hy:21, hero:false},
  {id:'mercador', name:'Mercado',            emoji:'🛒',action:'Itens e poções',
   x:5.5,z:2,    w:3.0,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x205a20,roofHex:0x103815,winHex:0x88ff88,
   hx:50, hy:40, hero:true},
  {id:'dungeon',  name:'Portão da Masmorra', emoji:'💀',action:'Entrar na masmorra!',
   x:0,  z:8,    w:3.4,d:1.8,wallH:3.6,roofH:0,   wallHex:0x1a1428,roofHex:0x000000,winHex:0xff2020,isDungeon:true,
   hx:23, hy:84, hero:true},
];

function initCity3D(){
  if(_city3) return;
  if(!window.THREE) return;
  const T = window.THREE;

  const canvas = document.getElementById('city-3d-canvas');
  if(!canvas) return;
  const W = canvas.offsetWidth  || window.innerWidth;
  const H = canvas.offsetHeight || window.innerHeight;

  const renderer = new T.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(W, H);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFShadowMap   /* PCF simples: ~igual visualmente, bem mais barato que PCFSoft */;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  const scene = new T.Scene();
  scene.background = new T.Color(0x0a0818);
  scene.fog = new T.FogExp2(0x080612, 0.015);

  // ── Camera: isometric 45° orthographic ──
  const aspect = W / H;
  const fV     = _cityFitFV(aspect);   // enquadra a cidade inteira (telas estreitas dão zoom-out)
  const cam = new T.OrthographicCamera(-fV*aspect, fV*aspect, fV, -fV, 0.1, 200);
  cam.position.set(18, 18, 18);
  cam.lookAt(0, 0, 0);
  cam.updateProjectionMatrix();

  const ambient = new T.AmbientLight(0x20182a, 0.22);
  scene.add(ambient);

  const sun = new T.DirectionalLight(0xffdd99, 0.95);
  sun.position.set(10, 16, 8);
  sun.castShadow = true;
  sun.shadow.mapSize.width = sun.shadow.mapSize.height = 2048;
  const sc = sun.shadow.camera;
  sc.left=-22; sc.right=22; sc.top=22; sc.bottom=-22; sc.far=100;
  sun.shadow.bias = -0.0008;
  scene.add(sun);

  const moon = new T.DirectionalLight(0x5070c8, 0.30);
  moon.position.set(-7, 12, -5); scene.add(moon);

  // ── Ground (cobblestone canvas texture) ──
  const cobbleTex = _cityMakeCobbleTex(T, 512);
  const ground = new T.Mesh(
    new T.PlaneGeometry(40, 40),
    new T.MeshStandardMaterial({map:cobbleTex, roughness:0.94, metalness:0.02})
  );
  ground.rotation.x = -Math.PI/2; ground.receiveShadow = true; scene.add(ground);

  // Street (lighter plaza strip)
  const streetTex = _cityMakeCobbleTex(T, 256, true);
  for(const [sw,sd,sx,sz] of [[14,3,0,-1],[3,18,0,0]]){
    const str = new T.Mesh(new T.PlaneGeometry(sw,sd),
      new T.MeshStandardMaterial({map:streetTex, roughness:0.90, metalness:0.02}));
    str.rotation.x=-Math.PI/2; str.position.set(sx,0.003,sz);
    str.receiveShadow=true; scene.add(str);
  }

  // ── Buildings ──
  const bldgGroups = {}, bldgPickMeshes = [];
  for(const bd of _CTY_BLDGS){
    const bg = _cityBuildBldg(T, bd);
    scene.add(bg);
    bldgGroups[bd.id] = bg;
    // Collect pickable wall meshes
    bg.traverse(c=>{ if(c.isMesh && !c.userData.noRay) bldgPickMeshes.push(c); });
  }

  // ── Street lamps ──
  const lamps = [];
  const lampPos = [[-3.5,0,-2],[3.5,0,-2],[-3.5,0,2.5],[3.5,0,2.5],[-6.5,0,-1],[6.5,0,-1]];
  for(const [lx,ly,lz] of lampPos){
    const lmp = _cityBuildLamp(T);
    lmp.group.position.set(lx,ly,lz); scene.add(lmp.group); lamps.push(lmp);
  }

  const treePos = [[-9,0,-7],[-9,0,0],[-9,0,5],[9,0,-7],[9,0,0],[9,0,5],
                    [-2.5,0,6.5],[2.5,0,6.5],[0,0,-11],[-4.5,0,-10],[4.5,0,-10]];
  for(const [tx,ty,tz] of treePos){ const tr=_cityBuildTree(T); tr.position.set(tx,ty,tz); scene.add(tr); }

  // ── Well/fountain at center ──
  scene.add(_cityBuildWell(T));

  const npcWP = [[-3,0,1],[0,0,3.5],[3,0,1],[3,0,-1.5],[0,0,-4],[-3,0,-1.5]];
  const npcs  = [];
  const npcC  = [0xcc8844, 0x8888cc, 0x44cc88, 0xcc4488, 0xcccc44];
  for(let i=0;i<5;i++){
    const npc = _cityBuildNPC(T, npcC[i%npcC.length]);
    npc.userData.wpIdx = i % npcWP.length;
    npc.userData.wpT   = i / 5;
    npc.userData.npcSpd = 0.65 + Math.random()*0.35;
    const wp = npcWP[npc.userData.wpIdx];
    npc.position.set(wp[0], 0, wp[2]);
    scene.add(npc); npcs.push(npc);
  }

  // ── Portal pulsing point light ──
  const portalLight = new T.PointLight(0xff1020, 1.0, 9);
  portalLight.position.set(0, 1.8, 8); scene.add(portalLight);

  _city3 = {
    T, scene, renderer, cam,
    ambient, sun, moon,
    bldgGroups, bldgPickMeshes,
    lamps, npcs, npcWP,
    portalLight,
    raycaster: new T.Raycaster(),
    hoveredId: null,
    animFrame: null,
    fV, aspect,
    zoomTween: null,
  };

  renderer.domElement.addEventListener('mousemove',  _cityMouseMove);
  renderer.domElement.addEventListener('click',      _cityClick);
  renderer.domElement.addEventListener('mouseleave', ()=>{ if(_city3){_city3.hoveredId=null; _cityHideTooltip(); }});

  // Toque: enquadramento já mostra tudo; um toque curto entra no prédio.
  let _ctx0, _cty0, _ctMoved;
  renderer.domElement.addEventListener('touchstart', e=>{
    if(e.touches.length===1){ _ctx0=e.touches[0].clientX; _cty0=e.touches[0].clientY; _ctMoved=0; } else { _ctMoved=999; }
  }, { passive:true });
  renderer.domElement.addEventListener('touchmove', e=>{
    if(e.touches.length===1) _ctMoved+=Math.abs(e.touches[0].clientX-_ctx0)+Math.abs(e.touches[0].clientY-_cty0);
  }, { passive:true });
  renderer.domElement.addEventListener('touchend', (e)=>{
    if(_ctMoved<14){ e.preventDefault(); _cityClick({ clientX:_ctx0, clientY:_cty0 }); }
  }, { passive:false });

  window.addEventListener('resize', _cityOnResize);

  _startCity3Loop();
  _updateCityTimeBadge();
  // Corrige o enquadramento depois que o layout assenta (canvas pode iniciar 0px).
  requestAnimationFrame(()=>{ if(_city3) _cityOnResize(); });
}

// Meia-altura do frustum que enquadra a cidade inteira. Em telas estreitas
// (aspect pequeno) aumenta para caber a largura; no desktop fica em 11 (igual).
function _cityFitFV(aspect){
  return Math.max(11, 10.5 / Math.max(aspect, 0.0001));
}
// Reajusta a câmera/renderer da cidade quando a tela muda (rotação/redimensão).
function _cityOnResize(){
  if(!_city3){ window.removeEventListener('resize', _cityOnResize); return; }
  const cv = document.getElementById('city-3d-canvas'); if(!cv) return;
  const W = cv.clientWidth || window.innerWidth, H = cv.clientHeight || window.innerHeight;
  const aspect = W / H, fV = _cityFitFV(aspect);
  _city3.renderer.setSize(W, H, false);
  _city3.aspect = aspect; _city3.fV = fV;
  const cam = _city3.cam;
  cam.left = -fV*aspect; cam.right = fV*aspect; cam.top = fV; cam.bottom = -fV;
  cam.updateProjectionMatrix();
}

function _cityMakeCobbleTex(T, sz, light=false){
  const cv=document.createElement('canvas'); cv.width=cv.height=sz;
  const c=cv.getContext('2d');
  const base = light ? 36 : 28;
  const CS=Math.round(sz/16);
  for(let gy=0;gy<sz;gy+=CS){
    const rowOff=((gy/CS|0)%2)*(CS/2);
    for(let gx=-CS+rowOff;gx<sz;gx+=CS){
      const v=base+((gx*7+gy*13)&0xff)%14; const bv=light?2:0;
      c.fillStyle=`rgb(${v},${v-bv},${v+3})`; c.fillRect(gx+1,gy+1,CS-2,CS-2);
    }
  }
  c.strokeStyle=`rgba(6,4,10,${light?0.45:0.65})`; c.lineWidth=1;
  for(let gy=0;gy<sz;gy+=CS){
    const rowOff=((gy/CS|0)%2)*(CS/2);
    c.beginPath(); c.moveTo(0,gy); c.lineTo(sz,gy); c.stroke();
    for(let gx=-CS+rowOff;gx<sz;gx+=CS){ c.beginPath(); c.moveTo(gx,gy); c.lineTo(gx,gy+CS); c.stroke(); }
  }
  const tex=new T.CanvasTexture(cv);
  tex.wrapS=tex.wrapT=T.RepeatWrapping; tex.repeat.set(6,6); return tex;
}

function _cityMakeWallTex(T, hex){
  const cv=document.createElement('canvas'); cv.width=cv.height=256;
  const c=cv.getContext('2d');
  const r=(hex>>16)&0xff, g=(hex>>8)&0xff, b=hex&0xff;
  c.fillStyle=`rgb(${r},${g},${b})`; c.fillRect(0,0,256,256);
  const bH=22, bW=46;
  for(let by=0;by<256;by+=bH){
    const rowOff=((by/bH|0)%2)*(bW/2);
    for(let bx=-bW+rowOff;bx<256;bx+=bW){
      const dr=Math.round((Math.random()-0.5)*20);
      c.fillStyle=`rgb(${Math.min(255,Math.max(0,r+dr))},${Math.min(255,Math.max(0,g+dr))},${Math.min(255,Math.max(0,b+dr))})`;
      c.fillRect(bx+1,by+1,bW-2,bH-2);
    }
  }
  c.strokeStyle='rgba(0,0,0,0.55)'; c.lineWidth=2;
  for(let by=0;by<256;by+=bH){
    const ro=((by/bH|0)%2)*(bW/2);
    c.beginPath(); c.moveTo(0,by); c.lineTo(256,by); c.stroke();
    for(let bx=-bW+ro;bx<256;bx+=bW){ c.beginPath(); c.moveTo(bx,by); c.lineTo(bx,by+bH); c.stroke(); }
  }
  return new T.CanvasTexture(cv);
}

function _cityBuildBldg(T, bd){
  const {id,wallHex,roofHex,winHex,x,z,w,d,wallH,roofH,isDungeon} = bd;
  const pg = new T.Group();
  pg.userData.bldgId = id;
  pg.position.set(x, 0, z);

  const wallTex = _cityMakeWallTex(T, wallHex);
  const wallMat = new T.MeshStandardMaterial({map:wallTex, roughness:0.88, metalness:0.08});
  const walls = new T.Mesh(new T.BoxGeometry(w, wallH, d), wallMat);
  walls.position.y = wallH/2;
  walls.castShadow = walls.receiveShadow = true;
  walls.userData.bldgId = id;  // for raycasting
  pg.add(walls);

  if(!isDungeon && roofH>0){
    const rR = Math.hypot(w,d)*0.5;
    const roof = new T.Mesh(
      new T.ConeGeometry(rR*0.72, roofH, 4),
      new T.MeshStandardMaterial({color:new T.Color(roofHex), roughness:0.92, metalness:0.06})
    );
    roof.rotation.y = Math.PI/4; roof.position.y = wallH+roofH/2;
    roof.castShadow = true; roof.userData.noRay=true; pg.add(roof);
  }

  if(isDungeon){
    // Gothic arch opening
    const stoneMat = new T.MeshStandardMaterial({color:new T.Color(wallHex), roughness:0.95, metalness:0.12});
    const darkMat  = new T.MeshStandardMaterial({color:0x040208, emissive:new T.Color(0x440068), emissiveIntensity:0.7, roughness:0.5});
    const aW=w*0.52, aH=wallH*0.78;
    // Dark hollow
    const hollow=new T.Mesh(new T.BoxGeometry(aW,aH,d+0.12),darkMat);
    hollow.position.y=aH/2; hollow.userData.noRay=true; pg.add(hollow);
    // Arch lintel
    const lintel=new T.Mesh(new T.BoxGeometry(aW+0.45,0.38,d+0.12),stoneMat);
    lintel.position.y=aH+0.19; lintel.userData.noRay=true; pg.add(lintel);
    // Side pillars
    for(const sx of [-(aW/2+0.22), aW/2+0.22]){
      const pil=new T.Mesh(new T.BoxGeometry(0.38,aH+0.38,d+0.12),stoneMat);
      pil.position.set(sx,aH*0.5,0); pil.userData.noRay=true; pg.add(pil);
    }
    // Steps in front
    [[w+0.4,0.14,0.4],[w+0.7,0.08,0.6]].forEach(([sw,sh,sd],i)=>{
      const step=new T.Mesh(new T.BoxGeometry(sw,sh,sd),stoneMat);
      step.position.set(0,sh/2,d/2+0.4+i*0.25); step.castShadow=true; step.receiveShadow=true; step.userData.noRay=true; pg.add(step);
    });
    // Skull emblem
    const skullMat = new T.MeshStandardMaterial({color:0xddddcc, emissive:0x332222, emissiveIntensity:0.3, roughness:0.7});
    const skull = new T.Mesh(new T.SphereGeometry(0.18,7,5), skullMat);
    skull.position.set(0, aH+0.72, d/2+0.05); skull.userData.noRay=true; pg.add(skull);
  } else {
    // Door
    const doorMat = new T.MeshStandardMaterial({color:0x100800, roughness:0.95});
    const door=new T.Mesh(new T.BoxGeometry(0.65,1.2,0.07),doorMat);
    door.position.set(0,0.6,d/2+0.03); door.userData.noRay=true; pg.add(door);
    // Windows
    const winMat = new T.MeshStandardMaterial({color:new T.Color(winHex), emissive:new T.Color(winHex), emissiveIntensity:0.55, roughness:0.3});
    for(const wx of [-w*0.25, w*0.25]){
      const win=new T.Mesh(new T.BoxGeometry(0.46,0.58,0.07),winMat);
      win.position.set(wx,wallH*0.62,d/2+0.03); win.userData.noRay=true; win.userData.isWindow=true; pg.add(win);
    }
    // Window point light (off at day)
    const wl=new T.PointLight(new T.Color(winHex), 0, 3.2);
    wl.position.set(0,wallH*0.62,d/2+0.5); wl.userData.isWinLight=true; pg.add(wl);
    // Torch flame + light
    const torchMat=new T.MeshStandardMaterial({color:0xffdd40,emissive:0xff8010,emissiveIntensity:2.0,roughness:0.5});
    const flame=new T.Mesh(new T.SphereGeometry(0.09,5,4),torchMat);
    flame.position.set(w*0.38,wallH*0.52,d/2+0.18); flame.userData.noRay=true; pg.add(flame);
    const tl=new T.PointLight(0xff9920,0,3.0);
    tl.position.set(w*0.38,wallH*0.52,d/2+0.38); tl.userData.isTorchLight=true; pg.add(tl);
  }

  return pg;
}

function _cityBuildLamp(T){
  const grp=new T.Group();
  const met=new T.MeshStandardMaterial({color:0x383040,roughness:0.65,metalness:0.70});
  const pole=new T.Mesh(new T.CylinderGeometry(0.042,0.058,2.3,7),met);
  pole.position.y=1.15; pole.castShadow=true; pole.userData.noRay=true; grp.add(pole);
  const arm=new T.Mesh(new T.CylinderGeometry(0.026,0.026,0.75,7),met);
  arm.rotation.z=Math.PI/2; arm.position.set(0.375,2.15,0); arm.userData.noRay=true; grp.add(arm);
  const head=new T.Mesh(new T.BoxGeometry(0.22,0.20,0.22),met);
  head.position.set(0.75,2.16,0); head.userData.noRay=true; grp.add(head);
  const bulbMat=new T.MeshStandardMaterial({color:0xffee88,emissive:new T.Color(0xffcc40),emissiveIntensity:2.5,roughness:0.3});
  const bulb=new T.Mesh(new T.SphereGeometry(0.075,6,6),bulbMat);
  bulb.position.set(0.75,2.14,0); bulb.userData.noRay=true; grp.add(bulb);
  const base=new T.Mesh(new T.CylinderGeometry(0.13,0.16,0.13,7),met);
  base.position.y=0.065; base.userData.noRay=true; grp.add(base);
  const light=new T.PointLight(0xffcc44, 0, 5.8); // intensity driven by day/night
  light.position.set(0.75,2.05,0); grp.add(light);
  return {group:grp, light, bulbMat};
}

function _cityBuildTree(T){
  const grp=new T.Group();
  const tH=1.2+Math.random()*0.9, lR=0.95+Math.random()*0.45;
  const trunkMat=new T.MeshStandardMaterial({color:0x3a2510,roughness:0.95,metalness:0.0});
  const leavesMat=new T.MeshStandardMaterial({color:0x1a4010,roughness:0.88,metalness:0.0});
  const leavesDark=new T.MeshStandardMaterial({color:0x0e2a08,roughness:0.88,metalness:0.0});
  const trunk=new T.Mesh(new T.CylinderGeometry(0.12,0.18,tH,6),trunkMat);
  trunk.position.y=tH/2; trunk.castShadow=true; trunk.userData.noRay=true; grp.add(trunk);
  const leaves=new T.Mesh(new T.SphereGeometry(lR,8,5),leavesMat);
  leaves.position.y=tH+lR*0.65; leaves.castShadow=true; leaves.userData.noRay=true; grp.add(leaves);
  const inner=new T.Mesh(new T.SphereGeometry(lR*0.62,6,4),leavesDark);
  inner.position.y=tH+lR*0.5; inner.userData.noRay=true; grp.add(inner);
  return grp;
}

function _cityBuildWell(T){
  const grp=new T.Group();
  const ston=new T.MeshStandardMaterial({color:0x2a2438,roughness:0.92,metalness:0.10});
  const watr=new T.MeshStandardMaterial({color:0x2040a0,roughness:0.10,metalness:0.60,transparent:true,opacity:0.85});
  const wood=new T.MeshStandardMaterial({color:0x4a2810,roughness:0.95,metalness:0.0});
  const basin=new T.Mesh(new T.CylinderGeometry(0.90,0.78,0.30,12),ston);
  basin.position.y=0.15; basin.receiveShadow=true; grp.add(basin);
  const water=new T.Mesh(new T.CircleGeometry(0.74,12),watr);
  water.rotation.x=-Math.PI/2; water.position.y=0.29; water.userData.noRay=true; grp.add(water);
  for(const px of [-0.70,0.70]){
    const post=new T.Mesh(new T.CylinderGeometry(0.056,0.056,1.1,7),wood);
    post.position.set(px,0.55,0); post.castShadow=true; grp.add(post);
  }
  const beam=new T.Mesh(new T.BoxGeometry(1.5,0.09,0.09),wood);
  beam.position.y=1.1; beam.castShadow=true; grp.add(beam);
  return grp;
}

function _cityBuildNPC(T, hexColor){
  const grp=new T.Group();
  const bodyMat=new T.MeshStandardMaterial({color:new T.Color(hexColor),roughness:0.9,metalness:0.0});
  const headMat=new T.MeshStandardMaterial({color:0xc89860,roughness:0.85,metalness:0.0});
  const body=new T.Mesh(new T.CylinderGeometry(0.14,0.16,0.52,8),bodyMat);
  body.position.y=0.46; body.castShadow=true; body.userData.noRay=true; grp.add(body);
  const head=new T.Mesh(new T.SphereGeometry(0.15,8,6),headMat);
  head.position.y=0.88; head.castShadow=true; head.userData.noRay=true; grp.add(head);
  return grp;
}

function _startCity3Loop(){
  let _last=Date.now();
  function tick(){
    if(!_city3) return;
    _city3.animFrame=requestAnimationFrame(tick);
    const now=Date.now(), dt=Math.min((now-_last)*0.001,0.05); _last=now;
    const t=now*0.001;
    const {T,scene,renderer,cam,ambient,sun,moon,bldgGroups,lamps,npcs,npcWP,portalLight,zoomTween}=_city3;

    // ── Day/night cycle ──
    _cityTOD=(_cityTOD+dt*0.008)%1.0; // full cycle ≈ 125 s
    const dayF=Math.max(0,Math.sin(_cityTOD*Math.PI));

    const nightAmb=new T.Color(0x12103a), dayAmb=new T.Color(0x908898);
    ambient.color.lerpColors(nightAmb,dayAmb,dayF);
    ambient.intensity=0.12+dayF*0.30;
    sun.intensity=dayF*0.98; moon.intensity=(1-dayF)*0.32;
    const nightSky=new T.Color(0x08060f), daySky=new T.Color(0x3a5890);
    scene.background.lerpColors(nightSky,daySky,dayF*dayF);
    const nightFog=new T.Color(0x060410), dayFog=new T.Color(0x283060);
    scene.fog.color.lerpColors(nightFog,dayFog,dayF);

    const lampInt=(1-dayF)*(0.75+0.15*Math.sin(t*2.8));
    for(const lmp of lamps){
      lmp.light.intensity=lampInt*1.1;
      lmp.bulbMat.emissiveIntensity=lampInt>0.05?2.5:0.4;
    }

    for(const bg of Object.values(bldgGroups)){
      bg.traverse(c=>{
        if(c.userData.isWinLight)   c.intensity=lampInt*0.55;
        if(c.userData.isTorchLight) c.intensity=lampInt*0.65*(0.8+0.2*Math.sin(t*4.8+c.position.x));
      });
    }

    // ── Portal pulsing ──
    portalLight.intensity=0.7+0.7*Math.sin(t*1.9);

    // ── Building hover lift ──
    for(const [id,bg] of Object.entries(bldgGroups)){
      const targetY=id===_city3.hoveredId ? 0.09 : 0;
      bg.position.y+=(targetY-bg.position.y)*0.12;
    }

    // ── NPC movement ──
    for(const npc of npcs){
      const {wpIdx,wpT,npcSpd}=npc.userData;
      const from=npcWP[wpIdx], to=npcWP[(wpIdx+1)%npcWP.length];
      const dist=Math.hypot(to[0]-from[0],to[2]-from[2]);
      let newT=wpT+dt*npcSpd/(dist||1);
      if(newT>=1){ newT=0; npc.userData.wpIdx=(wpIdx+1)%npcWP.length; }
      npc.userData.wpT=newT;
      npc.position.x=from[0]+(to[0]-from[0])*newT;
      npc.position.z=from[2]+(to[2]-from[2])*newT;
      const dx=to[0]-from[0],dz=to[2]-from[2];
      if(Math.abs(dx)+Math.abs(dz)>0.01) npc.rotation.y=Math.atan2(dx,dz);
    }

    // ── Zoom tween (dungeon entrance) ──
    if(_city3.zoomTween){
      const zt=_city3.zoomTween;
      zt.elapsed=(zt.elapsed||0)+dt;
      const p=Math.min(zt.elapsed/zt.duration,1);
      const e=p*p*(3-2*p); // smoothstep
      const newFV=zt.startFV+(zt.endFV-zt.startFV)*e;
      const a=_city3.aspect;
      cam.left=-newFV*a; cam.right=newFV*a; cam.top=newFV; cam.bottom=-newFV;
      cam.position.x+=(zt.tx-cam.position.x)*0.06;
      cam.position.z+=(zt.tz-cam.position.z)*0.06;
      cam.lookAt(0,1.5,8);
      cam.updateProjectionMatrix();
      if(p>=1 && zt.onDone){ const cb=zt.onDone; _city3.zoomTween=null; cb(); }
    }

    // ── Time badge ──
    if(Math.floor(t)%3===0 && Math.floor(t*10)%10===0) _updateCityTimeBadge();

    renderer.render(scene,cam);
  }
  tick();
}

function _cityPickBldg(e){
  if(!_city3) return null;
  const {raycaster,cam,bldgPickMeshes,renderer,T}=_city3;
  const rc=renderer.domElement.getBoundingClientRect();
  const mx=((e.clientX-rc.left)/rc.width)*2-1;
  const my=((e.clientY-rc.top)/rc.height)*-2+1;
  raycaster.setFromCamera(new T.Vector2(mx,my),cam);
  const hits=raycaster.intersectObjects(bldgPickMeshes,false);
  return hits.length ? hits[0].object.userData.bldgId??null : null;
}
function _cityMouseMove(e){
  if(!_city3) return;
  const id=_cityPickBldg(e);
  if(id!==_city3.hoveredId){
    _city3.hoveredId=id;
    _city3.renderer.domElement.style.cursor=id?'pointer':'default';
    if(id) _cityShowTooltip(id,e); else _cityHideTooltip();
  } else if(id) _cityMoveTooltip(e);
}
// Mapeamento de ids do raycaster (meshes 3D) → ids das lojas (abrirLoja).
// Corrige a divergência mercador→mercado sem alterar os ids dos meshes 3D.
const MAPA_IDS_LOJA = {
  ferreiro: 'ferreiro',
  taverna:  'taverna',
  mercador: 'mercado'   // corrige a divergência
};

function _cityClick(e){
  if(!_city3) return;
  const id=_cityPickBldg(e);
  if(!id) return;
  if(id==='dungeon') triggerDungeonEntrance();
  else if(id==='guilda') toast('⚔ Guilda dos Heróis — Missões em breve!','var(--gold)');
  else openShop(id);
}

function _cityShowTooltip(id,e){
  const bd=_CTY_BLDGS.find(b=>b.id===id); if(!bd) return;
  const tip=document.getElementById('city-bldg-tooltip'); if(!tip) return;
  const isDng=id==='dungeon';
  tip.innerHTML=`<h4>${bd.emoji} ${bd.name}</h4>`+
    `<p class="tip-action">${bd.action}</p>`+
    `<p class="tip-click">${isDng?'▶ CLIQUE PARA ENTRAR':'▶ CLIQUE PARA ABRIR'}</p>`;
  tip.style.display='block';
  tip.style.borderColor=isDng?'rgba(255,50,50,.7)':'rgba(var(--gold-rgb),.5)';
  _cityMoveTooltip(e);
}
function _cityMoveTooltip(e){
  const tip=document.getElementById('city-bldg-tooltip'); if(!tip||tip.style.display==='none') return;
  const tw=tip.offsetWidth||200, th=tip.offsetHeight||80;
  tip.style.left=Math.min(e.clientX+18,window.innerWidth-tw-8)+'px';
  tip.style.top=Math.max(0,Math.min(e.clientY-10,window.innerHeight-th-8))+'px';
}
function _cityHideTooltip(){
  const tip=document.getElementById('city-bldg-tooltip'); if(tip) tip.style.display='none';
}

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

function _updateCityTimeBadge(){
  const b=document.getElementById('city-time-badge'); if(!b) return;
  const tod=_cityTOD;
  b.textContent=tod<0.15||tod>0.88?'🌙 Noite profunda':
                tod<0.30?'🌅 Amanhecer':
                tod<0.55?'☀ Pleno dia':
                tod<0.70?'🌇 Entardecer':'🌆 Anoitecer';
}

function triggerDungeonEntrance(){
  if(!GS.ws||GS.ws.readyState!==1){
    toast('❌ Sem conexão com o servidor. Reinicie o iniciar.bat.','var(--red)'); return;
  }
  getAudioContext();
  // Web Audio: heavy gate sound
  try{
    const actx=getAudioContext();
    if(actx){
      const now=actx.currentTime;
      // Sawtooth gate creak: 80hz → 40hz
      const osc=actx.createOscillator(), g=actx.createGain();
      osc.type='sawtooth';
      osc.frequency.setValueAtTime(80,now);
      osc.frequency.linearRampToValueAtTime(40,now+1.0);
      g.gain.setValueAtTime(0.4,now); g.gain.linearRampToValueAtTime(0,now+1.3);
      osc.connect(g); g.connect(_sfxBus());
      osc.start(now); osc.stop(now+1.3);
      // Low rumble
      const osc2=actx.createOscillator(), g2=actx.createGain();
      osc2.type='sine'; osc2.frequency.value=38;
      g2.gain.setValueAtTime(0.28,now); g2.gain.linearRampToValueAtTime(0,now+1.6);
      osc2.connect(g2); g2.connect(_sfxBus());
      osc2.start(now); osc2.stop(now+1.6);
    }
  }catch(ex){}

  // Fade overlay
  let fo=document.getElementById('city-fade-overlay');
  if(!fo){ fo=document.createElement('div'); fo.id='city-fade-overlay'; fo.className='city-fade-overlay'; document.body.appendChild(fo); }

  // Camera zoom into portal
  if(_city3){
    _city3.zoomTween={startFV:_city3.fV, endFV:_city3.fV*0.3, tx:12,tz:26, duration:1.5, elapsed:0, onDone:null};
  }

  requestAnimationFrame(()=>{
    fo.classList.add('on');
    setTimeout(()=>{ send({type:'enter_dungeon'}); }, 900);
  });
}

function destroyCity3D(){
  if(!_city3) return;
  cancelAnimationFrame(_city3.animFrame);
  _city3.renderer.domElement.removeEventListener('mousemove',_cityMouseMove);
  _city3.renderer.domElement.removeEventListener('click',_cityClick);
  window.removeEventListener('resize', _cityOnResize);
  _city3.renderer.dispose();
  _city3=null;
  _cityHideTooltip();
  const fo=document.getElementById('city-fade-overlay');
  if(fo) fo.remove();
}

// ■  CITY SCREEN (modo imagem) — overlay em DOM sobre #screen-city

function initCityImage(){
  if(_cityImg) return;
  const host = document.getElementById('screen-city');
  if(!host) return;

  const stage = document.createElement('div');
  stage.id = 'city-stage';

  // Moldura 3:2 que define a caixa renderizada da imagem; imagem, hotspots,
  // vida e selo são posicionados DENTRO dela em % → alinhamento garantido.
  const frame = document.createElement('div');
  frame.id = 'city-frame';
  stage.appendChild(frame);

  const img = document.createElement('img');
  img.id = 'city-img';
  img.src = 'assets/city/alva_e_luz.jpg?v=' + (window.ASSET_VER || '1');
  img.alt = 'Cidade de Alva e Luz';
  img.draggable = false;
  frame.appendChild(img);

  const life = document.createElement('div');
  life.id = 'city-life';
  // Vida sutil: névoa nas bordas + brilhos piscando (tochas/janelas) + pulsar do portão.
  life.innerHTML =
    '<div class="city-fog"></div>' +
    '<div class="city-flicker" style="left:32%;top:46%"></div>' +
    '<div class="city-flicker" style="left:50%;top:40%;animation-delay:.7s"></div>' +
    '<div class="city-flicker" style="left:83%;top:38%;animation-delay:1.1s"></div>' +
    '<div class="city-flicker" style="left:60%;top:55%;animation-delay:.4s"></div>' +
    '<div class="city-gateglow" style="left:23%;top:84%"></div>';
  frame.appendChild(life);

  const hotWrap = document.createElement('div');
  hotWrap.id = 'city-hotspots';
  for(const bd of _CTY_BLDGS){
    if(bd.hx == null) continue;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'city-hotspot' + (bd.hero ? ' hero' : '') + (bd.id==='dungeon' ? ' dungeon' : '');
    btn.style.left = bd.hx + '%';
    btn.style.top  = bd.hy + '%';
    btn.setAttribute('aria-label', bd.name + ' — ' + bd.action);
    btn.title = bd.name + ' — ' + bd.action;
    const label = bd.id==='dungeon' ? 'Ir para a aventura' : bd.name;
    btn.innerHTML =
      '<span class="ch-glow" aria-hidden="true"></span>' +
      '<span class="ch-pin"><span class="ch-emoji">' + bd.emoji + '</span>' +
      '<span class="ch-name">' + label + '</span></span>';
    btn.addEventListener('click', () => _cityHotspotClick(bd.id));
    hotWrap.appendChild(btn);
  }
  frame.appendChild(hotWrap);
  host.appendChild(stage);

  const tb = document.getElementById('city-time-badge');
  if(tb) tb.style.display = 'none';

  _cityImg = { stage, frame, img, life, hotWrap, raf:0 };
}

function _cityHotspotClick(id){
  if(id === 'dungeon'){ triggerDungeonEntrance(); return; }
  if(id === 'guilda'){ openGuild(); return; }
  // openShop espera o id do prédio cru (ex.: 'mercador'); é o que o servidor usa
  // como chave da loja. (NÃO usar MAPA_IDS_LOJA: 'mercado' aponta p/ loja vazia.)
  openShop(id);
}

function destroyCityImage(){
  if(_cityImg){
    if(_cityImg.raf) cancelAnimationFrame(_cityImg.raf);
    if(_cityImg.stage && _cityImg.stage.parentNode) _cityImg.stage.parentNode.removeChild(_cityImg.stage);
    _cityImg = null;
  }
  const tb = document.getElementById('city-time-badge');
  if(tb) tb.style.display = '';
  // Remove o overlay preto de transição (senão fica cobrindo a masmorra — o
  // destroyCity3D fazia isso; o modo imagem precisa fazer o mesmo).
  const fo = document.getElementById('city-fade-overlay');
  if(fo) fo.remove();
}

// ── Fase 4b (história): overlay de história da campanha ───────────────────────
// Slideshow de história (layout A): imagem de fundo + texto sobreposto + áudio
// em loop. Cada cliente navega seus próprios slides; "Continuar" no último marca
// o beat como visto (de-dup por key em gameState.js).
let _storyIdx = 0;
let _storyMuted = false;
let _storyAudioEl = null;

function _storyAudioStop() {
  if (_storyAudioEl) { try { _storyAudioEl.pause(); } catch (e) {} _storyAudioEl.src = ''; _storyAudioEl = null; }
}

function _storyPaintMute() {
  const ov = document.getElementById('story-overlay');
  if (ov) ov.querySelector('#story-mute').textContent = _storyMuted ? '🔇' : '🔊';
}

function _storyPaint() {
  const beat = GS.pendingStory && GS.pendingStory();
  const ov = document.getElementById('story-overlay');
  if (!beat || !ov) return;
  const slide = beat.slides[_storyIdx] || {};
  const img = ov.querySelector('#story-img');
  if (slide.image) {
    img.style.backgroundImage = 'url("' + slide.image + '")';
    img.style.backgroundSize = (slide.fit === 'contain') ? 'contain' : 'cover';
  } else {
    img.style.backgroundImage = 'none';
  }
  const txtEl = ov.querySelector('#story-text');
  txtEl.textContent = slide.text || '';
  txtEl.style.display = slide.text ? 'block' : 'none';
  const dots = ov.querySelector('#story-dots');
  dots.innerHTML = '';
  beat.slides.forEach((_, i) => {
    const d = document.createElement('span');
    d.className = 'story-dot' + (i === _storyIdx ? ' on' : '');
    dots.appendChild(d);
  });
  ov.querySelector('#story-prev').style.visibility = _storyIdx > 0 ? 'visible' : 'hidden';
  ov.querySelector('#story-continue').textContent =
    (_storyIdx < beat.slides.length - 1) ? 'Continuar →' : 'Concluir';
  _storyPaintMute();
}

function renderStory() {
  const beat = GS.pendingStory && GS.pendingStory();
  let ov = document.getElementById('story-overlay');
  if (!beat || !beat.slides || !beat.slides.length) {
    if (ov) ov.style.display = 'none';
    _storyAudioStop();
    return;
  }
  if (!ov) {
    ov = document.createElement('div'); ov.id = 'story-overlay';
    ov.innerHTML =
      '<div id="story-img"></div>'
      + '<div id="story-scrim"></div>'
      + '<button id="story-mute" title="Som">🔊</button>'
      + '<div id="story-box">'
      +   '<div id="story-text"></div>'
      +   '<div id="story-nav">'
      +     '<button id="story-prev">‹ Voltar</button>'
      +     '<div id="story-dots"></div>'
      +     '<button id="story-continue">Continuar →</button>'
      +   '</div>'
      + '</div>';
    document.body.appendChild(ov);
    ov.querySelector('#story-prev').onclick = () => {
      if (_storyIdx > 0) { _storyIdx--; _storyPaint(); }
    };
    ov.querySelector('#story-continue').onclick = () => {
      const b = GS.pendingStory && GS.pendingStory();
      if (!b) return;
      if (_storyIdx < b.slides.length - 1) { _storyIdx++; _storyPaint(); }
      else { GS.marcarStoryVista(b.key); _storyAudioStop(); ov.style.display = 'none'; }
    };
    ov.querySelector('#story-mute').onclick = () => {
      _storyMuted = !_storyMuted;
      if (_storyAudioEl) _storyAudioEl.muted = _storyMuted;
      _storyPaintMute();
    };
  }
  // (Re)inicializa só quando o beat muda — evita resetar o índice/áudio a cada
  // broadcast de game_state (que reenvia a história enquanto ela está aberta).
  if (ov.dataset.key !== beat.key) {
    ov.dataset.key = beat.key;
    _storyIdx = 0;
    beat.slides.forEach(s => { if (s.image) { const im = new Image(); im.src = s.image; } });
    _storyAudioStop();
    if (beat.audio) {
      _storyAudioEl = new Audio(beat.audio);
      _storyAudioEl.loop = true; _storyAudioEl.muted = _storyMuted; _storyAudioEl.volume = 0.6;
      _storyAudioEl.play().catch(() => {});
    }
  }
  ov.style.display = 'block';
  _storyPaint();
}

function handleCityState(msg){
  _updateCityHeroBar(msg);
  // Legacy player bar (used by shop modal gold display)
  const lbar=$('city-players-bar');
  if(lbar) lbar.innerHTML=msg.players.map(p=>{
    const isMe=p.id===GS.myPid;
    return `<div class="city-pcard${isMe?' me':''}">
      <span>${p.emoji}</span><span class="city-pcard-name">${p.name}</span>
      <span style="color:var(--text2);font-size:.75rem;">${p.class_name}</span>
      <span class="city-pcard-gold">💰 ${p.gold}</span></div>`;
  }).join('');
  // Host controls
  const btnD=$('btn-enter-dungeon'), hint=$('city-host-hint');
  const dungBar=$('city-dungeon-bar');
  if(btnD){
    const isHost=GS.myPid&&GS.myPid===msg.host;
    // Em campanha, o botão indica a próxima fase a entrar.
    btnD.textContent = msg.campaign ? `▶ Ir para a aventura — Fase ${msg.campaign.phase}` : '▶ Ir para a aventura';
    btnD.style.display=isHost?'inline-block':'none';
    if(dungBar) dungBar.style.display=isHost?'flex':'none';
    if(hint) hint.textContent=isHost
      ?'Você é o anfitrião — clique no Portão ou aqui para entrar.'
      :'Aguardando o anfitrião iniciar a aventura…';
  }
  // Shop
  if(GS.activeShop) _renderShopItems();
  if(GS.pendingShopOpen){ const s=GS.pendingShopOpen; GS.pendingShopOpen=null; openShop(s); }
  // Monta a cidade conforme o modo (imagem por padrão; 3D como fallback).
  if(CITY_MODE==='image'){ if(!_cityImg) initCityImage(); }
  else if(!_city3&&window.THREE){ initCity3D(); }
  // Clear fade overlay if returning from dungeon
  const fo=document.getElementById('city-fade-overlay');
  if(fo){ fo.classList.remove('on'); setTimeout(()=>{ if(fo.parentNode) fo.remove(); },1200); }
  renderStory();   // Fase 4b: encerramento da fase (mostrado na cidade)
}

// ── Legacy 2D city data (kept so shop modal lookups still find building names) ──
const CITY_DUNGEON = { id: 'dungeon', x: 305, y: 352, w: 90, h: 88 };
const CITY_BUILDINGS = [
  { id:'taverna',  name:'Taverna',  emoji:'🍺', desc:'Comida e bebida (fome/sede)',
    x:40,  y:50,  w:190, h:165, baseColor:'#6b3a10', glowColor:'rgba(220,140,30,0.35)',
    roofColor:'#4a2508', doorColor:'#3d1f06', lightColor:'rgba(255,200,60,0.5)',
    tabs:null },
  { id:'ferreiro', name:'Ferreiro', emoji:'🔨', desc:'Armas e armaduras',
    x:470, y:50,  w:190, h:165, baseColor:'#5a2510', glowColor:'rgba(220,70,20,0.35)',
    roofColor:'#3d1808', doorColor:'#2a1005', lightColor:'rgba(255,130,40,0.5)',
    tabs:['Armas','Armaduras'] },
  { id:'mercador', name:'Mercador', emoji:'🛒', desc:'Poções e acessórios',
    x:40,  y:265, w:190, h:165, baseColor:'#0e4a1a', glowColor:'rgba(30,180,60,0.28)',
    roofColor:'#0a3012', doorColor:'#071e0b', lightColor:'rgba(60,220,90,0.4)',
    tabs:null },
  { id:'templo',   name:'Templo',   emoji:'⛪', desc:'Bênçãos e curas divinas',
    x:470, y:265, w:190, h:165, baseColor:'#1a1a70', glowColor:'rgba(80,80,220,0.32)',
    roofColor:'#10104a', doorColor:'#0a0a30', lightColor:'rgba(120,120,255,0.5)',
    tabs:null },
];

function openShop(shopId){
  if(!GS.cityState){
    // city_state not yet received — request it and retry when it arrives
    GS.pendingShopOpen = shopId;
    send({type:'get_city_state'});
    toast('Carregando loja…', 'var(--blue)');
    return;
  }
  GS.pendingShopOpen = null;
  GS.activeShop=shopId; GS.shopTabIdx=0;
  const modal=$('shop-modal'); if(!modal) return;
  modal.classList.add('open');
  const b=CITY_BUILDINGS.find(b=>b.id===shopId);
  const titles={taverna:'🍺 Taverna',ferreiro:'🔨 Ferreiro',mercador:'🛒 Mercador',templo:'⛪ Templo'};
  $('shop-title').textContent = titles[shopId]||shopId;
  const subtitles={
    taverna:'Descanse, coma e beba antes de partir para a aventura.',
    ferreiro:'Compre e venda armas e armaduras.',
    mercador:'Poções, amuletos e acessórios para sobreviver na masmorra.',
    templo:'Receba bênçãos divinas e cure seus ferimentos.',
  };
  $('shop-subtitle').textContent = subtitles[shopId]||'';
  // Tabs
  const tabsEl=$('shop-tabs'); tabsEl.innerHTML='';
  const tabDefs = shopId==='ferreiro'
    ? ['⚔ Armas','🛡 Armaduras','💰 Vender']
    : shopId==='mercador'
    ? ['🛒 Comprar','💰 Vender']
    : [];
  tabDefs.forEach((t,i)=>{
    const btn=document.createElement('button');
    btn.className='shop-tab'+(i===GS.shopTabIdx?' active':'');
    btn.textContent=t;
    btn.onclick=()=>{ GS.shopTabIdx=i; _updateShopTabs(); _renderShopItems(); };
    tabsEl.appendChild(btn);
  });
  _renderShopItems();
}

function _updateShopTabs(){
  document.querySelectorAll('.shop-tab').forEach((el,i)=>
    el.classList.toggle('active',i===GS.shopTabIdx));
}

function _renderShopItems(){
  if(!GS.cityState||!GS.activeShop) return;
  // Route sell tabs
  if(GS.activeShop==='ferreiro'&&GS.shopTabIdx===2){ _renderSellItems('gear'); return; }
  if(GS.activeShop==='mercador'&&GS.shopTabIdx===1){ _renderSellItems('bag');  return; }

  const myP=GS.cityState.players.find(p=>p.id===GS.myPid);
  const gold=myP?myP.gold:0;
  const goldEl=$('shop-gold-val'); if(goldEl) goldEl.textContent=gold;

  const shops=GS.cityState.shops;
  let items=[], shopKey=GS.activeShop;
  if(GS.activeShop==='ferreiro'){
    if(GS.shopTabIdx===0){ items=shops.ferreiro.weapons; shopKey='ferreiro_weapon'; }
    else                 { items=shops.ferreiro.armors;  shopKey='ferreiro_armor';  }
  } else {
    items=shops[GS.activeShop]||[];
  }

  const myClass = myP?myP.class_id:null;
  const list=$('shop-items-list'); if(!list) return;
  list.innerHTML=items.map(item=>{
    // Restrição de classe: allowed_classes ausente = todas as classes.
    const classRestrita = item.allowed_classes && myClass && !item.allowed_classes.includes(myClass);
    // Refeição de balcão (1×/visita): bloqueia se o herói já a pediu nesta visita.
    const jaUsada = item.effect==='meal_survival'
      && myP && (myP.taverna_refeicoes||[]).includes(item.id);
    const canBuy=gold>=item.price && !classRestrita && !jaUsada;
    const desc=_itemDesc(item);
    const kindTag=item.kind==='shield'?'<span style="color:var(--blue);font-size:.68rem;"> [escudo]</span>':'';
    const restritaTag=classRestrita?'<span style="color:var(--danger,#ff4136);font-size:.68rem;"> 🚫 Classe restrita</span>':'';
    const usadaTag=jaUsada?'<span style="color:var(--muted,#888);font-size:.68rem;"> ✔ já usada nesta visita</span>':'';
    return `<div class="shop-item"${(classRestrita||jaUsada)?' style="opacity:.5;"':''}>
      <span class="shop-item-emoji">${item.emoji||'📦'}</span>
      <div class="shop-item-info">
        <div class="shop-item-name">${item.name}${kindTag}${restritaTag}${usadaTag}</div>
        <div class="shop-item-desc">${desc}</div>
      </div>
      <span class="shop-item-price">💰 ${item.price}</span>
      <button class="btn-buy" ${canBuy?'':'disabled'}
        title="${classRestrita?'Sua classe não pode usar este item':jaUsada?'Já usada nesta visita à cidade':''}"
        onclick="buyItem('${shopKey}','${item.id}')">${classRestrita?'🚫 Restrito':jaUsada?'✔ Usada':'Comprar'}</button>
    </div>`;
  }).join('');
  // Tooltip de pergaminho (hover) — a loja usa innerHTML, então anexa por índice.
  const rows = list.querySelectorAll('.shop-item');
  items.forEach((item, idx) => {
    if(item.effect === 'scroll' && rows[idx]) aplicarTooltipPergaminho(rows[idx], item);
  });
}

function _renderSellItems(mode){
  const myP=GS.cityState&&GS.cityState.players.find(p=>p.id===GS.myPid);
  const gold=myP?myP.gold:0;
  const goldEl=$('shop-gold-val'); if(goldEl) goldEl.textContent=gold;
  const list=$('shop-items-list'); if(!list) return;
  if(!myP){ list.innerHTML=''; return; }

  const sellable=[];
  if(mode==='gear'||mode==='all'){
    const w=myP.gear&&myP.gear.weapon;
    if(w&&w.id!=='unarmed'){
      const bp=w.buy_price||0;
      sellable.push({slot:'weapon',item:w,sp:Math.max(1,Math.floor(bp/3)),tag:'Arma equipada'});
    }
    const a=myP.gear&&myP.gear.armor;
    if(a&&a.id&&a.id!=='cloak'){
      const bp=a.buy_price||0;
      sellable.push({slot:'armor',item:a,sp:Math.max(1,Math.floor(bp/3)),tag:'Armadura equipada'});
    }
    const _slotTags={off_hand:'Mão esquerda',head:'Cabeça',ring1:'Anel',ring2:'Anel',item1:'Item',item2:'Item'};
    for(const slot of ['off_hand','head','ring1','ring2','item1','item2']){
      const acc=myP.gear&&myP.gear[slot];
      if(acc){
        const bp=acc.buy_price||0;
        sellable.push({slot,item:acc,sp:Math.max(1,Math.floor(bp/3)),tag:_slotTags[slot]||'Acessório'});
      }
    }
  }
  if(mode==='bag'||mode==='all'){
    (myP.bag||[]).forEach((bagItem,i)=>{
      const bp=bagItem.buy_price||bagItem.price||0;
      sellable.push({slot:`bag_${i}`,item:bagItem,sp:Math.max(1,Math.floor(bp/3)),tag:'Mochila'});
    });
  }

  if(sellable.length===0){
    list.innerHTML='<div style="color:var(--text2);padding:20px;text-align:center;font-size:.82rem;">Nenhum item para vender.</div>';
    return;
  }
  list.innerHTML=sellable.map(({slot,item,sp,tag})=>`
    <div class="shop-item">
      <span class="shop-item-emoji">${item.emoji||'📦'}</span>
      <div class="shop-item-info">
        <div class="shop-item-name">${item.name}</div>
        <div class="shop-item-desc">${_itemDesc(item)} • <span style="color:var(--text3)">${tag}</span></div>
      </div>
      <span class="shop-item-price" style="color:var(--green);">+💰 ${sp}</span>
      <button class="btn-buy" style="background:var(--green);color:#000;"
        onclick="sellItem('${slot}')">Vender</button>
    </div>`).join('');
}

function _itemDesc(item){
  if(item.effect === 'scroll'){
    const pv = item.preview || {};
    const mg = (typeof GRIMORIO_CLIENT !== 'undefined') ? GRIMORIO_CLIENT[item.magia_id] : null;
    const partes = [`Nv ${item.nivel_conjurador||1}`];
    if(item.int_bonus) partes.push(`INT+${item.int_bonus}`);
    if(pv.dano) partes.push(pv.dano + (pv.talento_dano ? ' ×1.5' : ''));
    else if(pv.alcance === 0) partes.push('área no conjurador');
    return `${(mg&&mg.nome)||item.magia_id} • ${partes.join(' • ')}`;
  }
  if(item.die){
    const SUBTIPO={cortante:'Cortante',perfurante:'Perfurante',contundente:'Contusão'};
    const range=item.reach==='lanca' ? ' • Alcance 2 (reto) / 1 (diag)'
              : item.reach==='cajado' ? ' • Alcance: adjacentes + diagonais'
              : item.range ? ` • Alcance ${item.range}` : '';
    const sub=item.categoria?` • ${SUBTIPO[item.categoria]||item.categoria}`:'';
    const duas=item.two_handed?' • ✋✋ 2 mãos':'';
    const arr=item.throw_range?` • 🎯 Arremesso ${item.throw_range}`:'';
    const ehAdaga=item.id==='dagger'||/adaga/i.test(item.name||'');
    const segMao=ehAdaga?' • 2ª mão: usa DES':'';
    return `${item.die} dano (${item.stat==='dex'?'DES':'FOR'})${sub}${range}${duas}${arr}${segMao}`;
  }
  if(item.ac_bonus!=null){
    const kindTxt=item.kind==='shield'?'Escudo — soma com armadura':'Armadura';
    return `${kindTxt} • CA +${item.ac_bonus}`;
  }
  // Comida/bebida da taverna: fome/sede vêm nos campos item.fome / item.sede.
  if(item.effect==='food'||item.effect==='meal_survival'){
    const partes=[];
    if(item.fome) partes.push(`+${item.fome} fome`);
    if(item.sede) partes.push(`+${item.sede} sede`);
    let txt=partes.join(' / ');
    if(item.effect==='meal_survival') txt+=' • 1× por visita';
    return txt;
  }
  if(item.effect==='ale')
    return `+${item.value||0} fome/sede • -1 ataque por 10 rodadas`;
  if(item.effect==='wine')
    return `+${item.value||0} fome/sede • -1 ataque e reflexos por 10 rodadas`;
  if(item.effect==='ration')
    return `+${item.value||0} fome e sede`;
  const fx={
    heal:'Restaura HP', atk_bonus:'Bônus de Ataque',
    maxhp:'Aumenta HP máx', atk:'Bônus Ataque', spd:'Velocidade',
    full_heal:'Cura total de HP',
    bless:'Bônus de Ataque divino', cleanse:'Remove status negativos',
    temp_atk:'Ataque temporário',
    def_:'CA +',
  };
  const v=item.value?` ${item.value}`:'';
  return (fx[item.effect]||item.effect||'')+v;
}

function buyItem(shop, itemId){
  send({type:'shop_buy', shop, item_id:itemId});
}

function sellItem(slot){
  send({type:'sell_item', item_slot:slot});
}

function closeShop(){
  GS.activeShop=null;
  const m=$('shop-modal'); if(m) m.classList.remove('open');
}

// ═══════════════════════════════════════════════════════════════════════════
// ■  GUILDA DOS HERÓIS (Fase 0) — compra de especializações e técnicas
//    Overlay próprio (#guild-modal) criado sob demanda. A compra vai pelo
//    servidor (GS.guildBuy → guild_buy) e o city_state re-broadcast reabre/
//    re-renderiza o painel. Equipar técnica é feito na FICHA (não aqui).
// ═══════════════════════════════════════════════════════════════════════════
function _guildItemRow(i, owned, me){
  const lista = i.categoria === 'tecnica' ? (owned.tecnicas || []) : (owned.especializacoes || []);
  const has   = lista.includes(i.id);
  const reqOk = !i.requer || lista.includes(i.requer);
  const gold  = (me && me.gold) || 0;
  const custo = i.categoria === 'tecnica'
    ? ` · 🍖${i.custo_fome} 💧${i.custo_sede} · ⏱️${i.recarga_rodadas}r` : '';
  let action;
  if(has){
    action = `<span class="guild-owned">Possuído ✓</span>`;
  } else if(!reqOk){
    const reqNome = (GS.guildCatalogFor(me.class_id).find(x=>x.id===i.requer)||{}).nome || i.requer;
    action = `<span class="guild-locked">🔒 Requer ${reqNome}</span>`;
  } else {
    const can = gold >= i.preco;
    action = `<button class="guild-buy" ${can?'':'disabled'}
                title="${can?'':'Ouro insuficiente'}"
                onclick="GS.guildBuy('${i.id}')">Comprar 🪙${i.preco}</button>`;
  }
  return `<div class="guild-item${has?' is-owned':''}">
    <span class="gi-icon">${i.icon||'✨'}</span>
    <div class="gi-body"><b>${i.nome}</b><br><small>${i.desc||''}${custo}</small></div>
    ${action}</div>`;
}

function _renderGuild(){
  const modal = $('guild-modal'); if(!modal) return;
  const me = GS.me || ((GS.cityState && GS.cityState.players) || []).find(p => p.id === GS.myPid);
  if(!me) return;
  const owned   = GS.guildOwnedOf(GS.myPid);
  const catalog = GS.guildCatalogFor(me.class_id);
  const specs = catalog.filter(i => i.categoria === 'especializacao');
  const tecs  = catalog.filter(i => i.categoria === 'tecnica');
  const goldEl = $('guild-gold'); if(goldEl) goldEl.textContent = me.gold || 0;
  const sec = (arr) => arr.length
    ? arr.map(i => _guildItemRow(i, owned, me)).join('')
    : `<div class="guild-empty">— em breve —</div>`;
  const specEl = $('guild-list-spec'); if(specEl) specEl.innerHTML = sec(specs);
  const tecEl  = $('guild-list-tec');  if(tecEl)  tecEl.innerHTML  = sec(tecs);
}

function openGuild(){
  if(!GS.cityState){ toast('Carregando guilda…','var(--blue)'); return; }
  const me = GS.me || (GS.cityState.players || []).find(p => p.id === GS.myPid);
  if(!me){ toast('Guilda indisponível agora.','var(--danger)'); return; }
  let modal = $('guild-modal');
  if(!modal){
    modal = document.createElement('div');
    modal.id = 'guild-modal';
    modal.className = 'guild-modal';
    modal.innerHTML =
      `<div class="guild-box">
         <div class="guild-head">
           <h2>⚔ Guilda dos Heróis</h2>
           <button class="guild-close" onclick="closeGuild()" aria-label="Fechar">✕</button>
         </div>
         <div class="guild-sub">Aprimore sua classe permanentemente. Ouro: 💰 <span id="guild-gold">0</span></div>
         <div class="guild-sections">
           <section class="guild-sec"><h3>🌟 Especializações</h3><div class="guild-list" id="guild-list-spec"></div></section>
           <section class="guild-sec"><h3>⚔️ Técnicas da Guilda</h3><div class="guild-list" id="guild-list-tec"></div></section>
         </div>
       </div>`;
    modal.addEventListener('click', (e) => { if(e.target === modal) closeGuild(); });
    document.body.appendChild(modal);
  }
  modal.classList.add('open');
  _renderGuild();
}

function closeGuild(){
  const m = $('guild-modal'); if(m) m.classList.remove('open');
}

// ═══════════════════════════════════════════════════════════════════════════
// LOJA REUTILIZÁVEL (overlay) — lê GS.CATALOGO_ITENS, opera no herói ativo
// (modelo client-side de GS.getHeroiAtivo). NOTA: compras aqui ainda NÃO são
// autoritativas no servidor — para tornar autoritativo, trocar a mutação em
// comprarItem() por send({type:'shop_buy', shop, item_id}) (ver VISUAL_CONTRACT).
// Funções globais (usadas por onclick inline). Estas tocam o DOM, por isso
// vivem em game.js (gameState.js é livre de DOM).
// ═══════════════════════════════════════════════════════════════════════════
function renderDescricaoItem(item){
  switch(item.tipo){
    case 'arma': {
      const alcance = item.alcanceEspecial
        ? item.alcanceEspecial.descricao
        : 'Adjacente';
      const modos = item.modosDuasMaos
        ? `1 mão: ${item.danoUmaMao} | 2 mãos: ${item.danoDuasMaos}`
        : `Dano: ${item.dano}`;
      return `${modos} | ${item.atributo} | Alcance: ${alcance}`;
    }
    case 'armaDistancia':
      return `Dano: ${item.dano}+DEX | Alcance: ${item.alcance} quad. | ${item.slotSecundario === 'flechas' ? 'Requer flechas' : 'Slot secundário livre'}`;
    case 'armadura':
      return `Bônus CA: +${item.bonusCA}`;
    case 'escudo':
      return `Bônus CA: +${item.bonusCA}`;
    case 'secundario':
      return `Bônus visão: +${item.bonusVisao} quad. | Duração: ${item.duracao} rodadas`;
    case 'consumivel': {
      const partes = [];
      if(item.fome > 0) partes.push(`🍖 +${item.fome} fome`);
      if(item.sede > 0) partes.push(`💧 +${item.sede} sede`);
      return partes.join(' | ');
    }
    case 'municao': {
      const danoExtra = item.danoExtra
        ? ` | +${item.danoExtra} ${item.tipoDano}`
        : '';
      return `${item.quantidade} unidades${danoExtra}`;
    }
    case 'varinha':
      return `Slots de magia: ${item.slotsMagia} | Dano: ${item.dano} | Usar magia = ação bônus`;
    case 'itemMagico':
      return `+${item.slotsExtras} slots de inventário | Ocupa slot mágico`;
    default:
      return '';
  }
}

// ── Animação do D100 (Animar Mortos) — dois d10 temáticos (PASSO 3) ──────────
// Renderer puro: monta um overlay full-screen, anima a rolagem e chama
// onConclucao() ao fechar. Consome o objeto `resultado` retornado por
// handle_animar_mortos no servidor (PASSO 2): { d10_dezena, d10_unidade,
// rolagem, chance, zona_hostil, resultado }.
function animarRolagemD100(resultado, onConclucao) {
  const overlay = document.createElement('div')
  overlay.id = 'overlay-d100'
  overlay.style.cssText = `
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.88);
    z-index: 500;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: 'Cinzel', serif;
  `

  overlay.innerHTML = `
    <!-- Título -->
    <div style="
      color: #cc44ff;
      font-family: 'Cinzel Decorative', serif;
      font-size: 18px;
      letter-spacing: 4px;
      margin-bottom: 32px;
    ">💀 ANIMAR MORTOS</div>

    <!-- Os dois D10 -->
    <div style="display: flex; gap: 24px; margin-bottom: 32px;">

      <!-- D10 dezena -->
      <div style="text-align: center;">
        <div style="
          color: #8a7a5a;
          font-size: 9px;
          letter-spacing: 3px;
          margin-bottom: 8px;
        ">DEZENA</div>
        <div id="d10-dezena" style="
          width: 72px; height: 72px;
          background: rgba(150,0,200,0.15);
          border: 2px solid #9900cc;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
          color: #cc44ff;
          font-weight: bold;
        ">?</div>
      </div>

      <!-- D10 unidade -->
      <div style="text-align: center;">
        <div style="
          color: #8a7a5a;
          font-size: 9px;
          letter-spacing: 3px;
          margin-bottom: 8px;
        ">UNIDADE</div>
        <div id="d10-unidade" style="
          width: 72px; height: 72px;
          background: rgba(150,0,200,0.15);
          border: 2px solid #9900cc;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
          color: #cc44ff;
          font-weight: bold;
        ">?</div>
      </div>
    </div>

    <!-- Total -->
    <div id="total-d100" style="
      color: #ffffff;
      font-size: 42px;
      font-weight: bold;
      margin-bottom: 16px;
      opacity: 0;
      transition: opacity 0.4s ease;
    ">00</div>

    <!-- Faixas de resultado -->
    <div id="faixas-resultado" style="
      display: flex;
      gap: 8px;
      margin-bottom: 24px;
      font-size: 10px;
      letter-spacing: 1px;
    ">
      <span style="color:#ff4136;">
        💀 Hostil: 1–${resultado.zona_hostil || 0}
      </span>
      <span style="color:#8a7a5a;">|</span>
      <span style="color:#2ecc40;">
        ✅ Sucesso: ${(resultado.zona_hostil || 0) + 1}–${resultado.chance}
      </span>
      <span style="color:#8a7a5a;">|</span>
      <span style="color:#ff851b;">
        ❌ Falha: ${resultado.chance + 1}–99
      </span>
    </div>

    <!-- Resultado final -->
    <div id="resultado-d100" style="
      font-family: 'Cinzel Decorative', serif;
      font-size: 20px;
      opacity: 0;
      transition: opacity 0.5s ease;
      min-height: 32px;
    "></div>
  `

  document.body.appendChild(overlay)

  // Animação de rolagem
  const dezenaEl = document.getElementById('d10-dezena')
  const unidadeEl = document.getElementById('d10-unidade')
  const totalEl = document.getElementById('total-d100')
  const resultEl = document.getElementById('resultado-d100')

  let frame = 0
  const totalFrames = 24
  const intervalo = setInterval(() => {
    frame++
    dezenaEl.textContent  = Math.floor(Math.random() * 10)
    unidadeEl.textContent = Math.floor(Math.random() * 10)

    if (frame >= totalFrames) {
      clearInterval(intervalo)

      // Mostra resultado real
      const dezena  = resultado.d10_dezena
      const unidade = resultado.d10_unidade
      const total   = resultado.rolagem

      dezenaEl.textContent  = dezena
      unidadeEl.textContent = unidade

      setTimeout(() => {
        totalEl.textContent = total.toString().padStart(2, '0')
        totalEl.style.opacity = '1'

        setTimeout(() => {
          const cores = {
            sucesso: '#2ecc40',
            hostil:  '#ff4136',
            falha:   '#ff851b'
          }
          const textos = {
            sucesso: '✅ SUCESSO — Criatura animada!',
            hostil:  '💀 FALHA CATASTRÓFICA — Criatura hostil!',
            falha:   '❌ FALHA — O cadáver permanece inerte'
          }

          resultEl.textContent  = textos[resultado.resultado]
          resultEl.style.color  = cores[resultado.resultado]
          resultEl.style.opacity = '1'

          // Fecha após 2.5 segundos
          setTimeout(() => {
            overlay.style.opacity = '0'
            overlay.style.transition = 'opacity 0.4s ease'
            setTimeout(() => {
              overlay.remove()
              if (onConclucao) onConclucao()
            }, 400)
          }, 2500)
        }, 600)
      }, 300)
    }
  }, 60)
}

// ── Ficha do Pedro com aba de Magias (PASSO 4) ───────────────────────────────
// Renderers puros: retornam HTML (string) a partir de um objeto `heroi` que
// carrega os campos adicionados em HERO_DATA.pedro no PASSO 1
// (habilidadeClasse, animados, magiasConhecidas, magiasUsadasHoje,
// statsModificados.inteligencia).
//
// NOTA — ainda NÃO roteados a nenhum painel. Estado dos handlers referenciados:
//   • esconderTooltip()                   → existe (linha ~1488)
//   • mostrarTooltipHabilidade(ev, id)    → existe (PASSO 5, abaixo)
//   • mostrarTooltipAnimado(ev, id, obj)  → existe (PASSO 5, abaixo)
//   • trocarAbaFicha(aba, heroKey)        → NÃO existe (alterna ATRIBUTOS/MAGIAS)
//   • mostrarTooltipMagia(ev, id)         → NÃO existe
//   • renderConteudoAtributos(heroi)      → NÃO existe (citado só em comentário)
// A render em si funciona; os handlers ausentes só disparam em clique/hover e
// lançariam ReferenceError até serem implementados num passo futuro.
function renderFichaPedro(heroi) {
  const nivel     = heroi.nivel || 1
  const hab       = heroi.habilidadeClasse
  const slots     = hab.calcularSlots(nivel, heroi.statsModificados.inteligencia)
  const animados  = heroi.animados || []
  const slotsUsados = animados.reduce((s, a) => s + a.slots, 0)

  return `
    <!-- ABAS -->
    <div style="
      display: flex;
      border-bottom: 1px solid #c8a95133;
      margin-bottom: 16px;
    ">
      <button onclick="trocarAbaFicha('atributos','pedro')"
        id="aba-atributos" style="
        flex:1; padding:10px; background:transparent;
        border:none; border-bottom:2px solid #c8a951;
        color:#c8a951; font-family:'Cinzel',serif;
        font-size:10px; letter-spacing:2px; cursor:pointer;
      ">📊 ATRIBUTOS</button>
      <button onclick="trocarAbaFicha('magias','pedro')"
        id="aba-magias" style="
        flex:1; padding:10px; background:transparent;
        border:none; border-bottom:2px solid transparent;
        color:#8a7a5a; font-family:'Cinzel',serif;
        font-size:10px; letter-spacing:2px; cursor:pointer;
      ">💀 MAGIAS</button>
    </div>

    <!-- CONTEÚDO DA ABA -->
    <div id="conteudo-ficha-pedro">
      <!-- Atributos ficam aqui por padrão -->
      <!-- renderConteudoAtributos(heroi) -->
    </div>
  `
}

function renderAbaMagiasPedro(heroi) {
  const nivel      = heroi.nivel || 1
  const hab        = heroi.habilidadeClasse
  const slots      = hab.calcularSlots(nivel, heroi.statsModificados.inteligencia)
  const animados   = heroi.animados || []
  const slotsUsados = animados.reduce((s, a) => s + a.slots, 0)
  const usados     = heroi.magiasUsadasHoje || { primeiro:0, segundo:0, terceiro:0 }

  const config = {
    1: { primeiro:2, segundo:0, terceiro:0 },
    2: { primeiro:3, segundo:0, terceiro:0 },
    3: { primeiro:3, segundo:1, terceiro:0 },
    4: { primeiro:3, segundo:2, terceiro:0 },
    5: { primeiro:3, segundo:2, terceiro:1 }
  }[Math.min(nivel, 5)]

  return `
    <!-- HABILIDADE DE CLASSE -->
    <div style="margin-bottom:20px;">
      <div style="
        color:#8a7a5a; font-size:9px;
        letter-spacing:3px; margin-bottom:10px;
      ">⚗️ HABILIDADE DE CLASSE</div>

      <div
        onmouseenter="mostrarTooltipHabilidade(event,'animar_mortos')"
        onmouseleave="esconderTooltip()"
        onclick="usarAnimarMortos()"
        title="Clique para animar um cadáver adjacente"
        style="
          display:flex; align-items:center; gap:12px;
          padding:12px;
          background:rgba(150,0,200,0.08);
          border:1px solid #9900cc66;
          cursor:pointer;
        "
      >
        <div style="font-size:28px;">💀</div>
        <div style="flex:1;">
          <div style="
            color:#cc44ff;
            font-family:'Cinzel Decorative',serif;
            font-size:13px; margin-bottom:3px;
          ">Animar Mortos</div>
          <div style="
            color:#8a7a5a; font-size:10px; letter-spacing:1px;
          ">Habilidade de Classe • Ação Principal</div>
          <div style="color:#ff4444; font-size:10px; margin-top:3px;">
            🍖 -20 | 💧 -20 por uso
          </div>
        </div>
      </div>
    </div>

    <!-- EXÉRCITO ANIMADO -->
    <div style="margin-bottom:20px;">
      <div style="
        display:flex; justify-content:space-between;
        color:#8a7a5a; font-size:9px;
        letter-spacing:3px; margin-bottom:10px;
      ">
        <span>💀 EXÉRCITO ANIMADO</span>
        <span style="color:${slotsUsados >= slots ? '#ff4136' : '#2ecc40'}">
          ${slotsUsados}/${slots} slots
        </span>
      </div>

      <!-- Barra de slots -->
      <div style="display:flex; gap:3px; margin-bottom:12px;">
        ${Array.from({length: slots}).map((_, i) => `
          <div style="
            flex:1; height:6px;
            background:${i < slotsUsados ? '#cc44ff' : '#1a1a1a'};
            border:1px solid ${i < slotsUsados ? '#cc44ff' : '#2a2a2a'};
            transition:all 0.3s ease;
          "></div>
        `).join('')}
      </div>

      <!-- Comandar — só aparece no turno dos servos -->
      ${animados.length > 0 && GS.gameState?.animados_turn === GS.myPid ? `
        <button onclick="usarComandarAnimados()" style="
          width:100%; margin-bottom:10px; padding:7px;
          background:rgba(150,0,200,0.22); border:1px solid #9900ccaa;
          color:#cc44ff; font-family:'Cinzel',serif; font-size:10px;
          letter-spacing:2px; cursor:pointer;
        ">⚔️ AUTO-COMANDAR TODOS OS SERVOS</button>
      ` : ''}

      <!-- Animados -->
      ${animados.length > 0
        ? animados.map(a => `
          <div
            onmouseenter="mostrarTooltipAnimado(event, '${a.id}', ${JSON.stringify(a).replace(/"/g, '&quot;')})"
            onmouseleave="esconderTooltip()"
            style="
              display:flex; align-items:center; gap:10px;
              padding:10px 12px; margin-bottom:6px;
              background:rgba(150,0,200,0.05);
              border:1px solid #9900cc33;
              cursor:help;
            "
          >
            <div style="font-size:22px; min-width:28px; text-align:center;">
              ${a.icone}
            </div>
            <div style="flex:1;">
              <div style="
                color:#c8b89a; font-family:'Cinzel',serif;
                font-size:11px; margin-bottom:4px;
              ">${a.nome}</div>
              ${a.dominado_por_monstro ? `
                <div style="color:#ff4136; font-size:9px; margin-bottom:3px;">
                  ⛓️ Roubado por necromante!
                </div>` : (a.por_dominacao ? `
                <div style="color:#cc44ff; font-size:9px; margin-bottom:3px;">
                  🔒 Controle ${a.dominacao?.permanente ? 'PERMANENTE'
                    : `${(a.dominacao?.rodada || 2) - 1}/3 → permanente`}
                </div>` : '')}
              <div style="
                height:4px; background:#1a1a1a;
                border:1px solid #2a2a2a; margin-bottom:3px;
              ">
                <div style="
                  width:${(a.vida_atual/a.vida_max)*100}%;
                  height:100%;
                  background:${(a.vida_atual/a.vida_max) > 0.6
                    ? '#2ecc40' : (a.vida_atual/a.vida_max) > 0.3
                    ? '#ff851b' : '#ff4136'};
                "></div>
              </div>
              <div style="color:#8a7a5a; font-size:9px;">
                ❤️ ${a.vida_atual}/${a.vida_max}
              </div>
            </div>
            <div style="
              color:#cc44ff; font-size:9px;
              letter-spacing:1px; text-align:right;
            ">Nv.${a.nivel}<br>${a.slots} slot${a.slots > 1 ? 's' : ''}</div>
          </div>
        `).join('')
        : `<div style="
            color:#4a4a4a; font-size:11px;
            font-family:'Cinzel',serif;
            text-align:center; padding:16px;
            border:1px dashed #2a2a2a;
          ">Nenhuma criatura animada</div>`
      }
    </div>

    <!-- MAGIAS DO DIA (cartas do grimório) -->
    <div>
      <div style="
        color:#8a7a5a; font-size:9px;
        letter-spacing:3px; margin-bottom:12px;
      ">📜 MAGIAS DO DIA</div>
      ${renderMagiasFichaEmJogo(heroi, 'mage')}
    </div>
  `
}

// ── Tooltips da habilidade e dos animados (PASSO 5) ──────────────────────────
// Dependências PRESENTES e funcionais: renderLinhaTooltip (linha ~1767),
// elemento #item-tooltip (linha ~1722), esconderTooltip, GS.getHeroiAtivo.
//
// MISMATCH conhecido (reconciliação futura): GS.getHeroiAtivo() devolve o
// herói do MODELO DE EQUIPAMENTO (gameState.js → inicializarHeroi), que tem
// key/equipado/inventario/fome/sede mas NÃO tem habilidadeClasse nem
// statsModificados — esses campos vivem em HERO_DATA[heroKey] (game.js, PASSO 1).
// Como getHeroiAtivo() nunca retorna falsy (default victorCoiceBravo), o
// fallback `|| HERO_DATA['pedro']` NÃO dispara em jogo, então
// mostrarTooltipHabilidade lançaria TypeError (hab indefinido) até unificarmos
// os dois modelos de herói (ou lermos a habilidade de HERO_DATA[heroKey]).
// mostrarTooltipAnimado é autossuficiente (usa o objeto recebido) e funciona já.
function mostrarTooltipHabilidade(event, id) {
  if (id !== 'animar_mortos') return
  // Tooltip é específico do Pedro: usa o registro COMPLETO (habilidadeClasse +
  // statsModificados). GS.getHeroiAtivo() devolveria o modelo de equipamento
  // (sem esses campos), por isso preferimos HERO_DATA.pedro / GS.HERO_DATA.pedro.
  const heroi  = HERO_DATA?.pedro || GS.HERO_DATA?.pedro
  const nivel  = heroi.nivel || 1
  const hab    = heroi.habilidadeClasse
  const slots  = hab.calcularSlots(nivel, heroi.statsModificados.inteligencia)
  const t      = document.getElementById('item-tooltip')

  t.innerHTML = `
    <div style="padding:10px 14px 8px; border-bottom:1px solid #9900cc33;">
      <div style="
        font-family:'Cinzel Decorative',serif;
        color:#cc44ff; font-size:13px; margin-bottom:2px;
      ">💀 Animar Mortos</div>
      <div style="color:#8a7a5a; font-size:9px; letter-spacing:3px;">
        HABILIDADE DE CLASSE • SEMPRE DISPONÍVEL
      </div>
    </div>

    <div style="padding:10px 14px;">
      ${renderLinhaTooltip('⚡', 'Ação', 'Principal')}
      ${renderLinhaTooltip('📏', 'Alcance', 'Adjacente ao cadáver')}
      ${renderLinhaTooltip('🍖', 'Custo Fome', '-20 por uso')}
      ${renderLinhaTooltip('💧', 'Custo Sede', '-20 por uso')}
      ${renderLinhaTooltip('🔮', 'Slots Disponíveis', slots)}
      ${renderLinhaTooltip('📊', 'Slots = Nível', 'do monstro')}
    </div>

    <div style="
      padding:8px 14px;
      border-top:1px solid #9900cc33;
      border-bottom:1px solid #9900cc33;
      background:rgba(150,0,200,0.05);
    ">
      <div style="
        color:#cc44ff; font-size:9px;
        letter-spacing:3px; margin-bottom:8px;
      ">CHANCE DE SUCESSO</div>
      ${renderLinhaTooltip('✅', 'Criatura do seu nível', '90%')}
      ${renderLinhaTooltip('⬇️', '1 nível abaixo', '95%')}
      ${renderLinhaTooltip('⬇️', '2+ níveis abaixo', '99% (máx)')}
      ${renderLinhaTooltip('⬆️', '1 nível acima', '80% / hostil <10%')}
      ${renderLinhaTooltip('⬆️', '2 níveis acima', '70% / hostil <20%')}
      ${renderLinhaTooltip('⬆️', '3 níveis acima', '60% / hostil <30%')}
      ${renderLinhaTooltip('⬆️', '4 níveis acima', '50% / hostil <40%')}
    </div>

    <div style="
      padding:8px 14px;
      border-top:1px solid #9900cc33;
      border-bottom:1px solid #9900cc33;
      background:rgba(150,0,200,0.05);
    ">
      <div style="
        color:#cc44ff; font-size:9px;
        letter-spacing:3px; margin-bottom:8px;
      ">REGRAS DOS ANIMADOS</div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.8;">
        → Agem via ação bônus de Pedro<br>
        → Não podem ser curados<br>
        → Persistem entre aventuras<br>
        → Nunca recuperam pontos de vida<br>
        → A 0 de vida viram pó permanentemente<br>
        → Criaturas destruídas não podem ser reanimadas<br>
        → Se Pedro morrer todos viram pó imediatamente<br>
        → Hostis atacam o mais próximo — permanente
      </div>
    </div>

    <div style="
      padding:8px 14px; color:#c8b89a;
      font-size:10px; line-height:1.6; font-style:italic;
    ">
      Pedro concentra energia sombria sobre um cadáver,
      arrancando sua essência vital e aprisionando-a
      num corpo sem vida para servir eternamente.
    </div>
  `

  t.style.borderColor = '#9900cc'
  t.style.opacity = '1'
}

function mostrarTooltipAnimado(event, id, dadosAnimado) {
  const a = typeof dadosAnimado === 'string'
    ? JSON.parse(dadosAnimado)
    : dadosAnimado
  const t = document.getElementById('item-tooltip')
  const pctVida = (a.vida_atual / a.vida_max) * 100
  const corVida = pctVida > 60 ? '#2ecc40' :
                  pctVida > 30 ? '#ff851b' : '#ff4136'

  t.innerHTML = `
    <div style="padding:10px 14px 8px; border-bottom:1px solid #9900cc33;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
        <span style="font-size:20px;">${a.icone}</span>
        <div>
          <div style="
            font-family:'Cinzel Decorative',serif;
            color:#cc44ff; font-size:12px;
          ">${a.nome}</div>
          <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px;">
            MORTO-VIVO • NÍVEL ${a.nivel} • ${a.slots} SLOT${a.slots > 1 ? 'S' : ''}
          </div>
        </div>
      </div>
    </div>

    <div style="padding:10px 14px;">
      <div style="margin-bottom:8px;">
        <div style="
          display:flex; justify-content:space-between; margin-bottom:3px;
        ">
          <span style="color:#8a7a5a; font-size:10px;">❤️ Vida</span>
          <span style="color:${corVida}; font-size:11px; font-weight:bold;">
            ${a.vida_atual}/${a.vida_max}
          </span>
        </div>
        <div style="height:4px; background:#1a1a1a; border:1px solid #2a2a2a;">
          <div style="
            width:${pctVida}%; height:100%; background:${corVida};
          "></div>
        </div>
      </div>
      ${renderLinhaTooltip('🛡️', 'Classe de Armadura', a.ca)}
      ${renderLinhaTooltip('🎲', 'Dano', a.dano)}
      ${renderLinhaTooltip('👣', 'Movimento', `${a.movimento} casas`)}
      ${renderLinhaTooltip('⚔️', 'Alcance de ataque', '1 casa (4 direções)')}
    </div>

    <div style="
      padding:8px 14px;
      border-top:1px solid #9900cc33;
      text-align:center;
    ">
      <div style="color:#ff4136; font-size:9px; letter-spacing:1px;">
        ⚠️ Imune a curas • Não recupera vida
      </div>
      <div style="color:#4a4a4a; font-size:9px; margin-top:3px;">
        A 0 de vida vira pó permanentemente
      </div>
    </div>
  `

  t.style.borderColor = '#9900cc'
  t.style.opacity = '1'

  // Mostra alcance de ataque no mapa enquanto o cursor está sobre a ficha.
  window._animadoHover = a;
  if(GS.gameState) renderMap(GS.gameState);
}

// ── Aba ATRIBUTOS da ficha do Pedro (PASSO C) ────────────────────────────────
// IMPORTANTE: usa heroi.statsModificados/stats + calcularVidaMaxima. Por isso o
// herói passado precisa ser o registro COMPLETO (HERO_DATA de game.js), não o
// modelo de equipamento de GS.HERO_DATA — ver nota em trocarAbaFicha/_injetarFichaPedro.
function renderConteudoAtributosPedro(heroi) {
  const ATRIBUTOS = [
    { key: 'forca',        label: 'Força',        icone: '⚔️' },
    { key: 'destreza',     label: 'Destreza',     icone: '🏃' },
    { key: 'inteligencia', label: 'Inteligência', icone: '📖' },
    { key: 'constituicao', label: 'Constituição', icone: '🛡️' }
  ]

  const vidaMax = calcularVidaMaxima(
    'pedro',
    heroi.nivel || 1,
    heroi.statsModificados?.constituicao || heroi.stats?.constituicao
  )

  return `
    <!-- VIDA -->
    <div style="
      margin-bottom:14px; padding:10px 12px;
      background:rgba(255,65,54,0.08);
      border:1px solid #ff413644;
      display:flex; justify-content:space-between; align-items:center;
    ">
      <span style="color:#8a7a5a; font-size:11px; letter-spacing:2px;">
        ❤️ PONTOS DE VIDA
      </span>
      <div style="text-align:right;">
        <span style="color:#ff4136; font-size:18px; font-weight:bold;">
          ${heroi.vidaAtual || vidaMax}
        </span>
        <span style="color:#4a4a4a; font-size:13px;"> / ${vidaMax}</span>
      </div>
    </div>

    <!-- ATRIBUTOS -->
    ${ATRIBUTOS.map(attr => {
      const valorAtual = heroi.statsModificados?.[attr.key] || heroi.stats?.[attr.key] || 10
      const valorBase  = heroi.stats?.[attr.key] || 10
      const pct        = (valorAtual / 25) * 100
      const cor        = valorAtual > valorBase ? '#2ecc40' :
                         valorAtual < valorBase ? '#ff4136' : '#c8a951'
      return `
        <div style="margin-bottom:12px;">
          <div style="
            display:flex; justify-content:space-between;
            align-items:center; margin-bottom:4px;
          ">
            <span style="
              color:#8a7a5a; font-family:'Cinzel',serif;
              font-size:11px; letter-spacing:2px;
            ">${attr.icone} ${attr.label}</span>
            <span style="color:${cor}; font-size:13px; font-weight:bold;">
              ${valorAtual}
            </span>
          </div>
          <div style="height:6px; background:#1a1a1a; border:1px solid #2a2a2a;">
            <div style="
              width:${pct}%; height:100%; background:${cor};
              transition:width 0.6s ease;
            "></div>
          </div>
        </div>
      `
    }).join('')}

    <!-- NÍVEL -->
    <div style="
      margin-top:14px; padding:8px 12px;
      background:rgba(200,169,81,0.06);
      border:1px solid #c8a95133;
      display:flex; justify-content:space-between;
    ">
      <span style="color:#8a7a5a; font-size:11px; letter-spacing:2px;">NÍVEL</span>
      <span style="color:#c8a951; font-size:14px; font-weight:bold;">
        ${heroi.nivel || 1}
      </span>
    </div>
  `
}

// ── Troca de aba na ficha do Pedro (PASSO D) ─────────────────────────────────
// Fonte do herói: PREFERE HERO_DATA[heroiKey] (game.js, registro COMPLETO com
// stats/statsModificados) e cai para GS.HERO_DATA como fallback. Isto é uma
// correção deliberada do spec (que preferia GS): GS.HERO_DATA.pedro tem
// habilidadeClasse mas NÃO tem stats/statsModificados, e ambas as abas precisam
// deles (renderAbaMagiasPedro lê heroi.statsModificados.inteligencia).
function trocarAbaFicha(aba, heroiKey) {
  const conteudo = document.getElementById('conteudo-ficha-pedro')
  if (!conteudo) return

  const heroi = HERO_DATA?.[heroiKey] || GS.HERO_DATA?.[heroiKey]
  if (!heroi) return

  const btnAtributos = document.getElementById('aba-atributos')
  const btnMagias    = document.getElementById('aba-magias')
  if (!btnAtributos || !btnMagias) return

  const ativo   = '#c8a951'
  const inativo = '#8a7a5a'

  btnAtributos.style.borderBottomColor = aba === 'atributos' ? ativo : 'transparent'
  btnAtributos.style.color             = aba === 'atributos' ? ativo : inativo
  btnMagias.style.borderBottomColor    = aba === 'magias'    ? ativo : 'transparent'
  btnMagias.style.color                = aba === 'magias'    ? ativo : inativo

  conteudo.innerHTML = aba === 'atributos'
    ? renderConteudoAtributosPedro(heroi)
    : renderAbaMagiasPedro(heroi)
}

// Exposição global (PASSO F). _injetarFichaPedro / _classIdParaHeroiKey são
// declarações de função hoisted (definidas mais abaixo, junto de _csfShowPanel),
// portanto já existem aqui no momento desta atribuição.
window.trocarAbaFicha                = trocarAbaFicha
window.animarRolagemD100             = animarRolagemD100
window.mostrarTooltipHabilidade      = mostrarTooltipHabilidade
window.mostrarTooltipAnimado         = mostrarTooltipAnimado
window.renderAbaMagiasPedro          = renderAbaMagiasPedro
window.renderConteudoAtributosPedro  = renderConteudoAtributosPedro
window._injetarFichaPedro            = _injetarFichaPedro
window._classIdParaHeroiKey          = _classIdParaHeroiKey

// ── Ficha completa do herói DURANTE o jogo (overlay) ─────────────────────────
// Abre um overlay com a ficha do herói ativo. Para Pedro inclui as abas
// ATRIBUTOS e MAGIAS (Animar Mortos). Dispara via gatilho do HUD (a ligar).
//
// DEPENDÊNCIAS / DESVIOS (documentados):
//   • GS.me — adicionado em gameState.js (getter): jogador local autoritativo.
//     Quando presente (combate), HP/atributos/CA/nível vêm do servidor.
//   • Fonte do herói: a spec usava `GS.HERO_DATA || HERO_DATA`. CORRIGIDO para
//     `HERO_DATA || GS.HERO_DATA` (registro COMPLETO primeiro) — GS.HERO_DATA.pedro
//     NÃO tem stats/statsModificados/portrait, e renderAbaMagiasPedro lê
//     heroi.statsModificados.inteligencia (lançaria TypeError na aba MAGIAS).
//     Mesma correção aceita no _injetarFichaPedro da tela de seleção.
//   • Fome/Sede: a spec lê estadoServidor.hunger/thirst (/100); o servidor usa
//     fome/sede (0–10) via GS.getSurvival. Como hunger/thirst não existem, esse
//     bloco simplesmente NÃO renderiza (degradação graciosa) — sem erro.
function abrirFichaEmJogo(heroiKey) {
  // Remove overlay anterior se existir
  const anterior = document.getElementById('ficha-overlay-jogo')
  if (anterior) anterior.remove()

  // Obtém dados do herói — registro COMPLETO primeiro (stats/statsModificados/portrait)
  const heroi = HERO_DATA?.[heroiKey]
            || GS.HERO_DATA?.[heroiKey]
  if (!heroi) return

  // Obtém estado autoritativo do servidor para HP e stats
  const estadoServidor = GS.me || {}

  // Overlay escurecido
  const overlay = document.createElement('div')
  overlay.id = 'ficha-overlay-jogo'
  overlay.style.cssText = `
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.80);
    z-index: 300;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
  `

  // Container da ficha
  const container = document.createElement('div')
  container.style.cssText = `
    width: 320px;
    max-height: 88vh;
    overflow-y: auto;
    background: rgba(10,8,5,0.98);
    border: 1px solid #c8a951;
    position: relative;
  `

  // Cabeçalho com retrato e nome
  const cabecalho = document.createElement('div')
  cabecalho.style.cssText = `
    padding: 16px 20px 12px;
    border-bottom: 1px solid #c8a95133;
    display: flex;
    align-items: center;
    gap: 12px;
  `
  cabecalho.innerHTML = `
    <img
      src="${heroi.portrait || ''}"
      style="
        width:52px; height:52px;
        object-fit:cover; object-position:top;
        border:1px solid #c8a95166;
      "
      onerror="this.style.display='none'"
    />
    <div style="flex:1;">
      <div style="
        font-family:'Cinzel Decorative',serif;
        color:#c8a951; font-size:14px;
      ">${heroi.name || heroi.nome}</div>
      <div style="
        color:#8a7a5a; font-size:10px;
        letter-spacing:3px; margin-top:2px;
      ">${heroi.class || heroi.classeSelecao || ''}</div>
      <div style="
        color:#c8b89a; font-size:10px; margin-top:4px;
      ">NÍVEL ${estadoServidor.level || heroi.nivel || 1}</div>
    </div>
    <button
      onclick="document.getElementById('ficha-overlay-jogo').remove()"
      style="
        background:transparent; border:1px solid #4a4a4a;
        color:#8a7a5a; font-family:'Cinzel',serif;
        font-size:11px; padding:4px 10px; cursor:pointer;
        align-self:flex-start;
      "
    >✕</button>
  `

  // Área de conteúdo — abas para Pedro, padrão para os outros
  const conteudoArea = document.createElement('div')
  conteudoArea.style.cssText = 'padding: 16px 20px;'

  if (heroiKey === 'pedro') {
    // Pedro — com abas ATRIBUTOS e MAGIAS
    conteudoArea.innerHTML = `
      <div style="
        display:flex;
        border-bottom:1px solid #c8a95133;
        margin-bottom:16px;
      ">
        <button
          onclick="trocarAbaFichaJogo('atributos','pedro')"
          id="aba-jogo-atributos"
          style="
            flex:1; padding:9px; background:transparent;
            border:none; border-bottom:2px solid #c8a951;
            color:#c8a951; font-family:'Cinzel',serif;
            font-size:10px; letter-spacing:2px; cursor:pointer;
          "
        >📊 ATRIBUTOS</button>
        <button
          onclick="trocarAbaFichaJogo('magias','pedro')"
          id="aba-jogo-magias"
          style="
            flex:1; padding:9px; background:transparent;
            border:none; border-bottom:2px solid transparent;
            color:#8a7a5a; font-family:'Cinzel',serif;
            font-size:10px; letter-spacing:2px; cursor:pointer;
          "
        >💀 MAGIAS</button>
      </div>
      <div id="conteudo-ficha-jogo-pedro">
        ${renderConteudoAtributosFichaJogo(heroi, estadoServidor)}
      </div>
    `
  } else {
    // Outros heróis — só atributos
    conteudoArea.innerHTML = renderConteudoAtributosFichaJogo(heroi, estadoServidor)
  }

  // Botão fechar inferior
  const btnFechar = document.createElement('button')
  btnFechar.textContent = '✕ FECHAR'
  btnFechar.style.cssText = `
    width:100%; padding:11px;
    background:transparent;
    border:none; border-top:1px solid #1a1a1a;
    color:#8a7a5a; font-family:'Cinzel',serif;
    font-size:11px; letter-spacing:3px; cursor:pointer;
    transition:background 0.2s;
  `
  btnFechar.onmouseover = () => btnFechar.style.background = 'rgba(255,255,255,0.03)'
  btnFechar.onmouseout  = () => btnFechar.style.background = 'transparent'
  btnFechar.onclick     = () => {
    overlay.style.opacity = '0'
    setTimeout(() => overlay.remove(), 300)
  }

  // Clicar fora fecha
  overlay.onclick = (e) => {
    if (e.target === overlay) btnFechar.onclick()
  }

  container.appendChild(cabecalho)
  container.appendChild(conteudoArea)
  container.appendChild(btnFechar)
  overlay.appendChild(container)
  document.body.appendChild(overlay)

  // Fade in
  requestAnimationFrame(() => { overlay.style.opacity = '1' })
}

// Troca abas dentro da ficha em jogo — separado do trocarAbaFicha da seleção
function trocarAbaFichaJogo(aba, heroiKey) {
  const conteudo = document.getElementById('conteudo-ficha-jogo-pedro')
  if (!conteudo) return

  const heroi         = HERO_DATA?.[heroiKey] || GS.HERO_DATA?.[heroiKey]
  const estadoServidor = GS.me || {}
  if (!heroi) return

  const btnAtrib = document.getElementById('aba-jogo-atributos')
  const btnMagia = document.getElementById('aba-jogo-magias')
  if (!btnAtrib || !btnMagia) return

  const ativo   = '#c8a951'
  const inativo = '#8a7a5a'

  btnAtrib.style.borderBottomColor = aba === 'atributos' ? ativo : 'transparent'
  btnAtrib.style.color             = aba === 'atributos' ? ativo : inativo
  btnMagia.style.borderBottomColor = aba === 'magias'    ? ativo : 'transparent'
  btnMagia.style.color             = aba === 'magias'    ? ativo : inativo

  conteudo.innerHTML = aba === 'atributos'
    ? renderConteudoAtributosFichaJogo(heroi, estadoServidor)
    : renderAbaMagiasPedro(heroi)
}

// Renderiza atributos usando dados do servidor quando disponíveis
function renderConteudoAtributosFichaJogo(heroi, estadoServidor) {
  const ATRIBUTOS = [
    { key: 'forca',        serverKey: 'str_', label: 'Força',        icone: '⚔️' },
    { key: 'destreza',     serverKey: 'dex',  label: 'Destreza',     icone: '🏃' },
    { key: 'inteligencia', serverKey: 'int_', label: 'Inteligência', icone: '📖' },
    { key: 'constituicao', serverKey: 'con_', label: 'Constituição', icone: '🛡️' }
  ]

  // Prioriza dados do servidor — fallback para HERO_DATA
  const nivel   = estadoServidor.level  || heroi.nivel  || 1
  const hpAtual = estadoServidor.hp     || heroi.vidaAtual || '?'
  const hpMax   = estadoServidor.max_hp || calcularVidaMaxima?.(
    heroi.key, nivel,
    heroi.statsModificados?.constituicao || heroi.stats?.constituicao
  ) || '?'

  return `
    <!-- VIDA -->
    <div style="
      margin-bottom:14px; padding:10px 12px;
      background:rgba(255,65,54,0.08);
      border:1px solid #ff413644;
      display:flex; justify-content:space-between; align-items:center;
    ">
      <span style="color:#8a7a5a; font-size:11px; letter-spacing:2px;">
        ❤️ PONTOS DE VIDA
      </span>
      <div>
        <span style="color:#ff4136; font-size:18px; font-weight:bold;">
          ${hpAtual}
        </span>
        <span style="color:#4a4a4a; font-size:13px;"> / ${hpMax}</span>
      </div>
    </div>

    <!-- FOME E SEDE -->
    ${estadoServidor.hunger !== undefined ? `
      <div style="
        display:flex; gap:8px; margin-bottom:14px;
      ">
        <div style="
          flex:1; padding:8px 10px;
          background:rgba(255,133,27,0.08);
          border:1px solid #ff851b44;
        ">
          <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px; margin-bottom:4px;">
            🍖 FOME
          </div>
          <div style="height:5px; background:#1a1a1a; border:1px solid #2a2a2a;">
            <div style="
              width:${estadoServidor.hunger}%;
              height:100%; background:#ff851b;
            "></div>
          </div>
          <div style="color:#ff851b; font-size:10px; margin-top:3px;">
            ${estadoServidor.hunger}/100
          </div>
        </div>
        <div style="
          flex:1; padding:8px 10px;
          background:rgba(68,136,255,0.08);
          border:1px solid #4488ff44;
        ">
          <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px; margin-bottom:4px;">
            💧 SEDE
          </div>
          <div style="height:5px; background:#1a1a1a; border:1px solid #2a2a2a;">
            <div style="
              width:${estadoServidor.thirst}%;
              height:100%; background:#4488ff;
            "></div>
          </div>
          <div style="color:#4488ff; font-size:10px; margin-top:3px;">
            ${estadoServidor.thirst}/100
          </div>
        </div>
      </div>
    ` : ''}

    <!-- ATRIBUTOS -->
    ${ATRIBUTOS.map(attr => {
      const valor = estadoServidor[attr.serverKey]
            || heroi.statsModificados?.[attr.key]
            || heroi.stats?.[attr.key]
            || 10
      const pct = (valor / 25) * 100
      return `
        <div style="margin-bottom:12px;">
          <div style="
            display:flex; justify-content:space-between;
            align-items:center; margin-bottom:4px;
          ">
            <span style="
              color:#8a7a5a; font-family:'Cinzel',serif;
              font-size:11px; letter-spacing:2px;
            ">${attr.icone} ${attr.label}</span>
            <span style="color:#c8a951; font-size:13px; font-weight:bold;">
              ${valor}
            </span>
          </div>
          <div style="height:5px; background:#1a1a1a; border:1px solid #2a2a2a;">
            <div style="
              width:${pct}%; height:100%; background:#c8a951;
              transition:width 0.5s ease;
            "></div>
          </div>
        </div>
      `
    }).join('')}

    <!-- CA e NÍVEL -->
    <div style="
      display:flex; gap:8px; margin-top:14px;
    ">
      <div style="
        flex:1; padding:8px 12px;
        background:rgba(200,169,81,0.06);
        border:1px solid #c8a95133;
        display:flex; justify-content:space-between;
      ">
        <span style="color:#8a7a5a; font-size:10px; letter-spacing:2px;">NÍVEL</span>
        <span style="color:#c8a951; font-size:14px; font-weight:bold;">${nivel}</span>
      </div>
      ${estadoServidor.ac ? `
        <div style="
          flex:1; padding:8px 12px;
          background:rgba(200,169,81,0.06);
          border:1px solid #c8a95133;
          display:flex; justify-content:space-between;
        ">
          <span style="color:#8a7a5a; font-size:10px; letter-spacing:2px;">CA</span>
          <span style="color:#c8a951; font-size:14px; font-weight:bold;">
            ${estadoServidor.ac}${(estadoServidor.buffs_cancao && estadoServidor.buffs_cancao.bonus_ca) ? ` <span style="color:#4db8ff;font-size:.78em;" title="Canção Heroica de Henrique">🎵+${estadoServidor.buffs_cancao.bonus_ca}</span>` : ''}
          </span>
        </div>
      ` : ''}
    </div>
  `
}

// Usa Animar Mortos no cadáver adjacente (decisor puro em GS.cadaverAdjacente).
// Fecha a ficha para a animação D100 aparecer; o servidor valida e responde.
function usarAnimarMortos() {
  const cad = GS.cadaverAdjacente?.()
  if (!cad) { toast('Nenhum cadáver adjacente para animar.'); return }
  const ov = document.getElementById('ficha-overlay-jogo')
  if (ov) ov.remove()
  GS.animarMortos(cad.id)
}

// Comanda os animados (ação bônus). Fecha a ficha para ver o tabuleiro/ações.
function usarComandarAnimados() {
  const ov = document.getElementById('ficha-overlay-jogo')
  if (ov) ov.remove()
  GS.comandarAnimados()
}

// Exposição global
window.abrirFichaEmJogo             = abrirFichaEmJogo
window.trocarAbaFichaJogo           = trocarAbaFichaJogo
window.renderConteudoAtributosFichaJogo = renderConteudoAtributosFichaJogo
window.usarAnimarMortos             = usarAnimarMortos
window.usarComandarAnimados         = usarComandarAnimados

// ── Atalho de teclado: ESC fecha o overlay de ficha (visualização de outro herói).
// A ficha do Pedro agora é o painel principal (#my-stats com abas), então não há
// mais atalho/​botão para abrir a "ficha completa" do próprio Pedro.
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const aberta = document.getElementById('ficha-overlay-jogo')
    if (aberta) {
      aberta.style.opacity = '0'
      setTimeout(() => aberta.remove(), 300)
    }
  }
})

function abrirLoja(nomeLocal, heroiAtivo){
  window._lojaAtualAberta  = nomeLocal;  // loja atualmente aberta (limpa ao fechar)
  window._lojaUltimaAberta = nomeLocal;  // última loja (persiste p/ reabrir após compra)
  // Remove qualquer overlay anterior imediatamente (evita IDs duplicados
  // durante o fade de 300ms quando comprarItem reabre a loja).
  const stale = document.getElementById('loja-overlay');
  if(stale) stale.remove();

  const itensDaLoja = Object.values(GS.CATALOGO_ITENS).filter(
    item => item.loja === nomeLocal
  );

  const overlay = document.createElement('div');
  overlay.id = 'loja-overlay';
  overlay.style.cssText = `
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.85);
    z-index: 200;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity 0.3s ease;
  `;

  const nomesLojas = {
    ferreiro: '⚒️ Ferreiro',
    taverna:  '🍺 Taverna',
    mercado:  '🧙 Mercado'
  };

  overlay.innerHTML = `
    <div style="width: 700px; max-height: 85vh; background: rgba(10,8,5,0.98);
      border: 1px solid #c8a951; display: flex; flex-direction: column;
      font-family: 'Cinzel', serif;">
      <div style="padding: 20px 24px; border-bottom: 1px solid #c8a95133;
        display: flex; justify-content: space-between; align-items: center;">
        <span style="font-family: 'Cinzel Decorative', serif; color: #c8a951; font-size: 20px;">${nomesLojas[nomeLocal]}</span>
        <div style="display:flex; align-items:center; gap:20px;">
          <span style="color:#c8b89a; font-size:13px;">💰 ${heroiAtivo.moedas} moedas</span>
          <button onclick="fecharLoja()" style="background: transparent; border: 1px solid #4a4a4a;
            color: #8a7a5a; font-family: 'Cinzel', serif; font-size: 11px; padding: 6px 12px; cursor: pointer;">✕ FECHAR</button>
        </div>
      </div>
      <div style="overflow-y: auto; padding: 16px 24px; display: flex; flex-direction: column; gap: 8px;">
        ${itensDaLoja.map(item => {
          const podeComprar = item.permitidoPara.includes('todos') ||
            item.permitidoPara.includes(heroiAtivo.key);
          const semDinheiro = heroiAtivo.moedas < item.preco;
          const inventarioCheio = heroiAtivo.inventario.filter(Boolean).length >= 6;
          return `
            <div data-item-id="${item.id}" style="display: flex; justify-content: space-between; align-items: center;
              padding: 12px 16px; background: rgba(255,255,255,0.02);
              border: 1px solid ${podeComprar ? '#c8a95122' : '#ff413622'};
              opacity: ${podeComprar ? '1' : '0.4'};">
              <div>
                <div style="color:#c8b89a; font-size:13px; margin-bottom:3px;">${item.nome}</div>
                <div style="color:#8a7a5a; font-size:10px; letter-spacing:1px;">${renderDescricaoItem(item)}</div>
              </div>
              <div style="display:flex; align-items:center; gap:12px;">
                <span style="color:#c8a951; font-size:14px; font-weight:bold;">${item.preco} 🪙</span>
                <button onclick="comprarItem('${item.id}')"
                  ${!podeComprar || semDinheiro || inventarioCheio ? 'disabled' : ''}
                  style="background: transparent;
                    border: 1px solid ${!podeComprar || semDinheiro || inventarioCheio ? '#4a4a4a' : '#c8a951'};
                    color: ${!podeComprar || semDinheiro || inventarioCheio ? '#4a4a4a' : '#c8a951'};
                    font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: 2px;
                    padding: 6px 14px; cursor: pointer;">${!podeComprar ? 'RESTRITO' : semDinheiro ? 'SEM OURO' : inventarioCheio ? 'CHEIO' : 'COMPRAR'}</button>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  // Aplica tooltip a cada item da loja.
  overlay.querySelectorAll('[data-item-id]').forEach(el =>
    aplicarTooltipAoItem(el, el.dataset.itemId));
  requestAnimationFrame(() => { overlay.style.opacity = '1'; });
}

// Resolve o `shop` exato do servidor a partir do item.
// Ferreiro é dividido em ferreiro_weapon / ferreiro_armor (por tipo de item).
function _resolverShopServidor(item){
  switch(item.loja){
    case 'taverna': return 'taverna';
    case 'mercado': return 'mercador';
    case 'ferreiro':
      return (item.tipo === 'armadura' || item.tipo === 'escudo')
        ? 'ferreiro_armor' : 'ferreiro_weapon';
    default: return null;
  }
}

// Compra AUTORITATIVA: envia ao servidor pelo mesmo caminho do buyItem
// (mensagem shop_buy). O servidor revalida e atualiza bag/gear/gold; o cliente
// reflete via city_state/game_state. (Validações locais = só feedback rápido.)
function comprarItem(itemId){
  const heroi = GS.getHeroiAtivo();
  const item  = GS.CATALOGO_ITENS[itemId];
  if(!item){ console.error('Item não encontrado:', itemId); return; }

  // Feedback rápido (o servidor é a fonte da verdade e revalida)
  if(heroi.moedas < item.preco){
    GS.adicionarLog(`❌ ${heroi.name}: ouro insuficiente`);
    return;
  }
  const slotsLivres = heroi.inventario ? heroi.inventario.filter(s => s === null).length : 0;
  if(slotsLivres === 0){
    GS.adicionarLog(`❌ ${heroi.name}: inventário cheio`);
    return;
  }

  const shopKey = _resolverShopServidor(item);
  if(!shopKey){
    console.error('Shop não mapeado para loja:', item.loja);
    return;
  }

  // Mesmo formato do buyItem existente — caminho autoritativo do servidor.
  window._comprando = true;                       // compra em andamento
  send({ type: 'shop_buy', shop: shopKey, item_id: itemId });

  fecharLoja();   // reabre quando o servidor responder (city_state/erro)
  GS.adicionarLog(`🛒 Comprando ${item.nome}...`);
}

// Converte o bag[] do servidor para o inventario[] de tamanho fixo do cliente.
// Tenta casar o id no CATALOGO_ITENS; senão usa os dados do servidor (fallback).
function _converterBagParaInventario(bag, bagSize){
  const size = bagSize || 6;
  const inv  = new Array(size).fill(null);
  (bag || []).forEach((it, i) => {
    if(i >= size || !it) return;
    const cat = GS.CATALOGO_ITENS[it.id];
    inv[i] = cat ? { ...cat }
                 : { id: it.id, nome: it.name || it.id, tipo: it.tipo || it.type || 'item', ...it };
  });
  return inv;
}

// Sincroniza o herói do overlay (client-side) com o estado AUTORITATIVO do
// servidor (gold→moedas, bag→inventario). Chamado quando chega city_state.
function _sincronizarHeroiComServidor(serverPlayer){
  if(!serverPlayer || !GS.getHeroiAtivo) return;
  const heroi = GS.getHeroiAtivo();
  if(typeof serverPlayer.gold === 'number') heroi.moedas = serverPlayer.gold;
  if(Array.isArray(serverPlayer.bag))
    heroi.inventario = _converterBagParaInventario(serverPlayer.bag, serverPlayer.bag_size);
}

function fecharLoja(){
  window._lojaAtualAberta = null;   // limpa ao fechar
  const overlay = document.getElementById('loja-overlay');
  if(!overlay) return;
  overlay.style.opacity = '0';
  setTimeout(() => overlay.remove(), 300);
}

// Handlers de edifício (spec). Disponíveis para uso; os edifícios da cidade
// permanecem ligados à loja autoritativa do servidor (openShop) por _cityClick.
const onClicarFerreiro = () => abrirLoja('ferreiro', GS.getHeroiAtivo());
const onClicarTaverna  = () => abrirLoja('taverna',  GS.getHeroiAtivo());
const onClicarMercado  = () => abrirLoja('mercado',  GS.getHeroiAtivo());

// ═══════════════════════════════════════════════════════════════════════════
// TOOLTIP DE ITEM — sistema global reutilizável (loja, inventário, HUD).
// Lê GS.CATALOGO_ITENS. Aplicar em qualquer elemento de item via
// aplicarTooltipAoItem(elemento, itemId). (DOM → vive em game.js.)
// ═══════════════════════════════════════════════════════════════════════════
let _itemTooltipReady = false;
function _initItemTooltip(){
  if(_itemTooltipReady) return;
  _itemTooltipReady = true;
  let tooltip = document.getElementById('item-tooltip');
  if(!tooltip){
    tooltip = document.createElement('div');
    tooltip.id = 'item-tooltip';
    tooltip.style.cssText = `
      position: fixed; z-index: 999; width: 240px;
      background: rgba(8, 6, 4, 0.97);
      border: 1px solid #c8a951;
      font-family: 'Cinzel', serif;
      pointer-events: none; opacity: 0;
      transition: opacity 0.15s ease;
      box-shadow: 0 4px 24px rgba(0,0,0,0.8);
    `;
    document.body.appendChild(tooltip);
  }
  // Posiciona o tooltip perto do cursor (evita sair da tela).
  document.addEventListener('mousemove', (e) => {
    const t = document.getElementById('item-tooltip');
    if(!t || t.style.opacity === '0') return;
    const margin = 16;
    const rect = t.getBoundingClientRect();
    let x = e.clientX + margin;
    if(x + rect.width > window.innerWidth) x = e.clientX - rect.width - margin;
    let y = e.clientY + margin;
    if(y + rect.height > window.innerHeight) y = e.clientY - rect.height - margin;
    t.style.left = x + 'px';
    t.style.top  = y + 'px';
  });
}

function mostrarTooltip(itemId, event){
  _initItemTooltip();
  const item = GS.CATALOGO_ITENS[itemId];
  if(!item) return;
  const t = document.getElementById('item-tooltip');
  t.innerHTML = gerarConteudoTooltip(item);
  t.style.borderColor = corBordaPorPreco(item.preco);   // raridade por preço
  t.style.opacity = '1';
}

function esconderTooltip(){
  const t = document.getElementById('item-tooltip');
  if(t) t.style.opacity = '0';
  if(window._animadoHover){ window._animadoHover = null; if(GS.gameState) renderMap(GS.gameState); }
}

function renderLinhaTooltip(icone, label, valor){
  return `<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:5px; gap:8px;">
    <span style="color:#8a7a5a; font-size:10px; white-space:nowrap;">${icone} ${label}</span>
    <span style="color:#c8b89a; font-size:10px; text-align:right;">${valor}</span>
  </div>`;
}

function gerarConteudoTooltip(item){
  const coresTipo = {
    arma:          { cor:'#c8a951', label:'ARMA' },
    armaDistancia: { cor:'#c8a951', label:'ARMA À DISTÂNCIA' },
    armadura:      { cor:'#4a9eff', label:'ARMADURA' },
    escudo:        { cor:'#4a9eff', label:'ESCUDO' },
    secundario:    { cor:'#aaaaaa', label:'ACESSÓRIO' },
    consumivel:    { cor:'#2ecc40', label:'CONSUMÍVEL' },
    municao:       { cor:'#ff851b', label:'MUNIÇÃO' },
    varinha:       { cor:'#cc44ff', label:'VARINHA MÁGICA' },
    itemMagico:    { cor:'#cc44ff', label:'ITEM MÁGICO' }
  };
  const tipoInfo = coresTipo[item.tipo] || { cor:'#c8b89a', label:'ITEM' };
  const linhas = [];

  if(item.dano && item.dano !== '—') linhas.push(renderLinhaTooltip('🎲','Dano',item.dano));
  if(item.danoUmaMao){
    linhas.push(renderLinhaTooltip('🎲','1 mão',item.danoUmaMao));
    linhas.push(renderLinhaTooltip('🎲','2 mãos',item.danoDuasMaos));
  }
  const labelsAtributo = { forca:'Força', destreza:'Destreza', inteligencia:'Inteligência', carisma:'Carisma', forcaOuDestreza:'Força ou Destreza' };
  if(item.atributo) linhas.push(renderLinhaTooltip('📊','Atributo',labelsAtributo[item.atributo] || item.atributo));
  if(item.bonusCA) linhas.push(renderLinhaTooltip('🛡️','Bônus CA',`+${item.bonusCA}`));
  if(item.alcance) linhas.push(renderLinhaTooltip('📏','Alcance',`${item.alcance} quadrados`));
  if(item.alcanceEspecial) linhas.push(renderLinhaTooltip('📏','Alcance',item.alcanceEspecial.descricao));
  if(item.alcanceArremesso) linhas.push(renderLinhaTooltip('🎯','Arremesso',`${item.alcanceArremesso} quad. (diagonais incluídas)`));
  if(item.arremesso) linhas.push(renderLinhaTooltip('⚠️','Risco','Resultado 1 no d20 = arma destruída'));
  if(item.linhaVisao) linhas.push(renderLinhaTooltip('👁️','Linha de visão','Obrigatória para disparar'));
  if(item.tipo === 'arma') linhas.push(renderLinhaTooltip('🛡️','Escudo', item.escudo ? 'Permitido' : 'Não permitido'));
  if(item.duasMaos && !item.modosDuasMaos) linhas.push(renderLinhaTooltip('✋','Uso','Requer duas mãos'));
  if(item.modosDuasMaos) linhas.push(renderLinhaTooltip('✋','Uso','Uma ou duas mãos'));
  if(item.slotSecundario === 'flechas') linhas.push(renderLinhaTooltip('🏹','Munição','Requer flechas no slot secundário'));
  if(item.fome > 0) linhas.push(renderLinhaTooltip('🍖','Fome',`+${item.fome}`));
  if(item.sede > 0) linhas.push(renderLinhaTooltip('💧','Sede',`+${item.sede}`));
  if(item.duracao) linhas.push(renderLinhaTooltip('⏱️','Duração',`${item.duracao} rodadas`));
  if(item.bonusVisao) linhas.push(renderLinhaTooltip('👁️','Visão',`+${item.bonusVisao} quadrado`));
  if(item.quantidade) linhas.push(renderLinhaTooltip('📦','Quantidade',`${item.quantidade} unidades por slot`));
  if(item.slotsMagia) linhas.push(renderLinhaTooltip('✨','Slots de magia',`${item.slotsMagia}`));
  if(item.slotsExtras) linhas.push(renderLinhaTooltip('🎒','Slots extras',`+${item.slotsExtras} de inventário`));

  const especiais = gerarHabilidadesEspeciais(item);
  const nomesHerois = { victorCoiceBravo:'Victor', richardCavaleiro:'Richard', lewis:'Lewis', luccas:'Luccas', henrique:'Henrique', pedro:'Pedro' };
  const usuariosTexto = item.permitidoPara.includes('todos')
    ? 'Todos os heróis'
    : item.permitidoPara.map(k => nomesHerois[k] || k).join(', ');

  return `
    <div style="padding:10px 14px 8px; border-bottom:1px solid #c8a95133;">
      <div style="font-family:'Cinzel Decorative',serif; color:${tipoInfo.cor}; font-size:13px; margin-bottom:2px;">${item.nome}</div>
      <div style="color:${tipoInfo.cor}88; font-size:9px; letter-spacing:3px;">${tipoInfo.label}</div>
    </div>
    <div style="padding:10px 14px;">${linhas.join('')}</div>
    ${especiais ? `
      <div style="padding:8px 14px; border-top:1px solid #c8a95133; border-bottom:1px solid #c8a95133; background:rgba(200,169,81,0.05);">
        <div style="color:#c8a951; font-size:9px; letter-spacing:3px; margin-bottom:6px;">HABILIDADE ESPECIAL</div>
        ${especiais}
      </div>
    ` : ''}
    <div style="padding:8px 14px; border-top:1px solid #c8a95133;">
      <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px; margin-bottom:3px;">PODE USAR</div>
      <div style="color:#c8b89a; font-size:10px;">${usuariosTexto}</div>
    </div>
    <div style="padding:8px 14px; border-top:1px solid #c8a95133; display:flex; justify-content:space-between; align-items:center;">
      <span style="color:#8a7a5a; font-size:9px; letter-spacing:2px;">PREÇO</span>
      <span style="color:#c8a951; font-size:14px; font-weight:bold;">${item.preco} 🪙</span>
    </div>
  `;
}

function gerarHabilidadesEspeciais(item){
  const especiais = [];
  const L = (txt) => `<div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">${txt}</div>`;

  if(item.arremesso && item.id !== 'lanca_curta')   // lança tem bloco próprio (usa Força, não Destreza)
    especiais.push(L(`🎯 <strong style="color:#c8a951">Arremesso:</strong> Pode ser arremessada ${item.alcanceArremesso} quadrados em qualquer direção incluindo diagonais. Usa Destreza para acerto e dano. Resultado 1 no d20 = arma destruída permanentemente.`));
  if(item.id === 'chicote')
    especiais.push(L(`🔄 <strong style="color:#c8a951">Alcance Estendido:</strong> Atinge 2 quadrados adjacentes e 1 quadrado diagonal adjacente sem precisar se mover até o alvo.`));
  if(item.id === 'lanca_curta'){
    especiais.push(`
      <div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">
        🏹 <strong style="color:#44cc44">Arremesso:</strong>
        Pode ser arremessada até 3 quadrados em linha
        reta incluindo diagonais. Usa Força para acerto
        e dano (1d6 + FOR). Resultado 1 no d20 = lança
        destruída permanentemente.
      </div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">
        ↔️ <strong style="color:#c8a951">Alcance Lateral:</strong>
        No combate corpo a corpo atinge adjacente e
        casas laterais. Compatível com escudo.
      </div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.6;">
        ⚠️ <strong style="color:#ff4136">Atenção:</strong>
        Após o arremesso o slot de arma fica vazio.
        Equipe outra arma do inventário (ação livre, sem custo).
      </div>
    `);
  }
  if(item.id === 'lanca_longa' || item.id === 'alabarda')
    especiais.push(L(`📐 <strong style="color:#c8a951">Alcance Estendido:</strong> Atinge 2 casas adjacentes à frente e 1 casa diagonal adjacente. Requer duas mãos — incompatível com escudo.`));
  if(item.id === 'espada_bastarda')
    especiais.push(L(`⚔️ <strong style="color:#c8a951">Versátil:</strong> Uma mão: 1d10 de dano com escudo. Duas mãos: 3d4 de dano sem escudo. Troque o modo com ação bônus (-1 fome -1 sede).`));
  if(item.danoExtra)
    especiais.push(L(`🔥 <strong style="color:#ff6633">Incendiário:</strong> Adiciona ${item.danoExtra} de dano de fogo a cada disparo. Dano de fogo ignora bônus de CA de escudos.`));
  if(item.id === 'tocha')
    especiais.push(L(`🕯️ <strong style="color:#c8a951">Iluminação:</strong> Expande a linha de visão do personagem em 1 quadrado em todas as direções. Dura ${item.duracao} rodadas. Após expirar o slot fica vazio.`));
  if(item.tipo === 'varinha')
    especiais.push(L(`✨ <strong style="color:#cc44ff">Armazenamento de Magia:</strong> Guarda ${item.slotsMagia} magia(s) durante a campanha. Usar uma magia armazenada = ação bônus (-1 fome -1 sede). Não consome slot de magia do personagem. Recarregue na cidade.`));
  if(item.tipo === 'itemMagico' && item.slotsExtras)
    especiais.push(L(`🎒 <strong style="color:#cc44ff">Expansão de Inventário:</strong> Ocupa 1 slot mágico e adiciona permanentemente +${item.slotsExtras} slots ao inventário livre enquanto equipada.`));
  if(item.duasMaos && !item.modosDuasMaos && item.tipo === 'arma')
    especiais.push(L(`✋ <strong style="color:#c8a951">Duas Mãos:</strong> Incompatível com escudo ou 2ª arma. Equipar/trocar de equipamento é ação livre (sem custo).`));
  if (item.tipo === 'veneno') {
    const e = item.efeito || {};
    especiais.push(`
      <div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">
        ☠️ <strong style="color:#9900cc">Efeito:</strong>
        ${item.descricao}
      </div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">
        🎲 <strong style="color:#9900cc">Save:</strong>
        Fortitude dificuldade ${e.dificuldade}
        ${e.anula ? '— anula completamente' : '— efeito parcial no sucesso'}
      </div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.6;">
        🗡️ <strong style="color:#9900cc">Aplicação:</strong>
        Usar unta a arma equipada (ação bônus). O próximo golpe certeiro
        transfere o veneno ao alvo.
      </div>
    `);
  }
  if (item.id === 'adaga_secundaria') {
    especiais.push(`
      <div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">
        ⚔️ <strong style="color:#c8a951">Ataque Bônus:</strong>
        Equipe no slot secundário para um ataque extra
        adjacente como ação bônus. Usa Destreza para
        acerto e dano (1d4 + DEX). Sem penalidade.
      </div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;">
        🎯 <strong style="color:#c8a951">Arremesso Bônus:</strong>
        Pode ser arremessada como ação bônus até 3
        quadrados incluindo diagonais. Resultado 1 no
        d20 = adaga destruída permanentemente.
      </div>
      <div style="color:#c8b89a; font-size:10px; line-height:1.6;">
        🛡️ <strong style="color:#ff4136">Atenção:</strong>
        Ocupa o slot de escudo — incompatível com
        armas de duas mãos. Apenas Victor, Luccas
        e Henrique podem equipar.
      </div>
    `)
  }

  return especiais.length > 0 ? especiais.join('') : null;
}

// Aplica os eventos de tooltip a um elemento de item (loja/inventário/HUD).
function aplicarTooltipAoItem(elemento, itemId){
  if(!elemento || !itemId) return;
  elemento.addEventListener('mouseenter', (e) => mostrarTooltip(itemId, e));
  elemento.addEventListener('mouseleave', () => esconderTooltip());
}

// ── Tooltip de PERGAMINHO: nível de conjurador, dano/alcance/CD no nível e a
// chance de falha para o personagem ATUAL. Usa item.preview (vindo do servidor).
const _SAVE_LABEL_CLI = { reflexos:'Reflexos', fortitude:'Fortitude', vontade:'Vontade' };
function _chanceFalhaPergaminhoCli(item){
  const me = GS.me;
  if(!me) return null;
  if(me.class_id !== 'mage' && me.class_id !== 'cleric') return { naoPode:true };
  const nivel = item.nivel_conjurador || 1;
  const lvlPct = Math.min(95, Math.max(0, (nivel - (me.level||1))) * 15);
  const mg = (typeof GRIMORIO_CLIENT !== 'undefined') ? GRIMORIO_CLIENT[item.magia_id] : null;
  const classes = (mg && mg.classe) || [];
  const cross = classes.length > 0 && !classes.includes(me.class_id);
  return { lvlPct, cross };
}
function _tooltipPergaminhoHTML(item){
  const pv = item.preview || {};
  const mg = (typeof GRIMORIO_CLIENT !== 'undefined') ? GRIMORIO_CLIENT[item.magia_id] : null;
  const nomeMagia = (mg && mg.nome) || item.magia_id;
  const icone = (mg && mg.icone) || '📜';
  const circ = (item.circulo === 'primeiro' ? '1º' : item.circulo === 'segundo' ? '2º' : '3º');
  const linhas = [];
  linhas.push(renderLinhaTooltip('🧙','Conjurador', `Nível ${pv.nivel || item.nivel_conjurador || 1}`));
  if(item.int_bonus) linhas.push(renderLinhaTooltip('🧠','INT', `+${item.int_bonus} (CD/dano)`));
  if(pv.dano) linhas.push(renderLinhaTooltip('🎲','Dano', pv.dano + (pv.talento_dano ? ' ×1.5' : '')));
  if(pv.alcance != null)
    linhas.push(renderLinhaTooltip('📏','Alcance', pv.alcance === 0 ? 'no conjurador' : `${pv.alcance} quad.`));
  if(pv.area_raio) linhas.push(renderLinhaTooltip('💥','Área', `raio ${pv.area_raio}`));
  if(pv.cd != null) linhas.push(renderLinhaTooltip('🛡️','CD do save',
      `${pv.cd} (${_SAVE_LABEL_CLI[pv.save]||pv.save})${pv.talento_cd ? ' ⬆' : ''}`));
  if(!pv.dano && pv.efeito) linhas.push(renderLinhaTooltip('✨','Efeito', pv.efeito));
  else if(pv.duracao) linhas.push(renderLinhaTooltip('⏳','Duração',
      `${pv.duracao} rodada(s)${pv.talento_duracao ? ' +1' : ''}`));
  // Talentos do Pedro gravados no pergaminho.
  const tals = [];
  if(pv.talento_dano)    tals.push('Dano ×1.5');
  if(pv.talento_cd)      tals.push('CD +1');
  if(pv.talento_duracao) tals.push('Duração +1');
  if(tals.length) linhas.push(renderLinhaTooltip('✦','Talentos', tals.join(', ')));
  // Chance de falha para o personagem atual.
  const cf = _chanceFalhaPergaminhoCli(item);
  let falhaTxt;
  if(!cf) falhaTxt = '—';
  else if(cf.naoPode) falhaTxt = '<span style="color:#ff6b6b">só mago/clérigo</span>';
  else {
    falhaTxt = (cf.lvlPct > 0 ? `${cf.lvlPct}%` : 'nenhuma');
    if(cf.cross) falhaTxt += ' <span style="color:#ff6b6b">+50% classe</span>';
  }
  linhas.push(renderLinhaTooltip('🎯','Falha', falhaTxt));
  if(item.price != null) linhas.push(renderLinhaTooltip('💰','Preço', `${item.price} moedas`));
  return `
    <div style="padding:10px 12px;">
      <div style="color:#c8a951;font-size:13px;font-weight:700;margin-bottom:3px;">${icone} ${nomeMagia}</div>
      <div style="color:#8a7a5a;font-size:9px;letter-spacing:1px;margin-bottom:8px;">PERGAMINHO · ${circ} CÍRCULO</div>
      ${linhas.join('')}
    </div>`;
}
function aplicarTooltipPergaminho(elemento, item){
  if(!elemento || !item) return;
  elemento.addEventListener('mouseenter', () => {
    _initItemTooltip();
    const t = document.getElementById('item-tooltip');
    if(!t) return;
    t.innerHTML = _tooltipPergaminhoHTML(item);
    t.style.borderColor = corBordaPorPreco(item.price || 0);
    t.style.opacity = '1';
  });
  elemento.addEventListener('mouseleave', () => esconderTooltip());
}

// Cor da borda do tooltip por raridade (faixa de preço).
function corBordaPorPreco(preco){
  if(preco >= 300) return '#cc44ff'; // roxo — lendário
  if(preco >= 100) return '#4a9eff'; // azul — raro
  if(preco >= 40)  return '#2ecc40'; // verde — incomum
  return '#c8a951';                  // dourado — comum
}

function enterDungeon(){
  if(!GS.ws || GS.ws.readyState !== 1){
    toast('❌ Sem conexão com o servidor. Reinicie o iniciar.bat.', 'var(--red)');
    return;
  }
  send({type:'enter_dungeon'});
}

function handleGameState(msg){
  // GS._handle already updated GS.gameState, GS.isMyTurn, GS.pendingSkill
  syncDiceCanvas();
  renderMap(msg);
  centerOnPlayer(msg);
  renderPlayers(msg);
  renderMyPanel(msg);
  renderGMLog(msg.gm_log);
  updateTurnBadge(msg);
  updateMoveButtons(msg);
  renderObjectivesHUD(msg);
  _start2DHighlightLoop();
  renderStory();   // Fase 4b: abertura da fase (sobre o tabuleiro; não bloqueia)
}

// ── Fase 3: HUD de objetivos + botão "Libertar" (só em masmorra autorada) ─────
// Lê GS.objectives / GS.prisioneiroLibertavel (decisores em gameState.js).
const _OBJ_LABELS = {
  kill_all:        'Eliminar todos os monstros',
  kill_target:     'Derrotar o alvo',
  reach_exit:      'Chegar à saída',
  open_key_chest:  'Abrir o baú-chave',
  rescue_prisoner: 'Resgatar o prisioneiro',
};
function _objIcon(status){
  return status === 'done' ? '✅' : status === 'failed' ? '❌' : '⬜';
}
function _objRow(o){
  const label = _OBJ_LABELS[(o && o.type)] || (o && o.type) || 'Objetivo';
  return `<div class="obj-row"><span class="obj-ic">${_objIcon(o && o.status)}</span><span class="obj-lbl">${label}</span></div>`;
}
// Confirmação antes de encerrar a missão (itens largados podem ficar para trás).
// Usa um overlay próprio em vez de window.confirm(): o confirm nativo pode ser
// silenciosamente suprimido pelo navegador ("não permitir mais diálogos"),
// fazendo o botão parecer que "não funciona".
function encerrarMissaoConfirm(){
  if (document.getElementById('encerrar-missao-overlay')) return;   // já aberto
  const ov = document.createElement('div');
  ov.id = 'encerrar-missao-overlay';
  ov.style.cssText = 'position:fixed;inset:0;background:#000a;display:flex;'
    + 'align-items:center;justify-content:center;z-index:500;';
  ov.innerHTML =
    '<div style="background:rgba(28,20,6,0.98);border:1px solid var(--gold,#ffcc44);'
    + 'border-radius:12px;padding:22px 24px;max-width:340px;text-align:center;'
    + 'box-shadow:0 8px 30px #000b;">'
    + '<div style="color:var(--gold,#ffcc44);font-weight:700;font-size:1rem;margin-bottom:8px;">🏁 Encerrar missão?</div>'
    + '<div style="color:#e8dcc0;font-size:.82rem;line-height:1.4;margin-bottom:16px;">'
    + 'Pegue os itens de recompensa antes de encerrar. A missão será concluída e a campanha seguirá para a próxima aventura.</div>'
    + '<div style="display:flex;gap:10px;">'
    + '<button id="em-cancel" style="flex:1;padding:8px;border-radius:8px;border:1px solid #6a5a3a;'
    + 'background:rgba(40,32,16,0.9);color:#cbbe9c;font-weight:700;font-size:.78rem;cursor:pointer;">Cancelar</button>'
    + '<button id="em-ok" style="flex:1;padding:8px;border-radius:8px;border:1px solid var(--gold,#ffcc44);'
    + 'background:rgba(60,45,12,0.96);color:var(--gold,#ffcc44);font-weight:700;font-size:.78rem;cursor:pointer;">🏁 Encerrar</button>'
    + '</div></div>';
  const close = () => { if (ov.parentNode) ov.parentNode.removeChild(ov); };
  ov.addEventListener('click', e => { if (e.target === ov) close(); });
  document.body.appendChild(ov);
  document.getElementById('em-cancel').onclick = close;
  document.getElementById('em-ok').onclick = () => { close(); GS.encerrarMissao(); };
}
window.encerrarMissaoConfirm = encerrarMissaoConfirm;

function renderObjectivesHUD(msg){
  const hud = $('objectives-hud');
  const btn = $('btn-libertar');
  if(!hud) return;
  const obj = GS.objectives;   // null no procedural
  if(!obj){
    hud.style.display = 'none';
    if(btn) btn.style.display = 'none';
    return;
  }
  let html = '';
  const camp = GS.campaign;   // {name, phase, total} em campanha; null caso contrário
  if(camp){
    html += `<div class="obj-campaign">🗺️ Fase ${camp.phase} de ${camp.total} — ${camp.name}</div>`;
  }
  html += '<div class="obj-title">🎯 Objetivos</div>';
  if(obj.primary) html += `<div class="obj-primary">${_objRow(obj.primary)}</div>`;
  const secs = obj.secondary || [];
  if(secs.length){
    html += '<div class="obj-sec-label">Secundários</div>';
    for(const s of secs) html += _objRow(s);
  }
  if (GS.missionCompletePending) {
    html += `<button class="btn-encerrar-missao" onclick="encerrarMissaoConfirm()">🏁 Encerrar missão</button>`;
  }
  hud.innerHTML = html;
  hud.style.display = '';
  // Botão "Libertar": só quando há prisioneiro cativo adjacente no meu turno.
  if(btn) btn.style.display = GS.prisioneiroLibertavel ? '' : 'none';
}

function _start2DHighlightLoop(){
  if(_2dHighlightFrame || mode3D) return;
  function step(){
    const st = GS.gameState;
    const me = st && st.players.find(p => p.id === GS.myPid && p.alive);
    if(!mode3D && GS.isMyTurn && me && me.moves_left > 0 && st){
      _movePulse = 0.5 + 0.5 * Math.sin(Date.now() / 420);
      renderMap(st);
      _2dHighlightFrame = requestAnimationFrame(step);
    } else {
      _movePulse = 0.5;
      _2dHighlightFrame = null;
    }
  }
  _2dHighlightFrame = requestAnimationFrame(step);
}

function updateTurnBadge(msg){
  $('round-badge').textContent = `Rodada ${msg.round}`;
  // Turno dos servos (logo após o mago): destaca em roxo.
  if(msg.animados_turn){
    const owner = msg.players.find(p=>p.id===msg.animados_turn);
    $('turn-badge').textContent = owner ? `💀 Servos de ${owner.name}` : '💀 Servos';
    $('turn-badge').style.background = '#9900cc';
    $('turn-badge').style.color = '#fff';
    return;
  }
  const cur = msg.players.find(p=>p.id===msg.current_turn);
  // Deixa explícito de quem o grupo está esperando — antes só o nome aparecia
  // e novatos não sabiam se era a vez deles.
  if(cur && cur.id === GS.myPid){
    $('turn-badge').textContent = `▶ SUA VEZ — ${cur.emoji} ${cur.name}`;
  } else {
    $('turn-badge').textContent = cur ? `⏳ Aguardando ${cur.emoji} ${cur.name}...` : '—';
  }
  $('turn-badge').style.background = cur ? cur.color : 'var(--gold)';
  $('turn-badge').style.color = '#fff';
  updateTurnTimer(msg);
}

// ── Timer de 30s por turno ──────────────────────────────────────────────────
// O servidor é autoridade (encerra o turno aos 30s). Aqui só exibimos a contagem
// regressiva. Detectamos um turno NOVO pela mudança de `turn_timer_started`
// (epoch do servidor) e contamos localmente — assim evitamos desvio de relógio
// e não reiniciamos a cada push de estado dentro do mesmo turno.
let _ttState = { key:null, remaining:0, interval:null };
function _ttClear(){ if(_ttState.interval){ clearInterval(_ttState.interval); _ttState.interval=null; } }
function _ttRender(){
  const b = document.getElementById('turn-timer-badge'); if(!b) return;
  const s = _ttState.remaining;
  b.textContent = `⏳ ${s}s`;
  b.style.background = s<=10 ? '#c0392b' : '#2a2a2a';
  b.style.color = '#fff';
}
function updateTurnTimer(msg){
  const b = document.getElementById('turn-timer-badge'); if(!b) return;
  const active = msg.phase === 'playing' && msg.current_turn && msg.turn_timer_started;
  if(!active){ _ttClear(); _ttState.key=null; b.style.display='none'; return; }
  const limit = msg.turn_timer_limit || 30;
  if(msg.turn_timer_started !== _ttState.key){   // turno novo → reinicia a contagem
    _ttState.key = msg.turn_timer_started;
    _ttState.remaining = limit;
    _ttClear();
    _ttState.interval = setInterval(()=>{
      _ttState.remaining = Math.max(0, _ttState.remaining - 1);
      _ttRender();
      if(_ttState.remaining <= 0) _ttClear();
    }, 1000);
  }
  b.style.display = '';
  _ttRender();
}

function updateMoveButtons(msg){
  // Arrow buttons removed — movement is click-to-move only
}

// BFS helpers live in GS (gameState.js) — alias for brevity in render code
const bfsReachable = (...a) => GS.bfsReachable(...a);
const findPath     = (...a) => GS.findPath(...a);

// Center the map wrap on the player — runs inside rAF so canvas resize never beats it
function centerOnPlayer(state){
  if(mode3D) return;   // 3D camera handles its own view; 2D pixel offsets don't apply
  const me=state.players.find(p=>p.id===GS.myPid&&p.alive);
  if(!me) return;
  const wrap=$('map-wrap');
  const tl=Math.max(0, me.pos[0]*CELL+CELL/2 - wrap.clientWidth/2);
  const tt=Math.max(0, me.pos[1]*CELL+CELL/2 - wrap.clientHeight/2);
  requestAnimationFrame(()=>{ wrap.scrollLeft=tl; wrap.scrollTop=tt; });
}

// ══ WEAPON ICONS ═══════════════════════════════════════════════════════════

function drawWeapon(ctx, id, cx, cy){
  ctx.save(); ctx.translate(cx, cy);
  switch(id){
    case 'longsword':     _wLongsword(ctx);    break;
    case 'shortsword':    _wShortsword(ctx);   break;
    case 'staff':         _wStaff(ctx);        break;
    case 'bordao':        _wBordao(ctx);       break;
    case 'dagger':        _wDagger(ctx);       break;
    case 'warhammer':     _wWarhammer(ctx);    break;
    case 'longbow':       _wLongbow(ctx);      break;
    case 'hand_crossbow': _wHandCrossbow(ctx); break;
    case 'bastsword':     _wBastSword(ctx);    break;
    default:              _wLongsword(ctx);
  }
  ctx.restore();
}

function _wLongsword(ctx){
  // Blade
  ctx.fillStyle='#c4cdd8';
  ctx.beginPath(); ctx.moveTo(0,-23); ctx.lineTo(-3,-6); ctx.lineTo(-3,7); ctx.lineTo(3,7); ctx.lineTo(3,-6); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#7888a0'; ctx.lineWidth=0.6; ctx.stroke();
  // Groove
  ctx.strokeStyle='rgba(255,255,255,0.45)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0,-21); ctx.lineTo(0,5); ctx.stroke();
  // Crossguard
  ctx.fillStyle='#b08840'; ctx.fillRect(-10,6,20,3);
  // Grip
  ctx.fillStyle='#4a2e14'; ctx.fillRect(-2.5,9,5,12);
  ctx.strokeStyle='#c09040'; ctx.lineWidth=0.9;
  for(let i=0;i<3;i++){ ctx.beginPath(); ctx.moveTo(-2.5,11+i*3.5); ctx.lineTo(2.5,11+i*3.5); ctx.stroke(); }
  // Pommel
  ctx.fillStyle='#b08840'; ctx.beginPath(); ctx.ellipse(0,22,4,3,0,0,Math.PI*2); ctx.fill();
}

function _wStaff(ctx){
  // Shaft — stays within 44×68 canvas (center at 22,34)
  ctx.fillStyle='#6e4c28'; ctx.fillRect(-2,-16,4,34);
  ctx.strokeStyle='#9a7040'; ctx.lineWidth=0.5; ctx.strokeRect(-2,-16,4,34);
  // Bindings
  ctx.strokeStyle='#d0a040'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(-2,-10); ctx.lineTo(2,-10); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-2,-8);  ctx.lineTo(2,-8);  ctx.stroke();
  // Orb — positioned to stay within canvas top (y=-28 from center means y=6 from top — OK)
  ctx.fillStyle='#6030b8'; ctx.beginPath(); ctx.ellipse(0,-20,7,8,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#9050e0'; ctx.lineWidth=1; ctx.stroke();
  // Orb highlight
  ctx.fillStyle='rgba(255,255,255,0.35)'; ctx.beginPath(); ctx.ellipse(-2.5,-22,2.5,2,0,0,Math.PI*2); ctx.fill();
  // Glow ring (max y reach: -20+9=-29 → canvas y=34-29=5 — just inside)
  ctx.strokeStyle='rgba(180,100,255,0.5)'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.ellipse(0,-20,9,10,0,0,Math.PI*2); ctx.stroke();
}

function _wDagger(ctx){
  // Blade
  ctx.fillStyle='#c4cdd8';
  ctx.beginPath(); ctx.moveTo(0,-20); ctx.lineTo(-2.5,-4); ctx.lineTo(2.5,-4); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#7888a0'; ctx.lineWidth=0.6; ctx.stroke();
  ctx.strokeStyle='rgba(255,255,255,0.45)'; ctx.lineWidth=0.9;
  ctx.beginPath(); ctx.moveTo(0,-18); ctx.lineTo(0,-5); ctx.stroke();
  // Guard
  ctx.fillStyle='#8890a0'; ctx.fillRect(-7,-5,14,2.5);
  // Grip
  ctx.fillStyle='#2a1a08'; ctx.fillRect(-2,-3,4,11);
  ctx.strokeStyle='#d0a040'; ctx.lineWidth=0.9;
  for(let i=0;i<3;i++){ ctx.beginPath(); ctx.moveTo(-2,-1+i*3.2); ctx.lineTo(2,-1+i*3.2); ctx.stroke(); }
  // Pommel
  ctx.fillStyle='#8890a0'; ctx.beginPath(); ctx.ellipse(0,10,3.5,2.5,0,0,Math.PI*2); ctx.fill();
}

function _wWarhammer(ctx){
  // Handle
  ctx.fillStyle='#5c3a1e'; ctx.fillRect(-2,-14,4,30);
  ctx.strokeStyle='#8a6040'; ctx.lineWidth=0.5;
  // Bindings
  ctx.strokeStyle='#d0a040'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(-2,10); ctx.lineTo(2,10); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-2,12); ctx.lineTo(2,12); ctx.stroke();
  // Hammer head
  ctx.fillStyle='#6a6878'; ctx.fillRect(-9,-20,18,10);
  ctx.strokeStyle='#9090a8'; ctx.lineWidth=0.7; ctx.strokeRect(-9,-20,18,10);
  ctx.fillStyle='rgba(255,255,255,0.12)'; ctx.fillRect(-8,-19,16,2);
  // Top spike (y=-26 from center = canvas y=8 — fits in 68px)
  ctx.fillStyle='#505060';
  ctx.beginPath(); ctx.moveTo(0,-26); ctx.lineTo(-3,-20); ctx.lineTo(3,-20); ctx.closePath(); ctx.fill();
}

function _wLongbow(ctx){
  // Bow stave
  ctx.strokeStyle='#7a5430'; ctx.lineWidth=3;
  ctx.beginPath(); ctx.moveTo(0,-22); ctx.bezierCurveTo(15,-10,15,10,0,22); ctx.stroke();
  // String
  ctx.strokeStyle='#d8c888'; ctx.lineWidth=0.9;
  ctx.beginPath(); ctx.moveTo(0,-22); ctx.lineTo(0,22); ctx.stroke();
  // Arrow shaft
  ctx.strokeStyle='#9a7840'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0,-8); ctx.lineTo(0,18); ctx.stroke();
  // Arrowhead
  ctx.fillStyle='#a8b8c8';
  ctx.beginPath(); ctx.moveTo(0,-12); ctx.lineTo(-2.5,-8); ctx.lineTo(2.5,-8); ctx.closePath(); ctx.fill();
  // Fletching
  ctx.strokeStyle='#c84040'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0,18); ctx.lineTo(-3,14); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0,18); ctx.lineTo(3,14); ctx.stroke();
}

function _wBastSword(ctx){
  // Wide blade
  ctx.fillStyle='#b8c0d0';
  ctx.beginPath(); ctx.moveTo(0,-25); ctx.lineTo(-5,-4); ctx.lineTo(-4.5,8); ctx.lineTo(4.5,8); ctx.lineTo(5,-4); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#7080a0'; ctx.lineWidth=0.6; ctx.stroke();
  ctx.strokeStyle='rgba(255,255,255,0.4)'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(0,-23); ctx.lineTo(0,6); ctx.stroke();
  // Large crossguard
  ctx.fillStyle='#b09040'; ctx.fillRect(-13,7,26,4);
  ctx.strokeStyle='#d0b060'; ctx.lineWidth=0.6; ctx.strokeRect(-13,7,26,4);
  // Two-handed grip
  ctx.fillStyle='#3a2010'; ctx.fillRect(-3,11,6,14);
  ctx.strokeStyle='#c09040'; ctx.lineWidth=0.9;
  for(let i=0;i<3;i++){ ctx.beginPath(); ctx.moveTo(-3,13+i*4); ctx.lineTo(3,13+i*4); ctx.stroke(); }
  // Pommel
  ctx.fillStyle='#b09040'; ctx.beginPath(); ctx.ellipse(0,26,5.5,4,0,0,Math.PI*2); ctx.fill();
}

// ── Short sword (like longsword but smaller blade)
function _wShortsword(ctx){
  // Blade — shorter and slightly wider than longsword
  ctx.fillStyle='#c4cdd8';
  ctx.beginPath(); ctx.moveTo(0,-17); ctx.lineTo(-3.5,-4); ctx.lineTo(-3,7); ctx.lineTo(3,7); ctx.lineTo(3.5,-4); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#7888a0'; ctx.lineWidth=0.6; ctx.stroke();
  // Fuller groove
  ctx.strokeStyle='rgba(255,255,255,0.45)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0,-15); ctx.lineTo(0,5); ctx.stroke();
  // Crossguard
  ctx.fillStyle='#b08840'; ctx.fillRect(-9,6,18,3);
  // Grip
  ctx.fillStyle='#4a2e14'; ctx.fillRect(-2.5,9,5,10);
  ctx.strokeStyle='#c09040'; ctx.lineWidth=0.9;
  for(let i=0;i<2;i++){ ctx.beginPath(); ctx.moveTo(-2.5,11+i*3.8); ctx.lineTo(2.5,11+i*3.8); ctx.stroke(); }
  // Pommel
  ctx.fillStyle='#b08840'; ctx.beginPath(); ctx.ellipse(0,20,3.5,2.5,0,0,Math.PI*2); ctx.fill();
}

// ── Bordão / Quarterstaff — simple thick walking staff with iron tips
function _wBordao(ctx){
  // Main shaft
  ctx.fillStyle='#7a5c30'; ctx.fillRect(-2.5,-24,5,48);
  ctx.strokeStyle='#a07840'; ctx.lineWidth=0.5; ctx.strokeRect(-2.5,-24,5,48);
  // Wood grain lines
  ctx.strokeStyle='rgba(0,0,0,0.18)'; ctx.lineWidth=0.7;
  for(let y=-20;y<24;y+=7){ ctx.beginPath(); ctx.moveTo(-2,y); ctx.lineTo(2,y+2); ctx.stroke(); }
  // Iron cap top
  ctx.fillStyle='#808898'; ctx.fillRect(-3.5,-26,7,5);
  ctx.strokeStyle='#a0a8b0'; ctx.lineWidth=0.6; ctx.strokeRect(-3.5,-26,7,5);
  // Iron cap bottom
  ctx.fillStyle='#808898'; ctx.fillRect(-3.5,21,7,5);
  ctx.strokeStyle='#a0a8b0'; ctx.lineWidth=0.6; ctx.strokeRect(-3.5,21,7,5);
  // Bindings in middle
  ctx.strokeStyle='#c0a030'; ctx.lineWidth=1.4;
  for(const y of [-6,-3,0,3,6]){ ctx.beginPath(); ctx.moveTo(-3,y); ctx.lineTo(3,y); ctx.stroke(); }
}

// ── Hand Crossbow — compact crossbow with short tiller
function _wHandCrossbow(ctx){
  // Tiller (stock) — horizontal
  ctx.fillStyle='#5c3a18'; ctx.fillRect(-18,-2,26,6);
  ctx.strokeStyle='#8a5830'; ctx.lineWidth=0.6; ctx.strokeRect(-18,-2,26,6);
  // Prod (bow arms) — vertical centered
  ctx.strokeStyle='#6B4226'; ctx.lineWidth=4; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(-2,-16); ctx.lineTo(-2,16); ctx.stroke();
  // String
  ctx.strokeStyle='rgba(220,210,180,0.9)'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.moveTo(-2,-16); ctx.lineTo(8,1); ctx.lineTo(-2,16); ctx.stroke();
  // Bolt / quarrel
  ctx.strokeStyle='#9a7840'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(-16,1); ctx.lineTo(5,1); ctx.stroke();
  // Bolt tip
  ctx.fillStyle='#a8b8c8';
  ctx.beginPath(); ctx.moveTo(5,-1.5); ctx.lineTo(10,1); ctx.lineTo(5,3.5); ctx.closePath(); ctx.fill();
  // Trigger guard
  ctx.strokeStyle='#a08050'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(-2,4); ctx.quadraticCurveTo(2,12,-6,12); ctx.quadraticCurveTo(-10,12,-10,4); ctx.stroke();
  // Handle/grip
  ctx.fillStyle='#4a2e14'; ctx.fillRect(-12,3,6,14);
  ctx.strokeStyle='#c09040'; ctx.lineWidth=0.8;
  for(let i=0;i<3;i++){ ctx.beginPath(); ctx.moveTo(-12,5+i*4); ctx.lineTo(-6,5+i*4); ctx.stroke(); }
}

// ══ ARMOR ICONS ════════════════════════════════════════════════════════════

function drawArmor(ctx, id, cx, cy){
  ctx.save(); ctx.translate(cx, cy);
  switch(id){
    case 'plate':     _aPlate(ctx);    break;
    case 'robes':     _aRobes(ctx);    break;
    case 'leather':   _aLeather(ctx);  break;
    case 'chainmail': _aChainmail(ctx);break;
    case 'fullplate': _aFullPlate(ctx);break;
    case 'cloak':     _aCloak(ctx);    break;
    case 'none':      _aNoArmor(ctx);  break;
    default:          _aNoArmor(ctx);
  }
  ctx.restore();
}

// No armor — simple tunic outline with "10" CA marker
function _aNoArmor(ctx){
  // Simple cloth tunic
  ctx.fillStyle='#3a3020';
  ctx.beginPath();
  ctx.moveTo(-11,-16); ctx.lineTo(11,-16);
  ctx.lineTo(13,20); ctx.lineTo(-13,20);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#6a5838'; ctx.lineWidth=0.8; ctx.stroke();
  // Collar V
  ctx.strokeStyle='#8a7040'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(-5,-16); ctx.lineTo(0,-10); ctx.lineTo(5,-16); ctx.stroke();
  // Simple seam
  ctx.strokeStyle='rgba(255,255,255,0.1)'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.moveTo(0,-10); ctx.lineTo(0,18); ctx.stroke();
  // Fabric folds
  ctx.strokeStyle='rgba(0,0,0,0.25)'; ctx.lineWidth=0.6;
  for(const y of [-4,4,12]){
    ctx.beginPath(); ctx.moveTo(-10,y); ctx.lineTo(10,y); ctx.stroke();
  }
  // Belt
  ctx.fillStyle='#7a6030'; ctx.fillRect(-9,9,18,3);
  ctx.strokeStyle='#c0a040'; ctx.lineWidth=0.6; ctx.strokeRect(-9,9,18,3);
  // "CA 10" text label
  ctx.fillStyle='rgba(180,160,100,0.85)'; ctx.font='bold 7px monospace';
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText('CA 10',0,-24);
}

// Robe (mage) — purple flowing robe with arcane stars
function _aRobes(ctx){
  // Main body — trapezoid
  ctx.fillStyle='#3a1860';
  ctx.beginPath();
  ctx.moveTo(-12,-16); ctx.lineTo(12,-16);
  ctx.lineTo(17,22); ctx.lineTo(-17,22);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#6a30b0'; ctx.lineWidth=0.8; ctx.stroke();
  // Collar
  ctx.fillStyle='#28104a';
  ctx.beginPath();
  ctx.moveTo(-7,-16); ctx.quadraticCurveTo(0,-20,7,-16);
  ctx.quadraticCurveTo(3,-10,0,-8); ctx.quadraticCurveTo(-3,-10,-7,-16);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#9050e0'; ctx.lineWidth=0.6; ctx.stroke();
  // Arcane stars
  ctx.fillStyle='#e0c040';
  for(const [sx,sy] of [[-6,-4],[7,-2],[0,4],[-8,11],[8,13],[1,-10]]){
    ctx.beginPath(); ctx.arc(sx,sy,1.4,0,Math.PI*2); ctx.fill();
  }
  // Belt
  ctx.fillStyle='#7040a0'; ctx.fillRect(-11,8,22,3);
  ctx.strokeStyle='#c080f0'; ctx.lineWidth=0.5; ctx.strokeRect(-11,8,22,3);
  // Belt buckle
  ctx.fillStyle='#d0a030'; ctx.fillRect(-3,7,6,5);
  ctx.strokeStyle='#f0c040'; ctx.lineWidth=0.6; ctx.strokeRect(-3,7,6,5);
}

// Leather (rogue/ranger) — brown vest with rivets
function _aLeather(ctx){
  ctx.fillStyle='#6b3e1e';
  ctx.beginPath();
  ctx.moveTo(-12,-17); ctx.lineTo(12,-17);
  ctx.lineTo(14,20); ctx.lineTo(-14,20);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#9a6030'; ctx.lineWidth=0.8; ctx.stroke();
  // Shoulder straps
  ctx.fillStyle='#8b5226';
  ctx.fillRect(-12,-17,5,9); ctx.fillRect(7,-17,5,9);
  ctx.strokeStyle='#6a3015'; ctx.lineWidth=0.5;
  ctx.strokeRect(-12,-17,5,9); ctx.strokeRect(7,-17,5,9);
  // Center seam
  ctx.strokeStyle='#4a2808'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(0,-17); ctx.lineTo(0,20); ctx.stroke();
  // Stud rivets
  ctx.fillStyle='#c8b860';
  for(const [rx,ry] of [[-7,-10],[7,-10],[-7,-1],[7,-1],[-7,8],[7,8]]){
    ctx.beginPath(); ctx.arc(rx,ry,1.5,0,Math.PI*2); ctx.fill();
  }
  // Belt
  ctx.fillStyle='#c0a030'; ctx.fillRect(-9,11,18,3);
  ctx.strokeStyle='#e0c040'; ctx.lineWidth=0.5; ctx.strokeRect(-9,11,18,3);
  // Buckle
  ctx.strokeStyle='#f0d040'; ctx.lineWidth=1;
  ctx.strokeRect(-4,10,8,5);
}

// Chainmail (cleric) — metal rings with holy cross
function _aChainmail(ctx){
  ctx.fillStyle='#585870';
  ctx.beginPath();
  ctx.moveTo(-13,-17); ctx.lineTo(13,-17);
  ctx.lineTo(15,20); ctx.lineTo(-15,20);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#8080a0'; ctx.lineWidth=0.7; ctx.stroke();
  // Chain ring pattern
  ctx.strokeStyle='#9898b8'; ctx.lineWidth=0.7;
  for(let row=0;row<7;row++){
    for(let col=0;col<5;col++){
      const bx=-10+col*5+(row%2)*2.5;
      const by=-14+row*5;
      ctx.beginPath(); ctx.ellipse(bx,by,2.1,1.4,0,0,Math.PI*2); ctx.stroke();
    }
  }
  // Shoulder guards
  ctx.strokeStyle='#a0a0c0'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.ellipse(-13,-12,5,7,-0.3,0,Math.PI*2); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(13,-12,5,7,0.3,0,Math.PI*2); ctx.stroke();
  // Holy cross symbol
  ctx.strokeStyle='#f0c040'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(0,-8); ctx.lineTo(0,6); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-5,0); ctx.lineTo(5,0); ctx.stroke();
}

// Plate (warrior) — steel breastplate with pauldrons
function _aPlate(ctx){
  // Breastplate body
  ctx.fillStyle='#6878a8';
  ctx.beginPath();
  ctx.moveTo(-13,-17); ctx.lineTo(13,-17);
  ctx.lineTo(15,18); ctx.lineTo(-15,18);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#9090c8'; ctx.lineWidth=0.8; ctx.stroke();
  // Metal sheen highlight
  ctx.fillStyle='rgba(255,255,255,0.14)';
  ctx.fillRect(-11,-16,22,5);
  // Center ridge
  ctx.strokeStyle='#a8b0d0'; ctx.lineWidth=1.4;
  ctx.beginPath(); ctx.moveTo(0,-15); ctx.lineTo(0,16); ctx.stroke();
  // Horizontal plates
  ctx.strokeStyle='#8888b0'; ctx.lineWidth=0.9;
  for(const y of [-7,1,9]){
    ctx.beginPath(); ctx.moveTo(-12,y); ctx.lineTo(12,y); ctx.stroke();
  }
  // Pauldrons (shoulders)
  ctx.fillStyle='#5870a0';
  ctx.beginPath(); ctx.ellipse(-15,-12,6,9,-0.2,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#8090c0'; ctx.lineWidth=0.7; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(15,-12,6,9,0.2,0,Math.PI*2); ctx.fill(); ctx.stroke();
  // Collar
  ctx.strokeStyle='#c0c8e8'; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.arc(0,-17,6,Math.PI,0); ctx.stroke();
}

// Full plate (paladin) — ornate with holy symbol
function _aFullPlate(ctx){
  // Breastplate
  ctx.fillStyle='#4060c0';
  ctx.beginPath();
  ctx.moveTo(-14,-18); ctx.lineTo(14,-18);
  ctx.lineTo(16,19); ctx.lineTo(-16,19);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#7090e0'; ctx.lineWidth=0.8; ctx.stroke();
  // Gold top trim
  ctx.fillStyle='#d0a030'; ctx.fillRect(-14,-18,28,4);
  // Center ridge
  ctx.strokeStyle='#90b0f8'; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.moveTo(0,-14); ctx.lineTo(0,17); ctx.stroke();
  // Horizontal bands
  ctx.strokeStyle='#6080c0'; ctx.lineWidth=0.9;
  for(const y of [-6,2,10]){
    ctx.beginPath(); ctx.moveTo(-13,y); ctx.lineTo(13,y); ctx.stroke();
  }
  // Large pauldrons (gold-trimmed)
  ctx.fillStyle='#3050b0';
  ctx.beginPath(); ctx.ellipse(-16,-13,7,10,-0.2,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#7090d8'; ctx.lineWidth=0.7; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(16,-13,7,10,0.2,0,Math.PI*2); ctx.fill(); ctx.stroke();
  ctx.strokeStyle='#d0a030'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.ellipse(-16,-13,7,10,-0.2,0,Math.PI*2); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(16,-13,7,10,0.2,0,Math.PI*2); ctx.stroke();
  // Sun/cross holy symbol
  ctx.strokeStyle='#f8d840'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(0,-8); ctx.lineTo(0,9); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-6,1); ctx.lineTo(6,1); ctx.stroke();
  ctx.strokeStyle='#f8d840'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.arc(0,1,7,0,Math.PI*2); ctx.stroke();
  // Collar
  ctx.strokeStyle='#d0a030'; ctx.lineWidth=1.8;
  ctx.beginPath(); ctx.arc(0,-18,7,Math.PI,0); ctx.stroke();
}

// Cloak (mage/ranger) — hooded travel cloak, dark with silver clasp
function _aCloak(ctx){
  // Main cloak body — flowing trapezoid
  ctx.fillStyle='#1e1430';
  ctx.beginPath();
  ctx.moveTo(-14,-16); ctx.lineTo(14,-16);
  ctx.lineTo(18,22); ctx.lineTo(-18,22);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#3a2858'; ctx.lineWidth=0.8; ctx.stroke();
  // Hood opening
  ctx.fillStyle='#110c20';
  ctx.beginPath();
  ctx.moveTo(-8,-16); ctx.quadraticCurveTo(0,-24,8,-16);
  ctx.quadraticCurveTo(4,-12,0,-10); ctx.quadraticCurveTo(-4,-12,-8,-16);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#5040a0'; ctx.lineWidth=0.6; ctx.stroke();
  // Cloak fold lines
  ctx.strokeStyle='rgba(255,255,255,0.06)'; ctx.lineWidth=1;
  for(const [x1,y1,x2,y2] of [[-4,-14,-6,20],[4,-14,6,20],[0,-12,0,22]]){
    ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
  }
  // Silver clasp at neck
  ctx.fillStyle='#c0c8d8'; ctx.beginPath(); ctx.ellipse(0,-13,4,3,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#e0e8f0'; ctx.lineWidth=0.7; ctx.stroke();
  ctx.fillStyle='rgba(255,255,255,0.5)'; ctx.beginPath(); ctx.arc(-1,-14,1,0,Math.PI*2); ctx.fill();
  // Hem trim (faint silver border at bottom)
  ctx.strokeStyle='rgba(160,140,220,0.4)'; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(-17,20); ctx.lineTo(17,20); ctx.stroke();
}

// ══ SPRITE ENGINE ══════════════════════════════════════════════════════════

function _cl(hex, f) {
  const r=parseInt(hex.slice(1,3),16), g=parseInt(hex.slice(3,5),16), b=parseInt(hex.slice(5,7),16);
  return `rgb(${Math.min(255,r*f|0)},${Math.min(255,g*f|0)},${Math.min(255,b*f|0)})`;
}

function rr(ctx,x,y,w,h,r=3){
  ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
}

function drawFace(ctx, hx, hy, skin){
  // Head oval
  ctx.fillStyle=skin;
  ctx.beginPath(); ctx.ellipse(hx,hy,7.5,8.5,0,0,Math.PI*2); ctx.fill();
  // Face shading gradient
  const fg=ctx.createLinearGradient(hx-6,hy-8,hx+5,hy+9);
  fg.addColorStop(0,'rgba(255,255,255,0.25)'); fg.addColorStop(0.5,'rgba(0,0,0,0)'); fg.addColorStop(1,'rgba(0,0,0,0.28)');
  ctx.fillStyle=fg; ctx.beginPath(); ctx.ellipse(hx,hy,7.5,8.5,0,0,Math.PI*2); ctx.fill();
  // Outline
  ctx.strokeStyle='rgba(0,0,0,0.30)'; ctx.lineWidth=0.7; ctx.stroke();
  // Eye whites
  ctx.fillStyle='#faf4ee'; ctx.fillRect(hx-4.2,hy-2.2,3.2,2.4); ctx.fillRect(hx+1,hy-2.2,3.2,2.4);
  // Pupils
  ctx.fillStyle='#181820';
  ctx.beginPath(); ctx.arc(hx-2.7,hy-0.9,1.2,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.arc(hx+2.5,hy-0.9,1.2,0,Math.PI*2); ctx.fill();
  // Specular highlight
  ctx.fillStyle='rgba(255,255,255,0.92)';
  ctx.beginPath(); ctx.arc(hx-3.2,hy-1.4,0.55,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.arc(hx+2.0,hy-1.4,0.55,0,Math.PI*2); ctx.fill();
  // Nose shadow
  ctx.fillStyle='rgba(0,0,0,0.13)'; ctx.beginPath(); ctx.arc(hx,hy+1.8,1.5,0,Math.PI*2); ctx.fill();
}

function drawLegs(ctx, lc){
  ctx.fillStyle=lc; rr(ctx,-8,6,5,14,2); ctx.fill(); rr(ctx,3,6,5,14,2); ctx.fill();
  // Leg highlight
  ctx.fillStyle='rgba(255,255,255,0.13)'; ctx.fillRect(-7.5,7,2.5,12); ctx.fillRect(3.5,7,2.5,12);
  // Leg shadow
  ctx.fillStyle='rgba(0,0,0,0.18)'; ctx.fillRect(-4,7,1.5,12); ctx.fillRect(7,7,1.5,12);
}

// ── Hero class sprites (drawn at origin = tile center) ─────────────────────

function drawWarrior(ctx, color){
  // ── Plate greaves (legs hidden by skirt of armor)
  ctx.fillStyle='#8898b2'; rr(ctx,-7,9,5,11,2); ctx.fill(); rr(ctx,2,9,5,11,2); ctx.fill();
  const lgG=ctx.createLinearGradient(-7,9,2,20); lgG.addColorStop(0,'rgba(255,255,255,0.22)'); lgG.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=lgG; ctx.fillRect(-6.5,10,2,9); ctx.fillRect(2.5,10,2,9);
  // Sabatons
  ctx.fillStyle='#5a6878'; ctx.fillRect(-8,18,7,3); ctx.fillRect(1,18,7,3);

  // ── Blue surcoat split halves (tabard — class colour)
  ctx.fillStyle=color;
  ctx.beginPath(); ctx.moveTo(-9,5); ctx.lineTo(-9,18); ctx.lineTo(-3,18); ctx.lineTo(-3,5); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(3,5); ctx.lineTo(3,18); ctx.lineTo(9,18); ctx.lineTo(9,5); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#d4a820'; ctx.lineWidth=0.9;
  ctx.beginPath(); ctx.moveTo(-9,5); ctx.lineTo(-9,18); ctx.lineTo(-3,18); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(9,5); ctx.lineTo(9,18); ctx.lineTo(3,18); ctx.stroke();

  // ── Breastplate
  ctx.fillStyle='#96a8be'; rr(ctx,-10,-8,20,15,3); ctx.fill();
  const bpG=ctx.createLinearGradient(-10,-8,8,7); bpG.addColorStop(0,'rgba(255,255,255,0.30)'); bpG.addColorStop(0.5,'rgba(0,0,0,0)'); bpG.addColorStop(1,'rgba(0,0,0,0.20)');
  ctx.fillStyle=bpG; rr(ctx,-10,-8,20,15,3); ctx.fill();
  ctx.strokeStyle='#b8c8d8'; ctx.lineWidth=0.9; rr(ctx,-10,-8,20,15,3); ctx.stroke();
  // Surcoat centre strip
  ctx.fillStyle=color; rr(ctx,-4,-6,8,12,2); ctx.fill();
  ctx.strokeStyle='#d4a820'; ctx.lineWidth=0.8; rr(ctx,-4,-6,8,12,2); ctx.stroke();
  // Gold cross on surcoat
  ctx.strokeStyle='#f0c840'; ctx.lineWidth=1.6; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(0,-3); ctx.lineTo(0,4); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-2.5,0); ctx.lineTo(2.5,0); ctx.stroke();
  ctx.lineCap='butt';
  // Gold belt
  ctx.fillStyle='#c89818'; ctx.fillRect(-10,5,20,2.5);
  ctx.fillStyle='#f0c840'; ctx.beginPath(); ctx.ellipse(0,6.2,3,2,0,0,Math.PI*2); ctx.fill();

  // ── Pauldrons
  ctx.fillStyle='#8898b2';
  ctx.beginPath(); ctx.ellipse(-11,-3,6,4,0.25,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(11,-3,6,4,-0.25,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.22)';
  ctx.beginPath(); ctx.ellipse(-11,-4.5,3.5,2,0.25,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(11,-4.5,3.5,2,-0.25,0,Math.PI*2); ctx.fill();

  // ── Right arm (gauntlet reaching toward hammer)
  ctx.fillStyle='#8090a8'; rr(ctx,9,-2,4,12,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.14)'; ctx.fillRect(9.5,-1,1.5,9);

  // ── Left arm raised (upper, swinging hammer)
  ctx.fillStyle='#8090a8'; rr(ctx,-13,-14,4,12,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.14)'; ctx.fillRect(-12.5,-13,1.5,9);

  // ── War hammer (angled — swinging pose)
  ctx.save(); ctx.translate(11,-2); ctx.rotate(-0.38);
  // Handle
  ctx.fillStyle='#7a5030'; ctx.fillRect(-1.5,-24,3,28);
  ctx.strokeStyle='#a07848'; ctx.lineWidth=0.5; ctx.strokeRect(-1.5,-24,3,28);
  // Handle bindings
  ctx.strokeStyle='#d4a820'; ctx.lineWidth=1.2;
  for(let i=0;i<3;i++){ ctx.beginPath(); ctx.moveTo(-1.5,-2+i*2.8); ctx.lineTo(1.5,-2+i*2.8); ctx.stroke(); }
  // Hammer head (large, flat face + spike)
  ctx.fillStyle='#7a8090'; ctx.fillRect(-7,-33,15,11);
  const hmG=ctx.createLinearGradient(-7,-33,7,-22); hmG.addColorStop(0,'rgba(255,255,255,0.32)'); hmG.addColorStop(1,'rgba(0,0,0,0.15)');
  ctx.fillStyle=hmG; ctx.fillRect(-7,-33,15,11);
  ctx.strokeStyle='#a0a8b8'; ctx.lineWidth=0.8; ctx.strokeRect(-7,-33,15,11);
  // Spike on top
  ctx.fillStyle='#9098a8';
  ctx.beginPath(); ctx.moveTo(-2,-33); ctx.lineTo(0,-39); ctx.lineTo(2,-33); ctx.closePath(); ctx.fill();
  // Rivets
  ctx.fillStyle='#c8ccd8'; for(let r=0;r<2;r++) for(let c=0;c<3;c++){ctx.beginPath(); ctx.arc(-5+c*4.5,-29+r*3,0.9,0,Math.PI*2); ctx.fill();}
  ctx.restore();

  // ── Closed helmet with gold visor
  ctx.fillStyle='#8898b2'; ctx.beginPath(); ctx.ellipse(0,-19,10,11,0,0,Math.PI*2); ctx.fill();
  const hlG=ctx.createLinearGradient(-10,-30,8,-8); hlG.addColorStop(0,'rgba(255,255,255,0.32)'); hlG.addColorStop(0.5,'rgba(0,0,0,0)'); hlG.addColorStop(1,'rgba(0,0,0,0.28)');
  ctx.fillStyle=hlG; ctx.beginPath(); ctx.ellipse(0,-19,10,11,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#b0bac8'; ctx.lineWidth=0.8; ctx.stroke();
  // Gold visor frame
  ctx.fillStyle='#c89818'; ctx.fillRect(-8,-23,16,1.8); ctx.fillRect(-8,-14.5,16,1.8);
  // Visor grille bars
  ctx.strokeStyle='#d4a820'; ctx.lineWidth=0.9;
  for(let i=0;i<5;i++){ctx.beginPath(); ctx.moveTo(-7.5+i*3.5,-23); ctx.lineTo(-7.5+i*3.5,-14.5); ctx.stroke();}
  // Dark inside visor + warm eye glow
  ctx.fillStyle='rgba(0,0,0,0.42)'; ctx.fillRect(-7,-22.5,14,8);
  ctx.fillStyle='rgba(255,140,30,0.55)'; ctx.fillRect(-5,-20.5,4,2.5); ctx.fillRect(1,-20.5,4,2.5);
  // Helmet ridge on top
  ctx.fillStyle='#7888a0'; ctx.fillRect(-9,-30,18,4);
  ctx.fillStyle='rgba(255,255,255,0.18)'; ctx.fillRect(-8,-29.5,16,1.5);
  // Red plume
  ctx.strokeStyle='#c82020'; ctx.lineWidth=2.2; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(-1,-30); ctx.quadraticCurveTo(-4,-38,0,-41); ctx.stroke();
  ctx.strokeStyle='#e84040'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(2,-30); ctx.quadraticCurveTo(5,-36,2,-40); ctx.stroke();
  ctx.lineCap='butt';

  // ── Dwarf beard (brown, thick — visible below visor)
  ctx.fillStyle='#7a3e10';
  ctx.beginPath(); ctx.moveTo(-8,-12); ctx.lineTo(-11,0); ctx.lineTo(-9,8); ctx.lineTo(-5,11); ctx.lineTo(5,11); ctx.lineTo(9,8); ctx.lineTo(11,0); ctx.lineTo(8,-12); ctx.closePath(); ctx.fill();
  // Mid-tone
  ctx.fillStyle='#b06020';
  ctx.beginPath(); ctx.moveTo(-5,-12); ctx.lineTo(-7,-2); ctx.lineTo(-5,7); ctx.lineTo(5,7); ctx.lineTo(7,-2); ctx.lineTo(5,-12); ctx.closePath(); ctx.fill();
  // Highlight streak
  ctx.fillStyle='rgba(210,140,60,0.35)';
  ctx.beginPath(); ctx.moveTo(-2,-12); ctx.lineTo(-3,1); ctx.lineTo(3,1); ctx.lineTo(2,-12); ctx.closePath(); ctx.fill();
}

function drawMage(ctx, color){
  // ── Long flowing robe (gray-blue, like photo wizard)
  const robeBase='#8890a0';
  ctx.fillStyle=robeBase;
  ctx.beginPath(); ctx.moveTo(-10,-8); ctx.lineTo(-14,20); ctx.lineTo(14,20); ctx.lineTo(10,-8); ctx.closePath(); ctx.fill();
  // Robe shading
  const robeG=ctx.createLinearGradient(-12,-8,10,20); robeG.addColorStop(0,'rgba(255,255,255,0.18)'); robeG.addColorStop(0.5,'rgba(0,0,0,0)'); robeG.addColorStop(1,'rgba(0,0,0,0.25)');
  ctx.fillStyle=robeG; ctx.beginPath(); ctx.moveTo(-10,-8); ctx.lineTo(-14,20); ctx.lineTo(14,20); ctx.lineTo(10,-8); ctx.closePath(); ctx.fill();
  // Colour trim stripe down robe front
  ctx.fillStyle=color; rr(ctx,-3,-6,6,26,2); ctx.fill();
  ctx.strokeStyle=_cl(color,1.4); ctx.lineWidth=0.7; rr(ctx,-3,-6,6,26,2); ctx.stroke();
  // Orange sash / belt
  ctx.fillStyle='#c06010'; ctx.fillRect(-10,-1,20,3);
  ctx.strokeStyle='#e08020'; ctx.lineWidth=0.6; ctx.strokeRect(-10,-1,20,3);

  // ── Torso (robe body)
  ctx.fillStyle=robeBase; rr(ctx,-9,-8,18,14,3); ctx.fill();
  ctx.fillStyle=robeG; rr(ctx,-9,-8,18,14,3); ctx.fill();
  ctx.strokeStyle='rgba(255,255,255,0.14)'; ctx.lineWidth=1; rr(ctx,-9,-8,18,14,3); ctx.stroke();

  // ── Arms in sleeves
  ctx.fillStyle=robeBase; rr(ctx,-13,-7,4,10,2); ctx.fill(); rr(ctx,9,-7,4,10,2); ctx.fill();

  // ── Staff — held in left hand (orange flame, like photo)
  ctx.strokeStyle='#7a5020'; ctx.lineWidth=3; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(-13,-26); ctx.lineTo(-14,14); ctx.stroke();
  ctx.lineCap='butt';
  // Staff rings
  ctx.strokeStyle='#c89020'; ctx.lineWidth=1.4;
  for(let r=0;r<3;r++){ctx.beginPath(); ctx.moveTo(-15,-8+r*4); ctx.lineTo(-11,-8+r*4); ctx.stroke();}
  // Staff head (glowing orb + flame like photo)
  const staffOrbG=ctx.createRadialGradient(-13,-32,1,-13,-32,9);
  staffOrbG.addColorStop(0,'#fff8e0'); staffOrbG.addColorStop(0.3,'#ffb030'); staffOrbG.addColorStop(0.7,'#e06010'); staffOrbG.addColorStop(1,'rgba(200,80,0,0)');
  ctx.fillStyle=staffOrbG; ctx.beginPath(); ctx.arc(-13,-32,9,0,Math.PI*2); ctx.fill();
  // Flame spikes
  ctx.fillStyle='#ffca40';
  ctx.beginPath(); ctx.moveTo(-14,-36); ctx.quadraticCurveTo(-16,-44,-13,-42); ctx.quadraticCurveTo(-10,-44,-12,-36); ctx.closePath(); ctx.fill();
  ctx.fillStyle='#ff8820';
  ctx.beginPath(); ctx.moveTo(-14,-36); ctx.quadraticCurveTo(-15,-41,-13,-40); ctx.quadraticCurveTo(-11,-41,-12,-36); ctx.closePath(); ctx.fill();

  // ── Tall pointed wizard hat (like photo — gray with brim)
  const hatCol='#545a6a';
  // Brim
  ctx.fillStyle=hatCol; rr(ctx,-13,-22,26,4,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.15)'; rr(ctx,-13,-22,26,2,2); ctx.fill();
  ctx.strokeStyle=_cl(hatCol,0.7); ctx.lineWidth=0.7; rr(ctx,-13,-22,26,4,2); ctx.stroke();
  // Hat cone
  ctx.fillStyle=hatCol;
  ctx.beginPath(); ctx.moveTo(0,-43); ctx.lineTo(-11,-22); ctx.lineTo(11,-22); ctx.closePath(); ctx.fill();
  const hatG=ctx.createLinearGradient(-11,-43,9,-22); hatG.addColorStop(0,'rgba(255,255,255,0.22)'); hatG.addColorStop(1,'rgba(0,0,0,0.30)');
  ctx.fillStyle=hatG; ctx.beginPath(); ctx.moveTo(0,-43); ctx.lineTo(-11,-22); ctx.lineTo(11,-22); ctx.closePath(); ctx.fill();
  ctx.strokeStyle=_cl(hatCol,0.75); ctx.lineWidth=0.8; ctx.stroke();
  // Star/rune symbol on hat
  ctx.fillStyle='#f0e060'; ctx.font='bold 7px serif'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText('✦',0,-32);
  // Hat band (colour accent)
  ctx.strokeStyle=color; ctx.lineWidth=1.8;
  ctx.beginPath(); ctx.moveTo(-9,-23.5); ctx.lineTo(9,-23.5); ctx.stroke();

  // ── Face (visible below hat brim)
  drawFace(ctx,0,-15,'#d4c8b8');
  // White beard (like photo wizard)
  ctx.fillStyle='#e0dcd0';
  ctx.beginPath(); ctx.moveTo(-7,-8); ctx.lineTo(-9,2); ctx.lineTo(-7,12); ctx.lineTo(-4,14); ctx.lineTo(4,14); ctx.lineTo(7,12); ctx.lineTo(9,2); ctx.lineTo(7,-8); ctx.closePath(); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.4)';
  ctx.beginPath(); ctx.moveTo(-3,-8); ctx.lineTo(-4,3); ctx.lineTo(0,11); ctx.lineTo(4,3); ctx.lineTo(3,-8); ctx.closePath(); ctx.fill();
}

function drawRogue(ctx, color){
  // ── Long red cape (signature! — like photo rogue — drawn first, behind body)
  const capeRed='#9e1510'; // dark red base
  ctx.fillStyle=capeRed;
  ctx.beginPath(); ctx.moveTo(-9,-7); ctx.lineTo(-15,8); ctx.lineTo(-13,22); ctx.lineTo(-7,22); ctx.lineTo(-3,12); ctx.lineTo(3,12); ctx.lineTo(7,22); ctx.lineTo(13,22); ctx.lineTo(15,8); ctx.lineTo(9,-7); ctx.closePath(); ctx.fill();
  // Cape shading (left darker, right lighter — light from right)
  const capeG=ctx.createLinearGradient(-15,0,15,20); capeG.addColorStop(0,'rgba(0,0,0,0.30)'); capeG.addColorStop(0.5,'rgba(0,0,0,0)'); capeG.addColorStop(1,'rgba(255,255,255,0.12)');
  ctx.fillStyle=capeG; ctx.beginPath(); ctx.moveTo(-9,-7); ctx.lineTo(-15,8); ctx.lineTo(-13,22); ctx.lineTo(-7,22); ctx.lineTo(-3,12); ctx.lineTo(3,12); ctx.lineTo(7,22); ctx.lineTo(13,22); ctx.lineTo(15,8); ctx.lineTo(9,-7); ctx.closePath(); ctx.fill();
  // Cape highlight fold lines
  ctx.strokeStyle='rgba(220,60,40,0.45)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(-12,2); ctx.quadraticCurveTo(-11,14,-9,21); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(12,2); ctx.quadraticCurveTo(11,14,9,21); ctx.stroke();
  ctx.strokeStyle='rgba(0,0,0,0.25)'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.moveTo(-3,12); ctx.lineTo(0,22); ctx.lineTo(3,12); ctx.stroke(); // center split line

  // ── Dark leather legs
  ctx.fillStyle='#281e18'; rr(ctx,-7,7,5,13,2); ctx.fill(); rr(ctx,2,7,5,13,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.10)'; ctx.fillRect(-6.5,8,2,11); ctx.fillRect(2.5,8,2,11);
  // Boots
  ctx.fillStyle='#1a1210'; ctx.fillRect(-8,18,7,3); ctx.fillRect(1,18,7,3);

  // ── Leather torso (brown, like photo)
  ctx.fillStyle='#5a3a20'; rr(ctx,-9,-8,18,16,3); ctx.fill();
  const tG=ctx.createLinearGradient(-9,-8,7,8); tG.addColorStop(0,'rgba(255,255,255,0.18)'); tG.addColorStop(1,'rgba(0,0,0,0.22)');
  ctx.fillStyle=tG; rr(ctx,-9,-8,18,16,3); ctx.fill();
  ctx.strokeStyle='#7a5030'; ctx.lineWidth=0.8; rr(ctx,-9,-8,18,16,3); ctx.stroke();
  // Buckle / centre strap
  ctx.fillStyle='#c89820'; ctx.fillRect(-2,-8,4,14);
  ctx.strokeStyle='#e0b030'; ctx.lineWidth=0.7; ctx.strokeRect(-2,-8,4,14);
  // Gold buckle
  ctx.fillStyle='#d4a020'; ctx.fillRect(-3,3,6,3.5); ctx.strokeStyle='#f0c030'; ctx.lineWidth=0.7; ctx.strokeRect(-3,3,6,3.5);

  // ── Belt with pouches (leather, dark brown)
  ctx.fillStyle='#3a2010'; ctx.fillRect(-10,3,20,2.8);
  ctx.fillStyle='#5a3820'; ctx.fillRect(-9,3,5,5); ctx.fillRect(5,3,5,5); // pouches
  ctx.strokeStyle='#8a5828'; ctx.lineWidth=0.6; ctx.strokeRect(-9,3,5,5); ctx.strokeRect(5,3,5,5);

  // ── Arm (left — holding dagger)
  ctx.fillStyle='#5a3a20'; rr(ctx,-13,-7,4,10,2); ctx.fill();
  // ── Arm (right — holding dagger up)
  ctx.fillStyle='#5a3a20'; rr(ctx,9,-9,4,10,2); ctx.fill();

  // ── Left dagger (held forward)
  ctx.save(); ctx.translate(-14,0); ctx.rotate(0.45);
  ctx.fillStyle='#b8bec8'; ctx.beginPath(); ctx.moveTo(0,-12); ctx.lineTo(-2.5,2); ctx.lineTo(2.5,2); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(255,255,255,0.30)'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.moveTo(0,-10); ctx.lineTo(0,1); ctx.stroke();
  ctx.fillStyle='#7a7880'; ctx.fillRect(-4,1,8,2); // guard
  ctx.fillStyle='#4a2810'; ctx.fillRect(-1.5,3,3,6); // grip
  ctx.restore();
  // ── Right dagger (raised)
  ctx.save(); ctx.translate(12,-8); ctx.rotate(-0.55);
  ctx.fillStyle='#b8bec8'; ctx.beginPath(); ctx.moveTo(0,-12); ctx.lineTo(-2.5,2); ctx.lineTo(2.5,2); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(255,255,255,0.30)'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.moveTo(0,-10); ctx.lineTo(0,1); ctx.stroke();
  ctx.fillStyle='#7a7880'; ctx.fillRect(-4,1,8,2);
  ctx.fillStyle='#4a2810'; ctx.fillRect(-1.5,3,3,6);
  ctx.restore();

  // ── Dark hood (like photo assassin)
  ctx.fillStyle='#1e1820'; ctx.beginPath(); ctx.ellipse(0,-20,10,10,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#2e2430'; ctx.beginPath(); ctx.ellipse(0,-20,8,7,0,Math.PI,0); ctx.fill();
  // Hood shadow under brow
  ctx.fillStyle='rgba(0,0,0,0.50)'; ctx.beginPath(); ctx.ellipse(0,-21.5,7,4,0,0,Math.PI); ctx.fill();
  // Colour accent on hood rim (class colour)
  ctx.strokeStyle=color; ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.ellipse(0,-20,10,10,0,Math.PI*1.1,Math.PI*1.9); ctx.stroke();
  // Face visible (just eyes under hood shadow)
  drawFace(ctx,0,-21,'#c8a870');
}

function drawCleric(ctx, color){
  // ── White flowing robes (behind body)
  ctx.fillStyle='#ece8d8';
  ctx.beginPath(); ctx.moveTo(-8,-6); ctx.lineTo(-14,4); ctx.lineTo(-14,22); ctx.lineTo(-5,22); ctx.lineTo(-3,11); ctx.lineTo(0,22); ctx.lineTo(8,22); ctx.lineTo(10,4); ctx.lineTo(8,-6); ctx.closePath(); ctx.fill();
  const robeG=ctx.createLinearGradient(-14,0,10,20);
  robeG.addColorStop(0,'rgba(0,0,0,0.20)'); robeG.addColorStop(0.4,'rgba(0,0,0,0)'); robeG.addColorStop(1,'rgba(255,255,255,0.14)');
  ctx.fillStyle=robeG; ctx.beginPath(); ctx.moveTo(-8,-6); ctx.lineTo(-14,4); ctx.lineTo(-14,22); ctx.lineTo(-5,22); ctx.lineTo(-3,11); ctx.lineTo(0,22); ctx.lineTo(8,22); ctx.lineTo(10,4); ctx.lineTo(8,-6); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(155,142,118,0.38)'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.moveTo(-11,2); ctx.quadraticCurveTo(-10,12,-9,21); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-3,11); ctx.lineTo(-2,22); ctx.stroke();
  ctx.strokeStyle='rgba(200,160,20,0.5)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(-14,22); ctx.lineTo(10,22); ctx.stroke();

  // ── Chain mail legs
  ctx.fillStyle='#909898'; rr(ctx,-8,6,5,13,2); ctx.fill(); rr(ctx,3,6,5,13,2); ctx.fill();
  const legG=ctx.createLinearGradient(-8,6,-3,19);
  legG.addColorStop(0,'rgba(255,255,255,0.22)'); legG.addColorStop(1,'rgba(0,0,0,0.18)');
  ctx.fillStyle=legG; ctx.fillRect(-7.5,7,2,11); ctx.fillRect(3.5,7,2,11);
  ctx.strokeStyle='rgba(60,72,72,0.38)'; ctx.lineWidth=0.55;
  for(let y=8;y<19;y+=2.2){ ctx.beginPath(); ctx.moveTo(-8,y); ctx.lineTo(-3,y); ctx.stroke(); ctx.beginPath(); ctx.moveTo(3,y); ctx.lineTo(8,y); ctx.stroke(); }
  ctx.fillStyle='#4a3018'; ctx.fillRect(-9,17,7,5); ctx.fillRect(2,17,7,5);
  ctx.fillStyle='rgba(255,255,255,0.14)'; ctx.fillRect(-8.5,17,5,1.5); ctx.fillRect(2.5,17,5,1.5);

  // ── White surcoat with gold border and holy cross
  ctx.fillStyle='#f2eedf';
  ctx.beginPath(); ctx.moveTo(-6,-8); ctx.lineTo(-7,19); ctx.lineTo(7,19); ctx.lineTo(6,-8); ctx.closePath(); ctx.fill();
  const surG=ctx.createLinearGradient(-6,-8,6,16);
  surG.addColorStop(0,'rgba(255,255,255,0.35)'); surG.addColorStop(1,'rgba(0,0,0,0.12)');
  ctx.fillStyle=surG; ctx.beginPath(); ctx.moveTo(-6,-8); ctx.lineTo(-7,19); ctx.lineTo(7,19); ctx.lineTo(6,-8); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=1.4;
  ctx.beginPath(); ctx.moveTo(-6,-8); ctx.lineTo(-7,19); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(6,-8); ctx.lineTo(7,19); ctx.stroke();
  ctx.strokeStyle=color; ctx.lineWidth=2.4; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(0,-4); ctx.lineTo(0,12); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-5,1); ctx.lineTo(5,1); ctx.stroke();
  ctx.lineCap='butt';

  // ── Chain mail breastplate
  ctx.fillStyle='#a8b0b8'; rr(ctx,-10,-8,20,16,3); ctx.fill();
  ctx.strokeStyle='rgba(60,75,82,0.36)'; ctx.lineWidth=0.55;
  for(let y=-7;y<8;y+=2.4){ ctx.beginPath(); ctx.moveTo(-9,y); ctx.lineTo(9,y); ctx.stroke(); }
  const bpG=ctx.createLinearGradient(-10,-8,8,8);
  bpG.addColorStop(0,'rgba(255,255,255,0.26)'); bpG.addColorStop(0.4,'rgba(0,0,0,0)'); bpG.addColorStop(1,'rgba(0,0,0,0.20)');
  ctx.fillStyle=bpG; rr(ctx,-10,-8,20,16,3); ctx.fill();
  ctx.strokeStyle='#d4a020'; ctx.lineWidth=1.6; rr(ctx,-10,-8,20,16,3); ctx.stroke();

  // ── Pauldrons
  ctx.fillStyle='#9aa0a8';
  ctx.beginPath(); ctx.ellipse(-12,-5,6,4,0.3,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(12,-5,6,4,-0.3,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.22)';
  ctx.beginPath(); ctx.ellipse(-13,-7,4,2,0.3,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(11,-7,4,2,-0.3,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.ellipse(-12,-5,6,4,0.3,0,Math.PI*2); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(12,-5,6,4,-0.3,0,Math.PI*2); ctx.stroke();

  // ── Left arm (chain) + flanged mace
  ctx.fillStyle='#909898'; rr(ctx,-15,-7,5,11,2); ctx.fill();
  ctx.strokeStyle='#5a3a18'; ctx.lineWidth=2.5; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(-20,-4); ctx.lineTo(-19,9); ctx.stroke();
  ctx.strokeStyle='#7a5028'; ctx.lineWidth=1;
  for(let i=0;i<3;i++){ ctx.beginPath(); ctx.moveTo(-20.5,-1+i*3.5); ctx.lineTo(-17.5,-2+i*3.5); ctx.stroke(); }
  const mhG=ctx.createRadialGradient(-19,-9,1,-19,-9,7);
  mhG.addColorStop(0,'#d8c0a0'); mhG.addColorStop(0.55,'#9a7040'); mhG.addColorStop(1,'#503010');
  ctx.fillStyle=mhG; ctx.beginPath(); ctx.arc(-19,-9,5.5,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#b08048';
  for(let a=0;a<6;a++){
    ctx.save(); ctx.translate(-19,-9); ctx.rotate(a*Math.PI/3+0.25);
    ctx.beginPath(); ctx.moveTo(0,-5); ctx.lineTo(-2,-8.5); ctx.lineTo(2,-8.5); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  ctx.lineCap='butt';

  // ── Right arm (chain) + round holy shield
  ctx.fillStyle='#909898'; rr(ctx,10,-7,5,11,2); ctx.fill();
  ctx.save(); ctx.translate(21,1);
  const shG=ctx.createRadialGradient(0,0,1,0,0,9);
  shG.addColorStop(0,'#c8a868'); shG.addColorStop(0.65,'#9a7840'); shG.addColorStop(1,'#6a4820');
  ctx.fillStyle=shG; ctx.beginPath(); ctx.arc(0,0,9,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='rgba(80,48,8,0.3)'; ctx.lineWidth=0.7;
  for(let i=-8;i<=8;i+=3.5){ const h=Math.sqrt(Math.max(0,81-i*i)); ctx.beginPath(); ctx.moveTo(i,-h); ctx.lineTo(i,h); ctx.stroke(); }
  ctx.strokeStyle='#7a8898'; ctx.lineWidth=2.2; ctx.beginPath(); ctx.arc(0,0,8,0,Math.PI*2); ctx.stroke();
  ctx.strokeStyle='#5a6878'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(0,-6); ctx.lineTo(0,6); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-6,0); ctx.lineTo(6,0); ctx.stroke();
  ctx.fillStyle='#808898'; ctx.beginPath(); ctx.arc(0,0,2.5,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.4)'; ctx.beginPath(); ctx.arc(-0.5,-0.5,1,0,Math.PI*2); ctx.fill();
  ctx.restore();

  // ── Divine halo (drawn behind helm)
  const haloG=ctx.createRadialGradient(0,-24,9,0,-24,17);
  haloG.addColorStop(0,'rgba(255,210,50,0.18)'); haloG.addColorStop(1,'rgba(255,200,0,0)');
  ctx.fillStyle=haloG; ctx.beginPath(); ctx.arc(0,-24,17,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='rgba(255,215,50,0.65)'; ctx.lineWidth=2.5;
  ctx.beginPath(); ctx.arc(0,-24,12,0,Math.PI*2); ctx.stroke();

  // ── White/silver closed helm
  ctx.fillStyle='#d8d4c8'; ctx.beginPath(); ctx.ellipse(0,-23,10,11,0,Math.PI,0); ctx.fill();
  ctx.fillStyle='#e8e4d8'; rr(ctx,-10,-27,20,7,2); ctx.fill();
  const helmHG=ctx.createLinearGradient(-10,-30,8,-20);
  helmHG.addColorStop(0,'rgba(255,255,255,0.42)'); helmHG.addColorStop(0.5,'rgba(0,0,0,0)'); helmHG.addColorStop(1,'rgba(0,0,0,0.18)');
  ctx.fillStyle=helmHG; ctx.beginPath(); ctx.ellipse(0,-23,10,11,0,Math.PI,0); ctx.fill(); rr(ctx,-10,-27,20,7,2); ctx.fill();
  ctx.strokeStyle='#d4a020'; ctx.lineWidth=1.6; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(0,-32); ctx.lineTo(0,-25); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-3.5,-29); ctx.lineTo(3.5,-29); ctx.stroke();
  ctx.lineCap='butt';
  ctx.fillStyle='rgba(15,12,8,0.78)'; ctx.beginPath(); ctx.ellipse(0,-23,7.5,3,0,0,Math.PI); ctx.fill();
  ctx.fillStyle='rgba(255,218,50,0.75)'; ctx.beginPath(); ctx.arc(-2.5,-23,1.3,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(2.5,-23,1.3,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=1.4;
  ctx.beginPath(); ctx.moveTo(-10,-20); ctx.lineTo(10,-20); ctx.stroke();
}

function drawPaladin(ctx, color){
  // ── Green flowing cape (drawn first — behind body, like photo)
  const capeGreen = color; // class colour = green for paladin
  ctx.fillStyle=capeGreen;
  ctx.beginPath(); ctx.moveTo(-9,-6); ctx.lineTo(-16,4); ctx.lineTo(-14,22); ctx.lineTo(-7,22); ctx.lineTo(-5,10); ctx.lineTo(-2,22); ctx.lineTo(6,22); ctx.lineTo(8,6); ctx.lineTo(9,-6); ctx.closePath(); ctx.fill();
  const cpG=ctx.createLinearGradient(-16,0,8,20); cpG.addColorStop(0,'rgba(0,0,0,0.28)'); cpG.addColorStop(0.5,'rgba(0,0,0,0)'); cpG.addColorStop(1,'rgba(255,255,255,0.15)');
  ctx.fillStyle=cpG; ctx.beginPath(); ctx.moveTo(-9,-6); ctx.lineTo(-16,4); ctx.lineTo(-14,22); ctx.lineTo(-7,22); ctx.lineTo(-5,10); ctx.lineTo(-2,22); ctx.lineTo(6,22); ctx.lineTo(8,6); ctx.lineTo(9,-6); ctx.closePath(); ctx.fill();
  // Cape folds
  ctx.strokeStyle=_cl(capeGreen,0.7); ctx.lineWidth=0.9;
  ctx.beginPath(); ctx.moveTo(-13,2); ctx.quadraticCurveTo(-12,14,-10,21); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-5,10); ctx.lineTo(-3,22); ctx.stroke();
  // Cape collar
  ctx.fillStyle=_cl(capeGreen,1.3); ctx.beginPath(); ctx.ellipse(0,-9,8,3,0,Math.PI,0); ctx.fill();

  // ── Full plate leg armour
  ctx.fillStyle='#8090a8'; rr(ctx,-8,6,5,13,2); ctx.fill(); rr(ctx,3,6,5,13,2); ctx.fill();
  const lgG=ctx.createLinearGradient(-8,6,2,19); lgG.addColorStop(0,'rgba(255,255,255,0.25)'); lgG.addColorStop(1,'rgba(0,0,0,0.15)');
  ctx.fillStyle=lgG; ctx.fillRect(-7.5,7,2,11); ctx.fillRect(3.5,7,2,11);
  // Plate foot
  ctx.fillStyle='#6a7888'; ctx.fillRect(-9,17,7,4); ctx.fillRect(2,17,7,4);
  ctx.fillStyle='rgba(255,255,255,0.15)'; ctx.fillRect(-8.5,17,5,1.5); ctx.fillRect(2.5,17,5,1.5);

  // ── Breastplate (full plate — silver/blue)
  ctx.fillStyle='#8898b8'; rr(ctx,-10,-8,20,16,3); ctx.fill();
  const bpG=ctx.createLinearGradient(-10,-8,8,8); bpG.addColorStop(0,'rgba(255,255,255,0.35)'); bpG.addColorStop(0.45,'rgba(0,0,0,0)'); bpG.addColorStop(1,'rgba(0,0,0,0.22)');
  ctx.fillStyle=bpG; rr(ctx,-10,-8,20,16,3); ctx.fill();
  ctx.strokeStyle='#c8d0d8'; ctx.lineWidth=1; rr(ctx,-10,-8,20,16,3); ctx.stroke();
  // Gold trim on breastplate
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=1.4; rr(ctx,-10,-8,20,16,3); ctx.stroke();
  // Fleur cross on chest
  ctx.strokeStyle='#d4b030'; ctx.lineWidth=1.6; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(2,-5); ctx.lineTo(2,5); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-2,0); ctx.lineTo(6,0); ctx.stroke();
  ctx.lineCap='butt';
  // Gold belt
  ctx.fillStyle='#c8a020'; ctx.fillRect(-10,7,20,2.5);
  ctx.fillStyle='#f0c830'; ctx.beginPath(); ctx.ellipse(2,8.2,3,2,0,0,Math.PI*2); ctx.fill();

  // ── Pauldrons
  ctx.fillStyle='#8090a8';
  ctx.beginPath(); ctx.ellipse(-11,-3,6,4.5,0.2,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(11,-3,6,4.5,-0.2,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.22)';
  ctx.beginPath(); ctx.ellipse(-11,-4.5,3.5,2.2,0.2,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(11,-4.5,3.5,2.2,-0.2,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=0.8;
  ctx.beginPath(); ctx.ellipse(-11,-3,6,4.5,0.2,0,Math.PI*2); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(11,-3,6,4.5,-0.2,0,Math.PI*2); ctx.stroke();

  // ── SHIELD (left arm — wood+iron like photo: round, wood grain, iron rim+cross)
  ctx.save(); ctx.translate(-17,0);
  // Shield body (oval)
  ctx.fillStyle='#7a4820'; ctx.beginPath(); ctx.ellipse(0,0,8,11,0.15,0,Math.PI*2); ctx.fill();
  // Wood grain streaks
  ctx.strokeStyle='rgba(0,0,0,0.30)'; ctx.lineWidth=0.8;
  for(let i=-2;i<=2;i++){ctx.beginPath(); ctx.moveTo(i*2.5,-10); ctx.lineTo(i*2.5+1,10); ctx.stroke();}
  // Iron rim
  ctx.strokeStyle='#7a8898'; ctx.lineWidth=2.5; ctx.beginPath(); ctx.ellipse(0,0,8,11,0.15,0,Math.PI*2); ctx.stroke();
  ctx.strokeStyle='rgba(255,255,255,0.22)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.ellipse(-1,-1,6,8,0.15,Math.PI*1.2,Math.PI*1.8); ctx.stroke();
  // Iron cross on shield
  ctx.strokeStyle='#8898a8'; ctx.lineWidth=2; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(0,-7); ctx.lineTo(0,7); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-6,0); ctx.lineTo(6,0); ctx.stroke();
  ctx.lineCap='butt';
  // Centre boss
  ctx.fillStyle='#a0a8b8'; ctx.beginPath(); ctx.arc(0,0,2.5,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.45)'; ctx.beginPath(); ctx.arc(-0.5,-0.5,1,0,Math.PI*2); ctx.fill();
  ctx.restore();

  // ── Right arm + sword
  ctx.fillStyle='#8090a8'; rr(ctx,9,-8,4,12,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.18)'; ctx.fillRect(9.5,-7,1.5,10);
  // Sword blade (raised)
  ctx.strokeStyle='#c8d0e0'; ctx.lineWidth=2.8;
  ctx.beginPath(); ctx.moveTo(14,-24); ctx.lineTo(14,4); ctx.stroke();
  // Blade groove
  ctx.strokeStyle='rgba(255,255,255,0.40)'; ctx.lineWidth=0.9;
  ctx.beginPath(); ctx.moveTo(14,-22); ctx.lineTo(14,2); ctx.stroke();
  // Crossguard
  ctx.fillStyle='#c8a020'; ctx.fillRect(10,-5,8,2.5);
  ctx.fillStyle='rgba(255,255,255,0.30)'; ctx.fillRect(10,-4.5,8,1);
  // Grip
  ctx.fillStyle='#6a3a10'; ctx.fillRect(12.5,3,3.5,7);
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=0.9;
  for(let i=0;i<3;i++){ctx.beginPath(); ctx.moveTo(12.5,5+i*2.2); ctx.lineTo(16,5+i*2.2); ctx.stroke();}
  // Pommel
  ctx.fillStyle='#c8a020'; ctx.beginPath(); ctx.ellipse(14,12,3.5,2.5,0,0,Math.PI*2); ctx.fill();

  // ── Winged helmet (like photo paladin — gold wings on sides)
  ctx.fillStyle='#8090a8'; ctx.beginPath(); ctx.ellipse(0,-19,10,11,0,0,Math.PI*2); ctx.fill();
  const helG=ctx.createLinearGradient(-10,-30,8,-8); helG.addColorStop(0,'rgba(255,255,255,0.35)'); helG.addColorStop(0.5,'rgba(0,0,0,0)'); helG.addColorStop(1,'rgba(0,0,0,0.28)');
  ctx.fillStyle=helG; ctx.beginPath(); ctx.ellipse(0,-19,10,11,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=1.2; ctx.stroke(); // gold trim on helmet
  // Visor grille
  ctx.fillStyle='#c8a020'; ctx.fillRect(-8,-22,16,1.5); ctx.fillRect(-8,-14,16,1.5);
  ctx.strokeStyle='#c8a020'; ctx.lineWidth=0.9;
  for(let i=0;i<5;i++){ctx.beginPath(); ctx.moveTo(-7.5+i*3.5,-22); ctx.lineTo(-7.5+i*3.5,-14); ctx.stroke();}
  ctx.fillStyle='rgba(0,0,0,0.40)'; ctx.fillRect(-7,-21.5,14,7);
  ctx.fillStyle='rgba(200,220,255,0.50)'; ctx.fillRect(-5,-19.5,10,2.5); // blue eye glow
  // Helmet top ridge
  ctx.fillStyle='#7888a0'; ctx.fillRect(-9,-30,18,4);
  ctx.fillStyle='rgba(255,255,255,0.20)'; ctx.fillRect(-8,-29.5,16,1.5);
  // GOLD WINGS on sides (like photo paladin)
  ctx.fillStyle='#d4a818';
  ctx.beginPath(); ctx.moveTo(-10,-22); ctx.lineTo(-20,-32); ctx.lineTo(-16,-26); ctx.lineTo(-14,-20); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(10,-22); ctx.lineTo(20,-32); ctx.lineTo(16,-26); ctx.lineTo(14,-20); ctx.closePath(); ctx.fill();
  // Wing highlight
  ctx.fillStyle='rgba(255,220,80,0.45)';
  ctx.beginPath(); ctx.moveTo(-10,-22); ctx.lineTo(-18,-30); ctx.lineTo(-15,-25); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(10,-22); ctx.lineTo(18,-30); ctx.lineTo(15,-25); ctx.closePath(); ctx.fill();
  // Wing shadow outline
  ctx.strokeStyle='#a87810'; ctx.lineWidth=0.7;
  ctx.beginPath(); ctx.moveTo(-10,-22); ctx.lineTo(-20,-32); ctx.lineTo(-16,-26); ctx.lineTo(-14,-20); ctx.closePath(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(10,-22); ctx.lineTo(20,-32); ctx.lineTo(16,-26); ctx.lineTo(14,-20); ctx.closePath(); ctx.stroke();
  // Face (visible)
  drawFace(ctx,0,-20,'#d0c0a8');
}

function drawBard(ctx, color){
  const boot='#6a3010';
  ctx.fillStyle=boot; rr(ctx,-9,14,6,16,2); ctx.fill(); rr(ctx,3,14,6,16,2); ctx.fill();
  // Fold cuff
  ctx.fillStyle='#8a4520'; ctx.fillRect(-9,13,6,4); ctx.fillRect(3,13,6,4);
  ctx.fillStyle='#161a40';
  ctx.beginPath(); ctx.ellipse(-6,8,5.5,7,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(6,8,5.5,7,0,0,Math.PI*2); ctx.fill();
  const stripeW=2.8;
  for(let i=0;i<7;i++){
    ctx.fillStyle=i%2===0?'#0c0c0c':'#eceae0';
    ctx.fillRect(-11+i*stripeW,-11,stripeW,22);
  }
  // Round coat silhouette via clip then fill is complex — draw outline over stripes
  ctx.strokeStyle='#0c0c0c'; ctx.lineWidth=1.2;
  ctx.strokeRect(-11,-11,19.6,22);
  // Gold trim borders
  ctx.strokeStyle='#d4a820'; ctx.lineWidth=1.4;
  ctx.beginPath(); ctx.moveTo(-11,11); ctx.lineTo(8.6,11); ctx.stroke();   // hem
  ctx.beginPath(); ctx.moveTo(-11,-11); ctx.lineTo(8.6,-11); ctx.stroke(); // top
  ctx.beginPath(); ctx.moveTo(-11,-11); ctx.lineTo(-11,11); ctx.stroke();  // left edge
  ctx.beginPath(); ctx.moveTo(8.6,-11); ctx.lineTo(8.6,11); ctx.stroke(); // right edge
  // Front opening gold strip
  ctx.beginPath(); ctx.moveTo(-0.5,-11); ctx.lineTo(-0.5,11); ctx.stroke();
  ctx.fillStyle='#eceae4';
  ctx.beginPath(); ctx.ellipse(0,-10,8,4,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.18)'; ctx.lineWidth=0.6; ctx.stroke();
  ctx.fillStyle='#0c0c0c'; ctx.fillRect(-16,-5,6,12); ctx.fillRect(11,-5,6,12); // sleeve
  ctx.fillStyle='#d4a070'; ctx.beginPath(); ctx.ellipse(-13,8,3.5,3,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(14,8,3.5,3,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#9a5422';  // light wood
  ctx.beginPath(); ctx.ellipse(0,3,9,11,-0.15,0,Math.PI*2); ctx.fill();
  const luteG=ctx.createRadialGradient(-2,1,1,-2,1,9);
  luteG.addColorStop(0,'rgba(255,200,120,0.28)'); luteG.addColorStop(1,'rgba(0,0,0,0.18)');
  ctx.fillStyle=luteG; ctx.beginPath(); ctx.ellipse(0,3,9,11,-0.15,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#5c2818'; ctx.lineWidth=1.0; ctx.beginPath(); ctx.ellipse(0,3,9,11,-0.15,0,Math.PI*2); ctx.stroke();
  // Sound hole
  ctx.fillStyle='#0a0806'; ctx.beginPath(); ctx.arc(0,4,2.5,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#d4a820'; ctx.lineWidth=0.8; ctx.beginPath(); ctx.arc(0,4,2.5,0,Math.PI*2); ctx.stroke();
  // Neck (pointing upper-left)
  ctx.fillStyle='#3e1c0a'; ctx.strokeStyle='#0a0806'; ctx.lineWidth=0.7;
  ctx.beginPath(); ctx.moveTo(-5,-7); ctx.lineTo(-8,-8.5); ctx.lineTo(-14,-26); ctx.lineTo(-11,-26.5); ctx.closePath(); ctx.fill(); ctx.stroke();
  // Frets
  ctx.strokeStyle='#b0a080'; ctx.lineWidth=0.9;
  for(let i=0;i<4;i++){ const t=i/4; ctx.beginPath(); ctx.moveTo(-8-t*6,-8.5-t*18); ctx.lineTo(-6-t*5,-8-t*18.5); ctx.stroke(); }
  // Strings
  ctx.strokeStyle='rgba(220,210,160,0.9)'; ctx.lineWidth=0.6;
  for(let i=0;i<4;i++){ const ox=-0.5+i*1.5; ctx.beginPath(); ctx.moveTo(ox+1,13); ctx.lineTo(-7+ox-i*1.5,-26); ctx.stroke(); }
  ctx.fillStyle='#b04418';  // auburn hair (sides/back)
  ctx.beginPath(); ctx.ellipse(0,-20,10,12,0,0,Math.PI*2); ctx.fill();
  // Long hair strands falling
  ctx.fillStyle='#a03c14';
  rr(ctx,-12,-24,4,18,2); ctx.fill();  // left strand
  rr(ctx, 9,-24,4,16,2); ctx.fill();  // right strand
  drawFace(ctx,0,-20,'#d4a070');
  // Wide bard smile overlay
  ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=1.4;
  ctx.beginPath(); ctx.arc(0,-18,4,0.1,Math.PI-0.1,false); ctx.stroke();
  ctx.save(); ctx.translate(-2,-28); ctx.rotate(-0.30);
  ctx.fillStyle='#c81818';
  ctx.beginPath(); ctx.ellipse(0,0,10,5,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(0,-1,8,4,0,0,Math.PI); ctx.fill();  // dome
  ctx.strokeStyle='#7c1010'; ctx.lineWidth=1.0; ctx.beginPath(); ctx.ellipse(0,0,10,5,0,0,Math.PI*2); ctx.stroke();
  // Small button
  ctx.fillStyle='#d4a820'; ctx.beginPath(); ctx.arc(0,-4.5,1.5,0,Math.PI*2); ctx.fill();
  ctx.restore();
}

function drawGoblin(ctx){
  ctx.fillStyle='#3a5820'; rr(ctx,-6,3,4,11,2); ctx.fill(); rr(ctx,2,3,4,11,2); ctx.fill();
  ctx.fillStyle='#4a7428'; rr(ctx,-7,-5,14,10,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.1)'; ctx.fillRect(-5,-4,4,5);
  ctx.fillStyle='#4a7428'; rr(ctx,-10,-4,4,13,2); ctx.fill(); rr(ctx,6,-4,4,13,2); ctx.fill();
  ctx.fillStyle='#2a3810';
  for(let i=0;i<3;i++){ctx.beginPath(); ctx.ellipse(-8+i*1.5,9,1,3,0.3,0,Math.PI*2); ctx.fill();}
  for(let i=0;i<3;i++){ctx.beginPath(); ctx.ellipse(7+i*1.5,9,1,3,-0.3,0,Math.PI*2); ctx.fill();}
  ctx.fillStyle='#4a7428'; ctx.beginPath(); ctx.ellipse(0,-10,9,8,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#3a6020'; ctx.lineWidth=0.8; ctx.stroke();
  ctx.fillStyle='#4a7428';
  ctx.beginPath(); ctx.moveTo(-9,-7); ctx.lineTo(-15,-17); ctx.lineTo(-5,-11); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(9,-7); ctx.lineTo(15,-17); ctx.lineTo(5,-11); ctx.closePath(); ctx.fill();
  ctx.fillStyle='#ff7700'; ctx.beginPath(); ctx.ellipse(-3.5,-11,3,2.5,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(3.5,-11,3,2.5,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#1a0800'; ctx.beginPath(); ctx.arc(-3.5,-11,1.3,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(3.5,-11,1.3,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.7)'; ctx.fillRect(-3,-11,0.8,0.8); ctx.fillRect(3.8,-11,0.8,0.8);
  ctx.fillStyle='#d0c080'; ctx.fillRect(-5,-4,2.5,2); ctx.fillRect(-1.5,-4,3,2); ctx.fillRect(2.5,-4,2,2);
  ctx.strokeStyle='#5a3a10'; ctx.lineWidth=2; ctx.beginPath(); ctx.moveTo(9,0); ctx.lineTo(16,-9); ctx.stroke();
  ctx.fillStyle='#7a5030'; ctx.beginPath(); ctx.ellipse(17,-10,4,3,0.5,0,Math.PI*2); ctx.fill();
}

function drawSkeleton(ctx){
  const bone='#e0d8b8';
  ctx.fillStyle=bone; ctx.fillRect(-5.5,5,3,14); ctx.fillRect(2.5,5,3,14);
  ctx.beginPath(); ctx.arc(-4,11,3,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(4,11,3,0,Math.PI*2); ctx.fill();
  ctx.fillRect(-7,17,5,3); ctx.fillRect(2,17,5,3);
  ctx.beginPath(); ctx.ellipse(0,3,8,4,0,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(0,-5,7,9,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.4)';
  for(let i=0;i<4;i++){ctx.fillRect(-6,-1+i*3,3,1.5); ctx.fillRect(3,-1+i*3,3,1.5);}
  ctx.fillStyle=bone; ctx.fillRect(-13,-6,3,12); ctx.fillRect(10,-6,3,12);
  ctx.beginPath(); ctx.arc(-11.5,2,3,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(11.5,2,3,0,Math.PI*2); ctx.fill();
  for(let i=0;i<3;i++){ctx.fillRect(-15+i*1.5,7,1.5,5); ctx.fillRect(10+i*1.5,7,1.5,5);}
  ctx.beginPath(); ctx.ellipse(0,-17,9,9,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.2)'; ctx.lineWidth=0.7; ctx.stroke();
  ctx.fillStyle='#100800'; ctx.beginPath(); ctx.ellipse(-3.5,-18,3.5,3,0,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(3.5,-18,3.5,3,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(60,220,100,0.95)'; ctx.beginPath(); ctx.arc(-3.5,-18,1.5,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(3.5,-18,1.5,0,Math.PI*2); ctx.fill();
  ctx.fillStyle=bone; ctx.beginPath(); ctx.ellipse(0,-11,6,4,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.45)'; ctx.fillRect(-4,-12.5,2.5,2); ctx.fillRect(-0.5,-12.5,2.5,2); ctx.fillRect(2.5,-12.5,2,2);
  ctx.strokeStyle='#8090a8'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(-13,-16); ctx.lineTo(-13,4); ctx.stroke();
  ctx.fillStyle='#8090a8'; ctx.fillRect(-16,-5,6,2);
}

function drawOrc(ctx){
  const skin='#48a838'; // bright vivid green like painted miniature
  const bone='#d8c890'; // bone/ivory armour

  // ── Thick leather legs + wrapped boots
  ctx.fillStyle='#3a2010'; rr(ctx,-9,5,7,14,2); ctx.fill(); rr(ctx,2,5,7,14,2); ctx.fill();
  ctx.strokeStyle='#5a3010'; ctx.lineWidth=1;
  for(let y=8;y<18;y+=3.5){ ctx.beginPath(); ctx.moveTo(-9,y); ctx.lineTo(-2,y); ctx.stroke(); ctx.beginPath(); ctx.moveTo(2,y); ctx.lineTo(9,y); ctx.stroke(); }
  ctx.fillStyle='#281808'; ctx.fillRect(-10,17,8,5); ctx.fillRect(2,17,8,5);
  ctx.fillStyle='rgba(255,255,255,0.08)'; ctx.fillRect(-9.5,17,6,1.5); ctx.fillRect(2.5,17,6,1.5);

  // ── Leather chest with bone plate armour
  ctx.fillStyle='#5a3818'; rr(ctx,-11,-8,22,14,3); ctx.fill();
  const chG=ctx.createLinearGradient(-11,-8,9,6);
  chG.addColorStop(0,'rgba(255,255,255,0.12)'); chG.addColorStop(0.5,'rgba(0,0,0,0)'); chG.addColorStop(1,'rgba(0,0,0,0.28)');
  ctx.fillStyle=chG; rr(ctx,-11,-8,22,14,3); ctx.fill();
  // Bone plate left
  ctx.fillStyle=bone; rr(ctx,-10,-7,8,10,2); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.18)'; rr(ctx,-10,-7,8,10,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.28)'; ctx.fillRect(-9,-6,3,4);
  ctx.strokeStyle='rgba(80,60,20,0.5)'; ctx.lineWidth=0.8; rr(ctx,-10,-7,8,10,2); ctx.stroke();
  // Bone plate right
  ctx.fillStyle=bone; rr(ctx,2,-7,8,10,2); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.18)'; rr(ctx,2,-7,8,10,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.28)'; ctx.fillRect(3,-6,3,4);
  ctx.strokeStyle='rgba(80,60,20,0.5)'; ctx.lineWidth=0.8; rr(ctx,2,-7,8,10,2); ctx.stroke();
  // Sinew bindings between plates
  ctx.strokeStyle='#8a6030'; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.moveTo(-2,-4); ctx.lineTo(2,-4); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-2,0); ctx.lineTo(2,0); ctx.stroke();
  // Belt
  ctx.fillStyle='#3a2010'; ctx.fillRect(-11,4,22,4);
  ctx.fillStyle='rgba(255,255,255,0.08)'; ctx.fillRect(-11,4,22,1.5);
  // Trophy skull on belt
  ctx.fillStyle='#e0d4a8'; ctx.beginPath(); ctx.ellipse(0,6,3.5,3,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.38)'; ctx.beginPath(); ctx.arc(-1.2,5.5,1,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(1.2,5.5,1,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='rgba(80,60,20,0.5)'; ctx.lineWidth=0.7; ctx.beginPath(); ctx.ellipse(0,6,3.5,3,0,0,Math.PI*2); ctx.stroke();

  // ── Thick muscular arms (green skin)
  ctx.fillStyle=skin; rr(ctx,-16,-6,6,16,3); ctx.fill(); rr(ctx,10,-6,6,16,3); ctx.fill();
  const armG=ctx.createLinearGradient(-16,-6,-10,10);
  armG.addColorStop(0,'rgba(255,255,255,0.15)'); armG.addColorStop(0.6,'rgba(0,0,0,0)'); armG.addColorStop(1,'rgba(0,0,0,0.22)');
  ctx.fillStyle=armG; rr(ctx,-16,-6,6,16,3); ctx.fill();
  const armG2=ctx.createLinearGradient(16,-6,10,10);
  armG2.addColorStop(0,'rgba(255,255,255,0.15)'); armG2.addColorStop(0.6,'rgba(0,0,0,0)'); armG2.addColorStop(1,'rgba(0,0,0,0.22)');
  ctx.fillStyle=armG2; rr(ctx,10,-6,6,16,3); ctx.fill();
  // Bone forearm bands
  ctx.fillStyle=bone; ctx.fillRect(-17,5,8,3); ctx.fillRect(9,5,8,3);
  ctx.fillStyle='rgba(0,0,0,0.2)'; ctx.fillRect(-17,5,8,3); ctx.fillRect(9,5,8,3);
  ctx.strokeStyle='rgba(80,60,20,0.5)'; ctx.lineWidth=0.7; ctx.strokeRect(-17,5,8,3); ctx.strokeRect(9,5,8,3);
  // Heavy fists
  ctx.fillStyle=_cl(skin,0.85); ctx.beginPath(); ctx.ellipse(-13,12,5,4,0.4,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(13,12,5,4,-0.4,0,Math.PI*2); ctx.fill();

  // ── Large battle axe (right hand)
  ctx.strokeStyle='#5a3010'; ctx.lineWidth=3.5; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(14,5); ctx.lineTo(22,-20); ctx.stroke();
  ctx.strokeStyle='#8a4820'; ctx.lineWidth=1.5;
  for(let i=0;i<5;i++){ const t=i/4; ctx.beginPath(); ctx.arc(14+(22-14)*t,5+(-20-5)*t,1.8,0,Math.PI*2); ctx.stroke(); }
  ctx.save(); ctx.translate(24,-22); ctx.rotate(0.7);
  ctx.fillStyle='#808898';
  ctx.beginPath(); ctx.moveTo(-3,-10); ctx.bezierCurveTo(4,-14,12,-10,10,0); ctx.bezierCurveTo(12,10,4,10,-3,8); ctx.closePath(); ctx.fill();
  const blG=ctx.createLinearGradient(-3,-10,10,5);
  blG.addColorStop(0,'rgba(255,255,255,0.42)'); blG.addColorStop(0.35,'rgba(255,255,255,0.1)'); blG.addColorStop(0.65,'rgba(0,0,0,0)'); blG.addColorStop(1,'rgba(0,0,0,0.30)');
  ctx.fillStyle=blG; ctx.beginPath(); ctx.moveTo(-3,-10); ctx.bezierCurveTo(4,-14,12,-10,10,0); ctx.bezierCurveTo(12,10,4,10,-3,8); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='#c8ccd8'; ctx.lineWidth=1.2; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(-3,-10); ctx.bezierCurveTo(4,-14,12,-10,10,0); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-3,8); ctx.bezierCurveTo(4,10,12,10,10,0); ctx.stroke();
  ctx.fillStyle='#9098a8'; ctx.beginPath(); ctx.moveTo(-3,-10); ctx.lineTo(-1,-16); ctx.lineTo(2,-10); ctx.closePath(); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.3)'; ctx.beginPath(); ctx.moveTo(-3,-10); ctx.lineTo(-1,-16); ctx.lineTo(-1,-10); ctx.closePath(); ctx.fill();
  ctx.fillStyle='#505868'; for(const [rx,ry] of [[0,-4],[0,2],[-2,-1]]){ ctx.beginPath(); ctx.arc(rx,ry,0.9,0,Math.PI*2); ctx.fill(); }
  ctx.restore(); ctx.lineCap='butt';

  // ── Orc head (large, brutish)
  ctx.fillStyle=skin; ctx.beginPath(); ctx.ellipse(0,-18,11,10,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle=_cl(skin,0.72); ctx.lineWidth=0.8; ctx.stroke();
  // Heavy brow ridge
  ctx.fillStyle=_cl(skin,0.80); ctx.beginPath(); ctx.arc(-4,-22,3.5,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(4,-22,3.5,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(0,-24,3,0,Math.PI*2); ctx.fill();
  // Bone crown/headband
  ctx.fillStyle=bone; ctx.fillRect(-10,-27,20,4);
  ctx.fillStyle='rgba(0,0,0,0.2)'; ctx.fillRect(-10,-27,20,4);
  ctx.fillStyle='rgba(255,255,255,0.18)'; ctx.fillRect(-10,-27,20,1.5);
  ctx.strokeStyle='rgba(80,60,20,0.5)'; ctx.lineWidth=0.7; ctx.strokeRect(-10,-27,20,4);
  // Bone spikes on crown
  ctx.fillStyle=bone;
  for(const [sx] of [[-7],[0],[7]]){ ctx.beginPath(); ctx.moveTo(sx-2,-27); ctx.lineTo(sx+2,-27); ctx.lineTo(sx,-32); ctx.closePath(); ctx.fill(); ctx.strokeStyle='rgba(80,60,20,0.45)'; ctx.lineWidth=0.6; ctx.beginPath(); ctx.moveTo(sx-2,-27); ctx.lineTo(sx+2,-27); ctx.lineTo(sx,-32); ctx.closePath(); ctx.stroke(); }
  // Fierce red eyes
  ctx.fillStyle='#cc1800'; ctx.beginPath(); ctx.ellipse(-4,-19,3.2,2.8,0,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(4,-19,3.2,2.8,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#1a0000'; ctx.beginPath(); ctx.arc(-4,-19,1.4,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(4,-19,1.4,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.7)'; ctx.fillRect(-3.5,-19.5,0.8,0.8); ctx.fillRect(4.5,-19.5,0.8,0.8);
  // Thick nose
  ctx.fillStyle=_cl(skin,0.78); ctx.beginPath(); ctx.ellipse(0,-15,3.5,2.5,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.45)'; ctx.beginPath(); ctx.arc(-1.5,-15,1,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(1.5,-15,1,0,Math.PI*2); ctx.fill();
  // Ivory tusks
  ctx.fillStyle='#e8d898';
  ctx.beginPath(); ctx.moveTo(-5,-11); ctx.lineTo(-8,-7); ctx.lineTo(-4,-9); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(5,-11); ctx.lineTo(8,-7); ctx.lineTo(4,-9); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(140,110,30,0.5)'; ctx.lineWidth=0.6;
  ctx.beginPath(); ctx.moveTo(-5,-11); ctx.lineTo(-8,-7); ctx.lineTo(-4,-9); ctx.closePath(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(5,-11); ctx.lineTo(8,-7); ctx.lineTo(4,-9); ctx.closePath(); ctx.stroke();
  // Grimacing mouth
  ctx.strokeStyle='rgba(0,0,0,0.55)'; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.moveTo(-4,-12); ctx.quadraticCurveTo(0,-10,4,-12); ctx.stroke();
}

function drawDarkMage(ctx){
  const robe='#1a0830';
  ctx.fillStyle=robe; ctx.beginPath(); ctx.moveTo(-8,-8); ctx.lineTo(-13,19); ctx.lineTo(13,19); ctx.lineTo(8,-8); ctx.closePath(); ctx.fill();
  ctx.fillStyle='#250d45'; rr(ctx,-9,-8,18,14,3); ctx.fill();
  ctx.fillStyle='rgba(160,50,220,0.3)'; ctx.fillRect(-6,-7,5,11);
  ctx.fillStyle='rgba(180,50,230,0.85)'; ctx.font='5px serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText('ᚱ',-4,2); ctx.fillText('ᚦ',4,2);
  ctx.fillStyle='#250d45'; rr(ctx,-13,-7,5,10,2); ctx.fill(); rr(ctx,8,-7,5,10,2); ctx.fill();
  const og=ctx.createRadialGradient(-12,2,1,-12,2,5);
  og.addColorStop(0,'#ff80ff'); og.addColorStop(1,'#600080');
  ctx.fillStyle=og; ctx.beginPath(); ctx.arc(-12,3,5,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#c8c0b0'; for(let i=0;i<3;i++){ctx.fillRect(9+i*1.5,4,1.5,6);}
  ctx.fillStyle='#0d0420'; ctx.beginPath(); ctx.ellipse(0,-19,10,11,0,Math.PI,0); ctx.fill();
  ctx.fillStyle='#180830'; ctx.beginPath(); ctx.ellipse(0,-18,8,7.5,0,Math.PI,0); ctx.fill();
  ctx.fillStyle='rgba(0,0,0,0.65)'; ctx.beginPath(); ctx.ellipse(0,-21,8,6,0,0,Math.PI); ctx.fill();
  ctx.fillStyle='rgba(160,0,255,0.95)'; ctx.beginPath(); ctx.arc(-3,-20,2,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(3,-20,2,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='rgba(255,180,255,0.6)'; ctx.beginPath(); ctx.arc(-3,-20,0.8,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(3,-20,0.8,0,Math.PI*2); ctx.fill();
}

function drawTroll(ctx){
  const skin='#6a7050';
  ctx.fillStyle='#4a4830'; rr(ctx,-10,5,8,13,2); ctx.fill(); rr(ctx,2,5,8,13,2); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.08)'; ctx.fillRect(-9,6,3,10); ctx.fillRect(3,6,3,10);
  ctx.fillStyle=skin; rr(ctx,-13,-8,26,15,3); ctx.fill();
  ctx.fillStyle='rgba(255,255,255,0.07)'; ctx.fillRect(-11,-7,8,10);
  ctx.fillStyle=_cl(skin,0.82);
  for(const [bx,by,br] of [[-5,-4,2.5],[3,2,2],[7,-6,2],[-8,1,1.5],[0,-6,1.5]]){ctx.beginPath(); ctx.arc(bx,by,br,0,Math.PI*2); ctx.fill();}
  ctx.fillStyle=skin; rr(ctx,-18,-6,6,18,3); ctx.fill(); rr(ctx,12,-6,6,18,3); ctx.fill();
  ctx.fillStyle=_cl(skin,0.8); ctx.beginPath(); ctx.ellipse(-15,13,5,4,0.4,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(15,13,5,4,-0.4,0,Math.PI*2); ctx.fill();
  ctx.fillStyle=skin; ctx.beginPath(); ctx.ellipse(0,-15,12,8,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle=_cl(skin,0.7); ctx.lineWidth=0.8; ctx.stroke();
  ctx.fillStyle=_cl(skin,0.72); ctx.beginPath(); ctx.arc(-5,-20,4,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(5,-20,4,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(0,-22,3,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#e04000'; ctx.beginPath(); ctx.ellipse(-4,-16,3,2.5,0,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(4,-16,3,2.5,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#400'; ctx.beginPath(); ctx.arc(-4,-16,1.2,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(4,-16,1.2,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#2a1a10'; ctx.beginPath(); ctx.moveTo(-7,-10); ctx.quadraticCurveTo(0,-7,7,-10); ctx.fill();
  ctx.fillStyle='#d0c090'; for(let i=0;i<5;i++){ctx.beginPath(); ctx.moveTo(-6+i*3,-10); ctx.lineTo(-5+i*3,-7); ctx.lineTo(-4+i*3,-10); ctx.closePath(); ctx.fill();}
}

function drawDragon(ctx){
  ctx.fillStyle='rgba(180,20,0,0.65)';
  ctx.beginPath(); ctx.moveTo(-8,-8); ctx.lineTo(-26,-26); ctx.lineTo(-20,-4); ctx.lineTo(-14,10); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(8,-8); ctx.lineTo(26,-26); ctx.lineTo(20,-4); ctx.lineTo(14,10); ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(255,80,0,0.45)'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(-8,-8); ctx.lineTo(-24,-20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-8,-6); ctx.lineTo(-20,-4); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(8,-8); ctx.lineTo(24,-20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(8,-6); ctx.lineTo(20,-4); ctx.stroke();
  ctx.strokeStyle='#8a1500'; ctx.lineWidth=5; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(8,8); ctx.bezierCurveTo(20,15,28,5,32,12); ctx.stroke();
  const bg=ctx.createRadialGradient(-3,-5,2,0,0,16);
  bg.addColorStop(0,'#d03000'); bg.addColorStop(1,'#600a00');
  ctx.fillStyle=bg; ctx.beginPath(); ctx.ellipse(0,0,14,18,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#ff4000'; ctx.lineWidth=1; ctx.stroke();
  ctx.fillStyle='rgba(255,100,0,0.3)'; for(let i=0;i<4;i++){ctx.beginPath(); ctx.ellipse(0,-5+i*5,8-i,3,0,0,Math.PI*2); ctx.fill();}
  ctx.fillStyle='#7a1000'; rr(ctx,-10,12,7,10,3); ctx.fill(); rr(ctx,3,12,7,10,3); ctx.fill();
  ctx.fillStyle='#1a0800';
  for(let i=0;i<3;i++){ctx.beginPath(); ctx.ellipse(-8+i*1.8,22,1.5,4,0.4,0,Math.PI*2); ctx.fill();}
  for(let i=0;i<3;i++){ctx.beginPath(); ctx.ellipse(4+i*1.8,22,1.5,4,-0.4,0,Math.PI*2); ctx.fill();}
  ctx.fillStyle='#9a1800'; rr(ctx,-5,-18,10,11,3); ctx.fill();
  ctx.fillStyle='#b02000'; ctx.beginPath(); ctx.ellipse(0,-25,11,9,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#e03000'; ctx.lineWidth=0.8; ctx.stroke();
  ctx.fillStyle='#3a0a00'; ctx.beginPath(); ctx.moveTo(-7,-31); ctx.lineTo(-13,-40); ctx.lineTo(-5,-32); ctx.closePath(); ctx.fill(); ctx.beginPath(); ctx.moveTo(7,-31); ctx.lineTo(13,-40); ctx.lineTo(5,-32); ctx.closePath(); ctx.fill();
  ctx.fillStyle='#ffcc00'; ctx.beginPath(); ctx.ellipse(-4.5,-26,4,3,0,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(4.5,-26,4,3,0,0,Math.PI*2); ctx.fill();
  ctx.fillStyle='#1a0000'; ctx.beginPath(); ctx.ellipse(-4.5,-26,1.5,2.5,0.2,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.ellipse(4.5,-26,1.5,2.5,-0.2,0,Math.PI*2); ctx.fill();
  const fg=ctx.createLinearGradient(11,-28,26,-18);
  fg.addColorStop(0,'rgba(255,200,0,0.9)'); fg.addColorStop(1,'rgba(255,50,0,0)');
  ctx.fillStyle=fg; ctx.beginPath(); ctx.moveTo(10,-25); ctx.lineTo(28,-18); ctx.lineTo(26,-14); ctx.lineTo(8,-22); ctx.closePath(); ctx.fill();
}

// ── Miniaturas 2D dos heróis (frente.png) para o modo canvas ────────────────
// Antes o modo 2D desenhava heróis proceduralmente (drawWarrior, …) e NUNCA
// usava as PNGs. Agora usa as mesmas imagens do 3D. Carrega lazy; enquanto não
// carrega, drawHeroSprite cai no sprite procedural. Ao carregar, redesenha.
const _hero2DImg = {};
function _getHero2DImg(classId){
  if(!classId) return null;
  let img = _hero2DImg[classId];
  if(img === undefined){
    img = new Image();
    img.onload = () => { if(!mode3D && window.GS && GS.gameState){ try{ renderMap(GS.gameState); }catch(_){} } };
    img.src = _assetURL(`assets/pawns/${classId}/frente.png`);
    _hero2DImg[classId] = img;
  }
  return img;
}

// Mesma ideia para os monstros: usa assets/pawns/monstros/<image>/<image>.png.
const _mon2DImg = {};
function _getMonster2DImg(imageName){
  if(!imageName) return null;
  let img = _mon2DImg[imageName];
  if(img === undefined){
    img = new Image();
    img.onload = () => { if(!mode3D && window.GS && GS.gameState){ try{ renderMap(GS.gameState); }catch(_){} } };
    img.src = _assetURL(`assets/pawns/monstros/${imageName}/${imageName}.png`);
    _mon2DImg[imageName] = img;
  }
  return img;
}

// Miniatura 2D do prisioneiro (imagem editável). url completa em assets/pawns/prisioneiros/.
const _pris2DImg = {};
function _getPrisoner2DImg(imageName){
  if(!imageName) return null;
  let img = _pris2DImg[imageName];
  if(img === undefined){
    img = new Image();
    img.onload = () => { if(!mode3D && window.GS && GS.gameState){ try{ renderMap(GS.gameState); }catch(_){} } };
    img.src = _assetURL(`assets/pawns/prisioneiros/${imageName}`);
    _pris2DImg[imageName] = img;
  }
  return img;
}

// Miniatura 2D de objeto de decoração (PNG editável em assets/objetos/).
const _obj2DImg = {};
function _getObjeto2DImg(imageName){
  if(!imageName) return null;
  let img = _obj2DImg[imageName];
  if(img === undefined){
    img = new Image();
    img.onload = () => { if(!mode3D && window.GS && GS.gameState){ try{ renderMap(GS.gameState); }catch(_){} } };
    img.src = _assetURL(`assets/objetos/${imageName}`);
    _obj2DImg[imageName] = img;
  }
  return (img.complete && img.naturalWidth) ? img : null;
}

// Rotação de objetos (decorações): facing → ângulo. O facing canônico [0,1] é 0°;
// cada giro de 90° avança no sentido [0,1]→[1,0]→[0,-1]→[-1,0]. Usado no 2D (canvas)
// e no 3D (rotation.y), para a imagem do objeto realmente girar.
function _facingAngle2D(f){
  if(!f) return 0;
  if(f[0]===1  && f[1]===0)  return Math.PI/2;
  if(f[0]===0  && f[1]===-1) return Math.PI;
  if(f[0]===-1 && f[1]===0)  return -Math.PI/2;
  return 0;
}
function _facingAngleY3D(f){
  // Eixo Y do mundo 3D: sinal oposto ao 2D para o giro casar visualmente com o topo.
  if(!f) return 0;
  if(f[0]===1  && f[1]===0)  return -Math.PI/2;
  if(f[0]===0  && f[1]===-1) return Math.PI;
  if(f[0]===-1 && f[1]===0)  return Math.PI/2;
  return 0;
}

// Visibilidade de uma armadilha colocável para o jogador local:
//  • aliada (colocada por um jogador): visível a todos (para não pisarem);
//  • so_luccas (oculta de masmorra/kobold): só o Luccas (rogue) enxerga;
//  • hostil autorada: ESCONDIDA até ser revelada (detecção do Luccas/Clarividência →
//    visivel) ou disparada (ativada). Antes disso não aparece no mapa.
function _armadilhaVisivelParaMim(arm, me){
  if(arm.aliada) return true;
  if(arm.so_luccas) return !!(me && me.class_id === 'rogue');
  return !!(arm.visivel || arm.ativada);
}
// Cache 2D do PNG de uma armadilha (mesma pasta dos objetos de decoração).
function _getArmadilha2DImg(imageName){ return _getObjeto2DImg(imageName); }

// Escala da miniatura por PORTE (categoria de tamanho da ficha do monstro, vinda
// do servidor em m.porte). Guia a geração do sprite no 2D e no 3D. Ausente/
// desconhecido = "medio" (1.0). Ex.: kobolds são "pequeno".
const _PORTE_FATOR = { minusculo: 0.5, pequeno: 0.68, medio: 1.0, grande: 1.35, enorme: 1.7 };
function _pawnScaleFactor(porte){
  return _PORTE_FATOR[porte] || 1.0;
}

// Minis cujo PNG já traz a criatura enrolada sobre um pedestal redondo (cobras).
// Diferente das figuras "altas, pés na base", elas devem caber INTEIRAS no tile
// (largura E altura ≤ 1 quadrado), sem estourar para os tiles vizinhos. Tratadas
// à parte no 2D (drawMonsterSprite) e no 3D (_makeMonsterBillboard). Chaveadas
// pelo nome da imagem (m.image). _FIT_TILE_FRAC = lado-alvo como fração do tile.
const _FIT_TILE_PAWNS = new Set(['cobraConstritora', 'cobraVenenosa']);
const _FIT_TILE_FRAC  = 0.94;

// Minis grandes e largas (ogros) que devem PREENCHER a largura do tile (borda a
// borda) sem invadir os vizinhos: largura = _FILL_WIDTH_FRAC do tile; a altura
// segue a proporção real da arte (sem cap → mini imponente, bem maior em volume
// que as dos heróis), ancorada na base. Tratadas no 2D e no 3D, por m.image.
const _FILL_WIDTH_PAWNS = new Set(['ogroClava', 'ogroLanca']);
const _FILL_WIDTH_FRAC  = 0.98;

function drawHeroSprite(ctx, cx, cy, classId, color, isMe, isCur){
  ctx.save(); ctx.translate(cx,cy);
  const r=CELL/2-2;
  // Drop shadow (ellipse at feet)
  ctx.fillStyle='rgba(0,0,0,0.48)';
  ctx.beginPath(); ctx.ellipse(0,r*0.78,r*0.65,r*0.22,0,0,Math.PI*2); ctx.fill();
  // Active glow ring
  if(isCur){
    ctx.save(); ctx.shadowColor=color; ctx.shadowBlur=22;
    ctx.strokeStyle=color+'cc'; ctx.lineWidth=2.5;
    ctx.beginPath(); ctx.arc(0,-2,r+5,0,Math.PI*2); ctx.stroke(); ctx.restore();
  }
  // Class sprite — usa a miniatura PNG (frente.png), igual ao 3D; enquanto a
  // imagem não carrega, cai no sprite procedural (drawWarrior, …).
  const heroImg = _getHero2DImg(classId);
  if(heroImg && heroImg.complete && heroImg.naturalWidth){
    const feetY = r*0.82;                  // pés logo acima da sombra
    let h = CELL*1.55;                      // altura alvo (mini mais alta que o tile)
    let w = h * (heroImg.naturalWidth / heroImg.naturalHeight);
    const wMax = CELL*1.28;                 // limita largura (ex.: anão com machado+escudo)
    if(w > wMax){ h *= wMax/w; w = wMax; }
    ctx.drawImage(heroImg, -w/2, feetY - h, w, h);
  } else {
    ctx.save();
    ctx.scale(SPR_SCALE, SPR_SCALE);
    ctx.textAlign='center'; ctx.textBaseline='middle';
    switch(classId){
      case 'warrior': drawWarrior(ctx,color); break;
      case 'mage':    drawMage(ctx,color); break;
      case 'rogue':   drawRogue(ctx,color); break;
      case 'cleric':  drawCleric(ctx,color); break;
      case 'paladin': drawPaladin(ctx,color); break;
      case 'bard':    drawBard(ctx,color);   break;
      default:
        ctx.fillStyle=color; ctx.beginPath(); ctx.arc(0,0,r/SPR_SCALE,0,Math.PI*2); ctx.fill();
    }
    ctx.restore();
  }
  // Gold ring for me
  if(isMe){
    ctx.strokeStyle='#f0c040'; ctx.lineWidth=2.5;
    ctx.beginPath(); ctx.arc(0,-2,r+2,0,Math.PI*2); ctx.stroke();
  }
  // Name tag
  if(isMe||isCur){
    ctx.restore(); ctx.save(); ctx.translate(cx,cy);
    const tagFs=Math.round(CELL*0.14); ctx.font=`bold ${tagFs}px monospace`; ctx.textAlign='center';
    // (name drawn in renderMap loop below)
  }
  ctx.restore();
}

// Monstro ORIENTADO de 2 casas (croc/lagarto), EM PÉ cobrindo as duas casas.
// A BASE alongada (no eixo cabeça→cauda) indica a direção; a criatura fica ereta
// na orientação natural da arte (cabeça à ESQUERDA) e é espelhada quando encara
// leste. Norte/sul ficam em pé centralizados — a base mostra a direção. hcx,hcy =
// centro de tela da casa-cabeça (frente = m.pos).
function drawOrientedMonster2D(ctx, m, hcx, hcy){
  const f = m.facing || [-1,0];
  // Ponto médio entre cabeça e cauda (cauda = atrás da cabeça).
  const mcx = hcx - f[0]*CELL/2, mcy = hcy - f[1]*CELL/2;
  // Ângulo da BASE (segue o eixo do corpo, indicando a direção).
  const angBase = (f[0]===1) ? Math.PI : (f[1]===-1) ? Math.PI/2 : (f[1]===1) ? -Math.PI/2 : 0;
  ctx.save(); ctx.translate(mcx, mcy); ctx.rotate(angBase);
  ctx.fillStyle='rgba(0,0,0,0.40)';
  ctx.beginPath(); ctx.ellipse(0, 0, CELL*0.95, CELL*0.40, 0, 0, Math.PI*2); ctx.fill();
  ctx.fillStyle='#2a241c';
  ctx.beginPath(); ctx.ellipse(0, 0, CELL*0.90, CELL*0.36, 0, 0, Math.PI*2); ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.55)'; ctx.lineWidth=1.5; ctx.stroke();
  ctx.restore();
  // Criatura EM PÉ (billboard): orientação natural da arte; espelha para leste.
  const img = m.image ? _getMonster2DImg(m.image) : null;
  ctx.save(); ctx.translate(mcx, mcy);
  if(f[0]===1) ctx.scale(-1, 1);   // encara leste → espelha (cabeça da arte é à esquerda)
  if(img && img.complete && img.naturalWidth){
    const ar = img.naturalWidth/img.naturalHeight;
    let w = CELL*1.9, h = w/ar;     // comprimento ≈ 2 casas (criatura larga e baixa)
    const hMax = CELL*1.7;
    if(h > hMax){ h = hMax; w = h*ar; }
    ctx.drawImage(img, -w/2, CELL*0.34 - h, w, h);   // pés perto da base
  } else {
    ctx.fillStyle='#3a2e1e'; ctx.font=`${CELL*0.7}px serif`;
    ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(m.emoji||'🦎',0,0);
  }
  ctx.restore();
}

function drawMonsterSprite(ctx, cx, cy, m){
  ctx.save(); ctx.translate(cx,cy);
  const r=CELL/2-3;
  // Drop shadow
  ctx.fillStyle='rgba(0,0,0,0.45)';
  ctx.beginPath(); ctx.ellipse(0,r*0.78,r*0.65,r*0.22,0,0,Math.PI*2); ctx.fill();
  // Red ambient glow
  ctx.save(); ctx.shadowColor='#c01010'; ctx.shadowBlur=16;
  ctx.strokeStyle='rgba(200,30,30,0.40)'; ctx.lineWidth=2.5;
  ctx.beginPath(); ctx.arc(0,0,r+4,0,Math.PI*2); ctx.stroke(); ctx.restore();

  // Billboard PNG (assets/pawns/monstros/<image>) — igual aos heróis: alto, pés
  // na base, SEM recorte circular. Sem imagem (ex.: servos animados) → procedural.
  const mImg = m.image ? _getMonster2DImg(m.image) : null;
  if(mImg && mImg.complete && mImg.naturalWidth){
    const ar = mImg.naturalWidth / mImg.naturalHeight;
    if(_FIT_TILE_PAWNS.has(m.image)){
      // Cobra + pedestal cabem INTEIROS no quadrado: largura e altura ≤ tile.
      // Ancorada na base (perto da sombra), sem ultrapassar o topo do tile.
      const alvo = CELL*_FIT_TILE_FRAC;
      let w = alvo, h = alvo;
      if(ar >= 1) h = alvo/ar; else w = alvo*ar;
      const bottomY = CELL*0.47;            // base assenta perto da borda inferior
      ctx.drawImage(mImg, -w/2, bottomY - h, w, h);
    } else if(_FILL_WIDTH_PAWNS.has(m.image)){
      // Ogro: preenche a LARGURA do quadrado (sem invadir vizinhos); a altura
      // segue a proporção (mini imponente). Ancorado na base, como os demais.
      const feetY = r*0.82;
      const w = CELL*_FILL_WIDTH_FRAC;
      const h = w/ar;
      ctx.drawImage(mImg, -w/2, feetY - h, w, h);
    } else {
      const feetY = r*0.82;
      const sf = _pawnScaleFactor(m.porte);  // porte da ficha (kobolds = pequeno)
      let h = CELL*1.55*sf;
      let w = h * ar;
      const wMax = CELL*1.5*sf;              // criaturas largas (aranha, lobo) podem ser largas
      if(w > wMax){ h *= wMax/w; w = wMax; }
      ctx.drawImage(mImg, -w/2, feetY - h, w, h);
    }
  } else {
    // Clip to circle + sprite procedural
    ctx.save(); ctx.beginPath(); ctx.arc(0,0,r+2,0,Math.PI*2); ctx.clip();
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.scale(SPR_SCALE, SPR_SCALE);
    switch(m.type){
      case 'goblin':    drawGoblin(ctx); break;
      case 'skeleton':  drawSkeleton(ctx); break;
      case 'orc':       drawOrc(ctx); break;
      case 'dark_mage': drawDarkMage(ctx); break;
      case 'troll':     drawTroll(ctx); break;
      case 'dragon':    drawDragon(ctx); break;
      default:
        ctx.fillStyle='#2a0808'; ctx.beginPath(); ctx.arc(0,0,r/SPR_SCALE,0,Math.PI*2); ctx.fill();
        ctx.font=`${(CELL-14)/SPR_SCALE}px serif`; ctx.fillText(m.emoji,0,0);
    }
    ctx.restore();
  }
  ctx.restore();
}

// ══ END SPRITE ENGINE ═══════════════════════════════════════════════════════

// ══ 3D DIORAMA MAP ═══════════════════════════════════════════════════════════

const WALL_RISE = Math.round(CELL * 0.50); // visible wall-face height — taller = more 3D depth

// ── Vision set: tiles currently visible to the local player ──────────────────
// Enemies outside this set are hidden (fog of war). Floor/walls keep using
// exploredSet so already-discovered tiles remain permanently visible.
// Uses Chebyshev distance (max of |dx|, |dy|) — square radius = torch lantern.
// Raio de detecção (Chebyshev) do jogador local: base 6 + bônus de Visão do
// Guerreiro da Luz (Richard). Espelha _get_raio_visao(p) no servidor (base 3),
// mas aqui a base é maior pois governa a visibilidade AO VIVO de inimigos.
function getSightRadius(me){
  const base = 6;
  if(me?.class_id === 'paladin' && me?.guerreiro_luz_ativo){
    return base + (me?.guerreiro_luz_bonus?.visao || 0);
  }
  return base;
}

function computeVisionSet(state, me){
  const set = new Set();
  // Tiles revelados por magia (Clarividência) são visíveis ao vivo — mesmo
  // longe e através de portas fechadas — para mostrar o conteúdo da sala.
  if(state && state.revealed)
    for(const [rx,ry] of state.revealed) set.add(`${rx},${ry}`);
  if(!me) return set;
  const [px,py] = me.pos;
  const SIGHT   = getSightRadius(me);   // dinâmico: 6, 7 ou 8 conforme o bônus de Richard
  for(const [ex,ey] of state.explored){
    if(Math.max(Math.abs(ex-px), Math.abs(ey-py)) <= SIGHT)
      set.add(`${ex},${ey}`);
  }
  return set;
}

function _computeWeaponRangeTiles(state, me) {
  const tiles = state.tiles;
  const H = tiles.length, W = tiles[0].length;
  const [px, py] = me.pos;
  const wRng = me.weapon?.range ?? null;
  const exploredSet = new Set(state.explored.map(([x,y])=>`${x},${y}`));
  const result = new Set();
  for(let y = 0; y < H; y++) for(let x = 0; x < W; x++) {
    if(tiles[y][x] !== TILE_FLOOR) continue;
    if(!exploredSet.has(`${x},${y}`)) continue;
    const dx = Math.abs(px - x), dy = Math.abs(py - y);
    if(dx === 0 && dy === 0) continue;
    const inR = wRng != null
      ? Math.max(dx, dy) <= wRng && GS.hasLineOfSight(state, px, py, x, y)
      : (dx === 1 && dy === 0) || (dx === 0 && dy === 1);
    if(inR) result.add(`${x},${y}`);
  }
  return result;
}

function renderMap(state){
  if(!state.tiles) return;
  _atualizarZonasMagia(state);   // zonas persistentes (Bola de Fogo) — vale p/ 2D e 3D
  if(mode3D){ renderMap3D(state); return; }
  const canvas=$('dungeon-canvas');
  const W=state.tiles[0].length, H=state.tiles.length;
  applyDPR(canvas, W*CELL, H*CELL);
  const ctx=canvas.getContext('2d');

  const exploredSet=new Set(state.explored.map(([x,y])=>`${x},${y}`));
  // Terreno visível AO VIVO: explorado (permanente) + revelado (Clarividência e
  // visão dos minions). Tiles só-revelados revertem à névoa sozinhos quando o
  // minion sai (state.revealed encolhe no próximo broadcast). exploredSet segue
  // governando lógica (BFS/alcance) — terrainSet governa só o desenho do mapa.
  const revealedSet=new Set((state.revealed||[]).map(([x,y])=>`${x},${y}`));
  const terrainSet = revealedSet.size
    ? new Set([...exploredSet, ...revealedSet]) : exploredSet;
  const me=state.players.find(p=>p.id===GS.myPid&&p.alive);
  const visionSet=computeVisionSet(state, me);
  const {closed:doorClosed} = GS.doorSets(state);

  const isAnimadosTurn2D = state.animados_turn === GS.myPid;
  const meAnimados2D = (state.players.find(p=>p.id===GS.myPid)?.animados||[]).filter(a=>a.vida_atual>0);
  const selAnimado2D = isAnimadosTurn2D && _animadoSel
    ? meAnimados2D.find(a=>a.id===_animadoSel) : null;
  const meuPris2D = state.prisoner && state.prisoner.alive && state.prisoner.freed
    && state.prisoner.rescuer_pid === GS.myPid;
  const selPris2D = isAnimadosTurn2D && _prisSel && meuPris2D ? state.prisoner : null;

  const reachable=new Set();
  if(selAnimado2D && selAnimado2D.moves_left>0)
    bfsReachable(state.tiles,exploredSet,selAnimado2D.pos[0],selAnimado2D.pos[1],selAnimado2D.moves_left,reachable);
  else if(selPris2D && (selPris2D.moves_left||0)>0)
    bfsReachable(state.tiles,exploredSet,selPris2D.pos[0],selPris2D.pos[1],selPris2D.moves_left,reachable);
  else if(!isAnimadosTurn2D&&GS.isMyTurn&&me&&me.moves_left>0)
    bfsReachable(state.tiles,exploredSet,me.pos[0],me.pos[1],me.moves_left,reachable);

  const attackable=new Set();
  // Ataque do jogador (apenas no próprio turno, fora do turno dos servos)
  if(!isAnimadosTurn2D&&GS.isMyTurn&&me&&!me.action_done){
    const wRng=me.weapon?.range??null;
    for(const m of state.monsters){
      if(!m||m.hp<=0) continue;
      const dx=Math.abs(me.pos[0]-m.pos[0]), dy=Math.abs(me.pos[1]-m.pos[1]);
      const inR=wRng!=null
        ? Math.max(dx,dy)<=wRng && GS.hasLineOfSight(state, me.pos[0],me.pos[1], m.pos[0],m.pos[1])
        : (dx===1&&dy===0)||(dx===0&&dy===1);
      if(inR) attackable.add(`${m.pos[0]},${m.pos[1]}`);
    }
  }
  // Alcance de ataque do animado selecionado (turno dos servos) ou em hover — aditivo
  const atkRefAnimado2D = selAnimado2D || window._animadoHover;
  if(atkRefAnimado2D && atkRefAnimado2D.pos){
    const [ax,ay]=atkRefAnimado2D.pos;
    const isElec2D = atkRefAnimado2D.especial === 'linha_3q';
    const atkRange2D = isElec2D ? 3 : 1;
    for(const [ddx,ddy] of [[1,0],[-1,0],[0,1],[0,-1]])
      for(let r=1; r<=atkRange2D; r++)
        attackable.add(`${ax+ddx*r},${ay+ddy*r}`);
  }

  const weaponRangeTiles = (window._weaponRangePreview && me && !isAnimadosTurn2D)
    ? _computeWeaponRangeTiles(state, me) : new Set();

  // Durante a mira de magia, oculta realces de movimento/ataque (mostra alcance/área).
  if(window._modoMagia){ reachable.clear(); attackable.clear(); }

  // ── PASS 0: Void background — near-black with deep dungeon darkness
  ctx.fillStyle='#040308';
  ctx.fillRect(0,0,W*CELL,H*CELL);

  // ── PASS 1: Floor tiles (stone flagstones) — explorado OU revelado ao vivo.
  // Portas (DOOR) também recebem chão por baixo (folha desenhada no PASS 3.5).
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!terrainSet.has(`${x},${y}`)) continue;
    const t=state.tiles[y][x];
    if(t===TILE_FLOOR || t===TILE_DOOR){
      const mid = matDaCasa(state, x, y);
      drawFloor3D(ctx, x, y, reachable.has(`${x},${y}`), attackable.has(`${x},${y}`), weaponRangeTiles.has(`${x},${y}`), mid);
      if(mid==='entulho') drawEntulho2D(ctx, x, y);
    }
  }

  // ── PASS 1.5: Realce de MAGIA — alcance (vermelho), zona (laranja), área (verde)
  _desenharSpellHL2D(ctx, exploredSet);

  // ── PASS 1.6: Explosão do Elemental de Fogo — overlay vermelho pulsante
  if(_explosionTiles && _explosionTiles.size){
    const pulse = 0.55 + 0.40 * (0.5 + 0.5 * Math.sin(performance.now() / 80));
    ctx.save();
    ctx.fillStyle = `rgba(255,60,0,${(0.38 * pulse).toFixed(3)})`;
    ctx.strokeStyle = `rgba(255,120,0,${(0.90 * pulse).toFixed(3)})`;
    ctx.lineWidth = 2.5;
    for(const key of _explosionTiles){
      const [ex,ey] = key.split(',').map(Number);
      if(!exploredSet.has(key)) continue;
      const EX=ex*CELL, EY=ey*CELL;
      ctx.fillRect(EX+1,EY+1,CELL-2,CELL-2);
      ctx.strokeRect(EX+2,EY+2,CELL-4,CELL-4);
    }
    ctx.restore();
  }

  // ── PASS 2: Wall south-face shadows
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!terrainSet.has(`${x},${y}`)) continue;
    if(state.tiles[y][x]===TILE_WALL){
      const sy=y+1;
      if(sy<H && state.tiles[sy][x]===TILE_FLOOR && terrainSet.has(`${x},${sy}`))
        drawWallSouthFace(ctx, x, y, matDaCasa(state, x, y));
    }
  }

  // ── PASS 3: Wall top faces
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!terrainSet.has(`${x},${y}`)) continue;
    if(state.tiles[y][x]===TILE_WALL)
      drawWallTop3D(ctx, x, y, matDaCasa(state, x, y));
  }

  // ── PASS 3.5: Doors — closed = wooden leaf (blocks sight), open = frame ──────
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(state.tiles[y][x]!==TILE_DOOR) continue;
    if(!terrainSet.has(`${x},${y}`)) continue;
    const k=`${x},${y}`;
    drawDoor2D(ctx, state, x, y, doorClosed.has(k));
  }

  // ── PASS 4: Impenetrable fog on unexplored tiles (Diablo-style pitch-black)
  ctx.fillStyle='rgba(4,3,8,0.96)';
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!terrainSet.has(`${x},${y}`))
      ctx.fillRect(x*CELL, y*CELL, CELL, CELL);
  }

  // ── PASS 5: Dramatic Diablo torchlight (multi-layer, orange-red inferno glow)
  if(me){
    const lcx=me.pos[0]*CELL+CELL/2, lcy=me.pos[1]*CELL+CELL/2;
    // Hot spot (intense orange-white at player)
    const g1=ctx.createRadialGradient(lcx,lcy,0,lcx,lcy,CELL*2.2);
    g1.addColorStop(0,   'rgba(255,230,120,0.32)');
    g1.addColorStop(0.35,'rgba(255,160,40,0.18)');
    g1.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle=g1; ctx.fillRect(0,0,W*CELL,H*CELL);
    // Mid-range warm amber
    const g2=ctx.createRadialGradient(lcx,lcy,0,lcx,lcy,CELL*5);
    g2.addColorStop(0,   'rgba(255,130,20,0.14)');
    g2.addColorStop(0.50,'rgba(220,80,10,0.08)');
    g2.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle=g2; ctx.fillRect(0,0,W*CELL,H*CELL);
    // Long-range atmospheric red (hellish dungeon ambience)
    const g3=ctx.createRadialGradient(lcx,lcy,0,lcx,lcy,CELL*8);
    g3.addColorStop(0,   'rgba(180,50,10,0.08)');
    g3.addColorStop(0.60,'rgba(100,20,5,0.04)');
    g3.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle=g3; ctx.fillRect(0,0,W*CELL,H*CELL);
  }
  // Static wall torch sconces — small orange glow on explored wall tiles
  for(let ty=0;ty<H;ty++) for(let tx=0;tx<W;tx++){
    if(!exploredSet.has(`${tx},${ty}`)) continue;
    if(state.tiles[ty][tx]!==TILE_WALL) continue;
    // Only occasional wall tiles get a torch (deterministic by position)
    const th=((tx*3761)^(ty*2399))&0xFF;
    if(th%7!==0) continue;
    // Check that a floor tile is adjacent (torches on walls near walkable areas)
    const hasFloorNear=[[0,1],[0,-1],[1,0],[-1,0]].some(([dx,dy])=>{
      const nx=tx+dx, ny=ty+dy;
      return nx>=0&&ny>=0&&nx<W&&ny<H && state.tiles[ny][nx]===TILE_FLOOR && exploredSet.has(`${nx},${ny}`);
    });
    if(!hasFloorNear) continue;
    const tcx=tx*CELL+CELL/2, tcy=ty*CELL+CELL/2;
    const tG=ctx.createRadialGradient(tcx,tcy,0,tcx,tcy,CELL*2.5);
    tG.addColorStop(0,   'rgba(255,180,50,0.18)');
    tG.addColorStop(0.35,'rgba(255,110,20,0.09)');
    tG.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle=tG; ctx.fillRect(0,0,W*CELL,H*CELL);
    // Small torch flame dot on the wall
    ctx.fillStyle='rgba(255,200,80,0.85)';
    ctx.beginPath(); ctx.arc(tcx,tcy,3,0,Math.PI*2); ctx.fill();
    ctx.fillStyle='rgba(255,255,200,0.6)';
    ctx.beginPath(); ctx.arc(tcx,tcy,1.2,0,Math.PI*2); ctx.fill();
  }

  // ── PASS 6: Edge vignette (dark corners — claustrophobic dungeon feel)
  const vW=W*CELL, vH=H*CELL;
  const vig=ctx.createRadialGradient(vW/2,vH/2,Math.min(vW,vH)*0.28,vW/2,vH/2,Math.max(vW,vH)*0.85);
  vig.addColorStop(0,'rgba(0,0,0,0)');
  vig.addColorStop(0.65,'rgba(0,0,0,0.10)');
  vig.addColorStop(1,'rgba(0,0,0,0.72)');
  ctx.fillStyle=vig; ctx.fillRect(0,0,vW,vH);

  // ── Canção Heroica: anel dourado de raio 5 ao redor do bardo cantando ──
  const _bardo = state.players.find(p => p.class_id==='bard' && p.alive && p.cancao_ativa);
  if(_bardo && exploredSet.has(`${_bardo.pos[0]},${_bardo.pos[1]}`)){
    const bcx=_bardo.pos[0]*CELL+CELL/2, bcy=_bardo.pos[1]*CELL+CELL/2;
    const r=(CANCAO_RAIO_CLIENT+0.5)*CELL;
    const pulso=0.25+0.18*(0.5+0.5*Math.sin(performance.now()/520));
    ctx.save();
    ctx.beginPath(); ctx.arc(bcx,bcy,r,0,Math.PI*2);
    ctx.fillStyle='rgba(200,169,81,0.05)'; ctx.fill();
    ctx.lineWidth=2; ctx.strokeStyle=`rgba(200,169,81,${pulso.toFixed(3)})`; ctx.stroke();
    ctx.restore();
  }

  // ── Room markers (chest / boss / trap icons)
  ctx.textAlign='center'; ctx.textBaseline='middle';
  for(const room of state.rooms){
    if(room.cleared||!exploredSet.has(`${room.cx},${room.cy}`)) continue;
    const icon={chest:'🎁',boss:'☠️',trap:'⚠'}[room.role];
    if(!icon) continue;
    const X=room.cx*CELL, Y=room.cy*CELL;
    ctx.fillStyle='rgba(0,0,0,0.55)'; ctx.fillRect(X+8,Y+8,CELL-16,CELL-16);
    ctx.font=`${Math.round(CELL*0.62)}px serif`; ctx.fillText(icon,X+CELL/2,Y+CELL/2);
  }

  // ── Traps
  for(const trap of state.traps){
    const [tx,ty]=trap.pos;
    if(!exploredSet.has(`${tx},${ty}`)) continue;
    const X=tx*CELL, Y=ty*CELL;
    ctx.fillStyle='rgba(200,30,30,0.22)'; ctx.fillRect(X+4,Y+4,CELL-8,CELL-8);
    ctx.font=`${Math.round(CELL*0.55)}px serif`; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText('⚠',X+CELL/2,Y+CELL/2);
  }

  // ── Armadilhas colocáveis (Passo 2) — borda verde = aliada; vermelha = ativada
  {
  const _meArm = state.players.find(p=>p.id===GS.myPid);
  for(const arm of (state.armadilhas||[])){
    const [ax,ay]=arm.pos;
    if(!exploredSet.has(`${ax},${ay}`)) continue;
    if(!_armadilhaVisivelParaMim(arm, _meArm)) continue;   // escondida até ser revelada
    const X=ax*CELL, Y=ay*CELL;
    ctx.fillStyle = arm.ativada ? 'rgba(255,70,55,0.28)' : 'rgba(110,200,120,0.18)';
    ctx.fillRect(X+4,Y+4,CELL-8,CELL-8);
    ctx.lineWidth=2;
    ctx.strokeStyle = arm.ativada ? 'rgba(255,70,55,0.85)'
                    : arm.aliada ? 'rgba(110,210,120,0.75)' : 'rgba(255,150,40,0.75)';
    ctx.strokeRect(X+4.5,Y+4.5,CELL-9,CELL-9);
    // Imagem (PNG de assets/objetos) cobre o tile, mantendo proporção; senão, o ícone.
    const _aImg = arm.image ? _getArmadilha2DImg(arm.image) : null;
    if(_aImg){
      const ar = _aImg.naturalWidth / _aImg.naturalHeight;
      let dw = CELL-8, dh = (CELL-8)/ar;
      if(dh > CELL-8){ dh = CELL-8; dw = (CELL-8)*ar; }
      ctx.drawImage(_aImg, X+(CELL-dw)/2, Y+(CELL-dh)/2, dw, dh);
    } else {
      ctx.font=`${Math.round(CELL*0.5)}px serif`; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(arm.icone||'🪤',X+CELL/2,Y+CELL/2);
    }
  }
  }

  // ── Stairs (dungeon entrance / exit)
  if(state.stairs_pos){
    const [sx,sy]=state.stairs_pos;
    if(exploredSet.has(`${sx},${sy}`)){
      const X=sx*CELL, Y2=sy*CELL;
      // Stone step tones
      ctx.fillStyle='rgba(60,42,18,0.72)'; ctx.fillRect(X+3,Y2+3,CELL-6,CELL-6);
      ctx.strokeStyle='rgba(180,130,40,0.55)'; ctx.lineWidth=1;
      const steps=4, sh=(CELL-14)/steps;
      for(let s=0;s<steps;s++){
        const sy2=Y2+7+s*sh;
        ctx.fillStyle=`rgba(${90+s*12},${65+s*9},${28+s*7},0.65)`;
        ctx.fillRect(X+6+s*3,sy2,CELL-14-s*6,sh-1);
        ctx.strokeRect(X+6+s*3+0.5,sy2+0.5,CELL-15-s*6,sh-2);
      }
      // Persistent gold glow (staircase is always interactive)
      const gst=ctx.createRadialGradient(X+CELL/2,Y2+CELL/2,0,X+CELL/2,Y2+CELL/2,CELL*0.75);
      gst.addColorStop(0,'rgba(255,210,60,0.28)');
      gst.addColorStop(1,'rgba(0,0,0,0)');
      ctx.fillStyle=gst; ctx.fillRect(X-CELL/4,Y2-CELL/4,CELL*1.5,CELL*1.5);
      // Icon
      ctx.font=`${Math.round(CELL*0.45)}px serif`; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText('🪜',X+CELL/2,Y2+CELL/2);
      // Small label
      ctx.font=`bold ${Math.round(CELL*0.16)}px monospace`; ctx.textAlign='center'; ctx.textBaseline='top';
      ctx.fillStyle='rgba(255,220,80,0.90)';
      ctx.fillText('SAÍDA',X+CELL/2,Y2+CELL-14);
    }
  }

  // ── Exit tile (Fase 3 — masmorra autorada): bandeira de chegada 🏁
  if(GS.exitPos){
    const [ex,ey]=GS.exitPos;
    if(exploredSet.has(`${ex},${ey}`)){
      const X=ex*CELL, Y2=ey*CELL;
      // Glow azul-esverdeado (distinto do dourado da escada)
      const egl=ctx.createRadialGradient(X+CELL/2,Y2+CELL/2,0,X+CELL/2,Y2+CELL/2,CELL*0.78);
      egl.addColorStop(0,'rgba(60,220,180,0.32)');
      egl.addColorStop(1,'rgba(0,0,0,0)');
      ctx.fillStyle=egl; ctx.fillRect(X-CELL/4,Y2-CELL/4,CELL*1.5,CELL*1.5);
      ctx.font=`${Math.round(CELL*0.5)}px serif`; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText('🏁',X+CELL/2,Y2+CELL/2);
      ctx.font=`bold ${Math.round(CELL*0.16)}px monospace`; ctx.textAlign='center'; ctx.textBaseline='top';
      ctx.fillStyle='rgba(80,230,190,0.92)';
      ctx.fillText('CHEGADA',X+CELL/2,Y2+CELL-14);
    }
  }

  // ── Physical chests (2D overlay — gold glow + icon)
  ctx.textAlign='center'; ctx.textBaseline='middle';
  for(const chest of (state.chests||[])){
    const [cx2,cy2]=chest.pos;
    if(!exploredSet.has(`${cx2},${cy2}`)) continue;
    const X=cx2*CELL, Y=cy2*CELL;
    // Gold glow halo
    const cglow=ctx.createRadialGradient(X+CELL/2,Y+CELL/2,0,X+CELL/2,Y+CELL/2,CELL*0.82);
    cglow.addColorStop(0,'rgba(255,200,40,0.38)');
    cglow.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle=cglow; ctx.fillRect(X,Y,CELL,CELL);
    // Chest icon
    ctx.font=`${Math.round(CELL*0.58)}px serif`;
    ctx.fillText('🎁',X+CELL/2,Y+CELL/2);
    // Item count badge
    const total=(chest.items||[]).length+(chest.gold>0?1:0);
    if(total>0){
      ctx.font=`bold ${Math.round(CELL*0.18)}px monospace`;
      ctx.fillStyle='#ffe060'; ctx.fillText(`×${total}`,X+CELL/2,Y+CELL-10);
    }
  }

  // ── Decorations (2D overlay — emoji at footprint center + subtle fill)
  {
    const decors = GS.decorations;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    // Chão (special:floor) primeiro → fica EMBAIXO; objetos empilhados desenham por cima.
    const decorsDrawOrder = [...decors].sort((a, b) => ((a.special === 'floor') ? 0 : 1) - ((b.special === 'floor') ? 0 : 1));
    for (const d of decorsDrawOrder) {
      const tiles = GS.decorTilesOf(d);
      // Only draw if at least one tile in the footprint has been explored
      if (!tiles.some(([tx2, ty2]) => exploredSet.has(`${tx2},${ty2}`))) continue;
      // Subtle fill on all occupied tiles
      ctx.fillStyle = 'rgba(120,200,160,0.12)';
      for (const [tx2, ty2] of tiles) ctx.fillRect(tx2 * CELL, ty2 * CELL, CELL, CELL);
      // Image or emoji at footprint center
      const avgX = tiles.reduce((s, t) => s + t[0], 0) / tiles.length;
      const avgY = tiles.reduce((s, t) => s + t[1], 0) / tiles.length;
      const ecx = (avgX + 0.5) * CELL;
      const ecy = (avgY + 0.5) * CELL;
      // Escala visual (vscale): largura ×sx, altura ×sy (cresce p/ cima, base ancorada).
      const _vs = Array.isArray(d.vscale) ? d.vscale : [1, 1];
      const _sx = _vs[0] || 1, _sy = _vs[1] || 1;
      const _oImg = d.image ? _getObjeto2DImg(d.image) : null;
      if (_oImg && d.special === 'floor') {
        // Chão: preenche cada casa do footprint borda-a-borda (sem manter proporção).
        for (const [tx2, ty2] of tiles) ctx.drawImage(_oImg, tx2 * CELL, ty2 * CELL, CELL, CELL);
      } else if (_oImg) {
        const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
        const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
        const px = minX * CELL, py = minY * CELL;
        const pw = (maxX - minX + 1) * CELL, ph = (maxY - minY + 1) * CELL;
        const ar = _oImg.naturalWidth / _oImg.naturalHeight;
        const _ang = _facingAngle2D(d.facing);
        if (_ang === 0) {
          // ajusta mantendo proporção, ancorado embaixo (caminho original)
          let dw = pw, dh = pw / ar;
          if (dh > ph) { dh = ph; dw = ph * ar; }
          dw *= _sx; dh *= _sy;
          ctx.drawImage(_oImg, px + (pw - dw) / 2, py + (ph - dh), dw, dh);
        } else {
          // girado: encaixa no frame local (caixa possivelmente trocada p/ 90°/270°)
          // e gira sobre o centro do footprint.
          const _rot90 = (_ang === Math.PI / 2 || _ang === -Math.PI / 2);
          const boxW = _rot90 ? ph : pw, boxH = _rot90 ? pw : ph;
          let dw = boxW, dh = boxW / ar;
          if (dh > boxH) { dh = boxH; dw = boxH * ar; }
          dw *= _sx; dh *= _sy;
          ctx.save();
          ctx.translate(px + pw / 2, py + ph / 2);
          ctx.rotate(_ang);
          ctx.drawImage(_oImg, -dw / 2, -dh / 2, dw, dh);
          ctx.restore();
        }
      } else if (_sx === 1 && _sy === 1) {
        ctx.font = `${Math.floor(CELL * 0.8)}px serif`;
        ctx.fillText(d.emoji || '🪑', ecx, ecy);
      } else {
        // emoji escalado: ancorado na base do footprint, crescendo p/ cima
        const baseY = (Math.max(...tiles.map(t => t[1])) + 1) * CELL;
        ctx.font = `${Math.floor(CELL * 0.8 * Math.max(_sx, _sy))}px serif`;
        ctx.textBaseline = 'alphabetic';
        ctx.fillText(d.emoji || '🪑', ecx, baseY - 2);
        ctx.textBaseline = 'middle';
      }
      // Loot indicator badge
      if (d.tem_loot) {
        ctx.font = `bold ${Math.round(CELL * 0.18)}px monospace`;
        ctx.fillStyle = '#ffe060';
        ctx.fillText('💰', ecx + CELL * 0.28, ecy - CELL * 0.28);
      }
    }
    // O chão (special:floor) é PISO e foi desenhado por cima do realce de movimento
    // (PASS 1). Re-aplica o destaque azul/vermelho nas casas de chão para que a
    // indicação de movimentação/ataque apareça sobre a grama, como em piso normal.
    for (const d of decors) {
      if (d.special !== 'floor') continue;
      for (const [tx2, ty2] of GS.decorTilesOf(d)) {
        if (!exploredSet.has(`${tx2},${ty2}`)) continue;
        const k = `${tx2},${ty2}`, X = tx2 * CELL, Y = ty2 * CELL;
        if (reachable.has(k)) {
          const fa = 0.26 + 0.26 * _movePulse, pa = 0.70 + 0.30 * _movePulse;
          ctx.fillStyle = `rgba(30,107,255,${fa.toFixed(2)})`; ctx.fillRect(X + 2, Y + 2, CELL - 4, CELL - 4);
          ctx.strokeStyle = `rgba(60,140,255,${pa.toFixed(2)})`; ctx.lineWidth = 2; ctx.strokeRect(X + 2, Y + 2, CELL - 4, CELL - 4);
        } else if (attackable.has(k)) {
          ctx.fillStyle = 'rgba(255,30,30,0.13)'; ctx.fillRect(X + 2, Y + 2, CELL - 4, CELL - 4);
          ctx.strokeStyle = 'rgba(255,60,60,0.78)'; ctx.lineWidth = 2; ctx.strokeRect(X + 2, Y + 2, CELL - 4, CELL - 4);
        }
      }
    }
  }

  // ── Monsters: only visible within player's vision radius
  for(const m of state.monsters){
    const [mtx,mty]=m.pos;
    if(!visionSet.has(`${mtx},${mty}`)) continue;
    // Deslize fiel (entity_step): interpola a posição durante a animação.
    const _mStep = _serverStepPos(m.id);
    const mx = _mStep ? _mStep.x : mtx;
    const my = _mStep ? _mStep.y : mty;
    const cx=mx*CELL+CELL/2, cy=my*CELL+CELL/2;
    if(m.oriented){
      drawOrientedMonster2D(ctx, m, cx, cy);   // deitado, cobrindo as 2 casas
    } else {
      drawMiniBase(ctx, cx, cy, '#c02020', false);
      drawMonsterSprite(ctx, cx, cy-3, m);
    }
    // HP bar
    const pct=m.hp/m.max_hp;
    const barH=Math.max(4,Math.round(CELL*0.08));
    ctx.fillStyle='rgba(0,0,0,0.75)'; ctx.fillRect(mx*CELL+3,my*CELL+2,CELL-6,barH);
    ctx.fillStyle=pct>.5?'#27ae60':pct>.25?'#e67e22':'#e74c3c';
    ctx.fillRect(mx*CELL+3,my*CELL+2,(CELL-6)*pct,barH);
    ctx.strokeStyle='rgba(0,0,0,0.55)'; ctx.lineWidth=0.6;
    ctx.strokeRect(mx*CELL+3,my*CELL+2,CELL-6,barH);
    const mNameFs=Math.round(CELL*0.125);
    ctx.fillStyle='rgba(255,90,90,0.95)'; ctx.font=`bold ${mNameFs}px monospace`;
    ctx.textAlign='center'; ctx.textBaseline='top';
    ctx.fillText(m.name.slice(0,10), cx, my*CELL+barH+3);
  }

  // ── Corpses (cadáveres): alvos de Animar Mortos — ícone esmaecido roxo ──────
  for(const c of (state.corpses||[])){
    const [cxp,cyp]=c.pos;
    if(!visionSet.has(`${cxp},${cyp}`)) continue;
    const cx=cxp*CELL+CELL/2, cy=cyp*CELL+CELL/2;
    ctx.save();
    ctx.globalAlpha=0.55;
    ctx.font=`${Math.round(CELL*0.5)}px serif`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(c.icone||'💀', cx, cy);
    ctx.restore();
  }

  // ── Prisioneiro (Fase 3): cativo (acorrentado) vs. seguindo; barra de HP ──────
  const _pris = GS.prisoner;
  if(_pris && _pris.alive){
    const [pxr,pyr]=_pris.pos;
    // Interpola a posição visual durante a animação de passo (igual aos minions):
    // desliza casa a casa pelo caminho enquanto _mininoAnimState['prisoner'] existir.
    let drawX = pxr, drawY = pyr;
    const _pVis = _mininoAnimState.get('prisoner');
    if(_pVis && _pVis.pathPts){
      const segs = Math.max(1, _pVis.pathPts.length - 1);
      const tAll = Math.min((performance.now() - _pVis.startTime) / _pVis.dur, 1);
      const f  = tAll * segs;
      const si = Math.min(Math.floor(f), segs - 1);
      const st = easeInOut(f - si);
      const [x0,y0] = _pVis.pathPts[si];
      const [x1,y1] = _pVis.pathPts[si+1];
      drawX = x0 + (x1 - x0) * st;
      drawY = y0 + (y1 - y0) * st;
    }
    const _visPathP = _pVis && _pVis.pathPts
      ? _pVis.pathPts.some(([px,py]) => visionSet.has(`${px},${py}`) || exploredSet.has(`${px},${py}`))
      : false;
    if(visionSet.has(`${pxr},${pyr}`) || exploredSet.has(`${pxr},${pyr}`) || _visPathP){
      const cx=drawX*CELL+CELL/2, cy=drawY*CELL+CELL/2;
      // Anel de seleção quando o controlador o selecionou (janela pós-turno).
      if(_prisSel && _pris.freed && _pris.rescuer_pid===GS.myPid && state.animados_turn===GS.myPid){
        ctx.save();
        ctx.strokeStyle='#ffffff'; ctx.lineWidth=3;
        ctx.beginPath(); ctx.arc(cx, cy, CELL*0.42, 0, Math.PI*2); ctx.stroke();
        ctx.restore();
      }
      // Base do peão: tom amarelado se aliado/seguindo, acinzentado se cativo.
      drawMiniBase(ctx, cx, cy, _pris.freed?'#2e90c0':'#8a6d3b', false);
      const _pImg = _getPrisoner2DImg(_pris.image);
      if(_pImg && _pImg.complete && _pImg.naturalWidth){
        const sz = Math.round(CELL*0.78);
        ctx.drawImage(_pImg, cx - sz/2, cy - sz/2 - 3, sz, sz);
      } else {
        ctx.font=`${Math.round(CELL*0.46)}px serif`;
        ctx.textAlign='center'; ctx.textBaseline='middle';
        ctx.fillText(_pris.freed?'🧍':'⛓️', cx, cy-3);
      }
      // Barra de HP simples
      const max=_pris.max_hp||_pris.hp||1;
      const pct=Math.max(0,Math.min(1,_pris.hp/max));
      const barH=Math.max(4,Math.round(CELL*0.08));
      const bx=drawX*CELL, by=drawY*CELL;
      ctx.fillStyle='rgba(0,0,0,0.75)'; ctx.fillRect(bx+3,by+2,CELL-6,barH);
      ctx.fillStyle=pct>.5?'#27ae60':pct>.25?'#e67e22':'#e74c3c';
      ctx.fillRect(bx+3,by+2,(CELL-6)*pct,barH);
      ctx.strokeStyle='rgba(0,0,0,0.55)'; ctx.lineWidth=0.6;
      ctx.strokeRect(bx+3,by+2,CELL-6,barH);
      const fs=Math.round(CELL*0.125);
      ctx.fillStyle='rgba(255,210,120,0.95)'; ctx.font=`bold ${fs}px monospace`;
      ctx.textAlign='center'; ctx.textBaseline='top';
      ctx.fillText('Prisioneiro', cx, by+barH+3);
    }
  }

  // ── Animados (servos do Pedro / elementais): peão do MONSTRO ORIGINAL, aliado ──
  for(const pl of state.players){
    for(const a of (pl.animados||[])){
      if(!a.pos) continue;
      const [ax,ay]=a.pos;
      // Interpola posição visual durante animação 2D de passo (lerp easeInOut).
      // Enquanto _mininoAnimState tiver entrada para este animado, desenhamos na
      // posição interpolada; ao final a posição real do servidor já foi atualizada.
      let drawX = ax, drawY = ay;
      const _aStep = _serverStepPos(a.id);   // deslize fiel (servo auto-comandado)
      const _aVis = _mininoAnimState.get(a.id);
      if(_aStep){
        drawX = _aStep.x; drawY = _aStep.y;
      } else if(_aVis && _aVis.pathPts){
        // Caminho contínuo: encontra o segmento atual pelo tempo decorrido.
        const segs = Math.max(1, _aVis.pathPts.length - 1);
        const tAll = Math.min((performance.now() - _aVis.startTime) / _aVis.dur, 1);
        const f  = tAll * segs;
        const si = Math.min(Math.floor(f), segs - 1);
        const st = easeInOut(f - si);
        const [x0,y0] = _aVis.pathPts[si];
        const [x1,y1] = _aVis.pathPts[si+1];
        drawX = x0 + (x1 - x0) * st;
        drawY = y0 + (y1 - y0) * st;
      } else if(_aVis){
        const t = easeInOut(Math.min((performance.now() - _aVis.startTime) / _aVis.dur, 1));
        drawX = _aVis.fromX + (_aVis.toX - _aVis.fromX) * t;
        drawY = _aVis.fromY + (_aVis.toY - _aVis.fromY) * t;
      }
      // Visibilidade: a casa atual OU algum ponto do caminho devem estar à vista.
      const _visPath = _aVis && _aVis.pathPts
        ? _aVis.pathPts.some(([px,py]) => visionSet.has(`${px},${py}`))
        : (_aVis && visionSet.has(`${_aVis.toX},${_aVis.toY}`));
      if(!visionSet.has(`${ax},${ay}`) && !_visPath) continue;
      const cx=drawX*CELL+CELL/2, cy=drawY*CELL+CELL/2;
      drawMiniBase(ctx, cx, cy, '#9900cc', false);
      // Sprite original do monstro (goblin/orc/etc.) — fallback p/ ícone via emoji.
      drawMonsterSprite(ctx, cx, cy-3, { type:a.tipo, emoji:a.icone, name:a.nome });
      // Anel roxo de "animado aliado"; branco e grosso se selecionado.
      ctx.save();
      ctx.strokeStyle = (_animadoSel===a.id) ? '#ffffff' : '#cc44ff';
      ctx.lineWidth   = (_animadoSel===a.id) ? 3 : 2;
      ctx.beginPath(); ctx.arc(cx, cy-3, CELL/2-2, 0, Math.PI*2); ctx.stroke();
      ctx.restore();
      // Barra de vida (usa posição visual drawX/drawY)
      const pct=Math.max(0, (a.vida_atual||0)/(a.vida_max||1));
      const barH=Math.max(4,Math.round(CELL*0.08));
      ctx.fillStyle='rgba(0,0,0,0.75)'; ctx.fillRect(drawX*CELL+3,drawY*CELL+2,CELL-6,barH);
      ctx.fillStyle='#cc44ff'; ctx.fillRect(drawX*CELL+3,drawY*CELL+2,(CELL-6)*pct,barH);
    }
  }

  // ── Players: base disc then hero sprite
  ctx.textAlign='center'; ctx.textBaseline='middle';
  for(const p of state.players){
    if(!p.alive) continue;
    if(p.connected === false) continue;   // desconectado: deixou a masmorra, não desenha
    const [px,py]=p.pos;
    const X=px*CELL, Y=py*CELL, cx=X+CELL/2, cy=Y+CELL/2;
    const isCur=p.id===state.current_turn, isMe=p.id===GS.myPid;
    drawMiniBase(ctx, cx, cy, p.color, isCur||isMe);
    drawHeroSprite(ctx, cx, cy-3, p.class_id, p.color, isMe, isCur);
    if(isMe||isCur){
      const label=p.name.slice(0,9);
      const tagFs=Math.round(CELL*0.14);
      ctx.font=`bold ${tagFs}px monospace`; ctx.textAlign='center';
      const tw=ctx.measureText(label).width;
      ctx.fillStyle='rgba(0,0,0,0.88)';
      ctx.fillRect(cx-tw/2-4,Y+CELL-tagFs-4,tw+8,tagFs+2);
      ctx.fillStyle=isMe?'#f0c040':'#ffffff';
      ctx.textBaseline='top'; ctx.fillText(label,cx,Y+CELL-tagFs-3);
      ctx.textBaseline='middle';
    }
  }
}

// ── PAINTERS PROCEDURAIS DE MATERIAL (compartilhados 2D tile + 3D textura) ────
// Cada painter desenha UMA superfície preenchendo [ox,oy, ox+size, oy+size].
// r = função RNG determinística (0..1). Usados pelo 2D (size=CELL) e pelo 3D
// (size=256, textura cacheada) para a aparência ser idêntica nas duas vistas.
function _rng(seed){ let s=(seed>>>0)||1; return function(){ s=(s*1664525+1013904223)>>>0; return s/4294967296; }; }

function paintGrass(ctx, ox, oy, size, r){
  const g=ctx.createLinearGradient(ox,oy,ox,oy+size);
  g.addColorStop(0,'#3f7a35'); g.addColorStop(1,'#2c5a26');
  ctx.fillStyle=g; ctx.fillRect(ox,oy,size,size);
  for(let n=0;n<Math.round(size*0.36);n++){ const px=ox+r()*size,py=oy+r()*size,rr=size*(0.05+r()*0.13);
    ctx.fillStyle = r()<0.5 ? 'rgba(58,110,44,0.5)' : 'rgba(96,150,60,0.4)';
    ctx.beginPath(); ctx.ellipse(px,py,rr,rr*0.7,r()*3,0,Math.PI*2); ctx.fill(); }
  const blades=Math.round(size*1.15);
  for(let n=0;n<blades;n++){ const px=ox+r()*size,py=oy+size*0.06+r()*size*0.94,h=size*(0.06+r()*0.14),lean=(r()-0.5)*size*0.08;
    const sh=70+r()*70; ctx.strokeStyle=`rgb(${(sh*0.45)|0},${sh|0},${(sh*0.35)|0})`;
    ctx.lineWidth=Math.max(1,size/64); ctx.beginPath(); ctx.moveTo(px,py); ctx.lineTo(px+lean,py-h); ctx.stroke(); }
}

function paintDirt(ctx, ox, oy, size, r){
  ctx.fillStyle='#6b4a2e'; ctx.fillRect(ox,oy,size,size);
  for(let n=0;n<Math.round(size*0.47);n++){ const px=ox+r()*size,py=oy+r()*size,rr=size*(0.06+r()*0.18);
    ctx.fillStyle = r()<0.5 ? 'rgba(60,40,24,0.5)' : 'rgba(120,88,54,0.45)';
    ctx.beginPath(); ctx.ellipse(px,py,rr,rr*0.8,r()*3,0,Math.PI*2); ctx.fill(); }
  for(let n=0;n<Math.round(size*0.2);n++){ const px=ox+r()*size,py=oy+r()*size,rr=size*(0.012+r()*0.025);
    const s=80+r()*60; ctx.fillStyle=`rgb(${s|0},${(s*0.85)|0},${(s*0.7)|0})`;
    ctx.beginPath(); ctx.ellipse(px,py,rr,rr*0.8,0,0,Math.PI*2); ctx.fill();
    ctx.fillStyle='rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(px+rr*0.4,py+rr*0.4,rr,rr*0.7,0,0,Math.PI*2); ctx.fill(); }
}

function paintBrick(ctx, ox, oy, size, r, base, mortar){
  ctx.fillStyle=mortar; ctx.fillRect(ox,oy,size,size);
  const rh=size*0.17, bw=size*0.5; let row=0;
  for(let by=oy; by<oy+size; by+=rh){ const off=(row%2)?bw*0.5:0;
    for(let bx=ox-off; bx<ox+size; bx+=bw){ const v=(r()*16-8)|0;
      ctx.fillStyle=`rgb(${Math.max(0,base[0]+v)},${Math.max(0,base[1]+v)},${Math.max(0,base[2]+v)})`;
      ctx.fillRect(bx+1.5, by+1.5, bw-3, rh-3);
      ctx.fillStyle='rgba(255,255,255,0.05)'; ctx.fillRect(bx+1.5, by+1.5, bw-3, Math.max(1,size/40)); }
    row++; }
}

function paintCave(ctx, ox, oy, size, r){
  ctx.fillStyle='#241509'; ctx.fillRect(ox,oy,size,size);   // fundo marrom escuro (fendas)
  const step=size*0.22, pts=[];
  for(let gy=0;gy<5;gy++) for(let gx=0;gx<5;gx++)
    pts.push([ox+gx*step+step*0.3+(r()-0.5)*step*0.72, oy+gy*step+step*0.3+(r()-0.5)*step*0.72]);
  for(const p of pts){ const rad=size*(0.09+r()*0.10), nv=7+(r()*4|0), b=95+r()*60;
    // marrom forte: muito vermelho, pouco azul
    const R=Math.min(255,b*1.2|0), G=Math.min(255,b*0.72|0), B=Math.min(255,b*0.42|0);
    ctx.fillStyle=`rgb(${R},${G},${B})`;
    ctx.beginPath();
    for(let k=0;k<nv;k++){ const a=k/nv*Math.PI*2, rr=rad*(0.55+r()*0.75);  // contorno bem irregular
      const xx=p[0]+Math.cos(a)*rr, yy=p[1]+Math.sin(a)*rr; k?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy); }
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.6)'; ctx.lineWidth=Math.max(1,size/40); ctx.stroke();
    // sombra/fenda (relevo rugoso) e realce de tocha
    ctx.fillStyle='rgba(0,0,0,0.30)';
    ctx.beginPath(); ctx.ellipse(p[0]+rad*0.28,p[1]+rad*0.32,rad*0.5,rad*0.34,0,0,Math.PI*2); ctx.fill();
    ctx.fillStyle='rgba(255,200,130,0.16)';
    ctx.beginPath(); ctx.ellipse(p[0]-rad*0.32,p[1]-rad*0.36,rad*0.42,rad*0.28,0,0,Math.PI*2); ctx.fill(); }
}

// Lajota de pedra (textura 3D) numa cor-base — usada para pedra_negra (preta forte).
function paintStone(ctx, ox, oy, size, r, base){
  ctx.fillStyle='#06050a'; ctx.fillRect(ox,oy,size,size);
  const sub=2, sp=size/sub, grt=size*0.03;
  for(let sy=0;sy<sub;sy++) for(let sx=0;sx<sub;sx++){
    const v=(r()*22-11)|0, bx=ox+sx*sp+grt, by=oy+sy*sp+grt, bw=sp-grt*1.6, bh=sp-grt*1.6;
    const r0=Math.max(0,base[0]+v), g0=Math.max(0,base[1]+v), b0=Math.max(0,base[2]+Math.floor(v*0.7));
    const g=ctx.createLinearGradient(bx,by,bx+bw,by+bh);
    g.addColorStop(0,`rgb(${r0+26},${g0+24},${b0+24})`);
    g.addColorStop(0.5,`rgb(${r0},${g0},${b0})`);
    g.addColorStop(1,`rgb(${Math.max(0,r0-18)},${Math.max(0,g0-16)},${Math.max(0,b0-14)})`);
    ctx.fillStyle=g; ctx.fillRect(bx,by,bw,bh);
    ctx.fillStyle='rgba(0,0,0,0.42)'; ctx.fillRect(bx,by+bh-2,bw,2); ctx.fillRect(bx+bw-2,by,2,bh);
    if(r()<0.3){ ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=Math.max(1,size/120);
      const cx=bx+r()*bw, cy=by+r()*bh; ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(cx+size*0.06,cy+size*0.04); ctx.stroke(); }
  }
}

function paintRubble(ctx, ox, oy, size, r){
  ctx.fillStyle='#2b2620'; ctx.fillRect(ox,oy,size,size);
  for(let n=0;n<Math.round(size*0.13);n++){ const px=ox+size*0.06+r()*size*0.88,py=oy+size*0.06+r()*size*0.88,
      rw=size*(0.06+r()*0.13),rh=size*(0.05+r()*0.10), t=60+r()*55;
    ctx.fillStyle=`rgb(${t|0},${(t-7)|0},${(t-16)|0})`;
    ctx.beginPath(); ctx.ellipse(px,py,rw,rh,(r()-0.5)*3,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=Math.max(1,size/64); ctx.stroke();
    ctx.fillStyle='rgba(255,235,200,0.10)'; ctx.fillRect(px-rw*0.5,py-rh*0.7,rw,Math.max(1.5,size/40)); }
}

// ── PALETAS 2D DOS MATERIAIS ─────────────────────────────────────────────────
// base [r,g,b] da pedra/superfície; accent decide os detalhes procedurais.
// Espelha os ids de server.MATERIAIS. Pisos coloridos são cosméticos.
const MAT_PALETTE_2D = {
  // pisos
  pedra_cinza: { base: [44, 42, 50],  accent: 'stone' },
  terra:       { base: [74, 56, 38],  accent: 'dirt'  },
  grama:       { base: [46, 78, 40],  accent: 'grass' },
  pedra_negra: { base: [20, 19, 24],  accent: 'stone' },
  entulho:     { base: [70, 66, 58],  accent: 'rubble' },
  // paredes (topo)
  pedra_normal:  { base: [132, 130, 140], accent: 'wallStone' },
  enegrecida:    { base: [24, 23, 28],   accent: 'blackbrick' },
  pedra_caverna: { base: [120, 82, 46],  accent: 'cave' },
  desmoronada:   { base: [96, 88, 76],   accent: 'wallRubble' },
};
// Resolve o material de uma casa para render (default por estrutura do tile).
function matDaCasa(state, x, y){
  const m = state && state.materiais;
  const id = m && m[`${x},${y}`];
  if(id && MAT_PALETTE_2D[id]) return id;
  return (state.tiles[y][x] === TILE_WALL) ? 'pedra_normal' : 'pedra_cinza';
}

// ── DIABLO-STYLE FLOOR TILE — dark charcoal flagstones with blood & bone details
function drawFloor3D(ctx, x, y, isReachable, isAttackable, isWeaponPreview, matId){
  const X=x*CELL, Y=y*CELL;
  const h=((x*7919)^(y*3467)^(x<<5)^(y>>2))&0xFFFF;
  const pal = MAT_PALETTE_2D[matId] || MAT_PALETTE_2D.pedra_cinza;
  const [BR, BG, BB] = pal.base;

  // Estilos não-pedra têm painter próprio (sem grade de lajota).
  if(pal.accent==='grass'){ paintGrass(ctx, X, Y, CELL, _rng((x*53^y*97^7)>>>0)); }
  else if(pal.accent==='dirt'){ paintDirt(ctx, X, Y, CELL, _rng((x*29^y*71^3)>>>0)); }
  else {
  // Deep mortar joints — near-black with faint blue-gray
  ctx.fillStyle='#06050a';
  ctx.fillRect(X,Y,CELL,CELL);

  // 2×2 flagstone slabs — dark charcoal Diablo palette
  const sub=2, sp=CELL/sub, grt=2;
  for(let sy=0;sy<sub;sy++) for(let sx=0;sx<sub;sx++){
    const sh=((h^(sx*37+sy*11))^(sx<<9)^(sy<<5))&0xFFFF;
    const v=(sh%24)-12;

    const bx=X+sx*sp+grt, by=Y+sy*sp+grt;
    const bw=sp-grt*1.5, bh=sp-grt*1.5;

    // Dark gray-charcoal stone — slight blue-purple undertone (cave feel)
    const r0=Math.min(255,BR+v), g0=Math.min(255,BG+v), b0=Math.min(255,BB+Math.floor(v*0.6));

    // Gradient: top-left torch-lit, bottom-right shadow
    const sg=ctx.createLinearGradient(bx,by,bx+bw,by+bh);
    sg.addColorStop(0,  `rgb(${Math.min(255,r0+32)},${Math.min(255,g0+28)},${Math.min(255,b0+24)})`);
    sg.addColorStop(0.5,`rgb(${r0},${g0},${b0})`);
    sg.addColorStop(1,  `rgb(${Math.max(0,r0-24)},${Math.max(0,g0-20)},${Math.max(0,b0-18)})`);
    ctx.fillStyle=sg; ctx.fillRect(bx,by,bw,bh);

    // Torch-warm bevel top/left
    ctx.fillStyle='rgba(255,180,60,0.07)';
    ctx.fillRect(bx,by,bw,2); ctx.fillRect(bx,by,2,bh);
    // Deep bevel bottom/right
    ctx.fillStyle='rgba(0,0,0,0.40)';
    ctx.fillRect(bx,by+bh-2,bw,2); ctx.fillRect(bx+bw-2,by,2,bh);

    // Fissure / crack
    if((sh%9)===0){
      ctx.strokeStyle='rgba(0,0,0,0.52)'; ctx.lineWidth=0.8;
      const cx2=bx+5+(sh%Math.max(1,bw-14|0)), cy2=by+5+((sh>>4)%Math.max(1,bh-14|0));
      ctx.beginPath(); ctx.moveTo(cx2,cy2); ctx.lineTo(cx2+4+(sh%6),cy2+3+(sh%5)); ctx.stroke();
    }
    // Blood pool
    if((sh%19)===3){
      ctx.fillStyle='rgba(95,6,4,0.22)';
      ctx.beginPath(); ctx.ellipse(
        bx+5+(sh%Math.max(1,bw-14|0)), by+5+((sh>>3)%Math.max(1,bh-14|0)),
        5+(sh%5), 3+(sh%3), (sh%8)*0.4, 0, Math.PI*2); ctx.fill();
    }
    // Bone shard
    if((sh%31)===7){
      ctx.fillStyle='rgba(155,145,115,0.20)';
      ctx.fillRect(bx+4+(sh%Math.max(1,bw-12|0)), by+4+((sh>>5)%Math.max(1,bh-12|0)),
                   Math.min(7+(sh%5),bw-8), Math.min(2+(sh%2),bh-8));
    }
    // Dark moss patch
    if((sh%23)===11){
      ctx.fillStyle='rgba(20,38,14,0.28)';
      ctx.fillRect(bx+3+(sh%Math.max(1,bw-12|0)), by+3+((sh>>6)%Math.max(1,bh-12|0)),
                   Math.min(9+(sh%6),bw-6), Math.min(6+(sh%4),bh-6));
    }
  }
  }

  // Reachable tile highlight (blue) — opacity driven by _movePulse for slow pulsing
  if(isReachable){
    const pa = 0.70 + 0.30 * _movePulse;   // stroke: 0.70 → 1.00
    const fa = 0.26 + 0.26 * _movePulse;   // fill:   0.26 → 0.52
    const da = 0.65 + 0.35 * _movePulse;   // corner dots: 0.65 → 1.00
    ctx.strokeStyle=`rgba(60,140,255,${pa.toFixed(2)})`; ctx.lineWidth=2;
    ctx.strokeRect(X+2,Y+2,CELL-4,CELL-4);
    ctx.fillStyle=`rgba(30,107,255,${fa.toFixed(2)})`;
    ctx.fillRect(X+2,Y+2,CELL-4,CELL-4);
    ctx.fillStyle=`rgba(150,195,255,${da.toFixed(2)})`;
    const d=4;
    for(const [cx3,cy3] of [[X+d,Y+d],[X+CELL-d,Y+d],[X+d,Y+CELL-d],[X+CELL-d,Y+CELL-d]]){
      ctx.beginPath(); ctx.arc(cx3,cy3,1.8,0,Math.PI*2); ctx.fill();
    }
  }
  // Attackable tile highlight (red)
  if(isAttackable){
    ctx.strokeStyle='rgba(255,60,60,0.78)'; ctx.lineWidth=2;
    ctx.strokeRect(X+2,Y+2,CELL-4,CELL-4);
    ctx.fillStyle='rgba(255,30,30,0.13)';
    ctx.fillRect(X+2,Y+2,CELL-4,CELL-4);
    ctx.fillStyle='rgba(255,120,120,0.68)';
    const d=4;
    for(const [cx3,cy3] of [[X+d,Y+d],[X+CELL-d,Y+d],[X+d,Y+CELL-d],[X+CELL-d,Y+CELL-d]]){
      ctx.beginPath(); ctx.arc(cx3,cy3,1.8,0,Math.PI*2); ctx.fill();
    }
  }
  // Weapon range preview — área de alcance da arma (vermelho forte, hover no ícone)
  if(isWeaponPreview){
    ctx.fillStyle='rgba(220,0,0,0.52)';
    ctx.fillRect(X+1,Y+1,CELL-2,CELL-2);
    ctx.strokeStyle='rgba(255,0,0,0.98)'; ctx.lineWidth=2.5;
    ctx.strokeRect(X+2,Y+2,CELL-4,CELL-4);
    // borda interna luminosa
    ctx.strokeStyle='rgba(255,120,80,0.55)'; ctx.lineWidth=1;
    ctx.strokeRect(X+4,Y+4,CELL-8,CELL-8);
    // pontos de canto marcados
    ctx.fillStyle='rgba(255,80,40,1.0)';
    const d=4;
    for(const [cx3,cy3] of [[X+d,Y+d],[X+CELL-d,Y+d],[X+d,Y+CELL-d],[X+CELL-d,Y+CELL-d]]){
      ctx.beginPath(); ctx.arc(cx3,cy3,2.5,0,Math.PI*2); ctx.fill();
    }
  }
}

// ── ENTULHO 2D — monte de pedras desmoronadas (bloqueia movimento e visão) ───
function drawEntulho2D(ctx, x, y){
  const X=x*CELL, Y=y*CELL, h=((x*8161)^(y*5101))&0xFFFF;
  // base sombreada sob o monte
  ctx.fillStyle='rgba(0,0,0,0.35)';
  ctx.fillRect(X+2, Y+2, CELL-4, CELL-4);
  // pedras empilhadas
  const pedras=6;
  for(let i=0;i<pedras;i++){
    const sh=(h^(i*2917))&0xFFFF;
    const px=X+4+(sh%Math.max(1,CELL-12)), py=Y+5+((sh>>4)%Math.max(1,CELL-12));
    const rw=5+(sh%6), rh=4+((sh>>3)%5);
    const tone=70+((sh>>6)%40);
    ctx.fillStyle=`rgb(${tone},${tone-6},${tone-14})`;
    ctx.beginPath(); ctx.ellipse(px,py,rw,rh,(sh%6)*0.3,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=1; ctx.stroke();
    ctx.fillStyle='rgba(255,235,200,0.10)';  // brilho de tocha no topo
    ctx.fillRect(px-rw*0.5, py-rh*0.7, rw, 1.5);
  }
}

// ── DOOR TILE — closed = heavy wooden leaf; open = stone frame with dark gap ──
// Orientation is inferred from neighbouring walls: a door between vertical walls
// (left/right are walls) spans horizontally across the corridor and vice-versa.
function drawDoor2D(ctx, state, x, y, closed){
  const X=x*CELL, Y=y*CELL, T=state.tiles, H=T.length, W=T[0].length;
  const isWall=(tx,ty)=> ty<0||tx<0||ty>=H||tx>=W || T[ty][tx]===TILE_WALL;
  // Eixo da passagem: paredes à esquerda E direita ⇒ corredor sobe/desce, então
  // a folha atravessa na horizontal (vertical=true). Senão, folha vertical.
  const vertical = isWall(x-1,y) && isWall(x+1,y);
  ctx.save();
  if(closed){
    const m=8;                         // margem dentro da casa
    let dx, dy, dw, dh;
    if(vertical){ dx=X+2;   dy=Y+m;    dw=CELL-4;  dh=CELL-2*m; }   // folha horizontal
    else        { dx=X+m;   dy=Y+2;    dw=CELL-2*m; dh=CELL-4;  }   // folha vertical
    // moldura de pedra escura
    ctx.fillStyle='#15110c'; ctx.fillRect(X+1,Y+1,CELL-2,CELL-2);
    // madeira
    const grd=ctx.createLinearGradient(dx,dy,dx+dw,dy+dh);
    grd.addColorStop(0,'#5a3a1c'); grd.addColorStop(0.5,'#7a5028'); grd.addColorStop(1,'#4a2e16');
    ctx.fillStyle=grd; ctx.fillRect(dx,dy,dw,dh);
    // tábuas
    ctx.strokeStyle='rgba(20,12,6,0.8)'; ctx.lineWidth=2;
    const planks=3;
    for(let i=1;i<planks;i++){
      ctx.beginPath();
      if(vertical){ const px=dx+dw*i/planks; ctx.moveTo(px,dy); ctx.lineTo(px,dy+dh); }
      else        { const py=dy+dh*i/planks; ctx.moveTo(dx,py); ctx.lineTo(dx+dw,py); }
      ctx.stroke();
    }
    // bandas de ferro
    ctx.strokeStyle='#2a2a30'; ctx.lineWidth=3;
    if(vertical){
      for(const fy of [dy+dh*0.28, dy+dh*0.72]){ ctx.beginPath(); ctx.moveTo(dx,fy); ctx.lineTo(dx+dw,fy); ctx.stroke(); }
    } else {
      for(const fx of [dx+dw*0.28, dx+dw*0.72]){ ctx.beginPath(); ctx.moveTo(fx,dy); ctx.lineTo(fx,dy+dh); ctx.stroke(); }
    }
    // borda
    ctx.strokeStyle='#241608'; ctx.lineWidth=2; ctx.strokeRect(dx,dy,dw,dh);
    // argola/maçaneta
    ctx.strokeStyle='#d8c070'; ctx.lineWidth=2.5;
    ctx.beginPath(); ctx.arc(X+CELL/2, Y+CELL/2, 5, 0, Math.PI*2); ctx.stroke();
  } else {
    // Porta aberta: batentes de madeira nas laterais da passagem + vão escuro.
    ctx.fillStyle='rgba(8,6,4,0.45)';
    ctx.fillRect(X+CELL*0.18, Y+CELL*0.18, CELL*0.64, CELL*0.64);
    ctx.fillStyle='#5a3a1c';
    const jamb=6;
    if(vertical){   // batentes em cima e embaixo
      ctx.fillRect(X+2, Y+2, CELL-4, jamb);
      ctx.fillRect(X+2, Y+CELL-2-jamb, CELL-4, jamb);
    } else {        // batentes nas laterais
      ctx.fillRect(X+2, Y+2, jamb, CELL-4);
      ctx.fillRect(X+CELL-2-jamb, Y+2, jamb, CELL-4);
    }
  }
  ctx.restore();
}

// ── 3D WALL SOUTH FACE — visible stone masonry face (the wall's front face)
function drawWallSouthFace(ctx, x, y, matId){
  const X=x*CELL, Y=y*CELL;
  const faceH=WALL_RISE+6;  // height of visible stone face
  const faceY=Y+CELL-1;     // starts at bottom of wall top tile
  const h=((x*6131)^(y*4919))&0xFFFF;
  const pal = MAT_PALETTE_2D[matId] || MAT_PALETTE_2D.pedra_normal;
  const [BR, BG, BB] = pal.base;
  const cmix=(dr,dg,db,a)=>`rgba(${Math.max(0,Math.min(255,BR+dr))},${Math.max(0,Math.min(255,BG+dg))},${Math.max(0,Math.min(255,BB+db))},${a})`;

  // ── Base fill: stone wall FRONT FACE — medium gray castle stone, lit from above
  const wfG=ctx.createLinearGradient(0,faceY,0,faceY+faceH);
  wfG.addColorStop(0,    cmix(28, 26, 18, 0.99));  // top — lit face
  wfG.addColorStop(0.30, cmix(-6, -8, -14, 0.99)); // mid
  wfG.addColorStop(0.68, cmix(-50, -52, -54, 0.97)); // lower — shadow
  wfG.addColorStop(1,   'rgba(8,6,4,0)');
  ctx.fillStyle=wfG;
  ctx.fillRect(X+1,faceY,CELL-2,faceH);

  // ── Stone courses — horizontal mortar lines
  const courseH=Math.round(faceH*0.52);
  ctx.strokeStyle='rgba(0,0,0,0.55)'; ctx.lineWidth=1.8;
  if(courseH>4 && courseH<faceH-2){
    ctx.beginPath(); ctx.moveTo(X+1,faceY+courseH); ctx.lineTo(X+CELL-1,faceY+courseH); ctx.stroke();
  }
  // Light edge above mortar line (stone top edge)
  ctx.strokeStyle='rgba(180,172,158,0.55)'; ctx.lineWidth=0.8;
  if(courseH>4 && courseH<faceH-2){
    ctx.beginPath(); ctx.moveTo(X+2,faceY+courseH-1); ctx.lineTo(X+CELL-2,faceY+courseH-1); ctx.stroke();
  }

  // ── Vertical joints — alternating brick offset
  const q1=Math.round(CELL*0.27), q2=Math.round(CELL*0.73);
  ctx.strokeStyle='rgba(0,0,0,0.50)'; ctx.lineWidth=1.5;
  for(let row=0; row*courseH<faceH; row++){
    const jx=X+((row%2===0)?q1:q2);
    const jy=faceY+row*courseH;
    if(jx>X+4 && jx<X+CELL-4){
      ctx.beginPath();
      ctx.moveTo(jx, jy+2);
      ctx.lineTo(jx, Math.min(jy+courseH-2, faceY+faceH-4));
      ctx.stroke();
    }
  }

  // ── Top edge highlight — bright seam wall top → front face
  ctx.fillStyle='rgba(195,188,175,0.88)';
  ctx.fillRect(X+1,faceY,CELL-2,2);

  // ── Side-edge shadow (gives face an inset/depth look)
  const sL=ctx.createLinearGradient(X,0,X+9,0);
  sL.addColorStop(0,'rgba(0,0,0,0.55)'); sL.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=sL; ctx.fillRect(X+1,faceY,9,faceH);
  const sR=ctx.createLinearGradient(X+CELL-9,0,X+CELL,0);
  sR.addColorStop(0,'rgba(0,0,0,0)'); sR.addColorStop(1,'rgba(0,0,0,0.55)');
  ctx.fillStyle=sR; ctx.fillRect(X+CELL-9,faceY,8,faceH);

  // ── Subtle torch-glow tint on upper face (warm orange)
  const tG=ctx.createLinearGradient(0,faceY,0,faceY+faceH*0.4);
  tG.addColorStop(0,'rgba(255,140,30,0.08)');
  tG.addColorStop(1,'rgba(255,100,0,0)');
  ctx.fillStyle=tG; ctx.fillRect(X+1,faceY,CELL-2,faceH*0.4);
}

// ── DIABLO WALL TOP — dark menacing stone block viewed from above
function drawWallTop3D(ctx, x, y, matId){
  const X=x*CELL, Y=y*CELL;
  const h=((x*6271)^(y*2749)^(y<<4))&0xFFFF;
  const v=(h%18)-9;
  const pal = MAT_PALETTE_2D[matId] || MAT_PALETTE_2D.pedra_normal;
  const [BR, BG, BB] = pal.base;
  // Estilos próprios: caverna (pedra irregular) e enegrecida (tijolo preto).
  if(pal.accent==='cave'){ paintCave(ctx, X, Y, CELL, _rng((x*41^y*23^9)>>>0)); return; }
  if(pal.accent==='blackbrick'){ paintBrick(ctx, X, Y, CELL, _rng((x*7^y*13)>>>0), [22,21,26], '#070709'); return; }

  // Deep mortar — dark gray with faint blue tinge (grout between stones)
  ctx.fillStyle='#1a1c22';
  ctx.fillRect(X,Y,CELL,CELL);

  // Stone face — MEDIUM GRAY with cool blue tint (classic castle/dungeon stone wall)
  const r0=Math.min(255,BR+v), g0=Math.min(255,BG+v), b0=Math.min(255,BB+Math.floor(v*0.5));
  const wg=ctx.createLinearGradient(X,Y,X+CELL,Y+CELL);
  wg.addColorStop(0,  `rgb(${Math.min(255,r0+28)},${Math.min(255,g0+26)},${Math.min(255,b0+28)})`);
  wg.addColorStop(0.5,`rgb(${r0},${g0},${b0})`);
  wg.addColorStop(1,  `rgb(${Math.max(0,r0-30)},${Math.max(0,g0-28)},${Math.max(0,b0-26)})`);
  ctx.fillStyle=wg; ctx.fillRect(X+1,Y+1,CELL-2,CELL-2);

  // Mortar joints — brick offset pattern
  ctx.strokeStyle='rgba(0,0,0,0.62)'; ctx.lineWidth=1.8;
  const hOff=(y%2===0)?0:Math.floor(CELL/2);
  const vx=X+hOff;
  if(vx>X+3&&vx<X+CELL-3){ ctx.beginPath(); ctx.moveTo(vx,Y+2); ctx.lineTo(vx,Y+CELL-2); ctx.stroke(); }
  ctx.beginPath(); ctx.moveTo(X+2,Y+Math.floor(CELL/2)); ctx.lineTo(X+CELL-2,Y+Math.floor(CELL/2)); ctx.stroke();

  // Outer border — medium-dark seam between stones
  ctx.strokeStyle='rgba(0,0,0,0.70)'; ctx.lineWidth=2;
  ctx.strokeRect(X+1,Y+1,CELL-2,CELL-2);

  // Top-left subtle light edge (ambient vault lighting from above)
  ctx.fillStyle='rgba(255,255,255,0.10)';
  ctx.fillRect(X+1,Y+1,CELL-2,3);
  ctx.fillRect(X+1,Y+1,3,CELL-2);
  // Faint torch-warm tint
  ctx.fillStyle='rgba(255,170,50,0.05)';
  ctx.fillRect(X+1,Y+1,CELL-2,4);
  ctx.fillRect(X+1,Y+1,4,CELL-2);

  // Moisture/lichen dark patch
  if((h%7)===0){
    ctx.fillStyle='rgba(10,18,6,0.28)';
    const pw=Math.max(1,CELL-18)|0;
    ctx.fillRect(X+6+(h%pw), Y+6+((h>>3)%pw), 14+(h%10), 9+(h%7));
  }
  // Mineral vein (cold gray-white streak)
  if((h%11)===4){
    ctx.strokeStyle='rgba(190,195,210,0.16)'; ctx.lineWidth=1;
    ctx.beginPath();
    ctx.moveTo(X+5+(h%Math.max(1,CELL/2)|0), Y+4+(h%Math.max(1,CELL-14)|0));
    ctx.lineTo(X+CELL-5-(h%Math.max(1,CELL/3)|0), Y+CELL-4-(h%Math.max(1,CELL-20)|0));
    ctx.stroke();
  }
  // Crack
  if((h%9)===2){
    ctx.strokeStyle='rgba(0,0,0,0.36)'; ctx.lineWidth=0.8;
    ctx.beginPath();
    ctx.moveTo(X+4, Y+CELL/2+(h%10)-5);
    ctx.lineTo(X+CELL-4, Y+CELL/2-(h%7)+3);
    ctx.stroke();
  }
  // Rare iron ring/torch bracket hint
  if((h%17)===5){
    ctx.fillStyle='rgba(80,72,60,0.35)';
    ctx.beginPath(); ctx.arc(X+CELL/2,Y+CELL/2,5+(h%4),0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='rgba(110,100,80,0.25)'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.arc(X+CELL/2,Y+CELL/2,5+(h%4),0,Math.PI*2); ctx.stroke();
  }
  // Parede desmoronada: juntas extras quebradas sobre o bloco
  if(pal.accent==='wallRubble'){
    ctx.strokeStyle='rgba(0,0,0,0.45)'; ctx.lineWidth=1;
    for(let k=0;k<3;k++){
      const rx=X+4+((h>>(k*3))%Math.max(1,CELL-8)), ry=Y+4+((h>>(k*2))%Math.max(1,CELL-8));
      ctx.beginPath(); ctx.moveTo(rx,ry); ctx.lineTo(rx+5+(h%5), ry+3+(h%4)); ctx.stroke();
    }
  }
}

// ── MINIATURE BASE — black round base like real tabletop miniatures
function drawMiniBase(ctx, cx, cy, color, active){
  const by=cy+CELL*0.30;
  const rx=CELL*0.42, ry=CELL*0.145;

  // Cast shadow on floor
  ctx.fillStyle='rgba(0,0,0,0.72)';
  ctx.beginPath(); ctx.ellipse(cx+3,by+4,rx*1.08,ry*1.1,0,0,Math.PI*2); ctx.fill();

  // Coloured outer rim — class colour (gold when active/current turn)
  const rimCol = active ? '#f0c020' : color;
  ctx.fillStyle = rimCol;
  ctx.beginPath(); ctx.ellipse(cx,by,rx+3,ry+1.4,0,0,Math.PI*2); ctx.fill();

  // Main base body — black with painted-miniature look (dark brown texture)
  const bg=ctx.createLinearGradient(cx-rx,by-ry*1.2,cx+rx*0.4,by+ry*2);
  bg.addColorStop(0,'#2e2820');
  bg.addColorStop(0.30,'#181410');
  bg.addColorStop(0.65,'#0e0c0a');
  bg.addColorStop(1,'#06050403');
  ctx.fillStyle=bg;
  ctx.beginPath(); ctx.ellipse(cx,by,rx,ry,0,0,Math.PI*2); ctx.fill();

  // Highlight arc — painted edge gloss (top-left)
  const hl=ctx.createLinearGradient(cx-rx,by-ry,cx,by);
  hl.addColorStop(0,'rgba(120,105,85,0.65)');
  hl.addColorStop(0.55,'rgba(70,60,48,0.25)');
  hl.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=hl;
  ctx.beginPath(); ctx.ellipse(cx-rx*0.1,by-ry*0.12,rx*0.82,ry*0.5,0,0,Math.PI); ctx.fill();

  // Specular arc (top)
  ctx.strokeStyle=active?'rgba(255,240,120,0.75)':'rgba(90,80,65,0.60)';
  ctx.lineWidth=1.8;
  ctx.beginPath(); ctx.ellipse(cx,by-ry*0.18,rx*0.68,ry*0.38,0,Math.PI*1.10,Math.PI*1.90); ctx.stroke();
}

// ══ 3D DICE ANIMATION SYSTEM — Resin Collectible RPG Dice ════════════════════
// MeshStandardMaterial: roughness 0.85, opaque matte plastic — vivid solid colors.
// Each face has a 256×256 CanvasTexture: solid color bg, white Arial Black number, black chamfer.
// Same CanvasTexture used as map + bumpMap (bumpScale 0.8) for tactile number relief.
// SpotLight from above ensures vivid hues stay bright regardless of dungeon ambience.

// Matte plastic die colors — body color per die type (user spec)
// Die colors and text settings come from VC (src/visualConfig.js)
const DIE_COLORS = VC.dice.colors;

let _d3      = null;   // dice state (animFrame + cfr counter only — no separate scene)
const _dice3 = [];    // active die objects

// Floor Y = top surface of game board tiles (TH = 0.22)
const DICE_FLOOR_Y = 0.22;

/**
 * Bottom-right corner of the visible board near the active hero.
 * In the SW-225° isometric view, "bottom-right" = +X, +Z direction.
 * Falls back to board centre when game state is unavailable.
 */
function _getDiceArea(){
  if(!g3) return { x:5, z:5 };
  const cx = (g3.W-1)/2, cz = (g3.H-1)/2;
  return { x: Math.round(cx), z: Math.round(cz) };
}

// ══ DICE AUDIO — Web Audio API ═══════════════════════════════════════════════

let audioCtx = null;

// Unlock / create AudioContext — called on every user gesture so it stays
// running even if the browser suspended it after a tab-switch.
function _unlockAudio(){
  try{
    if(!audioCtx)
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if(audioCtx.state === 'suspended') audioCtx.resume();
  } catch(e){}
}

// Register on every common gesture type (not just first click)
['click','keydown','pointerdown','touchstart'].forEach(ev =>
  document.addEventListener(ev, _unlockAudio, { passive:true })
);

function getAudioContext(){
  _unlockAudio();
  return audioCtx;
}

// Two layers: high-freq transient crack + low thud — sounds like real dice.
function playImpact(intensity){
  if(intensity === undefined) intensity = 1.0;
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    const SR  = ctx.sampleRate;

    // Layer 1 — sharp transient crack (high-pass noise)
    const crackLen = Math.floor(SR * 0.055);
    const crackBuf = ctx.createBuffer(1, crackLen, SR);
    const cd = crackBuf.getChannelData(0);
    for(let i = 0; i < crackLen; i++){
      const t = i / crackLen;
      cd[i] = (Math.random()*2-1) * Math.exp(-t * 45) * intensity;
    }
    const crackSrc = ctx.createBufferSource();
    crackSrc.buffer = crackBuf;
    const hpf = ctx.createBiquadFilter();
    hpf.type = 'highpass'; hpf.frequency.value = 2200;
    const crackGain = ctx.createGain();
    crackGain.gain.value = 1.1;
    crackSrc.connect(hpf); hpf.connect(crackGain); crackGain.connect(_sfxBus());
    crackSrc.start(now);

    // Layer 2 — low body thud (pitched sine)
    const thudOsc  = ctx.createOscillator();
    const thudGain = ctx.createGain();
    thudOsc.type = 'sine';
    thudOsc.frequency.setValueAtTime(160 * intensity, now);
    thudOsc.frequency.exponentialRampToValueAtTime(55, now + 0.07);
    thudGain.gain.setValueAtTime(0.40 * intensity, now);
    thudGain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
    thudOsc.connect(thudGain); thudGain.connect(_sfxBus());
    thudOsc.start(now); thudOsc.stop(now + 0.09);
  } catch(e){}
}

// ── Roll sequence: rapid impacts that slow down (0 → 700 ms) ─────────────────
function playRollSound(){
  const ctx = getAudioContext();
  if(!ctx) return;
  // Staggered impacts — first few overlap for the initial scatter
  const times = [0, 80, 160, 255, 350, 440, 520, 590, 645, 690];
  times.forEach((ms, i) => {
    const intensity = 1.0 - (i / times.length) * 0.82;
    setTimeout(() => playImpact(intensity), ms);
  });
}

// ── Settle: satisfying "clunk" as die snaps to face ──────────────────────────
function playSettle(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(340, now);
    osc.frequency.exponentialRampToValueAtTime(110, now + 0.16);
    gain.gain.setValueAtTime(0.35, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.20);
    osc.connect(gain); gain.connect(_sfxBus());
    osc.start(now); osc.stop(now + 0.20);
  } catch(e){}
}

// ══ DAMAGE / HEAL AUDIO — anuncia quando uma criatura perde ou ganha HP ═══════
// Som sintetizado (sem assets), roteado pelo _sfxBus() para respeitar o volume.

// MEU herói tomou dano — sting descendente de dois tons, mais alarmante.
function playHeroHurt(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(520, now);
    osc.frequency.exponentialRampToValueAtTime(180, now + 0.18);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.85, now + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.30);
    const lpf = ctx.createBiquadFilter();
    lpf.type = 'lowpass'; lpf.frequency.value = 1400;
    osc.connect(lpf); lpf.connect(gain); gain.connect(_sfxBus());
    osc.start(now); osc.stop(now + 0.28);
  } catch(e){}
}

// Outra criatura tomou dano — "thud" grave e suave, mais discreto.
function playCreatureHit(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(190, now);
    osc.frequency.exponentialRampToValueAtTime(70, now + 0.10);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.50, now + 0.008);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
    osc.connect(gain); gain.connect(_sfxBus());
    osc.start(now); osc.stop(now + 0.17);
  } catch(e){}
}

// Qualquer criatura curou HP — chime ascendente e suave.
function playHeal(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    [523.25, 783.99].forEach((freq, i) => {  // C5 → G5
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      const t = now + i * 0.07;
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(0.45, t + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.34);
      osc.connect(gain); gain.connect(_sfxBus());
      osc.start(t); osc.stop(t + 0.36);
    });
  } catch(e){}
}

// Compara o HP de cada criatura entre game_states e dispara o som apropriado.
// Cobre heróis, monstros, servos (animados) de cada jogador e o prisioneiro.
let _hpSnapshot = new Map();   // entityId -> hp do último game_state

function _gatherHpEntries(st){
  const out = [];
  if(!st) return out;
  (st.players  || []).forEach(p => { if(p && p.id != null) out.push([`p:${p.id}`, p.hp, p.id === GS.myPid]); });
  (st.monsters || []).forEach(m => { if(m && m.id != null) out.push([`m:${m.id}`, m.hp, false]); });
  (st.players  || []).forEach(p => (p && p.animados || []).forEach(a => {
    if(a && a.id != null) out.push([`a:${a.id}`, (a.vida_atual != null ? a.vida_atual : a.hp), false]);
  }));
  const pr = st.prisoner;                       // singleton — sem id próprio
  if(pr && pr.hp != null) out.push(['pr:singleton', pr.hp, false]);
  return out;
}

function _detectHpChanges(st){
  const entries = _gatherHpEntries(st);
  let heroHurt = false, creatureHurt = false, healed = false;
  for(const [key, hp, isMine] of entries){
    if(hp == null) continue;
    const prev = _hpSnapshot.get(key);
    if(prev != null){
      if(hp < prev){ if(isMine) heroHurt = true; else creatureHurt = true; }
      else if(hp > prev){ healed = true; }
    }
  }
  // Reconstrói o snapshot só com as criaturas vistas neste estado.
  _hpSnapshot = new Map(entries.filter(e => e[1] != null).map(e => [e[0], e[1]]));
  if(heroHurt) playHeroHurt();
  if(creatureHurt) playCreatureHit();
  if(healed) playHeal();
}

// ── Keep 2D canvas sized (used only for label overlay) ──────────────────────
function syncDiceCanvas(){
  const wrap=$('map-wrap'), panel=$('map-panel'), dc=$('dice-canvas');
  if(!wrap||!panel||!dc) return;
  const wr=wrap.getBoundingClientRect(), pr=panel.getBoundingClientRect();
  dc.style.top=(wr.top-pr.top)+'px'; dc.style.left='0px';
  const cssW=Math.floor(wr.width), cssH=Math.floor(wr.height);
  dc._cssW=cssW; dc._cssH=cssH;
  applyDPR(dc, cssW, cssH);
}

const _particleSystems = [];

function _spawnGoldParticles(T, scene, pos){
  const N = 20;
  const posArr = new Float32Array(N * 3);
  const vels   = [];
  for(let i = 0; i < N; i++){
    posArr[i*3]   = pos.x + (Math.random()-.5)*0.3;
    posArr[i*3+1] = pos.y + 0.45;  // start just above die top face
    posArr[i*3+2] = pos.z + (Math.random()-.5)*0.3;
    vels.push({ x:(Math.random()-.5)*1.2, y:1.6+Math.random()*2.0, z:(Math.random()-.5)*1.2 });
  }
  const pGeo = new T.BufferGeometry();
  pGeo.setAttribute('position', new T.BufferAttribute(posArr, 3));
  const pMat = new T.PointsMaterial({
    color:0xffd700, size:0.10,
    transparent:true, opacity:1.0,
    sizeAttenuation:true, depthWrite:false,
  });
  const pts = new T.Points(pGeo, pMat);
  scene.add(pts);
  _particleSystems.push({ pts, pGeo, pMat, vels, N, elapsed:0, duration:800 });
}

function _updateParticles(dt){
  if(!g3) return;
  const s = dt/1000;
  for(let i=_particleSystems.length-1; i>=0; i--){
    const ps = _particleSystems[i];
    ps.elapsed += dt;
    const t = Math.min(ps.elapsed/ps.duration, 1.0);
    ps.pMat.opacity = Math.max(0, 1.0 - t*t);
    const pa = ps.pGeo.attributes.position.array;
    for(let j=0; j<ps.N; j++){
      pa[j*3]   += ps.vels[j].x * s;
      pa[j*3+1] += ps.vels[j].y * s;
      pa[j*3+2] += ps.vels[j].z * s;
      ps.vels[j].y -= 2.5*s;   // gentle gravity
    }
    ps.pGeo.attributes.position.needsUpdate = true;
    if(t>=1.0){
      g3.scene.remove(ps.pts);
      ps.pGeo.dispose(); ps.pMat.dispose();
      _particleSystems.splice(i,1);
    }
  }
}

// Assigns UV coordinates to every triangle so the texture centroid (0.5, 0.5)
// maps exactly to the visual centre of each face — number always readable.
// BoxGeometry already has correct per-face UVs, so d6 skips this step.
function _assignPerFaceUV(T, geo){
  // Work on a non-indexed copy so every 3 verts = 1 triangle
  const ng = geo.index ? geo.toNonIndexed() : geo;
  const vCount = ng.attributes.position.count;
  const faceCount = Math.floor(vCount / 3);
  const uvs = new Float32Array(vCount * 2);
  // Equilateral-triangle UV layout with centroid exactly at (0.5, 0.5)
  //   centroid = ((0.10+0.90+0.50)/3, (0.37+0.37+0.76)/3) = (0.50, 0.50) ✓
  const TU = [[0.10,0.37],[0.90,0.37],[0.50,0.76]];
  for(let i=0; i<faceCount; i++){
    const b=i*6;
    uvs[b+0]=TU[0][0]; uvs[b+1]=TU[0][1];
    uvs[b+2]=TU[1][0]; uvs[b+3]=TU[1][1];
    uvs[b+4]=TU[2][0]; uvs[b+5]=TU[2][1];
  }
  ng.setAttribute('uv', new T.BufferAttribute(uvs, 2));
  return ng;
}

function _buildDieGeo(T, type){
  switch(type){
    case 'd4':  return _assignPerFaceUV(T, new T.TetrahedronGeometry(0.60, 0));
    case 'd6':  return new T.BoxGeometry(0.78, 0.78, 0.78);  // Box UVs already correct
    case 'd8':  return _assignPerFaceUV(T, new T.OctahedronGeometry(0.62, 0));
    case 'd10': return _assignPerFaceUV(T, _buildD10Geo(T));
    case 'd12': return _assignPerFaceUV(T, new T.DodecahedronGeometry(0.62, 0));
    case 'd20': return _assignPerFaceUV(T, new T.IcosahedronGeometry(0.62, 0));
    default:    return _assignPerFaceUV(T, new T.IcosahedronGeometry(0.62, 0));
  }
}

// D10 — pentagonal trapezohedron via manual BufferGeometry (10 kite faces)
function _buildD10Geo(T){
  const h=0.72, r=0.62, y1=0.22, y2=-0.22;
  const TOP=[0,h,0], BOT=[0,-h,0], up=[], lo=[];
  for(let i=0;i<5;i++){
    const a1=i*2*Math.PI/5-Math.PI/2, a2=a1+Math.PI/5;
    up.push([r*Math.cos(a1),y1,r*Math.sin(a1)]);
    lo.push([r*Math.cos(a2),y2,r*Math.sin(a2)]);
  }
  const pos=[], nor=[];
  function tri(a,b,c){
    const ex=b[0]-a[0],ey=b[1]-a[1],ez=b[2]-a[2];
    const fx=c[0]-a[0],fy=c[1]-a[1],fz=c[2]-a[2];
    let nx=ey*fz-ez*fy,ny=ez*fx-ex*fz,nz=ex*fy-ey*fx;
    const l=Math.hypot(nx,ny,nz)||1; nx/=l;ny/=l;nz/=l;
    pos.push(...a,...b,...c);
    nor.push(nx,ny,nz, nx,ny,nz, nx,ny,nz);
  }
  for(let i=0;i<5;i++){
    const i1=(i+1)%5, ip=(i+4)%5;
    tri(TOP,up[i],lo[i]);   tri(TOP,lo[i],up[i1]);   // upper kite (2 tris)
    tri(BOT,lo[ip],up[i]);  tri(BOT,up[i],lo[i]);    // lower kite (2 tris)
  }
  const geo=new T.BufferGeometry();
  geo.setAttribute('position',new T.BufferAttribute(new Float32Array(pos),3));
  geo.setAttribute('normal',  new T.BufferAttribute(new Float32Array(nor),3));
  geo.computeBoundingSphere();
  return geo;
}

// ── Face texture — 256×256, matte-plastic body + contrasting number ──────────
// textColor is passed in so d4 (white body) gets black ink; all others white.
function _dieFaceTex(T, value, hexColor){
  const SZ=256, half=128;
  const cv=document.createElement('canvas'); cv.width=cv.height=SZ;
  const c=cv.getContext('2d');

  // ── Fundo na cor sólida do dado ────────────────────────────────────────────
  c.fillStyle = hexColor;
  c.fillRect(0, 0, SZ, SZ);

  // Vignette sutil: centro levemente claro → bordas mais escuras.
  // Material unlit (Basic) não recebe sombreamento da cena, então este gradiente
  // é o que separa visualmente as faces e dá volume de "dado de resina real".
  const vg = c.createRadialGradient(half, half, SZ*0.12, half, half, SZ*0.72);
  vg.addColorStop(0,   'rgba(255,255,255,0.16)');
  vg.addColorStop(0.55,'rgba(0,0,0,0)');
  vg.addColorStop(1,   'rgba(0,0,0,0.34)');
  c.fillStyle = vg;
  c.fillRect(0, 0, SZ, SZ);

  const bw = VC.dice.borderWidth;
  c.strokeStyle = VC.dice.strokeColor;
  c.lineWidth   = bw;
  c.strokeRect(bw/2, bw/2, SZ-bw, SZ-bw);

  // ── Number — white with black stroke for max contrast ─────────────────────
  const numStr = String(value);
  const baseFz = VC.dice.numberFontSize;
  const fs = numStr.length > 1 ? Math.round(baseFz * 110/130) : baseFz;
  c.textAlign    = 'center';
  c.textBaseline = 'middle';
  c.font    = `bold ${fs}px 'Arial Black', Arial, sans-serif`;
  c.lineJoin   = 'round';
  c.miterLimit = 2;

  // Stroke BEFORE fill so the outline sits under the fill
  c.strokeStyle = VC.dice.strokeColor;
  c.lineWidth   = VC.dice.numberStroke;
  c.strokeText(numStr, half, half);
  c.fillStyle = VC.dice.numberColor;
  c.fillText(numStr,   half, half);

  return new T.CanvasTexture(cv);
}

// ── D20 face texture — triangular face needs clip + smaller font + shifted Y ──
// IcosahedronGeometry maps each face as a triangle inscribed in UV space.
// Without clipping, a large font overflows the triangle edges.
// The visual centroid of the triangle is at y≈155, NOT y=128 (canvas midpoint).
function _dieFaceTexD20(T, value, hexColor){
  const SZ = 256, cx = 128;
  const cv = document.createElement('canvas'); cv.width = cv.height = SZ;
  const c  = cv.getContext('2d');

  // Solid background — same as all other faces
  c.fillStyle = hexColor;
  c.fillRect(0, 0, SZ, SZ);

  // Vignette sutil (mesma técnica de _dieFaceTex) — volume sem luz de cena
  const vg = c.createRadialGradient(cx, cx, SZ*0.12, cx, cx, SZ*0.72);
  vg.addColorStop(0,   'rgba(255,255,255,0.16)');
  vg.addColorStop(0.55,'rgba(0,0,0,0)');
  vg.addColorStop(1,   'rgba(0,0,0,0.34)');
  c.fillStyle = vg;
  c.fillRect(0, 0, SZ, SZ);

  // Clip everything to the triangle so no pixels bleed past the face edges
  c.save();
  const pts = VC.dice.d20.clipPts;
  c.beginPath();
  c.moveTo(pts[0][0], pts[0][1]);   // apex  (128, 20)
  c.lineTo(pts[1][0], pts[1][1]);   // right (236, 210)
  c.lineTo(pts[2][0], pts[2][1]);   // left  ( 20, 210)
  c.closePath();
  c.clip();

  const numStr = String(value);
  // 1-digit: 90px, 2-digit (10–20): 68px — both fit inside the triangle
  const fs = numStr.length === 1 ? VC.dice.d20.fontSz1 : VC.dice.d20.fontSz2;
  const numY = VC.dice.d20.numY;   // 155 — visual centroid of triangle

  c.textAlign    = 'center';
  c.textBaseline = 'middle';
  c.font    = `bold ${fs}px 'Arial Black', Arial, sans-serif`;
  c.lineJoin   = 'round';
  c.miterLimit = 2;

  // White stroke FIRST (per VISUAL_CONTRACT), black fill on top
  c.strokeStyle = VC.dice.strokeColor;   // '#FFFFFF'
  c.lineWidth   = VC.dice.numberStroke;  // 12px
  c.strokeText(numStr, cx, numY);
  c.fillStyle = VC.dice.numberColor;     // '#000000'
  c.fillText(numStr,   cx, numY);

  c.restore();
  return new T.CanvasTexture(cv);
}

// ── MeshBasicMaterial (unlit) — a cor do dado é EXATAMENTE a do hex ───────────
// Antes: Lambert + emissive 1.0 + luzes fortes → cor estourava p/ branco
// (dados "lavados"/pálidos). Basic ignora toda a iluminação da cena: faces
// 100% saturadas; o volume vem do vignette por-face da textura + bordas.
// dieType selects the correct face-texture builder (d20 uses triangular canvas).
function _buildDieMat(T, value, hexColor, dieType){
  const faceTex = dieType === 'd20'
    ? _dieFaceTexD20(T, value, hexColor)
    : _dieFaceTex(T, value, hexColor);
  return new T.MeshBasicMaterial({
    color:             0xffffff,                    // white so map texture hue shows unmodified
    map:               faceTex,
    transparent:       false,                       // fully opaque — never translucent
    opacity:           1.0,
    depthTest:         false,                       // always renders on top of all board geometry
    depthWrite:        true,                        // writes depth so dice occlude each other
  });
}

/** Random float in [a, b) */
function _rr(a, b){ return a + Math.random()*(b-a); }

/**
 * Compute unique flat face normals from a BufferGeometry (local space).
 * Handles both indexed and non-indexed geometries.
 */
function _getFlatNormals(geo){
  // Work on a non-indexed copy so every 3 positions = 1 triangle
  const g = geo.index ? geo.toNonIndexed() : geo;
  const pos = g.attributes.position;
  const cnt = pos.count;
  const normals = [];
  for(let i = 0; i < cnt; i += 3){
    const ax=pos.getX(i),   ay=pos.getY(i),   az=pos.getZ(i);
    const bx=pos.getX(i+1), by=pos.getY(i+1), bz=pos.getZ(i+1);
    const cx=pos.getX(i+2), cy=pos.getY(i+2), cz=pos.getZ(i+2);
    // Edge vectors
    const e1x=bx-ax, e1y=by-ay, e1z=bz-az;
    const e2x=cx-ax, e2y=cy-ay, e2z=cz-az;
    // Cross product → face normal
    const nx=e1y*e2z-e1z*e2y, ny=e1z*e2x-e1x*e2z, nz=e1x*e2y-e1y*e2x;
    const len=Math.hypot(nx,ny,nz);
    if(len<1e-6) continue;
    const nx2=nx/len, ny2=ny/len, nz2=nz/len;
    // Deduplicate: skip if very close to an existing normal
    let found=false;
    for(const n of normals){
      if(n.x*nx2+n.y*ny2+n.z*nz2 > 0.99){ found=true; break; }
    }
    if(!found) normals.push({x:nx2, y:ny2, z:nz2});
  }
  return normals;
}

/**
 * Return the quaternion that rotates the mesh so its face most aligned with
 * world-up points exactly upward.  Uses local-space face normals.
 */
function _snapRotation(T, mesh, faceLocalNormals){
  if(!faceLocalNormals || faceLocalNormals.length===0){
    return mesh.quaternion.clone();
  }
  const up  = new T.Vector3(0,1,0);
  const mQ  = mesh.quaternion;
  let bestDot=-2, bestLocal=null;
  for(const fn of faceLocalNormals){
    // Transform local face normal to world space with current mesh quaternion
    const fWorld = new T.Vector3(fn.x, fn.y, fn.z).applyQuaternion(mQ);
    const d = fWorld.dot(up);
    if(d > bestDot){ bestDot=d; bestLocal=fn; }
  }
  if(!bestLocal) return mQ.clone();
  // Quaternion that rotates local bestFace → world up
  const fromV = new T.Vector3(bestLocal.x, bestLocal.y, bestLocal.z);
  return new T.Quaternion().setFromUnitVectors(fromV, up);
}

const _tweens = [];

function _addTween(mesh, fromQ, toQ, duration, onDone){
  _tweens.push({ mesh, fromQ:fromQ.clone(), toQ:toQ.clone(), duration, elapsed:0, onDone });
}

function _updateTweens(dt){
  for(let i=_tweens.length-1; i>=0; i--){
    const tw = _tweens[i];
    tw.elapsed += dt;
    const t = Math.min(tw.elapsed/tw.duration, 1.0);
    const ease = t*t*(3-2*t);   // smooth-step
    tw.mesh.quaternion.slerpQuaternions(tw.fromQ, tw.toQ, ease);
    if(t>=1.0){
      tw.mesh.quaternion.copy(tw.toQ);
      if(tw.onDone) tw.onDone();
      _tweens.splice(i,1);
    }
  }
}

function _spawnDie3D(dieType, value, label, hexColor, flags){
  if(!g3) return;                         // game scene must be active
  flags = flags || {};
  const T = window.THREE;

  // One-time: create diceGroup that travels with the camera centre.
  // Material dos dados é unlit (MeshBasicMaterial) — não precisa de PointLights
  // dedicadas (eram 2 luzes a mais na cena, custo por frame sem efeito visual).
  if(_d3 && !_d3._diceGroup){
    const diceGroup = new T.Group();
    // Posição atualizada a cada frame em _startDiceLoop3D (segue o centro da câmera)
    g3.scene.add(diceGroup);
    _d3._diceGroup = diceGroup;
  }

  const geo  = _buildDieGeo(T, dieType);
  const mat  = _buildDieMat(T, value, hexColor, dieType);
  const mesh = new T.Mesh(geo, mat);
  mesh.castShadow=true; mesh.receiveShadow=true;
  mesh.scale.setScalar(VC.dice.scale);   // 30% larger for better board visibility

  // Dados em espaço LOCAL do diceGroup (grupo reposicionado cada frame).
  // floorY=0 → chão local coincide com o plano de flutuação do grupo no mundo.
  const floorY = 0;
  const dieRad = 0.42 * VC.dice.scale;

  // Dispersão relativa ao centro do grupo (±1.5 tiles)
  const spawnX = _rr(-1.5, 1.5);
  const spawnZ = _rr(-1.5, 1.5);
  // Cai de 2.5 unidades acima do chão local
  mesh.position.set(spawnX, floorY + 2.5, spawnZ);
  mesh.rotation.set(_rr(0,Math.PI*2), _rr(0,Math.PI*2), _rr(0,Math.PI*2));

  const faceNormals = _getFlatNormals(geo);

  mesh.renderOrder = 999;   // flush after all board geometry (reinforces depthTest:false)
  _d3._diceGroup.add(mesh);   // filho do grupo — move junto com ele
  _dice3.push({
    mesh, geo, mat,
    vel:    { x:_rr(-1,1), y:-8, z:_rr(-1,1) },
    angVel: { x:_rr(-15,15), y:_rr(-15,15), z:_rr(-15,15) },
    floorY, dieRad,
    area: { x:0, z:0 },   // relativo ao grupo — scatter contido em ±3 tiles locais
    bounces:0, phase:'rolling', alpha:1.0, settleT:0,
    value, label, dieType, faceNormals,
    discarded: !!flags.discarded, kept: !!flags.kept, offhand: !!flags.offhand,
  });

  if(!_d3.animFrame) _startDiceLoop3D();
  playRollSound();
}

function handleDiceRoll(msg){
  const dieType  = (msg.die||'d20').replace(/^\d+/,'');
  const delay    = (_dice3.length + _dice2.length) * (80 + Math.random()*70);   // staggered launch
  // Cores especiais p/ dado de desvantagem (Provocação) e off-hand (dual-wield),
  // para o jogador distinguir os 3 cenários visualmente:
  //   • Descartado (vermelho)  : 2º dado da desvantagem que NÃO valeu
  //   • Mantido (verde)        : dado da desvantagem que ficou (o pior)
  //   • Off-hand (laranja)     : dado da mão secundária (dual-wield Henrique)
  //   • Normal (padrão)        : dourado/azul conforme o tipo do dado
  let hexColor = DIE_COLORS[dieType] || VC.dice.colors.d20;
  if(msg.discarded) hexColor = 0xc0392b;        // vermelho — descartado
  else if(msg.kept) hexColor = 0x27ae60;        // verde — dado da desvantagem que valeu
  else if(msg.offhand) hexColor = 0xe67e22;     // laranja — mão secundária

  const flags = { discarded: !!msg.discarded, kept: !!msg.kept, offhand: !!msg.offhand };
  setTimeout(()=>{
    // Decide 3D vs 2D no MOMENTO do spawn (o jogador pode alternar a visão).
    // Antes: sem cena 3D ativa o dado simplesmente não aparecia (só o número
    // na narração do Mestre) — agora a visão 2D tem dados animados próprios.
    if(mode3D && g3){
      if(!_d3) _d3 = { animFrame:null, _cfr:0 };
      _spawnDie3D(dieType, msg.value, msg.label||dieType, hexColor, flags);
    } else {
      _spawnDie2D(dieType, msg.value, msg.label||dieType, hexColor, flags);
    }
  }, delay);
}

// ══ 2D DICE — dados animados sobre o dice-canvas na visão 2D ═════════════════
// Mesma identidade visual dos dados 3D: cor vibrante por tipo, número preto
// com contorno branco, vignette de volume, label dourado/colorido, som de
// rolagem. Física simples top-down: deslizam com atrito, quicam nas bordas,
// param mostrando o resultado real, somem após 3 s.
const _dice2 = [];
let _d2Frame = null;

function _hexCss(h){
  return typeof h === 'string' ? h : '#' + h.toString(16).padStart(6, '0');
}

function _dieMax(t){ return ({d4:4, d6:6, d8:8, d10:10, d12:12, d20:20})[t] || 20; }

function _spawnDie2D(dieType, value, label, hexColor, flags){
  syncDiceCanvas();   // garante tamanho/posição corretos do overlay
  const dc = $('dice-canvas');
  if(!dc) return;
  const W = dc._cssW || dc.clientWidth, H = dc._cssH || dc.clientHeight;
  if(!W || !H) return;
  const R = Math.max(26, Math.min(40, Math.min(W, H) * 0.055));
  _dice2.push({
    dieType, value, label, flags: flags || {},
    color: _hexCss(hexColor),
    x: W * 0.5 + _rr(-W * 0.16, W * 0.16),
    y: H * 0.34 + _rr(-36, 16),
    vx: _rr(-300, 300), vy: _rr(140, 340),
    rot: _rr(0, Math.PI * 2), vrot: _rr(-9, 9),
    R, t: 0, rollT: _rr(750, 1050),
    phase: 'rolling', alpha: 1, settleT: 0,
  });
  playRollSound();
  if(!_d2Frame) _startDiceLoop2D();
}

function _tickDie2(d, dt, W, H){
  if(d.phase === 'fading'){ d.alpha = Math.max(0, d.alpha - dt/500); return; }
  if(d.phase === 'settling'){
    d.settleT += dt;
    // endireita o dado suavemente para o resultado ficar legível
    d.vrot = 0;
    d.rot *= Math.pow(0.0035, dt/1000);
    if(d.settleT > 3000) d.phase = 'fading';
    return;
  }
  d.t += dt;
  const s = dt/1000;
  d.x += d.vx * s;  d.y += d.vy * s;  d.rot += d.vrot * s;
  const fr = Math.pow(0.16, s);            // atrito forte — para em ~1 s
  d.vx *= fr;  d.vy *= fr;  d.vrot *= Math.pow(0.28, s);
  const pad = d.R + 8;
  if(d.x < pad)     { d.x = pad;     d.vx =  Math.abs(d.vx) * 0.8; playImpact(0.5); }
  if(d.x > W - pad) { d.x = W - pad; d.vx = -Math.abs(d.vx) * 0.8; playImpact(0.5); }
  if(d.y < pad)     { d.y = pad;     d.vy =  Math.abs(d.vy) * 0.8; playImpact(0.5); }
  if(d.y > H - pad) { d.y = H - pad; d.vy = -Math.abs(d.vy) * 0.8; playImpact(0.5); }
  // normaliza rot para [-π, π] para o endireitamento girar pelo caminho curto
  if(d.t > d.rollT){
    d.rot = ((d.rot + Math.PI) % (Math.PI*2) + Math.PI*2) % (Math.PI*2) - Math.PI;
    d.phase = 'settling';
    playImpact(0.85);
  }
}

// Silhueta 2D por tipo de dado (triângulo, quadrado, losango, pentágono, hexágono)
function _dieShapePath2D(ctx, type, R){
  ctx.beginPath();
  const poly = (n) => {
    for(let i = 0; i < n; i++){
      const a = -Math.PI/2 + i * 2 * Math.PI / n;
      const px = R * Math.cos(a), py = R * Math.sin(a);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.closePath();
  };
  switch(type){
    case 'd4':  poly(3); break;
    case 'd6': {            // quadrado de cantos arredondados
      const r = R * 0.84, rd = r * 0.26;
      ctx.moveTo(-r + rd, -r);
      ctx.arcTo( r, -r,  r,  r, rd);
      ctx.arcTo( r,  r, -r,  r, rd);
      ctx.arcTo(-r,  r, -r, -r, rd);
      ctx.arcTo(-r, -r,  r, -r, rd);
      ctx.closePath(); break;
    }
    case 'd8':
    case 'd10': poly(4); break;   // losango
    case 'd12': poly(5); break;
    case 'd20':
    default:    poly(6); break;
  }
}

function _drawDie2D(ctx, d){
  const { R } = d;
  ctx.save();
  ctx.globalAlpha = d.alpha;
  ctx.translate(d.x, d.y);

  // sombra blob no "chão" (sem rotação)
  ctx.fillStyle = 'rgba(0,0,0,0.32)';
  ctx.beginPath();
  ctx.ellipse(3, R * 0.82, R * 0.95, R * 0.36, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.rotate(d.rot);

  // corpo na cor vibrante do dado + vignette de volume + borda branca
  _dieShapePath2D(ctx, d.dieType, R);
  ctx.fillStyle = d.color;
  ctx.fill();
  const vg = ctx.createRadialGradient(0, 0, R * 0.15, 0, 0, R);
  vg.addColorStop(0,    'rgba(255,255,255,0.22)');
  vg.addColorStop(0.60, 'rgba(0,0,0,0)');
  vg.addColorStop(1,    'rgba(0,0,0,0.38)');
  _dieShapePath2D(ctx, d.dieType, R);
  ctx.fillStyle = vg;
  ctx.fill();
  _dieShapePath2D(ctx, d.dieType, R);
  ctx.lineWidth = 3;
  ctx.strokeStyle = '#FFFFFF';
  ctx.stroke();

  // número: cicla aleatório enquanto rola; resultado real ao parar
  const numStr = d.phase === 'rolling'
    ? String(1 + Math.floor(Math.random() * _dieMax(d.dieType)))
    : String(d.value);
  const fs = Math.round(R * (numStr.length > 1 ? 0.66 : 0.85));
  ctx.font = `bold ${fs}px 'Arial Black', Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round';
  ctx.miterLimit = 2;
  const ny = d.dieType === 'd4' ? R * 0.18 : 0;   // centróide do triângulo é mais baixo
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 5;
  ctx.strokeText(numStr, 0, ny);
  ctx.fillStyle = '#000000';
  ctx.fillText(numStr, 0, ny);
  ctx.restore();

  // label acima do dado (sem rotação) — cores iguais às do modo 3D
  if(d.label && d.phase !== 'rolling'){
    ctx.save();
    ctx.globalAlpha = Math.min(1, d.alpha) * 0.9;
    let color = '#e8d180';
    if(d.flags.discarded)    color = '#e74c3c';
    else if(d.flags.kept)    color = '#2ecc71';
    else if(d.flags.offhand) color = '#f39c12';
    ctx.font = "bold 13px 'Cinzel', serif";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillStyle = 'rgba(0,0,0,0.85)';
    ctx.fillText(d.label, d.x + 1, d.y - d.R - 7 + 1);
    ctx.fillStyle = color;
    ctx.fillText(d.label, d.x, d.y - d.R - 7);
    ctx.restore();
  }
}

function _startDiceLoop2D(){
  const dc = $('dice-canvas');
  if(!dc) return;
  let last = performance.now();
  function frame(now){
    const dt = Math.min(now - last, 50); last = now;
    const ctx = dc.getContext('2d');
    const W = dc._cssW || dc.clientWidth, H = dc._cssH || dc.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, dc.width, dc.height);
    ctx.save();
    ctx.scale(dpr, dpr);
    for(let i = _dice2.length - 1; i >= 0; i--){
      const d = _dice2[i];
      _tickDie2(d, dt, W, H);
      if(d.alpha <= 0.01){ _dice2.splice(i, 1); continue; }
      _drawDie2D(ctx, d);
    }
    ctx.restore();
    if(_dice2.length){
      _d2Frame = requestAnimationFrame(frame);
    } else {
      _d2Frame = null;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, dc.width, dc.height);
    }
  }
  _d2Frame = requestAnimationFrame(frame);
}

// ── Per-frame die physics — Euler rotation, 60fps-normalised ─────────────────
function _tickDie3(obj, dt){
  const {mesh} = obj;

  // ── Fading out (0.5 s) ──
  if(obj.phase==='fading'){
    obj.alpha = Math.max(0, obj.alpha - dt/500);
    mesh.material.opacity = obj.alpha;
    mesh.material.transparent = true;
    return;
  }
  // ── Resting on board for 3 s, then fade ──
  if(obj.phase==='settling'){
    obj.settleT+=dt;
    if(obj.settleT>3000) obj.phase='fading';
    return;
  }
  // ── Waiting for snap tween to finish ──
  if(obj.phase==='snapping') return;

  // Normalise to 60 fps baseline so constants feel the same regardless of frame rate
  const s = dt/16.67;

  // ── Gravity: accumulate 0.4 velocity units per frame ──
  obj.vel.y -= 0.40*s;

  // ── Position integration (vel is units/s → divide by 60) ──
  mesh.position.x += obj.vel.x * s / 60;
  mesh.position.y += obj.vel.y * s / 60;
  mesh.position.z += obj.vel.z * s / 60;

  // ── Rotation: add angVel (rad/s) per frame (÷60 → rad/frame) ──
  mesh.rotation.x += obj.angVel.x * s / 60;
  mesh.rotation.y += obj.angVel.y * s / 60;
  mesh.rotation.z += obj.angVel.z * s / 60;

  // ── Rotational friction: 0.92 per frame ──
  const rdf = Math.pow(0.92, s);
  obj.angVel.x*=rdf; obj.angVel.y*=rdf; obj.angVel.z*=rdf;

  // ── Floor collision ──
  if(mesh.position.y - obj.dieRad < obj.floorY){
    mesh.position.y = obj.floorY + obj.dieRad;
    const preVelY   = obj.vel.y;               // save for impact intensity
    obj.vel.y  = Math.abs(obj.vel.y) * 0.45;  // bounceDamping
    obj.vel.x *= 0.88;                          // lateral friction
    obj.vel.z *= 0.88;
    obj.bounces++;
    playImpact(Math.min(1.0, Math.abs(preVelY) / 10));
  }

  // ── Area bounds — keep dice within 3 tiles of spawn centre ──
  const ax=obj.area.x, az=obj.area.z;
  if(Math.abs(mesh.position.x-ax)>3.0){
    mesh.position.x=ax+Math.sign(mesh.position.x-ax)*3.0; obj.vel.x*=-0.45;
  }
  if(Math.abs(mesh.position.z-az)>2.5){
    mesh.position.z=az+Math.sign(mesh.position.z-az)*2.5; obj.vel.z*=-0.45;
  }

  // ── Settle detection: met both velocity thresholds after ≥2 bounces ──
  const avMag=Math.hypot(obj.angVel.x, obj.angVel.y, obj.angVel.z);
  if(obj.bounces>=2 && Math.abs(obj.vel.y)<0.05 && avMag<0.30){
    obj.phase='snapping';
    const snapQ=_snapRotation(window.THREE, mesh, obj.faceNormals);
    _addTween(mesh, mesh.quaternion.clone(), snapQ, 420, ()=>{
      obj.phase='settling'; obj.settleT=0;
      playSettle();
      // Gold particle burst — usa posição mundial (mesh é filho do diceGroup)
      if(g3){ const _wp=new (window.THREE).Vector3(); mesh.getWorldPosition(_wp); _spawnGoldParticles(window.THREE,g3.scene,_wp); }
    });
  }
}

// ── Die-die sphere-sphere collision (prevents stacking / overlap) ─────────────
// Called once per frame after all individual _tickDie3 calls.
function _resolveDieCollisions(){
  const n = _dice3.length;
  if(n < 2) return;
  for(let i = 0; i < n; i++){
    const a = _dice3[i];
    // Only rolling dice participate — don't disturb snapping/settling/fading
    if(a.phase !== 'rolling') continue;
    for(let j = i+1; j < n; j++){
      const b = _dice3[j];
      if(b.phase !== 'rolling') continue;

      const dx = b.mesh.position.x - a.mesh.position.x;
      const dy = b.mesh.position.y - a.mesh.position.y;
      const dz = b.mesh.position.z - a.mesh.position.z;
      const distSq = dx*dx + dy*dy + dz*dz;
      const minDist = a.dieRad + b.dieRad;       // 0.84 units

      if(distSq >= minDist*minDist || distSq < 1e-6) continue;

      const dist   = Math.sqrt(distSq);
      const nx = dx/dist, ny = dy/dist, nz = dz/dist;

      // ── Positional correction: push both dice apart by half the overlap ──
      const overlap = (minDist - dist) * 0.5 + 0.005;  // tiny extra gap
      a.mesh.position.x -= nx*overlap;  a.mesh.position.y -= ny*overlap;  a.mesh.position.z -= nz*overlap;
      b.mesh.position.x += nx*overlap;  b.mesh.position.y += ny*overlap;  b.mesh.position.z += nz*overlap;

      // ── Velocity impulse — elastic collision, equal mass ──────────────────
      const dvx = b.vel.x - a.vel.x;
      const dvy = b.vel.y - a.vel.y;
      const dvz = b.vel.z - a.vel.z;
      const relVel = dvx*nx + dvy*ny + dvz*nz;
      if(relVel >= 0) continue;   // already separating — skip impulse

      const restitution = 0.50;
      const impulse = -(1 + restitution) * relVel * 0.5;  // ÷2 for equal masses
      a.vel.x -= impulse*nx;  a.vel.y -= impulse*ny;  a.vel.z -= impulse*nz;
      b.vel.x += impulse*nx;  b.vel.y += impulse*ny;  b.vel.z += impulse*nz;

      // Randomised spin kick on collision (feels physical)
      const spin = 4.0;
      a.angVel.x += (Math.random()-.5)*spin;  a.angVel.z += (Math.random()-.5)*spin;
      b.angVel.x += (Math.random()-.5)*spin;  b.angVel.z += (Math.random()-.5)*spin;

      // Softer impact click for die-on-die contact
      playImpact(Math.min(0.65, Math.abs(relVel) / 6));
    }
  }
}

// ── Labels dos dados (overlay 2D sobre o canvas dice-canvas) ────────────────
// Cada frame: projeta a posição mundial de cada dado para coordenadas de tela
// e desenha o label (ex.: "⚔️ Mão Principal", "🗡️ Mão Secundária", "Desvantagem
// — descartado") acima do dado, com cor sincronizada ao material do dado.
function _drawDiceLabels(){
  const dc = document.getElementById('dice-canvas');
  if(!dc || !g3 || !g3.camera || !g3.renderer) return;
  const ctx = dc.getContext('2d');
  // Limpa o overlay todo frame (não acumula).
  ctx.clearRect(0, 0, dc.width, dc.height);
  if(!_dice3.length) return;

  const T = window.THREE;
  const cssW = dc._cssW || dc.clientWidth;
  const cssH = dc._cssH || dc.clientHeight;
  const dpr  = window.devicePixelRatio || 1;
  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.font = "bold 13px 'Cinzel', serif";

  for(const obj of _dice3){
    if(!obj || !obj.mesh || obj.alpha <= 0.05) continue;
    if(obj.phase === 'fading' && obj.alpha < 0.4) continue;
    if(!obj.label) continue;
    // Posição do label acima da face superior do dado (mundo).
    const worldPos = new T.Vector3();
    obj.mesh.getWorldPosition(worldPos);
    worldPos.y += obj.dieRad + 0.25;
    // Projeção 3D → NDC → tela CSS.
    const ndc = worldPos.clone().project(g3.camera);
    if(ndc.z >= 1 || ndc.z <= -1) continue;   // fora do frustum
    const sx = (ndc.x * 0.5 + 0.5) * cssW;
    const sy = (-ndc.y * 0.5 + 0.5) * cssH;

    // Cor do label: igual à do material do dado (descartado=vermelho, kept=verde,
    // off-hand=laranja, normal=dourado).
    let color = '#e8d180';   // padrão dourado
    if(obj.discarded) color = '#e74c3c';
    else if(obj.kept) color = '#2ecc71';
    else if(obj.offhand) color = '#f39c12';

    // Sombra preta atrás para legibilidade
    ctx.globalAlpha = Math.min(1, obj.alpha) * 0.9;
    ctx.fillStyle = 'rgba(0,0,0,0.85)';
    ctx.fillText(obj.label, sx + 1, sy + 1);
    ctx.fillStyle = color;
    ctx.fillText(obj.label, sx, sy);
  }
  ctx.restore();
}

// Physics-only loop — dice live in g3.scene, rendered by the game's main renderer
function _startDiceLoop3D(){
  if(!_d3 || _d3.animFrame) return;
  let lastT = performance.now();
  function frame(now){
    if(!_d3) return;
    const dt = Math.min(now-lastT, 50); lastT=now;
    _d3._cfr++;

    // ── Reposiciona o grupo no centro da tela (segue câmera) ─────────────────
    if(_d3._diceGroup && g3 && g3.camera){
      const T3 = window.THREE;
      const cam = g3.camera;
      // NDC (0,0) = centro do canvas map-wrap = centro da área de jogo
      const near = new T3.Vector3(0, 0, -1).unproject(cam);
      const far  = new T3.Vector3(0, 0,  1).unproject(cam);
      const dir  = new T3.Vector3().subVectors(far, near).normalize();
      const FLOAT_Y = 2.5;   // altura de flutuação acima do tabuleiro
      if(Math.abs(dir.y) > 0.001){
        const t = (FLOAT_Y - near.y) / dir.y;
        _d3._diceGroup.position.set(near.x + dir.x*t, FLOAT_Y, near.z + dir.z*t);
      } else {
        _d3._diceGroup.position.set(near.x, FLOAT_Y, near.z);
      }
      // Escala do grupo = 1 (tamanho dos dados mantido igual ao anterior)
    }

    // Advance quaternion tweens (face-snap)
    _updateTweens(dt);
    // Advance gold particle bursts
    _updateParticles(dt);

    // Physics tick (individual)
    for(let i = 0; i < _dice3.length; i++) _tickDie3(_dice3[i], dt);

    // Die-die collision — prevents stacking / overlap
    _resolveDieCollisions();

    // Cleanup faded dice
    for(let i = _dice3.length-1; i >= 0; i--){
      if(_dice3[i].alpha <= 0.01){
        if(_d3._diceGroup) _d3._diceGroup.remove(_dice3[i].mesh);
        // Dispose COMPLETO: material.dispose() NÃO libera a CanvasTexture do map
        // — sem isto cada rolagem vazava uma textura 256² na GPU (lentidão
        // progressiva em sessões longas).
        if(_dice3[i].mat.map) _dice3[i].mat.map.dispose();
        _dice3[i].geo.dispose(); _dice3[i].mat.dispose();
        _dice3.splice(i, 1);
      }
    }

    // ── Desenha labels dos dados sobre o canvas 2D ────────────────────────────
    // Projeta a posição 3D do mesh para coordenadas de tela e desenha o label
    // acima do dado. Distingue: descartado (vermelho), kept (verde), off-hand
    // (laranja), normal (dourado). Resolve a confusão visual entre dual-wield
    // do Henrique e a desvantagem da Provocação.
    _drawDiceLabels();

    // Keep loop alive while dice or particles remain
    if(_dice3.length>0 || _particleSystems.length>0){
      _d3.animFrame = requestAnimationFrame(frame);
    } else {
      _d3.animFrame = null;
    }
  }
  _d3.animFrame = requestAnimationFrame(frame);
}

// ── Barras de Fome e Sede (sistema de sobrevivência) ───────────────────────
// Barras de Fome/Sede do HUD — refletem o recurso AUTORITATIVO do servidor
// (player.fome / player.sede, escala 0–100), que é o que as habilidades do warrior,
// o ataque básico, o caminhar e as ações bônus consomem. `p` = jogador do game_state.
function renderBarrasSobrevivencia(p){
  if(!p) return '';
  const fome = Math.max(0, Math.min(100, Math.round(p.fome ?? 100)));   // 0–100 (servidor)
  const sede = Math.max(0, Math.min(100, Math.round(p.sede ?? 100)));
  const pctFome = fome;   // já está na escala 0–100
  const pctSede = sede;

  function corBarra(v){                 // v na escala 0–100
    if(v > 70) return '#f0c040'; // dourado — saciado
    if(v > 40) return '#a0a0a0'; // cinza — neutro
    if(v > 20) return '#ff851b'; // laranja — leve
    if(v > 0)  return '#ff4500'; // laranja escuro — grave
    return '#ff1111';            // vermelho — esgotado
  }

  // Bloco de DOENÇA (sistema de doenças) — só aparece se o herói estiver doente.
  let doencaHTML = '';
  if(p.doente && p.doenca){
    const sevNome = {leve:'Leve', pesada:'Pesada', grave:'Grave'}[p.doenca.severidade] || 'Leve';
    const descs = {
      leve:  '-1 Reflexos · -1 Fortitude · -1 movimento',
      medio: '-2 DES · -2 FOR · +1 fome/sede por ação',
      grave: '-2 CON · -2 INT'
    };
    const linhas = (p.doenca.sintomas || []).map(t => `• ${descs[t] || t}`).join('<br>');
    doencaHTML = `
    <div style="width:100%; margin-bottom:6px; border:1px solid #6b3a6b; background:rgba(60,20,60,0.35); padding:4px 6px;">
      <div style="color:#cc88cc; font-family:'Cinzel',serif; font-size:9px; letter-spacing:1px; margin-bottom:2px;">🦠 DOENÇA ${sevNome.toUpperCase()}</div>
      <div style="color:#b59ab5; font-size:8.5px; line-height:1.35;">${linhas}</div>
      <div style="color:#7a5a7a; font-size:8px; margin-top:2px;">curável por clérigo ou templo</div>
    </div>`;
  }

  return doencaHTML + `
    <!-- FOME -->
    <div style="width:100%; margin-bottom:5px;">
      <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
        <span style="color:#8a7a5a; font-family:'Cinzel',serif; font-size:9px; letter-spacing:2px;">🍖 FOME</span>
        <span style="color:${corBarra(fome)}; font-family:'Cinzel',serif; font-size:9px;">${fome}/100</span>
      </div>
      <div style="width:100%; height:5px; background:#1a1a1a; border:1px solid #2a2a2a;">
        <div style="width:${pctFome}%; height:100%; background:${corBarra(fome)}; transition:width 0.5s ease, background 0.5s ease;"></div>
      </div>
    </div>

    <!-- SEDE -->
    <div style="width:100%; margin-bottom:5px;">
      <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
        <span style="color:#8a7a5a; font-family:'Cinzel',serif; font-size:9px; letter-spacing:2px;">💧 SEDE</span>
        <span style="color:${corBarra(sede)}; font-family:'Cinzel',serif; font-size:9px;">${sede}/100</span>
      </div>
      <div style="width:100%; height:5px; background:#1a1a1a; border:1px solid #2a2a2a;">
        <div style="width:${pctSede}%; height:100%; background:${corBarra(sede)}; transition:width 0.5s ease, background 0.5s ease;"></div>
      </div>
    </div>
  `;
}

// Vinheta de pressão na tela — reflete o pior estado (fome/sede) do herói local.
function atualizarEfeitosVisuais(heroi){
  const vinheta = document.getElementById('vinheta-sobrevivencia');
  if(!vinheta || !heroi) return;
  const piorEstado = Math.min(heroi.fome, heroi.sede);

  if(piorEstado <= 5){
    // Grave — vinheta vermelha pulsante
    vinheta.style.boxShadow = 'inset 0 0 80px rgba(255,17,17,0.4)';
    vinheta.style.animation = 'piscar 1.5s infinite';
  } else if(piorEstado <= 10){
    // Moderado — vinheta laranja fixa
    vinheta.style.boxShadow = 'inset 0 0 60px rgba(255,69,0,0.3)';
    vinheta.style.animation = 'none';
  } else if(piorEstado <= 19){
    // Leve — vinheta sutil
    vinheta.style.boxShadow = 'inset 0 0 40px rgba(255,133,27,0.15)';
    vinheta.style.animation = 'none';
  } else {
    // Normal — sem efeito
    vinheta.style.boxShadow = 'none';
    vinheta.style.animation = 'none';
  }
}

function renderPlayers(state){
  const el=$('player-cards'); el.innerHTML='';
  for(const p of state.players){
    const isMe=p.id===GS.myPid, isCur=p.id===state.current_turn;
    const disc=p.connected===false;
    const div=document.createElement('div');
    div.className='pcard'+(isMe?' me':'')+(isCur?' current':'')+(p.alive?'':' dead')+(disc?' disconnected':'');
    if(disc) div.style.opacity='0.45';
    const hpPct=Math.max(0,p.hp/p.max_hp*100);
    // MP foi removido do jogo — nenhuma classe usa mana (magias custam slots + fome/sede).
    const mpRowHTML = '';
    const _csong = p.buffs_cancao && Object.keys(p.buffs_cancao).length;
    div.innerHTML=`
      <div class="pcard-top">
        <span class="pcard-emoji">${p.emoji}</span>
        <span class="pcard-name" style="color:${p.color}">${p.name}</span>
        ${_csong ? '<span title="Inspirado pela Canção Heroica" style="color:#4db8ff;font-size:11px;">🎵</span>' : ''}
        <span class="pcard-lvl">Lv${p.level}</span>
      </div>
      <div class="bars">
        <div class="bar-row">
          <span class="bar-label">HP</span>
          <div class="bar-bg"><div class="bar-fill hp" style="width:${hpPct}%"></div></div>
          <span class="bar-val">${p.hp}/${p.max_hp}</span>
        </div>${mpRowHTML}
        <div class="survival-bars">${renderBarrasSobrevivencia(p)}</div>
      </div>`;
    // Clique no mini-card abre a ficha do herói correspondente.
    div.style.cursor = 'pointer';
    div.title        = 'Clique para ver a ficha';
    div.onclick      = () => {
      const key = _classIdParaHeroiKey(p.cls || p.class_id || p.key);
      abrirFichaEmJogo(key);
    };
    el.appendChild(div);
  }
  // Vinheta de pressão reflete o herói local (fome/sede autoritativos do servidor, 0–100).
  const _localP = state.players.find(x => x.id === GS.myPid);
  if (_localP) atualizarEfeitosVisuais({ fome: _localP.fome, sede: _localP.sede });
}

// ── Flags ativas do warrior (Victor) no turno atual ──────────────────────────
// Pré-visualiza as habilidades ARMADAS (toggle, client-side via GS) com o custo
// total que será cobrado ao atacar. Mostra também flags já APLICADAS no servidor
// (durante a janela de combate). Retorna '' quando não há nada armado/ativo.
function renderFlagsWarrior(me) {
  const armadas = (typeof GS !== 'undefined' && GS.getWarriorSelected) ? GS.getWarriorSelected() : []
  const EFEITO = {
    mira_certeira:    '<span style="color:#c8a951">⚔️ +2 acerto</span>',
    golpe_devastador: '<span style="color:#ff851b">💥 Dano ×2</span>',
    furia_berserker:  '<span style="color:#ff4444">🔥 Ataque extra</span>',
  }

  // Caso armadas (fase de seleção, antes do ataque)
  if (armadas.length) {
    const skills = (me.skills || []).filter(s => armadas.includes(s.id))
    const fome = skills.reduce((a, s) => a + (s.fome_cost || 0), 0)
    const sede = skills.reduce((a, s) => a + (s.sede_cost || 0), 0)
    const chips = skills.map(s => EFEITO[s.id] || `<span>${s.name}</span>`)
    return `
      <div style="margin-top:6px; padding:6px 8px; background:rgba(200,169,81,0.10);
        border:1px solid #c8a95155; font-family:'Cinzel',serif; font-size:9px; letter-spacing:1px;">
        <div style="display:flex; gap:8px; flex-wrap:wrap;">${chips.join(' | ')}</div>
        <div style="margin-top:3px; color:#8a7a5a;">Custo ao atacar: 🍖-${fome}${sede ? ` 💧-${sede}` : ''}</div>
      </div>`
  }

  // Caso flags já aplicadas no servidor (após atacar, dentro do turno)
  const bonusAcerto = me.skill_bonus_acerto || 0
  const dobrarDano  = me.skill_dobrar_dano || false
  const ataqueExtra = !!me.skill_ataque_extra
  if (!bonusAcerto && !dobrarDano && !ataqueExtra) return ''
  const ativos = []
  if (bonusAcerto > 0) ativos.push(`<span style="color:#c8a951">⚔️ +${bonusAcerto} acerto</span>`)
  if (dobrarDano)      ativos.push(EFEITO.golpe_devastador)
  if (ataqueExtra)     ativos.push(EFEITO.furia_berserker)
  return `
    <div style="margin-top:6px; padding:6px 8px; background:rgba(200,169,81,0.08);
      border:1px solid #c8a95133; font-family:'Cinzel',serif; font-size:9px; letter-spacing:1px;
      display:flex; gap:8px; flex-wrap:wrap;">
      ${ativos.join(' | ')}
    </div>`
}

// Armor type per class — reflects starting equipped armor
const CLASS_ARMOR = {
  warrior: {id:'leather',   name:'Armadura de Couro'},
  mage:    {id:'cloak',     name:'Manto'},
  rogue:   {id:'leather',   name:'Armadura de Couro'},
  cleric:  {id:'leather',   name:'Armadura de Couro'},
  bard:    {id:'cloak',     name:'Manto'},
  paladin: {id:'chainmail', name:'Cota de Malha'},
};

// Portrait paths for each class — keyed by class_id
const HERO_PORTRAIT_PATHS = {
  warrior: 'assets/portraits/victor.jpeg',
  paladin: 'assets/portraits/richard.jpeg',
  rogue:   'assets/portraits/luccas.jpeg',
  cleric:  'assets/portraits/lewis.jpeg',
  bard:    'assets/portraits/henrique.jpeg',
  mage:    'assets/portraits/pedro.jpeg',
};

// ── Botões de ação bônus para a adaga secundária (scaffolding) ───────────────
// NOTA: inserido verbatim conforme especificação. AINDA NÃO é chamado por
// renderMyPanel — o painel de ação bônus atual é construído inline lá e lê o
// estado AUTORITATIVO do servidor (`me.gear.off_hand`), não o modelo client-side
// da loja (`heroi.equipado.secundario`) que esta função usa. Os `tipo`
// ('ataqueAdagaSecundaria'/'arremessarAdagaSecundaria') também ainda não têm
// handlers. Mantido para a futura reconciliação modelo-loja ↔ estado-de-combate.
function renderBotoesAcaoBonus(heroi){
  const acoes = [];

  const secundario = heroi.equipado?.secundario

  if (secundario && secundario.id === 'adaga_secundaria') {
    // Ataque extra adjacente
    acoes.push({
      label: '🗡️ Ataque Extra — Adaga Secundária',
      descricao: `1d4 + DEX adjacente`,
      tipo: 'ataqueAdagaSecundaria'
    })

    // Arremesso
    acoes.push({
      label: '🎯 Arremessar Adaga Secundária',
      descricao: `1d4 + DEX — até 3 quadrados`,
      tipo: 'arremessarAdagaSecundaria'
    })
  }

  return acoes;
}

// Estado de UI: aba ativa do painel principal do Pedro e animado selecionado.
let _painelAbaPedro = 'atributos';
let _animadoSel = null;
let _prisSel = false;            // prisioneiro liberto selecionado (janela pós-turno do resgatador)
let _lastAnimadosTurn = null;
function trocarAbaPainel(aba){ _painelAbaPedro = aba; if(GS.gameState) renderMyPanel(GS.gameState); }
window.trocarAbaPainel = trocarAbaPainel;

// ═══════════════════════════════════════════════════════════════════════════
// HENRIQUE, O BARDO — Interface das 3 habilidades (Prompt 2)
//   • Conhecimento das Lendas (passiva): tooltip completo do inimigo no hover
//   • Canção Heroica (principal): toggle de buffs por atributo, raio 5
//   • Provocação (bônus): força o inimigo a atacar Henrique, raio 3
// Adaptado à arquitetura REAL do cliente: class_id (não `cls`), pos[] (não
// tx/ty), GS.adicionarLog/openTargetModal, e os campos reais do monstro que o
// servidor envia (name/emoji/hp/max_hp/ac/atk_bonus/damage/tier/xp/gold/...).
// ═══════════════════════════════════════════════════════════════════════════

const CANCAO_RAIO_CLIENT = 5;

const CANCAO_ATRIBUTOS_CLIENT = [
  { id:'acerto',      label:'Acerto',      icone:'⚔️', custo:'sede' },
  { id:'dano',        label:'Dano',        icone:'💥', custo:'fome' },
  { id:'ca',          label:'Armadura',    icone:'🛡️', custo:'sede' },
  { id:'movimento',   label:'Movimento',   icone:'👣', custo:'fome' },
  { id:'resistencia', label:'Resistência', icone:'✊', custo:'sede' },
];

// Custo de fome/sede de um conjunto de atributos da canção (1 por atributo).
function calcularCustoCancao(ativos){
  let fome = 0, sede = 0;
  (ativos||[]).forEach(id => {
    const attr = CANCAO_ATRIBUTOS_CLIENT.find(a => a.id === id);
    if(attr) (attr.custo === 'fome') ? fome++ : sede++;
  });
  return { fome, sede };
}

// Conhecimento das Lendas é coletivo: basta um Henrique vivo no grupo.
function _partyTemBardoVivo(){
  const st = GS.gameState;
  return !!(st && st.players && st.players.some(p => p.class_id === 'bard' && p.alive));
}

// Tooltip do inimigo. `full=false` → só o nome + HP/CA (visão comum).
// `full=true` (com Henrique no grupo) → ficha completa do monstro.
function fichaInimigoTooltipHTML(m, full){
  const nome = `<b>${m.emoji||'👾'} ${m.name}</b>`;
  if(!full) return `${nome}<br>HP ${m.hp}/${m.max_hp} | CA ${m.ac}`;
  const pct = Math.max(0, Math.min(100, (m.hp / Math.max(1,m.max_hp)) * 100));
  const cor = pct>60 ? '#2ecc40' : pct>30 ? '#ff851b' : '#ff4136';
  const TIER = {1:'Comum', 2:'Veterano', 3:'Elite', 4:'Chefe'};
  const DMG_ICON = {physical:'⚔️', fire:'🔥', cold:'❄️', lightning:'⚡', holy:'✨', poison:'☠️', magic:'🔮'};
  const SAVE_LBL = {fortitude:'Fort', reflexos:'Ref', vontade:'Von'};
  const ACT_LBL  = {acao:'ação', passiva:'passiva', acao_livre:'livre', magia:'magia'};
  const mod = v => { const n = Math.floor((v-10)/2); return (n>=0?'+':'')+n; };
  const fmt = v => (v>=0?'+':'')+v;

  const tags = [];
  if(m.undead) tags.push('💀 Morto-vivo');
  if(m.boss)   tags.push('👑 Chefe');

  const crVal = m.cr != null ? (m.cr < 1 ? `1/${Math.round(1/m.cr)}` : String(m.cr)) : null;

  // Atributos (FOR/DES/CON/INT) — apenas monstros no novo formato
  let atribHTML = '';
  if (m.str_ != null) {
    atribHTML = `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;margin-top:5px;">
      ${[{k:'str_',l:'FOR'},{k:'dex',l:'DES'},{k:'con_',l:'CON'},{k:'int_',l:'INT'}].map(({k,l})=>`
        <div style="background:rgba(255,255,255,0.04);padding:2px 0;text-align:center;">
          <div style="color:#8a7a5a;font-size:8px;">${l}</div>
          <div style="color:#c8b89a;font-size:10px;font-weight:bold;">${mod(m[k])}</div>
        </div>`).join('')}
    </div>`;
  }

  // Testes de resistência
  let savesHTML = '';
  if (m.fort != null) {
    savesHTML = `<div style="display:flex;gap:10px;margin-top:3px;font-size:9px;">
      <span style="color:#8a7a5a;">Fort <b style="color:#c8b89a;">${fmt(m.fort)}</b></span>
      <span style="color:#8a7a5a;">Ref <b style="color:#c8b89a;">${fmt(m.ref_)}</b></span>
      <span style="color:#8a7a5a;">Von <b style="color:#c8b89a;">${fmt(m.will)}</b></span>
    </div>`;
  }

  // Lista de ataques (novo formato)
  let attacksHTML = '';
  if (m.attacks && m.attacks.length) {
    const rows = m.attacks.map(atk => {
      const types = (atk.damage_types||[]).map(t=>DMG_ICON[t]||t).join('');
      const mult  = atk.num_attacks > 1 ? ` ×${atk.num_attacks}` : '';
      const oh    = atk.on_hit
        ? `<div style="color:#ff851b;font-size:9px;padding-left:6px;">↳ ${atk.on_hit.replace(/_/g,' ')}</div>`
        : '';
      return `<div style="font-size:10px;color:#c8b89a;">${atk.name}: <b>${atk.damage}</b>${types}${mult} <span style="color:#8a7a5a;">(+${atk.atk_bonus})</span></div>${oh}`;
    }).join('');
    attacksHTML = `<div style="margin-top:5px;padding-top:4px;border-top:1px solid #c8a95133;">
      <div style="color:#8a7a5a;font-size:8px;letter-spacing:1px;margin-bottom:2px;">ATAQUES</div>${rows}</div>`;
  }

  // Habilidades especiais
  let abilitiesHTML = '';
  if (m.special_abilities && m.special_abilities.length) {
    const rows = m.special_abilities.map(ab => {
      const max  = ab.uses_per_combat;
      const rem  = m.ability_uses ? (m.ability_uses[ab.id] ?? max) : max;
      const useStr = max ? ` ${rem}/${max}` : '';
      const dcStr  = ab.dc ? ` CD${ab.dc}/${SAVE_LBL[ab.save]||ab.save||''}` : '';
      const color  = (max && rem <= 0) ? '#666' : '#c8b89a';
      return `<div style="font-size:10px;color:${color};">${ab.name} <span style="color:#8a7a5a;">[${ACT_LBL[ab.action_type]||ab.action_type}${dcStr}${useStr}]</span></div>`;
    }).join('');
    abilitiesHTML = `<div style="margin-top:5px;padding-top:4px;border-top:1px solid #c8a95133;">
      <div style="color:#8a7a5a;font-size:8px;letter-spacing:1px;margin-bottom:2px;">HABILIDADES</div>${rows}</div>`;
  }

  // Imunidades e fraquezas
  let resistHTML = '';
  const imm  = m.immunities || [];
  const weak = m.weaknesses || [];
  if (imm.length || weak.length) {
    const immStr  = imm.map(i => DMG_ICON[i]||i).join(' ');
    const weakStr = weak.map(w => `${DMG_ICON[w.type]||w.type}${w.categoria?'/'+w.categoria:''} +${w.bonus_flat??'?'}`).join(' · ');
    resistHTML = `<div style="margin-top:4px;font-size:9px;">
      ${imm.length  ? `<div style="color:#4ec9b0;">Imune: ${immStr}</div>` : ''}
      ${weak.length ? `<div style="color:#ff6b6b;">Fraq: ${weakStr}</div>` : ''}
    </div>`;
  }

  // Legado: acerto/dano como linha simples (monstros antigos sem m.attacks)
  const legacyAtkHTML = !m.attacks
    ? `<div>🎯 Acerto <b>+${m.atk_bonus}</b> &nbsp;·&nbsp; 🎲 Dano <b>${m.damage||'?'}</b></div>` : '';

  return `
    <div style="min-width:220px;">
      <div style="display:flex;align-items:center;gap:6px;border-bottom:1px solid #c8a95155;padding-bottom:4px;margin-bottom:5px;">
        <span style="font-size:18px;">${m.emoji||'👾'}</span>
        <div>
          <div style="color:#c8a951;font-weight:bold;">${m.name}</div>
          <div style="color:#8a7a5a;font-size:.6rem;letter-spacing:2px;">📖 CONHECIMENTO DAS LENDAS</div>
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;">
        <span style="color:#8a7a5a;">❤️ Vida</span>
        <span style="color:${cor};font-weight:bold;">${m.hp}/${m.max_hp}</span>
      </div>
      <div style="height:5px;background:#1a1a1a;border:1px solid #2a2a2a;margin:2px 0 6px;">
        <div style="width:${pct}%;height:100%;background:${cor};"></div>
      </div>
      <div>🛡️ CA <b>${m.ac}</b>${crVal ? ` &nbsp;·&nbsp; ND <b>${crVal}</b>` : ''}</div>
      <div>🏅 <b>${TIER[m.tier]||m.tier||'?'}</b> &nbsp;·&nbsp; ✨ XP <b>${m.xp ?? '?'}</b>${!m.attacks && m.gold != null ? ` &nbsp;·&nbsp; 🪙 <b>${m.gold}</b>` : ''}</div>
      ${legacyAtkHTML}
      ${atribHTML}
      ${savesHTML}
      ${attacksHTML}
      ${abilitiesHTML}
      ${resistHTML}
      ${tags.length ? `<div style="margin-top:3px;color:#ff851b;">${tags.join(' · ')}</div>` : ''}
      ${(m.provocado && (m.provocado_turnos||0)>0) ? `<div style="margin-top:3px;color:#ff66cc;">😤 Provocado (${m.provocado_turnos}t)</div>` : ''}
    </div>`;
}

// ── Canção Heroica: painel flutuante de seleção de atributos ────────────────
let _selecionadosCancao = [];

function abrirPainelCancao(){
  const existente = document.getElementById('painel-cancao');
  if(existente){ existente.remove(); return; }   // toggle: reabrir fecha
  const me = GS.me;
  if(!me || me.class_id !== 'bard') return;
  if(me.cancao_ativa){ send({type:'desativar_cancao'}); return; }

  _selecionadosCancao = [];
  const painel = document.createElement('div');
  painel.id = 'painel-cancao';
  painel.style.cssText =
    "position:fixed;bottom:180px;left:50%;transform:translateX(-50%);" +
    "background:rgba(10,8,5,0.97);border:1px solid #c8a951;width:300px;" +
    "z-index:3000;padding:16px;font-family:'Cinzel',serif;box-shadow:0 0 24px rgba(0,0,0,0.7);";

  function render(){
    const custo  = calcularCustoCancao(_selecionadosCancao);
    const ataque = { fome: custo.fome + 2, sede: custo.sede + 1 };
    // Canção Heroica Suprema reduz a MANUTENÇÃO em -1🍖/-1💧 (mín 0); só o preview.
    const _red   = (GS.bardoCancaoSuprema && GS.bardoCancaoSuprema()) ? 1 : 0;
    const man    = { fome: Math.max(0, custo.fome - _red), sede: Math.max(0, custo.sede - _red) };
    const linhas = CANCAO_ATRIBUTOS_CLIENT.map(attr => {
      const ativo = _selecionadosCancao.includes(attr.id);
      const cl    = attr.custo === 'sede' ? '💧' : '🍖';
      return `
        <div onclick="toggleAtributoCancao('${attr.id}')" style="
          display:flex;align-items:center;gap:10px;padding:7px 9px;margin-bottom:4px;
          background:${ativo?'rgba(200,169,81,0.15)':'rgba(255,255,255,0.02)'};
          border:1px solid ${ativo?'#c8a951':'#2a2a2a'};cursor:pointer;">
          <div style="width:15px;height:15px;border:1px solid ${ativo?'#c8a951':'#4a4a4a'};
            background:${ativo?'#c8a951':'transparent'};display:flex;align-items:center;
            justify-content:center;font-size:10px;color:#1a1a1a;">${ativo?'✓':''}</div>
          <span style="font-size:15px;">${attr.icone}</span>
          <div style="flex:1;color:${ativo?'#c8a951':'#c8b89a'};font-size:11px;">+${(GS.bardoCancaoNivel?GS.bardoCancaoNivel(attr.id):1)} ${attr.label}</div>
          <span style="color:#8a7a5a;font-size:9px;">${cl}-1/turno</span>
        </div>`;
    }).join('');

    painel.innerHTML = `
      <div style="font-family:'Cinzel Decorative',serif;color:#c8a951;font-size:13px;margin-bottom:12px;text-align:center;">🎵 CANÇÃO HEROICA</div>
      <div style="margin-bottom:12px;">${linhas}</div>
      <div style="padding:8px 10px;margin-bottom:8px;background:rgba(255,133,27,0.06);border:1px solid #ff851b33;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span style="color:#8a7a5a;font-size:9px;letter-spacing:2px;">ATIVAR + MANUTENÇÃO${_red?' <span style="color:#c8a951;">(Suprema)</span>':''}</span>
          <span style="color:#ff851b;font-size:10px;">${_selecionadosCancao.length?((man.fome||man.sede)?`${man.fome?`🍖-${man.fome} `:''}${man.sede?`💧-${man.sede}`:''}/turno`:'🍖0 💧0/turno'):'Selecione atributos'}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
          <span style="color:#8a7a5a;font-size:9px;letter-spacing:2px;">SE ATACAR NO TURNO</span>
          <span style="color:#ff4136;font-size:10px;">${_selecionadosCancao.length?`🍖-${ataque.fome} 💧-${ataque.sede}`:'—'}</span>
        </div>
      </div>
      <div style="display:flex;gap:6px;">
        <button onclick="document.getElementById('painel-cancao').remove()" style="flex:1;padding:8px;background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">CANCELAR</button>
        <button onclick="confirmarCancao()" ${_selecionadosCancao.length?'':'disabled'} style="flex:2;padding:8px;background:${_selecionadosCancao.length?'rgba(200,169,81,0.15)':'transparent'};border:1px solid ${_selecionadosCancao.length?'#c8a951':'#4a4a4a'};color:${_selecionadosCancao.length?'#c8a951':'#4a4a4a'};font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:${_selecionadosCancao.length?'pointer':'not-allowed'};">🎵 CANTAR</button>
      </div>`;
  }

  render();
  document.body.appendChild(painel);

  window.toggleAtributoCancao = (id) => {
    _selecionadosCancao = _selecionadosCancao.includes(id)
      ? _selecionadosCancao.filter(s => s !== id)
      : [..._selecionadosCancao, id];
    render();
  };
  window.confirmarCancao = () => {
    if(!_selecionadosCancao.length) return;
    send({ type:'ativar_cancao', atributos:_selecionadosCancao });
    document.getElementById('painel-cancao')?.remove();
  };
}

// ── Provocação: seleção de alvo via modal padrão (raio 3, ação bônus) ───────
function iniciarProvocacao(){
  const me = GS.me;
  if(!me || me.class_id !== 'bard') return;
  if(!GS.isMyTurn || me.alive === false || (GS.gameState && GS.gameState.phase !== 'playing')){
    toast('Só é possível provocar no seu turno.', 'var(--orange)'); return;
  }
  if(me.bonus_action_used){ toast('Ação bônus já usada neste turno.', 'var(--orange)'); return; }
  if(me.fome < 3 || me.sede < 3){ toast('Provocação requer 🍖3 e 💧3.', 'var(--orange)'); return; }

  const st  = GS.gameState;
  const pp  = me.pos || [0,0];
  const alvos = (st.monsters||[]).filter(m => m && m.hp>0 &&
    Math.max(Math.abs(pp[0]-m.pos[0]), Math.abs(pp[1]-m.pos[1])) <= 3 &&
    !(m.provocado && (m.provocado_turnos||0) > 0));
  if(!alvos.length){ toast('Nenhum inimigo provocável a até 3 quadrados.', 'var(--orange)'); return; }
  if(alvos.length === 1){ send({ type:'provocacao', target_id:alvos[0].id }); return; }
  openTargetModal('😤 Provocação — Escolha o alvo (raio 3)', alvos, 'monster',
    id => send({ type:'provocacao', target_id:id }));
}

// Botão de habilidade do bardo no painel (substitui o toggle genérico).
function _bardSkillBtn(me, sk){
  const btn = document.createElement('button');
  btn.className = 'skill-btn';
  const myTurnPlay = GS.isMyTurn && me.alive && GS.gameState && GS.gameState.phase === 'playing';

  if(sk.id === 'cancao_heroica'){
    if(me.cancao_ativa){
      const c = me.cancao_custo || {fome:0, sede:0};
      const labels = (me.cancao_atributos||[]).map(id => {
        const a = CANCAO_ATRIBUTOS_CLIENT.find(x => x.id === id); return a ? a.label : id;
      }).join(' • ');
      btn.className += ' skill-active';
      btn.innerHTML = `
        <div class="skill-info">
          <div class="skill-name">🎵 ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● cantando</small></div>
          <div class="skill-desc">${labels || '—'}</div>
        </div>
        <div class="skill-cost">🍖${c.fome} 💧${c.sede}<br><small style="font-size:.6rem;">parar</small></div>`;
      btn.onclick = () => send({ type:'desativar_cancao' });   // parar a qualquer momento
    } else {
      btn.disabled = !myTurnPlay;
      btn.innerHTML = `
        <div class="skill-info">
          <div class="skill-name">🎵 ${sk.name}</div>
          <div class="skill-desc">${sk.description || 'Buffs para aliados em 5 quadrados.'}</div>
        </div>
        <div class="skill-cost">escolher</div>`;
      btn.onclick = () => abrirPainelCancao();
    }
  } else if(sk.id === 'provocacao'){
    const fc = sk.fome_cost ?? 3, sc = sk.sede_cost ?? 3;
    const temRec = me.fome >= fc && me.sede >= sc;
    const pode   = myTurnPlay && !me.bonus_action_used && temRec;
    btn.disabled = !pode;
    const aviso = me.bonus_action_used
      ? ' <small style="color:var(--text2);font-size:.62rem;">bônus usado</small>'
      : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
    const _pnv = GS.bardoProvocacaoNivel ? GS.bardoProvocacaoNivel() : 1;
    const _pextra = _pnv >= 3
      ? ' <span style="color:#c8a951;">II/III: desvantagem por toda a provocação, +2 CA e vantagem — e todos os aliados atacam o alvo com vantagem por 1 rodada.</span>'
      : _pnv === 2
      ? ' <span style="color:#c8a951;">II: a desvantagem dura toda a provocação; Henrique ganha +2 CA e ataca o alvo com vantagem.</span>'
      : '';
    btn.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">😤 ${sk.name}${aviso}</div>
        <div class="skill-desc">${sk.description || 'Força o inimigo a atacar Henrique (raio 3).'}${_pextra}</div>
      </div>
      <div class="skill-cost">🍖${fc} 💧${sc}</div>`;
    btn.onclick = () => iniciarProvocacao();
  }
  return btn;
}

// Ring 3D da Canção Heroica — criado/atualizado/removido conforme o estado.
function _sync3DCancaoRing(state){
  if(!g3 || !g3.scene || !window.THREE) return;
  const T = window.THREE;
  const bardo = (state.players||[]).find(p => p.class_id==='bard' && p.alive && p.cancao_ativa);
  if(!bardo){
    if(g3._cancaoRing){ g3.scene.remove(g3._cancaoRing); g3._cancaoRing = null; }
    return;
  }
  if(!g3._cancaoRing){
    const grupo = new T.Group();
    const raio  = CANCAO_RAIO_CLIENT + 0.5;   // cobre o tile do bardo + 5 ao redor
    const area  = new T.Mesh(
      new T.CircleGeometry(raio, 64).rotateX(-Math.PI/2),
      new T.MeshBasicMaterial({ color:0xc8a951, transparent:true, opacity:0.06, depthWrite:false }));
    const borda = new T.Mesh(
      new T.RingGeometry(raio-0.12, raio, 64).rotateX(-Math.PI/2),
      new T.MeshBasicMaterial({ color:0xc8a951, transparent:true, opacity:0.35, depthWrite:false }));
    grupo.add(area); grupo.add(borda);
    g3.scene.add(grupo);
    g3._cancaoRing = grupo;
  }
  const w = casaParaMundo(bardo.pos[0], bardo.pos[1]);
  g3._cancaoRing.position.set(w.x, 0.02, w.z);
}

// Exposição global p/ onclick inline e integração externa.
window.abrirPainelCancao = abrirPainelCancao;
window.iniciarProvocacao = iniciarProvocacao;

// ════════════════════════════════════════════════════════════════════════════
// PALADINO (Richard) — UI das 5 habilidades
// Mensagens WebSocket (ver server.py): imposicao_maos {target_id},
// golpe_sagrado / desativar_golpe_sagrado, protetor {target_id} /
// desativar_protetor, acao_livre_richard {habilidade_id, bonus?}.
// Alvos de aliado são escolhidos via openTargetModal (mesmo padrão da Provocação),
// não por crosshair 3D. Estado lido de me.* (guerreiro_luz_ativo/_bonus/_custo,
// golpe_sagrado_ativo, protetor_ativo/_alvo, regeneracao_ativa).
// ════════════════════════════════════════════════════════════════════════════

const GUERREIRO_LUZ_BONUS_CLIENT = [
  { id:'visao',  label:'Visão',  icone:'👁️', custo:'sede', max:2 },
  { id:'ataque', label:'Ataque', icone:'⚔️', custo:'sede', max:2 },
  { id:'dano',   label:'Dano',   icone:'💥', custo:'fome', max:2 },
  { id:'ca',     label:'CA',     icone:'🛡️', custo:'fome', max:2 },
];
let _bonusGuerreiro = { visao:0, ataque:0, dano:0, ca:0 };

// Painel com steppers +/- por bônus (0..2 cada). Sede paga Visão+Ataque,
// Fome paga Dano+CA — espelha _ativar_guerreiro_luz em server.py.
function abrirPainelGuerreiroLuz(){
  const existente = document.getElementById('painel-guerreiro-luz');
  if(existente){ existente.remove(); return; }   // toggle: reabrir fecha
  const me = GS.me;
  if(!me || me.class_id !== 'paladin') return;
  if(me.guerreiro_luz_ativo){ send({type:'acao_livre_richard', habilidade_id:'guerreiro_luz'}); return; }

  _bonusGuerreiro = { visao:0, ataque:0, dano:0, ca:0 };
  const painel = document.createElement('div');
  painel.id = 'painel-guerreiro-luz';
  painel.style.cssText =
    "position:fixed;bottom:180px;left:50%;transform:translateX(-50%);" +
    "background:rgba(10,8,5,0.97);border:1px solid #c8a951;width:300px;" +
    "z-index:3000;padding:16px;font-family:'Cinzel',serif;box-shadow:0 0 24px rgba(0,0,0,0.7);";

  function calcularCusto(){
    return { fome:_bonusGuerreiro.dano + _bonusGuerreiro.ca,
             sede:_bonusGuerreiro.visao + _bonusGuerreiro.ataque };
  }
  function render(){
    const custo = calcularCusto();
    const linhas = GUERREIRO_LUZ_BONUS_CLIENT.map(attr => {
      const valor = _bonusGuerreiro[attr.id];
      const cl = attr.custo === 'sede' ? '💧' : '🍖';
      return `
        <div style="display:flex;align-items:center;gap:10px;padding:8px 10px;margin-bottom:4px;
          background:${valor>0?'rgba(200,169,81,0.10)':'rgba(255,255,255,0.02)'};
          border:1px solid ${valor>0?'#c8a951':'#2a2a2a'};">
          <span style="font-size:16px;">${attr.icone}</span>
          <div style="flex:1;color:${valor>0?'#c8a951':'#c8b89a'};font-size:11px;">+${valor} ${attr.label}</div>
          <div style="display:flex;gap:4px;align-items:center;">
            <button onclick="ajustarBonusGuerreiro('${attr.id}',-1)" ${valor===0?'disabled':''}
              style="width:24px;height:24px;background:transparent;border:1px solid ${valor>0?'#c8a951':'#2a2a2a'};
              color:${valor>0?'#c8a951':'#4a4a4a'};cursor:${valor>0?'pointer':'not-allowed'};font-size:14px;line-height:1;">−</button>
            <span style="color:#c8a951;font-size:13px;font-weight:bold;min-width:16px;text-align:center;">${valor}</span>
            <button onclick="ajustarBonusGuerreiro('${attr.id}',1)" ${valor>=attr.max?'disabled':''}
              style="width:24px;height:24px;background:transparent;border:1px solid ${valor<attr.max?'#c8a951':'#2a2a2a'};
              color:${valor<attr.max?'#c8a951':'#4a4a4a'};cursor:${valor<attr.max?'pointer':'not-allowed'};font-size:14px;line-height:1;">+</button>
          </div>
          <span style="color:#8a7a5a;font-size:9px;min-width:38px;text-align:right;">${valor>0?`${cl}-${valor}/t`:''}</span>
        </div>`;
    }).join('');

    painel.innerHTML = `
      <div style="font-family:'Cinzel Decorative',serif;color:#c8a951;font-size:13px;margin-bottom:6px;text-align:center;">💡 GUERREIRO DA LUZ</div>
      <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:12px;text-align:center;">AÇÃO LIVRE — bônus fixos até desativar</div>
      <div style="margin-bottom:8px;">${linhas}</div>
      <div style="padding:8px 10px;margin-bottom:8px;background:rgba(255,133,27,0.06);border:1px solid #ff851b33;display:flex;justify-content:space-between;">
        <span style="color:#8a7a5a;font-size:9px;letter-spacing:2px;">CUSTO/TURNO</span>
        <span style="color:#ff851b;font-size:10px;">${(custo.fome||custo.sede)?`${custo.fome?`🍖-${custo.fome} `:''}${custo.sede?`💧-${custo.sede}`:''}`:'Selecione bônus'}</span>
      </div>
      <div style="display:flex;gap:6px;">
        <button onclick="document.getElementById('painel-guerreiro-luz').remove()" style="flex:1;padding:8px;background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">CANCELAR</button>
        <button onclick="confirmarGuerreiroLuz()" ${(custo.fome+custo.sede)===0?'disabled':''} style="flex:2;padding:8px;background:${(custo.fome+custo.sede)>0?'rgba(200,169,81,0.15)':'transparent'};border:1px solid ${(custo.fome+custo.sede)>0?'#c8a951':'#4a4a4a'};color:${(custo.fome+custo.sede)>0?'#c8a951':'#4a4a4a'};font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:${(custo.fome+custo.sede)>0?'pointer':'not-allowed'};">💡 ATIVAR</button>
      </div>`;
  }
  render();
  document.body.appendChild(painel);

  window.ajustarBonusGuerreiro = (id, delta) => {
    const attr = GUERREIRO_LUZ_BONUS_CLIENT.find(a => a.id === id);
    if(!attr) return;
    // Teto de atributos simultâneos (Fase 1c): ativar um NOVO atributo (0→>0)
    // além do limite possuído é bloqueado; o servidor também recusa (autoritativo).
    if(delta > 0 && _bonusGuerreiro[id] === 0){
      const cap = GS.paladinLuzMaxAtributos ? GS.paladinLuzMaxAtributos() : 2;
      const ativos = Object.values(_bonusGuerreiro).filter(v => v > 0).length;
      if(ativos >= cap){
        toast(`Guerreiro da Luz permite ${cap} atributo(s) ativo(s) — evolua na Guilda.`, 'var(--gold)');
        return;
      }
    }
    _bonusGuerreiro[id] = Math.max(0, Math.min(attr.max, _bonusGuerreiro[id] + delta));
    render();
  };
  window.confirmarGuerreiroLuz = () => {
    const custo = calcularCusto();
    if(custo.fome + custo.sede === 0) return;
    send({ type:'acao_livre_richard', habilidade_id:'guerreiro_luz', bonus:_bonusGuerreiro });
    document.getElementById('painel-guerreiro-luz')?.remove();
  };
}

// Aliados vivos (exceto Richard) dentro de `raio` (Chebyshev) da posição de me.
function _aliadosNoRaioPaladin(me, raio){
  const st = GS.gameState; if(!st) return [];
  const pp = me.pos || [0,0];
  return (st.players || []).filter(a => a && a.alive && a.id !== me.id && a.pos &&
    Math.max(Math.abs(pp[0]-a.pos[0]), Math.abs(pp[1]-a.pos[1])) <= raio);
}

// Protetor — ação bônus (raio 4). Escolhe aliado via modal (auto-envia se 1).
function iniciarModoProtetor(){
  const me = GS.me;
  if(!me || me.class_id !== 'paladin') return;
  if(!GS.isMyTurn || me.alive === false || (GS.gameState && GS.gameState.phase !== 'playing')){
    toast('Só é possível usar Protetor no seu turno.', 'var(--orange)'); return;
  }
  if(me.bonus_action_used){ toast('Ação bônus já usada neste turno.', 'var(--orange)'); return; }
  if(me.fome < 2 || me.sede < 2){ toast('Protetor requer 🍖2 e 💧2.', 'var(--orange)'); return; }
  const alvos = _aliadosNoRaioPaladin(me, 4);
  if(!alvos.length){ toast('Nenhum aliado a até 4 quadrados.', 'var(--orange)'); return; }
  if(alvos.length === 1){ send({ type:'protetor', target_id:alvos[0].id }); return; }
  openTargetModal('🛡️ Protetor — Escolha o aliado (raio 4)', alvos, 'player',
    id => send({ type:'protetor', target_id:id }));
}

// Imposição das Mãos — ação principal (aliado adjacente, raio 1).
function iniciarModoImposicaoMaos(){
  const me = GS.me;
  if(!me || me.class_id !== 'paladin') return;
  if(!GS.isMyTurn || me.alive === false || (GS.gameState && GS.gameState.phase !== 'playing')){
    toast('Só é possível usar Imposição das Mãos no seu turno.', 'var(--orange)'); return;
  }
  if(me.action_done){ toast('Ação principal já usada neste turno.', 'var(--orange)'); return; }
  if(me.fome < 3 || me.sede < 2){ toast('Imposição das Mãos requer 🍖3 e 💧2.', 'var(--orange)'); return; }
  const alvos = _aliadosNoRaioPaladin(me, 1);
  if(!alvos.length){ toast('Nenhum aliado adjacente.', 'var(--orange)'); return; }
  if(alvos.length === 1){ _enviarImposicaoMaos(alvos[0].id); return; }
  openTargetModal('🙏 Imposição das Mãos — Aliado adjacente', alvos, 'player',
    id => _enviarImposicaoMaos(id));
}

// Cura pelas Mãos III (opcional): +1d6 por +2🍖/+2💧, até 3×. Sem a especialização
// envia extra_d6:0 direto (fluxo idêntico ao anterior).
function _enviarImposicaoMaos(targetId){
  if(!GS.paladinCuraMaosExtra || !GS.paladinCuraMaosExtra()){
    send({ type:'imposicao_maos', target_id:targetId, extra_d6:0 }); return;
  }
  document.getElementById('painel-imposicao-extra')?.remove();
  let extra = 0;
  const painel = document.createElement('div');
  painel.id = 'painel-imposicao-extra';
  painel.style.cssText =
    "position:fixed;bottom:180px;left:50%;transform:translateX(-50%);" +
    "background:rgba(10,8,5,0.97);border:1px solid #c8a951;width:280px;" +
    "z-index:3000;padding:16px;font-family:'Cinzel',serif;box-shadow:0 0 24px rgba(0,0,0,0.7);";
  function render(){
    const custoFome = 3 + 2*extra, custoSede = 2 + 2*extra;
    painel.innerHTML = `
      <div style="font-family:'Cinzel Decorative',serif;color:#c8a951;font-size:13px;margin-bottom:8px;text-align:center;">🙏 IMPOSIÇÃO DAS MÃOS</div>
      <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:10px;text-align:center;">+1d6 EXTRA POR +2🍖 +2💧 (até 3×)</div>
      <div style="display:flex;align-items:center;gap:10px;padding:8px 10px;margin-bottom:10px;background:rgba(200,169,81,0.06);border:1px solid #c8a95133;">
        <button onclick="window._imposicaoExtraAjustar(-1)" ${extra===0?'disabled':''}
          style="width:26px;height:26px;background:transparent;border:1px solid ${extra>0?'#c8a951':'#2a2a2a'};color:${extra>0?'#c8a951':'#4a4a4a'};cursor:${extra>0?'pointer':'not-allowed'};font-size:15px;">−</button>
        <span style="flex:1;text-align:center;color:#c8a951;font-size:13px;">+${extra}d6 extra</span>
        <button onclick="window._imposicaoExtraAjustar(1)" ${extra>=3?'disabled':''}
          style="width:26px;height:26px;background:transparent;border:1px solid ${extra<3?'#c8a951':'#2a2a2a'};color:${extra<3?'#c8a951':'#4a4a4a'};cursor:${extra<3?'pointer':'not-allowed'};font-size:15px;">+</button>
      </div>
      <div style="padding:8px 10px;margin-bottom:10px;background:rgba(255,133,27,0.06);border:1px solid #ff851b33;display:flex;justify-content:space-between;">
        <span style="color:#8a7a5a;font-size:9px;letter-spacing:2px;">CUSTO TOTAL</span>
        <span style="color:#ff851b;font-size:10px;">🍖-${custoFome} 💧-${custoSede}</span>
      </div>
      <div style="display:flex;gap:6px;">
        <button onclick="document.getElementById('painel-imposicao-extra').remove()" style="flex:1;padding:8px;background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">CANCELAR</button>
        <button onclick="window._imposicaoExtraConfirmar()" style="flex:2;padding:8px;background:rgba(200,169,81,0.15);border:1px solid #c8a951;color:#c8a951;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">🙏 CURAR</button>
      </div>`;
  }
  render();
  document.body.appendChild(painel);
  window._imposicaoExtraAjustar = (delta) => { extra = Math.max(0, Math.min(3, extra + delta)); render(); };
  window._imposicaoExtraConfirmar = () => {
    send({ type:'imposicao_maos', target_id:targetId, extra_d6:extra });
    document.getElementById('painel-imposicao-extra')?.remove();
  };
}

// Indicador de visão expandida — mostrado no botão ativo do Guerreiro da Luz.
function renderIndicadorVisao(me){
  if(me.class_id !== 'paladin' || !me.guerreiro_luz_ativo) return '';
  const bonusVisao = me.guerreiro_luz_bonus?.visao || 0;
  if(bonusVisao === 0) return '';
  return `<div style="color:#c8a951;font-size:9px;letter-spacing:1px;margin-top:3px;">👁️ Visão +${bonusVisao} quadrados</div>`;
}

// Botão de habilidade do paladino (dedicado, fora do fluxo MP/toggle genérico).
function _paladinSkillBtn(me, sk){
  const btn = document.createElement('button');
  const myTurnPlay = GS.isMyTurn && me.alive && GS.gameState && GS.gameState.phase === 'playing';
  const fc = sk.fome_cost ?? 0, scst = sk.sede_cost ?? 0;
  const costStr = [fc?`🍖${fc}`:'', scst?`💧${scst}`:''].filter(Boolean).join(' ') || '—';
  const temRec  = me.fome >= fc && me.sede >= scst;

  const setBtn = (name, desc, cost, disabled, onclick, active) => {
    btn.className = 'skill-btn' + (active ? ' skill-active' : '');
    btn.disabled  = !!disabled;
    btn.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">${name}</div>
        <div class="skill-desc">${desc}</div>
      </div>
      <div class="skill-cost">${cost}</div>`;
    if(onclick) btn.onclick = onclick;
  };

  if(sk.id === 'guerreiro_luz'){
    if(me.guerreiro_luz_ativo){
      const b = me.guerreiro_luz_bonus || {};
      const c = me.guerreiro_luz_custo || {fome:0, sede:0};
      const lbls = Object.entries(b).filter(([,v]) => v>0).map(([k,v]) => `+${v} ${k}`).join(' • ');
      setBtn(`💡 ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● ativo</small>`,
             (lbls || '—') + renderIndicadorVisao(me), `🍖${c.fome} 💧${c.sede}<br><small style="font-size:.6rem;">parar</small>`,
             false, () => send({type:'acao_livre_richard', habilidade_id:'guerreiro_luz'}), true);
    } else {
      const _capLuz = GS.paladinLuzMaxAtributos ? GS.paladinLuzMaxAtributos() : 2;
      setBtn(`💡 ${sk.name} <small style="color:var(--text2);font-size:.62rem;">livre</small>`,
             `até ${_capLuz} atributo(s) simultâneo(s)`, 'escolher', !myTurnPlay,
             () => abrirPainelGuerreiroLuz(), false);
    }
  } else if(sk.id === 'regeneracao_divina'){
    const _raioRegen = GS.paladinRegenRaio ? GS.paladinRegenRaio() : 0;
    const _descRegen = _raioRegen > 0 ? `+1 HP por turno + aliados em raio ${_raioRegen}` : '+1 HP por turno';
    if(me.regeneracao_ativa){
      setBtn(`✨ ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● ativa</small>`,
             _descRegen, `🍖1 💧1<br><small style="font-size:.6rem;">parar</small>`,
             false, () => send({type:'acao_livre_richard', habilidade_id:'regeneracao_divina'}), true);
    } else {
      const hpFull = (me.hp != null && me.max_hp != null && me.hp >= me.max_hp);
      const aviso  = hpFull ? ' <small style="color:var(--text2);font-size:.62rem;">HP cheio</small>'
                   : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
      setBtn(`✨ ${sk.name}${aviso}`, _descRegen, costStr,
             !myTurnPlay || hpFull, () => send({type:'acao_livre_richard', habilidade_id:'regeneracao_divina'}), false);
    }
  } else if(sk.id === 'golpe_sagrado'){
    const _dadosSagrado = GS.paladinAtaqueSagradoDados ? GS.paladinAtaqueSagradoDados() : 1;
    if(me.golpe_sagrado_ativo){
      setBtn(`⚔️ ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● ativo</small>`,
             `+${_dadosSagrado}d8 sagrado por ataque`, `manut. 🍖1 💧1<br><small style="font-size:.6rem;">parar</small>`,
             false, () => send({type:'desativar_golpe_sagrado'}), true);
    } else {
      const pode  = myTurnPlay && !me.bonus_action_used && temRec;
      const aviso = me.bonus_action_used ? ' <small style="color:var(--text2);font-size:.62rem;">bônus usado</small>'
                  : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
      setBtn(`⚔️ ${sk.name}${aviso}`, sk.description || sk.desc || '', costStr, !pode,
             () => send({type:'golpe_sagrado'}), false);
    }
  } else if(sk.id === 'protetor'){
    const _raioDef  = GS.paladinDefensorRaio  ? GS.paladinDefensorRaio()  : 4;
    const _splitDef = GS.paladinDefensorSplit ? GS.paladinDefensorSplit() : 50;
    if(me.protetor_ativo){
      const alvo = (GS.gameState?.players || []).find(p => p.id === me.protetor_alvo);
      setBtn(`🛡️ ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● ativo</small>`,
             alvo ? `protegendo ${alvo.name} (${_splitDef}%/${_splitDef}%)` : '—',
             `manut. 🍖1<br><small style="font-size:.6rem;">parar</small>`,
             false, () => send({type:'desativar_protetor'}), true);
    } else {
      const pode  = myTurnPlay && !me.bonus_action_used && temRec;
      const aviso = me.bonus_action_used ? ' <small style="color:var(--text2);font-size:.62rem;">bônus usado</small>'
                  : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
      setBtn(`🛡️ ${sk.name}${aviso}`, `${sk.description || sk.desc || ''} (raio ${_raioDef}, ${_splitDef}%/${_splitDef}%)`, costStr, !pode,
             () => iniciarModoProtetor(), false);
    }
  } else if(sk.id === 'imposicao_maos'){
    const pode  = myTurnPlay && !me.action_done && temRec;
    const aviso = me.action_done ? ' <small style="color:var(--text2);font-size:.62rem;">ação usada</small>'
                : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
    const _dadosCura = GS.paladinCuraMaosDados ? GS.paladinCuraMaosDados() : 1;
    setBtn(`🙏 ${sk.name}${aviso}`, `${_dadosCura}d6 + FOR`, costStr, !pode,
           () => iniciarModoImposicaoMaos(), false);
  } else {
    setBtn(`${sk.icon || ''} ${sk.name}`, sk.description || sk.desc || '', costStr, !myTurnPlay, null, false);
  }
  return btn;
}

window.abrirPainelGuerreiroLuz  = abrirPainelGuerreiroLuz;
window.iniciarModoProtetor      = iniciarModoProtetor;
window.iniciarModoImposicaoMaos = iniciarModoImposicaoMaos;

// ═══════════════════════════════════════════════════════════════════════════
// LADINO (Luccas) — habilidades no cliente. Integra com os sistemas de venenos
// (CATALOGO_ITENS / weapon_poison) e armadilhas (game_state.armadilhas) já
// implementados no servidor. Convenções reais: me.class_id, me.pos[0/1],
// me.level, me.weapon_poison/_hits, arm.pos. Mensagens: detectar_armadilhas,
// esconder_sombras, veneno_rapido (livre), criar_armadilha, desarmar_armadilha.
// ═══════════════════════════════════════════════════════════════════════════

// Custos das armadilhas — alinhados ao servidor (ARMADILHA_CUSTO_FOME=2/SEDE=1
// + custo_ouro por tipo em ARMADILHAS).
const ARMADILHAS_LUCCAS = [
  { id:'buraco',                 nome:'Buraco',                icone:'🕳️', custo_ouro:0,  desc:'Reflexos dif 10 ou perde movimento. Permanente.' },
  { id:'armadilha_urso',         nome:'Armadilha de Urso',     icone:'🪤', custo_ouro:1,  desc:'1d4 dano + perde movimento. Some após ativar.' },
  { id:'fosso_estacas',          nome:'Fosso com Estacas',     icone:'⛏️', custo_ouro:2,  desc:'1d6 dano + perde movimento. Fica visível após ativar.' },
  { id:'rede',                   nome:'Rede',                  icone:'🕸️', custo_ouro:4,  desc:'Perde a rodada inteira. Some após ativar.' },
  { id:'armadilha_incendiaria',  nome:'Armadilha Incendiária', icone:'🔥', custo_ouro:10, desc:'1d6+1d4+1 fogo em 3 rodadas. Some após ativar.' },
  { id:'mina_terrestre',         nome:'Mina Terrestre',        icone:'💣', custo_ouro:20, desc:'2d6 em área (1 quad). Save reduz à metade. Some após ativar.' },
  { id:'fosso_envenenado',       nome:'Fosso Envenenado',      icone:'☠️', custo_ouro:2,  requer_veneno:true, desc:'1d6 dano + veneno escolhido. Fica visível após ativar.' },
  { id:'nuvem_gas',              nome:'Nuvem de Gás',          icone:'🌫️', custo_ouro:25, desc:'-1d6 CON por 3 rodadas em área. Save Fortitude dif 13.' },
];
const ARMADILHA_FOME = 2, ARMADILHA_SEDE = 1;

// Venenos na bolsa — o servidor manda itens com `id`/`veneno_id`, sem `tipo`;
// cruzamos com CATALOGO_ITENS p/ nome/descrição/ícone. Retorna lista normalizada.
function _venenosNaBolsa(me){
  const cat = (window.GS && GS.CATALOGO_ITENS) ? GS.CATALOGO_ITENS : {};
  const out = [];
  for(const it of (me && me.bag || [])){
    if(!it) continue;
    const c = cat[it.id] || (it.veneno_id ? cat[it.veneno_id] : null);
    const ehVeneno = it.tipo === 'veneno' || (c && c.tipo === 'veneno') || !!it.veneno_id;
    if(!ehVeneno) continue;
    out.push({
      id:        it.veneno_id || it.id,   // server casa por veneno_id OU id
      nome:      it.nome || it.name || (c && c.nome) || it.id,
      descricao: it.descricao || (c && c.descricao) || '',
      icone:     it.icone || it.emoji || (c && c.icone) || '☠️',
    });
  }
  return out;
}

function _rogueMyTurn(me){
  return !!(GS.isMyTurn && me && me.alive !== false && GS.gameState && GS.gameState.phase === 'playing');
}

function _temArmadilhaAdjacente(me){
  const armadilhas = (GS.gameState && GS.gameState.armadilhas) || [];
  const px = (me.pos||[0,0])[0], py = (me.pos||[0,0])[1];
  return armadilhas.some(arm => {
    const [ax,ay] = arm.pos || [99,99];
    return Math.max(Math.abs(ax-px), Math.abs(ay-py)) <= 1;
  });
}

// ── Painel: Criar Armadilha (ação principal) ────────────────────────────────
function abrirPainelCriarArmadilha(){
  const existente = document.getElementById('painel-armadilha');
  if(existente){ existente.remove(); return; }

  const me = GS.me;
  if(!me || me.class_id !== 'rogue') return;
  if(!_rogueMyTurn(me)){ toast('Só no seu turno.', 'var(--orange)'); return; }
  if(me.action_done){ GS.adicionarLog('❌ Ação principal já usada'); return; }

  const ouro    = me.gold || 0;
  const venenos = _venenosNaBolsa(me);
  let selecionada = null;
  let veneno_id   = null;

  const painel = document.createElement('div');
  painel.id = 'painel-armadilha';
  painel.style.cssText = `position:fixed; bottom:180px; left:50%; transform:translateX(-50%);
    background:rgba(10,8,5,0.97); border:1px solid #c8a951; width:320px; max-height:70vh;
    overflow-y:auto; z-index:200; padding:16px; font-family:'Cinzel',serif;`;

  function renderPainel(){
    painel.innerHTML = `
      <div style="font-family:'Cinzel Decorative',serif; color:#c8a951; font-size:13px; margin-bottom:12px; text-align:center;">🪤 CRIAR ARMADILHA</div>
      <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px; margin-bottom:10px; text-align:center;">💰 ${ouro} moedas | 🍖-${ARMADILHA_FOME} 💧-${ARMADILHA_SEDE} por criação</div>
      ${ARMADILHAS_LUCCAS.map(arm => {
        const desbloqueada = (GS.ladinoArmadilhasDesbloqueadas ? GS.ladinoArmadilhasDesbloqueadas() : ['buraco']).includes(arm.id);
        const podeComprar = ouro >= arm.custo_ouro;
        const temVeneno   = arm.requer_veneno ? venenos.length > 0 : true;
        const pode        = desbloqueada && podeComprar && temVeneno;
        const sel         = selecionada === arm.id;
        return `
          <div ${pode ? `onclick="selecionarArmadilha('${arm.id}')"` : ''} style="
            padding:10px 12px; margin-bottom:4px;
            background:${sel ? 'rgba(200,169,81,0.15)' : 'rgba(255,255,255,0.02)'};
            border:1px solid ${sel ? '#c8a951' : pode ? '#2a2a2a' : '#1a1a1a'};
            cursor:${pode ? 'pointer' : 'not-allowed'}; opacity:${pode ? 1 : 0.4};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
              <span style="color:${sel ? '#c8a951' : '#c8b89a'}; font-size:12px;">${arm.icone} ${arm.nome}</span>
              <span style="color:#c8a951; font-size:11px;">${arm.custo_ouro}🪙</span>
            </div>
            <div style="color:#8a7a5a; font-size:9px; line-height:1.5;">${arm.desc}</div>
            ${!desbloqueada ? `<div style="color:#ff851b; font-size:9px; margin-top:3px;">🔒 Compre a fórmula na Guilda dos Heróis</div>` : ''}
            ${desbloqueada && arm.requer_veneno ? `<div style="color:${venenos.length>0?'#9900cc':'#ff4136'}; font-size:9px; margin-top:3px;">${venenos.length>0?'☠️ Requer veneno — disponível':'⚠️ Sem veneno no inventário'}</div>` : ''}
          </div>`;
      }).join('')}
      ${selecionada && ARMADILHAS_LUCCAS.find(a=>a.id===selecionada)?.requer_veneno ? `
        <div style="margin-top:10px;">
          <div style="color:#9900cc; font-size:9px; letter-spacing:2px; margin-bottom:6px;">ESCOLHA O VENENO:</div>
          ${venenos.map(v => `
            <div onclick="selecionarVenenoPara('${v.id}')" style="
              padding:6px 10px; margin-bottom:3px;
              background:${veneno_id===v.id?'rgba(150,0,200,0.15)':'rgba(255,255,255,0.02)'};
              border:1px solid ${veneno_id===v.id?'#9900cc':'#2a2a2a'}; cursor:pointer;">
              <span style="color:#c8b89a; font-size:10px;">${v.icone} ${v.nome}</span>
            </div>`).join('')}
        </div>` : ''}
      <div style="display:flex; gap:6px; margin-top:12px;">
        <button onclick="document.getElementById('painel-armadilha').remove()" style="flex:1; padding:8px; background:transparent; border:1px solid #4a4a4a; color:#8a7a5a; font-family:'Cinzel',serif; font-size:10px; letter-spacing:2px; cursor:pointer;">CANCELAR</button>
        <button onclick="confirmarCriarArmadilha()" ${!selecionada ? 'disabled' : ''} style="flex:2; padding:8px;
          background:${selecionada?'rgba(200,169,81,0.15)':'transparent'};
          border:1px solid ${selecionada?'#c8a951':'#4a4a4a'};
          color:${selecionada?'#c8a951':'#4a4a4a'}; font-family:'Cinzel',serif; font-size:10px; letter-spacing:2px; cursor:pointer;">🪤 POSICIONAR</button>
      </div>`;
  }

  renderPainel();
  document.body.appendChild(painel);

  window.selecionarArmadilha = function(id){ selecionada = (selecionada === id ? null : id); veneno_id = null; renderPainel(); };
  window.selecionarVenenoPara = function(vid){ veneno_id = vid; renderPainel(); };
  window.confirmarCriarArmadilha = function(){
    if(!selecionada) return;
    const arm = ARMADILHAS_LUCCAS.find(a => a.id === selecionada);
    if(arm?.requer_veneno && !veneno_id){ GS.adicionarLog('⚠️ Escolha um veneno para o fosso'); return; }
    document.getElementById('painel-armadilha')?.remove();
    _ativarModoPlacementArmadilha(selecionada, veneno_id);
  };
}

function _ativarModoPlacementArmadilha(tipoId, venenoId){
  window._modoPlacementArmadilha = { tipoId, venenoId };
  try { if(g3 && g3.renderer) g3.renderer.domElement.style.cursor = 'crosshair'; } catch(e){}

  const legenda = document.createElement('div');
  legenda.id = 'legenda-armadilha';
  legenda.style.cssText = `position:fixed; bottom:120px; left:50%; transform:translateX(-50%);
    background:rgba(10,8,5,0.92); border:1px solid #c8a951; color:#c8a951; font-family:'Cinzel',serif;
    font-size:11px; letter-spacing:2px; padding:8px 20px; pointer-events:none; z-index:100;`;
  legenda.innerHTML = '🪤 Clique numa casa sua ou adjacente | ESC cancela';
  document.body.appendChild(legenda);

  document.addEventListener('keydown', function cancelarPlacement(e){
    if(e.key === 'Escape'){ _cancelarPlacementArmadilha(); document.removeEventListener('keydown', cancelarPlacement); }
  });
}

function _cancelarPlacementArmadilha(){
  window._modoPlacementArmadilha = null;
  try { if(g3 && g3.renderer) g3.renderer.domElement.style.cursor = 'default'; } catch(e){}
  document.getElementById('legenda-armadilha')?.remove();
}

function onClickTileParaArmadilha(tx, ty){
  if(!window._modoPlacementArmadilha) return;
  const { tipoId, venenoId } = window._modoPlacementArmadilha;
  send({ type:'criar_armadilha', tipo:tipoId, tx:tx, ty:ty, veneno_id:venenoId || null });
  _cancelarPlacementArmadilha();
}

// ── Painel: Veneno Rápido (ação livre) ──────────────────────────────────────
function abrirPainelVenenoRapido(){
  const existente = document.getElementById('painel-veneno-rapido');
  if(existente){ existente.remove(); return; }

  const me = GS.me;
  if(!me || me.class_id !== 'rogue') return;
  if(!_rogueMyTurn(me)){ toast('Só no seu turno.', 'var(--orange)'); return; }
  if((me.sede||0) < 1){ GS.adicionarLog('❌ Sede insuficiente 💧-1'); return; }

  const venenos = _venenosNaBolsa(me);
  if(venenos.length === 0){ GS.adicionarLog('❌ Sem venenos no inventário'); return; }

  const painel = document.createElement('div');
  painel.id = 'painel-veneno-rapido';
  painel.style.cssText = `position:fixed; bottom:180px; left:50%; transform:translateX(-50%);
    background:rgba(10,8,5,0.97); border:1px solid #9900cc; width:280px; z-index:200; padding:16px;
    font-family:'Cinzel',serif;`;
  painel.innerHTML = `
    <div style="font-family:'Cinzel Decorative',serif; color:#cc44ff; font-size:13px; margin-bottom:12px; text-align:center;">☠️ VENENO RÁPIDO</div>
    <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px; margin-bottom:10px; text-align:center;">Ação Livre | 💧-1 + consome o frasco</div>
    ${venenos.map(v => `
      <div onclick="confirmarVenenoRapido('${v.id}')" style="padding:10px 12px; margin-bottom:4px;
        background:rgba(150,0,200,0.06); border:1px solid #9900cc44; cursor:pointer; transition:all 0.2s;"
        onmouseover="this.style.borderColor='#9900cc'" onmouseout="this.style.borderColor='#9900cc44'">
        <div style="color:#cc44ff; font-size:11px; margin-bottom:3px;">${v.icone} ${v.nome}</div>
        <div style="color:#8a7a5a; font-size:9px;">${v.descricao || ''}</div>
      </div>`).join('')}
    <button onclick="document.getElementById('painel-veneno-rapido').remove()" style="width:100%; margin-top:10px; padding:8px; background:transparent; border:1px solid #4a4a4a; color:#8a7a5a; font-family:'Cinzel',serif; font-size:10px; letter-spacing:2px; cursor:pointer;">CANCELAR</button>`;
  document.body.appendChild(painel);

  window.confirmarVenenoRapido = function(venenoId){
    send({ type:'veneno_rapido', veneno_id:venenoId });
    document.getElementById('painel-veneno-rapido')?.remove();
  };
}

// ── Botões de habilidade do ladino (padrão skill-btn, como _paladinSkillBtn) ──
function _rogueSkillBtn(me, sk){
  const btn = document.createElement('button');
  const myTurnPlay = _rogueMyTurn(me);
  const fc = sk.fome_cost ?? 0, scst = sk.sede_cost ?? 0;
  const costStr = [fc?`🍖${fc}`:'', scst?`💧${scst}`:''].filter(Boolean).join(' ') || '—';
  const temRec  = (me.fome ?? 0) >= fc && (me.sede ?? 0) >= scst;

  const setBtn = (name, desc, cost, disabled, onclick, active) => {
    btn.className = 'skill-btn' + (active ? ' skill-active' : '');
    btn.disabled  = !!disabled;
    btn.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">${name}</div>
        <div class="skill-desc">${desc}</div>
      </div>
      <div class="skill-cost">${cost}</div>`;
    if(onclick) btn.onclick = onclick;
  };

  if(sk.id === 'ataque_furtivo'){
    const nd4 = (me.level ?? 1) <= 2 ? '2' : (me.level ?? 1) <= 4 ? '3' : '4';
    const nivelFurtivo = GS.ladinoFurtivoNivel ? GS.ladinoFurtivoNivel() : 1;
    const descFurtivo = nivelFurtivo >= 3
      ? `+${nd4}d4 se invisível ou com aliado adjacente; reage automaticamente 1×/inimigo/rodada ao ataque de um aliado`
      : nivelFurtivo === 2
      ? `+${nd4}d4 se invisível ou com aliado adjacente ao alvo`
      : `+${nd4}d4 apenas se estiver invisível/oculto`;
    setBtn(`🗡️ ${sk.name} <small style="color:var(--text2);font-size:.62rem;">passiva</small>`,
           descFurtivo, '—', true, null, false);

  } else if(sk.id === 'detectar_armadilhas'){
    if(me.detectar_ativo){
      setBtn(`🔍 ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● ativa</small>`,
             'revela armadilhas próximas e não as dispara', `manut. 💧1<br><small style="font-size:.6rem;">parar</small>`,
             false, () => send({type:'detectar_armadilhas'}), true);
    } else {
      const aviso = me.bonus_action_used ? ' <small style="color:var(--text2);font-size:.62rem;">bônus usado</small>' : '';
      setBtn(`🔍 ${sk.name}${aviso}`, sk.description || sk.desc || '', 'manut. 💧1',
             !(myTurnPlay && !me.bonus_action_used), () => send({type:'detectar_armadilhas'}), false);
    }

  } else if(sk.id === 'esconder_sombras'){
    const bonusEsc  = GS.ladinoEsconderBonus ? GS.ladinoEsconderBonus() : 0;
    const livreEsc  = GS.ladinoEsconderLivre ? GS.ladinoEsconderLivre() : false;
    const descEsc = `Teste de furtividade${bonusEsc>0?` (+${bonusEsc})`:''}${livreEsc?' — ação livre (não gasta bônus)':''}`;
    if(me.invisivel_sombras){
      setBtn(`🌑 ${sk.name} <small style="color:var(--gold);font-size:.65rem;">● invisível</small>`,
             `não é alvo dos monstros até atacar${livreEsc?' · +2 CA ao revelar':''}`, `manut. 🍖1 💧1<br><small style="font-size:.6rem;">sair</small>`,
             false, () => send({type:'esconder_sombras'}), true);
    } else {
      const pode  = myTurnPlay && (livreEsc || !me.bonus_action_used) && temRec;
      const aviso = (!livreEsc && me.bonus_action_used) ? ' <small style="color:var(--text2);font-size:.62rem;">bônus usado</small>'
                  : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
      setBtn(`🌑 ${sk.name}${aviso}`, descEsc, costStr, !pode,
             () => send({type:'esconder_sombras'}), false);
    }

  } else if(sk.id === 'veneno_rapido'){
    const venenos = _venenosNaBolsa(me);
    const maxHits = GS.ladinoVenenoMaxHits ? GS.ladinoVenenoMaxHits() : 1;
    const doisSlots = GS.ladinoVeneno2Slots ? GS.ladinoVeneno2Slots() : false;
    if(me.weapon_poison){
      const hits = me.weapon_poison_hits ?? 0;
      const slot2 = me.weapon_poison_2 ? ` + 2º veneno (${me.weapon_poison_2_hits ?? 0} golpe(s))` : (doisSlots ? ' · pode aplicar um 2º veneno' : '');
      setBtn(`☠️ ${sk.name} <small style="color:#cc44ff;font-size:.65rem;">● arma envenenada</small>`,
             `${hits}/${maxHits} golpe(s) restante(s)${slot2} — clique p/ trocar`, costStr,
             !(myTurnPlay && (me.sede ?? 0) >= scst && venenos.length > 0),
             () => abrirPainelVenenoRapido(), true);
    } else {
      const pode  = myTurnPlay && (me.sede ?? 0) >= scst && venenos.length > 0;
      const aviso = venenos.length === 0 ? ' <small style="color:var(--red);font-size:.62rem;">sem venenos</small>' : '';
      setBtn(`☠️ ${sk.name}${aviso}`, `dura ${maxHits} golpe(s) certeiro(s)${doisSlots?' · até 2 venenos simultâneos':''}`, costStr, !pode,
             () => abrirPainelVenenoRapido(), false);
    }

  } else if(sk.id === 'criar_armadilha'){
    const pode  = myTurnPlay && !me.action_done;
    const aviso = me.action_done ? ' <small style="color:var(--text2);font-size:.62rem;">ação usada</small>' : '';
    setBtn(`🪤 ${sk.name}${aviso}`, sk.description || sk.desc || '', costStr, !pode,
           () => abrirPainelCriarArmadilha(), false);

  } else {
    setBtn(`${sk.icon || ''} ${sk.name}`, sk.description || sk.desc || '', costStr, !myTurnPlay, null, false);
  }
  return btn;
}

// Botão "Desarmar Armadilha" — aparece só quando há armadilha na casa/adjacente.
function _rogueDesarmarBtn(me){
  if(!_temArmadilhaAdjacente(me)) return null;
  const btn = document.createElement('button');
  const pode = _rogueMyTurn(me) && !me.action_done;
  const bonusDes = GS.ladinoDesarmeBonus ? GS.ladinoDesarmeBonus() : 0;
  const recupera = GS.ladinoDesarmeRecupera ? GS.ladinoDesarmeRecupera() : false;
  btn.className = 'skill-btn';
  btn.disabled = !pode;
  btn.innerHTML = `
    <div class="skill-info">
      <div class="skill-name">🔧 Desarmar Armadilha${me.action_done ? ' <small style="color:var(--text2);font-size:.62rem;">ação usada</small>' : ''}</div>
      <div class="skill-desc">Teste de DES${bonusDes>0?` (+${bonusDes})`:''} na casa/adjacente (nat1 dispara em você)${recupera?' · chance de recuperar o ouro':''}</div>
    </div>
    <div class="skill-cost">principal</div>`;
  btn.onclick = () => send({type:'desarmar_armadilha'});
  return btn;
}

window.abrirPainelCriarArmadilha = abrirPainelCriarArmadilha;
window.abrirPainelVenenoRapido   = abrirPainelVenenoRapido;
window.onClickTileParaArmadilha  = onClickTileParaArmadilha;

// ═══════════════════════════════════════════════════════════════════════════
// FRADE LEWIS (cleric) — habilidades no cliente. Os 4 milagres (cura, cura_area,
// purificacao, ressurreicao) são ações principais dedicadas implementadas no
// servidor (ver server.py). Convenções REAIS do cliente: me.class_id (não `cls`),
// me.pos[0/1] (não tx/ty), GS.adicionarLog/toast, e seleção de alvo via
// openTargetModal — NÃO via highlights 3D. Cor temática: verde #44cc88.
// ═══════════════════════════════════════════════════════════════════════════

// Aliados VIVOS dentro de `raio` (Chebyshev). incluirSelf inclui o próprio Lewis.
function _aliadosVivosNoRaioCleric(me, raio, incluirSelf){
  const st = GS.gameState; if(!st) return [];
  const pp = me.pos || [0,0];
  return (st.players || []).filter(a => a && a.alive && a.pos &&
    (incluirSelf || a.id !== me.id) &&
    Math.max(Math.abs(pp[0]-a.pos[0]), Math.abs(pp[1]-a.pos[1])) <= raio);
}

// Aliados MORTOS dentro de `raio` (Ressurreição). Exclui o próprio Lewis.
function _aliadosMortosNoRaioCleric(me, raio){
  const st = GS.gameState; if(!st) return [];
  const pp = me.pos || [0,0];
  return (st.players || []).filter(a => a && a.alive === false && a.id !== me.id && a.pos &&
    Math.max(Math.abs(pp[0]-a.pos[0]), Math.abs(pp[1]-a.pos[1])) <= raio);
}

// Tipos de purificação — espelha PURIFICACAO_CUSTOS em server.py. `cond` lê os
// campos reais que o servidor envia no game_state (efeitos_veneno/cego/etc.).
const PURIFICACAO_TIPOS_LEWIS = [
  { id:'veneno',       label:'Veneno',       icone:'☠️', custo:'🍖-1',      cond: p => (p.efeitos_veneno && p.efeitos_veneno.length > 0) || p.cego },
  { id:'doenca',       label:'Doença',       icone:'🤒', custo:'🍖-2 💧-1', cond: p => !!p.doente },
  { id:'maldicao',     label:'Maldição',     icone:'💀', custo:'🍖-3 💧-2', cond: p => !!p.amaldicoado },
  { id:'petrificacao', label:'Petrificação', icone:'🗿', custo:'🍖-5 💧-5', cond: p => !!p.petrificado },
];

function _clericPodeAgir(me){
  if(!me || me.class_id !== 'cleric') return false;
  if(!GS.isMyTurn || me.alive === false || (GS.gameState && GS.gameState.phase !== 'playing')){
    toast('Só é possível usar milagres no seu turno.', 'var(--orange)'); return false;
  }
  if(me.action_done){ toast('Ação principal já usada neste turno.', 'var(--orange)'); return false; }
  return true;
}

// ── Cura individual — painel de configuração (dados + alcance) → alvo via modal ──
function abrirPainelCura(){
  const ex = document.getElementById('painel-cura');
  if(ex){ ex.remove(); return; }
  const me = GS.me;
  if(!_clericPodeAgir(me)) return;

  let numDados = 1, alcanceExtra = 0;
  const painel = document.createElement('div');
  painel.id = 'painel-cura';
  painel.style.cssText = `position:fixed;bottom:180px;left:50%;transform:translateX(-50%);
    background:rgba(10,8,5,0.97);border:1px solid #44cc88;width:300px;z-index:200;
    padding:16px;font-family:'Cinzel',serif;`;

  function render(){
    const bonusInt = getBonusAtributo(me.int_ ?? 10);
    const alcance  = 1 + alcanceExtra * 3;
    const custoFome = alcanceExtra, custoSede = numDados;
    painel.innerHTML = `
      <div style="font-family:'Cinzel Decorative',serif;color:#44cc88;font-size:13px;margin-bottom:12px;text-align:center;">🙌 CURA</div>
      <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:8px;">DADOS DE CURA — 💧-1 por dado</div>
      <div style="display:flex;gap:6px;margin-bottom:14px;">
        ${[1,2,3].filter(n => n <= GS.clericCuraTeto()).map(n => `<button onclick="window._curaSetDados(${n})" style="flex:1;padding:10px;
          background:${numDados===n?'rgba(68,204,136,0.20)':'transparent'};
          border:1px solid ${numDados===n?'#44cc88':'#2a2a2a'};color:${numDados===n?'#44cc88':'#c8b89a'};
          font-family:'Cinzel',serif;font-size:12px;cursor:pointer;">${n}d8</button>`).join('')}
      </div>
      <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:8px;">ALCANCE — 🍖-1 por extensão</div>
      <div style="display:flex;gap:6px;margin-bottom:14px;">
        ${[{v:0,l:'Adjacente'},{v:1,l:'+3 quad.'},{v:2,l:'+6 quad.'}].map(o => `<button onclick="window._curaSetAlcance(${o.v})" style="flex:1;padding:8px;
          background:${alcanceExtra===o.v?'rgba(68,204,136,0.15)':'transparent'};
          border:1px solid ${alcanceExtra===o.v?'#44cc88':'#2a2a2a'};color:${alcanceExtra===o.v?'#44cc88':'#c8b89a'};
          font-family:'Cinzel',serif;font-size:10px;cursor:pointer;">${o.l}</button>`).join('')}
      </div>
      <div style="padding:10px 12px;margin-bottom:12px;background:rgba(68,204,136,0.06);border:1px solid #44cc8833;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:#8a7a5a;font-size:10px;">Cura estimada</span><span style="color:#44cc88;font-size:12px;font-weight:bold;">${numDados}d8 ${bonusInt>=0?'+':''}${bonusInt} INT</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:#8a7a5a;font-size:10px;">Alcance</span><span style="color:#44cc88;font-size:11px;">${alcance} quadrado(s)</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#8a7a5a;font-size:10px;">Custo</span><span style="color:#ff851b;font-size:11px;">${custoFome>0?`🍖-${custoFome} `:''}💧-${custoSede}</span></div>
      </div>
      <div style="display:flex;gap:6px;">
        <button onclick="document.getElementById('painel-cura').remove()" style="flex:1;padding:8px;background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">CANCELAR</button>
        <button onclick="window._curaConfirmar()" style="flex:2;padding:8px;background:rgba(68,204,136,0.15);border:1px solid #44cc88;color:#44cc88;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">🙌 CURAR</button>
      </div>`;
  }

  window._curaSetDados   = (n) => { numDados = n; render(); };
  window._curaSetAlcance = (v) => { alcanceExtra = v; render(); };
  window._curaConfirmar  = () => {
    const meNow = GS.me;
    const alcance = 1 + alcanceExtra * 3;
    if((meNow.sede||0) < numDados){ toast(`Sede insuficiente 💧${numDados}`, 'var(--orange)'); return; }
    if((meNow.fome||0) < alcanceExtra){ toast(`Fome insuficiente 🍖${alcanceExtra}`, 'var(--orange)'); return; }
    const alvos = _aliadosVivosNoRaioCleric(meNow, alcance, true);
    document.getElementById('painel-cura')?.remove();
    if(!alvos.length){ toast('Nenhum aliado no alcance.', 'var(--orange)'); return; }
    const enviar = (id) => send({ type:'cura', target_id:id, num_dados:numDados, alcance_extra:alcanceExtra });
    if(alvos.length === 1){ enviar(alvos[0].id); return; }
    openTargetModal(`🙌 Cura ${numDados}d8 — alcance ${alcance}q`, alvos, 'player', enviar);
  };

  render();
  document.body.appendChild(painel);
}

// ── Cura em área — painel de configuração (dados) → envia (sem alvo) ──
function abrirPainelCuraArea(){
  const ex = document.getElementById('painel-cura-area');
  if(ex){ ex.remove(); return; }
  const me = GS.me;
  if(!_clericPodeAgir(me)) return;

  let numDados = 1;
  const painel = document.createElement('div');
  painel.id = 'painel-cura-area';
  painel.style.cssText = `position:fixed;bottom:180px;left:50%;transform:translateX(-50%);
    background:rgba(10,8,5,0.97);border:1px solid #44cc88;width:280px;z-index:200;
    padding:16px;font-family:'Cinzel',serif;`;

  function render(){
    const bonusInt = getBonusAtributo(me.int_ ?? 10);
    const custo = numDados * 4;
    const _mNivel = GS.clericMassaNivel(), _mRaio = 2 * _mNivel;
    painel.innerHTML = `
      <div style="font-family:'Cinzel Decorative',serif;color:#44cc88;font-size:13px;margin-bottom:12px;text-align:center;">🌟 CURA EM ÁREA</div>
      <div style="color:#8a7a5a;font-size:9px;letter-spacing:2px;margin-bottom:8px;text-align:center;">Raio ${_mRaio} quadrados | 🍖-4 💧-4 por dado</div>
      <div style="display:flex;gap:6px;margin-bottom:14px;">
        ${[1,2,3].filter(n => n <= _mNivel).map(n => `<button onclick="window._curaAreaSetDados(${n})" style="flex:1;padding:10px;
          background:${numDados===n?'rgba(68,204,136,0.20)':'transparent'};
          border:1px solid ${numDados===n?'#44cc88':'#2a2a2a'};color:${numDados===n?'#44cc88':'#c8b89a'};
          font-family:'Cinzel',serif;font-size:12px;cursor:pointer;">${n}d8</button>`).join('')}
      </div>
      <div style="padding:10px 12px;margin-bottom:12px;background:rgba(68,204,136,0.06);border:1px solid #44cc8833;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:#8a7a5a;font-size:10px;">Cura para todos</span><span style="color:#44cc88;font-size:12px;">${numDados}d8 ${bonusInt>=0?'+':''}${bonusInt}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:#8a7a5a;font-size:10px;">Raio</span><span style="color:#44cc88;font-size:11px;">${_mRaio} quadrados</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="color:#8a7a5a;font-size:10px;">Custo</span><span style="color:#ff851b;font-size:11px;">🍖-${custo} 💧-${custo}</span></div>
      </div>
      <div style="display:flex;gap:6px;">
        <button onclick="document.getElementById('painel-cura-area').remove()" style="flex:1;padding:8px;background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:10px;cursor:pointer;">CANCELAR</button>
        <button onclick="window._curaAreaConfirmar()" style="flex:2;padding:8px;background:rgba(68,204,136,0.15);border:1px solid #44cc88;color:#44cc88;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">🌟 CURAR ÁREA</button>
      </div>`;
  }

  window._curaAreaSetDados  = (n) => { numDados = n; render(); };
  window._curaAreaConfirmar = () => {
    const meNow = GS.me, custo = numDados * 4;
    if((meNow.fome||0) < custo || (meNow.sede||0) < custo){ toast(`Recursos insuficientes 🍖${custo} 💧${custo}`, 'var(--orange)'); return; }
    send({ type:'cura_area', num_dados:numDados });
    document.getElementById('painel-cura-area')?.remove();
  };

  render();
  document.body.appendChild(painel);
}

// ── Purificação — escolhe aliado adjacente afligido via modal; se vários efeitos,
// abre painel de escolha do tipo. Envia { type:'purificacao', target_id, tipo }. ──
function iniciarModoPurificacao(){
  const me = GS.me;
  if(!_clericPodeAgir(me)) return;
  // Só os tipos destravados pela Guilda (Fase 1b): venenos base; +doenças; +maldições/petrificação.
  const _permitidos = GS.clericPurifTipos();
  const alvos = _aliadosVivosNoRaioCleric(me, 1, true)
    .filter(a => PURIFICACAO_TIPOS_LEWIS.some(t => _permitidos.includes(t.id) && t.cond(a)));
  if(!alvos.length){ toast('Nenhum aliado adjacente com efeito que você saiba purificar.', 'var(--orange)'); return; }
  const escolher = (id) => {
    const alvo = (GS.gameState.players || []).find(p => p.id === id);
    if(!alvo) return;
    const efeitos = PURIFICACAO_TIPOS_LEWIS.filter(t => _permitidos.includes(t.id) && t.cond(alvo));
    if(efeitos.length === 0){ toast(`${alvo.name} não tem efeitos que você saiba purificar.`, 'var(--orange)'); return; }
    if(efeitos.length === 1){ send({ type:'purificacao', target_id:id, tipo:efeitos[0].id }); return; }
    _abrirPainelEscolhaPurificacao(alvo, efeitos);
  };
  if(alvos.length === 1){ escolher(alvos[0].id); return; }
  openTargetModal('✨ Purificação — Aliado adjacente', alvos, 'player', escolher);
}

function _abrirPainelEscolhaPurificacao(alvo, efeitos){
  document.getElementById('painel-purificacao')?.remove();
  const painel = document.createElement('div');
  painel.id = 'painel-purificacao';
  painel.style.cssText = `position:fixed;bottom:180px;left:50%;transform:translateX(-50%);
    background:rgba(10,8,5,0.97);border:1px solid #cc44ff;width:260px;z-index:200;
    padding:16px;font-family:'Cinzel',serif;`;
  painel.innerHTML = `
    <div style="font-family:'Cinzel Decorative',serif;color:#cc44ff;font-size:12px;margin-bottom:10px;text-align:center;">✨ PURIFICAR ${(alvo.name||'').toUpperCase()}</div>
    ${efeitos.map(ef => `<button onclick="window._purificarConfirmar('${alvo.id}','${ef.id}')" style="width:100%;padding:10px 12px;margin-bottom:4px;background:rgba(204,68,255,0.06);border:1px solid #cc44ff44;color:#c8b89a;font-family:'Cinzel',serif;font-size:11px;text-align:left;cursor:pointer;display:flex;justify-content:space-between;" onmouseover="this.style.borderColor='#cc44ff'" onmouseout="this.style.borderColor='#cc44ff44'"><span>${ef.icone} ${ef.label}</span><span style="color:#ff851b;font-size:10px;">${ef.custo}</span></button>`).join('')}
    <button onclick="document.getElementById('painel-purificacao').remove()" style="width:100%;margin-top:6px;padding:8px;background:transparent;border:1px solid #4a4a4a;color:#8a7a5a;font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">CANCELAR</button>`;
  document.body.appendChild(painel);
  window._purificarConfirmar = (targetId, tipo) => {
    send({ type:'purificacao', target_id:targetId, tipo });
    document.getElementById('painel-purificacao')?.remove();
  };
}

// ── Ressurreição — escolhe aliado MORTO adjacente via modal e envia. ──
function iniciarModoRessurreicao(){
  const me = GS.me;
  if(!_clericPodeAgir(me)) return;
  // Custo e efeito por nível da especialização (Fase 1b): 1 HP/10 · metade/15 · cheio/20.
  const _rNivel = GS.clericRessurNivel();
  const _rCusto = {1:10, 2:15, 3:20}[_rNivel];
  const _rEfeito = {1:'1 HP', 2:'metade dos PV', 3:'PV cheio'}[_rNivel];
  if((me.fome||0) < _rCusto || (me.sede||0) < _rCusto){ toast(`Ressurreição requer 🍖${_rCusto} e 💧${_rCusto}.`, 'var(--orange)'); return; }
  const mortos = _aliadosMortosNoRaioCleric(me, 1);
  if(!mortos.length){ toast('Nenhum aliado morto adjacente.', 'var(--orange)'); return; }
  const enviar = (id) => send({ type:'ressurreicao', target_id:id });
  if(mortos.length === 1){ enviar(mortos[0].id); return; }
  openTargetModal(`💫 Ressurreição (${_rEfeito}) — Aliado morto adjacente`, mortos, 'player', enviar);
}

// Botão de habilidade do Frade Lewis (padrão skill-btn, como _paladinSkillBtn).
function _clericSkillBtn(me, sk){
  const btn = document.createElement('button');
  const myTurnPlay = GS.isMyTurn && me.alive && GS.gameState && GS.gameState.phase === 'playing';
  const fc = sk.fome_cost ?? 0, scst = sk.sede_cost ?? 0;
  const costStr = [fc?`🍖${fc}`:'', scst?`💧${scst}`:''].filter(Boolean).join(' ') || '—';
  const acaoUsada = me.action_done;
  const podePrincipal = myTurnPlay && !acaoUsada;
  const avisoAcao = acaoUsada ? ' <small style="color:var(--text2);font-size:.62rem;">ação usada</small>' : '';

  const setBtn = (name, desc, cost, disabled, onclick) => {
    btn.className = 'skill-btn';
    btn.disabled  = !!disabled;
    btn.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">${name}</div>
        <div class="skill-desc">${desc}</div>
      </div>
      <div class="skill-cost">${cost}</div>`;
    if(onclick) btn.onclick = onclick;
  };

  const desc = sk.description || sk.desc || '';
  if(sk.id === 'cura'){
    setBtn(`🙌 ${sk.name}${avisoAcao}`, desc, '💧1+ / dado', !podePrincipal, () => abrirPainelCura());
  } else if(sk.id === 'cura_area'){
    setBtn(`🌟 ${sk.name}${avisoAcao}`, desc, '🍖4 💧4 / dado', !podePrincipal, () => abrirPainelCuraArea());
  } else if(sk.id === 'purificacao'){
    setBtn(`✨ ${sk.name}${avisoAcao}`, desc, '🍖1 a 5', !podePrincipal, () => iniciarModoPurificacao());
  } else if(sk.id === 'ressurreicao'){
    const temRec = (me.fome||0) >= 10 && (me.sede||0) >= 10;
    const aviso  = acaoUsada ? avisoAcao
                 : !temRec ? ' <small style="color:var(--red);font-size:.62rem;">sem recursos</small>' : '';
    setBtn(`💫 ${sk.name}${aviso}`, desc, costStr, !podePrincipal || !temRec, () => iniciarModoRessurreicao());
  } else {
    setBtn(`${sk.icon || ''} ${sk.name}`, desc, costStr, !myTurnPlay, null);
  }
  return btn;
}

// ─── Mago (Pedro): METAMAGIA (cliente) ──────────────────────────────────────
// 3 ações livres (toggles) EMPILHÁVEIS que MODIFICAM a magia do GRIMÓRIO lançada
// no turno (mensagem `magia` / handle_magia). O servidor cobra o custo ao LANÇAR
// e SÓ se a habilidade tiver efeito. Aqui só armamos/desarmamos (toggle).
// Magnitudes BASE (escalam com as especializações da Guilda — Fase 1f); baseline:
// só 1 metamagia por lançamento (Tecelagem Arcana desbloqueia empilhar 2/3).
//   🎯 Aprimorar  → +1 na CD do teste de resistência (base) (🍖-3)
//   ⏱️ Estender   → +1 turno na duração (base)              (🍖-3 💧-3)
//   💥 Fortalecer → dano ×1,25 (base)                       (🍖-6 💧-6)
function _mageSkillBtn(me, sk){
  const btn = document.createElement('button');
  const myTurnPlay = GS.isMyTurn && me.alive && GS.gameState && GS.gameState.phase === 'playing';
  let desc = sk.description || sk.desc || '';
  // A descrição reflete a magnitude possuída da especialização e o teto de
  // empilhamento (Fase 1f). Texto informativo — o servidor é autoritativo.
  {
    const cap = GS.magoTecelagemCap ? GS.magoTecelagemCap() : 1;
    const capTxt = ` (empilha até ${cap})`;
    if (sk.id === 'fortalecer_magia') {
      const mult = GS.magoFortalecerMult ? GS.magoFortalecerMult() : 1.25;
      desc = `Ação livre. Multiplica o dano da magia por ${String(mult).replace('.', ',')}.${capTxt}`;
    } else if (sk.id === 'aprimorar_magia') {
      const b = GS.magoAprimorarBonus ? GS.magoAprimorarBonus() : 1;
      desc = `Ação livre. +${b} na CD do teste de resistência da magia.${capTxt}`;
    } else if (sk.id === 'estender_magia') {
      const b = GS.magoEstenderBonus ? GS.magoEstenderBonus() : 1;
      desc = `Ação livre. +${b} rodada${b !== 1 ? 's' : ''} na duração da magia.${capTxt}`;
    }
  }
  const cfg = ({
    aprimorar_magia:  { icon: '🎯', flag: 'aprimorar_ativo',  custo: '🍖3'     },
    estender_magia:   { icon: '⏱️', flag: 'estender_ativo',   custo: '🍖3 💧3' },
    fortalecer_magia: { icon: '💥', flag: 'fortalecer_ativo', custo: '🍖6 💧6' },
  })[sk.id];
  if(!cfg){
    btn.className = 'skill-btn'; btn.disabled = true;
    btn.innerHTML = `<div class="skill-info"><div class="skill-name">${sk.icon||''} ${sk.name}</div></div>`;
    return btn;
  }
  const ativo = !!me[cfg.flag];
  btn.className = 'skill-btn' + (ativo ? ' skill-active' : '');
  btn.disabled  = !myTurnPlay;
  btn.innerHTML = `
    <div class="skill-info">
      <div class="skill-name">${cfg.icon} ${sk.name}${ativo ? ' <small style="color:var(--gold);font-size:.65rem;">● armada</small>' : ''}</div>
      <div class="skill-desc">${desc}</div>
    </div>
    <div class="skill-cost">${ativo ? 'parar' : cfg.custo}</div>`;
  btn.onclick = () => send({ type: sk.id });   // toggle: o servidor arma/desarma
  return btn;
}

// Exposição global (paridade com as demais classes; usado pelo loop de skills).
window._mageSkillBtn = _mageSkillBtn;

// Aba MAGIAS da ficha do Lewis (painel principal e seleção). O sistema de magias
// preparadas ainda não existe no servidor — por ora mostra os espaços de magia
// por nível como placeholder (mesmo padrão visual da aba do Pedro).
// ═══════════════════════════════════════════════════════════════════════════
// GRIMÓRIO (CLIENTE) — catálogo de cartas de magia (espelha GRIMORIO em server.py)
// Camada VISUAL: cartas + tooltip + abas de Pedro/Lewis. Os ids e círculos batem
// com o servidor; o lançamento (mensagem `magia`) será ligado no próximo passo.
// Adaptação ao cliente real: `me.class_id`/`me.level` (não cls/nivel); quando o
// herói não traz lista de magias conhecidas, mostramos TODAS as elegíveis pela
// classe (consistente com o gating por classe do servidor — ver handle_magia).
// ═══════════════════════════════════════════════════════════════════════════
const GRIMORIO_CLIENT = {
  // ── 1º CÍRCULO — MAGO ──────────────────────────────────────────────────────
  bola_fogo: {
    id:'bola_fogo', nome:'Bola de Fogo', icone:'🔥',
    circulo:'primeiro', classe:['mage'],
    tipo:'area_persistente', alcance_base:5, alcance_escala:1,
    custo:'🍖-1 💧-1',
    resumo:'1d6/nível. Área persiste 3 rodadas decaindo.',
    descricao:`<b>Alcance:</b> 5 +1 por nível<br>
               <b>R1:</b> 1d6 por nível | Reflexos: metade<br>
               <b>R2:</b> metade do dano R1<br>
               <b>R3:</b> metade do dano R2<br>
               <b>Área persiste:</b> entrar sofre dano, sair evita futuro<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  relampago: {
    id:'relampago', nome:'Relâmpago', icone:'⚡',
    circulo:'primeiro', classe:['mage'],
    tipo:'linha_reflexiva', alcance_base:7, alcance_escala:2,
    custo:'🍖-1 💧-1',
    resumo:'1d6/nível por impacto. Linha de 7 + ricochete.',
    descricao:`<b>Alcance:</b> 7 casas em linha reta (+2 por nível)<br>
               <b>Dano:</b> 1d6 por nível por impacto<br>
               <b>Ricochete:</b> volta pelo mesmo trajeto — casas atingidas 2x (verde escuro)<br>
               <b>Save:</b> Reflexos → metade por impacto<br>
               <b>⚠️ Pedro só é ferido na volta; pode ferir aliados</b>`
  },
  raio_congelante: {
    id:'raio_congelante', nome:'Raio Congelante', icone:'❄️',
    circulo:'primeiro', classe:['mage'],
    tipo:'alvo', alcance_base:3, alcance_escala:1,
    custo:'🍖-1 💧-1',
    resumo:'3d4+2d4/2níveis sem save. Fortitude ou paralisado.',
    descricao:`<b>Alcance:</b> 3 +1 por nível<br>
               <b>Dano:</b> 3d4 +2d4 a cada 2 níveis<br>
               <b>⚠️ Sem Reflexos:</b> dano sempre total<br>
               <b>Fortitude:</b> falha → paralisado 1 rodada<br>
               <b>Rodada seguinte:</b> novo Fortitude<br>
               <b>Sucesso:</b> age normalmente<br>
               <b>Falha:</b> mais 1 rodada (máx 2)`
  },
  sono: {
    id:'sono', nome:'Sono', icone:'🌙',
    circulo:'primeiro', classe:['mage'],
    tipo:'area', alcance:5, area:2,
    custo:'🍖-1 💧-1',
    resumo:'Área. Vontade ou dorme 1d4+1.',
    descricao:`<b>Save:</b> Vontade<br>
               <b>Falha:</b> dorme 1d4+1 rodadas<br>
               <b>Bônus:</b> 1º ataque contra dormindo = crítico<br>
               <b>Acorda:</b> ao receber qualquer dano<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  comando: {
    id:'comando', nome:'Comando', icone:'🗣️',
    circulo:'primeiro', classe:['mage','cleric'],
    tipo:'alvo', alcance:4,
    custo:'🍖-1 💧-1',
    resumo:'Vontade ou controla 1 ação.',
    descricao:`<b>Save:</b> Vontade<br>
               <b>Falha:</b> caster controla próxima ação<br>
               <b>Limitação:</b> sem habilidades especiais<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  medo: {
    id:'medo', nome:'Medo', icone:'😱',
    circulo:'primeiro', classe:['mage','cleric'],
    tipo:'area', alcance:5, area:2,
    custo:'🍖-1 💧-1',
    resumo:'Área. Vontade ou foge 1d4+1.',
    descricao:`<b>Save:</b> Vontade<br>
               <b>Falha:</b> foge 1d4+1 rodadas<br>
               <b>Efeitos:</b> -1 ataque, não se aproxima<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  clarividencia: {
    id:'clarividencia', nome:'Clarividência', icone:'🔮',
    circulo:'primeiro', classe:['mage','cleric'],
    tipo:'area_fixa', alcance:8, alvoLivre:true,   // alvoLivre: mira em QUALQUER casa do mapa (até na névoa)
    custo:'🍖-1 💧-1',
    resumo:'Revela área (monstros + armadilhas) em qualquer ponto do mapa. Dura 2 rodadas.',
    descricao:`<b>Alcance:</b> o mapa inteiro (mire em qualquer lugar)<br>
               <b>Área:</b> 4x4 (escala com nível)<br>
               <b>Efeito:</b> revela a névoa, os monstros e as armadilhas do local<br>
               <b>Duração:</b> 2 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  barreira_arcana: {
    id:'barreira_arcana', nome:'Barreira Arcana', icone:'🛡️',
    circulo:'primeiro', classe:['mage'],
    tipo:'buff_self', alcance:0,
    custo:'slot ao absorver',
    resumo:'Cancela 1 magia. Slot ao absorver.',
    descricao:`<b>Efeito:</b> cancela próxima magia recebida<br>
               <b>Duração:</b> até absorver<br>
               <b>Slot:</b> consumido ao absorver (não ao ativar)<br>
               <b>Ativação:</b> reação quando inimigo lança`
  },
  contramagica: {
    id:'contramagica', nome:'Contramágica', icone:'🛑',
    circulo:'primeiro', classe:['mage'],
    tipo:'reacao', alcance:0,
    custo:'🍖-1 💧-1 + 1 slot',
    resumo:'Reação. Teste oposto cancela magia.',
    descricao:`<b>Tipo:</b> Reação (fora do turno)<br>
               <b>Mecânica:</b> d20+INT vs inimigo d20+bônus<br>
               <b>Sucesso:</b> magia cancelada + inimigo perde ação<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot ao usar`
  },
  abencoar: {
    id:'abencoar', nome:'Abençoar', icone:'✨',
    circulo:'primeiro', classe:['cleric'],
    tipo:'area', alcance:0, area:3,
    custo:'🍖-1 💧-1',
    resumo:'Área 6x6. +1 ataque/dano/CA/res.',
    descricao:`<b>Área:</b> 6x6 centrado em Lewis<br>
               <b>Buff:</b> +1 ataque, dano, CA, resistência<br>
               <b>Duração:</b> 1d4+1 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  amaldicoar: {
    id:'amaldicoar', nome:'Amaldiçoar', icone:'☠️',
    circulo:'primeiro', classe:['cleric'],
    tipo:'area', alcance:5, area:1,
    custo:'🍖-1 💧-1',
    resumo:'Área 3x3. -1 ataque/dano/CA/res.',
    descricao:`<b>Área:</b> 3x3 centrado no alvo<br>
               <b>Debuff:</b> -1 ataque, dano, CA, resistência<br>
               <b>Duração:</b> 1d4+1 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  abencoar_arma: {
    id:'abencoar_arma', nome:'Abençoar Arma', icone:'⚔️',
    circulo:'primeiro', classe:['cleric'],
    tipo:'alvo_aliado', alcance:6,
    custo:'🍖-1 💧-1',
    resumo:'Arma de aliado +1 ataque/dano.',
    descricao:`<b>Alcance:</b> 6 quadrados<br>
               <b>Buff:</b> +1 ataque e dano na arma<br>
               <b>Duração:</b> 1d6+2 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  saciar: {
    id:'saciar', nome:'Saciar', icone:'💧',
    circulo:'primeiro', classe:['cleric'],
    tipo:'toque', alcance:1,
    custo:'🍖-1 💧-1',
    resumo:'Toque. +10 fome +10 sede.',
    descricao:`<b>Alcance:</b> adjacente<br>
               <b>Efeito:</b> +10 fome e +10 sede<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  // ── 2º CÍRCULO ─────────────────────────────────────────────────────────────
  silencio: {
    id:'silencio', nome:'Silêncio', icone:'🔇',
    circulo:'segundo', classe:['mage','cleric'],
    tipo:'area_fixa', alcance_base:5, alcance_escala:1, area_lado:4,
    custo:'🍖-1 💧-1',
    resumo:'Área 4x4. Sem magias nem Canção dentro.',
    descricao:`<b>Área:</b> 4x4 centrado no ponto<br>
               <b>Efeito:</b> magias não funcionam na área<br>
               <b>Duração:</b> 1d4+1 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  manto_escuridao: {
    id:'manto_escuridao', nome:'Manto de Escuridão', icone:'🌑',
    circulo:'segundo', classe:['mage','cleric'],
    tipo:'area_centrada', alcance:0, area:3,
    custo:'🍖-1 💧-1',
    resumo:'Raio 3. Escuridão — desvantagem sem visão noturna.',
    descricao:`<b>Raio:</b> 3 quadrados centrado no caster<br>
               <b>Sem visão noturna:</b> 2d20 usa menor nos ataques<br>
               <b>Com visão noturna:</b> 2d20 usa maior vs cegos<br>
               <b>Distância máxima à distância:</b> 2 quadrados<br>
               <b>Duração:</b> 1d4 rodadas`
  },
  criar_alimentos: {
    id:'criar_alimentos', nome:'Criar Alimentos', icone:'🍞',
    circulo:'segundo', classe:['cleric'],
    tipo:'utilidade', alcance:0,
    custo:'🍖-1 💧-1',
    resumo:'Cria pão e água. Lewis distribui.',
    descricao:`<b>Cria:</b> 1d6+1 água e 1d6+2 pão<br>
               <b>Distribuição:</b> Lewis escolhe quem recebe<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  regeneracao_magica: {
    id:'regeneracao_magica', nome:'Regeneração', icone:'🌿',
    circulo:'segundo', classe:['cleric'],
    tipo:'buff_aliado', alcance:6,
    custo:'🍖-1 💧-1',
    resumo:'Pool 2d6+2. +1 HP/rodada.',
    descricao:`<b>Pool:</b> 2d6+2 pontos de regeneração<br>
               <b>Cura:</b> +1 HP no início do turno do alvo<br>
               <b>Se morrer:</b> volta com 1 HP (-3 fome/sede)<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  protecao_energia: {
    id:'protecao_energia', nome:'Proteção contra Energia', icone:'🛡️',
    circulo:'segundo', classe:['mage','cleric'],
    tipo:'buff_self', alcance:0,
    custo:'🍖-1 💧-1',
    resumo:'Absorve 10 dano/rodada de fogo, gelo ou eletricidade.',
    descricao:`<b>Proteção:</b> 10 pontos/rodada de dano elemental<br>
               <b>Tipos:</b> fogo, gelo ou eletricidade<br>
               <b>Duração:</b> 1d6+1 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  invisibilidade: {
    id:'invisibilidade', nome:'Invisibilidade', icone:'🫥',
    circulo:'segundo', classe:['mage'],
    tipo:'buff_self', alcance:0,
    custo:'🍖-1 💧-1',
    resumo:'Inimigos não atacam. Vantagem + furtivo.',
    descricao:`<b>Efeito:</b> inimigos não podem atacar<br>
               <b>Ataque:</b> com vantagem (2d20 maior) + furtivo<br>
               <b>Quebra:</b> ao atacar ou lançar magia<br>
               <b>Duração:</b> 1d6+1 rodadas`
  },
  visao_escuro: {
    id:'visao_escuro', nome:'Visão no Escuro', icone:'👁️',
    circulo:'segundo', classe:['mage','cleric'],
    tipo:'buff_aliado', alcance:6,
    custo:'🍖-1 💧-1',
    resumo:'Aliado ignora escuridão. 1d6+2 rodadas.',
    descricao:`<b>Efeito:</b> ignora completamente o sistema de escuridão<br>
               <b>Duração:</b> 1d6+2 rodadas<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  jato_ar: {
    id:'jato_ar', nome:'Jato de Ar', icone:'🌪️',
    circulo:'segundo', classe:['mage'],
    tipo:'cone', comprimento:4, base:4,
    custo:'🍖-1 💧-1',
    resumo:'Cone. 1d6 dano + empurrão.',
    descricao:`<b>Cone:</b> 4 quadrados comp., 4 base<br>
               <b>Dano:</b> 1d6<br>
               <b>Falha Reflexos:</b> empurra 1d6 quadrados<br>
               <b>Sucesso:</b> empurra 2 quadrados<br>
               <b>Colisão parede:</b> +1d4 dano`
  },
  // ── 3º CÍRCULO ─────────────────────────────────────────────────────────────
  velocidade: {
    id:'velocidade', nome:'Velocidade', icone:'⚡',
    circulo:'terceiro', classe:['mage'],
    tipo:'buff_self', alcance:0,
    custo:'🍖-1 💧-1',
    resumo:'Dobra ações no turno. 1d4 rodadas.',
    descricao:`<b>Efeito:</b> todas as ações são dobradas<br>
               <b>Custo:</b> cada ação ainda custa fome/sede<br>
               <b>Duração:</b> 1d4 rodadas`
  },
  lentidao: {
    id:'lentidao', nome:'Lentidão', icone:'🐌',
    circulo:'terceiro', classe:['mage'],
    tipo:'area', alcance:5, area:1,
    custo:'🍖-1 💧-1',
    resumo:'Área 3x3. Falha: 1 ação/turno, -1 CA.',
    descricao:`<b>Save:</b> Vontade<br>
               <b>Falha:</b> 1 ação/rodada, sem reação, -1 CA<br>
               <b>Sucesso:</b> movimento ÷2, -1 ataque<br>
               <b>Duração:</b> 1d4 rodadas`
  },
  dominar_mente: {
    id:'dominar_mente', nome:'Dominar Mente', icone:'🧠',
    circulo:'terceiro', classe:['mage','cleric'],
    tipo:'alvo', alcance:5,
    custo:'🍖-1 💧-1',
    resumo:'Vontade ou dominado 1d4 rodadas.',
    descricao:`<b>Save:</b> Vontade<br>
               <b>Falha:</b> dominado 1d4 rodadas<br>
               <b>Novo teste:</b> ao sofrer dano (mesma dificuldade)<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  },
  dominar_morto_vivo: {
    id:'dominar_morto_vivo', nome:'Dominar Morto-Vivo', icone:'💀',
    circulo:'terceiro', classe:['mage'],
    tipo:'alvo', alcance:4,
    custo:'🍖-1 💧-1',
    resumo:'Controle progressivo de morto-vivo (3 rodadas).',
    descricao:`<b>Requer:</b> alvo do tipo morto-vivo<br>
               <b>Save:</b> Vontade (bônus = ND) ao lançar e a cada rodada<br>
               <b>Falha:</b> vira servo temporário (age na fase dos servos)<br>
               <b>3 falhas seguidas:</b> controle PERMANENTE<br>
               <b>Passar:</b> quebra o controle (volta hostil) — relançar<br>
               <b>Slot único</b> · não conta para Animar Mortos`
  },
  conjurar_elemental: {
    id:'conjurar_elemental', nome:'Conjurar Elemental', icone:'🌪️',
    circulo:'terceiro', classe:['cleric'],
    tipo:'invocacao', alcance:0,
    custo:'🍖-1 💧-1',
    resumo:'Invoca elemental controlado. 6 quad./turno.',
    descricao:`<b>Tipos:</b> Fogo (HP18 2d6), Elétrico (HP20 linha),
               Gelo (HP22 -2fís), Pedra (HP26 ½fís)<br>
               <b>Controle:</b> age após Lewis, 6 quad. movimento<br>
               <b>⚠️ Explosão afeta aliados`
  },
  raio_divino: {
    id:'raio_divino', nome:'Raio Divino', icone:'✨',
    circulo:'terceiro', classe:['cleric'],
    tipo:'alvo', alcance:6,
    custo:'🍖-1 💧-1',
    resumo:'1d6+1 por nível. Dobrado vs mortos.',
    descricao:`<b>Dano:</b> 1d6+1 por nível do personagem<br>
               <b>Save:</b> Reflexos → metade<br>
               <b>Vs mortos-vivos/demônios:</b> dano dobrado<br>
               <b>Custo:</b> 🍖-1 💧-1 + 1 slot`
  }
};

const _COR_CIRCULO = { primeiro:'#c8a951', segundo:'#4488ff', terceiro:'#cc44ff' };
const _RGB_CIRCULO = { primeiro:'200,169,81', segundo:'68,136,255', terceiro:'204,68,255' };
const _LABEL_CIRCULO = { primeiro:'1º Círculo', segundo:'2º Círculo', terceiro:'3º Círculo' };

// Carta de magia 60x72 — cor por círculo (ver VISUAL_CONTRACT.md).
function criarCartaMagia(magiaId, selecionada, disponivel, usada, modo) {
  const m = GRIMORIO_CLIENT[magiaId];
  if (!m) return '';
  const corCirculo = _COR_CIRCULO[m.circulo] || '#c8a951';
  const cor = usada ? '#2a2a2a' : disponivel ? corCirculo : '#4a4a4a';
  const rgb = _RGB_CIRCULO[m.circulo] || '200,169,81';
  // modo 'jogo' → clicar LANÇA a magia; 'selecao' (default) → escolhe na criação.
  const acao = (modo === 'jogo') ? `castarMagia('${magiaId}')` : `selecionarMagia('${magiaId}')`;
  return `
    <div class="carta-magia"
      data-magia-id="${magiaId}"
      onclick="${disponivel && !usada ? acao : ''}"
      onmouseenter="mostrarTooltipMagia('${magiaId}', event)"
      onmouseleave="ocultarTooltipMagia()"
      style="
        display:inline-flex; flex-direction:column;
        align-items:center; justify-content:center;
        width:60px; height:72px;
        background:${selecionada ? `rgba(${rgb},0.20)` : usada ? 'rgba(20,20,20,0.8)' : 'rgba(255,255,255,0.03)'};
        border:2px solid ${selecionada ? cor : usada ? '#1a1a1a' : cor + '44'};
        border-radius:4px;
        cursor:${disponivel && !usada ? 'pointer' : 'not-allowed'};
        opacity:${usada ? 0.35 : disponivel ? 1 : 0.5};
        transition:all 0.2s; position:relative; margin:3px;
      "
      onmouseover="if(${disponivel && !usada})this.style.borderColor='${cor}'"
      onmouseout="if(!${selecionada})this.style.borderColor='${cor}44'"
    >
      <div style="position:absolute; top:3px; right:3px; width:8px; height:8px; border-radius:50%; background:${cor}; opacity:${usada ? 0.3 : 1};"></div>
      <div style="font-size:22px; margin-bottom:3px; line-height:1;">${usada ? '💤' : m.icone}</div>
      <div style="color:${selecionada ? cor : usada ? '#2a2a2a' : '#8a7a5a'}; font-family:'Cinzel',serif; font-size:7px; letter-spacing:0.5px; text-align:center; line-height:1.2; max-width:54px; word-break:break-word;">${m.nome}</div>
      ${selecionada ? `<div style="position:absolute; bottom:2px; width:6px; height:6px; border-radius:50%; background:${cor};"></div>` : ''}
    </div>
  `;
}

// Tooltip da carta — aceita (magiaId, event) [novo] OU (event, magiaId) [chamadas
// antigas de renderAbaMagiasPedro], detectando qual argumento é o id (string).
function mostrarTooltipMagia(a, b) {
  const magiaId = (typeof a === 'string') ? a : b;
  const event   = (typeof a === 'string') ? b : a;
  const m = GRIMORIO_CLIENT[magiaId];
  if (!m) return;

  let tooltip = document.getElementById('tooltip-magia');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'tooltip-magia';
    tooltip.style.cssText = `position:fixed; z-index:999; pointer-events:none; background:rgba(10,8,5,0.98); border:1px solid #c8a951; width:220px; padding:12px 14px; font-family:'Cinzel',serif;`;
    document.body.appendChild(tooltip);
  }

  const corCirculo = _COR_CIRCULO[m.circulo];
  const labelCirculo = _LABEL_CIRCULO[m.circulo];
  tooltip.innerHTML = `
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; padding-bottom:8px; border-bottom:1px solid ${corCirculo}33;">
      <span style="font-size:24px;">${m.icone}</span>
      <div>
        <div style="color:${corCirculo}; font-size:12px; font-weight:bold;">${m.nome}</div>
        <div style="color:#8a7a5a; font-size:9px; letter-spacing:2px;">${labelCirculo}</div>
      </div>
    </div>
    <div style="color:#c8b89a; font-size:10px; line-height:1.7;">${m.descricao}</div>
    <div style="margin-top:8px; padding-top:6px; border-top:1px solid ${corCirculo}22; color:#ff851b; font-size:9px;">${m.custo}</div>
  `;
  tooltip.style.display = 'block';
  document.addEventListener('mousemove', _moverTooltipMagia);
  if (event) _moverTooltipMagia(event);
}

function _moverTooltipMagia(e) {
  const t = document.getElementById('tooltip-magia');
  if (!t || t.style.display === 'none') return;
  let x = e.clientX + 16, y = e.clientY + 16;
  if (x + 240 > window.innerWidth)  x = e.clientX - 240 - 16;
  if (y + 300 > window.innerHeight) y = e.clientY - 300 - 16;
  t.style.left = x + 'px';
  t.style.top  = y + 'px';
}

function ocultarTooltipMagia() {
  const t = document.getElementById('tooltip-magia');
  if (t) t.style.display = 'none';
  document.removeEventListener('mousemove', _moverTooltipMagia);
}

// Magias conhecidas do herói → lista de ids escolhidos pelo jogador.
// Vazio = nenhuma magia disponível (a escolha é obrigatória na criação).
function _magiasConhecidasIds(heroi) {
  const known = heroi && (heroi.magias_conhecidas
    || (Array.isArray(heroi.magiasConhecidas) ? heroi.magiasConhecidas.map(x => x.id || x) : null));
  return Array.isArray(known) ? known : [];
}

// Tabela de slots por nível (espelha SLOTS_POR_NIVEL no server). Mesma p/ as 2 classes.
const SLOTS_POR_NIVEL_CLIENT = {
  1: {primeiro:2, segundo:0, terceiro:0},
  2: {primeiro:3, segundo:0, terceiro:0},
  3: {primeiro:3, segundo:1, terceiro:0},
  4: {primeiro:3, segundo:2, terceiro:0},
  5: {primeiro:3, segundo:2, terceiro:1},
};

// Aba de magias em jogo: cartas por círculo + pips de slot com contagem regressiva.
function renderMagiasFichaEmJogo(heroi, cls) {
  cls = cls || (heroi && heroi.class_id) || 'mage';
  const nivel    = Math.min((heroi && (heroi.level || heroi.nivel)) || 1, 5);
  const known    = _magiasConhecidasIds(heroi);
  const limites  = SLOTS_POR_NIVEL_CLIENT[nivel];
  const cooldown = (heroi && heroi.slots_cooldown) || {primeiro:[], segundo:[], terceiro:[]};
  const round    = (window.GS && GS.gameState && GS.gameState.round) || 0;

  function renderCirculoMagias(circulo, label) {
    const magiasCirculo = known.filter(id => GRIMORIO_CLIENT[id] && GRIMORIO_CLIENT[id].circulo === circulo);
    const limite = limites[circulo] || 0;
    if (limite === 0) return `
      <div style="opacity:0.3; margin-bottom:12px;">
        <div style="color:#4a4a4a; font-size:9px; letter-spacing:2px;">${label} — disponível em nível maior</div>
      </div>`;

    // Contagens regressivas dos slots gastos (menores primeiro).
    const espera = (cooldown[circulo] || []).map(r => Math.max(0, r - round)).sort((a,b) => a - b);
    const livres = Math.max(0, limite - espera.length);

    const pips = Array.from({length: limite}).map((_, i) => {
      if (i < livres) {
        return `<div title="Pronto" style="width:16px; height:16px; border-radius:50%; background:#44cc88; border:1px solid #44cc88;"></div>`;
      }
      const falta = espera[i - livres];   // rodadas até liberar este slot
      return `<div title="Volta em ${falta} rodada(s)" style="width:16px; height:16px; border-radius:50%; background:#1a1a1a; border:1px solid #3a3a3a; display:flex; align-items:center; justify-content:center; color:#cc8844; font-size:9px;">${falta}</div>`;
    }).join('');

    return `
      <div style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="color:#8a7a5a; font-size:9px; letter-spacing:2px;">${label}</span>
          <span style="color:${livres === 0 ? '#ff4136' : '#44cc88'}; font-size:10px;">${livres}/${limite} slots</span>
        </div>
        <div style="display:flex; gap:4px; margin-bottom:8px;">${pips}</div>
        <div style="display:flex; flex-wrap:wrap; gap:4px;">
          ${magiasCirculo.map((id, idx) => criarCartaMagia(id, false, livres > 0, livres === 0, 'jogo')).join('')}
          ${magiasCirculo.length === 0 ? `<div style="color:#4a4a4a; font-size:9px; font-style:italic; padding:8px;">Nenhuma magia memorizada</div>` : ''}
        </div>
      </div>`;
  }

  return `
    <div style="padding:4px 0;">
      ${renderCirculoMagias('primeiro', '1º CÍRCULO')}
      ${renderCirculoMagias('segundo',  '2º CÍRCULO')}
      ${renderCirculoMagias('terceiro', '3º CÍRCULO')}
    </div>`;
}

// Seleção de magias na criação do personagem (helper; persistência fica no
// próximo passo, quando o servidor guardar `magias_conhecidas`).
function renderSelecaoMagias(heroiKey, circulo) {
  const cls    = heroiKey === 'pedro' ? 'mage' : 'cleric';
  const limite = { primeiro:2, segundo:0, terceiro:0 };
  const magiasDisponiveis = Object.values(GRIMORIO_CLIENT).filter(m =>
    m.circulo === circulo && m.classe.includes(cls));
  const selecionadas = (window._magiasSelecionadas && window._magiasSelecionadas[heroiKey]) || [];
  const max = limite[circulo] || 0;
  return `
    <div id="selecao-magias-${heroiKey}">
      <div style="color:#8a7a5a; font-size:9px; letter-spacing:3px; margin-bottom:10px;">ESCOLHA ${max} MAGIA${max > 1 ? 'S' : ''} DE 1º CÍRCULO</div>
      <div style="display:flex; flex-wrap:wrap; gap:2px; margin-bottom:14px;">
        ${magiasDisponiveis.map(m => {
          const sel  = selecionadas.includes(m.id);
          const pode = sel || selecionadas.length < max;
          return criarCartaMagia(m.id, sel, pode, false);
        }).join('')}
      </div>
      <div style="padding:8px 10px; background:rgba(200,169,81,0.05); border:1px solid #c8a95133; color:#8a7a5a; font-size:9px; text-align:center; letter-spacing:1px;">
        ${selecionadas.length}/${max} magias selecionadas
        ${selecionadas.length === max ? ' — <span style="color:#44cc88;">✓ Pronto</span>' : ''}
      </div>
    </div>`;
}

window.selecionarMagia = function(magiaId) {
  const heroiKey = window._heroiAtualSelecao || 'pedro';
  window._magiasSelecionadas = window._magiasSelecionadas || {};
  window._magiasSelecionadas[heroiKey] = window._magiasSelecionadas[heroiKey] || [];
  const lista = window._magiasSelecionadas[heroiKey];
  const max   = 2;
  if (lista.includes(magiaId)) {
    window._magiasSelecionadas[heroiKey] = lista.filter(id => id !== magiaId);
  } else if (lista.length < max) {
    window._magiasSelecionadas[heroiKey].push(magiaId);
  }
  const container = document.getElementById(`selecao-magias-${heroiKey}`);
  if (container) container.outerHTML = renderSelecaoMagias(heroiKey, 'primeiro');
};

window.criarCartaMagia         = criarCartaMagia;
window.mostrarTooltipMagia     = mostrarTooltipMagia;
window.ocultarTooltipMagia     = ocultarTooltipMagia;
window.renderSelecaoMagias     = renderSelecaoMagias;
window.renderMagiasFichaEmJogo = renderMagiasFichaEmJogo;
window.GRIMORIO_CLIENT         = GRIMORIO_CLIENT;

// ─── Lançamento de magia em jogo ─────────────────────────────────────────────
// Clicar uma carta na aba de magias chama castarMagia(). Magias sem alvo no
// tabuleiro são enviadas na hora; as demais entram em modo de mira (window.
// _modoMagia) e o próximo clique numa casa/alvo resolve o alvo e envia `magia`.
// O clique no tabuleiro é capturado em on3DClick (ver hook _modoMagia lá).
const GRIMORIO_IMPLEMENTADAS_CLIENT = new Set([
  'manto_escuridao', 'visao_escuro', 'bola_fogo', 'relampago', 'raio_congelante',
  'saciar', 'criar_alimentos', 'clarividencia', 'raio_divino',
  'abencoar', 'amaldicoar', 'abencoar_arma',
  'sono', 'medo', 'comando', 'dominar_mente', 'dominar_morto_vivo', 'lentidao',
  'invisibilidade', 'regeneracao_magica', 'jato_ar', 'velocidade', 'protecao_energia',
  'conjurar_elemental', 'silencio', 'barreira_arcana', 'contramagica'
]);

function _meVivoNaVez() {
  const me = GS.me;
  if (!me) return null;
  const jogando = GS.gameState && GS.gameState.phase === 'playing';
  if (!(GS.isMyTurn && me.alive && !me.action_done && jogando)) return null;
  return me;
}

function castarMagia(magiaId) {
  const m = GRIMORIO_CLIENT[magiaId];
  if (!m) return;
  const me = _meVivoNaVez();
  if (!me) { toast('Não é a sua vez ou a ação já foi usada.', '#ff6b6b'); return; }
  if (!GRIMORIO_IMPLEMENTADAS_CLIENT.has(magiaId)) {
    toast(`${m.icone} ${m.nome} ainda está em desenvolvimento.`, '#c8a951'); return;
  }
  // Conjurar Elemental: escolhe o tipo (4 elementos) antes de lançar.
  if (magiaId === 'conjurar_elemental') { _abrirPickerElemental(); return; }
  const tipo = m.tipo;
  // Buffs no próprio caster sem área desenhável → lança imediatamente.
  if (['buff_self', 'utilidade', 'reacao', 'invocacao'].includes(tipo)) {
    send({ type: 'magia', magia_id: magiaId });
    toast(`${m.icone} ${m.nome} lançada!`, '#c8a951');
    return;
  }
  // Demais magias entram em modo de mira no tabuleiro (mostram alcance/área).
  let alvoTipo;
  const ehArea = ['area', 'area_fixa', 'area_persistente'].includes(tipo);
  if (tipo === 'area_centrada')                                    alvoTipo = 'self_area'; // área fixa no caster, confirma c/ clique
  else if (ehArea && _alcanceMagiaCli(m, GS.me && GS.me.level) <= 0) alvoTipo = 'self_area'; // ex.: Abençoar (centrada no caster)
  else if (tipo === 'linha_reflexiva')                            alvoTipo = 'linha';
  else if (tipo === 'cone')                                       alvoTipo = 'cone';   // mira por direção
  else if (tipo === 'alvo')                                       alvoTipo = 'foe';
  else if (['alvo_aliado', 'buff_aliado', 'toque'].includes(tipo)) alvoTipo = 'ally';
  else                                                            alvoTipo = 'tile'; // area / area_fixa / area_persistente
  _iniciarModoMagia(magiaId, alvoTipo);
}

// Usa um PERGAMINHO: igual a castarMagia, mas envia `use_scroll` (carrega o id do
// item). A magia guardada é item.magia_id. Só mago/clérigo (servidor revalida).
function castarPergaminho(item) {
  if (!item || item.effect !== 'scroll') return;
  const magiaId = item.magia_id;
  const m = GRIMORIO_CLIENT[magiaId];
  if (!m) { toast('Pergaminho com magia desconhecida.', '#ff6b6b'); return; }
  const me = _meVivoNaVez();
  if (!me) { toast('Não é a sua vez ou a ação já foi usada.', '#ff6b6b'); return; }
  if (me.class_id !== 'mage' && me.class_id !== 'cleric') {
    toast('Apenas mago ou clérigo usam pergaminhos.', '#ff6b6b'); return;
  }
  if (magiaId === 'conjurar_elemental') {
    send({ type: 'use_scroll', item_id: item.id });
    toast(`📜 ${m.nome} (pergaminho)!`, '#c8a951'); return;
  }
  const tipo = m.tipo;
  if (['buff_self', 'utilidade', 'reacao', 'invocacao'].includes(tipo)) {
    send({ type: 'use_scroll', item_id: item.id });
    toast(`📜 ${m.nome} (pergaminho)!`, '#c8a951'); return;
  }
  let alvoTipo;
  const ehArea = ['area', 'area_fixa', 'area_persistente'].includes(tipo);
  if (tipo === 'area_centrada')                                    alvoTipo = 'self_area';
  else if (ehArea && _alcanceMagiaCli(m, me && me.level) <= 0)     alvoTipo = 'self_area';
  else if (tipo === 'linha_reflexiva')                            alvoTipo = 'linha';
  else if (tipo === 'cone')                                       alvoTipo = 'cone';
  else if (tipo === 'alvo')                                       alvoTipo = 'foe';
  else if (['alvo_aliado', 'buff_aliado', 'toque'].includes(tipo)) alvoTipo = 'ally';
  else                                                            alvoTipo = 'tile';
  _iniciarModoMagia(magiaId, alvoTipo, item.id);
}

function _iniciarModoMagia(magiaId, alvoTipo, scrollItemId) {
  const _def = GRIMORIO_CLIENT[magiaId];
  // alvoLivre: a magia mira qualquer casa do mapa, sem limite de alcance e
  // mesmo sob névoa (ex.: Clarividência). Some o anel vermelho de alcance.
  window._modoMagia = { magiaId, alvoTipo, alvoLivre: !!(_def && _def.alvoLivre),
                        scrollItemId: scrollItemId || null };
  // Realce: alcance (vermelho) fixo no caster; área (verde) segue o cursor.
  _recomputarAlcanceMagia();
  if (alvoTipo === 'self_area') _recomputarAreaMagia(null, null); // área fixa no caster
  else window._spellHL.area = new Set();
  _aplicarSpellHL();
  const dicas = {
    foe:       'Clique num INIMIGO',
    ally:      'Clique num ALIADO (ou em você)',
    tile:      'Clique numa CASA (centro da área)',
    linha:     'Clique numa CASA (direção do raio)',
    cone:      'Clique numa CASA (direção do cone)',
    self_area: 'Clique para CONFIRMAR (área em você)'
  };
  if (typeof g3 !== 'undefined' && g3 && g3.renderer) g3.renderer.domElement.style.cursor = 'crosshair';
  let leg = document.getElementById('legenda-magia');
  if (!leg) {
    leg = document.createElement('div');
    leg.id = 'legenda-magia';
    leg.style.cssText = 'position:fixed;bottom:120px;left:50%;transform:translateX(-50%);' +
      "background:rgba(10,8,5,0.92);border:1px solid #c8a951;color:#c8a951;font-family:'Cinzel',serif;" +
      'font-size:11px;letter-spacing:2px;padding:8px 20px;pointer-events:none;z-index:1000;';
    document.body.appendChild(leg);
  }
  const m = GRIMORIO_CLIENT[magiaId];
  leg.innerHTML = `${m.icone} ${m.nome.toUpperCase()} — ${dicas[alvoTipo] || 'Clique no alvo'} &nbsp;|&nbsp; ESC cancela`;
  leg.style.borderColor = '#c8a951';
  leg.style.color       = '#c8a951';
  leg.style.display = 'block';
  document.addEventListener('keydown', _keyMagiaEsc);
}

// Extrai o "spec" de alvo de um clique conforme o tipo de mira. Retorna
// { ok:true, fields:{...} } com os campos do protocolo `magia` (target_id /
// tx,ty / dir), ou { ok:false, msg } se o clique não é um alvo válido.
function _specAlvoMagia(alvoTipo, tx, ty) {
  const me = GS.me;
  const gs = GS.gameState || {};
  if (alvoTipo === 'self_area') return { ok: true, fields: {} };          // centrada no caster
  if (alvoTipo === 'tile')      return { ok: true, fields: { tx, ty } };
  if (alvoTipo === 'linha' || alvoTipo === 'cone') {
    if (!me) return { ok: false };
    const [dx, dy] = _dir8(tx - me.pos[0], ty - me.pos[1]);
    if (dx === 0 && dy === 0) return { ok: false, msg: 'Mire numa direção a partir de você.' };
    return { ok: true, fields: { dir: [dx, dy] } };
  }
  const alvo = (alvoTipo === 'foe')
    ? (gs.monsters || []).find(mm => mm.pos[0] === tx && mm.pos[1] === ty && mm.hp > 0)
    : (gs.players  || []).find(pp => pp.pos[0] === tx && pp.pos[1] === ty && pp.alive);
  if (!alvo) return { ok: false, msg: alvoTipo === 'foe' ? 'Clique num inimigo válido.' : 'Clique num aliado válido.' };
  // Magias de alvo exigem linha de visão — paredes/portas fechadas barram.
  if (me && !GS.hasLineOfSight(gs, me.pos[0], me.pos[1], tx, ty))
    return { ok: false, msg: '🧱 Uma parede bloqueia o feitiço até o alvo!' };
  return { ok: true, fields: { target_id: alvo.id } };
}

function _clickTileMagia(tx, ty) {
  const mode = window._modoMagia;
  if (!mode) return;
  const magiaId = mode.magiaId;
  const m  = GRIMORIO_CLIENT[magiaId];

  const spec = _specAlvoMagia(mode.alvoTipo, tx, ty);
  if (!spec.ok) { if (spec.msg) toast(spec.msg, '#ff6b6b'); return; }

  // Alcance: SÓ a Clarividência (alvoLivre) mira o mapa inteiro. As demais
  // respeitam o alcance original — alvo/centro deve estar dentro do raio
  // (o mesmo anel vermelho). Linha/cone/área-no-caster têm mira própria.
  // Pergaminho: o alcance escala pelo nível MARCADO no item (o servidor valida);
  // por isso pulamos o gate de alcance do cliente quando em modo pergaminho.
  if (!mode.scrollItemId && !mode.alvoLivre &&
      (mode.alvoTipo === 'tile' || mode.alvoTipo === 'foe' || mode.alvoTipo === 'ally')) {
    const me  = GS.me;
    const alc = _alcanceMagiaCli(m, me && me.level);
    if (me && alc > 0) {
      const d = Math.max(Math.abs(me.pos[0] - tx), Math.abs(me.pos[1] - ty));
      if (d > alc) { toast(`🚫 Fora de alcance — máximo ${alc} casa(s).`, '#ff6b6b'); return; }
    }
  }

  if (mode.scrollItemId) {
    send(Object.assign({ type: 'use_scroll', item_id: mode.scrollItemId }, spec.fields));
    toast(`📜 ${m.nome} (pergaminho)!`, '#c8a951');
  } else {
    send(Object.assign({ type: 'magia', magia_id: magiaId }, spec.fields));
    toast(`${m.icone} ${m.nome} lançada!`, '#c8a951');
  }
  _encerrarModoMagia();
}

function _encerrarModoMagia() {
  window._modoMagia = null;
  _limparSpellHLMira();   // remove alcance/área (zonas persistentes permanecem)
  const leg = document.getElementById('legenda-magia');
  if (leg) leg.style.display = 'none';
  if (typeof g3 !== 'undefined' && g3 && g3.renderer) g3.renderer.domElement.style.cursor = 'default';
  document.removeEventListener('keydown', _keyMagiaEsc);
}

function _keyMagiaEsc(e) {
  if (e.key === 'Escape') { _encerrarModoMagia(); toast('Magia cancelada.', '#888'); }
}

window.castarMagia = castarMagia;

// ── Conjurar Elemental: escolha do tipo (4 elementos) ───────────────────────
function _abrirPickerElemental() {
  if (!_meVivoNaVez()) { toast('Não é a sua vez ou a ação já foi usada.', '#ff6b6b'); return; }
  _fecharPickerElemental();
  const box = document.createElement('div');
  box.id = 'picker-elemental';
  box.style.cssText = 'position:fixed;bottom:140px;left:50%;transform:translateX(-50%);' +
    'display:flex;gap:8px;align-items:center;background:rgba(10,8,5,0.96);border:1px solid #c8a951;' +
    "padding:10px 14px;z-index:1001;font-family:'Cinzel',serif;";
  const tipos = [['fogo','🔥','Fogo','HP18·2d6'], ['eletrico','⚡','Elétrico','HP20·1d8'],
                 ['gelo','❄️','Gelo','HP22·1d6'], ['pedra','🪨','Pedra','HP26·1d8']];
  box.innerHTML =
    '<span style="color:#c8a951;font-size:11px;letter-spacing:2px;margin-right:4px;">🌪️ CONJURAR</span>' +
    tipos.map(([id, ic, nm, st]) =>
      `<button onclick="_conjurarElemental('${id}')" title="${st}" style="background:rgba(255,255,255,0.05);` +
      `border:1px solid #c8a95166;color:#e8d8b0;font-family:'Cinzel',serif;font-size:12px;padding:6px 10px;` +
      `cursor:pointer;border-radius:4px;text-align:center;line-height:1.3;">${ic}<br>${nm}</button>`).join('') +
    '<button onclick="_fecharPickerElemental()" style="background:none;border:none;color:#888;cursor:pointer;font-size:15px;margin-left:4px;">✕</button>';
  document.body.appendChild(box);
}
function _conjurarElemental(tipo) {
  send({ type: 'magia', magia_id: 'conjurar_elemental', tipo_elemental: tipo });
  toast('🌪️ Elemental conjurado! Encerre o turno para controlá-lo.', '#c8a951');
  _fecharPickerElemental();
}
function _fecharPickerElemental() {
  const b = document.getElementById('picker-elemental'); if (b) b.remove();
}
window._conjurarElemental    = _conjurarElemental;
window._fecharPickerElemental = _fecharPickerElemental;

// ─── Realce de alcance/área de magia (vermelho = alcance, verde = área) ───────
// Estado global lido pelos dois renderers. range/area = Set de "x,y"; zonas =
// lista persistente {cx,cy,raio} (de game_state.zonas_especiais — Bola de Fogo).
// range=alcance(vermelho), area=efeito(verde), double=atingido 2x(verde escuro), zonas=fogo persistente.
window._spellHL = { range: new Set(), area: new Set(), double: new Set(), zonas: [], escuridao: [], silencio: [] };

function _alcanceMagiaCli(m, level) {
  if (m.alcance_base != null) {
    const lv = level || 1;
    // Silêncio escala 1 a cada 2 níveis; as demais, 1 por nível (a partir do nível 1).
    if (m.id === 'silencio') return m.alcance_base + Math.floor(lv / 2) * (m.alcance_escala || 0);
    return m.alcance_base + (m.alcance_escala || 0) * (lv - 1);
  }
  return (m.alcance != null) ? m.alcance : 0;
}
// Direção 8-way dominante do caster até o cursor (cardinal ou diagonal).
function _dir8(ddx, ddy) {
  if (ddx === 0 && ddy === 0) return [0, 0];
  const ax = Math.abs(ddx), ay = Math.abs(ddy);
  if (ax > ay * 2) return [Math.sign(ddx), 0];
  if (ay > ax * 2) return [0, Math.sign(ddy)];
  return [Math.sign(ddx), Math.sign(ddy)];
}
// Caminho do Relâmpago: gasta `alcance` passos; ao bater em parede/borda inverte a
// direção (ricochete) e continua. Retorna Map "x,y" -> nº de vezes que pisou (1 ou 2+).
function _caminhoRelampagoCli(ox, oy, dx, dy, alcance) {
  const st = GS.gameState;
  const isWall = (x, y) => {
    const row = st && st.tiles && st.tiles[y];
    return !row || row[x] === undefined || row[x] !== TILE_FLOOR;
  };
  const counts = new Map();
  let x = ox, y = oy;
  for (let i = 0; i < alcance; i++) {
    let nx = x + dx, ny = y + dy;
    if (isWall(nx, ny)) {
      dx = -dx; dy = -dy;                 // ricochete
      nx = x + dx; ny = y + dy;
      if (isWall(nx, ny)) break;          // preso
    }
    x = nx; y = ny;
    const k = `${x},${y}`;
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  return counts;
}

// Casas do cone (Jato de Ar) na direção (dx,dy) — espelha _cone_tiles do servidor.
function _coneTilesCli(ox, oy, dx, dy, comp, base) {
  const st = GS.gameState;
  const isWall = (x, y) => {
    const row = st && st.tiles && st.tiles[y];
    return !row || row[x] === undefined || row[x] !== TILE_FLOOR;
  };
  const px = -dy, py = dx, out = new Set();
  for (let k = 1; k <= comp; k++) {
    const cxk = ox + dx * k, cyk = oy + dy * k;
    const hw = Math.max(0, Math.round((k / comp) * (base / 2)));
    for (let o = -hw; o <= hw; o++) {
      const tx = cxk + px * o, ty = cyk + py * o;
      if (!isWall(tx, ty)) out.add(`${tx},${ty}`);
    }
  }
  return out;
}
function _areaRaioMagiaCli(m) {
  if (m.area != null) return m.area;
  return ['area', 'area_persistente', 'area_fixa', 'area_centrada'].includes(m.tipo) ? 2 : 0;
}
// Quadrado de lado `lado` (ex.: 4x4 do Silêncio) — espelha _em_zona_quadrada do servidor.
function _addQuadrado(cx, cy, lado, out) {
  const h = Math.floor(lado / 2);   // 2 para 4x4 → casas cx-1..cx+2
  for (let y = cy - h + 1; y <= cy + h; y++)
    for (let x = cx - h + 1; x <= cx + h; x++)
      out.add(`${x},${y}`);
}
function _addCheb(cx, cy, raio, out) {
  for (let y = cy - raio; y <= cy + raio; y++)
    for (let x = cx - raio; x <= cx + raio; x++)
      if (Math.max(Math.abs(x - cx), Math.abs(y - cy)) <= raio) out.add(`${x},${y}`);
}
function _addLinha(x1, y1, x2, y2, out) {
  const dx = x2 - x1, dy = y2 - y1, steps = Math.max(Math.abs(dx), Math.abs(dy));
  if (steps === 0) { out.add(`${x1},${y1}`); return; }
  for (let i = 0; i <= steps; i++)
    out.add(`${Math.round(x1 + dx * i / steps)},${Math.round(y1 + dy * i / steps)}`);
}

function _recomputarAlcanceMagia() {
  const mode = window._modoMagia; if (!mode) return;
  const m = GRIMORIO_CLIENT[mode.magiaId], me = GS.me;
  const range = new Set();
  // Relâmpago/Jato de Ar não usam círculo vermelho — o trajeto/cone (verde) já mostra o alcance.
  // alvoLivre (Clarividência): sem anel de alcance — pode mirar o mapa inteiro.
  if (m && me && !mode.alvoLivre && mode.alvoTipo !== 'linha' && mode.alvoTipo !== 'cone') {
    const alc = _alcanceMagiaCli(m, me.level);
    if (alc > 0) _addCheb(me.pos[0], me.pos[1], alc, range);
  }
  window._spellHL.range = range;
}

function _recomputarAreaMagia(hx, hy) {
  const mode = window._modoMagia; if (!mode) return;
  const m = GRIMORIO_CLIENT[mode.magiaId], me = GS.me;
  const area = new Set(), dbl = new Set();
  if (m && me) {
    if (mode.alvoTipo === 'self_area') {
      _addCheb(me.pos[0], me.pos[1], _areaRaioMagiaCli(m), area);
    } else if (mode.alvoTipo === 'linha' && hx != null && hy != null) {
      // Relâmpago: caminho com ricochete; pisado 1x = verde claro, 2x = verde escuro.
      const [dx, dy] = _dir8(hx - me.pos[0], hy - me.pos[1]);
      mode.dir = [dx, dy];
      if (dx !== 0 || dy !== 0) {
        const alc = _alcanceMagiaCli(m, me.level);
        for (const [k, c] of _caminhoRelampagoCli(me.pos[0], me.pos[1], dx, dy, alc)) {
          if (c >= 2) dbl.add(k); else area.add(k);
        }
      }
    } else if (mode.alvoTipo === 'cone' && hx != null && hy != null) {
      // Jato de Ar: cone na direção do cursor (verde).
      const [dx, dy] = _dir8(hx - me.pos[0], hy - me.pos[1]);
      mode.dir = [dx, dy];
      if (dx !== 0 || dy !== 0) {
        for (const k of _coneTilesCli(me.pos[0], me.pos[1], dx, dy, m.comprimento || 4, m.base || 4)) area.add(k);
      }
    } else if (hx != null && hy != null) {
      if (mode.alvoTipo === 'tile' && m.area_lado)  _addQuadrado(hx, hy, m.area_lado, area); // Silêncio 4x4
      else if (mode.alvoTipo === 'tile')            _addCheb(hx, hy, _areaRaioMagiaCli(m), area);
      else                                          area.add(`${hx},${hy}`); // foe / ally
    }
  }
  window._spellHL.area   = area;
  window._spellHL.double = dbl;
  _aplicarSpellHL();
}

// Apenas dados (sem redraw) — chamado de dentro de renderMap/renderMap3D.
function _atualizarZonasMagia(state) {
  const zz = ((state && state.zonas_especiais) || []);
  window._spellHL.zonas     = zz.filter(z => z.ativa && z.tipo === 'bola_fogo')
                                .map(z => ({ cx: z.cx, cy: z.cy, raio: z.raio || 2 }));
  window._spellHL.escuridao = zz.filter(z => z.ativa && z.tipo === 'escuridao')
                                .map(z => ({ cx: z.cx, cy: z.cy, raio: z.raio || 3 }));
  window._spellHL.silencio  = zz.filter(z => z.ativa && z.tipo === 'silencio')
                                .map(z => ({ cx: z.cx, cy: z.cy, lado: z.lado || 4 }));
}

function _aplicarSpellHL() {
  if (mode3D) _aplicarSpellHL3D();
  else if (GS.gameState) renderMap(GS.gameState);   // 2D: redesenha (overlay lê _spellHL)
}

function _aplicarSpellHL3D() {
  if (typeof g3 === 'undefined' || !g3) return;
  const hl = window._spellHL || { range: new Set(), area: new Set(), zonas: [] };
  const zonaSet = new Set();
  for (const z of hl.zonas) _addCheb(z.cx, z.cy, z.raio, zonaSet);
  const escSet = new Set();
  for (const z of (hl.escuridao || [])) _addCheb(z.cx, z.cy, z.raio, escSet);
  const silSet = new Set();
  for (const z of (hl.silencio || [])) _addQuadrado(z.cx, z.cy, z.lado, silSet);
  const toggle = (dict, keys) => { if (!dict) return; for (const k in dict) dict[k].visible = keys.has(k); };
  toggle(g3.spellEscuridaoMeshes, escSet);   // névoa escura (no chão, sob os peões)
  toggle(g3.spellSilencioMeshes,  silSet);   // véu de silêncio
  toggle(g3.spellRangeMeshes,  hl.range);
  toggle(g3.spellZonaMeshes,   zonaSet);
  toggle(g3.spellDoubleMeshes, hl.double || new Set());  // verde escuro (atingido 2x)
  toggle(g3.spellAreaMeshes,   hl.area);                 // verde claro por último (por cima)
}

function _limparSpellHLMira() {
  window._spellHL.range  = new Set();
  window._spellHL.area   = new Set();
  window._spellHL.double = new Set();
  _aplicarSpellHL();
}

// Desenho do realce no canvas 2D (chamado por renderMap após o passe de chão).
function _desenharSpellHL2D(ctx, exploredSet) {
  const hl = window._spellHL || { range: new Set(), area: new Set(), zonas: [] };
  const draw = (key, color) => {
    if (exploredSet && !exploredSet.has(key)) return;
    const c = key.split(',');
    ctx.fillStyle = color;
    ctx.fillRect(+c[0] * CELL, +c[1] * CELL, CELL, CELL);
  };
  // Névoa escura (Manto de Escuridão) — desenhada no chão; personagens/monstros ficam por cima.
  const escSet = new Set();
  for (const z of (hl.escuridao || [])) _addCheb(z.cx, z.cy, z.raio, escSet);
  for (const k of escSet) draw(k, 'rgba(10,6,26,0.62)');
  // Silêncio 4x4 — véu azul-acinzentado suave.
  const silSet = new Set();
  for (const z of (hl.silencio || [])) _addQuadrado(z.cx, z.cy, z.lado, silSet);
  for (const k of silSet) draw(k, 'rgba(120,140,200,0.26)');
  for (const k of hl.range) draw(k, 'rgba(255,40,40,0.22)');     // alcance — vermelho
  const zonaSet = new Set();                                     // zona de fogo persistente — laranja
  for (const z of hl.zonas) _addCheb(z.cx, z.cy, z.raio, zonaSet);
  for (const k of zonaSet) draw(k, 'rgba(255,110,0,0.32)');
  for (const k of (hl.double || [])) draw(k, 'rgba(8,90,25,0.62)'); // atingido 2x — verde escuro
  for (const k of hl.area) draw(k, 'rgba(40,230,70,0.34)');      // área de efeito — verde (por cima)
}

// Lewis (cleric): aba de magias = cartas do grimório por círculo.
function renderAbaMagiasLewis(me){
  return `
    <div style="color:#8a7a5a;font-size:9px;letter-spacing:3px;margin-bottom:10px;">📜 MAGIAS DO DIA</div>
    ${renderMagiasFichaEmJogo(me, 'cleric')}`;
}

// Habilidades especiais de cada elemental (espelha o campo `especial` em
// _executar_conjurar_elemental, server.py). Exibidas na ficha do elemental.
const _ELEMENTAL_HABILIDADES_LEWIS = {
  fogo:     { cor:'#ff6b3d', label:'Explosão Ígnea',    desc:'Ao detonar, causa 6d6 de fogo em área (atinge aliados também).' },
  eletrico: { cor:'#5db8ff', label:'Descarga em Linha', desc:'Seu ataque atinge todos numa linha reta de 3 quadrados.' },
  gelo:     { cor:'#7fe0ff', label:'Corpo Glacial',     desc:'Recebe -2 de dano físico, porém +2 de dano de fogo.' },
  pedra:    { cor:'#caa472', label:'Pele de Pedra',     desc:'Reduz à metade todo o dano físico que recebe.' },
};

// Ficha dos elementais conjurados pelo Lewis (mesmo padrão da ficha do Pedro:
// card com HP/CA/dano/movimento + a habilidade especial do elemental). Lê
// me.animados (os elementais entram nessa lista no servidor). '' se não houver.
function renderElementaisLewis(me){
  const elementais = (me.animados || []).filter(a => a && (a.tipo === 'elemental' || a.tipo_elemental));
  if(!elementais.length) return '';
  return `
    <div style="margin-bottom:18px;">
      <div style="display:flex;justify-content:space-between;color:#8a7a5a;font-size:9px;letter-spacing:3px;margin-bottom:10px;">
        <span>🌪️ ELEMENTAIS CONJURADOS</span>
        <span style="color:#44cc88;">${elementais.length}</span>
      </div>
      <div style="color:#8a7a5a;font-size:9px;line-height:1.5;margin-bottom:10px;font-style:italic;">
        Agem após Lewis — encerre o turno para abrir a janela de controle e mover/atacar com cada elemental.
      </div>
      ${GS.gameState?.animados_turn === GS.myPid ? `
        <button onclick="usarComandarAnimados()" style="
          width:100%;margin-bottom:10px;padding:7px;
          background:rgba(68,204,136,0.18);border:1px solid #44cc88aa;
          color:#44cc88;font-family:'Cinzel',serif;font-size:10px;
          letter-spacing:2px;cursor:pointer;">⚔️ AUTO-COMANDAR TODOS OS ELEMENTAIS</button>
      ` : ''}
      ${elementais.map(a => {
        const tipo = a.tipo_elemental || 'pedra';
        const hab  = _ELEMENTAL_HABILIDADES_LEWIS[tipo] || { cor:'#44cc88', label:'Elemental', desc:'' };
        const pct  = Math.max(0, Math.min(100, (a.vida_atual / Math.max(1, a.vida_max)) * 100));
        const corVida = pct > 60 ? '#2ecc40' : pct > 30 ? '#ff851b' : '#ff4136';
        return `
          <div
            onmouseenter="mostrarTooltipAnimado(event, '${a.id}', ${JSON.stringify(a).replace(/"/g, '&quot;')})"
            onmouseleave="esconderTooltip()"
            style="padding:10px 12px;margin-bottom:6px;background:rgba(68,204,136,0.05);border:1px solid #44cc8833;cursor:default;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
              <div style="font-size:22px;min-width:28px;text-align:center;">${a.icone}</div>
              <div style="flex:1;">
                <div style="color:#c8b89a;font-family:'Cinzel',serif;font-size:11px;margin-bottom:4px;">${a.nome}</div>
                <div style="height:4px;background:#1a1a1a;border:1px solid #2a2a2a;margin-bottom:3px;">
                  <div style="width:${pct}%;height:100%;background:${corVida};"></div>
                </div>
                <div style="color:#8a7a5a;font-size:9px;">❤️ ${a.vida_atual}/${a.vida_max}</div>
              </div>
              <div style="color:#44cc88;font-size:9px;letter-spacing:1px;text-align:right;line-height:1.6;">🛡️ CA ${a.ca}<br>🎲 ${a.dano}<br>👣 ${a.movimento}q</div>
            </div>
            <div style="padding:6px 8px;background:rgba(0,0,0,0.25);border-left:2px solid ${hab.cor};">
              <div style="color:${hab.cor};font-size:9px;letter-spacing:2px;margin-bottom:2px;">✦ ${hab.label.toUpperCase()}</div>
              <div style="color:#c8b89a;font-size:9px;line-height:1.5;">${hab.desc}</div>
            </div>
          </div>`;
      }).join('')}
    </div>`;
}

window.abrirPainelCura          = abrirPainelCura;
window.abrirPainelCuraArea      = abrirPainelCuraArea;
window.iniciarModoPurificacao   = iniciarModoPurificacao;
window.iniciarModoRessurreicao  = iniciarModoRessurreicao;
window.renderAbaMagiasLewis     = renderAbaMagiasLewis;
window.renderElementaisLewis    = renderElementaisLewis;

function renderMyPanel(state){
  const me = state.players.find(p => p.id === GS.myPid);
  if(!me) return;

  const pFrame = document.getElementById('my-hero-portrait');
  const pImg   = document.getElementById('my-hero-portrait-img');
  if(pFrame && pImg){
    const portraitSrc = HERO_PORTRAIT_PATHS[me.class_id]
                     || (_CSD && _CSD[me.class_id]?.portrait)
                     || null;
    if(portraitSrc){
      pImg.src = portraitSrc;
      pFrame.classList.add('visible');
      pImg.onerror = () => pFrame.classList.remove('visible');
    } else {
      pFrame.classList.remove('visible');
      pImg.src = '';
    }
  }
  const canAct = GS.isMyTurn && me.alive && !me.action_done && state.phase === 'playing';

  // ── Bônus da Canção Heroica (Henrique): indicador azul ao lado do atributo ──
  // O servidor injeta `buffs_cancao` (ex.: {bonus_ca:1, bonus_mov:1}) nos aliados
  // no raio. Aqui só EXIBIMOS — a aplicação mecânica já é feita no server.
  const _cb = me.buffs_cancao || {};
  const _cancaoTag = (key) => _cb[key]
    ? ` <span style="color:#4db8ff;font-weight:bold;font-size:.78em;vertical-align:top;" title="Canção Heroica de Henrique">🎵+${_cb[key]}</span>`
    : '';

  // ── Bônus do Guerreiro da Luz (Richard): indicador AMARELO ao lado do atributo ──
  // O servidor aplica os bônus na resolução (CA/ataque/dano), não no valor exibido —
  // por isso mostramos como tag aditiva, ao lado da tag azul da Canção quando ambos
  // estiverem ativos. Naturalmente só aparece no paladino (campos só existem nele).
  const _glAtivo = !!me.guerreiro_luz_ativo;
  const _glBonus = me.guerreiro_luz_bonus || {};
  const _richardTag = (key) => (_glAtivo && _glBonus[key])
    ? ` <span style="color:#f8d040;font-weight:bold;font-size:.78em;vertical-align:top;" title="Guerreiro da Luz de Richard">💡+${_glBonus[key]}</span>`
    : '';
  // Golpe Sagrado: +1d8 sagrado por ataque (buff sustentado) — tag amarela no dano.
  const _golpeSagradoTag = () => me.golpe_sagrado_ativo
    ? ` <span style="color:#f8d040;font-weight:bold;font-size:.78em;vertical-align:top;" title="Golpe Sagrado de Richard (+1d8 sagrado por ataque)">⚔️+1d8</span>`
    : '';

  // ── Attribute values (explicit Number conversion — never undefined) ──
  const vStr  = (me.str_  != null) ? Number(me.str_)  : 10;
  const vDex  = (me.dex   != null) ? Number(me.dex)   : 10;
  const vCon  = (me.con_  != null) ? Number(me.con_)  : 10;
  const vInt  = (me.int_  != null) ? Number(me.int_)  : 10;
  const vAc   = (me.ac    != null) ? Number(me.ac)    : 10;
  const vAtk  = (me.atk_bonus != null) ? me.atk_bonus : 0;
  const vFort = (me.fort  != null) ? me.fort  : 0;
  const vRef  = (me.ref_  != null) ? me.ref_  : 0;
  const vWill = (me.will  != null) ? me.will  : 0;
  const vLvlBonus = (me.level_bonus != null) ? Number(me.level_bonus) : (me.level || 1);

  // ── Weapon info ──
  const weapon = (me.weapon && typeof me.weapon === 'object') ? me.weapon : null;
  const STAT_LABEL = {str_:'FOR', dex:'DES', con_:'CON', int_:'INT'};
  const wStat = weapon ? weapon.stat : 'str_';
  const wStatVal = (me[wStat] != null) ? Number(me[wStat]) : 10;
  const wMod = Math.floor((wStatVal - 10) / 2);
  const wModStr = (wMod >= 0 ? '+' : '') + wMod;
  let dmgFmt = '—';
  if(weapon && weapon.die){
    const sl = STAT_LABEL[wStat] || 'FOR';
    dmgFmt = `${weapon.die} ${wModStr} (${sl})`;
  } else {
    const strM = Math.floor((vStr - 10) / 2);
    dmgFmt = `1 ${strM >= 0 ? '+' : ''}${strM} (FOR)`;
  }

  // ── Damage label for attack button (use weapon's actual stat — DEX for crossbow, STR for melee) ──
  const atkWStatKey  = weapon ? (weapon.stat || 'str_') : 'str_';
  const atkWStatScore = (me[atkWStatKey] != null) ? Number(me[atkWStatKey]) : 10;
  const atkWMod = Math.floor((atkWStatScore - 10) / 2);
  const atkDieStr = weapon && weapon.die ? weapon.die : '1';
  const atkModStr = (atkWMod >= 0 ? '+' : '') + atkWMod;

  // ── Armor info ──
  const armorDef = CLASS_ARMOR[me.class_id] || {id:'none', name:'Sem Armadura'};
  const equippedArmor = me.gear && me.gear.armor;
  const armorId   = equippedArmor ? (equippedArmor.id || 'none') : armorDef.id;
  const armorName = equippedArmor ? equippedArmor.name : armorDef.name;

  // ── Build HTML ──
  const statsHTML = `
    <div class="ability-grid">
      <div class="ability-box">
        <span class="ability-label">Força</span>
        <span class="ability-score" style="color:#e8dfc8;font-size:1.2rem;">${vStr}</span>
        <span class="ability-mod">${(Math.floor((vStr-10)/2)>=0?'+':'')}${Math.floor((vStr-10)/2)}</span>
      </div>
      <div class="ability-box">
        <span class="ability-label">Destreza</span>
        <span class="ability-score" style="color:#e8dfc8;font-size:1.2rem;">${vDex}</span>
        <span class="ability-mod">${(Math.floor((vDex-10)/2)>=0?'+':'')}${Math.floor((vDex-10)/2)}</span>
      </div>
      <div class="ability-box">
        <span class="ability-label">Constituição</span>
        <span class="ability-score" style="color:#e8dfc8;font-size:1.2rem;">${vCon}</span>
        <span class="ability-mod">${(Math.floor((vCon-10)/2)>=0?'+':'')}${Math.floor((vCon-10)/2)}</span>
      </div>
      <div class="ability-box">
        <span class="ability-label">Inteligência</span>
        <span class="ability-score" style="color:#e8dfc8;font-size:1.2rem;">${vInt}</span>
        <span class="ability-mod">${(Math.floor((vInt-10)/2)>=0?'+':'')}${Math.floor((vInt-10)/2)}</span>
      </div>
    </div>

    <div class="combat-row">
      <div class="combat-chip" style="border-color:var(--gold);background:#181200;">
        <span class="cl">CA</span>
        <b style="color:#f8d040;font-size:1.1rem;">${vAc}${_cancaoTag('bonus_ca')}${_richardTag('ca')}</b>
      </div>
      <div class="combat-chip">
        <span class="cl">Ataque</span>
        <b style="color:#e8e0c8;">${vAtk >= 0 ? '+' : ''}${vAtk}${_cancaoTag('bonus_acerto')}${_richardTag('ataque')}</b>
      </div>
      <div class="combat-chip">
        <span class="cl">Mov</span>
        <b style="color:#e8e0c8;">${me.moves_left ?? 0}/${me.spd ?? 0}${_cancaoTag('bonus_mov')}</b>
      </div>
    </div>
    <div class="combat-row">
      <div class="combat-chip" style="border-color:var(--purple);background:#0e0820;flex:2;">
        <span class="cl">Bônus de Nível</span>
        <b style="color:#c080ff;">+${vLvlBonus}</b>
      </div>
      <div class="combat-chip">
        <span class="cl">Nível</span>
        <b style="color:#e8e0c8;">${me.level ?? 1}</b>
      </div>
      <div class="combat-chip">
        <span class="cl">XP</span>
        <b style="color:#e8e0c8;">${me.xp ?? 0}</b>
      </div>
    </div>

    <div class="save-row">
      <div class="save-box" style="border-color:var(--orange)">
        <span class="sv" style="color:var(--orange)">Fort</span>
        <span class="sv-val" style="color:#f8d040;">${vFort >= 0 ? '+' : ''}${vFort}${_cancaoTag('bonus_res')}</span>
        <span class="sv-sub">venenos</span>
      </div>
      <div class="save-box" style="border-color:var(--teal)">
        <span class="sv" style="color:var(--teal)">Ref</span>
        <span class="sv-val" style="color:#f8d040;">${vRef >= 0 ? '+' : ''}${vRef}${_cancaoTag('bonus_res')}</span>
        <span class="sv-sub">área/arm.</span>
      </div>
      <div class="save-box" style="border-color:var(--purple)">
        <span class="sv" style="color:var(--purple)">Von</span>
        <span class="sv-val" style="color:#f8d040;">${vWill >= 0 ? '+' : ''}${vWill}${_cancaoTag('bonus_res')}</span>
        <span class="sv-sub">magia</span>
      </div>
    </div>

    <div class="save-row" style="margin-top:4px;">
      <div class="save-box" style="border-color:#b8601a; min-width:60px;">
        <span class="sv" style="color:#e07820;">🍖</span>
        <span class="sv-val" style="color:${(me.fome??100)<=30?'#e05050':'#f8d040'};">${me.fome??100}/100</span>
        <span class="sv-sub">fome</span>
      </div>
      <div class="save-box" style="border-color:#1a60b8; min-width:60px;">
        <span class="sv" style="color:#2090e0;">💧</span>
        <span class="sv-val" style="color:${(me.sede??100)<=30?'#e05050':'#f8d040'};">${me.sede??100}/100</span>
        <span class="sv-sub">sede</span>
      </div>
      <div class="save-box" style="border-color:${me.bonus_action_used?'#555':'#c8a951'}; min-width:60px;">
        <span class="sv" style="color:${me.bonus_action_used?'#666':'#c8a951'};">🎯</span>
        <span class="sv-val" style="color:${me.bonus_action_used?'#666':'#c8a951'}; font-size:.72rem;">${me.bonus_action_used?'usada':'livre'}</span>
        <span class="sv-sub">bônus</span>
      </div>
    </div>
    ${me.regeneracao_ativa ? `
    <div style="margin-top:4px; padding:5px 8px; background:rgba(248,208,64,0.12); border:1px solid #f8d04066; border-radius:3px; display:flex; align-items:center; justify-content:center; gap:8px; font-family:'Cinzel',serif;">
      <span style="color:#f8d040; font-weight:bold; font-size:.95rem;">✨ +1 HP</span>
      <span style="color:#e8d8a0; font-size:.6rem; letter-spacing:1px;">REGENERAÇÃO DIVINA: +1 HP por turno</span>
    </div>` : ''}

    ${(() => {
      const f = me.fome ?? 100, s = me.sede ?? 100;
      // BÔNUS: +1 só quando fome E sede > 80 (saciado).
      if (f > 80 && s > 80) {
        return `<div style="margin-top:4px; padding:5px 8px; background:rgba(80,200,120,0.12); border:1px solid #50c87866; border-radius:3px; display:flex; align-items:center; justify-content:center; gap:8px; font-family:'Cinzel',serif;">
          <span style="color:#6bffa0; font-weight:bold; font-size:.95rem;">✦ +1</span>
          <span style="color:#a0e8c0; font-size:.6rem; letter-spacing:1px;">SACIADO (fome e sede &gt;80): acerto · resistência · dano</span>
        </div>`;
      }
      // PENALIDADE: -1 por fome/sede < 20 (somam).
      const pf = f < 20 ? 1 : 0, ps = s < 20 ? 1 : 0;
      const pen = pf + ps;
      if (pen) {
        const causas = [pf ? 'fome' : '', ps ? 'sede' : ''].filter(Boolean).join(' + ');
        return `<div style="margin-top:4px; padding:5px 8px; background:rgba(224,80,80,0.12); border:1px solid #e0505066; border-radius:3px; display:flex; align-items:center; justify-content:center; gap:8px; font-family:'Cinzel',serif;">
          <span style="color:#ff6b6b; font-weight:bold; font-size:.95rem;">⚠️ −${pen}</span>
          <span style="color:#e8a0a0; font-size:.6rem; letter-spacing:1px;">EXAUSTÃO (${causas} &lt;20): acerto · resistência · dano</span>
        </div>`;
      }
      return '';
    })()}

    <div class="equip-row">
      <div class="equip-item" style="position:relative;">
        <div class="gear-slot-label" style="align-self:flex-start;margin-bottom:2px;">⚔ ARMA</div>
        <canvas id="weapon-canvas" width="60" height="92" style="background:#0e0c1a;border-radius:3px;width:60px;height:92px;"></canvas>
        <div class="equip-name" style="color:#e8e0c8;font-weight:bold;">${weapon ? weapon.name : 'Desarmado'}</div>
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">${dmgFmt}${_cancaoTag('bonus_dano')}${_richardTag('dano')}${_golpeSagradoTag()}</div>
      </div>
      <div class="equip-item" style="position:relative;">
        <div class="gear-slot-label" style="align-self:flex-start;margin-bottom:2px;">🛡 ARMADURA</div>
        <canvas id="armor-canvas" width="60" height="92" style="background:#0e0c1a;border-radius:3px;width:60px;height:92px;"></canvas>
        <div class="equip-name" style="color:#e8e0c8;font-weight:bold;">${armorName}</div>
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">CA ${vAc}</div>
      </div>
    </div>
  `;

  // Pedro: painel principal É a ficha com abas Atributos/Magias (ficha completa
  // inline — sem opção extra de overlay). Demais heróis: só os atributos.
  if (me.class_id === 'mage') {
    const ATV = '#c8a951', INA = '#8a7a5a';
    const aba = (_painelAbaPedro === 'magias') ? 'magias' : 'atributos';
    const abasHTML = `
      <div style="display:flex; border-bottom:1px solid #c8a95133; margin-bottom:8px;">
        <button onclick="trocarAbaPainel('atributos')" style="flex:1;padding:6px;background:transparent;border:none;border-bottom:2px solid ${aba==='atributos'?ATV:'transparent'};color:${aba==='atributos'?ATV:INA};font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">📊 ATRIBUTOS</button>
        <button onclick="trocarAbaPainel('magias')" style="flex:1;padding:6px;background:transparent;border:none;border-bottom:2px solid ${aba==='magias'?ATV:'transparent'};color:${aba==='magias'?ATV:INA};font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">💀 MAGIAS</button>
      </div>`;
    // Sincroniza animados autoritativos (me.animados) no registro do Pedro p/ a aba Magias.
    const heroiPedro = HERO_DATA.pedro;
    if (Array.isArray(me.animados)) heroiPedro.animados = me.animados;
    // Enxerta os campos autoritativos do sistema de magias (como os animados acima):
    // sem isto, renderMagiasFichaEmJogo recebe o objeto estático sem magias conhecidas
    // e nenhuma carta aparece (bug do Pedro vs Lewis, que passa `me` direto).
    heroiPedro.magias_conhecidas = me.magias_conhecidas || [];
    heroiPedro.slots_cooldown    = me.slots_cooldown || {primeiro:[], segundo:[], terceiro:[]};
    heroiPedro.level             = me.level;
    const corpo = (aba === 'magias') ? renderAbaMagiasPedro(heroiPedro) : statsHTML;
    $('my-stats').innerHTML = abasHTML + corpo;
  } else if (me.class_id === 'cleric') {
    // Lewis: mesmo padrão de ficha do Pedro (abas), com aba extra de MAGIAS.
    const ATV = '#44cc88', INA = '#8a7a5a';
    const aba = (_painelAbaPedro === 'magias') ? 'magias' : 'atributos';
    const abasHTML = `
      <div style="display:flex; border-bottom:1px solid #44cc8833; margin-bottom:8px;">
        <button onclick="trocarAbaPainel('atributos')" style="flex:1;padding:6px;background:transparent;border:none;border-bottom:2px solid ${aba==='atributos'?ATV:'transparent'};color:${aba==='atributos'?ATV:INA};font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">📊 ATRIBUTOS</button>
        <button onclick="trocarAbaPainel('magias')" style="flex:1;padding:6px;background:transparent;border:none;border-bottom:2px solid ${aba==='magias'?ATV:'transparent'};color:${aba==='magias'?ATV:INA};font-family:'Cinzel',serif;font-size:10px;letter-spacing:2px;cursor:pointer;">✨ MAGIAS</button>
      </div>`;
    const corpo = (aba === 'magias')
      ? (renderElementaisLewis(me) + renderMagiasFichaEmJogo(me, 'cleric'))
      : statsHTML;
    $('my-stats').innerHTML = abasHTML + corpo;
  } else {
    $('my-stats').innerHTML = statsHTML;
  }

  // ── Draw weapon & armor icons (hi-DPI + scaled to fill larger canvas) ──
  const _capWId = weapon ? weapon.id : 'unarmed';
  const _capAId = armorId;
  requestAnimationFrame(() => {
    function drawEquipCanvas(id, drawFn){
      const c = document.getElementById(id);
      if(!c) return;
      try{
        const dpr = window.devicePixelRatio || 1;
        const cssW = 60, cssH = 92;
        const sc = (cssH / 68) * dpr; // scale to fill + DPR sharpness
        c.width  = Math.round(cssW * dpr);
        c.height = Math.round(cssH * dpr);
        c.style.width  = cssW + 'px';
        c.style.height = cssH + 'px';
        const cx2 = c.getContext('2d');
        cx2.clearRect(0, 0, c.width, c.height);
        // Origin at canvas centre, scaled for sharpness
        cx2.setTransform(sc, 0, 0, sc,
          Math.round(cssW / 2 * dpr),
          Math.round(cssH / 2 * dpr));
        drawFn(cx2);
      }catch(e){}
    }
    drawEquipCanvas('weapon-canvas', cx2 => drawWeapon(cx2, _capWId, 0, 0));
    drawEquipCanvas('armor-canvas',  cx2 => drawArmor(cx2,  _capAId, 0, 0));
  });

  // ── Check for attackable monsters (ranged: Chebyshev≤range; melee: cardinal adjacent) ──
  const _pp = me.pos || [0,0];
  const _wRange = weapon ? weapon.range : null;  // undefined for melee
  const _adjMonsters = (GS.gameState ? GS.gameState.monsters : []).filter(m=>{
    if(!m || m.hp <= 0) return false;
    const dx = Math.abs(_pp[0] - m.pos[0]);
    const dy = Math.abs(_pp[1] - m.pos[1]);
    if(_wRange != null) return Math.max(dx, dy) <= _wRange;   // ranged
    return (dx===1 && dy===0) || (dx===0 && dy===1);           // melee: cardinal only
  });
  const canAttack = canAct && _adjMonsters.length > 0;

  // ── Arremesso: UM botão por arma arremessável equipada (adaga / lança curta) ──
  // Cada botão arremessa o SEU slot (mão principal ou 2ª mão). Arremesso usa DES.
  const _throwWeapons = [];
  if(me.weapon && me.weapon.throw_range)
    _throwWeapons.push({slot:'weapon', item:me.weapon, hand:'mão principal'});
  if(me.gear && me.gear.off_hand && me.gear.off_hand.throw_range)
    _throwWeapons.push({slot:'off_hand', item:me.gear.off_hand, hand:'2ª mão'});
  const _throwBtns = _throwWeapons.map(tw=>{
    const tr = tw.item.throw_range;
    const tgts = (GS.gameState ? GS.gameState.monsters : []).filter(m=>
      m && m.hp>0 && Math.max(Math.abs(_pp[0]-m.pos[0]), Math.abs(_pp[1]-m.pos[1])) <= tr);
    const can = canAct && tgts.length>0;
    const die = tw.item.die || '1d4';
    return `<button class="btn-action" ${can?'':'disabled'} onclick="beginThrowSlot('${tw.slot}')"
      style="display:flex;flex-direction:column;align-items:center;gap:1px;padding:8px 6px;border-color:#ffaa00;">
      <span style="color:#ffc96b;">🎯 Arremessar ${tw.item.name}</span>
      <small style="color:var(--gold);font-size:.7rem;font-weight:bold;">${die} +DES dano</small>
      <small style="color:var(--text2);font-size:.62rem;">${tw.hand} · alcance ${tr} · perde a arma</small>
      ${canAct && !can ? '<small style="color:#e07060;display:block;font-size:.62rem;margin-top:2px;">nenhum alvo no alcance</small>' : ''}
    </button>`;
  }).join('');

  // ── Action buttons (with weapon damage formula shown) ──
  const _rangeHint = _wRange != null ? `alcance ${_wRange}` : 'corpo a corpo';
  const _adjHint = canAct && !canAttack
    ? `<small style="color:#e07060;display:block;font-size:.62rem;margin-top:2px;">${_wRange!=null?'inimigo fora de alcance':'aproxime-se!'}</small>`
    : '';
  $('action-btns').innerHTML = `
    <button class="btn-action" ${canAttack ? '' : 'disabled'} onclick="beginAttack()"
      style="display:flex;flex-direction:column;align-items:center;gap:1px;padding:8px 6px;">
      <span>${_wRange!=null?'🏹':'⚔'} Atacar</span>
      <small style="color:var(--gold);font-size:.7rem;font-weight:bold;">${atkDieStr}${atkModStr} dano${_cancaoTag('bonus_dano')}${_richardTag('dano')}${_golpeSagradoTag()}</small>
      <small style="color:var(--text2);font-size:.62rem;">${_rangeHint}</small>
      ${_adjHint}
    </button>
    ${_throwBtns}
  `;

  const sl = $('skills-list'); sl.innerHTML = '';
  // Acessos defensivos ao GS (resiliência a gameState.js desatualizado/cacheado:
  // um GS sem essas funções NÃO pode mais derrubar o painel + botão de turno).
  const _wSel   = (id) => !!(GS.isWarriorSkillSelected && GS.isWarriorSkillSelected(id));
  const _wToggle = (id) => { if (GS.toggleWarriorSkill) GS.toggleWarriorSkill(id); };

  for(const sk of (me.skills || [])){
    // ── Bardo (Henrique): botões dedicados (canção/provocação), fora do fluxo
    // genérico de toggle/MP — ver _bardSkillBtn. ───────────────────────────────
    if(me.class_id === 'bard' && (sk.id === 'cancao_heroica' || sk.id === 'provocacao')){
      sl.appendChild(_bardSkillBtn(me, sk));
      continue;
    }
    // ── Paladino (Richard): botões dedicados (ações livres/bônus/principal),
    // fora do fluxo genérico de toggle/MP — ver _paladinSkillBtn. ──────────────
    if(me.class_id === 'paladin'){
      sl.appendChild(_paladinSkillBtn(me, sk));
      continue;
    }
    // ── Ladino (Luccas): botões dedicados (furtivo/detectar/sombras/veneno/
    // armadilha), fora do fluxo genérico de toggle/MP — ver _rogueSkillBtn. ────
    if(me.class_id === 'rogue'){
      sl.appendChild(_rogueSkillBtn(me, sk));
      continue;
    }
    // ── Frade Lewis (cleric): milagres dedicados (cura/área/purificação/
    // ressurreição), fora do fluxo genérico de toggle/MP — ver _clericSkillBtn. ──
    if(me.class_id === 'cleric'){
      sl.appendChild(_clericSkillBtn(me, sk));
      continue;
    }
    // ── Mago (Pedro): metamagia (ações livres que modificam a próxima magia) —
    // botões dedicados (toggle/painel), fora do fluxo genérico de MP. ──────────
    if(me.class_id === 'mage' &&
       (sk.id === 'aprimorar_magia' || sk.id === 'estender_magia' || sk.id === 'fortalecer_magia')){
      sl.appendChild(_mageSkillBtn(me, sk));
      continue;
    }
    // Mago (Pedro): magias com custo de MP foram removidas da ficha.
    if (me.class_id === 'mage' && sk.mp != null) continue;

    // Duas famílias de habilidade: MP (demais classes) e Fome/Sede (warrior).
    const isSurvival = sk.mp == null;
    const fomeCost = sk.fome_cost || 0;
    const sedeCost = sk.sede_cost || 0;
    const icon = sk.icon ? sk.icon + ' ' : '';
    let desc = sk.description || sk.desc || '';
    // Guerreiro: a descrição reflete o nível possuído da especialização (Fase 1a).
    if (me.class_id === 'warrior') {
      const _esp = (GS.guildOwnedOf(me.id).especializacoes) || [];
      if (sk.id === 'golpe_devastador')
        desc = _esp.includes('guerreiro_golpe_3')
          ? 'Multiplica os dados de dano por 2 neste turno.'
          : 'Multiplica os dados de dano por 1,5 neste turno.';
      else if (sk.id === 'mira_certeira')
        desc = _esp.includes('guerreiro_mira_3')
          ? '+2 no acerto e +2 no dano neste turno.'
          : '+2 no dado de acerto neste turno.';
      else if (sk.id === 'furia_berserker')
        desc = _esp.includes('guerreiro_furia_3')
          ? '2 ataques extras neste turno.'
          : '1 ataque extra neste turno.';
    }
    const btn = document.createElement('button');

    if (isSurvival) {
      // ── Warrior: botão é um TOGGLE (arma/desarma). Custo só ao atacar. ──
      // SEMPRE disponível durante o meu turno — NÃO há teto de custo: o jogador
      // pode armar mesmo sem ter o recurso, esgotando fome/sede até 0 (risco de
      // exaustão). Quem administra o recurso é o jogador.
      const selected = _wSel(sk.id);
      const podeMarcar = GS.isMyTurn && me.alive && state.phase === 'playing';
      btn.className = 'skill-btn' + (selected ? ' skill-active' : '');
      btn.disabled = !podeMarcar;
      btn.innerHTML = `
        <div class="skill-info">
          <div class="skill-name">${icon}${sk.name}${selected ? ' <small style="color:var(--gold);font-size:.65rem;">● armada</small>' : ''}</div>
          <div class="skill-desc">${desc}</div>
        </div>
        <div class="skill-cost">${[fomeCost ? `🍖${fomeCost}` : '', sedeCost ? `💧${sedeCost}` : ''].filter(Boolean).join(' ') || '—'}</div>`;
      btn.onclick = () => {
        if (!_wSel(sk.id) && GS.getWarriorSelected().length >= GS.warriorComboCap()) {
          const cap = GS.warriorComboCap();
          toast(cap === 1
            ? 'Compre "Combinar Duas" na Guilda para armar 2 habilidades por turno.'
            : `Você só pode armar ${cap} habilidades por turno.`, 'var(--gold)');
          return;
        }
        _wToggle(sk.id); renderMyPanel(GS.gameState);
      };
    } else {
      // ── Demais classes: habilidade de MP (comportamento original). ──
      const ok = canAct && (me.mp >= sk.mp);
      const isActive = GS.pendingSkill && GS.pendingSkill.id === sk.id;
      btn.className = 'skill-btn' + (isActive ? ' skill-active' : '');
      btn.disabled = !ok && !isActive;
      btn.innerHTML = `
        <div class="skill-info">
          <div class="skill-name">${icon}${sk.name}${isActive ? ' <small style="color:var(--gold);font-size:.65rem;">● aguardando alvo</small>' : ''}</div>
          <div class="skill-desc">${desc}</div>
        </div>
        <div class="skill-cost">💙${sk.mp}</div>`;
      btn.onclick = () => {
        if(isActive){ GS.pendingSkill=null; renderMyPanel(GS.gameState); toast('Habilidade cancelada.','var(--text2)'); }
        else { beginSkill(sk, state); }
      };
    }
    sl.appendChild(btn);
  }

  // Warrior (Victor): indicadores das flags ativas neste turno, logo após as skills.
  if ((me.cls || me.class_id) === 'warrior') {
    sl.insertAdjacentHTML('beforeend', renderFlagsWarrior(me));
  }

  // ── Técnica(s) da Guilda equipada(s) (Fase 0) — 4º slot com recarga em rodadas ──
  const _tecEq  = GS.guildEquipOf(me.id);
  const _tecIds = [_tecEq.tecnica, _tecEq.tecnica_exclusiva].filter(Boolean);
  for(const tid of _tecIds){
    const cat = GS.guildCatalogFor(me.class_id).find(x => x.id === tid);
    if(!cat) continue;
    const restante = GS.tecnicaRestante(me, tid);
    const podeUsar = GS.isMyTurn && me.alive && state.phase === 'playing'
                     && restante === 0
                     && (me.fome||0) >= (cat.custo_fome||0) && (me.sede||0) >= (cat.custo_sede||0);
    const btn = document.createElement('button');
    btn.className = 'skill-btn guild-tec' + (restante > 0 ? ' skill-cooldown' : '');
    btn.disabled = !podeUsar;
    const estado = restante > 0
      ? ` <small style="color:#e07060;font-size:.65rem;">⏱️ recarrega em ${restante}r</small>` : '';
    btn.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">${cat.icon||'⚔️'} ${cat.nome} <small style="color:var(--gold);font-size:.58rem;">GUILDA</small>${estado}</div>
        <div class="skill-desc">${cat.desc||''}</div>
      </div>
      <div class="skill-cost">${restante>0 ? `${restante}r` : `🍖${cat.custo_fome} 💧${cat.custo_sede}`}</div>`;
    btn.onclick = () => GS.usarTecnica(tid);
    sl.appendChild(btn);
  }

  // Ladino (Luccas): botão de Desarmar Armadilha quando há uma na casa/adjacente.
  if (me.class_id === 'rogue') {
    const db = _rogueDesarmarBtn(me);
    if (db) sl.appendChild(db);
  }

  // ── Inventory ──
  const inv = $('inventory-list'); inv.innerHTML = '';
  const gear = me.gear || {};

  // ── Equipamento: 8 slots (paper-doll) ──
  const EQ_SLOTS = [
    {key:'weapon',   label:'Mão Direita', empty:'✊'},
    {key:'off_hand', label:'Mão Esquerda',empty:'🤚'},
    {key:'armor',    label:'Corpo',       empty:'👕'},
    {key:'head',     label:'Cabeça',      empty:'🧢'},
    {key:'ring1',    label:'Anel 1',      empty:'💍'},
    {key:'ring2',    label:'Anel 2',      empty:'💍'},
    {key:'item1',    label:'Item 1',      empty:'📦'},
    {key:'item2',    label:'Item 2',      empty:'📦'},
  ];
  const eqTitle = document.createElement('div');
  eqTitle.className = 'section-title'; eqTitle.style.marginTop = '4px';
  eqTitle.textContent = 'Equipamento';
  inv.appendChild(eqTitle);
  const eqGrid = document.createElement('div');
  eqGrid.className = 'equip-grid';
  for(const {key, label, empty} of EQ_SLOTS){
    const item = gear[key];
    const slot = document.createElement('div');
    slot.className = 'eq-slot' + (item ? ' filled' : '');
    slot.title = item ? `${item.name} — clique para desequipar` : label;
    const isAmmoSlot = item && item.effect === 'ammo';
    const ammoTag = isAmmoSlot
      ? `<div class="eq-slot-ammo" style="font-size:1rem;font-weight:900;color:var(--gold);text-align:center;line-height:1;text-shadow:0 0 6px rgba(255,200,50,.7);">×${item.ammo_count ?? 0}</div>`
      : '';
    slot.innerHTML = `
      <div class="eq-slot-label">${label}</div>
      <div class="eq-slot-emoji">${item ? item.emoji : `<span style="opacity:.35">${empty}</span>`}</div>
      <div class="eq-slot-name">${item ? item.name : '—'}</div>
      ${ammoTag}`;
    if(item){
      slot.appendChild(Object.assign(document.createElement('div'),
        {className:'eq-slot-x', textContent:'⤓', title:'Desequipar'}));
      slot.onclick = () => unequipSlot(key);
      aplicarTooltipAoItem(slot, item.id);   // tooltip (se id estiver no catálogo)
    }
    // Hover no slot de arma → mostra área de alcance no mapa
    if(key === 'weapon'){
      slot.addEventListener('mouseenter', () => {
        if(!item) return;
        window._weaponRangePreview = true;
        if(GS.gameState) renderMap(GS.gameState);
      });
      slot.addEventListener('mouseleave', () => {
        window._weaponRangePreview = false;
        if(GS.gameState) renderMap(GS.gameState);
      });
    }
    eqGrid.appendChild(slot);
  }
  inv.appendChild(eqGrid);

  // ── Inventário (bag_size slots — expansível por mochilas) ──
  const bag     = me.bag || [];
  const bagSize = me.bag_size || 6;
  const bagTitle = document.createElement('div');
  bagTitle.className = 'section-title';
  bagTitle.textContent = `Inventário (${bag.length}/${bagSize})`;
  inv.appendChild(bagTitle);
  const bagGrid = document.createElement('div');
  bagGrid.className = 'bag-grid';

  for(let i = 0; i < bagSize; i++){
    const item = bag[i];
    const slot = document.createElement('div');
    if(item){
      const isConsumable = !item.die && ((item.item_slot === 'bag') ||
        item.effect === 'heal' || item.effect === 'atk_bonus');
      const isEquippable = !!(item.item_slot && item.item_slot !== 'bag') || !!item.die;
      const typeLabel = item.die ? '⚔ Arma'
        : item.effect === 'ammo' ? `🏹 Munição (×${item.ammo_count ?? 0})`
        : ({weapon:'⚔ Arma', shield:'🛡 Escudo', armor:'🛡 Armadura',
            head:'⛑ Cabeça', ring:'💍 Anel', item:'🎒 Item',
            accessory:'📿 Acessório', bag:'🧪 Consumível'}[item.item_slot] || '📦 Item');
      slot.className = 'bag-slot filled';
      slot.title = item.name;
      const isAmmoBag = item.effect === 'ammo';
      slot.innerHTML = `
        <div class="bag-slot-num">${i+1}</div>
        <div class="bag-slot-emoji">${item.emoji}</div>
        ${isAmmoBag ? `<div style="font-size:1.05rem;font-weight:900;color:var(--gold);line-height:1;text-shadow:0 0 6px rgba(255,200,50,.7);">×${item.ammo_count ?? 0}</div>` : ''}
        <div class="bag-slot-name">${item.name}</div>
        <div class="bag-slot-type">${typeLabel}</div>`;
      aplicarTooltipAoItem(slot, item.id);   // tooltip (se id estiver no catálogo)
      if(isEquippable){
        const allowed = item.allowed_classes;
        const classRestricted = allowed && me?.class_id && !allowed.includes(me.class_id);
        const btn = document.createElement('button');
        btn.className = 'bag-slot-btn equip' + (classRestricted ? ' disabled' : '');
        btn.textContent = classRestricted ? '🚫 Classe restrita'
          : item.effect === 'ammo' ? '🏹 Equipar munição'
          : '⚙ Equipar';
        btn.disabled = !!classRestricted;
        btn.title = classRestricted ? `Apenas: ${allowed.join(', ')}` : '';
        if(!classRestricted) btn.onclick = () => equipFromBag(i);
        slot.appendChild(btn);
        // Adaga: botão extra para empunhar como 2ª arma (mão esquerda / dual-wield).
        const ehAdaga = (item.id === 'dagger' || /adaga/i.test(item.name || '')) && item.die;
        if(ehAdaga && !classRestricted){
          const btn2 = document.createElement('button');
          btn2.className = 'bag-slot-btn equip';
          btn2.textContent = '🗡️ 2ª arma';
          btn2.title = 'Empunhar na mão esquerda como 2ª arma (dual-wield — usa DES no acerto e dano)';
          btn2.onclick = () => equipOffhand(i);
          slot.appendChild(btn2);
        }
      } else if(item.effect === 'scroll'){
        aplicarTooltipPergaminho(slot, item);   // tooltip com nível/dano/alcance/CD/falha
        if(canAct){
        // Pergaminho mágico: entra em modo de mira (reusa a UI do grimório).
        const btn = document.createElement('button');
        const ehCaster = me && (me.class_id === 'mage' || me.class_id === 'cleric');
        btn.className = 'bag-slot-btn use' + (ehCaster ? '' : ' disabled');
        btn.textContent = ehCaster ? '📜 Conjurar' : '🚫 Só mago/clérigo';
        btn.disabled = !ehCaster;
        btn.title = ehCaster ? 'Conjura a magia guardada (mira no tabuleiro)'
                             : 'Apenas mago ou clérigo conseguem usar pergaminhos.';
        if(ehCaster) btn.onclick = () => castarPergaminho(item);
        slot.appendChild(btn);
        }
      } else if(isConsumable && canAct){
        const btn = document.createElement('button');
        // Se é ação bônus e já foi usada neste turno, desabilitar com aviso
        const isBonusAction = BONUS_ACTION_EFFECTS.has(item.effect);
        const bonusUsado = !!me.bonus_action_used;
        const bloqueado  = isBonusAction && bonusUsado;
        btn.className  = 'bag-slot-btn use' + (bloqueado ? ' disabled' : '');
        btn.textContent = bloqueado ? '⚠ Ação bônus usada' : (isBonusAction ? '🎯 Usar (bônus)' : '▶ Usar');
        btn.disabled    = bloqueado;
        btn.title       = bloqueado
          ? 'Você já usou sua ação bônus neste turno.'
          : isBonusAction ? 'Ação bônus — consome -1 Fome e -1 Sede' : '';
        if(!bloqueado) btn.onclick = () => useItem(item.id);
        slot.appendChild(btn);
      }
    } else {
      slot.className = 'bag-slot empty-slot';
      slot.innerHTML = `
        <div class="bag-slot-num" style="opacity:.5">${i+1}</div>
        <div class="bag-slot-emoji" style="font-size:1rem;opacity:.4">◻</div>
        <div class="bag-slot-type" style="font-size:.52rem">vazio</div>`;
    }
    bagGrid.appendChild(slot);
  }
  inv.appendChild(bagGrid);

  // ── Itens comprados na loja (modelo client-side GS.getHeroiAtivo) ──────────
  renderPurchasedItems(inv, canAct);

  // Gold
  const goldDiv = document.createElement('div');
  goldDiv.className = 'gold-display';
  goldDiv.innerHTML = `🪙 Ouro: <span>${me.gold ?? 0}</span>`;
  inv.appendChild(goldDiv);

  // End turn button
  $('btn-end-turn').disabled = !GS.isMyTurn || !me.alive || state.phase !== 'playing';
}

// ── Itens comprados na loja client-side (GS.getHeroiAtivo().inventario) ──────
// Renderiza os itens comprados no overlay de loja. Consumíveis ganham "Usar"
// (recupera fome/sede via GS.aplicarConsumivel). Equipamento ainda não é
// autoritativo no servidor — ver VISUAL_CONTRACT.
const _TIPO_ITEM_EMOJI = {
  arma:'⚔️', armaDistancia:'🏹', armadura:'🛡️', escudo:'🛡️',
  secundario:'🔦', consumivel:'🍖', municao:'🎯', varinha:'✨', itemMagico:'🎒'
};
const _TIPO_ITEM_LABEL = {
  arma:'⚔ Arma', armaDistancia:'🏹 Distância', armadura:'🛡 Armadura', escudo:'🛡 Escudo',
  secundario:'🔦 Acessório', consumivel:'🍖 Consumível', municao:'🎯 Munição',
  varinha:'✨ Varinha', itemMagico:'🎒 Item Mágico'
};

const _EQUIPADO_SLOTS = [
  {key:'arma',      label:'Arma'},
  {key:'armadura',  label:'Armadura'},
  {key:'cabeca',    label:'Cabeça'},
  {key:'secundario',label:'Secundário'},
  {key:'magico1',   label:'Mágico 1'},
  {key:'magico2',   label:'Mágico 2'},
];

function renderPurchasedItems(inv){
  const heroi = GS.getHeroiAtivo ? GS.getHeroiAtivo() : null;
  if(!heroi) return;

  // ── Equipado (da loja, modelo client-side) ──
  const equipados = _EQUIPADO_SLOTS
    .map(s => ({ ...s, it: heroi.equipado && heroi.equipado[s.key] }))
    .filter(x => x.it);
  if(equipados.length){
    const t = document.createElement('div');
    t.className = 'section-title';
    t.textContent = 'Equipado (Loja)';
    inv.appendChild(t);
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
      btn.onclick = () => desequiparComprado(key);
      slot.appendChild(btn);
      g.appendChild(slot);
    }
    inv.appendChild(g);
  }

  // ── Inventário comprado (client-side) ──
  const comprados = Array.isArray(heroi.inventario)
    ? heroi.inventario.map((it,idx)=>({it,idx})).filter(x=>x.it)
    : [];
  if(!comprados.length) return;

  const title = document.createElement('div');
  title.className = 'section-title';
  title.textContent = `Comprados na Loja (${comprados.length})`;
  inv.appendChild(title);

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
      btn.onclick = () => usarItemComprado(idx);
      slot.appendChild(btn);
    } else if(it.tipo !== 'municao'){
      const btn = document.createElement('button');
      btn.className = 'bag-slot-btn equip';
      btn.textContent = '⚙ Equipar';
      btn.onclick = () => equiparComprado(idx);
      slot.appendChild(btn);
    }
    grid.appendChild(slot);
  }
  inv.appendChild(grid);
}

function usarItemComprado(index){
  const heroi = GS.getHeroiAtivo();
  const item = heroi && heroi.inventario && heroi.inventario[index];
  if(!item) return;
  if(item.tipo === 'consumivel'){
    GS.aplicarConsumivel(item);          // recupera fome/sede + atualiza barras
    heroi.inventario[index] = null;      // consome o item
    if(GS.gameState) renderMyPanel(GS.gameState);
    toast(`Usou ${item.nome}`, 'var(--gold)');
  } else {
    toast('Este item não é consumível.', 'var(--gold)');
  }
}

function equiparComprado(index){
  if(GS.equiparItemComprado(index) && GS.gameState) renderMyPanel(GS.gameState);
}

function desequiparComprado(slot){
  if(GS.desequiparItemComprado(slot) && GS.gameState) renderMyPanel(GS.gameState);
}

let _openChestId = null;   // currently-open chest id (for auto-refresh)
let _openDecorLootId = null;   // currently-open decor loot id (for auto-refresh)

function openChestWindow(chest){
  _openChestId = chest.id;
  _openDecorLootId = null;   // disarm decor auto-refresh
  tocarSomBau();
  const titleEl = $('chest-title');
  if (titleEl) titleEl.textContent = '🎁 Baú de Tesouro';
  _renderChestWindow(chest);
  $('chest-overlay').classList.add('open');
}

function closeChestWindow(){
  _openChestId = null;
  _openDecorLootId = null;
  $('chest-overlay').classList.remove('open');
}

function _renderChestWindow(chest){
  const me = GS.gameState && GS.gameState.players.find(p=>p.id===GS.myPid&&p.alive);
  const isFull = me && (me.bag||[]).length >= (me.bag_size||6);
  const list = $('chest-items-list');
  list.innerHTML = '';

  const itemCount = (chest.items||[]).length;
  const hasGold   = chest.gold > 0;

  if(!hasGold && itemCount === 0){
    list.innerHTML = '<div class="chest-empty-msg">O baú está vazio.</div>';
    return;
  }

  // Gold row
  if(hasGold){
    const row = document.createElement('div');
    row.className = 'chest-gold-row';
    row.innerHTML = `<span class="chest-gold-label">🪙 ${chest.gold} Ouros</span>`;
    const btn = document.createElement('button');
    btn.className = 'chest-take-btn';
    btn.textContent = '⬆ Pegar';
    btn.onclick = () => takeFromChest(chest.id, 'gold', 0);
    row.appendChild(btn);
    list.appendChild(row);
  }

  // Item rows
  (chest.items||[]).forEach((item, idx) => {
    const isAmmo    = item.effect === 'ammo';
    const isWeapon  = !!item.die;
    const typeLabel = isWeapon
      ? `⚔ Arma (${item.die})`
      : isAmmo
        ? `🏹 Munição ×${item.ammo_count ?? 0}`
        : ({weapon:'⚔ Arma', armor:'🛡 Armadura', shield:'🛡 Escudo',
            accessory:'📿 Acessório', ring:'💍 Anel', head:'⛑ Cabeça',
            bag:'🧪 Consumível'}[item.item_slot] || '📦 Item');
    const statSuffix = isWeapon ? ''
      : item.effect==='heal'  ? ` +${item.value} HP`
      : item.effect==='atk'   ? ` +${item.value} Atq`
      : item.effect==='def_'  ? ` +${item.value} CA` : '';

    // Off_hand ammo slot may have space even when bag is full
    const ammoHasSpace = isAmmo && (() => {
      const me2 = GS.gameState && GS.gameState.players.find(p=>p.id===GS.myPid&&p.alive);
      const off = me2 && me2.gear && me2.gear.off_hand;
      if(off && off.effect==='ammo' && off.ammo_type===item.ammo_type && (off.ammo_count||0)<10) return true;
      const bagSlot = me2 && (me2.bag||[]).find(b=>b.effect==='ammo'&&b.ammo_type===item.ammo_type&&(b.ammo_count||0)<10);
      return !!bagSlot;
    })();

    const row = document.createElement('div');
    row.className = 'chest-item-row';
    row.innerHTML = `
      <div class="ci-info">
        <span class="ci-emoji">${item.emoji}</span>
        <div class="ci-text">
          <div class="ci-name">${item.name}</div>
          <div class="ci-type">${typeLabel}${statSuffix}</div>
        </div>
      </div>`;
    const btn = document.createElement('button');
    btn.className = 'chest-take-btn';
    btn.textContent = '⬆ Pegar';
    const cantPick = isFull && !ammoHasSpace;
    btn.disabled = cantPick;
    if(cantPick) btn.title = 'Inventário cheio!';
    btn.onclick = () => takeFromChest(chest.id, 'item', idx);
    row.appendChild(btn);
    list.appendChild(row);
  });
}

function takeFromChest(chestId, kind, index){
  send({ type:'take_from_chest', chest_id:chestId, kind, index });
}

// ── Reusable loot panel — used by both chests and decoration containers ───────
// { titulo, gold, items, onPegarOuro, onPegarItem(idx) }
// Reuses the chest overlay DOM; disarms chest auto-refresh and vice-versa.
function abrirPainelLoot({ titulo, gold, items, onPegarOuro, onPegarItem }) {
  _openChestId = null;   // disarm chest auto-refresh
  _openDecorLootId = null;
  const titleEl = $('chest-title');
  if (titleEl) titleEl.textContent = titulo || '📦 Objeto';
  const me = GS.gameState && GS.gameState.players.find(p => p.id === GS.myPid && p.alive);
  const isFull = me && (me.bag || []).length >= (me.bag_size || 6);
  const list = $('chest-items-list');
  list.innerHTML = '';

  const hasGold  = gold > 0;
  const hasItems = (items || []).length > 0;

  if (!hasGold && !hasItems) {
    list.innerHTML = '<div class="chest-empty-msg">O objeto está vazio.</div>';
    $('chest-overlay').classList.add('open');
    return;
  }

  if (hasGold) {
    const row = document.createElement('div');
    row.className = 'chest-gold-row';
    row.innerHTML = `<span class="chest-gold-label">🪙 ${gold} Ouros</span>`;
    const btn = document.createElement('button');
    btn.className = 'chest-take-btn';
    btn.textContent = '⬆ Pegar';
    btn.onclick = () => onPegarOuro();
    row.appendChild(btn);
    list.appendChild(row);
  }

  (items || []).forEach((item, idx) => {
    const isWeapon = !!item.die;
    const typeLabel = isWeapon
      ? `⚔ Arma (${item.die})`
      : ({ weapon: '⚔ Arma', armor: '🛡 Armadura', shield: '🛡 Escudo',
           accessory: '📿 Acessório', ring: '💍 Anel', head: '⛑ Cabeça',
           bag: '🧪 Consumível' }[item.item_slot] || '📦 Item');
    const statSuffix = isWeapon ? ''
      : item.effect === 'heal' ? ` +${item.value} HP`
      : item.effect === 'atk'  ? ` +${item.value} Atq`
      : item.effect === 'def_' ? ` +${item.value} CA` : '';
    const row = document.createElement('div');
    row.className = 'chest-item-row';
    row.innerHTML = `
      <div class="ci-info">
        <span class="ci-emoji">${item.emoji || '📦'}</span>
        <div class="ci-text">
          <div class="ci-name">${item.name}</div>
          <div class="ci-type">${typeLabel}${statSuffix}</div>
        </div>
      </div>`;
    const btn = document.createElement('button');
    btn.className = 'chest-take-btn';
    btn.textContent = '⬆ Pegar';
    btn.disabled = isFull;
    if (isFull) btn.title = 'Inventário cheio!';
    btn.onclick = () => onPegarItem(idx);
    row.appendChild(btn);
    list.appendChild(row);
  });

  $('chest-overlay').classList.add('open');
}

// ── Histórico de rolagens — faixa fixa sob o cabeçalho do log do Mestre ─────
// Os dados físicos somem em ~3 s; quem piscou ainda vê os últimos resultados
// aqui (mantém as 6 rolagens mais recentes, mais nova primeiro).
const _diceHist = [];
function updateDiceHistory(msg){
  const el = $('dice-history');
  if(!el) return;
  const die = (msg.die||'d20').replace(/^\d+/,'');
  let cor = ({d4:'#FFE000',d6:'#FF1111',d8:'#0055FF',d10:'#00DD44',d12:'#CC00FF',d20:'#FF5500'})[die] || '#FF5500';
  if(msg.discarded) cor = '#e74c3c';
  else if(msg.kept) cor = '#2ecc71';
  _diceHist.unshift({ die, value: msg.value, label: msg.label || die, cor });
  if(_diceHist.length > 6) _diceHist.pop();
  el.innerHTML = _diceHist.map(h =>
    `<span class="dh-item"><b style="color:${h.cor}">${h.die}=${h.value}</b> ${h.label}</span>`
  ).join('');
}

// ── Painel "Como jogar" — criado sob demanda (botão ❓ do cabeçalho) ─────────
function toggleAjuda(){
  let p = $('painel-ajuda');
  if(p){ p.remove(); return; }
  p = document.createElement('div');
  p.id = 'painel-ajuda';
  p.innerHTML = `
    <div class="ajuda-box">
      <h3>❓ Como Jogar</h3>
      <p><b>Seu turno:</b> mova (clique numa casa azul), faça <b>1 ação</b>
      (atacar, magia, abrir baú, item) e <b>1 ação bônus</b> da classe.
      Termine com <b>Encerrar Turno</b>.</p>
      <p><b>Objetivo:</b> explorar a masmorra, derrotar o chefe 👹 e voltar
      à escada para a cidade (comprar itens, descansar) antes do próximo andar.</p>
      <p><b>Dados:</b> <span style="color:#FF5500">■ d20</span> ataque/testes ·
      <span style="color:#FF1111">■ d6</span> / <span style="color:#0055FF">■ d8</span> dano ·
      <span style="color:#2ecc71">■ verde</span> dado mantido ·
      <span style="color:#e74c3c">■ vermelho</span> descartado.</p>
      <p><b>Fome 🍖 e Sede 💧:</b> caem com o tempo e com habilidades —
      zeradas causam penalidades. Coma/beba na cidade ou com itens.</p>
      <p><b>Câmera 3D:</b> arrastar = orbitar · direito = pan · scroll = zoom ·
      <b>R</b> ou ⌂ = vista padrão · 🎲 alterna 2D/3D.</p>
      <button class="btn-secondary" onclick="toggleAjuda()">Fechar</button>
    </div>`;
  document.body.appendChild(p);
}

// ── Som de baú — arpejo dourado curto (mesma infra WebAudio dos dados) ──────
function tocarSomBau(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    [523.25, 659.25, 783.99].forEach((f, i) => {   // C5–E5–G5
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'triangle';
      o.frequency.value = f;
      const t0 = now + i * 0.07;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.18, t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.55);
      o.connect(g); g.connect(_sfxBus());
      o.start(t0); o.stop(t0 + 0.6);
    });
  } catch(e){}
}

function renderGMLog(log){
  if(!log) return;
  const el=$('gm-log-body'); el.innerHTML='';
  for(const msg of log){
    const d=document.createElement('div');
    d.className='gm-msg';
    d.innerHTML=formatGMText(msg);
    el.appendChild(d);
  }
  el.scrollTop=el.scrollHeight;
}

function appendGM(text){
  const el=$('gm-log-body');
  const d=document.createElement('div');
  d.className='gm-msg'; d.innerHTML=formatGMText(text);
  el.appendChild(d);
  el.scrollTop=el.scrollHeight;
  // Trim old messages
  while(el.children.length>60) el.removeChild(el.firstChild);
}

function move(dx,dy){ GS.move(dx,dy); }

function endTurn(){ getAudioContext(); GS.endTurn(); }

// ── Ação Bônus — efeitos de item que consomem ação bônus (máx. 1/turno) ──────
// Espelha BONUS_ACTION_EFFECTS em server.py — manter sincronizados.
const ACOES_BONUS = ['beberPocao', 'usarItemMagico', 'envenenarArma', 'usarItem'];
const BONUS_ACTION_EFFECTS = new Set(['heal', 'atk_bonus', 'antidote']);

function useItem(itemId){ send({type:'use_item',item_id:itemId}); }

function equipFromBag(slotIndex){
  send({type:'equip_from_bag', slot_index: slotIndex});
}

// Equipa uma adaga na mão esquerda (off_hand) como 2ª arma (dual-wield).
function equipOffhand(slotIndex){
  send({type:'equip_offhand', slot_index: slotIndex});
}

function unequipSlot(slotKey){
  send({type:'unequip', slot_key: slotKey});
}
function reorderBag(fromIndex, toIndex){
  send({type:'reorder_bag', from_index: fromIndex, to_index: toIndex});
}

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

  // ── Técnica da Guilda (Fase 0) — equipar no 4º slot (só o próprio herói, na cidade) ──
  if(editable){
    const owned   = (GS.guildOwnedOf(player.id).tecnicas) || [];
    const eq      = GS.guildEquipOf(player.id);
    const catalog = GS.guildCatalogFor(player.class_id);
    const nomeDe = id => { const c = catalog.find(x => x.id === id); return c ? c.nome : id; };
    const isEx   = id => { const c = catalog.find(x => x.id === id); return !!(c && c.exclusiva); };

    const mkSelect = (slotKey, cur, filtro, labelVazio) => {
      const sel = document.createElement('select');
      sel.className = 'guild-equip-sel';
      const optVazio = new Option(labelVazio, '');
      if(!cur) optVazio.selected = true;
      sel.appendChild(optVazio);
      owned.filter(filtro).forEach(id => {
        const o = new Option(nomeDe(id), id);
        if(id === cur) o.selected = true;
        sel.appendChild(o);
      });
      sel.onchange = () => GS.guildEquip(slotKey, sel.value || null);
      return sel;
    };

    const tecTitle = document.createElement('div');
    tecTitle.className = 'section-title'; tecTitle.style.marginTop = '4px';
    tecTitle.textContent = '⚔️ Técnica da Guilda';
    body.appendChild(tecTitle);
    body.appendChild(mkSelect('tecnica', eq.tecnica, id => !isEx(id), '— nenhuma técnica —'));

    if(player.class_id === 'mage' || player.class_id === 'cleric'){
      const exTitle = document.createElement('div');
      exTitle.className = 'section-title'; exTitle.style.marginTop = '4px';
      exTitle.textContent = '✨ Técnica Exclusiva';
      body.appendChild(exTitle);
      body.appendChild(mkSelect('tecnica_exclusiva', eq.tecnica_exclusiva, id => isEx(id), '— nenhuma exclusiva —'));
    }

    if(!owned.length){
      const hint = document.createElement('div');
      hint.className = 'guild-empty'; hint.style.padding = '2px 2px 0';
      hint.textContent = 'Compre técnicas na Guilda dos Heróis.';
      body.appendChild(hint);
    }
  }
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

// Envia o ataque incluindo as habilidades ARMADAS do warrior (toggle). O custo
// de fome/sede é cobrado pelo servidor neste momento (a "ação"). Limpa a seleção
// após enviar — no próximo turno as skills voltam a ficar selecionáveis.
function sendAttack(targetId){
  const buffs = GS.getWarriorSelected();
  send({type:'attack', target_id:targetId, buffs});
  GS.clearWarriorSelected();
}

function beginAttack(){
  getAudioContext();
  const result = GS.resolveAttack();
  if(!result) return;
  if(result.type==='none'){ toast(result.reason); return; }
  if(result.type==='direct'){ GS.notifyAttack(); sendAttack(result.targetId); return; }
  // modal: multiple valid targets
  openTargetModal(result.title, result.targets, 'monster', id=>{ GS.notifyAttack(); sendAttack(id); });
}

// Arremessa a arma de um slot específico ('weapon' = mão principal, 'off_hand' =
// 2ª mão). Seleção rápida de alvo (modal se houver vários). Envia o slot para o
// servidor arremessar exatamente aquela arma.
function beginThrowSlot(slot){
  getAudioContext();
  const st = GS.gameState;
  const me = st && st.players.find(p=>p.id===GS.myPid && p.alive);
  if(!me) return;
  const item = slot === 'off_hand' ? (me.gear && me.gear.off_hand) : me.weapon;
  const tr = item && item.throw_range;
  if(!tr){ toast('Nenhuma arma de arremesso nessa mão.'); return; }
  const nome = (item && item.name) || 'arma';
  const pp = me.pos || [0,0];
  const targets = (st.monsters||[]).filter(m=>m && m.hp>0 &&
    Math.max(Math.abs(pp[0]-m.pos[0]), Math.abs(pp[1]-m.pos[1])) <= tr &&
    GS.hasLineOfSight(st, pp[0], pp[1], m.pos[0], m.pos[1]));   // paredes barram o arremesso
  if(!targets.length){ toast(`Nenhum inimigo à vista a até ${tr} quadrados para arremessar.`); return; }
  if(targets.length===1){ send({type:'throw', target_id:targets[0].id, slot}); return; }
  openTargetModal(`🎯 Arremessar ${nome} — Escolha o Alvo (alcance ${tr})`, targets, 'monster',
    id=>send({type:'throw', target_id:id, slot}));
}

function beginSkill(skill, state){
  getAudioContext();

  // (Warrior usa toggle de habilidades armadas — tratado no loop de botões via
  // GS.toggleWarriorSkill; nunca chega aqui. beginSkill cobre só skills de MP.)
  const result = GS.activateSkill(skill, state);
  if(result==='no_targets'){ toast('Nenhum inimigo vivo!'); return; }
  if(result==='pending_enemy'){
    renderMyPanel(GS.gameState);
    toast(`✨ ${skill.name} ativado — clique no inimigo no mapa!`, 'var(--purple)');
  } else if(result==='pending_ally'){
    renderMyPanel(GS.gameState);
    toast(`✨ ${skill.name} ativado — clique no aliado (ou em si mesmo) no mapa!`, 'var(--blue)');
  }
}

function openTargetModal(title, targets, kind, callback){
  $('target-title').textContent=title;
  const list=$('target-list'); list.innerHTML='';
  for(const t of targets){
    const item=document.createElement('div');
    item.className='target-item';
    item.innerHTML=`
      <span>${t.emoji||'?'}</span>
      <span>${t.name}</span>
      <span class="t-hp">HP ${t.hp}/${t.max_hp||t.hp}</span>`;
    item.onclick=()=>{ closeTargetModal(); callback(t.id); };
    list.appendChild(item);
  }
  $('target-modal').classList.add('open');
}

function closeTargetModal(){
  $('target-modal').classList.remove('open');
}

function handleGameOver(msg){
  setTimeout(()=>{
    showScreen('screen-end');
    if(msg.victory){
      $('end-title').textContent='⚔ VITÓRIA! ⚔';
      $('end-title').style.color='var(--gold)';
      $('end-msg').textContent='Os aventureiros salvaram o reino!';
    } else {
      $('end-title').textContent='💀 DERROTA 💀';
      $('end-title').style.color='var(--red)';
      $('end-msg').textContent='A escuridão venceu... desta vez.';
    }
    renderStory();   // Fase 4b: tela final da campanha (sobre o game over)
  }, 2000);
}

document.addEventListener('keydown', e=>{
  // ESC cancels pending skill regardless of whose turn it is
  if(e.key==='Escape' && GS.pendingSkill){
    GS.pendingSkill=null;
    if(GS.gameState) renderMyPanel(GS.gameState);
    toast('Habilidade cancelada.','var(--text2)');
    e.preventDefault(); return;
  }
  // R resets the 3D camera regardless of turn state
  if((e.key === 'r' || e.key === 'R') && mode3D){
    resetCamera3D();
    e.preventDefault(); return;
  }

  if(!GS.isMyTurn || !GS.gameState || GS.gameState.phase!=='playing') return;
  const me=GS.gameState.players.find(p=>p.id===GS.myPid);
  if(!me?.alive) return;
  switch(e.key){
    case 'ArrowUp':    case 'w': case 'W': GS.move(0,-1); e.preventDefault(); break;
    case 'ArrowDown':  case 's': case 'S': GS.move(0,1);  e.preventDefault(); break;
    case 'ArrowLeft':  case 'a': case 'A': GS.move(-1,0); e.preventDefault(); break;
    case 'ArrowRight': case 'd': case 'D': GS.move(1,0);  e.preventDefault(); break;
    case 'Enter': if(GS.isMyTurn) GS.endTurn();           break;
  }
});

// ── Mobile / touch helpers ──────────────────────────────────────────────────
function isMobile(){
  return window.matchMedia('(max-width: 820px)').matches
      || (('ontouchstart' in window) && window.innerWidth < 920);
}

// Converte um ponto da tela (clientX/Y) na casa [tx,ty] do tabuleiro 2D.
// Robusto a: hi-DPI (canvas.width = cssW×dpr) e zoom por toque (canvas.style.width
// alterado). A "casa em px de CSS" = rect.width / (nº de casas na horizontal).
function _canvasTileXY(cv, clientX, clientY){
  const rect = cv.getBoundingClientRect();
  const dpr  = window.devicePixelRatio || 1;
  const colsX = cv.width  / (dpr * CELL);   // nº de casas na horizontal
  const colsY = cv.height / (dpr * CELL);
  return [Math.floor((clientX - rect.left) / (rect.width  / colsX)),
          Math.floor((clientY - rect.top ) / (rect.height / colsY))];
}

// Canvas mouse interactions
function canvasTile(e){
  return _canvasTileXY(e.target, e.clientX, e.clientY);
}

// ── Toque no tabuleiro 2D: 1 dedo toca=mover / arrasta=rolar; 2 dedos=zoom ────
function _setup2DTouch(){
  const cv = $('dungeon-canvas'), wrap = $('map-wrap');
  if(!cv || !wrap || cv._touchWired) return;
  cv._touchWired = true;
  let sx, sy, st, moved, lx, ly, pinch = null;
  cv.addEventListener('touchstart', e => {
    if(e.touches.length === 1){
      const t = e.touches[0];
      sx = lx = t.clientX; sy = ly = t.clientY; st = Date.now(); moved = 0; pinch = null;
    } else if(e.touches.length === 2){
      const [a,b] = e.touches;
      pinch = { d0: Math.hypot(a.clientX-b.clientX, a.clientY-b.clientY),
                w0: cv.getBoundingClientRect().width,
                cx: (a.clientX+b.clientX)/2, cy: (a.clientY+b.clientY)/2 };
    }
    e.preventDefault();
  }, { passive:false });
  cv.addEventListener('touchmove', e => {
    if(pinch && e.touches.length === 2){
      const [a,b] = e.touches;
      const d = Math.hypot(a.clientX-b.clientX, a.clientY-b.clientY);
      const cssW = cv.width / (window.devicePixelRatio || 1);   // largura "nativa" do mapa
      let nw = pinch.w0 * (d / pinch.d0);
      nw = Math.max(cssW * 0.4, Math.min(cssW * 1.6, nw));       // limita o zoom
      const rect = wrap.getBoundingClientRect();
      const ratio = nw / cv.getBoundingClientRect().width;
      const ox = pinch.cx - rect.left + wrap.scrollLeft;
      const oy = pinch.cy - rect.top  + wrap.scrollTop;
      cv.style.width  = nw + 'px';
      cv.style.height = (nw * cv.height / cv.width) + 'px';
      wrap.scrollLeft = ox * ratio - (pinch.cx - rect.left);
      wrap.scrollTop  = oy * ratio - (pinch.cy - rect.top);
    } else if(e.touches.length === 1){
      const t = e.touches[0], dx = t.clientX - lx, dy = t.clientY - ly;
      moved += Math.abs(dx) + Math.abs(dy);
      wrap.scrollLeft -= dx; wrap.scrollTop -= dy;   // arrasta = rola o mapa
      lx = t.clientX; ly = t.clientY;
    }
    e.preventDefault();
  }, { passive:false });
  cv.addEventListener('touchend', e => {
    if(pinch){ if(e.touches.length === 0) pinch = null; e.preventDefault(); return; }
    if(moved < 14 && (Date.now() - st) < 500){     // toque curto e parado = "clique"
      const [tx,ty] = _canvasTileXY(cv, sx, sy);
      handleTileClick(tx, ty);
    }
    e.preventDefault();
  }, { passive:false });
}

$('dungeon-canvas').addEventListener('mousemove', e=>{
  if(!GS.gameState) return;
  const [tx,ty]=canvasTile(e);
  // Mira de MAGIA (2D): a área verde segue o cursor.
  if(window._modoMagia){ _recomputarAreaMagia(tx, ty); return; }
  const tip=$('tooltip');
  const myP=GS.gameState.players.find(p=>p.id===GS.myPid&&p.alive);

  if(GS.gameState.stairs_pos){
    const [sx,sy]=GS.gameState.stairs_pos;
    if(tx===sx&&ty===sy){
      tip.innerHTML=`🪜 <b>Escada de Saída</b><br><span style="color:#ffd040">Clique para retornar à cidade</span>`;
      tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
      $('dungeon-canvas').style.cursor='pointer'; return;
    }
  }

  // ── Pending skill: show targeting cursor & tooltip ──
  if(GS.pendingSkill){
    const sk=GS.pendingSkill;
    const MELEE_SKILLS=['heavy_blow','backstab','smite'];
    if(sk.target==='enemy'){
      const m=GS.gameState.monsters.find(m=>m.pos[0]===tx&&m.pos[1]===ty&&m.hp>0);
      if(m){
        const needsAdj=MELEE_SKILLS.includes(sk.id);
        let ok=true;
        if(needsAdj&&myP){const dx=Math.abs(myP.pos[0]-tx),dy=Math.abs(myP.pos[1]-ty);ok=(dx===1&&dy===0)||(dx===0&&dy===1);}
        tip.innerHTML=`<b>${m.emoji} ${m.name}</b><br>HP: ${m.hp}/${m.max_hp}<br><span style="color:${ok?'#f08080':'#f09030'}">${ok?'⚔ Clique → '+sk.name:'⚠ Fora de alcance (corpo a corpo)'}</span>`;
        tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
        $('dungeon-canvas').style.cursor=ok?'crosshair':'not-allowed'; return;
      }
    } else if(sk.target==='ally'){
      const pl=GS.gameState.players.find(p=>p.pos[0]===tx&&p.pos[1]===ty&&p.alive);
      if(pl){
        tip.innerHTML=`<b>${pl.emoji} ${pl.name}</b><br>HP: ${pl.hp}/${pl.max_hp}<br><span style="color:#80c0ff">💚 Clique → ${sk.name}</span>`;
        tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
        $('dungeon-canvas').style.cursor='crosshair'; return;
      }
    }
    tip.style.display='none'; $('dungeon-canvas').style.cursor='default'; return;
  }

  const monster=GS.gameState.monsters.find(m=>m.pos[0]===tx&&m.pos[1]===ty&&m.hp>0);
  if(monster){
    const _ddx=myP?Math.abs(myP.pos[0]-tx):99, _ddy=myP?Math.abs(myP.pos[1]-ty):99;
    const _wRng=myP&&myP.weapon&&myP.weapon.range!=null?myP.weapon.range:null;
    const inRange=_wRng!=null ? Math.max(_ddx,_ddy)<=_wRng : (_ddx===1&&_ddy===0)||(_ddx===0&&_ddy===1);
    const canAtk=GS.isMyTurn&&myP&&!myP.action_done&&inRange&&GS.gameState.phase==='playing';
    const atkLabel=canAtk?`<br><span style="color:#f55">${_wRng!=null?'🏹':'⚔'} Clique para atacar</span>`:'';
    // Conhecimento das Lendas (passiva do Henrique): ficha completa se há bardo vivo.
    tip.innerHTML=fichaInimigoTooltipHTML(monster, _partyTemBardoVivo())+atkLabel;
    tip.style.display='block';
    tip.style.left=(e.clientX+14)+'px';
    tip.style.top=(e.clientY-10)+'px';
    $('dungeon-canvas').style.cursor=canAtk?'crosshair':'default';
    return;
  }
  const player=GS.gameState.players.find(p=>p.pos[0]===tx&&p.pos[1]===ty&&p.alive);
  if(player){
    tip.innerHTML=`<b>${player.emoji} ${player.name}</b> (Lv${player.level})<br>HP: ${player.hp}/${player.max_hp}`;
    tip.style.display='block';
    tip.style.left=(e.clientX+14)+'px';
    tip.style.top=(e.clientY-10)+'px';
    $('dungeon-canvas').style.cursor='default';
    return;
  }
  tip.style.display='none';

  // Pointer cursor on reachable tiles when it's my turn
  if(GS.isMyTurn&&GS.gameState.phase==='playing'){
    const myP2=GS.gameState.players.find(p=>p.id===GS.myPid&&p.alive);
    if(myP2&&myP2.moves_left>0&&GS.gameState.tiles[ty]?.[tx]===TILE_FLOOR){
      $('dungeon-canvas').style.cursor='pointer'; return;
    }
  }
  $('dungeon-canvas').style.cursor='crosshair';
});

$('dungeon-canvas').addEventListener('mouseleave',()=>{
  $('tooltip').style.display='none';
  $('dungeon-canvas').style.cursor='crosshair';
});

// Click: unified handler (attack / skill / pathfind) — see handleTileClick below
$('dungeon-canvas').addEventListener('click', e=>{ handleTileClick(...canvasTile(e)); });
_setup2DTouch();   // habilita toque (mover/rolar/zoom) no tabuleiro 2D

// ── Gaveta da ficha (celular): abre/fecha o painel lateral ───────────────────
function toggleFichaDrawer(open){
  const panel = $('side-panel'), back = $('ficha-backdrop');
  if(!panel) return;
  const willOpen = (open === undefined) ? !panel.classList.contains('open') : !!open;
  panel.classList.toggle('open', willOpen);
  if(back) back.classList.toggle('open', willOpen);
  document.body.classList.toggle('drawer-open', willOpen);
}

// Press Enter to submit name
$('input-name').addEventListener('keydown',e=>{ if(e.key==='Enter') createRoom(); });
$('input-code').addEventListener('keydown',e=>{ if(e.key==='Enter') joinRoom(); });
$('input-code').addEventListener('input',e=>{ e.target.value=e.target.value.toUpperCase(); });

// ── Capa do jogo (splash) ────────────────────────────────────────────────
// A capa cobre a tela inicial no boot; o 1º clique/tecla a recua para fundo
// sutil (.dismissed). Tudo confinado a #screen-connect, então some sozinha ao
// trocar de tela. Se a imagem não existir, o splash é removido (jogo intacto).
(function initCoverSplash(){
  const cover = $('cover-splash');
  if(!cover) return;
  // Só mostra a capa se a imagem carregar; senão, remove para não bloquear nada.
  const probe = new Image();
  probe.onerror = () => cover.remove();
  probe.src = 'assets/capa.png';
  let dismissed = false;
  const dismiss = () => {
    if(dismissed) return;
    dismissed = true;
    cover.classList.add('dismissed');
    document.removeEventListener('keydown', dismiss, true);
  };
  cover.addEventListener('click', dismiss);
  document.addEventListener('keydown', dismiss, true);
})();

// ── Sistema de áudio: música de fundo + volumes (música/SFX) ─────────────────
// Música em loop nas telas de menu (abertura/seleção) e na cidade, com crossfade
// suave de 3 s entre faixas e fade-out de 3 s ao entrar no jogo (tabuleiro sem
// música). Painel ⚙️ global (em todas as telas) com dois sliders: Música e Sons.
// Volumes persistidos em localStorage. Renderização/UI pura atrelada a telas —
// sem lógica de jogo. Espelha o padrão do player de história (_storyAudioEl).
const MENU_MUSIC = {
  abertura: 'assets/music/abertura.mp3',
  selecao:  'assets/music/selecao.mp3',
  cidade:   'assets/music/cidade.mp3',
};
const _MM_FADE = 1500;    // ms de crossfade / fade-out
const _mmTracks = {};     // id -> HTMLAudioElement (criado sob demanda)
let _mmCurrent = null;    // id da faixa audível agora
let _mmStarted = false;   // a 1ª reprodução já começou? (autoplay/1º gesto)
let _mmFadeRAF = null;    // handle do requestAnimationFrame das rampas de volume
let _mmVol  = 0.6;        // volume da música (0..1) — sobrescrito por localStorage
let _sfxVol = 1.0;        // volume dos efeitos (0..1) — sobrescrito por localStorage

// ── Persistência dos volumes ────────────────────────────────────────────────
const _AUDIO_KEY = 'lfh_audio';
function _audioLoadPrefs(){
  try {
    const o = JSON.parse(localStorage.getItem(_AUDIO_KEY) || '{}');
    if (typeof o.music === 'number') _mmVol  = Math.max(0, Math.min(1, o.music));
    if (typeof o.sfx   === 'number') _sfxVol = Math.max(0, Math.min(1, o.sfx));
  } catch (e) {}
}
function _audioSavePrefs(){
  try { localStorage.setItem(_AUDIO_KEY, JSON.stringify({ music: _mmVol, sfx: _sfxVol })); } catch (e) {}
}

// ── Master de SFX: TODO efeito Web Audio passa por este gain (volume único) ──
// As funções de som conectam seu nó final a _sfxBus() em vez de ctx.destination.
let _sfxBusNode = null, _sfxBusCtx = null;
function _sfxBus(){
  const ctx = getAudioContext();
  if (!ctx) return null;
  if (_sfxBusCtx !== ctx || !_sfxBusNode){   // (re)cria se o AudioContext mudou
    _sfxBusNode = ctx.createGain();
    _sfxBusNode.gain.value = _sfxVol;
    _sfxBusNode.connect(ctx.destination);
    _sfxBusCtx = ctx;
  }
  return _sfxBusNode;
}
function _setSfxVol(v){
  _sfxVol = Math.max(0, Math.min(1, v));
  if (_sfxBusNode) _sfxBusNode.gain.value = _sfxVol;
  _audioSavePrefs();
}

// ── Música de fundo ──────────────────────────────────────────────────────────
function _mmEl(id){
  if (_mmTracks[id]) return _mmTracks[id];
  const a = new Audio(MENU_MUSIC[id]);
  a.loop = true; a.preload = 'auto'; a.volume = 0;
  _mmTracks[id] = a;
  return a;
}

// Loop único de rampa: cada faixa com fade ativo guarda seu descritor em _mmFade.
function _mmTick(){
  const now = performance.now();
  let active = false;
  for (const id in _mmTracks){
    const a = _mmTracks[id], f = a._mmFade;
    if (!f) continue;
    active = true;
    const t = Math.min(1, (now - f.t0) / f.dur);
    a.volume = Math.max(0, Math.min(1, f.from + (f.to - f.from) * t));
    if (t >= 1){
      a._mmFade = null;
      if (f.stop){ try { a.pause(); a.currentTime = 0; } catch (e) {} }
    }
  }
  _mmFadeRAF = active ? requestAnimationFrame(_mmTick) : null;
}

function _mmFadeTo(a, to, dur, stop){
  a._mmFade = { from: a.volume, to, dur: Math.max(1, dur), t0: performance.now(), stop: !!stop };
  if (!_mmFadeRAF) _mmFadeRAF = requestAnimationFrame(_mmTick);
}

// Toca a faixa `id` com crossfade a partir da atual. Falha de autoplay/arquivo
// é silenciosa (igual ao player de história) — nunca quebra o jogo.
function _mmPlay(id){
  if (!MENU_MUSIC[id]) return;
  const next = _mmEl(id);
  for (const other in _mmTracks){          // faz fade-out das demais
    if (other !== id) _mmFadeTo(_mmTracks[other], 0, _MM_FADE, true);
  }
  const cross = _mmStarted && _mmCurrent && _mmCurrent !== id;
  const p = next.play();
  if (p && p.catch) p.catch(() => {});
  _mmFadeTo(next, _mmVol, cross ? _MM_FADE : 600, false);
  _mmCurrent = id;
  _mmStarted = true;
}

function _mmStop(){                          // fade-out de tudo (entrar no jogo)
  for (const id in _mmTracks) _mmFadeTo(_mmTracks[id], 0, _MM_FADE, true);
  _mmCurrent = null;
}

function _setMusicVol(v){                    // slider de música — aplica ao vivo
  _mmVol = Math.max(0, Math.min(1, v));
  if (_mmCurrent && _mmTracks[_mmCurrent]) _mmFadeTo(_mmTracks[_mmCurrent], _mmVol, 150, false);
  _audioSavePrefs();
}

function _mmHideHint(){                       // esconde a dica da capa ao tocar
  const h = document.getElementById('cover-hint');
  if (h) h.style.opacity = '0';
}

// ── Painel ⚙️ de áudio (global, em todas as telas) ───────────────────────────
function _audioPanelEnsure(){
  let wrap = document.getElementById('audio-settings');
  if (wrap) return wrap;
  const pct = (v) => Math.round(v * 100);
  wrap = document.createElement('div');
  wrap.id = 'audio-settings';
  wrap.style.cssText = 'position:fixed;right:14px;top:14px;z-index:61;font-family:inherit;';
  wrap.innerHTML =
    '<button id="audio-gear" title="Áudio (música e sons)" style="width:42px;height:42px;'
    + 'border-radius:50%;border:1px solid #2a4a2a;background:rgba(13,26,13,.82);color:#a0e0a0;'
    + 'font-size:20px;cursor:pointer;line-height:1;padding:0;box-shadow:0 2px 8px rgba(0,0,0,.5);">⚙️</button>'
    + '<div id="audio-pop" style="display:none;position:absolute;right:0;top:50px;width:210px;'
    + 'background:rgba(13,20,13,.96);border:1px solid #2a4a2a;border-radius:10px;padding:12px 14px;'
    + 'box-shadow:0 6px 20px rgba(0,0,0,.6);color:#cfe9cf;font-size:.8rem;">'
    +   '<div style="display:flex;justify-content:space-between;margin-bottom:5px;">'
    +     '<span>🎵 Música</span><span id="aud-music-val">' + pct(_mmVol) + '%</span></div>'
    +   '<input id="aud-music" type="range" min="0" max="100" value="' + pct(_mmVol) + '" style="width:100%;">'
    +   '<div style="display:flex;justify-content:space-between;margin:12px 0 5px;">'
    +     '<span>🔊 Sons</span><span id="aud-sfx-val">' + pct(_sfxVol) + '%</span></div>'
    +   '<input id="aud-sfx" type="range" min="0" max="100" value="' + pct(_sfxVol) + '" style="width:100%;">'
    + '</div>';
  document.body.appendChild(wrap);
  const pop = wrap.querySelector('#audio-pop');
  wrap.querySelector('#audio-gear').onclick = (e) => {
    e.stopPropagation();
    pop.style.display = (pop.style.display === 'none') ? 'block' : 'none';
  };
  document.addEventListener('click', (e) => { if (!wrap.contains(e.target)) pop.style.display = 'none'; });
  const mSl = wrap.querySelector('#aud-music'), mVal = wrap.querySelector('#aud-music-val');
  mSl.oninput = () => { mVal.textContent = mSl.value + '%'; _setMusicVol(mSl.value / 100); };
  const sSl = wrap.querySelector('#aud-sfx'), sVal = wrap.querySelector('#aud-sfx-val');
  sSl.oninput = () => { sVal.textContent = sSl.value + '%'; _setSfxVol(sSl.value / 100); };
  return wrap;
}

// Chamado por showScreen() a cada troca de tela.
function _menuMusicOnScreen(id){
  _audioPanelEnsure();                       // ⚙️ visível em qualquer tela
  if (id === 'screen-connect')            _mmPlay('abertura');
  else if (id === 'screen-class-select')  _mmPlay('selecao');
  else if (id === 'screen-city')          _mmPlay('cidade');
  else                                    _mmStop();   // tabuleiro / fim: sem música
}

// Início da abertura: tenta tocar junto com a capa; se o browser bloquear o
// autoplay, começa no 1º clique/tecla (mesmo gesto que recua a capa).
let _mmGestureHooked = false;
function _mmHookFirstGesture(){
  if (_mmGestureHooked || _mmStarted) return;
  _mmGestureHooked = true;
  const go = () => {
    document.removeEventListener('pointerdown', go, true);
    document.removeEventListener('keydown', go, true);
    if (!_mmStarted){ _mmPlay('abertura'); _mmHideHint(); }
  };
  document.addEventListener('pointerdown', go, true);
  document.addEventListener('keydown', go, true);
}

(function _audioInit(){
  _audioLoadPrefs();
  _audioPanelEnsure();
  const active = document.querySelector('.screen.active');
  if (!active || active.id !== 'screen-connect') return;  // boot sempre na abertura
  const a = _mmEl('abertura');
  const p = a.play();
  if (p && p.then){
    p.then(() => { _mmCurrent = 'abertura'; _mmStarted = true;
                   _mmFadeTo(a, _mmVol, 800, false); _mmHideHint(); })
     .catch(() => _mmHookFirstGesture());     // autoplay bloqueado → espera gesto
  } else {
    _mmHookFirstGesture();
  }
})();

// THREE.JS  3D RENDERER
// Adiciona visão isométrica 3D ao tabuleiro, sem alterar lógica de jogo.
// Toggle: botão 🎲 3D no cabeçalho do mapa.

let mode3D = false;   // 3D view active?
let g3     = null;    // Three.js renderer state (null when 2D active)
let _movePulse       = 0.5;   // 0→1 sine value used by 2D and 3D highlight animations
let _2dHighlightFrame = null; // requestAnimationFrame handle for 2D pulse loop

// Set true while any mouse button is held and moved; on3DClick checks this flag
// to avoid firing a tile-click immediately after a camera drag/pan ends.
let _orbitDragMoved = false;

function toggle3D(){
  if(!window.THREE){
    toast('⚠ Three.js não disponível — verifique a conexão de internet.','var(--orange)');
    return;
  }
  mode3D = !mode3D;
  const btn   = $('btn-3d-toggle');
  const hint  = $('orbit-hint');
  const reset = $('btn-cam-reset');
  if(mode3D){
    btn.classList.add('active');
    btn.textContent = '◀ 2D';
    if(hint)  hint.style.display  = 'inline';
    if(reset) reset.style.display = 'inline-block';
    $('dungeon-canvas').style.display = 'none';
    if(GS.gameState) renderMap3D(GS.gameState);   // init3D called lazily inside
  } else {
    btn.classList.remove('active');
    btn.textContent = '🎲 3D';
    if(hint)  hint.style.display  = 'none';
    if(reset) reset.style.display = 'none';
    $('dungeon-canvas').style.display = 'block';
    dispose3D();
    if(GS.gameState) renderMap(GS.gameState);
  }
}

// Each TILE_FLOOR cell → chunky physical floor piece (thickness 0.22, gap 0.07/side)
// Each TILE_WALL cell → tall stone wall column (height 1.75, same footprint)
// Dark table surface underneath → gap between pieces = visible grid lines

function init3D(state){
  if(!window.THREE){ console.error('Three.js not loaded'); return; }
  if(!window.THREE.OrbitControls){ console.error('OrbitControls not loaded'); return; }
  if(g3) dispose3D();

  const T   = window.THREE;
  const wrap = $('map-wrap');
  const W = state.tiles[0].length, H = state.tiles.length;

  // Use offsetWidth/Height so the canvas covers map-wrap including its padding.
  // wrap.style is also set to position:relative so the canvas can be absolute.
  wrap.style.position = 'relative';
  const CW = wrap.offsetWidth  || 640;
  const CH = wrap.offsetHeight || 480;

  // ── Ambiente de iluminação (preset por mapa). Default "masmorra".
  // Controla luz/fog/exposição dos tiles explorados; a névoa de guerra é igual.
  const AMB = (VC.ambientes && VC.ambientes[state.ambiente]) || VC.ambientes.masmorra;
  const AMBL = AMB.lighting;

  // ── Scene
  const scene = new T.Scene();
  scene.background = new T.Color(AMB.scene.bgColor);
  // Subtle fog — keeps depth cue without hiding explored areas
  scene.fog = new T.FogExp2(AMB.scene.fogColor, AMB.scene.fogDensity);

  // ── Renderer
  const renderer = new T.WebGLRenderer({ antialias:true, powerPreference:'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(CW, CH);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type    = T.PCFShadowMap   /* PCF simples: ~igual visualmente, bem mais barato que PCFSoft */;
  renderer.toneMapping       = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = AMB.exposure;
  // Absolute-fill so canvas covers the full map-wrap area (including 8px padding)
  Object.assign(renderer.domElement.style, {
    display: 'block', position: 'absolute',
    top: '0', left: '0', width: '100%', height: '100%',
  });
  wrap.appendChild(renderer.domElement);

  // ── Orthographic isometric camera
  const aspect = CW / CH;
  const fH     = Math.max(W, H) * 0.60;
  const camera = new T.OrthographicCamera(-fH*aspect, fH*aspect, fH, -fH, -300, 300);
  camera.updateProjectionMatrix();

  // Sits at y=–0.01 — the 0.07-unit gap between tiles lets it show through,
  // creating natural grid lines without any extra geometry.
  const tableGeo = new T.PlaneGeometry(W + 8, H + 8);
  const tableMat = new T.MeshStandardMaterial({ color:0x0e0c15, roughness:0.98, metalness:0.0 });
  const tableM   = new T.Mesh(tableGeo, tableMat);
  tableM.rotation.x = -Math.PI / 2;
  tableM.position.set((W-1)/2, -0.01, (H-1)/2);
  tableM.receiveShadow = true;
  scene.add(tableM);

  const TW = 0.86;   // tile footprint width/depth  (gap = 0.07 per side)
  const TH = 0.22;   // floor tile thickness         (chunky physical piece)
  const WH = 1.75;   // wall tile height             (from table to top)

  const floorTex = generateTexture('floor');   // 512×512 paved tiles
  const wallTex  = generateTexture('wall');    // 512×512 irregular brickwork

  // ── BASE MATERIALS (cloned per tile for individual colour tint) ─────────────
  // Textures are in mid-gray range so material.color tints them to final hue.
  // wallBaseMat uses the same texture as roughnessMap so block faces catch light
  // differently from mortar gaps — creates tactile stone surface feel.
  const floorBaseMat = new T.MeshStandardMaterial({ map:floorTex, roughness:0.92, metalness:0.03 });
  const wallBaseMat  = new T.MeshStandardMaterial({ map:wallTex, roughnessMap:wallTex, roughness:0.92, metalness:0.04 });

  // Textura de canvas por material (cache por id). Usa os MESMOS painters do 2D
  // para a aparência 2D/3D coincidir. Materiais "de pedra" (cinza/normal/negra)
  // retornam null e seguem usando floorTex/wallTex tingidos pela cor.
  const _matTexCache = {};
  function makeMaterialTex(matId){
    if(matId in _matTexCache) return _matTexCache[matId];
    const S=256, cv=document.createElement('canvas'); cv.width=cv.height=S;
    const c=cv.getContext('2d'); const r=_rng((matId.length*2654435761)>>>0);
    let tex=null;
    switch(matId){
      case 'grama':         paintGrass(c,0,0,S,r); break;
      case 'terra':         paintDirt(c,0,0,S,r); break;
      case 'pedra_negra':   paintStone(c,0,0,S,r,[30,28,34]); break;
      case 'enegrecida':    paintBrick(c,0,0,S,r,[22,21,26],'#070709'); break;
      case 'pedra_caverna': paintCave(c,0,0,S,r); break;
      case 'desmoronada':   paintRubble(c,0,0,S,r); break;
      case 'entulho':       paintRubble(c,0,0,S,r); break;
    }
    if(matId==='grama'||matId==='terra'||matId==='pedra_negra'||matId==='enegrecida'||matId==='pedra_caverna'||matId==='desmoronada'||matId==='entulho'){
      tex=new T.CanvasTexture(cv); tex.wrapS=tex.wrapT=T.RepeatWrapping;
    }
    _matTexCache[matId]=tex; return tex;
  }

  const floorGeo = new T.BoxGeometry(TW, TH, TW);
  const wallGeo  = new T.BoxGeometry(TW, WH, TW);

  // Warm brownish ambient — dark but not pitch-black. Areas away from torches
  // are still barely readable; the torches provide the main visible illumination.
  // Warm-white ambient — ensures shadow areas are still readable
  const ambient = new T.AmbientLight(AMBL.ambient.color, AMBL.ambient.intensity);
  scene.add(ambient);

  // Main directional — warm key light from front-right above
  const showcase = new T.DirectionalLight(AMBL.dirMain.color, AMBL.dirMain.intensity);
  showcase.position.set(...AMBL.dirMain.pos);
  showcase.castShadow = true;
  showcase.shadow.mapSize.width = showcase.shadow.mapSize.height = 2048;
  showcase.shadow.camera.far    = 120;
  showcase.shadow.camera.left   = -(W + 6);
  showcase.shadow.camera.right  =  (W + 6);
  showcase.shadow.camera.top    =  (H + 6);
  showcase.shadow.camera.bottom = -(H + 6);
  showcase.shadow.bias = -0.0004;
  scene.add(showcase);

  // Cool fill — back-left; contrasts lit vs shadow without over-darkening
  const fillLight = new T.DirectionalLight(AMBL.dirFill.color, AMBL.dirFill.intensity);
  fillLight.position.set(...AMBL.dirFill.pos);
  scene.add(fillLight);

  // Warm back-rim — preserves silhouette readability on miniature backs
  const rimLight = new T.DirectionalLight(AMBL.rimLight.color, AMBL.rimLight.intensity);
  rimLight.position.set(...AMBL.rimLight.pos);
  scene.add(rimLight);

  // SW pawn-front light — as frentes das miniaturas apontam para sudoeste
  // (lado da câmera padrão) e ficavam de costas para dirMain (NE). Antes cada
  // peão carregava 2–3 PointLights próprias para compensar; esta directional
  // única ilumina todas as frentes com custo fixo e contagem de luzes ESTÁVEL
  // (variar o nº de luzes força o Three.js a recompilar todos os shaders).
  const pawnLight = new T.DirectionalLight(AMBL.dirPawn.color, AMBL.dirPawn.intensity);
  pawnLight.position.set(...AMBL.dirPawn.pos);
  scene.add(pawnLight);

  // Player-carried torch — warm flicker, follows player each frame.
  const torch = new T.PointLight(0xff9520, 5.5, 14.0, 1.8);
  torch.castShadow = true;
  torch.shadow.mapSize.width  = 512;
  torch.shadow.mapSize.height = 512;
  torch.shadow.radius = 3;     // PCFSoft blur radius
  torch.shadow.bias   = -0.001;
  scene.add(torch);

  // Vision lamp — bright white-warm fill ensuring clear sight within ~3 tiles.
  // No shadows (performance), positioned at eye-level so it lights miniatures well.
  // Decay=1.6 gives smooth falloff: bright at <2 tiles, dim at 4, invisible at 5.
  const visionLamp = new T.PointLight(0xfff8e8, 14.0, 9.0, 1.4);  // large bright halo around player
  scene.add(visionLamp);

  // ── WALL-SCONCE FILL LIGHTS (deterministic PointLights, corridor atmosphere) ──
  // Reduced intensity — now that per-room torches are the main room lights.
  const sconces = [];
  for(let ty=0; ty<H; ty++){
    for(let tx=0; tx<W; tx++){
      if(state.tiles[ty][tx] !== TILE_WALL) continue;
      const th = ((tx*3761)^(ty*2399))&0xFF;
      if(th%7 !== 0) continue;
      const hasFloor = [[0,1],[0,-1],[1,0],[-1,0]].some(([dx,dy])=>{
        const nx=tx+dx, ny=ty+dy;
        return nx>=0&&ny>=0&&nx<W&&ny<H&&state.tiles[ny][nx]===TILE_FLOOR;
      });
      if(!hasFloor) continue;
      const sl = new T.PointLight(0xffaa44, 2.8, 7.5, 1.8);
      sl.position.set(tx, 1.2, ty);
      sl.visible = false;
      scene.add(sl);
      sconces.push({x:tx, y:ty, light:sl});
    }
  }

  // ── PER-ROOM TORCHES (bracket + flame geometry + animated PointLight) ────────
  const wallTorches = [];
  try{ buildRoomTorches(T, scene, state, wallTorches, TW, TH, WH); }catch(e){ console.warn('buildRoomTorches:', e); }

  // ── ROOM FLOOR OVERLAYS (colored translucent plane per room role) ─────────────
  const roomOverlayMeshes = {};
  try{ buildRoomOverlays(T, scene, state, roomOverlayMeshes, TW, TH); }catch(e){ console.warn('buildRoomOverlays:', e); }

  let sceneryMeshes = {};
  try{ sceneryMeshes = buildSceneryBarrels(T, scene, state, TW, TH, WH); }catch(e){ console.warn('buildSceneryBarrels:', e); }

  // ── GLOWING GROUT (magic rune grid lines in trap rooms) ───────────────────────
  let groutMeshes = {}, groutMats = [];
  try{ ({ meshes: groutMeshes, mats: groutMats } = buildGlowingGrout(T, scene, state, TW, TH)); }catch(e){ console.warn('buildGlowingGrout:', e); }

  // ── MOVEMENT HIGHLIGHT PLANES (blue — MeshBasicMaterial, unaffected by lighting)
  const moveHighlightMeshes = {};
  const moveHighlightMat = new T.MeshBasicMaterial({ color: 0x1e6bff, opacity: 0.45, transparent: true, depthWrite: false });
  {
    const hGeo = new T.PlaneGeometry(TW * 0.90, TW * 0.90);
    for(let fy=0; fy<H; fy++) for(let fx=0; fx<W; fx++){
      if(state.tiles[fy][fx] !== TILE_FLOOR) continue;
      const m = new T.Mesh(hGeo, moveHighlightMat);
      m.rotation.x = -Math.PI / 2;
      m.position.set(fx, TH + 0.004, fy);
      m.visible = false; scene.add(m);
      moveHighlightMeshes[`${fx},${fy}`] = m;
    }
  }

  // ── ATTACK HIGHLIGHT PLANES (red — MeshBasicMaterial, unaffected by lighting)
  const atkHighlightMeshes = {};
  {
    const hGeo = new T.PlaneGeometry(TW * 0.90, TW * 0.90);
    const hMat = new T.MeshBasicMaterial({ color: 0xff2222, opacity: 0.35, transparent: true, depthWrite: false });
    for(let fy=0; fy<H; fy++) for(let fx=0; fx<W; fx++){
      if(state.tiles[fy][fx] !== TILE_FLOOR) continue;
      const m = new T.Mesh(hGeo, hMat);
      m.rotation.x = -Math.PI / 2;
      m.position.set(fx, TH + 0.006, fy);
      m.visible = false; scene.add(m);
      atkHighlightMeshes[`${fx},${fy}`] = m;
    }
  }

  // ── WEAPON RANGE PREVIEW PLANES (vermelho forte — hover no ícone da arma)
  const weaponRangeMeshes = {};
  {
    const hGeo = new T.PlaneGeometry(TW * 0.92, TW * 0.92);
    const hMat = new T.MeshBasicMaterial({ color: 0xff0000, opacity: 0.62, transparent: true, depthWrite: false });
    for(let fy=0; fy<H; fy++) for(let fx=0; fx<W; fx++){
      if(state.tiles[fy][fx] !== TILE_FLOOR) continue;
      const m = new T.Mesh(hGeo, hMat);
      m.rotation.x = -Math.PI / 2;
      m.position.set(fx, TH + 0.010, fy);
      m.visible = false; scene.add(m);
      weaponRangeMeshes[`${fx},${fy}`] = m;
    }
  }

  // ── SPELL HIGHLIGHT PLANES — alcance (vermelho), zona (laranja), 2x (verde escuro), área (verde)
  const spellRangeMeshes = {}, spellZonaMeshes = {}, spellDoubleMeshes = {}, spellAreaMeshes = {}, spellEscuridaoMeshes = {}, spellSilencioMeshes = {};
  {
    const hGeo = new T.PlaneGeometry(TW * 0.98, TW * 0.98);
    const escMat    = new T.MeshBasicMaterial({ color: 0x0a061a, opacity: 0.60, transparent: true, depthWrite: false });
    const silMat    = new T.MeshBasicMaterial({ color: 0x7888c8, opacity: 0.26, transparent: true, depthWrite: false });
    const rangeMat  = new T.MeshBasicMaterial({ color: 0xff2a2a, opacity: 0.16, transparent: true, depthWrite: false });
    const zonaMat   = new T.MeshBasicMaterial({ color: 0xff6a00, opacity: 0.30, transparent: true, depthWrite: false });
    const doubleMat = new T.MeshBasicMaterial({ color: 0x0a5a16, opacity: 0.60, transparent: true, depthWrite: false });
    const areaMat   = new T.MeshBasicMaterial({ color: 0x28e636, opacity: 0.32, transparent: true, depthWrite: false });
    const mk = (mat, yoff, fx, fy) => {
      const mm = new T.Mesh(hGeo, mat); mm.rotation.x = -Math.PI / 2;
      mm.position.set(fx, TH + yoff, fy); mm.visible = false; scene.add(mm); return mm;
    };
    for(let fy=0; fy<H; fy++) for(let fx=0; fx<W; fx++){
      if(state.tiles[fy][fx] !== TILE_FLOOR) continue;
      const key = `${fx},${fy}`;
      spellEscuridaoMeshes[key] = mk(escMat,    0.007, fx, fy);   // névoa escura no chão (sob os peões)
      spellSilencioMeshes[key]  = mk(silMat,    0.0072, fx, fy);  // véu de silêncio
      spellRangeMeshes[key]  = mk(rangeMat,  0.008, fx, fy);
      spellZonaMeshes[key]   = mk(zonaMat,   0.009, fx, fy);
      spellDoubleMeshes[key] = mk(doubleMat, 0.010, fx, fy);
      spellAreaMeshes[key]   = mk(areaMat,   0.012, fx, fy);
    }
  }

  // ── WET FLOOR REFLECTION (damp specular sheen — all dungeon floor tiles) ──────
  // A near-black low-roughness plane floats 2mm above each floor piece.
  // MeshStandardMaterial roughness 0.10 produces sharp torch reflections.
  const wetFloorMeshes = {};
  {
    const wetGeo = new T.PlaneGeometry(TW * 0.94, TW * 0.94);
    const wetMat = new T.MeshStandardMaterial({
      color: new T.Color(0x111111), roughness: 0.10, metalness: 0.0,
      opacity: 0.30, transparent: true, depthWrite: false
    });
    for(let fy=0; fy<H; fy++){
      for(let fx=0; fx<W; fx++){
        if(state.tiles[fy][fx] !== TILE_FLOOR) continue;
        const key = `${fx},${fy}`;
        const m = new T.Mesh(wetGeo, wetMat);
        m.rotation.x = -Math.PI / 2;
        m.position.set(fx, TH + 0.002, fy);   // 2mm above floor surface
        m.visible = false;
        scene.add(m);
        wetFloorMeshes[key] = m;
      }
    }
  }

  const tileMeshes = {};
  for(let y=0; y<H; y++){
    for(let x=0; x<W; x++){
      const key = `${x},${y}`;
      let mesh;
      // Per-tile hash: drives independent colour variation per piece
      const vf = ((x*7919^y*3467)&0xFF) / 255;
      const vw = ((x*6271^y*4423)&0xFF) / 255;

      if(state.tiles[y][x] === TILE_FLOOR || state.tiles[y][x] === TILE_DOOR){
        const mat = floorBaseMat.clone();
        // Cor base por material (default pedra_cinza); jitter por casa preserva o relevo.
        const mid3 = (state.materiais && state.materiais[key]) || 'pedra_cinza';
        const mc = (VC.materiais[mid3] || VC.materiais.pedra_cinza).color;
        const jit = vf*VC.floor.baseVariance;
        mat.color.setRGB(mc[0]+jit, mc[1]+jit, mc[2]+jit);
        const ftex = makeMaterialTex(mid3);
        if(ftex){ mat.map = ftex; mat.color.setRGB(1,1,1); }
        mat.emissive.set(VC.floor.emissive);
        mat.emissiveIntensity = 1.0;
        // Auto-iluminação: a própria textura emite, deixando a cor forte e
        // diferenciada mesmo na penumbra (grama/terra/pedra negra).
        if(ftex && (mid3==='grama' || mid3==='terra' || mid3==='pedra_negra')){
          mat.emissiveMap = ftex;
          mat.emissive.set(0xffffff);
          mat.emissiveIntensity = (mid3==='pedra_negra') ? 0.35 : 0.6;
        }
        mesh = new T.Mesh(floorGeo, mat);
        mesh.position.set(x, TH/2, y);     // bottom edge sits at y = 0
        mesh.receiveShadow = true;
        mesh.userData.isFloor = true;
        mesh.userData.gridX   = x;
        mesh.userData.gridY   = y;
        mesh.userData.baseMat = mat;        // saved for restoring after highlight
        if((state.materiais && state.materiais[key]) === 'entulho'){
          // Entulho oclui visão → bloco altura-de-parede de escombros sobre o chão.
          const ec = VC.materiais.entulho.color;
          const eMat = wallBaseMat.clone();
          eMat.color.setRGB(ec[0], ec[1], ec[2]);
          const etex = makeMaterialTex('entulho');
          if(etex){ eMat.map = etex; eMat.color.setRGB(1,1,1); }
          eMat.emissive.set(VC.wall.emissive); eMat.emissiveIntensity = 1.0;
          const eMesh = new T.Mesh(wallGeo, eMat);
          eMesh.position.set(x, WH/2, y);
          eMesh.scale.y = 0.7;                 // pilha um pouco mais baixa que a parede
          eMesh.castShadow = eMesh.receiveShadow = true;
          eMesh.visible = false;
          eMesh.userData.gridX = x; eMesh.userData.gridY = y;
          scene.add(eMesh);
          tileMeshes[`entulho:${key}`] = eMesh;   // revelado junto com a casa (ver visibilidade)
        }
      } else {
        const matId3 = (state.materiais && state.materiais[key]) || 'pedra_normal';
        const wc = (VC.materiais[matId3] || VC.materiais.pedra_normal).color;
        const mat = wallBaseMat.clone();
        // Cor base por material (default pedra_normal); jitter por casa preserva o relevo.
        const jw = vw*VC.wall.variance;
        mat.color.setRGB(wc[0]+jw, wc[1]+jw, wc[2]+jw);
        const wtex = makeMaterialTex(matId3);
        if(wtex){ mat.map = wtex; mat.color.setRGB(1,1,1); }
        mat.emissive.set(VC.wall.emissive);
        mat.emissiveIntensity = 1.0;
        mesh = new T.Mesh(wallGeo, mat);
        mesh.position.set(x, WH/2, y);     // bottom edge sits at y = 0
        mesh.castShadow    = true;
        mesh.receiveShadow = true;
        mesh.userData.isWall = true;
      }
      mesh.visible = false;     // revealed progressively as player explores
      scene.add(mesh);
      tileMeshes[key] = mesh;
    }
  }

  // ── DOOR LEAVES — wooden slab over each DOOR tile (hidden when open) ──────────
  const doorMeshes = {};
  {
    const isWall3D = (tx,ty)=> ty<0||tx<0||ty>=H||tx>=W || state.tiles[ty][tx]===TILE_WALL;
    const doorGeo  = new T.BoxGeometry(TW, WH*0.80, 0.12);
    const ironGeo  = new T.BoxGeometry(TW, 0.07, 0.14);
    for(let y=0; y<H; y++){
      for(let x=0; x<W; x++){
        if(state.tiles[y][x] !== TILE_DOOR) continue;
        const dMat = new T.MeshStandardMaterial({ color:0x6b4523, roughness:0.85, metalness:0.06,
                                                  emissive:0x110a04, emissiveIntensity:1.0 });
        const grp = new T.Group();
        const leaf = new T.Mesh(doorGeo, dMat);
        leaf.castShadow = true; leaf.receiveShadow = true;
        grp.add(leaf);
        const iMat = new T.MeshStandardMaterial({ color:0x2a2a30, roughness:0.6, metalness:0.5 });
        for(const oy of [WH*0.22, -WH*0.22]){
          const band = new T.Mesh(ironGeo, iMat); band.position.y = oy; grp.add(band);
        }
        // Corredor sobe/desce (paredes L+R) ⇒ folha atravessa em X (rotação 0).
        // Senão (paredes em cima/baixo) ⇒ folha ao longo de Z (gira 90°).
        const vertical = isWall3D(x-1,y) && isWall3D(x+1,y);
        if(!vertical) grp.rotation.y = Math.PI/2;
        grp.position.set(x, TH + WH*0.40, y);
        grp.visible = false;
        scene.add(grp);
        doorMeshes[`${x},${y}`] = grp;
      }
    }
  }

  // ── WALL ARCHITECTURE DETAILS (door arches, corner columns, baseboards) ───────
  let wallDetailMeshes = {};
  try{ wallDetailMeshes = buildWallDetails(T, scene, state, wallTex, TW, TH, WH); }catch(e){ console.warn('buildWallDetails:', e); }

  // Built once; visibility driven by exploredSet in renderMap3D.
  let stairGroup = null;
  if(state.stairs_pos){
    const [sx, sy] = state.stairs_pos;
    stairGroup = new T.Group();
    const sMat  = new T.MeshStandardMaterial({color:0x4a3620, roughness:0.86, metalness:0.10});
    const sEdge = new T.MeshStandardMaterial({color:0x6a5030, roughness:0.72, metalness:0.15});
    const sGold = new T.MeshStandardMaterial({
      color:new T.Color(0xffd060), emissive:new T.Color(0xffd060),
      emissiveIntensity:0.55, roughness:0.25, metalness:0.90
    });
    const NSTEPS=4, SW=0.80, SD=0.14, SH=0.055;
    for(let i=0;i<NSTEPS;i++){
      const sm=new T.Mesh(new T.BoxGeometry(SW,SH,SD),i===NSTEPS-1?sEdge:sMat);
      sm.position.set(sx, TH+(i+0.5)*SH, sy+(i-NSTEPS/2+0.5)*SD);
      sm.castShadow=sm.receiveShadow=true; stairGroup.add(sm);
    }
    // Gold inlay lines on each step edge
    for(let i=0;i<NSTEPS;i++){
      const gl=new T.Mesh(new T.BoxGeometry(SW+0.02,0.012,0.012),sGold);
      gl.position.set(sx, TH+(i+1)*SH-0.004, sy+(i-NSTEPS/2+1)*SD-SD/2);
      gl.userData.isStairGlow=true; stairGroup.add(gl);
    }
    // Glow ring at floor level
    const ring=new T.Mesh(new T.TorusGeometry(0.40,0.022,6,28),sGold);
    ring.rotation.x=Math.PI/2; ring.position.set(sx,TH+0.005,sy);
    ring.userData.isStairGlow=true; stairGroup.add(ring);
    // Warm point light above stairs
    const stairLight=new T.PointLight(0xffd080,1.2,3.5);
    stairLight.position.set(sx,TH+0.9,sy); stairGroup.add(stairLight);
    stairGroup.visible=false;
    scene.add(stairGroup);
  }

  // ── Exit marker (Fase 3 — masmorra autorada): mastro + bandeira 🏁 ────────────
  // Estático; visibilidade por fog (exploredSet) em renderMap3D, como stairGroup.
  let exitGroup = null;
  {
    const ex = (window.GS && GS.exitPos) || null;
    if(ex){
      const [exx, exy] = ex;
      exitGroup = new T.Group();
      const poleMat = new T.MeshStandardMaterial({color:0x8a8a96, roughness:0.5, metalness:0.6});
      const pole = new T.Mesh(new T.CylinderGeometry(0.025,0.025,0.95,8), poleMat);
      pole.position.set(exx, TH+0.475, exy); pole.castShadow=true; exitGroup.add(pole);
      const flagMat = new T.MeshStandardMaterial({
        color:new T.Color(0x3cdcb4), emissive:new T.Color(0x1c8a70),
        emissiveIntensity:0.55, roughness:0.45, metalness:0.10, side:T.DoubleSide
      });
      const flag = new T.Mesh(new T.PlaneGeometry(0.34,0.20), flagMat);
      flag.position.set(exx+0.18, TH+0.82, exy); exitGroup.add(flag);
      const ring = new T.Mesh(new T.TorusGeometry(0.40,0.020,6,28), flagMat);
      ring.rotation.x=Math.PI/2; ring.position.set(exx,TH+0.006,exy); exitGroup.add(ring);
      const exLight = new T.PointLight(0x60e0c0,0.9,3.0);
      exLight.position.set(exx,TH+0.9,exy); exitGroup.add(exLight);
      exitGroup.visible=false;
      scene.add(exitGroup);
    }
  }

  const entityGroup = new T.Group();
  scene.add(entityGroup);

  const raycaster = new T.Raycaster();

  const resizeObs = new ResizeObserver(() => { if(g3) resize3D(); });
  resizeObs.observe(wrap);

  const controls = new T.OrbitControls(camera, renderer.domElement);
  controls.enableDamping     = true;      // smooth deceleration on release
  controls.dampingFactor     = 0.08;
  controls.screenSpacePanning = true;    // right-drag pans parallel to screen
  controls.mouseButtons = {
    LEFT:   T.MOUSE.ROTATE,
    MIDDLE: T.MOUSE.DOLLY,
    RIGHT:  T.MOUSE.PAN,
  };
  // Zoom limits (OrthographicCamera: camera.zoom is modified by controls)
  controls.minZoom = 0.28;
  controls.maxZoom = 8.0;
  // Polar angle clamp — prevents camera from dipping below the board
  controls.minPolarAngle = 8  * Math.PI / 180;   //  8° above horizon  (wide low shot)
  controls.maxPolarAngle = 82 * Math.PI / 180;   // 82° = nearly straight down

  // ── FLOATING DUST PARTICLES (200 motes drifting upward — spore/smoke ambience)
  // Each mote has a fixed XZ position and a slowly increasing Y (resets at ceiling).
  // BufferGeometry + PointsMaterial — zero draw calls, ~6 KB of data.
  const DUST_N    = 200;
  const DUST_CEIL = WH + 0.6;   // reset threshold slightly above wall tops
  const _dXZ  = new Float32Array(DUST_N * 2);   // current XZ position
  const _dY   = new Float32Array(DUST_N);        // current Y height
  const _dVel = new Float32Array(DUST_N);        // upward drift speed
  const _dPosArr = new Float32Array(DUST_N * 3); // packed XYZ for BufferAttribute

  for(let i = 0; i < DUST_N; i++){
    _dXZ[i*2]   = Math.random() * (W - 1);
    _dXZ[i*2+1] = Math.random() * (H - 1);
    _dY[i]      = Math.random() * DUST_CEIL;
    _dVel[i]    = 0.00022 + Math.random() * 0.00060;  // 0.22–0.82 mm per ms upward
    _dPosArr[i*3]   = _dXZ[i*2];
    _dPosArr[i*3+1] = _dY[i];
    _dPosArr[i*3+2] = _dXZ[i*2+1];
  }
  const dustBuf = new T.BufferGeometry();
  dustBuf.setAttribute('position', new T.BufferAttribute(_dPosArr, 3));
  const dustPts = new T.Points(dustBuf,
    new T.PointsMaterial({
      color: 0xfff0cc, size: 0.024,
      transparent: true, opacity: 0.15,
      depthWrite: false, sizeAttenuation: true
    })
  );
  dustPts.visible = false;   // shown once the player reveals tiles
  scene.add(dustPts);

  // ── Hover showcase spotlight — dim gold point-light, driven each tick ───────
  // Intensity starts at 0 (off); the animation loop lerps it up when a figure
  // is hovered.  No shadow cast — cheap fill only.
  const hoverSpot = new T.PointLight(0xffd080, 0, 1.5);
  hoverSpot.castShadow = false;
  hoverSpot.userData.isHoverLight = true;
  scene.add(hoverSpot);

  g3 = {
    T, scene, renderer, camera, controls,
    ambient, torch, visionLamp, rimLight, fillLight, sconces,
    tileMeshes, doorMeshes, wallDetailMeshes, entityGroup, raycaster,
    wallTorches, roomOverlayMeshes,
    sceneryMeshes, groutMeshes, groutMats,
    wetFloorMeshes, moveHighlightMeshes, atkHighlightMeshes, moveHighlightMat,
    weaponRangeMeshes,
    spellRangeMeshes, spellZonaMeshes, spellDoubleMeshes, spellAreaMeshes, spellEscuridaoMeshes, spellSilencioMeshes,
    dustPts, dustVel: _dVel, dustXZ: _dXZ, dustY: _dY,
    dustCount: DUST_N, dustCeil: DUST_CEIL,
    W, H, animFrame:null, resizeObs,
    hoverSpot,
    stairGroup,                          // staircase mesh (null if no stairs)
    exitGroup,                           // Fase 3: marcador de saída 🏁 (null se não houver)
    chestMeshes: {},                     // chest_id → THREE.Group
    decorMeshes: {},                     // decor id → THREE.Mesh
    hoveredPos:  null,   // [gx, gy] of figure under cursor, or null
    selectedPos: null    // [gx, gy] of clicked-selected figure, or null
  };

  // ── Initial camera position + first OrbitControls sync ───────────────────
  resetCamera3D();
  resize3D();
  // Quando init3D roda logo após showScreen('screen-game'), o map-wrap pode
  // ainda não ter layout (offsetWidth=0) → o resize acima usa o fallback
  // 640×480. Re-mede após o navegador pintar para corrigir o aspect/escala
  // (a tela preta intermitente costumava vir daqui). O ResizeObserver cobre
  // mudanças posteriores; estes rAFs cobrem o primeiro frame.
  requestAnimationFrame(() => { if(g3) resize3D(); });
  requestAnimationFrame(() => requestAnimationFrame(() => { if(g3) resize3D(); }));
  startLoop3D();

  // ── Drag-guard listeners (detect any button drag → block next click) ──────
  // OrbitControls handles the actual camera movement; we only need to know
  // "did the pointer travel while a button was held?" to suppress tile clicks.
  const domEl = renderer.domElement;
  domEl.addEventListener('mousedown',  () => { _orbitDragMoved = false; });
  domEl.addEventListener('mousemove',  e  => { if(e.buttons) _orbitDragMoved = true; });

  domEl.addEventListener('click',      on3DClick);
  domEl.addEventListener('mousemove',  on3DMouseMove);
  domEl.addEventListener('mouseleave', () => {
    $('tooltip').style.display = 'none';
    if(g3) g3.hoveredPos = null;   // kill hover lift when cursor leaves canvas
  });

  // ── Toque no 3D: OrbitControls cuida de girar/pan/zoom; aqui detectamos um
  // TOQUE CURTO (sem arrastar) e o tratamos como clique para mover/atacar. ──
  let _t3x, _t3y, _t3moved;
  domEl.addEventListener('touchstart', e => {
    if(e.touches.length === 1){ _t3x = e.touches[0].clientX; _t3y = e.touches[0].clientY; _t3moved = 0; }
    else { _t3moved = 999; }   // 2 dedos = gesto de câmera, nunca clique
  }, { passive:true });
  domEl.addEventListener('touchmove', e => {
    if(e.touches.length === 1)
      _t3moved += Math.abs(e.touches[0].clientX - _t3x) + Math.abs(e.touches[0].clientY - _t3y);
  }, { passive:true });
  domEl.addEventListener('touchend', (e) => {
    if(_t3moved < 14){
      e.preventDefault();   // evita o "click" sintético duplicar o movimento
      _orbitDragMoved = false;
      on3DClick({ clientX: _t3x, clientY: _t3y });
    }
  }, { passive:false });
}

// generateTexture(type) → CanvasTexture.  Types: 'wall', 'floor', 'wood'.
// All textures use Math.random() — every session gets unique stone / grain.

function generateTexture(type){
  const T = window.THREE;
  if(!T) return null;
  switch(type){
    case 'wall':  return _mkWallTex(T, 512);
    case 'floor': return _mkFloorTex(T, 512);
    case 'wood':  return _mkWoodTex(T);
    default:      return null;
  }
}

// ── Wall: 512×512 irregular brickwork with mortar, per-block tone variation ──
function _mkWallTex(T, size){
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const c = cv.getContext('2d');

  // Mortar background — slightly blue-dark gap between stone blocks
  c.fillStyle = VC.wall.mortarHex;
  c.fillRect(0, 0, size, size);

  // Brickwork courses: random block height 40–60 px, alternating row offset
  let ry = 0, rowI = 0;
  while(ry < size + 2){
    const rh  = 40 + Math.floor(Math.random() * 21);   // 40–60 px tall
    const off = (rowI % 2 === 0) ? 0 : 55;             // brickwork offset
    let rx = -off;
    while(rx < size + 2){
      const bw = 80 + Math.floor(Math.random() * 41);  // 80–120 px wide
      // Independent ±15 variation per RGB channel
      const r = Math.min(255, Math.max(0, 90 + Math.round((Math.random()-0.5)*30)));
      const g = Math.min(255, Math.max(0, 90 + Math.round((Math.random()-0.5)*30)));
      const b = Math.min(255, Math.max(0, 90 + Math.round((Math.random()-0.5)*30)));
      c.fillStyle = `rgb(${r},${g},${b})`;
      // Inset 1.5 px so the 3px mortar gap is the background showing through
      c.fillRect(rx + 1.5, ry + 1.5, bw - 3, rh - 3);
      rx += bw;
    }
    ry += rh;
    rowI++;
  }

  // Subtle noise dots — simulates rough stone texture
  c.fillStyle = 'rgba(0,0,0,0.03)';
  for(let n = 0; n < 45000; n++){
    c.fillRect(Math.random()*size|0, Math.random()*size|0, 1, 1);
  }

  // Edge vignette — darkens corners so tiling looks atmospheric
  const grad = c.createRadialGradient(size/2,size/2, size*0.28, size/2,size/2, size*0.72);
  grad.addColorStop(0, 'rgba(0,0,0,0)');
  grad.addColorStop(1, 'rgba(0,0,0,0.30)');
  c.fillStyle = grad;
  c.fillRect(0, 0, size, size);

  const tex = new T.CanvasTexture(cv);
  tex.wrapS = tex.wrapT = T.RepeatWrapping;
  return tex;
}

// ── Floor: 512×512 paved stone tiles 64×64 with cracks and bevels ─────────────
function _mkFloorTex(T, size){
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const c = cv.getContext('2d');
  const TILE = 64, N = size / TILE | 0;  // 8 tiles per axis at 512

  // Grout fill — visible mid-dark seam between tiles
  c.fillStyle = VC.floor.groutHex;
  c.fillRect(0, 0, size, size);

  for(let ty = 0; ty < N; ty++){
    for(let tx = 0; tx < N; tx++){
      const px = tx * TILE, py = ty * TILE;

      // Per-tile tone variation ±10
      const v = Math.min(255, Math.max(0, 96 + Math.round((Math.random()-0.5)*20)));
      c.fillStyle = `rgb(${v},${v},${v})`;
      c.fillRect(px+2, py+2, TILE-4, TILE-4);

      // Top-left warm bevel — torch light catches raised tile edge
      c.fillStyle = 'rgba(255,200,120,0.11)';
      c.fillRect(px+2, py+2, TILE-4, 3);
      c.fillRect(px+2, py+2, 3, TILE-4);

      // Bottom-right shadow bevel
      c.fillStyle = 'rgba(0,0,0,0.22)';
      c.fillRect(px+2, py+TILE-5, TILE-4, 3);
      c.fillRect(px+TILE-5, py+2, 3, TILE-4);

      // 15% chance of a diagonal crack
      if(Math.random() < 0.15){
        const cx0 = px + 8 + Math.random()*(TILE-16);
        const cy0 = py + 8 + Math.random()*(TILE-16);
        const a   = Math.PI*0.22 + Math.random()*0.30;
        const len = 12 + Math.random()*18;
        const cx1 = cx0 + Math.cos(a)*len, cy1 = cy0 + Math.sin(a)*len;
        c.strokeStyle = 'rgba(0,0,0,0.42)'; c.lineWidth = 1.2;
        c.beginPath(); c.moveTo(cx0, cy0); c.lineTo(cx1, cy1); c.stroke();
        // Subtle highlight alongside crack edge
        c.strokeStyle = 'rgba(255,255,255,0.10)'; c.lineWidth = 0.8;
        c.beginPath(); c.moveTo(cx0+0.6, cy0+0.6); c.lineTo(cx1+0.6, cy1+0.6); c.stroke();
      }
    }
  }

  // ImageData micro-noise (step 8 px for performance on 512×512)
  const id = c.getImageData(0, 0, size, size);
  const d  = id.data;
  for(let i = 0; i < d.length; i += 32){
    const n = (Math.random()-0.5) * 14;
    d[i]   = Math.min(255, Math.max(0, d[i]   + n));
    d[i+1] = Math.min(255, Math.max(0, d[i+1] + n));
    d[i+2] = Math.min(255, Math.max(0, d[i+2] + n));
  }
  c.putImageData(id, 0, 0);

  const tex = new T.CanvasTexture(cv);
  tex.wrapS = tex.wrapT = T.RepeatWrapping;
  return tex;
}

// ── Wood: 256×512 vertical grain with plank seams and nails (for doors) ───────
function _mkWoodTex(T){
  const W = 256, H = 512;
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const c = cv.getContext('2d');

  // Medium brown base
  c.fillStyle = '#6b3f1f';
  c.fillRect(0, 0, W, H);

  // Vertical grain bands (8–12 px wide, ±20 tone per channel)
  let gx = 0;
  while(gx < W){
    const gw = 8 + Math.floor(Math.random() * 5);
    const v  = Math.round((Math.random()-0.5) * 40);
    const r  = Math.min(255, Math.max(0, 107 + v));
    const g  = Math.min(255, Math.max(0,  63 + Math.round(v * 0.65)));
    const b  = Math.min(255, Math.max(0,  31 + Math.round(v * 0.40)));
    c.fillStyle = `rgb(${r},${g},${b})`;
    c.fillRect(gx, 0, gw, H);
    gx += gw;
  }

  // Thin wavy dark streaks — fine wood grain lines
  c.strokeStyle = 'rgba(0,0,0,0.18)'; c.lineWidth = 0.9;
  for(let s = 0; s < 22; s++){
    const sx   = Math.random() * W;
    const amp  = 1.5 + Math.random() * 3;
    const freq = 0.008 + Math.random() * 0.012;
    c.beginPath(); c.moveTo(sx, 0);
    for(let y = 2; y < H; y += 4){
      c.lineTo(sx + Math.sin(y * freq + Math.random()*0.18) * amp, y);
    }
    c.stroke();
  }

  // Horizontal plank seams (every 120–160 px)
  let sy = 110 + Math.random() * 50;
  while(sy < H){
    c.strokeStyle = 'rgba(0,0,0,0.56)'; c.lineWidth = 1.8;
    c.beginPath(); c.moveTo(0, sy); c.lineTo(W, sy); c.stroke();
    c.strokeStyle = 'rgba(255,200,100,0.13)'; c.lineWidth = 1.0;
    c.beginPath(); c.moveTo(0, sy+1.5); c.lineTo(W, sy+1.5); c.stroke();
    sy += 120 + Math.random() * 40;
  }

  // Nails — dark circle with bright highlight
  for(const ny of [56, H/2-56, H/2+56, H-56]){
    for(const nx of [14, W-14]){
      c.fillStyle = 'rgba(28,16,6,0.82)';
      c.beginPath(); c.arc(nx, ny, 3.5, 0, Math.PI*2); c.fill();
      c.fillStyle = 'rgba(255,210,110,0.32)';
      c.beginPath(); c.arc(nx-1, ny-1, 1.6, 0, Math.PI*2); c.fill();
    }
  }

  // Per-pixel micro noise (step 8 px)
  const id = c.getImageData(0, 0, W, H);
  const d  = id.data;
  for(let i = 0; i < d.length; i += 32){
    const n = (Math.random()-0.5) * 18;
    d[i]   = Math.min(255, Math.max(0, d[i]   + n));
    d[i+1] = Math.min(255, Math.max(0, d[i+1] + Math.round(n * 0.65)));
    d[i+2] = Math.min(255, Math.max(0, d[i+2] + Math.round(n * 0.40)));
  }
  c.putImageData(id, 0, 0);

  const tex = new T.CanvasTexture(cv);
  tex.wrapS = tex.wrapT = T.RepeatWrapping;
  return tex;
}

function dispose3D(){
  if(!g3) return;
  cancelAnimationFrame(g3.animFrame);
  g3.resizeObs.disconnect();
  if(g3.controls) g3.controls.dispose();

  // ── Reset do sistema de dados 3D ──────────────────────────────────────────
  // _d3._diceGroup pertence à cena que está sendo destruída. Sem este reset,
  // na próxima masmorra os dados eram adicionados a um grupo ÓRFÃO (fora da
  // cena nova) e nunca mais apareciam — só o rótulo flutuante era desenhado.
  if(_d3 && _d3.animFrame) cancelAnimationFrame(_d3.animFrame);
  for(const die of _dice3){
    if(die.mat.map) die.mat.map.dispose();
    die.geo.dispose(); die.mat.dispose();
  }
  _dice3.length = 0;
  _d3 = null;

  g3.renderer.dispose();
  const el = g3.renderer.domElement;
  if(el.parentNode) el.parentNode.removeChild(el);
  // Restore map-wrap positioning so the 2D canvas flows normally
  const wrap = $('map-wrap');
  if(wrap) wrap.style.position = '';
  g3 = null;
}

// ── Reset camera to default Diablo-like isometric view ───────────────────────
// Called by the ⌂ button, the R key, and on init3D first frame.
// Moves the camera to SW-above position and snaps OrbitControls target to
// board centre; zoom is reset to 1 so frustum returns to its base size.

function resetCamera3D(){
  if(!g3) return;
  const { W, H, camera, controls } = g3;
  const cx = (W-1)/2, cz = (H-1)/2;
  const d  = Math.max(W, H) * 1.15;
  const az = 225 * Math.PI / 180;   // SW  — classic Diablo look
  const el = 52  * Math.PI / 180;   // ~isometric elevation

  camera.up.set(0, 1, 0);
  camera.position.set(
    cx + d * Math.cos(el) * Math.cos(az),
    d  * Math.sin(el),
    cz + d * Math.cos(el) * Math.sin(az)
  );
  camera.zoom = 1.0;
  camera.updateProjectionMatrix();

  controls.target.set(cx, 0.4, cz);
  controls.update();
}

function resize3D(){
  if(!g3) return;
  const wrap = $('map-wrap');
  // offsetWidth/Height includes the padding so the canvas fills the full container.
  const CW = wrap.offsetWidth, CH = wrap.offsetHeight;
  if(!CW || !CH) return;
  const { W, H, camera, renderer } = g3;
  const aspect = CW / CH;
  // Base frustum half-height — zoom handled by OrbitControls via camera.zoom.
  const fH = Math.max(W, H) * 0.60;
  camera.left   = -fH * aspect;  camera.right  = fH * aspect;
  camera.top    =  fH;           camera.bottom = -fH;
  camera.updateProjectionMatrix();
  renderer.setSize(CW, CH);
}

function startLoop3D(){
  function tick(){
    if(!g3) return;
    g3.animFrame = requestAnimationFrame(tick);
    const t = Date.now();

    // ── OrbitControls damping (pausado durante o seguimento de câmera) ───────
    if(!configCamera.seguindoPeao) g3.controls.update();
    atualizarCamera();   // seguimento suave do peão (quando ativo)

    // ── Player torch flicker (two sine waves for organic feel) ──────────────
    g3.torch.intensity = 8.5 + Math.sin(t/112)*1.0 + Math.sin(t/197)*0.7;

    // ── Wall torch flicker (each torch has a random phase offset) ───────────
    if(g3.wallTorches){
      for(const wt of g3.wallTorches){
        if(!wt.group.visible) continue;
        // Two overlapping sine waves → irregular organic crackle
        const fl = Math.sin(t*0.003  + wt.offset)*0.28
                 + Math.sin(t*0.0071 + wt.offset*1.3)*0.10;
        wt.light.intensity = 3.8 + fl;
        if(wt.flames){
          for(const cone of wt.flames){
            const subFl = fl + Math.sin(t*0.005 + cone.userData.subOffset)*0.12;
            if(cone.material) cone.material.emissiveIntensity = (cone.userData.baseEmissive||2.0) + subFl;
            cone.scale.y = 1.0 + subFl * 0.18;
          }
        }
      }
    }

    // ── Glowing grout pulse (trap-room magic rune lines) ─────────────────────
    if(g3.groutMats){
      const gp = 0.5 + 0.5 * Math.sin(t / 820);   // slow, deep purple breath
      for(const mat of g3.groutMats)
        mat.emissiveIntensity = 0.35 + gp * 0.90;
    }

    // ── Movement highlight pulse (blue overlay planes — slow sine breath) ───────
    if(g3.moveHighlightMat){
      const pulse = 0.5 + 0.5 * Math.sin(t / 420);
      g3.moveHighlightMat.opacity = 0.36 + 0.40 * pulse;
    }

    // ── Floating dust motes (upward drift, reset at ceiling, re-randomise XZ) ─
    if(g3.dustPts && g3.dustPts.visible){
      const attr = g3.dustPts.geometry.attributes.position;
      for(let i = 0; i < g3.dustCount; i++){
        g3.dustY[i] += g3.dustVel[i];
        if(g3.dustY[i] > g3.dustCeil){
          g3.dustY[i]      = 0;
          g3.dustXZ[i*2]   = Math.random() * g3.W;    // respawn at new XZ
          g3.dustXZ[i*2+1] = Math.random() * g3.H;
        }
        attr.array[i*3]   = g3.dustXZ[i*2];
        attr.array[i*3+1] = g3.dustY[i];
        attr.array[i*3+2] = g3.dustXZ[i*2+1];
      }
      attr.needsUpdate = true;
    }

    if(g3.stairGroup && g3.stairGroup.visible){
      const sp=0.45+0.55*Math.sin(t/600);
      g3.stairGroup.traverse(c=>{
        if(c.userData.isStairGlow&&c.material) c.material.emissiveIntensity=0.30+0.55*sp;
      });
    }

    // ── Chest glow pulse (golden shimmer on floor around each chest) ──────────
    if(g3.chestMeshes){
      const cp = 0.5 + 0.5 * Math.sin(t / 480);   // ~3 s breath cycle
      for(const grp of Object.values(g3.chestMeshes)){
        if(!grp.visible) continue;
        grp.traverse(c => {
          if(c.userData.isChestGlow && c.material){
            c.material.emissiveIntensity = 0.8 + 1.2 * cp;
            c.material.opacity = 0.25 + 0.30 * cp;
          }
        });
      }
    }

    // pulse: 0 → 1 → 0 on a ~2.2 s cycle.  Ring breathes in XZ; light fades.
    const pulse = 0.5 + 0.5 * Math.sin(t / 350);
    g3.entityGroup.traverse(child => {
      if(child.userData.isPulseRing){
        const s = 1.0 + 0.14 * pulse;
        child.scale.set(s, 1, s);
        child.material.emissiveIntensity = 1.1 + 1.1 * pulse;
      } else if(child.userData.isHaloLight){
        child.intensity = 0.7 + 1.0 * pulse;
      }
    });

    // Each figure Group (direct child of entityGroup) tagged with gridX/gridY:
    //   • Hover  → smooth Y-lift toward 0.15 units + dim gold vitrine spotlight
    //   • Select → slow Y-axis spin (ring glows by emissive; no extra light needed)
    const hovP  = g3.hoveredPos;
    const selP  = g3.selectedPos;
    const hspot = g3.hoverSpot;
    let hovFigY = 0.30;   // world-Y for the vitrine light (default when not hovering)
    g3.entityGroup.children.forEach(fig => {
      if(fig.type !== 'Group') return;
      // Não interfere no peão em movimento — _animarPasso controla o Y dele.
      if(estadoMovimento.emMovimento && fig === estadoMovimento.peaoAtivo) return;
      const gx = fig.userData.gridX, gy = fig.userData.gridY;
      if(gx === undefined) return;
      const isHov = hovP && gx === hovP[0] && gy === hovP[1];
      const isSel = selP && gx === selP[0] && gy === selP[1];
      // Smooth vertical lift (lerp coefficient 0.14 ≈ snappy but not instant)
      const targetY = isHov ? 0.15 : 0;
      fig.position.y += (targetY - fig.position.y) * 0.14;
      if(isHov) hovFigY = fig.position.y + 0.30;   // light tracks above base
      // Slow Y-rotation while selected (~3 rpm)
      if(isSel) fig.rotation.y += 0.008;
    });
    // Fade vitrine spotlight in/out
    if(hovP && hspot){
      hspot.position.set(hovP[0], hovFigY, hovP[1]);
      hspot.intensity += (0.60 - hspot.intensity) * 0.18;
    } else if(hspot){
      hspot.intensity *= 0.82;   // fast fade-out
    }

    // Portrait is HTML-only (class selection screen). Never meshes on the board.

    g3.renderer.render(g3.scene, g3.camera);
  }
  tick();
}

// ── Scene update (called wherever renderMap() is called) ─────────────────────

// Builds door arches, pillars, wood door panels, corner columns and baseboards.
// Returns a dict: tile-key → [mesh, ...] for fog-of-war visibility management.
// Called once from init3D; meshes start hidden (visible = false).
function buildWallDetails(T, scene, state, wallTex, TW, TH, WH){
  const tiles = state.tiles;
  const H = tiles.length, W = tiles[0].length;
  const det = {};

  // Stone material matching wallBaseMat, brightness-adjustable
  const mkSt = (v) => {
    const m = new T.MeshStandardMaterial({
      map: wallTex, roughnessMap: wallTex, roughness: 0.92, metalness: 0.04
    });
    m.color.setRGB(0.52*v, 0.50*v, 0.47*v);
    return m;
  };
  const woodTex  = generateTexture('wood');
  const woodMat  = new T.MeshStandardMaterial({
    map: woodTex, color: new T.Color(0x2a1208), roughness: 0.95, metalness: 0
  });
  const hingeMat = new T.MeshStandardMaterial({
    color: new T.Color(0x7a5a1a), roughness: 0.50, metalness: 0.84
  });

  const add = (key, mesh) => {
    mesh.receiveShadow = true;
    mesh.visible = false;
    scene.add(mesh);
    (det[key] = det[key] || []).push(mesh);
  };

  // Arch peak = WH exactly: pilH + 2*archR = WH - TH
  const archR  = 0.36;                     // arch major radius
  const archT  = 0.09;                     // arch tube radius
  const pilH   = WH - TH - 2 * archR;     // pillar height = 0.81
  const archCY = TH + pilH + archR;        // arch center Y = 1.39
  const pilCY  = TH + pilH * 0.5;         // pillar center Y = 0.625
  const doorW  = archR * 1.85;             // door panel width = 0.666

  const bsH  = 0.055;                      // baseboard height
  const bsDp = 0.10;                       // baseboard depth (from wall face)
  const bsY  = TH + bsH * 0.5;            // center Y (sits on floor surface)
  const bsFO = TW * 0.5 - bsDp * 0.30;   // wall-face offset (slight protrusion)

  // ── Shared geometries (one instance, many meshes via clone/direct reuse) ──
  const pilGeo = new T.BoxGeometry(0.22, pilH, 0.22);
  const colGeo = new T.CylinderGeometry(0.11, 0.14, WH, 8);
  const hinGeo = new T.CylinderGeometry(0.030, 0.030, 0.14, 6);
  const bsGX   = new T.BoxGeometry(TW + 0.04, bsH, bsDp);  // baseboard N/S faces
  const bsGZ   = new T.BoxGeometry(bsDp, bsH, TW + 0.04);  // baseboard E/W faces

  // ── Helper: count floor-tile orthogonal neighbors of tile (fx,fy) ─────────
  const floorNeighbors = (fx, fy) =>
    [[0,-1],[0,1],[1,0],[-1,0]].reduce((acc,[dx,dy]) => {
      const nx=fx+dx, ny=fy+dy;
      return acc + (nx>=0&&ny>=0&&nx<W&&ny<H&&tiles[ny][nx]===TILE_FLOOR ? 1 : 0);
    }, 0);

  for(let y = 0; y < H; y++){
    for(let x = 0; x < W; x++){
      const tile = tiles[y][x];
      const key  = `${x},${y}`;

      const gT  = (dx,dy) => { const nx=x+dx,ny=y+dy; return (nx>=0&&ny>=0&&nx<W&&ny<H)?tiles[ny][nx]:TILE_WALL; };
      const isW = (dx,dy) => gT(dx,dy) === TILE_WALL;
      const isF = (dx,dy) => gT(dx,dy) === TILE_FLOOR;

      if(tile === TILE_FLOOR){
        const wN=isW(0,-1), wS=isW(0,1), wE=isW(1,0), wW=isW(-1,0);
        const wCnt = (wN?1:0)+(wS?1:0)+(wE?1:0)+(wW?1:0);

        // Door = floor tile with walls on exactly 2 opposite sides,
        // and at least one open side leads to a wider area (≥3 floor neighbours = room tile)
        let axis = null;
        if(wCnt===2 && wN && wS){
          // Passage runs E-W; check if E or W side opens into a room
          const eRoom = isF(1,0)  && floorNeighbors(x+1, y) >= 3;
          const wRoom = isF(-1,0) && floorNeighbors(x-1, y) >= 3;
          if(eRoom || wRoom) axis = 'NS';
        } else if(wCnt===2 && wE && wW){
          const nRoom = isF(0,-1) && floorNeighbors(x, y-1) >= 3;
          const sRoom = isF(0, 1) && floorNeighbors(x, y+1) >= 3;
          if(nRoom || sRoom) axis = 'EW';
        }

        if(axis){
          // ── Stone arch: 7 individual voussoir BoxGeometry blocks in a fan ──
          // Each stone is tangentially rotated to follow the arc curvature.
          // Keystone (centre, i=3) is slightly brighter; blocks alternate tone.
          try{
            const N      = 7;
            const arcStp = archR * Math.PI / (N - 1);   // arc length per stone
            const stoneW = arcStp * 0.78;                // tangential width (gap for mortar)
            const stoneH = 0.17;                         // radial depth
            const stoneDp= archT * 2.2;                  // depth through arch thickness
            const archGrp = new T.Group();
            archGrp.position.set(x, archCY, y);
            // NS door: arch must span Z (N-S) — rotate group 90° around Y
            // EW door: arch spans X by default, no rotation needed
            if(axis === 'NS') archGrp.rotation.y = Math.PI / 2;
            for(let i = 0; i < N; i++){
              const θ  = i * Math.PI / (N - 1);    // 0 = right foot → π = left foot
              const cx = archR * Math.cos(θ);       // local X in arch plane
              const cy = archR * Math.sin(θ);       // local Y (up)
              const isKey = (i === Math.floor(N / 2));
              const stone = new T.Mesh(
                new T.BoxGeometry(stoneW, stoneH, stoneDp),
                mkSt(isKey ? 1.18 : (i % 2 === 0 ? 0.94 : 1.06))
              );
              stone.position.set(cx, cy, 0);
              stone.rotation.z = Math.PI / 2 + θ;  // tangential alignment
              stone.receiveShadow = true;
              archGrp.add(stone);
            }
            add(key, archGrp);
          }catch(e){}

          const pPos = axis === 'NS'
            ? [[x, pilCY, y-archR], [x, pilCY, y+archR]]
            : [[x-archR, pilCY, y], [x+archR, pilCY, y]];
          for(const [px,py,pz] of pPos){
            try{
              const pm = new T.Mesh(pilGeo, mkSt(1.06));
              pm.position.set(px, py, pz);
              add(key, pm);
            }catch(e){}
          }

          // ── Wood door panel (recessed 0.05 into passage) ─────────────────
          try{
            const dGeo = axis === 'NS'
              ? new T.BoxGeometry(doorW, pilH, 0.065)   // door face visible from E/W
              : new T.BoxGeometry(0.065, pilH, doorW);  // door face visible from N/S
            const dm = new T.Mesh(dGeo, woodMat.clone());
            dm.position.set(
              x + (axis === 'EW' ? 0.05 : 0),
              TH + pilH * 0.5,
              y + (axis === 'NS' ? 0.05 : 0)
            );
            add(key, dm);
          }catch(e){}

          // ── Hinges (2 aged-gold cylinders on the hinge-side pillar face) ──
          for(const hFrac of [0.26, 0.70]){
            try{
              const hm = new T.Mesh(hinGeo, hingeMat.clone());
              const hY = TH + pilH * hFrac;
              if(axis === 'NS'){
                hm.rotation.z = Math.PI / 2;  // cylinder axis → X (horizontal)
                hm.position.set(x + doorW*0.5 + 0.025, hY, y - archR + 0.06);
              } else {
                hm.rotation.x = Math.PI / 2;  // cylinder axis → Z (horizontal)
                hm.position.set(x - archR + 0.06, hY, y + doorW*0.5 + 0.025);
              }
              add(key, hm);
            }catch(e){}
          }
        }
      }

      // ── WALL TILE: baseboards on every floor-adjacent face ───────────────
      else if(tile === TILE_WALL){
        if(isF(0, 1)){  // floor to south
          try{ const bs=new T.Mesh(bsGX, mkSt(0.70)); bs.position.set(x, bsY, y+bsFO); add(key,bs); }catch(e){}
        }
        if(isF(0,-1)){  // floor to north
          try{ const bs=new T.Mesh(bsGX, mkSt(0.70)); bs.position.set(x, bsY, y-bsFO); add(key,bs); }catch(e){}
        }
        if(isF(1, 0)){  // floor to east
          try{ const bs=new T.Mesh(bsGZ, mkSt(0.70)); bs.position.set(x+bsFO, bsY, y); add(key,bs); }catch(e){}
        }
        if(isF(-1,0)){  // floor to west
          try{ const bs=new T.Mesh(bsGZ, mkSt(0.70)); bs.position.set(x-bsFO, bsY, y); add(key,bs); }catch(e){}
        }
      }
    }
  }

  // At each 2×2 block of tiles, add a column where exactly 3 walls meet 1 floor
  // (the classic dungeon inner-corner with an L-shaped wall junction).
  // Column sits in the inter-tile gap at (gx+0.5, WH/2, gy+0.5), always visible.
  for(let gy = 0; gy < H-1; gy++){
    for(let gx = 0; gx < W-1; gx++){
      const tNW = tiles[gy][gx],   tNE = tiles[gy][gx+1];
      const tSW = tiles[gy+1][gx], tSE = tiles[gy+1][gx+1];
      const wCnt = (tNW===TILE_WALL?1:0)+(tNE===TILE_WALL?1:0)+
                   (tSW===TILE_WALL?1:0)+(tSE===TILE_WALL?1:0);

      // Only handle 3-walls-1-floor intersections (true inner corners)
      if(wCnt !== 3) continue;

      // The visibility key is the single floor tile in this 2×2 block
      let visKey = null;
      for(const [dx,dy] of [[0,0],[1,0],[0,1],[1,1]]){
        const nx=gx+dx, ny=gy+dy;
        if(tiles[ny][nx] === TILE_FLOOR){ visKey=`${nx},${ny}`; break; }
      }
      if(!visKey) continue;

      try{
        const col = new T.Mesh(colGeo, mkSt(1.12));
        col.position.set(gx + 0.5, WH * 0.5, gy + 0.5);
        add(visKey, col);
      }catch(e){}
    }
  }

  return det;
}

// ── Per-room wall torches (bracket + flame + animated PointLight) ─────────────
// Selects 1–2 wall tiles per room and places a full torch assembly on each.
// wallTorches entries: { group, light, flame, offset, wallKey }
// L-shaped iron bracket via CatmullRomCurve3 + TubeGeometry
// Flattened TorusGeometry rusty bowl
// 3 overlapping ConeGeometry fire cones with independent Y-scale animation
function buildRoomTorches(T, scene, state, wallTorches, TW, TH, WH){
  if(!state.rooms || !state.tiles) return;
  const tiles = state.tiles;
  const H = tiles.length, W = tiles[0].length;

  // Iron material — dark rusty iron
  const ironMat = new T.MeshStandardMaterial({
    color: new T.Color(0x3a2010), roughness: 0.84, metalness: 0.55
  });

  for(const room of state.rooms){
    const {x: rx, y: ry, w: rw, h: rh} = room;

    // Collect wall-tile candidates on every boundary side
    const cands = [];
    for(let tx=rx; tx<rx+rw; tx++){
      const ty=ry-1;
      if(ty>=0 && tiles[ty][tx]===TILE_WALL && tiles[ry][tx]===TILE_FLOOR)
        cands.push({wx:tx, wy:ty, fdx:0, fdz:1});
    }
    for(let tx=rx; tx<rx+rw; tx++){
      const ty=ry+rh;
      if(ty<H && tiles[ty][tx]===TILE_WALL && tiles[ry+rh-1][tx]===TILE_FLOOR)
        cands.push({wx:tx, wy:ty, fdx:0, fdz:-1});
    }
    for(let ty=ry; ty<ry+rh; ty++){
      const tx=rx-1;
      if(tx>=0 && tiles[ty][tx]===TILE_WALL && tiles[ty][rx]===TILE_FLOOR)
        cands.push({wx:tx, wy:ty, fdx:1, fdz:0});
    }
    for(let ty=ry; ty<ry+rh; ty++){
      const tx=rx+rw;
      if(tx<W && tiles[ty][tx]===TILE_WALL && tiles[ty][rx+rw-1]===TILE_FLOOR)
        cands.push({wx:tx, wy:ty, fdx:-1, fdz:0});
    }
    if(!cands.length) continue;

    // Deterministic pick: 1 torch for small rooms, 2 for larger
    const hash = ((room.cx*7919)^(room.cy*3467)) & 0xFFFF;
    const nPick = (rw+rh >= 8 && cands.length >= 3) ? 2 : 1;
    const i1 = hash % cands.length;
    const i2 = (i1 + Math.floor(cands.length/2)) % cands.length;
    const picks = [cands[i1]];
    if(nPick === 2 && i2 !== i1) picks.push(cands[i2]);

    for(const {wx, wy, fdx, fdz} of picks){
      const grp = new T.Group();
      grp.position.set(wx + fdx*0.38, WH*0.50, wy + fdz*0.38);

      // ── L-shaped iron bracket via CatmullRomCurve3 ─────────────────────
      try{
        const curve = new T.CatmullRomCurve3([
          new T.Vector3(0,         0.02,         0),
          new T.Vector3(fdx*0.04,  0.03,  fdz*0.04),
          new T.Vector3(fdx*0.11,  0.055, fdz*0.11),
          new T.Vector3(fdx*0.15,  0.08,  fdz*0.15)
        ]);
        const brkMesh = new T.Mesh(
          new T.TubeGeometry(curve, 10, 0.013, 5, false),
          ironMat.clone()
        );
        brkMesh.receiveShadow = true;
        grp.add(brkMesh);
      }catch(e){}

      try{
        const bowl = new T.Mesh(
          new T.TorusGeometry(0.063, 0.025, 5, 12),
          ironMat.clone()
        );
        bowl.rotation.x = Math.PI / 2;   // lay ring flat
        bowl.scale.y    = 0.40;           // squash into shallow cup
        bowl.position.set(fdx*0.15, 0.11, fdz*0.15);
        bowl.receiveShadow = true;
        grp.add(bowl);
      }catch(e){}

      const fx = fdx*0.15, fz = fdz*0.15;
      const coneSpecs = [
        { r:0.046, h:0.18, col:0xff5500, em:0xff3300, ei:2.0, dy:0.000, ry: 0.00, rx: 0.00 },
        { r:0.030, h:0.16, col:0xff8800, em:0xff6600, ei:2.2, dy:0.010, ry: 1.00, rx: 0.10 },
        { r:0.018, h:0.13, col:0xffee80, em:0xffcc00, ei:2.5, dy:0.022, ry:-1.00, rx:-0.10 },
      ];
      const flames = [];
      for(const sp of coneSpecs){
        try{
          const cm = new T.Mesh(
            new T.ConeGeometry(sp.r, sp.h, 5),
            new T.MeshStandardMaterial({
              color: new T.Color(sp.col), emissive: new T.Color(sp.em),
              emissiveIntensity: sp.ei, roughness: 0.30, metalness: 0
            })
          );
          cm.position.set(fx, 0.16 + sp.dy, fz);
          cm.rotation.y = sp.ry;
          cm.rotation.x = sp.rx;
          cm.userData.baseEmissive = sp.ei;
          cm.userData.subOffset    = flames.length * 1.37;  // phase spread: 0 / 1.37 / 2.74 rad
          grp.add(cm);
          flames.push(cm);
        }catch(e){}
      }

      // castShadow is OFF for room torches — each castShadow PointLight needs
      // 6 cubemap shadow passes; with 10+ rooms this overflows WebGL resources.
      // Shadow casting is handled solely by the player's moving torch.
      const pl = new T.PointLight(0xff8800, 2.2, 5.5, 2.0);
      pl.position.set(fx, 0.28, fz);
      grp.add(pl);

      grp.visible = false;
      scene.add(grp);
      wallTorches.push({
        group:   grp,
        light:   pl,
        flames:  flames,
        offset:  ((wx*7919 ^ wy*3467) & 0xFF) / 255 * Math.PI * 2,
        wallKey: `${wx},${wy}`
      });
    }
  }
}

// ── Room floor colour overlays (translucent planes per room role) ─────────────
// chest → golden glow  |  boss → ominous dark red  |  trap → arcane purple
// Each floor tile inside the room gets a PlaneGeometry overlay slightly above it.
function buildRoomOverlays(T, scene, state, roomOverlayMeshes, TW, TH){
  if(!state.rooms || !state.tiles) return;
  const tiles = state.tiles;
  const H = tiles.length, W = tiles[0].length;

  const roleSpec = {
    chest: { color: 0xc8a030, opacity: 0.30 },
    boss:  { color: 0x6a1a1a, opacity: 0.20 },
    trap:  { color: 0x4a2a6a, opacity: 0.25 },
  };

  // One shared plane geometry, materials per role
  const planeGeo = new T.PlaneGeometry(TW * 0.92, TW * 0.92);
  const matCache = {};

  for(const room of state.rooms){
    const spec = roleSpec[room.role];
    if(!spec) continue;

    if(!matCache[room.role]){
      matCache[room.role] = new T.MeshBasicMaterial({
        color:       new T.Color(spec.color),
        transparent: true,
        opacity:     spec.opacity,
        depthWrite:  false,
        side:        T.DoubleSide
      });
    }
    const mat = matCache[room.role];

    for(let ty=room.y; ty<room.y+room.h; ty++){
      for(let tx=room.x; tx<room.x+room.w; tx++){
        if(ty<0||ty>=H||tx<0||tx>=W) continue;
        if(tiles[ty][tx] !== TILE_FLOOR) continue;
        const key = `${tx},${ty}`;
        if(roomOverlayMeshes[key]) continue;  // already has overlay (room overlap)
        const m = new T.Mesh(planeGeo, mat);
        m.rotation.x = -Math.PI / 2;
        m.position.set(tx, TH + 0.004, ty);  // float 4mm above floor surface
        m.visible = false;
        scene.add(m);
        roomOverlayMeshes[key] = m;
      }
    }
  }
}

// ── Scenery barrels — CylinderGeometry + TorusGeometry hoops at room corners ──
function buildSceneryBarrels(T, scene, state, TW, TH, WH){
  if(!state.rooms || !state.tiles) return {};
  const tiles = state.tiles;
  const mapH = tiles.length, mapW = tiles[0].length;
  const sceneryMeshes = {};

  const woodMat = new T.MeshStandardMaterial({
    color: new T.Color(0x4a2a10), roughness: 0.90, metalness: 0.05
  });
  const hoopMat = new T.MeshStandardMaterial({
    color: new T.Color(0x282828), roughness: 0.70, metalness: 0.65
  });
  // Shared geometries (reused across all barrels)
  const bodyGeo = new T.CylinderGeometry(0.11, 0.13, 0.28, 10);
  const lidGeo  = new T.CylinderGeometry(0.11, 0.11, 0.03, 10);
  const baseGeo = new T.CylinderGeometry(0.13, 0.13, 0.02, 10);
  const hoopGeo = new T.TorusGeometry(0.12, 0.013, 5, 12);

  for(const room of state.rooms){
    const {x: rx, y: ry, w: rw, h: rh} = room;

    // Collect L-corner floor tiles inside this room
    const corners = [];
    for(let fy=ry; fy<ry+rh; fy++){
      for(let fx=rx; fx<rx+rw; fx++){
        if(tiles[fy][fx] !== TILE_FLOOR) continue;
        const wallN = (fy > 0)       && tiles[fy-1][fx] === TILE_WALL;
        const wallS = (fy < mapH-1)  && tiles[fy+1][fx] === TILE_WALL;
        const wallW = (fx > 0)       && tiles[fy][fx-1] === TILE_WALL;
        const wallE = (fx < mapW-1)  && tiles[fy][fx+1] === TILE_WALL;
        // Only perpendicular pairs (L-corners), not opposite pairs (corridors)
        if     (wallN && wallW) corners.push({fx, fy, ox:-0.21, oz:-0.21});
        else if(wallN && wallE) corners.push({fx, fy, ox: 0.21, oz:-0.21});
        else if(wallS && wallW) corners.push({fx, fy, ox:-0.21, oz: 0.21});
        else if(wallS && wallE) corners.push({fx, fy, ox: 0.21, oz: 0.21});
      }
    }
    if(!corners.length) continue;

    // Deterministic pick: 1 barrel for small rooms, up to 2 for larger
    const hash = ((room.cx * 5381) ^ (room.cy * 2731)) & 0xFFFF;
    const nPick = (rw+rh >= 8 && corners.length >= 2) ? 2 : 1;
    const i1 = hash % corners.length;
    const i2 = (i1 + Math.floor(corners.length / 2)) % corners.length;
    const picks = [corners[i1]];
    if(nPick === 2 && i2 !== i1) picks.push(corners[i2]);

    for(const {fx, fy, ox, oz} of picks){
      const key = `${fx},${fy}`;
      const grp = new T.Group();

      // Deterministic Y rotation for variety
      const rotHash = ((fx * 4127) ^ (fy * 6311)) & 0xFF;
      grp.rotation.y = (rotHash / 255) * Math.PI * 0.5 - Math.PI * 0.25;
      grp.position.set(fx + ox, TH, fy + oz);

      // Body (tapered cylinder)
      const body = new T.Mesh(bodyGeo, woodMat);
      body.position.y = 0.14;   // half-height above base
      body.castShadow = true;
      grp.add(body);

      // Lid cap
      const lid = new T.Mesh(lidGeo, woodMat);
      lid.position.y = 0.295;   // body top + half of lid
      lid.castShadow = true;
      grp.add(lid);

      // Base disc
      const base = new T.Mesh(baseGeo, woodMat);
      base.position.y = 0.01;
      grp.add(base);

      // 3 metal hoops — evenly spaced vertically
      for(const hy of [0.07, 0.14, 0.21]){
        const hoop = new T.Mesh(hoopGeo, hoopMat);
        hoop.rotation.x = Math.PI / 2;   // lay flat around barrel
        hoop.position.y = hy;
        grp.add(hoop);
      }

      grp.visible = false;
      scene.add(grp);
      if(!sceneryMeshes[key]) sceneryMeshes[key] = [];
      sceneryMeshes[key].push(grp);
    }
  }
  return sceneryMeshes;
}

// ── Glowing grout — emissive rune lines on trap/magic room floor grids ────────
function buildGlowingGrout(T, scene, state, TW, TH){
  if(!state.rooms || !state.tiles) return { meshes:{}, mats:[] };
  const tiles = state.tiles;

  // Single shared emissive material — animated in startLoop3D
  const groutMat = new T.MeshStandardMaterial({
    color:    new T.Color(0x5500aa),
    emissive: new T.Color(0xaa00ff),
    emissiveIntensity: 0.6,
    roughness: 0.5, metalness: 0,
    transparent: true, opacity: 0.80,
    depthWrite: false
  });

  // Two strip orientations — horizontal (N/S edges) and vertical (W/E edges)
  const hGeo = new T.BoxGeometry(TW * 0.88, 0.007, 0.09);  // E–W strip
  const vGeo = new T.BoxGeometry(0.09, 0.007, TW * 0.88);  // N–S strip

  const groutMeshes = {};

  for(const room of state.rooms){
    if(room.role !== 'trap') continue;   // only in magic / trap rooms
    const {x: rx, y: ry, w: rw, h: rh} = room;

    for(let fy=ry; fy<ry+rh; fy++){
      for(let fx=rx; fx<rx+rw; fx++){
        if(tiles[fy][fx] !== TILE_FLOOR) continue;
        const key = `${fx},${fy}`;
        const meshes = [];

        // N grout edge (top border of this tile)
        const mN = new T.Mesh(hGeo, groutMat);
        mN.position.set(fx, TH + 0.006, fy - 0.5);
        mN.visible = false;
        scene.add(mN);
        meshes.push(mN);

        // W grout edge (left border of this tile)
        const mW = new T.Mesh(vGeo, groutMat);
        mW.position.set(fx - 0.5, TH + 0.006, fy);
        mW.visible = false;
        scene.add(mW);
        meshes.push(mW);

        groutMeshes[key] = meshes;
      }
    }
  }
  return { meshes: groutMeshes, mats: [groutMat] };
}

// Returns a THREE.Group placed at (chest.pos[0], 0.22, chest.pos[1]).
// Call once per chest; manage visibility externally via .visible.
function buildChest3D(T, chest){
  const TH = 0.22;   // floor tile top surface
  const grp = new T.Group();
  grp.position.set(chest.pos[0], TH, chest.pos[1]);
  grp.userData.chestId = chest.id;

  const woodMat = new T.MeshStandardMaterial({
    color: new T.Color(0x4a2008), roughness: 0.95, metalness: 0.0
  });
  const metalMat = new T.MeshStandardMaterial({
    color: new T.Color(0x9a7820), roughness: 0.30, metalness: 0.88
  });
  const glowMat = new T.MeshStandardMaterial({
    color:    new T.Color(0xffaa00),
    emissive: new T.Color(0xffaa00),
    emissiveIntensity: 1.0,
    transparent: true, opacity: 0.40, depthWrite: false
  });

  // Body
  const body = new T.Mesh(new T.BoxGeometry(0.50, 0.22, 0.36), woodMat);
  body.position.set(0, 0.11, 0);
  body.castShadow = body.receiveShadow = true;
  grp.add(body);

  // Lid (slightly open — hinged at back)
  const lid = new T.Mesh(new T.BoxGeometry(0.50, 0.11, 0.36), woodMat);
  lid.position.set(0, 0.26, -0.09);
  lid.rotation.x = -0.38;   // ~22° open
  lid.castShadow = lid.receiveShadow = true;
  grp.add(lid);

  // Front metal strap
  const strap = new T.Mesh(new T.BoxGeometry(0.52, 0.035, 0.035), metalMat);
  strap.position.set(0, 0.14, 0.185);
  grp.add(strap);

  // Horizontal corner bands (top/bottom of body)
  for(const y of [0.03, 0.20]){
    const band = new T.Mesh(new T.BoxGeometry(0.52, 0.03, 0.38), metalMat);
    band.position.set(0, y, 0);
    grp.add(band);
  }

  // Lock hasp
  const lock = new T.Mesh(new T.BoxGeometry(0.09, 0.09, 0.06), metalMat);
  lock.position.set(0, 0.235, 0.19);
  grp.add(lock);

  // Gold glow halo on the floor around the chest
  const glow = new T.Mesh(new T.PlaneGeometry(0.90, 0.90), glowMat);
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(0, 0.004, 0);   // just above floor surface
  glow.userData.isChestGlow = true;
  grp.add(glow);

  return grp;
}

// ═══════════════════════════════════════════════════════════════════════════
// MOVIMENTO ANIMADO DO PEÃO (3D) — segue o caminho do pathfinding, casa por
// casa, com fases levantar/avançar/pousar. Anima LOCALMENTE e só então envia
// os passos ao servidor (durante a animação não chega game_state, então o mesh
// do peão persiste). Bloqueia input enquanto anima.
// Adaptações ao código real: tile==world (casaParaMundo = identidade);
// getPeaoMesh busca no g3.entityGroup (peões taggeados com userData.pid);
// som de passo via playImpact. O consumo de fome/sede NÃO é feito aqui — é
// autoritativo no servidor (sistema unificado _consumir_recursos).
// ═══════════════════════════════════════════════════════════════════════════
const estadoMovimento = {
  emMovimento: false,
  filaCaminho: [],
  peaoAtivo:   null,
  heroi:       null,
  onConclucao: null,
};

// ── Estado de animação de movimentação dos minions (elementais/animados) ──────
// Bloqueia input da mesma forma que estadoMovimento durante animação de peão.
const estadoMininoMov = {
  emMovimento: false,
  peaoAtivo:   null,   // Three.js Group durante animação 3D
  onConclucao: null,
};

// map animadoId → {fromX,fromY,toX,toY,startTime,dur,onDone} — estado de anim 2D
const _mininoAnimState = new Map();
let   _mininoAnimRafId = null;

function podeReceberInput(){
  return !estadoMovimento.emMovimento && !estadoMininoMov.emMovimento;
}

// tile (x,y) → world (x,0,z). O tabuleiro usa 1 unidade por casa (identidade).
function casaParaMundo(x, z){ return { x: x, y: 0, z: z }; }

// Mesh (Group) do peão de um jogador no entityGroup 3D (taggeado por pid).
function getPeaoMesh(pid){
  if(!g3 || !g3.entityGroup) return null;
  return g3.entityGroup.children.find(c => c.userData && c.userData.pid === pid) || null;
}

// Mesh (Group) de um minion/animado no entityGroup 3D (taggeado por animadoId).
function getAnimadoMesh(animadoId){
  if(!g3 || !g3.entityGroup) return null;
  return g3.entityGroup.children.find(c => c.userData && c.userData.animadoId === animadoId) || null;
}

// Mesh (Group) de um monstro inimigo no entityGroup 3D (taggeado por monId).
function getMonsterMesh(monId){
  if(!g3 || !g3.entityGroup) return null;
  return g3.entityGroup.children.find(c => c.userData && c.userData.monId === monId) || null;
}

// Mesh (Group) do prisioneiro no entityGroup 3D (taggeado por userData.prisoner).
function getPrisonerMesh(){
  if(!g3 || !g3.entityGroup) return null;
  return g3.entityGroup.children.find(c => c.userData && c.userData.prisoner) || null;
}

// ── Deslize fiel passo-a-passo de inimigos / servos auto-comandados ──────────
// O servidor emite `entity_step` (from→to, 1 casa) a cada STEP_ANIM_DELAY. O
// cliente interpola por TEMPO a partir de um startTime fixo, acumulando os
// waypoints conforme chegam — assim acompanha o ritmo do servidor sem acumular
// atraso. Vale p/ 2D (override de posição no render) e 3D (reposiciona o mesh +
// leve "saltinho" do peão, o mesmo efeito de movimentação dos heróis).
const _serverStepAnim = new Map();   // id -> { pts:[[x,y]...], startTime, segDur }
let   _serverStepRaf  = null;
const SERVER_STEP_DUR_MS = 150;      // duração por casa (≥ STEP_ANIM_DELAY do servidor)

function _onEntityStep(msg){
  const id = msg.id, frm = msg.from, to = msg.to;
  const ent = _serverStepAnim.get(id);
  if(ent && ent.pts.length){
    const last = ent.pts[ent.pts.length - 1];
    // Encadeia se o novo passo continua de onde parou; senão recomeça limpo.
    if(last[0]===frm[0] && last[1]===frm[1]) ent.pts.push(to);
    else _serverStepAnim.set(id, { pts:[frm, to], startTime: performance.now(), segDur: SERVER_STEP_DUR_MS });
  } else {
    _serverStepAnim.set(id, { pts:[frm, to], startTime: performance.now(), segDur: SERVER_STEP_DUR_MS });
  }
  if(!_serverStepRaf) _serverStepRaf = requestAnimationFrame(_tickServerStep);
}

// Posição interpolada atual de uma entidade em deslize (ou null se não há).
// Retorna {x, y, hop} — hop∈[0,1] para o saltinho 3D.
function _serverStepPos(id){
  const ent = _serverStepAnim.get(id);
  if(!ent) return null;
  const segs = ent.pts.length - 1;
  const f = (performance.now() - ent.startTime) / ent.segDur;
  if(f >= segs){
    const p = ent.pts[segs];
    return { x:p[0], y:p[1], hop:0 };
  }
  const si = Math.floor(f), st = f - si, e = easeInOut(st);
  const [x0,y0] = ent.pts[si], [x1,y1] = ent.pts[si+1];
  return { x:x0+(x1-x0)*e, y:y0+(y1-y0)*e, hop:Math.sin(st*Math.PI) };
}

function _tickServerStep(){
  let any = false;
  for(const [id, ent] of _serverStepAnim){
    const segs = ent.pts.length - 1;
    const f = (performance.now() - ent.startTime) / ent.segDur;
    if(f >= segs){
      // Concluiu todos os waypoints recebidos: restaura o y do peão 3D e descarta.
      const mesh = getMonsterMesh(id) || getAnimadoMesh(id);
      if(mesh && mesh.userData._stepBaseY !== undefined){
        mesh.position.y = mesh.userData._stepBaseY;
        delete mesh.userData._stepBaseY;
      }
      _serverStepAnim.delete(id);
    } else any = true;
  }
  if(GS.gameState) renderMap(GS.gameState);
  _serverStepRaf = any ? requestAnimationFrame(_tickServerStep) : null;
}

// ── Animação 2D de minion ao longo de um caminho (lerp contínuo) ────────────
// Anima 2D contínuo ao longo de um caminho (pts = tiles absolutos, com origem).
// A duração escala com o nº de passos para manter ~DURACAO_PASSO_MS por casa.
function _startMininoAnimCaminho2D(animadoId, pts, onDone){
  _mininoAnimState.set(animadoId, {
    pathPts: pts,
    startTime: performance.now(),
    dur: DURACAO_PASSO_MS * Math.max(1, pts.length - 1),
    onDone,
  });
  if(!_mininoAnimRafId) _tickMininoAnim2D();
}

function _tickMininoAnim2D(){
  const now = performance.now();
  let anyActive = false;
  const done = [];
  for(const [id, anim] of _mininoAnimState){
    const t = (now - anim.startTime) / anim.dur;
    if(t >= 1) done.push(id);
    else anyActive = true;
  }
  if(GS.gameState) renderMap(GS.gameState);
  for(const id of done){
    const anim = _mininoAnimState.get(id);
    _mininoAnimState.delete(id);
    if(anim && anim.onDone) anim.onDone();
  }
  if(anyActive){
    _mininoAnimRafId = requestAnimationFrame(_tickMininoAnim2D);
  } else {
    _mininoAnimRafId = null;
  }
}

// Anima um minion ao longo de um CAMINHO inteiro (igual ao herói): o 3D faz
// lift/glide/land por casa via _animarPasso; o 2D interpola contínuo pelos
// segmentos. Os passos vão ao servidor já no início (mesmo padrão do herói),
// para a posição autoritativa e a névoa atualizarem em paralelo à animação.
function _animarEEnviarMoverCaminhoMinino(animado, passos){
  if(estadoMininoMov.emMovimento) return;
  if(!passos || !passos.length) return;
  estadoMininoMov.emMovimento = true;

  // Tiles absolutos do caminho (inclui a origem) para a animação contínua.
  const pts = [[animado.pos[0], animado.pos[1]]];
  let cx = animado.pos[0], cy = animado.pos[1];
  for(const [dx,dy] of passos){ cx+=dx; cy+=dy; pts.push([cx,cy]); }

  // Envia todos os passos ao servidor já (ele valida/decrementa cada um).
  for(const [dx,dy] of passos) GS.moverAnimado(animado.id, dx, dy);

  const onDone = () => {
    estadoMininoMov.emMovimento = false;
    estadoMininoMov.peaoAtivo   = null;
  };

  if(mode3D && g3){
    const peao = getAnimadoMesh(animado.id);
    if(peao){
      estadoMininoMov.peaoAtivo = peao;
      _animarCaminhoPeao3D(peao, pts.slice(1), onDone);   // anima casa a casa
      return;
    }
    // mesh não encontrado (fora da visão) — passos já enviados; nada a animar.
    onDone();
    return;
  }

  // Modo 2D — interpola contínuo ao longo do caminho.
  _startMininoAnimCaminho2D(animado.id, pts, onDone);
}

// Move o prisioneiro liberto ao longo de um CAMINHO — igual ao herói/minion:
// 3D faz lift/glide/land por casa via _animarPasso (com o som de peão); o 2D
// interpola contínuo. Os passos vão ao servidor já no início (ele valida/decrementa).
function _animarEEnviarMoverPrisioneiroCaminho(pris, passos){
  if(estadoMininoMov.emMovimento) return;
  if(!pris || !passos || !passos.length) return;
  estadoMininoMov.emMovimento = true;

  const pts = [[pris.pos[0], pris.pos[1]]];
  let cx = pris.pos[0], cy = pris.pos[1];
  for(const [dx,dy] of passos){ cx+=dx; cy+=dy; pts.push([cx,cy]); }

  for(const [dx,dy] of passos) GS.moverPrisioneiro(dx, dy);

  const onDone = () => {
    estadoMininoMov.emMovimento = false;
    estadoMininoMov.peaoAtivo   = null;
    if(GS.gameState){ if(mode3D && g3) renderMap3D(GS.gameState); else renderMap(GS.gameState); }
  };

  if(mode3D && g3){
    const peao = getPrisonerMesh();
    if(peao){
      estadoMininoMov.peaoAtivo = peao;
      _animarCaminhoPeao3D(peao, pts.slice(1), onDone);   // anima casa a casa (+ som)
      return;
    }
    onDone();   // mesh fora da visão — passos já enviados
    return;
  }
  // Modo 2D — interpola contínuo ao longo do caminho.
  _startMininoAnimCaminho2D('prisoner', pts, onDone);
}

// Sequência 3D: anima o peão casa a casa pelo caminho (tiles absolutos).
function _animarCaminhoPeao3D(peao, tilesAbs, onDone){
  let i = 0;
  const passo = () => {
    if(i >= tilesAbs.length){ if(onDone) onDone(); return; }
    const [tx,ty] = tilesAbs[i++];
    _animarPasso(peao, {x: tx, z: ty}, passo);
  };
  passo();
}

// Som de peão de plástico oco batendo na madeira — Web Audio puro, 3 camadas
// (tom do plástico ~280Hz + ressonância grave da madeira + clique de superfície),
// com leve variação aleatória e compressor para evitar distorção. Reusa o
// AudioContext existente (getAudioContext).
function tocarSomPasso(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    const variacao = 0.85 + Math.random() * 0.30;

    // Compressor final — todas as camadas passam por ele antes da saída.
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -18;
    comp.ratio.value     = 6;
    comp.attack.value    = 0.001;
    comp.release.value   = 0.08;
    comp.connect(_sfxBus());

    // CAMADA 1 — Tom principal do plástico (ruído filtrado, bandpass ~280Hz)
    const bufSize = Math.floor(ctx.sampleRate * 0.06);
    const buffer  = ctx.createBuffer(1, bufSize, ctx.sampleRate);
    const data    = buffer.getChannelData(0);
    for(let i = 0; i < bufSize; i++){
      const t = i / bufSize;
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, 3);   // ataque seco, decay
    }
    const ruido = ctx.createBufferSource();
    ruido.buffer = buffer;
    const filtro = ctx.createBiquadFilter();
    filtro.type = 'bandpass'; filtro.frequency.value = 280 * variacao; filtro.Q.value = 1.8;
    const ganho1 = ctx.createGain();
    ganho1.gain.setValueAtTime(0.55 * variacao, now);
    ganho1.gain.exponentialRampToValueAtTime(0.001, now + 0.07);
    ruido.connect(filtro); filtro.connect(ganho1); ganho1.connect(comp);
    ruido.start(now);

    // CAMADA 2 — Ressonância grave da madeira (sine 140→80Hz)
    const osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(140 * variacao, now);
    osc.frequency.exponentialRampToValueAtTime(80, now + 0.08);
    const ganho2 = ctx.createGain();
    ganho2.gain.setValueAtTime(0.20 * variacao, now);
    ganho2.gain.exponentialRampToValueAtTime(0.001, now + 0.10);
    osc.connect(ganho2); ganho2.connect(comp);
    osc.start(now); osc.stop(now + 0.10);

    // CAMADA 3 — Clique de superfície (transiente agudo, highpass 2400Hz)
    const bufClique  = ctx.createBuffer(1, Math.floor(ctx.sampleRate * 0.012), ctx.sampleRate);
    const dataClique = bufClique.getChannelData(0);
    for(let i = 0; i < dataClique.length; i++){
      const t = i / dataClique.length;
      dataClique[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, 5);
    }
    const clique = ctx.createBufferSource();
    clique.buffer = bufClique;
    const filtroClique = ctx.createBiquadFilter();
    filtroClique.type = 'highpass'; filtroClique.frequency.value = 2400;
    const ganhoClique = ctx.createGain();
    ganhoClique.gain.setValueAtTime(0.30 * variacao, now);
    ganhoClique.gain.exponentialRampToValueAtTime(0.001, now + 0.015);
    clique.connect(filtroClique); filtroClique.connect(ganhoClique); ganhoClique.connect(comp);
    clique.start(now);
  } catch(e){}
}

function easeOut(t){ return 1 - Math.pow(1 - t, 2); }
function easeIn(t){ return t * t; }
function easeInOut(t){ return t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2, 2)/2; }

const DURACAO_PASSO_MS = 250;   // 0.25s por casa
const ALTURA_ELEVACAO  = 0.4;   // unidades Three.js

function moverPeaoAoCaminho(peao, heroi, caminho, onConclucao){
  if(estadoMovimento.emMovimento) return;
  if(!peao || !caminho || caminho.length === 0){ if(onConclucao) onConclucao(); return; }
  estadoMovimento.emMovimento = true;
  estadoMovimento.filaCaminho = [...caminho];
  estadoMovimento.peaoAtivo   = peao;
  estadoMovimento.heroi       = heroi;
  estadoMovimento.onConclucao = onConclucao || null;
  iniciarSeguimentoCamera(peao);              // câmera passa a seguir o peão
  _executarProximoPasso();
}

function _executarProximoPasso(){
  if(estadoMovimento.filaCaminho.length === 0){
    estadoMovimento.emMovimento = false;        // libera input ANTES do callback
    encerrarSeguimentoCamera();                 // re-sincroniza OrbitControls
    const cb = estadoMovimento.onConclucao;
    estadoMovimento.onConclucao = null;
    if(cb) cb();
    return;
  }
  const destino = estadoMovimento.filaCaminho.shift();
  _animarPasso(estadoMovimento.peaoAtivo, destino, () => _executarProximoPasso());
}

function _animarPasso(peao, destino, onPasso){
  const inicio = { x: peao.position.x, y: peao.position.y, z: peao.position.z };
  const destinoWorld = casaParaMundo(destino.x, destino.z);
  let startTime = null;
  function tick(timestamp){
    if(startTime === null) startTime = timestamp;
    const progress = Math.min((timestamp - startTime) / DURACAO_PASSO_MS, 1);

    if(progress < 0.3){
      // FASE 1 — levanta
      const t = progress / 0.3, eased = easeOut(t);
      peao.position.y = inicio.y + ALTURA_ELEVACAO * eased;
      peao.rotation.x = -0.08 * eased;
    } else if(progress < 0.7){
      // FASE 2 — avança no ar
      const t = (progress - 0.3) / 0.4, eased = easeInOut(t);
      peao.position.y = inicio.y + ALTURA_ELEVACAO;
      peao.position.x = inicio.x + (destinoWorld.x - inicio.x) * eased;
      peao.position.z = inicio.z + (destinoWorld.z - inicio.z) * eased;
      peao.rotation.x = -0.08;
    } else {
      // FASE 3 — pousa
      const t = (progress - 0.7) / 0.3, eased = easeIn(t);
      peao.position.y = inicio.y + ALTURA_ELEVACAO * (1 - eased);
      peao.position.x = destinoWorld.x;
      peao.position.z = destinoWorld.z;
      peao.rotation.x = -0.08 * (1 - t);
      if(progress > 0.85 && progress < 0.95){
        const impacto = Math.sin((progress - 0.85) / 0.10 * Math.PI);
        peao.scale.y = 1.0 - (0.12 * impacto);
        peao.scale.x = 1.0 + (0.06 * impacto);
        peao.scale.z = 1.0 + (0.06 * impacto);
      } else {
        peao.scale.set(1, 1, 1);
      }
      if(progress >= 0.88 && !peao._somTocado){
        peao._somTocado = true;
        tocarSomPasso();
      }
    }

    if(progress < 1){
      requestAnimationFrame(tick);
    } else {
      peao.position.set(destinoWorld.x, inicio.y, destinoWorld.z);
      peao.rotation.set(0, peao.rotation.y, 0);
      peao.scale.set(1, 1, 1);
      peao._somTocado = false;
      onPasso();
    }
  }
  requestAnimationFrame(tick);
}

// ═══════════════════════════════════════════════════════════════════════════
// CÂMERA QUE SEGUE O PEÃO (3D) — durante o movimento desliza suavemente (lerp)
// para acompanhar o peão, PRESERVANDO o ângulo isométrico atual (captura o
// offset câmera→alvo e o translada). OrbitControls é desativado durante o
// seguimento e re-sincronizado ao final (sem cortes). Câmera ortográfica → não
// há "zoom por distância"; mantém-se o offset/zoom atuais.
// ═══════════════════════════════════════════════════════════════════════════
const configCamera = {
  seguindoPeao: false,
  velocidade:   0.08,                 // 0..1 — suavidade do lerp
  offset:       new THREE.Vector3(),  // offset câmera→alvo (preserva isométrico)
  alvoAtual:    new THREE.Vector3(),  // ponto observado (lerp suave)
};

function iniciarSeguimentoCamera(peao){
  if(!g3 || !g3.camera || !g3.controls) return;
  configCamera.seguindoPeao = true;
  g3.controls.enabled = false;                                   // evita conflito
  configCamera.offset.copy(g3.camera.position).sub(g3.controls.target);
  configCamera.alvoAtual.copy(g3.controls.target);
}

function atualizarCamera(){
  if(!configCamera.seguindoPeao || !g3 || !g3.camera) return;
  if(!estadoMovimento.emMovimento || !estadoMovimento.peaoAtivo) return;
  const peao = estadoMovimento.peaoAtivo;
  // Alvo desliza para a base do peão (y=0 → câmera não balança com o pulo).
  const destino = new THREE.Vector3(peao.position.x, 0, peao.position.z);
  configCamera.alvoAtual.lerp(destino, configCamera.velocidade);
  g3.camera.position.copy(configCamera.alvoAtual).add(configCamera.offset);
  g3.camera.lookAt(configCamera.alvoAtual);
}

function encerrarSeguimentoCamera(){
  if(!g3 || !g3.controls) return;
  configCamera.seguindoPeao = false;
  // Re-sincroniza o OrbitControls com a posição final (sem corte) e reativa.
  if(estadoMovimento.peaoAtivo){
    const p = estadoMovimento.peaoAtivo.position;
    g3.controls.target.set(p.x, 0, p.z);
  }
  g3.controls.update();          // re-deriva o estado interno (sem snap)
  g3.controls.enabled = true;
}

// Libera os recursos de GPU de um peão/sprite removido do entityGroup.
// THREE.js NÃO libera geometria/material/textura ao remover da cena — sem este
// descarte, cada game_state vazava dezenas de buffers (lentidão progressiva).
function _disposeEntityTree(root){
  root.traverse(o => {
    // Clones GLB compartilham geometria/material/texturas com o template em
    // cache (_heroGLBCache) — descartar aqui quebraria os próximos clones.
    if(o.userData && o.userData.isGLB) return;
    if(!(o.isMesh || o.isSprite)) return;
    // Sprites no r128 compartilham UMA geometria global — nunca descartá-la.
    if(o.isMesh && o.geometry) o.geometry.dispose();
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for(const m of mats){
      if(!m) continue;
      // Só descarta texturas EXCLUSIVAS do peão (placa de nome, sprite de
      // armadilha). Texturas em cache (_pawnTexCache, madeira da base, etc.)
      // são compartilhadas entre todos os peões e ficam vivas.
      for(const k of ['map','bumpMap','normalMap','emissiveMap','alphaMap']){
        if(m[k] && m[k]._owned) m[k].dispose();
      }
      m.dispose();
    }
  });
}

// ── Helpers para miniaturas extrudadas de decorações (PNG → 3D) ───────────────
function _disposeDecorMesh(obj){
  obj.traverse(o => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) {
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      // _shared: textura cacheada (ex.: chão via _pawnTexCache) reusada por outras
      // decorações — não descartar aqui, senão some das demais.
      mats.forEach(mm => { if (mm.map && !mm.map._shared) mm.map.dispose(); mm.dispose(); });
    }
  });
}
const _objImg3D = {};
function _buildObjetoMini(decorId, imageName, cells, facing){
  const make = (img) => {
    const slot = g3 && g3.decorMeshes[decorId];
    // a decoração pode ter sido removida/trocada enquanto carregava
    if (!slot || slot.userData.imageName !== imageName) return;
    // g3.T = alias do THREE (esta função é de módulo; o `T` local só existe
    // dentro de renderMap3D, então usamos g3.T para não dar ReferenceError).
    // DECOR_MINI_ESCALA: tamanho da miniatura por casa de footprint (ajuste aqui
    // para deixar as miniaturas maiores/menores no 3D).
    const grp = window.Miniatura3D.build(g3.T, { image: img, tileSize: Math.max(1, cells) * DECOR_MINI_ESCALA });
    grp.userData = { isDecor: true, decorId: decorId, imageName: imageName };
    grp.position.copy(slot.position);
    grp.rotation.y = _facingAngleY3D(facing);   // giro 90° aplicado já na construção assíncrona
    grp.visible = slot.visible;
    g3.scene.remove(slot); _disposeDecorMesh(slot);
    g3.scene.add(grp);
    g3.decorMeshes[decorId] = grp;
  };
  let img = _objImg3D[imageName];
  if (img) {
    if (img.complete && img.naturalWidth) make(img);
    // addEventListener (não `onload=`): várias decorações com o MESMO PNG ainda
    // carregando registram callbacks distintos sem sobrescrever umas às outras.
    else img.addEventListener('load', () => make(img), { once: true });
    return;
  }
  img = new Image();
  _objImg3D[imageName] = img;
  img.addEventListener('load', () => make(img), { once: true });
  img.src = _assetURL(`assets/objetos/${imageName}`);
  // Imagem em cache do navegador pode já estar `complete` ao definir o src,
  // sem disparar 'load' — então constrói na hora nesse caso.
  if (img.complete && img.naturalWidth) make(img);
}

function renderMap3D(state){
  if(!state || !state.tiles) return;
  // Durante a animação de movimento não reconstrói os peões (preserva o mesh
  // animado). Ao terminar, emMovimento=false e o próximo render reconcilia.
  // Idem para animação de minions (estadoMininoMov).
  if(estadoMovimento.emMovimento || estadoMininoMov.emMovimento) return;
  if(!g3){
    try { init3D(state); }
    catch(err){
      console.error('init3D failed:', err);
      toast('❌ Erro ao iniciar 3D: ' + err.message, 'var(--red)');
      // Fall back to 2D so the board is still visible
      mode3D = false;
      const btn=$('btn-3d-toggle'); if(btn){ btn.classList.remove('active'); btn.textContent='🎲 3D'; }
      const hint=$('orbit-hint'); if(hint) hint.style.display='none';
      const reset=$('btn-cam-reset'); if(reset) reset.style.display='none';
      $('dungeon-canvas').style.display='block';
      renderMap(state);
      return;
    }
  }
  if(!g3) return;

  const { T, tileMeshes, doorMeshes, W, H, entityGroup, sconces, torch } = g3;
  const exploredSet = new Set(state.explored.map(([x,y])=>`${x},${y}`));
  // Terreno visível ao vivo: explorado + revelado (Clarividência/minions). Reverte
  // à névoa sozinho quando o minion sai. exploredSet segue governando a lógica.
  const revealedSet = new Set((state.revealed||[]).map(([x,y])=>`${x},${y}`));
  const terrainSet = revealedSet.size
    ? new Set([...exploredSet, ...revealedSet]) : exploredSet;
  const { closed:doorClosed3D } = GS.doorSets(state);
  const me = state.players.find(p => p.id===GS.myPid && p.alive);
  const visionSet = computeVisionSet(state, me);

  // Reachable tiles (movement highlight)
  const isAnimadosTurn3D = state.animados_turn === GS.myPid;
  const meAnimados3D = (state.players.find(p=>p.id===GS.myPid)?.animados||[]).filter(a=>a.vida_atual>0);
  const selAnimado3D = isAnimadosTurn3D && _animadoSel
    ? meAnimados3D.find(a=>a.id===_animadoSel) : null;
  const meuPris3D = state.prisoner && state.prisoner.alive && state.prisoner.freed
    && state.prisoner.rescuer_pid === GS.myPid;
  const selPris3D = isAnimadosTurn3D && _prisSel && meuPris3D ? state.prisoner : null;

  const reachable = new Set();
  if(selAnimado3D && selAnimado3D.moves_left > 0)
    bfsReachable(state.tiles, exploredSet, selAnimado3D.pos[0], selAnimado3D.pos[1], selAnimado3D.moves_left, reachable);
  else if(selPris3D && (selPris3D.moves_left||0) > 0)
    bfsReachable(state.tiles, exploredSet, selPris3D.pos[0], selPris3D.pos[1], selPris3D.moves_left, reachable);
  else if(!isAnimadosTurn3D && GS.isMyTurn && me && me.moves_left > 0)
    bfsReachable(state.tiles, exploredSet, me.pos[0], me.pos[1], me.moves_left, reachable);

  // Attackable tiles (attack range highlight)
  const attackable3d = new Set();
  // Ataque do jogador (apenas no próprio turno, fora do turno dos servos)
  if(!isAnimadosTurn3D && GS.isMyTurn && me && !me.action_done){
    const wRng = me.weapon?.range ?? null;
    for(const m of state.monsters){
      if(!m || m.hp <= 0) continue;
      const dx = Math.abs(me.pos[0] - m.pos[0]), dy = Math.abs(me.pos[1] - m.pos[1]);
      const inR = wRng != null
        ? Math.max(dx,dy) <= wRng && GS.hasLineOfSight(state, me.pos[0],me.pos[1], m.pos[0],m.pos[1])
        : (dx===1&&dy===0)||(dx===0&&dy===1);
      if(inR) attackable3d.add(`${m.pos[0]},${m.pos[1]}`);
    }
  }
  // Alcance de ataque do animado selecionado (turno dos servos) ou em hover — aditivo
  const atkRefAnimado3D = selAnimado3D || window._animadoHover;
  if(atkRefAnimado3D && atkRefAnimado3D.pos){
    const [ax3,ay3] = atkRefAnimado3D.pos;
    const isElec3D = atkRefAnimado3D.especial === 'linha_3q';
    const atkRange3D = isElec3D ? 3 : 1;
    for(const [ddx,ddy] of [[1,0],[-1,0],[0,1],[0,-1]])
      for(let r=1; r<=atkRange3D; r++)
        attackable3d.add(`${ax3+ddx*r},${ay3+ddy*r}`);
  }

  // Durante a mira de magia, oculta realces de movimento/ataque (mostra alcance/área).
  if(window._modoMagia){ reachable.clear(); attackable3d.clear(); }

  // ── Tile visibility
  for(let y=0; y<H; y++){
    for(let x=0; x<W; x++){
      const key  = `${x},${y}`;
      const mesh = tileMeshes[key];
      if(!mesh) continue;
      mesh.visible = terrainSet.has(key);
      const ent3 = tileMeshes[`entulho:${key}`];
      if(ent3) ent3.visible = mesh.visible;
    }
  }

  // ── Door leaves: visible only while closed AND the door tile is visível ──────
  if(doorMeshes){
    for(const [key, grp] of Object.entries(doorMeshes))
      grp.visible = terrainSet.has(key) && doorClosed3D.has(key);
  }

  // ── Movement highlight overlay visibility (blue planes)
  if(g3.moveHighlightMeshes){
    for(const [key, m] of Object.entries(g3.moveHighlightMeshes))
      m.visible = exploredSet.has(key) && reachable.has(key);
  }

  // ── Attack highlight overlay visibility (red planes)
  if(g3.atkHighlightMeshes){
    for(const [key, m] of Object.entries(g3.atkHighlightMeshes))
      m.visible = exploredSet.has(key) && attackable3d.has(key);
  }

  // ── Weapon range preview planes (vermelho forte — hover no ícone da arma)
  if(g3.weaponRangeMeshes){
    const wRngTiles = (window._weaponRangePreview && me)
      ? _computeWeaponRangeTiles(state, me) : new Set();
    for(const [key, m] of Object.entries(g3.weaponRangeMeshes))
      m.visible = exploredSet.has(key) && wRngTiles.has(key);
  }

  // ── Realce de MAGIA (alcance vermelho / zona laranja / área verde) ──────────
  _aplicarSpellHL3D();

  // ── Explosão do Elemental de Fogo — meshes vermelhos temporários (3D) ───────
  if(g3.atkHighlightMeshes && _explosionTiles && _explosionTiles.size){
    for(const [key, m] of Object.entries(g3.atkHighlightMeshes)){
      if(_explosionTiles.has(key) && exploredSet.has(key)) m.visible = true;
    }
  }

  // ── Wall detail visibility (arches, corner columns, baseboards) ─────────────
  if(g3.wallDetailMeshes){
    for(const [key, arr] of Object.entries(g3.wallDetailMeshes))
      for(const m of arr) m.visible = terrainSet.has(key);
  }

  // ── Wall torch visibility (whole bracket group, keyed by wall tile) ──────────
  if(g3.wallTorches){
    for(const wt of g3.wallTorches)
      wt.group.visible = terrainSet.has(wt.wallKey);
  }

  // ── Room floor overlay visibility (transparent color planes) ─────────────────
  if(g3.roomOverlayMeshes){
    for(const [key, mesh] of Object.entries(g3.roomOverlayMeshes))
      mesh.visible = terrainSet.has(key);
  }

  if(g3.sceneryMeshes){
    for(const [key, arr] of Object.entries(g3.sceneryMeshes))
      for(const m of arr) m.visible = terrainSet.has(key);
  }

  // ── Glowing grout visibility (magic rune grid, trap rooms only) ───────────────
  if(g3.groutMeshes){
    for(const [key, arr] of Object.entries(g3.groutMeshes))
      for(const m of arr) m.visible = terrainSet.has(key);
  }

  // ── Wet floor reflection visibility (revealed with its floor tile) ───────────
  if(g3.wetFloorMeshes){
    for(const [key, m] of Object.entries(g3.wetFloorMeshes))
      m.visible = terrainSet.has(key);
  }

  // ── Dust motes: show once the player has revealed any tiles ──────────────────
  if(g3.dustPts && !g3.dustPts.visible && exploredSet.size > 0)
    g3.dustPts.visible = true;

  if(me){
    torch.position.set(me.pos[0], 1.1, me.pos[1]);
    g3.visionLamp.position.set(me.pos[0], 1.8, me.pos[1]);
  } else {
    torch.position.set(W/2, 1.1, H/2);
    g3.visionLamp.position.set(W/2, 1.8, H/2);
  }

  // ── Sconce visibility
  for(const sc of sconces)
    sc.light.visible = exploredSet.has(`${sc.x},${sc.y}`);

  // ── Staircase visibility
  if(g3.stairGroup && state.stairs_pos)
    g3.stairGroup.visible = exploredSet.has(`${state.stairs_pos[0]},${state.stairs_pos[1]}`);
  // Fase 3: marcador de saída visível quando a casa foi explorada.
  if(g3.exitGroup && GS.exitPos)
    g3.exitGroup.visible = exploredSet.has(`${GS.exitPos[0]},${GS.exitPos[1]}`);

  // ── Chest 3D models — persistent meshes, created/removed as chests appear/go ─
  const chests = state.chests || [];
  const liveChestIds = new Set(chests.map(c => c.id));

  // Remove meshes for chests that no longer exist
  for(const [cid, grp] of Object.entries(g3.chestMeshes)){
    if(!liveChestIds.has(cid)){
      g3.scene.remove(grp);
      delete g3.chestMeshes[cid];
    }
  }
  // Add new chest meshes + update visibility
  for(const chest of chests){
    const key = `${chest.pos[0]},${chest.pos[1]}`;
    if(!g3.chestMeshes[chest.id]){
      const grp = buildChest3D(g3.T, chest);
      g3.scene.add(grp);
      g3.chestMeshes[chest.id] = grp;
    }
    g3.chestMeshes[chest.id].visible = exploredSet.has(key);
  }

  // ── Decoration 3D meshes — procedural boxes/cylinders, ou miniatura extrudada ─
  {
    const decors = GS.decorations;
    const vistosDec = new Set();
    for (const d of decors) {
      vistosDec.add(d.id);
      const tiles = GS.decorTilesOf(d);
      // Determine footprint bounds
      const minX = Math.min(...tiles.map(t => t[0]));
      const maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1]));
      const maxY = Math.max(...tiles.map(t => t[1]));
      const wCells = maxX - minX + 1;
      const hCells = maxY - minY + 1;
      // Center of footprint in world coords (tile x,y map directly to world x,z)
      const worldX = (minX + maxX) / 2;
      const worldZ = (minY + maxY) / 2;
      const visivel = tiles.some(([tx2, ty2]) => exploredSet.has(`${tx2},${ty2}`));

      let mesh = g3.decorMeshes[d.id];

      if (d.special === 'floor' && d.image) {
        // ── Chão: decal deitado preenchendo TODO o footprint, borda-a-borda ──
        if (!mesh || mesh.userData.imageName !== d.image || mesh.userData.floorW !== wCells || mesh.userData.floorH !== hCells) {
          if (mesh) { g3.scene.remove(mesh); _disposeDecorMesh(mesh); }
          mesh = _chaoDecal3D(d, wCells, hCells);
          g3.scene.add(mesh);
          g3.decorMeshes[d.id] = mesh;
        }
        mesh.position.set(worldX, 0.222, worldZ);   // logo acima do piso (TH=0.22), sob os realces
        mesh.visible = visivel;
        continue;
      }

      if (d.image && window.Miniatura3D) {
        // ── Caminho miniatura extrudada (PNG) ──
        // (re)constrói se ainda não existe OU se a imagem mudou
        if (!mesh || mesh.userData.imageName !== d.image) {
          if (mesh) { g3.scene.remove(mesh); _disposeDecorMesh(mesh); }
          const placeholder = new T.Group();
          placeholder.userData = { isDecor: true, decorId: d.id, imageName: d.image, pending: true };
          // Posiciona ANTES de construir: se a imagem já estiver em cache, o
          // build roda síncrono e copia esta posição (senão a miniatura cairia em 0,0).
          placeholder.position.set(worldX, 0, worldZ);
          placeholder.visible = visivel;
          g3.scene.add(placeholder);
          g3.decorMeshes[d.id] = placeholder;
          mesh = placeholder;
          _buildObjetoMini(d.id, d.image, Math.max(wCells, hCells), d.facing);   // assíncrono (ou síncrono se em cache)
          mesh = g3.decorMeshes[d.id];   // _buildObjetoMini pode ter trocado o mesh (cache)
        }
        mesh.position.set(worldX, 0, worldZ);
        // Giro 90° (facing): roda a miniatura em pé sobre o eixo vertical.
        mesh.rotation.y = _facingAngleY3D(d.facing);
        // Escala visual (vscale): largura no plano (x,z), altura p/ cima (y);
        // o footprint já está embutido na geometria via tileSize.
        const _mvs = Array.isArray(d.vscale) ? d.vscale : [1, 1];
        mesh.scale.set(_mvs[0] || 1, _mvs[1] || 1, _mvs[0] || 1);
        mesh.visible = visivel;
        continue;
      }

      // ── Caminho procedural (sem image) ──
      // Se havia uma miniatura PNG antes (imageName), destrói e reconstrói como procedural
      if (mesh && mesh.userData.imageName) {
        g3.scene.remove(mesh); _disposeDecorMesh(mesh);
        mesh = null;
      }
      const spec = DECOR_3D[d.type] || { shape: 'box', h: 0.6, color: 0x999999 };
      if (!mesh) {
        const geo = spec.shape === 'cyl'
          ? new T.CylinderGeometry(0.4, 0.4, spec.h, 16)
          : new T.BoxGeometry(1, spec.h, 1);
        mesh = new T.Mesh(geo, new T.MeshStandardMaterial({ color: spec.color }));
        mesh.userData.isDecor = true;
        mesh.userData.decorId = d.id;
        g3.scene.add(mesh);
        g3.decorMeshes[d.id] = mesh;
      }
      // Escala visual (vscale): largura no plano ×sx, altura ×sy (ancorada no chão).
      const _pvs = Array.isArray(d.vscale) ? d.vscale : [1, 1];
      const _psx = _pvs[0] || 1, _psy = _pvs[1] || 1;
      mesh.position.set(worldX, spec.h * _psy / 2, worldZ);
      // Scale box to cover full footprint; cylinder mantém o raio (só vscale)
      if (spec.shape === 'box') mesh.scale.set(wCells * 0.9 * _psx, _psy, hCells * 0.9 * _psx);
      else mesh.scale.set(_psx, _psy, _psx);
      // Visibility: show if any footprint tile is explored
      mesh.visible = visivel;
    }
    // Remove meshes for decorations that no longer exist
    for (const id of Object.keys(g3.decorMeshes)) {
      if (!vistosDec.has(id)) {
        const m = g3.decorMeshes[id];
        g3.scene.remove(m); _disposeDecorMesh(m);
        delete g3.decorMeshes[id];
      }
    }
  }

  // ── Rebuild entity group ────────────────────────────────────────────────────
  // Assinatura do que é visível: se nada mudou desde o último game_state, NÃO
  // reconstrói os peões. Reconstruir a cada mensagem criava/vazava dezenas de
  // geometrias, materiais, texturas e PointLights — e a variação na contagem de
  // luzes força o Three.js a recompilar shaders (travadas perceptíveis).
  const entitySig = JSON.stringify([
    state.players.map(p => [p.id, p.pos, p.alive, p.color, p.class_id,
      (p.animados||[]).map(a => [a.id, a.pos, a.vida_atual, a.tipo])]),
    state.monsters.map(m => [m.type, m.pos, m.hp, m.image]),
    state.prisoner ? [state.prisoner.pos, state.prisoner.alive, state.prisoner.freed, state.prisoner.image, _prisSel] : null,
    state.corpses || [],
    (state.armadilhas||[]).map(a => [a.id, a.pos, a.ativada, a.so_luccas, a.icone, a.visivel, a.aliada, a.image]),
    state.rooms.map(r => [r.cx, r.cy, r.role, r.cleared]),
    state.current_turn, state.animados_turn, GS.myPid,
    g3.selectedPos, _animadoSel,
    state.explored.length, [...visionSet].sort().join('|'),
  ]);
  if(entitySig !== g3._entitySig){
  g3._entitySig = entitySig;

  // ── Cache por entidade: cada peão só é RECONSTRUÍDO quando sua aparência
  // muda (classe, cor, turno ativo, seleção...). Mudança apenas de posição
  // reaproveita o grupo inteiro e atualiza x/z — o movimento de UM peão não
  // recria os outros 10+ peões da cena.
  if(!g3._figCache) g3._figCache = new Map();
  const figCache = g3._figCache;
  const figsUsadas = new Set();

  // Esvazia o grupo SEM descartar — os peões vivem no cache; os que não forem
  // reutilizados nesta passada são descartados (com GPU liberada) no final.
  while(entityGroup.children.length) entityGroup.remove(entityGroup.children[0]);

  // Reaproveita a figura `key` se a assinatura visual não mudou; senão
  // reconstrói (descartando a antiga). Reposiciona em (x, z) quando passado.
  const obterFig = (key, sig, construir, x, y) => {
    let ent = figCache.get(key);
    if(!ent || ent.sig !== sig){
      if(ent) _disposeEntityTree(ent.fig);
      ent = { sig, fig: construir() };
      figCache.set(key, ent);
    }
    const fig = ent.fig;
    if(x !== undefined){
      fig.position.x = x;   // y é animado pelo hover-lift — não tocar
      fig.position.z = y;
      fig.userData.gridX = x;
      fig.userData.gridY = y;
    }
    figsUsadas.add(key);
    entityGroup.add(fig);
    return fig;
  };

  // Players
  for(const p of state.players){
    if(!p.alive) continue;
    if(p.connected === false) continue;   // desconectado: fora da masmorra, não desenha
    const [px,py] = p.pos;
    if(!exploredSet.has(`${px},${py}`)) continue;
    const pSel = g3.selectedPos && g3.selectedPos[0]===px && g3.selectedPos[1]===py;
    const isCur = p.id===state.current_turn;
    obterFig(`pl:${p.id}`,
      JSON.stringify([p.color, p.class_id, p.id===GS.myPid, isCur, !!pSel]),
      () => {
        const f = build3DFig(p.color, false, p.id===GS.myPid, isCur, px, py, p.class_id, null, pSel);
        f.userData.pid = p.id;          // permite getPeaoMesh(pid) p/ animação
        return f;
      }, px, py);
  }

  // Prisioneiro (Fase 3): peão com imagem editável; só quando visível/explorado.
  const _pris3D = state.prisoner;
  if(_pris3D && _pris3D.alive){
    const [prx,pry] = _pris3D.pos;
    if(visionSet.has(`${prx},${pry}`) || exploredSet.has(`${prx},${pry}`)){
      const prisSelNow = !!(_prisSel && isAnimadosTurn3D && _pris3D.freed
        && _pris3D.rescuer_pid === GS.myPid);
      obterFig('prisoner',
        JSON.stringify([_pris3D.freed, _pris3D.image, prisSelNow]),
        () => {
          const f = build3DPrisoner(g3.T, _pris3D, prisSelNow);
          f.userData.prisoner = true;   // permite getPrisonerMesh() p/ animação
          return f;
        },
        prx, pry);
    }
  }

  // Monsters — only visible within player's current vision radius
  for(const m of state.monsters){
    if(m.hp <= 0) continue;
    const [mx,my] = m.pos;
    if(!visionSet.has(`${mx},${my}`)) continue;
    const mSel = g3.selectedPos && g3.selectedPos[0]===mx && g3.selectedPos[1]===my;
    obterFig(`mon:${m.id}`,
      JSON.stringify([m.type, m.image, !!mSel, m.porte, !!m.oriented, m.facing]),
      () => {
        const f = build3DFig('#c82020', true, false, false, mx, my, null, m.type, mSel, m.image, m.porte, m.oriented, m.facing);
        f.userData.monId = m.id;   // taggeado para getMonsterMesh() / deslize fiel
        return f;
      },
      mx, my);
  }

  // Cadáveres — marca onde o Pedro pode reanimar (na visão atual)
  for(const c of (state.corpses||[])){
    const [cx,cy] = c.pos;
    if(!visionSet.has(`${cx},${cy}`)) continue;
    obterFig(`corp:${c.id}`, JSON.stringify(c), () => build3DCorpse(c));
  }

  // Animados (servos do Pedro) — peão do MONSTRO ORIGINAL com base/aro roxo (aliado)
  for(const pl of state.players){
    for(const a of (pl.animados||[])){
      if(!a.pos || (a.vida_atual||0) <= 0) continue;
      const [ax,ay] = a.pos;
      if(!visionSet.has(`${ax},${ay}`)) continue;
      obterFig(`ani:${a.id}`,
        JSON.stringify([a.tipo, _animadoSel===a.id]),
        () => {
          const f = build3DFig('#9900cc', true, false, false, ax, ay, null, a.tipo, _animadoSel===a.id);
          f.userData.animadoId = a.id;   // taggeado para getAnimadoMesh()
          return f;
        }, ax, ay);
    }
  }

  // Room icons (glowing spheres — only for un-looted/cleared non-chest rooms)
  for(const room of state.rooms){
    if(room.cleared || !exploredSet.has(`${room.cx},${room.cy}`)) continue;
    if(room.role === 'chest') continue;   // chest rooms show the 3D chest model instead
    obterFig(`room:${room.cx},${room.cy}`, room.role, () => {
      const cols = { boss:0xff2020, trap:0xff8800 };
      const col  = cols[room.role] ?? 0xffffff;
      const geo  = new T.SphereGeometry(0.13, 8, 6);
      const mat  = new T.MeshStandardMaterial({ color:col, emissive:col, emissiveIntensity:0.75 });
      const s    = new T.Mesh(geo, mat);
      s.position.set(room.cx, 0.22+0.18, room.cy);
      return s;
    });
  }

  // ── Armadilhas colocáveis (Passo 2) — sprites de emoji sobre o tile ─────────
  for(const arm of (state.armadilhas||[])){
    const [ax,ay] = arm.pos;
    if(!exploredSet.has(`${ax},${ay}`)) continue;
    if(!_armadilhaVisivelParaMim(arm, me)) continue;   // escondida até ser revelada
    if(arm.image){
      // Com imagem: decal deitado no chão (plano horizontal sobre a casa).
      const dec = obterFig(`arm:${arm.id}`,
        JSON.stringify([arm.image, arm.ativada]),
        () => _armadilhaDecal3D(arm, ax, ay));
      dec.position.set(ax, 0.232, ay);   // logo acima do piso (TH=0.22)
    } else {
      const sp = obterFig(`arm:${arm.id}`,
        JSON.stringify([arm.icone, arm.ativada, arm.so_luccas]),
        () => _armadilhaSprite3D(arm, ax, ay));
      sp.position.set(ax, 0.34, ay);   // sprite não tem hover-lift — y fixo
    }
  }

  // Descarta as figuras que saíram de cena (morte, fora da visão, consumidas).
  for(const [key, ent] of figCache){
    if(!figsUsadas.has(key)){
      _disposeEntityTree(ent.fig);
      figCache.delete(key);
    }
  }

  }   // fim do bloco de reconstrução condicionada por entitySig

  // ── Deslize fiel (entity_step): reposiciona meshes em animação ───────────────
  // Fora do gate do entitySig: roda todo frame para que, mesmo quando o
  // game_state não muda, os peões de monstros/servos deslizem casa a casa.
  if(_serverStepAnim.size){
    for(const [id] of _serverStepAnim){
      const step = _serverStepPos(id);
      if(!step) continue;
      const mesh = getMonsterMesh(id) || getAnimadoMesh(id);
      if(!mesh) continue;
      if(mesh.userData._stepBaseY === undefined) mesh.userData._stepBaseY = mesh.position.y;
      mesh.position.x = step.x;
      mesh.position.z = step.y;
      // Saltinho do peão (efeito de movimentação) — a entidade em deslize não
      // está sob o cursor, então não conflita com o hover-lift.
      mesh.position.y = mesh.userData._stepBaseY + step.hop * ALTURA_ELEVACAO * 0.5;
    }
  }

  // Canção Heroica: anel dourado de raio 5 ao redor do bardo (3D).
  try { _sync3DCancaoRing(state); } catch(e) { console.warn('cancaoRing:', e); }

  // Portraits are exclusive to the class selection screen (HTML). Not on the board.
}

// Sprite de armadilha (emoji em canvas). Verde/normal = armada; vermelho = ativada.
function _armadilhaSprite3D(arm, x, y){
  const T = g3.T;
  const cv = document.createElement('canvas'); cv.width = cv.height = 64;
  const ctx = cv.getContext('2d');
  ctx.font = '46px serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(arm.icone || '🪤', 32, 36);
  const tex = new T.CanvasTexture(cv);
  tex._owned = true;   // textura exclusiva deste sprite — descartável com ele (r128: Texture não tem userData)
  const sp  = new T.Sprite(new T.SpriteMaterial({
    map: tex, transparent: true, depthWrite: false,
    opacity: arm.so_luccas ? 0.6 : (arm.ativada ? 1.0 : 0.92),
    color:   arm.ativada ? new T.Color(0xff6655) : new T.Color(0xffffff),
  }));
  sp.scale.set(0.6, 0.6, 1);
  sp.position.set(x, 0.34, y);
  sp.userData.armadilhaId = arm.id;
  sp.userData.tipo = 'armadilha';
  return sp;
}

// Armadilha com imagem (PNG de assets/objetos): decal DEITADO no chão da casa.
// Plano horizontal (rotacionado -90° em X) com a textura do PNG, ajustado à
// proporção da arte sem invadir os tiles vizinhos. Vermelho quando ativada.
function _armadilhaDecal3D(arm, x, y){
  const T = g3.T;
  const grp = new T.Group();
  const mat = new T.MeshBasicMaterial({
    transparent: true, alphaTest: 0.12, depthWrite: false,
    color: arm.ativada ? new T.Color(0xff7766) : new T.Color(0xffffff),
  });
  const mesh = new T.Mesh(new T.PlaneGeometry(0.92, 0.92), mat);
  mesh.rotation.x = -Math.PI/2;     // deita o plano no chão
  mesh.renderOrder = 2;             // desenha sobre o piso, sob os peões
  mesh.userData.isGroundDecal = true;   // fora do passe de outline
  grp.add(mesh);
  const cacheKey = '__arm_' + arm.image;
  const aplicar = (tex) => {
    const im = tex.image; if(!im || !im.width) return;
    const ar = im.width / im.height;
    let w = 0.92, h = 0.92/ar;
    if(h > 0.92){ h = 0.92; w = 0.92*ar; }
    mesh.geometry.dispose();
    mesh.geometry = new T.PlaneGeometry(w, h);
  };
  let tex = _pawnTexCache[cacheKey];
  if(tex){ mat.map = tex; if(tex.image && tex.image.width) aplicar(tex); }
  else {
    tex = new T.TextureLoader().load(_assetURL(`assets/objetos/${arm.image}`), aplicar);
    _pawnTexCache[cacheKey] = tex;
    mat.map = tex;
  }
  grp.position.set(x, 0.232, y);
  grp.userData.armadilhaId = arm.id;
  grp.userData.tipo = 'armadilha';
  return grp;
}

// Chão (decoração pisável): decal DEITADO no chão que preenche TODO o footprint
// borda-a-borda (estica a textura, sem manter proporção — é um piso). Peões andam
// por cima. `wCells`/`hCells` = footprint efetivo (já com facing aplicado).
function _chaoDecal3D(d, wCells, hCells){
  const T = g3.T;
  const grp = new T.Group();
  const mat = new T.MeshBasicMaterial({ transparent: true, depthWrite: false });
  const mesh = new T.Mesh(new T.PlaneGeometry(wCells, hCells), mat);
  mesh.rotation.x = -Math.PI/2;      // deita o plano no chão
  // renderOrder -1: o chão é PISO — deve ficar SOB os realces de movimento/ataque
  // (planos azuis/vermelhos em TH+0.004…), senão a grama esconderia a indicação.
  mesh.renderOrder = -1;
  mesh.userData.isGroundDecal = true;   // fora do passe de outline
  grp.add(mesh);
  const cacheKey = '__chao_' + d.image;
  let tex = _pawnTexCache[cacheKey];
  if(tex){ mat.map = tex; }
  else {
    tex = new T.TextureLoader().load(_assetURL(`assets/objetos/${d.image}`));
    tex._shared = true;   // cacheada/reusada — _disposeDecorMesh não deve descartá-la
    _pawnTexCache[cacheKey] = tex;
    mat.map = tex;
  }
  grp.userData = { isDecor: true, decorId: d.id, imageName: d.image,
                   floorW: wCells, floorH: hCells };
  return grp;
}

// MINIATURE BUILDER SYSTEM
// Each hero class and monster type gets a distinctive 3D miniature.
// All figures sit on a round plastic base on top of the floor tile (TH=0.22).
// Positions and movement rules are UNCHANGED — only visuals differ.

// Creates a StandardMaterial mesh, adds it to the group, and returns the mesh.
function _addM(group, geo, mp, pos, rotZ){
  const T   = g3.T;
  const mat = new T.MeshStandardMaterial({
    color:            mp.color  instanceof T.Color ? mp.color  : new T.Color(mp.color  ?? 0x888888),
    emissive:         mp.emissive instanceof T.Color ? mp.emissive : new T.Color(mp.emissive ?? 0x000000),
    emissiveIntensity: mp.emissiveIntensity ?? 0,
    roughness: mp.roughness ?? 0.82,
    metalness: mp.metalness ?? 0.04,
    side:      mp.side ?? T.FrontSide
  });
  const mesh = new T.Mesh(geo, mat);
  if(pos)  mesh.position.set(pos[0], pos[1], pos[2]);
  if(rotZ) mesh.rotation.z = rotZ;
  mesh.castShadow    = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}

// Resin statue / painted collectible style.  Spec:
//   Metal  : roughness 0.25, metalness 0.85, yellowish tint
//   Sword  : roughness 0.22, metalness 0.88
//   Cloth  : roughness 0.95, metalness 0.00
//   Leather: roughness 0.80, metalness 0.05
//   Skin   : roughness 0.84, metalness 0.00
//   Wood   : roughness 1.00, metalness 0.00
//   Glow   : emissive = color, intensity i (default 1.2)

// Acabamento de MINIATURA DE PLÁSTICO PINTADA — roughness baixa-média dá o
// brilho satinado que define o volume (antes era fosco/poligonal).
function _mMtl(hex){ return {color:new g3.T.Color(hex??0xd4c870), roughness:0.24, metalness:0.86}; }
function _mSwd(hex){ return {color:new g3.T.Color(hex??0xd4dcec), roughness:0.20, metalness:0.90}; }
function _mClth(hex){
  const c = hex instanceof g3.T.Color ? hex : new g3.T.Color(hex);
  return {color:c, roughness:0.52, metalness:0.02, emissive:c.clone(), emissiveIntensity:VC.pawns.emissiveIntensity};
}
function _mLeather(hex){
  const c = new g3.T.Color(hex ?? 0x5a3818);
  return {color:c, roughness:0.46, metalness:0.04, emissive:c.clone(), emissiveIntensity:VC.pawns.emissiveIntensity};
}
function _mSkin(hex){
  const c = new g3.T.Color(hex ?? 0xd4a060);
  return {color:c, roughness:0.42, metalness:0.02, emissive:c.clone(), emissiveIntensity:VC.pawns.emissiveIntensity};
}
function _mWood(hex){ return {color:new g3.T.Color(hex??0x7a4a18), roughness:0.62, metalness:0.02}; }
function _mGlw(hex,i){ const c=new g3.T.Color(hex); return {color:c,emissive:c,emissiveIntensity:i??1.2,roughness:0.22,metalness:0.05}; }

// Cobblestone texture: cached procedural CanvasTexture (deterministic pattern).
let _stoneTopTex = null;

// ── Tampo de MADEIRA ESCURA para a base dos peões (corte de tora: anéis) ──────
let _woodTopTex = null;
function _getWoodTopTex(T){
  if(_woodTopTex) return _woodTopTex;
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#241106';
  ctx.fillRect(0, 0, 128, 128);
  // anéis de crescimento (elipses levemente excêntricas)
  for(let r = 62; r > 2; r -= 3.0){
    const tom = Math.sin(r * 1.7) * 0.5 + 0.5;
    ctx.strokeStyle = `rgb(${44 + tom*30},${24 + tom*17},${10 + tom*8})`;
    ctx.lineWidth = 2.3;
    ctx.beginPath();
    ctx.ellipse(64, 64, r, r * 0.93, 0.30, 0, Math.PI * 2);
    ctx.stroke();
  }
  // rachaduras radiais sutis
  ctx.strokeStyle = 'rgba(8,4,2,0.55)';
  ctx.lineWidth = 1.4;
  for(const [x1, y1] of [[118, 32], [22, 96], [98, 112], [40, 14]]){
    ctx.beginPath(); ctx.moveTo(64, 64); ctx.lineTo(x1, y1); ctx.stroke();
  }
  _woodTopTex = new T.CanvasTexture(c);
  return _woodTopTex;
}

function _getStoneTopTex(T){
  if(_stoneTopTex) return _stoneTopTex;
  const c = document.createElement('canvas');
  c.width = 64; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#09090b';
  ctx.fillRect(0,0,64,64);
  const stones = [
    [ 1, 1,20,14],[23, 1,18,16],[ 1,17,22,14],[25,19,18,14],
    [ 1,33,24,14],[27,35,20,14],[ 1,49,22,12],[25,51,20,10],
    [45, 1,18,16],[45,19,18,16],[45,37,18,14],[45,53,18,10]
  ];
  for(const [sx,sy,sw,sh] of stones){
    ctx.fillStyle = 'rgb(18,18,22)';
    ctx.fillRect(sx,sy,sw,sh);
    ctx.strokeStyle = '#040406';
    ctx.lineWidth = 1.2;
    ctx.strokeRect(sx+0.5,sy+0.5,sw-1,sh-1);
  }
  _stoneTopTex = new T.CanvasTexture(c);
  return _stoneTopTex;
}

// Gold name-plate sprite (billboards toward camera — always readable).
function _makeNamePlate(T, label){
  const c = document.createElement('canvas');
  c.width = 256; c.height = 44;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#5a3600';
  ctx.fillRect(0,0,256,44);
  ctx.fillStyle = VC.ui.colors.gold;        // aged gold as requested
  ctx.fillRect(3,3,250,38);
  // Inner bevel lines
  ctx.strokeStyle = '#e0c060';
  ctx.lineWidth = 1;
  ctx.strokeRect(5,5,246,34);
  ctx.font = 'bold 17px Georgia,serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  // Embossed effect: pale highlight shifted (+1,−1) then dark main text
  ctx.fillStyle = 'rgba(255,235,130,0.50)';
  ctx.fillText(label.toUpperCase(), 129, 21);
  ctx.fillStyle = '#1e0e00';
  ctx.fillText(label.toUpperCase(), 128, 22);
  const tex = new T.CanvasTexture(c);
  tex._owned = true;   // textura exclusiva deste sprite — descartável com ele (r128: Texture não tem userData)
  const sp  = new T.Sprite(new T.SpriteMaterial({map:tex, depthWrite:false}));
  sp.scale.set(0.46, 0.080, 1.0);
  return sp;
}

function _figureName(isMonster, classId, mType){
  if(!isMonster)
    return ({warrior:'Guerreiro',mage:'Pedro, o Tímido',rogue:'Luccas, o Astuto',cleric:'Frade Lewis',
             ranger:'Victor',bard:'Henrique, o Bardo',paladin:'Richard, o Cavaleiro'}[classId]) || 'Herói';
  return ({goblin:'Goblin',skeleton:'Skeleton',orc:'Orc Warrior',
           dark_mage:'Dark Mage',troll:'Troll',dragon:'Dragon'}[mType]) || 'Monster';
}

// ── Texture cache — persists across game_state rebuilds ──────────────────────
// For dungeon pawns: _pawnTexCache['mage'] = { frente: Texture, costas: Texture }
// For class-select:  _pawnTexCache['_cs_mage'] = Texture
const _pawnTexCache = {};

// ── Miniaturas 3D (GLB) — geradas por gerar_miniaturas_3d.py ──────────────────
// Malha com volume real (frente/costas texturizadas, espessura no perfil).
// Cache de templates: clona por instância; texturas/geometrias compartilhadas.
const _heroGLBCache  = {};   // classId -> THREE.Group (template) | 'erro'
const _heroGLBQueue  = {};   // classId -> [callbacks]

function _loadHeroGLB(T, classId, cb) {
  const cached = _heroGLBCache[classId];
  if (cached && cached !== 'erro') { cb(cached); return; }
  if (cached === 'erro') { cb(null); return; }
  if (_heroGLBQueue[classId]) { _heroGLBQueue[classId].push(cb); return; }
  if (!T.GLTFLoader) { cb(null); return; }

  _heroGLBQueue[classId] = [cb];
  // cache-buster: sem ele o navegador serve .glb antigos após regenerar os modelos
  new T.GLTFLoader().load(
    `assets/models3d/${classId}.glb?v=${Date.now()}`,
    g => {
      const tpl = g.scene;
      tpl.traverse(o => {
        if (o.isMesh) {
          o.castShadow = true;
          // leve emissivo para nunca ficar 100% preto contra a luz
          if (o.material) {
            o.material.emissive = new T.Color(0xffffff);
            o.material.emissiveIntensity = 0.05;
          }
        }
      });
      _heroGLBCache[classId] = tpl;
      _heroGLBQueue[classId].forEach(f => f(tpl));
      delete _heroGLBQueue[classId];
    },
    undefined,
    e => {
      console.warn(`[GLB] falha ao carregar ${classId}:`, e);
      _heroGLBCache[classId] = 'erro';
      _heroGLBQueue[classId].forEach(f => f(null));
      delete _heroGLBQueue[classId];
    }
  );
}

// GLB 3D desativado a pedido: heróis usam billboard 2D (frente.png) no tabuleiro
// e na seleção. O preload das miniaturas GLB foi removido (era trabalho inútil).

// Instancia a miniatura GLB dentro de grp. Retorna true se síncrono (cache),
// false se o template ainda não está disponível (carrega e adiciona async).
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

// Peão 3D do prisioneiro: base + billboard com a imagem editável (fallback: só a base).
// `sel` desenha um anel branco de seleção (controle manual na janela pós-turno).
function build3DPrisoner(T, pris, sel){
  const TH = 0.22;
  const Y0 = TH + 0.064;
  const grp = new T.Group();
  const baseCor = pris.freed ? 0x2e90c0 : 0x8a6d3b;
  const baseGeo = new T.CylinderGeometry(0.34, 0.38, 0.12, 24);
  const baseMat = new T.MeshStandardMaterial({ color: baseCor, roughness: 0.8 });
  const base = new T.Mesh(baseGeo, baseMat);
  base.position.y = 0.06;
  grp.add(base);
  if(sel){
    const ringGeo = new T.TorusGeometry(0.44, 0.05, 8, 28);
    const ringMat = new T.MeshBasicMaterial({ color: 0xffffff });
    const ring = new T.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = 0.13;
    grp.add(ring);
  }
  if(pris.image){
    _makeBillboardSprite(T, grp, `assets/pawns/prisioneiros/${pris.image}`,
      `_pris_${pris.image}`, Y0);
  }
  return grp;
}

// ── Billboard 2D voltado para a câmera (THREE.Sprite) ────────────────────────
// Dinâmica única de heróis e monstros: a figura SEMPRE aparece de frente e em pé
// na tela, em qualquer ângulo ou rotação da câmera. Usa apenas a `frente.png`
// (as costas nunca são vistas num billboard). SpriteMaterial é "unlit" — o
// sombreado já vem pintado na PNG, evitando a face escura do antigo standee.
//
// O tamanho respeita a PROPORÇÃO real da imagem (sem distorção): altura-alvo
// constante (H_ALVO) → todas as figuras com altura parecida; largura limitada
// (W_MAX) para figuras muito largas (ex.: anão com machado+escudo) não invadirem
// os tiles vizinhos. Como a textura carrega async, o tamanho final é aplicado no
// callback do loader; cada game_state reconstrói os peões, então o cache corrige.
//   texUrl   — caminho da PNG          cacheKey — chave em _pawnTexCache
//   Y0       — topo do disco da base (os "pés" da figura sentam aqui)
const _BB_H_ALVO = 2.05;   // altura no mundo (consistente entre figuras)
const _BB_W_MAX  = 1.55;   // largura máxima permitida
function _bbScaleFromImg(img, sf, mode){
  sf = sf || 1;
  const ar = (img && img.width && img.height) ? img.width / img.height : 0.55;
  if (mode === 'box'){
    // Cabe INTEIRA no tile (1 unidade de mundo): largura e altura ≤ _FIT_TILE_FRAC,
    // mantendo a proporção. Ignora porte/W_MAX — o tile já é o limite. (cobras)
    let w = _FIT_TILE_FRAC, h = _FIT_TILE_FRAC;
    if (ar >= 1) h = _FIT_TILE_FRAC / ar; else w = _FIT_TILE_FRAC * ar;
    return [w, h];
  }
  if (mode === 'width'){
    // Preenche a LARGURA do tile (borda a borda); a altura sobe na vertical pela
    // proporção real (sem cap), sem invadir os tiles vizinhos. Ignora porte/W_MAX. (ogros)
    const w = _FILL_WIDTH_FRAC;
    return [w, w / ar];
  }
  let w = _BB_H_ALVO * ar, h = _BB_H_ALVO;
  if (w > _BB_W_MAX){ w = _BB_W_MAX; h = _BB_W_MAX / ar; }
  return [w * sf, h * sf];
}
function _makeBillboardSprite(T, grp, texUrl, cacheKey, Y0, sizeFactor, mode) {
  const sf = sizeFactor || 1;
  let tex = _pawnTexCache[cacheKey];
  // depthTest:false + renderOrder alto → o peão NUNCA é ocultado pelas paredes 3D
  // (fica sempre em evidência, como pedido). alphaTest mantém as bordas nítidas.
  const mat = new T.SpriteMaterial({
    transparent: true,
    alphaTest:   0.12,
    depthWrite:  false,
    depthTest:   false,
  });
  const sp = new T.Sprite(mat);
  sp.center.set(0.5, 0);      // âncora nos "pés" → base plantada ao orbitar
  sp.position.set(0, Y0, 0);
  sp.renderOrder = 10;        // desenha depois das paredes/névoa
  // provisório até a textura carregar (real proporção é aplicada no callback)
  if (mode === 'box')        sp.scale.set(_FIT_TILE_FRAC, _FIT_TILE_FRAC, 1);
  else if (mode === 'width') sp.scale.set(_FILL_WIDTH_FRAC, _FILL_WIDTH_FRAC, 1);
  else                       sp.scale.set(_BB_H_ALVO * 0.55 * sf, _BB_H_ALVO * sf, 1);

  const aplicar = (texture) => {
    const [w, h] = _bbScaleFromImg(texture.image, sf, mode);
    sp.scale.set(w, h, 1);
  };
  if (tex) {
    mat.map = tex;
    if (tex.image && tex.image.width) aplicar(tex);   // já em cache e pronta
  } else {
    tex = new T.TextureLoader().load(_assetURL(texUrl), aplicar);
    _pawnTexCache[cacheKey] = tex;
    mat.map = tex;
  }
  grp.add(sp);
  return sp;
}

// Billboard PNG para monstros com campo `image` (apenas frente.png).
function _makeMonsterBillboard(T, grp, imageName, Y0, porte) {
  const mode = _FIT_TILE_PAWNS.has(imageName)   ? 'box'
             : _FILL_WIDTH_PAWNS.has(imageName) ? 'width'
             : null;
  _makeBillboardSprite(T, grp, `assets/pawns/monstros/${imageName}/${imageName}.png`,
                       '__mon_' + imageName, Y0, _pawnScaleFactor(porte), mode);
}

// Monstros ORIENTADOS (croc/lagarto): no 3D a criatura fica EM PÉ (billboard)
// centralizada nas 2 casas do corpo; a BASE alongada no chão (girada para o
// facing) indica a direção. Espelha para leste; norte/sul ficam em pé e a base
// mostra a direção. O flag `oriented` e o `facing` vêm do servidor. A arte é
// horizontal com a cabeça à ESQUERDA.
function _buildOrientedCreature3D(T, gx, gy, imageName, facing, isSelected){
  const TH  = 0.22;
  const grp = new T.Group();
  grp.userData.gridX = gx; grp.userData.gridY = gy;
  const f = (facing && facing.length === 2) ? facing : [-1, 0];
  // Centro do corpo (entre cabeça=âncora e cauda) em espaço LOCAL do grupo.
  const midX = -f[0] * 0.5, midZ = -f[1] * 0.5;
  // Ângulo Y da BASE no chão (segue o eixo cabeça→cauda = indica a direção).
  const angY = (f[0] ===  1) ? Math.PI
             : (f[1] ===  1) ? Math.PI / 2
             : (f[1] === -1) ? -Math.PI / 2 : 0;

  // Base no chão: posicionada no MEIO das 2 casas e girada para o facing.
  const body = new T.Group();
  body.position.set(midX, 0, midZ);
  body.rotation.y = angY;
  grp.add(body);

  // Sombra suave alongada (cobre as 2 casas).
  const shadow = new T.Mesh(
    new T.CircleGeometry(0.5, 24),
    new T.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.40, depthWrite: false })
  );
  shadow.rotation.x = -Math.PI / 2; shadow.scale.set(1.95, 0.95, 1);
  shadow.position.y = TH + 0.004; shadow.userData.isGroundDecal = true;
  body.add(shadow);

  // Disco de base escuro, achatado e alongado (estilo miniatura).
  const base = new T.Mesh(
    new T.CircleGeometry(0.48, 24),
    new T.MeshStandardMaterial({ color: 0x2a2018, roughness: 0.85, metalness: 0.0 })
  );
  base.rotation.x = -Math.PI / 2; base.scale.set(1.86, 0.84, 1);
  base.position.y = TH + 0.010; base.userData.isGroundDecal = true;
  body.add(base);

  // Anel de seleção alongado (no chão, segue o eixo do corpo).
  if (isSelected) {
    const sel = new T.Mesh(
      new T.TorusGeometry(0.5, 0.02, 8, 36),
      new T.MeshStandardMaterial({ color: 0xffd060, emissive: 0xffd060,
                                   emissiveIntensity: 1.6, roughness: 0.14, metalness: 0.9 })
    );
    sel.rotation.x = Math.PI / 2; sel.scale.set(1.7, 0.95, 1);
    sel.position.y = TH + 0.006; sel.userData.isSelectionRing = true;
    body.add(sel);
  }

  // Criatura EM PÉ: billboard (Sprite) sempre de frente p/ a câmera, centralizado
  // no meio das 2 casas. Espelha para leste (a arte tem a cabeça à esquerda).
  const flip = (f[0] === 1) ? -1 : 1;
  const mat = new T.SpriteMaterial({ transparent: true, alphaTest: 0.12,
                                     depthWrite: false, depthTest: false });
  const sp = new T.Sprite(mat);
  sp.center.set(0.5, 0);                       // pés na base
  sp.position.set(midX, TH + 0.064, midZ);     // no meio das 2 casas, sobre a base
  sp.renderOrder = 10;                          // sempre por cima das paredes/névoa
  const H = 2.05;                              // altura alvo (como os outros billboards)
  sp.scale.set(1.8 * flip, H, 1);              // provisório até a textura carregar
  const aplicar = (tex) => {
    const img = tex.image;
    if (img && img.width) {
      const ar = img.width / img.height;
      let w = H * ar, h = H;
      if (w > 2.0) { w = 2.0; h = w / ar; }   // largura ≤ ~2 casas (criatura larga e baixa)
      sp.scale.set(w * flip, h, 1);
    }
  };
  const cacheKey = '__mon_' + imageName;
  let tex = _pawnTexCache[cacheKey];
  if (tex) { mat.map = tex; if (tex.image && tex.image.width) aplicar(tex); }
  else {
    tex = new T.TextureLoader().load(
      _assetURL(`assets/pawns/monstros/${imageName}/${imageName}.png`), aplicar);
    _pawnTexCache[cacheKey] = tex; mat.map = tex;
  }
  grp.add(sp);

  grp.position.set(gx, 0, gy);
  return grp;
}

// hexColor  — class color (#rrggbb)  isMonster — true/false
// isMe      — local player?          isCurrent — active turn?
// gx,gy     — grid coordinates       classId   — 'warrior'|'mage'|…
// mType     — 'goblin'|'orc'|…      (monster only)
// mOriented/mFacing — monstro de 2 casas em pé cobrindo as 2 casas (croc/lagarto)

function build3DFig(hexColor, isMonster, isMe, isCurrent, gx, gy, classId, mType, isSelected, mImage, mPorte, mOriented, mFacing){
  const T   = g3.T;
  if (isMonster && mOriented && mImage) {
    return _buildOrientedCreature3D(T, gx, gy, mImage, mFacing, isSelected);
  }
  const TH  = 0.22;                        // floor tile thickness (must match init3D)
  const grp = new T.Group();
  grp.userData.gridX = gx;               // used by hover/selection animation loop
  grp.userData.gridY = gy;
  const clr = new T.Color(hexColor);

  const baseGrp = new T.Group(); baseGrp.name = 'base'; grp.add(baseGrp);

  // Blob shadow — soft dark oval on the tile surface
  const shadowR = isMonster ? 0.42 : 0.36;
  const shadowMesh = new T.Mesh(
    new T.CircleGeometry(shadowR, 24),
    new T.MeshBasicMaterial({ color:0x000000, transparent:true, opacity:0.55, depthWrite:false })
  );
  shadowMesh.rotation.x = -Math.PI / 2;
  shadowMesh.position.set(0, TH + 0.003, 0);
  shadowMesh.scale.set(1.0, 1.0, 0.70);
  shadowMesh.userData.isGroundDecal = true;
  baseGrp.add(shadowMesh);

  // Disco de base em MADEIRA ESCURA com leve brilho da cor do herói por dentro
  const baseR = isMonster ? 0.37 : 0.32;
  _addM(baseGrp,
    new T.CylinderGeometry(baseR, baseR+0.012, 0.074, 26),
    { color:new T.Color(0x35200f), roughness:0.82, metalness:0.00,
      emissive:clr.clone().multiplyScalar(0.06), emissiveIntensity:1.0 },
    [0, TH+0.037, 0]
  );

  // Colored emissive rim ring — identifies hero by color even in deep shadow
  const rimRing = new T.Mesh(
    new T.TorusGeometry(baseR+0.018, 0.009, 5, 28),
    new T.MeshStandardMaterial({
      color: clr, emissive: clr.clone(), emissiveIntensity: VC.pawns.rimEmissiveIntensity,
      roughness: 0.35, metalness: 0.0
    })
  );
  rimRing.rotation.x = Math.PI / 2;
  rimRing.position.set(0, TH + 0.074, 0);
  rimRing.castShadow = false;
  baseGrp.add(rimRing);

  // Tampo de madeira escura (tora) — textura procedural em CircleGeometry
  const stoneTex = _getWoodTopTex(T);
  const stoneTop = new T.Mesh(
    new T.CircleGeometry(baseR - 0.012, 24),
    new T.MeshStandardMaterial({ map:stoneTex, bumpMap:stoneTex, bumpScale:0.006,
                                  roughness:0.80, metalness:0.00 })
  );
  stoneTop.rotation.x    = -Math.PI / 2;
  stoneTop.position.set(0, TH + 0.075, 0);
  stoneTop.userData.isGroundDecal = true;
  baseGrp.add(stoneTop);

  // Gold name-plate Sprite — always faces camera, sits at the base front edge
  const displayName = _figureName(isMonster, classId, mType);
  const plate = _makeNamePlate(T, displayName);
  plate.position.set(0, TH + 0.055, baseR * 0.82);
  baseGrp.add(plate);

  // Thin gold rim for the local player's figure
  if(isMe){
    const rim = new T.Mesh(
      new T.TorusGeometry(baseR+0.014, 0.010, 5, 24),
      new T.MeshStandardMaterial({ color:new T.Color(0xf0c040), roughness:0.25, metalness:0.85 })
    );
    rim.rotation.x = Math.PI/2;
    rim.position.set(0, TH+0.074, 0);
    rim.castShadow = false;
    baseGrp.add(rim);
  }

  // ── Active-turn halo: pulsing gold torus + warm point-light underfoot ────────
  // Both are animated each frame in startLoop3D via userData flags.
  if(isCurrent){
    const ring = _addM(grp,
      new T.TorusGeometry(baseR+0.10, 0.026, 8, 32),
      { color:0xf0c040, emissive:new T.Color(0xf0c040), emissiveIntensity:1.8, roughness:0.18 },
      [0, TH+0.010, 0]
    );
    ring.rotation.x  = Math.PI / 2;
    ring.userData.isPulseRing = true;

    // PointLight sitting just above the tile — illuminates the figure from below
    const haloLight = new T.PointLight(0xf0a820, 1.4, 1.6);
    haloLight.position.set(0, TH + 0.07, 0);
    haloLight.userData.isHaloLight = true;
    grp.add(haloLight);
  }

  const Y0 = TH + 0.064;    // top of base disc; all builders start from here
  // Booster de resolução: silhuetas suaves (menos poligonal) em todos os peões
  _withSmoothGeo(T, () => {
  if(isMonster){
    if(mImage){
      _makeMonsterBillboard(T, grp, mImage, Y0, mPorte);
    } else {
      switch(mType){
        case 'goblin':    _miniGoblin(grp, clr, Y0);    break;
        case 'skeleton':  _miniSkeleton(grp, clr, Y0);  break;
        case 'orc':       _miniOrc(grp, clr, Y0);       break;
        case 'dark_mage': _miniDarkMage(grp, clr, Y0);  break;
        case 'troll':     _miniTroll(grp, clr, Y0);     break;
        case 'dragon':    _miniDragon(grp, clr, Y0);    break;
        default:          _miniGenericMonster(grp, clr, Y0); break;
      }
    }
  } else {
    _makeCharacterPawn(T, grp, classId, clr, Y0);
  }
  });

  // ── Selection ring — golden glowing torus at base, excluded from outline ──────
  if(isSelected){
    const selR = (isMonster ? 0.37 : 0.32) + 0.14;
    const selRing = new T.Mesh(
      new T.TorusGeometry(selR, 0.020, 8, 36),
      new T.MeshStandardMaterial({
        color: new T.Color(0xffd060),
        emissive: new T.Color(0xffd060),
        emissiveIntensity: 1.6,
        roughness: 0.14, metalness: 0.90
      })
    );
    selRing.rotation.x = Math.PI / 2;
    selRing.position.set(0, TH + 0.006, 0);
    selRing.castShadow = false;
    selRing.userData.isSelectionRing = true;
    grp.add(selRing);
  }

  // ── Dark outline pass — recursive backface-shell over every solid mesh ────────
  // Uses grp.traverse() so outlines work correctly on nested sub-groups (arm groups,
  // torso groups). Each outline is added to child.parent (same coordinate space).
  const outlineMat = new T.MeshBasicMaterial({ color:0x04030a, side:T.BackSide });
  const toOutline  = [];
  grp.traverse(child => {
    if(!(child instanceof T.Mesh)) return;
    if(child.userData.isGroundDecal || child.userData.isPulseRing ||
       child.userData.isOutline || child.userData.isSelectionRing) return;
    toOutline.push(child);
  });
  for(const child of toOutline){
    const om = new T.Mesh(child.geometry, outlineMat);
    om.position.copy(child.position);
    om.rotation.copy(child.rotation);
    om.scale.copy(child.scale).multiplyScalar(1.085);
    om.castShadow        = false;
    om.userData.isOutline = true;
    child.parent.add(om);   // same parent group = correct local transform
  }

  // A antiga PointLight individual sobre cada peão foi removida — a soma de
  // ambient + dirMain + dirPawn + visionLamp já garante visibilidade, e cada
  // luz a menos por peão reduz o custo de TODOS os materiais da cena.

  grp.position.set(gx, 0, gy);
  return grp;
}

// ── Cadáver 3D: marca onde um monstro derrotado pode ser reanimado ────────────
// Mancha escura + anel roxo emissivo (ponto de reanimação) + corpo tombado + crânio.
function build3DCorpse(c){
  const T = g3.T, TH = 0.22;
  const grp = new T.Group();
  // Mancha escura no chão
  const stain = new T.Mesh(
    new T.CircleGeometry(0.40, 24),
    new T.MeshBasicMaterial({ color:0x140018, transparent:true, opacity:0.72, depthWrite:false })
  );
  stain.rotation.x = -Math.PI/2; stain.position.set(0, TH+0.004, 0);
  stain.userData.isGroundDecal = true; grp.add(stain);
  // Anel roxo emissivo — indica ponto de reanimação
  const ring = new T.Mesh(
    new T.TorusGeometry(0.34, 0.02, 8, 28),
    new T.MeshStandardMaterial({ color:0xcc44ff, emissive:0x9900cc, emissiveIntensity:1.4, roughness:0.30, metalness:0.0 })
  );
  ring.rotation.x = Math.PI/2; ring.position.set(0, TH+0.02, 0); ring.castShadow = false; grp.add(ring);
  // Corpo tombado — esfera achatada escura
  const body = new T.Mesh(
    new T.SphereGeometry(0.20, 12, 10),
    new T.MeshStandardMaterial({ color:0x2a2030, roughness:0.90, metalness:0.05, emissive:0x1a0022, emissiveIntensity:0.4 })
  );
  body.scale.set(1.3, 0.42, 0.9); body.position.set(0, TH+0.10, 0); grp.add(body);
  // Crânio claro sobre o corpo
  const skull = new T.Mesh(
    new T.SphereGeometry(0.085, 10, 8),
    new T.MeshStandardMaterial({ color:0xd8d0c0, roughness:0.80, metalness:0.0 })
  );
  skull.position.set(0.12, TH+0.13, 0); grp.add(skull);
  grp.position.set(c.pos[0], 0, c.pos[1]);
  return grp;
}

// ── HERO: Warrior — dwarven axe fighter, squat/wide, 1/7 proportions ─────────
function _miniWarrior(g, clr, Y){
  const T    = g3.T;
  const plat = {color:new T.Color(0x3a3a3a),roughness:0.90,metalness:0.60}; // dark plate
  const rust = {color:new T.Color(0x5a3018),roughness:0.95,metalness:0.25}; // rust accent
  const rivM = {color:new T.Color(0x606868),roughness:0.58,metalness:0.80}; // rivet metal
  const shld = {color:new T.Color(0x4a4a52),roughness:0.68,metalness:0.76}; // shield metal
  const steW = {color:new T.Color(0x909898),roughness:0.44,metalness:0.86}; // dull axe steel
  const edgM = {color:new T.Color(0xc0c8d0),roughness:0.28,metalness:0.92}; // blade edge
  const sk   = _mSkin(0xb47840);
  const hairC = _mClth(0x1a1414);   // jet black hair
  const gryH  = _mClth(0x888888);   // gray streaks
  const woodD = _mWood(0x1e0c04);   // near-black axe handle

  // DWARF: torso low + wide, legs short and splayed
  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.102, 0);
  torso.rotation.x =  0.08;   // forward combat crouch
  torso.rotation.z = -0.05;   // lean toward axe side
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  const lL = _addM(legs, new T.CylinderGeometry(0.064,0.076,0.148,8), plat, [-0.090,Y+0.074,0.014]);
  lL.rotation.x= 0.20; lL.rotation.z=-0.15;
  const lR = _addM(legs, new T.CylinderGeometry(0.064,0.076,0.148,8), plat, [ 0.094,Y+0.074,-0.016]);
  lR.rotation.x=-0.16; lR.rotation.z= 0.17;
  // Sabatons (heavy armored boots)
  _addM(legs, new T.BoxGeometry(0.106,0.040,0.118), plat, [-0.090,Y+0.010, 0.030]);
  _addM(legs, new T.BoxGeometry(0.106,0.040,0.118), plat, [ 0.094,Y+0.010,-0.012]);
  // Knee plates
  _addM(legs, new T.BoxGeometry(0.088,0.032,0.072), plat, [-0.090,Y+0.142, 0.046]);
  _addM(legs, new T.BoxGeometry(0.088,0.032,0.072), plat, [ 0.094,Y+0.142,-0.032]);
  // Knee rivets L + R
  for(const sx of [-0.090, 0.094]){
    _addM(legs, new T.SphereGeometry(0.009,5,4), rivM, [sx-0.028,Y+0.148,-0.038]);
    _addM(legs, new T.SphereGeometry(0.009,5,4), rivM, [sx+0.028,Y+0.148,-0.038]);
  }

  // ── Torso — wide squat plate, gorget, tasset, front rivets ────────────────
  _addM(torso, new T.BoxGeometry(0.320,0.192,0.176), plat, [0,0.096,0]);
  _addM(torso, new T.BoxGeometry(0.010,0.188,0.014), rust, [0,0.096,-0.090]); // center seam
  _addM(torso, new T.BoxGeometry(0.318,0.024,0.014), rust, [0,0.040,-0.090]); // lower crease
  _addM(torso, new T.BoxGeometry(0.328,0.030,0.180), plat, [0,-0.007,0]);      // tasset plate
  _addM(torso, new T.CylinderGeometry(0.062,0.080,0.050,8), plat, [0,0.202,0]); // gorget
  // 3×2 front rivets
  for(const px of [-0.120,0,0.120]){
    for(const py of [0.056,0.146]){
      _addM(torso, new T.SphereGeometry(0.009,5,4), rivM, [px,py,-0.090]);
    }
  }
  // Pauldrons — large, dented
  for(const sx of [-0.214,0.214]){
    _addM(acc, new T.SphereGeometry(0.084,8,7), plat, [sx,0.168,0]);
    _addM(acc, new T.BoxGeometry(0.106,0.054,0.106), plat, [sx,0.216,0]);
    _addM(acc, new T.SphereGeometry(0.009,5,4), rivM, [sx,0.198,-0.078]);
    _addM(acc, new T.SphereGeometry(0.009,5,4), rivM, [sx*0.84,0.238,-0.076]);
  }

  const shA = new T.Group(); shA.name='shieldArm'; arms.add(shA);
  shA.position.set(-0.202,0.094,0); shA.rotation.z=0.32; shA.rotation.x=0.22;

  _addM(shA, new T.CylinderGeometry(0.054,0.064,0.170,7), plat, [0,0.085,0]);
  _addM(shA, new T.SphereGeometry(0.009,5,4), rivM, [0,0.168,-0.056]); // elbow rivet
  // Round shield disc (CylinderGeometry — flat faces in arm-local XZ plane)
  _addM(shA, new T.CylinderGeometry(0.150,0.150,0.026,14), shld, [0,0.232,0.028]);
  const shRim = _addM(shA, new T.TorusGeometry(0.150,0.012,5,18), shld, [0,0.232,0.028]);
  shRim.rotation.x = Math.PI/2; // torus lies in XZ plane matching disc
  // 8 rim spikes pointing outward in the disc plane
  for(let i=0;i<8;i++){
    const a = (i/8)*Math.PI*2;
    const sp = _addM(shA, new T.ConeGeometry(0.009,0.040,4), steW,
      [Math.cos(a)*0.169, 0.232, Math.sin(a)*0.169+0.028]);
    sp.rotation.z = -Math.PI/2;
    sp.rotation.y = -a;
  }
  // Engraved rune cross on shield face + center boss
  _addM(shA, new T.BoxGeometry(0.010,0.014,0.084), shld, [0,0.246,0.028]); // Z-bar
  _addM(shA, new T.BoxGeometry(0.084,0.014,0.010), shld, [0,0.246,0.028]); // X-bar
  _addM(shA, new T.SphereGeometry(0.024,7,6), steW, [0,0.252,0.030]); // boss

  // ── Axe arm — RIGHT, raised to shoulder, combat ready ─────────────────────
  const wA = new T.Group(); wA.name='axeArm'; arms.add(wA);
  wA.position.set(0.202,0.118,0); wA.rotation.z=-0.54; wA.rotation.y=-0.12;

  _addM(wA, new T.CylinderGeometry(0.054,0.064,0.170,7), plat, [0,0.085,0]);
  _addM(wA, new T.SphereGeometry(0.009,5,4), rivM, [0,0.168,-0.056]); // elbow rivet
  _addM(wA, new T.BoxGeometry(0.076,0.058,0.080), plat, [0,0.226,0]); // gauntlet fist

  const weap = new T.Group(); weap.name='weapon'; wA.add(weap);
  // Long dark wood handle — extends well above and below fist
  _addM(weap, new T.CylinderGeometry(0.013,0.016,0.62,6), woodD, [0,0.424,0]); // Y=0.114-0.734
  // Leather grip-wrap bands
  for(let i=0;i<4;i++){
    _addM(weap, new T.CylinderGeometry(0.018,0.018,0.012,6),
      _mLeather(0x140806), [0, 0.200+i*0.044, 0]);
  }
  _addM(weap, new T.SphereGeometry(0.024,6,5), steW, [0,0.118,0]); // pommel cap
  // Axe head socket (connects double blades to handle at top)
  _addM(weap, new T.BoxGeometry(0.048,0.106,0.044), steW, [0,0.718,0]);
  // Double blades — left + right, large crescent-shaped, slightly tilted
  const blL = _addM(weap, new T.BoxGeometry(0.198,0.082,0.020), steW, [-0.099,0.744,0]);
  blL.rotation.z =  0.18;
  const blR = _addM(weap, new T.BoxGeometry(0.198,0.082,0.020), steW, [ 0.099,0.744,0]);
  blR.rotation.z = -0.18;
  // Cutting edge highlights (brighter thin strip at outer tips)
  const eL = _addM(weap, new T.BoxGeometry(0.202,0.014,0.016), edgM, [-0.090,0.788,0]);
  eL.rotation.z =  0.18;
  const eR = _addM(weap, new T.BoxGeometry(0.202,0.014,0.016), edgM, [ 0.090,0.788,0]);
  eR.rotation.z = -0.18;
  // Axe eye inset (decorative hole through socket)
  _addM(weap, new T.BoxGeometry(0.022,0.042,0.048),
    {color:new T.Color(0x282828),roughness:0.92,metalness:0.38}, [0,0.718,0]);

  // ── Head — square dwarven face, wild hair, thick beard ────────────────────
  // Face sphere — 1/7 at dwarf scale (≈0.082)
  _addM(head, new T.SphereGeometry(0.082,10,9), sk, [0,0.216,0]);
  // Square jaw box overlapping lower face
  _addM(head, new T.BoxGeometry(0.156,0.056,0.118), sk, [0,0.174,0]);
  // Deep-set scowling eyes
  _addM(head, new T.SphereGeometry(0.012,5,4), _mClth(0x201408), [-0.030,0.220,-0.070]);
  _addM(head, new T.SphereGeometry(0.012,5,4), _mClth(0x201408), [ 0.030,0.220,-0.070]);
  // Heavy furrowed brows
  _addM(head, new T.BoxGeometry(0.046,0.013,0.010), hairC, [-0.022,0.242,-0.072]);
  _addM(head, new T.BoxGeometry(0.046,0.013,0.010), hairC, [ 0.022,0.242,-0.072]);
  // Broad flat nose
  _addM(head, new T.SphereGeometry(0.020,6,5), sk, [0,0.206,-0.076]);
  // Scowling mouth (thin, downturned)
  _addM(head, new T.BoxGeometry(0.052,0.010,0.010), sk, [0,0.184,-0.070]);
  _addM(head, new T.BoxGeometry(0.010,0.015,0.010), _mClth(0x8a4830), [-0.028,0.180,-0.069]);
  _addM(head, new T.BoxGeometry(0.010,0.015,0.010), _mClth(0x8a4830), [ 0.028,0.180,-0.069]);
  // Scar — diagonal raised ridge on left cheek
  const scar = _addM(head, new T.BoxGeometry(0.006,0.048,0.007),
    {color:new T.Color(0xb08858),roughness:0.88,metalness:0}, [-0.054,0.206,-0.064]);
  scar.rotation.z = 0.40;

  // Wild black hair (thick, unkempt)
  const hCap = _addM(head,
    new T.SphereGeometry(0.086,9,7,0,Math.PI*2,0,Math.PI*0.50), hairC, [0,0.224,0]);
  hCap.rotation.x = 0.04;
  // Side tufts sticking out wildly
  const htL = _addM(head, new T.CylinderGeometry(0.022,0.032,0.050,6), hairC, [-0.088,0.240,0.018]);
  htL.rotation.z=-0.36; htL.rotation.x=-0.12;
  const htR = _addM(head, new T.CylinderGeometry(0.022,0.032,0.050,6), hairC, [ 0.088,0.240,0.018]);
  htR.rotation.z= 0.36; htR.rotation.x=-0.12;
  // Gray streak overlays on hair
  _addM(head, new T.BoxGeometry(0.010,0.062,0.008), gryH, [-0.044,0.270,-0.040]);
  _addM(head, new T.BoxGeometry(0.010,0.062,0.008), gryH, [ 0.040,0.264,-0.040]);

  // Thick curly beard — main mass + side spheres + fork prongs
  _addM(head, new T.CylinderGeometry(0.016,0.070,0.154,8), hairC, [0,0.134,-0.040]);
  _addM(head, new T.SphereGeometry(0.050,8,6), hairC,  [0,   0.118,-0.042]); // chin bulk
  _addM(head, new T.SphereGeometry(0.038,7,5), hairC,  [-0.058,0.124,-0.038]); // L cheek
  _addM(head, new T.SphereGeometry(0.038,7,5), hairC,  [ 0.058,0.124,-0.038]); // R cheek
  _addM(head, new T.CylinderGeometry(0.012,0.022,0.058,6), hairC, [-0.028,0.070,-0.046]); // L prong
  _addM(head, new T.CylinderGeometry(0.012,0.022,0.058,6), hairC, [ 0.028,0.070,-0.046]); // R prong
  // Gray streaks in beard
  _addM(head, new T.BoxGeometry(0.008,0.122,0.008), gryH, [-0.018,0.128,-0.060]);
  _addM(head, new T.BoxGeometry(0.008,0.122,0.008), gryH, [ 0.018,0.128,-0.060]);
  // Drooping mustache halves
  _addM(head, new T.CylinderGeometry(0.013,0.018,0.056,5), hairC, [-0.030,0.192,-0.074]);
  _addM(head, new T.CylinderGeometry(0.013,0.018,0.056,5), hairC, [ 0.030,0.192,-0.074]);
}

// ── HERO: Mage — dark sorcerer, orb + skull staff, 1/7 proportions ──────────────
function _miniMage(g, clr, Y){
  const T     = g3.T;
  const rpurp = _mClth(0x180820);    // very dark purple-black robe
  const ipurp = _mClth(0x2e1258);    // inner purple — sleeve lining visible at cuff
  const dklth = _mLeather(0x181010); // dark leather armor (pectoral)
  const bone  = _mClth(0xd4cdb0);    // bone/ivory — skull
  const silv  = {color:new T.Color(0x9898a8),roughness:0.44,metalness:0.68}; // aged silver
  const sk    = _mSkin(0xd4d0c4);    // pale skin
  const hairC = _mClth(0x0a0808);    // jet black hair
  const engM  = _mGlw(0x9900ff,1.5); // purple energy orb
  const skWd  = _mWood(0x100808);    // near-black skull staff wood

  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.235, 0);
  torso.rotation.x = 0.12;          // dramatic forward lean
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  _addM(legs, new T.CylinderGeometry(0.070,0.162,0.46,10), rpurp, [0,Y+0.232,0]);
  _addM(legs, new T.CylinderGeometry(0.162,0.164,0.012,10), silv, [0,Y+0.008,0]); // hem silver
  // Belt
  _addM(legs, new T.CylinderGeometry(0.080,0.080,0.022,10), dklth, [0,Y+0.457,0]);
  // Skull belt charm
  _addM(legs, new T.SphereGeometry(0.024,8,7), bone,                 [0,   Y+0.450,-0.084]);
  _addM(legs, new T.SphereGeometry(0.008,5,4), _mClth(0x080808), [-0.011,Y+0.454,-0.104]);
  _addM(legs, new T.SphereGeometry(0.008,5,4), _mClth(0x080808), [ 0.011,Y+0.454,-0.104]);
  _addM(legs, new T.BoxGeometry(0.020,0.009,0.008), bone,             [0,   Y+0.438,-0.096]);

  _addM(torso, new T.CylinderGeometry(0.068,0.082,0.195,9), rpurp, [0,0.098,0]);
  _addM(torso, new T.BoxGeometry(0.080,0.096,0.016), dklth,          [0,0.092,-0.068]); // breastplate
  _addM(torso, new T.BoxGeometry(0.084,0.008,0.018), silv, [0, 0.140,-0.070]); // top trim
  _addM(torso, new T.BoxGeometry(0.084,0.008,0.018), silv, [0, 0.044,-0.070]); // bot trim
  _addM(torso, new T.BoxGeometry(0.008,0.104,0.018), silv, [-0.038,0.092,-0.070]); // L trim
  _addM(torso, new T.BoxGeometry(0.008,0.104,0.018), silv, [ 0.038,0.092,-0.070]); // R trim

  // ── Magic arm — LEFT, raised dramatically, energy orb above open hand ─────
  const mA = new T.Group(); mA.name='magicArm'; arms.add(mA);
  mA.position.set(-0.126,0.098,0); mA.rotation.z=0.72; mA.rotation.x=-0.32;

  _addM(mA, new T.CylinderGeometry(0.048,0.058,0.20,7), rpurp, [0,0.100,0]); // sleeve
  _addM(mA, new T.CylinderGeometry(0.036,0.046,0.026,8), ipurp, [0,0.200,0]); // inner cuff
  _addM(mA, new T.CylinderGeometry(0.023,0.029,0.086,6), sk,    [0,0.252,0]); // wrist
  const palmM = _addM(mA, new T.SphereGeometry(0.030,7,6), sk, [0,0.312,0]);
  palmM.scale.y = 0.58; // flattened open palm
  for(let fi=0;fi<4;fi++){
    const fx = -0.028+fi*0.019;
    _addM(mA, new T.CylinderGeometry(0.007,0.009,0.048,5), sk, [fx,0.352,-0.005]);
  }
  _addM(mA, new T.CylinderGeometry(0.008,0.010,0.036,5), sk, [-0.044,0.328,0.016]); // thumb
  // Energy orb hovering above hand
  const orbGrp = new T.Group(); orbGrp.name='energyOrb'; mA.add(orbGrp);
  orbGrp.position.set(0,0.424,0);
  _addM(orbGrp, new T.SphereGeometry(0.034,9,8), engM, [0,0,0]);
  const eRing = _addM(orbGrp, new T.TorusGeometry(0.044,0.007,5,14), engM, [0,0,0]);
  eRing.rotation.x = Math.PI*0.38;
  const pLight = new T.PointLight(0x9900ff, 1.8, 0.44);
  orbGrp.add(pLight);

  // ── Staff arm — RIGHT, lowered, gripping short skull staff ────────────────
  const stA = new T.Group(); stA.name='staffArm'; arms.add(stA);
  stA.position.set(0.136,0.064,0); stA.rotation.z=-0.18; stA.rotation.x=0.16;

  _addM(stA, new T.CylinderGeometry(0.048,0.058,0.20,7), rpurp, [0,0.100,0]); // sleeve
  _addM(stA, new T.CylinderGeometry(0.036,0.046,0.026,8), ipurp, [0,0.200,0]); // inner cuff
  _addM(stA, new T.CylinderGeometry(0.023,0.029,0.086,6), sk,    [0,0.252,0]); // wrist
  _addM(stA, new T.SphereGeometry(0.028,7,6), sk, [0,0.304,0]); // gripping fist
  for(let fi=0;fi<4;fi++){
    const fx = -0.021+fi*0.014;
    _addM(stA, new T.CylinderGeometry(0.006,0.008,0.030,5), sk, [fx,0.336,-0.014]);
  }
  // Short skull staff
  const weap = new T.Group(); weap.name='weapon'; stA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.011,0.013,0.30,6), skWd, [0,0.320,0]); // pole
  _addM(weap, new T.CylinderGeometry(0.015,0.015,0.010,7), silv, [0,0.474,0]); // collar
  const skull = _addM(weap, new T.SphereGeometry(0.032,8,7), bone, [0,0.510,0]);
  skull.scale.y = 0.82; // slightly flat skull dome
  _addM(weap, new T.SphereGeometry(0.009,5,4), _mClth(0x060606), [-0.014,0.516,-0.026]);
  _addM(weap, new T.SphereGeometry(0.009,5,4), _mClth(0x060606), [ 0.014,0.516,-0.026]);
  _addM(weap, new T.BoxGeometry(0.030,0.010,0.012), bone,           [0,0.490,-0.016]); // jaw
  _addM(weap, new T.BoxGeometry(0.026,0.005,0.010), _mClth(0x060606), [0,0.486,-0.022]); // teeth

  // ── Head — 1/7, pale, deep-set eyes, threatening expression ──────────────
  _addM(head, new T.SphereGeometry(0.092,10,9), sk, [0,0.314,0]); // pale face
  _addM(head, new T.SphereGeometry(0.012,5,4), _mClth(0x1a0838), [-0.028,0.322,-0.082]); // L eye
  _addM(head, new T.SphereGeometry(0.012,5,4), _mClth(0x1a0838), [ 0.028,0.322,-0.082]); // R eye
  _addM(head, new T.SphereGeometry(0.013,5,5), sk, [0,0.308,-0.088]); // sharp nose
  // Frowning mouth
  _addM(head, new T.BoxGeometry(0.026,0.007,0.007), _mClth(0x7c3830), [0,0.288,-0.083]);
  _addM(head, new T.BoxGeometry(0.007,0.009,0.007), _mClth(0x7c3830), [-0.015,0.284,-0.082]);
  _addM(head, new T.BoxGeometry(0.007,0.009,0.007), _mClth(0x7c3830), [ 0.015,0.284,-0.082]);
  // Furrowed brows
  _addM(head, new T.BoxGeometry(0.020,0.006,0.007), _mClth(0x100a1c), [-0.022,0.336,-0.086]);
  _addM(head, new T.BoxGeometry(0.020,0.006,0.007), _mClth(0x100a1c), [ 0.022,0.336,-0.086]);

  // Long straight black hair
  const hairCap = _addM(head,
    new T.SphereGeometry(0.094,9,7,0,Math.PI*2,0,Math.PI*0.52), hairC, [0,0.318,0]);
  hairCap.rotation.x = 0.04;
  const hL = _addM(head, new T.BoxGeometry(0.048,0.312,0.005), hairC, [-0.082,0.230,-0.014]);
  hL.rotation.z =  0.14; hL.rotation.x = 0.06;
  const hR = _addM(head, new T.BoxGeometry(0.048,0.312,0.005), hairC, [ 0.082,0.230,-0.014]);
  hR.rotation.z = -0.14; hR.rotation.x = 0.06;
  const hF = _addM(head, new T.BoxGeometry(0.030,0.272,0.005), hairC, [0,0.212,-0.078]);
  hF.rotation.x = 0.10;  // hangs over chest
  _addM(head, new T.BoxGeometry(0.068,0.282,0.005), hairC, [0,0.226,0.078]); // back mass

  // Fallen hood — bunched at back of neck
  _addM(acc, new T.CylinderGeometry(0.072,0.090,0.050,9), rpurp, [0,0.280,0.060]);
  _addM(acc, new T.BoxGeometry(0.108,0.038,0.024), rpurp, [0,0.262,0.076]); // drape
}

// ── HERO: Rogue — relaxed alert stance, wide-brim hat, hand crossbow ─────────
function _miniRogue(g, clr, Y){
  const T    = g3.T;
  const navy = _mClth(0x1e2e60);     // navy blue — trousers + shirt
  const capeC= _mClth(0x6878a4);     // medium gray — long cape
  const hatM = _mClth(0x2e3848);     // dark gray — wide-brim hat
  const lth  = _mLeather(0x7a3810);  // brown leather — boots, belt
  const sk   = _mSkin(0xd4a870);
  const teal = _mClth(0x14b4c4);     // turquoise — feather
  const xbow = _mMtl(0x888898);      // metal — crossbow fittings
  const xwod = _mWood(0x5c2818);     // dark wood — crossbow stock

  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.200, 0);
  torso.rotation.x = -0.08;
  torso.rotation.z = -0.06;          // weight-on-left-foot lean
  const arms  = new T.Group(); arms.name  = 'arms';        torso.add(arms);
  const head  = new T.Group(); head.name  = 'head';        torso.add(head);
  const acc   = new T.Group(); acc.name   = 'accessories'; torso.add(acc);

  // Left boot — planted, weight-bearing
  _addM(legs, new T.CylinderGeometry(0.034,0.046,0.22,8), lth, [-0.054,Y+0.112,0.010]);
  _addM(legs, new T.CylinderGeometry(0.050,0.050,0.020,8), lth, [-0.054,Y+0.226,0.010]); // cuff
  const btL = _addM(legs, new T.BoxGeometry(0.058,0.024,0.080), lth, [-0.054,Y+0.010,0.036]);
  btL.rotation.z = -0.03;
  // Right boot — slightly back, relaxed
  const bR = _addM(legs, new T.CylinderGeometry(0.032,0.044,0.20,8), lth, [0.060,Y+0.102,-0.022]);
  bR.rotation.x = 0.14; bR.rotation.z = 0.04;
  _addM(legs, new T.CylinderGeometry(0.048,0.048,0.018,8), lth, [0.060,Y+0.210,-0.022]);
  const btR = _addM(legs, new T.BoxGeometry(0.056,0.022,0.072), lth, [0.060,Y+0.010,-0.052]);
  btR.rotation.x = 0.12;

  const tL = _addM(legs, new T.CylinderGeometry(0.040,0.050,0.18,7), navy, [-0.054,Y+0.300,0.006]);
  tL.rotation.z = -0.05;
  const tR = _addM(legs, new T.CylinderGeometry(0.038,0.048,0.16,7), navy, [ 0.060,Y+0.288,-0.014]);
  tR.rotation.x = 0.12; tR.rotation.z = 0.05;
  // Knee crease ring (left)
  const kc = _addM(legs, new T.TorusGeometry(0.044,0.006,4,9), navy, [-0.054,Y+0.216,0.006]);
  kc.rotation.x = Math.PI/2;

  _addM(legs, new T.CylinderGeometry(0.068,0.072,0.022,10), lth, [0,Y+0.394,0]);
  _addM(legs, new T.CylinderGeometry(0.070,0.074,0.016,10), lth, [0,Y+0.372,0]);
  _addM(legs, new T.BoxGeometry(0.028,0.018,0.008), xbow, [0.000,Y+0.394,-0.073]); // main buckle
  _addM(legs, new T.BoxGeometry(0.022,0.014,0.008), xbow, [0.040,Y+0.376,-0.073]); // second buckle
  _addM(legs, new T.BoxGeometry(0.052,0.044,0.038), lth, [-0.090,Y+0.374,0.036]);  // left pouch
  _addM(legs, new T.SphereGeometry(0.010,5,4), xbow, [-0.090,Y+0.399,0.056]);      // pouch clasp
  _addM(legs, new T.BoxGeometry(0.036,0.032,0.026), lth, [0.096,Y+0.374,0.034]);   // right pouch

  _addM(torso, new T.CylinderGeometry(0.058,0.110,0.34,8), navy, [0,0.170,0]);
  _addM(torso, new T.BoxGeometry(0.028,0.068,0.010), _mClth(0x0c141e), [0,0.228,-0.059]); // V-neck
  _addM(torso, new T.SphereGeometry(0.058,6,5), navy, [-0.118,0.348,0.000]); // left shoulder
  _addM(torso, new T.SphereGeometry(0.060,6,5), navy, [ 0.118,0.348,0.000]); // right shoulder

  // ── CAPE — medium gray, long, thrown over left shoulder ───────────────
  // Shoulder drape piece (sits on left shoulder)
  const csh = _addM(acc, new T.SphereGeometry(0.096,8,6,Math.PI*1.22,Math.PI*0.80,0,Math.PI*0.64), capeC, [-0.110,0.362,0.000]);
  csh.scale.set(1.00,0.70,0.85); csh.rotation.y = 0.22;
  // Cape body — LatheGeometry for smooth curved profile (narrow top → wide hem)
  const capeGeo = new T.LatheGeometry([
    new T.Vector2(0.010, 0.196), new T.Vector2(0.082, 0.074),
    new T.Vector2(0.166,-0.085), new T.Vector2(0.196,-0.198)
  ], 11, Math.PI*0.55, Math.PI*1.18);
  const cb = _addM(acc, capeGeo, capeC, [-0.052,0.162,0.000]);
  cb.rotation.y = -0.18; cb.rotation.x = 0.08;
  // Inner lining visible at open right edge
  const capeInGeo = new T.LatheGeometry([
    new T.Vector2(0.012, 0.192), new T.Vector2(0.080, 0.072),
    new T.Vector2(0.162,-0.083), new T.Vector2(0.192,-0.195)
  ], 11, Math.PI*0.53, Math.PI*0.26);
  const ci = _addM(acc, capeInGeo, _mClth(0x3a4a6a), [-0.052,0.162,0.000]);
  ci.rotation.y = -0.04;

  // ── RIGHT ARM — hand crossbow, relaxed pointing down ──────────────────
  const rA = new T.Group(); rA.name='bowArm'; arms.add(rA);
  rA.position.set(0.144,0.290,0.016);
  rA.rotation.z = -0.22; rA.rotation.x = -0.08;
  _addM(rA, new T.CylinderGeometry(0.030,0.036,0.18,6), navy, [0,0.090,0]);
  _addM(rA, new T.CylinderGeometry(0.026,0.030,0.15,6), sk,   [0,0.250,0]);
  _addM(rA, new T.SphereGeometry(0.030,6,5),              sk,  [0,0.340,0]);
  // Hand crossbow — compact stock + barrel along arm axis (pointing down)
  const weap = new T.Group(); weap.name='weapon'; rA.add(weap);
  _addM(weap, new T.BoxGeometry(0.036,0.148,0.050), xwod, [0,0.424,0]);              // stock
  _addM(weap, new T.BoxGeometry(0.024,0.056,0.036), xbow, [0,0.396,0]);              // receiver
  _addM(weap, new T.CylinderGeometry(0.009,0.009,0.116,6), xbow, [0,0.510,-0.020]); // barrel
  // Bow arms (perpendicular to stock — rotate CylinderGeometry 90°)
  const bwa = _addM(weap, new T.CylinderGeometry(0.007,0.007,0.118,5), xwod, [0,0.540,0]);
  bwa.rotation.z = Math.PI/2;
  const bws = _addM(weap, new T.CylinderGeometry(0.003,0.003,0.114,4), _mClth(0xd0c8a0), [0,0.540,0]);
  bws.rotation.z = Math.PI/2;  // string
  // Trigger guard (curves in YZ plane around stock)
  const tg = _addM(weap, new T.TorusGeometry(0.018,0.005,4,8,Math.PI), xbow, [0,0.376,-0.004]);
  tg.rotation.z = Math.PI/2;

  const lA = new T.Group(); lA.name='idleArm'; arms.add(lA);
  lA.position.set(-0.142,0.280,0.012);
  lA.rotation.z = 0.28; lA.rotation.x = -0.14;
  _addM(lA, new T.CylinderGeometry(0.030,0.036,0.18,6), navy, [0,0.090,0]);
  _addM(lA, new T.CylinderGeometry(0.026,0.030,0.14,6), sk,   [0,0.250,0]);
  _addM(lA, new T.SphereGeometry(0.030,6,5),              sk,  [0,0.330,0]);
  for(let i=0;i<3;i++){
    const fi = _addM(lA, new T.CylinderGeometry(0.005,0.007,0.034,4), sk, [-0.010+i*0.010,0.366,-0.010]);
    fi.rotation.x = 0.20;
  }

  // ── HEAD — 1/7 proportion, young face, slight tilt ────────────────────
  _addM(head, new T.SphereGeometry(0.082,8,7), sk, [0,0.428,0]);
  head.rotation.z = 0.08;  // slight head tilt
  // Eyes — clear, alert (dark blue irises)
  for(const sx of [-0.024,0.024]){
    _addM(head, new T.SphereGeometry(0.012,5,4), {color:new T.Color(0x1c2c58),roughness:0.60,metalness:0.00}, [sx,0.434,-0.078]);
    _addM(head, new T.SphereGeometry(0.006,4,3), {color:new T.Color(0xffffff),roughness:0.20,metalness:0.00}, [sx+0.008,0.440,-0.082]);
  }
  _addM(head, new T.SphereGeometry(0.010,5,4), _mSkin(0xc89858), [0,0.416,-0.080]); // nose
  // Light smile arc
  const smile = _addM(head, new T.TorusGeometry(0.026,0.005,4,8,Math.PI*0.55), _mSkin(0xbe9060), [0,0.401,-0.077]);
  smile.rotation.z = Math.PI; smile.rotation.x = -0.16;

  const hat = new T.Group(); hat.name='hat'; acc.add(hat);
  hat.position.set(0,0.428,0);  // at head center
  hat.rotation.z =  0.08;       // match head tilt
  hat.rotation.y = -0.10;       // rakish tilt
  _addM(hat, new T.CylinderGeometry(0.158,0.166,0.016,16), hatM, [0,0.062,0]); // brim
  _addM(hat, new T.CylinderGeometry(0.082,0.090,0.118,12), hatM, [0,0.138,0]); // crown
  _addM(hat, new T.CylinderGeometry(0.082,0.082,0.010,12), hatM, [0,0.198,0]); // top cap
  _addM(hat, new T.CylinderGeometry(0.092,0.092,0.022,12), _mLeather(0x503010), [0,0.090,0]); // leather band
  _addM(hat, new T.BoxGeometry(0.014,0.016,0.008), xbow, [-0.078,0.092,-0.046]); // band pin

  // ── TURQUOISE FEATHER — curved, arching side-back ─────────────────────
  const fBase = new T.Group(); fBase.name='feather'; hat.add(fBase);
  fBase.position.set(-0.066,0.118,0.042);
  fBase.rotation.y =  0.38; fBase.rotation.z = -0.28; fBase.rotation.x = -0.14;
  // Quill segments arching up and back
  for(let i=0;i<6;i++){
    const t = i/5;
    const qr = Math.max(0.003, 0.008 - t*0.005);
    const seg = _addM(fBase, new T.CylinderGeometry(qr, qr+0.001, 0.050, 4),
      teal, [Math.sin(t*0.70)*0.015, 0.034+i*0.048, 0]);
    seg.rotation.z = t * 0.22;
  }
  // Feather vanes — flat barb boxes either side of quill
  for(let i=1;i<5;i++){
    const t = i/4;
    for(const sx of [-1,1]){
      const vane = _addM(fBase, new T.BoxGeometry(0.030+t*0.008,0.010,0.004), teal,
        [sx*(0.022+t*0.007), 0.052+i*0.050, 0.002]);
      vane.rotation.z = sx*(0.10+t*0.06);
    }
  }
}

// ── HERO: Cleric — elderly priest, blessing pose, 1/7 proportions ──────────────
function _miniCleric(g, clr, Y){
  const T     = g3.T;
  const robeC = _mClth(0xf0ece0);
  const au    = {color:new T.Color(0xb49038),roughness:0.42,metalness:0.78};
  const lth   = _mLeather(0x6a3010);
  const sk    = _mSkin(0xd4a870);
  const hairC = _mClth(0xb8a870);
  const whtH  = _mClth(0xdcd8c8);
  const woodC = _mWood(0x8a5420);

  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.215, 0);
  torso.rotation.x = 0.06;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  _addM(legs, new T.CylinderGeometry(0.042,0.048,0.20,7), robeC, [-0.046,Y+0.100,0]);
  _addM(legs, new T.CylinderGeometry(0.042,0.048,0.20,7), robeC, [ 0.046,Y+0.100,0]);

  // Long robe skirt
  _addM(legs, new T.CylinderGeometry(0.088,0.148,0.40,10), robeC, [0,Y+0.200,0]);
  _addM(legs, new T.CylinderGeometry(0.148,0.150,0.013,10), au, [0,Y+0.007,0]); // hem border
  _addM(legs, new T.BoxGeometry(0.012,0.376,0.011), au, [-0.072,Y+0.200,-0.090]); // L stripe
  _addM(legs, new T.BoxGeometry(0.012,0.376,0.011), au, [ 0.072,Y+0.200,-0.090]); // R stripe
  _addM(legs, new T.BoxGeometry(0.018,0.348,0.011), au, [0,Y+0.200,-0.098]);      // central

  // Leather belt + buckle
  _addM(legs, new T.CylinderGeometry(0.094,0.094,0.028,10), lth, [0,Y+0.400,0]);
  _addM(legs, new T.BoxGeometry(0.032,0.024,0.010), au, [0,Y+0.400,-0.096]);

  _addM(torso, new T.CylinderGeometry(0.078,0.095,0.220,9), robeC, [0,0.110,0]);
  _addM(torso, new T.BoxGeometry(0.018,0.210,0.010), au, [0,0.110,-0.080]); // chest stripe
  _addM(torso, new T.BoxGeometry(0.010,0.072,0.013), au, [0,0.140,-0.088]); // cross vertical
  _addM(torso, new T.BoxGeometry(0.054,0.014,0.013), au, [0,0.160,-0.088]); // cross horizontal
  _addM(torso, new T.BoxGeometry(0.013,0.015,0.098), au, [-0.072,0.215,-0.008]); // L shoulder
  _addM(torso, new T.BoxGeometry(0.013,0.015,0.098), au, [ 0.072,0.215,-0.008]); // R shoulder

  const bA = new T.Group(); bA.name='blessArm'; arms.add(bA);
  bA.position.set(-0.148,0.086,0); bA.rotation.z=-0.40; bA.rotation.x=-0.48;

  _addM(bA, new T.CylinderGeometry(0.044,0.052,0.20,7), robeC, [0,0.100,0]);
  _addM(bA, new T.CylinderGeometry(0.034,0.040,0.017,7), au,    [0,0.202,0]); // gold cuff
  _addM(bA, new T.CylinderGeometry(0.025,0.031,0.10, 6), sk,    [0,0.262,0]); // forearm
  const palmB = _addM(bA, new T.SphereGeometry(0.034,7,6), sk, [0,0.328,0]);
  palmB.scale.y = 0.54;
  for(let fi=0;fi<4;fi++){
    const fx = -0.030+fi*0.020;
    _addM(bA, new T.CylinderGeometry(0.007,0.009,0.050,5), sk, [fx,0.366,-0.004]);
  }
  _addM(bA, new T.CylinderGeometry(0.008,0.010,0.038,5), sk, [-0.048,0.344,0.016]); // thumb

  const sA = new T.Group(); sA.name='staffArm'; arms.add(sA);
  sA.position.set(0.148,0.136,0); sA.rotation.z=-0.26; sA.rotation.x=-0.06;

  _addM(sA, new T.CylinderGeometry(0.044,0.052,0.20,7), robeC, [0,0.100,0]);
  _addM(sA, new T.CylinderGeometry(0.034,0.040,0.017,7), au,    [0,0.202,0]); // gold cuff
  _addM(sA, new T.CylinderGeometry(0.025,0.031,0.10, 6), sk,    [0,0.262,0]); // forearm
  _addM(sA, new T.SphereGeometry(0.032,7,6), sk, [0,0.316,0]); // gripping fist
  for(let fi=0;fi<4;fi++){
    const fx = -0.024+fi*0.016;
    _addM(sA, new T.CylinderGeometry(0.006,0.008,0.034,5), sk, [fx,0.350,-0.018]);
  }

  // Staff weapon — tall pole + ornate golden top
  const weap = new T.Group(); weap.name='weapon'; sA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.012,0.015,0.42,6), woodC, [0,0.370,0]); // pole
  _addM(weap, new T.CylinderGeometry(0.019,0.019,0.015,8), au,   [0,0.585,0]); // collar
  const tH = _addM(weap, new T.TorusGeometry(0.044,0.009,6,16), au, [0,0.614,0]);
  tH.rotation.x = Math.PI/2;   // flat horizontal ring
  const tV = _addM(weap, new T.TorusGeometry(0.044,0.009,6,16), au, [0,0.614,0]);
  tV.rotation.y = Math.PI/2;   // vertical ring perpendicular
  _addM(weap, new T.SphereGeometry(0.024,8,7), au, [0,0.614,0]); // central orb
  const spX = _addM(weap, new T.CylinderGeometry(0.005,0.005,0.082,4), au, [0,0.614,0]);
  spX.rotation.z = Math.PI/2;
  const spZ = _addM(weap, new T.CylinderGeometry(0.005,0.005,0.082,4), au, [0,0.614,0]);
  spZ.rotation.x = Math.PI/2;
  for(let i=0;i<4;i++){
    const a = (i/4)*Math.PI*2;
    _addM(weap, new T.SphereGeometry(0.008,5,5), au,
      [Math.cos(a)*0.044, 0.614, Math.sin(a)*0.044]);
  }

  _addM(head, new T.SphereGeometry(0.098,10,9), sk, [0,0.332,0]); // face
  _addM(head, new T.SphereGeometry(0.011,5,4), _mClth(0x3a2e22), [-0.029,0.344,-0.088]); // L eye
  _addM(head, new T.SphereGeometry(0.011,5,4), _mClth(0x3a2e22), [ 0.029,0.344,-0.088]); // R eye
  _addM(head, new T.SphereGeometry(0.017,6,5), sk, [0,0.324,-0.096]); // nose (aged, larger)
  _addM(head, new T.BoxGeometry(0.030,0.008,0.008), _mClth(0xb06858), [0,0.302,-0.092]);
  _addM(head, new T.BoxGeometry(0.008,0.010,0.008), _mClth(0xb06858), [-0.017,0.305,-0.091]);
  _addM(head, new T.BoxGeometry(0.008,0.010,0.008), _mClth(0xb06858), [ 0.017,0.305,-0.091]);

  // Hair — gray-blonde crown (partial sphere cap)
  const hair = _addM(head,
    new T.SphereGeometry(0.100,9,7,0,Math.PI*2,0,Math.PI*0.44), hairC, [0,0.340,0]);
  hair.rotation.x = -0.06;
  _addM(head, new T.CylinderGeometry(0.018,0.025,0.038,6), hairC, [-0.084,0.335,0.012]); // L tuft
  _addM(head, new T.CylinderGeometry(0.018,0.025,0.038,6), hairC, [ 0.084,0.335,0.012]); // R tuft

  // Long forked beard
  _addM(head, new T.CylinderGeometry(0.013,0.052,0.24,7), hairC, [0,0.202,-0.046]); // main
  _addM(head, new T.CylinderGeometry(0.008,0.017,0.082,6), hairC, [-0.022,0.112,-0.054]); // L fork
  _addM(head, new T.CylinderGeometry(0.008,0.017,0.082,6), hairC, [ 0.022,0.112,-0.054]); // R fork
  _addM(head, new T.CylinderGeometry(0.004,0.010,0.196,5), whtH, [-0.009,0.204,-0.058]); // white L
  _addM(head, new T.CylinderGeometry(0.004,0.010,0.196,5), whtH, [ 0.009,0.204,-0.058]); // white R
  _addM(head, new T.CylinderGeometry(0.009,0.013,0.042,5), hairC, [-0.022,0.308,-0.092]); // L moustache
  _addM(head, new T.CylinderGeometry(0.009,0.013,0.042,5), hairC, [ 0.022,0.308,-0.092]); // R moustache

  // Sacred halo — glowing gold behind head
  const halo = _addM(acc, new T.TorusGeometry(0.128,0.017,6,26),
    _mGlw(0xd4a828,0.85), [0,0.342,0.106]);
  halo.rotation.x = Math.PI*0.10;
}

// ── HERO: Victor, O Coice Bravo — squat armored berserker, ExtrudeGeometry axe ──
// Ref photo: short & VERY wide, crouched squat pose, heavy dark plate armor,
// enormous double-bladed war axe raised in right hand, beer mug in left,
// round spiked shield on back, massive black beard fanning from jaw to chest.
// Scale: (1.0, 0.62, 1.0) — Y compressed to ~62 % of a normal hero.
// Width comes from extra-wide geometry (torso 0.52), NOT from scale.x.
function _miniVictor(g, clr, Y){
  const T = g3.T;

  // ── Materials — worn dark plate (NO emissive on armor per spec) ─────────
  const armM  = {color:new T.Color(0x252525), roughness:0.88, metalness:0.70};
  const armHi = {color:new T.Color(0x2e2e2e), roughness:0.82, metalness:0.65};
  const goldA = {color:new T.Color(0x8a6a2a), roughness:0.60, metalness:0.75}; // aged gold
  const shldM = {color:new T.Color(0x1e1e1e), roughness:0.85, metalness:0.65}; // shield
  const blEd  = {color:new T.Color(0xc8d0d8), roughness:0.18, metalness:0.94}; // blade edge
  const rivM  = {color:new T.Color(0x6a6a60), roughness:0.55, metalness:0.80};
  const woodD  = _mWood(0x3a2010);
  const lthDk  = _mLeather(0x3a2010);
  const skinC  = _mSkin(0x8a6040);
  const skinD  = _mSkin(0x7a5035);
  // Beard strand colors — 3 tones for depth illusion
  const bdH = [
    {color:new T.Color(0x111111), roughness:0.92, metalness:0.0},
    {color:new T.Color(0x222222), roughness:0.92, metalness:0.0},
    {color:new T.Color(0x333333), roughness:0.92, metalness:0.0},
  ];

  // ── Body sub-group: scale.y=0.62 → Victor ≈60% height of Paladin ─────────
  // Width comes from wide geometry (torso 0.52), NOT from scale.x
  const bdy = new T.Group(); bdy.name = 'victor';
  bdy.scale.set(1.0, 0.62, 1.0);
  bdy.position.set(0, Y, 0);
  g.add(bdy);

  const legs  = new T.Group(); legs.name  = 'legs';  bdy.add(legs);
  const torso = new T.Group(); torso.name = 'torso';
  torso.position.set(0, 0.50, 0);
  torso.rotation.x = 0.175;   // ~10° forward — crouched attack posture
  torso.rotation.y = -0.20;   // slight turn toward axe side
  bdy.add(torso);
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head';
  head.position.set(0, 0.37, 0); head.rotation.x = 0.16; // head tilted down — menacing
  torso.add(head);
  const acc  = new T.Group(); acc.name  = 'acc'; torso.add(acc);

  // CROUCHED LEGS — wide squat stance (35° thigh tilt)

  // Boots — heavy black armored boots
  const bootM = {color:new T.Color(0x181818), roughness:0.92, metalness:0.12};
  _addM(legs, new T.CylinderGeometry(0.080, 0.096, 0.10, 8), bootM, [-0.17, 0.050,  0.04]);
  _addM(legs, new T.BoxGeometry(0.14, 0.040, 0.18),           bootM, [-0.17, 0.004,  0.05]);
  _addM(legs, new T.CylinderGeometry(0.080, 0.096, 0.10, 8), bootM, [ 0.17, 0.050, -0.04]);
  _addM(legs, new T.BoxGeometry(0.14, 0.040, 0.18),           bootM, [ 0.17, 0.004, -0.03]);

  // Greaves (shins) — angled for crouched stance
  const shL = _addM(legs, new T.CylinderGeometry(0.090, 0.102, 0.20, 8), armM, [-0.17, 0.196, 0.02]);
  shL.rotation.x = -0.26; shL.rotation.z = -0.10;
  const shR = _addM(legs, new T.CylinderGeometry(0.090, 0.102, 0.20, 8), armM, [ 0.17, 0.196,-0.02]);
  shR.rotation.x = -0.22; shR.rotation.z =  0.10;
  // Greave rivet rows (aged gold)
  for(const [sx,zz] of [[-0.17, 0.02],[0.17,-0.02]]){
    _addM(legs, new T.SphereGeometry(0.013,5,4), goldA, [sx-0.050, 0.202, zz-0.096]);
    _addM(legs, new T.SphereGeometry(0.013,5,4), goldA, [sx+0.050, 0.202, zz-0.096]);
    _addM(legs, new T.SphereGeometry(0.013,5,4), goldA, [sx-0.036, 0.124, zz-0.096]);
    _addM(legs, new T.SphereGeometry(0.013,5,4), goldA, [sx+0.036, 0.124, zz-0.096]);
  }

  // Knee guards — flattened sphere, prominent in crouched pose
  const kpL = _addM(legs, new T.SphereGeometry(0.098, 8, 7), {color:new T.Color(0x1e1e1e), roughness:0.80, metalness:0.72}, [-0.18, 0.308, -0.050]);
  kpL.scale.y = 0.52;
  const kpR = _addM(legs, new T.SphereGeometry(0.098, 8, 7), {color:new T.Color(0x1e1e1e), roughness:0.80, metalness:0.72}, [ 0.18, 0.308, -0.050]);
  kpR.scale.y = 0.52;
  // Knee rivet (gold)
  _addM(legs, new T.SphereGeometry(0.016, 5, 4), goldA, [-0.18, 0.31, -0.096]);
  _addM(legs, new T.SphereGeometry(0.016, 5, 4), goldA, [ 0.18, 0.31, -0.096]);

  // Thighs — thick, crouched 35° forward tilt, wide spread
  const thL = _addM(legs, new T.CylinderGeometry(0.110, 0.136, 0.26, 8), armM, [-0.16, 0.425, 0.05]);
  thL.rotation.x =  0.610; thL.rotation.z = -0.24;
  const thR = _addM(legs, new T.CylinderGeometry(0.110, 0.136, 0.26, 8), armM, [ 0.16, 0.425, 0.05]);
  thR.rotation.x =  0.610; thR.rotation.z =  0.24;

  // TORSO — wide short armored barrel (0.52 × 0.32 × 0.30 per spec)

  // Main body — extra wide
  _addM(torso, new T.BoxGeometry(0.52, 0.32, 0.30), armM, [0, 0.160, 0]);
  // Upper chest (shoulders wider: 1.4 × torso)
  _addM(torso, new T.BoxGeometry(0.58, 0.12, 0.28), armM, [0, 0.292, 0]);

  // Breastplate (dark plate, worn)
  _addM(torso, new T.BoxGeometry(0.50, 0.24, 0.040),
    {color:new T.Color(0x1c1c1c), roughness:0.88, metalness:0.72}, [0, 0.195, -0.163]);
  _addM(torso, new T.BoxGeometry(0.010, 0.30, 0.016), goldA, [0, 0.195, -0.170]); // center seam
  for(let ei = 0; ei < 3; ei++)
    _addM(torso, new T.BoxGeometry(0.440, 0.007, 0.020), goldA, [0, 0.10+ei*0.082, -0.172]);
  for(let ri = 0; ri < 4; ri++)
    _addM(torso, new T.SphereGeometry(0.010, 5, 4), goldA, [0, 0.092+ri*0.070, -0.174]);
  // Chain mail visible at abdomen gap
  _addM(torso, new T.BoxGeometry(0.46, 0.050, 0.016),
    {color:new T.Color(0x2a2a2a), roughness:0.96, metalness:0.55}, [0, -0.010, -0.166]);

  // Tasset skirt — 4 hanging plates front
  for(let i = 0; i < 4; i++){
    const a = ((i-1.5)/3)*1.20;
    const pl = _addM(torso, new T.BoxGeometry(0.096, 0.116, 0.022),
      {color:new T.Color(0x232323), roughness:0.85, metalness:0.70},
      [Math.sin(a)*0.178, -0.065, -Math.abs(Math.cos(a))*0.155]);
    pl.rotation.y = -a*0.70;
    _addM(torso, new T.BoxGeometry(0.090, 0.006, 0.024), goldA,
      [Math.sin(a)*0.178, 0.0, -Math.abs(Math.cos(a))*0.162]);
  }
  // Side tassets
  for(const sx of [-0.31, 0.31])
    _addM(torso, new T.BoxGeometry(0.082, 0.090, 0.022), armM, [sx, -0.038, -0.105]);

  // Belt (leather + gold buckle)
  const belt = _addM(torso, new T.CylinderGeometry(0.276, 0.276, 0.030, 16), lthDk, [0, 0.0, 0]);
  belt.rotation.x = Math.PI/2;
  _addM(torso, new T.BoxGeometry(0.046, 0.034, 0.016), goldA, [0, 0.0, -0.278]);

  // Gorget (neck guard)
  _addM(torso, new T.CylinderGeometry(0.074, 0.096, 0.056, 10), armM, [0, 0.375, 0]);

  // Pauldrons — wide (1.4× torso shoulder): placed at ±0.36
  for(const sx of [-0.36, 0.36]){
    const sp = _addM(acc, new T.SphereGeometry(0.162, 8, 8), armM, [sx, 0.300, 0]);
    sp.scale.set(1.0, 0.66, 0.80);
    for(let ri = 0; ri < 5; ri++){
      const ra = (ri/4-0.5)*1.10;
      _addM(acc, new T.SphereGeometry(0.016, 5, 4), goldA,
        [sx+Math.sin(ra)*0.135, 0.340+Math.cos(ra)*0.070, -0.080]);
    }
    _addM(acc, new T.BoxGeometry(0.118, 0.052, 0.112), armM, [sx, 0.242, 0.0]);
  }

  // ROUND SHIELD — strapped to back (+Z direction in torso-local space)
  const shGrp = new T.Group(); shGrp.name = 'shield'; acc.add(shGrp);
  shGrp.position.set(-0.06, 0.14, 0.195); // behind torso
  shGrp.rotation.x = -0.12;

  const sdsc = _addM(shGrp, new T.CylinderGeometry(0.24, 0.24, 0.035, 20), shldM, [0,0,0]);
  sdsc.rotation.x = Math.PI/2;
  _addM(shGrp, new T.TorusGeometry(0.240, 0.022, 8, 22),
    {color:new T.Color(0x282828), roughness:0.82, metalness:0.68}, [0,0,0]);
  // 10 rim spikes
  for(let si = 0; si < 10; si++){
    const sa = (si/10)*Math.PI*2;
    const sp = new T.Mesh(new T.ConeGeometry(0.018, 0.055, 6),
      new T.MeshStandardMaterial({color:0x707070, roughness:0.40, metalness:0.88}));
    sp.position.set(Math.cos(sa)*0.252, 0, Math.sin(sa)*0.252);
    sp.rotation.z = -(sa - Math.PI*0.5); sp.rotation.x = Math.PI/2;
    sp.castShadow = true; shGrp.add(sp);
  }
  // Gold cross on face
  _addM(shGrp, new T.BoxGeometry(0.012, 0.190, 0.014), goldA, [0, 0, 0.020]);
  _addM(shGrp, new T.BoxGeometry(0.190, 0.012, 0.014), goldA, [0, 0, 0.020]);
  _addM(shGrp, new T.SphereGeometry(0.036, 8, 7),
    {color:new T.Color(0x606060), roughness:0.40, metalness:0.90}, [0, 0, 0.032]);
  // Leather straps (back)
  _addM(shGrp, new T.CylinderGeometry(0.010, 0.010, 0.148, 5), lthDk, [-0.062, 0, -0.026]);
  _addM(shGrp, new T.CylinderGeometry(0.010, 0.010, 0.148, 5), lthDk, [ 0.062, 0, -0.026]);

  // WAR-AXE ARM — RIGHT (raised, axe cocked back 30°)
  const wA = new T.Group(); wA.name = 'axeArm'; arms.add(wA);
  wA.position.set(0.305, 0.228, 0);
  wA.rotation.z = -0.66; wA.rotation.y = -0.15; wA.rotation.x = -0.20;

  _addM(wA, new T.CylinderGeometry(0.072, 0.086, 0.18, 8), armM, [0, 0.090, 0]);
  _addM(wA, new T.CylinderGeometry(0.062, 0.072, 0.16, 8), armM, [0, 0.265, 0]);
  _addM(wA, new T.BoxGeometry(0.084, 0.068, 0.088),         armM, [0, 0.376, 0]);
  _addM(wA, new T.SphereGeometry(0.010, 5, 4), rivM, [0, 0.178, -0.060]);
  for(let ki = 0; ki < 4; ki++)
    _addM(wA, new T.SphereGeometry(0.011, 5, 4), rivM, [-0.030+ki*0.020, 0.392, -0.044]);

  // ── WAR AXE — ExtrudeGeometry double blade (per spec) ─────────────────────
  const axeGrp = new T.Group(); axeGrp.name = 'axe'; wA.add(axeGrp);
  axeGrp.position.set(0, 0.475, 0); axeGrp.rotation.x = 0.52;

  // Handle + grip
  _addM(axeGrp, new T.CylinderGeometry(0.025, 0.025, 0.72, 8), woodD, [0, 0.360, 0]);
  for(let bi = 0; bi < 5; bi++)
    _addM(axeGrp, new T.CylinderGeometry(0.030, 0.030, 0.013, 6), lthDk, [0, 0.182+bi*0.050, 0]);
  _addM(axeGrp, new T.SphereGeometry(0.034, 7, 6),
    {color:new T.Color(0x585858), roughness:0.60, metalness:0.80}, [0, 0.0, 0]); // pommel
  // Socket
  _addM(axeGrp, new T.BoxGeometry(0.052, 0.118, 0.048),
    {color:new T.Color(0x5a5a62), roughness:0.44, metalness:0.86}, [0, 0.692, 0]);
  _addM(axeGrp, new T.SphereGeometry(0.018, 6, 5), goldA, [0, 0.696, -0.026]);
  _addM(axeGrp, new T.ConeGeometry(0.026, 0.096, 6),
    {color:new T.Color(0x808888), roughness:0.30, metalness:0.90}, [0, 0.762, 0]);

  // LEFT blade — ExtrudeGeometry (wide crescent per spec)
  const blShL = new T.Shape();
  blShL.moveTo(0,0); blShL.lineTo(-0.28,0.18); blShL.lineTo(-0.32,0);
  blShL.lineTo(-0.22,-0.18); blShL.lineTo(0,-0.05);
  const extOpts = {depth:0.025, bevelEnabled:true, bevelSize:0.008, bevelThickness:0.008, bevelSegments:2};
  const bMeshL = new T.Mesh(new T.ExtrudeGeometry(blShL, extOpts),
    new T.MeshStandardMaterial({color:0x909090, roughness:0.25, metalness:0.90}));
  bMeshL.position.set(-0.002, 0.712, -0.010); bMeshL.castShadow = true; axeGrp.add(bMeshL);

  // RIGHT blade — mirrored shape
  const blShR = new T.Shape();
  blShR.moveTo(0,0); blShR.lineTo(0.28,0.18); blShR.lineTo(0.32,0);
  blShR.lineTo(0.22,-0.18); blShR.lineTo(0,-0.05);
  const bMeshR = new T.Mesh(new T.ExtrudeGeometry(blShR, extOpts),
    new T.MeshStandardMaterial({color:0x909090, roughness:0.25, metalness:0.90}));
  bMeshR.position.set(0.002, 0.712, -0.010); bMeshR.castShadow = true; axeGrp.add(bMeshR);

  // Bright edge highlights on both blades
  _addM(axeGrp, new T.BoxGeometry(0.348, 0.011, 0.015), blEd, [-0.162, 0.750, 0]);
  _addM(axeGrp, new T.BoxGeometry(0.348, 0.011, 0.015), blEd, [ 0.162, 0.750, 0]);

  // BEER MUG ARM — LEFT (Victor holds axe AND drinks — his signature)
  const mugA = new T.Group(); mugA.name = 'mugArm'; arms.add(mugA);
  mugA.position.set(-0.295, 0.215, 0);
  mugA.rotation.z = 0.24; mugA.rotation.x = 0.34;

  _addM(mugA, new T.CylinderGeometry(0.072, 0.086, 0.18, 8), armM, [0, 0.090, 0]);
  _addM(mugA, new T.CylinderGeometry(0.062, 0.072, 0.16, 8), armM, [0, 0.265, 0]);
  _addM(mugA, new T.BoxGeometry(0.084, 0.068, 0.088),         armM, [0, 0.376, 0]);
  for(let ki = 0; ki < 4; ki++)
    _addM(mugA, new T.SphereGeometry(0.011, 5, 4), rivM, [-0.028+ki*0.018, 0.392, -0.044]);

  const mugGrp = new T.Group(); mugGrp.name = 'mug'; mugA.add(mugGrp);
  mugGrp.position.set(0, 0.482, 0);
  const mugMat = {color:new T.Color(0x545460), roughness:0.72, metalness:0.72};
  _addM(mugGrp, new T.CylinderGeometry(0.102, 0.090, 0.22, 12), mugMat, [0, 0.110, 0]);
  _addM(mugGrp, new T.CylinderGeometry(0.108, 0.102, 0.018, 12), mugMat, [0, 0.231, 0]);
  _addM(mugGrp, new T.CylinderGeometry(0.094, 0.090, 0.020, 12), mugMat, [0, 0.001, 0]);
  const hdl = _addM(mugGrp, new T.TorusGeometry(0.080, 0.018, 5, 12, Math.PI), mugMat, [0.086, 0.110, 0]);
  hdl.rotation.z = -Math.PI/2;
  for(let wi = 0; wi < 3; wi++)
    _addM(mugGrp, new T.TorusGeometry(0.104, 0.007, 4, 14),
      {color:new T.Color(0x404048), roughness:0.80, metalness:0.72}, [0, 0.056+wi*0.070, 0]);
  const foamM = {color:new T.Color(0xf5f0e0), roughness:1.0, metalness:0.0};
  _addM(mugGrp, new T.SphereGeometry(0.098, 8, 6), foamM, [0, 0.255, 0]);
  const fp = [[1.0,0.0],[0.31,0.95],[-0.81,0.59],[-0.81,-0.59],[0.31,-0.95]];
  for(const [fx, fz] of fp)
    _addM(mugGrp, new T.SphereGeometry(0.036+Math.abs(fx)*0.010, 5, 4), foamM,
      [fx*0.050, 0.270+Math.abs(fz)*0.008, fz*0.050]);

  // HEAD — wide, heavy, square-jawed dwarven face

  // Main skull — very wide oblate sphere
  const skull = _addM(head, new T.SphereGeometry(0.142, 12, 12), skinC, [0, 0.196, 0]);
  skull.scale.set(1.10, 1.00, 0.86);
  // Thick heavy neck
  _addM(head, new T.CylinderGeometry(0.074, 0.090, 0.068, 10), skinC, [0, 0.078, 0]);
  // Prominent brow shelf
  _addM(head, new T.SphereGeometry(0.060, 9, 7), skinD, [0, 0.266, -0.112]);
  _addM(head, new T.SphereGeometry(0.040, 7, 6), skinD, [-0.058, 0.262, -0.110]);
  _addM(head, new T.SphereGeometry(0.040, 7, 6), skinD, [ 0.058, 0.262, -0.110]);
  // Square jaw / chin
  _addM(head, new T.SphereGeometry(0.082, 9, 8), skinC, [0, 0.100, -0.078]);
  // Wide meaty cheeks
  _addM(head, new T.SphereGeometry(0.052, 8, 7), skinC, [-0.092, 0.196, -0.088]);
  _addM(head, new T.SphereGeometry(0.052, 8, 7), skinC, [ 0.092, 0.196, -0.088]);

  // Deep-set eyes — white sclera with dark iris, sunken under the brow
  for(const ex of [-0.046, 0.046]){
    _addM(head, new T.SphereGeometry(0.024, 8, 7),
      {color:new T.Color(0xcec6b0), roughness:0.9, metalness:0}, [ex, 0.216, -0.122]);
    _addM(head, new T.SphereGeometry(0.018, 7, 6),
      {color:new T.Color(0x060604), roughness:0.9, metalness:0}, [ex, 0.218, -0.128]);
  }
  // Heavy scowling brows — thick, angled hard inward
  const brL = _addM(head, new T.BoxGeometry(0.072, 0.018, 0.024),
    {color:new T.Color(0x111110), roughness:0.92, metalness:0}, [-0.042, 0.244, -0.124]);
  brL.rotation.z =  0.34;
  const brR = _addM(head, new T.BoxGeometry(0.072, 0.018, 0.024),
    {color:new T.Color(0x111110), roughness:0.92, metalness:0}, [ 0.042, 0.244, -0.124]);
  brR.rotation.z = -0.34;
  // Large flat dwarf nose
  _addM(head, new T.SphereGeometry(0.026, 7, 6), skinD, [0, 0.182, -0.136]);
  _addM(head, new T.SphereGeometry(0.014, 5, 4),
    {color:new T.Color(0x4a2818), roughness:0.9, metalness:0}, [-0.018, 0.174, -0.144]);
  _addM(head, new T.SphereGeometry(0.014, 5, 4),
    {color:new T.Color(0x4a2818), roughness:0.9, metalness:0}, [ 0.018, 0.174, -0.144]);
  // Battle scar on right cheek
  const scar = _addM(head, new T.BoxGeometry(0.007, 0.058, 0.008),
    {color:new T.Color(0xaa7850), roughness:0.88, metalness:0}, [0.070, 0.194, -0.116]);
  scar.rotation.z = -0.38;

  // BEARD — THE defining feature. Solid volumetric mass, not just strands.
  // Photo: jet-black, very full, covers lower face completely, flows to chest.

  // Upper beard — wide solid mass covering jaw and cheeks fully
  _addM(head, new T.SphereGeometry(0.072, 10, 9), bdH[0], [-0.078, 0.152, -0.048]); // L cheek bulk
  _addM(head, new T.SphereGeometry(0.072, 10, 9), bdH[0], [ 0.078, 0.152, -0.048]); // R cheek bulk
  _addM(head, new T.SphereGeometry(0.090, 11, 10), bdH[0], [0, 0.108, -0.058]);      // main chin mass
  // Sides of beard wrapping around the face
  _addM(head, new T.SphereGeometry(0.056, 8, 7), bdH[1], [-0.096, 0.130, -0.028]);
  _addM(head, new T.SphereGeometry(0.056, 8, 7), bdH[1], [ 0.096, 0.130, -0.028]);

  // Mid-beard column — thick cylinder tapering down from chin
  _addM(head, new T.CylinderGeometry(0.030, 0.096, 0.26, 12), bdH[0], [0, 0.110, -0.070]);
  // Lower beard shaft — fuller body below chin
  _addM(head, new T.CylinderGeometry(0.074, 0.054, 0.18, 10), bdH[0], [0, 0.022, -0.068]);
  // Bottom beard mass
  _addM(head, new T.SphereGeometry(0.064, 9, 8), bdH[0], [0, -0.028, -0.072]);

  // Beard split prongs — characteristic dwarven forked beard
  _addM(head, new T.CylinderGeometry(0.024, 0.034, 0.130, 7), bdH[0], [-0.044, -0.072, -0.074]);
  _addM(head, new T.CylinderGeometry(0.024, 0.034, 0.130, 7), bdH[0], [ 0.044, -0.072, -0.074]);
  _addM(head, new T.CylinderGeometry(0.016, 0.024, 0.100, 6), bdH[1], [0, -0.068, -0.076]); // center

  // Decorative surface strands layered OVER the solid mass for texture
  for(let bi = 0; bi < 14; bi++){
    const rz = -0.524 + (bi/13)*1.047;   // -30° to +30°
    const strand = new T.Mesh(
      new T.CylinderGeometry(0.007, 0.012, 0.26, 4),
      new T.MeshStandardMaterial({
        color: (bi%3===0) ? 0x111111 : (bi%3===1) ? 0x1e1e1e : 0x2a2a2a,
        roughness:0.94, metalness:0.0
      })
    );
    strand.position.set(Math.sin(rz)*0.048, 0.072, -0.095);
    strand.rotation.x = -0.08 + Math.abs(rz)*0.04;
    strand.rotation.z = rz;
    strand.castShadow = true; head.add(strand);
  }

  // Thick drooping mustache — wide and heavy, as in the photo
  const mustL = _addM(head, new T.CylinderGeometry(0.016, 0.024, 0.076, 6),
    bdH[0], [-0.036, 0.154, -0.120]);
  mustL.rotation.x = 0.20; mustL.rotation.z =  0.28;
  const mustR = _addM(head, new T.CylinderGeometry(0.016, 0.024, 0.076, 6),
    bdH[0], [ 0.036, 0.154, -0.120]);
  mustR.rotation.x = 0.20; mustR.rotation.z = -0.28;
  // Mustache center join
  _addM(head, new T.SphereGeometry(0.020, 7, 6), bdH[0], [0, 0.155, -0.128]);

  // Metal beard ring — dwarven tradition
  const bRng = new T.Mesh(new T.TorusGeometry(0.042, 0.010, 6, 14),
    new T.MeshStandardMaterial({color:0x6a6a60, roughness:0.55, metalness:0.80}));
  bRng.position.set(0, -0.010, -0.094); bRng.castShadow = true; head.add(bRng);

  // WILD DARK HAIR — thick, matted, medium-length, as in the photo

  // Dense skull cap (covers top and back of head)
  const hCap = _addM(head, new T.SphereGeometry(0.150, 11, 9, 0, Math.PI*2, 0, Math.PI*0.52),
    bdH[0], [0, 0.210, 0]);
  hCap.rotation.x = 0.05;

  // Large side masses — hair is thick on the sides of the face
  const hmL = _addM(head, new T.SphereGeometry(0.082, 9, 8), bdH[0], [-0.148, 0.238, 0.020]);
  hmL.scale.set(0.72, 1.0, 0.88);
  const hmR = _addM(head, new T.SphereGeometry(0.082, 9, 8), bdH[0], [ 0.148, 0.238, 0.020]);
  hmR.scale.set(0.72, 1.0, 0.88);

  // Wild sticking-out tufts (photo shows hair that goes sideways and outward)
  const htL = _addM(head, new T.CylinderGeometry(0.030, 0.042, 0.072, 6), bdH[0],
    [-0.138, 0.258, 0.012]);
  htL.rotation.z = -0.52; htL.rotation.x = -0.18;
  const htR = _addM(head, new T.CylinderGeometry(0.030, 0.042, 0.072, 6), bdH[0],
    [ 0.138, 0.258, 0.012]);
  htR.rotation.z =  0.52; htR.rotation.x = -0.18;
  // Upper tufts going upward (wild, uncombed)
  const htu1 = _addM(head, new T.CylinderGeometry(0.022, 0.030, 0.058, 5), bdH[1],
    [-0.110, 0.310, -0.010]);
  htu1.rotation.z = -0.72; htu1.rotation.y =  0.22;
  const htu2 = _addM(head, new T.CylinderGeometry(0.022, 0.030, 0.058, 5), bdH[1],
    [ 0.110, 0.310, -0.010]);
  htu2.rotation.z =  0.72; htu2.rotation.y = -0.22;
  const htu3 = _addM(head, new T.CylinderGeometry(0.018, 0.026, 0.050, 5), bdH[0],
    [ 0.030, 0.338, -0.040]);
  htu3.rotation.z =  0.18; htu3.rotation.x = -0.30;

  // Back-of-head clumps
  _addM(head, new T.SphereGeometry(0.052, 8, 6), bdH[0], [-0.090, 0.210, 0.096]);
  _addM(head, new T.SphereGeometry(0.052, 8, 6), bdH[0], [ 0.082, 0.202, 0.100]);
  _addM(head, new T.SphereGeometry(0.038, 7, 5), bdH[1], [ 0.000, 0.196, 0.108]);
  // Back strands hanging slightly down
  _addM(head, new T.CylinderGeometry(0.018, 0.026, 0.064, 5), bdH[0],
    [-0.060, 0.168, 0.108]);
  _addM(head, new T.CylinderGeometry(0.018, 0.026, 0.064, 5), bdH[0],
    [ 0.056, 0.164, 0.110]);
}

// ── HERO: Paladin — silver knight, heraldic shield, 1/7 proportions ───────────
function _miniPaladin(g, clr, Y){
  // RICHARD, O CAVALEIRO — armadura completa prata/dourada, capa azul, espada + escudo heráldico
  // Escala 1.0 — herói mais alto e imponente do grupo
  const T = g3.T;

  // Materiais
  const silv  = {color:new T.Color(0xb8b8c0), roughness:0.20, metalness:0.90}; // prata polida
  const silvH = {color:new T.Color(0xd0d4e0), roughness:0.14, metalness:0.96}; // prata highlight
  const au    = {color:new T.Color(0xc8a951), roughness:0.28, metalness:0.82}; // ouro #c8a951
  const royal = {color:new T.Color(0x1a3a8f), roughness:0.92, metalness:0.00, side:T.DoubleSide}; // azul capa
  const royalS= {color:new T.Color(0x1a3a8f), roughness:0.70, metalness:0.04}; // azul escudo
  const blade = {color:new T.Color(0xd4dce8), roughness:0.14, metalness:0.96}; // lâmina
  const sk    = _mSkin(0xc8956a);   // pele jovem adulto
  const hairM = {color:new T.Color(0x4a2e10), roughness:0.95, metalness:0.00}; // cabelo castanho
  const lthG  = _mLeather(0x3a2010);// couro empunhadura

  // Grupos
  const legs  = new T.Group(); legs.name  = 'legs';        g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';       g.add(torso);
  torso.position.set(0, Y+0.240, 0); // postura completamente ereta
  const arms  = new T.Group(); arms.name  = 'arms';        torso.add(arms);
  const head  = new T.Group(); head.name  = 'head';        torso.add(head);
  const acc   = new T.Group(); acc.name   = 'accessories'; torso.add(acc);

  // ── PERNAS — armadura de placas completa ──────────────────────────────────
  // Pé esquerdo 0.08 à frente, peso centrado
  for(const [sx, fwdZ] of [[-0.058, -0.016],[0.058, 0.008]]){
    // Coxas
    const thigh = _addM(legs, new T.CylinderGeometry(0.058,0.068,0.26,10), silv,
                        [sx, Y+0.310, fwdZ]);
    thigh.rotation.z = sx < 0 ? 0.04 : -0.04;
    // Anel dourado superior da coxa
    _addM(legs, new T.CylinderGeometry(0.060,0.061,0.008,10), au, [sx, Y+0.434, fwdZ]);
    // Caneleiras
    _addM(legs, new T.CylinderGeometry(0.052,0.060,0.22,10), silv, [sx, Y+0.112, fwdZ]);
    // Detalhe dourado topo/base caneleira
    _addM(legs, new T.CylinderGeometry(0.061,0.062,0.007,10), au, [sx, Y+0.220, fwdZ]);
    _addM(legs, new T.CylinderGeometry(0.061,0.062,0.007,10), au, [sx, Y+0.004, fwdZ]);
    // Sabatons
    _addM(legs, new T.BoxGeometry(0.104,0.044,0.184), silv, [sx, Y+0.022, fwdZ+0.018]);
    _addM(legs, new T.BoxGeometry(0.100,0.040,0.070), silv, [sx, Y+0.050, fwdZ-0.088]); // bico
    _addM(legs, new T.BoxGeometry(0.106,0.008,0.186), au, [sx, Y+0.048, fwdZ+0.018]); // borda dourada sabaton
  }
  // Joelheiras — SphereGeometry achatada
  for(const [sx, fwdZ] of [[-0.058,-0.016],[0.058,0.008]]){
    const kn = _addM(legs, new T.SphereGeometry(0.068,10,10), silvH, [sx, Y+0.220, fwdZ-0.020]);
    kn.scale.y = 0.52;
    // Rebordo dourado joelheira
    const kRing = _addM(legs, new T.TorusGeometry(0.064,0.006,6,16), au, [sx, Y+0.220, fwdZ-0.020]);
    kRing.rotation.x = Math.PI/2;
  }

  // ── SAIA DE BATALHA — 8 placas em leque ───────────────────────────────────
  const skirtY = Y+0.194;
  for(let i=0;i<8;i++){
    const angle = (i/8)*Math.PI*2;
    const r     = 0.112;
    const px    = Math.sin(angle)*r;
    const pz    = Math.cos(angle)*r;
    const plate = _addM(legs, new T.BoxGeometry(0.088,0.155,0.020), silv, [px, skirtY, pz]);
    plate.rotation.y = -angle;
    // Borda dourada em cada placa
    const brd = _addM(legs, new T.BoxGeometry(0.088,0.008,0.022), au, [px, skirtY-0.074, pz]);
    brd.rotation.y = -angle;
    const brdT = _addM(legs, new T.BoxGeometry(0.088,0.008,0.022), au, [px, skirtY+0.074, pz]);
    brdT.rotation.y = -angle;
  }
  // Anel de encaixe da saia
  _addM(legs, new T.CylinderGeometry(0.122,0.124,0.016,16), au, [0, skirtY+0.082, 0]);

  // ── TORSO — peitoral ornamentado polido ───────────────────────────────────
  _addM(torso, new T.BoxGeometry(0.340,0.360,0.210), silv, [0, 0.170, 0]);
  // Bordas traseiras do torso
  _addM(torso, new T.BoxGeometry(0.344,0.364,0.040), silvH, [0, 0.170, 0.088]); // costas
  // Nervura vertical central do peitoral — entalhe dourado
  _addM(torso, new T.BoxGeometry(0.012,0.320,0.016), au, [0, 0.172, -0.108]); // vert
  _addM(torso, new T.BoxGeometry(0.300,0.012,0.016), au, [0, 0.060, -0.108]); // horiz baixo
  _addM(torso, new T.BoxGeometry(0.300,0.012,0.016), au, [0, 0.230, -0.108]); // horiz meio
  _addM(torso, new T.BoxGeometry(0.300,0.012,0.016), au, [0, 0.320, -0.108]); // horiz topo
  // Medalhão central em relevo
  const med = _addM(torso, new T.BoxGeometry(0.042,0.042,0.018), au, [0, 0.192, -0.112]);
  med.rotation.z = Math.PI/4;
  _addM(torso, new T.SphereGeometry(0.018,7,6), au, [0, 0.192, -0.120]); // craveja
  // Arabescos — curvas decorativas nos quadrantes do peitoral
  for(const [qx,qy] of [[-0.090,0.080],[-0.090,0.280],[0.090,0.080],[0.090,0.280]]){
    const arc = _addM(torso, new T.TorusGeometry(0.038,0.006,6,12,Math.PI*0.65), au, [qx,qy,-0.108]);
    arc.rotation.z = qx < 0 ? Math.PI*0.25 : -Math.PI*0.25;
  }
  // Gorjal (gola de armadura)
  _addM(torso, new T.CylinderGeometry(0.066,0.080,0.058,12), silv, [0, 0.370, 0]);
  _addM(torso, new T.CylinderGeometry(0.081,0.082,0.010,12), au,   [0, 0.342, 0]); // anel dourado base gorjal
  // Espaldares grandes e arredondados
  for(const sx of [-0.228, 0.228]){
    const sp = _addM(acc, new T.SphereGeometry(0.124,10,10), silvH, [sx, 0.266, -0.010]);
    sp.scale.z = 0.72;
    // 3 rebites dourados em arco no espaldar
    for(let ri=0;ri<3;ri++){
      const ra = (ri-1)*0.38;
      _addM(acc, new T.SphereGeometry(0.010,6,5), au,
            [sx + Math.sin(ra)*0.072, 0.300 + Math.cos(ra)*0.040, -0.040]);
    }
    // Placa sob espaldar
    _addM(acc, new T.CylinderGeometry(0.084,0.096,0.044,10), silv, [sx, 0.210, 0]);
  }
  // Cinto largo + fivela
  _addM(torso, new T.BoxGeometry(0.360,0.055,0.230), _mLeather(0x5c3a1e), [0, -0.010, 0]);
  _addM(torso, new T.BoxGeometry(0.048,0.046,0.022), au, [0, -0.010, -0.116]); // fivela
  _addM(torso, new T.BoxGeometry(0.024,0.022,0.026), silvH, [0,-0.010,-0.126]); // pino fivela

  // ── CAPA AZUL — 3 segmentos simulando dobras ──────────────────────────────
  const capeBase = [0, 0.040, 0.116]; // posição base da capa (atrás do torso)
  // Segmento superior preso aos ombros
  const c0 = _addM(acc, new T.BoxGeometry(0.380,0.260,0.010), royal,
                   [capeBase[0], capeBase[1]+0.048, capeBase[2]]);
  // Segmento médio
  const c1 = _addM(acc, new T.BoxGeometry(0.340,0.300,0.010), royal,
                   [capeBase[0], capeBase[1]-0.180, capeBase[2]+0.014]);
  c1.rotation.x = 0.14;
  // Segmento inferior — mais aberto
  const c2 = _addM(acc, new T.BoxGeometry(0.295,0.340,0.010), royal,
                   [capeBase[0], capeBase[1]-0.400, capeBase[2]+0.032]);
  c2.rotation.x = 0.26;
  // Bordas douradas: laterais + bainha
  _addM(acc, new T.BoxGeometry(0.009,0.860,0.012), au, [-0.188,-0.200, capeBase[2]+0.010]); // L
  _addM(acc, new T.BoxGeometry(0.009,0.860,0.012), au, [ 0.188,-0.200, capeBase[2]+0.010]); // R
  _addM(acc, new T.BoxGeometry(0.295,0.009,0.012), au, [0,-0.574, capeBase[2]+0.030]); // bainha
  // Ombreira da capa
  _addM(acc, new T.BoxGeometry(0.390,0.038,0.018), royal, [0, 0.188, capeBase[2]-0.002]);

  // ── BRAÇO ESQUERDO — escudo heráldico ─────────────────────────────────────
  const shA = new T.Group(); shA.name='shieldArm'; arms.add(shA);
  shA.position.set(-0.222, 0.088, 0);
  shA.rotation.set(-0.30, -0.08, 0.22); // escudo levantado à altura do peito

  // Braço (parte superior + antebraço)
  _addM(shA, new T.CylinderGeometry(0.050,0.060,0.190,8), silv, [0, 0.095, 0]);
  _addM(shA, new T.CylinderGeometry(0.044,0.052,0.180,8), silv, [0, -0.090, 0]);
  // Cotovelo
  const elb = _addM(shA, new T.SphereGeometry(0.052,8,7), silvH, [0, 0.002, 0]);
  elb.scale.y = 0.75;
  // Manopla
  _addM(shA, new T.BoxGeometry(0.082,0.062,0.090), silv, [0,-0.194, 0]);

  // Escudo heráldico — ExtrudeGeometry forma clássica
  const shSh = new T.Shape();
  shSh.moveTo(-0.190, 0.270);
  shSh.lineTo( 0.190, 0.270);
  shSh.lineTo( 0.190,-0.080);
  shSh.quadraticCurveTo( 0.190,-0.160, 0.000,-0.290);
  shSh.quadraticCurveTo(-0.190,-0.160,-0.190,-0.080);
  shSh.closePath();
  const shExt = new T.ExtrudeGeometry(shSh,
    {depth:0.032, bevelEnabled:true, bevelSize:0.010, bevelThickness:0.010, bevelSegments:2});
  const shMesh = new T.Mesh(shExt, new T.MeshStandardMaterial(
    {color:new T.Color(0x1a3a8f), roughness:0.70, metalness:0.04}));
  shMesh.position.set(0, 0.010, -0.130);
  shMesh.castShadow = true;
  shA.add(shMesh);
  // Borda prata do escudo
  const shRim = new T.Mesh(shExt, new T.MeshStandardMaterial(
    {color:new T.Color(0xb8b8c0), roughness:0.20, metalness:0.90, wireframe:false}));
  shRim.position.set(0, 0.010, -0.126);
  shRim.scale.setScalar(1.036);
  shA.add(shRim);
  // Cruz dourada em relevo no escudo
  _addM(shA, new T.BoxGeometry(0.028,0.340,0.018), au, [0, 0.006, -0.152]); // vert
  _addM(shA, new T.BoxGeometry(0.260,0.028,0.018), au, [0, 0.088, -0.152]); // horiz
  _addM(shA, new T.SphereGeometry(0.020,7,6), au, [0, 0.088, -0.158]); // boss central
  // Alças do escudo (atrás)
  _addM(shA, new T.CylinderGeometry(0.008,0.008,0.200,6), _mLeather(0x3a2010), [0.040, 0.060,-0.080]);
  _addM(shA, new T.CylinderGeometry(0.008,0.008,0.200,6), _mLeather(0x3a2010), [-0.040,0.060,-0.080]);

  // ── BRAÇO DIREITO — espada longa em repouso nobre ─────────────────────────
  const wA = new T.Group(); wA.name='swordArm'; arms.add(wA);
  wA.position.set(0.222, 0.088, 0);
  wA.rotation.set(0.18, -0.06, -0.22); // braço relaxado, espada apontando para baixo

  // Braço
  _addM(wA, new T.CylinderGeometry(0.050,0.060,0.190,8), silv, [0, 0.095, 0]);
  _addM(wA, new T.CylinderGeometry(0.044,0.052,0.180,8), silv, [0,-0.090, 0]);
  const elbR = _addM(wA, new T.SphereGeometry(0.052,8,7), silvH, [0, 0.002, 0]);
  elbR.scale.y = 0.75;
  // Manopla
  _addM(wA, new T.BoxGeometry(0.082,0.062,0.090), silv, [0,-0.194, 0]);

  // Espada
  const weap = new T.Group(); weap.name='weapon'; wA.add(weap);
  weap.position.set(0.020,-0.210, 0);
  weap.rotation.z = -0.52; // 30° para baixo — postura de repouso nobre

  // Pomo dourado
  _addM(weap, new T.SphereGeometry(0.030,8,7), au, [0, 0.000, 0]);
  // Cabo com couro e grip
  _addM(weap, new T.CylinderGeometry(0.016,0.018,0.140,8), lthG, [0, 0.100, 0]);
  for(let gi=0;gi<4;gi++) // 4 anéis de grip
    _addM(weap, new T.TorusGeometry(0.020,0.006,5,12), au, [0, 0.030+gi*0.034, 0]);
  // Guarda cruciforme
  _addM(weap, new T.BoxGeometry(0.210,0.020,0.022), au, [0, 0.178, 0]); // horiz
  _addM(weap, new T.BoxGeometry(0.022,0.020,0.084), au, [0, 0.178, 0]); // profundidade
  _addM(weap, new T.SphereGeometry(0.016,6,5), au, [-0.102, 0.178, 0]); // ponta L
  _addM(weap, new T.SphereGeometry(0.016,6,5), au, [ 0.102, 0.178, 0]); // ponta R
  // Lâmina longa — levemente afunilada da guarda à ponta
  const blade2 = new T.Mesh(
    new T.CylinderGeometry(0.014, 0.003, 0.680, 6),
    new T.MeshStandardMaterial(blade));
  blade2.position.set(0, 0.528, 0);
  blade2.castShadow = true;
  weap.add(blade2);
  // Fullered (canal central) na lâmina
  _addM(weap, new T.BoxGeometry(0.006,0.580,0.004), {color:new T.Color(0xe8eef8),roughness:0.12,metalness:0.96},
        [0, 0.528, -0.008]);

  // ── CABEÇA — rosto forte, sem elmo ────────────────────────────────────────
  // Crânio
  const skull = _addM(head, new T.SphereGeometry(0.106,12,12), sk, [0, 0.310, 0]);
  skull.scale.set(1.0, 1.02, 0.92); // ligeiramente oblato
  // Queixo quadrado
  const chin = _addM(head, new T.BoxGeometry(0.118,0.072,0.104), sk, [0, 0.238, -0.004]);
  chin.rotation.x = 0.06;
  // Traços faciais — nariz
  _addM(head, new T.BoxGeometry(0.024,0.038,0.028), sk, [0, 0.290,-0.098]);
  // Olhos azul escuro levemente afundados
  for(const ox of [-0.034, 0.034])
    _addM(head, new T.SphereGeometry(0.018,8,7), {color:new T.Color(0x1a3a6a),roughness:0.85,metalness:0.00},
          [ox, 0.312, -0.088]);
  // Sobrancelhas castanhas arqueadas
  for(const [bx,bRz] of [[-0.034, 0.14],[0.034,-0.14]]){
    const brow = _addM(head, new T.BoxGeometry(0.050,0.011,0.016), hairM, [bx, 0.332,-0.090]);
    brow.rotation.z = bRz;
  }
  // Boca — mandíbula firme, sorriso contido
  _addM(head, new T.BoxGeometry(0.032,0.010,0.010), _mSkin(0x9a6448), [0, 0.262,-0.098]); // lábios
  // Cabelo castanho curto — só o topo + laterais + nuca
  const hairCap = new T.Mesh(
    new T.SphereGeometry(0.108,12,12,0,Math.PI*2,0,Math.PI*0.42),
    new T.MeshStandardMaterial(hairM));
  hairCap.position.set(0, 0.316, 0.004);
  hairCap.rotation.x = 0.06;
  head.add(hairCap);
  // Volumes laterais de cabelo
  for(const hx of [-0.082, 0.082]){
    const hv = _addM(head, new T.SphereGeometry(0.048,7,6), hairM, [hx, 0.306, 0.018]);
    hv.scale.set(0.70,0.90,0.78);
  }
  // Nuca
  _addM(head, new T.BoxGeometry(0.072,0.062,0.012), hairM, [0, 0.296, 0.098]);

  // Reflexo da armadura: a dirPawn (SW) da cena cumpre o papel da antiga
  // SpotLight + PointLight por peão (removidas por desempenho).
}

function _miniGenericHero(g, clr, Y){
  const T = g3.T;
  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.24, 0);
  torso.rotation.x = -0.08;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  for(const sx of [-0.052, 0.052]){
    const l = _addM(legs, new T.CylinderGeometry(0.044,0.056,0.24,7), _mLeather(0x4a3c28), [sx,Y+0.12,0]);
    l.rotation.x = sx > 0 ? 0.10 : -0.10;
  }
  _addM(torso, new T.CylinderGeometry(0.060,0.096,0.30,9), _mClth(clr), [0,0.15,0]);
  _addM(torso, new T.CylinderGeometry(0.034,0.040,0.06,6), _mSkin(0xd4a870), [0,0.31,0]);
  // Head — 1/7 (0.076 sphere, was 0.090)
  _addM(head, new T.SphereGeometry(0.076,8,7), _mSkin(0xd4a870), [0,0.38,0]);
  // Sword arm + weapon
  const wA = new T.Group(); wA.name='swordArm'; arms.add(wA);
  wA.position.set(0.096, 0.18, 0);
  wA.rotation.z = -0.48;
  _addM(wA, new T.CylinderGeometry(0.026,0.032,0.12,6), _mSkin(0xd4a870), [0,0.06,0]);
  _addM(wA, new T.SphereGeometry(0.030,5,4), _mSkin(0xd4a870), [0,0.14,0]);
  _addM(wA, new T.BoxGeometry(0.068,0.014,0.014), _mMtl(), [0,0.18,0]);
  const weap = new T.Group(); weap.name='weapon'; wA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.008,0.008,0.22,5), _mSwd(), [0,0.28,0]);
}

// ── HERO: Bard — performatic lean, Renaissance striped coat, lute ────────────
function _miniBard(g, clr, Y){
  const T      = g3.T;
  const blackC = _mClth(0x0c0c0c);       // black — coat stripes
  const whiteC = _mClth(0xeceadc);       // warm white — coat stripes + lace
  const gold   = _mMtl(0xd4a820);        // gold — trim, embroidery
  const dkblue = _mClth(0x161a3e);       // dark blue — poofy breeches
  const lth    = _mLeather(0x6a3010);    // brown — boots
  const red    = _mClth(0xc01818);       // bright red — beret
  const auburn = { color:new T.Color(0xa03414), roughness:0.88, metalness:0.00 };
  const sk     = _mSkin(0xd4a070);
  const ltwood = _mWood(0x9a5422);       // lute body
  const dkwood = _mWood(0x3e1c0a);       // lute neck / frets
  const strM   = { color:new T.Color(0xd8d0a8), roughness:0.55, metalness:0.18 }; // lute strings

  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.200, 0);
  torso.rotation.x =  0.16;   // lean back — performatic pose
  torso.rotation.y = -0.08;   // slight turn toward audience
  const arms  = new T.Group(); arms.name  = 'arms';        torso.add(arms);
  const head  = new T.Group(); head.name  = 'head';        torso.add(head);
  const acc   = new T.Group(); acc.name   = 'accessories'; torso.add(acc);

  // Left boot (front foot, slightly forward)
  _addM(legs, new T.CylinderGeometry(0.032,0.044,0.18,8), lth, [-0.050,Y+0.092,0.024]);
  _addM(legs, new T.CylinderGeometry(0.052,0.040,0.028,8), _mLeather(0x8a4520), [-0.050,Y+0.188,0.024]); // fold-down cuff
  const btL = _addM(legs, new T.BoxGeometry(0.056,0.022,0.074), lth, [-0.050,Y+0.008,0.054]);
  btL.rotation.x = -0.10;
  // Right boot (slightly back)
  _addM(legs, new T.CylinderGeometry(0.030,0.042,0.16,8), lth, [0.056,Y+0.082,-0.016]);
  _addM(legs, new T.CylinderGeometry(0.048,0.037,0.026,8), _mLeather(0x8a4520), [0.056,Y+0.170,-0.016]);
  const btR = _addM(legs, new T.BoxGeometry(0.054,0.020,0.068), lth, [0.056,Y+0.008,-0.046]);
  btR.rotation.x = 0.10;

  // Left (front) — puffed thigh sphere
  const bpL = _addM(legs, new T.SphereGeometry(0.060,8,6), dkblue, [-0.050,Y+0.295,0.014]);
  bpL.scale.set(0.78,0.66,0.82);
  // Lower cinch (where breeches tuck into boot top)
  _addM(legs, new T.CylinderGeometry(0.032,0.038,0.075,7), dkblue, [-0.050,Y+0.236,0.016]);
  _addM(legs, new T.CylinderGeometry(0.040,0.040,0.012,8), gold, [-0.050,Y+0.200,0.022]); // gold garter band
  // Right breeches poof
  const bpR = _addM(legs, new T.SphereGeometry(0.056,8,6), dkblue, [0.056,Y+0.282,-0.010]);
  bpR.scale.set(0.76,0.64,0.80);
  _addM(legs, new T.CylinderGeometry(0.030,0.036,0.068,7), dkblue, [0.056,Y+0.228,-0.010]);
  _addM(legs, new T.CylinderGeometry(0.038,0.038,0.012,8), gold, [0.056,Y+0.194,-0.016]);

  // ── RENAISSANCE COAT — 12 alternating black/white vertical stripes ────
  for(let i=0;i<12;i++){
    const c = i%2===0 ? blackC : whiteC;
    _addM(torso, new T.CylinderGeometry(0.062,0.118,0.340,2,1,false,
      i*(Math.PI*2/12), Math.PI*2/12), c, [0,0.170,0]);
  }
  // Coat flare hem (bottom)
  for(let i=0;i<12;i++){
    const c = i%2===0 ? blackC : whiteC;
    _addM(torso, new T.CylinderGeometry(0.118,0.136,0.040,2,1,false,
      i*(Math.PI*2/12), Math.PI*2/12), c, [0,-0.022,0]);
  }
  // Gold trim — hem ring
  _addM(torso, new T.CylinderGeometry(0.119,0.137,0.012,14), gold, [0,-0.040,0]);
  // Gold trim — collar ring
  _addM(torso, new T.CylinderGeometry(0.064,0.064,0.014,12), gold, [0,0.342,0]);
  // Gold trim — front opening (two thin vertical strips)
  for(const sx of [-0.012,0.012])
    _addM(torso, new T.BoxGeometry(0.014,0.340,0.016), gold, [sx,0.170,-0.061]);
  // Gold shoulder epaulette rings
  for(const sx of [-1,1])
    _addM(torso, new T.CylinderGeometry(0.050,0.050,0.012,8), gold, [sx*0.120,0.322,0]);

  for(let i=0;i<4;i++){
    const c = i%2===0 ? blackC : whiteC;
    for(const sx of [-1,1]){
      const sp = _addM(torso, new T.SphereGeometry(0.050,5,4,
        i*(Math.PI*2/4)+Math.PI*0.12, Math.PI*2/4), c, [sx*0.118,0.348,0]);
      sp.scale.set(0.90,0.76,0.86);
    }
  }

  _addM(torso, new T.CylinderGeometry(0.078,0.062,0.020,14), whiteC, [0,0.360,0]);
  _addM(torso, new T.CylinderGeometry(0.092,0.074,0.014,14), whiteC, [0,0.348,0]);
  // Scallop points around collar edge
  for(let i=0;i<9;i++){
    const a = (i/9)*Math.PI*2;
    _addM(torso, new T.SphereGeometry(0.011,5,4), whiteC,
      [Math.cos(a)*0.090, 0.344, Math.sin(a)*0.090]);
  }

  // ── LEFT ARM — holds lute neck (reaches forward-left) ─────────────────
  const lA = new T.Group(); lA.name='luteNeckArm'; arms.add(lA);
  lA.position.set(-0.110,0.300,0.014);
  lA.rotation.z  =  0.36; lA.rotation.x = -0.52;
  _addM(lA, new T.CylinderGeometry(0.028,0.034,0.16,6), blackC, [0,0.080,0]);
  _addM(lA, new T.CylinderGeometry(0.024,0.028,0.12,6), sk,     [0,0.212,0]);
  _addM(lA, new T.SphereGeometry(0.028,6,5), sk, [0,0.296,0]);
  // Curled fingers (chord hand)
  for(let i=0;i<4;i++){
    const fi = _addM(lA, new T.CylinderGeometry(0.005,0.007,0.032,4), sk, [-0.012+i*0.008,0.330,-0.010]);
    fi.rotation.x = 0.40; fi.rotation.z = 0.10;
  }

  // ── RIGHT ARM — supports lute body (reaches forward-right) ────────────
  const rA = new T.Group(); rA.name='luteBodyArm'; arms.add(rA);
  rA.position.set(0.114,0.282,0.012);
  rA.rotation.z  = -0.28; rA.rotation.x = -0.42;
  _addM(rA, new T.CylinderGeometry(0.028,0.034,0.16,6), blackC, [0,0.080,0]);
  _addM(rA, new T.CylinderGeometry(0.024,0.028,0.14,6), sk,     [0,0.218,0]);
  _addM(rA, new T.SphereGeometry(0.028,6,5), sk, [0,0.310,0]);
  // Strumming hand fingers
  for(let i=0;i<3;i++){
    const fi = _addM(rA, new T.CylinderGeometry(0.005,0.007,0.034,4), sk, [-0.008+i*0.010,0.344,-0.010]);
    fi.rotation.x = 0.28;
  }

  const lute = new T.Group(); lute.name='lute'; acc.add(lute);
  lute.position.set(0.016,0.186,-0.122);
  lute.rotation.x = -0.58;  // tilt neck toward audience / upward
  lute.rotation.y = -0.20;  // neck angled left
  lute.rotation.z = -0.12;  // slight cant

  // Lute body — pear-shaped via LatheGeometry
  const luteProfile = [
    new T.Vector2(0.000, 0.092), new T.Vector2(0.040, 0.072),
    new T.Vector2(0.070, 0.022), new T.Vector2(0.074,-0.018),
    new T.Vector2(0.064,-0.058), new T.Vector2(0.040,-0.082),
    new T.Vector2(0.000,-0.090)
  ];
  const luteBodyGeo = new T.LatheGeometry(luteProfile, 12);
  const lb = _addM(lute, luteBodyGeo, ltwood, [0,0,0]);
  lb.scale.z = 0.54;  // flatten to give depth (lute is not fully round)
  // Soundboard front face (slightly lighter wood, layered on front)
  const luteTopGeo = new T.LatheGeometry(luteProfile, 12);
  const lt2 = _addM(lute, luteTopGeo, _mWood(0xb06030), [0,0,-0.001]);
  lt2.scale.set(0.99,0.99,0.48);
  // Sound hole
  _addM(lute, new T.CircleGeometry(0.022,10),
    {color:new T.Color(0x0a0806),roughness:1.00,metalness:0.00}, [0,0.008,-0.047]);
  // Rosette ring
  _addM(lute, new T.TorusGeometry(0.022,0.005,4,12), gold, [0,0.008,-0.044]);
  // Bridge
  _addM(lute, new T.BoxGeometry(0.068,0.012,0.010), dkwood, [0,-0.048,-0.044]);
  // Neck (fingerboard) — along +Y axis in lute-local
  _addM(lute, new T.BoxGeometry(0.028,0.185,0.016), dkwood, [0,0.175,-0.028]);
  // Frets (6 thin strips perpendicular to neck)
  for(let i=0;i<6;i++)
    _addM(lute, new T.BoxGeometry(0.030,0.005,0.018), _mMtl(0xb0a080), [0,0.100+i*0.020,-0.026]);
  // Peghead (wider)
  _addM(lute, new T.BoxGeometry(0.042,0.032,0.014), dkwood, [0,0.280,-0.024]);
  // Tuning pegs (4 pegs, 2 per side)
  for(let pi=0;pi<4;pi++){
    const side = pi<2 ? -1 : 1;
    const peg = _addM(lute, new T.CylinderGeometry(0.005,0.005,0.026,4),
      _mMtl(0xb8a060), [side*0.002, 0.268+(pi%2)*0.016, -0.022]);
    peg.rotation.z = Math.PI/2;  // peg goes horizontally
  }
  // Strings — TubeGeometry from bridge to nut (4 strings)
  for(let si=0;si<4;si++){
    const sx = -0.018 + si*0.012;
    const strCurve = new T.LineCurve3(
      new T.Vector3(sx,-0.042,-0.042),      // bridge
      new T.Vector3(sx*0.7, 0.274,-0.022)   // nut at peghead
    );
    const strGeo = new T.TubeGeometry(strCurve, 2, 0.0018, 4, false);
    const strMesh = new T.Mesh(strGeo, new T.MeshStandardMaterial(strM));
    lute.add(strMesh);
  }

  _addM(head, new T.SphereGeometry(0.082,8,7), sk, [0,0.428,0]);
  // Wide open smile
  const smile = _addM(head, new T.TorusGeometry(0.032,0.006,4,10,Math.PI*0.72), _mSkin(0xbe9050), [0,0.396,-0.076]);
  smile.rotation.z = Math.PI; smile.rotation.x = -0.14;
  // Cheek puffs (wide grin)
  for(const sx of [-0.044,0.044])
    _addM(head, new T.SphereGeometry(0.020,5,4), _mSkin(0xc89060), [sx,0.399,-0.074]);
  // Eyes — happy crinkle (slightly squinted)
  for(const sx of [-0.024,0.024]){
    _addM(head, new T.SphereGeometry(0.011,5,4), {color:new T.Color(0x182038),roughness:0.60,metalness:0}, [sx,0.436,-0.078]);
    // Raised eyebrow (performer expression)
    const eb = _addM(head, new T.BoxGeometry(0.028,0.006,0.008), auburn, [sx,0.454,-0.080]);
    eb.rotation.z = sx > 0 ? -0.25 : 0.25;
  }
  _addM(head, new T.SphereGeometry(0.010,5,4), _mSkin(0xc89058), [0,0.416,-0.080]); // nose

  const hair = new T.Group(); hair.name='hair'; head.add(hair);
  hair.position.set(0,0.428,0);
  // Crown coverage
  const hairCap = _addM(hair, new T.SphereGeometry(0.086,8,6,0,Math.PI*2,0,Math.PI*0.50), auburn, [0,0,0]);
  hairCap.scale.y = 0.82;
  // Long wavy strands — individual curved cylinders
  const strands = [
    [-0.058,-0.054, 0.016,-0.24,-0.10,0.16],  // [x,y,z,rx,rz,height]
    [-0.074,-0.108, 0.006,-0.22,-0.06,0.16],
    [-0.062,-0.178, 0.000,-0.14,-0.04,0.14],
    [-0.062,-0.238,-0.006,-0.10,-0.02,0.12],  // lower strand
    [ 0.052,-0.058, 0.014, 0.20,-0.10,0.15],
    [ 0.068,-0.112, 0.004, 0.18,-0.05,0.15],
    [ 0.060,-0.178,-0.002, 0.12,-0.02,0.13],
    [ 0.000,-0.062, 0.064,-0.06, 0.08,0.14],  // back center
    [-0.020,-0.130, 0.060,-0.10, 0.04,0.13],  // back-left
    [ 0.020,-0.122, 0.058, 0.08, 0.04,0.13],  // back-right
  ];
  for(const [hx,hy,hz,rx,rz,ht] of strands){
    const st = _addM(hair, new T.CylinderGeometry(0.010,0.007,ht,4), auburn, [hx,hy,hz]);
    st.rotation.x = rx; st.rotation.z = rz;
  }

  const beret = new T.Group(); beret.name='beret'; head.add(beret);
  beret.position.set(-0.012,0.428,0.006);
  beret.rotation.z = -0.36;   // tilt left
  beret.rotation.y =  0.08;
  // Beret flat disk base
  _addM(beret, new T.CylinderGeometry(0.094,0.082,0.025,12), red, [0,0.040,0]);
  // Dome top
  const bdome = _addM(beret, new T.SphereGeometry(0.086,10,7,0,Math.PI*2,0,Math.PI*0.52), red, [0,0.042,0]);
  bdome.scale.y = 0.58;
  // Leather band rim
  _addM(beret, new T.CylinderGeometry(0.090,0.090,0.020,12), _mLeather(0x7c1010), [0,0.028,0]);
  // Gold center button
  _addM(beret, new T.SphereGeometry(0.009,5,4), gold, [0,0.088,0]);
}

// MONSTER MINIATURES  (Warhammer / Descent painted-mini style)

// ── MONSTER: Goblin — crouching ambush, named sub-groups ─────────────────────
function _miniGoblin(g, clr, Y){
  const T  = g3.T;
  const sk = _mSkin(0x4a9228);
  const lv = _mLeather(0x4a2e10);
  const kn = _mSwd(0x9aacb8);

  const legs  = new T.Group(); legs.name  = 'legs';       g.add(legs);
  const torso = new T.Group(); torso.name = 'torso';      g.add(torso);
  torso.position.set(0, Y+0.20, 0);
  torso.rotation.x = 0.28;

  // Crouching legs — wide low stance
  const lL = _addM(legs, new T.CylinderGeometry(0.040,0.052,0.18,7), sk, [-0.070,Y+0.09,0.020]);
  lL.rotation.x =  0.30;  lL.rotation.z = -0.08;
  const lR = _addM(legs, new T.CylinderGeometry(0.040,0.052,0.18,7), sk, [ 0.075,Y+0.09,-0.010]);
  lR.rotation.x = -0.15;  lR.rotation.z =  0.10;

  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  _addM(torso, new T.CylinderGeometry(0.055,0.090,0.26,8), lv, [0,0.13,0]);
  // Head — 1/7 proportion
  _addM(head, new T.SphereGeometry(0.076,8,7), sk, [0,0.28,0]);
  // Pointy ears angled out and back
  for(const sx of [-0.108, 0.108]){
    const e = _addM(acc, new T.ConeGeometry(0.020,0.068,5), sk, [sx,0.32,0]);
    e.rotation.z = sx > 0 ? -0.62 : 0.62;
    e.rotation.x = -0.12;
  }
  // Big glowing yellow-green eyes
  for(const sx of [-0.030, 0.030])
    _addM(head, new T.SphereGeometry(0.018,5,4), _mGlw(0xccff10, 1.2), [sx,0.293,-0.082]);
  // Lower jaw / sneer
  _addM(head, new T.BoxGeometry(0.068,0.020,0.044), sk, [0,0.248,-0.068]);

  // Stabbing right arm — knife thrust forward-up
  const wA = new T.Group(); wA.name='knifeArm'; arms.add(wA);
  wA.position.set(0.092, 0.20, 0);
  wA.rotation.z = -0.55;
  wA.rotation.y = -0.22;
  _addM(wA, new T.CylinderGeometry(0.030,0.036,0.14,6), sk, [0,0.07,0]);
  _addM(wA, new T.CylinderGeometry(0.024,0.030,0.12,6), sk, [0.008,0.20,0]);
  _addM(wA, new T.SphereGeometry(0.034,6,5), sk, [0.012,0.29,0]);
  // Jagged bone-handled knife
  const weap = new T.Group(); weap.name='weapon'; wA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.009,0.009,0.17,5), kn, [0.012,0.42,0]);
  _addM(weap, new T.CylinderGeometry(0.016,0.010,0.048,5), _mClth(0xd8c898), [0.012,0.29,0]);

  // Left arm — reaching clawed
  const lA = new T.Group(); lA.name='clawArm'; arms.add(lA);
  lA.position.set(-0.090, 0.18, 0);
  lA.rotation.z =  0.44;
  lA.rotation.x = -0.20;
  _addM(lA, new T.CylinderGeometry(0.028,0.034,0.14,6), sk, [0,0.07,0]);
  _addM(lA, new T.SphereGeometry(0.032,6,5), sk, [0,0.16,0]);
  for(let i=0;i<3;i++){
    const cl = _addM(lA, new T.ConeGeometry(0.007,0.036,4), sk, [-0.018+i*0.018,0.20,-0.020]);
    cl.rotation.x = -0.30;
  }
}

// ── MONSTER: Skeleton — scythe overhead swing, spectral eyes ─────────────────
function _miniSkeleton(g, clr, Y){
  const T   = g3.T;
  const bn  = { color:new T.Color(0xd8d4c0), roughness:0.88, metalness:0.00 };
  const bnD = { color:new T.Color(0xc0bc9e), roughness:0.90, metalness:0.00 };
  const wood= _mWood(0x503820);
  const bld = _mSwd(0xa8b0bc);

  const legs = new T.Group(); legs.name = 'legs'; g.add(legs);
  // Bony legs — spread lunge stance
  const lL = _addM(legs, new T.CylinderGeometry(0.022,0.030,0.26,6), bn, [-0.052,Y+0.13,0.010]);
  lL.rotation.x =  0.18;  lL.rotation.z = -0.06;
  const lR = _addM(legs, new T.CylinderGeometry(0.022,0.030,0.26,6), bn, [ 0.055,Y+0.13,-0.010]);
  lR.rotation.x = -0.10;  lR.rotation.z =  0.08;

  // Torso group — twisted into scythe swing
  const torso = new T.Group(); torso.name = 'torso'; g.add(torso);
  torso.position.set(0, Y+0.28, 0);
  torso.rotation.y  =  0.30;
  torso.rotation.x  = -0.10;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  // Thin ribcage
  _addM(torso, new T.CylinderGeometry(0.038,0.052,0.30,7), bn, [0,0.15,0]);
  // Rib pairs
  for(let i=0;i<4;i++){
    for(const sx of [-0.048, 0.048]){
      const rib = _addM(torso, new T.CylinderGeometry(0.006,0.006,0.062,5), bnD, [sx,0.08+i*0.06,0]);
      rib.rotation.z = sx > 0 ? 0.55 : -0.55;
    }
  }
  // Tattered robe shreds
  for(let i=0;i<4;i++){
    const a = (i/4)*Math.PI*2;
    const s = _addM(acc, new T.CylinderGeometry(0.010,0.030,0.14,4),
      {color:new T.Color(0x3c2c1a),roughness:0.95,metalness:0.00},
      [Math.cos(a)*0.044,-0.06,Math.sin(a)*0.044]);
    s.rotation.z = Math.cos(a)*0.25;
  }
  // Skull — 1/7 proportion
  _addM(head, new T.SphereGeometry(0.076,8,7), bn, [0,0.37,0]);
  // Spectral blue glowing eye sockets
  for(const sx of [-0.028,0.028])
    _addM(head, new T.SphereGeometry(0.022,6,5), _mGlw(0x2040ff, 2.0), [sx,0.378,-0.076]);
  // Nose void + jaw gap
  _addM(head, new T.SphereGeometry(0.014,5,4), {color:new T.Color(0x080408),roughness:1,metalness:0}, [0,0.356,-0.082]);
  _addM(head, new T.BoxGeometry(0.058,0.014,0.038), {color:new T.Color(0x080408),roughness:1,metalness:0}, [0,0.316,-0.072]);

  // Scythe arm — swept high in swing
  const sA = new T.Group(); sA.name='scytheArm'; arms.add(sA);
  sA.position.set(-0.060, 0.22, 0);
  sA.rotation.z = -0.78;
  sA.rotation.y = -0.18;
  _addM(sA, new T.CylinderGeometry(0.018,0.022,0.14,5), bn, [0,0.07,0]);
  _addM(sA, new T.CylinderGeometry(0.014,0.018,0.12,5), bn, [0.008,0.20,0]);
  _addM(sA, new T.SphereGeometry(0.026,5,4), bn, [0.012,0.28,0]);
  // Scythe weapon group
  const weap = new T.Group(); weap.name='weapon'; sA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.010,0.010,0.52,5), wood, [0,0.50,0]);
  const sb = _addM(weap, new T.CylinderGeometry(0.007,0.040,0.20,5), bld, [-0.040,0.76,0]);
  sb.rotation.z = 1.20;

  // Left arm — grasping reaching forward
  const lA = new T.Group(); lA.name='clawArm'; arms.add(lA);
  lA.position.set(0.062, 0.22, 0);
  lA.rotation.z =  0.38;
  lA.rotation.x = -0.30;
  _addM(lA, new T.CylinderGeometry(0.018,0.022,0.14,5), bn, [0,0.07,0]);
  _addM(lA, new T.CylinderGeometry(0.014,0.018,0.12,5), bn, [0,0.20,0]);
  _addM(lA, new T.SphereGeometry(0.026,5,4), bn, [0,0.28,0]);
  for(let i=0;i<3;i++)
    _addM(lA, new T.CylinderGeometry(0.005,0.008,0.042,4), bn, [-0.012+i*0.012,0.32,0]);
}

// ── MONSTER: Orc — charging axe swing, full armor, tusks ────────────────────
function _miniOrc(g, clr, Y){
  const T   = g3.T;
  const sk  = _mSkin(0x42a832);
  const ir  = { color:new T.Color(0x787888), roughness:0.52, metalness:0.62 };
  const bn  = { color:new T.Color(0xd8c890), roughness:0.86, metalness:0.00 };
  const dark= _mWood(0x2a1e14);

  const legs = new T.Group(); legs.name = 'legs'; g.add(legs);
  // Wide-stance charging legs
  const lL = _addM(legs, new T.CylinderGeometry(0.062,0.075,0.26,8), sk, [-0.095,Y+0.13,0.010]);
  lL.rotation.x =  0.18;  lL.rotation.z = -0.08;
  const lR = _addM(legs, new T.CylinderGeometry(0.062,0.075,0.26,8), sk, [ 0.100,Y+0.13,-0.015]);
  lR.rotation.x = -0.12;  lR.rotation.z =  0.10;
  // Boot armor
  for(const sx of [-0.095, 0.100])
    _addM(legs, new T.BoxGeometry(0.074,0.038,0.090), ir, [sx,Y+0.022,0.012]);

  // Torso group — charging lean + twist into axe swing
  const torso = new T.Group(); torso.name = 'torso'; g.add(torso);
  torso.position.set(0, Y+0.28, 0);
  torso.rotation.x = -0.12;
  torso.rotation.y =  0.18;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  // Massive torso
  _addM(torso, new T.CylinderGeometry(0.108,0.162,0.44,9), sk, [0,0.22,0]);
  // Crude iron chest plate
  _addM(torso, new T.BoxGeometry(0.195,0.100,0.148), ir, [0,0.29,0.005]);
  // Rivets
  for(const pos of [[-0.060,0.31,0.080],[0.060,0.31,0.080],[0.000,0.26,0.082]])
    _addM(torso, new T.SphereGeometry(0.010,5,4), {color:new T.Color(0xaaaaaa),roughness:0.38,metalness:0.85}, pos);
  // Belt skull trophy
  _addM(torso, new T.SphereGeometry(0.030,6,5), bn, [0.060,0.04,-0.060]);
  _addM(torso, new T.BoxGeometry(0.024,0.014,0.028), bn, [0.060,0.012,-0.060]);

  // Bone shoulder armor left
  const bshl = new T.Group(); bshl.name='shoulderL'; acc.add(bshl);
  bshl.position.set(-0.165, 0.38, 0);
  _addM(bshl, new T.SphereGeometry(0.082,7,5), bn, [0,0,0]);
  _addM(bshl, new T.ConeGeometry(0.018,0.078,5), bn, [0,0.092,0]);

  // Iron shoulder plate right
  _addM(acc, new T.BoxGeometry(0.110,0.064,0.098), ir, [0.168,0.38,0]);
  _addM(acc, new T.ConeGeometry(0.014,0.056,5), {color:new T.Color(0x888898),roughness:0.48,metalness:0.66}, [0.170,0.42,-0.030]);

  // Thick neck + massive head — 1/7 proportion
  _addM(head, new T.CylinderGeometry(0.068,0.082,0.10,8), sk, [0,0.50,0]);
  _addM(head, new T.SphereGeometry(0.106,10,8), sk, [0,0.59,0]);
  // Brow ridge
  _addM(head, new T.BoxGeometry(0.195,0.034,0.066), {color:new T.Color(0x358a28),roughness:0.82,metalness:0}, [0,0.636,-0.098]);
  // Bone spike crown (5)
  for(let i=0;i<5;i++){
    const a = (i/5)*Math.PI*2-Math.PI/2;
    const sp= _addM(head, new T.ConeGeometry(0.018,0.088,5), bn, [Math.cos(a)*0.095,0.625,Math.sin(a)*0.095]);
    sp.rotation.z=-Math.cos(a)*0.34;  sp.rotation.x=-Math.sin(a)*0.34;
  }
  // Ivory tusks
  for(const sx of [-0.048, 0.048]){
    const tk = _addM(head, new T.CylinderGeometry(0.013,0.007,0.068,5), {color:new T.Color(0xece0b0),roughness:0.62,metalness:0}, [sx,0.508,-0.106]);
    tk.rotation.x = 0.35;
  }
  // Glowing red eyes
  for(const sx of [-0.038,0.038])
    _addM(head, new T.SphereGeometry(0.018,6,5), _mGlw(0xff1010, 1.6), [sx,0.598,-0.112]);

  // Axe arm — massive swing
  const axA = new T.Group(); axA.name='axeArm'; arms.add(axA);
  axA.position.set(0.175, 0.32, 0);
  axA.rotation.z = -0.48;
  axA.rotation.y = -0.15;
  _addM(axA, new T.CylinderGeometry(0.050,0.060,0.18,7), sk, [0,0.09,0]);
  _addM(axA, new T.CylinderGeometry(0.042,0.050,0.12,7), ir, [0,0.22,0]);
  _addM(axA, new T.SphereGeometry(0.040,6,5), sk, [0,0.31,0]);
  const weap = new T.Group(); weap.name='weapon'; axA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.014,0.014,0.60,6), dark, [0,0.60,0]);
  _addM(weap, new T.BoxGeometry(0.044,0.240,0.076), ir, [0,0.93,0]);
  _addM(weap, new T.BoxGeometry(0.040,0.088,0.050), ir, [0.010,1.01,0]);

  // Left arm — raised in counter-balance
  const lA2 = new T.Group(); lA2.name='shieldArm'; arms.add(lA2);
  lA2.position.set(-0.155, 0.32, 0);
  lA2.rotation.z =  0.36;
  lA2.rotation.x = -0.18;
  _addM(lA2, new T.CylinderGeometry(0.044,0.054,0.16,7), sk, [0,0.08,0]);
  _addM(lA2, new T.CylinderGeometry(0.038,0.046,0.12,7), ir, [0,0.20,0]);
  _addM(lA2, new T.SphereGeometry(0.038,6,5), sk, [0,0.29,0]);
  // Armor spikes
  for(const pos of [[-0.066,0.24,-0.080],[0.066,0.24,-0.080]])
    _addM(acc, new T.ConeGeometry(0.012,0.054,5), {color:new T.Color(0x888898),roughness:0.50,metalness:0.60}, pos);
}

// ── MONSTER: Dark Mage — billowing robes, staff raised, summoning ─────────────
function _miniDarkMage(g, clr, Y){
  const T     = g3.T;
  const night = _mClth(0x1a0828);
  const purG  = _mGlw(0x9922ee, 1.4);
  const staffM= _mWood(0x2a1a38);
  const skinM = _mSkin(0xc8a068);

  const legs = new T.Group(); legs.name = 'legs'; g.add(legs);
  // Flowing robe hem sweeping forward
  const hem = _addM(legs, new T.CylinderGeometry(0.100,0.160,0.12,9), night, [0,Y+0.06,0.020]);
  hem.rotation.x = -0.06;
  _addM(legs, new T.CylinderGeometry(0.068,0.148,0.36,9), night, [0,Y+0.24,0]);

  // Torso group — leaning back for dramatic casting pose
  const torso = new T.Group(); torso.name = 'torso'; g.add(torso);
  torso.position.set(0, Y+0.44, 0);
  torso.rotation.x =  0.14;
  torso.rotation.y = -0.12;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  _addM(torso, new T.CylinderGeometry(0.058,0.082,0.24,9), night, [0,0.12,0]);
  // Robe side folds
  for(const sx of [-0.082, 0.082]){
    const fold = _addM(torso, new T.CylinderGeometry(0.034,0.048,0.18,6), night, [sx,0.09,0.020]);
    fold.rotation.z = sx > 0 ? 0.18 : -0.18;
  }
  // Neck + head — 1/7 proportion
  _addM(head, new T.CylinderGeometry(0.036,0.042,0.08,7), skinM, [0,0.26,0]);
  _addM(head, new T.SphereGeometry(0.080,8,7), skinM, [0,0.33,0]);
  // Deep hood
  const hood = _addM(acc, new T.SphereGeometry(0.118,9,7,0,Math.PI*2,0,Math.PI*0.65), night, [0,0.33,0]);
  hood.scale.y = 0.88;
  hood.rotation.x = 0.15;
  // Glowing violet eyes
  for(const sx of [-0.026, 0.026])
    _addM(head, new T.SphereGeometry(0.018,6,5), purG, [sx,0.33,-0.086]);

  // Staff arm — raised high with swirling energy orb
  const stA = new T.Group(); stA.name='staffArm'; arms.add(stA);
  stA.position.set(-0.088, 0.14, 0);
  stA.rotation.z =  0.58;
  stA.rotation.y = -0.14;
  _addM(stA, new T.CylinderGeometry(0.032,0.042,0.16,7), night, [0,0.08,0]);
  _addM(stA, new T.CylinderGeometry(0.024,0.032,0.12,7), night, [0,0.22,0]);
  _addM(stA, new T.SphereGeometry(0.030,6,5), skinM, [0,0.30,0]);
  const weap = new T.Group(); weap.name='weapon'; stA.add(weap);
  _addM(weap, new T.CylinderGeometry(0.012,0.012,0.68,6), staffM, [0,0.64,0]);
  // Death orb on staff top
  _addM(weap, new T.SphereGeometry(0.052,7,6), _mGlw(0xbb22ff, 1.60), [0,1.00,0]);
  // Energy rings
  for(let i=0;i<3;i++){
    const ring = _addM(weap, new T.TorusGeometry(0.048+i*0.016,0.005,4,12), _mGlw(0x9922ee, 0.8+i*0.3), [0,1.00,0]);
    ring.rotation.x = i*(Math.PI/3);
    ring.rotation.y = i*(Math.PI/4);
  }

  // Casting arm — reaching forward, palm glowing
  const cA = new T.Group(); cA.name='castArm'; arms.add(cA);
  cA.position.set(0.086, 0.14, 0);
  cA.rotation.z = -0.32;
  cA.rotation.x = -0.26;
  _addM(cA, new T.CylinderGeometry(0.030,0.040,0.16,7), night, [0,0.08,0]);
  _addM(cA, new T.CylinderGeometry(0.022,0.030,0.14,7), skinM, [0,0.22,0]);
  _addM(cA, new T.SphereGeometry(0.030,6,5), skinM, [0,0.31,0]);
  _addM(cA, new T.SphereGeometry(0.022,5,4), _mGlw(0xcc44ff, 1.8), [0,0.36,0]);
}

// ── MONSTER: Troll — overhead rock smash, charging lunge ─────────────────────
function _miniTroll(g, clr, Y){
  const T    = g3.T;
  const sk   = _mSkin(0x647550);
  const skD  = { color:new T.Color(0x507040), roughness:0.90, metalness:0.00 };
  const rock = { color:new T.Color(0x787c6c), roughness:0.96, metalness:0.00 };
  const claw = { color:new T.Color(0x4a4838), roughness:0.88, metalness:0.00 };

  const legs = new T.Group(); legs.name = 'legs'; g.add(legs);
  // Massive hunched legs
  const lL = _addM(legs, new T.CylinderGeometry(0.070,0.090,0.30,8), sk, [-0.110,Y+0.15,0.020]);
  lL.rotation.x =  0.12;  lL.rotation.z = -0.10;
  const lR = _addM(legs, new T.CylinderGeometry(0.070,0.090,0.30,8), sk, [ 0.115,Y+0.15,-0.015]);
  lR.rotation.x = -0.08;  lR.rotation.z =  0.12;
  // Clawed feet
  for(const sx of [-0.110, 0.115]){
    _addM(legs, new T.BoxGeometry(0.090,0.044,0.110), sk, [sx,Y+0.022,0.015]);
    for(let i=0;i<3;i++)
      _addM(legs, new T.ConeGeometry(0.014,0.048,4), claw, [sx-0.022+i*0.022,Y+0.003,-0.066]);
  }

  // Torso group — charging forward lunge
  const torso = new T.Group(); torso.name = 'torso'; g.add(torso);
  torso.position.set(0, Y+0.32, 0);
  torso.rotation.x = -0.20;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  _addM(torso, new T.CylinderGeometry(0.126,0.172,0.48,10), sk, [0,0.24,0]);
  // Skin warts / bumps
  for(const pos of [[-0.08,0.28,-0.12],[0.10,0.18,-0.11],[0.06,0.38,-0.10],[-0.09,0.12,-0.12]])
    _addM(acc, new T.SphereGeometry(0.022,5,4), skD, pos);
  // Hunched shoulders
  for(const sx of [-0.195, 0.195]){
    const s = _addM(torso, new T.SphereGeometry(0.115,7,5), skD, [sx,0.40,0]);
    s.scale.y = 0.82;
  }
  // Minimal neck + massive head — 1/7 proportion
  _addM(head, new T.CylinderGeometry(0.080,0.096,0.08,8), sk, [0,0.55,0]);
  _addM(head, new T.SphereGeometry(0.112,10,8), sk, [0,0.63,0]);
  // Warty nose
  _addM(head, new T.SphereGeometry(0.044,6,5), skD, [0,0.620,-0.124]);
  _addM(head, new T.ConeGeometry(0.012,0.028,4), skD, [0.012,0.612,-0.148]);
  // Sunken glowing yellow eyes
  for(const sx of [-0.042,0.042])
    _addM(head, new T.SphereGeometry(0.024,6,5), _mGlw(0xddcc10, 1.3), [sx,0.648,-0.116]);
  // Lower jaw tusks
  for(const sx of [-0.038, 0.038]){
    const tk = _addM(head, new T.CylinderGeometry(0.014,0.008,0.060,5), {color:new T.Color(0xd8c890),roughness:0.80,metalness:0}, [sx,0.575,-0.118]);
    tk.rotation.x = 0.40;
  }

  // Right arm — raised HIGH overhead with giant boulder
  const rA = new T.Group(); rA.name='smashArm'; arms.add(rA);
  rA.position.set(0.200, 0.34, 0);
  rA.rotation.z = -0.82;
  rA.rotation.y = -0.12;
  _addM(rA, new T.CylinderGeometry(0.058,0.070,0.20,8), sk, [0,0.10,0]);
  _addM(rA, new T.CylinderGeometry(0.048,0.058,0.18,8), sk, [0.006,0.31,0]);
  _addM(rA, new T.SphereGeometry(0.058,7,6), sk, [0.008,0.45,0]);
  // Giant boulder — weapon group
  const weap = new T.Group(); weap.name='weapon'; rA.add(weap);
  _addM(weap, new T.SphereGeometry(0.085,7,6), rock, [0.010,0.58,0]);
  _addM(weap, new T.ConeGeometry(0.022,0.052,4), rock, [ 0.080,0.62, 0.000]);
  _addM(weap, new T.ConeGeometry(0.022,0.052,4), rock, [-0.068,0.60, 0.040]);
  _addM(weap, new T.ConeGeometry(0.022,0.052,4), rock, [-0.020,0.64,-0.062]);

  // Left arm — outstretched for balance
  const lA = new T.Group(); lA.name='balanceArm'; arms.add(lA);
  lA.position.set(-0.192, 0.34, 0);
  lA.rotation.z =  0.38;
  lA.rotation.x = -0.22;
  _addM(lA, new T.CylinderGeometry(0.054,0.066,0.20,8), sk, [0,0.10,0]);
  _addM(lA, new T.CylinderGeometry(0.044,0.054,0.18,8), sk, [0,0.30,0]);
  _addM(lA, new T.SphereGeometry(0.054,7,6), sk, [0,0.44,0]);
  for(let i=0;i<4;i++){
    const cl = _addM(lA, new T.ConeGeometry(0.010,0.048,4), claw, [-0.024+i*0.016,0.50,-0.024]);
    cl.rotation.x = -0.28;
  }
}

// ── MONSTER: Dragon — rearing up, wings spread, fire breath ──────────────────
function _miniDragon(g, clr, Y){
  const T    = g3.T;
  const sc   = _mClth(0xb03812);
  const scD  = { color:new T.Color(0x8a2808), roughness:0.92, metalness:0.00 };
  const gold = _mMtl(0xd8901a);
  const fire = _mGlw(0xff4400, 2.2);

  const legs = new T.Group(); legs.name = 'legs'; g.add(legs);
  // Powerful haunches
  for(const sx of [-0.120, 0.120]){
    const h = _addM(legs, new T.SphereGeometry(0.106,7,6), sc, [sx,Y+0.22,0]);
    h.scale.set(0.90,0.82,1.00);
  }

  const acc = new T.Group(); acc.name = 'accessories'; g.add(acc);
  // Sweeping tail
  const tl = _addM(acc, new T.CylinderGeometry(0.022,0.075,0.34,7), sc, [0.020,Y+0.09,-0.14]);
  tl.rotation.z = 0.22; tl.rotation.x = 0.52;
  const tlT= _addM(acc, new T.ConeGeometry(0.030,0.12,5), scD, [0.028,Y+0.05,-0.28]);
  tlT.rotation.x = 0.80;

  // Main torso group — rearing up
  const body = new T.Group(); body.name = 'torso'; g.add(body);
  body.position.set(0, Y+0.30, 0);
  body.rotation.x = -0.28;

  _addM(body, new T.CylinderGeometry(0.148,0.188,0.48,10), sc, [0,0.24,0]);
  // Spine ridge
  for(let i=0;i<6;i++)
    _addM(body, new T.ConeGeometry(0.014,0.048,4), scD, [0,0.08+i*0.068,-0.132]);

  // Wings — angled up and back for display roar
  for(const sx of [-1, 1]){
    const wg = new T.Group(); wg.name = sx < 0 ? 'wingL' : 'wingR'; body.add(wg);
    wg.position.set(sx*0.12, 0.30, 0);
    wg.rotation.z = sx * 0.35;
    wg.rotation.y = sx * 0.20;
    // Wing membrane (tapered flat panel)
    const wm = _addM(wg, new T.BoxGeometry(0.020,0.320,0.270), {color:new T.Color(0x8c2808),roughness:0.92,metalness:0.00}, [sx*0.18,0.16,0]);
    wm.rotation.z = sx * 0.28;
    // Wing bone ribs
    for(let r=0;r<3;r++){
      const rib = _addM(wg, new T.CylinderGeometry(0.008,0.008,0.26+r*0.028,5), gold, [sx*(0.09+r*0.058),0.08+r*0.06,0]);
      rib.rotation.z = sx*(0.58+r*0.14);
    }
  }

  // Forearms — clawed grip
  const arms = new T.Group(); arms.name = 'arms'; body.add(arms);
  for(const sx of [-1, 1]){
    const arm = new T.Group(); arm.name = sx < 0 ? 'clawArmL' : 'clawArmR'; arms.add(arm);
    arm.position.set(sx*0.165, 0.06, 0);
    arm.rotation.z = sx * 0.45;
    arm.rotation.x = -0.20;
    _addM(arm, new T.CylinderGeometry(0.044,0.058,0.20,7), sc, [0,0.10,0]);
    _addM(arm, new T.CylinderGeometry(0.036,0.044,0.18,7), sc, [0,0.30,0]);
    _addM(arm, new T.SphereGeometry(0.042,6,5), sc, [0,0.42,0]);
    for(let i=0;i<4;i++){
      const cl = _addM(arm, new T.ConeGeometry(0.012,0.055,4), scD, [-0.024+i*0.016,0.48,-0.022]);
      cl.rotation.x = -0.30;
    }
  }

  // Neck group — arching forward
  const neck = new T.Group(); neck.name = 'neck'; body.add(neck);
  neck.position.set(0, 0.52, 0);
  neck.rotation.x = -0.22;
  _addM(neck, new T.CylinderGeometry(0.082,0.126,0.22,8), sc, [0,0.11,0]);
  for(let i=0;i<4;i++)
    _addM(neck, new T.ConeGeometry(0.012,0.040,4), scD, [0,0.04+i*0.050,-0.080]);

  // Head group — angled down for attack roar — 1/7 proportion
  const head = new T.Group(); head.name = 'head'; neck.add(head);
  head.position.set(0, 0.26, 0);
  head.rotation.x = -0.18;
  _addM(head, new T.SphereGeometry(0.118,9,8), sc, [0,0,0]);
  // Elongated snout
  const sn = _addM(head, new T.CylinderGeometry(0.042,0.078,0.14,7), scD, [0,-0.032,-0.130]);
  sn.rotation.x = 1.57;
  // Nostrils
  for(const sx of [-0.018, 0.018])
    _addM(head, new T.SphereGeometry(0.012,5,4), {color:new T.Color(0x400808),roughness:0.95,metalness:0}, [sx,-0.028,-0.186]);
  // FIRE BREATH jet
  const fb = _addM(head, new T.ConeGeometry(0.028,0.24,7), fire, [0,-0.044,-0.32]);
  fb.rotation.x = 1.57;
  // Glowing orange eyes
  for(const sx of [-0.042,0.042])
    _addM(head, new T.SphereGeometry(0.025,6,5), _mGlw(0xff7700, 2.4), [sx,0.025,-0.120]);
  // Gold horns
  for(const sx of [-0.072, 0.072]){
    const h = _addM(head, new T.ConeGeometry(0.030,0.26,6), gold, [sx,0.120,0]);
    h.rotation.z = sx * -3.2;
    h.rotation.x = 0.22;
  }
  // Forehead crest spikes
  for(let i=0;i<3;i++)
    _addM(head, new T.ConeGeometry(0.014,0.062,4), scD, [0,0.060+i*0.036,-0.090-i*0.018]);
}

function _miniGenericMonster(g, clr, Y){
  const T = g3.T;
  const legs = new T.Group(); legs.name = 'legs'; g.add(legs);
  // Legs
  for(const sx of [-0.068, 0.068]){
    const l = _addM(legs, new T.CylinderGeometry(0.046,0.058,0.24,7), _mClth(clr), [sx,Y+0.12,0]);
    l.rotation.x = sx > 0 ? 0.12 : -0.08;
  }
  // Torso group — forward menacing lean
  const torso = new T.Group(); torso.name = 'torso'; g.add(torso);
  torso.position.set(0, Y+0.24, 0);
  torso.rotation.x = -0.15;
  const arms = new T.Group(); arms.name = 'arms'; torso.add(arms);
  const head = new T.Group(); head.name = 'head'; torso.add(head);
  const acc  = new T.Group(); acc.name  = 'accessories'; torso.add(acc);

  _addM(torso, new T.CylinderGeometry(0.078,0.124,0.38,8), _mClth(clr), [0,0.19,0]);
  // Head — 1/7 proportion
  _addM(head, new T.SphereGeometry(0.086,8,7), {color:clr,roughness:0.82,metalness:0}, [0,0.45,0]);
  // Glowing red eyes
  for(const sx of [-0.030,0.030])
    _addM(head, new T.SphereGeometry(0.016,5,4), _mGlw(0xff2020, 1.4), [sx,0.460,-0.086]);
  // Horns
  for(const sx of [-0.052, 0.052]){
    const h = _addM(acc, new T.ConeGeometry(0.016,0.080,5), {color:new T.Color(0x303028),roughness:0.88,metalness:0}, [sx,0.510,0]);
    h.rotation.z = sx > 0 ? -0.40 : 0.40;
  }
  // Arms raised in menace
  for(const sx of [-1, 1]){
    const arm = new T.Group(); arm.name = sx < 0 ? 'armL' : 'armR'; arms.add(arm);
    arm.position.set(sx*0.110, 0.26, 0);
    arm.rotation.z = sx * 0.42;
    arm.rotation.x = -0.22;
    _addM(arm, new T.CylinderGeometry(0.036,0.046,0.18,6), _mClth(clr), [0,0.09,0]);
    _addM(arm, new T.SphereGeometry(0.034,5,4), _mClth(clr), [0,0.21,0]);
    for(let i=0;i<3;i++){
      const cl = _addM(arm, new T.ConeGeometry(0.009,0.040,4), {color:new T.Color(0x282820),roughness:0.90,metalness:0}, [-0.014+i*0.014,0.26,-0.018]);
      cl.rotation.x = -0.28;
    }
  }
}

// 3-D CLASS SELECTION SHOWCASE
// Spec: base radiusTop 0.6 h 0.08 | DirectionalLight×2 + AmbientLight 0.35
//       hover lift 0.12 | selection → slow Y-rotation + pulse ring at base
// Completely independent from the dungeon renderer (g3).

// ── Material presets (showcase) — acabamento de MINIATURA DE PLÁSTICO PINTADA ──
// Roughness baixa-média (0.4-0.55) dá o brilho satinado de resina/plástico pintado,
// que define melhor o volume do que o acabamento fosco (0.9+) anterior.
function _cClth(T,h){ return {color:new T.Color(h??0x666666),roughness:0.52,metalness:0.02}; }
function _cGold(T)  { return {color:new T.Color(0xc8a951),  roughness:0.26,metalness:0.92}; }
function _cLth (T,h){ return {color:new T.Color(h??0x5c3a1e),roughness:0.46,metalness:0.04}; }
function _cWood(T,h){ return {color:new T.Color(h??0x6b3f1f),roughness:0.62,metalness:0.02}; }
function _cSkin(T,h){ return {color:new T.Color(h??0xd4956a),roughness:0.42,metalness:0.02}; }
function _cGlow(T,h,i){ const c=new T.Color(h); return {color:c,emissive:c,emissiveIntensity:i??1.2,roughness:0.22,metalness:0.05}; }

// ── Booster de resolução de geometria ─────────────────────────────────────────
// Envolve a construção de um peão e força contagens mínimas de segmentos em
// Cylinder/Sphere/Cone/Torus, deixando as silhuetas suaves (menos "poligonal").
// Box não é afetado (faces planas devem ficar nítidas). Restaura no finally.
function _withSmoothGeo(T, buildFn){
  const O = { C:T.CylinderGeometry, S:T.SphereGeometry, Co:T.ConeGeometry, To:T.TorusGeometry };
  T.CylinderGeometry = function(rt,rb,h,rs,hs,oe,ts,tl){
    return new O.C(rt,rb,h, Math.max(rs||8,24), Math.max(hs||1,1), oe,ts,tl); };
  T.SphereGeometry = function(r,ws,hs,ps,pl,ts,tl){
    return new O.S(r, Math.max(ws||8,28), Math.max(hs||6,20), ps,pl,ts,tl); };
  T.ConeGeometry = function(r,h,rs,hs,oe,ts,tl){
    return new O.Co(r,h, Math.max(rs||8,24), Math.max(hs||1,1), oe,ts,tl); };
  T.TorusGeometry = function(r,tu,rs,ts,arc){
    return new O.To(r,tu, Math.max(rs||6,16), Math.max(ts||8,36), arc); };
  try { buildFn(); }
  finally { T.CylinderGeometry=O.C; T.SphereGeometry=O.S; T.ConeGeometry=O.Co; T.TorusGeometry=O.To; }
}

function _cM(T,grp,geo,mp,pos){
  const mat=new T.MeshStandardMaterial({
    color:   mp.color   instanceof T.Color?mp.color  :new T.Color(mp.color  ??0x888888),
    emissive:mp.emissive instanceof T.Color?mp.emissive:new T.Color(mp.emissive??0),
    emissiveIntensity:mp.emissiveIntensity??0,
    roughness:mp.roughness??0.82, metalness:mp.metalness??0.04
  });
  const m=new T.Mesh(geo,mat);
  if(pos) m.position.set(pos[0],pos[1],pos[2]);
  m.castShadow=m.receiveShadow=true;
  grp.add(m); return m;
}

// ── Base disc — spec: radiusTop 0.6, h 0.08, stone top, gold name plate ───────
function _cBase(T,label){
  const b=new T.Group(); b.name='base';
  // Disco de madeira escura
  _cM(T,b,new T.CylinderGeometry(0.60,0.62,0.08,28),
    {color:new T.Color(0x35200f),roughness:0.82,metalness:0},[0,0.04,0]);
  // Tampo de madeira (tora) — mesma textura procedural dos peões da masmorra
  const stM=new T.Mesh(new T.CircleGeometry(0.58,28),
    new T.MeshStandardMaterial({map:_getWoodTopTex(T),roughness:0.80,metalness:0}));
  stM.rotation.x=-Math.PI/2; stM.position.set(0,0.082,0); stM.receiveShadow=true; b.add(stM);
  // Gold name plate — BoxGeometry (spec 0.4×0.08×0.02) with canvas label
  const pc=document.createElement('canvas'); pc.width=256; pc.height=44;
  const pt=pc.getContext('2d');
  pt.fillStyle='#5a3600'; pt.fillRect(0,0,256,44);
  pt.fillStyle=VC.ui.colors.gold; pt.fillRect(3,3,250,38);
  pt.strokeStyle='#e0c060'; pt.lineWidth=1; pt.strokeRect(5,5,246,34);
  pt.font='bold 16px Georgia,serif'; pt.textAlign='center'; pt.textBaseline='middle';
  pt.fillStyle='rgba(255,235,130,.50)'; pt.fillText(label.toUpperCase(),129,21);
  pt.fillStyle='#1e0e00'; pt.fillText(label.toUpperCase(),128,22);
  const pl=new T.Mesh(new T.BoxGeometry(0.40,0.08,0.02),
    new T.MeshStandardMaterial({color:0xffffff,map:new T.CanvasTexture(pc),roughness:0.3,metalness:0.5}));
  pl.position.set(0,0.04,0.50); b.add(pl);
  return b;
}

// ── Hero group factory — base + figure + pulse ring + outline shell ────────────
const _CS_IDS   = ['warrior','mage','rogue','cleric','bard','paladin'];
const _CS_NAMES = {warrior:'Victor Coice Bravo',mage:'Pedro, o Tímido',rogue:'Luccas, o Astuto',cleric:'Frade Lewis',bard:'Henrique, o Bardo',paladin:'Richard, o Cavaleiro'};
const _CS_X     = [-3.60,-2.20,-0.60,1.00,2.40,3.60]; // reduzido de ±4.25 para ±3.60

// ── PNG genérico para a tela de seleção de classe ────────────────────────────
// Substitui _cWarrior/_cMage/_cRogue/etc.: carrega assets/pawns/{classId}/frente.png
// e cria um PlaneGeometry portrait centralizado sobre a base disc.
// Mesmas dimensões e posição de _cMage (já validadas com o mago).
function _cHeroPNG(T, g, Y, classId) {
  // GLB 3D desativado a pedido: a tela de seleção usa sempre o PNG 2D (frente).
  // A câmera da seleção é fixa e frontal, então o plano já fica de frente.
  // Dimensiona pela PROPORÇÃO real (sem distorcer) — as novas imagens não são 1:2.
  const cacheKey = '_cs_' + classId;
  const mat = new T.MeshStandardMaterial({
    color:       0xffffff,
    roughness:   0.80,
    metalness:   0.00,
    side:        T.DoubleSide,
    transparent: true,
    alphaTest:   0.05,
  });
  const plane = new T.Mesh(new T.PlaneGeometry(1, 1), mat);
  plane.rotation.y = 0;
  plane.castShadow   = true;
  plane.userData.noOL = true;

  const H_ALVO = 2.30, W_MAX = 1.70;
  const ajustar = (tex) => {
    const img = tex.image;
    const ar = (img && img.width && img.height) ? img.width / img.height : 0.55;
    let w = H_ALVO * ar, h = H_ALVO;
    if (w > W_MAX) { w = W_MAX; h = W_MAX / ar; }
    plane.scale.set(w, h, 1);
    plane.position.set(0, h / 2 + 0.08, 0);   // pés na base
  };
  let tex = _pawnTexCache[cacheKey];
  if (tex) {
    mat.map = tex;
    if (tex.image && tex.image.width) ajustar(tex);
    else plane.scale.set(1.2, H_ALVO, 1), plane.position.set(0, H_ALVO / 2 + 0.08, 0);
  } else {
    plane.scale.set(1.2, H_ALVO, 1);
    plane.position.set(0, H_ALVO / 2 + 0.08, 0);
    tex = new T.TextureLoader().load(_assetURL(`assets/pawns/${classId}/frente.png`), ajustar);
    _pawnTexCache[cacheKey] = tex;
    mat.map = tex;
  }
  g.add(plane);
}

function _cHero(T,classId,idx){
  const g=new T.Group();
  g.userData.classId=classId; g.userData.slot=idx;
  g.position.set(_CS_X[idx],0,0);
  g.add(_cBase(T,_CS_NAMES[classId]??classId));
  const Y=0.08;
  try {
    _cHeroPNG(T, g, Y, classId);
  } catch(e) {
    console.error('[_cHero] Erro ao construir herói "'+classId+'":', e);
    // Fallback: cubo genérico para o slot não quebrar os outros
    const fb = new T.Mesh(
      new T.BoxGeometry(0.30,0.80,0.20),
      new T.MeshStandardMaterial({color:new T.Color(0x886644),roughness:0.8,metalness:0.1})
    );
    fb.position.set(0,0.48,0); fb.castShadow=true; g.add(fb);
  }
  // Pulse selection ring
  const pr=new T.Mesh(new T.TorusGeometry(0.68,0.030,8,36),
    new T.MeshStandardMaterial({color:new T.Color(0xffd060),emissive:new T.Color(0xffd060),
      emissiveIntensity:0,roughness:0.14,metalness:0.90}));
  pr.rotation.x=Math.PI/2; pr.position.set(0,0.006,0);
  pr.castShadow=false; pr.userData.isPulseRing=true; g.add(pr);
  // Outline shell (BackSide clone on each mesh)
  const outMat=new T.MeshBasicMaterial({color:0x040306,side:T.BackSide});
  const toOL=[]; g.traverse(c=>{
    if(!(c instanceof T.Mesh)||c.userData.isPulseRing||c.userData.noOL) return;
    toOL.push(c);
  });
  for(const c of toOL){
    const om=new T.Mesh(c.geometry,outMat);
    om.position.copy(c.position); om.rotation.copy(c.rotation);
    om.scale.copy(c.scale).multiplyScalar(1.075);
    om.castShadow=false; om.userData.noOL=true; c.parent.add(om);
  }
  return g;
}

// ══ Warrior — Dwarf Axe Fighter ════════════════════════════════════════════════
function _cWarrior(T,g,Y){
  const plat={color:new T.Color(0x2a2a2a),roughness:0.95,metalness:0.55};
  const pltS={color:new T.Color(0x404040),roughness:0.88,metalness:0.62};
  const rivM={color:new T.Color(0x555555),roughness:0.58,metalness:0.80};
  const edgM={color:new T.Color(0xc0c8d0),roughness:0.25,metalness:0.95};
  const steW={color:new T.Color(0x8898a8),roughness:0.44,metalness:0.86};
  const shld={color:new T.Color(0x454550),roughness:0.72,metalness:0.72};
  const woodD=_cWood(T,0x1a0a02);
  const sk=_cSkin(T,0xb07838);
  const hairC=_cClth(T,0x181010);
  const hairG=_cClth(T,0x585050);

  // ── Figure sub-group: Y-scale 0.65 (dwarf proportions), X-scale 1.3 (wide) ──
  const fig=new T.Group(); fig.name='figure';
  fig.position.set(0,Y,0);
  fig.scale.set(1,0.65,1);
  g.add(fig);

  const lB=new T.Group(); lB.name='lowerBody'; fig.add(lB);
  const tr=new T.Group(); tr.name='torso';     fig.add(tr);
  tr.position.set(0,0.295,0); tr.rotation.x=0.14; // lean forward aggressively
  tr.scale.x=1.30; // extra wide torso + shoulders
  const rA=new T.Group(); rA.name='rightArm'; tr.add(rA);
  const lA=new T.Group(); lA.name='leftArm';  tr.add(lA);
  const hd=new T.Group(); hd.name='head';     tr.add(hd);
  const hr=new T.Group(); hr.name='hair';     tr.add(hr);
  const bd=new T.Group(); bd.name='beard';    tr.add(bd);
  const ac=new T.Group(); ac.name='accessories'; tr.add(ac);

  // ── LEGS — short, thick, spread wide, greaves with dents ─────────────────────
  _cM(T,lB,new T.CylinderGeometry(0.118,0.145,0.215,8),plat,[-0.106,0.108,0]);
  _cM(T,lB,new T.CylinderGeometry(0.118,0.145,0.215,8),plat,[ 0.106,0.108,0]);
  // Heavy greave plates (front)
  _cM(T,lB,new T.BoxGeometry(0.176,0.095,0.198),plat,[-0.106,0.030,0.018]);
  _cM(T,lB,new T.BoxGeometry(0.176,0.095,0.198),plat,[ 0.106,0.030,-0.018]);
  // Kneepads
  _cM(T,lB,new T.SphereGeometry(0.074,7,6),pltS,[-0.106,0.192,-0.090]);
  _cM(T,lB,new T.SphereGeometry(0.074,7,6),pltS,[ 0.106,0.192,-0.090]);
  // Knee rivets (4 per knee)
  for(const sx of [-0.106,0.106]){
    for(let i=0;i<4;i++){
      const a=(i/4)*Math.PI*2;
      _cM(T,lB,new T.SphereGeometry(0.011,4,3),rivM,[sx+Math.cos(a)*0.044,0.192+Math.sin(a)*0.030,-0.118]);
    }
  }
  // Scratch/dent marks on greave surface
  _cM(T,lB,new T.BoxGeometry(0.007,0.060,0.007),pltS,[-0.132,0.074,-0.104]);
  _cM(T,lB,new T.BoxGeometry(0.006,0.044,0.006),pltS,[ 0.085,0.060,-0.108]);
  // Sabatons (armored boots)
  _cM(T,lB,new T.BoxGeometry(0.166,0.064,0.228),{color:new T.Color(0x1e1e20),roughness:0.93,metalness:0.38},[-0.106,0.010,0.018]);
  _cM(T,lB,new T.BoxGeometry(0.166,0.064,0.228),{color:new T.Color(0x1e1e20),roughness:0.93,metalness:0.38},[ 0.106,0.010,-0.018]);

  // ── TORSO — wide dark plate, multiple overlapping layers, rivets ──────────────
  // Main body — 1.3× standard width (tr.scale.x handles the multiplication)
  _cM(T,tr,new T.BoxGeometry(0.540,0.308,0.292),plat,[0,0.154,0]);
  // Belly plate (extra overlapping layer)
  _cM(T,tr,new T.BoxGeometry(0.505,0.115,0.274),pltS,[0,-0.002,-0.012]);
  // Chest face plate
  _cM(T,tr,new T.BoxGeometry(0.436,0.210,0.030),pltS,[0,0.212,-0.153]);
  // Pectoral ridges
  _cM(T,tr,new T.BoxGeometry(0.188,0.092,0.024),{color:new T.Color(0x383838),roughness:0.90,metalness:0.58},[-0.118,0.260,-0.167]);
  _cM(T,tr,new T.BoxGeometry(0.188,0.092,0.024),{color:new T.Color(0x383838),roughness:0.90,metalness:0.58},[ 0.118,0.260,-0.167]);
  // Rivet grid (3 cols × 3 rows)
  for(let col=-1;col<=1;col++) for(let row=0;row<3;row++)
    _cM(T,tr,new T.SphereGeometry(0.013,5,4),rivM,[col*0.148,0.072+row*0.112,-0.170]);
  // Waist belt
  _cM(T,tr,new T.CylinderGeometry(0.165,0.165,0.048,10),_cLth(T,0x2a1808),[0,-0.016,0]);
  // Belt studs (6)
  for(let i=0;i<6;i++){const a=(i/6)*Math.PI*2; _cM(T,tr,new T.SphereGeometry(0.010,4,3),rivM,[Math.cos(a)*0.165,-0.006,Math.sin(a)*0.165]);}

  for(const[sx,rz] of [[0.330,-0.22],[-0.330,0.22]]){
    const pau=new T.Group(); tr.add(pau);
    pau.position.set(sx,0.278,0); pau.rotation.z=rz;
    _cM(T,pau,new T.BoxGeometry(0.197,0.112,0.234),plat,[0,0,0]);
    _cM(T,pau,new T.BoxGeometry(0.205,0.028,0.242),pltS,[0,0.072,0]);
    _cM(T,pau,new T.BoxGeometry(0.205,0.028,0.242),pltS,[0,-0.072,0]);
    // Angular outer plate
    _cM(T,pau,new T.BoxGeometry(0.030,0.114,0.234),{color:new T.Color(0x222224),roughness:0.94,metalness:0.50},[sx>0?0.102:-0.102,0,0]);
    // Pauldron rivets
    for(const px of [-0.063,0,0.063]) _cM(T,pau,new T.SphereGeometry(0.012,4,3),rivM,[px,0.076,-0.070]);
  }

  // ── RIGHT ARM — war axe, raised to shoulder height, attack position ───────────
  rA.position.set(0.326,0.250,0); rA.rotation.z=-0.56; rA.rotation.x=-0.34;
  _cM(T,rA,new T.CylinderGeometry(0.055,0.068,0.268,6),plat,[0,0.134,0]);
  _cM(T,rA,new T.SphereGeometry(0.057,6,5),sk,[0,0.282,0]);
  const w=new T.Group(); w.name='weapon'; rA.add(w);
  w.position.set(0,0.282,0);
  // Long dark wood handle
  _cM(T,w,new T.CylinderGeometry(0.020,0.026,0.880,6),woodD,[0,0.440,0]);
  // Leather grip wrappings
  for(let i=0;i<5;i++){const wr=_cM(T,w,new T.TorusGeometry(0.027,0.009,5,10),_cLth(T,0x3a1c06),[0,0.168+i*0.075,0]); wr.rotation.x=Math.PI/2;}
  // Pommel
  _cM(T,w,new T.SphereGeometry(0.034,6,5),steW,[0,0.016,0]);
  // Axe head — ExtrudeGeometry double-bit wide irregular blade
  const axS=new T.Shape();
  axS.moveTo(0,0.058); axS.lineTo(-0.055,0.270); axS.lineTo(-0.105,0.248);
  axS.lineTo(-0.188,0.182); axS.lineTo(-0.225,0.072); axS.lineTo(-0.200,-0.072);
  axS.lineTo(-0.188,-0.182); axS.lineTo(-0.105,-0.248); axS.lineTo(-0.055,-0.270);
  axS.lineTo(0,-0.058); axS.lineTo(0.038,-0.196); axS.lineTo(0.055,-0.096);
  axS.lineTo(0.055,0.096); axS.lineTo(0.038,0.196); axS.lineTo(0,0.058);
  const axGrp=new T.Group(); axGrp.name='axeHead'; w.add(axGrp);
  axGrp.position.set(0,0.880,0); axGrp.rotation.x=Math.PI/2;
  _cM(T,axGrp,new T.ExtrudeGeometry(axS,{depth:0.040,bevelEnabled:true,bevelThickness:0.005,bevelSize:0.007,bevelSegments:2}),
      {color:new T.Color(0x7888a0),roughness:0.38,metalness:0.90},[0,0,-0.020]);
  // Bright sharp edge highlight
  _cM(T,axGrp,new T.BoxGeometry(0.007,0.528,0.018),edgM,[-0.218,0,0.004]);
  // Axe collar socket
  _cM(T,axGrp,new T.CylinderGeometry(0.040,0.040,0.062,8),steW,[0,0,0]);
  // Decorative groove on blade
  _cM(T,axGrp,new T.BoxGeometry(0.006,0.390,0.005),{color:new T.Color(0x505860),roughness:0.5,metalness:0.7},[-0.082,0,0.024]);

  // ── LEFT ARM — round shield with border spikes and engraved symbol ────────────
  lA.position.set(-0.326,0.250,0); lA.rotation.z=0.40; lA.rotation.x=-0.18;
  _cM(T,lA,new T.CylinderGeometry(0.055,0.068,0.242,6),plat,[0,0.121,0]);
  _cM(T,lA,new T.SphereGeometry(0.057,6,5),sk,[0,0.260,0]);
  const sh=new T.Group(); sh.name='shield'; lA.add(sh);
  sh.position.set(0,0.408,0.058);
  // Shield disc
  _cM(T,sh,new T.CylinderGeometry(0.298,0.298,0.052,20),shld,[0,0,0]);
  // Shield face
  _cM(T,sh,new T.CircleGeometry(0.296,20),{color:new T.Color(0x3e3e48),roughness:0.74,metalness:0.66},[0,0.027,0]);
  // Rim
  const sRim=_cM(T,sh,new T.TorusGeometry(0.298,0.036,7,24),steW,[0,0,0]); sRim.rotation.x=Math.PI/2;
  // Center boss
  _cM(T,sh,new T.SphereGeometry(0.076,8,7),steW,[0,0.040,0]);
  // Symbol — hexagonal gold inlay
  _cM(T,sh,new T.CylinderGeometry(0.032,0.032,0.008,6),{color:new T.Color(0xc89820),roughness:0.26,metalness:0.94},[0,0.032,0]);
  // Border spikes (8 cones)
  for(let i=0;i<8;i++){const a=(i/8)*Math.PI*2, sp=_cM(T,sh,new T.ConeGeometry(0.019,0.090,4),steW,[Math.cos(a)*0.332,0.012,Math.sin(a)*0.332]); sp.rotation.z=-Math.PI/2; sp.rotation.y=-a;}
  // Rivets ring (6)
  for(let i=0;i<6;i++){const a=(i/6)*Math.PI*2; _cM(T,sh,new T.SphereGeometry(0.011,4,3),rivM,[Math.cos(a)*0.210,0.030,Math.sin(a)*0.210]);}

  _cM(T,hd,new T.SphereGeometry(0.164,10,9),sk,[0,0.568,0]);
  _cM(T,hd,new T.BoxGeometry(0.308,0.195,0.262),sk,[0,0.480,0]);
  _cM(T,hd,new T.BoxGeometry(0.272,0.070,0.224),sk,[0,0.362,0]); // wide chin
  // Angry furrowed brow ridge
  _cM(T,hd,new T.BoxGeometry(0.272,0.040,0.068),{color:new T.Color(0xa87028),roughness:0.90,metalness:0},[0,0.596,-0.144]);
  // Deep-set eyes
  for(const ex of [-0.082,0.082]){
    _cM(T,hd,new T.SphereGeometry(0.025,6,5),{color:new T.Color(0x180600),roughness:0.5,metalness:0},[ex,0.568,-0.152]);
    _cM(T,hd,new T.SphereGeometry(0.014,5,4),{color:new T.Color(0x601808),roughness:0.4,metalness:0.1},[ex,0.568,-0.164]);
  }
  // Angry V-brows
  const brL2=_cM(T,hd,new T.BoxGeometry(0.096,0.026,0.020),hairC,[-0.076,0.600,-0.158]); brL2.rotation.z=0.44;
  const brR2=_cM(T,hd,new T.BoxGeometry(0.096,0.026,0.020),hairC,[ 0.076,0.600,-0.158]); brR2.rotation.z=-0.44;
  // Broad flat nose
  _cM(T,hd,new T.SphereGeometry(0.036,7,6),sk,[0,0.516,-0.165]);
  _cM(T,hd,new T.BoxGeometry(0.078,0.028,0.022),sk,[0,0.506,-0.172]);
  // Grimace mouth
  _cM(T,hd,new T.BoxGeometry(0.090,0.016,0.016),{color:new T.Color(0x8a4022),roughness:0.90,metalness:0},[0,0.462,-0.160]);
  // Scar — thin raised ridge on left cheek
  const sc=_cM(T,hd,new T.BoxGeometry(0.011,0.078,0.008),{color:new T.Color(0xc09060),roughness:0.90,metalness:0},[-0.130,0.516,-0.150]); sc.rotation.z=0.34;
  // Cheekbone volume
  _cM(T,hd,new T.SphereGeometry(0.036,5,4),{color:new T.Color(0xb88042),roughness:0.93,metalness:0},[-0.126,0.544,-0.134]);
  _cM(T,hd,new T.SphereGeometry(0.036,5,4),{color:new T.Color(0xb88042),roughness:0.93,metalness:0},[ 0.126,0.544,-0.134]);

  // Hair cap (upper hemisphere)
  _cM(T,hr,new T.SphereGeometry(0.168,8,6,0,Math.PI*2,0,Math.PI*0.54),hairC,[0,0.566,0]);
  // Wild dishevelled tufts
  for(const[px,py,pz,r] of [[-0.158,0.642,-0.030,0.050],[0.158,0.642,-0.030,0.050],
      [0,0.660,-0.032,0.046],[-0.112,0.630,0.074,0.042],[0.112,0.630,0.074,0.042],[-0.060,0.646,0.090,0.036]])
    _cM(T,hr,new T.SphereGeometry(r,6,5),hairC,[px,py,pz]);
  // Grey streaks
  _cM(T,hr,new T.SphereGeometry(0.028,5,4),hairG,[-0.138,0.650,-0.040]);
  _cM(T,hr,new T.SphereGeometry(0.022,4,3),hairG,[ 0.120,0.636,0.060]);
  _cM(T,hr,new T.SphereGeometry(0.018,4,3),hairG,[0,0.656,-0.038]);

  // ── BEARD — thick, long, irregular curls — TubeGeometry strands ──────────────
  // Beard origin: chin at roughly (0, 0.362, −0.14) in tr-local space.
  // Strands descend to chest (~y 0.00) then curl at tips.
  const mkT=(pts,r)=>{try{const crv=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));return new T.TubeGeometry(crv,12,r,5,false);}catch(e){return null;}};
  const bDefs=[
    // central main strand
    [[[0,0.356,-0.150],[0.008,0.272,-0.170],[0.004,0.168,-0.172],[-0.006,0.076,-0.162],[-0.002,-0.010,-0.148]],0.038],
    // left primary
    [[[-0.072,0.354,-0.146],[-0.096,0.262,-0.164],[-0.084,0.164,-0.168],[-0.066,0.074,-0.158],[-0.044,-0.002,-0.144]],0.030],
    // right primary
    [[[0.072,0.354,-0.146],[0.094,0.264,-0.164],[0.082,0.166,-0.168],[0.062,0.076,-0.158],[0.040,-0.002,-0.144]],0.030],
    // left outer curl
    [[[-0.126,0.342,-0.135],[-0.162,0.250,-0.152],[-0.152,0.158,-0.157],[-0.120,0.076,-0.152],[-0.086,0.006,-0.135]],0.022],
    // right outer curl
    [[[0.126,0.342,-0.135],[0.160,0.252,-0.152],[0.150,0.160,-0.157],[0.116,0.078,-0.152],[0.082,0.008,-0.135]],0.022],
    // tip curl left (inward hook)
    [[[-0.052,0.004,-0.146],[-0.074,-0.042,-0.150],[-0.080,-0.072,-0.132],[-0.054,-0.094,-0.108]],0.018],
    // tip curl right
    [[[0.052,0.004,-0.146],[0.072,-0.042,-0.150],[0.076,-0.072,-0.132],[0.050,-0.094,-0.108]],0.018],
    // centre tip curl
    [[[0,-0.006,-0.150],[0.008,-0.050,-0.156],[0.002,-0.080,-0.138],[-0.006,-0.098,-0.114]],0.016],
  ];
  for(const[pts,r] of bDefs){const geo=mkT(pts,r); if(geo) _cM(T,bd,geo,hairC,[0,0,0]);}
  // Grey beard streak
  const bgG=mkT([[0,0.346,-0.154],[-0.006,0.258,-0.172],[0.004,0.170,-0.170],[-0.002,0.080,-0.160]],0.010);
  if(bgG) _cM(T,bd,bgG,hairG,[0,0,0]);
}

// ══ Mage — Dark Mage (Mago Negro) ══════════════════════════════════════════════
function _cMage(T,g,Y){
  // ── Substituído por PNG transparente (assets/pawns/mage/frente.png) ───────────
  // Câmera da seleção: position(lookX, 4.2, 9.0) → lookAt(lookX, 0.7, 0).
  // Camera vem do lado +Z; PlaneGeometry normal padrão = +Z → rotation.y = 0
  // aponta exatamente para a câmera sem precisar girar.
  // DoubleSide: visível de ambos os lados caso a câmera orbite levemente.
  const W = 1.10;    // largura
  const H = 2.20;    // altura portrait 1:2

  const CACHE_KEY = '_cs_mage';
  if (!_pawnTexCache[CACHE_KEY]) {
    _pawnTexCache[CACHE_KEY] = new T.TextureLoader().load('assets/pawns/mage/frente.png');
  }

  const mat = new T.MeshStandardMaterial({
    map:         _pawnTexCache[CACHE_KEY],
    color:       0xffffff,
    roughness:   0.80,
    metalness:   0.00,
    side:        T.DoubleSide,
    transparent: true,
    alphaTest:   0.05,
  });
  const plane = new T.Mesh(new T.PlaneGeometry(W, H), mat);
  plane.rotation.y = 0;
  plane.position.set(0, H / 2 + 0.08, 0);
  plane.castShadow   = true;
  plane.userData.noOL = true;
  g.add(plane);

  // ── CORPO ORIGINAL DA _cMage (mantido comentado para referência futura) ──────
  // Remova o bloco abaixo e descomente se quiser voltar à geometria 3D.
  /*
  const rob =_cClth(T,0x1a0a2e);  // black-purple robe
  const robH=_cClth(T,0x2a0a44);  // robe fold highlight
  const lth ={color:new T.Color(0x111010),roughness:0.88,metalness:0.06}; // dark leather
  const lthL={color:new T.Color(0x1c1818),roughness:0.82,metalness:0.08};
  const sv  ={color:new T.Color(0xa8b8c0),roughness:0.30,metalness:0.84}; // silver rivets
  const bon ={color:new T.Color(0xbcb090),roughness:0.82,metalness:0.04}; // bone/skull
  const eyeM={color:new T.Color(0x040408),roughness:0.80,metalness:0};    // dark eye sockets
  const sk  =_cSkin(T,0xc8b8a8);  // pale skin
  const hC  =_cClth(T,0x060406);  // near-black hair
  const wdD =_cWood(T,0x0a0606);  // very dark wood staff

  const lB=new T.Group(); lB.name='lowerBody'; g.add(lB);
  const tr=new T.Group(); tr.name='torso';     g.add(tr);
  tr.position.set(0,Y+0.240,0); tr.rotation.x=0.10; tr.rotation.z=-0.028;
  const rA=new T.Group(); rA.name='rightArm'; tr.add(rA);
  const lA=new T.Group(); lA.name='leftArm';  tr.add(lA);
  const hd=new T.Group(); hd.name='head';     tr.add(hd);
  const hr=new T.Group(); hr.name='hair';     tr.add(hr);
  const ac=new T.Group(); ac.name='accessories'; tr.add(ac);

  // ── ROBE LOWER — long, asymmetric (left side opens → boot revealed) ──────────
  // Full robe cone to floor
  _cM(T,lB,new T.CylinderGeometry(0.148,0.302,0.730,10),rob,[0,Y+0.365,0]);
  // Left-side opening crease (vertical strip, slightly lighter)
  const hO=_cM(T,lB,new T.BoxGeometry(0.055,0.630,0.016),robH,[-0.228,Y+0.365,-0.086]); hO.rotation.y=0.28;
  // Right-side drape fold
  const dR=_cM(T,lB,new T.BoxGeometry(0.072,0.660,0.014),robH,[ 0.202,Y+0.360,-0.090]); dR.rotation.y=-0.20;
  // Left boot — partially revealed through robe opening
  _cM(T,lB,new T.CylinderGeometry(0.058,0.074,0.334,8),lth,[-0.094,Y+0.186,0.022]);
  _cM(T,lB,new T.BoxGeometry(0.116,0.050,0.202),lth,[-0.094,Y+0.014,0.042]); // sole
  _cM(T,lB,new T.BoxGeometry(0.028,0.020,0.007),sv,[-0.094,Y+0.272,-0.068]); // buckle

  // ── TORSO — robe upper + leather breastplate + wide sleeves ──────────────────
  _cM(T,tr,new T.CylinderGeometry(0.108,0.168,0.500,8),rob,[0,0.250,0]);
  // Leather breastplate (dark, light-leather over robe)
  _cM(T,tr,new T.BoxGeometry(0.220,0.268,0.030),lth,[0,0.248,-0.128]);
  // Trim borders (silver frame)
  _cM(T,tr,new T.BoxGeometry(0.226,0.007,0.016),sv,[0,0.384,-0.132]);
  _cM(T,tr,new T.BoxGeometry(0.226,0.007,0.016),sv,[0,0.114,-0.132]);
  _cM(T,tr,new T.BoxGeometry(0.007,0.274,0.016),sv,[-0.114,0.249,-0.132]);
  _cM(T,tr,new T.BoxGeometry(0.007,0.274,0.016),sv,[ 0.114,0.249,-0.132]);
  // Rivets on breastplate (2 × 3)
  for(const[px,py] of [[-0.066,0.356],[0.066,0.356],[-0.066,0.249],[0.066,0.249],[-0.066,0.144],[0.066,0.144]])
    _cM(T,tr,new T.SphereGeometry(0.010,5,4),sv,[px,py,-0.144]);
  // Central engraved divider
  _cM(T,tr,new T.BoxGeometry(0.007,0.248,0.006),{color:new T.Color(0x280840),roughness:0.9,metalness:0},[0,0.249,-0.145]);
  // Wide sleeve right (drooping, fabric-heavy)
  _cM(T,tr,new T.CylinderGeometry(0.058,0.112,0.230,7),rob,[0.175,0.358,0]);
  // Wide sleeve left (tighter — arm raised)
  _cM(T,tr,new T.CylinderGeometry(0.050,0.094,0.200,7),rob,[-0.158,0.334,0]);

  _cM(T,tr,new T.CylinderGeometry(0.144,0.144,0.036,10),lthL,[0,-0.010,0]);
  // Belt buckle area
  _cM(T,tr,new T.BoxGeometry(0.044,0.032,0.008),sv,[0,-0.010,-0.148]);
  // Skull sphere body
  const skG=new T.Group(); skG.name='skullBelt'; tr.add(skG);
  skG.position.set(0,-0.012,-0.154);
  _cM(T,skG,new T.SphereGeometry(0.044,8,7),bon,[0,0,0]);
  // Skull eye sockets
  _cM(T,skG,new T.SphereGeometry(0.013,5,4),eyeM,[-0.019, 0.007,-0.034]);
  _cM(T,skG,new T.SphereGeometry(0.013,5,4),eyeM,[ 0.019, 0.007,-0.034]);
  // Nasal cavity
  _cM(T,skG,new T.CylinderGeometry(0.005,0.005,0.007,5),eyeM,[0,-0.007,-0.038]);
  // Teeth — 4 thin CylinderGeometry
  for(let i=0;i<4;i++) _cM(T,skG,new T.CylinderGeometry(0.004,0.003,0.018,4),bon,[-0.020+i*0.014,-0.032,-0.034]);

  // Cowl ring sitting on shoulders
  _cM(T,ac,new T.CylinderGeometry(0.096,0.144,0.074,9),rob,[0,0.570,0.080]);
  // Main hood drape (large panel falling behind head)
  const hood=_cM(T,ac,new T.BoxGeometry(0.208,0.286,0.022),rob,[0,0.426,0.118]); hood.rotation.x=0.36;
  // Hood side folds
  const hfL=_cM(T,ac,new T.BoxGeometry(0.086,0.252,0.014),rob,[-0.148,0.412,0.098]); hfL.rotation.z=0.24; hfL.rotation.x=0.30;
  const hfR=_cM(T,ac,new T.BoxGeometry(0.086,0.252,0.014),rob,[ 0.148,0.412,0.098]); hfR.rotation.z=-0.24; hfR.rotation.x=0.30;

  rA.position.set(0.228,0.382,0); rA.rotation.z=-0.30; rA.rotation.x=0.10;
  _cM(T,rA,new T.CylinderGeometry(0.046,0.058,0.240,6),rob,[0,0.120,0]);
  _cM(T,rA,new T.CylinderGeometry(0.034,0.044,0.196,6),sk,[0,0.358,0]);
  _cM(T,rA,new T.SphereGeometry(0.044,6,5),sk,[0,0.476,0]);
  // Short staff — gripped at mid-point, extends below and above
  const stf=new T.Group(); stf.name='staff'; rA.add(stf);
  stf.position.set(0,0.516,0);
  _cM(T,stf,new T.CylinderGeometry(0.016,0.020,0.580,6),wdD,[0,0.290,0]);
  // Leather grip wraps (3 bands)
  for(let i=0;i<3;i++){const wb=_cM(T,stf,new T.TorusGeometry(0.021,0.007,5,10),_cLth(T,0x200808),[0,0.068+i*0.060,0]); wb.rotation.x=Math.PI/2;}
  // Gem socket near skull
  _cM(T,stf,new T.CylinderGeometry(0.020,0.020,0.016,6),{color:new T.Color(0x1a0030),roughness:0.24,metalness:0.84},[0,0.548,0]);
  // Staff skull — sphere + features
  const skT=new T.Group(); skT.name='staffSkull'; stf.add(skT);
  skT.position.set(0,0.590,0);
  const skTb=_cM(T,skT,new T.SphereGeometry(0.050,8,7),bon,[0,0,0]); skTb.scale.y=0.84;
  _cM(T,skT,new T.BoxGeometry(0.054,0.026,0.038),bon,[0,-0.038,0]); // jaw extension
  _cM(T,skT,new T.SphereGeometry(0.012,5,4),eyeM,[-0.020, 0.005,-0.040]);
  _cM(T,skT,new T.SphereGeometry(0.012,5,4),eyeM,[ 0.020, 0.005,-0.040]);
  _cM(T,skT,new T.CylinderGeometry(0.005,0.005,0.007,5),eyeM,[0,-0.007,-0.042]);
  for(let i=0;i<3;i++) _cM(T,skT,new T.CylinderGeometry(0.003,0.003,0.016,4),bon,[-0.012+i*0.012,-0.030,-0.038]);

  // ── LEFT ARM — raised dramatically, palm up, magic orb ───────────────────────
  lA.position.set(-0.228,0.382,0); lA.rotation.z=0.84; lA.rotation.x=-0.24;
  _cM(T,lA,new T.CylinderGeometry(0.046,0.058,0.240,6),rob,[0,0.120,0]);
  _cM(T,lA,new T.CylinderGeometry(0.034,0.044,0.196,6),sk,[0,0.358,0]);
  // Wrist + open palm
  _cM(T,lA,new T.SphereGeometry(0.044,6,5),sk,[0,0.476,0]);
  // Fingers open upward (5 thin cylinders splayed from palm)
  const hndG=new T.Group(); hndG.name='hand'; lA.add(hndG);
  hndG.position.set(0,0.516,0);
  const fDat=[[-0.030,-0.004,0.006,-0.42,0],[-0.015,0.010,0.004,-0.18,0],
              [0,0.014,0,0,0],[ 0.015,0.010,0.004,0.18,0],[ 0.030,-0.004,0.006,0.42,0]];
  for(const[fx,fy,fz,rz] of fDat){
    const fg=_cM(T,hndG,new T.CylinderGeometry(0.008,0.010,0.078,4),sk,[fx,fy,fz]);
    fg.rotation.z=rz; fg.rotation.x=-0.26;
  }

  const orbG=new T.Group(); orbG.name='orbGroup'; lA.add(orbG);
  orbG.position.set(0,0.670,0);
  // Core energy sphere — emissive purple, intensity 2.0
  _cM(T,orbG,new T.SphereGeometry(0.072,10,9),_cGlow(T,0x9900ff,2.0),[0,0,0]);
  // Inner halo ring (tilted)
  const orR=_cM(T,orbG,new T.TorusGeometry(0.090,0.011,5,16),_cGlow(T,0xbb22ff,1.8),[0,0,0]);
  orR.rotation.x=Math.PI*0.30;
  // PointLight — purple, intensity 0.8, distance 1.5
  orbG.add(new T.PointLight(0x9900ff,0.8,1.5));

  const pGlow=_cGlow(T,0xcc33ff,2.0);

  // Particle orbit ring 1 — equatorial (6 particles)
  const pPiv1=new T.Group(); pPiv1.name='pPiv1'; orbG.add(pPiv1);
  for(let i=0;i<6;i++){
    const a=(i/6)*Math.PI*2;
    _cM(T,pPiv1,new T.SphereGeometry(0.013,5,4),pGlow,[Math.cos(a)*0.158,0,Math.sin(a)*0.158]);
  }
  // Particle orbit ring 2 — tilted 52° (4 particles, counter-direction)
  const pPiv2=new T.Group(); pPiv2.name='pPiv2'; orbG.add(pPiv2);
  pPiv2.rotation.z=Math.PI*0.29;
  for(let i=0;i<4;i++){
    const a=(i/4)*Math.PI*2+0.36;
    _cM(T,pPiv2,new T.SphereGeometry(0.010,5,4),pGlow,[Math.cos(a)*0.122,0,Math.sin(a)*0.122]);
  }

  // AnimationMixer — ring 1 forward (2s / rev)
  const mix1=new T.AnimationMixer(pPiv1);
  mix1.clipAction(new T.AnimationClip('orb1',2,[new T.NumberKeyframeTrack('.rotation[y]',[0,2],[0,Math.PI*2])])).play();
  // AnimationMixer — ring 2 reverse (1.4s / rev)
  const mix2=new T.AnimationMixer(pPiv2);
  mix2.clipAction(new T.AnimationClip('orb2',1.4,[new T.NumberKeyframeTrack('.rotation[y]',[0,1.4],[Math.PI*2,0])])).play();
  // Register mixers on the root group so the showcase loop can drive them
  if(!g.userData.mixers) g.userData.mixers=[];
  g.userData.mixers.push(mix1,mix2);

  // ── HEAD — pale, menacing, slightly tilted down (looking up) ──────────────────
  hd.rotation.x=-0.12;
  _cM(T,hd,new T.SphereGeometry(0.168,9,8),sk,[0,0.570,0]);
  _cM(T,hd,new T.BoxGeometry(0.218,0.108,0.208),sk,[0,0.490,0]); // jaw box
  _cM(T,hd,new T.BoxGeometry(0.200,0.058,0.188),sk,[0,0.388,0]); // chin
  // Eye shadow sockets (dark oval rings around deep-set eyes)
  const shadM={color:new T.Color(0x140814),roughness:0.95,metalness:0};
  for(const ex of [-0.062,0.062]){
    _cM(T,hd,new T.SphereGeometry(0.034,6,5),shadM,[ex,0.578,-0.146]);
    // Iris
    _cM(T,hd,new T.SphereGeometry(0.021,5,4),{color:new T.Color(0x280040),roughness:0.4,metalness:0.1},[ex,0.580,-0.157]);
    // Glint
    _cM(T,hd,new T.SphereGeometry(0.011,5,4),{color:new T.Color(0x8800cc),roughness:0.3,metalness:0.1},[ex+0.008,0.590,-0.164]);
  }
  // Narrow nose
  _cM(T,hd,new T.SphereGeometry(0.020,6,5),sk,[0,0.538,-0.154]);
  // Thin menacing mouth (asymmetric slight sneer)
  _cM(T,hd,new T.BoxGeometry(0.076,0.011,0.011),{color:new T.Color(0x7a2018),roughness:0.90,metalness:0},[0.012,0.500,-0.158]);
  // Sunken cheeks (dark shadow)
  _cM(T,hd,new T.SphereGeometry(0.026,5,4),shadM,[-0.112,0.538,-0.130]);
  _cM(T,hd,new T.SphereGeometry(0.026,5,4),shadM,[ 0.112,0.538,-0.130]);

  // ── HAIR — long straight black, thin PlaneGeometry-style panels ───────────────
  // Scalp cap
  _cM(T,hr,new T.SphereGeometry(0.170,9,7,0,Math.PI*2,0,Math.PI*0.53),hC,[0,0.572,0]);
  // Back panel — long, falling straight down
  const hp0=_cM(T,hr,new T.BoxGeometry(0.184,0.570,0.009),hC,[0,0.360,0.122]); hp0.rotation.x=-0.10;
  // Left side — falls over shoulder and chest
  const hp1=_cM(T,hr,new T.BoxGeometry(0.088,0.500,0.009),hC,[-0.158,0.342,-0.020]); hp1.rotation.z=0.15; hp1.rotation.x=0.06;
  const hp2=_cM(T,hr,new T.BoxGeometry(0.088,0.500,0.009),hC,[ 0.158,0.342,-0.020]); hp2.rotation.z=-0.15; hp2.rotation.x=0.06;
  // Front chest strands (falling forward over breastplate)
  const hp3=_cM(T,hr,new T.BoxGeometry(0.054,0.374,0.009),hC,[-0.132,0.210,-0.120]); hp3.rotation.z=0.12; hp3.rotation.x=0.24;
  const hp4=_cM(T,hr,new T.BoxGeometry(0.054,0.374,0.009),hC,[ 0.132,0.210,-0.120]); hp4.rotation.z=-0.12; hp4.rotation.x=0.24;
  // Outer thin strands (texture detail)
  const hp5=_cM(T,hr,new T.BoxGeometry(0.026,0.430,0.009),hC,[-0.194,0.296,0.048]); hp5.rotation.z=0.30;
  const hp6=_cM(T,hr,new T.BoxGeometry(0.026,0.430,0.009),hC,[ 0.194,0.296,0.048]); hp6.rotation.z=-0.30;
  // Centre parting strand (forward over forehead)
  _cM(T,hr,new T.BoxGeometry(0.018,0.110,0.009),hC,[0,0.528,-0.128]);
  */ // ── fim do bloco comentado (geometria 3D original) ─────────────────────────
}

// ══ Rogue — Shadow Thief ═══════════════════════════════════════════════════════
function _cRogue(T,g,Y){
  const nvy  = _cClth(T,0x1a2744);                                           // navy trousers
  const lt   = _cLth (T,0x6a3818);                                           // brown boots
  const ltF  = _cLth (T,0x8a5030);                                           // boot fold
  const dkS  = {color:new T.Color(0x1a1c2a),roughness:0.90,metalness:0.02}; // dark shirt
  const vest = _cLth (T,0x4a2808);                                           // leather vest
  const blt  = _cLth (T,0x5a3010);                                           // belt leather
  const bltM = {color:new T.Color(0x909098),roughness:0.42,metalness:0.80}; // belt metal
  const cpe  = _cClth(T,0x7a7a7a);                                           // grey cape
  const cpeDk= _cClth(T,0x525252);                                           // cape fold dark
  const sk   = _cSkin(T,0xd0a070);                                           // skin
  const hC   = _cClth(T,0x1c1410);                                           // dark hair
  const htC  = _cClth(T,0x383636);                                           // dark grey hat
  const tl   = {color:new T.Color(0x00aacc),roughness:0.52,metalness:0.05}; // turquoise feather
  const xb   = {color:new T.Color(0x888898),roughness:0.44,metalness:0.80}; // pistol metal
  const xw   = _cWood(T,0x5c2818);                                           // pistol grip wood

  const lB=new T.Group(); lB.name='lowerBody'; g.add(lB);
  const tr=new T.Group(); tr.name='torso';     g.add(tr);
  tr.position.set(0,Y+0.224,0);
  tr.rotation.x=-0.04;  // slight forward lean
  tr.rotation.z=-0.06;  // weight on left foot
  tr.rotation.y= 0.06;  // right shoulder slightly back
  const rA=new T.Group(); rA.name='rightArm'; tr.add(rA);
  const lA=new T.Group(); lA.name='leftArm';  tr.add(lA);
  const hd=new T.Group(); hd.name='head';     tr.add(hd);
  const hr=new T.Group(); hr.name='hair';     tr.add(hr);
  const ac=new T.Group(); ac.name='accessories'; tr.add(ac);

  // Left boot (left foot forward, z+)
  _cM(T,lB,new T.CylinderGeometry(0.064,0.082,0.368,8),lt, [-0.096,Y+0.184,0.020]); // shaft
  _cM(T,lB,new T.CylinderGeometry(0.075,0.080,0.034,8),ltF,[-0.096,Y+0.369,0.020]); // cuff band
  _cM(T,lB,new T.CylinderGeometry(0.082,0.072,0.026,8),ltF,[-0.096,Y+0.386,0.020]); // fold flare
  _cM(T,lB,new T.BoxGeometry(0.110,0.042,0.196),lt,[-0.096,Y+0.021,0.062]);          // foot
  _cM(T,lB,new T.BoxGeometry(0.104,0.038,0.066),lt,[-0.096,Y+0.038,-0.102]);         // heel cap
  // Right boot (right foot back, z-)
  _cM(T,lB,new T.CylinderGeometry(0.062,0.080,0.340,8),lt, [ 0.096,Y+0.170,-0.018]);
  _cM(T,lB,new T.CylinderGeometry(0.073,0.078,0.030,8),ltF,[ 0.096,Y+0.352,-0.018]);
  _cM(T,lB,new T.CylinderGeometry(0.080,0.070,0.024,8),ltF,[ 0.096,Y+0.367,-0.018]);
  _cM(T,lB,new T.BoxGeometry(0.108,0.042,0.190),lt,[ 0.096,Y+0.021,-0.060]);
  _cM(T,lB,new T.BoxGeometry(0.102,0.038,0.064),lt,[ 0.096,Y+0.038,-0.108]);

  const fldNvy={color:new T.Color(0x111b30),roughness:0.94,metalness:0};
  // Left thigh: cylinder + 2 fold crease rings
  _cM(T,lB,new T.CylinderGeometry(0.074,0.094,0.296,9),nvy,[-0.096,Y+0.532,0.012]);
  _cM(T,lB,new T.CylinderGeometry(0.082,0.078,0.010,8),fldNvy,[-0.096,Y+0.414,0.012]);
  _cM(T,lB,new T.CylinderGeometry(0.080,0.077,0.010,8),fldNvy,[-0.096,Y+0.444,0.012]);
  // Right thigh
  _cM(T,lB,new T.CylinderGeometry(0.071,0.091,0.272,9),nvy,[ 0.096,Y+0.510,-0.010]);
  _cM(T,lB,new T.CylinderGeometry(0.079,0.075,0.010,8),fldNvy,[ 0.096,Y+0.393,-0.010]);
  _cM(T,lB,new T.CylinderGeometry(0.077,0.074,0.010,8),fldNvy,[ 0.096,Y+0.421,-0.010]);

  _cM(T,lB,new T.BoxGeometry(0.088,0.072,0.060),blt,[-0.158,Y+0.648,0.040]); // L body
  _cM(T,lB,new T.BoxGeometry(0.090,0.024,0.062),_cLth(T,0x3a2008),[-0.158,Y+0.686,0.040]); // L flap
  _cM(T,lB,new T.BoxGeometry(0.022,0.018,0.008),bltM,[-0.158,Y+0.696,0.040]); // L buckle
  _cM(T,lB,new T.BoxGeometry(0.082,0.068,0.056),blt,[ 0.162,Y+0.642,0.038]); // R body
  _cM(T,lB,new T.BoxGeometry(0.084,0.022,0.058),_cLth(T,0x3a2008),[ 0.162,Y+0.677,0.038]); // R flap
  _cM(T,lB,new T.BoxGeometry(0.020,0.016,0.008),bltM,[ 0.162,Y+0.687,0.038]); // R buckle

  _cM(T,tr,new T.CylinderGeometry(0.098,0.182,0.524,9),dkS,[0,0.262,0]); // dark shirt
  // Vest: back slab + two side walls + two front half-panels (open V)
  _cM(T,tr,new T.BoxGeometry(0.296,0.412,0.010),vest,[0,0.208,0.134]);    // back
  _cM(T,tr,new T.BoxGeometry(0.038,0.412,0.272),vest,[-0.202,0.208,0]);   // side L
  _cM(T,tr,new T.BoxGeometry(0.038,0.412,0.272),vest,[ 0.202,0.208,0]);   // side R
  // Front panels — slight outward flare creating V opening
  const vpL=_cM(T,tr,new T.BoxGeometry(0.114,0.396,0.010),vest,[-0.086,0.208,-0.134]);
  vpL.rotation.y= 0.14;
  const vpR=_cM(T,tr,new T.BoxGeometry(0.114,0.396,0.010),vest,[ 0.086,0.208,-0.134]);
  vpR.rotation.y=-0.14;
  // Vest shoulder yoke + collar ring
  _cM(T,tr,new T.BoxGeometry(0.252,0.032,0.268),vest,[0,0.426,0]);
  _cM(T,tr,new T.CylinderGeometry(0.076,0.084,0.040,9),dkS,[0,0.480,0]);
  // Shirt sleeve shoulders
  for(const sx of [-0.200,0.200])
    _cM(T,tr,new T.SphereGeometry(0.104,7,6),dkS,[sx,0.468,0]);

  // ── DOUBLE BELT — two BoxGeometry bands on vest front face + 3 buckles ────────
  _cM(T,tr,new T.BoxGeometry(0.318,0.030,0.010),blt,[0,0.234,-0.140]); // upper band
  _cM(T,tr,new T.BoxGeometry(0.312,0.024,0.010),blt,[0,0.208,-0.140]); // lower band
  for(const bx of [0,-0.062,0.062])                                     // 3 buckles
    _cM(T,tr,new T.BoxGeometry(0.026,0.026,0.010),bltM,[bx,0.234,-0.143]);
  // Stitching dots along lower band
  for(let d=0;d<6;d++)
    _cM(T,tr,new T.SphereGeometry(0.005,3,2),bltM,[(-2.5+d)*0.044,0.208,-0.143]);

  // ── CAPE — grey (#7a7a7a), pinned left shoulder, open front, CatmullRom folds ─
  _cM(T,ac,new T.BoxGeometry(0.306,0.714,0.018),cpe,[-0.074,0.064,0.162]); // main drape
  _cM(T,ac,new T.BoxGeometry(0.216,0.044,0.026),cpe,[-0.092,0.490,0.138]); // shoulder yoke
  _cM(T,ac,new T.SphereGeometry(0.018,6,5),bltM,[-0.196,0.494,0.062]);     // cape clasp
  const mkCpe=(pts)=>{
    try{const c=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));
        return new T.TubeGeometry(c,12,0.010,5,false);}
    catch(e){return null;}
  };
  // Leading (right) edge — slight outward billow
  const cpeER=mkCpe([
    [ 0.082,0.484,0.154],[ 0.096,0.356,0.168],[ 0.090,0.186,0.172],
    [ 0.074,0.022,0.166],[ 0.058,-0.138,0.158],[ 0.044,-0.248,0.150],
  ]);
  if(cpeER) _cM(T,ac,cpeER,cpe,[0,0,0]);
  // Left edge (shoulder side)
  const cpeEL=mkCpe([
    [-0.230,0.490,0.148],[-0.242,0.352,0.162],[-0.238,0.174,0.168],
    [-0.232,-0.012,0.162],[-0.224,-0.210,0.152],[-0.218,-0.248,0.148],
  ]);
  if(cpeEL) _cM(T,ac,cpeEL,cpeDk,[0,0,0]);
  // Internal fold lines (two, suggesting flowing drape)
  const cpeF1=mkCpe([
    [-0.050,0.456,0.158],[-0.062,0.308,0.168],[-0.056,0.118,0.170],[-0.044,-0.082,0.164],[-0.034,-0.238,0.156],
  ]);
  if(cpeF1) _cM(T,ac,cpeF1,cpeDk,[0,0,0]);
  const cpeF2=mkCpe([
    [-0.144,0.436,0.156],[-0.154,0.288,0.166],[-0.150,0.098,0.168],[-0.142,-0.096,0.162],[-0.136,-0.248,0.154],
  ]);
  if(cpeF2) _cM(T,ac,cpeF2,cpeDk,[0,0,0]);

  lA.position.set(-0.246,0.400,0); lA.rotation.z=0.28; lA.rotation.x=-0.14;
  _cM(T,lA,new T.CylinderGeometry(0.050,0.062,0.298,7),dkS,[0,0.149,0]);
  _cM(T,lA,new T.CylinderGeometry(0.042,0.050,0.232,6),sk,  [0,0.406,0]);
  _cM(T,lA,new T.SphereGeometry(0.050,6,5),sk,[0,0.556,0]);
  _cM(T,lA,new T.CylinderGeometry(0.046,0.050,0.026,7),_cLth(T,0x2a1804),[0,0.540,0]); // fingerless glove cuff
  for(let fi=0;fi<4;fi++)
    _cM(T,lA,new T.CylinderGeometry(0.009,0.011,0.042,4),_cLth(T,0x2a1804),[(fi-1.5)*0.016,0.586,0]);

  // ── RIGHT ARM — pistol held low, barrel pointing downward ─────────────────────
  rA.position.set(0.244,0.372,0); rA.rotation.z=-0.20; rA.rotation.x=0.22; rA.rotation.y=0.08;
  _cM(T,rA,new T.CylinderGeometry(0.050,0.062,0.292,7),dkS,[0,0.146,0]);
  _cM(T,rA,new T.CylinderGeometry(0.042,0.050,0.226,6),sk,  [0,0.398,0]);
  _cM(T,rA,new T.SphereGeometry(0.050,6,5),sk,[0,0.544,0]);
  _cM(T,rA,new T.CylinderGeometry(0.046,0.050,0.026,7),_cLth(T,0x2a1804),[0,0.528,0]); // glove cuff
  // Pistol group (barrel pointing downward: rotation.x = PI-0.36 flips +Y to ~-Y)
  const wpG=new T.Group(); wpG.name='weapon'; rA.add(wpG);
  wpG.position.set(0.008,0.558,-0.020); wpG.rotation.x=Math.PI-0.36; wpG.rotation.z=0.08;
  // Barrel (hexagonal octagonal cross-section, tapered slightly)
  _cM(T,wpG,new T.CylinderGeometry(0.011,0.014,0.228,8),xb,[0,0.114,0]);
  _cM(T,wpG,new T.CylinderGeometry(0.016,0.016,0.012,8),xb,[0,0.008,0]); // barrel ring
  // Wooden grip
  _cM(T,wpG,new T.BoxGeometry(0.036,0.152,0.026),xw,[0,-0.082,0]);
  const gpC=_cM(T,wpG,new T.SphereGeometry(0.032,6,5),xw,[0,-0.172,0]); // pommel
  gpC.scale.set(0.88,0.68,0.78);
  // Trigger guard (half-torus arc)
  const tg=_cM(T,wpG,new T.TorusGeometry(0.026,0.005,4,8,Math.PI),bltM,[0,-0.066,-0.016]);
  tg.rotation.y=Math.PI/2;
  // Lock plate
  _cM(T,wpG,new T.BoxGeometry(0.018,0.058,0.012),bltM,[ 0.022,-0.038,0]);
  _cM(T,wpG,new T.BoxGeometry(0.010,0.030,0.010),bltM,[ 0.022,-0.006,0]); // hammer

  hd.rotation.z=0.14; // ~8° tilt to the left
  _cM(T,hd,new T.SphereGeometry(0.148,10,9),sk,[0,0.618,0]);          // cranium (slightly flat)
  _cM(T,hd,new T.BoxGeometry(0.200,0.084,0.196),sk,[0,0.546,0]);      // jaw
  _cM(T,hd,new T.BoxGeometry(0.166,0.058,0.186),sk,[0,0.500,0]);      // chin
  // Eyes + thin brows
  for(const ex of [-0.046,0.046]){
    _cM(T,hd,new T.SphereGeometry(0.020,6,5),{color:new T.Color(0x2a4070),roughness:0.50,metalness:0},[ex,0.634,-0.132]); // iris
    _cM(T,hd,new T.SphereGeometry(0.010,4,3),{color:new T.Color(0xffffff),roughness:0.2,metalness:0},[ex+0.007,0.642,-0.140]); // glint
    const bw=_cM(T,hd,new T.BoxGeometry(0.044,0.008,0.008),hC,[ex,0.652,-0.140]); // thin brow
    bw.rotation.z=ex<0? 0.08:-0.08;
  }
  _cM(T,hd,new T.SphereGeometry(0.016,6,5),sk,[0,0.600,-0.146]);      // nose
  // Slight asymmetric smile (right corner lifted)
  _cM(T,hd,new T.BoxGeometry(0.068,0.011,0.008),{color:new T.Color(0x803830),roughness:0.88,metalness:0},[0,0.562,-0.146]);
  const smR=_cM(T,hd,new T.SphereGeometry(0.011,4,4),{color:new T.Color(0x803830),roughness:0.88,metalness:0},[0.036,0.566,-0.144]);
  smR.scale.set(0.70,0.90,0.70); // right corner slightly raised = smirk
  // Ears
  for(const ex of [-0.142,0.142])
    _cM(T,hd,new T.SphereGeometry(0.024,5,4),sk,[ex,0.606,-0.006]);

  _cM(T,hr,new T.SphereGeometry(0.152,9,7,0,Math.PI*2,0,Math.PI*0.50),hC,[0,0.622,0]); // cap
  for(const sx of [-0.134,0.134])
    _cM(T,hr,new T.BoxGeometry(0.060,0.080,0.016),hC,[sx,0.596,-0.040]);  // side patches
  _cM(T,hr,new T.BoxGeometry(0.118,0.058,0.016),hC,[0,0.556,0.082]); // back wisp

  // ── WIDE-BRIM HAT — dark grey, TorusGeometry brim + CylinderGeometry crown ────
  const hatG=new T.Group(); hatG.name='hat'; ac.add(hatG);
  hatG.position.set(0,0.738,0.004); hatG.rotation.z=0.14; hatG.rotation.y=-0.08;
  // Brim: squashed TorusGeometry lying flat (inner radius matches crown)
  const brim=_cM(T,hatG,new T.TorusGeometry(0.226,0.068,4,14),htC,[0,-0.004,0]);
  brim.rotation.x=Math.PI/2; brim.scale.set(1,0.28,1); // squash flat
  // Crown
  _cM(T,hatG,new T.CylinderGeometry(0.148,0.162,0.138,12),htC,[0,0.073,0]);
  _cM(T,hatG,new T.CylinderGeometry(0.148,0.148,0.016,12),htC,[0,0.149,0]); // top cap
  // Hat band (dark leather strip)
  _cM(T,hatG,new T.CylinderGeometry(0.150,0.150,0.018,12),_cLth(T,0x2a1808),[0,0.008,0]);
  // Turquoise feather — TubeGeometry thin and gently curved
  const mkFth=(pts)=>{
    try{const c=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));
        return new T.TubeGeometry(c,18,0.009,5,false);}
    catch(e){return null;}
  };
  const fthGeo=mkFth([
    [ 0.158,0.010, 0.004],  // base — hat side
    [ 0.178,0.080,-0.012],  // rising
    [ 0.168,0.168,-0.028],  // arch peak
    [ 0.144,0.248,-0.040],  // curving back
    [ 0.112,0.306,-0.048],  // tip
  ]);
  if(fthGeo) _cM(T,hatG,fthGeo,tl,[0,0,0]);
  // Feather vane suggestion (thin flat BoxGeometry alongside shaft)
  const fthVane=_cM(T,hatG,new T.BoxGeometry(0.006,0.228,0.026),{color:new T.Color(0x0088aa),roughness:0.62,metalness:0.04},[0.150,0.170,-0.022]);
  fthVane.rotation.z=-0.40; fthVane.rotation.y=0.08;
}

// ══ Cleric — Holy Priest ═══════════════════════════════════════════════════════
function _cCleric(T,g,Y){
  const rob =_cClth(T,0xf0ead6);  // white-cream robe
  const robS=_cClth(T,0xe2d8be);  // robe fold/shadow
  const au  =_cGold(T);           // gold
  const lt  =_cLth(T,0x5c3a1e);  // brown leather belt
  const sk  =_cSkin(T,0xc4a06a); // mature tan skin
  const hC  =_cClth(T,0xbcaa68); // grey-blonde hair
  const wH  =_cClth(T,0xe8e4d4); // white hair strands
  const wd  =_cWood(T,0x7a4418); // turned wood staff

  const lB=new T.Group(); lB.name='lowerBody'; g.add(lB);
  const tr=new T.Group(); tr.name='torso';     g.add(tr);
  tr.position.set(0,Y+0.218,0); tr.rotation.x=0.08; tr.rotation.z=0.018;
  const rA=new T.Group(); rA.name='rightArm'; tr.add(rA);
  const lA=new T.Group(); lA.name='leftArm';  tr.add(lA);
  const hd=new T.Group(); hd.name='head';     tr.add(hd);
  const hr=new T.Group(); hr.name='hair';     tr.add(hr);
  const bd=new T.Group(); bd.name='beard';    tr.add(bd);
  const ac=new T.Group(); ac.name='accessories'; tr.add(ac);

  // ── ROBE LOWER — white-cream (#f0ead6), golden stripe, crosses, hem ──────────
  // Main robe cone (floor to waist)
  _cM(T,lB,new T.CylinderGeometry(0.150,0.300,0.736,11),rob,[0,Y+0.368,0]);
  // Robe fold/depth (slightly darker inner layer visible at front opening)
  _cM(T,lB,new T.BoxGeometry(0.034,0.720,0.012),robS,[0,Y+0.368,-0.187]);
  // Hem TubeGeometry border (TorusGeometry ring at base)
  const hem=_cM(T,lB,new T.TorusGeometry(0.292,0.013,6,28),au,[0,Y+0.016,0]);
  hem.rotation.x=Math.PI/2;
  // Golden vertical central stripe
  _cM(T,lB,new T.BoxGeometry(0.030,0.726,0.018),au,[0,Y+0.368,-0.190]);
  // Cross 1 — upper (BoxGeometry in relief on stripe)
  _cM(T,lB,new T.BoxGeometry(0.012,0.080,0.008),rob,[0,Y+0.574,-0.202]); // vertical
  _cM(T,lB,new T.BoxGeometry(0.058,0.012,0.008),rob,[0,Y+0.592,-0.202]); // horizontal
  // Cross 2 — lower
  _cM(T,lB,new T.BoxGeometry(0.012,0.076,0.008),rob,[0,Y+0.334,-0.202]);
  _cM(T,lB,new T.BoxGeometry(0.056,0.012,0.008),rob,[0,Y+0.350,-0.202]);

  _cM(T,tr,new T.CylinderGeometry(0.138,0.175,0.416,9),rob,[0,0.208,0]);
  for(const sx of [-0.165,0.165]) _cM(T,tr,new T.SphereGeometry(0.090,7,6),rob,[sx,0.322,0]);
  // Chest stripe
  _cM(T,tr,new T.BoxGeometry(0.028,0.400,0.018),au,[0,0.208,-0.144]);
  // Chest cross
  _cM(T,tr,new T.BoxGeometry(0.012,0.076,0.008),rob,[0,0.282,-0.154]);
  _cM(T,tr,new T.BoxGeometry(0.056,0.012,0.008),rob,[0,0.296,-0.154]);
  // Wide leather belt
  _cM(T,tr,new T.CylinderGeometry(0.148,0.150,0.054,10),lt,[0,-0.014,0]);
  // Buckle (front)
  _cM(T,tr,new T.BoxGeometry(0.046,0.040,0.010),{color:new T.Color(0x6e5c28),roughness:0.28,metalness:0.84},[0,-0.012,-0.156]);
  _cM(T,tr,new T.BoxGeometry(0.036,0.030,0.006),lt,[0,-0.012,-0.160]); // buckle inner frame

  rA.position.set(0.264,0.254,0); rA.rotation.z=-0.24; rA.rotation.x=-0.06;
  _cM(T,rA,new T.CylinderGeometry(0.052,0.064,0.332,6),rob,[0,0.166,0]);
  // Sleeve-cuff TubeGeometry border
  const cR=_cM(T,rA,new T.TorusGeometry(0.058,0.012,6,16),au,[0,0.338,0]); cR.rotation.x=Math.PI/2;
  _cM(T,rA,new T.SphereGeometry(0.050,6,5),sk,[0,0.370,0]);

  // Staff weapon group (held at grip level)
  const wp=new T.Group(); wp.name='weapon'; rA.add(wp);

  // Turned wood shaft — simulated with segments + bulge nodes (lathe effect)
  _cM(T,wp,new T.CylinderGeometry(0.015,0.023,0.220,7),wd,[0,0.110,0]);    // lower taper
  _cM(T,wp,new T.CylinderGeometry(0.021,0.015,0.140,7),wd,[0,0.290,0]);    // swell
  _cM(T,wp,new T.CylinderGeometry(0.016,0.021,0.140,7),wd,[0,0.430,0]);    // narrow
  _cM(T,wp,new T.CylinderGeometry(0.020,0.016,0.160,7),wd,[0,0.590,0]);    // upper swell
  _cM(T,wp,new T.CylinderGeometry(0.015,0.020,0.340,7),wd,[0,0.850,0]);    // slim top section
  // Bulge knobs at segment transitions (turned-wood look)
  for(const yp of [0.220,0.360,0.500,0.670,0.840])
    _cM(T,wp,new T.SphereGeometry(0.023,6,5),wd,[0,yp,0]);
  // Gold accent bands (2 bands on shaft)
  for(const yp of [0.360,0.670]){
    const rg=_cM(T,wp,new T.TorusGeometry(0.024,0.007,5,14),au,[0,yp,0]); rg.rotation.x=Math.PI/2;
  }
  // Gold collar at top of shaft
  _cM(T,wp,new T.CylinderGeometry(0.030,0.030,0.024,8),au,[0,1.032,0]);

  const topG=new T.Group(); topG.name='staffTop'; wp.add(topG);
  topG.position.set(0,1.052,0);
  // Main gold ring
  const mRing=_cM(T,topG,new T.TorusGeometry(0.096,0.019,7,20),au,[0,0,0]); mRing.rotation.x=Math.PI/2;
  // Outer accent ring (thinner)
  const oRing=_cM(T,topG,new T.TorusGeometry(0.110,0.009,6,20),au,[0,0,0]); oRing.rotation.x=Math.PI/2;
  // Centre sphere
  _cM(T,topG,new T.SphereGeometry(0.054,9,8),au,[0,0,0]);
  // 4 curved TubeGeometry petals radiating from ring
  const mkPetal=a=>{
    const cs=Math.cos(a), sn=Math.sin(a);
    const pts=[new T.Vector3(cs*0.096,0,sn*0.096), new T.Vector3(cs*0.174,0.058,sn*0.174),
               new T.Vector3(cs*0.142,0.112,sn*0.142), new T.Vector3(cs*0.066,0.118,sn*0.066),
               new T.Vector3(cs*0.016,0.088,sn*0.016)];
    try{return new T.TubeGeometry(new T.CatmullRomCurve3(pts),12,0.010,5,false);}catch(e){return null;}
  };
  for(let i=0;i<4;i++){const geo=mkPetal((i/4)*Math.PI*2); if(geo) _cM(T,topG,geo,au,[0,0,0]);}
  // Accent gem at each petal tip
  for(let i=0;i<4;i++){
    const a=(i/4)*Math.PI*2;
    _cM(T,topG,new T.SphereGeometry(0.015,6,5),_cGlow(T,0xf0d050,0.60),[Math.cos(a)*0.016,0.090,Math.sin(a)*0.016]);
  }

  // ── LEFT ARM — blessing, extended forward, palm open upward ──────────────────
  lA.position.set(-0.264,0.190,0); lA.rotation.z=-0.32; lA.rotation.x=-0.46;
  _cM(T,lA,new T.CylinderGeometry(0.052,0.064,0.264,6),rob,[0,0.132,0]);
  // Sleeve-cuff TubeGeometry border
  const cL=_cM(T,lA,new T.TorusGeometry(0.058,0.012,6,16),au,[0,0.270,0]); cL.rotation.x=Math.PI/2;
  // Forearm (skin)
  _cM(T,lA,new T.CylinderGeometry(0.038,0.050,0.202,6),sk,[0,0.404,0]);
  // Open palm
  const palmG=new T.Group(); palmG.name='palm'; lA.add(palmG);
  palmG.position.set(0,0.518,0);
  _cM(T,palmG,new T.BoxGeometry(0.090,0.046,0.072),sk,[0,0,0]);
  // 4 fingers (open upward)
  for(let i=0;i<4;i++) _cM(T,palmG,new T.CylinderGeometry(0.008,0.010,0.064,4),sk,[-0.033+i*0.022,0.052,-0.012]);
  // Thumb
  const th=_cM(T,palmG,new T.CylinderGeometry(0.009,0.012,0.052,4),sk,[-0.050,0.022,0.022]); th.rotation.z=0.44;

  // Golden blessing particles (Points geometry — subtle halo above palm)
  const pGeo=new T.BufferGeometry();
  const pPos=[];
  for(let i=0;i<28;i++){
    const a=Math.random()*Math.PI*2, r=0.038+Math.random()*0.094, h=0.032+Math.random()*0.118;
    pPos.push(r*Math.cos(a), h, r*Math.sin(a));
  }
  pGeo.setAttribute('position',new T.Float32BufferAttribute(pPos,3));
  const pPts=new T.Points(pGeo,new T.PointsMaterial({color:new T.Color(0xf0c840),size:0.018,sizeAttenuation:true,transparent:true,opacity:0.86}));
  pPts.castShadow=false; palmG.add(pPts);

  _cM(T,hd,new T.SphereGeometry(0.174,10,9),sk,[0,0.516,0]);
  _cM(T,hd,new T.BoxGeometry(0.222,0.096,0.210),sk,[0,0.440,0]); // jaw
  _cM(T,hd,new T.BoxGeometry(0.200,0.060,0.192),sk,[0,0.362,0]); // chin
  // Calm, slightly narrowed eyes
  for(const ex of [-0.058,0.058]){
    _cM(T,hd,new T.SphereGeometry(0.021,5,4),{color:new T.Color(0x6878a0),roughness:0.5,metalness:0},[ex,0.526,-0.156]);
    _cM(T,hd,new T.SphereGeometry(0.012,5,4),{color:new T.Color(0x8090b8),roughness:0.4,metalness:0},[ex+0.006,0.532,-0.163]);
    // Eyelid (serene, slightly hooded)
    const el=_cM(T,hd,new T.BoxGeometry(0.050,0.010,0.012),{color:new T.Color(0xb89070),roughness:0.90,metalness:0},[ex,0.539,-0.164]); el.rotation.z=ex<0?0.10:-0.10;
  }
  // Strong nose (mature)
  _cM(T,hd,new T.SphereGeometry(0.028,6,5),sk,[0,0.496,-0.168]);
  _cM(T,hd,new T.BoxGeometry(0.058,0.022,0.020),sk,[0,0.488,-0.174]);
  // Calm mouth (gentle upward curve)
  _cM(T,hd,new T.BoxGeometry(0.072,0.013,0.010),{color:new T.Color(0xb88460),roughness:0.90,metalness:0},[0,0.454,-0.168]);
  // Age lines (subtle forehead creases)
  _cM(T,hd,new T.BoxGeometry(0.054,0.006,0.007),{color:new T.Color(0xb89468),roughness:0.95,metalness:0},[0,0.560,-0.150]);
  _cM(T,hd,new T.BoxGeometry(0.040,0.005,0.006),{color:new T.Color(0xb89468),roughness:0.95,metalness:0},[0,0.572,-0.146]);

  _cM(T,hr,new T.SphereGeometry(0.178,9,7,0,Math.PI*2,0,Math.PI*0.38),hC,[0,0.528,0]);
  _cM(T,hr,new T.BoxGeometry(0.096,0.108,0.018),hC,[-0.165,0.472,0.026]);
  _cM(T,hr,new T.BoxGeometry(0.096,0.108,0.018),hC,[ 0.165,0.472,0.026]);
  // White temple streaks
  _cM(T,hr,new T.BoxGeometry(0.034,0.086,0.012),wH,[-0.160,0.472,0.018]);
  _cM(T,hr,new T.BoxGeometry(0.034,0.086,0.012),wH,[ 0.160,0.472,0.018]);

  // ── BEARD — long, bifurcated, TubeGeometry strands + white fios ──────────────
  // Chin at ~(0, 0.358, 0) in tr-local. Splits left + right descending to chest.
  const mkT=(pts,r)=>{try{const crv=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z))); return new T.TubeGeometry(crv,12,r,5,false);}catch(e){return null;}};
  const bDefs=[
    // Left main strand
    [[[-0.012,0.356,-0.150],[-0.056,0.268,-0.164],[-0.088,0.170,-0.168],[-0.104,0.074,-0.162],[-0.108,-0.018,-0.148]],0.030],
    // Right main strand
    [[[0.012,0.356,-0.150],[0.056,0.268,-0.164],[0.088,0.170,-0.168],[0.104,0.074,-0.162],[0.108,-0.018,-0.148]],0.030],
    // Left outer
    [[[-0.054,0.344,-0.143],[-0.112,0.256,-0.155],[-0.144,0.160,-0.158],[-0.148,0.068,-0.152],[-0.130,-0.012,-0.136]],0.020],
    // Right outer
    [[[0.054,0.344,-0.143],[0.112,0.256,-0.155],[0.144,0.160,-0.158],[0.148,0.068,-0.152],[0.130,-0.012,-0.136]],0.020],
    // Left tip curl
    [[[-0.110,-0.014,-0.146],[-0.124,-0.050,-0.146],[-0.116,-0.076,-0.128],[-0.088,-0.086,-0.108]],0.016],
    // Right tip curl
    [[[0.110,-0.014,-0.146],[0.122,-0.050,-0.146],[0.114,-0.076,-0.128],[0.086,-0.086,-0.108]],0.016],
    // Central bridge (short link at chin)
    [[[-0.012,0.350,-0.148],[0,0.360,-0.150],[0.012,0.350,-0.148]],0.018],
  ];
  for(const[pts,r] of bDefs){const geo=mkT(pts,r); if(geo) _cM(T,bd,geo,hC,[0,0,0]);}
  // White fios (thinner strands woven through)
  const wDefs=[
    [[[-0.024,0.346,-0.152],[-0.052,0.252,-0.165],[-0.078,0.158,-0.168],[-0.090,0.066,-0.158]],0.009],
    [[[0.024,0.346,-0.152],[0.052,0.254,-0.165],[0.076,0.160,-0.168],[0.088,0.068,-0.158]],0.009],
    [[[-0.068,0.338,-0.146],[-0.108,0.246,-0.154],[-0.134,0.154,-0.157],[-0.136,0.064,-0.150]],0.007],
    [[[0.068,0.338,-0.146],[0.106,0.248,-0.154],[0.132,0.156,-0.157],[0.134,0.066,-0.150]],0.007],
  ];
  for(const[pts,r] of wDefs){const geo=mkT(pts,r); if(geo) _cM(T,bd,geo,wH,[0,0,0]);}

  const hl=_cM(T,ac,new T.TorusGeometry(0.232,0.030,6,28),_cGlow(T,0xd4a828,0.82),[0,0.620,0.195]);
  hl.rotation.x=Math.PI*0.09;
}

// ══ Bard — Renaissance Lutenist ════════════════════════════════════════════════
function _cBard(T,g,Y){
  const nvy  = _cClth(T,0x1a2448);                                           // dark navy trousers
  const lt   = _cLth (T,0x6a3a18);                                           // brown boots
  const ltF  = _cLth (T,0x8a5232);                                           // boot fold (lighter)
  const wh   = {color:new T.Color(0xf0efeb),roughness:0.86,metalness:0};    // shirt white
  const blkS = {color:new T.Color(0x111111),roughness:0.92,metalness:0};    // black coat stripe
  const whs  = {color:new T.Color(0xe8e8e4),roughness:0.84,metalness:0};    // white coat stripe
  const gd   = {color:new T.Color(0xc8a951),roughness:0.28,metalness:0.88}; // gold border
  const sk   = _cSkin(T,0xd0a070);                                           // warm skin
  const hC   = _cClth(T,0x8b2500);                                           // red hair
  const red  = _cClth(T,0xcc1100);                                           // beret red
  const wd   = _cWood(T,0x7a4520);                                           // lute body wood
  const wdN  = _cWood(T,0x5a3010);                                           // neck wood (darker)
  const wdH  = {color:new T.Color(0x100804),roughness:0.95,metalness:0};    // soundhole dark
  const strM = {color:new T.Color(0xd8c870),roughness:0.20,metalness:0.10}; // gut strings

  const lB=new T.Group(); lB.name='lowerBody'; g.add(lB);
  const tr=new T.Group(); tr.name='torso';     g.add(tr);
  tr.position.set(0,Y+0.450,0); tr.rotation.x=0.10; tr.rotation.z=-0.02; // leaned back
  const rA=new T.Group(); rA.name='rightArm'; tr.add(rA);
  const lA=new T.Group(); lA.name='leftArm';  tr.add(lA);
  const hd=new T.Group(); hd.name='head';     tr.add(hd);
  const hr=new T.Group(); hr.name='hair';     tr.add(hr);
  const ac=new T.Group(); ac.name='accessories'; tr.add(ac);

  // Left boot (left foot forward, z+)
  _cM(T,lB,new T.CylinderGeometry(0.068,0.083,0.232,8),lt, [-0.093,Y+0.116,0.022]);
  _cM(T,lB,new T.CylinderGeometry(0.076,0.080,0.034,8),ltF,[-0.093,Y+0.233,0.022]); // cuff band
  _cM(T,lB,new T.CylinderGeometry(0.083,0.073,0.026,8),ltF,[-0.093,Y+0.250,0.022]); // fold flare
  _cM(T,lB,new T.BoxGeometry(0.112,0.042,0.198),lt,  [-0.093,Y+0.021,0.062]);        // foot
  _cM(T,lB,new T.BoxGeometry(0.106,0.038,0.068),lt,  [-0.093,Y+0.038,-0.100]);       // heel cap
  // Right boot (right foot back, z-)
  _cM(T,lB,new T.CylinderGeometry(0.066,0.081,0.214,8),lt, [ 0.093,Y+0.107,-0.016]);
  _cM(T,lB,new T.CylinderGeometry(0.074,0.078,0.032,8),ltF,[ 0.093,Y+0.220,-0.016]);
  _cM(T,lB,new T.CylinderGeometry(0.080,0.071,0.024,8),ltF,[ 0.093,Y+0.237,-0.016]);
  _cM(T,lB,new T.BoxGeometry(0.110,0.042,0.192),lt,  [ 0.093,Y+0.021,-0.056]);
  _cM(T,lB,new T.BoxGeometry(0.104,0.038,0.066),lt,  [ 0.093,Y+0.038,-0.106]);

  const fldNvy={color:new T.Color(0x101830),roughness:0.94,metalness:0};
  // Left thigh: lower cylinder + upper puff sphere
  _cM(T,lB,new T.CylinderGeometry(0.072,0.090,0.100,8),nvy,[-0.093,Y+0.302,0.014]);
  const ptL=_cM(T,lB,new T.SphereGeometry(0.106,8,7),nvy,[-0.093,Y+0.406,0.012]);
  ptL.scale.set(0.82,0.94,0.82);
  // Fold bands on left cylinder (darker pinch rings)
  for(let i=0;i<3;i++)
    _cM(T,lB,new T.CylinderGeometry(0.078+i*0.003,0.076+i*0.002,0.010,8),fldNvy,[-0.093,Y+0.260+i*0.022,0.012]);
  // Right thigh
  _cM(T,lB,new T.CylinderGeometry(0.070,0.088,0.092,8),nvy,[ 0.093,Y+0.288,-0.012]);
  const ptR=_cM(T,lB,new T.SphereGeometry(0.102,8,7),nvy,[ 0.093,Y+0.386,-0.010]);
  ptR.scale.set(0.80,0.92,0.80);
  for(let i=0;i<3;i++)
    _cM(T,lB,new T.CylinderGeometry(0.075+i*0.003,0.073+i*0.002,0.010,8),fldNvy,[ 0.093,Y+0.248+i*0.020,-0.010]);

  // ── TORSO — white shirt base + Renaissance striped coat ─────────────────────
  // White shirt underlay (underlayer, shows at collar and sleeve edges)
  _cM(T,tr,new T.CylinderGeometry(0.090,0.170,0.488,10),wh,[0,0.230,0]);
  // Coat — back slab + two sides
  _cM(T,tr,new T.BoxGeometry(0.268,0.468,0.008),blkS,[0,0.230,0.134]);   // back
  _cM(T,tr,new T.BoxGeometry(0.040,0.468,0.272),blkS,[-0.214,0.230,0]);  // side L
  _cM(T,tr,new T.BoxGeometry(0.040,0.468,0.272),blkS,[ 0.214,0.230,0]);  // side R
  // Front face: 8 alternating vertical stripe panels (z=-0.133)
  const SW=0.0336;
  for(let i=0;i<8;i++){
    const sx=-0.1512+i*SW+SW*0.5;
    _cM(T,tr,new T.BoxGeometry(SW-0.002,0.462,0.009),(i%2===0)?blkS:whs,[sx,0.230,-0.133]);
  }
  // Top/bottom coat caps
  _cM(T,tr,new T.BoxGeometry(0.268,0.034,0.272),blkS,[0,0.474,0]);
  _cM(T,tr,new T.BoxGeometry(0.268,0.028,0.272),blkS,[0,-0.006,0]);
  // Shoulder puffs (white — billowing shirt sleeves)
  for(const sx of [-0.208,0.208])
    _cM(T,tr,new T.SphereGeometry(0.108,7,6),whs,[sx,0.478,0]);
  // Gold belt band visible at coat hem line
  _cM(T,tr,new T.CylinderGeometry(0.158,0.158,0.024,10),gd,[0,-0.004,0]);
  _cM(T,tr,new T.BoxGeometry(0.046,0.034,0.012),gd,[0,-0.004,-0.162]); // front buckle

  // ── GOLD BORDER — TubeGeometry thin curves around coat perimeter ─────────────
  const mkBdr=(pts)=>{
    try{const c=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));
        return new T.TubeGeometry(c,pts.length*5,0.010,6,false);}
    catch(e){return null;}
  };
  // Left front vertical border
  const bL=mkBdr([[-0.172,0.466,-0.135],[-0.172,0.300,-0.135],[-0.172,0.124,-0.135],[-0.172,0.006,-0.135]]);
  if(bL) _cM(T,tr,bL,gd,[0,0,0]);
  // Right front vertical border
  const bR=mkBdr([[0.172,0.466,-0.135],[0.172,0.300,-0.135],[0.172,0.124,-0.135],[0.172,0.006,-0.135]]);
  if(bR) _cM(T,tr,bR,gd,[0,0,0]);
  // Bottom hem border
  const bBot=mkBdr([[-0.172,0.006,-0.135],[-0.086,0.002,-0.135],[0,0,-0.135],[0.086,0.002,-0.135],[0.172,0.006,-0.135]]);
  if(bBot) _cM(T,tr,bBot,gd,[0,0,0]);
  // Top collar edge
  const bTop=mkBdr([[-0.172,0.466,-0.135],[-0.090,0.476,-0.136],[-0.034,0.480,-0.136],[0.034,0.480,-0.136],[0.090,0.476,-0.136],[0.172,0.466,-0.135]]);
  if(bTop) _cM(T,tr,bTop,gd,[0,0,0]);
  // V-neck front opening (two angled gold lines meeting at mid-chest)
  const bVL=mkBdr([[-0.068,0.466,-0.136],[-0.026,0.398,-0.137],[0,0.360,-0.137]]);
  if(bVL) _cM(T,tr,bVL,gd,[0,0,0]);
  const bVR=mkBdr([[ 0.068,0.466,-0.136],[ 0.026,0.398,-0.137],[0,0.360,-0.137]]);
  if(bVR) _cM(T,tr,bVR,gd,[0,0,0]);

  // ── LACE COLLAR — flat disc + ring of fringe cylinders around neck ───────────
  _cM(T,tr,new T.CylinderGeometry(0.168,0.190,0.015,12),wh,[0,0.518,0]); // collar disc
  for(let i=0;i<18;i++){                                                   // lace fringe
    const a=(i/18)*Math.PI*2, cx=Math.cos(a)*0.188, cz=Math.sin(a)*0.188;
    _cM(T,tr,new T.CylinderGeometry(0.010,0.008,0.020,5),
      {color:new T.Color(0xe8e8e0),roughness:0.88,metalness:0},[cx,0.520,cz]);
  }
  for(let i=0;i<18;i++){                                                   // connecting pearls
    const a=((i+0.5)/18)*Math.PI*2, cx=Math.cos(a)*0.186, cz=Math.sin(a)*0.186;
    _cM(T,tr,new T.SphereGeometry(0.008,4,3),{color:new T.Color(0xdededa),roughness:0.90,metalness:0},[cx,0.518,cz]);
  }
  _cM(T,tr,new T.CylinderGeometry(0.076,0.084,0.038,10),wh,[0,0.548,0]); // shirt collar ring

  const luteG=new T.Group(); luteG.name='lute'; tr.add(luteG);
  luteG.position.set(-0.016,0.162,-0.216);
  luteG.rotation.x=-0.06; // face slightly toward camera
  luteG.rotation.z= 0.10; // slight tilt

  // Body — pear shape: lower bout + upper bout
  const lbod=_cM(T,luteG,new T.SphereGeometry(0.158,11,9),wd,[0,0,0]);
  lbod.scale.set(0.72,0.88,0.44);
  const lbod2=_cM(T,luteG,new T.SphereGeometry(0.114,9,8),wd,[0,0.166,0]);
  lbod2.scale.set(0.70,0.76,0.43);
  // Sound hole: dark cylinder + gold ring + 4-line rosette
  const shCyl=_cM(T,luteG,new T.CylinderGeometry(0.036,0.036,0.054,14),wdH,[0,0.020,-0.093]);
  shCyl.rotation.x=Math.PI/2;
  const shRing=_cM(T,luteG,new T.TorusGeometry(0.038,0.006,5,14),gd,[0,0.020,-0.094]);
  shRing.rotation.x=Math.PI/2;
  for(let r=0;r<4;r++){
    const deco=_cM(T,luteG,new T.BoxGeometry(0.070,0.004,0.006),
      {color:new T.Color(0xa85828),roughness:0.82,metalness:0.04},[0,0.020,-0.093]);
    deco.rotation.x=Math.PI/2; deco.rotation.z=(r/4)*Math.PI;
  }
  // Bridge at body bottom
  _cM(T,luteG,new T.BoxGeometry(0.088,0.012,0.008),_cWood(T,0x4a2808),[0,-0.052,-0.092]);

  // Neck group — angled up-left (~30° from vertical in luteG space)
  const neckG=new T.Group(); luteG.add(neckG);
  neckG.position.set(0,0.204,0); neckG.rotation.z=-0.52;
  _cM(T,neckG,new T.CylinderGeometry(0.017,0.024,0.484,6),wdN,[0,0.242,0]);
  for(let f=0;f<7;f++){                                                    // frets
    const fr=_cM(T,neckG,new T.BoxGeometry(0.040,0.006,0.010),
      {color:new T.Color(0xb89030),roughness:0.44,metalness:0.82},[0,0.058+f*0.058,0]);
  }
  _cM(T,neckG,new T.BoxGeometry(0.042,0.010,0.014),                       // nut
    {color:new T.Color(0xf0e8d0),roughness:0.50,metalness:0},[0,0.492,0]);

  // Headstock — bends back from neck top
  const hstG=new T.Group(); neckG.add(hstG);
  hstG.position.set(0,0.496,0); hstG.rotation.z=0.50;
  _cM(T,hstG,new T.BoxGeometry(0.046,0.108,0.020),wdN,[0,0.054,0]);
  for(const[px,py] of [[-0.028,0.018],[0.028,0.018],[-0.028,0.054],[0.028,0.054],[-0.028,0.088],[0.028,0.088]])
    _cM(T,hstG,new T.SphereGeometry(0.011,5,4),{color:new T.Color(0xb88810),roughness:0.30,metalness:0.86},[px,py,0]);

  // 6 strings — TubeGeometry from bridge up along neck in luteG local space
  // Neck tilts at z=-0.52 from neckG origin (0,0.204,0); approx headstock end in luteG:
  //   neckG top = (sin(-0.52)*0.484, 0.204+cos(0.52)*0.484, 0) = (-0.247, 0.618, 0)
  for(let s=0;s<6;s++){
    const ox=(s-2.5)*0.0108;
    try{
      const pts=[
        new T.Vector3(ox,-0.050,-0.088),               // bridge
        new T.Vector3(ox*0.96,0.020,-0.086),            // over sound hole
        new T.Vector3(ox*0.80,0.208,-0.014),            // neck base
        new T.Vector3(ox*0.65-0.124,0.416,0.016),       // neck mid
        new T.Vector3(ox*0.55-0.222,0.588,0.026),       // near headstock
      ];
      const c=new T.CatmullRomCurve3(pts);
      const geo=new T.TubeGeometry(c,22,0.0028,4,false);
      _cM(T,luteG,geo,strM,[0,0,0]);
    }catch(e){}
  }

  // ── LEFT ARM — fretting hand (reaches toward lute neck, raised) ──────────────
  lA.position.set(-0.228,0.394,0); lA.rotation.z=0.38; lA.rotation.x=-0.32; lA.rotation.y=0.16;
  _cM(T,lA,new T.CylinderGeometry(0.050,0.062,0.302,7),whs,[0,0.151,0]);   // sleeve
  _cM(T,lA,new T.CylinderGeometry(0.042,0.050,0.234,6),sk,  [0,0.410,0]);  // forearm
  _cM(T,lA,new T.SphereGeometry(0.050,6,5),sk,[0,0.560,0]);                 // hand
  for(let fi=0;fi<4;fi++)                                                    // fretting fingers
    _cM(T,lA,new T.CylinderGeometry(0.010,0.012,0.048,4),sk,[(fi-1.5)*0.018,0.598,0]);

  // ── RIGHT ARM — strumming hand (angled forward toward lute body) ─────────────
  rA.position.set(0.224,0.322,0); rA.rotation.z=-0.22; rA.rotation.x=-0.40; rA.rotation.y=-0.12;
  _cM(T,rA,new T.CylinderGeometry(0.050,0.062,0.296,7),whs,[0,0.148,0]);
  _cM(T,rA,new T.CylinderGeometry(0.042,0.050,0.230,6),sk,  [0,0.402,0]);
  _cM(T,rA,new T.SphereGeometry(0.050,6,5),sk,[0,0.546,0]);
  for(let fi=0;fi<4;fi++)                                                    // strumming fingers
    _cM(T,rA,new T.CylinderGeometry(0.009,0.011,0.044,4),sk,[(fi-1.5)*0.017,0.582,-0.014]);

  _cM(T,hd,new T.SphereGeometry(0.152,10,9),sk,[0,0.556,0]);           // cranium
  _cM(T,hd,new T.BoxGeometry(0.206,0.088,0.204),sk,[0,0.482,0]);       // jaw
  _cM(T,hd,new T.BoxGeometry(0.172,0.060,0.192),sk,[0,0.434,0]);       // chin
  // Round rosy cheeks
  for(const cx of [-0.076,0.076])
    _cM(T,hd,new T.SphereGeometry(0.052,6,5),{color:new T.Color(0xd48060),roughness:0.88,metalness:0},[cx,0.520,-0.120]);
  // Eyes — happy (green, arched brows pointing outward)
  for(const ex of [-0.050,0.050]){
    _cM(T,hd,new T.SphereGeometry(0.022,6,5),{color:new T.Color(0x3a6030),roughness:0.50,metalness:0},[ex,0.570,-0.136]); // iris
    _cM(T,hd,new T.SphereGeometry(0.012,4,3),{color:new T.Color(0xffffff),roughness:0.2,metalness:0},[ex+0.008,0.578,-0.144]); // glint
    const bw=_cM(T,hd,new T.BoxGeometry(0.046,0.011,0.010),{color:new T.Color(0x7a2400),roughness:0.80,metalness:0},[ex,0.590,-0.144]);
    bw.rotation.z=ex<0? 0.18:-0.18; // arched outward — happy expression
  }
  _cM(T,hd,new T.SphereGeometry(0.018,6,5),sk,[0,0.528,-0.148]);       // nose
  // Open smile: upper lip + teeth strip + lower lip + corner lifts
  _cM(T,hd,new T.BoxGeometry(0.086,0.014,0.008),{color:new T.Color(0x8a2818),roughness:0.86,metalness:0},[0,0.484,-0.148]);
  _cM(T,hd,new T.BoxGeometry(0.068,0.018,0.006),{color:new T.Color(0xf4f0ea),roughness:0.50,metalness:0},[0,0.474,-0.150]); // teeth
  _cM(T,hd,new T.BoxGeometry(0.072,0.012,0.008),{color:new T.Color(0x7a2010),roughness:0.86,metalness:0},[0,0.460,-0.148]);
  for(const cx of [-0.046,0.046])
    _cM(T,hd,new T.SphereGeometry(0.013,4,4),{color:new T.Color(0x8a2818),roughness:0.86,metalness:0},[cx,0.490,-0.146]);
  // Ears
  for(const ex of [-0.146,0.146])
    _cM(T,hd,new T.SphereGeometry(0.026,5,4),sk,[ex,0.542,-0.006]);

  // ── LONG WAVY RED HAIR — TubeGeometry CatmullRomCurve3 ──────────────────────
  _cM(T,hr,new T.SphereGeometry(0.160,9,7,0,Math.PI*2,0,Math.PI*0.52),hC,[0,0.562,0]); // hair cap
  const mkHair=(pts)=>{
    try{const c=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));
        return new T.TubeGeometry(c,14,0.014,6,false);}
    catch(e){return null;}
  };
  // Strands — all coordinates in tr-local space
  const hairDefs=[
    // Left side long strands falling to shoulder / chest
    [[-0.104,0.658,-0.078],[-0.146,0.582,-0.038],[-0.176,0.470,-0.004],[-0.192,0.328,0.014],[-0.178,0.192,0.004]],
    [[-0.078,0.652,-0.094],[-0.128,0.572,-0.034],[-0.160,0.444,0.006],[-0.172,0.298,0.018],[-0.158,0.160,0.008]],
    [[-0.052,0.682,-0.102],[-0.090,0.606,-0.052],[-0.116,0.476,0.008],[-0.126,0.330,0.022]],
    // Right side long strands
    [[ 0.104,0.658,-0.078],[ 0.146,0.582,-0.038],[ 0.176,0.470,-0.004],[ 0.192,0.328,0.014],[ 0.178,0.192,0.004]],
    [[ 0.078,0.652,-0.094],[ 0.128,0.572,-0.034],[ 0.160,0.444,0.006],[ 0.172,0.298,0.018],[ 0.158,0.160,0.008]],
    [[ 0.052,0.682,-0.102],[ 0.090,0.606,-0.052],[ 0.116,0.476,0.008],[ 0.126,0.330,0.022]],
    // Back hair
    [[-0.038,0.664,0.092],[-0.056,0.582,0.112],[-0.064,0.456,0.114],[-0.050,0.314,0.104]],
    [[ 0.038,0.664,0.092],[ 0.056,0.582,0.112],[ 0.064,0.456,0.114],[ 0.050,0.314,0.104]],
    // Front-framing strands (beside face)
    [[-0.080,0.672,-0.110],[-0.100,0.598,-0.128],[-0.094,0.508,-0.124],[-0.076,0.412,-0.106]],
    [[ 0.080,0.672,-0.110],[ 0.100,0.598,-0.128],[ 0.094,0.508,-0.124],[ 0.076,0.412,-0.106]],
  ];
  for(const pts of hairDefs){const geo=mkHair(pts); if(geo) _cM(T,hr,geo,hC,[0,0,0]);}

  // ── RED BERET — flat CylinderGeometry, tilted ~20° left ─────────────────────
  const hatG=new T.Group(); hatG.name='beret'; ac.add(hatG);
  hatG.position.set(0,0.688,0.004); hatG.rotation.z=-0.36; hatG.rotation.y=0.08;
  _cM(T,hatG,new T.CylinderGeometry(0.192,0.188,0.030,12),red,[0,0,0]);         // flat disc
  _cM(T,hatG,new T.SphereGeometry(0.184,9,6,0,Math.PI*2,0,Math.PI*0.24),red,[0,0.012,0]); // dome
  _cM(T,hatG,new T.CylinderGeometry(0.158,0.160,0.026,12),_cLth(T,0x990a00),[0,-0.026,0]); // headband
  _cM(T,hatG,new T.SphereGeometry(0.014,5,4),{color:new T.Color(0xaa0900),roughness:0.86,metalness:0},[0.006,0.016,0]); // fabric tab
}

// ══ Paladin — Silver Knight ════════════════════════════════════════════════════
function _cPaladin(T,g,Y){
  const sv  ={color:new T.Color(0xd4d8e0),roughness:0.15,metalness:0.96}; // polished silver
  const svH ={color:new T.Color(0xe2e8f2),roughness:0.12,metalness:0.98}; // highlight silver
  const au  ={color:new T.Color(0xcca830),roughness:0.22,metalness:0.88}; // gold
  const ry  =_cClth(T,0x1a3a8f);  // royal blue
  const sw  ={color:new T.Color(0xdce4f4),roughness:0.16,metalness:0.94}; // blade
  const lt  =_cLth(T,0x4a2810);   // belt leather
  const ltG =_cLth(T,0x3a2010);   // grip leather
  const sk  =_cSkin(T,0xc4a068);  // young skin
  const hC  =_cClth(T,0x5a3818);  // brown hair

  const lB=new T.Group(); lB.name='lowerBody'; g.add(lB);
  const tr=new T.Group(); tr.name='torso';     g.add(tr);
  tr.position.set(0,Y+0.232,0); tr.rotation.x=-0.05; // upright, open chest
  const rA=new T.Group(); rA.name='rightArm'; tr.add(rA);
  const lA=new T.Group(); lA.name='leftArm';  tr.add(lA);
  const hd=new T.Group(); hd.name='head';     tr.add(hd);
  const hr=new T.Group(); hr.name='hair';     tr.add(hr);
  const ac=new T.Group(); ac.name='accessories'; tr.add(ac);

  // ── GREAVES (CylinderGeometry segmented) + SABATONS ──────────────────────────
  // Left leg (slightly forward — left foot advanced)
  _cM(T,lB,new T.CylinderGeometry(0.080,0.100,0.210,8),sv,[-0.102,Y+0.300,0.014]); // thigh
  _cM(T,lB,new T.CylinderGeometry(0.072,0.086,0.196,8),sv,[-0.102,Y+0.112,0.016]); // shin
  _cM(T,lB,new T.CylinderGeometry(0.086,0.088,0.012,8),au,[-0.102,Y+0.196,0.015]); // gold segment ring
  const knL=_cM(T,lB,new T.SphereGeometry(0.076,7,6),sv,[-0.102,Y+0.210,-0.050]);  // kneecap
  const knLr=_cM(T,lB,new T.TorusGeometry(0.076,0.012,6,14),au,[-0.102,Y+0.210,-0.050]); knLr.rotation.x=Math.PI/2;
  _cM(T,lB,new T.BoxGeometry(0.134,0.050,0.210),sv,[-0.102,Y+0.016,0.018]);         // sabaton
  _cM(T,lB,new T.BoxGeometry(0.126,0.046,0.076),sv,[-0.102,Y+0.048,-0.106]);        // toe cap
  _cM(T,lB,new T.BoxGeometry(0.136,0.012,0.216),au,[-0.102,Y+0.046,0.018]);         // gold trim

  // Right leg (back — weight leg)
  _cM(T,lB,new T.CylinderGeometry(0.080,0.100,0.210,8),sv,[ 0.102,Y+0.300,-0.014]);
  _cM(T,lB,new T.CylinderGeometry(0.072,0.086,0.196,8),sv,[ 0.102,Y+0.112,-0.016]);
  _cM(T,lB,new T.CylinderGeometry(0.086,0.088,0.012,8),au,[ 0.102,Y+0.196,-0.015]);
  const knR=_cM(T,lB,new T.SphereGeometry(0.076,7,6),sv,[ 0.102,Y+0.210,-0.062]);
  const knRr=_cM(T,lB,new T.TorusGeometry(0.076,0.012,6,14),au,[ 0.102,Y+0.210,-0.062]); knRr.rotation.x=Math.PI/2;
  _cM(T,lB,new T.BoxGeometry(0.134,0.050,0.210),sv,[ 0.102,Y+0.016,-0.018]);
  _cM(T,lB,new T.BoxGeometry(0.126,0.046,0.076),sv,[ 0.102,Y+0.048,-0.108]);
  _cM(T,lB,new T.BoxGeometry(0.136,0.012,0.216),au,[ 0.102,Y+0.046,-0.018]);

  // ── BATTLE SKIRT (fauld) — 8 rectangular plates in fan around waist ───────────
  _cM(T,lB,new T.CylinderGeometry(0.162,0.170,0.038,10),sv,[0,Y+0.476,0]);  // base ring
  _cM(T,lB,new T.CylinderGeometry(0.170,0.170,0.010,10),au,[0,Y+0.456,0]);  // gold band
  for(let i=0;i<8;i++){
    const a=(i/8)*Math.PI*2, px=Math.sin(a)*0.158, pz=Math.cos(a)*0.158;
    const pl=_cM(T,lB,new T.BoxGeometry(0.076,0.134,0.016),sv,[px,Y+0.412,pz]);
    pl.rotation.y=-a; pl.rotation.x=0.07; // slight outward flare
    const pt=_cM(T,lB,new T.BoxGeometry(0.078,0.010,0.016),au,[px,Y+0.340,pz]); pt.rotation.y=-a;
  }

  _cM(T,tr,new T.BoxGeometry(0.462,0.522,0.286),sv,[0,0.254,0]);           // body
  _cM(T,tr,new T.BoxGeometry(0.438,0.490,0.024),svH,[0,0.254,-0.150]);     // front face (brighter)
  _cM(T,tr,new T.BoxGeometry(0.016,0.482,0.016),sv,[0,0.254,-0.160]);      // center ridge
  _cM(T,tr,new T.BoxGeometry(0.438,0.013,0.016),au,[0,0.362,-0.160]);      // horizontal divider
  _cM(T,tr,new T.BoxGeometry(0.438,0.013,0.016),au,[0,0.118,-0.160]);      // lower divider
  // Gorget (armor collar ring)
  _cM(T,tr,new T.CylinderGeometry(0.082,0.102,0.060,9),sv,[0,0.526,0]);
  _cM(T,tr,new T.CylinderGeometry(0.102,0.104,0.012,9),au,[0,0.494,0]);
  // Belt + buckle
  _cM(T,tr,new T.CylinderGeometry(0.148,0.150,0.052,10),lt,[0,-0.016,0]);
  _cM(T,tr,new T.BoxGeometry(0.060,0.046,0.012),au,[0,-0.014,-0.156]); // buckle
  _cM(T,tr,new T.BoxGeometry(0.050,0.036,0.007),lt,[0,-0.014,-0.160]);  // buckle inner

  // ── ARABESQUE — TubeGeometry curved gold engraving on breastplate ─────────────
  const mkA=(pts)=>{try{const c=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));return new T.TubeGeometry(c,10,0.007,5,false);}catch(e){return null;}};
  const arDefs=[
    // Central spine
    [[0,0.442,-0.155],[0,0.352,-0.158],[0,0.252,-0.158],[0,0.150,-0.155]],
    // Left upper flourish
    [[-0.010,0.364,-0.158],[-0.074,0.336,-0.163],[-0.106,0.286,-0.165],[-0.084,0.238,-0.163],[-0.038,0.246,-0.159]],
    // Right upper flourish
    [[0.010,0.364,-0.158],[0.074,0.336,-0.163],[0.106,0.286,-0.165],[0.084,0.238,-0.163],[0.038,0.246,-0.159]],
    // Left lower flourish
    [[-0.010,0.246,-0.158],[-0.070,0.212,-0.163],[-0.098,0.170,-0.165],[-0.070,0.130,-0.162],[-0.028,0.140,-0.158]],
    // Right lower flourish
    [[0.010,0.246,-0.158],[0.070,0.212,-0.163],[0.098,0.170,-0.165],[0.070,0.130,-0.162],[0.028,0.140,-0.158]],
    // Upper-left corner curl
    [[-0.106,0.420,-0.155],[-0.134,0.400,-0.160],[-0.132,0.372,-0.162],[-0.108,0.364,-0.160]],
    // Upper-right corner curl
    [[0.106,0.420,-0.155],[0.134,0.400,-0.160],[0.132,0.372,-0.162],[0.108,0.364,-0.160]],
    // Lower-left corner curl
    [[-0.104,0.186,-0.155],[-0.130,0.160,-0.160],[-0.126,0.134,-0.162],[-0.102,0.130,-0.160]],
    // Lower-right corner curl
    [[0.104,0.186,-0.155],[0.130,0.160,-0.160],[0.126,0.134,-0.162],[0.102,0.130,-0.160]],
  ];
  for(const pts of arDefs){const geo=mkA(pts); if(geo) _cM(T,tr,geo,au,[0,0,0]);}
  // Small accent dots at key nodes
  for(const[px,py] of [[0,0.442],[0,0.252],[-0.084,0.238],[0.084,0.238],[0,0.150]])
    _cM(T,tr,new T.SphereGeometry(0.010,5,4),au,[px,py,-0.162]);

  // ── PAULDRONS — large, rounded (SphereGeometry hemisphere) ────────────────────
  for(const[sx,dRz] of [[-0.304,-0.10],[0.304,0.10]]){
    const pau=new T.Group(); tr.add(pau);
    pau.position.set(sx,0.346,0); pau.rotation.z=dRz;
    const dome=_cM(T,pau,new T.SphereGeometry(0.164,8,7,0,Math.PI*2,0,Math.PI*0.54),sv,[0,0,0]);
    dome.rotation.z=sx<0?Math.PI/2:-Math.PI/2;   // dome faces outward
    const pRg=_cM(T,pau,new T.TorusGeometry(0.164,0.016,6,18),au,[0,0,0]); pRg.rotation.x=Math.PI/2;
    _cM(T,pau,new T.BoxGeometry(0.278,0.016,0.188),au,[0,0.004,0]);
  }

  // ── CAPE — royal blue (#1a3a8f), CatmullRomCurve3 fold lines ─────────────────
  _cM(T,ac,new T.BoxGeometry(0.406,0.832,0.018),ry,[0,-0.068,0.174]);   // main panel
  _cM(T,ac,new T.BoxGeometry(0.414,0.060,0.028),ry,[0,0.378,0.152]);    // shoulder yoke
  _cM(T,ac,new T.BoxGeometry(0.412,0.012,0.022),au,[0,-0.482,0.174]);   // gold hem
  _cM(T,ac,new T.BoxGeometry(0.012,0.808,0.022),au,[-0.205,-0.068,0.174]); // gold border L
  _cM(T,ac,new T.BoxGeometry(0.012,0.808,0.022),au,[ 0.205,-0.068,0.174]); // gold border R
  // Fold lines (TubeGeometry + CatmullRomCurve3)
  const mkF=(pts)=>{try{const c=new T.CatmullRomCurve3(pts.map(([x,y,z])=>new T.Vector3(x,y,z)));return new T.TubeGeometry(c,14,0.005,5,false);}catch(e){return null;}};
  const fldDk={color:new T.Color(0x0e2872),roughness:0.98,metalness:0};
  const foldDefs=[
    [[-0.095,0.368,0.178],[-0.112,0.148,0.182],[-0.118,-0.082,0.180],[-0.106,-0.340,0.178],[-0.090,-0.478,0.177]],
    [[ 0.000,0.368,0.179],[ 0.016,0.136,0.183],[-0.014,-0.098,0.181],[ 0.010,-0.356,0.179],[0.000,-0.478,0.178]],
    [[ 0.095,0.368,0.178],[ 0.113,0.152,0.182],[ 0.116,-0.086,0.180],[ 0.104,-0.342,0.178],[0.088,-0.478,0.177]],
  ];
  for(const pts of foldDefs){const geo=mkF(pts); if(geo) _cM(T,ac,geo,fldDk,[0,0,0]);}

  lA.position.set(-0.306,0.234,0); lA.rotation.z=0.26; lA.rotation.x=-0.20; lA.rotation.y=0.22;
  _cM(T,lA,new T.CylinderGeometry(0.080,0.098,0.342,7),sv,[0,0.171,0]);  // upper arm
  _cM(T,lA,new T.BoxGeometry(0.110,0.086,0.122),sv,[0,0.380,0]);          // forearm plate
  // Shield group
  const shG=new T.Group(); shG.name='shield'; lA.add(shG);
  shG.position.set(0,0.448,-0.074); shG.rotation.x=0.18;
  // Shield body (rounded rectangular — BoxGeometry + corner spheres)
  _cM(T,shG,new T.BoxGeometry(0.278,0.374,0.038),sv,[0,0,0]);              // metal back
  _cM(T,shG,new T.BoxGeometry(0.258,0.354,0.028),ry,[0,0,-0.022]);         // blue face
  // Round corners (4 spheres)
  for(const[cx,cy] of [[-0.118,0.156],[0.118,0.156],[-0.118,-0.156],[0.118,-0.156]])
    _cM(T,shG,new T.SphereGeometry(0.050,6,5),ry,[cx,cy,-0.018]);
  // Rim (silver edge)
  for(const[bw,bh,bx,by] of [[0.290,0.012,0,0.188],[0.290,0.012,0,-0.188],[0.012,0.378,-0.149,0],[0.012,0.378,0.149,0]])
    _cM(T,shG,new T.BoxGeometry(bw,bh,0.010),sv,[bx,by,-0.006]);
  // Golden cross in relief (flared arms)
  _cM(T,shG,new T.BoxGeometry(0.030,0.278,0.010),au,[0,0,-0.030]);          // vertical
  _cM(T,shG,new T.BoxGeometry(0.218,0.030,0.010),au,[0,0.048,-0.030]);      // horizontal
  // Cross arm-end flourishes (diamond tips)
  for(const[cx,cy] of [[0,0.158],[0,-0.124],[0.118,0.048],[-0.118,0.048]]){
    const df=_cM(T,shG,new T.BoxGeometry(0.026,0.026,0.008),au,[cx,cy,-0.034]); df.rotation.z=Math.PI/4;
  }
  // Center boss
  _cM(T,shG,new T.SphereGeometry(0.022,6,5),au,[0,0.048,-0.038]);

  rA.position.set(0.302,0.234,0); rA.rotation.z=-0.18; rA.rotation.x=0.08;
  _cM(T,rA,new T.CylinderGeometry(0.080,0.098,0.342,7),sv,[0,0.171,0]);
  _cM(T,rA,new T.BoxGeometry(0.110,0.086,0.122),sv,[0,0.380,0]);
  _cM(T,rA,new T.SphereGeometry(0.050,6,5),sk,[0,0.426,0]);                 // hand
  const wp=new T.Group(); wp.name='weapon'; rA.add(wp);
  wp.position.set(0,0.466,0);
  // Blade (long, silver, with center ridge)
  _cM(T,wp,new T.BoxGeometry(0.023,0.876,0.010),sw,[0,0.438,0]);
  _cM(T,wp,new T.BoxGeometry(0.006,0.856,0.006),svH,[0,0.436,0]);           // ridge
  // Blade tip (tapered)
  const bTip=_cM(T,wp,new T.CylinderGeometry(0.001,0.013,0.066,4),sw,[0,0.900,0]); bTip.rotation.x=0;
  // Cruciform guard (gold)
  _cM(T,wp,new T.BoxGeometry(0.272,0.022,0.020),au,[0,0.064,0]);             // crossguard
  _cM(T,wp,new T.BoxGeometry(0.022,0.022,0.196),au,[0,0.064,0]);             // depth bar
  _cM(T,wp,new T.SphereGeometry(0.018,6,5),au,[-0.142,0.064,0]);             // guard tip L
  _cM(T,wp,new T.SphereGeometry(0.018,6,5),au,[ 0.142,0.064,0]);             // guard tip R
  // Grip (leather wrapped handle)
  _cM(T,wp,new T.CylinderGeometry(0.015,0.019,0.186,6),ltG,[0,-0.060,0]);
  for(let i=0;i<3;i++){const wb=_cM(T,wp,new T.TorusGeometry(0.020,0.006,5,10),_cLth(T,0x5a3010),[0,-0.018+i*-0.048,0]); wb.rotation.x=Math.PI/2;}
  // Pommel
  _cM(T,wp,new T.SphereGeometry(0.030,7,6),au,[0,-0.172,0]);

  _cM(T,hd,new T.SphereGeometry(0.168,10,9),sk,[0,0.466,0]);
  _cM(T,hd,new T.BoxGeometry(0.210,0.096,0.208),sk,[0,0.388,0]); // jaw
  _cM(T,hd,new T.BoxGeometry(0.178,0.064,0.194),sk,[0,0.316,0]); // firm chin
  // Determined eyes
  for(const ex of [-0.052,0.052]){
    _cM(T,hd,new T.SphereGeometry(0.021,5,4),{color:new T.Color(0x3a4870),roughness:0.5,metalness:0},[ex,0.478,-0.148]);
    _cM(T,hd,new T.SphereGeometry(0.011,4,3),{color:new T.Color(0xffffff),roughness:0.2,metalness:0},[ex+0.006,0.486,-0.156]);
    // Strong brow
    const bw=_cM(T,hd,new T.BoxGeometry(0.048,0.012,0.012),hC,[ex,0.492,-0.158]); bw.rotation.z=ex<0?-0.12:0.12;
  }
  _cM(T,hd,new T.SphereGeometry(0.020,6,5),sk,[0,0.454,-0.160]); // nose
  _cM(T,hd,new T.BoxGeometry(0.058,0.012,0.010),{color:new T.Color(0xb07848),roughness:0.90,metalness:0},[0,0.420,-0.162]); // mouth
  // Short brown hair
  const hcap=_cM(T,hr,new T.SphereGeometry(0.170,9,7,0,Math.PI*2,0,Math.PI*0.42),hC,[0,0.472,0]); hcap.rotation.x=0.04;
  _cM(T,hr,new T.BoxGeometry(0.124,0.112,0.020),hC,[-0.128,0.436,-0.046]);
  _cM(T,hr,new T.BoxGeometry(0.124,0.112,0.020),hC,[ 0.128,0.436,-0.046]);
  _cM(T,hr,new T.BoxGeometry(0.144,0.090,0.020),hC,[0,0.396,0.088]);
}

// ── HP final por herói (base + bônus de Constituição — valor definitivo nível 1) ──
// Espelha CLASSES["hp"] em server.py. Para alterar: edite AQUI e no server.py.
const HERO_HP_CONFIG = {
  victorCoiceBravo: { hp: 14 },   // d12(12) + CON14(+2)
  richardCavaleiro: { hp: 12 },   // d10(10) + CON14(+2)
  pedro:            { hp: 7  },   // d6(6)   + CON12(+1)
  luccas:           { hp: 9  },   // d8(8)   + CON12(+1)
  henrique:         { hp: 9  },   // d8(8)   + CON12(+1)
  lewis:            { hp: 10 },   // d8(8)   + CON14(+2)
};

// ── Dados completos dos heróis — fonte canônica client-side ──────────────────
// Espelha server.py CLASSES. Para alterar stats, edite AQUI e no CLASSES.
// statsModificados começa igual a stats; efeitos de itens/habilidades o alteram em runtime.
const HERO_DATA = {
  victorCoiceBravo: {
    name: 'Victor, o Coice Bravo',
    class: 'GUERREIRO ANÃO',
    portrait: 'assets/portraits/victor.jpeg',
    hp: 14,
    stats: { forca: 18, destreza: 10, inteligencia: 8,  constituicao: 14 },
    statsModificados: { forca: 18, destreza: 10, inteligencia: 8,  constituicao: 14 },
    efeitos: [],
  },
  richardCavaleiro: {
    name: 'Richard, o Cavaleiro',
    class: 'PALADINO',
    portrait: 'assets/portraits/richard.jpeg',
    hp: 12,
    stats: { forca: 16, destreza: 10, inteligencia: 10, constituicao: 14 },
    statsModificados: { forca: 16, destreza: 10, inteligencia: 10, constituicao: 14 },
    efeitos: [],
  },
  pedro: {
    name: 'Pedro',
    class: 'MAGO NEGRO',
    portrait: 'assets/portraits/pedro.jpeg',
    hp: 7,
    stats: { forca: 8,  destreza: 12, inteligencia: 18, constituicao: 12 },
    statsModificados: { forca: 8,  destreza: 12, inteligencia: 18, constituicao: 12 },
    efeitos: [],

    // HABILIDADE DE CLASSE — sempre disponível
    habilidadeClasse: {
      id:          'animar_mortos',
      nome:        'Animar Mortos',
      tipo:        'habilidade_classe',
      icone:       '💀',
      acao:        'principal',
      alcance:     'adjacente ao cadáver',
      custo:       { fome: 20, sede: 20 },
      descricao:   'Pedro concentra energia sombria sobre o cadáver de uma criatura derrotada, arrancando sua essência vital e aprisionando-a num corpo sem vida para servir eternamente.',

      // Calcula slots disponíveis (base + Nível III da Guilda "Reviver os Mortos")
      calcularSlots(nivelPedro, inteligencia) {
        const bonus = getBonusAtributo(inteligencia)
        const bonusNivel = Math.floor(nivelPedro / 2)
        const extra = (window.GS && GS.magoReviverSlotsExtra) ? GS.magoReviverSlotsExtra() : 0
        return Math.max(1, bonus + bonusNivel) + extra
      },

      // Chance de sucesso: tabela da Guilda (Nível I/II/III), só depende do ND
      calcularChance(nivelPedro, nivelMonstro) {
        return (window.GS && GS.magoReviverChance) ? GS.magoReviverChance(nivelMonstro) : Math.min(99, Math.max(1, Math.round(100 - nivelMonstro * 20)))
      },

      // Zona de resultado hostil: inalterada pelo Nível da Guilda (ver CLAUDE.md)
      calcularZonaHostil(nivelPedro, nivelMonstro) {
        const nivelMaxPedro = nivelPedro <= 2 ? 2 :
                              nivelPedro <= 4 ? 4 : 5
        const diferenca = nivelMonstro - nivelMaxPedro
        return diferenca > 0 ? diferenca * 10 : 0
      },

      // Slots que um monstro ocupa: 1 fixo no Nível I; ND real no II/III
      calcularSlotsOcupados(nivelMonstro) {
        return (window.GS && GS.magoReviverSlotCusto) ? GS.magoReviverSlotCusto(nivelMonstro) : 1
      },

      // Interpreta resultado do d100
      interpretarResultado(rolagem, chance, zonaHostil) {
        if (rolagem <= zonaHostil)  return 'hostil'
        if (rolagem <= chance)      return 'sucesso'
        return 'falha'
      }
    },

    // Estado dos animados — persiste entre aventuras
    animados: [],

    // Magias conhecidas — vazio = todas as magias da classe (grimório). A aba
    // MAGIAS usa renderMagiasFichaEmJogo (cartas do GRIMORIO_CLIENT) + mensagem WS
    // 'magia'. NÃO confundir com as skills legadas fireball/ice_lance/magic_shield.
    magiasConhecidas: [],

    // Usos de magia restantes hoje — reseta na taverna
    magiasUsadasHoje: {
      primeiro: 0,
      segundo:  0,
      terceiro: 0
    }
  },
  luccas: {
    name: 'Luccas',
    class: 'LADRÃO',
    portrait: 'assets/portraits/luccas.jpeg',
    hp: 9,
    stats: { forca: 10, destreza: 18, inteligencia: 10, constituicao: 12 },
    statsModificados: { forca: 10, destreza: 18, inteligencia: 10, constituicao: 12 },
    efeitos: [],
  },
  henrique: {
    name: 'Henrique',
    class: 'BARDO',
    portrait: 'assets/portraits/henrique.jpeg',
    hp: 9,
    stats: { forca: 10, destreza: 16, inteligencia: 12, constituicao: 12 },
    statsModificados: { forca: 10, destreza: 16, inteligencia: 12, constituicao: 12 },
    efeitos: [],
  },
  lewis: {
    name: 'Lewis',
    class: 'CLÉRIGO',
    portrait: 'assets/portraits/lewis.jpeg',
    hp: 10,
    stats: { forca: 10, destreza: 10, inteligencia: 16, constituicao: 14 },
    statsModificados: { forca: 10, destreza: 10, inteligencia: 16, constituicao: 14 },
    efeitos: [],
  },
};

// ── Bônus de Constituição — tabela expandida D20 (0–25) ──────────────────────
// Usado na ficha de seleção e em qualquer cálculo client-side de HP.
// Espelha get_bonus_constituicao() em server.py — manter sincronizados.
function getBonusConstituicao(constituicao) {
  const tabela = {
     0: -5,  1: -5,  2: -4,  3: -4,  4: -3,  5: -3,
     6: -2,  7: -2,  8: -1,  9: -1, 10:  0, 11:  0,
    12: +1, 13: +1, 14: +2, 15: +2, 16: +3, 17: +3,
    18: +4, 19: +4, 20: +5, 21: +5, 22: +6, 23: +6,
    24: +7, 25: +7,
  };
  const valorSeguro = Math.max(0, Math.min(25, constituicao));
  return tabela[valorSeguro];
}

// ── Bônus genérico de atributo — tabela D20 padrão (0–25) ────────────────────
// Modificador padrão floor((v-10)/2). Usado por habilidades que escalam com um
// atributo (ex.: Animar Mortos do Pedro usa Inteligência).
function getBonusAtributo(valor) {
  const valorSeguro = Math.max(0, Math.min(25, valor));
  return Math.floor((valorSeguro - 10) / 2);
}

// ── Vida máxima por herói/nível (usado na ficha de seleção do Pedro) ─────────
// HERO_HP_CONFIG[heroKey].hp é o HP FINAL de nível 1 (já inclui o bônus de CON,
// espelha server.py). A tela de seleção é sempre nível 1; para níveis acima,
// cada nível extra soma o bônus de Constituição (mín. +1), mantendo a fórmula
// previsível sem inventar balanceamento novo.
function calcularVidaMaxima(heroKey, nivel = 1, constituicao) {
  const base = (HERO_HP_CONFIG[heroKey] && HERO_HP_CONFIG[heroKey].hp)
            ?? (HERO_DATA[heroKey] && HERO_DATA[heroKey].hp)
            ?? 10;
  const con = (typeof constituicao === 'number')
            ? constituicao
            : (HERO_DATA[heroKey]?.statsModificados?.constituicao
               ?? HERO_DATA[heroKey]?.stats?.constituicao
               ?? 10);
  const bonusCon = Math.max(1, getBonusConstituicao(con));
  return base + Math.max(0, (nivel || 1) - 1) * bonusCon;
}

// ■  FULL-SCREEN CLASS SELECT  (csf)
//    Hades / Darkest Dungeon-style dramatic hero selection.
//    Completely independent from g3 (dungeon renderer).

let csf = null; // full class-select state handle

const _CSD = {
  warrior:{ name:'VICTOR COICE BRAVO', cls:'VICTOR', skyHex:'#1a0800', lightHex:0xff4400,
    portrait:'assets/portraits/victor.jpeg',   // foto de referência (salvar o arquivo aqui)
    hp:14, stats:{forca:18,destreza:10,inteligencia:8,constituicao:14},
    desc:'Tanque de aço e sangue. Absorve golpes devastadores, afasta inimigos e nunca recua diante do perigo.',
    skills:[
      // Custos espelham CLASSES["warrior"]["skills"] em server.py (autoritativo).
      {icon:'⚔️',name:'Mira Certeira',
       desc:'Ativa +2 no acerto neste turno. Pode combinar com outras habilidades no mesmo turno.',
       fome_cost:0, sede_cost:2},
      {icon:'💥',name:'Golpe Devastador',
       desc:'Dobra cada dado de dano neste turno. O bônus de Força não é dobrado.',
       fome_cost:2, sede_cost:4},
      {icon:'🔥',name:'Fúria Berserker',
       desc:'Concede um ataque extra (2º ataque manual) neste turno.',
       fome_cost:5, sede_cost:5},
    ]},
  mage:{ name:'PEDRO, O TÍMIDO', cls:'PEDRO', skyHex:'#0a0020', lightHex:0x8833ff,
    portrait:'assets/portraits/pedro.jpeg',
    hp:7, stats:{forca:8,destreza:12,inteligencia:18,constituicao:12},
    desc:'Domina os arcanos proibidos. Devasta grupos de inimigos com magia de área letal.',
    skills:[
      { nome: 'Animar Mortos',    icone: '💀', desc: 'Habilidade de Classe — anima cadáveres como servos eternos' },
      { nome: 'Mísseis Mágicos',  icone: '✨', desc: '1º Círculo — 3 projéteis de 1d4+INT, acerto automático' },
      { nome: 'Raio de Gelo',     icone: '❄️', desc: '1º Círculo — 1d6+INT, alvo lento por 2 turnos' },
      { nome: 'Toque Sombrio',    icone: '🖤', desc: '1º Círculo — 1d8+INT de dano sombrio, adjacente' },
      { nome: 'Escudo Arcano',    icone: '🔮', desc: '1º Círculo — +3 CA por 3 turnos' },
      { nome: 'Bola de Fogo',     icone: '🔥', desc: '2º Círculo — 3d6 fogo em área 2 quadrados' },
      { nome: 'Drenar Vida',      icone: '🩸', desc: '2º Círculo — 2d6+INT, recupera metade como vida' },
      { nome: 'Névoa Venenosa',   icone: '☠️', desc: '2º Círculo — área 2 quad, -2 testes, 3 turnos' },
      { nome: 'Raio da Morte',    icone: '💜', desc: '3º Círculo — 5d6+INT em linha reta' },
      { nome: 'Controlar Mente',  icone: '🧠', desc: '3º Círculo — inimigo luta pelo grupo por 3 turnos' },
    ]},
  rogue:{ name:'LUCCAS, O ASTUTO', cls:'LUCCAS', skyHex:'#040800', lightHex:0x44cc44,
    portrait:'assets/portraits/luccas.jpeg',
    hp:9, stats:{forca:10,destreza:18,inteligencia:10,constituicao:12},
    desc:'Morte silenciosa nas sombras. Dano crítico devastador e mobilidade inigualável.',
    skills:[
      // Custos espelham CLASSES["rogue"]["skills"] em server.py (autoritativo).
      {icon:'🗡️',name:'Ataque Furtivo',
       desc:'Passiva. +2d4 de dano extra quando há aliado adjacente ao alvo (ou se estiver invisível). +1d4 por faixa de nível.',
       fome_cost:0, sede_cost:0},
      {icon:'🔍',name:'Detectar Armadilhas',
       desc:'Ação bônus (alternável). Revela armadilhas próximas e não dispara as da masmorra. Manutenção 💧-1/turno.',
       fome_cost:0, sede_cost:1},
      {icon:'🌑',name:'Esconder nas Sombras',
       desc:'Ação bônus. d20+DES vs percepção dos monstros. Invisível (não é alvo) até atacar — mover-se NÃO revela. Manutenção 🍖-1 💧-1/turno.',
       fome_cost:2, sede_cost:1},
      {icon:'☠️',name:'Veneno Rápido',
       desc:'Ação livre. Unta um veneno da bolsa na arma — os próximos golpes certeiros envenenam.',
       fome_cost:0, sede_cost:1},
      {icon:'🪤',name:'Criar Armadilha',
       desc:'Ação principal. 8 tipos de armadilha na casa/adjacente. 🍖-2 💧-1 + custo em ouro.',
       fome_cost:2, sede_cost:1},
    ]},
  cleric:{ name:'FRADE LEWIS', cls:'FRADE LEWIS', skyHex:'#140c00', lightHex:0xffdd44,
    portrait:'assets/portraits/lewis.jpeg',
    hp:10, stats:{forca:10,destreza:10,inteligencia:16,constituicao:14},
    desc:'Frade que canaliza milagres. Cura, purifica e ressuscita aliados. Não usa mana — seus milagres custam fome/sede.',
    skills:[
      {icon:'🙌',name:'Cura',
       desc:'Ação principal. 1d8 a 3d8 + INT em um aliado. Alcance estendível com fome.',
       fome_cost:0, sede_cost:1},
      {icon:'🌟',name:'Cura em Área',
       desc:'Ação principal. 1d8 a 3d8 + INT em todos os aliados no raio 5.',
       fome_cost:4, sede_cost:4},
      {icon:'✨',name:'Purificação',
       desc:'Ação principal. Remove veneno, doença, maldição ou petrificação de um aliado adjacente.',
       fome_cost:1, sede_cost:0},
      {icon:'💫',name:'Ressurreição',
       desc:'Ação principal. Traz um aliado morto adjacente de volta com 1 HP.',
       fome_cost:10, sede_cost:10},
    ]},
  bard:{ name:'HENRIQUE, O BARDO', cls:'HENRIQUE', skyHex:'#0a0005', lightHex:0xff66cc,
    portrait:'assets/portraits/henrique.jpeg',
    hp:9, stats:{forca:10,destreza:16,inteligencia:12,constituicao:12},
    desc:'Alma da taverna, terror do calabouço. Inspira aliados com canções e provoca inimigos. Não usa mana — suas habilidades custam fome/sede.',
    skills:[
      {icon:'📖',name:'Conhecimento das Lendas',
       desc:'Passiva — sempre ativa. Revela CA, HP exato, dano, nível e tesouro de qualquer inimigo ao passar o mouse.',
       fome_cost:0, sede_cost:0},
      {icon:'🎵',name:'Canção Heroica',
       desc:'Ação principal. +1 nos atributos escolhidos para aliados no raio de 5 quadrados. Custo variável por turno.',
       fome_cost:0, sede_cost:0},
      {icon:'😤',name:'Provocação',
       desc:'Ação bônus. Impõe desvantagem ao inimigo e o força a atacar Henrique por 3 turnos.',
       fome_cost:3, sede_cost:3},
    ]},
  paladin:{ name:'RICHARD, O CAVALEIRO', cls:'RICHARD', skyHex:'#0e0a00', lightHex:0xeeeeff,
    portrait:'assets/portraits/richard.jpeg',
    hp:12, stats:{forca:16,destreza:10,inteligencia:10,constituicao:14},
    desc:'Aço e honra forjados na mesma bigorna. Richard não conhece recuo — apenas o peso do escudo e a clareza do dever. Não usa mana — suas habilidades custam fome/sede.',
    skills:[
      {icon:'💡',name:'Guerreiro da Luz',
       desc:'Ação Livre. +1 ou +2 em Visão, Ataque, Dano e CA. Bônus fixos até desativar. Custo variável por turno.',
       fome_cost:0, sede_cost:0},
      {icon:'✨',name:'Regeneração Divina',
       desc:'Ação Livre. Recupera 1 HP por turno. Desativa ao atingir HP máximo. Ativar 🍖-2 💧-1; manutenção 🍖-1 💧-1.',
       fome_cost:2, sede_cost:1},
      {icon:'⚔️',name:'Golpe Sagrado',
       desc:'Ação Bônus. +1d8 dano sagrado por ataque. Dobrado contra mortos-vivos e demônios. 🍖-3 💧-3.',
       fome_cost:3, sede_cost:3},
      {icon:'🛡️',name:'Protetor',
       desc:'Ação Bônus. Aliado escolhido (raio 4) recebe metade do dano; a outra metade vai para Richard. 🍖-2 💧-2.',
       fome_cost:2, sede_cost:2},
      {icon:'🙏',name:'Imposição das Mãos',
       desc:'Ação Principal. Cura 1d6 + bônus de Força em aliado adjacente. Não funciona em si mesmo. 🍖-3 💧-2.',
       fome_cost:3, sede_cost:2},
    ]},
};

// ── Fixed pedestal positions (slot 2 = spotlight CENTER) ─────────────────────
const _CSF_SLOT_POS = [
  {x:-2.95, z:1.0},   // 0 — far-left
  {x:-1.78, z:0.4},   // 1 — mid-left
  {x:-0.55, z:-0.2},  // 2 — CENTER (spotlight, slightly closer to camera)
  {x: 0.80, z:0.4},   // 3 — mid-right
  {x: 1.95, z:0.9},   // 4 — right
  {x: 3.05, z:1.3},   // 5 — far-right (Richard) — compactado p/ caber na área visível
];
const _CSF_CENTER_SLOT = 2;
// Initial hero → slot mapping (slot 2 = warrior = default selection)
const _CSF_INIT_ORDER = ['mage','rogue','warrior','cleric','bard','paladin'];

function initClassSelectFull(){
  if(csf) return;
  if(!window.THREE) return;
  const T = window.THREE;

  const canvas = document.getElementById('cs-canvas');
  if(!canvas) return;
  const W = canvas.offsetWidth  || window.innerWidth;
  const H = canvas.offsetHeight || window.innerHeight;

  // Renderer (canvas ocupa a tela inteira; a câmera é deslocada para enquadrar
  // os peões só na faixa visível à esquerda do painel)
  const renderer = new T.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(W, H);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type    = T.PCFShadowMap   /* PCF simples: ~igual visualmente, bem mais barato que PCFSoft */;
  renderer.toneMapping       = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.4;

  // Scene
  const scene = new T.Scene();
  scene.background = new T.Color(0x0e0a00);
  scene.fog = new T.FogExp2(0x000000, 0.011);

  // Câmera ortográfica deslocada — enquadra os 6 heróis na faixa VISÍVEL (esquerda).
  // O painel direito cobre min(340px,36vw); a câmera descon­ta essa faixa.
  const aspect    = W / H;
  const panelPx   = Math.min(340, 0.36 * W);
  const visFrac   = Math.max(0.40, (W - panelPx) / W);  // fração visível (à esquerda)
  const PAWN_HALF = 3.75;   // meia-largura do conjunto de peões (±3.05 + margem p/ não cortar)
  const PAWN_MIDX = 0.05;   // centro X do conjunto de slots
  // camRight tal que a meia-largura dos peões caiba na metade da faixa visível
  const camRight  = PAWN_HALF / visFrac;
  const fH        = camRight / aspect;
  // lookX desloca o centro dos peões para o centro da faixa visível
  const lookX     = PAWN_MIDX + (1 - visFrac) * camRight;
  const cam = new T.OrthographicCamera(-camRight, camRight, fH, -fH, -30, 30);
  cam.position.set(lookX, 4.2, 9.0);
  cam.lookAt(lookX, 0.7, 0);
  cam.updateProjectionMatrix();

  // Iluminação de ESTÚDIO DE MINIATURAS — clara e definida, realça o plástico satinado
  // Ambient quente suave para que TODOS os 6 peões fiquem visíveis (não só o selecionado)
  scene.add(new T.AmbientLight(0xfff2e6, 0.62));
  // Hemisphere: céu quente / chão escuro — dá gradiente natural de cima p/ baixo
  scene.add(new T.HemisphereLight(0xfff0dc, 0x241810, 0.55));
  // KEY light forte do alto-frente-esquerda (define forma e brilho satinado)
  const key = new T.DirectionalLight(0xffffff, 1.25);
  key.position.set(-3, 6, 5);
  key.castShadow = true;
  key.shadow.mapSize.width = key.shadow.mapSize.height = 2048;
  key.shadow.camera.left = -8; key.shadow.camera.right = 8;
  key.shadow.camera.top = 6;   key.shadow.camera.bottom = -2;
  key.shadow.bias = -0.0004;
  scene.add(key);
  // FILL frio da direita (suaviza as sombras, dá volume)
  const fill = new T.DirectionalLight(0x9fc0ff, 0.42);
  fill.position.set(4, 3, 2); scene.add(fill);
  // RIM/back quente atrás (recorte de borda — separa do fundo)
  const rim = new T.DirectionalLight(0xffd2a0, 0.55);
  rim.position.set(0, 2.5, -5); scene.add(rim);

  // SpotLight — realce extra sobre o herói selecionado (aditivo)
  const spot = new T.SpotLight(0xfff8ee, 1.4, 12, Math.PI/4.2, 0.35, 1.0);
  spot.position.set(-0.6, 5.5, 2.5); spot.castShadow = false; scene.add(spot);
  const spotTarget = new T.Object3D(); spotTarget.position.set(-0.6, 0.8, 0); scene.add(spotTarget);
  spot.target = spotTarget;

  // PointLight colorido aos pés do herói selecionado (acento da cor da classe)
  const heroLight = new T.PointLight(0xff4400, 0.7, 4.0);
  heroLight.position.set(-0.6, 0.4, 0); scene.add(heroLight);

  // Ground
  const gnd = new T.Mesh(
    new T.PlaneGeometry(28, 16),
    new T.MeshStandardMaterial({color:0x050306, roughness:0.99, metalness:0.0})
  );
  gnd.rotation.x = -Math.PI/2; gnd.position.y = -0.005;
  gnd.receiveShadow = true; scene.add(gnd);

  // Build heroes in their initial slots
  const slotHeroes = [..._CSF_INIT_ORDER]; // slotHeroes[slotIdx] = classId
  const heroGroups = {};                   // classId → Three.Group (pedestal+hero)

  for(let i = 0; i < _CS_IDS.length; i++){
    const id      = _CS_IDS[i];
    const slotIdx = slotHeroes.indexOf(id);
    const sp      = _CSF_SLOT_POS[slotIdx];

    // _cHero já tem try/catch interno; esta camada garante que nenhum herói
    // trave a inicialização dos outros.
    let hg;
    try { hg = _cHero(T, id, i); }
    catch(e){
      console.error('[initClassSelectFull] Erro construindo slot "'+id+'":', e);
      hg = new T.Group(); // grupo vazio — pedestal aparece sem peão
    }
    hg.position.set(0, 0, 0);
    const pg = new T.Group();
    pg.userData.classId = id;
    pg.userData.slotIdx = slotIdx;
    _buildCsfPillar(T, pg, slotIdx === _CSF_CENTER_SLOT);
    pg.add(hg);
    pg.position.set(sp.x, 0, sp.z);
    pg.scale.setScalar(slotIdx === _CSF_CENTER_SLOT ? 0.86 : 0.64); // reduzidos p/ caber na área visível
    scene.add(pg);
    heroGroups[id] = pg;
  }

  // Particle ring
  const particles = _buildCsfParticles(T);
  scene.add(particles.group);

  // Sky color lookup
  const skyColors = {};
  for(const [id, d] of Object.entries(_CSD))
    skyColors[id] = new T.Color(d.skyHex);

  const defaultSel = slotHeroes[_CSF_CENTER_SLOT]; // 'warrior'

  csf = {
    T, scene, renderer, cam,
    heroGroups, slotHeroes,
    spot, spotTarget, heroLight,
    particles, skyColors,
    selectedId:   defaultSel,
    hoveredId:    null,
    takenIds:     new Set(),   // classes já escolhidas por OUTROS jogadores (indisponíveis)
    animFrame:    null,
    tweens:       [],
    confirmStart: Date.now(),
    confirmShown: false,
    raycaster:    new T.Raycaster(),
  };

  renderer.domElement.addEventListener('mousemove',  _csfMouseMove);
  renderer.domElement.addEventListener('click',      _csfClick);
  renderer.domElement.addEventListener('mouseleave', _csfMouseLeave);
  // Celular: tocar no modelo 3D seleciona o herói direto (raycast no toque).
  // preventDefault evita o `click` sintético duplicado logo após o touchend.
  renderer.domElement.addEventListener('touchend',   _csfTouchEnd, { passive:false });

  _startCsfLoop();
  _csfShowPanel(defaultSel, false);
  document.getElementById('cs-hint').textContent = 'Escolha seu herói — toque para selecionar';
  toggleCsInfo(false);   // celular: aba de características começa fechada
}

function _buildCsfPillar(T, parent, isCenter){
  const h  = isCenter ? 0.22 : 0.18;
  const r  = isCenter ? 0.52 : 0.44;
  // Madeira escura — combina com a base dos peões (pedido: sem tom cinza)
  const stone = new T.MeshStandardMaterial({color:new T.Color(0x2b1809), roughness:0.86, metalness:0.02});
  const capM  = new T.MeshStandardMaterial({map:_getWoodTopTex(T), color:new T.Color(0x9a7a55), roughness:0.78, metalness:0.02});
  // Base column
  const col = new T.Mesh(new T.CylinderGeometry(r, r*1.08, h, 8), stone);
  col.position.y = h * 0.5 - 0.005; col.receiveShadow = true; parent.add(col);
  // Cap ring
  const cap = new T.Mesh(new T.CylinderGeometry(r*1.06, r*1.06, 0.035, 8), capM);
  cap.position.y = h - 0.005; parent.add(cap);
  // Base ring
  const base = new T.Mesh(new T.CylinderGeometry(r*1.12, r*1.18, 0.03, 8), stone);
  base.position.y = 0.015; parent.add(base);
}

function _buildCsfParticles(T){
  const count = 30;
  const group = new T.Group();
  const meshes = [], mats = [], data = [];
  for(let i = 0; i < count; i++){
    const r  = 0.62 + Math.random() * 0.44;
    const h  = 0.08 + Math.random() * 0.82;
    const sp = 0.35 + Math.random() * 0.75;
    const ph = (i / count) * Math.PI * 2;
    const sz = 0.028 + Math.random() * 0.032;
    const mat = new T.MeshStandardMaterial({
      color:0xffd080, emissive:new T.Color(0xffaa22),
      emissiveIntensity:1.1, roughness:0.5, metalness:0.3
    });
    const mesh = new T.Mesh(new T.SphereGeometry(sz, 4, 4), mat);
    mesh.castShadow = false;
    group.add(mesh);
    meshes.push(mesh); mats.push(mat); data.push({r, h, sp, ph});
  }
  return {group, meshes, mats, data};
}

function _startCsfLoop(){
  let _last = Date.now();
  function tick(){
    if(!csf){ return; }
    csf.animFrame = requestAnimationFrame(tick);
    const now = Date.now();
    const dt  = Math.min((now - _last) * 0.001, 0.05);
    _last = now;
    const t   = now * 0.001;

    const {T, scene, renderer, cam,
           heroGroups, slotHeroes, tweens,
           spot, spotTarget, heroLight, particles, skyColors} = csf;

    // ── Process position tweens (swap animation)
    for(let i = tweens.length - 1; i >= 0; i--){
      const tw = tweens[i];
      tw.elapsed = (tw.elapsed || 0) + dt;
      const p  = Math.min(tw.elapsed / tw.duration, 1.0);
      const e  = p < 0.5 ? 2*p*p : -1+(4-2*p)*p; // easeInOut
      tw.obj.position.x = tw.sx + (tw.tx - tw.sx) * e;
      tw.obj.position.z = tw.sz + (tw.tz - tw.sz) * e;
      tw.obj.scale.setScalar(tw.ss + (tw.ts - tw.ss) * e);
      if(p >= 1.0) tweens.splice(i, 1);
    }

    // ── Hero Y-lift and idle scale
    for(const [id, pg] of Object.entries(heroGroups)){
      const isSel = id === csf.selectedId;
      const isHov = id === csf.hoveredId;
      const targetY = isSel ? 0.09 : (isHov ? 0.055 : 0);
      pg.position.y += (targetY - pg.position.y) * 0.12;
      // Scale (lerp only when not tweening)
      if(!tweens.some(tw => tw.obj === pg)){
        const slotIdx  = slotHeroes.indexOf(id);
        const targetS  = (slotIdx === _CSF_CENTER_SLOT) ? 0.86 : 0.64;
        const curS     = pg.scale.x;
        if(Math.abs(curS - targetS) > 0.001)
          pg.scale.setScalar(curS + (targetS - curS) * 0.10);
      }
      // Slow rotation for selected hero
      if(isSel){
        const hg = pg.children.find(c => c.userData.classId);
        if(hg) hg.rotation.y += 0.006 * dt * 60;
      }
    }

    // ── Move spotlight & hero light toward selected hero
    const selPg = heroGroups[csf.selectedId];
    if(selPg){
      const tx = selPg.position.x, tz = selPg.position.z;
      spot.position.x     += (tx + 0.4 - spot.position.x)     * 0.07;
      spotTarget.position.x += (tx - spotTarget.position.x)   * 0.09;
      spotTarget.position.z += (tz - spotTarget.position.z)   * 0.09;
      heroLight.position.x  += (tx - heroLight.position.x)    * 0.09;
      heroLight.position.z  += (tz - heroLight.position.z)    * 0.09;
      const lc = new T.Color(_CSD[csf.selectedId]?.lightHex ?? 0xffd080);
      heroLight.color.lerp(lc, 0.04);
    }

    // ── Sky lerp
    const targetSky = skyColors[csf.selectedId] || new T.Color(0x0e0a00);
    scene.background.lerp(targetSky, 0.025);

    // ── Particle orbit around selected hero
    const bx = selPg ? selPg.position.x : 0;
    const bz = selPg ? selPg.position.z : 0;
    const by = selPg ? selPg.position.y : 0;
    const pColor = new T.Color(_CSD[csf.selectedId]?.lightHex ?? 0xffaa22);
    for(let i = 0; i < particles.meshes.length; i++){
      const d     = particles.data[i];
      const angle = d.ph + t * d.sp;
      particles.meshes[i].position.set(
        bx + Math.cos(angle) * d.r,
        by + d.h,
        bz + Math.sin(angle) * d.r * 0.55
      );
      const pulse = 0.7 + 0.3 * Math.sin(t * 2.8 + d.ph);
      particles.mats[i].emissiveIntensity = pulse;
      particles.mats[i].color.lerp(pColor, 0.04);
      particles.mats[i].emissive.lerp(pColor, 0.04);
    }

    // ── Confirm timer
    if(!csf.confirmShown){
      const elapsed = now - csf.confirmStart;
      const pct     = Math.min(elapsed / 3000, 1) * 100;
      const fillEl  = document.getElementById('cs-progress-fill');
      if(fillEl) fillEl.style.width = pct + '%';
      if(elapsed >= 3000){
        csf.confirmShown = true;
        const btn = document.getElementById('cs-btn-confirm');
        if(btn) btn.style.display = 'block';
        if(fillEl) fillEl.style.width = '100%';
      }
    }

    renderer.render(scene, cam);
  }
  tick();
}

function _csfPick(e){
  if(!csf) return null;
  const {raycaster, cam, heroGroups, renderer} = csf;
  const T  = csf.T;
  const rc = renderer.domElement.getBoundingClientRect();
  const mx = ((e.clientX - rc.left) / rc.width)  *  2 - 1;
  const my = ((e.clientY - rc.top)  / rc.height) * -2 + 1;
  raycaster.setFromCamera(new T.Vector2(mx, my), cam);
  const hits = raycaster.intersectObjects(Object.values(heroGroups), true);
  if(!hits.length) return null;
  let obj = hits[0].object;
  while(obj.parent && obj.parent !== csf.scene) obj = obj.parent;
  return obj.userData.classId ?? null;
}
function _csfMouseMove(e){
  if(!csf) return;
  csf.hoveredId = _csfPick(e);
  csf.renderer.domElement.style.cursor =
    csf.hoveredId ? (csf.takenIds && csf.takenIds.has(csf.hoveredId) ? 'not-allowed' : 'pointer') : 'default';
}
function _csfClick(e){
  if(!csf) return;
  const id = _csfPick(e);
  if(id) csfSelectHero(id);
}
function _csfTouchEnd(e){
  if(!csf || !e.changedTouches || !e.changedTouches.length) return;
  const t  = e.changedTouches[0];
  const id = _csfPick({ clientX:t.clientX, clientY:t.clientY });
  if(id){ e.preventDefault(); csfSelectHero(id); }
}
function _csfMouseLeave(){ if(csf) csf.hoveredId = null; }

// Celular: abre/fecha a aba de características (gaveta inferior). Sem arg → alterna.
function toggleCsInfo(show){
  const panel = document.getElementById('cs-panel');
  const back  = document.getElementById('cs-info-backdrop');
  if(!panel) return;
  const open = (show === undefined) ? !panel.classList.contains('cs-open') : !!show;
  panel.classList.toggle('cs-open', open);
  if(back) back.classList.toggle('open', open);
}
window.toggleCsInfo = toggleCsInfo;

function csfSelectHero(classId){
  if(!csf || classId === csf.selectedId) return;
  if(csf.takenIds && csf.takenIds.has(classId)){
    toast('Personagem já escolhido por outro jogador.', 'var(--orange)');
    return;
  }
  const {slotHeroes, heroGroups, tweens} = csf;

  const newSlot = slotHeroes.indexOf(classId);
  const cenHero = slotHeroes[_CSF_CENTER_SLOT];

  if(newSlot !== _CSF_CENTER_SLOT){
    const newPg  = heroGroups[classId];
    const cenPg  = heroGroups[cenHero];
    const cenPos = _CSF_SLOT_POS[_CSF_CENTER_SLOT];
    const newPos = _CSF_SLOT_POS[newSlot];
    // Remove existing tweens on these objects
    for(let i = tweens.length - 1; i >= 0; i--)
      if(tweens[i].obj === newPg || tweens[i].obj === cenPg) tweens.splice(i, 1);
    // Swap tweens
    tweens.push({
      obj:newPg, duration:0.4, elapsed:0,
      sx:newPg.position.x, sz:newPg.position.z, ss:newPg.scale.x,
      tx:cenPos.x, tz:cenPos.z, ts:1.0
    });
    tweens.push({
      obj:cenPg, duration:0.4, elapsed:0,
      sx:cenPg.position.x, sz:cenPg.position.z, ss:cenPg.scale.x,
      tx:newPos.x, tz:newPos.z, ts:0.75
    });
    // Update data
    slotHeroes[_CSF_CENTER_SLOT] = classId;
    slotHeroes[newSlot]          = cenHero;
    heroGroups[classId].userData.slotIdx = _CSF_CENTER_SLOT;
    heroGroups[cenHero].userData.slotIdx = newSlot;
    // Light flash
    csf.heroLight.intensity = 2.8;
    setTimeout(()=>{ if(csf) csf.heroLight.intensity = 0.9; }, 180);
  }

  csf.selectedId = classId;

  // Reset confirm timer
  csf.confirmStart  = Date.now();
  csf.confirmShown  = false;
  const btn = document.getElementById('cs-btn-confirm');
  if(btn) btn.style.display = 'none';
  const fill = document.getElementById('cs-progress-fill');
  if(fill) fill.style.width = '0%';

  // Crossfade right panel
  const pane = document.getElementById('cs-pane-inner');
  if(pane){
    pane.classList.add('fade');
    setTimeout(()=>{ _csfShowPanel(classId, true); if(pane) pane.classList.remove('fade'); }, 230);
  } else {
    _csfShowPanel(classId, false);
  }
}

function _csfShowPanel(classId, animate){
  const d = _CSD[classId];
  if(!d) return;
  document.getElementById('cs-hero-name').textContent = d.name;
  document.getElementById('cs-hero-cls').textContent  = d.cls;
  document.getElementById('cs-desc').textContent      = d.desc;

  // ── Pontos de Vida na ficha de seleção ──────────────────────────────────────
  const hpEl = document.getElementById('cs-hp');
  if(hpEl){
    hpEl.innerHTML = `
      <div style="
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 6px 0 10px 0;
        padding: 6px 10px;
        background: rgba(180,30,30,0.13);
        border: 1px solid rgba(180,30,30,0.35);
      ">
        <span style="font-size:14px;">❤️</span>
        <span style="
          color: #8a7a5a;
          font-size: 11px;
          letter-spacing: 2px;
          text-transform: uppercase;
        ">Pontos de Vida</span>
        <span style="
          margin-left: auto;
          color: #e05050;
          font-size: 16px;
          font-weight: bold;
          letter-spacing: 1px;
        ">${d.hp}</span>
      </div>
    `;
  }

  // ── Portrait photo (shown only if the class defines a portrait path) ────────
  const frame = document.getElementById('cs-portrait-frame');
  const img   = document.getElementById('cs-portrait-img');
  if(frame && img){
    if(d.portrait){
      img.src = d.portrait;
      frame.classList.add('has-portrait');
      // Fade in on successful load; silently hide on error (file not saved yet)
      img.onload  = () => { frame.style.opacity = '1'; };
      img.onerror = () => { frame.classList.remove('has-portrait'); };
      frame.style.transition = 'opacity 0.4s ease';
      frame.style.opacity = '0';
      requestAnimationFrame(() => { frame.style.opacity = '1'; });
    } else {
      frame.classList.remove('has-portrait');
      img.src = '';
    }
  }

  // Renderizar apenas os 4 atributos oficiais: Força, Destreza, Inteligência, Constituição
  const ATRIBUTOS = [
    { key: 'forca',        label: 'Força' },
    { key: 'destreza',     label: 'Destreza' },
    { key: 'inteligencia', label: 'Inteligência' },
    { key: 'constituicao', label: 'Constituição' }
  ];

  function renderStats(stats) {
    return ATRIBUTOS.map(attr => `
      <div style="width:100%; margin-bottom:8px;">
        <div style="
          display: flex;
          justify-content: space-between;
          color: #8a7a5a;
          font-size: 11px;
          letter-spacing: 2px;
          margin-bottom: 3px;
        ">
          <span>${attr.label}</span>
          <span>${stats[attr.key] || 0}</span>
        </div>
        <div style="
          width: 100%;
          height: 6px;
          background: #1a1a1a;
          border: 1px solid #3a3a3a;
        ">
          <div style="
            width: ${((stats[attr.key] || 0) / 25) * 100}%;
            height: 100%;
            background: #c8a951;
            transition: width 0.4s ease;
          " class="cs-stat-bar" data-attr="${attr.key}"></div>
        </div>
      </div>
    `).join('');
  }

  document.getElementById('cs-stats').innerHTML = renderStats(d.stats);

  // Animate stat bars (escala 1–25, mapeada para 0–100%)
  requestAnimationFrame(()=>{
    ATRIBUTOS.forEach((attr)=>{
      const b=document.querySelector(`.cs-stat-bar[data-attr="${attr.key}"]`);
      if(b) b.style.width=((d.stats[attr.key] || 0) / 25) * 100 + '%';
    });
  });

  document.getElementById('cs-skills').innerHTML = d.skills.map(sk => `
    <div class="cs-skill">
      <span class="cs-skill-icon">${sk.icon ?? sk.icone ?? ''}</span>
      <div class="cs-skill-body">
        <div class="cs-skill-name">${sk.name ?? sk.nome ?? ''}</div>
        <div class="cs-skill-desc">${sk.desc ?? ''}</div>
        ${(sk.fome_cost || sk.sede_cost) ? `
          <div class="cs-skill-cost" style="
            margin-top:4px;
            font-size:10px;
            color:#ff851b;
            font-family:'Cinzel',serif;
            letter-spacing:1px;
          ">
            ${sk.fome_cost ? `🍖 -${sk.fome_cost}` : ''}
            ${sk.sede_cost ? `💧 -${sk.sede_cost}` : ''}
          </div>
        ` : sk.mp ? `
          <div class="cs-skill-cost" style="
            margin-top:4px;
            font-size:10px;
            color:#4488ff;
            font-family:'Cinzel',serif;
          ">💙 ${sk.mp} mana</div>
        ` : ''}
      </div>
    </div>
  `).join('');

  // ── Pedro: injeta o sistema novo de ficha (abas Atributos/Magias) (PASSO B) ──
  // Substitui o conteúdo de #cs-skills pelas abas; para outros heróis, remove
  // qualquer resíduo de uma seleção anterior do Pedro.
  const heroiKey = _classIdParaHeroiKey(classId);
  if (heroiKey === 'pedro') {
    _injetarFichaPedro();
  } else {
    const abaExistente = document.getElementById('abas-ficha-pedro');
    if (abaExistente) abaExistente.remove();
  }

  const panel = document.getElementById('cs-panel');
  if(panel) panel.classList.add('ready');
}

// Mapeia o classId do _CSD para a heroiKey usada em HERO_DATA/GS.HERO_DATA.
function _classIdParaHeroiKey(classId) {
  const mapa = {
    'mage':    'pedro',
    'cleric':  'lewis',
    'warrior': 'victorCoiceBravo',
    'paladin': 'richardCavaleiro',
    'rogue':   'luccas',
    'bard':    'henrique'
  };
  return mapa[classId] || classId;
}

// Injeta as abas Atributos/Magias do Pedro dentro do container de skills da ficha.
function _injetarFichaPedro() {
  // Registro COMPLETO primeiro (tem stats/statsModificados + habilidadeClasse);
  // GS.HERO_DATA.pedro é fallback (modelo de equipamento, sem stats).
  const heroi = HERO_DATA?.pedro || GS.HERO_DATA?.pedro;
  if (!heroi) return;

  const skillsContainer = document.getElementById('cs-skills');
  if (!skillsContainer) return;

  skillsContainer.innerHTML = '';

  const fichaContainer = document.createElement('div');
  fichaContainer.id = 'abas-ficha-pedro';
  fichaContainer.innerHTML = `
    <!-- ABAS -->
    <div style="
      display:flex;
      border-bottom:1px solid #c8a95133;
      margin-bottom:16px;
    ">
      <button
        onclick="trocarAbaFicha('atributos','pedro')"
        id="aba-atributos"
        style="
          flex:1; padding:8px; background:transparent;
          border:none; border-bottom:2px solid #c8a951;
          color:#c8a951; font-family:'Cinzel',serif;
          font-size:10px; letter-spacing:2px; cursor:pointer;
        "
      >📊 ATRIBUTOS</button>
      <button
        onclick="trocarAbaFicha('magias','pedro')"
        id="aba-magias"
        style="
          flex:1; padding:8px; background:transparent;
          border:none; border-bottom:2px solid transparent;
          color:#8a7a5a; font-family:'Cinzel',serif;
          font-size:10px; letter-spacing:2px; cursor:pointer;
        "
      >💀 MAGIAS</button>
    </div>

    <!-- CONTEÚDO DA ABA -->
    <div id="conteudo-ficha-pedro"></div>
  `;

  skillsContainer.appendChild(fichaContainer);

  // Renderiza atributos por padrão
  const conteudo = document.getElementById('conteudo-ficha-pedro');
  if (conteudo) {
    conteudo.innerHTML = renderConteudoAtributosPedro(heroi);
  }
}

function csUpdateLobbyBar(msg){
  const codeEl = document.getElementById('cs-room-code');
  if(codeEl) codeEl.textContent = msg.code || '----';

  const row = document.getElementById('cs-players-row');
  if(row) row.innerHTML = msg.players.map(p=>{
    const isMe = p.id === GS.myPid;
    const rdy  = !!p.class_id;
    const cls  = (p.class_id && msg.classes) ? msg.classes[p.class_id] : null;
    const tag  = cls ? ` ${cls.emoji}` : '';   // mostra a classe escolhida de cada um
    return `<span class="cs-player-chip${isMe?' me':''}${rdy?' ready':''}">${p.name}${tag}${p.id===msg.host?' ♛':''}</span>`;
  }).join('');

  // Seletor de masmorra — controlado pelo host; o modo é exibido a todos.
  const picker = document.getElementById('cs-dungeon-picker');
  if(picker){
    const isHost   = (msg.host === GS.myPid);
    const dungeons  = GS.lobbyDungeons;            // getter (sem parênteses)
    const campaigns = GS.lobbyCampaigns;           // getter (sem parênteses)
    const sel      = GS.lobbySelectedDungeon;     // getter (sem parênteses)
    const selCamp  = msg.selected_campaign || null;   // campanha selecionada (lobby_state)
    const modeTxt  = (GS.lobbyMode === 'campaign') ? 'Modo: Campanha'
                   : (GS.lobbyMode === 'authored') ? 'Modo: Masmorra' : 'Modo: Procedural';
    let opts = ['<option value="">Procedural (aleatória)</option>']
      .concat(dungeons.map(d =>
        `<option value="${d.file}"${d.file === sel ? ' selected' : ''}>${d.name}</option>`))
      .join('');
    if(campaigns.length){
      opts += `<optgroup label="Campanhas">` +
        campaigns.map(c =>
          `<option value="campaign:${c.file}"${c.file === selCamp ? ' selected' : ''}>${c.name}</option>`
        ).join('') +
        `</optgroup>`;
    }
    picker.innerHTML =
      `<label class="cs-dungeon-lbl">Masmorra:</label>` +
      `<select id="cs-dungeon-select"${isHost ? '' : ' disabled'}>${opts}</select>` +
      `<span class="cs-dungeon-mode">${modeTxt}</span>`;
    // Re-liga o onchange a cada render (o lobby é redesenhado a cada lobby_state).
    const dsel = document.getElementById('cs-dungeon-select');
    if(dsel) dsel.onchange = () => {
      const v = dsel.value || '';
      if(v.startsWith('campaign:')) GS.selectCampaign(v.slice('campaign:'.length));
      else { GS.selectCampaign(null); GS.selectDungeon(v || null); }  // limpa campanha ao escolher masmorra/procedural
    };
  }

  const btnS = document.getElementById('cs-btn-start');
  if(btnS) btnS.style.display = (msg.host===GS.myPid && msg.can_start) ? 'block' : 'none';
}

function csConfirmClass(){
  if(!csf || !csf.selectedId) return;
  if(csf.takenIds && csf.takenIds.has(csf.selectedId)){
    toast('Personagem já escolhido por outro jogador.', 'var(--orange)');
    return;
  }
  send({type:'select_class', class_id: csf.selectedId});
  toast(`${_CSD[csf.selectedId]?.cls ?? csf.selectedId} selecionado!`, 'var(--gold)');
  // Mago/clérigo: escolher 2 magias de 1º círculo (obrigatório p/ iniciar — gate no servidor).
  if(csf.selectedId === 'mage' || csf.selectedId === 'cleric'){
    mostrarOverlaySelecaoMagiasCriacao(csf.selectedId);
  }
}

function destroyClassSelectFull(){
  if(!csf) return;
  cancelAnimationFrame(csf.animFrame);
  csf.renderer.domElement.removeEventListener('mousemove',  _csfMouseMove);
  csf.renderer.domElement.removeEventListener('click',      _csfClick);
  csf.renderer.domElement.removeEventListener('mouseleave', _csfMouseLeave);
  csf.renderer.dispose();
  csf = null;
  // Remove portrait completely — no image data should persist into the dungeon
  const frame = document.getElementById('cs-portrait-frame');
  const img   = document.getElementById('cs-portrait-img');
  if(frame){ frame.classList.remove('has-portrait'); frame.style.opacity = '0'; }
  if(img)  { img.src = ''; img.onload = null; img.onerror = null; }
}

// ═══════════════════════════════════════════════════════════════════════════
// HIGHLIGHT DE ALCANCE — ARREMESSO DA ADAGA SECUNDÁRIA (3D)
// Adaptado ao código real: THREE → g3.T; scene → g3.scene; tile==world via
// casaParaMundo (grid [x,y] → world (x,0,y)); tiles em GS.gameState.tiles
// (TILE_FLOOR/TILE_WALL); inimigos em GS.gameState.monsters; alvo do mouse via
// get3DTile (retorna [x,y]). A execução usa a mensagem REAL `throw` (tratada por
// handle_throw, que já vira ação bônus se o jogador já agiu) — não a inexistente
// `bonus_action`. Geometria de alcance conforme a spec: linha reta OU diagonal,
// dentro do raio (Chebyshev) e com linha de visão sem paredes.
// ═══════════════════════════════════════════════════════════════════════════
const _highlightArremesso = { meshes: [], ativo: false, tileAlvo: null };

function getInimigoArremesso(x, y){
  const st = GS.gameState; if(!st) return null;
  return (st.monsters || []).find(m => m && m.hp > 0 && m.pos[0] === x && m.pos[1] === y) || null;
}
function temInimigoArremesso(x, y){ return !!getInimigoArremesso(x, y); }

// Linha de visão para arremesso: caminha tile a tile (reta ou diagonal) entre
// origem e destino; bloqueia se houver parede no meio. Substitui o inexistente
// `temLinhaDeVisao` da spec.
function temLinhaDeVisaoArremesso(ox, oy, dx, dy){
  const st = GS.gameState; if(!st || !st.tiles) return false;
  const sx = Math.sign(dx - ox), sy = Math.sign(dy - oy);
  let cx = ox, cy = oy;
  while(true){
    cx += sx; cy += sy;
    if(cx === dx && cy === dy) break;          // chegou ao alvo (não testa o tile do alvo)
    const row = st.tiles[cy]; if(!row) return false;
    if(row[cx] === TILE_WALL) return false;    // parede no caminho
  }
  return true;
}

// Tiles válidos de arremesso a partir de posicaoHeroi=[x,y], raio (Chebyshev).
function calcularTilesArremessoAdaga(posicaoHeroi, raio = 3){
  const tiles = [];
  const st = GS.gameState; if(!st || !st.tiles) return tiles;
  const [x, y] = posicaoHeroi;
  const H = st.tiles.length, W = st.tiles[0].length;
  for(let dx = -raio; dx <= raio; dx++){
    for(let dy = -raio; dy <= raio; dy++){
      if(dx === 0 && dy === 0) continue;                 // tile do próprio herói
      const dist = Math.max(Math.abs(dx), Math.abs(dy)); // Chebyshev (inclui diagonais)
      if(dist > raio) continue;
      const emLinhaReta = dx === 0 || dy === 0;          // arremesso em linha reta
      const emDiagonal  = Math.abs(dx) === Math.abs(dy); // ou diagonal perfeita
      if(!emLinhaReta && !emDiagonal) continue;
      const tx = x + dx, ty = y + dy;
      if(tx < 0 || ty < 0 || tx >= W || ty >= H) continue;
      if(st.tiles[ty][tx] !== TILE_FLOOR) continue;       // só piso
      if(!temLinhaDeVisaoArremesso(x, y, tx, ty)) continue;
      tiles.push({ x: tx, y: ty, dist, temInimigo: temInimigoArremesso(tx, ty) });
    }
  }
  return tiles;
}

const _ARREMESSO_Y = 0.12;        // altura do highlight acima do piso
function mostrarHighlightArremesso(posicaoHeroi){
  limparHighlightArremesso();
  if(!g3) return;
  const T = g3.T;
  const tiles = calcularTilesArremessoAdaga(posicaoHeroi);
  _highlightArremesso.ativo = true;
  tiles.forEach(tile => {
    const w   = casaParaMundo(tile.x, tile.y);
    const geo = new T.PlaneGeometry(0.9, 0.9);
    geo.rotateX(-Math.PI / 2);
    const cor = tile.temInimigo ? 0xff2222 : 0xffaa00;   // vermelho=inimigo, laranja=válido
    const mat = new T.MeshBasicMaterial({
      color: cor, transparent: true,
      opacity: tile.temInimigo ? 0.55 : 0.30, depthWrite: false,
    });
    const mesh = new T.Mesh(geo, mat);
    mesh.position.set(w.x, _ARREMESSO_Y, w.z);
    mesh.renderOrder = 999;
    mesh.userData.tilePos = tile;
    mesh.userData.tipo    = 'highlight_arremesso';
    g3.scene.add(mesh);
    _highlightArremesso.meshes.push(mesh);
  });
  _animarHighlightArremesso();
}

function limparHighlightArremesso(){
  if(g3){
    _highlightArremesso.meshes.forEach(m => {
      g3.scene.remove(m);
      if(m.geometry) m.geometry.dispose();
      if(m.material) m.material.dispose();
    });
    const traj = g3.scene.getObjectByName('trajetoria_arremesso');
    if(traj) g3.scene.remove(traj);
    if(g3.renderer) g3.renderer.domElement.style.cursor = 'default';
  }
  _highlightArremesso.meshes   = [];
  _highlightArremesso.ativo    = false;
  _highlightArremesso.tileAlvo = null;
  removerLegendaArremesso();
}

// Pulso de opacidade — tiles piscam levemente (RAF próprio; o loop principal
// renderiza a cena continuamente, então a mudança aparece).
function _animarHighlightArremesso(){
  if(!_highlightArremesso.ativo) return;
  const t = performance.now() / 1000;
  _highlightArremesso.meshes.forEach((mesh, i) => {
    const tile  = mesh.userData.tilePos;
    const base  = tile.temInimigo ? 0.55 : 0.30;
    mesh.material.opacity = base + Math.sin(t * 2.5 + i * 0.3) * 0.12;
  });
  requestAnimationFrame(_animarHighlightArremesso);
}

// Hover no tabuleiro durante o modo arremesso — destaca o tile sob o mouse e
// desenha a trajetória até o inimigo. Reutilizável entre o sistema secundário e
// o principal (recebe o objeto `sistema` correspondente). Chamado por on3DMouseMove.
function _processarHoverArremesso(e, sistema){
  if(!sistema.ativo || !g3) return;
  const el = g3.renderer.domElement;
  // Remove destaque anterior
  if(sistema.tileAlvo){
    const ant = sistema.meshes.find(m => m.userData.tilePos === sistema.tileAlvo);
    if(ant){ ant.scale.set(1, 1, 1); ant.position.y = _ARREMESSO_Y; }
  }
  sistema.tileAlvo = null;
  el.style.cursor = 'default';
  const tile = get3DTile(e);
  if(!tile) return;
  const [tx, ty] = tile;
  const meshAlvo = sistema.meshes.find(m =>
    m.userData.tilePos.x === tx && m.userData.tilePos.y === ty);
  if(meshAlvo){
    meshAlvo.scale.set(1.08, 1, 1.08);
    meshAlvo.position.y = _ARREMESSO_Y + 0.05;
    sistema.tileAlvo = meshAlvo.userData.tilePos;
    el.style.cursor = 'crosshair';
    if(meshAlvo.userData.tilePos.temInimigo){
      const me = GS.gameState.players.find(p => p.id === GS.myPid && p.alive);
      if(me) mostrarTrajetoriaArremesso(me.pos, [tx, ty]);
    }
  }
}
function onMouseMoveArremesso(e){ _processarHoverArremesso(e, _highlightArremesso); }

// Clique num tile durante o modo arremesso. Só arremessa em tile com inimigo;
// envia a mensagem REAL `throw` (target_id). Mantém o modo ativo em cliques
// inválidos (retry); limpa ao arremessar.
function onClickTileArremesso(tileClicado){
  if(!_highlightArremesso.ativo) return;
  const [tx, ty] = tileClicado;
  const meshValido = _highlightArremesso.meshes.find(m =>
    m.userData.tilePos.x === tx && m.userData.tilePos.y === ty);
  if(!meshValido){ GS.adicionarLog('⚠️ Fora do alcance de arremesso'); return; }
  const tile = meshValido.userData.tilePos;
  if(!tile.temInimigo){ GS.adicionarLog('⚠️ Arremesse em direção a um inimigo'); return; }
  const inimigo = getInimigoArremesso(tx, ty);
  if(!inimigo){ GS.adicionarLog('⚠️ Inimigo não encontrado'); return; }
  send({ type: 'throw', target_id: inimigo.id });   // handle_throw → vira ação bônus se já agiu
  limparHighlightArremesso();
}

// Linha tracejada amarela do herói ao alvo. origem/destino = [x,y].
function mostrarTrajetoriaArremesso(origem, destino){
  if(!g3) return;
  const T = g3.T;
  const old = g3.scene.getObjectByName('trajetoria_arremesso');
  if(old) g3.scene.remove(old);
  const o = casaParaMundo(origem[0], origem[1]);
  const d = casaParaMundo(destino[0], destino[1]);
  const pontos = [];
  const passos = 8;
  for(let i = 0; i <= passos; i++){
    const t = i / passos;
    pontos.push(new T.Vector3(o.x + (d.x - o.x) * t, 0.35, o.z + (d.z - o.z) * t));
  }
  const geo = new T.BufferGeometry().setFromPoints(pontos);
  const mat = new T.LineDashedMaterial({ color: 0xffaa00, dashSize: 0.15, gapSize: 0.10, linewidth: 1 });
  const linha = new T.Line(geo, mat);
  linha.computeLineDistances();
  linha.name = 'trajetoria_arremesso';
  g3.scene.add(linha);
}

// Legenda no rodapé durante o modo arremesso.
function mostrarLegendaArremesso(){
  if(document.getElementById('legenda-arremesso')) return;
  const legenda = document.createElement('div');
  legenda.id = 'legenda-arremesso';
  legenda.style.cssText = `
    position: fixed; bottom: 120px; left: 50%; transform: translateX(-50%);
    background: rgba(10,8,5,0.92); border: 1px solid #ffaa00; color: #ffaa00;
    font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 2px;
    padding: 8px 20px; pointer-events: none; z-index: 100;`;
  legenda.innerHTML = `
    🎯 MODO ARREMESSO —
    <span style="color:#ff2222">■</span> Inimigo
    <span style="color:#ffaa00">■</span> Tile válido —
    ESC para cancelar`;
  document.body.appendChild(legenda);
}
function removerLegendaArremesso(){
  const l = document.getElementById('legenda-arremesso');
  if(l) l.remove();
}

// Entrada do modo: lê a posição real do herói (gameState), exige adaga
// arremessável na mão secundária, mostra highlight + legenda, cursor crosshair,
// e ESC para cancelar. Exposta globalmente (onclick do botão do painel).
function iniciarModoArremessoAdagaSecundaria(){
  if(window._modoArremessoPrincipal){ toast('Cancele o arremesso atual primeiro (ESC).', 'var(--gold)'); return; }
  if(!g3){ toast('Arremesso com mira disponível apenas na visão 3D.', 'var(--gold)'); return; }
  const me = GS.gameState && GS.gameState.players.find(p => p.id === GS.myPid && p.alive);
  if(!me){ return; }
  const offThrow = me.gear && me.gear.off_hand && me.gear.off_hand.throw_range;
  if(!offThrow){ toast('Nenhuma adaga secundária arremessável equipada.', 'var(--gold)'); return; }
  window._modoArremessoAtivo = true;
  mostrarHighlightArremesso(me.pos);
  mostrarLegendaArremesso();
  if(g3.renderer) g3.renderer.domElement.style.cursor = 'crosshair';
  GS.adicionarLog('🎯 Clique num inimigo destacado para arremessar a adaga (ESC cancela).');
  document.addEventListener('keydown', function cancelar(ev){
    if(ev.key === 'Escape'){
      limparHighlightArremesso();
      window._modoArremessoAtivo = false;
      GS.adicionarLog('❌ Arremesso cancelado.');
      document.removeEventListener('keydown', cancelar);
    }
  });
}
window.iniciarModoArremessoAdagaSecundaria = iniciarModoArremessoAdagaSecundaria;

// ═══════════════════════════════════════════════════════════════════════════
// HIGHLIGHT DE ALCANCE — ARREMESSO DA ADAGA PRINCIPAL (mão de arma) — AZUL
// Sistema separado do secundário (mesmas regras de alcance/LOS via
// calcularTilesArremessoAdaga), porém cor AZUL para diferenciar. A execução usa
// a MESMA mensagem real `throw`: o servidor (_executar_arremesso) varre os slots
// na ordem ("weapon","off_hand") e arremessa o PRIMEIRO arremessável — ou seja,
// com a adaga na mão principal, é ela que voa; e handle_throw já decide sozinho
// se é AÇÃO PRINCIPAL (ainda não agiu) ou AÇÃO BÔNUS (já agiu). Não existe
// mensagem `bonus_action` no servidor — não é usada.
// ═══════════════════════════════════════════════════════════════════════════
const COR_HIGHLIGHT_ADAGA_PRINCIPAL = {
  tileVazio:        0x4488ff,   // azul — diferente do laranja da secundária
  tileInimigo:      0xff2222,   // vermelho — igual nos dois sistemas
  opacidadeBase:    0.30,
  opacidadeInimigo: 0.55,
};
const _highlightArremessoPrincipal = { meshes: [], ativo: false, tileAlvo: null };

function mostrarHighlightArremessoPrincipal(posicaoHeroi){
  limparHighlightArremessoPrincipal();
  if(!g3) return;
  const T = g3.T;
  const tiles = calcularTilesArremessoAdaga(posicaoHeroi);
  _highlightArremessoPrincipal.ativo = true;
  tiles.forEach(tile => {
    const w   = casaParaMundo(tile.x, tile.y);
    const geo = new T.PlaneGeometry(0.9, 0.9);
    geo.rotateX(-Math.PI / 2);
    const cor = tile.temInimigo
      ? COR_HIGHLIGHT_ADAGA_PRINCIPAL.tileInimigo
      : COR_HIGHLIGHT_ADAGA_PRINCIPAL.tileVazio;
    const opacidade = tile.temInimigo
      ? COR_HIGHLIGHT_ADAGA_PRINCIPAL.opacidadeInimigo
      : COR_HIGHLIGHT_ADAGA_PRINCIPAL.opacidadeBase;
    const mat = new T.MeshBasicMaterial({ color: cor, transparent: true, opacity: opacidade, depthWrite: false });
    const mesh = new T.Mesh(geo, mat);
    mesh.position.set(w.x, _ARREMESSO_Y, w.z);
    mesh.renderOrder = 999;
    mesh.userData.tilePos = tile;
    mesh.userData.tipo    = 'highlight_arremesso_principal';
    g3.scene.add(mesh);
    _highlightArremessoPrincipal.meshes.push(mesh);
  });
  _animarHighlightArremessoPrincipal();
}

function limparHighlightArremessoPrincipal(){
  if(g3){
    _highlightArremessoPrincipal.meshes.forEach(m => {
      g3.scene.remove(m);
      if(m.geometry) m.geometry.dispose();
      if(m.material) m.material.dispose();
    });
    const traj = g3.scene.getObjectByName('trajetoria_arremesso');
    if(traj) g3.scene.remove(traj);
    if(g3.renderer) g3.renderer.domElement.style.cursor = 'default';
  }
  _highlightArremessoPrincipal.meshes   = [];
  _highlightArremessoPrincipal.ativo    = false;
  _highlightArremessoPrincipal.tileAlvo = null;
  removerLegendaArremessoPrincipal();
}

function _animarHighlightArremessoPrincipal(){
  if(!_highlightArremessoPrincipal.ativo) return;
  const t = performance.now() / 1000;
  _highlightArremessoPrincipal.meshes.forEach((mesh, i) => {
    const tile = mesh.userData.tilePos;
    const base = tile.temInimigo ? COR_HIGHLIGHT_ADAGA_PRINCIPAL.opacidadeInimigo : COR_HIGHLIGHT_ADAGA_PRINCIPAL.opacidadeBase;
    mesh.material.opacity = base + Math.sin(t * 2.5 + i * 0.3) * 0.12;
  });
  requestAnimationFrame(_animarHighlightArremessoPrincipal);
}

function onMouseMoveArremessoPrincipal(e){ _processarHoverArremesso(e, _highlightArremessoPrincipal); }

function onClickTileArremessoPrincipal(tileClicado){
  if(!_highlightArremessoPrincipal.ativo) return;
  const [tx, ty] = tileClicado;
  const meshValido = _highlightArremessoPrincipal.meshes.find(m =>
    m.userData.tilePos.x === tx && m.userData.tilePos.y === ty);
  if(!meshValido){ GS.adicionarLog('⚠️ Fora do alcance de arremesso'); return; }
  const tile = meshValido.userData.tilePos;
  if(!tile.temInimigo){ GS.adicionarLog('⚠️ Arremesse em direção a um inimigo'); return; }
  const inimigo = getInimigoArremesso(tx, ty);
  if(!inimigo){ GS.adicionarLog('⚠️ Inimigo não encontrado'); return; }
  send({ type: 'throw', target_id: inimigo.id });   // servidor decide principal/bônus e o slot (mão principal primeiro)
  limparHighlightArremessoPrincipal();
}

function mostrarLegendaArremessoPrincipal(tipoAcao){
  removerLegendaArremessoPrincipal();
  const legenda = document.createElement('div');
  legenda.id = 'legenda-arremesso-principal';
  legenda.style.cssText = `
    position: fixed; bottom: 120px; left: 50%; transform: translateX(-50%);
    background: rgba(10,8,5,0.92); border: 1px solid #4488ff; color: #4488ff;
    font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 2px;
    padding: 8px 20px; pointer-events: none; z-index: 100;`;
  legenda.innerHTML = `
    🎯 ARREMESSO ${tipoAcao} —
    <span style="color:#ff2222">■</span> Inimigo
    <span style="color:#4488ff">■</span> Tile válido —
    ESC para cancelar`;
  document.body.appendChild(legenda);
}
function removerLegendaArremessoPrincipal(){
  const l = document.getElementById('legenda-arremesso-principal');
  if(l) l.remove();
}

// Entrada do modo (mão principal). Lê posição/estado reais do gameState; exige
// adaga arremessável na mão principal (me.weapon.throw_range) e ação disponível.
function iniciarModoArremessoAdagaPrincipal(){
  if(window._modoArremessoAtivo || window._modoArremessoPrincipal){
    toast('Cancele o arremesso atual primeiro (ESC).', 'var(--gold)'); return;
  }
  if(!g3){ toast('Arremesso com mira disponível apenas na visão 3D.', 'var(--gold)'); return; }
  const me = GS.gameState && GS.gameState.players.find(p => p.id === GS.myPid && p.alive);
  if(!me){ return; }
  const armaThrow = me.weapon && me.weapon.throw_range;
  if(!armaThrow){ toast('Nenhuma adaga arremessável na mão principal.', 'var(--gold)'); return; }
  if(me.action_done && me.bonus_action_used){ toast('Sem ações disponíveis para arremessar.', 'var(--gold)'); return; }
  const tipoAcao = me.action_done ? 'AÇÃO BÔNUS' : 'AÇÃO PRINCIPAL';
  window._modoArremessoPrincipal = true;
  mostrarHighlightArremessoPrincipal(me.pos);
  mostrarLegendaArremessoPrincipal(tipoAcao);
  if(g3.renderer) g3.renderer.domElement.style.cursor = 'crosshair';
  GS.adicionarLog(`🎯 Modo arremesso (mão principal) — ${tipoAcao}. Clique num inimigo (ESC cancela).`);
  document.addEventListener('keydown', function cancelar(ev){
    if(ev.key === 'Escape'){
      limparHighlightArremessoPrincipal();
      window._modoArremessoPrincipal = false;
      GS.adicionarLog('❌ Arremesso cancelado.');
      document.removeEventListener('keydown', cancelar);
    }
  });
}
window.iniciarModoArremessoAdagaPrincipal = iniciarModoArremessoAdagaPrincipal;
window.limparHighlightArremessoPrincipal  = limparHighlightArremessoPrincipal;

// ═══════════════════════════════════════════════════════════════════════════
// HIGHLIGHT DE ALCANCE — ARREMESSO DA LANÇA CURTA (mão de arma) — VERDE
// Sistema separado (mesmas regras de alcance/LOS via calcularTilesArremessoAdaga,
// hover compartilhado _processarHoverArremesso), cor VERDE para diferenciar das
// adagas. Execução pela mensagem real `throw` (servidor decide ação e slot).
// ⚠️ DORMENTE no jogo atual: nenhum personagem equipa `lanca_curta` (o servidor
// só tem `lanca` range-2 SEM throw_range), então o botão não aparece em jogo até
// a reconciliação catálogo↔servidor dar à lança curta uma arma arremessável.
// Além disso, quando ligado, o `throw` real usa DESTREZA p/ todo arremesso — o
// cálculo por FORÇA do spec está só no scaffolding do servidor (não roteado).
// ═══════════════════════════════════════════════════════════════════════════
const COR_HIGHLIGHT_LANCA = {
  tileVazio:        0x44cc44,   // verde — diferente de azul (principal) e laranja (secundária)
  tileInimigo:      0xff2222,   // vermelho — igual nos demais sistemas
  opacidadeBase:    0.30,
  opacidadeInimigo: 0.55,
};
const _highlightArremessoLanca = { meshes: [], ativo: false, tileAlvo: null };

function mostrarHighlightArremessoLanca(posicaoHeroi){
  limparHighlightArremessoLanca();
  if(!g3) return;
  const T = g3.T;
  const tiles = calcularTilesArremessoAdaga(posicaoHeroi);   // mesmo alcance 3 / linha reta+diagonal / LOS
  _highlightArremessoLanca.ativo = true;
  tiles.forEach(tile => {
    const w   = casaParaMundo(tile.x, tile.y);
    const geo = new T.PlaneGeometry(0.9, 0.9);
    geo.rotateX(-Math.PI / 2);
    const cor = tile.temInimigo ? COR_HIGHLIGHT_LANCA.tileInimigo : COR_HIGHLIGHT_LANCA.tileVazio;
    const opacidade = tile.temInimigo ? COR_HIGHLIGHT_LANCA.opacidadeInimigo : COR_HIGHLIGHT_LANCA.opacidadeBase;
    const mat = new T.MeshBasicMaterial({ color: cor, transparent: true, opacity: opacidade, depthWrite: false });
    const mesh = new T.Mesh(geo, mat);
    mesh.position.set(w.x, _ARREMESSO_Y, w.z);
    mesh.renderOrder = 999;
    mesh.userData.tilePos = tile;
    mesh.userData.tipo    = 'highlight_arremesso_lanca';
    g3.scene.add(mesh);
    _highlightArremessoLanca.meshes.push(mesh);
  });
  _animarHighlightArremessoLanca();
}

function limparHighlightArremessoLanca(){
  if(g3){
    _highlightArremessoLanca.meshes.forEach(m => {
      g3.scene.remove(m);
      if(m.geometry) m.geometry.dispose();
      if(m.material) m.material.dispose();
    });
    const traj = g3.scene.getObjectByName('trajetoria_arremesso');
    if(traj) g3.scene.remove(traj);
    if(g3.renderer) g3.renderer.domElement.style.cursor = 'default';
  }
  _highlightArremessoLanca.meshes   = [];
  _highlightArremessoLanca.ativo    = false;
  _highlightArremessoLanca.tileAlvo = null;
  removerLegendaArremessoLanca();
}

function _animarHighlightArremessoLanca(){
  if(!_highlightArremessoLanca.ativo) return;
  const t = performance.now() / 1000;
  _highlightArremessoLanca.meshes.forEach((mesh, i) => {
    const tile = mesh.userData.tilePos;
    const base = tile.temInimigo ? COR_HIGHLIGHT_LANCA.opacidadeInimigo : COR_HIGHLIGHT_LANCA.opacidadeBase;
    mesh.material.opacity = base + Math.sin(t * 2.5 + i * 0.3) * 0.12;
  });
  requestAnimationFrame(_animarHighlightArremessoLanca);
}

function onMouseMoveArremessoLanca(e){ _processarHoverArremesso(e, _highlightArremessoLanca); }

function onClickTileArremessoLanca(tileClicado){
  if(!_highlightArremessoLanca.ativo) return;
  const [tx, ty] = tileClicado;
  const meshValido = _highlightArremessoLanca.meshes.find(m =>
    m.userData.tilePos.x === tx && m.userData.tilePos.y === ty);
  if(!meshValido){ GS.adicionarLog('⚠️ Fora do alcance de arremesso'); return; }
  const tile = meshValido.userData.tilePos;
  if(!tile.temInimigo){ GS.adicionarLog('⚠️ Arremesse em direção a um inimigo'); return; }
  const inimigo = getInimigoArremesso(tx, ty);
  if(!inimigo){ GS.adicionarLog('⚠️ Inimigo não encontrado'); return; }
  send({ type: 'throw', target_id: inimigo.id });   // servidor decide principal/bônus e o slot
  limparHighlightArremessoLanca();
}

function mostrarLegendaArremessoLanca(tipoAcao){
  removerLegendaArremessoLanca();
  const legenda = document.createElement('div');
  legenda.id = 'legenda-arremesso-lanca';
  legenda.style.cssText = `
    position: fixed; bottom: 120px; left: 50%; transform: translateX(-50%);
    background: rgba(10,8,5,0.92); border: 1px solid #44cc44; color: #44cc44;
    font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 2px;
    padding: 8px 20px; pointer-events: none; z-index: 100;`;
  legenda.innerHTML = `
    🏹 ARREMESSO DE LANÇA ${tipoAcao} —
    <span style="color:#ff2222">■</span> Inimigo
    <span style="color:#44cc44">■</span> Tile válido —
    ESC para cancelar`;
  document.body.appendChild(legenda);
}
function removerLegendaArremessoLanca(){
  const l = document.getElementById('legenda-arremesso-lanca');
  if(l) l.remove();
}

function iniciarModoArremessoLanca(){
  if(window._modoArremessoAtivo || window._modoArremessoPrincipal || window._modoArremessoLanca){
    toast('Cancele o arremesso atual primeiro (ESC).', 'var(--gold)'); return;
  }
  if(!g3){ toast('Arremesso com mira disponível apenas na visão 3D.', 'var(--gold)'); return; }
  const me = GS.gameState && GS.gameState.players.find(p => p.id === GS.myPid && p.alive);
  if(!me){ return; }
  const arma = me.weapon;
  if(!arma || arma.id !== 'lanca_curta'){ toast('Lança curta não equipada.', 'var(--gold)'); return; }
  if(me.action_done && me.bonus_action_used){ toast('Sem ações disponíveis para arremessar.', 'var(--gold)'); return; }
  const tipoAcao = me.action_done ? 'AÇÃO BÔNUS' : 'AÇÃO PRINCIPAL';
  window._modoArremessoLanca = true;
  mostrarHighlightArremessoLanca(me.pos);
  mostrarLegendaArremessoLanca(tipoAcao);
  if(g3.renderer) g3.renderer.domElement.style.cursor = 'crosshair';
  GS.adicionarLog(`🏹 Modo arremesso de lança — ${tipoAcao}. Clique num inimigo (ESC cancela).`);
  document.addEventListener('keydown', function cancelar(ev){
    if(ev.key === 'Escape'){
      limparHighlightArremessoLanca();
      window._modoArremessoLanca = false;
      GS.adicionarLog('❌ Arremesso cancelado.');
      document.removeEventListener('keydown', cancelar);
    }
  });
}
window.iniciarModoArremessoLanca     = iniciarModoArremessoLanca;
window.limparHighlightArremessoLanca = limparHighlightArremessoLanca;

function get3DTile(e){
  if(!g3) return null;
  const { T, renderer, raycaster, camera, tileMeshes } = g3;
  const rect = renderer.domElement.getBoundingClientRect();
  const mx   = ((e.clientX - rect.left) / rect.width)  *  2 - 1;
  const my   = ((e.clientY - rect.top)  / rect.height) * -2 + 1;
  raycaster.setFromCamera(new T.Vector2(mx, my), camera);
  const floors = Object.values(tileMeshes).filter(m => m.visible && m.userData.isFloor);
  const hits   = raycaster.intersectObjects(floors);
  if(!hits.length) return null;
  const obj = hits[0].object;
  return [obj.userData.gridX, obj.userData.gridY];
}

// Mira LIVRE no 3D: intersecta um plano matemático na altura do chão e converte
// para coordenadas de grade. Funciona em QUALQUER casa do mapa — inclusive sob
// névoa (meshes invisíveis são ignorados pelo raycaster). Usado pela
// Clarividência, cujo alcance é o tabuleiro inteiro.
function get3DTilePlane(e){
  if(!g3) return null;
  const { T, renderer, raycaster, camera, W, H } = g3;
  const rect = renderer.domElement.getBoundingClientRect();
  const mx   = ((e.clientX - rect.left) / rect.width)  *  2 - 1;
  const my   = ((e.clientY - rect.top)  / rect.height) * -2 + 1;
  raycaster.setFromCamera(new T.Vector2(mx, my), camera);
  const plane = new T.Plane(new T.Vector3(0, 1, 0), -0.22);   // y = TH (topo do chão)
  const pt = new T.Vector3();
  if(!raycaster.ray.intersectPlane(plane, pt)) return null;
  const gx = Math.round(pt.x), gy = Math.round(pt.z);
  if(gx < 0 || gy < 0 || gx >= W || gy >= H) return null;
  return [gx, gy];
}

// ── 3D click handler: delegates to unified handleTileClick ───────────────────
// Guard: if the pointer moved while any button was held (orbit / pan / dolly),
// the mousedown → mousemove → mouseup sequence is a camera gesture, not a tap.
// Consume the synthetic click event and reset the flag for the next interaction.

function on3DClick(e){
  if(_orbitDragMoved){ _orbitDragMoved = false; return; }
  // Modo de mira de MAGIA: clicar uma carta arma a mira; aqui o clique no
  // tabuleiro resolve o alvo/casa e envia a mensagem `magia` (ver castarMagia).
  if(window._modoMagia){
    const tMag = window._modoMagia.alvoLivre ? get3DTilePlane(e) : get3DTile(e);
    if(tMag) _clickTileMagia(tMag[0], tMag[1]);
    return;
  }
  // Modo posicionamento de ARMADILHA (Luccas): clique numa casa para criar.
  if(window._modoPlacementArmadilha){
    const tArm = get3DTile(e);
    if(tArm) onClickTileParaArmadilha(tArm[0], tArm[1]);
    return;
  }
  // Modo arremesso da LANÇA CURTA (verde): clique no tabuleiro mira o alvo.
  if(window._modoArremessoLanca){
    const tArr = get3DTile(e);
    if(tArr) onClickTileArremessoLanca(tArr);
    if(!_highlightArremessoLanca.ativo) window._modoArremessoLanca = false;
    return;
  }
  // Modo arremesso da adaga PRINCIPAL (azul): clique no tabuleiro mira o alvo.
  if(window._modoArremessoPrincipal){
    const tArr = get3DTile(e);
    if(tArr) onClickTileArremessoPrincipal(tArr);
    if(!_highlightArremessoPrincipal.ativo) window._modoArremessoPrincipal = false;
    return;
  }
  // Modo arremesso da adaga SECUNDÁRIA (laranja): clique no tabuleiro mira o alvo.
  if(window._modoArremessoAtivo){
    const tArr = get3DTile(e);
    if(tArr) onClickTileArremesso(tArr);
    if(!_highlightArremesso.ativo) window._modoArremessoAtivo = false;  // arremessou → sai do modo
    return;
  }
  const tile = get3DTile(e);
  if(!tile) return;
  const [tx, ty] = tile;

  if(GS.gameState){
    const chest = (GS.gameState.chests||[]).find(c=>c.pos[0]===tx&&c.pos[1]===ty);
    if(chest){
      const myP = GS.gameState.players.find(p=>p.id===GS.myPid&&p.alive);
      const dist = myP ? Math.max(Math.abs(myP.pos[0]-tx), Math.abs(myP.pos[1]-ty)) : 99;
      if(dist <= 2){ openChestWindow(chest); return; }
      else { toast('Aproxime-se do baú para abri-lo!', 'var(--gold)'); return; }
    }
    // ── Decoration click (3D path — check footprint of each decoration) ─────────
    // Interativa (loot/fonte) → interage. Sólida (não-pisável) → bloqueia o clique.
    // Pisável (chão/fogueira) sem interação → deixa passar p/ a lógica de movimento
    // (o personagem caminha sobre o chão normalmente).
    const decsHere3D = GS.decorations.filter(d =>
      GS.decorTilesOf(d).some(t => t[0] === tx && t[1] === ty));
    if(decsHere3D.length){
      const inter3D = decsHere3D.find(d => d.tem_loot || d.special === 'fountain');
      if(inter3D){ GS.interagirDecor(inter3D.id); return; }
      if(decsHere3D.some(d => !d.pisavel)) return;   // objeto sólido bloqueia o caminho
      // só decoração(ões) pisável(is) → segue para o movimento
    }
  }

  if(g3 && GS.gameState){
    const hasEntity =
      GS.gameState.players.some(p  => p.alive && p.pos[0]===tx && p.pos[1]===ty) ||
      GS.gameState.monsters.some(m => m.hp>0   && m.pos[0]===tx && m.pos[1]===ty);
    if(hasEntity){
      g3.selectedPos = (g3.selectedPos && g3.selectedPos[0]===tx && g3.selectedPos[1]===ty)
        ? null : [tx, ty];
    } else {
      g3.selectedPos = null;
    }
  }
  handleTileClick(tx, ty);
}

function on3DMouseMove(e){
  if(!GS.gameState || !g3) return;
  // Mira de MAGIA: a área verde (efeito) segue o cursor enquanto você mira.
  if(window._modoMagia){
    const tMag = window._modoMagia.alvoLivre ? get3DTilePlane(e) : get3DTile(e);
    _recomputarAreaMagia(tMag ? tMag[0] : null, tMag ? tMag[1] : null);
    g3.renderer.domElement.style.cursor = 'crosshair';
    return;
  }
  if(window._modoArremessoLanca){ onMouseMoveArremessoLanca(e); return; }
  if(window._modoArremessoPrincipal){ onMouseMoveArremessoPrincipal(e); return; }
  if(window._modoArremessoAtivo){ onMouseMoveArremesso(e); return; }
  const tile = get3DTile(e);
  const tip  = $('tooltip');
  if(!tile){
    tip.style.display='none';
    g3.renderer.domElement.style.cursor='default';
    g3.hoveredPos = null;
    return;
  }
  const [tx,ty] = tile;
  const myP = GS.gameState.players.find(p=>p.id===GS.myPid&&p.alive);
  const el  = g3.renderer.domElement;

  if(GS.gameState.stairs_pos){
    const [sx,sy]=GS.gameState.stairs_pos;
    if(tx===sx&&ty===sy){
      tip.innerHTML=`🪜 <b>Escada de Saída</b><br><span style="color:#ffd040">Clique para retornar à cidade</span>`;
      tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
      el.style.cursor='pointer';
      g3.hoveredPos=null;   // don't hover-lift the tile as if it were a figure
      return;
    }
  }

  const hovChest = (GS.gameState.chests||[]).find(c=>c.pos[0]===tx&&c.pos[1]===ty);
  if(hovChest){
    const nItems = hovChest.items ? hovChest.items.length : 0;
    const dist   = myP ? Math.max(Math.abs(myP.pos[0]-tx), Math.abs(myP.pos[1]-ty)) : 99;
    const canOpen= dist <= 2;
    tip.innerHTML = `🎁 <b>Baú de Tesouro</b><br>` +
      `${hovChest.gold>0?`🪙 ${hovChest.gold} ouros  `:''}` +
      `${nItems>0?`📦 ${nItems} item(s)`:''}` +
      (canOpen
        ? `<br><span style="color:#ffd040">Clique para abrir</span>`
        : `<br><span style="color:#888">Aproxime-se para abrir</span>`);
    tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
    el.style.cursor = canOpen ? 'pointer' : 'default';
    g3.hoveredPos = null;
    return;
  }

  const monster = GS.gameState.monsters.find(m=>m.pos[0]===tx&&m.pos[1]===ty&&m.hp>0);
  if(monster){
    const dx=myP?Math.abs(myP.pos[0]-tx):99, dy=myP?Math.abs(myP.pos[1]-ty):99;
    const wRng = myP?.weapon?.range ?? null;
    const inR  = wRng!=null ? Math.max(dx,dy)<=wRng : (dx===1&&dy===0)||(dx===0&&dy===1);
    const canA = GS.isMyTurn && myP && !myP.action_done && inR && GS.gameState.phase==='playing';
    tip.innerHTML=fichaInimigoTooltipHTML(monster, _partyTemBardoVivo()) +
                  (canA ? `<br><span style="color:#f88">⚔ Clique → atacar</span>` : '');
    tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
    el.style.cursor = canA ? 'crosshair' : 'default';
    g3.hoveredPos = [tx, ty];   // trigger hover-lift + vitrine light
    return;
  }

  const player = GS.gameState.players.find(p=>p.pos[0]===tx&&p.pos[1]===ty&&p.alive);
  if(player){
    tip.innerHTML=`<b>${player.emoji} ${player.name}</b> Lv${player.level}<br>HP ${player.hp}/${player.max_hp}`;
    tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
    el.style.cursor='default';
    g3.hoveredPos = [tx, ty];   // trigger hover-lift + vitrine light
    return;
  }

  // Empty tile — clear hover state
  g3.hoveredPos = null;
  tip.style.display='none';
  if(GS.isMyTurn && GS.gameState.phase==='playing' && myP && myP.moves_left>0)
    el.style.cursor='pointer';
  else
    el.style.cursor='default';
}

// Called by both 2D canvas click and 3D on3DClick.
// Pure decision is delegated to GS.resolveTileClick(); this function handles
// the DOM-side effects (toast, renderMyPanel, send).
function handleTileClick(tx, ty){
  getAudioContext();
  if(!podeReceberInput()) return;   // bloqueia input durante a animação de movimento
  // ── Mira de MAGIA (2D e 3D): resolve alvo/casa e envia `magia` ─────────────
  // (No 3D, on3DClick já intercepta antes; aqui cobre o caminho do canvas 2D.)
  if(window._modoMagia){ _clickTileMagia(tx, ty); return; }
  // ── Stairs: clicking the staircase tile exits the dungeon immediately ────
  const _st = GS.gameState;
  if(_st && _st.stairs_pos){
    const [sx,sy] = _st.stairs_pos;
    if(tx===sx && ty===sy){
      send({type:'exit_dungeon'});
      return;
    }
  }

  // ── Chest click (2D canvas path — 3D path handled in on3DClick) ────────────
  if(_st && !mode3D){
    const chest = (_st.chests||[]).find(c=>c.pos[0]===tx&&c.pos[1]===ty);
    if(chest){
      const myP = _st.players.find(p=>p.id===GS.myPid&&p.alive);
      const dist = myP ? Math.max(Math.abs(myP.pos[0]-tx), Math.abs(myP.pos[1]-ty)) : 99;
      if(dist <= 2){ openChestWindow(chest); return; }
      else { toast('Aproxime-se do baú para abri-lo!', 'var(--gold)'); return; }
    }
  }

  // ── Decoration click (2D canvas path — 3D path handled in on3DClick) ─────────
  // Interativa (loot/fonte) → interage. Sólida → bloqueia o clique. Pisável
  // (chão/fogueira) sem interação → deixa passar p/ a lógica de movimento.
  if(_st && !mode3D){
    const decsHere = GS.decorations.filter(d =>
      GS.decorTilesOf(d).some(t => t[0] === tx && t[1] === ty));
    if(decsHere.length){
      const inter = decsHere.find(d => d.tem_loot || d.special === 'fountain');
      if(inter){ GS.interagirDecor(inter.id); return; }
      if(decsHere.some(d => !d.pisavel)) return;   // objeto sólido bloqueia o caminho
      // só decoração(ões) pisável(is) → segue para o movimento
    }
  }

  // ── Controle de servos/elementais (clique no tabuleiro, 2D e 3D) ────────────
  // Clique em servo = seleciona/deseleciona. Com servo selecionado: clique em
  // monstro adjacente = ataca; clique em casa adjacente livre = move 1 passo.
  // Só disponível durante o turno dos servos (animados_turn === myPid).
  if(_st && GS.isMyTurn && _st.animados_turn === GS.myPid){
    // ── Prisioneiro liberto: o resgatador o controla (só movimento) ───────────
    const _prisC = _st.prisoner;
    const meuPrisClk = _prisC && _prisC.alive && _prisC.freed && _prisC.rescuer_pid === GS.myPid;
    if(meuPrisClk && _prisC.pos[0]===tx && _prisC.pos[1]===ty){
      _prisSel = !_prisSel; _animadoSel = null; renderMap(_st); return;
    }
    if(meuPrisClk && _prisSel){
      const expSetP = new Set(_st.explored.map(([x,y])=>`${x},${y}`));
      for(const [rx,ry] of (_st.revealed||[])) expSetP.add(`${rx},${ry}`);
      const passosP = GS.findPath(_st.tiles, expSetP, _prisC.pos[0], _prisC.pos[1], tx, ty, _prisC.moves_left||0);
      if(passosP && passosP.length){ _animarEEnviarMoverPrisioneiroCaminho(_prisC, passosP); return; }
      _prisSel=false; renderMap(_st); return;   // sem caminho/alcance → desseleciona
    }
    const meP  = _st.players.find(p=>p.id===GS.myPid && p.alive);
    const meus = (meP && meP.animados) ? meP.animados.filter(a=>a.pos && a.vida_atual>0) : [];
    if(meus.length){
      const sobre = meus.find(a=>a.pos[0]===tx && a.pos[1]===ty);
      if(sobre){
        _animadoSel = (_animadoSel===sobre.id) ? null : sobre.id;
        renderMap(_st);
        return;
      }
      if(_animadoSel){
        const a = meus.find(x=>x.id===_animadoSel);
        if(a){
          const mon = (_st.monsters||[]).find(m=>m.hp>0 && m.pos[0]===tx && m.pos[1]===ty);
          if(mon){
            const isElecA = a.especial === 'linha_3q';
            const dx_a = Math.abs(a.pos[0]-mon.pos[0]), dy_a = Math.abs(a.pos[1]-mon.pos[1]);
            const dist_a = dx_a + dy_a;
            const emLinha = (dx_a===0 || dy_a===0) && dist_a >= 1 && dist_a <= 3;
            if(isElecA ? emLinha : dist_a === 1) GS.atacarAnimado(a.id, mon.id);
            else toast(isElecA
              ? '⚡ O elemental elétrico ataca em linha reta (máx 3 casas).'
              : 'O servo precisa estar cardinalmente adjacente ao alvo.');
            return;
          }
          // Movimento fluido: percorre o caminho inteiro até a casa clicada,
          // dentro do orçamento de movimento do minion (igual ao herói). O
          // pathfinding considera tiles explorados + revelados ao vivo (a área
          // que o próprio minion enxerga).
          const expSetMin = new Set(_st.explored.map(([x,y])=>`${x},${y}`));
          for(const [rx,ry] of (_st.revealed||[])) expSetMin.add(`${rx},${ry}`);
          const passosMin = GS.findPath(_st.tiles, expSetMin, a.pos[0], a.pos[1], tx, ty, a.moves_left||0);
          if(passosMin && passosMin.length){ _animarEEnviarMoverCaminhoMinino(a, passosMin); return; }
          _animadoSel=null; renderMap(_st); return;   // sem caminho/alcance → desseleciona
        }
      }
    }
  }

  const action = GS.resolveTileClick(tx, ty);
  if(!action) return; // nothing to do (null = consume silently)
  switch(action.type){
    case 'open_door':
      send({type:'open_door', tx:action.x, ty:action.y});
      break;
    case 'door_far':
      toast('🚪 Aproxime-se da porta para abri-la.', 'var(--gold)');
      break;
    case 'attack_blocked_wall':
      toast('🧱 Uma parede bloqueia a linha de tiro!', 'var(--orange)');
      break;
    case 'skill_blocked':
      toast('⚠ Este ataque requer inimigo cardinalmente adjacente!', 'var(--orange)');
      break;
    case 'skill':
      GS.notifySkill();
      send({type:'skill', skill_id:action.skillId, target_id:action.targetId});
      GS.pendingSkill = null;
      renderMyPanel(GS.gameState);
      break;
    case 'attack':
      GS.notifyAttack();
      sendAttack(action.targetId);
      break;
    case 'move': {
      const myP  = _st.players.find(p=>p.id===GS.myPid && p.alive);
      const peao = (mode3D && g3) ? getPeaoMesh(GS.myPid) : null;
      if(peao && myP){
        // Caminho absoluto (passos relativos → casas {x,z}) p/ a animação.
        let cx = myP.pos[0], cy = myP.pos[1];
        const caminho = [];
        for(const [dx,dy] of action.path){ cx+=dx; cy+=dy; caminho.push({x:cx, z:cy}); }
        // Envia os passos ao servidor JÁ — assim a névoa é revelada (server-side)
        // em paralelo à animação local, em vez de só iniciar o round-trip DEPOIS
        // dela. Isso elimina a demora de "continuidade do mapa" ao caminhar.
        for(const [dx,dy] of action.path) GS.move(dx, dy);
        // Anima localmente; ao concluir, reconcilia com o estado autoritativo
        // (renderMap3D fica bloqueado durante a animação — este render final
        // garante que a névoa revelada apareça assim que o peão pousa).
        moverPeaoAoCaminho(peao, myP, caminho, () => {
          if(GS.gameState) renderMap3D(GS.gameState);
        });
      } else {
        // 2D ou sem peão 3D — movimento instantâneo (comportamento anterior).
        for(const [dx,dy] of action.path) GS.move(dx, dy);
      }
      break;
    }
  }
}

// (OrbitControls handles all global pointer tracking internally — no custom
//  window-level mouse listeners needed for camera movement.)

// ── GS EVENT CALLBACKS — wire GS events to renderer functions ─────────────
GS.on('wsError', () =>
  toast('❌ Servidor não encontrado. Execute iniciar.bat primeiro!', 'var(--red)'));

GS.on('wsClosed', (gs, cs) => {
  if(gs && gs.phase !== 'ended') toast('Conexão encerrada.');
  else if(cs)                    toast('Conexão com o servidor encerrada.', 'var(--red)');
});

// Reconexão automática (gameState tenta sozinho a cada 2,5 s, até 8 vezes)
GS.on('reconnecting', (n, max) =>
  toast(`🔌 Conexão perdida — reconectando (${n}/${max})...`, 'var(--orange)'));
GS.on('reconnectFailed', () =>
  toast('❌ Não foi possível reconectar. Recarregue a página e use "Reconectar à última partida".', 'var(--red)'));

GS.on('lobbyState',  msg => handleLobby(msg));

GS.on('gameStart', () => {
  destroyClassSelectFull();
  showScreen('screen-city');
  // Proactively request city_state — handles cases where the first one was lost
  setTimeout(()=>{ if(!GS.cityState) send({type:'get_city_state'}); }, 400);
});

GS.on('cityState', msg => {
  _hpSnapshot.clear();   // de volta à cidade: zera HP base p/ a próxima masmorra
  // If returning from dungeon to city, tear down the 3D renderer first
  if(g3){ dispose3D(); mode3D = false; }
  // Ensure city screen is visible (covers both initial arrival and return from dungeon)
  showScreen('screen-city');
  handleCityState(msg);
  // ── Sincroniza o herói do overlay com o estado autoritativo do servidor ──
  const meSrv = (msg.players || []).find(p => p.id === GS.myPid);
  if(meSrv) _sincronizarHeroiComServidor(meSrv);
  // Compra concluída → reabre a loja já com saldo/inventário atualizados.
  if(window._comprando && window._lojaUltimaAberta){
    window._comprando = false;
    abrirLoja(window._lojaUltimaAberta, GS.getHeroiAtivo());
  }
  // Painel da ficha aberto → re-renderiza com o estado novo (equipar/reordenar).
  if(_fcPanelPid != null) _refreshFichaCidadePanel();
  // Painel da Guilda aberto → re-renderiza (compra recém-concluída atualiza saldo/estado).
  const _gm = $('guild-modal');
  if(_gm && _gm.classList.contains('open')) _renderGuild();
});

GS.on('shopResult',  msg =>
  toast(msg.msg.replace(/\*\*(.+?)\*\*/g,'$1'), 'var(--green)'));

GS.on('enterDungeon', () => {
  fecharFichaCidade();
  _hpSnapshot.clear();   // novo cenário: zera HP base (1º game_state não dispara som)
  if(CITY_MODE==='image') destroyCityImage(); else destroyCity3D();
  // Tear down any leftover dungeon renderer from a previous run so the fresh
  // game_state rebuilds the scene from the correct (new) map. Combined with
  // gameState=null (gameState.js), this eliminates the "stale map / black
  // screen" bug on the 2nd+ dungeon entry.
  if(g3) dispose3D();
  mode3D = false;
  showScreen('screen-game');
  // Auto-enable 3D when entering the dungeon (if Three.js is available).
  // gameState foi limpo no enter_dungeon → init3D aguarda o estado fresco.
  if(window.THREE) toggle3D();
});

GS.on('gameState', msg => {
  _detectHpChanges(msg);   // som de dano/cura por variação de HP entre estados
  handleGameState(msg);
  // Sincroniza os animados autoritativos do servidor no registro do Pedro,
  // para a ficha refletir HP/pó durante o combate.
  const meNow = (msg.players||[]).find(p => p.id === GS.myPid);
  if (meNow && Array.isArray(meNow.animados)) {
    HERO_DATA.pedro.animados = meNow.animados;
    if (GS.HERO_DATA && GS.HERO_DATA.pedro) GS.HERO_DATA.pedro.animados = meNow.animados;
  }
  // Entrou na minha janela de controle (servos e/ou prisioneiro) → dica única.
  if (msg.animados_turn === GS.myPid && _lastAnimadosTurn !== GS.myPid) {
    const _pr = msg.prisoner;
    const soPris = _pr && _pr.alive && _pr.freed && _pr.rescuer_pid === GS.myPid
      && !((msg.players.find(p=>p.id===GS.myPid)?.animados||[]).some(a=>a.vida_atual>0));
    toast(soPris
      ? '🧍 Mova o prisioneiro — clique nele e depois numa casa; então encerre o turno.'
      : '💀 Turno dos seus servos — clique num servo (azul=movimento, vermelho=ataque); depois encerre o turno.');
  }
  // Janela de controle encerrou → limpa seleções.
  if (_lastAnimadosTurn === GS.myPid && msg.animados_turn !== GS.myPid) {
    _animadoSel = null;
    _prisSel = false;
  }
  _lastAnimadosTurn = msg.animados_turn || null;
  // Auto-refresh open chest window (contents may have changed)
  if(_openChestId){
    const updatedChest = (msg.chests||[]).find(c=>c.id===_openChestId);
    if(updatedChest) _renderChestWindow(updatedChest);
    else closeChestWindow();   // chest was emptied and removed
  }
  // Close decor loot panel if the decoration is now empty or gone
  if(_openDecorLootId){
    const decor = (msg.decorations||[]).find(d=>d.id===_openDecorLootId);
    if(!decor || !decor.tem_loot) closeChestWindow();
  }
});

GS.on('gmNarration', text => appendGM(text));

// Deslize fiel passo-a-passo de monstros inimigos e servos auto-comandados.
GS.on('entityStep', msg => _onEntityStep(msg));

// Sistema de fome/sede — logs de sobrevivência (gameState.js, DOM-free) vão
// para o painel do GM.
GS.on('survivalLog', text => appendGM(text));

// Atualização em tempo real das barras de fome/sede + vinheta de pressão
// (disparado a cada consumo/colapso, antes do round-trip do servidor).
GS.on('survivalChanged', () => { if(GS.gameState) renderPlayers(GS.gameState); });

GS.on('gameOver',    msg  => handleGameOver(msg));

// Explosão do Elemental de Fogo: destaca tiles em vermelho por duracao_ms.
let _explosionTiles = null;
let _explosionTimer = null;
GS.on('explosionArea', msg => {
  if(_explosionTimer) clearTimeout(_explosionTimer);
  _explosionTiles = new Set((msg.tiles||[]).map(([x,y])=>`${x},${y}`));
  if(GS.gameState) renderMap(GS.gameState);
  _explosionTimer = setTimeout(() => {
    _explosionTiles = null;
    _explosionTimer = null;
    if(GS.gameState) renderMap(GS.gameState);
  }, msg.duracao_ms || 2200);
});

GS.on('diceRoll',    msg  => { handleDiceRoll(msg); updateDiceHistory(msg); });

// Resultado de Animar Mortos: sincroniza os animados no registro completo do
// Pedro (game.js) e dispara a animação D100. Ao final, atualiza a ficha em jogo
// se estiver aberta na aba Magias.
GS.on('animarResult', msg => {
  if (HERO_DATA.pedro && Array.isArray(msg.animados)) HERO_DATA.pedro.animados = msg.animados;
  animarRolagemD100(msg, () => {
    const cont = document.getElementById('conteudo-ficha-jogo-pedro');
    const magAtiva = document.getElementById('aba-jogo-magias');
    if (cont && magAtiva) {
      const heroi = HERO_DATA?.pedro || GS.HERO_DATA?.pedro;
      cont.innerHTML = renderAbaMagiasPedro(heroi);
    }
  });
});

GS.on('serverError', msg  => {
  toast(msg);
  // Compra recusada pelo servidor → reabre a loja para nova tentativa.
  if(window._comprando && window._lojaUltimaAberta){
    window._comprando = false;
    setTimeout(() => abrirLoja(window._lojaUltimaAberta, GS.getHeroiAtivo()), 400);
  }
});

// ── Overlay de escolha de nova magia ao subir de nível (Pedro/Lewis) ──────────
// Bloqueia só quem subiu: o servidor recusa end_turn até a escolha ser enviada.
function mostrarOverlayEscolhaMagia(msg){
  const rotulo = {primeiro:'1º', segundo:'2º', terceiro:'3º'}[msg.circulo] || msg.circulo;
  const opcoes = (msg.opcoes || []).filter(id => window.GRIMORIO_CLIENT && GRIMORIO_CLIENT[id]);
  const cartas = opcoes.map(id => {
    const m = GRIMORIO_CLIENT[id];
    return `
      <div onclick="window._escolherMagiaNivel('${id}')"
           onmouseenter="mostrarTooltipMagia('${id}', event)"
           onmouseleave="ocultarTooltipMagia()"
           style="display:inline-flex; flex-direction:column; align-items:center; justify-content:center;
                  width:74px; height:88px; cursor:pointer; margin:5px; border-radius:4px;
                  background:rgba(255,255,255,0.04); border:2px solid #c8a95155; transition:all 0.2s;"
           onmouseover="this.style.borderColor='#c8a951'"
           onmouseout="this.style.borderColor='#c8a95155'">
        <div style="font-size:26px; margin-bottom:4px; line-height:1;">${m.icone || '✨'}</div>
        <div style="color:#c8b89a; font-family:'Cinzel',serif; font-size:8px; text-align:center; line-height:1.2; max-width:66px; word-break:break-word;">${m.nome}</div>
      </div>`;
  }).join('');
  const existente = document.getElementById('overlay-escolha-magia');
  if (existente) existente.remove();
  const el = document.createElement('div');
  el.id = 'overlay-escolha-magia';
  el.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px;';
  el.innerHTML = `
    <div style="color:#c8a951; font-family:'Cinzel Decorative',serif; font-size:15px; letter-spacing:3px; text-align:center;">SUBIU DE NÍVEL<br><span style="font-size:11px; color:#8a7a5a; letter-spacing:2px;">Escolha 1 magia de ${rotulo} círculo</span></div>
    <div style="display:flex; flex-wrap:wrap; gap:6px; max-width:680px; justify-content:center;">${cartas || '<div style="color:#8a7a5a;">Nenhuma magia disponível</div>'}</div>`;
  document.body.appendChild(el);
}

window._escolherMagiaNivel = function(id){
  GS.escolherMagiaNivel(id);
  const el = document.getElementById('overlay-escolha-magia');
  if (el) el.remove();
};

GS.on('spellPickPrompt', mostrarOverlayEscolhaMagia);

// ── Decoration loot panel — reuses chest overlay with generic callbacks ────────
GS.on('decor_loot', msg => {
  abrirPainelLoot({
    titulo: '📦 Objeto',
    gold: msg.gold || 0,
    items: msg.items || [],
    onPegarOuro: () => GS.takeFromDecor(msg.decor_id, 'gold', 0),
    onPegarItem: (i) => GS.takeFromDecor(msg.decor_id, 'item', i),
  });
  _openDecorLootId = msg.decor_id;   // set AFTER abrirPainelLoot (which resets it)
});

// ── Overlay de seleção das 2 magias iniciais (criação, Pedro/Lewis) ───────────
function mostrarOverlaySelecaoMagiasCriacao(cls){
  window._magiasCriacaoSel = [];
  window._magiasCriacaoCls = cls;
  const existente = document.getElementById('overlay-selecao-criacao');
  if (existente) existente.remove();
  const el = document.createElement('div');
  el.id = 'overlay-selecao-criacao';
  el.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.88); z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px;';
  document.body.appendChild(el);
  _renderOverlaySelecaoCriacao();
}

function _renderOverlaySelecaoCriacao(){
  const el = document.getElementById('overlay-selecao-criacao');
  if(!el) return;
  const cls = window._magiasCriacaoCls;
  const sel = window._magiasCriacaoSel || [];
  const opcoes = Object.values(GRIMORIO_CLIENT).filter(m => m.circulo === 'primeiro' && m.classe.includes(cls));
  const cartas = opcoes.map(m => {
    const on = sel.includes(m.id);
    return `
      <div onclick="window._toggleMagiaCriacao('${m.id}')"
           onmouseenter="mostrarTooltipMagia('${m.id}', event)"
           onmouseleave="ocultarTooltipMagia()"
           style="display:inline-flex; flex-direction:column; align-items:center; justify-content:center;
                  width:74px; height:88px; cursor:pointer; margin:5px; border-radius:4px;
                  background:${on ? 'rgba(200,169,81,0.18)' : 'rgba(255,255,255,0.04)'};
                  border:2px solid ${on ? '#c8a951' : '#c8a95155'}; transition:all 0.2s;">
        <div style="font-size:26px; margin-bottom:4px; line-height:1;">${m.icone || '✨'}</div>
        <div style="color:#c8b89a; font-family:'Cinzel',serif; font-size:8px; text-align:center; line-height:1.2; max-width:66px; word-break:break-word;">${m.nome}</div>
      </div>`;
  }).join('');
  const pronto = sel.length === 2;
  el.innerHTML = `
    <div style="color:#c8a951; font-family:'Cinzel Decorative',serif; font-size:15px; letter-spacing:3px; text-align:center;">MAGIAS INICIAIS<br><span style="font-size:11px; color:#8a7a5a; letter-spacing:2px;">Escolha 2 magias de 1º círculo</span></div>
    <div style="display:flex; flex-wrap:wrap; gap:6px; max-width:680px; justify-content:center;">${cartas}</div>
    <div style="color:${pronto ? '#44cc88' : '#8a7a5a'}; font-size:11px; letter-spacing:1px;">${sel.length}/2 selecionadas</div>
    <button onclick="window._confirmarMagiasCriacao()" ${pronto ? '' : 'disabled'}
      style="padding:9px 22px; font-family:'Cinzel',serif; font-size:11px; letter-spacing:2px;
             background:${pronto ? 'rgba(68,204,136,0.18)' : 'rgba(80,80,80,0.18)'};
             color:${pronto ? '#44cc88' : '#666'}; border:1px solid ${pronto ? '#44cc88' : '#444'};
             cursor:${pronto ? 'pointer' : 'not-allowed'};">✓ CONFIRMAR</button>`;
}

window._toggleMagiaCriacao = function(id){
  const sel = window._magiasCriacaoSel || (window._magiasCriacaoSel = []);
  const i = sel.indexOf(id);
  if(i >= 0) sel.splice(i,1);
  else if(sel.length < 2) sel.push(id);
  _renderOverlaySelecaoCriacao();
};

window._confirmarMagiasCriacao = function(){
  const sel = window._magiasCriacaoSel || [];
  if(sel.length !== 2){ toast('Escolha 2 magias de 1º círculo.', 'var(--orange)'); return; }
  GS.setKnownSpells(sel);
  const el = document.getElementById('overlay-selecao-criacao');
  if (el) el.remove();
  toast('Magias escolhidas!', 'var(--gold)');
};