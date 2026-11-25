// Herói morto na masmorra: o retrato vira a caveira e, ao reviver, volta ao original.
// Roda da raiz: node tools/test_retrato_heroi_morto.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const raiz = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8').split('\r\n').join('\n');
const lang = fs.readFileSync(path.join(raiz, 'src/lang/interface.js'), 'utf8');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };

// [1] a imagem existe e a constante aponta para ela
ok(fs.existsSync(path.join(raiz, 'assets/portraits/heroi_morto_caveira.png')), 'falta o PNG da caveira');
ok(game.includes("const HERO_MORTO_CAVEIRA = 'assets/portraits/heroi_morto_caveira.png';"), 'constante da caveira ausente');

// [2] lógica pura: morto → caveira; vivo (ou alive ausente) → retrato da classe
const trecho = game.slice(game.indexOf('const HERO_MORTO_CAVEIRA'), game.indexOf('// Estado de UI: aba ativa do painel principal do Pedro'));
const retrato = new Function('HERO_PORTRAIT_PATHS', trecho + '; return {_heroiMorto, _retratoDoHeroi};')({warrior: 'assets/portraits/victor.jpeg'});
ok(retrato._retratoDoHeroi({class_id: 'warrior', alive: false}) === 'assets/portraits/heroi_morto_caveira.png', 'morto deve usar a caveira');
ok(retrato._retratoDoHeroi({class_id: 'warrior', alive: true}) === 'assets/portraits/victor.jpeg', 'vivo deve usar o retrato original');
ok(retrato._retratoDoHeroi({class_id: 'warrior'}) === 'assets/portraits/victor.jpeg', 'alive ausente conta como vivo');
ok(retrato._retratoDoHeroi(null) === null, 'sem herói não quebra');
// reviver: o MESMO herói volta ao original só trocando alive
const h = {class_id: 'warrior', alive: false};
const caveira = retrato._retratoDoHeroi(h); h.alive = true;
ok(caveira !== retrato._retratoDoHeroi(h) && retrato._retratoDoHeroi(h) === 'assets/portraits/victor.jpeg', 'ao reviver o original volta');

// [3] fiação: retrato grande do HUD e cartões dos heróis
ok(/const morto = _heroiMorto\(me\);/.test(game), 'HUD não consulta o estado de morto');
ok(game.includes("pFrame.classList.toggle('morto', morto);"), 'HUD não marca a classe morto');
ok(game.includes('_imgURL(HERO_MORTO_CAVEIRA, 384)'), 'HUD deve pedir a caveira reduzida (PNG de 2 MB)');
ok(game.includes('<img class="pcard-caveira"') && game.includes('_heroiMorto(p)'), 'cartão sem a caveira');
ok(game.includes("<span class=\"pcard-emoji\">${p.emoji}</span>"), 'cartão vivo mantém o emoji');

// [4] idioma
const linha = lang.split('\n').find(l => l.includes('"ui.hud.heroi_morto":'));
ok(linha && linha.includes('"en":') && linha.includes('"pt":'), 'chave ui.hud.heroi_morto sem pt/en');

console.log('test_retrato_heroi_morto: ' + n + ' verificações OK');
