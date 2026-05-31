'use strict';
// ===========================================================================
// game.js — Legends for Hire (todo o JavaScript do jogo)
// A estrutura HTML do <body> foi movida para cá e é injetada ANTES de
// qualquer código que acesse o DOM, preservando 100% o comportamento.
// ===========================================================================
document.body.innerHTML = `
<!-- ══ CONNECT ══ -->
<div id="screen-connect" class="screen active">
  <div class="logo">
    <h1>LEGENDS FOR HIRE</h1>
    <p>RPG de Tabuleiro Online — até 6 jogadores</p>
  </div>
  <div class="connect-panel">
    <h2>Entrar na Aventura</h2>
    <div style="background:#0d1a0d;border:1px solid #2a4a2a;border-radius:6px;padding:8px 12px;font-size:.75rem;color:#8ab88a;line-height:1.5;">
      ⚙️ <b style="color:#6fc96f;">Como jogar:</b> Clique duas vezes em <code style="background:#1a2a1a;padding:1px 5px;border-radius:3px;color:#a0e0a0;">iniciar.bat</code> para iniciar o servidor e abrir o jogo automaticamente.
    </div>
    <div class="field">
      <label>Seu nome de herói</label>
      <input id="input-name" type="text" maxlength="20" placeholder="Ex: Thorin" value="">
    </div>
    <div class="field">
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
    <button id="cs-btn-start" onclick="startGame()" style="display:none">▶ Iniciar Jogo</button>
  </div>
  <div id="cs-confirm-wrap">
    <div id="cs-progress-wrap"><div id="cs-progress-fill"></div></div>
    <button id="cs-btn-confirm" onclick="csConfirmClass()">⚔ Partir para a Aventura</button>
  </div>
  <div id="cs-hint">Escolha seu herói</div>
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
      <div id="view-3d-ctrls">
        <span id="orbit-hint">🖱 esq: orbitar &nbsp;·&nbsp; dir: pan &nbsp;·&nbsp; scroll: zoom</span>
        <button id="btn-cam-reset" onclick="resetCamera3D()" title="Visão isométrica padrão (R)">⌂ Reset</button>
        <button id="btn-3d-toggle" onclick="toggle3D()" title="Alternar visão 3D / 2D">🎲 3D</button>
      </div>
    </div>
    <div id="map-wrap">
      <canvas id="dungeon-canvas"></canvas>
    </div>
    <canvas id="dice-canvas"></canvas>
    <div id="gm-log">
      <div id="gm-log-header">
        <span>📖 MESTRE DO JOGO</span>
      </div>
      <div id="gm-log-body"></div>
    </div>
  </div>

  <div id="side-panel">
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
    <h3>🎁 Baú de Tesouro</h3>
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

const TILE_WALL=GS.TILE_WALL, TILE_FLOOR=GS.TILE_FLOOR;
const CELL=64; // px per tile (CSS pixels × devicePixelRatio)
const SPR_SCALE=CELL/48; // sprite scale factor (sprites designed for CELL=48)

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

function createRoom(){
  const name=getName(); if(!name) return;
  const url=$('input-server').value.trim()||'ws://localhost:8765';
  GS.connect(url, name, 'create');
}

function joinRoom(){
  const name=getName(); if(!name) return;
  const code=$('input-code').value.trim().toUpperCase();
  if(code.length!==4){ toast('Código deve ter 4 letras.'); return; }
  const url=$('input-server').value.trim()||'ws://localhost:8765';
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
  if(csf){ csf.selectedId = msg.players.find(p=>p.id===GS.myPid)?.class_id ?? csf.selectedId; }
}

function startGame(){ send({type:'start_game'}); }

// ■  CITY SCREEN — Three.js 3D isometric hub

let _city3 = null;
let _cityTOD = 0.78; // time-of-day: 0=midnight, 0.25=dawn, 0.5=noon, 0.75=dusk

const _CTY_BLDGS = [
  {id:'taverna',  name:'Taverna',            emoji:'🍺',action:'Descansar — recuperar HP',
   x:-5.5,z:-4,  w:3.2,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x7a3a10,roofHex:0x4a2208,winHex:0xffcc44},
  {id:'templo',   name:'Templo',             emoji:'⛪',action:'Bênçãos e curas divinas',
   x:0,  z:-7.5, w:4.0,d:3.2,wallH:3.0,roofH:2.2, wallHex:0x283088,roofHex:0x181858,winHex:0x88aaff},
  {id:'ferreiro', name:'Ferraria',           emoji:'⚒',action:'Comprar equipamentos',
   x:5.5,z:-4,   w:3.2,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x5a2810,roofHex:0x3a1808,winHex:0xff8822},
  {id:'guilda',   name:'Guilda dos Heróis',  emoji:'⚔',action:'Missões disponíveis',
   x:-5.5,z:2,   w:3.0,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x5a4a10,roofHex:0x3a3008,winHex:0xffee88},
  {id:'mercador', name:'Mercado',            emoji:'🛒',action:'Itens e poções',
   x:5.5,z:2,    w:3.0,d:2.4,wallH:2.2,roofH:1.8, wallHex:0x205a20,roofHex:0x103815,winHex:0x88ff88},
  {id:'dungeon',  name:'Portão da Masmorra', emoji:'💀',action:'Entrar na masmorra!',
   x:0,  z:8,    w:3.4,d:1.8,wallH:3.6,roofH:0,   wallHex:0x1a1428,roofHex:0x000000,winHex:0xff2020,isDungeon:true},
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
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  const scene = new T.Scene();
  scene.background = new T.Color(0x0a0818);
  scene.fog = new T.FogExp2(0x080612, 0.015);

  // ── Camera: isometric 45° orthographic ──
  const aspect = W / H;
  const fV     = 11;
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

  _startCity3Loop();
  _updateCityTimeBadge();
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
    return `<div class="city-hcard${isMe?' me':''}">
      <span style="font-size:18px;line-height:1">${p.emoji}</span>
      <div><div class="city-hcard-name">${p.name}</div>
           <div class="city-hcard-hp ${st}">${p.hp}/${p.max_hp} HP</div></div>
    </div>`;
  }).join('')+`<div class="city-gold-badge">💰 ${gold} Ouro</div>`;
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
      osc.connect(g); g.connect(actx.destination);
      osc.start(now); osc.stop(now+1.3);
      // Low rumble
      const osc2=actx.createOscillator(), g2=actx.createGain();
      osc2.type='sine'; osc2.frequency.value=38;
      g2.gain.setValueAtTime(0.28,now); g2.gain.linearRampToValueAtTime(0,now+1.6);
      osc2.connect(g2); g2.connect(actx.destination);
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
  _city3.renderer.dispose();
  _city3=null;
  _cityHideTooltip();
  const fo=document.getElementById('city-fade-overlay');
  if(fo) fo.remove();
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
    btnD.style.display=isHost?'inline-block':'none';
    if(dungBar) dungBar.style.display=isHost?'flex':'none';
    if(hint) hint.textContent=isHost
      ?'Você é o anfitrião — clique no Portão ou aqui para entrar.'
      :'Aguardando o anfitrião iniciar a aventura…';
  }
  // Shop
  if(GS.activeShop) _renderShopItems();
  if(GS.pendingShopOpen){ const s=GS.pendingShopOpen; GS.pendingShopOpen=null; openShop(s); }
  // Init 3D city scene on first arrival
  if(!_city3&&window.THREE) initCity3D();
  // Clear fade overlay if returning from dungeon
  const fo=document.getElementById('city-fade-overlay');
  if(fo){ fo.classList.remove('on'); setTimeout(()=>{ if(fo.parentNode) fo.remove(); },1200); }
}

// ── Legacy 2D city data (kept so shop modal lookups still find building names) ──
const CITY_DUNGEON = { id: 'dungeon', x: 305, y: 352, w: 90, h: 88 };
const CITY_BUILDINGS = [
  { id:'taverna',  name:'Taverna',  emoji:'🍺', desc:'Comida e descanso',
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

  const list=$('shop-items-list'); if(!list) return;
  list.innerHTML=items.map(item=>{
    const canBuy=gold>=item.price;
    const desc=_itemDesc(item);
    const kindTag=item.kind==='shield'?'<span style="color:var(--blue);font-size:.68rem;"> [escudo]</span>':'';
    return `<div class="shop-item">
      <span class="shop-item-emoji">${item.emoji||'📦'}</span>
      <div class="shop-item-info">
        <div class="shop-item-name">${item.name}${kindTag}</div>
        <div class="shop-item-desc">${desc}</div>
      </div>
      <span class="shop-item-price">💰 ${item.price}</span>
      <button class="btn-buy" ${canBuy?'':'disabled'}
        onclick="buyItem('${shopKey}','${item.id}')">Comprar</button>
    </div>`;
  }).join('');
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
  if(item.die){
    const range=item.range?` • Alcance ${item.range}`:'';
    return `${item.die} dano (${item.stat==='dex'?'DES':'FOR'})${range}`;
  }
  if(item.ac_bonus!=null){
    const kindTxt=item.kind==='shield'?'Escudo — soma com armadura':'Armadura';
    return `${kindTxt} • CA +${item.ac_bonus}`;
  }
  const fx={
    heal:'Restaura HP', mana:'Restaura Mana', atk_bonus:'Bônus de Ataque',
    maxhp:'Aumenta HP máx', atk:'Bônus Ataque', spd:'Velocidade',
    full_heal:'Cura total de HP', full_mana:'Restaura toda a mana',
    bless:'Bônus de Ataque divino', cleanse:'Remove status negativos',
    temp_atk:'Ataque temporário', full_heal_mp:'Cura HP e Mana completos',
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
}

function updateTurnBadge(msg){
  $('round-badge').textContent = `Rodada ${msg.round}`;
  const cur = msg.players.find(p=>p.id===msg.current_turn);
  $('turn-badge').textContent = cur ? `${cur.emoji} ${cur.name}` : '—';
  $('turn-badge').style.background = cur ? cur.color : 'var(--gold)';
  $('turn-badge').style.color = '#fff';
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
  // Class sprite — scaled to fill larger CELL
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
  // Clip to circle
  ctx.save(); ctx.beginPath(); ctx.arc(0,0,r+2,0,Math.PI*2); ctx.clip();
  ctx.textAlign='center'; ctx.textBaseline='middle';
  // Scale sprite to fill CELL
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
  ctx.restore();
}

// ══ END SPRITE ENGINE ═══════════════════════════════════════════════════════

// ══ 3D DIORAMA MAP ═══════════════════════════════════════════════════════════

const WALL_RISE = Math.round(CELL * 0.50); // visible wall-face height — taller = more 3D depth

// ── Vision set: tiles currently visible to the local player ──────────────────
// Enemies outside this set are hidden (fog of war). Floor/walls keep using
// exploredSet so already-discovered tiles remain permanently visible.
// Uses Chebyshev distance (max of |dx|, |dy|) — square radius = torch lantern.
function computeVisionSet(state, me){
  if(!me) return new Set();
  const [px,py] = me.pos;
  const SIGHT   = 6;
  const set     = new Set();
  for(const [ex,ey] of state.explored){
    if(Math.max(Math.abs(ex-px), Math.abs(ey-py)) <= SIGHT)
      set.add(`${ex},${ey}`);
  }
  return set;
}

function renderMap(state){
  if(!state.tiles) return;
  if(mode3D){ renderMap3D(state); return; }
  const canvas=$('dungeon-canvas');
  const W=state.tiles[0].length, H=state.tiles.length;
  applyDPR(canvas, W*CELL, H*CELL);
  const ctx=canvas.getContext('2d');

  const exploredSet=new Set(state.explored.map(([x,y])=>`${x},${y}`));
  const me=state.players.find(p=>p.id===GS.myPid&&p.alive);
  const visionSet=computeVisionSet(state, me);

  const reachable=new Set();
  if(GS.isMyTurn&&me&&me.moves_left>0)
    bfsReachable(state.tiles,exploredSet,me.pos[0],me.pos[1],me.moves_left,reachable);

  // ── PASS 0: Void background — near-black with deep dungeon darkness
  ctx.fillStyle='#040308';
  ctx.fillRect(0,0,W*CELL,H*CELL);

  // ── PASS 1: Floor tiles (stone flagstones) — only explored
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!exploredSet.has(`${x},${y}`)) continue;
    if(state.tiles[y][x]===TILE_FLOOR)
      drawFloor3D(ctx, x, y, reachable.has(`${x},${y}`));
  }

  // ── PASS 2: Wall south-face shadows
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!exploredSet.has(`${x},${y}`)) continue;
    if(state.tiles[y][x]===TILE_WALL){
      const sy=y+1;
      if(sy<H && state.tiles[sy][x]===TILE_FLOOR && exploredSet.has(`${x},${sy}`))
        drawWallSouthFace(ctx, x, y);
    }
  }

  // ── PASS 3: Wall top faces
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!exploredSet.has(`${x},${y}`)) continue;
    if(state.tiles[y][x]===TILE_WALL)
      drawWallTop3D(ctx, x, y);
  }

  // ── PASS 4: Impenetrable fog on unexplored tiles (Diablo-style pitch-black)
  ctx.fillStyle='rgba(4,3,8,0.96)';
  for(let y=0;y<H;y++) for(let x=0;x<W;x++){
    if(!exploredSet.has(`${x},${y}`))
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

  // ── Monsters: only visible within player's vision radius
  for(const m of state.monsters){
    const [mx,my]=m.pos;
    if(!visionSet.has(`${mx},${my}`)) continue;
    const cx=mx*CELL+CELL/2, cy=my*CELL+CELL/2;
    drawMiniBase(ctx, cx, cy, '#c02020', false);
    drawMonsterSprite(ctx, cx, cy-3, m);
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

  // ── Players: base disc then hero sprite
  ctx.textAlign='center'; ctx.textBaseline='middle';
  for(const p of state.players){
    if(!p.alive) continue;
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

// ── DIABLO-STYLE FLOOR TILE — dark charcoal flagstones with blood & bone details
function drawFloor3D(ctx, x, y, isReachable){
  const X=x*CELL, Y=y*CELL;
  const h=((x*7919)^(y*3467)^(x<<5)^(y>>2))&0xFFFF;

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
    const r0=Math.min(255,44+v), g0=Math.min(255,42+v), b0=Math.min(255,50+Math.floor(v*0.6));

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

  // Reachable tile highlight
  if(isReachable){
    ctx.strokeStyle='rgba(80,180,255,0.68)'; ctx.lineWidth=2;
    ctx.strokeRect(X+2,Y+2,CELL-4,CELL-4);
    ctx.fillStyle='rgba(50,120,255,0.09)';
    ctx.fillRect(X+2,Y+2,CELL-4,CELL-4);
    ctx.fillStyle='rgba(130,210,255,0.60)';
    const d=4;
    for(const [cx3,cy3] of [[X+d,Y+d],[X+CELL-d,Y+d],[X+d,Y+CELL-d],[X+CELL-d,Y+CELL-d]]){
      ctx.beginPath(); ctx.arc(cx3,cy3,1.8,0,Math.PI*2); ctx.fill();
    }
  }
}

// ── 3D WALL SOUTH FACE — visible stone masonry face (the wall's front face)
function drawWallSouthFace(ctx, x, y){
  const X=x*CELL, Y=y*CELL;
  const faceH=WALL_RISE+6;  // height of visible stone face
  const faceY=Y+CELL-1;     // starts at bottom of wall top tile
  const h=((x*6131)^(y*4919))&0xFFFF;

  // ── Base fill: stone wall FRONT FACE — medium gray castle stone, lit from above
  const wfG=ctx.createLinearGradient(0,faceY,0,faceY+faceH);
  wfG.addColorStop(0,   'rgba(148,142,134,0.99)'); // top — lit face (light gray)
  wfG.addColorStop(0.30,'rgba(110,106,100,0.99)'); // mid
  wfG.addColorStop(0.68,'rgba(58,54,50,0.97)');    // lower — in shadow
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
function drawWallTop3D(ctx, x, y){
  const X=x*CELL, Y=y*CELL;
  const h=((x*6271)^(y*2749)^(y<<4))&0xFFFF;
  const v=(h%18)-9;

  // Deep mortar — dark gray with faint blue tinge (grout between stones)
  ctx.fillStyle='#1a1c22';
  ctx.fillRect(X,Y,CELL,CELL);

  // Stone face — MEDIUM GRAY with cool blue tint (classic castle/dungeon stone wall)
  const r0=Math.min(255,132+v), g0=Math.min(255,130+v), b0=Math.min(255,140+Math.floor(v*0.5));
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
    crackSrc.connect(hpf); hpf.connect(crackGain); crackGain.connect(ctx.destination);
    crackSrc.start(now);

    // Layer 2 — low body thud (pitched sine)
    const thudOsc  = ctx.createOscillator();
    const thudGain = ctx.createGain();
    thudOsc.type = 'sine';
    thudOsc.frequency.setValueAtTime(160 * intensity, now);
    thudOsc.frequency.exponentialRampToValueAtTime(55, now + 0.07);
    thudGain.gain.setValueAtTime(0.40 * intensity, now);
    thudGain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
    thudOsc.connect(thudGain); thudGain.connect(ctx.destination);
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
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(now); osc.stop(now + 0.20);
  } catch(e){}
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

  // ── Solid color background — NO gradient, NO vignette, NO specular ────────
  c.fillStyle = hexColor;
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

// ── MeshLambertMaterial — emissive color bypasses scene lighting completely ───
// Lambert ignores roughness/metalness — the emissive component keeps the die's
// hue fully saturated even in the pitch-dark dungeon.
// dieType selects the correct face-texture builder (d20 uses triangular canvas).
function _buildDieMat(T, value, hexColor, dieType){
  const faceTex = dieType === 'd20'
    ? _dieFaceTexD20(T, value, hexColor)
    : _dieFaceTex(T, value, hexColor);
  return new T.MeshLambertMaterial({
    color:             0xffffff,                    // white so map texture hue shows unmodified
    map:               faceTex,
    emissive:          new T.Color(hexColor),       // die's own color always glows through
    emissiveIntensity: VC.dice.emissiveIntensity,   // 0.4 — vivid without being neon
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

function _spawnDie3D(dieType, value, label, hexColor){
  if(!g3) return;                         // game scene must be active
  const T = window.THREE;

  // One-time: create diceGroup with two PointLights that travel with the dice area.
  // Main light from above (y+2) illuminates top faces; fill from below (y-1) kills shadows.
  if(_d3 && !_d3._diceGroup){
    const area = _getDiceArea();
    const diceGroup = new T.Group();
    diceGroup.position.set(area.x, DICE_FLOOR_Y, area.z);

    const dlMain = new T.PointLight(0xffffff, VC.dice.light.main.intensity, VC.dice.light.main.distance);
    dlMain.position.set(0, VC.dice.light.main.yOffset, 0);
    diceGroup.add(dlMain);

    const dlFill = new T.PointLight(0xffffff, VC.dice.light.fill.intensity, VC.dice.light.fill.distance);
    dlFill.position.set(0, VC.dice.light.fill.yOffset, 0);
    diceGroup.add(dlFill);

    g3.scene.add(diceGroup);
    _d3._diceGroup = diceGroup;
  }

  const geo  = _buildDieGeo(T, dieType);
  const mat  = _buildDieMat(T, value, hexColor, dieType);
  const mesh = new T.Mesh(geo, mat);
  mesh.castShadow=true; mesh.receiveShadow=true;
  mesh.scale.setScalar(VC.dice.scale);   // 30% larger for better board visibility

  // Land at the board centre (scatter ±1.5 tiles around area)
  const area   = _getDiceArea();
  const floorY = DICE_FLOOR_Y;           // = 0.22 — top surface of board tiles
  const dieRad = 0.42 * VC.dice.scale;   // collision radius scales with die size

  // Scatter each die within ±1.5 tiles of the area centre
  const spawnX = area.x + _rr(-1.5, 1.5);
  const spawnZ = area.z + _rr(-1.5, 1.5);
  // Drop from 2.5 units above the floor (short, punchy fall)
  mesh.position.set(spawnX, floorY + 2.5, spawnZ);
  mesh.rotation.set(_rr(0,Math.PI*2), _rr(0,Math.PI*2), _rr(0,Math.PI*2));

  const faceNormals = _getFlatNormals(geo);

  mesh.renderOrder = 999;   // flush after all board geometry (reinforces depthTest:false)
  g3.scene.add(mesh);
  _dice3.push({
    mesh, geo, mat,
    vel:    { x:_rr(-1,1), y:-8, z:_rr(-1,1) },   // narrow lateral — stay near area
    angVel: { x:_rr(-15,15), y:_rr(-15,15), z:_rr(-15,15) },
    floorY, dieRad, area,                           // area captured at spawn time
    bounces:0, phase:'rolling', alpha:1.0, settleT:0,
    value, label, dieType, faceNormals,
  });

  if(!_d3.animFrame) _startDiceLoop3D();
  playRollSound();
}

function handleDiceRoll(msg){
  if(!_d3) _d3 = { animFrame:null, _cfr:0 };   // ensure state object exists

  const dieType  = (msg.die||'d20').replace(/^\d+/,'');
  const delay    = _dice3.length * (80 + Math.random()*70);   // staggered launch
  const hexColor = DIE_COLORS[dieType] || VC.dice.colors.d20;

  setTimeout(()=>_spawnDie3D(dieType, msg.value, msg.label||dieType, hexColor), delay);
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
      // Gold particle burst on the board at the die's resting position
      if(g3) _spawnGoldParticles(window.THREE, g3.scene, mesh.position);
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

// Physics-only loop — dice live in g3.scene, rendered by the game's main renderer
function _startDiceLoop3D(){
  if(!_d3 || _d3.animFrame) return;
  let lastT = performance.now();
  function frame(now){
    if(!_d3) return;
    const dt = Math.min(now-lastT, 50); lastT=now;
    _d3._cfr++;

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
        if(g3) g3.scene.remove(_dice3[i].mesh);
        _dice3[i].geo.dispose(); _dice3[i].mat.dispose();
        _dice3.splice(i, 1);
      }
    }

    // Keep loop alive while dice or particles remain
    if(_dice3.length>0 || _particleSystems.length>0){
      _d3.animFrame = requestAnimationFrame(frame);
    } else {
      _d3.animFrame = null;
    }
  }
  _d3.animFrame = requestAnimationFrame(frame);
}

function renderPlayers(state){
  const el=$('player-cards'); el.innerHTML='';
  for(const p of state.players){
    const isMe=p.id===GS.myPid, isCur=p.id===state.current_turn;
    const div=document.createElement('div');
    div.className='pcard'+(isMe?' me':'')+(isCur?' current':'')+(p.alive?'':' dead');
    const hpPct=Math.max(0,p.hp/p.max_hp*100);
    const mpPct=Math.max(0,p.mp/p.max_mp*100);
    div.innerHTML=`
      <div class="pcard-top">
        <span class="pcard-emoji">${p.emoji}</span>
        <span class="pcard-name" style="color:${p.color}">${p.name}</span>
        <span class="pcard-lvl">Lv${p.level}</span>
      </div>
      <div class="bars">
        <div class="bar-row">
          <span class="bar-label">HP</span>
          <div class="bar-bg"><div class="bar-fill hp" style="width:${hpPct}%"></div></div>
          <span class="bar-val">${p.hp}/${p.max_hp}</span>
        </div>
        <div class="bar-row">
          <span class="bar-label">MP</span>
          <div class="bar-bg"><div class="bar-fill mp" style="width:${mpPct}%"></div></div>
          <span class="bar-val">${p.mp}/${p.max_mp}</span>
        </div>
      </div>`;
    el.appendChild(div);
  }
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
  $('my-stats').innerHTML = `
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
        <b style="color:#f8d040;font-size:1.1rem;">${vAc}</b>
      </div>
      <div class="combat-chip">
        <span class="cl">Ataque</span>
        <b style="color:#e8e0c8;">${vAtk >= 0 ? '+' : ''}${vAtk}</b>
      </div>
      <div class="combat-chip">
        <span class="cl">Mov</span>
        <b style="color:#e8e0c8;">${me.moves_left ?? 0}/${me.spd ?? 0}</b>
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
        <span class="sv-val" style="color:#f8d040;">${vFort >= 0 ? '+' : ''}${vFort}</span>
        <span class="sv-sub">venenos</span>
      </div>
      <div class="save-box" style="border-color:var(--teal)">
        <span class="sv" style="color:var(--teal)">Ref</span>
        <span class="sv-val" style="color:#f8d040;">${vRef >= 0 ? '+' : ''}${vRef}</span>
        <span class="sv-sub">área/arm.</span>
      </div>
      <div class="save-box" style="border-color:var(--purple)">
        <span class="sv" style="color:var(--purple)">Von</span>
        <span class="sv-val" style="color:#f8d040;">${vWill >= 0 ? '+' : ''}${vWill}</span>
        <span class="sv-sub">magia</span>
      </div>
    </div>

    <div class="equip-row">
      <div class="equip-item" style="position:relative;">
        <div class="gear-slot-label" style="align-self:flex-start;margin-bottom:2px;">⚔ ARMA</div>
        <canvas id="weapon-canvas" width="60" height="92" style="background:#0e0c1a;border-radius:3px;width:60px;height:92px;"></canvas>
        <div class="equip-name" style="color:#e8e0c8;font-weight:bold;">${weapon ? weapon.name : 'Desarmado'}</div>
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">${dmgFmt}</div>
      </div>
      <div class="equip-item" style="position:relative;">
        <div class="gear-slot-label" style="align-self:flex-start;margin-bottom:2px;">🛡 ARMADURA</div>
        <canvas id="armor-canvas" width="60" height="92" style="background:#0e0c1a;border-radius:3px;width:60px;height:92px;"></canvas>
        <div class="equip-name" style="color:#e8e0c8;font-weight:bold;">${armorName}</div>
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">CA ${vAc}</div>
      </div>
    </div>
  `;

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

  // ── Action buttons (with weapon damage formula shown) ──
  const _rangeHint = _wRange != null ? `alcance ${_wRange}` : 'corpo a corpo';
  const _adjHint = canAct && !canAttack
    ? `<small style="color:#e07060;display:block;font-size:.62rem;margin-top:2px;">${_wRange!=null?'inimigo fora de alcance':'aproxime-se!'}</small>`
    : '';
  $('action-btns').innerHTML = `
    <button class="btn-action" ${canAttack ? '' : 'disabled'} onclick="beginAttack()"
      style="display:flex;flex-direction:column;align-items:center;gap:1px;padding:8px 6px;">
      <span>${_wRange!=null?'🏹':'⚔'} Atacar</span>
      <small style="color:var(--gold);font-size:.7rem;font-weight:bold;">${atkDieStr}${atkModStr} dano</small>
      <small style="color:var(--text2);font-size:.62rem;">${_rangeHint}</small>
      ${_adjHint}
    </button>
  `;

  const sl = $('skills-list'); sl.innerHTML = '';
  for(const sk of (me.skills || [])){
    const ok = canAct && me.mp >= sk.mp;
    const isActive = GS.pendingSkill && GS.pendingSkill.id === sk.id;
    const btn = document.createElement('button');
    btn.className = 'skill-btn' + (isActive ? ' skill-active' : '');
    btn.disabled = !ok && !isActive;
    btn.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">${sk.name}${isActive ? ' <small style="color:var(--gold);font-size:.65rem;">● aguardando alvo</small>' : ''}</div>
        <div class="skill-desc">${sk.desc}</div>
      </div>
      <div class="skill-cost">💙${sk.mp}</div>`;
    btn.onclick = () => {
      if(isActive){ GS.pendingSkill=null; renderMyPanel(GS.gameState); toast('Habilidade cancelada.','var(--text2)'); }
      else { beginSkill(sk, state); }
    };
    sl.appendChild(btn);
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
    slot.innerHTML = `
      <div class="eq-slot-label">${label}</div>
      <div class="eq-slot-emoji">${item ? item.emoji : `<span style="opacity:.35">${empty}</span>`}</div>
      <div class="eq-slot-name">${item ? item.name : '—'}</div>`;
    if(item){
      slot.appendChild(Object.assign(document.createElement('div'),
        {className:'eq-slot-x', textContent:'⤓', title:'Desequipar'}));
      slot.onclick = () => unequipSlot(key);
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
      const isConsumable = (item.item_slot === 'bag') ||
        item.effect === 'heal' || item.effect === 'mana' || item.effect === 'atk_bonus';
      const isEquippable = item.item_slot && item.item_slot !== 'bag';
      const typeLabel = {weapon:'⚔ Arma', shield:'🛡 Escudo', armor:'🛡 Armadura',
                         head:'⛑ Cabeça', ring:'💍 Anel', item:'🎒 Item',
                         accessory:'📿 Acessório', bag:'🧪 Consumível'}[item.item_slot] || '📦 Item';
      slot.className = 'bag-slot filled';
      slot.title = item.name;
      slot.innerHTML = `
        <div class="bag-slot-num">${i+1}</div>
        <div class="bag-slot-emoji">${item.emoji}</div>
        <div class="bag-slot-name">${item.name}</div>
        <div class="bag-slot-type">${typeLabel}</div>`;
      if(isEquippable){
        const btn = document.createElement('button');
        btn.className = 'bag-slot-btn equip';
        btn.textContent = '⚙ Equipar';
        btn.onclick = () => equipFromBag(i);
        slot.appendChild(btn);
      } else if(isConsumable && canAct){
        const btn = document.createElement('button');
        btn.className = 'bag-slot-btn use';
        btn.textContent = '▶ Usar';
        btn.onclick = () => useItem(item.id);
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

  // Gold
  const goldDiv = document.createElement('div');
  goldDiv.className = 'gold-display';
  goldDiv.innerHTML = `🪙 Ouro: <span>${me.gold ?? 0}</span>`;
  inv.appendChild(goldDiv);

  // End turn button
  $('btn-end-turn').disabled = !GS.isMyTurn || !me.alive || state.phase !== 'playing';
}

let _openChestId = null;   // currently-open chest id (for auto-refresh)

function openChestWindow(chest){
  _openChestId = chest.id;
  _renderChestWindow(chest);
  $('chest-overlay').classList.add('open');
}

function closeChestWindow(){
  _openChestId = null;
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
    const typeLabel = {
      weapon:'⚔ Arma', armor:'🛡 Armadura',
      accessory:'📿 Acessório', bag:'🧪 Consumível'
    }[item.item_slot] || '📦 Item';

    const row = document.createElement('div');
    row.className = 'chest-item-row';
    row.innerHTML = `
      <div class="ci-info">
        <span class="ci-emoji">${item.emoji}</span>
        <div class="ci-text">
          <div class="ci-name">${item.name}</div>
          <div class="ci-type">${typeLabel}${item.effect==='heal'?' +'+item.value+' HP':item.effect==='mana'?' +'+item.value+' MP':item.effect==='atk'?' +'+item.value+' Atq':item.effect==='def_'?' +'+item.value+' CA':''}</div>
        </div>
      </div>`;
    const btn = document.createElement('button');
    btn.className = 'chest-take-btn';
    btn.textContent = '⬆ Pegar';
    btn.disabled = isFull && item.item_slot !== 'weapon' && item.item_slot !== 'armor' && item.item_slot !== 'accessory';
    if(isFull) btn.title = 'Inventário cheio!';
    btn.onclick = () => takeFromChest(chest.id, 'item', idx);
    row.appendChild(btn);
    list.appendChild(row);
  });
}

function takeFromChest(chestId, kind, index){
  send({ type:'take_from_chest', chest_id:chestId, kind, index });
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

function move(dx,dy){ send({type:'move',dx,dy}); }

function endTurn(){ getAudioContext(); send({type:'end_turn'}); }

function useItem(itemId){ send({type:'use_item',item_id:itemId}); }

function equipFromBag(slotIndex){
  send({type:'equip_from_bag', slot_index: slotIndex});
}

function unequipSlot(slotKey){
  send({type:'unequip', slot_key: slotKey});
}

function beginAttack(){
  getAudioContext();
  const result = GS.resolveAttack();
  if(!result) return;
  if(result.type==='none'){ toast(result.reason); return; }
  if(result.type==='direct'){ send({type:'attack',target_id:result.targetId}); return; }
  // modal: multiple valid targets
  openTargetModal(result.title, result.targets, 'monster', id=>send({type:'attack',target_id:id}));
}

function beginSkill(skill, state){
  getAudioContext();
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

// Canvas mouse interactions
function canvasTile(e){
  const rect=e.target.getBoundingClientRect();
  return [Math.floor((e.clientX-rect.left)/CELL), Math.floor((e.clientY-rect.top)/CELL)];
}

$('dungeon-canvas').addEventListener('mousemove', e=>{
  if(!GS.gameState) return;
  const [tx,ty]=canvasTile(e);
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
    tip.innerHTML=`<b>${monster.emoji} ${monster.name}</b><br>HP: ${monster.hp}/${monster.max_hp} | Atk: +${monster.atk_bonus} | CA: ${monster.ac}${atkLabel}`;
    tip.style.display='block';
    tip.style.left=(e.clientX+14)+'px';
    tip.style.top=(e.clientY-10)+'px';
    $('dungeon-canvas').style.cursor=canAtk?'crosshair':'default';
    return;
  }
  const player=GS.gameState.players.find(p=>p.pos[0]===tx&&p.pos[1]===ty&&p.alive);
  if(player){
    tip.innerHTML=`<b>${player.emoji} ${player.name}</b> (Lv${player.level})<br>HP: ${player.hp}/${player.max_hp} | MP: ${player.mp}/${player.max_mp}`;
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

// Press Enter to submit name
$('input-name').addEventListener('keydown',e=>{ if(e.key==='Enter') createRoom(); });
$('input-code').addEventListener('keydown',e=>{ if(e.key==='Enter') joinRoom(); });
$('input-code').addEventListener('input',e=>{ e.target.value=e.target.value.toUpperCase(); });

// THREE.JS  3D RENDERER
// Adiciona visão isométrica 3D ao tabuleiro, sem alterar lógica de jogo.
// Toggle: botão 🎲 3D no cabeçalho do mapa.

let mode3D = false;   // 3D view active?
let g3     = null;    // Three.js renderer state (null when 2D active)

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

  // ── Scene
  const scene = new T.Scene();
  scene.background = new T.Color(VC.scene.bgColor);
  // Subtle fog — keeps depth cue without hiding explored areas
  scene.fog = new T.FogExp2(VC.scene.fogColor, VC.scene.fogDensity);

  // ── Renderer
  const renderer = new T.WebGLRenderer({ antialias:true, powerPreference:'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(CW, CH);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type    = T.PCFSoftShadowMap;
  renderer.toneMapping       = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;
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

  const floorGeo = new T.BoxGeometry(TW, TH, TW);
  const wallGeo  = new T.BoxGeometry(TW, WH, TW);

  // Warm brownish ambient — dark but not pitch-black. Areas away from torches
  // are still barely readable; the torches provide the main visible illumination.
  // Warm-white ambient — ensures shadow areas are still readable
  const ambient = new T.AmbientLight(VC.lighting.ambient.color, VC.lighting.ambient.intensity);
  scene.add(ambient);

  // Main directional — warm key light from front-right above
  const showcase = new T.DirectionalLight(VC.lighting.dirMain.color, VC.lighting.dirMain.intensity);
  showcase.position.set(...VC.lighting.dirMain.pos);
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
  const fillLight = new T.DirectionalLight(VC.lighting.dirFill.color, VC.lighting.dirFill.intensity);
  fillLight.position.set(...VC.lighting.dirFill.pos);
  scene.add(fillLight);

  // Warm back-rim — preserves silhouette readability on miniature backs
  const rimLight = new T.DirectionalLight(VC.lighting.rimLight.color, VC.lighting.rimLight.intensity);
  rimLight.position.set(...VC.lighting.rimLight.pos);
  scene.add(rimLight);

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

      if(state.tiles[y][x] === TILE_FLOOR){
        const mat = floorBaseMat.clone();
        // VC.floor.baseR (#888888) — clearly lighter than walls; emissive prevents pitch-black
        const fR = VC.floor.baseR + vf*VC.floor.baseVariance;
        mat.color.setRGB(fR, fR, fR);
        mat.emissive.set(VC.floor.emissive);
        mat.emissiveIntensity = 1.0;
        mesh = new T.Mesh(floorGeo, mat);
        mesh.position.set(x, TH/2, y);     // bottom edge sits at y = 0
        mesh.receiveShadow = true;
        mesh.userData.isFloor = true;
        mesh.userData.gridX   = x;
        mesh.userData.gridY   = y;
        mesh.userData.baseMat = mat;        // saved for restoring after highlight
      } else {
        const mat = wallBaseMat.clone();
        // VC.wall.baseR (#5a5a6a) — blue-gray stone, darker than floor; emissive keeps detail
        mat.color.setRGB(VC.wall.baseR+vw*VC.wall.variance, VC.wall.baseR+vw*VC.wall.variance, VC.wall.baseB+vw*VC.wall.varianceB);
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
  controls.maxZoom = 4.0;
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
    tileMeshes, wallDetailMeshes, entityGroup, raycaster,
    wallTorches, roomOverlayMeshes,
    sceneryMeshes, groutMeshes, groutMats,
    wetFloorMeshes,
    dustPts, dustVel: _dVel, dustXZ: _dXZ, dustY: _dY,
    dustCount: DUST_N, dustCeil: DUST_CEIL,
    W, H, animFrame:null, resizeObs,
    hoverSpot,
    stairGroup,                          // staircase mesh (null if no stairs)
    chestMeshes: {},                     // chest_id → THREE.Group
    hoveredPos:  null,   // [gx, gy] of figure under cursor, or null
    selectedPos: null    // [gx, gy] of clicked-selected figure, or null
  };

  // ── Initial camera position + first OrbitControls sync ───────────────────
  resetCamera3D();
  resize3D();
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

    // ── OrbitControls damping (must call every frame when enableDamping=true) ─
    g3.controls.update();

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

function renderMap3D(state){
  if(!state || !state.tiles) return;
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

  const { T, tileMeshes, W, H, entityGroup, sconces, torch } = g3;
  const exploredSet = new Set(state.explored.map(([x,y])=>`${x},${y}`));
  const me = state.players.find(p => p.id===GS.myPid && p.alive);
  const visionSet = computeVisionSet(state, me);

  // Reachable tiles (movement highlight)
  const reachable = new Set();
  if(GS.isMyTurn && me && me.moves_left > 0)
    bfsReachable(state.tiles, exploredSet, me.pos[0], me.pos[1], me.moves_left, reachable);

  // ── Tile visibility + emissive highlight for reachable floor tiles
  for(let y=0; y<H; y++){
    for(let x=0; x<W; x++){
      const key  = `${x},${y}`;
      const mesh = tileMeshes[key];
      if(!mesh) continue;
      const exp = exploredSet.has(key);
      mesh.visible = exp;
      if(exp && mesh.userData.isFloor){
        const mat   = mesh.userData.baseMat;
        const reach = reachable.has(key);
        // Emissive blue glow on reachable tiles — keeps texture visible
        mat.emissive.set(reach ? 0x0c2244 : 0x000000);
        mat.emissiveIntensity = reach ? 0.60 : 0.0;
        mesh.material = mat;   // ensures material reference is current
      }
    }
  }

  // ── Wall detail visibility (arches, corner columns, baseboards) ─────────────
  if(g3.wallDetailMeshes){
    for(const [key, arr] of Object.entries(g3.wallDetailMeshes))
      for(const m of arr) m.visible = exploredSet.has(key);
  }

  // ── Wall torch visibility (whole bracket group, keyed by wall tile) ──────────
  if(g3.wallTorches){
    for(const wt of g3.wallTorches)
      wt.group.visible = exploredSet.has(wt.wallKey);
  }

  // ── Room floor overlay visibility (transparent color planes) ─────────────────
  if(g3.roomOverlayMeshes){
    for(const [key, mesh] of Object.entries(g3.roomOverlayMeshes))
      mesh.visible = exploredSet.has(key);
  }

  if(g3.sceneryMeshes){
    for(const [key, arr] of Object.entries(g3.sceneryMeshes))
      for(const m of arr) m.visible = exploredSet.has(key);
  }

  // ── Glowing grout visibility (magic rune grid, trap rooms only) ───────────────
  if(g3.groutMeshes){
    for(const [key, arr] of Object.entries(g3.groutMeshes))
      for(const m of arr) m.visible = exploredSet.has(key);
  }

  // ── Wet floor reflection visibility (revealed with its floor tile) ───────────
  if(g3.wetFloorMeshes){
    for(const [key, m] of Object.entries(g3.wetFloorMeshes))
      m.visible = exploredSet.has(key);
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

  // ── Rebuild entity group
  while(entityGroup.children.length) entityGroup.remove(entityGroup.children[0]);

  // Players
  for(const p of state.players){
    if(!p.alive) continue;
    const [px,py] = p.pos;
    if(!exploredSet.has(`${px},${py}`)) continue;
    const pSel = g3.selectedPos && g3.selectedPos[0]===px && g3.selectedPos[1]===py;
    entityGroup.add(
      build3DFig(p.color, false, p.id===GS.myPid, p.id===state.current_turn, px, py, p.class_id, null, pSel)
    );
  }

  // Monsters — only visible within player's current vision radius
  for(const m of state.monsters){
    if(m.hp <= 0) continue;
    const [mx,my] = m.pos;
    if(!visionSet.has(`${mx},${my}`)) continue;
    const mSel = g3.selectedPos && g3.selectedPos[0]===mx && g3.selectedPos[1]===my;
    entityGroup.add( build3DFig('#c82020', true, false, false, mx, my, null, m.type, mSel) );
  }

  // Room icons (glowing spheres — only for un-looted/cleared non-chest rooms)
  for(const room of state.rooms){
    if(room.cleared || !exploredSet.has(`${room.cx},${room.cy}`)) continue;
    if(room.role === 'chest') continue;   // chest rooms show the 3D chest model instead
    const cols = { boss:0xff2020, trap:0xff8800 };
    const col  = cols[room.role] ?? 0xffffff;
    const geo  = new T.SphereGeometry(0.13, 8, 6);
    const mat  = new T.MeshStandardMaterial({ color:col, emissive:col, emissiveIntensity:0.75 });
    const s    = new T.Mesh(geo, mat);
    s.position.set(room.cx, 0.22+0.18, room.cy);
    entityGroup.add(s);
  }

  // Portraits are exclusive to the class selection screen (HTML). Not on the board.
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

// hexColor  — class color (#rrggbb)  isMonster — true/false
// isMe      — local player?          isCurrent — active turn?
// gx,gy     — grid coordinates       classId   — 'warrior'|'mage'|…
// mType     — 'goblin'|'orc'|…      (monster only)

function build3DFig(hexColor, isMonster, isMe, isCurrent, gx, gy, classId, mType, isSelected){
  const T   = g3.T;
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

  // Flat matte black base disc — #111111 with subtle hero-color glow from inside
  const baseR = isMonster ? 0.37 : 0.32;
  _addM(baseGrp,
    new T.CylinderGeometry(baseR, baseR+0.012, 0.074, 26),
    { color:new T.Color(VC.pawns.baseColor), roughness:1.00, metalness:0.00,
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

  // Cobblestone top — procedural canvas texture on a CircleGeometry
  const stoneTex = _getStoneTopTex(T);
  const stoneTop = new T.Mesh(
    new T.CircleGeometry(baseR - 0.012, 24),
    new T.MeshStandardMaterial({ map:stoneTex, bumpMap:stoneTex, bumpScale:0.007,
                                  roughness:0.96, metalness:0.00 })
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
    switch(mType){
      case 'goblin':    _miniGoblin(grp, clr, Y0);    break;
      case 'skeleton':  _miniSkeleton(grp, clr, Y0);  break;
      case 'orc':       _miniOrc(grp, clr, Y0);       break;
      case 'dark_mage': _miniDarkMage(grp, clr, Y0);  break;
      case 'troll':     _miniTroll(grp, clr, Y0);     break;
      case 'dragon':    _miniDragon(grp, clr, Y0);    break;
      default:          _miniGenericMonster(grp, clr, Y0); break;
    }
  } else {
    switch(classId){
      case 'warrior': _miniWarrior(grp, clr, Y0); break;
      case 'mage':    _miniMage(grp, clr, Y0);    break;
      case 'rogue':   _miniRogue(grp, clr, Y0);   break;
      case 'cleric':  _miniCleric(grp, clr, Y0);  break;
      case 'ranger':  _miniVictor(grp, clr, Y0);  break;  // Victor, O Coice Bravo
      case 'paladin': _miniPaladin(grp, clr, Y0); break;
      case 'bard':    _miniBard(grp, clr, Y0);    break;
      default:        _miniGenericHero(grp, clr, Y0); break;
    }
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

  // Individual overhead light (intensity 1.2) — each pawn is always clearly visible
  const pawnPL = new T.PointLight(0xffffff, VC.pawns.pointLightIntensity, VC.pawns.pointLightDistance);
  pawnPL.position.set(0, TH + 2.2, 0);
  pawnPL.castShadow = false;
  grp.add(pawnPL);

  grp.position.set(gx, 0, gy);
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

  // ── ILUMINAÇÃO ESPECIAL — reflexo na armadura polida ─────────────────────
  // SpotLight branca forte de cima — realça o metal polido
  const spot = new T.SpotLight(0xffffff, 1.8, 4.0, Math.PI*0.40, 0.45);
  spot.position.set(0.10, 1.80, -0.30);
  spot.target.position.set(0, Y+0.45, 0);
  g.add(spot);
  g.add(spot.target);
  // PointLight azul fraca atrás — ilumina a capa
  const capeLight = new T.PointLight(0x1a3a8f, 0.40, 2.4);
  capeLight.position.set(0, Y+0.35, 0.30);
  g.add(capeLight);
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
  // Black disc
  _cM(T,b,new T.CylinderGeometry(0.60,0.62,0.08,28),
    {color:new T.Color(0x0c0c0e),roughness:1,metalness:0},[0,0.04,0]);
  // Stone top
  const cv=document.createElement('canvas'); cv.width=cv.height=64;
  const cx=cv.getContext('2d');
  cx.fillStyle='#090909'; cx.fillRect(0,0,64,64);
  [[2,2,24,18],[28,3,20,18],[2,22,26,18],[30,23,22,16],[2,43,28,17],[32,44,22,14]].forEach(
    ([sx,sy,sw,sh])=>{
      cx.fillStyle='#111116'; cx.fillRect(sx,sy,sw,sh);
      cx.strokeStyle='#060608'; cx.lineWidth=1; cx.strokeRect(sx+.5,sy+.5,sw-1,sh-1);
    });
  const stM=new T.Mesh(new T.CircleGeometry(0.58,28),
    new T.MeshStandardMaterial({map:new T.CanvasTexture(cv),roughness:0.96,metalness:0}));
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

function _cHero(T,classId,idx){
  const g=new T.Group();
  g.userData.classId=classId; g.userData.slot=idx;
  g.position.set(_CS_X[idx],0,0);
  g.add(_cBase(T,_CS_NAMES[classId]??classId));
  const Y=0.08;
  try {
    _withSmoothGeo(T, () => {
      switch(classId){
        case 'warrior': _cWarrior(T,g,Y); break;
        case 'mage':    _cMage   (T,g,Y); break;
        case 'rogue':   _cRogue  (T,g,Y); break;
        case 'cleric':  _cCleric (T,g,Y); break;
        case 'bard':    _cBard   (T,g,Y); break;
        case 'paladin': _cPaladin(T,g,Y); break;
      }
    });
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
      {icon:'⚔',name:'Golpe Pesado',desc:'Ataque com bônus de dano massivo. Pode derrubar o alvo.'},
      {icon:'🛡',name:'Provocar',desc:'Força inimigos adjacentes a atacá-lo neste turno. Protege aliados.'},
      {icon:'💥',name:'Investida',desc:'Move 2 casas e ataca. Empurra o alvo 1 casa para trás.'},
    ]},
  mage:{ name:'PEDRO, O TÍMIDO', cls:'PEDRO', skyHex:'#0a0020', lightHex:0x8833ff,
    portrait:'assets/portraits/pedro.jpeg',
    hp:7, stats:{forca:8,destreza:12,inteligencia:18,constituicao:12},
    desc:'Domina os arcanos proibidos. Devasta grupos de inimigos com magia de área letal.',
    skills:[
      {icon:'🔥',name:'Bola de Fogo',desc:'Explosão arcana que atinge todos os inimigos no mapa.'},
      {icon:'❄',name:'Lança de Gelo',desc:'Projétil congelante que causa dano e imobiliza o alvo.'},
      {icon:'⚡',name:'Raio Arcano',desc:'Descarga elétrica instantânea de alto dano em único alvo.'},
    ]},
  rogue:{ name:'LUCCAS, O ASTUTO', cls:'LUCCAS', skyHex:'#040800', lightHex:0x44cc44,
    portrait:'assets/portraits/luccas.jpeg',
    hp:9, stats:{forca:10,destreza:18,inteligencia:10,constituicao:12},
    desc:'Morte silenciosa nas sombras. Dano crítico devastador e mobilidade inigualável.',
    skills:[
      {icon:'🗡',name:'Ataque Furtivo',desc:'Golpe preciso com +2d6 de dano furtivo extra.'},
      {icon:'💨',name:'Piscar',desc:'Teleporta até 3 casas instantaneamente. Não gasta movimento.'},
      {icon:'🎯',name:'Marcar Alvo',desc:'Próximo ataque ao alvo tem vantagem e +50% de dano.'},
    ]},
  cleric:{ name:'FRADE LEWIS', cls:'FRADE LEWIS', skyHex:'#140c00', lightHex:0xffdd44,
    portrait:'assets/portraits/lewis.jpeg',
    hp:10, stats:{forca:10,destreza:10,inteligencia:16,constituicao:14},
    desc:'Guardião da luz divina. Cura aliados, expulsa mortos-vivos e abençoa o grupo.',
    skills:[
      {icon:'✨',name:'Cura',desc:'Restaura 2d6+2 HP de um aliado adjacente ou si mesmo.'},
      {icon:'☀',name:'Luz Sagrada',desc:'Explosão de luz: dano sagrado a todos os inimigos na sala.'},
      {icon:'🙏',name:'Bênção',desc:'Concede +2 nas rolagens a todos os aliados por 2 turnos.'},
    ]},
  bard:{ name:'HENRIQUE, O BARDO', cls:'HENRIQUE', skyHex:'#0a0005', lightHex:0xff66cc,
    portrait:'assets/portraits/henrique.jpeg',
    hp:9, stats:{forca:10,destreza:16,inteligencia:12,constituicao:12},
    desc:'Alma da taverna, terror do calabouço. Inspira aliados e confunde inimigos com sua música.',
    skills:[
      {icon:'🎵',name:'Balada Curativa',desc:'Melodia mágica que cura todos os aliados em cena.'},
      {icon:'🎭',name:'Confundir',desc:'Inimigo perde sua próxima ação (Salvaguarda de Int).'},
      {icon:'🎸',name:'Inspirar',desc:'Aliado escolhido ganha um movimento extra este turno.'},
    ]},
  paladin:{ name:'RICHARD, O CAVALEIRO', cls:'RICHARD', skyHex:'#0e0a00', lightHex:0xeeeeff,
    portrait:'assets/portraits/richard.jpeg',
    hp:12, stats:{forca:16,destreza:10,inteligencia:10,constituicao:14},
    desc:'Aço e honra forjados na mesma bigorna. Richard não conhece recuo — apenas o peso do escudo e a clareza do dever.',
    skills:[
      {icon:'⚡',name:'Golpe Divino',desc:'Ataque + 2d6 de dano sagrado. Crítico automático vs. mortos-vivos.'},
      {icon:'🌟',name:'Aura Protetora',desc:'Todos os aliados adjacentes ganham +2 CA até próximo turno.'},
      {icon:'🛡',name:'Imposição de Mãos',desc:'Cura 1d8+3 HP tocando um aliado adjacente.'},
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
  renderer.shadowMap.type    = T.PCFSoftShadowMap;
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
    animFrame:    null,
    tweens:       [],
    confirmStart: Date.now(),
    confirmShown: false,
    raycaster:    new T.Raycaster(),
  };

  renderer.domElement.addEventListener('mousemove',  _csfMouseMove);
  renderer.domElement.addEventListener('click',      _csfClick);
  renderer.domElement.addEventListener('mouseleave', _csfMouseLeave);

  _startCsfLoop();
  _csfShowPanel(defaultSel, false);
  document.getElementById('cs-hint').textContent = 'Escolha seu herói — clique para selecionar';
}

function _buildCsfPillar(T, parent, isCenter){
  const h  = isCenter ? 0.22 : 0.18;
  const r  = isCenter ? 0.52 : 0.44;
  const stone = new T.MeshStandardMaterial({color:new T.Color(0x2a2530), roughness:0.88, metalness:0.15});
  const capM  = new T.MeshStandardMaterial({color:new T.Color(0x3a3040), roughness:0.72, metalness:0.28});
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
  csf.renderer.domElement.style.cursor = csf.hoveredId ? 'pointer' : 'default';
}
function _csfClick(e){
  if(!csf) return;
  const id = _csfPick(e);
  if(id) csfSelectHero(id);
}
function _csfMouseLeave(){ if(csf) csf.hoveredId = null; }

function csfSelectHero(classId){
  if(!csf || classId === csf.selectedId) return;
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

  document.getElementById('cs-skills').innerHTML = d.skills.map(sk=>`
    <div class="cs-skill">
      <span class="cs-skill-icon">${sk.icon}</span>
      <div class="cs-skill-body">
        <div class="cs-skill-name">${sk.name}</div>
        <div class="cs-skill-desc">${sk.desc}</div>
      </div>
    </div>
  `).join('');

  const panel = document.getElementById('cs-panel');
  if(panel) panel.classList.add('ready');
}

function csUpdateLobbyBar(msg){
  const codeEl = document.getElementById('cs-room-code');
  if(codeEl) codeEl.textContent = msg.code || '----';

  const row = document.getElementById('cs-players-row');
  if(row) row.innerHTML = msg.players.map(p=>{
    const isMe = p.id === GS.myPid;
    const rdy  = !!p.class_id;
    return `<span class="cs-player-chip${isMe?' me':''}${rdy?' ready':''}">${p.name}${p.id===msg.host?' ♛':''}</span>`;
  }).join('');

  const btnS = document.getElementById('cs-btn-start');
  if(btnS) btnS.style.display = (msg.host===GS.myPid && msg.can_start) ? 'block' : 'none';
}

function csConfirmClass(){
  if(!csf || !csf.selectedId) return;
  send({type:'select_class', class_id: csf.selectedId});
  toast(`${_CSD[csf.selectedId]?.cls ?? csf.selectedId} selecionado!`, 'var(--gold)');
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

// ── 3D click handler: delegates to unified handleTileClick ───────────────────
// Guard: if the pointer moved while any button was held (orbit / pan / dolly),
// the mousedown → mousemove → mouseup sequence is a camera gesture, not a tap.
// Consume the synthetic click event and reset the flag for the next interaction.

function on3DClick(e){
  if(_orbitDragMoved){ _orbitDragMoved = false; return; }
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
    tip.innerHTML=`<b>${monster.emoji} ${monster.name}</b><br>HP ${monster.hp}/${monster.max_hp} | CA ${monster.ac}` +
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

  const action = GS.resolveTileClick(tx, ty);
  if(!action) return; // nothing to do (null = consume silently)
  switch(action.type){
    case 'skill_blocked':
      toast('⚠ Este ataque requer inimigo cardinalmente adjacente!', 'var(--orange)');
      break;
    case 'skill':
      send({type:'skill', skill_id:action.skillId, target_id:action.targetId});
      GS.pendingSkill = null;
      renderMyPanel(GS.gameState);
      break;
    case 'attack':
      send({type:'attack', target_id:action.targetId});
      break;
    case 'move':
      for(const [dx,dy] of action.path) send({type:'move', dx, dy});
      break;
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

GS.on('lobbyState',  msg => handleLobby(msg));

GS.on('gameStart', () => {
  destroyClassSelectFull();
  showScreen('screen-city');
  // Proactively request city_state — handles cases where the first one was lost
  setTimeout(()=>{ if(!GS.cityState) send({type:'get_city_state'}); }, 400);
});

GS.on('cityState', msg => {
  // If returning from dungeon to city, tear down the 3D renderer first
  if(g3){ dispose3D(); mode3D = false; }
  // Ensure city screen is visible (covers both initial arrival and return from dungeon)
  showScreen('screen-city');
  handleCityState(msg);
});

GS.on('shopResult',  msg =>
  toast(msg.msg.replace(/\*\*(.+?)\*\*/g,'$1'), 'var(--green)'));

GS.on('enterDungeon', () => {
  destroyCity3D();
  showScreen('screen-game');
  // Auto-enable 3D when entering the dungeon (if Three.js is available)
  if(window.THREE && !mode3D) toggle3D();
});

GS.on('gameState', msg => {
  handleGameState(msg);
  // Auto-refresh open chest window (contents may have changed)
  if(_openChestId){
    const updatedChest = (msg.chests||[]).find(c=>c.id===_openChestId);
    if(updatedChest) _renderChestWindow(updatedChest);
    else closeChestWindow();   // chest was emptied and removed
  }
});

GS.on('gmNarration', text => appendGM(text));

GS.on('gameOver',    msg  => handleGameOver(msg));

GS.on('diceRoll',    msg  => handleDiceRoll(msg));

GS.on('serverError', msg  => toast(msg));