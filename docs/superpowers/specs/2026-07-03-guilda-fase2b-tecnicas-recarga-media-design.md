# Guilda dos Heróis — Fase 2b: Técnicas de Recarga Média (5 rodadas)

**Data:** 2026-07-03
**Status:** Design aprovado (conteúdo) — pronto para review do spec escrito
**Fase:** 2b — 2º lote das **Técnicas da Guilda** (4º slot, genéricas). Segue o 2a
(Recarga Curta). Reações (Ataque Coordenado, Sangue Frio) e o **Foco Absoluto**
(que vira reação, ver §7) ficam para o lote de reações.
**Depende de:** Fase 2a (infra de técnicas: `handle_usar_tecnica` com dispatch por
`efeito.tipo`, agrupamento da Guilda por recarga, campos de estado, reset de recarga
na cidade).

---

## 1. Visão geral

5 técnicas genéricas de Recarga Média (5 rodadas). Todas: `categoria:"tecnica"`,
`classe:None`, `exclusiva:False`, `recarga_rodadas:5`, `custo_fome:4`, `custo_sede:4`,
`preco:180`, ids prefixados `tecnica_`. Reusam o dispatch por `efeito.tipo` de
`handle_usar_tecnica` (buff-and-act: não consomem a ação principal). Algumas exigem
**alvo** (`target_id`), que `handle_usar_tecnica` já aceita.

### Fatos verificados no código
- `handle_usar_tecnica(pid, tecnica_id, target_id=None)` centraliza turno/recarga/custo.
- Sites de **desvantagem** de ataque de monstro (usados pela Provocação): 2 lugares em
  `_execute_one_monster_attack` e no caminho legado — `prov = bool(m.get("provocado_turno_efeito"))` /
  `desvantagem = prov or esc == "desvantagem"`.
- `eff_target_ac` em `handle_attack` (CA do alvo-monstro) soma `_mod_magia(target,"ca")`,
  `_camuflagem_bonus`, etc. — ponto para o −2 CA da Pressão Constante.
- `_verificar_ataque_furtivo(luccas, alvo)` (server.py ~5268) — ponto para a imunidade a furtivo.
- `_processar_dano_protetor(alvo_id, dano)` (~7455) hoje é **paladino-only**
  (`q.get("class_id")=="paladin"`) — precisa generalizar para a Tática Defensiva.
- Movimento: `handle_move` (~5031) valida o passo; `_entity_blocks` (~11425) bloqueia
  casas ocupadas por criaturas; decorações bloqueiam via `_blocks_tile`/`_decor_block_tiles`.
  **Não existe "terreno difícil"** no jogo.
- `_moves_base(p)` (com `_grito_mov_bonus`) é o cálculo autoritativo de movimento no reset.
- `_grito_mov_bonus`/`mov_bonus_ate`/`mov_bonus_val` (2a) são o padrão de +movimento por rodadas.

---

## 2. As 5 técnicas

| Técnica | id | Alvo | Efeito | `efeito.tipo` |
|---|---|---|---|---|
| ⚡ **Investida Heroica** | `tecnica_investida` | — | Dobra o movimento; se **andar ≥2 quadrados em linha reta** desde a ativação, o próximo ataque **corpo a corpo** recebe vantagem +2 dano (consome no ataque). | `investida` |
| 🛡️ **Defesa Impecável** | `tecnica_defesa_impecavel` | — | Até o próximo turno: ataques contra você são feitos com **desvantagem** e você fica **imune a Ataque Furtivo**. | `defesa_impecavel` |
| 😖 **Pressão Constante** | `tecnica_pressao_constante` | inimigo **adjacente** | O alvo sofre **−2 CA** por 2 rodadas. | `debuff_ca_alvo` |
| 🤝 **Tática Defensiva** | `tecnica_tatica_defensiva` | aliado (raio 4) | Por **1d4 rodadas**, metade do dano sofrido pelo aliado é transferida a você (split 50/50). | `tatica_defensiva` |
| 👻 **Passo Fantasma** | `tecnica_passo_fantasma` | — | Por **1d4 rodadas**: **+2 movimento** e você atravessa casas ocupadas por **objetos** (não paredes nem criaturas) ao mover; a casa final deve ser válida e sem criaturas. | `passo_fantasma` |

---

## 3. Mecânica por técnica (autoritativo no servidor)

### 3.1 Investida Heroica (`investida`)
- **Ativar:** `p["moves_left"] += p["spd"]` (dobra o movimento, como Pressa); grava
  `p["investida_origem"] = list(p["pos"])` e `p["investida_armada"] = True`.
- **Consumo (em `handle_attack`, ataque a monstro):** o bônus só vale se **corpo a corpo**
  (`w_range is None`) E o deslocamento líquido desde `investida_origem` for **reto e ≥2**:
  `dx = pos.x−origem.x`, `dy = pos.y−origem.y`; reto = (`dx==0` ou `dy==0`);
  magnitude = `max(|dx|,|dy|) ≥ 2`. Se válido → `vantagem = True` e **+2 de dano**
  (mesmo termo condicional da Mira Perfeita). Consome `investida_armada` no ataque
  corpo a corpo (acerto ou erro). Se o herói atacar sem ter carregado, o ataque ocorre
  normal e a flag permanece (aguarda um ataque que cumpra a condição), expirando no fim
  do turno. Campos limpos no reset de fim de turno.
- **Fronteira:** só melee; ataque à distância nunca consome nem recebe o bônus.

### 3.2 Defesa Impecável (`defesa_impecavel`)
- **Ativar:** `p["defesa_impecavel_ate"] = round_num + 1` (vale até o próximo turno).
- **Desvantagem no atacante:** nos 2 sites de ataque de monstro, incluir no cálculo de
  `desvantagem` a condição `alvo.get("defesa_impecavel_ate",0) >= round_num` (helper
  `_defesa_impecavel_ativa(p)`).
- **Imune a furtivo:** em `_verificar_ataque_furtivo(luccas, alvo)`, retornar `False`
  quando `alvo.get("defesa_impecavel_ate",0) >= round_num`.

### 3.3 Pressão Constante (`debuff_ca_alvo`)
- **Ativar (exige `target_id` de monstro adjacente):** valida que o alvo é monstro e
  está adjacente (Chebyshev 1) ao usuário; senão erro. Marca no monstro
  `alvo["pressao_ca_ate"] = round_num + 2` e `alvo["pressao_ca_val"] = 2`.
- **Aplicação:** em `handle_attack`, no `eff_target_ac`, subtrair
  `self._pressao_ca_pen(target)` (helper → `pressao_ca_val` enquanto
  `pressao_ca_ate >= round_num`, senão 0). CA menor = mais fácil de acertar.

### 3.4 Tática Defensiva (`tatica_defensiva`)
- **Ativar (exige `target_id` de aliado em raio 4):** valida aliado vivo dentro de
  `_no_raio(user, alvo, 4)`. Grava no **usuário**: `p["tatica_alvo"] = alvo_id`,
  `p["tatica_ate"] = round_num + rolar(1d4)`.
- **Split do dano:** generalizar `_processar_dano_protetor(alvo_id, dano)` para, além do
  paladino (Protetor), reconhecer um protetor genérico: qualquer jogador vivo `q` com
  `q.get("tatica_alvo")==alvo_id` e `q.get("tatica_ate",0) >= round_num`, aplicando split
  **50/50** (`_defensor_split` base já é 50/50 para não-paladino; para Tática usar sempre
  50/50). O paladino mantém seu comportamento (specs de Defensor). Expira sozinho quando
  `tatica_ate < round_num` (sem upkeep).
- **Escopo:** não empilha com o Protetor do paladino no mesmo alvo — se ambos existirem,
  aplica só um (prioridade: o primeiro encontrado; documentar).

### 3.5 Passo Fantasma (`passo_fantasma`)
- **Ativar:** `p["passo_fantasma_ate"] = round_num + rolar(1d4)`; concede +2 de movimento
  imediato (`moves_left += 2`) + buff transitório reusando `mov_bonus_ate`/`mov_bonus_val`
  (para o +2 sobreviver ao reset via `_grito_mov_bonus`). *(Nota: `mov_bonus_val=2` já é o
  mesmo valor do Grito; se o herói tiver Grito ativo o valor não empilha — aceitável.)*
- **Atravessar objetos:** em `handle_move`, enquanto `passo_fantasma_ate >= round_num`,
  a validação do passo **ignora o bloqueio de decoração** (permite pisar em casa de
  objeto), MAS mantém: paredes/limites do mapa (não atravessa) e `_entity_blocks`
  (não termina/pisa em casa de criatura). Assim a casa final é sempre válida e sem
  criaturas, e paredes continuam bloqueando.

---

## 4. Catálogo (`GUILD_CATALOG`, server.py)

5 entradas literais após as técnicas do 2a, no estilo do 2a. Exemplo:
```python
"tecnica_investida": {
    "id": "tecnica_investida", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
    "nome": "Investida Heroica", "icon": "⚡",
    "desc": "Dobra o movimento; se andar ≥2 casas em linha reta, o próximo ataque corpo a corpo tem vantagem +2 dano.",
    "efeito": {"tipo": "investida", "bonus_dano": 2},
},
# ... defesa_impecavel, pressao_constante (efeito debuff_ca_alvo, requer alvo),
#     tatica_defensiva (requer alvo aliado, raio 4), passo_fantasma
```
(As 5 seguem o mesmo shape; valores conforme §2. As que exigem alvo marcam
`"alvo": "monstro_adjacente"` / `"aliado_raio4"` para o cliente saber pedir o alvo.)

> **Agrupamento por recarga:** as 5 entram na faixa "Recarga Média (5 rodadas)" —
> o cliente já agrupa por `recarga_rodadas` (2a); nenhuma mudança de render necessária.

---

## 5. Cliente (`game.js` + `gameState.js`)

- As técnicas **sem alvo** (Investida, Defesa Impecável, Passo Fantasma) disparam
  `usar_tecnica` direto no botão do 4º slot, como as do 2a.
- As técnicas **com alvo** (Pressão Constante → inimigo adjacente; Tática Defensiva →
  aliado em raio 4) abrem o **modal de seleção de alvo** já existente (`openTargetModal`)
  filtrando os candidatos válidos, e enviam `usar_tecnica` com `target_id`. O tipo de
  alvo vem do campo `alvo` da entrada do catálogo.
- Sem novos getters de estado — o efeito é autoritativo no servidor.

---

## 6. Testes (`tools/test_tecnicas_espec.py`)

Novas seções (o arquivo já existe do 2a):
1. **Catálogo:** as 5 técnicas com `recarga_rodadas:5`, `preco:180`, custo 4/4, `classe:None`.
2. **Investida:** ativar dobra movimento + arma; helper de charge retorna vantagem/+2 só
   quando reto ≥2 e melee; deslocamento em L ou <2 não concede; expira no fim do turno.
3. **Defesa Impecável:** `_defesa_impecavel_ativa` True na janela; `_verificar_ataque_furtivo`
   retorna False contra alvo protegido; expira.
4. **Pressão Constante:** exige alvo adjacente (recusa não-adjacente); `_pressao_ca_pen`
   = 2 na janela, 0 após 2 rodadas; `eff_target_ac` reflete.
5. **Tática Defensiva:** exige aliado em raio 4; `_processar_dano_protetor` divide 50/50
   pelo protetor genérico enquanto `tatica_ate >= round_num`; expira.
6. **Passo Fantasma:** ativa buff de +2 mov (via `_grito_mov_bonus`/`_moves_base`) e o
   flag de atravessar objetos; helper `_passo_fantasma_ativo` True na janela; expira.
7. **Comum:** recarga 5 bloqueia reuso; fome/sede insuficientes recusam.

---

## 7. Fronteiras (NÃO neste lote)

- **Foco Absoluto** → adiado; vira **reação** ("Resistência Absoluta") num lote futuro.
  ⚠️ Há um conflito de nome com a técnica "Resistência Absoluta" da faixa Longa (8r,
  "todo dano reduzido à metade") — decidir fundir/renomear no lote de reações.
- Reações (Ataque Coordenado, Sangue Frio, Contra-Ataque, Oportunidade) — lote 2c.
- Passivas (Último Esforço) — lote 2d. Exclusivas Mago/Clérigo — Fase 3.
- "Terreno difícil" não existe → Passo Fantasma cobre só objetos.

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Investida: rastrear "linha reta ≥2" | Deslocamento líquido `investida_origem`→`pos` (reto = dx==0 ou dy==0, mag ≥2); testes cobrindo reto/L/curto/melee-vs-ranged. |
| Generalizar `_processar_dano_protetor` quebrar o Protetor do paladino | Manter o ramo paladino intacto; adicionar o ramo genérico (tatica) como alternativa; testes do paladino (`test_paladino_espec.py`) devem seguir verdes. |
| Passo Fantasma pular o bloqueio errado (parede/criatura) | Ignora só decoração; paredes e `_entity_blocks` (criaturas) permanecem — a casa final nunca é parede nem criatura. |
| Defesa Impecável / Pressão em 2 sites de ataque de monstro | Reusar os mesmos 2 sites da Provocação (verificar anchors por conteúdo no plano — números de linha shiftaram muito nas fases anteriores). |
| Buff de +2 mov do Passo Fantasma colidir com o Grito (`mov_bonus_val`) | Compartilham o campo; não empilham (assume-se 1 fonte por vez). Aceitável; documentado. |
| Alvo inválido (não-adjacente / fora do raio) | Validação explícita com mensagem de erro antes de debitar custo/recarga. |
