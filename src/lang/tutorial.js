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
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_TUTORIAL);
