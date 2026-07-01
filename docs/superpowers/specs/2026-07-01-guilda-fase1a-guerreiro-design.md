# Guilda dos Heróis — Fase 1a: Especializações do Guerreiro

**Data:** 2026-07-01
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 1a (Guerreiro). A Fase 1 é decomposta **por classe**; cada classe tem seu
próprio spec→plano→implementação. Ordem sugerida das próximas: Clérigo, Paladino,
Ladino, Bardo, Mago.
**Depende de:** Fase 0 (Fundação da Guilda) — já mergeada. Reusa
`GUILD_CATALOG`, `handle_guild_buy` (valida `requer`/classe/posse/ouro),
`guild_owned.especializacoes` (persistido por personagem), e o painel da Guilda
(aba Especializações já renderiza itens `categoria:"especializacao"`).

---

## 1. Visão geral

As **Especializações** são upgrades **permanentes e sempre ativos** que aprimoram
as habilidades-base da classe (sem ocupar slot, sem "equipar"; ver spec da Fase 0).
Esta sub-fase cobre o **Guerreiro** (Victor, `class_id: "warrior"`), cujas 3
habilidades — Mira Certeira, Golpe Devastador, Fúria Berserker — hoje estão no
"poder máximo". A Fase 1a **enfraquece o baseline gratuito** e vende os incrementos
como Especializações na Guilda.

### Estado atual (confirmado no código)
- As 3 habilidades são **armadas no cliente** (toggle, `warriorSelected` em
  `gameState.js`; sem custo ao armar) e enviadas como array `buffs` junto do
  `attack`. Servidor: `handle_attack` (server.py), bloco "Habilidades ARMADAS do
  warrior" — cobra a soma de `fome_cost`/`sede_cost` das selecionadas e seta flags.
- **Hoje não há limite de combinação:** todas as 3 podem ser armadas juntas.
- **Golpe Devastador:** `raw_dmg *= 2` (dobra os dados) — isto é, hoje o base já é o
  poder do **Nível III** do spec.
- **Mira Certeira:** `skill_bonus_acerto += 2`.
- **Fúria Berserker:** `skill_ataque_extra = True` + `skill_extra_usado` garantem
  **exatamente 1** ataque extra (resolvido inline em `handle_attack`, ~onde
  `p.get("skill_ataque_extra") and not p.get("skill_extra_usado")`). Reset por turno
  junto de `skill_dobrar_dano`/`skill_ataque_extra`/`skill_extra_usado`.

---

## 2. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Baseline gratuito | 3 habilidades na ficha, **só 1 armada por turno**, com números FRACOS: Mira **+2 acerto**, Golpe **×1,5**, Fúria **+1 ataque extra**. |
| Nerf real | Golpe cai de ×2 (atual) para **×1,5** no base. Quem já jogava perde poder até comprar Golpe III. |
| Combinar | comprar **Combinar Duas** → 2 por turno; **Mestre de Combate** → 3 por turno. |
| Níveis III | por habilidade: Mira III (+2 acerto **+2 dano**), Golpe III (**×2**), Fúria III (**+2** ataques extras, 3 no total). |
| Pré-requisitos | **Combinar Duas** é o portão: Mestre de Combate **e** os três Nível III exigem `guerreiro_combinar_2` comprado antes. Combinar Duas não tem pré-requisito. |
| Preços | Combinar Duas **150**, cada Nível III **200**, Mestre de Combate **300**. |
| Custo de uso | **Ouro é o único custo.** Usar upgrades custa o mesmo 🍖/💧 da base; combinar continua **somando** os custos das habilidades armadas (comportamento atual). Sem tabela de custo extra de progressão nesta sub-fase. |
| Arquitetura | Imperativa (estilo do código): catálogo só p/ exibição/compra; efeito lido inline em `handle_attack` via helper `_tem_espec(p, id)`. |
| Autoridade | Servidor é autoritativo: trunca `buffs` ao teto permitido mesmo se o cliente enviar mais. |

---

## 3. Catálogo (`GUILD_CATALOG`, server.py)

Cinco entradas `categoria:"especializacao"`, `classe:"warrior"`. Especializações
**não** têm `custo_fome`/`custo_sede`/`recarga_rodadas` (campos de técnica);
`exclusiva:false`. Campos usados pelo painel: `nome`, `icon`, `desc`, `preco`,
`requer`, `linha`, `nivel`.

```python
"guerreiro_combinar_2": {
    "id": "guerreiro_combinar_2", "categoria": "especializacao", "classe": "warrior",
    "linha": "guerreiro_combate", "nivel": 2, "requer": None, "exclusiva": False,
    "preco": 150, "nome": "Combinar Duas", "icon": "⚔️",
    "desc": "Permite armar DUAS habilidades no mesmo turno.",
},
"guerreiro_mestre_combate": {
    "id": "guerreiro_mestre_combate", "categoria": "especializacao", "classe": "warrior",
    "linha": "guerreiro_combate", "nivel": 4, "requer": "guerreiro_combinar_2", "exclusiva": False,
    "preco": 300, "nome": "Mestre de Combate", "icon": "🏆",
    "desc": "Permite armar as TRÊS habilidades no mesmo turno.",
},
"guerreiro_mira_3": {
    "id": "guerreiro_mira_3", "categoria": "especializacao", "classe": "warrior",
    "linha": "guerreiro_mira", "nivel": 3, "requer": "guerreiro_combinar_2", "exclusiva": False,
    "preco": 200, "nome": "Mira Certeira III", "icon": "🎯",
    "desc": "Mira Certeira também concede +2 de dano (além do +2 de acerto).",
},
"guerreiro_golpe_3": {
    "id": "guerreiro_golpe_3", "categoria": "especializacao", "classe": "warrior",
    "linha": "guerreiro_golpe", "nivel": 3, "requer": "guerreiro_combinar_2", "exclusiva": False,
    "preco": 200, "nome": "Golpe Devastador III", "icon": "💥",
    "desc": "Golpe Devastador passa a multiplicar os dados de dano por 2 (era ×1,5).",
},
"guerreiro_furia_3": {
    "id": "guerreiro_furia_3", "categoria": "especializacao", "classe": "warrior",
    "linha": "guerreiro_furia", "nivel": 3, "requer": "guerreiro_combinar_2", "exclusiva": False,
    "preco": 200, "nome": "Fúria Berserker III", "icon": "🔥",
    "desc": "Fúria Berserker concede 2 ataques extras (3 ataques no total).",
},
```

> **Compra:** `handle_guild_buy` (Fase 0) já valida classe, `requer`, posse e ouro,
> e persiste. Nenhuma mudança no handler. `guild_items_for_class("warrior")` passa a
> retornar estas 5 (+ técnicas genéricas como Brutalidade).

Helper novo (server.py, perto dos outros helpers de guilda):
```python
def tem_espec(player, espec_id):
    return espec_id in player.get("guild_owned", {}).get("especializacoes", [])
```
(Como método/local conforme conveniência em `handle_attack`; nome final
`_tem_espec` se método de `GameRoom`, ou função-módulo `tem_espec`.)

---

## 4. Enfraquecer o base + aplicar upgrades (`handle_attack`, server.py)

### 4.1 Limite de combinação (autoritativo)
No bloco "Habilidades ARMADAS do warrior", antes de aplicar `buffs`, calcular o
teto pela posse e **truncar**:
```python
teto = 1
if tem_espec(p, "guerreiro_mestre_combate"): teto = 3
elif tem_espec(p, "guerreiro_combinar_2"):   teto = 2
sel = [s for s in p.get("skills", []) if s["id"] in (buffs or []) and "mp" not in s]
if len(sel) > teto:
    sel = sel[:teto]
    await self.gm_say(f"**{p['name']}** só pode combinar {teto} habilidade(s) por turno.")
```
Só as `sel` truncadas cobram custo e aplicam efeito. (O cliente também limita — §6 —
mas o servidor é a autoridade.)

### 4.2 Golpe Devastador — ×1,5 base / ×2 com III
Onde hoje é `raw_dmg *= 2` (dentro do ramo `p.get("skill_dobrar_dano")`):
```python
if p.get("skill_dobrar_dano"):
    if tem_espec(p, "guerreiro_golpe_3"):
        raw_dmg *= 2
    else:
        raw_dmg = raw_dmg + raw_dmg // 2   # ×1,5 arredondado p/ baixo
```
O ramo desarmado (`base = 2 if skill_dobrar_dano else 1`) é raro para o Guerreiro
(sempre tem arma), mas para consistência: base do Golpe desarmado passa a
`1 + (1 if golpe_3 else 0)`? **Decisão:** manter o desarmado como está hoje
(`base = 2 if skill_dobrar_dano else 1`) — desarmado é caso de canto e o dano fixo
1→2 já é modesto; não vale complicar. Documentar essa exceção no código.

### 4.3 Mira Certeira III — +2 dano
Onde a Mira seta `skill_bonus_acerto += 2`, também setar um bônus de dano quando III:
```python
if sid == "mira_certeira":
    p["skill_bonus_acerto"] = p.get("skill_bonus_acerto", 0) + 2
    if tem_espec(p, "guerreiro_mira_3"):
        p["skill_bonus_dano"] = p.get("skill_bonus_dano", 0) + 2
```
Somar `p.get("skill_bonus_dano", 0)` no cálculo final de `dmg` (junto de
`cancao_dano`/`gl_dano`/`_tecnica_bonus_dano`), e **resetar** `skill_bonus_dano = 0`
no fim do turno junto das outras flags. (Campo novo no `make_player`:
`"skill_bonus_dano": 0`.)

### 4.4 Fúria Berserker III — contador de ataques extras
Refatorar o par booleano (`skill_ataque_extra`/`skill_extra_usado`) para um
**contador** `skill_ataques_extras`:
- Ao armar Fúria: `p["skill_ataques_extras"] = 2 if tem_espec(p,"guerreiro_furia_3") else 1`.
- No ponto onde hoje concede o extra (`if p.get("skill_ataque_extra") and not
  p.get("skill_extra_usado")`), trocar por: se `p.get("skill_ataques_extras", 0) >
  0`, decrementar e conceder outra ação de ataque (mesma mensagem "ataque extra
  disponível").
- Reset por turno: `skill_ataques_extras = 0` (substitui os dois booleanos antigos).
- Campo novo no `make_player`: `"skill_ataques_extras": 0` (remover
  `skill_ataque_extra`/`skill_extra_usado` — buscar TODAS as referências e migrar;
  há usos em ~2994-2996, ~4867, ~5103-5104, ~10110-10112).

> **Cuidado:** garantir que a mecânica de "ataque extra" continue exigindo o input
> do jogador (novo ataque) como hoje — o contador só habilita quantos extras restam,
> não dispara ataques automáticos.

---

## 5. Reset por turno + make_player

- `make_player` (server.py): adicionar `"skill_bonus_dano": 0` e
  `"skill_ataques_extras": 0`; remover `"skill_ataque_extra"`/`"skill_extra_usado"`.
- No reset de fim de turno (junto de `p["skill_dobrar_dano"] = False`): setar
  `p["skill_bonus_dano"] = 0` e `p["skill_ataques_extras"] = 0`.

---

## 6. Cliente (`game.js` + `gameState.js`)

- **Teto de combinação na UI:** a função de armar do Guerreiro
  (`toggleWarriorSkill`/`isWarriorSkillSelected` no lado do estado; render em
  `game.js`) passa a ler o teto de `GS.guildOwnedOf(me.id).especializacoes`
  (1 base / 2 com `guerreiro_combinar_2` / 3 com `guerreiro_mestre_combate`).
  Tentar armar além do teto **não marca** e mostra um toast/dica
  ("Compre Combinar Duas para armar 2 habilidades"). O servidor continua truncando
  como autoridade.
- **Descrições refletem a posse:** o botão do Golpe mostra ×2 se `guerreiro_golpe_3`;
  Mira mostra "+2 acerto +2 dano" se `guerreiro_mira_3`; Fúria "2 ataques extras" se
  `guerreiro_furia_3`. (Lê `guildOwnedOf`.)
- **Painel da Guilda:** já renderiza a aba Especializações (Fase 0); com as 5
  entradas novas, some o "— em breve —". Sem código novo além do catálogo.
- **Robustez na masmorra:** `guildOwnedOf` já cai para o player do `game_state`
  quando `cityState=null` (corrigido na Fase 0) — os tetos/descrições funcionam
  dentro da dungeon.

---

## 7. Testes (`tools/test_guerreiro_espec.py`)

Harness do projeto (`main()` async + `check()`; sem pytest). Reusa o `setup()` de
`test_guilda.py` ou replica. Cobrir, sem UI:

1. **Base enfraquecido:** sem especializações, armar só 1 habilidade é permitido;
   armar 2 no `buffs` → servidor trunca para 1.
2. **Golpe base ×1,5:** com Golpe armado e sem `guerreiro_golpe_3`, o multiplicador
   é ×1,5 (validar via helper de multiplicador ou uma rolagem determinística —
   *mockar* `random`/`roll_dice` para dado fixo e conferir o dano).
3. **Golpe III ×2:** com `guerreiro_golpe_3`, multiplicador ×2.
4. **Mira III:** com `guerreiro_mira_3`, aplica `skill_bonus_dano += 2` (e acerto +2).
5. **Fúria base 1 extra / Fúria III 2 extras:** `skill_ataques_extras` = 1 sem III,
   2 com `guerreiro_furia_3`; decrementa a cada extra concedido.
6. **Combinar:** `combinar_2` → teto 2; `mestre_combate` → teto 3.
7. **Compra (via handle_guild_buy):** `guerreiro_mira_3` recusado sem
   `guerreiro_combinar_2`; idem `mestre_combate`; com o pré-requisito, aceito.
8. **Reset por turno:** `skill_bonus_dano`/`skill_ataques_extras` zeram.

> Para dano determinístico, mockar `random.randint`/`roll_dice` (como outros testes
> do projeto fazem) para isolar o multiplicador.

---

## 8. Fronteiras (NÃO fazer nesta sub-fase)

- Outras classes (Clérigo/Paladino/Ladino/Bardo/Mago) — sub-fases próprias.
- Tabela de **custo extra de progressão** (baixo/médio/alto) — entra quando uma
  classe a exigir (Paladino/Clérigo).
- Reembolso/venda de especializações — não há.
- Qualquer técnica nova (4º slot) — é Fase 2.

---

## 9. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Nerf do Golpe (×2→×1,5) surpreende quem já jogava | Comportamento intencional e documentado; Golpe III restaura ×2. Registrar no CLAUDE.md. |
| Refactor de Fúria (booleanos→contador) quebrar o fluxo de ataque extra | Migrar TODAS as referências num passo; teste 5 fixa o comportamento (1 vs 2 extras, decremento). |
| Cliente e servidor divergirem no teto de combinação | Servidor é autoritativo (trunca); cliente só melhora UX. Teste 1/6 fixa o servidor. |
| Arredondamento do ×1,5 | Regra explícita: `raw_dmg + raw_dmg//2` (floor). Teste 2 fixa. |
