"""Guia das lições do Ladino no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_9": [
        P("atacar", ("Ataque o boneco de frente.", "Attack the dummy head-on."),
          porque=("Esse é o seu pior golpe: veja o dano cru contra a [[ca]].",
                  "This is your weakest strike: see the raw damage against [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_10": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("O seu ofício é o [[furtivo]]: escondido, o mesmo golpe dói muito mais.",
                  "Your trade is the [[furtivo]]: hidden, the same strike hurts far more."),
          ui="monstro:boneco_treino"),
    ],
    "treino_detectar": [
        P("detectar", ("Arme Detectar Armadilhas e chegue perto da casa 10,8.", "Arm Detect Traps and get close to square 10,8."),
          porque=("Ela revela os mecanismos próximos e cobra água de [[manutencao]].",
                  "It reveals nearby mechanisms and costs water as [[manutencao]]."),
          ui="habilidade:detectar_armadilhas"),
    ],
    "treino_desarmar": [
        P("desarmar", ("Fique ao lado da armadilha revelada e use Desarmar Armadilha.", "Stand next to the revealed trap and use Disarm Trap."),
          porque=("Se o teste falhar, tente de novo: a sala restaura o mecanismo.",
                  "If the test fails, try again: the room restores the mechanism.")),
    ],
    "treino_esconder": [
        P("esconder", ("Fique perto do boneco e use Esconder nas Sombras.", "Stay near the dummy and use Hide in the Shadows."),
          porque=("É ação bônus: dá para atacar na mesma rodada depois de se esconder.",
                  "It is a bonus action: you can attack in the same round after hiding."),
          ui="habilidade:esconder_sombras"),
    ],
    "treino_furtivo": [
        P("furtivo", ("Ataque o boneco enquanto estiver escondido.", "Attack the dummy while hidden."),
          porque=("O [[furtivo]] é passivo: o dano extra aparece quando as condições valem.",
                  "The [[furtivo]] is passive: the extra damage shows up when conditions hold."),
          ui="monstro:boneco_treino",
          dica=[("Se errar, esconda-se de novo e tente outra vez.", "If you miss, hide again and retry.")]),
    ],
    "treino_veneno": [
        P("veneno", ("Use Veneno Rápido e escolha o veneno de treino na bolsa.", "Use Quick Poison and pick the training poison in the bag."),
          porque=("É ação livre; confira quantas cargas ficaram na arma.",
                  "It is a free action; check how many charges the weapon holds."),
          ui="habilidade:veneno_rapido"),
    ],
    "treino_veneno_golpe": [
        P("golpe", ("Ataque o boneco com a arma untada.", "Attack the dummy with the coated weapon."),
          porque=("Observe a carga gasta e o [[teste_resistencia]] do alvo contra o veneno.",
                  "Watch the charge being spent and the target's [[teste_resistencia]] against the poison."),
          ui="monstro:boneco_treino"),
    ],
    "treino_criar": [
        P("criar", ("Use Criar Armadilha numa casa vazia da sala.", "Use Create Trap on an empty square in the room."),
          porque=("Buraco já está liberado; as outras fórmulas vêm da Guilda.",
                  "Pit is already unlocked; the other formulas come from the Guild."),
          ui="habilidade:criar_armadilha"),
    ],
    "porta_rogue": [
        P("porta", ("Abra a porta marcada e entre: é a sala exclusiva do seu herói.",
                    "Open the marked door and walk in: it is your hero's exclusive room."),
          porque=("Só a sua classe entra ali; lá você treina cada habilidade do seu herói.",
                  "Only your class can enter; there you practice each of your hero's abilities."),
          ui="porta:[14,7]",
          dica=[("Clique na porta para abri-la e depois ande até ela.",
                 "Click the door to open it, then walk onto it.")]),
    ],
}
