// src/visualConfig.js — Legends for Hire — Single Source of Visual Truth
//
// Every hardcoded color, roughness, intensity, and font value in game.html
// comes from this object. To change the game's look, edit ONLY this file.
//
// Mirrors VISUAL_CONTRACT.md — if they ever disagree, this file wins for JS.
//
// Usage: window.VC.dice.colors.d20  →  '#FF6600'

window.VC = {

  // ── Ambientes de iluminação do 3D (masmorra) ──────────────────────────────
  // Cada masmorra escolhe um preset via campo `ambiente` no JSON (default
  // "masmorra"). O preset controla SÓ luz/fog/exposição dos tiles já explorados;
  // a névoa de guerra (não-explorado = mesh oculto) é idêntica nos três.
  // Brilho crescente: penumbra < masmorra < ar_livre.
  // Lido por init3D em game.js: VC.ambientes[state.ambiente] || .masmorra.
  // As posições das direcionais são iguais às históricas; só mudam cores/intensidades.
  ambientes: {
    // Sombrio (cripta/caverna): mais escuro e fechado que o padrão.
    penumbra: {
      scene:    { bgColor: 0x141016, fogColor: 0x161018, fogDensity: 0.014 },
      exposure: 1.30,
      lighting: {
        ambient:  { color: 0xfff5e0, intensity: 0.55 },
        dirMain:  { color: 0xfffaf0, intensity: 1.50, pos: [ 5.0, 10.0,  5.0] },
        dirFill:  { color: 0xe8f0ff, intensity: 0.50, pos: [-4.0,  6.0, -4.0] },
        rimLight: { color: 0xffe0b0, intensity: 0.28, pos: [ 0.0,  4.0, -7.0] },
        dirPawn:  { color: 0xfff0d8, intensity: 0.90, pos: [-5.0,  8.0, -5.0] },
      },
    },
    // Padrão: claro e iluminado, com key forte preservando relevo/contraste.
    masmorra: {
      scene:    { bgColor: 0x1c1810, fogColor: 0x1c1810, fogDensity: 0.006 },
      exposure: 1.55,
      lighting: {
        ambient:  { color: 0xfff5e0, intensity: 1.05 },
        dirMain:  { color: 0xfffaf0, intensity: 2.10, pos: [ 5.0, 10.0,  5.0] },
        dirFill:  { color: 0xe8f0ff, intensity: 0.90, pos: [-4.0,  6.0, -4.0] },
        rimLight: { color: 0xffe0b0, intensity: 0.35, pos: [ 0.0,  4.0, -7.0] },
        // Luz SW dedicada às FRENTES dos peões (miniaturas olham para sudoeste,
        // lado da câmera padrão). Substitui as 2–3 PointLights que cada peão
        // carregava — contagem de luzes estável = sem recompilação de shaders.
        dirPawn:  { color: 0xfff0d8, intensity: 1.15, pos: [-5.0,  8.0, -5.0] },
      },
    },
    // Ar livre / dia: ainda mais claro, luz de sol neutra + preenchimento de céu.
    ar_livre: {
      scene:    { bgColor: 0x141414, fogColor: 0x223044, fogDensity: 0.003 },
      exposure: 1.65,
      lighting: {
        ambient:  { color: 0xfff6ea, intensity: 1.55 },
        dirMain:  { color: 0xffffff, intensity: 2.70, pos: [ 5.0, 10.0,  5.0] },
        dirFill:  { color: 0xdfeaff, intensity: 1.10, pos: [-4.0,  6.0, -4.0] },
        rimLight: { color: 0xffe0b0, intensity: 0.40, pos: [ 0.0,  4.0, -7.0] },
        dirPawn:  { color: 0xfff8ee, intensity: 1.30, pos: [-5.0,  8.0, -5.0] },
      },
    },
  },

  // ── Floor Tiles ────────────────────────────────────────────────────────────
  floor: {
    groutHex:    '#444444',  // seam visible between stone tiles
    baseR:        0.533,     // 0x888888 / 255 ≈ 0.533 — clearly lighter than walls
    baseVariance: 0.07,      // per-tile brightness jitter (adds ±0–7% per piece)
    emissive:    0x222222,   // minimum glow so floor never goes pitch-black
  },

  // ── Wall Tiles ─────────────────────────────────────────────────────────────
  wall: {
    mortarHex:  '#2a2a3a',   // blue-dark mortar gap between stone blocks
    baseR:       0.353,      // 0x5a / 255 ≈ 0.353  (R + G channels)
    baseB:       0.416,      // 0x6a / 255 ≈ 0.416  (B channel — blue-gray tint)
    variance:    0.06,       // R/G jitter per tile
    varianceB:   0.07,       // B jitter per tile
    emissive:   0x111120,    // preserves blue-stone silhouette in deep shadow
  },

  // ── Materiais de chão/parede (cores 3D por id; espelha server.MATERIAIS) ────
  // r,g,b em 0..1. Pisos coloridos cosméticos; entulho usa cor de parede-escombro.
  materiais: {
    pedra_cinza:   { color: [0.533, 0.533, 0.533] },
    terra:         { color: [0.42, 0.31, 0.20] },
    grama:         { color: [0.25, 0.42, 0.22] },
    pedra_negra:   { color: [0.14, 0.14, 0.16] },
    entulho:       { color: [0.34, 0.31, 0.27] },
    pedra_normal:  { color: [0.353, 0.353, 0.416] },
    enegrecida:    { color: [0.17, 0.17, 0.19] },
    pedra_caverna: { color: [0.30, 0.26, 0.21] },
    desmoronada:   { color: [0.33, 0.30, 0.25] },
  },

  // ── Dice ───────────────────────────────────────────────────────────────────
  // Material: MeshLambertMaterial — emissive ensures colors bypass scene lighting
  dice: {
    emissiveIntensity: 1.0,       // MAXIMUM: 100% emissive — dice glow with their own color regardless of scene lighting
    numberFontSize:    140,       // px — single digit; scaled proportionally for 2-digit
    numberStroke:      20,        // px MAXIMUM stroke — boldest white halo for absolute contrast
    borderWidth:        8,        // px black chamfer border on each face
    numberColor:      '#000000',  // black fill — maximum contrast on vivid backgrounds
    strokeColor:      '#FFFFFF',  // white stroke drawn before fill for visibility
    scale:             1.30,      // 30% larger than geometry base — easier to see on board
    light: {
      main: { intensity: 6.0, distance: 4.0, yOffset:  2.0 },  // MAXIMUM key light intensity for brightest top illumination
      fill: { intensity: 3.5, distance: 3.0, yOffset: -1.0 },  // MAXIMUM fill light to eliminate all shadows
    },
    colors: {
      d4:  '#FFE000',   // yellow
      d6:  '#FF1111',   // red
      d8:  '#0055FF',   // blue
      d10: '#00DD44',   // green
      d12: '#CC00FF',   // purple
      d20: '#FF5500',   // orange
    },

    // ── D20-specific overrides (triangular faces need separate treatment) ────
    // IcosahedronGeometry UV-maps each face as a triangle inside the canvas.
    // Numbers must be smaller and centered at the triangle's visual centroid.
    d20: {
      fontSz1:   90,           // px — single-digit faces (1–9)
      fontSz2:   68,           // px — two-digit faces (10–20)
      numY:     155,           // canvas y of visual centroid (below 128 midpoint)
      // Clip triangle (canvas px) keeps drawing within the visible triangular face
      clipPts: [[128, 20], [236, 210], [20, 210]],
    },
  },

  // ── Pawns / Miniatures ─────────────────────────────────────────────────────
  pawns: {
    emissiveIntensity:    0.10,   // cloth / leather / skin self-glow (10 % of color)
    baseColor:            0x111111,
    rimEmissiveIntensity: 0.85,   // colored rim ring that IDs each hero in shadow
    pointLightIntensity:  1.20,   // individual overhead PointLight per pawn
    pointLightDistance:   2.50,
  },

  // ── Typography ─────────────────────────────────────────────────────────────
  fonts: {
    title: "'Cinzel Decorative', serif",
    body:  "'Cinzel', serif",
  },

  // ── UI Colors & Transitions (consolidado de uiTheme.js) ────────────────────
  // Injetado em CSS como custom properties via uiTheme.js.
  // Acesso em JS: VC.ui.colors.gold, VC.ui.transitions.normal, etc.
  ui: {
    colors: {
      gold:       '#c8a951',
      goldDim:    '#8a6a2a',
      goldGlow:   '#c8a95144',      // #c8a951 @ ~27% opacity
      goldRgb:    '200,169,81',     // for rgba(var(--gold-rgb), alpha) usage
      dark:       '#0a0805',
      darkRgb:    '4,2,14',         // near-black used in gradients/panels
      darkPanel:  'rgba(4,2,14,0.92)',
      text:       '#c8b89a',
      textDim:    '#8a7a5a',
      textFaint:  '#5a4a3a'
    },
    transitions: {
      fast:   '0.2s ease',
      normal: '0.4s ease',
      slow:   '1s ease'
    }
  },

};

// ── Retrocompat: `VC.scene`/`VC.lighting` apontam para o preset padrão (masmorra).
// Código legado que lê esses caminhos continua funcionando; init3D escolhe o
// preset por `state.ambiente` via VC.ambientes.
window.VC.scene    = window.VC.ambientes.masmorra.scene;
window.VC.lighting = window.VC.ambientes.masmorra.lighting;
