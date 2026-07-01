# Guilda — Fase 1b (Especializações do Clérigo) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enfraquecer os 4 milagres do Clérigo (Cura, Cura em Massa, Purificação, Ressurreição) e vender os níveis II/III na Guilda, gateando dados/raio/tipos/HP pela posse de especializações.

**Architecture:** Servidor autoritativo, estilo imperativo da Fase 1a: 8 entradas `categoria:"especializacao"` no `GUILD_CATALOG` (só exibição/compra — `handle_guild_buy` já valida) + helpers testáveis (`_cura_teto`, `_massa_nivel`, `_purif_tipos`, `_ressur_nivel`) lidos por `tem_espec` dentro dos 4 handlers existentes. Cliente: painéis do Lewis respeitam os tetos/tipos possuídos.

**Tech Stack:** Python 3 + `websockets` (servidor); Vanilla JS (cliente). Testes no harness caseiro do projeto (`tools/test_*.py`), **não** pytest.

**Spec:** `docs/superpowers/specs/2026-07-01-guilda-fase1b-clerigo-design.md`

---

## Contexto de código (anchors — localizar por conteúdo)

- `GUILD_CATALOG` + `guild_item`/`guild_items_for_class`/`tem_espec` já existem. `tem_espec(player, espec_id)` retorna posse.
- Helpers do Guerreiro (`_golpe_raw`/`_teto_combinacao`/`_furia_extras`/`_mira_dano_bonus`) são métodos de `GameRoom` (~server.py:3736) — pôr os helpers do Clérigo perto.
- `handle_cura` (~6303): `num_dados = max(1, min(3, int((data or {}).get("num_dados", 1))))`.
- `handle_cura_area` (~6354): `num_dados  = max(1, min(3, int((data or {}).get("num_dados", 1))))` (ATENÇÃO: **dois espaços** após `num_dados`), e `raio = 5`.
- `handle_purificacao` (~6424): `if tipo not in self.PURIFICACAO_CUSTOS:` — validação de tipo; `PURIFICACAO_CUSTOS` tem `veneno/doenca/maldicao/petrificacao`.
- `handle_ressurreicao` (~6502): `custo_fome, custo_sede = 10, 10`; `alvo["hp"] = 1`.
- Cliente (`game.js`): `abrirPainelCura` (~8126) e `abrirPainelCuraArea` (~8190) têm seletor `${[1,2,3].map(n => ...)}` de dados; a Massa mostra "Raio 5" (~8208, 8217). `iniciarModoPurificacao` (~8240) filtra alvos por `PURIFICACAO_TIPOS_LEWIS`. `_clericSkillBtn` (~8289).

**Setup de teste** (`tools/test_clerigo_espec.py`):
```python
"""Especializações do Clérigo (Fase 1b). Roda da raiz: python tools/test_clerigo_espec.py"""
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
    r._no_raio = lambda *a, **k: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = phase; r._errs = errs
    return r

def cleric(**owned):
    p = make_player("c", "Lewis", "cleric", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    return p
```

---

## Task 1: Catálogo — 8 especializações do Clérigo

**Files:** Modify `server.py`; Create `tools/test_clerigo_espec.py`.

- [ ] **Step 1: Criar `tools/test_clerigo_espec.py`** com o cabeçalho/`setup`/`cleric` acima e este `main()`:
```python
async def main():
    # [1] Catálogo
    print("\n[1] Catálogo do Clérigo")
    ids = [i["id"] for i in S.guild_items_for_class("cleric")]
    for eid in ["clerigo_cura_2","clerigo_cura_3","clerigo_massa_2","clerigo_massa_3",
                "clerigo_purif_2","clerigo_purif_3","clerigo_ressur_2","clerigo_ressur_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cura_3 requer cura_2", S.guild_item("clerigo_cura_3")["requer"] == "clerigo_cura_2")
    check("massa_2 sem requer", S.guild_item("clerigo_massa_2")["requer"] is None)
    check("ressur_3 requer ressur_2", S.guild_item("clerigo_ressur_3")["requer"] == "clerigo_ressur_2")
    check("preço II = 150", S.guild_item("clerigo_cura_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("clerigo_purif_3")["preco"] == 200)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```
(Manter o summary/`sys.exit` no fim; tasks seguintes inserem blocos antes.)

- [ ] **Step 2: Rodar — MUST fail.** `python tools/test_clerigo_espec.py`

- [ ] **Step 3: Adicionar 8 entradas ao `GUILD_CATALOG`** (após as do Guerreiro):
```python
    "clerigo_cura_2": {
        "id": "clerigo_cura_2", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_cura", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Cura II", "icon": "🙌",
        "desc": "Cura pode usar até 2d8 + INT.",
    },
    "clerigo_cura_3": {
        "id": "clerigo_cura_3", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_cura", "nivel": 3, "requer": "clerigo_cura_2", "exclusiva": False,
        "preco": 200, "nome": "Cura III", "icon": "🙌",
        "desc": "Cura pode usar até 3d8 + INT.",
    },
    "clerigo_massa_2": {
        "id": "clerigo_massa_2", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_massa", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Cura em Massa II", "icon": "🌟",
        "desc": "Cura em Massa: até 2d8 + INT, raio 4.",
    },
    "clerigo_massa_3": {
        "id": "clerigo_massa_3", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_massa", "nivel": 3, "requer": "clerigo_massa_2", "exclusiva": False,
        "preco": 200, "nome": "Cura em Massa III", "icon": "🌟",
        "desc": "Cura em Massa: até 3d8 + INT, raio 6.",
    },
    "clerigo_purif_2": {
        "id": "clerigo_purif_2", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_purif", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Purificação II", "icon": "✨",
        "desc": "Purificação também remove doenças.",
    },
    "clerigo_purif_3": {
        "id": "clerigo_purif_3", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_purif", "nivel": 3, "requer": "clerigo_purif_2", "exclusiva": False,
        "preco": 200, "nome": "Purificação III", "icon": "✨",
        "desc": "Purificação também remove maldições e petrificação.",
    },
    "clerigo_ressur_2": {
        "id": "clerigo_ressur_2", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_ressur", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Ressurreição II", "icon": "💫",
        "desc": "Ressurreição traz o aliado com metade dos PV (🍖15 💧15).",
    },
    "clerigo_ressur_3": {
        "id": "clerigo_ressur_3", "categoria": "especializacao", "classe": "cleric",
        "linha": "clerigo_ressur", "nivel": 3, "requer": "clerigo_ressur_2", "exclusiva": False,
        "preco": 200, "nome": "Ressurreição III", "icon": "💫",
        "desc": "Ressurreição traz o aliado com PV cheio (🍖20 💧20).",
    },
```

- [ ] **Step 4: Rodar — MUST pass.**

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_clerigo_espec.py
git commit -m "feat(guilda): catalogo de especializacoes do Clerigo"
```

---

## Task 2: Cura — teto de dados (helper `_cura_teto`)

**Files:** Modify `server.py`; `tools/test_clerigo_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()` antes do summary:
```python
    # [2] Cura teto
    print("\n[2] Cura teto")
    r = setup()
    check("teto base = 1", r._cura_teto(cleric()) == 1)
    check("teto cura_2 = 2", r._cura_teto(cleric(esp=["clerigo_cura_2"])) == 2)
    check("teto cura_3 = 3", r._cura_teto(cleric(esp=["clerigo_cura_2","clerigo_cura_3"])) == 3)
    # integração: pedir 3 dados sem cura_3 cura no máx 1 (base). Dado fixo=8, INT p/ Lewis (16)=+3.
    _orig = S.random.randint; S.random.randint = lambda a,b: 8
    try:
        r = setup(); c = cleric(); c["pos"]=[0,0]; r.players["c"]=c
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=99; r.players["a"]=alvo
        await r.handle_cura("c", {"target_id":"a","num_dados":3,"alcance_extra":0})
        check("cura base clampa a 1 dado (1..8+3 → +11)", alvo["hp"] == 1 + (8 + 3))
    finally:
        S.random.randint = _orig
```

- [ ] **Step 2: Rodar — MUST fail** (`_cura_teto` inexistente).

- [ ] **Step 3: Helper `_cura_teto`** (método de `GameRoom`, perto de `_golpe_raw`):
```python
    def _cura_teto(self, p):
        """Máx. de d8 da Cura pela posse (1 base / 2 / 3)."""
        if tem_espec(p, "clerigo_cura_3"): return 3
        if tem_espec(p, "clerigo_cura_2"): return 2
        return 1
```

- [ ] **Step 4: Gatear `handle_cura`** — trocar
`num_dados = max(1, min(3, int((data or {}).get("num_dados", 1))))`
por
`num_dados = max(1, min(self._cura_teto(p), int((data or {}).get("num_dados", 1))))`.

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_clerigo_espec.py
git commit -m "feat(guilda): Cura gateia numero de dados por nivel (Clerigo)"
```

---

## Task 3: Cura em Massa — nível (dados + raio) via `_massa_nivel`

**Files:** Modify `server.py`; `tools/test_clerigo_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [3] Cura em Massa: nível → dados + raio
    print("\n[3] Cura em Massa")
    r = setup()
    check("massa base = 1", r._massa_nivel(cleric()) == 1)
    check("massa_2 = 2", r._massa_nivel(cleric(esp=["clerigo_massa_2"])) == 2)
    check("massa_3 = 3", r._massa_nivel(cleric(esp=["clerigo_massa_2","clerigo_massa_3"])) == 3)
    # integração: raio usado = 2*nível. Capturamos via r._no_raio.
    _orig = S.random.randint; S.random.randint = lambda a,b: 8
    raios = []
    try:
        r = setup()
        def cap_raio(p, alvo, raio, *a, **k): raios.append(raio); return True
        r._no_raio = cap_raio
        c = cleric(esp=["clerigo_massa_2"]); c["pos"]=[0,0]; r.players["c"]=c
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=99; r.players["a"]=alvo
        await r.handle_cura_area("c", {"num_dados":3})
        check("massa_2 usa raio 4", 4 in raios)
        check("massa_2 clampa dados a 2 (2*8+3=19)", alvo["hp"] == 1 + (2*8 + 3))
    finally:
        S.random.randint = _orig
```

- [ ] **Step 2: Rodar — MUST fail.**

- [ ] **Step 3: Helper `_massa_nivel`** (perto de `_cura_teto`):
```python
    def _massa_nivel(self, p):
        """Nível da Cura em Massa (1/2/3) — define teto de dados E raio (2×nível)."""
        if tem_espec(p, "clerigo_massa_3"): return 3
        if tem_espec(p, "clerigo_massa_2"): return 2
        return 1
```

- [ ] **Step 4: Gatear `handle_cura_area`** — trocar
`num_dados  = max(1, min(3, int((data or {}).get("num_dados", 1))))` e `raio = 5`
por:
```python
        nivel = self._massa_nivel(p)
        num_dados = max(1, min(nivel, int((data or {}).get("num_dados", 1))))
```
e, na linha do raio:
```python
        raio = 2 * nivel   # 2 / 4 / 6
```

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_clerigo_espec.py
git commit -m "feat(guilda): Cura em Massa gateia dados e raio por nivel (Clerigo)"
```

---

## Task 4: Purificação — tipos destravados via `_purif_tipos`

**Files:** Modify `server.py`; `tools/test_clerigo_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [4] Purificação: tipos por nível
    print("\n[4] Purificação")
    r = setup()
    check("base só veneno", r._purif_tipos(cleric()) == {"veneno"})
    check("II +doença", r._purif_tipos(cleric(esp=["clerigo_purif_2"])) == {"veneno","doenca"})
    check("III +maldição/petrif", r._purif_tipos(cleric(esp=["clerigo_purif_2","clerigo_purif_3"]))
          == {"veneno","doenca","maldicao","petrificacao"})
    # integração: purificar 'doenca' sem purif_2 é recusado
    r = setup(); c = cleric(); c["pos"]=[0,0]; r.players["c"]=c
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; r.players["a"]=alvo
    await r.handle_purificacao("c", {"target_id":"a","tipo":"doenca"})
    check("recusa doença sem purif_2", any("aprendeu" in e.lower() or "purific" in e.lower() for e in r._errs))
```

- [ ] **Step 2: Rodar — MUST fail** (`_purif_tipos` inexistente).

- [ ] **Step 3: Helper `_purif_tipos`** (perto dos outros):
```python
    def _purif_tipos(self, p):
        """Tipos de purificação destravados pela posse."""
        tipos = {"veneno"}
        if tem_espec(p, "clerigo_purif_2"): tipos.add("doenca")
        if tem_espec(p, "clerigo_purif_3"): tipos |= {"maldicao", "petrificacao"}
        return tipos
```

- [ ] **Step 4: Gatear `handle_purificacao`** — logo após o bloco `if tipo not in self.PURIFICACAO_CUSTOS: ... return`, inserir:
```python
        if tipo not in self._purif_tipos(p):
            await self.send_to(pid, {"type": "error",
                "msg": "Você ainda não aprendeu a purificar este mal — evolua a Purificação na Guilda."}); return
```

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_clerigo_espec.py
git commit -m "feat(guilda): Purificacao gateia tipos por nivel (Clerigo)"
```

---

## Task 5: Ressurreição — HP e custo por nível via `_ressur_nivel`

**Files:** Modify `server.py`; `tools/test_clerigo_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [5] Ressurreição: HP e custo por nível
    print("\n[5] Ressurreição")
    r = setup()
    check("ressur base = 1", r._ressur_nivel(cleric()) == 1)
    check("ressur_2 = 2", r._ressur_nivel(cleric(esp=["clerigo_ressur_2"])) == 2)
    check("ressur_3 = 3", r._ressur_nivel(cleric(esp=["clerigo_ressur_2","clerigo_ressur_3"])) == 3)
    # integração nível II: metade dos PV + custo 15/15
    r = setup(); c = cleric(esp=["clerigo_ressur_2"]); c["pos"]=[0,0]; c["fome"]=50; c["sede"]=50; r.players["c"]=c
    morto = make_player("a","Ana","warrior",1); morto["pos"]=[0,1]; morto["alive"]=False; morto["hp"]=0; morto["max_hp"]=20; r.players["a"]=morto
    await r.handle_ressurreicao("c", {"target_id":"a"})
    check("ressur II → metade PV (10)", morto["hp"] == 10)
    check("ressur II → custo 15/15", c["fome"] == 35 and c["sede"] == 35)
```

- [ ] **Step 2: Rodar — MUST fail** (`_ressur_nivel` inexistente / HP=1 fixo).

- [ ] **Step 3: Helper `_ressur_nivel`** (perto dos outros):
```python
    def _ressur_nivel(self, p):
        if tem_espec(p, "clerigo_ressur_3"): return 3
        if tem_espec(p, "clerigo_ressur_2"): return 2
        return 1
```

- [ ] **Step 4: Gatear `handle_ressurreicao`** — trocar `custo_fome, custo_sede = 10, 10` por:
```python
        nivel = self._ressur_nivel(p)
        custo_fome = custo_sede = {1: 10, 2: 15, 3: 20}[nivel]
```
e trocar `alvo["hp"] = 1` por:
```python
        alvo["hp"] = {1: 1, 2: max(1, alvo["max_hp"] // 2), 3: alvo["max_hp"]}[nivel]
```
Ajustar a `gm_say` para citar o HP concedido em vez de fixo "1 HP" — ex.: usar `alvo['hp']`:
`f"... traz **{alvo['name']}** de volta à vida com **{alvo['hp']} HP**! (🍖-{custo_fome} 💧-{custo_sede})"`.

- [ ] **Step 5: Rodar — MUST pass** + regressão:
`python tools/test_clerigo_espec.py` → 0 falharam
`python tools/test_devorador.py` → anote (não deve regredir).

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_clerigo_espec.py
git commit -m "feat(guilda): Ressurreicao com HP e custo por nivel (Clerigo)"
```

---

## Task 6: Cliente — painéis do Lewis respeitam os níveis

**Files:** Modify `src/gameState.js`, `game.js`.

- [ ] **Step 1: Getters no `gameState.js`** (perto de `warriorComboCap`):
```javascript
  // Níveis das especializações do Clérigo (lidos da posse; caem p/ game_state na masmorra).
  function clericCuraTeto() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('clerigo_cura_3')) return 3;
    if (e.includes('clerigo_cura_2')) return 2;
    return 1;
  }
  function clericMassaNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('clerigo_massa_3')) return 3;
    if (e.includes('clerigo_massa_2')) return 2;
    return 1;
  }
  function clericPurifTipos() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    const t = ['veneno'];
    if (e.includes('clerigo_purif_2')) t.push('doenca');
    if (e.includes('clerigo_purif_3')) t.push('maldicao', 'petrificacao');
    return t;
  }
  function clericRessurNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('clerigo_ressur_3')) return 3;
    if (e.includes('clerigo_ressur_2')) return 2;
    return 1;
  }
```
Exportar os 4 no `return { ... }` (junto de `warriorComboCap`).

- [ ] **Step 2: `abrirPainelCura` — limitar os dados ao teto.** No seletor
`${[1,2,3].map(n => ...)}` (~8147), trocar `[1,2,3]` por `[1,2,3].filter(n => n <= GS.clericCuraTeto())`. E clampar o inicial: logo após `let numDados = 1, alcanceExtra = 0;`, adicionar nada (1 sempre válido); mas garantir que `numDados` nunca exceda o teto — como começa em 1, ok.

- [ ] **Step 3: `abrirPainelCuraArea` — dados ao teto + raio por nível.** Ler o nível uma vez no início da função: `const _mNivel = GS.clericMassaNivel(); const _mRaio = 2 * _mNivel;`. Trocar o seletor `${[1,2,3].map(...)}` (~8210) por `${[1,2,3].filter(n => n <= _mNivel).map(...)}`. Substituir os literais "Raio 5"/"5 quadrados" (~8208, 8217) por `Raio ${_mRaio}` / `${_mRaio} quadrados`.

- [ ] **Step 4: Purificação — só tipos destravados.** Em `iniciarModoPurificacao` (~8240), onde filtra alvos por `PURIFICACAO_TIPOS_LEWIS.some(t => t.cond(a))`, adicionar o filtro de posse: só considerar tipos em `GS.clericPurifTipos()`. Ex.: `const _permitidos = GS.clericPurifTipos(); ... .filter(a => PURIFICACAO_TIPOS_LEWIS.some(t => _permitidos.includes(t.id) && t.cond(a)))`. E no painel de escolha de tipo (onde lista os tipos), filtrar por `_permitidos` também. **Ler a função inteira antes** para aplicar nos dois pontos (seleção de alvo + escolha do tipo).

- [ ] **Step 5: Ressurreição — refletir o nível.** No `_clericSkillBtn`/painel de ressurreição, mostrar o efeito do nível atual (`GS.clericRessurNivel()`): 1 HP (🍖10💧10) / metade (🍖15💧15) / cheio (🍖20💧20). Ajuste de texto; o envio (`type:'ressurreicao'`) permanece — o servidor decide HP/custo.

- [ ] **Step 6: Syntax check.** `node --check src/gameState.js && node --check game.js` → exit 0.

- [ ] **Step 7: Commit**
```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): paineis do Clerigo respeitam niveis das especializacoes"
```

---

## Task 7: Verificação E2E + docs

**Files:** Modify `CLAUDE.md`.

- [ ] **Step 1: Suíte**
`python tools/test_clerigo_espec.py` → 0 falharam
`python tools/test_guerreiro_espec.py` → 0 falharam (Fase 1a intacta)
`python tools/test_guilda.py` → 0 falharam (Fase 0)
`python tools/test_devorador.py` → combate ok

- [ ] **Step 2: Smoke test in-app** (padrão das fases anteriores; `.claude/launch.json` server `game`):
  - Subir preview; criar sala; escolher **Clérigo**; dar ouro (truque temporário-e-revertido de `start_gold` — bump o do `cleric`, reverter ao fim + `rm -rf saves/`).
  - Na Guilda: comprar `clerigo_cura_2` e `clerigo_purif_2`.
  - Na masmorra: painel de Cura mostra só 1–2 dados (não 3); painel da Massa mostra raio 2 (sem massa comprada); Purificação só oferece veneno/doença. Zero erros de console.

- [ ] **Step 3: `CLAUDE.md`** — na seção da Guilda, acrescentar parágrafo curto: "Especializações do Clérigo (Fase 1b): baseline enfraquecido (Cura 1d8, Massa 1d8/raio2, Purificação só venenos, Ressurreição 1HP); compras `clerigo_cura_2/3`, `clerigo_massa_2/3`, `clerigo_purif_2/3`, `clerigo_ressur_2/3` (II=150/III=200, III exige II por linha); gating em `handle_cura`/`handle_cura_area`/`handle_purificacao`/`handle_ressurreicao` via `_cura_teto`/`_massa_nivel`/`_purif_tipos`/`_ressur_nivel`; petrificação no III; Ressurreição HP 1/metade/cheio custo 10/15/20; teste `tools/test_clerigo_espec.py`." Registrar o nerf (Cura 3d8→1d8, raio 5→2).

- [ ] **Step 4: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(guilda): documentar especializacoes do Clerigo (Fase 1b)"
```

---

## Self-review (cobertura do spec)

- **§3 catálogo (8 nós)** → Task 1. ✔
- **§4.1 Cura teto** → Task 2. ✔
- **§4.2 Massa (dados + raio 2/4/6)** → Task 3. ✔
- **§4.3 Purificação (venenos/doenças/maldições+petrificação)** → Task 4. ✔
- **§4.4 Ressurreição (HP 1/metade/cheio; custo 10/15/20)** → Task 5. ✔
- **§5 cliente** → Task 6. ✔
- **§6 testes** → `tools/test_clerigo_espec.py` (Tasks 1-5) + smoke (Task 7). ✔
- **§8 riscos (nerf; `max(1, max_hp//2)`)** → nerf documentado (Task 7); `max(1, alvo["max_hp"]//2)` na Task 5; regressão devorador (Task 5). ✔

**Consistência de nomes:** helpers `_cura_teto`/`_massa_nivel`/`_purif_tipos`/`_ressur_nivel` (métodos de `GameRoom`); cliente `clericCuraTeto`/`clericMassaNivel`/`clericPurifTipos`/`clericRessurNivel`. Ids: `clerigo_{cura,massa,purif,ressur}_{2,3}`. Tipos de purificação: `veneno`/`doenca`/`maldicao`/`petrificacao` (como em `PURIFICACAO_CUSTOS`).

**Nota de teste:** os testes de integração stubam `_is_turn`/`_no_raio`/`_tem_linha_de_visao` e mockam `S.random.randint` para dado fixo — isola a lógica de gating sem depender de geometria/rolagem.
