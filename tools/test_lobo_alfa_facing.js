const fs = require('fs');
const assert = require('assert');
const source = fs.readFileSync('game.js', 'utf8');

function functionSource(name) {
  const match = source.match(new RegExp(`function ${name}\\s*\\(`));
  assert(match, `função ${name} não encontrada`);
  const start = match.index;
  const open = source.indexOf('{', start);
  let depth = 0;
  for (let i = open; i < source.length; i++) {
    if (source[i] === '{') depth++;
    if (source[i] === '}' && --depth === 0) return source.slice(start, i + 1);
  }
  throw new Error(`bloco de ${name} não foi fechado`);
}

const facing = new Function(`${functionSource('_facingToRotY')};` +
  `${functionSource('_monsterFacingToRotY')}; return _monsterFacingToRotY;`)();
const casos = [
  [[0, 1], 0],
  [[1, 0], Math.PI / 2],
  [[0, -1], Math.PI],
  [[-1, 0], -Math.PI / 2],
];
for (const [vetor] of casos) {
  const angle = facing(vetor, 'lobo_alfa', 'lobo_cinzento_customizado',
    'assets/models3d/monstros/lobo_alfa.glb');
  const original = facing(vetor, 'loboCinzento', 'lobo_cinzento',
    'assets/models3d/monstros/lobo.glb');
  assert(Math.abs(angle - original) < 1e-9,
    `Lobo Alfa deveria manter a calibração do GLB original para ${vetor}`);
}

for (const [vetor, esperado] of casos) {
  const angle = facing(vetor, 'lobisomem_alfa', 'lobisomem_alfa',
    'assets/models3d/monstros/lobisomem_alfa.glb');
  assert(Math.abs(angle - esperado) < 1e-9,
    `frente do Lobisomem Alfa para ${vetor} deveria usar ${esperado}, recebeu ${angle}`);
}

// A calibração é exclusiva: o Lobo Cinzento comum mantém sua orientação anterior.
const antigo = facing([0, 1], 'loboCinzento', 'lobo_cinzento',
  'assets/models3d/monstros/lobo.glb');
assert(Math.abs(antigo - Math.PI / 2) < 1e-9,
  'a orientação do Lobo Cinzento comum não deve mudar');
console.log('Lobo Alfa mantém o eixo do GLB original; 4 direções do Lobisomem Alfa alinhadas.');
