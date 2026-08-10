// Dicionário único do jogo — lido pelo CLIENTE via <script> (window.LANG_STRINGS)
// e pelo SERVIDOR via json.loads do objeto abaixo (server.py, _load_lang).
//
// REGRAS DO ARQUIVO:
//   • É JSON estrito dentro das chaves: aspas duplas, sem vírgula sobrando,
//     sem comentários DENTRO do objeto. Fora dele, comentários são livres —
//     o servidor ancora o recorte na LINHA "window.LANG_STRINGS =" (início
//     de linha, nunca dentro de comentário), não na primeira chave do arquivo.
//   • Parâmetros são {nome} e são substituídos por nome, nunca por posição.
//   • Falta a chave "en"? Cai no "pt". É isso que permite traduzir em lotes.
window.LANG_STRINGS = {
  "narracao.abre_porta": {
    "pt": "🚪 **{nome}** abre uma porta!",
    "en": "🚪 **{nome}** opens a door!"
  },
  "erro.porta_longe": {
    "pt": "Aproxime-se da porta para abri-la.",
    "en": "Get closer to the door to open it."
  },
  "ui.menu.audio_title": { "pt": "Áudio, idioma e opções", "en": "Audio, language and options" },
  "ui.menu.musica":      { "pt": "🎵 Música", "en": "🎵 Music" },
  "ui.menu.sons":        { "pt": "🔊 Sons", "en": "🔊 Sounds" },
  "ui.menu.idioma":      { "pt": "🌐 Idioma", "en": "🌐 Language" },
  "ui.menu.voltar_inicio": { "pt": "⌂ Voltar ao menu inicial", "en": "⌂ Back to main menu" },
  "ui.menu.sair":        { "pt": "⏻ Sair do jogo", "en": "⏻ Quit game" },
  "ui.menu.timer_ativo":   { "pt": "⏳ Limite de turno: ATIVO — desativar",
                             "en": "⏳ Turn limit: ON — turn off" },
  "ui.menu.timer_inativo": { "pt": "⏳ Limite de turno: DESATIVADO — ativar",
                             "en": "⏳ Turn limit: OFF — turn on" },
  "ui.menu.timer_nota_host":  { "pt": "Vale para toda a partida.",
                                "en": "Applies to the whole game." },
  "ui.menu.timer_nota_outro": { "pt": "Apenas o anfitrião pode alterar esta opção.",
                                "en": "Only the host can change this option." },
  "ui.menu.timer_so_host":    { "pt": "Somente o anfitrião pode alterar o limite de turno.",
                                "en": "Only the host can change the turn limit." }
};
