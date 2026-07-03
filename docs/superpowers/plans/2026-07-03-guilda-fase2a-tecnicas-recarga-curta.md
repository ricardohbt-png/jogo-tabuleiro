# Técnicas de Recarga Curta (Guilda Fase 2a) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 4 Técnicas da Guilda genéricas de Recarga Curta (3 rodadas) — Mira Perfeita, Espírito Indomável, Grito de Guerra, Pressa — reusando a infra existente de técnicas, e agrupar a aba de Técnicas da Guilda por faixa de recarga no cliente.

**Architecture:** Cada técnica é uma entrada `GUILD_CATALOG` (`categoria:"tecnica"`, `classe:None`) com `efeito:{tipo,...}`. `handle_usar_tecnica` (já centraliza turno/recarga/custo) ganha um ramo por `efeito.tipo`. Efeitos de consumo diferido (Mira Perfeita) leem uma flag no site relevante (`handle_attack`); buffs de movimento tocam o reset de turno; a imunidade a Silêncio é lida em `_em_silencio`.

**Tech Stack:** Python 3 (`server.py`), vanilla JS (`game.js`, `src/gameState.js`), harness de teste próprio (`tools/test_tecnicas_espec.py`).

**Spec:** `docs/superpowers/specs/2026-07-03-guilda-fase2a-tecnicas-recarga-curta-design.md`

---

## Arquivos tocados

- **Modify** `server.py`:
  - `GUILD_CATALOG` (~280, após `brutalidade`) — 4 técnicas.
  - `make_player` (~3318) — campos de estado (`tecnica_mira_perfeita`, `imune_silencio_ate`, `mov_bonus_ate`).
  - `handle_usar_tecnica` (~4202) — ramos novos por `efeito.tipo`.
  - `handle_attack` — consumo da Mira Perfeita (vantagem + `+2` dano no site ~5514).
  - `_em_silencio` (~9482) — respeitar imunidade temporária.
  - Reset de início de turno (~10842) — aplicar buff de movimento do Grito.
  - Reset de fim de turno (~10794) — limpar flag da Mira Perfeita.
- **Modify** `game.js` — agrupar Técnicas por `recarga_rodadas` na Guilda.
- **Create** `tools/test_tecnicas_espec.py`.
- **Modify** `CLAUDE.md` — parágrafo da Fase 2a.

> **Fatos verificados:** `handle_usar_tecnica` valida turno/equipada/recarga/fome-sede e NÃO consome ação principal (buff-and-act). `_tecnica_bonus_dano(p)` (4014) já soma no dano (sites 5514/5532). `_em_silencio(obj)` (9482) é posicional. Reset do próximo jogador em 10842 (`next_p["moves_left"] = next_p["spd"]`). Fim de turno limpa flags em ~10794.

---

### Task 1: Catálogo (4 técnicas) + arquivo de teste

**Files:** Modify `server.py` (`GUILD_CATALOG`); Create `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Criar `tools/test_tecnicas_espec.py`**

```python
"""Técnicas da Guilda — Recarga Curta (Fase 2a). Roda: python tools/test_tecnicas_espec.py"""
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
    r.phase = phase; r._errs = errs; r.round_num = 1
    return r

def hero(cls="warrior", tid=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    if tid:
        p["guild_owned"]["tecnicas"] = [tid]
        p["guild_equip"]["tecnica"] = tid
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo — Recarga Curta")
    for tid in ["tecnica_mira_perfeita","tecnica_espirito_indomavel","tecnica_grito_guerra","tecnica_pressa"]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 3", it and it["recarga_rodadas"] == 3)
        check(f"{tid} preco 100", it and it["preco"] == 100)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("pressa custa 4/4", S.guild_item("tecnica_pressa")["custo_fome"] == 4
          and S.guild_item("tecnica_pressa")["custo_sede"] == 4)
    check("mira custa 2/2", S.guild_item("tecnica_mira_perfeita")["custo_fome"] == 2)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tecnicas_espec.py` → FAIL (técnicas não existem no catálogo).

- [ ] **Step 3: Adicionar as 4 técnicas ao `GUILD_CATALOG`**

Em `server.py`, imediatamente após o bloco `"brutalidade": { ... },` (~287), inserir:

```python
    # ── Técnicas de Recarga Curta (Fase 2a) ─────────────────────────────────
    "tecnica_mira_perfeita": {
        "id": "tecnica_mira_perfeita", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 100, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 3,
        "nome": "Mira Perfeita", "icon": "🎯",
        "desc": "Próximo ataque à distância recebe vantagem; se acertar, +2 de dano.",
        "efeito": {"tipo": "mira_perfeita", "bonus_dano": 2},
    },
    "tecnica_espirito_indomavel": {
        "id": "tecnica_espirito_indomavel", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 100, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 3,
        "nome": "Espírito Indomável", "icon": "🧘", "acao_livre": True,
        "desc": "Ação livre. Remove Medo, Atordoamento e Lentidão; 1 rodada imune a Silêncio.",
        "efeito": {"tipo": "remove_status"},
    },
    "tecnica_grito_guerra": {
        "id": "tecnica_grito_guerra", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 100, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 3,
        "nome": "Grito de Guerra", "icon": "📣",
        "desc": "Todos os aliados recebem +2 de movimento por 1 rodada.",
        "efeito": {"tipo": "buff_aliados_mov", "bonus_mov": 2},
    },
    "tecnica_pressa": {
        "id": "tecnica_pressa", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 100, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 3,
        "nome": "Pressa", "icon": "💨",
        "desc": "O seu movimento é dobrado nesta rodada.",
        "efeito": {"tipo": "mov_self_dobrar"},
    },
```

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_tecnicas_espec.py` → PASS seção [1].

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): catalogo das Tecnicas de Recarga Curta (Fase 2a)"
```

---

### Task 2: Pressa (`mov_self_dobrar`) + campos de estado

**Files:** Modify `server.py` (`make_player` ~3318; `handle_usar_tecnica` ~4202); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Adicionar seção de teste [2]** (antes do print final em `main()`):

```python
    # [2] Pressa
    print("\n[2] Pressa")
    r = setup()
    p = hero("warrior", "tecnica_pressa"); r.players["h"] = p
    r.current_pid = lambda: "h"
    spd = p["spd"]; p["moves_left"] = spd; f0, s0 = p["fome"], p["sede"]
    await r.handle_usar_tecnica("h", "tecnica_pressa")
    check("pressa: +spd de movimento", p["moves_left"] == spd + spd)
    check("pressa: custo 4/4", p["fome"] == f0 - 4 and p["sede"] == s0 - 4)
    check("pressa: recarga setada", r.tecnica_restante(p, "tecnica_pressa") > 0)
```

- [ ] **Step 2: Rodar e ver falhar** — o efeito `mov_self_dobrar` ainda não é tratado; `moves_left` não muda.

Run: `python tools/test_tecnicas_espec.py` (Expected: [2] falha)

- [ ] **Step 3: Adicionar campos de estado em `make_player`**

Em `server.py`, junto de `"tecnica_buff_dano_arma": 0,` (~3318), acrescentar:
```python
        "tecnica_mira_perfeita": False,     # Mira Perfeita: próximo ataque à distância
        "imune_silencio_ate": 0,            # Espírito Indomável: imunidade a Silêncio até esta rodada
        "mov_bonus_ate": 0,                 # Grito de Guerra: +2 movimento no reset até esta rodada
```

- [ ] **Step 4: Tratar `mov_self_dobrar` em `handle_usar_tecnica`**

Em `server.py`, no dispatch (~4202-4205), estender:
```python
        ef = item.get("efeito", {})
        if ef.get("tipo") == "buff_turno":
            p["tecnica_buff_dano_arma"] = p.get("tecnica_buff_dano_arma", 0) + ef.get("bonus_dano_arma", 0)
        elif ef.get("tipo") == "mov_self_dobrar":
            p["moves_left"] = p.get("moves_left", 0) + p.get("spd", 0)
        # (demais tipos nas tasks seguintes)
```

- [ ] **Step 5: Rodar e ver passar** — `python tools/test_tecnicas_espec.py` → [1][2] PASS.

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Pressa (dobra movimento) + campos de estado"
```

---

### Task 3: Grito de Guerra (`buff_aliados_mov`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; reset de turno ~10842); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Seção de teste [3]**

```python
    # [3] Grito de Guerra
    print("\n[3] Grito de Guerra")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_grito_guerra"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1,1]
    ally["moves_left"] = ally["spd"]; r.players["a"] = ally
    p["moves_left"] = p["spd"]
    await r.handle_usar_tecnica("h", "tecnica_grito_guerra")
    check("grito: usuário +2 movimento", p["moves_left"] == p["spd"] + 2)
    check("grito: aliado +2 movimento", ally["moves_left"] == ally["spd"] + 2)
    check("grito: buff transitório setado", p["mov_bonus_ate"] == r.round_num + 1)
```

- [ ] **Step 2: Rodar e ver falhar** — efeito `buff_aliados_mov` não tratado.

- [ ] **Step 3: Tratar `buff_aliados_mov` no dispatch**

Em `handle_usar_tecnica`, acrescentar ramo:
```python
        elif ef.get("tipo") == "buff_aliados_mov":
            b = ef.get("bonus_mov", 2)
            for q in self.players.values():
                if not q.get("alive"): continue
                q["moves_left"] = q.get("moves_left", 0) + b
                q["mov_bonus_ate"] = self.round_num + 1
                q["mov_bonus_val"] = b
```

- [ ] **Step 4: Aplicar o buff no reset de início de turno**

Em `server.py` (~10842), trocar:
```python
            next_p = self.players[self.current_pid()]
            next_p["moves_left"] = next_p["spd"]
```
por:
```python
            next_p = self.players[self.current_pid()]
            _mov_extra = next_p.get("mov_bonus_val", 0) if next_p.get("mov_bonus_ate", 0) >= self.round_num else 0
            next_p["moves_left"] = next_p["spd"] + _mov_extra
```
(O `mov_bonus_val` default 0 no `make_player` não é necessário — `.get(...,0)` cobre.)

- [ ] **Step 5: Rodar e ver passar** — [1]-[3] PASS.

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Grito de Guerra (+2 movimento aliados 1 rodada)"
```

---

### Task 4: Espírito Indomável (`remove_status` + imunidade a Silêncio)

**Files:** Modify `server.py` (`handle_usar_tecnica`; `_em_silencio` ~9482); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Seção de teste [4]**

```python
    # [4] Espírito Indomável
    print("\n[4] Espírito Indomável")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_espirito_indomavel"); r.players["h"] = p
    p["com_medo"] = True; p["medo_rodadas"] = 3; p["perde_turno"] = True; p["lentidao"] = True
    await r.handle_usar_tecnica("h", "tecnica_espirito_indomavel")
    check("indomável: remove medo", not p.get("com_medo"))
    check("indomável: remove atordoamento", not p.get("perde_turno"))
    check("indomável: remove lentidão", not p.get("lentidao"))
    check("indomável: imunidade a silêncio setada", p["imune_silencio_ate"] == r.round_num + 1)
    # _em_silencio respeita a imunidade mesmo dentro de zona
    r._zonas_ativas = lambda tipo: [{"cx":0,"cy":0,"raio":3}] if tipo == "silencio" else []
    r._em_zona_quadrada = lambda x,y,z: True
    check("indomável: imune a silêncio ativo", r._em_silencio(p) is False)
```

- [ ] **Step 2: Rodar e ver falhar** — efeito `remove_status` não tratado.

- [ ] **Step 3: Tratar `remove_status` no dispatch**

```python
        elif ef.get("tipo") == "remove_status":
            for k in ("com_medo", "medo_rodadas", "perde_turno", "lentidao", "lentidao_rodadas"):
                p.pop(k, None)
            p["imune_silencio_ate"] = self.round_num + 1
```

- [ ] **Step 4: Respeitar a imunidade em `_em_silencio`**

Em `server.py` (~9482), trocar:
```python
    def _em_silencio(self, obj):
        x, y = obj.get("pos", [0, 0])
        return any(self._em_zona_quadrada(x, y, z) for z in self._zonas_ativas("silencio"))
```
por:
```python
    def _em_silencio(self, obj):
        if obj.get("imune_silencio_ate", 0) >= self.round_num:
            return False
        x, y = obj.get("pos", [0, 0])
        return any(self._em_zona_quadrada(x, y, z) for z in self._zonas_ativas("silencio"))
```

- [ ] **Step 5: Rodar e ver passar** — [1]-[4] PASS. Também `python tools/test_guilda.py` (verde — infra intacta).

- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Espirito Indomavel (remove status + imune a silencio)"
```

---

### Task 5: Mira Perfeita (`mira_perfeita`) + consumo em `handle_attack`

**Files:** Modify `server.py` (`handle_usar_tecnica`; `handle_attack` vantagem + dano ~5514; reset fim de turno ~10794); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Seção de teste [5]** (usa helper de ataque real com um monstro)

```python
    # [5] Mira Perfeita — flag armada e consumo
    print("\n[5] Mira Perfeita")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("ranger" if "ranger" in S.CLASSES else "warrior", "tecnica_mira_perfeita"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_mira_perfeita")
    check("mira: flag armada", p.get("tecnica_mira_perfeita") is True)
    check("mira: recarga setada", r.tecnica_restante(p, "tecnica_mira_perfeita") > 0)
    # consumo: ao marcar como consumida em ataque à distância
    p2 = hero("warrior"); p2["tecnica_mira_perfeita"] = True
    check("helper _mira_perfeita_ativa ranged=True", r._mira_perfeita_ativa(p2, True) == 2)
    check("helper _mira_perfeita_ativa melee=False", r._mira_perfeita_ativa(p2, False) == 0)
```

- [ ] **Step 2: Rodar e ver falhar** — `mira_perfeita` não tratado; `_mira_perfeita_ativa` inexistente.

- [ ] **Step 3: Tratar `mira_perfeita` + helper**

No dispatch de `handle_usar_tecnica`:
```python
        elif ef.get("tipo") == "mira_perfeita":
            p["tecnica_mira_perfeita"] = True
```
E um helper novo perto de `_tecnica_bonus_dano` (~4014):
```python
    def _mira_perfeita_ativa(self, p, is_ranged):
        """+2 de dano (e vantagem) do próximo ataque à distância sob Mira Perfeita."""
        return 2 if (is_ranged and p.get("tecnica_mira_perfeita")) else 0
```

- [ ] **Step 4: Consumir em `handle_attack` — vantagem + dano + limpar flag**

(a) Logo após a definição de `w_range` no ramo de alvo-monstro, capturar o estado da Mira (antes do range-check consumir nada): localize a linha `vantagem    = (bool(p.get("invisivel_magico"))` e troque para incluir a Mira:
```python
            _mira_ranged = bool(w_range is not None and p.get("tecnica_mira_perfeita"))
            vantagem    = (bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela"))
                           or esc == "vantagem"
                           or self._provocacao_atk_vantagem(p, target)
                           or _mira_ranged)
```
(b) No cálculo de dano de arma (~5514-5517), adicionar o termo `+ self._mira_perfeita_ativa(p, w_range is not None)`:
```python
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") + self._tecnica_bonus_dano(p)
                              + self._mira_perfeita_ativa(p, w_range is not None)
                              + p.get("skill_bonus_dano", 0)
                              - self._corrosao_arma_pen(p))
```
(c) Limpar a flag após o ataque à distância (uma vez usada, em acerto OU erro). Logo após o cálculo de `hit, roll, ...` do ataque do jogador, adicionar:
```python
            if _mira_ranged:
                p["tecnica_mira_perfeita"] = False
```
(Coloque essa limpeza após o `self._rolar_ataque(...)` do jogador — antes disso `_mira_ranged` já está definido; localize a chamada `_rolar_ataque(eff_atk, ...)`.)

- [ ] **Step 5: Limpar a flag no fim do turno (se não usada)**

Em `server.py` (~10794), junto de `p["tecnica_buff_dano_arma"] = 0`, adicionar:
```python
        p["tecnica_mira_perfeita"] = False   # Mira Perfeita não usada expira no fim do turno
```

- [ ] **Step 6: Rodar e ver passar** — `python tools/test_tecnicas_espec.py` → [1]-[5] PASS.
Regressão: `python tools/test_guilda.py`, `python tools/test_ladino_espec.py`, `python tools/test_bardo_espec.py` (combate/vantagem intactos).

- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Mira Perfeita (vantagem +2 dano no proximo ataque a distancia)"
```

---

### Task 6: Cliente — agrupar Técnicas por faixa de recarga

**Files:** Modify `game.js` (render da aba de Técnicas da Guilda)

- [ ] **Step 1: Localizar o render das técnicas na Guilda**

Procure em `game.js` por onde a Guilda lista os itens `categoria:"tecnica"` (função `openGuild`/`_renderGuild`/o loop que monta os cards de técnica). Use Grep por `categoria` e `tecnica` no contexto da Guilda.

- [ ] **Step 2: Agrupar por `recarga_rodadas`**

No ponto onde as técnicas são listadas, antes de renderizar os cards, agrupe por `recarga_rodadas` e emita um cabeçalho por faixa (ordem ascendente 3→5→8→10). Rótulos: `3` → "Recarga Curta (3 rodadas)", `5` → "Recarga Média (5)", `8` → "Recarga Longa (8)", `10` → "Recarga Muito Longa (10)". Exemplo de agrupamento:
```javascript
const _faixaLabel = { 3:'Recarga Curta (3 rodadas)', 5:'Recarga Média (5 rodadas)', 8:'Recarga Longa (8 rodadas)', 10:'Recarga Muito Longa (10 rodadas)' };
const _tecnicas = itens.filter(i => i.categoria === 'tecnica');
const _porFaixa = {};
_tecnicas.forEach(t => { (_porFaixa[t.recarga_rodadas] ||= []).push(t); });
Object.keys(_porFaixa).sort((a,b)=>a-b).forEach(rec => {
  // emitir cabeçalho _faixaLabel[rec] || (`Recarga ${rec} rodadas`) e depois os cards de _porFaixa[rec]
});
```
Mantenha o card individual de técnica exatamente como já é renderizado — só encapsule na agrupação por faixa.

- [ ] **Step 3: Sanidade** — `node --check game.js` (Expected: sem erro).

- [ ] **Step 4: Commit**
```bash
git add game.js
git commit -m "feat(guilda): agrupar Tecnicas da Guilda por faixa de recarga"
```

---

### Task 7: Verificação E2E (smoke) + docs

**Files:** Modify `CLAUDE.md`; Test manual via preview + suíte

- [ ] **Step 1: Suíte verde** — `python tools/test_tecnicas_espec.py` → `PASS=N FAIL=0`.

- [ ] **Step 2: Smoke E2E** — Bump temporário `CLASSES["warrior"]["start_gold"]` para 2000; `preview_start` "game"; abrir a Guilda e confirmar que a aba de Técnicas aparece **agrupada por faixa de recarga** e que comprar `tecnica_pressa` debita ouro e persiste. Validar os getters/estado via `preview_eval` se o handshake WS não subir (registrar honestamente, sem superestimar). Reverter o `start_gold` e `rm -rf saves/`.

- [ ] **Step 3: Documentar na CLAUDE.md** — após o parágrafo do Mago (Fase 1f), adicionar:

```markdown
> **Técnicas de Recarga Curta (Fase 2a):** 1º lote das Técnicas da Guilda (4º slot,
> genéricas, `categoria:"tecnica"`, `classe:None`, recarga 3, preço 100). 4 técnicas:
> **Mira Perfeita** (`mira_perfeita` — próximo ataque à distância com vantagem +2 dano;
> flag `tecnica_mira_perfeita` consumida em `handle_attack`, expira no fim do turno),
> **Espírito Indomável** (`remove_status` — limpa medo/atordoamento/lentidão + 1 rodada
> `imune_silencio_ate`, lido em `_em_silencio`; ação livre), **Grito de Guerra**
> (`buff_aliados_mov` — +2 movimento a todos os aliados; imediato + `mov_bonus_ate`
> aplicado no reset de turno), **Pressa** (`mov_self_dobrar` — `moves_left += spd`;
> custo 4/4). Efeitos despachados em `handle_usar_tecnica` por `efeito.tipo`. Cliente:
> aba de Técnicas da Guilda agrupada por faixa de recarga (3/5/8/10). Teste:
> `tools/test_tecnicas_espec.py`. Lotes seguintes: 2b (5r), 2c reações, 2d passivas; Fase 3 exclusivas.
```

- [ ] **Step 4: Commit final**
```bash
git add CLAUDE.md server.py
git commit -m "docs(guilda): documentar Tecnicas de Recarga Curta (Fase 2a)"
```

---

## Auto-revisão (checklist do autor do plano)

- **Cobertura do spec:** 4 técnicas → T1 (catálogo) + T2 (Pressa) + T3 (Grito) + T4 (Indomável) + T5 (Mira); agrupamento por recarga → T6; E2E+docs → T7. ✔
- **Sem placeholders:** todo passo traz o código real; a exceção é T6 (localizar o render da Guilda) por o anchor exato do cliente não ter sido lido — mitigado com guia por conteúdo + exemplo de código. ✔
- **Consistência de nomes:** `efeito.tipo` ∈ {`mira_perfeita`,`remove_status`,`buff_aliados_mov`,`mov_self_dobrar`}; campos `tecnica_mira_perfeita`/`imune_silencio_ate`/`mov_bonus_ate`/`mov_bonus_val`; helper `_mira_perfeita_ativa` — idênticos entre tasks. ✔
- **Risco (T5/T6):** os anchors de `handle_attack` (vantagem/dano) e do render do cliente exigem localização por conteúdo; ambos verificados por regressão (combate) e `node --check`. ✔
