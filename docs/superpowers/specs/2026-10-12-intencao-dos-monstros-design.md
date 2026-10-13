# Intenção dos monstros (previsão) — design

Data: 2026-10-12. Estado: aguardando revisão do autor.

## Objetivo

Hoje o herói só descobre quem o monstro vai atacar depois de encerrar o turno.
A meta é permitir decidir com informação (posicionar, proteger, recuar ou atacar
primeiro), no estilo de *Into the Breach*, sem mudar nenhuma regra de combate.

Escolha do autor: **previsão** ("o que ele faria se agisse agora"), com a
estrutura de dados pronta para evoluir depois para **compromisso** (o monstro
grava a intenção no fim do turno e a executa no seguinte).

## Fora de escopo

- Gravar a intenção na IA e fazê-la valer no turno seguinte (evolução B).
- Setas para habilidades de área e sons.
- Simular o movimento passo a passo dos monstros.

## 1. Módulo de previsão (servidor)

Mixin novo `monster_intent.py` (mesmo padrão de `tutorial_training.py`), só leitura.

`_prever_intencoes(pid)` devolve um item por monstro que o jogador enxerga:

```
{ monstro_id, alvo_id, alvo_tipo,   # heroi | animado | prisioneiro
  acao,          # "corpo" | "distancia" | "ameaca"
  alcanca,       # chega e ataca neste turno?
  casa_ataque,   # [x, y] de onde ataca (se alcanca)
  certeza }      # "firme" | "provavel"
```

Decisão, reusando a IA real:

1. Alvos por `_alvos_visiveis_para_monstro`; escolha por `_get_monster_primary_target`.
2. Monstros processados na **ordem da iniciativa**.
   Antes de começar guarda `_monster_ai_focus_target_id` e as casas reservadas;
   **restaura ambos em `finally`**. A previsão não altera a IA real.
   *Nota de implementação (revisão final):* na masmorra a iniciativa roda um
   `gm_phase(m)` por monstro e cada chamada zera o foco — não existe foco coletivo
   entre monstros. A previsão zera o foco antes de cada monstro; as casas reservadas
   continuam acumuladas (aproximam onde os monstros anteriores pararão). O
   orçamento de movimento é o do próximo turno (`_water_turn_moves` numa cópia),
   posto em `_water_moves_left` só durante o cálculo; ficha sem `ai_type` (caminho
   legado) só alcança se já estiver ao alcance.
3. `alcanca` = BFS de movimento (`_master_reach_bfs`) + `_monster_attack_in_range`.
4. Sem movimento simulado: tudo parte das posições atuais. "Firme" só quando o
   alvo está em alcance direto e nada pode mudar a escolha (sem provocação ativa
   nem outro monstro competindo); nos demais casos, "provável".

Exclusões: monstro dormente (`_monstro_ativo_em_combate` falso); Manual do Mestre
(sem previsão); Semi mostra o alvo forçado como "firme"; habilidade com rolagem
ou cooldown vira `acao: "ameaca"` com certeza "provável".

Cache por `(rodada, assinatura das posições de heróis e monstros)`.
*Nota:* a assinatura também cobre a vez e os campos que mudam a previsão sem
mover ninguém (invisibilidade, controle, altura, estados que tiram o turno, zonas).

## 2. Protocolo e visibilidade

- Cliente → servidor: `prever_intencoes {}` (com `heroi` no Solo com grupo).
- Servidor → cliente: `intencoes_monstros {rodada, itens:[…]}`, **privada**
  (`send_to`).
- O cliente pede no início da vez do herói (ou do herói em foco) e depois de
  mover/atacar, agrupando pedidos (≥ 250 ms). Nunca com a opção desligada, na
  fase dos monstros, fora da vez ou sendo o Mestre humano.
- Só entram monstros que o herói enxerga agora (mesma visão da névoa). Escondidos
  (ex.: Assassino Goblin invisível), em névoa ou em sala trancada: omitidos.
- Só em `phase == "playing"`, jogador vivo e na masmorra; fora disso, ignora.
  Limite de 1 resposta a cada 150 ms por jogador.
- O cliente descarta resposta cuja rodada/vez não bate com o estado atual.
  *Nota:* a resposta traz `vez` (= `current_turn` do `game_state` no pedido);
  `GS.intencoes()` só devolve itens enquanto rodada e vez baterem.
- `GS.pedirIntencoes()` e `GS.intencoes` em `src/gameState.js` (sem DOM), com
  cache invalidado a cada `game_state`, como `previsaoAtaque`.

## 3. Cliente (2D e 3D)

Regra híbrida:

- Padrão: seta só dos monstros cujo alvo previsto é herói meu ou aliado do grupo.
- Destaque forte: monstro sob o mouse/selecionado (qualquer alvo) + linha no tooltip
  ("⚔️ Vai atacar Pedro (provável)").
- Modo "todas": todas as setas dos monstros visíveis.

Aparência (a calibrar medindo): linha curva fina com ponta no alvo; cor por ação
(vermelho corpo a corpo, laranja distância, roxo ameaça); "firme" contínua,
"provável" tracejada e mais fraca; marcador na `casa_ataque` quando `alcanca`;
contador ×N quando vários miram o mesmo alvo.

`game.js`: `_desenharIntencoes2D` no fim do `renderMap` (redesenho ~12 fps como o
halo do tutorial); grupo `g3.intencoes` no 3D, malhas reaproveitadas, atualizado
no `startLoop3D`, respeitando a visão do herói.

Preferência por jogador em ⚙️ → Configurações de jogo: Desligado / Ameaças ao meu
grupo (padrão) / Todas, em `localStorage["lfh_intencoes"]` (com `try/catch`).
Atalho **T** alterna os modos (verificar colisão antes de implementar). Chaves
PT/EN e linha em "Como jogar".

## 4. Casos especiais e erros

- Provocação, Réquiem, Comando/Dominar: já entram em `_get_monster_primary_target`;
  viram "firme".
  *Nota:* Comando/Dominar NÃO entram ali (são tratados no despacho da iniciativa);
  monstro sob Comando/Dominar, dormindo, com medo, paralisado etc. não ganha seta
  (`_intent_perde_turno`, espelho de `_status_monstro_turno` e do prólogo).
- Sem alcance nem visão do alvo: `acao: "ameaca"`, `alcanca: false`; só no modo "todas".
- Monstro buscando a última posição (o "!"): sem seta de alvo.
- Hostilidade entre monstros: seta monstro→monstro só no modo "todas".
- Footprints grandes: seta do centro do corpo; alcance pelo cálculo da IA.
- Qualquer exceção em `_prever_intencoes` vira lista vazia; nunca derruba turno ou
  handler. Zero setas é estado válido.

## 5. Testes e critério de pronto

`tools/test_monster_intent.py`: (1) **paridade** com o alvo que a IA real escolhe
ao rodar `gm_phase` em cenários (ferido, conjurador, provocação, foco coletivo);
(2) **sem efeito colateral** no foco, casas reservadas e estado; (3) visibilidade
(névoa, sala trancada, invisível); (4) acesso (fora de `playing`, morto, taxa,
Mestre); (5) `alcanca` coerente com BFS + alcance, incluindo grande e à distância;
(6) Manual sem previsão e Semi com alvo forçado.

`tools/test_intencoes_cliente.js`: filtro padrão × "todas"; descarte de resposta
velha; contador ×N; preferência salva/restaurada; chaves PT/EN (`dividas.py` e o
placar de interface limpos).

Prova no navegador em cópia isolada (porta 8790+, sem tocar nos saves), com captura
por `renderer.render()` + `toDataURL` por causa do rAF em janela oculta.

## Evolução para B (não implementada)

A IA real passa a gravar o item acima em `m["intencao"]` no fim do turno do monstro
e a executá-lo no seguinte (com regra de fallback se o alvo sair). O cliente já
desenha a estrutura; a diferença é só a origem do dado e a promessa de "firme".
