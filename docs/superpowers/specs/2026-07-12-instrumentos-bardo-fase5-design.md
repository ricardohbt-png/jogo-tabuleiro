# Instrumentos do Bardo — Fase 5 (Improviso / Gaita)

**Data:** 2026-07-12
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** especificação (a implementar).
**Fecha:** o sistema de instrumentos (última fase do roadmap das Fases 1–5).

---

## 1. Visão geral

A **Gaita** é a 9ª e última base de instrumento. Sua habilidade, **Improviso**, é uma
**tabela meta 2d6**: a cada ativação rola 2d6 e **invoca a habilidade de assinatura de
outro instrumento** (Nota Cortante, Acorde Trovejante, Réquiem, etc.), no **tier da
qualidade da Gaita**. É uma "roleta caótica" — o bardo não escolhe o efeito, mas os
resultados altos são melhores e os baixos são fracos/arriscados. O topo da tabela (12)
é o **Encore**, uma cadeia de rerolls que, na **Gaita Rúnica**, pode escalar até o
**Grande Encore**.

A Gaita não introduz mecânica de efeito nova — ela **reusa** os dispatchers de efeito
já existentes (`_instr_nota_cortante`, `_instr_acorde_trovejante`, …). A novidade é a
**tabela de sorteio**, o **encadeamento de Encore** e um **helper central de débito de
fome/sede** que o Encore precisa para descontar o custo das ações dos aliados.

### Decisões-chave do brainstorm

| Tema | Decisão |
|---|---|
| Conceito | Roleta caótica: rola 2d6, tabela decide o efeito (baixo fraco, alto forte) |
| Tabela | "Meta": cada resultado invoca a habilidade de outro instrumento |
| Escala por qualidade | A qualidade da Gaita define o **tier** das habilidades invocadas (Velho/Rústico/Padrão). **Sem** bônus na rolagem 2d6 |
| Economia de ação | **1 mão**, custo **3🍖/3💧** (atacar E tocar no mesmo turno) |
| Mira | Servidor rola a cascata; passos sem-alvo aplicam na hora; passos com alvo (7/9/11) são enfileirados e o **jogador mira cada um** via quadro |
| Encore (12) | rola +2×; 2º 12 → Encore Menor; Rúnica recursa; 3º 12 → Grande Encore |
| Custo do Encore | Redução/isenção de fome/sede cobre **todas** as ações com custo — via helper central `_pagar_fome_sede` |

---

## 2. Base `gaita` em `INSTRUMENTOS_BASE`

```python
"gaita": {
    "nome": "Gaita", "icon": "🪗", "maos": 1, "modo": "ativada",
    "habilidade_nome": "Improviso",
    "desc": "Rola 2d6 e improvisa a habilidade de outro instrumento (no tier da "
            "Gaita). 12 = Encore: toca de novo duas vezes. Gaita Rúnica pode "
            "escalar até o Grande Encore.",
    "efeito": {"tipo": "improviso"},
    "custo_fome": 3, "custo_sede": 3,
    "afixos_validos": ["fome", "sede"],   # afixo reduz só o custo de ativação da Gaita
    "stats": {
        # A qualidade só carrega o tier; o Improviso lê `inst["qualidade"]`.
        "velho":   {},
        "rustico": {},
        "padrao":  {},
    },
    "runico": {"grande_encore": True},     # Rúnica: Encore recursivo + Grande Encore
}
```

Notas:
- `stats` por qualidade fica **vazio** de propósito — a Gaita não tem números próprios;
  o tier efetivo é `"padrao"` se `qualidade=="refinado"`, senão a própria qualidade.
  `_instrumento_stats` continua devolvendo `custo_fome`/`custo_sede` (com o desconto do
  afixo Refinado/Anão) normalmente.
- `_INSTRUMENTO_GENERO_FEM` **já** contém `"gaita"` (plumbado desde a Fase 1) — o nome
  derivado ("Gaita Velha", "Gaita Rúnica", "Gaita Lendária Élfica") já funciona.
- Origem Élfica não tem afixo aplicável à Gaita (afixos Élficos = `cd`/`alcance`/
  `duracao`, nenhum incide sobre a Gaita, cujos números vêm da base invocada) →
  `_afixo_aplicavel` rebaixa Élfica para Humana, exatamente como já acontece com o
  Alaúde. Anã (`fome_sede`) aplica (reduz o custo de ativação).

---

## 3. Improviso — resolução no servidor

### 3.1 Tabela 2d6 (tier = qualidade da Gaita)

| 2d6 | Resultado | Como é aplicado |
|---|---|---|
| 2 | **Desafinado** | Bardo sofre `-1` em Ataques e nos CDs das suas habilidades **até o início do próximo turno** (`p["desafinado_ate"] = round_num + 1`). Sem efeito nos inimigos. |
| 3 | **Falha** | Nada acontece. |
| 4 | **Ecos Dolorosos** (Sino) | Aura de retaliação por **1 rodada** (duração forçada a 1). |
| 5 | **Dueto Marcial** (Lira) | Buff por **1 rodada**. |
| 6 | **Dueto Fantasma** (Flauta) | Buff (`fracao` do tier) por **1 rodada**. |
| 7 | **Nota Cortante** (Harpa) | Alvo único (Reflexos → metade). **Precisa de alvo.** |
| 8 | **Acorde Trovejante** (Tambor) | AoE auto-centrada (raio do tier). Sem alvo. |
| 9 | **Réquiem Final** (Violino) | **Só a 1ª rodada**: Vontade vs CD → falha sofre `1 × dado` do tier. **Precisa de alvo.** Não inicia o Réquiem sustentado (sem taunt/manutenção/concentração). |
| 10 | **Sinfonia Heroica** (Alaúde) | Reforça a Canção por **1 rodada** (só vale se a Canção estiver ativa). |
| 11 | **Chamado do General** (Trompa) | Cone direcional (Vontade → medo + penalidade). **Precisa de direção.** |
| 12 | **Encore** | Ver §3.3. |

### 3.2 Reuso dos dispatchers — `st` sintetizado

Para cada resultado que invoca outra base, o Improviso constrói um **instrumento
virtual** e deriva os stats no tier da Gaita:

```python
virt = {"base": base_invocada, "qualidade": tier_gaita,
        "origem": "humana", "encantamento": "nenhum"}
st = self._instrumento_stats(virt)
```

e chama o `_instr_*` correspondente com `virt` como `inst`. Consequências desejadas:

- Os efeitos invocados usam **exatamente** os números daquele instrumento no tier da
  Gaita (a Gaita Padrão improvisa tudo no nível Padrão).
- Como `virt` tem `encantamento="nenhum"`, os **efeitos Rúnicos bespoke** das outras
  bases (Nota Cortante em linha, Acorde que atordoa, Alaúde que dá resistência) **não**
  são acionados pelo Improviso — o Rúnico da Gaita só afeta a cadeia de Encore. Isso é
  intencional.
- **CD do save** dos efeitos invocados: usa `_instrumento_cd(p, virt)` — `8 + mod(DES)`
  do bardo (o `inst` só entra na conta pelo eventual afixo de origem, que `virt` não
  tem). Idêntico ao CD de qualquer instrumento humano.

### 3.3 Encore / Grande Encore

- **12 = Encore:** rola 2d6 **mais duas vezes** e aplica os dois resultados (cada um
  pela tabela 2–12, incluindo poder cair em outro efeito).
- **2º 12** (um dos dois rerolls é 12) → **Encore Menor**: por **1 rodada**, todo
  **aliado do bardo em raio 5** (incl. o bardo) gasta **-1🍖/-1💧** nas ações; além
  disso **Mago e Clérigo** podem lançar **1 magia** sem custo de fome/sede.
- **Gaita não-Rúnica:** para no 2º 12 — o 12 do reroll rende o Encore Menor mas **não**
  rola de novo.
- **Gaita Rúnica:** "sempre que o resultado for 12, role +2×" — **recursivo**: cada 12
  na cadeia gera mais dois rerolls. Se surgir um **3º 12** na linhagem → **Grande
  Encore**: por **1d4 rodadas**, todos os personagens **sob a Canção Heroica** agem sem
  gastar fome/sede; além disso **Mago e Clérigo** lançam **magias ilimitadas** sem custo
  (respeitando ação e slots disponíveis).

**Contagem dos 12s (implementação):** o roll da cascata é totalmente resolvido no
servidor por uma função recursiva `_improviso_rolar_cascata(runico)` que devolve:
- a lista ordenada de **passos** aplicáveis (resultados 2–11, achatados na ordem de
  sorteio), e
- os **gatilhos meta**: `encore_menor: bool` (≥2 doze na cadeia) e `grande_encore: bool`
  (≥3 doze **e** Rúnica).

Guardas anti-loop: a recursão só ocorre na Rúnica; um teto de segurança (ex.
profundidade/total de rerolls) evita cascata infinita improvável mas possível.

### 3.4 Estados novos e limpeza

| Estado | Onde limpa |
|---|---|
| `p["desafinado_ate"]` | expira por comparação com `round_num` (sem reset explícito) |
| `p["encore_menor_ate"]` (por jogador afetado) | idem |
| `p["grande_encore_ate"]` (por jogador afetado) | idem |
| `p["encore_magia_gratis"]` (carga de 1 magia grátis Mago/Clérigo) | consumida no lançamento ou expira com a rodada |
| `p["sinfonia_temp_ate"]` / `p["sinfonia_temp_atributos"]` | expira por `round_num` |
| `p["improviso_pendente"]` (fila de passos com alvo) | resolvida por `improviso_alvo` ou descartada em `handle_end_turn` |

Todos seguem o padrão "expira por `round_num`" já usado no projeto (Ecos, Dueto,
`temp_def`, etc.) — sem novos ganchos de manutenção por turno.

---

## 4. Helper central de débito — `_pagar_fome_sede`

Hoje o débito de fome/sede é **espalhado** (`p["fome"] -= custo`, `max(0, …)` em ~10
handlers: magia, cura, cura_area, purificacao, ressurreicao, imposicao_maos, técnicas,
instrumentos, criar_armadilha, manutenções). **Não** há helper único.

Introduzimos:

```python
def _pagar_fome_sede(self, p, fome, sede, contexto=None):
    """Débito central de fome/sede. Aplica o desconto de Encore/Grande Encore
    e a magia grátis, depois debita (piso 0). `contexto="magia"` habilita a
    carga de magia grátis (Mago/Clérigo). Retorna (fome_paga, sede_paga)."""
    f, s = self._custo_fome_sede_efetivo(p, fome, sede, contexto)
    p["fome"] = max(0, p.get("fome", 0) - f)
    p["sede"] = max(0, p.get("sede", 0) - s)
    return f, s
```

`_custo_fome_sede_efetivo(p, fome, sede, contexto=None)`:
- **Grande Encore** ativo no jogador (`grande_encore_ate >= round_num`) → custo **0/0**.
- **Encore Menor** ativo (`encore_menor_ate >= round_num`) → **-1/-1** (piso 0).
- **Magia grátis** (Mago/Clérigo com `encore_magia_gratis` e a ação sendo uma magia) →
  custo 0/0 e consome a carga. (Sinalizado por um parâmetro `contexto="magia"` na
  chamada a partir de `handle_magia`.)

**Migração:** troco cada site de débito por `self._pagar_fome_sede(p, fome, sede)`. Os
sites de **checagem** de suficiência (`if p["fome"] < custo …`) passam a checar o custo
**efetivo** (`_custo_fome_sede_efetivo`) para não recusar uma ação que o Encore tornaria
grátis. Refactor com risco de regressão → coberto por teste dedicado (custo inalterado
quando não há Encore ativo; custo reduzido/zerado quando há).

> **Escopo consciente:** as **manutenções** por turno (Canção, Réquiem) também passam
> pelo helper, então ficam grátis sob Grande Encore — comportamento coerente com "todos
> sob a Canção agem sem custo".

---

## 5. Protocolo cliente ↔ servidor

### 5.1 Ativação

Reusa `usar_instrumento` (sem `target_id`/`dir`). `handle_usar_instrumento` despacha
`efeito.tipo == "improviso"` para o novo `_instr_improviso(p, inst, st, data)`.

Fluxo em `_instr_improviso`:
1. Rola a cascata (`_improviso_rolar_cascata`).
2. Aplica **imediatamente**, na ordem de sorteio, todos os passos **sem alvo**
   (2,3,4,5,6,8,10) e os gatilhos meta (Encore Menor / Grande Encore).
3. Enfileira os passos **com alvo** (7,9,11) em `p["improviso_pendente"]` como
   `{res, base, tier, alvo_tipo}` (`alvo_tipo` ∈ `monstro`/`direcao`).
4. Envia um evento **`improviso_resultado`** (`send_to`) com a cascata inteira para o
   **quadro** (lista de `{res, nome, precisa_alvo}`, flags de Encore/Grande Encore) e
   dá `push_state`.
5. Retorna `True` — o rodapé de `handle_usar_instrumento` debita o custo (via
   `_pagar_fome_sede`) e marca `instrumento_usado` (1 mão → `action_done` fica livre).

> **Ordem:** passos sem-alvo aplicam antes dos com-alvo (simplificação consciente da
> "roleta caótica"). Um alvo válido pode sumir (morto por um AoE anterior) → o passo
> pendente falha silenciosamente. Aceito.

### 5.2 Resolução dos alvos

Nova mensagem cliente→servidor **`improviso_alvo`** `{target_id? , dir?}` →
`handle_improviso_alvo`:
1. Valida turno + jogador + fila não vazia; tira o **primeiro** passo pendente.
2. Sintetiza `virt`/`st` (tier da Gaita) e chama o `_instr_*` correspondente com o
   alvo/direção recebido:
   - `res 7` → `_instr_nota_cortante` (`data={"target_id":…}`).
   - `res 9` → tick único do Réquiem (`_improviso_requiem_tick`).
   - `res 11` → `_instr_chamado_general` (`data={"dir":…}`).
3. `push_state`. Se a fila esvaziou, fim.

O cliente, ao receber `improviso_resultado`, mostra o quadro e, para cada pendente,
abre a mira em sequência: `res 7`/`9` → `openTargetModal` (monstro no alcance); `res 11`
→ `escolherDirecaoInstrumento` (8 direções, já existe). Cada escolha manda um
`improviso_alvo`.

**Descarte:** `handle_end_turn` limpa `p["improviso_pendente"]` (passos não mirados são
perdidos). O bardo não é obrigado a mirar.

### 5.3 Réquiem tick — `_improviso_requiem_tick(p, virt, st, m)`

Espelha o dano do 1º turno de `_processar_requiem_turno` sem o estado sustentado:
Vontade vs `_instrumento_cd(p, virt)` → falha sofre `roll_dice(st["dado"])` (contador=1);
mata via `_monster_dies`. Sem `requiem_alvo`/taunt/manutenção/concentração.

---

## 6. Integração com hooks de aura existentes

As habilidades de duração invocadas gravam os mesmos flags de sempre, **mas** seus
hooks de efeito hoje exigem o instrumento-base específico equipado (anti-cheese). Como
no Improviso o equipado é a **Gaita**, cada hook passa a aceitar `"gaita"` também:

| Hook | Mudança |
|---|---|
| `_instr_ecos_retaliar` (linha ~5336) | `off base in ("sino", "gaita")` |
| `_reacoes_instrumento_apos_ataque` — Dueto Marcial (linha ~5457) | `off base in ("lira", "gaita")` |
| `_reacoes_instrumento_apos_ataque` — Dueto Fantasma (linha ~5477) | `off base in ("flauta", "gaita")` |
| `_dueto_marcial_cap` (linha ~5444) | Gaita conta como cota 1 (Rúnica não dobra o Dueto — só a Lira Rúnica) |

**Sinfonia improvisada (res 10):** `_cancao_nivel_atributo`/`_sinfonia_bonus` hoje leem
o Alaúde equipado. Como a Gaita não é Alaúde, a Sinfonia improvisada usa um estado
temporário: `_instr_improviso` grava `p["sinfonia_temp_ate"]=round_num+1` e
`p["sinfonia_temp_atributos"]` (os atributos do Alaúde no tier da Gaita); os dois
getters somam +1 aos atributos cobertos **também** quando esse estado está ativo.

**Desafinado (res 2):** `-1` aplicado em (a) rolagem de ataque do bardo em
`handle_attack` e (b) `_instrumento_cd` (CD dos instrumentos que o bardo ativar)
enquanto `desafinado_ate >= round_num`.

---

## 7. Aquisição (loja + loot)

- **Loja (`SHOP_MERCHANT`):** SKUs de Gaita via `instrumento_sku` — velho/rústico/padrão,
  um refinado, uma Rúnica e uma Lendária (Refinada + Élfica/Anã + Rúnica) **para teste**,
  no mesmo estilo dos SKUs das Fases 4a/4b. Preços por qualidade (Velho < Rústico <
  Padrão < Refinado < Rúnica < Lendária).
- **Loot procedural:** adicionar `"gaita"` a `_ROLLER_BASES` — o roller
  (`gerar_instrumento_aleatorio`) passa a poder sortear Gaitas (incl. Rúnicas ~4%). O
  token `{"tipo":"instrumento_aleatorio"}` já resolve qualquer base.
- Roteamento bolsa-primeiro inalterado (`_route_acquired_item` já reconhece
  `tipo_item=="instrumento"`); a Gaita **não** auto-equipa.

---

## 8. Cliente (`gameState.js` + `game.js`)

- **`gameState.js`:** `GS.on("improviso_resultado", …)`; `GS.improvisoAlvo(target)` /
  `GS.improvisoDirecao(dir)` (novos senders). `instrumentoStatsClient` reconhece a base
  `gaita` (rótulo do tooltip — sem números próprios, mostra "Improviso: rola 2d6").
- **`game.js`:** o botão de instrumento do HUD (`_bardInstrumentoBtn`/`acionarInstrumento`)
  já cobre instrumentos ativados; para a Gaita ele dispara o Improviso **sem** abrir
  mira (a mira vem depois). Ao chegar `improviso_resultado`, renderiza o **quadro**
  (`renderImprovisoQuadro`): lista dos resultados sorteados (emoji + nome da habilidade),
  destaque de Encore/Encore Menor/Grande Encore, e um botão OK que inicia a fila de mira
  dos pendentes (reusa `openTargetModal` e `escolherDirecaoInstrumento`).
- Tooltip do instrumento (`_tooltipInstrumentoHTML`) descreve o Improviso e a tabela
  resumida.

---

## 9. Testes (`tools/test_instrumentos_bardo.py`)

Amplia o arquivo existente (seções novas, padrão dos `test_*`):

- **Tabela determinística:** injetando a rolagem 2d6 (monkeypatch de `roll_2d6`/random),
  cada resultado 2–11 dispara a habilidade certa no tier da Gaita (dano/alcance/duração
  corretos; duração forçada a 1 nas auras).
- **Desafinado (2):** bardo com -1 em ataque e CD enquanto ativo; expira.
- **Réquiem tick (9):** save Vontade; falha sofre 1×dado; sem `requiem_alvo` criado.
- **Encore (12):** rerolls aplicam dois efeitos; 2º 12 → Encore Menor (raio 5, -1 custo,
  1 magia grátis Mago/Clérigo); não-Rúnica não recursa.
- **Grande Encore (Rúnica, 3º 12):** cascata recursiva; 1d4 rodadas de custo 0 para quem
  está sob a Canção; Mago/Clérigo magias ilimitadas grátis; teto anti-loop respeitado.
- **`_pagar_fome_sede`:** custo inalterado sem Encore; -1 com Encore Menor; 0 com Grande
  Encore; magia grátis consome a carga; piso 0; checagem de suficiência usa o efetivo.
- **Fila de mira:** passos com alvo enfileirados; `improviso_alvo` resolve na ordem; alvo
  inválido falha sem crashar; `end_turn` descarta pendentes.
- **Hooks de aura via Gaita:** Ecos/Dueto Marcial/Dueto Fantasma improvisados retaliam/
  reagem com a Gaita equipada; Sinfonia improvisada reforça a Canção por 1 rodada.
- **Economia de ação:** 1 mão — improvisar não gasta a ação (pode atacar); custo 3/3;
  máx. 1 instrumento/turno.
- **Bard-only** e recusa sem fome/sede.

---

## 10. Fora de escopo

- Nada além da Gaita/Improviso — esta fecha o roadmap dos instrumentos.
- O helper `_pagar_fome_sede` centraliza o débito mas **não** muda os valores de custo
  de nenhuma ação existente (só passa a aplicar o desconto de Encore quando ativo).
- Sem novo modelo 3D/2D dedicado da Gaita além do emoji 🪗 (padrão dos demais).

---

## 11. Questões resolvidas

1. **Conceito do Improviso** — RESOLVIDO: roleta caótica 2d6 → tabela meta (§3.1).
2. **Escala por qualidade** — RESOLVIDO: tier das habilidades invocadas (§3.2).
3. **Mãos/custo** — RESOLVIDO: 1 mão, 3🍖/3💧 (§2).
4. **Mira** — RESOLVIDO: quadro + fila de mira por passo com alvo (§5).
5. **Encadeamento de 12s** — RESOLVIDO: 1º Encore, 2º Encore Menor, 3º (Rúnica) Grande
   Encore (§3.3).
6. **Escopo do desconto de custo** — RESOLVIDO: todas as ações com custo, via helper
   central (§4).
