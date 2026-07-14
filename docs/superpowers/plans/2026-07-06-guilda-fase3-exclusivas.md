# Guilda dos Heróis — Fase 3: Técnicas Exclusivas (Mago/Clérigo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar as 7 Técnicas Exclusivas da Guilda (2º slot `tecnica_exclusiva`, só Mago/Clérigo) que aprimoram a próxima magia lançada — Aprimorar/Estender/Canalização Arcana (5r), Empoderar/Geminada/Canalização Perfeita (8r), Magia Acelerada (10r).

**Architecture:** Segue exatamente o padrão já usado nas Fases 2a-2e: novas entradas em `GUILD_CATALOG` (server.py) despachadas por `efeito.tipo` dentro de `handle_usar_tecnica` (armam flags no jogador), consumidas dentro de `handle_magia`/executores de magia existentes. Nenhuma mensagem de protocolo nova. Duas generalizações pontuais e retrocompatíveis: `classe` no catálogo passa a aceitar lista (hoje só `None`/string), e `_testar_save` ganha um parâmetro `desvantagem`. Ver spec completa em `docs/superpowers/specs/2026-07-06-guilda-fase3-exclusivas-design.md`.

**Tech Stack:** Python 3 (`server.py`, `websockets`), JS vanilla (`game.js`, `src/gameState.js`), harness de teste custom (`tools/test_*.py`, sem pytest).

**Branch sugerido:** `guilda-fase3-exclusivas` (worktree, seguindo o padrão dos merges `worktree-guilda-fase2X-...` já usados nas fases anteriores).

---

## Task 1: `classe` do catálogo aceita lista (Mago + Clérigo)

**Files:**
- Modify: `server.py:724-730` (função `guild_item`/`guild_items_for_class`)
- Modify: `server.py:4131-4134` (dentro de `handle_guild_buy`)
- Modify: `src/gameState.js:1121-1124` (função `guildCatalogFor`)
- Test: `tools/test_guilda_fase3_espec.py` (novo arquivo)

- [ ] **Step 1: Criar o arquivo de teste com o skeleton + seção [1] (falhando)**

Criar `tools/test_guilda_fase3_espec.py`:

```python
"""Guilda dos Heróis — Fase 3: Técnicas Exclusivas (Mago/Clérigo).
Roda da raiz: python tools/test_guilda_fase3_espec.py"""
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
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r.round_num = 1
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r._tem_linha_de_visao = lambda *a, **k: True
    return r

def caster(cls="mage", tid_ex=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    p["magias_conhecidas"] = list(S.GRIMORIO_IMPLEMENTADAS)
    if tid_ex:
        p["guild_owned"]["tecnicas"] = [tid_ex]
        p["guild_equip"]["tecnica_exclusiva"] = tid_ex
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    print("\n[1] classe como lista — compra, catálogo, restrição")
    r = setup(phase="city")
    mago = caster("mage"); r.players["h"] = mago
    clerigo = caster("cleric"); r.players["c"] = clerigo
    guerreiro = caster("warrior"); r.players["w"] = guerreiro
    for pid_ in ("h", "c", "w"): r.players[pid_]["gold"] = 1000
    r._errs.clear()
    await r.handle_guild_buy("h", "tec_ex_aprimorar_magia")
    check("mago compra técnica exclusiva", "tec_ex_aprimorar_magia" in mago["guild_owned"]["tecnicas"])
    r._errs.clear()
    await r.handle_guild_buy("c", "tec_ex_aprimorar_magia")
    check("clérigo compra a mesma técnica", "tec_ex_aprimorar_magia" in clerigo["guild_owned"]["tecnicas"])
    r._errs.clear()
    await r.handle_guild_buy("w", "tec_ex_aprimorar_magia")
    check("guerreiro é recusado", "tec_ex_aprimorar_magia" not in guerreiro["guild_owned"]["tecnicas"])
    check("guerreiro recebe erro de classe", any("classe" in e.lower() for e in r._errs))
    ids_mage = [i["id"] for i in S.guild_items_for_class("mage")]
    ids_warr = [i["id"] for i in S.guild_items_for_class("warrior")]
    check("catálogo do mago inclui as 7 exclusivas",
          all(f"tec_ex_{n}" in ids_mage for n in
              ["aprimorar_magia", "estender_magia", "canalizacao_arcana", "empoderar_magia",
               "magia_geminada", "canalizacao_perfeita", "magia_acelerada"]))
    check("catálogo do guerreiro NÃO inclui nenhuma exclusiva",
          not any(i.startswith("tec_ex_") for i in ids_warr))

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar e confirmar que falha (as 7 técnicas ainda não existem no catálogo)**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` na seção [1] (ex.: `KeyError`/`guerreiro recebe erro de classe` falha porque `tec_ex_aprimorar_magia` nem existe em `GUILD_CATALOG`, então `guild_item` retorna `None` e `handle_guild_buy` erra com "Item da guilda desconhecido", não "não é da sua classe").

- [ ] **Step 3: Generalizar `classe` no servidor**

Em `server.py`, localizar (perto da linha 724):

```python
def guild_item(item_id):
    return GUILD_CATALOG.get(item_id)

def guild_items_for_class(class_id):
    """Itens do catálogo disponíveis para uma classe (cópias para envio)."""
    return [dict(v) for v in GUILD_CATALOG.values()
            if v["classe"] is None or v["classe"] == class_id]
```

Substituir por:

```python
def guild_item(item_id):
    return GUILD_CATALOG.get(item_id)

def _guild_classe_ok(item_classe, class_id):
    """True se `item_classe` (None, 1 class_id, ou lista/tupla de class_ids) libera `class_id`."""
    if item_classe is None:
        return True
    if isinstance(item_classe, (list, tuple, set)):
        return class_id in item_classe
    return item_classe == class_id

def guild_items_for_class(class_id):
    """Itens do catálogo disponíveis para uma classe (cópias para envio)."""
    return [dict(v) for v in GUILD_CATALOG.values() if _guild_classe_ok(v["classe"], class_id)]
```

Localizar em `handle_guild_buy` (perto da linha 4131):

```python
        # Classe compatível
        if item["classe"] is not None and item["classe"] != p.get("class_id"):
            await self.send_to(pid, {"type": "error", "msg": "Este aprimoramento não é da sua classe."})
            return
```

Substituir por:

```python
        # Classe compatível (classe pode ser None, 1 class_id, ou lista de class_ids)
        if not _guild_classe_ok(item["classe"], p.get("class_id")):
            await self.send_to(pid, {"type": "error", "msg": "Este aprimoramento não é da sua classe."})
            return
```

- [ ] **Step 4: Generalizar `classe` no cliente**

Em `src/gameState.js`, localizar (perto da linha 1121):

```js
  function guildCatalogFor(classId) {
    const catalog = (cityState && cityState.guild && cityState.guild.catalog) || guildCatalogCache || [];
    return catalog.filter(i => i.classe == null || i.classe === classId);
  }
```

Substituir por:

```js
  function guildCatalogFor(classId) {
    const catalog = (cityState && cityState.guild && cityState.guild.catalog) || guildCatalogCache || [];
    return catalog.filter(i => i.classe == null || i.classe === classId
      || (Array.isArray(i.classe) && i.classe.includes(classId)));
  }
```

- [ ] **Step 5: Adicionar as 7 entradas no `GUILD_CATALOG` (só os dados, sem lógica ainda)**

Em `server.py`, localizar o fim do bloco de técnicas da Fase 2e (perto da linha 437-445):

```python
    "tecnica_sorte": {
        "id": "tecnica_sorte", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 350, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 10,
        "nome": "Sorte", "icon": "🎲",
        "desc": "Depois de errar um ataque, você pode gastar esta técnica para "
                "rolá-lo novamente contra o mesmo alvo. Independente do Sangue Frio.",
        "efeito": {"tipo": "sorte"},
    },
```

Inserir logo depois (antes de `"guerreiro_combinar_2": {`):

```python
    # ── Técnicas Exclusivas (Fase 3) — Mago/Clérigo, slot tecnica_exclusiva ──
    "tec_ex_aprimorar_magia": {
        "id": "tec_ex_aprimorar_magia", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True,
        "linha": None, "nivel": None, "requer": None,
        "preco": 180, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 5,
        "nome": "Aprimorar Magia", "icon": "🎯",
        "desc": "A próxima magia recebe +1 na CD do teste de resistência "
                "(vale p/ magias de área também).",
        "efeito": {"tipo": "tec_ex_aprimorar"},
    },
    "tec_ex_estender_magia": {
        "id": "tec_ex_estender_magia", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True,
        "linha": None, "nivel": None, "requer": None,
        "preco": 180, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 5,
        "nome": "Estender Magia", "icon": "⏱️",
        "desc": "A próxima magia tem +1 rodada de duração, ou +1 quadrado de "
                "alcance se não tiver duração.",
        "efeito": {"tipo": "tec_ex_estender"},
    },
    "tec_ex_canalizacao_arcana": {
        "id": "tec_ex_canalizacao_arcana", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True,
        "linha": None, "nivel": None, "requer": None,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Canalização Arcana", "icon": "🌀",
        "desc": "A próxima magia ignora os efeitos de Silêncio.",
        "efeito": {"tipo": "tec_ex_canalizacao_arcana"},
    },
    "tec_ex_empoderar_magia": {
        "id": "tec_ex_empoderar_magia", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True,
        "linha": None, "nivel": None, "requer": None,
        "preco": 280, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 8,
        "nome": "Empoderar Magia", "icon": "💥",
        "desc": "A próxima magia ofensiva causa 50% a mais de dano (×1,5).",
        "efeito": {"tipo": "tec_ex_empoderar"},
    },
    "tec_ex_magia_geminada": {
        "id": "tec_ex_magia_geminada", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True, "alvo": "qualquer_vivo",
        "linha": None, "nivel": None, "requer": None,
        "preco": 280, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 8,
        "nome": "Magia Geminada", "icon": "👯",
        "desc": "Escolha um 2º alvo agora; a próxima magia de alvo único também "
                "o afeta, se estiver no alcance da magia. Não funciona em "
                "magias de área.",
        "efeito": {"tipo": "tec_ex_geminada"},
    },
    "tec_ex_canalizacao_perfeita": {
        "id": "tec_ex_canalizacao_perfeita", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True,
        "linha": None, "nivel": None, "requer": None,
        "preco": 280, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 8,
        "nome": "Canalização Perfeita", "icon": "🎴",
        "desc": "Na próxima magia de alvo único, o alvo testa resistência com "
                "desvantagem.",
        "efeito": {"tipo": "tec_ex_canalizacao_perfeita"},
    },
    "tec_ex_magia_acelerada": {
        "id": "tec_ex_magia_acelerada", "categoria": "tecnica",
        "classe": ["mage", "cleric"], "exclusiva": True,
        "linha": None, "nivel": None, "requer": None,
        "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
        "nome": "Magia Acelerada", "icon": "⚡",
        "desc": "A próxima magia é lançada como Ação Bônus — não gasta sua "
                "ação principal.",
        "efeito": {"tipo": "tec_ex_acelerada"},
    },
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` na seção [1], `FAIL=0`.

- [ ] **Step 7: Commit**

```bash
git add server.py src/gameState.js tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): Fase 3 — catálogo das 7 técnicas exclusivas + classe como lista"
```

---

## Task 2: `desvantagem` em `_testar_save`/`_save_mostrado`

**Files:**
- Modify: `server.py:10316-10325` (`_testar_save`)
- Modify: `server.py:9761-9767` (`_save_mostrado`)
- Test: `tools/test_guilda_fase3_espec.py`

- [ ] **Step 1: Escrever o teste (seção [2], falhando)**

Adicionar em `tools/test_guilda_fase3_espec.py`, ANTES de `print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")`:

```python
    print("\n[2] _testar_save: desvantagem rola 2d20 e usa o pior")
    r = setup()
    alvo = caster("mage")
    seq = iter([18, 5])
    orig_randint = S.random.randint
    S.random.randint = lambda a, b: next(seq)
    try:
        passou, d20, bonus, total = r._testar_save(alvo, "vontade", 10, desvantagem=True)
    finally:
        S.random.randint = orig_randint
    check("desvantagem usa o menor dos 2 rolls (5, não 18)", d20 == 5)

    seq2 = iter([18, 5])
    S.random.randint = lambda a, b: next(seq2)
    try:
        passou2, d20b, bonus2, total2 = r._testar_save(alvo, "vontade", 10)
    finally:
        S.random.randint = orig_randint
    check("sem desvantagem usa só a 1ª rolagem (18)", d20b == 18)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` — `_testar_save() got an unexpected keyword argument 'desvantagem'`.

- [ ] **Step 3: Implementar `desvantagem` em `_testar_save`**

Em `server.py`, localizar (perto da linha 10316):

```python
    def _testar_save(self, alvo, tipo_save, dificuldade, extra_mod=0, fonte=None):
        """Retorna (passou, d20, bonus, total). extra_mod: bônus/penalidade adicional.
        fonte: monstro-origem do efeito (habilidade de criatura) — habilita o +1 de
        resistência da Lenda do Bardo contra aquela espécie (só p/ jogadores)."""
        bonus = (self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia")
                 + extra_mod + self._lenda_resist_bonus(alvo, fonte)
                 + self._resistencia_saves_bonus(alvo))
        d20   = random.randint(1, 20)
        total = d20 + bonus
        return (total >= dificuldade), d20, bonus, total
```

Substituir por:

```python
    def _testar_save(self, alvo, tipo_save, dificuldade, extra_mod=0, fonte=None, desvantagem=False):
        """Retorna (passou, d20, bonus, total). extra_mod: bônus/penalidade adicional.
        fonte: monstro-origem do efeito (habilidade de criatura) — habilita o +1 de
        resistência da Lenda do Bardo contra aquela espécie (só p/ jogadores).
        desvantagem: rola 2d20 e usa o PIOR (Canalização Perfeita, Fase 3)."""
        bonus = (self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia")
                 + extra_mod + self._lenda_resist_bonus(alvo, fonte)
                 + self._resistencia_saves_bonus(alvo))
        d20   = min(random.randint(1, 20), random.randint(1, 20)) if desvantagem else random.randint(1, 20)
        total = d20 + bonus
        return (total >= dificuldade), d20, bonus, total
```

- [ ] **Step 4: Implementar `desvantagem` em `_save_mostrado`**

Em `server.py`, localizar (perto da linha 9761):

```python
    async def _save_mostrado(self, alvo, tipo, dif, extra_mod=0):
        """Faz um teste de resistência e anima o d20 do alvo no cliente."""
        extra_mod += self._save_weakness_pen(alvo, tipo)
        passou, d20, bonus, total = self._testar_save(alvo, tipo, dif, extra_mod=extra_mod)
        lab = {"reflexos": "Reflexos", "fortitude": "Fortitude", "vontade": "Vontade"}.get(tipo, tipo)
        await self._broadcast_dado("d20", d20, f"{lab} {'✓' if passou else '✗'}")
        return passou, d20, bonus, total
```

Substituir por:

```python
    async def _save_mostrado(self, alvo, tipo, dif, extra_mod=0, desvantagem=False):
        """Faz um teste de resistência e anima o d20 do alvo no cliente."""
        extra_mod += self._save_weakness_pen(alvo, tipo)
        passou, d20, bonus, total = self._testar_save(alvo, tipo, dif, extra_mod=extra_mod, desvantagem=desvantagem)
        lab = {"reflexos": "Reflexos", "fortitude": "Fortitude", "vontade": "Vontade"}.get(tipo, tipo)
        await self._broadcast_dado("d20", d20, f"{lab} {'✓' if passou else '✗'}")
        return passou, d20, bonus, total
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` nas seções [1]-[2], `FAIL=0`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): parâmetro desvantagem em _testar_save/_save_mostrado"
```

---

## Task 3: `alcance_bonus` roteado pelos 3 executores de dano/alcance

**Files:**
- Modify: `server.py:8620` (`_executar_magia_grimorio`, dispatch)
- Modify: `server.py:9776` (`_executar_bola_fogo`)
- Modify: `server.py:9895` (`_executar_relampago`)
- Modify: `server.py:9942` (`_executar_raio_congelante`)
- Test: `tools/test_guilda_fase3_espec.py`

- [ ] **Step 1: Escrever o teste (seção [3], falhando)**

Adicionar antes do rodapé de `main()`:

```python
    print("\n[3] alcance_bonus chega aos 3 executores (Raio Congelante)")
    r = setup()
    p = caster("mage"); p["pos"] = [0, 0]; r.players["h"] = p
    r.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [4, 0], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    magia = S.GRIMORIO["raio_congelante"]
    r._errs.clear()
    await r._executar_raio_congelante(p, magia, {"target_id": "m1"}, 1, 0, 0)
    check("sem alcance_bonus: fora do alcance recusado", any("alcance" in e.lower() for e in r._errs))
    check("sem alcance_bonus: HP intacto", r.monsters["m1"]["hp"] == 30)
    r._errs.clear()
    await r._executar_raio_congelante(p, magia, {"target_id": "m1"}, 1, 0, 1)
    check("com alcance_bonus=1: alcance suficiente, dano aplicado", r.monsters["m1"]["hp"] < 30)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` — `_executar_raio_congelante() takes 5 positional arguments but 6 were given`.

- [ ] **Step 3: Adicionar `alcance_bonus` ao dispatch de `_executar_magia_grimorio`**

Em `server.py`, localizar (perto da linha 8620):

```python
    async def _executar_magia_grimorio(self, caster, magia, data, dmg_mult=1, dur_bonus=0):
```

Substituir por:

```python
    async def _executar_magia_grimorio(self, caster, magia, data, dmg_mult=1, dur_bonus=0, alcance_bonus=0):
```

Localizar (perto da linha 8627-8635):

```python
        if mid == "bola_fogo":
            await self._executar_bola_fogo(caster, magia, data, dmg_mult, dur_bonus)

        elif mid == "relampago":
            await self._executar_relampago(caster, magia, data, dmg_mult)

        elif mid == "raio_congelante":
            await self._executar_raio_congelante(caster, magia, data, dmg_mult, dur_bonus)
```

Substituir por:

```python
        if mid == "bola_fogo":
            await self._executar_bola_fogo(caster, magia, data, dmg_mult, dur_bonus, alcance_bonus)

        elif mid == "relampago":
            await self._executar_relampago(caster, magia, data, dmg_mult, alcance_bonus)

        elif mid == "raio_congelante":
            await self._executar_raio_congelante(caster, magia, data, dmg_mult, dur_bonus, alcance_bonus)
```

- [ ] **Step 4: Adicionar `alcance_bonus` aos 3 executores**

Em `_executar_bola_fogo` (perto da linha 9776):

```python
    async def _executar_bola_fogo(self, caster, magia, data, dmg_mult, dur_bonus):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1)
```

Substituir por:

```python
    async def _executar_bola_fogo(self, caster, magia, data, dmg_mult, dur_bonus, alcance_bonus=0):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1) + alcance_bonus
```

Em `_executar_relampago` (perto da linha 9895):

```python
    async def _executar_relampago(self, caster, magia, data, dmg_mult):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1)
        save_dif  = self._dif_magia(caster, magia)
```

Substituir por:

```python
    async def _executar_relampago(self, caster, magia, data, dmg_mult, alcance_bonus=0):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1) + alcance_bonus
        save_dif  = self._dif_magia(caster, magia)
```

Em `_executar_raio_congelante` (perto da linha 9942):

```python
    async def _executar_raio_congelante(self, caster, magia, data, dmg_mult, dur_bonus):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1)
```

Substituir por:

```python
    async def _executar_raio_congelante(self, caster, magia, data, dmg_mult, dur_bonus, alcance_bonus=0):
        nivel     = caster.get("level", 1)
        bonus_int = mod(caster.get("int_", 10))
        alcance   = magia["alcance_base"] + magia["alcance_escala"] * (nivel - 1) + alcance_bonus
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` nas seções [1]-[3], `FAIL=0`.

- [ ] **Step 6: Rodar a suíte de magias para garantir que não regrediu nada**

Run: `python tools/test_magias_slots.py`
Expected: `PASS: N  FAIL: 0` (mesmo resultado de antes — `alcance_bonus=0` é o default, comportamento idêntico).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): parâmetro alcance_bonus em bola_fogo/relampago/raio_congelante"
```

---

## Task 4: Flags do jogador + reset de fim de turno

**Files:**
- Modify: `server.py:3522-3526` (dicionário inicial de `make_player`)
- Modify: `server.py:11371-11374` (reset de início/fim de turno)
- Test: `tools/test_guilda_fase3_espec.py`

- [ ] **Step 1: Escrever o teste (seção [4], falhando)**

Adicionar antes do rodapé de `main()`:

```python
    print("\n[4] Catálogo completo das 7 técnicas + flags iniciais do jogador")
    especificacao = {
        "tec_ex_aprimorar_magia":      (5, 180, 2, 2),
        "tec_ex_estender_magia":       (5, 180, 2, 2),
        "tec_ex_canalizacao_arcana":   (5, 180, 4, 4),
        "tec_ex_empoderar_magia":      (8, 280, 4, 4),
        "tec_ex_magia_geminada":       (8, 280, 6, 6),
        "tec_ex_canalizacao_perfeita": (8, 280, 4, 4),
        "tec_ex_magia_acelerada":      (10, 350, 6, 6),
    }
    for tid, (rec, preco, cf, cs) in especificacao.items():
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga {rec}", it and it["recarga_rodadas"] == rec)
        check(f"{tid} preco {preco}", it and it["preco"] == preco)
        check(f"{tid} custo {cf}/{cs}", it and it["custo_fome"] == cf and it["custo_sede"] == cs)
        check(f"{tid} classe = [mage, cleric]", it and set(it["classe"]) == {"mage", "cleric"})
        check(f"{tid} exclusiva=True", it and it["exclusiva"] is True)
    check("magia_geminada tem alvo qualquer_vivo",
          S.guild_item("tec_ex_magia_geminada").get("alvo") == "qualquer_vivo")
    p0 = caster("mage")
    for flag in ["tec_ex_aprimorar_armado", "tec_ex_estender_armado", "tec_ex_canalizacao_armado",
                 "tec_ex_empoderar_armado", "tec_ex_canalizacao_perfeita_armado", "tec_ex_acelerada_armado"]:
        check(f"flag inicial {flag} = False", p0[flag] is False)
    check("flag inicial tec_ex_geminada_alvo2_id = None", p0["tec_ex_geminada_alvo2_id"] is None)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` — `KeyError: 'tec_ex_aprimorar_armado'` (as entradas do catálogo já existem da Task 1, mas as flags do jogador não).

- [ ] **Step 3: Adicionar as flags no dicionário de `make_player`**

Em `server.py`, localizar (perto da linha 3522-3526):

```python
        # ── Metamagia do mago (Pedro) — inerte p/ outras classes ──
        # Magnitude BASE (escala com as especializações da Guilda — ver _resolver_metamagia):
        "aprimorar_ativo":   False,  # Aprimorar armada → +1 CD do save (base; II/III: +2/+3) (🍖-3 ao lançar)
        "estender_ativo":    False,  # Estender armada → +1 turno de duração (base; II/III: +2/+3) (🍖-3 💧-3)
        "fortalecer_ativo":  False,  # Fortalecer armada → dano ×1,25 (base; II/III: ×1,5/×2) (🍖-6 💧-6)
```

Substituir por (mantendo as 3 linhas originais e acrescentando o bloco novo):

```python
        # ── Metamagia do mago (Pedro) — inerte p/ outras classes ──
        # Magnitude BASE (escala com as especializações da Guilda — ver _resolver_metamagia):
        "aprimorar_ativo":   False,  # Aprimorar armada → +1 CD do save (base; II/III: +2/+3) (🍖-3 ao lançar)
        "estender_ativo":    False,  # Estender armada → +1 turno de duração (base; II/III: +2/+3) (🍖-3 💧-3)
        "fortalecer_ativo":  False,  # Fortalecer armada → dano ×1,25 (base; II/III: ×1,5/×2) (🍖-6 💧-6)
        # ── Técnicas Exclusivas da Guilda (Fase 3) — 2º slot, Mago/Clérigo ──
        # Independentes da Metamagia acima (podem empilhar); inerte p/ outras classes.
        "tec_ex_aprimorar_armado":              False,  # +1 CD do save na próxima magia
        "tec_ex_estender_armado":                False,  # +1 duração OU +1 alcance na próxima magia
        "tec_ex_canalizacao_armado":             False,  # próxima magia ignora Silêncio
        "tec_ex_empoderar_armado":                False,  # ×1,5 dano na próxima magia ofensiva
        "tec_ex_geminada_alvo2_id":              None,   # 2º alvo escolhido na ativação
        "tec_ex_canalizacao_perfeita_armado":    False,  # próximo save de alvo único com desvantagem
        "tec_ex_acelerada_armado":               False,  # próxima magia não gasta a ação principal
```

- [ ] **Step 4: Adicionar o reset de fim de turno**

Em `server.py`, localizar (perto da linha 11371-11374):

```python
        # metamagia do mago expira ao fim do turno (flags planas)
        p["aprimorar_ativo"]   = False
        p["estender_ativo"]    = False
        p["fortalecer_ativo"]  = False
```

Substituir por:

```python
        # metamagia do mago expira ao fim do turno (flags planas)
        p["aprimorar_ativo"]   = False
        p["estender_ativo"]    = False
        p["fortalecer_ativo"]  = False
        # técnicas exclusivas da Guilda (Fase 3) não usadas expiram ao fim do turno
        p["tec_ex_aprimorar_armado"] = False
        p["tec_ex_estender_armado"] = False
        p["tec_ex_canalizacao_armado"] = False
        p["tec_ex_empoderar_armado"] = False
        p["tec_ex_geminada_alvo2_id"] = None
        p["tec_ex_canalizacao_perfeita_armado"] = False
        p["tec_ex_acelerada_armado"] = False
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` nas seções [1]-[4], `FAIL=0`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): flags do jogador para as 7 técnicas exclusivas + reset de turno"
```

---

## Task 5: Helpers puros (dc/duração/alcance/dano/geminada)

**Files:**
- Modify: `server.py:4306` (logo após `_resolver_metamagia`)
- Test: `tools/test_guilda_fase3_espec.py`

- [ ] **Step 1: Escrever o teste (seção [5], falhando)**

Adicionar antes do rodapé de `main()`:

```python
    print("\n[5] Helpers puros da Fase 3")
    r = setup()
    magia_save = {"id": "x", "save": "vontade"}
    magia_sem_save = {"id": "y"}
    p = caster("mage")
    check("dc_bonus=0 sem armar", r._tec_ex_dc_bonus(p, magia_save) == 0)
    p["tec_ex_aprimorar_armado"] = True
    check("dc_bonus=1 armado + magia com save", r._tec_ex_dc_bonus(p, magia_save) == 1)
    check("dc_bonus=0 armado + magia sem save", r._tec_ex_dc_bonus(p, magia_sem_save) == 0)

    magia_dur = {"id": "z", "duracao": "1d4"}
    magia_sem_dur = {"id": "w", "alcance_base": 3, "alcance_escala": 1}
    p2 = caster("mage"); p2["tec_ex_estender_armado"] = True
    check("estender: +1 duração quando a magia tem duracao",
          r._tec_ex_dur_alcance_bonus(p2, magia_dur) == (1, 0))
    check("estender: +1 alcance quando a magia NÃO tem duracao",
          r._tec_ex_dur_alcance_bonus(p2, magia_sem_dur) == (0, 1))
    p3 = caster("mage")
    check("estender: (0,0) sem armar", r._tec_ex_dur_alcance_bonus(p3, magia_dur) == (0, 0))

    magia_dano = {"id": "k", "dano_por_nivel": "1d6"}
    p4 = caster("mage"); p4["tec_ex_empoderar_armado"] = True
    check("empoderar: ×1.5 em magia com dano", r._tec_ex_dmg_mult(p4, magia_dano) == 1.5)
    check("empoderar: ×1 em magia sem dano", r._tec_ex_dmg_mult(p4, magia_sem_dur) == 1)
    p5 = caster("mage")
    check("empoderar: ×1 sem armar", r._tec_ex_dmg_mult(p5, magia_dano) == 1)

    print("\n[5b] _geminada_alvo2_valido")
    r2 = setup()
    pc = caster("mage"); pc["pos"] = [0, 0]
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [2, 0]
    dead_ally = make_player("d", "Dan", "warrior", 2); dead_ally["alive"] = False; dead_ally["pos"] = [1, 0]
    monster = {"id": "m1", "name": "Alvo", "pos": [3, 0], "hp": 10, "max_hp": 10}
    dead_monster = {"id": "m2", "name": "Morto", "pos": [1, 0], "hp": 0, "max_hp": 10}
    magia_alvo_ofensiva = {"id": "raio_congelante", "tipo": "alvo", "alcance_base": 3, "alcance_escala": 1}
    magia_buff = {"id": "visao_escuro", "tipo": "buff_aliado", "alcance": 6}
    check("geminada: monstro vivo no alcance de magia ofensiva → válido",
          r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, monster))
    check("geminada: monstro morto → inválido",
          not r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, dead_monster))
    check("geminada: aliado num alvo ofensivo → inválido (tipo errado)",
          not r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, ally))
    check("geminada: aliado vivo no alcance de magia de buff → válido",
          r2._geminada_alvo2_valido(pc, magia_buff, ally))
    check("geminada: monstro num buff → inválido (tipo errado)",
          not r2._geminada_alvo2_valido(pc, magia_buff, monster))
    check("geminada: aliado morto → inválido",
          not r2._geminada_alvo2_valido(pc, magia_buff, dead_ally))
    far_monster = {"id": "m3", "name": "Longe", "pos": [10, 0], "hp": 10, "max_hp": 10}
    check("geminada: fora do alcance → inválido",
          not r2._geminada_alvo2_valido(pc, magia_alvo_ofensiva, far_monster))
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` — `AttributeError: 'GameRoom' object has no attribute '_tec_ex_dc_bonus'`.

- [ ] **Step 3: Implementar os 4 helpers**

Em `server.py`, localizar o fim de `_resolver_metamagia` (perto da linha 4306):

```python
            elif kind == "aprimorar":
                dc_bonus = self._aprimorar_bonus(p); mm_fome += cf; mm_sede += cs
                partes.append(f"Aprimorar (+{dc_bonus} CD)")
        return dmg_mult, dur_bonus, dc_bonus, mm_fome, mm_sede, partes, (len(candidatas) > teto)
```

Inserir logo depois (mantendo essas linhas intactas):

```python
    # ── Técnicas Exclusivas da Guilda (Fase 3, Mago/Clérigo) ────────────────────
    # Independentes da Metamagia acima: helpers puros lidos em handle_magia; os
    # bônus se SOMAM (dc/duração/alcance) ou multiplicam em cadeia (dano) com a
    # Metamagia do Mago, se ambas estiverem ativas no mesmo lançamento.
    def _tec_ex_dc_bonus(self, p, magia):
        """+1 na CD do save se Aprimorar Magia (Fase 3) estiver armada e a magia
        exigir teste de resistência."""
        return 1 if (p.get("tec_ex_aprimorar_armado") and "save" in magia) else 0

    def _tec_ex_dur_alcance_bonus(self, p, magia):
        """(dur_bonus, alcance_bonus) de Estender Magia (Fase 3): +1 rodada de
        duração se a magia tiver 'duracao', senão +1 quadrado de alcance."""
        if not p.get("tec_ex_estender_armado"):
            return 0, 0
        return (1, 0) if "duracao" in magia else (0, 1)

    def _tec_ex_dmg_mult(self, p, magia):
        """×1,5 de Empoderar Magia (Fase 3) se a magia causar dano."""
        return 1.5 if (p.get("tec_ex_empoderar_armado") and self._magia_tem_dano(magia)) else 1

    def _geminada_alvo2_valido(self, caster, magia, alvo2):
        """True se o 2º alvo da Magia Geminada é elegível: vivo, no alcance da
        magia a partir do caster, e do tipo certo (monstro p/ magia ofensiva
        'alvo', aliado p/ magia de buff 'alvo_aliado'/'buff_aliado')."""
        if not alvo2:
            return False
        vivo = alvo2["alive"] if self._eh_jogador(alvo2) else alvo2.get("hp", 0) > 0
        if not vivo:
            return False
        tipo = magia.get("tipo")
        if tipo == "alvo" and self._eh_jogador(alvo2):
            return False
        if tipo in ("alvo_aliado", "buff_aliado") and not self._eh_jogador(alvo2):
            return False
        alcance = magia.get("alcance")
        if alcance is None:
            nivel = caster.get("level", 1)
            alcance = magia.get("alcance_base", 0) + magia.get("alcance_escala", 0) * (nivel - 1)
        dist = max(abs(caster["pos"][0] - alvo2["pos"][0]), abs(caster["pos"][1] - alvo2["pos"][1]))
        return dist <= alcance
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` nas seções [1]-[5b], `FAIL=0`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): helpers puros das técnicas exclusivas (dc/duração/alcance/dano/geminada)"
```

---

## Task 6: `handle_usar_tecnica` — armar as 7 técnicas

**Files:**
- Modify: `server.py:4537-4565` (dentro de `handle_usar_tecnica`)
- Test: `tools/test_guilda_fase3_espec.py`

- [ ] **Step 1: Escrever o teste (seção [6], falhando)**

Adicionar antes do rodapé de `main()`:

```python
    print("\n[6] handle_usar_tecnica arma cada uma das 7 técnicas")
    for tid, flag, custo in [
        ("tec_ex_aprimorar_magia", "tec_ex_aprimorar_armado", (2, 2)),
        ("tec_ex_estender_magia", "tec_ex_estender_armado", (2, 2)),
        ("tec_ex_canalizacao_arcana", "tec_ex_canalizacao_armado", (4, 4)),
        ("tec_ex_empoderar_magia", "tec_ex_empoderar_armado", (4, 4)),
        ("tec_ex_canalizacao_perfeita", "tec_ex_canalizacao_perfeita_armado", (4, 4)),
        ("tec_ex_magia_acelerada", "tec_ex_acelerada_armado", (6, 6)),
    ]:
        r = setup(); r.current_pid = lambda: "h"
        p = caster("mage", tid_ex=tid); r.players["h"] = p
        f0, s0 = p["fome"], p["sede"]
        await r.handle_usar_tecnica("h", tid)
        check(f"{tid}: flag {flag} armada", p[flag] is True)
        check(f"{tid}: custo {custo}", p["fome"] == f0 - custo[0] and p["sede"] == s0 - custo[1])
        check(f"{tid}: recarga setada", r.tecnica_restante(p, tid) > 0)

    print("\n[6b] Magia Geminada — validação de alvo na ativação")
    r = setup(); r.current_pid = lambda: "h"
    p = caster("mage", tid_ex="tec_ex_magia_geminada"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1, 1]
    r.players["a"] = ally
    r._errs.clear()
    await r.handle_usar_tecnica("h", "tec_ex_magia_geminada", "h")
    check("geminada: recusa a si mesmo", any("você" in e.lower() for e in r._errs))
    check("geminada: flag não setada ao recusar", p["tec_ex_geminada_alvo2_id"] is None)
    r._errs.clear()
    dead = make_player("d", "Dan", "warrior", 2); dead["alive"] = False; dead["pos"] = [1, 1]
    r.players["d"] = dead
    await r.handle_usar_tecnica("h", "tec_ex_magia_geminada", "d")
    check("geminada: recusa alvo morto", any("vivo" in e.lower() for e in r._errs))
    await r.handle_usar_tecnica("h", "tec_ex_magia_geminada", "a")
    check("geminada: aceita aliado vivo", p["tec_ex_geminada_alvo2_id"] == "a")
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` — as flags continuam `False`/`None` porque `handle_usar_tecnica` não sabe despachar `efeito.tipo` `"tec_ex_*"` (cai no comentário `# (outros tipos/handlers chegam nas Fases 1-2)` sem fazer nada, mas ainda cobra custo/recarga — falha nas asserções de flag).

- [ ] **Step 3: Adicionar os 7 branches em `handle_usar_tecnica`**

Em `server.py`, localizar o fim do branch `"sorte"` (perto da linha 4537-4565):

```python
            else:
                await self.gm_say(f"🎲 **{p['name']}** tenta a Sorte de novo, mas erra outra vez!")
            p["ultimo_ataque_perdido"] = None
        # (outros tipos/handlers chegam nas Fases 1-2)
        p["fome"] -= item["custo_fome"]
```

Substituir por:

```python
            else:
                await self.gm_say(f"🎲 **{p['name']}** tenta a Sorte de novo, mas erra outra vez!")
            p["ultimo_ataque_perdido"] = None
        # ── Técnicas Exclusivas da Guilda (Fase 3, Mago/Clérigo) ────────────────
        elif ef.get("tipo") == "tec_ex_aprimorar":
            p["tec_ex_aprimorar_armado"] = True
        elif ef.get("tipo") == "tec_ex_estender":
            p["tec_ex_estender_armado"] = True
        elif ef.get("tipo") == "tec_ex_canalizacao_arcana":
            p["tec_ex_canalizacao_armado"] = True
        elif ef.get("tipo") == "tec_ex_empoderar":
            p["tec_ex_empoderar_armado"] = True
        elif ef.get("tipo") == "tec_ex_geminada":
            alvo2 = self.players.get(target_id) or self.monsters.get(target_id)
            vivo2 = alvo2 and (alvo2["alive"] if self._eh_jogador(alvo2) else alvo2.get("hp", 0) > 0)
            if not alvo2 or not vivo2 or target_id == pid:
                await self.send_to(pid, {"type": "error",
                    "msg": "Escolha um alvo vivo (não pode ser você)."}); return
            p["tec_ex_geminada_alvo2_id"] = target_id
        elif ef.get("tipo") == "tec_ex_canalizacao_perfeita":
            p["tec_ex_canalizacao_perfeita_armado"] = True
        elif ef.get("tipo") == "tec_ex_acelerada":
            p["tec_ex_acelerada_armado"] = True
        # (outros tipos/handlers chegam nas Fases 1-2)
        p["fome"] -= item["custo_fome"]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` nas seções [1]-[6b], `FAIL=0`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): handle_usar_tecnica arma as 7 técnicas exclusivas"
```

---

## Task 7: Integração completa em `handle_magia`

**Files:**
- Modify: `server.py:8531-8613` (`handle_magia`, reescrita completa da função)
- Modify: `server.py:9769-9773` (comentário de `_dif_magia`, cosmético)
- Modify: `server.py` (dentro de `_executar_raio_congelante`, chamada a `_save_mostrado`)
- Test: `tools/test_guilda_fase3_espec.py`

- [ ] **Step 1: Escrever o teste (seção [7], falhando)**

Adicionar antes do rodapé de `main()`:

```python
    print("\n[7] handle_magia: integração das 7 técnicas exclusivas")

    def _mk_caster_room(tid_ex, cls="mage"):
        rr = setup(); rr.current_pid = lambda: "h"; rr._is_turn = lambda pid: pid == "h"
        pp = caster(cls, tid_ex=tid_ex); pp["pos"] = [0, 0]; pp["action_done"] = False
        rr.players["h"] = pp
        return rr, pp

    async def _fixed_dano(n, d, *_a, **_k):
        return n * d   # cada dado no valor máximo — determinístico

    # [7a] Aprimorar Magia: soma +1 no _mm_dc_bonus lido por _dif_magia
    rr, pp = _mk_caster_room("tec_ex_aprimorar_magia")
    await rr.handle_usar_tecnica("h", "tec_ex_aprimorar_magia")
    rr.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    dc_vistos = []
    orig_dif = rr._dif_magia
    rr._dif_magia = lambda c, m: (dc_vistos.append(c.get("_mm_dc_bonus")), orig_dif(c, m))[1]
    await rr.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("aprimorar: _mm_dc_bonus=1 no momento do save", dc_vistos and dc_vistos[0] == 1)
    check("aprimorar: flag consumida após lançar", pp["tec_ex_aprimorar_armado"] is False)

    # [7a2] Empilha com a Metamagia do 1f (Mago): +1 (1f) + 1 (Fase 3) = 2
    rr2, pp2 = _mk_caster_room("tec_ex_aprimorar_magia")
    pp2["aprimorar_ativo"] = True
    await rr2.handle_usar_tecnica("h", "tec_ex_aprimorar_magia")
    rr2.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    dc_vistos2 = []
    orig_dif2 = rr2._dif_magia
    rr2._dif_magia = lambda c, m: (dc_vistos2.append(c.get("_mm_dc_bonus")), orig_dif2(c, m))[1]
    await rr2.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("aprimorar: empilha com Metamagia do 1f (1+1=2)", dc_vistos2 and dc_vistos2[0] == 2)

    # [7b] Estender Magia — caminho de duração (Visão no Escuro, círculo 2 → nível 3)
    rr3, pp3 = _mk_caster_room("tec_ex_estender_magia")
    pp3["level"] = 3
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1, 0]
    rr3.players["a"] = ally
    rr3._rolar_dado = lambda spec: 5
    await rr3.handle_usar_tecnica("h", "tec_ex_estender_magia")
    await rr3.handle_magia("h", {"magia_id": "visao_escuro", "target_id": "a"})
    check("estender: duração 5(base)+1(técnica)=6", ally["visao_escuro_rodadas"] == 6)

    # [7c] Estender Magia — caminho de alcance (Raio Congelante 1 casa além do alcance base)
    rr4, pp4 = _mk_caster_room("tec_ex_estender_magia")
    rr4.monsters = {"m1": {"id": "m1", "name": "Longe", "pos": [4, 0], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    await rr4.handle_usar_tecnica("h", "tec_ex_estender_magia")
    await rr4.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("estender: alcance+1 alcança alvo antes fora de alcance", rr4.monsters["m1"]["hp"] < 30)

    # [7d] Empoderar Magia — ×1,5 no dano
    rr5, pp5 = _mk_caster_room("tec_ex_empoderar_magia")
    rr5.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10}}
    rr5._rolar_dano_mostrado = _fixed_dano
    await rr5.handle_usar_tecnica("h", "tec_ex_empoderar_magia")
    await rr5.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    dano5 = 1000 - rr5.monsters["m1"]["hp"]
    rr6, pp6 = _mk_caster_room(None)
    rr6.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 1000, "max_hp": 1000, "ac": 10, "ca": 10}}
    rr6._rolar_dano_mostrado = _fixed_dano
    await rr6.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    dano6 = 1000 - rr6.monsters["m1"]["hp"]
    check("empoderar: dano ×1,5 vs sem técnica", dano5 == int(dano6 * 1.5 + 0.5))

    # [7e] Canalização Arcana — ignora Silêncio
    rr7, pp7 = _mk_caster_room("tec_ex_canalizacao_arcana")
    rr7._em_silencio = lambda pl: True
    rr7.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    rr7._errs.clear()
    await rr7.handle_usar_tecnica("h", "tec_ex_canalizacao_arcana")
    await rr7.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("canalização arcana: lança normalmente sob Silêncio",
          not any("silêncio" in e.lower() for e in rr7._errs))
    check("canalização arcana: dano aplicado", rr7.monsters["m1"]["hp"] < 30)

    rr8, pp8 = _mk_caster_room("tec_ex_canalizacao_arcana")
    rr8._em_silencio = lambda pl: True
    rr8.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    rr8._errs.clear()
    await rr8.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("sem canalização arcana: Silêncio bloqueia normalmente",
          any("silêncio" in e.lower() for e in rr8._errs))

    # [7f] Canalização Perfeita — desvantagem chega ao _save_mostrado
    rr9, pp9 = _mk_caster_room("tec_ex_canalizacao_perfeita")
    rr9.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    vistos_desv = []
    orig_save = rr9._save_mostrado
    async def spy_save(alvo, tipo, dif, extra_mod=0, desvantagem=False):
        vistos_desv.append(desvantagem)
        return await orig_save(alvo, tipo, dif, extra_mod=extra_mod, desvantagem=desvantagem)
    rr9._save_mostrado = spy_save
    await rr9.handle_usar_tecnica("h", "tec_ex_canalizacao_perfeita")
    await rr9.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("canalização perfeita: save do alvo pedido com desvantagem",
          vistos_desv and vistos_desv[0] is True)

    # [7g] Magia Geminada — aplica no 2º alvo também
    rr10, pp10 = _mk_caster_room("tec_ex_magia_geminada")
    rr10.monsters = {
        "m1": {"id": "m1", "name": "Alvo1", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10},
        "m2": {"id": "m2", "name": "Alvo2", "pos": [0, 2], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10},
    }
    await rr10.handle_usar_tecnica("h", "tec_ex_magia_geminada", "m2")
    await rr10.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("geminada: 1º alvo sofre dano", rr10.monsters["m1"]["hp"] < 30)
    check("geminada: 2º alvo também sofre dano", rr10.monsters["m2"]["hp"] < 30)
    check("geminada: flag consumida", pp10["tec_ex_geminada_alvo2_id"] is None)

    # [7h] Magia Acelerada — não consome a ação principal
    rr11, pp11 = _mk_caster_room("tec_ex_magia_acelerada")
    rr11.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    await rr11.handle_usar_tecnica("h", "tec_ex_magia_acelerada")
    await rr11.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("acelerada: action_done continua False", pp11["action_done"] is False)
    check("acelerada: flag consumida", pp11["tec_ex_acelerada_armado"] is False)
    rr12, pp12 = _mk_caster_room(None)
    rr12.monsters = {"m1": {"id": "m1", "name": "Alvo", "pos": [0, 1], "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    await rr12.handle_magia("h", {"magia_id": "raio_congelante", "target_id": "m1"})
    check("sem acelerada: action_done vira True normalmente", pp12["action_done"] is True)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `FAIL` em quase todas as subseções [7a]-[7h] (nenhum dos hooks foi ligado em `handle_magia`/`_executar_raio_congelante` ainda).

- [ ] **Step 3: Reescrever `handle_magia` por completo**

Em `server.py`, localizar a função inteira (perto da linha 8531-8613):

```python
    async def handle_magia(self, pid, data):
        """Lança uma magia do GRIMÓRIO (Pedro/mage, Lewis/cleric). Valida classe,
        elegibilidade, slots do círculo e custo de sobrevivência; despacha o efeito."""
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p["alive"]:
            return
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Sua classe não lança magias do grimório."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode lançar magias!"}); return
        if p.get("paralisado"):
            await self.send_to(pid, {"type": "error", "msg": "❄️ Você está paralisado e não pode lançar magias!"}); return
        if p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Você está dormindo e não pode lançar magias!"}); return
        if self._em_silencio(p):
            await self.send_to(pid, {"type": "error", "msg": "🔇 Você está numa área de Silêncio e não pode lançar magias!"}); return

        # ── Metamagia do mago (Pedro): Reflexa / Acelerar ─────────────────────
        is_mage = p.get("class_id") == "mage"

        # Ação principal (1 por turno).
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        magia_id = (data or {}).get("magia_id")
        magia = GRIMORIO.get(magia_id)
        if not magia:
            await self.send_to(pid, {"type": "error", "msg": "Magia desconhecida."}); return
        if magia_id not in p.get("magias_conhecidas", []):
            await self.send_to(pid, {"type": "error", "msg": f"{p['name']} não conhece {magia['nome']}."}); return
        if magia_id not in GRIMORIO_IMPLEMENTADAS:
            await self.send_to(pid, {"type": "error",
                "msg": f"{magia['icone']} {magia['nome']} ainda está em desenvolvimento."}); return

        # Custo do círculo: 1 SLOT do mesmo círculo (estrito). Ninguém usa MP.
        circulo = magia.get("circulo", "primeiro")
        if self._slots_disponiveis(p, circulo) <= 0:
            falta = self._proximo_slot_rodadas(p, circulo)
            extra = f" (volta em {falta} rodada{'s' if (falta or 0) != 1 else ''})" if falta is not None else ""
            await self.send_to(pid, {"type": "error",
                "msg": f"Sem slot de magia de {circulo} círculo{extra}."}); return

        # ── Metamagia (Pedro): Aprimorar (+1 CD do save) / Estender (+1 turno) /
        # Fortalecer (dano ×1,5). EMPILHÁVEIS; o custo em 🍖/💧 é pago AGORA e SÓ se
        # a habilidade tiver efeito nesta magia (tem dano / duração / teste). ─────
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

        # Cobra 1 SLOT do círculo + 🍖/💧 de sobrevivência.
        self._gastar_slot(p, circulo)
        p["fome"] = max(0, p.get("fome", 10) - 1)
        p["sede"] = max(0, p.get("sede", 10) - 1)
        self._verificar_estado_sobrevivencia(p)

        # Aprimorar: +1 na CD do save é lido por _dif_magia via flag temporária no caster.
        p["_mm_dc_bonus"] = dc_bonus
        await self._executar_magia_grimorio(p, magia, data or {}, dmg_mult, dur_bonus)
        p["_mm_dc_bonus"] = 0

        # Invisibilidade quebra ao lançar (a menos que a própria magia a tenha concedido agora).
        if p.get("invisivel_magico") and magia_id != "invisibilidade":
            p["invisivel_magico"] = False; p.pop("invisivel_magico_rodadas", None)
            await self.gm_say(f"🫥 **{p['name']}** revela-se ao lançar magia.")

        p["action_done"] = True
        await self.push_state()
```

Substituir pela função inteira abaixo (adiciona o bloco "Técnicas Exclusivas", o bypass de Silêncio, a Geminada e o desvio de `action_done` da Magia Acelerada; o resto é idêntico):

```python
    async def handle_magia(self, pid, data):
        """Lança uma magia do GRIMÓRIO (Pedro/mage, Lewis/cleric). Valida classe,
        elegibilidade, slots do círculo e custo de sobrevivência; despacha o efeito."""
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p["alive"]:
            return
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Sua classe não lança magias do grimório."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode lançar magias!"}); return
        if p.get("paralisado"):
            await self.send_to(pid, {"type": "error", "msg": "❄️ Você está paralisado e não pode lançar magias!"}); return
        if p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Você está dormindo e não pode lançar magias!"}); return
        # Canalização Arcana (Fase 3, técnica exclusiva): ignora Silêncio.
        if self._em_silencio(p) and not p.get("tec_ex_canalizacao_armado"):
            await self.send_to(pid, {"type": "error", "msg": "🔇 Você está numa área de Silêncio e não pode lançar magias!"}); return

        # ── Metamagia do mago (Pedro): Reflexa / Acelerar ─────────────────────
        is_mage = p.get("class_id") == "mage"

        # Ação principal (1 por turno).
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        magia_id = (data or {}).get("magia_id")
        magia = GRIMORIO.get(magia_id)
        if not magia:
            await self.send_to(pid, {"type": "error", "msg": "Magia desconhecida."}); return
        if magia_id not in p.get("magias_conhecidas", []):
            await self.send_to(pid, {"type": "error", "msg": f"{p['name']} não conhece {magia['nome']}."}); return
        if magia_id not in GRIMORIO_IMPLEMENTADAS:
            await self.send_to(pid, {"type": "error",
                "msg": f"{magia['icone']} {magia['nome']} ainda está em desenvolvimento."}); return

        # Custo do círculo: 1 SLOT do mesmo círculo (estrito). Ninguém usa MP.
        circulo = magia.get("circulo", "primeiro")
        if self._slots_disponiveis(p, circulo) <= 0:
            falta = self._proximo_slot_rodadas(p, circulo)
            extra = f" (volta em {falta} rodada{'s' if (falta or 0) != 1 else ''})" if falta is not None else ""
            await self.send_to(pid, {"type": "error",
                "msg": f"Sem slot de magia de {circulo} círculo{extra}."}); return

        # ── Metamagia (Pedro): Aprimorar (+1 CD do save) / Estender (+1 turno) /
        # Fortalecer (dano ×1,5). EMPILHÁVEIS; o custo em 🍖/💧 é pago AGORA e SÓ se
        # a habilidade tiver efeito nesta magia (tem dano / duração / teste). ─────
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

        # ── Técnicas Exclusivas da Guilda (Fase 3, Mago/Clérigo) ────────────────
        # Independentes da Metamagia acima: os bônus SE SOMAM/multiplicam se
        # ambas estiverem armadas no mesmo lançamento.
        tec_dc = self._tec_ex_dc_bonus(p, magia)
        tec_dur, alcance_bonus = self._tec_ex_dur_alcance_bonus(p, magia)
        tec_mult = self._tec_ex_dmg_mult(p, magia)
        dc_bonus  += tec_dc
        dur_bonus += tec_dur
        dmg_mult  *= tec_mult
        usou_acelerada = bool(p.get("tec_ex_acelerada_armado"))
        p["_tec_save_desvantagem"] = bool(p.get("tec_ex_canalizacao_perfeita_armado"))

        # Cobra 1 SLOT do círculo + 🍖/💧 de sobrevivência.
        self._gastar_slot(p, circulo)
        p["fome"] = max(0, p.get("fome", 10) - 1)
        p["sede"] = max(0, p.get("sede", 10) - 1)
        self._verificar_estado_sobrevivencia(p)

        # Aprimorar: +1 na CD do save é lido por _dif_magia via flag temporária no caster.
        p["_mm_dc_bonus"] = dc_bonus
        await self._executar_magia_grimorio(p, magia, data or {}, dmg_mult, dur_bonus, alcance_bonus)

        # Magia Geminada (Fase 3): reexecuta o mesmo efeito no 2º alvo, se elegível.
        # (_mm_dc_bonus/_tec_save_desvantagem seguem ativos — o 2º alvo recebe os
        # MESMOS bônus do 1º.)
        alvo2_id = p.get("tec_ex_geminada_alvo2_id")
        if alvo2_id and magia.get("tipo") in ("alvo", "alvo_aliado", "buff_aliado"):
            alvo2 = self.players.get(alvo2_id) or self.monsters.get(alvo2_id)
            if self._geminada_alvo2_valido(p, magia, alvo2):
                dados2 = dict(data or {}); dados2["target_id"] = alvo2_id
                await self._executar_magia_grimorio(p, magia, dados2, dmg_mult, dur_bonus, alcance_bonus)
                await self.gm_say(
                    f"👯 **{p['name']}** gemina **{magia['nome']}** em "
                    f"**{alvo2.get('name') or alvo2.get('nome')}**!")

        p["_mm_dc_bonus"] = 0
        p["_tec_save_desvantagem"] = False

        # Limpa as técnicas exclusivas armadas neste lançamento (consumidas).
        p["tec_ex_aprimorar_armado"] = False
        p["tec_ex_estender_armado"] = False
        p["tec_ex_canalizacao_armado"] = False
        p["tec_ex_empoderar_armado"] = False
        p["tec_ex_geminada_alvo2_id"] = None
        p["tec_ex_canalizacao_perfeita_armado"] = False
        p["tec_ex_acelerada_armado"] = False

        # Invisibilidade quebra ao lançar (a menos que a própria magia a tenha concedido agora).
        if p.get("invisivel_magico") and magia_id != "invisibilidade":
            p["invisivel_magico"] = False; p.pop("invisivel_magico_rodadas", None)
            await self.gm_say(f"🫥 **{p['name']}** revela-se ao lançar magia.")

        # Magia Acelerada (Fase 3): não gasta a ação principal deste turno.
        if not usou_acelerada:
            p["action_done"] = True
        await self.push_state()
```

- [ ] **Step 4: Passar `desvantagem` para o save de Raio Congelante**

Em `server.py`, dentro de `_executar_raio_congelante`, localizar:

```python
        # Fortitude evita a paralisação (não o dano).
        save_ok, *_ = await self._save_mostrado(alvo, "fortitude", self._dif_magia(caster, magia))
```

Substituir por:

```python
        # Fortitude evita a paralisação (não o dano). desvantagem: Canalização
        # Perfeita (Fase 3) — próximos executores de alvo único devem seguir o
        # mesmo padrão ao chamar _save_mostrado.
        save_ok, *_ = await self._save_mostrado(alvo, "fortitude", self._dif_magia(caster, magia),
                                                  desvantagem=caster.get("_tec_save_desvantagem", False))
```

- [ ] **Step 5: Atualizar o comentário de `_dif_magia` (cosmético, sem mudança de lógica)**

Em `server.py`, localizar (perto da linha 9769):

```python
    def _dif_magia(self, caster, magia):
        """Dificuldade para resistir: 8 + bônus de INT + círculo (1/2/3). Aprimorar
        Magia (Pedro) soma +1 via flag temporária `_mm_dc_bonus` setada em handle_magia."""
```

Substituir por:

```python
    def _dif_magia(self, caster, magia):
        """Dificuldade para resistir: 8 + bônus de INT + círculo (1/2/3). Soma o
        bônus temporário `_mm_dc_bonus`, setado em handle_magia a partir da
        Metamagia do Mago (1f) e/ou da técnica Aprimorar Magia da Guilda (Fase 3)."""
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_guilda_fase3_espec.py`
Expected: `PASS` em todas as seções [1]-[7h], `FAIL=0`.

- [ ] **Step 7: Rodar toda a suíte relevante (regressão)**

Run:
```bash
python tools/test_magias_slots.py
python tools/test_mago_espec.py
python tools/test_tecnicas_espec.py
python tools/test_guilda.py
```
Expected: `FAIL=0`/`FAIL: 0` em todos os 4 arquivos.

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_guilda_fase3_espec.py
git commit -m "feat(guilda): integra as 7 técnicas exclusivas em handle_magia"
```

---

## Task 8: Cliente — badge, dispatch da Geminada, remoção do TODO

**Files:**
- Modify: `game.js:1482-1505` (`_guildItemRow`)
- Modify: `game.js:9990-10044` (dispatch do botão do 4º slot)

- [ ] **Step 1: Badge "Exclusiva Mago/Clérigo" em `_guildItemRow`**

Em `game.js`, localizar (perto da linha 1482-1505):

```js
function _guildItemRow(i, owned, me){
  const lista = i.categoria === 'tecnica' ? (owned.tecnicas || []) : (owned.especializacoes || []);
  const has   = lista.includes(i.id);
  const reqOk = !i.requer || lista.includes(i.requer);
  const gold  = (me && me.gold) || 0;
  const custo = i.categoria === 'tecnica'
    ? ` · 🍖${i.custo_fome} 💧${i.custo_sede} · ⏱️${i.recarga_rodadas}r` : '';
  let action;
  if(has){
    action = `<span class="guild-owned">Possuído ✓</span>`;
  } else if(!reqOk){
    const reqNome = (GS.guildCatalogFor(me.class_id).find(x=>x.id===i.requer)||{}).nome || i.requer;
    action = `<span class="guild-locked">🔒 Requer ${reqNome}</span>`;
  } else {
    const can = gold >= i.preco;
    action = `<button class="guild-buy" ${can?'':'disabled'}
                title="${can?'':'Ouro insuficiente'}"
                onclick="GS.guildBuy('${i.id}')">Comprar 🪙${i.preco}</button>`;
  }
  return `<div class="guild-item${has?' is-owned':''}">
    <span class="gi-icon">${i.icon||'✨'}</span>
    <div class="gi-body"><b>${i.nome}</b><br><small>${i.desc||''}${custo}</small></div>
    ${action}</div>`;
}
```

Substituir por:

```js
function _guildItemRow(i, owned, me){
  const lista = i.categoria === 'tecnica' ? (owned.tecnicas || []) : (owned.especializacoes || []);
  const has   = lista.includes(i.id);
  const reqOk = !i.requer || lista.includes(i.requer);
  const gold  = (me && me.gold) || 0;
  const custo = i.categoria === 'tecnica'
    ? ` · 🍖${i.custo_fome} 💧${i.custo_sede} · ⏱️${i.recarga_rodadas}r` : '';
  const exclusivaBadge = i.exclusiva
    ? ' <b style="color:var(--gold);font-size:.7rem;">★ Exclusiva Mago/Clérigo</b>' : '';
  let action;
  if(has){
    action = `<span class="guild-owned">Possuído ✓</span>`;
  } else if(!reqOk){
    const reqNome = (GS.guildCatalogFor(me.class_id).find(x=>x.id===i.requer)||{}).nome || i.requer;
    action = `<span class="guild-locked">🔒 Requer ${reqNome}</span>`;
  } else {
    const can = gold >= i.preco;
    action = `<button class="guild-buy" ${can?'':'disabled'}
                title="${can?'':'Ouro insuficiente'}"
                onclick="GS.guildBuy('${i.id}')">Comprar 🪙${i.preco}</button>`;
  }
  return `<div class="guild-item${has?' is-owned':''}">
    <span class="gi-icon">${i.icon||'✨'}</span>
    <div class="gi-body"><b>${i.nome}</b>${exclusivaBadge}<br><small>${i.desc||''}${custo}</small></div>
    ${action}</div>`;
}
```

- [ ] **Step 2: Dispatch do botão do 4º slot — `qualquer_vivo` + remoção do TODO**

Em `game.js`, localizar (perto da linha 9990-10001):

```js
  // ── Técnica(s) da Guilda equipada(s) (Fase 0) — 4º slot com recarga em rodadas ──
  const _tecEq  = GS.guildEquipOf(me.id);
  const _tecIds = [_tecEq.tecnica, _tecEq.tecnica_exclusiva].filter(Boolean);
  for(const tid of _tecIds){
    const cat = GS.guildCatalogFor(me.class_id).find(x => x.id === tid);
    if(!cat) continue;
    const restante = GS.tecnicaRestante(me, tid);
    // TODO(Fase 3): quando existirem técnicas exclusivas equipadas simultaneamente com uma automática,
    // podeUsar também deve checar 'GS.myPid !== state.last_stand_pid' (hoje inalcançável: nenhuma
    // técnica tem exclusiva:True ainda, então o slot exclusivo nunca fica ocupado — GS.isMyTurn já
    // inclui a janela de Último Esforço, que hoje só existe para a técnica automática).
    const podeUsar = !cat.automatica && GS.isMyTurn && me.alive && state.phase === 'playing'
                     && restante === 0
                     && (me.fome||0) >= (cat.custo_fome||0) && (me.sede||0) >= (cat.custo_sede||0);
```

Substituir por:

```js
  // ── Técnica(s) da Guilda equipada(s) (Fase 0) — 4º slot com recarga em rodadas ──
  const _tecEq  = GS.guildEquipOf(me.id);
  const _tecIds = [_tecEq.tecnica, _tecEq.tecnica_exclusiva].filter(Boolean);
  for(const tid of _tecIds){
    const cat = GS.guildCatalogFor(me.class_id).find(x => x.id === tid);
    if(!cat) continue;
    const restante = GS.tecnicaRestante(me, tid);
    // Fase 3: técnicas exclusivas usam o mesmo podeUsar de qualquer técnica —
    // GS.isMyTurn já cobre a janela do Último Esforço, e decidimos (brainstorming)
    // NÃO bloquear o uso de técnicas da Guilda durante esses mini-turnos.
    const podeUsar = !cat.automatica && GS.isMyTurn && me.alive && state.phase === 'playing'
                     && restante === 0
                     && (me.fome||0) >= (cat.custo_fome||0) && (me.sede||0) >= (cat.custo_sede||0);
```

Localizar, mais abaixo (perto da linha 10032-10041):

```js
      } else if(cat.alvo === 'aliado'){
        // Ataque Coordenado (Fase 2c): marca um aliado vivo (qualquer distância) como par.
        const alvos = (state.players||[]).filter(q => q && q.alive && q.id !== me.id);
        if(!alvos.length){ toast('Nenhum aliado disponível.', 'var(--orange)'); return; }
        if(alvos.length === 1){ GS.usarTecnica(tid, alvos[0].id); return; }
        openTargetModal(`${cat.icon||'⚔️'} ${cat.nome} — escolha o par`, alvos, 'player',
          id => GS.usarTecnica(tid, id));
      } else {
        GS.usarTecnica(tid);
      }
    };
```

Substituir por:

```js
      } else if(cat.alvo === 'aliado'){
        // Ataque Coordenado (Fase 2c): marca um aliado vivo (qualquer distância) como par.
        const alvos = (state.players||[]).filter(q => q && q.alive && q.id !== me.id);
        if(!alvos.length){ toast('Nenhum aliado disponível.', 'var(--orange)'); return; }
        if(alvos.length === 1){ GS.usarTecnica(tid, alvos[0].id); return; }
        openTargetModal(`${cat.icon||'⚔️'} ${cat.nome} — escolha o par`, alvos, 'player',
          id => GS.usarTecnica(tid, id));
      } else if(cat.alvo === 'qualquer_vivo'){
        // Magia Geminada (Fase 3): 2º alvo pode ser aliado OU monstro, qualquer
        // distância (o servidor valida alcance/tipo na hora de lançar a magia).
        const aliados  = (state.players||[]).filter(q => q && q.alive && q.id !== me.id);
        const monstros = (state.monsters||[]).filter(m => m && m.hp>0);
        const alvos = [...aliados, ...monstros];
        if(!alvos.length){ toast('Nenhum alvo disponível.', 'var(--orange)'); return; }
        openTargetModal(`${cat.icon||'⚔️'} ${cat.nome} — escolha o 2º alvo`, alvos, 'any',
          id => GS.usarTecnica(tid, id));
      } else {
        GS.usarTecnica(tid);
      }
    };
```

- [ ] **Step 3: Verificação manual (não há harness de teste JS neste projeto)**

Rodar `iniciar.bat`, abrir o navegador, criar uma sala, selecionar Pedro (mage) e Lewis (cleric), ir até a cidade e abrir a Guilda (`openGuild`):
- Confirmar que as 7 técnicas aparecem nas faixas "Recarga Média/Longa/Muito Longa" com o selo "★ Exclusiva Mago/Clérigo".
- Comprar `Aprimorar Magia` com Pedro, equipar no slot exclusivo pela ficha, entrar na masmorra e conferir que o 4º botão aparece rotulado "GUILDA".
- Comprar/equipar `Magia Geminada`, clicar no botão do 4º slot e confirmar que abre o modal combinando aliados e monstros.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(guilda): cliente — badge exclusiva, modal da Geminada, remove TODO resolvido"
```

---

## Task 9: Documentação (CLAUDE.md) + regressão final

**Files:**
- Modify: `CLAUDE.md` (novo parágrafo blockquote no fim, seguindo o padrão das fases anteriores)

- [ ] **Step 1: Adicionar o parágrafo da Fase 3 no fim de `CLAUDE.md`**

Ao final do arquivo `CLAUDE.md` (depois do último parágrafo, "Técnicas de Recarga Longa (Fase 2e)"), adicionar:

```markdown

> **Técnicas Exclusivas (Fase 3 — Mago/Clérigo):** primeiro uso real do 2º slot
> (`tecnica_exclusiva`), reservado desde a Fase 0 mas nunca ocupado até agora.
> 7 técnicas (`categoria:"tecnica"`, `classe:["mage","cleric"]`, `exclusiva:True`)
> que aprimoram a **próxima magia** lançada — mesmo padrão "arma e age" das
> demais técnicas, mas rodando dentro de `handle_magia` em vez de `handle_attack`.
> **Recarga 5 (180🪙/2🍖2💧):** Aprimorar Magia (+1 CD do save), Estender Magia
> (+1 duração se a magia tiver `duracao`, senão +1 alcance), Canalização Arcana
> (ignora Silêncio — "não pode ser interrompida" fica inerte, sem mecanismo de
> interrupção de magia no jogo). **Recarga 8 (280🪙/4🍖4💧, exceto Geminada
> 6🍖6💧):** Empoderar Magia (×1,5 dano ofensivo), Magia Geminada (2º alvo
> escolhido **na ativação** — modal combinado aliado+monstro, `alvo:
> "qualquer_vivo"` — reexecuta o mesmo efeito nele se elegível: vivo, no
> alcance, e do tipo certo pro `tipo` da magia), Canalização Perfeita (o alvo
> testa resistência com desvantagem). **Recarga 10 (350🪙/6🍖6💧):** Magia
> Acelerada (a magia não marca `action_done` — libera a ação principal do
> turno). Todas **independentes** da Metamagia do Mago (Fase 1f, toggle
> permanente e gratuito): os bônus de Aprimorar/Estender se somam e os
> multiplicadores de dano (Empoderar/Fortalecer) multiplicam em cadeia se
> ambos estiverem ativos no mesmo lançamento — decisão de brainstorming, para
> não duplicar a lógica dos toggles existentes nem criar uma relação de
> exclusividade sem necessidade real de design. Duas generalizações
> retrocompatíveis: `classe` no catálogo passa a aceitar lista (`_guild_classe_ok`,
> usado em `guild_items_for_class`/`handle_guild_buy`; `guildCatalogFor` no
> cliente ganha o mesmo `Array.isArray`); `_testar_save`/`_save_mostrado` ganham
> `desvantagem` (rola 2d20, usa o pior — só chega a `_executar_raio_congelante`
> hoje, a única magia de alvo único com save implementada; os próximos
> executores de alvo único devem seguir o mesmo padrão). Interação com o
> Último Esforço (Fase 2e): decidido em brainstorming **não bloquear** — o TODO
> deixado em `game.js` foi resolvido sem nova restrição, já que `GS.isMyTurn`
> já cobre a janela do Último Esforço. Cliente: badge "★ Exclusiva Mago/Clérigo"
> em `_guildItemRow`; nenhuma seção nova na UI (as 7 técnicas caem nas faixas de
> recarga já existentes). Teste: `tools/test_guilda_fase3_espec.py`.
```

- [ ] **Step 2: Rodar a suíte completa do projeto**

Run (a partir da raiz):
```bash
python tools/test_guilda_fase3_espec.py
python tools/test_guilda.py
python tools/test_mago_espec.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_guerreiro_espec.py
python tools/test_ladino_espec.py
python tools/test_bardo_espec.py
python tools/test_reviver_mortos.py
python tools/test_tecnicas_espec.py
python tools/test_magias_slots.py
```
Expected: `FAIL=0`/`FAIL: 0` em todos os arquivos.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(guilda): documenta a Fase 3 (Técnicas Exclusivas) no CLAUDE.md"
```
