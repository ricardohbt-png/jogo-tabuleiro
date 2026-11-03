// Slide de história com vídeo: editor (ida e volta) e cliente do jogo.
// Roda da raiz: node tools/test_video_historia_cliente.js
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const raiz = path.join(__dirname, '..');
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };

const fonte = fs.readFileSync(path.join(raiz, 'tools/editor_story.js'), 'utf8');
const win = {}; vm.runInNewContext(fonte, { window: win, document: {}, URL: {}, alert() {} });
const E = win.EDITOR_STORY;
const salvo = { slides: [{ video: 'assets/story/a.mp4', image: 'assets/story/a.png', fit: 'contain' }, { video: 'assets/story/b.webm' }] };
const st = E.storyFromSaved(salvo);
ok(st.slides[0].video === 'assets/story/a.mp4', 'carrega o vídeo');
ok(E.storyCount(st) === 2, 'slide só de vídeo conta');
const volta = E.storyToSaved(st);
ok(volta.slides[0].video === 'assets/story/a.mp4' && volta.slides[0].image === 'assets/story/a.png' && volta.slides[0].fit === 'contain', 'ida e volta conserva o slide');
ok(volta.slides[1].video === 'assets/story/b.webm', 'slide só de vídeo sobrevive ao salvar');
ok(fonte.includes('hist-video-pick') && fonte.includes('video/mp4'), 'painel tem o botão de vídeo');

const js = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
ok(/function _storyVideoPaint\(/.test(js) && /function _storyVideoParar\(/.test(js), 'cliente toca e para o vídeo');
const paint = js.slice(js.indexOf('function _storyPaint('), js.indexOf('function _storyComplete('));
ok(paint.includes('_storyVideoPaint('), '_storyPaint pinta o vídeo');
const fim = js.slice(js.indexOf('function _storyComplete('), js.indexOf('// ── Cenas da campanha'));
ok((fim.match(/_storyVideoParar\(\)/g) || []).length >= 3, 'fechar a história para o vídeo nos 3 caminhos');
ok(fim.includes('_storyVideoAplicarMudo'), 'o botão de som alcança o vídeo');
ok(js.slice(js.indexOf('function _storyVideoEl'), js.indexOf('function _storyVideoPaint')).includes('playsInline'), 'não abre em tela cheia no celular');
console.log(`OK ${n} verificações`);
