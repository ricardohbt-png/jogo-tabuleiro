# Progressão de XP no modelo D&D 3.5 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a curva de XP que dispara por uma progressão 3.5 (prêmio por ND × nível próprio de cada herói, limiares 1000/3000/6000…, teto 20) e recalibrar a campanha Sombras para o ritmo 1→2→3→4.

**Architecture:** As regras ficam em funções puras module-level no `server.py`, ao lado de `monster_cr`/`trap_cr`. O XP do jogador passa a ser acumulado, e uma porta única `_conceder_xp` sobe quantos níveis couberem. Os saves antigos migram em `restore_character`. O cliente só lê `xp_nivel`/`xp_proximo` do payload. O gerador da campanha usa as mesmas funções para calibrar o XP dos objetivos.

**Tech Stack:** Python 3 (server.py, suítes `tools/test_*.py` com `check()` próprio), JS vanilla (game.js), dicionários `src/lang/*.js`.

**Spec:** `docs/superpowers/specs/2026-09-26-progressao-xp-dnd35-design.md`

---

## Antes de começar — regras deste repositório

- Trabalhe no worktree `C:\Users\RICARDO\Desktop\jogo tabuleiro\.claude\worktrees\campanha-sombras` (branch `feat/campanha-sombras`). Nunca no checkout principal.
- `server.py`, `game.js` e `CLAUDE.md` estão em **CRLF**, e vários comentários do `server.py` têm acentos corrompidos (`nÃ­vel`). Edite com a ferramenta Edit copiando o trecho exatamente como o Read mostra. Não use `replace("...\n...")` por script nem PowerShell.
- Rode as suítes da raiz do worktree com `PYTHONIOENCODING=utf-8`. Confira o **texto** (`N passaram, 0 falharam` e nenhum `❌`), não só o exit code.
- Não suba servidor na porta 8765: ela é do autor.

## Estrutura de arquivos

| Arquivo | Mudança |
|---|---|
| `server.py` | funções puras de XP (substituem `TRAP_XP_POR_CR`/`trap_xp`); `_conceder_xp`/`_subir_um_nivel` (substituem `_check_level_up`); 4 pontos de concessão; `_calc_monster_xp`/`_avg_level` saem; migração em `restore_character`; `xp_modelo` em `make_player`/`_DURABLE_FIELDS`; `xp_nivel`/`xp_proximo` nos dois payloads |
| `tools/test_xp_progressao.py` | **novo** — regras, concessão, migração, payload |
| `tools/test_modo_mestre.py` | seções [21]/[22] com a regra nova |
| `tools/test_magias_slots.py` | seção [7] usa `_conceder_xp` |
| `tools/editor_bestiary.js` | comentário cita `_subir_um_nivel` |
| `game.js`, `game.css` | barra de XP na ficha da cidade; tooltip e ficha do mestre sem o `xp` fixo |
| `src/lang/interface.js`, `src/lang/narracao.js` | chave nova da barra, narração de armadilha com valores diferentes, `caract_linha` sem XP, `sigla_xp` removida |
| `tools/gerar_campanha_sombras.py` | `METAS_NIVEL`, `curva_campanha`, `calibrar_xp_objetivos`, relatório da curva |
| `tools/test_campanha_sombras.py` | seção [7] passa a cobrar |
| `dungeons/sombras_*.json`, `tools/.sombras_assinaturas.json`, `tools/editor_dungeons.js` | regerados |
| `CLAUDE.md` | nota nova + dois parágrafos corrigidos |

---

### Task 1: Regras puras de XP

**Files:**
- Modify: `server.py` (bloco `TRAP_XP_POR_CR`/`trap_cr`/`trap_xp`, ~linhas 8813-8832)
- Create: `tools/test_xp_progressao.py`

- [ ] **Step 1: Escrever a suíte com a seção [1] (falha)**

Create `tools/test_xp_progressao.py`:

```python
"""Progressão de XP no modelo D&D 3.5. Roda da raiz: python tools/test_xp_progressao.py
Spec: docs/superpowers/specs/2026-09-26-progressao-xp-dnd35-design.md
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S                       # noqa: E402
from server import GameRoom, make_player  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    r = GameRoom("XP")
    async def noop(*a, **k):
        pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.phase = "playing"
    return r


# ─── [1] Regras puras ───────────────────────────────────────────────────────
def secao_regras():
    print("\n[1] Regras puras — xp_premio / xp_limiar / nivel_por_xp")
    check("nível 1 × ND 1 = 300", S.xp_premio(1, 1) == 300)
    check("ND igual ao nível = 300 × nível", all(S.xp_premio(n, n) == 300 * n for n in range(1, 21)))
    check("nível 1 × ND 3 = 3× o ND 1", S.xp_premio(1, 3) == 900)
    check("ND fracionário = fração do ND 1 (goblin ¼ no nível 1 → 75)", S.xp_premio(1, 0.25) == 75)
    check("ND fracionário segue o nível (¼ no nível 5 → 94)", S.xp_premio(5, 0.25) == 94)
    check("ND 0 não rende", S.xp_premio(1, 0) == 0)
    check("8 NDs abaixo não rende (nível 9 × ND 1)", S.xp_premio(9, 1) == 0)
    check("7 NDs abaixo ainda rende (nível 8 × ND 1)", S.xp_premio(8, 1) > 0)
    check("teto em nível + 7 (ND 20 no nível 1 = ND 8)", S.xp_premio(1, 20) == S.xp_premio(1, 8) == 3394)
    check("nível acima de 20 usa a linha do 20", S.xp_premio(38, 20) == S.xp_premio(20, 20))
    check("ND inválido não rende", S.xp_premio(1, "abc") == 0)
    check("parte por herói divide pelos vivos", S.xp_por_heroi(1, 1, 4) == 75)
    check("parte por herói tem mínimo 1", S.xp_por_heroi(1, 0.01, 6) == 1)
    check("parte sem prêmio é 0", S.xp_por_heroi(9, 1, 4) == 0)
    check("limiares 0/1000/3000/6000/10000",
          [S.xp_limiar(n) for n in range(1, 6)] == [0, 1000, 3000, 6000, 10000])
    check("limiar do nível 20 = 190000", S.xp_limiar(20) == 190000)
    check("nivel_por_xp nas bordas",
          [S.nivel_por_xp(x) for x in (0, 999, 1000, 2999, 3000)] == [1, 1, 2, 2, 3])
    check("nivel_por_xp tem teto 20", S.nivel_por_xp(10 ** 9) == S.XP_NIVEL_MAX == 20)
    check("xp_proximo_nivel", S.xp_proximo_nivel(1) == 1000 and S.xp_proximo_nivel(20) is None)
    check("migração: nível 2 com 30/60 → 2000", S.xp_migrado(2, 30) == 2000)
    check("migração: sobra acima do limiar antigo trava em 100%", S.xp_migrado(1, 999) == 1000)
    check("migração: nível 20+ fica no limiar do 20", S.xp_migrado(38, 5) == S.xp_limiar(20))


async def main():
    secao_regras()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
```

Os números saem da fórmula da spec: `xp_premio(5, 1) = round(1500 × 2^-2) = 375`, então `xp_premio(5, 0.25) = round(93,75) = 94`; e `xp_premio(1, 8) = round(300 × 2^3,5) = 3394`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_xp_progressao.py`
Expected: `AttributeError: module 'server' has no attribute 'xp_premio'`

- [ ] **Step 3: Implementar as funções puras**

Em `server.py`, **apague** a linha `TRAP_XP_POR_CR = 20` (e a linha em branco que a segue) e a função inteira:

```python
def trap_xp(cr):
    """XP de uma armadilha derivado do seu cr (dividido entre os heróis vivos)."""
    return round(float(cr) * TRAP_XP_POR_CR)
```

No lugar de `trap_xp`, logo depois de `trap_cr`, insira:

```python
# ─── Progressão de XP — modelo D&D 3.5 ──────────────────────────────────────
# Spec: docs/superpowers/specs/2026-09-26-progressao-xp-dnd35-design.md
# O XP do jogador é ACUMULADO (nunca subtraído); o nível é consequência dele.
XP_NIVEL_MAX = 20


def xp_premio(nivel, nd):
    """Prêmio TOTAL de um desafio de ND `nd` para um herói de nível `nivel`, antes de
    dividir pelo grupo. É a fórmula que gera a tabela 2-6 do DMG 3.5: ND abaixo de 1
    vale a fração do ND 1; 8 NDs abaixo do herói não rende; acima de nível+7, trava."""
    L = max(1, min(XP_NIVEL_MAX, int(nivel or 1)))
    try:
        nd = float(nd)
    except (TypeError, ValueError):
        return 0
    if nd <= 0:
        return 0
    if nd < 1:
        return round(nd * xp_premio(L, 1))
    if nd <= L - 8:
        return 0
    nd = min(nd, L + 7)
    return round(300 * L * 2 ** ((nd - L) / 2))


def xp_por_heroi(nivel, nd, vivos):
    """Parte de UM herói: prêmio com o nível DELE ÷ heróis vivos (mín. 1 se houver prêmio)."""
    premio = xp_premio(nivel, nd)
    return max(1, premio // max(1, int(vivos))) if premio > 0 else 0


def xp_limiar(n):
    """XP ACUMULADO exigido para estar no nível n: 0, 1000, 3000, 6000 … 190000."""
    n = max(1, int(n))
    return 500 * n * (n - 1)


def nivel_por_xp(xp):
    """Maior nível (≤ XP_NIVEL_MAX) cujo limiar cabe em `xp`."""
    n = 1
    while n < XP_NIVEL_MAX and xp_limiar(n + 1) <= xp:
        n += 1
    return n


def xp_proximo_nivel(nivel):
    """Limiar do próximo nível, ou None no nível máximo (vai ao cliente)."""
    return None if int(nivel) >= XP_NIVEL_MAX else xp_limiar(int(nivel) + 1)


def xp_migrado(nivel, xp_antigo):
    """Converte o XP da curva antiga (sobra DENTRO do nível, limiar nível×30) para o
    acumulado 3.5, preservando o nível e a fração de progresso."""
    L = max(1, min(XP_NIVEL_MAX, int(nivel or 1)))
    base = xp_limiar(L)
    if L >= XP_NIVEL_MAX:
        return base
    frac = min(1.0, max(0.0, float(xp_antigo or 0) / (L * 30)))
    return base + round(frac * (xp_limiar(L + 1) - base))
```

`trap_xp` ainda é chamado em `_conceder_xp_armadilha`. A Task 2 troca essa chamada; até lá o servidor importa normalmente, porque a chamada só roda em partida.

- [ ] **Step 4: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_xp_progressao.py`
Expected: `22 passaram, 0 falharam`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_xp_progressao.py
git commit -m "feat(xp): regras puras da progressao 3.5

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Porta única de concessão e os 4 pontos

**Files:**
- Modify: `server.py` — `_check_level_up` (~41364), `_monster_dies` (~41074), `_conceder_xp_armadilha` (~33575), `_avg_level`/`_calc_monster_xp` (~33559), `_conceder_objetivo_reward` (~41430), entrada "experiente" (~9765)
- Modify: `src/lang/narracao.js`, `tools/test_modo_mestre.py`, `tools/test_magias_slots.py`, `tools/editor_bestiary.js`
- Test: `tools/test_xp_progressao.py`

- [ ] **Step 1: Acrescentar a seção [2] à suíte (falha)**

Em `tools/test_xp_progressao.py`, antes de `async def main():`, insira:

```python
# ─── [2] Concessão ──────────────────────────────────────────────────────────
async def secao_concessao():
    print("\n[2] Concessão — _conceder_xp, monstro, armadilha, objetivo")
    r = sala()
    p = make_player("p1", "A", "warrior", 0)
    r.players = {"p1": p}
    await r._conceder_xp(p, 999)
    check("999 XP: continua no nível 1, XP acumulado", p["level"] == 1 and p["xp"] == 999)
    await r._conceder_xp(p, 1)
    check("1000 XP: nível 2 sem descontar XP", p["level"] == 2 and p["xp"] == 1000)
    await r._conceder_xp(p, 9000)
    check("vários níveis de uma vez (10000 → nível 5)", p["level"] == 5 and p["xp"] == 10000)
    check("ganhos por nível aplicados a cada nível", p["level_bonus"] == 5)
    await r._conceder_xp(p, 0)
    await r._conceder_xp(p, -50)
    check("zero/negativo não mexe", p["xp"] == 10000)
    await r._conceder_xp(p, 10 ** 7)
    check("teto no nível 20", p["level"] == 20)

    # Ficha migrada acima do XP: não rebaixa nem sobe de novo
    q = make_player("p9", "Q", "warrior", 0)
    q["level"] = 7; q["xp"] = 100
    await r._conceder_xp(q, 50)
    check("nível acima do XP não é rebaixado", q["level"] == 7 and q["xp"] == 150)

    # Monstro: cada herói com o PRÓPRIO nível
    r = sala(); r.rooms = []
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    a = make_player("p1", "A", "warrior", 0)
    b = make_player("p2", "B", "warrior", 0)
    await r._conceder_xp(b, S.xp_limiar(5))
    r.players = {"p1": a, "p2": b}
    gdef = next(m for m in S.MONSTER_DEFS if m["type"] == "goblin")
    g = S.make_monster(gdef, {"id": 1, "cx": 5, "cy": 5}); g["pos"] = [5, 5]; g["hp"] = 0
    r.monsters[g["id"]] = g
    xa, xb = a["xp"], b["xp"]
    await r._monster_dies(g, "p1")
    check("goblin: nível 1 ganha 75÷2 = 37", a["xp"] - xa == 37)
    check("goblin: nível 5 ganha 94÷2 = 47", b["xp"] - xb == 47)

    # Armadilha: tabela 3.5 com o trap_cr
    r = sala()
    h = make_player("h", "H", "warrior", 0)
    r.players = {"h": h}
    arm = {"id": "a1", "tipo": "mina_terrestre", "pos": [2, 2]}
    await r._conceder_xp_armadilha(arm)
    check("mina (cr .75) no nível 1 → 225", h["xp"] == 225)
    x1 = h["xp"]; await r._conceder_xp_armadilha(arm)
    check("armadilha não concede 2ª vez", h["xp"] == x1)

    # Objetivo: total do autor dividido pelos vivos, pela porta única
    r = sala()
    a = make_player("p1", "A", "warrior", 0)
    b = make_player("p2", "B", "mage", 0)
    r.players = {"p1": a, "p2": b}
    loot = []
    await r._conceder_objetivo_reward({"type": "kill_all", "xp": 2400, "reward": {"gold": 0}},
                                      is_primary=True, loot_acc=loot)
    check("objetivo 2400 ÷ 2 = 1200 cada, nível 2", a["xp"] == 1200 and a["level"] == 2)
    check("mago sobe e ganha escolha de magia", b["level"] == 2 and b.get("pending_spell_pick"))
```

E troque o `main` por:

```python
async def main():
    secao_regras()
    await secao_concessao()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_xp_progressao.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_conceder_xp'`

- [ ] **Step 3: `_conceder_xp` + `_subir_um_nivel` no lugar de `_check_level_up`**

Em `server.py`, substitua o método inteiro `async def _check_level_up(self, p):`, da linha `async def _check_level_up(self, p):` até `await self._enviar_spell_pick_prompt(p)` inclusive, por:

```python
    async def _conceder_xp(self, p, qtd):
        """Porta ÚNICA de XP (modelo 3.5): soma ao acumulado e sobe quantos níveis
        couberem. Nunca subtrai XP. Ficha migrada com nível acima do que o XP
        justifica não é rebaixada — só volta a subir quando o XP alcançar."""
        qtd = int(qtd or 0)
        if qtd <= 0:
            return
        p["xp"] = int(p.get("xp", 0) or 0) + qtd
        while p.get("level", 1) < nivel_por_xp(p["xp"]):
            await self._subir_um_nivel(p)

    async def _subir_um_nivel(self, p):
        """Ganhos de UM nível. Quem decide subir é `_conceder_xp`."""
        p["level"] += 1
        p["level_bonus"] = p["level"]   # level bonus = current level
        regra = LEVEL_PROGRESSAO[p["class_id"]]
        ganho_hp = regra["hp"] + get_bonus_constituicao(p["con_"])
        p["max_hp"] += ganho_hp
        p["hp"] = min(p["max_hp"], p["hp"] + ganho_hp)
        p["atk_bonus"] += 1
        p["base_atk_bonus"] += 1
        if p["level"] >= 3 and p["level"] % 2 == 1:
            for save in regra["saves_2"]:
                p[save] += 1
        if p["level"] >= 4 and (p["level"] - 1) % 3 == 0:
            for save in regra["saves_3"]:
                p[save] += 1
        p["fome_max_base"] = int(p.get("fome_max_base", p.get("fome_max", 100))) + regra["fome"]
        p["sede_max_base"] = int(p.get("sede_max_base", p.get("sede_max", 100))) + regra["sede"]
        _recalcular_maximos_sobrevivencia(p)
        p["fome"] = min(p["fome_max"], p["fome"] + regra["fome"])
        p["sede"] = min(p["sede_max"], p["sede"] + regra["sede"])
        _garantir_slots_guilda(p)
        await self.gm_say(T("narracao.subiu_para_o_nivel_pv_e_1_em_ataque_ganh", heroi=p['name'], p_level=p['level'], ganho_hp=ganho_hp))
        if p.get("class_id") in ("mage", "cleric"):
            # Slot novo do nível já entra cheio (slots_max_para usa o novo level).
            circ = NIVEL_NOVA_MAGIA.get(p["level"])
            if circ:
                p.setdefault("pending_spell_pick", []).append(circ)
                await self._enviar_spell_pick_prompt(p)
```

É o corpo antigo, sem `threshold`, sem `p["xp"] -= threshold` e desindentado um nível. Nenhum ganho mudou.

- [ ] **Step 4: Monstro**

Em `_monster_dies`, substitua o comentário (com acentos corrompidos) e as 5 linhas:

```python
        share_xp, alive_count = self._calc_monster_xp(m)
        for p in self.players.values():
            if p["alive"]:
                p["xp"] += share_xp
                await self._check_level_up(p)
```

por:

```python
        # XP (modelo 3.5): cada herói vivo consulta a tabela com o PRÓPRIO nível.
        vivos = [p for p in self.players.values() if p["alive"]]
        nd = monster_cr(m)
        for p in vivos:
            await self._conceder_xp(p, xp_por_heroi(p.get("level", 1), nd, len(vivos)))
```

Depois apague `_avg_level` e `_calc_monster_xp` inteiros. Antes, confirme que não sobrou leitor: `grep -n "_avg_level\|_calc_monster_xp" server.py tools/*.py` deve dar só as definições.

- [ ] **Step 5: Armadilha**

Em `_conceder_xp_armadilha`, substitua do `total = trap_xp(trap_cr(meta))` até o `await self.gm_say(...)` final:

```python
        total = trap_xp(trap_cr(meta))
        arm["xp_concedido"] = True
        if total <= 0:
            return
        share = max(1, total // len(vivos))
        for p in vivos:
            p["xp"] = p.get("xp", 0) + share
            await self._check_level_up(p)
        await self.gm_say(T("narracao.armadilha_superada_xp_para_o_grupo", share=share))
```

por:

```python
        nd = trap_cr(meta)
        arm["xp_concedido"] = True
        partes = {p["id"]: xp_por_heroi(p.get("level", 1), nd, len(vivos)) for p in vivos}
        if not any(partes.values()):
            return
        for p in vivos:
            await self._conceder_xp(p, partes[p["id"]])
        valores = set(partes.values())
        if len(valores) == 1:
            await self.gm_say(T("narracao.armadilha_superada_xp_para_o_grupo", share=valores.pop()))
        else:
            # Heróis de níveis diferentes ganham valores diferentes: sem número.
            await self.gm_say(T("narracao.armadilha_superada_xp_variavel"))
```

Atualize a docstring do método: troque "dividido entre os heróis vivos" por "pela tabela 3.5 com o nível de cada herói, dividido entre os vivos".

Em `src/lang/narracao.js`, logo após a entrada `"narracao.armadilha_superada_xp_para_o_grupo": {…},`, acrescente:

```js
  "narracao.armadilha_superada_xp_variavel": {
    "en": "✨ Trap overcome — the group gains experience!",
    "pt": "✨ Armadilha superada — o grupo ganha experiência!"
  },
```

- [ ] **Step 6: Objetivo e herói "experiente"**

Em `_conceder_objetivo_reward`, troque:

```python
            if xp_share:
                p["xp"] += xp_share
                await self._check_level_up(p)
```

por:

```python
            if xp_share:
                await self._conceder_xp(p, xp_share)
```

Na aprovação de entrada da campanha (regra `experienced`), troque:

```python
                    while fresh["level"] < target:
                        fresh["xp"] = fresh["level"] * 30
                        await self._check_level_up(fresh)
```

por:

```python
                    await self._conceder_xp(fresh, xp_limiar(target) - fresh.get("xp", 0))
```

Confira: `grep -n "_check_level_up\|trap_xp\|TRAP_XP_POR_CR" server.py` não deve dar nada.

- [ ] **Step 7: Testes antigos que citam a regra antiga**

`tools/test_magias_slots.py`, seção [7], troque:

```python
    p["xp"] = 999   # garante subir de nível
    await r._check_level_up(p)
```

por:

```python
    await r._conceder_xp(p, 1000)   # limiar do nível 2
```

`tools/test_modo_mestre.py`, seção [21], troque o título e a linha do `trap_xp`:

```python
    print("\n[21] ND/XP de armadilha — trap_cr/trap_xp")
```
→
```python
    print("\n[21] ND/XP de armadilha — trap_cr + tabela 3.5")
```
e
```python
    check("trap_xp deriva do cr", S.trap_xp(0.5) == round(0.5 * S.TRAP_XP_POR_CR))
```
→
```python
    check("XP de armadilha segue a tabela 3.5 pelo cr", S.xp_por_heroi(1, 0.5, 1) == 150)
```

Seção [22], troque:

```python
    check("XP concedido no 1º (mina cr .75 → 15)", r.players["h"]["xp"] == 15)
```

por:

```python
    check("XP concedido no 1º (mina cr .75, nível 1 → 225)", r.players["h"]["xp"] == 225)
```

`tools/editor_bestiary.js`: no comentário `// números abaixo espelham make_player + _check_level_up: equipamentos`, troque `_check_level_up` por `_subir_um_nivel`.

- [ ] **Step 8: Rodar**

Run:
```bash
PYTHONIOENCODING=utf-8 python tools/test_xp_progressao.py
PYTHONIOENCODING=utf-8 python tools/test_modo_mestre.py | tail -3
PYTHONIOENCODING=utf-8 python tools/test_magias_slots.py | tail -3
PYTHONIOENCODING=utf-8 python tools/test_objetivos.py | tail -3
```
Expected: `35 passaram, 0 falharam` na primeira; `0 falharam` nas outras (a de mestre segue com 364).

- [ ] **Step 9: Commit**

```bash
git add server.py src/lang/narracao.js tools/test_xp_progressao.py tools/test_modo_mestre.py tools/test_magias_slots.py tools/editor_bestiary.js
git commit -m "feat(xp): porta unica _conceder_xp; monstro, armadilha e objetivo na tabela 3.5

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Migração de saves e payload

**Files:**
- Modify: `server.py` — `_DURABLE_FIELDS` (~2486), `restore_character` (~2537), `make_player` (~8654), `_city_state_payload` (~10018), `_game_state_payload` (~41940)
- Test: `tools/test_xp_progressao.py`

- [ ] **Step 1: Seção [3] (falha)**

Antes de `async def main():` insira:

```python
# ─── [3] Saves antigos e payload ────────────────────────────────────────────
def secao_migracao_payload():
    print("\n[3] Migração de save e xp_nivel/xp_proximo no payload")
    p = make_player("p1", "A", "warrior", 0)
    check("ficha nova nasce no modelo 2", p.get("xp_modelo") == 2)
    check("xp_modelo é durável", "xp_modelo" in S.snapshot_character(p))

    antigo = {"level": 2, "xp": 30}              # save antigo: sem xp_modelo
    novo = make_player("p1", "A", "warrior", 0)
    S.restore_character(novo, antigo)
    check("save antigo: nível 2 com 30/60 → 2000", novo["level"] == 2 and novo["xp"] == 2000)
    check("save antigo ganha a marca", novo.get("xp_modelo") == 2)

    atual = {"level": 2, "xp": 1234, "xp_modelo": 2}
    outro = make_player("p1", "A", "warrior", 0)
    S.restore_character(outro, atual)
    check("save já migrado fica intacto", outro["xp"] == 1234)

    inflado = {"level": 38, "xp": 5}
    alto = make_player("p1", "A", "warrior", 0)
    S.restore_character(alto, inflado)
    check("ficha inflada mantém o nível", alto["level"] == 38 and alto["xp"] == S.xp_limiar(20))

    r = sala()
    q = make_player("p1", "A", "warrior", 0)
    q["xp"] = 1500; q["level"] = 2
    r.players = {"p1": q}
    cidade = r._city_state_payload()["players"][0]
    check("city_state traz xp_nivel/xp_proximo",
          cidade["xp_nivel"] == 1000 and cidade["xp_proximo"] == 3000)
    q["level"] = 20
    cidade = r._city_state_payload()["players"][0]
    check("nível 20 → xp_proximo None", cidade["xp_proximo"] is None)
```

E chame `secao_migracao_payload()` no `main`, depois de `await secao_concessao()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_xp_progressao.py`
Expected: `❌ ficha nova nasce no modelo 2`, e em seguida falhas ou `KeyError: 'xp_nivel'`.

- [ ] **Step 3: Implementar**

`_DURABLE_FIELDS`: troque `"gold", "hp", "max_hp", "xp", "level", "level_bonus",` por `"gold", "hp", "max_hp", "xp", "xp_modelo", "level", "level_bonus",`.

`restore_character`: logo após o laço `for k in _DURABLE_FIELDS:` (antes do comentário "Migra fichas antigas…"), insira:

```python
    # Curva de XP 3.5 (2026-09-26): ficha salva antes dela guarda a SOBRA dentro do
    # nível (limiar nível×30). Converte para o acumulado mantendo nível e progresso.
    if snap.get("xp_modelo") != 2:
        player["xp"] = xp_migrado(player.get("level", 1), snap.get("xp", 0))
        player["xp_modelo"] = 2
```

`restore_character` fica no topo do arquivo, antes da definição de `xp_migrado`. Não há problema, porque o nome só é resolvido quando a função roda.

`make_player`: troque `"xp": 0, "level": 1, "renome_individual": 0,` por `"xp": 0, "xp_modelo": 2, "level": 1, "renome_individual": 0,`.

`_city_state_payload`, no `dict(p, …)`, logo após `initiative=self.initiative_value(p),`, acrescente:

```python
                            xp_nivel=xp_limiar(p.get("level", 1)),
                            xp_proximo=xp_proximo_nivel(p.get("level", 1)),
```

`_game_state_payload`, no `snapshot = dict(p, …)`, logo após `initiative=self.initiative_value(p),`, acrescente as mesmas duas linhas (com a indentação daquele bloco).

- [ ] **Step 4: Rodar**

Run:
```bash
PYTHONIOENCODING=utf-8 python tools/test_xp_progressao.py
PYTHONIOENCODING=utf-8 python tools/test_savegames.py | tail -3
```
Expected: `43 passaram, 0 falharam`; savegames `0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_xp_progressao.py
git commit -m "feat(xp): migra saves para o XP acumulado; xp_nivel/xp_proximo no payload

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Cliente — barra de XP e XP fixo fora das fichas de monstro

**Files:**
- Modify: `game.js` (~23671 ficha da cidade; ~14811 tooltip do monstro; ~21359 ficha do mestre), `game.css` (~1320), `src/lang/interface.js`

- [ ] **Step 1: Ficha da cidade**

Em `game.js`, troque:

```js
  xp.innerHTML = `<span>${t('ui.ficha.experiencia')}</span><b>${player.xp ?? 0} XP</b>`;
```

por:

```js
  // XP acumulado (modelo 3.5): o servidor manda o início (xp_nivel) e o fim
  // (xp_proximo) do nível atual — o cliente não duplica a tabela.
  const xpTotal = Number(player.xp ?? 0);
  const fmtXp = n => Number(n).toLocaleString(I18N.lang === 'en' ? 'en-US' : 'pt-BR');
  if (player.xp_proximo != null) {
    const base = Number(player.xp_nivel ?? 0), prox = Number(player.xp_proximo);
    const pct = Math.max(0, Math.min(100, (xpTotal - base) / Math.max(1, prox - base) * 100));
    xp.innerHTML = `<span>${t('ui.ficha.experiencia')}</span>`
      + `<b>${t('ui.ficha.xp_de', {xp: fmtXp(xpTotal), prox: fmtXp(prox)})}</b>`
      + `<div class="fc-xp-bar"><div style="width:${pct.toFixed(1)}%"></div></div>`;
  } else {
    xp.innerHTML = `<span>${t('ui.ficha.experiencia')}</span><b>${fmtXp(xpTotal)} XP</b>`;
  }
```

Em `game.css`, na regra `.fc-xp-display{ display:flex; align-items:center; justify-content:space-between;`, acrescente `flex-wrap:wrap;` depois de `justify-content:space-between;`. Logo após a regra `.fc-xp-display b{ … }`, acrescente:

```css
.fc-xp-bar{ flex-basis:100%; height:4px; margin-top:5px; border-radius:2px;
  background:rgba(0,0,0,.35); overflow:hidden; }
.fc-xp-bar > div{ height:100%; background:#f0d98a; }
```

Em `src/lang/interface.js`, logo após a entrada `"ui.ficha.experiencia": {…},`, acrescente:

```js
  "ui.ficha.xp_de": {
    "en": "{xp} / {prox} XP",
    "pt": "{xp} / {prox} XP"
  },
```

- [ ] **Step 2: Tooltip do monstro e ficha do mestre**

Em `game.js` (~14811), troque:

```js
      <div>🏅 <b>${TIER[m.tier]||m.tier||'?'}</b> &nbsp;·&nbsp; ✨ ${t('ui.hud.sigla_xp')} <b>${m.xp ?? '?'}</b>${!m.attacks && m.gold != null ? ` &nbsp;·&nbsp; 🪙 <b>${m.gold}</b>` : ''}</div>
```

por:

```js
      <div>🏅 <b>${TIER[m.tier]||m.tier||'?'}</b>${!m.attacks && m.gold != null ? ` &nbsp;·&nbsp; 🪙 <b>${m.gold}</b>` : ''}</div>
```

Confirme que `ui.hud.sigla_xp` não tem outro leitor (`grep -n "sigla_xp" game.js src/*.js src/ui/*.js` vazio) e apague a entrada `"ui.hud.sigla_xp": {…},` de `src/lang/interface.js`.

Em `game.js` (~21359), no `t('ui.mestre.caract_linha', {…})`, remova o parâmetro `xp:m.xp ?? '—', ` (fica `{ia:…, tam:…, ouro:m.gold ?? '—'}`). Em `src/lang/interface.js`, a entrada `"ui.mestre.caract_linha"` passa a ser:

```js
  "ui.mestre.caract_linha": {
    "en": "AI: {ia} · size {tam} · gold {ouro}",
    "pt": "IA: {ia} · tamanho {tam} · ouro {ouro}"
  },
```

- [ ] **Step 3: Conferir**

Run:
```bash
node --check game.js
PYTHONIOENCODING=utf-8 python tools/test_idioma.py | tail -3
PYTHONIOENCODING=utf-8 python tools/test_interface.py | tail -3
node tools/test_idioma_cliente.js | tail -3
PYTHONIOENCODING=utf-8 python tools/dividas.py
```
Expected: sintaxe OK; as três suítes com `0 falharam`; `dividas.py` sem pendências. Se o placar do `test_interface` acusar o literal `" XP"` do ramo do nível máximo, troque-o por `${t('ui.ficha.xp_total', {xp: fmtXp(xpTotal)})}` com a chave `"ui.ficha.xp_total": {"en": "{xp} XP", "pt": "{xp} XP"}`.

- [ ] **Step 4: Commit**

```bash
git add game.js game.css src/lang/interface.js
git commit -m "feat(xp): barra de XP na ficha; XP fixo sai das fichas de monstro

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Recalibrar a campanha Sombras

**Files:**
- Modify: `tools/gerar_campanha_sombras.py`, `tools/test_campanha_sombras.py`
- Regenerated: `dungeons/sombras_*.json`, `tools/.sombras_assinaturas.json`, `tools/editor_dungeons.js`

- [ ] **Step 1: Seção [7] passa a cobrar (falha)**

Em `tools/test_campanha_sombras.py`, substitua a função `secao_curva` inteira (e o cabeçalho `# ─── [7] …` acima dela) por:

```python
# ─── [7] Curva de XP (modelo 3.5) ────────────────────────────────────────────
def secao_curva():
    print("\n[7] Curva de XP — cobra o ritmo 1→2→3→4 (spec XP 3.5, seção 5)")
    linhas = G.curva_campanha(MM)
    for a, ini, xp, fim in linhas:
        print(f"     {a}: entra no {ini}, sai no {fim} ({xp} XP)")
    curva = {a: (ini, fim) for a, ini, _xp, fim in linhas}
    check("cada masmorra começa no nível esperado do grupo",
          all(curva[a][0] == MM[a]["expected_party"]["level"] for a in G.ARQUIVOS))
    check("saídas 2 → 3 → 3 → 4", [curva[a][1] for a in G.ARQUIVOS] == [2, 3, 3, 4])
    check("só as masmorras com meta dão XP de objetivo",
          [MM[a]["objectives"]["primary"]["xp"] > 0 for a in G.ARQUIVOS] == [True, True, False, True])
    check("XP de objetivo em múltiplos de 100",
          all(MM[a]["objectives"]["primary"]["xp"] % 100 == 0 for a in G.ARQUIVOS))
    # Conta independente do gerador, só com as funções do servidor.
    defs = {m["type"]: m for m in S.MONSTER_DEFS}
    xp = 0
    for a in G.ARQUIVOS:
        for mo in MM[a]["monsters"]:
            if a == "sombras_3b_trono.json" and mo["room_id"] == 2:
                continue    # o esconderijo é opcional
            xp += S.xp_por_heroi(S.nivel_por_xp(xp), S.monster_cr(defs[mo["type"]]), 4)
        tot = MM[a]["objectives"]["primary"]["xp"]
        xp += max(1, tot // 4) if tot else 0
    check("conta independente termina no nível 4", S.nivel_por_xp(xp) == 4)
```

Run: `PYTHONIOENCODING=utf-8 python tools/test_campanha_sombras.py`
Expected: `AttributeError: module 'gerar_campanha_sombras' has no attribute 'curva_campanha'`

- [ ] **Step 2: Calibração no gerador**

Em `tools/gerar_campanha_sombras.py`, logo antes de `def preparar():`, insira:

```python
# ─── Curva de XP (spec 2026-09-26, seção 5) ──────────────────────────────────
HEROIS_CAMPANHA = 4
# Nível com que o grupo deve SAIR de cada masmorra. Os Salões não têm meta: o
# Covil é um destino só, medido no fim do Trono.
METAS_NIVEL = {"sombras_1_vau.json": 2, "sombras_2_minas.json": 3,
               "sombras_3b_trono.json": 4}


def _opcional(arquivo, mo):
    """O esconderijo do Trono (sala 2) é o chefe secreto: fora da conta."""
    return arquivo == "sombras_3b_trono.json" and mo["room_id"] == 2


def _xp_monstros(defn, arquivo, xp, herois):
    """XP acumulado de UM herói depois dos monstros obrigatórios da masmorra."""
    defs = {m["type"]: m for m in S.MONSTER_DEFS}
    for mo in defn["monsters"]:
        if not _opcional(arquivo, mo):
            xp += S.xp_por_heroi(S.nivel_por_xp(xp), S.monster_cr(defs[mo["type"]]), herois)
    return xp


def curva_campanha(mm, herois=HEROIS_CAMPANHA):
    """Percurso completo sem o esconderijo, grupo inteiro vivo:
    [(arquivo, nível de entrada, XP de saída, nível de saída)]."""
    xp, linhas = 0, []
    for arquivo in ARQUIVOS:
        defn = mm[arquivo]
        ini = S.nivel_por_xp(xp)
        xp = _xp_monstros(defn, arquivo, xp, herois)
        total = int(defn["objectives"]["primary"].get("xp", 0))
        if total > 0:
            xp += max(1, total // herois)
        linhas.append((arquivo, ini, xp, S.nivel_por_xp(xp)))
    return linhas


def calibrar_xp_objetivos(mm, herois=HEROIS_CAMPANHA):
    """Põe no objetivo principal de cada masmorra com meta o XP TOTAL do grupo que
    falta para sair no nível de METAS_NIVEL (múltiplo de 100, para cima). Muta e
    devolve `mm`. Armadilhas ficam de fora: o que elas rendem é folga."""
    xp = 0
    for arquivo in ARQUIVOS:
        prim = mm[arquivo]["objectives"]["primary"]
        prim["xp"] = 0
        xp = _xp_monstros(mm[arquivo], arquivo, xp, herois)
        meta = METAS_NIVEL.get(arquivo)
        if meta:
            falta = max(0, S.xp_limiar(meta) - xp)
            prim["xp"] = -(-falta * herois // 100) * 100
            if prim["xp"]:
                xp += max(1, prim["xp"] // herois)
    return mm
```

Em `preparar()`, troque `mm = masmorras()` por `mm = calibrar_xp_objetivos(masmorras())`.

Em `relatorio()`, antes de `linhas.append("Artes pedidas pelos slides:")`, insira:

```python
    linhas.append(f"Curva de XP (grupo de {HEROIS_CAMPANHA}, sem o esconderijo):")
    for arquivo, ini, xp, fim in curva_campanha(artefatos["masmorras"]):
        xp_obj = artefatos["masmorras"][arquivo]["objectives"]["primary"]["xp"]
        linhas.append(f"   {arquivo}: entra no {ini}, sai no {fim} ({xp} XP; objetivo {xp_obj})")
```

- [ ] **Step 3: Rodar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_campanha_sombras.py`
Expected: `71 passaram, 0 falharam` (antes 67; a seção [7] foi de 1 para 5 checks).

As seções [3]–[5] agora concedem XP de objetivo ao encerrar a missão, e o mago/clérigo que sobe de nível ganha uma escolha de magia pendente. Se alguma dessas seções quebrar por `pending_spell_pick` bloquear o `end_turn`, esvazie `p["pending_spell_pick"] = []` dos heróis logo depois do encerramento, no próprio teste. Registre o motivo num comentário e **não** mude a regra do servidor.

- [ ] **Step 4: Regerar a campanha**

Run:
```bash
PYTHONIOENCODING=utf-8 python tools/gerar_campanha_sombras.py --simular | grep -A5 "Curva de XP"
PYTHONIOENCODING=utf-8 python tools/gerar_campanha_sombras.py | tail -1
git status --short
```
Expected: a curva mostra saídas 2/3/3/4, depois `OK: 4 masmorras, 3 destinos, conversa do Bartender e anel gravados.` O status lista só `dungeons/sombras_*.json` (os que têm meta: Vau, Minas e Trono), `tools/.sombras_assinaturas.json` e `tools/editor_dungeons.js`. Se aparecerem `world_adventures.json`, `city_scenes.json` ou os de itens, confira com `git diff` que só mudou formatação; se mudou conteúdo, pare e relate.

- [ ] **Step 5: Commit**

```bash
git add tools/gerar_campanha_sombras.py tools/test_campanha_sombras.py dungeons/sombras_1_vau.json dungeons/sombras_2_minas.json dungeons/sombras_3a_saloes.json dungeons/sombras_3b_trono.json tools/.sombras_assinaturas.json tools/editor_dungeons.js
git commit -m "feat(campanha): XP dos objetivos calibrado para o ritmo 1-2-3-4 da tabela 3.5

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Bateria e documentação

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Bateria que toca XP e nível**

Run (script do scratchpad que relata exit code e contagem de ❌):
```bash
python "C:/Users/RICARDO/AppData/Local/Temp/claude/C--Users-RICARDO-Desktop-jogo-tabuleiro/481c0e8d-419c-46f6-ab59-86095bdc3420/scratchpad/suites.py" test_xp_progressao test_campanha_sombras test_modo_mestre test_magias_slots test_objetivos test_savegames test_masmorra_sequenciada test_tutorial test_guilda test_editor_itens test_cenas_conversa test_idioma test_interface test_idioma_cliente test_devorador test_projeteis test_ladino_espec test_clerigo_espec test_mago_espec test_reviver_mortos test_simulador_turno
```
Expected: `0 com problema`. Então descubra quem mais toca XP e nível: `grep -ln '"xp"\|\["level"\]\|_conceder_xp' tools/test_*.py`. Rode os que não estão na lista acima. Uma vermelha que crave um número da curva antiga é corrigida no número, não na regra. Qualquer outra vermelha: pare e relate, conferindo antes a memória `testes-pre-existentes-quebrados.md`.

- [ ] **Step 2: `CLAUDE.md`**

No parágrafo `> **Camada C — ND/XP de armadilha:**`, troque o trecho:

```
> 0.3) e `trap_xp(cr)=round(cr×TRAP_XP_POR_CR)` (=20). Só armadilhas **autoradas**
```
por:
```
> 0.3); o XP sai da tabela 3.5 (`xp_por_heroi` com o `cr`). Só armadilhas **autoradas**
```

e, no mesmo parágrafo, `(com\n> `_check_level_up`)` por `(pela porta\n> `_conceder_xp`)`. Leia o parágrafo e preserve as quebras de linha.

No parágrafo da campanha Sombras, troque a frase:

```
A curva de XP
> ainda dispara (a suíte relata o nível atingido; o conserto é o próximo subprojeto).
```
por:
```
O XP dos
> objetivos é calibrado pelo gerador para o ritmo 1→2→3→4 (ver "Progressão de XP 3.5").
```

Depois do parágrafo da campanha, acrescente:

```markdown
> **Progressão de XP 3.5 (2026-09-26):** o XP do jogador é **acumulado** (nunca subtraído)
> e o nível é consequência dele. Funções puras module-level em `server.py`: `xp_premio(nível,
> ND)` = `300 × nível × 2^((ND−nível)/2)` (ND < 1 vale a fração do ND 1; 8 NDs abaixo não
> rende; trava em nível+7), `xp_por_heroi` (÷ vivos, mín. 1), `xp_limiar(n) = 500·n·(n−1)`
> (1000, 3000, 6000 … 190000), `nivel_por_xp`, teto `XP_NIVEL_MAX = 20`. Cada herói consulta a
> tabela com o **próprio** nível, então quem está atrás alcança os outros sozinho. **Porta
> única** `_conceder_xp(p, qtd)`: sobe quantos níveis couberem via `_subir_um_nivel` (o antigo
> `_check_level_up`, que subtraía `nível×30` e subia 1 por vez). Monstro (`monster_cr`, inclusive
> os 6 legados — o campo `xp` fixo da ficha não vale mais), armadilha (`trap_cr`), objetivo (total
> autoral ÷ vivos) e entrada "experiente" passam por ela. **Saves:** `xp_modelo: 2` em
> `_DURABLE_FIELDS`; ficha sem a marca é convertida em `restore_character` por `xp_migrado`,
> mantendo nível e fração de progresso (ficha inflada pela curva antiga NÃO é rebaixada).
> Payload: `xp_nivel`/`xp_proximo` por jogador → barra na ficha da cidade. Teste:
> `tools/test_xp_progressao.py`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-09-26-progressao-xp-dnd35*`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: progressao de XP no modelo 3.5

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
