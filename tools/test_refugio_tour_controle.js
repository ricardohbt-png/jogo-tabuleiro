// O cartão do tour da Fazenda (#refugio-tour-card) só recebe o controle quando
// não há outra janela aberta: ele fica no fim do body e, antes, roubava a
// navegação de uma loja aberta depois dele.
// Rodar: node tools/test_refugio_tour_controle.js
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const src = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
const ini = src.indexOf('function _gamepadUiScope(){');
const fim = src.indexOf('\n}\n', ini) + 3;
const codigo = src.slice(ini, fim);

let falhas = 0;
function check(cond, msg){ console.log((cond ? '  ok  ' : '  FALHOU  ') + msg); if(!cond) falhas++; }

function rodar(abertos){
  const tela = {id: 'screen-city'};
  const ctx = {
    document: {
      getElementById: () => null,
      querySelectorAll: () => abertos,
      querySelector: () => tela,
    },
    _gamepadLayerVisible: () => true,
  };
  vm.createContext(ctx);
  vm.runInContext(codigo + '\nthis.r = _gamepadUiScope();', ctx);
  return ctx.r;
}

const loja = {id: 'shop-modal'};
const cartao = {id: 'refugio-tour-card'};
const mapa = {id: 'worldmap-overlay'};

check(rodar([cartao]) === cartao, 'sozinho, o cartão recebe o controle (passo do mapa)');
check(rodar([loja, cartao]) === loja, 'com uma loja aberta, a loja fica com o controle');
check(rodar([mapa, cartao]) === mapa, 'com o mapa-múndi aberto, o mapa fica com o controle');
check(rodar([]).id === 'screen-city', 'sem nada aberto, volta à tela ativa');

console.log(falhas ? `\n${falhas} falha(s)` : '\nOK');
process.exit(falhas ? 1 : 0);
