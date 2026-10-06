// Agrupamento de "Meus Jogos" e fiação do cliente.
// Roda da raiz: node tools/test_pontos_salvamento_cliente.js
const fs = require('fs');
const path = require('path');
const gs = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');

let ok = 0, falhas = 0;
function check(nome, cond){ if(cond){ ok++; console.log('  ✅ ' + nome); } else { falhas++; console.log('  ❌ ' + nome); } }

function extrair(src, nome){
  const i = src.indexOf('function ' + nome + '(');
  if(i < 0) throw new Error('função não encontrada: ' + nome);
  let j = src.indexOf('{', i), prof = 0;
  for(; j < src.length; j++){ if(src[j] === '{') prof++; else if(src[j] === '}' && --prof === 0) break; }
  return src.slice(i, j + 1);
}
const agruparJogos = new Function(extrair(gs, 'agruparJogos') + '; return agruparJogos;')();

console.log('\n[1] Abas e grupos');
const lista = [
  { id: 'a', play_mode: 'solo', members: { ana: {} }, anfitriao: 'ana' },
  { id: 'b', play_mode: 'multiplayer', members: { ana: {}, bia: {} }, anfitriao: 'ana' },
  { id: 'c', play_mode: 'multiplayer', members: { ana: {}, bia: {} }, anfitriao: 'bia' },
  { id: 'd', play_mode: 'solo', members: { ana: {} }, anfitriao: 'ana', arquivado: true },
  { id: 'e', members: { ana: {}, bia: {} }, anfitriao: 'bia' },           // sem play_mode → multi
  { id: 'f', has_master: true, members: { ana: {} }, anfitriao: 'ana' },  // Mestre → multi
];
const g = agruparJogos(lista, 'ana');
check('solo: só os não arquivados', g.solo.ativos.map(s => s.id).join() === 'a');
check('solo: arquivados à parte', g.solo.arquivados.map(s => s.id).join() === 'd');
check('multi: que eu hospedo', g.multiplayer.hospedo.map(s => s.id).join() === 'b,f');
check('multi: que eu participo', g.multiplayer.participo.map(s => s.id).join() === 'c,e');
check('contagem da aba ignora arquivados', g.solo.total === 1 && g.multiplayer.total === 4);
check('lista vazia não quebra', agruparJogos(null, 'ana').solo.total === 0);

console.log('\n[2] Fiação');
for (const f of ['salvarPonto', 'carregarPonto', 'apagarPonto', 'novoCapitulo', 'arquivarJogo', 'agruparJogos'])
  check(`GS exporta ${f}`, new RegExp('\\b' + f + '\\b[,\\s]').test(gs.slice(gs.indexOf('Contas / Jogos Salvos (Fase 3)'))));
check("trata ponto_salvo", gs.includes("case 'ponto_salvo'"));
check('aba lembrada em lfh_aba_jogos', game.includes("'lfh_aba_jogos'"));
check('⚙️ tem Salvar agora', game.includes('cfg-salvar-ponto'));
check('render novo de Meus Jogos', game.includes('function _renderMeusJogos('));
check('continuação não cria jogo novo', !game.includes('continue_from: sg.id'));

console.log('\n[3] Rótulo do ponto e jogo encerrado');
const tStub = (k, p) => k + (p ? '|' + (p.local || '') : '');
const rotuloPonto = new Function('t', extrair(game, '_rotuloPonto') + '; return _rotuloPonto;')(tStub);
check('manual com nome usa o nome', rotuloPonto({ tipo: 'manual', nome: 'Antes do Troll' }) === 'Antes do Troll');
check('manual sem nome não vira "Estado salvo"', rotuloPonto({ tipo: 'manual', nome: '', local: 'Alva' }) === 'ui.save.ponto.manual|Alva');
check('automático sem rótulo cai em migrado', rotuloPonto({ tipo: 'auto' }).startsWith('ui.save.ponto.migrado|'));
check('antes de fundir tem rótulo próprio', rotuloPonto({ tipo: 'auto', rotulo: 'antes_de_fundir' }).startsWith('ui.save.ponto.antes_de_fundir|'));
check('Novo capítulo aparece com o jogo encerrado, menos para o Mestre que saiu',
  game.includes('if (encerrado ? !mestreQueSaiu : anfitriao) {'));
check('Continuar desligado em jogo encerrado, até para o antigo anfitrião', game.includes('cont.disabled = !!encerrado;'));
check('pontos de jogo encerrado não têm Carregar/apagar', game.includes('_linhaPonto(sg, p, anfitriao && !encerrado)'));
check('Encerrar some depois de encerrado', game.includes("sg.master_account === conta && !encerrado)"));

console.log(`\n${ok} ok, ${falhas} falha(s)`);
process.exit(falhas ? 1 : 0);
