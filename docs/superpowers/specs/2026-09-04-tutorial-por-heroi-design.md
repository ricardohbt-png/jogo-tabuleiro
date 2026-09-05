# Tutorial por herói — Campo de Treinamento

Data: 2026-09-04
Status: design aprovado, aguardando plano de implementação

## Problema

O jogo não ensina a si mesmo. Um jogador novo entra numa masmorra sem saber o
que a Classe de Armadura faz, para que serve a sede, por que aquele monstro
levou o dobro de dano, nem quais são as habilidades do herói que ele escolheu.
As seis classes têm kits muito diferentes — o Guerreiro arma combinações no
cliente, Pedro gasta slots de círculo, Henrique sustenta uma canção, Luccas
coloca armadilhas — e nada disso é descoberto sem tentativa e erro.

## O que estamos construindo

Uma masmorra de treinamento onde **cada herói aprende o próprio kit ao mesmo
tempo**, em alas paralelas do mesmo mapa, cobrando do jogador a ação que acabou
de ser explicada antes de deixá-lo seguir.

Decisões de forma, tomadas no brainstorming:

- **Grupo misto.** Vários jogadores entram juntos; cada um recebe as lições da
  SUA classe. Não é um tutorial solo com seis arquivos.
- **Um mapa, seis alas.** `hero_spawns` por `class_id` já existe: cada classe
  nasce na entrada da própria ala. Ala de classe ausente fica vazia.
- **Ativo.** A porta só abre depois que a ação foi feita.
- **Autoria no editor**, estendendo a ferramenta de fala de NPC que já existe.

## Arquitetura

### 1. A lição é uma `fala` com tarefa

Nenhuma estrutura nova no arquivo da masmorra. Cada entrada de `falas` ganha
três campos **opcionais**; fala sem nenhum deles se comporta exatamente como
hoje.

```json
{
  "id": "licao_guerreiro_02",
  "pos": [12, 5],
  "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
  "texto": "Todo ataque rola 1d20 + acerto contra a Classe de Armadura do alvo...",
  "trigger": { "tipo": "proximidade", "raio": 2 },

  "classe": "warrior",
  "ordem": 2,
  "tarefa": {
    "tipo": "atacar",
    "alvo": "boneco_1",
    "vezes": 1,
    "texto_curto": "Ataque o boneco de treino"
  }
}
```

| Campo | Ausente | Presente |
|---|---|---|
| `classe` | fala comum, `broadcast` para todos | só dispara para o herói daquela classe; o balão vira `send_to` |
| `ordem` | dispara assim que o gatilho bate | só dispara se todas as lições da mesma classe com `ordem` menor já foram cumpridas |
| `tarefa` | a lição só explica e se conclui ao disparar | fica pendente até o jogador cumprir |
| `efeito` | a lição não muda o estado do herói | aplica o efeito ao disparar (ver abaixo) |

O servidor já impede dois jogadores com a mesma classe na mesma sala
(`CHARACTERS_IN_USE`), então `classe` identifica exatamente um jogador.

**Progresso é por jogador, sempre.** `classe` decide apenas quem *recebe* a
lição; uma lição sem `classe` fica pendente para cada herói separadamente.

#### O campo `efeito`

Uma lição pode alterar o estado do herói que a recebeu, no momento em que ela
dispara. É o que permite **ensinar uma regra fazendo o jogador senti-la**, em vez
de descrevê-la.

```json
"efeito": { "fome": 0, "sede": 0 }
```

Vocabulário mínimo e fechado: `fome` e `sede`, valores absolutos de 0 a 100,
aplicados ao jogador. Nada mais entra sem uma nova decisão de design — em
particular, `efeito` **não** mexe em HP, nível, ouro ou inventário.

Chega junto com a sala de Provisões, na Fase 2.

### 2. O relógio: um helper, vários pontos de sucesso

```python
await self._licao_evento(p, "atacar", alvo=m)
```

Chamado no **caminho de sucesso** de cada handler relevante — nunca antes da
validação, para que uma ação recusada não conte. O helper acha a lição pendente
daquele jogador, confere verbo e alvo, incrementa o contador, e ao chegar em
`vezes` marca a lição como cumprida e destrava a próxima da trilha.

Segue o padrão já existente no arquivo (`_verificar_falas`,
`_verificar_avistamento`): um método que os handlers chamam explicitamente, em
vez de um despachante genérico.

Estado no `GameRoom`:

- `self.licoes` — derivado de `self.falas` na carga da masmorra (as que têm `tarefa`)
- `self.licoes_feitas` — `set()` de ids cumpridos, usado pelo portão de porta
- `p["licao_progresso"]` — `{licao_id: contador}` por jogador

**Vocabulário da Fase 1** (verbos e onde são chamados):

| Verbo | Ponto de chamada |
|---|---|
| `mover_ate` | `handle_move`, depois do passo confirmado |
| `abrir_porta` | `handle_open_door`, depois de destrancar |
| `atacar` | `handle_attack`, no acerto |
| `matar` | `_monster_dies`, com `killer_pid` |
| `pegar_item` | `handle_take_from_chest`, `handle_take_all_from_chest`, `handle_pickup_item` |
| `equipar` | `handle_equip_from_bag` |
| `encerrar_turno` | `handle_end_turn` |

`alvo` na tarefa é opcional: ausente = qualquer alvo serve; preenchido = o id do
monstro, do baú ou a posição que a tarefa exige.

### 3. O portão: `door_conditions` ganha um terceiro tipo

`door_conditions` já aceita `{"type":"item"}` e `{"type":"decor"}`. Acrescenta-se:

```json
{ "type": "licao", "licao_id": "licao_guerreiro_02" }
```

`_door_condition_satisfied` devolve `licao_id in self.licoes_feitas`;
`_door_condition_message` explica que falta cumprir a lição.

**Não é preciso porta por jogador.** Cada ala tem portas próprias, então a
checagem em nível de grupo já é o comportamento certo — e um companheiro que
entre na sua ala apenas ajuda. Isso evita mexer em `_is_closed_door`, que é
consultado sem contexto de jogador por movimento, linha de visão e BFS.

### 4. A tela

`game_state` ganha um bloco compartilhado:

```json
"tutorial": {
  "por_classe": {
    "warrior": { "licao_id": "licao_guerreiro_02",
                 "texto_curto": "Ataque o boneco de treino",
                 "feito": 0, "vezes": 1,
                 "concluidas": 4, "total": 11 }
  }
}
```

O `game_state` é um broadcast único; cada cliente lê a entrada da própria classe.
De quebra, dá para mostrar o progresso do colega numa etapa futura.

No HUD, um quadro discreto `#licao-atual` — `⚑ Ataque o boneco de treino` — que
some quando não há tarefa pendente. O texto explicativo continua entregue pelo
`#fala-popup` que já existe, sem UI nova.

Cliente: `GS.licaoAtual()` em `src/gameState.js` (leitura pura do estado, sem
DOM, como manda a regra de arquitetura) e o render em `game.js`.

### 5. O editor

A ferramenta **"fala NPC"** vira **"fala / lição"**. O painel da entidade ganha:

- `classe` — dropdown com as 6 classes + "todas"
- `ordem` — inteiro, só habilitado quando há classe ou tarefa
- bloco `tarefa` — tipo (dropdown do vocabulário), alvo, vezes, texto curto
- bloco `efeito` — fome e sede, cada um com "não mexer" como padrão (Fase 2)

Tudo dentro de `S.falas`, reusando criação, seleção, mover, apagar, save e load
que já existem. `door_conditions` ganha a opção "lição" no painel de porta, com
dropdown dos ids de lição do mapa.

Validação nova, no `validar_dungeon` (servidor) e no validador do editor:

- tipo de tarefa fora do vocabulário
- `ordem` duplicada dentro da mesma classe
- `classe` fora das 6 conhecidas
- porta com `licao_id` que não existe no mapa, ou que aponta para uma fala sem `tarefa`
- `alvo` inválido para o verbo: em `mover_ate` é uma casa dentro do grid; nos
  demais é o id de uma entidade que existe no mapa
- `efeito` com chave fora de `fome`/`sede`, ou valor fora de 0–100

## O conteúdo: `dungeons/campo_de_treinamento.json`

`start_mode: hero_spawns`, `saida_permitida: false`, `expected_party {1, 1}`.

**Átrio comum.** Todos nascem aqui, cada `hero_spawn` numa casa vizinha. Lições
**sem `classe`**: mover até a marca, encerrar o turno, abrir a porta, pegar o
item do baú e equipar. Comer e beber **não** ficam aqui: viraram uma sala
inteira, com consequência (sala C).

Aqui **não há portão de lição, de propósito**. Mover, abrir porta e pegar item
já se cobram sozinhos: não dá para seguir sem fazer. Um portão aqui pararia
cinco jogadores à espera do sexto.

**Seis alas**, uma por classe, cinco salas cada, ligadas por portas com
`door_conditions` do tipo `licao`:

| Sala | Ensina | Alvo |
|---|---|---|
| A — Combate | acerto contra CA, dano, crítico, o dado 3D | boneco de treino |
| B — Kit | uma lição por habilidade da classe | 3–4 bonecos |
| C — Provisões | fome, sede, os medidores e o que a barra baixa custa | comida e água no chão |
| D — Perigo | armadilha, veneno e chamas, curar status | armadilha + monstro |
| E — Prova | fraqueza × resistência: o mesmo golpe doendo diferente | monstro com `weaknesses`/`resistances` |

### Sala C — Provisões

A regra que o jogo aplica hoje, e que a sala precisa transmitir:

| Estado | Efeito |
|---|---|
| fome **> 80 e** sede **> 80** | **+1** em acerto, dano e testes de resistência (SACIADO) |
| fome **< 20** | −1 nos mesmos três |
| sede **< 20** | −1, acumulável: os dois abaixo de 20 = **−2** |
| fome **ou** sede **= 0** | **−1 HP por rodada**, até voltar acima de 0. HP 0 = morte |

Ninguém chega a essa sala esfomeado — o tutorial é curto demais. Por isso a
primeira lição da sala usa `efeito` para **zerar fome e sede**: o jogador vê a
penalidade nos próprios dados, perde 1 HP no fecho da rodada, e só então come.
Comida e água estão no chão ao lado, então o custo real é 1 ou 2 de vida — e a
lição gruda porque doeu.

Depois de comer e beber até acima de 80, a última lição da sala mostra o **+1 de
SACIADO** aparecer, fechando o arco: o mesmo medidor pune e recompensa.

O risco de morte na sala é real e **aceito**: 1 HP por rodada, com comida ao
alcance e a lição avisando na tela. Não há exceção de motor protegendo o herói.

As seis alas desembocam num salão final. Objetivo principal
`all_heroes_at_exit` — funciona igual com 1 ou 6 jogadores, enquanto exigir
"todas as alas limpas" seria impossível para quem joga sozinho.

**Monstro novo:** `boneco_treino` em `monstros_personalizados.json` — HP alto,
CA 10, `movement: 0`, sem ataques, `cr: 0`. É o que torna as salas A e B
seguras para errar.

**Recompensa: zero XP, zero ouro, zero renome.** O destino é revisitável; com
recompensa vira fazenda de recursos.

**Entrada:** um ponto na ilustração de Alva e Luz, ao lado da Guilda, vinculado
a um destino de aventura revisitável com custo 🍖/💧 zero — reusando "ponto de
cidade vinculado a masmorra", que já funciona.

## Fases

**Fase 1 — motor + fatia vertical.** Campos `classe`, `ordem` e `tarefa`;
`_licao_evento` com os sete verbos básicos; roteamento por classe; painel
`#licao-atual`; `door_conditions` do tipo `licao`; campos e validação no editor;
`tools/test_tutorial.py`. Autorado: o átrio e a **sala A do Guerreiro** — o
bastante para provar o modelo ponta a ponta antes de escrever sessenta lições.

**Fase 2 — os verbos que faltam e o campo `efeito`.** Kit (`usar_habilidade`,
`usar_magia`, `usar_tecnica`, `usar_instrumento`); sobrevivência (`usar_item`,
`comer`, `beber`) mais o `efeito` que zera fome e sede; perigo
(`desarmar_armadilha`, `sofrer_status`, `curar_status`). Autorado: as salas B a
E do Guerreiro, fechando uma ala inteira.

**Fase 3 — as outras cinco alas e a porta de entrada.** Conteúdo das cinco alas
restantes, boneco de treino, ponto na cidade e destino revisitável.

## Testes

`tools/test_tutorial.py`, no padrão das suítes existentes:

- fala sem os campos novos continua disparando por `broadcast` (retrocompatível)
- lição com `classe` chega só ao jogador daquela classe
- lição fora de ordem não dispara antes de a anterior ser cumprida
- ação recusada não conta como cumprida
- `vezes > 1` só conclui na última
- porta com `type: "licao"` fica fechada antes e abre depois
- `validar_dungeon` recusa cada caso inválido da lista de validação
- o bloco `tutorial` do `game_state` reflete o progresso
- (Fase 2) `efeito` zera fome e sede do jogador que recebeu a lição, e **só**
  dele; comer e beber devolvem os medidores e o modificador volta a +1

## Decisões registradas

- **O texto das lições fica em português.** É conteúdo autoral, e a regra do
  projeto é que conteúdo vindo do editor não passa pelo dicionário. Só os
  rótulos do painel (`⚑ Lição atual`) ganham chaves `ui.*`.
- **`ordem` é por classe, não global.** Cada ala corre no próprio ritmo; nenhum
  herói espera outro em ponto nenhum do mapa.
- **Progresso é por jogador; o portão é por grupo.** A assimetria é intencional
  e evita tocar em `_is_closed_door`.

## Fora de escopo

- Tutorial do Modo Mestre (o mestre humano tem HUD e regras próprias).
- Tradução do conteúdo das lições.
- Lista de progresso com todas as lições da ala; a Fase 1 mostra só a atual.
- Refazer o balão de fala: a lição reusa o `#fala-popup` como está.
