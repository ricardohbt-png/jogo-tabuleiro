// NARRAÇÃO do mestre — o log que conta o que acontece na partida
// (etapa 4b-i do idioma).
//
// Mantido À MÃO: depois da migração o server.py não contém mais o texto
// em português, só a chave. A chave é o slug do texto SEM as interpolações.
window.LANG_NARRACAO = {
  "narracao.a_barreira_arcana_de_termina": {
    "en": "🛡️ **{alvo}**'s Arcane Barrier ends.",
    "pt": "🛡️ A Barreira Arcana de **{alvo}** termina."
  },
  "narracao.a_caiu_no_chao_perto_do_alvo_aproxime_se": {
    "en": "🗡️ The **{dagger}** fell to the ground near the target — get closer to retrieve it.",
    "pt": "🗡️ A **{dagger}** caiu no chão perto do alvo — aproxime-se para recuperá-la."
  },
  "narracao.a_cancao_heroica_de_se_cala_recursos_ins": {
    "en": "🔇 **{heroi}**'s Heroic Song falls silent — insufficient resources.",
    "pt": "🔇 A Canção Heroica de **{heroi}** se cala — recursos insuficientes."
  },
  "narracao.a_cancao_heroica_e_interrompida": {
    "en": "🔇 **{heroi}**'s Heroic Song is cut short — {motivo}.",
    "pt": "🔇 A Canção Heroica de **{heroi}** é interrompida — {motivo}."
  },
  "narracao.a_corrosao_consome_de_dano_hp": {
    "en": "☣️ The corrosion eats away at **{heroi}**: **{dano}** damage! ({p_hp}/{p_max_hp} HP)",
    "pt": "☣️ A corrosão consome **{heroi}**: **{dano}** de dano! ({p_hp}/{p_max_hp} HP)"
  },
  "narracao.a_corrupcao_crescente_de_apodrece_a_carn": {
    "en": "☠️ **{heroi}**'s **Growing Corruption** rots the flesh.",
    "pt": "☠️ A **Corrupção Crescente** de **{heroi}** apodrece a carne."
  },
  "narracao.a_defesa_de_ja_esta_corroida_ao_maximo_c": {
    "en": "🧪 **{nome}**'s defense is already corroded to the max (AC {base}).",
    "pt": "🧪 A defesa de **{nome}** já está corroída ao máximo (CA {base})."
  },
  "narracao.a_explosao_causa_ate_de_dano_em_chamas_r": {
    "en": "💥 The blast deals up to **{dano_total}** fire damage (radius {raio}) — DC 12 Reflex for half! It hits allies too!",
    "pt": "💥 A explosão causa até **{dano_total}** de dano em chamas (raio {raio}) — CD 12 Reflexos para metade! Atinge aliados também!"
  },
  "narracao.a_forma_de_tornou_se_permanente": {
    "en": "🦋 The form of **{nome_criatura_alvo}** has become permanent.",
    "pt": "🦋 A forma de **{nome_criatura_alvo}** tornou-se permanente."
  },
  "narracao.a_ilusao_do_dueto_fantasma_repete_o_golp": {
    "en": "🎶 The **Ghostly Duet**'s illusion repeats the blow on **{alvo}**: **{eco}** damage!",
    "pt": "🎶 A ilusão do **Dueto Fantasma** repete o golpe em **{alvo}**: **{eco}** de dano!"
  },
  "narracao.a_invisibilidade_de_termina": {
    "en": "🫥 **{alvo}**'s Invisibility ends.",
    "pt": "🫥 A Invisibilidade de **{alvo}** termina."
  },
  "narracao.a_invocacao_do_pergaminho_surge_hostil_p": {
    "en": "😈 The scroll's summon appears **HOSTILE** near **{heroi}**!",
    "pt": "😈 A invocação do pergaminho surge **HOSTIL** perto de **{heroi}**!"
  },
  "narracao.a_invocacao_falha_sem_se_materializar": {
    "en": "🌫️ The summon fails without materializing.",
    "pt": "🌫️ A invocação falha sem se materializar."
  },
  "narracao.a_licantropia_regenera_em_hp": {
    "en": "🐺 Lycanthropy regenerates **{heroi}** by +{cura} HP ({p_hp}/{p_max_hp}).",
    "pt": "🐺 A Licantropia regenera **{heroi}** em +{cura} HP ({p_hp}/{p_max_hp})."
  },
  "narracao.a_linha_eletrica_do_atinge_de_dano": {
    "en": "⚡ **{a_nome}**'s electric line hits **{extra}**: {d2} damage!",
    "pt": "⚡ A linha elétrica do **{a_nome}** atinge **{extra}**: {d2} de dano!"
  },
  "narracao.a_magia_falha_e_provoca_um_efeito_nocivo": {
    "en": "💥 The spell **fails** and causes a **harmful effect**! ({join_motivos}; harm d100={rh}≤{harm}%)",
    "pt": "💥 A magia **falha** e provoca um **efeito nocivo**! ({join_motivos}; nocivo d100={rh}≤{harm}%)"
  },
  "narracao.a_nuvem_acida_se_dissipou": {
    "en": "🧪 The Acid Cloud has dissipated.",
    "pt": "🧪 A Nuvem Ácida se dissipou."
  },
  "narracao.a_paralisacao_de_terminou": {
    "en": "✅ **{alvo}**'s paralysis has ended.",
    "pt": "✅ A paralisação de **{alvo}** terminou."
  },
  "narracao.a_pocao_de_regeneracao_cura_hp_reserva": {
    "en": "🌿 The **Regeneration Potion** heals **{heroi}** +{cura} HP ({p_hp}/{p_max_hp}; pool {pool}).",
    "pt": "🌿 A **Poção de Regeneração** cura **{heroi}** +{cura} HP ({p_hp}/{p_max_hp}; reserva {pool})."
  },
  "narracao.a_prisao_de_chamas_se_extingue": {
    "en": "The Prison of Flames burns out.",
    "pt": "A Prisão de Chamas se extingue."
  },
  "narracao.a_protecao_contra_energia_de_termina": {
    "en": "🛡️ **{alvo}**'s Protection from Energy ends.",
    "pt": "🛡️ A Proteção contra Energia de **{alvo}** termina."
  },
  "narracao.a_proxima_etapa_esta_indisponivel_o_grup": {
    "en": "⚠️ The next stage is unavailable ({motivo}). The group returns to town.",
    "pt": "⚠️ A próxima etapa está indisponível ({motivo}). O grupo retorna à cidade."
  },
  "narracao.a_velocidade_de_termina": {
    "en": "⚡ **{alvo}**'s Haste ends.",
    "pt": "⚡ A Velocidade de **{alvo}** termina."
  },
  "narracao.a_visao_no_escuro_de_se_esvai": {
    "en": "👁️ **{alvo}**'s Darkvision fades.",
    "pt": "👁️ A Visão no Escuro de **{alvo}** se esvai."
  },
  "narracao.a_zona_de_bola_de_fogo_se_extingue": {
    "en": "🔥 The Fireball zone burns out.",
    "pt": "🔥 A zona de Bola de Fogo se extingue."
  },
  "narracao.a_zona_de_se_dissipou": {
    "en": "🌫️ The {z_get_tipo} zone has dissipated.",
    "pt": "🌫️ A zona de {z_get_tipo} se dissipou."
  },
  "narracao.abateu_uma_criatura_e_desfere_uma_mordid": {
    "en": "🦁 **{monstro}** brought down a creature and lands an extra Bite!",
    "pt": "🦁 **{monstro}** abateu uma criatura e desfere uma Mordida adicional!"
  },
  "narracao.abencoa_a_arma_de_1_ataque_dano_e_ignora": {
    "en": "⚔️ **{caster}** blesses **{alvo}**'s weapon: +1 attack/damage and bypasses physical resistance/immunity for {dur} round(s).",
    "pt": "⚔️ **{caster}** abençoa a arma de **{alvo}**: +1 ataque/dano e ignora resistências/imunidade física por {dur} rodada(s)."
  },
  "narracao.abencoa_aliado_s_1_ataque_dano_ca_resist": {
    "en": "✨ **{caster}** blesses {n} ally(ies): +1 attack/damage/AC/resistance for {dur} round(s).",
    "pt": "✨ **{caster}** abençoa {n} aliado(s): +1 ataque/dano/CA/resistência por {dur} rodada(s)."
  },
  "narracao.abencoa_o_grupo_2_bonus_de_ataque_para_t": {
    "en": "🙏 **{heroi}** blesses the group! +2 Attack Bonus for everyone for 1 turn.",
    "pt": "🙏 **{heroi}** abençoa o grupo! +2 Bônus de Ataque para todos por 1 turno."
  },
  "narracao.acelera_acoes_dobradas_e_movimento_dobra": {
    "en": "⚡ **{caster}** hastens — doubled actions and doubled movement for {dur} round(s)!",
    "pt": "⚡ **{caster}** acelera — ações dobradas e movimento dobrado por {dur} rodada(s)!"
  },
  "narracao.acende_a_e_a_luz_em_volta_e_sugada_fica": {
    "en": "{item_emoji} **{heroi}** lights the **{item}**, and the light around it is swallowed: **hidden** until the end of the turn{extra}",
    "pt": "{item_emoji} **{heroi}** acende a **{item}**, e a luz em volta é sugada: fica **oculto** até o fim do turno{extra}"
  },
  "narracao.acerta_em_d20_vs_ca": {
    "en": "{defn_emoji} **{heroi}** hits **{target}** with **{defn}** (d20={roll}+{p_atk_bonus}={total} vs AC {target_ac})!",
    "pt": "{defn_emoji} **{heroi}** acerta **{defn}** em **{target}** (d20={roll}+{p_atk_bonus}={total} vs CA {target_ac})!"
  },
  "narracao.acerta_em_dano": {
    "en": "🐺 **{heroi}** hits {nome} on **{obj}**: **{dano} damage**.",
    "pt": "🐺 **{heroi}** acerta {nome} em **{obj}**: **{dano} dano**."
  },
  "narracao.acorda_com_o_dano": {
    "en": "🌙 **{alvo_get_name_or_alvo_ge}** wakes up from the damage!",
    "pt": "🌙 **{alvo_get_name_or_alvo_ge}** acorda com o dano!"
  },
  "narracao.adormeceu": {
    "en": "😴 **{tgt_name}** fell asleep!",
    "pt": "😴 **{tgt_name}** adormeceu!"
  },
  "narracao.afogamento_descricao": {
    "en": "The character failed Fortitude against the deep whirlpool and is drowning.",
    "pt": "O personagem falhou na Fortitude contra o redemoinho profundo e está se afogando."
  },
  "narracao.afogamento_nome": {
    "en": "Drowning",
    "pt": "Afogamento"
  },
  "narracao.afogamento_onda_descricao": {
    "en": "The Water Elemental's Enveloping Wave keeps the character trapped and causes drowning damage.",
    "pt": "A Onda Envolvente do Elemental de Água mantém o personagem preso e causa dano de afogamento."
  },
  "narracao.aguenta_o_impacto_fortitude_d20_vs_cd": {
    "en": "💪 **{tgt_name}** withstands the impact (Fortitude d20({d20}){sbs}={stot} vs DC {dc}).",
    "pt": "💪 **{tgt_name}** aguenta o impacto (Fortitude d20({d20}){sbs}={stot} vs CD {dc})."
  },
  "narracao.alvo_sem_nome": {
    "en": "The target",
    "pt": "O alvo"
  },
  "narracao.amaldicoa_alvo_s_1_ataque_dano_ca_resist": {
    "en": "☠️ **{caster}** curses {n} target(s): -1 attack/damage/AC/resistance for {dur} round(s) (affects allies/minions).",
    "pt": "☠️ **{caster}** amaldiçoa {n} alvo(s): -1 ataque/dano/CA/resistência por {dur} rodada(s) (afeta aliados/minions)."
  },
  "narracao.anima_um_novo_servo_ergue_se_d100": {
    "en": "💀 **{heroi}** animates **{corpse_nome}** — a new minion rises! (d100={rolagem})",
    "pt": "💀 **{heroi}** anima **{corpse_nome}** — um novo servo ergue-se! (d100={rolagem})"
  },
  "narracao.antecipa_o_ataque_furtivo_2_no_acerto": {
    "en": "👥 **{target}** anticipates the Sneak Attack — **-2** to hit!",
    "pt": "👥 **{target}** antecipa o Ataque Furtivo — **-2** no acerto!"
  },
  "narracao.ao_golpe_esmagador_de_fortitude_vs_cd": {
    "en": "🪨 {alvo} {resultado} **{monstro}**'s Crushing Blow (Fortitude {total} vs DC {int_ab_get_dc_17_or_17}).",
    "pt": "{alvo} {resultado} ao Golpe Esmagador de {monstro} (Fortitude {total} vs CD {int_ab_get_dc_17_or_17})."
  },
  "narracao.aperta_seus_aneis_em": {
    "en": "🐍 **{m}** tightens its coils around **{a}**! {d} constriction damage (automatic)!",
    "pt": "🐍 **{m}** aperta seus anéis em **{a}**! {d} de dano por constrição (automático)!"
  },
  "narracao.aplica_na_arma_acao_livre": {
    "en": "☠️ **{heroi}** applies **{venenos_vid_nome}** to the weapon (free action) — {desc_veneno}! 💧-{custo_sede}",
    "pt": "☠️ **{heroi}** aplica **{venenos_vid_nome}** na arma (ação livre) — {desc_veneno}! 💧-{custo_sede}"
  },
  "narracao.aprendeu": {
    "en": "📖 **{heroi}** learned **{m_nome}**!",
    "pt": "📖 **{heroi}** aprendeu **{m_nome}**!"
  },
  "narracao.aprendeu_a_forma_de_para_metamorfose": {
    "en": "🦋 **{nome_criatura_atacante}** learned the form of **{forma_get_name_tipo}** for Polymorph.",
    "pt": "🦋 **{nome_criatura_atacante}** aprendeu a forma de **{forma_get_name_tipo}** para Metamorfose."
  },
  "narracao.aproveita_a_oportunidade_para_se_mover_m": {
    "en": "⏳ **{heroi}** uses Opportunity to move further!",
    "pt": "⏳ **{heroi}** aproveita a Oportunidade para se mover mais!"
  },
  "narracao.arma_a_armadilha": {
    "en": "{icone} **{heroi}** arms **{nome}** (cost on cast).",
    "pt": "{icone} **{heroi}** arma **{nome}** (custo ao lançar)."
  },
  "narracao.armadilha_desarmada_com_sucesso": {
    "en": "✅ Trap disarmed successfully!{msg_recover}",
    "pt": "✅ Armadilha desarmada com sucesso!{msg_recover}"
  },
  "narracao.armadilha_raio_congelante_paralisa": {
    "en": "❄️ **{alvo}** is paralyzed by the freezing ray! Escape with Strength DC {dc} at the start of each turn.",
    "pt": "❄️ **{alvo}** está paralisado pelo raio congelante! Escapa com Força CD {dc} no início de cada turno."
  },
  "narracao.armadilha_superada_xp_para_o_grupo": {
    "en": "✨ Trap overcome — +{share} XP for the group!",
    "pt": "✨ Armadilha superada — +{share} XP para o grupo!"
  },
  "narracao.arrasta": {
    "en": "🐊 **{monstro}** drags **{c}**!",
    "pt": "🐊 **{monstro}** arrasta **{c}**!"
  },
  "narracao.arremessa_a_adaga_em_d20_4_vs_ca_de_dano": {
    "en": "🗡️ **{monstro}** throws the dagger at **{target}** (d20={d20}+4={total} vs AC {eff_ac}): **{dmg}** damage!",
    "pt": "🗡️ **{monstro}** arremessa a adaga em **{target}** (d20={d20}+4={total} vs CA {eff_ac}): **{dmg}** de dano!"
  },
  "narracao.arremessa_a_adaga_em_mas_erra_d20_4_vs_c": {
    "en": "🗡️ **{monstro}** throws the dagger at **{target}** but **misses** (d20={d20}+4={total} vs AC {eff_ac}).",
    "pt": "🗡️ **{monstro}** arremessa a adaga em **{target}** mas **erra** (d20={d20}+4={total} vs CA {eff_ac})."
  },
  "narracao.arremessa_a_lanca_ela_cai_em": {
    "en": "🔱 {nome_criatura_m} hurls the spear; it lands at {tile_0},{tile_1}.",
    "pt": "🔱 {nome_criatura_m} arremessa a lança; ela cai em {tile_0},{tile_1}."
  },
  "narracao.arremessa_em": {
    "en": "{defn_emoji} **{heroi}** throws **{defn}** at ({cx},{cy})!",
    "pt": "{defn_emoji} **{heroi}** arremessa **{defn}** em ({cx},{cy})!"
  },
  "narracao.arremessa_em_d20_vs_ca_dano": {
    "en": "🎯 **{heroi}** throws **{dagger}** at **{target}** (d20={roll}+{throw_atk}={total} vs AC {target_ac}):{crit_str} damage [{die_str}={raw}{sb} {throw_stat_name}] = **{dmg}**!",
    "pt": "🎯 **{heroi}** arremessa **{dagger}** em **{target}** (d20={roll}+{throw_atk}={total} vs CA {target_ac}):{crit_str} dano [{die_str}={raw}{sb} {throw_stat_name}] = **{dmg}**!"
  },
  "narracao.arremessa_em_d20_vs_ca_de": {
    "en": "{defn_emoji} **{heroi}** throws **{defn}** at **{target}** (d20={roll}+{p_atk_bonus}={total} vs AC {target_ac}):{crit_str} **{dmg}** {defn_elemento}!",
    "pt": "{defn_emoji} **{heroi}** arremessa **{defn}** em **{target}** (d20={roll}+{p_atk_bonus}={total} vs CA {target_ac}):{crit_str} **{dmg}** de {defn_elemento}!"
  },
  "narracao.arremessa_em_d20_vs_ca_errou": {
    "en": "🎯 **{heroi}** throws **{dagger}** at **{target}** (d20={roll}+{throw_atk}={total} vs AC {target_ac}): **MISS!**",
    "pt": "🎯 **{heroi}** arremessa **{dagger}** em **{target}** (d20={roll}+{throw_atk}={total} vs CA {target_ac}): **ERROU!**"
  },
  "narracao.arremessa_em_d20_vs_ca_errou_2": {
    "en": "{defn_emoji} **{heroi}** throws **{defn}** at **{target}** (d20={roll}+{p_atk_bonus}={total} vs AC {target_ac}): **MISS!**",
    "pt": "{defn_emoji} **{heroi}** arremessa **{defn}** em **{target}** (d20={roll}+{p_atk_bonus}={total} vs CA {target_ac}): **ERROU!**"
  },
  "narracao.arremessa_mas_rola_1_natural_a_adaga_se": {
    "en": "💥 **{heroi}** throws **{dagger}** but rolls a **natural 1** — the dagger is lost forever!",
    "pt": "💥 **{heroi}** arremessa **{dagger}** mas rola **1 natural** — a adaga se perde para sempre!"
  },
  "narracao.arremessa_mas_rola_1_natural_o_frasco_se": {
    "en": "{defn_emoji} **{heroi}** throws **{defn}** but rolls a **natural 1** — the flask shatters far from the target!",
    "pt": "{defn_emoji} **{heroi}** arremessa **{defn}** mas rola **1 natural** — o frasco se espatifa longe do alvo!"
  },
  "narracao.as_chamas_deixadas_pelo_molochus_se_apag": {
    "en": "🔥 The flames left by the Molochus burn out.",
    "pt": "🔥 As chamas deixadas pelo Molochus se apagam."
  },
  "narracao.as_coordenadas_do_mapa_mundi_foram_atual": {
    "en": "🧭 The world map coordinates have been updated.",
    "pt": "🧭 As coordenadas do mapa-múndi foram atualizadas."
  },
  "narracao.assume_a_forma_de": {
    "en": "🦋 **{nome_criatura_alvo}** takes the form of **{form_get_name_form_type}**.",
    "pt": "🦋 **{nome_criatura_alvo}** assume a forma de **{form_get_name_form_type}**."
  },
  "narracao.ataca_as_cegas_na_escuridao_desvantagem": {
    "en": "🌑 **{heroi}** attacks blindly in the dark — **disadvantage** (2d20, uses {roll}).",
    "pt": "🌑 **{heroi}** ataca às cegas na escuridão — **desvantagem** (2d20, usa {roll})."
  },
  "narracao.ataca_com_d20_usado_descartado": {
    "en": "⚠️ **{monstro}** attacks with **{modo}** ({join_motivos}) — d20 **{roll}** used, ~~{discarded}~~ discarded.",
    "pt": "⚠️ **{monstro}** ataca com **{modo}** ({join_motivos}) — d20 **{roll}** usado, ~~{discarded}~~ descartado."
  },
  "narracao.ataca_com_d20_vs_ca_dano": {
    "en": "⚔️ **{heroi}** attacks **{target}** with {weapon_name} (d20={roll}+{eff_atk}={total} vs AC {target_ac}):{crit_str} damage {dmg_detail}{holy_detail}{furtivo_detail} = **{dmg}**!",
    "pt": "⚔️ **{heroi}** ataca **{target}** com {weapon_name} (d20={roll}+{eff_atk}={total} vs CA {target_ac}):{crit_str} dano {dmg_detail}{holy_detail}{furtivo_detail} = **{dmg}**!"
  },
  "narracao.ataca_com_forca_descomunal": {
    "en": "💪 **{monstro}** attacks with **Overwhelming Strength**!",
    "pt": "💪 **{monstro}** ataca com **Força Descomunal**!"
  },
  "narracao.ataca_com_vantagem_e_revela_se": {
    "en": "🫥 **{heroi}** attacks with advantage and reveals themself!",
    "pt": "🫥 **{heroi}** ataca com vantagem e revela-se!"
  },
  "narracao.ataca_d20_vs_ca_de_dano": {
    "en": "⚔️ **{a_nome}** attacks **{monstro}** (d20={roll}+{bonus_ataque}={total} vs AC {m_ac}): **{dmg}** damage!",
    "pt": "⚔️ **{a_nome}** ataca **{monstro}** (d20={roll}+{bonus_ataque}={total} vs CA {m_ac}): **{dmg}** de dano!"
  },
  "narracao.ataca_d20_vs_ca_de_dano_2": {
    "en": "⚔️ **{a_nome}** attacks **{target}** (d20={roll}+{bonus_ataque}={total} vs AC {target_ac}): **{dmg}** damage!",
    "pt": "⚔️ **{a_nome}** ataca **{target}** (d20={roll}+{bonus_ataque}={total} vs CA {target_ac}): **{dmg}** de dano!"
  },
  "narracao.ataca_d20_vs_ca_de_dano_hp": {
    "en": "💢 **{monstro}** attacks **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}):{crit_str} **{dmg_alvo}** damage! ({target_hp}/{target_max_hp} HP)",
    "pt": "💢 **{monstro}** ataca **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}):{crit_str} **{dmg_alvo}** de dano! ({target_hp}/{target_max_hp} HP)"
  },
  "narracao.ataca_d20_vs_ca_de_dano_hp_2": {
    "en": "💢 **{monstro}** attacks **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}):{crit_str} **{dmg_ef}** damage! ({target_vida_atual}/{target_vida_max} HP)",
    "pt": "💢 **{monstro}** ataca **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}):{crit_str} **{dmg_ef}** de dano! ({target_vida_atual}/{target_vida_max} HP)"
  },
  "narracao.ataca_d20_vs_ca_errou": {
    "en": "⚔️ **{heroi}** attacks **{target}** (d20={roll}+{eff_atk}={total} vs AC {target_ac}): **MISS!**",
    "pt": "⚔️ **{heroi}** ataca **{target}** (d20={roll}+{eff_atk}={total} vs CA {target_ac}): **ERROU!**"
  },
  "narracao.ataca_d20_vs_ca_errou_2": {
    "en": "💢 **{monstro}** attacks **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}): **MISS!**",
    "pt": "💢 **{monstro}** ataca **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}): **ERROU!**"
  },
  "narracao.ataca_e_erra_d20_vs_ca": {
    "en": "⚔️ **{a_nome}** attacks **{monstro}** and misses (d20={roll}+{bonus_ataque}={total} vs AC {m_ac}).",
    "pt": "⚔️ **{a_nome}** ataca **{monstro}** e erra (d20={roll}+{bonus_ataque}={total} vs CA {m_ac})."
  },
  "narracao.ataca_e_erra_d20_vs_ca_2": {
    "en": "⚔️ **{a_nome}** attacks **{target}** and misses (d20={roll}+{bonus_ataque}={total} vs AC {target_ac}).",
    "pt": "⚔️ **{a_nome}** ataca **{target}** e erra (d20={roll}+{bonus_ataque}={total} vs CA {target_ac})."
  },
  "narracao.ataca_em_bando_2_acerto": {
    "en": "🐺 **{monstro}** attacks as a pack! (+2 to hit)",
    "pt": "🐺 **{monstro}** ataca em bando! (+2 acerto)"
  },
  "narracao.ataca_enquanto_preso_2_no_acerto": {
    "en": "⛓️ **{heroi}** attacks while restrained — **-2** to hit!",
    "pt": "⛓️ **{heroi}** ataca enquanto preso — **-2** no acerto!"
  },
  "narracao.ataca_mas_o_escudo_divino_bloqueia": {
    "en": "🛡️ **{monstro}** attacks **{tgt_name}** but the Divine Shield blocks it!",
    "pt": "🛡️ **{monstro}** ataca **{tgt_name}** mas o Escudo Divino bloqueia!"
  },
  "narracao.ataca_sustentando_a_cancao": {
    "en": "🎵⚔️ **{heroi}** attacks while sustaining the song (🍖-{custo_extra_fome} 💧-{custo_extra_sede}).",
    "pt": "🎵⚔️ **{heroi}** ataca sustentando a canção (🍖-{custo_extra_fome} 💧-{custo_extra_sede})."
  },
  "narracao.atinge_com_pisoteio_colossal_e_causa_de": {
    "en": "🦶 {monstro} hits {alvo} with **Colossal Stomp** for {dano} damage.",
    "pt": "{monstro} atinge {alvo} com Pisoteio Colossal e causa {dano} de dano."
  },
  "narracao.atinge_com_raio_divino_de_dano_sagrado": {
    "en": "✨ **{caster}** strikes **{alvo}** with Divine Ray: {dano} holy damage.",
    "pt": "✨ **{caster}** atinge **{alvo}** com Raio Divino: {dano} de dano sagrado."
  },
  "narracao.ativa": {
    "en": "⚔️ **{heroi}** activates **{item_nome}**!",
    "pt": "⚔️ **{heroi}** ativa **{item_nome}**!"
  },
  "narracao.ativa_2": {
    "en": "✦ **{m_get_name_o_monstro}** activates **{ability_get_name_ability}**!",
    "pt": "✦ **{m_get_name_o_monstro}** ativa **{ability_get_name_ability}**!"
  },
  "narracao.ativa_3": {
    "en": "**{heroi}** activates {join_nomes} (🍖-{total_fome}{f_total_sede_if_total_se}).",
    "pt": "**{heroi}** ativa {join_nomes} (🍖-{total_fome}{f_total_sede_if_total_se})."
  },
  "narracao.ativa_4": {
    "en": "{nome_criatura_m} activates {nome_criatura_ability}.",
    "pt": "{nome_criatura_m} ativa {nome_criatura_ability}."
  },
  "narracao.ativa_a_deteccao_de_armadilhas_armadilha": {
    "en": "🔍 **{heroi}** activates Trap Detection — {reveladas} trap(s) revealed. (upkeep 💧-1/turn)",
    "pt": "🔍 **{heroi}** ativa a Detecção de Armadilhas — {reveladas} armadilha(s) revelada(s). (manutenção 💧-1/turno)"
  },
  "narracao.ativa_a_regeneracao_runica_por_rodadas": {
    "en": "🔷 {monstro} activates **Runic Regeneration** for {m_runico_regen_rounds} rounds.",
    "pt": "{monstro} ativa a Regeneração Rúnica por {m_runico_regen_rounds} rodadas."
  },
  "narracao.ativa_aura_sagrada_2_ca_para_todos_por_2": {
    "en": "✨ **{heroi}** activates **Holy Aura**! +2 AC for everyone for 2 turns.",
    "pt": "✨ **{heroi}** ativa **Aura Sagrada**! +2 CA para todos por 2 turnos."
  },
  "narracao.ativa_brutalidade_todos_os_ataques_deste": {
    "en": "{nome_criatura_m} activates Brutality: every attack this turn deals +2 damage.",
    "pt": "{nome_criatura_m} ativa Brutalidade: todos os ataques deste turno causam +2 de dano."
  },
  "narracao.ativa_escudo_magico_4_ca_ate_o_proximo_t": {
    "en": "✨ **{heroi}** activates **Magic Shield**! +4 AC until the next turn.",
    "pt": "✨ **{heroi}** ativa **Escudo Mágico**! +4 CA até o próximo turno."
  },
  "narracao.ativa_escudo_magico_aprimorado_4_ca_por": {
    "en": "✨ **{heroi}** activates **Magic Shield** ⚡(Enhanced)! +4 AC for 2 turns.",
    "pt": "✨ **{heroi}** ativa **Escudo Mágico** ⚡(Aprimorado)! +4 CA por 2 turnos."
  },
  "narracao.ativa_para_ganhar_vantagem_no_combate": {
    "en": "✦ **{m_get_name_o_monstro}** activates **{ab_get_name_ab_get_id}** to gain the upper hand in combat!",
    "pt": "✦ **{m_get_name_o_monstro}** ativa **{ab_get_name_ab_get_id}** para ganhar vantagem no combate!"
  },
  "narracao.ativa_regeneracao_divina_1_hp_por_turno": {
    "en": "✨ **{heroi}** activates **Divine Regeneration** — +1 HP per turn. (🍖-{fome_cost} 💧-{sede_cost})",
    "pt": "✨ **{heroi}** ativa **Regeneração Divina** — +1 HP por turno. (🍖-{fome_cost} 💧-{sede_cost})"
  },
  "narracao.ativa_ultimo_esforco_e_luta_por_mais_2_t": {
    "en": "{nome_criatura_m} activates Last Stand and fights for 2 more turns.",
    "pt": "{nome_criatura_m} ativa Último Esforço e luta por mais 2 turnos."
  },
  "narracao.ativa_um_bau_armadilha_surge": {
    "en": "📦 **{heroi}** triggers a **Trap Chest**: **{monstro}** appears!",
    "pt": "📦 **{heroi}** ativa um **Baú-Armadilha**: **{monstro}** surge!"
  },
  "narracao.ativou": {
    "en": "⚠️ **{alvo_nome}** triggered **{nome}**!",
    "pt": "⚠️ **{alvo_nome}** ativou **{nome}**!"
  },
  "narracao.ativou_a_habilidade_pelo_atalho": {
    "en": "⚔️ {heroi} used {nome} from the shortcut bar.",
    "pt": "⚔️ {heroi} ativou a habilidade {nome} pelo atalho."
  },
  "narracao.ativou_o_objeto_chave": {
    "en": "🔑 **{heroi}** activated the key object!",
    "pt": "🔑 **{heroi}** ativou o objeto-chave!"
  },
  "narracao.ativou_um_mecanismo_outras_chaves_ainda": {
    "en": "⚙️ **{heroi}** activated a mechanism; more keys are still needed.",
    "pt": "⚙️ **{heroi}** ativou um mecanismo; outras chaves ainda são necessárias."
  },
  "narracao.aventura_concluida_retorna_gratuitamente": {
    "en": "🏁 **{aventura}** complete! The party returns to the city free of charge.{renome}",
    "pt": "🏁 **{aventura}** concluída! O grupo retorna gratuitamente à cidade.{renome}"
  },
  "narracao.aventura_renome": {
    "en": " Renown {bonus}.",
    "pt": " Renome {bonus}."
  },
  "narracao.azar_sobrenatural_rouba_o_critico_de_o_g": {
    "en": "☠️ **Uncanny Misfortune** steals **{heroi}**'s critical — the blow lands, but without the force it promised.",
    "pt": "☠️ **Azar Sobrenatural** rouba o crítico de **{heroi}** — o golpe acerta, mas sem a força que prometia."
  },
  "narracao.baixa_a_lamina_sagrada_golpe_sagrado_des": {
    "en": "⚔️ **{heroi}** lowers the holy blade — Holy Strike deactivated.",
    "pt": "⚔️ **{heroi}** baixa a lâmina sagrada — Golpe Sagrado desativado."
  },
  "narracao.bau_engolidor_escapa": {
    "en": "💪 **{heroi}** escapes the Swallowing Chest with Strength {total} vs DC {dc}!",
    "pt": "💪 **{heroi}** escapa do Baú Engolidor com Força {total} contra CD {dc}!"
  },
  "narracao.bau_engolidor_falha_escape": {
    "en": "📦 **{heroi}** fails to escape the Swallowing Chest ({total} vs DC {dc}).",
    "pt": "📦 **{heroi}** falha ao escapar do Baú Engolidor ({total} contra CD {dc})."
  },
  "narracao.bau_engolidor_prende_heroi": {
    "en": "📦 **{heroi}** is swallowed by the object! Escape with Strength DC {dc}.",
    "pt": "📦 **{heroi}** é engolido pelo objeto! Escape com Força CD {dc}."
  },
  "narracao.bebe_regeneracao": {
    "en": "🌿 **{m_get_name_o_monstro}** drinks **{item}** — regeneration +{val}.",
    "pt": "🌿 **{m_get_name_o_monstro}** bebe **{item}** — regeneração +{val}."
  },
  "narracao.bebe_reserva_de_regeneracao_hp_1_hp_por": {
    "en": "🌿 **{heroi}** drinks **{item}** — regeneration pool **{p_potion_regen_pool}** HP (+1 HP per round).",
    "pt": "🌿 **{heroi}** bebe **{item}** — reserva de regeneração **{p_potion_regen_pool}** HP (+1 HP por rodada)."
  },
  "narracao.beneficia_o_inimigo_por_engano": {
    "en": "😈 **{magia_nome}** benefits the enemy **{inimigo}** by mistake!",
    "pt": "😈 **{magia_nome}** beneficia o inimigo **{inimigo}** por engano!"
  },
  "narracao.bordao_alvo_perde_acao": {
    "en": "💫 **{alvo}** is stunned by the staff and loses its action this turn.",
    "pt": "💫 **{alvo}** está tonto pelo impacto do Bordão e perde sua ação neste turno."
  },
  "narracao.bordao_critico_atordoa": {
    "en": "the target is stunned and loses its next action",
    "pt": "o alvo fica tonto e perde sua próxima ação"
  },
  "narracao.bordao_critico_fortitude": {
    "en": "🔱 **{heroi}** lands a staff critical on **{alvo}**! Fortitude {total} vs DC {dc} — {resultado}.",
    "pt": "🔱 **{heroi}** acerta **{alvo}** com um crítico de Bordão! Fortitude {total} vs CD {dc} — {resultado}."
  },
  "narracao.bordao_critico_nao_afeta_imune": {
    "en": "🔱 The staff's critical impact does not affect **{alvo}** (construct/undead immunity).",
    "pt": "🔱 O impacto crítico do Bordão não afeta **{alvo}** (imunidade de construto/morto-vivo)."
  },
  "narracao.bordao_critico_resiste": {
    "en": "the target resists the concussive impact",
    "pt": "o alvo resiste ao impacto atordoante"
  },
  "narracao.cacador_das_trevas_ataque_extra_das_garr": {
    "en": "🌑 **Hunter of Darkness** — extra claw attack!",
    "pt": "🌑 **Caçador das Trevas** — ataque extra das garras!"
  },
  "narracao.cai_junto_com": {
    "en": "{nome_criatura_presa} falls together with {nome_criatura_alvo}.",
    "pt": "{nome_criatura_presa} cai junto com {nome_criatura_alvo}."
  },
  "narracao.cai_no_rodamoinho_profundo_fica_preso_e": {
    "en": "🌊 **{nome_criatura_criatura}** falls into the deep whirlpool, is trapped and loses the turn!",
    "pt": "🌊 **{nome_criatura_criatura}** cai no rodamoinho profundo, fica preso e perde o turno!"
  },
  "narracao.camara_gas_ativa": {
    "en": "☠️ The Gas Chamber fills room **{sala}** for **{duracao}** round(s). Fortitude DC 13 is required at the start of each turn.",
    "pt": "☠️ A Câmara de Gás preenche a sala **{sala}** por **{duracao}** rodada(s). É preciso testar Fortitude CD 13 no início de cada turno."
  },
  "narracao.camara_gas_resiste": {
    "en": "🫁 **{alvo_nome}** resists the gas this turn.",
    "pt": "🫁 **{alvo_nome}** resiste ao gás neste turno."
  },
  "narracao.camara_gas_se_dissipou": {
    "en": "☠️ The Gas Chamber dissipates.",
    "pt": "☠️ A Câmara de Gás se dissipa."
  },
  "narracao.cancao_heroica_de_manutencao": {
    "en": "🎵 **{heroi}**'s Heroic Song [{labels}] — upkeep 🍖-{custo_fome} 💧-{custo_sede}.",
    "pt": "🎵 Canção Heroica de **{heroi}** [{labels}] — manutenção 🍖-{custo_fome} 💧-{custo_sede}."
  },
  "narracao.cancao_monstro.entoa": {
    "en": "{nome} sings the Heroic Song and strengthens the allied monsters.",
    "pt": "{nome} entoa a Canção Heroica e fortalece os monstros aliados."
  },
  "narracao.cancao_monstro.entoa_atributos": {
    "en": "{nome} sings the Heroic Song ({atributos}) for the allied monsters.",
    "pt": "{nome} entoa a Canção Heroica ({atributos}) para os monstros aliados."
  },
  "narracao.cauda_em_de_dano_reflexos_vs_cd": {
    "en": "🦂 Tail on **{vitima}**: **{dano}** damage{e_derrubado_if_not_passo}! (Reflex {st} vs DC {cd})",
    "pt": "🦂 Cauda em **{vitima}**: **{dano}** de dano{e_derrubado_if_not_passo}! (Reflexos {st} vs CD {cd})"
  },
  "narracao.causa_de_constricao_em": {
    "en": "🦂 **{monstro}** deals **{dano}** Constriction damage to **{nome}**.",
    "pt": "🦂 **{monstro}** causa **{dano}** de Constrição em **{nome}**."
  },
  "narracao.causa_de_dano_no_estomago_de": {
    "en": "🫀 **{heroi}** deals **{dano}** damage to **{captor}**'s stomach ({p_engolido_dano}/{limite}).",
    "pt": "🫀 **{heroi}** causa **{dano}** de dano no estômago de **{captor}** ({p_engolido_dano}/{limite})."
  },
  "narracao.cego_por_rodada_s_em_ataques": {
    "en": "🙈 **{nome}**: **{alvo_nome}** blinded for {duracao} round(s) ({pen} to attacks)!",
    "pt": "🙈 **{nome}**: **{alvo_nome}** cego por {duracao} rodada(s) ({pen} em ataques)!"
  },
  "narracao.cegueira_expirou_em": {
    "en": "✅ Blindness expired on **{alvo_nome}**.",
    "pt": "✅ Cegueira expirou em **{alvo_nome}**."
  },
  "narracao.comanda_o_jogador_controlara_seu_proximo": {
    "en": "🗣️ **{caster}** commands **{alvo}** — the player will control their next turn!",
    "pt": "🗣️ **{caster}** comanda **{alvo}** — o jogador controlará seu próximo turno!"
  },
  "narracao.comanda_seus_servos_mortos_vivos": {
    "en": "💀 **{heroi}** commands their undead minions!",
    "pt": "💀 **{heroi}** comanda seus servos mortos-vivos!"
  },
  "narracao.combate_os_monstros_perceberam_os_herois": {
    "en": "⚔️ **Combat!** The monsters noticed the heroes!",
    "pt": "⚔️ **Combate!** Os monstros perceberam os heróis!"
  },
  "narracao.combo_devorador_crava_2_garras": {
    "en": "🦎 **Devouring Combo**! **{monstro}** sinks in 2 claws!",
    "pt": "🦎 **Combo Devorador**! **{monstro}** crava 2 garras!"
  },
  "narracao.come_a_fome_e_sede": {
    "en": "{item_emoji} **{heroi}** eats the **{item}**: +{val} hunger and +{val} thirst.",
    "pt": "{item_emoji} **{heroi}** come a **{item}**: +{val} fome e +{val} sede."
  },
  "narracao.comeca_a_sangrar": {
    "en": "🩸 {alvo} starts Bleeding.",
    "pt": "🩸 {alvo} começa a Sangrar."
  },
  "narracao.comeca_a_sangrar_apos_o_combo_devorador": {
    "en": "🩸 {alvo} starts Bleeding after the Devouring Combo.",
    "pt": "🩸 {alvo} começa a Sangrar após o Combo Devorador."
  },
  "narracao.comeca_a_sangrar_apos_o_dilacerar": {
    "en": "🩸 {alvo} starts Bleeding after the Rend.",
    "pt": "🩸 {alvo} começa a Sangrar após o Dilacerar."
  },
  "narracao.con_hp_max": {
    "en": " (max HP -{n})",
    "pt": " (HP máx -{n})"
  },
  "narracao.con_reduzida": {
    "en": "💉 **{alvo_nome}**: CON {antes}→{depois}{hp}.",
    "pt": "💉 **{alvo_nome}**: CON {antes}→{depois}{hp}."
  },
  "narracao.conjura_manto_de_escuridao": {
    "en": "🌑 **{monstro}** casts **Cloak of Darkness**!",
    "pt": "🌑 **{monstro}** conjura **Manto de Escuridão**!"
  },
  "narracao.conjura_o_dueto_fantasma_por_rodada_s": {
    "en": "🎶 **{heroi}** casts the **Ghostly Duet** for {st_duracao} round(s)!",
    "pt": "🎶 **{heroi}** conjura o **Dueto Fantasma** por {st_duracao} rodada(s)!"
  },
  "narracao.conjura_olhar_petrificante_por_rodada_s": {
    "en": "👁️ **{caster}** casts **Petrifying Gaze** for {dur} round(s).",
    "pt": "👁️ **{caster}** conjura **Olhar Petrificante** por {dur} rodada(s)."
  },
  "narracao.conjura_servo_s": {
    "en": "💀 **{monstro}** summons {len_invocados} minion(s): **{nomes}**!",
    "pt": "💀 **{monstro}** conjura {len_invocados} servo(s): **{nomes}**!"
  },
  "narracao.conjura_silencio_4x4_em_por_rodada_s_sem": {
    "en": "🔇 **{monstro}** casts **Silence** 4x4 at ({centro_0},{centro_1}) for {dur} round(s) — no spells inside!",
    "pt": "🔇 **{monstro}** conjura **Silêncio** 4x4 em ({centro_0},{centro_1}) por {dur} rodada(s) — sem magias dentro!"
  },
  "narracao.conjura_um_elemental_de_hp_dano_mov_cont": {
    "en": "🌪️ **{caster}** conjures a **{tipo_capitalize} Elemental** (HP {hpv}, damage {stats_get_dano_1d6}, move {mov}). Control it like the minions — end your turn to open the elementals' window.",
    "pt": "🌪️ **{caster}** conjura um **Elemental de {tipo_capitalize}** (HP {hpv}, dano {stats_get_dano_1d6}, mov {mov}). Controle-o como os servos — encerre o turno para abrir a janela dos elementais."
  },
  "narracao.conjuracao_bem_sucedida": {
    "en": "✨ Casting **successful**!{extra}",
    "pt": "✨ Conjuração **bem-sucedida**!{extra}"
  },
  "narracao.consegue_escapar_do_rodamoinho_e_pode_se": {
    "en": "🌊 **{nome_criatura_criatura}** escapes the whirlpool and can move normally.",
    "pt": "🌊 **{nome_criatura_criatura}** consegue escapar do rodamoinho e pode se mover normalmente."
  },
  "narracao.consome": {
    "en": "{item_emoji} **{heroi}** consumes **{item}**: {e_join_partes}.",
    "pt": "{item_emoji} **{heroi}** consome **{item}**: {e_join_partes}."
  },
  "narracao.consome_de_de": {
    "en": "☠️ **{maldicoes_mid_nome}** consumes **{perda}** {recurso} from **{heroi}**.",
    "pt": "☠️ **{maldicoes_mid_nome}** consome **{perda}** de {recurso} de **{heroi}**."
  },
  "narracao.contem_a_licantropia_no_d4": {
    "en": "🐺 **{heroi}** contains the Lycanthropy ({dado} on the d4).",
    "pt": "🐺 **{heroi}** contém a Licantropia ({dado} no d4)."
  },
  "narracao.continua_dominado_falha_3": {
    "en": "💀 **{a_nome}** remains dominated (failed {rod}/3).",
    "pt": "💀 **{a_nome}** continua dominado (falha {rod}/3)."
  },
  "narracao.continua_o_ultimo_esforco_mais_um_turno": {
    "en": "⚔️ **{heroi}** continues the Last Stand — one more turn!",
    "pt": "⚔️ **{heroi}** continua o Último Esforço — mais um turno!"
  },
  "narracao.continua_paralisado": {
    "en": "❄️ **{alvo}** remains paralyzed ({alvo_paralisado_rodadas}/{max_r}).",
    "pt": "❄️ **{alvo}** continua paralisado ({alvo_paralisado_rodadas}/{max_r})."
  },
  "narracao.continua_preso_na_rede_e_perde_o_turno": {
    "en": "🕸️ **{monstro}** remains stuck in the net and loses the turn!",
    "pt": "🕸️ **{monstro}** continua preso na rede e perde o turno!"
  },
  "narracao.continua_preso_no_rodamoinho_e_nao_pode": {
    "en": "🌪️ **{nome_criatura_criatura}** is still caught in the whirlpool and cannot move this turn.",
    "pt": "🌪️ **{nome_criatura_criatura}** continua preso no rodamoinho e não pode se mover neste turno."
  },
  "narracao.contrai_uma_doenca_sintomas_curavel_por": {
    "en": "🦠 **{heroi}** contracts a **{d_severidade_capitalize} Disease**! Symptoms: {sint}. (curable by a cleric or at the temple)",
    "pt": "🦠 **{heroi}** contrai uma **Doença {d_severidade_capitalize}**! Sintomas: {sint}. (curável por clérigo ou templo)"
  },
  "narracao.contramagica_de_falha_no_teste_oposto_vs": {
    "en": "🛑 **{alvo_get_name_alvo}**'s **Counterspell** fails the opposed check ({meu} vs {op}).",
    "pt": "🛑 **Contramágica** de **{alvo_get_name_alvo}** falha no teste oposto ({meu} vs {op})."
  },
  "narracao.contramagica_de_vence_o_teste_oposto_vs": {
    "en": "🛑 **{alvo_get_name_alvo}**'s **Counterspell** wins the opposed check ({meu} vs {op}) and cancels the spell!",
    "pt": "🛑 **Contramágica** de **{alvo_get_name_alvo}** vence o teste oposto ({meu} vs {op}) e cancela a magia!"
  },
  "narracao.corpo_pesado.dissipa": {
    "en": "The Curse of the Heavy Body fades from {alvo}.",
    "pt": "A Maldição do Corpo Pesado se dissipa de {alvo}."
  },
  "narracao.corpo_pesado.resiste": {
    "en": "{alvo} resists the Curse of the Heavy Body.",
    "pt": "{alvo} resiste à Maldição do Corpo Pesado."
  },
  "narracao.corpo_pesado.sofre": {
    "en": "{alvo} suffers the Curse of the Heavy Body: their Hunger and Thirst costs are doubled for {n} rounds.",
    "pt": "{alvo} sofre a Maldição do Corpo Pesado: seus custos de Fome e Sede ficam duplicados por {n} rodadas."
  },
  "narracao.corrosao_viva_em_agora_de_dano_por_turno": {
    "en": "☣️ **Living Corrosion** on **{heroi}** — now **{n}** damage per turn (2 rounds)!",
    "pt": "☣️ **Corrosão Viva** em **{heroi}** — agora **{n}** de dano por turno (2 rodadas)!"
  },
  "narracao.cospe": {
    "en": "🦖 **{monstro}** spits **{alvo_get_name_or_alvo_ge}** back out: {motivo}.",
    "pt": "🦖 **{monstro}** cospe **{alvo_get_name_or_alvo_ge}**: {motivo}."
  },
  "narracao.cospe_acido_em_de_dano_reflexos_vs_cd": {
    "en": "🧪 **{monstro}** spits acid at **{alvo}**: **{dano}** damage (Reflex {total} vs DC {cd}){metade_if_passou_else}",
    "pt": "🧪 **{monstro}** cospe ácido em **{alvo}**: **{dano}** de dano (Reflexos {total} vs CD {cd}){metade_if_passou_else}"
  },
  "narracao.cria_redemoinho_s_como_acao_livre_desta": {
    "en": "🌪️ **{caster}** creates {len_escolhidos} whirlpool(s) as a free action ({len_zona_redemoinhos}/{limite} of this spell).",
    "pt": "🌪️ **{caster}** cria {len_escolhidos} redemoinho(s) como ação livre ({len_zona_redemoinhos}/{limite} desta magia)."
  },
  "narracao.cria_um_bau_de_provisoes_em_com_alimento": {
    "en": "🍞 **{caster}** creates a **Supply Chest** at ({tx}, {ty}) with **{quantidade}** random food item(s){extra}!",
    "pt": "🍞 **{caster}** cria um **Baú de Provisões** em ({tx}, {ty}) com **{quantidade}** alimento(s) aleatório(s){extra}!"
  },
  "narracao.cria_uma_area_de_silencio_x_em_por_rodad": {
    "en": "🔇 **{caster}** creates a **Silence** area {lado}x{lado} at ({tx},{ty}) for {dur} round(s) — no spells and no Heroic Song bonuses inside (range {alcance}sq).",
    "pt": "🔇 **{caster}** cria uma área de **Silêncio** {lado}x{lado} em ({tx},{ty}) por {dur} rodada(s) — sem magias nem bônus de Canção Heroica dentro (alcance {alcance}q)."
  },
  "narracao.cria_uma_nuvem_acida_de_raio_por_rodada": {
    "en": "🧪 **{monstro}** creates an Acid Cloud of radius {raio} for {zona_duracao} round(s).",
    "pt": "🧪 **{monstro}** cria uma Nuvem Ácida de raio {raio} por {zona_duracao} rodada(s)."
  },
  "narracao.cura_d8_hp_alcance_q": {
    "en": "🙌 **{heroi}** heals **{alvo}** — {num_dados}d8({dados_str}){if_bonus_int_0_else}{bonus_int} = **{cura_real}** HP ({alvo_hp}/{alvo_max_hp}) | range {alcance_tiles}sq (🍖-{custo_fome} 💧-{custo_sede})",
    "pt": "🙌 **{heroi}** cura **{alvo}** — {num_dados}d8({dados_str}){if_bonus_int_0_else}{bonus_int} = **{cura_real}** HP ({alvo_hp}/{alvo_max_hp}) | alcance {alcance_tiles}q (🍖-{custo_fome} 💧-{custo_sede})"
  },
  "narracao.cura_em_hp_2d6_2": {
    "en": "💚 **{heroi}** heals **{t}** for **{heal}** HP! (2d6+2)",
    "pt": "💚 **{heroi}** cura **{t}** em **{heal}** HP! (2d6+2)"
  },
  "narracao.d20_vs_cd_a": {
    "en": "🦂 **{alvo_nome}** — {save_title} d20={d20}{if_sb_0_else}{sb}={total} vs DC {dc} → {resistiu_if_ok_else_falh} {nome}.",
    "pt": "🦂 **{alvo_nome}** — {save_title} d20={d20}{if_sb_0_else}{sb}={total} vs CD {dc} → {resistiu_if_ok_else_falh} a {nome}."
  },
  "narracao.da_o_bote_imovel_ataque_rapido_1_no_acer": {
    "en": "🐍 **{monstro}** strikes from stillness — **Quick Attack** (+1 to hit)!",
    "pt": "🐍 **{monstro}** dá o bote imóvel — **Ataque Rápido** (+1 no acerto)!"
  },
  "narracao.dano_elemental_de": {
    "en": "✨ Elemental damage: +{_xr} {_elem_pt}!",
    "pt": "✨ Dano elemental: +{_xr} de {_elem_pt}!"
  },
  "narracao.de_avanca_ao_estagio": {
    "en": "☠️ **{heroi}**'s **{mal_nome}** advances to stage {depois}.",
    "pt": "☠️ **{mal_nome}** de **{heroi}** avança ao estágio {depois}."
  },
  "narracao.de_con_por_rodada_s": {
    "en": "🌫️ **{alvo_nome}**: -{valor} CON for {duracao} round(s).",
    "pt": "🌫️ **{alvo_nome}**: -{valor} de CON por {duracao} rodada(s)."
  },
  "narracao.de_em_por_rodada_s": {
    "en": "☠️ **{nome}**: -{valor} {attr} on **{alvo_nome}** for {duracao} round(s).",
    "pt": "☠️ **{nome}**: -{valor} de {attr} em **{alvo_nome}** por {duracao} rodada(s)."
  },
  "narracao.de_esta": {
    "en": "🦷 **{label}**: **{heroi}**'s {nome_peca} is **{rot}** (-{nivel_pen})!",
    "pt": "🦷 **{label}**: {nome_peca} de **{heroi}** está **{rot}** (-{nivel_pen})!"
  },
  "narracao.de_foi_destruida_permanentemente": {
    "en": "💥 **{heroi}**'s {nome_peca} was **permanently destroyed**!",
    "pt": "💥 {nome_peca} de **{heroi}** foi **destruída permanentemente**!"
  },
  "narracao.de_resistiu_ao_golpe_sem_sofrer_dano": {
    "en": "🦷 **{label}**: **{heroi}**'s {nome_peca} withstood the blow without taking damage!",
    "pt": "🦷 **{label}**: {nome_peca} de **{heroi}** resistiu ao golpe sem sofrer dano!"
  },
  "narracao.definhar.area": {
    "en": "{caster} withers the life in a {lado}x{lado} area: {afetados} target(s) affected and {imunes} immune.",
    "pt": "{caster} faz a vida definhar em uma área {lado}x{lado}: {afetados} alvo(s) afetado(s) e {imunes} imune(s)."
  },
  "narracao.deixou_moeda_s": {
    "en": "💰 **{monstro}** dropped {gold} coin(s).",
    "pt": "💰 **{monstro}** deixou {gold} moeda(s)."
  },
  "narracao.deixou_moeda_s_2": {
    "en": "💰 **{monstro}** dropped {gold_total} coin(s).",
    "pt": "💰 **{monstro}** deixou {gold_total} moeda(s)."
  },
  "narracao.desaparece_de_e_surge_em": {
    "en": "🌀 **{alvo_get_name_alvo}** vanishes from {origem} and appears at {destino}!",
    "pt": "🌀 **{alvo_get_name_alvo}** desaparece de {origem} e surge em {destino}!"
  },
  "narracao.desaparece_nas_sombras_d20_vs_invisivel": {
    "en": "🌑 **{heroi}** vanishes into the shadows! (d20={d20}+{bonus_dex}={total} vs {dificuldade}) — invisible until acting. Upkeep 🍖-1 💧-1/turn.",
    "pt": "🌑 **{heroi}** desaparece nas sombras! (d20={d20}+{bonus_dex}={total} vs {dificuldade}) — invisível até agir. Manutenção 🍖-1 💧-1/turno."
  },
  "narracao.desaparece_nas_sombras_imune_a_ataques_a": {
    "en": "🌫️ **{monstro}** **vanishes into the shadows** — immune to ranged attacks and hard to hit (melee: -4) until its next turn!",
    "pt": "🌫️ **{monstro}** **desaparece nas sombras** — imune a ataques à distância e difícil de acertar (corpo a corpo: -4) até seu próximo turno!"
  },
  "narracao.desarma_a_armadilha": {
    "en": "{icone} **{heroi}** disarms **{nome}**.",
    "pt": "{icone} **{heroi}** desarma **{nome}**."
  },
  "narracao.desativa_a_deteccao_de_armadilhas": {
    "en": "🔍 **{heroi}** deactivates trap detection.",
    "pt": "🔍 **{heroi}** desativa a detecção de armadilhas."
  },
  "narracao.desce_as_escadas_e_retorna_a_masmorra": {
    "en": "🚪 **{heroi}** goes down the stairs and returns to the dungeon!",
    "pt": "🚪 **{heroi}** desce as escadas e retorna à masmorra!"
  },
  "narracao.desconectou_se": {
    "en": "🔌 **{heroi}** disconnected.",
    "pt": "🔌 **{heroi}** desconectou-se."
  },
  "narracao.desequipou": {
    "en": "📤 **{heroi}** unequipped **{item}**.",
    "pt": "📤 **{heroi}** desequipou **{item}**."
  },
  "narracao.desfere_golpe_de_mao_secundaria_com_acao": {
    "en": "🗡️ **{heroi}** lands an off-hand blow with **{off}** (bonus action) (d20={oroll}+{offhand_atk}={ototal} vs AC {tgt_ac}):{ocrit_str} damage [{off_die}={oraw}{osb} {ostat}] = **{odmg}**!",
    "pt": "🗡️ **{heroi}** desfere golpe de mão secundária com **{off}** (ação bônus) (d20={oroll}+{offhand_atk}={ototal} vs CA {tgt_ac}):{ocrit_str} dano [{off_die}={oraw}{osb} {ostat}] = **{odmg}**!"
  },
  "narracao.desfere_golpe_devastador": {
    "en": "{monstro} lands a Devastating Blow!",
    "pt": "{monstro} desfere um Golpe Devastador!"
  },
  "narracao.desfere_um_golpe_brutal_2_dano": {
    "en": "💥 **{monstro}** delivers a **Brutal Strike** (+2 damage)!",
    "pt": "💥 **{monstro}** desfere um **Golpe Brutal** (+2 dano)!"
  },
  "narracao.desfere_um_golpe_brutal_para_finalizar_2": {
    "en": "💥 **{monstro}** delivers a **Brutal Strike** to finish it off (+2 damage)!",
    "pt": "💥 **{monstro}** desfere um **Golpe Brutal** para finalizar (+2 dano)!"
  },
  "narracao.desnutricao.efeito_ataque": {
    "en": "-1 Attack",
    "pt": "-1 Ataque"
  },
  "narracao.desnutricao.efeito_dano": {
    "en": "-2 Damage",
    "pt": "-2 Dano"
  },
  "narracao.desnutricao.efeito_fome": {
    "en": "-{n} Hunger",
    "pt": "-{n} Fome"
  },
  "narracao.desnutricao.efeito_movimento": {
    "en": "-1 Movement for {n} rounds",
    "pt": "-1 Movimento por {n} rodadas"
  },
  "narracao.desnutricao.efeito_resistiu": {
    "en": "resisted Malnutrition",
    "pt": "resistiu à Desnutrição"
  },
  "narracao.desnutricao.efeito_so_atacar_mover": {
    "en": "can only attack or move for {n} rounds",
    "pt": "pode apenas atacar ou movimentar por {n} rodadas"
  },
  "narracao.desnutricao.resiste": {
    "en": "{alvo} resists Malnutrition: {efeitos}.",
    "pt": "{alvo} resiste à Desnutrição: {efeitos}."
  },
  "narracao.desnutricao.sofre": {
    "en": "{alvo} suffers the effects of Malnutrition: {efeitos}.",
    "pt": "{alvo} sofre os efeitos da Desnutrição: {efeitos}."
  },
  "narracao.desperta": {
    "en": "🌙 **{monstro}** wakes up.",
    "pt": "🌙 **{monstro}** desperta."
  },
  "narracao.deteccao_de_cessa_sede_insuficiente": {
    "en": "🔍 **{heroi}**'s Detection ceases — insufficient thirst.",
    "pt": "🔍 Detecção de **{heroi}** cessa — sede insuficiente."
  },
  "narracao.detecta_armadilhas_armadilha_s_revelada": {
    "en": "👁️ **{heroi}** detects traps! {len_revealed} trap(s) revealed.",
    "pt": "👁️ **{heroi}** detecta armadilhas! {len_revealed} armadilha(s) revelada(s)."
  },
  "narracao.devora_do_chao": {
    "en": "🍖 **{monstro}** devours **{it_get_name_metal}** off the ground!",
    "pt": "🍖 **{monstro}** devora **{it_get_name_metal}** do chão!"
  },
  "narracao.devora_o_material_destruido_e_recupera_h": {
    "en": "🍖 **{monstro}** devours the destroyed material and recovers **{ganho}** HP!",
    "pt": "🍖 **{monstro}** devora o material destruído e recupera **{ganho}** HP!"
  },
  "narracao.dilacera_e_causa_de_dano_extra": {
    "en": "🦁 **{monstro}** Mauls **{alvo_get_name_alvo}** for **{extra}** extra damage!",
    "pt": "🦁 **{monstro}** Dilacera **{alvo_get_name_alvo}** e causa **{extra}** de dano extra!"
  },
  "narracao.dilacera_e_causa_de_dano_extra_2": {
    "en": "🦁 **{monstro}** Mauls **{target_get_name_or_targe}** for **{extra}** extra damage!",
    "pt": "🦁 **{monstro}** Dilacera **{target_get_name_or_targe}** e causa **{extra}** de dano extra!"
  },
  "narracao.dispara_nota_cortante_em": {
    "en": "🎵 **{heroi}** fires **Cutting Note** at **{monstro}**!",
    "pt": "🎵 **{heroi}** dispara **Nota Cortante** em **{monstro}**!"
  },
  "narracao.dispara_nota_cortante_numa_linha_reta": {
    "en": "🎵 **{heroi}** fires **Cutting Note** in a straight line!",
    "pt": "🎵 **{heroi}** dispara **Nota Cortante** numa linha reta!"
  },
  "narracao.dissipa_o_guerreiro_da_luz": {
    "en": "💡 **{heroi}** dispels the Warrior of Light.",
    "pt": "💡 **{heroi}** dissipa o Guerreiro da Luz."
  },
  "narracao.domina_a_mente_de_por_rodada_s": {
    "en": "🧠 **{caster}** dominates **{alvo}**'s mind for {dur} round(s)!",
    "pt": "🧠 **{caster}** domina a mente de **{alvo}** por {dur} rodada(s)!"
  },
  "narracao.domina_controle_temporario_o_morto_vivo": {
    "en": "💀 **{caster}** dominates **{alvo}**! Temporary control — the undead will make a Will save (DC {dif}) each round; 3 failures in a row = PERMANENT control.",
    "pt": "💀 **{caster}** domina **{alvo}**! Controle temporário — o morto-vivo testará Vontade (CD {dif}) a cada rodada; 3 falhas seguidas = controle PERMANENTE."
  },
  "narracao.dominado_ataca_de_dano": {
    "en": "🧠 **{monstro}** (dominated) attacks **{alvo}**: {dmg} damage!",
    "pt": "🧠 **{monstro}** (dominado) ataca **{alvo}**: {dmg} de dano!"
  },
  "narracao.dominado_ataca_de_dano_2": {
    "en": "⚔️ **{a_nome}** (dominated) attacks **{target}**: **{dmg}** damage!",
    "pt": "⚔️ **{a_nome}** (dominado) ataca **{target}**: **{dmg}** de dano!"
  },
  "narracao.dominado_ataca_e_erra": {
    "en": "🧠 **{monstro}** (dominated) attacks **{alvo}** and misses!",
    "pt": "🧠 **{monstro}** (dominado) ataca **{alvo}** e erra!"
  },
  "narracao.dominado_ataca_e_erra_2": {
    "en": "⚔️ **{a_nome}** (dominated) attacks **{target}** and misses.",
    "pt": "⚔️ **{a_nome}** (dominado) ataca **{target}** e erra."
  },
  "narracao.dominado_avanca_contra": {
    "en": "🧠 **{monstro}** (dominated) advances on **{alvo}**.",
    "pt": "🧠 **{monstro}** (dominado) avança contra **{alvo}**."
  },
  "narracao.dominado_nao_encontra_outro_inimigo": {
    "en": "🧠 **{monstro}** (dominated) finds no other enemy.",
    "pt": "🧠 **{monstro}** (dominado) não encontra outro inimigo."
  },
  "narracao.dor_constante_cobra_seu_preco_de_1_de_da": {
    "en": "💢 **Constant Pain** takes its toll on **{heroi}** — **1** damage.",
    "pt": "💢 **Dor Constante** cobra seu preço de **{heroi}** — **1** de dano."
  },
  "narracao.duracao.permanentemente": {
    "en": "permanently",
    "pt": "permanentemente"
  },
  "narracao.duracao.por_rodadas": {
    "en": "for {dur} round(s)",
    "pt": "por {dur} rodada(s)"
  },
  "narracao.e_arremessado_contra_a_parede_de_colisao": {
    "en": "🌪️ **{nome}** is thrown against the wall (+{col} collision damage).",
    "pt": "🌪️ **{nome}** é arremessado contra a parede (+{col} de colisão)."
  },
  "narracao.e_atacado_dormindo_golpe_critico_e_despe": {
    "en": "🌙 **{target}** is attacked while asleep — **CRITICAL** hit, and wakes up!",
    "pt": "🌙 **{target}** é atacado dormindo — golpe **CRÍTICO** e desperta!"
  },
  "narracao.e_atacado_dormindo_golpe_critico_e_despe_2": {
    "en": "🌙 **{tgt_name}** is attacked while asleep — **CRITICAL** hit, and wakes up!",
    "pt": "🌙 **{tgt_name}** é atacado dormindo — golpe **CRÍTICO** e desperta!"
  },
  "narracao.e_atingido_em_cheio_d20_12_de_dano": {
    "en": "❌ **{pl}** is hit square on (d20={d20}+{bonus}={total} < 12) — {dano_final} damage.",
    "pt": "❌ **{pl}** é atingido em cheio (d20={d20}+{bonus}={total} < 12) — {dano_final} de dano."
  },
  "narracao.e_destruido_e_explode": {
    "en": "💥 **{animado_get_nome_element}** is destroyed and EXPLODES!",
    "pt": "💥 **{animado_get_nome_element}** é destruído e EXPLODE!"
  },
  "narracao.e_destruido_pela_luz_sagrada_nao_ha_reto": {
    "en": "✨ **{monstro}** is **destroyed by holy light** — there is no return!",
    "pt": "✨ **{monstro}** é **destruído pela luz sagrada** — não há retorno!"
  },
  "narracao.e_empurrado_1_quadrado_pelo_golpe_de_ven": {
    "en": "💨 **{tgt_name}** is pushed 1 square by the Gust of Wind!",
    "pt": "💨 **{tgt_name}** é empurrado 1 quadrado pelo Golpe de Vento!"
  },
  "narracao.e_envenenado_por_de_dano_por_rodada_ate": {
    "en": "💀 **{alvo_nome}** is poisoned by **{nome}** — {dano_txt} damage per round (up to {dur} round(s); {regra_save})!",
    "pt": "💀 **{alvo_nome}** é envenenado por **{nome}** — {dano_txt} de dano por rodada (até {dur} rodada(s); {regra_save})!"
  },
  "narracao.e_envolvido_pela_onda_de_e_fica_preso": {
    "en": "🌊 **{target}** is engulfed by **{monstro}**'s wave and is trapped!",
    "pt": "🌊 **{target}** é envolvido pela onda de **{monstro}** e fica preso!"
  },
  "narracao.e_imune_a": {
    "en": "☠️ **{alvo_get_name_or_alvo_ge}** is immune to {nome}.",
    "pt": "☠️ **{alvo_get_name_or_alvo_ge}** é imune a {nome}."
  },
  "narracao.e_imune_a_cegueira": {
    "en": "🛡️ **{alvo_nome}** is **immune to blindness**!",
    "pt": "🛡️ **{alvo_nome}** é **imune a cegueira**!"
  },
  "narracao.e_imune_a_controle_mental": {
    "en": "🛡️ **{alvo}** is immune to mind control.",
    "pt": "🛡️ **{alvo}** é imune a controle mental."
  },
  "narracao.e_imune_a_encantamentos": {
    "en": "🛡️ **{alvo}** is immune to enchantments.",
    "pt": "🛡️ **{alvo}** é imune a encantamentos."
  },
  "narracao.e_imune_a_paralisia": {
    "en": "🛡️ **{alvo}** is immune to paralysis.",
    "pt": "🛡️ **{alvo}** é imune à paralisia."
  },
  "narracao.e_imune_ao_veneno_do_lacralion": {
    "en": "☠️ **{alvo_get_name_alvo}** is immune to the Lacralion's Venom.",
    "pt": "☠️ **{alvo_get_name_alvo}** é imune ao Veneno do Lacralion."
  },
  "narracao.e_inabalavel_e_ignora_a_imobilizacao": {
    "en": "🪨 **{nome}** is Unshakable and ignores the immobilization!",
    "pt": "🪨 **{nome}** é Inabalável e ignora a imobilização!"
  },
  "narracao.e_incapacitado_todas_as_habilidades_sagr": {
    "en": "💫 **{heroi}** is incapacitated — all holy abilities unravel.",
    "pt": "💫 **{heroi}** é incapacitado — todas as habilidades sagradas se desfazem."
  },
  "narracao.e_infectado_fortitude_vs_cd": {
    "en": "🦠 **{target}** is infected! (Fortitude {tot} vs DC {dc})",
    "pt": "🦠 **{target}** é infectado! (Fortitude {tot} vs CD {dc})"
  },
  "narracao.e_infectado_fortitude_vs_cd_2": {
    "en": "🦠 **{target}** is infected! (Fortitude {total_save} vs DC {dc})",
    "pt": "🦠 **{target}** é infectado! (Fortitude {total_save} vs CD {dc})"
  },
  "narracao.e_preso_pelo_rodamoinho_e_perde_o_movime": {
    "en": "🌪️ **{nome_criatura_criatura}** is caught by the whirlpool and loses the remaining movement of the turn!",
    "pt": "🌪️ **{nome_criatura_criatura}** é preso pelo rodamoinho e perde o movimento restante do turno!"
  },
  "narracao.e_queimado_pelo_corpo_em_chamas_de_dano": {
    "en": "🔥 **{heroi}** is burned by the Body in Flames: **{fogo_alvo}** damage!",
    "pt": "🔥 **{heroi}** é queimado pelo Corpo em Chamas: **{fogo_alvo}** de dano!"
  },
  "narracao.e_queimado_pelo_corpo_em_chamas_de_de_da": {
    "en": "🔥 **{heroi}** is burned by **{target}**'s Body of Flames: **{fogo_alvo}** damage!",
    "pt": "🔥 **{heroi}** é queimado pelo Corpo em Chamas de **{target}**: **{fogo_alvo}** de dano!"
  },
  "narracao.e_revigorado_pela_agua_e_recupera_hp": {
    "en": "🌊 **{monstro}** is revitalized by the water and recovers **{cura} HP**.",
    "pt": "🌊 **{monstro}** é revigorado pela água e recupera **{cura} HP**."
  },
  "narracao.e_sensivel_a_venenos_duracao_dobrada": {
    "en": "🧪 **{alvo_nome}** is sensitive to poison — duration doubled!",
    "pt": "🧪 **{alvo_nome}** é sensível a venenos — duração dobrada!"
  },
  "narracao.e_sensivel_a_venenos_efeitos_dobrados": {
    "en": "🧪 **{alvo_nome}** is **sensitive to poison** — effects doubled!",
    "pt": "🧪 **{alvo_nome}** é **sensível a venenos** — efeitos dobrados!"
  },
  "narracao.e_teletransportado_para_nova_posicao": {
    "en": "{alvo} is teleported to a new position.",
    "pt": "{alvo} é teletransportado para uma nova posição."
  },
  "narracao.efeito_de_expirou_em": {
    "en": "✅ **{efeito_get_nome_veneno}**'s effect expired on **{alvo_nome}**.",
    "pt": "✅ Efeito de **{efeito_get_nome_veneno}** expirou em **{alvo_nome}**."
  },
  "narracao.em_d20_vs_ca_de_dano_hp": {
    "en": "💢 **{monstro}** · {atk_name} on **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}):{crit_str} **{dmg_alvo}** damage! ({target_hp}/{target_max_hp} HP)",
    "pt": "💢 **{monstro}** · {atk_name} em **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}):{crit_str} **{dmg_alvo}** de dano! ({target_hp}/{target_max_hp} HP)"
  },
  "narracao.em_d20_vs_ca_de_dano_hp_2": {
    "en": "💢 **{monstro}** · {atk_name} on **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}):{crit_str} **{dmg}** damage! ({target_hp}/{target_max_hp} HP)",
    "pt": "💢 **{monstro}** · {atk_name} em **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}):{crit_str} **{dmg}** de dano! ({target_hp}/{target_max_hp} HP)"
  },
  "narracao.em_d20_vs_ca_de_dano_hp_3": {
    "en": "💢 **{monstro}** · {atk_name} on **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}):{crit_str} **{dmg_ef}** damage! ({target_vida_atual}/{target_vida_max} HP)",
    "pt": "💢 **{monstro}** · {atk_name} em **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}):{crit_str} **{dmg_ef}** de dano! ({target_vida_atual}/{target_vida_max} HP)"
  },
  "narracao.em_d20_vs_ca_errou": {
    "en": "💢 **{monstro}** · {atk_def_get_name_ataque} on **{tgt_name}** (d20={roll}+{m_atk}={total} vs AC {effective_ac}): **MISS!**",
    "pt": "💢 **{monstro}** · {atk_def_get_name_ataque} em **{tgt_name}** (d20={roll}+{m_atk}={total} vs CA {effective_ac}): **ERROU!**"
  },
  "narracao.em_por_rodada_s": {
    "en": "☠️ **{nome}**: {_txt} on **{alvo_nome}** for {duracao} round(s).",
    "pt": "☠️ **{nome}**: {_txt} em **{alvo_nome}** por {duracao} rodada(s)."
  },
  "narracao.em_reflexos_vs_cd_e_sofre_de_fogo": {
    "en": "🔥 **{nome}** {passa_if_passou_else_fal} the Reflex save ({total} vs DC {cd}) and takes **{dano}** fire damage.",
    "pt": "🔥 **{nome}** {passa_if_passou_else_fal} em Reflexos ({total} vs CD {cd}) e sofre **{dano}** de fogo."
  },
  "narracao.em_reflexos_vs_cd_e_sofre_de_fogo_2": {
    "en": "🔥 **{heroi}** {resultado} the Reflex save ({total_save} vs DC {cd}) and takes **{dano_alvo}** fire damage.",
    "pt": "🔥 **{heroi}** {resultado} em Reflexos ({total_save} vs CD {cd}) e sofre **{dano_alvo}** de fogo."
  },
  "narracao.encerra_a_cancao_heroica": {
    "en": "🔇 **{heroi}** ends the Heroic Song.",
    "pt": "🔇 **{heroi}** encerra a Canção Heroica."
  },
  "narracao.encerra_a_prisao_de_chamas": {
    "en": "{caster} ends the Prison of Flames as a free action.",
    "pt": "{caster} encerra a Prisão de Chamas como ação livre."
  },
  "narracao.encerra_a_protecao_protetor_desativado": {
    "en": "🛡️ **{heroi}** ends the protection — Protector deactivated.",
    "pt": "🛡️ **{heroi}** encerra a proteção — Protetor desativado."
  },
  "narracao.encerra_a_regeneracao_divina": {
    "en": "✨ **{heroi}** ends the Divine Regeneration.",
    "pt": "✨ **{heroi}** encerra a Regeneração Divina."
  },
  "narracao.encheu_uma_garrafa_de_agua_na_fonte_rest": {
    "en": "💧 **{heroi}** filled a **Water Bottle** at the fountain ({d_charges} left).",
    "pt": "💧 **{heroi}** encheu uma **Garrafa de Água** na fonte ({d_charges} restantes)."
  },
  "narracao.encontrou_o_objeto_chave": {
    "en": "🔑 **{heroi}** found the key object!",
    "pt": "🔑 **{heroi}** encontrou o objeto-chave!"
  },
  "narracao.engole": {
    "en": "🦖 **{monstro}** swallows **{preso_get_name_or_preso}** whole!",
    "pt": "🦖 **{monstro}** engole **{preso_get_name_or_preso}**!"
  },
  "narracao.entoa_a_cancao_heroica_aliados_em_quadra": {
    "en": "🎵 **{heroi}** strikes up the **Heroic Song** [{labels}]! Allies within {CANCAO_RAIO} squares are inspired (🍖-{custo_fome} 💧-{custo_sede}).",
    "pt": "🎵 **{heroi}** entoa a **Canção Heroica** [{labels}]! Aliados em {CANCAO_RAIO} quadrados são inspirados (🍖-{custo_fome} 💧-{custo_sede})."
  },
  "narracao.entoa_o_dueto_marcial_por_rodada_s": {
    "en": "🎼 **{heroi}** sings the **Martial Duet** for {st_duracao} round(s)!",
    "pt": "🎼 **{heroi}** entoa o **Dueto Marcial** por {st_duracao} rodada(s)!"
  },
  "narracao.entra_em_furia_berserker_e_desfere_um_at": {
    "en": "🔥 {monstro} flies into **Berserker Rage** and lands an extra attack.",
    "pt": "{monstro} entra em Fúria Berserker e desfere um ataque adicional."
  },
  "narracao.entra_em_furia_berserker_e_repete_seus_a": {
    "en": "{nome_criatura_m} flies into a Berserker Rage and repeats its claw attacks.",
    "pt": "{nome_criatura_m} entra em Fúria Berserker e repete seus ataques de garras."
  },
  "narracao.entra_em_furia_cega_1_de_dano_mas_1_ca": {
    "en": "😡 **{monstro}** flies into **Blind Rage**! +1 damage, but -1 AC.",
    "pt": "😡 **{monstro}** entra em **Fúria Cega**! +1 de dano, mas -1 CA."
  },
  "narracao.entra_em_panico_amedrontado_r": {
    "en": "📯 **{monstro}** panics (Frightened {st_medo}r)!",
    "pt": "📯 **{monstro}** entra em pânico (Amedrontado {st_medo}r)!"
  },
  "narracao.entra_na_fase_2_e_passa_a_cacar_o_heroi": {
    "en": "⚔️ {nome_criatura_m} enters phase 2 and starts hunting the most wounded hero.",
    "pt": "⚔️ {nome_criatura_m} entra na fase 2 e passa a caçar o herói mais ferido."
  },
  "narracao.entrou_em_panico_vai_fugir_por_2_rodadas": {
    "en": "😱 **{monstro}** panicked! It will flee for 2 rounds. (d20={d20}{sb_str}={stot})",
    "pt": "😱 **{monstro}** entrou em pânico! Vai fugir por 2 rodadas. (d20={d20}{sb_str}={stot})"
  },
  "narracao.entrou_na_zona_de_fogo_e_sofre": {
    "en": "🔥 **{ator}** entered the fire zone and takes {d}!",
    "pt": "🔥 **{ator}** entrou na zona de fogo e sofre {d}!"
  },
  "narracao.enxerga_na_escuridao_e_ataca_com_vantage": {
    "en": "🌑 **{heroi}** sees in the dark and attacks with **advantage** (2d20, uses {roll}).",
    "pt": "🌑 **{heroi}** enxerga na escuridão e ataca com **vantagem** (2d20, usa {roll})."
  },
  "narracao.equipou": {
    "en": "{log_emoji} **{heroi}** equipped **{item}**!",
    "pt": "{log_emoji} **{heroi}** equipou **{item}**!"
  },
  "narracao.equipou_2a_arma_mao_esquerda": {
    "en": "{frase} (2nd weapon — off hand)",
    "pt": "{frase} (2ª arma — mão esquerda)"
  },
  "narracao.ergue_o_escudo_3_ca_ate_o_proximo_turno": {
    "en": "🛡️ **{heroi}** raises the shield! +3 AC until the next turn.",
    "pt": "🛡️ **{heroi}** ergue o escudo! +3 CA até o próximo turno."
  },
  "narracao.ergue_uma_barreira_arcana_reduz_de_todo": {
    "en": "🛡️ **{caster}** raises an **Arcane Barrier** — reduces **{reducao}** of all damage taken for **{dur} round(s)**.",
    "pt": "🛡️ **{caster}** ergue uma **Barreira Arcana** — reduz **{reducao}** de todo dano recebido por **{dur} rodada(s)**."
  },
  "narracao.erra_contra_vs_ca": {
    "en": "🐺 **{heroi}** misses {nome} against **{obj}** ({total} vs AC {ca}).",
    "pt": "🐺 **{heroi}** erra {nome} contra **{obj}** ({total} vs CA {ca})."
  },
  "narracao.erra_e_fica_desequilibrado_2_ca_ate_o_pr": {
    "en": "🐢 **{monstro}** misses and becomes unbalanced — **-2 AC** until the next turn!",
    "pt": "🐢 **{monstro}** erra e fica desequilibrado — **-2 CA** até o próximo turno!"
  },
  "narracao.erra_o_arremesso_em": {
    "en": "{defn_get_emoji} **{monstro}** misses the throw at **{target_get_name_target_g}**.",
    "pt": "{defn_get_emoji} **{monstro}** erra o arremesso em **{target_get_name_target_g}**."
  },
  "narracao.erra_o_golpe_de_mao_secundaria_d20_vs_ca": {
    "en": "🗡️ **{heroi}** misses the off-hand blow (d20={oroll}+{offhand_atk}={ototal} vs AC {tgt_ac}).",
    "pt": "🗡️ **{heroi}** erra o golpe de mão secundária (d20={oroll}+{offhand_atk}={ototal} vs CA {tgt_ac})."
  },
  "narracao.escapa_ao_ser_arrastado_por": {
    "en": "💨 **{c}** breaks free while being dragged by **{monstro}**!",
    "pt": "💨 **{c}** escapa ao ser arrastado por **{monstro}**!"
  },
  "narracao.escapa_da_paralisacao_com_forca": {
    "en": "💪 **{alvo}** breaks free of the freezing paralysis (Strength DC {dc}).",
    "pt": "💪 **{alvo}** escapa da paralisia congelante (Força CD {dc})."
  },
  "narracao.escapa_do_rodamoinho_profundo_e_pode_agi": {
    "en": "🌊 **{nome_criatura_criatura}** escapes the deep whirlpool and can act normally.",
    "pt": "🌊 **{nome_criatura_criatura}** escapa do rodamoinho profundo e pode agir normalmente."
  },
  "narracao.escuridao_criada_raio_rodada_s": {
    "en": "🌑 **Darkness** created — radius {raio}, {duracao} round(s).",
    "pt": "🌑 **Escuridão** criada — raio {raio}, {duracao} rodada(s)."
  },
  "narracao.esmaga_nas_mandibulas": {
    "en": "🦷 **{m}** crushes **{a}** in its jaws! {d} piercing damage (automatic)!",
    "pt": "🦷 **{m}** esmaga **{a}** nas mandíbulas! {d} de dano perfurante (automático)!"
  },
  "narracao.esquiva_da_explosao_d20_12_de_dano": {
    "en": "✅ **{pl}** dodges the blast (d20={d20}+{bonus}={total} ≥ 12) — {dano_final} damage.",
    "pt": "✅ **{pl}** esquiva da explosão (d20={d20}+{bonus}={total} ≥ 12) — {dano_final} de dano."
  },
  "narracao.esquiva_parcial_d20_12_de_dano": {
    "en": "🎲 **{monstro}** partially dodges (d20={d20}+{bonus}={total} ≥ 12) — {d} damage.",
    "pt": "🎲 **{monstro}** esquiva parcial (d20={d20}+{bonus}={total} ≥ 12) — {d} de dano."
  },
  "narracao.esta_apavorado_e_foge": {
    "en": "😱 **{monstro}** is terrified and flees!",
    "pt": "😱 **{monstro}** está apavorado e foge!"
  },
  "narracao.esta_apavorado_e_foge_encurralado": {
    "en": "😱 **{monstro}** is terrified and flees (cornered)!",
    "pt": "😱 **{monstro}** está apavorado e foge (encurralado)!"
  },
  "narracao.esta_derrubado_e_perde_o_movimento_deste": {
    "en": "🦵 **{heroi}** is knocked down and loses this turn's movement!",
    "pt": "🦵 **{heroi}** está derrubado e perde o movimento deste turno!"
  },
  "narracao.esta_dormindo_e_perde_o_turno": {
    "en": "🌙 **{monstro}** is asleep and loses the turn.",
    "pt": "🌙 **{monstro}** está dormindo e perde o turno."
  },
  "narracao.esta_dormindo_nao_pode_agir_neste_turno": {
    "en": "🌙 **{heroi}** is asleep — cannot act this turn.",
    "pt": "🌙 **{heroi}** está dormindo — não pode agir neste turno."
  },
  "narracao.esta_imobilizado_e_perdera_o_proximo_tur": {
    "en": "🕸️ **{tgt_name}** is immobilized and will lose the next turn!",
    "pt": "🕸️ **{tgt_name}** está imobilizado e perderá o próximo turno!"
  },
  "narracao.esta_imune_nao_faz_efeito": {
    "en": "🛡️ **{alvo}** is immune — **{magia}** has no effect.",
    "pt": "🛡️ **{alvo}** está imune — **{magia}** não faz efeito."
  },
  "narracao.esta_imunizado_contra_doencas": {
    "en": "🛡️ **{p_get_name_o_heroi}** is immune to diseases.",
    "pt": "🛡️ **{p_get_name_o_heroi}** está imunizado contra doenças."
  },
  "narracao.esta_imunizado_nao_faz_efeito": {
    "en": "🛡️ **{alvo_nome}** is immune — **{nome}** has no effect.",
    "pt": "🛡️ **{alvo_nome}** está imunizado — **{nome}** não faz efeito."
  },
  "narracao.esta_lento_e_perde_o_turno": {
    "en": "🐌 **{monstro}** is slowed and loses the turn.",
    "pt": "🐌 **{monstro}** está lento e perde o turno."
  },
  "narracao.esta_paralisado_novo_fortitude_por_rodad": {
    "en": "❄️ **{alvo}** is **paralyzed**! (new Fortitude save each round, max {alvo_paralisado_rodada_m})",
    "pt": "❄️ **{alvo}** está **paralisado**! (novo Fortitude por rodada, máx {alvo_paralisado_rodada_m})"
  },
  "narracao.esta_petrificado_e_perde_este_turno": {
    "en": "🗿 **{nome_criatura_monster}** is petrified and loses this turn.",
    "pt": "🗿 **{nome_criatura_monster}** está petrificado e perde este turno."
  },
  "narracao.esta_petrificado_e_perde_o_turno": {
    "en": "🗿 **{monstro}** is petrified and loses the turn!",
    "pt": "🗿 **{monstro}** está petrificado e perde o turno!"
  },
  "narracao.esta_preso_rede_e_perde_o_turno": {
    "en": "🕸️ **{monstro}** is trapped (net) and loses the turn!",
    "pt": "🕸️ **{monstro}** está preso (rede) e perde o turno!"
  },
  "narracao.esta_sob_comando_e_perde_a_acao": {
    "en": "🗣️ **{monstro}** is under Command and loses the action.",
    "pt": "🗣️ **{monstro}** está sob Comando e perde a ação."
  },
  "narracao.estanca_o_sangramento": {
    "en": "{heroi} stanches the Bleeding.",
    "pt": "{heroi} estanca o Sangramento."
  },
  "narracao.estanca_o_sangramento_mas_a_ferida_abe": {
    "en": "{heroi} stanches the Bleeding, but the Open Wound remains.",
    "pt": "{heroi} estanca o Sangramento, mas a Ferida Aberta permanece."
  },
  "narracao.evita_o_salto_selvagem_de_reflexos_vs_cd": {
    "en": "🦁 **{target_get_name_or_targe}** avoids **{monstro}**'s Savage Leap (Reflex {d20}{bonus_txt}={total} vs DC {dc}).",
    "pt": "🦁 **{target_get_name_or_targe}** evita o Salto Selvagem de **{monstro}** (Reflexos {d20}{bonus_txt}={total} vs CD {dc})."
  },
  "narracao.evitou": {
    "en": "✅ **{alvo_nome}** avoided **{tipo_nome}**!",
    "pt": "✅ **{alvo_nome}** evitou **{tipo_nome}**!"
  },
  "narracao.evitou_sem_dano": {
    "en": "✅ **{alvo_nome}** avoided **{nome}** without damage!",
    "pt": "✅ **{alvo_nome}** evitou **{nome}** sem dano!"
  },
  "narracao.explode_ao_morrer_de_fogo_em_raio_reflex": {
    "en": "💥 **{monstro}** explodes on death: {expressao} fire damage in radius {raio}! Reflex DC {cd} halves it.",
    "pt": "💥 **{monstro}** explode ao morrer: {expressao} de fogo em raio {raio}! Reflexos CD {cd} reduz à metade."
  },
  "narracao.explode_em_chamas_reflexos_cd_raio": {
    "en": "💥 **{monstro}** explodes in flames! (Reflex DC {cd}; radius {raio})",
    "pt": "💥 **{monstro}** explode em chamas! (Reflexos CD {cd}; raio {raio})"
  },
  "narracao.falha_ao_forcar_a_saida_do_estomago_de_f": {
    "en": "⛓️ **{heroi}** fails to force a way out of **{captor}**'s stomach (Strength {total} vs DC {dc}).",
    "pt": "⛓️ **{heroi}** falha ao forçar a saída do estômago de **{captor}** (Força {total} vs CD {dc})."
  },
  "narracao.falha_catastrofica_o_cadaver_de_ergue_se": {
    "en": "💀 **CATASTROPHIC FAILURE!** The corpse of **{corpse_nome}** rises HOSTILE! (d100={rolagem})",
    "pt": "💀 **FALHA CATASTRÓFICA!** O cadáver de **{corpse_nome}** ergue-se HOSTIL! (d100={rolagem})"
  },
  "narracao.falha_critica_a_armadilha_dispara_no_pro": {
    "en": "💀 Critical failure! The trap goes off on Luccas himself!",
    "pt": "💀 Falha crítica! A armadilha dispara no próprio Luccas!"
  },
  "narracao.falha_e_a_energia_se_perde_inutilmente": {
    "en": "🌫️ **{magia_nome}** fails and the energy is wasted.",
    "pt": "🌫️ **{magia_nome}** falha e a energia se perde inutilmente."
  },
  "narracao.falha_e_sofre_pen_ataque_1a_rodada": {
    "en": "fails and takes -1 on attack rolls for the first round",
    "pt": "falha e sofre -1 nas jogadas de ataque na primeira rodada"
  },
  "narracao.falha_em_animar_o_cadaver_permanece_iner": {
    "en": "💨 **{heroi}** fails to animate **{corpse_nome}** — the corpse stays inert. (d100={rolagem})",
    "pt": "💨 **{heroi}** falha em animar **{corpse_nome}** — o cadáver permanece inerte. (d100={rolagem})"
  },
  "narracao.falha_em_se_esconder_d20_vs": {
    "en": "❌ **{heroi}** fails to hide (d20={d20}+{bonus_dex}={total} vs {dificuldade}).",
    "pt": "❌ **{heroi}** falha em se esconder (d20={d20}+{bonus_dex}={total} vs {dificuldade})."
  },
  "narracao.falha_escape_paralisacao_com_forca": {
    "en": "❄️ **{alvo}** remains paralyzed — failed the Strength escape (DC {dc}).",
    "pt": "❄️ **{alvo}** continua paralisado — falhou no escape de Força (CD {dc})."
  },
  "narracao.falha_no_desarme_vs_tente_de_novo_no_pro": {
    "en": "❌ Disarm failed ({total} vs {dif}) — try again next turn.",
    "pt": "❌ Falha no desarme ({total} vs {dif}) — tente de novo no próximo turno."
  },
  "narracao.falha_no_olhar_petrificante_contra_cd_pe": {
    "en": "🗿 **{nome_criatura_alvo}** fails against the Petrifying Gaze ({total} vs DC {dc}) — petrification {alvo_petrificacao_marcas}/3.",
    "pt": "🗿 **{nome_criatura_alvo}** falha no Olhar Petrificante ({total} contra CD {dc}) — petrificação {alvo_petrificacao_marcas}/3."
  },
  "narracao.falhou_em_reflexos_e_sofre_de_dano": {
    "en": "{prefix} **{heroi}** failed the **Reflex** save (DC 13) and takes **{dano}** damage after the shield's reduction!",
    "pt": "{prefix} **{heroi}** falhou em **Reflexos** (CD 13) e sofre **{dano}** de dano após a redução do escudo!"
  },
  "narracao.fareja_a_presa_ferida_1_nas_mordidas": {
    "en": "🦎 **{monstro}** smells the wounded prey — **+1** to bites!",
    "pt": "🦎 **{monstro}** fareja a presa ferida — **+1** nas mordidas!"
  },
  "narracao.fareja_o_ar_mas_nao_encontra_alvo": {
    "en": "🐺 **{heroi}** sniffs the air, but finds no target.",
    "pt": "🐺 **{heroi}** fareja o ar, mas não encontra alvo."
  },
  "narracao.fase_concluida_retornem_a_cidade_antes_d": {
    "en": "🏆 Stage complete! Return to town before the next dungeon.",
    "pt": "🏆 Fase concluída! Retornem à cidade antes da próxima masmorra."
  },
  "narracao.faz_o_sino_ressoar_ecos_dolorosos_por_ro": {
    "en": "🔔 **{heroi}** makes the **Bell** ring out — painful echoes for {st_duracao} round(s)!",
    "pt": "🔔 **{heroi}** faz o **Sino** ressoar — ecos dolorosos por {st_duracao} rodada(s)!"
  },
  "narracao.fica_atordoado_fortitude_vs_cd_e_perde_a": {
    "en": "💫 **{tgt_name}** becomes **stunned** (Fortitude {stot} vs DC {dc}) and loses the next round!",
    "pt": "💫 **{tgt_name}** fica **atordoado** (Fortitude {stot} vs CD {dc}) e perde a próxima rodada!"
  },
  "narracao.fica_cambaleante_e_perde_sua_acao_de_ata": {
    "en": "🦖 **{monstro}** is left reeling and loses its attack action.",
    "pt": "🦖 **{monstro}** fica cambaleante e perde sua ação de ataque."
  },
  "narracao.fica_imobilizado_pelas_pincas_de_escape": {
    "en": "🦂 **{target}** is immobilized by **{monstro}**'s pincers! (escape: Fortitude DC {int_ab_get_dc_16_or_16})",
    "pt": "🦂 **{target}** fica imobilizado pelas pinças de **{monstro}**! (escape: Fortitude CD {int_ab_get_dc_16_or_16})"
  },
  "narracao.fica_imobilizado_pelo_salto_selvagem_de": {
    "en": "🦁 **{target_get_name_or_targe}** is Immobilized by **{monstro}**'s Savage Leap (Reflex {d20}{bonus_txt}={total} vs DC {dc}; escape: Strength DC {escape_dc}).",
    "pt": "🦁 **{target_get_name_or_targe}** fica Imobilizado pelo Salto Selvagem de **{monstro}** (Reflexos {d20}{bonus_txt}={total} vs CD {dc}; escape: Força CD {escape_dc})."
  },
  "narracao.fica_imobilizado_pelos_tentaculos_de_esc": {
    "en": "🦂 **{nome}** is Immobilized by **{monstro}**'s Tentacles (escape: Fortitude DC {int_ability_get_dc_17_or}).",
    "pt": "🦂 **{nome}** fica Imobilizado pelos Tentáculos de **{monstro}** (escape: Fortitude CD {int_ability_get_dc_17_or})."
  },
  "narracao.fica_invisivel_por_rodada_s_inimigos_nao": {
    "en": "🫥 **{caster}** turns invisible for {dur} round(s) — enemies can't target them; attacks with advantage; breaks on attacking/casting.",
    "pt": "🫥 **{caster}** fica invisível por {dur} rodada(s) — inimigos não o atacam; ataca com vantagem; quebra ao atacar/lançar."
  },
  "narracao.fica_lento_por_rodada_s": {
    "en": "🐌 **{alvo_nome}** is Slowed for {duracao} round(s).",
    "pt": "🐌 **{alvo_nome}** fica Lento por {duracao} rodada(s)."
  },
  "narracao.fica_preso_na_cola_movimento_reduzido_a": {
    "en": "🟢 **{nome}** is stuck in the glue — movement halved for {alvo_mov_reduzido_rodada} round(s)!",
    "pt": "🟢 **{nome}** fica preso na cola — movimento reduzido à metade por {alvo_mov_reduzido_rodada} rodada(s)!"
  },
  "narracao.fica_preso_na_rede_escapar_cd": {
    "en": "🕸️ **{nome}** is caught in the net! (escape: {es_tipo} DC {es_cd})",
    "pt": "🕸️ **{nome}** fica preso na rede! (escapar: {es_tipo} CD {es_cd})"
  },
  "narracao.fica_protegido_absorve_ate_de_dano_eleme": {
    "en": "🛡️ **{caster}** becomes protected: absorbs up to {reducao} elemental damage per round ({dur} round(s)).",
    "pt": "🛡️ **{caster}** fica protegido: absorve até {reducao} de dano elemental por rodada ({dur} rodada(s))."
  },
  "narracao.ficou_lento": {
    "en": "🐌 **{tgt_name}** became slowed!",
    "pt": "🐌 **{tgt_name}** ficou lento!"
  },
  "narracao.ficou_sem_flechas_e_recua": {
    "en": "🏹 **{monstro}** ran out of arrows and retreats!",
    "pt": "🏹 **{monstro}** ficou sem flechas e recua!"
  },
  "narracao.ficou_sem_virotes_e_tenta_fugir": {
    "en": "🏹 **{monstro}** ran out of bolts and tries to flee!",
    "pt": "🏹 **{monstro}** ficou sem virotes e tenta fugir!"
  },
  "narracao.finalmente_tomba_fortitude_vs_cd": {
    "en": "🧟 **{monstro}** finally falls (Fortitude {tot} vs DC {cd}).",
    "pt": "🧟 **{monstro}** finalmente tomba (Fortitude {tot} vs CD {cd})."
  },
  "narracao.foge_em_panico": {
    "en": "😱 **{monstro}** flees in panic!",
    "pt": "😱 **{monstro}** foge em pânico!"
  },
  "narracao.foi_amaldicoado": {
    "en": "☠️ **{alvo}** was cursed: **{mal_nome}** ({fonte}).",
    "pt": "☠️ **{alvo}** foi amaldiçoado: **{mal_nome}** ({fonte})."
  },
  "narracao.foi_amaldicoado_por_um_item": {
    "en": "☠️ **{heroi}** was cursed by an item: **{maldicoes_mid_nome}**.",
    "pt": "☠️ **{heroi}** foi amaldiçoado por um item: **{maldicoes_mid_nome}**."
  },
  "narracao.foi_cegado": {
    "en": "👁️ **{tgt_name}** was blinded!",
    "pt": "👁️ **{tgt_name}** foi cegado!"
  },
  "narracao.foi_derrotado_os_companheiros_devem_cont": {
    "en": "💔 **{heroi}** was defeated! The companions must carry on...",
    "pt": "💔 **{heroi}** foi derrotado! Os companheiros devem continuar..."
  },
  "narracao.foi_derrotado_xp": {
    "en": "💀 **{monstro}** was defeated! +{share_xp} XP!",
    "pt": "💀 **{monstro}** foi derrotado! +{share_xp} XP!"
  },
  "narracao.foi_derrotado_xp_2": {
    "en": "💀 **{monstro}** was defeated! +{share_xp} XP!{chest_msg}",
    "pt": "💀 **{monstro}** foi derrotado! +{share_xp} XP!{chest_msg}"
  },
  "narracao.foi_derrotado_xp_um_bau_de_saque_aparece": {
    "en": "💀 **{monstro}** was defeated! +{share_xp} XP! A **loot chest** appeared!",
    "pt": "💀 **{monstro}** foi derrotado! +{share_xp} XP! Um **baú de saque** apareceu!"
  },
  "narracao.foi_derrotado_xp_um_bau_de_saque_aparece_2": {
    "en": "💀 **{monstro}** was defeated! +{share_xp} XP. A **loot chest** appeared!{detalhe}",
    "pt": "💀 **{monstro}** foi derrotado! +{share_xp} XP. Um **baú de saque** apareceu!{detalhe}"
  },
  "narracao.foi_derrubado_d20_vs_cd_perde_o_moviment": {
    "en": "🐾 **{target}** was knocked down! (d20={d20}{sb_str}={stot} vs DC {dc}) — loses the remaining movement!",
    "pt": "🐾 **{target}** foi derrubado! (d20={d20}{sb_str}={stot} vs CD {dc}) — perde o movimento restante!"
  },
  "narracao.foi_destruido": {
    "en": "💨 **{animado_get_nome_servo}** was destroyed!",
    "pt": "💨 **{animado_get_nome_servo}** foi destruído!"
  },
  "narracao.foi_destruido_xp_os_ossos_perdem_a_estru": {
    "en": "💀 **{monstro}** was destroyed! +{share_xp} XP! The bones lose their magical structure.",
    "pt": "💀 **{monstro}** foi destruído! +{share_xp} XP! Os ossos perdem a estrutura mágica."
  },
  "narracao.foi_petrificado": {
    "en": "🗿 **{tgt_name}** was petrified!",
    "pt": "🗿 **{tgt_name}** foi petrificado!"
  },
  "narracao.foi_totalmente_petrificado_a_condicao_e": {
    "en": "🗿 **{nome_criatura_alvo}** was fully petrified. The condition is permanent until Purification.",
    "pt": "🗿 **{nome_criatura_alvo}** foi totalmente petrificado. A condição é permanente até Purificação."
  },
  "narracao.forca_a_sorte_e_acerta_com": {
    "en": "🎲 **{heroi}** forces Luck and hits **{alvo}** with {weapon_name} {dmg_detail} = **{dmg}**!",
    "pt": "🎲 **{heroi}** força a Sorte e acerta **{alvo}** com {weapon_name} {dmg_detail} = **{dmg}**!"
  },
  "narracao.fortitude_d20_vs_cd": {
    "en": "🎲 **{alvo_nome}** — Fortitude: d20({d20}){sb_str}={stot} vs DC {veneno_get_dificuldade_1} → {resistiu_if_save_ok_else}.",
    "pt": "🎲 **{alvo_nome}** — Fortitude: d20({d20}){sb_str}={stot} vs CD {veneno_get_dificuldade_1} → {resistiu_if_save_ok_else}."
  },
  "narracao.fortitude_d20_vs_cd_ao_veneno_do_lacrali": {
    "en": "☠️ **{alvo_nome}** — Fortitude d20={d20}{sb_txt}={total} vs DC {dc} → {resistiu_if_ok_else_falh} the Lacralion's Venom.",
    "pt": "☠️ **{alvo_nome}** — Fortitude d20={d20}{sb_txt}={total} vs CD {dc} → {resistiu_if_ok_else_falh} ao Veneno do Lacralion."
  },
  "narracao.fortuna_roubada_consome_ouros_de": {
    "en": "☠️ **Stolen Fortune** consumes **{perdido}** gold {motivo} from **{heroi}**.",
    "pt": "☠️ **Fortuna Roubada** consome **{perdido}** ouros {motivo} de **{heroi}**."
  },
  "narracao.fosso_perde_proxima_rodada": {
    "en": "🕳️ **{heroi}** is still inside the Pit and loses this entire round.",
    "pt": "🕳️ **{heroi}** ainda está no Fosso e perde esta rodada inteira."
  },
  "narracao.fosso_prende_heroi": {
    "en": "🕳️ **{heroi}** falls into the Pit and disappears from the map until the end of the next round.",
    "pt": "🕳️ **{heroi}** cai no Fosso e some do mapa até o fim da próxima rodada."
  },
  "narracao.frag_ferida_aberta": {
    "en": " +1 Open Wound",
    "pt": " +1 Ferida Aberta"
  },
  "narracao.frag_hemorragia": {
    "en": " + Haemorrhage",
    "pt": " + Hemorragia"
  },
  "narracao.furia_berserker_ataque_extra_disponivel": {
    "en": "🔥 **{heroi}** — Berserker Rage: extra attack available! Attack again.",
    "pt": "🔥 **{heroi}** — Fúria Berserker: ataque extra disponível! Ataque novamente."
  },
  "narracao.furia_bestial_sofre_de_dano": {
    "en": "🦷 **Bestial Fury**: **{alvo}** takes +**{extra}** damage!",
    "pt": "🦷 **Fúria Bestial**: **{alvo}** sofre +**{extra}** de dano!"
  },
  "narracao.furia_bestial_sofre_de_dano_2": {
    "en": "🦷 **Bestial Fury**: **{nome}** takes +**{extra}** damage!",
    "pt": "🦷 **Fúria Bestial**: **{nome}** sofre +**{extra}** de dano!"
  },
  "narracao.ganha_2_de_ca_por_1_rodada_ao_se_revelar": {
    "en": "🌀 **{heroi}** gains +2 AC for 1 round upon revealing themself!",
    "pt": "🌀 **{heroi}** ganha +2 de CA por 1 rodada ao se revelar!"
  },
  "narracao.gemina_em": {
    "en": "👯 **{heroi}** twins **{magia_nome}** onto **{alvo2_get_name_or_alvo2}**!",
    "pt": "👯 **{heroi}** gemina **{magia_nome}** em **{alvo2_get_name_or_alvo2}**!"
  },
  "narracao.gm.combat_start.0": {
    "en": "The battle begins! Show them what you are made of!",
    "pt": "O combate começa! Mostrem do que são capazes!"
  },
  "narracao.gm.combat_start.1": {
    "en": "Blades drawn! The enemy will give no quarter!",
    "pt": "Espadas em punho! O inimigo não dará trégua!"
  },
  "narracao.gm.combat_start.2": {
    "en": "Battle is joined! Fight with everything you have!",
    "pt": "Batalha declarada! Lutem com tudo!"
  },
  "narracao.gm.defeat.0": {
    "en": "The darkness has won... The dungeon remains perilous.",
    "pt": "A escuridão venceu... A masmorra permanece perigosa."
  },
  "narracao.gm.defeat.1": {
    "en": "Evil triumphed this time. But the legends of the fallen heroes will live on forever...",
    "pt": "O mal triunfou desta vez. Mas as lendas dos heróis caídos viverão eternamente..."
  },
  "narracao.gm.defeat.2": {
    "en": "The dungeon claims more victims. May they find peace beyond...",
    "pt": "A masmorra reivindica mais vítimas. Que encontrem paz além..."
  },
  "narracao.gm.intro.0": {
    "en": "Adventurers... The Fortress of Darkness awaits you. Monsters, traps and grim secrets dwell in its corridors. Only the bravest will survive. May fortune walk with you.",
    "pt": "Aventureiros... A Fortaleza das Trevas vos aguarda. Monstros, armadilhas e segredos sombrios residem em seus corredores. Apenas os mais corajosos sobreviverão. Que a sorte os acompanhe."
  },
  "narracao.gm.intro.1": {
    "en": "Legend tells of an ancient dragon guarding immeasurable treasure in the depths. Countless heroes have tried — none returned. Will you be the first to change that fate?",
    "pt": "A lenda fala de um dragão ancião que guarda tesouros imensuráveis nas profundezas. Inúmeros heróis tentaram — nenhum voltou. Serão vocês os primeiros a mudar esse destino?"
  },
  "narracao.gm.intro.2": {
    "en": "An ancient darkness has taken the dungeon. The villagers are counting on you. Enter with caution... evil is watching.",
    "pt": "Uma escuridão antiga tomou conta da masmorra. Os aldeões dependem de vocês. Entre com cautela... o mal os observa."
  },
  "narracao.gm.monster_moves.0": {
    "en": "The creatures advance through the shadows...",
    "pt": "As criaturas avançam nas sombras..."
  },
  "narracao.gm.monster_moves.1": {
    "en": "Heavy footsteps echo down the corridors. The monsters draw near.",
    "pt": "Passos pesados ecoam pelos corredores. Os monstros se aproximam."
  },
  "narracao.gm.monster_moves.2": {
    "en": "The enemy advances! Be ready!",
    "pt": "Os inimigos avançam! Estejam preparados!"
  },
  "narracao.gm.room_boss.0": {
    "en": "An unnatural cold fills the air. A malevolent presence waits...",
    "pt": "Um frio sobrenatural toma conta do ambiente. Uma presença maligna aguarda..."
  },
  "narracao.gm.room_boss.1": {
    "en": "Deep roars echo. The lord of darkness awaits you!",
    "pt": "Rugidos profundos ecoam. O senhor das trevas os aguarda!"
  },
  "narracao.gm.room_boss.2": {
    "en": "The darkness thickens. This is the final trial. All or nothing!",
    "pt": "A escuridão se adensa. Este é o desafio final. Tudo ou nada!"
  },
  "narracao.gm.room_chest.0": {
    "en": "An ancient chest rests at the centre. Could there be treasure?",
    "pt": "Um baú antigo repousa no centro. Será que há tesouros?"
  },
  "narracao.gm.room_chest.1": {
    "en": "An ornate coffer, unopened for centuries...",
    "pt": "Um cofre ornamentado que não era aberto há séculos..."
  },
  "narracao.gm.room_chest.2": {
    "en": "Among the rubble, a gleaming chest!",
    "pt": "Entre os destroços, um baú reluzente!"
  },
  "narracao.gm.room_empty.0": {
    "en": "The chamber seems empty... for now.",
    "pt": "A câmara parece vazia... por enquanto."
  },
  "narracao.gm.room_empty.1": {
    "en": "A heavy silence. Only dust and shadows.",
    "pt": "Silêncio pesado. Apenas poeira e sombras."
  },
  "narracao.gm.room_empty.2": {
    "en": "Nothing obvious here. But stay alert.",
    "pt": "Nada de óbvio aqui. Mas fiquem alertas."
  },
  "narracao.gm.room_monster.0": {
    "en": "Beware! Creatures emerge from the shadows!",
    "pt": "Cuidado! Criaturas emergem das sombras!"
  },
  "narracao.gm.room_monster.1": {
    "en": "A roar echoes off the walls. Enemies in sight!",
    "pt": "Um rugido ecoa pelas paredes. Inimigos à vista!"
  },
  "narracao.gm.room_monster.2": {
    "en": "Eyes gleam in the darkness. Ready yourselves for a fight!",
    "pt": "Olhos brilham na escuridão. Preparem-se para lutar!"
  },
  "narracao.gm.room_trap.0": {
    "en": "The floor sounds wrong. Tread very carefully...",
    "pt": "O chão soa estranho. Pisem com muito cuidado..."
  },
  "narracao.gm.room_trap.1": {
    "en": "Marks on the walls speak of battles past. Someone suffered here.",
    "pt": "Marcas nas paredes revelam combates passados. Alguém já sofreu aqui."
  },
  "narracao.gm.room_trap.2": {
    "en": "Something feels wrong about this room...",
    "pt": "Algo parece errado nesta sala..."
  },
  "narracao.gm.victory.0": {
    "en": "VICTORY! The heroes have slain the dragon and saved the realm! Your legend will be told for generations!",
    "pt": "VITÓRIA! Os heróis derrotaram o dragão e salvaram o reino! Sua lenda será contada por gerações!"
  },
  "narracao.gm.victory.1": {
    "en": "Evil is banished! The realm is safe, thanks to the courage of all of you!",
    "pt": "O mal foi banido! O reino está salvo graças à coragem de todos!"
  },
  "narracao.gm.victory.2": {
    "en": "GLORY TO THE ADVENTURERS! The darkness has retreated!",
    "pt": "GLÓRIA AOS AVENTUREIROS! A escuridão recuou!"
  },
  "narracao.golpe_sagrado_de_se_desfaz_recursos_insu": {
    "en": "⚔️ **{heroi}**'s Holy Strike unravels — insufficient resources.",
    "pt": "⚔️ Golpe Sagrado de **{heroi}** se desfaz — recursos insuficientes."
  },
  "narracao.golpe_sagrado_de_sustentado_1_1": {
    "en": "⚔️ **{heroi}**'s Holy Strike sustained 🍖-1 💧-1.",
    "pt": "⚔️ Golpe Sagrado de **{heroi}** sustentado 🍖-1 💧-1."
  },
  "narracao.golpeia_o_tambor_de_guerra_onda_sonora_r": {
    "en": "🥁 **{heroi}** strikes the **War Drum** — sound wave (radius {st_raio})!",
    "pt": "🥁 **{heroi}** golpeia o **Tambor de Guerra** — onda sonora (raio {st_raio})!"
  },
  "narracao.guardou_na_bolsa_total": {
    "en": "📦 **{heroi}** stowed **{item}** in the bag ({existing_ammo_count} total)!",
    "pt": "📦 **{heroi}** guardou **{item}** na bolsa ({existing_ammo_count} total)!"
  },
  "narracao.guerreiro_da_luz_de_se_apaga_recursos_in": {
    "en": "💡 **{heroi}**'s Warrior of Light fades — insufficient resources.",
    "pt": "💡 Guerreiro da Luz de **{heroi}** se apaga — recursos insuficientes."
  },
  "narracao.guerreiro_da_luz_de_sustentado": {
    "en": "💡 **{heroi}**'s Warrior of Light sustained 🍖-{custo_fome} 💧-{custo_sede}.",
    "pt": "💡 Guerreiro da Luz de **{heroi}** sustentado 🍖-{custo_fome} 💧-{custo_sede}."
  },
  "narracao.henrique_foi_incapacitado": {
    "en": "Henrique was incapacitated",
    "pt": "Henrique foi incapacitado"
  },
  "narracao.impoe_pressao_constante": {
    "en": "{monstro} applies Constant Pressure: -2 AC for 2 rounds.",
    "pt": "{monstro} impõe Pressão Constante: -2 CA por 2 rodadas."
  },
  "narracao.improvisa_a_sinfonia_heroica_por_1_rodad": {
    "en": "🪗 **{heroi}** improvises the **Heroic Symphony** for 1 round!",
    "pt": "🪗 **{heroi}** improvisa a **Sinfonia Heroica** por 1 rodada!"
  },
  "narracao.improvisa_e_desafina_1_em_ataques_e_cds": {
    "en": "🪗 **{heroi}** improvises and goes **out of tune** — -1 to attacks and DCs until the next turn.",
    "pt": "🪗 **{heroi}** improvisa e **desafina** — -1 em ataques e CDs até o próximo turno."
  },
  "narracao.improvisa_e_desafina_de_leve_nada_aconte": {
    "en": "🪗 **{heroi}** improvises… and goes slightly off-key (nothing happens).",
    "pt": "🪗 **{heroi}** improvisa… e desafina de leve (nada acontece)."
  },
  "narracao.inicia_o_requiem_final_sobre": {
    "en": "🎻 **{heroi}** begins the **Final Requiem** on **{monstro}**!",
    "pt": "🎻 **{heroi}** inicia o **Réquiem Final** sobre **{monstro}**!"
  },
  "narracao.invoca_cura_em_area_d8_hp_no_raio_q_cura": {
    "en": "🌟 **{heroi}** calls down **Mass Heal** — {num_dados}d8({dados_str}){if_bonus_int_0_else}{bonus_int} HP within radius {raio}sq | {len_curados} healed{join_curados_if_curados} (🍖-{custo_fome} 💧-{custo_sede})",
    "pt": "🌟 **{heroi}** invoca **Cura em Área** — {num_dados}d8({dados_str}){if_bonus_int_0_else}{bonus_int} HP no raio {raio}q | {len_curados} curado(s){join_curados_if_curados} (🍖-{custo_fome} 💧-{custo_sede})"
  },
  "narracao.invoca_golpe_sagrado_1d8_de_dano_sagrado": {
    "en": "⚔️ **{heroi}** calls on **Holy Strike** — +1d8 holy damage per attack! (🍖-{fome_cost} 💧-{sede_cost})",
    "pt": "⚔️ **{heroi}** invoca **Golpe Sagrado** — +1d8 de dano sagrado por ataque! (🍖-{fome_cost} 💧-{sede_cost})"
  },
  "narracao.invoca_luz_sagrada_2d6_int_dano_sagrado": {
    "en": "☀️ **{heroi}** invokes **Holy Light**! 2d6+INT holy damage to all enemies!",
    "pt": "☀️ **{heroi}** invoca **Luz Sagrada**! 2d6+INT dano sagrado em todos os inimigos!"
  },
  "narracao.ira_da_rocha_ardente_cria_lava": {
    "en": "🌋 **{caster}** invokes **Wrath of the Burning Rock**: a **{lado}x{lado}** lava area rises for **{dur}** round(s), at a range of **{alcance}** squares. **{chamas}** Living Flame(s) await tile selection.",
    "pt": "🌋 **{caster}** invoca **Ira da Rocha Ardente**: uma área de lava **{lado}x{lado}** surge por **{dur}** rodada(s), ao alcance de **{alcance}** casas. **{chamas}** Chama(s) Viva(s) aguardam a escolha das casas."
  },
  "narracao.ira_da_rocha_ardente_se_dissipa": {
    "en": "🌋 The **Wrath of the Burning Rock** area dissipates; the lava and Living Flames disappear.",
    "pt": "🌋 A área da **Ira da Rocha Ardente** se dissipa; a lava e as Chamas Vivas desaparecem."
  },
  "narracao.ira_da_rocha_chamas_vivas_colocadas": {
    "en": "🔥 **{caster}** places **{chamas}** Living Flame(s); they deal **2d4 fire** when touched and remain for **{dur}** round(s).",
    "pt": "🔥 **{caster}** posiciona **{chamas}** Chama(s) Viva(s); elas causam **2d4 de fogo** ao serem tocadas e permanecem por **{dur}** rodada(s)."
  },
  "narracao.ira_da_rocha_sem_casa_para_chama_viva": {
    "en": "🌋 There were no free tiles for Living Flames. The lava remains for **{dur}** round(s).",
    "pt": "🌋 Não havia casas livres para criar Chamas Vivas. A lava permanece por **{dur}** rodada(s)."
  },
  "narracao.ja_usou_sua_acao_bonus_neste_turno": {
    "en": "⚠️ **{heroi}** already used their bonus action this turn.",
    "pt": "⚠️ **{heroi}** já usou sua ação bônus neste turno."
  },
  "narracao.joga_sobre_si_e_apaga_as_chamas": {
    "en": "💧 **{heroi}** pours **{item}** over themself and puts out the flames!",
    "pt": "💧 **{heroi}** joga **{item}** sobre si e apaga as chamas!"
  },
  "narracao.lanca_abencoar_em_aliado_s_1_ataque_dano": {
    "en": "✨ **{monstro}** casts **Bless** on {n} ally(ies): +1 attack/damage/AC/saves for {dur} round(s)!",
    "pt": "✨ **{monstro}** lança **Abençoar** em {n} aliado(s): +1 ataque/dano/CA/resistência por {dur} rodada(s)!"
  },
  "narracao.lanca_amaldicoar_em_heroi_s_1_ataque_dan": {
    "en": "☠️ **{monstro}** casts **Curse** on {n} hero(es): -1 attack/damage/AC/saves for {dur} round(s)!",
    "pt": "☠️ **{monstro}** lança **Amaldiçoar** em {n} herói(s): -1 ataque/dano/CA/resistência por {dur} rodada(s)!"
  },
  "narracao.lanca_bola_de_fogo_inimigo_s_sofrem_de_d": {
    "en": "🔥 **{heroi}** casts **Fireball**{extra}! {len_alive_monsters} enemy(ies) take ~**{avg}** damage (4d6+INT)!",
    "pt": "🔥 **{heroi}** lança **Bola de Fogo**{extra}! {len_alive_monsters} inimigo(s) sofrem ~**{avg}** de dano (4d6+INT)!"
  },
  "narracao.lanca_bola_de_fogo_nivel_alcance_q_area": {
    "en": "🔥 **{caster}** casts **Fireball** (level {nivel}) — {dano_txt} | range {alcance}sq | 3x3 area | {atingidos} hit.",
    "pt": "🔥 **{caster}** lança **Bola de Fogo** (nível {nivel}) — {dano_txt} | alcance {alcance}q | área 3x3 | {atingidos} atingido(s)."
  },
  "narracao.lanca_bomba_de_fumaca_os_inimigos_errara": {
    "en": "💨 **{heroi}** throws a **Smoke Bomb**! Enemies will miss their next attack.",
    "pt": "💨 **{heroi}** lança **Bomba de Fumaça**! Os inimigos errarão o próximo ataque."
  },
  "narracao.lanca_clarividencia": {
    "en": "🔮 **{caster}** casts Clairvoyance — {partes} ({dur} round(s)).",
    "pt": "🔮 **{caster}** lança Clarividência — {partes} ({dur} rodada(s))."
  },
  "narracao.lanca_jato_de_ar_alvo_s_no_cone": {
    "en": "🌪️ **{caster}** casts Gust of Wind — {n} target(s) in the cone.",
    "pt": "🌪️ **{caster}** lança Jato de Ar — {n} alvo(s) no cone."
  },
  "narracao.lanca_lentidao_alvo_s_afetado_s_por_roda": {
    "en": "🐌 **{caster}** casts Slow — {n} target(s) affected for {dur} round(s) (affects allies/minions).",
    "pt": "🐌 **{caster}** lança Lentidão — {n} alvo(s) afetado(s) por {dur} rodada(s) (afeta aliados/minions)."
  },
  "narracao.lanca_medo_alvo_s_afetado_s_por_rodada_s": {
    "en": "😱 **{caster}** casts Fear — {n} target(s) affected for {dur} round(s) (-1 attack; affects allies/minions).",
    "pt": "😱 **{caster}** lança Medo — {n} alvo(s) afetado(s) por {dur} rodada(s) (-1 ataque; afeta aliados/minions)."
  },
  "narracao.lanca_raio_congelante_d4_sem_save_em": {
    "en": "❄️ **{caster}** casts **Ray of Frost**: {nd}d4 = {dano} (no save) on **{alvo}**.",
    "pt": "❄️ **{caster}** lança **Raio Congelante**: {nd}d4 = {dano} (sem save) em **{alvo}**."
  },
  "narracao.lanca_relampago": {
    "en": "⚡ **{caster}** casts **Lightning Bolt** (level {nivel}, range {alcance}sq w/ ricochet) — hits: {impactos}{multi}{caster_ferido}",
    "pt": "⚡ **{caster}** lança **Relâmpago** (nível {nivel}, alcance {alcance}q c/ ricochete) — impactos: {impactos}{multi}{caster_ferido}"
  },
  "narracao.lanca_sono_alvo_s_adormecem_por_ate_roda": {
    "en": "🌙 **{caster}** casts Sleep — {n} target(s) fall asleep for up to {dur} round(s) (also affects allies/minions).",
    "pt": "🌙 **{caster}** lança Sono — {n} alvo(s) adormecem por até {dur} rodada(s) (afeta aliados/minions também)."
  },
  "narracao.largou_no_chao": {
    "en": "🎒 **{heroi}** dropped **{item}** on the ground.",
    "pt": "🎒 **{heroi}** largou **{item}** no chão."
  },
  "narracao.libertou_o_prisioneiro": {
    "en": "🔓 **{heroi}** freed the prisoner!",
    "pt": "🔓 **{heroi}** libertou o prisioneiro!"
  },
  "narracao.loot_de_deixado_no_chao": {
    "en": "🎒 **{monstro}**'s loot was left on the ground!",
    "pt": "🎒 Loot de **{monstro}** deixado no chão!"
  },
  "narracao.mantem_a_concentracao_vontade_vs_cd_10": {
    "en": "🧙 **{monstro}** maintains concentration (Will {tot} vs DC 10).",
    "pt": "🧙 **{monstro}** mantém a concentração (Vontade {tot} vs CD 10)."
  },
  "narracao.mantem_o_sangue_frio_e_rola_novamente": {
    "en": "🧊 **{heroi}** keeps a cool head and rolls again!",
    "pt": "🧊 **{heroi}** mantém o sangue frio e rola novamente!"
  },
  "narracao.mantem_presa_e_causa_de_dano_automatico": {
    "en": "{nome_criatura_m} keeps {nome_criatura_presa} pinned and deals {dano} automatic damage ({expressao}).",
    "pt": "{nome_criatura_m} mantém {nome_criatura_presa} presa e causa {dano} de dano automático ({expressao})."
  },
  "narracao.mantem_protetor_sobre_1": {
    "en": "🛡️ **{heroi}** maintains Protector over **{alvo}** 🍖-1.",
    "pt": "🛡️ **{heroi}** mantém Protetor sobre **{alvo}** 🍖-1."
  },
  "narracao.mensagem": {
    "en": "{emoji} **{target}** {txt_livre} {rolagem}.",
    "pt": "{emoji} **{target}** {txt_livre} {rolagem}."
  },
  "narracao.metamagia": {
    "en": "🔮 **{heroi}** — metamagic: {join_partes}{custo_txt}.",
    "pt": "🔮 **{heroi}** — metamagia: {join_partes}{custo_txt}."
  },
  "narracao.motivo_meta.fim_da_magia": {
    "en": "the spell ended",
    "pt": "fim da magia"
  },
  "narracao.motivo_meta.forma_zerou": {
    "en": "the form dropped to 0 HP",
    "pt": "a forma chegou a 0 PV"
  },
  "narracao.motivo_meta.mago_morreu": {
    "en": "the mage died",
    "pt": "o mago morreu"
  },
  "narracao.motivo_meta.retorno_cidade": {
    "en": "returned to town",
    "pt": "retorno à cidade"
  },
  "narracao.motivo_meta.sem_fome_sede": {
    "en": "not enough Hunger or Thirst",
    "pt": "falta de Fome ou Sede"
  },
  "narracao.motivo_meta.tres_resistencias": {
    "en": "three saves against permanence",
    "pt": "três resistências à permanência"
  },
  "narracao.n_animado": {
    "en": "{n} minion",
    "pt": "{n} animado"
  },
  "narracao.n_animados": {
    "en": "{n} minions",
    "pt": "{n} animados"
  },
  "narracao.nao_afeta_imune_a_venenos": {
    "en": "🧪 **{nome}** doesn't affect **{alvo_nome}** (immune to poisons).",
    "pt": "🧪 **{nome}** não afeta **{alvo_nome}** (imune a venenos)."
  },
  "narracao.nao_esta_mais_petrificado": {
    "en": "✅ **{alvo_nome}** is no longer petrified.",
    "pt": "✅ **{alvo_nome}** não está mais petrificado."
  },
  "narracao.nao_pode_se_mover": {
    "en": "{emoji} **{target}** {txt_preso} **{monstro}**! {rolagem} — cannot move!",
    "pt": "{emoji} **{target}** {txt_preso} **{monstro}**! {rolagem} — não pode se mover!"
  },
  "narracao.nenhum_impacto": {
    "en": "none",
    "pt": "nenhum"
  },
  "narracao.neutraliza": {
    "en": "☑️ **{alvo_nome}** neutralizes **{efeito_get_nome_veneno}**!",
    "pt": "☑️ **{alvo_nome}** neutraliza **{efeito_get_nome_veneno}**!"
  },
  "narracao.npc_fala": {
    "en": "💬 **{npc}**: {texto}{renome}{item_note}",
    "pt": "💬 **{npc}**: {texto}{renome}{item_note}"
  },
  "narracao.npc_renome": {
    "en": " (Renown {bonus})",
    "pt": " (Renome {bonus})"
  },
  "narracao.o_acido_corroi_a_defesa_de_ca": {
    "en": "🧪 The acid corrodes **{nome}**'s defense: AC {base} → {novo}!",
    "pt": "🧪 O ácido corrói a defesa de **{nome}**: CA {base} → {novo}!"
  },
  "narracao.o_acido_gruda_em_de_dano_residual_na_pro": {
    "en": "🧪 The acid clings to **{target}** — **{dmg_2}** residual damage next round!",
    "pt": "🧪 O ácido gruda em **{target}** — **{dmg_2}** de dano residual na próxima rodada!"
  },
  "narracao.o_bau_esta_vazio_e_desaparece": {
    "en": "🔲 The chest is empty and disappears.",
    "pt": "🔲 O baú está vazio e desaparece."
  },
  "narracao.o_chao_permanece_em_chamas_por_rodada_s": {
    "en": "🔥 The ground stays ablaze for {ability_get_duration_2} round(s). Entering or starting your turn in the area deals 1d6 fire damage.",
    "pt": "🔥 O chão permanece em chamas por {ability_get_duration_2} rodada(s). Entrar ou iniciar o turno na área causa 1d6 de fogo."
  },
  "narracao.o_controle_sobre_se_rompe_volta_a_ser_ho": {
    "en": "💀 Control over **{monstro}** breaks — it turns hostile again.",
    "pt": "💀 O controle sobre **{monstro}** se rompe — volta a ser hostil."
  },
  "narracao.o_corpo_do_deixa_escapar": {
    "en": "🦖 The body of **{monstro}** lets **{c_get_name_or_c_get_nome}** escape.",
    "pt": "🦖 O corpo do **{monstro}** deixa **{c_get_name_or_c_get_nome}** escapar."
  },
  "narracao.o_dominio_de_sobre_torna_se_permanente": {
    "en": "💀 **{heroi}**'s control over **{a_nome}** becomes PERMANENT!",
    "pt": "💀 O domínio de **{heroi}** sobre **{a_nome}** torna-se PERMANENTE!"
  },
  "narracao.o_eco_da_morte_atravessa_de_dano": {
    "en": "💀 The **Echo of Death** tears through **{q}** — **{self_eco_morte_dano}** damage.",
    "pt": "💀 O **Eco da Morte** atravessa **{q}** — **{self_eco_morte_dano}** de dano."
  },
  "narracao.o_efeito_do_olhar_petrificante_termina_e": {
    "en": "✨ The Petrifying Gaze effect ends on **{nome_criatura_alvo}**.",
    "pt": "✨ O efeito do Olhar Petrificante termina em **{nome_criatura_alvo}**."
  },
  "narracao.o_estomago_e_rompido_por_dentro_sofre_de": {
    "en": "💥 The stomach bursts from the inside: **{captor}** takes **{interno}** internal damage and is left reeling.",
    "pt": "💥 O estômago é rompido por dentro: **{captor}** sofre **{interno}** de dano interno e fica cambaleante."
  },
  "narracao.o_grupo_parte_para_etapa_fome_sede_por_h": {
    "en": "The group sets out for **{adventure_nome}** — stage {stage_index_1}/{len_stages} (hunger -{fome}, thirst -{sede} per hero).",
    "pt": "O grupo parte para **{adventure_nome}** — etapa {stage_index_1}/{len_stages} (fome -{fome}, sede -{sede} por herói)."
  },
  "narracao.o_grupo_viajou_de_para_por_heroi": {
    "en": "🧭 The group traveled from **{origem}** to **{world_locations_destinat}** (🍖-{cost_fome} 💧-{cost_sede} per hero).",
    "pt": "🧭 O grupo viajou de **{origem}** para **{world_locations_destinat}** (🍖-{cost_fome} 💧-{cost_sede} por herói)."
  },
  "narracao.o_mestre_caiu_os_monstros_voltam_ao_cont": {
    "en": "🔌 The Game Master disconnected — monsters return to AI control.",
    "pt": "🔌 O mestre caiu — os monstros voltam ao controle da IA."
  },
  "narracao.o_mestre_reconectou_se": {
    "en": "🔌 The Game Master **{name}** reconnected.",
    "pt": "🔌 O mestre **{name}** reconectou-se."
  },
  "narracao.o_necromante_domina_permanentemente": {
    "en": "💀 The necromancer dominates **{a_nome}** PERMANENTLY!",
    "pt": "💀 O necromante domina **{a_nome}** PERMANENTEMENTE!"
  },
  "narracao.o_necromante_toma_o_controle_de_testara": {
    "en": "💀 The necromancer seizes control of **{alvo_nome}**! It will make a Will save (DC {dc}) each round; 3 failures in a row = PERMANENT control.",
    "pt": "💀 O necromante toma o controle de **{alvo_nome}**! Testará Vontade (CD {dc}) a cada rodada; 3 falhas seguidas = controle PERMANENTE."
  },
  "narracao.o_pergaminho_falha_e_a_energia_se_dissip": {
    "en": "🌫️ The scroll **fails** and the energy dissipates. ({join_motivos})",
    "pt": "🌫️ O pergaminho **falha** e a energia se dissipa. ({join_motivos})"
  },
  "narracao.o_prisioneiro": {
    "en": "the prisoner",
    "pt": "o prisioneiro"
  },
  "narracao.o_prisioneiro_esquiva_de_um_monstro": {
    "en": "🛡️ The prisoner dodges a monster!",
    "pt": "🛡️ O prisioneiro esquiva de um monstro!"
  },
  "narracao.o_prisioneiro_foi_morto_o_resgate_falhou": {
    "en": "☠️ The prisoner was killed! The rescue failed.",
    "pt": "☠️ O prisioneiro foi morto! O resgate falhou."
  },
  "narracao.o_requiem_final_de_se_encerra": {
    "en": "🎻 **{bardo}**'s Final Requiem ends — {motivo}.",
    "pt": "🎻 O Réquiem Final de **{bardo}** se encerra — {motivo}."
  },
  "narracao.o_requiem_final_dilacera": {
    "en": "🎻 The Final Requiem tears into **{monstro}**: {n}{st_dado} = **{dano}**!",
    "pt": "🎻 O Réquiem Final dilacera **{monstro}**: {n}{st_dado} = **{dano}**!"
  },
  "narracao.o_requiem_improvisado_fere_em": {
    "en": "🎻 The Improvised Requiem wounds **{monstro}** for **{dano}**!",
    "pt": "🎻 O Réquiem improvisado fere **{monstro}** em **{dano}**!"
  },
  "narracao.o_sangramento_de_terminou": {
    "en": "🩸 {alvo}'s Bleeding has stopped.",
    "pt": "🩸 O Sangramento de {alvo} terminou."
  },
  "narracao.o_silencio_de_se_dissipa_com_sua_morte": {
    "en": "🔇 **{monstro}**'s Silence dissipates with its death.",
    "pt": "🔇 O Silêncio de **{monstro}** se dissipa com sua morte."
  },
  "narracao.o_teletransporte_de_falha_saida_bloquead": {
    "en": "✅ **{alvo_get_name_alvo}**'s teleport fails: exit blocked.",
    "pt": "✅ O teletransporte de **{alvo_get_name_alvo}** falha: saída bloqueada."
  },
  "narracao.o_terreno_criado_pelo_chamado_do_inverno": {
    "en": "❄️ The terrain created by Call of Winter returned to normal.",
    "pt": "❄️ O terreno criado pelo Chamado do Inverno voltou ao normal."
  },
  "narracao.o_terreno_criado_pelo_senhor_das_aguas_v": {
    "en": "🌊 The terrain created by Lord of Waters returned to normal.",
    "pt": "🌊 O terreno criado pelo Senhor das Águas voltou ao normal."
  },
  "narracao.o_veneno_da_arma_de_acabou": {
    "en": "🧴 **{heroi}**'s weapon poison ran out.",
    "pt": "🧴 O veneno da arma de **{heroi}** acabou."
  },
  "narracao.o_veneno_do_projetil_de_acabou": {
    "en": "🧴 **{heroi}**'s projectile poison ran out.",
    "pt": "🧴 O veneno do projétil de **{heroi}** acabou."
  },
  "narracao.obj_ganhos": {
    "en": " {lista} each.",
    "pt": " {lista} a cada herói."
  },
  "narracao.obj_itens": {
    "en": " 🎁 Reward dropped: {lista}.",
    "pt": " 🎁 Recompensa largada: {lista}."
  },
  "narracao.obj_ouro": {
    "en": "+{n} gold",
    "pt": "+{n} ouro"
  },
  "narracao.obj_xp": {
    "en": "+{n} XP",
    "pt": "+{n} XP"
  },
  "narracao.objetivo_cumprido": {
    "en": "⭐ Objective **{nome}** complete!{ganhos}{itens}",
    "pt": "⭐ Objetivo **{nome}** cumprido!{ganhos}{itens}"
  },
  "narracao.objetivo_principal_cumprido_recolham_a_r": {
    "en": "🏁 Main objective complete! Collect your reward and click **End Mission** when you're ready.",
    "pt": "🏁 Objetivo principal cumprido! Recolham a recompensa e cliquem em **Encerrar missão** quando estiverem prontos."
  },
  "narracao.obtem_um_19_20_natural_com_o_machado_dup": {
    "en": "🪓 **{heroi}** rolls a natural 19/20 with the Double Axe — a second attack is available this turn.",
    "pt": "🪓 **{heroi}** obtém um 19/20 natural com o Machado Duplo — um segundo ataque está disponível neste turno."
  },
  "narracao.os_aventureiros_descem_novamente_as_esca": {
    "en": "🚪 The adventurers descend the stairs once more — the dungeon remains exactly as they left it.",
    "pt": "🚪 Os aventureiros descem novamente as escadas — a masmorra permanece exatamente como a deixaram."
  },
  "narracao.os_aventureiros_partem_da_cidade_e_adent": {
    "en": "The adventurers leave town and enter the dungeon. Round 1 — **{nome}**'s initiative.",
    "pt": "Os aventureiros partem da cidade e adentram a masmorra. Rodada 1 — iniciativa de **{nome}**."
  },
  "narracao.os_ecos_dolorosos_ferem_em": {
    "en": "🔔 The Aching Echoes wound **{monstro}** for **{dano}**!",
    "pt": "🔔 Os Ecos Dolorosos ferem **{monstro}** em **{dano}**!"
  },
  "narracao.os_efeitos_magicos_em_se_dissipam": {
    "en": "✨ The magical effects on **{alvo_get_name_alvo}** dissipate.",
    "pt": "✨ Os efeitos mágicos em **{alvo_get_name_alvo}** se dissipam."
  },
  "narracao.parte_para_a_investida_brutal_2_de_dano": {
    "en": "🐗 **{monstro}** charges into a **Brutal Charge** (+2 damage)!",
    "pt": "🐗 **{monstro}** parte para a **Investida Brutal** (+2 de dano)!"
  },
  "narracao.passa_sobre_a_brasa_e_sofre_de_dano_de_f": {
    "en": "🔥 **{nome_criatura_criatura}** walks over the embers and takes **{dano}** fire damage!",
    "pt": "🔥 **{nome_criatura_criatura}** passa sobre a brasa e sofre **{dano}** de dano de fogo!"
  },
  "narracao.passa_sobre_a_chama_viva_e_sofre_de_dano": {
    "en": "🔥 **{nome_criatura_criatura}** walks through the living flame and takes **{dano}** fire damage!",
    "pt": "🔥 **{nome_criatura_criatura}** passa sobre a chama viva e sofre **{dano}** de dano de fogo!"
  },
  "narracao.passou_no_teste_de_reflexos_e_se_esquivou": {
    "en": "{prefix} **{heroi}** made the **Reflex** save (DC 13) and dodged!",
    "pt": "{prefix} **{heroi}** passou no teste de **Reflexos** (CD 13) e se esquivou!"
  },
  "narracao.pega_fogo_por_rodada_s": {
    "en": "🔥 **{target}** catches fire for {dur} round(s)!",
    "pt": "🔥 **{target}** pega fogo por {dur} rodada(s)!"
  },
  "narracao.pega_fogo_por_rodada_s_2": {
    "en": "🔥 **{nome}** catches fire for {dur} round(s)!",
    "pt": "🔥 **{nome}** pega fogo por {dur} rodada(s)!"
  },
  "narracao.pegou_do_bau": {
    "en": "📦 **{heroi}** picked up **{item_get_emoji} {item}** from the chest{extra}!",
    "pt": "📦 **{heroi}** pegou **{item_get_emoji} {item}** do baú{extra}!"
  },
  "narracao.pegou_do_bau_2": {
    "en": "📦 **{heroi}** took **{item_emoji} {item}** from the chest!",
    "pt": "📦 **{heroi}** pegou **{item_emoji} {item}** do baú!"
  },
  "narracao.pegou_do_chao": {
    "en": "🎒 **{heroi}** picked up **{gi_item_name}** from the ground{extra}!",
    "pt": "🎒 **{heroi}** pegou **{gi_item_name}** do chão{extra}!"
  },
  "narracao.pegou_do_objeto": {
    "en": "🎒 **{heroi}** picked up **{item}** from the object{extra}!",
    "pt": "🎒 **{heroi}** pegou **{item}** do objeto{extra}!"
  },
  "narracao.pegou_ouros_do_bau": {
    "en": "🪙 **{heroi}** picked up **{recebido}** gold from the chest!",
    "pt": "🪙 **{heroi}** pegou **{recebido}** ouros do baú!"
  },
  "narracao.pegou_ouros_do_objeto": {
    "en": "🪙 **{heroi}** picked up **{recebido}** gold from the object!",
    "pt": "🪙 **{heroi}** pegou **{recebido}** ouros do objeto!"
  },
  "narracao.perde_a_concentracao_sem_magia_neste_tur": {
    "en": "💥 **{monstro}** loses concentration — no spell this turn! (Will {tot} vs DC 10)",
    "pt": "💥 **{monstro}** perde a concentração — sem magia neste turno! (Vontade {tot} vs CD 10)"
  },
  "narracao.perde_a_proxima_acao_de_movimento": {
    "en": "loses its next movement action",
    "pt": "perde a próxima ação de movimento"
  },
  "narracao.perde_a_rodada_inteira": {
    "en": "⏸️ **{alvo_nome}** loses the entire round!",
    "pt": "⏸️ **{alvo_nome}** perde a rodada inteira!"
  },
  "narracao.perde_o_movimento": {
    "en": "🦵 **{alvo_nome}** loses their movement!",
    "pt": "🦵 **{alvo_nome}** perde o movimento!"
  },
  "narracao.perde_ponto_s_de_altura_com_o_impacto": {
    "en": "{nome_criatura_m} loses {perda_real} point(s) of altitude from the impact.",
    "pt": "{nome_criatura_m} perde {perda_real} ponto(s) de altura com o impacto."
  },
  "narracao.perdera_apenas_o_movimento_no_proximo_tu": {
    "en": "🦂 **{alvo_nome}** will only lose movement on the next turn.",
    "pt": "🦂 **{alvo_nome}** perderá apenas o movimento no próximo turno."
  },
  "narracao.perdeu_a_conexao_e_deixou_a_masmorra_o_g": {
    "en": "🔌 **{heroi}** lost connection and left the dungeon. The group presses on!",
    "pt": "🔌 **{heroi}** perdeu a conexão e deixou a masmorra. O grupo segue em frente!"
  },
  "narracao.petrificado_por_rodada_s": {
    "en": "🗿 **{nome}**: **{alvo_nome}** petrified for {pet_dur} round(s)!",
    "pt": "🗿 **{nome}**: **{alvo_nome}** petrificado por {pet_dur} rodada(s)!"
  },
  "narracao.piso_congelado_escorrega_e_perde_o_movim": {
    "en": "Frozen Floor: **{nome_criatura_criatura}** slips and loses the remaining movement of the turn!",
    "pt": "Piso congelado: **{nome_criatura_criatura}** escorrega e perde o movimento restante do turno!"
  },
  "narracao.pisou_na_fogueira_e_sofre_de_fogo": {
    "en": "🔥 **{nome}** stepped into the campfire and takes **{dano}** fire damage!",
    "pt": "🔥 **{nome}** pisou na fogueira e sofre **{dano}** de fogo!"
  },
  "narracao.prepara_a_mira_certeira_para_o_proximo_a": {
    "en": "🎯 {monstro} lines up **Sure Aim** for the next attack.",
    "pt": "{monstro} prepara a Mira Certeira para o próximo ataque."
  },
  "narracao.prepara_contramagica_teste_oposto_para_c": {
    "en": "🛑 **{caster}** readies **Counterspell** — an opposed check to cancel the next incoming spell (consumes the reaction when used).",
    "pt": "🛑 **{caster}** prepara **Contramágica** — teste oposto para cancelar a próxima magia recebida (consome a reação ao usar)."
  },
  "narracao.prepara_custo_e_recarga_apos_o_efeito": {
    "en": "⚔️ **{heroi}** readies **{item_nome}** — cost and cooldown apply after the effect.",
    "pt": "⚔️ **{heroi}** prepara **{item_nome}** — custo e recarga após o efeito."
  },
  "narracao.prepara_em": {
    "en": "🪤 **{heroi}** sets **{tipo_nome}** at ({tx},{ty}).",
    "pt": "🪤 **{heroi}** prepara **{tipo_nome}** em ({tx},{ty})."
  },
  "narracao.prepara_investida_brutal": {
    "en": "{monstro} readies a Brutal Charge!",
    "pt": "{monstro} prepara uma Investida Brutal!"
  },
  "narracao.prepara_mas_seus_efeitos_ainda_nao_foram": {
    "en": "📖 **{caster}** prepares **{magia_nome}** {magia_get_icone}, but its effects have not been implemented yet (in development).",
    "pt": "📖 **{caster}** prepara **{magia_nome}** {magia_get_icone}, mas seus efeitos ainda não foram conjurados (em desenvolvimento)."
  },
  "narracao.prisao_de_chamas_criada": {
    "en": "{caster} creates a {lado}x{lado} Prison of Flames for {dur} rounds. The edges deal 2d8 and the heat reaches the eight neighbouring squares.",
    "pt": "{caster} cria uma Prisão de Chamas {lado}x{lado} por {dur} rodadas. As bordas causam 2d8 e o calor alcança as oito casas vizinhas."
  },
  "narracao.projetil_incendiario_de_dano_de_fogo": {
    "en": "🔥 Incendiary projectile: +{xdmg} fire damage!",
    "pt": "🔥 Projétil incendiário: +{xdmg} de dano de fogo!"
  },
  "narracao.protecao_de_absorve_de_resta": {
    "en": "🛡️ **{alvo}**'s protection absorbs {absorvido} of {tipo} ({alvo_protecao_restante} remaining).",
    "pt": "🛡️ Proteção de **{alvo}** absorve {absorvido} de {tipo} (resta {alvo_protecao_restante})."
  },
  "narracao.protege_com_escudo_divino_imune_a_dano_p": {
    "en": "🛡️ **{heroi}** protects **{t}** with **Divine Shield**! Immune to damage for 1 turn.",
    "pt": "🛡️ **{heroi}** protege **{t}** com **Escudo Divino**! Imune a dano por 1 turno."
  },
  "narracao.protetor_absorve_recebe_recebe": {
    "en": "🛡️ **Protector** absorbs it! **{alvo}** takes {dano_aliado}, **{richard}** takes {dano_richard}.",
    "pt": "🛡️ **Protetor** absorve! **{alvo}** recebe {dano_aliado}, **{richard}** recebe {dano_richard}."
  },
  "narracao.protetor_de_se_desfaz_aliado_fora_do_rai": {
    "en": "🛡️ **{heroi}**'s Protector unravels — ally out of range.",
    "pt": "🛡️ Protetor de **{heroi}** se desfaz — aliado fora do raio."
  },
  "narracao.protetor_de_se_desfaz_aliado_saiu_do_rai": {
    "en": "🛡️ **{richard}**'s Protector unravels — ally left the range.",
    "pt": "🛡️ Protetor de **{richard}** se desfaz — aliado saiu do raio."
  },
  "narracao.protetor_de_se_interrompe_fome_insuficie": {
    "en": "🛡️ **{heroi}**'s Protector is interrupted — insufficient hunger.",
    "pt": "🛡️ Protetor de **{heroi}** se interrompe — fome insuficiente."
  },
  "narracao.provoca_desvantagem_no_proximo_ataque_e": {
    "en": "😤 **{heroi}** taunts **{alvo}**! Disadvantage on its next attack, and it is forced to target him for 3 turns (🍖-{fome_cost} 💧-{sede_cost}).",
    "pt": "😤 **{heroi}** provoca **{alvo}**! Desvantagem no próximo ataque e alvo forçado por 3 turnos (🍖-{fome_cost} 💧-{sede_cost})."
  },
  "narracao.provoca_ele_deve_enfrenta_lo_por_rodadas": {
    "en": "😤 {monstro} taunts {alvo}: it must face him for {int_ability_get_duration} rounds.",
    "pt": "{monstro} provoca {alvo}: ele deve enfrentá-lo por {int_ability_get_duration} rodadas."
  },
  "narracao.purifica_livre_de": {
    "en": "✨ **{heroi}** purifies **{alvo}** — free of {nomes_tipo}! (🍖-{custo_fome} 💧-{custo_sede})",
    "pt": "✨ **{heroi}** purifica **{alvo}** — livre de {nomes_tipo}! (🍖-{custo_fome} 💧-{custo_sede})"
  },
  "narracao.raio_divino_dobrado_contra_morto_vivo_de": {
    "en": "✨ Divine Ray DOUBLED against **{alvo}** (undead/demon)!",
    "pt": "✨ Raio Divino DOBRADO contra **{alvo}** (morto-vivo/demônio)!"
  },
  "narracao.reage_ao_ataque_de_ataque_furtivo_suprem": {
    "en": "🗡️ **{luccas}** reacts to **{atacante}**'s attack — Supreme Sneak Attack! +{dano} damage [{nd4}d4] on **{target}**.",
    "pt": "🗡️ **{luccas}** reage ao ataque de **{atacante}** — Ataque Furtivo Supremo! +{dano} de dano [{nd4}d4] em **{target}**."
  },
  "narracao.reage_e_atinge_de_dano_hp": {
    "en": "↩️ **{atacante}** reacts and strikes **{alvo}**: **{dmg}** damage{extra}. ({alvo_hp}/{alvo_max_hp} HP)",
    "pt": "↩️ **{atacante}** reage e atinge **{alvo}**: **{dmg}** de dano{extra}. ({alvo_hp}/{alvo_max_hp} HP)"
  },
  "narracao.reage_mas_erra": {
    "en": "↩️ **{atacante}** reacts but **misses** **{alvo}**.",
    "pt": "↩️ **{atacante}** reage mas **erra** **{alvo}**."
  },
  "narracao.reaparece_das_sombras": {
    "en": "👁️ **{monstro}** reappears from the shadows.",
    "pt": "👁️ **{monstro}** reaparece das sombras."
  },
  "narracao.recarregou_do_bau_no_slot": {
    "en": "🏹 **{heroi}** restocked **{item}** from the chest (+{add} → {off_ammo_count} in the slot)!",
    "pt": "🏹 **{heroi}** recarregou **{item}** do baú (+{add} → {off_ammo_count} no slot)!"
  },
  "narracao.recebe_visao_no_escuro_ate_o_fim_da_miss": {
    "en": "👁️ **{alvo}** gains Darkvision until the end of the mission.",
    "pt": "👁️ **{alvo}** recebe Visão no Escuro até o fim da missão."
  },
  "narracao.recebe_visao_no_escuro_enquanto_o_manto": {
    "en": "👁️ **{caster}** gains Darkvision while Cloak of Darkness lasts.",
    "pt": "👁️ **{caster}** recebe Visão no Escuro enquanto o Manto de Escuridão durar."
  },
  "narracao.recebe_voo_e_pode_controlar_sua_altura_d": {
    "en": "🪶 **{alvo}** gains **Flight** and can control its altitude from {alvo_get_altura_altura_i} to {alvo_get_altura_max_altu}.",
    "pt": "🪽 **{alvo}** recebe **Voo** e pode controlar sua altura de {alvo_get_altura_altura_i} até {alvo_get_altura_max_altu}."
  },
  "narracao.reconectou_se_a_aventura": {
    "en": "🔌 **{name}** reconnected to the adventure.",
    "pt": "🔌 **{name}** reconectou-se à aventura."
  },
  "narracao.reconectou_se_e_voltou_a_masmorra": {
    "en": "🔌 **{name}** reconnected and returned to the dungeon!",
    "pt": "🔌 **{name}** reconectou-se e voltou à masmorra!"
  },
  "narracao.recorre_ao_instinto_de_sobrevivencia_e_p": {
    "en": "{nome_criatura_m} falls back on Survival Instinct and stays at 1 HP.",
    "pt": "{nome_criatura_m} recorre ao Instinto de Sobrevivência e permanece com 1 PV."
  },
  "narracao.recorre_ao_instinto_de_sobrevivencia_e_r": {
    "en": "🍀 **{heroi}** falls back on **Survival Instinct** and holds on with 1 HP!",
    "pt": "🍀 **{heroi}** recorre ao **Instinto de Sobrevivência** e resiste com 1 HP!"
  },
  "narracao.recua_das_chamas": {
    "en": "🟢 **{monstro}** backs away from the flames!",
    "pt": "🟢 **{monstro}** recua das chamas!"
  },
  "narracao.recua_esta_ferido_e_ficou_isolado_do_gru": {
    "en": "{nome_criatura_m} retreats: it is wounded and got cut off from the group.",
    "pt": "{nome_criatura_m} recua: está ferido e ficou isolado do grupo."
  },
  "narracao.recua_para_as_sombras_apos_morder": {
    "en": "🐍 **{monstro}** retreats into the shadows after biting.",
    "pt": "🐍 **{monstro}** recua para as sombras após morder."
  },
  "narracao.recupera_a_coragem": {
    "en": "😱 **{monstro}** regains its courage.",
    "pt": "😱 **{monstro}** recupera a coragem."
  },
  "narracao.recupera_a_pontaria_penalidade_da_cervej": {
    "en": "🍺 **{heroi}** regains their aim (the beer penalty wore off).",
    "pt": "🍺 **{heroi}** recupera a pontaria (penalidade da cerveja acabou)."
  },
  "narracao.recupera_automaticamente_a_lanca_do_chao": {
    "en": "🔱 {nome_criatura_m} automatically picks the spear back up from the ground.",
    "pt": "🔱 {nome_criatura_m} recupera automaticamente a lança do chão."
  },
  "narracao.recupera_hp_com_a_regeneracao_runica_rod": {
    "en": "🔷 {monstro} recovers {cura} HP from **Runic Regeneration** ({max_0_restantes_1} rounds left).",
    "pt": "{monstro} recupera {cura} HP com a Regeneração Rúnica ({max_0_restantes_1} rodadas restantes)."
  },
  "narracao.recupera_o_movimento_normal": {
    "en": "🟢 **{monstro}** regains normal movement.",
    "pt": "🟢 **{monstro}** recupera o movimento normal."
  },
  "narracao.recuperou_a_coragem": {
    "en": "😤 **{monstro}** regained its courage!",
    "pt": "😤 **{monstro}** recuperou a coragem!"
  },
  "narracao.recusa_a_morte_ultimo_esforco_dois_turno": {
    "en": "🔥 **{heroi}** refuses to die — **LAST STAND**! Two turns of fury before falling.",
    "pt": "🔥 **{heroi}** recusa a morte — **ÚLTIMO ESFORÇO**! Dois turnos de fúria antes de cair."
  },
  "narracao.recusa_se_a_tombar_fortitude_vs_cd_fica": {
    "en": "🧟 **{monstro}** refuses to fall! (Fortitude {tot} vs DC {cd}) — left at **1 HP**.",
    "pt": "🧟 **{monstro}** recusa-se a tombar! (Fortitude {tot} vs CD {cd}) — fica com **1 HP**."
  },
  "narracao.reforcos_um_a_entra_na_masmorra": {
    "en": "⚠️ **Reinforcements!** A **{mdef_get_name_monster_ty}** enters the dungeon!",
    "pt": "⚠️ **Reforços!** Um(a) **{mdef_get_name_monster_ty}** entra na masmorra!"
  },
  "narracao.regenera_reserva_1_hp_rodada_revive_uma": {
    "en": "🌿 **{caster}** regenerates **{alvo}** — pool {pool} (+1 HP/round; revives once with 1 HP).",
    "pt": "🌿 **{caster}** regenera **{alvo}** — reserva {pool} (+1 HP/rodada; revive uma vez com 1 HP)."
  },
  "narracao.regeneracao_cura_reserva": {
    "en": "🌿 Regeneration heals **{alvo}** +{cura} ({alvo_hp}/{alvo_max_hp}; pool {alvo_regen_pool}).",
    "pt": "🌿 Regeneração cura **{alvo}** +{cura} ({alvo_hp}/{alvo_max_hp}; reserva {alvo_regen_pool})."
  },
  "narracao.regeneracao_divina_1_hp_1_1": {
    "en": "✨ **{heroi}** — Divine Regeneration: +1 HP ({p_hp}/{p_max_hp}) 🍖-1 💧-1.",
    "pt": "✨ **{heroi}** — Regeneração Divina: +1 HP ({p_hp}/{p_max_hp}) 🍖-1 💧-1."
  },
  "narracao.regeneracao_divina_de_se_encerra_hp_maxi": {
    "en": "✨ **{heroi}**'s Divine Regeneration ends — max HP reached.",
    "pt": "✨ Regeneração Divina de **{heroi}** se encerra — HP máximo atingido."
  },
  "narracao.regeneracao_divina_de_se_interrompe_recu": {
    "en": "✨ **{heroi}**'s Divine Regeneration is interrupted — insufficient resources.",
    "pt": "✨ Regeneração Divina de **{heroi}** se interrompe — recursos insuficientes."
  },
  "narracao.regeneracao_divina_de_tambem_cura_1_hp": {
    "en": "✨ **{heroi}**'s Divine Regeneration also heals: {join_curados} (+1 HP).",
    "pt": "✨ Regeneração Divina de **{heroi}** também cura: {join_curados} (+1 HP)."
  },
  "narracao.relampago_feriu_caster": {
    "en": " | ⚠️ struck Pedro himself on the way back!",
    "pt": " | ⚠️ atingiu o próprio Pedro na volta!"
  },
  "narracao.relampago_multi": {
    "en": " | {n} target(s) hit twice",
    "pt": " | {n} alvo(s) atingido(s) 2x"
  },
  "narracao.reparou_completamente_por_moedas": {
    "en": "🔧 **{heroi}** fully repaired **{nome}** for **{custo}** gold.",
    "pt": "🔧 **{heroi}** reparou **{nome}** completamente por **{custo}** moedas."
  },
  "narracao.requiem_final_de_manutencao": {
    "en": "🎻 **{heroi}**'s Final Requiem — upkeep 🍖-{mf} 💧-{ms}.",
    "pt": "🎻 Réquiem Final de **{heroi}** — manutenção 🍖-{mf} 💧-{ms}."
  },
  "narracao.resiste": {
    "en": "resists",
    "pt": "resiste"
  },
  "narracao.resiste_a_amaldicoar_de": {
    "en": "☠️ **{alvo}** resists **{monstro}**'s Curse (d20({d20}){bonus}={total} vs DC {dc}).",
    "pt": "☠️ **{alvo}** resiste a Amaldiçoar de **{monstro}** (d20({d20}){bonus}={total} vs CD {dc})."
  },
  "narracao.resiste_a_dominar_mente": {
    "en": "🧠 **{alvo}** resists Dominate Mind.",
    "pt": "🧠 **{alvo}** resiste a Dominar Mente."
  },
  "narracao.resiste_a_engolir_de_fortitude_vs_cd": {
    "en": "🦖 **{preso_get_name_or_preso}** resists **{monstro}**'s Swallow (Fortitude {total} vs DC {dc}).",
    "pt": "🦖 **{preso_get_name_or_preso}** resiste a Engolir de **{monstro}** (Fortitude {total} vs CD {dc})."
  },
  "narracao.resiste_a_infeccao_fortitude_vs_cd": {
    "en": "🦠 **{target}** resists the infection (Fortitude {tot} vs DC {dc}).",
    "pt": "🦠 **{target}** resiste à infecção (Fortitude {tot} vs CD {dc})."
  },
  "narracao.resiste_a_infeccao_fortitude_vs_cd_2": {
    "en": "🦠 **{target}** resists the infection (Fortitude {total_save} vs DC {dc}).",
    "pt": "🦠 **{target}** resiste à infecção (Fortitude {total_save} vs CD {dc})."
  },
  "narracao.resiste_a_permanencia_3": {
    "en": "🛡️ **{nome_criatura_alvo}** resists the permanence ({n}/3).",
    "pt": "🛡️ **{nome_criatura_alvo}** resiste à permanência ({n}/3)."
  },
  "narracao.resiste_a_petrificacao_imunizado": {
    "en": "🛡️ **{alvo_nome}** resists petrification (immune)!",
    "pt": "🛡️ **{alvo_nome}** resiste à petrificação (imunizado)!"
  },
  "narracao.resiste_a_petrificacao_imunizado_2": {
    "en": "🛡️ **{tgt_name}** resists petrification (immune)!",
    "pt": "🛡️ **{tgt_name}** resiste à petrificação (imunizado)!"
  },
  "narracao.resiste_ao_comando": {
    "en": "🗣️ **{alvo}** resists Command.",
    "pt": "🗣️ **{alvo}** resiste ao Comando."
  },
  "narracao.resiste_ao_dominio_vontade_vs_cd_nd": {
    "en": "💀 **{alvo}** resists the control (Will vs DC {dif}, CR +{nd}).",
    "pt": "💀 **{alvo}** resiste ao domínio (Vontade vs CD {dif}, ND +{nd})."
  },
  "narracao.resiste_ao_lamento_improvisado": {
    "en": "🎻 **{monstro}** resists the improvised lament.",
    "pt": "🎻 **{monstro}** resiste ao lamento improvisado."
  },
  "narracao.resiste_ao_olhar_petrificante_contra_cd": {
    "en": "👁️ **{nome_criatura_alvo}** resists the Petrifying Gaze ({total} vs DC {dc}) — resistance {alvo_resistencia_petrifi}/3.",
    "pt": "👁️ **{nome_criatura_alvo}** resiste ao Olhar Petrificante ({total} contra CD {dc}) — resistência {alvo_resistencia_petrifi}/3."
  },
  "narracao.resiste_ao_requiem_nesta_rodada": {
    "en": "🎻 **{monstro}** resists the Requiem this round.",
    "pt": "🎻 **{monstro}** resiste ao Réquiem nesta rodada."
  },
  "narracao.resiste_mas_hesita": {
    "en": "📯 **{monstro}** resists, but hesitates.",
    "pt": "📯 **{monstro}** resiste, mas hesita."
  },
  "narracao.resiste_vontade_vs_cd_nd": {
    "en": "💀 **{alvo_nome}** resists (Will vs DC {dc}, CR +{nd}).",
    "pt": "💀 **{alvo_nome}** resiste (Vontade vs CD {dc}, ND +{nd})."
  },
  "narracao.resistiu_a_metamorfose": {
    "en": "🛡️ **{nome_criatura_alvo}** resisted Polymorph.",
    "pt": "🛡️ **{nome_criatura_alvo}** resistiu à Metamorfose."
  },
  "narracao.resistiu_a_paralisacao": {
    "en": "❄️ **{alvo}** resisted paralysis.",
    "pt": "❄️ **{alvo}** resistiu à paralisação."
  },
  "narracao.resistiu_ao": {
    "en": "☑️ **{alvo_nome}** resisted **{nome}**!",
    "pt": "☑️ **{alvo_nome}** resistiu ao **{nome}**!"
  },
  "narracao.resistiu_ao_derrube_d20": {
    "en": "🐾 **{target}** resisted the knockdown (d20={d20}{sb_str}={stot}).",
    "pt": "🐾 **{target}** resistiu ao derrube (d20={d20}{sb_str}={stot})."
  },
  "narracao.resistiu_ao_medo_d20": {
    "en": "💪 **{monstro}** resisted the fear! (d20={d20}{sb_str}={stot})",
    "pt": "💪 **{monstro}** resistiu ao medo! (d20={d20}{sb_str}={stot})"
  },
  "narracao.resistiu_ao_teleporte": {
    "en": "{alvo} resisted Teleport.",
    "pt": "{alvo} resistiu ao Teleporte."
  },
  "narracao.resistiu_ao_teleporte_com_rolagem": {
    "en": "{alvo} resisted Teleport ({total} against DC {dc}).",
    "pt": "{alvo} resistiu ao Teleporte ({total} contra CD {dc})."
  },
  "narracao.resistiu_ao_teletransporte": {
    "en": "✅ **{alvo_get_name_alvo}** resisted the teleport!",
    "pt": "✅ **{alvo_get_name_alvo}** resistiu ao teletransporte!"
  },
  "narracao.resistiu_ja_carrega_o_maximo_de_3_maldic": {
    "en": "☠️ **{alvo}** resisted: already carries the maximum of 3 curses.",
    "pt": "☠️ **{alvo}** resistiu: já carrega o máximo de 3 maldições."
  },
  "narracao.ressurreicao_traz_de_volta_a_vida_com_hp": {
    "en": "💫 **RESURRECTION!** **{heroi}** brings **{alvo}** back to life with **{alvo_hp} HP**! (🍖-{custo_fome} 💧-{custo_sede})",
    "pt": "💫 **RESSURREIÇÃO!** **{heroi}** traz **{alvo}** de volta à vida com **{alvo_hp} HP**! (🍖-{custo_fome} 💧-{custo_sede})"
  },
  "narracao.retorna_a_forma_normal": {
    "en": "🌙 **{heroi}** returns to their normal form.",
    "pt": "🌙 **{heroi}** retorna à forma normal."
  },
  "narracao.retorna_a_forma_original": {
    "en": "🦋 **{nome_criatura_alvo}** returns to its original form ({motivo}).",
    "pt": "🦋 **{nome_criatura_alvo}** retorna à forma original ({motivo})."
  },
  "narracao.revela_se": {
    "en": "🌑 **{heroi}** reveals themself ({motivo}).",
    "pt": "🌑 **{heroi}** revela-se ({motivo})."
  },
  "narracao.revela_se_ao_lancar_magia": {
    "en": "🫥 **{heroi}** reveals themself by casting a spell.",
    "pt": "🫥 **{heroi}** revela-se ao lançar magia."
  },
  "narracao.rodamoinho_descricao": {
    "en": "The character failed Reflex and is trapped in the whirlpool.",
    "pt": "O personagem falhou em Reflexos e ficou preso no redemoinho."
  },
  "narracao.rodamoinho_nome": {
    "en": "Whirlpool",
    "pt": "Redemoinho"
  },
  "narracao.rodamoinho_profundo_descricao": {
    "en": "The character failed Reflex and is trapped in the deep whirlpool.",
    "pt": "O personagem falhou em Reflexos e ficou preso no redemoinho profundo."
  },
  "narracao.rodamoinho_profundo_nome": {
    "en": "Deep Whirlpool",
    "pt": "Redemoinho profundo"
  },
  "narracao.rompe_o_controle_do_necromante_e_volta_a": {
    "en": "💀 **{a_nome}** breaks the necromancer's control and obeys **{dono_nome}** again!",
    "pt": "💀 **{a_nome}** rompe o controle do necromante e volta a obedecer **{dono_nome}**!"
  },
  "narracao.rompe_o_dominio_e_volta_a_ser_hostil": {
    "en": "💀 **{nome}** breaks free of the control and turns HOSTILE again!",
    "pt": "💀 **{nome}** rompe o domínio e volta a ser HOSTIL!"
  },
  "narracao.rompeu_dominar_mente_apos_o_dano_recebid": {
    "en": "🧠 **{monstro}** broke free of Dominate Mind after taking damage.",
    "pt": "🧠 **{monstro}** rompeu Dominar Mente após o dano recebido."
  },
  "narracao.sacia_fome_sede": {
    "en": "💧 **{caster}** sates **{alvo}** (+{fb} hunger, +{sb} thirst).",
    "pt": "💧 **{caster}** sacia **{alvo}** (+{fb} fome, +{sb} sede)."
  },
  "narracao.sacudida_jurassica": {
    "en": "🦖 **{monstro}** shakes **{alvo}** violently in its jaws and hurls them away! (Jurassic Shake)",
    "pt": "🦖 **{monstro}** sacode **{alvo}** violentamente nas mandíbulas e o arremessa! (Sacudida Jurássica)"
  },
  "narracao.sacudida_jurassica_colisao": {
    "en": "💥 **{alvo}** slams into an obstacle and takes {dano} more damage!",
    "pt": "💥 **{alvo}** se choca contra um obstáculo e sofre {dano} de dano a mais!"
  },
  "narracao.sai_das_sombras": {
    "en": "🌑 **{heroi}** steps out of the shadows.",
    "pt": "🌑 **{heroi}** sai das sombras."
  },
  "narracao.sai_das_sombras_sem_folego_para_se_mante": {
    "en": "🌑 **{heroi}** steps out of the shadows — out of breath to stay hidden.",
    "pt": "🌑 **{heroi}** sai das sombras — sem fôlego para se manter oculto."
  },
  "narracao.sangramento_profano_abre_as_feridas_de_1": {
    "en": "🩸 **Unholy Bleeding** tears **{heroi}**'s wounds open — **1** damage.",
    "pt": "🩸 **Sangramento Profano** abre as feridas de **{heroi}** — **1** de dano."
  },
  "narracao.save_d20_vs_dif": {
    "en": "🎲 **{alvo_nome}** — {veneno_get_save_fortitud} save: d20({d20}){sb_str}={stot} vs DC {veneno_get_dificuldade_1}{pen_str} → {resistiu_if_save_ok_else}.",
    "pt": "🎲 **{alvo_nome}** — save {veneno_get_save_fortitud}: d20({d20}){sb_str}={stot} vs dif {veneno_get_dificuldade_1}{pen_str} → {resistiu_if_save_ok_else}."
  },
  "narracao.save_d20_vs_dif_2": {
    "en": "🎲 {tipo_save} save: d20({d20}){sb_str}={stot} vs DC {tipo_dificuldade} → {evitou_if_save_ok_else_f}.",
    "pt": "🎲 Save {tipo_save}: d20({d20}){sb_str}={stot} vs dif {tipo_dificuldade} → {evitou_if_save_ok_else_f}."
  },
  "narracao.save_parcial_1_movimento_por_rodada_s": {
    "en": "⚠️ **{nome}**: partial save — **{alvo_nome}** -1 movement for {dur_falha} round(s).",
    "pt": "⚠️ **{nome}**: save parcial — **{alvo_nome}** -1 movimento por {dur_falha} rodada(s)."
  },
  "narracao.save_parcial_percepcao_de_reduzida_por_r": {
    "en": "⚠️ **{nome}**: partial save — **{alvo_nome}**'s perception reduced for {dur_falha} round(s).",
    "pt": "⚠️ **{nome}**: save parcial — percepção de **{alvo_nome}** reduzida por {dur_falha} rodada(s)."
  },
  "narracao.se_desfaz_em_po_para_abrir_caminho_ao_no": {
    "en": "💀 **{a_nome}** crumbles to dust to make way for the new control.",
    "pt": "💀 **{a_nome}** se desfaz em pó para abrir caminho ao novo domínio."
  },
  "narracao.se_dissipa_sem_alvo": {
    "en": "🌫️ **{magia_nome}** dissipates without a target.",
    "pt": "🌫️ **{magia_nome}** se dissipa sem alvo."
  },
  "narracao.se_esquiva_da_cola_sem_efeito": {
    "en": "🟢 **{nome}** dodges the glue — no effect!",
    "pt": "🟢 **{nome}** se esquiva da cola — sem efeito!"
  },
  "narracao.se_joga_no_chao_e_apaga_as_chamas": {
    "en": "🔥 **{heroi}** drops to the ground and puts out the flames!",
    "pt": "🔥 **{heroi}** se joga no chão e apaga as chamas!"
  },
  "narracao.se_liberta_do_dominio": {
    "en": "🧠 **{monstro}** breaks free of the control.",
    "pt": "🧠 **{monstro}** se liberta do domínio."
  },
  "narracao.se_libertou_da_paralisacao": {
    "en": "✅ **{alvo}** broke free of paralysis!",
    "pt": "✅ **{alvo}** se libertou da paralisação!"
  },
  "narracao.se_livra_de": {
    "en": "✨ **{heroi}** gets rid of {nome}.",
    "pt": "✨ **{heroi}** se livra de {nome}."
  },
  "narracao.se_livra_do_congelamento_progressivo": {
    "en": "🧊 **{heroi}** gets rid of the progressive freezing.",
    "pt": "🧊 **{heroi}** se livra do congelamento progressivo."
  },
  "narracao.se_recupera_da_embriaguez_penalidade_do": {
    "en": "🍷 **{heroi}** recovers from the drunkenness (the wine penalty wore off).",
    "pt": "🍷 **{heroi}** se recupera da embriaguez (penalidade do vinho acabou)."
  },
  "narracao.se_solta_da_rede": {
    "en": "🕸️ **{monstro}** breaks free of the net!",
    "pt": "🕸️ **{monstro}** se solta da rede!"
  },
  "narracao.se_soltou_do_agarrao_de_vs_cd": {
    "en": "💪 **{heroi}** broke free of **{captor}**'s grapple! ({detalhe} vs DC {dc})",
    "pt": "💪 **{heroi}** se soltou do agarrão de **{captor}**! ({detalhe} vs CD {dc})"
  },
  "narracao.se_soltou_o_predador_foi_abatido": {
    "en": "🔓 **{c}** broke free — the predator was slain!",
    "pt": "🔓 **{c}** se soltou — o predador foi abatido!"
  },
  "narracao.se_transforma_em_lobisomem_por_rodadas": {
    "en": "🐺 **{heroi}** transforms into a **Werewolf** for {duracao} rounds — {motivo}!",
    "pt": "🐺 **{heroi}** se transforma em **Lobisomem** por {duracao} rodadas — {motivo}!"
  },
  "narracao.se_volta_contra": {
    "en": "☠️ **{magia_nome}** turns against **{heroi}**!",
    "pt": "☠️ **{magia_nome}** se volta contra **{heroi}**!"
  },
  "narracao.sem_descanso_o_grupo_avanca_direto_para": {
    "en": "⛓️ No rest: the group presses straight on to stage {indice_1}/{len_stages} of **{adventure_get_nome_avent}**.",
    "pt": "⛓️ Sem descanso: o grupo avança direto para a etapa {indice_1}/{len_stages} de **{adventure_get_nome_avent}**."
  },
  "narracao.sem_herois_na_masmorra_a_expedicao_e_int": {
    "en": "🏙️ With no heroes left in the dungeon, the expedition is interrupted — the group regroups in town.",
    "pt": "🏙️ Sem heróis na masmorra, a expedição é interrompida — o grupo se reúne na cidade."
  },
  "narracao.sem_o_necromante_volta_a_obedecer": {
    "en": "💀 Without the necromancer, **{a_nome}** obeys **{dono_nome}** again.",
    "pt": "💀 Sem o necromante, **{a_nome}** volta a obedecer **{dono_nome}**."
  },
  "narracao.sem_seu_mestre_os_servos_mortos_vivos_de": {
    "en": "💨 Without their master, the undead minions crumble to dust!",
    "pt": "💨 Sem seu mestre, os servos mortos-vivos desfazem-se em pó!"
  },
  "narracao.seria_derrotado_mas_a_regeneracao_o_reer": {
    "en": "🌿 **{heroi}** would have been defeated, but **Regeneration** brings them back up with 1 HP! (-3 hunger/thirst)",
    "pt": "🌿 **{heroi}** seria derrotado, mas a **Regeneração** o reergue com 1 HP! (-3 fome/sede)"
  },
  "narracao.servo_perde_a_vez": {
    "en": "💀 {servo} loses its turn — {motivo}.",
    "pt": "💀 {servo} perde a vez — {motivo}."
  },
  "narracao.servo_salto_dormindo": {
    "en": "is asleep",
    "pt": "está dormindo"
  },
  "narracao.servo_salto_morto": {
    "en": "is destroyed",
    "pt": "está destruído"
  },
  "narracao.servo_salto_preso": {
    "en": "is caught in the whirlpool",
    "pt": "está preso pelo rodamoinho"
  },
  "narracao.so_pode_combinar_habilidade_s_por_turno": {
    "en": "**{heroi}** can only combine {teto} ability(ies) per turn — the rest were ignored.",
    "pt": "**{heroi}** só pode combinar {teto} habilidade(s) por turno — as demais foram ignoradas."
  },
  "narracao.so_pode_empilhar_metamagia_s_por_lancame": {
    "en": "🧵 **{heroi}** can only stack {self_teto_metamagia_p} metamagic(s) per cast — the rest were ignored.",
    "pt": "🧵 **{heroi}** só pode empilhar {self_teto_metamagia_p} metamagia(s) por lançamento — as demais foram ignoradas."
  },
  "narracao.sobe_as_escadas_rumo_a_cidade_e_volta_em": {
    "en": "🚪 **{heroi}** climbs the stairs toward the city (🍖-{fome} 💧-{sede}) and returns in {espera} round(s).",
    "pt": "🚪 **{heroi}** sobe as escadas rumo à cidade (🍖-{fome} 💧-{sede}) e volta em {espera} rodada(s)."
  },
  "narracao.sofre": {
    "en": "🎵 **{monstro}** takes **{dano}**{metade_if_save_ok_else}.",
    "pt": "🎵 **{monstro}** sofre **{dano}**{metade_if_save_ok_else}."
  },
  "narracao.sofre_2": {
    "en": "🔥 {rotulo}: **{nome}** takes {d}{extra}.",
    "pt": "🔥 {rotulo}: **{nome}** sofre {d}{extra}."
  },
  "narracao.sofre_3": {
    "en": "🥁 **{monstro}** takes **{dano}**{metade_if_save_ok_else}.",
    "pt": "🥁 **{monstro}** sofre **{dano}**{metade_if_save_ok_else}."
  },
  "narracao.sofre_ao_iniciar_o_turno_dentro_da_nuvem": {
    "en": "🧪 **{nome}** takes **{dano}** for starting the turn inside the Acid Cloud.",
    "pt": "🧪 **{nome}** sofre **{dano}** ao iniciar o turno dentro da Nuvem Ácida."
  },
  "narracao.sofre_congelamento_progressivo_movimento": {
    "en": "❄️ **{alvo}** suffers **Creeping Frost**: –{pilhas} movement for the next 2 turns.",
    "pt": "❄️ **{alvo}** sofre **Congelamento Progressivo**: –{pilhas} movimento pelos próximos 2 turnos."
  },
  "narracao.sofre_da_aura_escaldante_de": {
    "en": "🔥 **{alvo_get_name_or_alvo_ge}** takes **{dano}** from **{monstro}**'s Scalding Aura.",
    "pt": "🔥 **{alvo_get_name_or_alvo_ge}** sofre **{dano}** da Aura Escaldante de **{monstro}**."
  },
  "narracao.sofre_da_carapaca_espinhosa_de": {
    "en": "🦂 **{atacante_get_name_atacan}** takes **{dano}** from **{criatura_get_name_criatu}**'s Spiked Carapace.",
    "pt": "🦂 **{atacante_get_name_atacan}** sofre **{dano}** da Carapaça Espinhosa de **{criatura_get_name_criatu}**."
  },
  "narracao.sofre_da_nuvem_acida_de": {
    "en": "🧪 **{nome}** takes **{dano}** from **{monstro}**'s Acid Cloud.",
    "pt": "🧪 **{nome}** sofre **{dano}** da Nuvem Ácida de **{monstro}**."
  },
  "narracao.sofre_das_chamas_persistentes": {
    "en": "🔥 **{alvo_get_name_or_alvo_ge}** takes **{dano}** from the lingering flames.",
    "pt": "🔥 **{alvo_get_name_or_alvo_ge}** sofre **{dano}** das chamas persistentes."
  },
  "narracao.sofre_de": {
    "en": "{defn_emoji} **{nome}** takes {d} {defn_elemento} damage.",
    "pt": "{defn_emoji} **{nome}** sofre {d} de {defn_elemento}."
  },
  "narracao.sofre_de_afogar": {
    "en": "🌊 **{heroi}** takes **{dano}** damage from Drowning ({dano_base}{detalhe}).",
    "pt": "🌊 **{heroi}** sofre **{dano}** de Afogar ({dano_base}{detalhe})."
  },
  "narracao.sofre_de_d20_vs_cd": {
    "en": "🐉 **{target_name}** takes **{damage}** {labels_get_element_eleme} ({ability_get_save_reflexo} d20({d20}){bonus_text}={total} vs DC {ability_get_dc_13}){resistiu_if_passed_else}",
    "pt": "🐉 **{target_name}** sofre **{damage}** de {labels_get_element_eleme} ({ability_get_save_reflexo} d20({d20}){bonus_text}={total} vs CD {ability_get_dc_13}){resistiu_if_passed_else}"
  },
  "narracao.sofre_de_dano": {
    "en": "💥 **{alvo_nome}** takes **{dano}** damage ({elemento}).",
    "pt": "💥 **{alvo_nome}** sofre **{dano}** de dano ({elemento})."
  },
  "narracao.sofre_de_dano_2": {
    "en": "{defn_get_emoji} **{target_get_name_target_g}** takes **{dmg}** damage.",
    "pt": "{defn_get_emoji} **{target_get_name_target_g}** sofre **{dmg}** de dano."
  },
  "narracao.sofre_de_dano_3": {
    "en": "{defn_get_emoji} **{alvo_get_name_alvo_get_n}** takes **{dmg}** damage.",
    "pt": "{defn_get_emoji} **{alvo_get_name_alvo_get_n}** sofre **{dmg}** de dano."
  },
  "narracao.sofre_de_dano_adicional_do_veneno": {
    "en": "☠️ **{alvo_nome}** takes **{dano}** extra poison damage.",
    "pt": "☠️ **{alvo_nome}** sofre **{dano}** de dano adicional do veneno."
  },
  "narracao.sofre_de_dano_de_afogamento": {
    "en": "🌊 **{nome_criatura_criatura}** takes **{bruto}** drowning damage.",
    "pt": "🌊 **{nome_criatura_criatura}** sofre **{bruto}** de dano de afogamento."
  },
  "narracao.sofre_de_dano_hp": {
    "en": "💥 **{alvo_nome}** takes **{dano}** damage ({elemento}) ({alvo_hp}/{alvo_get_max_hp} HP).",
    "pt": "💥 **{alvo_nome}** sofre **{dano}** de dano ({elemento}) ({alvo_hp}/{alvo_get_max_hp} HP)."
  },
  "narracao.sofre_de_dano_sonoro": {
    "en": "🎵 **{monstro}** takes **{dano}** sonic damage{metade_resistiu_if_save}.",
    "pt": "🎵 **{monstro}** sofre **{dano}** de dano sonoro{metade_resistiu_if_save}."
  },
  "narracao.sofre_de_exaustao_1_hp": {
    "en": "☠️ **{heroi}** suffers from exhaustion ({e_join_motivos}) — **-1 HP** ({p_hp}/{p_max_hp}).",
    "pt": "☠️ **{heroi}** sofre de exaustão ({e_join_motivos}) — **-1 HP** ({p_hp}/{p_max_hp})."
  },
  "narracao.sofre_de_veneno_da_medusa_e_recebe_2_for": {
    "en": "☠️ **{nome_criatura_alvo}** takes {dano_extra} Medusa venom damage and gets -2 STR/-2 CON for {duracao} rounds (failed Fortitude).",
    "pt": "☠️ **{nome_criatura_alvo}** sofre {dano_extra} de veneno da Medusa e recebe -2 FOR/-2 CON por {duracao} rodadas (falha na Fortitude)."
  },
  "narracao.sofre_de_veneno_da_medusa_sucesso_na_for": {
    "en": "☠️ **{nome_criatura_alvo}** takes {dano_extra} Medusa venom damage (successful Fortitude).",
    "pt": "☠️ **{nome_criatura_alvo}** sofre {dano_extra} de veneno da Medusa (sucesso na Fortitude)."
  },
  "narracao.sofre_do_sangue_em_ebulicao_de": {
    "en": "🌋 **{atacante_get_name_or_ata}** takes **{dano}** from **{molochus}**'s Boiling Blood.",
    "pt": "🌋 **{atacante_get_name_or_ata}** sofre **{dano}** do Sangue em Ebulição de **{molochus}**."
  },
  "narracao.sofre_do_turbilhao_e_perdera": {
    "en": "🌪️ **{alvo}** takes {dano} from the Whirlwind and will lose its movement.",
    "pt": "🌪️ **{alvo}** sofre {dano} do Turbilhão e perderá o movimento."
  },
  "narracao.sofre_do_turbilhao_e_perdera_acao": {
    "en": "🌪️ **{alvo}** takes {dano} from the Whirlwind and will lose its next action.",
    "pt": "🌪️ **{alvo}** sofre {dano} do Turbilhão e perderá a próxima ação."
  },
  "narracao.sofre_empurrado_q": {
    "en": "🌪️ **{nome}** takes {dano} (pushed {push} square(s)).",
    "pt": "🌪️ **{nome}** sofre {dano} (empurrado {push}q)."
  },
  "narracao.sofre_pv_de_dano_recorrente": {
    "en": "🩸 {alvo} takes {dano} HP of recurring damage ({dano_sangramento} Bleeding{ferida}{hemorragia}).",
    "pt": "🩸 {alvo} sofre {dano} PV de dano recorrente ({dano_sangramento} Sangramento{ferida}{hemorragia})."
  },
  "narracao.sofreu_dano_e_perde_a_concentracao_sem_m": {
    "en": "🤕 **{monstro}** took damage and loses concentration — no spell this turn!",
    "pt": "🤕 **{monstro}** sofreu dano e perde a concentração — sem magia neste turno!"
  },
  "narracao.solo_sagrado_fere_em_de_dano_sagrado": {
    "en": "✝️ Holy ground wounds **{monstro}** for {dano} holy damage.",
    "pt": "✝️ Solo sagrado fere **{monstro}** em {dano} de dano sagrado."
  },
  "narracao.solta_das_garras": {
    "en": "{nome_criatura_m} releases {nome_criatura_presa} from its claws.",
    "pt": "{nome_criatura_m} solta {nome_criatura_presa} das garras."
  },
  "narracao.sopra_o_chamado_do_general_cone": {
    "en": "📯 **{heroi}** blows the **General's Call** (cone {comp})!",
    "pt": "📯 **{heroi}** sopra o **Chamado do General** (cone {comp})!"
  },
  "narracao.subiu_para_o_nivel_pv_e_1_em_ataque_ganh": {
    "en": "⭐ **{heroi}** leveled up to **{p_level}**! +{ganho_hp} HP and +1 Attack. Resistance and survival gains applied according to class.",
    "pt": "⭐ **{heroi}** subiu para o nível **{p_level}**! +{ganho_hp} PV e +1 em Ataque. Ganhos de resistência e sobrevivência aplicados conforme a classe."
  },
  "narracao.tatica_defensiva_assume_do_dano_de_que_s": {
    "en": "🤝 **Defensive Tactics**: **{tatico}** takes {dano_tatico} of **{alvo_nome}**'s damage (who takes {dano_aliado}).",
    "pt": "🤝 **Tática Defensiva**: **{tatico}** assume {dano_tatico} do dano de **{alvo_nome}** (que sofre {dano_aliado})."
  },
  "narracao.tempestade_ciclones_criada": {
    "en": "{caster} raises a {lado}x{lado} Cyclone Storm: {ciclones} cyclone(s), for {dur} rounds.",
    "pt": "{caster} cria uma Tempestade de Ciclones {lado}x{lado}: {ciclones} ciclone(s), por {dur} rodadas."
  },
  "narracao.tempestade_ciclones_dissipa": {
    "en": "The Cyclone Storm dies down.",
    "pt": "A Tempestade de Ciclones se dissipa."
  },
  "narracao.tempo_esgotado_o_turno_foi_encerrado": {
    "en": "⏳ Time's up! **{heroi}**'s turn ended automatically.",
    "pt": "⏳ Tempo esgotado! O turno de **{heroi}** foi encerrado automaticamente."
  },
  "narracao.tenta_a_sorte_de_novo_mas_erra_outra_vez": {
    "en": "🎲 **{heroi}** tries Luck again, but misses once more!",
    "pt": "🎲 **{heroi}** tenta a Sorte de novo, mas erra outra vez!"
  },
  "narracao.tenta_atacar_mas_a_fumaca_confunde": {
    "en": "💨 **{monstro}** tries to attack **{tgt_name}** but the smoke confuses it!",
    "pt": "💨 **{monstro}** tenta atacar **{tgt_name}** mas a fumaça confunde!"
  },
  "narracao.tenta_ataque_furtivo_mas_errou_d20_vs_ca": {
    "en": "🗡️ **{heroi}** attempts **Sneak Attack** but **MISSED** (d20={roll}={total} vs AC {t_ac})!",
    "pt": "🗡️ **{heroi}** tenta **Ataque Furtivo** mas **ERROU** (d20={roll}={total} vs CA {t_ac})!"
  },
  "narracao.tenta_ataque_furtivo_mas_o_inimigo_esta": {
    "en": "⚠ **{heroi}** attempts **Sneak Attack** but the enemy is out of range!",
    "pt": "⚠ **{heroi}** tenta **Ataque Furtivo** mas o inimigo está fora de alcance!"
  },
  "narracao.tenta_desarmar_d20_des_vs_dif": {
    "en": "🔧 **{heroi}** tries to disarm **{tipo_get_nome_arm_tipo}**: d20({d20})+DEX({bonus})={total} vs DC {dif}.",
    "pt": "🔧 **{heroi}** tenta desarmar **{tipo_get_nome_arm_tipo}**: d20({d20})+DES({bonus})={total} vs dif {dif}."
  },
  "narracao.tenta_escapar_mas_falha_vs_cd_perde_o_mo": {
    "en": "⛓️ **{heroi}** tries to break free but fails! ({detalhe} vs DC {dc}) — loses the movement!",
    "pt": "⛓️ **{heroi}** tenta escapar mas falha! ({detalhe} vs CD {dc}) — perde o movimento!"
  },
  "narracao.tenta_golpe_divino_mas_errou_d20_vs_ca": {
    "en": "⚡ **{heroi}** attempts **Divine Strike** but **MISSED** (d20={roll}={total} vs AC {t_ac})!",
    "pt": "⚡ **{heroi}** tenta **Golpe Divino** mas **ERROU** (d20={roll}={total} vs CA {t_ac})!"
  },
  "narracao.tenta_golpe_divino_mas_o_inimigo_esta_fo": {
    "en": "⚠ **{heroi}** attempts **Divine Strike** but the enemy is out of range!",
    "pt": "⚠ **{heroi}** tenta **Golpe Divino** mas o inimigo está fora de alcance!"
  },
  "narracao.tenta_golpe_pesado_mas_errou_d20_vs_ca": {
    "en": "💥 **{heroi}** attempts **Heavy Strike** but **MISSED** (d20={roll}={total} vs AC {t_ac})!",
    "pt": "💥 **{heroi}** tenta **Golpe Pesado** mas **ERROU** (d20={roll}={total} vs CA {t_ac})!"
  },
  "narracao.tenta_golpe_pesado_mas_o_inimigo_esta_fo": {
    "en": "⚠ **{heroi}** attempts **Heavy Strike** but the enemy is out of range!",
    "pt": "⚠ **{heroi}** tenta **Golpe Pesado** mas o inimigo está fora de alcance!"
  },
  "narracao.terreno.agua": {
    "en": "Water",
    "pt": "Água"
  },
  "narracao.terreno.agua_profunda": {
    "en": "Deep Water",
    "pt": "Água profunda"
  },
  "narracao.terreno.piso_congelado": {
    "en": "Frozen Floor",
    "pt": "Piso congelado"
  },
  "narracao.terreno.planicie_nevada": {
    "en": "Snowy Plain",
    "pt": "Planície nevada"
  },
  "narracao.tira_1_no_arremesso_a_adaga_se_quebra": {
    "en": "💥 **{monstro}** rolls a **1** on the throw — the dagger **breaks**!",
    "pt": "💥 **{monstro}** tira **1** no arremesso — a adaga **se quebra**!"
  },
  "narracao.tiranossauro_cauda_derruba": {
    "en": "🦖 **{monstro}** knocks **{alvo}** down with its tail! (d20={d20}{bonus}={total} vs DC {dc}) — no movement next turn.",
    "pt": "🦖 **{monstro}** derruba **{alvo}** com a cauda! (d20={d20}{bonus}={total} vs CD {dc}) — sem movimento no próximo turno."
  },
  "narracao.tiranossauro_resiste_cauda": {
    "en": "🦖 **{alvo}** keeps their footing against the Tyrannosaurus's tail! (Reflex {total} vs DC {dc})",
    "pt": "🦖 **{alvo}** resiste à cauda do Tiranossauro! (Reflexos {total} vs CD {dc})"
  },
  "narracao.torna_se_guerreiro_da_luz_visao_ataque_d": {
    "en": "💡 **{heroi}** becomes a **Warrior of Light** | vision+{bonus_validos_visao} attack+{bonus_validos_ataque} damage+{bonus_validos_dano} AC+{bonus_validos_ca} (upkeep 🍖-{custo_fome} 💧-{custo_sede}).",
    "pt": "💡 **{heroi}** torna-se **Guerreiro da Luz** | visão+{bonus_validos_visao} ataque+{bonus_validos_ataque} dano+{bonus_validos_dano} CA+{bonus_validos_ca} (manutenção 🍖-{custo_fome} 💧-{custo_sede})."
  },
  "narracao.torna_se_protetor_de_metade_do_dano_rece": {
    "en": "🛡️ **{heroi}** becomes **Protector** of **{alvo}** — damage is shared with Richard by the Protector rules. Richard also gains −3 damage reduction. (🍖-{fome_cost} 💧-{sede_cost})",
    "pt": "🛡️ **{heroi}** torna-se **Protetor** de **{alvo}** — o dano é dividido com Richard conforme as regras do Protetor. Richard também recebe redução de 3 no dano. (🍖-{fome_cost} 💧-{sede_cost})"
  },
  "narracao.transforma_uma_area_x_em": {
    "en": "❄️ **{caster}** turns a **{lado}x{lado}** area into **{tipo_txt}** {dur_txt}.",
    "pt": "❄️ **{caster}** transforma uma área **{lado}x{lado}** em **{tipo_txt}** {dur_txt}."
  },
  "narracao.transforma_uma_area_x_em_por_rodada_s": {
    "en": "🌊 **{caster}** turns a **{lado}x{lado}** area into **{tipo_txt}** for {dur} round(s).",
    "pt": "🌊 **{caster}** transforma uma área **{lado}x{lado}** em **{tipo_txt}** por {dur} rodada(s)."
  },
  "narracao.troll_cai_mas_regenera": {
    "en": "🩸 **{monstro}** falls, but its wounds begin to regenerate!",
    "pt": "🩸 **{monstro}** cai, mas seus ferimentos começam a se regenerar!"
  },
  "narracao.troll_regenera_4_pv": {
    "en": "🩸 **{monstro}** regenerates {cura} HP at the start of its turn.",
    "pt": "🩸 **{monstro}** regenera {cura} PV no início do turno."
  },
  "narracao.troll_se_ergue_com_1_pv": {
    "en": "🩸 **{monstro}** knits itself back together and rises with 1 HP!",
    "pt": "🩸 **{monstro}** recompõe o corpo e se ergue com 1 PV!"
  },
  "narracao.turno_controle_recursos": {
    "en": " 🍖 {fome}/10 💧 {sede}/10",
    "pt": " 🍖 {fome}/10 💧 {sede}/10"
  },
  "narracao.turno_de": {
    "en": "🎲 **{next_p}**'s turn!",
    "pt": "🎲 Turno de **{next_p}**!"
  },
  "narracao.turno_de_controle_de_mova_e_encerre": {
    "en": "💀 **{heroi}**'s control turn ({partes}) — move and end the turn again.{recursos}",
    "pt": "💀 Turno de controle de **{heroi}** ({partes}) — mova e encerre o turno novamente.{recursos}"
  },
  "narracao.turno_de_imobilizado_encerre_o_turno_par": {
    "en": "🕸️ **{next_p}**'s turn — immobilized! End the turn to continue.",
    "pt": "🕸️ Turno de **{next_p}** — imobilizado! Encerre o turno para continuar."
  },
  "narracao.turno_de_iniciativa": {
    "en": "🎲 **{heroi}**'s turn (Initiative {actor_initiative}).",
    "pt": "🎲 Turno de **{heroi}** (Iniciativa {actor_initiative})."
  },
  "narracao.um_bau_apareceu_no_centro_da_sala_aproxi": {
    "en": "🎁 A **chest** appeared in the center of the room! Approach it and click to collect.",
    "pt": "🎁 Um **baú** apareceu no centro da sala! Aproxime-se e clique nele para coletar."
  },
  "narracao.um_bau_de_saque_apareceu": {
    "en": "🎒 A **loot chest** appeared!",
    "pt": "🎒 Um **baú de saque** apareceu!"
  },
  "narracao.um_monstro_fere_o_prisioneiro": {
    "en": "⚔️ A monster wounds the prisoner ({dano})!",
    "pt": "⚔️ Um monstro fere o prisioneiro ({dano})!"
  },
  "narracao.uma_passagem_secreta_se_abriu_em": {
    "en": "🧱 A secret passage has opened at {sp_pos_0},{sp_pos_1}!",
    "pt": "🧱 Uma passagem secreta se abriu em {sp_pos_0},{sp_pos_1}!"
  },
  "narracao.unta_na_arma": {
    "en": "🧪 **{m_get_name_o_monstro}** smears **{item}** on their weapon.",
    "pt": "🧪 **{m_get_name_o_monstro}** unta **{item}** na arma."
  },
  "narracao.unta_na_arma_2": {
    "en": "{item_emoji} **{heroi}** coats **{item}** on the weapon — {desc}!",
    "pt": "{item_emoji} **{heroi}** unta **{item}** na arma — {desc}!"
  },
  "narracao.usa": {
    "en": "{item_emoji} **{heroi}** uses **{item}**: {txt}{extra}",
    "pt": "{item_emoji} **{heroi}** usa **{item}**: {txt}{extra}"
  },
  "narracao.usa_2": {
    "en": "📜 **{heroi}** uses **{scroll}**...",
    "pt": "📜 **{heroi}** usa **{scroll}**..."
  },
  "narracao.usa_3": {
    "en": "{defn_get_emoji} **{monstro}** uses **{defn}**!",
    "pt": "{defn_get_emoji} **{monstro}** usa **{defn}**!"
  },
  "narracao.usa_ataque_furtivo_em_d20_vs_ca_de_dano": {
    "en": "🗡️ **{heroi}** uses **Sneak Attack** on **{t}** (d20={roll}+{furtivo_atk}={total} vs AC {t_ac}): **{dmg}** sneak damage!",
    "pt": "🗡️ **{heroi}** usa **Ataque Furtivo** em **{t}** (d20={roll}+{furtivo_atk}={total} vs CA {t_ac}): **{dmg}** de dano furtivo!"
  },
  "narracao.usa_bonus_de_ataque_neste_turno": {
    "en": "{item_emoji} **{heroi}** uses **{item}**! +{val} Attack Bonus this turn!",
    "pt": "{item_emoji} **{heroi}** usa **{item}**! +{val} Bônus de Ataque neste turno!"
  },
  "narracao.usa_chuva_de_flechas_1d8_des_em_todos_os": {
    "en": "🏹 **{heroi}** uses **Arrow Rain**! 1d8+DES on all enemies!",
    "pt": "🏹 **{heroi}** usa **Chuva de Flechas**! 1d8+DES em todos os inimigos!"
  },
  "narracao.usa_de_ataque": {
    "en": "⚗️ **{m_get_name_o_monstro}** uses **{item}**: +{val} attack.",
    "pt": "⚗️ **{m_get_name_o_monstro}** usa **{item}**: +{val} de ataque."
  },
  "narracao.usa_e_fica_oculto": {
    "en": "🕯️ **{m_get_name_o_monstro}** uses **{item}** and becomes hidden.",
    "pt": "🕯️ **{m_get_name_o_monstro}** usa **{item}** e fica oculto."
  },
  "narracao.usa_e_neutraliza_o_veneno": {
    "en": "🟢 **{m_get_name_o_monstro}** uses **{item}** and neutralizes the poison.",
    "pt": "🟢 **{m_get_name_o_monstro}** usa **{item}** e neutraliza o veneno."
  },
  "narracao.usa_e_recebe_no_ataque": {
    "en": "⚗️ **{monstro}** uses **{elixir}** and gains +{elixir_get_value_0} to attack!",
    "pt": "⚗️ **{monstro}** usa **{elixir}** e recebe +{elixir_get_value_0} no ataque!"
  },
  "narracao.usa_e_recupera_hp": {
    "en": "🧪 **{monstro}** uses **{potion}** and recovers **{cura} HP**.",
    "pt": "🧪 **{monstro}** usa **{potion}** e recupera **{cura} HP**."
  },
  "narracao.usa_e_recupera_hp_2": {
    "en": "🧪 **{m_get_name_o_monstro}** uses **{item}** and recovers **{val}** HP.",
    "pt": "🧪 **{m_get_name_o_monstro}** usa **{item}** e recupera **{val}** HP."
  },
  "narracao.usa_e_recupera_hp_3": {
    "en": "{item_emoji} **{heroi}** uses **{item}** and recovers **{val}** HP!{doses_msg}",
    "pt": "{item_emoji} **{heroi}** usa **{item}** e recupera **{val}** HP!{doses_msg}"
  },
  "narracao.usa_em_save_d20_vs_cd": {
    "en": "✨ **{monstro}** uses **{ab_name}** on **{tgt_name}**! {ability_save} save: d20({d20}){sb_str}={stot} vs DC {ability_dc} — {resistiu_if_save_ok_else}",
    "pt": "✨ **{monstro}** usa **{ab_name}** em **{tgt_name}**! Save {ability_save}: d20({d20}){sb_str}={stot} vs CD {ability_dc} — {resistiu_if_save_ok_else}"
  },
  "narracao.usa_explosao_de_vapor_em_cone_de_quadrad": {
    "en": "🌋 **{monstro}** uses **Steam Burst** in a circle with a radius of {ability_get_range_3} squares.",
    "pt": "🌋 **{monstro}** usa **Explosão de Vapor** em um círculo de raio {ability_get_range_3} quadrados."
  },
  "narracao.usa_golpe_divino_em_d20_vs_ca_de_dano_sa": {
    "en": "⚡ **{heroi}** uses **Divine Strike** on **{t}** (d20={roll}+{p_atk_bonus}={total} vs AC {t_ac}): **{dmg}** holy damage!",
    "pt": "⚡ **{heroi}** usa **Golpe Divino** em **{t}** (d20={roll}+{p_atk_bonus}={total} vs CA {t_ac}): **{dmg}** de dano sagrado!"
  },
  "narracao.usa_golpe_pesado_em_d20_vs_ca_de_dano": {
    "en": "💥 **{heroi}** uses **Heavy Strike** on **{t}** (d20={roll}+{p_atk_bonus}={total} vs AC {t_ac}): **{dmg}** damage!",
    "pt": "💥 **{heroi}** usa **Golpe Pesado** em **{t}** (d20={roll}+{p_atk_bonus}={total} vs CA {t_ac}): **{dmg}** de dano!"
  },
  "narracao.usa_imposicao_das_maos_em_cura_hp": {
    "en": "🙏 **{heroi}** uses **Lay on Hands** on **{alvo}** — heals **{cura_efetiva}** HP ({alvo_hp}/{alvo_max_hp})! (🍖-{fome_cost} 💧-{sede_cost})",
    "pt": "🙏 **{heroi}** usa **Imposição das Mãos** em **{alvo}** — cura **{cura_efetiva}** HP ({alvo_hp}/{alvo_max_hp})! (🍖-{fome_cost} 💧-{sede_cost})"
  },
  "narracao.usa_investida_heroica_e_dobra_seu_desloc": {
    "en": "🐗 {monstro} uses **Heroic Charge** and doubles its movement this round.",
    "pt": "{monstro} usa Investida Heroica e dobra seu deslocamento nesta rodada."
  },
  "narracao.usa_investida_heroica_e_dobra_seu_desloc_2": {
    "en": "{nome_criatura_m} uses Heroic Charge and doubles its movement.",
    "pt": "{nome_criatura_m} usa Investida Heroica e dobra seu deslocamento."
  },
  "narracao.usa_lanca_de_gelo_em_de_dano_de_frio": {
    "en": "🧊 **{heroi}** uses **Ice Lance**{extra} on **{t}**: **{dmg}** cold damage!",
    "pt": "🧊 **{heroi}** usa **Lança de Gelo**{extra} em **{t}**: **{dmg}** de dano de frio!"
  },
  "narracao.usa_o_pergaminho_de_dominar_morto_vivo_e": {
    "en": "🧙 **{monstro}** uses the **Scroll of Dominate Undead** on **{alvo_nome}**!",
    "pt": "🧙 **{monstro}** usa o **Pergaminho de Dominar Morto-Vivo** em **{alvo_nome}**!"
  },
  "narracao.usa_para_envenenar_a_arma": {
    "en": "🧪 **{m_get_name_o_monstro}** uses **{item}** to poison their weapon.",
    "pt": "🧪 **{m_get_name_o_monstro}** usa **{item}** para envenenar a arma."
  },
  "narracao.usa_passo_fantasma_e_recebe_movimento_ne": {
    "en": "👻 {monstro} uses **Ghost Step** and gains +{bonus} movement this round.",
    "pt": "{monstro} usa Passo Fantasma e recebe +{bonus} movimento nesta rodada."
  },
  "narracao.usa_presenca_aterradora_contra_vontade_v": {
    "en": "😱 {monstro} uses **Terrifying Presence** against {heroi}: {resultado} (Will {total} vs DC {dc}).",
    "pt": "{monstro} usa Presença Aterradora contra {heroi}: {resultado} (Vontade {total} vs CD {dc})."
  },
  "narracao.usa_pressao_constante_2_de_ca_por_2_roda": {
    "en": "{nome_criatura_m} uses Constant Pressure: -2 AC for 2 rounds.",
    "pt": "{nome_criatura_m} usa Pressão Constante: -2 de CA por 2 rodadas."
  },
  "narracao.usa_provocar_todos_os_monstros_agora_foc": {
    "en": "😤 **{heroi}** uses **Taunt** — all monsters now focus on them!",
    "pt": "😤 **{heroi}** usa **Provocar** — todos os monstros agora focam nele!"
  },
  "narracao.usa_sopro_de_dragao_de_em": {
    "en": "🐉 **{monstro}** uses **Dragon's Breath** of {labels_get_element_eleme} in a {shape}!",
    "pt": "🐉 **{monstro}** usa **Sopro de Dragão** de {labels_get_element_eleme} em {shape}!"
  },
  "narracao.usa_tiro_duplo_em_acerto_s_de_dano_total": {
    "en": "🏹 **{heroi}** uses **Double Shot** on **{t}**: {hits} hit(s), **{total_dmg}** total damage!",
    "pt": "🏹 **{heroi}** usa **Tiro Duplo** em **{t}**: {hits} acerto(s), **{total_dmg}** de dano total!"
  },
  "narracao.usa_tiro_duplo_mas_ambos_os_tiros_errara": {
    "en": "🏹 **{heroi}** uses **Double Shot** but both shots **MISSED**!",
    "pt": "🏹 **{heroi}** usa **Tiro Duplo** mas ambos os tiros **ERRARAM**!"
  },
  "narracao.usa_tiro_perfurante_em_de_dano_acerto_au": {
    "en": "🎯 **{heroi}** uses **Piercing Shot** on **{t}**: **{dmg}** damage (automatic hit, ignores AC)!",
    "pt": "🎯 **{heroi}** usa **Tiro Perfurante** em **{t}**: **{dmg}** de dano (acerto automático, ignora CA)!"
  },
  "narracao.usou_acao_bonus_fome_sede": {
    "en": "🎯 **{heroi}** used a bonus action! 🍖 Hunger: {fome}/10 | 💧 Thirst: {sede}/10",
    "pt": "🎯 **{heroi}** usou ação bônus! 🍖 Fome: {fome}/10 | 💧 Sede: {sede}/10"
  },
  "narracao.usou_o_ultimo_projetil": {
    "en": "🏹 **{heroi}** used their last projectile!",
    "pt": "🏹 **{heroi}** usou o último projétil!"
  },
  "narracao.varre_a_cauda_pela_retaguarda": {
    "en": "🦂 **{monstro}** sweeps its tail through the back ranks!",
    "pt": "🦂 **{monstro}** varre a cauda pela retaguarda!"
  },
  "narracao.vinculo_maldito.cria": {
    "en": "{caster} forges a Cursed Bond of Pain with {alvo} for {n} rounds. Each bond transfers 25% of the damage taken.",
    "pt": "{caster} cria um Vínculo Maldito da Dor com {alvo} por {n} rodadas. Cada vínculo transfere 25% do dano sofrido."
  },
  "narracao.vinculo_maldito.resiste": {
    "en": "{alvo} resists the Cursed Bond of Pain.",
    "pt": "{alvo} resiste ao Vínculo Maldito da Dor."
  },
  "narracao.vira_a_fome_sede_mas_fica_alegre_1_ataqu": {
    "en": "{item_emoji} **{heroi}** downs the **{item}** (+{val} hunger/thirst), but turns merry: **-1 attack** for 10 rounds!",
    "pt": "{item_emoji} **{heroi}** vira a **{item}** (+{val} fome/sede), mas fica alegre: **-1 ataque** por 10 rodadas!"
  },
  "narracao.vira_a_fome_sede_mas_fica_embriagado_1_a": {
    "en": "{item_emoji} **{heroi}** downs the **{item}** (+{val} hunger/thirst), but gets drunk: **-1 attack / -1 Reflex** for 10 rounds!",
    "pt": "{item_emoji} **{heroi}** vira a **{item}** (+{val} fome/sede), mas fica embriagado: **-1 ataque / -1 Reflexos** por 10 rodadas!"
  },
  "narracao.virote_incendiario_de_dano_de_fogo": {
    "en": "🔥 Incendiary bolt: +{xdmg} fire damage!",
    "pt": "🔥 Virote incendiário: +{xdmg} de dano de fogo!"
  },
  "narracao.visao_de_expandida_para_raio": {
    "en": "👁️ **{heroi}**'s vision expanded to radius {raio}.",
    "pt": "👁️ Visão de **{heroi}** expandida para raio {raio}."
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_NARRACAO);
