// Fluxo real dos handlers visuais do Fosso, sem DOM ou WebGL.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
const scene = fs.readFileSync(path.join(root, 'src/combatScene.js'), 'utf8');
function extract(name) {
  const start = source.indexOf(`function ${name}(`);
  const end = source.indexOf('\nfunction ', start + 1);
  if (start < 0 || end < 0) throw new Error(`Handler ausente: ${name}`);
  return source.slice(start, end);
}
function setup() {
  const ctx = vm.createContext({console, performance: {now: () => 1000},
    GS: {myPid: 'p1', gameState: {players: [{id: 'p1', pos: [5, 5]}]}},
    mode3D: false, g3: null, _scheduleVisualFrame: () => 1,
    _armadilhaPos: msg => msg.pos, _armadilhaTileVisivel: () => true});
  ctx.window = ctx;
  vm.runInContext(scene, ctx);
  vm.runInContext(source.slice(source.indexOf('const _armadilhaAnims ='),
    source.indexOf('function _buracoQuedaPose2D(')) +
    ['_armadilhaId', '_armadilhaStyle', '_receberDisparoFosso',
      '_receberAnimacaoArmadilha'].map(extract).join('\n') +
    '\nfunction _tickBuracoQueda2D() {}\nfunction _tickArmadilhas2D() {}', ctx);
  return ctx;
}
let failed = 0, passed = 0;
function check(label, value) {
  if (value) {passed++; console.log('OK ' + label);}
  else {failed++; console.error('FALHOU ' + label);}
}
const event = {tipo_id: 'fosso', pos: [5, 5], alvos: ['p1']};
const hidden = {players: [{id: 'p1', pos: [5, 5], fosso_oculto: true}]};
const visible = {players: [{id: 'p1', pos: [5, 5]}]};
{
  const ctx = setup(); ctx._receberDisparoFosso(event);
  check('miniatura desce verticalmente durante a queda',
    ctx.CombatScene.poseFor('p:p1', 1450)?.dy < 0);
  check('disparo abre um fosso vazio, sem estacas', vm.runInContext(
    "_armadilhaAnims.some(a => a.style.kind === 'spike_pit' && a.style.variant === 'empty')", ctx));
  ctx._sincronizarFossoQuedas(hidden);
  check('900 ms encerram a descida sem revelar o herói preso',
    ctx.CombatScene.poseFor('p:p1', 2500)?.opacity === 0);
  ctx._sincronizarFossoQuedas(visible);
  check('fim da condição libera pose e ocultação local',
    ctx.CombatScene.poseFor('p:p1', 2500) === null &&
    vm.runInContext('_fossoQuedaDisparos.size === 0 && _buracoQuedas.size === 0', ctx));
  ctx._receberAnimacaoArmadilha({...event, sucesso: false, target_id: 'p1'});
  check('resultado privado não reinicia uma queda já encerrada',
    ctx.CombatScene.poseFor('p:p1', 2500) === null);
  ctx._receberDisparoFosso(event);
  check('uma nova queda após recuperação pode animar normalmente',
    ctx.CombatScene.pitFallActiveFor('p:p1', 1100));
}
{
  const ctx = setup(); ctx._receberDisparoFosso(event);
  ctx._sincronizarFossoQuedas(visible);
  check('primeiro estado já liberado não deixa ocultação permanente',
    ctx.CombatScene.poseFor('p:p1', 2500) === null &&
    vm.runInContext('_fossoQuedaDisparos.size === 0', ctx));
}
{
  const ctx = setup();
  ctx._receberAnimacaoArmadilha({...event, sucesso: true});
  check('sucesso no Reflexos não abre buraco nem inicia queda',
    ctx.CombatScene.poseFor('p:p1', 1500) === null &&
    vm.runInContext('_armadilhaAnims.length === 0', ctx));
  ctx._receberAnimacaoArmadilha({...event, sucesso: false});
  check('resultado privado sem condição de fosso não oculta o peão',
    ctx.CombatScene.poseFor('p:p1', 1500) === null);
}
console.log(`${passed} passaram, ${failed} falharam`);
process.exitCode = failed ? 1 : 0;
