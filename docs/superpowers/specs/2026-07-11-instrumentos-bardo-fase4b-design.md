# Instrumentos do Bardo — Fase 4b (Encantamento Rúnico — framework + efeitos simples)

**Data:** 2026-07-11
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** design aprovado no brainstorm; pendente revisão do spec.
**Depende de:** Fases 1–4a (framework + Origens, em master).

---

## 1. Visão geral

Fase 4b popula o **eixo Encantamento** (Rúnico) — o 3º e último eixo plumbado desde a
Fase 1 — com o **framework** (camada Rúnica em `_instrumento_stats`, nome, roller) e os
**5 efeitos Rúnicos diretos** (stat-based ou save-mod). Os 3 efeitos Rúnicos **bespoke**
(Harpa linha, Tambor atordoa, Alaúde resistências) ficam para a **Fase 4c**.

Também entrega o rótulo **Lendário** (quando os 3 eixos estão no máximo).

### Decisões do brainstorm

| Tema | Decisão |
|---|---|
| Raridade do Rúnico (roller) | **~4%** (muito raro), independente de origem/qualidade |
| Nome Lendário | **Substitui** — "Harpa Lendária Élfica" (rótulo Lendário no lugar de "Refinada … Rúnica", mantém origem) |
| Escopo 4b | framework + Sino/Flauta/Trompa (stat) + Violino (save) + Lira (já plumbado) |
| Efeitos bespoke | Harpa/Tambor/Alaúde → Fase 4c |

---

## 2. Camada Rúnica — `_instrumento_stats`

Cada base ganha um dict opcional `runico` em `INSTRUMENTOS_BASE` descrevendo a
modificação de stat. `_instrumento_stats` aplica após a camada Origem, quando
`inst["encantamento"] == "runico"`, via `_aplicar_runico(st, runico)`:

```python
def _aplicar_runico(st, runico):
    if not runico:
        return
    if "dado_set" in runico:        st["dado"]    = runico["dado_set"]
    if "duracao_delta" in runico and "duracao" in st:  st["duracao"] += runico["duracao_delta"]
    if "medo_delta"    in runico and "medo"    in st:  st["medo"]    += runico["medo_delta"]
```

**`runico` por base (4b):**
| Base | `runico` | Efeito |
|---|---|---|
| `sino` | `{"dado_set": "1d6"}` | Ecos Dolorosos passa a 1d6 (era 1d4/1d3/1) |
| `flauta` | `{"duracao_delta": 2}` | Dueto Fantasma dura +2 rodadas (3/4/5); fração 50% mantida |
| `trompa` | `{"medo_delta": 1}` | Chamado: Amedrontado 2 rodadas (medo 1→2) |

`harpa`/`tambor`/`alaude`/`violino`/`lira` **não** recebem `runico` no `_instrumento_stats`
(seus efeitos Rúnicos são lógica de handler — §3 — ou bespoke da Fase 4c).

**Cliente:** `instrumentoStatsClient` (`src/gameState.js`) espelha essa camada — lê
`inst.encantamento` e `base.runico` (a tabela `INSTRUMENTOS_BASE` já é enviada no
`game_start`) e aplica o mesmo `_aplicar_runico` em JS.

---

## 3. Efeitos Rúnicos de handler (não-stat)

- **Violino Rúnico — −1 Vontade do alvo:** em `_processar_requiem_turno`, ao rolar o save
  de Vontade do alvo, passar `extra_mod = -1` se o Violino do bardo é Rúnico
  (`off.get("encantamento") == "runico"`). O save do alvo fica mais difícil (dilacera mais).
- **Lira Rúnico — 2×/rodada:** **já plumbado** (`_dueto_marcial_cap` lê
  `inst.get("encantamento") == "runico"` → 2). A 4b só passa a **gerar** Lira Rúnica
  (roller/loja); nenhum código novo.

---

## 4. Nome — `_instrumento_nome`

Regras (concordância de gênero por `_INSTRUMENTO_GENERO_FEM`):
- **Lendário** — se `qualidade == "refinado"` **e** `origem in ("elfica","ana")` **e**
  `encantamento == "runico"` → nome = "{base} **Lendária/o** {Origem}" (ex.:
  "Harpa Lendária Élfica"). O rótulo Lendário substitui a qualidade e o sufixo Rúnico;
  a origem permanece.
- **Rúnico (não-Lendário)** — senão, monta o nome atual (base + qualidade + origem) e
  acrescenta " **Rúnica/o**" quando `encantamento == "runico"` (ex.: "Sino Padrão Rúnico",
  "Harpa Velha Rúnica").
- **Sem Rúnico** — inalterado (compat. Fase 4a).

Tabelas: `_RUNICO_LABEL = {"runico": ("Rúnico", "Rúnica")}`,
`_LENDARIO_LABEL = ("Lendário", "Lendária")`.

---

## 5. Roller — `gerar_instrumento_aleatorio`

Acrescenta o sorteio de encantamento (independente de base/qualidade/origem):
```python
    encantamento = "runico" if random.random() < 0.04 else "nenhum"
```
Passado a `criar_instrumento(..., encantamento, ...)`. Rúnico é compatível com qualquer
origem/qualidade (um Lendário sai quando calha Refinado + Élfica/Anã + Rúnico — raríssimo,
o que é o objetivo).

---

## 6. SKUs de teste na loja

Como as Origens da 4a, adicionar alguns SKUs **para teste**:
- `instrumento_sku` ganha `encantamento="nenhum"` (param opcional), repassado a
  `criar_instrumento`; o id inclui `_runico` quando Rúnico (e já inclui a origem da 4a),
  p/ não colidir.
- Adicionar ao `SHOP_MERCHANT`: alguns Rúnicos (ex.: Sino Padrão Rúnico, Flauta Padrão
  Rúnica, Trompa Padrão Rúnica, Violino Padrão Rúnico, Lira Padrão Rúnica) e **um Lendário**
  (ex.: Harpa Refinada Élfica Rúnica → "Harpa Lendária Élfica"). Preços altos.

---

## 7. Testes (`tools/test_instrumentos_bardo.py`)

- **Camada Rúnica:** Sino Rúnico `dado=="1d6"`; Flauta Rúnica `duracao == padrão+2`;
  Trompa Rúnica `medo == 2`. Instrumento sem Rúnico inalterado.
- **Violino Rúnico:** `_processar_requiem_turno` chama o save do alvo com `extra_mod == -1`
  quando Rúnico; `0` quando não.
- **Lira Rúnica:** `_dueto_marcial_cap` de uma Lira Rúnica == 2 (regressão do plumbado).
- **Nome:** "Sino Padrão Rúnico"; "Harpa Velha Rúnica"; Lendário "Harpa Lendária Élfica";
  sem Rúnico inalterado.
- **Roller:** com muitas amostras + `random.seed`, gera alguns Rúnicos (~4%); todo Rúnico é
  um instrumento válido.
- **SKU:** `instrumento_sku(..., encantamento="runico")` tem `encantamento=="runico"`, id com
  `_runico`, nome com "Rúnico/a"; SKUs na `SHOP_MERCHANT`; Lendário na loja tem nome
  "… Lendária …".
- Regressão: `test_instrumentos_bardo`, `test_bardo_espec`, `test_roteamento_itens` verdes.

---

## 8. Fora de escopo (Fase 4c / 5)

- **4c:** efeitos Rúnicos bespoke — **Harpa** (Nota Cortante atravessa uma linha reta;
  targeting direcional no cliente), **Tambor** (Acorde: falha = Atordoado/`perde_turno`;
  sucesso = −1 Ataque via `penalidades["ataque"]`), **Alaúde** (Canção também dá +1 em
  resistências vs medo/doença/veneno — via o hook de `_testar_save`/`_lenda_resist_bonus`).
- **5:** Improviso/Gaita.

---

## 9. Questões resolvidas

1. Raridade do Rúnico — ~4% no roller. §5.
2. Nome Lendário — substitui por "Lendária/o", mantém origem. §4.
3. Sino/Flauta/Trompa — stat overrides via `runico` dict. §2.
4. Violino/Lira — handler (Violino −1 Vontade; Lira já plumbado). §3.
5. Bespoke (Harpa/Tambor/Alaúde) — Fase 4c. §8.
