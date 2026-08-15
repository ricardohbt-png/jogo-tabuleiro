// INTERFACE do cliente (etapa 5) — rótulos, tooltips e mensagens de tela.
//
// Separado do strings.js porque este cresce muito (a etapa 5 traz ~636 chaves) e
// misturá-lo com as chaves de motor e das telas de conexão tornaria os dois
// difíceis de revisar. Mantido À MÃO, como o erros.js e o narracao.js.
//
// REGRAS DO ARQUIVO (as mesmas do strings.js):
//   • É JSON estrito dentro das chaves: aspas duplas, sem vírgula sobrando,
//     SEM COMENTÁRIO dentro do objeto. Fora dele, comentários são livres — o
//     servidor ancora o recorte na LINHA "window.LANG_INTERFACE =".
//   • Falta a chave "en"? Cai no "pt". É isso que permite traduzir em lotes.
//
// CONVENÇÃO: ui.<área>.<slug>, onde <área> é a TELA em que o texto aparece.
// A `ui.` tem PRIORIDADE sobre a `cat.` do servidor quando as duas existem —
// os catálogos do cliente guardam descrição mais rica (card HTML com alcance e
// efeito por rodada) que a frase curta do servidor. Ver aplicarCatalogo.
window.LANG_INTERFACE = {
  "ui.elemental.desc.eletrico": {
    "en": "Its attack hits everyone in a straight 3-square line.",
    "pt": "Seu ataque atinge todos numa linha reta de 3 quadrados."
  },
  "ui.elemental.desc.fogo": {
    "en": "On detonating, deals 6d6 fire damage in an area (hits allies too).",
    "pt": "Ao detonar, causa 6d6 de fogo em área (atinge aliados também)."
  },
  "ui.elemental.desc.gelo": {
    "en": "Takes -2 physical damage, but +2 fire damage.",
    "pt": "Recebe -2 de dano físico, porém +2 de dano de fogo."
  },
  "ui.elemental.desc.pedra": {
    "en": "Halves all physical damage it takes.",
    "pt": "Reduz à metade todo o dano físico que recebe."
  },
  "ui.elemental.label.eletrico": {
    "en": "Line Discharge",
    "pt": "Descarga em Linha"
  },
  "ui.elemental.label.fogo": {
    "en": "Fiery Blast",
    "pt": "Explosão Ígnea"
  },
  "ui.elemental.label.gelo": {
    "en": "Glacial Body",
    "pt": "Corpo Glacial"
  },
  "ui.elemental.label.padrao": {
    "en": "Elemental",
    "pt": "Elemental"
  },
  "ui.elemental.label.pedra": {
    "en": "Stone Skin",
    "pt": "Pele de Pedra"
  },
  "ui.heroi.classe.henrique": {
    "en": "BARD",
    "pt": "BARDO"
  },
  "ui.heroi.classe.lewis": {
    "en": "CLERIC",
    "pt": "CLÉRIGO"
  },
  "ui.heroi.classe.luccas": {
    "en": "THIEF",
    "pt": "LADRÃO"
  },
  "ui.heroi.classe.pedro": {
    "en": "BLACK MAGE",
    "pt": "MAGO NEGRO"
  },
  "ui.heroi.classe.richardCavaleiro": {
    "en": "PALADIN",
    "pt": "PALADINO"
  },
  "ui.heroi.classe.victorCoiceBravo": {
    "en": "DWARF WARRIOR",
    "pt": "GUERREIRO ANÃO"
  },
  "ui.item.tipo.arma": {
    "en": "⚔ Weapon",
    "pt": "⚔ Arma"
  },
  "ui.item.tipo.armaDistancia": {
    "en": "🏹 Ranged",
    "pt": "🏹 Distância"
  },
  "ui.item.tipo.armadura": {
    "en": "🛡 Armor",
    "pt": "🛡 Armadura"
  },
  "ui.item.tipo.consumivel": {
    "en": "🍖 Consumable",
    "pt": "🍖 Consumível"
  },
  "ui.item.tipo.escudo": {
    "en": "🛡 Shield",
    "pt": "🛡 Escudo"
  },
  "ui.item.tipo.itemMagico": {
    "en": "🎒 Magic Item",
    "pt": "🎒 Item Mágico"
  },
  "ui.item.tipo.municao": {
    "en": "🎯 Ammunition",
    "pt": "🎯 Munição"
  },
  "ui.item.tipo.secundario": {
    "en": "🔦 Accessory",
    "pt": "🔦 Acessório"
  },
  "ui.item.tipo.varinha": {
    "en": "✨ Wand",
    "pt": "✨ Varinha"
  },
  "ui.mestre.custo.bonus": {
    "en": "BONUS",
    "pt": "BÔNUS"
  },
  "ui.mestre.custo.livre": {
    "en": "FREE",
    "pt": "LIVRE"
  },
  "ui.mestre.custo.principal": {
    "en": "ACTION",
    "pt": "AÇÃO"
  },
  "ui.objetivo.all_heroes_at_exit": {
    "en": "All heroes at the exit",
    "pt": "Todos os heróis na saída"
  },
  "ui.objetivo.kill_all": {
    "en": "Defeat every monster",
    "pt": "Eliminar todos os monstros"
  },
  "ui.objetivo.kill_target": {
    "en": "Defeat the target",
    "pt": "Derrotar o alvo"
  },
  "ui.objetivo.open_key_chest": {
    "en": "Open the key chest",
    "pt": "Abrir o baú-chave"
  },
  "ui.objetivo.reach_exit": {
    "en": "Reach the exit",
    "pt": "Chegar à saída"
  },
  "ui.objetivo.rescue_prisoner": {
    "en": "Rescue the prisoner",
    "pt": "Resgatar o prisioneiro"
  },
  "ui.objetivo.salas_obrigatorias": {
    "en": "Required rooms",
    "pt": "Salas obrigatórias"
  },
  "ui.selecao.classe.bard": {
    "en": "HENRIQUE THE BARD",
    "pt": "HENRIQUE, O BARDO"
  },
  "ui.selecao.classe.cleric": {
    "en": "FRIAR LEWIS",
    "pt": "FRADE LEWIS"
  },
  "ui.selecao.classe.cls.bard": {
    "en": "HENRIQUE",
    "pt": "HENRIQUE"
  },
  "ui.selecao.classe.cls.cleric": {
    "en": "FRIAR LEWIS",
    "pt": "FRADE LEWIS"
  },
  "ui.selecao.classe.cls.mage": {
    "en": "PEDRO",
    "pt": "PEDRO"
  },
  "ui.selecao.classe.cls.paladin": {
    "en": "RICHARD",
    "pt": "RICHARD"
  },
  "ui.selecao.classe.cls.rogue": {
    "en": "LUCCAS",
    "pt": "LUCCAS"
  },
  "ui.selecao.classe.cls.warrior": {
    "en": "VICTOR",
    "pt": "VICTOR"
  },
  "ui.selecao.classe.desc.bard": {
    "en": "Soul of the tavern, terror of the dungeon. Inspires allies with songs and taunts enemies. Uses no mana — his abilities cost hunger/thirst.",
    "pt": "Alma da taverna, terror do calabouço. Inspira aliados com canções e provoca inimigos. Não usa mana — suas habilidades custam fome/sede."
  },
  "ui.selecao.classe.desc.cleric": {
    "en": "A friar who channels miracles. Heals, purifies and resurrects allies. Uses no mana — his miracles cost hunger/thirst.",
    "pt": "Frade que canaliza milagres. Cura, purifica e ressuscita aliados. Não usa mana — seus milagres custam fome/sede."
  },
  "ui.selecao.classe.desc.mage": {
    "en": "Master of forbidden arcana. Devastates packs of enemies with lethal area magic.",
    "pt": "Domina os arcanos proibidos. Devasta grupos de inimigos com magia de área letal."
  },
  "ui.selecao.classe.desc.paladin": {
    "en": "Steel and honour forged on the same anvil. Richard knows no retreat — only the weight of the shield and the clarity of duty. Uses no mana — his abilities cost hunger/thirst.",
    "pt": "Aço e honra forjados na mesma bigorna. Richard não conhece recuo — apenas o peso do escudo e a clareza do dever. Não usa mana — suas habilidades custam fome/sede."
  },
  "ui.selecao.classe.desc.rogue": {
    "en": "Silent death from the shadows. Devastating critical damage and unmatched mobility.",
    "pt": "Morte silenciosa nas sombras. Dano crítico devastador e mobilidade inigualável."
  },
  "ui.selecao.classe.desc.warrior": {
    "en": "A tank of steel and blood. Soaks up devastating blows, shoves enemies back and never retreats from danger.",
    "pt": "Tanque de aço e sangue. Absorve golpes devastadores, afasta inimigos e nunca recua diante do perigo."
  },
  "ui.selecao.classe.mage": {
    "en": "PEDRO THE TIMID",
    "pt": "PEDRO, O TÍMIDO"
  },
  "ui.selecao.classe.paladin": {
    "en": "RICHARD THE KNIGHT",
    "pt": "RICHARD, O CAVALEIRO"
  },
  "ui.selecao.classe.rogue": {
    "en": "LUCCAS THE CUNNING",
    "pt": "LUCCAS, O ASTUTO"
  },
  "ui.selecao.classe.warrior": {
    "en": "VICTOR THE FIERCE KICK",
    "pt": "VICTOR COICE BRAVO"
  },
  "ui.selecao.skill.animar_mortos": {
    "en": "Animate Dead",
    "pt": "Animar Mortos"
  },
  "ui.selecao.skill.aprimorar_magia": {
    "en": "Heighten Spell",
    "pt": "Aprimorar Magia"
  },
  "ui.selecao.skill.ataque_furtivo": {
    "en": "Sneak Attack",
    "pt": "Ataque Furtivo"
  },
  "ui.selecao.skill.cancao_heroica": {
    "en": "Heroic Song",
    "pt": "Canção Heroica"
  },
  "ui.selecao.skill.conhecimento_lendas": {
    "en": "Lore of Legends",
    "pt": "Conhecimento das Lendas"
  },
  "ui.selecao.skill.criar_armadilha": {
    "en": "Set Trap",
    "pt": "Criar Armadilha"
  },
  "ui.selecao.skill.cura": {
    "en": "Heal",
    "pt": "Cura"
  },
  "ui.selecao.skill.cura_area": {
    "en": "Mass Heal",
    "pt": "Cura em Área"
  },
  "ui.selecao.skill.desc.animar_mortos": {
    "en": "Class ability — animates corpses as eternal servants.",
    "pt": "Habilidade de classe — anima cadáveres como servos eternos."
  },
  "ui.selecao.skill.desc.aprimorar_magia": {
    "en": "Free action. Increases the next spell's saving throw DC by +1.",
    "pt": "Ação livre. Aumenta em +1 a CD do teste de resistência da próxima magia."
  },
  "ui.selecao.skill.desc.ataque_furtivo": {
    "en": "Passive. +2d4 extra damage when an ally is adjacent to the target (or while invisible). +1d4 per level tier.",
    "pt": "Passiva. +2d4 de dano extra quando há aliado adjacente ao alvo (ou se estiver invisível). +1d4 por faixa de nível."
  },
  "ui.selecao.skill.desc.cancao_heroica": {
    "en": "Main action. +1 to the chosen attributes for allies within a radius of 5 squares. Variable cost per turn.",
    "pt": "Ação principal. +1 nos atributos escolhidos para aliados no raio de 5 quadrados. Custo variável por turno."
  },
  "ui.selecao.skill.desc.conhecimento_lendas": {
    "en": "Passive — always on. Reveals AC, exact HP, damage, level and treasure of any enemy on hover.",
    "pt": "Passiva — sempre ativa. Revela CA, HP exato, dano, nível e tesouro de qualquer inimigo ao passar o mouse."
  },
  "ui.selecao.skill.desc.criar_armadilha": {
    "en": "Main action. 8 trap types on your square or an adjacent one. 🍖-2 💧-1 + gold cost.",
    "pt": "Ação principal. 8 tipos de armadilha na casa/adjacente. 🍖-2 💧-1 + custo em ouro."
  },
  "ui.selecao.skill.desc.cura": {
    "en": "Main action. 1d8 to 3d8 + INT on one ally. Range extendable with hunger.",
    "pt": "Ação principal. 1d8 a 3d8 + INT em um aliado. Alcance estendível com fome."
  },
  "ui.selecao.skill.desc.cura_area": {
    "en": "Main action. 1d8 to 3d8 + INT on every ally within radius 5.",
    "pt": "Ação principal. 1d8 a 3d8 + INT em todos os aliados no raio 5."
  },
  "ui.selecao.skill.desc.detectar_armadilhas": {
    "en": "Bonus action (toggle). Reveals nearby traps and does not set off dungeon ones. Upkeep 💧-1/turn.",
    "pt": "Ação bônus (alternável). Revela armadilhas próximas e não dispara as da masmorra. Manutenção 💧-1/turno."
  },
  "ui.selecao.skill.desc.esconder_sombras": {
    "en": "Bonus action. d20+DEX vs the monsters' perception. Invisible (not targetable) until you attack — moving does NOT reveal you. Upkeep 🍖-1 💧-1/turn.",
    "pt": "Ação bônus. d20+DES vs percepção dos monstros. Invisível (não é alvo) até atacar — mover-se NÃO revela. Manutenção 🍖-1 💧-1/turno."
  },
  "ui.selecao.skill.desc.estender_magia": {
    "en": "Free action. Increases a spell's duration by 1 turn.",
    "pt": "Ação livre. Aumenta em 1 turno a duração de uma magia."
  },
  "ui.selecao.skill.desc.fortalecer_magia": {
    "en": "Free action. Multiplies the next spell's damage by 1.5.",
    "pt": "Ação livre. Multiplica por 1,5 o dano da próxima magia."
  },
  "ui.selecao.skill.desc.furia_berserker": {
    "en": "Grants one extra attack (2nd manual attack) this turn.",
    "pt": "Concede um ataque extra (2º ataque manual) neste turno."
  },
  "ui.selecao.skill.desc.golpe_devastador": {
    "en": "Doubles every damage die this turn. The Strength bonus is not doubled.",
    "pt": "Dobra cada dado de dano neste turno. O bônus de Força não é dobrado."
  },
  "ui.selecao.skill.desc.golpe_sagrado": {
    "en": "Bonus action. +1d8 holy damage per attack. Doubled against undead and demons. 🍖-3 💧-3.",
    "pt": "Ação Bônus. +1d8 dano sagrado por ataque. Dobrado contra mortos-vivos e demônios. 🍖-3 💧-3."
  },
  "ui.selecao.skill.desc.guerreiro_luz": {
    "en": "Free action. +1 or +2 to Vision, Attack, Damage and AC. Fixed bonuses until switched off. Variable cost per turn.",
    "pt": "Ação Livre. +1 ou +2 em Visão, Ataque, Dano e CA. Bônus fixos até desativar. Custo variável por turno."
  },
  "ui.selecao.skill.desc.imposicao_maos": {
    "en": "Main action. Heals 1d6 + Strength bonus on an adjacent ally. Does not work on himself. 🍖-3 💧-2.",
    "pt": "Ação Principal. Cura 1d6 + bônus de Força em aliado adjacente. Não funciona em si mesmo. 🍖-3 💧-2."
  },
  "ui.selecao.skill.desc.mira_certeira": {
    "en": "Grants +2 to hit this turn. Can be combined with other abilities in the same turn.",
    "pt": "Ativa +2 no acerto neste turno. Pode combinar com outras habilidades no mesmo turno."
  },
  "ui.selecao.skill.desc.protetor": {
    "en": "Bonus action. The chosen ally (radius 4) takes half the damage; the other half goes to Richard. 🍖-2 💧-2.",
    "pt": "Ação Bônus. Aliado escolhido (raio 4) recebe metade do dano; a outra metade vai para Richard. 🍖-2 💧-2."
  },
  "ui.selecao.skill.desc.provocacao": {
    "en": "Bonus action. Imposes disadvantage on the enemy and forces it to attack Henrique for 3 turns.",
    "pt": "Ação bônus. Impõe desvantagem ao inimigo e o força a atacar Henrique por 3 turnos."
  },
  "ui.selecao.skill.desc.purificacao": {
    "en": "Main action. Removes poison, disease, curse or petrification from an adjacent ally.",
    "pt": "Ação principal. Remove veneno, doença, maldição ou petrificação de um aliado adjacente."
  },
  "ui.selecao.skill.desc.regeneracao_divina": {
    "en": "Free action. Recovers 1 HP per turn. Switches off at full HP. Activate 🍖-2 💧-1; upkeep 🍖-1 💧-1.",
    "pt": "Ação Livre. Recupera 1 HP por turno. Desativa ao atingir HP máximo. Ativar 🍖-2 💧-1; manutenção 🍖-1 💧-1."
  },
  "ui.selecao.skill.desc.ressurreicao": {
    "en": "Main action. Brings an adjacent dead ally back with 1 HP.",
    "pt": "Ação principal. Traz um aliado morto adjacente de volta com 1 HP."
  },
  "ui.selecao.skill.desc.veneno_rapido": {
    "en": "Free action. Coats a poison from the bag onto the weapon — the next hits poison the target.",
    "pt": "Ação livre. Unta um veneno da bolsa na arma — os próximos golpes certeiros envenenam."
  },
  "ui.selecao.skill.detectar_armadilhas": {
    "en": "Detect Traps",
    "pt": "Detectar Armadilhas"
  },
  "ui.selecao.skill.esconder_sombras": {
    "en": "Hide in Shadows",
    "pt": "Esconder nas Sombras"
  },
  "ui.selecao.skill.estender_magia": {
    "en": "Extend Spell",
    "pt": "Estender Magia"
  },
  "ui.selecao.skill.fortalecer_magia": {
    "en": "Empower Spell",
    "pt": "Fortalecer Magia"
  },
  "ui.selecao.skill.furia_berserker": {
    "en": "Berserker Fury",
    "pt": "Fúria Berserker"
  },
  "ui.selecao.skill.golpe_devastador": {
    "en": "Devastating Blow",
    "pt": "Golpe Devastador"
  },
  "ui.selecao.skill.golpe_sagrado": {
    "en": "Holy Strike",
    "pt": "Golpe Sagrado"
  },
  "ui.selecao.skill.guerreiro_luz": {
    "en": "Warrior of Light",
    "pt": "Guerreiro da Luz"
  },
  "ui.selecao.skill.imposicao_maos": {
    "en": "Lay on Hands",
    "pt": "Imposição das Mãos"
  },
  "ui.selecao.skill.mira_certeira": {
    "en": "Sure Aim",
    "pt": "Mira Certeira"
  },
  "ui.selecao.skill.protetor": {
    "en": "Protector",
    "pt": "Protetor"
  },
  "ui.selecao.skill.provocacao": {
    "en": "Taunt",
    "pt": "Provocação"
  },
  "ui.selecao.skill.purificacao": {
    "en": "Purification",
    "pt": "Purificação"
  },
  "ui.selecao.skill.regeneracao_divina": {
    "en": "Divine Regeneration",
    "pt": "Regeneração Divina"
  },
  "ui.selecao.skill.ressurreicao": {
    "en": "Resurrection",
    "pt": "Ressurreição"
  },
  "ui.selecao.skill.veneno_rapido": {
    "en": "Quick Poison",
    "pt": "Veneno Rápido"
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_INTERFACE);
