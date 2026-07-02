# Especializações do Bardo (Guilda Fase 1e) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar à Guilda as especializações do Bardo (Henrique): Canção Heroica II (5 nós + Suprema), Provocação II/III e Lendas (Avançadas por espécie + Supremas), tudo autoritativo no servidor.

**Architecture:** Segue o padrão das Fases 1a-1d: entradas `categoria:"especializacao"`, `classe:"bard"` em `GUILD_CATALOG` (parte literal + parte **gerada** de `MONSTER_DEFS`, como as Fórmulas de Armadilha do Ladino), gating por `tem_espec(player, id)` + helpers em `GameRoom`, e getters no cliente. Nenhum novo protocolo WebSocket.

**Tech Stack:** Python 3 (`server.py`), vanilla JS (`src/gameState.js`, `game.js`), harness de teste próprio do projeto (`tools/test_*.py`, rodado com `python tools/test_bardo_espec.py`).

**Spec:** `docs/superpowers/specs/2026-07-02-guilda-fase1e-bardo-design.md`

---

## Arquivos tocados

- **Modify** `server.py`:
  - `GUILD_CATALOG` (~279) — 8 nós literais do bardo.
  - Após `GUILD_CATALOG.update(_gerar_catalogo_formulas_armadilha())` (~2443) — `_LENDA_PRECO_TIER`, `_gerar_catalogo_lendas()`, `GUILD_CATALOG.update(...)`.
  - `_aplicar_buffs_cancao` (~6489), `handle_ativar_cancao` (~6459-6476), `_cobrar_manutencao_cancao` (~6506) — nível por atributo + custo reduzido.
  - `handle_provocacao` (~6566) — registrar janela de vantagem dos aliados (III).
  - Sites de reset da desvantagem (~11176, ~12906) — persistência (II).
  - Sites de `effective_ac` de ataque de monstro (~11164, ~12887) — +2 CA (II).
  - `handle_attack` (~5224 `eff_atk`, ~5242 `vantagem`) — +1 ataque de Lenda e vantagem da Provocação.
  - `_testar_save` (~9485) — param `fonte=None` + bônus de resistência de Lenda.
  - 6 sites de save de habilidade de monstro (11286, 11650, 11761, 11827, 12293, 12611) — `fonte=m`.
  - Novos helpers de `GameRoom`: `_cancao_nivel_atributo`, `_cancao_custo_reducao`, `_provocador`, `_provocacao_ca_bonus`, `_provocacao_atk_vantagem`, `_bardo_lendas`, `_lenda_atk_bonus`, `_lenda_resist_bonus`.
- **Modify** `src/gameState.js` — getters do bardo + export.
- **Modify** `game.js` — descrições dos painéis do Henrique (Canção/Provocação).
- **Create** `tools/test_bardo_espec.py`.
- **Modify** `CLAUDE.md` — parágrafo da Fase 1e.

> **Fatos verificados no código:**
> - `tem_espec(player, id)` (458): `id in player["guild_owned"]["especializacoes"]`.
> - `MONSTER_DEFS` (810): cada item tem `type`, `name`, `emoji`, `tier`.
> - `_cancao_bonus(p, chave)` (9204) devolve `p.get("buffs_cancao", {}).get(chave, 0)` — ao gravar valor 2 no buff, o +2 flui sem mudar nada aqui.
> - `_player_effective_ac(p)` (10642) NÃO recebe o atacante → o +2 CA da Provocação II é somado inline nos sites de ataque de monstro (onde `m` existe).
> - `_rolar_ataque(atk, ac, vantagem=False, desvantagem=False)` (9371).
> - `_testar_save(alvo, tipo, dif, extra_mod=0)` (9485).
> - Helpers de catálogo p/ teste: `S.guild_items_for_class(classe)`, `S.guild_item(id)`, `S.GUILD_CATALOG`.
> - `make_player(pid, nome, class_id, idx)` cria jogador com `guild_owned["especializacoes"]`.

---

### Task 1: Catálogo do Bardo (8 nós literais + Lendas geradas)

**Files:**
- Modify: `server.py` (`GUILD_CATALOG` ~317 após `guerreiro_furia_3`; gerador após `server.py:2443`)
- Test: `tools/test_bardo_espec.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_bardo_espec.py`:

```python
"""Especializações do Bardo (Fase 1e). Roda da raiz: python tools/test_bardo_espec.py"""
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

def bard(**owned):
    p = make_player("b", "Henrique", "bard", 0)
    p["guild_owned"]["especializacoes"] = list(owned.get("esp", []))
    p["pos"] = [0, 0]; p["alive"] = True
    return p

def monster(mid="m1", type_="goblin", pos=(0,1), hp=20):
    return {"id": mid, "type": type_, "name": "Goblin", "nome": "Goblin",
            "pos": list(pos), "hp": hp, "max_hp": hp, "ac": 10}

async def main():
    # [1] Catálogo literal do bardo
    print("\n[1] Catálogo do Bardo (literais)")
    ids = [i["id"] for i in S.guild_items_for_class("bard")]
    for eid in ["bardo_cancao_acerto","bardo_cancao_dano","bardo_cancao_ca",
                "bardo_cancao_movimento","bardo_cancao_resistencia",
                "bardo_cancao_suprema","bardo_provocacao_2","bardo_provocacao_3",
                "bardo_lendas_supremas"]:
        check(f"catálogo tem {eid}", eid in ids)
    check("cada canção custa 100", all(S.guild_item(f"bardo_cancao_{a}")["preco"] == 100
          for a in ["acerto","dano","ca","movimento","resistencia"]))
    check("canção suprema custa 200", S.guild_item("bardo_cancao_suprema")["preco"] == 200)
    check("provocacao_2 custa 150", S.guild_item("bardo_provocacao_2")["preco"] == 150)
    check("provocacao_3 requer _2", S.guild_item("bardo_provocacao_3")["requer"] == "bardo_provocacao_2")
    check("lendas supremas custa 300", S.guild_item("bardo_lendas_supremas")["preco"] == 300)

    # [2] Lendas geradas de MONSTER_DEFS
    print("\n[2] Lendas Avançadas (geradas)")
    ids = [i["id"] for i in S.guild_items_for_class("bard")]
    for mdef in S.MONSTER_DEFS:
        gid = f"lenda_{mdef['type']}"
        check(f"catálogo tem {gid}", gid in ids)
    check("preço goblin (T1) = 60", S.guild_item("lenda_goblin")["preco"] == 60)
    check("preço orc (T2) = 90", S.guild_item("lenda_orc")["preco"] == 90)
    check("preço troll (T3) = 120", S.guild_item("lenda_troll")["preco"] == 120)
    check("preço dragon (T4) = 200", S.guild_item("lenda_dragon")["preco"] == 200)
    check("lenda guarda lenda_tipo", S.guild_item("lenda_goblin")["lenda_tipo"] == "goblin")

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_bardo_espec.py`
Expected: FAIL — catálogo não tem `bardo_*`/`lenda_*` (KeyError em `guild_item` ou checks vermelhos).

- [ ] **Step 3: Adicionar os 8 nós literais no `GUILD_CATALOG`**

Em `server.py`, logo após o bloco `"guerreiro_furia_3": {...}` (~317) — antes de `"clerigo_cura_2"` — inserir:

```python
    # ── Bardo (Fase 1e) ─────────────────────────────────────────────────────
    "bardo_cancao_acerto": {
        "id": "bardo_cancao_acerto", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_cancao", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 100, "nome": "Canção: Acerto +1", "icon": "🎵",
        "desc": "O bônus de Acerto da Canção Heroica sobe de +1 para +2.",
    },
    "bardo_cancao_dano": {
        "id": "bardo_cancao_dano", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_cancao", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 100, "nome": "Canção: Dano +1", "icon": "🎵",
        "desc": "O bônus de Dano da Canção Heroica sobe de +1 para +2.",
    },
    "bardo_cancao_ca": {
        "id": "bardo_cancao_ca", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_cancao", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 100, "nome": "Canção: Armadura +1", "icon": "🎵",
        "desc": "O bônus de Armadura da Canção Heroica sobe de +1 para +2.",
    },
    "bardo_cancao_movimento": {
        "id": "bardo_cancao_movimento", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_cancao", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 100, "nome": "Canção: Movimento +1", "icon": "🎵",
        "desc": "O bônus de Movimento da Canção Heroica sobe de +1 para +2.",
    },
    "bardo_cancao_resistencia": {
        "id": "bardo_cancao_resistencia", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_cancao", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 100, "nome": "Canção: Resistência +1", "icon": "🎵",
        "desc": "O bônus de Resistência da Canção Heroica sobe de +1 para +2.",
    },
    "bardo_cancao_suprema": {
        "id": "bardo_cancao_suprema", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_cancao", "nivel": 3, "requer": None, "exclusiva": False,
        "preco": 200, "nome": "Canção Heroica Suprema", "icon": "🎶",
        "desc": "A manutenção da Canção Heroica custa -1🍖 e -1💧 (mínimo 0).",
    },
    "bardo_provocacao_2": {
        "id": "bardo_provocacao_2", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_provocacao", "nivel": 2, "requer": None, "exclusiva": False,
        "preco": 150, "nome": "Provocação II", "icon": "😤",
        "desc": "A desvantagem dura toda a provocação; Henrique ganha +2 CA e ataca o alvo com vantagem.",
    },
    "bardo_provocacao_3": {
        "id": "bardo_provocacao_3", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_provocacao", "nivel": 3, "requer": "bardo_provocacao_2", "exclusiva": False,
        "preco": 200, "nome": "Provocação III", "icon": "😤",
        "desc": "Todos os aliados atacam o alvo provocado com vantagem por 1 rodada.",
    },
    "bardo_lendas_supremas": {
        "id": "bardo_lendas_supremas", "categoria": "especializacao", "classe": "bard",
        "linha": "bardo_lendas", "nivel": 3, "requer": None, "exclusiva": False,
        "preco": 300, "nome": "Lendas Supremas", "icon": "📖",
        "desc": "Todos os bônus de Lenda passam a beneficiar o grupo inteiro (enquanto Henrique vivo).",
    },
```

- [ ] **Step 4: Adicionar o gerador de Lendas**

Em `server.py`, logo após a linha `GUILD_CATALOG.update(_gerar_catalogo_formulas_armadilha())` (~2443), inserir:

```python

_LENDA_PRECO_TIER = {1: 60, 2: 90, 3: 120, 4: 200}

def _gerar_catalogo_lendas():
    """Gera um nó de compra `lenda_<type>` para cada tipo em MONSTER_DEFS —
    extensível: monstros novos aparecem sozinhos na Guilda do Bardo."""
    entradas = {}
    for mdef in MONSTER_DEFS:
        gid = f"lenda_{mdef['type']}"
        entradas[gid] = {
            "id": gid, "categoria": "especializacao", "classe": "bard",
            "linha": "bardo_lendas", "nivel": None, "requer": None, "exclusiva": False,
            "preco": _LENDA_PRECO_TIER.get(mdef.get("tier", 1), 90),
            "nome": f"Lenda: {mdef['name']}", "icon": mdef.get("emoji", "📖"),
            "desc": f"+1 de ataque e +1 nos saves contra {mdef['name']}.",
            "lenda_tipo": mdef["type"],
        }
    return entradas

GUILD_CATALOG.update(_gerar_catalogo_lendas())
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_bardo_espec.py`
Expected: PASS nas seções [1] e [2] (FAIL restante = seções ainda não escritas; ok por enquanto se você só adicionou [1]/[2]).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_bardo_espec.py
git commit -m "feat(guilda): catalogo do Bardo (Cancao/Provocacao/Lendas geradas)"
```

---

### Task 2: Canção Heroica — nível por atributo + custo reduzido (Suprema)

**Files:**
- Modify: `server.py` (`_aplicar_buffs_cancao` ~6489; `handle_ativar_cancao` ~6459; `_cobrar_manutencao_cancao` ~6506)
- Test: `tools/test_bardo_espec.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()` (antes do bloco de print final):

```python
    # [3] Canção Heroica — nível por atributo + Suprema
    print("\n[3] Canção Heroica")
    r = setup()
    check("nivel base acerto = 1", r._cancao_nivel_atributo(bard(), "acerto") == 1)
    check("nivel comprado dano = 2",
          r._cancao_nivel_atributo(bard(esp=["bardo_cancao_dano"]), "dano") == 2)
    check("dano não afeta acerto",
          r._cancao_nivel_atributo(bard(esp=["bardo_cancao_dano"]), "acerto") == 1)
    check("reducao base = 0", r._cancao_custo_reducao(bard()) == 0)
    check("reducao com suprema = 1",
          r._cancao_custo_reducao(bard(esp=["bardo_cancao_suprema"])) == 1)

    # buffs aplicados usam o nível
    r = setup()
    b = bard(esp=["bardo_cancao_dano"]); r.players["b"] = b
    b["cancao_atributos"] = ["acerto", "dano"]
    await r._aplicar_buffs_cancao(b)
    check("buff acerto = 1", b["buffs_cancao"].get("bonus_acerto") == 1)
    check("buff dano = 2 (comprado)", b["buffs_cancao"].get("bonus_dano") == 2)

    # ativação com Suprema debita custo reduzido (mín 0)
    r = setup()
    b = bard(esp=["bardo_cancao_suprema"]); r.players["b"] = b
    b["fome"] = 10; b["sede"] = 10
    await r.handle_ativar_cancao("b", {"atributos": ["dano", "acerto"]})
    # dano=fome, acerto=sede → custo bruto 1/1, reduzido a 0/0
    check("ativação suprema não gasta fome", b["fome"] == 10)
    check("ativação suprema não gasta sede", b["sede"] == 10)
    check("custo salvo já reduzido", b["cancao_custo"] == {"fome": 0, "sede": 0})
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_bardo_espec.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute '_cancao_nivel_atributo'`.

- [ ] **Step 3: Adicionar os helpers**

Em `server.py`, logo antes de `async def handle_ativar_cancao` (~6444, junto do bloco da canção), inserir:

```python
    def _cancao_nivel_atributo(self, p, attr_id):
        """Bônus daquele atributo na Canção Heroica: 2 se comprado na Guilda, senão 1."""
        return 2 if tem_espec(p, f"bardo_cancao_{attr_id}") else 1

    def _cancao_custo_reducao(self, p):
        """Redução de manutenção da canção com a Canção Heroica Suprema (-1🍖 -1💧)."""
        return 1 if tem_espec(p, "bardo_cancao_suprema") else 0
```

- [ ] **Step 4: Usar o nível nos buffs**

Em `_aplicar_buffs_cancao` (~6491-6495), trocar:

```python
        buffs = {}
        for attr_id in bardo.get("cancao_atributos", []):
            attr = next((a for a in CANCAO_ATRIBUTOS if a["id"] == attr_id), None)
            if attr:
                buffs[attr["efeito"]] = 1
```

por:

```python
        buffs = {}
        for attr_id in bardo.get("cancao_atributos", []):
            attr = next((a for a in CANCAO_ATRIBUTOS if a["id"] == attr_id), None)
            if attr:
                buffs[attr["efeito"]] = self._cancao_nivel_atributo(bardo, attr_id)
```

- [ ] **Step 5: Reduzir o custo na ativação**

Em `handle_ativar_cancao`, trocar o trecho (~6459-6469):

```python
        custo = _calcular_custo_cancao(atrib_validos)
        if p["fome"] < custo["fome"] or p["sede"] < custo["sede"]:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{custo['fome']} 💧{custo['sede']}."}); return

        p["fome"] = max(0, p["fome"] - custo["fome"])
        p["sede"] = max(0, p["sede"] - custo["sede"])

        p["cancao_ativa"]       = True
        p["cancao_atributos"]   = atrib_validos
        p["cancao_custo"]       = custo
```

por:

```python
        custo_bruto = _calcular_custo_cancao(atrib_validos)
        red = self._cancao_custo_reducao(p)
        custo = {"fome": max(0, custo_bruto["fome"] - red),
                 "sede": max(0, custo_bruto["sede"] - red)}
        if p["fome"] < custo["fome"] or p["sede"] < custo["sede"]:
            await self.send_to(pid, {"type": "error",
                "msg": f"Recursos insuficientes — precisa 🍖{custo['fome']} 💧{custo['sede']}."}); return

        p["fome"] = max(0, p["fome"] - custo["fome"])
        p["sede"] = max(0, p["sede"] - custo["sede"])

        p["cancao_ativa"]       = True
        p["cancao_atributos"]   = atrib_validos
        p["cancao_custo"]       = custo
```

> `cancao_custo` guarda o custo JÁ reduzido — o upkeep (`_cobrar_manutencao_cancao`) lê `cancao_custo` diretamente, então a redução propaga sem mais mudanças. Nenhuma edição extra em `_cobrar_manutencao_cancao`.

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_bardo_espec.py`
Expected: PASS nas seções [1]-[3].

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_bardo_espec.py
git commit -m "feat(guilda): Cancao Heroica II (+2 por atributo) e Suprema (manutencao -1/-1)"
```

---

### Task 3: Provocação II/III — desvantagem persistente, +2 CA, vantagem

**Files:**
- Modify: `server.py` (`handle_provocacao` ~6566; resets ~11176 e ~12906; `effective_ac` ~11164 e ~12887; `handle_attack` vantagem ~5242)
- Test: `tools/test_bardo_espec.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [4] Provocação II/III
    print("\n[4] Provocação")
    r = setup(); r.round_num = 5
    b = bard(esp=["bardo_provocacao_2"]); r.players["b"] = b
    ally = make_player("a", "Ana", "warrior", 1); ally["pos"] = [0,0]; ally["alive"] = True; r.players["a"] = ally
    mprov = monster(pos=(0,1)); mprov["provocado_turnos"] = 3; mprov["provocado_por"] = "b"
    check("_provocador acha o bardo", r._provocador(mprov) is b)
    check("+2 CA quando o alvo é o bardo dono",
          r._provocacao_ca_bonus(b, mprov) == 2)
    check("sem +2 CA para outro aliado",
          r._provocacao_ca_bonus(ally, mprov) == 0)
    check("bardo ataca com vantagem (II)",
          r._provocacao_atk_vantagem(b, mprov) is True)
    check("aliado NÃO tem vantagem sem III",
          r._provocacao_atk_vantagem(ally, mprov) is False)

    # III: aliados ganham vantagem na janela da rodada
    r = setup(); r.round_num = 5
    b3 = bard(esp=["bardo_provocacao_2","bardo_provocacao_3"]); r.players["b"] = b3
    ally3 = make_player("a","Ana","warrior",1); ally3["pos"]=[0,0]; ally3["alive"]=True; r.players["a"] = ally3
    m3 = monster(pos=(0,1)); m3["provocado_turnos"]=3; m3["provocado_por"]="b"
    m3["provocado_aliados_vantagem_round"] = 5
    check("aliado tem vantagem (III, mesma rodada)",
          r._provocacao_atk_vantagem(ally3, m3) is True)
    m3["provocado_aliados_vantagem_round"] = 4  # rodada anterior
    check("aliado sem vantagem fora da janela",
          r._provocacao_atk_vantagem(ally3, m3) is False)

    # provocador morto/ausente → sem bônus
    r = setup(); r.round_num = 5
    b4 = bard(esp=["bardo_provocacao_2"]); b4["alive"] = False; r.players["b"] = b4
    m4 = monster(pos=(0,1)); m4["provocado_turnos"]=3; m4["provocado_por"]="b"
    check("bardo morto → _provocador None", r._provocador(m4) is None)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_bardo_espec.py`
Expected: FAIL — `AttributeError: ... '_provocador'`.

- [ ] **Step 3: Adicionar os helpers**

Em `server.py`, logo após `handle_provocacao` (após ~6574, antes do comentário do Frade Lewis ~6576), inserir:

```python
    def _provocador(self, monstro):
        """Retorna o bardo (vivo) que provocou este monstro, ou None."""
        pid = monstro.get("provocado_por")
        b = self.players.get(pid) if pid else None
        if (b and b.get("alive") and b.get("class_id") == "bard"
                and monstro.get("provocado_turnos", 0) > 0):
            return b
        return None

    def _provocacao_ca_bonus(self, alvo_player, monstro):
        """+2 CA do alvo quando o monstro que ele provocou (Provocação II) o ataca."""
        b = self._provocador(monstro)
        if b and b["id"] == alvo_player.get("id") and tem_espec(b, "bardo_provocacao_2"):
            return 2
        return 0

    def _provocacao_atk_vantagem(self, atacante, monstro):
        """Vantagem ao atacar o monstro provocado: o bardo (Provocação II) sempre;
        qualquer aliado se Provocação III e dentro da janela de 1 rodada."""
        b = self._provocador(monstro)
        if not b:
            return False
        if atacante.get("id") == b["id"] and tem_espec(b, "bardo_provocacao_2"):
            return True
        if (tem_espec(b, "bardo_provocacao_3")
                and monstro.get("provocado_aliados_vantagem_round") == self.round_num):
            return True
        return False
```

- [ ] **Step 4: Registrar a janela de vantagem (III) na provocação**

Em `handle_provocacao`, logo após `alvo["provocado_por"] = pid` (~6569), inserir:

```python
        if tem_espec(p, "bardo_provocacao_3"):
            alvo["provocado_aliados_vantagem_round"] = self.round_num
```

- [ ] **Step 5: Desvantagem persistente (II) — site novo (~11170-11176)**

Em `_execute_one_monster_attack`, trocar (~11175-11176):

```python
        if prov:
            m["provocado_turno_efeito"] = False
```

por:

```python
        if prov and not (self._provocador(m) and tem_espec(self._provocador(m), "bardo_provocacao_2")):
            m["provocado_turno_efeito"] = False
```

E somar o +2 CA na CA efetiva desse site — trocar (~11164):

```python
        effective_ac = self._player_effective_ac(target) if is_player else target["ca"]
```

por:

```python
        effective_ac = self._player_effective_ac(target) if is_player else target["ca"]
        if is_player:
            effective_ac += self._provocacao_ca_bonus(target, m)
```

- [ ] **Step 6: Desvantagem persistente (II) + CA — site legado (~12887-12906)**

Em `server.py`, no site legado, trocar (~12905-12906):

```python
                if prov:
                    m["provocado_turno_efeito"] = False
```

por:

```python
                if prov and not (self._provocador(m) and tem_espec(self._provocador(m), "bardo_provocacao_2")):
                    m["provocado_turno_efeito"] = False
```

E somar o +2 CA — trocar o bloco de cálculo (~12884-12891):

```python
                if is_player:
                    gl_ca = (target.get("guerreiro_luz_bonus", {}).get("ca", 0)
                             if target.get("guerreiro_luz_ativo") else 0)
                    effective_ac = (target["ac"] + self.temp_def.get(target["id"], 0)
                                    + self._cancao_bonus(target, "bonus_ca")
                                    + gl_ca + self._mod_magia(target, "ca"))   # Abençoar (+CA no aliado)
                else:
                    effective_ac = target["ca"]
```

por:

```python
                if is_player:
                    gl_ca = (target.get("guerreiro_luz_bonus", {}).get("ca", 0)
                             if target.get("guerreiro_luz_ativo") else 0)
                    effective_ac = (target["ac"] + self.temp_def.get(target["id"], 0)
                                    + self._cancao_bonus(target, "bonus_ca")
                                    + gl_ca + self._mod_magia(target, "ca")   # Abençoar (+CA no aliado)
                                    + self._provocacao_ca_bonus(target, m))   # Provocação II
                else:
                    effective_ac = target["ca"]
```

- [ ] **Step 7: Vantagem do bardo/aliados em `handle_attack`**

Em `handle_attack`, trocar (~5242):

```python
            vantagem    = bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela")) or esc == "vantagem"
```

por:

```python
            vantagem    = (bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela"))
                           or esc == "vantagem"
                           or self._provocacao_atk_vantagem(p, target))
```

- [ ] **Step 8: Rodar e ver passar**

Run: `python tools/test_bardo_espec.py`
Expected: PASS nas seções [1]-[4].

- [ ] **Step 9: Commit**

```bash
git add server.py tools/test_bardo_espec.py
git commit -m "feat(guilda): Provocacao II/III (desvantagem persistente, +2 CA, vantagem)"
```

---

### Task 4: Lendas — bônus de ataque (+1)

**Files:**
- Modify: `server.py` (helpers perto dos da Provocação; `eff_atk` em `handle_attack` ~5224)
- Test: `tools/test_bardo_espec.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [5] Lendas — ataque +1
    print("\n[5] Lendas: ataque")
    r = setup()
    b = bard(esp=["lenda_goblin"]); r.players["b"] = b
    ally = make_player("a","Ana","warrior",1); ally["pos"]=[0,0]; ally["alive"]=True; r.players["a"] = ally
    gob = monster(type_="goblin"); orc = monster(type_="orc")
    check("bardo +1 ataque vs goblin estudado", r._lenda_atk_bonus(b, gob) == 1)
    check("bardo +0 ataque vs orc não estudado", r._lenda_atk_bonus(b, orc) == 0)
    check("aliado +0 sem Lendas Supremas", r._lenda_atk_bonus(ally, gob) == 0)

    # Supremas: aliados também ganham
    r = setup()
    b2 = bard(esp=["lenda_goblin","bardo_lendas_supremas"]); r.players["b"] = b2
    ally2 = make_player("a","Ana","warrior",1); ally2["pos"]=[0,0]; ally2["alive"]=True; r.players["a"] = ally2
    check("aliado +1 com Supremas", r._lenda_atk_bonus(ally2, monster(type_="goblin")) == 1)

    # bardo morto → sem bônus
    r = setup()
    bd = bard(esp=["lenda_goblin"]); bd["alive"] = False; r.players["b"] = bd
    ally3 = make_player("a","Ana","warrior",1); ally3["alive"]=True; r.players["a"] = ally3
    check("sem bardo vivo → _bardo_lendas None", r._bardo_lendas() is None)
    check("bardo morto → aliado sem bônus", r._lenda_atk_bonus(ally3, monster(type_="goblin")) == 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_bardo_espec.py`
Expected: FAIL — `AttributeError: ... '_lenda_atk_bonus'`.

- [ ] **Step 3: Adicionar os helpers de Lenda**

Em `server.py`, logo após `_provocacao_atk_vantagem` (Task 3, ~6605), inserir:

```python
    def _bardo_lendas(self):
        """Retorna o bardo vivo (dono das Lendas) da party, ou None."""
        return next((q for q in self.players.values()
                     if q.get("class_id") == "bard" and q.get("alive")), None)

    def _lenda_atk_bonus(self, atacante, monstro):
        """+1 de ataque vs a espécie estudada. Base: só o próprio bardo. Com
        Lendas Supremas: qualquer aliado, enquanto o bardo estiver vivo."""
        b = self._bardo_lendas()
        if not b or not tem_espec(b, f"lenda_{monstro.get('type', '')}"):
            return 0
        if atacante.get("id") == b["id"] or tem_espec(b, "bardo_lendas_supremas"):
            return 1
        return 0

    def _lenda_resist_bonus(self, alvo_player, fonte_monstro):
        """+1 nos saves contra as habilidades daquela espécie (mesma regra de grupo
        das Lendas de ataque). Só para jogadores; `fonte_monstro` None → 0."""
        if not fonte_monstro:
            return 0
        b = self._bardo_lendas()
        if not b or not tem_espec(b, f"lenda_{fonte_monstro.get('type', '')}"):
            return 0
        if alvo_player.get("id") == b["id"] or tem_espec(b, "bardo_lendas_supremas"):
            return 1
        return 0
```

> `_lenda_resist_bonus` é adicionado agora (junto dos irmãos) mas só é USADO na Task 5.

- [ ] **Step 4: Somar +1 no `eff_atk` de `handle_attack`**

Em `handle_attack`, no cálculo de `eff_atk` (~5224-5228), trocar:

```python
            eff_atk = (p["atk_bonus"] + p.get("skill_bonus_acerto", 0) + surv_mod + preso_pen
                       + cancao_acerto + gl_atk + self._pen(p, "ataque")
                       + self._mod_magia(p, "ataque")                        # Abençoar
                       - self._corrosao_arma_pen(p)                          # arma de madeira corroída
                       - (4 if target.get("oculto_sombras") else 0))         # alvo oculto nas sombras (corpo a corpo)
```

por:

```python
            eff_atk = (p["atk_bonus"] + p.get("skill_bonus_acerto", 0) + surv_mod + preso_pen
                       + cancao_acerto + gl_atk + self._pen(p, "ataque")
                       + self._mod_magia(p, "ataque")                        # Abençoar
                       + self._lenda_atk_bonus(p, target)                    # Lenda (bardo estudou a espécie)
                       - self._corrosao_arma_pen(p)                          # arma de madeira corroída
                       - (4 if target.get("oculto_sombras") else 0))         # alvo oculto nas sombras (corpo a corpo)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_bardo_espec.py`
Expected: PASS nas seções [1]-[5].

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_bardo_espec.py
git commit -m "feat(guilda): Lendas concedem +1 de ataque vs a especie estudada"
```

---

### Task 5: Lendas — bônus de resistência (+1) via `_testar_save(fonte=…)`

**Files:**
- Modify: `server.py` (`_testar_save` ~9485; sites de save de habilidade de monstro: 11286, 11650, 11761, 11827, 12293, 12611)
- Test: `tools/test_bardo_espec.py`

> **Escopo isolado — só habilidade de monstro vs jogador.** Os 6 sites abaixo têm o monstro `m` em escopo e o alvo é jogador (guardado por `target_obj["kind"] == "player"` ou equivalente). NÃO tocar: venenos (`_aplicar_veneno` 9512), doença-tick (9754/9790), paralisação (9165), escape de agarrão (11685), saves cujo alvo é monstro (11519/12703/13049), nem `_save_mostrado` (nenhum dos 6 passa por ele; os monstros que usam `_save_mostrado` miram animados, não jogadores). O helper `_lenda_resist_bonus` já devolve 0 quando `fonte` é None, então os demais sites ficam inertes.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [6] Lendas — resistência +1 (via _testar_save fonte)
    print("\n[6] Lendas: resistência")
    r = setup()
    b = bard(esp=["lenda_goblin"]); r.players["b"] = b
    gob = monster(type_="goblin")
    check("resist +1 vs habilidade de goblin (bardo)",
          r._lenda_resist_bonus(b, gob) == 1)
    check("resist +0 sem fonte", r._lenda_resist_bonus(b, None) == 0)
    check("resist +0 vs espécie não estudada",
          r._lenda_resist_bonus(b, monster(type_="orc")) == 0)

    # _testar_save soma o bônus quando recebe fonte monstro
    import random as _rnd
    _rnd.seed(1)
    # bônus base do bardo é determinístico; comparamos com/sem fonte no mesmo d20
    def _bonus_only(alvo, fonte):
        # roda com d20 fixo isolando o bônus
        _rnd.seed(42); _, _d, sb_no, _t = r._testar_save(alvo, "fortitude", 99)
        _rnd.seed(42); _, _d2, sb_yes, _t2 = r._testar_save(alvo, "fortitude", 99, fonte=fonte)
        return sb_yes - sb_no
    check("_testar_save(fonte=goblin) soma +1 p/ bardo dono",
          _bonus_only(b, gob) == 1)
    check("_testar_save(fonte=None) não soma",
          _bonus_only(b, None) == 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_bardo_espec.py`
Expected: FAIL — `_testar_save() got an unexpected keyword argument 'fonte'`.

- [ ] **Step 3: Adicionar `fonte` ao `_testar_save`**

Em `server.py`, trocar (~9485-9490):

```python
    def _testar_save(self, alvo, tipo_save, dificuldade, extra_mod=0):
        """Retorna (passou, d20, bonus, total). extra_mod: bônus/penalidade adicional ao save."""
        bonus = self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia") + extra_mod
        d20   = random.randint(1, 20)
        total = d20 + bonus
        return (total >= dificuldade), d20, bonus, total
```

por:

```python
    def _testar_save(self, alvo, tipo_save, dificuldade, extra_mod=0, fonte=None):
        """Retorna (passou, d20, bonus, total). extra_mod: bônus/penalidade adicional.
        fonte: monstro-origem do efeito (habilidade de criatura) — habilita o +1 de
        resistência da Lenda do Bardo contra aquela espécie (só p/ jogadores)."""
        bonus = (self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia")
                 + extra_mod + self._lenda_resist_bonus(alvo, fonte))
        d20   = random.randint(1, 20)
        total = d20 + bonus
        return (total >= dificuldade), d20, bonus, total
```

- [ ] **Step 4: Passar `fonte=m` nos 6 sites de habilidade de monstro**

Cada troca abaixo adiciona `, fonte=m` na chamada existente:

Site A (~11286, sistema modular de habilidade):
```python
        save_ok, d20, sb, stot = self._testar_save(target, ability["save"], ability["dc"])
```
→
```python
        save_ok, d20, sb, stot = self._testar_save(target, ability["save"], ability["dc"], fonte=m)
```

Site B (~11650, Derrubar):
```python
                save_ok, d20, sb, stot = self._testar_save(target, "reflexos", dc)
```
→
```python
                save_ok, d20, sb, stot = self._testar_save(target, "reflexos", dc, fonte=m)
```

Site C (~11761, Agarrar/crocodilo):
```python
            save_ok, d20, sb, stot = self._testar_save(target, "fortitude", dc)
```
→
```python
            save_ok, d20, sb, stot = self._testar_save(target, "fortitude", dc, fonte=m)
```

Site D (~11827, Constrição/cobra):
```python
            save_ok, d20, sb, stot = self._testar_save(target, "fortitude", dc)
```
→
```python
            save_ok, d20, sb, stot = self._testar_save(target, "fortitude", dc, fonte=m)
```

Site E (~12293, Infecção/zumbi):
```python
            ok, d20, sb, tot = self._testar_save(target, "fortitude", dc)
```
→
```python
            ok, d20, sb, tot = self._testar_save(target, "fortitude", dc, fonte=m)
```

Site F (~12611, Força Descomunal/ogro):
```python
                passou, d20, sb, stot = self._testar_save(target, "fortitude", 10)
```
→
```python
                passou, d20, sb, stot = self._testar_save(target, "fortitude", 10, fonte=m)
```

> Sites C e D têm a MESMA linha `self._testar_save(target, "fortitude", dc)`. São em funções diferentes (`_ai_crocodilo`/agarrar vs `_ai_cobra_constritora`) — edite pelo contexto (linha ~11761 e ~11827). Ambos recebem `, fonte=m`.

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_bardo_espec.py`
Expected: PASS nas seções [1]-[6].

- [ ] **Step 6: Regressão — suíte relacionada continua verde**

Run: `python tools/test_ladino_espec.py` e `python tools/test_paladino_espec.py`
Expected: ambas PASS (nenhuma regressão nos saves/combate).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_bardo_espec.py
git commit -m "feat(guilda): Lendas concedem +1 de resistencia vs habilidades da especie"
```

---

### Task 6: Cliente — getters + descrições dos painéis do Henrique

**Files:**
- Modify: `src/gameState.js` (getters ~1425 junto dos do ladino; export ~1669)
- Modify: `game.js` (descrições dos painéis de Canção/Provocação do bardo)

- [ ] **Step 1: Adicionar getters no `gameState.js`**

Em `src/gameState.js`, junto dos getters de especialização (após `ladinoEsconderLivre`, ~1430), inserir:

```javascript
  function bardoCancaoNivel(attr) {   // 'acerto'|'dano'|'ca'|'movimento'|'resistencia'
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    return e.includes('bardo_cancao_' + attr) ? 2 : 1;
  }
  function bardoCancaoSuprema() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('bardo_cancao_suprema');
  }
  function bardoProvocacaoNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('bardo_provocacao_3')) return 3;
    if (e.includes('bardo_provocacao_2')) return 2;
    return 1;
  }
  function bardoLendasSupremas() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('bardo_lendas_supremas');
  }
```

- [ ] **Step 2: Exportar os getters**

Em `src/gameState.js`, no `return { ... }` (junto de `ladinoEsconderLivre`, ~1669), adicionar:

```javascript
    bardoCancaoNivel,
    bardoCancaoSuprema,
    bardoProvocacaoNivel,
    bardoLendasSupremas,
```

- [ ] **Step 3: Refletir nível nas descrições (Canção)**

No `game.js`, no painel que lista os atributos da Canção Heroica do bardo (procure por `CANCAO_ATRIBUTOS` ou o texto "Canção Heroica" / os labels Acerto/Dano/Armadura/Movimento/Resistência no HUD do bardo). Para cada atributo, exibir o bônus corrente `+${GS.bardoCancaoNivel(id)}` na label e, quando `GS.bardoCancaoSuprema()`, anexar uma nota "(manutenção reduzida)". Manter o layout existente; só interpolar o número. Se o painel hoje mostra "+1" fixo, trocar por `+${GS.bardoCancaoNivel(id)}`.

- [ ] **Step 4: Refletir nível nas descrições (Provocação)**

No `game.js`, no botão/tooltip de Provocação do bardo, quando `GS.bardoProvocacaoNivel() >= 2` acrescentar "(II: desvantagem dura toda a provocação, +2 CA e vantagem contra o alvo)"; quando `=== 3` acrescentar "(III: aliados também atacam com vantagem por 1 rodada)". Texto informativo apenas.

- [ ] **Step 5: Sanidade — sem erro de sintaxe JS**

Run: `node -e "require('./src/gameState.js')"` (se o módulo for CommonJS-safe) ou abra o jogo (Task 7) e confira o console. Expected: sem erro de parse.

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): cliente reflete niveis de Cancao/Provocacao do Bardo"
```

---

### Task 7: Verificação E2E (smoke) + docs

**Files:**
- Modify: `CLAUDE.md`
- Test: manual via preview + suíte

- [ ] **Step 1: Suíte verde**

Run: `python tools/test_bardo_espec.py`
Expected: `PASS=N FAIL=0`.

- [ ] **Step 2: Smoke E2E (compra na Guilda)**

Bump temporário do ouro inicial do bardo para testar compra: em `server.py`, `CLASSES["bard"]["start_gold"]` → valor alto (ex.: 2000) SÓ para o smoke. Subir o servidor com `preview_start` (config "game"), criar sala, escolher Henrique, iniciar, abrir a Guilda e comprar `bardo_provocacao_2` + uma `lenda_goblin`; confirmar débito de ouro e persistência. Verificar via `preview_console_logs`/`preview_network` que `guild_buy` retorna sucesso e o `city_state` traz os ids em `guild_owned.especializacoes`.

- [ ] **Step 3: Reverter o bump e limpar saves**

Reverter `start_gold` do bardo ao valor original. Remover saves gerados no smoke:
```bash
rm -rf saves/
```
(Confirmar que `saves/` é gitignored — não deve aparecer em `git status`.)

- [ ] **Step 4: Documentar na CLAUDE.md**

Adicionar, ao fim do bloco de blockquotes de especializações (após o parágrafo do Ladino/Fase 1d), um novo parágrafo:

```markdown
> **Especializações do Bardo (Fase 1e):** gateiam as 3 linhas de Henrique.
> **Canção Heroica:** 5 nós `bardo_cancao_{acerto,dano,ca,movimento,resistencia}`
> (100 cada) sobem aquele atributo de +1 para +2 (`_cancao_nivel_atributo` em
> `_aplicar_buffs_cancao`); `bardo_cancao_suprema` (200) reduz a manutenção em
> -1🍖/-1💧 (`_cancao_custo_reducao`, aplicado na ativação; `cancao_custo` guarda o
> valor já reduzido). **Provocação:** `bardo_provocacao_2` (150) faz a desvantagem
> durar toda a provocação (não zera `provocado_turno_efeito` enquanto o provocador
> tem a espec), dá +2 CA ao bardo (`_provocacao_ca_bonus` nos sites de ataque de
> monstro) e vantagem ao bardo contra o alvo; `bardo_provocacao_3` (200, requer _2)
> estende a vantagem a todos os aliados por 1 rodada (`provocado_aliados_vantagem_round`).
> Vantagem via `_provocacao_atk_vantagem` em `handle_attack`. **Lendas:** catálogo
> gerado de `MONSTER_DEFS` (`_gerar_catalogo_lendas` + `GUILD_CATALOG.update`, preço
> por tier T1 60/T2 90/T3 120/T4 200) — cada `lenda_<tipo>` dá +1 de ataque
> (`_lenda_atk_bonus` em `eff_atk`) e +1 de resistência (`_lenda_resist_bonus` via
> novo param `fonte` de `_testar_save`, passado nos 6 sites de habilidade de
> monstro) contra a espécie; `bardo_lendas_supremas` (300) estende ambos os bônus a
> todo o grupo enquanto Henrique vive. Cliente: `GS.bardoCancaoNivel/
> bardoCancaoSuprema/bardoProvocacaoNivel/bardoLendasSupremas`. Teste:
> `tools/test_bardo_espec.py`.
```

- [ ] **Step 5: Commit final**

```bash
git add CLAUDE.md server.py
git commit -m "docs(guilda): documentar especializacoes do Bardo (Fase 1e)"
```

---

## Auto-revisão (checklist do autor do plano)

- **Cobertura do spec:** Canção II (5 nós) → T1/T2; Canção Suprema → T1/T2; Provocação II/III → T1/T3; Lendas Avançadas (geradas) → T1/T4/T5; Lendas Supremas → T1/T4/T5; cliente → T6; testes → T1-T5; docs → T7. ✔
- **Sem placeholders:** todo passo de código traz o código real. ✔
- **Consistência de nomes:** helpers `_cancao_nivel_atributo`, `_cancao_custo_reducao`, `_provocador`, `_provocacao_ca_bonus`, `_provocacao_atk_vantagem`, `_bardo_lendas`, `_lenda_atk_bonus`, `_lenda_resist_bonus`; campos `provocado_aliados_vantagem_round`, `cancao_custo`, `buffs_cancao`; getters `bardoCancaoNivel/bardoCancaoSuprema/bardoProvocacaoNivel/bardoLendasSupremas` — usados de forma idêntica em todas as tasks. ✔
- **Risco isolado (resistência):** `fonte=None` default + `_lenda_resist_bonus` guarda None/espécie/dono → sites não-monstro ficam inertes; só 6 sites recebem `fonte=m`, enumerados por linha e função. ✔
