# Cenas de conversa por local — design

Data: 2026-07-30

## Problema

A cena de conversa da taverna funciona bem e o autor quer usá-la em outros
lugares da cidade (mercado, e locais novos como docas ou praça). Hoje isso é
impossível por duas razões estruturais:

1. `TAVERN_SCENES` é **uma cena por cidade** (`TAVERN_SCENES[city_id]`),
   enviada como `city_state.tavern` e renderizada num ponto fixo do cliente —
   a aba 0 da loja `taverna` (`GS.shopTabIdx===0` hardcoded em
   `_renderShopItems`).
2. O clique num ponto da ilustração descarta qual ponto foi clicado:
   `_cityHotspotClick(point.type)` (game.js) passa adiante só o **tipo** do
   prédio.

Além disso, uma conversa marcada como "Uso único" continua listada depois de
resolvida: o servidor manda `disponivel:false`, mas o cliente filtra apenas
por `oculta`, então o jogador só descobre que a conversa acabou ao clicar e
receber o erro "Esta conversa já foi concluída.".

## O que já existe (e não precisa ser construído)

- **"Uso único" por conversa**: o seletor já está no editor
  (`tools/editor_city.js`, `data-conv-once`) e o servidor já bloqueia a
  repetição (`handle_tavern_npc`, conjunto `tavern_conversations_done`,
  persistido no savegame).
- **Requisitos e efeitos de conversa**: renome mínimo, nível do grupo, fato,
  item; concede renome, fato e item. Tudo validado por
  `_clean_tavern_conversations` / `_clean_requirement`.
- **Pontos editáveis na ilustração**: `CITY_MAP_POINTS` já é a fonte única do
  que aparece na cidade, com editor de posição e sincronização por cidade.

## Decisões tomadas

| Questão | Decisão |
|---|---|
| Conversa resolvida | "Uso único" passa a **sumir** do menu (uma opção só, sem campo novo) |
| Modelo | Cena é entidade própria, **vinculada a um ponto** do mapa da cidade |
| Cena × loja | Cena vira a **aba "💬 Conversas"** do mesmo modal, como na taverna |
| Taverna | **Migra** para o sistema genérico — um caminho de código só |
| Ponto novo | Emoji e nome **livres** por ponto |
| Armazenamento | `CITY_SCENES[cidade][cena]`, seguindo o padrão dos outros dados de cidade |
| Nomenclatura | Renomear `tavern-*` → `cena-*` no CSS e nas funções |

## 1. Modelo de dados

`CITY_SCENES[cidade][cena]` substitui `TAVERN_SCENES[cidade]`. A cena guarda
o que a taverna já guarda, mais um rótulo:

```python
CITY_SCENES = {"alva_e_luz": {"taverna": {
    "nome": "Taverna",                  # rótulo da aba e título no editor
    "background": "assets/city/taverna.png",
    "art_ratio": 1.5,
    "mode": "individual",               # "individual" | "mask"
    "mask": "assets/tavern/frequentadores.png",
    "slots": [ ... formato atual, inalterado ... ],
}}}
```

Persistência em `city_scenes.json` (substitui `tavern_scenes.json`).
Id de cena: `[a-z0-9_-]{1,48}`, a mesma regra dos demais ids do projeto.

Como os outros três subsistemas de cidade (`CITY_SHOPS`, `CITY_MAP_POINTS`,
`TAVERN_SCENES`), `CITY_SCENES` é semeado na própria declaração e sincronizado
por `_sincronizar_cidades_derivadas` — criar e excluir cidade no editor
continua correto sem código novo.

### Vínculo cena ↔ ponto

O vínculo mora **no ponto**, não na cena. `CITY_MAP_POINTS[cidade][ponto]`
ganha o campo opcional `scene`:

```json
"mercador": {"x": 50, "y": 40, "type": "mercador", "scene": "boatos_do_mercado"},
"docas":    {"x": 18, "y": 72, "type": "cena", "emoji": "🌊", "name": "Docas", "scene": "docas"}
```

A direção importa: um ponto tem **no máximo uma** cena, então "duas cenas
disputando o mesmo local" não é um estado representável, e o runtime é uma
consulta direta (ponto → cena), sem varredura nem regra de desempate.

No editor a apresentação é invertida para casar com o modelo mental do autor:
dentro do painel da cena há um campo "Vinculada a" (dropdown de pontos).
Escolher um ponto grava `scene` nele **e limpa** o campo de qualquer outro
ponto que apontasse para essa cena.

### Ponto de tipo `cena`

- `valid_types` (em `_save_city_shops_upload`) ganha `"cena"`.
- O campo `emoji` passa a ser aceito em **qualquer** ponto, sobrepondo o emoji
  fixo de `pointMeta` (game.js) quando presente.
- `pointMeta` ganha a entrada `cena` (emoji padrão `💬`).
- `pointAllowed` (game.js) libera o tipo `cena` — ele não depende de loja.

A taverna migra para a cena de id `taverna`, vinculada ao ponto `taverna` que
`_garantir_pontos_implicitos` já cria. Sem caso especial: ela vira a primeira
cliente da regra geral.

## 2. Runtime e protocolo

### Payload

`city_state.tavern` (uma cena) → `city_state.scenes` (dicionário das cenas da
cidade atual). `_tavern_payload` vira `_cenas_payload`, aplicando por conversa
a mesma avaliação de requisito que já faz.

`city_state.city_map_points` já viaja hoje, então o cliente recebe de graça
qual ponto abre qual cena.

### Mensagem

`tavern_npc {npc_id, conversation_id}` → `scene_npc {scene_id, npc_id,
conversation_id}`. `handle_tavern_npc` → `handle_scene_npc`, mesmo corpo mais
o passo de resolver a cena antes do slot. Recusa cena inexistente com a mesma
forma de erro já usada para slot e conversa inexistentes.

### Chave de conversa concluída

`cidade:npc:conversa` → `cidade:cena:npc:conversa`.

### Filtragem no servidor (fecha o vazamento e entrega o "sumir")

Hoje `_tavern_payload` manda a conversa bloqueada **com o texto completo** e
apenas marca `oculta:true`; quem não a desenha é o cliente
(`conversations.filter(conv=>!conv.oculta)`). O comentário no servidor diz que
isso evita revelar spoilers pelo painel, mas não evita — o texto está no
payload.

`_cenas_payload` passa a **omitir do payload**:

- a conversa cujo requisito não foi cumprido;
- a conversa de uso único já concluída.

Consequências: o filtro do cliente desaparece; o vazamento fecha; e "sumir
depois de resolvida" sai como comportamento natural, não como uma segunda
regra. Os campos `disponivel` / `oculta` / `bloqueio` deixam de existir no
payload.

Custo aceito: some a possibilidade de a interface sinalizar "há algo trancado
aqui". Se isso for desejado depois, volta como um **contador** sem texto
(`trancadas: 2`), que é a forma que não vaza.

### O que fica igual de propósito

- Renome e fatos continuam **globais do grupo** — uma conversa nas Docas pode
  destravar outra na Taverna.
- O conjunto de conversas concluídas continua **um só por partida**,
  persistido no savegame.

## 3. Cliente

### `openShop` recebe o id do ponto

É a mudança de chave. `_cityHotspotClick(point.type)` descarta qual ponto foi
clicado, o que não se sustenta com uma cena por ponto. Passando o id, a função
resolve duas coisas independentes:

- **cena** = `scenes[ponto.scene]`, se o ponto tiver uma;
- **loja** = a loja de `ponto.type`, se aquele tipo for loja e a cidade a
  tiver.

As abas viram *[💬 nome da cena] + [abas da loja]*. Os três casos caem no mesmo
caminho:

| Ponto | Resultado |
|---|---|
| Taverna / Mercado com cena | aba de conversa + abas de compra |
| Ferreiro sem cena | só abas de compra — idêntico a hoje |
| Docas (tipo `cena`) | só a aba de conversa |

Os tipos que não são loja e já têm destino próprio — `dungeon`, `caravana`,
`guilda` — continuam despachando pelo tipo, **antes** dessa resolução, e o
dropdown "Vinculada a" do editor **não os oferece**. Assim não existe o estado
"cena vinculada a um ponto que nunca a abre".

Some o `GS.shopTabIdx===0` hardcoded para taverna. A aba de cena se identifica
por si mesma e `GS.activeScene` guarda a cena aberta, para o `scene_npc` saber
o que enviar.

### Cidade em 3D

O raycaster dos meshes conhece tipo de prédio, não ponto (`_cityClick` /
`MAPA_IDS_LOJA`). Ele resolve para o **primeiro ponto daquele tipo** na cidade
atual — correto, já que os prédios 3D são os nativos e há um ponto de cada.

### Renomeação

`.tavern-scene`, `.tavern-npc`, `.tavern-hud`, `.tavern-bg`, `.tavern-mask*`,
`.tavern-dialogue*`, `.tavern-back`, `.tavern-hint`, `.tavern-empty` e
`#shop-modal.tavern-cena` → prefixo `cena-`. `_renderTavernConversations` →
`_renderCenaConversas`; `_showTavernDialogue` → `_showCenaDialogo`;
`_openTavernNpcId` → `_openCenaNpcId`. Mecânico, em `game.js` e `game.css`.

A prévia do editor (`.cityed-tavern-preview`) mantém seu nome — é do editor,
não do jogo, e continua sendo a taverna de referência do WYSIWYG.

## 4. Editor

A aba "💬 Taverna e NPCs" vira "💬 Cenas e NPCs":

- lista das cenas da cidade + botão "+ Nova cena" (pede id e nome);
- selecionada uma cena, o painel abaixo é o de hoje — nome, fundo, máscara,
  NPCs, conversas, prévia WYSIWYG;
- campo **"Vinculada a"**: dropdown com os pontos da cidade e a opção "criar
  ponto novo", que pede emoji, nome e posição (x/y em %);
- botão de excluir cena (limpa também o `scene` do ponto vinculado).

O editor de conversas em si não muda. O seletor "Uso único" que já existe
passa a significar "some depois de resolvida".

## 5. Migração

**Arquivo.** No boot: `city_scenes.json` ausente e `tavern_scenes.json`
presente → converte uma vez. Cada cena vira `{cidade: {"taverna": cena}}` com
`nome: "Taverna"`, e o ponto `taverna` de cada cidade ganha `scene:"taverna"`.
O arquivo antigo permanece intocado como rede de segurança.

**Savegames.** As chaves de conversa concluída com 3 partes ganham `taverna`
no meio ao carregar (`cidade:npc:conversa` → `cidade:taverna:npc:conversa`),
para o jogador não ver conversas já resolvidas voltarem.

**Carregador.** `_load_tavern_scenes` é hoje um *merge sobre a base declarada
em código*: só edita cenas de cidades que já existem e só cria slots com
prefixo `npc_`. O carregador novo (`_load_city_scenes`) precisa poder **criar
cenas inteiras** vindas do arquivo, porque a partir de agora a maioria das
cenas não existe no código. Mantém a mesma disciplina de validação — ids por
regex, caminhos obrigatoriamente sob `assets/`, tetos de quantidade (32 slots
por cena, 12 conversas por slot, 40 pontos por cidade) — afrouxando apenas o
que impede criar. Teto novo: **16 cenas por cidade**.

## 6. Testes

`tools/test_cenas_conversa.py` (novo):

1. cena criada e vinculada a um ponto novo aparece em `city_state.scenes`, e o
   ponto traz o `scene`;
2. conversa de uso único **some** do payload depois de resolvida; a de uso
   repetido **permanece**;
3. ponto com loja + cena entrega as duas coisas (abas de compra continuam);
4. conversa bloqueada por requisito **não vaza texto** no payload;
5. migração do formato antigo: `tavern_scenes.json` → `CITY_SCENES` com a cena
   sob `taverna` e o ponto vinculado;
6. migração das chaves de savegame de 3 para 4 partes.

`tools/test_cidades_editor.py` ganha: criar e excluir cidade trata `CITY_SCENES`
como trata os outros derivados (cidade nova nasce sem cenas; cidade excluída
some do dicionário).

Como nos outros testes de cidade do projeto, os JSON reais são isolados numa
pasta temporária.

## Fora de escopo

- Conversa com ramificação em árvore — a lista com requisitos continua sendo o
  mecanismo de progressão.
- Cena de conversa dentro de masmorra (lá existem as falas de NPC, outro
  sistema).
- NPC que se move ou troca de imagem conforme o estado do jogo.
- Sinalização visual de "conversa trancada" (ver seção 2 — volta como contador
  se for desejado).
