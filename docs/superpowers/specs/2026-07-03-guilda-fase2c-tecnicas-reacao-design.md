# Guilda dos Heróis — Fase 2c: Técnicas de Reação

**Data:** 2026-07-03
**Status:** Design aprovado (conteúdo) — pronto para review do spec escrito
**Fase:** 2c — 3º lote das **Técnicas da Guilda**. Segue 2a (Curta) e 2b (Média).
Foca em **reações** (efeitos que disparam sozinhos em eventos, fora do próprio turno).
**Depende de:** Fase 2a/2b (infra `handle_usar_tecnica` + dispatch por `efeito.tipo`)
e do padrão de reação já existente: **Furtivo Supremo** (`_furtivo_reativo`, server.py
~5397) — reação auto-disparada dentro de um gancho, aplicando dano direto (sem
re-invocar `handle_attack`, evitando recursão).

---

## 1. Visão geral

4 técnicas de reação genéricas. Reações **auto-disparam** (sem prompt): a técnica é
comprada/equipada e, quando o gatilho ocorre, o efeito acontece automaticamente.
Duas delas fazem um **ataque básico reativo** (helper compartilhado). Faixa de
recarga define o preço (a Guilda já agrupa por recarga).

**Fora deste lote:** Oportunidade (manipula ordem de turno — mini-lote próprio).

### Fundação: `_ataque_basico_reativo(self, atacante, alvo)`
Ataque básico disparado fora do turno (não chama `handle_attack` → sem recursão):
- Rola d20 + `atacante["atk_bonus"]` vs CA do `alvo` (monstro: `alvo["ac"]`).
- No acerto: dano = `roll_dice(weapon["die"]) + mod(stat)` da arma do atacante
  (arma sem dado → 1). **Acoplamento com o Ladino:** se `atacante["class_id"]=="rogue"`
  e `_verificar_ataque_furtivo(atacante, alvo)` (regras da classe), soma os dados de
  Furtivo (`_dados_furtivo(level)` → Nd4). Aplica no `alvo["hp"]`; se `hp<=0`, chama
  `_monster_dies`. Broadcast do d20/dano + `gm_say`.
- Não dispara outras reações (aplica dano direto), espelhando `_furtivo_reativo`.

---

## 2. As 4 reações

| Técnica | id | Faixa/Preço | Custo | Gatilho / Efeito | `efeito.tipo` |
|---|---|---|---|---|---|
| 🤝 **Ataque Coordenado** | `tecnica_ataque_coordenado` | 5r / 180 | +4/+4 | Alvo = aliado. Neste turno, ao você atacar um inimigo, o aliado par faz um ataque básico reativo no mesmo alvo (1×/turno). | `ataque_coordenado` |
| 🧊 **Sangue Frio** | `tecnica_sangue_frio` | 5r / 180 | +2/+2 | Arma-se; no seu **1º erro** de ataque, re-rola aquele ataque (1×, depois recarga). | `sangue_frio` |
| 🛡️ **Resistência Absoluta** | `tecnica_resistencia_absoluta` | 5r / 180 | +4/+4 | +2 em **todos os saves** por 2 rodadas. | `buff_saves` |
| 🗡️ **Contra-Ataque** | `tecnica_contra_ataque` | 8r / 280 | +6/+6 | Até o próximo turno: sempre que um monstro **errar** você (e ele estiver no alcance da sua arma elegível), você faz um ataque básico reativo nele. | `contra_ataque` |

> Custos e recargas vêm do design original: Sangue Frio +2/+2, os demais +4/+4 (5r) e
> Contra-Ataque +6/+6 (8r).

---

## 3. Mecânica por técnica (autoritativo no servidor)

### 3.1 Ataque Coordenado (`ataque_coordenado`)
- **Ativar (exige `target_id` de aliado vivo):** grava no usuário
  `p["coordenado_alvo"] = ally_id` e `p["coordenado_turno"] = self.turn_index` (vale
  só o turno atual). Sem alcance obrigatório (o par pode estar em qualquer lugar; o
  ataque reativo dele é que precisa alcançar o alvo).
- **Gatilho (hook em `handle_attack`, após o ataque resolver, como o `_furtivo_reativo`):**
  se o atacante tem `coordenado_alvo` armado no `turn_index` atual, o aliado par
  (`self.players[coordenado_alvo]`, vivo) faz `_ataque_basico_reativo(par, target)` no
  mesmo inimigo — **desde que** o par esteja no alcance da própria arma
  (`_alvo_no_alcance_arma(par, target)`); senão, apenas não dispara. Consome
  (`coordenado_alvo=None`) após a 1ª tentativa neste turno.
- Limpo no reset de fim de turno.

### 3.2 Sangue Frio (`sangue_frio`)
- **Ativar:** `p["sangue_frio_armado"] = True`.
- **Gatilho (em `handle_attack`):** quando o ataque do jogador **erra** (`not hit`) e
  `sangue_frio_armado`, re-rola UMA vez o mesmo ataque (novo `_rolar_ataque` com os
  mesmos `eff_atk`/`eff_target_ac`/vantagem/desvantagem); usa o novo resultado. Consome
  `sangue_frio_armado=False` e entra em **recarga** (a técnica só entra em recarga ao
  disparar — `handle_usar_tecnica` seta a recarga ao ativar, então o "armado" é o estado
  entre ativar e disparar; a recarga já corre a partir da ativação). Zera na cidade.
- **Nota de escopo:** aplica-se só ao ataque principal do jogador em `handle_attack`
  (não a arremessos/mão-secundária), consistente com outros efeitos de turno.

### 3.3 Resistência Absoluta (`buff_saves`)
- **Ativar:** `p["resistencia_saves_ate"] = self.round_num + 2` (2 rodadas) e
  `p["resistencia_saves_val"] = 2`.
- **Aplicação:** em `_testar_save`, somar `self._resistencia_saves_bonus(alvo)` ao bônus
  (helper → `resistencia_saves_val` enquanto `resistencia_saves_ate >= round_num`, senão 0),
  **para jogadores**. Auto-expira.

### 3.4 Contra-Ataque (`contra_ataque`)
- **Ativar:** `p["contra_ataque_ate"] = self.round_num + 1` (até o próximo turno).
- **Elegibilidade de arma** (`_arma_contra_ataque_ok(p)`): corpo a corpo / alcance
  estendido (Lança `reach:lanca`, Chicote/Alabarda `range:2`) **ou a Besta de Mão**
  (`hand_crossbow`); **exclui** Arco Curto, Arco Longo e Besta pesada (as demais em
  `RANGED_AMMO`). Regra: `wid == "hand_crossbow"` → True; `wid in RANGED_AMMO` → False;
  senão True.
- **Alcance** (`_alvo_no_alcance_arma(p, m)`): monstro dentro do alcance real da arma —
  `range` (Chebyshev ≤ wr para chicote/alabarda/besta-de-mão), `reach:lanca`
  (`_lanca_no_alcance_jogador`), `reach:cajado` (`_cajado_no_alcance_jogador`), senão
  adjacência melee (`_is_adjacent_to_monster`).
- **Gatilho (nos 2 sites de ERRO de ataque de monstro — `return False # errou` em
  `_execute_one_monster_attack` ~11733 e no caminho legado ~13449):** quando o monstro
  `m` erra um jogador com `contra_ataque_ate >= round_num`, arma elegível e `m` no
  alcance → `_ataque_basico_reativo(jogador, m)`. Dispara a cada erro até expirar.

---

## 4. Catálogo (`GUILD_CATALOG`) — 4 entradas literais

Estilo 2a/2b. Ex.:
```python
"tecnica_contra_ataque": {
    "id": "tecnica_contra_ataque", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 280, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 8,
    "nome": "Contra-Ataque", "icon": "🗡️",
    "desc": "Até o próximo turno, quando um inimigo errar você (e estiver no alcance da sua arma corpo a corpo ou besta de mão), você o ataca de volta.",
    "efeito": {"tipo": "contra_ataque"},
},
# ... ataque_coordenado (efeito {"tipo":"ataque_coordenado"}, "alvo":"aliado"), 5r/180 4/4;
#     sangue_frio ({"tipo":"sangue_frio"}) 5r/180 2/2;
#     resistencia_absoluta ({"tipo":"buff_saves","saves":2,"rodadas":2}) 5r/180 4/4
```
> Agrupamento por recarga na Guilda já existe (2a) — as de 5r e 8r caem nas faixas
> "Recarga Média"/"Recarga Longa" automaticamente. (A faixa 8r ganha seu 1º item aqui.)

---

## 5. Cliente (`game.js`)

- **Ataque Coordenado** tem `alvo: "aliado"` → abre `openTargetModal` (padrão do 2b) com
  aliados vivos (sem raio — o par pode estar longe), enviando `usar_tecnica` com `target_id`.
- **Sangue Frio, Resistência Absoluta, Contra-Ataque** são auto-centradas → botão dispara
  `usar_tecnica` direto. As reações depois disparam sozinhas no servidor (broadcasts
  `dice_roll` + `gm_narration` já animam no cliente).

---

## 6. Testes (`tools/test_tecnicas_espec.py`)

Novas seções:
1. **Catálogo:** 4 técnicas com recarga/preço/custo corretos (Contra-Ataque 8r/280/6-6;
   os outros 5r/180; Sangue Frio 2-2).
2. **`_ataque_basico_reativo`:** acerto aplica dano (stub de `_rolar_ataque`/`d20_attack`);
   atacante rogue com furtivo elegível soma dados de furtivo; morte do alvo chama `_monster_dies`.
3. **Ataque Coordenado:** ativar grava par + turno; o hook faz o par atacar o alvo 1×
   (com o par no alcance) e não dispara se o par estiver fora do alcance; consome no turno.
4. **Sangue Frio:** ativar arma; num erro, re-rola (stub controlando o 2º d20); consome.
5. **Resistência Absoluta:** `_resistencia_saves_bonus` = 2 na janela, 0 após 2 rodadas;
   `_testar_save` reflete.
6. **Contra-Ataque:** `_arma_contra_ataque_ok` (melee/lança/chicote/alabarda/besta-de-mão =
   True; arco/besta-pesada = False); `_alvo_no_alcance_arma` por tipo; o hook de erro de
   monstro dispara o ataque reativo só com arma elegível + monstro no alcance + janela ativa.
7. **Comum:** recarga bloqueia reuso; fome/sede insuficientes recusam; alvo inválido (Coordenado) recusa sem custo.

---

## 7. Fronteiras (NÃO neste lote)

- **Oportunidade** (ordem de turno) — mini-lote próprio.
- Passivas (Último Esforço, Instinto de Sobrevivência) — lote 2d.
- Exclusivas Mago/Clérigo — Fase 3.
- A técnica "Resistência Absoluta" de 8r (dano à metade) do design original é **outra**
  coisa; será renomeada quando o lote Longo (self-buffs 8r: Conhecimento do Caçador,
  Determinação, redução de dano) for feito.
- Ataque Coordenado recíproco no turno do aliado (só o jogador ativo age por turno → o
  gatilho prático é você→par; a direção par→você é inócua num único turno).

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Recursão de reação (ataque reativo dispara outra reação) | `_ataque_basico_reativo` aplica dano direto, não chama `handle_attack` (igual `_furtivo_reativo`). |
| Anchors dos 2 sites de erro de monstro shiftados | Localizar por conteúdo (`return False` após `**ERROU!**` gm_say); lição das fases anteriores. |
| Sangue Frio re-rolar em loop | Consome a flag ANTES de re-rolar (uma única nova rolagem). |
| Elegibilidade de arma confundir chicote/alabarda (têm `range`) com arco | Regra por `RANGED_AMMO` + exceção `hand_crossbow`; chicote/alabarda/lança não usam munição → elegíveis. Testes cobrindo cada arma. |
| Furtivo reativo do Ladino aplicar sem condição | Gate por `_verificar_ataque_furtivo` (regras da classe); sem condição = ataque básico simples. |
| Morte do alvo no ataque reativo | `_monster_dies` chamado quando `hp<=0`; reusa o caminho de morte existente. |
| Contra-Ataque disparar contra monstro que atacou à distância e está longe | `_alvo_no_alcance_arma` barra se fora do alcance da arma. |
