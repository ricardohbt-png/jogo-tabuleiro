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
    "ui.arremesso.cancele_primeiro": {
      "en": "Cancel the current throw first (ESC).",
      "pt": "Cancele o arremesso atual primeiro (ESC)."
    },
    "ui.arremesso.log_lanca": {
      "en": "🏹 Spear throw mode — {acao}. Click an enemy (ESC cancels).",
      "pt": "🏹 Modo arremesso de lança — {acao}. Clique num inimigo (ESC cancela)."
    },
    "ui.arremesso.log_principal": {
      "en": "🎯 Throw mode (main hand) — {acao}. Click an enemy (ESC cancels).",
      "pt": "🎯 Modo arremesso (mão principal) — {acao}. Clique num inimigo (ESC cancela)."
    },
    "ui.arremesso.sem_acoes": {
      "en": "No actions available to throw.",
      "pt": "Sem ações disponíveis para arremessar."
    },
    "ui.arremesso.sem_adaga": {
      "en": "No throwable dagger in the main hand.",
      "pt": "Nenhuma adaga arremessável na mão principal."
    },
    "ui.arremesso.sem_lanca": {
      "en": "Short spear not equipped.",
      "pt": "Lança curta não equipada."
    },
    "ui.arremesso.so_3d": {
      "en": "Aimed throwing is only available in the 3D view.",
      "pt": "Arremesso com mira disponível apenas na visão 3D."
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
    "ui.bau.vazio": {
      "en": "The chest is empty.",
      "pt": "O baú está vazio."
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
    "ui.cena.nada_novo": {
      "en": "This person has nothing new to tell for now.",
      "pt": "Esta pessoa não tem nada novo para contar por enquanto."
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
    "ui.cena.voltar_area_comum": {
      "en": "🚪 Back to the common room",
      "pt": "🚪 Voltar à área comum"
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
    "ui.conexao.reconectando": {
      "en": "🔌 Connection lost — reconnecting ({n}/{max})...",
      "pt": "🔌 Conexão perdida — reconectando ({n}/{max})..."
    },
    "ui.conexao.servidor_nao_encontrado": {
      "en": "❌ Server not found. Run iniciar.bat first!",
      "pt": "❌ Servidor não encontrado. Execute iniciar.bat primeiro!"
    },
    "ui.conta.criar_agora": {
      "en": "That account does not exist. Create it now with this nickname and PIN?",
      "pt": "Conta não existe. Criar agora com esse apelido e PIN?"
    },
    "ui.dano_tipo.fogo": {
      "en": "fire",
      "pt": "fogo"
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
    "ui.ficha.habilidades_botao": {
      "en": "Abilities (H)",
      "pt": "Habilidades (H)"
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
    "ui.habilidade.alcance_cajado": {
      "en": "📐 <strong style=\"color:#c8a951\">Extended Reach:</strong> Hits 2 adjacent squares in front and 1 adjacent diagonal square. Requires two hands — incompatible with a shield.",
      "pt": "📐 <strong style=\"color:#c8a951\">Alcance Estendido:</strong> Atinge 2 casas adjacentes à frente e 1 casa diagonal adjacente. Requer duas mãos — incompatível com escudo."
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
    "ui.habilidade.critico_espada": {
      "en": "⚔️ <strong style=\"color:#c8a951\">Improved Critical:</strong> A natural 19 or 20 on the d20 is a critical when the attack hits.",
      "pt": "⚔️ <strong style=\"color:#c8a951\">Crítico Aprimorado:</strong> Um resultado natural de 19 ou 20 no d20 é crítico quando o ataque acerta."
    },
    "ui.habilidade.duas_maos": {
      "en": "✋ <strong style=\"color:#c8a951\">Two Hands:</strong> Incompatible with a shield or a second weapon. Equipping/swapping gear is a free action (no cost).",
      "pt": "✋ <strong style=\"color:#c8a951\">Duas Mãos:</strong> Incompatível com escudo ou 2ª arma. Equipar/trocar de equipamento é ação livre (sem custo)."
    },
    "ui.habilidade.escolha_somente": {
      "en": "Choose only {n} abilities for this combination.",
      "pt": "Escolha somente {n} habilidades para esta combinação."
    },
    "ui.habilidade.expansao_inventario": {
      "en": "🎒 <strong style=\"color:#cc44ff\">Inventory Expansion:</strong> Takes 1 magic slot and permanently adds +{p1} slots to the free inventory while equipped.",
      "pt": "🎒 <strong style=\"color:#cc44ff\">Expansão de Inventário:</strong> Ocupa 1 slot mágico e adiciona permanentemente +{p1} slots ao inventário livre enquanto equipada."
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
    "ui.habilidade.selecione_casa_desarmar": {
      "en": "Select an adjacent square to disarm.",
      "pt": "Selecione uma casa adjacente para desarmar."
    },
    "ui.habilidade.sem_acao_manual": {
      "en": "This ability is passive or has no manual action.",
      "pt": "Esta habilidade é passiva ou não possui uma ação manual."
    },
    "ui.habilidade.so_na_masmorra": {
      "en": "Abilities can only be used in the dungeon.",
      "pt": "Habilidades só podem ser usadas na masmorra."
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
    "ui.hud.acao_usada": {
      "en": "action used",
      "pt": "ação usada"
    },
    "ui.hud.apagar_chamas": {
      "en": "Put out flames",
      "pt": "Apagar chamas"
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
    "ui.hud.bonus": {
      "en": "bonus",
      "pt": "bônus"
    },
    "ui.hud.bonus_usado": {
      "en": "bonus used",
      "pt": "bônus usado"
    },
    "ui.hud.cancao_de_henrique": {
      "en": "Henrique's Heroic Song",
      "pt": "Canção Heroica de Henrique"
    },
    "ui.hud.cantando": {
      "en": "singing",
      "pt": "cantando"
    },
    "ui.hud.criar_armadilha_desc": {
      "en": "Pick an adjacent square. DEX check{b}; a natural 1 sets the trap off on you.",
      "pt": "Selecione uma casa adjacente. Teste de DES{b}; 1 natural dispara a armadilha em você."
    },
    "ui.hud.detectar_desc": {
      "en": "reveals nearby traps and does not set them off",
      "pt": "revela armadilhas próximas e não as dispara"
    },
    "ui.hud.equipado_loja": {
      "en": "Equipped (Shop)",
      "pt": "Equipado (Loja)"
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
    "ui.hud.invisivel": {
      "en": "invisible",
      "pt": "invisível"
    },
    "ui.hud.invisivel_desc": {
      "en": "monsters cannot target you until you attack",
      "pt": "não é alvo dos monstros até atacar"
    },
    "ui.hud.limite_habilidades": {
      "en": "You can only ready {n} abilities per turn.",
      "pt": "Você só pode armar {n} habilidades por turno."
    },
    "ui.hud.livre": {
      "en": "free",
      "pt": "livre"
    },
    "ui.hud.mais_ca_revelar": {
      "en": "+2 AC on revealing",
      "pt": "+2 CA ao revelar"
    },
    "ui.hud.mao_principal": {
      "en": "main hand",
      "pt": "mão principal"
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
    "ui.hud.parar": {
      "en": "stop",
      "pt": "parar"
    },
    "ui.hud.passiva": {
      "en": "passive",
      "pt": "passiva"
    },
    "ui.hud.recupera_ouro": {
      "en": "You may recover the gold.",
      "pt": "Pode recuperar o ouro."
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
    "ui.hud.selecione_casa": {
      "en": "pick the square",
      "pt": "selecione a casa"
    },
    "ui.hud.sem_aliado": {
      "en": "No ally available.",
      "pt": "Nenhum aliado disponível."
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
    "ui.hud.usada": {
      "en": "used",
      "pt": "usada"
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
    "ui.item.desc.alcance_lanca": {
      "en": "Range 2 (straight) / 1 (diag)",
      "pt": "Alcance 2 (reto) / 1 (diag)"
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
    "ui.item.material.metal": {
      "en": "metal",
      "pt": "metálica"
    },
    "ui.item.material.organic": {
      "en": "organic",
      "pt": "orgânica"
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
    "ui.loja.classe_restrita": {
      "en": "Class restricted",
      "pt": "Classe restrita"
    },
    "ui.loja.comprar": {
      "en": "Buy",
      "pt": "Comprar"
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
    "ui.loja.remover_maldicao": {
      "en": "Remove: {nome}",
      "pt": "Remover: {nome}"
    },
    "ui.loja.restrito": {
      "en": "Restricted",
      "pt": "Restrito"
    },
    "ui.loja.title_classe_restrita": {
      "en": "Your class cannot use this item",
      "pt": "Sua classe não pode usar este item"
    },
    "ui.loja.title_ja_usada": {
      "en": "Already used on this visit to town",
      "pt": "Já usada nesta visita à cidade"
    },
    "ui.loja.usada": {
      "en": "Used",
      "pt": "Usada"
    },
    "ui.magia.abencoar.desc": {
      "en": "<b>Area:</b> 6x6 centred on Lewis<br>\n               <b>Buff:</b> +1 attack, damage, AC, resistance<br>\n               <b>Duration:</b> 1d4+1 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Área:</b> 6x6 centrado em Lewis<br>\n               <b>Buff:</b> +1 ataque, dano, CA, resistência<br>\n               <b>Duração:</b> 1d4+1 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.abencoar_arma.desc": {
      "en": "<b>Range:</b> 6 squares<br>\n               <b>Buff:</b> +1 attack and damage on the weapon<br>\n               <b>Blessed weapon:</b> ignores reductions, halved damage and physical immunity<br>\n               <b>Duration:</b> 1d6+2 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Alcance:</b> 6 quadrados<br>\n               <b>Buff:</b> +1 ataque e dano na arma<br>\n               <b>Arma abençoada:</b> ignora reduções, dano pela metade e imunidade física<br>\n               <b>Duração:</b> 1d6+2 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
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
    "ui.magia.clarividencia.desc": {
      "en": "<b>Range:</b> the whole map (aim anywhere)<br>\n               <b>Area:</b> 4x4 (scales with level)<br>\n               <b>Effect:</b> reveals the fog, the monsters and the traps there<br>\n               <b>Duration:</b> 2 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Alcance:</b> o mapa inteiro (mire em qualquer lugar)<br>\n               <b>Área:</b> 4x4 (escala com nível)<br>\n               <b>Efeito:</b> revela a névoa, os monstros e as armadilhas do local<br>\n               <b>Duração:</b> 2 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.comando.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Target:</b> 1 monster (constructs, undead and those immune to enchantment resist)<br>\n               <b>Fail:</b> on its next turn, YOU direct the monster — movement, main action, abilities and items<br>\n               <b>Duration:</b> 1 turn<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Alvo:</b> 1 monstro (construtos, mortos-vivos e imunes a encantamento resistem)<br>\n               <b>Falha:</b> no próximo turno dele, VOCÊ dirige o monstro — movimento, ação principal, habilidades e itens<br>\n               <b>Duração:</b> 1 turno<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
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
    "ui.magia.esc_cancela": {
      "en": "ESC cancels",
      "pt": "ESC cancela"
    },
    "ui.magia.invisibilidade.desc": {
      "en": "<b>Effect:</b> enemies cannot attack you<br>\n               <b>Attack:</b> with advantage (higher of 2d20) + sneak<br>\n               <b>Breaks:</b> on attacking or casting a spell<br>\n               <b>Duration:</b> 1d6+1 rounds",
      "pt": "<b>Efeito:</b> inimigos não podem atacar<br>\n               <b>Ataque:</b> com vantagem (2d20 maior) + furtivo<br>\n               <b>Quebra:</b> ao atacar ou lançar magia<br>\n               <b>Duração:</b> 1d6+1 rodadas"
    },
    "ui.magia.jato_ar.desc": {
      "en": "<b>Cone:</b> 4 squares long, 4 wide at the base<br>\n               <b>Damage:</b> 1d6 per level<br>\n               <b>Failed Reflex:</b> pushes 1d6 squares<br>\n               <b>Success:</b> pushes 2 squares<br>\n               <b>Wall collision:</b> +1d4 damage",
      "pt": "<b>Cone:</b> 4 quadrados comp., 4 base<br>\n               <b>Dano:</b> 1d6 por nível<br>\n               <b>Falha Reflexos:</b> empurra 1d6 quadrados<br>\n               <b>Sucesso:</b> empurra 2 quadrados<br>\n               <b>Colisão parede:</b> +1d4 dano"
    },
    "ui.magia.lentidao.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Fail:</b> 1 action/round, no reaction, -1 AC<br>\n               <b>Success:</b> movement ÷2, -1 attack<br>\n               <b>Duration:</b> 1d4 rounds",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Falha:</b> 1 ação/rodada, sem reação, -1 CA<br>\n               <b>Sucesso:</b> movimento ÷2, -1 ataque<br>\n               <b>Duração:</b> 1d4 rodadas"
    },
    "ui.magia.manto_escuridao.desc": {
      "en": "<b>Radius:</b> 3 squares centred on the caster<br>\n               <b>Without night vision:</b> attacks roll 2d20 and use the lower<br>\n               <b>With night vision:</b> 2d20 uses the higher vs the blinded<br>\n               <b>Caster:</b> gains darkvision for the cloak's duration<br>\n               <b>Maximum ranged distance:</b> 2 squares<br>\n               <b>Duration:</b> 1d4 rounds",
      "pt": "<b>Raio:</b> 3 quadrados centrado no caster<br>\n               <b>Sem visão noturna:</b> 2d20 usa menor nos ataques<br>\n               <b>Com visão noturna:</b> 2d20 usa maior vs cegos<br>\n               <b>Conjurador:</b> recebe visão no escuro pela duração do manto<br>\n               <b>Distância máxima à distância:</b> 2 quadrados<br>\n               <b>Duração:</b> 1d4 rodadas"
    },
    "ui.magia.medo.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Fail:</b> flees for 1d4+1 rounds<br>\n               <b>Effects:</b> -1 attack, will not approach<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Falha:</b> foge 1d4+1 rodadas<br>\n               <b>Efeitos:</b> -1 ataque, não se aproxima<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
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
    "ui.magia.silencio.desc": {
      "en": "<b>Area:</b> 4x4 centred on the point<br>\n               <b>Effect:</b> spells do not work inside the area<br>\n               <b>Duration:</b> 1d4+1 rounds<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Área:</b> 4x4 centrado no ponto<br>\n               <b>Efeito:</b> magias não funcionam na área<br>\n               <b>Duração:</b> 1d4+1 rodadas<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
    },
    "ui.magia.sono.desc": {
      "en": "<b>Save:</b> Will<br>\n               <b>Fail:</b> sleeps for 1d4+1 rounds<br>\n               <b>Bonus:</b> 1st attack against a sleeping target = critical<br>\n               <b>Wakes:</b> on taking any damage<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
      "pt": "<b>Save:</b> Vontade<br>\n               <b>Falha:</b> dorme 1d4+1 rodadas<br>\n               <b>Bônus:</b> 1º ataque contra dormindo = crítico<br>\n               <b>Acorda:</b> ao receber qualquer dano<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
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
    "ui.mundo.cancelar_ajuste": {
      "en": "Cancel adjustment",
      "pt": "Cancelar ajuste"
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
    "ui.mundo.salvar_posicoes": {
      "en": "Save positions",
      "pt": "Salvar posições"
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
    "ui.status.defesa_impecavel": {
      "en": "Flawless Defence",
      "pt": "Defesa Impecável"
    },
    "ui.status.defesa_impecavel_ef": {
      "en": "Attacks against you have disadvantage",
      "pt": "Ataques contra você têm desvantagem"
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
    "ui.status.saciado": {
      "en": "Well Fed",
      "pt": "Saciado"
    },
    "ui.status.saciado_ef": {
      "en": "+1 attack · +1 damage · +1 saves",
      "pt": "+1 ataque · +1 dano · +1 resistências"
    },
    "ui.tabuleiro.confirmar_saida": {
      "en": "Leaving by the stairs costs 🍖{f} and 💧{s} (round trip).\nYou return in {n} round(s) and the dungeon carries on without you.\n\nLeave?",
      "pt": "Sair pela escada custa 🍖{f} e 💧{s} (ida e volta).\nVocê volta em {n} rodada(s) e a masmorra continua sem você.\n\nSair?"
    },
    "ui.tabuleiro.elemental_linha": {
      "en": "⚡ The lightning elemental attacks in a straight line (max 3 squares).",
      "pt": "⚡ O elemental elétrico ataca em linha reta (máx 3 casas)."
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
    "ui.tabuleiro.sem_saida": {
      "en": "There is no way out of this dungeon.",
      "pt": "Não há como sair desta masmorra."
    },
    "ui.tabuleiro.so_no_seu_turno": {
      "en": "You can only leave on your turn.",
      "pt": "Só é possível sair no seu turno."
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
    }
  };
Object.assign(window.LANG_STRINGS, window.LANG_INTERFACE);
