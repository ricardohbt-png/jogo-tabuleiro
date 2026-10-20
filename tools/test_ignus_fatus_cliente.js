// Regressions for illusion placement, movement input, and visual lifecycle.
'use strict';
const fs = require('fs');
const path = require('path');
const source = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let pass = 0, fail = 0;
function check(label, ok) {
  if (ok) { pass++; console.log('  ✅ ' + label); }
  else { fail++; console.log('  ❌ ' + label); }
}
function body(name) {
  const start = source.indexOf(`function ${name}(`);
  if (start < 0) return '';
  const brace = source.indexOf('{', start);
  let depth = 0;
  for (let i = brace; i < source.length; i++) {
    if (source[i] === '{') depth++;
    if (source[i] === '}' && --depth === 0) return source.slice(brace + 1, i);
  }
  return '';
}

console.log('\n[1] Mira e colocação');
const placement = body('_illusionPlacementTiles');
check('há cálculo local de casas livres dentro de alcance e linha de visão',
  !!placement && placement.includes('hasLineOfSight')
    && placement.includes('pos') && placement.includes('6')
    && placement.includes('_illusionTileBlocked'));
check('a prévia exclui decorações sólidas e entulho',
  body('_illusionTileBlocked').includes('decorTilesOf')
    && body('_illusionTileBlocked').includes('pisavel')
    && body('_illusionTileBlocked').includes('entulho'));
check('usar os dois itens inicia seleção no tabuleiro sem enviar antes da escolha',
  body('useItem').includes('_iniciarMiraIlusao')
    && body('_iniciarMiraIlusao').includes("'illusion_placement'")
    && body('_clickTileIlusao').includes('target_pos')
    && body('useItem').indexOf('_iniciarMiraIlusao') < body('useItem').indexOf("send({type:'use_item'"));
check('clique inválido não envia item e Escape cancela a mira',
  body('_clickTileIlusao').includes('mode.valid?.has(key)')
    && body('_clickTileIlusao').includes('target_pos')
    && body('_aimStart').includes("event.key !== 'Escape'"));

console.log('\n[2] Movimento da Fata Morgana');
check('o turno oferece mover ou pular somente antes do herói agir',
  body('_promptarMovimentoIlusao').includes('current_turn')
    && body('_promptarMovimentoIlusao').includes('move_order_round')
    && body('_promptarMovimentoIlusao').includes('action_done')
    && body('_iniciarMiraIlusao').includes('confirmText'));
check('a confirmação envia move_illusion com destino e o botão de pular envia destino nulo',
  body('_clickTileIlusao').includes("type:'move_illusion'")
    && body('_clickTileIlusao').includes('illusion_id')
    && body('_pularMovimentoIlusao').includes("type:'move_illusion'")
    && body('_pularMovimentoIlusao').includes('target_pos:null'));
check('clique, teclado e gamepad usam o mesmo caminho de seleção',
  source.includes('if(_illusionMode){ _clickTileIlusao(tx,ty); return; }')
    && body('_teclaModoIlusao').includes('_clickTileIlusao')
    && body('_gamepadAccept').includes('handleTileClick')
    && body('_gamepadCancel').includes('_pularMovimentoIlusao'));

console.log('\n[3] Arte e remoção da cena');
check('2D desenha os PNGs dos itens com opacidade fantasmagórica no Ignus',
  body('_getIllusion2DImg').includes('assets/itens/')
    && body('_drawIllusions2D').includes('${illusion.kind}.png')
    && body('_drawIllusions2D').includes('globalAlpha'));
check('3D reconcilia os sprites pela lista de game_state.illusions',
  body('_syncIllusions3D').includes('state.illusions')
    && body('_syncIllusions3D').includes('assets/itens/')
    && body('_syncIllusions3D').includes('scene.remove'));
check('game_state inicia o aviso e encerra uma seleção quando o turno já avançou',
  body('handleGameState').includes('_promptarMovimentoIlusao')
    && body('handleGameState').includes('_aimEnd'));

console.log('\n[4] renderMap3D usa visionSet só depois de declará-lo (TDZ)');
const r3d = body('renderMap3D');
check('_syncIllusions3D vem depois de "let visionSet"',
  r3d.indexOf('let visionSet') >= 0 && r3d.indexOf('_syncIllusions3D(state,visionSet)') > r3d.indexOf('let visionSet'));

console.log('\n[5] Uso pela bolsa: fecha o inventário e pinta as casas válidas de verde');
const usar = body('useItem');
check('useItem fecha a bolsa antes da mira de ilusão (senão o clique no mapa cai no modal e cancela)',
  /illusion_lure[\s\S]{0,400}InventoryModal\.close\(\)[\s\S]{0,120}_iniciarMiraIlusao\('placement'/.test(usar));
const mira = body('_iniciarMiraIlusao');
check('as casas válidas vão no canal verde (area) e o alcance no vermelho (range)',
  /area:\s*valid/.test(mira) && /range:\s*placement\s*\?\s*_illusionRangeTiles\(me\)/.test(mira));
check('a mira recusa fora do turno ou sem ação bônus, como nos arremessáveis',
  /!GS\.isMyTurn\s*\|\|\s*me\.bonus_action_used/.test(mira));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
