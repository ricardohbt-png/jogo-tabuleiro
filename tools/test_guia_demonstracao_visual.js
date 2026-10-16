const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const codigo = fs.readFileSync(path.join(__dirname, '..', 'src', 'guiaDemonstracaoVisual.js'), 'utf8');
const contextoVm = { window: {} };
vm.runInNewContext(codigo, contextoVm);
const criar = contextoVm.window.GuiaDemonstracaoVisual.criar;

function cronometro() {
  let agora = 0, sequencia = 0;
  const pendentes = new Map();
  return {
    agora: () => agora,
    agendar: fn => { const id = ++sequencia; pendentes.set(id, fn); return id; },
    cancelarAgendamento: id => pendentes.delete(id),
    quadro: ms => {
      agora = ms;
      const fila = [...pendentes.values()];
      pendentes.clear();
      fila.forEach(fn => fn(agora));
    },
    pendentes: () => pendentes.size
  };
}

const clock = cronometro();
const amostras = [];
let fins = 0;
const demo = criar({
  agendar: clock.agendar,
  cancelarAgendamento: clock.cancelarAgendamento,
  agora: clock.agora,
  aoQuadro: amostra => amostras.push(amostra),
  aoFim: () => { fins++; }
});
const op = { acao: 'prever_movimento', alvo: 'casa:[5,15]' };

assert.strictEqual(demo.iniciar(op, { origem: [1, 2] }), true, 'inicia operação visual válida');
assert.strictEqual(amostras[0].progresso, 0, 'primeira amostra começa em zero');
assert.deepStrictEqual(amostras[0].contexto.origem, [1, 2], 'contexto segue para o renderizador');
clock.quadro(300);
clock.quadro(800);
assert.deepStrictEqual(amostras.map(x => x.progresso), [0, 0.25, 2 / 3], 'progresso cresce de forma monotônica');
clock.quadro(1200);
assert.strictEqual(amostras.at(-1).progresso, 1, 'progresso termina em um');
assert.strictEqual(fins, 1, 'fim chamado exatamente uma vez');
assert.strictEqual(demo.ativo(), false, 'timeline encerra');

assert.strictEqual(demo.iniciar(op, null), true, 'pode repetir como uma animação nova');
assert.strictEqual(amostras.at(-1).progresso, 0, 'repetição começa novamente em zero');
assert.strictEqual(demo.cancelar(), true, 'cancelamento encerra a animação');
assert.strictEqual(clock.pendentes(), 0, 'cancelamento limpa o quadro agendado');
demo.cancelar();
assert.strictEqual(clock.pendentes(), 0, 'cancelar repetidamente é idempotente');

const antes = amostras.length;
assert.strictEqual(demo.iniciar({ acao: 'atacar', alvo: 'boneco' }, null), false, 'operação não visual é rejeitada');
assert.strictEqual(demo.ativo(), false, 'operação inválida deixa timeline inativa');
assert.strictEqual(clock.pendentes(), 0, 'operação inválida não agenda quadro');
assert.strictEqual(amostras.length, antes, 'operação inválida não emite amostra');
console.log('6 verificações da timeline visual passaram');
