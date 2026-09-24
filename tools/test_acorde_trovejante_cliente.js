// Testes do feedback visual do Acorde Trovejante, sem navegador.
// Roda da raiz: node tools/test_acorde_trovejante_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');
const SRC = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){
  if(cond){ PASS++; console.log('  ✅ ' + name); }
  else { FAIL++; console.log('  ❌ ' + name); }
}
function fnSource(name){
  const i=SRC.indexOf('function '+name+'(');
  if(i<0)throw new Error('função não encontrada: '+name);
  const sig=/\)\s*\{/g;sig.lastIndex=i;const m=sig.exec(SRC);
  if(!m)throw new Error('corpo não encontrado: '+name);
  const body=m.index+m[0].lastIndexOf('{');let depth=0;
  for(let k=body;k<SRC.length;k++){
    if(SRC[k]==='{')depth++;
    else if(SRC[k]==='}'&&--depth===0)return SRC.slice(i,k+1);
  }
  throw new Error('chaves desbalanceadas: '+name);
}
const performance={now:()=>1000};
const code=[
  'const ACORDE_TROVEJANTE_DEFAULT_EXPAND_MS=690;',
  'const ACORDE_TROVEJANTE_DEFAULT_SHATTER_MS=720;',
  'const ACORDE_TROVEJANTE_DEFAULT_SHARD_MS=610;',
  fnSource('_acordeTrovejanteHash'),
  fnSource('_acordeTrovejanteAnimFromMessage'),
].join('\n');
const api=new Function('performance','Math','Date',code+'\nreturn {_acordeTrovejanteAnimFromMessage};')(
  performance,Math,Date);

console.log('\n[1] Contrato do evento e tempos da animação');
const anim=api._acordeTrovejanteAnimFromMessage({animation_id:'acorde-test-1',caster_id:'p1',origin:[5,5],radius:2});
check('evento válido cria animação no ponto do bardo',!!anim&&anim.origin[0]===5&&anim.origin[1]===5);
check('raio real do instrumento é conservado',anim?.radius===2&&anim.extent>2);
check('expansão termina antes do estilhaçamento',anim?.shatterAt-anim.start>=anim.expandMs);
check('evento sem origem é descartado',api._acordeTrovejanteAnimFromMessage({radius:2})===null);

console.log('\n[2] Prévia vermelha e estilhaçamento');
check('hover do Tambor calcula casas do raio sem bloquear paredes',
  /function _iniciarPreviaAcordeTrovejante[\s\S]*window\._spellHL\.range = tiles/.test(SRC));
check('render 2D e 3D colorem essa prévia de vermelho',
  /window\._acordeTrovejantePreview/.test(SRC)
    && /AIM_COLORS\.blocked\.fill/.test(SRC)
    && /AIM_COLORS\.blocked\.hex/.test(SRC));
check('rompimento aciona tremor leve respeitando movimento reduzido',
  /pulseShake\(now,170,\.025/.test(SRC)&&/!_reduzMovimento\(\)/.test(fnSource('_acordeTrovejanteRuptura')));
check('animação é encaminhada pelo receptor compartilhado',
  /_receberAnimacaoAcordeTrovejante,/.test(SRC));

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exitCode=FAIL?1:0;
