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

function montar(estado, temporarios) {
  const corpo = extrair('_menuStatusMarkup');
  const fabrica = new Function('GS', 't', '_rotulo', '_fmtBonus', '_modAtributo', '_modificadoresTemporariosStatus',
    corpo + '\nreturn _menuStatusMarkup;');
  const t = (k, p) => p && p.n != null ? `${k}:${p.n}` : k;
  return fabrica(
    { gameState: estado, cityState: null, getWarriorSelected: () => [] },
    t, (id, pre, pad) => pad, n => (n >= 0 ? '+' : '') + n, v => Math.floor(((v || 10) - 10) / 2),
    () => temporarios);
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

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
