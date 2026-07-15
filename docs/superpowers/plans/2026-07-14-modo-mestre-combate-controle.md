# Modo Mestre — Combate ao Avistar, Controle Manual e Ficha do Monstro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o controle de monstros pelo mestre realmente jogável — monstros acordam ao serem avistados por um herói (só com mestre), entram em Manual por padrão, e o mestre os dirige na sequência de turnos — além de mostrar a imagem do mestre na seleção e uma ficha do monstro ao clicar.

**Architecture:** Servidor (`server.py`): um flag `alertado` por monstro + o helper `_monstro_ativo_em_combate` decidem se um monstro age/é-controlável; `_verificar_avistamento` (chamado após passo de herói e ao abrir porta) acorda a sala inteira quando um herói tem linha de visão a um monstro, setando `control_mode="manual"`. Tudo gateado por `_mestre_ativo()` — sem mestre, o comportamento é byte-idêntico ao de hoje (dormência por sala-trancada). Cliente (`game.js`): imagem do mestre na seleção + ficha do monstro ao clicar (puro cliente; os stats já chegam no `game_state`).

**Tech Stack:** Python 3 + `websockets` (servidor headless; testes `tools/test_*.py`), Vanilla JS (`src/gameState.js`, `game.js`, `game.css`). Sem bundler, sem framework de teste JS.

**Convenção:** localize cada edição pela **assinatura da função** + **string âncora**, não por número de linha (`server.py`/`game.js` são grandes). Só faça `git add` dos arquivos que você tocou; `git status` antes de cada commit. Spec: `docs/superpowers/specs/2026-07-14-modo-mestre-combate-controle-design.md`.

---

## Estrutura de arquivos

- **Modificar** `server.py`:
  - novos helpers `_heroi_enxerga_monstro`, `_monstro_ativo_em_combate`, `_verificar_avistamento`.
  - `handle_move` (após `_aplicar_fogueira_se_pisar`, antes do `push_state`) — chama `_verificar_avistamento`.
  - `handle_open_door` (após o loop `for r in locked_owners`, antes do `push_state`) — chama `_verificar_avistamento`.
  - `gm_phase` — troca a checagem de sala-trancada por `_monstro_ativo_em_combate`.
  - `monster_step` (em `_activate_initiative_actor`) — pula monstro não-ativo.
- **Modificar** `tools/test_modo_mestre.py` — testes novos.
- **Modificar** `game.js` — imagem do mestre na seleção (`_csApplyMasterMode`), ficha do monstro (`renderFichaMonstro` + ramo de mestre em `handleTileClick` + clique nas linhas do HUD).
- **Modificar** `game.css` — estilos da imagem do mestre e da ficha do monstro.

Nenhuma mudança de servidor para a ficha do monstro (os stats já são enviados). Todos os caminhos novos são no-op quando `_mestre_ativo()` é falso.

---

## Task 1: Helpers de atividade em combate (`alertado`)

**Files:** Modify `server.py` (novos `_heroi_enxerga_monstro`, `_monstro_ativo_em_combate`). Test: `tools/test_modo_mestre.py`.

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()` de `tools/test_modo_mestre.py`, antes do print final:

```python
    print("\n[12] _monstro_ativo_em_combate — sem mestre = sala-trancada (byte-idêntico)")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = None   # sem mestre
    r.rooms = [{"id": 1, "locked": True}, {"id": 2, "locked": False}]
    m_trancado = {"id": "g1", "hp": 8, "pos": [1, 1], "room_id": 1}
    m_aberto   = {"id": "g2", "hp": 8, "pos": [2, 2], "room_id": 2}
    m_sem_sala = {"id": "g3", "hp": 8, "pos": [3, 3]}
    check("sem mestre: monstro em sala trancada NÃO ativo", r._monstro_ativo_em_combate(m_trancado) is False)
    check("sem mestre: monstro em sala aberta ativo", r._monstro_ativo_em_combate(m_aberto) is True)
    check("sem mestre: monstro sem sala ativo", r._monstro_ativo_em_combate(m_sem_sala) is True)

    print("\n[12b] _monstro_ativo_em_combate — com mestre = flag alertado")
    r.master_pid = "m1"; r.connections["m1"] = object()
    check("com mestre: não-alertado NÃO ativo", r._monstro_ativo_em_combate(m_aberto) is False)
    m_aberto["alertado"] = True
    check("com mestre: alertado ativo", r._monstro_ativo_em_combate(m_aberto) is True)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL em [12] — `_monstro_ativo_em_combate` não existe.

- [ ] **Step 3: Implementar**

Adicione os dois helpers ao `GameRoom`, perto de `_monstro_enxerga_alvo` (busque `def _monstro_enxerga_alvo`):

```python
    def _heroi_enxerga_monstro(self, hero, m):
        """True se o herói tem linha de visão ao monstro (visão do HERÓI: raio +
        LOS + oclusão por objetos altos). Base do 'avistar' que inicia o combate."""
        if not m.get("pos") or not hero.get("pos"):
            return False
        hx, hy = hero["pos"]; mx, my = m["pos"]
        if max(abs(hx - mx), abs(hy - my)) > self._get_raio_visao(hero):
            return False
        if not self._tem_linha_de_visao([hx, hy], [mx, my]):
            return False
        return not self._tall_oclui_caminho(hx, hy, mx, my)

    def _monstro_ativo_em_combate(self, m):
        """Um monstro age / é controlável / é alvo?
        COM mestre: só se já foi 'alertado' (avistado). SEM mestre: comportamento
        de hoje — ativo a menos que sua sala esteja trancada (byte-idêntico)."""
        if self._mestre_ativo():
            return bool(m.get("alertado"))
        room_m = self._room_by_id(m.get("room_id"))
        return not (room_m and room_m.get("locked"))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py` → PASS em [12]/[12b]. Também `python tools/test_guilda.py` → 44/0.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): helpers _heroi_enxerga_monstro + _monstro_ativo_em_combate (flag alertado)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Despertar por avistamento (`_verificar_avistamento`) + hooks

**Files:** Modify `server.py` (novo `_verificar_avistamento`; chamadas em `handle_move` e `handle_open_door`). Test: `tools/test_modo_mestre.py`.

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()`:

```python
    print("\n[13] _verificar_avistamento acorda a sala e seta Manual (só com mestre)")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    r.players = {"hA": {"id": "hA", "pos": [0, 0], "alive": True, "connected": True}}
    m1 = {"id": "g1", "hp": 8, "pos": [5, 5], "room_id": 7}
    m2 = {"id": "g2", "hp": 8, "pos": [6, 5], "room_id": 7}   # mesma sala
    m3 = {"id": "g3", "hp": 8, "pos": [9, 9], "room_id": 8}   # outra sala
    r.monsters = {"g1": m1, "g2": m2, "g3": m3}
    # stub do avistamento: o herói só enxerga g1
    r._heroi_enxerga_monstro = lambda hero, m: (m["id"] == "g1")
    await r._verificar_avistamento()
    check("g1 alertado", m1.get("alertado") is True)
    check("g2 (mesma sala) alertado", m2.get("alertado") is True)
    check("g3 (outra sala) NÃO alertado", m3.get("alertado") is not True)
    check("g1 vira Manual", m1.get("control_mode") == "manual")
    check("g2 vira Manual", m2.get("control_mode") == "manual")

    print("\n[13b] idempotente + só-mestre")
    chamadas = {"n": 0}
    _orig = r.gm_say
    async def _cnt(*a, **k): chamadas["n"] += 1
    r.gm_say = _cnt
    await r._verificar_avistamento()   # tudo já alertado → não re-narra
    check("não re-narra sala já acordada", chamadas["n"] == 0)
    r.gm_say = _orig
    # sem mestre: no-op
    r.master_pid = None
    m4 = {"id": "g4", "hp": 8, "pos": [1, 1], "room_id": 9}
    r.monsters["g4"] = m4
    r._heroi_enxerga_monstro = lambda hero, m: True
    await r._verificar_avistamento()
    check("sem mestre: não acorda", m4.get("alertado") is not True)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py` → FAIL em [13] — `_verificar_avistamento` não existe.

- [ ] **Step 3: Implementar**

Adicione o método ao `GameRoom`, perto dos helpers da Task 1:

```python
    async def _verificar_avistamento(self):
        """Só-mestre: se um herói vivo avista um monstro dormente, acorda a SALA
        inteira dele (alertado=True) e o coloca em Manual. Idempotente."""
        if not self._mestre_ativo():
            return
        herois = [p for p in self.players.values() if self._ativo(p)]
        if not herois:
            return
        salas_narradas = set()
        for m in list(self.monsters.values()):
            if m.get("hp", 0) <= 0 or m.get("alertado"):
                continue
            if not any(self._heroi_enxerga_monstro(h, m) for h in herois):
                continue
            rid = m.get("room_id")
            grupo = ([mm for mm in self.monsters.values()
                      if mm.get("hp", 0) > 0 and mm.get("room_id") == rid]
                     if rid is not None else [m])
            for mm in grupo:
                if not mm.get("alertado"):
                    mm["alertado"] = True
                    mm["control_mode"] = "manual"   # mestre dirige por padrão
            chave = rid if rid is not None else id(m)
            if chave not in salas_narradas:
                salas_narradas.add(chave)
                await self.gm_say("⚔️ **Combate!** Os monstros perceberam os heróis!")
```

Em `handle_move`, o fim é (âncora `await self._aplicar_fogueira_se_pisar(p)` seguido de `await self.push_state()`):

```python
        # Fogueira: 1d4 de fogo ao entrar.
        if p["alive"]:
            await self._aplicar_fogueira_se_pisar(p)

        await self.push_state()
```

Insira a checagem de avistamento entre a fogueira e o `push_state`:

```python
        # Fogueira: 1d4 de fogo ao entrar.
        if p["alive"]:
            await self._aplicar_fogueira_se_pisar(p)

        await self._verificar_avistamento()   # Modo Mestre: herói pode ter avistado monstros
        await self.push_state()
```

Em `handle_open_door`, o fim é (âncora `for r in locked_owners:` … seguido de `await self.push_state()`):

```python
        for r in locked_owners:
            r["locked"] = False
            self._reveal_room(r)
            key = "room_" + r["role"]
            if key in GM:
                await self.gm_say(gm(key))
        await self.push_state()
```

Insira a checagem antes do `push_state`:

```python
        for r in locked_owners:
            r["locked"] = False
            self._reveal_room(r)
            key = "room_" + r["role"]
            if key in GM:
                await self.gm_say(gm(key))
        await self._verificar_avistamento()   # sala revelada → herói avista → combate
        await self.push_state()
```

> Se o corpo real de `handle_move`/`handle_open_door` divergir das âncoras citadas, PARE e reporte NEEDS_CONTEXT com o trecho real — não adivinhe o ponto de inserção.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py` → PASS até [13b]. `python tools/test_guilda.py` → 44/0.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): despertar por avistamento acorda a sala + Manual por padrao

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Despacho pula monstro não-ativo (dormência generalizada)

**Files:** Modify `server.py` (`gm_phase`, `monster_step` em `_activate_initiative_actor`). Test: `tools/test_modo_mestre.py`.

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()`:

```python
    print("\n[14] monstro não-alertado (com mestre) é pulado no despacho")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    m = {"id": "g1", "hp": 8, "pos": [1, 1], "room_id": 5, "control_mode": "manual"}
    r.monsters = {"g1": m}
    # dormente (sem alertado) → o helper diz inativo, então o despacho deve pular
    check("dormente não é ativo", r._monstro_ativo_em_combate(m) is False)
    m["alertado"] = True
    check("acordado é ativo", r._monstro_ativo_em_combate(m) is True)
```

> O pulo em si (não abrir a janela Manual / não rodar `gm_phase`) é comportamento assíncrono do laço de iniciativa; este teste trava o **predicado** que o despacho consulta. O comportamento ponta-a-ponta é validado in-app na Task 6.

- [ ] **Step 2: Rodar e ver falhar/passar**

Run: `python tools/test_modo_mestre.py` — [14] já passa com o helper da Task 1 (é uma checagem de guarda). Se falhar, o helper regrediu.

- [ ] **Step 3: Implementar o pulo no despacho**

**3a.** Em `gm_phase`, a checagem de dormência atual é (âncora `room_m = self._room_by_id(m.get("room_id"))` seguido de `if room_m and room_m.get("locked"):`):

```python
            room_m = self._room_by_id(m.get("room_id"))
            if room_m and room_m.get("locked"):
                continue
```

Troque pela checagem generalizada:

```python
            if not self._monstro_ativo_em_combate(m):
                continue
```

> Sem mestre, `_monstro_ativo_em_combate` retorna exatamente `not (room_m and room_m.get("locked"))` → o `continue` dispara nos mesmos casos de hoje (byte-idêntico). Com mestre, pula os não-alertados.

**3b.** Em `monster_step` (dentro de `_activate_initiative_actor`), o corpo atual é (âncora `async def monster_step(mid):`):

```python
        async def monster_step(mid):
            monster = self.monsters.get(mid)
            if monster and monster.get("hp", 0) > 0:
                mode = monster.get("control_mode", "auto") if self._mestre_ativo() else "auto"
                if mode == "manual":
                    await self._master_manual_window(monster)
                else:
                    await self.gm_phase(monster)   # auto e semi (semi força o alvo em _get_monster_primary_target)
            await self._advance_initiative()
        self.initiative_task = asyncio.create_task(monster_step(actor["id"]))
```

Adicione a guarda de atividade logo após pegar o monstro vivo, para não abrir a janela Manual de um monstro dormente:

```python
        async def monster_step(mid):
            monster = self.monsters.get(mid)
            if monster and monster.get("hp", 0) > 0 and self._monstro_ativo_em_combate(monster):
                mode = monster.get("control_mode", "auto") if self._mestre_ativo() else "auto"
                if mode == "manual":
                    await self._master_manual_window(monster)
                else:
                    await self.gm_phase(monster)   # auto e semi (semi força o alvo em _get_monster_primary_target)
            await self._advance_initiative()
        self.initiative_task = asyncio.create_task(monster_step(actor["id"]))
```

> Sem mestre, `_monstro_ativo_em_combate` = a regra de sala-trancada. Antes, um monstro em sala trancada chegava no `monster_step` e `gm_phase(monster)` o pulava internamente (via a checagem trocada em 3a); agora ele é pulado um passo antes, com o mesmo efeito líquido (nenhuma ação) — e a iniciativa avança igual. Comportamento observável idêntico sem mestre.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py` → tudo PASS. `python tools/test_guilda.py` → 44/0. `python tools/test_devorador.py` → esperado passar (regressão de IA de monstro).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): despacho pula monstro dormente via _monstro_ativo_em_combate

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Imagem do mestre na seleção de personagem (cliente)

**Files:** Modify `game.js` (`_csApplyMasterMode`), `game.css`. Sem harness de teste JS → verificação in-app.

- [ ] **Step 1: Estender `_csApplyMasterMode`**

O corpo atual é (âncora `function _csApplyMasterMode(){`):

```javascript
function _csApplyMasterMode(){
  const jaMestre = GS.isMaster();
  const panel   = document.getElementById('cs-panel');
  const confirm = document.getElementById('cs-confirm-wrap');
  const hint    = document.getElementById('cs-hint');
  const infoBtn = document.getElementById('cs-info-btn');
  if(panel)   panel.style.display   = jaMestre ? 'none' : '';
  if(confirm) confirm.style.display = jaMestre ? 'none' : '';
  if(infoBtn) infoBtn.style.display = jaMestre ? 'none' : '';
  if(hint) hint.textContent = jaMestre
    ? '🎭 Você é o Mestre — controlará os monstros na masmorra.'
    : 'Escolha seu herói — toque para selecionar';
}
```

Adicione a troca do carrossel (`#cs-canvas`) pela imagem do mestre. Substitua a função por:

```javascript
function _csApplyMasterMode(){
  const jaMestre = GS.isMaster();
  const panel   = document.getElementById('cs-panel');
  const confirm = document.getElementById('cs-confirm-wrap');
  const hint    = document.getElementById('cs-hint');
  const infoBtn = document.getElementById('cs-info-btn');
  if(panel)   panel.style.display   = jaMestre ? 'none' : '';
  if(confirm) confirm.style.display = jaMestre ? 'none' : '';
  if(infoBtn) infoBtn.style.display = jaMestre ? 'none' : '';
  if(hint) hint.textContent = jaMestre
    ? '🎭 Você é o Mestre — controlará os monstros na masmorra.'
    : 'Escolha seu herói — toque para selecionar';
  // Carrossel 3D de peões ↔ imagem do mestre
  const canvas = document.getElementById('cs-canvas');
  let mimg = document.getElementById('cs-master-portrait');
  if(jaMestre && !mimg){
    mimg = document.createElement('div');
    mimg.id = 'cs-master-portrait';
    mimg.innerHTML =
      '<img src="assets/portraits/mestre_do_jogo.jpeg" alt="Mestre do Jogo">' +
      '<div class="cs-master-cap">📖 Mestre do Jogo</div>';
    // insere no mesmo container do canvas
    if(canvas && canvas.parentNode) canvas.parentNode.appendChild(mimg);
  }
  if(canvas) canvas.style.display = jaMestre ? 'none' : '';
  if(mimg)   mimg.style.display   = jaMestre ? 'flex' : 'none';
}
```

- [ ] **Step 2: CSS**

Em `game.css`, adicione (perto de outros estilos de `cs-`):

```css
#cs-master-portrait{
  position:absolute; inset:0; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:12px; z-index:3;
}
#cs-master-portrait img{
  max-width:70%; max-height:70%; object-fit:contain;
  border:2px solid var(--gold); border-radius:12px;
  box-shadow:0 8px 40px rgba(0,0,0,.6);
}
#cs-master-portrait .cs-master-cap{
  font-size:1.3rem; color:var(--gold); font-weight:bold; letter-spacing:.5px;
}
```

> `#cs-canvas` fica dentro de um container posicionado; `position:absolute; inset:0` faz a imagem cobrir a mesma área. Se o layout real precisar de ajuste (o container do canvas não é `position:relative`), ajuste o container — confira com o app.

- [ ] **Step 3: Verificação in-app**

`node --check game.js`. Depois, no app (ver Task 6 para subir o servidor do worktree/repo): entre no lobby, clique "🎭 Assumir como Mestre" → na área da seleção, o carrossel de peões some e aparece a imagem `mestre_do_jogo.jpeg` com a legenda; clicar de novo (virar herói) traz o carrossel de volta.

- [ ] **Step 4: Commit**

```bash
git add game.js game.css
git commit -m "feat(mestre): imagem do mestre na selecao (troca o carrossel de peoes)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Ficha do monstro ao clicar (cliente)

**Files:** Modify `game.js` (`renderFichaMonstro` novo; ramo de mestre em `handleTileClick`; clique nas linhas de `renderMasterHud`), `game.css`. Verificação in-app.

- [ ] **Step 1: `renderFichaMonstro(m)` + `#ficha-monstro`**

Adicione em `game.js` (perto de `renderMasterHud`, busque `function renderMasterHud`):

```javascript
  function renderFichaMonstro(m){
    if(!m){ return; }
    let host = document.getElementById('ficha-monstro');
    if(!host){ host = document.createElement('div'); host.id = 'ficha-monstro'; document.body.appendChild(host); }
    host.style.display = 'block';
    const linhaAtaque = (a) => {
      const dano = a.damage || a.dano || '';
      const b = (a.atk_bonus!=null) ? (a.atk_bonus>=0?'+':'')+a.atk_bonus : '';
      return `<div class="fm-atk">⚔️ ${a.name||a.nome||'Ataque'} ${b} · ${dano}</div>`;
    };
    const linhaHab = (h) => `<div class="fm-hab"><b>${h.name||h.nome||h.id}</b> — ${h.descricao||h.desc||''}</div>`;
    const ataques = (m.attacks||[]).map(linhaAtaque).join('') ||
                    (m.atk_bonus!=null ? linhaAtaque({name:'Ataque', atk_bonus:m.atk_bonus, damage:m.damage}) : '');
    const habs = (m.special_abilities||[]).map(linhaHab).join('');
    const stat = (lbl,v)=> (v!=null? `<span class="fm-stat">${lbl} ${v}</span>` : '');
    host.innerHTML =
      `<div class="fm-head"><span class="fm-emoji">${m.emoji||'👾'}</span>`+
      `<span class="fm-nome">${m.name||m.type||'Monstro'}</span>`+
      `<button class="fm-close" title="Fechar">✕</button></div>`+
      `<div class="fm-vitais">❤️ ${m.hp}/${m.max_hp||m.hp} · 🛡️ CA ${m.ac??'—'} · 👣 ${m.movement??'—'}</div>`+
      `<div class="fm-stats">${stat('FOR',m.str_)}${stat('DES',m.dex)}${stat('CON',m.con_)}${stat('INT',m.int_)}`+
      `${stat('Fort',m.fort)}${stat('Ref',m.ref_)}${stat('Von',m.will)}</div>`+
      (ataques? `<div class="fm-sec">Ataques</div>${ataques}`:'')+
      (habs? `<div class="fm-sec">Habilidades</div>${habs}`:'');
    host.querySelector('.fm-close').onclick = () => { host.style.display='none'; };
  }
  function _monstroEmCasa(tx, ty){
    const st = GS.gameState; if(!st) return null;
    return (st.monsters||[]).find(m => m.hp>0 && m.pos && m.pos[0]===tx && m.pos[1]===ty) || null;
  }
```

> `_monstroEmCasa` usa a âncora (`m.pos`) do monstro. Monstros multi-casa (footprint) só respondem na casa-âncora — aceitável para a Fase A (nota no plano); refine com `GS.decorTilesOf`-style se necessário depois.

- [ ] **Step 2: Ramo de mestre em `handleTileClick`**

No início de `handleTileClick(tx, ty)` (âncora `function handleTileClick(tx, ty){` … logo após `if(!podeReceberInput()) return;`), adicione o ramo do mestre ANTES de qualquer lógica de herói (magia/itens/baús):

```javascript
function handleTileClick(tx, ty){
  getAudioContext();
  if(!podeReceberInput()) return;
  // ── Mestre: clicar num monstro abre a ficha; o mestre não faz ações de herói ──
  if(GS.isMaster()){
    const mon = _monstroEmCasa(tx, ty);
    if(mon) renderFichaMonstro(mon);
    return;
  }
```

Mantenha o resto da função inalterado. (Sem essa guarda, o mestre cairia na lógica de magia/itens de herói, que não se aplica a ele.)

- [ ] **Step 3: Clique nas linhas do HUD abre a ficha**

Em `renderMasterHud`, a linha do monstro tem um `onclick` que faz toggle de seleção (âncora `if(_masterSel.has(mid)) _masterSel.delete(mid); else _masterSel.add(mid);`). Adicione a abertura da ficha junto do toggle. O bloco atual é:

```javascript
      if(_masterSel.has(mid)) _masterSel.delete(mid); else _masterSel.add(mid);
```

Envolva para também abrir a ficha (mantendo a seleção):

```javascript
      if(_masterSel.has(mid)) _masterSel.delete(mid); else _masterSel.add(mid);
      const _mon = (GS.gameState.monsters||[]).find(x=>x.id===mid);
      if(_mon) renderFichaMonstro(_mon);
```

> Verifique o nome exato da variável do id na linha (`mid`) ao implementar; se for outro (ex.: `m.id`), use-o.

- [ ] **Step 4: Esconder a ficha fora do jogo / quando não-mestre**

Onde a HUD do mestre é escondida para não-mestres (na render do painel do herói, busque `getElementById('hud-mestre')` com `display='none'`), esconda também `#ficha-monstro`. Adicione ao lado:

```javascript
    const _fm = document.getElementById('ficha-monstro'); if(_fm) _fm.style.display='none';
```

- [ ] **Step 5: CSS**

Em `game.css`:

```css
#ficha-monstro{
  position:fixed; left:12px; bottom:12px; width:280px; z-index:60;
  background:var(--dark-panel,rgba(20,16,12,.96)); border:1px solid var(--border,#5a4632);
  border-radius:10px; padding:10px 12px; color:var(--text,#e8ddc8);
  box-shadow:0 6px 30px rgba(0,0,0,.6); font-size:.86rem; display:none;
}
#ficha-monstro .fm-head{ display:flex; align-items:center; gap:8px; font-weight:bold; }
#ficha-monstro .fm-emoji{ font-size:1.4rem; }
#ficha-monstro .fm-nome{ flex:1; color:var(--gold,#d9b45a); }
#ficha-monstro .fm-close{ background:none; border:none; color:var(--text2,#a89878); cursor:pointer; font-size:1rem; }
#ficha-monstro .fm-vitais{ margin:6px 0; }
#ficha-monstro .fm-stats{ display:flex; flex-wrap:wrap; gap:4px 10px; margin-bottom:4px; }
#ficha-monstro .fm-stat{ opacity:.85; font-size:.8rem; }
#ficha-monstro .fm-sec{ color:var(--gold,#d9b45a); font-weight:bold; margin:6px 0 2px; border-top:1px solid var(--border,#5a4632); padding-top:4px; }
#ficha-monstro .fm-atk, #ficha-monstro .fm-hab{ margin:2px 0; line-height:1.3; }
```

- [ ] **Step 6: Verificação in-app** (Task 6)

`node --check game.js`. No app, como mestre, clicar num monstro (tabuleiro) e numa linha do HUD abre a ficha com HP/CA/ataques/habilidades; ✕ fecha; a ficha some ao voltar pra cidade / virar herói.

- [ ] **Step 7: Commit**

```bash
git add game.js game.css
git commit -m "feat(mestre): ficha do monstro ao clicar (HP, ataques, habilidades)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Verificação in-app do ciclo completo (2 clientes)

**Files:** nenhum (verificação). Requer subir o servidor DESTE repositório (`python server.py` na raiz do repo onde este plano roda) na porta 8765, e 2 abas de navegador.

> **Aprendizado da Fase A:** `preview_start` roda o `server.py` da RAIZ do projeto. Garanta que a porta 8765 esteja livre (feche outros servidores) e que o servidor servido seja o DESTA branch. Confirme via `curl -s http://localhost:8765/src/gameState.js | grep -c renderFichaMonstro` (deve ser ≥1 se o game.js certo estiver sendo servido — ajuste o alvo do grep conforme o arquivo).

- [ ] **Step 1:** Suba o servidor e abra 2 abas. Aba A = herói (crie a sala, escolha guerreiro). Aba B = mestre (entre na sala pelo código, clique "Assumir como Mestre" → confira a imagem do mestre).
- [ ] **Step 2:** Inicie o jogo (host) e entre na masmorra. Na aba B (mestre): confirme visão sem névoa + HUD do mestre.
- [ ] **Step 3:** Na aba A (herói), ande até **avistar** um monstro (linha de visão). Confirme no log a narração "⚔️ Combate!" e que os monstros da sala viraram **manual** (badge no HUD do mestre) e `alertado`.
- [ ] **Step 4:** Encerre o turno do herói até a iniciativa chegar num monstro. Confirme que a **janela Manual abre na aba B** (setas/atacar/encerrar), que mover/atacar funciona e que "Encerrar monstro" avança a iniciativa.
- [ ] **Step 5:** Clique num monstro (tabuleiro e HUD) na aba B → confirme a **ficha do monstro** com HP/CA/ataques/habilidades.
- [ ] **Step 6:** Confirme que um monstro **não avistado** (em sala ainda não vista) permanece parado e não abre janela Manual quando sua iniciativa chega (é pulado).
- [ ] **Step 7:** Registre o resultado (screenshots/observações). Sem commit (é verificação).

---

## Task 7: Documentação (CLAUDE.md)

**Files:** Modify `CLAUDE.md`.

- [ ] **Step 1:** Atualize a nota da mensagem `open_door` e a nota de arquitetura do Modo Mestre para refletir: monstros acordam por **avistamento** (linha de visão) além de abrir porta, acordam a sala inteira, e entram em **Manual** por padrão — **só quando há mestre** (sem mestre, dormência por sala-trancada, byte-idêntica). Cite `_verificar_avistamento`/`_monstro_ativo_em_combate`/`_heroi_enxerga_monstro`, a flag `alertado`, a imagem `assets/portraits/mestre_do_jogo.jpeg` na seleção e a ficha do monstro (`renderFichaMonstro`, puro cliente). Aponte o teste `tools/test_modo_mestre.py` e a spec `docs/superpowers/specs/2026-07-14-modo-mestre-combate-controle-design.md`.

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mestre): combate ao avistar + Manual por padrao + ficha do monstro"
```

---

## Self-Review (do autor do plano)

**Cobertura da spec:**
- §1 Despertar por LOS → Task 1 (`_heroi_enxerga_monstro`/`_monstro_ativo_em_combate`) + Task 2 (`_verificar_avistamento` + hooks) + Task 3 (despacho pula dormente). ✓
- §2 Acorda em Manual → Task 2 (seta `control_mode="manual"` no despertar). ✓
- §3 Garantir o fluxo → Task 6 (verificação in-app do ciclo). ✓
- §4 Imagem do mestre → Task 4. ✓
- §5 Ficha do monstro → Task 5. ✓
- Escopo só-mestre → gateado por `_mestre_ativo()` em `_monstro_ativo_em_combate`/`_verificar_avistamento`; testes [12]/[13b] provam no-op sem mestre. ✓
- Não-regressão sem mestre → [12] (byte-idêntico) + regressão guilda/devorador nas Tasks. ✓

**Consistência de nomes:** `alertado`, `_heroi_enxerga_monstro`, `_monstro_ativo_em_combate`, `_verificar_avistamento`, `renderFichaMonstro`, `_monstroEmCasa`, `#ficha-monstro`, `#cs-master-portrait` — usados consistentemente. Reusa `_get_raio_visao`, `_tem_linha_de_visao`, `_tall_oclui_caminho`, `_room_by_id`, `_mestre_ativo`, `_ativo`, `renderMasterHud`, `_csApplyMasterMode`, `handleTileClick` (todos verificados existentes).

**Riscos sinalizados:** (1) âncoras de `handle_move`/`handle_open_door` — implementador deve parar se divergirem; (2) LOS herói→monstro usa a visão do herói (não a de `_monstro_enxerga_alvo`, que é do monstro) — decisão registrada; (3) monstros multi-casa respondem só na âncora na ficha/clique — aceito p/ Fase A; (4) porta 8765 / servidor certo na verificação in-app.
