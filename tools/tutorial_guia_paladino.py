"""Guia das lições do Paladino no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_15": [
        P("atacar", ("Ao trabalho: ataque o boneco.", "To work: attack the dummy."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]].",
                  "The [[d20]] plus your attack bonus must match or beat the [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_16": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Golpe Sagrado soma um dado a cada ataque: você é a linha entre o grupo e o chão.",
                  "Holy Strike adds a die to every attack: you are the line between the group and the floor."),
          ui="monstro:boneco_treino"),
    ],
    "treino_refem": [
        P("libertar", ("Ande até o refém na casa 35,25 e clique em Libertar prisioneiro.", "Walk to the hostage at square 35,25 and click Free prisoner."),
          porque=("Depois do resgate você poderá protegê-lo e curá-lo.", "After the rescue you can protect and heal him.")),
    ],
    "treino_protetor": [
        P("proteger", ("Ao lado do refém, use Protetor nele e encerre o turno.", "Next to the hostage, use Protector on him and end your turn."),
          porque=("O dano se divide entre vocês e a sua parte é reduzida.",
                  "The damage is split between you and your share is reduced."),
          ui="botao:encerrar_turno"),
    ],
    "treino_maos": [
        P("curar", ("Ao lado do refém ferido, use Imposição das Mãos.", "Next to the wounded hostage, use Lay on Hands."),
          porque=("A lição pede a cura desse mesmo refém.", "The lesson asks you to heal that same hostage."),
          ui="habilidade:imposicao_maos"),
    ],
    "treino_sagrado": [
        P("ativar", ("Ative Golpe Sagrado no nível disponível.", "Activate Holy Strike at the available level."),
          porque=("Há custo de ativação e de [[manutencao]] a cada rodada.",
                  "There is an activation cost and [[manutencao]] every round."),
          ui="habilidade:golpe_sagrado"),
    ],
    "treino_sagrado_golpe": [
        P("atacar", ("Ataque o boneco com Golpe Sagrado ativo.", "Attack the dummy with Holy Strike active."),
          porque=("Observe o dado sagrado somado ao dano.", "Watch the holy die added to the damage."),
          ui="monstro:boneco_treino"),
    ],
    "treino_regen": [
        P("regenerar", ("Ative Regeneração Divina e encerre a sua vez.", "Activate Divine Regeneration and end your turn."),
          porque=("A tarefa só termina quando a regeneração recuperar vida de verdade.",
                  "The task only ends when regeneration actually restores life."),
          ui="habilidade:regeneracao_divina"),
    ],
    "treino_luz": [
        P("luz", ("Ative Guerreiro da Luz e compare seus bônus.", "Activate Warrior of Light and compare your bonuses."),
          porque=("Veja visão, acerto, dano e defesa mudarem.", "See your vision, attack, damage and defense change."),
          ui="habilidade:guerreiro_luz"),
    ],
}
