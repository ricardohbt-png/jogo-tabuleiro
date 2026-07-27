# Antídotos e curas de status (consumíveis)

**Data:** 2026-07-28
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Relacionadas:** Fase F (sub-aba Poções do Editor de Itens), Fase H (venenos), Fase J (habilidades concedidas)

## Objetivo

Criar três consumíveis que **curam um status e concedem imunidade temporária** a ele:

| Item | Cura | Imunidade |
|---|---|---|
| **Antídoto** (item nativo já existente) | veneno (inclui cegueira por veneno) | veneno, 1d4 rodadas |
| **Óleo Dissolvente** (novo) | petrificação | petrificação, 1d4 rodadas |
| **Elixir Depurativo** (novo) | doença | doença, 1d4 rodadas |

Usáveis **em si mesmo ou num aliado adjacente**, e **autoráveis** na sub-aba Poções do Editor
de Itens (com o dado da imunidade configurável).

## Contexto

### A cura de status já existe — mas presa dentro da Purificação

`handle_purificacao` (o milagre do clérigo) contém, **inline**, a lógica de remoção de cada
status: veneno (reverter `efeitos_veneno` + limpar `cego`/`cego_pen_ataque`/`bloqueia_distancia`),
petrificação (`petrificado`/`petrificado_rodadas`), doença (chama `_curar_doenca`, que **já é um
helper** e devolve bool) e maldição. São ~40 linhas que os consumíveis precisam reusar.

### O antídoto nativo é um nome mentiroso

`SHOP_MERCHANT` tem `{"id": "antidote", "name": "Antídoto", "effect": "heal", "value": 6}` — ou
seja, hoje ele **cura 6 HP e não remove veneno nenhum**. Além disso, `"antidote"` já está listado
em `BONUS_ACTION_EFFECTS`, mas **não existe ramo `antidote` no `handle_use_item` do jogador**
(só no `_monster_use_item` do mestre). A conversão para o efeito real foi **aprovada** e é uma
mudança de gameplay consciente.

### Fontes reais de cada status (levantadas para posicionar a imunidade)

| Status | Fontes |
|---|---|
| Veneno | `_aplicar_veneno` (todas as operações) |
| Petrificação | **duas**: o ramo `petrificar` de `_aplicar_veneno` **e** a habilidade de monstro `effect == "petrificado"` (fonte independente de veneno) |
| Doença | `_aplicar_doenca` (fonte única hoje: infecção de zumbi) |

Isso confirma que a imunidade à petrificação não é redundante com a de veneno.

### Alvo e economia de ação

Todos os consumíveis atuais são de uso próprio e passam por `handle_use_item(pid, item_id)`
como **ação bônus** (`BONUS_ACTION_EFFECTS`). Para mirar um aliado existe o helper de cliente
`openTargetModal(title, targets, kind, callback)` — um modal simples que lista alvos
(`{id, name, emoji, hp, max_hp}`) e devolve o id escolhido; é o que as técnicas com
`alvo:"aliado"` já usam.

O clique no item da bolsa passa por `useItem(itemId)` (game.js:12629), chamado de
`src/ui/inventoryModal.js:307`. Colocando a decisão de mira **dentro de `useItem`**, o modal de
inventário não precisa mudar.

## Decisões de design (aprovadas)

1. **Alvo**: si mesmo **ou aliado adjacente** (Chebyshev ≤ 1).
2. **Os três concedem imunidade** ao status que curam, com duração em dado.
3. **Autoráveis** na sub-aba Poções do Editor de Itens.
4. **Converter o `antidote` nativo** de `heal` para `cure_poison` (mudança de gameplay aprovada).

## Arquitetura

### 1. Servidor — helpers de cura (extração)

Extrair de `handle_purificacao`, sem mudar comportamento:

```python
def _curar_veneno_status(self, alvo) -> bool   # efeitos_veneno + cegueira
def _curar_petrificacao(self, alvo) -> bool    # petrificado + rodadas
```
`_curar_doenca(p) -> bool` **já existe**. `handle_purificacao` passa a chamar os três nos ramos
`veneno`/`petrificacao`/`doenca` (o ramo `maldicao` fica inline — fora do escopo).

### 2. Servidor — imunidade temporária genérica

```python
def _conceder_imunidade_status(self, p, status, rodadas)  # p["imunidades_status"][status] = round_num + rodadas
def _imune_a_status(self, p, status) -> bool              # > round_num
```
`status` ∈ `{"veneno", "petrificacao", "doenca"}` (set `_STATUS_IMUNIZAVEIS`).

**Quatro pontos de bloqueio:**

- `_aplicar_veneno`: junto da checagem de imunidade estática existente → se
  `_imune_a_status(alvo, "veneno")`, narra e retorna.
- `_aplicar_veneno`, ramo `petrificar` (falha do save): se
  `_imune_a_status(alvo, "petrificacao")`, não petrifica (narra a resistência).
- Habilidade de monstro `effect == "petrificado"`: mesma checagem antes de setar.
- `_aplicar_doenca`: no topo, se `_imune_a_status(p, "doenca")`, narra e retorna.

**Nota de estado:** a imunidade é gravada como rodada absoluta (`round_num + N`), como o resto do
motor (`mov_bonus_ate`, `contra_ataque_ate`, …). Segue a mesma semântica desses campos.

### 3. Servidor — três efeitos de consumível

Novos ramos em `handle_use_item`, despachados por `effect`:
`cure_poison` → veneno · `cure_petrification` → petrificação · `cure_disease` → doença.

Cada ramo: resolve o alvo (padrão = quem usou), **cura** via o helper correspondente e **concede
a imunidade** rolando o dado do item (`imunidade_dado`, ex. `"1d4"`; ausente → sem imunidade).
Os três entram em `BONUS_ACTION_EFFECTS` (ação bônus, como os demais consumíveis).

**Importante:** o item é consumido mesmo que o alvo não tivesse o status — a imunidade preventiva
é um uso legítimo (beber antídoto antes de entrar na sala do basilisco). A narração distingue os
dois casos.

### 4. Protocolo e alvo

- `use_item` ganha **`target_id` opcional** (ausente = quem usou → retrocompatível com clientes
  antigos e com todos os outros consumíveis).
- `handle_use_item(pid, item_id, target_id=None)`; o dispatch passa `msg.get("target_id")`.
- Validação (só para os 3 efeitos novos): alvo deve ser jogador **vivo** e **adjacente**
  (`_no_raio(p, alvo, 1)`); alvo inválido → erro, **sem** consumir o item nem a ação bônus.

### 5. Cliente — uma função

`useItem(itemId, targetId)` (game.js:12629) passa a decidir: se o item é de cura de status e não
veio alvo, monta a lista (o próprio herói + aliados vivos adjacentes) e abre `openTargetModal`,
chamando-se de volta com o id escolhido. `src/ui/inventoryModal.js` **não muda**.

### 6. Itens nativos (SHOP_MERCHANT)

- **Antídoto** (`antidote`): `effect` `heal`→`cure_poison`, `imunidade_dado:"1d4"`.
- **Óleo Dissolvente** (`oleo_dissolvente`, 🫗): `cure_petrification`, `imunidade_dado:"1d4"`.
- **Elixir Depurativo** (`elixir_depurativo`, 🧴): `cure_disease`, `imunidade_dado:"1d4"`.

### 7. Editor de Itens (sub-aba Poções)

`_ITEM_POTION_EFFECTS` += os 3 efeitos. A validação grava `imunidade_dado` (dado `NdX` válido,
opcional). No form, quando o efeito é de cura, aparecem os campos de **dado da imunidade**
(quantidade + faces) no lugar de "Valor"/"Doses"; a lógica pura (`serializePotion`) reflete isso.

### 8. Testes

**`tools/test_editor_itens.py`** — seção `[K1]`–`[K6]`:

- [K1] helpers de cura: `_curar_veneno_status`/`_curar_petrificacao` limpam o status e devolvem
  bool; a Purificação do clérigo continua funcionando (não regrediu).
- [K2] imunidade: `_conceder_imunidade_status`/`_imune_a_status`; expira quando `round_num` passa.
- [K3] bloqueio nas 4 fontes: veneno, petrificação por veneno, petrificação por habilidade de
  monstro, e doença.
- [K4] uso em si mesmo: cada um dos 3 efeitos cura e concede imunidade; o item é consumido mesmo
  sem o status presente.
- [K5] uso em aliado adjacente (com `target_id`); alvo distante é recusado **sem** consumir o item.
- [K6] itens nativos e editor: o `antidote` nativo tem `effect:"cure_poison"`; os 3 efeitos são
  aceitos por `_validate_custom_potion` com `imunidade_dado`, e id inválido é rejeitado.

**`tools/test_editor_items_logic.js`**: `serializePotion` com os 3 efeitos + `imunidade_dado`.

Verificar o estado **committado** em worktree isolado.

**Estado conhecido do working tree (NÃO é regressão):** com o WIP do usuário,
`tools/test_editor_itens.py` aborta na seção `[7]` (lojas por cidade); verificar as seções novas
importando o módulo. Também pré-existentes: `test_roteamento_itens.py` e 1 flaky em
`test_devorador.py`.

## Fora de escopo

- Cura de **maldição** por consumível (o ramo continua só na Purificação).
- Imunidade a outros status (medo, atordoamento, cegueira isolada, lentidão).
- Arremessar esses itens num aliado à distância (são de contato/uso).
- Monstros usando os novos efeitos pelo mestre (`_monster_use_item` mantém o ramo `antidote`
  atual, que limpa as chaves de veneno do monstro).

## Critérios de aceite

- Os três itens curam o status correspondente, em si e em aliado adjacente, e concedem imunidade
  pela duração rolada.
- Enquanto imune, o status não é aplicado por nenhuma das fontes levantadas; após expirar, volta
  a ser aplicável.
- O `antidote` nativo cura veneno de verdade.
- Alvo inválido (distante/morto) não consome item nem ação bônus.
- A Purificação do clérigo continua idêntica após a extração dos helpers.
- Os 3 efeitos aparecem na sub-aba Poções com o dado da imunidade.
- Testes `[K1]`–`[K6]` e node verdes no estado committado isolado.
