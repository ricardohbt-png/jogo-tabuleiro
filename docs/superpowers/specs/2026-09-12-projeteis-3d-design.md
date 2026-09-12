# Projéteis no 3D (frente B) — design

**Data:** 2026-09-12
**Escopo:** armas à distância (arco, besta, besta de mão — herói, monstro e servo animado), arremesso de itens (`handle_throw_item`, modos `ataque_alvo` e `area`) e a lança arremessada do kobold lanceiro. Servidor (campo novo no `attack_feedback` + 2 emissões novas) + módulo `src/combatScene.js` + render em `game.js`.
**Fora de escopo:** ataques naturais à distância de monstro sem categoria perfurante (cuspe, teia, sopro — frente C), magias (já têm animação própria), modo 2D, modelos GLB de projétil.
**Depende de:** `docs/superpowers/specs/2026-09-10-animacao-combate-hibrida-design.md` (a cena de combate; "GOLPE", "IMPACTO", `handoff`, `pendingFor` são de lá).

## 1. Problema

Ataques com arco/besta e itens arremessados não têm projétil: hoje é a linha+seta+placa e, desde a frente A, o "coice" do atacante com impacto instantâneo. O frasco de fogo grego "teleporta" ao lado de uma bola de fogo que voa. O `attack_feedback` não diz qual projétil é, e o arremesso de item nem emite `attack_feedback`.

## 2. Decisões de design (brainstorming)

- **Fontes:** armas à distância + itens arremessados (+ a lança do kobold). Cuspe/sopro ficam para a frente C.
- **Sincronia:** o projétil **dispara quando o d20 assenta** (o `GOLPE` da cena vira o lançamento) e o **impacto acontece na chegada** — a tensão do dado continua sendo o clímax; o voo é o suspense final.
- **Erro:** a flecha **passa reto** pelo alvo e crava 1 casa além; frasco cai numa casa vizinha. **Natural 1:** cai a meio caminho.
- **Visual:** híbrido — seta/virote/lança em **malha procedural** orientada pela trajetória; itens arremessados usam o **PNG do próprio item** como sprite girando.

## 3. Protocolo

### 3.1 Campo `projectile` no `attack_feedback start` (opcional)

```
projectile: {
  kind: 'arrow' | 'bolt' | 'spear' | 'item',
  item_id?: str,        // kind 'item' — para achar o PNG
  item_emoji?: str,     // kind 'item' — fallback quando não há PNG
  area?: bool,          // arremesso de área (sem alvo único)
  area_raio?: int,      // com area — raio Chebyshev
  sem_dado?: bool       // não há d20 a esperar: lança assim que o result chega
}
```

Cliente antigo ignora o campo. Nenhum outro payload muda (`result`, `dice_roll`, `game_state`, `combat_damage_events`).

### 3.2 Derivação no servidor — helper único `_projetil_de(atacante, arma_ou_ataque)`

Chamado pelos 3 sites que já emitem `start` (herói em `handle_attack`, monstro em `_execute_one_monster_attack`, servo animado em `atacar_animado`):

- **Herói:** arma com projétil → `arco_curto`/`longbow` → `arrow`; `besta`/`hand_crossbow` → `bolt`; armas do editor pelo campo `ammo` (`flechas`→`arrow`, `virotes`→`bolt`). Arma com `range` mas sem projétil (chicote, alabarda) → **sem campo**.
- **Monstro / servo:** ataque com `range ≥ 2` **e** `categoria == "perfurante"` → `arrow`; a ficha pode declarar `"projectile": "arrow"|"bolt"|"spear"` no ataque para sobrepor (kobold besteiro → `bolt`). Não-perfurante → sem campo.
- Retorna `None` quando não há projétil; o site só inclui o campo se não for `None`.

### 3.3 Arremesso de item passa a emitir `attack_feedback` (`handle_throw_item`)

- `ataque_alvo`: `start` antes do d20 e `result` depois (mesmo contrato do ataque; `hit`/`crit`/`natural_*` reais); `projectile = {kind:'item', item_id}`.
- `area`: não há teste de ataque. `start` com `target_pos=[tx,ty]`, `target_id=None`, `projectile={kind:'item', item_id, area:true, area_raio, sem_dado:true}`; `result` imediato com `hit:true`.

### 3.4 Arremesso de arma

Só o **kobold lanceiro** (`_kobold_throw_lance`) arremessa arma hoje — e ele já passa por `_execute_one_monster_attack`, logo já emite `attack_feedback`; o dict de ataque montado inline ali ganha `"projectile": "spear"` e a regra de 3.2 faz o resto (sem `sem_dado`: a IA anuncia o d20 normalmente). O `handle_arremesso_lanca` do herói **é código morto** (nenhum despacho de mensagem o chama e o cliente não o envia) — fica fora de escopo; se um dia for religado, cai na mesma regra por `throw_range` da arma.

## 4. A cena com voo (`src/combatScene.js`)

A cena guarda `projectile` (do `start`). Só o trecho `GOLPE → IMPACTO` muda:

```
… ESPERANDO_DADO ──► GOLPE = LANÇAMENTO ──(voo, travelMs)──► IMPACTO (chegada) ──► RECUPERANDO …
```

- **Lançamento:** ao entrar em `GOLPE`, a cena emite o comando **`launch`** `{id, kind, item_id, from:[x,z], to:[x,z], dir, travelMs, hit, fumble, crit, area, area_raio}`. O `result` já é conhecido nesse ponto. O atacante faz o **coice** (pose `ranged` já existente) no mesmo instante.
- **`travelMs`** = `clamp(dist_casas × msPerTile[kind], travelMinMs, travelMaxMs)`, onde `dist_casas` = distância Chebyshev entre `aPos` e `tPos`; passa pela `duration` injetada (é animação, não timeout — em `instant` vira ~0).
- **Impacto na chegada:** a fase `GOLPE` dura `travelMs` (em vez de `strike.ms`); `impactAt = launchAt + travelMs`. Reação do alvo, número, cue, crítico, morte, hand-off: tudo como na frente A, só o instante muda.
- **`sem_dado`** (só o arremesso de área hoje): a cena pula `ESPERANDO_DADO` — `ARMANDO` → `GOLPE` assim que o `result` está presente (imediato). `dieSettled` **não** consome dado para cenas `sem_dado` (senão o d20 de um save seria roubado).
- **Área** (`targetKey` nulo, `area:true`): sem pose de alvo; `pendingFor` nunca devolve uma cena de área (não há alvo único); na chegada emite `impact` com `area:true`, `area_raio` e `targetPos` — o `game.js` mostra o frasco quebrando. Os **números** dos atingidos são atrasados até a chegada pelo portão `_projetilFeedbackStartAt(entry)` (seção 5.4).
- **Erro:** `launch.hit=false` → o `to` do voo é estendido `missOvershootTiles` casas além do alvo na direção `dir`; o `impactAt` continua sendo a chegada **ao alvo** (a esquiva dispara aí); o trecho além é só visual. **Fumble** (`natural_fumble`): `to` = `from + (tPos − from) × fumbleFraction`, sem impacto no alvo (a cena emite `impact` com `hit:false` no fim do voo encurtado — a esquiva não ocorre; o alvo nem foi alcançado).
- Sem `projectile` no `start` → cena byte-idêntica à de hoje (o teste existente com 204 checks não muda).

## 5. Render (`game.js`)

### 5.1 Módulo de efeito

Família dos efeitos existentes (`_bolaFogoBuild3D`/`Update3D`/`Dispose3D`): **`_projetilBuild3D(anim)` / `_projetilUpdate3D(anim, now)` / `_projetilDispose3D(anim)`**, lista `_projeteis` alimentada pelo comando `launch` (em `_executarComandoCena`) e atualizada no `tick` de `startLoop3D` ao lado de `_tickCombatScene`. `dispose3D`/`init3D` limpam `_projeteis`.

### 5.2 Geometria por `kind` (procedural, criada uma vez por tipo e clonada)

- **`arrow`:** haste `CylinderGeometry` (r 0,012, comp. 0,55, madeira escura) + ponta `ConeGeometry` (cinza-aço) + 2 empenas `PlaneGeometry` 0,08×0,05 `DoubleSide` cruzadas na cauda.
- **`bolt`:** comp. 0,35, haste r 0,018, uma empena curta.
- **`spear`:** comp. 0,95, ponta maior, sem empenas.
- **`item`:** `Sprite` com o PNG `assets/itens/<item_id>.png` (mesmo caminho do ícone do inventário, `_assetURL`); sem PNG → sprite de canvas com o emoji do item (como `build3DCorpse`). Escala ~0,35; `material.rotation` gira `itemSpinPerSec` voltas/s.

Materiais **próprios** do projétil (nunca clones de peão; nada de `_sceneMats`); objeto de cena independente (não filho do peão); geometria+material descartados em `_projetilDispose3D`.

### 5.3 Trajetória

Parábola vertical entre o centro de `from` (y = `launchY` 0,45) e o centro de `to` (y = `landY` 0,35); altura do arco por tipo (`arc`: seta 0,25 + 0,04/casa, virote 0,08, lança 0,35, item 0,55). Meshes orientados pela tangente (`lookAt(pos + velocidade)`); sprites só giram. `from`/`to` vêm do `launch` (posições do `attack_feedback`), nunca de `userData.gridX`.

- **Acerto:** seta some com a reação (`hitLingerMs` 300); item "quebra" — `_spawnBurstParticles` na cor do elemento (`fogo`→laranja, `sagrado`→dourado, `ácido`→verde, senão cinza) e o sprite some.
- **Erro:** seta pousa 1 casa além, cravada ~35° no chão por `stickMs` (900) e desvanece; item fica caído `stickMs` e desvanece.
- **Fumble:** cai no chão a meio caminho, mesmo tratamento do erro.
- **Área:** frasco voa até a casa-alvo; na chegada, burst maior (`areaBurst.base + areaBurst.perRadius × raio`) + anel fino no chão (`TorusGeometry`, `AdditiveBlending`, como o anel de derrota) expandindo e desvanecendo em 400 ms.

### 5.4 Portão dos números de área

`_projetilFeedbackStartAt(entry)` — generalização do `_bolaFogoFeedbackStartAt`: para cada `anim` de área em voo, se `entry.pos` está a ≤ `area_raio` (Chebyshev) do `to`, devolve o `impactAt` (o maior, se houver mais de um). O diff de HP consulta os dois portões (bola de fogo e projétil) e usa o mais tardio. Os saves rolam durante o voo.

## 6. Configuração (`VC.feedback.combat.scene.projectile`)

```js
projectile: {
  enabled: true,
  msPerTile: { arrow: 55, bolt: 45, spear: 75, item: 90 },
  travelMinMs: 220, travelMaxMs: 900,
  arc: { arrow: 0.25, arrowPerTile: 0.04, bolt: 0.08, spear: 0.35, item: 0.55 },
  launchY: 0.45, landY: 0.35,
  missOvershootTiles: 1,
  fumbleFraction: 0.5,
  stickMs: 900, hitLingerMs: 300,
  itemSpinPerSec: 2.5,
  areaBurst: { base: 18, perRadius: 8 },
}
```

- `travelMs` passa pela `duration` injetada (`fast` = 55%; `instant` ≈ 0 → o `launch` é emitido mas o `game.js` não cria voo quando `travelMs < 20`, e o impacto sai imediato).
- `projectile.enabled=false`: o servidor continua mandando o campo; o cliente o ignora (`configure` não repassa `projectile` à cena) → cena idêntica à de hoje.
- Sem tratamento extra de `prefers-reduced-motion`; sem i18n; sem mudança no editor (o `projectile` da ficha de monstro é opcional e só lido pelo servidor).

## 7. Testes

- **Servidor — `tools/test_projeteis.py`:** `_projetil_de` nos 4 casos de herói (arco→arrow, besta→bolt, chicote→None, arma do editor `ammo:"virotes"`→bolt) e nos 3 de monstro (`range≥2` perfurante→arrow, ficha com `projectile:"bolt"`→bolt, não-perfurante→None); `handle_throw_item` emite `start`+`result` nos dois modos (`ataque_alvo` com `hit` do d20 real; `area` com `target_pos`, `target_id=None`, `sem_dado`, `area_raio`); o ataque do kobold lanceiro sai com `kind:'spear'`; os payloads existentes não perdem campo.
- **Módulo — `tools/test_combat_scene.js`:** `launch` emitido na entrada de `GOLPE` com `hit/fumble/travelMs/from/to` corretos (erro estende `to` 1 casa; fumble encurta); `impactAt = launchAt + travelMs`; `sem_dado` pula `ESPERANDO_DADO` e não consome d20; área sem `targetKey` emite `impact{area:true}` e `pendingFor` não a devolve; `instant` → `travelMs≈0`; sem `projectile` → os 204 checks atuais intocados.
- **Estático (seção `[33]`):** `game.js` tem `_projetilBuild3D`/`_projetilUpdate3D`/`_projetilDispose3D`; o `tick` chama o update; `dispose3D` limpa `_projeteis`; o diff de HP consulta `_projetilFeedbackStartAt`.
- **Navegador (obrigatória):** herói com arco (comprar na cidade se o loadout não tiver) e goblin arqueiro; acerto com a flecha voando e o número na chegada; erro passando reto e cravando; frasco de óleo quebrando no alvo; bomba de área com anel e números atrasados; modo `instant`. Gravar a linha do tempo (`_scenes[].phase` + posição do projétil a cada 50 ms), não só screenshot.

## 8. Riscos e decisões registradas

- **Dado roubado por cena `sem_dado`:** a área não espera d20, mas os saves rolam d20 durante o voo — `dieSettled` ignora cenas `sem_dado`, senão a próxima cena normal perderia o dado.
- **Duas cenas de projétil do mesmo atacante** (Fúria com arco): a fila da frente A já serializa; o 2º voo só sai depois do `FIM` do 1º.
- **PNG ausente** (item do editor sem arte): sprite de emoji em canvas, nunca um sprite vazio.
- **`travelMs` e o `instant`:** é a única duração da cena que muda de fase a fase; passa pela `duration` como as demais animações, ao contrário dos timeouts (lição da frente A).
