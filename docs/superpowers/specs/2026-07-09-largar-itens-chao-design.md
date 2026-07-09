# Sub-projeto C — Largar/pegar itens no chão

**Data:** 2026-07-09
**Escopo:** `server.py` (autoritativo) + `src/gameState.js` (senders/getters puros) +
`game.js` (render 2D/3D + gesto). Ordem: estado → protocolo → render (CLAUDE.md).
**Depende de:** Sub-projeto B (`_route_acquired_item`) — concluído.

## Objetivo

Permitir, **na masmorra**, largar um item no chão (numa das 8 casas ao redor) e
pegá-lo de volta — inclusive por outro jogador, servindo para (a) descartar itens
sem ir à cidade e (b) passar itens entre heróis. Espelha o modelo dos baús.

## Decisões de design (do brainstorming)

- **Alvo do drop:** automático — o servidor escolhe a 1ª das 8 casas adjacentes que
  seja chão livre. O jogador não escolhe a casa.
- **Custo/timing:** ação **livre, a qualquer momento** (como abrir baú / equipar).
  Não passa por `_is_turn` nem consome ação/movimento. Qualquer jogador pode
  largar/pegar mesmo fora do próprio turno.
- **Origem do drop:** bolsa **e** slots equipados (largar de um slot desequipa na
  hora).
- **Confirmação:** nenhuma — larga imediatamente (recuperável: fica na casa ao lado).
- **Alcance de pegar:** adjacente ao item, Chebyshev ≤ 1.
- **Persistência:** os itens no chão persistem **exatamente como `self.chests`** —
  ficam na memória do `GameRoom` ao ir/voltar da cidade (mesmo lugar) e só são
  limpos quando uma masmorra **nova** é gerada (após encerrar a missão). Sem
  save/restore novo.
- **Névoa:** sem gating — enviados sempre no `game_state`, como os baús (estão em
  áreas já exploradas de qualquer modo).

## Estado do mundo

`self.ground_items: dict[str, dict]` — `id -> {"id", "item", "pos":[x,y]}`.

- Inicializa `self.ground_items = {}` no `__init__` (junto de `self.chests`, ~L3949).
- Reseta `self.ground_items = {}` **apenas** no bloco de masmorra nova
  (`if nova:`, ~L5185), ao lado de `corpses`/`chests`/`monsters`/`traps`. NÃO é
  resetado em `_voltar_para_cidade` (por isso persiste ao sair/voltar).
- Serializado em `push_state`: `"ground_items": list(self.ground_items.values())`.

## Protocolo

### Client → Server

| Mensagem | Campos | Efeito |
|---|---|---|
| `drop_item` | `source` (`'bag'`\|`'gear'`), `index` (se bag) **ou** `slot_key` (se gear) | Larga o item na 1ª casa livre adjacente. |
| `pickup_item` | `ground_id` | Pega o item do chão (adjacente ≤1) para o inventário. |

Dispatch em `handle_message` (junto de `take_from_chest`).

### Server → Client

`game_state.ground_items: [{id, item, pos:[x,y]}]`.

## Servidor — handlers e helpers

### `_free_drop_tile_near(pos)` (novo)
Como `_free_tile_near`, mas exclui também: decorações sólidas (`_decor_block_tiles`
/ `_blocks_tile`), outros `ground_items`, e jogadores vivos. Retorna a 1ª casa livre
(ordem determinística) ou `None` se as 8 estiverem bloqueadas.

### `handle_drop_item(pid, source, index, slot_key)`
1. Valida jogador vivo e fase `playing`. (Sem `_is_turn` — ação livre.)
2. Obtém o item:
   - `source == 'bag'`: `item = p["bag"][index]` (valida índice).
   - `source == 'gear'`: `item = p["gear"][slot_key]` (valida slot não-vazio).
3. Acha a casa: `tile = self._free_drop_tile_near(p["pos"])`; se `None` → erro
   "Sem espaço adjacente para largar." e retorna (sem remover o item).
4. Remove da origem:
   - bag: `p["bag"].pop(index)`.
   - gear: espelha `handle_unequip` — `p["gear"][slot_key] = None`,
     `_apply_gear_effect(p, item, False)`, e se `slot_key == "weapon"` restaura
     `p["weapon"] = {**WEAPONS["unarmed"]}`.
5. Cria `self.ground_items[new_id()] = {"id", "item": item, "pos": tile}`.
6. `gm_say` + `push_state`.

### `handle_pickup_item(pid, ground_id)`
1. Valida jogador vivo, fase `playing`. (Sem `_is_turn`.)
2. `gi = self.ground_items.get(ground_id)`; senão erro "Item não encontrado.".
3. Distância: `Chebyshev(p["pos"], gi["pos"]) <= 1`; senão "Muito longe do item!".
4. `res = self._route_acquired_item(p, gi["item"])`:
   - `'full'` → erro "Inventário cheio e slot ocupado — abra espaço primeiro." e
     mantém o item no chão.
   - senão → `del self.ground_items[ground_id]`; `gm_say` (`equipado — bolsa cheia`
     se `'equipped'`); `push_state`.

## Cliente — `src/gameState.js`

- Getter `get groundItems() { return (gameState && gameState.ground_items) || []; }`.
- Senders: `dropItem(source, ref)` → `send({type:'drop_item', source, index?/slot_key?})`;
  `pickupItem(id)` → `send({type:'pickup_item', ground_id:id})`.
- Resolver puro `groundItemPickable(gi, myPlayer)` → bool (adjacência ≤1) — usado
  pelo render para habilitar o clique.
- Exporta no objeto de retorno.

## Cliente — `game.js` (render + gesto)

- **Largar (gesto):** no `InventoryModal`, ao arrastar um item (bag ou gear) e
  soltar **fora do frame do modal** (no backdrop `#inv-modal-overlay`), chamar
  `GS.dropItem(...)` com a seleção atual (`_selected`), fechar/atualizar o modal.
  Reusa o `_selected` já existente (`{kind:'bag',index}` / `{kind:'gear',slotKey}`)
  → mapeia para `source`/`index`/`slot_key`.
- **Render 2D:** para cada `GS.groundItems`, desenhar o ícone (`itemIconHTML`/emoji)
  na casa, com um brilho leve; casa clicável se adjacente.
- **Render 3D:** mesh/sprite pequeno na casa (padrão de `chestMeshes`), clicável.
- **Pegar:** clique num item do chão adjacente → `GS.pickupItem(id)`; se longe,
  `toast('Muito longe do item.')`.

## Verificação

Teste novo `tools/test_ground_items.py` (estilo `tools/test_*.py`, stub de rede):

1. Largar da bolsa → item sai da bolsa e aparece em `ground_items` numa casa
   adjacente livre.
2. Largar de um slot equipado (arma) → desequipa (efeito revertido, `p["weapon"]`
   volta a desarmado) e cai no chão.
3. Todas as 8 casas ocupadas (paredes/decoração/itens) → recusa, item permanece.
4. Pegar por **outro** jogador adjacente → sai do chão, entra na bolsa (via
   `_route_acquired_item`).
5. Pegar longe (Chebyshev >1) → erro, item permanece.
6. Pegar com bolsa cheia + slot ocupado → recusa ('full'), item permanece.
7. **Persistência:** largar um item, `_voltar_para_cidade()`, reentrar (mesma
   masmorra, `nova=False`) → item continua no mesmo lugar; gerar masmorra nova
   (`nova=True`) → `ground_items` limpo.

Rodar da raiz: `python tools/test_ground_items.py`. Rodar também
`tools/test_persistencia_masmorra.py` e `tools/test_roteamento_itens.py` (sem
regressão).
