# Camada B — Reforços do Mestre — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que o mestre (Modo Mestre Jogador) implante monstros de reforço, de uma reserva definida pelo autor da fase, em qualquer casa livre durante a partida.

**Architecture:** O autor grava `master_reinforcements: [{type,count}]` na masmorra (editor). Ao entrar na dungeon o servidor materializa `self.master_reserve` (dict `type→count`). Uma nova mensagem `mestre_implantar_reforco` cria o monstro via `make_monster` (nasce `alertado`+`manual`), que entra sozinho na iniciativa da próxima rodada via o `_rebuild_initiative` já existente. Tudo condicionado a `_mestre_ativo()` — sem mestre, byte-idêntico. O HUD do mestre ganha uma seção "Reforços" e um modo de clique-para-implantar.

**Tech Stack:** Python (`server.py`, `websockets`), Vanilla JS (`game.js`, `src/gameState.js`), editor Vanilla JS (`tools/editor.js`/`.html`). Testes: `tools/test_modo_mestre.py` (harness caseiro com `check(name, cond)`).

**Spec:** `docs/superpowers/specs/2026-07-15-modo-mestre-camada-b-reforcos-design.md`

---

## File Structure

- **Modify `server.py`** — estado (`self.master_reserve`), carga da masmorra, `validar_dungeon`, helper `_tile_livre_para_reforco`, handler `handle_mestre_implantar_reforco`, dispatch, serialização em `push_state`.
- **Modify `tools/test_modo_mestre.py`** — novas seções de teste (servidor autoritativo).
- **Modify `src/gameState.js`** — sender `mestreImplantarReforco` + export.
- **Modify `game.js`** — seção "Reforços" no HUD do mestre + modo implantar em `handleTileClick`.
- **Modify `tools/editor.js`** — estado + serialização (save/load) + painel "Reforços do Mestre".
- **Modify `tools/editor.html`** — container do painel.
- **Modify `CLAUDE.md`** — nota de protocolo + arquitetura.

**Protocolo (nota de nomenclatura):** o envelope de mensagem já usa a chave `type` para o NOME da mensagem. Portanto o tipo do monstro viaja como **`monster_type`** (não `type`) em `mestre_implantar_reforco` para evitar colisão.

---

## Task 1: Servidor — estado da reserva + carga da masmorra + serialização

**Files:**
- Modify: `server.py` (`__init__` ~4507; bloco de carga da dungeon ~6294; `push_state` ~17298)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao final de `main()` em `tools/test_modo_mestre.py` (antes do bloco de impressão do total), uma função helper e uma seção. Cole o helper logo após os imports/helpers do topo (perto de `def lobby_room()`):

```python
def playing_room_com_mestre():
    """Sala em fase 'playing' com um mestre conectado e mapa mínimo."""
    r = lobby_room()
    r.phase = "playing"
    r.master_pid = "m1"; r.master_name = "Mestre"
    r.connections["m1"] = object()   # mestre conectado → _mestre_ativo() True
    r.map_w = 10; r.map_h = 10
    r.tiles = [[S.FLOOR]*10 for _ in range(10)]
    r.rooms = []
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    return r
```

E a seção de teste dentro de `main()`:

```python
    print("\n[16] Reforços — carga da reserva")
    r = playing_room_com_mestre()
    defn = {"master_reinforcements": [{"type": "goblin", "count": 2},
                                      {"type": "orc", "count": 1},
                                      {"type": "goblin", "count": 3}]}
    r._carregar_master_reserve(defn)
    check("goblin soma 2+3=5", r.master_reserve.get("goblin") == 5)
    check("orc = 1", r.master_reserve.get("orc") == 1)
    r._carregar_master_reserve({"master_reinforcements": [{"type": "tipo_inexistente", "count": 9}]})
    check("tipo inválido é ignorado", "tipo_inexistente" not in r.master_reserve)
    r._carregar_master_reserve({})
    check("sem campo → reserva vazia", r.master_reserve == {})
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL com `AttributeError: 'GameRoom' object has no attribute '_carregar_master_reserve'`.

- [ ] **Step 3: Implementar**

Em `server.py`, no `__init__` da `GameRoom`, logo após `self.master_manual_mid = None` (~linha 4509), adicione:

```python
        self.master_reserve = {}   # Camada B: type→count restante de reforços do mestre
```

Adicione o método de carga (coloque perto dos outros helpers do mestre, ex.: após `_mestre_ativo`):

```python
    def _carregar_master_reserve(self, defn):
        """Materializa a reserva de reforços do mestre a partir do defn da masmorra
        (Camada B). type→count restante. Tipos desconhecidos e counts ≤0 são
        ignorados. Inerte sem mestre (só é lido em handle_mestre_implantar_reforco)."""
        reserve = {}
        for entry in (defn.get("master_reinforcements") or []):
            if not isinstance(entry, dict):
                continue
            t = entry.get("type")
            try:
                c = int(entry.get("count", 0) or 0)
            except (TypeError, ValueError):
                c = 0
            if c > 0 and any(d["type"] == t for d in MONSTER_DEFS):
                reserve[t] = reserve.get(t, 0) + c
        self.master_reserve = reserve
```

No bloco de carga da dungeon, logo após o loop que carrega os monstros (após `self.monsters[m["id"]] = m`, ~linha 6294), chame:

```python
        # Reforços do Mestre (Camada B) — reserva inerte sem mestre.
        self._carregar_master_reserve(defn)
```

Em `push_state` (~linha 17298), logo após a linha `"master_manual_mid": self.master_manual_mid,`, adicione a serialização enriquecida (name/emoji para o HUD não precisar de catálogo no cliente):

```python
            "master_reserve": [
                {"type": t, "count": c,
                 "name":  next((d.get("name", t)  for d in MONSTER_DEFS if d["type"] == t), t),
                 "emoji": next((d.get("emoji", "👾") for d in MONSTER_DEFS if d["type"] == t), "👾")}
                for t, c in self.master_reserve.items()
            ],
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção [16]; total sobe.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): carrega reserva de reforcos (master_reserve) + serializa no game_state"
```

---

## Task 2: Servidor — validação em `validar_dungeon`

**Files:**
- Modify: `server.py` (`validar_dungeon` ~2869, após a validação de `decorations`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione em `main()` de `tools/test_modo_mestre.py`:

```python
    print("\n[17] Reforços — validar_dungeon")
    base = {"schema_version": 1, "grid": {"w": 8, "h": 8},
            "tiles": [[0]*8 for _ in range(8)],
            "entrance": {"x": 1, "y": 1}}
    def _com_reinf(rf):
        d = dict(base); d["master_reinforcements"] = rf; return d
    ok, _ = S.validar_dungeon(_com_reinf([{"type": "goblin", "count": 2}]))
    check("reforço válido aceito", ok is True)
    ok, msg = S.validar_dungeon(_com_reinf([{"type": "naoexiste", "count": 1}]))
    check("tipo inexistente rejeitado", ok is False and "desconhecido" in msg.lower())
    ok, msg = S.validar_dungeon(_com_reinf([{"type": "goblin", "count": 0}]))
    check("count < 1 rejeitado", ok is False)
    ok, _ = S.validar_dungeon(_com_reinf("naoelista"))
    check("não-lista rejeitada", ok is False)
```

> Nota: `validar_dungeon` já valida `entrance`/`grid`; o `base` acima é o mínimo que passa nas checagens anteriores. Se o teste falhar por uma checagem anterior (ex.: chão alcançável), ajuste `tiles`/`entrance` para satisfazê-la — o alvo aqui é só o bloco de `master_reinforcements`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — hoje `validar_dungeon` aceita qualquer `master_reinforcements` (não valida), então "tipo inexistente rejeitado" e "count < 1 rejeitado" falham.

- [ ] **Step 3: Implementar**

Em `server.py`, dentro de `validar_dungeon`, logo após o bloco que valida `decorations` (após a linha que trata `decors`/`ocupadas`, antes do `return True, ...` final), adicione:

```python
    reinf = defn.get("master_reinforcements", [])
    if not isinstance(reinf, list):
        return False, "master_reinforcements deve ser uma lista."
    _valid_monster_types = {d["type"] for d in MONSTER_DEFS}
    for entry in reinf:
        if not isinstance(entry, dict):
            return False, "cada reforço deve ser um objeto JSON."
        if entry.get("type") not in _valid_monster_types:
            return False, f"reforço com tipo de monstro desconhecido: {entry.get('type')!r}."
        c = entry.get("count")
        if not isinstance(c, int) or isinstance(c, bool) or c < 1:
            return False, f"reforço com count inválido: {c!r} (inteiro ≥ 1)."
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção [17].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): valida master_reinforcements em validar_dungeon"
```

---

## Task 3: Servidor — helper de casa livre + handler de implante + dispatch

**Files:**
- Modify: `server.py` (helper perto de `_free_drop_tile_near` ~7292; handler perto de `handle_mestre_encerrar_monstro` ~8798; dispatch ~18185)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione em `main()` de `tools/test_modo_mestre.py`:

```python
    print("\n[18] Reforços — implante")
    r = playing_room_com_mestre()
    r.master_reserve = {"goblin": 2}
    await r.handle_mestre_implantar_reforco("m1", "goblin", 4, 4)
    novos = [m for m in r.monsters.values() if m["pos"] == [4, 4]]
    check("monstro criado na casa", len(novos) == 1)
    check("nasce alertado", novos[0].get("alertado") is True)
    check("nasce em manual", novos[0].get("control_mode") == "manual")
    check("reserva decrementou", r.master_reserve.get("goblin") == 1)
    check("entra no rebuild de iniciativa", (
        r._rebuild_initiative() or True) and
        any(e["id"] == novos[0]["id"] for e in r.initiative_order))

    # esgotar remove a chave
    await r.handle_mestre_implantar_reforco("m1", "goblin", 5, 5)
    check("reserva zerada remove a chave", "goblin" not in r.master_reserve)

    # recusas
    r2 = playing_room_com_mestre(); r2.master_reserve = {"goblin": 1}
    r2.monsters["x"] = {"id": "x", "pos": [4, 4], "hp": 5}   # casa ocupada
    await r2.handle_mestre_implantar_reforco("m1", "goblin", 4, 4)
    check("recusa casa ocupada (não decrementa)", r2.master_reserve.get("goblin") == 1)
    await r2.handle_mestre_implantar_reforco("m1", "orc", 6, 6)
    check("recusa tipo fora da reserva", "orc" not in [m.get("type") for m in r2.monsters.values()])
    await r2.handle_mestre_implantar_reforco("naomestre", "goblin", 6, 6)
    check("recusa quem não é mestre", r2.master_reserve.get("goblin") == 1)

    # sem mestre conectado → no-op
    r3 = playing_room_com_mestre(); r3.master_reserve = {"goblin": 1}
    del r3.connections["m1"]   # mestre não conectado → _mestre_ativo() False
    await r3.handle_mestre_implantar_reforco("m1", "goblin", 6, 6)
    check("sem mestre ativo → não implanta", r3.master_reserve.get("goblin") == 1)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL com `AttributeError: 'GameRoom' object has no attribute 'handle_mestre_implantar_reforco'`.

- [ ] **Step 3: Implementar**

Em `server.py`, adicione o helper de casa livre logo após `_free_drop_tile_near` (~linha 7292):

```python
    def _tile_livre_para_reforco(self, tx, ty):
        """True se (tx,ty) é chão livre para implantar um reforço: dentro do mapa,
        não bloqueada por parede/porta/decoração sólida (_blocks_tile) e sem
        monstro/jogador vivo, baú ou item no chão. Espelha _free_drop_tile_near
        para uma casa ESCOLHIDA."""
        if not (0 <= tx < self.map_w and 0 <= ty < self.map_h):
            return False
        if self._blocks_tile(tx, ty):
            return False
        occupied = {tuple(m["pos"]) for m in self.monsters.values() if m.get("hp", 0) > 0}
        occupied |= {tuple(c["pos"]) for c in self.chests.values()}
        occupied |= {tuple(g["pos"]) for g in self.ground_items.values()}
        occupied |= {tuple(pp["pos"]) for pp in self.players.values() if pp.get("alive")}
        return (tx, ty) not in occupied
```

Adicione o handler logo após `handle_mestre_encerrar_monstro` (~linha 8798):

```python
    async def handle_mestre_implantar_reforco(self, pid, monster_type, tx, ty):
        """Mestre implanta um reforço da reserva numa casa livre (ação livre, a
        qualquer momento). O monstro nasce alertado+manual e entra na iniciativa
        da próxima rodada via _rebuild_initiative. Só com mestre ativo."""
        if pid != self.master_pid or not self._mestre_ativo():
            return
        if self.phase != "playing":
            return
        if self.master_reserve.get(monster_type, 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Sem reforços desse tipo na reserva."}); return
        mdef = next((d for d in MONSTER_DEFS if d["type"] == monster_type), None)
        if not mdef:
            await self.send_to(pid, {"type": "error", "msg": "Tipo de monstro inválido."}); return
        try:
            tx = int(tx); ty = int(ty)
        except (TypeError, ValueError):
            return
        if not self._tile_livre_para_reforco(tx, ty):
            await self.send_to(pid, {"type": "error", "msg": "Casa ocupada ou inválida para implantar."}); return
        sala = {"id": None, "cx": tx, "cy": ty}   # reforço não pertence a sala autorada
        m = make_monster(mdef, sala)
        m["pos"] = [tx, ty]
        m["alertado"] = True
        m["control_mode"] = "manual"
        self.monsters[m["id"]] = m
        self.master_reserve[monster_type] -= 1
        if self.master_reserve[monster_type] <= 0:
            del self.master_reserve[monster_type]
        await self.gm_say(f"⚠️ **Reforços!** Um(a) **{mdef.get('name', monster_type)}** entra na masmorra!")
        await self.push_state()
```

No dispatch de mensagens, logo após o ramo `elif t == "mestre_encerrar_monstro":` (~linha 18185), adicione:

```python
                elif t == "mestre_implantar_reforco":
                    if room: await room.handle_mestre_implantar_reforco(
                        pid, msg.get("monster_type"), msg.get("tx"), msg.get("ty"))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção [18].

- [ ] **Step 5: Rodar a regressão do servidor**

Run: `python tools/test_modo_mestre.py` (todas as seções) e `python tools/test_devorador.py`
Expected: sem falhas novas.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): handle_mestre_implantar_reforco + _tile_livre_para_reforco + dispatch"
```

---

## Task 4: Cliente — sender em `gameState.js`

**Files:**
- Modify: `src/gameState.js` (senders ~1285; export ~2113)

- [ ] **Step 1: Adicionar o sender**

Em `src/gameState.js`, logo após `function mestreEncerrarMonstro(...)` (perto da linha 1285, junto dos outros senders do mestre), adicione:

```javascript
  function mestreImplantarReforco(monsterType, tx, ty) {
    send({ type: 'mestre_implantar_reforco', monster_type: monsterType, tx, ty });
  }
```

No objeto exportado (perto de `mestreMoverMonstro,` na lista de exports ~linha 2113), adicione a linha:

```javascript
    mestreImplantarReforco,
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check src/gameState.js`
Expected: sem erro.

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(mestre): sender mestreImplantarReforco no gameState"
```

---

## Task 5: Cliente — seção "Reforços" no HUD + modo implantar

**Files:**
- Modify: `game.js` (`renderMasterHud` ~10105; `handleTileClick` ramo do mestre ~20860)

- [ ] **Step 1: Renderizar a seção "Reforços" no HUD do mestre**

Em `game.js`, dentro de `renderMasterHud(state)`, ache onde o HTML do painel é montado (a template string com `mestre-row`/`mestre-modos`). Adicione, ao final do HTML do painel (antes do fechamento que atribui a `host.innerHTML`), uma seção de reforços. Como a estrutura exata do template varia, gere a seção numa variável e concatene:

```javascript
  const reserva = state.master_reserve || [];
  const reforcoHtml = reserva.length ? (
    '<div class="mestre-reforcos"><div class="mestre-sec">⚠️ Reforços</div>' +
    reserva.map(r =>
      `<button class="mestre-reforco-btn${window._modoImplantarReforco === r.type ? ' armado' : ''}" data-rtype="${r.type}">` +
      `${r.emoji || '👾'} ${r.name || r.type} <b>×${r.count}</b></button>`
    ).join('') +
    (window._modoImplantarReforco ? '<div class="mestre-reforco-dica">Clique numa casa livre para implantar (Esc cancela)</div>' : '') +
    '</div>'
  ) : '';
```

Concatene `reforcoHtml` na `host.innerHTML` (adicione `+ reforcoHtml` ao final da atribuição do template do painel).

Depois do bloco que faz o wiring dos outros botões (perto de `host.querySelectorAll('.mestre-row')...`), adicione o wiring dos botões de reforço:

```javascript
  host.querySelectorAll('.mestre-reforco-btn').forEach(btn => {
    btn.onclick = () => {
      const t = btn.dataset.rtype;
      window._modoImplantarReforco = (window._modoImplantarReforco === t) ? null : t;
      renderMasterHud(GS.gameState);
    };
  });
```

- [ ] **Step 2: Tratar o clique no tabuleiro (modo implantar)**

Em `game.js`, em `handleTileClick(tx, ty)`, no ramo do mestre (o bloco `if(GS.isMaster()){ ... }` adicionado na fase de combate), troque o corpo para tratar o modo implantar ANTES de abrir a ficha:

```javascript
  if(GS.isMaster()){
    if(window._modoImplantarReforco){
      GS.mestreImplantarReforco(window._modoImplantarReforco, tx, ty);
      window._modoImplantarReforco = null;
      return;
    }
    const mon = _monstroEmCasa(tx, ty);
    if(mon) renderFichaMonstro(mon);
    return;
  }
```

- [ ] **Step 3: Cancelar o modo com Esc**

Ache o handler global de tecla Esc em `game.js` (busque por `'Escape'`). Adicione, junto das outras limpezas de modo (perto de onde `_modoMagia`/`_modoThrowItem` são zerados):

```javascript
    if(window._modoImplantarReforco){ window._modoImplantarReforco = null; if(GS.isMaster()) renderMasterHud(GS.gameState); }
```

- [ ] **Step 4: CSS mínimo (opcional, reusa estilos do HUD)**

Em `game.css`, perto dos estilos `.mestre-*`, adicione:

```css
.mestre-reforcos{ margin-top:6px; }
.mestre-reforco-btn{ display:block; width:100%; text-align:left; margin:2px 0; cursor:pointer; }
.mestre-reforco-btn.armado{ outline:2px solid var(--gold,#d9b45a); }
.mestre-reforco-dica{ font-size:.75rem; opacity:.85; margin-top:2px; }
```

- [ ] **Step 5: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem erro.

- [ ] **Step 6: Commit**

```bash
git add game.js game.css
git commit -m "feat(mestre): HUD de reforcos + modo implantar (clique no tabuleiro)"
```

---

## Task 6: Editor — estado + serialização + painel "Reforços do Mestre"

**Files:**
- Modify: `tools/editor.js` (estado `S` ~18; save ~1218; load ~1357; novo render)
- Modify: `tools/editor.html` (container do painel)

- [ ] **Step 1: Estado + serialização (save/load)**

Em `tools/editor.js`, no objeto de estado inicial `S` (~linha 18, junto de `secretPassages: []`), adicione:

```javascript
    masterReinforcements: [],
```

No objeto serializado do `save` (~linha 1218, junto de `secret_passages: ...`), adicione:

```javascript
      master_reinforcements: S.masterReinforcements.map(r => ({ type: r.type, count: r.count })),
```

No carregamento (~linha 1357, junto de `S.secretPassages = ...`), adicione:

```javascript
    S.masterReinforcements = (obj.master_reinforcements || [])
      .filter(r => r && r.type)
      .map(r => ({ type: r.type, count: Math.max(1, parseInt(r.count, 10) || 1) }));
```

- [ ] **Step 2: Container no HTML**

Em `tools/editor.html`, ache a barra lateral de ferramentas (onde ficam os painéis de monstros/objetivos). Adicione, seguindo o padrão dos painéis existentes:

```html
<div id="reinforce-panel" class="editor-panel">
  <h3>⚠️ Reforços do Mestre</h3>
  <div class="reinforce-add">
    <select id="reinforce-type"></select>
    <input id="reinforce-count" type="number" min="1" value="1" style="width:56px">
    <button id="reinforce-add-btn">+ Adicionar</button>
  </div>
  <ul id="reinforce-list"></ul>
</div>
```

- [ ] **Step 3: Render + wiring do painel**

Em `tools/editor.js`, adicione a função de render e o wiring (chame `renderReinforcements()` de onde os outros painéis são (re)desenhados, ex.: na função de refresh geral da UI; e popule o `<select>` no boot, junto de onde `CAT.monsters` já é usado para a paleta de monstros):

```javascript
  function renderReinforcements() {
    const sel = document.getElementById('reinforce-type');
    if (sel && !sel.dataset.filled) {
      sel.innerHTML = (CAT.monsters || [])
        .map(m => `<option value="${m.type || m.id}">${m.emoji || '👾'} ${m.name || m.type || m.id}</option>`)
        .join('');
      sel.dataset.filled = '1';
    }
    const list = document.getElementById('reinforce-list');
    if (!list) return;
    list.innerHTML = S.masterReinforcements.map((r, i) => {
      const meta = (CAT.monsters || []).find(m => (m.type || m.id) === r.type) || {};
      return `<li>${meta.emoji || '👾'} ${meta.name || r.type} ×${r.count}` +
             ` <button data-ri="${i}" class="reinforce-del">✕</button></li>`;
    }).join('');
    list.querySelectorAll('.reinforce-del').forEach(b => {
      b.onclick = () => { S.masterReinforcements.splice(+b.dataset.ri, 1); renderReinforcements(); };
    });
  }

  (function wireReinforcements() {
    const addBtn = document.getElementById('reinforce-add-btn');
    if (!addBtn) return;
    addBtn.onclick = () => {
      const type = document.getElementById('reinforce-type').value;
      const count = Math.max(1, parseInt(document.getElementById('reinforce-count').value, 10) || 1);
      if (!type) return;
      const existing = S.masterReinforcements.find(r => r.type === type);
      if (existing) existing.count += count;
      else S.masterReinforcements.push({ type, count });
      renderReinforcements();
    };
  })();
```

> Se o editor tiver uma função central de "refresh da UI" (busque por onde `renderDecorations`/painéis são chamados), adicione `renderReinforcements();` lá também, para o painel refletir o load de uma masmorra existente.

- [ ] **Step 4: Verificar sintaxe**

Run: `node --check tools/editor.js`
Expected: sem erro.

- [ ] **Step 5: Verificação manual rápida**

Abra o editor, adicione 2× goblin + 1× orc no painel, salve, recarregue a masmorra e confirme que o painel repovoa. (Sem harness automatizado para o editor.)

- [ ] **Step 6: Commit**

```bash
git add tools/editor.js tools/editor.html
git commit -m "feat(editor): painel Reforcos do Mestre (master_reinforcements)"
```

---

## Task 7: Documentação (CLAUDE.md)

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Nota de protocolo**

Em `CLAUDE.md`, na tabela **Client → Server**, logo após a linha `mestre_encerrar_monstro`, adicione:

```markdown
| `mestre_implantar_reforco` | `monster_type`, `tx`, `ty` — o mestre implanta um monstro da **reserva de reforços** (`master_reinforcements` da masmorra) numa casa livre. Ação livre, a qualquer momento; nasce `alertado`+`manual` e entra na iniciativa da próxima rodada. Só com mestre ativo. |
```

- [ ] **Step 2: Nota de arquitetura**

Adicione um parágrafo `>` após a nota "Modo Mestre — Combate ao avistar…":

```markdown
> **Modo Mestre — Camada B: Reforços do Mestre:** o autor grava
> `master_reinforcements: [{type,count}]` na masmorra (editor, painel "Reforços do
> Mestre"; validado em `validar_dungeon`). Ao entrar na dungeon o servidor
> materializa `self.master_reserve` (`type→count`, via `_carregar_master_reserve`;
> inerte sem mestre). A mensagem `mestre_implantar_reforco`
> (`handle_mestre_implantar_reforco`) cria o monstro via `make_monster` numa casa
> livre (`_tile_livre_para_reforco`, espelha `_free_drop_tile_near`), `alertado`+
> `manual`; ele entra sozinho na iniciativa da próxima rodada (`_rebuild_initiative`
> itera `self.monsters` fresco). `master_reserve` vai no `game_state` enriquecido com
> name/emoji para o HUD. Cliente: `GS.mestreImplantarReforco` + seção "Reforços" no
> `renderMasterHud` com modo de clique-para-implantar (`window._modoImplantarReforco`,
> tratado no ramo de mestre de `handleTileClick`). Só-mestre; sem mestre,
> byte-idêntico. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-15-modo-mestre-camada-b-reforcos*`.
> Teste: `tools/test_modo_mestre.py`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mestre): Camada B (Reforcos do Mestre) no CLAUDE.md"
```

---

## Ordem de execução e verificação final

1. Tasks 1→3 (servidor, TDD) — cada uma verde antes da próxima.
2. Task 4→5 (cliente) — `node --check` após cada.
3. Task 6 (editor) — `node --check` + verificação manual.
4. Task 7 (docs).
5. **Regressão final:** `python tools/test_modo_mestre.py` (todas as seções verdes) + `node --check game.js src/gameState.js tools/editor.js`.
6. Verificação in-app (2 clientes) fica para uma etapa manual, como nas fases anteriores do Modo Mestre.
