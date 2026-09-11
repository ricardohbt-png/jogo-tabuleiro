# Animação de combate híbrida (3D) — design

**Data:** 2026-09-10
**Escopo:** cliente 3D (`game.js` + módulo puro novo). Sem mudança de servidor, protocolo ou i18n.
**Fora de escopo:** modo 2D (canvas), projéteis de ataque à distância (frente B), pós-processamento (frente C), modelos rigados (frente D).

## 1. Problema

Os 64 GLBs de herói e monstro são estáticos (zero clips, zero skins — verificado no JSON de cada arquivo). Hoje um ataque no 3D é: cue sonoro, linha + seta + anel + placa de texto entre atacante e alvo (`_attackFeedbacks`), d20 físico que rola, e — quando o `game_state` com o HP novo chega — número flutuante e uma oscilação de 190 ms / 0,055 rad no alvo (`_hitReactions`). O atacante não se move; o alvo mal reage; a morte é o peão sumindo e a lápide aparecendo no mesmo frame.

O feedback que existe é bom mas chega **antes** de o dado assentar, então a tensão do "rolou… 18! acertou!" se perde.

## 2. Tom: híbrido

Base de **miniatura de mesa** (peça desliza, balança, tomba) para todo ataque; **exageros de videogame** (flash, knockback maior, hit-stop, shake de câmera, partículas) reservados a **crítico e morte** — os momentos que a mesa comemora.

## 3. Arquitetura

### 3.1 Módulo puro `src/combatScene.js` (`window.CombatScene`)

Máquina de estados **sem DOM/THREE** (mesmo padrão de `src/difficulty.js` e `src/i18n.js`), testável em node. Uma **cena por `attack_id`**.

Entrada (eventos):
- `start(msg)` — do `attack_feedback` fase `start` (`attacker_id`, `target_id`, `attacker_pos`, `target_pos`).
- `result(msg)` — fase `result` (`hit`, `crit`, `natural_critical`, `natural_fumble`).
- `dieSettled({die, value, label})` — gancho do d20 3D (ver 3.3).
- `handoff(targetKey, impact)` — do diff de HP (ver 3.4): `{amount, kind, damageType, critical, status, death}`.
- `tick(now)` — avança fases por tempo; devolve comandos.

Saída (comandos consumidos pelo `game.js`): `windup`, `strike`, `impact{...}`, `death{key, dir}`, `end`.

Consultas: `poseFor(key, now)` → `{dx, dz, rotX, rotZ, scaleY, flash} | null`; `pendingFor(targetKey)` → cena que ainda vai dar impacto nesse alvo, ou `null`; `isDying(key)`; `shake(now)` → offset de câmera ou `null`.

Chaves de entidade seguem as já usadas pelo `_hitReactions`: `p:<pid>`, `m:<mid>`, `a:<aid>`, `pr:singleton`.

### 3.2 Linha do tempo

```
start ──► ARMANDO ──► (result) ──► ESPERANDO_DADO ──► GOLPE ──► IMPACTO ──► FIM
```

| Fase | Atacante | Duração |
|---|---|---|
| `ARMANDO` | recua `windup.dist` (0,15 casa) para longe do alvo, ease-out | 180 ms, depois segura |
| `ESPERANDO_DADO` | mantém a pose armada | até `dieSettled` (ou fallback) |
| `GOLPE` | avança `strike.dist` (0,35 casa) rumo ao alvo, `rotation.x −0,12`, ease-in | 110 ms |
| `IMPACTO` | alvo reage; número, flash, crit/morte (seção 4) | — |
| `FIM` → retorno | volta à casa com overshoot 0,03 | 220 ms |

Regras de sincronia:
- A cena em `ESPERANDO_DADO` **mais antiga** consome o **primeiro d20 que assentar depois do seu `result`**. Não há correlação por id: o servidor emite o `dice_roll` do ataque logo após o `result`, e a fila `_dadosMagiaFila` já impede dados de se atropelarem.
- Re-rolagem (Sangue Frio/Sorte): o `result` só é emitido depois do reroll, e a cena só consome dado com `result` já recebido — o último d20 é o que vale.

Fallbacks (todos levam a `GOLPE` imediato):
- nenhum d20 assentar em `waitDieMs` (3,5 s) após o `result`;
- `_animationSpeedMode === 'instant'` → `result` colapsa direto em `IMPACTO` (sem investida, sem shake, número na hora — igual a hoje);
- `result` sem `start` (mensagem perdida/reconexão) → só a fase de impacto;
- qualquer cena com mais de `expireMs` (6 s) é encerrada e o peão restaura a base.

Fila: dois ataques do mesmo atacante (Fúria) → a 2ª cena só entra em `ARMANDO` após o `FIM` da 1ª.

### 3.3 Gancho do dado

No d20 3D, o ponto onde `obj.phase='settling'` é atribuído após o tween de `snapping` (onde toca `playSettle()` e solta as partículas douradas) chama `CombatScene.dieSettled({die, value, label})`.

### 3.4 Hand-off do dano (a cena é dona do instante do impacto)

O diff de HP (`_hpSnapshot`, em `game.js`) hoje dispara `_playCombatCue`, `_triggerHitReaction` e `_spawnCombatFeedback` na hora. Passa a:

```
if(mode3D && g3){ const cena = CombatScene.pendingFor(key); if(cena){ cena.handoff({...}); continue; } }
// senão: comportamento atual, intocado
```

Consequências:
- Dano **sem** cena (magia, armadilha, veneno, chamas, queda) segue exatamente como hoje.
- Cura nunca passa pela cena.
- No 2D (`!mode3D`) nada muda.
- O `game_state` com o HP novo chega **antes** de o dado assentar (caso normal) — a cena guarda o impacto e o solta no `IMPACTO`. Se chegar depois (rede lenta), a cena já está em `IMPACTO`/`FIM` e o hand-off dispara o feedback imediatamente. Para isso valer, a **reação do alvo** (oscilação/esquiva/flash/shake) é decidida por `result.hit`/`crit` — não depende do hand-off; o hand-off só acrescenta o **número**, o cue de dano e a **morte**. A cena continua viva (sem pose) por até `expireMs` esperando um hand-off tardio.
- `death` vem no mesmo hand-off (o diff já detecta morte para o texto "☠").

### 3.5 Aplicação da pose no peão (idempotente, por chave)

No laço por peão de `renderMap3D` (onde já se escreve `fig.rotation.z = base + _hitReaction3DAngle(key)`), consulta-se `CombatScene.poseFor(key, now)`:
- `position.x/z = posição autoritativa (userData.gridX/gridY) + dx/dz` — o laço é dono de x/z **só enquanto houver pose**; sem pose não escreve.
- `rotation.x`, `scale.y` somados à base; `rotation.z` continua vindo da reação, agora com direção do golpe em vez do `seed`.
- Exclusões: peão em `estadoMovimento` (herói andando) e peão em deslize `entity_step` são pulados; o deslize pula figs com pose ativa. `rotation.y` não é tocado (redemoinho já o usa).
- A pose é por **chave**, não por `Group`: a assinatura de `obterFig` inclui seleção/chamas/veneno, e um clique no monstro no meio da cena reconstrói o objeto.
- Ao `FIM` a pose some e o frame seguinte restaura a base — nenhum estado torto sobrevive.

### 3.6 Flash com material compartilhado

`template.clone()` do GLB compartilha materiais; pintar `emissive` acenderia todos os goblins. No primeiro flash de um peão, seus materiais são clonados **uma vez** (marcados `_owned` para o `_disposeEntityTree` existente) e guardados em `userData._flashMats`. Só peões com crítico/morte pagam isso. Para sprites (`SpriteMaterial`), o flash clareia `material.color`.

### 3.7 Morte: o peão sobrevive ao `game_state` que o remove

Na varredura de descarte (`for(const [key, ent] of figCache) if(!figsUsadas.has(key)) …`), se `CombatScene.isDying(key)`, o fig é **transferido** para `g3._dyingFigs` em vez de descartado. O driver da morte é dono total do transform dele (fora do laço normal — o tombo gira em eixo arbitrário sem disputar `rotation.z`) e chama `_disposeEntityTree` ao terminar. O cadáver (`corp:`/`hero-corpse:`) nasce `visible=false` e liga quando a morte acaba. Se a remoção chegar antes do impacto (caso normal), o fig espera parado em `_dyingFigs` até o dado assentar.

Vale para monstro, servo animado, prisioneiro e herói.

### 3.8 Shake de câmera

OrbitControls recalcula a câmera de `position − target` a cada `update()`; um offset deixado lá seria absorvido como movimento do usuário. No tick de `startLoop3D`: **subtrair** o offset do frame anterior antes de `controls.update()`/`atualizarCamera()`, **somar** o novo depois. Ruído 2D de duas senoides com fases distintas (como as tochas), decaindo em `crit.shakeMs`. Respeita `matchMedia('(prefers-reduced-motion: reduce)')`.

### 3.9 Partículas

`_spawnGoldParticles(T, scene, pos)` generaliza para `_spawnBurstParticles(T, scene, pos, color, n)`; o dourado do dado vira caso particular. `_updateParticles` inalterado.

## 4. Vocabulário de movimentos

Corpo a corpo = distância Chebyshev entre `attacker_pos` e `target_pos` ≤ `meleeRange` (1,5).

**Atacante**
- Corpo a corpo: armar → golpe → retorno (3.2).
- À distância: sem investida; **recuo** de 0,10 casa contrário ao alvo em 90 ms, retorno em 200 ms (coice).
- Fumble (natural 1): golpe avança 0,50 casa e o retorno vem com oscilação (curva de `_hitReaction3DAngle`, 2 ciclos) no próprio atacante.

**Alvo, no `IMPACTO`**
- Acerto: oscilação amplificada (0,14 rad, 260 ms) na direção oposta ao atacante + **empurrão** de 0,12 casa e volta. Número flutuante e cue de dano saem neste instante.
- Erro: **esquiva** — 0,08 rad para trás, 200 ms, sem deslocamento, sem número (o sprite "ERROU" existente permanece).
- Crítico (`natural_critical` ou `crit`): acerto + flash emissivo branco (0→0,9→0 em 140 ms) + empurrão 0,30 + **hit-stop** de 80 ms (retorno do atacante e empurrão do alvo congelados) + shake (140 ms, amplitude 0,06) + burst de 18 partículas na cor de `damageTypes[tipo].color`.

**Morte**
- Tomba 90° em torno do eixo horizontal perpendicular à direção do golpe (cai para longe do atacante), 380 ms ease-in, quique de 4° no chão; escurece (`color × 0,35`) e desvanece (`opacity → 0`) nos últimos 200 ms; squash `scale.y 0,85` no toque.
- Recebe shake + partículas mesmo em acerto normal.
- Lápide/cadáver aparece só ao terminar (3.7).

Nada disso usa esqueleto: tudo é transformação da raiz do peão, igual para GLB, sprite e mini procedural.

## 5. Configuração

`src/visualConfig.js` → `feedback.combat.scene` (fonte única dos números):

```js
scene: {
  enabled: true,
  meleeRange: 1.5,
  windup:   { dist: 0.15, ms: 180 },
  strike:   { dist: 0.35, ms: 110, tiltX: 0.12 },
  recover:  { ms: 220, overshoot: 0.03 },
  ranged:   { recoil: 0.10, msOut: 90, msBack: 200 },
  fumble:   { dist: 0.50, wobbleCycles: 2 },
  hit:      { angle: 0.14, ms: 260, push: 0.12 },
  dodge:    { angle: 0.08, ms: 200 },
  crit:     { push: 0.30, flashMs: 140, flashPeak: 0.9, hitStopMs: 80,
              shakeMs: 140, shakeAmp: 0.06, particles: 18 },
  death:    { fallMs: 380, bounceDeg: 4, darken: 0.35, fadeMs: 200, squashY: 0.85 },
  waitDieMs: 3500,
  expireMs:  6000,
}
```

- `enabled=false` desliga o módulo inteiro (o diff de HP volta a disparar na hora) — rota de fuga.
- Toda duração passa por `_animationProgressDuration` (`fast` = 55%, `instant` = colapso, ver 3.2).
- Não se cria toggle novo de "reduzir movimento": `instant` já cumpre esse papel; só o shake honra `prefers-reduced-motion`.

## 6. Testes

- **`tools/test_combat_scene.js`** (node, puro): os cenários de ordem de eventos — `game_state` antes do dado (normal), dado antes do `game_state`, dois ataques seguidos do mesmo atacante (fila), reroll (último d20 vale), erro sem dano (esquiva), morte no hand-off; os fallbacks — sem dado em 3,5 s, `instant`, `result` sem `start`, expiração em 6 s; `poseFor` por fase (deslocamento aponta para o alvo; zero no `FIM`); corpo a corpo × à distância pela distância; `isDying` e `pendingFor`.
- **`tools/test_interface.py`**: checagem estática de que o diff de HP em `game.js` consulta `CombatScene.pendingFor` antes de `_spawnCombatFeedback`/`_triggerHitReaction` no ramo 3D (anti-regressão do hand-off).
- **Prova em navegador** (obrigatória): servidor **reiniciado**, `?v=` no cache-buster, 3D; um acerto corpo a corpo, um erro, um crítico (alvo `dormindo` → crítico automático no servidor) e uma morte — screenshot no instante do impacto de cada um; medidor de FPS sem custo fora do golpe.

## 7. Riscos e decisões registradas

- **Sincronia sem id de dado:** aceita-se "primeiro d20 após o `result`" em vez de correlação explícita, para não mexer no servidor. Se aparecer um caso em que um d20 alheio assenta entre `result` e o d20 do ataque, a correção é adicionar `attack_id` ao `dice_roll` — trabalho pequeno e isolado.
- **Materiais compartilhados:** o flash clona por peão sob demanda (3.6); nunca pintar o material do template.
- **OrbitControls absorve offsets:** o shake subtrai-antes/soma-depois (3.8); esquecer isso faz a câmera derivar.
- **Fig reconstruído no meio da cena:** pose por chave (3.5); nunca guardar o `Group` na cena.
