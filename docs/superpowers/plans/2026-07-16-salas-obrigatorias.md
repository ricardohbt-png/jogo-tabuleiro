# Salas Obrigatórias — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development ou executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Marcar salas como obrigatórias (visitar/limpar) no editor, expostas como o objetivo `salas_obrigatorias`, com progresso N/M.

**Architecture:** Cada sala ganha `required`+`required_mode`. Servidor rastreia visitas (`salas_visitadas` em `handle_move`) e avalia o objetivo em `_objetivo_cumprido`, com progresso no payload de status; validação exige ≥1 sala marcada. Editor: checkbox no painel da sala + opção no dropdown de objetivo. Cliente: rótulo/progresso do objetivo.

**Spec:** `docs/superpowers/specs/2026-07-16-salas-obrigatorias-design.md`

**Base:** limpa (WIP do usuário no checkpoint `4391e12`). `git add <arquivos específicos>`.

---

## Task 1: Servidor — objetivo + rastreio de visita + validação

**Files:** `server.py` (`__init__` ~4728; dungeon-entry reset ~6557; `handle_move` ~7209; `_objetivo_cumprido` ~18212; status payload ~18250; `validar_dungeon`). Test: `tools/test_modo_mestre.py`.

- [ ] **Step 1: Teste que falha** — em `main()`:
```python
    print("\n[23] Salas obrigatórias")
    r = playing_room_com_mestre()
    r.rooms = [{"id":0,"x":0,"y":0,"w":3,"h":3,"required":True,"required_mode":"clear"},
               {"id":1,"x":5,"y":0,"w":3,"h":3,"required":True,"required_mode":"visit"},
               {"id":2,"x":0,"y":5,"w":3,"h":3}]
    r.salas_visitadas = set()
    r.monsters = {"m":{"id":"m","hp":5,"room_id":0,"pos":[1,1]}}
    obj = {"type":"salas_obrigatorias"}
    check("pendente: sala 0 com monstro vivo", r._objetivo_cumprido(obj) is False)
    p = r._salas_obrigatorias_progresso()
    check("progresso 0/2 (visit ainda não, clear ainda não)", p == (0, 2))
    r.monsters["m"]["hp"] = 0   # sala 0 limpa
    r.salas_visitadas.add(1)    # sala 1 visitada
    check("cumprido quando todas atendem", r._objetivo_cumprido(obj) is True)
    check("progresso 2/2", r._salas_obrigatorias_progresso() == (2, 2))
    # clear de sala vazia conta
    r2 = playing_room_com_mestre()
    r2.rooms = [{"id":0,"x":0,"y":0,"w":3,"h":3,"required":True,"required_mode":"clear"}]
    r2.salas_visitadas = set(); r2.monsters = {}
    check("clear de sala vazia = cumprida", r2._objetivo_cumprido({"type":"salas_obrigatorias"}) is True)
    # validação
    base_sr = dict(base); base_sr["objectives"] = {"primary": {"type":"salas_obrigatorias"}, "secondary": []}
    ok, msg = S.validar_dungeon(base_sr)
    check("obj sem salas marcadas rejeitado", ok is False and "salas" in msg.lower())
```

- [ ] **Step 2: Rodar e ver falhar** — `AttributeError: _salas_obrigatorias_progresso` / `salas_visitadas`.

- [ ] **Step 3: Implementar**

(a) `__init__` (~4728, perto de `mission_complete_pending`): `self.salas_visitadas = set()`.

(b) Reset na entrada da masmorra (~6557, junto de `self.mission_complete_pending = False`): `self.salas_visitadas = set()`.

(c) `_objetivo_cumprido` — antes do `return False` final, adicionar:
```python
        if t == "salas_obrigatorias":
            req = [rm for rm in self.rooms if rm.get("required")]
            return all(self._sala_obrigatoria_ok(rm) for rm in req)
```
E dois helpers (perto de `_objetivo_cumprido`):
```python
    def _sala_obrigatoria_ok(self, rm):
        if rm.get("required_mode") == "visit":
            return rm["id"] in self.salas_visitadas
        # default: clear — sem monstros vivos com aquele room_id
        return not any(m["hp"] > 0 and m.get("room_id") == rm["id"]
                       for m in self.monsters.values())

    def _salas_obrigatorias_progresso(self):
        req = [rm for rm in self.rooms if rm.get("required")]
        feitas = sum(1 for rm in req if self._sala_obrigatoria_ok(rm))
        return feitas, len(req)
```

(d) Rastreio de visita em `handle_move` — após o passo do herói ser confirmado (onde `p["pos"]` é atualizado; procurar o commit do movimento), adicionar:
```python
        _sala_atual = player_room(self.rooms, p["pos"][0], p["pos"][1])
        if _sala_atual is not None:
            self.salas_visitadas.add(_sala_atual["id"])
```

(e) Status com progresso — em `_check_objectives`, onde monta `"primary"`/`"secondary"`, incluir o progresso para objetivos `salas_obrigatorias`. Trocar a construção por um helper:
```python
    def _objetivo_payload(self, obj):
        d = {"type": (obj or {}).get("type"), "status": self._objetivo_status(obj)}
        if d["type"] == "salas_obrigatorias":
            f, t = self._salas_obrigatorias_progresso()
            d["progresso"] = {"feitas": f, "total": t}
        return d
```
E usar `self._objetivo_payload(prim)` / `[self._objetivo_payload(s) for s in secs]` no lugar das linhas atuais.

(f) `validar_dungeon` — no bloco de objetivos (ou perto do fim), validar:
```python
    _objs = []
    _o = defn.get("objectives") or {}
    if _o.get("primary"): _objs.append(_o["primary"])
    _objs.extend(_o.get("secondary") or [])
    _rooms_req = [r for r in (defn.get("rooms") or []) if isinstance(r, dict) and r.get("required")]
    for _ob in _objs:
        if isinstance(_ob, dict) and _ob.get("type") == "salas_obrigatorias" and not _rooms_req:
            return False, "objetivo salas_obrigatorias sem salas marcadas como obrigatórias."
    for _r in (defn.get("rooms") or []):
        if isinstance(_r, dict) and _r.get("required_mode") not in (None, "visit", "clear"):
            return False, f"required_mode inválido: {_r.get('required_mode')!r} (visit|clear)."
```

- [ ] **Step 4: Rodar e ver passar** — seção [23].

- [ ] **Step 5: Commit** — `git add server.py tools/test_modo_mestre.py` + `feat(mestre): objetivo salas_obrigatorias + rastreio de visita`.

---

## Task 2: Editor — marcação da sala + dropdown + serialização

**Files:** `tools/editor.js` (room panel ~1020; OBJ ~871; rooms save ~1281; rooms load ~1419).

- [ ] **Step 1: Checkbox + seletor no painel da sala** — no bloco `k === "room"` (~1020), após o checkbox `p-locked`, acrescentar à template:
```javascript
        + `<label style="display:block;margin-top:6px"><input type="checkbox" id="p-required" ${ref.required ? "checked" : ""}> sala obrigatória</label>`
        + (ref.required ? `<label>modo</label><select id="p-reqmode"><option value="clear"${(ref.required_mode||"clear")==="clear"?" selected":""}>limpar (matar monstros)</option><option value="visit"${ref.required_mode==="visit"?" selected":""}>visitar (entrar)</option></select>` : "")
```
E o wiring (após os handlers de role/locked):
```javascript
      document.getElementById("p-required").onchange = e => { if (e.target.checked) { ref.required = true; if (!ref.required_mode) ref.required_mode = "clear"; } else { delete ref.required; delete ref.required_mode; } renderPanel(); };
      if (ref.required) { var _rm = document.getElementById("p-reqmode"); if (_rm) _rm.onchange = e => { ref.required_mode = e.target.value; }; }
```
> A template do painel `k === "room"` é uma única atribuição a `panel.innerHTML`. Concatene os trechos `+` \`...\` na expressão (ajuste crases). Se o `role` já cobrir semântica, mantenha ambos.

- [ ] **Step 2: Dropdown de objetivo** — em `const OBJ = [...]` (~871), adicionar `"salas_obrigatorias"`.

- [ ] **Step 3: Serialização das salas** — no `save()` (rooms ~1281), incluir os campos quando presentes:
```javascript
      rooms: S.rooms.map(r => Object.assign({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: r.locked, doors: r.doors.map(d => d.slice()) }, r.required ? { required: true, required_mode: r.required_mode || "clear" } : {})),
```
No load (rooms ~1419), preservar:
```javascript
    S.rooms = (obj.rooms || []).map(r => Object.assign({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: !!r.locked, doors: (r.doors || []).map(d => d.slice()) }, r.required ? { required: true, required_mode: r.required_mode === "visit" ? "visit" : "clear" } : {}));
```

- [ ] **Step 4: `node --check tools/editor.js`.**

- [ ] **Step 5: Commit** — `git add tools/editor.js` + `feat(editor): marcar sala obrigatoria (visitar/limpar) + objetivo`.

---

## Task 3: Cliente — rótulo/progresso do objetivo

**Files:** `game.js` (onde os objetivos são rotulados/renderizados).

- [ ] **Step 1: Localizar** onde `game_state` objetivos viram texto (busca por `kill_all`/`reach_exit`/`objetivo`/`objectives` em game.js).

- [ ] **Step 2: Implementar** — adicionar o rótulo amigável de `salas_obrigatorias` ("Salas obrigatórias") e, se o objetivo tem `progresso`, anexar " (f/t salas)". Reusar o padrão de rótulo existente dos outros tipos.

- [ ] **Step 3: `node --check game.js`.**

- [ ] **Step 4: Commit** — `git add game.js` + `feat(mestre): rotulo/progresso do objetivo salas_obrigatorias`.

---

## Task 4: Docs (CLAUDE.md)

- [ ] Nota curta na seção da Camada C: objetivo `salas_obrigatorias` (por sala visitar/limpar, progresso N/M, `salas_visitadas`, validação). Commit.

---

## Verificação final
1. `python tools/test_modo_mestre.py` — seção [23] verde, sem regressão.
2. `node --check game.js tools/editor.js`.
3. Manual: marcar 2 salas (1 visitar, 1 limpar) + objetivo salas_obrigatorias; conferir progresso e cumprimento em jogo.
