# Ficha do personagem na cidade (fotos + equipar/organizar) — Design (v2)

**Data:** 2026-06-24
**Branch base:** master (trabalho na branch `feat/objetivos-recompensa-deletar-sala`)

> **v2 substitui a v1.** A v1 (cliente-only, modelo cosmético `GS.getHeroiAtivo`)
> estava errada: o modelo cosmético é sobrescrito a cada `city_state` (re-sincroniza
> a `bag` autoritativa do servidor), então equipar por ali não persiste e duplica
> itens. A v2 usa o **modelo autoritativo do servidor** (`player.gear` / `player.bag`),
> que já é enviado a todos no `city_state`. As funções da v1
> (`_renderFichaCidadeEquip`, modal central `abrirFichaCidade`) são removidas.

## Problema

Na tela da cidade não há como ver a ficha do personagem nem equipar/organizar os
itens comprados na loja antes de entrar na masmorra. Além disso, os cards de herói
mostram só um emoji — o usuário quer ver a foto (rosto) de cada herói.

## Objetivo

1. Cada card de herói na cidade mostra a **foto do rosto** (recorte 3:4).
2. Clicar na foto abre a **ficha completa** num **painel lateral esquerdo
   deslizante**: atributos + equipamento (8 slots) + inventário.
3. No meu herói: equipar/desequipar e **organizar o inventário por arrastar-e-soltar**.
4. Clicar na foto de outro herói abre a ficha dele em **somente-leitura**.

## Decisões (brainstorming)

| Tópico | Decisão |
|---|---|
| Fotos | **Todos** os cards mostram a foto do rosto (3:4, recorte no topo). |
| Posição | Painel **lateral esquerdo** deslizante (✕ / clicar fora fecha). |
| Modelo de dados | **Autoritativo do servidor** (`gear`/`bag`). Mexe em server.py + protocolo. |
| Drag-and-drop | Reordenar bolsa **e** equipar/desequipar arrastando. |
| Outros heróis | Ficha **somente-leitura** (atributos + equipamento + bolsa). |
| Consumíveis | Só aparecem na bolsa (arrastáveis); **sem** botão usar (Taverna resolve). |

## Modelo de dados (autoritativo, já existente)

- `player.gear` — 8 slots nomeados: `weapon`, `off_hand`, `armor`, `head`,
  `ring1`, `ring2`, `item1`, `item2` (server.py:2794).
- `player.bag` — lista de itens (≤ `player.bag_size`, default 6).
- Compras na loja vão para `player.bag` (server.py:3465+).
- `broadcast_city_state` envia `list(self.players.values())` — `gear`/`bag` de
  **todos** disponíveis no cliente (server.py:3367).
- Handlers existentes (já roteados): `handle_equip_from_bag(pid, slot_index)`,
  `handle_equip_offhand(pid, slot_index)`, `handle_unequip(pid, slot_key)`. Todos
  terminam com `await self.push_state()`.

## Restrição-chave descoberta

`push_state()` faz broadcast de **`game_state`** (campos de masmorra: tiles,
monsters, …). Na fase `city` não há masmorra e o cliente está em `screen-city`,
então um `game_state` ali é incorreto. **Por isso** os handlers de equipar precisam
de broadcast **ciente da fase**.

## Design — Servidor (`server.py`)

### 1. Broadcast ciente da fase
Helper:
```python
async def push_state_or_city(self):
    if self.phase == "city":
        await self.broadcast_city_state()
    else:
        await self.push_state()
```
Trocar a chamada final `await self.push_state()` por `await self.push_state_or_city()`
em `handle_equip_from_bag`, `handle_equip_offhand` e `handle_unequip`. Comportamento
na masmorra fica idêntico (phase != "city" → push_state).

### 2. Reordenar a bolsa
```python
async def handle_reorder_bag(self, pid, from_index, to_index):
    p = self.players.get(pid)
    if not p: return
    bag = p["bag"]; n = len(bag)
    if from_index < 0 or from_index >= n: return
    item = bag.pop(from_index)
    to_index = max(0, min(to_index, len(bag)))   # clamp; len já decrementado
    bag.insert(to_index, item)
    await self.push_state_or_city()
```
Roteamento no protocolo: `elif t == "reorder_bag": ... handle_reorder_bag(pid,
int(from_index), int(to_index))`.

> Nenhuma mudança nos handlers de equipar além do broadcast; a validação de
> classe/2-mãos/inventário-cheio já existe e vale na cidade.

## Design — Cliente (`game.js` + `game.css`)

### 3. Fotos nos cards (todos os heróis)
`_updateCityHeroBar`: trocar o emoji pela foto `CLASS_PORTRAITS[p.class_id]`
(game.js:6719) recortada no rosto:
`width:100%; aspect-ratio:3/4; object-fit:cover; object-position:top center;`
(fallback para emoji se a imagem falhar, via `onerror`). Cada card recebe
`cursor:pointer` e `onclick` → `abrirFichaCidade(p.id)`.

### 4. Painel lateral esquerdo deslizante
Elemento único `#ficha-cidade-panel` docado à esquerda (`position:fixed; left:0;
top:0; height:100vh; transform:translateX(-100%)`), classe `.open` desliza para
`translateX(0)`. Backdrop `#ficha-cidade-backdrop` (clicar fora fecha). Botão ✕ no
topo. Reabrir com outro herói re-renderiza o conteúdo.

### 5. Corpo do painel — `renderFichaCidadeBody(player, editable)`
- **Cabeçalho:** foto, nome, classe, nível (do registro do jogador).
- **Atributos:** `renderConteudoAtributosFichaJogo(heroiStatic, player)` (reuso).
- **Equipamento:** paper-doll dos 8 `EQ_SLOTS` lendo `player.gear` (espelha o
  bloco do `renderMyPanel`, game.js:9366). Se `editable`: clique no slot cheio
  desequipa (`unequipSlot`); é alvo de drop. Se não: só leitura.
- **Inventário:** `bag_size` slots lendo `player.bag`. Se `editable`: cada item é
  arrastável + botão equipar (`equipFromBag`/`equipOffhand`); slots são alvo de
  drop para reordenar. Se não: só leitura.

`editable = (player.id === GS.myPid)`.

### 6. Drag-and-drop (HTML5) — só no painel editável
- `dragstart` guarda a origem: `{kind:'bag', index}` ou `{kind:'gear', slotKey}`.
- Drop em **slot da bolsa** vindo de `bag` → `reorderBag(from, toIndex)`.
- Drop em **slot da bolsa** vindo de `gear` → `unequipSlot(slotKey)`.
- Drop em **slot de equipamento** vindo de `bag`:
  - slot `off_hand` e item é adaga/escudo → `equipOffhand(index)`;
  - senão → `equipFromBag(index)` (o servidor coloca no slot certo pela categoria).
- `dragover` com `preventDefault` nos alvos válidos + classe visual `.drop-target`.
- Senders cliente: `equipFromBag`/`equipOffhand`/`unequipSlot` já existem
  (game.js:10078+); adicionar `reorderBag(from,to)` → `send({type:'reorder_bag',
  from_index, to_index})`.

### 7. Re-render ao vivo
No handler `GS.on('cityState', …)`: se `#ficha-cidade-panel.open` existir,
chamar `_refreshFichaCidadePanel()` (re-renderiza o corpo com o player atual do
`city_state`). Guardar o `pid` aberto numa variável de módulo.

### 8. Remoção da v1
Remover `abrirFichaCidade` (modal central) e `_renderFichaCidadeEquip`/
`_refreshFichaCidade` cosméticos; substituídos pelo painel autoritativo. O ponto
de entrada (`onclick` no card) passa a chamar o novo `abrirFichaCidade(pid)`.

## Fluxo de dados

```
clique na foto do card → abrirFichaCidade(pid)
  └─ lê GS.cityState.players[pid] (gear/bag/atributos)
  └─ renderFichaCidadeBody(player, editable = pid===myPid)
       editable: botão/drag → equipFromBag/equipOffhand/unequipSlot/reorderBag
         → servidor muta gear/bag → broadcast_city_state (phase==city)
         → GS.on('cityState') → _refreshFichaCidadePanel()
```

## Tratamento de erros / casos de borda

- **Drop em slot vazio da bolsa** além de `len(bag)`: `to_index` é clampado para o
  fim da lista (move para o fim). Sem erro.
- **Equipar com restrição de classe / 2 mãos / bolsa cheia:** o servidor já recusa
  e envia `error`; o cliente mostra o toast e o estado não muda.
- **Arrastar no painel só-leitura:** itens não recebem `draggable`; slots não são
  alvos de drop.
- **Foto ausente/erro de carregamento:** `onerror` cai para o emoji da classe.
- **city_state ainda não chegou:** cards só existem após o estado; sem caso
  degenerado.

## Testes

- **Servidor (`tools/test_*.py`, padrão asyncio):** novo
  `tools/test_ficha_cidade.py` cobrindo:
  - equipar na fase city → item vai de `bag` para o `gear` certo e o broadcast é
    `city_state` (não `game_state`);
  - desequipar na cidade devolve à bolsa;
  - `reorder_bag` troca a ordem dos itens (e clampa índices fora do intervalo);
  - equipar na masmorra continua emitindo `game_state` (não regrediu).
- **Cliente:** sem harness unitário; verificação manual no app (carregar página
  valida sintaxe; exercício do painel/drag in-browser).

## Fora de escopo (YAGNI)

- Usar consumível pela ficha da cidade.
- Editar a ficha de outros heróis.
- Recorte por-herói “fino” da foto (usa-se um `object-position` único; ajuste fino
  pode vir depois).
- Persistência adicional além do que `gear`/`bag` já fazem.
