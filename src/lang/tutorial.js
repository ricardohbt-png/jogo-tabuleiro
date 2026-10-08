// Textos do tutorial guiado (janela da lição com passos). Mantido à mão.
window.LANG_TUTORIAL = {
  "ui.tutorial.passo_de": {
    "en": "Step {i} of {n}",
    "pt": "Passo {i} de {n}"
  },
  "ui.tutorial.me_mostra": {
    "en": "Show me",
    "pt": "Me mostra"
  },
  "ui.tutorial.entendi": {
    "en": "Got it",
    "pt": "Entendi"
  },
  "ui.tutorial.dica": {
    "en": "Hint",
    "pt": "Dica"
  },
  "ui.tutorial.dica_erro.fora_da_vez": {
    "en": "It is not your turn yet. Wait for the others to act.",
    "pt": "Ainda não é a sua vez. Espere os outros agirem."
  },
  "ui.tutorial.dica_erro.sem_acao": {
    "en": "You already used your main action this turn. End your turn to get it back.",
    "pt": "Você já usou sua ação principal neste turno. Encerre o turno para recuperá-la."
  },
  "ui.tutorial.dica_erro.longe_do_alvo": {
    "en": "The target is too far. Walk closer and try again.",
    "pt": "O alvo está longe. Ande até ficar perto dele e tente de novo."
  },
  "ui.tutorial.dica_erro.alvo_errado": {
    "en": "That is not the exercise target. Look for the highlighted one.",
    "pt": "Esse não é o alvo do exercício. Procure o que está destacado na tela."
  },
  "ui.tutorial.dica_erro.sem_sinfonia": {
    "en": "The Symphony only reinforces the stats your Lute covers. Turn the song off and sing it again choosing Attack.",
    "pt": "A Sinfonia só reforça os atributos que o Alaúde cobre. Desative a canção e entoe de novo escolhendo Acerto."
  },
  "ui.tutorial.dica_erro.sem_alvo_na_linha": {
    "en": "No dummy on that line. Stand in the same row or column as the dummy, up to 3 squares away.",
    "pt": "Nenhum boneco nessa linha. Fique na mesma linha ou coluna do boneco, a até 3 casas."
  },
  "ui.tutorial.resultado.acerto": {
    "en": "You rolled {roll} + {bonus} = {total} against AC {ca}: hit!",
    "pt": "Você rolou {roll} + {bonus} = {total} contra CA {ca}: acertou!"
  },
  "ui.tutorial.resultado.critico": {
    "en": "You rolled {roll} + {bonus} = {total} against AC {ca}: critical hit!",
    "pt": "Você rolou {roll} + {bonus} = {total} contra CA {ca}: acerto crítico!"
  },
  "ui.tutorial.resultado.erro": {
    "en": "You rolled {roll} + {bonus} = {total} against AC {ca}: miss. Try again.",
    "pt": "Você rolou {roll} + {bonus} = {total} contra CA {ca}: errou. Tente de novo."
  },
  "ui.tutorial.modelo.guild.aprendeu": {
    "en": "Repeat the exercise to try {nome} and see your new numbers.",
    "pt": "Repita o exercício com {nome} e veja seus novos valores."
  },
  "ui.tutorial.modelo.guild.repita": {
    "en": "Use the ability again and compare the new values.",
    "pt": "Use a habilidade de novo e compare os novos valores."
  },
  "ui.tutorial.modelo.magia.abrir": {
    "en": "Open the Grimoire with the spells button.",
    "pt": "Abra o Grimório no botão das magias."
  },
  "ui.tutorial.modelo.magia.lancar": {
    "en": "Cast {nome} on a training target or on yourself.",
    "pt": "Lance {nome} num alvo de treino ou em você."
  },
  "ui.tutorial.passo_ok": { "pt": "Passo concluído!", "en": "Step complete!" },
  "ui.tutorial.licao_concluida": { "pt": "Lição concluída!", "en": "Lesson complete!" },
  "ui.tutorial.recompensa": { "pt": "+{ouro} ouro · +{xp} XP", "en": "+{ouro} gold · +{xp} XP" },
  "ui.tutorial.recompensa_trilha": { "pt": "Trilha completa! Bônus incluído.", "en": "Track complete! Bonus included." }
};
Object.assign(window.LANG_STRINGS, window.LANG_TUTORIAL);
