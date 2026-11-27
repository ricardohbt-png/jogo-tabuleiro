// O menu ⚔️ Habilidades da barra mostra o Animar Mortos do Pedro (habilidade de classe,
// que não mora na lista de habilidades do painel). Roda da raiz: node tools/test_barra_animar_mortos.js
'use strict';
const U = require('./js_teste_util');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

const GAME = U.ler('game.js');
function menu(me, opts = {}) {
  const r = U.executar(GAME, ['_habilidadesEspelhadas'], {
    document: { getElementById: () => ({ querySelectorAll: () => [] }) },
    GS: { me, isMyTurn: opts.vez !== false, myPid: 'p', guildOwnedOf: () => ({ especializacoes: opts.especs || [] }) },
    t: (k, p) => k + (p ? JSON.stringify(p) : ''),
    ABILITY_ICON_ASSETS: { animar_mortos: 'x.png' },
    abilityIconHtml: (id, emoji) => `<img data-id="${id}">`,
  });
  return { itens: r.api._habilidadesEspelhadas(), chamadas: r.chamadas };
}

console.log('\n[1] Pedro vê Animar Mortos no menu');
let m = menu({ class_id: 'mage', alive: true, action_done: false });
const animar = m.itens.find(h => h.nome === 'ui.animar.nome_curto');
check('o item aparece', !!animar);
check('com descrição e custo', !!animar && animar.desc && /ui\.animar\.custo_por_uso/.test(animar.custo));
check('disponível na vez, com a ação principal livre', !!animar && animar.off === false);
animar && animar.orig.click();
check('o clique faz o mesmo que a ficha (usarAnimarMortos)',
  m.chamadas.some(c => c.nome === 'usarAnimarMortos' && c.args.length === 0));
check('sem a especialização, não há Senhor da Morte', !m.itens.some(h => h.nome === 'ui.animar.senhor_da_morte'));

console.log('\n[2] Indisponível fora da vez ou com a ação principal gasta');
check('fora da vez: esmaecido', menu({ class_id: 'mage', alive: true }, { vez: false }).itens.find(h => h.nome === 'ui.animar.nome_curto').off === true);
check('ação principal gasta: esmaecido', menu({ class_id: 'mage', alive: true, action_done: true }).itens.find(h => h.nome === 'ui.animar.nome_curto').off === true);

console.log('\n[3] Senhor da Morte com a especialização');
m = menu({ class_id: 'mage', alive: true }, { especs: ['mago_reviver_4'] });
const senhor = m.itens.find(h => h.nome === 'ui.animar.senhor_da_morte');
check('o item aparece', !!senhor);
senhor && senhor.orig.click();
check('o clique usa a versão Senhor da Morte',
  m.chamadas.some(c => c.nome === 'usarAnimarMortos' && c.args[0] === 'senhor_da_morte'));

console.log('\n[4] Outras classes não ganham o item');
check('guerreiro: nada de Animar Mortos', !menu({ class_id: 'warrior', alive: true }).itens.some(h => h.nome === 'ui.animar.nome_curto'));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
