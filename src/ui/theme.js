// ═══════════════════════════════════════════════════════════════════════════════
// uiTheme.js — Legends for Hire
//
// CSS Custom Properties Injector
//
// Reads all UI colors, fonts, and transitions from window.VC (visualConfig.js)
// and injects them as CSS custom properties so the stylesheet can use var(--gold),
// var(--text), var(--trans-normal), etc.
//
// This file is intentionally minimal — all semantic values live in visualConfig.js.
//
// Usage in CSS: var(--gold), var(--text), var(--trans-normal), etc.
// Usage in JS : VC.ui.colors.gold, VC.ui.fonts.title, VC.ui.transitions.normal
// ═══════════════════════════════════════════════════════════════════════════════

(function injectTheme() {
  'use strict';

  // Espera VC estar disponível (carregado em index.html antes deste script)
  if (typeof window.VC === 'undefined') {
    console.error('uiTheme.js: window.VC não encontrado. Verifique que visualConfig.js foi carregado primeiro.');
    return;
  }

  const r = document.documentElement.style;
  const c = window.VC.ui.colors;
  const f = window.VC.fonts;
  const t = window.VC.ui.transitions;

  // Injetar fonts
  r.setProperty('--font-title',   f.title);
  r.setProperty('--font-body',    f.body);

  // Injetar colors
  r.setProperty('--gold',         c.gold);
  r.setProperty('--gold2',        c.goldDim);
  r.setProperty('--gold-dim',     c.goldDim);
  r.setProperty('--gold-glow',    c.goldGlow);
  r.setProperty('--gold-rgb',     c.goldRgb);

  r.setProperty('--dark',         c.dark);
  r.setProperty('--dark-rgb',     c.darkRgb);
  r.setProperty('--dark-panel',   c.darkPanel);

  r.setProperty('--text',         c.text);
  r.setProperty('--text-dim',     c.textDim);
  r.setProperty('--text-faint',   c.textFaint);

  // Injetar transitions
  r.setProperty('--trans-fast',   t.fast);
  r.setProperty('--trans-normal', t.normal);
  r.setProperty('--trans-slow',   t.slow);
})();
