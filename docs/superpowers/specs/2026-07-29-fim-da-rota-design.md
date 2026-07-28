# Fim da rota: história própria ao concluir a última etapa

**Data:** 2026-07-29
**Status:** aprovado (brainstorming)
**Depende de:** `2026-07-28-historia-em-slides-nas-aventuras-design.md`

## Problema

Cada etapa de uma aventura tem abertura e encerramento em slides. Ao concluir a última
etapa, o encerramento **dela** é exibido — mas não há onde escrever o fecho da **rota
inteira**, que é uma coisa diferente: a última masmorra termina, e a história que levou
o grupo por todas as etapas também.

Hoje o autor teria de misturar os dois textos no mesmo campo da última etapa, perdendo a
distinção entre "esta masmorra acabou" e "esta jornada acabou".

## Escopo

Um campo de história por **destino** (não por etapa), exibido logo após o encerramento da
última etapa, antes de o grupo chegar à cidade.

## Decisões de design

| Questão | Decisão |
|---|---|
| Onde o campo mora | No **destino** (`outro_rota`), ao lado de nome/custos/requisitos |
| Quando aparece | Ao concluir a **última** etapa, emendado ao encerramento dela, no mesmo slideshow |
| Etapa intermediária | Só o encerramento dela — o fim da rota não dispara |
| Momento da transição | **Não muda**: o beat viaja no `city_state` e o slideshow é um overlay de tela cheia, então o jogador lê antes de ver a cidade |
| Formato | Mesmo dos demais campos de história: string ou `{slides, audio}` |

## Arquitetura

### Servidor

O destino ganha `outro_rota`, normalizado por `_clean_story_field` em
`_save_world_adventures_upload` — o mesmo helper que já protege os campos de história das
etapas (aceita string ou objeto de slides; restringe mídia a `assets/story/`).

No ramo não-encadeado de `handle_encerrar_missao`, o beat de encerramento passa a ser
montado com duas partes:

```python
partes = [etapa.get("outro")]
if completed_index + 1 >= len(stages):      # foi a última etapa: a rota acabou
    partes.append(adventure.get("outro_rota"))
fim = _story_beat(f"fim:{adventure_id}:{completed_index}", partes)
```

`_story_beat` concatena as partes na ordem e descarta as vazias, devolvendo `None` se
tudo estiver vazio. Consequências, todas sem código extra:

- etapa intermediária sem encadeamento → só o encerramento dela;
- última etapa → encerramento da etapa **e** fim da rota, em sequência no mesmo
  slideshow;
- destino sem `outro_rota` → idêntico ao comportamento de hoje.

A `key` do beat não muda (`fim:<id>:<indice>`), então o de-dup por chave do cliente
continua funcionando como está.

### Editor

Um botão **"🏁 fim da rota"** no painel do destino, logo abaixo de "Renome por etapa
concluída" — fora do bloco "Rota de masmorras", porque o campo é do destino inteiro e não
de uma etapa. Abre o painel de slides compartilhado (`EDITOR_STORY.openHistoryEditor`),
com o estado normalizado em `_outroRotaSt` e serializado por `storyToSaved` no salvar,
seguindo exatamente o padrão dos botões de abertura/encerramento das etapas.

### Cliente

Nenhuma mudança. O beat chega no `city_state` e `renderStory` o exibe como qualquer
outro.

## Testes

Seção [19] em `tools/test_masmorra_sequenciada.py`:

1. concluir a **última** etapa emite um beat com o encerramento da etapa seguido do fim
   da rota, nessa ordem;
2. concluir uma etapa **intermediária** não encadeada emite só o encerramento dela;
3. destino **sem** `outro_rota` continua emitindo só o encerramento da etapa
   (não-regressão);
4. `outro_rota` com slides sobrevive ao round-trip de `_save_world_adventures_upload`.

## Fora de escopo

- Segurar a transição para a cidade até o jogador fechar os slides (o overlay de tela
  cheia já resolve o que se queria).
- Campo equivalente de "início da rota" — a abertura da 1ª etapa já cumpre esse papel.
- Fim de rota em campanhas (`mode == "campaign"`), que têm o próprio `outro` de campanha.
