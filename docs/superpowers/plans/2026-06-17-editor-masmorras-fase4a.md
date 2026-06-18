# Editor de Masmorras — Fase 4a (Runtime de Campanha) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jogar uma campanha autorada — sequência ordenada de masmorras; concluir o objetivo de uma fase leva à cidade/loja e à próxima fase; última fase = vitória. Heróis carregam HP/XP/ouro/itens.

**Architecture:** `campaigns/*.json` lista arquivos de `dungeons/`. O lobby seleciona uma campanha (`select_campaign`). `enter_dungeon` carrega a masmorra da fase atual (caminho autorado da Fase 1). O avanço acontece em `_check_objectives` (Fase 3): principal cumprido → se não é a última fase, avança e volta à cidade (helper `_voltar_para_cidade`); senão, `end_game(victory)`. Procedural intacto.

**Tech Stack:** Python (`server.py`, autoritativo) + Vanilla JS (`src/gameState.js`, `game.js`). Testes = scripts `tools/test_*.py` com `check()` (NÃO pytest).

**Spec:** `docs/superpowers/specs/2026-06-17-editor-masmorras-fase4a-design.md`

---

## Notas de design (ler antes de começar)

- **Convenção de teste:** ver `tools/test_persistencia_masmorra.py`. `sys.path.insert` da raiz, `import server`, `GameRoom("TEST")`, stub de rede (`gm_say/broadcast/push_state/send_to/broadcast_city_state` = noop), helper `check()`, `sys.exit(1 if FAIL else 0)`, `sys.stdout.reconfigure(encoding="utf-8")` no topo. Rodar com `PYTHONIOENCODING=utf-8` no Windows.
- **Mirrors:** os helpers de campanha espelham os de masmorra: `carregar_dungeon`/`validar_dungeon`/`listar_dungeons`/`DUNGEONS_DIR` (server.py). `os`/`json` já importados no topo.
- **Anchors atuais (linhas aproximadas — localizar por texto):** `enter_dungeon` autorada `autorada = self.mode == "authored" and self.dungeon_def is not None` (~3469); o `nova` block segue. `_check_objectives` bloco de conclusão (~11911-11917). `handle_exit_dungeon` (~6013). `handle_select_dungeon`/`broadcast_lobby` (Fase 1). `GameRoom.__init__` defaults perto de `self.dungeon_def = None`.
- **Commits:** cada task termina com `git add <arquivos exatos>` (nunca `git add -A`).

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | helpers de campanha; `__init__` defaults; `handle_select_campaign` + dispatch; `broadcast_lobby` (campaigns); `enter_dungeon` (carrega fase); `autorada` estendido; `_voltar_para_cidade` + branch de avanço em `_check_objectives`; campo `campaign` em `push_state`/`city_state` |
| `campaigns/test_campanha.json` | Criar | Fixture de campanha (2 fases) |
| `dungeons/test_camp_a.json`, `dungeons/test_camp_b.json` | Criar | Masmorras-fase mínimas (kill_all), grids distintos |
| `tools/test_campanha.py` | Criar | Testes headless do runtime de campanha |
| `src/gameState.js` | Modificar | getter `campaign`/`lobbyCampaigns`; sender `selectCampaign` |
| `game.js` | Modificar | grupo "Campanhas" no dropdown; indicador "Fase N de M"; botão "Entrar na próxima fase" |

---

## Task 1: Helpers de campanha + fixtures + validação

**Files:**
- Modify: `server.py` (após os helpers de dungeon, perto de `listar_dungeons`)
- Create: `campaigns/test_campanha.json`, `dungeons/test_camp_a.json`, `dungeons/test_camp_b.json`
- Create: `tools/test_campanha.py`

- [ ] **Step 1: Criar as masmorras-fase e a campanha**

`dungeons/test_camp_a.json`:

```json
{
  "schema_version": 1, "id": "test_camp_a", "name": "Campanha A",
  "grid": { "w": 10, "h": 8 },
  "tiles": [
    [0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0]
  ],
  "rooms": [ { "id": 0, "x": 1, "y": 1, "w": 8, "h": 6, "role": "entrance", "locked": false, "doors": [] } ],
  "entrance": { "x": 2, "y": 2 }, "exit": null,
  "monsters": [ { "type": "goblin", "pos": [5,3], "room_id": 0, "boss": false, "target": false } ],
  "chests": [], "traps": [], "prisoner": null,
  "objectives": { "primary": { "type": "kill_all" }, "secondary": [] }
}
```

`dungeons/test_camp_b.json`:

```json
{
  "schema_version": 1, "id": "test_camp_b", "name": "Campanha B",
  "grid": { "w": 12, "h": 8 },
  "tiles": [
    [0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0]
  ],
  "rooms": [ { "id": 0, "x": 1, "y": 1, "w": 10, "h": 6, "role": "entrance", "locked": false, "doors": [] } ],
  "entrance": { "x": 2, "y": 2 }, "exit": null,
  "monsters": [ { "type": "skeleton", "pos": [5,3], "room_id": 0, "boss": false, "target": false } ],
  "chests": [], "traps": [], "prisoner": null,
  "objectives": { "primary": { "type": "kill_all" }, "secondary": [] }
}
```

`campaigns/test_campanha.json`:

```json
{ "schema_version": 1, "id": "test_campanha", "name": "Campanha de Teste", "dungeons": ["test_camp_a.json", "test_camp_b.json"] }
```

Conferir que cada masmorra valida: `python -c "import server,json; print(server.validar_dungeon(json.load(open('dungeons/test_camp_a.json',encoding='utf-8'))), server.validar_dungeon(json.load(open('dungeons/test_camp_b.json',encoding='utf-8'))))"` → ambos `(True, 'ok')`.

- [ ] **Step 2: Escrever o teste que falha**

Criar `tools/test_campanha.py`:

```python
"""Testes da Fase 4a: runtime de campanha.
Roda da raiz: python tools/test_campanha.py"""
import asyncio, sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, carregar_campanha, validar_campanha, listar_campanhas

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup_room():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop; r.broadcast_lobby = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys()); r.host_pid = "p1"
    return r

def test_validacao():
    print("\n[1] validar/listar campanha")
    defn = carregar_campanha("test_campanha.json")
    check("carrega o arquivo", defn is not None)
    ok, msg = validar_campanha(defn)
    check(f"campanha válida ({msg})", ok is True)
    check("aparece em listar_campanhas",
          any(c["file"] == "test_campanha.json" for c in listar_campanhas()))
    check("lista vazia recusa", validar_campanha({"schema_version": 1, "dungeons": []})[0] is False)
    check("fase inexistente recusa",
          validar_campanha({"schema_version": 1, "dungeons": ["nao_existe.json"]})[0] is False)
    check("path traversal recusado", carregar_campanha("../server.py") is None)

async def main():
    test_validacao()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL — `ImportError: cannot import name 'carregar_campanha'`.

- [ ] **Step 4: Implementar os helpers**

Em `server.py`, logo após `listar_dungeons` (procurar `def listar_dungeons`), inserir:

```python
CAMPAIGNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campaigns")

def carregar_campanha(file):
    """Lê e parseia um arquivo de CAMPAIGNS_DIR. Retorna dict ou None."""
    if not isinstance(file, str) or not file or file != os.path.basename(file):
        return None  # proteção contra path traversal
    caminho = os.path.join(CAMPAIGNS_DIR, file)
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def validar_campanha(defn):
    """Valida um dict de campanha. Retorna (ok: bool, msg: str). Cada fase deve
    existir em dungeons/ e passar em validar_dungeon."""
    if not isinstance(defn, dict):
        return False, "Campanha não é um objeto JSON."
    if defn.get("schema_version") != 1:
        return False, f"schema_version não suportado: {defn.get('schema_version')!r} (esperado 1)."
    dungeons = defn.get("dungeons")
    if not (isinstance(dungeons, list) and len(dungeons) >= 1):
        return False, "campanha precisa de ao menos uma masmorra em 'dungeons'."
    for i, file in enumerate(dungeons):
        d = carregar_dungeon(file) if isinstance(file, str) else None
        if d is None:
            return False, f"fase {i+1}: masmorra '{file}' não encontrada."
        ok, msg = validar_dungeon(d)
        if not ok:
            return False, f"fase {i+1} ('{file}'): {msg}"
    return True, "ok"

def listar_campanhas():
    """Varre CAMPAIGNS_DIR e devolve [{id, name, file}] das campanhas válidas."""
    out = []
    try:
        arquivos = sorted(f for f in os.listdir(CAMPAIGNS_DIR) if f.endswith(".json"))
    except Exception:
        return out
    for file in arquivos:
        defn = carregar_campanha(file)
        if not defn:
            continue
        ok, _ = validar_campanha(defn)
        if ok:
            out.append({"id": defn.get("id", file), "name": defn.get("name", file), "file": file})
    return out
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_campanha.py`
Expected: PASS — `=== 6 passou, 0 falhou ===`.

- [ ] **Step 6: Commit**

```bash
git add server.py campaigns/test_campanha.json dungeons/test_camp_a.json dungeons/test_camp_b.json tools/test_campanha.py
git commit -m "feat: helpers de campanha (carregar/validar/listar) + fixtures (Fase 4a)"
```

---

## Task 2: Estado + seleção no lobby

**Files:**
- Modify: `server.py` (`__init__`; `handle_select_campaign` + dispatch; `broadcast_lobby`; `handle_select_dungeon` limpa campanha)
- Test: `tools/test_campanha.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
async def test_selecao():
    print("\n[2] seleção de campanha no lobby")
    r = setup_room(); r.phase = "lobby"
    check("defaults: campaign None, phase 0",
          getattr(r, "campaign", "x") is None and getattr(r, "campaign_phase", -1) == 0)
    await r.handle_select_campaign("p1", "test_campanha.json")
    check("modo vira campaign", r.mode == "campaign")
    check("campaign carregado", r.campaign and r.campaign["id"] == "test_campanha")
    check("campaign_phase = 0", r.campaign_phase == 0)
    # inválida não muda estado
    await r.handle_select_campaign("p1", "nao_existe.json")
    check("campanha inválida mantém a seleção", r.mode == "campaign")
    # null volta para procedural
    await r.handle_select_campaign("p1", None)
    check("None volta para procedural", r.mode == "procedural" and r.campaign is None)
    # selecionar masmorra avulsa limpa a campanha
    await r.handle_select_campaign("p1", "test_campanha.json")
    await r.handle_select_dungeon("p1", "test_camp_a.json")
    check("select_dungeon limpa a campanha", r.campaign is None and r.mode == "authored")
    # não-host é ignorado
    r.mode = "procedural"
    await r.handle_select_campaign("p2", "test_campanha.json")
    check("não-host ignorado", r.mode == "procedural")
```

E em `main()`: `await test_selecao()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL no `[2]` — `campaign` é `"x"` (default ausente) / `handle_select_campaign` inexistente.

- [ ] **Step 3: Defaults no `__init__`**

Em `server.py`, no `GameRoom.__init__`, logo após o bloco de defaults da Fase 3 (`self._objetivo_concluido = False`), inserir:

```python
        # Fase 4a — campanha.
        self.campaign = None         # dict carregado (modo "campaign")
        self.campaign_phase = 0      # índice da fase atual em campaign["dungeons"]
```

- [ ] **Step 4: `handle_select_campaign` + limpar campanha em `handle_select_dungeon`**

Em `server.py`, inserir como método de `GameRoom`, logo após `handle_select_dungeon`:

```python
    async def handle_select_campaign(self, pid, file):
        """Host escolhe uma campanha do lobby. file=None → procedural."""
        if pid != self.host_pid:
            return
        if self.phase != "lobby":
            return
        if not file:
            self.mode = "procedural"; self.selected_dungeon = None
            self.dungeon_def = None; self.campaign = None; self.campaign_phase = 0
        else:
            defn = carregar_campanha(file)
            ok, msg = (False, "Campanha não encontrada.") if defn is None else validar_campanha(defn)
            if not ok:
                await self.send_to(pid, {"type": "error", "msg": f"Campanha inválida: {msg}"})
                return
            self.mode = "campaign"; self.campaign = defn; self.campaign_phase = 0
            self.selected_dungeon = None; self.dungeon_def = None
        await self.broadcast_lobby()
```

E em `handle_select_dungeon` (Fase 1), nos DOIS ramos (procedural e autorado), limpar a campanha. Localizar dentro de `handle_select_dungeon` a linha `self.mode = "procedural"; self.selected_dungeon = None` e a linha `self.mode = "authored"; self.selected_dungeon = file` e, logo após cada uma, inserir:

```python
            self.campaign = None; self.campaign_phase = 0
```

- [ ] **Step 5: Campanhas no `broadcast_lobby`**

Em `server.py`, em `broadcast_lobby`, no dict do payload, após a linha `"dungeons": listar_dungeons(),` inserir:

```python
            "campaigns": listar_campanhas(),
```

- [ ] **Step 6: Rotear `select_campaign`**

Em `server.py`, no switch de mensagens, após o ramo `elif t == "select_dungeon":`, inserir:

```python
                elif t == "select_campaign":
                    if room: await room.handle_select_campaign(pid, msg.get("file"))
```

- [ ] **Step 7: Rodar e ver passar**

Run: `python tools/test_campanha.py`
Expected: PASS — bloco `[2]` verde, `0 falhou`.

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat: selecao de campanha no lobby (select_campaign) (Fase 4a)"
```

---

## Task 3: Carregar a fase atual em `enter_dungeon`

**Files:**
- Modify: `server.py` (`enter_dungeon`: carrega `dungeon_def` da fase + `autorada` estendido)
- Test: `tools/test_campanha.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
async def test_entrada_fase0():
    print("\n[3] enter_dungeon carrega a fase atual da campanha")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    r.phase = "city"
    await r.enter_dungeon("p1")
    check("carregou a fase 0 (grid 10×8 de camp_a)", r.map_w == 10 and r.map_h == 8)
    check("monstro da fase 0 (goblin)",
          sorted(m["type"] for m in r.monsters.values()) == ["goblin"])
    check("dungeon_def aponta a fase atual", r.dungeon_def is not None
          and r.dungeon_def.get("id") == "test_camp_a")
    check("objetivos da fase carregados", r.objectives
          and r.objectives["primary"]["type"] == "kill_all")
```

E em `main()`: `await test_entrada_fase0()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL no `[3]` — modo campaign não carrega; cai no procedural (grid 30×30).

- [ ] **Step 3: Carregar a fase + estender `autorada`**

Em `server.py`, em `enter_dungeon`, localizar:

```python
        nova = not self.dungeon_generated
        pids = list(self.players.keys())
        autorada = self.mode == "authored" and self.dungeon_def is not None
```

Substituir por:

```python
        nova = not self.dungeon_generated
        pids = list(self.players.keys())
        # Campanha: a 1ª entrada de cada fase carrega a masmorra da fase atual.
        if self.mode == "campaign" and self.campaign and nova:
            self.dungeon_def = carregar_dungeon(self.campaign["dungeons"][self.campaign_phase])
        autorada = self.mode in ("authored", "campaign") and self.dungeon_def is not None
```

> O resto de `enter_dungeon` já trata `autorada` (carrega via `load_authored_dungeon`, monta `door_rooms`, posiciona heróis pela `entrance` do `dungeon_def`, pula o spawn procedural). Nada mais a mudar aqui.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_campanha.py`
Expected: PASS — bloco `[3]` verde, `0 falhou`.

- [ ] **Step 5: Regressão**

Run: `python tools/test_objetivos.py` → `0 falhou`; `python tools/test_dungeon_loader.py` → `0 falhou`; `python tools/test_persistencia_masmorra.py` → `0 falhou` (procedural intacto).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat: enter_dungeon carrega a fase atual da campanha (Fase 4a)"
```

---

## Task 4: Avanço de fase + vitória final

**Files:**
- Modify: `server.py` (`_voltar_para_cidade` extraído; `handle_exit_dungeon` reusa; branch de avanço em `_check_objectives`)
- Test: `tools/test_campanha.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
async def test_avanco_e_vitoria():
    print("\n[4] avanço de fase, preservação e vitória final")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    r.phase = "city"
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]
    p1["gold"] = 99; p1["hp"] = max(1, p1["hp"] - 3); hp_antes = p1["hp"]
    # cumpre o objetivo da fase 0 (kill_all)
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("após concluir fase 0 → cidade", r.phase == "city")
    check("avançou para a fase 1", r.campaign_phase == 1)
    check("dungeon_generated zerado p/ carregar a próxima", r.dungeon_generated is False)
    check("HP preservado entre fases", r.players["p1"]["hp"] == hp_antes)
    check("ouro preservado entre fases", r.players["p1"]["gold"] == 99)

    # entra na fase 1
    await r.enter_dungeon("p1")
    check("fase 1 carregada (grid 12×8 de camp_b)", r.map_w == 12 and r.map_h == 8)
    check("monstro da fase 1 (skeleton)",
          sorted(m["type"] for m in r.monsters.values()) == ["skeleton"])

    # cumpre o objetivo da última fase → vitória da campanha
    vit = {"c": False, "v": None}
    async def fake_end(victory): vit["c"] = True; vit["v"] = victory
    r.end_game = fake_end
    for m in r.monsters.values(): m["hp"] = 0
    await r._check_objectives()
    check("última fase concluída → end_game(victory)", vit["c"] and vit["v"] is True)

async def test_retomar_mesma_fase():
    print("\n[5] sair sem concluir retoma a mesma fase")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    r.phase = "city"
    await r.enter_dungeon("p1")
    await r.handle_exit_dungeon("p1")     # sai sem concluir
    check("voltou à cidade", r.phase == "city")
    check("fase não avançou", r.campaign_phase == 0)
    await r.enter_dungeon("p1")
    check("retomou a fase 0 (10×8)", r.map_w == 10 and r.map_h == 8)
```

E em `main()`: `await test_avanco_e_vitoria()` e `await test_retomar_mesma_fase()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_campanha.py`
Expected: FAIL no `[4]` — concluir a fase 0 chama `end_game` em vez de avançar; `_voltar_para_cidade` inexistente.

- [ ] **Step 3: Extrair `_voltar_para_cidade` e reusar em `handle_exit_dungeon`**

Em `server.py`, SUBSTITUIR `handle_exit_dungeon` (~`server.py:6013`) inteiro por:

```python
    async def handle_exit_dungeon(self, pid):
        if self.phase != "playing": return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        await self.gm_say(f"🚪 **{p['name']}** usa as escadas de saída. Os aventureiros retornam à cidade!")
        await self._voltar_para_cidade()

    async def _voltar_para_cidade(self):
        """Transição masmorra→cidade reusável (saída pela escada e avanço de fase)."""
        self._cancelar_timer_turno()   # fora da masmorra não há timer de turno
        self.phase = "city"
        self._gerar_loja_pergaminhos()
        for pp in self.players.values():
            pp["moves_left"]        = pp["spd"]
            pp["action_done"]       = False
            pp["bonus_action_used"] = False
            pp["taverna_refeicoes"] = []   # refeições de balcão renovam a cada visita à cidade
        await self.broadcast_city_state()
```

- [ ] **Step 4: Branch de avanço em `_check_objectives`**

Em `server.py`, em `_check_objectives`, localizar o bloco de conclusão:

```python
            self._objetivo_concluido = True
            for s in secs:
                if self._objetivo_cumprido(s):
                    await self._conceder_bonus_secundario(s)
            await self.end_game(victory=True)
```

Substituir por:

```python
            self._objetivo_concluido = True
            for s in secs:
                if self._objetivo_cumprido(s):
                    await self._conceder_bonus_secundario(s)
            if (self.mode == "campaign" and self.campaign
                    and self.campaign_phase < len(self.campaign["dungeons"]) - 1):
                # Avança para a próxima fase via cidade/loja.
                self.campaign_phase += 1
                self.dungeon_generated = False     # próxima entrada carrega a nova fase
                self._objetivo_concluido = False   # a nova fase tem seus próprios objetivos
                await self.gm_say("🏆 Fase concluída! Retornem à cidade antes da próxima masmorra.")
                await self._voltar_para_cidade()
            else:
                await self.end_game(victory=True)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_campanha.py`
Expected: PASS — blocos `[4]` e `[5]` verdes, `0 falhou`.

- [ ] **Step 6: Regressão**

Run: `python tools/test_objetivos.py` → `0 falhou` (Fase 3: modo não-campanha ainda chama `end_game(victory)`); `python tools/test_persistencia_masmorra.py` → `0 falhou` (handle_exit_dungeon ainda funciona).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat: avanco de fase via cidade + vitoria final da campanha (Fase 4a)"
```

---

## Task 5: Serialização + cliente

**Files:**
- Modify: `server.py` (`push_state`/`broadcast_city_state` — campo `campaign`)
- Modify: `src/gameState.js`
- Modify: `game.js`
- Test: `tools/test_campanha.py`

- [ ] **Step 1: Campo `campaign` no `push_state` e `city_state`**

Em `server.py`, definir um helper de payload e usá-lo nos dois broadcasts. Inserir como método de `GameRoom` (perto de `push_state`):

```python
    def _campaign_payload(self):
        if self.mode == "campaign" and self.campaign:
            return {"name": self.campaign.get("name"),
                    "phase": self.campaign_phase + 1,
                    "total": len(self.campaign["dungeons"])}
        return None
```

No dict do `push_state` (após `"stairs_pos": self.stairs_pos,`) e no dict do `broadcast_city_state` (após `"host": self.host_pid,`), inserir:

```python
            "campaign": self._campaign_payload(),
```

- [ ] **Step 2: Teste de serialização**

Adicionar a `tools/test_campanha.py` (e chamar em `main()`):

```python
async def test_serializacao():
    print("\n[6] push_state expõe campaign")
    r = setup_room(); r.phase = "lobby"
    await r.handle_select_campaign("p1", "test_campanha.json")
    cap = {}
    async def capb(msg):
        if msg.get("type") == "game_state": cap.update(msg)
    r.broadcast = capb
    r.phase = "city"; await r.enter_dungeon("p1")
    await GameRoom.push_state(r)
    check("game_state traz campaign", cap.get("campaign") is not None)
    check("campaign phase/total corretos",
          cap["campaign"]["phase"] == 1 and cap["campaign"]["total"] == 2)
```

E em `main()`: `await test_serializacao()`. Rodar: `python tools/test_campanha.py` → `0 falhou`.

- [ ] **Step 3: Commit do servidor**

```bash
git add server.py tools/test_campanha.py
git commit -m "feat: serializa campaign (fase/total) no game_state/city_state (Fase 4a)"
```

- [ ] **Step 4: `gameState.js` — getters/sender**

Localizar o padrão dos getters/senders da Fase 1/3:
`python -c "[print(i+1,l.rstrip()) for i,l in enumerate(open('src/gameState.js',encoding='utf-8')) if 'lobbyDungeons' in l or 'selectDungeon' in l or 'function objectives' in l or 'get objectives' in l][:10]"`

Os campos `campaign` (em `gameState`) e `campaigns` (em `lobbyState`) já chegam nas mensagens. Adicionar, no MESMO estilo dos getters existentes (property getters) e do sender `selectDungeon` (função):

```javascript
  function campaign()       { return (gameState && gameState.campaign) || null; }
  function lobbyCampaigns() { return (lobbyState && lobbyState.campaigns) || []; }
  function selectCampaign(file) { send({ type: 'select_campaign', file: file || null }); }
```

Expor `campaign`/`lobbyCampaigns` como property getters e `selectCampaign` como função no objeto público `GS` (onde `selectDungeon`/`objectives` são expostos), seguindo o estilo do arquivo.

- [ ] **Step 5: `game.js` — dropdown, indicador e botão**

Editar `game.js` pelo tool de Edit (regra do projeto). Localizar o dropdown de masmorras do lobby e o HUD:
`python -c "[print(i+1,l.rstrip()) for i,l in enumerate(open('game.js',encoding='utf-8')) if 'cs-dungeon-select' in l or 'lobbyDungeons' in l or 'objectives-hud' in l or 'btn-enter-dungeon' in l][:15]"`

1. **Grupo "Campanhas" no dropdown do lobby:** onde as opções de masmorra são montadas (de `GS.lobbyDungeons`), acrescentar um `<optgroup label="Campanhas">` com `GS.lobbyCampaigns()`, usando `value="campaign:<file>"`. No `onchange`, se o valor começa com `campaign:`, chamar `GS.selectCampaign(file)`; senão, `GS.selectDungeon(...)` como hoje (e `selectCampaign(null)` ao escolher Procedural, para limpar a campanha).
2. **Indicador "Fase N de M":** quando `GS.campaign()` existe, mostrar perto do HUD de objetivos um texto `Fase ${c.phase} de ${c.total} — ${c.name}`. Esconder caso contrário.
3. **Botão "Entrar na próxima fase":** na cidade, quando `GS.campaign()` existe, o botão de entrar na masmorra (`#btn-enter-dungeon`) deve exibir `▶ Entrar na fase ${c.phase}` (ou "Entrar na próxima fase"); senão, o texto atual. Re-render junto do estado.

- [ ] **Step 6: Commit do cliente**

```bash
git add src/gameState.js game.js
git commit -m "feat: campanhas no lobby + indicador de fase + botao no cliente (Fase 4a)"
```

---

## Task 6: Verificação ponta-a-ponta no navegador

**Files:** nenhum (verificação com preview_* tools).

- [ ] **Step 1: Subir o servidor** (`python server.py`), abrir `http://localhost:8765/index.html`.

- [ ] **Step 2: Fluxo de campanha (via socket de teste, como na Fase 1/3):** `create_room` → `select_campaign test_campanha.json` → `select_class` → `start_game` → `enter_dungeon`. Verificar `game_state.campaign` = `{phase:1,total:2}`, grid 10×8. Matar o monstro (atacar) → confirmar transição para `city_state` com `campaign.phase=2` e HP/ouro preservados → `enter_dungeon` → fase 1 (12×8) → concluir → `game_over victory`.

- [ ] **Step 3: UI:** abrir o jogo, confirmar o grupo "Campanhas" no dropdown do lobby, o indicador "Fase N de M" no HUD e o botão de próxima fase na cidade. Console sem erros. Screenshot.

- [ ] **Step 4: Regressão procedural/masmorra única:** procedural → sem `campaign` (null), boss-kill → vitória; masmorra única (Fase 1) → carrega normalmente.

- [ ] **Step 5: Parar o servidor e relatar evidências.**

---

## Self-Review (cobertura do spec)

- **campaigns/*.json + validação** → Task 1 (`carregar_campanha`/`validar_campanha`/`listar_campanhas` + fixtures).
- **Seleção no lobby (select_campaign) + campaigns no lobby_state** → Task 2.
- **Estado da sala (campaign/campaign_phase) + enter_dungeon carrega a fase + autorada estendido** → Tasks 2/3.
- **Avanço de fase via cidade + vitória final + `_voltar_para_cidade`** → Task 4.
- **Progressão (HP/ouro preservados)** → Task 4 (teste explícito).
- **Retomar mesma fase ao sair sem concluir** → Task 4.
- **Serialização (campaign) + cliente (dropdown/indicador/botão)** → Task 5.
- **Procedural/masmorra única intactos** → guardas `self.mode`/`self.campaign`; regressão em Tasks 3/4/6.

**Sem placeholders:** todo Step de servidor traz código completo; Steps de cliente trazem getters/sender concretos + âncoras de localização (game.js/gameState.js grandes).

**Consistência de nomes:** `CAMPAIGNS_DIR`, `carregar_campanha`, `validar_campanha`, `listar_campanhas`, `handle_select_campaign`, `self.campaign`, `self.campaign_phase`, `_voltar_para_cidade`, `_campaign_payload`; cliente `campaign`/`lobbyCampaigns`/`selectCampaign`; mensagem `select_campaign`; campo `campaign` (`{name,phase,total}`).
