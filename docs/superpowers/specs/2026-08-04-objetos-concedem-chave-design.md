# Objetos que concedem palavra-chave / item-chave

**Data:** 2026-08-04
**Status:** desenho aprovado, pronto para plano de implementação

## Problema

O editor não tem como fazer um objeto de masmorra **entregar** uma chave narrativa.
Hoje as palavras-chave globais do grupo (`self.fatos`) só nascem de conversas e
cenas de NPC (`efeito.fato`, `give_key`), e itens-chave só saem de baús. Falta o
elo: interagir com um altar, uma tumba ou uma estante e sair de lá com algo que
destranca uma missão ou revela um destino no mapa-múndi.

## O que já existe (e não muda)

| Peça | Onde | Papel |
|---|---|---|
| `self.fatos` | `GameRoom` | conjunto de palavras-chave globais do grupo; persistido no savegame (`_checkpoint_savegame` grava `fatos`, `load` restaura) |
| `_grupo_tem_item(item_id)` | server.py | procura o item na bolsa/equipamento de qualquer herói |
| `_avaliar_requisito(raw)` | server.py | já testa `renome_min`, `nivel_grupo_min`, **`item_id`**, **`fato`**, `aventura_id` |
| `_aventura_visivel` + `oculto_ate_liberar` | server.py | destino do mapa-múndi só aparece quando o requisito passa |
| `_route_acquired_item` | server.py | roteamento bolsa-primeiro de todo item adquirido |
| `key_objective` da decoração | server.py + editor | outra coisa: conclui o objetivo legado `open_key_chest` |

**Consequência importante:** o lado do *consumo* para "descobrir um novo local"
já está pronto. Esta feature não toca `_avaliar_requisito` nem `_aventura_visivel`.

## Decisões

1. **Concede palavra-chave E/OU item-chave**, escolha por objeto. Os dois campos
   são opcionais e independentes.
2. **Gatilho:** interagir com o objeto (`interagir_decor`), uma vez por partida.
3. **Uso na missão:** um tipo novo de objetivo, `possuir_chave` — principal ou
   secundário, no mesmo dropdown dos demais.
4. **Autoria da chave:** texto livre com autocompletar (`<datalist>`) alimentado
   por todas as chaves já concedidas ou exigidas em qualquer masmorra/destino.
   Sem cadastro prévio, sem arquivo novo.
5. **Feedback ao jogador:** narração do GM + a linha do objetivo no HUD. Sem tela
   nova.

### Abordagem escolhida para o "conceder"

Campo `concede` na decoração, aplicado em `handle_interagir_decor` — o menor
delta possível, ao lado do `key_objective` que já mora ali.

Descartadas: (a) lista genérica `efeitos:[{tipo,...}]` espelhando
`_scene_apply_effects` — motor para dois casos, YAGNI; (b) decoração dispara uma
cena que faz `give_key` — obriga uma cena inteira por chave. Se um dia surgir um
terceiro efeito, migrar `concede` → `efeitos` é mecânico.

## Servidor

### Formato

```json
"concede": { "fato": "selo_rei_morto", "item_id": "chave_bronze" }
```

Ambos opcionais. Ausente/vazio = comportamento atual, byte-idêntico.

### `handle_interagir_decor`

O bloco novo entra **depois** do ramo de `key_objective` e **antes** do ramo de
fonte/container, para que um objeto-chave que também é baú funcione nos dois
papéis na mesma interação.

- **`fato`** → `self.fatos.add(fato)`, narração
  `📜 **<nome>** descobriu: <fato>`. Nunca falha (não ocupa espaço).
- **`item_id`** → resolve no catálogo mesclado e passa por `_route_acquired_item`.
  Retorno `'full'` → erro `"Inventário cheio!"` e a decoração **não** é marcada
  como concedida; o herói volta depois e pega.
- Flag `concedido` (bool) na decoração impede duplicar fato/item e re-narrar;
  vai no `game_state` junto dos demais campos serializados da decoração.

Ordem dentro do bloco: concede o fato primeiro, o item depois. Se o item falhar,
o fato já concedido permanece — `fatos` é idempotente, então a re-interação só
tenta o item de novo.

### Objetivo `possuir_chave`

```json
{ "type": "possuir_chave", "fato": "selo_rei_morto", "item_id": "chave_bronze" }
```

Pelo menos um dos dois campos. Com os dois preenchidos, exige **ambos**.

`_objetivo_cumprido` ganha o ramo:

```python
if t == "possuir_chave":
    fato = (obj.get("fato") or "").strip()
    item = (obj.get("item_id") or "").strip()
    if not fato and not item: return False
    if fato and fato not in self.fatos: return False
    if item and not self._grupo_tem_item(item): return False
    return True
```

Nada mais muda: recompensa (XP/ouro/baú de itens), `mission_complete_pending` e o
botão "🏁 Encerrar missão" saem do caminho já existente de `_check_objectives`.
`_objetivo_payload` não precisa de campo extra — o rótulo é montado no cliente a
partir do próprio objetivo.

### Validação (`validar_dungeon`)

- `concede`, se presente, deve ser dict.
- `concede.fato`: string, ≤100 caracteres (mesmo teto aplicado na carga do
  savegame em `room.fatos`).
- `concede.item_id`: string existente no catálogo de itens mesclado.
- Objetivo `possuir_chave` sem `fato` **e** sem `item_id` é recusado.

## Editor

### Painel da decoração (`tools/editor.js`)

Bloco novo **"🔑 Concede ao interagir"**, abaixo do checkbox "objeto-chave":

- **Palavra-chave** — `<input list="ed-chaves">`.
- **Item-chave** — o mesmo seletor de `CAT.items` já usado em baús/recompensas,
  com opção vazia.
- Dica curta esclarecendo que isto é diferente do "objeto-chave" legado (que
  conclui `open_key_chest`).

`buildJSON` serializa `concede` só quando pelo menos um campo está preenchido;
o loader lê o campo de volta.

### Datalist global de chaves (`tools/editor_keys.js`)

Módulo novo, sem DOM, ~40 linhas, testável em node (padrão do
`editor_items_logic.js`). Coleta e deduplica, em ordem:

1. decorações e objetivos da masmorra aberta (estado `S`);
2. `window.EDITOR_DUNGEONS[].defn` — `decorations[].concede.fato` e
   `objectives.primary/secondary[].fato` (o índice gerado guarda o defn completo);
3. requisitos do mapa-múndi — `requisito.fato` em `world_adventures`.

Um único `<datalist id="ed-chaves">` é injetado uma vez e usado pelos campos que
**concedem** e pelos que **consomem** chave: objetivo `possuir_chave`, requisito
do destino no mapa-múndi (`tools/editor_world.js`) e requisito de conversa.

### Dropdown de objetivos

Entrada nova **"Obter a chave"**. Ao selecioná-la, aparecem os dois campos
(palavra-chave com datalist + seletor de item), no mesmo padrão condicional dos
forms do Editor de Itens.

## Cliente

- Narração: já coberta por `gm_say`.
- `_objRow` (`game.js`) ganha o rótulo do tipo novo: `Obter: <fato>` /
  `Obter: <item>` / os dois. Status pendente/cumprido vem do
  `_objetivo_payload` existente.
- **Nenhuma mensagem WebSocket nova** — `interagir_decor` já é o gatilho.

## Testes

`tools/test_chaves_objetos.py`:

1. Objeto concede fato → `fatos` contém a chave; segunda interação não duplica
   nem re-narra.
2. Objeto concede item → cai na bolsa via `_route_acquired_item`; bolsa cheia →
   recusa **sem** marcar `concedido`, e a re-interação depois de liberar espaço
   entrega.
3. Objetivo `possuir_chave` pendente → cumprido após interagir; concede
   recompensa e liga `mission_complete_pending`. Cobre também o caso de exigir
   fato **e** item.
4. Ponta-a-ponta do pedido: fato ganho na masmorra → volta pra cidade → destino
   com `oculto_ate_liberar` + `requisito.fato` **aparece** no `city_state`, e
   antes disso não aparecia.
5. Regressão: decoração sem `concede` → estado byte-idêntico ao de hoje.
6. `validar_dungeon` recusa `concede` malformado e `possuir_chave` vazio.

`tools/test_editor_keys.js` (node): o extrator de chaves sobre um defn sintético
— dedupe, ordem, e tolerância a campos ausentes.

## Fora de escopo

- Registro global de chaves com nome legível e ícone (cadastro prévio).
- Painel "📖 Pistas" na cidade listando os fatos do grupo.
- Baús concedendo palavra-chave (um baú já pode carregar o **item**-chave).
- Consumir/gastar uma chave (uma vez obtida, é permanente).
- Monstros ou armadilhas concedendo chave.
