// Exercita a função real de popup, incluindo tradução, arte e a janela de rede.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const root = path.join(__dirname, '..');
let language = 'pt';
const nodes = new Map();
function node() {
  return {textContent: '', innerHTML: '', children: [], className: '',
    replaceChildren() { this.children = []; },
    classList: {add() {}, remove() {}}, appendChild(child) { this.children.push(child); }};
}
const context = vm.createContext({window: {LANG_STRINGS: {}}, document: {createElement: node},
  $: id => { if (!nodes.has(id)) nodes.set(id, node()); return nodes.get(id); },
  tocarSomArmadilha() { throw new Error('Aviso de prisão não dispara som de armadilha'); },
  _trapPopupOpen: false,
  Image: class {}, _assetURL: path => path,
});
vm.runInContext(fs.readFileSync(path.join(root, 'src/lang/interface.js'), 'utf8'), context);
context.t = (key, params = {}) => {
  const entry = context.window.LANG_INTERFACE[key];
  assert.ok(entry, `tradução ausente: ${key}`);
  return (entry[language] || entry.pt).replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`);
};
const game = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
vm.runInContext(game.match(/function _isWhirlpoolResult\(msg\)\{[\s\S]*?\n\}/)[0], context);
const popup = game.slice(game.indexOf('function _showTrapResult(msg)'), game.indexOf('function closeTrapWindow()'));
vm.runInContext(popup, context);
const descriptions = new Set();
for (const lang of ['pt', 'en']) {
  language = lang;
  for (const cause of ['teia', 'cola', 'piche']) {
    nodes.clear();
    context._showTrapResult({tipo: 'prisao', tipo_id: 'prisao', prisao_id: cause,
      imagem: 'preso.png', duracao: 3, sucesso: false, efeitos_extra: []});
    assert.equal(nodes.get('trap-icon').children[0].src, 'assets/armadilhas/preso.png');
    assert.ok(nodes.get('trap-title').textContent.length > 0);
    assert.ok(!nodes.get('trap-desc').textContent.includes('undefined'));
    descriptions.add(nodes.get('trap-desc').textContent);
    if (cause === 'cola') assert.match(nodes.get('trap-status').textContent, /3/);
  }
}
assert.equal(descriptions.size, 6, 'texto específico por causa e idioma');
nodes.clear();
context._showTrapResult({tipo_id: 'rede', nome: 'Rede', sucesso: false, efeitos_extra: []});
assert.equal(nodes.get('trap-icon').children[0].src, 'assets/armadilhas/armadilha_rede.png');
assert.equal(nodes.get('trap-title').textContent, 'Rede');
for (const lang of ['pt', 'en']) {
  language = lang;
  nodes.clear();
  context._showTrapResult({tipo: 'agarrado', tipo_id: 'agarrado', imagem: 'agarrado.png',
    captor: 'Crocodilo', escape_dc: 17, escape_saves: ['forca', 'reflexos'], efeitos_extra: []});
  assert.match(nodes.get('trap-title').textContent, /Agarrado|Grappled/);
  assert.match(nodes.get('trap-desc').textContent, /Crocodilo/);
  assert.match(nodes.get('trap-desc').textContent, /−2/);
  const effects = nodes.get('trap-effects').children.map(n => n.textContent).join(' ');
  assert.match(effects, /17/);
  assert.match(effects, /Força|Strength/);
  assert.match(effects, /Reflexos|Reflexes/);
  assert.match(effects, /início|start/);
  assert.equal(nodes.get('trap-icon').children[0].src, 'assets/armadilhas/agarrado.png');
}
for (const lang of ['pt', 'en']) {
  language = lang;
  for (const turn of ['atual', 'proximo']) {
    nodes.clear();
    context._showTrapResult({tipo: 'derrubado', tipo_id: 'derrubado', imagem: 'derrubado.png',
      turno_efeito: turn, fonte: 'Tirano', efeitos_extra: []});
    assert.match(nodes.get('trap-title').textContent, /Derrubado|Knocked down/);
    assert.match(nodes.get('trap-desc').textContent, /Tirano/);
    assert.match(nodes.get('trap-desc').textContent, /atacar|attack/);
    assert.match(nodes.get('trap-status').textContent, turn === 'atual' ? /restante|rest/ : /próximo|next/);
    assert.equal(nodes.get('trap-icon').children[0].src, 'assets/armadilhas/derrubado.png');
  }
}
for (const lang of ['pt', 'en']) {
  language = lang;
  nodes.clear();
  context._showTrapResult({tipo: 'silencio', tipo_id: 'silencio', imagem: 'silencio.png', duracao: 3, efeitos_extra: []});
  assert.match(nodes.get('trap-title').textContent, /Silenciado|Silenced/);
  assert.match(nodes.get('trap-desc').textContent, /magias|spells/);
  assert.match(nodes.get('trap-desc').textContent, /Canção Heroica|Heroic Song/);
  assert.match(nodes.get('trap-desc').textContent, /mover|move/);
  const effects = nodes.get('trap-effects').children.map(n => n.textContent).join(' ');
  assert.match(effects, /3/);
  assert.match(effects, /Sair|Leaving/);
  assert.equal(nodes.get('trap-icon').children[0].src, 'assets/armadilhas/silencio.png');
}
for (const lang of ['pt', 'en']) {
  language = lang;
  nodes.clear();
  context._showTrapResult({tipo_id: 'amaldicoar_xama', imagem: 'amaldicoado.png', sucesso: false,
    nome: context.t('ui.amaldicoar_xama.titulo'),
    descricao: context.t('ui.amaldicoar_xama.descricao', {monstro: 'Xamã'}),
    efeitos_extra: [context.t('ui.amaldicoar_xama.penalidades', {ataque:-1,dano:-1,ca:-1,resistencia:-1}),
      context.t('ui.amaldicoar_xama.duracao', {n:3}), context.t('ui.amaldicoar_xama.termino')]});
  assert.equal(nodes.get('trap-icon').children[0].src, 'assets/armadilhas/amaldicoado.png');
  assert.match(nodes.get('trap-title').textContent, /Amaldiçoado|Cursed/);
  const effects = nodes.get('trap-effects').children.map(n => n.textContent).join(' ');
  assert.match(effects, /-1/); assert.match(effects, /3/); assert.match(effects, /automatic/);
}
console.log('OK: avisos em PT/EN, incluindo Amaldiçoar do xamã, com imagens e durações corretas.');
