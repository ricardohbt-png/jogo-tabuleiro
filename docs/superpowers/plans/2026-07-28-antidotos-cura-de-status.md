# Antídotos e curas de status — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Três consumíveis que curam um status (veneno / petrificação / doença) e concedem imunidade temporária a ele, usáveis em si ou em aliado adjacente, e autoráveis na sub-aba Poções.

**Architecture:** A lógica de cura já existe presa dentro de `handle_purificacao` — é extraída para helpers reusáveis. Uma imunidade temporária genérica (`imunidades_status[status] = round_num + N`) é checada em 4 pontos (as fontes reais de cada status). Três efeitos novos de consumível em `handle_use_item`, com `target_id` opcional no protocolo; no cliente, a decisão de mira mora dentro de `useItem`, então o modal de inventário não muda.

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`game.js`, `tools/editor_items_*.js`), testes: `python tools/test_editor_itens.py`, `python tools/test_clerigo_espec.py`, `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de commit (WIP do usuário) — LER ANTES DE QUALQUER COMMIT

O usuário reworka `server.py`, `game.js` e `src/gameState.js` em paralelo. **NUNCA** `git add` nesses arquivos, nem `git add -A`.

**Método que funcionou melhor (use este):** em vez de extrair hunks (que varrem o WIP quase sempre), gere o conteúdo desejado aplicando suas mudanças sobre o **conteúdo do HEAD** e prepare o blob no índice:

```bash
SP=<scratchpad>
git show HEAD:server.py > "$SP/head.py"
# script Python com substituições EXATAS (falha alto se o alvo não for único):
python "$SP/stage.py" "$SP/head.py" "$SP/want.py"
python -c "import ast,io; ast.parse(io.open(r'<SP>/want.py',encoding='utf-8').read()); print('sintaxe OK')"
BLOB=$(git hash-object -w "$SP/want.py")
git update-index --cacheinfo 100644,$BLOB,server.py
git diff --cached -- server.py          # confira: só o seu código
git diff --cached -- server.py | grep -cE "city_shop|_slot_prune|_restaurar_sobrevivencia"   # deve ser 0
```

O script de substituição deve usar uma função que **conte as ocorrências e aborte se ≠ 1** — isso pega alvo ambíguo antes de corromper o arquivo. Arquivos fora do WIP (`tools/test_*.py`, `tools/editor_items_*.js`) vão por `git add` normal.

## ⚠️ A suíte aborta no working tree (pré-existente)

`python tools/test_editor_itens.py` CRASHA na seção `[7]` (WIP de lojas por cidade). **Não é seu.** Verifique via import direto:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location('t','tools/test_editor_itens.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.test_curar_status_helpers()
print(f'{m.PASS} passaram, {m.FAIL} falharam')
"
```

---

## File Structure

- **Modify:** `server.py` — helpers de cura extraídos; imunidade genérica + 4 bloqueios; 3 efeitos em `handle_use_item`; `target_id` no dispatch; 3 itens nativos; `_ITEM_POTION_EFFECTS`.
- **Modify:** `tools/test_editor_itens.py` — seção `[K1]`–`[K6]`.
- **Modify:** `game.js` — `useItem` decide a mira.
- **Modify:** `tools/editor_items_logic.js` + `tools/test_editor_items_logic.js` — `serializePotion` com os 3 efeitos.
- **Modify:** `tools/editor_items_editor.js` — campos do dado de imunidade.
- **Modify:** `CLAUDE.md` — nota da fase.

**Ordem:** Task 1 (helpers) → Task 2 (imunidade) → Task 3 (efeitos+protocolo) → Task 4 (nativos+editor) → Task 5 (cliente) → Task 6 (verificação/docs).

---

## Task 1: Extrair os helpers de cura

**Files:**
- Modify: `server.py` (`handle_purificacao`, ramos `veneno`/`petrificacao`/`doenca`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione ao final, antes de `if __name__ == "__main__":`:

```python
def test_curar_status_helpers():
    print("\n[K1] Helpers de cura de status")
    r = _gear_room()
    # Veneno: efeitos + cegueira
    p = S.make_player("p1", "Victor", "warrior", 0)
    p["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1, "duracao": 3,
                            "save": "fortitude", "dificuldade": 10}]
    p["cego"] = True; p["cego_rodadas"] = 3; p["cego_pen_ataque"] = -4
    p["penalidades"] = {"ataque": -4}
    p["bloqueia_distancia"] = True
    check("cura veneno devolve True", r._curar_veneno_status(p) is True)
    check("efeitos_veneno limpos", p["efeitos_veneno"] == [])
    check("cegueira removida", not p.get("cego") and p.get("cego_rodadas") == 0)
    check("penalidade de ataque revertida", p["penalidades"].get("ataque") == 0)
    check("volta a atacar à distância", p.get("bloqueia_distancia") is False)
    check("sem veneno devolve False", r._curar_veneno_status(p) is False)
    # Petrificação
    p2 = S.make_player("p2", "Aliado", "rogue", 1)
    p2["petrificado"] = True; p2["petrificado_rodadas"] = 3
    check("cura petrificação devolve True", r._curar_petrificacao(p2) is True)
    check("petrificado limpo", not p2.get("petrificado") and p2.get("petrificado_rodadas") == 0)
    check("sem petrificação devolve False", r._curar_petrificacao(p2) is False)

def test_purificacao_intacta():
    print("\n[K1b] Purificação do clérigo continua funcionando após a extração")
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Lewis", "cleric", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["fome"], p["sede"] = 20, 20
    alvo = S.make_player("p2", "Aliado", "rogue", 1)
    r.players["p2"] = alvo
    p["pos"] = [1, 1]; alvo["pos"] = [2, 1]
    alvo["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1, "duracao": 3,
                               "save": "fortitude", "dificuldade": 10}]
    asyncio.run(r.handle_purificacao("p1", {"tipo": "veneno", "target_id": "p2"}))
    check("purificação removeu o veneno", not alvo.get("efeitos_veneno"))
    alvo2 = S.make_player("p3", "Outro", "rogue", 2)
    r.players["p3"] = alvo2; alvo2["pos"] = [1, 2]
    alvo2["petrificado"] = True; alvo2["petrificado_rodadas"] = 2
    p["action_done"] = False
    asyncio.run(r.handle_purificacao("p1", {"tipo": "petrificacao", "target_id": "p3"}))
    check("purificação removeu a petrificação", not alvo2.get("petrificado"))
```

Registre no `if __name__ == "__main__":`, logo após a última linha de chamadas existente:
```python
    test_curar_status_helpers(); test_purificacao_intacta()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando as duas.
Expected: FAIL — `_curar_veneno_status` / `_curar_petrificacao` não existem.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione os dois helpers na classe `GameRoom`, **imediatamente antes** de `async def handle_purificacao`:

```python
    def _curar_veneno_status(self, alvo):
        """Remove todos os efeitos de veneno e a cegueira por veneno. Devolve True
        se havia algo para curar. Extraído de handle_purificacao para ser reusado
        pelos consumíveis de cura (antídoto)."""
        efeitos = alvo.get("efeitos_veneno", [])
        cego = alvo.get("cego")
        if not efeitos and not cego:
            return False
        for efeito in efeitos:
            self._reverter_efeito_veneno(alvo, efeito)
        alvo["efeitos_veneno"] = []
        if cego:
            alvo["cego"] = False
            alvo["cego_rodadas"] = 0
            pen = alvo.pop("cego_pen_ataque", -4)
            alvo.setdefault("penalidades", {})
            alvo["penalidades"]["ataque"] = alvo["penalidades"].get("ataque", 0) - pen
            alvo["bloqueia_distancia"] = False
        return True

    def _curar_petrificacao(self, alvo):
        """Remove a petrificação. Devolve True se havia algo para curar."""
        if not alvo.get("petrificado"):
            return False
        alvo["petrificado"] = False
        alvo["petrificado_rodadas"] = 0
        return True
```

3b. Em `handle_purificacao`, troque o ramo de veneno:
```python
        if tipo == "veneno":
            efeitos = alvo.get("efeitos_veneno", [])
            cego = alvo.get("cego")
            if efeitos or cego:
                for efeito in efeitos:
                    self._reverter_efeito_veneno(alvo, efeito)
                alvo["efeitos_veneno"] = []
                if cego:
                    alvo["cego"] = False
                    alvo["cego_rodadas"] = 0
                    pen = alvo.pop("cego_pen_ataque", -4)
                    alvo.setdefault("penalidades", {})
                    alvo["penalidades"]["ataque"] = alvo["penalidades"].get("ataque", 0) - pen
                    alvo["bloqueia_distancia"] = False
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está envenenado."}); return
```
por:
```python
        if tipo == "veneno":
            if self._curar_veneno_status(alvo):
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está envenenado."}); return
```

3c. Troque o ramo de petrificação:
```python
        elif tipo == "petrificacao":
            if alvo.get("petrificado"):
                alvo["petrificado"] = False
                alvo["petrificado_rodadas"] = 0
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está petrificado."}); return
```
por:
```python
        elif tipo == "petrificacao":
            if self._curar_petrificacao(alvo):
                removido = True
            else:
                await self.send_to(pid, {"type": "error", "msg": f"{alvo['name']} não está petrificado."}); return
```

(O ramo de doença já chama `self._curar_doenca(alvo)`; o de maldição fica como está.)

- [ ] **Step 4: Rodar e ver passar**

Import direto: as duas novas.
Expected: 0 falharam. Rode também `python tools/test_clerigo_espec.py` (exercita a Purificação) e reporte a linha final.

- [ ] **Step 5: Commit (ver receita no topo)**

```bash
git add tools/test_editor_itens.py
# gerar HEAD+mudanças e preparar o blob (receita do topo)
git diff --cached -- server.py
git commit -m "refactor(status): extrai helpers de cura de veneno e petrificação

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Imunidade temporária genérica + 4 bloqueios

**Files:**
- Modify: `server.py` (helpers novos; `_aplicar_veneno` ×2; habilidade de monstro `petrificado`; `_aplicar_doenca`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicione após `test_purificacao_intacta`:

```python
def test_imunidade_status_helpers():
    print("\n[K2] Imunidade temporária de status")
    r = _gear_room()
    r.round_num = 5
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem imunidade", not r._imune_a_status(p, "veneno"))
    r._conceder_imunidade_status(p, "veneno", 3)
    check("imune após conceder", r._imune_a_status(p, "veneno") is True)
    check("outro status não é afetado", not r._imune_a_status(p, "doenca"))
    r.round_num = 8
    check("expira quando a rodada passa", not r._imune_a_status(p, "veneno"))

def test_imunidade_bloqueia_fontes():
    print("\n[K3] Imunidade bloqueia as 4 fontes")
    # 1) veneno
    r = _gear_room(); r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r._conceder_imunidade_status(p, "veneno", 5)
    asyncio.run(r._aplicar_veneno(p, "veneno_aranha_sombria"))
    check("veneno bloqueado pela imunidade", not p.get("efeitos_veneno"))
    # 2) petrificação por veneno (basilisco)
    r2 = _gear_room(); r2.round_num = 1
    p2 = S.make_player("p1", "Victor", "warrior", 0)
    r2.players["p1"] = p2
    p2["fort"] = -50   # garante falha no save
    r2._conceder_imunidade_status(p2, "petrificacao", 5)
    asyncio.run(r2._aplicar_veneno(p2, "veneno_basilisco"))
    check("petrificação por veneno bloqueada", not p2.get("petrificado"))
    # 3) petrificação por habilidade de monstro
    r3 = _gear_room(); r3.round_num = 1
    p3 = S.make_player("p1", "Victor", "warrior", 0)
    r3.players["p1"] = p3
    r3._conceder_imunidade_status(p3, "petrificacao", 5)
    check("helper reconhece a imunidade", r3._imune_a_status(p3, "petrificacao") is True)
    # 4) doença
    r4 = _gear_room(); r4.round_num = 1
    p4 = S.make_player("p1", "Victor", "warrior", 0)
    r4.players["p1"] = p4
    r4._conceder_imunidade_status(p4, "doenca", 5)
    asyncio.run(r4._aplicar_doenca(p4, "leve"))
    check("doença bloqueada pela imunidade", not p4.get("doente"))
    # sem imunidade, a doença aplica normalmente (prova que o teste é honesto)
    r5 = _gear_room(); r5.round_num = 1
    p5 = S.make_player("p1", "Victor", "warrior", 0)
    r5.players["p1"] = p5
    asyncio.run(r5._aplicar_doenca(p5, "leve"))
    check("sem imunidade a doença aplica", p5.get("doente") is True)
```

Registre no `__main__` após a linha da Task 1:
```python
    test_imunidade_status_helpers(); test_imunidade_bloqueia_fontes()
```

- [ ] **Step 2: Rodar e ver falhar**

Expected: FAIL — `_conceder_imunidade_status` / `_imune_a_status` não existem.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione a constante module-level junto dos outros sets de itens (perto de `_ITEM_POTION_EFFECTS`):
```python
# Status que um consumível pode curar e contra os quais pode imunizar.
_STATUS_IMUNIZAVEIS = {"veneno", "petrificacao", "doenca"}
```

3b. Adicione os dois helpers na classe `GameRoom`, logo após `_curar_petrificacao`:
```python
    def _conceder_imunidade_status(self, p, status, rodadas):
        """Imunidade temporária a um status (veneno/petrificacao/doenca). Guarda a
        rodada-limite absoluta, como os demais buffs temporários do motor."""
        if status not in _STATUS_IMUNIZAVEIS or rodadas <= 0:
            return
        p.setdefault("imunidades_status", {})[status] = self.round_num + int(rodadas)

    def _imune_a_status(self, p, status):
        """True enquanto a imunidade temporária àquele status não expirou."""
        return (p.get("imunidades_status", {}) or {}).get(status, 0) > self.round_num
```

3c. **Bloqueio 1 — veneno.** Em `_aplicar_veneno`, logo após a checagem de imunidade estática
(o bloco que narra "não afeta … (imune a venenos)"), adicione:
```python
        if self._eh_jogador(alvo) and self._imune_a_status(alvo, "veneno"):
            await self.gm_say(f"🛡️ **{alvo_nome}** está imunizado — **{nome}** não faz efeito.")
            return
```

3d. **Bloqueio 2 — petrificação por veneno.** No ramo `elif op == "petrificar":`, dentro do
`else:` (falha do save), o código hoje é:
```python
            else:
                pet_dur = self._rolar_dado(veneno.get("duracao", 1)) * dobro
                alvo["petrificado"]         = True
```
Troque por:
```python
            else:
                if self._eh_jogador(alvo) and self._imune_a_status(alvo, "petrificacao"):
                    await self.gm_say(f"🛡️ **{alvo_nome}** resiste à petrificação (imunizado)!")
                    await self.push_state()
                    return
                pet_dur = self._rolar_dado(veneno.get("duracao", 1)) * dobro
                alvo["petrificado"]         = True
```

3e. **Bloqueio 3 — petrificação por habilidade de monstro.** No trecho que hoje é:
```python
            elif effect == "petrificado":
                target["petrificado"] = True
                target["petrificado_rodadas"] = ability.get("effect_duration", 1)
                await self.gm_say(f"🗿 **{tgt_name}** foi petrificado!")
```
Troque por:
```python
            elif effect == "petrificado":
                if self._eh_jogador(target) and self._imune_a_status(target, "petrificacao"):
                    await self.gm_say(f"🛡️ **{tgt_name}** resiste à petrificação (imunizado)!")
                else:
                    target["petrificado"] = True
                    target["petrificado_rodadas"] = ability.get("effect_duration", 1)
                    await self.gm_say(f"🗿 **{tgt_name}** foi petrificado!")
```

3f. **Bloqueio 4 — doença.** Em `_aplicar_doenca`, logo após:
```python
        if not self._eh_jogador(p):
            return False
```
adicione:
```python
        if self._imune_a_status(p, "doenca"):
            await self.gm_say(f"🛡️ **{p.get('name','O herói')}** está imunizado contra doenças.")
            return False
```

- [ ] **Step 4: Rodar e ver passar**

Import direto: as duas novas + as da Task 1 → 0 falharam.

- [ ] **Step 5: Commit (ver receita no topo)**

```bash
git add tools/test_editor_itens.py
# blob sobre o HEAD (receita do topo)
git commit -m "feat(status): imunidade temporária a veneno, petrificação e doença

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Três efeitos de consumível + `target_id` no protocolo

**Files:**
- Modify: `server.py` (`BONUS_ACTION_EFFECTS`, `handle_use_item`, dispatch de `use_item`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicione após `test_imunidade_bloqueia_fontes`:

```python
def _sala_turno_cura():
    """Sala com herói no turno + um aliado adjacente e um distante."""
    r = _gear_room()
    r.phase = "playing"; r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["pos"] = [1, 1]; p["fome"], p["sede"] = 10, 10
    perto = S.make_player("p2", "Perto", "rogue", 1)
    longe = S.make_player("p3", "Longe", "cleric", 2)
    r.players["p2"] = perto; r.players["p3"] = longe
    perto["pos"] = [2, 1]; longe["pos"] = [9, 9]
    return r, p, perto, longe

def _frasco(effect, imunidade="1d4", iid=None):
    return {"id": iid or effect, "name": "Frasco", "emoji": "🧪",
            "item_slot": "bag", "effect": effect, "value": 0,
            "imunidade_dado": imunidade}

def test_cura_status_em_si():
    print("\n[K4] Consumíveis curam o próprio herói e imunizam")
    # Veneno
    r, p, _, _ = _sala_turno_cura()
    p["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1, "duracao": 3,
                            "save": "fortitude", "dificuldade": 10}]
    p["bag"] = [_frasco("cure_poison")]
    asyncio.run(r.handle_use_item("p1", "cure_poison"))
    check("veneno curado", not p.get("efeitos_veneno"))
    check("imunidade concedida", r._imune_a_status(p, "veneno") is True)
    check("frasco consumido", not p["bag"])
    # Petrificação
    r2, p2, _, _ = _sala_turno_cura()
    p2["petrificado"] = True; p2["petrificado_rodadas"] = 3
    p2["bag"] = [_frasco("cure_petrification")]
    asyncio.run(r2.handle_use_item("p1", "cure_petrification"))
    check("petrificação curada", not p2.get("petrificado"))
    check("imune a petrificação", r2._imune_a_status(p2, "petrificacao") is True)
    # Doença
    r3, p3, _, _ = _sala_turno_cura()
    asyncio.run(r3._aplicar_doenca(p3, "leve"))
    p3["bag"] = [_frasco("cure_disease")]
    asyncio.run(r3.handle_use_item("p1", "cure_disease"))
    check("doença curada", not p3.get("doente"))
    check("imune a doença", r3._imune_a_status(p3, "doenca") is True)
    # Uso preventivo: consome mesmo sem o status
    r4, p4, _, _ = _sala_turno_cura()
    p4["bag"] = [_frasco("cure_poison")]
    asyncio.run(r4.handle_use_item("p1", "cure_poison"))
    check("uso preventivo consome o item", not p4["bag"])
    check("uso preventivo imuniza", r4._imune_a_status(p4, "veneno") is True)

def test_cura_status_em_aliado():
    print("\n[K5] Consumíveis em aliado adjacente")
    r, p, perto, longe = _sala_turno_cura()
    perto["petrificado"] = True; perto["petrificado_rodadas"] = 3
    p["bag"] = [_frasco("cure_petrification")]
    asyncio.run(r.handle_use_item("p1", "cure_petrification", "p2"))
    check("aliado adjacente curado", not perto.get("petrificado"))
    check("imunidade vai para o ALVO", r._imune_a_status(perto, "petrificacao") is True)
    check("quem usou não fica imune", not r._imune_a_status(p, "petrificacao"))
    check("frasco consumido", not p["bag"])
    # Alvo distante: recusa sem consumir
    r2, p2, _, longe2 = _sala_turno_cura()
    longe2["petrificado"] = True
    p2["bag"] = [_frasco("cure_petrification")]
    asyncio.run(r2.handle_use_item("p1", "cure_petrification", "p3"))
    check("alvo distante recusado", longe2.get("petrificado") is True)
    check("item NÃO consumido em alvo inválido", len(p2["bag"]) == 1)
    check("ação bônus NÃO gasta em alvo inválido", not p2.get("bonus_action_used"))
```

Registre no `__main__` após a linha da Task 2:
```python
    test_cura_status_em_si(); test_cura_status_em_aliado()
```

- [ ] **Step 2: Rodar e ver falhar**

Expected: FAIL — `handle_use_item` não aceita 3º argumento / não conhece os efeitos.

- [ ] **Step 3: Implementar em `server.py`**

3a. `BONUS_ACTION_EFFECTS` — hoje:
```python
    BONUS_ACTION_EFFECTS = {"heal", "regeneration", "atk_bonus", "antidote", "coat_poison", "veil_shadow"}
```
→
```python
    BONUS_ACTION_EFFECTS = {"heal", "regeneration", "atk_bonus", "antidote", "coat_poison",
                            "veil_shadow", "cure_poison", "cure_petrification", "cure_disease"}
```

3b. Assinatura: `async def handle_use_item(self, pid, item_id):` → `async def handle_use_item(self, pid, item_id, target_id=None):`

3c. **Validação do alvo, ANTES do consumo da ação bônus.** O handler já tem um bloco de guardas
que precedem `if effect in self.BONUS_ACTION_EFFECTS:` (veil_shadow, Último Esforço, doses).
Adicione mais uma guarda nesse bloco, logo antes da linha `max_uses = int(item.get("max_uses", 1) or 1)`:
```python
        # Consumíveis de cura de status miram o próprio herói ou um aliado ADJACENTE.
        # Validar antes da ação bônus: alvo inválido não gasta item nem ação.
        _CURA_STATUS = {"cure_poison": "veneno", "cure_petrification": "petrificacao",
                        "cure_disease": "doenca"}
        alvo_cura = p
        if effect in _CURA_STATUS:
            if target_id and target_id != pid:
                alvo_cura = self.players.get(target_id)
                if not alvo_cura or not alvo_cura.get("alive"):
                    await self.send_to(pid, {"type": "error", "msg": "Aliado inválido."}); return
                if not self._no_raio(p, alvo_cura, 1):
                    await self.send_to(pid, {"type": "error",
                        "msg": "O aliado precisa estar adjacente."}); return
```

3d. **Os três ramos de efeito.** Adicione no encadeamento de `elif effect == ...` (por exemplo,
logo após o ramo `elif effect == "atk_bonus":`):
```python
        elif effect in _CURA_STATUS:
            status = _CURA_STATUS[effect]
            curou = (self._curar_veneno_status(alvo_cura) if status == "veneno" else
                     self._curar_petrificacao(alvo_cura) if status == "petrificacao" else
                     self._curar_doenca(alvo_cura))
            rod = self._rolar_dado(item.get("imunidade_dado", 0))
            if rod:
                self._conceder_imunidade_status(alvo_cura, status, rod)
            quem = "" if alvo_cura is p else f" em **{alvo_cura['name']}**"
            nome_status = {"veneno": "veneno", "petrificacao": "petrificação",
                           "doenca": "doença"}[status]
            if curou:
                txt = f"cura o {nome_status}{quem}"
            else:
                txt = f"não havia {nome_status}{quem} para curar"
            extra = f" — imune a {nome_status} por **{rod}** rodada(s)!" if rod else "."
            await self.gm_say(f"{item['emoji']} **{p['name']}** usa **{item['name']}**: {txt}{extra}")
```

3e. **Dispatch** — hoje:
```python
                elif t == "use_item":
                    if room: await room.handle_use_item(pid, msg.get("item_id"))
```
→
```python
                elif t == "use_item":
                    if room: await room.handle_use_item(pid, msg.get("item_id"), msg.get("target_id"))
```

- [ ] **Step 4: Rodar e ver passar**

Import direto: as duas novas + todas as anteriores → 0 falharam.

- [ ] **Step 5: Commit (ver receita no topo)**

```bash
git add tools/test_editor_itens.py
git commit -m "feat(itens): consumíveis que curam status e imunizam (si ou aliado adjacente)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Itens nativos + editor (validação e lógica pura)

**Files:**
- Modify: `server.py` (`SHOP_MERCHANT`, `_ITEM_POTION_EFFECTS`, `_validate_custom_potion`)
- Modify: `tools/editor_items_logic.js`
- Test: `tools/test_editor_itens.py`, `tools/test_editor_items_logic.js`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione após `test_cura_status_em_aliado`:

```python
def test_itens_nativos_e_editor_cura():
    print("\n[K6] Itens nativos + validação no editor")
    ant = next((i for i in S.SHOP_MERCHANT if i["id"] == "antidote"), None)
    check("antídoto nativo existe", ant is not None)
    check("antídoto cura veneno de verdade", ant and ant.get("effect") == "cure_poison")
    check("antídoto tem dado de imunidade", ant and ant.get("imunidade_dado") == "1d4")
    oleo = next((i for i in S.SHOP_MERCHANT if i["id"] == "oleo_dissolvente"), None)
    check("óleo dissolvente na loja", oleo and oleo.get("effect") == "cure_petrification")
    elix = next((i for i in S.SHOP_MERCHANT if i["id"] == "elixir_depurativo"), None)
    check("elixir depurativo na loja", elix and elix.get("effect") == "cure_disease")
    # Validação de poção custom com os 3 efeitos
    for eff in ("cure_poison", "cure_petrification", "cure_disease"):
        ok, it = S._validate_custom_item(potion_sample(id=f"p_{eff}", effect=eff,
                                                       imunidade_dado="1d6"))
        check(f"aceita {eff}", ok and it.get("effect") == eff)
        check(f"{eff} preserva imunidade_dado", ok and it.get("imunidade_dado") == "1d6")
    okb, itb = S._validate_custom_item(potion_sample(id="p_bad", effect="cure_poison",
                                                     imunidade_dado="1d7"))
    check("dado de imunidade inválido é descartado", okb and "imunidade_dado" not in itb)
```

Em `tools/test_editor_items_logic.js`, adicione antes do `console.log` final:
```javascript
// Antídotos — efeitos de cura de status com dado de imunidade
check("POTION_EFFECTS inclui os 3 efeitos de cura",
  L.POTION_EFFECTS.indexOf("cure_poison") >= 0
  && L.POTION_EFFECTS.indexOf("cure_petrification") >= 0
  && L.POTION_EFFECTS.indexOf("cure_disease") >= 0);
const cura = L.serializePotion({name:"Antídoto Forte", effect:"cure_poison",
  imun_qtd:2, imun_faces:6,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:30});
check("serializePotion cura grava effect", cura.effect === "cure_poison");
check("serializePotion cura grava imunidade_dado", cura.imunidade_dado === "2d6");
check("cura não grava doses", cura.max_uses === undefined);
const heal = L.serializePotion({name:"Cura", effect:"heal", value:10});
check("heal não grava imunidade_dado", heal.imunidade_dado === undefined);
```

Registre a chamada python no `__main__`:
```python
    test_itens_nativos_e_editor_cura()
```

- [ ] **Step 2: Rodar e ver falhar**

Python: FAIL (antídoto ainda é `heal`; óleo/elixir não existem; validação rejeita os efeitos).
Node: FAIL (`POTION_EFFECTS` sem os 3).

- [ ] **Step 3: Implementar**

3a. `server.py` — em `SHOP_MERCHANT`, troque a linha do antídoto:
```python
    {"id": "antidote",      "name": "Antídoto",          "emoji": "💚",  "price": 5,  "item_slot": "bag",   "effect": "heal",      "value": 6},
```
por (o antídoto corrigido + os dois itens novos):
```python
    {"id": "antidote",      "name": "Antídoto",          "emoji": "💚",  "price": 5,  "item_slot": "bag",   "effect": "cure_poison", "value": 0, "imunidade_dado": "1d4",
     "descricao": "Neutraliza venenos e protege contra novos por 1d4 rodadas."},
    {"id": "oleo_dissolvente", "name": "Óleo Dissolvente", "emoji": "🫗", "price": 25, "item_slot": "bag", "effect": "cure_petrification", "value": 0, "imunidade_dado": "1d4",
     "descricao": "Dissolve a pedra: cura petrificação e protege por 1d4 rodadas."},
    {"id": "elixir_depurativo", "name": "Elixir Depurativo", "emoji": "🧴", "price": 20, "item_slot": "bag", "effect": "cure_disease", "value": 0, "imunidade_dado": "1d4",
     "descricao": "Purga doenças do corpo e protege por 1d4 rodadas."},
```

3b. `server.py` — `_ITEM_POTION_EFFECTS`:
```python
_ITEM_POTION_EFFECTS = {"heal", "regeneration", "atk_bonus"}
```
→
```python
_ITEM_POTION_EFFECTS = {"heal", "regeneration", "atk_bonus",
                        "cure_poison", "cure_petrification", "cure_disease"}
```

3c. `server.py` — em `_validate_custom_potion`, logo antes do `return True, item` final (onde já
há o bloco `if effect == "heal": ... max_uses ...`), adicione:
```python
    if effect in ("cure_poison", "cure_petrification", "cure_disease"):
        dado = raw.get("imunidade_dado")
        if dado and _die_ok(dado):
            item["imunidade_dado"] = str(dado).lower()
```

3d. `tools/editor_items_logic.js` — `POTION_EFFECTS`:
```javascript
  var POTION_EFFECTS = ["heal", "regeneration", "atk_bonus"];
```
→
```javascript
  var POTION_EFFECTS = ["heal", "regeneration", "atk_bonus",
                        "cure_poison", "cure_petrification", "cure_disease"];
```
E em `serializePotion`, logo após o bloco `if (effect === "heal") { ... }`, adicione:
```javascript
    if (effect.indexOf("cure_") === 0) {
      var iq = Math.max(1, +d.imun_qtd || 1);
      item.imunidade_dado = buildDie(iq, d.imun_faces || 4);
    }
```

- [ ] **Step 4: Rodar e ver passar**

Python: import direto do novo teste + os anteriores → 0 falharam.
Node: `node tools/test_editor_items_logic.js` → 0 falharam.

- [ ] **Step 5: Commit**

`tools/editor_items_logic.js` e os testes vão por `git add`; `server.py` pela receita do topo.
```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js tools/test_editor_itens.py
git commit -m "feat(itens): antídoto real + óleo e elixir nativos; efeitos de cura no editor

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Cliente — mira do consumível e campos do editor

**Files:**
- Modify: `game.js` (`useItem`, ~12629)
- Modify: `tools/editor_items_editor.js` (`renderPotionForm`, leitura)

- [ ] **Step 1: Mira em `game.js`**

Hoje:
```javascript
function useItem(itemId){ send({type:'use_item',item_id:itemId}); }
```
Troque por:
```javascript
// Consumíveis que curam status podem ser usados no próprio herói ou num aliado
// ADJACENTE — se o alvo não veio, abre o modal de alvo (o servidor revalida).
const CURA_STATUS_EFFECTS = ['cure_poison', 'cure_petrification', 'cure_disease'];
function useItem(itemId, targetId){
  if(targetId === undefined){
    const me = GS.gameState && GS.gameState.players.find(p => p.id === GS.myPid);
    const it = me && (me.bag || []).find(b => b.id === itemId);
    if(it && CURA_STATUS_EFFECTS.includes(it.effect)){
      const alvos = (GS.gameState.players || []).filter(q =>
        q.alive && (q.id === me.id ||
          Math.max(Math.abs(q.pos[0] - me.pos[0]), Math.abs(q.pos[1] - me.pos[1])) <= 1));
      if(alvos.length > 1){
        openTargetModal(`${it.emoji || '🧪'} ${it.name} — Escolha o alvo`, alvos, 'ally',
          id => useItem(itemId, id));
        return;
      }
    }
  }
  send({type:'use_item', item_id:itemId, target_id: targetId});
}
```
Note: com apenas o próprio herói por perto, o modal é pulado e o item é usado em si mesmo
(um clique só, como hoje). `src/ui/inventoryModal.js` **não muda**.

- [ ] **Step 2: Campos do dado de imunidade no editor**

Em `tools/editor_items_editor.js`:

2a. Em `novoDraftPotion()`, acrescente os dois campos ao objeto devolvido:
```javascript
      imun_qtd:1, imun_faces:4,
```

2b. Em `renderPotionForm`, a seção "Efeito" hoje mostra Valor e (só p/ heal) Doses. Troque o
corpo dessa `seccao` para incluir os campos de imunidade quando o efeito for de cura:
```javascript
      seccao("Efeito",
        campo("Tipo", '<select id="ie-effect">' + (L.POTION_EFFECTS || ["heal","regeneration","atk_bonus"]).map(function (e) {
          return '<option value="' + e + '"' + (e === draft.effect ? " selected" : "") + '>' + esc(POTION_LABELS[e] || e) + '</option>'; }).join("") + '</select>') +
        (draft.effect.indexOf("cure_") === 0
          ? campo("Imunidade (quantidade)", numInput("ie-imunq", draft.imun_qtd, 1, 10)) +
            campo("Imunidade (dado)", '<select id="ie-imunf">' + [4,6,8,10,12].map(function (x) {
              return '<option' + (x === draft.imun_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>') +
            '<span class="ie-hint">Cura o status e imuniza pelo número de rodadas rolado.</span>'
          : campo("Valor", numInput("ie-value", draft.value, 0, 999)) +
            (draft.effect === "heal" ? campo("Doses (garrafa)", numInput("ie-maxuses", draft.max_uses, 1, 20)) :
              '<span class="ie-hint">Doses só se aplicam a poções de Cura.</span>'))),
```

2c. Em `POTION_LABELS`, acrescente os rótulos:
```javascript
    cure_poison:"Antídoto (cura veneno)", cure_petrification:"Óleo (cura petrificação)",
    cure_disease:"Elixir (cura doença)",
```

2d. Em `currentPotionDraftFromForm`, as leituras de `ie-value`/`ie-maxuses` precisam virar
defensivas (esses campos somem nos efeitos de cura) e as novas precisam ser lidas. Troque:
```javascript
    draft.value = Math.max(0, +g("ie-value").value || 0);
```
por:
```javascript
    var vv = g("ie-value"); if (vv) draft.value = Math.max(0, +vv.value || 0);
    var iq = g("ie-imunq"); if (iq) draft.imun_qtd = Math.max(1, +iq.value || 1);
    var ifa = g("ie-imunf"); if (ifa) draft.imun_faces = +ifa.value || 4;
```

- [ ] **Step 3: Verificar**

Run: `node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js parse OK')"`
Expected: `game.js parse OK`

Run: `node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('editor parse OK')"`
Expected: `editor parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: 0 falharam.

- [ ] **Step 4: Commit**

`tools/editor_items_editor.js` por `git add`; `game.js` pela receita do topo (blob sobre o HEAD).
```bash
git add tools/editor_items_editor.js
git diff --cached -- game.js
git commit -m "feat(itens): mira dos consumíveis de cura + campos de imunidade no editor

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Verificação isolada + docs + memória

- [ ] **Step 1: Suíte no estado COMMITADO isolado**

```bash
git worktree add --detach /tmp/lfh_vk HEAD
cd /tmp/lfh_vk
python tools/test_editor_itens.py
python tools/test_clerigo_espec.py
python tools/test_guilda.py
node tools/test_editor_items_logic.js
node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js OK')"
node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('editor OK')"
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_vk --force
```
Expected: `[K1]`–`[K6]` verdes e nada regredido. **Rode também** `python tools/test_devorador.py`
e `python tools/test_ladino_espec.py` (tocam veneno/petrificação) e reporte as linhas finais —
lembrando que `test_devorador.py` tem 1 teste flaky pré-existente de rolagem aleatória.

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação ao final, resumindo: helpers `_curar_veneno_status`/
`_curar_petrificacao` extraídos de `handle_purificacao` (que passa a chamá-los); imunidade
temporária genérica (`imunidades_status[status] = round_num + N`, helpers
`_conceder_imunidade_status`/`_imune_a_status`) checada nas **4 fontes** (veneno; petrificação por
veneno; petrificação por habilidade de monstro; doença); 3 efeitos de consumível
(`cure_poison`/`cure_petrification`/`cure_disease`) como ação bônus, curando + imunizando por
`imunidade_dado`; `use_item` ganhou `target_id` **opcional** (si mesmo ou aliado adjacente,
validado antes de gastar item/ação); **mudança de gameplay**: o `antidote` nativo era
`effect:"heal"` (curava 6 HP e não removia veneno) e virou `cure_poison`; itens novos
`oleo_dissolvente` e `elixir_depurativo` no mercador; editor expõe os 3 efeitos com o dado de
imunidade; cliente decide a mira dentro de `useItem` (o modal de inventário não mudou). Cite os
testes `[K1]`–`[K6]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-28-antidotos-cura-de-status.md
git commit -m "docs(itens): registra os antídotos e curas de status

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Memória**

Crie `memory/antidotos-cura-de-status.md` (tipo `project`) com o que foi feito, o estado, a
contagem de checks, a mudança de gameplay do antídoto e o follow-up de smoke in-app. Linha-índice
no topo de `MEMORY.md`.

- [ ] **Step 5: Follow-up manual (usuário)**

`python server.py` → comprar Antídoto, Óleo Dissolvente e Elixir Depurativo no mercador. Em
combate: tomar veneno e usar o antídoto (deve curar e imunizar); pedir para um aliado adjacente
usar o óleo em você enquanto petrificado; conferir no editor a sub-aba Poções com os 3 efeitos
novos e o dado de imunidade.

---

## Self-Review (autor do plano)

- **Cobertura do spec:** helpers extraídos + purificação intacta (T1, [K1]/[K1b]) ✓; imunidade
  genérica + 4 bloqueios (T2, [K2]/[K3]) ✓; 3 efeitos + `target_id` + validação de alvo sem
  consumir (T3, [K4]/[K5]) ✓; 3 itens nativos + antídoto convertido + editor (T4, [K6]) ✓;
  cliente com mira em `useItem` e campos do editor (T5) ✓; verificação/docs/memória (T6) ✓.
- **Uso preventivo consome o item** (decisão do spec) — coberto explicitamente em [K4].
- **Alvo inválido não consome** — coberto em [K5], e a implementação (T3, 3c) posiciona a
  validação **antes** do bloco de ação bônus, que é o que garante isso.
- **Consistência de nomes:** `_CURA_STATUS` (T3) mapeia effect→status e é usado pela validação e
  pelo ramo de efeito; `imunidade_dado` é o mesmo nome no item nativo (T4, 3a), na validação
  (T4, 3c), no `serializePotion` (T4, 3d) e no ramo de efeito (T3, 3d). `CURA_STATUS_EFFECTS`
  (cliente, T5) lista os mesmos 3 efeitos.
- **Risco:** `_aplicar_veneno` e `_aplicar_doenca` são chamados em muitos pontos; a T6 roda
  `test_devorador`, `test_ladino_espec` e `test_clerigo_espec` além da suíte principal.
- **Sem placeholders:** todos os passos têm código/comando concreto.
