# Perseguição dos monstros — todo dano alerta e rastro por Percepção — design

**Data:** 2026-09-26
**Status:** aprovado em brainstorming

## Contexto — o que já existe

A IA já tem memória de perseguição, vinda do commit `a0c3835` ("memoria de monstro"):

- `_monster_remember_visible_targets(m, targets)`: quando o monstro vê um herói, grava
  `ai_last_seen = {target_id, pos, round, room_id}` nele e em todos os monstros vivos da mesma
  sala de origem (`room_id` é a sala onde o monstro nasceu, fixa).
- `_monster_register_attack_alert(attacker, target)`: faz o mesmo com a posição de quem atacou
  (`reason: "attack"`), chamado hoje só em 4 pontos: `handle_attack`,
  `handle_comandar_animados`, `handle_atacar_animado` e `_elemental_raio_atacar`.
- `_monster_search_last_seen(m)`: no turno sem alvo visível (`gm_phase`), anda até a última
  posição conhecida; conta `searches` e esquece depois de 3 turnos. Há também um teto de
  segurança de 3 rodadas desde a observação (`_monster_last_seen_goal`).

Um experimento sem navegador confirmou: ver o herói e perdê-lo atrás de uma parede leva o
monstro até o último ponto visto, onde ele procura por 3 rodadas; ser atacado de longe o leva
até a origem do ataque.

## Lacunas corrigidas

1. **Só o ataque básico alerta.** Magia, item arremessado, instrumento do bardo e técnica da
   Guilda causam dano sem gravar de onde veio.
2. **Ao chegar à última posição, o monstro para.** Não tenta seguir para onde o herói foi.

O compartilhamento do alerta com a sala inteira continua como está (decisão do autor).

## 1. Todo dano alerta — gancho na ação do herói

No laço de mensagens (`handler`), toda mensagem de um herói numa sala em masmorra
(`room.phase == "playing"`, `pid in room.players`) passa por:

```
hp_antes = room._hp_monstros()              # {id: hp} dos monstros vivos
... despacha a mensagem como hoje ...
await room._alertar_monstros_feridos(pid, hp_antes)
```

`_alertar_monstros_feridos(pid, hp_antes)`: para cada monstro que existia e tinha HP > 0 em
`hp_antes` e cujo HP atual é menor, chama `_monster_register_attack_alert(herói, monstro)`.
Isso cobre magia, arremesso, instrumento, técnica, ataque básico e fontes futuras, sem gancho
por executor. Monstro morto na ação é ignorado (`_monster_register_attack_alert` já recusa
alvo com HP ≤ 0).

- As 4 chamadas atuais continuam: repetem a mesma memória (idempotente), e as de servos gravam
  a posição do SERVO, que é quem atacou.
- Dano contínuo (veneno, chamas, zonas, armadilhas) não passa por uma ação do herói e não
  alerta.
- Herói ausente (`fora_masmorra`) ou sem posição: nada é gravado (a função já recusa atacante
  sem `pos`).

## 2. Seguir a pista — teste de Percepção

Em `_monster_search_last_seen`, quando o monstro **está na última posição conhecida** e não vê
nenhum alvo (é o único caminho que chama a função), antes de encerrar o turno ele faz um teste
de rastro, `_monster_tentar_rastro(m)`:

- **Herói rastreável:** o `target_id` da memória aponta para um jogador vivo (`alive`), dentro
  da masmorra (`_ativo`) e com `pos`. **Não** é rastreável se estiver invisível
  (`invisivel_sombras`, `invisivel_magico`, `oculto_vela`), a menos que o monstro tenha
  `faro_implacavel_minotauro`. Sem herói rastreável, não há teste.
- **Um teste por chegada:** a memória guarda `rastro_testado_em = [x, y]`. O teste só acontece
  se a posição atual do monstro for diferente da última onde ele testou. Ficar parado no mesmo
  ponto nas rodadas seguintes não gera testes novos.
- **Teste:** `d20 + (distância ÷ 2) ≤ Percepção`. A distância é Chebyshev entre o monstro e a
  posição ATUAL do herói, dividida por 2 com arredondamento para baixo. A Percepção é a da
  ficha, via `_get_percepcao_monstro(m)`. Exemplo: Percepção 12, herói a 6 casas → precisa
  tirar 9 ou menos.
- **Sucesso:** `ai_last_seen["pos"]` passa a ser a posição atual do herói. O `round` e o
  contador `searches` **não** mudam: o prazo de 3 rodadas continua correndo. O monstro segue
  andando para o novo ponto no mesmo turno, se ainda tiver movimento. Narração:
  "🐾 {monstro} encontra o rastro de {herói}!".
- **Falha:** nada muda; o monstro continua procurando ali. Sem narração, para não poluir o log.
- Cada monstro testa por si ao chegar. A pista nova vale só para o monstro que passou: não é
  propagada à sala.

O d20 do teste usa `random.randint(1, 20)`, para os testes poderem fixá-lo.

## 3. Modo Mestre

A busca e o rastro rodam só no caminho da IA (`gm_phase`). Monstro em Manual continua sendo do
mestre. Sem mestre, o jogo segue como hoje, com os dois acréscimos.

## 4. i18n

Uma chave nova em `src/lang/narracao.js`: `narracao.encontra_o_rastro`
(pt: "🐾 {monstro} encontra o rastro de {heroi}!", en: "🐾 {monstro} picks up {heroi}'s
trail!"). O nome do monstro usa `nome_criatura(m)` e o do herói vai cru (nome de jogador).

## 5. Testes — `tools/test_perseguicao.py` (novo)

Cena montada sem navegador: sala com uma parede e uma passagem, um orc e um herói.

- magia (dano por `_dano_em_alvo` dentro de uma ação) e arremesso passam a gravar
  `ai_last_seen` com a posição do herói; dano de veneno fora de ação não grava;
- `_alertar_monstros_feridos` ignora monstro que não perdeu HP e monstro morto;
- rastro com d20 fixado em sucesso: a memória passa à posição atual do herói, o `round` e o
  `searches` não mudam, e o monstro anda para lá;
- rastro com d20 fixado em falha: memória intacta, monstro parado;
- um teste só por chegada ao mesmo ponto;
- herói invisível não deixa rastro; com `faro_implacavel_minotauro` deixa;
- prazo de 3 rodadas: sem ver o herói, a memória some mesmo com rastros bem-sucedidos;
- ver o herói de novo zera a busca;
- não-regressão: `test_modo_mestre`, `test_simulador_turno`, `test_agarrao`, `test_devorador`
  continuam verdes.

## Fora de escopo

- Propagar a pista nova à sala.
- Rastro de servos animados ou do prisioneiro (só heróis).
- Mostrar o d20 do teste ao jogador.
