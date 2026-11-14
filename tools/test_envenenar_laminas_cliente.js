// Painel "Envenenar" (game.js): clicar no cartao das Laminas de Riposta tem de
// enviar `envenenar_laminas`. Regressao: o cartao usava `method` (inexistente)
// em vez de `metodo` e lancava ReferenceError ao clicar.
//
// Roda da raiz:  node tools/test_envenenar_laminas_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){ if(cond){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }

function fnSource(name){
  const i = SRC.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('funcao nao encontrada: ' + name);
  let d = 0;
  // a lista de parametros tem `{...}` (desestruturacao): o corpo comeca no 1o `){`
  for(let k = SRC.indexOf('){', i) + 1; k < SRC.length; k++){
    if(SRC[k] === '{') d++;
    else if(SRC[k] === '}'){ d--; if(!d) return SRC.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + name);
}

// DOM minimo: so o que o painel usa.
class El {
  constructor(){ this.dataset = {}; this.style = {}; this.children = []; this.handlers = {};
    this.disabled = false; this.removed = false; this._html = ''; }
  set innerHTML(v){ this._html = v; this.children = this.children.filter(c => c._cartao); }
  get innerHTML(){ return this._html; }
  appendChild(c){ c._cartao = true; this.children.push(c); return c; }
  addEventListener(ev, fn){ this.handlers[ev] = fn; }
  querySelectorAll(){ return []; }
  querySelector(sel){
    if(sel === '#veneno-alvos') return this.lista || (this.lista = new El());
    return new El();
  }
  remove(){ this.removed = true; }
}

function abrir(opts, alvos){
  const enviados = [];
  const painel = new El();
  const doc = {
    getElementById: () => null,
    createElement: () => painel._criados ? new El() : (painel._criados = true, painel),
    body: { appendChild(){} },
  };
  const me = { class_id: 'rogue', sede: 5, bonus_action_used: false };
  const GS = {
    me,
    venenoAlvos: () => alvos,
    adicionarLog(){},
    ladinoVeneno2Slots: () => false,
    ladinoVenenoMaxHits: () => 3,
    itemSourceFields: s => ({ source: s && s.source }),
  };
  const fn = new Function('document', 'GS', 'send', 't', 'toast', '_rogueMyTurn', '_venenosNaBolsa',
    '_nomeVenenoPorId', '_esc', '_itemLabel', 'window',
    fnSource('abrirPainelEnvenenar') + '\nreturn abrirPainelEnvenenar;')(
    doc, GS, m => enviados.push(m), k => k, () => {}, () => true,
    () => [{ id: 'fungo', nome: 'Fungo', descricao: '', icone: '☠️' }],
    id => id, s => String(s), () => 'item', { GS });
  fn(opts);
  return { enviados, painel };
}

const alvos = { armas: [], municoes: [],
  laminas: [{ index: 2, qtd: 4, total: 4, item: { name: 'Laminas' } }] };

console.log('[1] veneno rapido: cartao de laminas envia envenenar_laminas');
{
  const { enviados, painel } = abrir({ metodo: 'veneno_rapido' }, alvos);
  const cartao = painel.lista.children[0];
  check('o cartao de laminas existe e esta liberado', !!cartao && !cartao.disabled);
  let erro = null;
  try { cartao.handlers.click(); } catch(e){ erro = e; }
  check('clicar nao lanca erro (' + (erro && erro.message) + ')', !erro);
  const m = enviados[0] || {};
  check('envia envenenar_laminas', m.type === 'envenenar_laminas');
  check('method acompanha o metodo do painel', m.method === 'veneno_rapido');
  check('blade_index e quantity vem do alvo', m.blade_index === 2 && m.quantity === 4);
  check('poison_id e o veneno escolhido; sem item_id', m.poison_id === 'fungo' && m.item_id === null);
}

console.log('[2] frasco: envia o frasco como item_id');
{
  const { enviados, painel } = abrir({ metodo: 'frasco', venenoId: 'fungo' }, alvos);
  painel.lista.children[0].handlers.click();
  const m = enviados[0] || {};
  check('method frasco e item_id do frasco', m.method === 'frasco' && m.item_id === 'fungo');
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
