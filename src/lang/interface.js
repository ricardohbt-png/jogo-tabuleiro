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
  "ui.magia.dominar_mente.desc": {
    "en": "<b>Save:</b> Will<br>\n               <b>Target:</b> 1 monster (constructs, undead and those immune to enchantment resist)<br>\n               <b>Fail:</b> YOU direct the monster on each of its turns for 1d4+1 rounds<br>\n               <b>New save:</b> each point of damage taken gives a cumulative +2 on the next Will; passing breaks the control<br>\n               <b>Cost:</b> 🍖-1 💧-1 + 1 slot",
    "pt": "<b>Save:</b> Vontade<br>\n               <b>Alvo:</b> 1 monstro (construtos, mortos-vivos e imunes a encantamento resistem)<br>\n               <b>Falha:</b> VOCÊ dirige o monstro a cada turno dele por 1d4+1 rodadas<br>\n               <b>Novo teste:</b> cada dano sofrido dá +2 cumulativo na próxima Vontade; passar rompe o controle<br>\n               <b>Custo:</b> 🍖-1 💧-1 + 1 slot"
  },
  "ui.magia.dominar_morto_vivo.desc": {
    "en": "<b>Requires:</b> an undead target<br>\n               <b>Save:</b> Will (bonus = CR) on casting and every round<br>\n               <b>Fail:</b> becomes a temporary servant (acts in the servants' phase)<br>\n               <b>3 fails in a row:</b> PERMANENT control<br>\n               <b>Passing:</b> breaks the control (turns hostile again) — recast<br>\n               <b>Single slot</b> · does not count towards Animate Dead",
    "pt": "<b>Requer:</b> alvo do tipo morto-vivo<br>\n               <b>Save:</b> Vontade (bônus = ND) ao lançar e a cada rodada<br>\n               <b>Falha:</b> vira servo temporário (age na fase dos servos)<br>\n               <b>3 falhas seguidas:</b> controle PERMANENTE<br>\n               <b>Passar:</b> quebra o controle (volta hostil) — relançar<br>\n               <b>Slot único</b> · não conta para Animar Mortos"
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
