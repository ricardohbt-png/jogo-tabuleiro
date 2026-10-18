// Regressão: pontos extras com o mesmo ID em cidades diferentes devem ser recriados.
// node tools/test_city_hotspots_location_cliente.js
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8').replace(/\r\n/g, '\n');
function extrair(src, nome){
  const i = src.indexOf('function ' + nome + '(');
  assert(i >= 0, 'função não encontrada: ' + nome);
  let j = src.indexOf('{', i), prof = 0;
  for(; j < src.length; j++){
    if(src[j] === '{') prof++;
    else if(src[j] === '}' && --prof === 0) break;
  }
  return src.slice(i, j + 1);
}

const helpers = extrair(game, '_resetCityExtraHotspotsForLocation');
const refresh = extrair(game, '_refreshCityLocation');
assert(refresh.indexOf('_resetCityExtraHotspotsForLocation(location.id)') < refresh.indexOf("querySelectorAll('[data-city-point]')"),
  'os pontos antigos devem ser removidos antes de reconciliar os IDs da nova cidade');

const caravanMarker = { dataset: { cityExtra: '1', cityPoint: 'ponto_1' }, removed: false,
  remove(){ this.removed = true; } };
const farmMarker = { dataset: { cityExtra: '1', cityPoint: 'ponto_1' }, removed: false,
  remove(){ this.removed = true; } };
const nativeMarker = { dataset: { cityPoint: 'taverna' }, removed: false,
  remove(){ this.removed = true; } };
const markers = [caravanMarker, nativeMarker];
const context = {
  _cityImg: { locationId: 'vila_dos_charcos', hotWrap: {
    querySelectorAll(selector){
      assert.strictEqual(selector, '[data-city-extra]');
      return markers.filter(marker => marker.dataset.cityExtra && !marker.removed);
    },
  } },
};
const reset = new Function('_cityImg', helpers + '; return _resetCityExtraHotspotsForLocation;')(context._cityImg);

reset('alva_e_luz');
assert(caravanMarker.removed, 'o botão antigo de caravana deve sair ao entrar em Alva');
assert.strictEqual(context._cityImg.locationId, 'alva_e_luz', 'a cidade atual deve ser registrada');
assert(!nativeMarker.removed, 'hotspots nativos não devem ser removidos');

markers.push(farmMarker);
reset('alva_e_luz');
assert(!farmMarker.removed, 'atualizações na mesma cidade devem preservar o botão');

reset('vila_dos_charcos');
assert(farmMarker.removed, 'o botão da Fazenda deve sair ao voltar para Charcos');
assert.strictEqual(context._cityImg.locationId, 'vila_dos_charcos');

console.log('OK: ponto_1 é reconstruído ao trocar entre Charcos e Alva, sem apagar hotspots nativos.');
