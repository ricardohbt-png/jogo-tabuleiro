// Textos dos quadros (popups) que o servidor manda: trap_result, curse_result,
// sleep/stun/poison/petrify/freezing/equipment_damage... Mantido à mão.
window.LANG_QUADROS = {
  "quadro.1_em_ataques": {
    "pt": "-1 em ataques",
    "en": "-1 on attacks"
  },
  "quadro.1_rodada": {
    "pt": "1 rodada",
    "en": "1 round"
  },
  "quadro.1_turno": {
    "pt": "1 turno",
    "en": "1 turn"
  },
  "quadro.a_area_permanece_em_chamas_e_pode_causar_dan": {
    "pt": "A área permanece em chamas e pode causar dano novamente",
    "en": "The area keeps burning and may deal damage again"
  },
  "quadro.a_armadilha_libera_uma_onda_de_sono_que_domi": {
    "pt": "A armadilha libera uma onda de sono que domina seus sentidos.",
    "en": "The trap releases a wave of sleep that overwhelms your senses."
  },
  "quadro.a_continua_causando_dano": {
    "pt": "A {tipo_meta_get_nome_a} continua causando dano.",
    "en": "The {tipo_meta_get_nome_a} keeps dealing damage."
  },
  "quadro.a_descarga_eletrica_atravessa_seu_corpo": {
    "pt": "A descarga elétrica atravessa seu corpo.",
    "en": "The electric discharge runs through your body."
  },
  "quadro.a_explosao_de_fogo_envolve_voce_completament": {
    "pt": "A explosão de fogo envolve você completamente.",
    "en": "The fiery blast engulfs you completely."
  },
  "quadro.a_forca_descomunal_do_ogro_o_deixa_atordoado": {
    "pt": "A Força Descomunal do ogro o deixa atordoado.",
    "en": "The ogre's Monstrous Strength leaves you stunned."
  },
  "quadro.a_infeccao_se_espalha_pelo_seu_corpo_a_condi": {
    "pt": "A infecção se espalha pelo seu corpo. A condição permanece até ser curada por Purificação, elixir ou templo.",
    "en": "The infection spreads through your body. The condition lasts until cured by Purification, an elixir or the temple."
  },
  "quadro.a_rajada_violenta_o_atinge_e_o_arremessa_par": {
    "pt": "A rajada violenta o atinge e o arremessa para trás.",
    "en": "The violent gust strikes you and hurls you backward."
  },
  "quadro.a_saida_esta_bloqueada_o_portal_nao_consegue": {
    "pt": "A saída está bloqueada; o portal não consegue se abrir.",
    "en": "The exit is blocked; the portal cannot open."
  },
  "quadro.a_serpente_de_bronze_imobilizou_voce": {
    "pt": "A Serpente de Bronze imobilizou você.",
    "en": "The Bronze Serpent immobilized you."
  },
  "quadro.acerto_e_dano_menos": {
    "pt": "Acerto e dano -{n}",
    "en": "Attack and damage -{n}"
  },
  "quadro.acertou_voce_e_causaria_de_dano_ativar_para": {
    "pt": "{nome_criatura_atacan} acertou você e causaria {dano} de dano. Ativar {bracelete_get_name_o} para reduzir o dano em {bracelet_reaction_di}?",
    "en": "{nome_criatura_atacan} hit you and would deal {dano} damage. Activate {bracelete_get_name_o} to reduce the damage by {bracelet_reaction_di}?"
  },
  "quadro.acertou_voce_usar_sorte_para_forca_lo_a_rerr": {
    "pt": "{name} acertou você. Usar Sorte para forçá-lo a rerrolar com −2?",
    "en": "{name} hit you. Use Luck to force a reroll at −2?"
  },
  "quadro.acido_do_grotao": {
    "pt": "Ácido do Grotão",
    "en": "Grotão Acid"
  },
  "quadro.acido_residual": {
    "pt": "Ácido Residual",
    "en": "Residual Acid"
  },
  "quadro.adormecido_por_rodada_s": {
    "pt": "😴 Adormecido por {duracao_sono} rodada(s)",
    "en": "😴 Asleep for {duracao_sono} round(s)"
  },
  "quadro.age_apenas_em_rodadas_alternadas": {
    "pt": "Age apenas em rodadas alternadas",
    "en": "Acts only every other round"
  },
  "quadro.age_sob_o_controle_do_conjurador_a_partir_do": {
    "pt": "Age sob o controle do conjurador a partir do próximo turno",
    "en": "Acts under the caster's control from your next turn"
  },
  "quadro.arma_destruida_sem_recuperar": {
    "pt": "A arma foi destruída permanentemente e não pode ser recuperada",
    "en": "The weapon was destroyed for good and cannot be recovered"
  },
  "quadro.arma_quebrada": {
    "pt": "Arma Quebrada",
    "en": "Weapon Broken"
  },
  "quadro.armadura_quebrada": {
    "pt": "Armadura Quebrada",
    "en": "Armor Broken"
  },
  "quadro.as_chamas_continuam_queimando": {
    "pt": "As chamas continuam queimando.",
    "en": "The flames keep burning."
  },
  "quadro.ate_o_fim_do_proximo_turno": {
    "pt": "até o fim do próximo turno",
    "en": "until the end of your next turn"
  },
  "quadro.atingiu_estado": {
    "pt": "{fonte} atingiu {peca}. Estado: {estado}.",
    "en": "{fonte} hit {peca}. Condition: {estado}."
  },
  "quadro.atordoado": {
    "pt": "Atordoado",
    "en": "Stunned"
  },
  "quadro.bau_armadilha_titulo": {
    "pt": "Baú-Armadilha",
    "en": "Trapped Chest"
  },
  "quadro.bola_de_fogo": {
    "pt": "Bola de Fogo",
    "en": "Fireball"
  },
  "quadro.buraco_escondido": {
    "pt": "Buraco Escondido",
    "en": "Hidden Pit"
  },
  "quadro.ca_menos": {
    "pt": "CA -{n}",
    "en": "AC -{n}"
  },
  "quadro.ca_menos_bonus_perdido": {
    "pt": "CA -{n} (bônus da armadura perdido)",
    "en": "AC -{n} (armor bonus lost)"
  },
  "quadro.cada_dano_sofrido_concede_2_cumulativo_no_pr": {
    "pt": "Cada dano sofrido concede +2 cumulativo no próximo teste de Vontade",
    "en": "Each instance of damage taken grants a cumulative +2 on the next Will save"
  },
  "quadro.cai_perto_do_alvo_reparar": {
    "pt": "Cai perto do alvo; pode ser recolhida e reparada no ferreiro",
    "en": "Lands near the target; it can be picked up and repaired at the blacksmith"
  },
  "quadro.caiu_no_abismo_e_morreu": {
    "pt": "☠️ Caiu no abismo e morreu.",
    "en": "☠️ Fell into the abyss and died."
  },
  "quadro.camara_de_gas": {
    "pt": "Câmara de Gás",
    "en": "Gas Chamber"
  },
  "quadro.classe_errada_d100": {
    "pt": "classe errada (d100={rc}≤50%)",
    "en": "wrong class (d100={rc}≤50%)"
  },
  "quadro.classe_ok_d100": {
    "pt": "classe ok (d100={rc}>50%)",
    "en": "class ok (d100={rc}>50%)"
  },
  "quadro.comando": {
    "pt": "Comando",
    "en": "Command"
  },
  "quadro.composicao_encontro_invalida": {
    "pt": "Composição de encontro inválida.",
    "en": "Invalid encounter composition."
  },
  "quadro.congelamento_progressivo": {
    "pt": "Congelamento Progressivo",
    "en": "Progressive Freezing"
  },
  "quadro.corrosao": {
    "pt": "Corrosão",
    "en": "Corrosion"
  },
  "quadro.corrosao_nivel": {
    "pt": "🛠️ {peca}: corrosão nível {nivel} ({estado})",
    "en": "🛠️ {peca}: corrosion level {nivel} ({estado})"
  },
  "quadro.corrosao_piora": {
    "pt": "A corrosão piora se a peça for atingida novamente",
    "en": "The corrosion worsens if the piece is hit again"
  },
  "quadro.cuspe_de_acido": {
    "pt": "Cuspe de Ácido",
    "en": "Acid Spit"
  },
  "quadro.dano_de_fogo_total_por_falhar_no_teste_de_re": {
    "pt": "Dano de fogo total por falhar no teste de Reflexos",
    "en": "Full fire damage for failing the Reflex save"
  },
  "quadro.dano_eletrico_total_por_falhar_no_teste_de_r": {
    "pt": "Dano elétrico total por falhar no teste de Reflexos",
    "en": "Full lightning damage for failing the Reflex save"
  },
  "quadro.dano_sagrado_total_por_falhar_no_teste_de_re": {
    "pt": "Dano sagrado total por falhar no teste de Reflexos",
    "en": "Full holy damage for failing the Reflex save"
  },
  "quadro.de_dano_de": {
    "pt": "{dano} de dano de {nomes_elemento_get_e}",
    "en": "{dano} {nomes_elemento_get_e} damage"
  },
  "quadro.de_dano_de_acido": {
    "pt": "{dano} de dano de ácido",
    "en": "{dano} acid damage"
  },
  "quadro.de_dano_de_acido_no_turno_seguinte": {
    "pt": "{dano} de dano de ácido no turno seguinte",
    "en": "{dano} acid damage on the following turn"
  },
  "quadro.de_dano_de_gelo": {
    "pt": "{dano} de dano de gelo",
    "en": "{dano} cold damage"
  },
  "quadro.de_dano_por_colisao": {
    "pt": "+{col} de dano por colisão",
    "en": "+{col} collision damage"
  },
  "quadro.de_dano_por_rodada": {
    "pt": "{veneno_get_dano_1d4} de dano por rodada",
    "en": "{veneno_get_dano_1d4} damage per round"
  },
  "quadro.de_dano_sofrido": {
    "pt": "{dano} de dano sofrido",
    "en": "{dano} damage taken"
  },
  "quadro.deve_fugir_sempre_que_possivel": {
    "pt": "Deve fugir sempre que possível",
    "en": "Must flee whenever possible"
  },
  "quadro.disparos_acerto_ou_erro_envenenam_o_alvo": {
    "pt": "{VENENO_CARGAS} disparos (acerto ou erro) envenenam o alvo",
    "en": "{VENENO_CARGAS} shots (hit or miss) poison the target"
  },
  "quadro.doenca": {
    "pt": "Doença {severidade_capitaliz}",
    "en": "{severidade_capitaliz} Disease"
  },
  "quadro.dominar_mente": {
    "pt": "Dominar Mente",
    "en": "Dominate Mind"
  },
  "quadro.duracao_2_turnos": {
    "pt": "Duração: 2 turnos",
    "en": "Duration: 2 turns"
  },
  "quadro.duracao_ate_o_proximo_turno": {
    "pt": "Duração: até o próximo turno",
    "en": "Duration: until the next turn"
  },
  "quadro.duracao_rodada_s": {
    "pt": "Duração: {int_duracao_or_0} rodada(s)",
    "en": "Duration: {int_duracao_or_0} round(s)"
  },
  "quadro.em_chamas": {
    "pt": "Em Chamas",
    "en": "On Fire"
  },
  "quadro.engolido": {
    "pt": "Engolido",
    "en": "Swallowed"
  },
  "quadro.equipamento_danificado": {
    "pt": "Equipamento Danificado",
    "en": "Equipment Damaged"
  },
  "quadro.escapa_com_teste_de_forca_cd_no_inicio_de_ca": {
    "pt": "💪 Escapa com teste de Força CD {escape_dc} no início de cada turno",
    "en": "💪 Escape with a DC {escape_dc} Strength check at the start of each turn"
  },
  "quadro.escuridao": {
    "pt": "escuridão",
    "en": "darkness"
  },
  "quadro.estado.danificado": {
    "pt": "danificado",
    "en": "damaged"
  },
  "quadro.estado.destruido": {
    "pt": "destruído",
    "en": "destroyed"
  },
  "quadro.estado.intacto": {
    "pt": "intacto",
    "en": "intact"
  },
  "quadro.estado.muito_danificado": {
    "pt": "muito danificado",
    "en": "badly damaged"
  },
  "quadro.estado.quebrado": {
    "pt": "quebrado",
    "en": "broken"
  },
  "quadro.falha_critica_de_arremesso": {
    "pt": "Falha crítica de arremesso",
    "en": "Critical throw failure"
  },
  "quadro.falha_no_teste_de_reflexos_dano_total": {
    "pt": "Falha no teste de Reflexos: dano total",
    "en": "Reflex save failed: full damage"
  },
  "quadro.falhou_na_fortitude_cd_esta_paralisado": {
    "pt": "❄️ Falhou na Fortitude CD {cd_paralisia}: está paralisado",
    "en": "❄️ Failed the DC {cd_paralisia} Fortitude save: paralyzed"
  },
  "quadro.falhou_no_teste_de_fortitude_e_sofreu_de_dan": {
    "pt": "☠️ Falhou no teste de Fortitude e sofreu {dano} de dano",
    "en": "☠️ Failed the Fortitude save and took {dano} damage"
  },
  "quadro.falhou_nos_reflexos_o_monstro_ataca_imediata": {
    "pt": "⚔️ Falhou nos Reflexos: o monstro ataca imediatamente!",
    "en": "⚔️ Failed the Reflex save: the monster attacks at once!"
  },
  "quadro.fome": {
    "pt": "fome",
    "en": "hunger"
  },
  "quadro.impacto_do_arremesso": {
    "pt": "Impacto do arremesso",
    "en": "Throw impact"
  },
  "quadro.imune_a_paralisia": {
    "pt": "🛡️ Imune à paralisia",
    "en": "🛡️ Immune to paralysis"
  },
  "quadro.imune_a_por_rodada_s": {
    "pt": " — imune a {nome_status} por **{rod}** rodada(s)!",
    "en": " — immune to {nome_status} for **{rod}** round(s)!"
  },
  "quadro.jato_de_acido": {
    "pt": "Jato de Ácido",
    "en": "Acid Jet"
  },
  "quadro.jato_de_ar": {
    "pt": "Jato de Ar",
    "en": "Air Jet"
  },
  "quadro.lanca_uma_rajada_de_acido_corrosivo_contra_v": {
    "pt": "{fonte} lança uma rajada de ácido corrosivo contra você. Reflexos {total_save} vs. CD {cd}.",
    "en": "{fonte} spits a burst of corrosive acid at you. Reflex {total_save} vs. DC {cd}."
  },
  "quadro.lentidao": {
    "pt": "Lentidão",
    "en": "Slow"
  },
  "quadro.maca_do_zero_absoluto": {
    "pt": "Maça do Zero Absoluto",
    "en": "Absolute Zero Mace"
  },
  "quadro.mapa_encontro_ausente": {
    "pt": "Mapa de encontro de viagem ausente.",
    "en": "The travel encounter map is missing."
  },
  "quadro.marcas_de_petrificacao_3_3": {
    "pt": "Marcas de Petrificação: 3/3",
    "en": "Petrification marks: 3/3"
  },
  "quadro.medo": {
    "pt": "Medo",
    "en": "Fear"
  },
  "quadro.mordida_corrosiva": {
    "pt": "Mordida Corrosiva",
    "en": "Corrosive Bite"
  },
  "quadro.motivos_parenteses": {
    "pt": " ({motivos})",
    "en": " ({motivos})"
  },
  "quadro.movimento_menos": {
    "pt": "Movimento -{n}",
    "en": "Movement -{n}"
  },
  "quadro.movimento_reduzido_em_quadrado_s": {
    "pt": "Movimento reduzido em {pilhas} quadrado(s)",
    "en": "Movement reduced by {pilhas} square(s)"
  },
  "quadro.nao_pode_atacar_nem_usar_habilidades": {
    "pt": "Não pode atacar nem usar habilidades",
    "en": "Cannot attack or use abilities"
  },
  "quadro.nao_pode_mover_atacar_ou_usar_habilidades_du": {
    "pt": "Não pode mover, atacar ou usar habilidades durante esse turno",
    "en": "Cannot move, attack or use abilities during that turn"
  },
  "quadro.nao_pode_se_aproximar_da_fonte_do_medo": {
    "pt": "Não pode se aproximar da fonte do medo",
    "en": "Cannot approach the source of the fear"
  },
  "quadro.nao_pode_se_mover": {
    "pt": "Não pode se mover",
    "en": "Cannot move"
  },
  "quadro.nao_pode_se_mover_atacar_nem_usar_habilidade": {
    "pt": "Não pode se mover, atacar nem usar habilidades",
    "en": "Cannot move, attack or use abilities"
  },
  "quadro.nao_pode_se_mover_atacar_nem_usar_habilidade_2": {
    "pt": "Não pode se mover, atacar nem usar habilidades durante esse turno",
    "en": "Cannot move, attack or use abilities during that turn"
  },
  "quadro.nao_pode_se_mover_atacar_ou_usar_habilidades": {
    "pt": "Não pode se mover, atacar ou usar habilidades",
    "en": "Cannot move, attack or use abilities"
  },
  "quadro.nenhum_equipamento_equipado_disponivel_para": {
    "pt": "🛠️ Nenhum equipamento equipado disponível para corroer",
    "en": "🛠️ No equipped gear available to corrode"
  },
  "quadro.nivel_d100": {
    "pt": "nível (d100={rn}≤{chance}%)",
    "en": "level (d100={rn}≤{chance}%)"
  },
  "quadro.nivel_ok_d100": {
    "pt": "nível ok (d100={rn}>{chance}%)",
    "en": "level ok (d100={rn}>{chance}%)"
  },
  "quadro.no_inicio_do_seu_proximo_turno_voce_sofre_me": {
    "pt": "No início do seu próximo turno, você sofre metade desse dano novamente",
    "en": "At the start of your next turn, you take half that damage again"
  },
  "quadro.no_proximo_turno_o_conjurador_controlara_seu": {
    "pt": "No próximo turno, o conjurador controlará seu movimento",
    "en": "On your next turn, the caster will control your movement"
  },
  "quadro.novo_teste_de_fortitude_no_inicio_de_cada_tu": {
    "pt": "Novo teste de Fortitude no início de cada turno",
    "en": "New Fortitude save at the start of each turn"
  },
  "quadro.o_acido_continua_corroendo": {
    "pt": "O ácido continua corroendo.",
    "en": "The acid keeps eating away."
  },
  "quadro.o_acido_do_jato_continua_queimando_no_inicio": {
    "pt": "O ácido do jato continua queimando no início do seu turno.",
    "en": "The acid from the jet keeps burning at the start of your turn."
  },
  "quadro.o_conjurador_tambem_controlara_sua_acao_prin": {
    "pt": "O conjurador também controlará sua ação principal e habilidades",
    "en": "The caster will also control your main action and abilities"
  },
  "quadro.o_efeito_acumula_ate_3_de_movimento": {
    "pt": "O efeito acumula até -3 de movimento",
    "en": "The effect stacks up to -3 movement"
  },
  "quadro.o_frio_se_acumula_em_seu_corpo_apos_a_garra": {
    "pt": "O frio se acumula em seu corpo após a Garra Congelante.",
    "en": "Cold builds up in your body after the Freezing Claw."
  },
  "quadro.o_gas_preenche_a_sala_fortitude_cd_13_evita": {
    "pt": "O gás preenche a sala. Fortitude CD 13 evita o dano neste turno.",
    "en": "Gas fills the room. Fortitude DC 13 avoids the damage this turn."
  },
  "quadro.o_golpe_critico_de_bordao_deixou_voce_atordo": {
    "pt": "O golpe crítico de Bordão deixou você atordoado.",
    "en": "The Quarterstaff's critical hit left you stunned."
  },
  "quadro.o_golpe_esmagador_de_deixou_voce_atordoado": {
    "pt": "O Golpe Esmagador de {nome_criatura_m} deixou você atordoado.",
    "en": "{nome_criatura_m}'s Crushing Blow left you stunned."
  },
  "quadro.o_medo_magico_toma_conta_de_voce": {
    "pt": "O medo mágico toma conta de você.",
    "en": "Magical fear takes hold of you."
  },
  "quadro.o_peao_some_do_mapa_e_fica_protegido_contra": {
    "pt": "🕳️ O peão some do mapa e fica protegido contra ataques e efeitos adversos até o fim da rodada perdida",
    "en": "🕳️ The pawn leaves the map and is protected from attacks and harmful effects until the end of the lost round"
  },
  "quadro.o_primeiro_ataque_recebido_e_critico": {
    "pt": "O primeiro ataque recebido é crítico",
    "en": "The first attack against you is a critical hit"
  },
  "quadro.o_raio_pode_ricochetear_e_atingir_o_mesmo_al": {
    "pt": "O raio pode ricochetear e atingir o mesmo alvo novamente",
    "en": "The bolt may ricochet and hit the same target again"
  },
  "quadro.o_raio_sagrado_atinge_voce_sem_que_consiga_s": {
    "pt": "O raio sagrado atinge você sem que consiga se esquivar.",
    "en": "The holy ray strikes you before you can dodge."
  },
  "quadro.o_turbilhao_do_elemental_de_ar_o_deixa_sem_f": {
    "pt": "O Turbilhão do Elemental de Ar o deixa sem fôlego.",
    "en": "The Air Elemental's Whirlwind leaves you breathless."
  },
  "quadro.o_veneno_foi_aplicado_seus_efeitos_persistem": {
    "pt": "O veneno foi aplicado. Seus efeitos persistem até a duração terminar ou serem purificados.",
    "en": "The poison took hold. Its effects last until the duration ends or it is purified."
  },
  "quadro.olhar_petrificante": {
    "pt": "Olhar Petrificante",
    "en": "Petrifying Gaze"
  },
  "quadro.paralisia_dura_no_maximo_rodada_s": {
    "pt": "Paralisia dura no máximo {paralisado_rodada_ma} rodada(s)",
    "en": "Paralysis lasts at most {paralisado_rodada_ma} round(s)"
  },
  "quadro.peca_destruida_permanentemente": {
    "pt": "A peça foi destruída permanentemente",
    "en": "The piece was destroyed for good"
  },
  "quadro.perdera_a_proxima_rodada": {
    "pt": "⏸️ Perderá a próxima rodada",
    "en": "⏸️ Will lose the next round"
  },
  "quadro.perdeu_o_movimento": {
    "pt": "🦵 Perdeu o movimento",
    "en": "🦵 Lost movement"
  },
  "quadro.petrificacao": {
    "pt": "Petrificação",
    "en": "Petrification"
  },
  "quadro.petrificacao_total_o_corpo_foi_transformado": {
    "pt": "Petrificação total: o corpo foi transformado em pedra",
    "en": "Full petrification: the body was turned to stone"
  },
  "quadro.petrificado": {
    "pt": "Petrificado",
    "en": "Petrified"
  },
  "quadro.presenca_aterradora": {
    "pt": "Presença Aterradora",
    "en": "Terrifying Presence"
  },
  "quadro.preso_em_gelo": {
    "pt": "Preso em gelo",
    "en": "Trapped in ice"
  },
  "quadro.provocado": {
    "pt": "provocado",
    "en": "taunted"
  },
  "quadro.quebrou_sob_e_nao_pode_mais_ser_usada": {
    "pt": "{peca} quebrou sob {fonte} e não pode mais ser usada.",
    "en": "{peca} broke under {fonte} and can no longer be used."
  },
  "quadro.quebrou_sob_sua_protecao_foi_perdida": {
    "pt": "{peca} quebrou sob {fonte}; sua proteção foi perdida.",
    "en": "{peca} broke under {fonte}; its protection is lost."
  },
  "quadro.raio_congelante": {
    "pt": "Raio Congelante",
    "en": "Ray of Frost"
  },
  "quadro.raio_divino": {
    "pt": "Raio Divino",
    "en": "Divine Ray"
  },
  "quadro.reflexos_bem_sucedidos_ele_so_agira_na_proxi": {
    "pt": "✅ Reflexos bem-sucedidos: ele só agirá na próxima rodada.",
    "en": "✅ Reflex save succeeded: it will only act next round."
  },
  "quadro.reflexos_cd_12_a_criatura_salta_do_objeto": {
    "pt": "Reflexos CD 12. A criatura salta do objeto.",
    "en": "Reflex DC 12. The creature leaps out of the object."
  },
  "quadro.relampago": {
    "pt": "Relâmpago",
    "en": "Lightning Bolt"
  },
  "quadro.resistiu_a_paralisia_fortitude_cd": {
    "pt": "✅ Resistiu à paralisia (Fortitude CD {cd_paralisia})",
    "en": "✅ Resisted paralysis (Fortitude DC {cd_paralisia})"
  },
  "quadro.resistiu_a_paralisia_no_teste_de_fortitude": {
    "pt": "Resistiu à paralisia no teste de Fortitude",
    "en": "Resisted paralysis on the Fortitude save"
  },
  "quadro.resistiu_ao_gas_neste_turno": {
    "pt": "🫁 Resistiu ao gás neste turno",
    "en": "🫁 Resisted the gas this turn"
  },
  "quadro.saidas_obrigatorias_invalidas": {
    "pt": "Saídas obrigatórias ausentes ou inválidas; revise esta etapa no editor.",
    "en": "Required exits are missing or invalid; review this stage in the editor."
  },
  "quadro.salta_do_objeto_em": {
    "pt": "👹 {name} salta do objeto em {v0},{v1}!",
    "en": "👹 {name} leaps out of the object at {v0},{v1}!"
  },
  "quadro.se_falhar_permanece_congelado_o_efeito_termi": {
    "pt": "Se falhar, permanece congelado; o efeito termina após no máximo 2 rodadas",
    "en": "On a failure you stay frozen; the effect ends after at most 2 rounds"
  },
  "quadro.sede": {
    "pt": "sede",
    "en": "thirst"
  },
  "quadro.seu_personagem_morreu_em_combate": {
    "pt": "Seu personagem morreu em combate.",
    "en": "Your character died in combat."
  },
  "quadro.seu_proximo_ataque_e_um_ataque_furtivo_autom": {
    "pt": " — seu próximo ataque é um **Ataque Furtivo** automático!",
    "en": " — your next attack is an automatic **Sneak Attack**!"
  },
  "quadro.seu_proximo_ataque_tem_vantagem": {
    "pt": " — seu próximo ataque tem **vantagem**!",
    "en": " — your next attack has **advantage**!"
  },
  "quadro.so_pode_ser_removida_por_purificacao_ou_item": {
    "pt": "Só pode ser removida por Purificação ou item que cure petrificação",
    "en": "Can only be removed by Purification or an item that cures petrification"
  },
  "quadro.sofrera_de_dano_de_acido_na_rodada_seguinte": {
    "pt": "🧪 Sofrerá {residual} de dano de ácido na rodada seguinte",
    "en": "🧪 Will take {residual} acid damage next round"
  },
  "quadro.sofreu_de_dano": {
    "pt": "💥 Sofreu {dano_trap} de dano",
    "en": "💥 Took {dano_trap} damage"
  },
  "quadro.sofreu_de_dano_2": {
    "pt": "💥 Sofreu {dano_total} de dano",
    "en": "💥 Took {dano_total} damage"
  },
  "quadro.sofreu_de_dano_3": {
    "pt": "💥 Sofreu {dano} de dano",
    "en": "💥 Took {dano} damage"
  },
  "quadro.sofreu_de_dano_de_acido": {
    "pt": "💥 Sofreu {dano} de dano de ácido",
    "en": "💥 Took {dano} acid damage"
  },
  "quadro.sofreu_de_dano_de_gelo": {
    "pt": "💥 Sofreu {dano} de dano de gelo",
    "en": "💥 Took {dano} cold damage"
  },
  "quadro.sofreu_de_dano_do_desabamento": {
    "pt": "💥 Sofreu {dano} de dano do desabamento",
    "en": "💥 Took {dano} damage from the collapse"
  },
  "quadro.sofreu_de_dano_perfurante": {
    "pt": "💥 Sofreu {dano} de dano perfurante",
    "en": "💥 Took {dano} piercing damage"
  },
  "quadro.sono": {
    "pt": "Sono",
    "en": "Sleep"
  },
  "quadro.sopro_de_dragao": {
    "pt": "Sopro de Dragão",
    "en": "Dragon Breath"
  },
  "quadro.sua_vontade_foi_subjugada_por_uma_forca_arca": {
    "pt": "Sua vontade foi subjugada por uma força arcana.",
    "en": "Your will has been subdued by an arcane force."
  },
  "quadro.sucesso_no_teste_de_reflexos_dano_reduzido_a": {
    "pt": "Sucesso no teste de Reflexos: dano reduzido à metade",
    "en": "Reflex save succeeded: damage halved"
  },
  "quadro.sucesso_no_teste_de_reflexos_efeito_reduzido": {
    "pt": "Sucesso no teste de Reflexos: efeito reduzido",
    "en": "Reflex save succeeded: effect reduced"
  },
  "quadro.teleportado_para": {
    "pt": "🌀 Teleportado para {v0},{v1}",
    "en": "🌀 Teleported to {v0},{v1}"
  },
  "quadro.teste_livre_de_forca_cd_16_no_inicio_do_turn": {
    "pt": "Teste livre de Força CD 16 no início do turno para escapar",
    "en": "Free DC 16 Strength check at the start of the turn to escape"
  },
  "quadro.todos_os_bonus_removidos": {
    "pt": "Todos os bônus desta peça foram removidos",
    "en": "All bonuses of this piece were removed"
  },
  "quadro.toque_putrefato": {
    "pt": "Toque Putrefato",
    "en": "Rotting Touch"
  },
  "quadro.torca_para_que_seus_companheiros_consigam_re": {
    "pt": "Torça para que seus companheiros consigam resgatá-lo",
    "en": "Hope your companions can rescue you"
  },
  "quadro.transformou_seu_corpo_em_pedra_a_petrificaca": {
    "pt": "{fonte} transformou seu corpo em pedra. A petrificação é permanente até ser removida.",
    "en": "{fonte} turned your body to stone. The petrification is permanent until removed."
  },
  "quadro.transformou_seu_corpo_em_pedra_voce_nao_pode": {
    "pt": "{fonte} transformou seu corpo em pedra. Você não pode agir enquanto o efeito durar.",
    "en": "{fonte} turned your body to stone. You cannot act while the effect lasts."
  },
  "quadro.um_aliado_pode_traze_lo_de_volta_com_ressurr": {
    "pt": "Um aliado pode trazê-lo de volta com Ressurreição",
    "en": "An ally can bring you back with Resurrection"
  },
  "quadro.um_buraco_disfarcado_se_abre_sob_seus_pes": {
    "pt": "Um buraco disfarçado se abre sob seus pés.",
    "en": "A hidden pit opens beneath your feet."
  },
  "quadro.um_equipamento_equipado_pode_sofrer_corrosao": {
    "pt": "Um equipamento equipado pode sofrer corrosão",
    "en": "A piece of equipped gear may be corroded"
  },
  "quadro.um_golpe_critico_envolve_voce_em_gelo_sobren": {
    "pt": "Um golpe crítico envolve você em gelo sobrenatural.",
    "en": "A critical blow encases you in supernatural ice."
  },
  "quadro.um_raio_de_frio_arcano_atinge_voce": {
    "pt": "Um raio de frio arcano atinge você.",
    "en": "A ray of arcane cold strikes you."
  },
  "quadro.uma_forca_magica_torna_cada_gesto_mais_dific": {
    "pt": "Uma força mágica torna cada gesto mais difícil.",
    "en": "A magical force makes every gesture harder."
  },
  "quadro.uma_magia_de_sono_domina_seus_sentidos": {
    "pt": "Uma magia de sono domina seus sentidos.",
    "en": "A sleep spell overwhelms your senses."
  },
  "quadro.uma_ordem_magica_invade_sua_mente": {
    "pt": "Uma ordem mágica invade sua mente.",
    "en": "A magical order invades your mind."
  },
  "quadro.usa_sopro_de_dragao_em_reflexos_vs_cd": {
    "pt": "{fonte} usa Sopro de Dragão em {formato}. Reflexos {total_save} vs. CD {cd}.",
    "en": "{fonte} uses Dragon Breath in a {formato}. Reflex {total_save} vs. DC {cd}."
  },
  "quadro.ve_na_escuridao": {
    "pt": "vê na escuridão",
    "en": "sees in the dark"
  },
  "quadro.veneno": {
    "pt": "☠️ Veneno: {veneno_nome}",
    "en": "☠️ Poison: {veneno_nome}"
  },
  "quadro.vitalidade": {
    "pt": "Vitalidade: {n}/3",
    "en": "Durability: {n}/3"
  },
  "quadro.voce_acorda_ao_sofrer_dano": {
    "pt": "Você acorda ao sofrer dano",
    "en": "You wake up when you take damage"
  },
  "quadro.voce_errou_o_ataque_usar_sorte_para_rerrolar": {
    "pt": "Você errou o ataque. Usar Sorte para rerrolar com +2?",
    "en": "You missed the attack. Use Luck to reroll with +2?"
  },
  "quadro.voce_esta_paralisado": {
    "pt": "Você está paralisado",
    "en": "You are paralyzed"
  },
  "quadro.voce_falhou_no_teste_de_usar_sorte_para_rerr": {
    "pt": "Você falhou no teste de {tipo_save}. Usar Sorte para rerrolar com +2?",
    "en": "You failed the {tipo_save} save. Use Luck to reroll with +2?"
  },
  "quadro.voce_ficou_preso_no_bau_forca_cd_para_escapa": {
    "pt": "📦 Você ficou preso no baú. Força CD {tipo_get_escape_difi} para escapar.",
    "en": "📦 You are trapped in the chest. Strength DC {tipo_get_escape_difi} to escape."
  },
  "quadro.voce_morreu": {
    "pt": "Você morreu",
    "en": "You died"
  },
  "quadro.voce_nao_pode_mais_agir_nesta_aventura": {
    "pt": "Você não pode mais agir nesta aventura",
    "en": "You can no longer act in this adventure"
  },
  "quadro.voce_nao_pode_se_mover_atacar_nem_usar_habil": {
    "pt": "Você não pode se mover, atacar nem usar habilidades durante esse turno",
    "en": "You cannot move, attack or use abilities during that turn"
  },
  "quadro.voce_perde_a_proxima_acao": {
    "pt": "Você perde a próxima ação",
    "en": "You lose your next action"
  },
  "quadro.voce_perde_a_proxima_rodada": {
    "pt": "Você perde a próxima rodada",
    "en": "You lose the next round"
  },
  "quadro.voce_perde_o_movimento_no_proximo_turno": {
    "pt": "Você perde o movimento no próximo turno",
    "en": "You lose your movement on the next turn"
  },
  "quadro.voce_perde_sua_proxima_rodada": {
    "pt": "Você perde sua próxima rodada",
    "en": "You lose your next round"
  },
  "quadro.voce_resistiu_parcialmente_a_lentidao_mas_ai": {
    "pt": "Você resistiu parcialmente à Lentidão, mas ainda sente seus efeitos.",
    "en": "You partly resisted the Slow, but still feel its effects."
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_QUADROS);
