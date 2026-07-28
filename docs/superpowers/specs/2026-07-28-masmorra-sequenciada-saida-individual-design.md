# Masmorra sequenciada + saída individual pela escada

**Data:** 2026-07-28
**Status:** aprovado (brainstorming)

## Problema

Hoje, uma aventura do mapa-múndi com várias etapas (`WORLD_ADVENTURES[...]["dungeons"]`)
devolve o grupo à cidade/mapa-múndi ao fim de cada etapa: `handle_encerrar_missao`
chama `_voltar_para_cidade()`, e o anfitrião precisa clicar de novo no ponto do mapa
para começar a etapa seguinte. Isso quebra a sensação de "masmorra sequenciada" —
o autor não tem como emendar as fases.

Além disso, a saída pela escada (`handle_exit_dungeon`) leva o **grupo inteiro** de
volta à cidade, de graça, de qualquer casa do mapa e a qualquer momento. Não existe
como um herói sozinho ir reabastecer enquanto os outros seguem, nem como o autor
proibir a saída numa masmorra sem volta.

## Escopo

1. **Etapas encadeadas:** ao encerrar uma etapa marcada como encadeada, a próxima
   masmorra começa imediatamente, sem passar pela cidade nem pelo mapa-múndi.
2. **Saída individual:** a escada passa a ser pessoal — o herói sai sozinho, paga
   fome/sede da viagem e espera N rodadas antes de reentrar; a masmorra continua
   rodando para os demais.
3. **Controles no editor:** encadeamento por etapa (editor de mapa-múndi), permissão
   de saída por masmorra (editor de masmorras), custo e espera por aventura.

## Decisões de design

| Questão | Decisão |
|---|---|
| Descanso entre etapas encadeadas | **Nada se recupera** — HP, fome/sede, slots de magia, recargas de técnica, corrosão e status atravessam a emenda |
| Saída pela escada | **Sempre individual**; se todos saírem, a sala volta à cidade |
| O que o ausente pode fazer | **Cidade completa** (lojas, templo, taverna, guilda, ficha) |
| Espera em rodadas | **Uma só espera de ida e volta**: rolada na saída, ele só reentra quando zera |
| Custo de fome/sede | **Ida e volta cobrados na saída** (`2 ×` o custo da aventura); sem o total, não pode sair |
| Requisito para sair | **Estar na casa da escada, no próprio turno** |
| Onde fica o flag de encadear | **Na etapa da aventura** (mapa-múndi); campanhas ficam fora por ora |
| Onde ficam custo/espera | **Na aventura**; a permissão de saída fica **na masmorra** |
| Objetivo cumprido com herói fora | **Ele participa normalmente** — recebe XP/ouro e vai junto na etapa encadeada |
| Transição encadeada | **Encerramento da etapa + abertura da próxima**, em sequência |

## Arquitetura

A escolha central é como representar "um jogador na cidade enquanto a sala está na
masmorra", já que `self.phase` é da sala inteira. Adotada a **flag por jogador com
portão único**, seguindo o padrão que o projeto já usa para exceções pontuais
(`_is_turn` alargado no Último Esforço, `_mestre_ativo()`): um portão, muitos sites
intocados.

Alternativas descartadas: uma sala-sombra de cidade (duplica ouro/bolsa/savegame em
dois objetos e cria sincronização real) e transformar `phase` num dicionário por
jogador (toca dezenas de sites — timers, iniciativa, `end_game` — sem ganho
proporcional).

### Etapas encadeadas

`handle_encerrar_missao`, no ramo `if self.world_adventure_id:`, passa a consultar a
etapa recém-concluída. Se ela está marcada `encadear` **e** existe próxima etapa:

1. grava `world_adventure_progress` e concede o renome, como hoje;
2. monta o beat de história com encerramento da etapa N + abertura da etapa N+1
   (`_story_beat` já aceita várias partes) e o envia junto do `game_state` da nova
   masmorra;
3. avança `world_adventure_index`, carrega a masmorra da próxima etapa, seta
   `dungeon_generated = False` e chama `enter_dungeon(...)` — **sem** passar por
   `_voltar_para_cidade`.

Como `_voltar_para_cidade` é quem recarrega slots, zera `technique_cooldowns` e renova
refeições, não passar por ele já entrega "nada se recupera". O único ajuste é no bloco
`if nova:` de `enter_dungeon`, que reseta corrosão/vinho/cerveja/chamas por dungeon
nova: na emenda encadeada esses resets ficam suprimidos. Cadáveres, baús e itens no
chão continuam sendo limpos — é um mapa novo.

O custo de fome/sede da aventura **não** é cobrado de novo na etapa encadeada (o grupo
não voltou à cidade para partir outra vez). Heróis mortos continuam mortos.

### Saída individual

**Sair** — `handle_exit_dungeon` reescrito. Valida, nesta ordem:

- é o turno do jogador (`_is_turn`);
- ele está em cima de `stairs_pos`;
- a masmorra permite saída (`dungeon_def["saida_permitida"]`, default `True`);
- ele tem `2 × fome` e `2 × sede` da aventura.

Passando, debita o custo total, rola a espera e grava:

```python
p["fora_masmorra"] = {"rodadas_restantes": N}
```

e encerra o turno dele.

**Portão único — `_ativo(p)`.** Hoje é `alive and connected`, e já significa "está no
tabuleiro, na iniciativa e é alvo válido" (é assim que o desconectado sai da masmorra).
Passa a ser:

```python
return bool(p) and bool(p.get("alive")) and p.get("connected", True) \
       and not p.get("fora_masmorra")
```

Os 27 sites que consultam `_ativo` passam a tratar o ausente como um desconectado —
peão fora do tabuleiro, fora da fila de iniciativa, não é alvo de monstro nem de
habilidade — sem serem tocados.

**Na cidade.** Novo helper `_em_cidade(pid)` = `self.phase == "city"` ou o jogador tem
a flag. Substitui `if self.phase != "city"` em cinco handlers: `handle_shop_buy`,
`handle_shop_sell`, `handle_guild_buy`, `handle_guild_equip` e `handle_tavern_npc`.
Ficam **deliberadamente de fora** `handle_world_travel`, `handle_world_adventure`,
`enter_dungeon` e `handle_city_map_points` — são ações de grupo/anfitrião, e ninguém
viaja o mundo com metade do grupo numa masmorra.

`push_state_or_city` passa a mandar `city_state` individual (`send_to`) para cada
ausente e `game_state` para os demais.

**Contagem.** O decremento fica no fecho de rodada de `_advance_initiative` (onde
`round_num += 1`). Guarda-se **rodadas restantes**, não uma rodada-alvo absoluta —
assim o contador sobrevive a uma emenda encadeada, que reinicia o `round_num`. Ao
chegar a zero, o herói volta automaticamente: reaparece na escada de entrada (mesma
lógica do `rejoin` em partida), com movimento e ação cheios, e entra na iniciativa da
rodada seguinte. Ele também pode clicar em "Voltar à masmorra" assim que o contador
zera, sem esperar a virada.

**Casos-limite.**

- Se todos os heróis saírem, ou se todos os presentes na masmorra morrerem havendo
  herói vivo na cidade, a sala volta para a cidade (`_voltar_para_cidade`), com
  narração. O TPK atual testa `any(p["alive"] for ...)`, então um vivo na cidade já
  impede o game over sozinho — o que falta é não deixar a masmorra sem ninguém.
- Um herói fora conta como membro do grupo na divisão de XP/ouro dos objetivos e é
  levado junto na etapa encadeada.
- Sair encerra o turno; ele não age no mesmo turno em que saiu.

## Editor

**Editor de mapa-múndi (`tools/editor_world.js`), painel do destino:**

- cada linha da rota de masmorras ganha um checkbox **"⛓️ próxima começa
  imediatamente"**, desabilitado na última etapa;
- ao lado de 🍖/💧 de partida, a **espera para retornar**: modo `fixa` (número de
  rodadas) ou `dados` (fórmula `NdX`, com `+N` opcional).

`adventure["dungeons"]` é hoje uma lista de strings. Cada entrada passa a aceitar
**string (legado) ou objeto `{file, encadear}`** — mesmo padrão que campanhas já usam
com `_fase_obj`/`_fase_file`. Ganha-se um par de helpers `_etapa_obj`/`_etapa_file`, e
aventuras já salvas continuam válidas sem migração.

O custo de viagem da saída individual reusa os `fome`/`sede` que a aventura já tem
(cobrados ×2 na saída). Numa masmorra fora de aventura — avulsa ou de campanha — não
há aventura de onde tirar valores: o padrão é custo 0 e espera 0, isto é, sair continua
funcionando como hoje, só que individual.

**Editor de masmorras (`tools/editor.js`), painel de nível de masmorra:** checkbox
**"🚪 heróis podem sair pela escada de entrada"**, default ligado — masmorras já salvas
não mudam de comportamento. `validar_dungeon` aceita e normaliza o campo.

## Cliente

- **Escada:** clicar só age se o herói estiver em cima dela e for o turno dele. Abre
  confirmação com o custo real ("Sair custa 🍖6 💧6 e você volta em 1d4 rodadas") e
  fica desabilitada quando falta recurso ou a masmorra não permite saída.
- **Ausente, para os outros:** no HUD do grupo aparece esmaecido, com
  "🏙️ na cidade — volta em N rodadas".
- **Ausente, para ele mesmo:** a tela da cidade, com banner do contador e um botão
  **"Voltar à masmorra"** ativo quando N chega a 0.
- **Emenda encadeada:** o `renderStory` atual já roda um beat com vários slides; ele só
  recebe encerramento + abertura no mesmo beat, e o tabuleiro novo entra em seguida.

## Testes

`tools/test_masmorra_sequenciada.py` (novo, no padrão dos testes de servidor):

1. aventura de 2 etapas encadeada — encerrar a etapa 1 vai direto para a 2, `phase`
   nunca passa por `city`, e slots/recargas/HP/fome não se recuperam;
2. mesma aventura sem o flag — continua voltando à cidade (não-regressão);
3. saída recusada: fora da escada; fora do turno; sem recurso para ida+volta; masmorra
   com saída desabilitada;
4. saída válida: debita 2× o custo, o herói sai da iniciativa e deixa de ser alvo, e os
   demais seguem jogando;
5. o ausente compra na loja enquanto a sala segue em `playing`; e recebe erro ao tentar
   `world_travel`/`enter_dungeon`;
6. o contador decrementa por rodada e ele reaparece na escada quando zera;
7. objetivo concluído com um herói fora: ele recebe a parte de XP/ouro e entra na etapa
   encadeada;
8. todos saem / todos os presentes morrem havendo um vivo na cidade → sala volta à
   cidade, sem game over.

`tools/test_campanha.py` e `tools/test_persistencia_masmorra.py`, que já exercitam
`handle_exit_dungeon`, são ajustados ao novo contrato (posicionar o herói na escada e
ser o turno dele).

## Fora de escopo

- Encadeamento em **campanhas** (`mode == "campaign"`) — o flag fica só nas aventuras
  do mapa-múndi.
- Recuperação parcial configurável entre etapas (descanso curto, cura por etapa).
- Saída em grupo por decisão do anfitrião — a escada é sempre individual.
- Viagem entre cidades com o grupo dividido.
