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
  body('_ilusaoComOrdemDisponivel').includes('current_turn')
    && body('_ilusaoComOrdemDisponivel').includes('move_order_round')
    && body('_ilusaoComOrdemDisponivel').includes('action_done')
    && body('_promptarMovimentoIlusao').includes('_ilusaoComOrdemDisponivel')
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
check('2D desenha a réplica do herói (frente.png da classe do dono), translúcida e mais etérea no Ignus',
  body('_illusionClassId').includes('class_id')
    && body('_illusionGhostCanvas').includes('_getHero2DImg')
    && body('_drawIllusions2D').includes('_illusionGhostCanvas')
    && body('_drawIllusions2D').includes('globalAlpha')
    && body('_illusionGhostStyle').includes("'ignus_fatus'"));
check('3D mostra o PNG do herói (assets/pawns/<classe>/frente.png), não o ícone do item',
  body('_syncIllusions3D').includes('assets/pawns/')
    && body('_syncIllusions3D').includes('frente.png')
    && !body('_syncIllusions3D').includes('assets/itens/')
    && body('_syncIllusions3D').includes('state.illusions')
    && body('_syncIllusions3D').includes('scene.remove'));
check('a seta de intenção nomeia a ilusão (não "um aliado") quando o alvo é uma ilusão',
  source.includes("t('ui.ilusao.alvo_tooltip'"));
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

console.log('\n[6] Janela de movimento da Fata Morgana (antes de o herói mover/agir)');
const vm = require('vm');
const sbx = { GS: { isMyTurn: true, myPid: 'p1' } };
vm.createContext(sbx);
vm.runInContext(source.slice(source.indexOf('function _rodadaDoEstado('), source.indexOf('// Botão para reabrir a ordem')), sbx);
const estado = (extra = {}, illusion = {}) => ({
  phase: 'playing', current_turn: 'p1', round: 3,            // o game_state manda `round`, não `round_num`
  players: [{ id: 'p1', alive: true, moved_this_turn: false, action_done: false, ...extra }],
  illusions: [{ id: 'i1', owner_pid: 'p1', kind: 'fata_morgana', ...illusion }],
});
const disponivel = st => vm.runInContext('_ilusaoComOrdemDisponivel', sbx)(st);
check('ilusão recém-criada (sem ordem na rodada) abre a janela com o campo `round` do estado',
  disponivel(estado())?.id === 'i1');
check('ordem já dada nesta rodada fecha a janela', disponivel(estado({}, { move_order_round: 3 })) === null);
check('ordem de uma rodada anterior não impede a desta', disponivel(estado({}, { move_order_round: 2 }))?.id === 'i1');
check('depois que o herói move, a janela fecha', disponivel(estado({ moved_this_turn: true })) === null);
check('depois que o herói age, a janela fecha', disponivel(estado({ action_done: true })) === null);
check('o Ignus Fatus nunca abre a janela', disponivel(estado({}, { kind: 'ignus_fatus' })) === null);
check('existe o botão para reabrir a ordem depois de um Esc',
  body('_mostrarBotaoMoverIlusao').includes('ilusao-mover-btn') && body('_iniciarMiraIlusao').includes("reason==='cancel'"));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
