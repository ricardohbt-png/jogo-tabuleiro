# Masmorra sequenciada + saída individual — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Etapas de uma aventura do mapa-múndi podem emendar direto na próxima masmorra, e um herói pode sair sozinho pela escada — pagando fome/sede e esperando N rodadas — enquanto o resto do grupo continua jogando.

**Architecture:** Duas mudanças independentes no `server.py`. (1) `handle_encerrar_missao` ganha um ramo que carrega a próxima etapa e chama `enter_dungeon` sem passar por `_voltar_para_cidade` — é justamente `_voltar_para_cidade` que recarrega slots/recargas, então "nada se recupera" sai de graça. (2) Um jogador ausente ganha a flag `p["fora_masmorra"]`; o portão `_ativo(p)` passa a excluí-lo (cobrindo 27 sites sem tocá-los, exatamente como um desconectado), e um portão novo `_em_cidade(pid)` libera os 5 handlers de loja/guilda/taverna para ele.

**Tech Stack:** Python 3 + `websockets` (servidor autoritativo, sem framework), JS vanilla (`game.js`, `src/gameState.js`, `tools/editor*.js`). Testes são scripts `asyncio` em `tools/test_*.py`, rodados da raiz.

**Spec:** `docs/superpowers/specs/2026-07-28-masmorra-sequenciada-saida-individual-design.md`

---

## Contexto que o implementador precisa

**Como rodar um teste:** da raiz do projeto, `python tools/test_masmorra_sequenciada.py`. O script imprime `=== N passou, M falhou ===` e sai com código 1 se algo falhou. Não há pytest neste projeto — os testes são scripts próprios com um `check(nome, condição)`. Siga o formato de `tools/test_campanha.py`.

**Estado relevante do `GameRoom` (server.py):**
- `self.phase` — `"lobby"` | `"city"` | `"playing"`, da SALA inteira.
- `self.players` — dict `pid -> ficha`; `self.connections` — dict `pid -> websocket`.
- `self.world_adventure_id` / `self.world_adventure_index` — aventura do mapa-múndi em curso e índice da etapa.
- `self.world_adventure_progress` — dict `adventure_id -> etapas concluídas`.
- `self.stairs_pos` — casa da escada de entrada; `self.round_num` — rodada atual.
- `self.dungeon_generated` — `False` força `enter_dungeon` a gerar/carregar um mapa novo.

**Masmorras de teste que já existem:** `dungeons/test_camp_a.json` (grid 10×8, 1 goblin, objetivo `kill_all`) e `dungeons/test_camp_b.json` (grid 12×8, 1 skeleton). Use as duas como as duas etapas da aventura de teste.

**Convenção de commit:** mensagens em português, prefixo `feat(...)`/`test(...)`/`docs(...)`. **Faça `git add` apenas dos arquivos que você tocou** — o usuário mantém trabalho em andamento não commitado em `server.py` e `game.js`; nunca use `git add -A` nem `git commit -a`.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta feature |
|---|---|
| `server.py` | Helpers de etapa/espera, encadeamento, saída individual, portões `_ativo`/`_em_cidade`, contador de rodadas |
| `tools/test_masmorra_sequenciada.py` | **Criar** — toda a cobertura da feature |
| `tools/test_campanha.py` | Ajuste: `handle_exit_dungeon` mudou de contrato |
| `tools/test_persistencia_masmorra.py` | Idem |
| `tools/editor_world.js` | Checkbox de encadear + intro/outro por etapa + espera de retorno |
| `tools/editor.html` | Checkbox "heróis podem sair pela escada" na barra de meta |
| `tools/editor.js` | Ler/gravar `saida_permitida` no JSON da masmorra |
| `src/gameState.js` | Senders `voltarMasmorra`, getters de estado do ausente |
| `game.js` | Confirmação na escada, card esmaecido no HUD, banner + botão na cidade |

---

### Task 1: Helpers de etapa e de espera

Aventuras guardam `dungeons` como lista de **strings**. Para caber o flag de encadeamento, cada entrada passa a aceitar string (legado) OU objeto — mesmo padrão que campanhas já usam em `_fase_obj`/`_fase_file` (`server.py:4281-4295`).

**Files:**
- Modify: `server.py` (logo após `_fase_obj`, ~linha 4296)
- Test: `tools/test_masmorra_sequenciada.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_masmorra_sequenciada.py` com o conteúdo abaixo (é o esqueleto que as tasks seguintes vão crescer):

```python
"""Testes de masmorra sequenciada + saída individual pela escada.
Roda da raiz: python tools/test_masmorra_sequenciada.py"""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def test_helpers_etapa():
    print("\n[1] helpers de etapa e espera")
    check("_etapa_file de string", server._etapa_file("a.json") == "a.json")
    check("_etapa_file de objeto", server._etapa_file({"file": "b.json"}) == "b.json")
    check("_etapa_file de lixo", server._etapa_file(7) is None)
    check("_etapa_obj normaliza string",
          server._etapa_obj("a.json") == {"file": "a.json", "encadear": False,
                                          "intro": "", "outro": ""})
    check("_etapa_obj preserva encadear",
          server._etapa_obj({"file": "b.json", "encadear": True})["encadear"] is True)
    check("_etapa_obj preserva intro/outro",
          server._etapa_obj({"file": "b.json", "intro": "abre", "outro": "fecha"})["intro"] == "abre")
    # espera
    check("espera default é fixa 0",
          server._clean_espera(None) == {"modo": "fixa", "rodadas": 0, "dados": ""})
    check("espera fixa preserva rodadas",
          server._clean_espera({"modo": "fixa", "rodadas": 3})["rodadas"] == 3)
    check("espera fixa faz clamp em 99",
          server._clean_espera({"modo": "fixa", "rodadas": 500})["rodadas"] == 99)
    check("espera com dados válidos",
          server._clean_espera({"modo": "dados", "dados": "1d4"})["dados"] == "1d4")
    check("dados inválidos caem para fixa",
          server._clean_espera({"modo": "dados", "dados": "muito"})["modo"] == "fixa")
    check("_rolar_espera fixa devolve o valor",
          server._rolar_espera({"modo": "fixa", "rodadas": 2}) == 2)
    check("_rolar_espera dados fica na faixa",
          1 <= server._rolar_espera({"modo": "dados", "dados": "1d4"}) <= 4)

async def main():
    test_helpers_etapa()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `AttributeError: module 'server' has no attribute '_etapa_file'`

- [ ] **Step 3: Implementar os helpers**

Em `server.py`, IMEDIATAMENTE APÓS a função `_fase_obj` (que termina em `return {"file": None, "intro": "", "outro": ""}`, ~linha 4295), INSIRA:

```python
def _etapa_file(item):
    """O arquivo de uma etapa de aventura (string legada ou objeto {file,...})."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("file")
    return None

def _etapa_obj(item):
    """Normaliza uma etapa de aventura para {file, encadear, intro, outro}.
    `encadear` faz a próxima etapa começar imediatamente, sem passar pela cidade."""
    if isinstance(item, str):
        return {"file": item, "encadear": False, "intro": "", "outro": ""}
    if isinstance(item, dict):
        return {"file": item.get("file"), "encadear": bool(item.get("encadear")),
                "intro": item.get("intro", ""), "outro": item.get("outro", "")}
    return {"file": None, "encadear": False, "intro": "", "outro": ""}

def _clean_espera(raw):
    """Normaliza a espera de retorno de uma aventura para
    {'modo': 'fixa'|'dados', 'rodadas': int, 'dados': str}. Fórmula inválida
    rebaixa o modo para 'fixa' — o autor nunca fica com uma espera quebrada."""
    raw = raw if isinstance(raw, dict) else {}
    modo = "dados" if raw.get("modo") == "dados" else "fixa"
    try:
        rodadas = max(0, min(99, int(raw.get("rodadas", 0))))
    except (TypeError, ValueError):
        rodadas = 0
    dados = str(raw.get("dados") or "").strip()[:16]
    if not re.fullmatch(r"\d{0,2}d\d{1,3}([+-]\d{1,3})?", dados):
        dados = ""
    if modo == "dados" and not dados:
        modo = "fixa"
    return {"modo": modo, "rodadas": rodadas, "dados": dados}

def _rolar_espera(espera):
    """Quantas rodadas o herói fica fora da masmorra nesta saída."""
    e = _clean_espera(espera)
    if e["modo"] == "dados":
        return max(0, roll_dice(e["dados"]))
    return e["rodadas"]
```

`re` e `roll_dice` já existem no módulo (`import re` no topo; `roll_dice` em `server.py:563`).

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 14 passou, 0 falhou ===`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(masmorra): helpers de etapa de aventura e de espera de retorno"
```

---

### Task 2: Persistência dos campos novos (aventura e masmorra)

O editor de mapa-múndi grava por `_save_world_adventures_upload` (`server.py:293-341`), que hoje reduz `dungeons` a uma lista de strings — precisa preservar `encadear`/`intro`/`outro` e a `espera_retorno`. E a masmorra ganha `saida_permitida`.

**Files:**
- Modify: `server.py:325-335` (limpeza de `dungeons` em `_save_world_adventures_upload`)
- Modify: `server.py:8173` (`handle_world_adventure` usa `_etapa_file`)
- Modify: `server.py:4113` (`validar_dungeon`, após o bloco `expected_party`)
- Modify: `server.py:8273-8278` (`enter_dungeon`, bloco `if nova:`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_masmorra_sequenciada.py`, ADICIONE antes de `async def main()`:

```python
def test_persistencia_campos():
    print("\n[2] persistência dos campos novos")
    row = {"id": "rota_teste", "nome": "Rota", "x": 10, "y": 20, "fome": 2, "sede": 3,
           "espera_retorno": {"modo": "dados", "dados": "1d4"},
           "dungeons": [{"file": "test_camp_a.json", "encadear": True, "outro": "fecha-1"},
                        "test_camp_b.json"]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou a aventura ({res if not ok else 'ok'})", ok is True)
        a = server.WORLD_ADVENTURES["rota_teste"]
        check("etapa 1 virou objeto com encadear",
              a["dungeons"][0] == {"file": "test_camp_a.json", "encadear": True,
                                   "intro": "", "outro": "fecha-1"})
        check("etapa 2 (string legada) normalizada",
              a["dungeons"][1]["file"] == "test_camp_b.json"
              and a["dungeons"][1]["encadear"] is False)
        check("espera_retorno preservada",
              a["espera_retorno"] == {"modo": "dados", "rodadas": 0, "dados": "1d4"})
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()

def test_validacao_saida():
    print("\n[3] validar_dungeon aceita saida_permitida")
    defn = server.carregar_dungeon("test_camp_a.json")
    defn["saida_permitida"] = False
    check("saida_permitida False é válida", server.validar_dungeon(defn)[0] is True)
    defn["saida_permitida"] = "talvez"
    check("saida_permitida não-booleana recusa", server.validar_dungeon(defn)[0] is False)
    defn.pop("saida_permitida")
    check("ausente continua válida", server.validar_dungeon(defn)[0] is True)
```

E, em `main()`, chame as duas logo após `test_helpers_etapa()`:

```python
    test_persistencia_campos()
    test_validacao_saida()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "etapa 1 virou objeto com encadear" (hoje vira a string `"test_camp_a.json"`) e em "saida_permitida não-booleana recusa".

- [ ] **Step 3: Implementar**

**3a.** Em `server.py`, dentro de `_save_world_adventures_upload`, SUBSTITUA:

```python
        files = row.get("dungeons", [])
        if not isinstance(files, list): files = []
        files = [str(f) for f in files if str(f) in allowed_files][:20]
        if not files:
            continue
```

por:

```python
        files = row.get("dungeons", [])
        if not isinstance(files, list): files = []
        etapas = []
        for raw_stage in files[:20]:
            et = _etapa_obj(raw_stage)
            if et["file"] in allowed_files:
                etapas.append({"file": et["file"], "encadear": et["encadear"],
                               "intro": str(et["intro"] or "")[:2000],
                               "outro": str(et["outro"] or "")[:2000]})
        if not etapas:
            continue
```

**3b.** No dict `cleaned[aid]` logo abaixo, TROQUE `"dungeons": files,` por `"dungeons": etapas,` e ACRESCENTE a espera. O dict fica:

```python
        cleaned[aid] = {"id": aid, "nome": name[:80], "x": x, "y": y,
                        "fome": fome, "sede": sede, "dungeons": etapas,
                        "espera_retorno": _clean_espera(row.get("espera_retorno")),
                        "requisito": req, "renome_recompensa": renome_reward}
```

**3c.** Em `handle_world_adventure` (`server.py:8173`), TROQUE:

```python
        file = stages[stage_index]
```

por:

```python
        file = _etapa_file(stages[stage_index])
```

**3d.** Em `validar_dungeon`, LOGO APÓS o bloco de `expected_party` (que termina com a linha `return False, f"expected_party.level inválido: {lv!r} (inteiro ≥ 1)."`), INSIRA:

```python
    sp = defn.get("saida_permitida")
    if sp is not None and not isinstance(sp, bool):
        return False, f"saida_permitida inválido: {sp!r} (booleano)."
```

**3e.** Em `enter_dungeon`, dentro do bloco `if nova:`, LOGO APÓS o `if autorada: ... else: ...` que carrega o mapa (ou seja, depois da linha `self.tiles, self.rooms = generate_dungeon()`), INSIRA:

```python
            # Saída pela escada: autorável por masmorra; procedural sempre permite.
            self.saida_permitida = bool(self.dungeon_def.get("saida_permitida", True)) if autorada else True
```

**3f.** Em `GameRoom.__init__`, junto de `self.expected_party = ...` (`server.py:5904`), ACRESCENTE:

```python
        self.saida_permitida = True   # masmorra permite sair pela escada de entrada
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 21 passou, 0 falhou ===`

Rode também a não-regressão do mapa-múndi e das campanhas:
Run: `python tools/test_campanha.py`
Expected: `0 falhou`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(masmorra): persiste encadear/espera na aventura e saida_permitida na masmorra"
```

---

### Task 3: Encadeamento das etapas

**Files:**
- Modify: `server.py:21088-21103` (ramo de aventura em `handle_encerrar_missao`)
- Modify: `server.py` (método novo `_emendar_proxima_etapa`, logo após `handle_encerrar_missao`)
- Modify: `server.py:8304-8309` (resets do `if nova:` em `enter_dungeon`)
- Modify: `server.py:12374` (`_voltar_para_cidade` limpa o beat pendente) e `server.py:21340` (`push_state` envia `story`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_masmorra_sequenciada.py`, ADICIONE (antes de `main()`):

```python
def _aventura(encadear):
    return {"id": "test_seq", "nome": "Rota Encadeada", "x": 10, "y": 10,
            "fome": 1, "sede": 1, "renome_recompensa": 1,
            "requisito": {"renome_min": 0, "nivel_grupo_min": 0,
                          "item_id": "", "fato": "", "aventura_id": ""},
            "espera_retorno": {"modo": "fixa", "rodadas": 2, "dados": ""},
            "dungeons": [{"file": "test_camp_a.json", "encadear": encadear,
                          "intro": "", "outro": "FECHA-1"},
                         {"file": "test_camp_b.json", "encadear": False,
                          "intro": "ABRE-2", "outro": ""}]}

def setup_room(encadear=True):
    """Sala de 2 heróis parada na cidade, com a aventura de teste instalada."""
    server.WORLD_ADVENTURES["test_seq"] = _aventura(encadear)
    r = GameRoom("SEQ")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop; r.broadcast_lobby = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys()); r.host_pid = "p1"
    r.phase = "city"
    return r

async def _concluir_etapa(r):
    """Mata tudo, recalcula objetivos e encerra a missão pelo host."""
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    await r.handle_encerrar_missao("p1")

async def test_encadeamento():
    print("\n[4] etapa encadeada começa imediatamente")
    r = setup_room(encadear=True)
    await r.handle_world_adventure("p1", "test_seq")
    check("entrou na etapa 1 (10×8)", r.map_w == 10 and r.map_h == 8)
    p1 = r.players["p1"]
    p1["hp"] = max(1, p1["hp"] - 4); hp_antes = p1["hp"]
    p1["technique_cooldowns"] = {"brutalidade": 99}
    p1["fome"] = 7; p1["sede"] = 5
    await _concluir_etapa(r)
    check("NÃO passou pela cidade", r.phase == "playing")
    check("carregou a etapa 2 (12×8)", r.map_w == 12 and r.map_h == 8)
    check("índice avançou", r.world_adventure_index == 1)
    check("progresso gravado", r.world_adventure_progress.get("test_seq") == 1)
    check("segue na mesma aventura", r.world_adventure_id == "test_seq")
    check("HP não se recupera", r.players["p1"]["hp"] == hp_antes)
    check("recarga de técnica não se recupera",
          r.players["p1"]["technique_cooldowns"] == {"brutalidade": 99})
    check("fome/sede não se recuperam e não são cobradas de novo",
          r.players["p1"]["fome"] == 7 and r.players["p1"]["sede"] == 5)
    check("beat de história encadeada montado",
          r._story_encadeada and [s.get("text") for s in r._story_encadeada["slides"]]
          == ["FECHA-1", "ABRE-2"])
    # última etapa: sem próxima, encerra normalmente pela cidade
    await _concluir_etapa(r)
    check("última etapa volta à cidade", r.phase == "city")
    check("aventura encerrada", r.world_adventure_id is None)

async def test_sem_encadeamento():
    print("\n[5] sem o flag, continua voltando à cidade (não-regressão)")
    r = setup_room(encadear=False)
    await r.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r)
    check("voltou à cidade", r.phase == "city")
    check("aventura liberada", r.world_adventure_id is None)
    check("progresso gravado mesmo assim", r.world_adventure_progress.get("test_seq") == 1)
```

E em `main()`:

```python
    await test_encadeamento()
    await test_sem_encadeamento()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "NÃO passou pela cidade" (hoje `r.phase == "city"`).

- [ ] **Step 3: Implementar**

**3a.** Em `server.py`, SUBSTITUA todo o ramo `if self.world_adventure_id:` de `handle_encerrar_missao` (linhas 21088-21103, do `if self.world_adventure_id:` até o `return`) por:

```python
        if self.world_adventure_id:
            adventure_id = self.world_adventure_id
            adventure = WORLD_ADVENTURES.get(adventure_id) or {}
            adventure_name = adventure.get("nome", "aventura")
            stages = list(adventure.get("dungeons") or [])
            completed_index = self.world_adventure_index if isinstance(self.world_adventure_index, int) else 0
            self.world_adventure_progress[adventure_id] = max(
                int(self.world_adventure_progress.get(adventure_id, 0) or 0), completed_index + 1)
            reward = int(adventure.get("renome_recompensa", 1) or 0)
            if reward:
                self.renome = max(0, self.renome + reward)
            # Etapa marcada como encadeada: emenda direto na próxima, sem cidade.
            etapa = _etapa_obj(stages[completed_index]) if completed_index < len(stages) else {"encadear": False}
            if etapa["encadear"] and completed_index + 1 < len(stages):
                await self._emendar_proxima_etapa(adventure, completed_index + 1)
                return
            self.world_adventure_id = None
            self.world_adventure_index = None
            self.dungeon_generated = False
            self._objetivo_concluido = False
            await self.gm_say(f"🏁 **{adventure_name}** concluída! O grupo retorna gratuitamente à cidade." + (f" Renome {reward:+d}." if reward else ""))
            await self._voltar_para_cidade()
            return
```

**3b.** LOGO APÓS o fim de `handle_encerrar_missao` (antes de `async def handle_libertar_prisioneiro`), INSIRA o método novo:

```python
    async def _emendar_proxima_etapa(self, adventure, indice):
        """Encadeamento: a próxima etapa começa imediatamente, sem passar pela
        cidade. Como quem recarrega slots/recargas/refeições é
        `_voltar_para_cidade`, não chamá-lo já entrega o 'nada se recupera' —
        HP, fome/sede, slots, recargas e status atravessam a emenda."""
        stages = list(adventure.get("dungeons") or [])
        anterior = _etapa_obj(stages[indice - 1])
        proxima  = _etapa_obj(stages[indice])
        defn = carregar_dungeon(proxima["file"])
        ok, motivo = validar_dungeon(defn) if defn else (False, "masmorra não encontrada")
        if not ok:
            # Etapa quebrada não pode prender o grupo na masmorra concluída.
            await self.gm_say(f"⚠️ A próxima etapa está indisponível ({motivo}). O grupo retorna à cidade.")
            self.world_adventure_id = None; self.world_adventure_index = None
            self.dungeon_generated = False; self._objetivo_concluido = False
            await self._voltar_para_cidade()
            return
        self._story_encadeada = _story_beat(
            f"encadeada:{adventure.get('id')}:{indice}",
            [anterior.get("outro"), proxima.get("intro")])
        self.mode = "authored"; self.selected_dungeon = proxima["file"]; self.dungeon_def = defn
        self.world_adventure_index = indice
        self.dungeon_generated = False
        self._objetivo_concluido = False
        self._emendando = True    # suprime os resets "por masmorra nova" (ver enter_dungeon)
        await self.gm_say(f"⛓️ Sem descanso: o grupo avança direto para a etapa {indice + 1}/{len(stages)} de **{adventure.get('nome', 'aventura')}**.")
        try:
            await self.enter_dungeon(self.host_pid, from_world_adventure=True)
        finally:
            self._emendando = False
```

**3c.** Em `GameRoom.__init__`, junto da linha `self.saida_permitida = True` acrescentada na Task 2, INSIRA:

```python
        self._story_encadeada = None   # beat de emenda entre etapas (consumido pelo cliente)
        self._emendando = False        # True durante _emendar_proxima_etapa
```

**3d.** Em `enter_dungeon`, no laço que posiciona os jogadores, o bloco `if nova:` reseta corrosão/vinho/cerveja/chamas. TROQUE a linha:

```python
            if nova:
```

(a que fica dentro do `for i, pid2 in enumerate(pids):`, seguida de `self._resetar_corrosao(...)`) por:

```python
            if nova and not self._emendando:
```

**3e.** Em `_voltar_para_cidade`, LOGO APÓS a linha `self.phase = "city"`, INSIRA:

```python
        self._story_encadeada = None   # a emenda não sobrevive à volta para a cidade
```

**3f.** Em `push_state`, no dict do broadcast, LOGO APÓS a linha `"campaign": self._campaign_payload(),` INSIRA:

```python
            "story": self._story_encadeada,   # beat da emenda; cliente faz de-dup por key
```

O cliente já consome isto sem mudança: `_captarStory` em `src/gameState.js:1717` lê `msg.story` de qualquer mensagem e deduplica por `beat.key`.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 35 passou, 0 falhou ===`

Run: `python tools/test_campanha.py`
Expected: `0 falhou`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(masmorra): etapa encadeada emenda direto na proxima, sem passar pela cidade"
```

---

### Task 4: Saída individual pela escada

Espelha `handle_disconnect_em_jogo` (`server.py:8625-8652`), que já resolve "o herói sai da masmorra, o peão vai para fora do tabuleiro e o turno avança".

**Files:**
- Modify: `server.py:8499-8502` (`_ativo`)
- Modify: `server.py:12362-12369` (`handle_exit_dungeon`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

ADICIONE em `tools/test_masmorra_sequenciada.py`:

```python
async def _entrar_e_posicionar_na_escada(r, pid="p1"):
    await r.handle_world_adventure("p1", "test_seq")
    r.players[pid]["pos"] = list(r.stairs_pos)
    r.initiative_order = [{"kind": "player", "id": pid, "seq": 0, "initiative": 99,
                           "dex": 0, "int": 0}]
    r.initiative_index = 0; r.initiative_active = True
    return r.players[pid]

async def test_saida_recusada():
    print("\n[6] saída pela escada — recusas")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 50; p["sede"] = 50
    # longe da escada
    p["pos"] = [r.stairs_pos[0] + 2, r.stairs_pos[1]]
    await r.handle_exit_dungeon("p1")
    check("longe da escada não sai", p.get("fora_masmorra") is None)
    p["pos"] = list(r.stairs_pos)
    # fora do turno
    r.initiative_order[0]["id"] = "p2"
    await r.handle_exit_dungeon("p1")
    check("fora do turno não sai", p.get("fora_masmorra") is None)
    r.initiative_order[0]["id"] = "p1"
    # sem provisões para ida e volta (custo da aventura é 1/1 → precisa de 2/2)
    p["fome"] = 1; p["sede"] = 50
    await r.handle_exit_dungeon("p1")
    check("sem fome para ida+volta não sai", p.get("fora_masmorra") is None)
    p["fome"] = 50; p["sede"] = 1
    await r.handle_exit_dungeon("p1")
    check("sem sede para ida+volta não sai", p.get("fora_masmorra") is None)
    # masmorra sem saída
    p["fome"] = 50; p["sede"] = 50; r.saida_permitida = False
    await r.handle_exit_dungeon("p1")
    check("masmorra sem saída não deixa sair", p.get("fora_masmorra") is None)

async def test_saida_efetiva():
    print("\n[7] saída pela escada — efeito")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    check("marcado como fora", isinstance(p.get("fora_masmorra"), dict))
    check("espera fixa de 2 rodadas", p["fora_masmorra"]["rodadas_restantes"] == 2)
    check("cobrou ida e volta (2×1 fome)", p["fome"] == 8)
    check("cobrou ida e volta (2×1 sede)", p["sede"] == 8)
    check("peão saiu do tabuleiro", p["pos"] == [-1, -1])
    check("_ativo passa a ser falso", r._ativo(p) is False)
    check("companheiro segue ativo", r._ativo(r.players["p2"]) is True)
    check("a sala continua na masmorra", r.phase == "playing")
    check("não sai duas vezes", (await r.handle_exit_dungeon("p1")) is None
          and p["fome"] == 8)
```

E em `main()`:

```python
    await test_saida_recusada()
    await test_saida_efetiva()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "longe da escada não sai" — hoje `handle_exit_dungeon` leva o grupo inteiro à cidade de qualquer casa.

- [ ] **Step 3: Implementar**

**3a.** Em `server.py`, SUBSTITUA `_ativo` inteiro por:

```python
    def _ativo(self, p):
        """Jogador ativo no jogo: vivo, conectado E dentro da masmorra.
        Desconectados e quem saiu pela escada (`fora_masmorra`) ficam com o peão
        fora do tabuleiro, são pulados na ordem de turnos e não são alvo."""
        return (bool(p) and bool(p.get("alive")) and p.get("connected", True)
                and not p.get("fora_masmorra"))
```

**3b.** SUBSTITUA `handle_exit_dungeon` inteiro por:

```python
    def _custo_viagem_saida(self):
        """Custo de IDA E VOLTA da saída individual: 2× o custo da aventura em
        curso. Fora de uma aventura (masmorra avulsa/campanha) a viagem é grátis."""
        adv = WORLD_ADVENTURES.get(self.world_adventure_id) or {}
        return 2 * int(adv.get("fome", 0) or 0), 2 * int(adv.get("sede", 0) or 0)

    async def handle_exit_dungeon(self, pid):
        """Saída INDIVIDUAL pela escada de entrada: o herói vai para a cidade e a
        masmorra continua para os demais. Espelha handle_disconnect_em_jogo (peão
        fora do tabuleiro + turno avança); o retorno é contado em
        _tick_retorno_masmorra."""
        p = self.players.get(pid)
        if not p or not p.get("alive") or p.get("fora_masmorra"):
            return
        if not self._is_turn(pid):
            await self.send_to(pid, {"type": "error", "msg": "Só é possível sair no seu turno."}); return
        if not self.saida_permitida:
            await self.send_to(pid, {"type": "error", "msg": "Não há como sair desta masmorra."}); return
        if not self.stairs_pos or list(p["pos"]) != list(self.stairs_pos):
            await self.send_to(pid, {"type": "error", "msg": "Vá até a escada de entrada para sair."}); return
        fome, sede = self._custo_viagem_saida()
        if p.get("fome", 0) < fome or p.get("sede", 0) < sede:
            await self.send_to(pid, {"type": "error",
                "msg": f"Provisões insuficientes para ir e voltar (precisa de 🍖{fome} e 💧{sede})."}); return
        p["fome"] -= fome; p["sede"] -= sede
        espera = _rolar_espera((WORLD_ADVENTURES.get(self.world_adventure_id) or {}).get("espera_retorno"))
        p["fora_masmorra"] = {"rodadas_restantes": espera}
        p["pos"] = [-1, -1]   # fora do tabuleiro: monstros ignoram, não ocupa casa
        await self.gm_say(
            f"🚪 **{p['name']}** sobe as escadas rumo à cidade "
            f"(🍖-{fome} 💧-{sede}) e volta em {espera} rodada(s).")
        era_turno = (self.phase == "playing" and self.current_pid() == pid)
        if era_turno:
            await self._forcar_fim_turno(pid)   # avança o turno (já reinicia o timer)
        await self.push_state()
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 48 passou, 0 falhou ===`

- [ ] **Step 5: Ajustar os dois testes que usavam o contrato antigo**

`tools/test_campanha.py:118` e `tools/test_persistencia_masmorra.py:77` chamam `handle_exit_dungeon` esperando que o GRUPO volte à cidade. Como a saída agora é individual, esses testes devem chamar `_voltar_para_cidade()`, que é o que eles realmente querem exercitar ("sair sem concluir retoma a mesma fase").

Em `tools/test_campanha.py`, TROQUE:

```python
    await r.handle_exit_dungeon("p1")     # sai sem concluir
```

por:

```python
    await r._voltar_para_cidade()         # grupo abandona a masmorra sem concluir
```

Em `tools/test_persistencia_masmorra.py`, TROQUE a linha `await r.handle_exit_dungeon("p1")` por `await r._voltar_para_cidade()`.

Run: `python tools/test_campanha.py` → `0 falhou`
Run: `python tools/test_persistencia_masmorra.py` → `0 falhou`

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py tools/test_campanha.py tools/test_persistencia_masmorra.py
git commit -m "feat(masmorra): saida pela escada vira individual, com custo de ida e volta"
```

---

### Task 5: O ausente age na cidade

**Files:**
- Modify: `server.py:6007-6016` (`broadcast` ganha `skip`)
- Modify: `server.py:6344-6382` (`broadcast_city_state` → payload extraído)
- Modify: `server.py:12653-12659` (`push_state_or_city`) e `server.py:21340` (broadcast do `push_state`)
- Modify: `server.py` — 5 handlers de cidade (`6433`, `6470`, `7576`, `7789`, `8118`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

ADICIONE em `tools/test_masmorra_sequenciada.py`:

```python
async def test_ausente_na_cidade():
    print("\n[8] o ausente age na cidade, a sala segue na masmorra")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    check("sala continua em playing", r.phase == "playing")
    check("_em_cidade só para quem saiu",
          r._em_cidade("p1") is True and r._em_cidade("p2") is False)
    # compra na loja estando fora
    p["gold"] = 999
    antes = len(p["bag"])
    await r.handle_shop_buy("p1", "mercador", "torch")
    check("comprou no mercador estando fora", len(p["bag"]) > antes)
    # o companheiro dentro da masmorra NÃO compra
    q = r.players["p2"]; q["gold"] = 999; antes_q = len(q["bag"])
    await r.handle_shop_buy("p2", "mercador", "torch")
    check("quem está na masmorra não compra", len(q["bag"]) == antes_q)
    # ações de grupo continuam bloqueadas para o ausente
    destino_antes = r.world_location
    await r.handle_world_travel("p1", "vila_charcos")
    check("ausente não viaja pelo mundo", r.world_location == destino_antes)

async def test_broadcast_separado():
    print("\n[9] game_state não chega a quem está na cidade")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    recebidos = {"p1": [], "p2": []}
    class FakeWS:
        def __init__(self, pid): self.pid = pid
        async def send(self, data):
            import json as _j
            recebidos[self.pid].append(_j.loads(data)["type"])
    r.connections = {"p1": FakeWS("p1"), "p2": FakeWS("p2")}
    del r.broadcast; del r.send_to        # usa os métodos reais da classe
    await r.handle_exit_dungeon("p1")
    recebidos["p1"].clear(); recebidos["p2"].clear()
    await GameRoom.push_state(r)
    check("p1 (na cidade) não recebe game_state", "game_state" not in recebidos["p1"])
    check("p2 (na masmorra) recebe game_state", "game_state" in recebidos["p2"])
    await r.push_state_or_city()
    check("p1 recebe city_state", "city_state" in recebidos["p1"])
    check("p2 não recebe city_state", "city_state" not in recebidos["p2"])
```

E em `main()`:

```python
    await test_ausente_na_cidade()
    await test_broadcast_separado()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_em_cidade'`

- [ ] **Step 3: Implementar**

**3a.** SUBSTITUA `broadcast` (`server.py:6007`) por:

```python
    async def broadcast(self, msg, skip=None):
        """Envia a todos os conectados. `skip` (set de pids) exclui destinatários —
        usado para não mandar game_state a quem está na cidade (fora_masmorra)."""
        dead = []
        data = json.dumps(msg)
        skip = skip or ()
        for pid, ws in list(self.connections.items()):
            if pid in skip:
                continue
            try:
                await ws.send(data)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.connections.pop(pid, None)
```

**3b.** Adicione os portões. LOGO APÓS `_ativo` (Task 4), INSIRA:

```python
    def _fora_da_masmorra(self, pid):
        """Pids que saíram pela escada e estão na cidade com a sala em jogo."""
        p = self.players.get(pid)
        return bool(p and p.get("fora_masmorra"))

    def _pids_fora(self):
        return {pid for pid, p in self.players.items() if p.get("fora_masmorra")}

    def _em_cidade(self, pid):
        """Pode usar lojas/guilda/taverna: a sala inteira está na cidade OU este
        jogador saiu sozinho pela escada."""
        return self.phase == "city" or self._fora_da_masmorra(pid)
```

**3c.** Extraia o payload da cidade. SUBSTITUA a assinatura de `broadcast_city_state` (`server.py:6344`) — o corpo `await self.broadcast({...})` vira:

```python
    def _city_state_payload(self):
        return {
```

…mantendo TODO o dict existente inalterado (de `"type": "city_state",` até o fecho do `"guild"`), e trocando o fechamento `})` final por `}`. Em seguida, LOGO APÓS esse método, ACRESCENTE:

```python
    async def broadcast_city_state(self):
        await self.broadcast(self._city_state_payload())

    async def send_city_state_to(self, pid):
        """city_state individual — para quem está na cidade com a sala em jogo."""
        await self.send_to(pid, self._city_state_payload())
```

**3d.** SUBSTITUA `push_state_or_city` por:

```python
    async def push_state_or_city(self):
        """Broadcast ciente da fase: na cidade os clientes estão em screen-city e
        usam city_state; na masmorra usam game_state (push_state). Quem saiu pela
        escada recebe city_state individual mesmo com a sala em jogo."""
        if self.phase == "city":
            await self.broadcast_city_state()
            return
        for pid in self._pids_fora():
            await self.send_city_state_to(pid)
        await self.push_state()
```

**3e.** No final de `push_state`, TROQUE `await self.broadcast({` por `await self.broadcast(msg_state, skip=self._pids_fora())`. Concretamente: renomeie o argumento inline para uma variável. SUBSTITUA a linha `await self.broadcast({` por:

```python
        msg_state = {
```

e o fechamento `})` do dict (última linha do método, logo após `"materiais": self._serializar_materiais(),`) por:

```python
        }
        # Quem está na cidade (fora_masmorra) não recebe game_state: o cliente
        # prefere gameState a cityState e mostraria o paperdoll da masmorra.
        await self.broadcast(msg_state, skip=self._pids_fora())
```

**3f.** Nos CINCO handlers de cidade, troque o portão. Em cada um, SUBSTITUA a linha `if self.phase != "city":` por `if not self._em_cidade(pid):`:

- `handle_guild_buy` (~`server.py:6433`)
- `handle_guild_equip` (~`server.py:6470`)
- `handle_shop_buy` (~`server.py:7576`)
- `handle_shop_sell` (~`server.py:7789`)
- `handle_tavern_npc` (~`server.py:8118`) — aqui a linha é `if self.phase != "city" or pid not in self.players:` e vira `if not self._em_cidade(pid) or pid not in self.players:`

**NÃO** toque em `handle_world_travel`, `handle_world_adventure`, `enter_dungeon` nem `handle_city_map_points`: são ações de grupo/anfitrião e devem seguir exigindo a sala inteira na cidade.

**3g.** Esses 5 handlers terminam chamando `broadcast_city_state()`. Para o ausente ver o resultado sem mandar city_state ao grupo inteiro em plena masmorra, TROQUE a chamada final de cada um dos 5 por `await self.push_state_or_city()`.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 57 passou, 0 falhou ===`

Run: `python tools/test_ficha_cidade.py`
Expected: `0 falhou` (garante que a extração do payload não quebrou a cidade normal)

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(masmorra): heroi fora da masmorra usa lojas e guilda com a sala em jogo"
```

---

### Task 6: Contagem das rodadas, retorno e casos-limite

**Files:**
- Modify: `server.py:8475-8487` (`_advance_initiative`)
- Modify: `server.py` (métodos novos `_tick_retorno_masmorra`, `_reentrar_masmorra`, `handle_voltar_masmorra`, `_checar_masmorra_vazia`)
- Modify: `server.py:21954` (dispatch de mensagens)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

ADICIONE em `tools/test_masmorra_sequenciada.py`:

```python
async def test_contador_e_retorno():
    print("\n[10] contador de rodadas e retorno")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    check("espera inicial 2", p["fora_masmorra"]["rodadas_restantes"] == 2)
    await r._tick_retorno_masmorra()
    check("após 1 rodada resta 1", p["fora_masmorra"]["rodadas_restantes"] == 1)
    await r._tick_retorno_masmorra()
    check("após 2 rodadas resta 0", p["fora_masmorra"]["rodadas_restantes"] == 0)
    check("ainda está fora (rodada de tolerância)", r._ativo(p) is False)
    await r._tick_retorno_masmorra()
    check("na rodada seguinte volta sozinho", p.get("fora_masmorra") is None)
    check("voltou ativo", r._ativo(p) is True)
    check("reapareceu na escada", list(p["pos"]) == list(r.stairs_pos))
    check("com turno cheio", p["action_done"] is False and p["moves_left"] > 0)

async def test_volta_manual():
    print("\n[11] botão de voltar à masmorra")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    await r.handle_voltar_masmorra("p1")
    check("não volta antes de zerar", p.get("fora_masmorra") is not None)
    p["fora_masmorra"]["rodadas_restantes"] = 0
    await r.handle_voltar_masmorra("p1")
    check("volta ao zerar", p.get("fora_masmorra") is None)
    check("de volta ao tabuleiro", list(p["pos"]) == list(r.stairs_pos))

async def test_masmorra_esvazia():
    print("\n[12] masmorra sem ninguém volta para a cidade")
    r = setup_room()
    for pid in ("p1", "p2"):
        r.players[pid]["fome"] = 10; r.players[pid]["sede"] = 10
    await _entrar_e_posicionar_na_escada(r, "p1")
    await r.handle_exit_dungeon("p1")
    check("com 1 dentro, segue em jogo", r.phase == "playing")
    r.players["p2"]["pos"] = list(r.stairs_pos)
    r.initiative_order = [{"kind": "player", "id": "p2", "seq": 0, "initiative": 99,
                           "dex": 0, "int": 0}]
    r.initiative_index = 0
    await r.handle_exit_dungeon("p2")
    check("todos fora → sala volta à cidade", r.phase == "city")
    check("ninguém fica marcado como fora",
          all(not q.get("fora_masmorra") for q in r.players.values()))

async def test_morte_com_heroi_na_cidade():
    print("\n[13] presentes morrem com um herói na cidade")
    r = setup_room()
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    fim = {"chamou": False}
    async def fake_end(victory, story=None): fim["chamou"] = True
    r.end_game = fake_end
    r.players["p2"]["alive"] = False
    await r._checar_masmorra_vazia()
    check("não é game over", fim["chamou"] is False)
    check("sala volta à cidade", r.phase == "city")

async def test_recompensa_com_ausente():
    print("\n[14] o ausente participa da recompensa e da etapa encadeada")
    r = setup_room(encadear=True)
    p = await _entrar_e_posicionar_na_escada(r)
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    xp_antes = p["xp"]; ouro_antes = p["gold"]
    r.objectives = {"primary": {"type": "kill_all", "xp": 100,
                                "reward": {"gold": 100, "items": []}},
                    "secondary": []}
    r._objetivo_concluido = False
    await _concluir_etapa(r)
    check("ausente recebeu XP", p["xp"] > xp_antes)
    check("ausente recebeu ouro", p["gold"] > ouro_antes)
    check("emendou na etapa 2", r.phase == "playing" and r.world_adventure_index == 1)
    check("segue fora, com o contador de pé", p.get("fora_masmorra") is not None)
```

E em `main()`:

```python
    await test_contador_e_retorno()
    await test_volta_manual()
    await test_masmorra_esvazia()
    await test_morte_com_heroi_na_cidade()
    await test_recompensa_com_ausente()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_tick_retorno_masmorra'`

- [ ] **Step 3: Implementar**

**3a.** LOGO APÓS `handle_exit_dungeon` (Task 4), INSIRA os quatro métodos:

```python
    async def _tick_retorno_masmorra(self):
        """Fecho de rodada: conta a espera de quem está fora. Ao zerar, o herói
        ganha UMA rodada de tolerância (para clicar em 'Voltar à masmorra' sem
        pressa); na rodada seguinte ele volta sozinho."""
        for pid, p in list(self.players.items()):
            fora = p.get("fora_masmorra")
            if not fora:
                continue
            if fora.get("rodadas_restantes", 0) > 0:
                fora["rodadas_restantes"] -= 1
                if fora["rodadas_restantes"] == 0:
                    await self.send_to(pid, {"type": "error",
                        "msg": "Você já pode voltar à masmorra."})
            else:
                await self._reentrar_masmorra(pid)

    async def _reentrar_masmorra(self, pid):
        """Traz de volta quem estava na cidade: reaparece na escada de entrada,
        com turno cheio, e volta a contar na iniciativa da próxima rodada."""
        p = self.players.get(pid)
        if not p or not p.get("fora_masmorra"):
            return
        p.pop("fora_masmorra", None)
        if self.phase != "playing":
            return   # a sala já voltou à cidade — não há masmorra para reentrar
        p["pos"] = self._free_tile_near(list(self.stairs_pos or [0, 0]))
        p.pop("facing", None)
        p["moves_left"]        = self._water_turn_moves(p, p["spd"])
        p["action_done"]       = False
        p["bonus_action_used"] = False
        await self.send_to(pid, {"type": "enter_dungeon"})
        await self.gm_say(f"🚪 **{p['name']}** desce as escadas e retorna à masmorra!")
        await self.push_state()

    async def handle_voltar_masmorra(self, pid):
        """Botão 'Voltar à masmorra': só depois que a espera zerou."""
        p = self.players.get(pid)
        fora = p.get("fora_masmorra") if p else None
        if not fora:
            return
        if fora.get("rodadas_restantes", 0) > 0:
            await self.send_to(pid, {"type": "error",
                "msg": f"A viagem ainda leva {fora['rodadas_restantes']} rodada(s)."}); return
        await self._reentrar_masmorra(pid)

    async def _checar_masmorra_vazia(self):
        """Sem nenhum herói ativo dentro da masmorra (todos saíram ou os presentes
        morreram) mas com alguém vivo na cidade, a expedição termina: a sala volta
        à cidade em vez de ficar travada. Devolve True se voltou."""
        if self.phase != "playing":
            return False
        if any(self._ativo(p) for p in self.players.values()):
            return False
        if not any(p.get("alive") for p in self.players.values()):
            return False   # TPK de verdade — quem trata é o fluxo de game over
        for p in self.players.values():
            p.pop("fora_masmorra", None)
        await self.gm_say("🏙️ Sem heróis na masmorra, a expedição é interrompida — o grupo se reúne na cidade.")
        await self._voltar_para_cidade()
        return True
```

**3b.** Chame o tick no fecho de rodada. Em `_advance_initiative`, LOGO APÓS a linha `await self._aplicar_exaustao_rodada()`, INSIRA:

```python
            await self._tick_retorno_masmorra()
```

**3c.** Chame o guarda de masmorra vazia no fim de `handle_exit_dungeon`. SUBSTITUA as duas últimas linhas dele:

```python
        if era_turno:
            await self._forcar_fim_turno(pid)   # avança o turno (já reinicia o timer)
        await self.push_state()
```

por:

```python
        if await self._checar_masmorra_vazia():
            return
        if era_turno:
            await self._forcar_fim_turno(pid)   # avança o turno (já reinicia o timer)
        await self.send_city_state_to(pid)
        await self.push_state()
```

**3d.** Chame-o também quando o último presente morre. Em `_player_dies`, na linha que hoje é:

```python
        if not any(p["alive"] for p in self.players.values()):
            await self.end_game(victory=False)
```

(a que fica ~`server.py:20899`), SUBSTITUA por:

```python
        if not any(p["alive"] for p in self.players.values()):
            await self.end_game(victory=False)
        else:
            await self._checar_masmorra_vazia()
```

**3e.** Registre a mensagem no dispatch. Em `server.py`, junto do `elif t == "exit_dungeon":` (~linha 21972), ACRESCENTE:

```python
                elif t == "voltar_masmorra":
                    if room: await room.handle_voltar_masmorra(pid)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 78 passou, 0 falhou ===`

Rode a bateria de não-regressão:
Run: `python tools/test_campanha.py` → `0 falhou`
Run: `python tools/test_persistencia_masmorra.py` → `0 falhou`
Run: `python tools/test_objetivos.py` → `0 falhou`
Run: `python tools/test_modo_mestre.py` → `0 falhou`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(masmorra): espera em rodadas, retorno pela escada e sala sem herois"
```

---

### Task 7: Editor de mapa-múndi — encadear e espera

**Files:**
- Modify: `tools/editor_world.js:27` (aventura nova), `:44` (linhas da sequência), `:45` (formulário), `:46` (sync), `:48-51` (handlers)

- [ ] **Step 1: Aventura nova nasce com os campos**

Em `tools/editor_world.js:27`, no `push` do botão `#worlded-add`, SUBSTITUA o objeto por:

```javascript
config.adventures.push({id:id,nome:'Novo destino',x:50,y:50,fome:0,sede:0,dungeons:[],espera_retorno:{modo:'fixa',rodadas:0,dados:''},requisito:{tipo:'nenhum',valor:''}});
```

- [ ] **Step 2: Normalizar as etapas ao renderizar**

Em `tools/editor_world.js`, na função que renderiza o painel, LOGO APÓS a linha `a.dungeons=Array.isArray(a.dungeons)?a.dungeons:[];` (linha 38), INSIRA:

```javascript
    // Etapa pode vir como string (formato antigo) ou objeto {file,encadear,intro,outro}.
    a.dungeons=a.dungeons.map(d=>typeof d==='string'?{file:d,encadear:false,intro:'',outro:''}:{file:d.file,encadear:!!d.encadear,intro:d.intro||'',outro:d.outro||''});
    a.espera_retorno=Object.assign({modo:'fixa',rodadas:0,dados:''},a.espera_retorno||{});
```

E na linha 41, TROQUE `const available=catalog.filter(d=>!a.dungeons.includes(d.file));` por:

```javascript
    const available=catalog.filter(d=>!a.dungeons.some(s=>s.file===d.file));
```

- [ ] **Step 3: Linha da sequência com checkbox e textos**

Em `tools/editor_world.js:44`, SUBSTITUA a construção de `sequence` por:

```javascript
    const sequence=a.dungeons.map((stage,index)=>'<div class="worlded-sequence-row"><b>'+String(index+1)+'ª</b><span>'+esc(dungeonName(stage.file))+'</span><button type="button" data-stage-up="'+index+'"'+(index===0?' disabled':'')+' title="Mover para cima">↑</button><button type="button" data-stage-down="'+index+'"'+(index===a.dungeons.length-1?' disabled':'')+' title="Mover para baixo">↓</button><button type="button" data-stage-remove="'+index+'" title="Remover">×</button>'
      +'<label title="A próxima etapa começa imediatamente, sem voltar ao mapa-múndi"><input type="checkbox" data-stage-chain="'+index+'"'+(stage.encadear?' checked':'')+(index===a.dungeons.length-1?' disabled':'')+'> ⛓️ emendar na próxima</label>'
      +'<label>Encerramento<textarea data-stage-outro="'+index+'" rows="2">'+esc(stage.outro||'')+'</textarea></label>'
      +'<label>Abertura<textarea data-stage-intro="'+index+'" rows="2">'+esc(stage.intro||'')+'</textarea></label>'
      +'</div>').join('')||'<small>Nenhuma masmorra vinculada. Adicione a primeira etapa abaixo.</small>';
```

- [ ] **Step 4: Campos da espera no formulário**

Em `tools/editor_world.js:45`, dentro do `host.innerHTML=...`, LOGO APÓS o bloco `<div class="worlded-cost">…</div>` (o das 🍖/💧), INSIRA (concatenando na mesma string):

```javascript
      +'<div class="worlded-cost"><label>Espera para retornar<select id="we-wait-mode"><option value="fixa"'+(a.espera_retorno.modo==='fixa'?' selected':'')+'>Fixa (rodadas)</option><option value="dados"'+(a.espera_retorno.modo==='dados'?' selected':'')+'>Dados</option></select></label><label>Rodadas<input id="we-wait-rounds" type="number" min="0" max="99" value="'+Number(a.espera_retorno.rodadas||0)+'"></label><label>Fórmula<input id="we-wait-dice" value="'+esc(a.espera_retorno.dados||'')+'" placeholder="1d4"></label></div>'
```

- [ ] **Step 5: Sincronizar e ligar os handlers**

Em `tools/editor_world.js:46`, no fim da função `sync`, ACRESCENTE:

```javascript
    a.espera_retorno={modo:$('#we-wait-mode',host).value==='dados'?'dados':'fixa',rodadas:Math.max(0,Math.min(99,Number($('#we-wait-rounds',host).value)||0)),dados:$('#we-wait-dice',host).value.trim()};
```

Em `tools/editor_world.js:48`, no handler de `#we-add-dungeon`, TROQUE o corpo por:

```javascript
    $('#we-add-dungeon',host).onclick=()=>{const file=$('#we-dungeon-catalog',host).value;if(file&&!a.dungeons.some(s=>s.file===file)){a.dungeons.push({file:file,encadear:false,intro:'',outro:''});render();}};
```

E LOGO APÓS os handlers `data-stage-remove` (linha 51), ACRESCENTE:

```javascript
    host.querySelectorAll('[data-stage-chain]').forEach(cb=>cb.onchange=()=>{a.dungeons[Number(cb.dataset.stageChain)].encadear=cb.checked;});
    host.querySelectorAll('[data-stage-intro]').forEach(ta=>ta.oninput=()=>{a.dungeons[Number(ta.dataset.stageIntro)].intro=ta.value;});
    host.querySelectorAll('[data-stage-outro]').forEach(ta=>ta.oninput=()=>{a.dungeons[Number(ta.dataset.stageOutro)].outro=ta.value;});
```

- [ ] **Step 6: Verificar no editor real**

Abra `http://localhost:8765/tools/editor.html` (com `python server.py` rodando), vá à aba do mapa-múndi, crie um destino com 2 masmorras, marque "⛓️ emendar na próxima" na 1ª, escreva um encerramento, escolha espera por dados `1d4` e salve. Recarregue a página e confirme que o checkbox, os textos e a espera voltaram preenchidos.

- [ ] **Step 7: Commit**

```bash
git add tools/editor_world.js
git commit -m "feat(editor): encadeamento por etapa e espera de retorno no mapa-mundi"
```

---

### Task 8: Editor de masmorras — permitir sair pela escada

**Files:**
- Modify: `tools/editor.html:23-26` (barra de meta)
- Modify: `tools/editor.js:22` (default), `:1583` (buildJSON), `:1733` (loadJSON), `:1785` (preencher campo), `:1816` (save)

- [ ] **Step 1: Campo no HTML**

Em `tools/editor.html`, LOGO APÓS o `<select id="m-ambiente">…</select>` e seu `</label>`, INSIRA:

```html
      <label title="Se desmarcado, os heróis não podem deixar a masmorra pela escada de entrada">
        <input type="checkbox" id="m-saida" checked> 🚪 saída pela escada
      </label>
```

- [ ] **Step 2: Default no estado**

Em `tools/editor.js:22`, TROQUE:

```javascript
    meta: { schema_version: 1, id: "nova_masmorra", name: "Nova Masmorra", ambiente: "masmorra" },
```

por:

```javascript
    meta: { schema_version: 1, id: "nova_masmorra", name: "Nova Masmorra", ambiente: "masmorra", saida_permitida: true },
```

- [ ] **Step 3: Gravar no JSON**

Em `tools/editor.js:1583` (`buildJSON`), TROQUE:

```javascript
      schema_version: 1, id: S.meta.id, name: S.meta.name, ambiente: S.meta.ambiente || "masmorra",
```

por:

```javascript
      schema_version: 1, id: S.meta.id, name: S.meta.name, ambiente: S.meta.ambiente || "masmorra",
      saida_permitida: S.meta.saida_permitida !== false,
```

- [ ] **Step 4: Ler do JSON**

Em `tools/editor.js:1733` (`loadJSON`), TROQUE:

```javascript
               ambiente: ["penumbra", "masmorra", "ar_livre"].includes(obj.ambiente) ? obj.ambiente : "masmorra" };
```

por:

```javascript
               ambiente: ["penumbra", "masmorra", "ar_livre"].includes(obj.ambiente) ? obj.ambiente : "masmorra",
               // Ausente = permitida: masmorras salvas antes deste campo não mudam de comportamento.
               saida_permitida: obj.saida_permitida !== false };
```

E, junto das linhas que preenchem os inputs (~1785), LOGO APÓS `document.getElementById("m-ambiente").value = ...`, INSIRA:

```javascript
    document.getElementById("m-saida").checked = S.meta.saida_permitida !== false;
```

- [ ] **Step 5: Ler o campo ao salvar**

Em `tools/editor.js:1816` (`save`), LOGO APÓS `S.meta.ambiente = document.getElementById("m-ambiente").value || "masmorra";`, INSIRA:

```javascript
    S.meta.saida_permitida = document.getElementById("m-saida").checked;
```

- [ ] **Step 6: Verificar no editor real**

Abra o editor, desmarque "🚪 saída pela escada", salve a masmorra e reabra: o checkbox deve voltar desmarcado. Confirme no arquivo em `dungeons/` que existe `"saida_permitida": false`.

- [ ] **Step 7: Commit**

```bash
git add tools/editor.html tools/editor.js
git commit -m "feat(editor): checkbox de saida pela escada no painel da masmorra"
```

---

### Task 9: Cliente — camada de estado

**Files:**
- Modify: `src/gameState.js` (senders e getters, junto de `exitDungeon`/`selectCampaign`)

- [ ] **Step 1: Sender e getters**

Em `src/gameState.js`, junto dos demais senders (por exemplo perto de `selectCampaign`, ~linha 1708), INSIRA:

```javascript
  // ── Saída individual pela escada (masmorra sequenciada) ────────────────────
  // O herói sai sozinho, vai para a cidade e volta N rodadas depois. Enquanto
  // está fora, o servidor manda city_state só para ele (não game_state).
  function voltarMasmorra() { send({ type: 'voltar_masmorra' }); }

  function foraMasmorraDe(p) {
    return (p && p.fora_masmorra) || null;
  }
  function estouForaDaMasmorra() {
    const cs = cityState;
    const me = cs && (cs.players || []).find(p => p.id === myPid);
    return !!foraMasmorraDe(me);
  }
  function rodadasParaVoltar() {
    const cs = cityState;
    const me = cs && (cs.players || []).find(p => p.id === myPid);
    const fora = foraMasmorraDe(me);
    return fora ? (fora.rodadas_restantes | 0) : 0;
  }
```

Exporte os quatro no objeto público do módulo (o mesmo `return {...}`/`window.GS = {...}` onde `exitDungeon` já aparece): acrescente `voltarMasmorra, foraMasmorraDe, estouForaDaMasmorra, rodadasParaVoltar,`.

- [ ] **Step 2: Verificar que carrega**

Com `python server.py` rodando, abra `http://localhost:8765/index.html`, e no console do navegador rode:

```javascript
typeof GS.voltarMasmorra
```

Expected: `"function"` (e nenhum erro de sintaxe no console).

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(cliente): estado do heroi fora da masmorra e sender de retorno"
```

---

### Task 10: Cliente — escada, HUD e banner da cidade

**Files:**
- Modify: `game.js:23252-23261` (clique na escada)
- Modify: `game.js:8262-8290` (`renderPlayers`)
- Modify: `game.js` (banner na cidade, dentro do handler de `cityState`, ~23482)

- [ ] **Step 1: Clique na escada pede confirmação**

Em `game.js`, SUBSTITUA o bloco do clique na escada (`// ── Stairs: clicking the staircase tile exits the dungeon immediately ────`) por:

```javascript
  // ── Escada: sair é INDIVIDUAL — custa fome/sede e tem espera em rodadas ────
  const _st = GS.gameState;
  if(_st && _st.stairs_pos){
    const [sx,sy] = _st.stairs_pos;
    if(tx===sx && ty===sy){
      const me = (_st.players||[]).find(p=>p.id===GS.myPid && p.alive);
      if(!me) return;
      if(_st.saida_permitida === false){ toast('Não há como sair desta masmorra.', 'var(--red)'); return; }
      if(!GS.isMyTurn()){ toast('Só é possível sair no seu turno.', 'var(--red)'); return; }
      if(me.pos[0]!==sx || me.pos[1]!==sy){ toast('Vá até a escada para sair.', 'var(--red)'); return; }
      const custo = _st.custo_saida || {fome:0, sede:0};
      const espera = _st.espera_saida || '0';
      if(me.fome < custo.fome || me.sede < custo.sede){
        toast(`Provisões insuficientes: a viagem custa 🍖${custo.fome} e 💧${custo.sede}.`, 'var(--red)');
        return;
      }
      if(!confirm(`Sair pela escada custa 🍖${custo.fome} e 💧${custo.sede} (ida e volta).\n`
                  + `Você volta em ${espera} rodada(s) e a masmorra continua sem você.\n\nSair?`)) return;
      fecharQuadrosFlutuantes();
      send({type:'exit_dungeon'});
      return;
    }
  }
```

Para o cliente ter `custo_saida`/`espera_saida`/`saida_permitida`, ACRESCENTE ao dict `msg_state` de `push_state` (server.py, junto de `"stairs_pos": self.stairs_pos,`):

```python
            "saida_permitida": self.saida_permitida,
            "custo_saida": dict(zip(("fome", "sede"), self._custo_viagem_saida())),
            "espera_saida": (lambda e: e["dados"] if e["modo"] == "dados" else str(e["rodadas"]))(
                _clean_espera((WORLD_ADVENTURES.get(self.world_adventure_id) or {}).get("espera_retorno"))),
```

- [ ] **Step 2: Card esmaecido no HUD**

Em `game.js`, dentro de `renderPlayers`, LOGO APÓS a linha `const disc=p.connected===false;`, INSIRA:

```javascript
    const fora=p.fora_masmorra||null;
```

TROQUE a linha seguinte, `if(disc) div.style.opacity='0.45';`, por:

```javascript
    if(disc||fora) div.style.opacity='0.45';
```

E, dentro do template `div.innerHTML`, LOGO APÓS a `<div class="pcard-top">…</div>` (antes de `<div class="bars">`), INSIRA:

```javascript
      ${fora ? `<div class="pcard-fora" style="font-size:11px;color:#8fc6ff;">🏙️ na cidade — volta em ${fora.rodadas_restantes|0} rodada(s)</div>` : ''}
```

- [ ] **Step 3: Banner e botão na cidade**

Em `game.js`, no handler `GS.on('cityState', …)`, LOGO APÓS `handleCityState(msg);`, INSIRA:

```javascript
  _renderBannerForaMasmorra();
```

E defina a função LOGO ANTES desse handler:

```javascript
// Banner do herói que saiu sozinho da masmorra: contador + botão de retorno.
// Só existe quando a SALA continua na masmorra e este cliente está na cidade.
function _renderBannerForaMasmorra(){
  const host = document.getElementById('screen-city');
  let el = document.getElementById('fora-masmorra-banner');
  if(!GS.estouForaDaMasmorra()){ if(el) el.remove(); return; }
  const n = GS.rodadasParaVoltar();
  if(!el){
    el = document.createElement('div');
    el.id = 'fora-masmorra-banner';
    el.style.cssText = 'position:absolute;top:8px;left:50%;transform:translateX(-50%);'
      + 'z-index:60;background:rgba(20,26,38,.92);border:1px solid #4a6f9e;border-radius:8px;'
      + 'padding:8px 14px;color:#dce8ff;font-size:13px;display:flex;gap:10px;align-items:center;';
    host.appendChild(el);
  }
  el.innerHTML = `<span>🏙️ Você deixou a masmorra — ${n>0 ? `volta em <b>${n}</b> rodada(s)` : '<b>pronto para voltar</b>'}</span>`;
  const btn = document.createElement('button');
  btn.textContent = '⛓️ Voltar à masmorra';
  btn.disabled = n > 0;
  btn.onclick = () => GS.voltarMasmorra();
  el.appendChild(btn);
}
```

- [ ] **Step 4: Verificar no jogo real**

Suba o servidor (`python server.py`), abra duas abas em `http://localhost:8765/index.html`, crie sala com 2 heróis, entre numa aventura de 2 etapas com encadeamento e espera fixa 1. Verifique:

1. um herói anda até a escada, clica, vê a confirmação com o custo, aceita → ele vai para a tela da cidade com o banner, e a outra aba continua na masmorra com o card dele esmaecido;
2. o herói na cidade abre o mercador e compra algo;
3. passadas as rodadas, o botão libera e ele volta para a escada;
4. concluindo o objetivo com o flag de encadeamento, os slides de encerramento/abertura aparecem e o mapa da etapa 2 entra sem passar pela cidade.

- [ ] **Step 5: Commit**

```bash
git add game.js server.py
git commit -m "feat(cliente): confirmacao na escada, card do ausente e banner de retorno"
```

---

## Verificação final

- [ ] `python tools/test_masmorra_sequenciada.py` → `0 falhou`
- [ ] `python tools/test_campanha.py` → `0 falhou`
- [ ] `python tools/test_persistencia_masmorra.py` → `0 falhou`
- [ ] `python tools/test_objetivos.py` → `0 falhou`
- [ ] `python tools/test_modo_mestre.py` → `0 falhou`
- [ ] `python tools/test_ficha_cidade.py` → `0 falhou`
- [ ] `python tools/test_guilda.py` → mesmo número de falhas do HEAD (há falhas pré-existentes; compare antes e depois)
- [ ] Smoke test in-app com 2 clientes (Task 10, Step 4) concluído
- [ ] Atualizar o `CLAUDE.md` com um parágrafo da feature, no padrão dos demais blocos `>` (protocolo: mensagens `exit_dungeon` com o novo contrato e `voltar_masmorra`; campos `saida_permitida`, `espera_retorno`, `encadear`)
