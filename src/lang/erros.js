// Mensagens de RECUSA do servidor ao jogador (etapa 4a do idioma).
//
// Mantido À MÃO: depois da migração o server.py não contém mais o texto
// em português, só a chave, então não há de onde gerar de novo. A chave é
// o slug do texto original, o que garante que a mesma recusa use sempre a
// mesma frase.
window.LANG_ERROS = {
  "erro._circulo_primeiro": {
    "en": "first",
    "pt": "primeiro"
  },
  "erro._circulo_segundo": {
    "en": "second",
    "pt": "segundo"
  },
  "erro._circulo_terceiro": {
    "en": "third",
    "pt": "terceiro"
  },
  "erro._extra_escuridao_limita_alcance": {
    "en": " (darkness limits range to 2 squares — use Darkvision)",
    "pt": " (escuridão limita o alcance a 2q — use Visão no Escuro)"
  },
  "erro._local_bolsa_ou_mao_esquerda": {
    "en": "in the bag or off hand",
    "pt": "na bolsa ou na mão esquerda"
  },
  "erro._local_mao_esquerda": {
    "en": "in the off hand",
    "pt": "na mão esquerda"
  },
  "erro._municao_flechas": {
    "en": "arrows",
    "pt": "flechas"
  },
  "erro._municao_virotes": {
    "en": "bolts",
    "pt": "virotes"
  },
  "erro._regra_diagonal_ate": {
    "en": "; diagonal up to {diagonal}",
    "pt": "; diagonal até {diagonal}"
  },
  "erro._regra_em_linha_reta": {
    "en": " in a straight line",
    "pt": " em linha reta"
  },
  "erro._volta_em_1_rodada": {
    "en": " (returns in {falta} round)",
    "pt": " (volta em {falta} rodada)"
  },
  "erro._volta_em_n_rodadas": {
    "en": " (returns in {falta} rounds)",
    "pt": " (volta em {falta} rodadas)"
  },
  "erro.a_fonte_esta_seca": {
    "en": "💧 The fountain is dry.",
    "pt": "💧 A fonte está seca."
  },
  "erro.a_masmorra_esta_pausada_durante_uma_cena": {
    "en": "The dungeon is paused during a scene.",
    "pt": "A masmorra está pausada durante uma cena."
  },
  "erro.a_porta_esta_fechada_clique_nela_para_ab": {
    "en": "🚪 The door is closed. Click it to open.",
    "pt": "🚪 A porta está fechada. Clique nela para abri-la."
  },
  "erro.a_viagem_ainda_leva_rodadas": {
    "en": "The trip still takes {rodadas} round(s).",
    "pt": "A viagem ainda leva {rodadas} rodada(s)."
  },
  "erro.acao_bonus_ja_usada_neste_turno": {
    "en": "Bonus action already used this turn.",
    "pt": "Ação bônus já usada neste turno."
  },
  "erro.acao_principal_ja_usada_neste_turno": {
    "en": "Main action already used this turn.",
    "pt": "Ação principal já usada neste turno."
  },
  "erro.agarrado_por_captor_nao_pode_se_mover": {
    "en": "Grappled by {captor} — can't move.",
    "pt": "Agarrado por {captor} — não pode se mover."
  },
  "erro.aliado_ainda_esta_vivo": {
    "en": "{aliado} is still alive.",
    "pt": "{aliado} ainda está vivo."
  },
  "erro.aliado_fora_do_alcance": {
    "en": "Ally out of range.",
    "pt": "Aliado fora do alcance."
  },
  "erro.aliado_fora_do_alcance_4_casas": {
    "en": "Ally out of range (4 squares).",
    "pt": "Aliado fora do alcance (4 casas)."
  },
  "erro.aliado_fora_do_raio_de_quadrados": {
    "en": "Ally out of the {raio}-square radius.",
    "pt": "Aliado fora do raio de {raio} quadrados."
  },
  "erro.aliado_invalido": {
    "en": "Invalid ally.",
    "pt": "Aliado inválido."
  },
  "erro.aliado_nao_carrega_essa_maldicao": {
    "en": "{aliado} doesn't carry that curse.",
    "pt": "{aliado} não carrega essa maldição."
  },
  "erro.aliado_nao_encontrado": {
    "en": "Ally not found.",
    "pt": "Aliado não encontrado."
  },
  "erro.aliado_nao_esta_amaldicoado": {
    "en": "{aliado} is not cursed.",
    "pt": "{aliado} não está amaldiçoado."
  },
  "erro.aliado_nao_esta_doente": {
    "en": "{aliado} is not sick.",
    "pt": "{aliado} não está doente."
  },
  "erro.aliado_nao_esta_envenenado": {
    "en": "{aliado} is not poisoned.",
    "pt": "{aliado} não está envenenado."
  },
  "erro.aliado_nao_esta_petrificado": {
    "en": "{aliado} is not petrified.",
    "pt": "{aliado} não está petrificado."
  },
  "erro.alvo_de_area_invalido": {
    "en": "Invalid area target.",
    "pt": "Alvo de área inválido."
  },
  "erro.alvo_desapareceu_nas_sombras": {
    "en": "🌫️ {alvo} vanished into the shadows — immune to ranged attacks!",
    "pt": "🌫️ {alvo} desapareceu nas sombras — imune a ataques à distância!"
  },
  "erro.alvo_do_requiem_invalido": {
    "en": "Invalid Requiem target.",
    "pt": "Alvo do Réquiem inválido."
  },
  "erro.alvo_fora_da_area_ou_sopro_sem_usos_em_r": {
    "en": "Target outside the area, or the breath weapon has no uses left/is on cooldown.",
    "pt": "Alvo fora da área, ou sopro sem usos/em recarga."
  },
  "erro.alvo_fora_de_alcance": {
    "en": "Target out of range.",
    "pt": "Alvo fora de alcance."
  },
  "erro.alvo_fora_de_alcance_aproxime_diagonal": {
    "en": "⚠ {alvo} is out of range! Get closer (1 square, diagonals included).",
    "pt": "⚠ {alvo} está fora de alcance! Aproxime-se (1 quadrado, inclusive diagonal)."
  },
  "erro.alvo_fora_de_alcance_aproxime_ortogonal": {
    "en": "⚠ {alvo} is out of range! Get closer (1 orthogonal square).",
    "pt": "⚠ {alvo} está fora de alcance! Aproxime-se (1 quadrado ortogonal)."
  },
  "erro.alvo_fora_de_alcance_de_arremesso": {
    "en": "⚠ {alvo} out of throwing range (max {alcance} squares).",
    "pt": "⚠ {alvo} fora de alcance de arremesso (máx {alcance} quadrados)."
  },
  "erro.alvo_fora_de_alcance_max": {
    "en": "⚠ {alvo} out of range (max {alcance} squares).",
    "pt": "⚠ {alvo} fora de alcance (máx {alcance} quadrados)."
  },
  "erro.alvo_fora_de_alcance_maximo_quadrados": {
    "en": "⚠ {alvo} is out of range! (maximum {alcance} squares{regra}){extra}",
    "pt": "⚠ {alvo} está fora de alcance! (máximo {alcance} quadrados{regra}){extra}"
  },
  "erro.alvo_fora_do_alcance": {
    "en": "Target out of range.",
    "pt": "Alvo fora do alcance."
  },
  "erro.alvo_fora_do_alcance_casas": {
    "en": "Target out of range ({alcance} squares).",
    "pt": "Alvo fora do alcance ({alcance} casas)."
  },
  "erro.alvo_fora_do_alcance_da_lanca": {
    "en": "⚠ {alvo} is out of the spear's reach! (2 squares in a straight line or 1 diagonally)",
    "pt": "⚠ {alvo} está fora do alcance da lança! (2 casas em linha reta ou 1 na diagonal)"
  },
  "erro.alvo_fora_do_alcance_da_magia": {
    "en": "Target out of the spell's range.",
    "pt": "Alvo fora do alcance da magia."
  },
  "erro.alvo_fora_do_alcance_dist_maior_que": {
    "en": "Target out of range ({dist} > {alcance}).",
    "pt": "Alvo fora do alcance ({dist} > {alcance})."
  },
  "erro.alvo_fora_do_alcance_maximo_q": {
    "en": "Target out of range — maximum {alcance} squares.",
    "pt": "Alvo fora do alcance — máximo {alcance}q."
  },
  "erro.alvo_fora_do_alcance_maximo_quadrados_prov": {
    "en": "Target out of range — maximum {alcance} squares.",
    "pt": "Alvo fora do alcance — máximo {alcance} quadrados."
  },
  "erro.alvo_fora_do_alcance_ou_maldicao_sem_uso": {
    "en": "Target out of range, or the curse has no uses left/is on cooldown.",
    "pt": "Alvo fora do alcance, ou maldição sem usos/em recarga."
  },
  "erro.alvo_invalido": {
    "en": "Invalid target.",
    "pt": "Alvo inválido."
  },
  "erro.alvo_invalido_para_esta_magia": {
    "en": "Invalid target for this spell.",
    "pt": "Alvo inválido para esta magia."
  },
  "erro.alvo_ja_esta_morto": {
    "en": "Target is already dead.",
    "pt": "Alvo já está morto."
  },
  "erro.alvo_nao_encontrado": {
    "en": "Target not found.",
    "pt": "Alvo não encontrado."
  },
  "erro.alvo_nao_esta_adjacente": {
    "en": "Target is not adjacent.",
    "pt": "Alvo não está adjacente."
  },
  "erro.animado_invalido": {
    "en": "Invalid minion.",
    "pt": "Animado inválido."
  },
  "erro.apenas_henrique_pode_usar_esta_habilidad": {
    "en": "Only Henrique can use this ability.",
    "pt": "Apenas Henrique pode usar esta habilidade."
  },
  "erro.apenas_mago_ou_clerigo_conseguem_usar_pe": {
    "en": "Only the mage or cleric can use magic scrolls.",
    "pt": "Apenas mago ou clérigo conseguem usar pergaminhos mágicos."
  },
  "erro.apenas_o_anfitriao_pode_ajustar_este_pon": {
    "en": "Only the host can adjust this point.",
    "pt": "Apenas o anfitrião pode ajustar este ponto."
  },
  "erro.apenas_o_anfitriao_pode_ajustar_os_ponto": {
    "en": "Only the host can adjust the map points.",
    "pt": "Apenas o anfitrião pode ajustar os pontos do mapa."
  },
  "erro.apenas_o_anfitriao_pode_entrar_na_masmor": {
    "en": "Only the host can enter the dungeon.",
    "pt": "Apenas o anfitrião pode entrar na masmorra."
  },
  "erro.apenas_o_anfitriao_pode_escolher_o_desti": {
    "en": "Only the host can choose the travel destination.",
    "pt": "Apenas o anfitrião pode escolher o destino da viagem."
  },
  "erro.apenas_o_anfitriao_pode_iniciar": {
    "en": "Only the host can start.",
    "pt": "Apenas o anfitrião pode iniciar."
  },
  "erro.apenas_o_anfitriao_pode_iniciar_uma_expe": {
    "en": "Only the host can start an expedition.",
    "pt": "Apenas o anfitrião pode iniciar uma expedição."
  },
  "erro.apenas_o_bardo_usa_instrumentos": {
    "en": "Only the bard uses instruments.",
    "pt": "Apenas o bardo usa instrumentos."
  },
  "erro.apenas_o_mago_ou_clerigo_comanda_servos": {
    "en": "Only the mage or cleric commands minions.",
    "pt": "Apenas o mago ou clérigo comanda servos."
  },
  "erro.apenas_pedro_pode_usar_animar_mortos": {
    "en": "Only Pedro can use Animate Dead.",
    "pt": "Apenas Pedro pode usar Animar Mortos."
  },
  "erro.apenas_pedro_pode_usar_habilidade": {
    "en": "Only Pedro can use {habilidade}.",
    "pt": "Apenas Pedro pode usar {habilidade}."
  },
  "erro.aproxime_se_da_escada_de_entrada_para_sa": {
    "en": "Get closer to the entrance stairs to exit.",
    "pt": "Aproxime-se da escada de entrada para sair."
  },
  "erro.aproxime_se_do_prisioneiro": {
    "en": "Get closer to the prisoner.",
    "pt": "Aproxime-se do prisioneiro."
  },
  "erro.arma_de_2_maos_desequipe_antes_de_usar_item": {
    "en": "You're wielding a two-handed weapon — unequip it before using {item}.",
    "pt": "Você empunha uma arma de 2 mãos — desequipe-a antes de usar {item}."
  },
  "erro.armadilha_invalida": {
    "en": "Invalid trap.",
    "pt": "Armadilha inválida."
  },
  "erro.bau_nao_encontrado": {
    "en": "Chest not found.",
    "pt": "Baú não encontrado."
  },
  "erro.cadaver_invalido_ou_ja_consumido": {
    "en": "Invalid corpse, or already consumed.",
    "pt": "Cadáver inválido ou já consumido."
  },
  "erro.caminho_bloqueado": {
    "en": "Path blocked.",
    "pt": "Caminho bloqueado."
  },
  "erro.caminho_bloqueado_para_o_prisioneiro": {
    "en": "Path blocked for the prisoner.",
    "pt": "Caminho bloqueado para o prisioneiro."
  },
  "erro.caminho_bloqueado_para_o_servo": {
    "en": "Path blocked for the minion.",
    "pt": "Caminho bloqueado para o servo."
  },
  "erro.campanha_invalida": {
    "en": "Invalid campaign: {motivo}",
    "pt": "Campanha inválida: {motivo}"
  },
  "erro.casa_ocupada_ou_invalida_para_implantar": {
    "en": "Square occupied or invalid to deploy on.",
    "pt": "Casa ocupada ou inválida para implantar."
  },
  "erro.cego_nao_pode_usar_ataques_a_distancia": {
    "en": "🙈 Blinded — can't use ranged attacks!",
    "pt": "🙈 Cego — não pode usar ataques à distância!"
  },
  "erro.cena_nao_encontrada": {
    "en": "Scene not found.",
    "pt": "Cena não encontrada."
  },
  "erro.centro_da_bola_de_fogo_fora_do_alcance": {
    "en": "Fireball's center out of range ({dist} > {alcance}).",
    "pt": "Centro da Bola de Fogo fora do alcance ({dist} > {alcance})."
  },
  "erro.centro_da_magia_fora_do_alcance": {
    "en": "Spell's center out of range ({dist} > {alcance}).",
    "pt": "Centro da magia fora do alcance ({dist} > {alcance})."
  },
  "erro.centro_de_area_invalido": {
    "en": "Invalid area center.",
    "pt": "Centro de área inválido."
  },
  "erro.centro_fora_de_alcance_max": {
    "en": "⚠ Center out of range (max {alcance} squares).",
    "pt": "⚠ Centro fora de alcance (máx {alcance} quadrados)."
  },
  "erro.centro_fora_do_alcance_dist_maior_que": {
    "en": "Center out of range ({dist} > {alcance}).",
    "pt": "Centro fora do alcance ({dist} > {alcance})."
  },
  "erro.classe_em_uso_em_outra_sala": {
    "en": "{classe} is already in use in another room.",
    "pt": "{classe} já está em uso em outra sala."
  },
  "erro.classe_ja_escolhida_por_outro_jogador": {
    "en": "Class already chosen by another player.",
    "pt": "Classe já escolhida por outro jogador."
  },
  "erro.coloque_a_armadilha_na_sua_casa_ou_casa": {
    "en": "Place the trap on your square or an adjacent one.",
    "pt": "Coloque a armadilha na sua casa ou casa adjacente."
  },
  "erro.comando_so_pode_ter_um_monstro_como_alvo": {
    "en": "Command can only target a monster.",
    "pt": "Comando só pode ter um monstro como alvo."
  },
  "erro.conclua_ou_pule_a_cena_antes_de_entrar_n": {
    "en": "Finish or skip the scene before entering the dungeon.",
    "pt": "Conclua ou pule a cena antes de entrar na masmorra."
  },
  "erro.conversa_bloqueada_requer": {
    "en": "Conversation locked: requires ",
    "pt": "Conversa bloqueada: requer "
  },
  "erro.conversa_nao_encontrada": {
    "en": "Conversation not found.",
    "pt": "Conversa não encontrada."
  },
  "erro.coordenadas_do_mapa_invalidas": {
    "en": "Invalid map coordinates.",
    "pt": "Coordenadas do mapa inválidas."
  },
  "erro.curar_licantropia_no_estagio_iv_exige_o": {
    "en": "Curing Lycanthropy at stage IV requires double the hunger and thirst.",
    "pt": "Curar Licantropia no estágio IV exige o dobro de fome e sede."
  },
  "erro.desative_a_cancao_atual_antes_de_trocar": {
    "en": "Turn off the current song before changing the attributes.",
    "pt": "Desative a canção atual antes de trocar os atributos."
  },
  "erro.destino_de_aventura_invalido": {
    "en": "Invalid adventure destination.",
    "pt": "Destino de aventura inválido."
  },
  "erro.destino_inalcancavel": {
    "en": "Destination unreachable.",
    "pt": "Destino inalcançável."
  },
  "erro.destino_indisponivel": {
    "en": "Destination unavailable: ",
    "pt": "Destino indisponível: "
  },
  "erro.destino_invalido": {
    "en": "Invalid destination.",
    "pt": "Destino inválido."
  },
  "erro.direcao_invalida_para_o_jato_de_ar": {
    "en": "Invalid direction for Gust of Wind.",
    "pt": "Direção inválida para o Jato de Ar."
  },
  "erro.direcao_invalida_para_o_relampago": {
    "en": "Invalid direction for Lightning Bolt.",
    "pt": "Direção inválida para o Relâmpago."
  },
  "erro.e_preciso_pelo_menos_1_heroi_para_inicia": {
    "en": "At least 1 hero is needed to start.",
    "pt": "É preciso pelo menos 1 herói para iniciar."
  },
  "erro.em_ultimo_esforco_voce_nao_pode_se_curar": {
    "en": "🔥 You can't heal yourself during Last Stand!",
    "pt": "🔥 Em Último Esforço você não pode se curar!"
  },
  "erro.encerre_seu_turno_primeiro_para_abrir_o": {
    "en": "End your turn first to open the minions' turn.",
    "pt": "Encerre seu turno primeiro para abrir o turno dos servos."
  },
  "erro.encerre_seu_turno_primeiro_para_atacar_c": {
    "en": "End your turn first to attack with the minions.",
    "pt": "Encerre seu turno primeiro para atacar com os servos."
  },
  "erro.encerre_seu_turno_primeiro_para_mover_o": {
    "en": "End your turn first to move the prisoner.",
    "pt": "Encerre seu turno primeiro para mover o prisioneiro."
  },
  "erro.encerre_seu_turno_primeiro_para_mover_os": {
    "en": "End your turn first to move the minions.",
    "pt": "Encerre seu turno primeiro para mover os servos."
  },
  "erro.erro_interno": {
    "en": "Internal error: {tipo}",
    "pt": "Erro interno: {tipo}"
  },
  "erro.escolha_exatamente_2_magias_de_1o_circul": {
    "en": "Choose exactly 2 first-circle spells.",
    "pt": "Escolha exatamente 2 magias de 1º círculo."
  },
  "erro.escolha_invalida": {
    "en": "Invalid choice.",
    "pt": "Escolha inválida."
  },
  "erro.escolha_pelo_menos_um_atributo_para_a_ca": {
    "en": "Choose at least one attribute for the song.",
    "pt": "Escolha pelo menos um atributo para a canção."
  },
  "erro.escolha_pelo_menos_um_bonus": {
    "en": "Choose at least one bonus.",
    "pt": "Escolha pelo menos um bônus."
  },
  "erro.escolha_sua_nova_magia_antes_de_encerrar": {
    "en": "Choose your new spell before ending the turn.",
    "pt": "Escolha sua nova magia antes de encerrar o turno."
  },
  "erro.escolha_um_aliado_vivo": {
    "en": "Choose a living ally.",
    "pt": "Escolha um aliado vivo."
  },
  "erro.escolha_um_aliado_vivo_nao_pode_ser_voce": {
    "en": "Choose a living ally (can't be you).",
    "pt": "Escolha um aliado vivo (não pode ser você)."
  },
  "erro.escolha_um_alvo_vivo_nao_pode_ser_voce": {
    "en": "Choose a living target (can't be you).",
    "pt": "Escolha um alvo vivo (não pode ser você)."
  },
  "erro.escolha_um_destino_no_mapa_do_mundo_para": {
    "en": "Choose a destination on the world map to start a dungeon.",
    "pt": "Escolha um destino no mapa do mundo para iniciar uma masmorra."
  },
  "erro.escolha_um_veneno_para_a_armadilha": {
    "en": "Choose a poison for the trap.",
    "pt": "Escolha um veneno para a armadilha."
  },
  "erro.escolha_uma_casa_adjacente_para_o_bau": {
    "en": "Choose an adjacent square for the chest.",
    "pt": "Escolha uma casa adjacente para o baú."
  },
  "erro.escolha_uma_direcao_para_a_nota_cortante": {
    "en": "Choose a direction for the runic Cutting Note.",
    "pt": "Escolha uma direção para a Nota Cortante rúnica."
  },
  "erro.escolha_uma_direcao_para_o_chamado": {
    "en": "Choose a direction for the General's Call.",
    "pt": "Escolha uma direção para o Chamado."
  },
  "erro.escombros_bloqueiam_o_caminho": {
    "en": "Rubble blocks the path.",
    "pt": "Escombros bloqueiam o caminho."
  },
  "erro.essa_casa_esta_ocupada_ou_bloqueada_para": {
    "en": "That square is occupied or blocked for the chest.",
    "pt": "Essa casa está ocupada ou bloqueada para o baú."
  },
  "erro.essa_maldicao_nao_esta_ativa": {
    "en": "That curse isn't active.",
    "pt": "Essa maldição não está ativa."
  },
  "erro.esse_jogador_ainda_esta_conectado": {
    "en": "That player is still connected.",
    "pt": "Esse jogador ainda está conectado."
  },
  "erro.esse_personagem_e_de_outro_jogador_neste": {
    "en": "This character belongs to another player in this game.",
    "pt": "Esse personagem é de outro jogador neste jogo."
  },
  "erro.esta_campanha_nao_aceita_novos_jogadores": {
    "en": "This campaign isn't accepting new players.",
    "pt": "Esta campanha não aceita novos jogadores."
  },
  "erro.esta_cena_nao_esta_mais_ativa": {
    "en": "This scene is no longer active.",
    "pt": "Esta cena não está mais ativa."
  },
  "erro.esta_conversa_ja_foi_concluida": {
    "en": "This conversation has already been completed.",
    "pt": "Esta conversa já foi concluída."
  },
  "erro.esta_magia_nao_possui_uso_manual_neste_t": {
    "en": "This spell has no manual use here.",
    "pt": "Esta magia não possui uso manual neste teste."
  },
  "erro.esta_magia_nao_tem_uso_manual": {
    "en": "This spell has no manual use.",
    "pt": "Esta magia não tem uso manual."
  },
  "erro.esta_pocao_ja_nao_possui_doses": {
    "en": "This potion has no doses left.",
    "pt": "Esta poção já não possui doses."
  },
  "erro.esta_tecnica_nao_e_exclusiva": {
    "en": "This technique isn't exclusive.",
    "pt": "Esta técnica não é exclusiva."
  },
  "erro.estas_chamas_fogo_grego_nao_se_apagam_co": {
    "en": "🟢 These flames (Greek Fire) don't go out with water — spend your action to put them out!",
    "pt": "🟢 Estas chamas (Fogo Grego) não se apagam com água — gaste sua ação para apagá-las!"
  },
  "erro.este_aprimoramento_nao_e_da_sua_classe": {
    "en": "This upgrade isn't for your class.",
    "pt": "Este aprimoramento não é da sua classe."
  },
  "erro.este_destino_ainda_nao_possui_uma_masmor": {
    "en": "This destination doesn't have a dungeon yet.",
    "pt": "Este destino ainda não possui uma masmorra."
  },
  "erro.este_golpe_nao_tem_mais_cargas_neste_tur": {
    "en": "This strike has no charges left this turn.",
    "pt": "Este golpe não tem mais cargas neste turno."
  },
  "erro.este_inimigo_ja_esta_provocado": {
    "en": "This enemy is already taunted.",
    "pt": "Este inimigo já está provocado."
  },
  "erro.este_item_e_consumivel_use_o_durante_o_c": {
    "en": "This item is a consumable — use it during combat!",
    "pt": "Este item é consumível — use-o durante o combate!"
  },
  "erro.este_item_nao_tem_efeito_em_monstros": {
    "en": "This item has no effect on monsters.",
    "pt": "Este item não tem efeito em monstros."
  },
  "erro.este_monstro_ja_agiu_neste_turno": {
    "en": "This monster has already acted this turn.",
    "pt": "Este monstro já agiu neste turno."
  },
  "erro.este_monstro_ja_usou_a_acao_bonus": {
    "en": "This monster has already used its bonus action.",
    "pt": "Este monstro já usou a ação bônus."
  },
  "erro.este_monstro_ja_usou_a_acao_principal": {
    "en": "This monster has already used its main action.",
    "pt": "Este monstro já usou a ação principal."
  },
  "erro.este_objeto_nao_possui_mecanismo": {
    "en": "This object has no mechanism.",
    "pt": "Este objeto não possui mecanismo."
  },
  "erro.este_servo_esta_dormindo": {
    "en": "🌙 This minion is asleep.",
    "pt": "🌙 Este servo está dormindo."
  },
  "erro.este_servo_esta_sob_controle_de_um_necro": {
    "en": "💀 This minion is under a necromancer's control!",
    "pt": "💀 Este servo está sob controle de um necromante!"
  },
  "erro.faca_login_para_escolher_um_personagem_n": {
    "en": "Log in to choose a character in this game.",
    "pt": "Faça login para escolher um personagem neste jogo."
  },
  "erro.fome_insuficiente_precisa": {
    "en": "Not enough food — needs 🍖{fome}.",
    "pt": "Fome insuficiente — precisa 🍖{fome}."
  },
  "erro.fome_sede_insuficientes": {
    "en": "Insufficient hunger/thirst.",
    "pt": "Fome/sede insuficientes."
  },
  "erro.frequentador_nao_encontrado": {
    "en": "Patron not found.",
    "pt": "Frequentador não encontrado."
  },
  "erro.golpe_brutal_em_recarga": {
    "en": "Brutal Strike on cooldown.",
    "pt": "Golpe Brutal em recarga."
  },
  "erro.golpe_sagrado_ja_esta_ativo": {
    "en": "Holy Strike is already active.",
    "pt": "Golpe Sagrado já está ativo."
  },
  "erro.guerreiro_da_luz_permite_atributos_ativos": {
    "en": "Warrior of Light allows {max_atributos} active attribute(s) — upgrade at the Guild.",
    "pt": "Guerreiro da Luz permite {max_atributos} atributo(s) ativo(s) — evolua na Guilda."
  },
  "erro.ha_um_objeto_bloqueando_o_caminho": {
    "en": "There's an object blocking the path.",
    "pt": "Há um objeto bloqueando o caminho."
  },
  "erro.habilidade_invalida": {
    "en": "Invalid ability.",
    "pt": "Habilidade inválida."
  },
  "erro.habilidade_livre_invalida": {
    "en": "Invalid free ability.",
    "pt": "Habilidade livre inválida."
  },
  "erro.habilidade_nao_ativavel_manualmente_ia_a": {
    "en": "Ability can't be activated manually (AI only).",
    "pt": "Habilidade não ativável manualmente (IA apenas)."
  },
  "erro.habilidade_passiva": {
    "en": "{habilidade} is passive — no need to activate.",
    "pt": "{habilidade} é passiva — não precisa ativar."
  },
  "erro.habilidade_sem_usos_ou_em_recarga": {
    "en": "Ability has no uses left or is on cooldown.",
    "pt": "Habilidade sem usos ou em recarga."
  },
  "erro.hp_ja_esta_no_maximo": {
    "en": "HP is already at maximum.",
    "pt": "HP já está no máximo."
  },
  "erro.instrumento_de_2_maos_exige_concentracao": {
    "en": "A two-handed instrument requires concentration — you've already used your action.",
    "pt": "Instrumento de 2 mãos exige concentração — você já usou sua ação."
  },
  "erro.instrumento_em_desenvolvimento": {
    "en": "Instrument still in development.",
    "pt": "Instrumento em desenvolvimento."
  },
  "erro.inventario_cheio": {
    "en": "Inventory full!",
    "pt": "Inventário cheio!"
  },
  "erro.inventario_cheio_e_mao_s_ocupada_s_abra": {
    "en": "Inventory full and hand(s) occupied — free up space to buy.",
    "pt": "Inventário cheio e mão(s) ocupada(s) — abra espaço para comprar."
  },
  "erro.inventario_cheio_e_slot_ocupado_abra_esp": {
    "en": "Inventory full and slot occupied — free up space to buy.",
    "pt": "Inventário cheio e slot ocupado — abra espaço para comprar."
  },
  "erro.inventario_cheio_e_slot_ocupado_abra_esp_2": {
    "en": "Inventory full and slot occupied — free up space first.",
    "pt": "Inventário cheio e slot ocupado — abra espaço primeiro."
  },
  "erro.inventario_cheio_max_itens": {
    "en": "Inventory full (max {max_itens} items)!",
    "pt": "Inventário cheio (máx {max_itens} itens)!"
  },
  "erro.inventario_cheio_nao_ha_espaco_para_dese": {
    "en": "Inventory full — no room to unequip.",
    "pt": "Inventário cheio — não há espaço para desequipar."
  },
  "erro.item_da_guilda_desconhecido": {
    "en": "Unknown guild item.",
    "pt": "Item da guilda desconhecido."
  },
  "erro.item_e_arma_de_2_maos_desequipe_escudo": {
    "en": "{item} is a two-handed weapon — unequip the shield or 2nd weapon first.",
    "pt": "{item} é arma de 2 mãos — desequipe o escudo ou a 2ª arma primeiro."
  },
  "erro.item_invalido": {
    "en": "Invalid item.",
    "pt": "Item inválido."
  },
  "erro.item_ja_pedido_nesta_visita": {
    "en": "You already ordered {item} on this visit to the city.",
    "pt": "Você já pediu {item} nesta visita à cidade."
  },
  "erro.item_nao_arremessavel": {
    "en": "Item can't be thrown.",
    "pt": "Item não arremessável."
  },
  "erro.item_nao_encontrado": {
    "en": "Item not found.",
    "pt": "Item não encontrado."
  },
  "erro.item_nao_encontrado_na_bolsa": {
    "en": "Item not found in the bag.",
    "pt": "Item não encontrado na bolsa."
  },
  "erro.item_nao_encontrado_na_mochila": {
    "en": "Item not found in the bag.",
    "pt": "Item não encontrado na mochila."
  },
  "erro.item_nao_encontrado_no_inventario": {
    "en": "Item not found in the inventory.",
    "pt": "Item não encontrado no inventário."
  },
  "erro.item_nao_usavel_pelo_mestre": {
    "en": "Item can't be used by the game master.",
    "pt": "Item não usável pelo mestre."
  },
  "erro.ja_existe_um_mestre_nesta_sala": {
    "en": "There's already a game master in this room.",
    "pt": "Já existe um mestre nesta sala."
  },
  "erro.ja_existe_uma_armadilha_nessa_casa": {
    "en": "There's already a trap on that square.",
    "pt": "Já existe uma armadilha nessa casa."
  },
  "erro.jogador_nao_encontrado_nesta_sala": {
    "en": "Player not found in this room.",
    "pt": "Jogador não encontrado nesta sala."
  },
  "erro.jogo_ja_iniciado": {
    "en": "Game already started.",
    "pt": "Jogo já iniciado."
  },
  "erro.linha_de_descarga_bloqueada_por_parede": {
    "en": "⚡ Discharge line blocked by a wall.",
    "pt": "⚡ Linha de descarga bloqueada por parede."
  },
  "erro.magia_ainda_em_desenvolvimento": {
    "en": "{icone} {magia} is still in development.",
    "pt": "{icone} {magia} ainda está em desenvolvimento."
  },
  "erro.magia_desconhecida": {
    "en": "Unknown spell.",
    "pt": "Magia desconhecida."
  },
  "erro.magia_do_pergaminho_desconhecida": {
    "en": "Unknown scroll spell.",
    "pt": "Magia do pergaminho desconhecida."
  },
  "erro.magia_do_pergaminho_nao_disponivel": {
    "en": "Scroll spell not available.",
    "pt": "Magia do pergaminho não disponível."
  },
  "erro.magia_indisponivel_para_este_monstro": {
    "en": "Spell not available for this monster.",
    "pt": "Magia indisponível para este monstro."
  },
  "erro.magia_invalida_para_este_circulo_classe": {
    "en": "Invalid spell for this circle/class.",
    "pt": "Magia inválida para este círculo/classe."
  },
  "erro.magia_invalida_para_sua_classe_circulo": {
    "en": "Invalid spell for your class/circle.",
    "pt": "Magia inválida para sua classe/círculo."
  },
  "erro.magia_sem_usos_ou_em_recarga": {
    "en": "Spell has no uses left or is on cooldown.",
    "pt": "Magia sem usos ou em recarga."
  },
  "erro.magos_e_clerigos_devem_escolher_2_magias": {
    "en": "Mages and clerics must choose 2 spells before starting.",
    "pt": "Magos e clérigos devem escolher 2 magias antes de iniciar."
  },
  "erro.mao_esquerda_ocupada_e_inventario_cheio": {
    "en": "Left hand occupied and inventory full!",
    "pt": "Mão esquerda ocupada e inventário cheio!"
  },
  "erro.masmorra_invalida": {
    "en": "Invalid dungeon: {motivo}",
    "pt": "Masmorra inválida: {motivo}"
  },
  "erro.mestre_dos_mortos_so_pode_ser_usado_na_p": {
    "en": "Master of the Dead can only be used on the first action and requires room to summon.",
    "pt": "Mestre dos Mortos só pode ser usado na primeira ação e requer espaço para invocar."
  },
  "erro.monstro_do_bau_armadilha_invalido": {
    "en": "Invalid chest-trap monster.",
    "pt": "Monstro do baú-armadilha inválido."
  },
  "erro.monstro_sem_movimento_neste_turno": {
    "en": "Monster has no movement left this turn.",
    "pt": "Monstro sem movimento neste turno."
  },
  "erro.movimento_insuficiente_casa_custa": {
    "en": "Not enough movement: this tile costs {custo}.",
    "pt": "Movimento insuficiente: esta casa custa {custo}."
  },
  "erro.mp_insuficiente": {
    "en": "Insufficient MP.",
    "pt": "MP insuficiente."
  },
  "erro.muito_longe_do_bau": {
    "en": "Too far from the chest!",
    "pt": "Muito longe do baú!"
  },
  "erro.muito_longe_do_item": {
    "en": "Too far from the item!",
    "pt": "Muito longe do item!"
  },
  "erro.muito_longe_do_objeto": {
    "en": "Too far from the object!",
    "pt": "Muito longe do objeto!"
  },
  "erro.nada_equipado_nesse_slot": {
    "en": "Nothing equipped in that slot.",
    "pt": "Nada equipado nesse slot."
  },
  "erro.nao_e_o_seu_turno": {
    "en": "Not your turn.",
    "pt": "Não é o seu turno."
  },
  "erro.nao_e_possivel_ativar_este_mecanismo": {
    "en": "Can't activate this mechanism.",
    "pt": "Não é possível ativar este mecanismo."
  },
  "erro.nao_foi_possivel_envenenar_a_arma": {
    "en": "Couldn't poison the weapon.",
    "pt": "Não foi possível envenenar a arma."
  },
  "erro.nao_foi_possivel_salvar_o_ponto_da_cidad": {
    "en": "Couldn't save the town point.",
    "pt": "Não foi possível salvar o ponto da cidade."
  },
  "erro.nao_foi_possivel_salvar_os_pontos_do_map": {
    "en": "Couldn't save the map points.",
    "pt": "Não foi possível salvar os pontos do mapa."
  },
  "erro.nao_ha_como_sair_desta_masmorra": {
    "en": "There's no way out of this dungeon.",
    "pt": "Não há como sair desta masmorra."
  },
  "erro.nao_ha_espaco_livre_ao_lado_para_a_armad": {
    "en": "No free space nearby for the trap to trigger.",
    "pt": "Não há espaço livre ao lado para a armadilha disparar."
  },
  "erro.nao_ha_prisioneiro_para_libertar": {
    "en": "No prisoner to free.",
    "pt": "Não há prisioneiro para libertar."
  },
  "erro.nao_ha_prisioneiro_para_mover": {
    "en": "No prisoner to move.",
    "pt": "Não há prisioneiro para mover."
  },
  "erro.nenhum_ataque_recente_para_rerolar": {
    "en": "No recent attack to reroll.",
    "pt": "Nenhum ataque recente para rerolar."
  },
  "erro.nenhum_inimigo_na_linha": {
    "en": "No enemy in the line.",
    "pt": "Nenhum inimigo na linha."
  },
  "erro.nenhum_inimigo_no_alcance": {
    "en": "No enemy in range.",
    "pt": "Nenhum inimigo no alcance."
  },
  "erro.nenhum_inimigo_no_cone": {
    "en": "No enemy in the cone.",
    "pt": "Nenhum inimigo no cone."
  },
  "erro.nenhum_inimigo_para_os_animados_atacarem": {
    "en": "No enemy for the minions to attack.",
    "pt": "Nenhum inimigo para os animados atacarem."
  },
  "erro.nenhum_instrumento_equipado_mao_do_escud": {
    "en": "No instrument equipped (off hand).",
    "pt": "Nenhum instrumento equipado (mão do escudo)."
  },
  "erro.nenhum_item_neste_slot": {
    "en": "No item in this slot.",
    "pt": "Nenhum item neste slot."
  },
  "erro.nenhum_ponto_valido_foi_informado": {
    "en": "No valid point was given.",
    "pt": "Nenhum ponto válido foi informado."
  },
  "erro.nenhuma_arma_para_vender": {
    "en": "No weapon to sell.",
    "pt": "Nenhuma arma para vender."
  },
  "erro.nenhuma_armadilha_revelada_adjacente_par": {
    "en": "No revealed trap adjacent to disarm.",
    "pt": "Nenhuma armadilha revelada adjacente para desarmar."
  },
  "erro.nenhuma_armadura_para_vender": {
    "en": "No armor to sell.",
    "pt": "Nenhuma armadura para vender."
  },
  "erro.nenhuma_coordenada_valida_foi_informada": {
    "en": "No valid coordinate was given.",
    "pt": "Nenhuma coordenada válida foi informada."
  },
  "erro.nenhuma_escolha_de_magia_pendente": {
    "en": "No pending spell choice.",
    "pt": "Nenhuma escolha de magia pendente."
  },
  "erro.nesta_primeira_etapa_a_aventura_parte_de": {
    "en": "In this first stage, the adventure departs from Alva e Luz.",
    "pt": "Nesta primeira etapa, a aventura parte de Alva e Luz."
  },
  "erro.ninguem_agarrado_e_adjacente_para_esta_a": {
    "en": "No one grappled and adjacent for this action.",
    "pt": "Ninguém agarrado e adjacente para esta ação."
  },
  "erro.o_aliado_deve_estar_adjacente_a_voce": {
    "en": "The ally must be adjacent to you.",
    "pt": "O aliado deve estar adjacente a você."
  },
  "erro.o_aliado_precisa_estar_adjacente": {
    "en": "The ally needs to be adjacent.",
    "pt": "O aliado precisa estar adjacente."
  },
  "erro.o_alvo_nao_e_um_morto_vivo": {
    "en": "The target isn't undead.",
    "pt": "O alvo não é um morto-vivo."
  },
  "erro.o_alvo_nao_esta_mais_disponivel": {
    "en": "The target is no longer available.",
    "pt": "O alvo não está mais disponível."
  },
  "erro.o_bau_deve_ser_criado_em_uma_casa_adjace": {
    "en": "The chest must be created on an adjacent tile.",
    "pt": "O baú deve ser criado em uma casa adjacente."
  },
  "erro.o_bau_esta_cheio": {
    "en": "The chest is full.",
    "pt": "O baú está cheio."
  },
  "erro.o_cadaver_deve_estar_a_ate_3_casas_de_pe": {
    "en": "The corpse must be within 3 tiles of Pedro.",
    "pt": "O cadáver deve estar a até 3 casas de Pedro."
  },
  "erro.o_centro_da_area_precisa_estar_em_uma_ca": {
    "en": "The area's center must be on a valid tile.",
    "pt": "O centro da área precisa estar em uma casa válida."
  },
  "erro.o_elemental_eletrico_ataca_em_linha_reta": {
    "en": "⚡ The electric elemental attacks in a straight line (max 3 tiles).",
    "pt": "⚡ O elemental elétrico ataca em linha reta (máx 3 casas)."
  },
  "erro.o_inimigo_precisa_estar_adjacente": {
    "en": "The enemy needs to be adjacent.",
    "pt": "O inimigo precisa estar adjacente."
  },
  "erro.o_mestre_ainda_esta_conectado": {
    "en": "The game master is still connected.",
    "pt": "O mestre ainda está conectado."
  },
  "erro.o_mestre_desta_campanha_e_fixo_e_tambem": {
    "en": "This campaign's Game Master is fixed and is also the host.",
    "pt": "O Mestre desta campanha é fixo e também é o anfitrião."
  },
  "erro.o_mestre_nao_escolhe_classe_solte_o_pape": {
    "en": "The game master doesn't choose a class. Drop the game master role first.",
    "pt": "O mestre não escolhe classe. Solte o papel de mestre primeiro."
  },
  "erro.o_objeto_esta_vazio": {
    "en": "The object is empty.",
    "pt": "O objeto está vazio."
  },
  "erro.o_refugio_dos_herois_ainda_esta_bloquead": {
    "en": "The Heroes' Refuge is still locked.",
    "pt": "O Refúgio dos Heróis ainda está bloqueado."
  },
  "erro.o_teste_nao_esta_mais_disponivel": {
    "en": "The test is no longer available.",
    "pt": "O teste não está mais disponível."
  },
  "erro.objeto_nao_encontrado": {
    "en": "Object not found.",
    "pt": "Objeto não encontrado."
  },
  "erro.objeto_sem_loot": {
    "en": "Object has no loot.",
    "pt": "Objeto sem loot."
  },
  "erro.os_pontos_da_cidade_so_podem_ser_ajustad": {
    "en": "Town points can only be adjusted in the Editor.",
    "pt": "Os pontos da cidade só podem ser ajustados no Editor."
  },
  "erro.os_pontos_do_mapa_so_podem_ser_ajustados": {
    "en": "Map points can only be adjusted in the Editor.",
    "pt": "Os pontos do mapa só podem ser ajustados no Editor."
  },
  "erro.ouro_insuficiente": {
    "en": "Not enough gold.",
    "pt": "Ouro insuficiente."
  },
  "erro.ouro_insuficiente_2": {
    "en": "Not enough gold!",
    "pt": "Ouro insuficiente!"
  },
  "erro.ouro_insuficiente_precisa": {
    "en": "Not enough gold — needs {ouro}🪙.",
    "pt": "Ouro insuficiente — precisa {ouro}🪙."
  },
  "erro.outro_aventureiro_esta_neste_espaco": {
    "en": "Another adventurer is in this space.",
    "pt": "Outro aventureiro está neste espaço."
  },
  "erro.outro_jogador_ja_fez_a_escolha_do_grupo": {
    "en": "Another player already made the group's choice.",
    "pt": "Outro jogador já fez a escolha do grupo."
  },
  "erro.parede_bloqueia_arremesso": {
    "en": "🧱 A wall blocks the throw to {alvo}!",
    "pt": "🧱 Uma parede bloqueia o arremesso até {alvo}!"
  },
  "erro.parede_bloqueia_lanca_de_gelo": {
    "en": "🧱 A wall blocks Ice Lance's path to {alvo}!",
    "pt": "🧱 Uma parede bloqueia a Lança de Gelo até {alvo}!"
  },
  "erro.parede_bloqueia_linha_de_tiro": {
    "en": "🧱 A wall blocks the line of fire to {alvo}!",
    "pt": "🧱 Uma parede bloqueia a linha de tiro até {alvo}!"
  },
  "erro.pedido_enviado_para_votacao_dos_membros": {
    "en": "Request sent for a vote among active members.",
    "pt": "Pedido enviado para votação dos membros ativos."
  },
  "erro.pergaminho_nao_encontrado": {
    "en": "Scroll not found.",
    "pt": "Pergaminho não encontrado."
  },
  "erro.personagem_nao_conhece_magia": {
    "en": "{personagem} doesn't know {magia}.",
    "pt": "{personagem} não conhece {magia}."
  },
  "erro.ponto_da_cidade_invalido": {
    "en": "Invalid town point.",
    "pt": "Ponto da cidade inválido."
  },
  "erro.posicao_invalida_para_a_armadilha": {
    "en": "Invalid position for the trap.",
    "pt": "Posição inválida para a armadilha."
  },
  "erro.preso_por_captor_impossivel_mover": {
    "en": "⛓️ You are grappled by **{captor}**! You can't move (try to escape on your next turn).",
    "pt": "⛓️ Você está preso por **{captor}**! Impossível se mover (tente escapar no próximo turno)."
  },
  "erro.prisioneiro_sem_movimento_neste_turno": {
    "en": "Prisoner has no movement this turn.",
    "pt": "Prisioneiro sem movimento neste turno."
  },
  "erro.provisoes_insuficientes_ir_e_voltar": {
    "en": "Not enough provisions for the round trip (needs 🍖{fome} and 💧{sede}).",
    "pt": "Provisões insuficientes para ir e voltar (precisa de 🍖{fome} e 💧{sede})."
  },
  "erro.purificacao_requer_contato_adjacente": {
    "en": "Purification requires adjacent contact.",
    "pt": "Purificação requer contato adjacente."
  },
  "erro.purificar_o_item_vinculado_exige_5_de_fo": {
    "en": "Purifying the bound item requires +5 hunger and +5 thirst.",
    "pt": "Purificar o item vinculado exige +5 de fome e +5 de sede."
  },
  "erro.recursos_insuficientes_fome_sede": {
    "en": "Not enough resources 🍖{fome} 💧{sede}.",
    "pt": "Recursos insuficientes 🍖{fome} 💧{sede}."
  },
  "erro.recursos_insuficientes_metamagia": {
    "en": "Not enough resources for metamagic 🍖-{fome} 💧-{sede}.",
    "pt": "Recursos insuficientes p/ metamagia 🍖-{fome} 💧-{sede}."
  },
  "erro.recursos_insuficientes_para_a_expedicao": {
    "en": "Not enough resources for the expedition: ",
    "pt": "Recursos insuficientes para a expedição: "
  },
  "erro.recursos_insuficientes_para_viajar": {
    "en": "Not enough resources to travel: ",
    "pt": "Recursos insuficientes para viajar: "
  },
  "erro.recursos_insuficientes_parenteses_fome_sede": {
    "en": "Not enough resources (🍖-{fome} 💧-{sede}).",
    "pt": "Recursos insuficientes (🍖-{fome} 💧-{sede})."
  },
  "erro.recursos_insuficientes_precisa_fome_sede": {
    "en": "Not enough resources — needs 🍖{fome} 💧{sede}.",
    "pt": "Recursos insuficientes — precisa 🍖{fome} 💧{sede}."
  },
  "erro.requer_antes": {
    "en": "Requires first: {requisito}.",
    "pt": "Requer antes: {requisito}."
  },
  "erro.ressurreicao_requer_contato_adjacente_co": {
    "en": "Resurrection requires adjacent contact with the ally.",
    "pt": "Ressurreição requer contato adjacente com o aliado."
  },
  "erro.richard_nao_pode_se_proteger_com_esta_ha": {
    "en": "Richard can't protect himself with this ability.",
    "pt": "Richard não pode se proteger com esta habilidade."
  },
  "erro.sala_cheia_6_herois_nao_ha_vaga_de_heroi": {
    "en": "Room full (6 heroes) — no hero slot available for you.",
    "pt": "Sala cheia (6 heróis) — não há vaga de herói para você."
  },
  "erro.sala_cheia_maximo_6_herois_1_mestre": {
    "en": "Room full (max 6 heroes + 1 master).",
    "pt": "Sala cheia (máximo 6 heróis + 1 mestre)."
  },
  "erro.sala_nao_encontrada": {
    "en": "Room not found.",
    "pt": "Sala não encontrada."
  },
  "erro.sala_nao_encontrada_para_reconexao": {
    "en": "Room not found for reconnection.",
    "pt": "Sala não encontrada para reconexão."
  },
  "erro.sede_insuficiente_parenteses": {
    "en": "Not enough water (💧-{sede}).",
    "pt": "Sede insuficiente (💧-{sede})."
  },
  "erro.sede_insuficiente_precisa": {
    "en": "Not enough water — needs 💧{sede}.",
    "pt": "Sede insuficiente — precisa 💧{sede}."
  },
  "erro.selecione_uma_casa_adjacente_para_desarm": {
    "en": "Select an adjacent tile to disarm.",
    "pt": "Selecione uma casa adjacente para desarmar."
  },
  "erro.sem_credito_de_oportunidade_disponivel": {
    "en": "No Opportunity credit available.",
    "pt": "Sem crédito de Oportunidade disponível."
  },
  "erro.sem_espaco_adjacente_para_largar": {
    "en": "No adjacent space to drop it.",
    "pt": "Sem espaço adjacente para largar."
  },
  "erro.sem_folego_atacar_sob_cancao": {
    "en": "Not enough stamina to attack while singing — needs 🍖{fome} 💧{sede} (or deactivate the song).",
    "pt": "Sem fôlego para atacar sob a canção — precisa 🍖{fome} 💧{sede} (ou desative a canção)."
  },
  "erro.sem_linha_de_visao_para_o_alvo": {
    "en": "🧱 No line of sight to the target.",
    "pt": "🧱 Sem linha de visão para o alvo."
  },
  "erro.sem_movimentos_restantes": {
    "en": "No movement left.",
    "pt": "Sem movimentos restantes."
  },
  "erro.sem_municao_no_local": {
    "en": "🏹 No {municao} (basic, fire, or silver) {local}!",
    "pt": "🏹 Sem {municao} (básicos, incendiários ou de prata) {local}!"
  },
  "erro.sem_ouro_aqui": {
    "en": "No gold here.",
    "pt": "Sem ouro aqui."
  },
  "erro.sem_ouro_neste_bau": {
    "en": "No gold in this chest.",
    "pt": "Sem ouro neste baú."
  },
  "erro.sem_reforcos_desse_tipo_na_reserva": {
    "en": "No reinforcements of that type in reserve.",
    "pt": "Sem reforços desse tipo na reserva."
  },
  "erro.sem_slot_de_magia_de_circulo": {
    "en": "No {circulo}-circle spell slot{extra}.",
    "pt": "Sem slot de magia de {circulo} círculo{extra}."
  },
  "erro.servo_ja_atacou_neste_turno": {
    "en": "Minion already attacked this turn.",
    "pt": "Servo já atacou neste turno."
  },
  "erro.servo_nao_esta_adjacente_ao_alvo": {
    "en": "Minion isn't adjacent to the target.",
    "pt": "Servo não está adjacente ao alvo."
  },
  "erro.servo_sem_movimento_neste_turno": {
    "en": "Minion has no movement this turn.",
    "pt": "Servo sem movimento neste turno."
  },
  "erro.sessao_de_teste_nao_encontrada_ou_expira": {
    "en": "Test session not found or expired.",
    "pt": "Sessão de teste não encontrada ou expirada."
  },
  "erro.seu_pedido_ja_esta_aguardando_votacao": {
    "en": "Your request is already awaiting a vote.",
    "pt": "Seu pedido já está aguardando votação."
  },
  "erro.silencio_dos_deuses_impede_lancar_magias": {
    "en": "Silence of the Gods prevents casting spells.",
    "pt": "Silêncio dos Deuses impede lançar magias."
  },
  "erro.slot_de_inventario_invalido": {
    "en": "Invalid inventory slot.",
    "pt": "Slot de inventário inválido."
  },
  "erro.slot_de_tecnica_invalido": {
    "en": "Invalid technique slot.",
    "pt": "Slot de técnica inválido."
  },
  "erro.slot_invalido": {
    "en": "Invalid slot.",
    "pt": "Slot inválido."
  },
  "erro.slots_insuficientes_necessarios_disponiv": {
    "en": "Not enough slots — {necessarios} needed, {disponiveis} available.",
    "pt": "Slots insuficientes — {necessarios} necessários, {disponiveis} disponíveis."
  },
  "erro.so_e_possivel_equipar_tecnicas_na_cidade": {
    "en": "Techniques can only be equipped in town.",
    "pt": "Só é possível equipar técnicas na cidade."
  },
  "erro.so_e_possivel_sair_no_seu_turno": {
    "en": "You can only leave on your turn.",
    "pt": "Só é possível sair no seu turno."
  },
  "erro.so_monstros_conjuradores_podem_usar_perg": {
    "en": "Only spellcasting monsters can use scrolls.",
    "pt": "Só monstros conjuradores podem usar pergaminhos."
  },
  "erro.so_nas_sombras_e_fora_de_recarga": {
    "en": "Only while in the shadows and off cooldown.",
    "pt": "Só nas sombras e fora de recarga."
  },
  "erro.so_uma_adaga_pode_ser_empunhada_como_2a": {
    "en": "Only a dagger can be wielded as a 2nd weapon in the off hand.",
    "pt": "Só uma adaga pode ser empunhada como 2ª arma na mão esquerda."
  },
  "erro.somente_o_anfitriao_pode_alterar_o_limit": {
    "en": "Only the host can change the turn limit.",
    "pt": "Somente o anfitrião pode alterar o limite de turno."
  },
  "erro.somente_o_anfitriao_pode_encerrar_a_cena": {
    "en": "Only the host can end the scene.",
    "pt": "Somente o anfitrião pode encerrar a cena."
  },
  "erro.sorte_e_passiva_e_reage_automaticamente": {
    "en": "Luck is passive and triggers automatically when a roll fails.",
    "pt": "Sorte é passiva e reage automaticamente quando uma rolagem falha."
  },
  "erro.sua_classe_nao_escolhe_magias": {
    "en": "Your class doesn't choose spells.",
    "pt": "Sua classe não escolhe magias."
  },
  "erro.sua_classe_nao_lanca_magias_do_grimorio": {
    "en": "Your class doesn't cast spells from the grimoire.",
    "pt": "Sua classe não lança magias do grimório."
  },
  "erro.sua_classe_nao_pode_usar_item": {
    "en": "Your class can't use {item}!",
    "pt": "Sua classe não pode usar {item}!"
  },
  "erro.sua_classe_nao_tem_slot_de_tecnica_exclu": {
    "en": "Your class doesn't have an exclusive technique slot.",
    "pt": "Sua classe não tem slot de técnica exclusiva."
  },
  "erro.tecnica_desconhecida": {
    "en": "Unknown technique.",
    "pt": "Técnica desconhecida."
  },
  "erro.tecnica_e_automatica": {
    "en": "{tecnica} is automatic — it can't be activated manually.",
    "pt": "{tecnica} é automática — não pode ser ativada manualmente."
  },
  "erro.tecnica_em_recarga": {
    "en": "{tecnica} is on cooldown ({rodadas} rounds).",
    "pt": "{tecnica} em recarga ({rodadas} rodadas)."
  },
  "erro.tecnica_exclusiva_vai_no_slot_exclusivo": {
    "en": "Exclusive techniques go in the exclusive slot.",
    "pt": "Técnica exclusiva vai no slot exclusivo."
  },
  "erro.tecnica_ja_preparada": {
    "en": "{tecnica} is already primed for the next effect.",
    "pt": "{tecnica} já está preparada para o próximo efeito."
  },
  "erro.tecnica_nao_equipada": {
    "en": "Technique not equipped.",
    "pt": "Técnica não equipada."
  },
  "erro.templo_cobra_ouro_cura_maldicao": {
    "en": "The Temple charges {preco} gold to cure this curse.",
    "pt": "O Templo cobra {preco} ouro para curar esta maldição."
  },
  "erro.templo_liberta_de_maldicao": {
    "en": "⛪ **{personagem}** was freed from **{maldicao}** ({preco} gold).",
    "pt": "⛪ **{personagem}** foi liberto de **{maldicao}** ({preco} ouro)."
  },
  "erro.teste_invalido": {
    "en": "Invalid test.",
    "pt": "Teste inválido."
  },
  "erro.tipo_de_monstro_invalido": {
    "en": "Invalid monster type.",
    "pt": "Tipo de monstro inválido."
  },
  "erro.tipo_de_purificacao_invalido": {
    "en": "Invalid purification type.",
    "pt": "Tipo de purificação inválido."
  },
  "erro.todas_as_masmorras_deste_destino_ja_fora": {
    "en": "All dungeons for this destination have already been completed.",
    "pt": "Todas as masmorras deste destino já foram concluídas."
  },
  "erro.todos_os_herois_devem_escolher_uma_class": {
    "en": "All heroes must choose a class.",
    "pt": "Todos os heróis devem escolher uma classe."
  },
  "erro.um_inimigo_bloqueia_o_caminho": {
    "en": "An enemy blocks the way!",
    "pt": "Um inimigo bloqueia o caminho!"
  },
  "erro.um_servo_animado_ocupa_este_espaco": {
    "en": "An animated minion occupies this space.",
    "pt": "Um servo animado ocupa este espaço."
  },
  "erro.uma_parede_bloqueia_a_energia_curativa_p": {
    "en": "🧱 A wall blocks the healing energy — you need to see the ally!",
    "pt": "🧱 Uma parede bloqueia a energia curativa — precisa ver o aliado!"
  },
  "erro.uma_parede_bloqueia_a_trajetoria_da_bola": {
    "en": "🧱 A wall blocks Fireball's path!",
    "pt": "🧱 Uma parede bloqueia a trajetória da Bola de Fogo!"
  },
  "erro.uma_parede_bloqueia_a_trajetoria_do_arre": {
    "en": "🧱 A wall blocks the throw's path!",
    "pt": "🧱 Uma parede bloqueia a trajetória do arremesso!"
  },
  "erro.uma_parede_bloqueia_o_arremesso": {
    "en": "A wall blocks the throw.",
    "pt": "Uma parede bloqueia o arremesso."
  },
  "erro.uma_parede_bloqueia_o_raio_congelante": {
    "en": "🧱 A wall blocks Ray of Frost!",
    "pt": "🧱 Uma parede bloqueia o Raio Congelante!"
  },
  "erro.use_o_clique_direito_para_arremessar_est": {
    "en": "Use right-click to throw this item.",
    "pt": "Use o clique direito para arremessar este item."
  },
  "erro.veneno_desconhecido": {
    "en": "Unknown poison.",
    "pt": "Veneno desconhecido."
  },
  "erro.veneno_invalido": {
    "en": "Invalid poison.",
    "pt": "Veneno inválido."
  },
  "erro.veneno_nao_encontrado_na_bolsa": {
    "en": "Poison not found in bag.",
    "pt": "Veneno não encontrado na bolsa."
  },
  "erro.voce_ainda_nao_aprendeu_a_purificar_este": {
    "en": "You haven't learned to purify this affliction yet — upgrade Purification at the Guild.",
    "pt": "Você ainda não aprendeu a purificar este mal — evolua a Purificação na Guilda."
  },
  "erro.voce_empunha_uma_arma_de_2_maos_nao_pode": {
    "en": "You're wielding a 2-handed weapon — you can't use a 2nd weapon.",
    "pt": "Você empunha uma arma de 2 mãos — não pode usar uma 2ª arma."
  },
  "erro.voce_esta_dormindo_e_nao_pode_agir": {
    "en": "🌙 You're asleep and can't act!",
    "pt": "🌙 Você está dormindo e não pode agir!"
  },
  "erro.voce_esta_dormindo_e_nao_pode_lancar_mag": {
    "en": "🌙 You're asleep and can't cast spells!",
    "pt": "🌙 Você está dormindo e não pode lançar magias!"
  },
  "erro.voce_esta_dormindo_e_nao_pode_se_mover": {
    "en": "🌙 You're asleep and can't move!",
    "pt": "🌙 Você está dormindo e não pode se mover!"
  },
  "erro.voce_esta_em_area_de_silencio_nao_pode_c": {
    "en": "🔇 You're in a Silence area — you can't cast!",
    "pt": "🔇 Você está em área de Silêncio — não pode conjurar!"
  },
  "erro.voce_esta_imobilizado_e_nao_pode_se_move": {
    "en": "🕸️ You're immobilized and can't move! End your turn.",
    "pt": "🕸️ Você está imobilizado e não pode se mover! Encerre o turno."
  },
  "erro.voce_esta_numa_area_de_silencio_e_nao_po": {
    "en": "🔇 You're in a Silence area and can't cast spells!",
    "pt": "🔇 Você está numa área de Silêncio e não pode lançar magias!"
  },
  "erro.voce_esta_paralisado_e_nao_pode_agir": {
    "en": "❄️ You're paralyzed and can't act!",
    "pt": "❄️ Você está paralisado e não pode agir!"
  },
  "erro.voce_esta_paralisado_e_nao_pode_lancar_m": {
    "en": "❄️ You're paralyzed and can't cast spells!",
    "pt": "❄️ Você está paralisado e não pode lançar magias!"
  },
  "erro.voce_esta_paralisado_e_nao_pode_se_mover": {
    "en": "❄️ You're paralyzed and can't move!",
    "pt": "❄️ Você está paralisado e não pode se mover!"
  },
  "erro.voce_esta_petrificado_e_nao_pode_agir": {
    "en": "🗿 You're petrified and can't act!",
    "pt": "🗿 Você está petrificado e não pode agir!"
  },
  "erro.voce_esta_petrificado_e_nao_pode_lancar": {
    "en": "🗿 You're petrified and can't cast spells!",
    "pt": "🗿 Você está petrificado e não pode lançar magias!"
  },
  "erro.voce_esta_petrificado_e_nao_pode_se_move": {
    "en": "🗿 You're petrified and can't move!",
    "pt": "🗿 Você está petrificado e não pode se mover!"
  },
  "erro.voce_ja_conhece_essa_magia": {
    "en": "You already know that spell.",
    "pt": "Você já conhece essa magia."
  },
  "erro.voce_ja_esta_em_uma_sala_saia_dela_antes": {
    "en": "You're already in a room. Leave it before entering another.",
    "pt": "Você já está em uma sala. Saia dela antes de entrar em outra."
  },
  "erro.voce_ja_esta_furtivo_a_vela_nao_acumula": {
    "en": "You're already stealthed — the Candle of Darkness doesn't stack with another stealth effect.",
    "pt": "Você já está furtivo — a vela não acumula com outro efeito de furtividade."
  },
  "erro.voce_ja_pode_voltar_a_masmorra": {
    "en": "You can already return to the dungeon.",
    "pt": "Você já pode voltar à masmorra."
  },
  "erro.voce_ja_possui_isto": {
    "en": "You already own this.",
    "pt": "Você já possui isto."
  },
  "erro.voce_ja_tocou_um_instrumento_neste_turno": {
    "en": "You already played an instrument this turn.",
    "pt": "Você já tocou um instrumento neste turno."
  },
  "erro.voce_nao_aprendeu_a_formula_de_armadilha": {
    "en": "You haven't learned the {armadilha} formula yet — buy it at the Guild.",
    "pt": "Você ainda não aprendeu a fórmula de {armadilha} — compre na Guilda."
  },
  "erro.voce_nao_consegue_conjurar_agora": {
    "en": "You can't cast right now.",
    "pt": "Você não consegue conjurar agora."
  },
  "erro.voce_nao_controla_este_prisioneiro": {
    "en": "You don't control this prisoner.",
    "pt": "Você não controla este prisioneiro."
  },
  "erro.voce_nao_esta_em_chamas": {
    "en": "You're not on fire.",
    "pt": "Você não está em chamas."
  },
  "erro.voce_nao_pode_curar_a_si_mesmo_com_esta": {
    "en": "You can't heal yourself with this ability.",
    "pt": "Você não pode curar a si mesmo com esta habilidade."
  },
  "erro.voce_nao_pode_votar_nesta_solicitacao": {
    "en": "You can't vote on this request.",
    "pt": "Você não pode votar nesta solicitação."
  },
  "erro.voce_nao_possui_esta_tecnica": {
    "en": "You don't own this technique.",
    "pt": "Você não possui esta técnica."
  },
  "erro.voce_nao_sabe_criar_armadilhas": {
    "en": "You don't know how to create traps.",
    "pt": "Você não sabe criar armadilhas."
  },
  "erro.voce_nao_sabe_desarmar_armadilhas_habili": {
    "en": "You don't know how to disarm traps (Rogue ability).",
    "pt": "Você não sabe desarmar armadilhas (habilidade do Ladino)."
  },
  "erro.voce_nao_sabe_detectar_armadilhas_habili": {
    "en": "You don't know how to detect traps (Rogue ability).",
    "pt": "Você não sabe detectar armadilhas (habilidade do Ladino)."
  },
  "erro.voce_nao_sabe_se_esconder_nas_sombras_ha": {
    "en": "You don't know how to hide in the shadows (Rogue ability).",
    "pt": "Você não sabe se esconder nas sombras (habilidade do Ladino)."
  },
  "erro.voce_nao_sabe_usar_cura": {
    "en": "You don't know how to use Heal.",
    "pt": "Você não sabe usar Cura."
  },
  "erro.voce_nao_sabe_usar_cura_em_area": {
    "en": "You don't know how to use Area Heal.",
    "pt": "Você não sabe usar Cura em Área."
  },
  "erro.voce_nao_sabe_usar_esta_habilidade": {
    "en": "You don't know how to use this ability.",
    "pt": "Você não sabe usar esta habilidade."
  },
  "erro.voce_nao_sabe_usar_golpe_sagrado": {
    "en": "You don't know how to use Holy Strike.",
    "pt": "Você não sabe usar Golpe Sagrado."
  },
  "erro.voce_nao_sabe_usar_imposicao_das_maos_ha": {
    "en": "You don't know how to use Lay on Hands (Paladin ability).",
    "pt": "Você não sabe usar Imposição das Mãos (habilidade do Paladino)."
  },
  "erro.voce_nao_sabe_usar_protetor": {
    "en": "You don't know how to use Protector.",
    "pt": "Você não sabe usar Protetor."
  },
  "erro.voce_nao_sabe_usar_provocacao": {
    "en": "You don't know how to use Taunt.",
    "pt": "Você não sabe usar Provocação."
  },
  "erro.voce_nao_sabe_usar_purificacao": {
    "en": "You don't know how to use Purification.",
    "pt": "Você não sabe usar Purificação."
  },
  "erro.voce_nao_sabe_usar_ressurreicao": {
    "en": "You don't know how to use Resurrection.",
    "pt": "Você não sabe usar Ressurreição."
  },
  "erro.voce_nao_sabe_usar_veneno_rapido": {
    "en": "You don't know how to use Quick Poison.",
    "pt": "Você não sabe usar Veneno Rápido."
  },
  "erro.voce_nao_tem_servos": {
    "en": "You have no minions.",
    "pt": "Você não tem servos."
  },
  "erro.voce_nao_tem_uma_adaga_equipada_para_arr": {
    "en": "You don't have a dagger equipped to throw.",
    "pt": "Você não tem uma adaga equipada para arremessar."
  },
  "erro.voce_precisa_de_1_e_1_para_desarmar_a_ar": {
    "en": "You need 🍖1 and 💧1 to disarm the trap.",
    "pt": "Você precisa de 🍖1 e 💧1 para desarmar a armadilha."
  },
  "erro.voz_quebrada_impede_cancoes_heroicas": {
    "en": "Broken Voice prevents Heroic Songs.",
    "pt": "Voz Quebrada impede Canções Heroicas."
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_ERROS);
