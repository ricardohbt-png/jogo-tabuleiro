// Regression tests for the cooperative-marker client protocol and input wiring.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
let PASS = 0, FAIL = 0;
const check = (name, ok) => { if (ok) { PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } };
const sent = [];
let socket;
global.WebSocket = class { constructor() { this.readyState = 1; socket = this; } send(raw) { sent.push(JSON.parse(raw)); } close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: '', protocol: 'http:', host: 'localhost' };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(root, 'src/gameState.js'), 'utf8') + '; GS');
GS.connect('ws://localhost', 'Ana', 'create');

console.log('\n[1] Protocolo de marcador');
check('expõe criação de marcador', typeof GS.createCooperativeMarker === 'function');
if (GS.createCooperativeMarker) {
  check('envia categoria e alvo tile', GS.createCooperativeMarker('danger', 'tile', [3, 4]) === true);
  const tile = sent.filter(x => x.type === 'cooperative_marker').pop();
  check('serializa pos sem campos de alvo extra', tile?.category === 'danger' && tile?.target_type === 'tile' && tile?.pos?.join(',') === '3,4' && !('target_id' in tile));
  check('valida categoria e formato do alvo antes de enviar', GS.createCooperativeMarker('bogus', 'tile', [1, 1]) === false && GS.createCooperativeMarker('attack', 'enemy', '') === false);
  check('serializa inimigo por ID', GS.createCooperativeMarker('attack', 'enemy', 'skel-1') === true && sent.filter(x => x.type === 'cooperative_marker').pop()?.target_id === 'skel-1');
}
check('expõe sincronização da preferência de visão', typeof GS.setCooperativeVisionPreference === 'function');
if (GS.setCooperativeVisionPreference) {
  GS.setCooperativeVisionPreference(true);
  check('envia preferência efêmera ao servidor', sent.filter(x => x.type === 'cooperative_vision_preference').pop()?.enabled === true);
}

console.log('\n[2] Integração de seleção');
const game = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
check('modo de seleção intercepta o clique antes de ações normais', /function handleTileClick\(tx, ty\)\{[\s\S]{0,350}_handleCooperativeMarkerTarget\(tx, ty\)/.test(game));
check('modo de seleção intercepta clique 3D antes da mira de habilidades', /function on3DClick\(e\)\{[\s\S]{0,240}_handleCooperativeMarkerTarget[\s\S]{0,100}return;/.test(game));
check('Escape cancela a seleção de marcador', /Escape[\s\S]{0,180}_cancelCooperativeMarkerTarget/.test(game));
check('controle de categorias oferece foco de teclado e gamepad', /data-cooperative-marker-category[\s\S]{0,180}data-gamepad-action="activate"/.test(game));
check('preferência é reportada ao entrar no estado de masmorra', /function handleGameState\(msg\)\{[\s\S]{0,1200}setCooperativeVisionPreference/.test(game));
const lang = fs.readFileSync(path.join(root, 'src/lang/interface.js'), 'utf8');
check('rótulos localizados em português e inglês', lang.includes('ui.marker.attack') && lang.includes('ui.marker.danger') && lang.includes('ui.marker.investigate') && lang.includes('ui.marker.move'));
console.log(`\n${'='.repeat(56)}\n  ${PASS} passaram, ${FAIL} falharam\n${'='.repeat(56)}`);
process.exit(FAIL ? 1 : 0);
