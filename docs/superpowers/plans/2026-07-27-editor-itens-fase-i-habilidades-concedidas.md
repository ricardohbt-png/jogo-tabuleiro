# Editor de Itens — Fase I: Habilidades concedidas por item — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer `granted_ability` virar poder real — um item equipado (arma/armadura/escudo/anel/bota) concede técnicas ativáveis e especializações passivas da Guilda, mais uma amostra de 3 habilidades de herói.

**Architecture:** Um helper novo (`_habilidades_concedidas`) lê os `granted_ability` do `gear` equipado. Dois portões de uma linha (`tem_tecnica_equipada`, `tem_espec`) passam a aceitá-lo, o que destrava todo o motor da Guilda sem tocar nos efeitos. Três handlers de herói têm a trava de classe relaxada pelo mesmo padrão. O cliente ganha os botões: técnicas concedidas entram no laço do 4º slot (rótulo "ITEM") e as habilidades de herói vêm prontas do servidor via um campo novo em `push_state`.

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`game.js`, `src/gameState.js`, `tools/editor_items_*.js`), testes: `python tools/test_editor_itens.py` e `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de partial staging — LER ANTES DAS TASKS 1, 2, 3 e 5

O usuário reworka `server.py`, `game.js` e `src/gameState.js` em paralelo (WIP "Barreira Arcana" + lojas por cidade). **NUNCA** `git add` nesses arquivos, nem `git add -A`.

```bash
git add <arquivos de teste / editor_items_*.js>   # seguros, fora do WIP
git diff -- <arquivo> > /tmp/all.patch            # SEUS hunks + o WIP
# Leia /tmp/all.patch, identifique os @@ hunks QUE VOCÊ escreveu e monte
# /tmp/mine.patch = header (4 linhas: diff/index/---/+++) + APENAS esses hunks.
git apply --cached /tmp/mine.patch
git diff --cached -- <arquivo>                    # confira a olho: só o seu código
```

Se vazar qualquer linha do WIP: `git reset <arquivo>` e refaça. `git add -p` é interativo e **não funciona** aqui. Um patch por arquivo.

**Esta fase toca várias regiões de `server.py`** (portões ~1672; handlers de herói ~11653/~15601/~15646; `push_state` ~20803; validação ~22000+). Extraia com cuidado, conferindo a vizinhança de cada hunk.

## ⚠️ A suíte aborta no working tree (pré-existente)

`python tools/test_editor_itens.py` CRASHA na seção `[7]` por causa do WIP de lojas por cidade em `handle_shop_buy`. **Não é seu, não conserte, não toque em `handle_shop_buy`.** Verifique as seções novas importando o módulo:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location('t','tools/test_editor_itens.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.test_habilidade_concedida_helper()
print(f'{m.PASS} passaram, {m.FAIL} falharam')
"
```

(No HEAD commitado, sem o WIP, a suíte roda inteira — é assim que a Task 6 verifica.)

---

## File Structure

- **Modify:** `server.py` — `_habilidades_concedidas` + 2 portões; 3 travas de herói + mensagens; `_granted_hero_skills` + injeção em `push_state`; `_granted_ability_valida` + 3 validadores.
- **Modify:** `tools/test_editor_itens.py` — seção `[I1]`–`[I6]`.
- **Modify:** `tools/editor_items_editor.js` — seletor de habilidade nos 5 forms, opções filtradas/agrupadas.
- **Modify:** `src/gameState.js` — getter `tecnicasConcedidasPorItem`.
- **Modify:** `game.js` — botões de técnica concedida + botões de habilidade de herói concedida.
- **Modify:** `CLAUDE.md` — nota da Fase I.

---

## Task 1: Servidor — helper + portões da Guilda

**Files:**
- Modify: `server.py` (junto de `tem_espec`/`tem_tecnica_equipada`, ~1672-1680)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione ao final (antes do bloco `if __name__ == "__main__":`):

```python
def _item_com_habilidade(aid, **over):
    """Peça de gear mínima que concede uma habilidade."""
    base = {"id": "peca_hab", "name": "Peça Encantada", "granted_ability": aid}
    base.update(over); return base

def test_habilidade_concedida_helper():
    print("\n[I1] _habilidades_concedidas varre o gear equipado")
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem itens: conjunto vazio", S._habilidades_concedidas(p) == set())
    p["gear"]["weapon"] = _item_com_habilidade("guild_brutalidade")
    check("coleta da arma", S._habilidades_concedidas(p) == {"guild_brutalidade"})
    p["gear"]["ring1"] = _item_com_habilidade("guild_guerreiro_mira_3", id="anel_x")
    check("coleta de vários slots",
          S._habilidades_concedidas(p) == {"guild_brutalidade", "guild_guerreiro_mira_3"})
    p["gear"]["armor"] = {"id": "sem_hab", "name": "Cota"}
    check("ignora item sem granted_ability",
          S._habilidades_concedidas(p) == {"guild_brutalidade", "guild_guerreiro_mira_3"})
    p["gear"]["boots"] = _item_com_habilidade(None, id="bota_x")
    check("ignora granted_ability vazio",
          S._habilidades_concedidas(p) == {"guild_brutalidade", "guild_guerreiro_mira_3"})
    check("gear ausente não quebra", S._habilidades_concedidas({}) == set())

def test_portoes_concedidos():
    print("\n[I2] Portões aceitam habilidade concedida por item")
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem item: técnica não equipada", not S.tem_tecnica_equipada(p, "brutalidade"))
    check("sem item: sem especialização", not S.tem_espec(p, "guerreiro_mira_3"))
    p["gear"]["weapon"] = _item_com_habilidade("guild_brutalidade")
    check("com item: técnica liberada", S.tem_tecnica_equipada(p, "brutalidade"))
    check("item de técnica não libera especialização", not S.tem_espec(p, "guerreiro_mira_3"))
    p["gear"]["ring1"] = _item_com_habilidade("guild_guerreiro_mira_3", id="anel_x")
    check("com item: especialização liberada", S.tem_espec(p, "guerreiro_mira_3"))
    p["gear"]["weapon"] = None
    check("desequipar remove a técnica", not S.tem_tecnica_equipada(p, "brutalidade"))
    check("a outra peça continua valendo", S.tem_espec(p, "guerreiro_mira_3"))

def test_tecnica_concedida_uso():
    print("\n[I3] Técnica concedida por item é usável (efeito+custo+recarga)")
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["gear"]["weapon"] = _item_com_habilidade("guild_brutalidade")
    p["fome"], p["sede"] = 10, 10
    asyncio.run(r.handle_usar_tecnica("p1", "brutalidade"))
    check("efeito aplicado (+2 dano de arma)", p.get("tecnica_buff_dano_arma") == 2)
    check("custo debitado", p["fome"] < 10 and p["sede"] < 10)
    check("entrou em recarga", r.tecnica_restante(p, "brutalidade") > 0)
    p["tecnica_buff_dano_arma"] = 0
    asyncio.run(r.handle_usar_tecnica("p1", "brutalidade"))
    check("2ª ativação recusada pela recarga", p.get("tecnica_buff_dano_arma") == 0)

def test_espec_concedida_efeito():
    print("\n[I4] Especialização concedida altera o efeito real")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    check("sem item: Mira III não dá bônus", r._mira_dano_bonus(p) == 0)
    p["gear"]["ring1"] = _item_com_habilidade("guild_guerreiro_mira_3", id="anel_x")
    check("com item: Mira III dá +2 de dano", r._mira_dano_bonus(p) == 2)
    p["gear"]["ring1"] = None
    check("desequipar volta a 0", r._mira_dano_bonus(p) == 0)
```

Registre no `if __name__ == "__main__":`, logo APÓS a linha `test_veneno_msg_penalidade()`:

```python
    test_habilidade_concedida_helper(); test_portoes_concedidos()
    test_tecnica_concedida_uso(); test_espec_concedida_efeito()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando as 4 funções.
Expected: FAIL — `_habilidades_concedidas` não existe (AttributeError).

- [ ] **Step 3: Implementar em `server.py`**

Localize as funções `tem_espec` e `tem_tecnica_equipada` (module-level, ~1672). Insira o helper **imediatamente antes** de `tem_espec` e reescreva os dois portões:

```python
def _habilidades_concedidas(player):
    """Ids de `granted_ability` dos itens EQUIPADOS (Fase I). Varre todos os slots
    de gear: hoje só arma/armadura/escudo/anel/bota carregam o campo, mas assim
    elmo/acessórios futuros funcionam sem mexer aqui."""
    out = set()
    for peca in (player.get("gear") or {}).values():
        if isinstance(peca, dict):
            aid = peca.get("granted_ability")
            if aid:
                out.add(aid)
    return out

def tem_espec(player, espec_id):
    """True se o jogador possui a especialização comprada (Fase 1+) OU se um item
    equipado a concede (Fase I)."""
    if espec_id in player.get("guild_owned", {}).get("especializacoes", []):
        return True
    return f"guild_{espec_id}" in _habilidades_concedidas(player)

def tem_tecnica_equipada(player, tecnica_id):
    """True se a técnica está no 4º slot equipado do jogador (normal ou exclusiva)
    OU se um item equipado a concede (Fase I)."""
    eq = player.get("guild_equip", {})
    if tecnica_id in (list(eq.get("tecnicas", [])) + [eq.get("tecnica"), eq.get("tecnica_exclusiva")]):
        return True
    return f"guild_{tecnica_id}" in _habilidades_concedidas(player)
```

- [ ] **Step 4: Rodar e ver passar**

Import direto chamando as 4 funções.
Expected: `[I1]`–`[I4]` verdes (0 falharam).

Rode também uma checagem de regressão (os portões são muito usados):
```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location('t','tools/test_editor_itens.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.test_validacao(); m.test_merge(); m.test_validacao_veneno(); m.test_veneno_merge()
m.test_habilidade_concedida_helper(); m.test_portoes_concedidos()
m.test_tecnica_concedida_uso(); m.test_espec_concedida_efeito()
print(f'{m.PASS} passaram, {m.FAIL} falharam')
"
```
Expected: 0 falharam. Rode também `python tools/test_guilda.py` — ele exercita os portões da Guilda; anote o resultado (se já falhava antes da sua mudança, é pré-existente: confirme rodando `git stash` **NÃO** — apenas reporte o resultado ao controlador).

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunk único em `server.py` (helper + 2 portões, contíguos).

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com o hunk dos portões, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): itens equipados concedem técnicas e especializações da Guilda

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — 3 habilidades de herói + payload p/ o cliente

**Files:**
- Modify: `server.py` (`handle_imposicao_maos` ~11653; `handle_detectar_armadilhas` ~15601; `handle_esconder_sombras` ~15646; novo `_granted_hero_skills`; `push_state` ~20803)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_itens.py`, adicione após `test_espec_concedida_efeito`:

```python
def _turn_room_hero(cls_id="warrior"):
    """Sala com um herói da classe dada, turno ativo (para handlers de habilidade)."""
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Heroi", cls_id, 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None
    p["fome"], p["sede"] = 10, 10
    return r, p

def test_habilidades_heroi_concedidas():
    print("\n[I5] Amostra de habilidades de herói concedidas por item")
    # Detectar Armadilhas (ladino) num guerreiro
    r, p = _turn_room_hero("warrior")
    asyncio.run(r.handle_detectar_armadilhas("p1", {}))
    check("sem item: detectar recusado", not p.get("detectar_ativo"))
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    asyncio.run(r.handle_detectar_armadilhas("p1", {}))
    check("com item: detectar ativado", p.get("detectar_ativo") is True)
    # Esconder nas Sombras (ladino) num clérigo
    r2, p2 = _turn_room_hero("cleric")
    asyncio.run(r2.handle_esconder_sombras("p2_inexistente", {}))   # no-op seguro
    asyncio.run(r2.handle_esconder_sombras("p1", {}))
    check("sem item: esconder recusado", not p2.get("invisivel_sombras"))
    p2["gear"]["boots"] = _item_com_habilidade("hero_rogue_esconder_sombras", id="bota_e")
    asyncio.run(r2.handle_esconder_sombras("p1", {}))
    check("com item: esconder tentado (ativo ou teste falhou)",
          "invisivel_sombras" in p2 or p2.get("bonus_action_used"))
    # Imposição das Mãos (paladino) num guerreiro, curando um aliado adjacente
    r3, p3 = _turn_room_hero("warrior")
    aliado = S.make_player("p2", "Aliado", "cleric", 1)
    r3.players["p2"] = aliado
    p3["pos"] = [1, 1]; aliado["pos"] = [2, 1]
    aliado["hp"] = 1
    asyncio.run(r3.handle_imposicao_maos("p1", {"target_id": "p2"}))
    check("sem item: imposição recusada", aliado["hp"] == 1)
    p3["gear"]["armor"] = _item_com_habilidade("hero_paladin_imposicao_maos", id="cota_i")
    asyncio.run(r3.handle_imposicao_maos("p1", {"target_id": "p2"}))
    check("com item: aliado curado", aliado["hp"] > 1)

def test_mensagens_sem_richard():
    print("\n[I5b] Mensagens da Imposição não citam Richard")
    r, p = _turn_room_hero("warrior")
    erros = []
    async def se(pid, msg): erros.append(msg.get("msg", ""))
    r.send_to = se
    p["gear"]["armor"] = _item_com_habilidade("hero_paladin_imposicao_maos", id="cota_i")
    asyncio.run(r.handle_imposicao_maos("p1", {"target_id": "p1"}))   # curar a si mesmo
    check("erro de auto-cura não cita Richard",
          erros and all("Richard" not in e for e in erros))

def test_granted_hero_skills_payload():
    print("\n[I5c] push_state expõe as habilidades de herói concedidas")
    p = S.make_player("p1", "Victor", "warrior", 0)
    r = _gear_room()
    check("sem item: lista vazia", r._granted_hero_skills(p) == [])
    p["gear"]["ring1"] = _item_com_habilidade("hero_rogue_detectar_armadilhas", id="anel_d")
    skills = r._granted_hero_skills(p)
    check("com item: 1 habilidade", len(skills) == 1)
    check("traz o id real da skill", skills and skills[0].get("id") == "detectar_armadilhas")
    check("marca a classe de origem", skills and skills[0].get("granted_origem") == "rogue")
```

Registre no `if __name__ == "__main__":`, após a linha da Task 1:

```python
    test_habilidades_heroi_concedidas(); test_mensagens_sem_richard()
    test_granted_hero_skills_payload()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando as 3 funções.
Expected: FAIL — as travas de classe recusam mesmo com o item; `_granted_hero_skills` não existe.

- [ ] **Step 3: Implementar em `server.py`**

3a. **`handle_detectar_armadilhas`** (~15601). Troque:
```python
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode detectar armadilhas."}); return
```
por:
```python
        if p.get("class_id") != "rogue" and \
                "hero_rogue_detectar_armadilhas" not in _habilidades_concedidas(p):
            await self.send_to(pid, {"type": "error",
                "msg": "Você não sabe detectar armadilhas (habilidade do Ladino)."}); return
```

3b. **`handle_esconder_sombras`** (~15646). Troque:
```python
        if p.get("class_id") != "rogue":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Luccas pode usar esta habilidade."}); return
```
por:
```python
        if p.get("class_id") != "rogue" and \
                "hero_rogue_esconder_sombras" not in _habilidades_concedidas(p):
            await self.send_to(pid, {"type": "error",
                "msg": "Você não sabe se esconder nas sombras (habilidade do Ladino)."}); return
```

3c. **`handle_imposicao_maos`** (~11653). Troque a trava:
```python
        if p.get("class_id") != "paladin":
            await self.send_to(pid, {"type": "error", "msg": "Apenas Richard pode usar esta habilidade."}); return
```
por:
```python
        if p.get("class_id") != "paladin" and \
                "hero_paladin_imposicao_maos" not in _habilidades_concedidas(p):
            await self.send_to(pid, {"type": "error",
                "msg": "Você não sabe usar Imposição das Mãos (habilidade do Paladino)."}); return
```
E generalize as outras duas mensagens que citam "Richard" no mesmo handler:
```python
            await self.send_to(pid, {"type": "error", "msg": "Richard não pode curar a si mesmo com esta habilidade."}); return
```
→
```python
            await self.send_to(pid, {"type": "error",
                "msg": "Você não pode curar a si mesmo com esta habilidade."}); return
```
e
```python
            await self.send_to(pid, {"type": "error", "msg": "Aliado deve estar adjacente a Richard."}); return
```
→
```python
            await self.send_to(pid, {"type": "error",
                "msg": "O aliado deve estar adjacente a você."}); return
```

3d. **Novo método `_granted_hero_skills`** — adicione na classe `GameRoom`, logo antes de `push_state` (ou perto de outros helpers de payload):

```python
    # Amostra da Fase I: habilidades de herói que um item pode conceder.
    # id do catálogo do editor -> (classe de origem, id real da skill)
    GRANTED_HERO_SKILLS = {
        "hero_rogue_detectar_armadilhas": ("rogue", "detectar_armadilhas"),
        "hero_rogue_esconder_sombras":    ("rogue", "esconder_sombras"),
        "hero_paladin_imposicao_maos":    ("paladin", "imposicao_maos"),
    }

    def _granted_hero_skills(self, p):
        """Definições reais das habilidades de herói concedidas por itens equipados
        (Fase I), para o cliente renderizar o botão. Cada entrada é a skill da classe
        de origem + 'granted_origem'. Evita duplicar nomes/custos no cliente."""
        out = []
        concedidas = _habilidades_concedidas(p)
        for aid, (cls_id, skill_id) in self.GRANTED_HERO_SKILLS.items():
            if aid not in concedidas:
                continue
            if p.get("class_id") == cls_id:
                continue   # já é da classe: o painel normal já mostra
            skill = next((s for s in CLASSES.get(cls_id, {}).get("skills", [])
                          if s.get("id") == skill_id), None)
            if skill:
                out.append(dict(skill, granted_origem=cls_id))
        return out
```

3e. **Injeção no `push_state`** (~20803). Troque:
```python
        players_state = [dict(p, initiative=self.initiative_value(p),
                              vision_radius=self._get_raio_visao(p))
                         for p in self.players.values()]
```
por:
```python
        players_state = [dict(p, initiative=self.initiative_value(p),
                              vision_radius=self._get_raio_visao(p),
                              granted_hero_skills=self._granted_hero_skills(p))
                         for p in self.players.values()]
```

- [ ] **Step 4: Rodar e ver passar**

Import direto chamando as 3 funções novas + as 4 da Task 1.
Expected: `[I5]`, `[I5b]`, `[I5c]` verdes; `[I1]`–`[I4]` continuam verdes.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks: 3 travas de herói (+2 mensagens), `_granted_hero_skills`+`GRANTED_HERO_SKILLS`, e a linha do `push_state`. São regiões distantes — extraia cada hunk conferindo a vizinhança.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): itens concedem 3 habilidades de herói (amostra da Fase I)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — validação de `granted_ability`

**Files:**
- Modify: `server.py` (novo `_granted_ability_valida`; `_validate_custom_weapon`, `_validate_custom_armor`, `_validate_custom_accessory`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione em `tools/test_editor_itens.py` após `test_granted_hero_skills_payload`:

```python
def test_validacao_granted_ability():
    print("\n[I6] Validação de granted_ability")
    check("aceita técnica da Guilda", S._granted_ability_valida("guild_brutalidade"))
    check("aceita especialização", S._granted_ability_valida("guild_guerreiro_mira_3"))
    check("aceita habilidade de herói da amostra",
          S._granted_ability_valida("hero_rogue_detectar_armadilhas"))
    check("rejeita id desconhecido", not S._granted_ability_valida("guild_nao_existe"))
    check("rejeita herói fora da amostra",
          not S._granted_ability_valida("hero_cleric_ressurreicao"))
    check("rejeita None", not S._granted_ability_valida(None))
    ok, it = S._validate_custom_item(sample(id="arma_hab", granted_ability="guild_brutalidade"))
    check("arma preserva id suportado", ok and it.get("granted_ability") == "guild_brutalidade")
    ok2, it2 = S._validate_custom_item(sample(id="arma_hab2", granted_ability="xpto"))
    check("arma descarta id nao suportado", ok2 and it2.get("granted_ability") is None)
    ok3, it3 = S._validate_custom_item(armor_sample(id="cota_hab", granted_ability="guild_brutalidade"))
    check("armadura preserva id suportado", ok3 and it3.get("granted_ability") == "guild_brutalidade")
    ok4, it4 = S._validate_custom_item(armor_sample(id="cota_hab2", granted_ability="xpto"))
    check("armadura descarta id nao suportado", ok4 and it4.get("granted_ability") is None)
    ok5, it5 = S._validate_custom_item(accessory_sample(id="anel_hab",
        granted_ability="hero_paladin_imposicao_maos"))
    check("acessorio preserva id suportado",
          ok5 and it5.get("granted_ability") == "hero_paladin_imposicao_maos")
    ok6, it6 = S._validate_custom_item(accessory_sample(id="anel_hab2", granted_ability="xpto"))
    check("acessorio descarta id nao suportado", ok6 and it6.get("granted_ability") is None)
```

Registre no `if __name__ == "__main__":` após a linha da Task 2:
```python
    test_validacao_granted_ability()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto.
Expected: FAIL — `_granted_ability_valida` não existe.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione o helper na região de itens custom, logo antes de `_validate_custom_item`:

```python
def _granted_ability_valida(aid):
    """True se o id de granted_ability é suportado pela Fase I: técnica ou
    especialização da Guilda (prefixo guild_), ou uma das habilidades de herói da
    amostra. Ids fora disso seriam metadado morto — a validação os descarta."""
    if not aid or not isinstance(aid, str):
        return False
    if aid in GameRoom.GRANTED_HERO_SKILLS:
        return True
    if aid.startswith("guild_"):
        entry = GUILD_CATALOG.get(aid[len("guild_"):])
        return bool(entry) and entry.get("categoria") in ("tecnica", "especializacao")
    return False
```

3b. Nos **três** validadores, troque a linha que grava o campo. Ela hoje é idêntica nos três:
```python
        "granted_ability": (str(raw["granted_ability"]) if raw.get("granted_ability") else None),
```
Troque (nas três ocorrências — `_validate_custom_weapon`, `_validate_custom_armor`, `_validate_custom_accessory`) por:
```python
        "granted_ability": (str(raw["granted_ability"])
                            if _granted_ability_valida(raw.get("granted_ability")) else None),
```

- [ ] **Step 4: Rodar e ver passar**

Import direto chamando `m.test_validacao_granted_ability()` + as seções anteriores.
Expected: `[I6]` verde; nada regride.

- [ ] **Step 5: Commit (partial staging)**

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): valida granted_ability contra o conjunto suportado

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Editor — seletor de habilidade nos 5 tipos de item

**Files:**
- Modify: `tools/editor_items_editor.js`

Sem teste headless. Verificação: parse + node verde. Leia o arquivo antes para confirmar `abilityOptions`, `renderArmorForm`, `renderAccessoryForm`, `seccao`/`campo`/`esc`, `draft`. Se algo diferir, pare e reporte NEEDS_CONTEXT.

- [ ] **Step 1: Filtrar e agrupar as opções**

Substitua a função `abilityOptions()` (hoje devolve `{id, name}` de todas as habilidades `heroi`/`guilda`) por uma versão que devolve grupos:

```javascript
  // Fase I: só habilidades que o motor realmente concede — técnicas e
  // especializações da Guilda, e a amostra de habilidades de herói.
  var GRANTED_HERO_IDS = ["hero_rogue_detectar_armadilhas",
                          "hero_rogue_esconder_sombras",
                          "hero_paladin_imposicao_maos"];
  function abilityGroups() {
    var libs = (window.EDITOR_CATALOG || {}).monster_abilities || [];
    var tec = [], esp = [], her = [];
    libs.forEach(function (a) {
      if (a.source === "guilda" && a.guild_category === "tecnica") tec.push(a);
      else if (a.source === "guilda" && a.guild_category === "especializacao") esp.push(a);
      else if (a.source === "heroi" && GRANTED_HERO_IDS.indexOf(a.id) >= 0) her.push(a);
    });
    return [["Técnicas da Guilda", tec], ["Especializações da Guilda", esp],
            ["Habilidades de Herói", her]];
  }
  // Campo reusado pelos 5 formulários de item equipável.
  function campoHabilidade() {
    var grupos = abilityGroups().map(function (g) {
      if (!g[1].length) return "";
      return '<optgroup label="' + esc(g[0]) + '">' + g[1].map(function (a) {
        return '<option value="' + esc(a.id) + '"' +
          (a.id === draft.granted_ability ? " selected" : "") + '>' + esc(a.name) + '</option>';
      }).join("") + '</optgroup>';
    }).join("");
    return campo("Habilidade", '<select id="ie-abil"><option value=""' +
      (draft.granted_ability ? "" : " selected") + '>— nenhuma —</option>' + grupos + '</select>');
  }
```

- [ ] **Step 2: Usar o campo compartilhado no form de armas**

No `renderForm` (form de armas), a seção de habilidade hoje monta o `<select>` inline usando `abilityOptions()`. Substitua o corpo dessa `seccao` por:

```javascript
      seccao("Habilidade concedida (ativa ao equipar)", campoHabilidade()),
```
E remova a linha `var abil = abilityOptions();` (agora sem uso) do início de `renderForm`.

- [ ] **Step 3: Adicionar a seção em armaduras/escudos**

Em `renderArmorForm`, adicione uma nova seção logo ANTES da seção "Restrição de classe":

```javascript
      seccao("Habilidade concedida (ativa ao equipar)", campoHabilidade()),
```

- [ ] **Step 4: Adicionar a seção em anéis/botas**

Em `renderAccessoryForm`, adicione a mesma seção logo ANTES da seção "Restrição de classe":

```javascript
      seccao("Habilidade concedida (ativa ao equipar)", campoHabilidade()),
```

- [ ] **Step 5: Ler o campo nos dois leitores novos**

`currentDraftFromForm` (armas) já faz `draft.granted_ability = g("ie-abil").value;`. Adicione a mesma leitura, **de forma defensiva**, em `currentArmorDraftFromForm` e `currentAccessoryDraftFromForm` (logo antes do `return draft;` de cada uma):

```javascript
    var ab = g("ie-abil"); if (ab) draft.granted_ability = ab.value;
```

- [ ] **Step 6: Verificar e commitar**

Run: `node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('parse OK')"`
Expected: `parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: PASS.

```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): seletor de habilidade concedida nos 5 tipos de item equipável

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Cliente — botões das habilidades concedidas

**Files:**
- Modify: `src/gameState.js` (getter novo)
- Modify: `game.js` (laço do 4º slot + bloco de habilidades de herói)

**Ambos os arquivos têm WIP do usuário** — leia a receita de partial staging no topo e faça **um patch por arquivo**.

- [ ] **Step 1: Getter em `src/gameState.js`**

Adicione junto dos outros getters da Guilda (procure `tecnicaRestante` / `guildEquipOf` no objeto exportado e adicione a função perto da definição deles):

```javascript
  // Fase I: técnicas concedidas por itens equipados (ids SEM o prefixo guild_).
  function tecnicasConcedidasPorItem(player) {
    var out = [];
    var gear = (player && player.gear) || {};
    Object.keys(gear).forEach(function (k) {
      var it = gear[k];
      var aid = it && it.granted_ability;
      if (aid && aid.indexOf("guild_") === 0) {
        var tid = aid.slice(6);
        if (out.indexOf(tid) < 0) out.push(tid);
      }
    });
    return out;
  }
```
E exporte-a no objeto público do módulo (junto de `tecnicaRestante`/`guildEquipOf`).

- [ ] **Step 2: Técnicas concedidas no laço do 4º slot (`game.js`)**

Localize (~11969):
```javascript
  const _tecEq  = GS.guildEquipOf(me.id);
  const _tecIds = (_tecEq.tecnicas || []).filter(Boolean);
  for(const tid of _tecIds){
```
Substitua por:
```javascript
  const _tecEq  = GS.guildEquipOf(me.id);
  // Fase I: técnicas concedidas por itens equipados entram no mesmo laço
  // (rótulo "ITEM"); a recarga é compartilhada com a da Guilda pelo id.
  const _tecItem = GS.tecnicasConcedidasPorItem(me);
  const _tecIds = (_tecEq.tecnicas || []).filter(Boolean)
                    .concat(_tecItem.filter(t => !(_tecEq.tecnicas || []).includes(t)));
  for(const tid of _tecIds){
```

- [ ] **Step 3: Rótulo "ITEM" (mesmo laço, poucas linhas abaixo)**

Localize, dentro do `btn.innerHTML` do mesmo laço:
```javascript
        <div class="skill-name">${abilityIconHtml(cat, cat.icon||'⚔️')} ${cat.nome} <small style="color:var(--gold);font-size:.58rem;">${cat.automatica ? 'AUTOMÁTICA' : 'GUILDA'}</small>${estado}</div>
```
Substitua por:
```javascript
        <div class="skill-name">${abilityIconHtml(cat, cat.icon||'⚔️')} ${cat.nome} <small style="color:var(--gold);font-size:.58rem;">${cat.automatica ? 'AUTOMÁTICA' : (_tecItem.includes(tid) ? 'ITEM' : 'GUILDA')}</small>${estado}</div>
```

- [ ] **Step 4: Botões das habilidades de herói concedidas (`game.js`)**

O laço principal do HUD itera `me.skills` e despacha por classe — uma habilidade concedida não está em `me.skills`, então precisa de um bloco próprio. Adicione **logo após o fim desse laço** (imediatamente antes do bloco `// ── Técnica(s) da Guilda equipada(s)`):

```javascript
  // ── Fase I: habilidades de herói concedidas por item (renderiza o botão da
  // classe de origem; o servidor manda a definição real em granted_hero_skills) ──
  for(const sk of (me.granted_hero_skills || [])){
    if(sk.granted_origem === 'rogue')        sl.appendChild(_rogueSkillBtn(me, sk));
    else if(sk.granted_origem === 'paladin') sl.appendChild(_paladinSkillBtn(me, sk));
  }
```

**Antes de escrever**, leia `_rogueSkillBtn` e `_paladinSkillBtn` e confirme que só leem campos genéricos do jogador (`me.fome`, `me.sede`, `me.detectar_ativo`, `me.invisivel_sombras`, `sk.*`). Se algum deles depender de estado exclusivo da classe (ex.: campo que só existe no ladino), **pare e reporte DONE_WITH_CONCERNS** descrevendo o acoplamento em vez de forçar.

- [ ] **Step 5: Verificar**

Run: `node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js parse OK')"`
Expected: `game.js parse OK`

Run: `node -e "new Function(require('fs').readFileSync('src/gameState.js','utf8')); console.log('gameState.js parse OK')"`
Expected: `gameState.js parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: PASS (inalterado).

- [ ] **Step 6: Commit (partial staging — DOIS patches, um por arquivo)**

```bash
git diff -- src/gameState.js > /tmp/gs_all.patch
# montar /tmp/gs_mine.patch com o header + APENAS o hunk do getter (e o do export)
git apply --cached /tmp/gs_mine.patch
git diff -- game.js > /tmp/gj_all.patch
# montar /tmp/gj_mine.patch com o header + APENAS os hunks do 4º slot e do bloco novo
git apply --cached /tmp/gj_mine.patch
git diff --cached -- src/gameState.js game.js   # conferir: só o código da Fase I
git commit -m "feat(itens): HUD mostra as habilidades concedidas por item

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Verificação isolada + docs + memória

**Files:**
- Modify: `CLAUDE.md`
- Modify (fora do repo): memória do projeto

- [ ] **Step 1: Rodar a suíte no estado COMMITADO isolado**

```bash
git worktree add --detach /tmp/lfh_verify_i HEAD
cd /tmp/lfh_verify_i
python tools/test_editor_itens.py
python tools/test_guilda.py
node tools/test_editor_items_logic.js
node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js OK')"
node -e "new Function(require('fs').readFileSync('src/gameState.js','utf8')); console.log('gameState.js OK')"
node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('editor OK')"
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_verify_i --force
```
Expected: `[I1]`–`[I6]` verdes em `test_editor_itens.py`, node verde, 3 parses OK. **`test_guilda.py` é o teste mais exposto a esta fase** (exercita os portões) — se falhar, compare com o estado anterior (`git stash` NÃO; use outro worktree em `HEAD~N`) antes de concluir que é regressão. Pré-existentes conhecidos: `test_roteamento_itens.py` e 1 flaky em `test_devorador.py`.

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação após a nota da Fase H resumindo a Fase I: `granted_ability` deixa de ser metadado; `_habilidades_concedidas` (varre todo o gear) + os 2 portões de uma linha (`tem_espec`, `tem_tecnica_equipada`) destravam técnicas ativáveis e especializações passivas da Guilda; amostra de 3 habilidades de herói (detectar armadilhas, esconder nas sombras, imposição das mãos) com a trava de classe relaxada pelo mesmo padrão + mensagens generalizadas (não citam mais "Richard"/"Luccas"); `_granted_hero_skills` injetado no `push_state` para o cliente renderizar; validação passa a rejeitar ids não suportados; editor ganha o seletor nos 5 tipos de item, filtrado e agrupado; recarga compartilhada com a Guilda pelo id; restrição de classe da técnica respeitada. Explique por que as outras ~17 habilidades de herói ficam para a Fase J (`handle_skill` é legado/inerte; cada habilidade é mensagem+handler+trava+painel). Cite os arquivos e o teste `[I1]`–`[I6]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-27-editor-itens-fase-i-habilidades-concedidas.md
git commit -m "docs(itens): registra o Editor de Itens — Fase I (habilidades concedidas)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Atualizar memória**

Crie `memory/editor-itens-fase-i-habilidades-concedidas.md` (tipo `project`): o que foi feito, estado (branch `feat/instrumentos-bardo-fase5`, não mergeada), contagem de checks, o achado de que `handle_skill` é legado/inerte (por isso a Fase J), e o follow-up de smoke in-app. Adicione a linha-índice no topo de `MEMORY.md`, linkando `[[editor-itens-fase-h-venenos]]`.

- [ ] **Step 5: Follow-up manual (usuário)**

Smoke test in-app: `python server.py` → `tools/editor.html` → "Editor de itens" → criar (a) uma arma concedendo **Brutalidade** (técnica), (b) um anel concedendo **Mira Certeira III** (especialização, guerreiro) e (c) uma bota concedendo **Detectar Armadilhas**. Marcar "Baús / recompensas" (o "Loja" segue afetado pelo WIP de lojas por cidade). Em jogo: equipar e conferir o botão "ITEM" no HUD, a recarga, e o botão de detectar armadilhas num herói que não é o Ladino.

---

## Self-Review (autor do plano)

- **Cobertura do spec:** helper + 2 portões (T1) ✓; 3 travas de herói + mensagens generalizadas (T2) ✓; `_granted_hero_skills` + injeção no `push_state` (T2) ✓; validação (T3) ✓; seletor nos 5 forms, filtrado e agrupado (T4) ✓; HUD técnicas "ITEM" + botões de herói (T5) ✓; testes [I1]–[I6] (T1/T2/T3) ✓; verificação isolada + docs + memória (T6) ✓.
- **Recarga compartilhada e restrição de classe:** saem de graça — `technique_cooldowns` é indexado pelo id, e o cliente só renderiza o botão se a técnica estiver em `guildCatalogFor(me.class_id)` (que já filtra por classe). Sem código extra.
- **Risco identificado e mitigado:** `tem_espec`/`tem_tecnica_equipada` são consultados em MUITOS pontos do motor; a Task 1 pede uma checagem de regressão explícita e a Task 6 roda `test_guilda.py` (o mais exposto).
- **Risco no cliente:** `_rogueSkillBtn`/`_paladinSkillBtn` podem ler estado exclusivo da classe; a Task 5 manda ler os dois helpers antes e reportar DONE_WITH_CONCERNS em vez de forçar.
- **Consistência de nomes:** `_habilidades_concedidas` (T1) é usado em T2/T3; `GRANTED_HERO_SKILLS` (T2) é lido por `_granted_ability_valida` (T3) — T3 depende de T2, ordem respeitada. `granted_hero_skills` (payload, T2) casa com `me.granted_hero_skills` (T5). `tecnicasConcedidasPorItem` (T5, gameState) casa com `GS.tecnicasConcedidasPorItem` (T5, game.js).
- **Sem placeholders:** todos os passos têm código/comando concreto.
