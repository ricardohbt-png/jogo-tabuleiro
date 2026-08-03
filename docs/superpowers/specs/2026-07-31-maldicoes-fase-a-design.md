# Maldições Fase A — design

Data: 2026-07-31

## Problema

O sistema de maldições tem 25 entradas no catálogo `MALDICOES`, mas **só 7
têm efeito no código**. As outras 18 existem apenas como dado: o jogo narra a
maldição, mostra na ficha, abre o quadro de resultado e cobra 150–800 ouro no
Templo para removê-la — e ela não muda nada.

O agravante é o sorteio aleatório, que é o modo padrão da armadilha de maldição
e da habilidade Amaldiçoar:

| Categoria | Opções sorteáveis | Sem efeito |
|---|---|---|
| leve | 8 | 6 (**75%**) |
| média | 8 | 6 (**75%**) |
| grave | 4 | 1 (25%) |

Funcionam hoje: `maos_tremulas`, `passos_pesados`, `corpo_exausto`,
`correntes_invisiveis`, `silencio_deuses`, `voz_quebrada`, `espirito_covarde`.

## Decomposição

As 18 restantes variam muito de custo, então o trabalho foi fatiado **por
custo**, não por gravidade:

- **Fase A (este spec)** — as 6 baratas (um gancho já existente, 1–2 pontos de
  código) + a camada declarativa de modificadores + o conserto das penalidades
  de veneno.
- **Fase B** — as médias, que precisam de gancho de turno e decisão de escala:
  Sangramento Profano, Dor Constante, Fome Eterna, Sede Infinita, Tocado pela
  Morte, Maldição da Ferrugem, Eco da Morte.
- **Fase C** — as caras ou vagas (Carne Frágil, Alma Quebrada, Licantropia,
  Corrupção Crescente) e o sistema de estágios, que hoje é cosmético.

Cada fase tem seu próprio spec, plano e ciclo de implementação.

## 1. Camada declarativa de modificadores

Hoje cada maldição numérica é uma checagem hardcoded no meio de um cálculo:

```python
maldicao_atk = -2 if self._tem_maldicao(p, "maos_tremulas") else 0   # handle_attack
maldicao_mov = -3 if self._tem_maldicao(p, "correntes_invisiveis") else 0  # _moves_base
if tipo_save == "vontade" and ... self._tem_maldicao(alvo, "espirito_covarde"): bonus -= 2
```

Cada maldição numérica nova acrescenta mais uma dessas, espalhando o catálogo
pelo arquivo.

Cada entrada de `MALDICOES` passa a aceitar um campo opcional `mods`:

```python
"maos_tremulas":        {..., "mods": {"ataque": -2}},
"olhos_escuridao":      {..., "mods": {"visao": -2}},
"lamina_enferrujada":   {..., "mods": {"dano_fisico": -2}},
"correntes_invisiveis": {..., "mods": {"movimento": -3}},
"espirito_covarde":     {..., "mods": {"vontade": -2}},
"marca_cacador":        {..., "mods": {"ca": -1}},
```

com um helper único:

```python
def _maldicao_mod(self, p, chave):
    """Soma os modificadores das maldições ativas para uma chave."""
    return sum(MALDICOES[m["id"]].get("mods", {}).get(chave, 0)
               for m in self._maldicoes(p))
```

**Cinco pontos de leitura**, um por chave:

| Chave | Onde | Observação |
|---|---|---|
| `ataque` | `eff_atk` em `handle_attack` | substitui a checagem hardcoded |
| `movimento` | `_moves_base` | substitui a checagem hardcoded |
| `vontade` | `_testar_save` | substitui a checagem hardcoded; só para jogador |
| `visao` | `_get_raio_visao` | novo; já existe piso `max(1, …)` |
| `dano_fisico` | `_resolver_dano_ataque_basico` | novo; piso 1 |
| `ca` | `_player_effective_ac` | novo; ver Marca do Caçador |

`_resolver_dano_ataque_basico` é o helper compartilhado do dano de arma
(extraído na Fase 2e da Guilda), chamado tanto pelo ataque normal quanto pelo
ataque reativo — colocar a leitura ali cobre os dois de uma vez.
`_player_effective_ac` é função única consultada pelos dois sites de ataque de
monstro.

Ganho: maldição numérica futura vira **uma linha de dados**. Custo: uma
indireção — quem lê `_get_raio_visao` vê `_maldicao_mod` em vez de "maldição"
escrito ali. Mitigado por nome explícito e comentário no catálogo.

### Conserto junto: `_pen` para jogadores

`_pen(alvo, chave)` lê `alvo["penalidades"][chave]`, gravado pelo sistema de
venenos. Hoje é consultado assim:

| Chave | Monstro | Jogador |
|---|---|---|
| `ataque` | sim | sim |
| `movimento` | — | sim |
| `dano` | sim (3 sites) | **não** |
| `ca` | — | **não** |

Ou seja: um veneno que aplica penalidade de dano ou de CA num herói grava o
valor e **ninguém lê**. É bug pré-existente, exatamente nas duas funções que a
Fase A já vai editar: `_pen(p, "dano")` entra em `_resolver_dano_ataque_basico`
e `_pen(p, "ca")` em `_player_effective_ac`, ao lado das leituras novas de
`_maldicao_mod`.

Não é escopo novo — é consertar a função que já está sendo editada.

## 2. Semântica das cinco que precisavam de decisão

As descrições do catálogo admitem mais de uma leitura, então a semântica está
escrita aqui. Duas delas (Marca do Caçador, Lâmina Enferrujada) acabam caindo na
camada declarativa da seção 1; as outras três (Aura Profana, Fortuna Roubada,
Azar Sobrenatural) são comportamentais e têm gancho próprio.

Olhos da Escuridão não aparece aqui: "−2 alcance de visão" só tem uma leitura
possível e já está na tabela da seção 1.

### Marca do Caçador
"inimigos recebem +1 contra você" → **+1 no teste de ataque** dos monstros
contra o amaldiçoado. Não afeta dano.

Implementada como **−1 na CA efetiva** do amaldiçoado, não como +1 somado ao
ataque de cada monstro: para um teste de ataque as duas coisas são
matematicamente idênticas, e `_player_effective_ac` é um funil único, enquanto
o bônus de ataque do monstro é calculado em três lugares diferentes. Um gancho
em vez de três, sem chance de esquecer um.

Entra pela chave `ca` da camada declarativa (`"mods": {"ca": -1}`), o que a
torna dado como as numéricas, apesar de o catálogo descrevê-la pelo lado do
atacante.

### Aura Profana
"aliados adjacentes: -1 ataque" → os **outros** heróis vivos a Chebyshev ≤1 do
amaldiçoado levam -1 no teste de ataque. O próprio amaldiçoado não é afetado.
Um ponto só, no `eff_atk` de `handle_attack`: varre os aliados adjacentes
procurando quem carrega a maldição. Empilha com dois amaldiçoados encostados —
é raro e o catálogo não pede teto.

### Lâmina Enferrujada
"-2 dano físico" → só o dano da **arma** do herói (corpo a corpo e à distância).
Não corta dano elemental adicional, magia nem armadilha; senão vira uma
maldição genérica de dano e o nome perde o sentido. Piso de 1, como o resto do
código já faz. Implementada pela chave `dano_fisico` da camada declarativa.

### Fortuna Roubada
"recebe metade do ouro" → vale para ouro **adquirido na aventura**: baú
(`handle_take_from_chest`), container de decoração (`handle_take_from_decor`) e
recompensa de objetivo (`_conceder_objetivo_reward`).

**Não** vale para venda de item: a loja mostra um preço e receber metade dele
seria confuso, e é patrimônio próprio, não achado.

Arredonda para baixo (`//2`). Narra o que se perdeu — sem isso o jogador só vê
um número errado e pensa que é bug.

### Azar Sobrenatural
"primeiro 20 natural não crita" → o primeiro 20 natural **por masmorra** vira
acerto normal; os seguintes critam.

A escolha de escopo é de balanceamento: como quase todo herói ataca uma vez por
turno, "primeiro por rodada" equivaleria a *nunca critar* — pesado demais para
uma maldição **leve**, e mais duro que várias médias. "Uma vez e acabou" seria o
oposto: o jogador pagaria 150 ouro para remover algo que já não faz nada.

Flag por jogador (`azar_20_gasto`), zerada ao entrar na masmorra, junto dos
demais resets de `enter_dungeon`. O ponto de leitura é o mesmo `roll == 20` de
`handle_attack` que a lógica de crítico já usa.

## 3. Testes

`tools/test_maldicoes.py` (hoje 38 checks) cresce para ~70.

**O risco real não são as maldições novas — é a migração das três existentes.**
Trocar as checagens hardcoded pela camada declarativa tem que ser
comprovadamente idêntico em comportamento. Cada uma ganha um teste que fixa o
número **antes** da migração e roda igual depois:

1. ataque com e sem Mãos Trêmulas (−2 exatos)
2. movimento com e sem Correntes Invisíveis (−3 exatos)
3. Vontade com e sem Espírito Covarde (−2 exatos)

Uma seção por maldição nova:

4. visão cai 2 com Olhos da Escuridão, respeitando o piso de 1
5. dano da arma cai 2 com Lâmina Enferrujada, com piso 1; dano elemental e de
   magia **não** caem
6. a CA efetiva cai 1 com Marca do Caçador, e um ataque de monstro que erraria
   por exatamente 1 passa a acertar
7. aliado adjacente ao portador de Aura Profana ataca com −1; o próprio
   portador não
8. ouro de baú, de container e de recompensa cai pela metade com Fortuna
   Roubada; venda de item **não** cai
9. o primeiro 20 natural na masmorra não crita com Azar Sobrenatural; o segundo
   crita; entrar de novo na masmorra rearma

E uma para o conserto do `_pen`:

10. veneno com penalidade de dano num herói reduz o dano da arma dele
11. veneno com penalidade de CA num herói reduz a CA efetiva dele

Além disso, a regressão das suítes vizinhas — `handle_attack`, `_moves_base`,
`_testar_save` e `_get_raio_visao` são caminhos que quase toda suíte exercita:
`test_editor_itens`, `test_devorador`, `test_guilda`, `test_modo_mestre`,
`test_savegames`, `test_roteamento_itens`.

## Fora de escopo (deliberado)

- **Fraqueza Arcana** — "magias causam metade do dano" exige achar onde cada
  executor de magia calcula dano; são vários. Fase B ou C.
- **A segunda metade de Espírito Covarde** — "falha contra medo". A Fase A
  entrega o −2 de Vontade, que é o número que o catálogo promete.
- Tudo que é médio ou caro (ver Decomposição).
- **Sistema de estágios** — continua cosmético até a Fase C.

## Resultado esperado

6 maldições novas + 3 migradas + penalidades de veneno saindo do inerte. As
leves passam de 2/8 para 6/8 funcionando: o sorteio de maldição leve deixa de
ser 75% inócuo e passa a 25%.
