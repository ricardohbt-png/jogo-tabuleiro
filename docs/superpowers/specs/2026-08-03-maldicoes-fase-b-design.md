# Maldições Fase B — design

Data: 2026-08-03

## Onde estamos

Auditoria original: 18 das 25 maldições não tinham efeito nenhum no código. A
Fase A entregou 6 e a camada declarativa `mods`; o autor implementou a
Licantropia por conta própria, com um sistema de estágios de verdade.

Inventário atual (contagem por referências reais em `server.py`, não por
memória):

| Categoria | Com efeito | Inertes |
|---|---|---|
| leve | 7/8 | Fraqueza Arcana |
| média | 3/8 | Carne Frágil, Sangramento Profano, Dor Constante, Alma Quebrada, Maldição da Ferrugem |
| grave | 3/4 não-progressivas | Eco da Morte |
| progressivas | Licantropia | Fome Eterna, Sede Infinita, Tocado pela Morte, Corrupção Crescente |

**Fase B (este spec):** as 4 progressivas restantes + a camada de estágio
compartilhada. Fecha o item "estágio é cosmético" da auditoria: estágio passa a
significar algo em **todas** as progressivas, não só na Licantropia.

**Fase C (depois):** as 7 não-progressivas restantes. Aí o catálogo fecha.

## 1. Camada declarativa de estágio

A Licantropia hoje resolve seus parâmetros numa função dedicada:

```python
    def _licantropia_config(self, p):
        estagio = self._maldicao_estagio(entrada)
        return {"estagio": estagio, "chance": 4 if estagio >= 4 else estagio,
                "for": (2, 3, 4, 4, 4)[estagio - 1], ...}
```

Repetir esse formato mais quatro vezes espalharia o número do estágio pelo
arquivo. Cada progressiva passa a declarar suas rampas como tuplas de 5 no
catálogo:

```python
"fome_eterna":   {..., "progressiva": True, "estagios": {"dreno_fome": (1, 2, 2, 3, 3)}},
"sede_infinita": {..., "progressiva": True, "estagios": {"dreno_sede": (1, 2, 2, 3, 3)}},
"tocado_morte":  {..., "progressiva": True, "estagios": {"reducao_cura_pct": (20, 30, 40, 50, 60)}},
"licantropia":   {..., "progressiva": True,
                  "estagios": {"chance": (1, 2, 3, 4, 4), "for": (2, 3, 4, 4, 4),
                               "con": (2, 3, 3, 3, 3), "des": (1, 1, 2, 2, 2),
                               "reducao": (1, 2, 2, 3, 3), "regen": (1, 2, 2, 3, 3),
                               "intervalo_regen": (3, 3, 2, 2, 2)}},
```

com um helper único:

```python
    def _maldicao_estagio_cfg(self, p, maldicao_id):
        """Parâmetros da progressiva no estágio atual do herói, ou None se ele
        não a carrega. Único ponto que sabe ler o campo `estagios`."""
```

`_licantropia_config` vira uma casca fina sobre ele (ou some, se todos os
consumidores puderem chamar o genérico). O `4 if estagio >= 4 else estagio` da
chance vira a tupla `(1, 2, 3, 4, 4)` — a mesma regra, dita como dado.

Mesma filosofia do `mods` da Fase A: dado no catálogo, um leitor só.

### A migração vem primeiro e sozinha

**35 números** (7 parâmetros × 5 estágios) fixados por teste ANTES de qualquer
mudança. Se um só mudar depois, a migração quebrou e o teste acusa. É a mesma
disciplina que na Fase A impediu que três maldições funcionando fossem
quebradas em silêncio — e aqui o código migrado é recém-escrito pelo autor e
validado em jogo, então o cuidado importa mais ainda.

## 2. Fome Eterna e Sede Infinita

Drenam **por rodada**, no início do turno do herói — exatamente onde a
Licantropia já chama `_processar_regeneracao_licantropia`. A drenagem entra ao
lado, na mesma passagem: nenhum gancho novo, e o comportamento fica junto do
irmão temático.

Rampa: **1, 2, 2, 3, 3** por rodada.

A escolha do mecanismo importa: **não** é sobretaxa por ação. Corpo Exausto
(média) já faz isso via `_custo_fome_sede_efetivo`, e repetir o mecanismo com
um número maior daria duas maldições indistinguíveis em categorias diferentes.
Dreno passivo é qualitativamente outra coisa — não adianta ficar parado.

Descartado também reduzir o **teto** de fome/sede: é o mais temático, e o campo
`fome_max_modificadores` até existe em `make_player` e em `_DURABLE_FIELDS`, mas
**nunca é lido por nada**. Usá-lo significaria implementar o sistema de teto
inteiro junto — uma fase por si só.

## 3. Tocado pela Morte

Reduz a **cura de HP**, por estágio: **20, 30, 40, 50, 60%**, arredondando para
baixo, com **piso de 1** quando a cura original era ≥1. Sem o piso, uma poção
de 1 HP no estágio V curaria zero e o jogador acharia que está bugado.

Só cura de HP — não mexe em comida e bebida. Fome Eterna e Sede Infinita já
apertam esses recursos; as três doeriam no mesmo lugar e virariam a mesma
maldição com três nomes.

### O funil de cura

Não existe funil. Classificando site a site (o rascunho deste spec dizia "29",
número de um grep largo demais que contava cura de monstro e mudança de
`max_hp`), são **10 curas reais de herói**:

`_apply_skill`, `handle_cura`, `handle_cura_area`, `handle_imposicao_maos`,
`_processar_manutencao_richard` (dois: próprio e aliados),
`_processar_regeneracao_licantropia`, `_processar_buffs_magicos_turno`,
`handle_use_item` (poção) e `_processar_regeneracao_pocao_turno`.

**Três sites parecidos que NÃO podem entrar no funil:** o top-up de HP ao
equipar item de `maxhp` (`_apply_single_effect`), o top-up por CON
(`_apply_attribute_delta`) e o ganho de nível. Não são cura — são ajuste de
teto — e os dois primeiros já carregam a trava do Último Esforço.

**Ressurreição também fica de fora:** ela define o HP para um valor fixo (1,
metade ou cheio), não soma cura. Reduzi-la poderia levar o herói a menos de 1 HP
ao voltar.

Aplicar a redução só nas fontes principais deixaria buracos silenciosos — cura
por item, técnica ou magia nova continuaria em 100% e ninguém notaria.

Extrair:

```python
    def _curar_hp(self, alvo, cura, fonte=""):
        """Cura HP respeitando o teto. Ponto ÚNICO — é aqui que Tocado pela
        Morte reduz a recuperação, e onde qualquer regra futura sobre cura vai
        morar. Devolve o quanto realmente curou."""
```

e migrar os 10 sites.

Custo: refatoração em código que funciona. Mitigação: o diff é mecânico e
conferível, e cada família de cura ganha caracterização antes — poção, Cura do
clérigo, Cura em Massa, Imposição das Mãos, Regeneração Divina, regeneração de
poção.

Ganho além da maldição: hoje qualquer regra nova sobre cura precisaria ser
escrita 10 vezes, e ninguém saberia disso até esquecer uma.

## 4. Corrupção Crescente

Dispara **no avanço de estágio**, dentro do `_progredir_maldicoes_missao` que já
existe, e a geração é **garantida** — não uma rolagem.

O gatilho é o mais raro dos que consideramos (no máximo 4 disparos na vida do
personagem, a cada 2 aventuras concluídas). Uma rolagem por cima poderia fazer a
maldição nunca gerar nada; garantida, ela entrega quatro momentos memoráveis. O
custo aceito é que ela fica dormente entre os avanços.

| Avanço | Gera |
|---|---|
| → II | doença `leve` |
| → III | doença `pesada` |
| → IV | maldição aleatória **média** |
| → V | maldição aleatória **grave** |

> **Atenção às chaves de doença.** `DOENCA_SEVERIDADE` aceita `leve`, `pesada` e
> `grave` — **não existe `media`**. E `_aplicar_doenca` faz
> `DOENCA_SEVERIDADE.get(severidade, ["leve"])`: uma chave errada não levanta
> erro, ela vira `leve` em silêncio. O rascunho deste spec dizia "doença média" e
> teria produzido uma doença mais fraca do que o descrito, sem ninguém notar.
> Os testes devem afirmar os **sintomas resultantes**, não só que ficou doente.

O sorteio reusa o filtro que a armadilha de maldição e o Amaldiçoar já usam:
categoria certa e **nunca progressiva**. Isso resolve o risco de laço sem
código novo — Corrupção Crescente não pode gerar outra Corrupção Crescente nem
uma Licantropia.

O teto de 3 maldições por herói já recusa sozinho, com narração, se não houver
espaço (`_aplicar_maldicao` → "resistiu: já carrega o máximo de 3").

## 5. Testes

`tools/test_maldicoes.py` (hoje 67) chega a ~100.

**O risco são as duas migrações, não as maldições novas.**

Caracterização, antes de qualquer mudança:

1. os 35 números da Licantropia (7 parâmetros × 5 estágios)
2. uma cura por família nos 29 sites: poção, Cura do clérigo, Imposição das
   Mãos, Regeneração Divina, cura em área, ressurreição

Uma seção por maldição nova:

3. Fome Eterna drena a fome pela rampa do estágio, no início do turno; Sede
   Infinita idem para sede; nenhuma das duas mexe no recurso da outra
4. Tocado pela Morte reduz a cura pela porcentagem do estágio, arredondando
   para baixo, e **respeita o piso de 1** quando a cura original era ≥1
5. Corrupção Crescente gera doença ao avançar para II e III, e maldição ao
   avançar para IV e V — afirmando os **sintomas** da doença, não só o flag
   `doente`, para pegar a chave de severidade errada (ver a nota da seção 4)
6. Corrupção Crescente **nunca** sorteia uma progressiva
7. com o herói já em 3 maldições, a geração é recusada sem quebrar nada

Regressão: `handle_attack`, `_moves_base`, `_testar_save`, os ganchos de turno e
todas as fontes de cura são atravessados por quase toda suíte —
`test_editor_itens`, `test_devorador`, `test_guilda`, `test_modo_mestre`,
`test_savegames`, `test_masmorra_sequenciada`, `test_clerigo_espec`,
`test_paladino_espec`.

## Fora de escopo (deliberado)

As 7 não-progressivas restantes viram a **Fase C**: Fraqueza Arcana, Carne
Frágil, Sangramento Profano, Dor Constante, Alma Quebrada, Maldição da
Ferrugem, Eco da Morte.

Carne Frágil (+2 dano recebido) é a mais cara delas: 67 pontos reduzem HP no
arquivo, sem funil único. Se a extração do `_curar_hp` correr bem nesta fase,
ela vira o argumento para fazer o mesmo com dano.

## Resultado esperado

As 4 progressivas restantes saem do inerte e o estágio deixa de ser cosmético
em todo o sistema. O catálogo vai de 14/25 para **18/25** com efeito, e as
graves ficam completas menos Eco da Morte.
