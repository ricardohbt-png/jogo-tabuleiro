# Ponto da cidade vinculado a uma masmorra

Data: 2026-08-04

## Problema

No editor de cidades, um ponto da ilustração só pode ser uma loja ou um local de
conversa. A única forma de partir para uma masmorra é pela Caravana de Viagem →
mapa-múndi → destino. Falta poder colocar uma entrada de masmorra direto na
ilustração da cidade — e as duas coisas (loja/local × masmorra) precisam ser
opções separadas na hora de criar o ponto.

## Decisões

1. **O vínculo aponta para um destino do mapa-múndi** (`WORLD_ADVENTURES`), não
   para um arquivo de masmorra. Assim o ponto herda de graça etapas encadeadas,
   requisitos, custo de 🍖/💧, progresso, revisitável, história em slides e
   destino oculto — tudo já implementado e testado.
2. **Dois botões de adicionar** no editor: loja/local (como hoje) e entrada de
   masmorra.
3. **O marcador espelha o mapa-múndi**: destino oculto não aparece; bloqueado
   aparece e o clique explica o que falta; concluído e não revisitável aparece e
   avisa.
4. **O clique abre um quadro de confirmação** com nome, custo, etapa e requisito,
   com o botão "Entrar" restrito ao anfitrião.

## Modelo de dados

O ponto de `CITY_MAP_POINTS[cidade][ponto]` ganha um campo opcional:

```json
{ "x": 40.0, "y": 55.0, "type": "dungeon", "name": "Cripta", "emoji": "🚪",
  "aventura": "cripta_dos_sussurros" }
```

`type:"dungeon"` já está na allow-list do servidor (`_load_city_map_points` e
`_save_city_shops_upload`) desde a entrada direta legada, mas nunca foi
oferecido pelo editor. Passa a ser o tipo do ponto de masmorra.

**Regra de integridade:** um ponto `dungeon` sem `aventura` válida não é
desenhado no jogo — espelha o que já vale para o ponto de `cena` sem cena
vinculada (botão morto na ilustração é pior que marcador ausente).

A checagem de **existência** do destino acontece no save do editor
(`_save_city_shops_upload`): id inexistente perde o campo `aventura`, e o ponto
continua salvo para o autor corrigir. No **boot** (`_load_city_map_points`) só
há checagem de formato do id, exatamente como já é feito com `scene`: se
`world_adventures.json` estiver ausente ou corrompido, `WORLD_ADVENTURES` fica
vazio e uma checagem de existência aqui apagaria todos os vínculos da memória —
que o próximo save do editor gravaria em disco. Formato no boot, existência no
save, e o filtro de payload cobre o resto.

`_garantir_pontos_implicitos` não cria pontos de masmorra: eles são sempre
autorais.

## Servidor

**Nenhuma mensagem nova.** A confirmação envia `world_adventure` com o id do
destino — o mesmo handler do mapa-múndi (`handle_world_adventure`), que já cobre
requisito, custo, etapa atual, revisita, validação da masmorra e a trava de
anfitrião. Um caminho só para os dois pontos de entrada.

**Filtro de spoiler.** `city_map_points` viaja no payload como o dicionário
global de todas as cidades. Um novo `_city_points_payload(self)` devolve uma
cópia sem os pontos de masmorra cujo destino não está visível para esta sala
(`_aventura_visivel`, o mesmo predicado que já filtra `world.adventures`). Assim
nem o id do destino oculto chega ao cliente. Destino visível porém bloqueado
continua no payload — é o marcador que o clique explica.

Os pontos de outros tipos passam intocados pela cópia.

Ponto de aplicação: há um único lugar que serializa `CITY_MAP_POINTS` para o
cliente — `"city_map_points": CITY_MAP_POINTS` no payload de cidade —, trocado
pela chamada nova. O payload do editor (`_city_shops_editor_payload`) **não**
filtra: o autor precisa enxergar o que criou.

## Cliente (`game.js`)

- `pointAllowed` ganha o ramo `dungeon`: só desenha o marcador se
  `point.aventura` estiver entre os `world.adventures` recebidos. Vale para o
  marcador nativo e para os criados pelo editor (o mesmo predicado atende os
  dois laços).
- `_cityHotspotClick`, no ramo `type === 'dungeon'`, deixa de chamar
  `triggerDungeonEntrance()` e abre o quadro de confirmação do destino
  vinculado. A função legada permanece intocada (o botão oculto "⚔ Entrar na
  Masmorra" continua como está).
- O quadro reusa o conteúdo do painel do mapa-múndi (nome, `🍖 -N / 💧 -N`,
  "Próxima etapa: 2 de 3", requisito pendente, "Rota concluída" sem botão,
  botão desabilitado com título "Apenas o anfitrião inicia a expedição."). Esse
  trecho é **extraído do painel do mapa-múndi para uma função compartilhada** e
  chamado pelos dois — em vez de duplicar as regras de exibição em dois lugares
  que sairiam de sincronia.
- Fechar o quadro volta à ilustração, sem entrar.

Fora de escopo: o marcador no modo 3D da cidade (`_CTY_BLDGS`) — pontos do
editor só existem no modo ilustração, como já acontece hoje com todos eles.

## Editor de cidades (`tools/editor_city.js`)

Na aba do mapa da cidade, o botão `+ Adicionar ponto` vira dois:

- `+ Adicionar ponto (loja/local)` — cria `{type:'mercador', name:'Novo ponto'}`,
  comportamento atual.
- `+ Adicionar entrada de masmorra` — cria
  `{type:'dungeon', emoji:'🚪', name:'Entrada de masmorra'}`.

O painel do ponto escolhe o formulário pelo tipo:

- Tipo `dungeon`: o campo "Tipo / loja vinculada" é substituído por "Destino
  vinculado", um `<select>` com os destinos de `world_adventures` (nome + id).
  Opção vazia "— nenhum destino —" e aviso visível quando o destino escolhido
  não tem masmorra (`dungeons` vazio) ou quando nenhum destino foi escolhido,
  já que nesse caso o marcador não aparece no jogo.
- Demais tipos: formulário atual, sem `dungeon` no dropdown (o tipo só se obtém
  pelo botão dedicado, mantendo as duas opções realmente separadas).

Nome, emoji, X e Y são iguais nos dois. A aba de cidades não conhece os destinos
hoje (só a aba do mapa-múndi os carrega), então `_city_shops_editor_payload`
passa a incluir uma lista enxuta `adventures: [{id, nome, dungeons: N}]` — o
suficiente para montar o `<select>` e o aviso de destino sem masmorra.

## Testes

`tools/test_cidades_editor.py`, seção nova:

1. Round-trip: ponto `dungeon` com `aventura` válida sobrevive a save → arquivo
   → boot com o campo intacto.
2. `aventura` inexistente é descartada no save e no load; o ponto permanece.
3. Payload: destino oculto e bloqueado → o ponto some de `city_map_points` da
   sala; cumprido o requisito → o ponto aparece. Pontos de outros tipos não são
   afetados.
4. Destino visível mas bloqueado permanece no payload.
5. Entrada pelo ponto: `handle_world_adventure` com o id do destino do ponto
   produz o mesmo resultado do caminho pelo mapa-múndi (masmorra carregada,
   custo cobrado).

## Não faz parte

- Criar ou editar destinos/aventuras pela aba de cidades (segue no editor de
  mapa-múndi).
- Vincular o ponto a um arquivo `dungeons/*.json` avulso.
- Marcador de masmorra no modo 3D da cidade.
- Mudanças na entrada legada `triggerDungeonEntrance()`.
