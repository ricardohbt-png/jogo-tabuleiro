# Música de fundo dos menus (com crossfade) — Design

**Data:** 2026-06-22
**Branch:** feat/hud-paladino-richard (música é independente; pode ir em branch própria)

## Objetivo

Tocar música de fundo em loop nas duas telas de menu:

- **Tela de abertura** (`screen-connect`) — música A.
- **Tela de seleção de personagem** (`screen-class-select`) — música B.

Ao trocar da abertura para a seleção, fazer **crossfade suave de 3 s** entre as duas
faixas. Ao entrar no jogo de fato, a música de menu faz **fade-out de 3 s** e para.

## Decisões (confirmadas com o usuário)

| Tema | Decisão |
|---|---|
| Música da abertura | `WhatsApp Audio 2026-06-22 at 10.55.08.mpeg` (renomeado → `abertura.mp3`) |
| Música da seleção | Trilha de áudio de `WhatsApp Video 2026-06-22 at 11.01.00.mp4`, **extraída** para `selecao.mp3` |
| Volume | ~0,6 (igual à música de história) |
| Controle de mute | Botão flutuante 🔊/🔇, só nas duas telas de menu; mute por sessão (não persistido) |
| Crossfade abertura→seleção | 3 segundos |
| Quando parar | Fade-out de 3 s ao iniciar o jogo (`screen-game`); sem música de menu em jogo/cidade/fim |
| Início da música de abertura | Tenta tocar junto com a capa; se o browser bloquear (autoplay), começa no 1º clique/tecla, com a dica "Clique para começar" visível até começar |

## Restrição de plataforma (autoplay)

Browsers **proíbem** áudio com som antes da primeira interação do usuário. Não há
contorno. Portanto:

1. No carregamento, tenta-se `play()` na faixa de abertura.
2. Se o browser permitir (raro), toca imediatamente.
3. Se bloquear, a dica existente `#cover-hint` ("Clique para começar") permanece e a
   música começa no 1º clique/tecla — capturado pelo handler `dismiss` da capa
   ([game.js:9905](game.js:9905)) + um listener de gesto único de reserva.

## Arquitetura

Conforme `CLAUDE.md`: isto é **renderização/UI pura** (áudio atrelado a telas).
Tudo vive em `game.js`, seguindo o padrão já existente de `_storyAudioEl`.
**Sem mudanças em `server.py`** (qualquer coisa sob `assets/` já é servida via
`_STATIC_ROOTS`; mime `.mp3` → `audio/mpeg` já registrado). **Sem mudanças em
`gameState.js`** (que permanece sem referências a DOM/Audio).

### Assets

- Criar pasta `assets/music/`.
- `assets/music/abertura.mp3` — copiado/renomeado do `.mpeg` da abertura.
- `assets/music/selecao.mp3` — **extraído** do `.mp4` via ffmpeg (instalado localmente),
  apenas a trilha de áudio, codificada em MP3.

### Gerenciador de música de menu (novo código em `game.js`)

- Dois objetos `Audio`, `loop=true`, `volume` alvo ~0,6, `preload`.
- `crossfadeTo(track, 3000)` — rampa o volume da faixa atual 0,6→0 e da nova 0→0,6 ao
  longo de 3 s via `requestAnimationFrame`; ao fim, `pause()` na faixa que saiu.
- `fadeOutStop(3000)` — rampa a faixa atual →0 em 3 s e para (ao iniciar o jogo).
- Falha silenciosa se um arquivo não carregar (`.catch(()=>{})`), igual ao player de
  história — nunca quebra o jogo.
- Estado de mute (`_menuMuted`) aplicado ao volume-alvo das rampas.

### Integração com troca de telas

Hook em `showScreen(id)` ([game.js:256](game.js:256)):

- `id === 'screen-class-select'` → `crossfadeTo(selecao, 3000)`.
- `id === 'screen-game' | 'screen-city' | 'screen-end'` → `fadeOutStop(3000)`.

A tela de abertura (`screen-connect`) já nasce `active` no HTML (não passa por
`showScreen` no boot), então o **início** da faixa de abertura é tratado pela rotina de
autoplay/capa descrita acima, não pelo hook de `showScreen`.

### Controle de mute

Pequeno botão flutuante 🔊/🔇, fixo num canto, visível **apenas** em `screen-connect` e
`screen-class-select` (escondido nas demais). Alterna `_menuMuted` (escopo de sessão).

## Casos de borda

- Arquivo de faixa ausente / falha de decode → silêncio, sem erro fatal.
- Voltar à tela de abertura (ex.: após desconexão) → crossfade de volta para a abertura.
- Mute respeitado durante crossfades (rampas miram em 0 quando mutado).

## Verificação

Áudio de browser não tem teste unitário trivial. Plano:

1. Carregar a página via preview tools; conferir ausência de erros no console.
2. Confirmar que os `Audio` são criados e `play()` é chamado.
3. Confirmar que transições de tela disparam crossfade / fade-out.
4. Teste auditivo final feito pelo usuário (o harness não "ouve").

## Fora de escopo (YAGNI)

- Persistir mute entre sessões (não pedido).
- Música nas telas de cidade/loja/fim.
- Controle de volume granular (slider) — só mute on/off.
