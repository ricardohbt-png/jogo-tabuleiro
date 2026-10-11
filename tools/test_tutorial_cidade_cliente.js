// Executa as funções reais do passeio com armazenamento e interface isolados.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const source = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
function func(nome) {
  const inicio = source.indexOf(`function ${nome}(`);
  assert(inicio >= 0);
  const fim = source.indexOf('\nfunction ', inicio + 1);
  return source.slice(inicio, fim);
}
let dados = {status: 'done', etapa: 4, execucao: 'antiga'};
let exibicoes = 0;
const contexto = {
  _cidadeTourLer: () => dados,
  _cidadeTourSalvar: value => { dados = value; },
  _cidadeTourTentarMostrar: () => { exibicoes++; },
  _cidadeTourLimparDestaques: () => {},
  _CIDADE_TOUR_PARADAS: [1, 2, 3, 4],
  GS: {activeShop: false},
  document: {getElementById: () => null},
};
vm.createContext(contexto);
vm.runInContext(func('_cidadeTourIniciarOuRetomar') + '\n' + func('_cidadeTourConcluir'), contexto);
contexto._cidadeTourIniciarOuRetomar(true, 'nova');
assert.equal(dados.status, 'active');
assert.equal(dados.etapa, 0);
assert.equal(exibicoes, 1);
dados.etapa = 2;
contexto._cidadeTourIniciarOuRetomar(true, 'nova');
assert.equal(dados.etapa, 2, 'atualização da cidade preserva etapa');
contexto._cidadeTourConcluir();
assert.equal(dados.status, 'done');
assert.equal(dados.execucao, 'nova');
contexto._cidadeTourIniciarOuRetomar(true, 'nova');
assert.equal(dados.status, 'done', 'reconexão não repete passeio concluído');
contexto._cidadeTourIniciarOuRetomar(true, 'outra');
assert.equal(dados.status, 'active', 'nova conclusão do treinamento oferece novo passeio');
contexto._cidadeTourConcluir(true);
contexto._cidadeTourIniciarOuRetomar(true, 'outra');
assert.equal(dados.status, 'skipped', 'pular é respeitado durante a mesma execução');
console.log('OK: passeio reinicia por missão e preserva progresso, conclusão e dispensa.');
