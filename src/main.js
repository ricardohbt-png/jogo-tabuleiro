// ═══════════════════════════════════════════════════════════════════════════════
// src/main.js — Legends for Hire
//
// Main entry point for the Legends for Hire RPG client.
// Coordinates all game modules and initializes the application.
//
// Load order:
// 1. visualConfig.js (window.VC)
// 2. src/ui/theme.js (CSS custom properties)
// 3. src/gameState.js (window.GS)
// 4. src/main.js (this file)
// 5. Inline game code in index.html
//
// This module will eventually contain:
// - Game initialization
// - Screen management (title → selection → city → dungeon)
// - Module coordination
// ═══════════════════════════════════════════════════════════════════════════════

'use strict';

console.log('Loading Legends for Hire — Main module...');

// Validate visualConfig is loaded
if (typeof window.VC === 'undefined') {
  console.error('ERROR: visualConfig.js not loaded. Check <head> scripts.');
  throw new Error('visualConfig.js is required.');
}

console.log('✓ visualConfig.js loaded.');

// NOTE: gameState.js loads AFTER this file, so we validate it in inline code
// or defer validation to when the full page is loaded.

// Future: This is where screen management, module loading,
// and game initialization will happen once code is refactored.

// ── Exposição global (window-aware) ─────────────────────────────────────────
// GS e CATALOGO_ITENS são expostos em `window` AQUI — não em gameState.js, que
// por contrato é livre de window/DOM (ver CLAUDE.md). main.js carrega logo após
// gameState.js e antes de game.js, então GS já existe neste ponto.
if (typeof GS !== 'undefined') {
  window.GS = GS;
  window.CATALOGO_ITENS = GS.CATALOGO_ITENS;
} else {
  console.error('❌ GS não encontrado em main.js — verifique a ordem dos scripts.');
}
