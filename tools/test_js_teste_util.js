// Testes do utilitário de testes (js_teste_util). Roda da raiz: node tools/test_js_teste_util.js
'use strict';
const U = require('./js_teste_util');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

const SRC = [
  "const MAPA = { a: 'x', b: '}' , c: [1, 2] };",
  'function dificil(p = {x: 1}, q) {',
  '  const s = "texto com } e { dentro";',
  '  const t = `template ${q ? `aninhado {${p.x}}` : "}"} fim`;',
  '  // comentário com } solto',
  '  /* outro { comentário */',
  '  if (q) { ajudante(q); }',
  '  return s.length + t.length;',
  '}',
  'async function assinc(a) { await algo(a); }',
  'function usaFora(n) { const o = new Set(); o.add(n); registrar(o); return Math.max(n, 1); }',
].join('\n');

console.log('\n[1] funcao: acha pelo nome e casa as chaves');
const f = U.funcao(SRC, 'dificil');
check('pega a função inteira apesar de chaves em string, template e comentário', f.startsWith('function dificil(') && f.endsWith('return s.length + t.length;\n}'));
check('aceita async function', U.funcao(SRC, 'assinc').startsWith('async function assinc('));
let erro = null; try { U.funcao(SRC, 'naoExiste'); } catch (e) { erro = e.message; }
check('função inexistente avisa com o nome', /naoExiste/.test(erro || ''));

console.log('\n[2] constante e bloco');
check('lê o valor da constante (com "}" dentro de string)', U.constante(SRC, 'MAPA').b === '}' && U.constante(SRC, 'MAPA').c[1] === 2);
check('bloco devolve o objeto inteiro', U.bloco(SRC, 'MAPA = {').endsWith('[1, 2] }'));
check('parênteses casados', U.parenteses(SRC, SRC.indexOf('dificil(')) === '(p = {x: 1}, q)');
check('funcaoQueContem acha a função de um trecho', U.funcaoQueContem(SRC, SRC.indexOf('ajudante(q)')) === 'dificil');

console.log('\n[3] executar: nomes desconhecidos viram espiões; globais do JS passam');
const r = U.executar(SRC, ['usaFora', 'dificil'], {});
check('retorno usa Math e Set reais', r.api.usaFora(5) === 5);
check('o espião registrou a chamada e o argumento', r.chamadas.length === 1 && r.chamadas[0].nome === 'registrar' && r.chamadas[0].args[0].has(5));
r.api.dificil({ x: 2 }, true);
check('chamada dentro de if também é registrada', r.chamadas.some(c => c.nome === 'ajudante'));
const r2 = U.executar(SRC, ['usaFora'], { registrar: (o) => { r2_visto = o.size; } });
var r2_visto; r2.api.usaFora(3);
check('o que o teste fornece no ctx é usado no lugar do espião', r2_visto === 1 && r2.chamadas.length === 0);

console.log('\n[4] chamadas e chamaAntes');
const ch = U.chamadas(f);
check('lista chamadas em ordem, sem as de dentro de string/comentário', ch.includes('ajudante') && !ch.includes('comentário'));
check('chamaAntes respeita a ordem', U.chamaAntes('a(); b(); c();', 'a', 'c') && !U.chamaAntes('a(); b(); c();', 'c', 'a'));
check('palavras-chave não contam como chamada', !U.chamadas('if (x) { while (y) {} }').length);

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
