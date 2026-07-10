# Instrumentos do Bardo — Fase 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao bardo (Henrique) um slot de instrumento musical que concede uma habilidade de assinatura escalável por qualidade, entregando o framework completo + 4 habilidades (Nota Cortante, Acorde Trovejante, Ecos Dolorosos, Sinfonia Heroica).

**Architecture:** Espelha o sistema de Técnicas da Guilda. Uma tabela-base autoritativa (`INSTRUMENTOS_BASE`) define cada instrumento; instâncias guardam só seus atributos (base/qualidade/origem/encantamento/afixos) e os números efetivos são derivados on-the-fly por `_instrumento_stats`. O instrumento vive num novo slot de gear `"instrumento"` (bard-only), e as habilidades ativadas são despachadas por `handle_usar_instrumento` (mensagem `usar_instrumento`), reusando a maquinaria de save/dano/empurrão/morte já existente. Origem/Encantamento ficam plumbados mas não populados (Fases 4+).

**Tech Stack:** Python (servidor WebSocket autoritativo, `server.py`), Vanilla JS (`src/gameState.js` estado, `game.js` render/HUD), testes `tools/test_*.py` (asserts puros contra o `GameRoom`, sem framework).

**Spec:** `docs/superpowers/specs/2026-07-10-instrumentos-bardo-fase1-design.md`

---

## Arquivos

| Arquivo | Responsabilidade | Ação |
|---|---|---|
| `server.py` | `INSTRUMENTOS_BASE`, `criar_instrumento`, `_instrumento_stats`, `_instrumento_nome`, `_instrumento_cd`, slot de gear, economia de ação, `handle_usar_instrumento` + efeitos, hook de Sinfonia na Canção, hook de Ecos no ataque de monstro, loja/loot, loadout de Henrique | Modify |
| `src/gameState.js` | Sender `usarInstrumento`, getters `instrumentoEquipado`/`instrumentoStatsCliente`/`instrumentoDisponivel` | Modify |
| `game.js` | Botão de instrumento no HUD do bardo + mira; slot de instrumento na ficha da cidade (só bardo) | Modify |
| `tools/test_instrumentos_bardo.py` | Testes do servidor (stats, economia de ação, 4 efeitos, bard-only, custo) | Create |

**Convenções reusadas (não reimplementar):**
- `roll_dice(die_str)` (linha ~55) — rola "NdM"/"N".
- `mod(score)` — modificador de atributo.
- `_distancia_chebyshev(a, b)` (~155) e `_no_raio(origem, alvo, raio)` (~7612).
- `_save_mostrado(alvo, tipo, dif) -> (passou, d20, bonus, total)` async (~10384). `tipo` ∈ `"reflexos"|"fortitude"|"vontade"`.
- `_rolar_dano_mostrado(n, faces, label)` async (~10364) — anima cada dado no cliente e devolve a soma.
- `_broadcast_dado(die, value, label)` async (~10361).
- `_empurrar(alvo, dx, dy, dist) -> bool_colidiu` (~10310).
- `_monster_dies(m, killer_pid)` async (~14812).
- `_dif_magia` padrão de CD: `8 + mod + ...` (~10392).
- `_cancao_nivel_atributo(p, attr_id)` (~7616) — hook da Sinfonia Heroica.
- `_slot_category_for_item(item)` (~8532), `GEAR_SLOTS` (~3541), `_equip_into_slot` (~8560), `_executar_equip_from_bag` (~8616).
- `gm_say(msg)` async — narração do GM.
- `usarTecnica` sender (client ~1223) como modelo de `usarInstrumento`.

---

## Task 1: Tabela-base, geração e derivação de stats

**Files:**
- Modify: `server.py` (inserir logo após o bloco `GUILD_CATALOG`/`CANCAO_ATRIBUTOS`, nível de módulo — perto da linha ~154, junto das outras constantes de topo; funções puras, sem `self`)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_instrumentos_bardo.py`:

```python
"""Testes do sistema de Instrumentos do Bardo — Fase 1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def test_stats_por_qualidade():
    # Harpa: velho 3q/1d4, rustico 4q/1d6, padrao 5q/2d6
    for q, alc, dano in [("velho", 3, "1d4"), ("rustico", 4, "1d6"), ("padrao", 5, "2d6")]:
        inst = server.criar_instrumento("harpa", q)
        st = server.GameRoom._instrumento_stats(inst)
        assert st["alcance"] == alc, (q, st)
        assert st["dano"] == dano, (q, st)
        assert st["custo_fome"] == 3 and st["custo_sede"] == 3, st

def test_refinado_afixo_alcance():
    inst = server.criar_instrumento("harpa", "refinado", refinado_bonus="alcance")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["alcance"] == 6, st          # padrao(5) + 1
    assert st["dano"] == "2d6", st

def test_refinado_afixo_custo_nunca_negativo():
    inst = server.criar_instrumento("sino", "refinado", refinado_bonus="fome")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["custo_fome"] == 1, st       # 2 - 1
    assert st["custo_sede"] == 2, st

def test_nome_derivado():
    assert server.criar_instrumento("harpa", "velho")["nome"] == "Harpa Velha"
    assert server.criar_instrumento("tambor", "padrao")["nome"] == "Tambor de Guerra Padrão"

def test_tipo_item_e_maos():
    inst = server.criar_instrumento("harpa", "padrao")
    assert inst["tipo_item"] == "instrumento"
    assert server.INSTRUMENTOS_BASE["harpa"]["maos"] == 2
    assert server.INSTRUMENTOS_BASE["sino"]["maos"] == 1

if __name__ == "__main__":
    import inspect
    fns = [f for n, f in sorted(globals().items()) if n.startswith("test_") and inspect.isfunction(f)]
    for f in fns:
        f(); print("ok", f.__name__)
    print(f"\n{len(fns)} testes passaram.")
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'criar_instrumento'` (ou `INSTRUMENTOS_BASE`).

- [ ] **Step 3: Implementar a tabela-base + geração + derivação**

Em `server.py`, logo após `CANCAO_ATRIBUTOS`/`_calcular_custo_cancao` (~linha 154), adicionar:

```python
# ─── INSTRUMENTOS DO BARDO (Fase 1) ─────────────────────────────────────────────
# Tabela-base autoritativa. Uma instância de instrumento guarda só seus atributos
# (base/qualidade/origem/encantamento/afixos); os números efetivos são derivados
# por GameRoom._instrumento_stats. Origem/Encantamento ficam plumbados p/ Fases 4+.
INSTRUMENTOS_BASE = {
    "harpa": {
        "nome": "Harpa", "icon": "🎵", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Nota Cortante",
        "efeito": {"tipo": "nota_cortante", "save": "reflexos"},
        "custo_fome": 3, "custo_sede": 3,
        "afixos_validos": ["fome", "sede", "alcance"],
        "stats": {
            "velho":   {"alcance": 3, "dano": "1d4"},
            "rustico": {"alcance": 4, "dano": "1d6"},
            "padrao":  {"alcance": 5, "dano": "2d6"},
        },
    },
    "tambor": {
        "nome": "Tambor de Guerra", "icon": "🥁", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Acorde Trovejante",
        "efeito": {"tipo": "acorde_trovejante", "save": "reflexos"},
        "custo_fome": 4, "custo_sede": 4,
        "afixos_validos": ["fome", "sede", "alcance"],   # "alcance" => +1 raio
        "stats": {
            "velho":   {"raio": 1, "dano": "1d2", "push": 0},
            "rustico": {"raio": 2, "dano": "1d4", "push": 1},
            "padrao":  {"raio": 2, "dano": "2d4", "push": 2},
        },
    },
    "sino": {
        "nome": "Sino", "icon": "🔔", "maos": 1, "modo": "ativada",
        "habilidade_nome": "Ecos Dolorosos",
        "efeito": {"tipo": "ecos_dolorosos"},
        "custo_fome": 2, "custo_sede": 2,
        "afixos_validos": ["fome", "sede", "duracao"],
        "stats": {
            "velho":   {"dano": "1",   "duracao": 2},
            "rustico": {"dano": "1d3", "duracao": 2},
            "padrao":  {"dano": "1d4", "duracao": 3},
        },
    },
    "alaude": {
        "nome": "Alaúde", "icon": "🪕", "maos": 2, "modo": "passiva",
        "habilidade_nome": "Sinfonia Heroica",
        "efeito": {"tipo": "sinfonia_heroica"},
        "custo_fome": 0, "custo_sede": 0,   # herda o custo da Canção Heroica
        "afixos_validos": ["fome", "sede"],
        "stats": {
            "velho":   {"atributos": ["acerto"]},
            "rustico": {"atributos": ["acerto", "dano"]},
            "padrao":  {"atributos": ["acerto", "dano", "ca", "movimento", "resistencia"]},
        },
    },
}

_QUALIDADE_LABEL = {  # (masculino, feminino) p/ nome derivado
    "velho": ("Velho", "Velha"), "rustico": ("Rústico", "Rústica"),
    "padrao": ("Padrão", "Padrão"), "refinado": ("Refinado", "Refinada"),
}
_INSTRUMENTO_GENERO_FEM = {"harpa", "trompa", "lira", "flauta", "gaita"}  # p/ concordância

def criar_instrumento(base, qualidade="padrao", origem="humana", encantamento="nenhum",
                      refinado_bonus=None, origem_bonus=None):
    """Cria uma instância de instrumento (item de bolsa/gear). base ∈ INSTRUMENTOS_BASE."""
    b = INSTRUMENTOS_BASE[base]
    inst = {
        "id": "instrumento", "tipo_item": "instrumento",
        "base": base, "qualidade": qualidade,
        "origem": origem, "encantamento": encantamento,
        "refinado_bonus": refinado_bonus if qualidade == "refinado" else None,
        "origem_bonus": origem_bonus if origem in ("elfica", "ana") else None,
        "icon": b["icon"], "allowed_classes": ["bard"],
    }
    inst["nome"] = _instrumento_nome(inst)
    return inst

def _instrumento_nome(inst):
    b = INSTRUMENTOS_BASE[inst["base"]]
    fem = inst["base"] in _INSTRUMENTO_GENERO_FEM
    ql = _QUALIDADE_LABEL.get(inst["qualidade"], ("Padrão", "Padrão"))[1 if fem else 0]
    return f"{b['nome']} {ql}"
```

Em seguida, os **métodos derivadores** dentro da classe `GameRoom` (junto dos demais helpers, ex. perto de `_cancao_nivel_atributo` ~7616). São `@staticmethod` porque não usam estado da sala, exceto `_instrumento_cd`:

```python
    @staticmethod
    def _instrumento_stats(inst):
        """Números efetivos de um instrumento: Qualidade → Refinado → Origem →
        Encantamento. Custos nunca < 0. (Origem/Encantamento são no-op na Fase 1.)"""
        b = INSTRUMENTOS_BASE[inst["base"]]
        q = "padrao" if inst["qualidade"] == "refinado" else inst["qualidade"]
        st = dict(b["stats"][q])                       # cópia do core
        st["custo_fome"] = b["custo_fome"]
        st["custo_sede"] = b["custo_sede"]
        st["save"] = b["efeito"].get("save")
        # Refinado: 1 afixo pré-rolado
        if inst["qualidade"] == "refinado":
            GameRoom._aplicar_afixo(st, inst.get("refinado_bonus"))
        # Origem (Fase 4): 1 afixo cultural — plumbado, sem valores na Fase 1
        if inst.get("origem_bonus"):
            GameRoom._aplicar_afixo(st, inst["origem_bonus"])
        st["custo_fome"] = max(0, st["custo_fome"])
        st["custo_sede"] = max(0, st["custo_sede"])
        return st

    @staticmethod
    def _aplicar_afixo(st, bonus):
        """Aplica um afixo 'Escolha 1' aos stats efetivos, se aplicável."""
        if bonus == "fome":
            st["custo_fome"] -= 1
        elif bonus == "sede":
            st["custo_sede"] -= 1
        elif bonus == "alcance":
            if "alcance" in st: st["alcance"] += 1
            if "raio" in st:    st["raio"] += 1
        elif bonus == "duracao":
            if "duracao" in st: st["duracao"] += 1
        elif bonus == "cd":
            st["cd_bonus"] = st.get("cd_bonus", 0) + 1   # somado em _instrumento_cd

    def _instrumento_cd(self, bardo, inst):
        """CD do save do instrumento: 8 + mod(DES) + afixo de CD (Élfica, Fase 4).
        DES porque é o atributo dos instrumentos do bardo (WEAPONS['instrumento'])."""
        st = self._instrumento_stats(inst)
        return 8 + mod(bardo.get("dex", 10)) + st.get("cd_bonus", 0)
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS (5 testes).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): tabela-base + criar_instrumento + _instrumento_stats/cd/nome"
```

---

## Task 2: Slot de gear `instrumento` (bard-only) + equipar

**Files:**
- Modify: `server.py` — `GEAR_SLOTS` (~3541); `_slot_category_for_item` (~8532); `_executar_equip_from_bag` (~8616); gear inicial (~3619)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao arquivo de teste um helper de sala + o teste de equipar. `criar_room_bardo()` monta um `GameRoom` mínimo em masmorra com o bardo no índice de turno.

```python
def _room_bardo():
    room = server.GameRoom.__new__(server.GameRoom)
    room.phase = "playing"
    room.round_num = 1
    room.turn_index = 0
    room.monsters = {}
    room.players = {}
    # bardo mínimo
    p = {
        "id": "p1", "name": "Henrique", "class_id": "bard", "alive": True,
        "pos": [5, 5], "dex": 16, "int_": 12, "spd": 6,
        "fome": 100, "sede": 100, "hp": 9, "max_hp": 9,
        "action_done": False, "instrumento_usado": False,
        "bag": [], "bag_size": 6,
        "gear": {k: None for k in server.GEAR_SLOTS},
        "moves_left": 6,
    }
    room.players["p1"] = p
    room.turn_order = ["p1"]
    return room, p

def test_slot_instrumento_existe():
    assert "instrumento" in server.GEAR_SLOTS

def test_slot_category_instrumento():
    inst = server.criar_instrumento("harpa", "padrao")
    assert server.GameRoom._slot_category_for_item(inst) == "instrumento"
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — `"instrumento" not in GEAR_SLOTS` / categoria devolve `"bag"`.

- [ ] **Step 3: Implementar o slot**

3a. `GEAR_SLOTS` (~3541) — adicionar `"instrumento"`:

```python
GEAR_SLOTS = ("weapon", "off_hand", "armor", "head", "boots", "ring1", "ring2", "item1", "item2", "instrumento")
```

3b. `_slot_category_for_item` (~8532) — no início, antes das outras checagens:

```python
        if s == "instrumento" or item.get("tipo_item") == "instrumento":
            return "instrumento"
```

3c. `_executar_equip_from_bag` (~8674, junto dos `elif cat == ...`) — adicionar antes do `else` final:

```python
        elif cat == "instrumento":
            if p.get("class_id") != "bard":
                await self.send_to(pid, {"type": "error",
                    "msg": "Apenas o bardo pode empunhar instrumentos musicais."})
                p["bag"].insert(slot_index, item)   # devolve à bolsa (já foi removido)
                return False
            log = self._equip_into_slot(p, item, "instrumento", "🎵")
```

> Nota: `_equip_into_slot` chama `_apply_gear_effect(p, item, True)`; instrumentos não
> têm `effect`, então é no-op — a habilidade é lida ao vivo do slot no combate.

3d. Gear inicial (~3619) — a construção do dict `"gear"` já usa slots nomeados; como não há mais um `{k: None}`, adicionar a linha do slot:

```python
            "item2":    None,                  # item ativo
            "instrumento": None,               # bardo: instrumento musical (Fase 1)
```

- [ ] **Step 4: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): slot de gear instrumento bard-only + equipar da bolsa"
```

---

## Task 3: Economia de ação + `handle_usar_instrumento` (esqueleto)

**Files:**
- Modify: `server.py` — novo handler `handle_usar_instrumento` (perto de `handle_usar_tecnica` ~4656); resetar `instrumento_usado` no início do turno; roteamento da mensagem `usar_instrumento`
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
import asyncio
def _run(coro): asyncio.get_event_loop().run_until_complete(coro)

def _mute(room):
    async def noop(*a, **k): return None
    room.gm_say = noop
    room.send_to = noop
    room.broadcast = noop
    room.push_state = noop
    room._broadcast_dado = noop

def test_economia_2maos_bloqueia_apos_acao():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "padrao")  # 2 mãos
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True,
         "ref_": 0, "ca": 10, "saves_base": {}}
    room.monsters["m1"] = m
    p["action_done"] = True                      # já atacou
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 20                          # nada aconteceu (bloqueado)

def test_economia_1mao_nao_gasta_acao_principal():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("sino", "padrao")   # 1 mão
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False             # ação principal continua livre

def test_um_instrumento_por_turno():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("sino", "padrao")
    _run(room.handle_usar_instrumento("p1", {}))
    fome_apos_1 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))  # 2ª vez no mesmo turno: recusa
    assert p["fome"] == fome_apos_1               # não debitou de novo
```

> `_is_turn` é usado pelo handler. Para o teste, adicionar ao `_room_bardo` um stub:
> após montar a sala, `room._is_turn = lambda pid: pid == "p1"`.

Adicionar essa linha em `_room_bardo` antes do `return`:

```python
    room._is_turn = lambda pid: pid == "p1"
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — `handle_usar_instrumento` não existe.

- [ ] **Step 3: Implementar o handler (esqueleto com economia de ação + custo)**

Perto de `handle_usar_tecnica` (~4656), adicionar. Os branches de efeito ficam nas Tasks 4–7; por ora só `nota_cortante`/`ecos_dolorosos` como stubs mínimos que os testes desta task exercitam (Sino ativa flag; Harpa checa economia). Implemento o dispatch completo aqui e as Tasks 4–7 preenchem os efeitos:

```python
    async def handle_usar_instrumento(self, pid, data=None):
        """Ativa a habilidade do instrumento equipado (bardo). Espelha
        handle_usar_tecnica: valida turno/economia de ação/custo 🍖💧 e despacha
        por efeito.tipo. Passivas (Alaúde) nunca chegam aqui."""
        if self.phase != "playing":
            return
        p = self.players.get(pid)
        if not p or not p.get("alive") or not self._is_turn(pid):
            await self.send_to(pid, {"type": "error", "msg": "Não é o seu turno."}); return
        if p.get("class_id") != "bard":
            await self.send_to(pid, {"type": "error", "msg": "Apenas o bardo usa instrumentos."}); return
        inst = p["gear"].get("instrumento")
        if not inst:
            await self.send_to(pid, {"type": "error", "msg": "Nenhum instrumento equipado."}); return
        base = INSTRUMENTOS_BASE[inst["base"]]
        if base["modo"] != "ativada":
            await self.send_to(pid, {"type": "error",
                "msg": f"{base['habilidade_nome']} é passiva — não precisa ativar."}); return
        # Economia de ação
        duas_maos = base["maos"] == 2
        if p.get("instrumento_usado"):
            await self.send_to(pid, {"type": "error",
                "msg": "Você já tocou um instrumento neste turno."}); return
        if duas_maos and p.get("action_done"):
            await self.send_to(pid, {"type": "error",
                "msg": "Instrumento de 2 mãos exige concentração — você já usou sua ação."}); return
        st = self._instrumento_stats(inst)
        if p.get("fome", 0) < st["custo_fome"] or p.get("sede", 0) < st["custo_sede"]:
            await self.send_to(pid, {"type": "error", "msg": "Fome/sede insuficientes."}); return

        # Despacho por efeito. Cada branch retorna sem tocar em custo/flags; a
        # cobrança acontece DEPOIS do sucesso (para não gastar em alvo inválido).
        tipo = base["efeito"]["tipo"]
        ok = False
        if tipo == "nota_cortante":
            ok = await self._instr_nota_cortante(p, inst, st, data)
        elif tipo == "acorde_trovejante":
            ok = await self._instr_acorde_trovejante(p, inst, st, data)
        elif tipo == "ecos_dolorosos":
            ok = await self._instr_ecos_dolorosos(p, inst, st, data)
        else:
            await self.send_to(pid, {"type": "error", "msg": "Instrumento em desenvolvimento."}); return
        if not ok:
            return   # erro já enviado pelo branch (alvo inválido/fora de alcance)

        # Cobra custo + marca economia de ação
        p["fome"] = max(0, p["fome"] - st["custo_fome"])
        p["sede"] = max(0, p["sede"] - st["custo_sede"])
        p["instrumento_usado"] = True
        if duas_maos:
            p["action_done"] = True
        await self.push_state()
```

Stubs mínimos para os testes desta task (as Tasks 4–7 substituem pelo corpo real):

```python
    async def _instr_nota_cortante(self, p, inst, st, data):
        return False   # implementado na Task 4

    async def _instr_acorde_trovejante(self, p, inst, st, data):
        return False   # implementado na Task 5

    async def _instr_ecos_dolorosos(self, p, inst, st, data):
        return True    # Task 6 implementa a aura; por ora só consome o custo
```

Reset de `instrumento_usado`: localizar onde `action_done`/`bonus_action_used` são
resetados no início do turno (buscar por `"action_done"] = False` no fluxo de troca
de turno — mesmo ponto que zera `moves_left`). Adicionar ao lado:

```python
            p["instrumento_usado"] = False
```

> Buscar: `grep -n 'action_done"\] = False' server.py` — há o ponto de reset de
> turno (não a criação do jogador). Adicionar a linha no MESMO bloco de reset.

- [ ] **Step 4: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS. (Harpa bloqueia após `action_done`; Sino não gasta ação principal; 2º uso recusado.)

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): handle_usar_instrumento + economia de acao (1h/2h, 1 por turno)"
```

---

## Task 4: Efeito Nota Cortante (Harpa, 2 mãos)

**Files:**
- Modify: `server.py` — corpo de `_instr_nota_cortante`
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_nota_cortante_dano_e_alcance():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "padrao")  # 5q, 2d6
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [8, 5], "alive": True,
         "ref_": -50}   # ref_ muito baixo → falha o save → dano cheio
    room.monsters["m1"] = m
    # força save falho e dano determinístico
    room._testar_save = lambda alvo, tipo, dif, **k: (False, 1, 0, 1)
    server.roll_dice_orig = server.roll_dice
    server.roll_dice = lambda s: 10 if s == "2d6" else server.roll_dice_orig(s)
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    server.roll_dice = server.roll_dice_orig
    assert m["hp"] == 20, m["hp"]            # 30 - 10 (dano cheio)

def test_nota_cortante_meia_no_sucesso():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True, "ref_": 50}
    room.monsters["m1"] = m
    room._testar_save = lambda alvo, tipo, dif, **k: (True, 20, 0, 20)  # passa
    server.roll_dice_orig = server.roll_dice
    server.roll_dice = lambda s: 10 if s == "2d6" else server.roll_dice_orig(s)
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    server.roll_dice = server.roll_dice_orig
    assert m["hp"] == 25, m["hp"]            # 30 - 5 (metade)

def test_nota_cortante_fora_de_alcance_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("harpa", "velho")   # 3q
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [10, 5], "alive": True, "ref_": 0}
    room.monsters["m1"] = m
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert m["hp"] == 30 and p["fome"] == fome0   # nada aconteceu, sem custo
```

> Os testes usam `_save_mostrado` internamente; como o handler chama `_save_mostrado`
> (async, que chama `_testar_save`), stubar `room._save_mostrado` diretamente é mais
> simples. Ajustar os stubs para: `room._save_mostrado = async lambda...`. Como
> lambdas não podem ser async, definir no teste:
> ```python
> async def _save_falha(*a, **k): return (False, 1, 0, 1)
> async def _save_passa(*a, **k): return (True, 20, 0, 20)
> ```
> e atribuir `room._save_mostrado = _save_falha` / `_save_passa`. Também stubar
> `room._rolar_dano_mostrado` para retorno determinístico em vez de mexer em
> `roll_dice`:
> ```python
> async def _dano10(n, faces, label): return 10
> room._rolar_dano_mostrado = _dano10
> ```
> Reescrever os dois primeiros testes usando esses stubs (dano fixo 10 → cheio 10 /
> metade 5). Remover a manipulação de `server.roll_dice`.

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — `_instr_nota_cortante` devolve `False` (stub) → alvo intacto quando deveria sofrer dano.

- [ ] **Step 3: Implementar Nota Cortante**

Substituir o stub por:

```python
    async def _instr_nota_cortante(self, p, inst, st, data):
        """Alvo único até `alcance` casas; dano sonoro; save de Reflexos → metade."""
        alvo_id = (data or {}).get("target_id")
        m = self.monsters.get(alvo_id)
        if not m or m.get("hp", 0) <= 0:
            await self.send_to(p["id"], {"type": "error", "msg": "Alvo inválido."}); return False
        if self._distancia_chebyshev(p["pos"], m["pos"]) > st["alcance"]:
            await self.send_to(p["id"], {"type": "error",
                "msg": f"Alvo fora do alcance ({st['alcance']} casas)."}); return False
        await self.gm_say(f"🎵 **{p['name']}** dispara **Nota Cortante** em **{m['name']}**!")
        dano = await self._rolar_dano_mostrado(*_ndfaces(st["dano"]), "🎵 Dano sonoro")
        save_ok, *_ = await self._save_mostrado(m, "reflexos", self._instrumento_cd(p, inst))
        if save_ok:
            dano = dano // 2
        m["hp"] = max(0, m["hp"] - dano)
        await self.gm_say(f"🎵 **{m['name']}** sofre **{dano}** de dano sonoro"
                          f"{' (metade — resistiu)' if save_ok else ''}.")
        if m["hp"] <= 0:
            await self._monster_dies(m, p["id"])
        return True
```

Adicionar o helper de parsing de dado (nível de módulo, perto de `roll_dice`):

```python
def _ndfaces(die_str):
    """'2d6' -> (2, 6); '1' -> (1, 1) (dano fixo de 1 ponto)."""
    if "d" not in die_str:
        return (int(die_str), 1)
    n, faces = die_str.split("d")
    return (int(n or 1), int(faces))
```

> `_rolar_dano_mostrado(1, 1, ...)` soma um "d1" (sempre 1) → dano fixo de 1, usado
> pelo Sino Velho ("dano": "1"). Correto.

- [ ] **Step 4: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Nota Cortante (Harpa) — alvo unico, save Reflexos meia"
```

---

## Task 5: Efeito Acorde Trovejante (Tambor, 2 mãos, AoE)

**Files:**
- Modify: `server.py` — corpo de `_instr_acorde_trovejante`
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_acorde_aoe_falha_empurra():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["instrumento"] = server.criar_instrumento("tambor", "padrao")  # raio2, 2d4, push2
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True}  # dentro do raio
    far = {"id": "m2", "name": "Ogro", "hp": 30, "pos": [12, 5], "alive": True} # fora
    room.monsters = {"m1": m, "m2": far}
    async def _save_falha(*a, **k): return (False, 1, 0, 1)
    async def _dano8(n, faces, label): return 8
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano8
    empurrados = []
    room._empurrar = lambda alvo, dx, dy, dist: empurrados.append((alvo["id"], dx, dy, dist)) or False
    _run(room.handle_usar_instrumento("p1", {}))
    assert m["hp"] == 22          # 30 - 8 (cheio)
    assert far["hp"] == 30        # fora do raio, intacto
    assert ("m1", 1, 0, 2) in empurrados   # empurrado 2 casas para longe (+x)

def test_acorde_sucesso_meia_sem_empurrao():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("tambor", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters = {"m1": m}
    async def _save_passa(*a, **k): return (True, 20, 0, 20)
    async def _dano8(n, faces, label): return 8
    room._save_mostrado = _save_passa
    room._rolar_dano_mostrado = _dano8
    room._empurrar = lambda *a: (_ for _ in ()).throw(AssertionError("não deveria empurrar"))
    _run(room.handle_usar_instrumento("p1", {}))
    assert m["hp"] == 26          # 30 - 4 (metade)
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — stub devolve False.

- [ ] **Step 3: Implementar Acorde Trovejante**

```python
    async def _instr_acorde_trovejante(self, p, inst, st, data):
        """AoE centrada no bardo (raio Chebyshev). Falha: dano cheio + empurrão;
        sucesso: metade, sem empurrão. push=0 → -1 movimento no lugar do empurrão."""
        alvos = [m for m in self.monsters.values()
                 if m.get("hp", 0) > 0 and self._no_raio(p, m, st["raio"])]
        if not alvos:
            await self.send_to(p["id"], {"type": "error", "msg": "Nenhum inimigo no alcance."}); return False
        await self.gm_say(f"🥁 **{p['name']}** golpeia o **Tambor de Guerra** — onda sonora (raio {st['raio']})!")
        cd = self._instrumento_cd(p, inst)
        for m in alvos:
            dano = await self._rolar_dano_mostrado(*_ndfaces(st["dano"]), "🥁 Dano sonoro")
            save_ok, *_ = await self._save_mostrado(m, "reflexos", cd)
            if save_ok:
                dano = dano // 2
            m["hp"] = max(0, m["hp"] - dano)
            if not save_ok:
                if st.get("push", 0) > 0:
                    dx = (m["pos"][0] > p["pos"][0]) - (m["pos"][0] < p["pos"][0])
                    dy = (m["pos"][1] > p["pos"][1]) - (m["pos"][1] < p["pos"][1])
                    self._empurrar(m, dx, dy, st["push"])
                else:
                    m["mov_pen_val"] = 1
                    m["mov_pen_ate"] = self.round_num + 1
            await self.gm_say(f"🥁 **{m['name']}** sofre **{dano}**"
                              f"{' (metade)' if save_ok else ''}.")
            if m["hp"] <= 0:
                await self._monster_dies(m, p["id"])
        return True
```

> `mov_pen_val`/`mov_pen_ate` (push=0 do Tambor Velho): campo novo, aplicado só a
> monstros. Para a Fase 1 basta gravá-lo; a leitura no cálculo de movimento do
> monstro é opcional (o Tambor Velho é fraco por design). Se o loop de movimento de
> monstro já suportar uma penalidade de mov, plugar ali; senão, deixar gravado
> (não quebra nada). Documentar essa lacuna no CLAUDE.md ao final.

- [ ] **Step 4: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Acorde Trovejante (Tambor) — AoE save + empurrao"
```

---

## Task 6: Efeito Ecos Dolorosos (Sino, 1 mão, aura de retaliação)

**Files:**
- Modify: `server.py` — corpo de `_instr_ecos_dolorosos` + hook no ataque de monstro vs jogador
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Localizar o site de dano de ataque de monstro vs jogador**

Run: `grep -n '_execute_one_monster_attack\|def _monstro_ataca\|hp"\] -= ' server.py` para achar onde o dano do ataque de monstro é aplicado ao jogador. Anotar o(s) ponto(s) — é lá que o Ecos retalia (mesmo padrão do `_execute_one_monster_attack` citado no CLAUDE.md para Defesa Impecável/Contra-Ataque).

- [ ] **Step 2: Escrever os testes que falham**

```python
def test_ecos_ativa_aura():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["instrumento"] = server.criar_instrumento("sino", "padrao")  # 1d4, dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["ecos_ate"] == room.round_num + 3
    assert p["ecos_dano"] == "1d4"
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False   # 1 mão: pode atacar depois

def test_ecos_retaliacao():
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num + 2
    p["ecos_dano"] = "1d4"
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    room.monsters["m1"] = m
    async def _dano3(n, faces, label): return 3
    room._rolar_dano_mostrado = _dano3
    _run(room._instr_ecos_retaliar(p, m))     # helper de retaliação
    assert m["hp"] == 17

def test_ecos_expira():
    room, p = _room_bardo(); _mute(room)
    p["ecos_ate"] = room.round_num - 1        # já expirou
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True}
    _run(room._instr_ecos_retaliar(p, m))
    assert m["hp"] == 20                       # sem retaliação
```

- [ ] **Step 3: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — `ecos_ate` não setado / `_instr_ecos_retaliar` não existe.

- [ ] **Step 4: Implementar Ecos**

Corpo real (substitui o stub `return True` da Task 3):

```python
    async def _instr_ecos_dolorosos(self, p, inst, st, data):
        """Ativa a aura de retaliação por `duracao` rodadas. Enquanto ativa, todo
        monstro que acertar o bardo em corpo a corpo sofre `dano` sonoro."""
        p["ecos_ate"] = self.round_num + st["duracao"]
        p["ecos_dano"] = st["dano"]
        await self.gm_say(f"🔔 **{p['name']}** faz o **Sino** ressoar — "
                          f"ecos dolorosos por {st['duracao']} rodada(s)!")
        return True

    async def _instr_ecos_retaliar(self, p, m):
        """Aplica a retaliação de Ecos a um monstro que acabou de acertar o bardo."""
        if p.get("ecos_ate", 0) < self.round_num:
            return
        if m.get("hp", 0) <= 0:
            return
        dano = await self._rolar_dano_mostrado(*_ndfaces(p.get("ecos_dano", "1d4")), "🔔 Ecos")
        m["hp"] = max(0, m["hp"] - dano)
        await self.gm_say(f"🔔 Os Ecos Dolorosos ferem **{m['name']}** em **{dano}**!")
        if m["hp"] <= 0:
            await self._monster_dies(m, p["id"])
```

- [ ] **Step 5: Ligar o hook no ataque de monstro**

No(s) ponto(s) achados no Step 1, DEPOIS de o dano do monstro `m` ser aplicado a um
jogador `alvo` num ataque corpo a corpo bem-sucedido, adicionar:

```python
                if alvo.get("class_id") == "bard" and alvo.get("ecos_ate", 0) >= self.round_num:
                    await self._instr_ecos_retaliar(alvo, m)
```

> Usar os nomes de variável reais do site (o alvo-jogador e o monstro atacante).
> Só corpo a corpo: se o site distinguir melee/ranged, condicionar ao ramo melee.

- [ ] **Step 6: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Ecos Dolorosos (Sino) — aura de retaliacao no ataque melee"
```

---

## Task 7: Sinfonia Heroica (Alaúde, passiva, hook na Canção)

**Files:**
- Modify: `server.py` — `_cancao_nivel_atributo` (~7616)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_sinfonia_boost_por_qualidade():
    room, p = _room_bardo(); _mute(room)
    # sem alaúde: nível base 1 (sem espec de guilda)
    p["guild_owned"] = {"especializacoes": [], "tecnicas": []}
    assert room._cancao_nivel_atributo(p, "acerto") == 1
    # Alaúde Velho: só "acerto" ganha +1
    p["gear"]["instrumento"] = server.criar_instrumento("alaude", "velho")
    assert room._cancao_nivel_atributo(p, "acerto") == 2
    assert room._cancao_nivel_atributo(p, "dano") == 1
    # Alaúde Padrão: todos os 5 ganham +1
    p["gear"]["instrumento"] = server.criar_instrumento("alaude", "padrao")
    for a in ("acerto", "dano", "ca", "movimento", "resistencia"):
        assert room._cancao_nivel_atributo(p, a) == 2, a

def test_sinfonia_empilha_com_espec():
    room, p = _room_bardo(); _mute(room)
    # espec de guilda dá base 2; Alaúde soma +1 → 3
    p["guild_owned"] = {"especializacoes": ["bardo_cancao_acerto"], "tecnicas": []}
    p["gear"]["instrumento"] = server.criar_instrumento("alaude", "padrao")
    assert room._cancao_nivel_atributo(p, "acerto") == 3
```

> `tem_espec(p, "bardo_cancao_acerto")` lê de `p["guild_owned"]["especializacoes"]`.
> Confirmar a chave real com `grep -n 'def tem_espec' server.py`; ajustar o stub do
> jogador se necessário.

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — Alaúde não afeta o nível.

- [ ] **Step 3: Implementar o hook**

`_cancao_nivel_atributo` (~7616) passa a somar o boost do Alaúde equipado:

```python
    def _cancao_nivel_atributo(self, p, attr_id):
        """Bônus daquele atributo na Canção: 2 se comprado na Guilda (senão 1),
        +1 se o bardo empunha um Alaúde cuja Sinfonia Heroica cobre esse atributo."""
        base = 2 if tem_espec(p, f"bardo_cancao_{attr_id}") else 1
        base += self._sinfonia_bonus(p, attr_id)
        return base

    def _sinfonia_bonus(self, p, attr_id):
        """+1 se um Alaúde equipado inclui `attr_id` na Sinfonia Heroica (por qualidade)."""
        inst = p.get("gear", {}).get("instrumento")
        if not inst or inst.get("base") != "alaude":
            return 0
        st = self._instrumento_stats(inst)
        return 1 if attr_id in st.get("atributos", []) else 0
```

- [ ] **Step 4: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Sinfonia Heroica (Alaude) — +1 nos atributos da Cancao por qualidade"
```

---

## Task 8: Aquisição (loja + loot) e roteamento de item

**Files:**
- Modify: `server.py` — catálogo da loja (`handle_shop_buy`/SHOP), `_route_acquired_item`/`_slot_category_for_item` (já cobre `tipo_item`); permitir instrumento em baú/recompensa
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Localizar o catálogo da loja**

Run: `grep -n 'SHOP\|def handle_shop_buy\|shop_item\|def _route_acquired_item' server.py`.
Identificar a estrutura de catálogo da loja (dict de itens por `shop_id`/`item_id`).

- [ ] **Step 2: Escrever o teste que falha**

```python
def test_instrumento_roteia_para_bolsa():
    room, p = _room_bardo(); _mute(room)
    inst = server.criar_instrumento("harpa", "rustico")
    res = room._route_acquired_item(p, inst)
    assert res == "bag"
    assert inst in p["bag"]
    assert p["gear"]["instrumento"] is None    # NÃO auto-equipa

def test_instrumento_loja_gera_instancia():
    # o SKU de loja precisa produzir uma instância válida de instrumento
    sku = server.instrumento_sku("harpa", "rustico", preco=120)
    assert sku["tipo_item"] == "instrumento"
    assert sku["buy_price"] == 120
    assert sku["allowed_classes"] == ["bard"]
```

- [ ] **Step 3: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — `instrumento_sku` não existe; possivelmente `_route_acquired_item` não reconhece a categoria (deve, via `tipo_item`; se auto-equipar, ajustar).

- [ ] **Step 4: Implementar SKU de loja + entradas + roteamento**

4a. Helper de SKU (nível de módulo, perto de `criar_instrumento`):

```python
def instrumento_sku(base, qualidade="padrao", preco=100, refinado_bonus=None):
    """Instância de instrumento para venda na loja (com buy_price)."""
    inst = criar_instrumento(base, qualidade, refinado_bonus=refinado_bonus)
    inst["buy_price"] = preco
    return inst
```

4b. Adicionar entradas ao catálogo da loja (usar a estrutura real achada no Step 1).
Preços por qualidade (Fase 1, todas Humanas/sem encantamento):

```python
    # Instrumentos do bardo (Fase 1) — loja da cidade
    instrumento_sku("harpa",  "velho",   preco=60),
    instrumento_sku("harpa",  "rustico", preco=120),
    instrumento_sku("harpa",  "padrao",  preco=220),
    instrumento_sku("tambor", "rustico", preco=140),
    instrumento_sku("tambor", "padrao",  preco=240),
    instrumento_sku("sino",   "rustico", preco=90),
    instrumento_sku("sino",   "padrao",  preco=160),
    instrumento_sku("alaude", "rustico", preco=130),
    instrumento_sku("alaude", "padrao",  preco=230),
    instrumento_sku("harpa",  "refinado", preco=320, refinado_bonus="alcance"),
```

> Encaixar no formato exato do catálogo existente (chave por `id`? lista?). Se a loja
> indexa por `item_id` único e todos os instrumentos têm `id == "instrumento"`, dar um
> `id` único ao SKU (ex. `f"instrumento_{base}_{qualidade}"`) preservando
> `tipo_item == "instrumento"` e `base`. `_slot_category_for_item` usa `tipo_item`,
> não `id`, então isso é seguro. Ajustar `instrumento_sku` para setar
> `inst["id"] = f"instrumento_{base}_{qualidade}"` se a loja exigir id único.

4c. Roteamento: confirmar que `_route_acquired_item` manda instrumentos para a bolsa
(sem auto-equipar). Localizar o passo de "resgate-equipa" e garantir que a categoria
`instrumento` **não** entre nele (ou entre só para bardo). O caminho mais simples:
no início de `_route_acquired_item`, se `item.get("tipo_item") == "instrumento"`,
forçar rota de bolsa:

```python
        if item.get("tipo_item") == "instrumento":
            if len(p["bag"]) < p.get("bag_size", 6):
                p["bag"].append(item); return "bag"
            return "full"
```

- [ ] **Step 5: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): SKUs de loja + roteamento bolsa-primeiro (loot reusa item pipeline)"
```

---

## Task 9: Loadout inicial de Henrique (arma real + Alaúde Velho)

**Files:**
- Modify: `server.py` — CLASSES bard `weapon` (~1025); gear inicial do bardo (~3619)
- Test: `tools/test_instrumentos_bardo.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
def test_loadout_inicial_henrique():
    p = server.criar_player("p1", "Henrique", "bard", slot=0)  # assinatura real: ver grep
    # arma real (com die), não mais o "instrumento" sem dano
    assert p["gear"]["weapon"].get("id") != "instrumento"
    assert p["weapon"].get("die")                    # arma de dano
    # Alaúde Velho no slot de instrumento
    inst = p["gear"]["instrumento"]
    assert inst and inst["base"] == "alaude" and inst["qualidade"] == "velho"
```

> Confirmar a assinatura real da fábrica de jogador: `grep -n 'def criar_player\|def make_player\|def _novo_jogador' server.py` e ajustar a chamada do teste.

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_instrumentos_bardo.py`
Expected: FAIL — weapon ainda é "instrumento"; slot de instrumento vazio.

- [ ] **Step 3: Implementar o loadout**

3a. CLASSES bard (~1025): trocar a arma inicial de dano. Henrique já tinha a adaga
como 2ª mão; agora a adaga (real, 1d4 finesse/dex) vira a arma principal:

```python
        "ac_base": 13, "weapon": "dagger", "atk_bonus": 3,   # arma real (adaga) na mão principal; instrumento vai p/ o slot próprio
```

3b. Gear inicial (~3619): após montar o dict de gear, para o bardo, colocar o
Alaúde Velho no slot de instrumento. Localizar onde `_STARTING_OFFHAND`/gear por
classe é resolvido e adicionar (logo antes do `return {...}` de `criar_player`, ou
no ponto onde class-specific gear é ajustado):

```python
    if cls_id == "bard":
        gear_dict["instrumento"] = criar_instrumento("alaude", "velho")
```

> Se o gear é construído inline dentro do dict de `return`, extrair para uma var
> `gear_dict` antes do `return` e referenciá-la (`"gear": gear_dict`). Ajustar o
> `off_hand` inicial do bardo se ele ainda apontar para a adaga (evitar duas adagas):
> deixar `off_hand` livre (`None`) ou manter a 2ª adaga (dual-wield) — decisão de
> sabor; o padrão é deixar como está (2ª adaga) já que não conflita.

- [ ] **Step 4: Rodar e confirmar passa**

Run: `python tools/test_instrumentos_bardo.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): loadout inicial de Henrique (adaga real + Alaude Velho)"
```

---

## Task 10: Cliente — sender + getters + roteamento da mensagem

**Files:**
- Modify: `src/gameState.js` — sender `usarInstrumento`, getters, export
- Modify: `server.py` — rotear `usar_instrumento` no dispatcher de mensagens WebSocket

- [ ] **Step 1: Rotear a mensagem no servidor**

Run: `grep -n "'usar_tecnica'\|\"usar_tecnica\"\|msg\[.type.\]" server.py` para achar o
dispatcher (onde cada `type` chama seu handler). Adicionar ao lado do `usar_tecnica`:

```python
        elif t == "usar_instrumento":
            await self.handle_usar_instrumento(pid, data)
```

> Usar a forma exata do dispatcher (if/elif por `t`/`msg_type`, ou dict de handlers).

- [ ] **Step 2: Adicionar sender + getters no cliente**

Em `src/gameState.js`, perto de `usarTecnica` (~1223):

```javascript
  function usarInstrumento(target)   { send({ type: 'usar_instrumento', target_id: (target && target.id != null) ? target.id : null }); }

  // Instrumento equipado do jogador (lido do game_state; cidade usa cityState).
  function instrumentoEquipadoDe(pid) {
    const src = gameState || cityState;
    const gp = (src && src.players || []).find(p => p.id === pid);
    return (gp && gp.gear && gp.gear.instrumento) || null;
  }
  // Disponível para ativar neste turno? (só ativada; respeita economia de ação)
  function instrumentoDisponivel(player) {
    const inst = player && player.gear && player.gear.instrumento;
    if (!inst) return false;
    const base = (instrumentoBaseCache && instrumentoBaseCache[inst.base]) || null;
    if (!base || base.modo !== 'ativada') return false;
    if (player.instrumento_usado) return false;
    if (base.maos === 2 && player.action_done) return false;
    return true;
  }
```

> `instrumentoBaseCache`: o cliente precisa dos metadados de `INSTRUMENTOS_BASE`
> (nome/mãos/modo/ícone) para rótulos e economia de ação. Exportar `INSTRUMENTOS_BASE`
> do servidor no `game_state` (ou no `game_start`) uma vez, como já se faz com o
> catálogo da Guilda. Adicionar no servidor: incluir
> `"instrumentos_base": {k: {campos leves} for ...}` no payload inicial e cachear no
> cliente em `instrumentoBaseCache` (espelho de `guildCatalogCache`). Campos leves:
> `nome, icon, maos, modo, habilidade_nome`.

Exportar no objeto retornado (junto de `usarTecnica`):

```javascript
    usarInstrumento,
    instrumentoEquipadoDe,
    instrumentoDisponivel,
```

- [ ] **Step 3: Verificar carregamento (sem erro de sintaxe)**

Run: `python -c "print('sintaxe do servidor ok')" && node --check src/gameState.js`
Expected: sem erros. (Se `node` indisponível, abrir o jogo e conferir o console.)

- [ ] **Step 4: Commit**

```bash
git add src/gameState.js server.py
git commit -m "feat(instrumentos): cliente — sender usarInstrumento + getters + roteamento da mensagem"
```

---

## Task 11: Cliente — botão no HUD do bardo + mira + slot na ficha

**Files:**
- Modify: `game.js` — botão de instrumento no painel do bardo; mira (target modal p/ Nota Cortante; auto p/ Acorde/Ecos); slot de instrumento na ficha da cidade
- **IMPORTANTE:** editar `game.js` SEMPRE via ferramenta Edit (nunca PowerShell — ver memória do projeto)

- [ ] **Step 1: Localizar os padrões existentes**

Run (via Grep tool): botão de técnica no HUD (`usarTecnica`, `openTargetModal`), render
dos slots de gear na ficha da cidade (`renderFichaCidadeBody`/`_fcDropOnGear`), e o
painel de habilidades do bardo (`cancao`, `provocacao`).

- [ ] **Step 2: Adicionar o botão de instrumento no painel do bardo**

No render do HUD do bardo (onde ficam os botões de Canção/Provocação), adicionar um
botão condicionado a ter instrumento ATIVADO equipado. Código (padrão dos outros
botões; `GS` é o módulo de estado):

```javascript
  const inst = me.gear && me.gear.instrumento;
  const base = inst && INSTRUMENTOS_BASE_CLIENT[inst.base];
  if (base && base.modo === 'ativada') {
    const st = instrumentoStatsClient(inst);           // espelho leve p/ rótulo
    const disponivel = GS.instrumentoDisponivel(me);
    const btn = el('button', {
      class: 'skill-btn' + (disponivel ? '' : ' disabled'),
      disabled: !disponivel,
      title: `${base.habilidade_nome} — 🍖${st.custo_fome} 💧${st.custo_sede}`,
      onclick: () => acionarInstrumento(inst, base),
    }, `${base.icon} ${base.habilidade_nome}`);
    painel.appendChild(btn);
  }
```

`acionarInstrumento` escolhe a mira conforme o efeito:

```javascript
  function acionarInstrumento(inst, base) {
    const tipo = base.efeito_tipo;   // exportado no payload leve
    if (tipo === 'nota_cortante') {
      // mira em 1 monstro dentro do alcance (reusa o modal de alvo existente)
      openTargetModal({
        filtro: 'monstro',
        onPick: (alvo) => GS.usarInstrumento(alvo),
      });
    } else {
      // Acorde (AoE ao redor) e Ecos (self) não precisam de alvo
      GS.usarInstrumento(null);
    }
  }
```

> Ajustar `openTargetModal` à assinatura real (ver Step 1). `INSTRUMENTOS_BASE_CLIENT`
> e `instrumentoStatsClient` são o cache/espelho leve introduzido na Task 10 (renomear
> para o nome usado lá). `efeito_tipo` deve estar no payload leve — incluí-lo.

- [ ] **Step 3: Slot de instrumento na ficha da cidade (só bardo)**

No render dos slots de gear da ficha (`renderFichaCidadeBody`), adicionar um slot
`instrumento` **apenas quando `player.class_id === 'bard'`**, reusando o mesmo
componente/drag-drop dos outros slots (`_fcDropOnGear` já roteia por
`_slot_category_for_item` no servidor, que agora devolve `instrumento`):

```javascript
    if (player.class_id === 'bard') {
      slots.push(renderGearSlot('instrumento', '🎵 Instrumento', player.gear.instrumento));
    }
```

> Usar o helper real de render de slot (ver Step 1). O equipar por arrastar já
> funciona: arrastar um instrumento da bolsa para o slot dispara o equip existente,
> que o servidor valida (bard-only) na Task 2.

- [ ] **Step 4: Verificação no jogo (preview)**

Subir o servidor e abrir o preview:
- `mcp__Claude_Browser__preview_start` com `.claude/launch.json` (ou `python server.py`).
- Criar sala, escolher Henrique, entrar na masmorra.
- Confirmar: botão "🪕 Sinfonia Heroica" NÃO aparece (Alaúde é passiva); comprar/lootar
  uma Harpa, equipar pela ficha, ver o botão "🎵 Nota Cortante", mirar num monstro e
  confirmar dano + animação de dado.
- `read_console_messages` (sem erros), `computer screenshot` como prova.

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(instrumentos): HUD do bardo (botao + mira) + slot de instrumento na ficha"
```

---

## Task 12: Documentação (CLAUDE.md + memória)

**Files:**
- Modify: `CLAUDE.md` — nova mensagem `usar_instrumento` na tabela Client→Server; bloco descritivo do sistema de instrumentos
- Modify: `C:\Users\RICARDO\.claude\projects\C--Users-RICARDO-Desktop-jogo-tabuleiro\memory\` — nota + índice

- [ ] **Step 1: Atualizar CLAUDE.md**

Adicionar à tabela Client→Server:

```markdown
| `usar_instrumento` | `target_id` opcional — o bardo ativa a habilidade do instrumento equipado (só `modo:"ativada"`). Nota Cortante mira 1 monstro; Acorde/Ecos são auto-centrados. Economia de ação: 2 mãos = atacar OU tocar; 1 mão = atacar E tocar; máx. 1/turno (`instrumento_usado`). Custo em 🍖/💧 conforme os stats derivados; sem recarga. |
```

E um parágrafo-resumo (estilo dos demais blocos `>`) descrevendo `INSTRUMENTOS_BASE`,
`criar_instrumento`/`_instrumento_stats`/`_instrumento_cd`, o slot de gear
`"instrumento"` (bard-only), os 4 efeitos, o hook da Sinfonia em
`_cancao_nivel_atributo`, o hook do Ecos no ataque de monstro, a aquisição por
loja/loot, o loadout de Henrique (adaga + Alaúde Velho), e as Fases 2–5 pendentes.
Mencionar a lacuna do `mov_pen_val` do Tambor Velho (gravado, leitura opcional).

- [ ] **Step 2: Atualizar a memória**

Criar `memory/instrumentos-bardo.md` (frontmatter `type: project`) resumindo o sistema
e o estado (Fase 1 concluída; Fases 2–5 pendentes; specs/plans em
`docs/superpowers/`). Adicionar 1 linha em `memory/MEMORY.md`.

- [ ] **Step 3: Rodar a suíte completa de testes do servidor**

Run: `python tools/test_instrumentos_bardo.py`
Run (regressão): `python tools/test_bardo_espec.py` e `python tools/test_guilda.py`
Expected: todos PASS (a mudança em `_cancao_nivel_atributo` não quebra a espec da Canção).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(instrumentos): documenta sistema de instrumentos do bardo (Fase 1) no CLAUDE.md"
```

---

## Self-Review (cobertura do spec)

- §2.1 instância → Task 1 (`criar_instrumento`). ✅
- §2.2 `INSTRUMENTOS_BASE` → Task 1. ✅ (ids de atributo corrigidos p/ acerto/ca)
- §2.3 `_instrumento_stats` (camadas + custo≥0) → Task 1. ✅
- §2.3 CD do save (8+mod(DES), Élfica+1 plumbado) → Task 1 (`_instrumento_cd`). ✅
- §2.4 nome derivado → Task 1 (`_instrumento_nome`). ✅
- §3.1 slot de gear bard-only → Task 2. ✅
- §3.2 economia de ação (1h/2h, `instrumento_usado`, passiva) → Task 3. ✅
- §4 `handle_usar_instrumento` → Task 3. ✅
- §4.1 Nota Cortante → Task 4. ✅
- §4.2 Acorde Trovejante → Task 5. ✅
- §4.3 Ecos Dolorosos (aura ativada) → Task 6. ✅
- §4.4 Sinfonia Heroica (passiva) → Task 7. ✅
- §5 aquisição loja+loot → Task 8. ✅
- §6 loadout de Henrique → Task 9. ✅
- §7 cliente (sender/getters/HUD/ficha) → Tasks 10–11. ✅
- §8 testes → Tasks 1–9 (TDD) + Task 12 regressão. ✅

**Lacunas conhecidas (aceitas, documentadas na Task 12):**
- `mov_pen_val` do Tambor Velho (push=0) é gravado mas a leitura no movimento do
  monstro é opcional na Fase 1 (o Tambor Velho é fraco por design).
- Vários passos exigem `grep` para casar a estrutura real (dispatcher de mensagens,
  catálogo de loja, fábrica de jogador, sites de ataque de monstro, helpers de HUD/
  ficha do cliente). São confirmações de nomes locais, não decisões de design.
