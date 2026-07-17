# Modo Mestre — Inventário do monstro (SP2): itens usáveis + habilidades ativáveis ampliadas

**Data:** 2026-07-17
**Escopo:** Subprojeto 2 (segue o SP1 — controle manual do monstro). Revisado após
descobrir que o usuário já implementou o sistema de equipamento no editor/servidor.

## Contexto — o que JÁ existe (feito pelo usuário em paralelo)

O editor de criaturas ganhou a opção de **inventário completo** (`equipment_enabled`
+ `equipped_items`), e o servidor já tem quase toda a máquina:

- `_aplicar_equipamentos_monstro(m)` (server.py ~4546): lê `equipped_items`, copia do
  `_DUNGEON_ITEM_CATALOG`, e:
  - **Arma** (item com `die`) → reconstrói `m["attacks"]` (dano/alcance/atributo) e grava
    `m["equipped_weapon"]`.
  - **Armadura/escudo/elmo** → somam `ac_bonus`/`def_` em `m["ac"]`
    (`equipment_ac_bonus`); efeitos `maxhp`/`spd`/`atk` também aplicados.
  - **`coat_poison`** → unta o veneno na `attacks[0]["on_hit"]` (`equipment_poison`).
  - **`m["equipment_consumables"]`** = itens com `item_slot=="bag"` (poções,
    arremessáveis, etc.) — **o inventário usável**.
- `_monster_try_equipment_item(m, target)` (~16203): a **IA** já usa cura de emergência,
  elixir (atk_bonus) e arremessáveis (via `_monster_throw_item`).
- `_monster_throw_item(m, target_obj, item)` (~16246): resolvedor de arremesso do monstro
  (fonte=monstro, alvo=herói) — **já existe**.
- Morte: `equipped_items` inteiro cai como loot (`_monster_dies` ~18656).
- Serialização: `push_state` faz `dict(m,…)`, então `equipment_consumables`,
  `equipped_weapon`, `equipment_items`, `ability_uses`, etc. **já chegam ao cliente**.

Verificado materializando o monstro exemplo **"soldado"**: CA 11→17, Espada Longa
1d8/+3, `equipment_consumables` = [Poção de Cura, Cantil de Água, Caneca de Cerveja,
Rede, Granada]. O sistema funciona.

**O buraco para o Modo Mestre:** hoje **só a IA** usa esses itens e habilidades. Na
janela Manual o **mestre não tem como acioná-los**. É isso que o SP2 entrega.

## Decisões (do brainstorming)

- Inventário = poções, arremessáveis, venenos, além de arma/armadura (equipamento já
  aplicado). **Fonte = `equipment_consumables`** (não inventar `carried_items`).
- Efeitos: catálogo do jogador, mapeados ao monstro. **food/ração/vinho/cerveja =
  recusa** ("sem efeito em monstros"). **Pergaminho = só monstro conjurador**.
- Itens não usados **caem no loot na morte** (já é o comportamento de `equipped_items`).
- Economia de ação **espelha o jogador**: consumível de bolsa = ação bônus; arremesso/
  pergaminho = ação principal.
- **Habilidades especiais do monstro devem aparecer e ser ativáveis pelo mestre, com
  usos e recarga** — inclusive as derivadas de herói/guilda (ex.: Mira Certeira do
  soldado), que o SP1 ainda não tornava ativáveis.

## Parte 1 — Itens usáveis pelo mestre

### Servidor
- Nova msg `mestre_usar_item {monster_id, item_id, target_id?, tx?, ty?}` →
  `handle_mestre_usar_item(pid, ...)`: valida `pid==master_pid`, `monster_id==
  master_manual_mid`, monstro vivo; localiza o item em `m["equipment_consumables"]`
  por `id`; despacha por `effect`.
- **Economia de ação:** novo flag `m["_master_bonus_acted"]` (1 ação bônus/turno) para
  os `BONUS_ACTION_EFFECTS` (heal/regeneration/atk_bonus/antidote/coat_poison/
  veil_shadow); `m["_master_acted"]` (já existe, compartilhado com atacar/habilidade)
  para `throwable`/`scroll`. Ambos resetados na abertura da janela
  (`_master_manual_window`).
- **Dispatch por efeito (versão-monstro):**
  | effect | comportamento | economia |
  |---|---|---|
  | `heal` | `m.hp=min(max_hp, hp+val)`; doses via `uses_left` | bônus |
  | `regeneration` | `m["potion_regen_pool"] += val`; tica +1/rodada no turno do monstro (novo tick em `gm_phase`) | bônus |
  | `atk_bonus` | `m["equipment_attack_bonus"] += val` por 1 turno (reusa o campo já somado no ataque) | bônus |
  | `coat_poison` | reaplica veneno em `attacks[0]["on_hit"]` (reusa `equipment_poison`) | bônus |
  | `veil_shadow` | `m["oculto_item"]` 1 turno (não é alvo; some no próximo turno) | bônus |
  | `antidote` | limpa veneno do monstro | bônus |
  | `throwable` | **reusa `_monster_throw_item(m, {"kind":"player","obj":herói}, item)`** mirando um herói (valida alcance/LOS já dentro dele). Ele **não** remove o item — o handler remove após a chamada (igual à IA em ~16222) | principal |
  | `scroll` | **só se `_monster_e_conjurador(m)`** (tem `monster_spells` ou habilidade `action_type=="magia"`); conjura via `_executar_magia_grimorio(m, magia, data)`; só magias em `GRIMORIO_IMPLEMENTADAS`; senão recusa | principal |
  | `food`/`ration`/`wine`/`ale` | **recusa** ("sem efeito em monstros") | — |
- Consumo do item: arremessável some (o `_monster_throw_item` já remove? — se não,
  remover no handler em acerto/erro); heal com doses decrementa `uses_left`; scroll/
  demais removem 1 de `equipment_consumables`.
- **Refator DRY:** extrair de `_monster_try_equipment_item` os efeitos por-item
  (heal/elixir) para helpers reusados pelo handler manual, evitando duplicar a lógica
  (a IA e o mestre chamam o mesmo helper).

### Cliente (ficha)
- `renderFichaMonstro` ganha a seção **"Itens"**, lendo `m.equipment_consumables`:
  cada item com emoji/nome/descrição + botão **Usar**. Arremessável/pergaminho abrem
  mira num herói (`openTargetModal` de heróis no alcance / `tx,ty` p/ área);
  consumível de alvo-próprio usa direto. Botão desabilita conforme economia
  (`_master_bonus_acted`/`_master_acted`), food/ale ("sem efeito") e scroll em não-
  conjurador ("IA apenas"). Mostra também **arma/armadura equipadas** em leitura
  (`m.equipped_weapon`/itens com `ac_bonus`), como referência.
- `src/gameState.js`: sender `mestreUsarItem(monsterId, itemId, targetId?, tx?, ty?)`.

## Parte 2 — Habilidades especiais ativáveis (ampliação do SP1)

O SP1 só tornou ativáveis as habilidades com `save`+`dc` (via `_use_monster_ability`).
As habilidades derivadas de **herói/guilda** (`source in {heroi, guilda}`,
`action_type != passiva`, com `monster_effect` — ex.: **Mira Certeira**,
`vantagem_combate`, `uses_per_day:3`, `cooldown_turns:4`) apareciam como "IA apenas".
Agora devem ser ativáveis pelo mestre, com usos/recarga corretos.

### Servidor
- `_habilidade_ativavel_manual(ability)` passa a aceitar **duas famílias**:
  (a) save+dc (como hoje) → resolve por `_use_monster_ability`;
  (b) `source in {heroi, guilda}` e `action_type != passiva` → resolve por um novo
  helper `_ativar_editor_ability(m, ability)` (self-buff, sem alvo).
- **Refator DRY:** extrair de `_monster_try_editor_ability` o núcleo "gasta uso+recarga
  (`monster_ability_uses`/`monster_ability_cooldowns`) e aplica
  `editor_ability_advantage`/`editor_ability_damage`" para `_ativar_editor_ability`,
  chamado tanto pela IA quanto pelo handler manual (contadores consistentes).
- `handle_mestre_usar_habilidade` (do SP1) ganha o ramo (b): se a habilidade é editor
  hero/guild, chama `_ativar_editor_ability` (não exige `target_id`), respeita
  usos/recarga de `monster_ability_*`, seta `_master_acted` (é ação). Recusa se sem
  usos/em recarga.
- **Consistência de exibição:** helper `_ability_counters(m, ability)` retorna
  `(usos_restantes, recarga_restante)` do dicionário correto por família
  (save+dc → `ability_*`; editor → `monster_ability_*`). Não muda serialização (os 4
  dicts já vão no `game_state`).

### Cliente (ficha — seção "Ações" do SP1)
- `ativavel(a)` passa a incluir a família editor (`source in {heroi,guilda}` e
  `action_type != 'passiva'`), além de save+dc.
- `usosRest(a)`/`cdRest(a)` escolhem o dict certo por família (save+dc → `ability_*`;
  editor → `monster_ability_*`), refletindo o gasto real.
- `_mestreAtivarHabilidade(m, abid)` ramifica: save+dc → mira um herói
  (`openTargetModal`); editor self-buff → ativa direto (sem modal).

## Parte 3 — Testes (`tools/test_modo_mestre.py`)

- **Materialização do soldado:** `equipment_consumables` populado; arma reconstrói o
  ataque; CA soma o equipamento.
- **`mestre_usar_item`:** heal cura o monstro (bônus); throwable chama `_monster_throw_item`
  mirando o herói (principal); food recusada; scroll recusado em não-conjurador e
  aceito em conjurador (mock de `_executar_magia_grimorio`); economia (1 bônus + 1
  principal/turno).
- **`mestre_usar_habilidade` (editor):** Mira Certeira ativável; gasta
  `monster_ability_uses`/`monster_ability_cooldowns`; aplica `editor_ability_advantage`;
  seta `_master_acted`; recusa sem usos/em recarga; `_ativar_editor_ability` é o mesmo
  caminho da IA.
- **Paridade sem-mestre:** byte-idêntico.

## Fora de escopo
- Coat_poison manual sofisticado (troca de veneno mid-combat além do reaplicar).
- Equipar/desequipar itens do monstro em tempo real pelo mestre (o equipamento é
  fixado na criação; SP2 só **usa** consumíveis).
- Pergaminho no nível gravado no scroll (usa-se o nível de conjurador do monstro).
