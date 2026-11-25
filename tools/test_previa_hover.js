// Prévia de alcance no hover (habilidades/magias) e faixa de dano na previsão de ataque.
// Roda da raiz: node tools/test_previa_hover.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const raiz = path.join(__dirname, '..');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };

global.WebSocket = class { constructor() { this.readyState = 1; } send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: '', protocol: 'http:', host: 'x' };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, 'src/gameState.js'), 'utf8') + '; GS');

// [1] faixa de dano: mín–máx de um acerto comum
let f = GS.faixaDanoPrevisao({dano_dado: '1d8', dano_fixo: 3});
ok(f.min === 4 && f.max === 11, '1d8+3 deve ser 4–11, veio ' + JSON.stringify(f));
f = GS.faixaDanoPrevisao({dano_dado: '2d6', dano_fixo: 0, golpe_mult: 1.5});
ok(f.min === 3 && f.max === 18, '2d6×1,5 deve ser 3–18, veio ' + JSON.stringify(f));
f = GS.faixaDanoPrevisao({dano_dado: '1d6', dano_fixo: 2, furtivo_d4: 2});
ok(f.min === 5 && f.max === 16, '1d6+2+2d4 deve ser 5–16, veio ' + JSON.stringify(f));
f = GS.faixaDanoPrevisao({dano_dado: '1d4', dano_fixo: -5});
ok(f.min === 1 && f.max === 1, 'piso de dano 1, veio ' + JSON.stringify(f));
f = GS.faixaDanoPrevisao(null);
ok(f.min === 0 && f.max === 0, 'sem previsão devolve 0–0');
// a média fica sempre dentro da faixa
for (const p of [{dano_dado: '1d10', dano_fixo: 4}, {dano_dado: '3d6', dano_fixo: 1, golpe_mult: 2}]) {
  const fx = GS.faixaDanoPrevisao(p), med = GS.danoMedioPrevisao(p);
  ok(fx.min <= med && med <= fx.max, 'média fora da faixa para ' + JSON.stringify(p));
}

// [2] fiação no game.js
const game = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8').split('\r\n').join('\n');
ok(/function _previaAlcanceMostrar\(alcance\)/.test(game), 'falta _previaAlcanceMostrar');
ok(/if\(_aimSessionState\.current\) return;\n  const me = GS\.me;/.test(game), 'a prévia não pode rodar durante uma mira');
ok(/function _barraFechar\(\)\{\n  _barraMenuAberto = null;\n  _previaAlcanceLimpar\(\);/.test(game), 'fechar o menu deve limpar a prévia');
ok(/mouseenter', \(\) => _previaAlcanceMostrar\(h\.alcance\)/.test(game), 'habilidades sem hover de alcance');
ok(/mouseenter', \(\) => _previaAlcanceMostrar\(alc\)/.test(game), 'magias sem hover de alcance');
ok(/dataset\.alcance = '1'/.test(game) && /dataset\.alcance = '4'/.test(game), 'técnicas com alvo sem alcance');
ok(/btn\.dataset\.alcance = String\(item\.throw_range/.test(game), 'arremesso de arma sem alcance');
ok(/GS\.faixaDanoPrevisao\(prev\)/.test(game), 'tooltip não usa a faixa de dano');

// [3] magias sem anel de alcance (auto-lançadas, linha, cone, área centrada)
const m = game.match(/function _alcancePreviaMagia\(m, me\)\{[\s\S]*?\n\}/)[0];
for (const t of ['buff_self', 'utilidade', 'reacao', 'invocacao', 'area_centrada', 'linha_reflexiva', 'cone'])
  ok(m.includes("'" + t + "'"), 'tipo sem anel não listado: ' + t);

console.log('test_previa_hover: ' + n + ' verificações OK');

// [4] ícones de status no card (extrai a lógica pura do game.js e roda em node)
{
  const src = game.match(/function _condicoesDoCard\(a\)\{[\s\S]*?\n\}\nfunction _statusCardHTML/)[0].replace(/function _statusCardHTML$/, '');
  const t = k => ({'ui.condicao.sangramento':'Sangramento','ui.condicao.ferida_aberta_titulo':'Ferida aberta','ui.condicao.hemorragia':'Hemorragia',
    'ui.hud.resumo_chamas':'Em chamas','ui.hud.resumo_acido':'Ácido','ui.hud.resumo_veneno':'Veneno','ui.hud.resumo_sono':'Dormindo',
    'ui.hud.resumo_paralisia':'Paralisia','ui.hud.resumo_cegueira':'Cegueira','ui.condicao.petrificacao':'Petrificação',
    'ui.status.card.medo':'Amedrontado','ui.status.card.lento':'Lento'}[k] || k);
  const condicoes = new Function('t', src + '; return _condicoesDoCard;')(t);
  ok(condicoes(null).length === 0 && condicoes({}).length === 0, 'sem condições deve devolver lista vazia');
  let c = condicoes({sangramento_nivel: 2, sangramento_rodadas: 3, em_chamas_rodadas: 2, efeitos_veneno: [{duracao: 4}, {duracao: 1}]});
  ok(c.length === 3, 'esperava 3 condições, veio ' + c.length);
  ok(c[0].nome === 'Sangramento' && c[0].valor === 'N2' && c[0].rodadas === 3, 'sangramento: nível e duração');
  ok(c[1].nome === 'Em chamas' && c[1].rodadas === 2, 'chamas com duração');
  ok(c[2].nome === 'Veneno' && c[2].valor === '×2' && c[2].rodadas === 4, 'veneno: contagem e maior duração');
  c = condicoes({ferida_aberta: true, hemorragia: true, com_medo: true, medo_rodadas: 2, lento: true, lento_rodadas: 1});
  ok(c.map(x => x.nome).join() === 'Ferida aberta,Hemorragia,Amedrontado,Lento', 'condições sem duração e medo/lento');
  ok(condicoes({sangramento_nivel: 0, em_chamas_rodadas: 0, efeitos_veneno: []}).length === 0, 'zeros não geram ícone');
  ok(/\$\{_statusCardHTML\(hero\)\}\$\{_renderRecursosRodada\(hero, state, true\)\}/.test(game), 'card do herói sem status');
  ok(/\$\{_statusCardHTML\(a\)\}\$\{_renderRecursosRodada\(a, state, true\)\}/.test(game), 'card de outro herói sem status');
  ok(/<\/div><\/div>\$\{_statusCardHTML\(a\)\}/.test(game), 'card de monstro sem status');
}
console.log('test_previa_hover (com status): ' + n + ' verificações OK');
