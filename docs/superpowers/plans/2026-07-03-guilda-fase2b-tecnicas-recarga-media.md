# Técnicas de Recarga Média (Guilda Fase 2b) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 5 Técnicas da Guilda genéricas de Recarga Média (5 rodadas) — Investida Heroica, Defesa Impecável, Pressão Constante, Tática Defensiva, Passo Fantasma — reusando o dispatch por `efeito.tipo` e o modal de alvo do cliente.

**Architecture:** Cada técnica = entrada `GUILD_CATALOG` (`categoria:"tecnica"`, `classe:None`, recarga 5, preço 180) com `efeito:{tipo,...}`. `handle_usar_tecnica` (já central) ganha um ramo por `efeito.tipo`; as técnicas com alvo usam o `target_id` que ele já aceita. Hooks de consumo em `handle_attack` (Investida, Pressão), nos sites de ataque de monstro (Defesa Impecável), em `_processar_dano_protetor` (Tática) e `handle_move` (Passo Fantasma).

**Tech Stack:** Python 3 (`server.py`), vanilla JS (`game.js`), harness próprio (`tools/test_tecnicas_espec.py`, já existe do 2a).

**Spec:** `docs/superpowers/specs/2026-07-03-guilda-fase2b-tecnicas-recarga-media-design.md`

---

## Arquivos tocados

- **Modify** `server.py`:
  - `GUILD_CATALOG` (após as técnicas do 2a) — 5 técnicas.
  - `make_player` — campos de estado (`investida_armada`, `investida_origem`, `defesa_impecavel_ate`, `tatica_alvo`, `tatica_ate`, `passo_fantasma_ate`).
  - `handle_usar_tecnica` — 5 ramos novos (2 exigem `target_id`).
  - `handle_attack` — Investida (vantagem+dano no melee carregado) + Pressão (−2 CA no `eff_target_ac`).
  - 2 sites de ataque de monstro (desvantagem) — Defesa Impecável.
  - `_verificar_ataque_furtivo` — imunidade a furtivo (Defesa Impecável).
  - `_processar_dano_protetor` — protetor genérico (Tática Defensiva).
  - `handle_move` — bypass de objetos (Passo Fantasma).
  - reset de fim de turno — limpar `investida_armada`.
  - Helpers novos: `_pressao_ca_pen`, `_defesa_impecavel_ativa`, `_passo_fantasma_ativo`, `_investida_bonus`.
- **Modify** `game.js` — seleção de alvo (modal) p/ Pressão Constante e Tática Defensiva.
- **Modify** `tools/test_tecnicas_espec.py` — novas seções.
- **Modify** `CLAUDE.md` — parágrafo do 2b.

> **Fatos verificados (anchors por conteúdo — números aproximados):**
> - `eff_target_ac = (target["ac"] + self._mod_magia(target, "ca") + self._camuflagem_bonus(target) ...` (~5504).
> - Sites de desvantagem de monstro: `prov = bool(m.get("provocado_turno_efeito"))` / `desvantagem = prov or esc == "desvantagem"` — DOIS lugares (~11525-11526 e ~13257-13258), ambos com `target`/`is_player` em escopo.
> - `_verificar_ataque_furtivo(self, luccas, alvo)` (~5268). **NOTA:** só rogue→monstro; nenhum monstro dá furtivo a jogador → a imunidade é **inerte hoje** (implementada defensivamente).
> - `handle_move` blocks: WALL (~5061), porta fechada (~5064), `_decor_block_tiles` (~5068), `_mat_solid_tiles` (~5071), monstro (~5076), jogador (~5082), animado (~5088).
> - `_processar_dano_protetor(alvo_id, dano)` (~7455) — paladino-only; `_defensor_split(richard, dano)` base = 50/50.
> - `handle_usar_tecnica(pid, tecnica_id, target_id=None)` — já aceita alvo; valida turno/recarga/custo; dispatch por `efeito.tipo`.
> - Padrão de +movimento por rodadas: `mov_bonus_ate`/`mov_bonus_val` somados em `_moves_base` via `_grito_mov_bonus`.
> - Modal de alvo do cliente: `openTargetModal(titulo, alvos, 'monster'|'player', id => send({type:'usar_tecnica', tecnica_id, target_id:id}))` (usado pela Provocação com `'monster'`).

---

### Task 1: Catálogo (5 técnicas)

**Files:** Modify `server.py` (`GUILD_CATALOG`); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Add test section [6] (catálogo 2b)** — inserir antes do print final em `main()`:

```python
    # [6] Catálogo — Recarga Média (2b)
    print("\n[6] Catálogo — Recarga Média")
    for tid in ["tecnica_investida","tecnica_defesa_impecavel","tecnica_pressao_constante",
                "tecnica_tatica_defensiva","tecnica_passo_fantasma"]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 5", it and it["recarga_rodadas"] == 5)
        check(f"{tid} preco 180", it and it["preco"] == 180)
        check(f"{tid} custo 4/4", it and it["custo_fome"] == 4 and it["custo_sede"] == 4)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("pressao exige alvo monstro adjacente",
          S.guild_item("tecnica_pressao_constante").get("alvo") == "monstro_adjacente")
    check("tatica exige alvo aliado",
          S.guild_item("tecnica_tatica_defensiva").get("alvo") == "aliado_raio4")
```

- [ ] **Step 2: Rodar e ver falhar** — `python tools/test_tecnicas_espec.py` → FAIL.

- [ ] **Step 3: Adicionar as 5 técnicas ao `GUILD_CATALOG`**

Localize a última técnica do 2a (`"tecnica_pressa": {...},`) via Grep por `"tecnica_pressa"` e insira IMEDIATAMENTE APÓS o seu `},`:

```python
    # ── Técnicas de Recarga Média (Fase 2b) ─────────────────────────────────
    "tecnica_investida": {
        "id": "tecnica_investida", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Investida Heroica", "icon": "⚡",
        "desc": "Dobra o movimento; se andar ≥2 casas em linha reta, o próximo ataque corpo a corpo tem vantagem +2 dano.",
        "efeito": {"tipo": "investida", "bonus_dano": 2},
    },
    "tecnica_defesa_impecavel": {
        "id": "tecnica_defesa_impecavel", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Defesa Impecável", "icon": "🛡️",
        "desc": "Até o próximo turno, ataques contra você têm desvantagem e você fica imune a Ataque Furtivo.",
        "efeito": {"tipo": "defesa_impecavel"},
    },
    "tecnica_pressao_constante": {
        "id": "tecnica_pressao_constante", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Pressão Constante", "icon": "😖", "alvo": "monstro_adjacente",
        "desc": "Um inimigo adjacente sofre -2 de CA por 2 rodadas.",
        "efeito": {"tipo": "debuff_ca_alvo", "ca": 2, "rodadas": 2},
    },
    "tecnica_tatica_defensiva": {
        "id": "tecnica_tatica_defensiva", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Tática Defensiva", "icon": "🤝", "alvo": "aliado_raio4",
        "desc": "Escolha um aliado em até 4 casas; por 1d4 rodadas, metade do dano dele é transferida a você.",
        "efeito": {"tipo": "tatica_defensiva", "raio": 4},
    },
    "tecnica_passo_fantasma": {
        "id": "tecnica_passo_fantasma", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Passo Fantasma", "icon": "👻",
        "desc": "Por 1d4 rodadas: +2 de movimento e você atravessa casas ocupadas por objetos (não paredes nem criaturas).",
        "efeito": {"tipo": "passo_fantasma", "bonus_mov": 2},
    },
```

- [ ] **Step 4: Rodar e ver passar** — seção [6] PASS.
- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): catalogo das Tecnicas de Recarga Media (Fase 2b)"
```

---

### Task 2: Campos de estado + Pressão Constante (`debuff_ca_alvo`)

**Files:** Modify `server.py` (`make_player`; `handle_usar_tecnica`; `eff_target_ac` ~5504); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [7]**

```python
    # [7] Pressão Constante
    print("\n[7] Pressão Constante")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    r._no_raio = lambda a,b,raio,*x,**k: max(abs(a["pos"][0]-b["pos"][0]), abs(a["pos"][1]-b["pos"][1])) <= raio
    p = hero("warrior", "tecnica_pressao_constante"); p["pos"] = [0,0]; r.players["h"] = p
    mob = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":14,"ca":14}
    r.monsters = {"m1": mob}
    await r.handle_usar_tecnica("h", "tecnica_pressao_constante", "m1")
    check("pressao: -2 CA marcado no alvo", mob.get("pressao_ca_val") == 2 and mob["pressao_ca_ate"] == r.round_num + 2)
    check("pressao: helper _pressao_ca_pen = 2 na janela", r._pressao_ca_pen(mob) == 2)
    # alvo não-adjacente é recusado
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 1
    r2._no_raio = r._no_raio
    p2 = hero("warrior", "tecnica_pressao_constante"); p2["pos"] = [0,0]; r2.players["h"] = p2
    far = {"id":"m2","name":"Orc","nome":"Orc","pos":[5,5],"hp":20,"max_hp":20,"ac":14,"ca":14}
    r2.monsters = {"m2": far}
    await r2.handle_usar_tecnica("h", "tecnica_pressao_constante", "m2")
    check("pressao: recusa alvo não-adjacente", far.get("pressao_ca_val") is None and any("adjacente" in e.lower() for e in r2._errs))
    # expira após 2 rodadas
    r.round_num += 3
    check("pressao: expira", r._pressao_ca_pen(mob) == 0)
```

- [ ] **Step 2: Rodar e ver falhar** — `debuff_ca_alvo`/`_pressao_ca_pen` inexistentes.

- [ ] **Step 3: Campos de estado em `make_player`**

Junto de `"tecnica_mira_perfeita": False,` (campos de técnica), adicionar:
```python
        "investida_armada": False,          # Investida Heroica: charge armada
        "investida_origem": None,           # pos ao ativar a Investida
        "defesa_impecavel_ate": 0,          # Defesa Impecável até esta rodada
        "tatica_alvo": None,                # Tática Defensiva: aliado protegido
        "tatica_ate": 0,                    # Tática Defensiva até esta rodada
        "passo_fantasma_ate": 0,            # Passo Fantasma até esta rodada
```

- [ ] **Step 4: Helper `_pressao_ca_pen` + ramo no dispatch**

Perto de `_tecnica_bonus_dano` (helpers de técnica), adicionar:
```python
    def _pressao_ca_pen(self, m):
        """-CA da Pressão Constante enquanto ativa no monstro."""
        return m.get("pressao_ca_val", 0) if m.get("pressao_ca_ate", 0) >= self.round_num else 0
```
No dispatch de `handle_usar_tecnica` (após os ramos do 2a), adicionar:
```python
        elif ef.get("tipo") == "debuff_ca_alvo":
            alvo = self.monsters.get(target_id) if target_id else None
            if not alvo or alvo.get("hp", 0) <= 0:
                await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
            if max(abs(alvo["pos"][0]-p["pos"][0]), abs(alvo["pos"][1]-p["pos"][1])) > 1:
                await self.send_to(pid, {"type": "error", "msg": "O inimigo precisa estar adjacente."}); return
            alvo["pressao_ca_val"] = ef.get("ca", 2)
            alvo["pressao_ca_ate"] = self.round_num + ef.get("rodadas", 2)
```
> **VERIFICADO:** em `handle_usar_tecnica`, o custo é apenas CHECADO antes do dispatch de `efeito`; o DÉBITO de 🍖/💧 e o set de recarga acontecem no rabo compartilhado DEPOIS do bloco `if/elif`. Portanto um `return` de erro dentro do ramo (alvo inválido) NÃO gasta custo nem entra em recarga — basta retornar no ramo. Não reestruture a ordem.

- [ ] **Step 5: Aplicar −CA no `eff_target_ac`**

Em `handle_attack`, no cálculo de `eff_target_ac` (~5504), adicionar o termo `- self._pressao_ca_pen(target)`:
```python
            eff_target_ac = (target["ac"] + self._mod_magia(target, "ca")
                             + self._camuflagem_bonus(target)
                             + self._cacador_trevas_ca_bonus(target)
                             - self._pressao_ca_pen(target)
                             - self._furia_cega_ca_pen(target)
                             - self._lento_previsivel_ca_pen(target))
```
(Localize o bloco exato por conteúdo — mantenha os demais termos idênticos, só insira a nova linha.)

- [ ] **Step 6: Rodar e ver passar** — [6][7] PASS. Compile OK. `python tools/test_guilda.py` verde.
- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Pressao Constante (-2 CA em inimigo adjacente) + campos de estado 2b"
```

---

### Task 3: Defesa Impecável (`defesa_impecavel`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; 2 sites de desvantagem de monstro; `_verificar_ataque_furtivo`); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [8]**

```python
    # [8] Defesa Impecável
    print("\n[8] Defesa Impecável")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_defesa_impecavel"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_defesa_impecavel")
    check("defesa: janela setada", p["defesa_impecavel_ate"] == r.round_num + 1)
    check("defesa: _defesa_impecavel_ativa True", r._defesa_impecavel_ativa(p) is True)
    # imune a furtivo (rogue tentando furtivo contra p)
    luccas = hero("rogue"); luccas["invisivel_sombras"] = True
    check("defesa: imune a furtivo", r._verificar_ataque_furtivo(luccas, p) is False)
    # expira
    r.round_num += 2
    check("defesa: expira", r._defesa_impecavel_ativa(p) is False)
```

- [ ] **Step 2: Rodar e ver falhar** — `defesa_impecavel`/`_defesa_impecavel_ativa` inexistentes.

- [ ] **Step 3: Helper + ramo no dispatch**

Helper perto dos de técnica:
```python
    def _defesa_impecavel_ativa(self, p):
        return p.get("defesa_impecavel_ate", 0) >= self.round_num
```
Ramo no dispatch:
```python
        elif ef.get("tipo") == "defesa_impecavel":
            p["defesa_impecavel_ate"] = self.round_num + 1
```

- [ ] **Step 4: Desvantagem nos 2 sites de ataque de monstro**

Em AMBOS os sites (localize por conteúdo `prov = bool(m.get("provocado_turno_efeito"))` seguido de `desvantagem = prov or esc == "desvantagem"`), trocar a linha `desvantagem = ...` para incluir a Defesa Impecável do alvo-jogador:
```python
                desvantagem = (prov or esc == "desvantagem"
                               or (is_player and self._defesa_impecavel_ativa(target)))
```
(Um site tem indentação ~8 espaços e o outro ~16 — ajuste a indentação de cada; `is_player`/`target` estão em escopo nos dois.)

- [ ] **Step 5: Imunidade a furtivo em `_verificar_ataque_furtivo`**

No início de `_verificar_ataque_furtivo(self, luccas, alvo)` (~5268), antes do teste de invisibilidade, adicionar:
```python
        if alvo.get("defesa_impecavel_ate", 0) >= self.round_num:
            return False   # Defesa Impecável: imune a Ataque Furtivo (inerte hoje — nenhum monstro dá furtivo a jogador)
```

- [ ] **Step 6: Rodar e ver passar** — [6]-[8] PASS. `python tools/test_ladino_espec.py`, `python tools/test_bardo_espec.py` verdes (furtivo/desvantagem intactos).
- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Defesa Impecavel (desvantagem contra voce + imune a furtivo)"
```

---

### Task 4: Tática Defensiva (`tatica_defensiva`) — protetor genérico

**Files:** Modify `server.py` (`handle_usar_tecnica`; `_processar_dano_protetor` ~7455); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [9]**

```python
    # [9] Tática Defensiva
    print("\n[9] Tática Defensiva")
    import random as _rnd; _rnd.seed(3)
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    r._no_raio = lambda a,b,raio,*x,**k: max(abs(a["pos"][0]-b["pos"][0]), abs(a["pos"][1]-b["pos"][1])) <= raio
    p = hero("warrior", "tecnica_tatica_defensiva"); p["pos"] = [0,0]; p["hp"] = 20; p["max_hp"] = 20; r.players["h"] = p
    ally = make_player("a","Ana","cleric",1); ally["alive"]=True; ally["pos"]=[1,1]; ally["hp"]=20; ally["max_hp"]=20; r.players["a"]=ally
    await r.handle_usar_tecnica("h", "tecnica_tatica_defensiva", "a")
    check("tatica: alvo gravado no usuário", p["tatica_alvo"] == "a")
    check("tatica: janela 1d4 setada", p["tatica_ate"] >= r.round_num + 1 and p["tatica_ate"] <= r.round_num + 4)
    # split 50/50 via _processar_dano_protetor no dano do aliado
    dano_alvo, transfer = await r._processar_dano_protetor("a", 10)
    check("tatica: aliado recebe metade", dano_alvo == 5)
    check("tatica: usuário recebe a outra metade", transfer is not None and transfer[0]["id"] == "h" and transfer[1] == 5)
    # aliado fora do raio 4 é recusado
    r3 = setup(); r3.current_pid = lambda: "h"; r3.round_num = 1; r3._no_raio = r._no_raio
    p3 = hero("warrior","tecnica_tatica_defensiva"); p3["pos"]=[0,0]; r3.players["h"]=p3
    far = make_player("a","Ana","cleric",1); far["alive"]=True; far["pos"]=[9,9]; r3.players["a"]=far
    await r3.handle_usar_tecnica("h","tecnica_tatica_defensiva","a")
    check("tatica: recusa aliado fora do raio 4", p3.get("tatica_alvo") is None)
```

- [ ] **Step 2: Rodar e ver falhar** — `tatica_defensiva` não tratado.

- [ ] **Step 3: Ramo no dispatch (valida aliado raio 4)**

```python
        elif ef.get("tipo") == "tatica_defensiva":
            alvo = self.players.get(target_id) if target_id else None
            if not alvo or not alvo.get("alive") or alvo["id"] == pid:
                await self.send_to(pid, {"type": "error", "msg": "Escolha um aliado vivo."}); return
            if not self._no_raio(p, alvo, ef.get("raio", 4)):
                await self.send_to(pid, {"type": "error", "msg": "Aliado fora do alcance (4 casas)."}); return
            p["tatica_alvo"] = alvo["id"]
            p["tatica_ate"] = self.round_num + self._rolar_dado("1d4")
```
(Use o helper de rolagem existente — confirme o nome: `_rolar_dado` ou `roll_dice`. Se for `roll_dice(str)`, use `roll_dice("1d4")`.)

- [ ] **Step 4: Generalizar `_processar_dano_protetor`**

Em `_processar_dano_protetor(self, alvo_id, dano_original)` (~7455), APÓS o bloco do paladino (que retorna se achou `richard`), acrescentar um segundo protetor genérico (Tática Defensiva) quando o paladino não cobre o alvo. Reescreva o início para tentar o paladino e, se não houver, tentar a Tática:
```python
        richard = next(
            (q for q in self.players.values()
             if q.get("class_id") == "paladin" and q.get("protetor_ativo")
             and q.get("protetor_alvo") == alvo_id and q.get("alive")),
            None)
        if richard:
            # ... (bloco existente do paladino, inalterado) ...
            return dano_alvo, (richard, dano_richard)   # (mantém o retorno atual do bloco)
        # Tática Defensiva (técnica genérica): metade/metade, expira por rodada.
        tatico = next(
            (q for q in self.players.values()
             if q.get("tatica_alvo") == alvo_id and q.get("tatica_ate", 0) >= self.round_num
             and q.get("alive") and q["id"] != alvo_id),
            None)
        if tatico:
            dano_aliado = dano_original // 2
            dano_tatico = dano_original - dano_aliado   # a "metade" que sobra vai pro tático
            await self.gm_say(
                f"🤝 **Tática Defensiva**: **{tatico['name']}** assume {dano_tatico} do dano de "
                f"**{self.players[alvo_id]['name']}** (que sofre {dano_aliado}).")
            return dano_aliado, (tatico, dano_tatico)
        return dano_original, None
```
> **CUIDADO:** preserve EXATAMENTE o bloco existente do paladino (split via `_defensor_split`, checagem de raio, mensagens). Só ENVOLVA-o em `if richard:` e adicione o ramo `tatico` + o `return dano_original, None` final. Rode `test_paladino_espec.py` para garantir que o Protetor do paladino segue idêntico.

- [ ] **Step 5: Rodar e ver passar** — [6]-[9] PASS. `python tools/test_paladino_espec.py` verde (Protetor intacto).
- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Tatica Defensiva (split 50/50, raio 4, 1d4 rodadas)"
```

---

### Task 5: Passo Fantasma (`passo_fantasma`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; `handle_move` ~5068-5073); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [10]**

```python
    # [10] Passo Fantasma
    print("\n[10] Passo Fantasma")
    import random as _rnd2; _rnd2.seed(5)
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_passo_fantasma"); p["moves_left"] = p["spd"]; r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_passo_fantasma")
    check("passo: +2 movimento imediato", p["moves_left"] == p["spd"] + 2)
    check("passo: buff de mov transitório", p["mov_bonus_ate"] == r.round_num + 1 and p.get("mov_bonus_val") == 2)
    check("passo: janela 1d4 setada", p["passo_fantasma_ate"] >= r.round_num + 1 and p["passo_fantasma_ate"] <= r.round_num + 4)
    check("passo: _passo_fantasma_ativo True", r._passo_fantasma_ativo(p) is True)
```

- [ ] **Step 2: Rodar e ver falhar** — `passo_fantasma`/`_passo_fantasma_ativo` inexistentes.

- [ ] **Step 3: Helper + ramo no dispatch**

Helper:
```python
    def _passo_fantasma_ativo(self, p):
        return p.get("passo_fantasma_ate", 0) >= self.round_num
```
Ramo:
```python
        elif ef.get("tipo") == "passo_fantasma":
            p["passo_fantasma_ate"] = self.round_num + self._rolar_dado("1d4")
            b = ef.get("bonus_mov", 2)
            p["moves_left"] = p.get("moves_left", 0) + b
            p["mov_bonus_ate"] = self.round_num + 1
            p["mov_bonus_val"] = b
```
(Use o mesmo helper de rolagem do Task 4.)

- [ ] **Step 4: Bypass de objetos em `handle_move`**

Em `handle_move`, os blocos de decoração e escombros (~5068-5073):
```python
        if (nx, ny) in self._decor_block_tiles:
            await self.send_to(pid, {"type": "error", "msg": "Há um objeto bloqueando o caminho."})
            return
        if (nx, ny) in self._mat_solid_tiles:
            await self.send_to(pid, {"type": "error", "msg": "Escombros bloqueiam o caminho."})
            return
```
trocar para pular esses dois blocos quando Passo Fantasma ativo (paredes/portas/criaturas continuam bloqueando):
```python
        _passo = self._passo_fantasma_ativo(p)
        if not _passo and (nx, ny) in self._decor_block_tiles:
            await self.send_to(pid, {"type": "error", "msg": "Há um objeto bloqueando o caminho."})
            return
        if not _passo and (nx, ny) in self._mat_solid_tiles:
            await self.send_to(pid, {"type": "error", "msg": "Escombros bloqueiam o caminho."})
            return
```
> As checagens de WALL (~5061), porta fechada (~5064), monstro (~5076), jogador (~5082) e animado (~5088) NÃO mudam — garantem que a casa final é válida e sem criaturas.

- [ ] **Step 5: Rodar e ver passar** — [6]-[10] PASS. Compile OK. `python tools/test_guilda.py` verde.
- [ ] **Step 6: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Passo Fantasma (+2 mov + atravessa objetos)"
```

---

### Task 6: Investida Heroica (`investida`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; `handle_attack` — vantagem+dano melee carregado; reset de fim de turno); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [11]**

```python
    # [11] Investida Heroica
    print("\n[11] Investida Heroica")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_investida"); p["pos"] = [0,0]; p["moves_left"] = p["spd"]; r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_investida")
    check("investida: dobra movimento", p["moves_left"] == p["spd"] + p["spd"])
    check("investida: armada + origem", p["investida_armada"] is True and p["investida_origem"] == [0,0])
    # helper de charge: reto ≥2 melee → 2; L / <2 / ranged → 0
    p["pos"] = [0,3]   # andou 3 em linha reta (coluna)
    check("investida: reto ≥2 melee → 2", r._investida_bonus(p, is_ranged=False) == 2)
    check("investida: ranged → 0", r._investida_bonus(p, is_ranged=True) == 0)
    p["pos"] = [1,1]   # L (dx=1,dy=1) → não é reto
    check("investida: L → 0", r._investida_bonus(p, is_ranged=False) == 0)
    p["pos"] = [0,1]   # reto mas só 1
    check("investida: reto <2 → 0", r._investida_bonus(p, is_ranged=False) == 0)
    # sem origem/flag → 0
    p2 = hero("warrior"); p2["pos"] = [0,5]
    check("investida: sem flag → 0", r._investida_bonus(p2, is_ranged=False) == 0)
```

- [ ] **Step 2: Rodar e ver falhar** — `investida`/`_investida_bonus` inexistentes.

- [ ] **Step 3: Helper + ramo no dispatch**

Helper (perto dos de técnica):
```python
    def _investida_bonus(self, p, is_ranged):
        """+2 de dano (e vantagem) da Investida se armada, melee e carga reta ≥2."""
        if is_ranged or not p.get("investida_armada"):
            return 0
        o = p.get("investida_origem")
        if not o:
            return 0
        dx, dy = p["pos"][0] - o[0], p["pos"][1] - o[1]
        reto = (dx == 0 or dy == 0)
        if reto and max(abs(dx), abs(dy)) >= 2:
            return 2
        return 0
```
Ramo no dispatch:
```python
        elif ef.get("tipo") == "investida":
            p["moves_left"] = p.get("moves_left", 0) + p.get("spd", 0)
            p["investida_origem"] = list(p["pos"])
            p["investida_armada"] = True
```

- [ ] **Step 4: Consumo em `handle_attack` (melee carregado)**

Espelha a Mira Perfeita. No bloco de vantagem (`_mira_ranged = ...`), acrescentar a Investida:
```python
            _mira_ranged = bool(w_range is not None and p.get("tecnica_mira_perfeita"))
            _investida = bool(w_range is None and self._investida_bonus(p, is_ranged=False))
            vantagem    = (bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela"))
                           or esc == "vantagem"
                           or self._provocacao_atk_vantagem(p, target)
                           or _mira_ranged or _investida)
            desvantagem = esc == "desvantagem"
            hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
            if _mira_ranged:
                p["tecnica_mira_perfeita"] = False
            if p.get("investida_armada") and w_range is None:
                p["investida_armada"] = False   # consome no 1º ataque melee (com ou sem carga)
```
No cálculo de dano de arma (onde já entra `(2 if _mira_ranged else 0)`), somar também `(2 if _investida else 0)`:
```python
                              + (2 if _mira_ranged else 0)   # Mira Perfeita
                              + (2 if _investida else 0)      # Investida Heroica (carga reta ≥2)
```

- [ ] **Step 5: Limpar no fim do turno**

Junto de `p["tecnica_mira_perfeita"] = False` no reset de fim de turno, adicionar:
```python
        p["investida_armada"] = False
        p["investida_origem"] = None
```

- [ ] **Step 6: Rodar e ver passar** — [6]-[11] PASS. `python tools/test_tecnicas_espec.py`, `python tools/test_bardo_espec.py`, `python tools/test_ladino_espec.py` verdes.
- [ ] **Step 7: Commit**
```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Tecnica Investida Heroica (carga reta >=2, melee, vantagem +2 dano)"
```

---

### Task 7: Cliente — seleção de alvo (Pressão Constante, Tática Defensiva)

**Files:** Modify `game.js` (onde o botão do 4º slot dispara `usar_tecnica`)

- [ ] **Step 1: Localizar o disparo da técnica no HUD**

Grep em `game.js` por `usar_tecnica` / `usarTecnica` / o botão do 4º slot (a técnica equipada). Identifique onde o clique envia `{type:'usar_tecnica', tecnica_id}`.

- [ ] **Step 2: Abrir o modal de alvo quando a técnica tiver `alvo`**

No handler do clique da técnica, ler a entrada do catálogo (`GS.guildCatalogFor(me.class_id).find(x=>x.id===tid)` ou o getter equivalente já usado) e, se tiver `alvo`:
- `alvo === 'monstro_adjacente'`: montar a lista de monstros adjacentes (Chebyshev 1 do `me.pos`) e chamar
  `openTargetModal('😖 Pressão Constante — inimigo adjacente', alvos, 'monster', id => send({type:'usar_tecnica', tecnica_id: tid, target_id: id}))`.
- `alvo === 'aliado_raio4'`: montar a lista de aliados vivos com `max(|dx|,|dy|) <= 4` de `me.pos` e chamar
  `openTargetModal('🤝 Tática Defensiva — aliado (4 casas)', alvos, 'player', id => send({type:'usar_tecnica', tecnica_id: tid, target_id: id}))`.
- Sem `alvo`: mantém o envio direto `send({type:'usar_tecnica', tecnica_id: tid})`.

Use o padrão exato do `openTargetModal` já usado pela Provocação (`iniciarProvocacao`) como referência de assinatura/filtragem. Se houver 1 só candidato, envie direto (como a Provocação faz).

- [ ] **Step 3: Sanidade** — `node --check game.js`.
- [ ] **Step 4: Commit**
```bash
git add game.js
git commit -m "feat(guilda): cliente pede alvo p/ Pressao Constante e Tatica Defensiva"
```

---

### Task 8: Verificação E2E (smoke) + docs

**Files:** Modify `CLAUDE.md`; Test via preview + suíte

- [ ] **Step 1: Suíte verde** — `python tools/test_tecnicas_espec.py` → `PASS=N FAIL=0`; regressões `test_guilda.py`/`test_paladino_espec.py`/`test_ladino_espec.py`/`test_bardo_espec.py` verdes.

- [ ] **Step 2: Smoke E2E** — Bump `CLASSES["warrior"]["start_gold"]` p/ 2000; `preview_start` "game"; abrir a Guilda e confirmar que as 5 técnicas aparecem na faixa "Recarga Média (5 rodadas)"; carregar a página e checar console sem erros; validar getters/estado via `preview_eval` se o WS não subir (registrar honestamente). Reverter `start_gold` e `rm -rf saves/`.

- [ ] **Step 3: Documentar na CLAUDE.md** — após o parágrafo do 2a, adicionar:

```markdown
> **Técnicas de Recarga Média (Fase 2b):** 2º lote das Técnicas da Guilda (recarga 5,
> preço 180, +4🍖/+4💧). **Investida Heroica** (`investida` — dobra movimento; se a carga
> for reta ≥2 casas desde a ativação e o ataque for corpo a corpo, vantagem +2 dano;
> `_investida_bonus`, consumida em `handle_attack`), **Defesa Impecável** (`defesa_impecavel`
> — até o próximo turno, ataques contra você com desvantagem, via `_defesa_impecavel_ativa`
> nos 2 sites de ataque de monstro; + imune a furtivo em `_verificar_ataque_furtivo` —
> inerte hoje, nenhum monstro dá furtivo a jogador), **Pressão Constante** (`debuff_ca_alvo`
> — inimigo adjacente −2 CA por 2 rodadas via `_pressao_ca_pen` no `eff_target_ac`),
> **Tática Defensiva** (`tatica_defensiva` — aliado em raio 4, 1d4 rodadas, split 50/50
> generalizando `_processar_dano_protetor`), **Passo Fantasma** (`passo_fantasma` — 1d4
> rodadas: +2 movimento + atravessa objetos em `handle_move`, mantendo paredes/criaturas).
> Cliente: técnicas com `alvo` (Pressão/Tática) usam `openTargetModal`. Teste:
> `tools/test_tecnicas_espec.py`. Próximos: 2c reações, 2d passivas; Fase 3 exclusivas.
```

- [ ] **Step 4: Commit final**
```bash
git add CLAUDE.md server.py
git commit -m "docs(guilda): documentar Tecnicas de Recarga Media (Fase 2b)"
```

---

## Auto-revisão (checklist do autor do plano)

- **Cobertura do spec:** 5 técnicas → T1 (catálogo) + T2 (Pressão+campos) + T3 (Defesa) + T4 (Tática) + T5 (Passo) + T6 (Investida); cliente de alvo → T7; E2E+docs → T8. ✔
- **Sem placeholders:** todo passo traz código real; exceções guiadas por conteúdo: T2/T3/T6 (anchors de combate) e T7 (cliente) — mitigadas com o padrão exato + `is_player`/`target` verificados em escopo. ✔
- **Consistência de nomes:** `efeito.tipo` ∈ {`investida`,`defesa_impecavel`,`debuff_ca_alvo`,`tatica_defensiva`,`passo_fantasma`}; campos `investida_armada`/`investida_origem`/`defesa_impecavel_ate`/`tatica_alvo`/`tatica_ate`/`passo_fantasma_ate`/`pressao_ca_ate`/`pressao_ca_val`; helpers `_pressao_ca_pen`/`_defesa_impecavel_ativa`/`_passo_fantasma_ativo`/`_investida_bonus` — idênticos entre tasks. ✔
- **Risco (validação de alvo antes do custo):** T2 alerta explicitamente para validar alvo antes de debitar custo/recarga em `handle_usar_tecnica`. ✔
- **Risco (generalizar Protetor):** T4 preserva o bloco do paladino e roda `test_paladino_espec.py`. ✔
- **Ordem de rolagem 1d4:** confirmar o helper (`_rolar_dado` vs `roll_dice`) no início de T4; usar o mesmo em T5. ✔
