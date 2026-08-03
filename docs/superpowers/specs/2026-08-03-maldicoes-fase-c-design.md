# Maldições Fase C — design

Data: 2026-08-03

## Onde estamos

A auditoria original encontrou 18 das 25 maldições sem efeito nenhum. As Fases
A e B, mais a Licantropia escrita pelo autor, levaram o catálogo a **18/25**.

Restam as 7 não-progressivas:

| Categoria | Inertes |
|---|---|
| leve | Fraqueza Arcana |
| média | Carne Frágil, Sangramento Profano, Dor Constante, Alma Quebrada, Maldição da Ferrugem |
| grave | Eco da Morte |

Esta fase fecha o catálogo em **25/25**.

## A exploração mudou o custo estimado

Duas maldições que as fases anteriores classificaram como caras são baratas:

**Carne Frágil** parecia exigir instrumentar os 67 pontos que reduzem HP. Mas
`_apply_damage_types` já é o funil de "ajustar o dano pelas características do
alvo", é chamado com o jogador como alvo no caminho de ataque de monstro, e a
**redução de dano da Licantropia já vive lá**. Carne Frágil é a imagem
espelhada disso.

**Fraqueza Arcana** parecia exigir tocar cada executor de magia. Mas
`handle_magia` já monta um `dmg_mult` e o plumba até todos eles — canal criado
para a Metamagia Fortalecer e para a técnica Empoderar.

Por isso a Fase C cabe num spec só; não precisa ser fatiada.

## 1. As quatro que já têm gancho

### Carne Frágil
Entra na camada declarativa da Fase A com uma chave nova: `"mods": {"dano_recebido": 2}`,
lida em `_apply_damage_types` ao lado da redução da Licantropia — mesmo lugar,
sinal oposto.

A guarda `_eh_jogador` é **obrigatória**: `_apply_damage_types` é chamado com
monstro como alvo na maioria das vezes, e o leitor de maldição
(`_maldicao_mod` → `_maldicoes`) **muta o dict que recebe**.

### Eco da Morte
Em `_player_dies`: quando um herói morre, cada aliado que carrega a maldição
sofre 10.

O dano **não pode matar** (piso de 1 HP). Não é generosidade: sem o piso, A
morre → B toma 10 e morre → C toma 10, e uma morte vira efeito dominó recursivo
dentro do próprio `_player_dies`. O piso corta a cascata na raiz, sem precisar
de guarda de reentrância.

**São 10 exatos, aplicados direto** — não passam por `_apply_damage_types`. Se
passassem, Carne Frágil os transformaria em 12 e uma resistência a necrótico os
reduziria, e o número que o catálogo promete deixaria de ser o número que
acontece. É dano da maldição, não um golpe que se possa aparar.

### Maldição da Ferrugem
Reusa `_corroer_equipamento` no gancho de fim de combate que já existe
(`_testar_licantropia_fim_combate`, escrito pelo autor para a Licantropia), que
passa a ter nome genérico e a tratar as duas maldições.

**A conferir na implementação:** a assinatura é
`_corroer_equipamento(self, m, p, armaduras_ids, armas_ids, cura, label)`, onde
`m` é o Devorador que se cura ao corroer. Sem monstro por trás, é preciso
verificar se `None` passa limpo ou se o parâmetro precisa virar opcional. Se a
função depender de `m` de forma não trivial, **parar e reportar** em vez de
duplicar a lógica de corrosão.

### Fraqueza Arcana
Multiplica por 0,5 o `dmg_mult` que `handle_magia` monta, logo após o bloco de
metamagia — o mesmo canal do Fortalecer.

**Risco pré-existente que esta maldição torna visível:** o Fortalecer já produz
multiplicadores fracionários (×1,25) e pelo menos um executor faz
`dmg = max(1, (...) * dmg_mult)` **sem** `int()`. Ou seja, dano fracionário já
é possível hoje; ×0,5 tornaria isso frequente em vez de raro. O plano inclui um
teste que afirma **dano inteiro**. Se ele pegar fração, arredondar é uma linha
no executor afetado — e a Fraqueza Arcana terá consertado um bug pré-existente,
como as penalidades de veneno na Fase A.

## 2. As três com semântica decidida

### Alma Quebrada
Zera os dois helpers que já existem e são inequivocamente "bônus que um aliado
concede": `_cancao_bonus` (Canção Heroica e a Sinfonia do alaúde) e
`_grito_mov_bonus` (Grito de Guerra). Uma linha em cada.

**Duas ficam de fora, com motivo:**

- **Guerreiro da Luz** é auto-buff do próprio paladino, não bônus de aliado.
  Bloqueá-lo puniria o Richard por carregar a maldição.
- **Abençoar** chega por `_mod_magia`, que não distingue magia lançada por um
  aliado de magia que o próprio herói lançou em si. Bloquear tudo ali derrubaria
  os buffs próprios. Separar as duas coisas é uma mudança maior do que a
  maldição justifica.

Também ficam de fora, por decisão explícita: cura de aliado e as mecânicas de
dividir dano (Protetor, Tática Defensiva). Bloquear cura transformaria uma
média na maldição mais dura do catálogo — o grupo carregaria um herói incurável
a masmorra inteira.

### Sangramento Profano
"1 dano no início do turno após sofrer dano."

Evita o problema dos 67 sites: em vez de instrumentar cada lugar que tira HP, o
herói **guarda o HP no início do seu turno** (`_hp_turno_anterior`). No turno
seguinte, se o HP atual for menor que o guardado, ele sofreu dano no intervalo —
e leva 1. Zero ganchos em sites de dano, e cai na mesma função de início de
turno que a Fase B criou para o dreno de fome/sede.

### Dor Constante
"Ações causam 1 dano" → **só a ação principal, no máximo 1 por turno.** Mover-se
e ação bônus ficam de fora: assim o jogador entende o custo e ainda pode
escolher passar o turno para não sangrar.

Cobrado em `handle_end_turn`: se `action_done` está marcado, 1 de dano na hora.

**Furo conhecido e aceito:** o turno também pode terminar por estouro de timer,
e nesse caminho o dano não cobra. Instrumentar os **22** sites que marcam
`action_done` seria a alternativa correta e imediata, mas é a maior refatoração
das três fases num campo lido em dezenas de condições — não se paga por uma
maldição média. Se o furo incomodar, fecha-se depois acrescentando o mesmo
gancho no caminho do timer.

## 3. Testes

`tools/test_maldicoes.py` (hoje 140) chega a ~170.

**Esta fase não tem migração** — nenhuma task troca código que já funciona. O
risco muda de natureza: é de alcance, não de regressão.

1. **Carne Frágil** soma 2 ao dano recebido pelo herói, e **não** afeta monstro
   (a guarda `_eh_jogador`); curar/danificar monstro não escreve campos de
   maldição nele
2. **Fraqueza Arcana** reduz o dano da magia à metade **e o dano continua
   inteiro**
3. **Eco da Morte** tira 10 de cada aliado amaldiçoado quando um herói morre;
   **não mata** (piso de 1); com dois amaldiçoados, ninguém morre em cascata
4. **Maldição da Ferrugem** degrada uma peça ao fim do combate, e só de quem
   carrega a maldição
5. **Alma Quebrada** zera Canção e Grito de Guerra, e **não** zera o Guerreiro
   da Luz de quem o ativou
6. **Sangramento Profano** tira 1 quando o HP caiu desde o turno anterior, e
   **nada** quando o HP está igual
7. **Dor Constante** tira 1 ao encerrar o turno com a ação usada, e **nada** ao
   encerrar sem usar a ação

Regressão: `_apply_damage_types`, `handle_magia`, `_player_dies`,
`handle_end_turn` e o início de turno são atravessados por quase toda suíte —
`test_editor_itens`, `test_devorador`, `test_guilda`, `test_modo_mestre`,
`test_savegames`, `test_masmorra_sequenciada`, `test_clerigo_espec`,
`test_paladino_espec`, `test_bardo_espec`, `test_ladino_espec`, `test_mago_espec`.

## Resultado esperado

Catálogo em **25/25**. A auditoria começou com 7 funcionando; termina com todas.

## Fora de escopo

- Instrumentar os 22 sites de `action_done` (ver Dor Constante).
- Distinguir magia lançada por aliado de magia própria em `_mod_magia` (ver
  Alma Quebrada).
- Bloquear cura ou divisão de dano na Alma Quebrada.
