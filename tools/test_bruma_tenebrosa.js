// Bruma tenebrosa — roda da raiz: node tools/test_bruma_tenebrosa.js
// Verifica integração do preset e que a camada atmosférica continua visual,
// respeita o terreno revelado e não interfere nos controles de visão.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.join(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const check = (name, ok) => {
  if (ok) console.log('  ✅ ' + name);
  else { console.error('  ❌ ' + name); process.exitCode = 1; }
};

const visualSrc = read('src/visualConfig.js');
const visualCtx = { window: {} };
vm.runInNewContext(visualSrc, visualCtx);
const preset = visualCtx.window.VC.ambientes.bruma_tenebrosa;
check('preset visual possui paleta fria, neblina de cena e iluminação',
  !!preset && preset.scene && preset.lighting && preset.scene.fogDensity > 0
  && preset.scene.bgColor !== preset.scene.fogColor);

const editorHtml = read('tools/editor.html');
const editorJs = read('tools/editor.js');
const lang = read('src/lang/editor.js');
const server = read('server.py');
check('editor oferece a Bruma tenebrosa', /option value="bruma_tenebrosa"/.test(editorHtml));
check('editor preserva o preset no abre-e-salva', /\["penumbra",\s*"masmorra",\s*"ar_livre",\s*"bruma_tenebrosa"\]/.test(editorJs));
check('preset tem nome localizado em português e inglês', /ui\.editor\.topo\.ambiente\.bruma_tenebrosa/.test(lang));
check('servidor aceita o preset na masmorra autorada', /"penumbra",\s*"masmorra",\s*"ar_livre",\s*"bruma_tenebrosa"/.test(server));

const game = read('game.js');
check('2D atualiza uma camada atmosférica independente',
  /function _sincronizarBruma2D\(/.test(game) && /function _desenharBruma2D\(/.test(game));
check('2D limita o desenho às casas em terrainSet',
  /function _sincronizarBruma2D\([\s\S]*?\[\.\.\.terrainSet\]/.test(game)
  && /function _desenharBruma2D\([\s\S]*?destination-in[\s\S]*?maskCanvas/.test(game));
check('2D remove a camada ao sair do preset',
  /function _sincronizarBruma2D\([\s\S]*?bruma_tenebrosa[\s\S]*?remove\(/.test(game));
check('3D atualiza a névoa rasteira no ciclo de quadros',
  /function _atualizarBruma3D\(/.test(game) && /_atualizarBruma3D\(now\)/.test(game));
check('3D limita a névoa às casas reveladas',
  /function _atualizarBruma3D\([\s\S]*?terrainSet\.has/.test(game));
check('bruma não muda o cálculo de visão nem revela casas',
  !/bruma_tenebrosa[\s\S]{0,500}(?:computeVisionSet|visionSet\.add|exploredSet\.add)/.test(game));
