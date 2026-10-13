"""Previsão da intenção dos monstros (somente leitura).

Mixin de GameRoom. Reusa os helpers de alvo/alcance da IA real para responder
"quem este monstro atacaria se agisse agora?" sem alterar nenhum estado: o foco
coletivo e as casas reservadas são salvos e restaurados em `finally`.

Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
O item devolvido é a MESMA estrutura que a evolução B (intenção gravada pela IA
no fim do turno do monstro) usaria.
"""

_AUSENTE = object()


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
        """Monstros na ordem da iniciativa vigente (reproduz o foco coletivo);
        os que não estão na fila vão ao fim."""
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
        return True

    # ── um monstro ────────────────────────────────────────────────────────────
    def _intent_compulsao(self, m):
        if self._requiem_forca_bardo(m):
            return True
        if m.get("provocado") and m.get("provocado_turnos", 0) > 0:
            return True
        return bool(self._mestre_ativo() and m.get("control_mode") == "semi"
                    and m.get("master_target_id"))

    def _intent_de_monstro(self, m, alvos_base):
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
        else:
            # 2) alcança movendo? (mesma busca de casa da IA, com o BFS do movimento)
            try:
                orcamento = int(m.get("movement", 4) or 0)
            except (TypeError, ValueError):
                orcamento = 4
            alcancaveis = self._master_reach_bfs(m, orcamento)
            if a_dist is not None:
                goal = self._monster_ranged_goal(m, escolhido, a_dist)
                atk_usado = a_dist
            else:
                goal = self._monster_melee_goal(m, escolhido)
                atk_usado = a_corpo
            if goal is not None and tuple(goal) in alcancaveis:
                alcanca, casa = True, list(goal)

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
