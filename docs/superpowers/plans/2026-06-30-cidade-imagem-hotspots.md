# Cidade por imagem com hotspots — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a cena 3D da cidade por uma imagem ilustrada ("Alva e Luz") com hotspots clicáveis que abrem as lojas existentes; a entrada da masmorra vira "Ir para a aventura" no portão.

**Architecture:** Mudança só de renderização no cliente. Uma constante `CITY_MODE` escolhe entre o novo overlay em DOM (`initCityImage`) e a cena 3D atual (`initCity3D`, preservada como fallback). Hotspots são `<button>` posicionados em % sobre a imagem e chamam os handlers de loja/masmorra que já existem. Nada muda em `server.py` nem em `gameState.js`.

**Tech Stack:** Vanilla JS + DOM/CSS no `game.js`/`game.css`. Imagem estática servida por `assets/`. Sem framework, sem bundler, sem test runner JS (verificação é in-app + os testes Python de `tools/` continuam passando intactos).

**Spec:** `docs/superpowers/specs/2026-06-30-cidade-imagem-hotspots-design.md`

---

## Notas de verificação

Não há test runner JS neste projeto. A verificação de cada tarefa visual é **rodar o app e olhar**:

```bash
python server.py      # serve página + WS na porta 8765
# abrir http://localhost:8765/index.html
# criar sala → escolher classe → start → cair na cidade (screen-city)
```

Onde houver ferramenta de preview disponível, usar `preview_start` → `preview_snapshot`/`preview_screenshot` para confirmar. Os testes Python existentes (`python -m pytest tools/` ou os scripts individuais) **não tocam** nesta área; rodá-los só garante que nada de servidor quebrou (não deve, pois `server.py` não muda).

---

## File Structure

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `assets/city/alva_e_luz.jpg` | Renomear de `.png` | Imagem-base da cidade (é JPEG de fato) |
| `game.js` | Modificar | `CITY_MODE`, `_CTY_BLDGS` (coords), `initCityImage`/`destroyCityImage`, branch de mount/unmount, rótulo do botão |
| `game.css` | Modificar | Palco 3:2 responsivo, hotspots, brilho hero, vida sutil, mobile |

---

## Task 1: Backup de segurança + corrigir formato da imagem

**Files:**
- Renomear: `assets/city/alva_e_luz.png` → `assets/city/alva_e_luz.jpg`

- [ ] **Step 1: Commit de segurança do estado atual (rollback)**

A árvore tem WIP não relacionado; o backup cobre o repo todo para poder voltar.

```bash
git add -A
git commit -m "chore: snapshot antes da cidade por imagem (rollback point)"
```

Expected: um commit criado. Anote o hash (`git rev-parse HEAD`) — é o ponto de retorno.

- [ ] **Step 2: Renomear a imagem para a extensão real (JPEG)**

```bash
git mv assets/city/alva_e_luz.png assets/city/alva_e_luz.jpg
```

(Se `git mv` reclamar que o arquivo não está rastreado, use `mv assets/city/alva_e_luz.png assets/city/alva_e_luz.jpg`.)

- [ ] **Step 3: Confirmar dimensões/format**

Run:
```bash
python -c "from PIL import Image; im=Image.open('assets/city/alva_e_luz.jpg'); print(im.format, im.size)"
```
Expected: `JPEG (1536, 1024)` (proporção 3:2).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore(city): renomeia alva_e_luz para .jpg (formato real)"
```

---

## Task 2: `CITY_MODE` + dados de hotspot + branch de mount/unmount

**Files:**
- Modify: `game.js` (bloco de cidade a partir da linha ~422; array `_CTY_BLDGS` ~427-440; mount ~1140; unmount ~19574)

- [ ] **Step 1: Adicionar a constante de modo**

Logo acima de `let _city3 = null;` (linha ~424) inserir:

```javascript
// 'image' = cidade ilustrada com hotspots (padrão). '3d' = cena Three.js antiga (fallback).
const CITY_MODE = 'image';
let _cityImg = null;   // estado do overlay de imagem (espelha _city3)
```

- [ ] **Step 2: Acrescentar coords de hotspot ao `_CTY_BLDGS`**

Adicionar `hx`,`hy` (posição em % na imagem) e `hero` a cada item. Valores iniciais (calibrados na Task 5). Editar o array existente para incluir os campos — exemplo do item templo:

```javascript
  {id:'templo',   name:'Templo',             emoji:'⛪',action:'Bênçãos e curas divinas',
   x:0,  z:-7.5, w:4.0,d:3.2,wallH:3.0,roofH:2.2, wallHex:0x283088,roofHex:0x181858,winHex:0x88aaff,
   hx:63, hy:42, hero:true},
```

Valores iniciais para os 6 (ajuste fino na Task 5):

```
taverna : hx:20, hy:64, hero:false
templo  : hx:63, hy:42, hero:true
ferreiro: hx:74, hy:58, hero:false
guilda  : hx:46, hy:24, hero:false
mercador: hx:34, hy:46, hero:true
dungeon : hx:30, hy:88, hero:true
```

(`mercador` é o id do mesh; o clique já mapeia para a loja `mercado` via `MAPA_IDS_LOJA`.)

- [ ] **Step 3: Branch no mount (linha ~1140)**

Trocar:

```javascript
  // Init 3D city scene on first arrival
  if(!_city3&&window.THREE) initCity3D();
```

por:

```javascript
  // Monta a cidade conforme o modo (imagem por padrão; 3D como fallback).
  if(CITY_MODE==='image'){ if(!_cityImg) initCityImage(); }
  else if(!_city3&&window.THREE){ initCity3D(); }
```

- [ ] **Step 4: Branch no unmount (linha ~19574)**

Trocar a linha `destroyCity3D();` por:

```javascript
  if(CITY_MODE==='image') destroyCityImage(); else destroyCity3D();
```

- [ ] **Step 5: Verificar que não quebrou o carregamento**

Abrir o app e entrar na cidade. Como `initCityImage` ainda não existe, espera-se um erro no console apontando `initCityImage is not defined` — isso **confirma** que o branch está ativo. Prosseguir para a Task 3 (que define a função). Não commitar ainda (código incompleto).

---

## Task 3: `initCityImage()` / `destroyCityImage()` — palco, imagem e hotspots

**Files:**
- Modify: `game.js` (adicionar as funções logo após `destroyCity3D()`, ~linha 999+)

- [ ] **Step 1: Implementar as funções**

Inserir após o fim de `destroyCity3D()`:

```javascript
// ■  CITY SCREEN (modo imagem) — overlay em DOM sobre #screen-city

function initCityImage(){
  if(_cityImg) return;
  const host = document.getElementById('screen-city');
  if(!host) return;

  const stage = document.createElement('div');
  stage.id = 'city-stage';

  const img = document.createElement('img');
  img.id = 'city-img';
  img.src = 'assets/city/alva_e_luz.jpg?v=' + (window.ASSET_VER || '1');
  img.alt = 'Cidade de Alva e Luz';
  img.draggable = false;
  stage.appendChild(img);

  // Camada de vida (preenchida na Task 7) — não captura cliques.
  const life = document.createElement('div');
  life.id = 'city-life';
  stage.appendChild(life);

  // Selo com o nome da cidade (no lugar do badge de dia/noite).
  const seal = document.createElement('div');
  seal.id = 'city-seal';
  seal.textContent = 'Alva e Luz';
  stage.appendChild(seal);

  const hotWrap = document.createElement('div');
  hotWrap.id = 'city-hotspots';
  for(const bd of _CTY_BLDGS){
    if(bd.hx == null) continue;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'city-hotspot' + (bd.hero ? ' hero' : '') + (bd.id==='dungeon' ? ' dungeon' : '');
    btn.style.left = bd.hx + '%';
    btn.style.top  = bd.hy + '%';
    btn.setAttribute('aria-label', bd.name + ' — ' + bd.action);
    btn.title = bd.name + ' — ' + bd.action;
    const label = bd.id==='dungeon' ? 'Ir para a aventura' : bd.name;
    btn.innerHTML =
      '<span class="ch-glow" aria-hidden="true"></span>' +
      '<span class="ch-pin"><span class="ch-emoji">' + bd.emoji + '</span>' +
      '<span class="ch-name">' + label + '</span></span>';
    btn.addEventListener('click', () => _cityHotspotClick(bd.id));
    hotWrap.appendChild(btn);
  }
  stage.appendChild(hotWrap);
  host.appendChild(stage);

  // Esconde o badge de dia/noite (sem sentido no modo imagem).
  const tb = document.getElementById('city-time-badge');
  if(tb) tb.style.display = 'none';

  _cityImg = { stage, img, life, hotWrap, raf:0 };
}

function _cityHotspotClick(id){
  if(id === 'dungeon'){ triggerDungeonEntrance(); return; }
  if(id === 'guilda'){ toast('⚔ Guilda dos Heróis — Missões em breve!','var(--gold)'); return; }
  openShop(MAPA_IDS_LOJA[id] || id);
}

function destroyCityImage(){
  if(_cityImg){
    if(_cityImg.raf) cancelAnimationFrame(_cityImg.raf);
    if(_cityImg.stage && _cityImg.stage.parentNode) _cityImg.stage.parentNode.removeChild(_cityImg.stage);
    _cityImg = null;
  }
  const tb = document.getElementById('city-time-badge');
  if(tb) tb.style.display = '';
}
```

Observações:
- `MAPA_IDS_LOJA`, `openShop`, `triggerDungeonEntrance`, `toast` e `_CTY_BLDGS` já existem no arquivo — esta função apenas os reusa.
- `window.ASSET_VER` pode não existir; o `|| '1'` cobre isso (cache-buster mínimo). Se o projeto já tem uma variável global de versão de asset, use-a no lugar.
- O portão é clicável por todos (igual ao portal 3D de hoje); o servidor é autoritativo sobre quem pode entrar — comportamento idêntico ao atual.

- [ ] **Step 2: Verificar clique funcional (sem CSS ainda)**

Abrir o app, entrar na cidade. Os botões aparecerão sem estilo (empilhados/sobre a imagem crua), mas:
- Clicar no hotspot do templo → abre o modal de loja do templo.
- Clicar no do mercado → abre a loja do mercado.
- Clicar no do portão → dispara a transição de entrada na masmorra.
- Console sem erros de `undefined`.

Use `preview_snapshot` (se disponível) para confirmar a presença dos botões `.city-hotspot`.

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(city): modo imagem com hotspots clicaveis (sem estilo)"
```

---

## Task 4: CSS — palco 3:2 responsivo, hotspots, brilho hero, hover

**Files:**
- Modify: `game.css` (adicionar bloco no fim, ou perto das regras de `#screen-city`)

- [ ] **Step 1: Adicionar o CSS do palco e da imagem**

```css
/* ===== Cidade por imagem (CITY_MODE='image') ===== */
#screen-city #city-stage{
  position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  background:#0b0a12;                 /* moldura escura na sobra (letterbox vira quadro) */
  overflow:hidden;
}
#city-img{
  width:auto; height:auto;
  max-width:100%; max-height:100%;
  aspect-ratio:3 / 2;                 /* casa com 1536x1024 */
  object-fit:cover;
  user-select:none; -webkit-user-drag:none;
  box-shadow:0 0 60px 10px rgba(0,0,0,.6) inset;
}
/* Camada de hotspots ocupa exatamente a caixa da imagem renderizada. */
#city-hotspots{
  position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
  width:min(100%, calc(100vh * 3 / 2));
  aspect-ratio:3 / 2;
  pointer-events:none;               /* só os botões capturam clique */
}
```

Nota de robustez: ancorar `#city-hotspots` na mesma caixa renderizada da imagem é o ponto crítico do responsivo. A regra acima reproduz o "contain" de uma imagem 3:2 dentro do palco. Se na verificação os hotspots não casarem com a imagem em alguma proporção de tela, trocar a abordagem para envolver `<img>` + `#city-hotspots` num wrapper `#city-frame` com `aspect-ratio:3/2; max-width/max-height` e posicionar ambos por dentro dele (frame dita a caixa; img e hotspots usam `inset:0`). Preferir o wrapper se houver qualquer desencontro — é mais à prova de erro.

- [ ] **Step 2: Adicionar o CSS dos hotspots e do brilho hero**

```css
.city-hotspot{
  position:absolute; transform:translate(-50%,-50%);
  pointer-events:auto; cursor:pointer;
  background:none; border:none; padding:0; margin:0;
  display:flex; align-items:center; justify-content:center;
}
.city-hotspot .ch-pin{
  display:inline-flex; align-items:center; gap:6px;
  padding:5px 11px; border-radius:18px;
  background:rgba(18,14,9,.72); color:#f0e6d2;
  border:1px solid rgba(240,230,210,.4);
  font-size:13px; line-height:1; white-space:nowrap;
  transition:transform .15s ease, box-shadow .15s ease, background .15s ease;
}
.city-hotspot .ch-emoji{ font-size:15px; }
/* Holofote no chão sob o marcador (aparece no hover/foco). */
.city-hotspot .ch-glow{
  position:absolute; top:50%; left:50%; width:120px; height:60px;
  transform:translate(-50%,-30%);
  border-radius:50%;
  background:radial-gradient(closest-side, rgba(255,225,150,.55), rgba(255,225,150,0));
  opacity:0; transition:opacity .18s ease; pointer-events:none;
}
.city-hotspot:hover .ch-pin,
.city-hotspot:focus-visible .ch-pin{
  transform:scale(1.12);
  background:rgba(58,44,18,.92); color:#ffe79a;
  border-color:#ffe79a; box-shadow:0 0 14px 3px rgba(255,225,150,.5);
}
.city-hotspot:hover .ch-glow,
.city-hotspot:focus-visible .ch-glow{ opacity:1; }

/* Prédios 'hero': rótulo só no hover (o prédio se reconhece sozinho). */
.city-hotspot.hero .ch-name{
  max-width:0; overflow:hidden; opacity:0;
  transition:max-width .2s ease, opacity .2s ease, margin .2s ease;
}
.city-hotspot.hero:hover .ch-name,
.city-hotspot.hero:focus-visible .ch-name{ max-width:140px; opacity:1; }

/* Brilho de silhueta dos hero: glow grande sobre o prédio, no hover. */
.city-hotspot.hero .ch-glow{
  width:160px; height:130px; transform:translate(-50%,-50%);
  background:radial-gradient(closest-side, rgba(255,225,150,.5), rgba(255,225,150,0));
}
.city-hotspot.dungeon .ch-pin{
  background:rgba(90,20,20,.8); color:#ffd2d2; border-color:#e24b4a;
}
.city-hotspot.dungeon:hover .ch-pin,
.city-hotspot.dungeon:focus-visible .ch-pin{
  background:rgba(120,26,26,.95); color:#fff; border-color:#ff6a6a;
  box-shadow:0 0 16px 4px rgba(226,75,74,.6);
}

/* Selo "Alva e Luz" no lugar do badge de dia/noite. */
#city-seal{
  position:absolute; top:14px; left:50%; transform:translateX(-50%);
  padding:5px 16px; border-radius:6px;
  background:rgba(20,16,10,.6); color:#e8dcc0;
  border:1px solid rgba(232,220,192,.35);
  font-family:'Cinzel',serif; font-size:15px; letter-spacing:.5px;
  pointer-events:none;
}
```

(Se a fonte `Cinzel`/serif não existir no projeto, usar a família serif já usada nos títulos do jogo; checar `game.css` por uma `font-family` de cabeçalho existente.)

- [ ] **Step 3: Verificar visual**

Abrir a cidade. Esperado:
- Imagem enquadrada e centralizada, com moldura escura na sobra.
- 6 marcadores; taverna/ferraria/guilda com rótulo sempre; templo/mercado/portão só ícone até o hover.
- Hover acende o marcador + holofote; nos hero, aparece o glow grande + rótulo.
- Clique continua abrindo as lojas certas.

`preview_screenshot` para registrar.

- [ ] **Step 4: Commit**

```bash
git add game.css
git commit -m "style(city): palco 3:2 responsivo, marcadores e brilho hero"
```

---

## Task 5: Calibrar coords dos hotspots e dos brilhos hero

**Files:**
- Modify: `game.js` (`_CTY_BLDGS` `hx`/`hy`)
- Modify: `game.css` (tamanho/offset de `.ch-glow` por prédio, se necessário)

- [ ] **Step 1: Abrir a cidade e comparar marcadores com a imagem**

Olhando a imagem real (`assets/city/alva_e_luz.jpg`):
- **Templo** = grande domo dourado à direita do centro.
- **Mercado** = aglomerado de tendas coloridas (telhados coloridos) à esquerda do domo.
- **Portão** = abertura na muralha, base/esquerda da imagem (a estrada que sai).
- **Guilda/Taverna/Ferraria** = posições plausíveis sobre quarteirões; manter espalhadas e legíveis, sem sobrepor.

- [ ] **Step 2: Ajustar `hx`/`hy`**

Editar os valores no `_CTY_BLDGS` até cada marcador pousar sobre o prédio/área correta. Iterar visualmente (recarregar a cada ajuste). Critério: cada marcador claramente sobre seu alvo; nenhum marcador encavalado em outro.

- [ ] **Step 3: Ajustar o brilho hero**

Conferir que o `.ch-glow` dos hero cobre o prédio (não fica deslocado). Se um prédio (ex.: o domo) for maior/menor que o glow padrão, criar uma regra específica por id, ex.:

```css
.city-hotspot[aria-label^="Templo"] .ch-glow{ width:200px; height:160px; }
```

(ou adicionar uma classe por id ao botão na Task 3 se preferir seletor mais limpo).

- [ ] **Step 4: Verificar em duas proporções de tela**

Redimensionar a janela (largo e estreito) — `preview_resize` se disponível. Os marcadores devem continuar sobre os prédios (provando a ancoragem da Task 4). Se desencontrarem, aplicar o fallback do wrapper `#city-frame` descrito na Task 4 Step 1.

- [ ] **Step 5: Commit**

```bash
git add game.js game.css
git commit -m "fix(city): calibra posicao dos hotspots e brilhos sobre a imagem"
```

---

## Task 6: "Ir para a aventura" na barra + gating preservado

**Files:**
- Modify: `game.js` (linha ~1129, texto do botão `#btn-enter-dungeon`)

- [ ] **Step 1: Trocar o rótulo do botão da barra**

Na linha ~1129, trocar:

```javascript
    btnD.textContent = msg.campaign ? `▶ Entrar na fase ${msg.campaign.phase}` : '⚔ Entrar na Masmorra';
```

por:

```javascript
    btnD.textContent = msg.campaign ? `▶ Ir para a aventura — Fase ${msg.campaign.phase}` : '▶ Ir para a aventura';
```

O gating (host-only, `display` da barra, hint) **permanece igual** — só o texto muda. O hotspot do portão na imagem continua disparando `triggerDungeonEntrance()` (server autoritativo).

- [ ] **Step 2: Verificar**

- Como host: barra inferior mostra "▶ Ir para a aventura"; clicar nela ou no portão entra.
- Como não-host: barra escondida (como antes); hint "Aguardando o anfitrião…".

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(city): renomeia entrada da masmorra para 'Ir para a aventura'"
```

---

## Task 7: Camada de vida sutil (CSS-first) + reduced-motion

**Files:**
- Modify: `game.js` (`initCityImage` — popular `#city-life` com nós de glow)
- Modify: `game.css` (animações)

- [ ] **Step 1: Popular a camada de vida no `initCityImage`**

Dentro de `initCityImage`, após criar `life` e antes de `stage.appendChild(life)` já feito, preencher com glows de tocha/janela e a névoa. Adicionar:

```javascript
  // Vida sutil: névoa nas bordas + brilhos piscando (tochas/janelas).
  life.innerHTML =
    '<div class="city-fog"></div>' +
    '<div class="city-flicker" style="left:31%;top:46%"></div>' +
    '<div class="city-flicker" style="left:34%;top:51%;animation-delay:.7s"></div>' +
    '<div class="city-flicker" style="left:74%;top:58%;animation-delay:1.1s"></div>' +
    '<div class="city-flicker" style="left:20%;top:64%;animation-delay:.4s"></div>' +
    '<div class="city-gateglow" style="left:30%;top:88%"></div>';
```

(As coords espelham aproximadamente as dos hotspots; ajustar junto na calibração se quiser.)

- [ ] **Step 2: Adicionar as animações no CSS**

```css
#city-life{ position:absolute; inset:0; pointer-events:none; }
.city-fog{
  position:absolute; inset:-10%;
  background:
    radial-gradient(60% 40% at 0% 50%, rgba(200,205,220,.18), transparent 70%),
    radial-gradient(60% 40% at 100% 50%, rgba(200,205,220,.16), transparent 70%);
  animation:cityFog 18s ease-in-out infinite alternate;
}
@keyframes cityFog{ from{transform:translateX(-2%);} to{transform:translateX(2%);} }
.city-flicker{
  position:absolute; width:46px; height:46px; transform:translate(-50%,-50%);
  border-radius:50%;
  background:radial-gradient(closest-side, rgba(255,170,60,.5), transparent 70%);
  animation:cityFlicker 2.6s ease-in-out infinite;
}
@keyframes cityFlicker{ 0%,100%{opacity:.35;} 45%{opacity:.85;} 60%{opacity:.5;} }
.city-gateglow{
  position:absolute; width:90px; height:90px; transform:translate(-50%,-50%);
  border-radius:50%;
  background:radial-gradient(closest-side, rgba(226,75,74,.45), transparent 70%);
  animation:cityGate 2.2s ease-in-out infinite;
}
@keyframes cityGate{ 0%,100%{opacity:.4; transform:translate(-50%,-50%) scale(.9);}
                     50%{opacity:.8; transform:translate(-50%,-50%) scale(1.1);} }

@media (prefers-reduced-motion: reduce){
  .city-fog, .city-flicker, .city-gateglow{ animation:none; }
}
```

- [ ] **Step 3: Verificar**

Cidade tem agora névoa deslizando, brilhos piscando e o portão pulsando. Em sistema com "reduzir movimento" ativo, tudo fica estático. Confirmar que a camada não captura cliques (hotspots ainda clicáveis).

- [ ] **Step 4: Commit**

```bash
git add game.js game.css
git commit -m "feat(city): camada de vida sutil (nevoa, flicker, pulsar do portao)"
```

---

## Task 8: Pass de mobile + verificação final

**Files:**
- Modify: `game.css` (media query mobile)

- [ ] **Step 1: Garantir a barra de aventura no mobile**

A barra `#city-dungeon-bar` já existe e é host-only. Para o portão no retrato ser pequeno demais, garantir que a barra inferior fique acessível. Adicionar:

```css
@media (max-width:820px){
  .city-hotspot .ch-pin{ font-size:14px; padding:6px 12px; }   /* alvo de toque maior */
  #city-seal{ font-size:13px; top:8px; }
}
```

(O `#city-dungeon-bar` já aparece para o host independentemente do tamanho; nenhuma mudança de gating necessária. Se na verificação ele estiver coberto pela imagem, garantir `z-index` acima de `#city-stage` — o stage usa o fluxo normal; checar a ordem de `z-index` em `game.css` e elevar a barra se preciso.)

- [ ] **Step 2: Verificação final (desktop + mobile)**

`preview_resize` para ~390px de largura (retrato) e tela larga. Conferir o checklist do spec:
- Imagem enquadrada sem cortar portão/névoa nas duas larguras.
- 6 hotspots clicáveis abrindo loja/guilda/aventura.
- Hover/foco: marcador + holofote; hero com brilho.
- Portão = "Ir para a aventura"; barra inferior acessível como host no mobile.
- Vida sutil visível; some com reduced-motion.
- Barra de heróis (topo) e ficha da cidade (clicar num herói) ainda funcionam.
- Trocar temporariamente `CITY_MODE='3d'` → a cena antiga volta sem erro; reverter para `'image'`.

- [ ] **Step 3: Rodar os testes Python (sanidade — nada de servidor mudou)**

Run:
```bash
python -m pytest tools/ -q
```
Expected: passam como antes (esta mudança não toca servidor). Se algum já falhava no baseline por motivo não relacionado, ignorar — o critério é "não introduziu nova falha".

- [ ] **Step 4: Commit final**

```bash
git add game.css
git commit -m "polish(city): ajustes de mobile e verificacao final"
```

---

## Self-review (cobertura do spec)

- Manter 6 pontos → Task 2/3 (loop por `_CTY_BLDGS`, todos com hotspot). ✔
- Img 2 = cidade, img 1 fora → só `alva_e_luz.jpg` é referenciada. ✔
- Destaque híbrido (marcador + brilho hero) → Task 4 (`.ch-glow`, `.hero`). ✔
- Vida sutil + reduced-motion → Task 7. ✔
- PC + celular (palco travado + barra inferior) → Task 4/8. ✔
- "Ir para a aventura" no portão + barra → Task 3 (label) / Task 6 (botão). ✔
- Gating preservado → Task 6 Step 1 (só texto muda). ✔
- Selo no lugar do badge de tempo → Task 3/4. ✔
- `CITY_MODE` rollback + 3D preservado → Task 2; verificado na Task 8. ✔
- Sem mudança em `server.py`/`gameState.js` → nenhuma task os toca. ✔
- Formato JPEG corrigido → Task 1. ✔
