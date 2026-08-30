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
//   • As chaves "lista.separador" e "lista.ultimo" são do MOTOR, não de
//     conteúdo: um parâmetro pode ser uma LISTA de fragmentos, e o t() a junta
//     com elas (" e " × " and "). NÃO dê parâmetros a essas duas — o _valor()
//     do cliente chama t() para lê-las, e um parâmetro criaria recursão.
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
  "ui.menu.audio":       { "pt": "🔊 Áudio", "en": "🔊 Audio" },
  "ui.menu.musica":      { "pt": "🎵 Música", "en": "🎵 Music" },
  "ui.menu.sons":        { "pt": "🔊 Sons", "en": "🔊 Sounds" },
  "ui.menu.idioma":      { "pt": "🌐 Idioma", "en": "🌐 Language" },
  "ui.menu.desempenho":  { "pt": "🖥️ Desempenho", "en": "🖥️ Performance" },
  "ui.menu.qualidade":   { "pt": "⚙ Qualidade", "en": "⚙ Quality" },
  "ui.menu.qual_alta":   { "pt": "Alta", "en": "High" },
  "ui.menu.qual_media":  { "pt": "Média", "en": "Medium" },
  "ui.menu.qual_baixa":  { "pt": "Baixa", "en": "Low" },
  "ui.menu.qual_dica":   { "pt": "Baixa desliga sombras e reduz luzes e resolução — use se a masmorra 3D estiver travando.", "en": "Low turns off shadows and cuts lights and resolution — use it if the 3D dungeon stutters." },
  "ui.menu.mostrar_fps": { "pt": "Mostrar FPS", "en": "Show FPS" },
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
                                "en": "Only the host can change the turn limit." },
  "ui.menu.timer_indisponivel": { "pt": "⏳ Limite de turno — entrar em uma partida",
                                   "en": "⏳ Turn limit — join a game" },
  "ui.menu.timer_nota_partida": { "pt": "Disponível quando uma partida estiver aberta.",
                                   "en": "Available when a game is open." },
  "ui.tooltip.tipo_dano": { "pt": "Tipo de dano", "en": "Damage type" },
  "ui.tooltip.categoria": { "pt": "Categoria", "en": "Category" },
  "ui.tooltip.area": { "pt": "Área", "en": "Area" },
  "ui.tooltip.materiais": { "pt": "Materiais", "en": "Materials" },
  "ui.tooltip.cone": { "pt": "Cone", "en": "Cone" },
  "ui.tooltip.medo": { "pt": "Medo", "en": "Fear" },
  "ui.tooltip.empurrao": { "pt": "Empurrão", "en": "Push" },
  "ui.tooltip.dano_repetido": { "pt": "Dano repetido", "en": "Repeated damage" },
  "ui.tooltip.falha_parcial": { "pt": "Falha parcial", "en": "Partial failure" },
  "ui.tooltip.resistente_corrosao": { "pt": "Resistente à corrosão", "en": "Corrosion resistant" },
  "ui.tooltip.runico": { "pt": "Rúnico", "en": "Runic" },
  "ui.connect.cover_hint":  { "pt": "Clique para começar", "en": "Click to start" },
  "ui.connect.subtitulo":   { "pt": "RPG de Tabuleiro Online — até 6 jogadores",
                              "en": "Online Tabletop RPG — up to 6 players" },
  "ui.connect.titulo":      { "pt": "Entrar na Aventura", "en": "Join the Adventure" },
  "ui.connect.nome_label":  { "pt": "Seu nome de herói", "en": "Your hero name" },
  "ui.connect.nome_ph":     { "pt": "Ex: Thorin", "en": "e.g. Thorin" },
  "ui.connect.servidor_label": { "pt": "Endereço do servidor", "en": "Server address" },
  "ui.connect.senha_label": { "pt": "Senha — para jogos salvos",
                              "en": "Password — for saved games" },
  "ui.connect.btn_conta":   { "pt": "🎲 Entrar com minha conta", "en": "🎲 Sign in with my account" },
  "ui.connect.ajuda_conta": { "pt": "Primeira vez? O apelido acima vira sua conta. Use o mesmo apelido + senha para voltar aos seus jogos.",
                              "en": "First time? The nickname above becomes your account. Use the same nickname + password to get back to your games." },
  "ui.connect.div_rapido":  { "pt": "ou jogo rápido (sem salvar)", "en": "or quick game (no saving)" },
  "ui.connect.btn_criar":   { "pt": "⚔ Criar Nova Sala", "en": "⚔ Create New Room" },
  "ui.connect.div_ou":      { "pt": "ou", "en": "or" },
  "ui.connect.codigo_label": { "pt": "Código da sala", "en": "Room code" },
  "ui.connect.btn_entrar":  { "pt": "Entrar", "en": "Join" },
  "ui.connect.btn_reconectar": { "pt": "🔌 Reconectar à última partida",
                                 "en": "🔌 Reconnect to last game" },
  "ui.savegames.titulo":    { "pt": "Meus Jogos", "en": "My Games" },
  "ui.savegames.div_amigo": { "pt": "entrar no jogo de um amigo", "en": "join a friend's game" },
  "ui.savegames.codigo_label": { "pt": "Código da sala do amigo", "en": "Friend's room code" },
  "ui.savegames.btn_entrar": { "pt": "Entrar", "en": "Join" },
  "ui.savegames.ajuda":     { "pt": "Peça o código que aparece no topo do lobby de quem criou o jogo. Você escolhe seu personagem lá e ele fica vinculado à sua conta.",
                              "en": "Ask for the code shown at the top of the lobby of whoever created the game. You pick your character there and it gets linked to your account." },
  "ui.savegames.div_criar": { "pt": "criar novo", "en": "create new" },
  "ui.savegames.nome_label": { "pt": "Nome do jogo", "en": "Game name" },
  "ui.savegames.nome_ph":   { "pt": "Ex: A Sociedade do Anel", "en": "e.g. The Fellowship of the Ring" },
  "ui.savegames.campanha_label": { "pt": "Campanha", "en": "Campaign" },
  "ui.savegames.mestre_label": { "pt": "Este jogo terá um Mestre humano",
                                 "en": "This game will have a human Game Master" },
  "ui.savegames.btn_criar": { "pt": "➕ Criar jogo", "en": "➕ Create game" },
  "ui.savegames.btn_voltar": { "pt": "← Voltar", "en": "← Back" },
  "lista.separador": { "pt": ", ",  "en": ", " },
  "lista.ultimo":    { "pt": " e ", "en": " and " }
};
