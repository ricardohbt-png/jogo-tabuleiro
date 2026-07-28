# História em slides nas aventuras do mapa-múndi

**Data:** 2026-07-28
**Status:** aprovado (brainstorming)
**Depende de:** `2026-07-28-masmorra-sequenciada-saida-individual-design.md`

## Problema

A feature de masmorra sequenciada deu a cada etapa de aventura um `intro` e um `outro`,
mas o editor de mapa-múndi só oferece **textarea** — não dá para usar imagens nem áudio,
que o sistema de história já suporta desde a Fase 4b das campanhas.

Além disso, dos três momentos possíveis só um está ligado: a transição encadeada.
Entrar numa aventura não mostra a abertura da 1ª etapa, e o `outro` da última etapa
nunca é exibido — a rota termina e o grupo cai direto na cidade.

Por fim, ao voltar de uma masmorra o jogador reencontra o **mapa-múndi**, não a cidade.
O mapa-múndi é um overlay sobre `screen-city` que só é escondido quando a cidade muda
(`_refreshCityLocation`); como entrar numa aventura não muda `world_location`, o overlay
continua aberto por baixo e reaparece na volta.

## Escopo

1. Editor de slides (imagem + texto + áudio) para a abertura e o encerramento de cada
   etapa de aventura, reusando o editor que já existe nas campanhas.
2. Exibir os três beats: abertura da 1ª etapa, transição encadeada (já existe) e
   encerramento da rota.
3. Ao voltar da masmorra, cair na ilustração da cidade em que o grupo estava.

## Decisões de design

| Questão | Decisão |
|---|---|
| Encerramento da rota | É o `outro` da **última etapa** — sem campo próprio de "fim de rota" |
| Editor de slides | **Extraído** de `editor_campaign.js` para um módulo compartilhado |
| Formato salvo | String quando é um slide só de texto (retrocompatível); `{slides, audio}` quando há imagem ou áudio |
| Onde o encerramento aparece | Sobre a tela da **cidade** — ao fechar o slideshow o grupo já está nela |
| Voltar para a cidade | O cliente esconde o overlay do mapa-múndi ao entrar na masmorra |

## Arquitetura

### Editor

O editor de slides (miniatura, upload de imagem, áudio em loop, reordenar, pré-visualizar)
está hoje dentro do IIFE de `tools/editor_campaign.js`. Oito funções saem para um
`tools/editor_story.js` novo, exposto como `window.EDITOR_STORY`, **sem mudança de
lógica**: `emptyStory`, `storyFromSaved`, `storyToSaved`, `storyCount`, `histButtonHTML`,
`pickFile`, `openHistoryEditor`, `slideCard`. O upload de mídia já é um módulo
compartilhado (`window.STORY_UPLOAD`, em `tools/story_upload.js`), então nada de rede se
move. `editor_campaign.js` passa a consumir o módulo e a aba Campanha deve continuar
idêntica — é a verificação de não-regressão da extração.

Em `tools/editor_world.js`, as duas textareas por etapa viram dois botões
**"📖 abertura"** e **"📖 encerramento"** com contador de slides, abrindo o mesmo painel.
`storyFromSaved` normaliza o que veio do arquivo (string legada ou objeto) e
`storyToSaved` devolve a forma mínima ao salvar.

No servidor, `_save_world_adventures_upload` hoje força `str(et["intro"])[:2000]`, o que
destruiria um objeto de slides. Passa a usar um helper novo `_clean_story_field(raw)`,
que aceita string ou `{slides:[{text,image,fit}], audio}`, descarta slides vazios,
limita o texto e **restringe os caminhos de mídia a `assets/story/`**.

### Runtime

Os três beats usam o mesmo campo `story`, que o cliente já consome sem alteração:
`_captarStory` (`src/gameState.js`) lê `msg.story` de qualquer mensagem e deduplica por
`key`.

| Momento | Onde é montado | Como chega ao cliente |
|---|---|---|
| Abertura da etapa | `handle_world_adventure` | `game_state.story` |
| Transição encadeada | `_emendar_proxima_etapa` (já existe) | `game_state.story` |
| Encerramento (volta à cidade) | ramo não-encadeado de `handle_encerrar_missao` | `city_state.story` |

O ramo não-encadeado emite o `outro` da etapa **recém-concluída**, seja ela a última da
rota ou uma intermediária sem `encadear` — nos dois casos o grupo volta à cidade e é o
mesmo beat. Tratar só a última deixaria o `outro` de uma etapa intermediária ser
silenciosamente descartado. Como a abertura é montada em `handle_world_adventure`, ela
vale para **toda** etapa iniciada pelo mapa, não só a primeira.

Para o encerramento, `_city_state_payload` ganha `"story": self._story_encadeada` — o
mesmo atributo já usado pelos outros dois beats, já limpo em `_voltar_para_cidade`. A
ordem importa: o beat precisa ser gravado **depois** de `_voltar_para_cidade` limpá-lo,
ou o `broadcast_city_state` sairia sem ele.

Chaves dos beats (para o de-dup do cliente): `aventura:<id>:<indice>` na abertura,
`encadeada:<id>:<indice>` na transição (já existente) e `fim:<id>:<indice>` no
encerramento. A chave inclui o índice da etapa, então reentrar na mesma rota numa etapa
diferente mostra a abertura de novo; repetir a MESMA etapa (o grupo abandonou e voltou)
não mostra — o de-dup é por sessão de cliente.

| Momento | `key` |
|---|---|
| Abertura | `aventura:<adventure_id>:<indice>` |
| Transição | `encadeada:<adventure_id>:<indice da que começa>` |
| Encerramento | `fim:<adventure_id>:<indice da concluída>` |

### Volta para a cidade

Nada muda no servidor: `handle_world_adventure` nunca alterou `world_location`, então o
grupo já retorna à mesma cidade. O cliente passa a chamar `hideWorldMap()` no handler de
`enterDungeon`, de modo que o overlay não esteja mais aberto quando o `city_state` da
volta chegar. Isso cobre os três caminhos de retorno: fim da rota, abandono pela escada
e a saída individual de um herói.

## Testes

`tools/test_masmorra_sequenciada.py` ganha três seções:

1. **[15]** uma aventura salva com `intro` em objeto de slides (texto + imagem) sobrevive
   ao round-trip de `_save_world_adventures_upload`, e um caminho de imagem fora de
   `assets/story/` é descartado;
2. **[16]** `handle_world_adventure` monta o beat de abertura da 1ª etapa, com a `key`
   esperada, e ele sai no `game_state`;
3. **[17]** ao concluir uma etapa sem encadeamento (última ou intermediária), o `outro`
   dela sai no `city_state` — e uma etapa sem `outro` não emite beat nenhum.

Não-regressão: `tools/test_campanha.py` (seções de história) continua verde após a
extração do módulo, e a aba Campanha do editor é conferida no navegador.

## Fora de escopo

- Campo próprio de "encerramento da rota", separado do `outro` da última etapa.
- Slides no editor de masmorras avulsas (a masmorra em si não tem intro/outro).
- Beats na **campanha** (`mode == "campaign"`): ela já tem o seu próprio sistema de
  história e não é tocada, além de passar a usar o módulo de editor extraído.
