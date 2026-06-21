# Ficha — Totais Efetivos de Arma e Armadura — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Os ícones ⚔ ARMA e 🛡 ARMADURA da ficha própria mostram o dano efetivo (uma expressão consolidada com todos os bônus ativos) e a CA efetiva (com badges por modificador), e ao passar o mouse sobre a arma o mapa destaca o alcance em vermelho (com formas corretas para armas de alcance).

**Architecture:** O servidor (`server.py`) é a fonte da verdade: extrai a soma de dano sustentado para um helper compartilhado por `handle_attack` (display == rolagem), e envia `weapon_damage`, `effective_ac` e `ac_breakdown` no payload de cada jogador. O cliente (`game.js`) só renderiza; a lógica pura de alcance migra para `gameState.js` (`GS.weaponRangeTiles`). Skills armadas do warrior (Golpe Devastador ×2) são sobrepostas no cliente, pois só existem como estado do cliente até o ataque.

**Tech Stack:** Python 3.x (`websockets`), Vanilla JS (browser IIFE `GS`), canvas 2D + Three.js r128. Testes de servidor no padrão `tools/test_*.py` (rodam da raiz com `python tools/<x>.py`). Cliente verificado via workflow de preview no browser (não há test runner JS no projeto).

**Spec:** `docs/superpowers/specs/2026-06-21-ficha-arma-armadura-totais-design.md`

---

## Estrutura de Arquivos

| Arquivo | Mudança |
|---|---|
| `server.py` | `_sustained_dano_bonus`, `_weapon_damage_breakdown`, `_ac_breakdown`, `_players_for_state`; refatorar `handle_attack` p/ usar o helper; `push_state` envia o payload enriquecido |
| `tools/test_ficha_totais.py` | **Criar** — testa parity dano + breakdown de CA |
| `src/gameState.js` | `GS.weaponRangeTiles(state, me)` (lógica pura de alcance + reach) |
| `game.js` | Render do ícone de arma (expressão), do ícone de armadura (badges), hover no ⚔ ARMA; trocar chamadas p/ `GS.weaponRangeTiles` |

---

## Task 1: Servidor — helper de dano sustentado + breakdown de arma

**Files:**
- Modify: `server.py` (adicionar `_sustained_dano_bonus` e `_weapon_damage_breakdown` perto de `_player_effective_ac`; refatorar 2 pontos de `handle_attack`)
- Test: `tools/test_ficha_totais.py`

A pilha real de dano em `handle_attack` (acerto armado) hoje é:
```
dmg = raw_dmg + stat_bonus ; if crit: dmg *= 2
dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano + self._mod_magia(p,"dano") - self._corrosao_arma_pen(p))
```
A parte aditiva sustentada (NÃO dobrada por crítico) será extraída para `_sustained_dano_bonus`, compartilhada entre o cálculo real e o display.

- [ ] **Step 1: Escrever o teste falhando**

Criar `tools/test_ficha_totais.py`:

```python
"""Testa os totais efetivos da ficha: parity do dano sustentado (display ==
rolagem) e breakdown de CA. Roda da raiz: python tools/test_ficha_totais.py"""
import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, mod

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    return r

def mk(r, cls="warrior"):
    p = make_player("p1", "Herói", cls, 0)
    p["fome"] = p["sede"] = 50          # neutro: sem saciado (+1) nem exaustão (-1/-2)
    r.players[p["id"]] = p
    return p

# ── Breakdown de arma ─────────────────────────────────────────────────────
r = setup(); p = mk(r, "warrior")          # machado_basico 1d6, str_; FOR 18 → +4
bd = r._weapon_damage_breakdown(p)
check("die do machado é 1d6", bd["die"] == "1d6")
check("flat_bonus base = mod(FOR)", bd["flat_bonus"] == mod(p["str_"]))
check("sem dados extras sem buff", bd["extra_dice"] == [])

# Golpe Sagrado sustentado → +1d8 em extra_dice
p["golpe_sagrado_ativo"] = True
bd = r._weapon_damage_breakdown(p)
check("Golpe Sagrado vira +1d8", any(e["die"] == "1d8" for e in bd["extra_dice"]))
p["golpe_sagrado_ativo"] = False

# mods_magia dano +1 entra no flat
r._set_mod_magia(p, {"dano": 1}, 3)
bd = r._weapon_damage_breakdown(p)
check("mods_magia dano soma no flat", bd["flat_bonus"] == mod(p["str_"]) + 1)
p.pop("mods_magia", None)

# Hook de arma mágica (campo futuro dano_bonus)
p["weapon"]["dano_bonus"] = 2
bd = r._weapon_damage_breakdown(p)
check("dano_bonus do item entra no flat", bd["flat_bonus"] == mod(p["str_"]) + 2)
p["weapon"].pop("dano_bonus", None)

# Parity: _sustained_dano_bonus reflete a soma real sustentada
r._set_mod_magia(p, {"dano": 1}, 3)
sust = r._sustained_dano_bonus(p)
check("sustained = mod_magia(1) sem outros buffs", sust == 1)
p.pop("mods_magia", None)

print(f"\nTask1: {PASS} passou, {FAIL} falhou")
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_ficha_totais.py`
Expected: FALHA com `AttributeError: 'GameRoom' object has no attribute '_weapon_damage_breakdown'`

- [ ] **Step 3: Implementar os helpers**

Em `server.py`, logo abaixo de `_player_effective_ac` (procure `def _player_effective_ac(self, p):`), adicionar:

```python
    def _sustained_dano_bonus(self, p):
        """Bônus de dano SUSTENTADO (não dobrado por crítico) — compartilhado
        entre handle_attack (rolagem real) e o display da ficha."""
        gl_dano = (p.get("guerreiro_luz_bonus", {}).get("dano", 0)
                   if p.get("guerreiro_luz_ativo") else 0)
        return (self._modificador_sobrevivencia(p)
                + self._cancao_bonus(p, "bonus_dano")
                + gl_dano
                + self._mod_magia(p, "dano")
                - self._corrosao_arma_pen(p))

    def _weapon_damage_breakdown(self, p):
        """Estrutura de dano para a ficha (sem alvo). die + flat_bonus sustentado
        + dados extras sustentados + condicionais (fora do número principal)."""
        weapon = p.get("weapon")
        die = weapon.get("die") if weapon else None
        if weapon and weapon.get("finesse"):
            stat_bonus = max(mod(p.get("str_", 12)), mod(p.get("dex", 12)))
            stat_label = "finesse"
        elif weapon and die:
            stat_bonus = mod(p.get(weapon["stat"], 12))
            stat_label = weapon["stat"]
        else:
            stat_bonus = mod(p.get("str_", 12))      # desarmado: base 1 + FOR
            stat_label = "str_"
        weapon_plus = weapon.get("dano_bonus", 0) if weapon else 0   # hook arma mágica futura
        flat = stat_bonus + weapon_plus + self._sustained_dano_bonus(p)
        extra_dice = []
        if p.get("golpe_sagrado_ativo"):
            extra_dice.append({"die": "1d8", "label": "Golpe Sagrado",
                               "note": "dobra vs morto-vivo/demônio"})
        conditionals = []
        if p.get("class_id") == "rogue":
            nd4 = self._dados_furtivo(p.get("level", 1))
            conditionals.append({"text": f"+{nd4}d4 furtivo",
                                 "note": "se aliado adjacente ao alvo ou invisível"})
        return {"die": die, "stat": stat_label, "flat_bonus": flat,
                "extra_dice": extra_dice, "conditionals": conditionals}
```

- [ ] **Step 4: Refatorar `handle_attack` para usar o helper (parity)**

Em `handle_attack`, no ramo armado, substituir a linha:
```python
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") - self._corrosao_arma_pen(p))
```
por:
```python
                    dmg = max(1, dmg + self._sustained_dano_bonus(p))
```
E no ramo desarmado, substituir:
```python
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano + self._mod_magia(p, "dano"))
```
por:
```python
                    dmg = max(1, dmg + self._sustained_dano_bonus(p))
```
(`_corrosao_arma_pen` retorna 0 quando desarmado, então a soma fica idêntica.)

- [ ] **Step 5: Rodar o teste e ver passar**

Run: `python tools/test_ficha_totais.py`
Expected: PASS em todos os checks da Task1; saída `Task1: N passou, 0 falhou`

- [ ] **Step 6: Sanidade — testes de combate existentes ainda passam**

Run: `python tools/test_ogro.py && python tools/test_devorador.py`
Expected: ambos terminam sem `❌` (exit 0). Garante que o refactor de `handle_attack` não mudou o dano.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_ficha_totais.py
git commit -m "feat(server): breakdown de dano sustentado compartilhado para a ficha"
```

---

## Task 2: Servidor — effective_ac + ac_breakdown + payload enriquecido

**Files:**
- Modify: `server.py` (`_ac_breakdown`, `_players_for_state`; `push_state`)
- Test: `tools/test_ficha_totais.py` (adicionar bloco Task2)

- [ ] **Step 1: Escrever o teste falhando**

Adicionar ao final de `tools/test_ficha_totais.py`, ANTES da linha `print(f"\nTask1: ...")` mude para um print final único. Substitua o bloco final por:

```python
# ── Breakdown de CA ───────────────────────────────────────────────────────
r2 = setup(); q = mk(r2, "mage")           # cajado_madeira; CA base do mago
base_ac = q["ac"]
bdca = r2._ac_breakdown(q)
check("breakdown começa com Base", bdca[0]["label"] == "Base" and bdca[0]["value"] == base_ac)

# def. temporária com duração → badge com turns
r2.temp_def[q["id"]] = 3
r2.temp_def_turnos[q["id"]] = 2
eff = r2._player_effective_ac(q)
bdca = r2._ac_breakdown(q)
temp = next((e for e in bdca if e["label"] == "Temporário"), None)
check("badge Temporário existe", temp is not None and temp["value"] == 3)
check("badge Temporário tem turns=2", temp and temp.get("turns") == 2)
check("effective_ac = soma do breakdown",
      eff == sum(e["value"] for e in bdca))

# magia de CA → badge com rodadas
r2.temp_def.pop(q["id"], None); r2.temp_def_turnos.pop(q["id"], None)
r2._set_mod_magia(q, {"ca": -2}, 4)
bdca = r2._ac_breakdown(q)
mg = next((e for e in bdca if e["label"] == "Magia"), None)
check("badge Magia negativo", mg is not None and mg["value"] == -2)
check("badge Magia tem turns das rodadas", mg and mg.get("turns") == 4)

# payload enriquecido
players = r2._players_for_state()
pl = players[0]
check("payload tem effective_ac", "effective_ac" in pl)
check("payload tem ac_breakdown", "ac_breakdown" in pl)
check("payload tem weapon_damage", "weapon_damage" in pl)
check("enrich não muta o dict vivo", "effective_ac" not in r2.players[q["id"]])

print(f"\nTotal: {PASS} passou, {FAIL} falhou")
sys.exit(1 if FAIL else 0)
```

(E remova o `print(f"\nTask1: ...")` / `sys.exit` antigos do final da Task1.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_ficha_totais.py`
Expected: FALHA com `AttributeError: ... '_ac_breakdown'`

- [ ] **Step 3: Implementar `_ac_breakdown` e `_players_for_state`**

Em `server.py`, abaixo de `_weapon_damage_breakdown`, adicionar:

```python
    def _ac_breakdown(self, p):
        """Lista de modificadores de CA ativos para os badges da ficha. Soma das
        entradas == _player_effective_ac(p)."""
        out = [{"label": "Base", "value": p["ac"]}]
        mm = self._mod_magia(p, "ca")
        if mm:
            out.append({"label": "Magia", "value": mm,
                        "turns": (p.get("mods_magia") or {}).get("rodadas")})
        td = self.temp_def.get(p["id"], 0)
        if td:
            out.append({"label": "Temporário", "value": td,
                        "turns": self.temp_def_turnos.get(p["id"], 1)})
        cc = self._cancao_bonus(p, "bonus_ca")
        if cc:
            out.append({"label": "Canção", "value": cc})
        gl = (p.get("guerreiro_luz_bonus", {}).get("ca", 0)
              if p.get("guerreiro_luz_ativo") else 0)
        if gl:
            out.append({"label": "Guerreiro da Luz", "value": gl})
        cor = self._corrosao_ca_pen(p)
        if cor:
            out.append({"label": "Corrosão", "value": -cor})
        return out

    def _players_for_state(self):
        """Cópia rasa de cada jogador com os totais efetivos da ficha anexados —
        sem poluir o dict vivo (que carrega estado autoritativo)."""
        out = []
        for p in self.players.values():
            pc = dict(p)
            pc["effective_ac"]  = self._player_effective_ac(p)
            pc["ac_breakdown"]  = self._ac_breakdown(p)
            pc["weapon_damage"] = self._weapon_damage_breakdown(p)
            out.append(pc)
        return out
```

- [ ] **Step 4: Usar o payload enriquecido em `push_state`**

Em `push_state`, trocar:
```python
            "players": list(self.players.values()),
```
(a ocorrência dentro de `push_state`, ~`"type": "game_state"`) por:
```python
            "players": self._players_for_state(),
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_ficha_totais.py`
Expected: `Total: N passou, 0 falhou`

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_ficha_totais.py
git commit -m "feat(server): envia effective_ac, ac_breakdown e weapon_damage no game_state"
```

---

## Task 3: Cliente — `GS.weaponRangeTiles` (lógica pura de alcance + reach)

**Files:**
- Modify: `src/gameState.js` (nova função + export no objeto retornado)
- Modify: `game.js` (trocar chamadas; remover `_computeWeaponRangeTiles`)

Hoje `_computeWeaponRangeTiles` (em `game.js`) trata melee só como 4 ortogonais. Vamos movê-la para `gameState.js` e adicionar as formas de reach espelhando o servidor (`_lanca_no_alcance_jogador`, `_cajado_no_alcance_jogador`).

- [ ] **Step 1: Adicionar `weaponRangeTiles` em `gameState.js`**

Em `src/gameState.js`, dentro do IIFE `const GS = (() => {` (perto de `function hasLineOfSight(...)`), adicionar:

```javascript
  // Conjunto de tiles atacáveis pela arma equipada a partir da casa do herói.
  // Espelha as formas do servidor: ranged = Chebyshev≤range com LOS; lança =
  // 2 ortogonais retos (sem parede no meio) / 1 diagonal; cajado/reach = Chebyshev 1;
  // melee com range explícito = Chebyshev≤range com LOS; melee padrão = 4 ortogonais.
  function weaponRangeTiles(state, me) {
    const result = new Set();
    if (!state || !state.tiles || !me || !me.pos) return result;
    const tiles = state.tiles;
    const H = tiles.length, W = tiles[0].length;
    const [px, py] = me.pos;
    const explored = new Set((state.explored || []).map(([x, y]) => `${x},${y}`));
    // TILE_FLOOR já está no escopo do IIFE (== 1). Uma casa é "passável" para o
    // realce de alcance se for piso explorado (a prévia não atravessa parede/porta).
    const blocked = (x, y) =>
      y < 0 || x < 0 || y >= H || x >= W || tiles[y][x] !== TILE_FLOOR;
    const ok = (x, y) =>
      !blocked(x, y) && explored.has(`${x},${y}`) && !(x === px && y === py);
    const w = me.weapon || {};
    const range = (w.range != null) ? w.range : null;
    const reach = w.reach || null;

    if (range != null) {                                  // ranged ou melee com range
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (!ok(x, y)) continue;
        if (Math.max(Math.abs(px - x), Math.abs(py - y)) <= range
            && hasLineOfSight(state, px, py, x, y)) result.add(`${x},${y}`);
      }
    } else if (reach === 'lanca') {                       // 2 retos / 1 diagonal
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const m1x = px + dx, m1y = py + dy;
        if (ok(m1x, m1y)) result.add(`${m1x},${m1y}`);
        const m2x = px + dx * 2, m2y = py + dy * 2;        // 2 casas só se a do meio for piso
        if (!blocked(m1x, m1y) && ok(m2x, m2y)) result.add(`${m2x},${m2y}`);
      }
      for (const [dx, dy] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
        if (ok(px + dx, py + dy)) result.add(`${px + dx},${py + dy}`);
    } else if (reach === 'cajado') {                      // Chebyshev 1
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++)
        if (ok(px + dx, py + dy)) result.add(`${px + dx},${py + dy}`);
    } else {                                              // melee padrão: 4 ortogonais
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]])
        if (ok(px + dx, py + dy)) result.add(`${px + dx},${py + dy}`);
    }
    return result;
  }
```

E no objeto retornado pelo IIFE (onde aparece `hasLineOfSight,`), adicionar a linha:
```javascript
    weaponRangeTiles,
```

- [ ] **Step 2: Trocar as chamadas em `game.js` e remover a função antiga**

Em `game.js`, na função `renderMap` (procure `_computeWeaponRangeTiles(state, me)`), trocar:
```javascript
  const weaponRangeTiles = (window._weaponRangePreview && me && !isAnimadosTurn2D)
    ? _computeWeaponRangeTiles(state, me) : new Set();
```
por:
```javascript
  const weaponRangeTiles = (window._weaponRangePreview && me && !isAnimadosTurn2D)
    ? GS.weaponRangeTiles(state, me) : new Set();
```

Na parte 3D (procure a outra ocorrência `_computeWeaponRangeTiles`, dentro do bloco `if(g3.weaponRangeMeshes)`), trocar:
```javascript
    const wRngTiles = (window._weaponRangePreview && me)
      ? _computeWeaponRangeTiles(state, me) : new Set();
```
por:
```javascript
    const wRngTiles = (window._weaponRangePreview && me)
      ? GS.weaponRangeTiles(state, me) : new Set();
```

Depois, remover a definição inteira de `function _computeWeaponRangeTiles(state, me) { ... }` em `game.js` (o bloco entre `function _computeWeaponRangeTiles` e o `}` que o fecha, logo acima de `function renderMap`).

- [ ] **Step 3: Verificar no browser (sem regressão de alcance)**

Iniciar o preview e abrir o jogo:
- `preview_start` (servir o projeto), entrar numa partida com um herói melee (ex.: warrior).
- Passar o mouse no slot de arma do **inventário** (que já dispara a prévia) e confirmar via `preview_screenshot` que os quadrados vermelhos aparecem nas 4 casas ortogonais (melee padrão).
- Trocar para um herói/arma de alcance (mago com cajado) e confirmar que a prévia mostra as 8 casas Chebyshev-1.
- `preview_console_logs`: nenhum erro `GS.weaponRangeTiles is not a function` ou `_computeWeaponRangeTiles is not defined`.

- [ ] **Step 4: Commit**

```bash
git add src/gameState.js game.js
git commit -m "refactor(client): move alcance de arma p/ GS.weaponRangeTiles + reach correto"
```

---

## Task 4: Cliente — ícone ⚔ ARMA com expressão consolidada

**Files:**
- Modify: `game.js` (`renderMyPanel`: cálculo de `dmgFmt` e o HTML do `equip-stat` da arma)

- [ ] **Step 1: Construir a expressão a partir de `me.weapon_damage`**

Em `game.js`, dentro de `renderMyPanel`, na seção `// ── Weapon info ──`, substituir todo o bloco que define `dmgFmt` (de `let dmgFmt = '—';` até o fim do `else { ... dmgFmt = ... }`) por:

```javascript
  // Expressão de dano consolidada — fonte: server (me.weapon_damage). Skills
  // ARMADAS do warrior (Golpe Devastador ×2) são estado do cliente e entram aqui.
  let dmgFmt = '—', dmgBuffed = false;
  const wd = me.weapon_damage;
  if (wd) {
    const fb = wd.flat_bonus || 0;
    const head = wd.die ? wd.die : '1';
    let expr = `${head} ${fb >= 0 ? '+' : ''}${fb}`;
    for (const e of (wd.extra_dice || [])) expr += ` +${e.die}`;
    // Golpe Devastador armado (warrior): dobra os dados → sufixo ×2
    const armadas = (typeof GS !== 'undefined' && GS.getWarriorSelected) ? GS.getWarriorSelected() : [];
    if (armadas.includes('golpe_devastador')) { expr += ' ×2'; dmgBuffed = true; }
    if (fb !== 0 || (wd.extra_dice || []).length) dmgBuffed = true;
    // condicionais (furtivo) como termo marcado, fora do número principal
    for (const c of (wd.conditionals || [])) expr += ` <span style="opacity:.7">(${c.text})</span>`;
    dmgFmt = expr;
  } else {
    // Fallback defensivo (estado pré-patch): dado + mod do atributo da arma
    const _w = (me.weapon && me.weapon.die) ? me.weapon : null;
    const _m = Math.floor(((me[(_w && _w.stat) || 'str_'] ?? 10) - 10) / 2);
    dmgFmt = `${_w ? _w.die : '1'} ${_m >= 0 ? '+' : ''}${_m}`;
  }
```

- [ ] **Step 2: Atualizar o HTML do `equip-stat` da arma (remover tags antigos)**

Em `renderMyPanel`, no HTML do bloco `equip-row`, trocar a linha do dano da arma:
```javascript
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">${dmgFmt}${_cancaoTag('bonus_dano')}${_richardTag('dano')}${_golpeSagradoTag()}</div>
```
por:
```javascript
        <div class="equip-stat" style="color:${dmgBuffed ? '#f8e08a' : '#f8c840'};font-size:.72rem;">${dmgFmt}</div>
```

(Os bônus agora estão consolidados na expressão — Canção/Guerreiro da Luz no `flat_bonus`, Golpe Sagrado em `extra_dice`. Os helpers `_cancaoTag`/`_richardTag`/`_golpeSagradoTag` continuam usados em OUTROS lugares do painel; não remover as definições.)

- [ ] **Step 3: Verificar no browser**

- Entrar com o **warrior** (machado 1d6, FOR 18): a ficha deve mostrar `1d6 +4`. `preview_screenshot`.
- Entrar com **Richard (paladin)** e ativar Golpe Sagrado (`golpe_sagrado`): deve aparecer ` +1d8` na expressão. `preview_screenshot`.
- Com o warrior, armar **Golpe Devastador**: a expressão ganha ` ×2`. `preview_screenshot`.
- `preview_console_logs`: sem erros.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(client): icone de arma mostra dano efetivo consolidado"
```

---

## Task 5: Cliente — ícone 🛡 ARMADURA com CA efetiva + badges

**Files:**
- Modify: `game.js` (`renderMyPanel`: badges de CA e headline do `equip-stat` da armadura; chip CA do `combat-row`)

- [ ] **Step 1: Construir os badges de CA a partir de `me.ac_breakdown`**

Em `game.js`, dentro de `renderMyPanel`, logo após a seção `// ── Armor info ──`, adicionar:

```javascript
  // CA efetiva (server) + badges por modificador ativo. Fallback: me.ac.
  const effAc = (me.effective_ac != null) ? Number(me.effective_ac) : vAc;
  const acBadges = (me.ac_breakdown || [])
    .filter(e => e.label !== 'Base' && e.value)
    .map(e => {
      const pos = e.value > 0;
      const sinal = pos ? '+' : '−';
      const mag = Math.abs(e.value);
      const cor = pos ? '#7fd0ff' : '#ff7b6b';
      const turns = (e.turns != null) ? ` <span style="opacity:.7">(${e.turns}t)</span>` : '';
      return `<span title="${e.label}" style="color:${cor};font-weight:bold;font-size:.78em;margin-left:3px;">${sinal}${mag}${turns}</span>`;
    }).join('');
```

- [ ] **Step 2: Usar `effAc` + badges no ícone de armadura e no chip CA**

No HTML do `equip-row`, trocar a linha da CA da armadura:
```javascript
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">CA ${vAc}</div>
```
por:
```javascript
        <div class="equip-stat" style="color:#f8c840;font-size:.72rem;">CA ${effAc}${acBadges}</div>
```

E no `combat-row`, trocar o chip CA:
```javascript
        <b style="color:#f8d040;font-size:1.1rem;">${vAc}${_cancaoTag('bonus_ca')}${_richardTag('ca')}</b>
```
por:
```javascript
        <b style="color:#f8d040;font-size:1.1rem;">${effAc}${acBadges}</b>
```

- [ ] **Step 3: Verificar no browser**

- Mago: ficha mostra `CA <base>` sem badges quando não há buffs. `preview_screenshot`.
- Lançar uma defesa temporária no mago (ou simular `temp_def`) e confirmar `CA` maior + badge `+N (Xt)` com o contador. Avançar uma rodada e ver o contador diminuir. `preview_screenshot`.
- Aplicar um efeito que reduz CA (ex.: magia `ca` negativa) e ver badge vermelho `−N`.
- `preview_console_logs`: sem erros.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(client): icone de armadura mostra CA efetiva com badges de modificadores"
```

---

## Task 6: Cliente — hover no ícone ⚔ ARMA destaca o alcance

**Files:**
- Modify: `game.js` (`renderMyPanel`: handlers de hover no `.equip-item` da arma após `$('my-stats').innerHTML = ...`)

O destaque já existe via `window._weaponRangePreview` + `GS.weaponRangeTiles`. Falta ligar o hover ao ícone ⚔ ARMA da ficha (hoje só o slot de inventário dispara).

- [ ] **Step 1: Anexar handlers ao bloco da arma**

Em `game.js`, em `renderMyPanel`, logo após o ponto em que o HTML é injetado em `#my-stats` (procure o final do `if (me.class_id === 'mage') { ... } else if (me.class_id === 'cleric') { ... } else { $('my-stats').innerHTML = statsHTML; }`), adicionar:

```javascript
  // Hover no ícone ⚔ ARMA da ficha → destaca o alcance no mapa (2D e 3D).
  const _armaIcon = document.querySelector('#my-stats .equip-row .equip-item:first-child');
  if (_armaIcon && me.weapon && me.weapon.die) {
    _armaIcon.style.cursor = 'help';
    _armaIcon.addEventListener('mouseenter', () => {
      window._weaponRangePreview = true;
      if (GS.gameState) renderMap(GS.gameState);
    });
    _armaIcon.addEventListener('mouseleave', () => {
      window._weaponRangePreview = false;
      if (GS.gameState) renderMap(GS.gameState);
    });
  }
```

(O primeiro `.equip-item` do `.equip-row` é o da arma — ver a ordem no HTML do `equip-row`: arma vem antes da armadura.)

- [ ] **Step 2: Verificar no browser**

- Warrior: passar o mouse sobre o ícone ⚔ ARMA (não o slot de inventário) → 4 casas ortogonais em vermelho. `preview_screenshot`.
- Equipar uma **lança** (reach lanca) e confirmar 2 casas em linha reta + diagonais. Equipar um **arco** e confirmar o raio com linha de visão (paredes cortam).
- Tirar o mouse → o destaque some. `preview_console_logs`: sem erros.

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(client): hover no icone de arma da ficha destaca o alcance"
```

---

## Verificação final (após todas as tasks)

- [ ] `python tools/test_ficha_totais.py` → `Total: N passou, 0 falhou`
- [ ] `python tools/test_ogro.py` e `python tools/test_devorador.py` → sem `❌` (parity de combate intacta)
- [ ] Preview: ficha do warrior/mago/paladin mostra expressão de dano consolidada; ativar Canção (Henrique no grupo)/Golpe Sagrado/Abençoar muda o número; CA mostra badges com contador; hover na arma pinta o alcance correto por tipo de arma; sem erros no console.
