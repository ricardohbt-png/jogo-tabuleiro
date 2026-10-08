"""Cenários do Campo de Treinamento. Não cria conexões nem membros de campanha."""
from copy import deepcopy

# Lições-ponte que levam o herói de volta ao corredor DEPOIS da trilha da classe
# (`volta_<classe>`): pertencem à classe, mas não contam para o bônus da trilha
# (que sai na última lição de verdade) e são refeitas junto com a sala.
LICAO_FORA_DA_TRILHA_PREFIXOS = ("volta_",)


def _licao_fora_da_trilha(lic):
    return str((lic or {}).get("id", "")).startswith(LICAO_FORA_DA_TRILHA_PREFIXOS)


class TutorialTraining:
    def _training_room(self, actor, x, y):
        """Restrição permanente, independente de porta, voo e estado de lição."""
        owner = actor or {}
        if owner.get("owner"):
            owner = self.players.get(owner["owner"], {})
        if owner is getattr(self, "prisoner", None):
            owner = self.players.get(owner.get("rescuer_pid"), {})
        for room in self.rooms:
            cls = room.get("allowed_class")
            if cls and (room["x"] <= x < room["x"] + room["w"]
                        and room["y"] <= y < room["y"] + room["h"]
                        or [x, y] in room.get("doors", [])):
                if owner.get("class_id") != cls:
                    return room
        return None

    async def _training_check_entry(self, pid, actor, x, y):
        room = self._training_room(actor, x, y)
        if room:
            api = self._tutorial_api()
            await self.send_to(pid, {"type": "error", "msg": api.T(
                "erro.sala_exclusiva_heroi", heroi=api.CLASSES[room["allowed_class"]]["name"])})
            return False
        return True

    def _training_ally(self, p, ident):
        ally = getattr(self, "training_allies", {}).get(ident)
        if not ally or not p or ally.get("allowed_class") != p.get("class_id"):
            return None
        room = self._room_containing_point(p.get("pos", [-1, -1]))
        return ally if room and room["id"] == ally["room_id"] else None

    def _training_heal_targets(self, p):
        return list(self.players.values()) + [a for a in self.training_allies.values()
                                               if self._training_ally(p, a["id"]) is not None]

    def _slots_livres_treino(self, p, pos=None):
        """Fatia 15: dentro da sala exclusiva do Mago as magias não gastam slots.

        Derivado da posição (sem estado novo, nada para a foto nem para o
        `repetir_tutorial`): vale só no modo treinamento, para o Mago, numa
        casa de piso da sala com `allowed_class == "mage"`. A porta e o corredor
        ficam fora. O Clérigo e a mesa de teste do editor não entram."""
        if not getattr(self, "training_mode", False) or not p:
            return False
        if p.get("class_id") != "mage" or p.get("test_hero") or not p.get("alive", True):
            return False
        x, y = pos if pos is not None else p.get("pos", [-1, -1])
        for room in self.rooms:
            if (room.get("allowed_class") == "mage"
                    and room["x"] <= x < room["x"] + room["w"]
                    and room["y"] <= y < room["y"] + room["h"]):
                return True
        return False

    async def _avisar_slots_treino(self, p, antes, depois):
        """Aviso curto só quando a regra liga/desliga (não a cada passo)."""
        if antes == depois or not p:
            return
        motivo = "slots_treino_liga" if depois else "slots_treino_desliga"
        await self.send_to(p["id"], {"type": "licao_dica", "motivo": motivo})

    def _training_init(self, defn):
        self.training_mode = defn.get("tutorial_training") is True
        self.training_allies = {}
        self.training_state = {}
        if not self.training_mode:
            return
        api = self._tutorial_api()
        for authored, live in zip(defn.get("traps", []), self.armadilhas):
            if authored.get("id") == "trap_treino_luccas":
                live["id"] = authored["id"]
        self.training_state["trap_template"] = deepcopy(next(
            (a for a in self.armadilhas if a.get("id") == "trap_treino_luccas"), None))
        for cls in ("cleric", "bard"):
            room = next((r for r in self.rooms if r.get("allowed_class") == cls), None)
            if not room:
                continue
            for n in range(2 if cls == "cleric" else 1):
                ident = f"__treino_{cls}_{n + 1}"
                a = api.make_player(ident, f"Aprendiz {n + 1}", "warrior", 0)
                a.update(training_ally=True, allowed_class=cls, room_id=room["id"],
                         pos=[room["x"] + 3 + n, room["y"] + 2],
                         hp=5, max_hp=20, alive=True, gold=0, xp=0, connected=False,
                         pawn_override="soldado")   # miniatura do Soldado (2D png / 3D glb)
                self.training_allies[ident] = a
        for m in self.monsters.values():
            room = self._room_by_id(m.get("room_id"))
            if room and room.get("allowed_class"):
                m["training_target"] = True
                m["training_class"] = room["allowed_class"]
                m["xp"] = 0
        # Baú dentro de uma sala exclusiva: o que ele guarda é emprestado (some na saída)
        # e o molde permite recolocá-lo cheio no `repetir_tutorial`.
        self.training_state["baus_modelo"] = {}
        for ch in self.chests.values():
            room = self._room_containing_point(ch["pos"])
            if room and room.get("allowed_class"):
                for it in ch["items"]:
                    it["tutorial_loan"] = True
                self.training_state["baus_modelo"][room["allowed_class"]] = {
                    "pos": list(ch["pos"]), "gold": ch["gold"], "items": deepcopy(ch["items"])}
        if self.prisoner:
            room = self._room_by_id(self.prisoner.get("room_id"))
            if room and room.get("allowed_class") == "paladin":
                self.prisoner["training_refem"] = True
                self.prisoner["nome"] = "Refém de treinamento"
                # Molde para devolver o refém depois de dispensado (repetir_tutorial).
                self.training_state["refem_modelo"] = deepcopy(self.prisoner)

    def _training_devolver_emprestimos(self, p):
        """Tira da bolsa e das mãos o que o baú da sala emprestou; o Alaúde do Bardo volta à mão do escudo."""
        p["bag"] = [i for i in p.get("bag", []) if not i.get("tutorial_loan")]
        gear = p.get("gear") or {}
        off = gear.get("off_hand")
        if off and off.get("tutorial_loan"):
            api = self._tutorial_api()
            alaude = next((i for i in p["bag"] if i.get("tipo_item") == "instrumento"
                           and i.get("base") == "alaude"), None)
            if alaude:
                p["bag"].remove(alaude)
            gear["off_hand"] = alaude or api.criar_instrumento("alaude", "velho")

    def _training_recolocar_bau(self, cls):
        """Devolve o baú da sala (cheio) se ele sumiu ou perdeu o que emprestava."""
        modelo = self.training_state.get("baus_modelo", {}).get(cls)
        if not modelo:
            return
        bau = next((c for c in self.chests.values() if list(c["pos"]) == modelo["pos"]), None)
        if bau is None:
            self._spawn_chest(modelo["pos"], modelo["gold"], modelo["items"])
            return
        ids = {i.get("id") for i in bau["items"]}
        for it in modelo["items"]:
            if it.get("id") not in ids:
                bau["items"].append(deepcopy(it))

    def _training_refem_pode_ir(self, pr, x, y):
        """O refém do exercício anda, mas só dentro da própria sala."""
        sala = self._room_containing_point([x, y])
        return bool(sala and sala.get("id") == pr.get("room_id"))

    async def _training_refem_chegou(self, pid, pr):
        """O refém terminou um passo: se era a missão de guiá-lo, cumpre e dispensa."""
        p = self.players.get(pid)
        lesson = next((l for l in self.licoes if l["id"] == (p or {}).get("licao_atual")), None)
        if not lesson or (lesson.get("tarefa") or {}).get("tipo") != "guiar_refem":
            return
        await self._licao_evento(p, "guiar_refem", alvo=list(pr["pos"]))
        if lesson["id"] in (p.get("licoes_feitas") or []):
            await self._dispensar_prisioneiro(p)

    async def _dispensar_prisioneiro(self, p=None):
        """Tira o refém do jogo sem derrota: some do tabuleiro e do estado, e o
        jogador deixa de controlá-lo. O molde fica em training_state para o
        `repetir_tutorial` devolvê-lo."""
        pr = self.prisoner
        if not pr or not pr.get("training_refem"):
            return
        self.prisoner = None
        self.prisioneiro_done = True
        for h in self.players.values():
            if h.get("protetor_alvo") == "__prisioneiro__":
                h["protetor_ativo"] = False; h["protetor_alvo"] = None
        await self.gm_say(self._tutorial_api().T("narracao.refem_agradece_e_se_retira"))
    def _training_spell_available(self, p, mid):
        api = self._tutorial_api()
        magic = api.GRIMORIO.get(mid) or {}
        slots = api.slots_max_para(p)
        return (mid in p.get("magias_conhecidas", [])
                and mid in api.GRIMORIO_IMPLEMENTADAS
                and int(slots.get(magic.get("circulo"), 0) or 0) > 0)

    def _training_requirements(self, p, lesson):
        req = lesson.get("requisitos") or {}
        api = self._tutorial_api()
        if p.get("level", 1) < req.get("nivel", 1):
            return False
        if req.get("guild") and not api.tem_espec(p, req["guild"]):
            return False
        if req.get("instrumento") and (p.get("gear", {}).get("off_hand") or {}).get("tipo_item") != "instrumento":
            return False
        if req.get("magia") and not self._training_spell_available(p, req["magia"]):
            return False
        kind = req.get("magia_tipo")
        if kind:
            spells = [api.GRIMORIO[mid] for mid in p.get("magias_conhecidas", [])
                      if self._training_spell_available(p, mid)]
            if kind == "qualquer":
                return bool(spells)
            if kind == "dano":
                return any(m.get("dano_base") or m.get("dano_por_nivel") for m in spells)
            if kind == "save":
                return any(m.get("save") for m in spells)
            if kind == "duracao":
                return any(m.get("duracao") or m.get("rodadas") for m in spells)
        return True

    def _training_add_unlocked_lessons(self):
        """Novas lições por magia ou especialização possuída; sem conceder poderes."""
        if not self.training_mode:
            return
        api = self._tutorial_api()
        bases = list(self.licoes)
        added = set()
        for p in self.players.values():
            cls = p.get("class_id")
            room = next((r for r in self.rooms if r.get("allowed_class") == cls), None)
            if not room:
                continue
            order = 100
            owned = p.get("guild_owned") or {}
            for ident in owned.get("especializacoes", []):
                item = api.GUILD_CATALOG.get(ident) or {}
                line = item.get("linha")
                skill = next((sk for (c, sk), ln in api.HERO_SKILL_GUILD_LINES.items()
                              if c == cls and ln == line), None)
                skill = skill or {"bardo_cancao": "cancao_heroica",
                                  "bardo_provocacao": "provocacao", "mago_reviver": "animar_mortos"}.get(line)
                base = next((l for l in bases if l.get("classe") == cls
                             and ((l.get("tarefa") or {}).get("alvo") == skill
                                  or skill == "protetor" and (l.get("tarefa") or {}).get("tipo") == "proteger")), None) if skill else None
                if not base:
                    continue
                lesson = deepcopy(base)
                lesson.pop("guia", None)    # o guia da lição-base fala do exercício original
                # `habilidade:` só quando a skill é o alvo da tarefa (é o que o botão traz).
                alvo_base = (base.get("tarefa") or {}).get("alvo")
                lesson.update(id=f"treino_guild_{ident}", ordem=order,
                              requisitos={"guild": ident},
                              guia_modelo={"tipo": "guild", "id": ident,
                                           "skill": skill if alvo_base == skill else None},
                              texto=f"Você aprendeu {item.get('nome', ident)}. {item.get('desc', '')} "
                                    "Repita o exercício e observe os valores da sua nova habilidade.")
                order += 1
                if lesson["id"] not in added:
                    self.falas.append(lesson); self.licoes.append(lesson); added.add(lesson["id"])

        for p in self.players.values():
            cls = p.get("class_id")
            room = next((r for r in self.rooms if r.get("allowed_class") == cls), None)
            if not room:
                continue
            order = 200
            for mid in p.get("magias_conhecidas", []):
                if not self._training_spell_available(p, mid):
                    continue
                magic = api.GRIMORIO[mid]
                lesson = {"id": f"treino_magia_{cls}_{mid}", "classe": cls, "ordem": order,
                          "pos": [room["x"] + 1, room["y"] + 2],
                          "trigger": {"tipo": "sala"}, "falante": {"nome": "Instrutor Arcano", "emoji": "🔮"},
                          "texto": f"Pratique {magic.get('nome', mid)}. {magic.get('descricao', '')} "
                                   "Abra o Grimório e use a magia nos alvos de treino ou em você, conforme o tipo.",
                          "requisitos": {"magia": mid},
                          "guia_modelo": {"tipo": "magia", "id": mid},
                          "sala_exclusiva": True,
                          "tarefa": {"tipo": "usar_magia", "alvo": mid, "vezes": 1,
                                     "texto_curto": f"Pratique {magic.get('nome', mid)}"}}
                order += 1
                if lesson["id"] not in added:
                    self.falas.append(lesson); self.licoes.append(lesson); added.add(lesson["id"])

        for p in self.players.values():
            for lesson in self.licoes:
                if lesson.get("classe") == p.get("class_id") and lesson["id"] in p.get("tutorial_history", []):
                    if lesson["id"] not in p["licoes_feitas"]:
                        p["licoes_feitas"].append(lesson["id"])
                    p["licao_progresso"][lesson["id"]] = (lesson.get("tarefa") or {}).get("vezes", 1)
                    self.licoes_feitas.add(lesson["id"])

    async def _training_prepare(self, p, lesson):
        if not self.training_mode or not lesson.get("classe"):
            return
        room = self._room_containing_point(p["pos"])
        if not room or room.get("allowed_class") != p.get("class_id"):
            return
        api = self._tutorial_api()
        tar = lesson.get("tarefa") or {}
        aid = tar.get("alvo")
        if aid in ("detectar_armadilhas", "desarmar_armadilha") or tar.get("tipo") == "desarmar_armadilha":
            template = self.training_state.get("trap_template")
            if template and not any(a.get("id") == template["id"] for a in self.armadilhas):
                self.armadilhas.append(deepcopy(template))
            for trap in self.armadilhas:
                if trap.get("id") == "trap_treino_luccas":
                    trap.update(triggered=False, desarmada=False, esgotada=False,
                                visivel=aid != "detectar_armadilhas")
            if aid == "detectar_armadilhas":
                p["detectar_ativo"] = False
                p["status"] = [s for s in p.get("status", []) if s != "detect_trap"]
        # Uma reposição explícita antes do exercício evita esgotar o curso.
        p["fome"] = max(p.get("fome", 0), 80)
        p["sede"] = max(p.get("sede", 0), 80)
        allies = [a for a in self.training_allies.values() if a["allowed_class"] == p["class_id"]]
        if aid in ("cura", "cura_area"):
            for a in allies:
                a["hp"] = 5; a["alive"] = True
        if aid == "purificacao" and allies:
            a = allies[0]
            a["cego"] = True; a["cego_pen_ataque"] = 0
            a["bloqueia_distancia"] = True
        if aid == "ressurreicao" and allies:
            a = allies[0]; a["alive"] = False; a["hp"] = 0
            self.hero_corpses[a["id"]] = {"id": a["id"], "pos": list(a["pos"]),
                                            "class_id": a["class_id"], "name": a["name"]}
        if aid == "regeneracao_divina":
            p["hp"] = max(2, p["max_hp"] - 2)
        if tar.get("tipo") == "proteger":
            p["hp"] = max(2, p["hp"])
        if aid == "veneno_rapido":
            if not any(i.get("id") == "veneno_fungo_acre" for i in p.get("bag", [])):
                item = api.hidratar_itens_bau([{"id": "veneno_fungo_acre"}])[0]
                item["tutorial_loan"] = True
                if len(p["bag"]) < p.get("bag_size", 20):
                    p["bag"].append(item)
        if aid == "animar_mortos":
            ident = "treino_cadaver_mago"
            mdef = next(m for m in api.MONSTER_DEFS if m["type"] == "esqueleto_humano")
            self.corpses[ident] = {"id": ident, "pos": [room["x"] + 2, room["y"] + 2],
                                  "nome": "Esqueleto de treinamento", "tipo": mdef["type"],
                                  "icone": "💀", "nd": 0.25, "nivel": 1, "ca": 10,
                                  "vida_max": 8, "dano": "1d4", "ficha_original": deepcopy(mdef),
                                  "training_target": True}

    async def _training_event(self, p, kind, target=None, amount=0):
        """Condições de resultado usadas pelos exercícios, além dos eventos legados."""
        if not self.training_mode or not p:
            return
        lesson = next((l for l in self.licoes if l["id"] == p.get("licao_atual")), None)
        tar = (lesson or {}).get("tarefa") or {}
        if not lesson or not self._licao_no_lugar(p, lesson["pos"]):
            return
        aid = tar.get("alvo")
        if kind == "curar" and aid == "imposicao_maos":
            if target is not self.prisoner or amount <= 0 or not self.training_state.get("paladin", {}).get("protegido"):
                return
            await self._licao_evento(p, "usar_habilidade", alvo=aid, contexto={"alvo_id": "__prisioneiro__", "cura": amount})
        elif kind == "curar" and aid in ("cura", "cura_area"):
            if target and target.get("training_ally") and amount > 0:
                await self._licao_evento(p, "usar_habilidade", alvo=aid, contexto={"alvo_id": target["id"], "cura": amount})
        elif kind == "regenerou" and amount > 0:
            await self._licao_evento(p, "regenerar", alvo="regeneracao_divina")

    async def _training_end_turn(self, p):
        if not self.training_mode or not p:
            return
        lesson = next((l for l in self.licoes if l["id"] == p.get("licao_atual")), None)
        tar = (lesson or {}).get("tarefa") or {}
        if p.get("class_id") == "rogue" and tar.get("tipo") == "desarmar_armadilha":
            trap = next((a for a in self.armadilhas if a.get("id") == "trap_treino_luccas"), None)
            if not trap or trap.get("esgotada"):
                if trap:
                    self.armadilhas.remove(trap)
                await self._training_prepare(p, lesson)
        if tar.get("tipo") == "proteger" and self._licao_no_lugar(p, lesson["pos"]):
            pr = self.prisoner
            if (pr and pr.get("training_refem") and pr.get("alive") and pr.get("freed")
                    and p.get("protetor_ativo") and p.get("protetor_alvo") == "__prisioneiro__"
                    and self._no_raio(p, pr, self._defensor_raio(p))):
                pr["hp"] = max(pr["hp"], 7)
                before = (pr["hp"], p["hp"])
                await self._aplicar_dano_alvo(pr, 8, self._tutorial_api().DMG_PHYSICAL, None, is_attack=True)
                if pr.get("alive") and p.get("alive") and pr["hp"] < before[0]:
                    self.training_state.setdefault("paladin", {})["protegido"] = True
                    await self.gm_say(f"Treinamento: o refém recebeu {before[0] - pr['hp']} de dano; "
                                      f"Richard recebeu {before[1] - p['hp']} após sua redução. Agora cure o refém.")
                    await self._licao_evento(p, "proteger", alvo="__prisioneiro__")

    def _placa_em_evidencia(self, p):
        """{id, pos} da placa da sala do herói enquanto faltam lições de habilidade da classe.

        Lições de habilidade = as autoradas `treino_*` da classe (fora as geradas em jogo
        (`treino_guild_*`/`treino_magia_*`, geradas por compra/magia), as comuns `fala_*` e as pontes `porta_/volta_`),
        com requisitos cumpridos. Lição pulada já está em `licoes_feitas`, então conta como
        cumprida: a placa não fica acesa para sempre em quem abandonou a etapa."""
        if not getattr(self, "training_mode", False):
            return None
        cls = p.get("class_id")
        if not cls:
            return None
        feitas = p.get("licoes_feitas") or []
        faltam = any(l.get("classe") == cls and str(l["id"]).startswith("treino_")
                     and not str(l["id"]).startswith(("treino_guild_", "treino_magia_")) and l["id"] not in feitas
                     and self._training_requirements(p, l)
                     for l in self.licoes)
        if not faltam:
            return None
        placa = next((d for d in self.decorations if d.get("id") == "placa_" + cls), None)
        if not placa or not placa.get("pos"):
            return None
        return {"id": placa["id"], "pos": list(placa["pos"])}

    async def handle_repetir_tutorial(self, pid):
        p = self.players.get(pid)
        if not self.training_mode or not p or not self._is_turn(pid):
            return
        room = self._room_containing_point(p["pos"])
        if not room or room.get("allowed_class") != p.get("class_id"):
            return
        ids = {l["id"] for l in self.licoes if l.get("classe") == p["class_id"]
               and (l.get("sala_exclusiva") or _licao_fora_da_trilha(l))}
        p["licao_atual"] = None
        p["licoes_puladas"] = [i for i in p.get("licoes_puladas", []) if i not in ids]
        p["licoes_feitas"] = [i for i in p.get("licoes_feitas", []) if i not in ids]
        p["licao_progresso"] = {k:v for k,v in p.get("licao_progresso", {}).items() if k not in ids}
        self.licoes_feitas.difference_update(ids)
        self._training_devolver_emprestimos(p)
        self._training_recolocar_bau(p["class_id"])
        modelo = self.training_state.get("refem_modelo")
        if p["class_id"] == "paladin" and modelo and (self.prisoner is None or self.prisoner.get("training_refem")):
            self.prisoner = deepcopy(modelo)   # volta à casa de origem, inteiro
            self.prisioneiro_done = False
            p["protetor_ativo"] = False; p["protetor_alvo"] = None
            self.training_state.pop("paladin", None)
        await self._verificar_falas(p, room)
        await self.push_state()

    def _training_cleanup(self):
        if not self.training_mode:
            return
        for p in self.players.values():
            self._training_devolver_emprestimos(p)
            vid = self.training_state.get(p.get("class_id"), {}).get("loan_poison")
            if vid:
                self._set_weapon_poison_slots(p, [v for v in self._weapon_poison_slots(p) if v != vid])
            p["animados"] = [a for a in p.get("animados", []) if not a.get("training_target")]
        self.training_allies = {}; self.training_state = {}; self.training_mode = False
