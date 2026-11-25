// Menu de ações do turno (Magias | Habilidades | Encerrar turno) e card de quem está agindo.
// Verificações estáticas sobre game.js + a lógica pura do espelho de habilidades, rodada em node.
// Roda da raiz: node tools/test_menu_acoes.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const raiz = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8').split('\r\n').join('\n');
const lang = fs.readFileSync(path.join(raiz, 'src/lang/interface.js'), 'utf8');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };

// [1] o retrato do monstro virou função e a iniciativa a usa (um lugar só)
ok(/function _retratoDoAtor\(actor, monster\)/.test(game), 'falta _retratoDoAtor');
ok(/const portrait = _retratoDoAtor\(actor, monster\);/.test(game), 'iniciativa não usa _retratoDoAtor');
ok(/_retratoDoAtor\(a, outro\.monster\)/.test(game), 'card da vez não usa _retratoDoAtor');
ok((game.match(/retratos\/monstros\/lobo_cinzento\.png/g) || []).length === 1, 'tabela de retratos duplicada');

// [2] a barra existe no template e é sincronizada depois do painel de habilidades
ok(/<div id="turn-actions-bar" hidden><\/div>/.test(game), 'container da barra ausente');
const fimPainel = game.indexOf('  // End turn button\n  _atualizarBotaoEncerrarTurno(state);');
ok(fimPainel > 0 && game.slice(fimPainel, fimPainel + 200).includes('_barraSincronizar();'),
  'renderMyPanel não sincroniza a barra');

// [3] ordem dos botões: Magias (só mago/clérigo) antes de Habilidades, depois Encerrar turno
const iMag = game.indexOf('data-menu="magias" data-gamepad-action');
const iHab = game.indexOf('data-menu="habilidades" data-gamepad-action');
const iFim = game.indexOf('class="tam-tab tam-end"');
ok(iMag > 0 && iMag < iHab && iHab < iFim, 'ordem dos botões incorreta');
ok(/hero\.class_id === 'mage' \|\| hero\.class_id === 'cleric'/.test(game), 'Magias deve ser só de mago/clérigo');

// [4] descrição só depois de 1,5 s; passivas fora; indisponível escurecido (is-off), não removido
ok(/_BARRA_TIP_MS = 1500/.test(game), 'atraso da descrição deve ser 1500 ms');
ok(/passivaTxt\.includes\(m\)\)\) continue/.test(game), 'passivas devem ficar fora da lista');
ok(/'tam-icon' \+ \(h\.off \? ' is-off' : ''\)/.test(game), 'indisponível deve ficar escurecido');

// [5] chaves de idioma com pt e en
for (const k of ['habilidades', 'magias', 'encerrar', 'sem_habilidades', 'em_recarga', 'indisponivel', 'vez_de']) {
  const m = lang.match(new RegExp('"ui\\.menuacoes\\.' + k + '":[^\\n]*'));
  ok(m && /"en":/.test(m[0]) && /"pt":/.test(m[0]), 'chave ui.menuacoes.' + k + ' sem pt/en');
}

// [6] ouvintes únicos: a barra não registra GS.on
const trecho = game.slice(game.indexOf('// ── Barra de ações do turno'), game.indexOf('function renderTurnHeroHud'));
ok(!/GS\.on\(/.test(trecho), 'a barra não deve registrar GS.on (um ouvinte por evento)');

console.log('test_menu_acoes: ' + n + ' verificações OK');
