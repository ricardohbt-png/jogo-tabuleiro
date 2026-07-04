# Guilda dos Heróis — Fase 2a: Técnicas de Recarga Curta (3 rodadas)

**Data:** 2026-07-03
**Status:** Design aprovado (conteúdo) — pronto para review do spec escrito
**Fase:** 2a — primeiro lote das **Técnicas da Guilda** (4º slot, genéricas). A Fase 1
(Especializações 1a–1f) está completa. Fase 2 decomposta por **faixa de recarga**
(3/5/8/10 rodadas); reações e passivas ficam para lotes finais.
**Depende de:** Fase 0 (infra de técnicas: `handle_usar_tecnica`, `handle_guild_equip`,
`GUILD_CATALOG` `categoria:"tecnica"`, recarga/reset na cidade, HUD do 4º slot).

---

## 1. Visão geral

Adiciona **4 técnicas genéricas** de Recarga Curta (3 rodadas) — qualquer herói pode
comprar e equipar 1 no 4º slot. A infra já existe e foi validada com **Brutalidade**
(recarga 3, +2 dano de arma). Este lote reusa o padrão e introduz alguns
`efeito.tipo` novos + seus pontos de consumo.

### Faixa (régua poder↔custo↔preço, fixada com o usuário)
| Faixa | Recarga | Custo padrão | Preço |
|---|---|---|---|
| Curta | **3 rodadas** | +2🍖 / +2💧 (Pressa: +4/+4) | **100** |

### Fatos verificados no código
- `handle_usar_tecnica` (server.py ~4143): valida turno/equipada/recarga/fome-sede,
  aplica `efeito` por `tipo`, debita custo, seta `technique_cooldowns[tid] = round_num
  + recarga_rodadas`. **NÃO consome a ação principal** → técnicas já são "buff-and-act"
  (a "ação livre" do Espírito Indomável não exige framework novo).
- Só `efeito.tipo == "buff_turno"` está implementado (Brutalidade → `tecnica_buff_dano_arma`).
- Movimento: `moves_left` (resetado para `spd` no início do turno — sites ~3305/4703/7435);
  `handle_move` (~4976) decrementa e checa `perde_turno`.
- Ataque: `handle_attack` (~5096+) tem `w_range = weapon.get("range")` (à distância se
  não-None) e a var `vantagem` (~5317). `eff_atk`/dano montados logo abaixo.
- Status do jogador: `com_medo`+`medo_rodadas` (Medo), `perde_turno` (Atordoamento/rede),
  `lentidao`/mods de magia (Lentidão). **Silêncio é POSICIONAL** (`_em_silencio(p)` checa
  se `p` está dentro de uma área de silêncio) — não é um campo do jogador.
- Buffs da canção usam `buffs_cancao` (`bonus_mov` etc.) lidos por getters dedicados —
  referência de "buff transitório por rodada".

---

## 2. As 4 técnicas (definidas com o usuário)

Todas: `categoria:"tecnica"`, `classe:None`, `exclusiva:False`, `recarga_rodadas:3`,
`preco:100`, ids prefixados `tecnica_`.

| Técnica | id | Efeito | Custo | `efeito.tipo` |
|---|---|---|---|---|
| 🎯 **Mira Perfeita** | `tecnica_mira_perfeita` | Próximo ataque **à distância** com vantagem; se acertar, +2 dano | +2/+2 | `mira_perfeita` |
| 🧘 **Espírito Indomável** *(ação livre)* | `tecnica_espirito_indomavel` | Remove imediatamente Medo, Atordoamento e Lentidão do próprio herói; concede 1 rodada de imunidade a Silêncio | +2/+2 | `remove_status` |
| 📣 **Grito de Guerra** | `tecnica_grito_guerra` | Todos os aliados vivos (incluindo o usuário) recebem **+2 de movimento** por 1 rodada | +2/+2 | `buff_aliados_mov` |
| 💨 **Pressa** | `tecnica_pressa` | O movimento do herói é **dobrado** nesta rodada | +4/+4 | `mov_self_dobrar` |

---

## 3. Mecânica por técnica (autoritativo no servidor)

Todas resolvidas dentro do dispatch de `handle_usar_tecnica` (novo ramo por `tipo`),
com o consumo/aplicação nos sites indicados.

### 3.1 Mira Perfeita (`mira_perfeita`)
- **Ativar:** `p["tecnica_mira_perfeita"] = True`.
- **Consumo (em `handle_attack`):** se o ataque for **à distância** (`w_range is not None`)
  e `p.get("tecnica_mira_perfeita")`: força `vantagem = True` e marca +2 de dano ao
  acertar; limpa a flag ao final do ataque (consome tanto em acerto quanto em erro — a
  vantagem já foi usada). Se o herói atacar corpo-a-corpo com a flag ativa, ela **não**
  é consumida (aguarda um ataque à distância) — a técnica é situacional, coerente com o
  texto "próximo ataque à distância".
- **Nota:** o +2 de dano entra no cálculo de dano já existente (novo termo condicional).

### 3.2 Espírito Indomável (`remove_status`)
- **Ativar (ação livre):** limpa do próprio jogador os status que existem e se aplicam a
  heróis: `com_medo`/`medo_rodadas`; `perde_turno`; e o estado de Lentidão do jogador
  (campo/mod correspondente — mapeado exatamente no plano). Para **Silêncio** (posicional),
  concede imunidade temporária: `p["imune_silencio_ate"] = round_num + 1`, e `_em_silencio(p)`
  passa a retornar `False` enquanto `round_num <= imune_silencio_ate`.
- **Custo/recarga** normais. Continua utilizável mesmo sob os status que remove (é o
  ponto da técnica) — a validação de turno permanece.
- **Escopo:** remove só os 4 status citados; não toca veneno/petrificação/etc.

### 3.3 Grito de Guerra (`buff_aliados_mov`)
- **Ativar:** para cada jogador vivo (incluindo o usuário), concede +2 de movimento por
  1 rodada. Implementação: bump imediato de `moves_left += 2` (ajuda quem ainda não moveu
  neste ciclo) **e** um buff transitório `mov_bonus_ate = round_num + 1` que soma +2 ao
  `spd` no reset de início de turno enquanto válido (hook no site de reset de `moves_left`).
  O buff expira sozinho (comparação com `round_num`).
- **Raio:** todo o grupo (sem limite de distância — é um "grito"), consistente com o texto
  "todos os aliados".

### 3.4 Pressa (`mov_self_dobrar`)
- **Ativar:** `p["moves_left"] = p.get("moves_left", 0) + p["spd"]` (concede um deslocamento
  inteiro extra nesta rodada — "movimento dobrado"). Custo +4/+4 (mais caro na faixa, como
  no design original).

---

## 4. Catálogo (`GUILD_CATALOG`, server.py)

4 entradas literais no estilo de `brutalidade`:

```python
"tecnica_mira_perfeita": {
    "id": "tecnica_mira_perfeita", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 100, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 3,
    "nome": "Mira Perfeita", "icon": "🎯",
    "desc": "Próximo ataque à distância recebe vantagem; se acertar, +2 de dano.",
    "efeito": {"tipo": "mira_perfeita", "bonus_dano": 2},
},
# ... espirito_indomavel (efeito {"tipo":"remove_status"}, "acao_livre": True),
#     grito_guerra ({"tipo":"buff_aliados_mov","bonus_mov":2,"duracao":1}),
#     pressa (custo 4/4; {"tipo":"mov_self_dobrar"})
```
(Os quatro seguem o mesmo shape; valores conforme a tabela da seção 2.)

> **Agrupamento por recarga na Guilda:** o cliente passa a agrupar a aba de Técnicas por
> `recarga_rodadas` (3/5/8/10) — introduzido aqui de forma que os lotes seguintes só
> acrescentem entradas. Cabeçalho por faixa; ordena por recarga asc.

---

## 5. Cliente (`game.js` + `gameState.js`)

- **Agrupamento por recarga** na aba de Técnicas da Guilda (`_renderGuild`/equivalente):
  agrupa `categoria:"tecnica"` por `recarga_rodadas`, com cabeçalho "Recarga N rodadas".
- **Mira Perfeita:** indicador visual de flag armada é opcional (o HUD do 4º slot já
  mostra a técnica e a recarga). Sem novo protocolo.
- **Alvos:** as 4 técnicas são auto-centradas (sem seleção de alvo) → o botão do 4º slot
  dispara `usar_tecnica` direto, como a Brutalidade.

---

## 6. Testes (`tools/test_tecnicas_espec.py`)

Harness do projeto. Cobrir:
1. **Catálogo:** as 4 técnicas existem com `recarga_rodadas:3`, `preco:100`, custos
   corretos (Pressa 4/4), `classe:None`.
2. **Mira Perfeita:** ativar seta a flag; um ataque à distância consome a flag, aplica
   vantagem e +2 dano; ataque corpo-a-corpo NÃO consome; recarga setada.
3. **Espírito Indomável:** com `com_medo`/`perde_turno`/lentidão setados, ativar limpa os
   três; `imune_silencio_ate` setado e `_em_silencio` retorna False sob imunidade.
4. **Grito de Guerra:** todos os aliados ganham +2 `moves_left`; buff transitório setado;
   expira após 1 rodada.
5. **Pressa:** `moves_left` aumenta em `spd`; custo 4/4 debitado; recarga setada.
6. **Comum:** recarga bloqueia reuso; fome/sede insuficientes recusam.

---

## 7. Fronteiras (NÃO neste lote)

- Faixas 5/8/10 rodadas (lotes 2b+), reações (Contra-Ataque, Ataque Coordenado,
  Oportunidade, Sangue Frio) e passivas (Último Esforço) — lotes finais.
- Exclusivas Mago/Clérigo — Fase 3.
- Não alterar o consumo de ação das técnicas (mantém "buff-and-act" atual).

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Silêncio é posicional — "remover" não mapeia a um campo | Imunidade temporária (`imune_silencio_ate`) lida em `_em_silencio`; escopo explícito. |
| Buff de movimento por "1 rodada" pode vazar entre turnos | `mov_bonus_ate = round_num + 1`, aplicado no reset e comparado a `round_num` (expira sozinho, padrão já usado em outros buffs). |
| Mira Perfeita consumir em ataque errado | Por design: a vantagem já foi gasta; a flag limpa em acerto E erro (só em ataques à distância). Teste dedicado. |
| Técnicas não consomem ação (Pressa + atacar no mesmo turno) | Comportamento pré-existente e intencional (buff-and-act); Pressa custa +4/+4 e recarga 3 para compensar. |
| Campos de status do jogador (lentidão) diferirem do esperado | O plano mapeia os campos exatos contra o código antes de implementar; escopo restrito aos 4 status. |
