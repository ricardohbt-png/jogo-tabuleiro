// Menu de Status (tecla S): efeito temporário com `ate` (Defesa Impecável,
// Resistência Absoluta) derrubava _menuStatusMarkup com ReferenceError — a
// variável `r` (rodada atual) só existia em _modificadoresTemporariosStatus.
// Extrai a função REAL do game.js e a roda com stubs.
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');

let pass = 0, fail = 0;
const check = (nome, cond) => { if (cond) { pass++; console.log('  ✅ ' + nome); } else { fail++; console.log('  ❌ ' + nome); } };

function extrair(nome) {
  const ini = src.indexOf('\nfunction ' + nome + '(');
  if (ini < 0) throw new Error('função não encontrada: ' + nome);
  const fim = src.indexOf('\n}', ini);
  return src.slice(ini, fim + 2);
}

function montar(estado, temporarios, armaBaseId = id => id) {
  const corpo = extrair('_weaponAttributeKey') + '\n' + extrair('_percepcaoDetalhesStatus') + '\n' + extrair('_menuStatusMarkup');
  const fabrica = new Function('GS', 't', '_rotulo', '_fmtBonus', '_modAtributo', '_modificadoresTemporariosStatus',
    corpo + '\nreturn _menuStatusMarkup;');
  const t = (k, p) => p && p.n != null ? `${k}:${p.n}` : k;
  return fabrica(
    { gameState: estado, cityState: null, getWarriorSelected: () => [], armaBaseId },
    t, (id, pre, pad) => pad, n => (n >= 0 ? '+' : '') + n, v => Math.floor(((v || 10) - 10) / 2),
    () => temporarios);
}

// A ficha deve concordar com as regras do servidor para ambas as mãos.
{
  const fn = montar(null, []);
  const p = {class_id:'rogue',str_:10,dex:18,atk_bonus:5,level_bonus:1,fome:50,sede:50,
    weapon:{id:'shortsword',stat:'str_',die:'1d6'},
    gear:{off_hand:{id:'dagger',stat:'str_',die:'1d4',finesse:true}}};
  check('Ladino: espada usa FOR no acerto', fn(p).includes('ui.status.acerto_total</span><b>+1</b>'));
  check('Ladino: adaga usa DES superior na segunda mão', fn(p).includes('ui.status.acerto_mao_sec</span><b>+5</b>'));
  p.class_id='warrior'; p.atk_bonus=1;
  p.weapon={id:'longbow',stat:'dex',die:'1d8'};
  check('Guerreiro: arco usa DES no acerto', fn(p).includes('ui.status.acerto_total</span><b>+5</b>'));
}

const heroi = { name: 'Victor', ac: 14, fort: 2, ref_: 1, will: 0, str_: 14, atk_bonus: 3, fome: 50, sede: 50 };

console.log('\n[1] Efeito com `ate` (Defesa Impecável) não derruba o painel');
{
  const fn = montar({ round: 3 }, [{ nome: 'Defesa Impecável', efeito: 'x', ate: 5, rodadas: null }]);
  let html = null, erro = null;
  try { html = fn(heroi); } catch (e) { erro = e; }
  check('sem exceção', erro === null);
  check('mostra 2 rodadas restantes (5 - 3)', html && html.includes('ui.status.rodadas_restantes:2'));
}

console.log('\n[2] Efeito já vencido não mostra contador');
{
  const fn = montar({ round: 9 }, [{ nome: 'Resistência Absoluta', efeito: 'x', ate: 5, rodadas: null }]);
  const html = fn(heroi);
  check('sem contador', !html.includes('rodadas_restantes'));
}

console.log('\n[3] Na cidade (sem gameState) também não quebra');
{
  const fn = montar(null, [{ nome: 'Defesa Impecável', efeito: 'x', ate: 5, rodadas: null }]);
  let erro = null;
  try { fn(heroi); } catch (e) { erro = e; }
  check('sem exceção', erro === null);
}

// Materiais não integram p.atk_bonus: devem somar no total da arma.
{
  const fn = montar(null, []);
  const p = {...heroi, dex: 12, level_bonus: 1,
    weapon: {id:'shortsword_aco_damasco',die:'1d6',stat:'str_',atk_bonus:1},
    gear: {off_hand:{id:'dagger_obsidiana_ferro',die:'1d4',finesse:true,damage_bonus:1}}};
  const html = fn(p);
  check('Damasco soma +1 ao acerto principal', html.includes('ui.status.acerto_total</span><b>+4</b>'));
  check('Obsidiana soma +1 ao dano secundário', html.includes('1d4 +2 → 1d4 +3'));
  p.gear.off_hand.atk_bonus = 1;
  check('material soma ao acerto secundário', fn(p).includes('ui.status.acerto_mao_sec</span><b>+4</b>'));
  p.weapon = {...p.weapon, atk_bonus:0,dmg_bonus:0,damage_bonus:1};
  check('dano material soma mesmo com dmg_bonus zero', fn(p).includes('1d6 +2 → 1d6 +3'));
}

// Executa o coletor real: bebidas precisam aparecer com suas durações por dose.
{
  const t = (k, p) => k + (p ? ':' + p.n : '');
  const fn = new Function('GS', 't', '_rotulo', 'GRIMORIO_CLIENT',
    extrair('_modificadoresTemporariosStatus') + '\nreturn _modificadoresTemporariosStatus;')(
      {gameState:{round:1}, getWarriorSelected:()=>[]}, t, (id, pre, fallback)=>fallback, {});
  const base = {fome:50, sede:50};
  for(const [id, field] of [['hidromel','hidromel_penalty_rodadas'], ['rum','rum_penalty_rodadas'], ['absinto','absinto_penalty_rodadas']]){
    const rows = fn({...base, [field]:[10,7]});
    const drinks = rows.filter(r => r.nome.includes(`cat.item.${id}.nome`));
    check(`${id}: duas doses mantêm seus prazos 10 e 7`, drinks.length === 2 && drinks[0].rodadas === 10 && drinks[1].rodadas === 7);
    const stacked = fn({...base, [field]:[10,10]});
    check(`${id}: doses de mesmo prazo mostram penalidade acumulada`, stacked.some(r => r.efeito === `ui.status.${id}_penalidade_ef:2` && r.rodadas === 10));
    check(`${id}: efeito expirado some`, !fn({...base,[field]:[]}).some(r => r.nome.includes(`cat.item.${id}.nome`)));
  }
  for(const [flag,timer] of [['vinho_ativo','vinho_rodadas'], ['cerveja_ativo','cerveja_rodadas'], ['cerveja_ana_ca_ativo','cerveja_ana_ca_rodadas']])
    check(`${flag}: aparece por 10 rodadas`, fn({...base,[flag]:true,[timer]:10}).some(r => r.rodadas === 10));
  const heavy = fn({...base,absinto_penalty_rodadas:[1,3,5,7,9]});
  check('absinto: cinco doses mostram -2 movimento até a primeira expiração', heavy.some(r => r.efeito === 'ui.status.bebida_movimento_ef:2' && r.rodadas === 1));
  const light = fn({...base,absinto_penalty_rodadas:[3,5,7,9]});
  check('absinto: quatro doses mostram -1 movimento até restarem duas', light.some(r => r.efeito === 'ui.status.bebida_movimento_ef:1' && r.rodadas === 5));
}

// Arco Bruto do Combatente (e variantes): Força soma ao DANO, nunca ao acerto.
{
  // armaBaseId real: tira o sufixo de material (como GS.armaBaseId no jogo).
  const fn = montar(null, [], id => id.replace(/_(aco_damasco|obsidiana_ferro|liga_titanio|freixo_negro|cedro_rubro|cerne_tita|prata)$/, ''));
  const p = {class_id:'warrior',str_:18,dex:14,atk_bonus:3,level_bonus:1,fome:50,sede:50,
    weapon:{id:'arco_bruto_combatente',stat:'dex',die:'1d10',add_strength_to_damage:true},gear:{}};
  check('Arco Bruto: dano soma DES + FOR (+2 +4)', fn(p).includes('1d10 +6 →'));
  // atk_bonus 3 já embute a FOR +4 da classe: 3 − 4 + DES +2 = +1 (a Força não entra no acerto).
  check('Arco Bruto: acerto continua só com DES', fn(p).includes('ui.status.acerto_total</span><b>+1</b>'));
  p.weapon = {id:'arco_bruto_combatente_cedro_rubro',stat:'dex',die:'1d10',add_strength_to_damage:true};
  check('Variante do Arco Bruto também soma a Força no dano', fn(p).includes('1d10 +6 →'));
  p.weapon = {id:'arco_composto_longo',stat:'dex',die:'1d10'};
  check('Outro arco continua só com DES no dano', fn(p).includes('1d10 +2 →'));
}

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
