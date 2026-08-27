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
    "ui.comando.controlando": {
      "en": "🗣️ You control {nome}",
      "pt": "🗣️ Você controla {nome}"
    },
    "ui.comando.como_voltar": {
      "en": "Your character sheet comes back when this creature's turn ends. Use the panel on the right to move and attack, then press <b>End monster</b>.",
      "pt": "Sua ficha volta quando a vez desta criatura terminar. Use o painel à direita para mover e atacar e depois clique em <b>Encerrar monstro</b>."
    },
    "dado.acerto": {
      "en": "To-hit",
      "pt": "Acerto"
    },
    "dado.armadura": {
      "en": "Armour",
      "pt": "Armadura"
    },
    "dado.arremesso": {
      "en": "Throw",
      "pt": "Arremesso"
    },
    "dado.ataque_das_sombras": {
      "en": "Shadow Strike",
      "pt": "Ataque das Sombras"
    },
    "dado.ataque_furtivo": {
      "en": "Sneak Attack",
      "pt": "Ataque Furtivo"
    },
    "dado.ataque_furtivo_reacao": {
      "en": "Sneak Attack (reaction)",
      "pt": "Ataque Furtivo (reação)"
    },
    "dado.ataque_mao_principal": {
      "en": "⚔️ Attack (Main Hand)",
      "pt": "⚔️ Ataque (Mão Principal)"
    },
    "dado.ataque_mao_secundaria": {
      "en": "🗡️ Attack (Off Hand)",
      "pt": "🗡️ Ataque (Mão Secundária)"
    },
    "dado.bordao_cd": {
      "en": "Staff — stun DC",
      "pt": "Bordão — CD do atordoamento"
    },
    "dado.bola_de_fogo": {
      "en": "Fireball",
      "pt": "Bola de Fogo"
    },
    "dado.carapaca_espinhosa": {
      "en": "Spiked Carapace",
      "pt": "Carapaça Espinhosa"
    },
    "dado.chuva_de_flechas": {
      "en": "Arrow Rain",
      "pt": "Chuva de Flechas"
    },
    "dado.corpo_eletrico": {
      "en": "⚡ Lightning Body",
      "pt": "⚡ Corpo Elétrico"
    },
    "dado.corpo_em_chamas": {
      "en": "🔥 Burning Body",
      "pt": "🔥 Corpo em Chamas"
    },
    "dado.corpo_energetico": {
      "en": "Energy Body",
      "pt": "Corpo Energético"
    },
    "dado.cura": {
      "en": "Heal",
      "pt": "Cura"
    },
    "dado.cura_em_area": {
      "en": "Mass Heal",
      "pt": "Cura em Área"
    },
    "dado.dano": {
      "en": "Damage",
      "pt": "Dano"
    },
    "dado.dano_retaliacao": {
      "en": "Retaliation Damage",
      "pt": "Dano de Retalia\u00e7\u00e3o"
    },
    "dado.dano_2a_mao": {
      "en": "Damage (off hand)",
      "pt": "Dano (2ª mão)"
    },
    "dado.dano_arremesso": {
      "en": "Damage (throw)",
      "pt": "Dano (arremesso)"
    },
    "dado.dano_reacao": {
      "en": "Damage (reaction)",
      "pt": "Dano (reação)"
    },
    "dado.explosao_6d6": {
      "en": "🔥 Blast 6d6",
      "pt": "🔥 Explosão 6d6"
    },
    "dado.fogueira": {
      "en": "Campfire",
      "pt": "Fogueira"
    },
    "dado.furtivo": {
      "en": "Sneak",
      "pt": "Furtivo"
    },
    "dado.golpe_divino": {
      "en": "Divine Strike",
      "pt": "Golpe Divino"
    },
    "dado.golpe_pesado": {
      "en": "Heavy Blow",
      "pt": "Golpe Pesado"
    },
    "dado.golpe_sagrado": {
      "en": "Holy Strike",
      "pt": "Golpe Sagrado"
    },
    "dado.imposicao_das_maos": {
      "en": "Lay on Hands",
      "pt": "Imposição das Mãos"
    },
    "dado.lanca_de_gelo": {
      "en": "Ice Lance",
      "pt": "Lança de Gelo"
    },
    "dado.linha": {
      "en": "⚡ Line",
      "pt": "⚡ Linha"
    },
    "dado.luz_sagrada": {
      "en": "Holy Light",
      "pt": "Luz Sagrada"
    },
    "dado.movimento": {
      "en": "Movement",
      "pt": "Movimento"
    },
    "dado.reflexos": {
      "en": "Reflex",
      "pt": "Reflexos"
    },
    "dado.reflexos_morte_explosiva": {
      "en": "Reflex — Explosive Death",
      "pt": "Reflexos — Morte Explosiva"
    },
    "dado.resistencia": {
      "en": "Save",
      "pt": "Resistência"
    },
    "dado.sagrado": {
      "en": "Holy",
      "pt": "Sagrado"
    },
    "dado.sobrecarga": {
      "en": "Overload",
      "pt": "Sobrecarga"
    },
    "dado.sorte_2_no_ataque": {
      "en": "🎲 Luck (+2 to the attack)",
      "pt": "🎲 Sorte (+2 no ataque)"
    },
    "dado.sorte_2_no_teste_de_resistencia": {
      "en": "🎲 Luck (+2 to the save)",
      "pt": "🎲 Sorte (+2 no teste de resistência)"
    },
    "dado.sorte_nova_rolagem": {
      "en": "🎲 Luck (reroll)",
      "pt": "🎲 Sorte (nova rolagem)"
    },
    "dado.tiro_duplo": {
      "en": "Double Shot",
      "pt": "Tiro Duplo"
    },
    "dado.tiro_perfurante": {
      "en": "Piercing Shot",
      "pt": "Tiro Perfurante"
    },
    "dado.veneno_do_lacralion": {
      "en": "Lacralion Venom",
      "pt": "Veneno do Lacralion"
    },
    "ui.acao.arremessar_adaga": {
      "en": "🎯 Throw Off-hand Dagger",
      "pt": "🎯 Arremessar Adaga Secundária"
    },
    "ui.acao.arremessar_adaga_desc": {
      "en": "1d4 + DEX — up to 3 squares",
      "pt": "1d4 + DES — até 3 quadrados"
    },
    "ui.acao.ataque_extra_adaga": {
      "en": "🗡️ Extra Attack — Off-hand Dagger",
      "pt": "🗡️ Ataque Extra — Adaga Secundária"
    },
    "ui.acao.ataque_extra_adaga_desc": {
      "en": "1d4 + DEX adjacent",
      "pt": "1d4 + DES adjacente"
    },
    "ui.ajuda.camera": {
      "en": "<b>3D camera:</b> drag = orbit · right button = pan · scroll = zoom · <b>R</b> or ⌂ = default view · 🎲 toggles 2D/3D.",
      "pt": "<b>Câmera 3D:</b> arrastar = orbitar · direito = pan · scroll = zoom · <b>R</b> ou ⌂ = vista padrão · 🎲 alterna 2D/3D."
    },
    "ui.ajuda.dados": {
      "en": "<b>Dice:</b> <span style=\"color:#FF5500\">■ d20</span> attack/checks · <span style=\"color:#FF1111\">■ d6</span> / <span style=\"color:#0055FF\">■ d8</span> damage · <span style=\"color:#2ecc71\">■ green</span> die kept · <span style=\"color:#e74c3c\">■ red</span> discarded.",
      "pt": "<b>Dados:</b> <span style=\"color:#FF5500\">■ d20</span> ataque/testes · <span style=\"color:#FF1111\">■ d6</span> / <span style=\"color:#0055FF\">■ d8</span> dano · <span style=\"color:#2ecc71\">■ verde</span> dado mantido · <span style=\"color:#e74c3c\">■ vermelho</span> descartado."
    },
    "ui.ajuda.fome_sede": {
      "en": "<b>Hunger 🍖 and Thirst 💧:</b> they drop over time and with abilities — at zero they cause penalties. Eat/drink in the city or with items.",
      "pt": "<b>Fome 🍖 e Sede 💧:</b> caem com o tempo e com habilidades — zeradas causam penalidades. Coma/beba na cidade ou com itens."
    },
    "ui.ajuda.objetivo": {
      "en": "<b>Goal:</b> explore the dungeon, defeat the boss 👹 and return to the stairs to the city (buy items, rest) before the next floor.",
      "pt": "<b>Objetivo:</b> explorar a masmorra, derrotar o chefe 👹 e voltar à escada para a cidade (comprar itens, descansar) antes do próximo andar."
    },
    "ui.ajuda.titulo": {
      "en": "❓ How to Play",
      "pt": "❓ Como Jogar"
    },
    "ui.ajuda.turno": {
      "en": "<b>Your turn:</b> move (click a blue square), take <b>1 action</b> (attack, spell, open a chest, item) and <b>1 bonus action</b> from your class. Finish with <b>End Turn</b>.",
      "pt": "<b>Seu turno:</b> mova (clique numa casa azul), faça <b>1 ação</b> (atacar, magia, abrir baú, item) e <b>1 ação bônus</b> da classe. Termine com <b>Encerrar Turno</b>."
    },
    "ui.animar.alcance_ataque": {
      "en": "Attack range",
      "pt": "Alcance de ataque"
    },
    "ui.animar.alcance_valor": {
      "en": "Adjacent to the corpse",
      "pt": "Adjacente ao cadáver"
    },
    "ui.animar.ataques": {
      "en": "Attacks",
      "pt": "Ataques"
    },
    "ui.animar.chance_titulo": {
      "en": "SUCCESS CHANCE",
      "pt": "CHANCE DE SUCESSO"
    },
    "ui.animar.classe_acao": {
      "en": "Class Ability • Main Action",
      "pt": "Habilidade de Classe • Ação Principal"
    },
    "ui.animar.clique_cadaver": {
      "en": "Click a highlighted corpse within range.",
      "pt": "Clique em um cadáver destacado dentro do alcance."
    },
    "ui.animar.clique_cadaver_3": {
      "en": "Click a corpse within 3 squares to create an undead servant.",
      "pt": "Clique em um cadáver a até 3 casas para criar um servo morto-vivo."
    },
    "ui.animar.clique_titulo": {
      "en": "Click to animate an adjacent corpse",
      "pt": "Clique para animar um cadáver adjacente"
    },
    "ui.animar.custo_fome": {
      "en": "Hunger Cost",
      "pt": "Custo Fome"
    },
    "ui.animar.custo_por_uso": {
      "en": "🍖 -{n} | 💧 -{n} per use",
      "pt": "🍖 -{n} | 💧 -{n} por uso"
    },
    "ui.animar.custo_sede": {
      "en": "Thirst Cost",
      "pt": "Custo Sede"
    },
    "ui.animar.do_monstro": {
      "en": "of the monster",
      "pt": "do monstro"
    },
    "ui.animar.exercito": {
      "en": "💀 ANIMATED ARMY",
      "pt": "💀 EXÉRCITO ANIMADO"
    },
    "ui.animar.falha": {
      "en": "❌ FAILURE — The corpse stays inert",
      "pt": "❌ FALHA — O cadáver permanece inerte"
    },
    "ui.animar.falha_catastrofica": {
      "en": "💀 CATASTROPHIC FAILURE — Hostile creature!",
      "pt": "💀 FALHA CATASTRÓFICA — Criatura hostil!"
    },
    "ui.animar.lore": {
      "en": "Pedro focuses dark energy upon a corpse, tearing out its vital essence and binding it into a lifeless body to serve for eternity.",
      "pt": "Pedro concentra energia sombria sobre um cadáver, arrancando sua essência vital e aprisionando-a num corpo sem vida para servir eternamente."
    },
    "ui.animar.max_pct": {
      "en": "{n}% (max)",
      "pt": "{n}% (máx)"
    },
    "ui.animar.modo_legenda": {
      "en": "💀 ANIMATE DEAD — click a green corpse within 3 squares | ESC cancels",
      "pt": "💀 ANIMAR MORTOS — clique em um cadáver verde a até 3 casas | ESC cancela"
    },
    "ui.animar.n_casas": {
      "en": "{n} squares",
      "pt": "{n} casas"
    },
    "ui.animar.nivel_abaixo": {
      "en": "{n} level below",
      "pt": "{n} nível abaixo"
    },
    "ui.animar.nivel_abaixo_mais": {
      "en": "2+ levels below",
      "pt": "2+ níveis abaixo"
    },
    "ui.animar.nivel_acima": {
      "en": "{n} levels above",
      "pt": "{n} níveis acima"
    },
    "ui.animar.nivel_igual": {
      "en": "Creature of your level",
      "pt": "Criatura do seu nível"
    },
    "ui.animar.nome": {
      "en": "💀 Animate Dead",
      "pt": "💀 Animar Mortos"
    },
    "ui.animar.nome_curto": {
      "en": "Animate Dead",
      "pt": "Animar Mortos"
    },
    "ui.animar.pct_hostil": {
      "en": "{p}% / hostile <{h}%",
      "pt": "{p}% / hostil <{h}%"
    },
    "ui.animar.por_uso": {
      "en": "-{n} per use",
      "pt": "-{n} por uso"
    },
    "ui.animar.regra.acao_bonus": {
      "en": "They act via Pedro's bonus action",
      "pt": "Agem via ação bônus de Pedro"
    },
    "ui.animar.regra.hostis": {
      "en": "Hostile ones attack the nearest — permanently",
      "pt": "Hostis atacam o mais próximo — permanente"
    },
    "ui.animar.regra.morte_pedro": {
      "en": "If Pedro dies they all turn to dust at once",
      "pt": "Se Pedro morrer todos viram pó imediatamente"
    },
    "ui.animar.regra.persistem": {
      "en": "They persist between adventures",
      "pt": "Persistem entre aventuras"
    },
    "ui.animar.regra.sem_cura": {
      "en": "They cannot be healed",
      "pt": "Não podem ser curados"
    },
    "ui.animar.regra.sem_reanimar": {
      "en": "Destroyed creatures cannot be reanimated",
      "pt": "Criaturas destruídas não podem ser reanimadas"
    },
    "ui.animar.regra.sem_recuperar": {
      "en": "They never recover hit points",
      "pt": "Nunca recuperam pontos de vida"
    },
    "ui.animar.regra.viram_po": {
      "en": "At 0 HP they turn to dust permanently",
      "pt": "A 0 de vida viram pó permanentemente"
    },
    "ui.animar.regras_titulo": {
      "en": "RULES OF THE ANIMATED",
      "pt": "REGRAS DOS ANIMADOS"
    },
    "ui.animar.sem_cadaver": {
      "en": "No corpse within 3 squares to animate.",
      "pt": "Nenhum cadáver a até 3 casas para animar."
    },
    "ui.animar.sempre_disponivel": {
      "en": "CLASS ABILITY • ALWAYS AVAILABLE",
      "pt": "HABILIDADE DE CLASSE • SEMPRE DISPONÍVEL"
    },
    "ui.animar.servo_imune": {
      "en": "⚠️ Immune to healing • Does not recover HP",
      "pt": "⚠️ Imune a curas • Não recupera vida"
    },
    "ui.animar.servo_linha": {
      "en": "UNDEAD • LEVEL {nivel} • {slots} SLOT(S)",
      "pt": "MORTO-VIVO • NÍVEL {nivel} • {slots} SLOT(S)"
    },
    "ui.animar.servo_po": {
      "en": "At 0 HP it turns to dust permanently",
      "pt": "A 0 de vida vira pó permanentemente"
    },
    "ui.animar.servo_selecionado": {
      "en": "— {nome} is selected.",
      "pt": "— {nome} está selecionado."
    },
    "ui.animar.slots_disponiveis": {
      "en": "Available Slots",
      "pt": "Slots Disponíveis"
    },
    "ui.animar.slots_nivel": {
      "en": "Slots = Level",
      "pt": "Slots = Nível"
    },
    "ui.animar.slots_x_y": {
      "en": "{usados}/{total} slots",
      "pt": "{usados}/{total} slots"
    },
    "ui.animar.tooltip_custo": {
      "en": "🍖 -20 &nbsp; 💧 -20 &nbsp; · &nbsp; Range: 3 squares",
      "pt": "🍖 -20 &nbsp; 💧 -20 &nbsp; · &nbsp; Alcance: 3 casas"
    },
    "ui.animar.tooltip_desc": {
      "en": "Animate a corpse within 3 squares to create an undead servant. The success chance rises with Pedro's level.",
      "pt": "Anime um cadáver a até 3 casas para criar um servo morto-vivo. A chance de sucesso aumenta conforme o nível do Pedro."
    },
    "ui.animar.turno_servos": {
      "en": "💀 Your servants' turn",
      "pt": "💀 Turno dos seus servos"
    },
    "ui.animar.uma_casa_4dir": {
      "en": "1 square (4 directions)",
      "pt": "1 casa (4 direções)"
    },
    "ui.armadilha.a_magia": {
      "en": "the spell",
      "pt": "a magia"
    },
    "ui.armadilha.acido_cheio": {
      "en": "❌ The acid hit you full on!",
      "pt": "❌ O ácido atingiu você em cheio!"
    },
    "ui.armadilha.acido_parcial": {
      "en": "🟡 You partly resisted the acid.",
      "pt": "🟡 Você resistiu parcialmente ao ácido."
    },
    "ui.armadilha.acido_tick": {
      "en": "🧪 The acid continues burning ({n} damage).",
      "pt": "🧪 O ácido continua corroendo ({n} de dano)."
    },
    "ui.armadilha.amaldicoado": {
      "en": "☠️ Cursed: {nome}",
      "pt": "☠️ Amaldiçoado: {nome}"
    },
    "ui.armadilha.arma_quebrada": {
      "en": "💥 {peca} broke and can no longer be used.",
      "pt": "💥 {peca} quebrou e não pode mais ser usada."
    },
    "ui.armadilha.armadilha_incendiaria.desc": {
      "en": "1d6+1d4+1 fire over 3 rounds. Vanishes once triggered.",
      "pt": "1d6+1d4+1 fogo em 3 rodadas. Some após ativar."
    },
    "ui.armadilha.armadilha_urso.desc": {
      "en": "1d4 damage + lose your movement. Vanishes once triggered.",
      "pt": "1d4 dano + perde movimento. Some após ativar."
    },
    "ui.armadilha.armadura_quebrada": {
      "en": "🛡️ {peca} broke and its defensive bonuses are lost.",
      "pt": "🛡️ {peca} quebrou e seus bônus defensivos foram perdidos."
    },
    "ui.armadilha.atingido": {
      "en": "❌ You were hit!",
      "pt": "❌ Você foi atingido!"
    },
    "ui.armadilha.atordoado": {
      "en": "💫 Stunned — duration: {n}.",
      "pt": "💫 Atordoado — duração: {n}."
    },
    "ui.armadilha.bau_engolidor.desc": {
      "en": "Can only be placed on an object. Reflex DC 20 avoids; on a failure the target is trapped until it passes Strength DC 20.",
      "pt": "Só pode ser colocado em um objeto. Reflexos CD 20 evita; na falha, fica preso até passar em Força CD 20."
    },
    "ui.armadilha.engolido.titulo": {
      "en": "Swallowed",
      "pt": "Engolido"
    },
    "ui.armadilha.engolido.status": {
      "en": "🫀 SWALLOWED",
      "pt": "🫀 ENGOLIDO"
    },
    "ui.armadilha.engolido.desc": {
      "en": "The Tyrant of the Wild swallowed you. You are inside its stomach until you escape or break a path out.",
      "pt": "O Tirano da Mata engoliu você. Você permanece dentro do estômago até escapar ou abrir caminho para fora."
    },
    "ui.armadilha.engolido.dano": {
      "en": "🧪 Suffers {dano} acid damage at the start of each turn.",
      "pt": "🧪 Sofre {dano} de dano ácido no início de cada turno."
    },
    "ui.armadilha.engolido.movimento": {
      "en": "🚫 Cannot move while swallowed.",
      "pt": "🚫 Não pode se mover enquanto estiver engolido."
    },
    "ui.armadilha.engolido.ataque": {
      "en": "⚔️ Can attack only the inside of the Tyrant.",
      "pt": "⚔️ Pode atacar somente o interior do Tirano."
    },
    "ui.armadilha.engolido.escape": {
      "en": "💪 Spend the action to attempt Strength DC {dc} and escape.",
      "pt": "💪 Gaste a ação para tentar Força CD {dc} e escapar."
    },
    "ui.armadilha.buraco.desc": {
      "en": "Reflex DC 10 or lose your movement. Permanent.",
      "pt": "Reflexos dif 10 ou perde movimento. Permanente."
    },
    "ui.armadilha.congelamento": {
      "en": "❄️ {nome} affected you.",
      "pt": "❄️ {nome} afetou você."
    },
    "ui.armadilha.congelamento_nome": {
      "en": "Freezing",
      "pt": "Congelamento"
    },
    "ui.armadilha.danificado": {
      "en": "damaged",
      "pt": "danificado"
    },
    "ui.armadilha.dano_continuo": {
      "en": "🔥 Ongoing damage: {n}",
      "pt": "🔥 Dano contínuo: {n}"
    },
    "ui.armadilha.doenca": {
      "en": "🦠 You caught a {sev} disease.",
      "pt": "🦠 Você contraiu uma doença {sev}."
    },
    "ui.armadilha.enfeiticado": {
      "en": "✨ Bewitched by {nome} — duration: {n} round(s).",
      "pt": "✨ Enfeitiçado por {nome} — duração: {n} rodada(s)."
    },
    "ui.armadilha.equip_danificado": {
      "en": "🛠️ {peca}: {estado}.",
      "pt": "🛠️ {peca}: {estado}."
    },
    "ui.armadilha.equipamento": {
      "en": "Equipment",
      "pt": "Equipamento"
    },
    "ui.armadilha.escapou": {
      "en": "✅ You escaped!",
      "pt": "✅ Você escapou!"
    },
    "ui.armadilha.estagio": {
      "en": " — stage {n}",
      "pt": " — estágio {n}"
    },
    "ui.armadilha.falha_magia": {
      "en": "💥 You failed the save against {nome} and took {dano} damage.",
      "pt": "💥 Você falhou no teste contra {nome} e sofreu {dano} de dano."
    },
    "ui.armadilha.fosso_envenenado.desc": {
      "en": "1d6 damage + the chosen poison. Becomes visible once triggered.",
      "pt": "1d6 dano + veneno escolhido. Fica visível após ativar."
    },
    "ui.armadilha.fosso_estacas.desc": {
      "en": "1d6 damage + lose your movement. Becomes visible once triggered.",
      "pt": "1d6 dano + perde movimento. Fica visível após ativar."
    },
    "ui.armadilha.guilhotina.desc": {
      "en": "Reflex DC 15 avoids. On a failure, takes 1d6, loses its movement and the next round; stays hidden and protected during that time.",
      "pt": "Reflexos CD 15 evita. Na falha, sofre 1d6, perde o movimento e a próxima rodada; fica oculto e protegido nesse período."
    },
    "ui.armadilha.jato_acido.desc": {
      "en": "Reflex DC 18 avoids. On a failure, 2d6 acid + 1 corrosion level on equipment; half the damage on the next round.",
      "pt": "Reflexos CD 18 evita. Na falha, 2d6 ácido + 1 nível de corrosão em equipamento; metade do dano na rodada seguinte."
    },
    "ui.armadilha.lamina_escondida.desc": {
      "en": "Reflex DC 15 or take 1d8. Poison optional. Vanishes once triggered.",
      "pt": "Reflexos dif 15 ou sofre 1d8. Veneno opcional. Some após ativar."
    },
    "ui.armadilha.lamina_pendulo.desc": {
      "en": "Reflex DC 14 or take 2d6. Stays active for 3 rounds.",
      "pt": "Reflexos dif 14 ou sofre 2d6. Permanece ativa por 3 rodadas."
    },
    "ui.armadilha.magia": {
      "en": "a spell",
      "pt": "magia"
    },
    "ui.armadilha.maldicao": {
      "en": "curse",
      "pt": "maldição"
    },
    "ui.armadilha.mina_terrestre.desc": {
      "en": "2d6 in an area (1 sq). A save halves it. Vanishes once triggered.",
      "pt": "2d6 em área (1 quad). Save reduz à metade. Some após ativar."
    },
    "ui.armadilha.morte": {
      "en": "💀 Your character died. Hope your companions can rescue them.",
      "pt": "💀 Seu personagem morreu. Torça para que seus companheiros possam resgatá-lo."
    },
    "ui.armadilha.nuvem_gas.desc": {
      "en": "-1d6 CON for 3 rounds in an area. Fortitude save DC 13.",
      "pt": "-1d6 CON por 3 rodadas em área. Save Fortitude dif 13."
    },
    "ui.armadilha.parcial": {
      "en": "🟡 You partly resisted!",
      "pt": "🟡 Você resistiu parcialmente!"
    },
    "ui.armadilha.petrificado": {
      "en": "🗿 Petrified — duration: {n} round(s).",
      "pt": "🗿 Petrificado — duração: {n} rodada(s)."
    },
    "ui.armadilha.rede.desc": {
      "en": "Lose the whole round. Vanishes once triggered.",
      "pt": "Perde a rodada inteira. Some após ativar."
    },
    "ui.armadilha.sono": {
      "en": "🌙 Asleep — duration: {n} round(s).",
      "pt": "🌙 Adormecido — duração: {n} rodada(s)."
    },
    "ui.armadilha.sua_arma": {
      "en": "Your weapon",
      "pt": "Sua arma"
    },
    "ui.armadilha.sua_armadura": {
      "en": "Your armour",
      "pt": "Sua armadura"
    },
    "ui.armadilha.temporaria": {
      "en": "temporary",
      "pt": "temporária"
    },
    "ui.armadilha.titulo_padrao": {
      "en": "Trap",
      "pt": "Armadilha"
    },
    "ui.armadilha.veneno": {
      "en": "☠️ Poisoned — duration: {n} round(s).",
      "pt": "☠️ Envenenado — duração: {n} rodada(s)."
    },
    "ui.arremesso.acao_bonus": {
      "en": "BONUS ACTION",
      "pt": "AÇÃO BÔNUS"
    },
    "ui.arremesso.acao_principal": {
      "en": "MAIN ACTION",
      "pt": "AÇÃO PRINCIPAL"
    },
    "ui.arremesso.agora_nao": {
      "en": "You can't throw right now.",
      "pt": "Não é possível arremessar agora."
    },
    "ui.arremesso.arremessar": {
      "en": "Throw",
      "pt": "Arremessar"
    },
    "ui.arremesso.cancele_primeiro": {
      "en": "Cancel the current throw first (ESC).",
      "pt": "Cancele o arremesso atual primeiro (ESC)."
    },
    "ui.arremesso.direcao_inimigo": {
      "en": "⚠️ Throw towards an enemy",
      "pt": "⚠️ Arremesse em direção a um inimigo"
    },
    "ui.arremesso.escolha_alvo": {
      "en": "🎯 Throw {nome} — Choose the Target (range {alcance})",
      "pt": "🎯 Arremessar {nome} — Escolha o Alvo (alcance {alcance})"
    },
    "ui.arremesso.inimigo_nao_encontrado": {
      "en": "⚠️ Enemy not found",
      "pt": "⚠️ Inimigo não encontrado"
    },
    "ui.arremesso.legenda_casa": {
      "en": "Valid square",
      "pt": "Casa válida"
    },
    "ui.arremesso.legenda_esc": {
      "en": "ESC to cancel",
      "pt": "ESC para cancelar"
    },
    "ui.arremesso.legenda_inimigo": {
      "en": "Enemy",
      "pt": "Inimigo"
    },
    "ui.arremesso.legenda_lanca": {
      "en": "🏹 SPEAR THROW {acao}",
      "pt": "🏹 ARREMESSO DE LANÇA {acao}"
    },
    "ui.arremesso.legenda_modo": {
      "en": "🎯 THROW MODE",
      "pt": "🎯 MODO ARREMESSO"
    },
    "ui.arremesso.legenda_principal": {
      "en": "🎯 THROW {acao}",
      "pt": "🎯 ARREMESSO {acao}"
    },
    "ui.arremesso.log_lanca": {
      "en": "🏹 Spear throw mode — {acao}. Click an enemy (ESC cancels).",
      "pt": "🏹 Modo arremesso de lança — {acao}. Clique num inimigo (ESC cancela)."
    },
    "ui.arremesso.log_mira_alvo": {
      "en": "Throw aim — click a highlighted enemy (ESC cancels).",
      "pt": "Mira de arremesso — clique num inimigo destacado (ESC cancela)."
    },
    "ui.arremesso.log_mira_area": {
      "en": "Throw aim — click a square (the green area follows the cursor) (ESC cancels).",
      "pt": "Mira de arremesso — clique numa casa (área verde segue o cursor) (ESC cancela)."
    },
    "ui.arremesso.log_principal": {
      "en": "🎯 Throw mode (main hand) — {acao}. Click an enemy (ESC cancels).",
      "pt": "🎯 Modo arremesso (mão principal) — {acao}. Clique num inimigo (ESC cancela)."
    },
    "ui.arremesso.mira_alvo": {
      "en": "Click an ENEMY (range {alcance})",
      "pt": "Clique num INIMIGO (alcance {alcance})"
    },
    "ui.arremesso.mira_area": {
      "en": "Click a SQUARE (radius {raio} area, range {alcance})",
      "pt": "Clique numa CASA (área raio {raio}, alcance {alcance})"
    },
    "ui.arremesso.sem_acoes": {
      "en": "No actions available to throw.",
      "pt": "Sem ações disponíveis para arremessar."
    },
    "ui.arremesso.sem_adaga": {
      "en": "No throwable dagger in the main hand.",
      "pt": "Nenhuma adaga arremessável na mão principal."
    },
    "ui.arremesso.sem_adaga_secundaria": {
      "en": "No throwable off-hand dagger equipped.",
      "pt": "Nenhuma adaga secundária arremessável equipada."
    },
    "ui.arremesso.sem_arma_na_mao": {
      "en": "No throwing weapon in that hand.",
      "pt": "Nenhuma arma de arremesso nessa mão."
    },
    "ui.arremesso.sem_inimigo_a_vista": {
      "en": "No enemy in sight within {n} squares to throw at.",
      "pt": "Nenhum inimigo à vista a até {n} quadrados para arremessar."
    },
    "ui.arremesso.sem_lanca": {
      "en": "Short spear not equipped.",
      "pt": "Lança curta não equipada."
    },
    "ui.arremesso.so_3d": {
      "en": "Aimed throwing is only available in the 3D view.",
      "pt": "Arremesso com mira disponível apenas na visão 3D."
    },
    "ui.ataque.sem_alvo_adjacente": {
      "en": "No adjacent enemy. Move next to one!",
      "pt": "Nenhum inimigo adjacente. Mova-se para ao lado de um inimigo!"
    },
    "ui.ataque.sem_alvo_distancia": {
      "en": "No enemy within {n} squares!",
      "pt": "Nenhum inimigo a até {n} quadrados!"
    },
    "ui.ataque.titulo_adjacente": {
      "en": "Attack — Choose the Adjacent Enemy",
      "pt": "Atacar — Escolha o Inimigo Adjacente"
    },
    "ui.ataque.titulo_distancia": {
      "en": "Ranged attack — Choose the Target (range {n})",
      "pt": "Atacar à distância — Escolha o Alvo (alcance {n})"
    },
    "ui.atributo.carisma": {
      "en": "Charisma",
      "pt": "Carisma"
    },
    "ui.atributo.constituicao": {
      "en": "Constitution",
      "pt": "Constituição"
    },
    "ui.atributo.destreza": {
      "en": "Dexterity",
      "pt": "Destreza"
    },
    "ui.atributo.forca": {
      "en": "Strength",
      "pt": "Força"
    },
    "ui.atributo.forcaOuDestreza": {
      "en": "Strength or Dexterity",
      "pt": "Força ou Destreza"
    },
    "ui.atributo.inteligencia": {
      "en": "Intelligence",
      "pt": "Inteligência"
    },
    "ui.atributo.sigla.con_": {
      "en": "CON",
      "pt": "CON"
    },
    "ui.atributo.sigla.dex": {
      "en": "DEX",
      "pt": "DES"
    },
    "ui.atributo.sigla.int_": {
      "en": "INT",
      "pt": "INT"
    },
    "ui.atributo.sigla.str_": {
      "en": "STR",
      "pt": "FOR"
    },
    "ui.atributo.visao": {
      "en": "Sight",
      "pt": "Visão"
    },
    "ui.bardo.provocacao_2": {
      "en": "II: the disadvantage lasts the whole taunt; Henrique gains +2 AC and attacks the target with advantage.",
      "pt": "II: a desvantagem dura toda a provocação; Henrique ganha +2 CA e ataca o alvo com vantagem."
    },
    "ui.bardo.provocacao_3": {
      "en": "II/III: disadvantage for the whole taunt, +2 AC and advantage — and every ally attacks the target with advantage for 1 round.",
      "pt": "II/III: desvantagem por toda a provocação, +2 CA e vantagem — e todos os aliados atacam o alvo com vantagem por 1 rodada."
    },
    "ui.bardo.provocacao_desc": {
      "en": "Forces the enemy to attack Henrique (radius 3).",
      "pt": "Força o inimigo a atacar Henrique (raio 3)."
    },
    "ui.bardo.provocar_custo": {
      "en": "Taunt requires 🍖3 and 💧3.",
      "pt": "Provocação requer 🍖3 e 💧3."
    },
    "ui.bardo.provocar_sem_alvo": {
      "en": "No tauntable enemy within 3 squares.",
      "pt": "Nenhum inimigo provocável a até 3 quadrados."
    },
    "ui.bardo.provocar_so_turno": {
      "en": "You can only taunt on your turn.",
      "pt": "Só é possível provocar no seu turno."
    },
    "ui.bardo.provocar_titulo": {
      "en": "😤 Taunt — Choose the target (radius 3)",
      "pt": "😤 Provocação — Escolha o alvo (raio 3)"
    },
    "ui.bau.ativar_mecanismo": {
      "en": "Activate mechanism",
      "pt": "Ativar mecanismo"
    },
    "ui.bau.inventario_cheio": {
      "en": "Inventory full!",
      "pt": "Inventário cheio!"
    },
    "ui.bau.nome": {
      "en": "Treasure Chest",
      "pt": "Baú de Tesouro"
    },
    "ui.bau.objeto": {
      "en": "📦 Object",
      "pt": "📦 Objeto"
    },
    "ui.bau.objeto_vazio": {
      "en": "The object is empty.",
      "pt": "O objeto está vazio."
    },
    "ui.bau.ouros": {
      "en": "{n} Gold",
      "pt": "{n} Ouros"
    },
    "ui.bau.pegar": {
      "en": "⬆ Take",
      "pt": "⬆ Pegar"
    },
    "ui.bau.pegar_tudo": {
      "en": "⬆ Take all",
      "pt": "⬆ Pegar tudo"
    },
    "ui.bau.pegar_tudo_desc": {
      "en": "Collects the gold and every item that fits in the inventory.",
      "pt": "Coleta o ouro e todos os itens que couberem no inventário."
    },
    "ui.bau.slot.accessory": {
      "en": "📿 Accessory",
      "pt": "📿 Acessório"
    },
    "ui.bau.slot.arma_dado": {
      "en": "⚔ Weapon ({die})",
      "pt": "⚔ Arma ({die})"
    },
    "ui.bau.slot.armor": {
      "en": "🛡 Armour",
      "pt": "🛡 Armadura"
    },
    "ui.bau.slot.bag": {
      "en": "🧪 Consumable",
      "pt": "🧪 Consumível"
    },
    "ui.bau.slot.head": {
      "en": "⛑ Head",
      "pt": "⛑ Cabeça"
    },
    "ui.bau.slot.municao_x": {
      "en": "🏹 Ammo ×{n}",
      "pt": "🏹 Munição ×{n}"
    },
    "ui.bau.slot.padrao": {
      "en": "📦 Item",
      "pt": "📦 Item"
    },
    "ui.bau.slot.ring": {
      "en": "💍 Ring",
      "pt": "💍 Anel"
    },
    "ui.bau.slot.shield": {
      "en": "🛡 Shield",
      "pt": "🛡 Escudo"
    },
    "ui.bau.slot.weapon": {
      "en": "⚔ Weapon",
      "pt": "⚔ Arma"
    },
    "ui.bau.stat_atq": {
      "en": "Atk",
      "pt": "Atq"
    },
    "ui.bau.stat_ca": {
      "en": "AC",
      "pt": "CA"
    },
    "ui.bau.stat_hp": {
      "en": "HP",
      "pt": "HP"
    },
    "ui.bau.subtitulo": {
      "en": "Get close to the chest to collect",
      "pt": "Aproxime-se do baú para coletar"
    },
    "ui.bau.titulo": {
      "en": "🎁 Treasure Chest",
      "pt": "🎁 Baú de Tesouro"
    },
    "ui.bau.vazio": {
      "en": "The chest is empty.",
      "pt": "O baú está vazio."
    },
    "ui.cancao.ativar_manutencao": {
      "en": "ACTIVATE + UPKEEP",
      "pt": "ATIVAR + MANUTENÇÃO"
    },
    "ui.cancao.atributo.acerto": {
      "en": "To-hit",
      "pt": "Acerto"
    },
    "ui.cancao.atributo.ca": {
      "en": "Armour",
      "pt": "Armadura"
    },
    "ui.cancao.atributo.dano": {
      "en": "Damage",
      "pt": "Dano"
    },
    "ui.cancao.atributo.movimento": {
      "en": "Movement",
      "pt": "Movimento"
    },
    "ui.cancao.atributo.resistencia": {
      "en": "Resistance",
      "pt": "Resistência"
    },
    "ui.cancao.cantar": {
      "en": "🎵 SING",
      "pt": "🎵 CANTAR"
    },
    "ui.cancao.por_turno": {
      "en": "/turn",
      "pt": "/turno"
    },
    "ui.cancao.se_atacar": {
      "en": "IF YOU ATTACK THIS TURN",
      "pt": "SE ATACAR NO TURNO"
    },
    "ui.cancao.selecione_atributos": {
      "en": "Select attributes",
      "pt": "Selecione atributos"
    },
    "ui.cancao.suprema": {
      "en": "(Supreme)",
      "pt": "(Suprema)"
    },
    "ui.cancao.titulo": {
      "en": "🎵 HEROIC SONG",
      "pt": "🎵 CANÇÃO HEROICA"
    },
    "ui.cena.alt_fundo": {
      "en": "Scene of the place",
      "pt": "Cena do local"
    },
    "ui.cena.ao_concluir": {
      "en": "On completion: {lista}",
      "pt": "Ao concluir: {lista}"
    },
    "ui.cena.bau_compartilhado": {
      "en": "🧰 Open the shared chest",
      "pt": "🧰 Abrir baú compartilhado"
    },
    "ui.cena.bau_compartilhado_titulo": {
      "en": "🧰 Shared chest",
      "pt": "🧰 Baú compartilhado"
    },
    "ui.cena.bau_heroi": {
      "en": "🧰 Open the hero's chest",
      "pt": "🧰 Abrir baú do herói"
    },
    "ui.cena.conversando": {
      "en": "Talking…",
      "pt": "Conversando…"
    },
    "ui.cena.conversar_com": {
      "en": "Talk to {nome}",
      "pt": "Conversar com {nome}"
    },
    "ui.cena.dica_clique": {
      "en": "Click a group of regulars to talk.",
      "pt": "Clique em um grupo de frequentadores para conversar."
    },
    "ui.cena.encerrar_com_pendencias": {
      "en": "There are {n} required event(s) not reached. End anyway?",
      "pt": "Há {n} evento(s) obrigatório(s) não alcançado(s). Encerrar mesmo assim?"
    },
    "ui.cena.entrar_quarto": {
      "en": "🛏️ Enter the hero's room",
      "pt": "🛏️ Entrar no quarto do herói"
    },
    "ui.cena.entrar_refugio": {
      "en": "🚪 Enter the Refuge",
      "pt": "🚪 Entrar no Refúgio"
    },
    "ui.cena.fechar_conversa": {
      "en": "Close conversation",
      "pt": "Fechar conversa"
    },
    "ui.cena.fim_botao": {
      "en": "Finish and return to the game",
      "pt": "Concluir e voltar ao jogo"
    },
    "ui.cena.fim_texto": {
      "en": "The scene is complete.",
      "pt": "A cena foi concluída."
    },
    "ui.cena.fim_titulo": {
      "en": "End of the scene",
      "pt": "Fim da cena"
    },
    "ui.cena.nada_novo": {
      "en": "This person has nothing new to tell for now.",
      "pt": "Esta pessoa não tem nada novo para contar por enquanto."
    },
    "ui.cena.pular_confirm": {
      "en": "Skip the scene? Mandatory effects will be kept.",
      "pt": "Pular a cena? Os efeitos obrigatórios serão mantidos."
    },
    "ui.cena.renome_grupo": {
      "en": "★ Party renown: {n}",
      "pt": "★ Renome do grupo: {n}"
    },
    "ui.cena.requer": {
      "en": "Requires: {lista}",
      "pt": "Requer: {lista}"
    },
    "ui.cena.sem_frequentadores": {
      "en": "This place has no regulars set up yet.",
      "pt": "Este local ainda não possui frequentadores configurados."
    },
    "ui.cena.teste_falha": {
      "en": "Test failed: {total} against DC {cd}.",
      "pt": "Falha no teste: {total} contra CD {cd}."
    },
    "ui.cena.teste_sucesso": {
      "en": "Test succeeded: {total} against DC {cd}.",
      "pt": "Sucesso no teste: {total} contra CD {cd}."
    },
    "ui.cena.voltar_area_comum": {
      "en": "🚪 Back to the common room",
      "pt": "🚪 Voltar à área comum"
    },
    "ui.cidade.acao.ferreiro": {
      "en": "Buy equipment",
      "pt": "Comprar equipamentos"
    },
    "ui.cidade.acao.guilda": {
      "en": "Buy specialisations and techniques",
      "pt": "Comprar especializações e técnicas"
    },
    "ui.cidade.acao.mercador": {
      "en": "Items and potions",
      "pt": "Itens e poções"
    },
    "ui.cidade.acao.taverna": {
      "en": "Eat and drink — restore hunger and thirst",
      "pt": "Comer e beber — recuperar fome e sede"
    },
    "ui.cidade.acao.templo": {
      "en": "Blessings and divine healing",
      "pt": "Bênçãos e curas divinas"
    },
    "ui.cidade.ajustar_pontos": {
      "en": "📍 Adjust points",
      "pt": "📍 Ajustar pontos"
    },
    "ui.cidade.arraste_pontos": {
      "en": "Drag the reference points to the right places and click Save points.",
      "pt": "Arraste os pontos de referência para os locais corretos e clique em Salvar pontos."
    },
    "ui.cidade.cancelar_ajuste": {
      "en": "✕ Cancel adjustment",
      "pt": "✕ Cancelar ajuste"
    },
    "ui.cidade.caravana_titulo": {
      "en": "Travelling Caravan — open the world map",
      "pt": "Caravana de Viagem — abrir mapa-múndi"
    },
    "ui.cidade.carregando": {
      "en": "⏳ Loading…",
      "pt": "⏳ Carregando…"
    },
    "ui.cidade.clique_abrir": {
      "en": "▶ CLICK TO OPEN",
      "pt": "▶ CLIQUE PARA ABRIR"
    },
    "ui.cidade.clique_entrar": {
      "en": "▶ CLICK TO ENTER",
      "pt": "▶ CLIQUE PARA ENTRAR"
    },
    "ui.cidade.dica_anfitriao": {
      "en": "You are the host — click the Gate or here to enter.",
      "pt": "Você é o anfitrião — clique no Portão ou aqui para entrar."
    },
    "ui.cidade.dica_convidado": {
      "en": "Waiting for the host to start the adventure…",
      "pt": "Aguardando o anfitrião iniciar a aventura…"
    },
    "ui.cidade.entrada_sem_destino": {
      "en": "⚠ This entrance is not linked to any destination.",
      "pt": "⚠ Esta entrada não está vinculada a nenhum destino."
    },
    "ui.cidade.entrar_masmorra": {
      "en": "⚔ Enter the Dungeon",
      "pt": "⚔ Entrar na Masmorra"
    },
    "ui.cidade.guilda_missoes_em_breve": {
      "en": "⚔ Heroes' Guild — Quests coming soon!",
      "pt": "⚔ Guilda dos Heróis — Missões em breve!"
    },
    "ui.cidade.ir_aventura": {
      "en": "Go on the adventure",
      "pt": "Ir para a aventura"
    },
    "ui.cidade.ir_aventura_btn": {
      "en": "▶ Go on the adventure",
      "pt": "▶ Ir para a aventura"
    },
    "ui.cidade.ir_aventura_fase": {
      "en": "▶ Go on the adventure — Phase {n}",
      "pt": "▶ Ir para a aventura — Fase {n}"
    },
    "ui.cidade.mapa_mundi": {
      "en": "🧭 World map",
      "pt": "🧭 Mapa-múndi"
    },
    "ui.cidade.ponto.caravana": {
      "en": "Travelling Caravan",
      "pt": "Caravana de Viagem"
    },
    "ui.cidade.ponto.cena": {
      "en": "Place",
      "pt": "Local"
    },
    "ui.cidade.ponto.dungeon": {
      "en": "Dungeon entrance",
      "pt": "Entrada da masmorra"
    },
    "ui.cidade.ponto.ferreiro": {
      "en": "Blacksmith",
      "pt": "Ferreiro"
    },
    "ui.cidade.ponto.guilda": {
      "en": "Guild",
      "pt": "Guilda"
    },
    "ui.cidade.ponto.mercador": {
      "en": "Merchant",
      "pt": "Mercador"
    },
    "ui.cidade.ponto.refugio": {
      "en": "Heroes' Refuge",
      "pt": "Refúgio dos Heróis"
    },
    "ui.cidade.ponto.taverna": {
      "en": "Tavern",
      "pt": "Taverna"
    },
    "ui.cidade.ponto.templo": {
      "en": "Temple",
      "pt": "Templo"
    },
    "ui.cidade.predio.ferreiro": {
      "en": "Smithy",
      "pt": "Ferraria"
    },
    "ui.cidade.predio.guilda": {
      "en": "Heroes' Guild",
      "pt": "Guilda dos Heróis"
    },
    "ui.cidade.predio.mercador": {
      "en": "Market",
      "pt": "Mercado"
    },
    "ui.cidade.predio.taverna": {
      "en": "Tavern",
      "pt": "Taverna"
    },
    "ui.cidade.predio.templo": {
      "en": "Temple",
      "pt": "Templo"
    },
    "ui.cidade.refugio_bloqueado": {
      "en": "🔒 The Heroes' Refuge is still locked.",
      "pt": "🔒 O Refúgio dos Heróis ainda está bloqueado."
    },
    "ui.cidade.salvar_pontos": {
      "en": "Save points",
      "pt": "Salvar pontos"
    },
    "ui.classe_curta.bard": {
      "en": "Bard",
      "pt": "Bardo"
    },
    "ui.classe_curta.cleric": {
      "en": "Cleric",
      "pt": "Clérigo"
    },
    "ui.classe_curta.mage": {
      "en": "Mage",
      "pt": "Mago"
    },
    "ui.classe_curta.paladin": {
      "en": "Paladin",
      "pt": "Paladino"
    },
    "ui.classe_curta.rogue": {
      "en": "Rogue",
      "pt": "Ladino"
    },
    "ui.classe_curta.warrior": {
      "en": "Warrior",
      "pt": "Guerreiro"
    },
    "ui.clerigo.cura_alcance": {
      "en": "RANGE — 🍖-1 per extension",
      "pt": "ALCANCE — 🍖-1 por extensão"
    },
    "ui.clerigo.cura_area_sub": {
      "en": "Radius {raio} squares | 🍖-4 💧-4 per die",
      "pt": "Raio {raio} quadrados | 🍖-4 💧-4 por dado"
    },
    "ui.clerigo.cura_area_titulo": {
      "en": "🌟 AREA HEAL",
      "pt": "🌟 CURA EM ÁREA"
    },
    "ui.clerigo.cura_dados": {
      "en": "HEALING DICE — 💧-1 per die",
      "pt": "DADOS DE CURA — 💧-1 por dado"
    },
    "ui.clerigo.cura_titulo": {
      "en": "🙌 HEAL",
      "pt": "🙌 CURA"
    },
    "ui.clerigo.cura_todos": {
      "en": "Healing for everyone",
      "pt": "Cura para todos"
    },
    "ui.clerigo.curar_area_botao": {
      "en": "🌟 HEAL AREA",
      "pt": "🌟 CURAR ÁREA"
    },
    "ui.clerigo.milagre_so_turno": {
      "en": "Miracles can only be used on your turn.",
      "pt": "Só é possível usar milagres no seu turno."
    },
    "ui.clerigo.purificar_alvo_limpo": {
      "en": "{nome} has no effects you know how to cleanse.",
      "pt": "{nome} não tem efeitos que você saiba purificar."
    },
    "ui.clerigo.purificar_sem_alvo": {
      "en": "No adjacent ally with an effect you know how to cleanse.",
      "pt": "Nenhum aliado adjacente com efeito que você saiba purificar."
    },
    "ui.clerigo.purificar_titulo": {
      "en": "✨ Cleanse — Adjacent ally",
      "pt": "✨ Purificação — Aliado adjacente"
    },
    "ui.clerigo.ressur_custo": {
      "en": "Resurrection requires 🍖{n} and 💧{n}.",
      "pt": "Ressurreição requer 🍖{n} e 💧{n}."
    },
    "ui.clerigo.ressur_efeito.1": {
      "en": "1 HP",
      "pt": "1 HP"
    },
    "ui.clerigo.ressur_efeito.2": {
      "en": "half HP",
      "pt": "metade dos PV"
    },
    "ui.clerigo.ressur_efeito.3": {
      "en": "full HP",
      "pt": "PV cheio"
    },
    "ui.clerigo.ressur_titulo": {
      "en": "💫 Resurrection ({efeito}) — Adjacent dead ally",
      "pt": "💫 Ressurreição ({efeito}) — Aliado morto adjacente"
    },
    "ui.clerigo.sem_aliado_morto": {
      "en": "No adjacent dead ally.",
      "pt": "Nenhum aliado morto adjacente."
    },
    "ui.conexao.codigo_4_letras": {
      "en": "Code must have 4 letters.",
      "pt": "Código deve ter 4 letras."
    },
    "ui.conexao.codigo_copiado": {
      "en": "Code copied!",
      "pt": "Código copiado!"
    },
    "ui.conexao.digite_nome": {
      "en": "Type a hero name.",
      "pt": "Digite um nome de herói."
    },
    "ui.conexao.encerrada": {
      "en": "Connection closed.",
      "pt": "Conexão encerrada."
    },
    "ui.conexao.encerrada_servidor": {
      "en": "Connection to the server closed.",
      "pt": "Conexão com o servidor encerrada."
    },
    "ui.conexao.falhou": {
      "en": "❌ Could not reconnect. Reload the page and use \"Reconnect to the last game\".",
      "pt": "❌ Não foi possível reconectar. Recarregue a página e use \"Reconectar à última partida\"."
    },
    "ui.conexao.fechamento_bloqueado": {
      "en": "Your browser blocked the window from closing. You already left the match and are back at the main menu.",
      "pt": "Seu navegador bloqueou o fechamento. Você já saiu da partida e voltou ao menu inicial."
    },
    "ui.conexao.reconectando": {
      "en": "🔌 Connection lost — reconnecting ({n}/{max})...",
      "pt": "🔌 Conexão perdida — reconectando ({n}/{max})..."
    },
    "ui.conexao.reconectar_sala": {
      "en": "🔌 Reconnect to room {codigo} as {nome}",
      "pt": "🔌 Reconectar à sala {codigo} como {nome}"
    },
    "ui.conexao.sem_servidor": {
      "en": "No connection to the server.",
      "pt": "Sem conexão com o servidor."
    },
    "ui.conexao.sem_servidor_reinicie": {
      "en": "❌ No connection to the server. Restart iniciar.bat.",
      "pt": "❌ Sem conexão com o servidor. Reinicie o iniciar.bat."
    },
    "ui.conexao.servidor_nao_encontrado": {
      "en": "❌ Server not found. Run iniciar.bat first!",
      "pt": "❌ Servidor não encontrado. Execute iniciar.bat primeiro!"
    },
    "ui.connect.hint_host": {
      "en": "⚙️ <b style=\"color:#6fc96f;\">How to play:</b> Double-click <code style=\"background:#1a2a1a;padding:1px 5px;border-radius:3px;color:#a0e0a0;\">iniciar.bat</code> to start the server and open the game automatically.",
      "pt": "⚙️ <b style=\"color:#6fc96f;\">Como jogar:</b> Clique duas vezes em <code style=\"background:#1a2a1a;padding:1px 5px;border-radius:3px;color:#a0e0a0;\">iniciar.bat</code> para iniciar o servidor e abrir o jogo automaticamente."
    },
    "ui.conta.criar_agora": {
      "en": "That account does not exist. Create it now with this nickname and PIN?",
      "pt": "Conta não existe. Criar agora com esse apelido e PIN?"
    },
    "ui.conta.pin_4_digitos": {
      "en": "The PIN must have 4 digits.",
      "pt": "O PIN deve ter 4 dígitos."
    },
    "ui.dano_tipo.fogo": {
      "en": "fire",
      "pt": "fogo"
    },
    "ui.diag.arquivo_nao_carregou": {
      "en": "file did not load (404 or network)",
      "pt": "arquivo não carregou (404 ou rede)"
    },
    "ui.diag.cliente_antigo": {
      "en": "OLD client cached — reload with Ctrl+Shift+R.",
      "pt": "Cliente ANTIGO em cache — recarregue com Ctrl+Shift+R."
    },
    "ui.diag.conexao_falhou": {
      "en": "connection failed (is the server up?)",
      "pt": "conexão falhou (o servidor está no ar?)"
    },
    "ui.diag.copiar": {
      "en": "Copy report",
      "pt": "Copiar relatório"
    },
    "ui.diag.painel_titulo": {
      "en": "🔎 3D art diagnostics",
      "pt": "🔎 Diagnóstico de arte 3D"
    },
    "ui.diag.relatorio_copiado": {
      "en": "Report copied.",
      "pt": "Relatório copiado."
    },
    "ui.diag.titulo": {
      "en": "3D ART DIAGNOSTICS — {data}",
      "pt": "DIAGNÓSTICO DE ARTE 3D — {data}"
    },
    "ui.dificuldade.dificil": {
      "en": "Hard",
      "pt": "Difícil"
    },
    "ui.dificuldade.equilibrada": {
      "en": "Balanced",
      "pt": "Equilibrada"
    },
    "ui.dificuldade.facil": {
      "en": "Easy",
      "pt": "Fácil"
    },
    "ui.dificuldade.mortal": {
      "en": "Deadly",
      "pt": "Mortal"
    },
    "ui.elemental.agem_apos": {
      "en": "They act after Lewis — end the turn to open the control window and move/attack with each elemental.",
      "pt": "Agem após Lewis — encerre o turno para abrir a janela de controle e mover/atacar com cada elemental."
    },
    "ui.elemental.auto_comandar": {
      "en": "⚔️ AUTO-COMMAND ALL ELEMENTALS",
      "pt": "⚔️ AUTO-COMANDAR TODOS OS ELEMENTAIS"
    },
    "ui.elemental.conjurado": {
      "en": "🌪️ Elemental summoned! End the turn to control it.",
      "pt": "🌪️ Elemental conjurado! Encerre o turno para controlá-lo."
    },
    "ui.elemental.conjurados_titulo": {
      "en": "🌪️ SUMMONED ELEMENTALS",
      "pt": "🌪️ ELEMENTAIS CONJURADOS"
    },
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
    "ui.elemental.tipo.eletrico": {
      "en": "Lightning",
      "pt": "Elétrico"
    },
    "ui.elemental.tipo.fogo": {
      "en": "Fire",
      "pt": "Fogo"
    },
    "ui.elemental.tipo.gelo": {
      "en": "Ice",
      "pt": "Gelo"
    },
    "ui.elemental.tipo.pedra": {
      "en": "Stone",
      "pt": "Pedra"
    },
    "ui.equipar.bolsa_cheia": {
      "en": "❌ Inventory full — no room to unequip",
      "pt": "❌ Inventário cheio — sem espaço para desequipar"
    },
    "ui.equipar.classe_nao_usa": {
      "en": "❌ {heroi} cannot use {item}",
      "pt": "❌ {heroi} não pode usar {item}"
    },
    "ui.equipar.duas_maos": {
      "en": "❌ {item} requires two hands — remove the shield first",
      "pt": "❌ {item} requer duas mãos — remova o escudo primeiro"
    },
    "ui.equipar.escudo_com_duas_maos": {
      "en": "❌ Cannot use a shield with a two-handed weapon",
      "pt": "❌ Não pode usar escudo com arma de duas mãos"
    },
    "ui.equipar.sem_slot": {
      "en": "❌ {item} cannot be equipped",
      "pt": "❌ {item} não pode ser equipado"
    },
    "ui.equipar.slot_incompativel": {
      "en": "❌ {item} cannot be equipped in this slot",
      "pt": "❌ {item} não pode ser equipado neste slot"
    },
    "ui.ficha.compre_tecnicas": {
      "en": "Buy techniques at the Heroes' Guild.",
      "pt": "Compre técnicas na Guilda dos Heróis."
    },
    "ui.ficha.doenca": {
      "en": "{tipo} disease",
      "pt": "Doença {tipo}"
    },
    "ui.ficha.experiencia": {
      "en": "EXPERIENCE",
      "pt": "EXPERIÊNCIA"
    },
    "ui.ficha.fome": {
      "en": "HUNGER",
      "pt": "FOME"
    },
    "ui.ficha.habilidade_classe": {
      "en": "⚗️ CLASS ABILITY",
      "pt": "⚗️ HABILIDADE DE CLASSE"
    },
    "ui.ficha.habilidade_classe_curta": {
      "en": "CLASS ABILITY",
      "pt": "HABILIDADE DE CLASSE"
    },
    "ui.ficha.habilidades_botao": {
      "en": "Abilities (H)",
      "pt": "Habilidades (H)"
    },
    "ui.ficha.iniciativa": {
      "en": "INITIATIVE",
      "pt": "INICIATIVA"
    },
    "ui.ficha.magias_title": {
      "en": "Spells",
      "pt": "Magias"
    },
    "ui.ficha.modificadores_males": {
      "en": "TEMPORARY MODIFIERS — AFFLICTIONS",
      "pt": "MODIFICADORES TEMPORÁRIOS — MALES"
    },
    "ui.ficha.nenhuma_exclusiva": {
      "en": "— no exclusive —",
      "pt": "— nenhuma exclusiva —"
    },
    "ui.ficha.nenhuma_tecnica": {
      "en": "— no technique —",
      "pt": "— nenhuma técnica —"
    },
    "ui.ficha.nivel": {
      "en": "LEVEL",
      "pt": "NÍVEL"
    },
    "ui.ficha.nivel_caixa": {
      "en": "LEVEL {n}",
      "pt": "NÍVEL {n}"
    },
    "ui.ficha.percepcao": {
      "en": "PERCEPTION",
      "pt": "PERCEPÇÃO"
    },
    "ui.ficha.pontos_de_vida": {
      "en": "HIT POINTS",
      "pt": "PONTOS DE VIDA"
    },
    "ui.ficha.raio_visao": {
      "en": "VISION RADIUS",
      "pt": "RAIO DE VISÃO"
    },
    "ui.ficha.sede": {
      "en": "THIRST",
      "pt": "SEDE"
    },
    "ui.ficha.so_leitura": {
      "en": "read only",
      "pt": "só leitura"
    },
    "ui.ficha.status_botao": {
      "en": "📊 Status (S)",
      "pt": "📊 Status (S)"
    },
    "ui.ficha.tecnica_exclusiva": {
      "en": "✨ Exclusive Technique",
      "pt": "✨ Técnica Exclusiva"
    },
    "ui.ficha.tecnica_guilda": {
      "en": "⚔️ Guild Technique",
      "pt": "⚔️ Técnica da Guilda"
    },
    "ui.ficha.tecnica_guilda_n": {
      "en": "Guild Technique {n}",
      "pt": "Técnica da Guilda {n}"
    },
    "ui.ficha.ver_inventario": {
      "en": "View inventory",
      "pt": "Ver inventário"
    },
    "ui.ficha.ver_magias": {
      "en": "View spells (M)",
      "pt": "Ver magias (M)"
    },
    "ui.fim.derrota_msg": {
      "en": "Darkness won... this time.",
      "pt": "A escuridão venceu... desta vez."
    },
    "ui.fim.derrota_titulo": {
      "en": "💀 DEFEAT 💀",
      "pt": "💀 DERROTA 💀"
    },
    "ui.fim.jogar_novamente": {
      "en": "Play Again",
      "pt": "Jogar Novamente"
    },
    "ui.fim.vitoria_msg": {
      "en": "The adventurers saved the realm!",
      "pt": "Os aventureiros salvaram o reino!"
    },
    "ui.fim.vitoria_titulo": {
      "en": "⚔ VICTORY! ⚔",
      "pt": "⚔ VITÓRIA! ⚔"
    },
    "ui.fora.banner": {
      "en": "🏙️ You left the dungeon — {estado}",
      "pt": "🏙️ Você deixou a masmorra — {estado}"
    },
    "ui.fora.pronto": {
      "en": "<b>ready to return</b>",
      "pt": "<b>pronto para voltar</b>"
    },
    "ui.fora.volta_em": {
      "en": "back in <b>{n}</b> round(s)",
      "pt": "volta em <b>{n}</b> rodada(s)"
    },
    "ui.fora.voltar_masmorra": {
      "en": "⛓️ Back to the dungeon",
      "pt": "⛓️ Voltar à masmorra"
    },
    "ui.geral.cancelar": {
      "en": "Cancel",
      "pt": "Cancelar"
    },
    "ui.geral.cancelar_caixa": {
      "en": "CANCEL",
      "pt": "CANCELAR"
    },
    "ui.geral.confirmar": {
      "en": "✓ CONFIRM",
      "pt": "✓ CONFIRMAR"
    },
    "ui.geral.fechar": {
      "en": "Close",
      "pt": "Fechar"
    },
    "ui.geral.pronto": {
      "en": "✓ Ready",
      "pt": "✓ Pronto"
    },
    "ui.geral.quad": {
      "en": "sq.",
      "pt": "quad."
    },
    "ui.guerreiro_luz.ataque": {
      "en": "Attack",
      "pt": "Ataque"
    },
    "ui.guerreiro_luz.ca": {
      "en": "AC",
      "pt": "CA"
    },
    "ui.guerreiro_luz.dano": {
      "en": "Damage",
      "pt": "Dano"
    },
    "ui.guerreiro_luz.visao": {
      "en": "Sight",
      "pt": "Visão"
    },
    "ui.guilda.especializacoes": {
      "en": "🌟 Specialisations",
      "pt": "🌟 Especializações"
    },
    "ui.guilda.exclusiva_badge": {
      "en": "★ Mage/Cleric only",
      "pt": "★ Exclusiva Mago/Clérigo"
    },
    "ui.guilda.indisponivel": {
      "en": "Guild unavailable right now.",
      "pt": "Guilda indisponível agora."
    },
    "ui.guilda.possuido": {
      "en": "Owned ✓",
      "pt": "Possuído ✓"
    },
    "ui.guilda.recarga_media": {
      "en": "Medium Recharge (5 rounds)",
      "pt": "Recarga Média (5 rodadas)"
    },
    "ui.guilda.requer": {
      "en": "🔒 Requires {nome}",
      "pt": "🔒 Requer {nome}"
    },
    "ui.guilda.subtitulo": {
      "en": "Improve your class permanently. Gold:",
      "pt": "Aprimore sua classe permanentemente. Ouro:"
    },
    "ui.guilda.tecnicas": {
      "en": "⚔️ Guild Techniques",
      "pt": "⚔️ Técnicas da Guilda"
    },
    "ui.guilda.tecnicas_caixa": {
      "en": "GUILD TECHNIQUES",
      "pt": "TÉCNICAS DA GUILDA"
    },
    "ui.guilda.titulo": {
      "en": "⚔ Heroes' Guild",
      "pt": "⚔ Guilda dos Heróis"
    },
    "ui.habilidade.alcance_cajado": {
      "en": "📐 <strong style=\"color:#c8a951\">Extended Reach:</strong> Hits 2 adjacent squares in front and 1 adjacent diagonal square. Requires two hands — incompatible with a shield.",
      "pt": "📐 <strong style=\"color:#c8a951\">Alcance Estendido:</strong> Atinge 2 casas adjacentes à frente e 1 casa diagonal adjacente. Requer duas mãos — incompatível com escudo."
    },
    "ui.habilidade.alcance_lanca": {
      "en": "🔱 <strong style=\"color:#c8a951\">Extended Reach:</strong> Hits up to 2 orthogonal squares ahead or 1 adjacent diagonal square. It does not require two hands.",
      "pt": "🔱 <strong style=\"color:#c8a951\">Alcance Estendido:</strong> Atinge até 2 casas ortogonais à frente ou 1 casa diagonal adjacente. Não requer duas mãos."
    },
    "ui.habilidade.impacto_bordao": {
      "en": "💫 <strong style=\"color:#c8a951\">Concussive Critical:</strong> On a natural 20, the target makes Fortitude DC 10 + 1d6. On a failure, it becomes stunned and loses its next action. Does not affect constructs or undead.",
      "pt": "💫 <strong style=\"color:#c8a951\">Impacto Atordoante:</strong> Em um 20 natural, o alvo faz Fortitude CD 10 + 1d6. Se falhar, fica tonto e perde sua próxima ação. Não funciona contra construtos nem mortos-vivos."
    },
    "ui.habilidade.cajado_arcano": {
      "en": "✨ <strong style=\"color:#cc44ff\">Arcane Staff:</strong> Damage spells deal +2 damage of the spell's type. Area spells gain exactly 1 square in each dimension (3x3 becomes 4x4). Grants one extra 1st-circle spell slot, used last and recharging after 20 rounds; the slot disappears when unequipped.",
      "pt": "✨ <strong style=\"color:#cc44ff\">Cajado Arcano:</strong> Magias de dano causam +2 de dano do tipo da magia. Magias de área ganham exatamente 1 quadrado em cada dimensão (3x3 passa a 4x4). Concede 1 slot extra de magia de 1º círculo, usado por último e recarregado após 20 rodadas; o slot desaparece ao desequipar."
    },
    "ui.habilidade.alcance_chicote": {
      "en": "🔄 <strong style=\"color:#c8a951\">Extended Reach:</strong> Hits 2 adjacent squares and 1 adjacent diagonal square without having to move to the target.",
      "pt": "🔄 <strong style=\"color:#c8a951\">Alcance Estendido:</strong> Atinge 2 quadrados adjacentes e 1 quadrado diagonal adjacente sem precisar se mover até o alvo."
    },
    "ui.habilidade.armazenamento_magia": {
      "en": "✨ <strong style=\"color:#cc44ff\">Spell Storage:</strong> Holds {p1} spell(s) for the campaign. Using a stored spell = bonus action (-1 hunger -1 thirst). It does not consume the character's spell slot. Recharge in town.",
      "pt": "✨ <strong style=\"color:#cc44ff\">Armazenamento de Magia:</strong> Guarda {p1} magia(s) durante a campanha. Usar uma magia armazenada = ação bônus (-1 fome -1 sede). Não consome slot de magia do personagem. Recarregue na cidade."
    },
    "ui.habilidade.arremesso": {
      "en": "🎯 <strong style=\"color:#c8a951\">Throw:</strong> Can be thrown {p1} squares in any direction, diagonals included. Uses Dexterity for the attack and damage. A 1 on the d20 = the weapon is destroyed permanently.",
      "pt": "🎯 <strong style=\"color:#c8a951\">Arremesso:</strong> Pode ser arremessada {p1} quadrados em qualquer direção incluindo diagonais. Usa Destreza para acerto e dano. Resultado 1 no d20 = arma destruída permanentemente."
    },
    "ui.habilidade.arremesso_lanca": {
      "en": "<div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        🏹 <strong style=\"color:#44cc44\">Throw:</strong>\n        Can be thrown up to 4 squares in a straight line, diagonals included. Uses\n        Strength for the attack and damage (1d6 + STR). A 1 on the d20 = the spear is\n        destroyed permanently.\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ↔️ <strong style=\"color:#c8a951\">Side Reach:</strong>\n        In melee it hits all 8 adjacent squares. Compatible with a shield.\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6;\">\n        ⚠️ <strong style=\"color:#ff4136\">Warning:</strong>\n        After the throw the weapon slot is empty. Equip another weapon from your\n        inventory (free action, no cost).\n      </div>",
      "pt": "\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        🏹 <strong style=\"color:#44cc44\">Arremesso:</strong>\n        Pode ser arremessada até 4 quadrados em linha\n        reta incluindo diagonais. Usa Força para acerto\n        e dano (1d6 + FOR). Resultado 1 no d20 = lança\n        destruída permanentemente.\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ↔️ <strong style=\"color:#c8a951\">Alcance Lateral:</strong>\n        No combate corpo a corpo atinge todos os 8\n        quadrados adjacentes. Compatível com escudo.\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6;\">\n        ⚠️ <strong style=\"color:#ff4136\">Atenção:</strong>\n        Após o arremesso o slot de arma fica vazio.\n        Equipe outra arma do inventário (ação livre, sem custo).\n      </div>\n    "
    },
    "ui.habilidade.ataque_bonus_secundaria": {
      "en": "<div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ⚔️ <strong style=\"color:#c8a951\">Bonus Attack (off hand):</strong>\n        Equipped in the off hand, it grants an extra adjacent attack as a bonus action.\n        Uses the better of Strength and Dexterity for the attack and damage\n        (1d4 + STR/DEX).\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        🎯 <strong style=\"color:#c8a951\">Throw:</strong>\n        Can be thrown up to 3 squares, diagonals included. A 1 on the d20 = the dagger\n        is destroyed permanently.\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6;\">\n        🛡️ <strong style=\"color:#ff4136\">Warning:</strong>\n        It takes the off-hand slot — incompatible with two-handed weapons.\n      </div>",
      "pt": "\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ⚔️ <strong style=\"color:#c8a951\">Ataque Bônus (mão secundária):</strong>\n        Equipada na mão esquerda, dá um ataque extra\n        adjacente como ação bônus. Usa o melhor bônus entre\n        Força e Destreza para acerto e dano (1d4 + FOR/DES).\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        🎯 <strong style=\"color:#c8a951\">Arremesso:</strong>\n        Pode ser arremessada até 3 quadrados incluindo\n        diagonais. Resultado 1 no d20 = adaga destruída\n        permanentemente.\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6;\">\n        🛡️ <strong style=\"color:#ff4136\">Atenção:</strong>\n        Ocupa o slot da mão esquerda — incompatível com\n        armas de duas mãos.\n      </div>\n    "
    },
    "ui.habilidade.ataque_extra_secundaria": {
      "en": "<div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ⚔️ <strong style=\"color:#c8a951\">Extra Attack (off hand):</strong>\n        The whip can be equipped in the off hand in place of the shield and makes an\n        extra attack as a bonus action, keeping its reach of up to 2 squares. Uses\n        Dexterity for the attack and damage (1d4 + DEX).\n      </div>",
      "pt": "\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ⚔️ <strong style=\"color:#c8a951\">Ataque Extra (mão secundária):</strong>\n        O chicote pode ser equipado na mão esquerda no lugar do escudo e realiza\n        um ataque extra como ação bônus, preservando alcance de até 2 quadrados.\n        Usa Destreza para acerto e dano (1d4 + DES).\n      </div>\n    "
    },
    "ui.habilidade.combinacao_armada": {
      "en": "Combination armed. Choose the target manually to attack.",
      "pt": "Combinação armada. Escolha o alvo manualmente para atacar."
    },
    "ui.habilidade.combinacao_cancelada": {
      "en": "Attack combination cancelled.",
      "pt": "Combinação de ataque cancelada."
    },
    "ui.habilidade.combo_so_turno": {
      "en": "The combination can only be prepared on the warrior's turn.",
      "pt": "A combinação só pode ser preparada no turno do guerreiro."
    },
    "ui.habilidade.critico_espada": {
      "en": "⚔️ <strong style=\"color:#c8a951\">Improved Critical:</strong> A natural 19 or 20 on the d20 is a critical when the attack hits.",
      "pt": "⚔️ <strong style=\"color:#c8a951\">Crítico Aprimorado:</strong> Um resultado natural de 19 ou 20 no d20 é crítico quando o ataque acerta."
    },
    "ui.habilidade.duas_maos": {
      "en": "✋ <strong style=\"color:#c8a951\">Two Hands:</strong> Incompatible with a shield or a second weapon. Equipping/swapping gear is a free action (no cost).",
      "pt": "✋ <strong style=\"color:#c8a951\">Duas Mãos:</strong> Incompatível com escudo ou 2ª arma. Equipar/trocar de equipamento é ação livre (sem custo)."
    },
    "ui.habilidade.escolha_n_habilidades": {
      "en": "Choose {n} abilities for the attack",
      "pt": "Escolha {n} habilidades para o ataque"
    },
    "ui.habilidade.escolha_n_metamagias": {
      "en": "Choose {n} metamagics for the next spell",
      "pt": "Escolha {n} metamagias para a próxima magia"
    },
    "ui.habilidade.escolha_somente": {
      "en": "Choose only {n} abilities for this combination.",
      "pt": "Escolha somente {n} habilidades para esta combinação."
    },
    "ui.habilidade.expansao_inventario": {
      "en": "🎒 <strong style=\"color:#cc44ff\">Inventory Expansion:</strong> Takes 1 magic slot and permanently adds +{p1} slots to the free inventory while equipped.",
      "pt": "🎒 <strong style=\"color:#cc44ff\">Expansão de Inventário:</strong> Ocupa 1 slot mágico e adiciona permanentemente +{p1} slots ao inventário livre enquanto equipada."
    },
    "ui.habilidade.ficha_indisponivel": {
      "en": "Ability sheet unavailable right now.",
      "pt": "Ficha de habilidades indisponível agora."
    },
    "ui.habilidade.iluminacao": {
      "en": "🕯️ <strong style=\"color:#c8a951\">Illumination:</strong> Extends the character's line of sight by 1 square in every direction. Lasts {p1} rounds. Once it expires the slot is empty.",
      "pt": "🕯️ <strong style=\"color:#c8a951\">Iluminação:</strong> Expande a linha de visão do personagem em 1 quadrado em todas as direções. Dura {p1} rodadas. Após expirar o slot fica vazio."
    },
    "ui.habilidade.impacto_maca": {
      "en": "💥 <strong style=\"color:#c8a951\">Devastating Impact:</strong> On a natural 20 on the d20, the Mace's damage is tripled.",
      "pt": "💥 <strong style=\"color:#c8a951\">Impacto Devastador:</strong> Quando o ataque obtém 20 natural no d20, o dano da Maça é triplicado."
    },
    "ui.habilidade.impacto_machado_orc": {
      "en": "💥 <strong style=\"color:#c8a951\">Devastating Impact:</strong> On a natural 20 on the d20, the Orcish Battleaxe's damage is tripled.",
      "pt": "💥 <strong style=\"color:#c8a951\">Impacto Devastador:</strong> Quando o ataque obtém 20 natural no d20, o dano do Machado de Guerra Órquico é triplicado."
    },
    "ui.habilidade.impacto_mangual": {
      "en": "💥 <strong style=\"color:#c8a951\">Devastating Impact:</strong> On a natural 20 on the d20, the Flail's damage is multiplied by 2.5.",
      "pt": "💥 <strong style=\"color:#c8a951\">Impacto Devastador:</strong> Quando o ataque obtém 20 natural no d20, o dano do Mangual é multiplicado por 2,5."
    },
    "ui.habilidade.impacto_martelo": {
      "en": "💥 <strong style=\"color:#c8a951\">Devastating Impact:</strong> On a natural 20 on the d20, the Warhammer's damage is tripled.",
      "pt": "💥 <strong style=\"color:#c8a951\">Impacto Devastador:</strong> Quando o ataque obtém 20 natural no d20, o dano do Martelo de Guerra é triplicado."
    },
    "ui.habilidade.incendiario": {
      "en": "🔥 <strong style=\"color:#ff6633\">Incendiary:</strong> Adds {p1} fire damage to every shot. Fire damage ignores the AC bonus from shields.",
      "pt": "🔥 <strong style=\"color:#ff6633\">Incendiário:</strong> Adiciona {p1} de dano de fogo a cada disparo. Dano de fogo ignora bônus de CA de escudos."
    },
    "ui.habilidade.limite_por_turno": {
      "en": "You can only arm {n} ability(ies) per turn.",
      "pt": "Você só pode armar {n} habilidade(s) por turno."
    },
    "ui.habilidade.nao_e_sua_vez": {
      "en": "It's not your turn.",
      "pt": "Não é a sua vez."
    },
    "ui.habilidade.passiva_ja_ativa": {
      "en": "This ability is passive and already active.",
      "pt": "Esta habilidade é passiva e já está ativa."
    },
    "ui.habilidade.sec_ativas": {
      "en": "ACTIVE ABILITIES",
      "pt": "HABILIDADES ATIVAS"
    },
    "ui.habilidade.sec_passivas": {
      "en": "PASSIVE AND ALWAYS ON",
      "pt": "PASSIVAS E SEMPRE ATIVAS"
    },
    "ui.habilidade.selecione_casa_desarmar": {
      "en": "Select an adjacent square to disarm.",
      "pt": "Selecione uma casa adjacente para desarmar."
    },
    "ui.habilidade.sem_acao_manual": {
      "en": "This ability is passive or has no manual action.",
      "pt": "Esta habilidade é passiva ou não possui uma ação manual."
    },
    "ui.habilidade.sem_ativas": {
      "en": "No active ability found.",
      "pt": "Nenhuma habilidade ativa encontrada."
    },
    "ui.habilidade.sem_descricao": {
      "en": "No description available.",
      "pt": "Sem descrição disponível."
    },
    "ui.habilidade.sem_passivas": {
      "en": "No passive ability found.",
      "pt": "Nenhuma habilidade passiva encontrada."
    },
    "ui.habilidade.sem_tecnicas": {
      "en": "No Guild technique acquired.",
      "pt": "Nenhuma técnica da Guilda adquirida."
    },
    "ui.habilidade.so_na_masmorra": {
      "en": "Abilities can only be used in the dungeon.",
      "pt": "Habilidades só podem ser usadas na masmorra."
    },
    "ui.habilidade.tecla_h": {
      "en": "H key",
      "pt": "tecla H"
    },
    "ui.habilidade.tres_armadas": {
      "en": "Three abilities armed. Choose the target manually to attack.",
      "pt": "Três habilidades armadas. Escolha o alvo manualmente para atacar."
    },
    "ui.habilidade.uma_de_n": {
      "en": "1 of {n} abilities selected.",
      "pt": "1 de {n} habilidades selecionada."
    },
    "ui.habilidade.veneno": {
      "en": "<div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ☠️ <strong style=\"color:#9900cc\">Effect:</strong> {p1}\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        🎲 <strong style=\"color:#9900cc\">Save:</strong> Fortitude DC {p2} {p3}\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6;\">\n        🗡️ <strong style=\"color:#9900cc\">Application:</strong>\n        Using it coats the equipped weapon (bonus action). The next hit transfers the\n        poison to the target.\n      </div>",
      "pt": "\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        ☠️ <strong style=\"color:#9900cc\">Efeito:</strong>\n        {p1}\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6; margin-bottom:6px;\">\n        🎲 <strong style=\"color:#9900cc\">Save:</strong>\n        Fortitude dificuldade {p2}\n        {p3}\n      </div>\n      <div style=\"color:#c8b89a; font-size:10px; line-height:1.6;\">\n        🗡️ <strong style=\"color:#9900cc\">Aplicação:</strong>\n        Usar unta a arma equipada (ação bônus). O próximo golpe certeiro\n        transfere o veneno ao alvo.\n      </div>\n    "
    },
    "ui.habilidade.versatil": {
      "en": "⚔️ <strong style=\"color:#c8a951\">Versatile:</strong> One hand: 1d10 damage with a shield. Two hands: 3d4 damage without a shield. Switch modes with a bonus action (-1 hunger -1 thirst).",
      "pt": "⚔️ <strong style=\"color:#c8a951\">Versátil:</strong> Uma mão: 1d10 de dano com escudo. Duas mãos: 3d4 de dano sem escudo. Troque o modo com ação bônus (-1 fome -1 sede)."
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
    "ui.hud.acao_bonus_ja_usada": {
      "en": "Bonus action already used this turn.",
      "pt": "Ação bônus já usada neste turno."
    },
    "ui.hud.acao_principal_ja_usada": {
      "en": "Main action already used this turn.",
      "pt": "Ação principal já usada neste turno."
    },
    "ui.hud.acao_usada": {
      "en": "action used",
      "pt": "ação usada"
    },
    "ui.hud.acoes": {
      "en": "Actions",
      "pt": "Ações"
    },
    "ui.hud.ajuda_title": {
      "en": "How to play",
      "pt": "Como jogar"
    },
    "ui.hud.apagar_chamas": {
      "en": "Put out flames",
      "pt": "Apagar chamas"
    },
    "ui.fogo.prompt_titulo": {
      "en": "🔥 You are on fire",
      "pt": "🔥 Você está em chamas"
    },
    "ui.fogo.prompt_texto": {
      "en": "The flames will cause residual damage. Choose how to put them out ({n} round(s) remaining):",
      "pt": "As chamas causarão dano residual. Escolha como apagá-las ({n} rodada(s) restantes):"
    },
    "ui.fogo.usar_agua": {
      "en": "💧 Use a water bottle/canteen (free)",
      "pt": "💧 Usar garrafa/cantil de água (grátis)"
    },
    "ui.fogo.gastar_acao": {
      "en": "🔥 Spend your action to put out the fire",
      "pt": "🔥 Gastar sua ação para apagar o fogo"
    },
    "ui.fogo.nao_apagar": {
      "en": "Do not put it out",
      "pt": "Não apagar (sofrer o dano)"
    },
    "ui.fogo.agua_disponivel": {
      "en": "Water is available and puts out these flames without spending the action.",
      "pt": "Há água disponível e ela apaga estas chamas sem gastar a ação."
    },
    "ui.fogo.sem_agua": {
      "en": "No water bottle or canteen is available.",
      "pt": "Você não possui garrafa ou cantil de água."
    },
    "ui.fogo.agua_fogo_grego": {
      "en": "Greek Fire cannot be put out with water.",
      "pt": "Fogo Grego não pode ser apagado com água."
    },
    "ui.fogo.acao_indisponivel": {
      "en": "The action is not available right now.",
      "pt": "A ação não está disponível no momento."
    },
    "ui.hud.arma_envenenada": {
      "en": "poisoned weapon",
      "pt": "arma envenenada"
    },
    "ui.hud.armada": {
      "en": "readied",
      "pt": "armada"
    },
    "ui.hud.ate_atributos": {
      "en": "up to {n} simultaneous attribute(s)",
      "pt": "até {n} atributo(s) simultâneo(s)"
    },
    "ui.hud.ativa": {
      "en": "on",
      "pt": "ativa"
    },
    "ui.hud.ativo": {
      "en": "on",
      "pt": "ativo"
    },
    "ui.hud.aventureiros": {
      "en": "Adventurers",
      "pt": "Aventureiros"
    },
    "ui.hud.banner_chamas_rodadas": {
      "en": "{n} ROUND(S)",
      "pt": "{n} RODADA(S)"
    },
    "ui.hud.banner_em_chamas": {
      "en": "🔥 ON FIRE",
      "pt": "🔥 EM CHAMAS"
    },
    "ui.hud.banner_exaustao": {
      "en": "EXHAUSTION ({causas} &lt;20): to-hit · saves · damage",
      "pt": "EXAUSTÃO ({causas} &lt;20): acerto · resistência · dano"
    },
    "ui.hud.banner_pocao_regen": {
      "en": "REGENERATION POTION: {n} HP IN RESERVE",
      "pt": "POÇÃO DE REGENERAÇÃO: {n} HP NA RESERVA"
    },
    "ui.hud.banner_regeneracao": {
      "en": "DIVINE REGENERATION: +1 HP per turn",
      "pt": "REGENERAÇÃO DIVINA: +1 HP por turno"
    },
    "ui.hud.banner_requiem": {
      "en": "🎻 REQUIEM",
      "pt": "🎻 RÉQUIEM"
    },
    "ui.hud.banner_requiem_alvo": {
      "en": "TARGET: {alvo} — {dano} (UPKEEP 🍖-2 💧-2)",
      "pt": "ALVO: {alvo} — {dano} (MANUT. 🍖-2 💧-2)"
    },
    "ui.hud.banner_saciado": {
      "en": "SATED (hunger and thirst &gt;80): to-hit · saves · damage",
      "pt": "SACIADO (fome e sede &gt;80): acerto · resistência · dano"
    },
    "ui.hud.banner_turnos_restantes": {
      "en": "{n} TURN(S) LEFT",
      "pt": "{n} TURNO(S) RESTANTE(S)"
    },
    "ui.hud.banner_ultimo_esforco": {
      "en": "🔥 LAST STAND",
      "pt": "🔥 ÚLTIMO ESFORÇO"
    },
    "ui.hud.bonus": {
      "en": "bonus",
      "pt": "bônus"
    },
    "ui.hud.bonus_usado": {
      "en": "bonus used",
      "pt": "bônus usado"
    },
    "ui.hud.cam_reset_title": {
      "en": "Default isometric view (R)",
      "pt": "Visão isométrica padrão (R)"
    },
    "ui.hud.cancao_de_henrique": {
      "en": "Henrique's Heroic Song",
      "pt": "Canção Heroica de Henrique"
    },
    "ui.hud.cantando": {
      "en": "singing",
      "pt": "cantando"
    },
    "ui.hud.chamas_agua_ou_acao": {
      "en": "WATER OR THE ACTION PUTS IT OUT",
      "pt": "ÁGUA OU AÇÃO APAGA"
    },
    "ui.hud.chamas_so_acao": {
      "en": "ONLY THE ACTION PUTS IT OUT (GREEK FIRE)",
      "pt": "SÓ A AÇÃO APAGA (FOGO GREGO)"
    },
    "ui.hud.criar_armadilha_desc": {
      "en": "Pick an adjacent square. DEX check{b}; a natural 1 sets the trap off on you.",
      "pt": "Selecione uma casa adjacente. Teste de DES{b}; 1 natural dispara a armadilha em você."
    },
    "ui.hud.detectar_desc": {
      "en": "reveals nearby traps and does not set them off",
      "pt": "revela armadilhas próximas e não as dispara"
    },
    "ui.hud.doenca_curavel": {
      "en": "curable by a cleric or the temple",
      "pt": "curável por clérigo ou templo"
    },
    "ui.hud.doenca_titulo": {
      "en": "🦠 {sev} DISEASE",
      "pt": "🦠 DOENÇA {sev}"
    },
    "ui.hud.encerrar_turno": {
      "en": "⏭ End Turn",
      "pt": "⏭ Encerrar Turno"
    },
    "ui.hud.equipado_loja": {
      "en": "Equipped (Shop)",
      "pt": "Equipado (Loja)"
    },
    "ui.hud.escapar_bau": {
      "en": "Escape the chest",
      "pt": "Escapar do baú"
    },
    "ui.hud.espaco_ok": {
      "en": "✓ Spacing 0.94",
      "pt": "✓ Espaço 0,94"
    },
    "ui.hud.espaco_reset_title": {
      "en": "Back to the previous 0.94 spacing",
      "pt": "Voltar ao espaçamento anterior de 0,94"
    },
    "ui.hud.espaco_restaurado": {
      "en": "↶ 3D spacing restored to 0.94.",
      "pt": "↶ Espaçamento 3D restaurado para 0,94."
    },
    "ui.hud.espaco_voltar": {
      "en": "↶ Spacing 0.94",
      "pt": "↶ Espaço 0,94"
    },
    "ui.hud.exausto_efeitos": {
      "en": "-2 DEX · -2 STR · +1 hunger/thirst per action",
      "pt": "-2 DES · -2 FOR · +1 fome/sede por ação"
    },
    "ui.hud.fechar_ficha": {
      "en": "✕ Close sheet",
      "pt": "✕ Fechar ficha"
    },
    "ui.hud.fora_de_turno_ou_acao_usada": {
      "en": "It's not your turn or the action was already used.",
      "pt": "Não é a sua vez ou a ação já foi usada."
    },
    "ui.hud.forca_bau": {
      "en": "Strength DC 20 · main action",
      "pt": "Força CD 20 · ação principal"
    },
    "ui.hud.forca_estomago": {
      "en": "Strength against the stomach",
      "pt": "Força contra o estômago"
    },
    "ui.hud.forcar_saida": {
      "en": "Force your way out",
      "pt": "Forçar saída"
    },
    "ui.hud.furtivo_1": {
      "en": "+{n}d4 only while invisible/hidden",
      "pt": "+{n}d4 apenas se estiver invisível/oculto"
    },
    "ui.hud.furtivo_2": {
      "en": "+{n}d4 if invisible or with an ally adjacent to the target",
      "pt": "+{n}d4 se invisível ou com aliado adjacente ao alvo"
    },
    "ui.hud.furtivo_3": {
      "en": "+{n}d4 if invisible or with an adjacent ally; reacts automatically 1×/enemy/round to an ally's attack",
      "pt": "+{n}d4 se invisível ou com aliado adjacente; reage automaticamente 1×/inimigo/rodada ao ataque de um aliado"
    },
    "ui.hud.gasta_acao_principal": {
      "en": "uses your main action",
      "pt": "gasta a ação principal"
    },
    "ui.hud.guilda": {
      "en": "GUILD",
      "pt": "GUILDA"
    },
    "ui.hud.habilidades": {
      "en": "Abilities",
      "pt": "Habilidades"
    },
    "ui.hud.inspirado_cancao": {
      "en": "Inspired by the Heroic Song",
      "pt": "Inspirado pela Canção Heroica"
    },
    "ui.hud.inventario_title": {
      "en": "Inventory",
      "pt": "Inventário"
    },
    "ui.hud.invisivel": {
      "en": "invisible",
      "pt": "invisível"
    },
    "ui.hud.invisivel_desc": {
      "en": "monsters cannot target you until you attack",
      "pt": "não é alvo dos monstros até atacar"
    },
    "ui.hud.libertar_prisioneiro": {
      "en": "🔓 Free the prisoner",
      "pt": "🔓 Libertar prisioneiro"
    },
    "ui.hud.limite_habilidades": {
      "en": "You can only ready {n} abilities per turn.",
      "pt": "Você só pode armar {n} habilidades por turno."
    },
    "ui.hud.livre": {
      "en": "free",
      "pt": "livre"
    },
    "ui.hud.log_acao_principal_usada": {
      "en": "❌ Main action already used",
      "pt": "❌ Ação principal já usada"
    },
    "ui.hud.mais_ca_revelar": {
      "en": "+2 AC on revealing",
      "pt": "+2 CA ao revelar"
    },
    "ui.hud.mao_principal": {
      "en": "main hand",
      "pt": "mão principal"
    },
    "ui.hud.mapa_cr_title": {
      "en": "CR Map (master)",
      "pt": "Mapa de CR (mestre)"
    },
    "ui.hud.mestre_do_jogo": {
      "en": "📖 GAME MASTER",
      "pt": "📖 MESTRE DO JOGO"
    },
    "ui.hud.meu_personagem": {
      "en": "My Character",
      "pt": "Meu Personagem"
    },
    "ui.hud.mova_prisioneiro": {
      "en": "🧍 Move the prisoner — click them and then a square; then end the turn.",
      "pt": "🧍 Mova o prisioneiro — clique nele e depois numa casa; então encerre o turno."
    },
    "ui.hud.mover_mais": {
      "en": "move",
      "pt": "mover"
    },
    "ui.hud.oportunidade": {
      "en": "Opportunity",
      "pt": "Oportunidade"
    },
    "ui.hud.oportunidade_desc": {
      "en": "Spend the extra credit on movement now, or simply act normally (attack/heal/cast a spell/etc.) to spend it automatically.",
      "pt": "Gaste o crédito extra em movimento agora, ou apenas aja normalmente (atacar/curar/lançar magia/etc.) para gastá-lo automaticamente."
    },
    "ui.hud.orbit_hint": {
      "en": "🖱 left: orbit &nbsp;·&nbsp; right: pan &nbsp;·&nbsp; scroll: zoom",
      "pt": "🖱 esq: orbitar &nbsp;·&nbsp; dir: pan &nbsp;·&nbsp; scroll: zoom"
    },
    "ui.hud.parar": {
      "en": "stop",
      "pt": "parar"
    },
    "ui.hud.passiva": {
      "en": "passive",
      "pt": "passiva"
    },
    "ui.hud.personagem_title": {
      "en": "Character (actions and abilities)",
      "pt": "Personagem (ações e habilidades)"
    },
    "ui.hud.recupera_ouro": {
      "en": "You may recover the gold.",
      "pt": "Pode recuperar o ouro."
    },
    "ui.hud.recupera_ouro_curto": {
      "en": "chance to recover the gold",
      "pt": "chance de recuperar o ouro"
    },
    "ui.hud.remover": {
      "en": "Remove",
      "pt": "Remover"
    },
    "ui.hud.sair": {
      "en": "exit",
      "pt": "sair"
    },
    "ui.hud.segunda_mao": {
      "en": "off hand",
      "pt": "2ª mão"
    },
    "ui.hud.selecionar_alvo": {
      "en": "Select Target",
      "pt": "Selecionar Alvo"
    },
    "ui.hud.selecione_casa": {
      "en": "pick the square",
      "pt": "selecione a casa"
    },
    "ui.hud.sem_aliado": {
      "en": "No ally available.",
      "pt": "Nenhum aliado disponível."
    },
    "ui.hud.sem_aliado_adjacente": {
      "en": "No adjacent ally.",
      "pt": "Nenhum aliado adjacente."
    },
    "ui.hud.sem_aliado_raio4": {
      "en": "No ally within 4 squares.",
      "pt": "Nenhum aliado a até 4 quadrados."
    },
    "ui.hud.sem_alvo": {
      "en": "No target available.",
      "pt": "Nenhum alvo disponível."
    },
    "ui.hud.slot.arma": {
      "en": "Weapon",
      "pt": "Arma"
    },
    "ui.hud.slot.armadura": {
      "en": "Armour",
      "pt": "Armadura"
    },
    "ui.hud.slot.cabeca": {
      "en": "Head",
      "pt": "Cabeça"
    },
    "ui.hud.slot.magico1": {
      "en": "Magic 1",
      "pt": "Mágico 1"
    },
    "ui.hud.slot.magico2": {
      "en": "Magic 2",
      "pt": "Mágico 2"
    },
    "ui.hud.slot.secundario": {
      "en": "Off hand",
      "pt": "Secundário"
    },
    "ui.hud.so_no_seu_turno": {
      "en": "Only on your turn.",
      "pt": "Só no seu turno."
    },
    "ui.hud.tag_automatica": {
      "en": "AUTOMATIC",
      "pt": "AUTOMÁTICA"
    },
    "ui.hud.tag_item": {
      "en": "ITEM",
      "pt": "ITEM"
    },
    "ui.hud.three_indisponivel": {
      "en": "⚠ Three.js unavailable — check your internet connection.",
      "pt": "⚠ Three.js não disponível — verifique a conexão de internet."
    },
    "ui.hud.toggle3d_title": {
      "en": "Toggle 3D / 2D view",
      "pt": "Alternar visão 3D / 2D"
    },
    "ui.hud.turno_1": {
      "en": "Round 1",
      "pt": "Turno 1"
    },
    "ui.hud.usada": {
      "en": "used",
      "pt": "usada"
    },
    "ui.hud.visao_mais": {
      "en": "👁️ Sight +{n} squares",
      "pt": "👁️ Visão +{n} quadrados"
    },
    "ui.instrumento.custo": {
      "en": "Cost",
      "pt": "Custo"
    },
    "ui.instrumento.custo_cancao": {
      "en": "same as the Heroic Song",
      "pt": "igual ao da Canção Heroica"
    },
    "ui.instrumento.dano_sonoro": {
      "en": "{dano} sonic",
      "pt": "{dano} sonoro"
    },
    "ui.instrumento.duas_maos": {
      "en": "2 hands — attack OR play in the same turn",
      "pt": "2 mãos — atacar OU tocar no mesmo turno"
    },
    "ui.instrumento.escolha_alvo": {
      "en": "{icone} {nome} — Choose the target (range {alcance}sq)",
      "pt": "{icone} {nome} — Escolha o alvo (alcance {alcance}q)"
    },
    "ui.instrumento.escolha_direcao": {
      "en": "Choose the direction",
      "pt": "Escolha a direção"
    },
    "ui.instrumento.escolha_direcao_dica": {
      "en": "Choose the direction of the call",
      "pt": "Escolha a direção do chamado"
    },
    "ui.instrumento.improviso_direcao": {
      "en": "Improvisation — Direction",
      "pt": "Improviso — Direção"
    },
    "ui.instrumento.quadrados": {
      "en": "{n} squares",
      "pt": "{n} quadrados"
    },
    "ui.instrumento.raio": {
      "en": "Radius",
      "pt": "Raio"
    },
    "ui.instrumento.rodadas": {
      "en": "{n} rounds",
      "pt": "{n} rodadas"
    },
    "ui.instrumento.sem_inimigo_raio": {
      "en": "No enemy within {n} squares.",
      "pt": "Nenhum inimigo a até {n} quadrados."
    },
    "ui.instrumento.uma_mao": {
      "en": "1 hand — attack AND play in the same turn",
      "pt": "1 mão — atacar E tocar no mesmo turno"
    },
    "ui.inv.bau_compartilhado_caixa": {
      "en": "SHARED CHEST",
      "pt": "BAÚ COMPARTILHADO"
    },
    "ui.inv.bau_heroi": {
      "en": "Hero's chest",
      "pt": "Baú do herói"
    },
    "ui.inv.bau_heroi_caixa": {
      "en": "HERO'S CHEST",
      "pt": "BAÚ DO HERÓI"
    },
    "ui.inv.bloqueado_duas_maos": {
      "en": "Blocked — two-handed weapon equipped",
      "pt": "Bloqueado — arma de duas mãos equipada"
    },
    "ui.inv.comparado": {
      "en": "COMPARED TO EQUIPPED",
      "pt": "COMPARADO AO EQUIPADO"
    },
    "ui.inv.decorar_quarto": {
      "en": "🛏️ Decorate room",
      "pt": "🛏️ Decorar quarto"
    },
    "ui.inv.depositar": {
      "en": "Deposit",
      "pt": "Depositar"
    },
    "ui.inv.dica_do_bau": {
      "en": "Click an item in the chest to send it to your bag.",
      "pt": "Clique num item do baú para mandá-lo para a bolsa."
    },
    "ui.inv.dica_para_o_bau": {
      "en": "Click an item to select it and click a chest slot to store it — or drag it.",
      "pt": "Clique num item para selecionar e clique num espaço do baú para guardar — ou arraste."
    },
    "ui.inv.doses_restantes": {
      "en": "Doses left",
      "pt": "Doses restantes"
    },
    "ui.inv.espaco_vazio": {
      "en": "Empty slot",
      "pt": "Espaço vazio"
    },
    "ui.inv.inventario": {
      "en": "Inventory",
      "pt": "Inventário"
    },
    "ui.inv.municao_aria": {
      "en": "{n} projectiles left",
      "pt": "{n} projéteis restantes"
    },
    "ui.inv.quantidade_ouro": {
      "en": "Amount of gold",
      "pt": "Quantidade de ouro"
    },
    "ui.inv.slot.armor": {
      "en": "Armour",
      "pt": "Armadura"
    },
    "ui.inv.slot.boots": {
      "en": "Boots",
      "pt": "Bota"
    },
    "ui.inv.slot.head": {
      "en": "Helmet",
      "pt": "Elmo"
    },
    "ui.inv.slot.item1": {
      "en": "Magic Item 1",
      "pt": "Item Mágico 1"
    },
    "ui.inv.slot.item2": {
      "en": "Magic Item 2",
      "pt": "Item Mágico 2"
    },
    "ui.inv.slot.magico1": {
      "en": "Magic Item 1",
      "pt": "Item Mágico 1"
    },
    "ui.inv.slot.magico2": {
      "en": "Magic Item 2",
      "pt": "Item Mágico 2"
    },
    "ui.inv.slot.off_hand": {
      "en": "Off hand / shield",
      "pt": "Mão esquerda / escudo"
    },
    "ui.inv.slot.ring1": {
      "en": "Ring 1",
      "pt": "Anel 1"
    },
    "ui.inv.slot.ring2": {
      "en": "Ring 2",
      "pt": "Anel 2"
    },
    "ui.inv.slot.secundario": {
      "en": "Off hand / shield",
      "pt": "Mão esquerda / escudo"
    },
    "ui.inv.slot.weapon": {
      "en": "Weapon",
      "pt": "Arma"
    },
    "ui.inv.somente_leitura": {
      "en": "(read only)",
      "pt": "(somente leitura)"
    },
    "ui.inv.titulo": {
      "en": "INVENTORY",
      "pt": "INVENTÁRIO"
    },
    "ui.item.adaga.nome": {
      "en": "Dagger",
      "pt": "Adaga"
    },
    "ui.item.adaga_secundaria.nome": {
      "en": "Off-hand Dagger",
      "pt": "Adaga Secundária"
    },
    "ui.item.agua_benta.desc": {
      "en": "Throw (4 sq., DEX attack). Deals 2d6 holy damage and creates a holy zone for 2 rounds.",
      "pt": "Arremesse (4 quad., ataque por DES). Causa 2d6 de dano sagrado e cria uma zona sagrada por 2 rodadas."
    },
    "ui.item.agua_fresca.nome": {
      "en": "Fresh Water",
      "pt": "Água Fresca"
    },
    "ui.item.alcance_especial.alabarda": {
      "en": "2 adjacent squares + 1 adjacent diagonal",
      "pt": "2 casas adjacentes + 1 diagonal adjacente"
    },
    "ui.item.alcance_especial.chicote": {
      "en": "2 adjacent squares + 1 adjacent diagonal",
      "pt": "2 quadrados adjacentes + 1 diagonal adjacente"
    },
    "ui.item.alcance_especial.lanca_curta": {
      "en": "All 8 adjacent squares",
      "pt": "Todos os 8 quadrados adjacentes"
    },
    "ui.item.alcance_especial.lanca_longa": {
      "en": "2 adjacent squares + 1 adjacent diagonal",
      "pt": "2 casas adjacentes + 1 diagonal adjacente"
    },
    "ui.item.arco_longo.nome": {
      "en": "Long Bow",
      "pt": "Arco Longo"
    },
    "ui.item.armadura_batalha.nome": {
      "en": "Battle Armour",
      "pt": "Armadura de Batalha"
    },
    "ui.item.armadura_cat.leve": {
      "en": "Light",
      "pt": "Leve"
    },
    "ui.item.armadura_cat.media": {
      "en": "Medium",
      "pt": "Média"
    },
    "ui.item.armadura_cat.pesada": {
      "en": "Heavy",
      "pt": "Pesada"
    },
    "ui.item.armadura_couro.nome": {
      "en": "Leather Armour",
      "pt": "Armadura de Couro"
    },
    "ui.item.banquete_frasco.nome": {
      "en": "Feast in a Flask",
      "pt": "Banquete em Frasco"
    },
    "ui.item.besta_leve.nome": {
      "en": "Light Crossbow",
      "pt": "Besta Leve"
    },
    "ui.item.besta_mao.nome": {
      "en": "Hand Crossbow",
      "pt": "Besta de Mão"
    },
    "ui.item.bolsa_dimensao.desc": {
      "en": "+6 free inventory slots.",
      "pt": "+6 slots de inventário livre."
    },
    "ui.item.bolsa_dimensao.nome": {
      "en": "Bag of Holding",
      "pt": "Bolsa de Dimensão"
    },
    "ui.item.bomba_fumaca.desc": {
      "en": "Area (radius 1, range 4). Creates darkness for 2 rounds — blocks sight and covers the retreat. No damage.",
      "pt": "Área (raio 1, alcance 4). Cria escuridão por 2 rodadas — bloqueia a visão e cobre o recuo. Sem dano."
    },
    "ui.item.bomba_incendiaria.desc": {
      "en": "Area (radius 1, range 4). 2d6 fire, Reflex DC 12 (half).",
      "pt": "Área (raio 1, alcance 4). 2d6 de fogo, Reflexos CD 12 (metade)."
    },
    "ui.item.cajado.nome": {
      "en": "Staff",
      "pt": "Cajado"
    },
    "ui.item.carne_seca.nome": {
      "en": "Dried Meat",
      "pt": "Carne Seca"
    },
    "ui.item.cerveja_ana.nome": {
      "en": "Dwarven Ale",
      "pt": "Cerveja Anã"
    },
    "ui.item.cola_alquimica.desc": {
      "en": "Throw (4 sq., DEX attack). The target rolls Reflex DC 12; on a failure its movement is halved for 2 rounds.",
      "pt": "Arremesse (4 quad., ataque por DES). O alvo testa Reflexos CD 12; se falhar, fica com o movimento reduzido à metade por 2 rodadas."
    },
    "ui.item.cota_malha.nome": {
      "en": "Chain Mail",
      "pt": "Cota de Malha"
    },
    "ui.item.couro_leve.nome": {
      "en": "Light Leather",
      "pt": "Couro Leve"
    },
    "ui.item.desc.adjacente": {
      "en": "Adjacent",
      "pt": "Adjacente"
    },
    "ui.item.desc.alcance": {
      "en": "Range {n}",
      "pt": "Alcance {n}"
    },
    "ui.item.desc.alcance_adjacentes": {
      "en": "Range: every adjacent square",
      "pt": "Alcance: todos os quadrados adjacentes"
    },
    "ui.item.desc.alcance_mangual": {
      "en": "Range: 1 square — any of the 8 adjacent squares, including diagonals",
      "pt": "Alcance: 1 quadrado — qualquer uma das 8 casas adjacentes, incluindo diagonais"
    },
    "ui.item.desc.alcance_lanca": {
      "en": "Range: 2 orthogonal squares ahead or 1 adjacent diagonal square",
      "pt": "Alcance: 2 casas ortogonais à frente ou 1 casa diagonal adjacente"
    },
    "ui.item.desc.alcance_quad": {
      "en": "Range: {n} sq.",
      "pt": "Alcance: {n} quad."
    },
    "ui.item.desc.alcance_reto": {
      "en": "Range {n} in a straight line",
      "pt": "Alcance {n} em linha reta"
    },
    "ui.item.desc.alcance_reto_diag": {
      "en": "Range {n} straight / {d} diagonal",
      "pt": "Alcance {n} reto / {d} diagonal"
    },
    "ui.item.desc.alcance_txt": {
      "en": "Range: {alcance}",
      "pt": "Alcance: {alcance}"
    },
    "ui.item.desc.area_no_conjurador": {
      "en": "area on the caster",
      "pt": "área no conjurador"
    },
    "ui.item.desc.armadura": {
      "en": "Armour",
      "pt": "Armadura"
    },
    "ui.item.desc.arremesso": {
      "en": "🎯 Throw {n}",
      "pt": "🎯 Arremesso {n}"
    },
    "ui.item.desc.bonus_ca": {
      "en": "AC bonus: +{n}",
      "pt": "Bônus CA: +{n}"
    },
    "ui.item.desc.bonus_visao": {
      "en": "Vision bonus: +{n} sq.",
      "pt": "Bônus visão: +{n} quad."
    },
    "ui.item.desc.ca_mais": {
      "en": "AC +{n}",
      "pt": "CA +{n}"
    },
    "ui.item.desc.cerveja": {
      "en": "+{n} hunger/thirst • -1 attack for 10 rounds",
      "pt": "+{n} fome/sede • -1 ataque por 10 rodadas"
    },
    "ui.item.desc.crit_19_20": {
      "en": "natural critical: 19–20",
      "pt": "crítico natural: 19–20"
    },
    "ui.item.desc.crit_2_5": {
      "en": "Natural 20: ×2.5 damage",
      "pt": "20 natural: dano ×2,5"
    },
    "ui.item.desc.crit_segundo_ataque": {
      "en": "Natural 19/20: second attack",
      "pt": "19/20 natural: segundo ataque"
    },
    "ui.item.desc.crit_triplo": {
      "en": "Natural 20: triple damage",
      "pt": "20 natural: dano triplicado"
    },
    "ui.item.desc.dano": {
      "en": "Damage: {dano}",
      "pt": "Dano: {dano}"
    },
    "ui.item.desc.dano_arma": {
      "en": "{die} damage ({stat})",
      "pt": "{die} dano ({stat})"
    },
    "ui.item.desc.des": {
      "en": "DEX",
      "pt": "DES"
    },
    "ui.item.desc.duas_maos": {
      "en": "✋✋ 2 hands",
      "pt": "✋✋ 2 mãos"
    },
    "ui.item.desc.duracao_rodadas": {
      "en": "Duration: {n} rounds",
      "pt": "Duração: {n} rodadas"
    },
    "ui.item.desc.escudo_soma": {
      "en": "Shield — stacks with armour",
      "pt": "Escudo — soma com armadura"
    },
    "ui.item.desc.flechas": {
      "en": "Arrows: off hand",
      "pt": "Flechas: mão esquerda"
    },
    "ui.item.desc.for": {
      "en": "STR",
      "pt": "FOR"
    },
    "ui.item.desc.for_des": {
      "en": "STR/DEX",
      "pt": "FOR/DES"
    },
    "ui.item.desc.magia_acao_bonus": {
      "en": "Casting a spell = bonus action",
      "pt": "Usar magia = ação bônus"
    },
    "ui.item.desc.mais_dano": {
      "en": "+{n} damage",
      "pt": "+{n} dano"
    },
    "ui.item.desc.mais_fome": {
      "en": "+{n} hunger",
      "pt": "+{n} fome"
    },
    "ui.item.desc.mais_sede": {
      "en": "+{n} thirst",
      "pt": "+{n} sede"
    },
    "ui.item.desc.modos_duas_maos": {
      "en": "1 hand: {uma} | 2 hands: {duas}",
      "pt": "1 mão: {uma} | 2 mãos: {duas}"
    },
    "ui.item.desc.nivel": {
      "en": "Lv {n}",
      "pt": "Nv {n}"
    },
    "ui.item.desc.ocupa_slot_magico": {
      "en": "Takes up a magic slot",
      "pt": "Ocupa slot mágico"
    },
    "ui.item.desc.prata": {
      "en": "Silver",
      "pt": "Prata"
    },
    "ui.item.desc.prata_arma": {
      "en": "Silver: withstands 5 corrosion levels (the first 2 without penalties) and can damage enemies resistant to normal weapons",
      "pt": "Prata: resiste a 5 níveis de corrosão (os 2 primeiros sem penalidade) e pode causar dano em inimigos resistentes a armas normais"
    },
    "ui.item.desc.racao": {
      "en": "+{n} hunger and thirst",
      "pt": "+{n} fome e sede"
    },
    "ui.item.desc.regeneracao": {
      "en": "Pool of {n} HP • recovers +1 HP per round",
      "pt": "Reserva {n} HP • recupera +1 HP por rodada"
    },
    "ui.item.desc.requer_flechas": {
      "en": "Requires arrows",
      "pt": "Requer flechas"
    },
    "ui.item.desc.resiste_corrosao": {
      "en": "⚙️ resists +1 corrosion hit",
      "pt": "⚙️ resiste +1 golpe de corrosão"
    },
    "ui.item.desc.segunda_mao": {
      "en": "Off hand: extra attack; replaces the shield",
      "pt": "2ª mão: ataque extra; substitui o escudo"
    },
    "ui.item.desc.slot_sec_livre": {
      "en": "Off-hand slot free",
      "pt": "Slot secundário livre"
    },
    "ui.item.desc.slots_inventario": {
      "en": "+{n} inventory slots",
      "pt": "+{n} slots de inventário"
    },
    "ui.item.desc.slots_magia": {
      "en": "Spell slots: {n}",
      "pt": "Slots de magia: {n}"
    },
    "ui.item.desc.uma_por_visita": {
      "en": "1× per visit",
      "pt": "1× por visita"
    },
    "ui.item.desc.unidades": {
      "en": "{n} units",
      "pt": "{n} unidades"
    },
    "ui.item.desc.vinho": {
      "en": "+{n} hunger/thirst • -1 attack and reflexes for 10 rounds",
      "pt": "+{n} fome/sede • -1 ataque e reflexos por 10 rodadas"
    },
    "ui.item.desc.virotes": {
      "en": "Bolts: bag or off hand",
      "pt": "Virotes: bolsa ou mão esquerda"
    },
    "ui.item.efeito.atk": {
      "en": "Attack Bonus",
      "pt": "Bônus Ataque"
    },
    "ui.item.efeito.atk_bonus": {
      "en": "Attack Bonus",
      "pt": "Bônus de Ataque"
    },
    "ui.item.efeito.bless": {
      "en": "Divine Attack Bonus",
      "pt": "Bônus de Ataque divino"
    },
    "ui.item.efeito.cleanse": {
      "en": "Removes negative statuses",
      "pt": "Remove status negativos"
    },
    "ui.item.efeito.def_": {
      "en": "AC +",
      "pt": "CA +"
    },
    "ui.item.efeito.full_heal": {
      "en": "Full HP heal",
      "pt": "Cura total de HP"
    },
    "ui.item.efeito.heal": {
      "en": "Restores HP",
      "pt": "Restaura HP"
    },
    "ui.item.efeito.maxhp": {
      "en": "Raises max HP",
      "pt": "Aumenta HP máx"
    },
    "ui.item.efeito.spd": {
      "en": "Speed",
      "pt": "Velocidade"
    },
    "ui.item.efeito.temp_atk": {
      "en": "Temporary attack",
      "pt": "Ataque temporário"
    },
    "ui.item.escudo_leve.nome": {
      "en": "Light Shield",
      "pt": "Escudo Leve"
    },
    "ui.item.escudo_pesado.nome": {
      "en": "Heavy Shield",
      "pt": "Escudo Pesado"
    },
    "ui.item.espada_bastarda.nome": {
      "en": "Bastard Sword",
      "pt": "Espada Bastarda"
    },
    "ui.item.espada_curta.nome": {
      "en": "Short Sword",
      "pt": "Espada Curta"
    },
    "ui.item.espada_duas_maos.nome": {
      "en": "Two-handed Sword",
      "pt": "Espada de Duas Mãos"
    },
    "ui.item.espada_longa.nome": {
      "en": "Long Sword",
      "pt": "Espada Longa"
    },
    "ui.item.flechas_incendiarias.nome": {
      "en": "Incendiary Arrows (10)",
      "pt": "Flechas Incendiárias (10)"
    },
    "ui.item.fogo_grego.desc": {
      "en": "Throw (4 sq., DEX attack). 2d6 fire and the target catches fire (1/round for 1d4 rounds). Only the action puts it out — water does not work.",
      "pt": "Arremesse (4 quad., ataque por DES). 2d6 de fogo e o alvo pega fogo (1/rodada por 1d4 rodadas). Só a ação apaga — água não funciona."
    },
    "ui.item.frasco_acido.desc": {
      "en": "Throw (4 sq., DEX attack). 1d6 acid + half on the next round. Corrodes the target's defence (−1 AC per hit).",
      "pt": "Arremesse (4 quad., ataque por DES). 1d6 de ácido + metade na rodada seguinte. Corrói a defesa do alvo (−1 CA por acerto)."
    },
    "ui.item.frasco_oleo.desc": {
      "en": "Throw (4 sq., DEX attack). 1d6 fire and the target catches fire (1/round for 1d4 rounds). Put out with Water or by spending the action.",
      "pt": "Arremesse (4 quad., ataque por DES). 1d6 de fogo e o alvo pega fogo (1/rodada por 1d4 rodadas). Apaga com Água ou gastando a ação."
    },
    "ui.item.granada.desc": {
      "en": "Area (radius 1, range 4). 2d6 blast, Reflex DC 12 (half).",
      "pt": "Área (raio 1, alcance 4). 2d6 de explosão, Reflexos CD 12 (metade)."
    },
    "ui.item.granada_superior.desc": {
      "en": "Area (radius 1, range 4). 3d6 blast, Reflex DC 15 (half).",
      "pt": "Área (raio 1, alcance 4). 3d6 de explosão, Reflexos CD 15 (metade)."
    },
    "ui.item.iguaria_elfica.nome": {
      "en": "Elven Delicacy",
      "pt": "Iguaria Élfica"
    },
    "ui.item.kit_sobrevivencia.nome": {
      "en": "Survival Kit",
      "pt": "Kit de Sobrevivência"
    },
    "ui.item.lanca_longa.nome": {
      "en": "Long Spear",
      "pt": "Lança Longa"
    },
    "ui.item.machado.nome": {
      "en": "Axe",
      "pt": "Machado"
    },
    "ui.item.machado_grande.nome": {
      "en": "Great Axe",
      "pt": "Machado Grande"
    },
    "ui.item.martelo.nome": {
      "en": "Hammer",
      "pt": "Martelo"
    },
    "ui.item.material.metal": {
      "en": "metal",
      "pt": "metálica"
    },
    "ui.item.material.organic": {
      "en": "organic",
      "pt": "orgânica"
    },
    "ui.item.mochila_encantada.desc": {
      "en": "+2 free inventory slots.",
      "pt": "+2 slots de inventário livre."
    },
    "ui.item.mochila_encantada.nome": {
      "en": "Enchanted Leather Backpack",
      "pt": "Mochila de Couro Encantada"
    },
    "ui.item.mochila_viajante.desc": {
      "en": "+4 free inventory slots.",
      "pt": "+4 slots de inventário livre."
    },
    "ui.item.mochila_viajante.nome": {
      "en": "Traveller's Backpack",
      "pt": "Mochila do Viajante"
    },
    "ui.item.nao_consumivel": {
      "en": "This item is not consumable.",
      "pt": "Este item não é consumível."
    },
    "ui.item.pao_duro.nome": {
      "en": "Stale Bread",
      "pt": "Pão Duro"
    },
    "ui.item.placas_pesadas.nome": {
      "en": "Heavy Plate",
      "pt": "Placas Pesadas"
    },
    "ui.item.pocao_hidratante.nome": {
      "en": "Hydrating Potion",
      "pt": "Poção Hidratante"
    },
    "ui.item.rede_arremesso.desc": {
      "en": "Throw (4 sq., DEX attack). The target is trapped; to escape it spends the turn on a Fortitude DC 12 check.",
      "pt": "Arremesse (4 quad., ataque por DES). O alvo fica preso; para escapar gasta o turno num teste de Fortitude CD 12."
    },
    "ui.item.refeicao_completa.nome": {
      "en": "Full Meal",
      "pt": "Refeição Completa"
    },
    "ui.item.robes.nome": {
      "en": "Robes",
      "pt": "Robes"
    },
    "ui.item.subtipo.contundente": {
      "en": "Bludgeoning",
      "pt": "Contusão"
    },
    "ui.item.subtipo.cortante": {
      "en": "Slashing",
      "pt": "Cortante"
    },
    "ui.item.subtipo.perfurante": {
      "en": "Piercing",
      "pt": "Perfurante"
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
    "ui.item.tipo_label.arma": {
      "en": "WEAPON",
      "pt": "ARMA"
    },
    "ui.item.tipo_label.armaDistancia": {
      "en": "RANGED WEAPON",
      "pt": "ARMA À DISTÂNCIA"
    },
    "ui.item.tipo_label.armadura": {
      "en": "ARMOUR",
      "pt": "ARMADURA"
    },
    "ui.item.tipo_label.consumivel": {
      "en": "CONSUMABLE",
      "pt": "CONSUMÍVEL"
    },
    "ui.item.tipo_label.escudo": {
      "en": "SHIELD",
      "pt": "ESCUDO"
    },
    "ui.item.tipo_label.itemMagico": {
      "en": "MAGIC ITEM",
      "pt": "ITEM MÁGICO"
    },
    "ui.item.tipo_label.municao": {
      "en": "AMMUNITION",
      "pt": "MUNIÇÃO"
    },
    "ui.item.tipo_label.padrao": {
      "en": "ITEM",
      "pt": "ITEM"
    },
    "ui.item.tipo_label.secundario": {
      "en": "ACCESSORY",
      "pt": "ACESSÓRIO"
    },
    "ui.item.tipo_label.varinha": {
      "en": "MAGIC WAND",
      "pt": "VARINHA MÁGICA"
    },
    "ui.item.tocha.nome": {
      "en": "Torch",
      "pt": "Tocha"
    },
    "ui.item.varinha_arcana.desc": {
      "en": "Stores 3 spells. Casting = bonus action.",
      "pt": "Armazena 3 magias. Usar magia = ação bônus."
    },
    "ui.item.varinha_arcana.nome": {
      "en": "Arcane Wand",
      "pt": "Varinha Arcana"
    },
    "ui.item.varinha_poder.desc": {
      "en": "Stores 2 spells. Casting = bonus action.",
      "pt": "Armazena 2 magias. Usar magia = ação bônus."
    },
    "ui.item.varinha_poder.nome": {
      "en": "Wand of Power",
      "pt": "Varinha de Poder"
    },
    "ui.item.varinha_simples.desc": {
      "en": "Stores 1 spell. Casting = bonus action.",
      "pt": "Armazena 1 magia. Usar magia = ação bônus."
    },
    "ui.item.varinha_simples.nome": {
      "en": "Simple Wand",
      "pt": "Varinha Simples"
    },
    "ui.item.veneno_agonia_sufocante.desc": {
      "en": "LEGENDARY. Coated on the weapon: 1d4 damage per round for up to 1d4 rounds. Each round, Fortitude DC 14 neutralises the poison.",
      "pt": "LENDÁRIO. Untado na arma: 1d4 de dano por rodada por até 1d4 rodadas. A cada rodada, Fortitude CD 14 neutraliza o veneno."
    },
    "ui.item.veneno_aranha_sombria.desc": {
      "en": "Reduces Strength by 1d4 for 1d6 rounds. Fortitude DC 8 negates.",
      "pt": "Reduz 1d4 de Força por 1d6 rodadas. Fortitude dif. 8 anula."
    },
    "ui.item.veneno_ardonia_negra.desc": {
      "en": "Fortitude DC 14 negates. On a failure, takes 1 point of damage per round for 2d4 rounds.",
      "pt": "Fortitude CD 14 anula. Se falhar, sofre 1 ponto de dano por rodada durante 2d4 rodadas."
    },
    "ui.item.veneno_basilisco.desc": {
      "en": "Petrifies for 1 round (Fort. DC 12). Partial failure: -1 movement for 1d4 rounds.",
      "pt": "Petrifica por 1 rodada (Fort. dif. 12). Falha parcial: -1 movimento por 1d4 rodadas."
    },
    "ui.item.veneno_cobra_cuspidora.desc": {
      "en": "-1d4 Constitution for 1d6 rounds. Recalculates HP. Fortitude DC 10 negates.",
      "pt": "-1d4 de Constituição por 1d6 rodadas. Recalcula HP. Fortitude dif. 10 anula."
    },
    "ui.item.veneno_dor_escarlate.desc": {
      "en": "Fortitude DC 12 negates. On a failure, takes 1 point of damage per round for 1d6 rounds.",
      "pt": "Fortitude CD 12 anula. Se falhar, sofre 1 ponto de dano por rodada durante 1d6 rodadas."
    },
    "ui.item.veneno_escorpiao_pedra.desc": {
      "en": "-1 to attacks and -1 square of movement for 1d6 rounds. Fortitude DC 9 negates.",
      "pt": "-1 em ataques e -1 quadrado de movimento por 1d6 rodadas. Fortitude dif. 9 anula."
    },
    "ui.item.veneno_fungo_acre.desc": {
      "en": "Fortitude DC 10 negates. On a failure, takes 1 point of damage per round for 1d4 rounds.",
      "pt": "Fortitude CD 10 anula. Se falhar, sofre 1 ponto de dano por rodada durante 1d4 rodadas."
    },
    "ui.item.veneno_polvo_abissal.desc": {
      "en": "Blinds for 1d4 rounds — -4 to attacks, no ranged (Fort. DC 11). Partial failure: -2 perception.",
      "pt": "Falha em Fortitude CD 11: cego por 1d4 rodadas, visão 1 quadrado, -5 percepção, -4 em ataques e sem ataques à distância. Sucesso: -2 percepção por 1d4 rodadas."
    },
    "ui.item.vidro_acido_grande.desc": {
      "en": "Throw (4 sq., DEX attack). 2d6 acid + half on the next round. Corrodes the target's defence (−2 AC per hit).",
      "pt": "Arremesse (4 quad., ataque por DES). 2d6 de ácido + metade na rodada seguinte. Corrói a defesa do alvo (−2 CA por acerto)."
    },
    "ui.item.virotes_incendiarios.nome": {
      "en": "Incendiary Bolts (10)",
      "pt": "Virotes Incendiários (10)"
    },
    "ui.ladino.compre_formula": {
      "en": "🔒 Buy the formula at the Heroes' Guild",
      "pt": "🔒 Compre a fórmula na Guilda dos Heróis"
    },
    "ui.ladino.criar_armadilha_custo": {
      "en": "💰 {ouro} coins | 🍖-{fome} 💧-{sede} per trap",
      "pt": "💰 {ouro} moedas | 🍖-{fome} 💧-{sede} por criação"
    },
    "ui.ladino.criar_armadilha_titulo": {
      "en": "🪤 SET TRAP",
      "pt": "🪤 CRIAR ARMADILHA"
    },
    "ui.ladino.desarmar_desc": {
      "en": "DEX check{b} on your square or an adjacent one (nat 1 sets it off on you)",
      "pt": "Teste de DES{b} na casa/adjacente (nat1 dispara em você)"
    },
    "ui.ladino.desarmar_nome": {
      "en": "🔧 Disarm Trap",
      "pt": "🔧 Desarmar Armadilha"
    },
    "ui.ladino.dois_venenos": {
      "en": "up to 2 simultaneous poisons",
      "pt": "até 2 venenos simultâneos"
    },
    "ui.ladino.esconder_desc": {
      "en": "Stealth check{b} — bonus action",
      "pt": "Teste de furtividade{b} — ação bônus"
    },
    "ui.ladino.requer_veneno_falta": {
      "en": "⚠️ No poison in the inventory",
      "pt": "⚠️ Sem veneno no inventário"
    },
    "ui.ladino.requer_veneno_ok": {
      "en": "☠️ Requires poison — available",
      "pt": "☠️ Requer veneno — disponível"
    },
    "ui.ladino.sede_insuficiente": {
      "en": "❌ Not enough thirst 💧-1",
      "pt": "❌ Sede insuficiente 💧-1"
    },
    "ui.ladino.sem_venenos": {
      "en": "❌ No poisons in the inventory",
      "pt": "❌ Sem venenos no inventário"
    },
    "ui.ladino.veneno_opcional": {
      "en": "☠️ Poison optional",
      "pt": "☠️ Veneno opcional"
    },
    "ui.ladino.veneno_rapido_custo": {
      "en": "Free action | 💧-1 + consumes the vial",
      "pt": "Ação Livre | 💧-1 + consome o frasco"
    },
    "ui.ladino.veneno_rapido_titulo": {
      "en": "☠️ QUICK POISON",
      "pt": "☠️ VENENO RÁPIDO"
    },
    "ui.loja.aba.alimentos": {
      "en": "🍺 Food",
      "pt": "🍺 Alimentos"
    },
    "ui.loja.aba.armaduras": {
      "en": "🛡 Armour",
      "pt": "🛡 Armaduras"
    },
    "ui.loja.aba.armas": {
      "en": "⚔ Weapons",
      "pt": "⚔ Armas"
    },
    "ui.loja.aba.comprar": {
      "en": "🛒 Buy",
      "pt": "🛒 Comprar"
    },
    "ui.loja.aba.conversas": {
      "en": "Conversations",
      "pt": "Conversas"
    },
    "ui.loja.aba.instrumentos": {
      "en": "🎵 Instruments",
      "pt": "🎵 Instrumentos"
    },
    "ui.loja.aba.municao": {
      "en": "🏹 Ammunition",
      "pt": "🏹 Munição"
    },
    "ui.loja.aba.reparar": {
      "en": "🔧 Repair",
      "pt": "🔧 Reparar"
    },
    "ui.loja.aba.pergaminhos": {
      "en": "📜 Scrolls",
      "pt": "📜 Pergaminhos"
    },
    "ui.loja.aba.vender": {
      "en": "💰 Sell",
      "pt": "💰 Vender"
    },
    "ui.loja.aba.venenos": {
      "en": "☠️ Poisons",
      "pt": "☠️ Venenos"
    },
    "ui.loja.carregando": {
      "en": "Loading shop…",
      "pt": "Carregando loja…"
    },
    "ui.loja.classe_restrita": {
      "en": "Class restricted",
      "pt": "Classe restrita"
    },
    "ui.loja.comprar": {
      "en": "Buy",
      "pt": "Comprar"
    },
    "ui.loja.reparo.nivel": {
      "en": "Corrosion: {n} level(s)",
      "pt": "Corrosão: {n} nível(is)"
    },
    "ui.loja.reparo.equipado": {
      "en": "Equipped",
      "pt": "Equipado"
    },
    "ui.loja.reparo.bolsa": {
      "en": "Backpack",
      "pt": "Bolsa"
    },
    "ui.loja.reparo.custo_nivel": {
      "en": "{n} coin(s) per level",
      "pt": "{n} moeda(s) por nível"
    },
    "ui.loja.reparo.vazio": {
      "en": "No weapons, armour or shields need repair.",
      "pt": "Nenhuma arma, armadura ou escudo precisa de reparo."
    },
    "ui.loja.reparo.botao": {
      "en": "Repair all",
      "pt": "Reparar tudo"
    },
    "ui.loja.curar": {
      "en": "Cure",
      "pt": "Curar"
    },
    "ui.loja.desc_remover_maldicao": {
      "en": "Cures one curse; the price depends on its severity.",
      "pt": "Cura uma maldição; o preço depende da gravidade."
    },
    "ui.loja.escudo": {
      "en": "shield",
      "pt": "escudo"
    },
    "ui.loja.ja_usada": {
      "en": "already used this visit",
      "pt": "já usada nesta visita"
    },
    "ui.loja.log_inventario_cheio": {
      "en": "❌ {nome}: inventory full",
      "pt": "❌ {nome}: inventário cheio"
    },
    "ui.loja.log_ouro_insuficiente": {
      "en": "❌ {nome}: not enough gold",
      "pt": "❌ {nome}: ouro insuficiente"
    },
    "ui.loja.ouro": {
      "en": "💰 Gold:",
      "pt": "💰 Ouro:"
    },
    "ui.loja.remover_maldicao": {
      "en": "Remove: {nome}",
      "pt": "Remover: {nome}"
    },
    "ui.loja.restrito": {
      "en": "Restricted",
      "pt": "Restrito"
    },
    "ui.loja.subtitulo.ferreiro": {
      "en": "Buy and sell weapons, armour and ammunition.",
      "pt": "Compre e venda armas, armaduras e munição."
    },
    "ui.loja.subtitulo.mercador": {
      "en": "Potions, amulets and accessories to survive the dungeon.",
      "pt": "Poções, amuletos e acessórios para sobreviver na masmorra."
    },
    "ui.loja.subtitulo.taverna": {
      "en": "Rest, eat and drink before setting out on the adventure.",
      "pt": "Descanse, coma e beba antes de partir para a aventura."
    },
    "ui.loja.subtitulo.templo": {
      "en": "Receive divine blessings and heal your wounds.",
      "pt": "Receba bênçãos divinas e cure seus ferimentos."
    },
    "ui.loja.tag.acessorio": {
      "en": "Accessory",
      "pt": "Acessório"
    },
    "ui.loja.tag.arma_equipada": {
      "en": "Equipped weapon",
      "pt": "Arma equipada"
    },
    "ui.loja.tag.armadura_equipada": {
      "en": "Equipped armour",
      "pt": "Armadura equipada"
    },
    "ui.loja.tag.boots": {
      "en": "Boots",
      "pt": "Botas"
    },
    "ui.loja.tag.head": {
      "en": "Head",
      "pt": "Cabeça"
    },
    "ui.loja.tag.item1": {
      "en": "Item",
      "pt": "Item"
    },
    "ui.loja.tag.item2": {
      "en": "Item",
      "pt": "Item"
    },
    "ui.loja.tag.mochila": {
      "en": "Backpack",
      "pt": "Mochila"
    },
    "ui.loja.tag.off_hand": {
      "en": "Off hand",
      "pt": "Mão esquerda"
    },
    "ui.loja.tag.ring1": {
      "en": "Ring",
      "pt": "Anel"
    },
    "ui.loja.tag.ring2": {
      "en": "Ring",
      "pt": "Anel"
    },
    "ui.loja.title_classe_restrita": {
      "en": "Your class cannot use this item",
      "pt": "Sua classe não pode usar este item"
    },
    "ui.loja.title_ja_usada": {
      "en": "Already used on this visit to town",
      "pt": "Já usada nesta visita à cidade"
    },
    "ui.loja.titulo.ferreiro": {
      "en": "🔨 Blacksmith",
      "pt": "🔨 Ferreiro"
    },
    "ui.loja.titulo.mercador": {
      "en": "🛒 Merchant",
      "pt": "🛒 Mercador"
    },
    "ui.loja.titulo.taverna": {
      "en": "🍺 Tavern",
      "pt": "🍺 Taverna"
    },
    "ui.loja.titulo.templo": {
      "en": "⛪ Temple",
      "pt": "⛪ Templo"
    },
    "ui.loja.titulo_padrao": {
      "en": "Shop",
      "pt": "Loja"
    },
    "ui.loja.usada": {
      "en": "Used",
      "pt": "Usada"
    },
    "ui.loja.voltar_mapa": {
      "en": "← Back to the Map",
      "pt": "← Voltar ao Mapa"
    },
    "ui.magia.abencoar.desc": {
      "en": "<b>Area:</b> 6x6 centred on Lewis<br>\n               <b>Buff:</b> +1 attack, damage, AC, resistance<br>\n               <b>Duration:</b> 1d4+1 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Área:</b> 6x6 centrado em Lewis<br>\n               <b>Buff:</b> +1 ataque, dano, CA, resistência<br>\n               <b>Duração:</b> 1d4+1 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.abencoar_arma.desc": {
      "en": "<b>Range:</b> 6 squares<br>\n               <b>Buff:</b> +1 attack and damage on the weapon<br>\n               <b>Blessed weapon:</b> ignores reductions, halved damage and physical immunity<br>\n               <b>Duration:</b> 1d6+2 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Alcance:</b> 6 quadrados<br>\n               <b>Buff:</b> +1 ataque e dano na arma<br>\n               <b>Arma abençoada:</b> ignora reduções, dano pela metade e imunidade física<br>\n               <b>Duração:</b> 1d6+2 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.aliado_invalido": {
      "en": "Click a valid ally.",
      "pt": "Clique num aliado válido."
    },
    "ui.magia.amaldicoar.desc": {
      "en": "<b>Area:</b> 3x3 centred on the target<br>\n               <b>Debuff:</b> -1 attack, damage, AC, resistance<br>\n               <b>Duration:</b> 1d4+1 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Área:</b> 3x3 centrado no alvo<br>\n               <b>Debuff:</b> -1 ataque, dano, CA, resistência<br>\n               <b>Duração:</b> 1d4+1 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.barreira_arcana.desc": {
      "en": "<b>Effect:</b> reduces all incoming damage by 5<br>\n               <b>Duration:</b> 1d6 + 1 round per mage level + 1 fixed round<br>\n               <b>Extend:</b> +1 round<br>\n               <b>Empower:</b> reduction becomes 7<br>\n               <b>Heighten:</b> does not apply (no saving throw)",
      "pt": "<b>Efeito:</b> reduz 5 de todo dano recebido<br>\n               <b>Duração:</b> 1d6 + 1 rodada por nível do mago + 1 rodada fixa<br>\n               <b>Estender:</b> +1 rodada<br>\n               <b>Fortalecer:</b> redução passa a 7<br>\n               <b>Aprimorar:</b> não se aplica (sem teste de resistência)"
    },
    "ui.magia.bola_fogo.desc": {
      "en": "<b>Range:</b> 5 squares<br>\n               <b>Area:</b> 3×3, centred on the chosen point<br>\n               <b>R1:</b> 1d6 per level | Reflex: half<br>\n               <b>R2:</b> half of the R1 damage<br>\n               <b>R3:</b> half of the R2 damage (Extend: +1 residual round)<br>\n               <b>Area persists:</b> entering takes damage, leaving avoids further<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Alcance:</b> 5 casas<br>\n               <b>Área:</b> 3×3, centrada no ponto escolhido<br>\n               <b>R1:</b> 1d6 por nível | Reflexos: metade<br>\n               <b>R2:</b> metade do dano R1<br>\n               <b>R3:</b> metade do dano R2 (Estender: +1 rodada residual)<br>\n               <b>Área persiste:</b> entrar sofre dano, sair evita futuro<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.circulo.primeiro": {
      "en": "1st Circle",
      "pt": "1º Círculo"
    },
    "ui.magia.circulo.segundo": {
      "en": "2nd Circle",
      "pt": "2º Círculo"
    },
    "ui.magia.circulo.terceiro": {
      "en": "3rd Circle",
      "pt": "3º Círculo"
    },
    "ui.magia.circulo_caixa.primeiro": {
      "en": "1ST CIRCLE",
      "pt": "1º CÍRCULO"
    },
    "ui.magia.circulo_caixa.segundo": {
      "en": "2ND CIRCLE",
      "pt": "2º CÍRCULO"
    },
    "ui.magia.circulo_caixa.terceiro": {
      "en": "3RD CIRCLE",
      "pt": "3º CÍRCULO"
    },
    "ui.magia.clarividencia.desc": {
      "en": "<b>Range:</b> the whole map (aim anywhere)<br>\n               <b>Area:</b> 4x4 (scales with level)<br>\n               <b>Effect:</b> reveals the fog, the monsters and the traps there<br>\n               <b>Duration:</b> 2 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Alcance:</b> o mapa inteiro (mire em qualquer lugar)<br>\n               <b>Área:</b> 4x4 (escala com nível)<br>\n               <b>Efeito:</b> revela a névoa, os monstros e as armadilhas do local<br>\n               <b>Duração:</b> 2 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.comando.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Target:</b> 1 monster (constructs, undead and those immune to enchantment resist)<br>\n               <b>Fail:</b> on its next turn, YOU direct the monster — movement, main action, abilities and items<br>\n               <b>Duration:</b> 1 turn<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Alvo:</b> 1 monstro (construtos, mortos-vivos e imunes a encantamento resistem)<br>\n               <b>Falha:</b> no próximo turno dele, VOCÊ dirige o monstro — movimento, ação principal, habilidades e itens<br>\n               <b>Duração:</b> 1 turno<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.conhecidas": {
      "en": "KNOWN SPELLS",
      "pt": "MAGIAS CONHECIDAS"
    },
    "ui.magia.conjurar_elemental.desc": {
      "en": "<b>Types:</b> Fire (HP18 2d6), Lightning (HP20 line),\n               Ice (HP22 -2phys), Stone (HP26 ½phys)<br>\n               <b>Control:</b> acts after Lewis, 6 sq. movement<br>\n               <b>⚠️ The blast hits allies",
      "pt": "<b>Tipos:</b> Fogo (HP18 2d6), Elétrico (HP20 linha),\n               Gelo (HP22 -2fís), Pedra (HP26 ½fís)<br>\n               <b>Controle:</b> age após Lewis, 6 quad. movimento<br>\n               <b>⚠️ Explosão afeta aliados"
    },
    "ui.magia.contramagica.desc": {
      "en": "<b>Type:</b> Reaction (off-turn)<br>\n               <b>Mechanic:</b> d20+INT vs the enemy's d20+bonus<br>\n               <b>Success:</b> spell cancelled + enemy loses its action<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot on use",
      "pt": "<b>Tipo:</b> Reação (fora do turno)<br>\n               <b>Mecânica:</b> d20+INT vs inimigo d20+bônus<br>\n               <b>Sucesso:</b> magia cancelada + inimigo perde ação<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot ao usar"
    },
    "ui.magia.criar_alimentos.desc": {
      "en": "<b>Creates:</b> a chest on a free adjacent square<br>\n               <b>Contents:</b> 1d4+2 random tavern foods<br>\n               <b>Empower:</b> multiplies the final item count<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Cria:</b> baú em uma casa adjacente livre<br>\n               <b>Conteúdo:</b> 1d4+2 alimentos aleatórios da taverna<br>\n               <b>Fortalecer:</b> multiplica a quantidade final de itens<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.dica.adjacent_tile": {
      "en": "Click an adjacent GREEN SQUARE to create the chest",
      "pt": "Clique numa CASA VERDE adjacente para criar o baú"
    },
    "ui.magia.dica.ally": {
      "en": "Click an ALLY (or yourself)",
      "pt": "Clique num ALIADO (ou em você)"
    },
    "ui.magia.dica.cone": {
      "en": "Click a SQUARE (direction of the cone)",
      "pt": "Clique numa CASA (direção do cone)"
    },
    "ui.magia.dica.foe": {
      "en": "Click an ENEMY",
      "pt": "Clique num INIMIGO"
    },
    "ui.magia.dica.linha": {
      "en": "Click a SQUARE (direction of the bolt)",
      "pt": "Clique numa CASA (direção do raio)"
    },
    "ui.magia.dica.self_area": {
      "en": "Click to CONFIRM (area on you)",
      "pt": "Clique para CONFIRMAR (área em você)"
    },
    "ui.magia.dica.tile": {
      "en": "Click a SQUARE (centre of the area)",
      "pt": "Clique numa CASA (centro da área)"
    },
    "ui.magia.dica_padrao": {
      "en": "Click the target",
      "pt": "Clique no alvo"
    },
    "ui.magia.dominar_mente.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Target:</b> 1 monster (constructs, undead and those immune to enchantment resist)<br>\n               <b>Fail:</b> YOU direct the monster on each of its turns for 1d4+1 rounds<br>\n               <b>New save:</b> each point of damage taken gives a cumulative +2 on the next Will; passing breaks the control<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Alvo:</b> 1 monstro (construtos, mortos-vivos e imunes a encantamento resistem)<br>\n               <b>Falha:</b> VOCÊ dirige o monstro a cada turno dele por 1d4+1 rodadas<br>\n               <b>Novo teste:</b> cada dano sofrido dá +2 cumulativo na próxima Vontade; passar rompe o controle<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.dominar_morto_vivo.desc": {
      "en": "<b>Requires:</b> an undead target<br>\n               <b>Save:</b> Will (bonus = CR) on casting and every round<br>\n               <b>Fail:</b> becomes a temporary servant (acts in the servants' phase)<br>\n               <b>3 fails in a row:</b> PERMANENT control<br>\n               <b>Passing:</b> breaks the control (turns hostile again) — recast<br>\n               <b>Single slot</b> · does not count towards Animate Dead",
      "pt": "<b>Requer:</b> alvo do tipo morto-vivo<br>\n               <b>Save:</b> Vontade (bônus = ND) ao lançar e a cada rodada<br>\n               <b>Falha:</b> vira servo temporário (age na fase dos servos)<br>\n               <b>3 falhas seguidas:</b> controle PERMANENTE<br>\n               <b>Passar:</b> quebra o controle (volta hostil) — relançar<br>\n               <b>Slot único</b> · não conta para Animar Mortos"
    },
    "ui.magia.em_desenvolvimento": {
      "en": "{icone} {nome} is still in development.",
      "pt": "{icone} {nome} ainda está em desenvolvimento."
    },
    "ui.magia.esc_cancela": {
      "en": "ESC cancels",
      "pt": "ESC cancela"
    },
    "ui.magia.escolha_1_do_circulo": {
      "en": "Choose 1 spell of the {circulo} circle",
      "pt": "Escolha 1 magia de {circulo} círculo"
    },
    "ui.magia.escolha_1_magia": {
      "en": "CHOOSE {n} SPELL OF THE 1ST CIRCLE",
      "pt": "ESCOLHA {n} MAGIA DE 1º CÍRCULO"
    },
    "ui.magia.escolha_n_magias": {
      "en": "CHOOSE {n} SPELLS OF THE 1ST CIRCLE",
      "pt": "ESCOLHA {n} MAGIAS DE 1º CÍRCULO"
    },
    "ui.magia.ficha_indisponivel": {
      "en": "Spell sheet unavailable right now.",
      "pt": "Ficha de magias indisponível agora."
    },
    "ui.magia.fora_de_alcance": {
      "en": "🚫 Out of range — max {n} square(s).",
      "pt": "🚫 Fora de alcance — máximo {n} casa(s)."
    },
    "ui.magia.grimorio": {
      "en": "GRIMOIRE",
      "pt": "GRIMÓRIO"
    },
    "ui.magia.inimigo_invalido": {
      "en": "Click a valid enemy.",
      "pt": "Clique num inimigo válido."
    },
    "ui.magia.invisibilidade.desc": {
      "en": "<b>Effect:</b> enemies cannot attack you<br>\n               <b>Attack:</b> with advantage (higher of 2d20) + sneak<br>\n               <b>Breaks:</b> on attacking or casting a spell<br>\n               <b>Duration:</b> 1d6+1 rounds",
      "pt": "<b>Efeito:</b> inimigos não podem atacar<br>\n               <b>Ataque:</b> com vantagem (2d20 maior) + furtivo<br>\n               <b>Quebra:</b> ao atacar ou lançar magia<br>\n               <b>Duração:</b> 1d6+1 rodadas"
    },
    "ui.magia.jato_ar.desc": {
      "en": "<b>Cone:</b> 4 squares long, 4 wide at the base<br>\n               <b>Damage:</b> 1d6 per level<br>\n               <b>Failed Reflex:</b> pushes 1d6 squares<br>\n               <b>Success:</b> pushes 2 squares<br>\n               <b>Wall collision:</b> +1d4 damage",
      "pt": "<b>Cone:</b> 4 quadrados comp., 4 base<br>\n               <b>Dano:</b> 1d6 por nível<br>\n               <b>Falha Reflexos:</b> empurra 1d6 quadrados<br>\n               <b>Sucesso:</b> empurra 2 quadrados<br>\n               <b>Colisão parede:</b> +1d4 dano"
    },
    "ui.magia.lancada": {
      "en": "{icone} {nome} cast!",
      "pt": "{icone} {nome} lançada!"
    },
    "ui.magia.lentidao.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Fail:</b> 1 action/round, no reaction, -1 AC<br>\n               <b>Success:</b> movement ÷2, -1 attack<br>\n               <b>Duration:</b> 1d4 rounds",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Falha:</b> 1 ação/rodada, sem reação, -1 CA<br>\n               <b>Sucesso:</b> movimento ÷2, -1 ataque<br>\n               <b>Duração:</b> 1d4 rodadas"
    },
    "ui.magia.magias_iniciais": {
      "en": "STARTING SPELLS",
      "pt": "MAGIAS INICIAIS"
    },
    "ui.magia.manto_escuridao.desc": {
      "en": "<b>Radius:</b> 3 squares centred on the caster<br>\n               <b>Without night vision:</b> attacks roll 2d20 and use the lower<br>\n               <b>With night vision:</b> 2d20 uses the higher vs the blinded<br>\n               <b>Caster:</b> gains darkvision for the cloak's duration<br>\n               <b>Maximum ranged distance:</b> 2 squares<br>\n               <b>Duration:</b> 1d4 rounds",
      "pt": "<b>Raio:</b> 3 quadrados centrado no caster<br>\n               <b>Sem visão noturna:</b> 2d20 usa menor nos ataques<br>\n               <b>Com visão noturna:</b> 2d20 usa maior vs cegos<br>\n               <b>Conjurador:</b> recebe visão no escuro pela duração do manto<br>\n               <b>Distância máxima à distância:</b> 2 quadrados<br>\n               <b>Duração:</b> 1d4 rodadas"
    },
    "ui.magia.medo.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Fail:</b> flees for 1d4+1 rounds<br>\n               <b>Effects:</b> -1 attack, will not approach<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Falha:</b> foge 1d4+1 rodadas<br>\n               <b>Efeitos:</b> -1 ataque, não se aproxima<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.menu_aria": {
      "en": "Spell menu",
      "pt": "Menu de magias"
    },
    "ui.magia.mire_direcao": {
      "en": "Aim in a direction from yourself.",
      "pt": "Mire numa direção a partir de você."
    },
    "ui.magia.modificadores": {
      "en": "SPELL MODIFIERS",
      "pt": "MODIFICADORES DE MAGIA"
    },
    "ui.magia.n_selecionadas": {
      "en": "{n}/{max} spells selected",
      "pt": "{n}/{max} magias selecionadas"
    },
    "ui.magia.nenhuma_conhecida": {
      "en": "No spell known.",
      "pt": "Nenhuma magia conhecida."
    },
    "ui.magia.nenhuma_disponivel": {
      "en": "No spell available",
      "pt": "Nenhuma magia disponível"
    },
    "ui.magia.ordinal.primeiro": {
      "en": "1st",
      "pt": "1º"
    },
    "ui.magia.ordinal.segundo": {
      "en": "2nd",
      "pt": "2º"
    },
    "ui.magia.ordinal.terceiro": {
      "en": "3rd",
      "pt": "3º"
    },
    "ui.magia.parede_bloqueia": {
      "en": "🧱 A wall blocks the spell to the target!",
      "pt": "🧱 Uma parede bloqueia o feitiço até o alvo!"
    },
    "ui.magia.protecao_energia.desc": {
      "en": "<b>Protection:</b> 10 points/round of elemental damage<br>\n               <b>Types:</b> fire, ice, lightning, acid, water or holy<br>\n               <b>Duration:</b> 1d6+1 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Proteção:</b> 10 pontos/rodada de dano elemental<br>\n               <b>Tipos:</b> fogo, gelo, eletricidade, ácido, água ou sagrado<br>\n               <b>Duração:</b> 1d6+1 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.raio_congelante.desc": {
      "en": "<b>Range:</b> 3 +1 per level<br>\n               <b>Damage:</b> 3d4 +2d4 every 2 levels<br>\n               <b>⚠️ No Reflex save:</b> damage is always full<br>\n               <b>Fortitude:</b> fail → paralysed for 1 round<br>\n               <b>Next round:</b> new Fortitude save<br>\n               <b>Success:</b> acts normally<br>\n               <b>Fail:</b> 1 more round (max 2)",
      "pt": "<b>Alcance:</b> 3 +1 por nível<br>\n               <b>Dano:</b> 3d4 +2d4 a cada 2 níveis<br>\n               <b>⚠️ Sem Reflexos:</b> dano sempre total<br>\n               <b>Fortitude:</b> falha → paralisado 1 rodada<br>\n               <b>Rodada seguinte:</b> novo Fortitude<br>\n               <b>Sucesso:</b> age normalmente<br>\n               <b>Falha:</b> mais 1 rodada (máx 2)"
    },
    "ui.magia.raio_divino.desc": {
      "en": "<b>Damage:</b> 1d6+1 per character level<br>\n               <b>Save:</b> Reflex → half<br>\n               <b>Vs undead/demons:</b> damage doubled<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Dano:</b> 1d6+1 por nível do personagem<br>\n               <b>Save:</b> Reflexos → metade<br>\n               <b>Vs mortos-vivos/demônios:</b> dano dobrado<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.regeneracao_magica.desc": {
      "en": "<b>Pool:</b> 2d6+2 regeneration points<br>\n               <b>Healing:</b> +1 HP at the start of the target's turn<br>\n               <b>If it dies:</b> comes back with 1 HP (-3 hunger/thirst)<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Pool:</b> 2d6+2 pontos de regeneração<br>\n               <b>Cura:</b> +1 HP no início do turno do alvo<br>\n               <b>Se morrer:</b> volta com 1 HP (-3 fome/sede)<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.relampago.desc": {
      "en": "<b>Range:</b> 4 squares in a straight line (+1 per level)<br>\n               <b>Damage:</b> 1d6 per level per hit<br>\n               <b>Ricochet:</b> returns along the same path — squares hit twice (dark green)<br>\n               <b>Save:</b> Reflex → half per hit<br>\n               <b>⚠️ Pedro is only hurt on the way back; it can hurt allies</b><br>\n               <b>Extend Spell:</b> does not apply (instantaneous effect)",
      "pt": "<b>Alcance:</b> 4 casas em linha reta (+1 por nível)<br>\n               <b>Dano:</b> 1d6 por nível por impacto<br>\n               <b>Ricochete:</b> volta pelo mesmo trajeto — casas atingidas 2x (verde escuro)<br>\n               <b>Save:</b> Reflexos → metade por impacto<br>\n               <b>⚠️ Pedro só é ferido na volta; pode ferir aliados</b><br>\n               <b>Estender Magia:</b> não se aplica (efeito instantâneo)"
    },
    "ui.magia.saciar.desc": {
      "en": "<b>Range:</b> adjacent<br>\n               <b>Effect:</b> +20 hunger and +20 thirst<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Alcance:</b> adjacente<br>\n               <b>Efeito:</b> +20 fome e +20 sede<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.sem_magias": {
      "en": "This character has no spells.",
      "pt": "Este personagem não possui magias."
    },
    "ui.magia.sem_modificadores": {
      "en": "No spell modifier available.",
      "pt": "Nenhum modificador de magia disponível."
    },
    "ui.magia.sem_slot": {
      "en": "no slot available",
      "pt": "sem slot disponível"
    },
    "ui.magia.silencio.desc": {
      "en": "<b>Area:</b> 4x4 centred on the point<br>\n               <b>Effect:</b> spells do not work inside the area<br>\n               <b>Duration:</b> 1d4+1 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Área:</b> 4x4 centrado no ponto<br>\n               <b>Efeito:</b> magias não funcionam na área<br>\n               <b>Duração:</b> 1d4+1 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.slot_disponivel": {
      "en": "Slot available",
      "pt": "Slot disponível"
    },
    "ui.magia.slot_nivel_maior": {
      "en": "Available at a higher level",
      "pt": "Disponível em nível maior"
    },
    "ui.magia.slot_volta_em": {
      "en": "Back in {n} round(s)",
      "pt": "Volta em {n} rodada(s)"
    },
    "ui.magia.slots_aria": {
      "en": "Spell slots",
      "pt": "Slots de magias"
    },
    "ui.magia.slots_disponiveis": {
      "en": "{livres}/{total} available",
      "pt": "{livres}/{total} disponíveis"
    },
    "ui.magia.slots_recarga": {
      "en": "Recharge per circle",
      "pt": "Recarga por círculo"
    },
    "ui.magia.slots_titulo": {
      "en": "SPELL SLOTS",
      "pt": "SLOTS DE MAGIAS"
    },
    "ui.magia.so_na_masmorra": {
      "en": "Spells can only be used in the dungeon.",
      "pt": "Magias só podem ser usadas na masmorra."
    },
    "ui.magia.sono.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Fail:</b> sleeps for 1d4+1 rounds<br>\n               <b>Bonus:</b> 1st attack against a sleeping target = critical<br>\n               <b>Wakes:</b> on taking any damage<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Falha:</b> dorme 1d4+1 rodadas<br>\n               <b>Bônus:</b> 1º ataque contra dormindo = crítico<br>\n               <b>Acorda:</b> ao receber qualquer dano<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.subiu_de_nivel": {
      "en": "LEVEL UP",
      "pt": "SUBIU DE NÍVEL"
    },
    "ui.magia.tecla_m": {
      "en": "M key",
      "pt": "tecla M"
    },
    "ui.magia.velocidade.desc": {
      "en": "<b>Effect:</b> every action is doubled<br>\n               <b>Cost:</b> each action still costs hunger/thirst<br>\n               <b>Duration:</b> 1d4 rounds",
      "pt": "<b>Efeito:</b> todas as ações são dobradas<br>\n               <b>Custo:</b> cada ação ainda custa fome/sede<br>\n               <b>Duração:</b> 1d4 rodadas"
    },
    "ui.magia.visao_escuro.desc": {
      "en": "<b>Effect:</b> ignores the darkness system entirely<br>\n               <b>Duration:</b> until you leave the dungeon<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Efeito:</b> ignora completamente o sistema de escuridão<br>\n               <b>Duração:</b> até sair da masmorra<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.maldicao.alma_quebrada": {
      "en": "Broken Soul",
      "pt": "Alma Quebrada"
    },
    "ui.maldicao.alma_quebrada.ef": {
      "en": "receives no bonuses from allies",
      "pt": "não recebe bônus de aliados"
    },
    "ui.maldicao.ativa": {
      "en": "curse active",
      "pt": "maldição ativa"
    },
    "ui.maldicao.aura_profana": {
      "en": "Profane Aura",
      "pt": "Aura Profana"
    },
    "ui.maldicao.aura_profana.ef": {
      "en": "adjacent allies get −1 attack",
      "pt": "aliados adjacentes −1 ataque"
    },
    "ui.maldicao.azar_sobrenatural": {
      "en": "Supernatural Misfortune",
      "pt": "Azar Sobrenatural"
    },
    "ui.maldicao.azar_sobrenatural.ef": {
      "en": "the first natural 20 is not a critical",
      "pt": "primeiro 20 natural não é crítico"
    },
    "ui.maldicao.carne_fragil": {
      "en": "Fragile Flesh",
      "pt": "Carne Frágil"
    },
    "ui.maldicao.carne_fragil.ef": {
      "en": "+2 damage taken",
      "pt": "+2 dano recebido"
    },
    "ui.maldicao.corpo_exausto": {
      "en": "Exhausted Body",
      "pt": "Corpo Exausto"
    },
    "ui.maldicao.corpo_exausto.ef": {
      "en": "actions cost +1 hunger and thirst",
      "pt": "ações custam +1 fome e sede"
    },
    "ui.maldicao.correntes_invisiveis": {
      "en": "Invisible Chains",
      "pt": "Correntes Invisíveis"
    },
    "ui.maldicao.correntes_invisiveis.ef": {
      "en": "−3 movement",
      "pt": "−3 movimento"
    },
    "ui.maldicao.corrupcao_crescente": {
      "en": "Growing Corruption",
      "pt": "Corrupção Crescente"
    },
    "ui.maldicao.dor_constante": {
      "en": "Constant Pain",
      "pt": "Dor Constante"
    },
    "ui.maldicao.dor_constante.ef": {
      "en": "actions deal 1 damage to you",
      "pt": "ações causam 1 dano"
    },
    "ui.maldicao.eco_morte": {
      "en": "Echo of Death",
      "pt": "Eco da Morte"
    },
    "ui.maldicao.eco_morte.ef": {
      "en": "an ally's death deals 10 damage",
      "pt": "morte de aliado causa 10 dano"
    },
    "ui.maldicao.espirito_covarde": {
      "en": "Cowardly Spirit",
      "pt": "Espírito Covarde"
    },
    "ui.maldicao.espirito_covarde.ef": {
      "en": "−2 Will",
      "pt": "−2 Vontade"
    },
    "ui.maldicao.estagio": {
      "en": "(stage {n})",
      "pt": "(estágio {n})"
    },
    "ui.maldicao.fome_eterna": {
      "en": "Eternal Hunger",
      "pt": "Fome Eterna"
    },
    "ui.maldicao.fortuna_roubada": {
      "en": "Stolen Fortune",
      "pt": "Fortuna Roubada"
    },
    "ui.maldicao.fortuna_roubada.ef": {
      "en": "half the gold acquired",
      "pt": "metade do ouro adquirido"
    },
    "ui.maldicao.fraqueza_arcana": {
      "en": "Arcane Weakness",
      "pt": "Fraqueza Arcana"
    },
    "ui.maldicao.fraqueza_arcana.ef": {
      "en": "spells deal half damage",
      "pt": "magias causam metade do dano"
    },
    "ui.maldicao.lamina_enferrujada": {
      "en": "Rusted Blade",
      "pt": "Lâmina Enferrujada"
    },
    "ui.maldicao.lamina_enferrujada.ef": {
      "en": "−2 physical damage",
      "pt": "−2 dano físico"
    },
    "ui.maldicao.licantropia": {
      "en": "Lycanthropy",
      "pt": "Licantropia"
    },
    "ui.maldicao.maldicao_ferrugem": {
      "en": "Curse of Rust",
      "pt": "Maldição da Ferrugem"
    },
    "ui.maldicao.maldicao_ferrugem.ef": {
      "en": "equipment degrades after combat",
      "pt": "equipamento degrada após combate"
    },
    "ui.maldicao.maos_tremulas": {
      "en": "Trembling Hands",
      "pt": "Mãos Trêmulas"
    },
    "ui.maldicao.maos_tremulas.ef": {
      "en": "−2 on attacks",
      "pt": "−2 em ataques"
    },
    "ui.maldicao.marca_cacador": {
      "en": "Hunter's Mark",
      "pt": "Marca do Caçador"
    },
    "ui.maldicao.marca_cacador.ef": {
      "en": "enemies get +1 to attack you",
      "pt": "inimigos +1 para atacar você"
    },
    "ui.maldicao.olhos_escuridao": {
      "en": "Eyes of Darkness",
      "pt": "Olhos da Escuridão"
    },
    "ui.maldicao.olhos_escuridao.ef": {
      "en": "−2 vision",
      "pt": "−2 visão"
    },
    "ui.maldicao.passos_pesados": {
      "en": "Heavy Steps",
      "pt": "Passos Pesados"
    },
    "ui.maldicao.passos_pesados.ef": {
      "en": "moving costs +1 thirst",
      "pt": "mover custa +1 sede"
    },
    "ui.maldicao.sangramento_profano": {
      "en": "Profane Bleeding",
      "pt": "Sangramento Profano"
    },
    "ui.maldicao.sangramento_profano.ef": {
      "en": "1 damage at the start of your turn after taking damage",
      "pt": "1 dano no início do turno após sofrer dano"
    },
    "ui.maldicao.sede_infinita": {
      "en": "Endless Thirst",
      "pt": "Sede Infinita"
    },
    "ui.maldicao.silencio_deuses": {
      "en": "Silence of the Gods",
      "pt": "Silêncio dos Deuses"
    },
    "ui.maldicao.silencio_deuses.ef": {
      "en": "cannot cast spells",
      "pt": "não lança magias"
    },
    "ui.maldicao.tocado_morte": {
      "en": "Death-Touched",
      "pt": "Tocado pela Morte"
    },
    "ui.maldicao.voz_quebrada": {
      "en": "Broken Voice",
      "pt": "Voz Quebrada"
    },
    "ui.maldicao.voz_quebrada.ef": {
      "en": "cannot use Songs",
      "pt": "não usa Canções"
    },
    "ui.mestre.acao": {
      "en": "⚡ ACTION",
      "pt": "⚡ AÇÃO"
    },
    "ui.mestre.acao_gasta": {
      "en": "action already used",
      "pt": "ação já gasta"
    },
    "ui.mestre.acao_tipo.acao": {
      "en": "action",
      "pt": "ação"
    },
    "ui.mestre.acao_tipo.acao_livre": {
      "en": "free",
      "pt": "livre"
    },
    "ui.mestre.acao_tipo.magia": {
      "en": "spell",
      "pt": "magia"
    },
    "ui.mestre.acao_tipo.passiva": {
      "en": "passive",
      "pt": "passiva"
    },
    "ui.mestre.alcance_n": {
      "en": "range {n}",
      "pt": "alcance {n}"
    },
    "ui.mestre.alcance_q": {
      "en": "range {n}sq",
      "pt": "alcance {n}q"
    },
    "ui.mestre.arte_3d": {
      "en": "🔎 3D art (models and images)",
      "pt": "🔎 Arte 3D (modelos e imagens)"
    },
    "ui.mestre.ataque": {
      "en": "Attack",
      "pt": "Ataque"
    },
    "ui.mestre.ataques": {
      "en": "ATTACKS",
      "pt": "ATAQUES"
    },
    "ui.mestre.atributos_resistencias": {
      "en": "ATTRIBUTES AND SAVES",
      "pt": "ATRIBUTOS E RESISTÊNCIAS"
    },
    "ui.mestre.bonus": {
      "en": "✨ BONUS",
      "pt": "✨ BÔNUS"
    },
    "ui.mestre.caract_linha": {
      "en": "AI: {ia} · size {tam} · XP {xp} · gold {ouro}",
      "pt": "IA: {ia} · tamanho {tam} · XP {xp} · ouro {ouro}"
    },
    "ui.mestre.caracteristicas": {
      "en": "TRAITS",
      "pt": "CARACTERÍSTICAS"
    },
    "ui.mestre.clique_criatura_valida": {
      "en": "Click a valid creature inside the red squares.",
      "pt": "Clique numa criatura válida dentro dos quadrados vermelhos."
    },
    "ui.mestre.clique_implantar": {
      "en": "Click a free square to deploy (Esc cancels)",
      "pt": "Clique numa casa livre para implantar (Esc cancela)"
    },
    "ui.mestre.conjurador_nivel": {
      "en": "caster level {n}",
      "pt": "conjurador nível {n}"
    },
    "ui.mestre.corpo_a_corpo": {
      "en": "melee",
      "pt": "corpo a corpo"
    },
    "ui.mestre.cr_medio": {
      "en": "average CR",
      "pt": "CR médio"
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
    "ui.mestre.defesas": {
      "en": "BESTIARY DEFENCES",
      "pt": "DEFESAS DO BESTIÁRIO"
    },
    "ui.mestre.diagnostico": {
      "en": "DIAGNOSTICS",
      "pt": "DIAGNÓSTICO"
    },
    "ui.mestre.escolha_alvo": {
      "en": "{nome} — Choose the target",
      "pt": "{nome} — Escolha o alvo"
    },
    "ui.mestre.falas": {
      "en": "LINES",
      "pt": "FALAS"
    },
    "ui.mestre.ficha_de": {
      "en": "{nome}'s sheet",
      "pt": "Ficha de {nome}"
    },
    "ui.mestre.fraquezas": {
      "en": "Weaknesses",
      "pt": "Fraquezas"
    },
    "ui.mestre.gastam_acao": {
      "en": "— they use the action",
      "pt": "— gastam a ação"
    },
    "ui.mestre.habilidades": {
      "en": "ABILITIES",
      "pt": "HABILIDADES"
    },
    "ui.mestre.habilidades_titulo": {
      "en": "Abilities",
      "pt": "Habilidades"
    },
    "ui.mestre.ia_apenas": {
      "en": "AI only",
      "pt": "IA apenas"
    },
    "ui.mestre.ia_padrao": {
      "en": "default",
      "pt": "padrão"
    },
    "ui.mestre.implantacao_cancelada": {
      "en": "Deployment cancelled.",
      "pt": "Implantação cancelada."
    },
    "ui.mestre.imunidades": {
      "en": "Immunities",
      "pt": "Imunidades"
    },
    "ui.mestre.magias": {
      "en": "SPELLS",
      "pt": "MAGIAS"
    },
    "ui.mestre.magias_disponiveis": {
      "en": "AVAILABLE SPELLS",
      "pt": "MAGIAS DISPONÍVEIS"
    },
    "ui.mestre.magias_habilidades": {
      "en": "SPELLS AND ABILITIES",
      "pt": "MAGIAS E HABILIDADES"
    },
    "ui.mestre.magias_monstro": {
      "en": "✦ MONSTER SPELLS",
      "pt": "✦ MAGIAS DO MONSTRO"
    },
    "ui.mestre.mapa_cr": {
      "en": "🗺️ CR Map",
      "pt": "🗺️ Mapa de CR"
    },
    "ui.mestre.metade_dano": {
      "en": "half damage",
      "pt": "metade do dano"
    },
    "ui.mestre.minimapa_indisponivel": {
      "en": "Minimap unavailable.",
      "pt": "Minimapa indisponível."
    },
    "ui.mestre.mira_legenda": {
      "en": "{icone} {rotulo} — click a red square | ESC cancels",
      "pt": "{icone} {rotulo} — clique numa casa vermelha | ESC cancela"
    },
    "ui.mestre.monstro": {
      "en": "Monster",
      "pt": "Monstro"
    },
    "ui.mestre.monstro_sem_habilidades": {
      "en": "This monster has no abilities.",
      "pt": "Este monstro não possui habilidades."
    },
    "ui.mestre.monstro_sem_magias": {
      "en": "This monster has no spells.",
      "pt": "Este monstro não possui magias."
    },
    "ui.mestre.movimento": {
      "en": "👣 MOVEMENT",
      "pt": "👣 MOVIMENTO"
    },
    "ui.mestre.nao_implementada": {
      "en": "not implemented",
      "pt": "não implementada"
    },
    "ui.mestre.nd_nivel": {
      "en": "CR {nd} · level {nivel}",
      "pt": "ND {nd} · nível {nivel}"
    },
    "ui.mestre.percepcao_nota": {
      "en": "sheet base · +1 per living ally within 3 squares during stealth",
      "pt": "base da ficha · +1 por aliado vivo a até 3 casas durante furtividade"
    },
    "ui.mestre.poder_preview": {
      "en": "power {n} · player preview:",
      "pt": "poder {n} · preview jogadores:"
    },
    "ui.mestre.porte": {
      "en": "SIZE",
      "pt": "PORTE"
    },
    "ui.mestre.porte_medio": {
      "en": "medium",
      "pt": "médio"
    },
    "ui.mestre.reducao": {
      "en": "reduction {n}",
      "pt": "redução {n}"
    },
    "ui.mestre.reforcos": {
      "en": "REINFORCEMENTS",
      "pt": "REFORÇOS"
    },
    "ui.mestre.resistencias": {
      "en": "Resistances",
      "pt": "Resistências"
    },
    "ui.mestre.sem_alvo_adj": {
      "en": "No adjacent target.",
      "pt": "Nenhum alvo adjacente."
    },
    "ui.mestre.sem_alvo_monstro": {
      "en": "No monster available as a target.",
      "pt": "Nenhum monstro disponível como alvo."
    },
    "ui.mestre.sem_alvo_raio": {
      "en": "No target within {n}sq.",
      "pt": "Nenhum alvo a até {n}q."
    },
    "ui.mestre.sem_ataque": {
      "en": "No attack registered.",
      "pt": "Nenhum ataque cadastrado."
    },
    "ui.mestre.sem_habilidade": {
      "en": "No ability.",
      "pt": "Nenhuma habilidade."
    },
    "ui.mestre.sem_heroi_vivo": {
      "en": "No living hero.",
      "pt": "Nenhum herói vivo."
    },
    "ui.mestre.sem_magia": {
      "en": "No spell.",
      "pt": "Nenhuma magia."
    },
    "ui.mestre.sem_reforcos": {
      "en": "No reinforcements or lines in this dungeon.",
      "pt": "Sem reforços nem falas nesta masmorra."
    },
    "ui.metamagia.aprimorar": {
      "en": "Free action. +{n} to the spell's saving throw DC.",
      "pt": "Ação livre. +{n} na CD do teste de resistência da magia."
    },
    "ui.metamagia.armadas": {
      "en": "Metamagics armed. Choose the spell and the target manually.",
      "pt": "Metamagias armadas. Escolha a magia e o alvo manualmente."
    },
    "ui.metamagia.empilha_ate": {
      "en": "(stacks up to {n})",
      "pt": "(empilha até {n})"
    },
    "ui.metamagia.escolha_somente": {
      "en": "Choose only {n} metamagics for Arcane Weaving.",
      "pt": "Escolha somente {n} metamagias para a Tecelagem Arcana."
    },
    "ui.metamagia.escolha_uma": {
      "en": "Choose one of the mage's three metamagics.",
      "pt": "Escolha uma das três metamagias do mago."
    },
    "ui.metamagia.estender": {
      "en": "Free action. +{n} round to the spell's duration.",
      "pt": "Ação livre. +{n} rodada na duração da magia."
    },
    "ui.metamagia.estender_plural": {
      "en": "Free action. +{n} rounds to the spell's duration.",
      "pt": "Ação livre. +{n} rodadas na duração da magia."
    },
    "ui.metamagia.fortalecer": {
      "en": "Free action. Multiplies the spell's damage by {mult}.",
      "pt": "Ação livre. Multiplica o dano da magia por {mult}."
    },
    "ui.metamagia.tecelagem_so_turno": {
      "en": "Arcane Weaving can only be prepared on the mage's turn.",
      "pt": "Tecelagem Arcana só pode ser preparada no turno do mago."
    },
    "ui.metamagia.tres_armadas": {
      "en": "Three metamagics armed. Choose the spell and the target manually.",
      "pt": "Três metamagias armadas. Escolha a magia e o alvo manualmente."
    },
    "ui.missao.encerrar_aviso": {
      "en": "Take the reward items before ending. The mission will be completed and the campaign moves on to the next adventure.",
      "pt": "Pegue os itens de recompensa antes de encerrar. A missão será concluída e a campanha seguirá para a próxima aventura."
    },
    "ui.missao.encerrar_botao": {
      "en": "🏁 End mission",
      "pt": "🏁 Encerrar missão"
    },
    "ui.missao.encerrar_titulo": {
      "en": "🏁 End the mission?",
      "pt": "🏁 Encerrar missão?"
    },
    "ui.mundo.ajustar_pontos": {
      "en": "Adjust points",
      "pt": "Ajustar pontos"
    },
    "ui.mundo.ajuste_pontos": {
      "en": "Point adjustment",
      "pt": "Ajuste dos pontos"
    },
    "ui.mundo.ajuste_pontos_desc": {
      "en": "Drag each compass rose to its correct position on the map.",
      "pt": "Arraste cada rosa até a posição correta no mapa."
    },
    "ui.mundo.alt_mapa": {
      "en": "World map of Varlúzia",
      "pt": "Mapa-múndi de Varlúzia"
    },
    "ui.mundo.alt_mapa_simples": {
      "en": "Map of Varlúzia",
      "pt": "Mapa de Varlúzia"
    },
    "ui.mundo.cancelar_ajuste": {
      "en": "Cancel adjustment",
      "pt": "Cancelar ajuste"
    },
    "ui.mundo.em_viagem": {
      "en": "Travelling",
      "pt": "Em viagem"
    },
    "ui.mundo.entrada_masmorra": {
      "en": "Dungeon entrance",
      "pt": "Entrada de masmorra"
    },
    "ui.mundo.entrada_masmorra_desc": {
      "en": "Expedition: 🍖 -{fome} and 💧 -{sede} for each hero.",
      "pt": "Expedição: 🍖 -{fome} e 💧 -{sede} para cada herói."
    },
    "ui.mundo.escolha_destino_desc": {
      "en": "Select a connected city or village to check the travel cost.",
      "pt": "Selecione uma cidade ou vila conectada para consultar o custo da viagem."
    },
    "ui.mundo.iniciando_expedicao": {
      "en": "Starting the expedition…",
      "pt": "Iniciando expedição…"
    },
    "ui.mundo.local_atual": {
      "en": "Current location",
      "pt": "Local atual"
    },
    "ui.mundo.local_atual_desc": {
      "en": "The party is already in this city.",
      "pt": "O grupo já está nesta cidade."
    },
    "ui.mundo.local_distante": {
      "en": "Distant location",
      "pt": "Local distante"
    },
    "ui.mundo.local_distante_desc": {
      "en": "There is no direct route available from the current city yet.",
      "pt": "Ainda não existe uma rota direta disponível a partir da cidade atual."
    },
    "ui.mundo.proxima_etapa": {
      "en": "Next stage: {atual} of {total}. The rest unlock once you clear the previous one.",
      "pt": "Próxima etapa: {atual} de {total}. As demais liberam após concluir a anterior."
    },
    "ui.mundo.req_info": {
      "en": "information: {id}",
      "pt": "informação: {id}"
    },
    "ui.mundo.req_item": {
      "en": "item: {id}",
      "pt": "item: {id}"
    },
    "ui.mundo.req_nivel": {
      "en": "party level {n}",
      "pt": "nível do grupo {n}"
    },
    "ui.mundo.req_renome": {
      "en": "renown {n}",
      "pt": "renome {n}"
    },
    "ui.mundo.req_rota": {
      "en": "route completed: {id}",
      "pt": "rota concluída: {id}"
    },
    "ui.mundo.requisito": {
      "en": "Requirement: {lista}.",
      "pt": "Requisito: {lista}."
    },
    "ui.mundo.rota_concluida": {
      "en": "Route completed",
      "pt": "Rota concluída"
    },
    "ui.mundo.rota_concluida_desc": {
      "en": "The party has already cleared the {n} dungeons of this destination.",
      "pt": "O grupo já concluiu as {n} masmorras deste destino."
    },
    "ui.mundo.rota_disponivel": {
      "en": "Route available",
      "pt": "Rota disponível"
    },
    "ui.mundo.rota_disponivel_desc": {
      "en": "Party travel: 🍖 -{fome} and 💧 -{sede} for each hero.",
      "pt": "Viagem do grupo: 🍖 -{fome} e 💧 -{sede} para cada herói."
    },
    "ui.mundo.rumo_a": {
      "en": "Heading to {nome}…",
      "pt": "Rumo a {nome}…"
    },
    "ui.mundo.salvar_posicoes": {
      "en": "Save positions",
      "pt": "Salvar posições"
    },
    "ui.mundo.so_anfitriao_expedicao": {
      "en": "Only the host starts the expedition.",
      "pt": "Apenas o anfitrião inicia a expedição."
    },
    "ui.mundo.so_anfitriao_viagem": {
      "en": "Only the host chooses the destination.",
      "pt": "Apenas o anfitrião escolhe o destino."
    },
    "ui.mundo.titulo": {
      "en": "🧭 Varlúzia — choose a destination",
      "pt": "🧭 Varlúzia — escolha um destino"
    },
    "ui.mundo.viajar_para": {
      "en": "Travel to {nome}",
      "pt": "Viajar para {nome}"
    },
    "ui.mundo.voltar_cidade": {
      "en": "← Back to the city",
      "pt": "← Voltar à cidade"
    },
    "ui.mundo.voltar_mapa": {
      "en": "← Back to the world map",
      "pt": "← Voltar ao mapa-múndi"
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
    "ui.objetivo.secundarios": {
      "en": "Secondary",
      "pt": "Secundários"
    },
    "ui.paladino.ativar": {
      "en": "💡 ACTIVATE",
      "pt": "💡 ATIVAR"
    },
    "ui.paladino.custo_turno": {
      "en": "COST/TURN",
      "pt": "CUSTO/TURNO"
    },
    "ui.paladino.dados_extra": {
      "en": "+{n}d6 extra",
      "pt": "+{n}d6 extra"
    },
    "ui.paladino.imposicao_custo": {
      "en": "Lay on Hands requires 🍖3 and 💧2.",
      "pt": "Imposição das Mãos requer 🍖3 e 💧2."
    },
    "ui.paladino.imposicao_extra": {
      "en": "+1d6 EXTRA PER +2🍖 +2💧 (up to 3×)",
      "pt": "+1d6 EXTRA POR +2🍖 +2💧 (até 3×)"
    },
    "ui.paladino.imposicao_painel_titulo": {
      "en": "🙏 LAY ON HANDS",
      "pt": "🙏 IMPOSIÇÃO DAS MÃOS"
    },
    "ui.paladino.imposicao_so_turno": {
      "en": "Lay on Hands can only be used on your turn.",
      "pt": "Só é possível usar Imposição das Mãos no seu turno."
    },
    "ui.paladino.imposicao_titulo": {
      "en": "🙏 Lay on Hands — Adjacent ally",
      "pt": "🙏 Imposição das Mãos — Aliado adjacente"
    },
    "ui.paladino.luz_subtitulo": {
      "en": "FREE ACTION — fixed bonuses until switched off",
      "pt": "AÇÃO LIVRE — bônus fixos até desativar"
    },
    "ui.paladino.luz_titulo": {
      "en": "💡 WARRIOR OF LIGHT",
      "pt": "💡 GUERREIRO DA LUZ"
    },
    "ui.paladino.protetor_so_turno": {
      "en": "Protector can only be used on your turn.",
      "pt": "Só é possível usar Protetor no seu turno."
    },
    "ui.paladino.selecione_bonus": {
      "en": "Select bonuses",
      "pt": "Selecione bônus"
    },
    "ui.pausa.continuar": {
      "en": "Keep playing <kbd>Esc</kbd>",
      "pt": "Continuar jogando <kbd>Esc</kbd>"
    },
    "ui.pausa.fechar": {
      "en": "Close menu",
      "pt": "Fechar menu"
    },
    "ui.pausa.menu_inicial": {
      "en": "⌂ Back to the main menu",
      "pt": "⌂ Voltar ao menu inicial"
    },
    "ui.pausa.pergunta": {
      "en": "What would you like to do?",
      "pt": "O que deseja fazer?"
    },
    "ui.pausa.sair": {
      "en": "⏻ Quit the game",
      "pt": "⏻ Sair do jogo"
    },
    "ui.pausa.titulo": {
      "en": "Pause menu",
      "pt": "Menu de pausa"
    },
    "ui.pergaminho.alcance": {
      "en": "Range",
      "pt": "Alcance"
    },
    "ui.pergaminho.area": {
      "en": "Area",
      "pt": "Área"
    },
    "ui.pergaminho.cd_save": {
      "en": "Save DC",
      "pt": "CD do save"
    },
    "ui.pergaminho.conjurador": {
      "en": "Caster",
      "pt": "Conjurador"
    },
    "ui.pergaminho.dano": {
      "en": "Damage",
      "pt": "Dano"
    },
    "ui.pergaminho.duracao": {
      "en": "Duration",
      "pt": "Duração"
    },
    "ui.pergaminho.efeito": {
      "en": "Effect",
      "pt": "Efeito"
    },
    "ui.pergaminho.falha": {
      "en": "Failure",
      "pt": "Falha"
    },
    "ui.pergaminho.falha_classe": {
      "en": "+50% class",
      "pt": "+50% classe"
    },
    "ui.pergaminho.falha_nenhuma": {
      "en": "none",
      "pt": "nenhuma"
    },
    "ui.pergaminho.int_bonus": {
      "en": "+{n} (DC/damage)",
      "pt": "+{n} (CD/dano)"
    },
    "ui.pergaminho.moedas": {
      "en": "{n} coins",
      "pt": "{n} moedas"
    },
    "ui.pergaminho.nivel": {
      "en": "Level {n}",
      "pt": "Nível {n}"
    },
    "ui.pergaminho.no_conjurador": {
      "en": "on the caster",
      "pt": "no conjurador"
    },
    "ui.pergaminho.preco": {
      "en": "Price",
      "pt": "Preço"
    },
    "ui.pergaminho.quadrados": {
      "en": "{n} sq.",
      "pt": "{n} quad."
    },
    "ui.pergaminho.raio": {
      "en": "radius {n}",
      "pt": "raio {n}"
    },
    "ui.pergaminho.rodadas": {
      "en": "{n} round(s)",
      "pt": "{n} rodada(s)"
    },
    "ui.pergaminho.rodape": {
      "en": "SCROLL · {circulo} CIRCLE",
      "pt": "PERGAMINHO · {circulo} CÍRCULO"
    },
    "ui.pergaminho.so_conjurador": {
      "en": "mage/cleric only",
      "pt": "só mago/clérigo"
    },
    "ui.pergaminho.so_conjurador_usa": {
      "en": "Only a mage or cleric can use scrolls.",
      "pt": "Apenas mago ou clérigo usam pergaminhos."
    },
    "ui.pergaminho.talento_cd": {
      "en": "DC +1",
      "pt": "CD +1"
    },
    "ui.pergaminho.talento_dano": {
      "en": "Damage ×1.5",
      "pt": "Dano ×1.5"
    },
    "ui.pergaminho.talento_duracao": {
      "en": "Duration +1",
      "pt": "Duração +1"
    },
    "ui.pergaminho.talentos": {
      "en": "Talents",
      "pt": "Talentos"
    },
    "ui.purificacao.doenca": {
      "en": "Disease",
      "pt": "Doença"
    },
    "ui.purificacao.maldicao": {
      "en": "Curse",
      "pt": "Maldição"
    },
    "ui.purificacao.petrificacao": {
      "en": "Petrification",
      "pt": "Petrificação"
    },
    "ui.purificacao.veneno": {
      "en": "Poison",
      "pt": "Veneno"
    },
    "ui.refugio.abrir_bau_heroi": {
      "en": "🛏️ Open the hero's chest",
      "pt": "🛏️ Abrir baú do herói"
    },
    "ui.refugio.aplicar_fundo": {
      "en": "Apply background",
      "pt": "Aplicar fundo"
    },
    "ui.refugio.aventureiro": {
      "en": "adventurer",
      "pt": "aventureiro"
    },
    "ui.refugio.bau_compartilhado": {
      "en": "Shared chest",
      "pt": "Baú compartilhado"
    },
    "ui.refugio.bau_privado": {
      "en": "Private chest",
      "pt": "Baú privado"
    },
    "ui.refugio.bau_privado_alheio": {
      "en": "The private chest cannot be accessed by another player.",
      "pt": "O baú privado não pode ser acessado por outro jogador."
    },
    "ui.refugio.bau_privado_desc": {
      "en": "Your {n} slots (💰 {ouro}) live in the chest window, next to your inventory.",
      "pt": "Seus {n} espaços (💰 {ouro}) ficam na janela do baú, ao lado do seu inventário."
    },
    "ui.refugio.bolsa_vazia": {
      "en": "Bag empty.",
      "pt": "Bolsa vazia."
    },
    "ui.refugio.depositar_ouro": {
      "en": "Deposit gold",
      "pt": "Depositar ouro"
    },
    "ui.refugio.espaco_privado": {
      "en": "Your private space",
      "pt": "Seu espaço privado"
    },
    "ui.refugio.fundo_quarto": {
      "en": "Room background",
      "pt": "Fundo do quarto"
    },
    "ui.refugio.guardar": {
      "en": "Store",
      "pt": "Guardar"
    },
    "ui.refugio.guardar_itens": {
      "en": "Store items",
      "pt": "Guardar itens"
    },
    "ui.refugio.guardar_no_bau": {
      "en": "Store in the chest",
      "pt": "Guardar no baú"
    },
    "ui.refugio.quarto_de": {
      "en": "🛏️ {nome}'s room",
      "pt": "🛏️ Quarto de {nome}"
    },
    "ui.refugio.quartos_privados": {
      "en": "Private rooms",
      "pt": "Quartos privados"
    },
    "ui.refugio.renome_individual": {
      "en": "Individual renown: {n}",
      "pt": "Renome individual: {n}"
    },
    "ui.refugio.retirar": {
      "en": "Take",
      "pt": "Retirar"
    },
    "ui.refugio.retirar_do_bau": {
      "en": "Take from the chest",
      "pt": "Retirar do baú"
    },
    "ui.refugio.retirar_ouro": {
      "en": "Withdraw gold",
      "pt": "Retirar ouro"
    },
    "ui.refugio.sem_quartos": {
      "en": "No rooms registered yet.",
      "pt": "Nenhum quarto cadastrado ainda."
    },
    "ui.refugio.sem_trofeu": {
      "en": "No trophy placed.",
      "pt": "Nenhum troféu alocado."
    },
    "ui.refugio.seu_quarto": {
      "en": "(your room)",
      "pt": "(seu quarto)"
    },
    "ui.refugio.somente_visual": {
      "en": "View only",
      "pt": "Somente visualização"
    },
    "ui.refugio.subtitulo": {
      "en": "Shared campaign chest · {n}/{max} slots · 💰 {ouro}",
      "pt": "Baú compartilhado da campanha · {n}/{max} espaços · 💰 {ouro}"
    },
    "ui.refugio.titulo": {
      "en": "🏰 Heroes' Refuge",
      "pt": "🏰 Refúgio dos Heróis"
    },
    "ui.refugio.trofeus": {
      "en": "Trophies",
      "pt": "Troféus"
    },
    "ui.refugio.vazio": {
      "en": "Empty.",
      "pt": "Vazio."
    },
    "ui.refugio.voltar_cidade": {
      "en": "Back to the city",
      "pt": "Voltar à cidade"
    },
    "ui.refugio.voltar_refugio": {
      "en": "Back to the refuge",
      "pt": "Voltar ao refúgio"
    },
    "ui.resistencia.fortitude": {
      "en": "Fortitude",
      "pt": "Fortitude"
    },
    "ui.resistencia.reflexos": {
      "en": "Reflex",
      "pt": "Reflexos"
    },
    "ui.resistencia.vontade": {
      "en": "Will",
      "pt": "Vontade"
    },
    "ui.save.apagar_confirm": {
      "en": "Delete \"{nome}\"? This is permanent.",
      "pt": "Apagar \"{nome}\"? Isso é permanente."
    },
    "ui.save.avulso": {
      "en": "One-off",
      "pt": "Avulso"
    },
    "ui.save.campanha": {
      "en": "Campaign",
      "pt": "Campanha"
    },
    "ui.save.codigo_4_letras": {
      "en": "The code must have 4 letters.",
      "pt": "O código deve ter 4 letras."
    },
    "ui.save.de_nome_ao_jogo": {
      "en": "Give the game a name.",
      "pt": "Dê um nome ao jogo."
    },
    "ui.save.encerrar": {
      "en": "End",
      "pt": "Encerrar"
    },
    "ui.save.encerrar_confirm": {
      "en": "End this campaign? It will be preserved and can spawn a continuation.",
      "pt": "Encerrar esta campanha? Ela ficará preservada e poderá gerar uma continuação."
    },
    "ui.save.encerrar_title": {
      "en": "Ends this Master campaign and keeps it as history",
      "pt": "Encerra esta campanha de Mestre e preserva-a como histórico"
    },
    "ui.save.entrada_auto": {
      "en": "Automatic",
      "pt": "Automática"
    },
    "ui.save.entrada_novos": {
      "en": "New players joining",
      "pt": "Entrada de novos jogadores"
    },
    "ui.save.entrada_voto": {
      "en": "Vote of the active members",
      "pt": "Votação dos membros ativos"
    },
    "ui.save.fase_membros": {
      "en": " · phase {f} · {n} hero(es)",
      "pt": " · fase {f} · {n} herói(s)"
    },
    "ui.save.heroi": {
      "en": "hero",
      "pt": "herói"
    },
    "ui.save.nome_nova_campanha": {
      "en": "Name of the new campaign:",
      "pt": "Nome da nova campanha:"
    },
    "ui.save.pediu_vaga": {
      "en": "{quem} asked for the {heroi} slot. Approve?",
      "pt": "{quem} pediu a vaga de {heroi}. Aprovar?"
    },
    "ui.save.sequel_title": {
      "en": "Creates a new campaign with the same group, copying the current state",
      "pt": "Cria uma nova campanha no mesmo grupo, copiando o estado atual"
    },
    "ui.save.sigla.fort": {
      "en": "FORT",
      "pt": "FORT"
    },
    "ui.save.sigla.ref": {
      "en": "REF",
      "pt": "REF"
    },
    "ui.save.sigla.von": {
      "en": "WILL",
      "pt": "VON"
    },
    "ui.save.subst_experiente": {
      "en": "Experienced, no items",
      "pt": "Experiente, sem itens"
    },
    "ui.save.subst_herda": {
      "en": "Inherits the previous sheet",
      "pt": "Herda a ficha anterior"
    },
    "ui.save.subst_nivel1": {
      "en": "Level 1",
      "pt": "Nível 1"
    },
    "ui.save.substituicao": {
      "en": "Hero replacement",
      "pt": "Substituição de herói"
    },
    "ui.save.sufixo_continuacao": {
      "en": " — continued",
      "pt": " — continuação"
    },
    "ui.selecao.aria_grid": {
      "en": "Character selection",
      "pt": "Seleção de personagens"
    },
    "ui.selecao.assumir_mestre": {
      "en": "🎭 Take the Master's seat",
      "pt": "🎭 Assumir como Mestre"
    },
    "ui.selecao.caracteristicas": {
      "en": "ℹ️ Traits",
      "pt": "ℹ️ Características"
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
    "ui.selecao.copiar_codigo": {
      "en": "Click to copy",
      "pt": "Clique para copiar"
    },
    "ui.selecao.escolha_2_magias": {
      "en": "Choose 2 spells of the 1st circle.",
      "pt": "Escolha 2 magias de 1º círculo."
    },
    "ui.selecao.escolha_heroi": {
      "en": "Choose your hero",
      "pt": "Escolha seu herói"
    },
    "ui.selecao.escolha_heroi_toque": {
      "en": "Choose your hero — tap to select",
      "pt": "Escolha seu herói — toque para selecionar"
    },
    "ui.selecao.iniciar_jogo": {
      "en": "▶ Start Game",
      "pt": "▶ Iniciar Jogo"
    },
    "ui.selecao.iniciativa": {
      "en": "⚡ INITIATIVE",
      "pt": "⚡ INICIATIVA"
    },
    "ui.selecao.ja_escolhido": {
      "en": "Character already chosen by another player.",
      "pt": "Personagem já escolhido por outro jogador."
    },
    "ui.selecao.masmorra_procedural": {
      "en": "Procedural (random)",
      "pt": "Procedural (aleatória)"
    },
    "ui.selecao.mestre_virar_heroi": {
      "en": "🎭 Master — click to become a hero",
      "pt": "🎭 Mestre — clique para virar herói"
    },
    "ui.selecao.partir_aventura": {
      "en": "⚔ Set Out on the Adventure",
      "pt": "⚔ Partir para a Aventura"
    },
    "ui.selecao.percepcao": {
      "en": "👁‍🗨 PERCEPTION",
      "pt": "👁‍🗨 PERCEPÇÃO"
    },
    "ui.selecao.raio_visao": {
      "en": "👁 SIGHT RADIUS",
      "pt": "👁 RAIO DE VISÃO"
    },
    "ui.selecao.sala": {
      "en": "ROOM",
      "pt": "SALA"
    },
    "ui.selecao.selecionar": {
      "en": "Select {nome}",
      "pt": "Selecionar {nome}"
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
      "en": "Bonus action. d20+DEX vs the monsters' perception. You can't attack in the same turn. Invisible (not targetable) until you attack — moving does NOT reveal you. Upkeep 🍖-1 💧-1/turn.",
      "pt": "Ação bônus. d20+DES vs percepção dos monstros. Não pode atacar no mesmo turno. Invisível (não é alvo) até atacar — mover-se NÃO revela. Manutenção 🍖-1 💧-1/turno."
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
    },
    "ui.selecao.ver_caracteristicas_title": {
      "en": "See the hero's traits",
      "pt": "Ver características do herói"
    },
    "ui.selecao.voce_e_mestre": {
      "en": "🎭 You are the Master — you will control the monsters in the dungeon.",
      "pt": "🎭 Você é o Mestre — controlará os monstros na masmorra."
    },
    "ui.sobrevivencia.aviso_colapso": {
      "en": "⚠️ Restore hunger or thirst within {n} turns or you will die!",
      "pt": "⚠️ Recupere fome ou sede em {n} turnos ou morrerá!"
    },
    "ui.sobrevivencia.estado.colapso": {
      "en": "Collapse",
      "pt": "Colapso"
    },
    "ui.sobrevivencia.estado.grave": {
      "en": "Severe Pressure",
      "pt": "Pressão Grave"
    },
    "ui.sobrevivencia.estado.leve": {
      "en": "Light Pressure",
      "pt": "Pressão Leve"
    },
    "ui.sobrevivencia.estado.moderada": {
      "en": "Moderate Pressure",
      "pt": "Pressão Moderada"
    },
    "ui.sobrevivencia.estado.neutro": {
      "en": "Neutral",
      "pt": "Neutro"
    },
    "ui.sobrevivencia.estado.saciado": {
      "en": "Sated",
      "pt": "Saciado"
    },
    "ui.sobrevivencia.fome": {
      "en": "Hunger",
      "pt": "Fome"
    },
    "ui.sobrevivencia.fome_caixa": {
      "en": "HUNGER",
      "pt": "FOME"
    },
    "ui.sobrevivencia.modificador": {
      "en": "Modifier",
      "pt": "Modificador"
    },
    "ui.sobrevivencia.sede": {
      "en": "Thirst",
      "pt": "Sede"
    },
    "ui.sobrevivencia.sede_caixa": {
      "en": "THIRST",
      "pt": "SEDE"
    },
    "ui.status.acerto_total": {
      "en": "Total to-hit",
      "pt": "Acerto total"
    },
    "ui.status.aria": {
      "en": "Character status",
      "pt": "Status do personagem"
    },
    "ui.status.arma_equipada": {
      "en": "Equipped weapon",
      "pt": "Arma equipada"
    },
    "ui.status.atrib.ataque": {
      "en": "attack",
      "pt": "ataque"
    },
    "ui.status.atrib.bonus_acerto": {
      "en": "attack",
      "pt": "ataque"
    },
    "ui.status.atrib.bonus_ca": {
      "en": "AC",
      "pt": "CA"
    },
    "ui.status.atrib.bonus_dano": {
      "en": "damage",
      "pt": "dano"
    },
    "ui.status.atrib.bonus_mov": {
      "en": "movement",
      "pt": "movimento"
    },
    "ui.status.atrib.bonus_res": {
      "en": "saves",
      "pt": "resistências"
    },
    "ui.status.atrib.ca": {
      "en": "AC",
      "pt": "CA"
    },
    "ui.status.atrib.dano": {
      "en": "damage",
      "pt": "dano"
    },
    "ui.status.atrib.visao": {
      "en": "vision",
      "pt": "visão"
    },
    "ui.status.barreira_arcana": {
      "en": "Arcane Barrier",
      "pt": "Barreira Arcana"
    },
    "ui.status.barreira_arcana_ef": {
      "en": "-{n} to all damage · {r} round(s)",
      "pt": "-{n} de todo dano · {r} rodada(s)"
    },
    "ui.status.base_atual": {
      "en": "base → current",
      "pt": "base → atual"
    },
    "ui.status.bencao_ativa": {
      "en": "Blessing active",
      "pt": "Bênção ativa"
    },
    "ui.status.brutalidade": {
      "en": "Brutality",
      "pt": "Brutalidade"
    },
    "ui.status.brutalidade_ef": {
      "en": "+{n} weapon damage",
      "pt": "+{n} dano de arma"
    },
    "ui.status.cancao_heroica": {
      "en": "Heroic Song",
      "pt": "Canção Heroica"
    },
    "ui.status.cego": {
      "en": "Blinded",
      "pt": "Cego"
    },
    "ui.status.cego_ef": {
      "en": "Penalty on ranged attacks",
      "pt": "Penalidade em ataques à distância"
    },
    "ui.status.classe_armadura": {
      "en": "Armour Class",
      "pt": "Classe de Armadura"
    },
    "ui.status.combate": {
      "en": "COMBAT",
      "pt": "COMBATE"
    },
    "ui.status.defesa_impecavel": {
      "en": "Flawless Defence",
      "pt": "Defesa Impecável"
    },
    "ui.status.defesa_impecavel_ef": {
      "en": "Attacks against you have disadvantage",
      "pt": "Ataques contra você têm desvantagem"
    },
    "ui.status.desarmado": {
      "en": "Unarmed",
      "pt": "Desarmado"
    },
    "ui.status.detalhe_acerto": {
      "en": "BAB {bba} · {attr} {mod} · weapon {arma} · temporary {temp}",
      "pt": "BBA {bba} · {attr} {mod} · arma {arma} · temporários {temp}"
    },
    "ui.status.em_chamas": {
      "en": "On fire",
      "pt": "Em chamas"
    },
    "ui.status.em_chamas_ef": {
      "en": "Takes damage for {n} round(s)",
      "pt": "Sofre dano por {n} rodada(s)"
    },
    "ui.status.envenenado": {
      "en": "Poisoned",
      "pt": "Envenenado"
    },
    "ui.status.envenenado_ef": {
      "en": "Penalty active · {n} round(s)",
      "pt": "Penalidade ativa · {n} rodada(s)"
    },
    "ui.status.exaustao": {
      "en": "Exhaustion",
      "pt": "Exaustão"
    },
    "ui.status.exaustao_ef": {
      "en": "-{n} attack · -{n} damage · -{n} saves",
      "pt": "-{n} ataque · -{n} dano · -{n} resistências"
    },
    "ui.status.sangramento": {
      "en": "Bleeding {n}",
      "pt": "Sangramento {n}"
    },
    "ui.status.sangramento_ef": {
      "en": "{n} HP per round · {r} round(s) remaining",
      "pt": "{n} PV por rodada · {r} rodada(s) restantes"
    },
    "ui.status.ferida_aberta": {
      "en": "Open Wound",
      "pt": "Ferida Aberta"
    },
    "ui.status.ferida_aberta_ef": {
      "en": "+1 HP per round · requires healing to close",
      "pt": "+1 PV por rodada · requer cura para fechar"
    },
    "ui.status.hemorragia": {
      "en": "Haemorrhage",
      "pt": "Hemorragia"
    },
    "ui.status.hemorragia_ef": {
      "en": "Doubles Bleeding damage, not Open Wound damage",
      "pt": "Dobra o dano do Sangramento, não o da Ferida Aberta"
    },
    "ui.condicao.sangramento": {
      "en": "Bleeding",
      "pt": "Sangramento"
    },
    "ui.condicao.sangramento_desc": {
      "en": "Bleeding level {n}: {dano} HP of recurring damage per round.",
      "pt": "Sangramento nível {n}: {dano} PV de dano recorrente por rodada."
    },
    "ui.condicao.hemorragia": {
      "en": "Haemorrhage",
      "pt": "Hemorragia"
    },
    "ui.condicao.hemorragia_desc": {
      "en": "Haemorrhage doubles Bleeding damage, but does not double Open Wound damage.",
      "pt": "A Hemorragia dobra o dano do Sangramento, mas não dobra o dano da Ferida Aberta."
    },
    "ui.condicao.aplicada": {
      "en": "CONDITION APPLIED",
      "pt": "CONDIÇÃO APLICADA"
    },
    "ui.condicao.duracao": {
      "en": "Remaining duration: {n} round(s).",
      "pt": "Duração restante: {n} rodada(s)."
    },
    "ui.condicao.ferida_aberta": {
      "en": "Open Wound: +1 HP per round; healing is required to close it.",
      "pt": "Ferida Aberta: +1 PV por rodada; requer cura para ser fechada."
    },
    "ui.condicao.hemorragia_ativa": {
      "en": "Haemorrhage active: Bleeding damage is doubled.",
      "pt": "Hemorragia ativa: o dano do Sangramento está dobrado."
    },
    "ui.condicao.hemorragia_duracao": {
      "en": "Active while Bleeding remains: {n} round(s) remaining.",
      "pt": "Ativa enquanto houver Sangramento: {n} rodada(s) restantes."
    },
    "ui.status.furia_berserker": {
      "en": "Berserker Fury",
      "pt": "Fúria Berserker"
    },
    "ui.status.furia_berserker_ef": {
      "en": "Extra attack",
      "pt": "Ataque extra"
    },
    "ui.status.golpe_decisivo": {
      "en": "Decisive Strike",
      "pt": "Golpe Decisivo"
    },
    "ui.status.golpe_decisivo_ef": {
      "en": "Next attack will be a critical",
      "pt": "Próximo ataque será crítico"
    },
    "ui.status.golpe_devastador": {
      "en": "Devastating Blow",
      "pt": "Golpe Devastador"
    },
    "ui.status.golpe_devastador_ef": {
      "en": "Enhanced damage dice",
      "pt": "Dados de dano aprimorados"
    },
    "ui.status.golpe_sagrado": {
      "en": "Holy Strike",
      "pt": "Golpe Sagrado"
    },
    "ui.status.golpe_sagrado_ef": {
      "en": "+1d8 holy on attacks",
      "pt": "+1d8 sagrado nos ataques"
    },
    "ui.status.guerreiro_luz": {
      "en": "Warrior of Light",
      "pt": "Guerreiro da Luz"
    },
    "ui.status.indisponivel": {
      "en": "Status unavailable right now.",
      "pt": "Status indisponível agora."
    },
    "ui.status.investida_heroica": {
      "en": "Heroic Charge",
      "pt": "Investida Heroica"
    },
    "ui.status.investida_heroica_ef": {
      "en": "Next melee attack enhanced",
      "pt": "Próximo ataque corpo a corpo aprimorado"
    },
    "ui.status.lentidao": {
      "en": "Slowed",
      "pt": "Lentidão"
    },
    "ui.status.lentidao_ef": {
      "en": "-1 attack · -1 AC",
      "pt": "-1 ataque · -1 CA"
    },
    "ui.status.medo": {
      "en": "Fear",
      "pt": "Medo"
    },
    "ui.status.medo_ef": {
      "en": "Combat penalty",
      "pt": "Penalidade de combate"
    },
    "ui.status.mira_certeira": {
      "en": "Sure Aim",
      "pt": "Mira Certeira"
    },
    "ui.status.mira_certeira_ef": {
      "en": "+2 attack",
      "pt": "+2 ataque"
    },
    "ui.status.mira_perfeita": {
      "en": "Perfect Aim",
      "pt": "Mira Perfeita"
    },
    "ui.status.mira_perfeita_ef": {
      "en": "Advantage at range · +2 damage",
      "pt": "Vantagem à distância · +2 dano"
    },
    "ui.status.modificadores_temp": {
      "en": "TEMPORARY MODIFIERS",
      "pt": "MODIFICADORES TEMPORÁRIOS"
    },
    "ui.status.paralisado": {
      "en": "Paralysed",
      "pt": "Paralisado"
    },
    "ui.status.paralisado_ef": {
      "en": "Cannot act",
      "pt": "Não pode agir"
    },
    "ui.status.regeneracao_divina": {
      "en": "Divine Regeneration",
      "pt": "Regeneração Divina"
    },
    "ui.status.regeneracao_divina_ef": {
      "en": "+1 HP per round",
      "pt": "+1 PV por rodada"
    },
    "ui.status.resistencia_absoluta": {
      "en": "Absolute Resilience",
      "pt": "Resistência Absoluta"
    },
    "ui.status.resistencia_absoluta_ef": {
      "en": "+{n} on saving throws",
      "pt": "+{n} em testes de resistência"
    },
    "ui.status.resistencias": {
      "en": "SAVING THROWS",
      "pt": "TESTES DE RESISTÊNCIA"
    },
    "ui.status.rodadas_restantes": {
      "en": "{n} round(s)",
      "pt": "{n} rodada(s)"
    },
    "ui.status.saciado": {
      "en": "Well Fed",
      "pt": "Saciado"
    },
    "ui.status.saciado_ef": {
      "en": "+1 attack · +1 damage · +1 saves",
      "pt": "+1 ataque · +1 dano · +1 resistências"
    },
    "ui.status.sem_temporarios": {
      "en": "No temporary bonus or penalty.",
      "pt": "Nenhum bônus ou penalidade temporária."
    },
    "ui.status.tecla_s": {
      "en": "E key",
      "pt": "tecla E"
    },
    "ui.status.titulo": {
      "en": "📊 STATUS",
      "pt": "📊 STATUS"
    },
    "ui.tabuleiro.clique_atacar": {
      "en": "Click to attack",
      "pt": "Clique para atacar"
    },
    "ui.tabuleiro.clique_voltar_cidade": {
      "en": "Click to return to the city",
      "pt": "Clique para retornar à cidade"
    },
    "ui.tabuleiro.confirmar_saida": {
      "en": "Leaving by the stairs costs 🍖{f} and 💧{s} (round trip).\nYou return in {n} round(s) and the dungeon carries on without you.\n\nLeave?",
      "pt": "Sair pela escada custa 🍖{f} e 💧{s} (ida e volta).\nVocê volta em {n} rodada(s) e a masmorra continua sem você.\n\nSair?"
    },
    "ui.tabuleiro.elemental_linha": {
      "en": "⚡ The lightning elemental attacks in a straight line (max 3 squares).",
      "pt": "⚡ O elemental elétrico ataca em linha reta (máx 3 casas)."
    },
    "ui.tabuleiro.escada_saida": {
      "en": "Exit Stairs",
      "pt": "Escada de Saída"
    },
    "ui.tabuleiro.heroi": {
      "en": "Hero",
      "pt": "Herói"
    },
    "ui.tabuleiro.inicio": {
      "en": "{classe} START",
      "pt": "INÍCIO {classe}"
    },
    "ui.tabuleiro.perto_da_escada": {
      "en": "Get closer to the stairs to leave.",
      "pt": "Aproxime-se da escada para sair."
    },
    "ui.tabuleiro.perto_do_bau": {
      "en": "Get closer to the chest to open it!",
      "pt": "Aproxime-se do baú para abri-lo!"
    },
    "ui.tabuleiro.provisoes_insuficientes": {
      "en": "Not enough provisions: the trip costs 🍖{f} and 💧{s}.",
      "pt": "Provisões insuficientes: a viagem custa 🍖{f} e 💧{s}."
    },
    "ui.tabuleiro.saida": {
      "en": "EXIT",
      "pt": "SAÍDA"
    },
    "ui.tabuleiro.sem_saida": {
      "en": "There is no way out of this dungeon.",
      "pt": "Não há como sair desta masmorra."
    },
    "ui.tabuleiro.so_no_seu_turno": {
      "en": "You can only leave on your turn.",
      "pt": "Só é possível sair no seu turno."
    },
    "ui.tecnica.automatica": {
      "en": "This technique is automatic.",
      "pt": "Esta técnica é automática."
    },
    "ui.tecnica.recarrega_em": {
      "en": "Technique recharges in {n} round(s).",
      "pt": "Técnica recarrega em {n} rodada(s)."
    },
    "ui.tecnica.so_turno_masmorra": {
      "en": "The technique can only be used on your turn in the dungeon.",
      "pt": "A técnica só pode ser usada no seu turno na masmorra."
    },
    "ui.tooltip.acao": {
      "en": "Action",
      "pt": "Ação"
    },
    "ui.tooltip.alcance": {
      "en": "Range",
      "pt": "Alcance"
    },
    "ui.tooltip.anula": {
      "en": "negates",
      "pt": "anula"
    },
    "ui.tooltip.arremesso": {
      "en": "Throw",
      "pt": "Arremesso"
    },
    "ui.tooltip.atributo": {
      "en": "Attribute",
      "pt": "Atributo"
    },
    "ui.tooltip.bonus_ca": {
      "en": "AC Bonus",
      "pt": "Bônus CA"
    },
    "ui.tooltip.dano": {
      "en": "Damage",
      "pt": "Dano"
    },
    "ui.tooltip.dano_adicional": {
      "en": "Extra damage",
      "pt": "Dano adicional"
    },
    "ui.tooltip.duas_maos": {
      "en": "2 hands",
      "pt": "2 mãos"
    },
    "ui.tooltip.duracao": {
      "en": "Duration",
      "pt": "Duração"
    },
    "ui.tooltip.efeito": {
      "en": "Effect",
      "pt": "Efeito"
    },
    "ui.tooltip.efeito_parcial": {
      "en": "partial effect on success",
      "pt": "efeito parcial em sucesso"
    },
    "ui.tooltip.escudo": {
      "en": "Shield",
      "pt": "Escudo"
    },
    "ui.tooltip.fome": {
      "en": "Hunger",
      "pt": "Fome"
    },
    "ui.tooltip.habilidade_especial": {
      "en": "SPECIAL ABILITY",
      "pt": "HABILIDADE ESPECIAL"
    },
    "ui.tooltip.linha_visao": {
      "en": "Line of sight",
      "pt": "Linha de visão"
    },
    "ui.tooltip.linha_visao_val": {
      "en": "Required to shoot",
      "pt": "Obrigatória para disparar"
    },
    "ui.tooltip.mais_quadrado": {
      "en": "+{n} square",
      "pt": "+{n} quadrado"
    },
    "ui.tooltip.municao": {
      "en": "Ammunition",
      "pt": "Munição"
    },
    "ui.tooltip.nao_permitido": {
      "en": "Not allowed",
      "pt": "Não permitido"
    },
    "ui.tooltip.permitido": {
      "en": "Allowed",
      "pt": "Permitido"
    },
    "ui.tooltip.pode_usar": {
      "en": "CAN USE",
      "pt": "PODE USAR"
    },
    "ui.tooltip.preco": {
      "en": "PRICE",
      "pt": "PREÇO"
    },
    "ui.tooltip.principal": {
      "en": "Main",
      "pt": "Principal"
    },
    "ui.tooltip.projeteis": {
      "en": "{n} projectiles",
      "pt": "{n} projéteis"
    },
    "ui.tooltip.quad_diagonais": {
      "en": "{n} sq. (diagonals included)",
      "pt": "{n} quad. (diagonais incluídas)"
    },
    "ui.tooltip.quadrados": {
      "en": "{n} squares",
      "pt": "{n} quadrados"
    },
    "ui.tooltip.quantidade": {
      "en": "Quantity",
      "pt": "Quantidade"
    },
    "ui.tooltip.reducao_dano": {
      "en": "Damage reduction",
      "pt": "Redução de dano"
    },
    "ui.tooltip.reducao_dano_val": {
      "en": "−{n} per attack/effect, no per-round cap",
      "pt": "−{n} por ataque/efeito, sem limite por rodada"
    },
    "ui.tooltip.requer_duas_maos": {
      "en": "Requires two hands",
      "pt": "Requer duas mãos"
    },
    "ui.tooltip.requer_flechas": {
      "en": "Requires arrows in the off-hand slot",
      "pt": "Requer flechas no slot secundário"
    },
    "ui.tooltip.resistencia": {
      "en": "Save",
      "pt": "Resistência"
    },
    "ui.tooltip.resistencia_val": {
      "en": "{save} DC {cd} — {anula}",
      "pt": "{save} CD {cd} — {anula}"
    },
    "ui.tooltip.restantes": {
      "en": "Remaining",
      "pt": "Restantes"
    },
    "ui.tooltip.risco": {
      "en": "Risk",
      "pt": "Risco"
    },
    "ui.tooltip.risco_val": {
      "en": "A 1 on the d20 = weapon destroyed",
      "pt": "Resultado 1 no d20 = arma destruída"
    },
    "ui.tooltip.rodadas": {
      "en": "{n} rounds",
      "pt": "{n} rodadas"
    },
    "ui.tooltip.sede": {
      "en": "Thirst",
      "pt": "Sede"
    },
    "ui.tooltip.slots_extras": {
      "en": "Extra slots",
      "pt": "Slots extras"
    },
    "ui.tooltip.slots_extras_val": {
      "en": "+{n} inventory",
      "pt": "+{n} de inventário"
    },
    "ui.tooltip.slots_magia": {
      "en": "Spell slots",
      "pt": "Slots de magia"
    },
    "ui.tooltip.todos_herois": {
      "en": "All heroes",
      "pt": "Todos os heróis"
    },
    "ui.tooltip.uma_mao": {
      "en": "1 hand",
      "pt": "1 mão"
    },
    "ui.tooltip.uma_ou_duas": {
      "en": "One or two hands",
      "pt": "Uma ou duas mãos"
    },
    "ui.tooltip.unidades_slot": {
      "en": "{n} units per slot",
      "pt": "{n} unidades por slot"
    },
    "ui.tooltip.uso": {
      "en": "Use",
      "pt": "Uso"
    },
    "ui.tooltip.visao": {
      "en": "Vision",
      "pt": "Visão"
    },
    "ui.atalhos.titulo": {
      "en": "SHORTCUTS",
      "pt": "ATALHOS"
    },
    "ui.atalhos.ajuda": {
      "en": "S to toggle · drag actions here",
      "pt": "S abre/fecha · arraste ações para cá"
    },
    "ui.atalhos.vazio": {
      "en": "Empty shortcut",
      "pt": "Atalho vazio"
    },
    "ui.atalhos.clique_ativar": {
      "en": "click or press its key to use",
      "pt": "clique ou pressione a tecla para usar"
    },
    "ui.atalhos.removido": {
      "en": "Shortcut removed",
      "pt": "Atalho removido"
    },
    "ui.atalhos.item_indisponivel": {
      "en": "That item is no longer in your bag.",
      "pt": "Esse item não está mais na sua bolsa."
    }
  };
Object.assign(window.LANG_STRINGS, window.LANG_INTERFACE);
