// Mensagens de RECUSA do servidor ao jogador (etapa 4a do idioma).
//
// Diferente do catalogo.js, este arquivo é mantido À MÃO: depois da migração o
// server.py não contém mais o texto em português, só a chave, então não há de
// onde gerar de novo. A chave é o slug do texto original, o que garante que a
// mesma recusa use sempre a mesma frase.
window.LANG_ERROS = {
  "erro.sala_cheia_maximo_6_herois_1_mestre": {
    "pt": "Sala cheia (máximo 6 heróis + 1 mestre).",
    "en": "Room full (max 6 heroes + 1 master)."
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_ERROS);
