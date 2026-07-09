# Sub-projeto B — Roteamento unificado de compra/loot (bolsa-primeiro)

**Data:** 2026-07-09
**Escopo:** `server.py` (autoritativo). Cliente não muda.
**Depende de:** Sub-projeto A (dessincronização da cidade) — concluído.

## Problema

Hoje o roteamento de um item recém-adquirido é inconsistente entre os pontos de
aquisição:

- **Compra de arma/armadura/escudo:** slot livre → auto-equipa; slot ocupado →
  bolsa; bolsa cheia (com slot ocupado) → recusa.
- **Compra de anel/acessório:** vai **sempre** pra bolsa; nunca auto-equipa num
  slot livre; bolsa cheia → recusa.
- **Loot de baú / drop de monstro:** tudo vai pra bolsa via `_add_to_inventory`;
  bolsa cheia → recusa; nunca auto-equipa.

Consequência: quando a bolsa está cheia mas um slot de equipar está livre, o item
é recusado — mesmo havendo espaço lógico para ele. A regra de negócio desejada
("não pode adquirir só quando a bolsa **E** os slots correspondentes estiverem
ocupados") não é atendida.

## Modelo desejado — "bolsa-primeiro com resgate-equipar"

Um item adquirido é **colocável** quando **(a bolsa tem espaço) OU (um slot
correspondente está livre)**. A preferência, quando ambos estão disponíveis, é a
**bolsa** (equipar é uma ação manual do jogador).

### Regra única

Novo helper `_route_acquired_item(p, item)` → retorna `'bag' | 'equipped' | 'full'`:

1. **Bolsa tem espaço** (`len(bag) < bag_size`) → anexa à bolsa. Retorna `'bag'`.
   Vale inclusive para o 1º item de um slot vazio (muda o comportamento atual de
   auto-equipar).
2. **Bolsa cheia, mas um slot correspondente está livre e o item é equipável ali**
   → auto-equipa como **resgate** (log avisa "bolsa cheia — equipado direto").
   Retorna `'equipped'`.
3. **Bolsa cheia E todos os slots correspondentes ocupados** (ou o item não é
   equipável por conflito) → Retorna `'full'`. O chamador recusa: compra estorna o
   ouro; loot permanece no baú.

### Slots correspondentes por categoria

Reusa `_slot_category_for_item(item)` (já existe):

| categoria | slot(s) alvo |
|---|---|
| `weapon` | `weapon` |
| `armor` | `armor` |
| `off_hand` | `off_hand` |
| `head` | `head` |
| `boots` | `boots` |
| `ring` | `ring1` **ou** `ring2` (primeiro livre) |
| `item` | `item1` **ou** `item2` (primeiro livre) |
| `bag` (consumível) | — (sem slot; só a bolsa) |

### Resgate-equipar: reaproveitamento e conflitos

- O passo 2 deve respeitar as mesmas validações do equipar manual
  (`_executar_equip_from_bag`): restrição de classe (`allowed_classes`) e conflito
  de arma de 2 mãos × escudo/2ª arma. Se o conflito impedir o equipar, o passo 2
  falha e cai para o passo 3 (`'full'`).
- Ao equipar arma, sincronizar a cópia de combate `p["weapon"]` (mesmos campos que
  `_executar_equip_from_bag` copia) — senão o jogador continua "desarmado" no
  combate mesmo com a arma no slot.
- Equipar aplica efeitos de gear (`_apply_gear_effect` / `_equip_into_slot` /
  `_equip_into_pair`), que já cuidam de CA/atributos.

## Exceções (permanecem fora do helper)

- **Munição** (`effect == "ammo"`): mantém o empilhamento especial atual em
  off_hand/bolsa nos dois pontos (compra e loot). Não passa pelo helper.
- **Consumíveis** (`cat == "bag"`: poções, pergaminhos, provisões): sem slot de
  equipar; passo 1 (bolsa) ou passo 3 (`'full'`). O helper já cobre isso
  naturalmente (categoria `bag` não tem slot alvo → só bolsa).

## Pontos de chamada a alterar

1. **`handle_buy_item`** (`server.py` ~4803):
   - `ferreiro_weapon`: substituir o ramo "slot livre → auto-equipa / ocupado →
     bolsa" por `_route_acquired_item`. Mensagens conforme o retorno.
   - `ferreiro_armor` (armadura e escudo): idem. Munição continua no ramo próprio.
   - `mercador`/`ferreiro_ammo`/`taverna` (acessório/anel/elmo/bota): substituir o
     ramo "sempre bolsa" por `_route_acquired_item`. Munição e consumíveis
     (`slot == "bag"`/`ammo`) mantêm ramos próprios.
   - Em `'full'`: estornar o ouro e enviar erro (comportamento atual preservado).
2. **`handle_take_from_chest`** (`server.py` ~8544): o ramo não-munição passa a usar
   `_route_acquired_item` em vez de `_add_to_inventory`. Em `'full'`, mantém o item
   no baú e envia erro. **O loot de monstro chega por aqui** — ao morrer, o monstro
   larga um baú (`_spawn_chest` em `_monster_dies`), então não há um ponto de
   "drop direto no inventário" separado a alterar.
3. **`handle_take_from_decor`** (`server.py` ~12221): loot de decoração-container
   (pode ser equipamento) passa a usar `_route_acquired_item`. Em `'full'`, mantém
   o item no container e envia erro.

**Fonte** (`interagir_decor`, `server.py` ~12178): dá `garrafa_agua`, um
consumível — roteável pelo helper (categoria `bag` → bolsa/`'full'`), sem
comportamento novo. Pode migrar para o helper por consistência ou permanecer em
`_add_to_inventory` (é o passo 1 do helper de qualquer modo).

`_add_to_inventory` é mantido (o helper o usa internamente no passo 1).

## Comportamento alterado (intencional)

- Comprar arma/armadura/escudo com o slot **livre** deixa de auto-equipar: agora
  vai pra bolsa. O jogador equipa pelo boneco (modal de inventário). Auto-equipar
  só ocorre como resgate quando a bolsa está cheia.
- Anéis/acessórios e loot passam a poder ser adquiridos com a bolsa cheia, desde
  que exista um slot correspondente livre (resgate-equipar).

## Verificação

Teste novo `tools/test_roteamento_itens.py` (estilo dos demais `tools/test_*.py`),
cobrindo, por categoria (arma, armadura, escudo, anel, acessório, consumível):

- Bolsa com espaço → `'bag'` (não auto-equipa mesmo com slot livre).
- Bolsa cheia + slot livre → `'equipped'` (resgate) + efeitos aplicados + (arma)
  `p["weapon"]` sincronizado.
- Bolsa cheia + slots ocupados → `'full'` (compra estorna ouro; loot fica no baú).
- Conflito de 2 mãos no resgate → `'full'`.
- Munição e consumível seguem seus caminhos próprios (não regridem).

Rodar da raiz: `python tools/test_roteamento_itens.py`.
