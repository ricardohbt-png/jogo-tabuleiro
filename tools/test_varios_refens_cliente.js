// Vários reféns — lado do cliente. Roda da raiz:
//   node tools/test_varios_refens_cliente.js
//
// O servidor manda `game_state.prisoners` (lista, cada um com `id` refem_N) e
// não manda mais o campo singular `prisoner`. O cliente precisa desenhar e
// controlar cada refém pelo id: libertar o certo, ocupar a casa de todos,
// reconhecer a vez de cada um na janela pós-turno e nunca mostrar quem já
// chegou a salvo, morreu ou saiu do tabuleiro ([-1,-1]).
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const raiz = path.join(__dirname, '..');

let PASS = 0, FAIL = 0;
function check(nome, cond, extra) {
  if (cond) { PASS++; console.log('  ✅ ' + nome); }
  else { FAIL++; console.log('  ❌ ' + nome + (extra ? '\n     ' + extra : '')); }
}

const enviados = [];
const sandbox = {
  window: {}, console,
  WebSocket: class { constructor() { this.readyState = 1; } send(s) { enviados.push(JSON.parse(s)); } close() {} },
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  location: { search: '', protocol: 'http:', host: 'x' },
  setTimeout: () => 0, clearTimeout: () => {}, setInterval, clearInterval,
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(raiz, 'src', 'gameState.js'), 'utf8')
  + '\n;globalThis.__GS = GS;', sandbox);
const GS = sandbox.__GS;
GS.connect('ws://x', 'Ana', 'create');

const piso = Array.from({ length: 6 }, () => Array(8).fill(1));
const refem = (id, extra = {}) => Object.assign(
  { id, nome: id, pos: [0, 0], alive: true, freed: false, salvo: false,
    rescuer_pid: null, modo: 'guiar', hp: 7, max_hp: 7, moves_left: 0 }, extra);

function estado({ prisoners, janela = null, atual = null, turno = 'm', extra = {} }) {
  GS.injectPreviewState(Object.assign({
    type: 'game_state', phase: 'playing', master_pid: 'm', current_turn: turno,
    tiles: piso, explored: [], chests: [], monsters: [], decorations: [], rooms: [], materiais: {},
    players: [{ id: 'm', name: 'Ana', class_id: 'paladin', alive: true, pos: [2, 2], moves_left: 6 }],
    prisoners,
    animados_turn: janela, animados_order: [],
    animados_atual: janela ? { m: atual } : {}, animados_done: [],
  }, extra));
}

console.log('\n[1] GS.prisoners: só quem está no tabuleiro');
estado({ prisoners: [
  refem('refem_0', { pos: [3, 3] }),
  refem('refem_1', { pos: [1, 1], salvo: true }),
  refem('refem_2', { pos: [4, 4], alive: false, hp: 0 }),
  refem('refem_3', { pos: [-1, -1] }),
  refem('refem_4', { pos: [5, 5], freed: true, rescuer_pid: 'm' }),
] });
const ids = (GS.prisoners || []).map(p => p.id);
check('lista com os dois do mapa, na ordem', JSON.stringify(ids) === '["refem_0","refem_4"]', JSON.stringify(ids));
check('GS.prisoner é o primeiro do mapa', GS.prisoner && GS.prisoner.id === 'refem_0');
check('ehRefemId reconhece qualquer refém da lista', GS.ehRefemId('refem_4') && GS.ehRefemId('refem_1'));
check('ehRefemId recusa servo e o apelido antigo', !GS.ehRefemId('a1') && !GS.ehRefemId('prisoner'));
estado({ prisoners: [refem('refem_0', { salvo: true })] });
check('todos salvos: GS.prisoner é null', GS.prisoner === null && GS.prisoners.length === 0);
estado({ prisoners: [], extra: { prisoner: refem('velho', { pos: [3, 2] }) } });
check('campo singular antigo é ignorado', GS.prisoner === null);

console.log('\n[2] refensLibertaveis: cativos vivos adjacentes, na minha vez');
const quatro = [
  refem('refem_0', { pos: [3, 2] }),                                  // adjacente, cativo
  refem('refem_1', { pos: [1, 1] }),                                  // adjacente (diagonal), cativo
  refem('refem_2', { pos: [2, 3], freed: true, rescuer_pid: 'm' }),   // adjacente, já liberto
  refem('refem_3', { pos: [2, 1], alive: false, hp: 0 }),             // adjacente, morto
  refem('refem_4', { pos: [5, 5] }),                                  // longe
];
estado({ prisoners: quatro });
const lib = GS.refensLibertaveis().map(p => p.id);
check('só os dois cativos vivos adjacentes', JSON.stringify(lib) === '["refem_0","refem_1"]', JSON.stringify(lib));
check('prisioneiroLibertavel continua verdadeiro', GS.prisioneiroLibertavel === true);
estado({ prisoners: quatro, turno: 'outro' });
check('fora da vez: nenhum', GS.refensLibertaveis().length === 0 && GS.prisioneiroLibertavel === false);

console.log('\n[3] Toda casa de refém do mapa é ocupada');
estado({ prisoners: [
  refem('refem_0', { pos: [3, 2] }),
  refem('refem_1', { pos: [2, 3], freed: true, rescuer_pid: 'm' }),
  refem('refem_2', { pos: [1, 2], salvo: true }),
] });
const exp = new Set(); for (let y = 0; y < 6; y++) for (let x = 0; x < 8; x++) exp.add(`${x},${y}`);
const azuis = new Set(); GS.bfsReachable(piso, exp, 2, 2, 3, azuis);
check('casa do cativo não é destino', !azuis.has('3,2'));
check('casa do liberto não é destino', !azuis.has('2,3'));
check('casa de quem chegou a salvo fica livre', azuis.has('1,2'));

console.log('\n[4] Janela pós-turno: a vez de cada refém pelo id');
const guias = [
  refem('refem_0', { pos: [3, 2], freed: true, rescuer_pid: 'm', moves_left: 6 }),
  refem('refem_1', { pos: [4, 2], freed: true, rescuer_pid: 'm', moves_left: 6 }),
];
estado({ prisoners: guias, janela: 'm', atual: 'refem_1' });
check('seleção do refém da vez é válida', GS.animadoSelecaoValida('refem_1') === true);
check('outro refém fora da vez não é', GS.animadoSelecaoValida('refem_0') === false);
check('o botão encerra o refém da vez', GS.animadoPendenteParaEncerrar('refem_0') === 'refem_1');
const peca = GS.pecaControlada();
check('pecaControlada aponta o refém da vez',
  peca && peca.kind === 'prisoner' && peca.id === 'refem_1' && peca.ref.id === 'refem_1'
  && peca.pos[0] === 4 && peca.moves_left === 6, JSON.stringify(peca && { k: peca.kind, id: peca.id }));

console.log('\n[5] Mensagens levam o id do refém');
enviados.length = 0;
GS.libertarPrisioneiro('refem_1');
GS.moverPrisioneiro(1, 0, 'refem_1');
GS.moverPrisioneiroCaminho([[1, 0], [0, 1]], 'refem_0');
const [lb, mv, cm] = enviados;
check('libertar_prisioneiro com refem_id', lb && lb.type === 'libertar_prisioneiro' && lb.refem_id === 'refem_1');
check('mover_prisioneiro com refem_id', mv && mv.type === 'mover_prisioneiro' && mv.refem_id === 'refem_1' && mv.dx === 1);
check('mover_prisioneiro_caminho com refem_id', cm && cm.type === 'mover_prisioneiro_caminho'
  && cm.refem_id === 'refem_0' && cm.path.length === 2);
enviados.length = 0;
GS.libertarPrisioneiro();
check('sem id, o servidor escolhe (campo ausente)', enviados[0] && !('refem_id' in enviados[0]));

console.log('\n[6] game.js não conhece mais o refém único');
const gj = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
check('sem a chave pr:singleton', !gj.includes('pr:singleton'));
check('sem o apelido __prisoner__', !gj.includes('__prisoner__'));
check('sem o apelido __prisioneiro__', !gj.includes('__prisioneiro__'));
check('sem leitura de state.prisoner / st.prisoner',
  !/\b(state|st|_st|msg)\??\.prisoner\b/.test(gj), (gj.match(/\b(state|st|_st|msg)\??\.prisoner\b.{0,30}/) || [''])[0]);
check('sem comparação com o literal "prisoner" como id de peça', !/=== ?'prisoner'\s*\)?\s*[?{]/.test(gj.replace(/kind ?=== ?'prisoner'/g, '')));
check('um peão 3D por refém', gj.includes("obterFig('prisoner:'+"));
check('getPrisonerMesh recebe o id', /function getPrisonerMesh\(id\)/.test(gj));
check('_prisSel guarda id ou null', /let _prisSel = null;/.test(gj));
check('mais de um cativo abre a escolha', gj.includes('ui.hud.libertar_qual'));
check('o deslize do servidor acha o peão do refém', /getPrisonerMesh\(id\)/.test(gj));
const gs = fs.readFileSync(path.join(raiz, 'src', 'gameState.js'), 'utf8');
check('gameState.js não lê gameState.prisoner', !/gameState\??\.prisoner\b/.test(gs));

console.log('\n[7] Texto novo traduzido');
const lang = fs.readFileSync(path.join(raiz, 'src', 'lang', 'interface.js'), 'utf8');
const blocoQual = (lang.match(/"ui\.hud\.libertar_qual":\s*\{[^}]*\}/) || [''])[0];
check('ui.hud.libertar_qual tem pt e en', /"pt":\s*"[^"]+"/.test(blocoQual) && /"en":\s*"[^"]+"/.test(blocoQual));

console.log('\n[8] Rótulo do refém: nome próprio, "Prisioneiro" traduzido e numerado');
const semNome = [
  refem('refem_0', { pos: [3, 2], nome: 'Prisioneiro' }),
  refem('refem_1', { pos: [1, 1], nome: null }),
  refem('refem_2', { pos: [2, 1], nome: 'Elara' }),
];
check('nome padrão não é nome próprio', GS.nomeProprioRefem(semNome[0]) === null && GS.nomeProprioRefem(semNome[1]) === null);
check('nome do autor é nome próprio', GS.nomeProprioRefem(semNome[2]) === 'Elara');
const rot = GS.rotulosRefens(semNome, 'Prisoner', (nome, n) => `${nome} ${n}`);
check('dois sem nome ganham rótulos distintos', rot.get('refem_0') === 'Prisoner 1' && rot.get('refem_1') === 'Prisoner 2',
  JSON.stringify([...rot]));
check('o nomeado mantém o nome', rot.get('refem_2') === 'Elara');
check('um só sem nome não ganha número',
  GS.rotulosRefens([semNome[0], semNome[2]], 'Prisoner', (nome, n) => `${nome} ${n}`).get('refem_0') === 'Prisoner');
// O _rotuloRefem real do game.js, com o tradutor em inglês do dicionário.
const ini = gj.indexOf('function _rotuloRefem(');
const fim = gj.indexOf('\n}', ini) + 2;
const ctxLang = { window: { LANG_STRINGS: {} } };
vm.runInNewContext(lang, ctxLang);
const dic = ctxLang.window.LANG_INTERFACE;
const tEn = (k, p = {}) => String((dic[k] || {}).en || k).replace(/\{(\w+)\}/g, (_, x) => p[x]);
const rotuloRefem = vm.runInNewContext(`(${gj.slice(ini, fim)})`, { GS, t: tEn });
estado({ prisoners: semNome });
const rotulosEn = semNome.map(pr => rotuloRefem(pr));
check('em inglês, o padrão não sai "Prisioneiro" cru', rotulosEn.every(r => !r.includes('Prisioneiro')), JSON.stringify(rotulosEn));
check('em inglês, dois sem nome são distintos', rotulosEn[0] !== rotulosEn[1] && rotulosEn[0].startsWith('Prisoner'));
check('em inglês, o nomeado mantém o nome', rotulosEn[2] === 'Elara');
check('modal, Protetor e lista do Paladino usam _rotuloRefem',
  /function libertarRefem\(\)[\s\S]{0,400}_rotuloRefem\(pr\)/.test(gj)
  && /_aliadosNoRaioPaladin[\s\S]{0,700}_rotuloRefem\(pr, st\)/.test(gj)
  && /refemProtegido \? \{name:_rotuloRefem\(refemProtegido\)\}/.test(gj));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
