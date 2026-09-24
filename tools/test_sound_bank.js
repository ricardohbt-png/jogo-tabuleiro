// tools/test_sound_bank.js — node tools/test_sound_bank.js
// Regras puras do banco de sons. Spec: 2026-09-23-sons-efeitos-sonoros-design.md
const fs = require('fs');
const path = require('path');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
global.window = {};
eval(fs.readFileSync(path.join(__dirname, '..', 'src', 'soundBank.js'), 'utf8'));
const SB = global.window.SoundBank;

console.log('\n[1] Catálogo');
const eventos = Object.keys(SB.SFX);
for (const e of ['golpe_cortante','golpe_perfurante','golpe_contundente','golpe_natural','golpe_critico',
                 'golpe_erro','escudo_bloqueio','dor_heroi','dor_criatura','porta_abre','moedas','item_pegar',
                 'equipar','beber','escada','sua_vez','nivel','objetivo','clique','recusa',
                 'amb_masmorra','amb_penumbra','amb_ar_livre'])
  check('tem ' + e, eventos.includes(e));
for (const f of SB.FAMILIAS) check('rugido e morte de ' + f, !!SB.SFX['rugido_' + f] && !!SB.SFX['morte_' + f]);
check('todo evento tem lista de arquivos, volume e canal válido', eventos.every(e => {
  const d = SB.SFX[e];
  return Array.isArray(d.arquivos) && d.volume > 0 && d.volume <= 1 && (d.canal === 'efeitos' || d.canal === 'ambiente');
}));
check('só os amb_* são do canal ambiente', eventos.every(e => (SB.SFX[e].canal === 'ambiente') === e.startsWith('amb_')));

console.log('\n[2] familiaDe');
const fam = t => SB.familiaDe({ type: t });
check('goblin_arqueiro → humanoide', fam('goblin_arqueiro') === 'humanoide');
check('lobo_cinzento_customizado → fera', fam('lobo_cinzento_customizado') === 'fera');
check('esqueleto_humano → morto_vivo', fam('esqueleto_humano') === 'morto_vivo');
check('zumbi_infectado → morto_vivo', fam('zumbi_infectado') === 'morto_vivo');
check('cobra_venenosa → reptil_inseto', fam('cobra_venenosa') === 'reptil_inseto');
check('tirano_da_mata → grande', fam('tirano_da_mata') === 'grande');
check('grande_medusa → grande (antes de medusa)', fam('grande_medusa') === 'grande');
check('medusa → humanoide', fam('medusa') === 'humanoide');
check('elemental_fogo → null (sem voz)', fam('elemental_fogo') === null);
check('boneco_treino → null', fam('boneco_treino') === null);
check('desconhecido 1×1 → humanoide', SB.familiaDe({ type: 'coisa_nova', size: [1, 1] }) === 'humanoide');
check('desconhecido 2×2 → grande', SB.familiaDe({ type: 'coisa_nova', size: [2, 2] }) === 'grande');
check('sem type → humanoide', SB.familiaDe({}) === 'humanoide');
check('molochus_adulto → fera', fam('molochus_adulto') === 'fera');
check('estrangulador → humanoide', fam('estrangulador') === 'humanoide');

console.log('\n[3] audibilidade');
const vis = new Set(['5,5', '6,5', '17,5']);
let a = SB.audibilidade({});
check('sem pos: ganho 1, sem abafar, sem pan', a.ganho === 1 && !a.abafado && !a.panLivre);
a = SB.audibilidade({ pos: [5, 5], visao: vis, mePos: [5, 5] });
check('visível na mesma casa: ganho 1', a.ganho === 1 && !a.abafado && a.panLivre);
a = SB.audibilidade({ pos: [17, 5], visao: vis, mePos: [5, 5] });
check('visível a 12 casas: ganho 0.4', Math.abs(a.ganho - 0.4) < 1e-9);
a = SB.audibilidade({ pos: [11, 5], visao: new Set(['11,5']), mePos: [5, 5] });
check('visível a 6 casas: ganho 0.7', Math.abs(a.ganho - 0.7) < 1e-9);
a = SB.audibilidade({ pos: [9, 9], visao: vis, mePos: [5, 5] });
check('na névoa: 0.35, abafado, SEM pan', a.ganho === 0.35 && a.abafado && !a.panLivre);
a = SB.audibilidade({ pos: [9, 9], visao: vis, mePos: [5, 5], mestre: true });
check('mestre nunca ouve abafado', a.ganho === 1 && !a.abafado);
a = SB.audibilidade({ pos: [9, 9], visao: null, mePos: [5, 5] });
check('sem conjunto de visão (cidade): trata como visível', !a.abafado);
a = SB.audibilidade({ pos: [5.4, 4.6], visao: vis, mePos: [5, 5] });
check('posição fracionária arredonda para a casa', !a.abafado);

console.log('\n[4] escolherVariante');
check('lista vazia → -1', SB.escolherVariante(0, -1) === -1);
check('uma variante → 0', SB.escolherVariante(1, 0) === 0);
let repetiu = false, ult = -1;
for (let i = 0; i < 200; i++) { const v = SB.escolherVariante(3, ult); if (v === ult) repetiu = true; if (v < 0 || v > 2) repetiu = true; ult = v; }
check('3 variantes: nunca repete a anterior e fica no intervalo', !repetiu);
check('rnd injetável e determinístico', SB.escolherVariante(3, 0, () => 0) === 1 && SB.escolherVariante(3, 2, () => 0) === 0);

console.log('\n[5] criarLimitador');
const L = SB.criarLimitador(3);
check('primeiro toca', L.pode('moedas', 0, 0.5));
L.registrar('moedas', 0, 400, 0.5);
check('mesmo evento dentro do intervalo NÃO toca', !L.pode('moedas', 100, 0.5));
check('depois do intervalo toca', L.pode('moedas', SB.SFX.moedas.intervaloMs + 1, 0.5));
L.reset();
L.registrar('golpe_cortante', 0, 1000, 0.5); L.registrar('golpe_perfurante', 0, 1000, 0.5); L.registrar('clique', 0, 1000, 0.1);
check('teto cheio: descarta o novo', !L.pode('porta_abre', 10, 0.9));
check('teto libera quando os sons terminam', L.pode('porta_abre', 1001, 0.9));
check('evento desconhecido nunca toca', !L.pode('nao_existe', 5000, 1));

console.log('\n[6] diffSons');
const base = { portas: ['3,4'], me: { ouro: 10, bag: [{ id: 'x' }, null], gear: { weapon: { id: 'dagger' } }, nivel: 1 },
               meuTurno: false, missao: false, monstros: [{ id: 'm1', type: 'goblin', pos: [2, 2] }] };
let r = SB.diffSons(null, base);
check('primeiro estado só semeia (sem eventos)', r.eventos.length === 0);
check('monstros já visíveis no primeiro estado ficam ouvidos', r.snap.ouvidos.has('m1'));
const ev = (prev, atual) => SB.diffSons(prev, atual).eventos.map(e => e.evento);
const s0 = r.snap;
check('nada mudou → nada toca', ev(s0, base).length === 0);
r = SB.diffSons(s0, { ...base, portas: ['3,4', '7,8'] });
check('porta nova aberta → porta_abre com pos', r.eventos.length === 1 && r.eventos[0].evento === 'porta_abre' && r.eventos[0].pos[0] === 7 && r.eventos[0].pos[1] === 8);
check('ouro subiu → moedas', ev(s0, { ...base, me: { ...base.me, ouro: 25 } }).join() === 'moedas');
check('ouro caiu → nada', ev(s0, { ...base, me: { ...base.me, ouro: 5 } }).length === 0);
check('bolsa cresceu → item_pegar', ev(s0, { ...base, me: { ...base.me, bag: [{ id: 'x' }, { id: 'y' }] } }).join() === 'item_pegar');
check('gear mudou → só equipar (sem item_pegar)', ev(s0, { ...base, me: { ...base.me, bag: [{ id: 'x' }, { id: 'dagger' }], gear: {} } }).join() === 'equipar');
const comPocao = { ...base, me: { ...base.me, bag: [{ id: 'p', effect: 'heal', uses_left: 2 }] } };
const sP = SB.diffSons(null, comPocao).snap;
check('dose de poção gasta → beber', ev(sP, { ...base, me: { ...base.me, bag: [{ id: 'p', effect: 'heal', uses_left: 1 }] } }).join() === 'beber');
check('nível subiu → nivel', ev(s0, { ...base, me: { ...base.me, nivel: 2 } }).join() === 'nivel');
check('turno virou meu → sua_vez', ev(s0, { ...base, meuTurno: true }).join() === 'sua_vez');
check('missão cumprida → objetivo', ev(s0, { ...base, missao: true }).join() === 'objetivo');
r = SB.diffSons(s0, { ...base, monstros: [...base.monstros, { id: 'm2', type: 'lobo_cinzento', pos: [4, 4] }, { id: 'm3', type: 'goblin', pos: [5, 4] }] });
check('monstros novos visíveis → UM rugido só', r.eventos.filter(e => e.evento.startsWith('rugido_')).length === 1);
check('rugido do primeiro novo, com família e pos', r.eventos[0].evento === 'rugido_fera' && r.eventos[0].pos[0] === 4);
check('os dois novos ficam ouvidos', r.snap.ouvidos.has('m2') && r.snap.ouvidos.has('m3'));
check('monstro já ouvido não ruge de novo', ev(r.snap, { ...base, monstros: [{ id: 'm2', type: 'lobo_cinzento', pos: [4, 4] }] }).length === 0);
check('monstro sem voz (elemental) não ruge', ev(s0, { ...base, monstros: [{ id: 'e1', type: 'elemental_fogo', pos: [1, 1] }] }).length === 0);
check('sem herói (mestre): não quebra, só eventos globais', ev(s0, { ...base, me: null, missao: true }).join() === 'objetivo');

console.log('\n[7] eventoAmbiente');
check('preset conhecido', SB.eventoAmbiente('penumbra') === 'amb_penumbra');
check('preset desconhecido → masmorra', SB.eventoAmbiente('lua') === 'amb_masmorra');
check('ausente → masmorra', SB.eventoAmbiente(undefined) === 'amb_masmorra');
{
  const guardado = SB.SFX.amb_penumbra.arquivos;
  SB.SFX.amb_penumbra.arquivos = [];
  check('preset sem arquivo → masmorra', SB.eventoAmbiente('penumbra') === 'amb_masmorra');
  SB.SFX.amb_penumbra.arquivos = guardado;
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
