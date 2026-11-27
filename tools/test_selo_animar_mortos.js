// O selo de efeito ativo mostra o NOME do Animar Mortos, não o id cru.
// Roda da raiz: node tools/test_selo_animar_mortos.js
'use strict';
const U = require('./js_teste_util');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

const GAME = U.ler('game.js');
function efeitos(extraCtx) {
  const r = U.executar(GAME, ['_coletarEfeitosAtivos'], Object.assign({
    GS: { myPid: 'p', guildCatalogFor: () => [] },
    window: {},
    t: k => '«' + k + '»',
    ABILITY_ICON_ASSETS: { animar_mortos: 'x.png' },
    GRIMORIO_CLIENT: {},
    MODIFICADORES_METAMAGIA: [],
    _zonasEscuridaoComDesvantagem: () => [],
    _efeitosVisuaisSuprimidos: new Set(),
    _efeitosVisuaisLocais: new Map(),
  }, extraCtx));
  const player = { id: 'p', class_id: 'mage', alive: true, skills: [] };
  return r.api._coletarEfeitosAtivos({ players: [player] }, player);
}

console.log('\n[1] Mirando o Animar Mortos');
let e = efeitos({ window: { _modoAnimarMortos: true } }).find(x => x.id === 'animar_mortos');
check('o selo aparece', !!e);
check('com o nome traduzido, não o id cru', !!e && e.nome === '«ui.animar.nome_curto»');

console.log('\n[2] Registrado como efeito visual local (o caminho da ficha e da barra)');
e = efeitos({ _efeitosVisuaisLocais: new Map([['p:animar_mortos', { id: 'animar_mortos', kind: 'skill', playerId: 'p' }]]) })
  .find(x => x.id === 'animar_mortos');
check('também com o nome traduzido', !!e && e.nome === '«ui.animar.nome_curto»');

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
