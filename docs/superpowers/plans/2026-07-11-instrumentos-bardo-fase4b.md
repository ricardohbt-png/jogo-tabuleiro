# Instrumentos do Bardo — Fase 4b (Encantamento Rúnico — framework + efeitos simples) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Popular o eixo Encantamento (Rúnico) — camada Rúnica em `_instrumento_stats`, os 5 efeitos diretos (Sino/Flauta/Trompa/Violino/Lira), nome Rúnico/Lendário, roller ~4% e SKUs de teste.

**Architecture:** Camada aditiva sobre o framework já plumbado. `runico` dict por base + `_aplicar_runico` em `_instrumento_stats` (server) e no mirror `instrumentoStatsClient` (client); Violino lê o flag no handler do Réquiem; Lira já plumbada; nome/roller/SKU estendidos. Sem mudança de framework.

**Tech Stack:** Python (`server.py`), Vanilla JS (`src/gameState.js`), testes `tools/test_instrumentos_bardo.py`.

**Spec:** `docs/superpowers/specs/2026-07-11-instrumentos-bardo-fase4b-design.md`

---

## Pontos de integração (confirmados; verificar por leitura)
- `criar_instrumento(base, qualidade, origem, encantamento, refinado_bonus, origem_bonus)` já grava `encantamento`.
- `_instrumento_stats` (server.py ~8130) aplica `refinado_bonus` + `origem_bonus`; a camada Rúnica entra antes do clamp `max(0,...)`. `_aplicar_afixo` é `@staticmethod`.
- `_instrumento_nome` (~301 na Fase 4a) — hoje base+qualidade+origem.
- `_processar_requiem_turno` (server.py ~11309): `save_ok, *_ = await self._save_mostrado(m, "vontade", self._instrumento_cd(bardo, off))` — `off` (o Violino) está em escopo.
- `_dueto_marcial_cap(inst)` (server.py ~5245) já dá 2 se `inst.get("encantamento")=="runico"`.
- `gerar_instrumento_aleatorio` (~342) e `instrumento_sku` (~322).
- Cliente `instrumentoStatsClient` (`src/gameState.js` ~1278) — aplica os afixos; a camada Rúnica entra depois.
- `SHOP_MERCHANT` bloco de instrumentos (~2448+).
- Testes: helpers em `tools/test_instrumentos_bardo.py`.

---

## Task 1: Camada Rúnica de stats (server + cliente)

**Files:** `server.py`, `src/gameState.js`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_runico_stat_layer():
    sino = server.criar_instrumento("sino", "padrao", encantamento="runico")
    assert server.GameRoom._instrumento_stats(sino)["dano"] == "1d6"
    flauta = server.criar_instrumento("flauta", "padrao", encantamento="runico")
    assert server.GameRoom._instrumento_stats(flauta)["duracao"] == 5   # 3 + 2
    trompa = server.criar_instrumento("trompa", "padrao", encantamento="runico")
    assert server.GameRoom._instrumento_stats(trompa)["medo"] == 2      # 1 + 1
    # sem Rúnico: inalterado
    assert server.GameRoom._instrumento_stats(server.criar_instrumento("sino", "padrao"))["dano"] == "1d4"
```

- [ ] **Step 2** — Run `python tools/test_instrumentos_bardo.py` → FAIL.

- [ ] **Step 3 — implementar.**

3a. Adicionar `runico` aos 3 bases em `INSTRUMENTOS_BASE` (dentro de cada entrada, ao lado de `stats`):
```python
    # sino:
        "runico": {"dano_set": "1d6"},
    # flauta:
        "runico": {"duracao_delta": 2},
    # trompa:
        "runico": {"medo_delta": 1},
```

3b. Adicionar `_aplicar_runico` (`@staticmethod` em GameRoom, perto de `_aplicar_afixo`):
```python
    @staticmethod
    def _aplicar_runico(st, runico):
        """Camada de Encantamento Rúnico sobre os stats efetivos (só stat-based)."""
        if not runico:
            return
        if "dano_set" in runico:
            st["dano"] = runico["dano_set"]
        if "duracao_delta" in runico and "duracao" in st:
            st["duracao"] += runico["duracao_delta"]
        if "medo_delta" in runico and "medo" in st:
            st["medo"] += runico["medo_delta"]
```

3c. Chamar em `_instrumento_stats`, DEPOIS do `origem_bonus` e ANTES do clamp de custo:
```python
        if inst.get("origem_bonus"):
            GameRoom._aplicar_afixo(st, inst["origem_bonus"])
        if inst.get("encantamento") == "runico":
            GameRoom._aplicar_runico(st, b.get("runico"))
        st["custo_fome"] = max(0, st["custo_fome"])
```

3d. Cliente — em `instrumentoStatsClient` (`src/gameState.js`), DEPOIS do `if (inst.origem_bonus) afixo(...)` e antes do clamp:
```javascript
    if (inst.origem_bonus) afixo(inst.origem_bonus);
    if (inst.encantamento === 'runico' && b.runico) {
      const r = b.runico;
      if ('dano_set' in r) st.dano = r.dano_set;
      if ('duracao_delta' in r && 'duracao' in st) st.duracao += r.duracao_delta;
      if ('medo_delta' in r && 'medo' in st) st.medo += r.medo_delta;
    }
```

- [ ] **Step 4** — Run → PASS. `node --check src/gameState.js` → OK.
- [ ] **Step 5 — Commit:**
```bash
git add server.py src/gameState.js tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): camada Runica de stats (Sino d6, Flauta +2r, Trompa medo 2) + espelho cliente"
```

---

## Task 2: Violino Rúnico (−1 Vontade do alvo) + Lira Rúnica (regressão)

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):
```python
def test_violino_runico_menos_1_vontade():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao", encantamento="runico")
    m = {"id": "m1", "name": "Lich", "hp": 100, "max_hp": 100, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0
    caps = []
    async def _cap(alvo, tipo, dif, extra_mod=0, **k): caps.append(extra_mod); return (True, 20, 0, 20)
    room._save_mostrado = _cap
    _run(room._processar_requiem_turno(m))
    assert caps == [-1]

def test_violino_normal_sem_penalidade():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")   # sem Rúnico
    m = {"id": "m1", "name": "Lich", "hp": 100, "max_hp": 100, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0
    caps = []
    async def _cap(alvo, tipo, dif, extra_mod=0, **k): caps.append(extra_mod); return (True, 20, 0, 20)
    room._save_mostrado = _cap
    _run(room._processar_requiem_turno(m))
    assert caps == [0]

def test_lira_runica_cap_2():
    room, p = _room_bardo()
    inst = server.criar_instrumento("lira", "padrao", encantamento="runico")
    assert room._dueto_marcial_cap(inst) == 2
    assert room._dueto_marcial_cap(server.criar_instrumento("lira", "padrao")) == 1
```

- [ ] **Step 2** — Run → FAIL (Violino ainda não passa `extra_mod`).

- [ ] **Step 3 — implementar.** Em `_processar_requiem_turno` (~11309), trocar a linha do save:
```python
        save_ok, *_ = await self._save_mostrado(m, "vontade", self._instrumento_cd(bardo, off))
```
por:
```python
        extra = -1 if off.get("encantamento") == "runico" else 0   # Violino Rúnico: -1 Vontade do alvo
        save_ok, *_ = await self._save_mostrado(m, "vontade", self._instrumento_cd(bardo, off), extra_mod=extra)
```
(Lira: nada a mudar — `_dueto_marcial_cap` já lê o encantamento; o 3º teste é regressão.)

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Violino Runico -1 Vontade do alvo (Requiem) + regressao Lira Runica 2x"
```

---

## Task 3: Nome — Lendário + sufixo Rúnico

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):
```python
def test_nome_runico():
    assert server.criar_instrumento("sino", "padrao", encantamento="runico")["name"] == "Sino Padrão Rúnico"
    assert server.criar_instrumento("harpa", "velho", encantamento="runico")["name"] == "Harpa Velha Rúnica"

def test_nome_lendario():
    # Refinado + Élfica + Rúnico → Lendário (substitui, mantém origem)
    inst = server.criar_instrumento("harpa", "refinado", origem="elfica",
                                    origem_bonus="cd", encantamento="runico")
    assert inst["name"] == "Harpa Lendária Élfica"
    inst2 = server.criar_instrumento("tambor", "refinado", origem="ana",
                                     origem_bonus="fome_sede", encantamento="runico")
    assert inst2["name"] == "Tambor de Guerra Lendário Anão"

def test_nome_sem_runico_inalterado():
    assert server.criar_instrumento("harpa", "velho")["name"] == "Harpa Velha"
    assert server.criar_instrumento("harpa", "refinado", origem="elfica",
                                    origem_bonus="cd")["name"] == "Harpa Refinada Élfica"
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.** Adicionar as tabelas (perto de `_ORIGEM_LABEL`):
```python
_RUNICO_LABEL   = ("Rúnico", "Rúnica")
_LENDARIO_LABEL = ("Lendário", "Lendária")
```
Reescrever `_instrumento_nome`:
```python
def _instrumento_nome(inst):
    b = INSTRUMENTOS_BASE[inst["base"]]
    fem = inst["base"] in _INSTRUMENTO_GENERO_FEM
    orig = inst.get("origem", "humana")
    runico = inst.get("encantamento") == "runico"
    # Lendário: 3 eixos no máximo → "Lendária/o" no lugar de qualidade+Rúnico; origem mantida.
    if inst.get("qualidade") == "refinado" and orig in _ORIGEM_LABEL and runico:
        return f"{b['nome']} {_LENDARIO_LABEL[1 if fem else 0]} {_ORIGEM_LABEL[orig][1 if fem else 0]}"
    ql = _QUALIDADE_LABEL.get(inst["qualidade"], ("Padrão", "Padrão"))[1 if fem else 0]
    nome = f"{b['nome']} {ql}"
    if orig in _ORIGEM_LABEL:
        nome += " " + _ORIGEM_LABEL[orig][1 if fem else 0]
    if runico:
        nome += " " + _RUNICO_LABEL[1 if fem else 0]
    return nome
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): nome Runico + rotulo Lendario (substitui, mantem origem)"
```

---

## Task 4: Roller Rúnico (~4%) + `instrumento_sku` com encantamento

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):
```python
def test_roller_gera_runico():
    _rnd.seed(7)
    encs = set()
    for _ in range(2000):
        encs.add(server.gerar_instrumento_aleatorio().get("encantamento"))
    assert "runico" in encs and "nenhum" in encs   # gera ambos ao longo das amostras

def test_roller_runico_valido():
    _rnd.seed(11)
    for _ in range(2000):
        inst = server.gerar_instrumento_aleatorio()
        if inst.get("encantamento") == "runico":
            assert inst["tipo_item"] == "instrumento"
            server.GameRoom._instrumento_stats(inst)   # não lança

def test_sku_encantamento():
    sku = server.instrumento_sku("sino", "padrao", preco=300, encantamento="runico")
    assert sku["encantamento"] == "runico"
    assert sku["id"] == "instrumento_sino_padrao_runico"
    assert "Rúnico" in sku["name"]
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.**

3a. `gerar_instrumento_aleatorio` — sortear encantamento e repassar. Trocar o `return`:
```python
    encantamento = "runico" if random.random() < 0.04 else "nenhum"
    return criar_instrumento(base, qualidade, origem, encantamento, refinado_bonus, origem_bonus)
```

3b. `instrumento_sku` — novo param `encantamento` + sufixo no id:
```python
def instrumento_sku(base, qualidade="padrao", preco=100, refinado_bonus=None,
                    origem="humana", origem_bonus=None, encantamento="nenhum"):
    """Instância de instrumento para a loja/loot (id único + price/buy_price)."""
    inst = criar_instrumento(base, qualidade, origem=origem, encantamento=encantamento,
                             refinado_bonus=refinado_bonus, origem_bonus=origem_bonus)
    suf = f"_{origem}" if origem in ("elfica", "ana") else ""
    if encantamento == "runico":
        suf += "_runico"
    inst["id"] = f"instrumento_{base}_{qualidade}{suf}"
    inst["price"] = preco
    inst["buy_price"] = preco
    return inst
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): roller sorteia Runico (~4%) + instrumento_sku com encantamento"
```

---

## Task 5: SKUs de teste na loja (Rúnico + Lendário)

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_skus_runico_lendario():
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_sino_padrao_runico" in ids
    assert "instrumento_violino_padrao_runico" in ids
    # Lendário (Refinado + Élfica + Rúnico) na loja, com nome "Lendária"
    lend = next(i for i in server.SHOP_MERCHANT
                if i.get("id") == "instrumento_harpa_refinado_elfica_runico")
    assert "Lendária" in lend["name"]
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.** Após os SKUs de origem (Fase 4a) no bloco de instrumentos de `SHOP_MERCHANT`, adicionar:
```python
    # Encantamento Rúnico (Fase 4b) — compráveis para teste.
    instrumento_sku("sino",    "padrao", 300, encantamento="runico"),
    instrumento_sku("flauta",  "padrao", 340, encantamento="runico"),
    instrumento_sku("trompa",  "padrao", 400, encantamento="runico"),
    instrumento_sku("violino", "padrao", 560, encantamento="runico"),
    instrumento_sku("lira",    "padrao", 360, encantamento="runico"),
    # Lendário (Refinado + Élfica + Rúnico) — o topo dos 3 eixos.
    instrumento_sku("harpa", "refinado", 900, origem="elfica", origem_bonus="cd", encantamento="runico"),
]
```
(Substituir o `]` final do bloco de instrumentos por essas linhas + `]`; garantir que o id da Harpa Lendária é `instrumento_harpa_refinado_elfica_runico` — origem antes de `_runico`.)

- [ ] **Step 4** — Run → PASS. `python tools/test_roteamento_itens.py` → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): SKUs Runico + Lendario na loja para teste"
```

---

## Task 6: Docs + regressão final

**Files:** `CLAUDE.md`; Test suíte.

- [ ] **Step 1 — CLAUDE.md.** Após o bloco da Fase 4a dos instrumentos, adicionar um `>`:
```markdown
> **Fase 4b (Encantamento Rúnico — framework + efeitos simples):** popula o 3º eixo. Camada
> Rúnica em `_instrumento_stats` (`_aplicar_runico` lê o dict `runico` do base quando
> `encantamento=="runico"`): Sino `dano→1d6`, Flauta `duracao +2` (3/4/5), Trompa `medo +1`
> (Amedrontado 2r). Violino Rúnico: `_processar_requiem_turno` passa `extra_mod=-1` no save
> de Vontade do alvo. Lira Rúnica: 2×/rodada (já plumbado em `_dueto_marcial_cap`). Nome
> (`_instrumento_nome`): sufixo "Rúnico/a"; **Lendário** (Refinado + origem≠Humana + Rúnico)
> substitui por "Lendária/o {Origem}" (ex.: "Harpa Lendária Élfica"). Roller sorteia Rúnico
> ~4% (independente de origem/qualidade). `instrumento_sku` ganhou `encantamento` (id
> `..._runico`); SKUs Rúnicos + 1 Lendário na loja **para teste**. Cliente:
> `instrumentoStatsClient` espelha a camada Rúnica. Fase 4c (efeitos Rúnicos bespoke): Harpa
> (Nota Cortante em linha), Tambor (Atordoa/−1 Ataque), Alaúde (+resistências na Canção).
> Testes: `tools/test_instrumentos_bardo.py`.
```
Verificar cada afirmação contra o código.

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
git commit -m "docs(instrumentos): documenta Fase 4b (Encantamento Runico) no CLAUDE.md"
```

---

## Self-Review (cobertura do spec)

- §2 camada Rúnica (Sino/Flauta/Trompa) + cliente → Task 1. ✅
- §3 Violino (−1 Vontade) + Lira (regressão) → Task 2. ✅
- §4 nome Rúnico/Lendário → Task 3. ✅
- §5 roller ~4% → Task 4. ✅
- §6 SKUs de teste (Rúnico + Lendário) → Tasks 4–5. ✅
- §7 testes → Tasks 1–5 (TDD) + Task 6 (regressão). ✅

**Lacunas conhecidas (aceitas):**
- A chance de 4% no roller é testada por presença (gera ambos ao longo de 2000 amostras),
  não pela proporção exata (evita flakiness estatística).
- Os efeitos bespoke (Harpa/Tambor/Alaúde) NÃO estão nesta fase (4c) — um Rúnico dessas 3
  bases já pode ser gerado/comprado, mas seu efeito Rúnico específico só chega na 4c
  (o instrumento funciona normalmente, só sem o bônus Rúnico dedicado). Documentar.
