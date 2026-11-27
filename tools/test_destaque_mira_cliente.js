// Destaque de mira das reações elementais — lado do cliente.
// Roda da raiz: node tools/test_destaque_mira_cliente.js
// A paridade das CASAS com o servidor está em tools/test_destaque_mira.py; aqui: criaturas afetadas,
// o _reagePrever real do game.js (extraído e executado) e a fiação (hooks, pools 3D, desenho 2D, textos).
'use strict';
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
const GAME = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8').split('\r\n').join('\n');
const MOD = fs.readFileSync(path.join(raiz, 'src', 'reacoesElementais.js'), 'utf8');
const U = require('./js_teste_util');
let PASS = 0, FAIL = 0;
function check(nome, cond) { if (cond) { PASS++; console.log('  ✅ ' + nome); } else { FAIL++; console.log('  ❌ ' + nome); } }

global.window = {};
eval(MOD + '; window.ReacoesElementais');
const RE = window.ReacoesElementais;

function fnSource(nome) {
  const i = GAME.indexOf('function ' + nome + '(');
  if (i < 0) throw new Error('função não encontrada: ' + nome);
  let d = 0;
  for (let k = GAME.indexOf('{', i); k < GAME.length; k++) {
    if (GAME[k] === '{') d++;
    else if (GAME[k] === '}') { d--; if (!d) return GAME.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + nome);
}

const agua = (x0, x1, y) => { const o = {}; for (let x = x0; x <= x1; x++) o[`${x},${y}`] = 'agua'; return o; };
const mundo = (extra) => Object.assign({
  materiais: {}, zonas_especiais: [], rooms: [], tiles: [], pontes: [], players: [], monsters: [],
}, extra || {});

console.log('\n[1] criaturas que sofreriam dano');
{
  const st = mundo({
    materiais: agua(3, 9, 5),
    players: [{ id: 'a', pos: [3, 5], hp: 10, alive: true }, { id: 'b', pos: [6, 5], hp: 10, alive: true },
              { id: 'v', pos: [7, 5], hp: 10, alive: true, altura: 2 }, { id: 'f', pos: [3, 9], hp: 10, alive: true }],
    monsters: [{ id: 'm', pos: [8, 5], hp: 8 }, { id: 'morto', pos: [9, 5], hp: 0 }],
  });
  const casas = [[3, 5]];
  const prev = RE.preverReacoes(st, 'lightning', casas);
  const alvos = RE.alvosDasReacoes(st, prev, casas, null).map(c => c.join(','));
  check('choque: quem está na poça e não levou o golpe é afetado', alvos.includes('6,5') && alvos.includes('8,5'));
  check('choque: quem levou o golpe direto não repete', !alvos.includes('3,5'));
  check('choque: criatura voando e criatura fora d\'água ficam de fora', !alvos.includes('7,5') && !alvos.includes('3,9'));
  check('choque: morto não conta', !alvos.includes('9,5'));
}
{
  const st = mundo({
    materiais: { '5,5': 'piche', '6,5': 'piche', '9,5': 'piso_congelado' },
    players: [{ id: 'a', pos: [6, 5], hp: 10, alive: true }, { id: 'g', pos: [9, 5], hp: 10, alive: true }],
  });
  const casas = [[5, 5]];
  const prev = RE.preverReacoes(st, 'fire', casas);
  const alvos = RE.alvosDasReacoes(st, prev, casas, null).map(c => c.join(','));
  check('ignição: criatura na mancha de piche sofre', alvos.includes('6,5'));
  check('degelo não causa dano: criatura sobre o gelo longe do fogo fica sem anel', !alvos.includes('9,5'));
}
{
  const tiles = Array.from({ length: 12 }, (_, y) => Array.from({ length: 12 }, (_, x) => (x >= 1 && x <= 8 && y >= 1 && y <= 8 ? 1 : 0)));
  const st = mundo({ tiles, rooms: [{ id: 0, x: 1, y: 1, w: 8, h: 8 }],
    zonas_especiais: [{ tipo: 'camara_gas', room_id: 0, ativa: true }],
    players: [{ id: 'a', pos: [2, 2], hp: 10, alive: true }, { id: 'v', pos: [5, 5], hp: 10, alive: true, altura: 2 },
              { id: 'fora', pos: [10, 10], hp: 10, alive: true }] });
  const prev = RE.preverReacoes(st, 'fire', [[3, 3]]);
  const alvos = RE.alvosDasReacoes(st, prev, [[3, 3]], null).map(c => c.join(','));
  check('gás: todos na sala sofrem, inclusive quem voa', alvos.includes('2,2') && alvos.includes('5,5'));
  check('gás: quem está fora da sala não', !alvos.includes('10,10'));
}
{
  const st = mundo({ materiais: { '5,5': 'agua', '6,5': 'agua' },
    monsters: [{ id: 'g', pos: [5, 5], hp: 30, grande: true }] });
  const tilesDe = c => [[c.pos[0], c.pos[1]], [c.pos[0] + 1, c.pos[1]]];
  const prev = RE.preverReacoes(st, 'cold', [[5, 5]]);
  const alvos = RE.alvosDasReacoes(st, prev, [[5, 5]], tilesDe).map(c => c.join(','));
  check('footprint: criatura grande marca todas as casas dela', alvos.includes('5,5') && alvos.includes('6,5'));
}

console.log('\n[2] _reagePrever do game.js (executado)');
{
  const src = ['_anelDaAreaMira', '_reagePrever', '_reageSufixo'].map(fnSource).join('\n');
  const consts = GAME.slice(GAME.indexOf('const _ELEMENTO_MIRA_MAGIA'), GAME.indexOf('// A Prisão de Chamas só acende a borda'));
  const montar = (state, modo) => {
    const ctx = { ReacoesElementais: RE, window: { ReacoesElementais: RE, _spellHL: { area: new Set(), double: new Set(), reage: undefined }, ...modo },
      GS: { gameState: state, monsterTiles: m => [m.pos] }, t: (k, p) => k + (p ? '(' + p.n + ')' : '') };
    const keys = Object.keys(ctx);
    const api = new Function(...keys, consts + '\n' + src + '\nreturn {prever:_reagePrever, anel:_anelDaAreaMira, sufixo:_reageSufixo};')(...keys.map(k => ctx[k]));
    return { api, hl: ctx.window._spellHL, win: ctx.window };
  };
  const st = mundo({ materiais: agua(3, 9, 5), players: [{ id: 'b', pos: [6, 5], hp: 10, alive: true }] });
  let { api, hl } = montar(st, { _modoMagia: { magiaId: 'relampago' } });
  api.prever(new Set(['3,5', '4,5']));
  check('Relâmpago sobre a poça: reação de choque com as 7 casas', hl.reage && hl.reage.tipos.choque && hl.reage.tipos.choque.size === 7);
  check('anel na criatura que seria atingida', hl.reage && hl.reage.alvos.has('6,5'));
  check('texto da mira cita o choque e a contagem', hl.reage && hl.reage.texto === 'ui.mira.reage.choque(7)');
  check('sufixo só aparece quando a mira é válida', api.sufixo(true).includes('choque') && api.sufixo(false) === '');
  ({ api, hl } = montar(st, { _modoMagia: { magiaId: 'raio_congelante' } }));
  api.prever(new Set(['6,5']));
  check('Raio Congelante numa casa d\'água: congelamento', hl.reage && hl.reage.tipos.congelar && hl.reage.tipos.congelar.has('6,5'));
  ({ api, hl } = montar(st, { _modoMagia: { magiaId: 'bola_fogo' } }));
  api.prever(new Set(['6,5']));
  check('Bola de Fogo sobre água comum: nada reage', hl.reage === null);
  ({ api, hl } = montar(st, { _modoMagia: { magiaId: 'cura' } }));
  api.prever(new Set(['6,5']));
  check('magia sem elemento: nada reage', hl.reage === null);
  const stPiche = mundo({ materiais: { '5,5': 'piche', '6,5': 'piche' } });
  ({ api, hl } = montar(stPiche, { _modoThrowItem: { id: 'frasco_oleo', area: 0 } }));
  api.prever(new Set(['5,5']));
  check('Frasco de Óleo no piche: ignição da mancha', hl.reage && hl.reage.tipos.ignicao && hl.reage.tipos.ignicao.size === 2);
  ({ api, hl } = montar(stPiche, { _modoThrowItem: { id: 'frasco_piche', area: 1 } }));
  api.prever(new Set(['5,5']));
  check('Frasco de Piche (sem elemento): nada reage', hl.reage === null);
  ({ api, hl } = montar(stPiche, { _modoThrowItem: { id: 'fogo_grego', area: null } }));
  api.prever(new Set(['6,5']));
  check('Fogo Grego (alvo único) no piche: ignição', hl.reage && hl.reage.tipos.ignicao);
  const quadro = new Set(); for (let x = 4; x <= 6; x++) for (let y = 4; y <= 6; y++) quadro.add(`${x},${y}`);
  const anel = api.anel(quadro);
  check('anel da Prisão de Chamas: a borda do 3x3 (8 casas), sem o centro', anel.size === 8 && !anel.has('5,5'));
  api.prever(new Set());
  check('área vazia limpa o destaque', hl.reage === null);
}

console.log('\n[3] fiação no game.js');
// Olha o comportamento e o conteúdo, não a forma exata das linhas (js_teste_util).
{
  const magia = U.constante(GAME, '_ELEMENTO_MIRA_MAGIA'), item = U.constante(GAME, '_ELEMENTO_MIRA_ITEM');
  check('Relâmpago/Bola/Prisão/Raio Congelante mapeados', magia.relampago === 'lightning' && magia.bola_fogo === 'fire'
    && magia.prisao_chamas === 'fire' && magia.raio_congelante === 'cold');
  check('óleo, Fogo Grego e Bomba Incendiária mapeados (piche não)', item.frasco_oleo === 'fire' && item.fogo_grego === 'fire'
    && item.bomba_incendiaria === 'fire' && !('frasco_piche' in item));
  // As duas recomputações de área, EXECUTADAS: as prévias recebem a área antes do desenho.
  const previasAntesDoDesenho = (r) => {
    const nomes = r.chamadas.map(c => c.nome), area = r.ctx.window._spellHL.area;
    const iDes = nomes.indexOf('_aplicarSpellHL');
    return iDes >= 0 && ['_reagePrever', '_atingidosPrever'].every(n => {
      const i = nomes.indexOf(n);
      return i >= 0 && i < iDes && r.chamadas[i].args[0] === area;
    });
  };
  const rM = U.executar(GAME, ['_recomputarAreaMagia'], {
    window: { _modoMagia: { magiaId: 'x', alvoTipo: 'foe' }, _spellHL: {} },
    GRIMORIO_CLIENT: { x: {} }, GS: { me: { pos: [1, 1] } } });
  rM.api._recomputarAreaMagia(4, 5);
  check('_recomputarAreaMagia calcula a prévia antes de aplicar', rM.ctx.window._spellHL.area.has('4,5') && previasAntesDoDesenho(rM));
  const rT = U.executar(GAME, ['_recomputarAreaThrow'], {
    window: { _modoThrowItem: { area: 1 }, _spellHL: {} },
    _addCheb(cx, cy, r, out) { out.add(`${cx},${cy}`); } });
  rT.api._recomputarAreaThrow(2, 3);
  check('_recomputarAreaThrow calcula a prévia', rT.ctx.window._spellHL.area.has('2,3') && previasAntesDoDesenho(rT));
  check('arremesso de alvo único calcula a prévia no hover', U.chamadas(U.funcao(GAME, '_aimHoverThrow')).includes('_reagePrever'));
  check('status da mira ganha o texto da reação (magia e arremesso)',
    U.chamadas(U.funcao(GAME, '_aimHoverMagic')).includes('_reageSufixo') && U.chamadas(U.funcao(GAME, '_aimHoverThrow')).includes('_reageSufixo'));
  check('limpeza: _aimSetHighlights e a limpeza geral zeram o destaque', (GAME.match(/_spellHL\.reage\s*=\s*null/g) || []).length >= 2);
  check('3D: um pool por tipo de reação + pool de anéis', /spellReageMeshes\[tp\]\s*=\s*_mkSpell\(/.test(GAME) && /spellReageAlvoMeshes\s*=\s*_mkOverlayPool\(/.test(GAME));
  const g3 = U.bloco(GAME, 'g3 = {');
  check('3D: pools entram no objeto g3', /\bspellReageMeshes\b/.test(g3) && /\bspellReageAlvoMeshes\b/.test(g3));
  check('3D: toggle recebe lista (nunca null: o filtro de visibilidade espalha o argumento)', !/spellReage[A-Za-z]*, hl\.reage[^;]*\|\| null\)/.test(GAME));
  const hl3d = U.funcao(GAME, '_aplicarSpellHL3D');
  check('3D: _aplicarSpellHL3D alterna os pools de reação', hl3d.includes('spellReageMeshes') && hl3d.includes('spellReageAlvoMeshes')
    && U.chamadas(hl3d).includes('toggle'));
  const hl2d = U.funcao(GAME, '_desenharSpellHL2D');
  check('2D: _desenharSpellHL2D pinta cor, ícone e anel', hl2d.includes('hl.reage') && hl2d.includes('_REAGE_ICONE') && hl2d.includes('reage.alvos'));
  const icones = U.constante(GAME, '_REAGE_ICONE');
  check('os 5 tipos têm cor 2D, cor 3D, ícone e texto', ['choque', 'ignicao', 'congelar', 'gas', 'derreter'].every(k =>
    typeof icones[k] === 'string' && new RegExp(`${k}: n => t\\('ui\\.mira\\.reage\\.${k}'`).test(GAME)));
}
check('index.html carrega o módulo (já existente)', fs.readFileSync(path.join(raiz, 'index.html'), 'utf8').includes('src/reacoesElementais.js'));

console.log('\n[4] idiomas');
const lang = fs.readFileSync(path.join(raiz, 'src', 'lang', 'interface.js'), 'utf8').replace(/\r?\n/g, ' ');
for (const k of ['choque', 'ignicao', 'congelar', 'gas', 'derreter']) {
  const chave = '"ui.mira.reage.' + k + '"';
  const i = lang.indexOf(chave);
  const trecho = i >= 0 ? lang.slice(i, i + 260) : '';
  check('ui.mira.reage.' + k + ' pt+en com {n}', i >= 0 && trecho.includes('"pt"') && trecho.includes('"en"') && (trecho.match(/\{n\}/g) || []).length >= 2);
}

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
