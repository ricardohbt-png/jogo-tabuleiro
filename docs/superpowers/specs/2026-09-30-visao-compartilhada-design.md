# Visão compartilhada entre heróis — desenho

## Problema

No multiplayer, cada jogador só vê o que o **próprio** herói enxerga (raio de visão +
linha de visão, cortada pela sombra dos objetos altos). Quando o peão de um colega sai
dessa área, o que ele vê some da tela. Isso é desejado como padrão, mas o autor quer uma
opção para o grupo ver tudo o que qualquer herói vê, deixando o jogo mais dinâmico.

## Como a visão funciona hoje

- O servidor manda o **mesmo** `game_state` a todos (monstros e peões inclusos); não há
  filtro por visão no servidor.
- O cliente esconde o que não vê: `computeVisionSet(state, me)` (`game.js`) é o ponto
  único consultado por 2D, 3D, som, tooltips e alvos.
- Servos animados e elementais invocados **já** compartilham visão com todos: o servidor
  manda em `game_state.revealed` um raio de 2 casas com linha de visão em volta de cada
  um (`_live_reveal_tiles` / `MINION_VISAO_RAIO`). O prisioneiro resgatado não entra.

## Decisões

1. **Duas chaves** (opção C):
   - **Permissão do anfitrião** — `GameRoom.visao_compartilhada_permitida` (padrão
     `True`), alterada por `set_visao_compartilhada {enabled}` (só o anfitrião),
     salva no jogo salvo e enviada no `game_state` e no `city_state`. Molde: o limite de
     tempo por turno (`turn_timer_enabled` / `handle_set_turn_timer`).
   - **Escolha do jogador** — botão no painel ⚙️, salvo em
     `localStorage["lfh_visao_compartilhada"]` (padrão **desligado**).
   - A soma só acontece com as duas ligadas.
2. **Fontes somadas:** cada outro herói **vivo** e **dentro da masmorra**, com o raio
   (`getSightRadius`) e a linha de visão dele. Servos seguem como hoje (sempre
   compartilhados pelo servidor).
3. **Prisioneiro resgatado** passa a entrar em `_live_reveal_tiles` com o mesmo raio dos
   servos, sempre (independente da opção).
4. **Cegueira:** se o **seu** herói está cego, não soma a visão dos aliados (mesma regra
   que já suspende `revealed`).
5. **Sombra dos objetos:** casa que você enxerga pela visão de um aliado não é desenhada
   como "visão bloqueada".
6. **Fora de escopo:** atacar/mirar continua exigindo a linha de visão do seu herói
   (autoritativo no servidor); monstro escondido/invisível continua escondido; Mestre e
   mesa de teste inalterados.

## Componentes

- `server.py`: campo da sala, handler, despacho, payloads (`game_state`/`city_state`),
  jogo salvo (gravar/carregar), prisioneiro em `_live_reveal_tiles`.
- `src/gameState.js`: `setVisaoCompartilhada(enabled)` (envia a mensagem) e a função
  pura `heroisVisaoCompartilhada(state, myPid, ativa)` que devolve os heróis cuja visão
  entra na soma.
- `game.js`: preferência local, linha no painel ⚙️ (+ refresh no `_setLang` e na
  abertura do painel), `computeVisionSet` somando os heróis, filtro da sombra.
- `src/lang/interface.js` + `src/lang/erros.js`: textos PT/EN.

## Testes

- `tools/test_visao_compartilhada.py` (servidor): padrão permitido; anfitrião alterna;
  não-anfitrião recusado; campo no payload; persiste no jogo salvo; prisioneiro
  resgatado em `revealed`.
- `tools/test_visao_compartilhada_cliente.js` (node): `heroisVisaoCompartilhada` só com
  a opção ativa; exclui morto, fora da masmorra, o próprio herói e o caso cego; a fiação
  do `computeVisionSet` e do filtro da sombra.
