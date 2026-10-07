"""Guia das lições do Guerreiro no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_5": [
        P("atacar", ("Clique no boneco de treino para atacar.", "Click the training dummy to attack."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]] do alvo.",
                  "The [[d20]] plus your attack bonus must match or beat the target's [[ca]]."),
          ui="monstro:boneco_treino",
          dica=[("Ande até ficar ao lado do boneco e clique nele.", "Walk next to the dummy and click it.")]),
    ],
    "fala_6": [
        P("matar", ("Continue atacando até derrubar o boneco.", "Keep attacking until the dummy falls."),
          porque=("Um 20 natural é [[critico]]. Você é o muro do grupo: aguenta e devolve.",
                  "A natural 20 is a [[critico]]. You are the group's wall: you take hits and give them back."),
          ui="monstro:boneco_treino"),
    ],
    "treino_mira": [
        P("mira", ("Clique em Mira Certeira e depois no boneco.", "Click Precise Aim and then the dummy."),
          porque=("Ela soma acerto ao seu [[d20]]; veja o bônus nos dados.",
                  "It adds attack bonus to your [[d20]]; watch the bonus in the dice."),
          ui="habilidade:mira_certeira",
          dica=[("O botão da habilidade fica no painel de ações, à direita.", "The ability button is in the actions panel, on the right.")]),
    ],
    "treino_golpe": [
        P("golpe", ("Clique em Golpe Devastador e depois no boneco.", "Click Devastating Strike and then the dummy."),
          porque=("Cada habilidade armada gasta sua [[acao_principal]]; observe os dados de dano.",
                  "Each armed ability spends your [[acao_principal]]; watch the damage dice."),
          ui="habilidade:golpe_devastador",
          dica=[("Se já usou sua ação, clique em Encerrar Turno antes.", "If you already used your action, click End Turn first.")]),
    ],
    "treino_furia": [
        P("furia", ("Clique em Fúria Berserker e ataque o boneco.", "Click Berserker Fury and attack the dummy."),
          porque=("A Fúria dá um ataque extra: não encerre o turno depois deste golpe.",
                  "Fury grants an extra attack: do not end your turn after this hit."),
          ui="habilidade:furia_berserker"),
    ],
    "treino_furia_extra": [
        P("extra", ("Ataque outra vez agora, antes de encerrar o turno.", "Attack again now, before ending your turn."),
          porque=("O ataque extra só vale neste turno; qualquer boneco serve de alvo.",
                  "The extra attack only works this turn; any dummy is a valid target."),
          ui="monstro:boneco_treino",
          dica=[("Se já passou a vez, arme a Fúria de novo e ataque duas vezes.", "If you already passed, arm Fury again and attack twice.")]),
    ],
    "treino_guerreiro_fim": [
        P("conferir", ("Confira a comida e a água que você gastou.", "Check the food and water you spent."),
          porque=("Habilidades cobram [[fome_sede]]; guerreiro esfomeado luta mal.",
                  "Abilities cost [[fome_sede]]; a starving warrior fights poorly.")),
        P("encerrar", ("Clique em Encerrar Turno para concluir.", "Click End Turn to finish."),
          ui="botao:encerrar_turno"),
    ],
}
