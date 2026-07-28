# Destino oculto no mapa-múndi até cumprir o requisito

**Data:** 2026-07-29
**Status:** aprovado (brainstorming)

## Problema

Todo destino de aventura marcado no mapa-múndi aparece para o jogador desde o início.
Um destino com requisito (renome, nível do grupo, item-chave, informação de taverna ou
rota anterior concluída) fica visível, com o requisito listado na prévia, e o servidor
apenas recusa a entrada. Não há como o autor esconder um destino até que ele seja
liberado — a existência do conteúdo é entregue de graça.

## Escopo

Uma opção por destino, no editor de mapa-múndi, que **remove o ponto do mapa** enquanto
o requisito não estiver cumprido. Ao cumprir, o ponto aparece sozinho.

## Decisões de design

| Questão | Decisão |
|---|---|
| O que o jogador vê enquanto bloqueado | **Nada** — o marcador não existe no mapa |
| Onde o filtro acontece | **No servidor**, no payload do `city_state` — o destino nem chega ao cliente |
| Padrão | `false` — rotas já salvas continuam visíveis como hoje |
| Destino oculto acessado por mensagem forjada | Responde **"Destino de aventura inválido"**, igual a um id inexistente |
| Editor | Vê e edita o destino oculto normalmente |

## Arquitetura

### Servidor

Cada destino ganha o campo `oculto_ate_liberar` (bool), normalizado em
`_save_world_adventures_upload` junto dos demais campos.

Um helper decide a visibilidade:

```python
def _aventura_visivel(self, adventure):
    """Destino oculto some do mapa até o requisito ser cumprido. Sem o flag,
    o destino é sempre visível (bloqueado ou não), como sempre foi."""
    if not adventure.get("oculto_ate_liberar"):
        return True
    return self._avaliar_requisito(adventure.get("requisito"))[0]
```

`_city_state_payload` passa a filtrar `world.adventures` por ele. Como o destino não
entra no payload, não há nada a espiar pelo cliente — a decisão é autoritativa.

`handle_world_adventure` já recusa quando o requisito não é cumprido, mas hoje a
mensagem enumera o que falta ("requer renome 5, item-chave: …"). Para um destino oculto
isso vazaria justamente o que se quer esconder. A guarda passa a responder **"Destino de
aventura inválido."** — a mesma resposta de um id inexistente — quando o destino é
oculto e ainda bloqueado. Um cliente forjado não distingue as duas situações. Destinos
**não** ocultos mantêm a mensagem detalhada de hoje, que é útil.

O payload do editor (`_world_adventures_editor_payload`) **não** filtra: o autor precisa
enxergar o destino que criou.

### Editor

Um checkbox **"🕵️ ocultar no mapa até liberar"** no painel do destino, dentro do bloco
"Requisitos para iniciar a rota" — é onde ele faz sentido, já que o requisito é a
condição que revela o ponto.

O checkbox fica **desabilitado**, com a dica "preencha um requisito para poder ocultar",
quando nenhum requisito está preenchido. O motivo: um requisito vazio **passa** em
`_avaliar_requisito`, então o flag sem requisito não esconde nada — o destino continua
visível. Desabilitar evita que o autor marque a caixa e ache que escondeu o ponto. É
orientação de UI, não trava: o servidor aceita o flag de qualquer forma e o resultado é
simplesmente um destino visível.

### Cliente

Nenhuma mudança. `showWorldMap` desenha o que vier em `world.adventures`.

## Testes

Seção [18] em `tools/test_masmorra_sequenciada.py`:

1. destino com o flag e requisito não cumprido **não** aparece em `city_state`;
2. cumprido o requisito (renome suficiente), ele aparece;
3. destino **sem** o flag e bloqueado continua aparecendo (não-regressão);
4. `handle_world_adventure` num destino oculto e bloqueado responde "Destino de aventura
   inválido." e não muda a fase da sala;
5. `_world_adventures_editor_payload` continua listando o destino oculto;
6. o flag sobrevive ao round-trip de `_save_world_adventures_upload`.

## Fora de escopo

- Marcador "???" ou qualquer pista visual de que há conteúdo bloqueado ali.
- Ocultar **cidades** (`WORLD_LOCATIONS`) — só destinos de aventura.
- Revelar por evento narrativo fora do sistema de requisitos que já existe.
