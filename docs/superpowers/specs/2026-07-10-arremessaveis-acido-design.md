# Sub-projeto C — Arremessáveis de Ácido (dano residual + corrosão)

**Data:** 2026-07-10
**Status:** aprovado (brainstorming)

## Contexto

Terceiro sub-projeto da família de arremessáveis do mercado (ver memória
`arremessaveis-roadmap`). **A** (fogo single-target) e **B** (área com save) já
estão mergeados em `master`. Este spec cobre os dois itens de **ácido**: Frasco de
Ácido e Vidro de Ácido Grande — arremesso single-target (teste de ataque por DES)
com **dano residual** (metade na rodada seguinte) e **corrosão** da defesa do alvo.

## Infraestrutura existente reaproveitada

- **`_throw_item_alvo`** (Sub-projeto A): caminho single-target completo — mira
  vermelha, teste de ataque por DES vs CA, LOS/alcance, item consumido em acerto E
  erro, aplicação de dano via `_aplicar_dano_alvo`, e efeitos declarativos por
  campo do catálogo (ex.: `em_chamas`). O ácido pluga aqui com campos novos.
- **`_processar_em_chamas_turno`** (Sub-projeto A): tick de status por rodada,
  varrendo jogadores + monstros + prisioneiro. O tick residual do ácido é um
  método irmão no mesmo ponto de chamada.
- **Sistema de corrosão** (`_corroer_equipamento`, devorador orgânico/metal): é
  **player-cêntrico** (opera em `p["gear"]`/`p["weapon"]` com listas de material).
  **Monstros não têm equipamento corroível** neste engine — só `m["ac"]`. Por isso
  a corrosão do ácido age na **CA** do monstro (ver decisão 3).

## Decisões de design

1. **Ação principal** para os dois itens (uniforme com A/B).
2. Corrosão e residual só no **acerto**. Item consumido em acerto e erro
   (espatifa), como todos os arremessáveis.
3. **Corrosão vs monstro = redução de CA** (nenhum monstro tem equipamento
   corroível hoje). −1 CA por acerto (Frasco), −2 (Vidro Grande), cumulativo, com
   **piso de CA = 5** (evita acerto automático). Auto-reseta por masmorra (monstros
   são recriados a cada masmorra). A corrosão passa por um **helper único**
   `_acido_corroer(alvo, pontos)` cuja bifurcação já prevê o ramo de equipamento
   estilo-herói para quando/se monstros ganharem gear corroível (sub-projeto
   próprio) — **sem código morto**: só o ponto de extensão comentado.
4. **Residual** = `dano_inicial // 2` (arredonda pra baixo), **um tick único** na
   rodada seguinte.
5. Elemento `"acido"` (sem fraqueza/resistência específica hoje — dano normal).

## Componentes

### 1. Catálogo + loja (`server.py`)

- Duas entradas em `ARREMESSAVEIS` (`alvo:"ataque_alvo"`, `alcance:4`, `dano`,
  `elemento:"acido"`) com dois campos novos:
  - `residual: True`
  - `corrosao_ac: 1` (Frasco) / `2` (Vidro Grande)
- Duas entradas em `SHOP_MERCHANT` (`effect:"throwable"`), preços 20 / 50.

### 2. Efeitos no `_throw_item_alvo` (`server.py`)

No ramo de **acerto** do `_throw_item_alvo` (Sub-projeto A), após
`_aplicar_dano_alvo`, adicionar (guardado pelos campos do catálogo, mantendo o
helper genérico):

- Se `defn.get("residual")` e o alvo continua vivo: `alvo["acido_residual"] =
  max(alvo.get("acido_residual", 0), dmg // 2)` (o residual é sempre a metade do
  dano deste acerto; usa `max` para não regredir se dois frascos acertarem na mesma
  rodada). `dmg` é o dano já aplicado deste arremesso.
- Se `defn.get("corrosao_ac")` e o alvo é monstro: `await self._acido_corroer(alvo,
  defn["corrosao_ac"])`.

### 3. Helper de corrosão (`server.py`)

```
_acido_corroer(self, alvo, pontos):
    # Ponto de extensão (dormant hoje): se o alvo tiver equipamento corroível,
    # corrói o equipamento estilo-herói (_corroer_equipamento). Nenhum monstro
    # tem esse campo hoje — quando/se ganharem gear, é aqui que pluga.
    # Ramo ativo: corrói a CA do monstro.
    base = alvo.get("ac", 10)
    novo = max(_ACIDO_AC_MIN, base - pontos)   # _ACIDO_AC_MIN = 5
    if novo < base:
        alvo["ac"] = novo
        alvo["ac_corroida"] = alvo.get("ac_corroida", 0) + (base - novo)
        gm_say(...)   # "🧪 A carapaça de <alvo> corrói: CA <base>→<novo>."
```

Constante nova `_ACIDO_AC_MIN = 5`. Monstros são recriados por masmorra, então a CA
corroída some naturalmente (sem reset explícito).

### 4. Tick residual (`server.py`)

- Novo `_processar_acido_residual_turno` — espelha `_processar_em_chamas_turno`:
  varre jogadores + monstros + prisioneiro; para cada `acido_residual > 0` e vivo,
  aplica esse dano (`_dano_em_alvo`, elemento `"acido"`) e limpa `acido_residual`.
  Chamado no `handle_end_turn`, logo após `_processar_em_chamas_turno`.

### 5. Cliente (`src/gameState.js`)

- Duas entradas em `CATALOGO_ITENS` (`arremessavel:true`, `alvo:"ataque_alvo"`,
  `alcance:4`, tooltip do efeito). **Nenhuma UI nova** — reusa a mira vermelha
  single-target do Sub-projeto A.

### 6. Imagens

- `assets/itens/frasco_acido.png` / `assets/itens/vidro_acido_grande.png`
  (convenção `assets/itens/<id>.png`, fallback emoji 🧪 / 🫙).

### 7. Itens (loja/mercado)

| Item | id | Emoji | Alcance | Ataque | Dano | Residual | Corrosão | Preço |
|---|---|---|---|---|---|---|---|---|
| Frasco de Ácido | `frasco_acido` | 🧪 | 4 | DES vs CA | 1d6 ácido | metade na rodada seguinte | −1 CA (piso 5) | 20 🪙 |
| Vidro de Ácido Grande | `vidro_acido_grande` | 🫙 | 4 | DES vs CA | 2d6 ácido | metade na rodada seguinte | −2 CA (piso 5) | 50 🪙 |

### 8. Testes (`tools/test_arremessaveis_acido.py`)

- Acerto: dano de ácido aplicado; `acido_residual == dano // 2`; CA do monstro cai
  (−1 Frasco / −2 Vidro Grande).
- Tick residual: `_processar_acido_residual_turno` aplica metade e limpa
  `acido_residual`.
- Cumulativo: dois Frascos → CA cai 2 no total, respeitando o **piso 5**.
- Piso: monstro com CA baixa não desce abaixo de 5.
- Erro (CA alta / seed): item consumido, sem dano/residual/corrosão.
- Vidro Grande: dano 2d6 e −2 CA.
- Regressão: A (`test_arremessaveis.py`) e B (`test_arremessaveis_area.py`) seguem
  verdes.

## Fora de escopo (deste sub-projeto)

- Dar equipamento corroível a monstros (o ramo estilo-herói fica dormant) — feature
  própria futura.
- Cola/Rede — controle (Sub-projeto D).
- Veneno Agonia Sufocante (Sub-projeto E).
- Exibir a CA corroída no tooltip do monstro (YAGNI; pode entrar depois).
