# Inventário do monstro (SP2) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No Modo Mestre, o mestre usa manualmente os itens de bolsa do monstro (poções, arremessáveis, veneno, pergaminho) e ativa TODAS as habilidades especiais dele (inclusive as derivadas de herói/guilda), com usos e recarga visíveis na ficha.

**Architecture:** Apoia-se no sistema de equipamento já existente do usuário: `m["equipment_consumables"]` (itens de bolsa) e os resolvedores da IA (`_monster_throw_item`, efeitos de `_monster_try_equipment_item`). O SP2 adiciona os **handlers de mestre** que reusam esses resolvedores + a **UI da ficha**. Habilidades de editor (herói/guilda) ganham um caminho de ativação manual compartilhado com a IA (`_ativar_editor_ability`).

**Tech Stack:** Python (`server.py`), Vanilla JS (`game.js`, `src/gameState.js`), CSS (`game.css`). Testes: harness `check()` em `tools/test_modo_mestre.py`, rodado com `python tools/test_modo_mestre.py`.

**Invariante:** tudo gateia por `_mestre_ativo()` + janela Manual (`master_manual_mid`). Sem mestre, byte-idêntico.

**⚠️ WIP do usuário (autorizado a bundlar):** `server.py`, `game.js`, `game.css`, `monstros_personalizados.json`, `tools/editor_monsters_custom.js` têm WIP não-commitado do sistema de equipamento. O usuário autorizou incluí-lo nos commits. **Use `git add <arquivos específicos>`** (nunca `git add -A`/`.`) — há assets/dungeons soltos que NÃO devem entrar. Confira `git status` antes de cada commit.

---

### Task 1: Servidor — `handle_mestre_usar_item` (itens de bolsa) + economia de ação

**Files:**
- Modify: `server.py` (`_master_manual_window` — resetar `_master_bonus_acted`; novos métodos perto de `_monster_try_equipment_item` ~16203; dispatcher perto de `mestre_usar_habilidade`)
- Test: `tools/test_modo_mestre.py` (nova seção `[27]`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir em `tools/test_modo_mestre.py`, antes de `print(f"\n=== {PASS}...`):

```python
    print("\n[27] mestre_usar_item — heal (bônus), throwable (principal), food recusado")
    r = playing_room_com_mestre()
    heal_calls = {"n": 0}
    m = {"id": "g1", "hp": 5, "max_hp": 12, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "attacks": [{"name": "espada"}],
         "equipment_consumables": [
            {"id": "health_potion", "name": "Poção", "effect": "heal", "value": 6},
            {"id": "granada", "name": "Granada", "effect": "throwable"},
            {"id": "cantil_agua", "name": "Cantil", "effect": "food"},
         ]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 10, "max_hp": 10}}
    # heal → cura o monstro, gasta a ação bônus, remove a poção
    await r.handle_mestre_usar_item("m1", "g1", "health_potion", None, None, None)
    check("curou o monstro", m["hp"] == 11)
    check("gastou ação bônus", m["_master_bonus_acted"] is True)
    check("poção removida", not any(i["id"] == "health_potion" for i in m["equipment_consumables"]))
    check("ação principal livre", m["_master_acted"] is False)
    # throwable → chama _monster_throw_item mirando o herói, gasta a ação principal
    throws = {"n": 0}
    async def fake_throw(mm, target_obj, item): throws["n"] += 1
    r._monster_throw_item = fake_throw
    r._tem_linha_de_visao = lambda a, b: True
    await r.handle_mestre_usar_item("m1", "g1", "granada", "hA", None, None)
    check("arremessou no herói", throws["n"] == 1)
    check("gastou ação principal", m["_master_acted"] is True)
    check("granada removida", not any(i["id"] == "granada" for i in m["equipment_consumables"]))
    # food → recusado, sem efeito
    r._errs.clear()
    await r.handle_mestre_usar_item("m1", "g1", "cantil_agua", None, None, None)
    check("food recusado", any("efeito" in e.lower() for e in r._errs))
    check("cantil continua na bolsa", any(i["id"] == "cantil_agua" for i in m["equipment_consumables"]))
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — `AttributeError: ... has no attribute 'handle_mestre_usar_item'`.

- [ ] **Step 3: Resetar `_master_bonus_acted` na abertura da janela**

Em `server.py`, no método `_master_manual_window`, logo após a linha `m["_master_acted"] = False`, inserir:

```python
        m["_master_bonus_acted"] = False
```

- [ ] **Step 4: Implementar o handler + helper de conjurador**

Em `server.py`, logo após o método `_monster_throw_item` (termina ~16305), inserir:

```python
    def _monster_e_conjurador(self, m):
        """True se o monstro tem conjuração na ficha (monster_spells não-vazio ou
        alguma habilidade action_type=='magia') — ex.: necromante."""
        if m.get("monster_spells"):
            return True
        return any(ab.get("action_type") == "magia" for ab in m.get("special_abilities", []))

    async def handle_mestre_usar_item(self, pid, monster_id, item_id, target_id, tx, ty):
        """Manual: o mestre usa um item de bolsa do monstro (equipment_consumables).
        Consumíveis de alvo-próprio = ação bônus; arremesso/pergaminho = principal.
        Espelha a economia do jogador."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        m = self.monsters.get(monster_id)
        if not m or m["hp"] <= 0:
            return
        bag = m.get("equipment_consumables", [])
        item = next((i for i in bag if i.get("id") == item_id), None)
        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado no inventário."}); return
        effect = item.get("effect")

        # Sem efeito em monstros: comida/bebida (fome/sede).
        if effect in {"food", "ration", "wine", "ale"}:
            await self.send_to(pid, {"type": "error", "msg": "Este item não tem efeito em monstros."}); return

        # Arremesso — ação PRINCIPAL.
        if effect == "throwable":
            if m.get("_master_acted"):
                await self.send_to(pid, {"type": "error", "msg": "Este monstro já usou a ação principal."}); return
            defn = ARREMESSAVEIS.get(item_id)
            if not defn:
                await self.send_to(pid, {"type": "error", "msg": "Item não arremessável."}); return
            alvo = self.players.get(target_id)
            if not alvo or not alvo.get("alive"):
                await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
            rng = defn.get("alcance", 0)
            if max(abs(m["pos"][0] - alvo["pos"][0]), abs(m["pos"][1] - alvo["pos"][1])) > rng:
                await self.send_to(pid, {"type": "error", "msg": "Alvo fora de alcance."}); return
            if not self._tem_linha_de_visao(m["pos"], alvo["pos"]):
                await self.send_to(pid, {"type": "error", "msg": "Uma parede bloqueia o arremesso."}); return
            m["_master_acted"] = True
            await self._monster_throw_item(m, {"kind": "player", "obj": alvo}, item)
            if item in bag:
                bag.remove(item)   # some em acerto E erro (igual à IA)
            await self.push_state(); return

        # Pergaminho — ação PRINCIPAL, só monstro conjurador.
        if effect == "scroll":
            if m.get("_master_acted"):
                await self.send_to(pid, {"type": "error", "msg": "Este monstro já usou a ação principal."}); return
            if not self._monster_e_conjurador(m):
                await self.send_to(pid, {"type": "error", "msg": "Só monstros conjuradores podem usar pergaminhos."}); return
            sid = item.get("magia_id")   # itens de pergaminho gravam a magia em magia_id (ver gerar_pergaminho)
            magia = GRIMORIO.get(sid)
            if not magia or sid not in GRIMORIO_IMPLEMENTADAS:
                await self.send_to(pid, {"type": "error", "msg": "Magia do pergaminho não disponível."}); return
            data = {"target_id": target_id, "tx": tx, "ty": ty}
            m["_master_acted"] = True
            await self._executar_magia_grimorio(m, magia, data)
            if item in bag:
                bag.remove(item)
            await self.push_state(); return

        # Consumíveis de alvo-próprio — ação BÔNUS.
        if effect not in self.BONUS_ACTION_EFFECTS:
            await self.send_to(pid, {"type": "error", "msg": "Item não usável pelo mestre."}); return
        if m.get("_master_bonus_acted"):
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já usou a ação bônus."}); return
        val = int(item.get("value", 0) or 0)
        removed = True
        if effect == "heal":
            m["hp"] = min(m.get("max_hp", m["hp"]), m["hp"] + val)
            max_uses = int(item.get("max_uses", 1) or 1)
            if max_uses > 1:
                uses_left = int(item.get("uses_left", max_uses) or 1) - 1
                item["uses_left"] = uses_left
                removed = uses_left <= 0
            await self.gm_say(f"🧪 **{m['name']}** usa **{item['name']}** e recupera **{val}** HP.")
        elif effect == "regeneration":
            m["potion_regen_pool"] = m.get("potion_regen_pool", 0) + val
            await self.gm_say(f"🌿 **{m['name']}** bebe **{item['name']}** — regeneração +{val}.")
        elif effect == "atk_bonus":
            m["equipment_attack_bonus"] = m.get("equipment_attack_bonus", 0) + val
            await self.gm_say(f"⚗️ **{m['name']}** usa **{item['name']}**: +{val} de ataque.")
        elif effect == "coat_poison":
            vid = item.get("veneno_id")
            if vid and m.get("attacks"):
                m["attacks"][0]["on_hit"] = vid
                m["equipment_poison"] = vid
            await self.gm_say(f"🧪 **{m['name']}** unta **{item['name']}** na arma.")
        elif effect == "antidote":
            for k in ("veneno", "veneno_dano", "veneno_rodadas", "envenenado"):
                m.pop(k, None)
            await self.gm_say(f"🟢 **{m['name']}** usa **{item['name']}** e neutraliza o veneno.")
        elif effect == "veil_shadow":
            m["oculto_item"] = True
            await self.gm_say(f"🕯️ **{m['name']}** usa **{item['name']}** e fica oculto.")
        m["_master_bonus_acted"] = True
        if removed and item in bag:
            bag.remove(item)
        await self.push_state()
```

- [ ] **Step 5: Adicionar a entrada do dispatcher**

Em `server.py`, logo após a linha do `mestre_usar_habilidade` no dispatcher, inserir:

```python
                elif t == "mestre_usar_item":
                    if room: await room.handle_mestre_usar_item(pid, msg.get("monster_id"), msg.get("item_id"), msg.get("target_id"), msg.get("tx"), msg.get("ty"))
```

- [ ] **Step 6: Rodar e confirmar sucesso**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção `[27]`; contagem final `0 falharam`.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): mestre usa itens de bolsa do monstro (poção/arremesso/pergaminho)"
```

---

### Task 2: Servidor — habilidades de editor (herói/guilda) ativáveis pelo mestre

**Files:**
- Modify: `server.py` (`_monster_try_editor_ability` — extrair helper ~16201; `_habilidade_ativavel_manual` ~16343; `handle_mestre_usar_habilidade` ~16352)
- Test: `tools/test_modo_mestre.py` (nova seção `[28]`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir em `tools/test_modo_mestre.py` antes da tally final:

```python
    print("\n[28] mestre_usar_habilidade — habilidade de editor (herói/guilda) ativável")
    r = playing_room_com_mestre()
    ab = {"id": "hero_warrior_mira_certeira", "source": "heroi", "name": "Mira Certeira",
          "action_type": "acao", "monster_effect": "vantagem_combate",
          "uses_per_day": 3, "cooldown_turns": 4}
    m = {"id": "g1", "hp": 10, "pos": [2, 2], "size": [1, 1], "control_mode": "manual",
         "_master_acted": False, "special_abilities": [ab],
         "monster_ability_uses": {"hero_warrior_mira_certeira": 3},
         "monster_ability_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    check("predicado aceita editor ability", r._habilidade_ativavel_manual(ab) is True)
    await r.handle_mestre_usar_habilidade("m1", "g1", "hero_warrior_mira_certeira", None)
    check("aplicou vantagem", m.get("editor_ability_advantage", 0) >= 1)
    check("gastou 1 uso", m["monster_ability_uses"]["hero_warrior_mira_certeira"] == 2)
    check("entrou em recarga", m["monster_ability_cooldowns"].get("hero_warrior_mira_certeira", 0) > 0)
    check("consumiu a ação", m["_master_acted"] is True)
    # sem usos → recusa
    m["_master_acted"] = False; m["monster_ability_uses"]["hero_warrior_mira_certeira"] = 0
    r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "hero_warrior_mira_certeira", None)
    check("sem usos recusado", m["_master_acted"] is False)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL em `[28]` — `_habilidade_ativavel_manual` retorna False para a editor ability (ela não tem save/dc).

- [ ] **Step 3: Extrair `_ativar_editor_ability` de `_monster_try_editor_ability`**

Em `server.py`, no método `_monster_try_editor_ability`, o bloco que hoje faz (dentro do loop, quando a habilidade está disponível): decrementa `uses`, seta `cooldowns[aid]`, seta `editor_ability_advantage`/`editor_ability_damage` e narra. **Substituir** esse corpo por uma chamada ao novo helper, e criar o helper logo acima:

```python
    def _ativar_editor_ability(self, m, ab):
        """Aplica o efeito genérico de uma habilidade de editor (herói/guilda):
        gasta uso+recarga (monster_ability_*) e concede vantagem+dano no próximo
        golpe. Compartilhado pela IA e pelo controle manual do mestre. Retorna
        True se ativou, False se sem usos / em recarga."""
        aid = ab.get("id")
        uses = m.setdefault("monster_ability_uses", {})
        cds = m.setdefault("monster_ability_cooldowns", {})
        if not aid or uses.get(aid, ab.get("uses_per_day", 1)) <= 0:
            return False
        if cds.get(aid, 0) > 0:
            return False
        uses[aid] = uses.get(aid, ab.get("uses_per_day", 1)) - 1
        cd = max(0, int(ab.get("cooldown_turns", 0) or 0))
        if cd:
            cds[aid] = cd
        m["editor_ability_advantage"] = max(1, m.get("editor_ability_advantage", 0))
        m["editor_ability_damage"] = max(1, m.get("editor_ability_damage", 0))
        return True
```

E dentro de `_monster_try_editor_ability`, o loop passa a:

```python
        for ab in m.get("special_abilities", []):
            if ab.get("source") not in {"heroi", "guilda"} or ab.get("action_type") == "passiva":
                continue
            if self._ativar_editor_ability(m, ab):
                await self.gm_say(f"✦ **{m['name']}** ativa **{ab.get('name', ab.get('id'))}** para ganhar vantagem no combate!")
                return True
        return False
```

- [ ] **Step 4: Estender o predicado e o handler**

Em `server.py`, substituir `_habilidade_ativavel_manual`:

```python
    def _habilidade_ativavel_manual(self, ability):
        """O mestre ativa: (a) habilidades save+dc (via _use_monster_ability) OU
        (b) habilidades de editor herói/guilda (self-buff, via _ativar_editor_ability)."""
        if not ability or ability.get("action_type") == "passiva":
            return False
        if ability.get("save") is not None and ability.get("dc") is not None:
            return True
        return ability.get("source") in {"heroi", "guilda"}
```

E em `handle_mestre_usar_habilidade`, após localizar `ability` e validar `_habilidade_ativavel_manual`, ANTES do bloco de alvo/`_use_monster_ability`, inserir o ramo de editor:

```python
        # Ramo (b): habilidade de editor (herói/guilda) — self-buff, sem alvo.
        if not (ability.get("save") is not None and ability.get("dc") is not None):
            if not self._ativar_editor_ability(m, ability):
                await self.send_to(pid, {"type": "error", "msg": "Habilidade sem usos ou em recarga."}); return
            m["_master_acted"] = True
            await self.gm_say(f"✦ **{m['name']}** ativa **{ability.get('name', ability['id'])}**!")
            await self.push_state(); return
```

(O restante do handler — validação de alvo + `_use_monster_ability` — continua para o ramo save+dc.)

- [ ] **Step 5: Rodar e confirmar sucesso**

Run: `python tools/test_modo_mestre.py`
Expected: PASS em `[28]`; contagem final `0 falharam`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): ativar habilidades de editor (herói/guilda) do monstro pela ficha"
```

---

### Task 3: Cliente (gameState.js) — sender `mestreUsarItem`

**Files:**
- Modify: `src/gameState.js` (defs perto de `mestreUsarHabilidade`; export)

- [ ] **Step 1: Adicionar o sender**

Em `src/gameState.js`, logo após a linha de `mestreUsarHabilidade`, inserir:

```javascript
  function mestreUsarItem(monsterId, itemId, targetId, tx, ty) { send({ type: 'mestre_usar_item', monster_id: monsterId, item_id: itemId, target_id: targetId, tx, ty }); }
```

- [ ] **Step 2: Exportar**

No objeto de retorno, logo após `mestreUsarHabilidade,`, inserir:

```javascript
    mestreUsarItem,
```

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(mestre): sender mestreUsarItem"
```

---

### Task 4: Cliente (game.js) — ficha: seção "Itens" + habilidades de editor ativáveis

**Files:**
- Modify: `game.js` (`renderFichaMonstro` ~10353; `_mestreAtivarHabilidade` ~10411)

- [ ] **Step 1: Ampliar `ativavel`/`usosRest`/`cdRest` para habilidades de editor**

Em `game.js`, dentro de `renderFichaMonstro`, substituir as três funções auxiliares por:

```javascript
  const ehEditor = (a) => (a.source === 'heroi' || a.source === 'guilda') && a.action_type && a.action_type !== 'passiva';
  const ativavel = (a) => (a.action_type !== 'passiva' && a.save != null && a.dc != null) || ehEditor(a);
  const usosRest = (a) => {
    const lim = (a.uses_per_combat != null) ? a.uses_per_combat
              : (a.uses_per_day != null ? a.uses_per_day : null);
    if (lim == null) return '∞';
    const dict = ehEditor(a) ? (m.monster_ability_uses || {}) : (m.ability_uses || {});
    const u = dict[a.id];
    return (u != null ? u : lim);
  };
  const cdRest = (a) => {
    const dict = ehEditor(a) ? (m.monster_ability_cooldowns || {}) : (m.ability_cooldowns || {});
    return dict[a.id] || 0;
  };
```

- [ ] **Step 2: Ramificar `_mestreAtivarHabilidade` (editor = sem alvo)**

Em `game.js`, substituir `_mestreAtivarHabilidade` por:

```javascript
function _mestreAtivarHabilidade(m, abid){
  const st = GS.gameState; if(!st) return;
  const ab = (m.special_abilities||[]).find(a=>a.id===abid);
  if(!ab) return;
  // Habilidade de editor (herói/guilda): self-buff, ativa direto sem alvo.
  if((ab.source === 'heroi' || ab.source === 'guilda') && !(ab.save != null && ab.dc != null)){
    GS.mestreUsarHabilidade(m.id, abid, null); return;
  }
  const rng = ab.range || null;
  const alvos = (st.players||[]).filter(p => {
    if(!p.alive) return false;
    const dx=Math.abs(m.pos[0]-p.pos[0]), dy=Math.abs(m.pos[1]-p.pos[1]);
    return rng!=null ? Math.max(dx,dy)<=rng : ((dx===1&&dy===0)||(dx===0&&dy===1));
  });
  if(!alvos.length){ toast(`Nenhum herói ${rng?('a até '+rng+'q'):'adjacente'}.`, 'var(--orange)'); return; }
  openTargetModal(`${ab.name||abid} — Escolha o alvo`, alvos, 'player',
    (alvoId)=> GS.mestreUsarHabilidade(m.id, abid, alvoId));
}
```

- [ ] **Step 3: Adicionar a seção "Itens" e a arma/armadura na ficha**

Em `game.js`, dentro de `renderFichaMonstro`, ANTES da linha `host.innerHTML =`, inserir os construtores:

```javascript
  const cons = m.equipment_consumables || [];
  const FOOD = new Set(['food','ration','wine','ale']);
  const itemUsavel = (it) => {
    if(FOOD.has(it.effect)) return false;
    if(it.effect === 'throwable') return isManual && !acted;
    if(it.effect === 'scroll') return isManual && !acted && _monConjurador(m);
    return isManual && !m._master_bonus_acted;   // consumível bônus
  };
  const linhaItem = (it) => {
    const podeUsar = itemUsavel(it);
    const motivo = FOOD.has(it.effect) ? '<span class="fm-ia">sem efeito</span>'
                 : (it.effect === 'scroll' && !_monConjurador(m)) ? '<span class="fm-ia">só conjurador</span>'
                 : `<button class="fm-usar-item" data-iid="${it.id}"${podeUsar?'':' disabled'}>Usar</button>`;
    return `<div class="fm-hab fm-item"><div class="fm-ab-top"><b>${it.emoji||'🎒'} ${it.name||it.id}</b> ${motivo}</div>`+
           `<div class="fm-ab-desc">${it.descricao||it.desc||''}</div></div>`;
  };
  const eqW = m.equipped_weapon ? `<div class="fm-eq">🗡️ ${m.equipped_weapon.name}</div>` : '';
  const eqA = (m.equipment_items||[]).filter(i=>i.ac_bonus||i.effect==='def_')
              .map(i=>`<div class="fm-eq">🛡️ ${i.name}</div>`).join('');
```

E na string `host.innerHTML`, logo após a seção de Passivas, acrescentar:

```javascript
    (cons.length? `<div class="fm-sec">Itens</div>${cons.map(linhaItem).join('')}`:'')+
    ((eqW||eqA)? `<div class="fm-sec">Equipado</div>${eqW}${eqA}`:'')
```

- [ ] **Step 4: Wiring do botão "Usar" + helper `_monConjurador`**

Em `game.js`, no fim de `renderFichaMonstro` (após o wiring de `.fm-usar`), inserir:

```javascript
  host.querySelectorAll('.fm-usar-item').forEach(btn => {
    btn.onclick = () => _mestreUsarItemFicha(m, btn.dataset.iid);
  });
```

E adicionar, logo após `_mestreAtivarHabilidade`, os helpers:

```javascript
function _monConjurador(m){
  return (m.monster_spells && m.monster_spells.length > 0) ||
         (m.special_abilities||[]).some(a => a.action_type === 'magia');
}
function _mestreUsarItemFicha(m, iid){
  const st = GS.gameState; if(!st) return;
  const it = (m.equipment_consumables||[]).find(i=>i.id===iid);
  if(!it) return;
  // Arremessável / pergaminho de alvo: mira um herói.
  if(it.effect === 'throwable' || it.effect === 'scroll'){
    const alvos = (st.players||[]).filter(p=>p.alive);
    if(!alvos.length){ toast('Nenhum herói vivo.', 'var(--orange)'); return; }
    openTargetModal(`${it.name||iid} — Escolha o alvo`, alvos, 'player',
      (alvoId)=> GS.mestreUsarItem(m.id, iid, alvoId, null, null));
    return;
  }
  // Consumível de alvo-próprio: usa direto.
  GS.mestreUsarItem(m.id, iid, null, null, null);
}
```

- [ ] **Step 5: Verificação (leitura/sintaxe)**

Run: `node --check game.js && node --check src/gameState.js`
Expected: sem erros. E `grep -n "_mestreUsarItemFicha\|mestreUsarItem\|equipment_consumables" game.js` mostra o wiring.

- [ ] **Step 6: Commit**

```bash
git add game.js
git commit -m "feat(mestre): ficha do monstro — seção Itens (usar) + habilidades de editor ativáveis"
```

---

### Task 5: Cliente (game.css) — estilos da seção Itens/Equipado

**Files:**
- Modify: `game.css` (após as regras `.fm-*` ~588)

- [ ] **Step 1: Adicionar estilos**

Em `game.css`, após `#ficha-monstro .fm-ia{ ... }`, inserir:

```css
#ficha-monstro .fm-item{ border-top:1px dotted var(--border,#5a4632); padding-top:4px; margin-top:4px; }
#ficha-monstro .fm-usar-item{ background:#2a5a7a; color:#fff; border:none; border-radius:6px; font-size:.72rem; padding:3px 8px; cursor:pointer; }
#ficha-monstro .fm-usar-item:hover:not(:disabled){ background:#3a6f9a; }
#ficha-monstro .fm-usar-item:disabled{ opacity:.4; cursor:not-allowed; }
#ficha-monstro .fm-eq{ font-size:.78rem; opacity:.85; margin:1px 0; }
```

- [ ] **Step 2: Commit**

```bash
git add game.css
git commit -m "style(mestre): estilos da seção Itens/Equipado da ficha do monstro"
```

---

### Task 6: Smoke in-app + doc no CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rodar a suíte do servidor**

Run: `python tools/test_modo_mestre.py`
Expected: `=== N passaram, 0 falharam ===`.

- [ ] **Step 2: Smoke in-app (2 abas: mestre + herói) com o "soldado"**

Subir o jogo, pôr um **soldado** em Manual. Conferir na ficha: seção **Itens** (Poção de Cura → cura o monstro/ação bônus; Granada/Rede → mira um herói/ação principal; Cantil/Cerveja → "sem efeito"); seção **Ações** com **Mira Certeira** ativável mostrando **usos (3) e recarga (4r)**, gastando ao ativar; **Equipado** mostrando Espada Longa + armaduras.

- [ ] **Step 3: Documentar no CLAUDE.md**

Em `CLAUDE.md`, na seção do Modo Mestre, inserir uma nota resumindo o SP2 (itens de bolsa usáveis pelo mestre via `equipment_consumables`/`handle_mestre_usar_item`; habilidades de editor ativáveis via `_ativar_editor_ability`; economia bônus/principal; food recusado; pergaminho só conjurador; seção Itens/Equipado na ficha; teste seções [27]/[28]).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mestre): SP2 inventário do monstro (itens usáveis + habilidades de editor)"
```

---

## Notas de verificação

- **Server:** TDD via `tools/test_modo_mestre.py` (`check()`), `python tools/test_modo_mestre.py`.
- **Client:** sem runner JS — `node --check` + leitura + smoke in-app (Task 6).
- **WIP bundlado:** commits usam `git add <arquivos específicos>`; nunca `-A`.
- **Paridade sem-mestre:** tudo gateia por `pid==master_pid` + janela Manual.
