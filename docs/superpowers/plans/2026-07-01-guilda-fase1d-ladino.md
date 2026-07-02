# Guilda — Fase 1d (Especializações do Ladino) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesenhar o Ataque Furtivo (base restrito + reação Suprema), tornar as Fórmulas de Armadilha extensíveis e vendáveis, e gatear Desarme/Veneno Rápido/Esconder nas Sombras — 5 linhas, 15 nós na Guilda.

**Architecture:** Servidor autoritativo, estilo imperativo das fases anteriores: 8 nós literais no `GUILD_CATALOG` (Furtivo/Desarme/Veneno/Esconder) + 7 nós **gerados dinamicamente** a partir de novos campos em `ARMADILHAS` (Fórmulas — extensível para armadilhas futuras sem tocar no catálogo). Helpers testáveis lidos por `tem_espec` nos handlers do Luccas. Duas mudanças estruturais reais: (1) reação automática do Furtivo Supremo hookada em `handle_attack`/`handle_throw`; (2) Veneno Rápido ganha um 2º slot (`weapon_poison_2`).

**Tech Stack:** Python 3 + `websockets` (servidor); Vanilla JS (cliente). Testes no harness caseiro (`tools/test_*.py`), **não** pytest.

**Spec:** `docs/superpowers/specs/2026-07-01-guilda-fase1d-ladino-design.md`

---

## Contexto de código (anchors confirmados — localizar por conteúdo, linhas podem deslocar)

- `GUILD_CATALOG = {` (~server.py:279) fecha em `# Fases 1-2 acrescentam aqui.` seguido de `}` (~420-421). `guild_item`/`guild_items_for_class`/`tem_espec` vêm logo depois (~423+).
- `ARMADILHAS = {` (~2333) — 8 tipos: `buraco`, `armadilha_urso`, `fosso_estacas`, `rede`, `armadilha_incendiaria`, `mina_terrestre`, `fosso_envenenado`, `nuvem_gas`.
- `make_player`: `"weapon_poison": None,` / `"weapon_poison_hits": 0,` (~3154-3155).
- `self.round_num = 1` (~3457); `self.temp_def = {}` (~3468, já expira sozinho em 1 turno — ver ~10376-10382).
- `_dados_furtivo(self, nivel)` (~4936); `_verificar_ataque_furtivo(self, luccas, alvo)` (~4942); `_quebrar_invisibilidade(self, p, motivo="ao agir")` (~4955), chamado só em `handle_attack` ("ao atacar").
- `handle_attack`: bloco furtivo passivo (~5218-5227) → `target["hp"] -= dmg` (~5228) → `gm_say` → dano de projétil incendiário → `if target["hp"] <= 0: _monster_dies`. Bloco de veneno melee: `elif p.get("weapon_poison"): ... p["weapon_poison_hits"] -= 1 ...` (~5249-5255).
- `handle_throw` (~5335): outro caminho de ataque de jogador (arremesso de adaga) com seu próprio `target["hp"] -= dmg` (~5428) → `if target["hp"] <= 0: _monster_dies`.
- **Fora de escopo desta fase** (decisão de escopo, YAGNI): outros caminhos de dano a monstro (ataque de mão secundária/offhand ~5297, arremesso de lança, animados controlados ~5924 dentro de `handle_comandar_animados`, dano de magia) **não** disparam a reação do Furtivo Supremo — só `handle_attack` (mão principal) e `handle_throw`.
- `handle_criar_armadilha` (~9553): `tipo = ARMADILHAS.get(tipo_id)` (~9566), seguido de checagem de ouro/fome/sede.
- `handle_desarmar_armadilha` (~9767): `total = d20 + bonus` (~9787, `bonus = mod(DES)`); sucesso remove a armadilha sem recuperação.
- `handle_esconder_sombras` (~9882): ação bônus, `total = d20 + bonus_dex` (~9787... na verdade dentro desta função, ~9914), seta `p["bonus_action_used"] = True`.
- `handle_veneno_rapido` (~9947): monta `cargas = VENENO_CARGAS if _is_ranged else 1`, seta `p["weapon_poison"]`/`p["weapon_poison_hits"]`.

**Setup de teste** (`tools/test_ladino_espec.py`):
```python
"""Especializações do Ladino (Fase 1d). Roda da raiz: python tools/test_ladino_espec.py"""
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

def rogue(**owned):
    p = make_player("l", "Luccas", "rogue", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]
    return p

def monster(mid="m1", pos=(0,1), hp=20):
    return {"id": mid, "name": "Goblin", "pos": list(pos), "hp": hp, "max_hp": hp, "ac": 10}
```

---

## Task 1: Catálogo — 8 nós literais (Furtivo, Desarme, Veneno, Esconder)

**Files:** Modify `server.py`; Create `tools/test_ladino_espec.py`.

- [ ] **Step 1: Criar `tools/test_ladino_espec.py`** com o cabeçalho/`setup`/`rogue`/`monster` acima e este `main()`:
```python
async def main():
    # [1] Catálogo — 8 nós literais
    print("\n[1] Catálogo do Ladino (literais)")
    ids = [i["id"] for i in S.guild_items_for_class("rogue")]
    for eid in ["ladino_furtivo_2","ladino_furtivo_3","ladino_desarme_2","ladino_desarme_3",
                "ladino_veneno_2","ladino_veneno_3","ladino_esconder_2","ladino_esconder_3"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("furtivo_3 requer furtivo_2", S.guild_item("ladino_furtivo_3")["requer"] == "ladino_furtivo_2")
    check("desarme_2 sem requer", S.guild_item("ladino_desarme_2")["requer"] is None)
    check("veneno_3 requer veneno_2", S.guild_item("ladino_veneno_3")["requer"] == "ladino_veneno_2")
    check("esconder_3 requer esconder_2", S.guild_item("ladino_esconder_3")["requer"] == "ladino_esconder_2")
    check("preço II = 150", S.guild_item("ladino_furtivo_2")["preco"] == 150)
    check("preço III = 200", S.guild_item("ladino_esconder_3")["preco"] == 200)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```
(Manter summary/`sys.exit` no fim; tasks seguintes inserem blocos antes.)

- [ ] **Step 2: Rodar — MUST fail.** `python tools/test_ladino_espec.py`

- [ ] **Step 3: Adicionar as 8 entradas ao `GUILD_CATALOG`** — trocar
```python
    # Fases 1-2 acrescentam aqui.
}
```
por
```python
    "ladino_furtivo_2": { "id":"ladino_furtivo_2","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_furtivo","nivel":2,"requer":None,"exclusiva":False,"preco":150,
        "nome":"Ataque Furtivo II","icon":"🗡️",
        "desc":"Ataque Furtivo também dispara se há aliado adjacente ao alvo." },
    "ladino_furtivo_3": { "id":"ladino_furtivo_3","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_furtivo","nivel":3,"requer":"ladino_furtivo_2","exclusiva":False,"preco":200,
        "nome":"Ataque Furtivo Supremo","icon":"🗡️",
        "desc":"1×/inimigo/rodada: quando um aliado acerta um inimigo, Luccas reage com um Ataque Furtivo nele." },
    "ladino_desarme_2": { "id":"ladino_desarme_2","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_desarme","nivel":2,"requer":None,"exclusiva":False,"preco":150,
        "nome":"Desarme II","icon":"🔧","desc":"+2 na chance de desarmar armadilhas." },
    "ladino_desarme_3": { "id":"ladino_desarme_3","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_desarme","nivel":3,"requer":"ladino_desarme_2","exclusiva":False,"preco":200,
        "nome":"Desarme III","icon":"🔧","desc":"Chance extra de recuperar o ouro da armadilha desarmada." },
    "ladino_veneno_2": { "id":"ladino_veneno_2","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_veneno","nivel":2,"requer":None,"exclusiva":False,"preco":150,
        "nome":"Veneno Rápido II","icon":"☠️","desc":"O veneno na arma (corpo a corpo) dura 2 golpes certeiros." },
    "ladino_veneno_3": { "id":"ladino_veneno_3","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_veneno","nivel":3,"requer":"ladino_veneno_2","exclusiva":False,"preco":200,
        "nome":"Veneno Rápido III","icon":"☠️","desc":"Pode manter 2 venenos diferentes na arma ao mesmo tempo." },
    "ladino_esconder_2": { "id":"ladino_esconder_2","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_esconder","nivel":2,"requer":None,"exclusiva":False,"preco":150,
        "nome":"Esconder nas Sombras II","icon":"🌑","desc":"+2 na chance de se esconder nas sombras." },
    "ladino_esconder_3": { "id":"ladino_esconder_3","categoria":"especializacao","classe":"rogue",
        "linha":"ladino_esconder","nivel":3,"requer":"ladino_esconder_2","exclusiva":False,"preco":200,
        "nome":"Esconder nas Sombras III","icon":"🌑",
        "desc":"Ativar não gasta mais a ação bônus. Ao ser revelado, +2 de CA por 1 rodada." },
    # Fases 1-2 acrescentam aqui.
}
```

- [ ] **Step 4: Rodar — MUST pass.**

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): catalogo literal do Ladino (Furtivo/Desarme/Veneno/Esconder)"
```

---

## Task 2: Catálogo — Fórmulas de Armadilha (extensível, gerado a partir de `ARMADILHAS`)

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [2] Fórmulas de armadilha (geradas)
    print("\n[2] Fórmulas de armadilha")
    ids = [i["id"] for i in S.guild_items_for_class("rogue")]
    for eid, preco in [("ladino_armadilha_urso",100), ("ladino_fosso_estacas",120),
                        ("ladino_fosso_envenenado",130), ("ladino_rede",150),
                        ("ladino_armadilha_incendiaria",180), ("ladino_mina_terrestre",220),
                        ("ladino_nuvem_gas",250)]:
        check(f"catálogo tem {eid}", eid in ids)
        check(f"{eid} preço {preco}", S.guild_item(eid)["preco"] == preco)
    check("buraco não vira nó de compra", "ladino_buraco" not in ids and
          not any(v.get("nome","").endswith("Buraco") for v in S.GUILD_CATALOG.values()))
```

- [ ] **Step 2: Rodar — MUST fail** (as entradas geradas ainda não existem).

- [ ] **Step 3: Adicionar `formula_guild_id`/`formula_preco` a 7 das 8 entradas de `ARMADILHAS`.**
`ARMADILHAS = {` já existe com 8 tipos; adicionar os dois campos novos a cada um (exceto `buraco`, que fica sem eles). Localizar cada bloco pelo nome e acrescentar as duas chaves dentro do dict, por exemplo para `armadilha_urso`:
```python
    "armadilha_urso": {
        "nome": "Armadilha de Urso", "icone": "🪤", "dificuldade": 10, "save": "reflexos",
        "custo_ouro": 1, "persiste": False,
        "efeitos": [{"tipo": "dano", "valor": "1d4", "elemento": "fisico"},
                    {"tipo": "perder_movimento"}],
        "descricao": "1d4 de dano + perde movimento. Some após ativar.",
        "formula_guild_id": "ladino_armadilha_urso", "formula_preco": 100,
    },
```
Repetir o mesmo padrão (adicionar as 2 chaves ao final do dict, antes do `},` de fechamento) para:
- `fosso_estacas` → `"formula_guild_id": "ladino_fosso_estacas", "formula_preco": 120,`
- `rede` → `"formula_guild_id": "ladino_rede", "formula_preco": 150,`
- `armadilha_incendiaria` → `"formula_guild_id": "ladino_armadilha_incendiaria", "formula_preco": 180,`
- `mina_terrestre` → `"formula_guild_id": "ladino_mina_terrestre", "formula_preco": 220,`
- `fosso_envenenado` → `"formula_guild_id": "ladino_fosso_envenenado", "formula_preco": 130,`
- `nuvem_gas` → `"formula_guild_id": "ladino_nuvem_gas", "formula_preco": 250,`

`buraco` **não** recebe esses campos (fica sempre grátis).

- [ ] **Step 4: Gerar as entradas no `GUILD_CATALOG` a partir de `ARMADILHAS`.**
Logo após a função `guild_items_for_class` (que já existe perto de `guild_item`, após o fechamento do `GUILD_CATALOG` literal ~linha 423+), adicionar:
```python
def _gerar_catalogo_formulas_armadilha():
    """Gera entradas de compra para cada tipo de ARMADILHAS que tiver
    formula_guild_id — extensível: armadilhas futuras só precisam desses
    2 campos para aparecerem automaticamente na Guilda."""
    entradas = {}
    for tipo_id, tipo in ARMADILHAS.items():
        gid = tipo.get("formula_guild_id")
        if not gid:
            continue
        entradas[gid] = {
            "id": gid, "categoria": "especializacao", "classe": "rogue",
            "linha": "ladino_armadilhas", "nivel": None, "requer": None, "exclusiva": False,
            "preco": tipo.get("formula_preco", 100),
            "nome": f"Fórmula: {tipo['nome']}", "icon": tipo.get("icone", "🪤"),
            "desc": f"Desbloqueia permanentemente a fabricação de {tipo['nome']}.",
        }
    return entradas

GUILD_CATALOG.update(_gerar_catalogo_formulas_armadilha())
```
**Ordem importa:** `ARMADILHAS` (definido ~linha 2333) precisa existir ANTES desta chamada. Como `GUILD_CATALOG` é definido ~linha 279 (antes de `ARMADILHAS`), o `GUILD_CATALOG.update(...)` deve ser colocado **depois** da definição de `ARMADILHAS` (~linha 2389, logo após o `}` que fecha `ARMADILHAS`), não junto dos outros helpers de guilda. Colocar `_gerar_catalogo_formulas_armadilha` e a chamada `GUILD_CATALOG.update(...)` imediatamente após o fechamento de `ARMADILHAS`.

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): catalogo extensivel de Formulas de Armadilha (gerado de ARMADILHAS)"
```

---

## Task 3: Ataque Furtivo — redesign do base (gate "aliado adjacente")

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [3] Ataque Furtivo — base vs II
    print("\n[3] Ataque Furtivo base/II")
    r = setup()
    luccas = rogue(); luccas["pos"] = [0,0]; r.players["l"] = luccas
    aliado = make_player("a", "Ana", "warrior", 1); aliado["pos"] = [1,1]; aliado["alive"] = True; r.players["a"] = aliado
    alvo = monster(pos=(1,1))
    check("base: sem oculto e sem furtivo_2 → False", not r._verificar_ataque_furtivo(luccas, alvo))
    luccas["invisivel_sombras"] = True
    check("base: oculto → True", r._verificar_ataque_furtivo(luccas, alvo))
    luccas["invisivel_sombras"] = False
    luccas["guild_owned"]["especializacoes"] = ["ladino_furtivo_2"]
    check("com furtivo_2: aliado adjacente ao alvo → True", r._verificar_ataque_furtivo(luccas, alvo))
```

- [ ] **Step 2: Rodar — MUST fail** (hoje `_verificar_ataque_furtivo` retorna True mesmo sem `ladino_furtivo_2`).

- [ ] **Step 3: Gatear `_verificar_ataque_furtivo`.** Trocar:
```python
    def _verificar_ataque_furtivo(self, luccas, alvo):
        """True se Luccas estiver invisível nas sombras, oculto pela Vela da
        Escuridão, OU houver um aliado vivo (jogador) adjacente — Chebyshev — ao alvo."""
        if luccas.get("invisivel_sombras") or luccas.get("oculto_vela"):
            return True
        ax, ay = alvo["pos"]
        for pid2, aliado in self.players.items():
            if pid2 == luccas["id"] or not aliado["alive"]:
                continue
            if max(abs(aliado["pos"][0] - ax), abs(aliado["pos"][1] - ay)) <= 1:
                return True
        return False
```
por:
```python
    def _verificar_ataque_furtivo(self, luccas, alvo):
        """True se Luccas estiver invisível nas sombras/oculto (base), OU (com
        ladino_furtivo_2) houver um aliado vivo (jogador) adjacente — Chebyshev
        — ao alvo."""
        if luccas.get("invisivel_sombras") or luccas.get("oculto_vela"):
            return True
        if not tem_espec(luccas, "ladino_furtivo_2"):
            return False
        ax, ay = alvo["pos"]
        for pid2, aliado in self.players.items():
            if pid2 == luccas["id"] or not aliado["alive"]:
                continue
            if max(abs(aliado["pos"][0] - ax), abs(aliado["pos"][1] - ay)) <= 1:
                return True
        return False
```

- [ ] **Step 4: Rodar — MUST pass** + regressão `python tools/test_devorador.py` (anote — o furtivo passivo do Luccas fica mais restrito por padrão; verificar que nada mais depende do comportamento antigo).

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): Ataque Furtivo base restrito a oculto; aliado adjacente exige furtivo_2"
```

---

## Task 4: Ataque Furtivo Supremo — reação automática (`_furtivo_reativo`)

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [4] Ataque Furtivo Supremo (reação)
    print("\n[4] Furtivo Supremo — reação")
    _orig_rand = S.random.randint; S.random.randint = lambda a,b: 4  # dado fixo=4
    try:
        # aliado (warrior) ataca e Luccas (com furtivo_3) reage
        r = setup(); r.round_num = 1
        luccas = rogue(esp=["ladino_furtivo_2","ladino_furtivo_3"]); luccas["pos"]=[5,5]; r.players["l"]=luccas
        aliado = make_player("a","Ana","warrior",1); aliado["pos"]=[0,0]; r.players["a"]=aliado
        alvo = monster(hp=20)
        await r._furtivo_reativo(aliado, alvo)
        check("reação aplica dano (2d4 nível 1 = 8)", alvo["hp"] == 12)
        # 2ª vez no MESMO alvo na MESMA rodada não dispara de novo
        await r._furtivo_reativo(aliado, alvo)
        check("não reage 2x no mesmo alvo na mesma rodada", alvo["hp"] == 12)
        # nova rodada libera de novo
        r.round_num = 2
        await r._furtivo_reativo(aliado, alvo)
        check("nova rodada libera a reação de novo", alvo["hp"] == 4)
        # Luccas atacando não dispara nele mesmo
        r2 = setup(); r2.round_num = 1
        luccas2 = rogue(esp=["ladino_furtivo_3"]); luccas2["pos"]=[0,0]; r2.players["l"]=luccas2
        alvo2 = monster(hp=20)
        await r2._furtivo_reativo(luccas2, alvo2)
        check("não reage ao próprio ataque de Luccas", alvo2["hp"] == 20)
        # alvo já morto não recebe reação
        r3 = setup(); r3.round_num = 1
        luccas3 = rogue(esp=["ladino_furtivo_3"]); luccas3["pos"]=[5,5]; r3.players["l"]=luccas3
        aliado3 = make_player("a","Ana","warrior",1); aliado3["pos"]=[0,0]; r3.players["a"]=aliado3
        alvo3 = monster(hp=0)
        await r3._furtivo_reativo(aliado3, alvo3)
        check("não reage a alvo já com hp<=0", alvo3["hp"] == 0)
        # sem furtivo_3 não reage
        r4 = setup(); r4.round_num = 1
        luccas4 = rogue(esp=["ladino_furtivo_2"]); luccas4["pos"]=[5,5]; r4.players["l"]=luccas4
        aliado4 = make_player("a","Ana","warrior",1); aliado4["pos"]=[0,0]; r4.players["a"]=aliado4
        alvo4 = monster(hp=20)
        await r4._furtivo_reativo(aliado4, alvo4)
        check("sem furtivo_3 não reage", alvo4["hp"] == 20)
        # Luccas petrificado não reage
        r5 = setup(); r5.round_num = 1
        luccas5 = rogue(esp=["ladino_furtivo_3"]); luccas5["pos"]=[5,5]; luccas5["petrificado"]=True; r5.players["l"]=luccas5
        aliado5 = make_player("a","Ana","warrior",1); aliado5["pos"]=[0,0]; r5.players["a"]=aliado5
        alvo5 = monster(hp=20)
        await r5._furtivo_reativo(aliado5, alvo5)
        check("Luccas petrificado não reage", alvo5["hp"] == 20)
        # Luccas paralisado não reage
        r6 = setup(); r6.round_num = 1
        luccas6 = rogue(esp=["ladino_furtivo_3"]); luccas6["pos"]=[5,5]; luccas6["paralisado"]=True; r6.players["l"]=luccas6
        aliado6 = make_player("a","Ana","warrior",1); aliado6["pos"]=[0,0]; r6.players["a"]=aliado6
        alvo6 = monster(hp=20)
        await r6._furtivo_reativo(aliado6, alvo6)
        check("Luccas paralisado não reage", alvo6["hp"] == 20)
        # Luccas imobilizado (perde_turno) não reage
        r7 = setup(); r7.round_num = 1
        luccas7 = rogue(esp=["ladino_furtivo_3"]); luccas7["pos"]=[5,5]; luccas7["perde_turno"]=True; r7.players["l"]=luccas7
        aliado7 = make_player("a","Ana","warrior",1); aliado7["pos"]=[0,0]; r7.players["a"]=aliado7
        alvo7 = monster(hp=20)
        await r7._furtivo_reativo(aliado7, alvo7)
        check("Luccas imobilizado não reage", alvo7["hp"] == 20)
    finally:
        S.random.randint = _orig_rand
```

- [ ] **Step 2: Rodar — MUST fail** (`_furtivo_reativo` inexistente).

- [ ] **Step 3: Adicionar `_furtivo_reativo`** (método de `GameRoom`, perto de `_verificar_ataque_furtivo`):
```python
    async def _furtivo_reativo(self, atacante, target):
        """Ataque Furtivo Supremo (ladino_furtivo_3): reage ao acerto de um aliado
        contra um inimigo, 1x por inimigo por rodada. Não dispara no próprio
        ataque de Luccas, nem se Luccas estiver incapaz de reagir (petrificado,
        paralisado ou imobilizado — perde_turno)."""
        if atacante.get("class_id") == "rogue" or target.get("hp", 0) <= 0:
            return
        luccas = next((q for q in self.players.values()
                       if q.get("class_id") == "rogue" and q.get("alive")
                       and q["id"] != atacante["id"]), None)
        if not luccas or not tem_espec(luccas, "ladino_furtivo_3"):
            return
        if luccas.get("petrificado") or luccas.get("paralisado") or luccas.get("perde_turno"):
            return
        if luccas.get("furtivo_reativo_round") != self.round_num:
            luccas["furtivo_reativo_round"] = self.round_num
            luccas["furtivo_reativo_alvos"] = set()
        if target["id"] in luccas.get("furtivo_reativo_alvos", set()):
            return
        luccas["furtivo_reativo_alvos"].add(target["id"])
        nd4 = self._dados_furtivo(luccas.get("level", 1))
        dano = sum(random.randint(1, 4) for _ in range(nd4))
        await self.broadcast({"type": "dice_roll", "die": "d4", "value": dano,
                               "label": "Ataque Furtivo (reação)"})
        target["hp"] -= dano
        await self.gm_say(f"🗡️ **{luccas['name']}** reage ao ataque de **{atacante['name']}** — "
                          f"Ataque Furtivo Supremo! +{dano} de dano [{nd4}d4] em **{target['name']}**.")
```

- [ ] **Step 4: Hookar em `handle_attack`** (mão principal). Trocar:
```python
                target["hp"] -= dmg
                crit_str = " **CRÍTICO!**" if crit else ""
```
por:
```python
                target["hp"] -= dmg
                await self._furtivo_reativo(p, target)
                crit_str = " **CRÍTICO!**" if crit else ""
```

- [ ] **Step 5: Hookar em `handle_throw`** (arremesso). Trocar:
```python
            target["hp"] -= dmg
            sb = f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod)
```
por:
```python
            target["hp"] -= dmg
            await self._furtivo_reativo(p, target)
            sb = f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod)
```

- [ ] **Step 6: Rodar — MUST pass** + regressão `python tools/test_devorador.py` (anote).

- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): Ataque Furtivo Supremo - reacao automatica 1x/inimigo/rodada"
```

---

## Task 5: Fórmulas de Armadilha — gate em `handle_criar_armadilha`

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [5] Fórmulas: gate em handle_criar_armadilha
    print("\n[5] Fórmulas — gate")
    r = setup(); r.gold_check = True
    luccas = rogue(); luccas["pos"] = [0,0]; luccas["gold"] = 100; r.players["l"] = luccas
    check("buraco sempre destravado", "buraco" in r._armadilhas_desbloqueadas(luccas))
    check("armadilha_urso bloqueada sem fórmula", "armadilha_urso" not in r._armadilhas_desbloqueadas(luccas))
    await r.handle_criar_armadilha("l", {"tipo": "armadilha_urso", "tx": 0, "ty": 0})
    check("recusa criar tipo bloqueado (sem armadilha nova)", len(r.armadilhas) == 0 and r._errs)
    luccas["guild_owned"]["especializacoes"] = ["ladino_armadilha_urso"]
    check("armadilha_urso destravada após compra (simulada)", "armadilha_urso" in r._armadilhas_desbloqueadas(luccas))
    r._errs = []
    await r.handle_criar_armadilha("l", {"tipo": "armadilha_urso", "tx": 0, "ty": 0})
    check("cria armadilha destravada com sucesso", len(r.armadilhas) == 1 and not r._errs)
```

- [ ] **Step 2: Rodar — MUST fail** (`_armadilhas_desbloqueadas` inexistente; sem gate, o `handle_criar_armadilha` cria a armadilha bloqueada de graça).

- [ ] **Step 3: Adicionar `_armadilhas_desbloqueadas`** (método de `GameRoom`, perto de `_furtivo_reativo`):
```python
    def _armadilhas_desbloqueadas(self, p):
        """Tipos de armadilha que o Ladino pode fabricar: buraco sempre grátis;
        os demais exigem a Fórmula correspondente (extensível via ARMADILHAS)."""
        tipos = set()
        for tipo_id, tipo in ARMADILHAS.items():
            gid = tipo.get("formula_guild_id")
            if gid is None or tem_espec(p, gid):
                tipos.add(tipo_id)
        return tipos
```

- [ ] **Step 4: Gatear `handle_criar_armadilha`.** Trocar:
```python
        tipo_id = msg.get("tipo")
        tipo = ARMADILHAS.get(tipo_id)
        if not tipo:
            await self.send_to(pid, {"type": "error", "msg": "Armadilha inválida."}); return
```
por:
```python
        tipo_id = msg.get("tipo")
        tipo = ARMADILHAS.get(tipo_id)
        if not tipo:
            await self.send_to(pid, {"type": "error", "msg": "Armadilha inválida."}); return
        if tipo_id not in self._armadilhas_desbloqueadas(p):
            await self.send_to(pid, {"type": "error",
                "msg": f"Você ainda não aprendeu a fórmula de {tipo['nome']} — compre na Guilda."}); return
```

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): handle_criar_armadilha gateia tipo pela formula comprada"
```

---

## Task 6: Desarme — bônus +2 e recuperação de ouro (III)

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [6] Desarme — bônus e recuperação
    print("\n[6] Desarme")
    r = setup()
    check("bônus base = 0", r._desarme_bonus(rogue()) == 0)
    check("bônus com desarme_2 = 2", r._desarme_bonus(rogue(esp=["ladino_desarme_2"])) == 2)
    check("bônus com desarme_3 = 2 (não soma mais)", r._desarme_bonus(rogue(esp=["ladino_desarme_2","ladino_desarme_3"])) == 2)
    # integração: desarme_3 recupera ouro em sucesso duplo (mock d20 alto)
    _orig_rand = S.random.randint; S.random.randint = lambda a,b: 20
    try:
        r = setup(); luccas = rogue(esp=["ladino_desarme_2","ladino_desarme_3"])
        luccas["pos"] = [0,0]; luccas["gold"] = 0; luccas["dex"] = 10; r.players["l"] = luccas
        r.armadilhas = [{"id":"arm1","tipo":"armadilha_urso","pos":[0,0],"visivel":True,"ativada":False}]
        r._armadilha_no_tile = lambda x,y: next((a for a in r.armadilhas if a["pos"]==[x,y]), None)
        await r.handle_desarmar_armadilha("l", {})
        check("desarmou com sucesso", len(r.armadilhas) == 0)
        check("recuperou o ouro (custo_ouro da armadilha_urso=1)", luccas["gold"] == 1)
    finally:
        S.random.randint = _orig_rand
```

- [ ] **Step 2: Rodar — MUST fail** (`_desarme_bonus` inexistente).

- [ ] **Step 3: Adicionar `_desarme_bonus`** (método de `GameRoom`):
```python
    def _desarme_bonus(self, p):
        return 2 if (tem_espec(p, "ladino_desarme_2") or tem_espec(p, "ladino_desarme_3")) else 0
```

- [ ] **Step 4: Gatear `handle_desarmar_armadilha`.** Trocar `total = d20 + bonus` por
`total = d20 + bonus + self._desarme_bonus(p)`. Em seguida, trocar o ramo de
sucesso:
```python
        elif total >= dif:
            self.armadilhas = [a for a in self.armadilhas if a["id"] != arm["id"]]
            await self.gm_say("✅ Armadilha desarmada com sucesso!")
```
por:
```python
        elif total >= dif:
            custo_ouro_arm = tipo.get("custo_ouro", 0)
            recuperou = False
            if tem_espec(p, "ladino_desarme_3") and custo_ouro_arm > 0:
                d20r = random.randint(1, 20)
                totalr = d20r + bonus + self._desarme_bonus(p)
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20r,
                                       "label": f"{p['name']} — Recuperar"})
                if totalr >= dif:
                    p["gold"] += custo_ouro_arm
                    recuperou = True
            self.armadilhas = [a for a in self.armadilhas if a["id"] != arm["id"]]
            msg_recover = f" Recuperou 🪙{custo_ouro_arm}!" if recuperou else ""
            await self.gm_say(f"✅ Armadilha desarmada com sucesso!{msg_recover}")
```

- [ ] **Step 5: Rodar — MUST pass.**

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): Desarme +2 (II) e recuperacao de ouro (III)"
```

---

## Task 7: Veneno Rápido — 2 golpes (II) e 2 slots simultâneos (III)

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [7] Veneno Rápido
    print("\n[7] Veneno Rápido")
    r = setup()
    check("golpes base = 1", r._veneno_rapido_max_hits(rogue()) == 1)
    check("golpes com veneno_2 = 2", r._veneno_rapido_max_hits(rogue(esp=["ladino_veneno_2"])) == 2)
    check("2 slots sem veneno_3", not r._veneno_rapido_2_slots(rogue()))
    check("2 slots com veneno_3", r._veneno_rapido_2_slots(rogue(esp=["ladino_veneno_2","ladino_veneno_3"])))
    # integração: aplicar 1º veneno preenche slot 1; 2º (com veneno_3) preenche slot 2 sem apagar o 1º
    r = setup()
    luccas = rogue(esp=["ladino_veneno_2","ladino_veneno_3"])
    luccas["sede"] = 50
    luccas["weapon"] = {"id": "dagger"}
    luccas["bag"] = [{"id":"frasco_a","veneno_id":"veneno_fraco"}, {"id":"frasco_b","veneno_id":"veneno_forte"}]
    r.players["l"] = luccas
    S.VENENOS.setdefault("veneno_fraco", {"nome":"Fraco"})
    S.VENENOS.setdefault("veneno_forte", {"nome":"Forte"})
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_fraco"})
    check("1º veneno preenche slot 1", luccas["weapon_poison"] == "veneno_fraco")
    check("slot 1 dura 2 golpes (veneno_2)", luccas["weapon_poison_hits"] == 2)
    await r.handle_veneno_rapido("l", {"veneno_id": "veneno_forte"})
    check("2º veneno preenche slot 2 (não apaga o 1º)",
          luccas["weapon_poison"] == "veneno_fraco" and luccas.get("weapon_poison_2") == "veneno_forte")
```

- [ ] **Step 2: Rodar — MUST fail** (helpers inexistentes; sem eles a 2ª aplicação sobrescreve o slot 1).

- [ ] **Step 3: Adicionar campos em `make_player`.** Trocar:
```python
        "weapon_poison":       None,   # veneno untado na arma (Veneno Rápido / coat_poison)
        "weapon_poison_hits":  0,      # golpes certeiros restantes com veneno
```
por:
```python
        "weapon_poison":       None,   # veneno untado na arma (Veneno Rápido / coat_poison)
        "weapon_poison_hits":  0,      # golpes certeiros restantes com veneno
        "weapon_poison_2":       None,   # 2º veneno (só com ladino_veneno_3)
        "weapon_poison_2_hits":  0,
```

- [ ] **Step 4: Adicionar helpers** (métodos de `GameRoom`, perto de `_desarme_bonus`):
```python
    def _veneno_rapido_max_hits(self, p):
        """Golpes que o veneno melee dura (1 base / 2 com ladino_veneno_2)."""
        return 2 if tem_espec(p, "ladino_veneno_2") else 1

    def _veneno_rapido_2_slots(self, p):
        return tem_espec(p, "ladino_veneno_3")
```

- [ ] **Step 5: Gatear `handle_veneno_rapido`.** Trocar:
```python
        cargas = VENENO_CARGAS if _is_ranged else 1
        p["weapon_poison"]      = vid
        p["weapon_poison_hits"] = cargas
```
por:
```python
        cargas = VENENO_CARGAS if _is_ranged else self._veneno_rapido_max_hits(p)
        if not _is_ranged and p.get("weapon_poison") and self._veneno_rapido_2_slots(p) and not p.get("weapon_poison_2"):
            p["weapon_poison_2"]      = vid
            p["weapon_poison_2_hits"] = cargas
        else:
            p["weapon_poison"]      = vid
            p["weapon_poison_hits"] = cargas
```

- [ ] **Step 6: Aplicar o 2º veneno no hit melee (`handle_attack`).** Trocar:
```python
                    elif p.get("weapon_poison"):
                        # Corpo a corpo: 1 carga, consumida só no golpe certeiro.
                        await self._aplicar_veneno(target, p["weapon_poison"], fonte="ataque")
                        p["weapon_poison_hits"] = p.get("weapon_poison_hits", 1) - 1
                        if p["weapon_poison_hits"] <= 0:
                            p["weapon_poison"] = None
                            await self.gm_say(f"🧴 O veneno da arma de **{p['name']}** acabou.")
```
por:
```python
                    elif p.get("weapon_poison"):
                        # Corpo a corpo: 1 carga, consumida só no golpe certeiro.
                        await self._aplicar_veneno(target, p["weapon_poison"], fonte="ataque")
                        p["weapon_poison_hits"] = p.get("weapon_poison_hits", 1) - 1
                        if p["weapon_poison_hits"] <= 0:
                            p["weapon_poison"] = None
                            await self.gm_say(f"🧴 O veneno da arma de **{p['name']}** acabou.")
                    if p.get("weapon_poison_2"):
                        await self._aplicar_veneno(target, p["weapon_poison_2"], fonte="ataque")
                        p["weapon_poison_2_hits"] = p.get("weapon_poison_2_hits", 1) - 1
                        if p["weapon_poison_2_hits"] <= 0:
                            p["weapon_poison_2"] = None
                            await self.gm_say(f"🧴 O 2º veneno da arma de **{p['name']}** acabou.")
```
(O `elif` do slot 1 permanece ligado ao `if _ranged_poison_vid:` anterior; o novo
bloco do slot 2 é um `if` independente, para aplicar os dois no mesmo golpe.)

- [ ] **Step 7: Rodar — MUST pass** + regressão `python tools/test_devorador.py` (anote).

- [ ] **Step 8: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): Veneno Rapido dura 2 golpes (II) + 2 slots simultaneos (III)"
```

---

## Task 8: Esconder nas Sombras — bônus, ação livre e CA ao revelar

**Files:** Modify `server.py`; `tools/test_ladino_espec.py`.

- [ ] **Step 1: Teste que falha** — inserir em `main()`:
```python
    # [8] Esconder nas Sombras
    print("\n[8] Esconder nas Sombras")
    r = setup()
    check("bônus base = 0", r._esconder_bonus(rogue()) == 0)
    check("bônus com esconder_2 = 2", r._esconder_bonus(rogue(esp=["ladino_esconder_2"])) == 2)
    check("bônus com esconder_3 = 2 (não soma mais)", r._esconder_bonus(rogue(esp=["ladino_esconder_2","ladino_esconder_3"])) == 2)
    # sem esconder_3: gasta ação bônus
    r = setup(); luccas = rogue(); luccas["pos"]=[0,0]; luccas["fome"]=50; luccas["sede"]=50; r.players["l"]=luccas
    _orig_rand = S.random.randint; S.random.randint = lambda a,b: 20
    try:
        await r.handle_esconder_sombras("l", {})
        check("sem esconder_3: gasta ação bônus", luccas.get("bonus_action_used") is True)
    finally:
        S.random.randint = _orig_rand
    # com esconder_3: NÃO gasta ação bônus
    r2 = setup(); luccas2 = rogue(esp=["ladino_esconder_2","ladino_esconder_3"]); luccas2["pos"]=[0,0]
    luccas2["fome"]=50; luccas2["sede"]=50; r2.players["l"]=luccas2
    _orig_rand2 = S.random.randint; S.random.randint = lambda a,b: 20
    try:
        await r2.handle_esconder_sombras("l", {})
        check("com esconder_3: não gasta ação bônus", not luccas2.get("bonus_action_used"))
    finally:
        S.random.randint = _orig_rand2
    # ao ser revelado com esconder_3, ganha +2 de CA (temp_def)
    r3 = setup(); luccas3 = rogue(esp=["ladino_esconder_2","ladino_esconder_3"]); luccas3["id"]="l"
    luccas3["invisivel_sombras"] = True; r3.players["l"] = luccas3
    await r3._quebrar_invisibilidade(luccas3, "ao atacar")
    check("CA +2 por 1 rodada ao revelar com esconder_3", r3.temp_def.get("l") == 2)
    # sem esconder_3, não ganha CA
    r4 = setup(); luccas4 = rogue(); luccas4["id"]="l"
    luccas4["invisivel_sombras"] = True; r4.players["l"] = luccas4
    await r4._quebrar_invisibilidade(luccas4, "ao atacar")
    check("sem esconder_3, não ganha CA ao revelar", r4.temp_def.get("l", 0) == 0)
```

- [ ] **Step 2: Rodar — MUST fail** (`_esconder_bonus` inexistente; sem gate, sempre gasta ação bônus e nunca dá CA).

- [ ] **Step 3: Adicionar `_esconder_bonus`** (método de `GameRoom`):
```python
    def _esconder_bonus(self, p):
        return 2 if (tem_espec(p, "ladino_esconder_2") or tem_espec(p, "ladino_esconder_3")) else 0
```

- [ ] **Step 4: Gatear `handle_esconder_sombras`.** Trocar `total = d20 + bonus_dex` por
`total = d20 + bonus_dex + self._esconder_bonus(p)`. Trocar:
```python
        p["bonus_action_used"] = True
```
(a que fica **antes** do cálculo de `sucesso`, dentro deste handler) por:
```python
        if not tem_espec(p, "ladino_esconder_3"):
            p["bonus_action_used"] = True
```

- [ ] **Step 5: Adicionar bônus de CA em `_quebrar_invisibilidade`.** Trocar:
```python
    async def _quebrar_invisibilidade(self, p, motivo="ao agir"):
        """Encerra o estado invisível das sombras (atacar/mover revela Luccas)."""
        if not p.get("invisivel_sombras"):
            return False
        p["invisivel_sombras"] = False
        await self.gm_say(f"🌑 **{p['name']}** revela-se ({motivo}).")
        return True
```
por:
```python
    async def _quebrar_invisibilidade(self, p, motivo="ao agir"):
        """Encerra o estado invisível das sombras (atacar/mover revela Luccas)."""
        if not p.get("invisivel_sombras"):
            return False
        p["invisivel_sombras"] = False
        await self.gm_say(f"🌑 **{p['name']}** revela-se ({motivo}).")
        if tem_espec(p, "ladino_esconder_3"):
            self.temp_def[p["id"]] = self.temp_def.get(p["id"], 0) + 2
            await self.gm_say(f"🌀 **{p['name']}** ganha +2 de CA por 1 rodada ao se revelar!")
        return True
```

- [ ] **Step 6: Rodar — MUST pass** + regressão `python tools/test_devorador.py` (anote).

- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_ladino_espec.py
git commit -m "feat(guilda): Esconder nas Sombras +2 (II), acao livre e +2 CA ao revelar (III)"
```

---

## Task 9: Cliente — painéis do Luccas respeitam os níveis

**Files:** Modify `src/gameState.js`, `game.js`.

- [ ] **Step 1: Getters em `gameState.js`** (perto dos getters do Paladino):
```javascript
  function ladinoArmadilhasDesbloqueadas() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    const mapa = {
      armadilha_urso: 'ladino_armadilha_urso', fosso_estacas: 'ladino_fosso_estacas',
      fosso_envenenado: 'ladino_fosso_envenenado', rede: 'ladino_rede',
      armadilha_incendiaria: 'ladino_armadilha_incendiaria', mina_terrestre: 'ladino_mina_terrestre',
      nuvem_gas: 'ladino_nuvem_gas',
    };
    const tipos = ['buraco'];
    for (const [tipo, gid] of Object.entries(mapa)) if (e.includes(gid)) tipos.push(tipo);
    return tipos;
  }
  function ladinoFurtivoNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('ladino_furtivo_3')) return 3;
    if (e.includes('ladino_furtivo_2')) return 2;
    return 1;
  }
  function ladinoDesarmeBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    return (e.includes('ladino_desarme_2') || e.includes('ladino_desarme_3')) ? 2 : 0;
  }
  function ladinoDesarmeRecupera() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_desarme_3');
  }
  function ladinoVenenoMaxHits() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_veneno_2') ? 2 : 1;
  }
  function ladinoVeneno2Slots() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_veneno_3');
  }
  function ladinoEsconderBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    return (e.includes('ladino_esconder_2') || e.includes('ladino_esconder_3')) ? 2 : 0;
  }
  function ladinoEsconderLivre() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_esconder_3');
  }
```
Exportar todos os 8 no `return { ... }` (junto dos getters do Paladino).

- [ ] **Step 2: Painel de criar armadilha — filtrar por tipo destravado.**
Localizar `ARMADILHAS_LUCCAS` (lista de tipos com nome/ícone/custo, usada pelo
painel de criação) e o local que renderiza os botões de escolha de tipo.
Filtrar/desabilitar os tipos não presentes em `GS.ladinoArmadilhasDesbloqueadas()`,
mostrando "compre na Guilda" nos bloqueados em vez de escondê-los totalmente
(consistente com o padrão de "bloqueado com dica" usado no painel da Guilda).

- [ ] **Step 3: Descrições refletem o nível** — no renderer dedicado do Luccas
(botões de Ataque Furtivo passivo/Desarme/Veneno Rápido/Esconder nas Sombras),
usar os getters acima para mostrar o texto correto (ex.: Desarme mostra "+2" se
`ladinoDesarmeBonus()>0`; Veneno Rápido mostra "dura 2 golpes" se
`ladinoVenenoMaxHits()===2` e "pode aplicar um 2º veneno" se
`ladinoVeneno2Slots()`; Esconder nas Sombras mostra "+2" e, se
`ladinoEsconderLivre()`, "não gasta ação bônus").

- [ ] **Step 4: Syntax check.** `node --check src/gameState.js && node --check game.js` → exit 0.

- [ ] **Step 5: Commit**
```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): paineis do Ladino respeitam niveis das especializacoes"
```

---

## Task 10: Verificação E2E + docs

**Files:** Modify `CLAUDE.md`.

- [ ] **Step 1: Suíte**
`python tools/test_ladino_espec.py` → 0 falharam
`python tools/test_paladino_espec.py` / `test_clerigo_espec.py` / `test_guerreiro_espec.py` / `test_guilda.py` → 0 falharam (fases anteriores intactas)
`python tools/test_devorador.py` → combate ok (regressão dos handlers tocados: `handle_attack`, `handle_throw`, veneno, furtivo)

- [ ] **Step 2: Smoke test in-app** (padrão das fases; `.claude/launch.json` server `game`):
  - Subir preview; criar sala; escolher **Ladino**; dar ouro (bump temporário-e-revertido do `start_gold` do `rogue`; `rm -rf saves/` ao fim).
  - Na Guilda: confirmar que as 7 Fórmulas aparecem na aba Especializações (geradas dinamicamente); comprar `ladino_furtivo_2` e `ladino_armadilha_urso`.
  - Na masmorra: confirmar que criar armadilha oferece "Armadilha de Urso" (destravada) e recusa/bloqueia outra não comprada; zero erros de console.

- [ ] **Step 3: `CLAUDE.md`** — na seção da Guilda, acrescentar parágrafo do Ladino:
baseline enfraquecido do Ataque Furtivo (base só oculto; "aliado adjacente" exige
`ladino_furtivo_2`); reação automática do Furtivo Supremo (`_furtivo_reativo`,
hookada em `handle_attack`/`handle_throw`, bloqueada se Luccas
petrificado/paralisado/imobilizado); catálogo **extensível** de Fórmulas de
Armadilha (`formula_guild_id`/`formula_preco` em `ARMADILHAS`,
`_gerar_catalogo_formulas_armadilha`); Desarme +2 e recuperação de ouro (III);
Veneno Rápido com 2 slots (`weapon_poison`/`weapon_poison_2`); Esconder nas
Sombras ação livre + CA via `self.temp_def` no III. Teste:
`tools/test_ladino_espec.py`.

- [ ] **Step 4: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(guilda): documentar especializacoes do Ladino (Fase 1d)"
```

---

## Self-review (cobertura do spec)

- **§4.1 catálogo literal (8 nós)** → Task 1. ✔
- **§4.2 Fórmulas extensíveis (7 nós gerados)** → Task 2. ✔
- **§5.1 redesign Furtivo (base + II)** → Task 3. ✔
- **§5.1 Furtivo Supremo (reação, 1x/inimigo/rodada, bloqueios de incapacidade)** → Task 4. ✔
- **§5.2 gate de Fórmulas em `handle_criar_armadilha`** → Task 5. ✔
- **§5.3 Desarme (+2, recuperação)** → Task 6. ✔
- **§5.4 Veneno Rápido (2 golpes, 2 slots)** → Task 7. ✔
- **§5.5 Esconder nas Sombras (+2, ação livre, CA)** → Task 8. ✔
- **§6 cliente** → Task 9. ✔
- **§7 testes** → `tools/test_ladino_espec.py` (Tasks 1-8) + smoke (Task 10). ✔
- **§9 riscos (nerf, duplicidade/incapacidade da reação, refactor de veneno, geração do catálogo, `temp_def` aditivo)** → todos endereçados nas tasks correspondentes com testes dedicados. ✔

**Escopo explicitamente limitado (documentado no plano, não no spec original, mas
consistente com YAGNI):** a reação do Furtivo Supremo só é hookada em
`handle_attack` (mão principal) e `handle_throw` (arremesso) — não em ataque de
mão secundária/offhand, arremesso de lança, animados controlados, ou dano de
magia. Se o usuário quiser cobertura total depois, é um follow-up pequeno e
isolado (mesma função `_furtivo_reativo`, só mais pontos de chamada).

**Consistência de nomes:** helpers `_armadilhas_desbloqueadas`/`_furtivo_reativo`/
`_desarme_bonus`/`_veneno_rapido_max_hits`/`_veneno_rapido_2_slots`/
`_esconder_bonus` (métodos de `GameRoom`); `_gerar_catalogo_formulas_armadilha`
(função de módulo). Campos: `weapon_poison_2`/`weapon_poison_2_hits`,
`furtivo_reativo_round`/`furtivo_reativo_alvos`, `formula_guild_id`/
`formula_preco` (em `ARMADILHAS`). Cliente: `ladinoArmadilhasDesbloqueadas`/
`ladinoFurtivoNivel`/`ladinoDesarmeBonus`/`ladinoDesarmeRecupera`/
`ladinoVenenoMaxHits`/`ladinoVeneno2Slots`/`ladinoEsconderBonus`/
`ladinoEsconderLivre`.
