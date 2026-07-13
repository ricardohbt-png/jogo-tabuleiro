# Instrumentos do Bardo — Fase 5 (Improviso / Gaita) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar a Gaita (habilidade Improviso — tabela 2d6 meta que invoca as habilidades dos outros instrumentos, com Encore/Grande Encore), fechando o sistema de instrumentos do bardo.

**Architecture:** Servidor autoritativo em `server.py`: nova base `gaita` em `INSTRUMENTOS_BASE`; `_instr_improviso` rola uma cascata 2d6 (pura, recursiva na Rúnica) e reusa os `_instr_*` existentes sintetizando um instrumento virtual no tier da Gaita; Encore/Grande Encore descontam fome/sede via um helper central novo `_pagar_fome_sede`. Passos com alvo são enfileirados e mirados pelo cliente (novo `improviso_alvo`). Cliente reusa o botão de instrumento do HUD + um quadro de resultado.

**Tech Stack:** Python 3 (`websockets`), Vanilla JS (cliente), testes `tools/test_*.py` (asyncio, monkeypatch de `server.roll_dice`).

**Spec:** `docs/superpowers/specs/2026-07-12-instrumentos-bardo-fase5-design.md`

**⚠️ WIP no working tree:** `server.py` e `game.js` têm alterações não-commitadas do usuário (ácido/veneno, GLB/trap). **Antes de executar**, o working tree deve estar limpo (usuário commita/stasha o WIP) para que os commits da Fase 5 não varram o WIP. Ver "Pré-requisito" no handoff.

---

## Convenções de teste (ler antes de começar)

`tools/test_instrumentos_bardo.py` já existe. Padrão:
- `room, p = _room_bardo()` cria uma sala mínima com o bardo Henrique (`fome/sede=100`).
- `_run(coro)` = `asyncio.run(coro)`.
- Stubar assíncronos: `room.gm_say = noop`, `room.send_to = noop`, `room.push_state = noop`
  (onde `async def noop(*a, **k): pass`).
- Forçar rolagens: `server.roll_dice = lambda s: N` (restaurar depois), `room._save_mostrado`,
  `room._rolar_dano_mostrado`, `room._rolar_ataque`.
- Rodar: `python tools/test_instrumentos_bardo.py` (o arquivo chama os testes no fim, ou
  usar `pytest tools/test_instrumentos_bardo.py -v` se preferir — verifique o rodapé do
  arquivo e siga o padrão existente).

Cada tarefa: escreve teste → roda e falha → implementa → roda e passa → commita.

---

## Task 1: Base `gaita` em `INSTRUMENTOS_BASE`

**Files:**
- Modify: `server.py` (dict `INSTRUMENTOS_BASE`, após a entrada `"violino"`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_gaita_base_existe():
    b = server.INSTRUMENTOS_BASE["gaita"]
    assert b["maos"] == 1 and b["modo"] == "ativada"
    assert b["habilidade_nome"] == "Improviso"
    assert b["efeito"]["tipo"] == "improviso"
    assert b["custo_fome"] == 3 and b["custo_sede"] == 3
    assert b["runico"]["grande_encore"] is True

def test_gaita_nome_e_genero():
    assert server.criar_instrumento("gaita", "velho")["name"] == "Gaita Velha"
    inst = server.criar_instrumento("gaita", "padrao", encantamento="runico")
    assert "Rúnica" in inst["name"], inst["name"]

def test_gaita_stats_custo():
    st = server.GameRoom._instrumento_stats(server.criar_instrumento("gaita", "padrao"))
    assert st["custo_fome"] == 3 and st["custo_sede"] == 3
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: KeyError `'gaita'`.

- [ ] **Step 3: Implementar — adicionar a base**

Em `server.py`, dentro de `INSTRUMENTOS_BASE`, logo após a entrada `"violino": {…},` e antes do `}` que fecha o dict:

```python
    "gaita": {
        "nome": "Gaita", "icon": "🪗", "maos": 1, "modo": "ativada",
        "habilidade_nome": "Improviso",
        "desc": "Rola 2d6 e improvisa a habilidade de outro instrumento (no tier da "
                "Gaita). 12 = Encore: toca de novo duas vezes. A Gaita Rúnica pode "
                "escalar até o Grande Encore.",
        "efeito": {"tipo": "improviso"},
        "custo_fome": 3, "custo_sede": 3,
        "afixos_validos": ["fome", "sede"],
        "stats": {
            "velho":   {},
            "rustico": {},
            "padrao":  {},
        },
        "runico": {"grande_encore": True},
    },
```

`_INSTRUMENTO_GENERO_FEM` já contém `"gaita"` (não mexer). `_instrumento_stats` já
devolve `custo_fome`/`custo_sede` a partir do `custo_fome`/`custo_sede` da base.

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: os 3 novos testes passam.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): base Gaita (Improviso) em INSTRUMENTOS_BASE"
```

---

## Task 2: Rolagem da cascata 2d6 — `_rolar_2d6` + `_improviso_rolar_cascata`

Função **pura** (sem I/O) que resolve toda a lógica de Encore/Grande Encore e devolve
os passos aplicáveis + os gatilhos meta. Isolá-la torna a mecânica testável sem stubar
efeitos.

**Files:**
- Modify: `server.py` (métodos novos na classe `GameRoom`, perto de `handle_usar_instrumento`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_cascata_sem_encore():
    room, p = _room_bardo()
    room._rolar_2d6 = lambda: 7
    passos, meta = room._improviso_rolar_cascata(runico=False)
    assert passos == [7]
    assert meta == {"encore_menor": False, "grande_encore": False}

def test_cascata_encore_simples():
    room, p = _room_bardo()
    seq = iter([12, 7, 3])  # 12 → rola 7 e 3
    room._rolar_2d6 = lambda: next(seq)
    passos, meta = room._improviso_rolar_cascata(runico=False)
    assert passos == [7, 3]              # os dois rerolls
    assert meta["encore_menor"] is False and meta["grande_encore"] is False

def test_cascata_encore_menor():
    room, p = _room_bardo()
    seq = iter([12, 12, 5])  # 12 → rola 12 (2º doze) e 5; não-rúnica NÃO recursa
    room._rolar_2d6 = lambda: next(seq)
    passos, meta = room._improviso_rolar_cascata(runico=False)
    assert passos == [5]                 # o 12 do reroll não vira passo aplicável
    assert meta["encore_menor"] is True and meta["grande_encore"] is False

def test_cascata_grande_encore_runica():
    room, p = _room_bardo()
    # 12 → [12, 3]; o 12 interno (rúnica) recursa → [12, 4]; o 12 aninhado (3º doze) recursa → [2, 3]
    seq = iter([12, 12, 3, 12, 4, 2, 3])
    room._rolar_2d6 = lambda: next(seq)
    passos, meta = room._improviso_rolar_cascata(runico=True)
    assert meta["encore_menor"] is True and meta["grande_encore"] is True
    assert 12 not in passos              # 12 nunca vira passo aplicável

def test_cascata_teto_anti_loop():
    room, p = _room_bardo()
    room._rolar_2d6 = lambda: 12         # sempre 12 (rúnica): precisa terminar
    passos, meta = room._improviso_rolar_cascata(runico=True)
    assert meta["grande_encore"] is True # atingiu o teto sem travar
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: AttributeError `_improviso_rolar_cascata`.

- [ ] **Step 3: Implementar**

Em `server.py`, dentro de `class GameRoom`, adicionar (perto de `handle_usar_instrumento`):

```python
    def _rolar_2d6(self):
        return random.randint(1, 6) + random.randint(1, 6)

    def _improviso_rolar_cascata(self, runico, _profundidade=0, _contador=None):
        """Resolve a cascata de Improviso. Devolve (passos, meta):
          passos: lista ordenada de resultados 2–11 aplicáveis (12 nunca entra);
          meta: {'encore_menor': bool, 'grande_encore': bool}.
        Regra: 12 = Encore → rola +2×. O 2º 12 na cadeia liga encore_menor.
        Só a Gaita Rúnica recursa em cada 12; o 3º 12 liga grande_encore.
        _contador conta quantos 12 já saíram na linhagem (para Encore Menor/Grande)."""
        if _contador is None:
            _contador = [0]
        passos = []
        meta = {"encore_menor": False, "grande_encore": False}
        TETO = 40  # guarda anti-loop (rúnica com 12 infinito)
        r = self._rolar_2d6()
        if r != 12:
            passos.append(r)
            return passos, meta
        # r == 12 → Encore: rola +2×
        _contador[0] += 1
        if _contador[0] >= 2:
            meta["encore_menor"] = True
        if _contador[0] >= 3 and runico:
            meta["grande_encore"] = True
        for _ in range(2):
            if _contador[0] > TETO:
                meta["grande_encore"] = meta["grande_encore"] or (_contador[0] >= 3 and runico)
                break
            sub = self._rolar_2d6()
            if sub == 12:
                _contador[0] += 1
                if _contador[0] >= 2:
                    meta["encore_menor"] = True
                if _contador[0] >= 3 and runico:
                    meta["grande_encore"] = True
                if runico:
                    sp, sm = self._improviso_rolar_cascata(
                        runico, _profundidade + 1, _contador)
                    passos.extend(sp)
                    meta["encore_menor"] = meta["encore_menor"] or sm["encore_menor"]
                    meta["grande_encore"] = meta["grande_encore"] or sm["grande_encore"]
                # não-rúnica: o 12 do reroll não recursa nem vira passo
            else:
                passos.append(sub)
        return passos, meta
```

> **Nota de implementação:** o `_rolar_2d6` recursivo é chamado de novo dentro do
> ramo rúnico; para os testes com `seq = iter([...])` isso consome a sequência na
> ordem em que os 12 disparam mais rerolls — os valores de teste acima já refletem
> essa ordem. Verifique que `import random` está no topo de `server.py` (já está).

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: os 5 testes de cascata passam.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Improviso — rolagem da cascata 2d6 (Encore/Grande Encore)"
```

---

## Task 3: Helper central de custo — `_custo_fome_sede_efetivo` + `_pagar_fome_sede`

Sem migração de sites ainda (Task 7). Só o helper e a leitura dos estados de Encore.

**Files:**
- Modify: `server.py` (métodos novos na classe `GameRoom`, perto de `_cobrar_manutencao_cancao`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_pagar_fome_sede_sem_encore():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    room._pagar_fome_sede(p, 3, 2)
    assert p["fome"] == 7 and p["sede"] == 8

def test_pagar_fome_sede_encore_menor():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    p["encore_menor_ate"] = room.round_num
    room._pagar_fome_sede(p, 3, 2)
    assert p["fome"] == 8 and p["sede"] == 9   # -1 cada (piso 0)

def test_pagar_fome_sede_grande_encore():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    p["grande_encore_ate"] = room.round_num
    room._pagar_fome_sede(p, 5, 5)
    assert p["fome"] == 10 and p["sede"] == 10  # custo 0

def test_pagar_fome_sede_magia_gratis():
    room, p = _room_bardo()
    p["fome"] = 10; p["sede"] = 10
    p["encore_magia_gratis"] = 1
    room._pagar_fome_sede(p, 4, 4, contexto="magia")
    assert p["fome"] == 10 and p["sede"] == 10
    assert p.get("encore_magia_gratis", 0) == 0  # consumiu a carga
    # segunda magia já paga normal
    room._pagar_fome_sede(p, 4, 4, contexto="magia")
    assert p["fome"] == 6 and p["sede"] == 6

def test_pagar_fome_sede_piso_zero():
    room, p = _room_bardo()
    p["fome"] = 1; p["sede"] = 0
    room._pagar_fome_sede(p, 3, 3)
    assert p["fome"] == 0 and p["sede"] == 0
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: AttributeError `_pagar_fome_sede`.

- [ ] **Step 3: Implementar**

Em `server.py`, dentro de `class GameRoom` (perto de `_cobrar_manutencao_cancao`):

```python
    def _custo_fome_sede_efetivo(self, p, fome, sede, contexto=None):
        """Custo após descontos de Encore. Grande Encore zera; Encore Menor -1/-1;
        magia grátis (Mago/Clérigo, contexto='magia') zera e consome a carga."""
        if p.get("grande_encore_ate", -1) >= self.round_num:
            return 0, 0
        if contexto == "magia" and p.get("encore_magia_gratis", 0) > 0 \
           and p.get("class_id") in ("mage", "cleric"):
            p["encore_magia_gratis"] = p.get("encore_magia_gratis", 0) - 1
            return 0, 0
        if p.get("encore_menor_ate", -1) >= self.round_num:
            return max(0, fome - 1), max(0, sede - 1)
        return fome, sede

    def _pagar_fome_sede(self, p, fome, sede, contexto=None):
        """Débito central de fome/sede com desconto de Encore. Piso 0.
        Retorna (fome_paga, sede_paga)."""
        f, s = self._custo_fome_sede_efetivo(p, fome, sede, contexto)
        p["fome"] = max(0, p.get("fome", 0) - f)
        p["sede"] = max(0, p.get("sede", 0) - s)
        return f, s
```

> **Atenção ao Grande Encore + magia grátis:** o Grande Encore já zera tudo antes de
> chegar no ramo de `contexto=='magia'`, então a carga `encore_magia_gratis` NÃO é
> consumida indevidamente durante o Grande Encore. Correto.

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: os 5 testes passam.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): helper central _pagar_fome_sede com desconto de Encore"
```

---

## Task 4: Aplicação dos gatilhos meta — Encore Menor / Grande Encore

**Files:**
- Modify: `server.py` (métodos novos na classe `GameRoom`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def _add_aliado(room, pid, pos, cls="warrior", cancao=False):
    q = {"id": pid, "name": pid, "class_id": cls, "alive": True, "pos": pos,
         "fome": 100, "sede": 100, "gear": {k: None for k in server.GEAR_SLOTS}}
    if cancao:
        q["buffs_cancao"] = {}
    room.players[pid] = q
    return q

def test_encore_menor_raio5():
    room, p = _room_bardo()
    perto = _add_aliado(room, "a1", [7, 5], "warrior")     # dist 2 → dentro
    longe = _add_aliado(room, "a2", [20, 20], "mage")      # fora do raio 5
    room._aplicar_encore_menor(p)
    assert perto["encore_menor_ate"] == room.round_num
    assert "encore_menor_ate" not in longe
    assert p["encore_menor_ate"] == room.round_num          # o bardo também

def test_encore_menor_magia_gratis_mago_clerigo():
    room, p = _room_bardo()
    mago = _add_aliado(room, "m1", [6, 5], "mage")
    guerreiro = _add_aliado(room, "g1", [6, 6], "warrior")
    room._aplicar_encore_menor(p)
    assert mago["encore_magia_gratis"] == 1
    assert guerreiro.get("encore_magia_gratis", 0) == 0

def test_grande_encore_sob_cancao():
    room, p = _room_bardo()
    server.roll_dice = lambda s: 3   # 1d4 → 3
    dentro = _add_aliado(room, "c1", [9, 9], "cleric", cancao=True)
    fora = _add_aliado(room, "c2", [9, 8], "warrior", cancao=False)
    room._aplicar_grande_encore(p)
    assert dentro["grande_encore_ate"] == room.round_num + 3
    assert "grande_encore_ate" not in fora
    assert dentro["encore_magia_gratis"] >= 999   # magias ilimitadas p/ clérigo sob canção
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: AttributeError `_aplicar_encore_menor`.

- [ ] **Step 3: Implementar**

```python
    def _aplicar_encore_menor(self, bardo):
        """1 rodada: aliados do bardo em raio 5 (incl. ele) gastam -1🍖/-1💧;
        Mago/Clérigo ganham 1 magia grátis."""
        for q in self.players.values():
            if not q.get("alive"):
                continue
            if _distancia_chebyshev(q["pos"], bardo["pos"]) > 5:
                continue
            q["encore_menor_ate"] = self.round_num
            if q.get("class_id") in ("mage", "cleric"):
                q["encore_magia_gratis"] = max(q.get("encore_magia_gratis", 0), 1)

    def _aplicar_grande_encore(self, bardo):
        """1d4 rodadas: todos sob a Canção Heroica agem sem custo; Mago/Clérigo
        magias ilimitadas grátis."""
        dur = server.roll_dice("1d4") if hasattr(server, "roll_dice") else roll_dice("1d4")
        ate = self.round_num + dur
        for q in self.players.values():
            if not q.get("alive") or "buffs_cancao" not in q:
                continue
            q["grande_encore_ate"] = ate
            if q.get("class_id") in ("mage", "cleric"):
                q["encore_magia_gratis"] = 999999
```

> **`buffs_cancao`:** é a chave que marca "sob a Canção Heroica" (mesmo critério do
> Alaúde Rúnico da Fase 4c — "sob a Canção" = `buffs_cancao` presente). Confirme o
> nome exato da chave em `_aplicar_buffs_cancao` e ajuste se necessário.
> **`roll_dice`:** é uma função de módulo em `server.py`; chame `roll_dice("1d4")`
> diretamente (o `hasattr` acima é só defensivo — simplifique para `roll_dice("1d4")`
> se preferir, já que os testes monkeypatcham `server.roll_dice`).

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: os 3 testes passam.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Encore Menor / Grande Encore (aplicação nos aliados)"
```

---

## Task 5: `_instr_improviso` — dispatcher + efeitos sem-alvo

Aplica os passos sem-alvo (2,3,4,5,6,8,10) reusando os `_instr_*` com instrumento
virtual, força durações a 1 rodada, aplica os gatilhos meta, e enfileira os com-alvo.

**Files:**
- Modify: `server.py` (novo método `_instr_improviso` + helpers `_improviso_invocar_st`,
  `_improviso_aplicar_passo`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def _bardo_com_gaita(qual="padrao", runico=False):
    room, p = _room_bardo()
    async def noop(*a, **k): pass
    room.gm_say = noop; room.send_to = noop; room.push_state = noop
    p["gear"]["off_hand"] = server.criar_instrumento(
        "gaita", qual, encantamento=("runico" if runico else "nenhum"))
    return room, p

def test_improviso_resultado_ecos_1rodada():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 4          # Ecos Dolorosos
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["ecos_ate"] == room.round_num + 1     # forçado a 1 rodada

def test_improviso_resultado_desafinado():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 2
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["desafinado_ate"] == room.round_num + 1

def test_improviso_enfileira_alvo():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 7          # Nota Cortante — precisa de alvo
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    fila = p.get("improviso_pendente", [])
    assert len(fila) == 1 and fila[0]["res"] == 7 and fila[0]["alvo_tipo"] == "monstro"

def test_improviso_encore_aplica_meta():
    room, p = _bardo_com_gaita()
    seq = iter([12, 8, 12])  # 12 → [8, 12]; o 12 do reroll → Encore Menor (não-rúnica)
    room._rolar_2d6 = lambda: next(seq)
    room._save_mostrado = _make_save(True); room._rolar_dano_mostrado = _make_dano(0)
    room.monsters = {}   # sem alvos p/ o Acorde: só não deve crashar
    st = server.GameRoom._instrumento_stats(p["gear"]["off_hand"])
    _run(room._instr_improviso(p, p["gear"]["off_hand"], st, {}))
    assert p["encore_menor_ate"] == room.round_num
```

Adicione ao arquivo os helpers de teste `_make_save`/`_make_dano` se ainda não existirem:

```python
def _make_save(ok):
    async def _s(m, tipo, cd, **k): return (ok, 10, cd)
    return _s
def _make_dano(n):
    async def _d(nd, faces, label): return n
    return _d
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: AttributeError `_instr_improviso`.

- [ ] **Step 3: Implementar**

```python
    # Passos que precisam de alvo/direção (enfileirados p/ o cliente mirar)
    _IMPROVISO_ALVO = {7: ("nota_cortante", "monstro"),
                       9: ("requiem_tick", "monstro"),
                       11: ("chamado_general", "direcao")}
    # Passos sem alvo: (base_invocada, forca_duracao_1)
    _IMPROVISO_AUTO = {
        4: ("sino",   True),    # Ecos Dolorosos, 1 rodada
        5: ("lira",   True),    # Dueto Marcial, 1 rodada
        6: ("flauta", True),    # Dueto Fantasma, 1 rodada
        8: ("tambor", False),   # Acorde Trovejante (auto, raio)
        10:("alaude", None),    # Sinfonia (tratada à parte)
    }

    def _improviso_tier(self, inst):
        q = inst.get("qualidade", "padrao")
        return "padrao" if q == "refinado" else q

    def _improviso_virt_st(self, inst, base):
        """Instrumento virtual da base invocada no tier da Gaita + seus stats."""
        virt = {"base": base, "qualidade": self._improviso_tier(inst),
                "origem": "humana", "encantamento": "nenhum",
                "tipo_item": "instrumento"}
        return virt, self._instrumento_stats(virt)

    async def _instr_improviso(self, p, inst, st, data):
        runico = inst.get("encantamento") == "runico"
        passos, meta = self._improviso_rolar_cascata(runico)
        # gatilhos meta primeiro (afetam custos das ações subsequentes na rodada)
        if meta["grande_encore"]:
            self._aplicar_grande_encore(p)
        if meta["encore_menor"]:
            self._aplicar_encore_menor(p)
        p.setdefault("improviso_pendente", [])
        cascata_cli = []
        for res in passos:
            cascata_cli.append({"res": res, "nome": self._improviso_nome_passo(res),
                                "precisa_alvo": res in self._IMPROVISO_ALVO})
            if res in self._IMPROVISO_ALVO:
                _tipo, alvo_tipo = self._IMPROVISO_ALVO[res]
                p["improviso_pendente"].append(
                    {"res": res, "tier": self._improviso_tier(inst), "alvo_tipo": alvo_tipo})
            else:
                await self._improviso_aplicar_passo(p, inst, res)
        await self.send_to(p["id"], {
            "type": "improviso_resultado", "cascata": cascata_cli,
            "encore_menor": meta["encore_menor"], "grande_encore": meta["grande_encore"],
            "pendentes": len(p["improviso_pendente"])})
        return True

    async def _improviso_aplicar_passo(self, p, inst, res):
        """Aplica um passo sem-alvo (2,3,4,5,6,8,10)."""
        if res == 3:
            await self.gm_say(f"🪗 **{p['name']}** improvisa… e desafina de leve (nada acontece).")
            return
        if res == 2:
            p["desafinado_ate"] = self.round_num + 1
            await self.gm_say(f"🪗 **{p['name']}** improvisa e **desafina** — -1 em ataques e CDs até o próximo turno.")
            return
        if res == 10:  # Sinfonia temporária (1 rodada)
            _virt, vst = self._improviso_virt_st(inst, "alaude")
            p["sinfonia_temp_ate"] = self.round_num + 1
            p["sinfonia_temp_atributos"] = list(vst.get("atributos", []))
            await self.gm_say(f"🪗 **{p['name']}** improvisa a **Sinfonia Heroica** por 1 rodada!")
            return
        base, forca_dur = self._IMPROVISO_AUTO[res]
        virt, vst = self._improviso_virt_st(inst, base)
        if forca_dur:
            vst = dict(vst); vst["duracao"] = 1
        if base == "sino":
            await self._instr_ecos_dolorosos(p, virt, vst, {})
        elif base == "lira":
            await self._instr_dueto_marcial(p, virt, vst, {})
        elif base == "flauta":
            await self._instr_dueto_fantasma(p, virt, vst, {})
        elif base == "tambor":
            await self._instr_acorde_trovejante(p, virt, vst, {})

    def _improviso_nome_passo(self, res):
        return {2: "Desafinado", 3: "Falha", 4: "Ecos Dolorosos", 5: "Dueto Marcial",
                6: "Dueto Fantasma", 7: "Nota Cortante", 8: "Acorde Trovejante",
                9: "Réquiem (1ª rodada)", 10: "Sinfonia Heroica",
                11: "Chamado do General"}.get(res, "?")
```

> **`_save_mostrado` assinatura:** confirme a assinatura real (nos testes existentes é
> `_save_mostrado(m, tipo, cd)` retornando `(save_ok, roll, …)`). Os helpers de efeito
> chamados já a usam — nenhuma mudança aqui.

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: os testes de improviso passam.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): _instr_improviso — passos sem-alvo + fila de alvos + meta"
```

---

## Task 6: Réquiem tick + resolução de alvos — `handle_improviso_alvo`

**Files:**
- Modify: `server.py` (novos `_improviso_requiem_tick`, `handle_improviso_alvo`; roteamento
  da mensagem no despachante WebSocket)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_improviso_alvo_nota_cortante():
    room, p = _bardo_com_gaita()
    room.monsters = {"m1": {"id": "m1", "name": "Orc", "hp": 30, "pos": [6, 5],
                            "def_reflexos": 0}}
    room._save_mostrado = _make_save(False); room._rolar_dano_mostrado = _make_dano(6)
    room._instrumento_cd = lambda p, inst: 11
    p["improviso_pendente"] = [{"res": 7, "tier": "padrao", "alvo_tipo": "monstro"}]
    _run(room.handle_improviso_alvo("p1", {"target_id": "m1"}))
    assert room.monsters["m1"]["hp"] == 24     # 30 - 6
    assert p["improviso_pendente"] == []

def test_improviso_requiem_tick():
    room, p = _bardo_com_gaita()
    room.monsters = {"m1": {"id": "m1", "name": "Orc", "hp": 30, "pos": [6, 5]}}
    room._save_mostrado = _make_save(False); room._instrumento_cd = lambda p, i: 11
    server.roll_dice = lambda s: 5
    virt, vst = room._improviso_virt_st(p["gear"]["off_hand"], "violino")
    _run(room._improviso_requiem_tick(p, virt, vst, room.monsters["m1"]))
    assert room.monsters["m1"]["hp"] == 25     # 30 - (1 × d6=5)
    assert "requiem_alvo" not in p             # não inicia o Réquiem sustentado
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: AttributeError `handle_improviso_alvo`.

- [ ] **Step 3: Implementar**

```python
    async def _improviso_requiem_tick(self, p, virt, st, m):
        """Só a 1ª rodada do Réquiem: Vontade vs CD → falha sofre 1×dado do tier."""
        if not m or m.get("hp", 0) <= 0:
            return
        save_ok, *_ = await self._save_mostrado(m, "vontade", self._instrumento_cd(p, virt))
        if save_ok:
            await self.gm_say(f"🎻 **{m['name']}** resiste ao lamento improvisado.")
            return
        dano = server.roll_dice(st["dado"]) if hasattr(server, "roll_dice") else roll_dice(st["dado"])
        m["hp"] = max(0, m["hp"] - dano)
        await self.gm_say(f"🎻 O Réquiem improvisado fere **{m['name']}** em **{dano}**!")
        if m["hp"] <= 0:
            await self._monster_dies(m, p["id"])

    async def handle_improviso_alvo(self, pid, data=None):
        p = self.players.get(pid)
        if not p or not p.get("alive") or not self._is_turn(pid):
            return
        fila = p.get("improviso_pendente") or []
        if not fila:
            return
        passo = fila.pop(0)
        inst = p["gear"].get("off_hand")
        if not inst or inst.get("base") != "gaita":
            await self.push_state(); return
        virt_base = {7: "harpa", 9: "violino", 11: "trompa"}[passo["res"]]
        virt, vst = self._improviso_virt_st(inst, virt_base)
        if passo["res"] == 7:
            await self._instr_nota_cortante(p, virt, vst, {"target_id": (data or {}).get("target_id")})
        elif passo["res"] == 9:
            m = self.monsters.get((data or {}).get("target_id"))
            if m and self._no_raio(p, m, vst.get("alcance", 6)):
                await self._improviso_requiem_tick(p, virt, vst, m)
            else:
                await self.send_to(pid, {"type": "error", "msg": "Alvo do Réquiem inválido."})
        elif passo["res"] == 11:
            await self._instr_chamado_general(p, virt, vst, {"dir": (data or {}).get("dir")})
        await self.push_state()
```

Roteamento WebSocket: localize o despachante de mensagens (onde estão os `elif t ==
"usar_instrumento":`), e adicione:

```python
                elif t == "improviso_alvo":
                    await room.handle_improviso_alvo(pid, msg)
```

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: passa.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): resolução de alvos do Improviso (Nota/Réquiem/Chamado)"
```

---

## Task 7: Ligar o Improviso ao `handle_usar_instrumento` + limpeza no end_turn

**Files:**
- Modify: `server.py` (`handle_usar_instrumento` dispatch; débito via helper;
  `handle_end_turn` limpeza da fila)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_usar_instrumento_gaita_1mao():
    room, p = _bardo_com_gaita()
    room._rolar_2d6 = lambda: 3          # Falha — sem efeito colateral
    p["fome"] = 10; p["sede"] = 10
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False     # 1 mão: ação livre p/ atacar
    assert p["fome"] == 7 and p["sede"] == 7   # custo 3/3 via _pagar_fome_sede

def test_end_turn_limpa_fila_improviso():
    room, p = _bardo_com_gaita()
    p["improviso_pendente"] = [{"res": 7, "tier": "padrao", "alvo_tipo": "monstro"}]
    # stub mínimo do resto do end_turn: ver nota abaixo
    room._limpar_improviso_pendente(p)   # helper isolado, chamado por handle_end_turn
    assert p.get("improviso_pendente") in (None, [])
```

> **Nota:** `handle_end_turn` é grande e faz muita coisa. Para testar sem montá-lo
> inteiro, extraia a limpeza num helper `_limpar_improviso_pendente(p)` e chame-o de
> dentro de `handle_end_turn`. O teste exercita o helper.

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: falha (dispatch de improviso ausente / helper ausente).

- [ ] **Step 3: Implementar**

Em `handle_usar_instrumento`, no bloco de dispatch por `tipo`, adicionar antes do `else`:

```python
        elif tipo == "improviso":
            ok = await self._instr_improviso(p, inst, st, data)
```

E trocar o débito do rodapé (linhas atuais `p["fome"] = max(0, p["fome"] - st["custo_fome"])`
/ `p["sede"] = …`) por:

```python
        self._pagar_fome_sede(p, st["custo_fome"], st["custo_sede"])
```

Adicionar o helper e chamá-lo em `handle_end_turn` (perto de onde outros flags de fim de
turno são resetados):

```python
    def _limpar_improviso_pendente(self, p):
        if p.get("improviso_pendente"):
            p["improviso_pendente"] = []
```

Em `handle_end_turn`, no ponto onde o jogador do turno é finalizado, chamar
`self._limpar_improviso_pendente(p)` para o jogador que encerra.

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: passa.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Gaita ligada ao handle_usar_instrumento + limpeza no end_turn"
```

---

## Task 8: Hooks de aura aceitam Gaita + Desafinado + Sinfonia temporária

**Files:**
- Modify: `server.py` (`_instr_ecos_retaliar`, `_bardo_dueto_marcial`,
  `_reacoes_instrumento_apos_ataque` [ramo Dueto Fantasma], `_sinfonia_bonus`,
  `_instrumento_cd`, `handle_attack` [ramo do bardo])
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_ecos_retalia_com_gaita():
    room, p = _bardo_com_gaita()
    p["ecos_ate"] = room.round_num; p["ecos_dano"] = "1d4"
    room._rolar_dano_mostrado = _make_dano(3)
    m = {"id": "m1", "name": "Orc", "hp": 10, "pos": [6, 5]}
    room.monsters = {"m1": m}
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 7     # retaliou mesmo com Gaita equipada

def test_sinfonia_temporaria_reforca_cancao():
    room, p = _bardo_com_gaita()
    p["sinfonia_temp_ate"] = room.round_num + 1
    p["sinfonia_temp_atributos"] = ["acerto"]
    p["buffs_cancao"] = {}
    assert room._sinfonia_bonus(p, "acerto") == 1
    assert room._sinfonia_bonus(p, "dano") == 0

def test_desafinado_reduz_cd():
    room, p = _bardo_com_gaita()
    cd_base = room._instrumento_cd(p, p["gear"]["off_hand"])
    p["desafinado_ate"] = room.round_num
    assert room._instrumento_cd(p, p["gear"]["off_hand"]) == cd_base - 1
```

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: falha.

- [ ] **Step 3: Implementar**

1. `_instr_ecos_retaliar` — trocar a checagem de base:
```python
        if not off or off.get("tipo_item") != "instrumento" or off.get("base") not in ("sino", "gaita"):
            return
```

2. `_bardo_dueto_marcial` — idem no `off.get("base")`:
```python
            if not off or off.get("tipo_item") != "instrumento" or off.get("base") not in ("lira", "gaita"):
                continue
```

3. `_reacoes_instrumento_apos_ataque` (ramo Dueto Fantasma) — trocar
   `self._instr_base_off(atacante) == "flauta"` por:
```python
           and self._instr_base_off(atacante) in ("flauta", "gaita") \
```

4. `_sinfonia_bonus` — somar o caminho temporário:
```python
    def _sinfonia_bonus(self, p, attr_id):
        inst = p.get("gear", {}).get("off_hand")
        if inst and inst.get("tipo_item") == "instrumento" and inst.get("base") == "alaude":
            st = self._instrumento_stats(inst)
            if attr_id in st.get("atributos", []):
                return 1
        if p.get("sinfonia_temp_ate", -1) >= self.round_num \
           and attr_id in p.get("sinfonia_temp_atributos", []):
            return 1
        return 0
```

5. `_instrumento_cd` — aplicar Desafinado. Localize o método (`def _instrumento_cd`)
   e no retorno subtraia 1 quando `p.get("desafinado_ate", -1) >= self.round_num`:
```python
        cd = 8 + _mod(p.get("dex", 10))   # (forma atual — confira)
        if p.get("desafinado_ate", -1) >= self.round_num:
            cd -= 1
        return cd
```

6. `handle_attack` — no ramo do atacante bardo, aplicar -1 à rolagem de ataque quando
   `desafinado_ate >= round_num`. Localize onde o `atk_bonus`/`eff_atk` do jogador é
   montado e some `-1` condicional. (Reuse o padrão do `acorde_atk_pen`/`_lenda_atk_bonus`
   já existentes para achar o ponto certo.)

> **`_sinfonia_bonus` é `@staticmethod` hoje?** Não — usa `self`. Confirme e mantenha
> como método de instância (precisa de `self.round_num`). O `_cancao_nivel_atributo`
> que o chama já passa `p`.

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: passa.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): hooks de aura aceitam Gaita + Desafinado + Sinfonia temporária"
```

---

## Task 9: Migrar débitos de custo para `_pagar_fome_sede` (ações ativas)

Migra **só os handlers de ação ativa** (conjuros/habilidades/instrumentos/técnicas/
armadilha) e as **manutenções** Canção/Réquiem. **Não** migra: custo de sobrevivência
de ataque, movimento, descanso na cidade, upkeep de venenos/chamas — não são "ações"
escolhidas com custo de habilidade.

**Handlers no escopo** (localizar o débito `p["fome"]=max(0,…)`/`p["sede"]=…` dentro de
cada um e trocar pela chamada ao helper):

| Handler | contexto |
|---|---|
| `handle_magia` (custo base E metamagia extra) | `"magia"` |
| `handle_cura`, `handle_cura_area` | — |
| `handle_purificacao`, `handle_ressurreicao` | — |
| `handle_imposicao_maos` | — |
| `handle_usar_tecnica` | — |
| `handle_criar_armadilha` | — |
| `_cobrar_manutencao_cancao`, `_cobrar_manutencao_requiem` | — |
| `handle_animar_mortos` (se cobrar 🍖/💧) | — |

(`handle_usar_instrumento` já foi migrado na Task 7.)

**Files:**
- Modify: `server.py` (os handlers acima)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste de regressão + de desconto (falhando)**

```python
def test_magia_gratis_via_encore(monkey=None):
    # Prova o desconto num handler migrado: cura do clérigo sob Grande Encore = custo 0.
    room, _p = _room_bardo()
    async def noop(*a, **k): pass
    room.gm_say = noop; room.send_to = noop; room.push_state = noop
    cl = {"id": "c1", "name": "Lewis", "class_id": "cleric", "alive": True,
          "pos": [5, 5], "fome": 10, "sede": 10, "int_": 12, "wis": 14,
          "gear": {k: None for k in server.GEAR_SLOTS}, "action_done": False,
          "buffs_cancao": {}, "grande_encore_ate": room.round_num}
    room.players["c1"] = cl
    room._is_turn = lambda pid: True
    # dispara a manutenção da canção (handler migrado) — deve custar 0 sob Grande Encore
    _run(room._cobrar_manutencao_cancao(cl))
    assert cl["fome"] == 10 and cl["sede"] == 10
```

> Este teste cobre um handler migrado de forma isolada (a manutenção da Canção). Não
> tente montar `handle_magia` inteiro no teste — a prova de que o helper aplica o
> desconto já está na Task 3; aqui só confirmamos que a **migração** roteia pelo helper.

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: `_cobrar_manutencao_cancao` ainda debita direto → falha.

- [ ] **Step 3: Implementar a migração**

Em cada handler do escopo, substituir o par de linhas de débito. Exemplos:

`_cobrar_manutencao_cancao` (procure `p["fome"] = max(0, p["fome"] - custo["fome"])`):
```python
        self._pagar_fome_sede(p, custo["fome"], custo["sede"])
```

`handle_magia` (o custo base 🍖-1/💧-1 e os extras de metamagia): rotear o débito final
pelo helper com `contexto="magia"`:
```python
        self._pagar_fome_sede(p, fome_total, sede_total, contexto="magia")
```
(Adapte aos nomes de variável locais reais — `total_fome`/`custo_extra_fome`/etc.
Junte num único débito por chamada quando possível; se houver dois débitos separados,
passe `contexto="magia"` só no primeiro para não consumir a carga de magia grátis duas
vezes.)

Repetir para cada handler da tabela. **Regra:** a checagem de suficiência
(`if p["fome"] < custo …`) deve usar `self._custo_fome_sede_efetivo(p, fome, sede, ctx)`
para não recusar uma ação que o Encore tornaria grátis.

- [ ] **Step 4: Rodar TODOS os testes do servidor + verificar passa**

Run:
```bash
python tools/test_instrumentos_bardo.py
python tools/test_bardo_espec.py
python tools/test_guilda.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
```
Expected: tudo passa (regressão dos custos existentes intacta quando não há Encore).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "refactor(custo): rotear débitos de ação por _pagar_fome_sede (habilita Encore)"
```

---

## Task 10: Aquisição — SKUs de loja + roller procedural

**Files:**
- Modify: `server.py` (`SHOP_MERCHANT` — SKUs; `_ROLLER_BASES`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Teste falhando**

```python
def test_gaita_no_roller():
    assert "gaita" in server._ROLLER_BASES

def test_gaita_sku_na_loja():
    ids = [it.get("id", "") for it in server.SHOP_MERCHANT.get("itens", server.SHOP_MERCHANT)
           if isinstance(it, dict)]
    assert any("gaita" in i for i in ids), ids
```

> Ajuste `test_gaita_sku_na_loja` à estrutura real de `SHOP_MERCHANT` (lista de SKUs
> geradas por `instrumento_sku(...)`). Veja como os SKUs da Fase 4 são declarados (linhas
> ~2460–2493) e espelhe.

- [ ] **Step 2: Rodar e verificar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: falha.

- [ ] **Step 3: Implementar**

`_ROLLER_BASES` (linha ~342): adicionar `"gaita"`:
```python
_ROLLER_BASES = ["harpa", "tambor", "sino", "alaude", "trompa", "lira", "flauta", "violino", "gaita"]
```

SKUs na lista de `instrumento_sku(...)` do `SHOP_MERCHANT` (junto dos demais instrumentos):
```python
    instrumento_sku("gaita", "velho",    90),
    instrumento_sku("gaita", "rustico",  170),
    instrumento_sku("gaita", "padrao",   300),
    instrumento_sku("gaita", "refinado", 420, refinado_bonus="fome"),
    instrumento_sku("gaita", "padrao",   480, encantamento="runico"),   # Rúnica (teste)
    instrumento_sku("gaita", "refinado", 1100, origem="ana", origem_bonus="fome_sede", encantamento="runico"),  # Lendária (teste)
```

- [ ] **Step 4: Rodar e verificar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: passa.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Gaita na loja + roller procedural"
```

---

## Task 11: Cliente — senders/getters + quadro do Improviso + fila de mira

O cliente reusa o botão de instrumento do HUD. Ao chegar `improviso_resultado`, mostra o
quadro da cascata e, se `pendentes > 0`, abre a mira em sequência.

**Files:**
- Modify: `src/gameState.js` (handler + senders)
- Modify: `game.js` (`acionarInstrumento`, quadro, fila de mira, tooltip)
- Modify: `game.css` (estilo do quadro — opcional, reusar `.status-banner`/modal existente)

- [ ] **Step 1: `gameState.js` — sender + evento**

Localize os senders de instrumento (`usarInstrumento`) e adicione:
```javascript
  improvisoAlvo(targetId, dir) {
    send({ type: "improviso_alvo", target_id: targetId || null, dir: dir || null });
  },
```
Registre o evento do servidor no roteador de mensagens (onde `game_state`/`dice_roll` são
tratados):
```javascript
      case "improviso_resultado":
        _emit("improviso_resultado", msg);
        break;
```
Exponha `improvisoAlvo` no objeto `GS` exportado (junto de `usarInstrumento`).

- [ ] **Step 2: `game.js` — disparar Improviso sem mira inicial**

Em `acionarInstrumento` (o handler do botão de instrumento do HUD), quando a base do
instrumento equipado for `"gaita"`, chamar `GS.usarInstrumento(null, null)` **sem** abrir
`openTargetModal` (a mira vem depois, via `improviso_resultado`). Para as outras bases,
o comportamento atual permanece.

- [ ] **Step 3: `game.js` — quadro + fila de mira**

Registrar `GS.on("improviso_resultado", renderImprovisoQuadro)`. `renderImprovisoQuadro(msg)`:
1. Monta um overlay simples (reusar o padrão de `#trap-overlay`/modal existente) listando
   `msg.cascata` (emoji + `nome`), com destaque se `msg.encore_menor`/`msg.grande_encore`.
2. Botão **OK** que fecha o quadro e, se `msg.pendentes > 0`, inicia a fila de mira: para
   cada pendente, o cliente sabe o tipo pelo próximo passo — como o servidor mantém a fila,
   o cliente pode simplesmente, ao clicar OK, começar a mirar o **primeiro** pendente e,
   a cada `game_state` recebido após um `improviso_alvo`, verificar se ainda há pendentes
   (`me.improviso_pendente?.length`) e reabrir a mira.
3. Mira por tipo: se o próximo pendente for `alvo_tipo:"monstro"` → `openTargetModal(...)`
   (monstro; ao escolher → `GS.improvisoAlvo(id)`); se `"direcao"` →
   `escolherDirecaoInstrumento(dir => GS.improvisoAlvo(null, dir))`.

> Para o cliente saber o `alvo_tipo` de cada pendente, inclua a lista completa no evento:
> troque, em `_instr_improviso` (server), `"pendentes": len(...)` por
> `"pendentes": [{"res": x["res"], "alvo_tipo": x["alvo_tipo"]} for x in p["improviso_pendente"]]`.
> Atualize o teste `test_improviso_enfileira_alvo` se necessário (ele checa `p[...]`, não o
> evento, então segue válido).

- [ ] **Step 4: Tooltip**

Em `_tooltipInstrumentoHTML`, adicionar um ramo para `base=="gaita"` descrevendo o
Improviso (rola 2d6 → habilidade de outro instrumento; 12 = Encore) e o custo.

- [ ] **Step 5: Verificação in-app (browser)**

Subir o servidor e verificar no preview:
- Equipar uma Gaita (comprar na loja), ativar o Improviso, ver o quadro aparecer.
- Rolar até cair num alvo (7/9/11) e confirmar que a mira abre e resolve.
- (Ver seção "Verificação" no handoff — usar as ferramentas do Browser pane.)

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js game.js game.css
git commit -m "feat(instrumentos): cliente do Improviso — quadro da cascata + fila de mira"
```

---

## Task 12: Documentação — CLAUDE.md + memória

**Files:**
- Modify: `CLAUDE.md` (bloco dos Instrumentos — adicionar a Fase 5)
- Modify: `C:\Users\RICARDO\.claude\projects\C--Users-RICARDO-Desktop-jogo-tabuleiro\memory\instrumentos-bardo-roadmap.md` e `MEMORY.md`

- [ ] **Step 1: CLAUDE.md**

Adicionar, após o bloco da Fase 4c, um parágrafo `> **Fase 5 (Improviso/Gaita):** …`
resumindo: base `gaita` (1 mão, Improviso), tabela 2d6 meta que invoca os outros
instrumentos no tier da Gaita, Encore (2 rerolls) / Encore Menor (2º 12, aura raio 5) /
Grande Encore (Rúnica, 3º 12, 1d4 rodadas sem custo sob a Canção), helper central
`_pagar_fome_sede`, protocolo `improviso_alvo`, e "fecha o roadmap dos instrumentos".
Atualizar a tabela do protocolo (`usar_instrumento` menciona a Gaita; adicionar
`improviso_alvo`).

- [ ] **Step 2: Memória**

Atualizar `instrumentos-bardo-roadmap.md`: marcar a Fase 5 como concluída/mergeada
(remover "só falta a Fase 5"). Ajustar o hook em `MEMORY.md`.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(instrumentos): documenta a Fase 5 (Improviso/Gaita) no CLAUDE.md"
```

(A memória fica fora do repo — salvar via Write, sem commit.)

---

## Task 13: Fechamento do branch

- [ ] Rodar a suíte de testes relevante uma última vez (Task 9, Step 4).
- [ ] Usar a skill `superpowers:finishing-a-development-branch` para decidir merge/PR.
- [ ] Atualizar a memória `guilda-especializacoes-roadmap`/`instrumentos-bardo-roadmap`
      conforme o desfecho (push pendente etc.).

---

## Self-review do plano (feito)

- **Cobertura do spec:** §2 base→T1; §3.1 tabela→T5/T6; §3.2 reuso→T5; §3.3 Encore→T2/T4;
  §3.4 estados/limpeza→T5/T7; §4 custo central→T3/T9; §5 protocolo→T5/T6/T7/T11;
  §5.3 Réquiem tick→T6; §6 hooks/Desafinado/Sinfonia→T8; §7 aquisição→T10; §8 cliente→T11;
  §9 testes→distribuídos; docs→T12. Sem lacunas.
- **Placeholders:** nenhum passo sem código; pontos "confirme a assinatura/estrutura real"
  são notas de verificação (o código-alvo existe), não placeholders de conteúdo.
- **Consistência de tipos:** `_improviso_rolar_cascata(runico)→(passos, meta)`,
  `_pagar_fome_sede(p,f,s,contexto=None)`, `_improviso_virt_st→(virt, st)`,
  `improviso_pendente=[{res,tier,alvo_tipo}]`, evento `improviso_resultado` e mensagem
  `improviso_alvo{target_id,dir}` — nomes usados de forma idêntica entre tarefas.
