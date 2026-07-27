# Fase J: habilidades de herói restantes concedidas por item — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estender a concessão por item às 11 habilidades de herói restantes viáveis (4 do clérigo, 2 do ladino, 4 do paladino, 1 do bardo), totalizando 14 com as da Fase I.

**Architecture:** O mecanismo da Fase I já existe (`_habilidades_concedidas`, `GRANTED_HERO_SKILLS`, `_granted_hero_skills` no `push_state`, botões no HUD). Esta fase extrai um helper DRY (`_pode_hab_heroi`), relaxa 14 travas de classe com ele, corrige a lacuna dos upkeeps (habilidade concedida não pagava manutenção), cresce o mapa de 3→14 entradas e adiciona 2 despachos no cliente.

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`game.js`, `tools/editor_items_editor.js`), testes: `python tools/test_editor_itens.py`, `python tools/test_guilda.py`, `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de partial staging — LER ANTES DE QUALQUER COMMIT

O usuário reworka `server.py`, `game.js` e `src/gameState.js` em paralelo. **NUNCA** `git add` nesses arquivos, nem `git add -A`.

```bash
git add <arquivos de teste / editor_items_*.js>   # seguros, fora do WIP
git diff -- <arquivo> > /tmp/all.patch
# Identifique os @@ hunks QUE VOCÊ escreveu; monte /tmp/mine.patch =
# header (4 linhas) + APENAS esses hunks.
git apply --cached /tmp/mine.patch
git diff --cached -- <arquivo>    # confira: só o seu código
```

**LIÇÃO DA FASE I — leia com atenção:** em vários pontos o WIP do usuário edita **as mesmas linhas** que esta fase toca. Quando isso acontece, o hunk auto-extraído **varre o WIP**. Nesse caso:

1. `git reset <arquivo>` para desfazer;
2. obtenha a versão do HEAD: `git show HEAD:server.py | sed -n 'INI,FIMp'`;
3. **escreva o patch à mão** contra o HEAD (só a sua mudança);
4. `git apply --cached --recount /caminho/mine.patch`;
5. **valide a versão que será commitada**:
   ```bash
   git show :server.py > /tmp/staged.py
   python -c "import ast; ast.parse(open('/tmp/staged.py',encoding='utf-8').read()); print('OK')"
   ```

Se um hunk seu ficar idêntico a algo que o WIP já tem, commitar essa forma é o certo — o diff do usuário encolhe e não há conflito.

## ⚠️ A suíte aborta no working tree (pré-existente)

`python tools/test_editor_itens.py` CRASHA na seção `[7]` (WIP de lojas por cidade em `handle_shop_buy`). **Não é seu, não conserte.** Verifique via import direto:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location('t','tools/test_editor_itens.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.test_hab_clerigo_concedida()
print(f'{m.PASS} passaram, {m.FAIL} falharam')
"
```

---

## File Structure

- **Modify:** `server.py` — helpers `_pode_hab_heroi`/`_tem_alguma_hab_heroi`; retrofit das 3 travas da Fase I; 14 travas relaxadas; `_provocador`; `GRANTED_HERO_SKILLS` 3→14.
- **Modify:** `tools/test_editor_itens.py` — seção `[J1]`–`[J6]`.
- **Modify:** `game.js` — 2 despachos no bloco de habilidades concedidas.
- **Modify:** `tools/editor_items_editor.js` — `GRANTED_HERO_IDS` 3→14.
- **Modify:** `CLAUDE.md` — nota da Fase J.

**Ordem importa:** a Task 1 (helpers + mapa) é pré-requisito de todas as outras.

---

## Task 1: Helpers DRY + mapa de 14 entradas

**Files:**
- Modify: `server.py` (helpers junto de `_habilidades_concedidas`, ~1349; retrofit das 3 travas da Fase I; `GRANTED_HERO_SKILLS`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione ao final, antes do bloco `if __name__ == "__main__":`:

```python
def test_helpers_hab_heroi():
    print("\n[J0] Helpers de habilidade de herói")
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("classe dona passa sem item",
          S._pode_hab_heroi(S.make_player("p2", "L", "cleric", 1), "cleric", "hero_cleric_cura"))
    check("outra classe sem item: não", not S._pode_hab_heroi(p, "cleric", "hero_cleric_cura"))
    p["gear"]["ring1"] = _item_com_habilidade("hero_cleric_cura", id="anel_c")
    check("outra classe com item: sim", S._pode_hab_heroi(p, "cleric", "hero_cleric_cura"))
    check("item de uma não libera outra",
          not S._pode_hab_heroi(p, "cleric", "hero_cleric_ressurreicao"))
    aids = {"hero_rogue_detectar_armadilhas", "hero_rogue_esconder_sombras"}
    check("conjunto: sem nenhuma concedida", not S._tem_alguma_hab_heroi(p, "rogue", aids))
    p["gear"]["boots"] = _item_com_habilidade("hero_rogue_esconder_sombras", id="bota_s")
    check("conjunto: com uma concedida", S._tem_alguma_hab_heroi(p, "rogue", aids))
    check("conjunto: classe dona passa",
          S._tem_alguma_hab_heroi(S.make_player("p3", "L", "rogue", 2), "rogue", aids))

def test_mapa_14_habilidades():
    print("\n[J0b] Mapa GRANTED_HERO_SKILLS com 14 habilidades")
    m = S.GameRoom.GRANTED_HERO_SKILLS
    check("14 entradas", len(m) == 14)
    esperados = {
        "hero_rogue_detectar_armadilhas", "hero_rogue_esconder_sombras",
        "hero_paladin_imposicao_maos",
        "hero_cleric_cura", "hero_cleric_cura_area", "hero_cleric_purificacao",
        "hero_cleric_ressurreicao",
        "hero_rogue_criar_armadilha", "hero_rogue_veneno_rapido",
        "hero_paladin_golpe_sagrado", "hero_paladin_protetor",
        "hero_paladin_regeneracao_divina", "hero_paladin_guerreiro_luz",
        "hero_bard_provocacao",
    }
    check("ids esperados", set(m.keys()) == esperados)
    check("todos validam", all(S._granted_ability_valida(a) for a in esperados))
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    p["gear"]["ring1"] = _item_com_habilidade("hero_cleric_cura", id="anel_c")
    sk = r._granted_hero_skills(p)
    check("payload traz a skill real de cura", len(sk) == 1 and sk[0].get("id") == "cura")
    check("payload marca a origem", sk and sk[0].get("granted_origem") == "cleric")
```

Registre no `if __name__ == "__main__":`, logo APÓS `test_validacao_granted_ability()`:

```python
    test_helpers_hab_heroi(); test_mapa_14_habilidades()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando as duas funções.
Expected: FAIL — `_pode_hab_heroi` não existe; o mapa tem 3 entradas.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione os dois helpers **logo após** `_habilidades_concedidas` (module-level, ~1349):

```python
def _pode_hab_heroi(player, cls_id, aid):
    """True se o jogador é da classe dona da habilidade OU se um item equipado a
    concede (Fase I/J). Portão único de todas as habilidades de herói concedíveis."""
    return player.get("class_id") == cls_id or aid in _habilidades_concedidas(player)

def _tem_alguma_hab_heroi(player, cls_id, aids):
    """True se o jogador é da classe OU tem qualquer um dos ids concedidos. Usado
    pelos upkeeps, que cobrem várias habilidades sustentadas de uma vez."""
    if player.get("class_id") == cls_id:
        return True
    return bool(set(aids) & _habilidades_concedidas(player))
```

3b. Cresça `GameRoom.GRANTED_HERO_SKILLS` (hoje com 3 entradas) para:

```python
    GRANTED_HERO_SKILLS = {
        # Fase I (amostra)
        "hero_rogue_detectar_armadilhas": ("rogue", "detectar_armadilhas"),
        "hero_rogue_esconder_sombras":    ("rogue", "esconder_sombras"),
        "hero_paladin_imposicao_maos":    ("paladin", "imposicao_maos"),
        # Fase J — clérigo
        "hero_cleric_cura":               ("cleric", "cura"),
        "hero_cleric_cura_area":          ("cleric", "cura_area"),
        "hero_cleric_purificacao":        ("cleric", "purificacao"),
        "hero_cleric_ressurreicao":       ("cleric", "ressurreicao"),
        # Fase J — ladino
        "hero_rogue_criar_armadilha":     ("rogue", "criar_armadilha"),
        "hero_rogue_veneno_rapido":       ("rogue", "veneno_rapido"),
        # Fase J — paladino
        "hero_paladin_golpe_sagrado":     ("paladin", "golpe_sagrado"),
        "hero_paladin_protetor":          ("paladin", "protetor"),
        "hero_paladin_regeneracao_divina":("paladin", "regeneracao_divina"),
        "hero_paladin_guerreiro_luz":     ("paladin", "guerreiro_luz"),
        # Fase J — bardo
        "hero_bard_provocacao":           ("bard", "provocacao"),
    }
```

3c. **Retrofit das 3 travas da Fase I** para o helper (um padrão só no código):

Em `handle_detectar_armadilhas`, troque:
```python
        if p.get("class_id") != "rogue" and \
                "hero_rogue_detectar_armadilhas" not in _habilidades_concedidas(p):
```
por:
```python
        if not _pode_hab_heroi(p, "rogue", "hero_rogue_detectar_armadilhas"):
```

Em `handle_esconder_sombras`, troque:
```python
        if p.get("class_id") != "rogue" and \
                "hero_rogue_esconder_sombras" not in _habilidades_concedidas(p):
```
por:
```python
        if not _pode_hab_heroi(p, "rogue", "hero_rogue_esconder_sombras"):
```

Em `handle_imposicao_maos`, troque:
```python
        if p.get("class_id") != "paladin" and \
                "hero_paladin_imposicao_maos" not in _habilidades_concedidas(p):
```
por:
```python
        if not _pode_hab_heroi(p, "paladin", "hero_paladin_imposicao_maos"):
```

- [ ] **Step 4: Rodar e ver passar**

Import direto: `m.test_helpers_hab_heroi(); m.test_mapa_14_habilidades()`.
Expected: 0 falharam.

Regressão da Fase I (o retrofit mexeu nas 3 travas):
```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location('t','tools/test_editor_itens.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.test_habilidade_concedida_helper(); m.test_portoes_concedidos()
m.test_tecnica_concedida_uso(); m.test_espec_concedida_efeito()
m.test_habilidades_heroi_concedidas(); m.test_mensagens_sem_richard()
m.test_granted_hero_skills_payload(); m.test_validacao_granted_ability()
m.test_helpers_hab_heroi(); m.test_mapa_14_habilidades()
print(f'{m.PASS} passaram, {m.FAIL} falharam')
"
```
Expected: 0 falharam.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch com: hunk dos 2 helpers, hunk do GRANTED_HERO_SKILLS,
# e os 3 hunks do retrofit. Conferir a vizinhança de cada um.
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "refactor(itens): portão único _pode_hab_heroi + mapa de 14 habilidades

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Clérigo (4 milagres) + Ladino (2 habilidades)

**Files:**
- Modify: `server.py` (`handle_cura` ~11414, `handle_cura_area` ~11468, `handle_purificacao` ~11540, `handle_ressurreicao` ~11623, `handle_criar_armadilha` ~15184, `handle_veneno_rapido` ~15745)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicione após `test_mapa_14_habilidades`:

```python
def test_hab_clerigo_concedida():
    print("\n[J1] Milagres do clérigo concedidos por item")
    # Cura: guerreiro cura um aliado ferido
    r, p = _turn_room_hero("warrior")
    aliado = S.make_player("p2", "Aliado", "rogue", 1)
    r.players["p2"] = aliado
    p["pos"] = [1, 1]; aliado["pos"] = [2, 1]; aliado["hp"] = 1
    asyncio.run(r.handle_cura("p1", {"target_id": "p2", "num_dados": 1}))
    check("sem item: cura recusada", aliado["hp"] == 1)
    p["gear"]["ring1"] = _item_com_habilidade("hero_cleric_cura", id="anel_c")
    asyncio.run(r.handle_cura("p1", {"target_id": "p2", "num_dados": 1}))
    check("com item: aliado curado", aliado["hp"] > 1)
    # Purificação: remove veneno de um aliado adjacente
    r2, p2 = _turn_room_hero("warrior")
    al2 = S.make_player("p2", "Aliado", "rogue", 1)
    r2.players["p2"] = al2
    p2["pos"] = [1, 1]; al2["pos"] = [2, 1]
    al2["efeitos_veneno"] = [{"nome": "V", "operacao": "dano", "dano": 1,
                              "duracao": 3, "save": "fortitude", "dificuldade": 10}]
    asyncio.run(r2.handle_purificacao("p1", {"tipo": "veneno", "target_id": "p2"}))
    check("sem item: purificação recusada", len(al2.get("efeitos_veneno", [])) == 1)
    p2["gear"]["armor"] = _item_com_habilidade("hero_cleric_purificacao", id="cota_p")
    asyncio.run(r2.handle_purificacao("p1", {"tipo": "veneno", "target_id": "p2"}))
    check("com item: veneno removido", not al2.get("efeitos_veneno"))
    # Ressurreição: revive um aliado morto adjacente
    r3, p3 = _turn_room_hero("warrior")
    al3 = S.make_player("p2", "Morto", "rogue", 1)
    r3.players["p2"] = al3
    p3["pos"] = [1, 1]; al3["pos"] = [2, 1]
    al3["alive"] = False; al3["hp"] = 0
    p3["fome"], p3["sede"] = 30, 30
    asyncio.run(r3.handle_ressurreicao("p1", {"target_id": "p2"}))
    check("sem item: ressurreição recusada", al3["alive"] is False)
    p3["gear"]["ring2"] = _item_com_habilidade("hero_cleric_ressurreicao", id="anel_r")
    asyncio.run(r3.handle_ressurreicao("p1", {"target_id": "p2"}))
    check("com item: aliado revivido", al3["alive"] is True)
    # Cura em Área: aceita a chamada com o item (sem erro de classe)
    r4, p4 = _turn_room_hero("warrior")
    al4 = S.make_player("p2", "Aliado", "rogue", 1)
    r4.players["p2"] = al4
    p4["pos"] = [1, 1]; al4["pos"] = [2, 1]; al4["hp"] = 1
    p4["gear"]["boots"] = _item_com_habilidade("hero_cleric_cura_area", id="bota_ca")
    asyncio.run(r4.handle_cura_area("p1", {"num_dados": 1}))
    check("com item: cura em área curou alguém", al4["hp"] > 1 or p4["hp"] == p4["max_hp"])

def test_hab_ladino_concedida():
    print("\n[J2] Habilidades do ladino concedidas por item")
    # Criar armadilha (buraco é sempre liberado, sem fórmula)
    r, p = _turn_room_hero("warrior")
    p["pos"] = [3, 3]
    n0 = len(r.armadilhas)
    asyncio.run(r.handle_criar_armadilha("p1", {"tipo": "buraco"}))
    check("sem item: criar armadilha recusado", len(r.armadilhas) == n0)
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_criar_armadilha", id="anel_a")
    asyncio.run(r.handle_criar_armadilha("p1", {"tipo": "buraco"}))
    check("com item: armadilha criada", len(r.armadilhas) == n0 + 1)
    # Veneno rápido: unta a arma equipada
    r2, p2 = _turn_room_hero("warrior")
    p2["weapon"] = {"id": "wt", "name": "Lâmina", "die": "1d8", "stat": "str_",
                    "categoria": "cortante", "poison_slots": []}
    p2["bag"] = [{"id": "veneno_aranha_sombria", "name": "Veneno", "emoji": "🕷️",
                  "item_slot": "bag", "effect": "coat_poison",
                  "veneno_id": "veneno_aranha_sombria"}]
    asyncio.run(r2.handle_veneno_rapido("p1", {"veneno_id": "veneno_aranha_sombria"}))
    check("sem item: veneno rápido recusado", r2._weapon_poison_slots(p2) == [])
    p2["gear"]["boots"] = _item_com_habilidade("hero_rogue_veneno_rapido", id="bota_v")
    asyncio.run(r2.handle_veneno_rapido("p1", {"veneno_id": "veneno_aranha_sombria"}))
    check("com item: arma untada", r2._weapon_poison_slots(p2) != [])
```

Registre no `if __name__ == "__main__":` após a linha da Task 1:
```python
    test_hab_clerigo_concedida(); test_hab_ladino_concedida()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando as duas.
Expected: FAIL — as travas de classe recusam mesmo com o item.

- [ ] **Step 3: Implementar em `server.py`**

Troque cada trava pelo helper. **Seis edições**, cada uma substituindo DUAS linhas (a condição e a mensagem) por duas linhas novas:

`handle_cura`:
```python
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Cura."}); return
```
→
```python
        if not _pode_hab_heroi(p, "cleric", "hero_cleric_cura"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Cura."}); return
```

`handle_cura_area`:
```python
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Cura em Área."}); return
```
→
```python
        if not _pode_hab_heroi(p, "cleric", "hero_cleric_cura_area"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Cura em Área."}); return
```

`handle_purificacao`:
```python
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Purificação."}); return
```
→
```python
        if not _pode_hab_heroi(p, "cleric", "hero_cleric_purificacao"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Purificação."}); return
```

`handle_ressurreicao`:
```python
        if p.get("class_id") != "cleric":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Lewis pode usar Ressurreição."}); return
```
→
```python
        if not _pode_hab_heroi(p, "cleric", "hero_cleric_ressurreicao"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Ressurreição."}); return
```

`handle_criar_armadilha`:
```python
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode criar armadilhas."}); return
```
→
```python
        if not _pode_hab_heroi(p, "rogue", "hero_rogue_criar_armadilha"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe criar armadilhas."}); return
```

`handle_veneno_rapido`:
```python
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode usar Veneno Rápido."}); return
```
→
```python
        if not _pode_hab_heroi(p, "rogue", "hero_rogue_veneno_rapido"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Veneno Rápido."}); return
```

- [ ] **Step 4: Rodar e ver passar**

Import direto: as duas novas + as da Task 1.
Expected: 0 falharam.

- [ ] **Step 5: Commit (partial staging)**

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# 6 hunks (4 clérigo + 2 ladino). Conferir vizinhança de cada.
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): itens concedem os milagres do clérigo e 2 habilidades do ladino

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Paladino (4 sustentadas) + Bardo (provocação) + upkeeps

**Files:**
- Modify: `server.py` (`handle_golpe_sagrado` ~11719, `handle_desativar_golpe_sagrado` ~11742, `handle_protetor` ~11751, `handle_desativar_protetor` ~11782, `handle_acao_livre_richard` ~11792, `_processar_manutencao_richard` ~11871, `handle_provocacao` ~11287, `_provocador` ~11322, `_processar_inicio_turno_luccas` ~15775)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicione após `test_hab_ladino_concedida`:

```python
def test_hab_paladino_concedida():
    print("\n[J3] Sustentadas do paladino concedidas por item")
    # Golpe Sagrado: ativa e desativa
    r, p = _turn_room_hero("warrior")
    asyncio.run(r.handle_golpe_sagrado("p1"))
    check("sem item: golpe sagrado recusado", not p.get("golpe_sagrado_ativo"))
    p["gear"]["weapon"] = _item_com_habilidade("hero_paladin_golpe_sagrado", id="esp_g")
    asyncio.run(r.handle_golpe_sagrado("p1"))
    check("com item: golpe sagrado ativo", p.get("golpe_sagrado_ativo") is True)
    asyncio.run(r.handle_desativar_golpe_sagrado("p1"))
    check("com item: golpe sagrado desativado", not p.get("golpe_sagrado_ativo"))
    # Protetor: ativa e desativa (alvo aliado)
    r2, p2 = _turn_room_hero("warrior")
    al = S.make_player("p2", "Aliado", "rogue", 1)
    r2.players["p2"] = al
    p2["pos"] = [1, 1]; al["pos"] = [2, 1]
    asyncio.run(r2.handle_protetor("p1", {"target_id": "p2"}))
    check("sem item: protetor recusado", not p2.get("protetor_ativo"))
    p2["gear"]["armor"] = _item_com_habilidade("hero_paladin_protetor", id="cota_pr")
    asyncio.run(r2.handle_protetor("p1", {"target_id": "p2"}))
    check("com item: protetor ativo", p2.get("protetor_ativo") is True)
    asyncio.run(r2.handle_desativar_protetor("p1"))
    check("com item: protetor desativado", not p2.get("protetor_ativo"))
    # Ação livre: conceder UMA não libera a OUTRA
    r3, p3 = _turn_room_hero("warrior")
    p3["hp"] = max(1, p3["max_hp"] - 5)
    p3["gear"]["ring1"] = _item_com_habilidade("hero_paladin_regeneracao_divina", id="anel_rg")
    asyncio.run(r3.handle_acao_livre_richard("p1", {"habilidade_id": "regeneracao_divina"}))
    check("com item: regeneração ativa", p3.get("regeneracao_ativa") is True)
    asyncio.run(r3.handle_acao_livre_richard("p1", {"habilidade_id": "guerreiro_luz"}))
    check("item de regeneração NÃO libera guerreiro da luz",
          not p3.get("guerreiro_luz_ativo") and not p3.get("gdl_ativo"))

def test_hab_bardo_concedida():
    print("\n[J4] Provocação concedida por item")
    r, p = _room_com_alvo()
    p["class_id"] = "warrior"
    m = r.monsters["m1"]
    asyncio.run(r.handle_provocacao("p1", {"target_id": "m1"}))
    check("sem item: provocação recusada", not m.get("provocado_por"))
    p["gear"]["ring1"] = _item_com_habilidade("hero_bard_provocacao", id="anel_pv")
    asyncio.run(r.handle_provocacao("p1", {"target_id": "m1"}))
    check("com item: monstro provocado", m.get("provocado_por") == "p1")
    check("_provocador reconhece o não-bardo", r._provocador(m) is not None)

def test_upkeep_habilidade_concedida():
    print("\n[J5] Upkeep cobra manutenção de habilidade concedida (fix da Fase I)")
    # Ladino: Detectar Armadilhas concedida a um guerreiro passa a custar sede
    r, p = _turn_room_hero("warrior")
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    asyncio.run(r.handle_detectar_armadilhas("p1", {}))
    check("detectar ativo", p.get("detectar_ativo") is True)
    sede0 = p["sede"]
    asyncio.run(r._processar_inicio_turno_luccas(p))
    check("upkeep do ladino cobrado", p["sede"] < sede0)
    # Paladino: Regeneração Divina concedida a um guerreiro tica no upkeep
    r2, p2 = _turn_room_hero("warrior")
    p2["gear"]["ring1"] = _item_com_habilidade("hero_paladin_regeneracao_divina", id="anel_rg")
    p2["hp"] = max(1, p2["max_hp"] - 5)
    asyncio.run(r2.handle_acao_livre_richard("p1", {"habilidade_id": "regeneracao_divina"}))
    hp0 = p2["hp"]
    asyncio.run(r2._processar_manutencao_richard(p2))
    check("upkeep do paladino rodou (curou ou cobrou)",
          p2["hp"] != hp0 or p2["fome"] < 10 or p2["sede"] < 10)
```

Registre no `if __name__ == "__main__":` após a linha da Task 2:
```python
    test_hab_paladino_concedida(); test_hab_bardo_concedida()
    test_upkeep_habilidade_concedida()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando as três.
Expected: FAIL — travas recusam; upkeeps não rodam para não-classe.

- [ ] **Step 3: Implementar em `server.py`**

3a. `handle_golpe_sagrado`:
```python
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar Golpe Sagrado."}); return
```
→
```python
        if not _pode_hab_heroi(p, "paladin", "hero_paladin_golpe_sagrado"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Golpe Sagrado."}); return
```

3b. `handle_desativar_golpe_sagrado` (uma linha só):
```python
        if not p or p.get("class_id") != "paladin" or not p.get("golpe_sagrado_ativo"): return
```
→
```python
        if not p or not _pode_hab_heroi(p, "paladin", "hero_paladin_golpe_sagrado") \
                or not p.get("golpe_sagrado_ativo"): return
```

3c. `handle_protetor`:
```python
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar Protetor."}); return
```
→
```python
        if not _pode_hab_heroi(p, "paladin", "hero_paladin_protetor"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Protetor."}); return
```

3d. `handle_desativar_protetor`:
```python
        if not p or p.get("class_id") != "paladin" or not p.get("protetor_ativo"): return
```
→
```python
        if not p or not _pode_hab_heroi(p, "paladin", "hero_paladin_protetor") \
                or not p.get("protetor_ativo"): return
```

3e. `handle_acao_livre_richard` — a trava passa a ser lida **depois** do `habilidade_id`, para que conceder uma não libere a outra. O trecho hoje é:
```python
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar esta habilidade."}); return

        habilidade_id = data.get("habilidade_id") if data else None
        if habilidade_id == "regeneracao_divina":
```
Troque por:
```python
        habilidade_id = data.get("habilidade_id") if data else None
        if habilidade_id not in ("regeneracao_divina", "guerreiro_luz"):
            await self.send_to(pid, {"type": "error", "msg": "Habilidade livre inválida."}); return
        if not _pode_hab_heroi(p, "paladin", f"hero_paladin_{habilidade_id}"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar esta habilidade."}); return

        if habilidade_id == "regeneracao_divina":
```
O `else:` final que hoje emite "Habilidade livre inválida." fica inalcançável mas inofensivo — **deixe-o como está** (remover mexeria em mais linhas do que o necessário).

3f. `_processar_manutencao_richard` (upkeep — cobre as 4 sustentadas):
```python
        if p.get("class_id") != "paladin" or not p.get("alive"): return
```
→
```python
        if not _tem_alguma_hab_heroi(p, "paladin", (
                "hero_paladin_golpe_sagrado", "hero_paladin_protetor",
                "hero_paladin_regeneracao_divina", "hero_paladin_guerreiro_luz",
        )) or not p.get("alive"): return
```

3g. `_processar_inicio_turno_luccas` (upkeep — **fix da Fase I**):
```python
        if p.get("class_id") != "rogue" or not p["alive"]:
            return
```
→
```python
        if not _tem_alguma_hab_heroi(p, "rogue", (
                "hero_rogue_detectar_armadilhas", "hero_rogue_esconder_sombras",
        )) or not p["alive"]:
            return
```

3h. `handle_provocacao`:
```python
        if p.get("class_id") != "bard":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Henrique pode usar Provocação."}); return
```
→
```python
        if not _pode_hab_heroi(p, "bard", "hero_bard_provocacao"):
            await self.send_to(pid, {"type": "error", "msg": "Você não sabe usar Provocação."}); return
```

3i. `_provocador` — hoje exige `class_id == "bard"`:
```python
        if (b and b.get("alive") and b.get("class_id") == "bard"
                and monstro.get("provocado_turnos", 0) > 0):
```
→
```python
        if (b and b.get("alive")
                and _pode_hab_heroi(b, "bard", "hero_bard_provocacao")
                and monstro.get("provocado_turnos", 0) > 0):
```

- [ ] **Step 4: Rodar e ver passar**

Import direto: as três novas + todas as anteriores (`[I*]` e `[J*]`).
Expected: 0 falharam. Rode também `python tools/test_guilda.py` e reporte a linha final.

- [ ] **Step 5: Commit (partial staging)**

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# 9 hunks. Conferir vizinhança de CADA um (o WIP do usuário é extenso nesta faixa).
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): itens concedem as sustentadas do paladino e a provocação do bardo

Corrige também a lacuna da Fase I: os upkeeps agora cobram a manutenção de
habilidades concedidas a heróis de outra classe.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Cliente + editor + teste de sincronia

**Files:**
- Modify: `game.js` (bloco de habilidades concedidas em `renderMyPanel`)
- Modify: `tools/editor_items_editor.js` (`GRANTED_HERO_IDS`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste de sincronia que falha**

Adicione após `test_upkeep_habilidade_concedida`:

```python
def test_sincronia_editor_servidor():
    print("\n[J6] Lista do editor em sincronia com o servidor")
    import re, os
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "tools", "editor_items_editor.js")
    src = open(caminho, encoding="utf-8").read()
    bloco = re.search(r"GRANTED_HERO_IDS\s*=\s*\[(.*?)\]", src, re.S)
    check("GRANTED_HERO_IDS encontrado no editor", bool(bloco))
    ids_js = set(re.findall(r'"([^"]+)"', bloco.group(1))) if bloco else set()
    ids_py = set(S.GameRoom.GRANTED_HERO_SKILLS.keys())
    faltam = ids_py - ids_js
    sobram = ids_js - ids_py
    check(f"editor não deixa nenhuma de fora (faltam: {sorted(faltam)})", not faltam)
    check(f"editor não lista id inexistente (sobram: {sorted(sobram)})", not sobram)
```

Registre no `if __name__ == "__main__":` após a linha da Task 3:
```python
    test_sincronia_editor_servidor()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando `m.test_sincronia_editor_servidor()`.
Expected: FAIL — o editor lista 3 ids, o servidor tem 14 (11 "faltam").

- [ ] **Step 3: Crescer a lista no editor**

Em `tools/editor_items_editor.js`, troque:
```javascript
  var GRANTED_HERO_IDS = ["hero_rogue_detectar_armadilhas",
                          "hero_rogue_esconder_sombras",
                          "hero_paladin_imposicao_maos"];
```
por:
```javascript
  // Mantida em sincronia com GameRoom.GRANTED_HERO_SKILLS (server.py) — há um
  // teste que compara as duas listas (test_editor_itens.py, seção [J6]).
  var GRANTED_HERO_IDS = ["hero_rogue_detectar_armadilhas",
                          "hero_rogue_esconder_sombras",
                          "hero_paladin_imposicao_maos",
                          "hero_cleric_cura", "hero_cleric_cura_area",
                          "hero_cleric_purificacao", "hero_cleric_ressurreicao",
                          "hero_rogue_criar_armadilha", "hero_rogue_veneno_rapido",
                          "hero_paladin_golpe_sagrado", "hero_paladin_protetor",
                          "hero_paladin_regeneracao_divina", "hero_paladin_guerreiro_luz",
                          "hero_bard_provocacao"];
```

- [ ] **Step 4: Despachos novos no cliente**

Em `game.js`, no bloco da Fase I:
```javascript
  for(const sk of (me.granted_hero_skills || [])){
    if(sk.granted_origem === 'rogue')        sl.appendChild(_rogueSkillBtn(me, sk));
    else if(sk.granted_origem === 'paladin') sl.appendChild(_paladinSkillBtn(me, sk));
  }
```
Troque por:
```javascript
  for(const sk of (me.granted_hero_skills || [])){
    if(sk.granted_origem === 'rogue')        sl.appendChild(_rogueSkillBtn(me, sk));
    else if(sk.granted_origem === 'paladin') sl.appendChild(_paladinSkillBtn(me, sk));
    else if(sk.granted_origem === 'cleric')  sl.appendChild(_clericSkillBtn(me, sk));
    else if(sk.granted_origem === 'bard')    sl.appendChild(_bardSkillBtn(me, sk));
  }
```

- [ ] **Step 5: Verificar**

Import direto: `m.test_sincronia_editor_servidor()` → 0 falharam.

Run: `node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js parse OK')"`
Expected: `game.js parse OK`

Run: `node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('editor parse OK')"`
Expected: `editor parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: PASS.

- [ ] **Step 6: Commit (partial staging — game.js está no WIP; o editor NÃO)**

```bash
git add tools/editor_items_editor.js tools/test_editor_itens.py
git diff -- game.js > /tmp/gj_all.patch
# montar /tmp/gj_mine.patch com o header + APENAS o hunk dos despachos
git apply --cached /tmp/gj_mine.patch
git diff --cached -- game.js
git commit -m "feat(itens): HUD e editor cobrem as 14 habilidades concedíveis

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Verificação isolada + docs + memória

**Files:**
- Modify: `CLAUDE.md`
- Modify (fora do repo): memória do projeto

- [ ] **Step 1: Rodar a suíte no estado COMMITADO isolado**

Foi essa verificação que revelou o gate inline na Fase I — não pule.

```bash
git worktree add --detach /tmp/lfh_verify_j HEAD
cd /tmp/lfh_verify_j
python tools/test_editor_itens.py
python tools/test_guilda.py
node tools/test_editor_items_logic.js
node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js OK')"
node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('editor OK')"
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_verify_j --force
```
Expected: `[J0]`–`[J6]` e `[I1]`–`[I6]` verdes, `test_guilda.py` sem falhas, node verde, parses OK. Pré-existentes conhecidos: `test_roteamento_itens.py` e 1 flaky em `test_devorador.py`.

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação após a nota da Fase I resumindo a Fase J: portão único `_pode_hab_heroi` (+ `_tem_alguma_hab_heroi` para os upkeeps) com retrofit das 3 travas da Fase I; 11 habilidades novas (4 milagres do clérigo, criar armadilha + veneno rápido do ladino, 4 sustentadas do paladino, provocação do bardo) → mapa de 14; gate por `habilidade_id` em `handle_acao_livre_richard` (conceder uma não libera a outra); `_provocador` aceita provocador não-bardo; **fix da lacuna da Fase I** (os upkeeps `_processar_inicio_turno_luccas` e `_processar_manutencao_richard` agora cobram manutenção de habilidade concedida); cliente com 2 despachos novos (`_clericSkillBtn`/`_bardSkillBtn`); editor com 14 ids + teste de sincronia `[J6]`. Liste o Tier 3 que fica de fora e por quê. Cite os testes `[J0]`–`[J6]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-27-fase-j-habilidades-heroi-concedidas.md
git commit -m "docs(itens): registra a Fase J (habilidades de herói concedidas)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Atualizar memória**

Crie `memory/fase-j-habilidades-heroi-concedidas.md` (tipo `project`): o que foi feito, estado (branch `feat/instrumentos-bardo-fase5`, não mergeada), contagem de checks, o fix dos upkeeps, e o Tier 3 que resta. Adicione a linha-índice no topo de `MEMORY.md`, linkando `[[editor-itens-fase-i-habilidades-concedidas]]`.

- [ ] **Step 5: Follow-up manual (usuário)**

Smoke test in-app: `python server.py` → editor → criar (a) um anel concedendo **Cura**, (b) uma armadura concedendo **Protetor** e (c) uma bota concedendo **Criar Armadilha**. Marcar "Baús / recompensas". Em jogo, com um guerreiro: equipar e conferir os botões no HUD (painel do clérigo/paladino/ladino aparecendo só com a habilidade concedida), usar cada uma, e confirmar que as sustentadas cobram manutenção no início do turno.

---

## Self-Review (autor do plano)

- **Cobertura do spec:** helpers DRY + retrofit (T1) ✓; mapa 3→14 (T1) ✓; 6 travas Tier 1 (T2) ✓; 9 sites Tier 2 incluindo os 2 upkeeps e `_provocador` (T3) ✓; gate por `habilidade_id` (T3, 3e) ✓; fix da lacuna da Fase I (T3, 3g + teste [J5]) ✓; cliente 2 despachos (T4) ✓; editor 14 ids (T4) ✓; teste de sincronia (T4, [J6]) ✓; verificação isolada + docs + memória (T5) ✓.
- **Contagem de sites:** 6 (T2) + 9 (T3) = 15 edições, das quais 14 são "travas" no sentido do spec — `_provocador` é a 15ª (helper de bônus, não trava de handler). Consistente com o spec, que o lista à parte.
- **Ordem de dependência:** T1 define `_pode_hab_heroi`/`_tem_alguma_hab_heroi` usados por T2/T3, e o mapa lido por T4 ([J6]). Respeitada.
- **Helpers de teste reusados:** `_item_com_habilidade`, `_turn_room_hero` e `_gear_room` vêm da Fase I; `_room_com_alvo` é pré-existente. Todos já no arquivo.
- **Risco:** `_provocador` e os upkeeps são chamados em laços de combate/turno — a Task 3 pede rodar `test_guilda.py` e a suíte inteira. A Task 5 repete isolado.
- **Sem placeholders:** todos os passos têm código/comando concreto.
