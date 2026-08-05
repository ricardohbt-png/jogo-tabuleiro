# Upkeep de início de turno no modo Manual — design

Data: 2026-08-05
Branch de origem: `feat/instrumentos-bardo-fase5`

## Problema

Um monstro em `control_mode == "manual"` é despachado para
`_master_manual_window` em vez de `gm_phase` (server.py, `_activate_initiative_actor`,
ramo `monster_step`). Todo o upkeep de início de turno vive dentro da `gm_phase`,
então o monstro do mestre não passa por nada dele.

Consequência de jogo: **o monstro sob controle do mestre é imune a controle de
multidão**. Ele não perde o turno por petrificação, paralisia, rede, enredado,
sono, comando, dominar, medo ou lentidão; não sofre tique de veneno; o Réquiem
Final do bardo não o fere; maldições não expiram; e o lobisomem não regenera.

A lacuna é anterior a este trabalho — vem da Fase A do Modo Mestre, quando a
janela Manual foi criada. Foi descoberta ao implementar a Task 7 do plano da
ficha do monstro, porque as recargas também não andavam.

O que já foi corrigido lá (commit `ae77839`) é apenas o mínimo que aquelas
habilidades exigiam: expiração de `oculto_sombras` e tique de
`ability_cooldowns`/`monster_ability_cooldowns`, em `_upkeep_inicio_turno_manual`.
A docstring desse método registra que a cobertura é parcial.

## Decisão de escopo

**Prólogo inteiro, Provocação à parte.**

O bloco de upkeep da `gm_phase` é um prólogo coeso: uma sequência que termina
decidindo se o monstro age ou perde o turno. Ele é extraído por inteiro e
compartilhado.

A contagem da Provocação do bardo fica **fora**: ela não pertence ao prólogo —
roda depois, dentro da ação da IA, duplicada em dois pontos (server.py:23077 no
ramo `ai_type` e server.py:23219 no caminho legado). Trazê-la para o prólogo
consertaria o mestre, mas mudaria o momento da contagem para a IA, de depois da
ação para antes. Fica como item separado.

## Arquitetura

### O método extraído

```
_upkeep_inicio_turno_monstro(m, alive_monsters) -> bool
```

`True` = o monstro pode agir. `False` = o turno foi consumido.

Conteúdo, na ordem exata em que hoje aparece na `gm_phase`:

1. `_processar_mare_viva_turno(m)`
2. `_processar_venenos_turno(m)`
3. `_processar_mods_magia_turno(m)` — Amaldiçoar expira por rodada
4. lobisomem: regeneração +2 PV (salvo `regeneracao_bloqueada`) e
   `furia_lobisomem` em PV ≤ 12
5. morreu? → `False`
6. `_processar_requiem_turno(m)`
7. morreu? → `False`
8. `petrificado` → narra e `False`
9. `paralisado` → `_processar_paralisacao_turno(m)`; se consumir, `False`
10. `perde_turno` → `inabalavel` limpa e segue; senão narra e `False`
11. `enredado` → `inabalavel` limpa e segue; senão
    `_processar_enredado_turno(m)`; se consumir, `False`
12. `_status_monstro_turno(m, alive_monsters) == "pulou"` → `False`
13. senão `True`

A ordem é preservada literalmente. Como é extração pura, a IA fica
**byte-idêntica** — a mesma invariante que sustentou as Tasks 5, 6 e 7 do plano
da ficha do monstro.

### Os dois chamadores

**`gm_phase`** substitui o bloco por:

```python
            if not await self._upkeep_inicio_turno_monstro(m, alive_monsters):
                continue
```

**`_master_manual_window`** chama o prólogo **antes de abrir a janela**. Se o
retorno for `False`, retorna sem abrir. O encaixe é limpo porque `monster_step`
chama `_advance_initiative()` depois da janela de qualquer forma: o monstro
paralisado simplesmente não ganha janela e a iniciativa segue sozinha. A
narração já sai por `gm_say`, que é broadcast — o mestre vê o que aconteceu.

### Ordem dentro da janela Manual — ponto de paridade

`_upkeep_inicio_turno_manual` (expiração de `oculto_sombras` + tique das
recargas, da Task 7) hoje roda incondicionalmente ao abrir a janela. Na IA os
dois efeitos equivalentes vivem **dentro** de `_ai_bugbear_sombras` e `_ai_ogro`,
que só rodam se o prólogo passou — ou seja, sob a IA um monstro paralisado
**não** tica recarga.

Portanto a ordem correta em `_master_manual_window` é:

1. prólogo (`_upkeep_inicio_turno_monstro`); se `False`, retorna
2. só então `_upkeep_inicio_turno_manual(m)` e o resto dos resets do turno

Sem essa ordem, o monstro do mestre recarregaria habilidades enquanto
paralisado e a IA não.

### Dormência

A guarda `_monstro_ativo_em_combate(m)` continua onde está: na `gm_phase` antes
do prólogo, e no despacho de `monster_step` antes de chamar a janela. Monstro
dormente pula o upkeep nos dois caminhos, como hoje.

## Testes

Em `tools/test_modo_mestre.py`, seguindo o padrão numerado do arquivo:

- **Turno perdido não abre janela** — monstro `petrificado`, depois `paralisado`,
  depois `perde_turno`: `_master_manual_window` retorna sem setar
  `master_manual_mid` e sem criar o `asyncio.Event`.
- **Veneno tica no Manual** — monstro envenenado perde PV ao abrir a janela.
- **Réquiem fere no Manual** — monstro alvo do Réquiem sofre o dano.
- **Recarga não anda no turno perdido** — monstro paralisado com
  `ability_cooldowns` não vê os valores decrementarem (paridade com a IA).
- **Recarga anda no turno normal** — o caso já coberto pela Task 7 segue verde.
- **IA byte-idêntica** — um monstro em `auto` com os mesmos estados percorre a
  `gm_phase` e produz o mesmo resultado de antes da extração.

## Invariante

Sem mestre conectado, ou com o monstro em `auto`, o comportamento tem de
permanecer **byte-idêntico**. É a premissa de todo o Modo Mestre e a razão de o
prólogo ser extraído inteiro, em vez de reimplementado para o Manual.

## Fora de escopo

- **Contagem da Provocação do bardo** — duplicada em dois pontos pós-ação da IA;
  unificá-la mudaria a ordem para a IA. Item próprio.
- Redesenho do laço de iniciativa.
- Qualquer mudança no que os estados fazem — este trabalho só faz o monstro do
  mestre passar pelos mesmos efeitos que o monstro da IA já sofre.
