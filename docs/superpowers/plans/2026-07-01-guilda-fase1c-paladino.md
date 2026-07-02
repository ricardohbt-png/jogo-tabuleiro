# Guilda — Fase 1c (Especializações do Paladino) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enfraquecer as 5 habilidades-base do Paladino e vender os níveis II/III na Guilda (9 nós), gateando cura/dano/atributos/alcance/raio pela posse.

**Architecture:** Servidor autoritativo, estilo imperativo das Fases 1a/1b: 9 entradas `categoria:"especializacao"` no `GUILD_CATALOG` + helpers testáveis (`_cura_maos_dados`, `_ataque_sagrado_dados`, `_gdl_max_atributos`, `_gdl_trap_raio`, `_defensor_raio`, `_defensor_split`, `_regen_raio`) lidos por `tem_espec` nos handlers do Richard. Detecção de armadilhas reusa a revelação do Ladino (generalizada por raio).

**Tech Stack:** Python 3 + `websockets` (servidor); Vanilla JS (cliente). Testes no harness caseiro (`tools/test_*.py`), **não** pytest.

**Spec:** `docs/superpowers/specs/2026-07-01-guilda-fase1c-paladino-design.md`

---

## Contexto de código (anchors — localizar por conteúdo)

- `GUILD_CATALOG`, `guild_item`, `guild_items_for_class`, `tem_espec` já existem. Helpers do Clérigo (`_cura_teto`/`_massa_nivel`/`_purif_tipos`/`_ressur_nivel`) são métodos de `GameRoom` (~server.py:3810) — pôr os do Paladino perto.
- `handle_imposicao_maos` (~6632): `raw = roll_dice("1d6")`; `cura = max(1, raw + mod(p["str_"]))`; custo `fome_cost, sede_cost = 3, 2` (validado antes).
- Golpe Sagrado em `handle_attack` (~5116): `if p.get("golpe_sagrado_ativo"): holy_roll = roll_dice("1d8"); ... holy = self._apply_damage_types(holy_roll, [DMG_HOLY], target, None); ... dmg += holy`.
- `_ativar_guerreiro_luz` (~6777): monta `bonus_validos = {"visao":_b("visao"),"ataque":_b("ataque"),"dano":_b("dano"),"ca":_b("ca")}` (cada 0–2); custo por ponto; ao ativar com `visao>0` chama `_reveal_around`. **Sem limite** de atributos hoje.
- `handle_protetor` (~6702): `_no_raio(p, alvo, 4)`. `_processar_dano_protetor` (~6873): `_no_raio(richard, alvo, 4)` e `dano_aliado = dano_richard = dano_original // 2`.
- `_processar_manutencao_richard` (~6817): bloco Regeneração (~6822-6834) cura só Richard (+1 HP, 🍖1💧1).
- `_revelar_armadilhas_luccas` (~9696): revela `self.traps` não disparadas e `self.armadilhas` colocáveis hostis dentro de `_get_raio_visao(p)` (Chebyshev). Retorna quantas revelou.

**Setup de teste** (`tools/test_paladino_espec.py`):
```python
"""Especializações do Paladino (Fase 1c). Roda da raiz: python tools/test_paladino_espec.py"""
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
    r._no_raio = lambda p, alvo, raio, *a, **k: max(abs(p["pos"][0]-alvo["pos"][0]), abs(p["pos"][1]-alvo["pos"][1])) <= raio
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = phase; r._errs = errs
    return r

def paladin(**owned):
    p = make_player("r", "Richard", "paladin", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]
    return p
```

---

## Task 1: Catálogo — 9 especializações do Paladino

**Files:** Modify `server.py`; Create `tools/test_paladino_espec.py`.

- [ ] **Step 1: Criar `tools/test_paladino_espec.py`** com o cabeçalho/`setup`/`paladin` acima e este `main()`:
```python
async def main():
    # [1] Catálogo
    print("\n[1] Catálogo do Paladino")
    ids = [i["id"] for i in S.guild_items_for_class("paladin")]
    for eid in ["paladino_cura_maos_2","paladino_cura_maos_3","paladino_ataque_sagrado_2",
                "paladino_luz_2","paladino_luz_3","paladino_defensor_2","paladino_defensor_3",
                "paladino_regen_2","paladino_regen_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cura_maos_3 requer _2", S.guild_item("paladino_cura_maos_3")["requer"] == "paladino_cura_maos_2")
    check("ataque_sagrado_2 sem requer", S.guild_item("paladino_ataque_sagrado_2")["requer"] is None)
    check("luz_3 requer luz_2", S.guild_item("paladino_luz_3")["requer"] == "paladino_luz_2")
    check("preço II = 150", S.guild_item("paladino_defensor_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("paladino_regen_3")["preco"] == 200)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```
(Manter summary/`sys.exit` no fim; tasks seguintes inserem blocos antes.)

- [ ] **Step 2: Rodar — MUST fail.** `python tools/test_paladino_espec.py`

- [ ] **Step 3: Adicionar 9 entradas ao `GUILD_CATALOG`** (após as do Clérigo). Usar exatamente os dicts da §3 do spec (`paladino_cura_maos_2/3`, `paladino_ataque_sagrado_2`, `paladino_luz_2/3`, `paladino_defensor_2/3`, `paladino_regen_2/3`), com `categoria:"especializacao"`, `classe:"paladin"`, `exclusiva:False`, preços 150 (II) / 200 (III), e `requer` = o `_2` da linha para cada III (e `None` para os II e para `ataque_sagrado_2`).

- [ ] **Step 4: Rodar — MUST pass.**

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): catalogo de especializacoes do Paladino"
```

---

## Task 2: Cura pelas Mãos (2d6 no II; +1d6 opcional no III)

**Files:** Modify `server.py`; `tools/test_paladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [2] Cura pelas Mãos
    print("\n[2] Cura pelas Mãos")
    r = setup()
    check("dados base = 1", r._cura_maos_dados(paladin()) == 1)
    check("dados II = 2", r._cura_maos_dados(paladin(esp=["paladino_cura_maos_2"])) == 2)
    _orig = S.roll_dice; S.roll_dice = lambda s: sum(6 for _ in range(int(s.split("d")[0])))  # cada dado=6
    try:
        # base: 1d6(=6)+FOR. Richard FOR mod: usar o valor real de make_player.
        r = setup(); p = paladin(esp=["paladino_cura_maos_2"]); r.players["r"]=p
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=99; r.players["a"]=alvo
        from server import mod
        await r.handle_imposicao_maos("r", {"target_id":"a"})
        check("II cura 2d6+FOR (12+mod)", alvo["hp"] == 1 + (12 + mod(p["str_"])))
        # III: +1d6 opcional (extra_d6=2) → +2d6 e custo +4/+4
        r = setup(); p = paladin(esp=["paladino_cura_maos_2","paladino_cura_maos_3"]); p["fome"]=50; p["sede"]=50; r.players["r"]=p
        alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=1; alvo["max_hp"]=999; r.players["a"]=alvo
        await r.handle_imposicao_maos("r", {"target_id":"a","extra_d6":2})
        check("III +2d6 (2d6 base + 2d6 extra = 24 + FOR)", alvo["hp"] == 1 + (24 + mod(p["str_"])))
        check("III custo base+extra (3+4 fome / 2+4 sede)", p["fome"] == 50-7 and p["sede"] == 50-6)
    finally:
        S.roll_dice = _orig
```

- [ ] **Step 2: Rodar — MUST fail** (`_cura_maos_dados` inexistente).

- [ ] **Step 3: Helper** (método de `GameRoom`, perto dos helpers do Clérigo):
```python
    def _cura_maos_dados(self, p):
        return 2 if tem_espec(p, "paladino_cura_maos_2") else 1
```

- [ ] **Step 4: Gatear `handle_imposicao_maos`.** Trocar o cálculo de `raw`/`cura` e o custo:
```python
        # extra_d6 (Cura pelas Mãos III): +1d6 por +2🍖/+2💧, até 3 (só se possuído)
        extra_d6 = max(0, min(3, int((data or {}).get("extra_d6", 0)))) if tem_espec(p, "paladino_cura_maos_3") else 0
        fome_cost, sede_cost = 3 + 2 * extra_d6, 2 + 2 * extra_d6
        if p["fome"] < fome_cost or p["sede"] < sede_cost:
            await self.send_to(pid, {"type": "error", "msg": f"Recursos insuficientes 🍖{fome_cost} 💧{sede_cost}."}); return
```
(substituindo a linha antiga `fome_cost, sede_cost = 3, 2` e sua checagem). E trocar a rolagem:
```python
        n_dados = self._cura_maos_dados(p) + extra_d6
        raw = sum(roll_dice("1d6") for _ in range(n_dados))
        await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw, "label": "Imposição das Mãos"})
        cura = max(1, raw + mod(p["str_"]))
```
(substituindo `raw = roll_dice("1d6")` e o `dice_roll` correspondente). O resto (aplicar cura, débito, `action_done`) permanece — mas garanta que o débito use `fome_cost`/`sede_cost` já calculados.

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): Cura pelas Maos 2d6 (II) + opcao +1d6 (III) no Paladino"
```

---

## Task 3: Ataque Sagrado — +2d8 no II

**Files:** Modify `server.py`; `tools/test_paladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [3] Ataque Sagrado (dados)
    print("\n[3] Ataque Sagrado")
    r = setup()
    check("sagrado base = 1 d8", r._ataque_sagrado_dados(paladin()) == 1)
    check("sagrado II = 2 d8", r._ataque_sagrado_dados(paladin(esp=["paladino_ataque_sagrado_2"])) == 2)
```

- [ ] **Step 2: Rodar — MUST fail.**

- [ ] **Step 3: Helper:**
```python
    def _ataque_sagrado_dados(self, p):
        return 2 if tem_espec(p, "paladino_ataque_sagrado_2") else 1
```

- [ ] **Step 4: Gatear o Golpe Sagrado em `handle_attack`** (~5116). Trocar:
```python
                    holy_roll = roll_dice("1d8")
```
por:
```python
                    holy_roll = sum(roll_dice("1d8") for _ in range(self._ataque_sagrado_dados(p)))
```
(O `dice_roll` broadcast e o `_apply_damage_types` continuam usando `holy_roll`.)

- [ ] **Step 5: Rodar — MUST pass** + regressão `python tools/test_devorador.py` (anote).

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): Ataque Sagrado +2d8 (II) no Paladino"
```

---

## Task 4: Guerreiro da Luz — teto de atributos (2/3/4)

**Files:** Modify `server.py`; `tools/test_paladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [4] Guerreiro da Luz: teto de atributos
    print("\n[4] Guerreiro da Luz (atributos)")
    r = setup()
    check("max base = 2", r._gdl_max_atributos(paladin()) == 2)
    check("max luz_2 = 3", r._gdl_max_atributos(paladin(esp=["paladino_luz_2"])) == 3)
    check("max luz_3 = 4", r._gdl_max_atributos(paladin(esp=["paladino_luz_2","paladino_luz_3"])) == 4)
    # integração: 3 atributos sem luz_2 é recusado
    r = setup(); p = paladin(); p["fome"]=50; p["sede"]=50; r.players["r"]=p
    await r._ativar_guerreiro_luz(p, "r", {"bonus":{"ataque":1,"dano":1,"ca":1}})
    check("recusa 3 atributos sem luz_2", not p.get("guerreiro_luz_ativo") and r._errs)
    # com luz_2 aceita 3
    r = setup(); p = paladin(esp=["paladino_luz_2"]); p["fome"]=50; p["sede"]=50; r.players["r"]=p
    await r._ativar_guerreiro_luz(p, "r", {"bonus":{"ataque":1,"dano":1,"ca":1}})
    check("aceita 3 atributos com luz_2", p.get("guerreiro_luz_ativo") is True)
```

- [ ] **Step 2: Rodar — MUST fail** (`_gdl_max_atributos` inexistente).

- [ ] **Step 3: Helper:**
```python
    def _gdl_max_atributos(self, p):
        if tem_espec(p, "paladino_luz_3"): return 4
        if tem_espec(p, "paladino_luz_2"): return 3
        return 2
```

- [ ] **Step 4: Gatear `_ativar_guerreiro_luz`.** Logo após montar `bonus_validos`, antes de calcular custo, inserir:
```python
        n_ativos = sum(1 for v in bonus_validos.values() if v > 0)
        if n_ativos > self._gdl_max_atributos(p):
            await self.send_to(pid, {"type": "error",
                "msg": f"Guerreiro da Luz permite {self._gdl_max_atributos(p)} atributo(s) ativo(s) — evolua na Guilda."}); return
```

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): Guerreiro da Luz gateia numero de atributos (2/3/4)"
```

---

## Task 5: Guerreiro da Luz — detecção de armadilhas (raio 1/2/3)

**Files:** Modify `server.py`; `tools/test_paladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [5] Guerreiro da Luz: detecção de armadilhas
    print("\n[5] Guerreiro da Luz (armadilhas)")
    r = setup()
    check("trap raio base = 1", r._gdl_trap_raio(paladin()) == 1)
    check("trap raio luz_2 = 2", r._gdl_trap_raio(paladin(esp=["paladino_luz_2"])) == 2)
    check("trap raio luz_3 = 3", r._gdl_trap_raio(paladin(esp=["paladino_luz_2","paladino_luz_3"])) == 3)
    # integração: revela armadilha colocável hostil a 2 quadrados com raio 2
    r = setup(); p = paladin(esp=["paladino_luz_2"]); p["pos"]=[0,0]; r.players["r"]=p
    r.armadilhas = [{"pos":[0,2], "visivel": False, "criador": "monstro1"}]
    r.traps = []
    r.explored = set()
    n = r._revelar_armadilhas_raio(p, r._gdl_trap_raio(p))
    check("revelou armadilha a 2q com raio 2", r.armadilhas[0]["visivel"] is True and n == 1)
    # fora do raio (raio 1) não revela
    r = setup(); p = paladin(); p["pos"]=[0,0]; r.players["r"]=p
    r.armadilhas = [{"pos":[0,2], "visivel": False, "criador": "monstro1"}]
    r.traps = []; r.explored = set()
    r._revelar_armadilhas_raio(p, r._gdl_trap_raio(p))
    check("não revela a 2q com raio 1", r.armadilhas[0]["visivel"] is False)
```

- [ ] **Step 2: Rodar — MUST fail** (`_gdl_trap_raio`/`_revelar_armadilhas_raio` inexistentes).

- [ ] **Step 3: Helper `_gdl_trap_raio`:**
```python
    def _gdl_trap_raio(self, p):
        if tem_espec(p, "paladino_luz_3"): return 3
        if tem_espec(p, "paladino_luz_2"): return 2
        return 1
```

- [ ] **Step 4: Generalizar a revelação por raio.** Refatorar `_revelar_armadilhas_luccas` para delegar a um novo `_revelar_armadilhas_raio(self, p, raio)` (mover o corpo, trocar `raio = self._get_raio_visao(p)` por o parâmetro), e `_revelar_armadilhas_luccas` passa a ser:
```python
    def _revelar_armadilhas_luccas(self, p):
        return self._revelar_armadilhas_raio(p, self._get_raio_visao(p))
```
E o novo método (corpo idêntico ao atual, mas usando o `raio` recebido):
```python
    def _revelar_armadilhas_raio(self, p, raio):
        """Revela traps de masmorra e armadilhas colocáveis hostis dentro de `raio` de p."""
        px, py = p["pos"]
        reveladas = 0
        for tr in self.traps:
            if tr["triggered"]:
                continue
            if max(abs(tr["pos"][0] - px), abs(tr["pos"][1] - py)) <= raio \
               and tuple(tr["pos"]) not in self.explored:
                self.explored.add(tuple(tr["pos"]))
                reveladas += 1
        for a in self.armadilhas:
            if a.get("esgotada") or a.get("visivel"):
                continue
            if a.get("criador") in self.players:
                continue
            if max(abs(a["pos"][0] - px), abs(a["pos"][1] - py)) <= raio:
                a["visivel"] = True
                reveladas += 1
        return reveladas
```

- [ ] **Step 5: Chamar na ativação e no upkeep do Guerreiro da Luz.**
Em `_ativar_guerreiro_luz`, no bloco `if bonus_validos["visao"] > 0 and p.get("pos"):` (que já revela névoa), acrescentar após o `_reveal_around`:
```python
            self._revelar_armadilhas_raio(p, self._gdl_trap_raio(p))
```
E no upkeep `_processar_manutencao_richard`, no tratamento do Guerreiro da Luz (buscar o bloco `guerreiro_luz_ativo`; se o upkeep do GdL ainda não revela armadilhas, adicionar): se `p.get("guerreiro_luz_ativo")` e `p.get("guerreiro_luz_bonus",{}).get("visao",0) > 0`, chamar `self._revelar_armadilhas_raio(p, self._gdl_trap_raio(p))`.

- [ ] **Step 6: Rodar — MUST pass** + regressão de Luccas: `python tools/test_devorador.py` (o refactor de `_revelar_armadilhas_luccas` não pode quebrar). Anote.

- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): Guerreiro da Luz detecta armadilhas por raio (1/2/3)"
```

---

## Task 6: Defensor — alcance (raio 5) + split 40/40

**Files:** Modify `server.py`; `tools/test_paladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [6] Defensor
    print("\n[6] Defensor")
    r = setup()
    check("raio base = 4", r._defensor_raio(paladin()) == 4)
    check("raio II = 5", r._defensor_raio(paladin(esp=["paladino_defensor_2"])) == 5)
    check("split base = (5,5) de 10", r._defensor_split(paladin(), 10) == (5, 5))
    check("split III = (4,4) de 10", r._defensor_split(paladin(esp=["paladino_defensor_2","paladino_defensor_3"]), 10) == (4, 4))
    # integração: _processar_dano_protetor divide 40/40 com _3
    r = setup(); p = paladin(esp=["paladino_defensor_2","paladino_defensor_3"]); p["pos"]=[0,0]
    p["protetor_ativo"]=True; p["protetor_alvo"]="a"; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; r.players["a"]=alvo
    dano_alvo, transfer = await r._processar_dano_protetor("a", 10)
    check("protetor III → aliado 4", dano_alvo == 4)
    check("protetor III → richard 4", transfer is not None and transfer[1] == 4)
```

- [ ] **Step 2: Rodar — MUST fail.**

- [ ] **Step 3: Helpers:**
```python
    def _defensor_raio(self, p):
        return 5 if tem_espec(p, "paladino_defensor_2") else 4
    def _defensor_split(self, richard, dano):
        if tem_espec(richard, "paladino_defensor_3"):
            parte = (dano * 2) // 5   # 40% (floor); 20% mitigado
            return parte, parte
        metade = dano // 2
        return metade, metade
```

- [ ] **Step 4: Aplicar em `handle_protetor` e `_processar_dano_protetor`.**
- Em `handle_protetor`, trocar `_no_raio(p, alvo, 4)` por `_no_raio(p, alvo, self._defensor_raio(p))`.
- Em `_processar_dano_protetor`, trocar `_no_raio(richard, alvo, 4)` por `_no_raio(richard, alvo, self._defensor_raio(richard))`, e trocar:
```python
        dano_aliado  = dano_original // 2
        dano_richard = dano_original // 2
```
por:
```python
        dano_aliado, dano_richard = self._defensor_split(richard, dano_original)
```

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): Defensor alcance 5 (II) + split 40/40 (III)"
```

---

## Task 7: Regeneração — cura aliados (raio 1/2)

**Files:** Modify `server.py`; `tools/test_paladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [7] Regeneração em área
    print("\n[7] Regeneração")
    r = setup()
    check("regen raio base = 0", r._regen_raio(paladin()) == 0)
    check("regen raio II = 1", r._regen_raio(paladin(esp=["paladino_regen_2"])) == 1)
    check("regen raio III = 2", r._regen_raio(paladin(esp=["paladino_regen_2","paladino_regen_3"])) == 2)
    # integração: upkeep com regen_2 cura aliado adjacente ferido
    r = setup(); p = paladin(esp=["paladino_regen_2"]); p["pos"]=[0,0]; p["hp"]=5; p["max_hp"]=20
    p["fome"]=50; p["sede"]=50; p["regeneracao_ativa"]=True; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=5; alvo["max_hp"]=20; r.players["a"]=alvo
    await r._processar_manutencao_richard(p)
    check("regen II cura Richard +1", p["hp"] == 6)
    check("regen II cura aliado adjacente +1", alvo["hp"] == 6)
    # base não cura aliado
    r = setup(); p = paladin(); p["pos"]=[0,0]; p["hp"]=5; p["max_hp"]=20; p["fome"]=50; p["sede"]=50; p["regeneracao_ativa"]=True; r.players["r"]=p
    alvo = make_player("a","Ana","warrior",1); alvo["pos"]=[0,1]; alvo["hp"]=5; alvo["max_hp"]=20; r.players["a"]=alvo
    await r._processar_manutencao_richard(p)
    check("base não cura aliado", alvo["hp"] == 5)
```

- [ ] **Step 2: Rodar — MUST fail** (`_regen_raio` inexistente).

- [ ] **Step 3: Helper:**
```python
    def _regen_raio(self, p):
        if tem_espec(p, "paladino_regen_3"): return 2
        if tem_espec(p, "paladino_regen_2"): return 1
        return 0
```

- [ ] **Step 4: Curar aliados no upkeep.** No bloco Regeneração de `_processar_manutencao_richard`, no `else` (onde Richard ganha +1 HP), após `p["hp"] = min(...)`, adicionar:
```python
                raio_reg = self._regen_raio(p)
                if raio_reg > 0:
                    curados = []
                    for q in self.players.values():
                        if q is p or not q.get("alive"): continue
                        if q.get("hp", 0) >= q.get("max_hp", 0): continue
                        if max(abs(q["pos"][0]-p["pos"][0]), abs(q["pos"][1]-p["pos"][1])) <= raio_reg:
                            q["hp"] = min(q["max_hp"], q["hp"] + 1); curados.append(q["name"])
                    if curados:
                        await self.gm_say(f"✨ Regeneração Divina de **{p['name']}** também cura: {', '.join(curados)} (+1 HP).")
```
(Upkeep de custo mantém 🍖1💧1 do Richard, inalterado.)

- [ ] **Step 5: Rodar — MUST pass** + regressão `python tools/test_devorador.py` (anote).

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_paladino_espec.py
git commit -m "feat(guilda): Regeneracao Divina cura aliados por raio (II/III)"
```

---

## Task 8: Cliente — painéis do Richard respeitam os níveis

**Files:** Modify `src/gameState.js`, `game.js`.

- [ ] **Step 1: Getters no `gameState.js`** (perto de `clericRessurNivel`):
```javascript
  function paladinCuraMaosDados()   { return (guildOwnedOf(myPid).especializacoes||[]).includes('paladino_cura_maos_2') ? 2 : 1; }
  function paladinCuraMaosExtra()   { return (guildOwnedOf(myPid).especializacoes||[]).includes('paladino_cura_maos_3'); }
  function paladinAtaqueSagradoDados(){ return (guildOwnedOf(myPid).especializacoes||[]).includes('paladino_ataque_sagrado_2') ? 2 : 1; }
  function paladinLuzMaxAtributos() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('paladino_luz_3')) return 4;
    if (e.includes('paladino_luz_2')) return 3;
    return 2;
  }
```
Exportar os 4 no `return { ... }`.

- [ ] **Step 2: Guerreiro da Luz — limitar atributos no painel.** No renderer do Richard (`game.js`, painel de escolha dos bônus do Guerreiro da Luz — grepar por `guerreiro_luz`/`_ativarGuerreiroLuz`/o painel que monta os 4 sliders visão/ataque/dano/CA), impedir ativar mais que `GS.paladinLuzMaxAtributos()` atributos não-zero: ao confirmar, se o nº de atributos > 0 exceder o teto, `toast('Guerreiro da Luz permite N atributos — evolua na Guilda.')` e não enviar. **Ler o painel inteiro antes** para inserir no ponto de confirmação.

- [ ] **Step 3: Cura pelas Mãos — opção +1d6 (III) + descrição 2d6 (II).** No painel/botão da Imposição das Mãos, se `GS.paladinCuraMaosExtra()`, oferecer um seletor de `extra_d6` (0–3) mostrando o custo extra (+2🍖/+2💧 cada) e enviar `extra_d6` no `imposicao_maos`. A descrição mostra "2d6+FOR" se `paladinCuraMaosDados()===2`. (Se hoje a Imposição não tem painel — só pede alvo —, adicionar um pequeno painel só quando `paladinCuraMaosExtra()` for true; caso contrário mantém o fluxo atual enviando `extra_d6:0`.)

- [ ] **Step 4: Descrições.** Golpe Sagrado mostra "+2d8" se `paladinAtaqueSagradoDados()===2`; Defensor/Regeneração refletem o nível (raio 5 / 40% / aliados) nas descrições dos botões (ler a posse via `GS.guildOwnedOf(me.id).especializacoes`).

- [ ] **Step 5: Syntax check.** `node --check src/gameState.js && node --check game.js` → exit 0.

- [ ] **Step 6: Commit**
```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): paineis do Paladino respeitam niveis das especializacoes"
```

---

## Task 9: Verificação E2E + docs

**Files:** Modify `CLAUDE.md`.

- [ ] **Step 1: Suíte**
`python tools/test_paladino_espec.py` → 0 falharam
`python tools/test_clerigo_espec.py` / `test_guerreiro_espec.py` / `test_guilda.py` → 0 falharam
`python tools/test_devorador.py` → combate ok (regressão dos handlers/refactor de armadilhas)

- [ ] **Step 2: Smoke test in-app** (padrão das fases; `.claude/launch.json` server `game`):
  - Subir preview; criar sala; escolher **Paladino**; dar ouro (bump temporário-e-revertido do `start_gold` do `paladin`; `rm -rf saves/` ao fim).
  - Na Guilda: comprar `paladino_cura_maos_2` e `paladino_luz_2`.
  - Verificar (via getters/painéis): Cura pelas Mãos indica 2d6; Guerreiro da Luz permite 3 atributos (o 4º é barrado); zero erros de console.

- [ ] **Step 3: `CLAUDE.md`** — na seção da Guilda, acrescentar parágrafo do Paladino: baseline enfraquecido (Guerreiro da Luz 4→2 atributos, Cura Mãos 2d6→1d6, Golpe Sagrado 2d8→1d8, Defensor 50/50, Regeneração só Richard); compras `paladino_cura_maos_2/3`, `paladino_ataque_sagrado_2`, `paladino_luz_2/3`, `paladino_defensor_2/3`, `paladino_regen_2/3` (II=150/III=200, III exige II); helpers `_cura_maos_dados`/`_ataque_sagrado_dados`/`_gdl_max_atributos`/`_gdl_trap_raio`/`_defensor_raio`/`_defensor_split`/`_regen_raio`; detecção de armadilhas via `_revelar_armadilhas_raio` (generalizado do Ladino); Defensor III split 40/40; teste `tools/test_paladino_espec.py`. Registrar o nerf.

- [ ] **Step 4: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(guilda): documentar especializacoes do Paladino (Fase 1c)"
```

---

## Self-review (cobertura do spec)

- **§3 catálogo (9 nós)** → Task 1. ✔
- **§4.1 Cura pelas Mãos (2d6 II; +1d6 III)** → Task 2. ✔
- **§4.2 Ataque Sagrado (+2d8 II)** → Task 3. ✔
- **§4.3 Guerreiro da Luz (atributos 2/3/4)** → Task 4; **(detecção armadilhas 1/2/3)** → Task 5. ✔
- **§4.4 Defensor (raio 5 II; split 40/40 III)** → Task 6. ✔
- **§4.5 Regeneração (aliados raio 1/2)** → Task 7. ✔
- **§5 cliente** → Task 8. ✔
- **§6 testes** → `tools/test_paladino_espec.py` (Tasks 1-7) + smoke (Task 9). ✔
- **§8 riscos (nerf; refactor armadilhas; split floor; regressão)** → nerf documentado (Task 9); refactor isolado + regressão devorador (Tasks 5/3/7); `(dano*2)//5` (Task 6). ✔

**Consistência de nomes:** helpers `_cura_maos_dados`/`_ataque_sagrado_dados`/`_gdl_max_atributos`/`_gdl_trap_raio`/`_defensor_raio`/`_defensor_split`/`_regen_raio` + `_revelar_armadilhas_raio` (todos métodos de `GameRoom`); cliente `paladinCuraMaosDados`/`paladinCuraMaosExtra`/`paladinAtaqueSagradoDados`/`paladinLuzMaxAtributos`. Ids: `paladino_{cura_maos,ataque_sagrado,luz,defensor,regen}_{2,3}` (ataque_sagrado só `_2`). Payload novo: `imposicao_maos.extra_d6`.

**Nota de teste:** o `setup()` usa um `_no_raio` real baseado em Chebyshev (não stub `True`) para os testes de Defensor/Regeneração/Protetor dependerem de distância; `roll_dice` é mockado para dado fixo nos testes de cura.
