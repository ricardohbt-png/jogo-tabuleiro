// Parede acompanha o terreno no 3D + lápide de monstro no topo do platô.
// Roda da raiz: node tools/test_altura_parede_cliente.js
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');

let ok = 0, falhas = 0;
function check(nome, cond){
  if(cond){ ok++; console.log('  ✅ ' + nome); }
  else { falhas++; console.log('  ❌ ' + nome); }
}

function extrair(nome){
  const i = src.indexOf('function ' + nome + '(');
  if(i < 0) throw new Error('função não encontrada: ' + nome);
  let j = src.indexOf('{', i), prof = 0;
  for(; j < src.length; j++){
    if(src[j] === '{') prof++;
    else if(src[j] === '}' && --prof === 0) break;
  }
  return src.slice(i, j + 1);
}

const codigo = `
  const TILE_WALL = 0, TILE_FLOOR = 1, TILE_DOOR = 2;
  const TERRENO_ELEVACAO_STEP_3D = 0.24;
  const ELEVACAO_TERRENO_MIN = -1, ELEVACAO_TERRENO_MAX = 10;
  ${extrair('elevacaoTerreno')}
  ${extrair('nivelParede3D')}
  ${extrair('elevacaoEnfeiteParede3D')}
  return { nivelParede3D, elevacaoEnfeiteParede3D };
`;
const { nivelParede3D, elevacaoEnfeiteParede3D } = new Function(codigo)();

// 5x5: parede na borda, chão no miolo.
function estado(elevacoes = {}, alturas){
  const W = 0, F = 1;
  const tiles = [];
  for(let y = 0; y < 5; y++){
    const row = [];
    for(let x = 0; x < 5; x++) row.push(x === 0 || y === 0 || x === 4 || y === 4 ? W : F);
    tiles.push(row);
  }
  return { tiles, elevacoes, alturas_parede: alturas };
}

console.log('\n[1] Automático: maior chão das 8 casas ao redor');
check('sem elevação, a parede fica no 0', nivelParede3D(estado(), 0, 2) === 0);
check('platô 4 ao lado ergue a parede para 4', nivelParede3D(estado({ '1,2': 4 }), 0, 2) === 4);
check('vale o mais alto dos vizinhos', nivelParede3D(estado({ '1,1': 2, '1,3': 6 }), 0, 2) === 6);
check('diagonal também conta', nivelParede3D(estado({ '1,1': 3 }), 0, 0) === 3);
check('chão afundado (−1) não rebaixa a parede', nivelParede3D(estado({ '1,2': -1 }), 0, 2) === 0);
check('chão a 2 casas não conta', nivelParede3D(estado({ '2,2': 5 }), 0, 2) === 0);
const comPorta = estado({ '1,2': 3 });
comPorta.tiles[2][1] = 2;
check('porta elevada também ergue a parede', nivelParede3D(comPorta, 0, 2) === 3);

console.log('\n[2] Manual vence o automático');
check('manual 7 sem platô', nivelParede3D(estado({}, { '0,2': 7 }), 0, 2) === 7);
check('manual 0 trava a parede ao lado de um platô 5',
  nivelParede3D(estado({ '1,2': 5 }, { '0,2': 0 }), 0, 2) === 0);
check('manual acima de 10 é limitado a 10', nivelParede3D(estado({}, { '0,2': 40 }), 0, 2) === 10);
check('valor não inteiro cai no automático',
  nivelParede3D(estado({ '1,2': 2 }, { '0,2': 'x' }), 0, 2) === 2);

console.log('\n[3] Enfeite de parede sobe com o chão à frente');
check('tocha diante de platô 4 sobe 4 degraus',
  Math.abs(elevacaoEnfeiteParede3D(estado({ '1,2': 4 }), 0, 2, 1, 2) - 4 * 0.24) < 1e-9);
check('não passa da altura da parede travada em 0',
  elevacaoEnfeiteParede3D(estado({ '1,2': 4 }, { '0,2': 0 }), 0, 2, 1, 2) === 0);
check('chão afundado não afunda o enfeite',
  elevacaoEnfeiteParede3D(estado({ '1,2': -1 }), 0, 2, 1, 2) === 0);

console.log('\n[4] Fiação no render');
const malha = src.indexOf('const wallScale = (WH + nivelParede3D(state, x, y)');
const proxy = src.indexOf('_prepararTileProxy(mesh);', malha);
check('a malha da parede escala por nivelParede3D', malha > 0);
check('a escala vem ANTES de _prepararTileProxy (que congela a matriz)', proxy > malha);
check('assinatura do tabuleiro inclui alturas_parede',
  /alturasParede\}#\$\{pontes\}/.test(src));
check('lápide do monstro passa x,y ao obterFig (assenta no platô)',
  src.includes('() => build3DCorpse(c), cx, cy)'));
check('visual de derrota nasce no topo do terreno', src.includes('(v.baseY || 0) + .32'));
check('colunas de canto crescem com a parede', src.includes('col.scale.y = colScale'));

console.log(`\n${ok} ok, ${falhas} falha(s)`);
process.exit(falhas ? 1 : 0);
