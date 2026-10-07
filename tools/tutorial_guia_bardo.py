"""Guia das lições do Bardo no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_13": [
        P("atacar", ("Acerte o boneco: é o primeiro compasso da balada.", "Hit the dummy: the first beat of the ballad."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]].",
                  "The [[d20]] plus your attack bonus must match or beat the [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_14": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Sua arma é a Canção Heroica: aliados num raio de cinco casas lutam melhor, e ela cobra [[manutencao]].",
                  "Your weapon is the Heroic Song: allies within five squares fight better, and it costs [[manutencao]]."),
          ui="monstro:boneco_treino"),
    ],
    "treino_cancao": [
        P("cancao", ("Clique em Canção Heroica e escolha um benefício.", "Click Heroic Song and choose a benefit."),
          porque=("A canção beneficia você e os aliados dentro do alcance.",
                  "The song benefits you and the allies within range."),
          ui="habilidade:cancao_heroica"),
    ],
    "treino_cancao_manter": [
        P("manter", ("Clique em Encerrar Turno com a canção ativa.", "Click End Turn with the song active."),
          porque=("Ela cobra [[manutencao]] de comida e água a cada rodada.",
                  "It charges [[manutencao]] in food and water every round."),
          ui="botao:encerrar_turno"),
    ],
    "treino_cancao_parar": [
        P("parar", ("Desative a Canção Heroica.", "Turn off the Heroic Song."),
          porque=("Assim o efeito e o gasto de recursos acabam.", "That ends the effect and the resource drain.")),
    ],
    "treino_provocar": [
        P("provocar", ("Clique em Provocação e depois no boneco.", "Click Taunt and then the dummy."),
          porque=("O alvo faz um [[teste_resistencia]]; resistir não invalida o uso.",
                  "The target makes a [[teste_resistencia]]; resisting does not invalidate the use."),
          ui="habilidade:provocacao"),
    ],
    "treino_instrumento": [
        P("instrumento", ("Abra as opções do instrumento e use a habilidade num alvo.", "Open the instrument options and use its ability on a target."),
          porque=("O instrumento complementa seu repertório de bardo.", "The instrument rounds out your bard repertoire.")),
    ],
}
