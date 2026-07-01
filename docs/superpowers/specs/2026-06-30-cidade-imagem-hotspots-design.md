# Cidade por imagem com hotspots — Design

**Data:** 2026-06-30
**Branch atual:** feat/miniatura-png-objetos
**Tipo:** Mudança de renderização (cliente). Sem alteração de servidor nem de estado.

## Objetivo

Substituir a cena 3D procedural da cidade (`screen-city`) por uma **imagem
ilustrada** ("Alva e Luz", `assets/city/alva_e_luz.png`) com **pontos clicáveis
(hotspots)** sobre os prédios. Clicar no templo abre a loja do templo, no mercado
abre o mercado, etc. A entrada da masmorra passa a ficar no **portão da muralha**,
renomeada para **"Ir para a aventura"**. Objetivo final: cidade mais bonita,
funcional e clara.

## Decisões fechadas no brainstorm

| Tema | Decisão |
|---|---|
| Prédios/lojas | **Manter os 6 pontos** atuais (taverna, templo, ferraria, guilda, mercado, portão). Prédios sem forma reconhecível na imagem ganham marcador rotulado. |
| Papel das imagens | **Img 2 ("Alva e Luz") = cidade**. Img 1 (rua do mercado) = só referência de estilo, não entra no jogo. Lojas abrem como painéis normais. |
| Tipo de destaque | **Híbrido**: marcadores flutuantes nos 6 + brilho de silhueta nos 3 reconhecíveis (templo, mercado, portão). Sem recortar a imagem. |
| Vida na cena | **Imagem + vida sutil** (CSS-first): névoa nas bordas, brilho piscando em tochas/janelas, pulsar no portão, respiração dos marcadores. |
| Telas | **PC e celular igualmente**: palco de proporção travada + barra inferior de aventura no mobile. |
| Rollback | Constante `CITY_MODE` (`'image'` padrão / `'3d'` fallback) — a cena 3D atual é **preservada**, não deletada. |

## Arquitetura

Tudo em `game.js` + `game.css` + o arquivo de imagem. **Nada** em `server.py`
(o protocolo de loja/masmorra já existe) nem em `gameState.js` (sem lógica nova).
Confere com a regra do `CLAUDE.md`: lógica no servidor/`gameState.js`, render no
`game.js`.

### `CITY_MODE`
- Constante no topo do bloco de cidade em `game.js`: `const CITY_MODE = 'image';`
- No ponto onde hoje se chama `initCity3D()`, passa a ser:
  `CITY_MODE === 'image' ? initCityImage() : initCity3D()`.
- `destroyCity3D()` ganha o par `destroyCityImage()`, e a desmontagem da tela
  escolhe pelo modo. As funções 3D (`initCity3D`, `_cityBuild*`, loop, raycast)
  **permanecem intactas** — viram fallback inerte quando `CITY_MODE==='image'`.

### `initCityImage()` — monta o overlay em DOM
Dentro de `#screen-city`, monta (e guarda referências para limpeza):

1. **Palco** `#city-stage`: `<div>` com proporção travada 3:2 (a imagem é
   1536×1024), centralizado, `max-width`/`max-height` conforme o viewport;
   moldura escura/vinheta preenche a sobra (letterbox vira "quadro").
2. **Imagem** `<img id="city-img" src="assets/city/alva_e_luz.png?v=…">`
   preenchendo o palco (`width/height:100%`, `object-fit:cover` dentro do palco
   3:2 — como a imagem já é 3:2, não há corte).
3. **Camada de vida** `#city-life` (absoluta, `pointer-events:none`): divs de
   glow posicionados + animações CSS; partículas opcionais num `<canvas>` pequeno.
4. **Hotspots** `#city-hotspots`: um `<button class="city-hotspot">` por prédio,
   posicionado em `%` (`left`,`top`) via `hx`,`hy`.

`destroyCityImage()` remove os nós criados, cancela `requestAnimationFrame` das
partículas e remove listeners de resize.

### Hotspots — reaproveitando `_CTY_BLDGS`
- Em cada item de `_CTY_BLDGS` acrescenta `hx`,`hy` (posição em % na imagem) e
  `hero:true` nos 3 reconhecíveis. As coords são calibradas olhando a imagem
  (templo = domo à direita; mercado = tendas coloridas ao centro-esquerda;
  portão = abertura da muralha na base; taverna/ferraria/guilda = posições
  plausíveis sobre telhados, sempre com rótulo).
- Cada hotspot:
  - `position:absolute; left:hx%; top:hy%; transform:translate(-50%,-50%)`.
  - Conteúdo: ícone (emoji atual) + nome. Os 3 `hero` podem ocultar o rótulo até
    o hover (o prédio se reconhece sozinho); os 3 sem prédio mostram rótulo
    sempre.
  - `title`/`aria-label` com nome + ação (acessibilidade + fallback de tooltip).
  - `onclick` → **handlers atuais, sem mudança**:
    - `dungeon` → `triggerDungeonEntrance()`
    - `guilda` → toast "Missões em breve"
    - resto → `openShop(MAPA_IDS_LOJA[id] || id)` (mantém o fix mercador→mercado)
  - Hover/foco: marcador cresce + acende + "holofote" no chão; nos `hero`,
    aparece o brilho de silhueta.

### Destaque híbrido
- **Marcador** (`.city-hotspot`): pílula translúcida sempre visível; no
  `:hover`/`:focus-visible` aumenta escala, aumenta brilho da borda e mostra um
  elemento `::after` de holofote radial no chão.
- **Brilho de silhueta** (só `hero`): um `<span class="city-hero-glow">`
  posicionado/ dimensionado sobre o prédio (radial-gradient + box-shadow suave),
  `opacity:0` por padrão, `opacity:1` no hover/foco do hotspot. Tamanho/posição
  calibrados por prédio. Sem recorte de imagem.

### Responsivo (PC + celular)
- `#city-stage` usa `aspect-ratio: 3 / 2` e cabe no viewport
  (`max-width:100%`, `max-height:100%`, centralizado por flex). Sobra vira
  moldura escura — proposital.
- Hotspots em `%` acompanham o palco automaticamente.
- **Mobile/retrato:** o "Ir para a aventura" também aparece na barra existente
  `#city-dungeon-bar` (toque garantido, fora da imagem). Em telas largas a barra
  pode ficar oculta (o hotspot do portão basta) ou discreta — decidir na
  implementação por media query.
- Barra de heróis (`#city-hero-bar`, topo) e ficha lateral
  (`abrirFichaCidade`/`#ficha-cidade-panel`) **inalteradas**.

### Vida sutil (CSS-first, leve)
- Névoa: 1–2 camadas com gradiente translúcido animadas por `@keyframes`
  (deslize lento) nas bordas — a img já tem névoa nas pontas, então casa.
- Tochas/janelas: poucos divs de glow (radial) em coords fixas com `@keyframes`
  de flicker (opacity/scale sutis).
- Portão: pulsar de glow (reaproveita a ideia da luz do portal 3D).
- Marcadores: leve "respiração" de brilho.
- Partículas/vaga-lumes: **opcional**, `<canvas>` pequeno com poucas partículas,
  `requestAnimationFrame`.
- **`prefers-reduced-motion: reduce`** desliga as animações (estado estático).

### Entrada da masmorra ("Ir para a aventura")
- O hotspot do portão e a versão na `#city-dungeon-bar` respeitam as **mesmas
  regras de habilitação** do botão atual (host / fase de campanha pronta). A
  lógica de quem pode entrar **não muda**; só o rótulo passa a
  "Ir para a aventura" e a posição vai pro portão.
- Texto do botão da barra: trocar "Entrar na Masmorra"/"Entrar na fase X" por
  "Ir para a aventura" (mantendo, se houver, o número da fase como sufixo —
  decidir na implementação; preferência: "▶ Ir para a aventura" e, em campanha,
  "▶ Ir para a aventura — Fase X").

### Badge de tempo
- `#city-time-badge` (dia/noite) perde sentido sem ciclo. **Esconder** no modo
  imagem (ou reusar como selo discreto "Alva e Luz"). Preferência: selo com o
  nome da cidade, canto superior, discreto.

## Detalhe do arquivo de imagem
- `assets/city/alva_e_luz.png` é na verdade **JPEG** (1536×1024). Navegadores
  renderizam por content-sniffing, mas o `server.py` envia `Content-Type:
  image/png` (por extensão). Resolver na implementação: **renomear para
  `alva_e_luz.jpg`** (Content-Type correto via mimetypes) e referenciar `.jpg`,
  **ou** reencodar de fato para PNG. Preferência: renomear para `.jpg`
  (menor/limpo). Atualizar o caminho no `<img>` conforme a escolha.
- `assets` já está em `_STATIC_ROOTS` no `server.py` → servido sem mudança.
- Usar cache-buster (`?v=…`) como os demais assets.

## Fora de escopo (YAGNI)
- Transição/zoom da img 2 pra img 1 ao clicar (descartado).
- Recorte de prédios em PNGs separados (descartado — risco estético).
- Ciclo dia/noite por overlay sobre a foto (descartado — briga com sombras
  pintadas).
- Qualquer mudança em loja, ficha, combate, protocolo ou `gameState.js`.

## Plano de segurança / rollback
1. **Antes de implementar:** commit de segurança (snapshot do estado atual) para
   poder voltar. (A árvore tem WIP não relacionado; o backup cobre o repo todo.)
2. **Em runtime:** `CITY_MODE='3d'` restaura a cena antiga instantaneamente.

## Critérios de aceite
- [ ] Cidade renderiza a imagem "Alva e Luz" enquadrada (3:2) em PC e celular,
      sem corte do portão nem da névoa.
- [ ] 6 hotspots clicáveis e rotulados; clique abre a loja correta / guilda /
      aventura, exatamente como antes.
- [ ] Hover/foco mostra marcador aceso + holofote; nos 3 `hero` aparece o brilho
      de silhueta.
- [ ] Portão = "Ir para a aventura", habilitado pelas mesmas regras de antes;
      no mobile também acessível pela barra inferior.
- [ ] Vida sutil visível (névoa/flicker/pulsar) e desligada com
      `prefers-reduced-motion`.
- [ ] Barra de heróis e ficha da cidade continuam funcionando.
- [ ] `CITY_MODE='3d'` volta à cena 3D sem erro.
- [ ] Sem mudança em `server.py` nem `gameState.js`.
