// NARRAÇÃO do mestre — o log que conta o que acontece na partida
// (etapa 4b-i do idioma).
//
// Como o erros.js e ao contrário do catalogo.js, é mantido À MÃO: depois da
// migração o server.py não contém mais o texto em português, só a chave, então
// não há de onde gerar de novo. A chave é o slug do texto SEM as interpolações.
window.LANG_NARRACAO = {};
Object.assign(window.LANG_STRINGS, window.LANG_NARRACAO);
