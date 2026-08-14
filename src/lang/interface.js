// INTERFACE do cliente (etapa 5) — rótulos, tooltips e mensagens de tela.
//
// Separado do strings.js porque este cresce muito (a etapa 5 traz ~636 chaves) e
// misturá-lo com as chaves de motor e das telas de conexão tornaria os dois
// difíceis de revisar. Mantido À MÃO, como o erros.js e o narracao.js.
//
// REGRAS DO ARQUIVO (as mesmas do strings.js):
//   • É JSON estrito dentro das chaves: aspas duplas, sem vírgula sobrando,
//     SEM COMENTÁRIO dentro do objeto. Fora dele, comentários são livres — o
//     servidor ancora o recorte na LINHA "window.LANG_INTERFACE =".
//   • Falta a chave "en"? Cai no "pt". É isso que permite traduzir em lotes.
//
// CONVENÇÃO: ui.<área>.<slug>, onde <área> é a TELA em que o texto aparece.
// A `ui.` tem PRIORIDADE sobre a `cat.` do servidor quando as duas existem —
// os catálogos do cliente guardam descrição mais rica (card HTML com alcance e
// efeito por rodada) que a frase curta do servidor. Ver aplicarCatalogo.
window.LANG_INTERFACE = {
  "ui.item.tipo.arma": {
    "en": "⚔ Weapon",
    "pt": "⚔ Arma"
  },
  "ui.item.tipo.armaDistancia": {
    "en": "🏹 Ranged",
    "pt": "🏹 Distância"
  },
  "ui.item.tipo.armadura": {
    "en": "🛡 Armor",
    "pt": "🛡 Armadura"
  },
  "ui.item.tipo.consumivel": {
    "en": "🍖 Consumable",
    "pt": "🍖 Consumível"
  },
  "ui.item.tipo.escudo": {
    "en": "🛡 Shield",
    "pt": "🛡 Escudo"
  },
  "ui.item.tipo.itemMagico": {
    "en": "🎒 Magic Item",
    "pt": "🎒 Item Mágico"
  },
  "ui.item.tipo.municao": {
    "en": "🎯 Ammunition",
    "pt": "🎯 Munição"
  },
  "ui.item.tipo.secundario": {
    "en": "🔦 Accessory",
    "pt": "🔦 Acessório"
  },
  "ui.item.tipo.varinha": {
    "en": "✨ Wand",
    "pt": "✨ Varinha"
  },
  "ui.mestre.custo.bonus": {
    "en": "BONUS",
    "pt": "BÔNUS"
  },
  "ui.mestre.custo.livre": {
    "en": "FREE",
    "pt": "LIVRE"
  },
  "ui.mestre.custo.principal": {
    "en": "ACTION",
    "pt": "AÇÃO"
  },
  "ui.objetivo.all_heroes_at_exit": {
    "en": "All heroes at the exit",
    "pt": "Todos os heróis na saída"
  },
  "ui.objetivo.kill_all": {
    "en": "Defeat every monster",
    "pt": "Eliminar todos os monstros"
  },
  "ui.objetivo.kill_target": {
    "en": "Defeat the target",
    "pt": "Derrotar o alvo"
  },
  "ui.objetivo.open_key_chest": {
    "en": "Open the key chest",
    "pt": "Abrir o baú-chave"
  },
  "ui.objetivo.reach_exit": {
    "en": "Reach the exit",
    "pt": "Chegar à saída"
  },
  "ui.objetivo.rescue_prisoner": {
    "en": "Rescue the prisoner",
    "pt": "Resgatar o prisioneiro"
  },
  "ui.objetivo.salas_obrigatorias": {
    "en": "Required rooms",
    "pt": "Salas obrigatórias"
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_INTERFACE);
