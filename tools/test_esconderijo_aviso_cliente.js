// Esconderijo notado (cliente): GS repassa a mensagem; game.js mostra toast, brilho 2D/3D e o
// marcador 💰 no 3D. Roda da raiz: node tools/test_esconderijo_aviso_cliente.js
const fs = require('fs');
const path = require('path');
const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
const gs = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
let pass = 0, fail = 0;
const check = (n, c) => { if (c) { pass++; console.log('  ✅ ' + n); } else { fail++; console.log('  ❌ ' + n); } };

check('GS emite esconderijoAchado ao receber a mensagem', /case 'esconderijo_achado':\s*_emit\('esconderijoAchado', msg\)/.test(gs));
check('game.js ouve esconderijoAchado, mostra toast e guarda o brilho',
  /GS\.on\('esconderijoAchado'[\s\S]{0,400}toast\([\s\S]{0,200}_achadosAtivos\.set\(/.test(game));
check('só um GS.on para esconderijoAchado (o segundo substituiria o primeiro)',
  (game.match(/GS\.on\('esconderijoAchado'/g) || []).length === 1);
check('3D: marcador 💰 em objeto com tem_loot e brilho pulsando no loop',
  /_decorLootBadge3D\(\)/.test(game) && /d\.tem_loot && !lb/.test(game) && /_syncLootBadges3D\(\);\s*_updateAchados3D\(now\);/.test(game));
check('3D: o badge de loot sai de cena com o objeto (filho da malha)', /mesh\.add\(lb\)/.test(game));
check('3D: o marcador é sincronizado por quadro (a malha GLB chega depois do estado)', /function _syncLootBadges3D\(\)/.test(game) && !/Objeto com item\/ouro a pegar[\s\S]{0,200}for \(const d of decors\)/.test(game));
check('2D: moldura dourada enquanto o brilho está ativo e reagenda o redesenho',
  /_achadosAtivos\.has\(d\.id\)[\s\S]{0,700}_agendarChamas2D\(\)/.test(game));
check('texto do aviso não mostra os ** do markdown', game.includes(String.raw`String(msg.texto).replace(/\*\*/g, '')`));
console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
