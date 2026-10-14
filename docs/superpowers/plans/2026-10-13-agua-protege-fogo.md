# Água protege do fogo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quem está na água sofre metade do dano de fogo e não pega fogo; quem está em chamas e entra na água é apagado; Fogo Grego ignora tudo.

**Architecture:** Dois predicados derivados da posição/material (`_agua_protege`, no mixin `TerrainReactions`) alimentam três pontos já existentes do servidor: o funil `_apply_damage_types` (resistência de metade injetada), `_aplicar_em_chamas` (bloqueia o status) e o gancho de movimento/tick que apaga as chamas. O Fogo Grego é uma exceção por escopo (`_fogo_ignora_agua`) e pela flag `chamas_agua_apaga` do próprio alvo. Cliente: só o tooltip da casa.

**Tech Stack:** Python (server.py + terrain_reactions.py), JS vanilla (src/reacoesElementais.js, src/lang/interface.js, src/lang/narracao.js), testes em `tools/`.

**Spec:** `docs/superpowers/specs/2026-10-13-agua-protege-fogo-design.md`

## Global Constraints

- `server.py`, `game.js`, `src/lang/*.js` e `CLAUDE.md` são **CRLF**: edite com a ferramenta Edit (ou script byte-exato) e confirme com Python que `data.count(b'\n') == data.count(b'\r\n')`. `terrain_reactions.py` e o spec são LF/CRLF conforme o git (não converta à mão).
- Trailer de commit: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commits só com caminhos explícitos. Sem push/merge.
- Nunca tocar `C:/Users/RICARDO/Desktop/jogo tabuleiro` (checkout do autor com trabalho em andamento), `savegames/`, `accounts/`, `groups/`, nem a porta 8765.
- `GS.on` substitui o ouvinte anterior: não adicionar `GS.on` de evento já usado.
- Falhas conhecidas do `master`, **não atribuíveis a esta branch**: `test_salvar_masmorra` [2] (atributos `cooperative_*`), `test_interface` (1 literal em `abrirMenuHabilidades`), `dividas.py` total 1, `test_editor_idioma` ("editor.js (3)"), `test_vocabulario` [12], `test_sons_cliente` (2).
- Textos novos em pt e en; chaves `narracao.*` em `src/lang/narracao.js`, `ui.reacao.*` em `src/lang/interface.js` (paridade de `{parâmetros}` pt/en é testada).
- Regra de água do spec: "na água" = **todas** as casas do footprint são `agua`, `agua_profunda`, `rodamoinho` ou `rodamoinho_profundo` e sem ponte (`_water_tile_kind`); voador acima do chão (`_voo_imune_terreno`) nunca conta; pântano conta só para imunidade/apagar chamas, nunca para a metade do dano.

## Review Focus

- Monstro 2×2 com **uma** casa fora da água não tem proteção nenhuma (nem metade, nem imunidade) — teste na Task 1.
- Criatura com resistência a fogo já existente na água: quarto do dano; com imunidade a fogo: 0 (nunca negativo) — Task 1.
- Dano de fogo que **mata** ou dano 0/1 não pode estourar (`max(0, …)`, arredondamento `(n+1)//2` do funil) — Task 1.
- Entrar na água em chamas apaga **uma vez** e não narra de novo no tick seguinte; sair da água não reacende — Task 1.
- Fogo Grego: pega e queima na água, dano cheio no impacto e no tick, e a flag `chamas_agua_apaga=False` não vaza para o próximo arremesso comum (escopo desligado em `finally`, inclusive com exceção) — Task 1.
- Servo animado (`vida_atual`, dano pelo `_ajustar_dano_elemental` fora de `_apply_damage_types`): a regra **não** o cobre nesses caminhos; documentado em teste/CLAUDE.md, não um defeito escondido — Task 3.

---

### Task 1: Motor — predicado, metade do dano, imunidade, apagar, Fogo Grego

**Files:**
- Modify: `terrain_reactions.py` (predicado `_agua_protege`, constante `RX_AGUA_MATERIAIS`)
- Modify: `server.py` (`_apply_damage_types` ~39555–39700; `_aplicar_em_chamas` ~37047; novo `_apagar_chamas_na_agua` ao lado dele; `_aplicar_lava_se_pisar` ~34742; `_processar_em_chamas_turno` ~37455; wrappers de `_throw_item_alvo` ~20901, `_throw_item_area` ~21004, `_monster_throw_item` ~42503; os 4 sítios que narram "pega fogo" ~20984, ~21071, ~42533, ~42578)
- Modify: `src/lang/narracao.js` (chave `narracao.chamas_apagadas_na_agua`)
- Create: `tools/test_agua_protege_fogo.py`

**Interfaces:**
- Produces: `GameRoom._agua_protege(criatura, *, pantano=False) -> bool`; `GameRoom._aplicar_em_chamas(alvo, rodadas, agua_apaga) -> bool` (True se aplicou); `async GameRoom._apagar_chamas_na_agua(criatura) -> bool`; atributo `GameRoom._fogo_ignora_agua: bool` (padrão `False`) e `@contextmanager GameRoom._escopo_fogo_grego(defn)`.
- Consumes: `self._rx_tiles_da(criatura)`, `self._water_tile_kind(x, y)`, `self._ponte_em(x, y)`, `self._voo_imune_terreno(criatura)`, `DMG_FIRE`, `nome_criatura`, `T`.

- [ ] **Step 1: Escrever os testes que falham** — crie `tools/test_agua_protege_fogo.py` reaproveitando os helpers do `tools/test_terrain_reactions.py` (copie `check`, `sala`, `heroi`, `monstro`, `pinta`, `roda` literalmente do topo daquele arquivo, mudando o docstring e o código da sala para `"AGUAFOGO"`). Depois os casos, cada um com `check(...)`:

```python
print("[1] metade do dano de fogo")
r = sala()
h = heroi(r, "h1", "Ana", "mage", (5, 5))
check("fora da água: dano cheio", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
pinta(r, "agua", [(5, 5)])
check("na água rasa: metade", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
check("na água: dano 1 não vira 0", r._apply_damage_types(1, [S.DMG_FIRE], h) >= 1)
check("na água: outro elemento intacto", r._apply_damage_types(8, [S.DMG_COLD], h) == 8)
for mat in ("agua_profunda", "rodamoinho", "rodamoinho_profundo"):
    pinta(r, mat, [(5, 5)])
    check(f"{mat} conta", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
pinta(r, "pantano", [(5, 5)])
check("pântano NÃO dá metade do dano", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
pinta(r, "agua", [(5, 5)])
h["altura"] = 3; h["voo"] = True
check("voador não conta", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
h["altura"] = 0; h["voo"] = False

print("[2] footprint e soma com resistências")
r = sala()
grande = None
for d in S.MONSTER_DEFS:
    m = monstro(r, d["type"], (6, 6))
    if len(r._monster_tiles(m)) == 4:
        grande = m; break
    del r.monsters[m["id"]]
check("existe monstro 2x2 para o teste", grande is not None)
tiles = r._monster_tiles(grande)
pinta(r, "agua", tiles[:3])
check("2x2 com uma casa fora: sem proteção", r._apply_damage_types(8, [S.DMG_FIRE], grande) == 8)
pinta(r, "agua", tiles)
check("2x2 todo na água: metade", r._apply_damage_types(8, [S.DMG_FIRE], grande) == 4)
g2 = S.make_player("h2", "Bia", "warrior", 1); g2["pos"] = [9, 9]; r.players["h2"] = g2
pinta(r, "agua", [(9, 9)])
g2["resistances"] = [{"type": S.DMG_FIRE, "mode": "half"}]
check("resistência existente + água = quarto", r._apply_damage_types(8, [S.DMG_FIRE], g2) == 2)
g2["resistances"] = []; g2["immunities"] = [S.DMG_FIRE]
check("imune a fogo na água segue 0", r._apply_damage_types(8, [S.DMG_FIRE], g2) == 0)
```

```python
print("[3] imunidade a pegar fogo")
r = sala()
h = heroi(r, "h1", "Ana", "warrior", (5, 5))
check("fora da água: pega fogo", r._aplicar_em_chamas(h, 3, True) is True and h["em_chamas_rodadas"] == 3)
h["em_chamas_rodadas"] = 0
pinta(r, "agua", [(5, 5)])
check("na água: não pega fogo", r._aplicar_em_chamas(h, 3, True) is False and h.get("em_chamas_rodadas", 0) == 0)
pinta(r, "pantano", [(5, 5)])
check("no pântano: não pega fogo", r._aplicar_em_chamas(h, 3, True) is False)
pinta(r, "agua", [(5, 5)])
check("Fogo Grego pega mesmo na água", r._aplicar_em_chamas(h, 3, False) is True and h["em_chamas_rodadas"] == 3)

print("[4] água apaga")
r = sala()
h = heroi(r, "h1", "Ana", "warrior", (5, 5))
pinta(r, "agua", [(6, 5)])
h["em_chamas_rodadas"] = 3; h["chamas_agua_apaga"] = True
roda(r._apagar_chamas_na_agua(h))
check("fora da água não apaga", h["em_chamas_rodadas"] == 3)
h["pos"] = [6, 5]
roda(r._aplicar_lava_se_pisar(h))
check("passo na água apaga (gancho de movimento)", h["em_chamas_rodadas"] == 0)
check("narra o apagar", any("água" in n.lower() or "water" in n.lower() for n in r.narr))
n0 = len(r.narr)
roda(r._aplicar_lava_se_pisar(h))
check("não narra de novo", len(r.narr) == n0)
h["em_chamas_rodadas"] = 3
roda(r._processar_em_chamas_turno())
check("rede de segurança no tick apaga sem dano", h["em_chamas_rodadas"] == 0 and h["hp"] == h["max_hp"])
h["pos"] = [5, 5]
check("sair da água não reacende", h["em_chamas_rodadas"] == 0)
h["pos"] = [6, 5]; h["em_chamas_rodadas"] = 3; h["chamas_agua_apaga"] = False
roda(r._aplicar_lava_se_pisar(h))
check("Fogo Grego não é apagado pela água", h["em_chamas_rodadas"] == 3)

print("[5] Fogo Grego: dano cheio e escopo")
r = sala()
h = heroi(r, "h1", "Ana", "warrior", (5, 5))
pinta(r, "agua", [(5, 5)])
with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
    check("escopo ligado: dano cheio", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)
check("escopo desligado ao sair", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
try:
    with r._escopo_fogo_grego({"chamas_agua_apaga": False}):
        raise RuntimeError("x")
except RuntimeError:
    pass
check("escopo desligado após exceção", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
with r._escopo_fogo_grego({"chamas_agua_apaga": True}):
    check("óleo comum não liga o escopo", r._apply_damage_types(8, [S.DMG_FIRE], h) == 4)
h["em_chamas_rodadas"] = 2; h["chamas_agua_apaga"] = False
check("tick de Fogo Grego em chamas: dano cheio", r._apply_damage_types(8, [S.DMG_FIRE], h) == 8)

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
```

Acrescente também, antes do rodapé, o teste ponta a ponta do arremesso com o handler real: herói com `fogo_grego` (e outro com `frasco_oleo`) arremessando em goblin na água via `r._throw_item_alvo(p, S.ARREMESSAVEIS[id], item, goblin["id"])` com `S.roll_d20`/dados fixados se o teste de acerto atrapalhar (patche `S.random.randint`/o rolador usado em `_throw_item_alvo` para forçar acerto): óleo → goblin na água **não** fica em chamas e leva ≈ metade; fogo grego → fica em chamas e leva o dano cheio. Se forçar o acerto exigir mais que patchar o d20, compare `_apply_damage_types` dentro do escopo como acima e registre isso no relatório.

- [ ] **Step 2: Rodar e ver falhar** — `python -X utf8 tools/test_agua_protege_fogo.py`. Esperado: falhas (métodos inexistentes / valores cheios).

- [ ] **Step 3: Predicado em `terrain_reactions.py`** — acrescente à seção "geometria e estado das casas" (logo após `_rx_estado`):

```python
    def _agua_protege(self, criatura, *, pantano=False):
        """True se TODAS as casas do footprint são água (ou, com `pantano`, também
        pântano) e a criatura não voa acima do chão. Derivado de posição/material:
        nenhum estado novo, nada a persistir."""
        if not criatura or self._voo_imune_terreno(criatura):
            return False
        tiles = self._rx_tiles_da(criatura)
        if not tiles:
            return False
        for x, y in tiles:
            if self._water_tile_kind(x, y):
                continue
            if pantano and not self._ponte_em(x, y) and self.materiais.get((x, y)) == "pantano":
                continue
            return False
        return True
```

- [ ] **Step 4: Metade do dano em `_apply_damage_types`** — antes do laço `for resistance in target.get("resistances", []):` crie a lista efetiva e troque o laço para iterá-la:

```python
        resistencias = list(target.get("resistances", []))
        if (DMG_FIRE in damage_types and not getattr(self, "_fogo_ignora_agua", False)
                and not (target.get("em_chamas_rodadas", 0) > 0
                         and not target.get("chamas_agua_apaga", True))
                and self._agua_protege(target)):
            resistencias.append({"type": DMG_FIRE, "mode": "half"})
        for resistance in resistencias:
```
Confirme com grep que `target.get("resistances"` não é lido de outra forma dentro da função. Inicialize `self._fogo_ignora_agua = False` em `GameRoom.__init__` e registre-o como `"efemero"` em `FOTO_SALA_CATEGORIAS` (o `test_salvar_masmorra` [2] varre atributos sem categoria).

- [ ] **Step 5: Imunidade + apagar + escopo em `server.py`** — substitua `_aplicar_em_chamas` e acrescente os helpers logo depois (use `from contextlib import contextmanager` se ainda não importado):

```python
    def _aplicar_em_chamas(self, alvo, rodadas, agua_apaga):
        """... (docstring atual) ... Devolve False quando a água/pântano impede."""
        if agua_apaga and self._agua_protege(alvo, pantano=True):
            return False
        atual = alvo.get("em_chamas_rodadas", 0)
        alvo["em_chamas_rodadas"] = max(atual, int(rodadas))
        alvo["chamas_agua_apaga"] = bool(agua_apaga)
        return True

    async def _apagar_chamas_na_agua(self, criatura):
        """Zera as chamas apagáveis de quem está na água/pântano. True se apagou."""
        if (not criatura or criatura.get("em_chamas_rodadas", 0) <= 0
                or not criatura.get("chamas_agua_apaga", True)
                or not self._agua_protege(criatura, pantano=True)):
            return False
        criatura["em_chamas_rodadas"] = 0
        await self.gm_say(T("narracao.chamas_apagadas_na_agua", nome=nome_criatura(criatura)))
        return True

    @contextmanager
    def _escopo_fogo_grego(self, defn):
        """Liga `_fogo_ignora_agua` enquanto o dano de um item com chamas não
        apagáveis (Fogo Grego) é aplicado; sempre desliga, mesmo com exceção."""
        ligar = bool(defn) and defn.get("chamas_agua_apaga", True) is False
        antes = self._fogo_ignora_agua
        if ligar:
            self._fogo_ignora_agua = True
        try:
            yield
        finally:
            self._fogo_ignora_agua = antes
```
Nos 4 sítios que fazem `self._aplicar_em_chamas(...)` seguido de narração "pega fogo" (~20984, ~21071, ~42578; o de ~42533 não narra), use o retorno: `if self._aplicar_em_chamas(...): await self.gm_say(...)` (mantendo o resto igual). Em `_aplicar_lava_se_pisar`, logo depois do `return` do voo e **antes** do gancho do piche, acrescente `await self._apagar_chamas_na_agua(criatura)`. Em `_processar_em_chamas_turno`, depois da checagem de vivo e antes de `_aguardar_decisao_chamas`: `if await self._apagar_chamas_na_agua(alvo): continue`.

- [ ] **Step 6: Wrappers do escopo nos arremessos** — renomeie `_throw_item_alvo`, `_throw_item_area` e `_monster_throw_item` para `*_impl` (mesma assinatura, corpo intocado) e crie, com os nomes originais:

```python
    async def _throw_item_alvo(self, p, defn, item, target_id, target_pos=None, source_location=None):
        with self._escopo_fogo_grego(defn):
            return await self._throw_item_alvo_impl(p, defn, item, target_id, target_pos, source_location)

    async def _throw_item_area(self, p, defn, item, tx, ty, source_location=None):
        with self._escopo_fogo_grego(defn):
            return await self._throw_item_area_impl(p, defn, item, tx, ty, source_location)

    async def _monster_throw_item(self, m, target_obj, item):
        with self._escopo_fogo_grego(ARREMESSAVEIS.get((item or {}).get("id"))):
            return await self._monster_throw_item_impl(m, target_obj, item)
```
Confirme com grep que nenhum teste ou código chama os nomes `_impl` e que nenhum `patch` de `_throw_item_*` quebra (rode a bateria de arremessáveis: `tools/test_arremessaveis*.py`, `test_projeteis.py`, `test_editor_itens.py`).

- [ ] **Step 7: Narração** — em `src/lang/narracao.js` (CRLF; siga o formato das chaves vizinhas) acrescente:

```js
  "narracao.chamas_apagadas_na_agua": {
    "pt": "🌊 {nome} mergulha na água e as chamas se apagam.",
    "en": "🌊 {nome} plunges into the water and the flames go out."
  },
```

- [ ] **Step 8: Rodar** — `python -X utf8 tools/test_agua_protege_fogo.py` (todos ok) e as regressões: `tools/test_terrain_reactions.py`, `test_arremessaveis*.py`, `test_projeteis.py`, `test_prisao_chamas.py`, `test_ira_rocha_ardente.py`, `test_monster_intent.py`, `test_idioma.py`, `test_salvar_masmorra.py` (só as falhas conhecidas), `test_protocolo_robustez.py`.

- [ ] **Step 9: Commit**

```bash
git add terrain_reactions.py server.py src/lang/narracao.js tools/test_agua_protege_fogo.py
git commit -m "feat: água protege do fogo (metade do dano, sem chamas, apaga)"
```

---

### Task 2: Cliente — tooltip das casas de água e pântano

**Files:**
- Modify: `src/reacoesElementais.js` (`descreverCasa`)
- Modify: `src/lang/interface.js` (chaves `ui.reacao.casa.*`)
- Test: `tools/test_reacoes_cliente.js`

**Interfaces:**
- Consumes: `descreverCasa(state, x, y) -> {chave, params} | null` (existente); materiais `agua`, `agua_profunda`, `rodamoinho`, `rodamoinho_profundo`, `pantano`.
- Produces: chaves `ui.reacao.casa.agua` (atualizada), `ui.reacao.casa.agua_fogo` (profunda/redemoinho), `ui.reacao.casa.pantano`.

- [ ] **Step 1: Testes que falham** — em `tools/test_reacoes_cliente.js`, junto dos checks de `descreverCasa`:

```js
check("água rasa: conduz e protege", RE.descreverCasa(st2, 2, 1).chave === "ui.reacao.casa.agua");
const stW = { materiais: { "1,1": "agua_profunda", "2,1": "rodamoinho", "3,1": "rodamoinho_profundo", "4,1": "pantano" }, round: 1 };
check("água profunda -> agua_fogo", RE.descreverCasa(stW, 1, 1).chave === "ui.reacao.casa.agua_fogo");
check("redemoinho -> agua_fogo", RE.descreverCasa(stW, 2, 1).chave === "ui.reacao.casa.agua_fogo");
check("redemoinho profundo -> agua_fogo", RE.descreverCasa(stW, 3, 1).chave === "ui.reacao.casa.agua_fogo");
check("pântano -> pantano", RE.descreverCasa(stW, 4, 1).chave === "ui.reacao.casa.pantano");
```
Acrescente um check que as 3 chaves existem com `pt` e `en` e que o `pt` de `agua` menciona fogo (`/fogo/i`) e o de `pantano` menciona chamas. Siga o estilo de carga dos dicionários que o arquivo já usa.

- [ ] **Step 2: Rodar e ver falhar** — `node tools/test_reacoes_cliente.js`.

- [ ] **Step 3: Implementar** — em `descreverCasa`, depois do ramo `agua`:

```js
    if (mat === 'agua_profunda' || mat === 'rodamoinho' || mat === 'rodamoinho_profundo')
      return { chave: 'ui.reacao.casa.agua_fogo', params: {} };
    if (mat === 'pantano') return { chave: 'ui.reacao.casa.pantano', params: {} };
```
Em `src/lang/interface.js` (CRLF) atualize e acrescente:

```js
  "ui.reacao.casa.agua": {
    "en": "Water: conducts electricity; halves fire damage and prevents burning",
    "pt": "Água: conduz eletricidade; metade do dano de fogo e não pega fogo"
  },
  "ui.reacao.casa.agua_fogo": {
    "en": "Water: halves fire damage and prevents burning",
    "pt": "Água: metade do dano de fogo e não pega fogo"
  },
  "ui.reacao.casa.pantano": {
    "en": "Swamp: prevents burning",
    "pt": "Pântano: não pega fogo"
  },
```

- [ ] **Step 4: Rodar** — `node tools/test_reacoes_cliente.js`, `python -X utf8 tools/test_interface.py`, `python -X utf8 tools/test_idioma.py`, `node tools/test_idioma_cliente.js`, `node --check game.js`. `test_interface`: só a falha conhecida.

- [ ] **Step 5: Commit**

```bash
git add src/reacoesElementais.js src/lang/interface.js tools/test_reacoes_cliente.js
git commit -m "feat: tooltip da água e do pântano descreve a proteção contra fogo"
```

---

### Task 3: Documentação e bateria final

**Files:**
- Modify: `CLAUDE.md` (acrescentar ao bloco "Reações elementais (2026-10-13)" um parágrafo "Água protege do fogo"), `docs/superpowers/specs/2026-10-13-agua-protege-fogo-design.md` (somente se algo diferiu)
- Test: bateria

- [ ] **Step 1: CLAUDE.md** (CRLF; Edit) — ~8 linhas em português logo depois do bloco das reações: regra (`_agua_protege`, footprint inteiro, voo, pântano só status); os três pontos (`_apply_damage_types` resistência de metade injetada; `_aplicar_em_chamas` devolve bool; `_apagar_chamas_na_agua` no gancho `_aplicar_lava_se_pisar` e no tick); Fogo Grego (`_escopo_fogo_grego` nos wrappers `_throw_item_*`/`_monster_throw_item`, flag do alvo no tick); **limite conhecido:** servo animado (`vida_atual`) toma dano de fogo por `_ajustar_dano_elemental` fora de `_apply_damage_types`, então não recebe a metade nesses caminhos; fora de escopo: IA preferir água; testes `tools/test_agua_protege_fogo.py` e `tools/test_reacoes_cliente.js`.

- [ ] **Step 2: Bateria** (registre comandos e resultados): `python -X utf8 tools/test_agua_protege_fogo.py`; `python -X utf8 tools/test_terrain_reactions.py`; `node tools/test_reacoes_cliente.js`; `python -X utf8 tools/test_monster_intent.py`; `node tools/test_intencoes_cliente.js`; `python -X utf8 tools/test_perseguicao.py`; `python -X utf8 tools/test_modo_mestre.py`; `python -X utf8 tools/test_handler_smoke.py`; `python -X utf8 tools/test_chamado_inverno.py`; `python -X utf8 tools/test_ira_rocha_ardente.py`; `python -X utf8 tools/test_prisao_chamas.py`; `python -X utf8 tools/test_senhor_das_aguas.py`; `python -X utf8 tools/test_tempestade_correcoes.py`; `python -X utf8 tools/test_salvar_masmorra.py`; `python -X utf8 tools/test_interface.py`; `python -X utf8 tools/dividas.py`; `python -X utf8 tools/test_idioma.py`; `node tools/test_idioma_cliente.js`; `python -X utf8 tools/test_protocolo_robustez.py`; `python -X utf8 tools/test_editor_itens.py`; `python -X utf8 tools/test_projeteis.py`; `node --check game.js`. Qualquer falha fora da lista de conhecidas: determine se a branch a causou e corrija.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md docs/superpowers/specs/2026-10-13-agua-protege-fogo-design.md
git commit -m "docs: documenta a proteção da água contra fogo"
```

(A prova no navegador, em servidor isolado e depois da última correção — fogo em quem está na água, entrar na água em chamas, Fogo Grego — fica a cargo do controlador.)

---

## Self-Review

- **Cobertura do spec:** regras "na água"/pântano/voo → `_agua_protege` (Task 1 Step 3); metade do dano → Step 4; imunidade a pegar fogo → Step 5 (`_aplicar_em_chamas`); água apaga (passo + tick) → Step 5; Fogo Grego (dano e status, escopo) → Steps 5–6; interações/persistência (nada novo, `_fogo_ignora_agua` efêmero) → Step 4; cliente → Task 2; testes → Task 1 Step 1 e Task 2; fora de escopo e limite do servo → Task 3.
- **Nomes consistentes:** `_agua_protege`, `_apagar_chamas_na_agua`, `_escopo_fogo_grego`, `_fogo_ignora_agua`, `_aplicar_em_chamas` (bool), `narracao.chamas_apagadas_na_agua`, `ui.reacao.casa.{agua,agua_fogo,pantano}` — iguais em todas as tarefas.
- **Riscos abertos para o implementador:** a assinatura real e os chamadores dos wrappers (`_throw_item_*`); se `target.get("resistances")` é lido fora do laço; como forçar acerto no teste de arremesso; confirmar se `contextmanager` já está importado; CRLF dos arquivos editados.
