/* Guardas de interação do inspetor de monstro em canvas 2D e 3D. */
const fs = require('fs');
const src = fs.readFileSync('game.js', 'utf8');
const stateSrc = fs.readFileSync('src/gameState.js', 'utf8');
const check = (name, condition) => {
  console.log(`${condition ? '✅' : '❌'} ${name}`);
  if (!condition) process.exitCode = 1;
};

const compact2d = src.match(/const monster=_masterMonsterAtTileClient\(GS\.gameState, tx, ty\);([\s\S]*?)\n  const player=/)?.[1] || '';
const monster3dAt = src.lastIndexOf('const monster = _masterMonsterAtTileClient(GS.gameState, tx, ty);');
const compact3d = monster3dAt >= 0 ? src.slice(monster3dAt, src.indexOf('const player = GS.gameState.players', monster3dAt)) : '';
const context2d = src.match(/\$\('dungeon-canvas'\)\.addEventListener\('contextmenu',[\s\S]*?\n\}\);/)?.[0] || '';
const context3d = src.match(/domEl\.addEventListener\('contextmenu',[\s\S]*?\n  \}\);/)?.[0] || '';
const openInspect = src.match(/function _abrirInspecaoMonstro\(tx,ty\)\{([\s\S]*?)\n\}/)?.[1] || '';
const currentInspect = src.match(/function _inspectedMonster\(state\)\{([\s\S]*?)\n\}/)?.[1] || '';

console.log('[1] hover permanece compacto e sem área de perigo');
check('2D não injeta ficha completa no hover', !compact2d.includes('fichaInimigoTooltipHTML'));
check('3D não injeta ficha completa no hover', !compact3d.includes('fichaInimigoTooltipHTML'));
check('hover não mostra aviso textual de ameaça', !compact2d.includes('ui.perigo.possivel') && !compact3d.includes('ui.perigo.possivel'));
check('há resumo curto de nome, vida e CA', src.includes('function _monsterTooltipCompactHTML('));

console.log('[2] botão direito abre inspeção nas duas vistas');
check('2D bloqueia menu do navegador e inspeciona a casa', context2d.includes('preventDefault') && context2d.includes('_abrirInspecaoMonstro'));
check('3D distingue clique direito de arrasto', context3d.includes('_rightClickPointer') && context3d.includes('_abrirInspecaoMonstro'));
check('ficha detalhada usa o nível atual de conhecimento', /fichaInimigoTooltipHTML\(monster, bard, null, level\)/.test(src));
check('conhecimento não depende mais de bestiário no game_state', !/gameState\?\.bestiary/.test(src));
check('clique direito solicita conhecimento privado ao servidor', /GS\.inspectMonster\?\.\(monster\.id\)/.test(src));
check('resposta privada atualiza apenas o monstro inspecionado', /GS\.on\('monsterKnowledgeState',[\s\S]*?String\(msg\.monster_id\)!==String\(_inspectedMonsterId\)/.test(src));
check('cliente encaminha pedido/resposta de conhecimento', /type: 'inspect_monster'/.test(stateSrc) && /case 'monster_knowledge_state'/.test(stateSrc));
check('modo Mestre/teste pode abrir o inspetor', !/GS\.isMaster\(\)|state\?\.test_mode/.test(openInspect));
check('modo Mestre/teste mantém áreas após abrir', !/GS\.isMaster\(\)|state\.test_mode/.test(currentInspect));

console.log('[3] inspeção pode ser encerrada pelo jogador');
check('Escape fecha a inspeção', /e\.key === 'Escape'[\s\S]{0,100}_fecharInspecaoMonstro\(\)/.test(src));
check('painel tem botão acessível de fechar', src.includes('monster-inspector-close') && src.includes('data-gamepad-action="activate"'));
