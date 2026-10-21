// Editor de masmorras — opção "marcador de entrada" (escada ou poste).
// Roda da raiz: node tools/test_marcador_entrada_editor.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (...p) => fs.readFileSync(path.join(__dirname, '..', ...p), 'utf8');
const html = ler('tools', 'editor.html'), js = ler('tools', 'editor.js'), lang = ler('src', 'lang', 'editor.js');
let pass = 0, fail = 0;
function check(label, ok) { if (ok) { pass++; console.log('  ✅ ' + label); } else { fail++; console.log('  ❌ ' + label); } }
function body(name) {
  const start = js.indexOf(`function ${name}(`);
  if (start < 0) return '';
  const brace = js.indexOf('{', start);
  let depth = 0;
  for (let i = brace; i < js.length; i++) {
    if (js[i] === '{') depth++;
    if (js[i] === '}' && --depth === 0) return js.slice(brace + 1, i);
  }
  return '';
}

console.log('\n[1] Seletor no topo do editor');
check('há o seletor m-marcador com escada e poste', /id="m-marcador"/.test(html)
  && /<option value="escada"/.test(html) && /<option value="poste"/.test(html));
check('o texto do seletor é traduzível', /data-i18n="ui\.editor\.topo\.marcador"/.test(html)
  && /data-i18n-title="ui\.editor\.topo\.marcador_dica"/.test(html));

console.log('\n[2] Abrir, montar e salvar');
const build = body('buildJSON'), load = body('loadJSON'), save = body('save');
check('loadJSON lê o campo (ausente = escada) e põe no seletor',
  /marcador_entrada\s*:\s*obj\.marcador_entrada\s*===\s*"poste"\s*\?\s*"poste"\s*:\s*"escada"/.test(load)
  && /getElementById\("m-marcador"\)\.value/.test(load));
check('buildJSON só grava quando é poste (arquivos antigos não mudam) e lê o seletor na hora (prévia)',
  /marcador_entrada:\s*"poste"/.test(build) && /getElementById\("m-marcador"\)/.test(build));
check('save() guarda a escolha em S.meta', /S\.meta\.marcador_entrada\s*=/.test(save));
const iMeta = js.indexOf('meta: { schema_version');
check('o meta nasce com escada', /marcador_entrada:\s*"escada"/.test(js.slice(iMeta, iMeta + 260)));

console.log('\n[3] Textos PT/EN');
for (const k of ['ui.editor.topo.marcador', 'ui.editor.topo.marcador_dica', 'ui.editor.topo.marcador.escada', 'ui.editor.topo.marcador.poste']) {
  const m = lang.match(new RegExp('"' + k.replace(/\./g, '\\.') + '": \\{([\\s\\S]*?)\\n  \\}'));
  check(k + ' tem pt e en', !!m && /"pt":/.test(m[1]) && /"en":/.test(m[1]));
}

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
