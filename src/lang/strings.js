// Dicionário único do jogo — lido pelo CLIENTE via <script> (window.LANG_STRINGS)
// e pelo SERVIDOR via json.loads do objeto abaixo (server.py, _load_lang).
//
// REGRAS DO ARQUIVO:
//   • É JSON estrito dentro das chaves: aspas duplas, sem vírgula sobrando,
//     sem comentários DENTRO do objeto (este cabeçalho pode ter comentários,
//     desde que não use chaves de abertura ou fechamento).
//   • Parâmetros são marcados com o nome entre chaves (ex.: nome) e são
//     substituídos por nome, nunca por posição.
//   • Falta a chave "en"? Cai no "pt". É isso que permite traduzir em lotes.
window.LANG_STRINGS = {
  "narracao.abre_porta": {
    "pt": "🚪 **{nome}** abre uma porta!",
    "en": "🚪 **{nome}** opens a door!"
  },
  "erro.porta_longe": {
    "pt": "Aproxime-se da porta para abri-la.",
    "en": "Get closer to the door to open it."
  }
};
