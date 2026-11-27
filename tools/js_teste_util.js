// Utilitário dos testes de cliente: executar funções REAIS do game.js em vez de conferir o texto.
//
// Por que existe: testes que procuram a FORMA exata do código ("a linha A vem logo antes
// da B", "a chamada é escrita assim") quebram quando alguém reescreve o código sem mudar o
// que ele faz. Estes três utilitários deixam o teste olhar o comportamento:
//
//   funcao(src, nome)            → texto de uma função de topo, achada pelo NOME (contando
//                                   chaves; ignora parâmetros, strings e comentários)
//   executar(src, nomes, ctx)    → executa as funções com `ctx` como ambiente; qualquer nome
//                                   que o teste não forneceu vira um ESPIÃO (não faz nada e
//                                   registra a chamada). Acrescentar uma chamada nova à função
//                                   não quebra mais o teste.
//   chamadas(corpo)              → nomes chamados dentro de um trecho, na ordem (para checar
//                                   "chama X" ou "X antes de Y" sem exigir linhas coladas)
'use strict';
const fs = require('fs');
const path = require('path');

const RAIZ = path.join(__dirname, '..');
function ler(rel) {
  return fs.readFileSync(path.join(RAIZ, rel), 'utf8').split('\r\n').join('\n');
}

// Pula string/template/comentário a partir de `i` (que aponta para o caractere de abertura).
function _pular(src, i) {
  const c = src[i], d = src[i + 1];
  if (c === '/' && d === '/') { const j = src.indexOf('\n', i); return j < 0 ? src.length : j; }
  if (c === '/' && d === '*') { const j = src.indexOf('*/', i + 2); return j < 0 ? src.length : j + 2; }
  if (c === "'" || c === '"') {
    for (let k = i + 1; k < src.length; k++) {
      if (src[k] === '\\') { k++; continue; }
      if (src[k] === c || src[k] === '\n') return k + 1;
    }
    return src.length;
  }
  if (c === '`') {
    for (let k = i + 1; k < src.length; k++) {
      if (src[k] === '\\') { k++; continue; }
      if (src[k] === '`') return k + 1;
      if (src[k] === '$' && src[k + 1] === '{') {
        let prof = 1; k += 2;
        while (k < src.length && prof) {
          const e = src[k];
          if (e === "'" || e === '"' || e === '`' || (e === '/' && (src[k + 1] === '/' || src[k + 1] === '*'))) { k = _pular(src, k); continue; }
          if (e === '{') prof++; else if (e === '}') prof--;
          k++;
        }
        k--;
      }
    }
    return src.length;
  }
  return i + 1;
}

// Texto da função `nome` (function / async function), do cabeçalho ao `}` que a fecha.
function funcao(src, nome) {
  const re = new RegExp('(?:^|\\n)\\s*(?:async\\s+)?function\\s+' + nome.replace(/\$/g, '\\$') + '\\s*\\(');
  const m = re.exec(src);
  if (!m) throw new Error('função não encontrada: ' + nome);
  const comeco = m.index + m[0].search(/(?:async\s+)?function/);
  // fim dos parâmetros: primeira `{` fora de string depois do cabeçalho
  let k = m.index + m[0].length, prof = 1;
  while (k < src.length && prof) {               // parênteses dos parâmetros
    const c = src[k];
    if (c === "'" || c === '"' || c === '`') { k = _pular(src, k); continue; }
    if (c === '(') prof++; else if (c === ')') prof--;
    k++;
  }
  k = src.indexOf('{', k);
  let chaves = 0;
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "'" || c === '"' || c === '`' || (c === '/' && (src[k + 1] === '/' || src[k + 1] === '*'))) { k = _pular(src, k) - 1; continue; }
    if (c === '{') chaves++;
    else if (c === '}' && --chaves === 0) return src.slice(comeco, k + 1);
  }
  throw new Error('chaves desbalanceadas em ' + nome);
}

// Bloco `{…}` que começa na primeira chave depois de `marco` (texto exato do começo do bloco,
// por exemplo 'g3 = {'). Para olhar o conteúdo de um objeto sem depender da ordem das chaves.
function bloco(src, marco) {
  const i = src.indexOf(marco);
  if (i < 0) throw new Error('marco não encontrado: ' + marco);
  let k = src.indexOf('{', i), chaves = 0;
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "'" || c === '"' || c === '`' || (c === '/' && (src[k + 1] === '/' || src[k + 1] === '*'))) { k = _pular(src, k) - 1; continue; }
    if (c === '{') chaves++;
    else if (c === '}' && --chaves === 0) return src.slice(src.indexOf('{', i), k + 1);
  }
  throw new Error('chaves desbalanceadas depois de ' + marco);
}

// Texto `(…)` que começa no primeiro parêntese a partir de `idx`, com os parênteses casados.
function parenteses(src, idx) {
  let k = src.indexOf('(', idx), prof = 0;
  const ini = k;
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "'" || c === '"' || c === '`' || (c === '/' && (src[k + 1] === '/' || src[k + 1] === '*'))) { k = _pular(src, k) - 1; continue; }
    if (c === '(') prof++;
    else if (c === ')' && --prof === 0) return src.slice(ini, k + 1);
  }
  throw new Error('parênteses desbalanceados a partir de ' + idx);
}

// Nome da função de topo que contém a posição `idx` (a última declarada antes dela).
function funcaoQueContem(src, idx) {
  const re = /\n\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(/g;
  let m, nome = null;
  while ((m = re.exec(src)) && m.index < idx) nome = m[1];
  return nome;
}

// Valor de uma constante de topo (`const nome = …;`), avaliado. Para conferir o CONTEÚDO de
// um mapa ou lista sem depender de espaços, ordem das chaves ou quebra de linha.
function constante(src, nome) {
  const m = new RegExp('(?:^|\\n)\\s*const\\s+' + nome.replace(/\$/g, '\\$') + '\\s*=').exec(src);
  if (!m) throw new Error('constante não encontrada: ' + nome);
  let k = m.index + m[0].length, prof = 0;
  const ini = k;
  for (; k < src.length; k++) {
    const c = src[k];
    if (c === "'" || c === '"' || c === '`' || (c === '/' && (src[k + 1] === '/' || src[k + 1] === '*'))) { k = _pular(src, k) - 1; continue; }
    if ('([{'.includes(c)) prof++;
    else if (')]}'.includes(c)) prof--;
    else if ((c === ';' || c === '\n') && prof === 0 && src.slice(ini, k).trim()) break;
  }
  return new Function('return (' + src.slice(ini, k) + ');')();
}

// Espião: chamável; registra (nome, argumentos) em `log`.
function _espiao(nome, log) {
  return function (...args) { log.push({ nome, args }); return undefined; };
}

// Executa as funções `nomes` (texto extraído de `src`) com o ambiente `ctx`. Nomes que o
// ctx não tem viram espiões; os globais do JS (Set, Math, JSON…) passam direto.
// Devolve { api: {nome: função}, chamadas: [{nome, args}], ctx }.
function executar(src, nomes, ctx = {}, extra = '') {
  const chamadas = [];
  const ambiente = new Proxy(ctx, {
    has: (alvo, k) => typeof k === 'string' && !(k in globalThis && !(k in alvo)),
    get: (alvo, k) => {
      if (k in alvo) return alvo[k];
      if (k === Symbol.unscopables) return undefined;
      if (typeof k === 'string' && !(k in globalThis)) return (alvo[k] = _espiao(k, chamadas));
      return globalThis[k];
    },
    set: (alvo, k, v) => { alvo[k] = v; return true; },
  });
  const corpo = extra + '\n' + nomes.map(n => funcao(src, n)).join('\n') +
    '\nreturn {' + nomes.join(',') + '};';
  // `with` só existe fora do modo estrito: é ele que leva os nomes livres ao ambiente.
  const api = new Function('__amb', 'with(__amb){ return (function(){' + corpo + '})(); }')(ambiente);
  return { api, chamadas, ctx };
}

// Nomes chamados num trecho de código, na ordem em que aparecem (ignora strings/comentários).
function chamadas(trecho) {
  let limpo = '';
  for (let k = 0; k < trecho.length;) {
    const c = trecho[k];
    if (c === "'" || c === '"' || c === '`' || (c === '/' && (trecho[k + 1] === '/' || trecho[k + 1] === '*'))) {
      const j = _pular(trecho, k); limpo += ' '.repeat(j - k); k = j; continue;
    }
    limpo += c; k++;
  }
  const out = [];
  const re = /([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(/g;
  let m;
  while ((m = re.exec(limpo))) {
    const n = m[1];
    if (!/^(if|for|while|switch|catch|function|return|typeof|new)$/.test(n)) out.push(n);
  }
  return out;
}

// "Dentro de `trecho`, `a` é chamado antes de `b`" (primeiras ocorrências).
function chamaAntes(trecho, a, b) {
  const l = chamadas(trecho);
  const ia = l.indexOf(a), ib = l.indexOf(b);
  return ia >= 0 && ib >= 0 && ia < ib;
}

module.exports = { ler, funcao, bloco, parenteses, funcaoQueContem, constante, executar, chamadas, chamaAntes };
