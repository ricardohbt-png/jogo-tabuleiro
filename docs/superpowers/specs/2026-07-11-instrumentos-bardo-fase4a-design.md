# Instrumentos do Bardo — Fase 4a (Origens Élfica / Anã)

**Data:** 2026-07-11
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** design aprovado no brainstorm; pendente revisão do spec.
**Depende de:** Fases 1–3 (framework de instrumentos, em master).

---

## 1. Visão geral

Fase 4a popula o **eixo Origem** (Élfica/Anã) que já está plumbado desde a Fase 1
(`criar_instrumento` aceita `origem`/`origem_bonus`; `_instrumento_stats` aplica
`origem_bonus` via `_aplicar_afixo`). Entrega:

1. O afixo composto da **Anã** (`fome_sede`: −1🍖 **e** −1💧).
2. **Pools de afixo por origem**, filtrados ao que faz sentido em cada instrumento.
3. **Nome com origem** (concordância de gênero).
4. Um **roller procedural** ponderado (`gerar_instrumento_aleatorio`).
5. Um **token de loot autoral** `{"tipo": "instrumento_aleatorio"}` que resolve num
   instrumento procedural onde um designer o colocar (loot table de monstro ou
   recompensa/baú).
6. **SKUs de origem na loja** (Élfica/Anã) — decisão do usuário: **por ora**, instrumentos
   de origem ficam compráveis na loja para facilitar o teste (ver §5.1). Conveniência de
   teste; pode ser reduzido depois para "só loot".

Encantamento Rúnico + Lendário ficam para a **Fase 4b** (slice seguinte).

### Decisões do brainstorm

| Tema | Decisão |
|---|---|
| Aquisição de origens | **Loja (para testar, por ora)** + token de loot autoral |
| Raridade do loot | **Ponderada** (qualidade e origem, ver §4) |
| Entrada no jogo | Token autoral **+** SKUs de origem na loja (teste) |

---

## 2. Afixos de origem

**Valores (da tabela do usuário):**
- **Élfica** — escolha 1: `cd` (+1 CD do save) · `alcance` (+1 quadrado) · `duracao` (+1 rodada).
- **Anã** — escolha 1: `fome_sede` (−1🍖 **e** −1💧) · `duracao` (+1 rodada) · `concentracao` (+2 em testes de concentração do Réquiem).

**`_aplicar_afixo` (server.py ~8141)** ganha o ramo composto:
```python
        elif bonus == "fome_sede":
            st["custo_fome"] -= 1
            st["custo_sede"] -= 1
```
`cd`/`alcance`/`duracao` já existem. `concentracao` **não** entra em `_aplicar_afixo`
(não altera stats) — é lido direto em `_concentracao_requiem` (`origem_bonus ==
"concentracao"` → +2), já implementado na Fase 3. Ou seja: um afixo `concentracao` só
precisa ser gravado no item; nenhum código novo de leitura.

**Aplicabilidade por instrumento** — `_afixo_aplicavel(base, bonus)`:
| Afixo | Aplica quando |
|---|---|
| `fome_sede` | sempre (todo instrumento tem custo) |
| `cd` | a base tem save (`b["efeito"].get("save")`) → harpa/tambor/trompa/violino |
| `alcance` | stats-padrão têm `alcance`/`raio`/`cone` → harpa/tambor/trompa/violino |
| `duracao` | stats-padrão têm `duracao` → sino/lira/flauta |
| `concentracao` | `efeito.tipo == "requiem_final"` → violino |

`_afixos_validos_origem(base, origem)` = pool da origem ∩ aplicáveis à base.

---

## 3. Nome com origem — `_instrumento_nome`

Acrescenta o adjetivo de origem após a qualidade, com concordância de gênero (fem se
`base in _INSTRUMENTO_GENERO_FEM`):
- Humana → **sem sufixo** (compatível com o nome atual).
- Élfica → "Élfica"/"Élfico".
- Anã → "Anã"/"Anão".

Ex.: "Harpa Refinada Élfica", "Tambor de Guerra Padrão Anão", "Alaúde Velho Anão".
(Sufixo de Rúnico/Lendário fica para a 4b.)

---

## 4. Roller procedural — `gerar_instrumento_aleatorio(bases=None)`

Função de módulo (perto de `criar_instrumento`). Passos:
1. **Base:** sorteia entre `bases` (default = as 8 implementadas:
   harpa/tambor/sino/alaude/trompa/lira/flauta/violino).
2. **Qualidade** (ponderada): Velho 35% · Rústico 30% · Padrão 25% · Refinado 10%.
3. **Origem** (ponderada): Humana 70% · Élfica 15% · Anã 15%.
   - Se a origem sorteada for Élfica/Anã mas **não houver afixo aplicável** à base
     (`_afixos_validos_origem` vazio — só ocorre com Élfica no Alaúde), **rebaixa para
     Humana** (evita "Élfica" sem bônus).
4. **Afixos pré-rolados:**
   - Refinado → `refinado_bonus` = escolha aleatória entre os afixos-base aplicáveis
     (`fome`/`sede`/`alcance`/`duracao` ∩ aplicáveis — a Fase 1 já usa `afixos_validos`
     do base; reusar/filtrar por `_afixo_aplicavel`).
   - Élfica/Anã → `origem_bonus` = escolha aleatória em `_afixos_validos_origem(base, origem)`.
5. Retorna `criar_instrumento(base, qualidade, origem, "nenhum", refinado_bonus, origem_bonus)`.

Determinismo para teste: o roller usa `random`; os testes fixam `random.seed`/monkeypatch
para asserir invariantes (origem_bonus sempre aplicável à base; nunca Élfica-Alaúde;
distribuição aproximada com muitas amostras).

---

## 5. Loot autoral — token `{"tipo": "instrumento_aleatorio"}`

O token é reconhecido nos **dois caminhos de loot** que hoje entregam itens:
- **Drop de monstro:** `_roll_monster_loot(m)` devolve o dict do loot_table; o consumidor
  em `_monster_dies` (~15545) já roteia `{"tipo":"item","id":...}`/`{"tipo":"gold",...}`.
  Acrescentar o caso `{"tipo":"instrumento_aleatorio"}` → gera via
  `gerar_instrumento_aleatorio()` e roteia como item adquirido (mesmo pipeline de baú/
  `_route_acquired_item`).
- **Hidratação de baú/recompensa:** `hidratar_itens_bau(items)` (~5666) normaliza a lista
  de itens de um baú; acrescentar o caso do token → substitui por um instrumento gerado.

**Resolução centralizada:** um helper `_resolver_loot_instrumento(entry)` que, dado um
dict de loot, retorna a instância de instrumento se `entry.get("tipo") ==
"instrumento_aleatorio"` (senão None) — chamado dos dois sites acima para não duplicar.

**Placement de referência (para não deixar a feature inerte):** adicionar o token a
**1–2 loot tables temáticas** de monstro (ex.: um chefe/ inimigo "musical"/tesouro) como
exemplo — a maior parte do placement fica a cargo dos designers (masmorras/recompensas).
Documentar o token no CLAUDE.md para autores.

### 5.1 SKUs de origem na loja (teste, por ora)

`instrumento_sku(base, qualidade, preco, refinado_bonus=None)` ganha parâmetros opcionais
`origem`/`origem_bonus` (repassados a `criar_instrumento`), e o id único passa a incluir a
origem quando não Humana (`instrumento_{base}_{qualidade}_{origem}` para não colidir com o
SKU Humano). Adicionar ao `SHOP_MERCHANT` um punhado de SKUs de origem para teste — ao
menos um Élfico e um Anão em bases variadas, com `origem_bonus` fixo (ex.: Harpa Padrão
Élfica [cd], Violino Padrão Anão [concentracao], Sino Padrão Élfico [duracao]). Preços mais
altos que os Humanos equivalentes (origens são melhores). Documentar como conveniência de
teste (removível depois).

---

## 6. Cliente

Nenhuma mudança estrutural. O nome com origem já aparece (o cliente lê `item.name`), e o
tooltip de instrumento (`_tooltipInstrumentoHTML`) mostra os stats derivados — que já
refletem os afixos de origem via `instrumentoStatsClient` (espelha `_instrumento_stats`,
que aplica `origem_bonus`). **Verificar** que o mirror cliente cobre o novo afixo
`fome_sede` e o `concentracao` (no-op nos stats) — adicionar `fome_sede` ao `afixo()` do
`instrumentoStatsClient` em `src/gameState.js`.

---

## 7. Testes (`tools/test_instrumentos_bardo.py`)

- **Afixo `fome_sede`:** reduz fome E sede em 1 (piso 0); via origem Anã num instrumento.
- **Aplicabilidade:** `_afixos_validos_origem("alaude","elfica")` vazio; `("violino","ana")`
  inclui `concentracao`; `("harpa","elfica")` inclui `cd`/`alcance` mas não `duracao`.
- **Nome:** "Harpa … Élfica" (fem), "Tambor de Guerra … Anão" (masc), Humana sem sufixo.
- **Roller:** N amostras → toda instância tem `origem_bonus` aplicável à base; nunca
  Élfica-Alaúde com bônus nulo (vira Humana); só bases implementadas.
- **Token de loot:** `_resolver_loot_instrumento({"tipo":"instrumento_aleatorio"})` devolve
  um instrumento (`tipo_item=="instrumento"`); `{"tipo":"item",...}` devolve None.
- **SKU de origem:** `instrumento_sku("harpa","padrao",preco=..., origem="elfica",
  origem_bonus="cd")` tem `origem=="elfica"`, `origem_bonus=="cd"`, id único distinto do
  Humano, e aparece em `SHOP_MERCHANT`; o nome reflete a origem.
- Regressão: `test_instrumentos_bardo`, `test_bardo_espec`, `test_roteamento_itens` verdes.

---

## 8. Fora de escopo (Fase 4b / 5)

- **4b:** Encantamento **Rúnico** — 8 efeitos bespoke (Harpa atravessa linha, Tambor
  atordoa, Sino d6, Alaúde +resistências, Trompa medo 2r, Lira 2×/rodada [plumbado],
  Flauta 5r, Violino −1 Vontade) + **Lendário** (rótulo do máximo dos 3 eixos) + Rúnico no
  roller de loot.
- **5:** Improviso/Gaita.

---

## 9. Questões resolvidas

1. Aquisição — token de loot autoral **+ SKUs de origem na loja (por ora, para teste)**. §5/§5.1.
2. Raridade — ponderada. §4.
3. Entrada no jogo — token autoral (sem chance automática em baús) + compra na loja. §5/§5.1.
4. Élfica sem afixo aplicável (Alaúde) — rebaixa para Humana. §4.
