"""Guia das lições do Clérigo no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_11": [
        P("atacar", ("Ataque o boneco com a sua maça.", "Attack the dummy with your mace."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]].",
                  "The [[d20]] plus your attack bonus must match or beat the [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_12": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Seu peso é outro: cada ponto devolvido vale mais que o dano. Cada dado de cura gasta água.",
                  "Your weight is elsewhere: every point healed beats damage dealt. Each healing die costs water."),
          ui="monstro:boneco_treino"),
    ],
    "treino_cura": [
        P("aproximar", ("Fique ao lado do Aprendiz 1, que está ferido.", "Stand next to Apprentice 1, who is wounded.")),
        P("curar", ("Clique em Cura e use um dado no Aprendiz 1.", "Click Heal and use one die on Apprentice 1."),
          porque=("Confira a vida recuperada e o custo de água.", "Check the life recovered and the water cost."),
          ui="habilidade:cura"),
    ],
    "treino_cura_area": [
        P("curar", ("Fique perto dos dois aprendizes e use Cura em Área.", "Stay near both apprentices and use Area Heal."),
          porque=("No nível inicial o raio é de 2 casas: confira a área antes de confirmar.",
                  "At the starting level the radius is 2 squares: check the area before confirming."),
          ui="habilidade:cura_area"),
    ],
    "treino_purificar": [
        P("purificar", ("Fique ao lado do Aprendiz 1, use Purificação e escolha Veneno.", "Stand next to Apprentice 1, use Purify and choose Poison."),
          porque=("Ele está cego por um veneno simulado; o efeito desaparece.",
                  "He is blinded by a simulated poison; the effect disappears."),
          ui="habilidade:purificacao"),
    ],
    "treino_ressuscitar": [
        P("ressuscitar", ("Fique ao lado do Aprendiz 1 e use Ressurreição.", "Stand next to Apprentice 1 and use Resurrection."),
          porque=("Ele simula um aliado caído e volta com a vida que sua habilidade permite.",
                  "He simulates a fallen ally and returns with the life your ability allows."),
          ui="habilidade:ressurreicao"),
    ],
    "porta_cleric": [
        P("porta", ("Abra a porta marcada e entre: é a sala exclusiva do seu herói.",
                    "Open the marked door and walk in: it is your hero's exclusive room."),
          porque=("Só a sua classe entra ali; lá você treina cada habilidade do seu herói.",
                  "Only your class can enter; there you practice each of your hero's abilities."),
          ui="porta:[30,6]",
          dica=[("Clique na porta para abri-la e depois ande até ela.",
                 "Click the door to open it, then walk onto it.")]),
    ],
    "volta_cleric": [
        P("sair", ("Saia da sala pela porta marcada e volte ao corredor.",
                   "Leave the room through the marked door and return to the corridor."),
          porque=("O treino da sua classe acabou; as outras lições continuam nas salas seguintes.",
                  "Your class training is over; the other lessons continue in the next rooms."),
          ui="porta:[30, 6]".replace(" ", ""),
          conclui={"tipo": "mover_ate", "alvo": [30, 6]}),
        P("seguir", ("Siga para a próxima sala e ande até a casa marcada.",
                     "Head to the next room and walk to the marked square."),
          porque=("Lá o Mestre de Armas ensina comida, água, itens e o resto do arsenal.",
                  "There the Weapon Master teaches food, water, items and the rest of the arsenal."),
          ui="casa:[28,15]",
          dica=[("Abrir porta é grátis: clique nela e siga em frente.",
                 "Opening a door is free: click it and keep going.")]),
    ],
}
