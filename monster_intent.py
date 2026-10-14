"""Previsão da intenção dos monstros (somente leitura).

Mixin de GameRoom. Reusa os helpers de alvo/alcance da IA real para responder
"quem este monstro atacaria no próximo turno dele?" sem alterar nenhum estado: o
foco (zerado por monstro, como cada gm_phase(m) da iniciativa faz), as casas
reservadas e o `_water_moves_left` de cada monstro são salvos e restaurados em
`finally`. A paridade com a IA real é provada rodando gm_phase em
tools/test_monster_intent.py [6c].

Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
O item devolvido é a MESMA estrutura que a evolução B (intenção gravada pela IA
no fim do turno do monstro) usaria.
"""

import copy

_AUSENTE = object()

# Campos que mudam a previsão sem mexer em posição/vida: entram na assinatura
# do cache (`_intent_assinatura`). Alvo: visibilidade, controle (pontuação de
# alvo), altura/voo, engolido. Monstro: estados que tiram o turno, compulsões,
# orçamento de movimento e memória de adaptação.
INTENT_CAMPOS_ALVO = (
    "alive", "hp", "max_hp", "vida_atual", "vida_max",
    "invisivel_sombras", "invisivel_magico", "oculto_vela", "fosso_oculto",
    "paralisado", "imobilizado", "enredado", "preso", "derrubado",
    "engolido", "altura", "voo", "voo_magico", "visao_escuro", "cego",
    "fora_masmorra", "connected", "class_id", "requiem_alvo",
)
INTENT_CAMPOS_MONSTRO = INTENT_CAMPOS_ALVO + (
    "alertado", "control_mode", "master_target_id",
    "provocado", "provocado_turnos", "provocado_por",
    "comando_pendente_pid", "dominio_mente_pendente_pid", "petrificado",
    "turbilhao_perde_acao", "turbilhao_perde_movimento", "bordao_atordoado",
    "perde_turno", "dormindo", "dormindo_rodadas", "comandado", "dominado",
    "dominado_rodadas", "dominado_permanente", "com_medo", "medo_rodadas",
    "lento", "lento_rodadas", "lento_pulou", "movement", "requiem_por",
    "ai_adaptation", "attacks", "ai_type",
)


class MonsterIntent:
    # ── seleção de quem entra na previsão ────────────────────────────────────
    def _intent_observadores(self, p):
        """Heróis cuja visão vale para este pedido: o próprio e os do mesmo
        controlador (Solo com grupo)."""
        ctrl = p.get("controlador")
        obs = [p]
        if ctrl:
            obs += [q for q in self.players.values()
                    if q is not p and (q.get("controlador") == ctrl
                                       or q.get("id") == ctrl) and self._ativo(q)]
        return obs

    def _intent_monstros_em_ordem(self):
        """Monstros na ordem da iniciativa vigente (as casas reservadas por um
        atacante valem para os seguintes); os que não estão na fila vão ao fim."""
        ordem = [e.get("id") for e in self.initiative_order if e.get("kind") == "monster"]
        vistos = set()
        saida = []
        for mid in ordem:
            m = self.monsters.get(mid)
            if m is not None and mid not in vistos:
                vistos.add(mid)
                saida.append(m)
        for mid, m in self.monsters.items():
            if mid not in vistos:
                saida.append(m)
        return saida

    def _intent_monstro_elegivel(self, m):
        if m.get("hp", 0) <= 0:
            return False
        if m.get("invisivel_sombras") or m.get("invisivel_magico") or m.get("oculto_vela"):
            return False
        if not self._monstro_ativo_em_combate(m):
            return False
        if self._mestre_ativo() and m.get("control_mode") == "manual":
            return False
        if self._intent_perde_turno(m):
            return False
        return True

    def _intent_perde_turno(self, m):
        """Espelho SÓ LEITURA dos estados que fazem o monstro não atacar no
        próximo turno: o despacho de `_activate_initiative_actor` (Comando /
        Dominar Mente pendentes, petrificado), o prólogo
        `_upkeep_inicio_turno_monstro` (perda de ação, atordoado, rede,
        paralisia, enredado) e `_status_monstro_turno` (sono, comando,
        domínio, medo, lentidão). Paralisia/enredado têm teste de saída no
        turno: na dúvida, sem seta."""
        if m.get("comando_pendente_pid") or m.get("dominio_mente_pendente_pid"):
            return True
        if m.get("petrificado") or m.get("turbilhao_perde_acao") or m.get("bordao_atordoado"):
            return True
        if m.get("perde_turno") and not self._tem_habilidade(m, "inabalavel"):
            return True
        if m.get("paralisado"):
            return True
        if m.get("enredado") and not self._tem_habilidade(m, "inabalavel"):
            return True
        # _status_monstro_turno: o contador decide se o estado ainda vale
        if m.get("dormindo") and m.get("dormindo_rodadas", 0) > 0:
            return True
        if m.get("comandado"):
            return True
        if m.get("dominado") and (m.get("dominado_permanente")
                                  or m.get("dominado_rodadas", 0) > 0):
            return True
        if m.get("com_medo") and m.get("medo_rodadas", 0) > 0:
            return True
        # Lentidão alterna: o próximo turno é perdido quando lento_pulou vira True.
        if (m.get("lento") and m.get("lento_rodadas", 0) > 0
                and not m.get("lento_pulou", False)):
            return True
        return False

    def _intent_orcamento(self, m):
        """Movimento do PRÓXIMO turno do monstro, como a gm_phase o calcula no
        início da vez (`_water_turn_moves`). Calculado numa cópia: a função
        mexe em marcadores de terreno e na Canção do monstro."""
        try:
            copia = copy.deepcopy(m)
            orcamento = int(self._water_turn_moves(copia, copia.get("movement", 4)) or 0)
        except Exception:
            orcamento = 0
        if m.get("turbilhao_perde_movimento"):
            return 0
        if m.get("preso") and self._captor_ativo(m):
            return 0
        return max(0, orcamento)

    # ── um monstro ────────────────────────────────────────────────────────────
    def _intent_compulsao(self, m):
        if self._requiem_forca_bardo(m):
            return True
        if m.get("provocado") and m.get("provocado_turnos", 0) > 0:
            return True
        return bool(self._mestre_ativo() and m.get("control_mode") == "semi"
                    and m.get("master_target_id"))

    def _intent_de_monstro(self, m, alvos_base):
        """Previsão de um monstro. O `_water_moves_left` guardado é o do turno
        PASSADO (a gm_phase o renova no início da vez e o gasta a cada passo):
        trocado pelo orçamento do próximo turno durante o cálculo e devolvido
        em `finally` (ausente volta a ser ausente)."""
        orcamento = self._intent_orcamento(m)
        antes = m.get("_water_moves_left", _AUSENTE)
        m["_water_moves_left"] = orcamento
        try:
            return self._intent_de_monstro_calc(m, alvos_base, orcamento)
        finally:
            if antes is _AUSENTE:
                m.pop("_water_moves_left", None)
            else:
                m["_water_moves_left"] = antes

    def _intent_de_monstro_calc(self, m, alvos_base, orcamento):
        alvos = self._alvos_visiveis_para_monstro(m, alvos_base)
        escolhido = self._get_monster_primary_target(m, alvos)
        if not escolhido:
            return None
        obj = escolhido["obj"]
        ataques = self._monster_hostility_attacks(m)
        a_dist = next((a for a in ataques if a.get("range")), None)
        a_corpo = next((a for a in ataques if not a.get("range")), None)
        papel = self._monster_ai_role(m)
        alvo_pos = list(obj["pos"])

        # 1) já em alcance sem se mexer?
        em_alcance = None
        for atk in ([a_dist] if a_dist else []) + ([a_corpo] if a_corpo else []):
            if self._monster_attack_in_range(m, alvo_pos, atk):
                em_alcance = atk
                break
        casa = None
        atk_usado = em_alcance
        alcanca = False
        if em_alcance is not None:
            alcanca, casa = True, list(m["pos"])
        elif m.get("ai_type"):
            # 2) alcança movendo? (mesma busca de casa da IA, com o BFS do
            # movimento). Só a IA modular anda E ataca no mesmo turno: a ficha
            # sem ai_type (caminho legado da gm_phase) ataca só se já estiver
            # ao alcance; fora dele dá um passo e para.
            alcancaveis = self._master_reach_bfs(m, orcamento) if orcamento > 0 else set()
            if a_dist is not None:
                goal = self._monster_ranged_goal(m, escolhido, a_dist)
                atk_usado = a_dist
            else:
                goal = self._monster_melee_goal(m, escolhido)
                atk_usado = a_corpo
            if goal is not None and tuple(goal) in alcancaveis:
                alcanca, casa = True, list(goal)
        else:
            atk_usado = a_corpo or a_dist

        if papel in {"controlador", "suporte"} or atk_usado is None:
            acao = "ameaca"
        elif atk_usado.get("range"):
            acao = "distancia"
        else:
            acao = "corpo"

        # "firme" só quando nada pode mudar a escolha: compulsão, ou único alvo
        # visível já ao alcance sem mover. Habilidade especial nunca é firme.
        firme = (acao != "ameaca"
                 and (self._intent_compulsao(m)
                      or (len(alvos) == 1 and em_alcance is not None)))
        return {
            "monstro_id": m["id"],
            "alvo_id": obj.get("id"),
            "alvo_tipo": "animado" if escolhido.get("kind") == "animado" else "heroi",
            "alvo_pos": alvo_pos,
            "acao": acao,
            "alcanca": bool(alcanca),
            "casa_ataque": casa if alcanca else None,
            "certeza": "firme" if firme else "provavel",
        }

    # ── API ───────────────────────────────────────────────────────────────────
    def _prever_intencoes(self, pid):
        """Lista de intenções dos monstros que o herói `pid` enxerga agora."""
        p = self.players.get(pid)
        if not p or not self._ativo(p) or not p.get("pos"):
            return []
        foco_antes = self.__dict__.get("_monster_ai_focus_target_id", _AUSENTE)
        reservas_antes = self.__dict__.get("_monster_ai_reserved_tiles", _AUSENTE)
        try:
            self._monster_ai_focus_target_id = None
            self._monster_ai_reserved_tiles = set()
            alvos_base = self._alvos_hostis_para_monstros()
            observadores = self._intent_observadores(p)
            itens = []
            for m in self._intent_monstros_em_ordem():
                if not self._intent_monstro_elegivel(m):
                    continue
                if not any(self._heroi_enxerga_monstro(o, m) for o in observadores):
                    continue
                # A iniciativa roda um gm_phase(m) por monstro, e cada chamada
                # zera o foco: não há foco coletivo entre monstros na masmorra.
                # As casas reservadas, ao contrário, ficam acumuladas: aproximam
                # as casas que os monstros anteriores já terão ocupado.
                self._monster_ai_focus_target_id = None
                item = self._intent_de_monstro(m, alvos_base)
                if item:
                    itens.append(item)
            return itens
        except Exception:
            return []
        finally:
            for nome, antes in (("_monster_ai_focus_target_id", foco_antes),
                                ("_monster_ai_reserved_tiles", reservas_antes)):
                if antes is _AUSENTE:
                    self.__dict__.pop(nome, None)
                else:
                    setattr(self, nome, antes)
