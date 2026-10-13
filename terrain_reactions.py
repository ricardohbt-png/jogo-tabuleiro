"""Reações elementais (terreno × elemento).

Mixin de GameRoom. Cada fonte elementar diz "este elemento atingiu estas casas"
(`_rx_registrar`) dentro de um escopo por ação (`evento_elemental`); ao fim da
ação o escopo resolve cada linha de `REACOES` UMA vez sobre a união das casas
(é o dedupe por evento). Mudanças de terreno usam o registro de camadas
temporárias do Chamado do Inverno (`_aplicar_camadas_terreno_inverno`).

Spec: docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md
"""
import contextlib
import traceback

# Mesmos valores de server.DMG_FIRE / DMG_COLD / DMG_LIGHTNING (um teste confere).
RX_FIRE = "fire"
RX_COLD = "cold"
RX_LIGHTNING = "lightning"
RX_ELEMENTOS = (RX_FIRE, RX_COLD, RX_LIGHTNING)

RX_PROFUNDIDADE_MAX = 2
RX_CHOQUE_RAIO = 6
RX_CHOQUE_TETO = 24
RX_PICHE_TETO = 40
RX_DURACAO_GELO = 3
RX_DURACAO_CROSTA = 3
RX_CD_PADRAO = 12
RX_DURACAO_CHAMAS = 3
RX_DADO_CHAMAS = "1d6"

# Tabela de dados: elemento × estado da casa → efeito (nome do método).
# `efeito: None` + `ativa: False` = linha reservada (fogo + gelo, fora da v1).
REACOES = [
    {"id": "choque_na_poca",  "elemento": RX_LIGHTNING, "estado": "agua_rasa", "efeito": "_rx_choque",          "ativa": True},
    {"id": "incendiar_piche", "elemento": RX_FIRE,      "estado": "piche",     "efeito": "_rx_incendiar_piche", "ativa": True},
    {"id": "congelar_agua",   "elemento": RX_COLD,      "estado": "agua_rasa", "efeito": "_rx_congelar_agua",   "ativa": True},
    {"id": "crosta_de_lava",  "elemento": RX_COLD,      "estado": "lava",      "efeito": "_rx_crosta_lava",     "ativa": True},
    {"id": "derreter_gelo",   "elemento": RX_FIRE,      "estado": "gelo",      "efeito": None,                  "ativa": False},
]


class TerrainReactions:
    # ── escopo por ação ──────────────────────────────────────────────────────
    @contextlib.asynccontextmanager
    async def evento_elemental(self, origem):
        """Abre o escopo de uma ação; aninhado reaproveita o escopo aberto."""
        if self._rx_escopo is not None:
            yield self._rx_escopo
            return
        esc = {"origem": dict(origem or {}), "pend": {}}
        self._rx_escopo = esc
        try:
            yield esc
        finally:
            self._rx_escopo = None
        # Se o corpo lançar, esta linha não roda: ação abortada não reage (pendências descartadas).
        await self._rx_resolver(esc, 0)

    def _rx_origem_atual(self, **kw):
        if self._rx_escopo is not None:
            self._rx_escopo["origem"].update({k: v for k, v in kw.items() if v is not None})

    async def _rx_registrar(self, elemento, casas, *, dano=None, atingidos=(), origem=None):
        if self._rx_em_reacao or elemento not in RX_ELEMENTOS or not casas:
            return
        implicito = self._rx_escopo is None
        esc = self._rx_escopo if not implicito else {"origem": dict(origem or {}), "pend": {}}
        pend = esc["pend"].setdefault(elemento, {"casas": set(), "dano": 0, "atingidos": set()})
        pend["casas"].update((int(x), int(y)) for x, y in casas)
        if dano:
            pend["dano"] = max(pend["dano"], int(dano))
        pend["atingidos"].update(atingidos)
        if origem and not implicito:
            esc["origem"].update({k: v for k, v in origem.items() if v is not None})
        if implicito:
            await self._rx_resolver(esc, 0)

    async def _rx_registrar_alvo(self, alvo, elemento, dano, caster_id=None):
        """Atalho dos funis de dano: registra as casas da criatura atingida."""
        if elemento not in RX_ELEMENTOS or self._rx_em_reacao:
            return
        await self._rx_registrar(
            elemento, self._rx_tiles_da(alvo), dano=dano,
            atingidos={alvo.get("id")}, origem={"tipo": "dano", "caster_id": caster_id})

    # ── geometria e estado das casas ────────────────────────────────────────
    def _rx_tiles_da(self, criatura):
        pos = criatura.get("pos")
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            return []
        if self.monsters.get(criatura.get("id")) is criatura:
            return [(int(x), int(y)) for x, y in self._monster_tiles(criatura)]
        return [(int(pos[0]), int(pos[1]))]

    def _rx_tiles_area(self, cx, cy, raio=None, lado=None):
        """Casas de chão de uma área quadrada: `lado` explícito, ou o quadrado de
        raio Chebyshev `raio` (lado 2*raio+1, âncora simétrica)."""
        lado = int(lado) if lado else 2 * int(raio or 0) + 1
        return [(int(x), int(y)) for x, y in self._inverno_area_tiles(cx, cy, lado)]

    def _rx_estado(self, estado, tile):
        x, y = tile
        mat = self.materiais.get((x, y))
        if estado == "agua_rasa":
            return self._water_tile_kind(x, y) == "agua"
        if estado == "piche":
            return mat == "piche" and not self._ponte_em(x, y)
        if estado == "lava":
            return self._is_lava_tile(x, y)
        if estado == "gelo":
            return mat in {"piso_congelado", "planicie_nevada"}
        return False

    def _rx_regiao(self, sementes, pred, *, raio, teto):
        """Casas conectadas (4 vizinhos) que satisfazem `pred`, a partir das
        sementes, dentro de `raio` (Chebyshev, None = sem limite) e até `teto`."""
        sem = sorted({tuple(s) for s in sementes if pred(tuple(s))}, key=lambda t: (t[1], t[0]))
        vistos = list(sem)
        conj = set(sem)
        i = 0
        while i < len(vistos) and len(vistos) < teto:
            x, y = vistos[i]
            i += 1
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                n = (x + dx, y + dy)
                if n in conj or not pred(n):
                    continue
                if raio is not None and min(max(abs(n[0] - s[0]), abs(n[1] - s[1])) for s in sem) > raio:
                    continue
                conj.add(n)
                vistos.append(n)
                if len(vistos) >= teto:
                    break
        return vistos[:teto]

    # ── resolução ───────────────────────────────────────────────────────────
    async def _rx_resolver(self, esc, profundidade):
        if profundidade > RX_PROFUNDIDADE_MAX:
            return
        antes = self._rx_em_reacao
        self._rx_em_reacao = True
        try:
            for elemento in sorted(esc["pend"]):
                pend = esc["pend"][elemento]
                casas = sorted(pend["casas"], key=lambda t: (t[1], t[0]))
                for linha in REACOES:
                    if not linha["ativa"] or not linha["efeito"] or linha["elemento"] != elemento:
                        continue
                    alvo_casas = [t for t in casas if self._rx_estado(linha["estado"], t)]
                    if not alvo_casas:
                        continue
                    try:
                        await getattr(self, linha["efeito"])(alvo_casas, esc["origem"], pend, profundidade)
                    except Exception:  # uma reação com defeito não aborta a ação já aplicada
                        traceback.print_exc()
        finally:
            self._rx_em_reacao = antes

    async def _rx_encadear(self, elemento, casas, esc, profundidade):
        """Uma reação que dispara outra: novo escopo, profundidade + 1."""
        filho = {"origem": dict(esc.get("origem", {})),
                 "pend": {elemento: {"casas": {tuple(c) for c in casas}, "dano": 0, "atingidos": set()}}}
        await self._rx_resolver(filho, profundidade + 1)

    def _rx_id(self, tipo):
        self._rx_seq += 1
        return f"rx_{tipo}_{self.round_num}_{self._rx_seq}"

    async def _rx_anunciar(self, tipo, casas, origem_pos):
        await self.broadcast({"type": "reacao_elemental", "tipo": tipo,
                              "casas": [list(c) for c in casas], "origem": list(origem_pos)})

    # ── efeitos ─────────────────────────────────────────────────────────────
    async def _rx_choque(self, tiles, origem, pend, prof):
        regiao = self._rx_regiao(tiles, lambda t: self._rx_estado("agua_rasa", t),
                                 raio=RX_CHOQUE_RAIO, teto=RX_CHOQUE_TETO)
        await self._rx_anunciar("choque", regiao, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.choque"))
        base = int(pend.get("dano") or origem.get("dano") or 0)
        if base <= 0:
            return
        cd = int(origem.get("cd") or RX_CD_PADRAO)
        for alvo in self._alvos_no_inverno(regiao):
            if alvo.get("id") in pend["atingidos"] or self._voo_imune_terreno(alvo):
                continue
            ok, *_ = await self._save_mostrado(alvo, "reflexos", cd, mitigacao="half_damage")
            d = max(1, base // 2)
            if ok:
                d = max(1, d // 2)
            if "vida_atual" not in alvo:
                d = self._apply_damage_types(d, [RX_LIGHTNING], alvo)
            if d > 0:
                await self._dano_em_alvo(alvo, d, "eletricidade", origem.get("caster_id"))

    async def _rx_congelar_agua(self, tiles, origem, pend, prof):
        zid = self._rx_id("gelo")
        self._aplicar_camadas_terreno_inverno(
            tiles, "piso_congelado", zid, permanente=False,
            expira_em=self.round_num + RX_DURACAO_GELO)
        await self._rx_anunciar("congelar", tiles, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.congelar"))
        cd = int(origem.get("cd") or RX_CD_PADRAO)
        for alvo in self._alvos_no_inverno(tiles):
            if self._voo_imune_terreno(alvo):
                continue
            ok, *_ = await self._save_mostrado(alvo, "reflexos", cd)
            if not ok:
                alvo["moves_left"] = 0
                alvo["movimento_perdido"] = True

    async def _rx_crosta_lava(self, tiles, origem, pend, prof):
        zid = self._rx_id("crosta")
        self._aplicar_camadas_terreno_inverno(
            tiles, "lava_solidificada", zid, permanente=False,
            expira_em=self.round_num + RX_DURACAO_CROSTA)
        await self._rx_anunciar("crosta", tiles, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.crosta"))

    # ── piche em chamas ─────────────────────────────────────────────────────
    def _rx_em_zona_chamas(self, tile):
        for z in self.zonas_especiais:
            if z.get("tipo") == "chamas_piche" and z.get("ativa") \
                    and any((int(a), int(b)) == tile for a, b in z.get("tiles", [])):
                return True
        return False

    def _rx_alvo_na_zona(self, alvo, zona):
        area = {(int(a), int(b)) for a, b in zona.get("tiles", [])}
        return any(t in area for t in self._rx_tiles_da(alvo))

    async def _rx_incendiar_piche(self, tiles, origem, pend, prof):
        regiao = self._rx_regiao(
            tiles, lambda t: self._rx_estado("piche", t) and not self._rx_em_zona_chamas(t),
            raio=None, teto=RX_PICHE_TETO)
        if not regiao:
            return
        zona = {"id": self._rx_id("chamas_piche"), "tipo": "chamas_piche",
                "tiles": [list(t) for t in regiao], "criado_em": self.round_num,
                "expira_em": self.round_num + RX_DURACAO_CHAMAS, "ativa": True,
                "caster": origem.get("caster_id")}
        self.zonas_especiais.append(zona)
        await self._rx_anunciar("incendio", regiao, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.piche_pegou_fogo"))
        for alvo in self._alvos_no_inverno(regiao):
            await self._rx_fogo_piche(alvo, zona, "ignição")

    async def _rx_fogo_piche(self, alvo, zona, motivo):
        """1d6 de fogo + em chamas, só no piso. Não reentra no motor."""
        if not self._vivo(alvo) or self._voo_imune_terreno(alvo):
            return
        if self._rx_altura(alvo) > 0:
            return
        antes = self._rx_em_reacao
        self._rx_em_reacao = True
        try:
            raw = self._rolar_dado(RX_DADO_CHAMAS)
            await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw,
                                  "label": self._rx_T("dado.chamas_de_piche"),
                                  "damage_type": RX_FIRE})
            dano = raw if "vida_atual" in alvo else self._apply_damage_types(raw, [RX_FIRE], alvo)
            await self._dano_em_alvo(alvo, dano, "fogo", zona.get("caster"))
            if self._vivo(alvo):
                self._aplicar_em_chamas(alvo, self._rolar_dado("1d4"), True)
        finally:
            self._rx_em_reacao = antes

    def _consumir_piche(self, tiles):
        """O fogo consumiu o piche: mancha temporária volta ao material original;
        piche pintado no editor (base == piche) vira pedra_negra."""
        for t in (tuple(x) for x in tiles):
            reg = self._terrenos_inverno.get(t)
            if reg:
                reg["camadas"] = [c for c in reg.get("camadas", []) if c.get("material") != "piche"]
                if reg["camadas"]:
                    self.materiais[t] = reg["camadas"][-1]["material"]
                else:
                    base = reg.get("base")
                    novo = "pedra_negra" if base == "piche" else base
                    if novo is None:
                        self.materiais.pop(t, None)
                    else:
                        self.materiais[t] = novo
                    self._terrenos_inverno.pop(t, None)
            elif self.materiais.get(t) == "piche":
                self.materiais[t] = "pedra_negra"
        self._rebuild_materiais_index()
