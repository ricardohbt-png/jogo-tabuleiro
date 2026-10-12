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

console.log('\n[3] Dados do marcador para renderização');
const viewSource = game.match(/function _cooperativeMarkerView\(state, visionSet\)\{[\s\S]*?\n\}/)?.[0];
const styleSource = game.match(/function _cooperativeMarkerStyle\(category\)\{[\s\S]*?\n\}/)?.[0];
check('helper de renderização filtra marcadores inválidos', !!viewSource);
check('mapeia categorias para ícones distintos', !!styleSource);
if (viewSource && styleSource) {
  const markerView = new Function('TILE_WALL', `${viewSource}\n${styleSource}\nreturn { _cooperativeMarkerView, _cooperativeMarkerStyle };`)(0);
  const state = {tiles:[[1,1,1],[1,1,1],[1,1,1]], monsters:[{id:'orc',hp:4,pos:[1,1]}], cooperative_markers:[
    {owner_id:'a',category:'attack',target_type:'enemy',target_id:'orc',pos:[1,1]},
    {owner_id:'b',category:'danger',target_type:'tile',pos:[0,0]},
    {owner_id:'c',category:'move',target_type:'tile',pos:[2,2]},
    {owner_id:'d',category:'investigate',target_type:'enemy',target_id:'gone',pos:[1,1]},
  ]};
  let visible = markerView._cooperativeMarkerView(state, new Set(['1,1','0,0']));
  check('aplica visão do destinatário antes de desenhar', visible.length === 2 && visible.every(m => m.x === 1 || (m.x === 0 && m.y === 0)));
  check('remove alvo morto ou ausente', !visible.some(m => m.target_id === 'gone'));
  check('posição de inimigo segue a posição autorizada pelo servidor', visible.find(m => m.target_id === 'orc')?.x === 1 && visible.find(m => m.target_id === 'orc')?.y === 1);
  state.cooperative_markers[0].pos = [2,2];
  visible = markerView._cooperativeMarkerView(state, new Set(['2,2','0,0']));
  check('posição atualizada do alvo acompanha o próximo estado', visible.find(m => m.target_id === 'orc')?.x === 2 && visible.find(m => m.target_id === 'orc')?.y === 2);
  const icons = ['attack','danger','investigate','move'].map(c => markerView._cooperativeMarkerStyle(c)?.icon);
  check('cada categoria possui glyph próprio e alto contraste', icons.every(Boolean) && new Set(icons).size === 4);
}
check('camada 2D desenha os marcadores por cima do mapa', /_drawCooperativeMarkers2D\(ctx, state, visionSet\)/.test(game));
check('camada 3D sincroniza sprites filtrados no fim do render', /_syncCooperativeMarkers3D\(state, visionSet\)/.test(game));
check('sprites 3D são descartados quando removidos e ao encerrar a cena', game.includes('_clearCooperativeMarkerSprites3D(g3.cooperativeMarkerGroup)'));
check('botão B cancela seleção antes dos outros modos', /function _gamepadCancel\(\)\{[\s\S]{0,260}_cancelCooperativeMarkerTarget\(\)/.test(game));
check('armar marcador limpa prévia de movimento pendente', /function _armCooperativeMarker\(category\)\{[\s\S]{0,320}_cancelarPreviaMovimento\(\{silent:true\}\)/.test(game));
check('teclado navega e confirma alvo durante a marcação', /const move = \{ArrowUp:[\s\S]{0,1200}_handleCooperativeMarkerTarget/.test(game));
check('cursor de alvo é desenhado sem depender de controle conectado', /function _drawCooperativeMarkers2D\([\s\S]{0,1800}_cooperativeMarkerCursor[\s\S]{0,500}strokeRect/.test(game));
check('movimentar cursor em modo marcador não recria prévia de movimento', /function _gamepadAtualizarPreviaMovimento\(state\)\{[\s\S]{0,100}_cooperativeMarkerMode/.test(game));
check('confirmação do controle prioriza alvo do marcador', /function _gamepadAccept\(state\)\{[\s\S]{0,300}_handleCooperativeMarkerTarget[\s\S]{0,300}if\(GS\.pendingMove\)/.test(game));
console.log(`\n${'='.repeat(56)}\n  ${PASS} passaram, ${FAIL} falharam\n${'='.repeat(56)}`);
process.exit(FAIL ? 1 : 0);
