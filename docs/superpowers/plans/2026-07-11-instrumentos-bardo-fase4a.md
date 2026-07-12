# Instrumentos do Bardo — Fase 4a (Origens Élfica/Anã) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Popular o eixo Origem (Élfica/Anã) dos instrumentos — afixo composto da Anã, pools de afixo por origem, nome com origem, roller procedural, token de loot autoral e SKUs de origem na loja (para teste).

**Architecture:** Camada aditiva sobre o framework já plumbado (`criar_instrumento`/`_instrumento_stats`/`_aplicar_afixo` já aplicam `origem_bonus`). Funções de módulo novas (`gerar_instrumento_aleatorio`, `_afixo_aplicavel`, `_afixos_validos_origem`, `_resolver_loot_instrumento`) + hooks nos 2 sites de loot + SKUs na loja. Sem mudança de framework.

**Tech Stack:** Python (`server.py`), Vanilla JS (`src/gameState.js`), testes `tools/test_instrumentos_bardo.py`.

**Spec:** `docs/superpowers/specs/2026-07-11-instrumentos-bardo-fase4a-design.md`

---

## Pontos de integração (confirmados; verificar por leitura)
- `criar_instrumento(base, qualidade, origem, encantamento, refinado_bonus, origem_bonus)` (~277) — já grava `origem`/`origem_bonus` (só se origem in elfica/ana).
- `instrumento_sku(base, qualidade, preco, refinado_bonus=None)` (~293) — id único `instrumento_{base}_{qualidade}`, `price`/`buy_price`.
- `_instrumento_nome(inst)` (~301) — hoje "{nome} {qualidade}".
- `_INSTRUMENTO_GENERO_FEM` (~275), `_QUALIDADE_LABEL` (perto).
- `_aplicar_afixo(st, bonus)` (~8141) — fome/sede/alcance(+raio+cone)/duracao/cd.
- `_instrumento_stats` (~8122) aplica `refinado_bonus` e `origem_bonus`.
- `_concentracao_requiem` (~5216) lê `origem_bonus == "concentracao"` → +2 (Fase 3; nada a mudar).
- Loot: `hidratar_itens_bau(items)` módulo (~2751); `_monster_dies` cadeia `elif loot.get("tipo") == ...` (~15550-15586).
- Cliente: `instrumentoStatsClient(inst)` + seu `afixo()` interno (`src/gameState.js` ~1277).
- Testes: helpers em `tools/test_instrumentos_bardo.py`.

---

## Task 1: Afixo composto `fome_sede` (server + cliente)

**Files:** `server.py`, `src/gameState.js`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_afixo_fome_sede():
    st = {"custo_fome": 3, "custo_sede": 3}
    server.GameRoom._aplicar_afixo(st, "fome_sede")
    assert st["custo_fome"] == 2 and st["custo_sede"] == 2

def test_ana_fome_sede_no_instrumento():
    inst = server.criar_instrumento("harpa", "padrao", origem="ana", origem_bonus="fome_sede")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["custo_fome"] == 2 and st["custo_sede"] == 2   # 3-1 / 3-1
```

- [ ] **Step 2** — Run `python tools/test_instrumentos_bardo.py` → FAIL (fome_sede não tratado).

- [ ] **Step 3 — implementar.** Em `_aplicar_afixo` (server.py ~8141), adicionar o ramo (após `sede`):
```python
        elif bonus == "fome_sede":
            st["custo_fome"] -= 1
            st["custo_sede"] -= 1
```
Cliente — em `instrumentoStatsClient`'s `afixo()` (src/gameState.js), espelhar (e fechar a lacuna do `cone`, que o servidor tem e o cliente não):
```javascript
      if (bonus === 'fome') st.custo_fome -= 1;
      else if (bonus === 'sede') st.custo_sede -= 1;
      else if (bonus === 'fome_sede') { st.custo_fome -= 1; st.custo_sede -= 1; }
      else if (bonus === 'alcance') { if ('alcance' in st) st.alcance += 1; if ('raio' in st) st.raio += 1; if ('cone' in st) st.cone += 1; }
      else if (bonus === 'duracao') { if ('duracao' in st) st.duracao += 1; }
```
(adaptar ao texto real do `afixo()`; preservar o resto.)

- [ ] **Step 4** — Run → PASS. `node --check src/gameState.js` → OK.
- [ ] **Step 5 — Commit:**
```bash
git add server.py src/gameState.js tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): afixo composto fome_sede (Ana) + espelho no cliente"
```

---

## Task 2: Aplicabilidade de afixos por origem

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_afixos_validos_origem():
    # Élfica no Alaúde: nada aplicável (sem save/alcance/duracao) → vazio
    assert server._afixos_validos_origem("alaude", "elfica") == []
    # Violino Anã: inclui concentracao
    assert "concentracao" in server._afixos_validos_origem("violino", "ana")
    # Harpa Élfica: cd e alcance aplicáveis; duracao não (harpa não tem duracao)
    va = server._afixos_validos_origem("harpa", "elfica")
    assert "cd" in va and "alcance" in va and "duracao" not in va
    # Sino Élfica: duracao aplicável; cd/alcance não
    vs = server._afixos_validos_origem("sino", "elfica")
    assert "duracao" in vs and "cd" not in vs and "alcance" not in vs
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.** Funções de módulo (perto de `criar_instrumento`):
```python
_ORIGEM_AFIXOS = {
    "elfica": ["cd", "alcance", "duracao"],
    "ana":    ["fome_sede", "duracao", "concentracao"],
}

def _afixo_aplicavel(base, bonus):
    """True se o afixo faz efeito neste instrumento (evita origem sem bônus)."""
    b = INSTRUMENTOS_BASE[base]
    stp = b["stats"]["padrao"]
    if bonus == "fome_sede":
        return True
    if bonus == "cd":
        return bool(b["efeito"].get("save"))
    if bonus == "alcance":
        return any(k in stp for k in ("alcance", "raio", "cone"))
    if bonus == "duracao":
        return "duracao" in stp
    if bonus == "concentracao":
        return b["efeito"].get("tipo") == "requiem_final"
    return False

def _afixos_validos_origem(base, origem):
    """Pool de afixos da origem ∩ aplicáveis à base."""
    return [a for a in _ORIGEM_AFIXOS.get(origem, []) if _afixo_aplicavel(base, a)]
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): pools de afixo por origem + aplicabilidade por base"
```

---

## Task 3: Nome com origem (concordância de gênero)

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_nome_com_origem():
    assert server.criar_instrumento("harpa", "refinado", origem="elfica",
                                    origem_bonus="cd")["name"] == "Harpa Refinada Élfica"
    assert server.criar_instrumento("tambor", "padrao", origem="ana",
                                    origem_bonus="fome_sede")["name"] == "Tambor de Guerra Padrão Anão"
    # Humana: sem sufixo (compatível com o comportamento atual)
    assert server.criar_instrumento("harpa", "velho")["name"] == "Harpa Velha"
```

- [ ] **Step 2** — Run → FAIL (sem sufixo de origem).

- [ ] **Step 3 — implementar.** Adicionar a tabela de rótulo de origem (perto de `_QUALIDADE_LABEL`):
```python
_ORIGEM_LABEL = {          # (masculino, feminino)
    "elfica": ("Élfico", "Élfica"),
    "ana":    ("Anão", "Anã"),
}
```
E estender `_instrumento_nome`:
```python
def _instrumento_nome(inst):
    b = INSTRUMENTOS_BASE[inst["base"]]
    fem = inst["base"] in _INSTRUMENTO_GENERO_FEM
    ql = _QUALIDADE_LABEL.get(inst["qualidade"], ("Padrão", "Padrão"))[1 if fem else 0]
    nome = f"{b['nome']} {ql}"
    orig = inst.get("origem", "humana")
    if orig in _ORIGEM_LABEL:
        nome += " " + _ORIGEM_LABEL[orig][1 if fem else 0]
    return nome
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): nome do instrumento reflete a origem (concordancia de genero)"
```

---

## Task 4: Roller procedural `gerar_instrumento_aleatorio`

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
import random as _rnd

def test_roller_gera_instrumentos_validos():
    _rnd.seed(1234)
    for _ in range(300):
        inst = server.gerar_instrumento_aleatorio()
        assert inst["tipo_item"] == "instrumento"
        assert inst["base"] in server.INSTRUMENTOS_BASE
        # origem_bonus, se houver, é aplicável à base
        if inst.get("origem_bonus"):
            assert inst["origem_bonus"] in server._afixos_validos_origem(inst["base"], inst["origem"])
        # nunca Alaúde Élfico com bônus nulo (deve ter rebaixado p/ Humana)
        if inst["base"] == "alaude":
            assert inst["origem"] != "elfica"

def test_roller_respeita_bases():
    _rnd.seed(1)
    for _ in range(50):
        inst = server.gerar_instrumento_aleatorio(bases=["harpa"])
        assert inst["base"] == "harpa"
```

- [ ] **Step 2** — Run → FAIL (`gerar_instrumento_aleatorio` ausente).

- [ ] **Step 3 — implementar.** Funções de módulo (perto de `criar_instrumento`):
```python
_ROLLER_BASES = ["harpa", "tambor", "sino", "alaude", "trompa", "lira", "flauta", "violino"]
_ROLLER_QUALIDADES = [("velho", 35), ("rustico", 30), ("padrao", 25), ("refinado", 10)]
_ROLLER_ORIGENS = [("humana", 70), ("elfica", 15), ("ana", 15)]

def _weighted_choice(pairs):
    total = sum(w for _, w in pairs)
    r = random.uniform(0, total)
    acc = 0.0
    for val, w in pairs:
        acc += w
        if r <= acc:
            return val
    return pairs[-1][0]

def gerar_instrumento_aleatorio(bases=None):
    """Instrumento procedural ponderado (base × qualidade × origem), com afixos
    pré-rolados válidos. Élfica sem afixo aplicável (Alaúde) rebaixa p/ Humana."""
    base = random.choice(bases or _ROLLER_BASES)
    qualidade = _weighted_choice(_ROLLER_QUALIDADES)
    origem = _weighted_choice(_ROLLER_ORIGENS)
    origem_bonus = None
    if origem in ("elfica", "ana"):
        validos = _afixos_validos_origem(base, origem)
        if validos:
            origem_bonus = random.choice(validos)
        else:
            origem = "humana"
    refinado_bonus = None
    if qualidade == "refinado":
        afx = INSTRUMENTOS_BASE[base].get("afixos_validos", [])
        if afx:
            refinado_bonus = random.choice(afx)
    return criar_instrumento(base, qualidade, origem, "nenhum", refinado_bonus, origem_bonus)
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): roller procedural ponderado (base/qualidade/origem)"
```

---

## Task 5: Token de loot `instrumento_aleatorio` + placement de referência

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_resolver_loot_instrumento():
    inst = server._resolver_loot_instrumento({"tipo": "instrumento_aleatorio"})
    assert inst is not None and inst["tipo_item"] == "instrumento"
    assert server._resolver_loot_instrumento({"tipo": "item", "id": "x"}) is None
    assert server._resolver_loot_instrumento({"id": "y"}) is None

def test_hidratar_itens_bau_token():
    out = server.hidratar_itens_bau([{"tipo": "instrumento_aleatorio"}])
    assert len(out) == 1 and out[0]["tipo_item"] == "instrumento"
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.**

3a. Helper de módulo (perto de `gerar_instrumento_aleatorio`):
```python
def _resolver_loot_instrumento(entry):
    """Token de loot procedural: {"tipo":"instrumento_aleatorio"} → instância; senão None."""
    if isinstance(entry, dict) and entry.get("tipo") == "instrumento_aleatorio":
        return gerar_instrumento_aleatorio()
    return None
```

3b. `hidratar_itens_bau` (~2751) — reconhecer o token no laço:
```python
    for it in items or []:
        if not isinstance(it, dict):
            continue
        inst = _resolver_loot_instrumento(it)
        if inst:
            out.append(inst); continue
        base = _DUNGEON_ITEM_CATALOG.get(it.get("id"))
        if base:
            out.append(deepcopy(base))
```

3c. `_monster_dies` — na cadeia de `elif loot.get("tipo") == ...` (~15563, junto de `scroll`/`comida`), adicionar:
```python
                elif loot.get("tipo") == "instrumento_aleatorio":
                    loot_items.append(gerar_instrumento_aleatorio())
```

3d. **Placement de referência:** escolher 1 monstro temático (ex.: um chefe ou inimigo
com loot_table rica) e reservar uma faixa pequena para o token. Localizar sua
`loot_table` em `MONSTER_DEFS` e ajustar uma faixa (ex.: transformar a cauda `None` numa
faixa de token):
```python
        # exemplo: era "91-100": None  →  vira token de instrumento raro
        "96-100": {"tipo": "instrumento_aleatorio"},
```
(Escolher o monstro por leitura; manter as faixas somando 1-100. Reportar qual monstro.)

- [ ] **Step 4** — Run → PASS. `python tools/test_roteamento_itens.py` (regressão de loot/rota) → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): token de loot instrumento_aleatorio (baus + drop) + placement de referencia"
```

---

## Task 6: SKUs de origem na loja (teste)

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_sku_origem():
    sku = server.instrumento_sku("harpa", "padrao", preco=320, origem="elfica", origem_bonus="cd")
    assert sku["origem"] == "elfica" and sku["origem_bonus"] == "cd"
    assert sku["id"] == "instrumento_harpa_padrao_elfica"    # id distinto do Humano
    assert "Élfica" in sku["name"]
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_harpa_padrao_elfica" in ids
    assert "instrumento_violino_padrao_ana" in ids
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.**

3a. Estender `instrumento_sku` (~293):
```python
def instrumento_sku(base, qualidade="padrao", preco=100, refinado_bonus=None,
                    origem="humana", origem_bonus=None):
    """Instância de instrumento para a loja/loot (id único + price/buy_price)."""
    inst = criar_instrumento(base, qualidade, origem=origem, encantamento="nenhum",
                             refinado_bonus=refinado_bonus, origem_bonus=origem_bonus)
    suf = f"_{origem}" if origem in ("elfica", "ana") else ""
    inst["id"] = f"instrumento_{base}_{qualidade}{suf}"
    inst["price"] = preco
    inst["buy_price"] = preco
    return inst
```

3b. Adicionar SKUs de origem ao bloco de instrumentos em `SHOP_MERCHANT` (conveniência de
teste; preços mais altos que os Humanos):
```python
    # Origens (Fase 4a) — compráveis para teste; a via "real" é loot procedural.
    instrumento_sku("harpa",  "padrao", 320, origem="elfica", origem_bonus="cd"),
    instrumento_sku("harpa",  "padrao", 320, origem="elfica", origem_bonus="alcance"),
    instrumento_sku("sino",   "padrao", 240, origem="elfica", origem_bonus="duracao"),
    instrumento_sku("tambor", "padrao", 340, origem="ana",    origem_bonus="fome_sede"),
    instrumento_sku("lira",   "padrao", 300, origem="ana",    origem_bonus="duracao"),
    instrumento_sku("violino","padrao", 480, origem="ana",    origem_bonus="concentracao"),
```

- [ ] **Step 4** — Run → PASS. `python tools/test_roteamento_itens.py` → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): SKUs de origem na loja (Elfica/Ana) para teste"
```

---

## Task 7: Docs + regressão final

**Files:** `CLAUDE.md`; Test suíte.

- [ ] **Step 1 — CLAUDE.md.** Após o bloco da Fase 3 dos instrumentos, adicionar um `>`:
```markdown
> **Fase 4a (Origens Élfica/Anã):** popula o eixo Origem (já plumbado desde a Fase 1).
> Afixos por origem — Élfica {`cd`,`alcance`,`duracao`}, Anã {`fome_sede`(−1🍖−1💧),`duracao`,
> `concentracao`(+2 no Réquiem, lido em `_concentracao_requiem`)} — pré-rolados e filtrados
> por `_afixo_aplicavel`/`_afixos_validos_origem` (Élfica sem afixo aplicável, ex.: Alaúde,
> rebaixa p/ Humana). `_aplicar_afixo` ganhou `fome_sede`. `_instrumento_nome` acrescenta o
> adjetivo de origem com concordância de gênero (Élfica/Élfico, Anã/Anão). Roller procedural
> `gerar_instrumento_aleatorio` (ponderado: qualidade 35/30/25/10, origem 70/15/15). Loot:
> token autoral `{"tipo":"instrumento_aleatorio"}` resolvido por `_resolver_loot_instrumento`
> em `hidratar_itens_bau` (baús/recompensas) e na cadeia de loot de `_monster_dies` (drop) —
> designers posicionam o token nas loot tables/recompensas. Loja: SKUs de origem
> (`instrumento_sku` com `origem`/`origem_bonus`; id `instrumento_{base}_{qualidade}_{origem}`)
> adicionados **para teste**. Cliente: `instrumentoStatsClient` espelha `fome_sede`. Fase 4b:
> Encantamento Rúnico (8 efeitos) + Lendário + Rúnico no roller. Testes:
> `tools/test_instrumentos_bardo.py`.
```
Verificar cada afirmação contra o código antes de escrever.

- [ ] **Step 2 — regressão** (registrar PASS/FAIL):
```bash
python tools/test_instrumentos_bardo.py
python tools/test_bardo_espec.py
python tools/test_roteamento_itens.py
python tools/test_tecnicas_espec.py
python -c "import server"
node --check src/gameState.js
```
Se algo falhar, STOP e reportar DONE_WITH_CONCERNS.

- [ ] **Step 3 — Commit:**
```bash
git add CLAUDE.md
git commit -m "docs(instrumentos): documenta Fase 4a (Origens Elfica/Ana) no CLAUDE.md"
```

---

## Self-Review (cobertura do spec)

- §2 afixo `fome_sede` + aplicabilidade → Tasks 1–2. ✅
- §3 nome com origem → Task 3. ✅
- §4 roller procedural (pesos + fallback Élfica-Alaúde) → Task 4. ✅
- §5 token de loot (2 sites + resolução centralizada + placement) → Task 5. ✅
- §5.1 SKUs de origem na loja → Task 6. ✅
- §6 cliente (`fome_sede` no mirror) → Task 1. ✅
- §7 testes → Tasks 1–6 (TDD) + Task 7 (regressão). ✅

**Lacunas conhecidas (aceitas):**
- `concentracao` como afixo não altera stats (lido direto em `_concentracao_requiem`); o
  teste do roller só garante que ele é gravado quando aplicável (violino), não re-testa o +2
  (já coberto na Fase 3).
- Placement de referência do token fica em 1 monstro; o grosso do placement é autoral.
