"""Guia das lições do Paladino no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_15": [
        P("atacar", ("Ataque o boneco de treino.", "Attack the training dummy."),
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
        P("proteger", ("Fique ao lado do refém, use Protetor nele e encerre o turno.", "Stand next to the hostage, use Protector on him and end your turn."),
          porque=("O dano se divide entre vocês e a sua parte é reduzida.",
                  "The damage is split between you and your share is reduced."),
          ui="botao:encerrar_turno"),
    ],
    "treino_maos": [
        P("curar", ("Fique ao lado do refém ferido e use Imposição das Mãos.", "Stand next to the wounded hostage and use Lay on Hands."),
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
    "porta_paladin": [
        P("porta", ("Abra a porta marcada e entre: é a sala exclusiva do seu herói.",
                    "Open the marked door and walk in: it is your hero's exclusive room."),
          porque=("Só a sua classe entra ali; lá você treina cada habilidade do seu herói.",
                  "Only your class can enter; there you practice each of your hero's abilities."),
          ui="porta:[31,25]",
          dica=[("Clique na porta para abri-la e depois ande até ela.",
                 "Click the door to open it, then walk onto it.")]),
    ],
    "volta_paladin": [
        P("sair", ("Saia da sala pela porta marcada e volte ao corredor.",
                   "Leave the room through the marked door and return to the corridor."),
          porque=("O treino da sua classe acabou; as outras lições continuam nas salas seguintes.",
                  "Your class training is over; the other lessons continue in the next rooms."),
          ui="porta:[31, 25]".replace(" ", ""),
          conclui={"tipo": "mover_ate", "alvo": [31, 25]}),
        P("seguir", ("Siga para a próxima sala e ande até a casa marcada.",
                     "Head to the next room and walk to the marked square."),
          porque=("Lá o Mestre de Armas ensina comida, água, itens e o resto do arsenal.",
                  "There the Weapon Master teaches food, water, items and the rest of the arsenal."),
          ui="casa:[28,15]",
          dica=[("Abrir porta é grátis: clique nela e siga em frente.",
                 "Opening a door is free: click it and keep going.")]),
    ],
}
