# Objetivos com XP/Recompensa + Deletar Salas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir deletar salas no editor e definir XP + recompensa (ouro/itens) por objetivo, com o XP/ouro divididos entre os heróis vivos, os itens largados num baú de recompensa, e o encerramento da fase passando a ser manual (botão com confirmação) em vez de automático.

**Architecture:** O editor (`tools/editor.js`, browser-only) ganha um botão de deletar sala e campos de XP/recompensa por objetivo, persistidos no JSON da masmorra. O servidor (`server.py`) generaliza a concessão de recompensa (dividindo XP/ouro entre vivos e largando itens num baú via `_spawn_chest`), remove a transição automática de fim de fase de `_check_objectives`, e expõe um flag `mission_complete_pending` + um novo handler `handle_encerrar_missao`. O cliente (`src/gameState.js` + `game.js`) expõe o flag e mostra um botão "Encerrar missão" com confirmação no HUD de objetivos.

**Tech Stack:** Python 3.x (`asyncio`, `websockets`) no servidor; Vanilla JS no cliente/editor; testes Python com o runner `check()`/`PASS`/`FAIL` caseiro em `tools/test_*.py` (NÃO pytest), rodados da raiz com `python tools/<arquivo>.py`.

---

## File Structure

- `server.py` (modificar) — concessão de recompensa por objetivo, flag/handler de encerramento manual, payload `game_state`, roteamento da mensagem.
- `tools/test_objetivos.py` (modificar) — atualizar testes do comportamento antigo (conclusão automática) + adicionar testes de XP/ouro dividido, baú de recompensa, flag e `encerrar_missao`.
- `src/gameState.js` (modificar) — getter `missionCompletePending` + sender `encerrarMissao`.
- `game.js` (modificar) — botão "Encerrar missão" no HUD de objetivos + confirmação.
- `tools/editor.js` (modificar) — deletar sala; editor de XP/recompensa por objetivo; persistência em `buildJSON`/`loadJSON`.
- `CLAUDE.md` (modificar) — protocolo (`encerrar_missao`) + nota de objetivos.

> **Nota sobre testes de cliente:** `editor.js`, `gameState.js` e `game.js` rodam só no browser e não têm harness de teste JS no projeto. Suas tarefas são verificadas por revisão de código + checagens manuais via `window.EDITOR` no console (descritas nos passos). Toda a lógica de jogo testável automaticamente fica no servidor (Tarefas 1–2), cobrindo o comportamento de ponta a ponta.

---

## Task 1: Servidor — concessão de recompensa por objetivo (XP/ouro divididos + itens acumulados)

Substitui `_conceder_bonus_secundario` por uma função geral que lê `xp` e `reward` do objetivo, divide XP e ouro entre os heróis vivos, e acumula os itens de recompensa numa lista (para o baú da Tarefa 2).

**Files:**
- Modify: `server.py` — adicionar `_resolve_reward_item` e `_conceder_objetivo_reward` ao lado de `_conceder_bonus_secundario` (≈12162-12170; o antigo é removido só na Tarefa 2).
- Test: `tools/test_objetivos.py` (novos testes `test_reward_dividido` e `test_reward_default_secundario`).

- [ ] **Step 1: Escrever o teste que falha**

Adicione esta função em `tools/test_objetivos.py` (antes de `async def main`):

```python
async def test_reward_dividido():
    print("\n[11] recompensa de objetivo: XP e ouro divididos entre os vivos + itens acumulados")
    r = setup_authored()
    r.dungeon_def["objectives"] = {
        "primary": {"type": "kill_all",
                    "xp": 100, "reward": {"gold": 80, "items": [{"id": "magic_sword"}]}},
        "secondary": []}
    await r.enter_dungeon("p1")
    p1, p2 = r.players["p1"], r.players["p2"]
    xp1, ouro1 = p1["xp"], p1["gold"]
    loot = []
    obj = r.objectives["primary"]
    await r._conceder_objetivo_reward(obj, is_primary=True, loot_acc=loot)
    # 2 heróis vivos: 100 XP -> 50 cada; 80 ouro -> 40 cada
    check("XP dividido entre os vivos (50)", p1["xp"] == xp1 + 50 and p2["xp"] == p2["xp"])
    check("ouro dividido entre os vivos (40)", p1["gold"] == ouro1 + 40)
    check("item de recompensa acumulado", any(i.get("id") == "magic_sword" for i in loot))


async def test_reward_default_secundario():
    print("\n[12] secundário sem xp/reward usa o padrão (50/25)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "kill_all"},
                                   "secondary": [{"type": "open_key_chest"}]}
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]; xp0, ouro0 = p1["xp"], p1["gold"]
    loot = []
    await r._conceder_objetivo_reward(r.objectives["secondary"][0], is_primary=False, loot_acc=loot)
    check("XP padrão do secundário (max(1,50//2)=25)", p1["xp"] == xp0 + 25)
    check("ouro padrão do secundário (25//2=12)", p1["gold"] == ouro0 + 12)
```

E registre as duas em `main()` (após `test_bonus_secundario()`):

```python
    await test_reward_dividido()
    await test_reward_default_secundario()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_objetivos.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute '_conceder_objetivo_reward'`.

- [ ] **Step 3: Implementar a função**

Em `server.py`, **logo após** o método `_conceder_bonus_secundario` (≈12162-12170), adicione os dois métodos abaixo (deixe `_conceder_bonus_secundario` no lugar por ora — a Tarefa 2 o remove ao reescrever `_check_objectives`):

```python
    def _resolve_reward_item(self, iid):
        """Resolve um id de item de recompensa numa definição completa (deepcopy)."""
        idef = (
            next((i for i in CHEST_ITEMS    if i["id"] == iid), None) or
            next((i for i in SHOP_WEAPONS   if i["id"] == iid), None) or
            next((i for i in SHOP_MERCHANT  if i["id"] == iid), None)
        )
        return deepcopy(idef) if idef else None

    async def _conceder_objetivo_reward(self, obj, is_primary, loot_acc):
        """Concede a recompensa de um objetivo cumprido.

        XP e ouro vêm como TOTAL no objetivo e são divididos igualmente entre os
        heróis vivos; os itens de recompensa são resolvidos e acrescentados a
        `loot_acc` (a Tarefa 2 os larga num único baú). Compatibilidade: objetivos
        sem `xp`/`reward` usam os padrões antigos (secundário=50/25, principal=0)."""
        obj = obj or {}
        xp_default   = 0 if is_primary else OBJ_BONUS_XP
        ouro_default = 0 if is_primary else OBJ_BONUS_OURO
        xp_total   = int(obj.get("xp", xp_default))
        reward     = obj.get("reward") or {}
        ouro_total = int(reward.get("gold", ouro_default))
        vivos = [p for p in self.players.values() if p.get("alive")]
        n = max(1, len(vivos))
        xp_share   = max(1, xp_total // n) if xp_total > 0 else 0
        ouro_share = ouro_total // n if ouro_total > 0 else 0
        for p in vivos:
            if xp_share:   p["xp"]   += xp_share
            if ouro_share: p["gold"] += ouro_share
            await self._check_level_up(p)
        itens_nomes = []
        for it in (reward.get("items") or []):
            idef = self._resolve_reward_item(it.get("id"))
            if idef:
                loot_acc.append(idef)
                itens_nomes.append(idef.get("name", idef.get("id", "item")))
        nome = obj.get("type", "objetivo")
        partes = [f"⭐ Objetivo **{nome}** cumprido!"]
        if xp_share:   partes.append(f"+{xp_share} XP")
        if ouro_share: partes.append(f"+{ouro_share} ouro")
        partes_txt = " ".join(partes[:1]) + (" " + ", ".join(partes[1:]) + " a cada herói." if len(partes) > 1 else "")
        if itens_nomes:
            partes_txt += " 🎁 Recompensa largada: " + ", ".join(itens_nomes) + "."
        await self.gm_say(partes_txt)
```

> Nota: `CHEST_ITEMS`, `SHOP_WEAPONS`, `SHOP_MERCHANT`, `OBJ_BONUS_XP`, `OBJ_BONUS_OURO` e `deepcopy` já são globais usados em `server.py` (ex.: `_roll_monster_loot` ≈12018-12020). `_conceder_bonus_secundario` continua existindo nesta tarefa (será removido na Tarefa 2), então os testes antigos seguem verdes.

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_objetivos.py`
Expected: `=== N passou, 0 falhou ===` — os dois novos testes (`[11]`, `[12]`) passam e nenhum dos antigos quebra (o comportamento de `_check_objectives` ainda é o original).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(objetivos): recompensa por objetivo com XP/ouro divididos + itens"
```

---

## Task 2: Servidor — encerramento manual da missão (flag + baú de recompensa + handler)

`_check_objetivos` para de encerrar a fase automaticamente: ao cumprir o principal, concede as recompensas (Tarefa 1), larga UM baú com todos os itens e liga `mission_complete_pending`. Um novo `handle_encerrar_missao` executa a transição antiga (cidade/vitória).

**Files:**
- Modify: `server.py` — init do flag (≈3042, 3656, 3717), `_check_objectives` (≈12201-12234), novo `handle_encerrar_missao`, payload de `push_state` (≈12387), roteamento (≈12572-12573).
- Test: `tools/test_objetivos.py` (atualizar `test_conclusao_simples` e `test_bonus_secundario`; novo `test_encerrar_missao`).

- [ ] **Step 1: Atualizar os testes existentes para o novo comportamento**

Em `tools/test_objetivos.py`, **substitua** o corpo de `test_conclusao_simples` (≈54-101) por:

```python
async def test_conclusao_simples():
    print("\n[2] cumprir o principal NÃO encerra: liga mission_complete_pending")

    async def cenario(primary_type, prep):
        r = setup_authored()
        d = r.dungeon_def
        d["objectives"] = {"primary": {"type": primary_type}, "secondary": []}
        await r.enter_dungeon("p1")
        vit = {"chamado": False, "victory": None}
        async def fake_end(victory, story=None): vit["chamado"] = True; vit["victory"] = victory
        r.end_game = fake_end
        await prep(r)
        await r._check_objectives()
        return r, vit

    async def mata_todos(r):
        for m in r.monsters.values(): m["hp"] = 0
    r, vit = await cenario("kill_all", mata_todos)
    check("kill_all → missão pode ser encerrada", r.mission_complete_pending is True)
    check("kill_all NÃO encerra automaticamente", vit["chamado"] is False)

    r2 = setup_authored(); r2.dungeon_def["objectives"] = {"primary": {"type": "kill_all"}, "secondary": []}
    await r2.enter_dungeon("p1")
    await r2._check_objectives()
    check("kill_all com monstros vivos não libera encerramento", r2.mission_complete_pending is False)

    async def mata_alvo(r):
        for m in r.monsters.values():
            if m.get("authored_target"): m["hp"] = 0
    r, vit = await cenario("kill_target", mata_alvo)
    check("kill_target → missão pode ser encerrada", r.mission_complete_pending is True)

    async def poe_na_saida(r):
        list(r.players.values())[0]["pos"] = list(r.exit_pos)
    r, vit = await cenario("reach_exit", poe_na_saida)
    check("reach_exit → missão pode ser encerrada", r.mission_complete_pending is True)

    async def abre_chave(r):
        r.key_chest_opened = True
    r, vit = await cenario("open_key_chest", abre_chave)
    check("open_key_chest → missão pode ser encerrada", r.mission_complete_pending is True)
```

**Substitua** o corpo de `test_bonus_secundario` (≈158-172) por:

```python
async def test_bonus_secundario():
    print("\n[4] secundário cumprido concede bônus ao cumprir o principal (ainda sem encerrar)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "kill_all"},
                                   "secondary": [{"type": "open_key_chest"}]}
    await r.enter_dungeon("p1")
    vit = {"c": False}
    async def fe(victory=True, story=None): vit["c"] = True
    r.end_game = fe
    p1 = r.players["p1"]
    xp0, ouro0 = p1["xp"], p1["gold"]
    for m in r.monsters.values(): m["hp"] = 0
    r.key_chest_opened = True
    await r._check_objectives()
    check("XP do grupo subiu pelo secundário", p1["xp"] > xp0)
    check("ouro do grupo subiu pelo secundário", p1["gold"] > ouro0)
    check("não encerrou automaticamente", vit["c"] is False)
    check("mission_complete_pending ligado", r.mission_complete_pending is True)
```

E adicione o novo teste (antes de `async def main`):

```python
async def test_encerrar_missao():
    print("\n[13] encerrar_missao faz a transição e larga baú de recompensa")
    r = setup_authored()
    r.dungeon_def["objectives"] = {
        "primary": {"type": "kill_all", "xp": 60, "reward": {"items": [{"id": "magic_sword"}]}},
        "secondary": []}
    await r.enter_dungeon("p1")
    vit = {"c": False, "v": None}
    async def fe(victory, story=None): vit["c"] = True; vit["v"] = victory
    r.end_game = fe
    n_chests0 = len(r.chests)
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("baú de recompensa largado", len(r.chests) == n_chests0 + 1)
    check("baú contém o item de recompensa",
          any(any(i.get("id") == "magic_sword" for i in c["items"]) for c in r.chests.values()))
    check("ainda não encerrou (espera o botão)", vit["c"] is False)
    await r.handle_encerrar_missao("p1")
    check("encerrar_missao chama end_game(victory)", vit["c"] is True and vit["v"] is True)
```

E registre em `main()` (após `test_reward_default_secundario()`):

```python
    await test_encerrar_missao()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_objetivos.py`
Expected: FAIL — `mission_complete_pending` não existe / `handle_encerrar_missao` não existe.

- [ ] **Step 3: Inicializar o flag**

Em `server.py`, logo após **cada** ocorrência de `self._objetivo_concluido = False` (linhas ≈3042, ≈3656 e dentro do reset em ≈3717), acrescente na linha seguinte:

```python
        self.mission_complete_pending = False
```

(No reset combinado da ≈3717, que está numa única linha com `;`, acrescente `; self.mission_complete_pending = False` ao fim dela.)

- [ ] **Step 4: Reescrever a transição em `_check_objectives`**

Em `server.py`, substitua o bloco (≈12212-12234) que começa em
`if (self.phase == "playing" and not self._objetivo_concluido` por:

```python
        if (self.phase == "playing" and not self._objetivo_concluido
                and prim and self._objetivo_cumprido(prim)):
            self._objetivo_concluido = True
            loot = []
            await self._conceder_objetivo_reward(prim, is_primary=True, loot_acc=loot)
            for s in secs:
                if self._objetivo_cumprido(s):
                    await self._conceder_objetivo_reward(s, is_primary=False, loot_acc=loot)
            if loot:
                vivos = [p for p in self.players.values() if p.get("alive")]
                pos = list(vivos[0]["pos"]) if vivos else list(self.exit_pos or self.stairs_pos or [0, 0])
                self._spawn_chest(pos, 0, loot)
            self.mission_complete_pending = True
            await self.gm_say("🏁 Objetivo principal cumprido! Recolham a recompensa e cliquem em **Encerrar missão** quando estiverem prontos.")
```

Em seguida, **remova** o método agora não usado `_conceder_bonus_secundario` (≈12162-12170) — sua lógica foi substituída por `_conceder_objetivo_reward` (Tarefa 1).

- [ ] **Step 5: Adicionar `handle_encerrar_missao`**

Em `server.py`, logo após `_check_objectives` (antes de `async def handle_libertar_prisioneiro`, ≈12236), adicione:

```python
    async def handle_encerrar_missao(self, pid):
        """Encerramento manual da fase após o objetivo principal cumprido.
        Faz a transição que antes era automática em _check_objectives."""
        if self.phase != "playing" or not self.mission_complete_pending:
            return
        self.mission_complete_pending = False
        if (self.mode == "campaign" and self.campaign
                and self.campaign_phase < len(self.campaign["dungeons"]) - 1):
            fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
            self._campaign_outro = _story_beat(f"outro:{self.campaign_phase}", [fase.get("outro")])
            self.campaign_phase += 1
            self.dungeon_generated = False
            self._objetivo_concluido = False
            await self.gm_say("🏆 Fase concluída! Retornem à cidade antes da próxima masmorra.")
            await self._voltar_para_cidade()
        else:
            story = None
            if self.mode == "campaign" and self.campaign:
                fase = _fase_obj(self.campaign["dungeons"][self.campaign_phase])
                story = _story_beat(f"final:{self.campaign_phase}",
                                    [fase.get("outro"), self.campaign.get("outro")])
            await self.end_game(victory=True, story=story)
```

- [ ] **Step 6: Expor o flag em `push_state`**

Em `server.py`, no dict de `push_state` (≈12387, junto de `"objectives": self.objective_status,`), acrescente:

```python
            "mission_complete_pending": self.mission_complete_pending,
```

- [ ] **Step 7: Rotear a mensagem `encerrar_missao`**

Em `server.py`, após o bloco de `libertar_prisioneiro` (≈12572-12573), adicione:

```python
                elif t == "encerrar_missao":
                    if room: await room.handle_encerrar_missao(pid)
```

- [ ] **Step 8: Rodar a suíte inteira**

Run: `python tools/test_objetivos.py`
Expected: `=== N passou, 0 falhou ===` (todos verdes, incluindo `[2]`, `[4]`, `[11]`, `[12]`, `[13]`).

- [ ] **Step 9: Rodar os testes de regressão relacionados**

Run: `python tools/test_campanha.py` e `python tools/test_roundtrip_editor.py`
Expected: ambos `0 falhou`.

- [ ] **Step 10: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(objetivos): encerramento manual da missao + bau de recompensa"
```

---

## Task 3: Cliente — getter e sender em `gameState.js`

**Files:**
- Modify: `src/gameState.js` — getter `missionCompletePending` (≈1356) e sender `encerrarMissao` (≈1136) + export (≈1446).

- [ ] **Step 1: Adicionar o decisor/getter e o sender**

Em `src/gameState.js`, logo após `function libertarPrisioneiro()` (≈1136), adicione:

```javascript
  // Há objetivo principal cumprido aguardando o encerramento manual da fase?
  function missionCompletePending() { return !!(gameState && gameState.mission_complete_pending); }
  // Sender: encerra a missão (servidor faz a transição cidade/vitória).
  function encerrarMissao() { send({ type: 'encerrar_missao' }); }
```

- [ ] **Step 2: Expor o getter no objeto público**

Em `src/gameState.js`, junto dos getters de Fase 3 (após `get prisioneiroLibertavel()`, ≈1358), adicione:

```javascript
    get missionCompletePending() { return missionCompletePending(); },
```

- [ ] **Step 3: Exportar o sender**

Em `src/gameState.js`, junto de `libertarPrisioneiro,` no bloco de exports (≈1446), adicione:

```javascript
    encerrarMissao,        // encerramento manual da missão (chamado com parênteses)
```

- [ ] **Step 4: Verificar sintaxe**

Run: `node --check src/gameState.js`
Expected: sem saída (sintaxe OK).

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js
git commit -m "feat(cliente): getter missionCompletePending + sender encerrarMissao"
```

---

## Task 4: Cliente — botão "Encerrar missão" no HUD (`game.js`)

**Files:**
- Modify: `game.js` — `renderObjectivesHUD` (≈2953-2979) + função global de confirmação.

- [ ] **Step 1: Adicionar a função de confirmação**

Em `game.js`, logo antes de `function renderObjectivesHUD(msg){` (≈2953), adicione:

```javascript
// Confirmação antes de encerrar a missão (itens largados podem ficar para trás).
function encerrarMissaoConfirm(){
  if (confirm('Pegue os itens de recompensa antes de encerrar. Tem certeza que quer terminar a missão?')) {
    GS.encerrarMissao();
  }
}
window.encerrarMissaoConfirm = encerrarMissaoConfirm;
```

- [ ] **Step 2: Renderizar o botão no HUD**

Em `game.js`, dentro de `renderObjectivesHUD`, logo antes de `hud.innerHTML = html;` (≈2975), adicione:

```javascript
  if (GS.missionCompletePending) {
    html += `<button class="btn-encerrar-missao" onclick="encerrarMissaoConfirm()">🏁 Encerrar missão</button>`;
  }
```

- [ ] **Step 3: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem saída (sintaxe OK).

- [ ] **Step 4: Verificação visual (preview)**

Suba o jogo (`python server.py`) e verifique via preview: numa partida autorada, ao cumprir o objetivo principal, o HUD de objetivos mostra o botão "🏁 Encerrar missão"; clicar abre o `confirm`; confirmar envia `encerrar_missao` e a fase termina (cidade/vitória). Em partida procedural (`GS.objectives` nulo) o HUD continua oculto e o botão não aparece.

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(cliente): botao Encerrar missao no HUD de objetivos"
```

---

## Task 5: Editor — deletar sala (`tools/editor.js`)

**Files:**
- Modify: `tools/editor.js` — helper `deleteRoom` + UI no ramo `k === "room"` de `renderPanel` (≈226-232) + export (≈471).

- [ ] **Step 1: Adicionar o helper `deleteRoom`**

Em `tools/editor.js`, logo após `function eraseAt(x, y) { ... }` (≈175), adicione:

```javascript
  function deleteRoom(room, clearFloor) {
    const idx = S.rooms.indexOf(room);
    if (idx >= 0) S.rooms.splice(idx, 1);
    if (clearFloor) {
      for (let j = room.y; j < room.y + room.h; j++) {
        for (let i = room.x; i < room.x + room.w; i++) {
          if (S.tiles[j] && S.tiles[j][i] !== undefined) {
            if (S.tiles[j][i] === DOOR) doorUnlink(i, j);
            S.tiles[j][i] = WALL;
          }
        }
      }
    }
    // Entidades que apontavam para esta sala ficam sem sala (não são apagadas).
    for (const m of S.monsters) if (m.room_id === room.id) m.room_id = null;
    if (S.prisoner && S.prisoner.room_id === room.id) S.prisoner.room_id = null;
    S.sel = null; renderPanel(); render();
  }
```

> As portas da sala removida somem junto com `room.doors` ao dar `splice`; só ao limpar o chão precisamos `doorUnlink` (porque o tile DOOR vira WALL e nenhuma outra sala pode continuar referenciando-o).

- [ ] **Step 2: Adicionar a UI de deletar no painel da sala**

Em `tools/editor.js`, no ramo `else if (k === "room")` de `renderPanel` (≈226-232), substitua o bloco por:

```javascript
    } else if (k === "room") {
      panel.innerHTML = `<b>▦ Sala #${ref.id}</b>
        <label>role</label><select id="p-role">${opt(["entrance", "monster", "chest", "trap", "boss", "empty"].map(r => ({ v: r })), ref.role, o => o.v)}</select>
        <label><input type="checkbox" id="p-locked" ${ref.locked ? "checked" : ""}> trancada</label>
        <div style="margin-top:8px;color:#8a7a5a;font-size:11px">portas: ${ref.doors.length}</div>
        <button id="p-del-room" style="margin-top:10px">🗑 Deletar sala</button>
        <div id="p-del-confirm" style="display:none;margin-top:6px">
          <div style="font-size:11px;color:#d8a0a0;margin-bottom:4px">Deletar a sala #${ref.id}?</div>
          <button id="p-del-keep">Deletar (manter chão)</button>
          <button id="p-del-clear">Deletar (limpar chão)</button>
        </div>`;
      document.getElementById("p-role").onchange = e => { ref.role = e.target.value; render(); };
      document.getElementById("p-locked").onchange = e => { ref.locked = e.target.checked; render(); };
      document.getElementById("p-del-room").onclick = () => {
        document.getElementById("p-del-confirm").style.display = "";
      };
      document.getElementById("p-del-keep").onclick = () => deleteRoom(ref, false);
      document.getElementById("p-del-clear").onclick = () => deleteRoom(ref, true);
```

- [ ] **Step 3: Expor `deleteRoom` para verificação no console**

Em `tools/editor.js`, no objeto `window.EDITOR = { ... }` (≈471), acrescente `deleteRoom,` na lista.

- [ ] **Step 4: Verificar sintaxe**

Run: `node --check tools/editor.js`
Expected: sem saída (sintaxe OK).

- [ ] **Step 5: Verificação manual (preview / console)**

Abra `tools/editor.html`, crie uma sala (ferramenta "sala", arrastar ≥2×2). Com a ferramenta "selecionar", clique na sala → painel mostra "🗑 Deletar sala". Confirme:
- "Deletar (manter chão)": `window.EDITOR.S.rooms.length` diminui em 1; os tiles da área continuam FLOOR (`window.EDITOR.S.tiles`).
- "Deletar (limpar chão)": além de remover a sala, os tiles da área viram WALL (0) e portas internas somem.
- Um monstro com `room_id` da sala deletada fica com `room_id === null` (não é apagado).

- [ ] **Step 6: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): deletar sala (manter ou limpar o chao)"
```

---

## Task 6: Editor — XP e recompensa por objetivo (`tools/editor.js`)

Adiciona campos de XP/ouro/itens ao painel de objetivos (principal e cada secundário) e persiste no JSON.

**Files:**
- Modify: `tools/editor.js` — ramo "sem seleção" de `renderPanel` (≈180-194), `buildJSON` (≈315), `loadJSON` (≈386), default ao adicionar secundário (≈191).

- [ ] **Step 1: Adicionar normalização e o sub-render de recompensa**

Em `tools/editor.js`, logo antes de `function renderPanel() {` (≈180), adicione:

```javascript
  function objDefaults(isPrimary) {
    return { xp: isPrimary ? 0 : 50, reward: { gold: isPrimary ? 0 : 25, items: [] } };
  }
  function normalizeObjective(obj, isPrimary) {
    const d = objDefaults(isPrimary);
    if (typeof obj.xp !== "number") obj.xp = d.xp;
    if (!obj.reward || typeof obj.reward !== "object") obj.reward = { gold: d.reward.gold, items: [] };
    if (typeof obj.reward.gold !== "number") obj.reward.gold = d.reward.gold;
    if (!Array.isArray(obj.reward.items)) obj.reward.items = [];
    return obj;
  }
  // HTML dos campos de recompensa de um objetivo. `pfx` é um prefixo único de ids.
  function rewardFieldsHTML(obj, pfx) {
    return `<label>XP (total, dividido entre os vivos) <input id="${pfx}-xp" type="number" min="0" value="${obj.xp}"></label>
      <label>ouro (total, dividido) <input id="${pfx}-gold" type="number" min="0" value="${obj.reward.gold}"></label>
      <label>itens de recompensa</label>
      <div id="${pfx}-items">${obj.reward.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="${pfx}-rm">×</button></div>`).join("")}</div>
      <select id="${pfx}-add">${opt(CAT.items.map(it => ({ v: it.id, name: it.name })), "", o => o.v + " — " + o.name)}</select>
      <button id="${pfx}-additem">+ item</button>`;
  }
  function wireRewardFields(obj, pfx) {
    document.getElementById(`${pfx}-xp`).onchange = e => { obj.xp = Math.max(0, Number(e.target.value) | 0); };
    document.getElementById(`${pfx}-gold`).onchange = e => { obj.reward.gold = Math.max(0, Number(e.target.value) | 0); };
    document.getElementById(`${pfx}-additem`).onclick = () => { const id = document.getElementById(`${pfx}-add`).value; if (id) obj.reward.items.push({ id }); renderPanel(); };
    panel.querySelectorAll(`.${pfx}-rm`).forEach(b => b.onclick = () => { obj.reward.items.splice(Number(b.dataset.i), 1); renderPanel(); });
  }
```

- [ ] **Step 2: Reescrever o ramo "sem seleção" de `renderPanel`**

Em `tools/editor.js`, substitua o bloco `if (!S.sel) { ... return; }` (≈181-195) por:

```javascript
    if (!S.sel) {
      const OBJ = ["kill_target", "kill_all", "reach_exit", "open_key_chest", "rescue_prisoner"];
      const o = S.objectives;
      normalizeObjective(o.primary, true);
      o.secondary.forEach(s => normalizeObjective(s, false));
      panel.innerHTML = `<b>🗺️ Masmorra</b>
        <label>objetivo principal</label>
        <select id="o-prim">${OBJ.map(t => `<option value="${t}"${o.primary.type === t ? " selected" : ""}>${t}</option>`).join("")}</select>
        ${rewardFieldsHTML(o.primary, "o-prim-rw")}
        <hr style="border-color:#3a3022;margin:10px 0">
        <label>objetivos secundários</label>
        <div id="o-sec">${o.secondary.map((s, i) => `<div class="o-sec-item" style="border-top:1px solid #3a3022;padding-top:6px;margin-top:6px">
          <select data-i="${i}" class="o-secsel">${OBJ.map(t => `<option value="${t}"${s.type === t ? " selected" : ""}>${t}</option>`).join("")}</select>
          <button data-i="${i}" class="o-rm">× remover</button>
          ${rewardFieldsHTML(s, "o-sec" + i + "-rw")}
        </div>`).join("")}</div>
        <button id="o-add">+ secundário</button>`;
      document.getElementById("o-prim").onchange = e => { o.primary.type = e.target.value; };
      wireRewardFields(o.primary, "o-prim-rw");
      document.getElementById("o-add").onclick = () => { o.secondary.push({ type: "rescue_prisoner", ...objDefaults(false) }); renderPanel(); };
      panel.querySelectorAll(".o-secsel").forEach(sel => sel.onchange = e => { o.secondary[Number(e.target.dataset.i)].type = e.target.value; });
      panel.querySelectorAll(".o-rm").forEach(b => b.onclick = () => { o.secondary.splice(Number(b.dataset.i), 1); renderPanel(); });
      o.secondary.forEach((s, i) => wireRewardFields(s, "o-sec" + i + "-rw"));
      return;
    }
```

- [ ] **Step 3: Persistir em `buildJSON`**

Em `tools/editor.js`, no `buildJSON` (≈315), substitua a linha `objectives: S.objectives,` por:

```javascript
      objectives: {
        primary: { type: S.objectives.primary.type, xp: S.objectives.primary.xp | 0,
                   reward: { gold: (S.objectives.primary.reward.gold | 0), items: S.objectives.primary.reward.items.map(i => ({ id: i.id })) } },
        secondary: S.objectives.secondary.map(s => ({ type: s.type, xp: s.xp | 0,
                   reward: { gold: (s.reward.gold | 0), items: s.reward.items.map(i => ({ id: i.id })) } })),
      },
```

- [ ] **Step 4: Normalizar em `loadJSON`**

Em `tools/editor.js`, no `loadJSON` (≈386), substitua a linha
`S.objectives = obj.objectives || { primary: { type: "kill_all" }, secondary: [] };` por:

```javascript
    S.objectives = obj.objectives || { primary: { type: "kill_all" }, secondary: [] };
    if (!S.objectives.primary) S.objectives.primary = { type: "kill_all" };
    if (!Array.isArray(S.objectives.secondary)) S.objectives.secondary = [];
    normalizeObjective(S.objectives.primary, true);
    S.objectives.secondary.forEach(s => normalizeObjective(s, false));
```

- [ ] **Step 5: Verificar sintaxe**

Run: `node --check tools/editor.js`
Expected: sem saída (sintaxe OK).

- [ ] **Step 6: Verificação manual (round-trip)**

Abra `tools/editor.html`. No painel sem seleção, defina XP=120 e ouro=90 no principal e adicione o item `magic_sword`. Adicione um secundário e ajuste seus campos. No console:
```js
const d = window.EDITOR.buildJSON();
console.log(JSON.stringify(d.objectives, null, 2));   // deve conter xp/reward em primary e secondary
window.EDITOR.loadJSON(d);                              // round-trip
console.log(window.EDITOR.S.objectives);               // valores preservados
```
Confirme também que `server.validar_dungeon` aceita o JSON (a Tarefa 2 já roda `test_roundtrip_editor.py`).

- [ ] **Step 7: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): XP e recompensa (ouro/itens) por objetivo"
```

---

## Task 7: Documentação — `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` — tabela Client→Server + nota de objetivos/portas.

- [ ] **Step 1: Adicionar a mensagem na tabela de protocolo**

Em `CLAUDE.md`, na tabela "Client → Server", logo após a linha de `libertar_prisioneiro` (ou junto de `end_turn`), adicione a linha:

```markdown
| `encerrar_missao` | — (herói encerra a fase após o objetivo principal cumprido; só habilitado quando `mission_complete_pending`). Concluir o principal **não** encerra mais automaticamente: o servidor concede a recompensa, larga um baú e liga `mission_complete_pending`; o cliente mostra "🏁 Encerrar missão" (com confirmação) que dispara esta mensagem. |
```

- [ ] **Step 2: Documentar o formato dos objetivos**

Em `CLAUDE.md`, na seção de protocolo Server→Client (após a nota de "Portas/salas trancadas"), adicione um parágrafo:

```markdown
> **Objetivos com recompensa:** cada objetivo (`objectives.primary` e cada
> `objectives.secondary[i]`) aceita `xp` (int, total dividido igualmente entre os
> heróis vivos) e `reward { gold, items:[{id}] }` (ouro dividido; itens largados num
> baú de recompensa via `_spawn_chest`). Campos ausentes usam o padrão antigo
> (secundário 50 XP/25 ouro; principal sem extra). As recompensas são concedidas ao
> cumprir o objetivo **principal**; a fase só termina quando um herói clica em
> "Encerrar missão" (`encerrar_missao`). `game_state.mission_complete_pending` indica
> esse estado. Editor: deletar salas e definir XP/recompensa por objetivo.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: encerrar_missao + objetivos com XP/recompensa"
```

---

## Task 8: Verificação final integrada

- [ ] **Step 1: Rodar a suíte de testes do servidor**

Run: `python tools/test_objetivos.py && python tools/test_campanha.py && python tools/test_roundtrip_editor.py && python tools/test_persistencia_masmorra.py`
Expected: todos `=== N passou, 0 falhou ===`.

- [ ] **Step 2: Checar sintaxe de todo o cliente alterado**

Run: `node --check src/gameState.js && node --check game.js && node --check tools/editor.js`
Expected: sem saída.

- [ ] **Step 3: Teste end-to-end manual (preview)**

Suba `python server.py`, crie/carregue uma masmorra autorada com um objetivo principal e um secundário, ambos com XP/ouro/itens. Jogue até cumprir o principal e confirme: GM anuncia XP/ouro a cada herói + itens largados; um baú de recompensa aparece; o HUD mostra "🏁 Encerrar missão"; clicar pede confirmação; confirmar encerra (cidade em campanha / vitória fora dela). Verifique que dungeons antigas (sem `xp`/`reward`) ainda concedem 50/25 nos secundários.

- [ ] **Step 4: Commit final (se houver ajustes)**

```bash
git add -A && git commit -m "test: verificacao integrada objetivos/recompensa/encerramento"
```
