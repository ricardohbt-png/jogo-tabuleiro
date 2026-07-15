# Camada C-a — ND unificado + Termômetro no Editor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar `cr` (Nível de Desafio) a todo monstro, um módulo de dificuldade compartilhado, e um termômetro de dificuldade no editor de masmorras (total + pior sala, com preview de 2/4/6 jogadores).

**Architecture:** Servidor ganha `cr` nos 6 monstros legados + helper `monster_cr` + campo `expected_party` (carga/validação/serialização). Um módulo puro `src/difficulty.js` (window.Difficulty) centraliza faixas/limiares/cores e é incluído no editor e no jogo. O editor computa total/pior-sala a partir do `cr` do catálogo e mostra barras coloridas + seletor 2/4/6. Fase C-b (minimapa em jogo) é um plano separado que reusa `src/difficulty.js` e `expected_party` do `game_state`.

**Tech Stack:** Python (`server.py`), Vanilla JS (`src/difficulty.js`, `tools/editor.js`), catálogo gerado (`tools/export_catalog.py` → `tools/editor_catalog.js`). Testes: `tools/test_modo_mestre.py` (harness caseiro `check(name, cond)`), `node --check`, self-test via `node -e`.

**Spec:** `docs/superpowers/specs/2026-07-15-modo-mestre-camada-c-nd-termometro-design.md`

---

## File Structure

- **Modify `server.py`** — `cr` nos 6 legados; `monster_cr` (module-level); `expected_party` em `__init__`, `_norm_expected_party`, carga da dungeon, `validar_dungeon`, `push_state`.
- **Modify `tools/test_modo_mestre.py`** — seções de teste [19]/[20].
- **Create `src/difficulty.js`** — módulo puro de dificuldade.
- **Modify `index.html`** — incluir `src/difficulty.js`.
- **Modify `tools/editor.html`** — incluir `../src/difficulty.js`.
- **Regenerate & commit `tools/editor_catalog.js`** — via `export_catalog.py` (exceção consciente: aqui a regeneração É a mudança).
- **Modify `tools/editor.js`** — estado `expectedParty` + serialização + UI de grupo esperado + termômetro (total/pior-sala) + preview 2/4/6.

**Ordering:** Task 1 (server cr) → 2 (server expected_party) → 3 (regen catalog, precisa do cr) → 4 (difficulty.js) → 5 (editor expected_party) → 6 (editor termômetro, precisa de 3+4+5).

---

## Task 1: Servidor — `cr` nos legados + helper `monster_cr`

**Files:**
- Modify: `server.py` (`MONSTER_DEFS` 6 legados ~linhas 1436-1441; novo `monster_cr` antes de `def make_monster` ~linha 4231)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione em `main()` de `tools/test_modo_mestre.py` (após a última seção existente):

```python
    print("\n[19] ND unificado — monster_cr")
    check("cr explícito é usado", S.monster_cr({"cr": 1.5, "tier": 1}) == 1.5)
    check("fallback por tier sem cr", S.monster_cr({"tier": 3}) == 2.0)
    check("fallback default sem cr nem tier", S.monster_cr({}) == 1.0)
    _by = lambda t: next(d for d in S.MONSTER_DEFS if d["type"] == t)
    check("goblin legado cr 0.25", S.monster_cr(_by("goblin")) == 0.25)
    check("skeleton legado cr 0.5", S.monster_cr(_by("skeleton")) == 0.5)
    check("orc legado cr 0.75", S.monster_cr(_by("orc")) == 0.75)
    check("dark_mage legado cr 0.5", S.monster_cr(_by("dark_mage")) == 0.5)
    check("troll legado cr 1.5", S.monster_cr(_by("troll")) == 1.5)
    check("dragon legado cr 5", S.monster_cr(_by("dragon")) == 5.0)
    check("todos MONSTER_DEFS resolvem cr>0", all(S.monster_cr(d) > 0 for d in S.MONSTER_DEFS))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute 'monster_cr'`.

- [ ] **Step 3: Implementar**

(a) Nos 6 monstros legados de `MONSTER_DEFS` (server.py ~linhas 1436-1441), adicione `"cr": <valor>,` a cada dict. Os valores exatos:
- `goblin` → `"cr": 0.25`
- `skeleton` → `"cr": 0.5`
- `orc` → `"cr": 0.75`
- `dark_mage` → `"cr": 0.5`
- `troll` → `"cr": 1.5`
- `dragon` → `"cr": 5.0`

Ex.: a linha do goblin passa a ter `..., "gold": 5, "tier": 1, "cr": 0.25},`. Mantenha o resto de cada linha intacto.

(b) Adicione, module-level, logo antes de `def make_monster(mdef, room):` (~linha 4231):

```python
_CR_POR_TIER = {1: 0.5, 2: 1.0, 3: 2.0, 4: 5.0}

def monster_cr(mdef):
    """Nível de Desafio (cr) unificado do monstro. Usa o cr explícito quando
    presente; senão cai para um valor derivado do tier. Fonte única da verdade."""
    cr = mdef.get("cr")
    if cr is not None:
        try:
            return float(cr)
        except (TypeError, ValueError):
            pass
    return _CR_POR_TIER.get(mdef.get("tier", 1), 1.0)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção [19].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): cr unificado nos monstros legados + helper monster_cr"
```

---

## Task 2: Servidor — campo `expected_party` (carga/validação/serialização)

**Files:**
- Modify: `server.py` (`__init__` ~4507; `_norm_expected_party` novo; carga da dungeon ~6297 após `_carregar_master_reserve`; `validar_dungeon` ~2956; `push_state` ~17298)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione em `main()` de `tools/test_modo_mestre.py`:

```python
    print("\n[20] expected_party — normalização/validação")
    check("default sem campo", S.GameRoom._norm_expected_party(None) == {"heroes": 4, "level": 1})
    check("valores válidos preservados", S.GameRoom._norm_expected_party({"heroes": 6, "level": 3}) == {"heroes": 6, "level": 3})
    check("clampa heroes p/ 6", S.GameRoom._norm_expected_party({"heroes": 99, "level": 1})["heroes"] == 6)
    check("clampa heroes p/ 1", S.GameRoom._norm_expected_party({"heroes": 0, "level": 1})["heroes"] == 1)
    check("level mínimo 1", S.GameRoom._norm_expected_party({"heroes": 4, "level": 0})["level"] == 1)
    r = playing_room_com_mestre()
    check("default no __init__", r.expected_party == {"heroes": 4, "level": 1})
    # validar_dungeon (reusa o `base` da seção [17]; se aquela seção não estiver
    # no arquivo, reconstrua um base mínimo válido como lá)
    def _com_ep(ep):
        d = dict(base); d["expected_party"] = ep; return d
    ok, _ = S.validar_dungeon(_com_ep({"heroes": 4, "level": 2}))
    check("ep válido aceito", ok is True)
    ok, msg = S.validar_dungeon(_com_ep({"heroes": 7, "level": 1}))
    check("heroes>6 rejeitado", ok is False and "heroes" in msg.lower())
    ok, _ = S.validar_dungeon(_com_ep({"heroes": 4, "level": 0}))
    check("level<1 rejeitado", ok is False)
    ok, _ = S.validar_dungeon(_com_ep("naoobj"))
    check("não-objeto rejeitado", ok is False)
```

> `base` é o dict de masmorra mínima válida definido na seção [17] deste mesmo arquivo. Se necessário, replique-o aqui.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — `_norm_expected_party` não existe; `r.expected_party` não existe.

- [ ] **Step 3: Implementar**

(a) Em `GameRoom.__init__`, logo após `self.master_reserve = {}` (~linha 4510), adicione:

```python
        self.expected_party = {"heroes": 4, "level": 1}   # Camada C: grupo esperado (referência)
```

(b) Adicione o normalizador estático (perto dos helpers do mestre, ex.: após `_carregar_master_reserve`):

```python
    @staticmethod
    def _norm_expected_party(ep):
        """Normaliza o grupo esperado da masmorra (Camada C). heroes 1–6, level ≥1.
        Default {4,1}. Defensivo — a validação estrita fica em validar_dungeon."""
        if isinstance(ep, dict):
            try:
                return {"heroes": max(1, min(6, int(ep.get("heroes", 4)))),
                        "level":  max(1, int(ep.get("level", 1)))}
            except (TypeError, ValueError):
                pass
        return {"heroes": 4, "level": 1}
```

(c) No bloco de carga da dungeon, logo após `self._carregar_master_reserve(defn)` (~linha 6297), adicione:

```python
        self.expected_party = self._norm_expected_party(defn.get("expected_party"))
```

(d) Em `validar_dungeon`, logo após o bloco de `master_reinforcements` (~linha 2956), adicione:

```python
    ep = defn.get("expected_party")
    if ep is not None:
        if not isinstance(ep, dict):
            return False, "expected_party deve ser um objeto JSON."
        h = ep.get("heroes"); lv = ep.get("level")
        if not isinstance(h, int) or isinstance(h, bool) or not (1 <= h <= 6):
            return False, f"expected_party.heroes inválido: {h!r} (inteiro 1–6)."
        if not isinstance(lv, int) or isinstance(lv, bool) or lv < 1:
            return False, f"expected_party.level inválido: {lv!r} (inteiro ≥ 1)."
```

(e) Em `push_state` (~linha 17298), logo após a linha `"master_reserve": [...]` (que a Camada B adicionou), adicione:

```python
            "expected_party": self.expected_party,
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção [20].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): campo expected_party (carga/validacao/serializacao)"
```

---

## Task 3: Regenerar o catálogo do editor (cr nos legados)

**Files:**
- Regenerate: `tools/editor_catalog.js` (via `tools/export_catalog.py`)

- [ ] **Step 1: Regenerar**

Run: `python tools/export_catalog.py`

- [ ] **Step 2: Conferir que o cr dos legados entrou**

Run: `grep -A1 '"type": "goblin"' tools/editor_catalog.js | grep -c '"cr"'` (esperado ≥1) — ou abra o arquivo e confirme que a entrada `goblin` agora tem `"cr": 0.25`, `dragon` tem `"cr": 5`, etc.

- [ ] **Step 3: Commit** (exceção consciente — aqui a regeneração É a mudança)

```bash
git add tools/editor_catalog.js
git commit -m "chore(editor): regenera catalogo com cr dos monstros legados"
```

---

## Task 4: Módulo de dificuldade compartilhado `src/difficulty.js`

**Files:**
- Create: `src/difficulty.js`
- Modify: `index.html` (loader ~linha 23); `tools/editor.html` (loader ~linha 56)

- [ ] **Step 1: Criar `src/difficulty.js`**

```javascript
// Módulo de dificuldade compartilhado entre o editor e o cliente de jogo.
// Puro (sem DOM). Exposto como window.Difficulty (browser) / global.Difficulty (node).
// Ponto ÚNICO de calibração das faixas de dificuldade da Camada C.
(function (root) {
  'use strict';
  var CR_POR_TIER = { 1: 0.5, 2: 1.0, 3: 2.0, 4: 5.0 };
  // Faixas por razão CR/poder. Ordem crescente; `max` é o teto exclusivo da faixa.
  var FAIXAS = [
    { key: 'facil',       label: 'Fácil',       color: '#4caf50', max: 0.4 },
    { key: 'equilibrada', label: 'Equilibrada', color: '#c9b037', max: 0.8 },
    { key: 'dificil',     label: 'Difícil',     color: '#e08a2b', max: 1.2 },
    { key: 'mortal',      label: 'Mortal',      color: '#d0473f', max: Infinity }
  ];
  function crFromEntry(entry) {
    if (!entry) return 0;
    var cr = entry.cr;
    if (cr !== undefined && cr !== null && !isNaN(parseFloat(cr))) return parseFloat(cr);
    return CR_POR_TIER[entry.tier] || 1.0;
  }
  function poder(heroes, level) { return Math.max(1, (heroes || 0) * (level || 0)); }
  function faixa(nd, pod) {
    var ratio = nd / Math.max(1, pod);
    for (var i = 0; i < FAIXAS.length; i++) { if (ratio < FAIXAS[i].max) return FAIXAS[i]; }
    return FAIXAS[FAIXAS.length - 1];
  }
  root.Difficulty = { crFromEntry: crFromEntry, poder: poder, faixa: faixa, FAIXAS: FAIXAS };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
```

- [ ] **Step 2: Self-test (node)**

Run:
```bash
node --check src/difficulty.js && node -e "require('./src/difficulty.js'); var D=global.Difficulty; console.assert(D.faixa(0.3,1).key==='facil','facil'); console.assert(D.faixa(0.6,1).key==='equilibrada','equil'); console.assert(D.faixa(1.0,1).key==='dificil','dif'); console.assert(D.faixa(2.0,1).key==='mortal','mortal'); console.assert(D.crFromEntry({cr:2})===2,'cr'); console.assert(D.crFromEntry({tier:4})===5,'tier'); console.assert(D.poder(4,2)===8,'poder'); console.log('difficulty.js OK');"
```
Expected: `difficulty.js OK` (sem AssertionError).

- [ ] **Step 3: Incluir no `index.html`**

Na linha ~23 (o `document.write` que carrega `gameState.js`/`main.js`/`game.js`/…), adicione o difficulty.js ANTES do `game.js`. A linha vira (insira o novo `document.write` logo após o de `gameState.js`):

```javascript
document.write('<script src="src/difficulty.js?v='+v+'"><\/script>');
```

- [ ] **Step 4: Incluir no `tools/editor.html`**

Na linha ~56, o array `s=[...]` de scripts. Adicione `"../src/difficulty.js"` como PRIMEIRO item do array (antes de `editor_catalog.js`), já que `editor.html` está em `tools/` e o módulo está em `src/`:

```javascript
var s=["../src/difficulty.js","editor_catalog.js","editor_monsters_custom.js","editor_dungeons.js","editor.js","editor_bestiary.js","editor_monster_editor.js","story_upload.js","editor_campaign.js"];
```

- [ ] **Step 5: Verificar sintaxe**

Run: `node --check index.html 2>/dev/null || true` (index.html não é JS puro; pule) e confirme visualmente as duas inclusões. `node --check src/difficulty.js` já passou no Step 2.

- [ ] **Step 6: Commit**

```bash
git add src/difficulty.js index.html tools/editor.html
git commit -m "feat(dificuldade): modulo compartilhado src/difficulty.js (faixas de CR)"
```

---

## Task 5: Editor — grupo esperado (estado + serialização + inputs)

**Files:**
- Modify: `tools/editor.js` (estado `S` ~18; save ~1240; load ~1381; painel `!S.sel` de `renderPanel` ~822)

- [ ] **Step 1: Estado + serialização**

(a) No estado inicial `S` (~linha 18, junto de `masterReinforcements: []`), adicione:

```javascript
    expectedParty: { heroes: 4, level: 1 },
```

(b) No `save()` (~linha 1240, junto de `master_reinforcements: ...`), adicione:

```javascript
      expected_party: { heroes: S.expectedParty.heroes, level: S.expectedParty.level },
```

(c) No load (~linha 1381, junto de `S.masterReinforcements = ...`), adicione:

```javascript
    S.expectedParty = (function (ep) {
      ep = ep || {};
      return { heroes: Math.max(1, Math.min(6, parseInt(ep.heroes, 10) || 4)),
               level:  Math.max(1, parseInt(ep.level, 10) || 1) };
    })(obj.expected_party);
```

- [ ] **Step 2: Inputs de grupo esperado no painel**

No ramo `!S.sel` de `renderPanel` (onde ficam objetivos + Reforços do Mestre da Camada B), adicione — dentro da template string, logo APÓS a seção de reforços (procure `id="reinforce-list"` … `reinforce-add-btn`) e antes do fechamento — o bloco de grupo esperado:

```javascript
        + `<hr style="border-color:#3a3022;margin:10px 0">
        <label>👥 grupo esperado</label>
        <div style="display:flex;gap:6px;align-items:center;margin-top:4px">
          <span>heróis</span><input id="ep-heroes" type="number" min="1" max="6" value="${S.expectedParty.heroes}" style="width:48px">
          <span>nível</span><input id="ep-level" type="number" min="1" value="${S.expectedParty.level}" style="width:48px">
        </div>`
```

> Nota: a template do painel `!S.sel` é uma única atribuição a `panel.innerHTML`. Concatene o trecho acima na expressão correta (o painel da Camada B já usa `+ \`...\`` para anexar seções). Ajuste as crases/`+` para encaixar na expressão existente.

E no wiring (após o painel ser inserido, junto do wiring dos botões de reforço), adicione:

```javascript
      var epH = document.getElementById("ep-heroes");
      var epL = document.getElementById("ep-level");
      if (epH) epH.onchange = e => { S.expectedParty.heroes = Math.max(1, Math.min(6, parseInt(e.target.value, 10) || 4)); renderPanel(); };
      if (epL) epL.onchange = e => { S.expectedParty.level  = Math.max(1, parseInt(e.target.value, 10) || 1); renderPanel(); };
```

- [ ] **Step 3: Verificar sintaxe**

Run: `node --check tools/editor.js`
Expected: sem erro.

- [ ] **Step 4: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): campo grupo esperado (expected_party)"
```

---

## Task 6: Editor — termômetro (total + pior sala) + preview 2/4/6

**Files:**
- Modify: `tools/editor.js` (painel `!S.sel` de `renderPanel`, logo após os inputs de grupo esperado da Task 5; módulo usa `window.Difficulty`)

- [ ] **Step 1: Estado de preview (module-level)**

Perto do topo do IIFE do `editor.js` (junto de outras vars de módulo), adicione:

```javascript
  var _ndPreviewHeroes = null;   // null = usa S.expectedParty.heroes; 2/4/6 = preview
```

- [ ] **Step 2: Helpers de cálculo + render do termômetro**

Adicione, dentro do IIFE do `editor.js` (perto das outras funções `render*`), estas funções:

```javascript
  function _ndPorSala() {
    // Soma de cr por room_id (null vira grupo "sem sala"). Retorna {total, pior}.
    var porSala = {}, total = 0;
    (S.monsters || []).forEach(function (m) {
      var entry = (CAT.monsters || []).find(function (c) { return c.type === m.type; });
      var cr = window.Difficulty ? window.Difficulty.crFromEntry(entry) : 0;
      total += cr;
      var key = (m.room_id == null) ? "__none__" : m.room_id;
      porSala[key] = (porSala[key] || 0) + cr;
    });
    var pior = 0;
    Object.keys(porSala).forEach(function (k) { if (porSala[k] > pior) pior = porSala[k]; });
    return { total: total, pior: pior };
  }

  function _termometroHTML() {
    if (!window.Difficulty) return "";
    var heroes = (_ndPreviewHeroes != null) ? _ndPreviewHeroes : S.expectedParty.heroes;
    var pod = window.Difficulty.poder(heroes, S.expectedParty.level);
    var nd = _ndPorSala();
    function linha(rot, valor) {
      var f = window.Difficulty.faixa(valor, pod);
      var pct = Math.max(4, Math.min(100, (valor / (pod * 1.5)) * 100));
      return '<div style="margin-top:4px"><span>' + rot + ': <b>' + valor.toFixed(2) + '</b> — ' +
        '<span style="color:' + f.color + '">' + f.label + '</span></span>' +
        '<div style="height:8px;background:#241d14;border-radius:4px;overflow:hidden;margin-top:2px">' +
        '<div style="height:100%;width:' + pct + '%;background:' + f.color + '"></div></div></div>';
    }
    var sel = [2, 4, 6].map(function (n) {
      var on = ((_ndPreviewHeroes != null ? _ndPreviewHeroes : S.expectedParty.heroes) === n);
      return '<button data-ndprev="' + n + '" class="ndprev' + (on ? ' on' : '') + '">' + n + '</button>';
    }).join("");
    return '<hr style="border-color:#3a3022;margin:10px 0"><label>🌡️ termômetro (poder ' + pod + ')</label>' +
      linha("Total", nd.total) + linha("Pior sala", nd.pior) +
      '<div style="margin-top:6px;display:flex;gap:4px;align-items:center"><span>preview jogadores:</span>' + sel + '</div>';
  }
```

- [ ] **Step 3: Injetar no painel + wiring**

No ramo `!S.sel` de `renderPanel`, concatene `+ _termometroHTML()` na template do `panel.innerHTML`, logo após os inputs de grupo esperado (Task 5). Depois, no wiring, adicione:

```javascript
      panel.querySelectorAll(".ndprev").forEach(function (b) {
        b.onclick = function () {
          var n = parseInt(b.dataset.ndprev, 10);
          _ndPreviewHeroes = (_ndPreviewHeroes === n) ? null : n;
          renderPanel();
        };
      });
```

- [ ] **Step 4: CSS mínimo (opcional)**

Se quiser, em `tools/editor.css`: `.ndprev{cursor:pointer;padding:2px 8px} .ndprev.on{outline:2px solid #d9b45a}`. (Ou deixe sem — funciona com estilo padrão.)

- [ ] **Step 5: Verificar sintaxe + verificação manual**

Run: `node --check tools/editor.js`
Manual: abra o editor, coloque monstros em salas diferentes, confirme que Total e Pior-sala aparecem com faixas coloridas, que mudar heróis/nível recalcula, e que os botões 2/4/6 alternam o preview.

- [ ] **Step 6: Commit**

```bash
git add tools/editor.js tools/editor.css
git commit -m "feat(editor): termometro de dificuldade (total/pior-sala) + preview 2/4/6"
```

---

## Verificação final (Fase C-a)

1. `python tools/test_modo_mestre.py` — seções [19]/[20] verdes, sem regressão.
2. `node --check src/difficulty.js tools/editor.js` — sem erro; `node -e` self-test de difficulty.js OK.
3. `tools/editor_catalog.js` regenerado e commitado (cr nos legados).
4. Verificação manual do termômetro no editor.
5. **Fase C-b (minimapa do mestre em jogo)** é um plano separado, a ser escrito depois desta fase concluída — reusa `src/difficulty.js` e `game_state.expected_party` (já serializado na Task 2).
