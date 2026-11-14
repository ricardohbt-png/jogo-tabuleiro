// Venenos aprimorados no cliente: o id do frasco melhorado (`<base>__upgrade__<cd>_<pot>_<dur>`)
// nao existe no catalogo estatico, entao nome, descricao e tipo de acao sao montados a partir do
// veneno-base. Antes o painel Envenenar e o status mostravam o id cru e o tooltip dizia
// "acao principal" para o frasco (que gasta acao bonus).
//
// Roda da raiz:  node tools/test_venenos_aprimorados_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const raiz = path.join(__dirname, '..');
const SRC = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
const check = (nome, cond) => { if (cond) { PASS++; console.log('  ✅ ' + nome); } else { FAIL++; console.log('  ❌ ' + nome); } };

// Dicionario real (todos os src/lang/*.js), para o `t` de teste ser o do jogo.
const ctx = vm.createContext({ window: {} });
const arquivos = fs.readdirSync(path.join(raiz, 'src', 'lang')).filter(f => f.endsWith('.js'))
  .sort((a, b) => (a === 'strings.js' ? -1 : b === 'strings.js' ? 1 : a.localeCompare(b)));
for (const f of arquivos)
  vm.runInContext(fs.readFileSync(path.join(raiz, 'src', 'lang', f), 'utf8'), ctx);
const dic = ctx.window.LANG_STRINGS || {};
let idioma = 'pt';
const t = (k, p) => {
  const e = dic[k];
  if (!e) return k;
  return String(e[idioma] ?? e.pt).replace(/\{(\w+)\}/g, (_, n) => (p && p[n] !== undefined ? p[n] : '{' + n + '}'));
};

function bloco(nome) {
  const i = SRC.indexOf('function ' + nome + '(');
  if (i < 0) throw new Error('funcao nao encontrada: ' + nome);
  let d = 0;
  for (let k = SRC.indexOf('{', SRC.indexOf(')', i)); k < SRC.length; k++) {
    if (SRC[k] === '{') d++;
    else if (SRC[k] === '}') { d--; if (!d) return SRC.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + nome);
}
function constante(nome) {
  const i = SRC.indexOf('const ' + nome + ' =');
  if (i < 0) throw new Error('const nao encontrada: ' + nome);
  return SRC.slice(i, SRC.indexOf(';', i) + 1);
}

const catalogo = {
  veneno_fungo_acre: { nome: 'Fungo Acre', descricao: 'Fortitude CD 10 anula. Se falhar: 1 dano por rodada.' },
  veneno_escorpiao_pedra: { nome: 'Veneno do Escorpião Pedra', descricao: '-1 ataque, -1 movimento.' },
};
const GS = { me: { bag: [], gear: {} }, CATALOGO_ITENS: catalogo };
const BONUS_ACTION_EFFECTS = new Set(['heal', 'coat_poison', 'antidote']);
const _acaoEconomiaMeta = tipo => ({ tipo, label: 'x.' + tipo });

const codigo = [
  constante('_VENENO_MELHORIA_CD'), constante('_VENENO_MELHORIA_POTENCIA'), constante('_VENENO_MELHORIA_DURACAO'),
  bloco('_partesVenenoId'), bloco('_sufixoMelhoriasVeneno'), bloco('_nomeVenenoBaseDesconhecido'),
  bloco('_nomeVenenoPorId'), bloco('_descricaoVenenoPorId'), bloco('_itemAcaoMeta'),
  'return {_partesVenenoId,_sufixoMelhoriasVeneno,_nomeVenenoPorId,_descricaoVenenoPorId,_itemAcaoMeta};',
].join('\n');
const F = new Function('t', 'GS', 'window', 'BONUS_ACTION_EFFECTS', '_acaoEconomiaMeta', codigo)(
  (k, p) => t(k, p), GS, { GS }, BONUS_ACTION_EFFECTS, _acaoEconomiaMeta);

console.log('[1] id do frasco');
{
  const p = F._partesVenenoId('veneno_fungo_acre__upgrade__mortal_concentrado_prolongado');
  check('separa base e melhorias', p.base === 'veneno_fungo_acre' && p.cd === 'mortal'
    && p.potencia === 'concentrado' && p.duracao === 'prolongado' && p.melhorado);
  const b = F._partesVenenoId('veneno_fungo_acre');
  check('veneno comum nao e melhorado', !b.melhorado && b.base === 'veneno_fungo_acre');
}

console.log('[2] nome');
{
  check('comum: nome do catalogo', F._nomeVenenoPorId('veneno_fungo_acre') === 'Fungo Acre');
  check('melhorado: nome-base + melhoria (nunca o id)',
    F._nomeVenenoPorId('veneno_fungo_acre__upgrade__aprimorado_nenhum_nenhum') === 'Fungo Acre Aprimorado');
  check('todas as melhorias, em ordem cd/potencia/duracao',
    F._nomeVenenoPorId('veneno_escorpiao_pedra__upgrade__avancado_fortalecido_destilado')
      === 'Veneno do Escorpião Pedra Avançado Fortalecido Destilado');
  check('o maximo vira Fatal',
    F._nomeVenenoPorId('veneno_fungo_acre__upgrade__mortal_concentrado_prolongado') === 'Fungo Acre Fatal');
  idioma = 'en';
  check('em ingles a melhoria e traduzida',
    F._nomeVenenoPorId('veneno_fungo_acre__upgrade__aprimorado_nenhum_prolongado') === 'Fungo Acre Improved Prolonged');
  idioma = 'pt';
  check('nenhuma saida contem "__upgrade__"',
    !F._nomeVenenoPorId('veneno_fungo_acre__upgrade__mortal_nenhum_nenhum').includes('__upgrade__'));
}

console.log('[3] veneno criado no editor (fora do catalogo estatico)');
{
  GS.me.bag = [{ id: 'ensaio_sobre_a_cegueira__upgrade__mortal_nenhum_nenhum', veneno_id: 'ensaio_sobre_a_cegueira__upgrade__mortal_nenhum_nenhum',
    name: 'Ensaio sobre a Cegueira Mortal', effect: 'coat_poison' }];
  check('usa o nome do frasco que o jogador carrega',
    F._nomeVenenoPorId('ensaio_sobre_a_cegueira__upgrade__mortal_nenhum_nenhum') === 'Ensaio sobre a Cegueira Mortal');
  check('o veneno-base sem frasco vira nome legivel, nao o id',
    !F._nomeVenenoPorId('veneno_desconhecido_x').includes('veneno_'));
  GS.me.bag = [];
}

console.log('[4] descricao');
{
  check('comum: descricao do catalogo', F._descricaoVenenoPorId('veneno_fungo_acre').startsWith('Fortitude CD 10'));
  const d = F._descricaoVenenoPorId('veneno_fungo_acre__upgrade__aprimorado_concentrado_prolongado');
  check('melhorado: mantem a do veneno-base', d.startsWith('Fortitude CD 10'));
  check('melhorado: resume CD, efeito e duracao', d.includes('CD +2') && d.includes('efeito ×2') && d.includes('duração +4 rodadas'));
  const f = F._descricaoVenenoPorId('veneno_escorpiao_pedra__upgrade__nenhum_fortalecido_nenhum');
  check('fortalecido usa virgula decimal', f.includes('efeito ×1,5'));
  idioma = 'en';
  check('em ingles o resumo e traduzido', F._descricaoVenenoPorId('veneno_fungo_acre__upgrade__mortal_nenhum_nenhum').includes('Upgrades: DC +6.'));
  idioma = 'pt';
}

console.log('[5] tipo de acao do frasco');
{
  const meta = F._itemAcaoMeta({ item_slot: 'bag', effect: 'coat_poison' });
  check('frasco de veneno e acao bonus', meta && meta.tipo === 'acao_bonus');
  check('item de bolsa comum continua acao principal', F._itemAcaoMeta({ item_slot: 'bag', effect: 'food' }).tipo === 'acao_principal');
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
