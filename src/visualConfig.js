// src/visualConfig.js — Legends for Hire — Single Source of Visual Truth
//
// Every hardcoded color, roughness, intensity, and font value in game.html
// comes from this object. To change the game's look, edit ONLY this file.
//
// Mirrors VISUAL_CONTRACT.md — if they ever disagree, this file wins for JS.
//
// Usage: window.VC.dice.colors.d20  →  '#FF6600'

window.VC = {

  // ── Scene / Atmosphere ─────────────────────────────────────────────────────
  scene: {
    bgColor:    0x1c1810,   // dark brownish-black
    fogColor:   0x1c1810,
    fogDensity: 0.02,       // FogExp2 — max per VISUAL_CONTRACT
  },

  // ── Dungeon Lighting ───────────────────────────────────────────────────────
  lighting: {
    ambient:  { color: 0xfff5e0, intensity: 0.70 },
    dirMain:  { color: 0xfffaf0, intensity: 1.80, pos: [ 5.0, 10.0,  5.0] },
    dirFill:  { color: 0xe8f0ff, intensity: 0.60, pos: [-4.0,  6.0, -4.0] },
    rimLight: { color: 0xffe0b0, intensity: 0.22, pos: [ 0.0,  4.0, -7.0] },
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
