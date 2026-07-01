# Guilda — Fase 1a (Especializações do Guerreiro) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enfraquecer as 3 habilidades-base do Guerreiro e vender os incrementos como Especializações na Guilda (Combinar Duas, Mestre de Combate, Mira/Golpe/Fúria III), reusando a infra de compra/persistência da Fase 0.

**Architecture:** Servidor autoritativo. Entradas `categoria:"especializacao"` no `GUILD_CATALOG` (só exibição/compra — `handle_guild_buy` já valida). Efeitos aplicados inline em `handle_attack` via helpers pequenos e testáveis: `tem_espec` (posse), `_teto_combinacao` (1/2/3 habilidades armadas), `_golpe_raw` (×1,5 base / ×2 com III), `_furia_extras` (1 ou 2 ataques extras) e `skill_bonus_dano` (Mira III). Cliente limita a armação e reflete os níveis na UI.

**Tech Stack:** Python 3 + `websockets` (servidor); Vanilla JS (cliente). Testes no harness caseiro do projeto (`tools/test_*.py`: `main()` async + `check()`, rodado da raiz), **não** pytest.

**Spec:** `docs/superpowers/specs/2026-07-01-guilda-fase1a-guerreiro-design.md`

---

## Contexto de código (anchors verificados — localizar por conteúdo, linhas podem deslocar)

- `GUILD_CATALOG` + helpers de guilda (`guild_item`, `guild_items_for_class`) e `handle_guild_buy` já existem (Fase 0). `handle_guild_buy` valida `classe`/`requer`/posse/ouro e persiste em `guild_owned.especializacoes`.
- `make_player` tem hoje (server.py ~2993-2996): `"skill_bonus_acerto": 0`, `"skill_dobrar_dano": False`, `"skill_ataque_extra": False`, `"skill_extra_usado": False`.
- `handle_attack` (server.py):
  - Bloco "Habilidades ARMADAS do warrior" (~4849): `sel = [s for s in p.get("skills", []) if s["id"] in buffs and "mp" not in s]`; debita custo; loop seta flags: `mira_certeira`→`skill_bonus_acerto += 2` (~4862), `golpe_devastador`→`skill_dobrar_dano = True` (~4864), `furia_berserker`→`skill_ataque_extra = True` (~4866).
  - Golpe dobra em **3 lugares**: armado principal `raw_dmg *= 2` (~4949-4950); desarmado `base = 2 if skill_dobrar_dano else 1` (~4972); **mão secundária** `oraw *= 2` (~5077-5078).
  - Soma final do dano (armado principal, ~4958): `dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano + self._mod_magia(p,"dano") + self._tecnica_bonus_dano(p) - self._corrosao_arma_pen(p))`.
  - Fúria extra (~5103): `if p.get("skill_ataque_extra") and not p.get("skill_extra_usado"): p["skill_extra_usado"] = True; <gm_say> else: p["action_done"] = True`.
- Reset por turno (server.py ~10108-10112): `skill_bonus_acerto=0`, `skill_dobrar_dano=False`, `skill_ataque_extra=False`, `skill_extra_usado=False`.
- Cliente `gameState.js`: `toggleWarriorSkill(id)` (~1318), `isWarriorSkillSelected`, `getWarriorSelected`, `warriorSelected` (array). `guildOwnedOf(pid)` (Fase 0) já cai p/ o player do `game_state` na masmorra.
- Cliente `game.js`: render dos botões do warrior no loop de skills; o toggle é ligado em `btn.onclick = () => { _wToggle(sk.id); renderMyPanel(GS.gameState); }` (~9794). `_wToggle`/`_wSel` são wrappers de `GS.toggleWarriorSkill`/`GS.isWarriorSkillSelected`.

**Convenção de teste** (novo `tools/test_guerreiro_espec.py`): mesmo cabeçalho de `tools/test_guilda.py` (import `server as S`, `from server import GameRoom, make_player`, `check()`, `setup()`), summary + `sys.exit(1 if FAIL else 0)` no fim. Testes de compra usam pasta temporária (`S.GUILD_SAVE_DIR`) e limpam `S.CHARACTERS_IN_USE`.

---

## Task 1: Catálogo do Guerreiro + helper `tem_espec`

**Files:** Modify `server.py`; Create `tools/test_guerreiro_espec.py`.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_guerreiro_espec.py`:
```python
"""Especializações do Guerreiro (Fase 1a). Roda da raiz: python tools/test_guerreiro_espec.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup(phase="playing"):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r.phase = phase; r._errs = errs
    return r

def warrior(**owned):
    p = make_player("p1", "Victor", "warrior", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    return p

async def main():
    # [1] Catálogo + tem_espec
    print("\n[1] Catálogo do Guerreiro")
    ids = [i["id"] for i in S.guild_items_for_class("warrior")]
    for eid in ["guerreiro_combinar_2","guerreiro_mestre_combate","guerreiro_mira_3",
                "guerreiro_golpe_3","guerreiro_furia_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("combinar_2 sem requer", S.guild_item("guerreiro_combinar_2")["requer"] is None)
    check("mestre requer combinar_2", S.guild_item("guerreiro_mestre_combate")["requer"] == "guerreiro_combinar_2")
    check("mira_3 requer combinar_2", S.guild_item("guerreiro_mira_3")["requer"] == "guerreiro_combinar_2")
    check("preço combinar_2 = 150", S.guild_item("guerreiro_combinar_2")["preco"] == 150)
    check("preço mestre = 300", S.guild_item("guerreiro_mestre_combate")["preco"] == 300)
    check("preço mira_3 = 200", S.guild_item("guerreiro_mira_3")["preco"] == 200)
    p = warrior(esp=["guerreiro_golpe_3"])
    check("tem_espec True", S.tem_espec(p, "guerreiro_golpe_3"))
    check("tem_espec False", not S.tem_espec(p, "guerreiro_mira_3"))

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar — MUST fail** (`guerreiro_combinar_2` ausente / `tem_espec` inexistente).
Run: `python tools/test_guerreiro_espec.py`

- [ ] **Step 3: Adicionar as 5 entradas ao `GUILD_CATALOG`** (dentro do dict, após `"brutalidade": {...},`):
```python
    "guerreiro_combinar_2": {
        "id": "guerreiro_combinar_2", "categoria": "especializacao", "classe": "warrior",
        "linha": "guerreiro_combate", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Combinar Duas", "icon": "⚔️",
        "desc": "Permite armar DUAS habilidades no mesmo turno.",
    },
    "guerreiro_mestre_combate": {
        "id": "guerreiro_mestre_combate", "categoria": "especializacao", "classe": "warrior",
        "linha": "guerreiro_combate", "nivel": 4, "requer": "guerreiro_combinar_2", "exclusiva": False,
        "preco": 300, "nome": "Mestre de Combate", "icon": "🏆",
        "desc": "Permite armar as TRÊS habilidades no mesmo turno.",
    },
    "guerreiro_mira_3": {
        "id": "guerreiro_mira_3", "categoria": "especializacao", "classe": "warrior",
        "linha": "guerreiro_mira", "nivel": 3, "requer": "guerreiro_combinar_2", "exclusiva": False,
        "preco": 200, "nome": "Mira Certeira III", "icon": "🎯",
        "desc": "Mira Certeira também concede +2 de dano (além do +2 de acerto).",
    },
    "guerreiro_golpe_3": {
        "id": "guerreiro_golpe_3", "categoria": "especializacao", "classe": "warrior",
        "linha": "guerreiro_golpe", "nivel": 3, "requer": "guerreiro_combinar_2", "exclusiva": False,
        "preco": 200, "nome": "Golpe Devastador III", "icon": "💥",
        "desc": "Golpe Devastador passa a multiplicar os dados de dano por 2 (era ×1,5).",
    },
    "guerreiro_furia_3": {
        "id": "guerreiro_furia_3", "categoria": "especializacao", "classe": "warrior",
        "linha": "guerreiro_furia", "nivel": 3, "requer": "guerreiro_combinar_2", "exclusiva": False,
        "preco": 200, "nome": "Fúria Berserker III", "icon": "🔥",
        "desc": "Fúria Berserker concede 2 ataques extras (3 ataques no total).",
    },
```

- [ ] **Step 4: Adicionar o helper `tem_espec`** (server.py, junto de `guild_item`/`guild_items_for_class`):
```python
def tem_espec(player, espec_id):
    """True se o jogador possui a especialização comprada (Fase 1+)."""
    return espec_id in player.get("guild_owned", {}).get("especializacoes", [])
```

- [ ] **Step 5: Rodar — MUST pass.** Run: `python tools/test_guerreiro_espec.py` → 0 falharam.

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_guerreiro_espec.py
git commit -m "feat(guilda): catalogo de especializacoes do Guerreiro + helper tem_espec"
```

---

## Task 2: Campos novos + refactor da Fúria (booleanos → contador)

**Files:** Modify `server.py` (`make_player`, reset de turno, `handle_attack` arming + ponto do extra); `tools/test_guerreiro_espec.py`.

- [ ] **Step 1: Teste que falha** — adicionar em `main()` antes do summary:
```python
    # [2] Campos novos + Fúria contador
    print("\n[2] Fúria contador + campos")
    r = setup("playing")
    check("_furia_extras base = 1", r._furia_extras(warrior()) == 1)
    check("_furia_extras III = 2", r._furia_extras(warrior(esp=["guerreiro_furia_3"])) == 2)
    p = make_player("p1", "Victor", "warrior", 0)
    check("make_player tem skill_ataques_extras", p.get("skill_ataques_extras") == 0)
    check("make_player tem skill_bonus_dano", p.get("skill_bonus_dano") == 0)
    check("removeu skill_ataque_extra", "skill_ataque_extra" not in p)
    check("removeu skill_extra_usado", "skill_extra_usado" not in p)
```

- [ ] **Step 2: Rodar — MUST fail** (`_furia_extras` inexistente; campos ausentes).

- [ ] **Step 3: `make_player`** — trocar as 4 linhas (~2993-2996) por:
```python
        "skill_bonus_acerto": 0,
        "skill_bonus_dano":   0,      # Mira Certeira III: +2 dano quando armada
        "skill_dobrar_dano":  False,
        "skill_ataques_extras": 0,    # Fúria: nº de ataques extras restantes neste turno (1 base / 2 c/ III)
```

- [ ] **Step 4: Helper `_furia_extras`** (método de `GameRoom`, perto de `_tecnica_bonus_dano`):
```python
    def _furia_extras(self, p):
        """Ataques extras concedidos pela Fúria: 2 com Nível III, senão 1."""
        return 2 if tem_espec(p, "guerreiro_furia_3") else 1
```

- [ ] **Step 5: Arming da Fúria** (~4866) — trocar:
```python
                    elif sid == "furia_berserker":
                        p["skill_ataque_extra"] = True
```
por:
```python
                    elif sid == "furia_berserker":
                        p["skill_ataques_extras"] = self._furia_extras(p)
```

- [ ] **Step 6: Ponto do ataque extra** (~5103) — trocar o bloco:
```python
        if p.get("skill_ataque_extra") and not p.get("skill_extra_usado"):
            p["skill_extra_usado"] = True
            await self.gm_say(f"🔥 **{p['name']}** — Fúria Berserker: ataque extra disponível! Ataque novamente.")
        else:
            p["action_done"] = True
```
por:
```python
        if p.get("skill_ataques_extras", 0) > 0:
            p["skill_ataques_extras"] -= 1
            await self.gm_say(f"🔥 **{p['name']}** — Fúria Berserker: ataque extra disponível! Ataque novamente.")
        else:
            p["action_done"] = True
```

- [ ] **Step 7: Reset por turno** (~10108-10112) — trocar as linhas dos 4 campos por:
```python
        p["skill_bonus_acerto"] = 0
        p["skill_bonus_dano"]   = 0
        p["skill_dobrar_dano"]  = False
        p["skill_ataques_extras"] = 0
```

- [ ] **Step 8: Verificar que não sobrou referência** aos campos antigos:
Run: `grep -rn "skill_ataque_extra\|skill_extra_usado" server.py`
Expected: **nenhuma** ocorrência (todas migradas). Se aparecer, migrar.

- [ ] **Step 9: Rodar testes — MUST pass** (guerreiro_espec + regressão):
Run: `python tools/test_guerreiro_espec.py` → 0 falharam
Run: `python tools/test_devorador.py` → deve continuar (combate); anote o resultado.

- [ ] **Step 10: Commit**
```bash
git add server.py tools/test_guerreiro_espec.py
git commit -m "feat(guilda): Furia como contador de ataques extras + campos skill_bonus_dano/skill_ataques_extras"
```

---

## Task 3: Teto de combinação (1/2/3 habilidades)

**Files:** Modify `server.py` (`handle_attack` arming); `tools/test_guerreiro_espec.py`.

- [ ] **Step 1: Teste que falha** — adicionar em `main()`:
```python
    # [3] Teto de combinação
    print("\n[3] Teto de combinação")
    r = setup("playing")
    check("teto base = 1", r._teto_combinacao(warrior()) == 1)
    check("teto combinar_2 = 2", r._teto_combinacao(warrior(esp=["guerreiro_combinar_2"])) == 2)
    check("teto mestre = 3", r._teto_combinacao(warrior(esp=["guerreiro_combinar_2","guerreiro_mestre_combate"])) == 3)
```

- [ ] **Step 2: Rodar — MUST fail** (`_teto_combinacao` inexistente).

- [ ] **Step 3: Helper `_teto_combinacao`** (método de `GameRoom`):
```python
    def _teto_combinacao(self, p):
        """Máx. de habilidades do warrior armadas por turno pela posse de especializações."""
        if tem_espec(p, "guerreiro_mestre_combate"): return 3
        if tem_espec(p, "guerreiro_combinar_2"):      return 2
        return 1
```

- [ ] **Step 4: Truncar `sel` no arming** (~4849-4851) — logo após montar `sel`, antes de somar custo:
```python
                sel = [s for s in p.get("skills", [])
                       if s["id"] in buffs and "mp" not in s]
                teto = self._teto_combinacao(p)
                if len(sel) > teto:
                    sel = sel[:teto]
                    await self.gm_say(f"**{p['name']}** só pode combinar {teto} habilidade(s) por turno — as demais foram ignoradas.")
```
(O resto do bloco — soma de custo, loop de flags — continua operando sobre `sel`.)

- [ ] **Step 5: Rodar — MUST pass.** Run: `python tools/test_guerreiro_espec.py` → 0 falharam.

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_guerreiro_espec.py
git commit -m "feat(guilda): teto autoritativo de combinacao de habilidades do Guerreiro"
```

---

## Task 4: Golpe Devastador ×1,5 base / ×2 com III

**Files:** Modify `server.py` (`handle_attack` — armado principal + mão secundária); `tools/test_guerreiro_espec.py`.

- [ ] **Step 1: Teste que falha** — adicionar em `main()`:
```python
    # [4] Golpe ×1,5 / ×2
    print("\n[4] Golpe Devastador")
    r = setup("playing")
    base = warrior(); base["skill_dobrar_dano"] = True
    check("sem golpe_3 → ×1,5 (10→15)", r._golpe_raw(base, 10) == 15)
    check("×1,5 arredonda p/ baixo (7→10)", r._golpe_raw(base, 7) == 10)
    iii = warrior(esp=["guerreiro_golpe_3"]); iii["skill_dobrar_dano"] = True
    check("com golpe_3 → ×2 (10→20)", r._golpe_raw(iii, 10) == 20)
    off = warrior(); off["skill_dobrar_dano"] = False
    check("golpe não armado → sem mudança", r._golpe_raw(off, 10) == 10)
```

- [ ] **Step 2: Rodar — MUST fail** (`_golpe_raw` inexistente).

- [ ] **Step 3: Helper `_golpe_raw`** (método de `GameRoom`):
```python
    def _golpe_raw(self, p, raw):
        """Golpe Devastador nos dados: ×2 com Nível III, ×1,5 (floor) no base; sem efeito se não armado."""
        if not p.get("skill_dobrar_dano"):
            return raw
        if tem_espec(p, "guerreiro_golpe_3"):
            return raw * 2
        return raw + raw // 2
```

- [ ] **Step 4: Aplicar no armado principal** (~4949-4950) — trocar:
```python
                    if p.get("skill_dobrar_dano"):
                        raw_dmg *= 2   # Golpe Devastador: dobra os dados de dano
```
por:
```python
                    raw_dmg = self._golpe_raw(p, raw_dmg)   # Golpe: ×1,5 base / ×2 com Nível III
```

- [ ] **Step 5: Aplicar na mão secundária** (~5077-5078) — trocar:
```python
                    if p.get("skill_dobrar_dano"):
                        oraw *= 2
```
por:
```python
                    oraw = self._golpe_raw(p, oraw)   # Golpe também vale na mão secundária
```

> **Nota:** o ramo DESARMADO (~4972, `base = 2 if skill_dobrar_dano else 1`) fica **inalterado** de propósito (caso de canto; dano fixo 1→2 já modesto). Documentado no spec §4.2.

- [ ] **Step 6: Rodar testes — MUST pass** (guerreiro_espec + devorador de regressão).
Run: `python tools/test_guerreiro_espec.py` → 0 falharam
Run: `python tools/test_devorador.py` → anote o resultado.

- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_guerreiro_espec.py
git commit -m "feat(guilda): Golpe Devastador x1.5 base / x2 com Nivel III (helper _golpe_raw)"
```

---

## Task 5: Mira Certeira III (+2 dano)

**Files:** Modify `server.py` (`handle_attack` arming + soma do dano); `tools/test_guerreiro_espec.py`.

- [ ] **Step 1: Teste que falha** — adicionar em `main()`:
```python
    # [5] Mira Certeira III (+2 dano)
    print("\n[5] Mira III")
    r = setup("playing")
    check("_mira_dano base = 0", r._mira_dano_bonus(warrior()) == 0)
    check("_mira_dano III = 2", r._mira_dano_bonus(warrior(esp=["guerreiro_mira_3"])) == 2)
```

- [ ] **Step 2: Rodar — MUST fail** (`_mira_dano_bonus` inexistente).

- [ ] **Step 3: Helper `_mira_dano_bonus`** (método de `GameRoom`):
```python
    def _mira_dano_bonus(self, p):
        """+2 de dano da Mira Certeira III (0 se não possuído)."""
        return 2 if tem_espec(p, "guerreiro_mira_3") else 0
```

- [ ] **Step 4: Arming da Mira** (~4862-4863) — trocar:
```python
                    if sid == "mira_certeira":
                        p["skill_bonus_acerto"] = p.get("skill_bonus_acerto", 0) + 2
```
por:
```python
                    if sid == "mira_certeira":
                        p["skill_bonus_acerto"] = p.get("skill_bonus_acerto", 0) + 2
                        p["skill_bonus_dano"] = p.get("skill_bonus_dano", 0) + self._mira_dano_bonus(p)
```

- [ ] **Step 5: Somar `skill_bonus_dano` no dano** (armado principal ~4958-4960) — adicionar `+ p.get("skill_bonus_dano", 0)` dentro do `max(1, ...)`:
```python
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") + self._tecnica_bonus_dano(p)
                              + p.get("skill_bonus_dano", 0)
                              - self._corrosao_arma_pen(p))
```

- [ ] **Step 6: Rodar — MUST pass.** Run: `python tools/test_guerreiro_espec.py` → 0 falharam.

- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_guerreiro_espec.py
git commit -m "feat(guilda): Mira Certeira III concede +2 de dano"
```

---

## Task 6: Cliente — teto de armação + descrições por nível

**Files:** Modify `src/gameState.js`, `game.js`.

- [ ] **Step 1: Getter `warriorComboCap` em `gameState.js`** — perto de `toggleWarriorSkill` (~1318):
```javascript
  // Teto de habilidades armadas do warrior pela posse de especializações da Guilda.
  function warriorComboCap() {
    const esp = (guildOwnedOf(myPid).especializacoes) || [];
    if (esp.includes('guerreiro_mestre_combate')) return 3;
    if (esp.includes('guerreiro_combinar_2'))     return 2;
    return 1;
  }
```
Exportar no `return { ... }` (junto de `toggleWarriorSkill`): adicionar `warriorComboCap,`.

- [ ] **Step 2: Guardar o teto no toggle (game.js)** — no `onclick` do botão do warrior (~9794), trocar:
```javascript
      btn.onclick = () => { _wToggle(sk.id); renderMyPanel(GS.gameState); };
```
por:
```javascript
      btn.onclick = () => {
        if (!_wSel(sk.id) && GS.getWarriorSelected().length >= GS.warriorComboCap()) {
          const cap = GS.warriorComboCap();
          toast(cap === 1
            ? 'Compre "Combinar Duas" na Guilda para armar 2 habilidades.'
            : `Você só pode armar ${cap} habilidades por turno.`, 'var(--gold)');
          return;
        }
        _wToggle(sk.id); renderMyPanel(GS.gameState);
      };
```
(`GS.getWarriorSelected` já é exportado.)

- [ ] **Step 3: Descrições refletem a posse** — no render do botão do warrior (onde monta `desc`/nome, mesmo loop ~9788), ajustar o texto por posse lida de `GS.guildOwnedOf(me.id).especializacoes`. Exemplo mínimo: se a skill for `golpe_devastador` e possuir `guerreiro_golpe_3`, mostrar "dano ×2" senão "dano ×1,5"; `mira_certeira` com `guerreiro_mira_3` → "+2 acerto, +2 dano"; `furia_berserker` com `guerreiro_furia_3` → "2 ataques extras". Ler uma vez antes do loop:
```javascript
  const _esp = (GS.guildOwnedOf(me.id).especializacoes) || [];
  const _golpeMult = _esp.includes('guerreiro_golpe_3') ? '×2' : '×1,5';
  const _miraTxt   = _esp.includes('guerreiro_mira_3') ? '+2 acerto, +2 dano' : '+2 acerto';
  const _furiaTxt  = _esp.includes('guerreiro_furia_3') ? '2 ataques extras' : '+1 ataque extra';
```
e usar essas strings na `desc` do respectivo botão (substituindo o texto fixo atual das 3 skills do warrior). **Ler o loop inteiro antes** para inserir sem quebrar as outras classes.

- [ ] **Step 4: Syntax check.** Run: `node --check src/gameState.js && node --check game.js` → exit 0.

- [ ] **Step 5: Commit**
```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): cliente respeita teto de combinacao + descricoes por nivel (Guerreiro)"
```

---

## Task 7: Verificação E2E + docs

**Files:** Modify `CLAUDE.md`.

- [ ] **Step 1: Suíte de servidor**
Run: `python tools/test_guerreiro_espec.py` → 0 falharam
Run: `python tools/test_guilda.py` → 0 falharam (Fase 0 intacta)
Run: `python tools/test_devorador.py` → combate ok (regressão do refactor da Fúria/Golpe)

- [ ] **Step 2: Smoke test in-app** (padrão da Fase 0 — `.claude/launch.json` já tem o server `game`, `autoPort:false`):
  - Subir preview; criar sala; escolher Guerreiro; **na Guilda**: sem `combinar_2`, tentar comprar `guerreiro_mira_3` → recusado (pré-requisito). Comprar `combinar_2`, depois `guerreiro_golpe_3`.
  - Na masmorra: tentar armar 2 habilidades sem `combinar_2` → cliente bloqueia (toast). Após comprar `combinar_2` → arma 2.
  - Golpe: confirmar que o botão mostra ×2 após comprar `guerreiro_golpe_3`.
  - *(Para dar ouro, reusar o truque temporário-e-revertido de `start_gold` da Fase 0; ao fim, reverter e remover `saves/`.)*
  - Confirmar zero erros de console (`preview_console_logs level:error`).

- [ ] **Step 3: Atualizar `CLAUDE.md`** — na seção da Guilda, acrescentar um parágrafo curto: "Especializações do Guerreiro (Fase 1a): baseline enfraquecido (Golpe ×1,5, 1 habilidade/turno) + compras `guerreiro_combinar_2`/`mestre_combate`/`mira_3`/`golpe_3`/`furia_3`; efeitos em `handle_attack` via `tem_espec`/`_teto_combinacao`/`_golpe_raw`/`_furia_extras`/`_mira_dano_bonus`; teste `tools/test_guerreiro_espec.py`." Registrar o **nerf do Golpe** como mudança de gameplay.

- [ ] **Step 4: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(guilda): documentar especializacoes do Guerreiro (Fase 1a)"
```

---

## Self-review (cobertura do spec)

- **§2 baseline enfraquecido** → Task 3 (teto=1) + Task 4 (Golpe ×1,5). ✔
- **§3 catálogo (5 nós, preços, requer)** → Task 1. ✔
- **§4.1 limite de combinação autoritativo** → Task 3. ✔
- **§4.2 Golpe ×1,5/×2 (3 lugares; desarmado inalterado)** → Task 4 (armado principal + mão secundária; desarmado documentado). ✔
- **§4.3 Mira III +2 dano** → Task 5. ✔
- **§4.4 Fúria contador** → Task 2. ✔
- **§5 make_player + reset** → Task 2. ✔
- **§6 cliente (teto + descrições)** → Task 6. ✔
- **§7 testes** → `tools/test_guerreiro_espec.py` (Tasks 1-5) + smoke (Task 7). ✔
- **§9 riscos (nerf Golpe, refactor Fúria)** → nerf documentado (Task 7); refactor com grep de referências (Task 2 Step 8) + regressão devorador (Tasks 2/4). ✔

**Consistência de nomes:** `tem_espec` (módulo); `_teto_combinacao`/`_golpe_raw`/`_furia_extras`/`_mira_dano_bonus` (métodos de `GameRoom`); campos `skill_bonus_dano`/`skill_ataques_extras` (novos), `skill_ataque_extra`/`skill_extra_usado` (removidos); cliente `warriorComboCap` + `getWarriorSelected`/`guildOwnedOf` (já existentes). Ids do catálogo: `guerreiro_combinar_2`/`guerreiro_mestre_combate`/`guerreiro_mira_3`/`guerreiro_golpe_3`/`guerreiro_furia_3`.
