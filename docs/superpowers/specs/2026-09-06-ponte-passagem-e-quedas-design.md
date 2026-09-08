# Ponte como passagem e quedas só por empurrão

Data: 2026-09-06
Status: design aprovado, aguardando plano de implementação

## Problema

Dois defeitos distintos, ambos observados em jogo pelo autor.

**1. A ponte às vezes não fica azul.** O campo `altura` da ponte é um *snapshot*
gravado no momento em que ela é criada (`placeBridge`, `tools/editor.js`), e
`paintElevation` nunca o atualiza. Quem cria a ponte **antes** de pintar a
elevação dos platôs fica com `altura: 0` — a ponte deitada no fundo do vão. O
herói no platô (elevação 3) precisaria descer 3 níveis para pisar nela, o passo
é recusado, e nenhuma casa da ponte entra no alcance.

A falha é silenciosa. O validador do editor só reclama quando as duas *pontas*
divergem entre si (`ponte X liga alturas diferentes`); com as duas pontas em 3 e
a ponte em 0, ele não avisa nada.

**2. Dá para cair andando.** Hoje o movimento voluntário pode terminar em queda
em dois casos: sair pela lateral de uma ponte (`_aplicar_queda_terreno` trata
`saiu_da_ponte` como queda mesmo com desnível 1, porque a ponte não tem rampa
lateral) e, no modo `transicao_altura: "declive"`, qualquer descida de um nível.
O jogador cai por engano num clique.

### O que já funciona (medido, não suposto)

Antes de qualquer mudança, foi medido o comportamento atual com uma matriz de
geometrias (vertical/horizontal × largura 1/2/3 × vão de parede/chão baixo) e
com a masmorra real `dungeons/caverna_vulcanica.json`:

- o servidor **permite** platô → ponte → platô e **recusa** ponte → vão lateral
  quando o desnível é maior que 1;
- a névoa **revela** a ponte e o outro lado (a LOS já exclui a ponte do bloqueio
  por parede);
- `_serializar_pontes` já manda `pontes` no `game_state`, e o BFS do cliente já
  trata casa de ponte como piso;
- **as 12 geometrias atravessam.** O único caso da matriz que falhou foi a ponte
  com `altura: 0` — exatamente o defeito 1.

Ou seja: a passagem em si não precisa ser construída, precisa parar de ser
sabotada pelo campo `altura` desatualizado.

## O que estamos construindo

Três mudanças pequenas e uma bateria de testes.

Decisões tomadas no brainstorming:

- **A ponte não guarda mais a própria altura**; ela é derivada do terreno.
- Se as pontas divergirem, vale a **mais baixa**.
- **Movimento voluntário nunca causa queda.** O passo que causaria queda deixa
  de ser oferecido, em vez de ser permitido-com-dano.
- **Descer exatamente 1 nível continua permitido**, e passa a ser sempre seguro.
  Desnível de 2 ou mais segue bloqueado, como já é hoje.
  - Ressalva, para não haver duas leituras: isso vale no modo `rampa`, que é o
    padrão. Numa masmorra marcada como `declive`, descer 1 nível andando
    **deixa de ser oferecido** — lá essa descida causa queda por definição do
    modo, e a regra "movimento voluntário nunca cai" vence. O `declive` continua
    valendo para o empurrão.
- **Empurrão continua derrubando.** É a única fonte de queda por desnível.

## Arquitetura

### Peça 1 — altura da ponte derivada do terreno

Helper único no servidor:

```
_ponte_altura(ponte) = min(elev_cru(inicio), elev_cru(fim))
```

`elev_cru` lê `self.elevacoes` **diretamente**. Não pode usar
`_elevacao_terreno`: essa consulta `_ponte_alturas`, que é justamente o índice
sendo construído — daria dependência circular, e o valor lido seria o da rodada
anterior.

- `_rebuild_pontes_index` passa a derivar e **ignora** o campo salvo no JSON.
  Todas as casas da ponte recebem essa mesma altura — a superfície é plana, é o
  que o índice já faz hoje.
- `_serializar_pontes` continua emitindo `altura`, agora com o valor derivado.
  **Consequência deliberada: o cliente não muda uma linha.** `_elevacaoTerreno`
  em `src/gameState.js` já lê `ponte.altura`.
- No editor, `placeBridge` grava o derivado e `elevationAt` passa a enxergar a
  ponte, para o desenho e o clamp concordarem com o jogo.
- Masmorras já salvas com `altura` errada voltam a funcionar **ao carregar**,
  sem migração de arquivo e sem o autor precisar recriar a ponte.

O campo permanece no JSON por retrocompatibilidade — arquivos antigos continuam
válidos —, mas deixa de ser fonte de verdade em qualquer lugar.

### Peça 2 — um predicado de passo, dois usos

Novo predicado no servidor:

```
_passo_seguro(criatura, origem, destino)
  = _passo_elevacao_permitido(...)      # desnível ≤ 1 (regra atual)
  E  não causaria queda
```

"Não causaria queda" é: o destino não é mais baixo que a origem; **ou** a descida
é de exatamente 1 nível, não é saída lateral de ponte, e `transicao_altura` não é
`declive`.

Os **nove caminhos de deslocamento passo-a-passo** passam a exigir o predicado e
**deixam de chamar** `_aplicar_queda_terreno`:

| caminho | quem move |
|---|---|
| `handle_move` | herói |
| `_passo_monstro` | IA |
| `_monster_move_step` | IA |
| `_commit_monster_step` | IA **e** mestre no controle manual |
| `handle_comandar_animados` | servos do Pedro |
| `handle_mover_animado` | servo, controle manual |
| `_animado_ataca_jogador` | servo se aproximando |
| `handle_mover_prisioneiro` | prisioneiro |
| deslocamento do licantropo descontrolado | herói sem controle |

O licantropo entra nesta lista por decisão explícita: perda de controle não é
empurrão, e pela regra combinada ele não deve cair andando.

`_empurrar` fica **intocado**. Ele nunca consultou `_passo_elevacao_permitido` —
move livre e chama `_aplicar_queda_terreno` diretamente —, então apertar a regra
do passo não o enfraquece. Inclusive o caso especial em que o vão é parede
(a criatura fica na última casa da ponte e recebe o dano do desnível) continua
como está.

### Peça 3 — o cliente espelha a regra

`_walkable` em `src/gameState.js` ganha a mesma condição de segurança, usando
`transicao_altura` e `_ponteEm` — os dois já chegam no `game_state`.

Sem isso o azul ofereceria casas que o servidor recusaria, que é pior do que o
defeito original: o jogador clica e nada acontece, sem explicação.

## Fluxo de dados

```
editor  ──grava pontes[] (altura derivada, informativa)──►  dungeons/*.json
                                                                  │
                                              carga da masmorra   ▼
                                        _rebuild_pontes_index  →  _ponte_alturas
                                        (deriva de self.elevacoes, ignora o JSON)
                                                                  │
                       _elevacao_terreno(x,y) consulta _ponte_alturas primeiro
                                                                  │
                    ┌─────────────────────────────────────────────┤
                    ▼                                             ▼
        _passo_seguro (9 caminhos voluntários)        _serializar_pontes → game_state
        recusa o passo que cairia                                 │
        NÃO chama _aplicar_queda_terreno                          ▼
                                                    _elevacaoTerreno / _walkable
                                                    (mesmo predicado → mesmo azul)

        _empurrar  ──ignora o predicado──►  _aplicar_queda_terreno  (única fonte de queda)
```

## Tratamento de erro e casos de borda

- **Pontas divergentes:** vale a mais baixa. A ponta mais alta vira um degrau
  comum — de 1, transponível; de 2+, bloqueado. Nenhum caso especial novo.
- **Ponte sobre parede:** já suportado (`_ponte_em` isenta a casa em
  `_blocks_tile` e na LOS). Não muda.
- **Ponte de largura par:** `_pontes_tiles` desloca a faixa para
  `inicio[0] - largura//2`. Comportamento atual, medido e correto na matriz;
  fica como está.
- **Criatura presa no meio da ponte:** com todas as saídas laterais bloqueadas,
  só resta andar ao longo da ponte. É o comportamento desejado, não um travamento.
- **Voo:** `_voo_imune_terreno` já isenta quem voa acima do solo, tanto do custo
  de elevação quanto da queda. Não muda.
- **JSON antigo com `altura` inconsistente:** aceito e sobrescrito na carga.

## Testes

Servidor — `tools/test_ponte_passagem.py` (novo):

1. ponte carregada de um JSON com `altura: 0` sobre platôs de 3 passa a ter
   altura 3 (o defeito 1, como teste de regressão);
2. pontas divergentes (3 e 4) resolvem para 3;
3. platô → ponte → platô permitido; ponte → vão lateral recusado;
4. nenhum dos nove caminhos voluntários chama `_aplicar_queda_terreno`;
5. **`_empurrar` continua derrubando** da ponte e do platô — a prova de que o
   corte não foi longe demais;
6. modo `declive`: descer 1 andando deixa de ser oferecido, e o empurrão que
   desce 1 continua causando queda.

Cliente — `tools/test_elevacao_rampa.js` (estender):

7. a matriz de 12 geometrias (vertical/horizontal × largura 1/2/3 × vão de
   parede/chão) atravessa, e o vão ao lado da ponte nunca entra no alcance;
8. servidor e cliente concordam: para uma amostra de passos, `_passo_seguro` e
   `_walkable` dão a mesma resposta.

O item 8 é o que impede o modo de falha mais caro desta mudança — azul e regra
divergirem.

## Fora de escopo

- Ponte em rampa (altura variando ao longo do vão). Foi considerada e recusada:
  mexeria em render 3D, custo de movimento e LOS.
- Aposentar `transicao_altura`. O modo `declive` continua existindo e continua
  valendo para o empurrão; ele só deixa de derrubar quem anda.
- Corrimão, ponte destrutível, ponte que cai.
