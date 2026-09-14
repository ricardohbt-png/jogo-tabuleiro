# Sacudida Jurássica + RD 4 do Tiranossauro Rex — Design

**Data:** 2026-09-13
**Branch de trabalho:** `wip/altura-voo-petrificacao` (o Tiranossauro Rex vive no WIP não
commitado de `server.py`, ~linha 5016)

## Objetivo

1. A RD 4 do Tiranossauro Rex passa a valer **só contra armas comuns** (`common_weapon_only`),
   igual ao Tirano da Mata/Ancestral. Magia, habilidades, dano de monstro e arma mágica
   atravessam.
2. Nova **passiva** *Sacudida Jurássica*: quando uma criatura fica Presa na Mordida, no
   **início do próximo turno do Tiranossauro** ela sofre automaticamente o dano da Mordida
   (4d12+7) **+2d6**, é solta e **arremessada 4 casas**; se colidir com um obstáculo sólido
   antes de completar as 4 casas, sofre **+2d6**.

Decisões fechadas em brainstorming:

| Dúvida | Decisão |
|---|---|
| O que a passiva substitui? | **As duas**: a ação `sacudida_brutal` (recarga 5) do T-Rex **e** o dano automático das Mandíbulas no início do turno. Sem isso a presa tomaria a mordida duas vezes na mesma rodada. |
| O T-Rex age depois de sacudir? | **Sim, normalmente** — a passiva não gasta ação. Move, morde (pode agarrar de novo) e usa a Caudada. |
| RD 4 | **Só armas comuns** (`common_weapon_only: True`). |
| O que conta como "parede" no +2d6? | **Qualquer obstáculo sólido**: parede de tile, porta fechada, decoração sólida e borda do mapa. Outra criatura interrompe o voo **sem** o bônus. |

## Estado atual (antes)

- Ficha do T-Rex: `resistances: [{"type":"physical","reduction":4}]` (RD geral).
- `mandibulas_colossais` com `automatic_damage: "4d12+7"` — aplicado em `_tirano_inicio_turno`
  a cada presa adjacente.
- `sacudida_brutal` como **ação** com `cooldown_turns: 5`, `bite_damage`/`extra_damage`/
  `wall_damage`/`throw_distance`. A IA (`_ai_tirano`) a dispara sempre que fora de recarga,
  antes de qualquer outra coisa; o mestre a ativa pela ficha (`handle_mestre_usar_habilidade`).
- `_empurrar(alvo, dx, dy, dist, detalhes=True)` devolve `{colidiu, parede}`; `parede` só é
  verdadeiro para tile `WALL` (fora da ponte). Porta fechada e decoração sólida **não** param
  o empurrão (a criatura atravessa) — defeito pré-existente. Borda do mapa interrompe com
  `parede=False`.

## Design

### 1. Ficha do Tiranossauro Rex (`server.py`, bloco `MONSTER_DEFS.extend` dos tiranossaurídeos)

- `resistances` → `[{"type": "physical", "reduction": 4, "common_weapon_only": True}]`.
- **Remover** `sacudida_brutal` da lista `special_abilities` do T-Rex. Tirano da Mata e Tirano
  Ancestral **mantêm** a `sacudida_brutal` deles, intocados (id compartilhado continua
  existindo para eles; `_tirano_sacudida` segue servindo os dois).
- **Adicionar** a passiva:

  ```python
  {"id": "sacudida_jurassica", "name": "Sacudida Jurássica", "action_type": "passiva",
   "bite_damage": "4d12+7", "extra_damage": "2d6", "wall_damage": "2d6",
   "damage_types": ["physical"], "throw_distance": 4,
   "descricao": "No início do turno do Tiranossauro, a criatura Presa sofre o dano da "
                "Mordida (4d12+7) +2d6, é solta e arremessada 4 casas. Se colidir com um "
                "obstáculo sólido antes do fim do arremesso, sofre +2d6 de dano físico."}
  ```

- A descrição das Mandíbulas Aprisionadoras do T-Rex passa a dizer que a presa é sacudida no
  início do turno (em vez de "sofre 4d12+7 automaticamente"). O campo `automatic_damage`
  **continua na ficha** (o validador do editor o preenche com default de qualquer forma); quem
  o desliga é o código, ver §2.

### 2. Início do turno (`_tirano_inicio_turno`)

Chamado no prólogo `_upkeep_inicio_turno_monstro`, que é **comum à IA e à janela Manual do
mestre** — logo a passiva dispara nos dois modos sem código extra (regra registrada na
memória "Manual pula a gm_phase": efeito de turno vai no prólogo).

Nova ordem dentro de `_tirano_inicio_turno(m)`:

1. `sacudida = self._tirano_ability(m, "sacudida_jurassica")`.
2. Se `sacudida` existe: para cada presa em `_agarrados_por(m)` que esteja adjacente ao
   footprint (`_is_adjacent_to_monster`), chama `await self._tirano_sacudida_jurassica(m, preso, sacudida)`.
   **Não** aplica o `automatic_damage` das Mandíbulas nesse caso.
3. Senão (Tirano da Mata/Ancestral e fichas antigas): comportamento atual das Mandíbulas,
   byte-idêntico.
4. O bloco do `engolido` (ácido do Engolir) fica como está.

### 3. `_tirano_sacudida_jurassica(m, preso, ab)` — novo helper

Extraído do ramo `rex_shake` de `_tirano_sacudida`, que fica **inalterado** para a
`sacudida_brutal` dos outros tiranos (não há mais T-Rex passando por ele; o ramo `rex_shake`
continua válido para uma ficha custom que dê `bite_damage` à `sacudida_brutal`).

1. Narração `T("narracao.sacudida_jurassica", monstro=nome_criatura(m), alvo=nome_criatura(preso))`.
2. `bruto = roll_dice(f"{bite_expr}+{extra}")` — `bite_expr` = `ab["bite_damage"]`, com o
   mesmo fallback de `_tirano_sacudida` (índice do ataque de mordida → `"4d12+7"`).
   `dano = _apply_damage_types(bruto, [DMG_PHYSICAL], preso)` (a RD da vítima vale; sem save).
   `await _dano_em_alvo(preso, dano, DMG_PHYSICAL, m["id"])`.
3. Se `_vivo(preso)`: `await _soltar_agarrado(preso)`; direção = sinal de
   `(preso.pos − casa_mais_próxima)`, onde a casa mais próxima é o tile de `_monster_tiles(m)`
   com menor Chebyshev e, em empate, menor Manhattan até a vítima (evita diagonal torta que a
   âncora do 2×2 produz). `res = await _empurrar(preso, dx, dy, throw_distance, detalhes=True)`.
4. Se `res["parede"]` e `_vivo(preso)`: narração
   `T("narracao.sacudida_jurassica_colisao", alvo=..., dano=...)` e mais `roll_dice(wall_damage)`
   pelo mesmo funil `_apply_damage_types` + `_dano_em_alvo`.
5. Vale para herói **e** para monstro/servo preso (o agarrão já prende monstro — ver memória
   do agarrão). `_dano_em_alvo` e `_empurrar` já são genéricos pelo alvo.

### 4. `_empurrar` — obstáculo sólido

- Substituir `self.tiles[ny][nx] == WALL and not self._ponte_em(nx, ny)` por
  `self._blocks_tile(nx, ny)`; `_blocks_tile` já trata ponte (sobre ponte só decoração
  bloqueia), parede, porta fechada e decoração sólida. O caso especial `saiu_da_ponte`
  (queda ao sair da ponte para um WALL-abismo) é preservado exatamente como está, e nesse
  caso `parede` continua `False`.
- Borda do mapa passa a devolver `parede=True`.
- Único chamador que lê `parede` hoje: `_tirano_sacudida` (linha ~36504). Os demais chamadores
  recebem só o booleano `colidiu`, cujo significado não muda.
- **Efeito colateral aceito (correção):** todo empurrão passa a parar em porta fechada e
  decoração sólida em vez de atravessá-las.

### 5. IA e mestre

- `_ai_tirano`: sem mudança. `_tirano_sacudida(m)` devolve `False` para o T-Rex (não tem mais
  `sacudida_brutal`); após a passiva soltar a presa, `preso` é `None` e o T-Rex segue o fluxo
  normal (move, Mordida, Caudada). O ramo `is_trex and preso` continua servindo o caso raro de
  presa **não adjacente** no início do turno (ninguém foi sacudido).
- `_habilidade_ativavel_manual`: passiva → `False` (mostra "IA apenas" na ficha), correto —
  não há o que ativar à mão.
- `game.js` `_animadoManualAbilityList`: sem mudança (lista de ativáveis).

### 6. Editor de criaturas

- `_validate_custom_monster` (`server.py`, dois sites: normalização ~42133 e `entry` ~42359):
  ramo `sacudida_jurassica` com `bite_damage` (str, default `"4d12+7"`), `extra_damage`
  (`"2d6"`), `wall_damage` (`"2d6"`), `throw_distance` (1–8, default 4), `damage_types`
  físico, `action_type` forçado `"passiva"`, e descrição gerada.
- `tools/editor_monster_editor.js`: linha 219 (serialização) e os dois pontos que hoje tratam
  `sacudida_brutal` (~477 e ~654) ganham o irmão `sacudida_jurassica` com os mesmos campos
  menos `damage_dice/faces`.
- Regenerar `tools/editor_catalog.js` com `python tools/export_catalog.py` (arquivo gerado).

### 7. Idioma

Duas chaves novas em `src/lang/narracao.js` (pt/en, paridade de `{params}` — o
`test_erros.py` cobra):

- `narracao.sacudida_jurassica` — "{monstro} sacode {alvo} violentamente nas mandíbulas e o
  arremessa!" / "{monstro} shakes {alvo} violently in its jaws and hurls it away!"
- `narracao.sacudida_jurassica_colisao` — "{alvo} se choca contra um obstáculo e sofre {dano}
  a mais!" / "{alvo} slams into an obstacle and takes {dano} more!"

Nome e descrição da habilidade **não** se traduzem (habilidades de monstro não são família de
catálogo — regra da etapa 4c).

### 8. Testes (`tools/test_tirano.py`)

Seções novas/alteradas, com `roll_dice` mockado como as existentes:

- `[1]` RD do T-Rex é `[{"type":"physical","reduction":4,"common_weapon_only":True}]`; arma
  comum sofre −4, arma `magical` não.
- `[2]` T-Rex **não** tem `sacudida_brutal` e tem `sacudida_jurassica` passiva.
- `[2b]` Prólogo: herói preso adjacente + `_upkeep_inicio_turno_monstro(m, …)` → um único
  `roll_dice("4d12+7+2d6")` (não há `4d12+7` avulso das Mandíbulas), presa solta, posição a
  4 casas na direção oposta ao footprint, HP debitado.
- `[2c]` Parede a 2 casas → para na casa antes da parede e rola `2d6` extra. Repetir com
  porta fechada (`DOOR` + sala `locked`), decoração sólida e borda do mapa: todos `+2d6`.
  Outro herói no caminho: para antes dele, **sem** `2d6`.
- `[2d]` Depois da sacudida o T-Rex ainda ataca no mesmo turno (a IA executa a Mordida contra
  alguém adjacente).
- `[2e]` Presa que escapou no próprio turno (`preso=False`) não é sacudida.
- `[2f]` Tirano da Mata inalterado: dano automático das Mandíbulas no prólogo e
  `sacudida_brutal` com recarga (os checks existentes migram para o Mata).
- `[4]` Round-trip do editor preserva `sacudida_jurassica` (bite/extra/wall/throw).
- Manual: com `master_pid` ativo e monstro em `manual`, o prólogo dispara a sacudida
  igualmente (reusa o padrão de `test_modo_mestre.py`).

Rodar depois: `tools/test_tirano.py`, `tools/test_agarrao.py`, `tools/test_ponte*.py` (se
existir) e a suíte de idioma (`tools/test_idioma.py`, `tools/test_narracao.py`).

## Fora de escopo

- Animação 3D dedicada do arremesso (o peão só reposiciona no `game_state` seguinte).
- Popup `trap_result` para a vítima.
- Qualquer mudança na Sacudida Brutal do Tirano da Mata/Ancestral.
- Tradução de nome/descrição da habilidade.
