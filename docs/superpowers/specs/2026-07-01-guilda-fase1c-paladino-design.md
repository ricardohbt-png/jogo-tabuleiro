# Guilda dos Heróis — Fase 1c: Especializações do Paladino

**Data:** 2026-07-01
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 1c (Paladino). Fase 1 decomposta por classe. Feito: 1a (Guerreiro),
1b (Clérigo). Próximas: Ladino, Bardo, Mago.
**Depende de:** Fase 0 + padrão das Fases 1a/1b (`tem_espec`, entradas
`categoria:"especializacao"` no `GUILD_CATALOG`, `handle_guild_buy`).

---

## 1. Visão geral

Especializações = upgrades permanentes e sempre-ativos das habilidades-base
(sem slot, sem "equipar"). Esta sub-fase cobre o **Paladino** (Richard,
`class_id:"paladin"`) — a classe mais extensa, com **5 linhas**. As 5 habilidades
hoje estão no poder máximo; a Fase 1c **enfraquece o baseline** e vende os níveis
II/III na Guilda.

### Estado atual (confirmado no código)
As 5 habilidades de Richard NÃO passam pelo fluxo genérico de `skill` (sem `mp`):
- **`handle_imposicao_maos`** (~6632): Cura pelas Mãos — `roll_dice("1d6") + mod(str_)`
  em aliado adjacente; 🍖3💧2.
- **Golpe Sagrado** (`handle_golpe_sagrado` ~6670, toggle; dano aplicado em
  `handle_attack` ~5116: `holy_roll = roll_dice("1d8")`; upkeep 🍖1💧1 em
  `_processar_manutencao_richard`).
- **`_ativar_guerreiro_luz`** (~6777): escolhe bônus `visao/ataque/dano/ca` (0–2 cada),
  custo por ponto; **hoje sem limite** de quantos atributos não-zero. Visão expande
  a névoa (`_reveal_around` com `_get_raio_visao`).
- **`handle_protetor`** (~6702, ação bônus; `_no_raio(p, alvo, 4)`) + transferência em
  **`_processar_dano_protetor`** (~6873): `dano_aliado = dano_richard = dano_original // 2`,
  checa `_no_raio(richard, alvo, 4)`.
- **`_ativar_regeneracao_divina`** (~6759) + upkeep em `_processar_manutencao_richard`
  (~6822): +1 HP **só do Richard**/turno, 🍖1💧1.

---

## 2. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Modelo | Base = Nível I grátis fraco; comprar II/III; **III exige II** por linha; II=150, III=200. 9 nós. |
| Cura pelas Mãos | Base 1d6+FOR; **II → 2d6+FOR**; **III → opção +1d6 por +2🍖/+2💧 por uso** (repetível, cap 3). |
| Ataque Sagrado | Base +1d8 sagrado; **II → +2d8**. (Só II — sem III.) |
| Guerreiro da Luz | Base **2 atributos** ativos; II → 3; III → 4. Com Visão ativa, **detecta armadilhas** no raio **1 / 2 / 3** por nível. |
| Defensor | Base 50%/50% raio 4; **II → raio 5**; **III → 40%/40%** (20% do dano é mitigado). |
| Regeneração | Base **só Richard** (+1 HP); **II → +1 HP aliados adjacentes** (raio 1); **III → raio 2**. |
| Custo | Ouro é o custo das compras; a Cura Mãos III adiciona +2🍖/+2💧 opcional por +1d6. Demais mantêm o custo atual. |
| Arquitetura | Imperativa: catálogo p/ exibição/compra; gating inline nos handlers via `tem_espec` + helpers. |
| Autoridade | Servidor autoritativo (limita atributos/dados; recusa opções não destravadas). |

---

## 3. Catálogo (`GUILD_CATALOG`, server.py)

Nove entradas `categoria:"especializacao"`, `classe:"paladin"`, `exclusiva:false`.

```python
"paladino_cura_maos_2": { "id":"paladino_cura_maos_2","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_cura_maos","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Cura pelas Mãos II","icon":"🙏","desc":"Imposição das Mãos cura 2d6 + FOR." },
"paladino_cura_maos_3": { "id":"paladino_cura_maos_3","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_cura_maos","nivel":3,"requer":"paladino_cura_maos_2","exclusiva":False,"preco":200,
    "nome":"Cura pelas Mãos III","icon":"🙏","desc":"Pode gastar +2🍖/+2💧 por +1d6 de cura (até 3×)." },
"paladino_ataque_sagrado_2": { "id":"paladino_ataque_sagrado_2","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_ataque_sagrado","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Ataque Sagrado II","icon":"⚔️","desc":"Golpe Sagrado causa +2d8 de dano sagrado por ataque." },
"paladino_luz_2": { "id":"paladino_luz_2","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_luz","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Guerreiro da Luz II","icon":"💡","desc":"Mantém 3 atributos ativos; com Visão, detecta armadilhas em raio 2." },
"paladino_luz_3": { "id":"paladino_luz_3","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_luz","nivel":3,"requer":"paladino_luz_2","exclusiva":False,"preco":200,
    "nome":"Guerreiro da Luz III","icon":"💡","desc":"Mantém 4 atributos ativos; com Visão, detecta armadilhas em raio 3." },
"paladino_defensor_2": { "id":"paladino_defensor_2","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_defensor","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Defensor II","icon":"🛡️","desc":"O alcance da proteção aumenta para 5 quadrados." },
"paladino_defensor_3": { "id":"paladino_defensor_3","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_defensor","nivel":3,"requer":"paladino_defensor_2","exclusiva":False,"preco":200,
    "nome":"Defensor III","icon":"🛡️","desc":"O dano dividido cai para 40%/40% (20% é mitigado)." },
"paladino_regen_2": { "id":"paladino_regen_2","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_regen","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Regeneração II","icon":"✨","desc":"Regeneração Divina também cura +1 HP dos aliados adjacentes." },
"paladino_regen_3": { "id":"paladino_regen_3","categoria":"especializacao","classe":"paladin",
    "linha":"paladino_regen","nivel":3,"requer":"paladino_regen_2","exclusiva":False,"preco":200,
    "nome":"Regeneração III","icon":"✨","desc":"A Regeneração Divina alcança aliados em raio 2." },
```

`handle_guild_buy` (Fase 0) valida classe/`requer`/posse/ouro. Sem mudança.

---

## 4. Gating no servidor (helpers + handlers)

Helpers como métodos de `GameRoom`, perto dos helpers do Clérigo (`_cura_teto` etc.),
usando `tem_espec(p, id)`:

```python
    def _cura_maos_dados(self, p):
        return 2 if tem_espec(p, "paladino_cura_maos_2") else 1
    def _ataque_sagrado_dados(self, p):
        return 2 if tem_espec(p, "paladino_ataque_sagrado_2") else 1
    def _gdl_max_atributos(self, p):
        if tem_espec(p, "paladino_luz_3"): return 4
        if tem_espec(p, "paladino_luz_2"): return 3
        return 2
    def _gdl_trap_raio(self, p):
        if tem_espec(p, "paladino_luz_3"): return 3
        if tem_espec(p, "paladino_luz_2"): return 2
        return 1
    def _defensor_raio(self, p):
        return 5 if tem_espec(p, "paladino_defensor_2") else 4
    def _regen_raio(self, p):
        if tem_espec(p, "paladino_regen_3"): return 2
        if tem_espec(p, "paladino_regen_2"): return 1
        return 0
```

### 4.1 Cura pelas Mãos (`handle_imposicao_maos`)
- Rolar `_cura_maos_dados(p)` d6 (em vez de 1) + `mod(str_)`.
- **III (opt-in):** ler `extra_d6 = clamp(0..3, data.extra_d6)`; se >0, exigir
  `tem_espec(p,"paladino_cura_maos_3")` (senão zerar); somar `extra_d6` d6 à cura e
  cobrar `+2*extra_d6` 🍖 e 💧 (além do custo base 🍖3💧2). Validar recursos totais
  antes de aplicar.

### 4.2 Ataque Sagrado (`handle_attack`, bloco Golpe Sagrado ~5116)
- Trocar `roll_dice("1d8")` por rolar `_ataque_sagrado_dados(p)` d8 (soma). Ex.:
  `holy_roll = sum(roll_dice("1d8") for _ in range(self._ataque_sagrado_dados(p)))`.
  Ajustar o `dice_roll`/label.

### 4.3 Guerreiro da Luz (`_ativar_guerreiro_luz`)
- Após montar `bonus_validos`, contar atributos não-zero; se
  `> _gdl_max_atributos(p)` → recusar ("Guerreiro da Luz permite N atributos ativos").
- **Detecção de armadilhas:** quando `bonus_validos["visao"] > 0` (na ativação e a
  cada upkeep enquanto ativo com Visão), revelar as armadilhas dentro de
  `_gdl_trap_raio(p)` ao redor de Richard — reusar o mecanismo de revelação de
  armadilhas do Ladino (marcar `visivel`/`revelada` das `armadilhas` colocáveis e das
  `traps` de masmorra no raio). O upkeep vive em `_processar_manutencao_richard`.

### 4.4 Defensor (`handle_protetor` + `_processar_dano_protetor`)
- Trocar os dois `_no_raio(..., 4)` por `_no_raio(..., self._defensor_raio(richard/p))`.
- Split do dano: helper
  ```python
      def _defensor_split(self, richard, dano):
          if tem_espec(richard, "paladino_defensor_3"):
              parte = (dano * 2) // 5    # 40% (floor)
              return parte, parte        # aliado, richard — 20% mitigado
          return dano // 2, dano // 2    # base 50/50
  ```
  Usar em `_processar_dano_protetor` no lugar de `dano_original // 2`.

### 4.5 Regeneração (`_processar_manutencao_richard`, bloco regeneração)
- Após curar Richard +1 (comportamento atual), se `_regen_raio(p) > 0`: para cada
  aliado vivo (≠ Richard) dentro de `_regen_raio(p)` (Chebyshev) com HP < máx, +1 HP.
  Upkeep de custo mantém 🍖1💧1 (não escala com aliados). Mensagem lista os curados.

---

## 5. Cliente (`game.js` — renderer do Richard)

Lendo `GS.guildOwnedOf(me.id).especializacoes` (getters em `gameState.js`:
`paladinCuraMaosDados`, `paladinAtaqueSagradoDados`, `paladinLuzMaxAtributos`,
`paladinDefensorRaio`, `paladinRegenRaio`):
- **Imposição das Mãos:** se `cura_maos_3`, oferecer seletor de +1d6 (0–3) com o custo
  extra; enviar `extra_d6`. Descrição mostra 2d6 se `cura_maos_2`.
- **Golpe Sagrado:** descrição mostra +2d8 se `ataque_sagrado_2`.
- **Guerreiro da Luz:** o painel de escolha de atributos limita o nº de atributos
  não-zero ao teto (`paladinLuzMaxAtributos`); tentar exceder mostra dica.
- **Defensor/Regeneração:** descrições refletem o nível (raio 5 / 40% / aliados).

> Robustez na masmorra: `guildOwnedOf` já cai para o player do `game_state`. O
> servidor é autoritativo.

---

## 6. Testes (`tools/test_paladino_espec.py`)

Harness do projeto; helper `paladin(**owned)`. Stubar `_is_turn`/`_no_raio`/
`_tem_linha_de_visao`; mockar `roll_dice`/`random.randint` para dado fixo. Cobrir:
1. **Helpers:** `_cura_maos_dados` 1/2; `_ataque_sagrado_dados` 1/2;
   `_gdl_max_atributos` 2/3/4; `_gdl_trap_raio` 1/2/3; `_defensor_raio` 4/5;
   `_regen_raio` 0/1/2; `_defensor_split` (50/50 base; 40/40 com `_3`).
2. **Imposição:** base 1d6+FOR; com `cura_maos_2` 2d6+FOR (dado fixo → cura esperada);
   com `cura_maos_3` e `extra_d6=2`, cura +2d6 e custo +4🍖/+4💧.
3. **Golpe Sagrado:** dano sagrado dobra com `ataque_sagrado_2` (verificar via helper
   ou integração de ataque com mock).
4. **Guerreiro da Luz:** recusa 3 atributos sem `luz_2`; aceita 3 com `luz_2`, 4 com `luz_3`.
5. **Defensor:** `_processar_dano_protetor` divide 50/50 base; 40/40 com `_3`; raio 5 com `_2`.
6. **Regeneração:** upkeep cura aliado adjacente com `regen_2`; raio 2 com `regen_3`;
   base não cura aliados.
7. **Compra:** cada III recusado sem o II da linha.

---

## 7. Fronteiras (NÃO fazer nesta sub-fase)

- Outras classes; reembolso; tabela de custo extra genérica (Cura Mãos III traz o
  próprio +2/+2).

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Nerf (Guerreiro da Luz 4→2 atributos; Cura/Golpe/Defensor/Regen enfraquecidos) surpreende | Intencional; documentar no CLAUDE.md; níveis restauram/superam. |
| Detecção de armadilhas (feature nova) tocar sistemas de trap/névoa | Isolar numa task própria; reusar o mecanismo de revelação já existente; teste dedicado. |
| Split 40/40 arredondar mal | Regra explícita `(dano*2)//5`; teste 5 fixa. Base `//2` inalterado. |
| Regeneração em área alterar o upkeep de Richard | Curar aliados é aditivo ao bloco existente; custo de upkeep inalterado; teste 6. |
| 5 handlers + handle_attack + 2 processadores tocados | Uma task por linha no plano; regressão `test_devorador`. |
