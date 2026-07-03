# Especializações do Mago (Guilda Fase 1f) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar à Guilda as especializações de Metamagia do Mago (Pedro): Tecelagem Arcana (cap de empilhamento) e magnitudes de Fortalecer/Aprimorar/Estender, com baseline enfraquecido, tudo autoritativo no servidor.

**Architecture:** Segue o padrão das Fases 1a-1e: entradas `categoria:"especializacao"`, `classe:"mage"` em `GUILD_CATALOG`, gating por `tem_espec` + helpers em `GameRoom`. O núcleo é um helper puro `_resolver_metamagia(p, magia)` que substitui o bloco inline de metamagia em `handle_magia` (mais testável). Nenhum novo protocolo WebSocket.

**Tech Stack:** Python 3 (`server.py`), vanilla JS (`src/gameState.js`, `game.js`), harness de teste próprio (`tools/test_*.py`, rodado com `python tools/test_mago_espec.py`).

**Spec:** `docs/superpowers/specs/2026-07-02-guilda-fase1f-mago-design.md`

---

## Arquivos tocados

- **Modify** `server.py`:
  - `GUILD_CATALOG` (~279) — 8 nós literais do mago.
  - Helpers novos de `GameRoom` perto de `_teto_combinacao` (~3964): `_teto_metamagia`, `_fortalecer_mult`, `_aprimorar_bonus`, `_estender_bonus`, `_resolver_metamagia`.
  - `handle_magia` (~7897-7921) — troca o bloco inline de metamagia por chamada a `_resolver_metamagia`.
- **Modify** `src/gameState.js` — getters + export.
- **Modify** `game.js` — descrições dos botões de metamagia (`_mageSkillBtn`, ~8429).
- **Create** `tools/test_mago_espec.py`.
- **Modify** `CLAUDE.md` — parágrafo da Fase 1f.

> **Fatos verificados no código:**
> - `tem_espec(player, id)` (server.py:~513): `id in player["guild_owned"]["especializacoes"]`.
> - `_teto_combinacao` (3964) é a referência de teto por especialização.
> - `_magia_tem_dano(self, magia)` (7942): `any(str(k).startswith("dano") for k in magia.keys())` ou id em lista de dano.
> - Bloco de metamagia em `handle_magia` (7900-7921): monta `dmg_mult=1.5`/`dur_bonus=1`/`dc_bonus=1` inline, sem teto, cobrando 🍖/💧 por metamagia aplicável.
> - Cliente: `_mageSkillBtn(me, sk)` (game.js:8429) monta os 3 botões; `desc = sk.description || sk.desc || ''` (8432) é o texto exibido em `.skill-desc` (8449). Padrão de override por nível já existe para o Guerreiro (game.js:~9872).
> - Helpers de catálogo p/ teste: `S.guild_items_for_class(classe)`, `S.guild_item(id)`.
> - `make_player(pid, nome, class_id, idx)` cria jogador com `guild_owned["especializacoes"]`.

---

### Task 1: Catálogo do Mago (8 nós literais)

**Files:**
- Modify: `server.py` (`GUILD_CATALOG`, inserir após o último nó do Bardo `bardo_lendas_supremas`)
- Test: `tools/test_mago_espec.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_mago_espec.py`:

```python
"""Especializações do Mago (Fase 1f). Roda da raiz: python tools/test_mago_espec.py"""
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
    r._is_turn = lambda pid: True
    r.phase = phase; r._errs = errs
    return r

def mage(**owned):
    p = make_player("m", "Pedro", "mage", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]; p["alive"] = True
    return p

# magia fake com dano + duração + save (para exercitar as 3 metamagias)
def magia_completa():
    return {"id": "fake", "dano_por_nivel": "1d6", "duracao": 3, "save": "reflexos"}

async def main():
    # [1] Catálogo do Mago
    print("\n[1] Catálogo do Mago")
    ids = [i["id"] for i in S.guild_items_for_class("mage")]
    for eid in ["mago_tecelagem_2","mago_tecelagem_3","mago_fortalecer_2","mago_fortalecer_3",
                "mago_aprimorar_2","mago_aprimorar_3","mago_estender_2","mago_estender_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("tecelagem_2 = 150", S.guild_item("mago_tecelagem_2")["preco"] == 150)
    check("tecelagem_3 = 300", S.guild_item("mago_tecelagem_3")["preco"] == 300)
    check("fortalecer_2 = 200", S.guild_item("mago_fortalecer_2")["preco"] == 200)
    check("fortalecer_3 = 250", S.guild_item("mago_fortalecer_3")["preco"] == 250)
    check("aprimorar_2 = 150", S.guild_item("mago_aprimorar_2")["preco"] == 150)
    check("estender_2 = 150", S.guild_item("mago_estender_2")["preco"] == 150)
    check("tecelagem_3 requer _2", S.guild_item("mago_tecelagem_3")["requer"] == "mago_tecelagem_2")
    check("fortalecer_3 requer _2", S.guild_item("mago_fortalecer_3")["requer"] == "mago_fortalecer_2")
    check("aprimorar_3 requer _2", S.guild_item("mago_aprimorar_3")["requer"] == "mago_aprimorar_2")
    check("estender_3 requer _2", S.guild_item("mago_estender_3")["requer"] == "mago_estender_2")
    check("aprimorar_2 sem requer", S.guild_item("mago_aprimorar_2")["requer"] is None)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_mago_espec.py`
Expected: FAIL — `guild_item` devolve None p/ os ids `mago_*` (TypeError ou checks vermelhos).

- [ ] **Step 3: Adicionar os 8 nós no `GUILD_CATALOG`**

Em `server.py`, imediatamente após o nó `"bardo_lendas_supremas": { ... },` (fim do bloco do Bardo, antes de `"clerigo_cura_2"` OU onde o bloco do Bardo termina), inserir:

```python
    # ── Mago (Fase 1f) — Metamagia ──────────────────────────────────────────
    "mago_tecelagem_2": {
        "id": "mago_tecelagem_2", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_tecelagem", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Tecelagem Arcana II", "icon": "🧵",
        "desc": "Permite empilhar 2 metamagias no mesmo lançamento.",
    },
    "mago_tecelagem_3": {
        "id": "mago_tecelagem_3", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_tecelagem", "nivel": 3, "requer": "mago_tecelagem_2", "exclusiva": False,
        "preco": 300, "nome": "Tecelagem Arcana III", "icon": "🧵",
        "desc": "Permite empilhar as 3 metamagias no mesmo lançamento.",
    },
    "mago_fortalecer_2": {
        "id": "mago_fortalecer_2", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_fortalecer", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 200, "nome": "Fortalecer II", "icon": "💥",
        "desc": "Fortalecer Magia multiplica o dano por 1,5 (era ×1,25).",
    },
    "mago_fortalecer_3": {
        "id": "mago_fortalecer_3", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_fortalecer", "nivel": 3, "requer": "mago_fortalecer_2", "exclusiva": False,
        "preco": 250, "nome": "Fortalecer III", "icon": "💥",
        "desc": "Fortalecer Magia multiplica o dano por 2.",
    },
    "mago_aprimorar_2": {
        "id": "mago_aprimorar_2", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_aprimorar", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Aprimorar II", "icon": "🎯",
        "desc": "Aprimorar Magia dá +2 na CD do save (era +1).",
    },
    "mago_aprimorar_3": {
        "id": "mago_aprimorar_3", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_aprimorar", "nivel": 3, "requer": "mago_aprimorar_2", "exclusiva": False,
        "preco": 200, "nome": "Aprimorar III", "icon": "🎯",
        "desc": "Aprimorar Magia dá +3 na CD do save.",
    },
    "mago_estender_2": {
        "id": "mago_estender_2", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_estender", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Estender II", "icon": "⏱️",
        "desc": "Estender Magia dá +2 rodadas de duração (era +1).",
    },
    "mago_estender_3": {
        "id": "mago_estender_3", "categoria": "especializacao", "classe": "mage",
        "linha": "mago_estender", "nivel": 3, "requer": "mago_estender_2", "exclusiva": False,
        "preco": 200, "nome": "Estender III", "icon": "⏱️",
        "desc": "Estender Magia dá +3 rodadas de duração.",
    },
```

> Localize o fim do bloco do Bardo por conteúdo (`"bardo_lendas_supremas"`). Se não achar, insira os 8 nós em qualquer ponto dentro do dict `GUILD_CATALOG` literal (antes do fechamento `}` do dict), mantendo o estilo/indentação de 4 espaços.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_mago_espec.py`
Expected: PASS na seção [1] (FAIL=0 se só a [1] existe).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_mago_espec.py
git commit -m "feat(guilda): catalogo do Mago (Metamagia: Tecelagem/Fortalecer/Aprimorar/Estender)"
```

---

### Task 2: Helpers + resolução de metamagia (cap + magnitude)

**Files:**
- Modify: `server.py` (helpers perto de `_teto_combinacao` ~3964; bloco de metamagia em `handle_magia` ~7900-7921)
- Test: `tools/test_mago_espec.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`, antes do print final:

```python
    # [2] Helpers de nível
    print("\n[2] Helpers de metamagia")
    r = setup()
    check("teto base = 1", r._teto_metamagia(mage()) == 1)
    check("teto tecelagem_2 = 2", r._teto_metamagia(mage(esp=["mago_tecelagem_2"])) == 2)
    check("teto tecelagem_3 = 3", r._teto_metamagia(mage(esp=["mago_tecelagem_3"])) == 3)
    check("fortalecer base = 1.25", r._fortalecer_mult(mage()) == 1.25)
    check("fortalecer_2 = 1.5", r._fortalecer_mult(mage(esp=["mago_fortalecer_2"])) == 1.5)
    check("fortalecer_3 = 2.0", r._fortalecer_mult(mage(esp=["mago_fortalecer_3"])) == 2.0)
    check("aprimorar base = 1", r._aprimorar_bonus(mage()) == 1)
    check("aprimorar_3 = 3", r._aprimorar_bonus(mage(esp=["mago_aprimorar_3"])) == 3)
    check("estender base = 1", r._estender_bonus(mage()) == 1)
    check("estender_3 = 3", r._estender_bonus(mage(esp=["mago_estender_3"])) == 3)

    # [3] Resolução de metamagia (cap + magnitude + custo)
    print("\n[3] _resolver_metamagia")
    r = setup()
    mg = magia_completa()
    # base: as 3 armadas, teto 1 → só Fortalecer aplica (dmg 1.25), excedeu=True
    p = mage(); p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto1: dmg=1.25", dmg == 1.25)
    check("teto1: dur=0 (não aplicou Estender)", dur == 0)
    check("teto1: dc=0 (não aplicou Aprimorar)", dc == 0)
    check("teto1: custo só do Fortalecer 6/6", (mf, ms) == (6, 6))
    check("teto1: excedeu=True", exc is True)

    # tecelagem_2: Fortalecer + Estender
    p = mage(esp=["mago_tecelagem_2"]); p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto2: dmg=1.25 e dur=1", dmg == 1.25 and dur == 1)
    check("teto2: dc=0 (Aprimorar cortado)", dc == 0)
    check("teto2: custo 6+3 / 6+3", (mf, ms) == (9, 9))
    check("teto2: excedeu=True", exc is True)

    # tecelagem_3: as três
    p = mage(esp=["mago_tecelagem_3"]); p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("teto3: as três aplicam", dmg == 1.25 and dur == 1 and dc == 1)
    check("teto3: custo 6+3+3 / 6+3", (mf, ms) == (12, 9))
    check("teto3: excedeu=False", exc is False)

    # magnitude com upgrades (teto 3)
    p = mage(esp=["mago_tecelagem_3","mago_fortalecer_3","mago_aprimorar_3","mago_estender_3"])
    p["fortalecer_ativo"]=True; p["estender_ativo"]=True; p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, mg)
    check("magnitude: dmg=2.0", dmg == 2.0)
    check("magnitude: dur=3", dur == 3)
    check("magnitude: dc=3", dc == 3)

    # aplicabilidade: magia sem save não cobra Aprimorar
    p = mage(esp=["mago_tecelagem_3"]); p["aprimorar_ativo"]=True
    dmg, dur, dc, mf, ms, partes, exc = r._resolver_metamagia(p, {"id":"x","dano_por_nivel":"1d6"})
    check("sem save: Aprimorar não aplica (dc=0, custo 0)", dc == 0 and (mf, ms) == (0, 0))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_mago_espec.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute '_teto_metamagia'`.

- [ ] **Step 3: Adicionar os helpers**

Em `server.py`, logo após `_teto_combinacao` (após seu `return 1`, ~3968), inserir:

```python
    def _teto_metamagia(self, p):
        """Quantas metamagias podem empilhar no mesmo lançamento (base 1)."""
        if tem_espec(p, "mago_tecelagem_3"): return 3
        if tem_espec(p, "mago_tecelagem_2"): return 2
        return 1

    def _fortalecer_mult(self, p):
        """Multiplicador de dano do Fortalecer Magia (base ×1,25)."""
        if tem_espec(p, "mago_fortalecer_3"): return 2.0
        if tem_espec(p, "mago_fortalecer_2"): return 1.5
        return 1.25

    def _aprimorar_bonus(self, p):
        """Bônus na CD do save do Aprimorar Magia (base +1)."""
        if tem_espec(p, "mago_aprimorar_3"): return 3
        if tem_espec(p, "mago_aprimorar_2"): return 2
        return 1

    def _estender_bonus(self, p):
        """Rodadas extras de duração do Estender Magia (base +1)."""
        if tem_espec(p, "mago_estender_3"): return 3
        if tem_espec(p, "mago_estender_2"): return 2
        return 1

    def _resolver_metamagia(self, p, magia):
        """Resolve as metamagias armadas aplicáveis a `magia`, respeitando o teto de
        empilhamento (ordem de prioridade: Fortalecer > Estender > Aprimorar).
        Retorna (dmg_mult, dur_bonus, dc_bonus, mm_fome, mm_sede, partes, excedeu)."""
        dmg_mult, dur_bonus, dc_bonus = 1, 0, 0
        tem_dano    = self._magia_tem_dano(magia)
        tem_duracao = "duracao" in magia
        tem_save    = "save" in magia
        candidatas = []   # (kind, custo_fome, custo_sede) — armadas E aplicáveis
        if p.get("fortalecer_ativo") and tem_dano:    candidatas.append(("fortalecer", 6, 6))
        if p.get("estender_ativo") and tem_duracao:   candidatas.append(("estender", 3, 3))
        if p.get("aprimorar_ativo") and tem_save:     candidatas.append(("aprimorar", 3, 0))
        teto = self._teto_metamagia(p)
        aplicadas = candidatas[:teto]
        mm_fome = mm_sede = 0
        partes = []
        for kind, cf, cs in aplicadas:
            if kind == "fortalecer":
                dmg_mult = self._fortalecer_mult(p); mm_fome += cf; mm_sede += cs
                partes.append(f"Fortalecer (dano ×{dmg_mult:g})")
            elif kind == "estender":
                dur_bonus = self._estender_bonus(p); mm_fome += cf; mm_sede += cs
                partes.append(f"Estender (+{dur_bonus} turno{'s' if dur_bonus != 1 else ''})")
            elif kind == "aprimorar":
                dc_bonus = self._aprimorar_bonus(p); mm_fome += cf; mm_sede += cs
                partes.append(f"Aprimorar (+{dc_bonus} CD)")
        return dmg_mult, dur_bonus, dc_bonus, mm_fome, mm_sede, partes, (len(candidatas) > teto)
```

- [ ] **Step 4: Trocar o bloco inline em `handle_magia`**

Em `server.py`, substituir o bloco (~7900-7921):

```python
        dmg_mult, dur_bonus, dc_bonus = 1, 0, 0
        if is_mage:
            tem_dano    = self._magia_tem_dano(magia)
            tem_duracao = "duracao" in magia
            tem_save    = "save" in magia
            mm_fome = mm_sede = 0
            partes = []
            if p.get("fortalecer_ativo") and tem_dano:
                dmg_mult = 1.5; mm_fome += 6; mm_sede += 6; partes.append("Fortalecer (dano ×1,5)")
            if p.get("estender_ativo") and tem_duracao:
                dur_bonus = 1; mm_fome += 3; mm_sede += 3; partes.append("Estender (+1 turno)")
            if p.get("aprimorar_ativo") and tem_save:
                dc_bonus = 1; mm_fome += 3; partes.append("Aprimorar (+1 CD)")
            if (mm_fome or mm_sede):
                if p["fome"] < mm_fome or p["sede"] < mm_sede:
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Recursos insuficientes p/ metamagia 🍖-{mm_fome} 💧-{mm_sede}."}); return
                p["fome"] = max(0, p["fome"] - mm_fome)
                p["sede"] = max(0, p["sede"] - mm_sede)
            if partes:
                custo_txt = (f" | 🍖-{mm_fome}" + (f" 💧-{mm_sede}" if mm_sede else "")) if (mm_fome or mm_sede) else ""
                await self.gm_say(f"🔮 **{p['name']}** — metamagia: {', '.join(partes)}{custo_txt}.")
```

por:

```python
        dmg_mult, dur_bonus, dc_bonus = 1, 0, 0
        if is_mage:
            dmg_mult, dur_bonus, dc_bonus, mm_fome, mm_sede, partes, excedeu = self._resolver_metamagia(p, magia)
            if excedeu:
                await self.gm_say(
                    f"🧵 **{p['name']}** só pode empilhar {self._teto_metamagia(p)} metamagia(s) por "
                    f"lançamento — as demais foram ignoradas.")
            if (mm_fome or mm_sede):
                if p["fome"] < mm_fome or p["sede"] < mm_sede:
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Recursos insuficientes p/ metamagia 🍖-{mm_fome} 💧-{mm_sede}."}); return
                p["fome"] = max(0, p["fome"] - mm_fome)
                p["sede"] = max(0, p["sede"] - mm_sede)
            if partes:
                custo_txt = (f" | 🍖-{mm_fome}" + (f" 💧-{mm_sede}" if mm_sede else "")) if (mm_fome or mm_sede) else ""
                await self.gm_say(f"🔮 **{p['name']}** — metamagia: {', '.join(partes)}{custo_txt}.")
```

> Semântica preservada: cobra só as metamagias aplicáveis, custo pago agora, mesma mensagem. Muda apenas: baseline (×1,25, teto 1), magnitudes via helpers, e o aviso de excedente.

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_mago_espec.py`
Expected: PASS nas seções [1]-[3] (FAIL=0).

- [ ] **Step 6: Regressão + compile**

Run: `python -c "import py_compile; py_compile.compile('server.py', doraise=True); print('OK')"` (Expected: OK)
Run: `python tools/test_guilda.py` (Expected: verde) e `python tools/test_devorador.py` (Expected: 165/0 — exercita magias/pergaminhos, garante que a metamagia de pergaminho não regrediu).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_mago_espec.py
git commit -m "feat(guilda): Metamagia com cap de empilhamento e magnitudes por especializacao"
```

---

### Task 3: Cliente — getters + descrições dos botões de metamagia

**Files:**
- Modify: `src/gameState.js` (getters junto dos do bardo; export)
- Modify: `game.js` (`_mageSkillBtn` ~8429-8451)

- [ ] **Step 1: Adicionar getters no `gameState.js`**

Em `src/gameState.js`, logo após `bardoLendasSupremas` (junto dos getters de especialização), inserir:

```javascript
  // ── Mago (Fase 1f) — Metamagia ─────────────────────────────────────────────
  function magoTecelagemCap() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_tecelagem_3')) return 3;
    if (e.includes('mago_tecelagem_2')) return 2;
    return 1;
  }
  function magoFortalecerMult() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_fortalecer_3')) return 2;
    if (e.includes('mago_fortalecer_2')) return 1.5;
    return 1.25;
  }
  function magoAprimorarBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_aprimorar_3')) return 3;
    if (e.includes('mago_aprimorar_2')) return 2;
    return 1;
  }
  function magoEstenderBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_estender_3')) return 3;
    if (e.includes('mago_estender_2')) return 2;
    return 1;
  }
```

- [ ] **Step 2: Exportar os getters**

Em `src/gameState.js`, no `return { ... }` (junto de `bardoLendasSupremas`), adicionar:

```javascript
    magoTecelagemCap,
    magoFortalecerMult,
    magoAprimorarBonus,
    magoEstenderBonus,
```

- [ ] **Step 3: Refletir magnitude + teto nas descrições dos botões**

Em `game.js`, dentro de `_mageSkillBtn(me, sk)`, logo após a linha `const desc = sk.description || sk.desc || '';` (~8432), inserir um override por id (mesmo padrão do Guerreiro):

```javascript
  let _mdesc = desc;
  if (me.class_id === 'mage') {
    const cap = GS.magoTecelagemCap ? GS.magoTecelagemCap() : 1;
    const capTxt = ` (empilha até ${cap})`;
    if (sk.id === 'fortalecer_magia') {
      const mult = GS.magoFortalecerMult ? GS.magoFortalecerMult() : 1.25;
      _mdesc = `Ação livre. Multiplica o dano da magia por ${String(mult).replace('.', ',')}.${capTxt}`;
    } else if (sk.id === 'aprimorar_magia') {
      const b = GS.magoAprimorarBonus ? GS.magoAprimorarBonus() : 1;
      _mdesc = `Ação livre. +${b} na CD do teste de resistência da magia.${capTxt}`;
    } else if (sk.id === 'estender_magia') {
      const b = GS.magoEstenderBonus ? GS.magoEstenderBonus() : 1;
      _mdesc = `Ação livre. +${b} rodada${b !== 1 ? 's' : ''} na duração da magia.${capTxt}`;
    }
  }
```

E na montagem do `innerHTML` (~8449), trocar `${desc}` por `${_mdesc}` na linha:

```javascript
      <div class="skill-desc">${desc}</div>
```
→
```javascript
      <div class="skill-desc">${_mdesc}</div>
```

- [ ] **Step 4: Sanidade de sintaxe**

Run: `node --check src/gameState.js` (Expected: sem erro)
Run: `node --check game.js` (Expected: sem erro)

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): cliente reflete magnitude e teto da Metamagia do Mago"
```

---

### Task 4: Verificação E2E (smoke) + docs

**Files:**
- Modify: `CLAUDE.md`
- Test: manual via preview + suíte

- [ ] **Step 1: Suíte verde**

Run: `python tools/test_mago_espec.py`
Expected: `PASS=N FAIL=0`.

- [ ] **Step 2: Smoke E2E (compra na Guilda)**

Bump temporário do ouro inicial do mago para o smoke: em `server.py`, `CLASSES["mage"]["start_gold"]` → 2000 (SÓ para o smoke). Subir com `preview_start` (config "game"), criar sala, escolher Pedro, iniciar, abrir a Guilda e comprar `mago_tecelagem_2` + `mago_fortalecer_2`; confirmar débito de ouro e persistência em `guild_owned.especializacoes` (via `preview_console_logs`/`preview_network`). Se o handshake WebSocket não subir no ambiente de preview, registrar isso honestamente e confiar na cobertura server-side (não superestimar).

- [ ] **Step 3: Reverter o bump e limpar saves**

Reverter `start_gold` do mago para 20. Remover saves gerados:
```bash
rm -rf saves/
```
Confirmar que `saves/` continua gitignored (não aparece em `git status`).

- [ ] **Step 4: Documentar na CLAUDE.md**

Adicionar, após o parágrafo do Bardo (Fase 1e), um novo parágrafo:

```markdown
> **Especializações do Mago (Fase 1f):** gateiam a **Metamagia** de Pedro
> (Aprimorar/Estender/Fortalecer). Baseline enfraquecido: hoje as 3 metamagias
> empilhavam ilimitado → **1 por lançamento**; **Fortalecer** ×1,5 → **×1,25**.
> **Compras** (`categoria:"especializacao"`, `classe:"mage"`; III exige II):
> `mago_tecelagem_2/3` (empilhar 2/3 — 150/300), `mago_fortalecer_2/3` (×1,5/×2 —
> 200/250), `mago_aprimorar_2/3` (+2/+3 CD — 150/200), `mago_estender_2/3` (+2/+3
> rodadas — 150/200). O núcleo é `_resolver_metamagia(p, magia)` (helper puro que
> substituiu o bloco inline de `handle_magia`): reúne as metamagias armadas E
> aplicáveis (dano/duração/save), trunca ao `_teto_metamagia(p)` na ordem
> Fortalecer→Estender→Aprimorar, e aplica as magnitudes via `_fortalecer_mult`/
> `_aprimorar_bonus`/`_estender_bonus`. A metamagia gravada em **pergaminho**
> (`gerar_pergaminho`) fica inalterada (+1/×1,5/+1). Cliente: `GS.magoTecelagemCap/
> magoFortalecerMult/magoAprimorarBonus/magoEstenderBonus` — as descrições dos
> botões refletem magnitude + teto. Teste: `tools/test_mago_espec.py`.
```

- [ ] **Step 5: Commit final**

```bash
git add CLAUDE.md server.py
git commit -m "docs(guilda): documentar especializacoes do Mago (Fase 1f)"
```

---

## Auto-revisão (checklist do autor do plano)

- **Cobertura do spec:** Catálogo 8 nós → T1; baseline nerf (×1,25, teto 1) + magnitudes + cap → T2 (`_resolver_metamagia` + `handle_magia`); cliente → T3; testes → T1/T2; docs + E2E → T4; fronteira pergaminho → T2 (regressão devorador) + T4 (doc). ✔
- **Sem placeholders:** todo passo de código traz o código real. ✔
- **Consistência de nomes:** helpers `_teto_metamagia`/`_fortalecer_mult`/`_aprimorar_bonus`/`_estender_bonus`/`_resolver_metamagia`; ids `mago_tecelagem_2/3`, `mago_fortalecer_2/3`, `mago_aprimorar_2/3`, `mago_estender_2/3`; getters `magoTecelagemCap/magoFortalecerMult/magoAprimorarBonus/magoEstenderBonus` — idênticos em todas as tasks. ✔
- **Assinatura de retorno:** `_resolver_metamagia` retorna a 7-tupla `(dmg_mult, dur_bonus, dc_bonus, mm_fome, mm_sede, partes, excedeu)` — usada igual no teste [3] e no `handle_magia`. ✔
