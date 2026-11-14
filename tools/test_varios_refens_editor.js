// Vários reféns no editor de masmorras. Roda da raiz:
//   node tools/test_varios_refens_editor.js
// Carrega o tools/editor.js REAL numa página de mentira (DOM em Proxy) e usa window.EDITOR.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const raiz = path.join(__dirname, '..');
let PASS = 0, FAIL = 0;
function check(nome, cond, extra) {
  if (cond) { PASS++; console.log('  ✅ ' + nome); }
  else { FAIL++; console.log('  ❌ ' + nome + (extra ? '\n     ' + extra : '')); }
}
const ler = (...p) => fs.readFileSync(path.join(raiz, ...p), 'utf8');

// ── DOM universal: qualquer propriedade vira outro stub chamável ──
function stub() {
  const alvo = function () {};
  const props = { style: {}, dataset: {}, classList: { add() {}, remove() {}, toggle() {}, contains: () => false } };
  return new Proxy(alvo, {
    get(_, k) {
      if (k === Symbol.toPrimitive) return () => '';
      if (k === 'value' || k === 'innerHTML' || k === 'textContent') return props[k] !== undefined ? props[k] : '';
      if (k === 'checked') return !!props.checked;
      if (k === 'getContext') return () => stub();
      if (k === 'querySelectorAll') return () => [];
      if (k === 'getBoundingClientRect') return () => ({ left: 0, top: 0, width: 100, height: 100 });
      if (k in props) return props[k];
      if (k === 'length') return 0;
      return stub();
    },
    set(_, k, v) { props[k] = v; return true; },
    apply() { return stub(); },
  });
}
const doc = stub();
const store = {};
const win = {
  EDITOR_CATALOG: { monsters: [], items: [], traps: [], venoms: [], curses: [], decorations: [], materiais: [] },
  addEventListener() {}, setTimeout, clearTimeout,
  localStorage: { getItem: k => store[k] || null, setItem(k, v) { store[k] = String(v); } },
};
const ctx = { document: doc, console, setTimeout, clearTimeout,
  alert() {}, confirm: () => true, prompt: () => null, requestAnimationFrame() {}, localStorage: win.localStorage,
  navigator: {}, location: { search: '' }, Image: function () {}, FileReader: function () {}, WebSocket: function () {},
  performance: { now: () => 0 }, getComputedStyle: () => ({}) };
Object.assign(ctx, win); ctx.window = ctx; ctx.self = ctx;
vm.createContext(ctx);
const win2 = ctx;
for (const f of ['src/lang/strings.js', 'src/lang/editor.js', 'src/lang/catalogo.js', 'src/lang/interface.js', 'src/lang/erros.js', 'src/lang/narracao.js', 'src/lang/composto.js', 'src/lang/tutorial.js', 'src/lang/tutorial_guia.js', 'src/i18n.js', 'tools/editor_i18n.js', 'tools/editor_guia_logic.js']) {
  try { vm.runInContext(ler(f), ctx, { filename: f }); } catch (e) { /* idioma opcional neste teste */ }
}
let erroCarga = null;
try { vm.runInContext(ler('tools/editor.js'), ctx, { filename: 'editor.js' }); } catch (e) { erroCarga = e; }
const E = ctx.EDITOR;
if (erroCarga || !E) { console.log('não carregou o editor:', erroCarga && erroCarga.stack); process.exit(1); }
const S = E.S;

function mapaBase() {
  const w = 12, h = 12;
  const tiles = Array.from({ length: h }, (_, y) => Array.from({ length: w }, (_, x) => (x === 0 || y === 0 || x === w - 1 || y === h - 1 ? 0 : 1)));
  return { schema_version: 1, id: 't', name: 'T', grid: { w, h }, tiles,
    rooms: [{ id: 0, x: 1, y: 1, w: 10, h: 10, role: 'entrance', locked: false, doors: [] }],
    entrance: { x: 1, y: 1 }, exit: { x: 10, y: 10 }, prisoner: null,
    monsters: [], chests: [], traps: [], decorations: [],
    objectives: { primary: { type: 'rescue_prisoner', xp: 0, reward: { gold: 0, items: [] } }, secondary: [] } };
}
const clone = o => JSON.parse(JSON.stringify(o));
const por = (x, y) => { S.tool = 'prisoner'; E.placeEntity(x, y); };

console.log('\n[1] Colocar, recusar o 13º e apagar só o da casa');
E.loadJSON(mapaBase());
check('S.prisoners existe e começa vazia', Array.isArray(S.prisoners) && S.prisoners.length === 0);
for (let i = 0; i < 3; i++) por(2 + i, 3);
check('três colocados ficam três', S.prisoners.length === 3, 'n=' + S.prisoners.length);
E.eraseAt(3, 3);
check('apagar remove só o da casa', S.prisoners.length === 2 && S.prisoners.every(p => p.pos[0] !== 3));
S.prisoners.length = 0;
for (let i = 0; i < 12; i++) por(1 + (i % 10), 2 + Math.floor(i / 10));
check('doze cabem', S.prisoners.length === 12, 'n=' + S.prisoners.length);
por(5, 8);
check('o 13º é recusado', S.prisoners.length === 12);
por(1, 2);
check('casa já ocupada não duplica', S.prisoners.length === 12);

console.log('\n[2] Ida e volta com 3 reféns, destino, meta e faixas');
const m3 = mapaBase();
m3.prisoners = [
  { pos: [2, 2], room_id: 0, image: 'a.png', model3d: 'a.glb', nome: 'Ana' },
  { pos: [3, 2], room_id: 0 },
  { pos: [4, 2], room_id: 0, nome: 'Cai' }];
delete m3.prisoner;
m3.objectives.primary = { type: 'rescue_prisoner', xp: 0, reward: { gold: 0, items: [] }, destino: 'entrada', meta: 2,
  faixas: [{ de: 0, ate: 0, xp: 0, gold: 0, renome: -2, fato: 'nenhum' }, { de: 1, ate: 2, xp: 10, gold: 5 }, { de: 3, ate: 3, xp: 50, gold: 20, renome: 3, fato: 'todos' }] };
E.loadJSON(clone(m3));
const j3 = E.buildJSON();
check('3 reféns: grava prisoners e não prisoner', Array.isArray(j3.prisoners) && j3.prisoners.length === 3 && !('prisoner' in j3));
check('conserva nome, imagem e modelo', j3.prisoners && j3.prisoners[0].nome === 'Ana' && j3.prisoners[0].image === 'a.png' && j3.prisoners[0].model3d === 'a.glb' && j3.prisoners[2].nome === 'Cai' && !('nome' in j3.prisoners[1]));
check('conserva destino, meta e faixas', j3.objectives.primary.destino === 'entrada' && j3.objectives.primary.meta === 2
  && JSON.stringify(j3.objectives.primary.faixas) === JSON.stringify(m3.objectives.primary.faixas));

// O editor sempre ordenou as chaves à sua maneira e descarta renome 0 do se_falhar: compara sem isso.
const canon = v => JSON.stringify(v, (k, x) => (x && typeof x === 'object' && !Array.isArray(x)) ? Object.fromEntries(Object.entries(x).sort(([a], [b]) => a < b ? -1 : 1)) : x);
const semFalhar = o => { const c = JSON.parse(JSON.stringify(o)); if (c.primary) delete c.primary.se_falhar; return c; };
console.log('\n[3] Um refém volta idêntico; zero, sem chaves novas');
for (const arq of ['elara_leonel_2.json', 'elara_riacho_celeiro.json', 'elara_adhadal_1.json']) {
  const orig = JSON.parse(ler('dungeons', arq));
  E.loadJSON(clone(orig));
  const out = E.buildJSON();
  check(arq + ': prisoner idêntico', JSON.stringify(out.prisoner) === JSON.stringify(orig.prisoner) && !('prisoners' in out),
    JSON.stringify(out.prisoner) + ' vs ' + JSON.stringify(orig.prisoner));
  check(arq + ': objectives idêntico', canon(semFalhar(out.objectives)) === canon(semFalhar(orig.objectives)));
}
E.loadJSON(clone(mapaBase()));
const j0 = E.buildJSON();
check('zero reféns: sem prisoners e prisoner nulo como hoje', !('prisoners' in j0) && j0.prisoner === null);
check('objetivo sem destino/meta/faixas não ganha chave vazia', !('destino' in j0.objectives.primary) && !('meta' in j0.objectives.primary) && !('faixas' in j0.objectives.primary));
const m1 = mapaBase(); m1.prisoner = { pos: [2, 2], room_id: 0 };
E.loadJSON(clone(m1));
const j1 = E.buildJSON();
check('um refém grava prisoner (objeto) e não prisoners', j1.prisoner && j1.prisoner.pos[0] === 2 && !('prisoners' in j1));
const m1b = mapaBase(); m1b.prisoners = [{ pos: [2, 2], room_id: 0 }]; delete m1b.prisoner;
E.loadJSON(clone(m1b));
const j1b = E.buildJSON();
check('prisoners de tamanho 1 grava prisoner', !!j1b.prisoner && !('prisoners' in j1b));

console.log('\n[4] Validação');
const tem = (txt, slug) => { const k = 'ui.editor.masmorra.valid.' + slug; return txt.includes(String(ctx.t(k)).split(/\{[^}]*\}/).map(x => x.trim()).sort((a, b) => b.length - a.length)[0]); };
function erros(mut) { const m = mapaBase(); mut(m); E.loadJSON(clone(m)); return E.validarEditor().erros.join(' | '); }
const comRef = (m, n) => { delete m.prisoner; m.prisoners = Array.from({ length: n }, (_, i) => ({ pos: [2 + i, 2], room_id: 0 })); };
let e = erros(m => { comRef(m, 2); });
check('2 reféns sem faixas é acusado', tem(e, 'refens_sem_faixas'), e);
e = erros(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 2 }]; m.objectives.primary.meta = 3; });
check('meta maior que o total é acusada', tem(e, 'refens_meta'), e);
e = erros(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 0 }, { de: 2, ate: 2 }]; });
check('buraco nas faixas é acusado', tem(e, 'refens_faixa_buraco'), e);
e = erros(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 1 }, { de: 1, ate: 2 }]; });
check('sobreposição é acusada', tem(e, 'refens_faixa_sobrepoe'), e);
e = erros(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 2 }]; m.objectives.primary.destino = 'saida'; m.exit = null; });
check('destino saida sem saída é acusado', tem(e, 'refens_destino_saida'), e);
e = erros(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 2, xp: 1 }]; });
check('mapa de 2 reféns bem formado não acusa faixa/meta', !/refens_|faixas do resgate|reféns/i.test(e), e);
e = erros(m => { comRef(m, 2); m.objectives.primary.type = 'kill_all'; });
check('2 reféns com outro objetivo principal é acusado', tem(e, 'refens_objetivo'), e);

e = erros(m => { m.prisoner = null; m.objectives.primary.faixas = [{ de: 0, ate: 0 }]; });
check('faixas com zero reféns é acusado', tem(e, 'refens_sem_refens'), e);
const comFaixa = (campo, valor) => erros(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 1 }, { de: 2, ate: 2, [campo]: valor }]; });
for (const [campo, ruim, bom] of [['xp', -5, 999999], ['xp', 1000000, 0], ['gold', -1, 999999], ['gold', 1000000, 0], ['renome', -10000, -9999], ['renome', 10000, 9999]]) {
  check(campo + ' ' + ruim + ' é acusado', tem(comFaixa(campo, ruim), 'refens_faixa_campo'));
  check(campo + ' ' + bom + ' (limite) é aceito', !tem(comFaixa(campo, bom), 'refens_faixa_campo'));
}
check('fato com 101 caracteres é acusado', tem(comFaixa('fato', 'x'.repeat(101)), 'refens_faixa_fato'));
check('fato com 100 caracteres é aceito', !tem(comFaixa('fato', 'x'.repeat(100)), 'refens_faixa_fato'));

console.log('\n[4b] O servidor concorda com o editor (validar_dungeon real)');
const { spawnSync } = require('child_process');
function servidor(mut) {
  const m = mapaBase(); mut(m); E.loadJSON(clone(m));
  const json = E.buildJSON();
  const r = spawnSync('python', ['-X', 'utf8', '-c', 'import sys,json,server; ok,msg=server.validar_dungeon(json.load(sys.stdin)); print(json.dumps([ok,msg]))'],
    { input: JSON.stringify(json), cwd: raiz, encoding: 'utf8' });
  try { return JSON.parse(r.stdout.trim().split('\n').pop()); } catch (x) { return [null, r.stderr.slice(-300)]; }
}
const conj = (campo, valor) => servidor(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 1 }, { de: 2, ate: 2, [campo]: valor }]; });
const bomS = servidor(m => { comRef(m, 2); m.objectives.primary.faixas = [{ de: 0, ate: 2, xp: 5 }]; });
check('servidor aceita o mapa bem formado do editor', bomS[0] === true, JSON.stringify(bomS));
check('servidor rejeita faixas sem reféns (como o editor)', servidor(m => { m.objectives.primary.faixas = [{ de: 0, ate: 0 }]; })[0] === false);
for (const [campo, ruim] of [['xp', -5], ['gold', 1000000], ['renome', -10000]]) {
  check('servidor rejeita ' + campo + ' ' + ruim + ' (como o editor)', conj(campo, ruim)[0] === false);
}
check('servidor rejeita fato de 101 caracteres', conj('fato', 'x'.repeat(101))[0] === false);

console.log('\n[5] Copiar e colar tratam a lista como monstros');
E.loadJSON(clone(mapaBase()));
por(2, 2); por(3, 2);
S.rooms.length = 0;   // a região não pode cortar a sala ao meio
const clip = E.captureRegion({ x: 2, y: 2, w: 2, h: 1 });
check('captureRegion leva os dois reféns', clip && clip.data.prisoners && clip.data.prisoners.length === 2);
E.pasteRegion(clip, [2, 6]);
check('colar duplica deslocado', S.prisoners.length === 4 && S.prisoners.some(p => p.pos[0] === 2 && p.pos[1] === 6) && S.prisoners.some(p => p.pos[0] === 3 && p.pos[1] === 6));

console.log('\n[6] Textos pt e en');
const lang = ler('src', 'lang', 'editor.js');
for (const k of ['ui.editor.masmorra.painel.prisioneiro_nome', 'ui.editor.masmorra.resgate.titulo', 'ui.editor.masmorra.resgate.destino', 'ui.editor.masmorra.resgate.meta',
  'ui.editor.masmorra.resgate.faixas', 'ui.editor.masmorra.resgate.faixa_add',
  'ui.editor.masmorra.valid.refens_limite', 'ui.editor.masmorra.valid.refens_sem_faixas', 'ui.editor.masmorra.valid.refens_meta',
  'ui.editor.masmorra.valid.refens_faixa_buraco', 'ui.editor.masmorra.valid.refens_faixa_sobrepoe', 'ui.editor.masmorra.valid.refens_destino_saida',
  'ui.editor.masmorra.valid.refens_objetivo']) {
  const i = lang.indexOf('"' + k + '": {');
  const b = i < 0 ? '' : lang.slice(i, lang.indexOf('\n  }', i));
  check(k + ' tem pt e en', /"pt":/.test(b) && /"en":/.test(b));
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
