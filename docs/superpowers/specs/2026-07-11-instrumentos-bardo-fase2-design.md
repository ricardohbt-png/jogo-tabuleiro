# Instrumentos do Bardo — Fase 2 (Trompa / Lira / Flauta)

**Data:** 2026-07-11
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** design aprovado no brainstorm; pendente revisão do spec.
**Depende de:** Fase 1 (framework de instrumentos, já em master).

---

## 1. Visão geral

Fase 2 adiciona **3 novas bases** de instrumento ao sistema da Fase 1, sem tocar no
framework (slot `off_hand`, `INSTRUMENTOS_BASE`, `_instrumento_stats`,
`handle_usar_instrumento`, economia de ação, tooltip). Cada base é uma nova entrada em
`INSTRUMENTOS_BASE` + um handler de efeito (`_instr_*`) despachado por `efeito.tipo`:

| Base | Habilidade | Mãos | Tipo de efeito | Alvo |
|---|---|---|---|---|
| `trompa` | Chamado do General | 2 | `chamado_general` | cone direcional |
| `lira` | Dueto Marcial | 1 | `dueto_marcial` | auto (buff reativo) |
| `flauta` | Dueto Fantasma | 1 | `dueto_fantasma` | auto (buff de eco) |

Mais uma peça **compartilhada**: uma penalidade de movimento real em monstros
(`mov_pen_val`/`mov_pen_ate`), lida no orçamento de movimento do monstro — usada pela
Trompa e que **fecha a lacuna** deixada na Fase 1 (o Tambor Velho, `push:0`, já grava
esses campos mas ninguém os lia).

### Decisões do brainstorm

| Tema | Decisão |
|---|---|
| Ilusão da Flauta | **Eco abstrato** — sem entidade no tabuleiro; repete o ataque do bardo com fração do dano |
| Penalidade de mov. da Trompa | **Implementar de verdade** + retro-ligar o Tambor Velho da Fase 1 |
| Cadência do Dueto Marcial | **1×/rodada** base; **2×/rodada** na versão Rúnica (plumbado; Rúnico só é gerado na Fase 4) |

---

## 2. Peça compartilhada — penalidade de movimento de monstro

**Realidade do código:** o orçamento de movimento do monstro é lido como
`m.get("movement", N)` em ~20 ramos de IA distintos — **não há um ponto único**. O
codebase já resolve isso para a **Cola** (item de gruda): reduz `m["movement"]`
diretamente, guardando o original em `m["mov_reduzido_orig"]` e a duração em
`m["mov_reduzido_rodadas"]`, com **restauração** processada 1×/turno no início do turno
do monstro (`if "mov_reduzido_orig" in m:` em `_processar_*_turno`, ~linha 9950). Vamos
**reusar esse mesmo mecanismo** — todos os ~20 ramos passam a respeitar a redução de
graça, e a expiração/restauração já existe.

**Helper `_reduzir_mov_monstro(m, val, rodadas)`** (aplicador, não leitor): guarda o
original (uma vez), aplica a **maior** redução (`m["movement"] = min(atual, orig-val)`,
**piso 1**) e a **maior** duração (`max`), reusando os campos `mov_reduzido_*` da Cola.
Nunca aumenta o movimento. A restauração fica a cargo do processador de turno já
existente.

**Retro-fix Fase 1:** o ramo `push == 0` de `_instr_acorde_trovejante` (Tambor Velho)
passa a chamar `_reduzir_mov_monstro(m, 1, 1)` em vez de gravar os campos `mov_pen_*`
(que ninguém lia) — resolvendo a lacuna documentada na Fase 1.

---

## 3. Trompa de Guerra — Chamado do General (2 mãos, `chamado_general`)

**Mira:** cone **direcional**. O cliente envia `dir:[dx,dy]` (mesma UX do Relâmpago).
O servidor usa `_cone_tiles(ox, oy, dx, dy, comp, base)` a partir da casa do bardo,
com `comp = st["cone"]` (largura = default do helper).

**Resolução:** cada monstro vivo nas casas do cone faz **Vontade** vs
`_instrumento_cd(bardo, inst)`:
- **Falha:** Amedrontado — `m["com_medo"]=True`, `m["medo_rodadas"]=st["medo"]` (reusa
  `_processar_medo`/`_fugir_monstro`) **+** `_reduzir_mov_monstro(m, st["pen_falha"], 1)`
  (só se `pen_falha>0`).
- **Sucesso:** só `_reduzir_mov_monstro(m, st["pen_sucesso"], 1)` (só se `pen_sucesso>0`).

Cada alvo recebe seu `dice_roll` de save (padrão das AoE). `custo_fome/sede` = 3/3.

**Stats por qualidade** (`afixos_validos: ["fome","sede","alcance"]`; `alcance`→+1 cone):
| Qualidade | cone | medo | pen_falha | pen_sucesso |
|---|---|---|---|---|
| velho   | 3 | 1 | 0 | 0 |
| rustico | 4 | 1 | 1 | 0 |
| padrao  | 5 | 1 | 2 | 1 |

---

## 4. Lira — Dueto Marcial (1 mão, `dueto_marcial`)

**Ativação** (`handle_usar_instrumento`, ramo `dueto_marcial`): liga o buff —
`p["dueto_marcial_ate"] = round_num + st["duracao"]`. Sem alvo. Custo 3/3.

**Reação** (hook em `handle_attack`, ao lado de `ataque_coordenado`/`_furtivo_reativo`):
quando um **aliado** `q` (jogador vivo, `q != bardo`) ataca um monstro `alvo`, se o
**bardo** (algum jogador vivo com Dueto Marcial ativo e Lira ainda equipada) satisfaz:
- `dueto_marcial_ate >= round_num`,
- bardo vivo e `gear.off_hand` é um instrumento base `lira`,
- `q` adjacente ao bardo (Chebyshev ≤1),
- `alvo` adjacente ao bardo (Chebyshev ≤1),
- cota da rodada não esgotada,

então o bardo desfere `_ataque_basico_reativo(bardo, alvo)` (o núcleo reativo da Fase
2c, que já trata acerto/dano/crítico/morte e o furtivo do Ladino quando aplicável).

**Cota por rodada:** `_dueto_marcial_cap(inst)` = **1** base, **2** se
`inst["encantamento"] == "runico"` (Fase 4). Contagem em `bardo["dueto_marcial_usos"]`
+ `bardo["dueto_marcial_usos_round"]` (reseta quando `round_num` muda). Nunca dispara
recursivamente (o ataque reativo do bardo não re-chama o hook para si mesmo — o hook só
olha ataques de aliados `!= bardo`).

**Stats** (`afixos_validos: ["fome","sede","duracao"]`):
| Qualidade | duracao |
|---|---|
| velho | 1 |
| rustico | 2 |
| padrao | 3 |

---

## 5. Flauta — Dueto Fantasma (1 mão, `dueto_fantasma`)

**Ativação** (ramo `dueto_fantasma`): liga o buff —
`p["dueto_fantasma_ate"] = round_num + st["duracao"]` e
`p["dueto_fantasma_fracao"] = st["fracao"]`. Sem alvo. Custo 3/3. Como é de 1 mão, o
bardo ainda pode atacar no mesmo turno (a ativação só marca `instrumento_usado`, não a
ação principal) — e o 1º eco já sai nesse ataque.

**Eco** (hook em `handle_attack`, no ramo do ataque do **próprio bardo**): depois que um
**ataque básico de arma** do bardo **acerta** um monstro `alvo` e aplica `dmg`, se
`dueto_fantasma_ate >= round_num` e a Flauta ainda está equipada (`gear.off_hand` base
`flauta`) e o bardo está vivo, a ilusão repete no **mesmo alvo**:
`eco = (dmg * fracao) // 100`; `alvo["hp"] -= eco`; narra como ilusão; mata via
`_monster_dies` se `hp<=0`. **Sem novo teste de acerto** (é uma cópia — "repete o
ataque"); **não recorre** (o eco não é um ataque básico, não redispara o hook); só vale
para ataques básicos de arma (não magia, não habilidade de instrumento, não o ataque
reativo do Dueto Marcial). Dispara **1 eco por ataque básico** do bardo enquanto o buff
durar (sem cota de rodada — limitado pela ação/turno do bardo).

**Stats** (`afixos_validos: ["fome","sede","duracao"]`; `fracao` em % inteiro):
| Qualidade | duracao | fracao |
|---|---|---|
| velho | 1 | 25 |
| rustico | 2 | 40 |
| padrao | 3 | 50 |

---

## 6. Despacho e cliente

**Servidor** (`handle_usar_instrumento`): 3 novos ramos por `efeito.tipo` —
`chamado_general` (lê `dir` de `data`), `dueto_marcial` (auto), `dueto_fantasma`
(auto). Todos passam pela validação comum de turno/economia de ação/custo já existente.

**`INSTRUMENTOS_BASE`:** 3 novas entradas (trompa/lira/flauta) com `nome`, `icon`,
`maos`, `modo:"ativada"`, `habilidade_nome`, `desc` (para o tooltip), `efeito`,
`custo_*`, `afixos_validos`, `stats`.

**Cliente (`game.js` `acionarInstrumento`):**
- `chamado_general` → **seletor de direção** (reusa o fluxo `dir:[dx,dy]` do Relâmpago;
  ver como Pedro mira o Relâmpago no cliente) → `GS.usarInstrumento` com a direção.
- `dueto_marcial` / `dueto_fantasma` → auto-centrados → `GS.usarInstrumento(null)`.
- O `sender` `usarInstrumento` passa a aceitar/repassar `dir` além de `target_id`
  (mensagem `usar_instrumento { target_id?, dir? }`).
- Tooltip de hover já funciona (lê `desc`/stats de `INSTRUMENTOS_BASE` via
  `instrumentoStatsClient`); os stats de cone/duração/fração aparecem no quadro.

**Loja/loot:** SKUs de trompa/lira/flauta adicionados a `SHOP_MERCHANT` via
`instrumento_sku` (preços por qualidade). Loot reusa o pipeline de item.

---

## 7. Testes (`tools/test_instrumentos_bardo.py`)

- **Penalidade de movimento:** `_mov_pen_monstro` ativa/expira; piso 1; o orçamento de
  movimento do monstro reflete a penalidade; Tambor Velho (`push:0`) agora reduz o
  movimento (fecha a lacuna).
- **Chamado do General:** monstros no cone falham → medo + pen_falha; passam →
  pen_sucesso; alcance do cone por qualidade; fora do cone intactos.
- **Dueto Marcial:** ativa buff; ataque de aliado adjacente a alvo adjacente → bardo
  revida; cap 1/rodada respeitado; reseta na virada de rodada; Rúnico (`encantamento
  =="runico"`) permite 2/rodada; não dispara se bardo sem Lira equipada / morto / fora
  de adjacência; não recorre.
- **Dueto Fantasma:** ataque básico do bardo que acerta → eco de `fracao` do dano no
  mesmo alvo; miss não ecoa; sem recursão; expira; não dispara sem Flauta equipada /
  morto; magia/habilidade não ecoam.
- **Economia de ação:** Trompa (2 mãos) = atacar OU tocar; Lira/Flauta (1 mão) = atacar
  E tocar; máx. 1 instrumento/turno.
- Regressão: `test_bardo_espec`, `test_tecnicas_espec`, `test_guilda` seguem verdes.

---

## 8. Fora de escopo (Fases 3–5)

- **Fase 3:** Réquiem Final (Violino) — DoT escalonado + quebra de concentração.
- **Fase 4:** Origens Élfica/Anã + Encantamento Rúnico (inclui o Dueto Marcial 2×/rodada
  já plumbado aqui) + rótulo Lendário + loot procedural.
- **Fase 5:** Improviso/Gaita (tabela 2d6 meta + Encore).

---

## 9. Questões resolvidas

1. **Ilusão da Flauta** — eco abstrato (sem entidade). §5.
2. **Penalidade de movimento** — implementada de verdade + retro-fix do Tambor. §2.
3. **Cadência do Dueto Marcial** — 1/rodada base, 2/rodada Rúnico (plumbado). §4.
4. **Guardas "instrumento ainda equipado + bardo vivo"** aplicadas a Lira e Flauta
   (lição do Ecos da Fase 1). §4/§5.
