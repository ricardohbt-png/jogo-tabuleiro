# ND/XP de Armadilha (design)

**Data:** 2026-07-16
**Escopo:** 2ª sub-feature da Camada C do Modo Mestre — dar a cada tipo de armadilha
autorada um Nível de Desafio (`cr`) que soma à dificuldade da sala (termômetro/
minimapa) e concede XP ao grupo quando a armadilha é vencida (desarmada ou disparada-
e-sobrevivida).

## Contexto

A Camada C-a/b (ND unificado + termômetro no editor + minimapa do mestre) já está
implementada e validada. Hoje o termômetro/minimapa contam só o `cr` dos monstros por
sala; as armadilhas não têm peso de dificuldade nem dão XP (só monstros dão, via
`_calc_monster_xp`, dividido entre os heróis vivos). Esta sub-feature estende o ND
unificado às armadilhas e adiciona a elas uma recompensa de XP.

**⚠️ Sobreposição de WIP:** o catálogo `ARMADILHAS` (server.py) e o `export_catalog.py`
estão sendo editados pelo usuário em paralelo (ele adicionou `armadilha_teletransporte`
e `armadilha_dardos_envenenados`, totalizando 10 tipos). A **implementação** desta spec
mexe nesses arquivos, então deve rodar **depois** que o usuário commitar seu trabalho de
armadilhas. O helper `trap_cr` com fallback cobre qualquer tipo novo automaticamente.

### Decisões do brainstorm (confirmadas pelo usuário)

1. **Gatilho do XP:** ao **desarmar** OU ao **disparar e o alvo sobreviver** (o que vier
   primeiro concede o XP, uma única vez por armadilha).
2. **Valor do XP:** derivado do `cr` — `trap_xp(cr) = round(cr × K)` (K≈20, ajustável).
3. **Quem recebe:** dividido entre os heróis vivos (mesmo padrão de `_calc_monster_xp`).
4. **cr no termômetro:** sim — o `cr` das armadilhas de uma sala soma ao `cr` dos
   monstros, no termômetro (editor) e no minimapa (mestre).
5. **Escopo:** só armadilhas **autoradas** (`self.armadilhas` vindas de `defn`). As
   colocadas pelo Luccas em jogo (aliadas) e os buracos procedurais (`self.traps`) NÃO
   dão XP nem contam no termômetro.
6. **Sobreviver:** o alvo que disparou continua **vivo após o efeito** → concede o XP; se
   morrer, sem XP (a armadilha "venceu").

## Estado atual relevante do código (verificado)

- `ARMADILHAS` (server.py): dict de 10 tipos; campos por tipo incluem `custo_ouro`,
  `descricao`, `dificuldade`, `efeitos`, `formula_guild_id`/`formula_preco`, `icone`,
  `nome`, `persiste`, `save`. **Sem `cr` nem `xp`.**
- Armadilhas autoradas: `defn.get("traps")` → `make_authored_trap(t)` → `self.armadilhas`
  (cada uma com `tipo`, `pos`, etc.). As colocáveis do Luccas também entram em
  `self.armadilhas` mas com `aliada:True` (criador é jogador).
- XP de monstro: `_calc_monster_xp(m)` → `(xp_por_jogador, alive_count)`; aplicado com
  `p["xp"] += share_xp` para os vivos. É o padrão a reusar para a divisão.
- Desarme: `handle_desarmar_armadilha` (Luccas; teste de DES; devolve `custo_ouro` com a
  spec `ladino_desarme_3`). **Não dá XP hoje.**
- Disparo: `_disparar_armadilha` (1 alvo), `_aplicar_armadilha_area` (Mina/Gás),
  `_processar_efeitos_armadilha_turno` (tick da Incendiária) — pontos onde o efeito é
  aplicado e o `trap_result` é enviado.
- `game_state.armadilhas`: cada item já traz `tipo`/`pos`/`icone`/`nome`/etc. (falta `cr`).
- `_crPorSalaMapa` (game.js) e `_ndPorSala` (tools/editor.js): hoje somam só `cr` de
  monstros por sala. `src/difficulty.js` centraliza a matemática das faixas.
- `export_catalog.py` já exporta uma lista `traps` (o editor tem paleta de armadilhas).

## Componentes

### 1. cr por tipo + helpers (servidor — dado)

- Adicionar `cr` a cada tipo de `ARMADILHAS`. Valores iniciais (ajustáveis): `buraco` 0.1,
  `rede` 0.15, `armadilha_urso` 0.25, `fosso_estacas` 0.35, `nuvem_gas` 0.4,
  `fosso_envenenado` 0.5, `armadilha_incendiaria` 0.5, `mina_terrestre` 0.75. Os tipos
  novos do usuário recebem `cr` também (a definir na implementação; até lá, fallback).
- Helper `trap_cr(meta)` (module-level): `float(meta["cr"])` se presente, senão fallback
  (ex.: `min(1.0, max(0.1, (meta.get("dificuldade", 10) - 8) / 6))` ou um default 0.3 —
  detalhe de calibração na implementação). Fonte única da verdade.
- Helper `trap_xp(cr)` = `round(cr * TRAP_XP_POR_CR)` com `TRAP_XP_POR_CR = 20` (constante
  nomeada, ajustável).

### 2. Concessão de XP (servidor — runtime)

- Flag por armadilha: `xp_concedido` (bool). Concede uma única vez.
- Helper `_conceder_xp_armadilha(arm, alvo=None)`: se `arm` é autorada (não `aliada`) e
  ainda não concedeu, calcula `trap_xp(trap_cr(ARMADILHAS[arm["tipo"]]))`, divide entre os
  heróis vivos (mesmo cálculo de `_calc_monster_xp`: `max(1, xp // vivos)` por herói),
  soma em `p["xp"]`, marca `xp_concedido=True`, narra. (Reusar/extrair a divisão comum se
  útil.)
- **Desarme:** em `handle_desarmar_armadilha`, no ramo de sucesso, chamar
  `_conceder_xp_armadilha(arm)`.
- **Disparo-sobrevivido:** em `_disparar_armadilha` e `_aplicar_armadilha_area`, após
  aplicar o efeito, se o alvo (herói) continua vivo (`_ativo`/`hp>0`), chamar
  `_conceder_xp_armadilha(arm, alvo)`. (No AoE, basta um alvo herói vivo para conceder uma
  vez.) O tick da Incendiária não concede (o disparo inicial já cobre).
- Level-up: se `p["xp"]` cruzar o limiar, o fluxo de subida de nível existente (o mesmo
  usado pelo XP de monstro) trata — reusar, não duplicar.

### 3. cr no termômetro/minimapa (integração com a Camada C)

- **Serialização:** incluir `cr` em cada item de `game_state.armadilhas` (autoradas), lido
  de `trap_cr`. (As `aliada` podem mandar `cr:0` ou omitir — não contam.)
- **Catálogo do editor:** `export_catalog.py` passa a incluir `cr` em cada `trap` exportada
  (regenerar `editor_catalog.js`).
- **Minimapa (game.js `_crPorSalaMapa`):** além dos monstros, somar o `cr` das armadilhas
  autoradas de `state.armadilhas` cuja `pos` cai na sala (mesmo agrupamento por sala; usar
  o mesmo mapeamento posição→sala dos monstros por `room_id`, ou casar a `pos` da armadilha
  à sala que a contém — ver detalhe na implementação).
- **Termômetro (editor `_ndPorSala`):** somar o `cr` das `S.traps` (por `tipo` via
  `CAT.traps`) agrupadas por sala (posição→sala) ao total/pior-sala.

### 4. Fronteiras de módulo

- `server.py`: `cr` no catálogo + `trap_cr`/`trap_xp`/`_conceder_xp_armadilha` +
  ganchos no desarme e nos disparos + `cr` na serialização.
- `export_catalog.py` + `editor_catalog.js`: `cr` nas traps (regeneração).
- `tools/editor.js`: `_ndPorSala` inclui armadilhas.
- `game.js`: `_crPorSalaMapa` inclui armadilhas.
- Nenhuma mudança em `src/difficulty.js` (a matemática de faixa é a mesma).

## Testes

- **Servidor** (`tools/test_modo_mestre.py` ou dedicado):
  - `trap_cr` (cr explícito vs fallback) e `trap_xp` (derivação por K).
  - `_conceder_xp_armadilha`: concede uma vez (2ª chamada é no-op via `xp_concedido`);
    divide entre os vivos; ignora armadilhas `aliada`.
  - desarme concede XP; disparo com alvo vivo concede; disparo com alvo morto não concede.
- **Editor/jogo:** `node --check`; verificação manual — armadilhas somam ao cr da sala no
  termômetro (editor) e no minimapa (mestre).
- Regenerar `editor_catalog.js` com `cr` nas traps.

## Fora de escopo

- Armadilhas colocadas pelo Luccas em jogo (aliadas) e buracos procedurais (`self.traps`)
  — não dão XP nem contam no termômetro.
- Rebalancear os `cr`/K (valores iniciais ajustáveis).
- Salas obrigatórias e validador de 6 regras — specs futuras da Camada C.
- Qualquer efeito de `expected_party` em runtime.
