# Sons e efeitos sonoros — design

**Data:** 2026-09-23
**Status:** aprovado em brainstorming, aguardando plano de implementação

## Objetivo

Aumentar a imersão pelo som, sem música de masmorra. Hoje todo efeito é sintetizado
pela Web Audio API (≈40 sons de magia, dados, passos, baú, armadilha) e há eventos
importantes sem som nenhum: porta, loot, subir de nível, início do turno, criaturas,
cliques e erro/esquiva. O golpe corpo a corpo só tem duas variações (`damage`/`critical`).
O canal de volume "ambiente" existe no painel de áudio e nada toca nele.

## Decisões tomadas

| Tema | Decisão |
|---|---|
| Origem dos sons | **Híbrido**: amostras gravadas para sons "físicos"; as magias continuam sintetizadas |
| Fonte dos arquivos | Pacotes **CC0** indicados pelo Claude; cada download só com aprovação explícita |
| Escopo | Combate físico, exploração e loot, criaturas, interface e ritmo do turno |
| Ambiente | Um loop por preset `ambiente` da masmorra |
| Névoa | O que não está visível soa **abafado, mais baixo e sem panorâmica** |

## Arquitetura

### `src/soundBank.js` (novo, puro)

Sem DOM, sem `window`, sem Web Audio, no padrão de `src/combatScene.js` e testável em node.
Exporta `window.SoundBank` no navegador e `module.exports` no node.

- **Catálogo** `SFX`: `evento → { arquivos: [...], volume, pitchJitter, volJitter, canal, intervaloMs }`.
  O canal é `efeitos` ou `ambiente`. Os caminhos são relativos a `assets/sfx/`.
- **Famílias de criatura** `FAMILIA_CRIATURA`: `tipo de monstro → humanoide | fera | morto_vivo | reptil_inseto | grande`.
  Espécie ausente no mapa: `grande` se o `size` ocupar mais de 1×1, senão `humanoide`.
- **`audibilidade(pos, estado, meuHeroi)`** → `{ ganho, abafado, pan }`:
  - sem `pos` (som de interface ou do próprio herói): ganho 1, sem abafar, pan 0;
  - casa **visível**: ganho de 1 caindo linearmente até 0,4 a 12 casas; `pan` pelo eixo X relativo ao herói, limitado a ±0,6;
  - casa **fora da visão** (névoa ou atrás de porta fechada): ganho 0,35, `abafado: true`, **pan 0** (não revela o lado);
  - sem herói (mestre, espectador): ganho 1 no visível; o mestre vê o mapa inteiro, então nada sai abafado para ele.
- **`escolherVariante(evento, ultimo)`**: sorteia entre os arquivos sem repetir o último.
- **Controle de avalanche** (`podeTocar(evento, agora, tocando)`): respeita o `intervaloMs` por evento e o teto de
  **8 sons simultâneos**; acima do teto, o som novo de menor ganho é descartado.

A visibilidade de uma casa é lida do mesmo estado que o render usa (`explored`/`visible`
do `game_state`); o módulo recebe esses dados por parâmetro e não os calcula.

### `game.js`

- **`sfx(evento, opts)`**: ponto único de reprodução. `opts = { pos, familia, forcar }`.
  Consulta `SoundBank`, carrega o arquivo sob demanda (`fetch` + `decodeAudioData`, cache
  por caminho, uma requisição em voo por arquivo) e toca via `AudioBufferSourceNode`
  → `BiquadFilter` passa-baixa (só quando `abafado`, corte ~900 Hz) → `StereoPanner` → canal.
- **Canal de efeitos**: o `_sfxBus()` existente. **Canal de ambiente**: um `_ambienceBus()`
  novo, no mesmo molde, ligado ao `_ambienceVol` que o painel de áudio já salva.
- **Recuo para síntese**: se o evento não tem arquivo, ou o arquivo falhou ao carregar, toca
  a função sintetizada correspondente (quando existir) — nada fica mudo na transição.
- **Ambiente**: `_ambienciaTocar(preset)` com crossfade de 2 s; ligado ao entrar na masmorra
  (`enterDungeon`) e desligado ao voltar à cidade. O preset vem do `ambiente` da masmorra;
  ausente → `masmorra`. O loop usa `loop = true` no `AudioBufferSourceNode`.

### `server.py`

Um único acréscimo: o campo opcional **`impacto`** no `attack_feedback` de fase `start`,
com um de `cortante | perfurante | contundente | natural`. Helper module-level
`_impacto_de(defn, monstro=False)` ao lado de `_projetil_de`:

- herói: a `categoria` da arma equipada (`cortante`/`perfurante`/`contundente`);
- monstro: `natural` para mordida, garra, ferrão, cauda e afins (pelo nome ou pelos
  `damage_types` do ataque); arma de monstro com `categoria` usa a categoria;
- sem informação: o campo é **omitido** (o payload fica byte-idêntico ao de hoje).

Nenhuma mensagem nova e nenhum outro campo.

## Eventos e gatilhos

| Grupo | Evento (`sfx`) | Gatilho no cliente | Quem ouve |
|---|---|---|---|
| Combate | `golpe_<impacto>` (+ `golpe_critico` sobreposto) | comando `impact` da `CombatScene`, no instante do golpe | todos, com a regra da névoa |
| Combate | `golpe_erro` | `impact` com erro | todos |
| Combate | `escudo_bloqueio` | `impact` com erro e alvo com escudo em `gear` | todos |
| Combate | `dor_heroi` / `dor_criatura` | hand-off de dano da `CombatScene` | todos |
| Exploração | `porta_abre` | casa `DOOR` que deixou de estar fechada entre dois `game_state` | todos |
| Exploração | `moedas` | o **seu** ouro subiu | só você |
| Exploração | `item_pegar` | a **sua** bolsa cresceu | só você |
| Exploração | `equipar` | um slot do **seu** `gear` mudou | só você |
| Exploração | `beber` | poção consumida por você | só você |
| Exploração | `escada` | o **seu** `fora_masmorra` mudou | só você |
| Criaturas | `rugido_<familia>` | 1ª vez que cada monstro fica visível para você (conjunto de ids já ouvidos, zerado a cada masmorra nova) | só você |
| Criaturas | `morte_<familia>` | fluxo de morte existente (`_mortesVisuaisPendentes`), quando o peão tomba | todos |
| Interface | `sua_vez` | o turno passou a ser seu | só você |
| Interface | `nivel` | o **seu** `level` subiu | só você |
| Interface | `objetivo` | `mission_complete_pending` ligou | todos |
| Interface | `clique` / `painel` | abrir/fechar painéis e botões principais | só você |
| Interface | `recusa` | mensagem `error` do servidor | só você |
| Ambiente | `amb_masmorra` / `amb_penumbra` / `amb_ar_livre` | entrar na masmorra | só você |

Volumes relativos no catálogo: interface bem abaixo do combate; `sua_vez` e `nivel` acima da interface.

## Arquivos

- Pasta `assets/sfx/<grupo>/` (`combate`, `exploracao`, `criaturas`, `interface`, `ambiente`).
- Preparação com **ffmpeg** (disponível na máquina): corte de silêncio, normalização de loudness,
  `.ogg` mono para efeitos e estéreo para ambiente, loop sem clique no ponto de emenda.
- Orçamento: **< 3 MB** de efeitos; ambiente ≈ 1,5 MB por loop.
- Só os arquivos usados entram no repositório (não os ZIPs), mais `assets/sfx/LICENCAS.md`
  com origem e licença de cada arquivo. O servidor já serve `assets/`: sem mudança na allow-list.

Pacotes candidatos (licença a confirmar arquivo por arquivo antes de usar):
- [Kenney — RPG Audio](https://kenney.nl/assets/rpg-audio) (CC0; foley, passos, armas)
- [OpenGameArt — 80 CC0 creature SFX](https://opengameart.org/content/80-cc0-creature-sfx)
- [OpenGameArt — Monster Sound Pack, Volume 1](https://opengameart.org/content/monster-sound-pack-volume-1)
- [OpenGameArt — Loopable Dungeon Ambience](https://opengameart.org/content/loopable-dungeon-ambience)
- Kenney — Impact Sounds / Interface Sounds (para golpes e interface; confirmar CC0)

## Testes

- **Node — `tools/test_sound_bank.js`:** `audibilidade` (visível perto, visível longe, névoa,
  atrás de porta, sem herói, mestre); névoa sempre com pan 0; variante sem repetição imediata;
  `intervaloMs`; teto de 8 simultâneos; família por tipo e recuo por tamanho.
- **Python — `tools/test_sons_impacto.py`:** `impacto` no `attack_feedback start` para arma
  cortante, perfurante e contundente, ataque natural de monstro e arma de monstro com categoria;
  sem categoria → campo ausente.
- **Consistência (no teste node):** todo arquivo do catálogo existe em `assets/sfx/`, e todo
  arquivo de `assets/sfx/` (exceto `LICENCAS.md`) é citado no catálogo.

## Verificação no navegador

Partida real com contador de disparos exposto só para depuração: porta, baú com moedas, subir
de nível, ataque com acerto e com erro, monstro avistado e morto, ambiente entrando e saindo.
Critério: cada evento dispara **uma vez**, no canal certo, com o ganho e o filtro esperados.
A avaliação de ouvido fica com o autor; o ajuste fino é trocar um arquivo ou um número do catálogo.

## Fora de escopo

- Sons presos a objetos (fogueira e fonte com volume pela distância).
- Refazer as magias sintetizadas.
- Música de masmorra.
- Tradução: sons não têm texto; o painel de áudio já existe e já está traduzido.
