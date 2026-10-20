// Velocidade do turno dos inimigos — interface (análise estática do game.js).
// Roda da raiz: node tools/test_turno_inimigo_ui.js
'use strict';
const fs = require('fs'), path = require('path');
const source = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
const lang = fs.readFileSync(path.join(__dirname, '..', 'src', 'lang', 'interface.js'), 'utf8');
let pass = 0, fail = 0;
function check(label, ok) { if (ok) { pass++; console.log('  ✅ ' + label); } else { fail++; console.log('  ❌ ' + label); } }
function body(name) {
  const start = source.indexOf(`function ${name}(`);
  if (start < 0) return '';
  const brace = source.indexOf('{', start);
  let depth = 0;
  for (let i = brace; i < source.length; i++) {
    if (source[i] === '{') depth++;
    if (source[i] === '}' && --depth === 0) return source.slice(brace + 1, i);
  }
  return '';
}
const count = (re) => (source.match(re) || []).length;

console.log('\n[1] Seletor nas configurações do jogo');
check('o painel ⚙️ tem os dois seletores', source.includes('id="cfg-ritmo-nivel"') && source.includes('id="cfg-ritmo-auto"'));
const ref = body('_refreshVelocidadeInimigosOption');
check('o refresh usa o nível do estado e o anfitrião', ref.includes('GS.velocidadeInimigos') && ref.includes('souAnfitriao'));
check('"Passo a passo" só aparece quando o servidor permite (Solo)', ref.includes('ritmo_passo_permitido') && ref.includes("'passo'"));
check('o tempo automático só aparece no passo a passo', ref.includes('ritmoAutoSegundos') && /cfg-ritmo-auto/.test(ref));
const envio = source.slice(source.indexOf('const _enviarRitmo'), source.indexOf('const _enviarRitmo') + 700);
check('trocar o nível ou o tempo chama o mesmo envio', /cfg-ritmo-nivel'\)\.onchange = _enviarRitmo/.test(source)
  && /cfg-ritmo-auto'\)\.onchange = _enviarRitmo/.test(source));
check('o envio manda o nível ao servidor', envio.includes('GS.setVelocidadeInimigos'));
check('quem não é anfitrião não envia', envio.includes('souAnfitriao') && envio.indexOf('souAnfitriao') < envio.indexOf('GS.setVelocidadeInimigos'));
check('o refresh roda onde os outros da sala rodam',
  count(/_refreshVelocidadeInimigosOption\(\);/g) >= count(/_refreshAtravessarOption\(\);/g));

console.log('\n[2] Faixa de resumo');
const faixa = body('_renderFaixaInimigo');
check('a faixa existe e é montada por DOM (sem innerHTML com texto do servidor)',
  !!faixa && faixa.includes('faixa-inimigo') && !/innerHTML\s*=\s*[^;]*(atacante_nome|alvo_nome)/.test(faixa));
const textoAtq = body('_textoAtaqueInimigo');
check('mostra quem, em quem, resultado e dano', faixa.includes('atacante_nome') && faixa.includes('alvo_nome')
  && textoAtq.includes('acertou') && textoAtq.includes('dano') && textoAtq.includes('impacto'));
check('versão genérica sem nome do monstro', faixa.includes('generico'));
check('o botão Continuar só existe quando a espera é por clique', faixa.includes("'clique'") && faixa.includes('GS.continuarTurnoInimigo'));
check('Enter/Espaço continuam a faixa', body('_teclaFaixaInimigo').includes('GS.continuarTurnoInimigo')
  && /_teclaFaixaInimigo\(/.test(source.slice(source.indexOf("document.addEventListener('keydown'"))));
check('o botão de confirmar do controle também', body('_gamepadAccept').includes('_faixaInimigoAberta'));
check('um único GS.on por evento', count(/GS\.on\('turnoInimigo'/g) === 1 && count(/GS\.on\('resumoInimigo'/g) === 1);
check('o idioma redesenha a faixa aberta', body('_setLang').includes('_renderFaixaInimigo'));

console.log('\n[3] Anel no monstro que age');
check('2D: anel vermelho e tracejado desenhados no laço dos monstros visíveis',
  body('_anelInimigo2D').includes('setLineDash') && /_anelInimigo2D\(ctx/.test(source));
check('2D: a animação agenda redesenho enquanto há monstro agindo', body('_anelInimigo2D').includes('_agendarChamas2D'));
const a3 = body('_anelInimigo3D');
check('3D: anel por monstro, sincronizado no laço de render', !!a3 && a3.includes('getMonsterMesh') && source.includes('_anelInimigo3D();'));
check('3D: limpa os anéis fora do turno', a3.includes('scene.remove'));
check('3D: o anel não passa pelo tone mapping (senão o vermelho desbota)', (a3.match(/toneMapped: false/g) || []).length === 2);
check('o anel acompanha o tamanho do monstro grande e fica no centro do peão',
  body('_anelInimigo2D').includes('logicalW') && a3.includes('_monsterFootprintSize') && a3.includes('fig.position.x'));

console.log('\n[4] Textos PT/EN');
const chaves = ['ui.turno_inimigo.atacou', 'ui.turno_inimigo.atacou_generico', 'ui.turno_inimigo.acertou',
  'ui.turno_inimigo.acertou_critico', 'ui.turno_inimigo.errou', 'ui.turno_inimigo.dano', 'ui.turno_inimigo.sem_dano',
  'ui.turno_inimigo.continuar', 'ui.menu.ritmo_titulo', 'ui.menu.ritmo_atual', 'ui.menu.ritmo_lento',
  'ui.menu.ritmo_muito_lento', 'ui.menu.ritmo_passo', 'ui.menu.ritmo_auto_off', 'ui.menu.ritmo_auto_n',
  'ui.menu.ritmo_so_host', 'ui.menu.ritmo_nota_host', 'ui.menu.ritmo_nota_outro'];
for (const k of chaves) {
  const bloco = lang.match(new RegExp('"' + k.replace(/\./g, '\\.') + '": \\{([\\s\\S]*?)\\n  \\}'));
  check(k + ' tem pt e en', !!bloco && /"pt":/.test(bloco[1]) && /"en":/.test(bloco[1]));
}

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
