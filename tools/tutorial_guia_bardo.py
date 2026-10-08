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
    "porta_bard": [
        P("porta", ("Abra a porta marcada e entre: é a sala exclusiva do seu herói.",
                    "Open the marked door and walk in: it is your hero's exclusive room."),
          porque=("Só a sua classe entra ali; lá você treina cada habilidade do seu herói.",
                  "Only your class can enter; there you practice each of your hero's abilities."),
          ui="porta:[15,23]",
          dica=[("Clique na porta para abri-la e depois ande até ela.",
                 "Click the door to open it, then walk onto it.")]),
    ],
    "volta_bard": [
        P("sair", ("Saia da sala pela porta marcada e volte ao corredor.",
                   "Leave the room through the marked door and return to the corridor."),
          porque=("O treino da sua classe acabou; as outras lições continuam nas salas seguintes.",
                  "Your class training is over; the other lessons continue in the next rooms."),
          ui="porta:[15, 23]".replace(" ", ""),
          conclui={"tipo": "mover_ate", "alvo": [15, 23]}),
        P("seguir", ("Siga para a próxima sala e ande até a casa marcada.",
                     "Head to the next room and walk to the marked square."),
          porque=("Lá o Mestre de Armas ensina comida, água, itens e o resto do arsenal.",
                  "There the Weapon Master teaches food, water, items and the rest of the arsenal."),
          ui="casa:[28,15]",
          dica=[("Abrir porta é grátis: clique nela e siga em frente.",
                 "Opening a door is free: click it and keep going.")]),
    ],
}
