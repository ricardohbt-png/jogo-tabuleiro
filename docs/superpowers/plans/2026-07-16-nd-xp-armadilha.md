# ND/XP de Armadilha — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development ou executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Dar a cada armadilha autorada um `cr` (soma ao termômetro/minimapa da Camada C) e XP ao grupo quando vencida (desarmada ou disparada-e-sobrevivida).

**Architecture:** `cr` por tipo em `ARMADILHAS` + helpers `trap_cr`/`trap_xp` (server). XP dividido entre vivos, uma vez por armadilha (flag), no desarme e no disparo-sobrevivido. `cr` plumbado ao `game_state.armadilhas` (minimapa) e ao catálogo do editor (termômetro). `_crPorSalaMapa` (game.js) e `_ndPorSala` (editor.js) passam a somar as armadilhas por sala.

**Spec:** `docs/superpowers/specs/2026-07-16-nd-xp-armadilha-design.md`

**Base:** o WIP do usuário foi commitado (checkpoint). Implementar sobre a base limpa; `git add <arquivos específicos>`.

---

## Task 1: cr no catálogo + helpers `trap_cr`/`trap_xp` (servidor)

**Files:** `server.py` (`ARMADILHAS` ~3331; helpers perto de `monster_cr` ~4302). Test: `tools/test_modo_mestre.py`.

- [ ] **Step 1: Teste que falha** — em `main()`:
```python
    print("\n[21] ND/XP de armadilha — trap_cr/trap_xp")
    check("cr explícito", S.trap_cr({"cr": 0.5}) == 0.5)
    check("fallback por dificuldade", S.trap_cr({"dificuldade": 14}) == S.trap_cr({"dificuldade": 14}))
    check("fallback default", S.trap_cr({}) > 0)
    check("trap_xp deriva do cr", S.trap_xp(0.5) == round(0.5 * S.TRAP_XP_POR_CR))
    check("mina tem cr", S.trap_cr(S.ARMADILHAS["mina_terrestre"]) == 0.75)
    check("buraco tem cr", S.trap_cr(S.ARMADILHAS["buraco"]) == 0.1)
```

- [ ] **Step 2: Rodar e ver falhar** — `python tools/test_modo_mestre.py` → `AttributeError: trap_cr`.

- [ ] **Step 3: Implementar** — (a) adicionar `"cr": <v>` a cada tipo de `ARMADILHAS`: buraco 0.1, rede 0.15, armadilha_urso 0.25, fosso_estacas 0.35, nuvem_gas 0.4, fosso_envenenado 0.5, armadilha_incendiaria 0.5, mina_terrestre 0.75. Para os tipos novos (`armadilha_teletransporte`, `armadilha_dardos_envenenados`): teletransporte 0.4, dardos 0.4 (ajustável). (b) módulo-level, perto de `monster_cr`:
```python
TRAP_XP_POR_CR = 20

def trap_cr(meta):
    """cr unificado da armadilha (Camada C). cr explícito, senão fallback pela
    dificuldade do save (DC 8→0.1 … escala suave), senão default 0.3."""
    cr = meta.get("cr")
    if cr is not None:
        try: return float(cr)
        except (TypeError, ValueError): pass
    dif = meta.get("dificuldade")
    if isinstance(dif, (int, float)) and not isinstance(dif, bool):
        return max(0.1, min(1.0, round((dif - 8) / 6.0, 2)))
    return 0.3

def trap_xp(cr):
    return round(float(cr) * TRAP_XP_POR_CR)
```

- [ ] **Step 4: Rodar e ver passar** — seção [21] verde.

- [ ] **Step 5: Commit** — `git add server.py tools/test_modo_mestre.py` + `feat(mestre): cr/xp por tipo de armadilha (trap_cr/trap_xp)`.

---

## Task 2: Concessão de XP (desarme + disparo-sobrevivido)

**Files:** `server.py` (`_conceder_xp_armadilha` novo; hook em `handle_desarmar_armadilha` ~13784 e `_disparar_armadilha` ~13480). Test: `tools/test_modo_mestre.py`.

- [ ] **Step 1: Teste que falha** — usa um `playing_room_com_mestre()` ou room com 1 herói vivo; cria uma armadilha autorada; verifica:
```python
    print("\n[22] ND/XP de armadilha — concessão")
    r = playing_room_com_mestre()
    r.players["h"] = {"id":"h","name":"H","class_id":"warrior","alive":True,"hp":10,"pos":[1,1],"xp":0,"level":1}
    arm = {"id":"a1","tipo":"mina_terrestre","pos":[2,2]}
    xp0 = r.players["h"]["xp"]
    r._conceder_xp_armadilha(arm)
    check("XP concedido no 1º", r.players["h"]["xp"] > xp0)
    check("marca xp_concedido", arm.get("xp_concedido") is True)
    x1 = r.players["h"]["xp"]; r._conceder_xp_armadilha(arm)
    check("não concede 2ª vez", r.players["h"]["xp"] == x1)
    arm2 = {"id":"a2","tipo":"buraco","pos":[3,3],"aliada":True}
    xp_before = r.players["h"]["xp"]; r._conceder_xp_armadilha(arm2)
    check("aliada não concede", r.players["h"]["xp"] == xp_before)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar** — helper (perto de `_calc_monster_xp`):
```python
    def _conceder_xp_armadilha(self, arm, alvo=None):
        """XP de armadilha autorada, uma vez, dividido entre os heróis vivos."""
        if not arm or arm.get("aliada") or arm.get("xp_concedido"):
            return
        meta = ARMADILHAS.get(arm.get("tipo"))
        if not meta:
            return
        vivos = [p for p in self.players.values() if p.get("alive")]
        if not vivos:
            return
        total = trap_xp(trap_cr(meta))
        if total <= 0:
            arm["xp_concedido"] = True; return
        share = max(1, total // len(vivos))
        for p in vivos:
            p["xp"] = p.get("xp", 0) + share
        arm["xp_concedido"] = True
```
Hook no desarme (após `self.armadilhas = [a for a in self.armadilhas if a["id"] != arm["id"]]` no ramo de sucesso, ~13784):
```python
            self._conceder_xp_armadilha(arm)
```
Hook no disparo-sobrevivido: em `_disparar_armadilha`, ao FINAL do corpo (após aplicar efeitos), e antes dos `return` dos especiais, conceder se o alvo herói continua vivo:
```python
        if alvo.get("id") in self.players and alvo.get("alive"):
            self._conceder_xp_armadilha(arm, alvo)
```
(Colocar essa checagem em cada caminho de saída relevante do `_disparar_armadilha`: fim do ramo alvo-único, e antes dos `return` de teletransporte/dardos; para `area`, o `_aplicar_armadilha_area` chama por alvo — conceder lá se algum herói sobreviveu, uma vez via a flag.)
> Se o level-up automático depender de um método (ex. `_check_level_up`), chamá-lo após somar XP, reusando o mesmo do XP de monstro. Verificar o padrão no site de `p["xp"] += share_xp`.

- [ ] **Step 4: Rodar e ver passar.**

- [ ] **Step 5: Commit** — `git add server.py tools/test_modo_mestre.py` + `feat(mestre): XP de armadilha (desarme + disparo-sobrevivido, 1x, dividido)`.

---

## Task 3: cr na serialização de `game_state.armadilhas`

**Files:** `server.py` (serialização das armadilhas no `push_state`).

- [ ] **Step 1: Localizar** a serialização das armadilhas no payload de `push_state` (busca por onde `self.armadilhas` vira a lista enviada — filtro de visíveis). 

- [ ] **Step 2: Implementar** — incluir `cr` em cada item autorado: `"cr": (0 if a.get("aliada") else trap_cr(ARMADILHAS.get(a["tipo"], {})))`. (As `aliada` mandam 0 — não contam no minimapa.)

- [ ] **Step 3: Verificar** — `python -c "import ast; ast.parse(open('server.py',encoding='utf-8').read())"`.

- [ ] **Step 4: Commit** — `git add server.py` + `feat(mestre): cr das armadilhas no game_state`.

---

## Task 4: cr no catálogo do editor (export + regenerar)

**Files:** `tools/export_catalog.py` (~34); regenerar `tools/editor_catalog.js`.

- [ ] **Step 1: Implementar** — no bloco `traps` de `export_catalog.py`, adicionar `"cr": server.trap_cr(meta)` ao dict de cada trap.

- [ ] **Step 2: Regenerar** — `python tools/export_catalog.py`; conferir que uma trap tem `cr` no `editor_catalog.js`.

- [ ] **Step 3: Commit** — `git add tools/export_catalog.py tools/editor_catalog.js` + `feat(editor): cr das armadilhas no catalogo`.

---

## Task 5: Armadilhas no cr da sala (termômetro + minimapa)

**Files:** `game.js` (`_crPorSalaMapa`); `tools/editor.js` (`_ndPorSala`).

- [ ] **Step 1: game.js `_crPorSalaMapa`** — além de monstros, somar `cr` das armadilhas de `state.armadilhas` por sala. Como as armadilhas têm `pos` (não `room_id`), casar a `pos` à sala que a contém:
```javascript
  (state.armadilhas || []).forEach(function(a){
    var cr = a.cr || 0; if(!cr) return;
    total += cr;
    var r = (state.rooms||[]).find(function(rm){ return a.pos && a.pos[0]>=rm.x && a.pos[0]<rm.x+rm.w && a.pos[1]>=rm.y && a.pos[1]<rm.y+rm.h; });
    if(r && porRoom[r.id] != null) porRoom[r.id] += cr;
  });
```
(inserir dentro de `_crPorSalaMapa`, após o loop de monstros, antes de calcular `medio`.)

- [ ] **Step 2: editor.js `_ndPorSala`** — somar `cr` das `S.traps` (por `tipo` via `CAT.traps`) agrupadas por sala (pos→sala pelas `S.rooms`):
```javascript
    (S.traps || []).forEach(function(t){
      var meta = (CAT.traps || []).find(function(c){ return c.type === t.tipo || c.tipo === t.tipo; });
      var cr = meta ? (window.Difficulty ? window.Difficulty.crFromEntry(meta) : (meta.cr||0)) : 0;
      if(!cr) return;
      total += cr;
      var r = (S.rooms||[]).find(function(rm){ return t.pos && t.pos[0]>=rm.x && t.pos[0]<rm.x+rm.w && t.pos[1]>=rm.y && t.pos[1]<rm.y+rm.h; });
      var key = r ? r.id : "__none__";
      porSala[key] = (porSala[key] || 0) + cr;
    });
```
> Conferir os campos reais: `S.traps[i].tipo`/`.pos`, `CAT.traps[i].tipo`/`.cr`, e `S.rooms[i].{x,y,w,h,id}`. `Difficulty.crFromEntry` usa `.cr`/`.tier` — como trap não tem `tier`, garantir que use `.cr` (ou ler `meta.cr` direto).

- [ ] **Step 3: Verificar** — `node --check game.js tools/editor.js`.

- [ ] **Step 4: Commit** — `git add game.js tools/editor.js` + `feat(mestre): armadilhas somam ao cr da sala (termometro + minimapa)`.

---

## Task 6: Docs (CLAUDE.md)

- [ ] **Step 1** — nota curta na seção da Camada C: armadilhas têm `cr` (`trap_cr`/`trap_xp`), somam ao cr da sala no termômetro/minimapa, e dão XP (desarme/disparo-sobrevivido, 1x, dividido entre vivos); só autoradas.

- [ ] **Step 2: Commit** — `git add CLAUDE.md`.

---

## Verificação final
1. `python tools/test_modo_mestre.py` — seções [21]/[22] verdes, sem regressão.
2. `node --check game.js tools/editor.js`; `editor_catalog.js` regenerado com cr nas traps.
3. Verificação manual: armadilha numa sala aumenta o cr dela no termômetro/minimapa; desarmar/sobreviver dá XP uma vez.
