# Tutorial por herói — Fase 1: motor de lições

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer uma `fala` autorada virar uma **lição** — dirigida a uma classe, com uma tarefa que o jogador precisa cumprir e uma porta que só abre depois disso.

**Architecture:** Três campos opcionais (`classe`, `ordem`, `tarefa`) em cada entrada de `falas` no arquivo da masmorra. Fala sem nenhum deles continua sendo a fala de hoje, byte-idêntica. O servidor deriva `self.licoes` na carga, roteia o balão por `send_to` em vez de `broadcast`, registra progresso **por jogador** (`p["licao_atual"]`, `p["licao_progresso"]`, `p["licoes_feitas"]`) e marca conclusão **por sala** (`self.licoes_feitas`, que é o que o portão de porta consulta). Sete verbos são disparados do caminho de sucesso dos handlers por um único helper, `_licao_evento`.

**Tech Stack:** Python 3 + `websockets` (servidor, `server.py`), JS vanilla (`game.js`, `src/gameState.js`, `tools/editor.js`), testes por script (`python tools/test_tutorial.py`, `node tools/test_tutorial_cliente.js`).

**Spec:** `docs/superpowers/specs/2026-09-04-tutorial-por-heroi-design.md`

**Convenções deste repositório que valem para todas as tarefas:**

- Rode tudo da raiz do projeto (`C:\Users\RICARDO\Desktop\jogo tabuleiro`).
- **Pare o servidor antes de gravar em `server.py` ou `game.js`.** Um servidor rodando trava a escrita no Windows (`OSError: Errno 22`), e um `node --check` depois de um write que falhou valida o arquivo ANTIGO — falso verde.
- **Nunca use `git add .` nem `git add -A`.** O diretório tem trabalho em andamento do autor. Adicione só os arquivos que a tarefa nomeia.
- Texto de conteúdo autoral (as lições do mapa) fica em **português**, sem passar pelo dicionário. Só rótulo de interface ganha chave `ui.*`.
- Números de linha mudam entre sessões (o autor edita em paralelo). **Ancore cada edição pelo trecho de código citado**, não por linha.

## Como commitar neste repositório (leia antes da primeira edição)

**O autor tem ~110 arquivos modificados e não commitados no diretório de trabalho.** Seis deles são justamente os que este plano toca: `server.py`, `game.js`, `src/gameState.js`, `tools/editor.js`, `src/lang/erros.js` e `src/lang/interface.js`. Um `git add server.py` varreria milhares de linhas do trabalho do autor para dentro do seu commit.

Para cada arquivo dessa lista, encene **apenas as suas linhas**:

```bash
# 1. ANTES de editar, guarde o arquivo como ele está agora (HEAD + WIP do autor):
cp server.py /tmp/antes_server.py

# 2. Edite normalmente.

# 3. Gere o patch só das SUAS mudanças e aplique-o ao índice:
git diff --no-index --diff-algorithm=histogram /tmp/antes_server.py server.py   | sed 's|/tmp/antes_server.py|a/server.py|; s|b/server.py|b/server.py|' > /tmp/meu_server.patch
git apply --cached --check /tmp/meu_server.patch && git apply --cached /tmp/meu_server.patch

# 4. CONFIRME que só as suas linhas entraram antes de commitar:
git diff --cached --stat
```

**Use `--diff-algorithm=histogram`, não `diff -u`.** O algoritmo LCS padrão do `diff` desalinha diante de blocos de código parecidos e inventa hunks fantasma — num arquivo de 34 mil linhas isso produziu ~150 linhas de diferença falsa que pareciam edição concorrente do autor. O histogram não faz isso.

Se o `git apply --cached --check` recusar o patch, **pare e reporte DONE_WITH_CONCERNS** — isso significa que o WIP do autor mexeu no contexto ao redor da sua edição, e forçar o commit corromperia o trabalho dele.

Arquivos que **você cria** (`tools/test_tutorial.py`, `tools/test_tutorial_cliente.js`, `dungeons/campo_de_treinamento.json`) não têm esse problema: `git add <arquivo>` neles é seguro.

Depois de commitar, confirme que o WIP do autor continua lá e fora do índice:

```bash
git status --porcelain server.py    # deve continuar mostrando " M server.py"
```

---

### Task 1: Fundação — o que é uma lição, e a validação dos campos novos

**Files:**
- Modify: `server.py` (constantes de módulo perto de `WALL/FLOOR/DOOR`; função `validar_dungeon`)
- Test: `tools/test_tutorial.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_tutorial.py` com o conteúdo completo abaixo. O cabeçalho segue o padrão das suítes do projeto (`tools/test_bardo_espec.py`).

```python
"""Tutorial por herói — Fase 1 (motor de lições). Roda da raiz: python tools/test_tutorial.py"""
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

def mapa_base(**extra):
    """Masmorra mínima válida: 6x6, uma sala, entrada e saída."""
    tiles = [[S.WALL]*6 for _ in range(6)]
    for y in range(1, 5):
        for x in range(1, 5):
            tiles[y][x] = S.FLOOR
    d = {
        "schema_version": 1, "id": "t", "name": "t",
        "grid": {"w": 6, "h": 6}, "tiles": tiles,
        "rooms": [{"id": 0, "x": 1, "y": 1, "w": 4, "h": 4,
                   "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": {"x": 4, "y": 4},
        "monsters": [], "chests": [], "traps": [], "decorations": [],
        "secret_passages": [], "falas": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }
    d.update(extra)
    return d

def licao(**kw):
    """Uma lição autorada, com os campos obrigatórios já preenchidos."""
    base = {"id": "lic_1", "pos": [2, 2], "falante": {"nome": "Mestre", "emoji": "🧙"},
            "texto": "Ande até a marca.", "trigger": {"tipo": "proximidade", "raio": 2},
            "classe": "warrior", "ordem": 1,
            "tarefa": {"tipo": "mover_ate", "alvo": [3, 3], "vezes": 1,
                       "texto_curto": "Ande até a marca"}}
    base.update(kw)
    return base


async def main():
    print("\n[1] Validação dos campos novos da lição")
    ok, _ = S.validar_dungeon(mapa_base(falas=[licao()]))
    check("lição bem formada passa", ok is True)

    ok, msg = S.validar_dungeon(mapa_base(falas=[licao(classe="druida")]))
    check("classe desconhecida é recusada", ok is False and "classe" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "dancar", "vezes": 1, "texto_curto": "x"})]))
    check("verbo desconhecido é recusado", ok is False and "tipo" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": ""})]))
    check("tarefa sem texto_curto é recusada", ok is False)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "encerrar_turno", "vezes": 0, "texto_curto": "x"})]))
    check("vezes menor que 1 é recusado", ok is False)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(id="a", ordem=1), licao(id="b", ordem=1)]))
    check("ordem duplicada na mesma classe é recusada", ok is False and "ordem" in msg)

    ok, _ = S.validar_dungeon(mapa_base(falas=[
        licao(id="a", ordem=1, classe="warrior"),
        licao(id="b", ordem=1, classe="mage")]))
    check("mesma ordem em classes diferentes passa", ok is True)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(trigger={"tipo": "manual"})]))
    check("lição com gatilho manual é recusada", ok is False and "manual" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "mover_ate", "alvo": [99, 99], "vezes": 1,
                      "texto_curto": "x"})]))
    check("alvo de mover_ate fora do grid é recusado", ok is False)

    ok, _ = S.validar_dungeon(mapa_base(falas=[
        {"id": "f", "pos": [2, 2], "falante": {"nome": "", "emoji": "🧙"},
         "texto": "oi", "trigger": {"tipo": "manual"}}]))
    check("fala comum sem os campos novos continua válida", ok is True)

    print(f"\n{'='*50}\n  {PASS} passaram, {FAIL} falharam\n{'='*50}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA. As checagens de recusa passam por acidente (o validador de hoje aceita tudo e devolve `ok=True`, então `ok is False` falha). Você deve ver `❌` em pelo menos: classe desconhecida, verbo desconhecido, tarefa sem texto_curto, vezes menor que 1, ordem duplicada, gatilho manual, alvo fora do grid.

- [ ] **Step 3: Escrever as constantes de módulo**

Em `server.py`, logo depois do bloco `WALL  = 0 / FLOOR = 1 / DOOR  = 2`, acrescente:

```python
# ── Tutorial: uma "lição" é uma fala com classe e/ou tarefa ───────────────
# Fala sem nenhum dos dois continua sendo a fala de NPC de sempre.
LICAO_CLASSES = ("warrior", "mage", "rogue", "cleric", "bard", "paladin")
LICAO_VERBOS  = ("mover_ate", "abrir_porta", "atacar", "matar",
                 "pegar_item", "equipar", "encerrar_turno")
# Verbos cujo alvo é uma casa [x,y]; nos demais o alvo é uma string
# (tipo do monstro, para atacar/matar; id do item, para pegar/equipar).
LICAO_VERBOS_CASA = ("mover_ate", "abrir_porta")


def _e_licao(fala):
    """True se esta fala autorada é uma lição de tutorial."""
    return bool(isinstance(fala, dict) and (fala.get("classe") or fala.get("tarefa")))
```

- [ ] **Step 4: Escrever a validação**

Em `server.py`, dentro de `validar_dungeon`, o laço que hoje é

```python
    for _f in (defn.get("falas") or []):
        if not isinstance(_f, dict):
            return False, "cada fala deve ser um objeto JSON."
        if not (_f.get("texto") or "").strip():
            return False, "fala com texto vazio."
        _tg = (_f.get("trigger") or {}).get("tipo")
        if _tg not in ("proximidade", "sala", "manual"):
            return False, f"fala com gatilho inválido: {_tg!r} (proximidade|sala|manual)."
        if not in_grid(_f.get("pos")):
            return False, f"fala em casa inválida: {_f.get('pos')}."
```

passa a ser (mantenha as quatro checagens existentes e acrescente o bloco depois delas, ainda dentro do mesmo `for`):

```python
    for _f in (defn.get("falas") or []):
        if not isinstance(_f, dict):
            return False, "cada fala deve ser um objeto JSON."
        if not (_f.get("texto") or "").strip():
            return False, "fala com texto vazio."
        _tg = (_f.get("trigger") or {}).get("tipo")
        if _tg not in ("proximidade", "sala", "manual"):
            return False, f"fala com gatilho inválido: {_tg!r} (proximidade|sala|manual)."
        if not in_grid(_f.get("pos")):
            return False, f"fala em casa inválida: {_f.get('pos')}."
        if not _e_licao(_f):
            continue
        # ── Lição de tutorial ──
        if _tg == "manual":
            return False, "lição de tutorial não aceita gatilho manual."
        _cls = _f.get("classe")
        if _cls is not None and _cls not in LICAO_CLASSES:
            return False, f"lição com classe inválida: {_cls!r}."
        if _f.get("ordem") is not None and not isinstance(_f["ordem"], int):
            return False, "ordem de lição deve ser um inteiro."
        _tar = _f.get("tarefa")
        if _tar is None:
            continue
        if not isinstance(_tar, dict):
            return False, "tarefa de lição deve ser um objeto JSON."
        if _tar.get("tipo") not in LICAO_VERBOS:
            return False, f"lição com tipo de tarefa inválido: {_tar.get('tipo')!r}."
        if not isinstance(_tar.get("vezes", 1), int) or _tar.get("vezes", 1) < 1:
            return False, "tarefa de lição precisa de vezes maior ou igual a 1."
        if not (_tar.get("texto_curto") or "").strip():
            return False, "tarefa de lição sem texto_curto."
        _alvo = _tar.get("alvo")
        if _alvo not in (None, "", []):
            if _tar["tipo"] in LICAO_VERBOS_CASA:
                if not in_grid(_alvo):
                    return False, f"alvo de {_tar['tipo']} fora do mapa: {_alvo}."
            elif not isinstance(_alvo, str):
                return False, f"alvo de {_tar['tipo']} deve ser um texto."

    _ordens_vistas = set()
    for _f in (defn.get("falas") or []):
        if not _e_licao(_f) or _f.get("ordem") is None:
            continue
        _chave = (_f.get("classe"), _f["ordem"])
        if _chave in _ordens_vistas:
            return False, (f"duas lições com a mesma ordem {_chave[1]} para "
                           f"{_chave[0] or 'todas as classes'}.")
        _ordens_vistas.add(_chave)
```

- [ ] **Step 5: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
```

Esperado: `0 falharam`, saída 0.

- [ ] **Step 6: Garantir que nada quebrou nas masmorras existentes**

```bash
python tools/test_modo_mestre.py
```

Esperado: mesmo número de `✅` de antes e `0 falharam` (as falas de NPC da seção [24] continuam válidas — nenhuma delas tem `classe` ou `tarefa`).

- [ ] **Step 7: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): a licao e uma fala com classe e tarefa, validada na carga

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Carga — `self.licoes`, `self.licoes_feitas` e os campos do jogador

**Files:**
- Modify: `server.py` (`GameRoom.__init__`, carga da masmorra, `make_player`)
- Test: `tools/test_tutorial.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_tutorial.py`, acrescente a fábrica de sala logo depois de `def licao(...)`:

```python
def sala(falas=None):
    """Sala em 'playing' com mapa 6x6, uma sala e as falas dadas já carregadas."""
    r = GameRoom("TEST")
    falas_msg = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "fala":
            falas_msg.append((pid, msg))
    async def cap_bcast(msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "fala":
            falas_msg.append((None, msg))
    r.gm_say = noop; r.push_state = noop; r._broadcast_dado = noop
    r.broadcast = cap_bcast; r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.map_w = 6; r.map_h = 6
    r.tiles = [[S.WALL]*6 for _ in range(6)]
    for y in range(1, 5):
        for x in range(1, 5):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 4, "h": 4, "role": "entrance",
                "locked": False, "doors": [], "cleared": True, "looted": True}]
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    r._carregar_licoes({"falas": falas or []})
    r._falas_msg = falas_msg
    return r

def heroi(r, pid="h1", classe="warrior", pos=(2, 2)):
    p = make_player(pid, "Herói", classe, 0)
    p["pos"] = list(pos); p["alive"] = True
    r.players[pid] = p
    return p
```

E acrescente a seção de teste antes do bloco de placar final:

```python
    print("\n[2] Carga das lições")
    r = sala([licao(id="a"), {"id": "f", "pos": [2, 2],
                              "falante": {}, "texto": "oi",
                              "trigger": {"tipo": "manual"}}])
    check("só a lição entra em self.licoes", [l["id"] for l in r.licoes] == ["a"])
    check("as duas continuam em self.falas", len(r.falas) == 2)
    check("licoes_feitas começa vazio", r.licoes_feitas == set())

    p = heroi(r)
    check("jogador nasce sem lição atual", p["licao_atual"] is None)
    check("jogador nasce com progresso vazio", p["licao_progresso"] == {})
    check("jogador nasce sem lições feitas", p["licoes_feitas"] == [])
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA com `AttributeError: 'GameRoom' object has no attribute '_carregar_licoes'`.

- [ ] **Step 3: Implementar a carga**

Em `server.py`, no `GameRoom.__init__`, ao lado da linha que já existe

```python
        self.falas = []            # Falas de NPC (marcadores autorados)
```

acrescente:

```python
        self.licoes = []           # Tutorial: falas que são lição (classe e/ou tarefa)
        self.licoes_feitas = set() # ids de lição cumpridos por qualquer herói
```

Ainda em `server.py`, acrescente o método logo **acima** de `async def _disparar_fala`:

```python
    def _carregar_licoes(self, defn):
        """Deriva as lições das falas autoradas. Chamado na carga da masmorra.
        Uma lição é uma fala com `classe` e/ou `tarefa` — as demais seguem
        sendo falas de NPC comuns e não entram aqui.

        O progresso de lição pertence à execução da masmorra, não à carreira do
        personagem: quem rejoga o tutorial recebe as lições de novo."""
        self.falas = [dict(f, disparada=False) for f in (defn.get("falas") or [])]
        self.licoes = [f for f in self.falas if _e_licao(f)]
        self.licoes_feitas = set()
        for p in self.players.values():
            p["licao_atual"] = None
            p["licao_progresso"] = {}
            p["licoes_feitas"] = []
```

E na carga da masmorra, substitua a linha

```python
        self.falas = [dict(f, disparada=False) for f in (defn.get("falas") or [])]
```

por

```python
        self._carregar_licoes(defn)
```

- [ ] **Step 4: Implementar os campos do jogador**

Em `server.py`, dentro de `make_player`, no mesmo dicionário onde já existem campos de runtime como `"technique_cooldowns": {}`, acrescente:

```python
        # ── Tutorial ── progresso é POR JOGADOR; a conclusão também entra em
        # room.licoes_feitas, que é o que o portão de porta consulta.
        "licao_atual": None,        # id da lição pendente (o painel do HUD lê daqui)
        "licao_progresso": {},      # {licao_id: vezes já feitas}
        "licoes_feitas": [],        # ids que ESTE jogador cumpriu (lista: vai no JSON)
```

- [ ] **Step 5: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
```

Esperado: `0 falharam`.

- [ ] **Step 6: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): carga das licoes e campos de progresso no jogador

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `_licao_evento` — o registro de progresso

**Files:**
- Modify: `server.py` (novos métodos perto de `_verificar_falas`)
- Test: `tools/test_tutorial.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tools/test_tutorial.py`, antes do placar:

```python
    print("\n[3] _licao_evento registra o progresso")
    r = sala([licao(id="a", tarefa={"tipo": "atacar", "alvo": "goblin",
                                    "vezes": 2, "texto_curto": "Ataque"})])
    p = heroi(r)
    p["licao_atual"] = "a"; p["licao_progresso"]["a"] = 0

    await r._licao_evento(p, "matar", alvo="goblin")
    check("verbo errado não conta", p["licao_progresso"]["a"] == 0)

    await r._licao_evento(p, "atacar", alvo="orc")
    check("alvo errado não conta", p["licao_progresso"]["a"] == 0)

    await r._licao_evento(p, "atacar", alvo="goblin")
    check("verbo e alvo certos contam", p["licao_progresso"]["a"] == 1)
    check("vezes=2 ainda não concluiu", p["licao_atual"] == "a")

    await r._licao_evento(p, "atacar", alvo="goblin")
    check("a segunda vez conclui", p["licao_atual"] is None)
    check("entrou nas feitas do jogador", "a" in p["licoes_feitas"])
    check("entrou nas feitas da sala", "a" in r.licoes_feitas)

    await r._licao_evento(p, "atacar", alvo="goblin")
    check("depois de concluída não conta mais", p["licao_progresso"]["a"] == 2)

    print("\n[3b] Alvo ausente aceita qualquer um")
    r = sala([licao(id="a", tarefa={"tipo": "atacar", "vezes": 1,
                                    "texto_curto": "Ataque"})])
    p = heroi(r)
    p["licao_atual"] = "a"; p["licao_progresso"]["a"] = 0
    await r._licao_evento(p, "atacar", alvo="qualquer_bicho")
    check("sem alvo na tarefa, qualquer alvo serve", "a" in p["licoes_feitas"])

    print("\n[3c] Alvo de casa compara coordenada")
    r = sala([licao(id="a", tarefa={"tipo": "mover_ate", "alvo": [3, 3],
                                    "vezes": 1, "texto_curto": "Ande"})])
    p = heroi(r)
    p["licao_atual"] = "a"; p["licao_progresso"]["a"] = 0
    await r._licao_evento(p, "mover_ate", alvo=[2, 3])
    check("casa errada não conta", p["licao_progresso"]["a"] == 0)
    await r._licao_evento(p, "mover_ate", alvo=[3, 3])
    check("casa certa conclui", "a" in p["licoes_feitas"])
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA com `AttributeError: 'GameRoom' object has no attribute '_licao_evento'`.

- [ ] **Step 3: Implementar**

Em `server.py`, logo depois do método `_carregar_licoes` que você criou na Task 2:

```python
    @staticmethod
    def _licao_alvo_ok(esperado, real):
        """Alvo da tarefa: ausente = qualquer um serve. Casa compara [x,y];
        o resto compara texto (tipo do monstro, id do item)."""
        if esperado in (None, "", []):
            return True
        if isinstance(esperado, (list, tuple)):
            return isinstance(real, (list, tuple)) and list(esperado) == list(real)
        return esperado == real

    async def _licao_concluir(self, p, lic):
        """Marca a lição como cumprida por este jogador e pela sala."""
        feitas = p.setdefault("licoes_feitas", [])
        if lic["id"] not in feitas:
            feitas.append(lic["id"])
        self.licoes_feitas.add(lic["id"])
        if p.get("licao_atual") == lic["id"]:
            p["licao_atual"] = None

    async def _licao_evento(self, p, verbo, alvo=None):
        """Registra progresso na lição pendente do jogador.

        Chamado do caminho de SUCESSO dos handlers — ação recusada não conta.
        Sem lição pendente, ou com verbo/alvo diferentes do esperado, é um
        no-op barato: fora de uma masmorra-tutorial não há lição nenhuma."""
        if not p or not self.licoes:
            return
        lic_id = p.get("licao_atual")
        if not lic_id:
            return
        lic = next((l for l in self.licoes if l["id"] == lic_id), None)
        tar = (lic or {}).get("tarefa") or {}
        if not lic or tar.get("tipo") != verbo:
            return
        if not self._licao_alvo_ok(tar.get("alvo"), alvo):
            return
        prog = p.setdefault("licao_progresso", {})
        prog[lic_id] = prog.get(lic_id, 0) + 1
        if prog[lic_id] >= int(tar.get("vezes", 1) or 1):
            await self._licao_concluir(p, lic)
```

- [ ] **Step 4: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
```

Esperado: `0 falharam`.

- [ ] **Step 5: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): _licao_evento registra progresso por jogador

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Disparo — por classe, uma vez por jogador, e na ordem

**Files:**
- Modify: `server.py` (`_disparar_fala`, `_verificar_falas`, `handle_disparar_fala`)
- Test: `tools/test_tutorial.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tools/test_tutorial.py`, antes do placar:

```python
    print("\n[4] Disparo da lição")
    r = sala([licao(id="a", classe="warrior", pos=[3, 3],
                    trigger={"tipo": "proximidade", "raio": 1},
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (3, 3))
    m = heroi(r, "h2", "mage", (3, 3))
    await r._verificar_falas(g, None)
    await r._verificar_falas(m, None)
    check("a lição chegou ao guerreiro", any(pid == "h1" for pid, _ in r._falas_msg))
    check("a lição NÃO chegou ao mago", not any(pid == "h2" for pid, _ in r._falas_msg))
    check("nada foi para broadcast", not any(pid is None for pid, _ in r._falas_msg))
    check("virou a lição atual do guerreiro", g["licao_atual"] == "a")
    check("o mago segue sem lição", m["licao_atual"] is None)

    n = len(r._falas_msg)
    await r._verificar_falas(g, None)
    check("não repete para o mesmo jogador", len(r._falas_msg) == n)

    print("\n[4b] Lição sem tarefa se conclui ao disparar")
    r = sala([licao(id="a", classe="warrior", pos=[3, 3],
                    trigger={"tipo": "proximidade", "raio": 1}, tarefa=None)])
    g = heroi(r, "h1", "warrior", (3, 3))
    await r._verificar_falas(g, None)
    check("sem tarefa não vira lição atual", g["licao_atual"] is None)
    check("sem tarefa já entra nas feitas", "a" in g["licoes_feitas"])

    print("\n[4c] A ordem segura a lição seguinte")
    r = sala([
        licao(id="a", classe="warrior", ordem=1, pos=[3, 3],
              trigger={"tipo": "proximidade", "raio": 5},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "1"}),
        licao(id="b", classe="warrior", ordem=2, pos=[3, 3],
              trigger={"tipo": "proximidade", "raio": 5},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "2"}),
    ])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("só a de ordem 1 disparou", g["licao_atual"] == "a")
    await r._licao_evento(g, "encerrar_turno")
    await r._verificar_falas(g, None)
    check("cumprida a 1, a 2 dispara", g["licao_atual"] == "b")

    print("\n[4d] Fala comum não regrediu")
    r = sala([{"id": "f", "pos": [3, 3], "falante": {"nome": "N", "emoji": "🧙"},
               "texto": "oi", "trigger": {"tipo": "proximidade", "raio": 5}}])
    g = heroi(r, "h1", "warrior", (2, 2))
    m = heroi(r, "h2", "mage", (2, 2))
    await r._verificar_falas(g, None)
    check("fala comum vai por broadcast", any(pid is None for pid, _ in r._falas_msg))
    check("fala comum marca disparada", r.falas[0].get("disparada") is True)
    n = len(r._falas_msg)
    await r._verificar_falas(m, None)
    check("fala comum não repete para o segundo herói", len(r._falas_msg) == n)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA em "a lição NÃO chegou ao mago", "nada foi para broadcast", "virou a lição atual do guerreiro" e nas seções [4b] e [4c] — hoje `_disparar_fala` faz broadcast para todos e ignora classe e ordem.

- [ ] **Step 3: Implementar**

Em `server.py`, substitua **todo** o método `_disparar_fala` e **todo** o método `_verificar_falas` por:

```python
    async def _disparar_fala(self, fala, p=None):
        """Exibe uma fala de NPC. Fala comum: broadcast, uma vez para a sala.
        Lição: chega só ao herói que a recebeu e entra no painel dele."""
        if not fala:
            return
        payload = {"type": "fala",
                   "falante": fala.get("falante") or {},
                   "texto": fala.get("texto", ""),
                   "pos": fala.get("pos")}
        if not _e_licao(fala):
            if fala.get("disparada"):
                return
            fala["disparada"] = True
            await self.broadcast(payload)
            return
        if p is None:
            return                      # lição sem destinatário não dispara
        p.setdefault("licao_progresso", {})[fala["id"]] = 0
        if fala.get("tarefa"):
            p["licao_atual"] = fala["id"]
        await self.send_to(p["id"], payload)
        if not fala.get("tarefa"):
            await self._licao_concluir(p, fala)   # lição que só explica

    def _licao_liberada(self, p, fala):
        """True se as lições da mesma classe com ordem menor já foram
        cumpridas POR ESTE jogador. Sem ordem, nada segura."""
        ordem = fala.get("ordem")
        if ordem is None:
            return True
        feitas = p.get("licoes_feitas") or []
        return all(outra["id"] in feitas
                   for outra in self.licoes
                   if outra.get("ordem") is not None
                   and outra["ordem"] < ordem
                   and outra.get("classe") == fala.get("classe"))

    def _fala_elegivel(self, p, fala):
        """Se esta fala pode disparar agora para este jogador."""
        if not _e_licao(fala):
            return not fala.get("disparada")
        if fala.get("classe") and fala["classe"] != p.get("class_id"):
            return False
        if fala["id"] in (p.get("licao_progresso") or {}):
            return False                     # já disparou para ele
        if fala.get("tarefa") and p.get("licao_atual"):
            return False    # uma tarefa pendente por vez: não sobrescreve o painel
        return self._licao_liberada(p, fala)

    async def _verificar_falas(self, p, entered):
        """Gatilhos automáticos de fala (proximidade + entrar na sala) após um passo."""
        for fala in list(getattr(self, "falas", [])):
            if not self._fala_elegivel(p, fala):
                continue
            trig = fala.get("trigger") or {}
            tipo = trig.get("tipo")
            pos = fala.get("pos")
            if tipo == "proximidade" and pos:
                raio = int(trig.get("raio", 2) or 2)
                if max(abs(p["pos"][0] - pos[0]), abs(p["pos"][1] - pos[1])) <= raio:
                    await self._disparar_fala(fala, p)
            elif tipo == "sala" and entered and pos:
                sala = player_room(self.rooms, pos[0], pos[1])
                if sala and sala["id"] == entered["id"]:
                    await self._disparar_fala(fala, p)
```

Em `handle_disparar_fala`, acrescente a guarda de que uma lição nunca é manual — logo depois da checagem `if (fala.get("trigger") or {}).get("tipo") != "manual": return`:

```python
        if _e_licao(fala):
            return          # lição não é disparada pelo mestre: ela é do herói
```

- [ ] **Step 4: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
```

Esperado: `0 falharam`.

- [ ] **Step 5: Confirmar que a fala de NPC do Modo Mestre não regrediu**

```bash
python tools/test_modo_mestre.py
```

Esperado: `0 falharam`. A seção [24] cobre proximidade, sala e manual de falas comuns.

- [ ] **Step 6: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): licao dispara por classe, uma vez por jogador, na ordem

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Os sete verbos nos handlers

**Files:**
- Modify: `server.py` (`handle_move`, `handle_open_door`, `handle_attack`, `_monster_dies`, `handle_take_from_chest`, `handle_pickup_item`, `handle_equip_from_bag`, `handle_end_turn`)
- Test: `tools/test_tutorial.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tools/test_tutorial.py`, antes do placar. As duas primeiras seções exercitam handlers de ponta a ponta; a terceira é uma varredura estática que prova que os outros cinco pontos de chamada existem — o padrão de varredura já usado em `tools/test_narracao.py`.

```python
    print("\n[5] handle_move dispara mover_ate")
    r = sala([licao(id="a", classe="warrior", pos=[1, 1],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa={"tipo": "mover_ate", "alvo": [3, 2], "vezes": 1,
                            "texto_curto": "Ande até a marca"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["moves_left"] = 6
    await r.handle_move("h1", 1, 0)
    check("mover até a casa alvo cumpre a lição", "a" in g["licoes_feitas"])

    print("\n[5b] handle_end_turn dispara encerrar_turno")
    r = sala([licao(id="a", classe="warrior", pos=[2, 2],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["moves_left"] = 6
    await r._verificar_falas(g, None)
    check("a lição está pendente", g["licao_atual"] == "a")
    async def _noop_adv(*a, **k): pass
    # Sem fila de iniciativa, handle_end_turn cai no bloco legado e divide por
    # len(self.player_order) — que é zero neste fixture. A fila ligada faz o
    # handler sair pelo caminho normal, depois do gancho da lição.
    r._advance_initiative = _noop_adv
    r.initiative_active = True
    await r.handle_end_turn("h1")
    check("encerrar o turno cumpre a lição", "a" in g["licoes_feitas"])

    print("\n[5c] Os outros cinco pontos de chamada existem")
    fonte = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
    for verbo in ("abrir_porta", "atacar", "matar", "pegar_item", "equipar"):
        check(f"server.py chama _licao_evento com {verbo}",
              f'_licao_evento(p, "{verbo}"' in fonte
              or f'_licao_evento(p_dor, "{verbo}"' in fonte
              or f'_licao_evento(_matador, "{verbo}"' in fonte)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA em "mover até a casa alvo cumpre a lição", "encerrar o turno cumpre a lição" e nas cinco checagens da [5c].

- [ ] **Step 3: Ligar `mover_ate` e `encerrar_turno`**

Em `server.py`, dentro de `handle_move`, a linha

```python
        await self._verificar_falas(p, entered)       # Falas de NPC: proximidade + sala
```

vira duas linhas — o evento vem **antes**, para que cumprir a lição atual libere a próxima da ordem no mesmo passo:

```python
        await self._licao_evento(p, "mover_ate", alvo=list(p["pos"]))
        await self._verificar_falas(p, entered)       # Falas de NPC: proximidade + sala
```

Em `handle_end_turn`, logo depois do bloco que cobra a Dor Constante:

```python
        p_dor = self.players.get(pid)
        if p_dor:
            await self._cobrar_dor_constante(p_dor)
            await self._licao_evento(p_dor, "encerrar_turno")
```

- [ ] **Step 4: Ligar `abrir_porta`**

Em `server.py`, dentro de `handle_open_door`, há **duas** saídas de sucesso. Em cada uma, acrescente a chamada imediatamente antes do `await self.push_state()`.

Primeira (porta sem sala trancada):

```python
            self.opened_doors.add((tx, ty))
            self.explored.add((tx, ty))
            await self.gm_say(T("narracao.abre_porta", nome=p["name"]))
            await self._licao_evento(p, "abrir_porta", alvo=[tx, ty])
            await self.push_state()
            return
```

Segunda (porta que destranca salas), logo depois de `await self._verificar_avistamento()`:

```python
        await self._verificar_avistamento()   # sala revelada → herói avista → combate
        await self._licao_evento(p, "abrir_porta", alvo=[tx, ty])
        await self.push_state()
```

- [ ] **Step 5: Ligar `atacar` e `matar`**

Em `server.py`, dentro de `handle_attack`, na ramificação do acerto, logo depois da linha

```python
                await self._reacoes_instrumento_apos_ataque(p, target, dmg)
```

acrescente:

```python
                await self._licao_evento(p, "atacar", alvo=target.get("type"))
```

Em `_monster_dies`, logo depois do bloco do Instinto de Sobrevivência do Minotauro (o `if instinto and cds.get(...)` que pode dar `return`), acrescente:

```python
        _matador = self.players.get(killer_pid)
        if _matador:
            await self._licao_evento(_matador, "matar", alvo=m.get("type"))
```

- [ ] **Step 6: Ligar `pegar_item` e `equipar`**

Em `server.py`, em `handle_take_from_chest`, o bloco final passa a ser (todas as saídas por falha já retornaram antes deste ponto, e `item` só está ligado quando `kind == "item"`):

```python
        else:
            return

        if kind == "item":
            await self._licao_evento(p, "pegar_item", alvo=item.get("id"))

        # Remove chest if empty
        if chest["gold"] <= 0 and not chest["items"]:
```

**`handle_take_all_from_chest` não precisa de gancho:** ele coleta chamando `handle_take_from_chest` item a item, então herda este.

Em `handle_pickup_item`, imediatamente antes do `await self.push_state()` final (`gi` continua ligado ao dicionário mesmo depois do `del`):

```python
        await self.gm_say(T("narracao.pegou_do_chao", heroi=p['name'], gi_item_name=nome_item(gi['item']), extra=extra))
        await self._licao_evento(p, "pegar_item", alvo=(gi["item"] or {}).get("id"))
        await self.push_state()
```

Em `handle_equip_from_bag`, o corpo passa a capturar o item **antes** de equipar (depois de equipado ele já saiu da bolsa):

```python
        p = self.players.get(pid)
        if not p or "bag" not in p:   # ainda no lobby: ficha incompleta
            return
        _bag = p.get("bag") or []
        _it = _bag[slot_index] if 0 <= slot_index < len(_bag) else None
        if not await self._executar_equip_from_bag(pid, slot_index):
            return                                   # validação falhou (erro já enviado)
        await self._licao_evento(p, "equipar", alvo=(_it or {}).get("id"))
        await self.push_state_or_city()
```

- [ ] **Step 7: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
```

Esperado: `0 falharam`.

- [ ] **Step 8: Confirmar que os handlers tocados não regrediram**

```bash
python tools/test_roteamento_itens.py
python tools/test_ground_items.py
python tools/test_modo_mestre.py
```

Esperado: `0 falharam` nas três.

- [ ] **Step 9: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): os sete verbos disparam do caminho de sucesso dos handlers

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: A porta que só abre com a lição cumprida

**Files:**
- Modify: `server.py` (carga de `door_conditions`, `_door_condition_satisfied`, `_door_condition_message`, `_serializar_condicoes_portas`, `validar_dungeon`)
- Modify: `src/lang/erros.js` (mensagem da recusa)
- Test: `tools/test_tutorial.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tools/test_tutorial.py`, antes do placar:

```python
    print("\n[6] Porta com condição de lição")
    r = sala([licao(id="a", classe="warrior",
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    r.tiles[3][4] = S.DOOR
    r.rooms.append({"id": 1, "x": 5, "y": 1, "w": 1, "h": 4, "role": "monster",
                    "locked": True, "doors": [[4, 3]], "cleared": True, "looted": True})
    r.door_rooms = {(4, 3): [1]}
    r.door_conditions = {(4, 3): {"type": "licao", "licao_id": "a"}}
    r.door_condition_activated = {(4, 3): set()}
    check("porta fechada antes da lição", r._door_condition_satisfied((4, 3)) is False)
    r.licoes_feitas.add("a")
    check("porta abre depois da lição", r._door_condition_satisfied((4, 3)) is True)
    check("serializa sem estourar", "4,3" in r._serializar_condicoes_portas())

    print("\n[6b] Validação da porta de lição")
    def mapa_porta(cond):
        d = mapa_base(falas=[licao(id="a")])
        d["tiles"][3][4] = S.DOOR
        d["rooms"][0]["doors"] = [[4, 3]]
        d["door_conditions"] = {"4,3": cond}
        return d
    ok, _ = S.validar_dungeon(mapa_porta({"type": "licao", "licao_id": "a"}))
    check("porta apontando para lição existente passa", ok is True)
    ok, msg = S.validar_dungeon(mapa_porta({"type": "licao", "licao_id": "zzz"}))
    check("licao_id inexistente é recusado", ok is False and "zzz" in msg)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA — `_door_condition_satisfied` cai no ramo `decor` e devolve `False` mesmo depois de `licoes_feitas.add("a")`; e a validação aceita `type: "licao"` sem conferir o id.

- [ ] **Step 3: Implementar a carga**

Em `server.py`, na carga de `door_conditions`, o `if/else` passa a ter três ramos:

```python
        self.door_conditions = {}
        for key, cond in (defn.get("door_conditions") or {}).items():
            dx, dy = (int(v) for v in key.split(","))
            if cond.get("type") == "item":
                self.door_conditions[(dx, dy)] = {"type": "item", "item_id": cond["item_id"]}
            elif cond.get("type") == "licao":
                self.door_conditions[(dx, dy)] = {"type": "licao",
                                                  "licao_id": cond.get("licao_id", "")}
            else:
                self.door_conditions[(dx, dy)] = {
                    "type": "decor",
                    "key_decor_ids": list(cond.get("key_decor_ids") or []),
                    "keys_mode": cond.get("keys_mode", "any"),
                }
```

- [ ] **Step 4: Implementar a checagem, a mensagem e a serialização**

Em `_door_condition_satisfied`, acrescente o ramo depois do de item:

```python
        if cond["type"] == "item":
            return self._grupo_tem_item(cond.get("item_id"))
        if cond["type"] == "licao":
            return cond.get("licao_id") in getattr(self, "licoes_feitas", set())
```

Em `_door_condition_message`:

```python
        if cond.get("type") == "licao":
            return T("erro.porta_exige_licao")
```

Em `_serializar_condicoes_portas`, o `if/else` vira:

```python
            if cond["type"] == "item":
                row["item_id"] = cond.get("item_id")
            elif cond["type"] == "licao":
                row["licao_id"] = cond.get("licao_id")
            else:
                row["key_decor_ids"] = list(cond.get("key_decor_ids") or [])
                row["keys_mode"] = cond.get("keys_mode", "any")
                row["activated_decor_ids"] = list(self.door_condition_activated.get((x, y), set()))
```

- [ ] **Step 5: Acrescentar a chave de idioma**

Em `src/lang/erros.js`, acrescente ao dicionário:

```javascript
  "erro.porta_exige_licao": {
    pt: "Esta porta só abre quando você cumprir a lição atual.",
    en: "This door only opens once you complete your current lesson."
  },
```

- [ ] **Step 6: Implementar a validação**

Em `server.py`, dentro de `validar_dungeon`, no laço de `door_conditions`, troque a linha do tipo permitido e acrescente o ramo. Antes do laço, monte o conjunto de ids de lição:

```python
    _licao_ids = {f.get("id") for f in (defn.get("falas") or [])
                  if _e_licao(f) and (f.get("tarefa"))}
    for key, cond in door_conditions.items():
        if not isinstance(key, str) or not re.fullmatch(r"\d+,\d+", key):
            return False, f"chave de condicao de porta invalida: {key!r}."
        dx, dy = (int(v) for v in key.split(","))
        if not in_grid([dx, dy]) or tile_at([dx, dy]) != DOOR:
            return False, f"condicao de abertura referencia uma casa que nao e porta: {key}."
        if not isinstance(cond, dict) or cond.get("type") not in ("item", "decor", "licao"):
            return False, f"condicao de porta invalida em {key}: use item, decor ou licao."
        if cond["type"] == "licao":
            if cond.get("licao_id") not in _licao_ids:
                return False, (f"porta {key} aponta para uma licao que nao existe ou "
                               f"nao tem tarefa: {cond.get('licao_id')!r}.")
        elif cond["type"] == "item":
            ...
```

Mantenha o resto do laço (`item` e `decor`) exatamente como está, apenas mudando o `if cond["type"] == "item":` para `elif cond["type"] == "item":` e o `else:` final para o ramo de `decor`.

- [ ] **Step 7: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
node tools/test_idioma_cliente.js
```

Esperado: `0 falharam` no primeiro; `0 falharam` no segundo (a chave nova tem `pt` e `en` com os mesmos parâmetros — nenhum, neste caso).

- [ ] **Step 8: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py src/lang/erros.js — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): door_conditions ganha o tipo licao

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: O bloco `tutorial` no `game_state`

**Files:**
- Modify: `server.py` (`_game_state_payload` e um método novo `_tutorial_payload`)
- Test: `tools/test_tutorial.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tools/test_tutorial.py`, antes do placar:

```python
    print("\n[7] Bloco tutorial do game_state")
    r = sala([])
    check("masmorra sem lição não manda bloco", r._tutorial_payload() is None)

    r = sala([licao(id="a", classe="warrior", ordem=1,
                    tarefa={"tipo": "atacar", "alvo": "goblin", "vezes": 3,
                            "texto_curto": "Ataque o boneco"}),
              licao(id="b", classe="mage", ordem=1,
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["licao_atual"] = "a"; g["licao_progresso"]["a"] = 1
    bloco = r._tutorial_payload()["por_classe"]["warrior"]
    check("mostra a lição atual", bloco["licao_id"] == "a")
    check("mostra o texto curto", bloco["texto_curto"] == "Ataque o boneco")
    check("mostra o progresso", bloco["feito"] == 1 and bloco["vezes"] == 3)
    check("total conta só as da classe", bloco["total"] == 1)
    check("mago sem herói na sala não aparece",
          "mage" not in r._tutorial_payload()["por_classe"])

    g["licao_atual"] = None; g["licoes_feitas"] = ["a"]
    bloco = r._tutorial_payload()["por_classe"]["warrior"]
    check("sem pendência, licao_id é nulo", bloco["licao_id"] is None)
    check("conta a concluída", bloco["concluidas"] == 1)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_tutorial.py
```

Esperado: FALHA com `AttributeError: 'GameRoom' object has no attribute '_tutorial_payload'`.

- [ ] **Step 3: Implementar**

Em `server.py`, acrescente o método logo antes de `_serializar_condicoes_portas`:

```python
    def _tutorial_payload(self):
        """Bloco `tutorial` do game_state — None fora de uma masmorra-tutorial.

        O game_state é um broadcast único, então o progresso vai chaveado por
        classe e cada cliente lê a entrada da própria. Como o servidor impede
        dois jogadores com a mesma classe na sala, classe = um jogador."""
        if not getattr(self, "licoes", None):
            return None
        por_classe = {}
        for p in self.players.values():
            cls = p.get("class_id")
            if not cls:
                continue
            lic = next((l for l in self.licoes if l["id"] == p.get("licao_atual")), None)
            tar = (lic or {}).get("tarefa") or {}
            por_classe[cls] = {
                "licao_id": lic["id"] if lic else None,
                "texto_curto": tar.get("texto_curto", ""),
                "feito": (p.get("licao_progresso") or {}).get(lic["id"], 0) if lic else 0,
                "vezes": int(tar.get("vezes", 1) or 1) if lic else 0,
                "concluidas": len(p.get("licoes_feitas") or []),
                "total": sum(1 for l in self.licoes
                             if not l.get("classe") or l["classe"] == cls),
            }
        return {"por_classe": por_classe}
```

Em `_game_state_payload`, ao lado da linha que já existe

```python
            "expected_party": self.expected_party,
```

acrescente:

```python
            "tutorial": self._tutorial_payload(),
```

- [ ] **Step 4: Rodar o teste e ver passar**

```bash
python tools/test_tutorial.py
```

Esperado: `0 falharam`.

- [ ] **Step 5: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: server.py — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial.py
git commit -m "feat(tutorial): game_state carrega o progresso das licoes por classe

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Cliente — `GS.licaoAtual()`

**Files:**
- Modify: `src/gameState.js`
- Test: `tools/test_tutorial_cliente.js` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_tutorial_cliente.js`. O padrão de carga (`eval` do arquivo com um `window` falso, capturando o `GS`) foi verificado neste repositório e devolve os 250 membros do módulo.

```javascript
// Lição do tutorial no cliente — roda da raiz: node tools/test_tutorial_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

function injetar(tutorial, classe = "warrior") {
  GS.injectPreviewState({
    type: "game_state", master_pid: "p1",
    players: [{ id: "p1", name: "G", class_id: classe, alive: true, pos: [1, 1] }],
    monsters: [], tiles: [[0]], rooms: [], explored: [], round: 1,
    tutorial,
  });
}

console.log("\n[1] licaoAtual devolve a lição da minha classe");
injetar({ por_classe: { warrior: { licao_id: "a", texto_curto: "Ataque o boneco",
                                   feito: 1, vezes: 3, concluidas: 2, total: 5 } } });
const lic = GS.licaoAtual();
check("achou a lição", lic && lic.licao_id === "a");
check("trouxe o texto curto", lic.texto_curto === "Ataque o boneco");
check("trouxe o progresso", lic.feito === 1 && lic.vezes === 3);

console.log("\n[2] Silêncio quando não há lição para mim");
injetar({ por_classe: { mage: { licao_id: "b", texto_curto: "x", feito: 0,
                                vezes: 1, concluidas: 0, total: 1 } } });
check("lição de outra classe não vaza", GS.licaoAtual() === null);

injetar({ por_classe: { warrior: { licao_id: null, texto_curto: "", feito: 0,
                                   vezes: 0, concluidas: 5, total: 5 } } });
check("sem pendência devolve null", GS.licaoAtual() === null);

injetar(null);
check("masmorra comum devolve null", GS.licaoAtual() === null);

console.log(`\n${"=".repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${"=".repeat(50)}`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
node tools/test_tutorial_cliente.js
```

Esperado: FALHA com `TypeError: GS.licaoAtual is not a function`.

- [ ] **Step 3: Implementar**

Em `src/gameState.js`, acrescente a função junto das outras leituras puras de estado (perto de `masterManual`):

```javascript
  // ── Tutorial ── Lição pendente do MEU herói, ou null. Leitura pura: o bloco
  // vem chaveado por classe porque game_state é um broadcast único.
  function licaoAtual() {
    if (!gameState || !gameState.tutorial) return null;
    const me = (gameState.players || []).find(p => p.id === myPid);
    if (!me || !me.class_id) return null;
    const lic = (gameState.tutorial.por_classe || {})[me.class_id];
    return (lic && lic.licao_id) ? lic : null;
  }
```

E exporte-a no objeto devolvido pelo módulo, ao lado de `masterManualMid`:

```javascript
    licaoAtual,
```

- [ ] **Step 4: Rodar o teste e ver passar**

```bash
node tools/test_tutorial_cliente.js
```

Esperado: `0 falharam`.

- [ ] **Step 5: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: src/gameState.js — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git add tools/test_tutorial_cliente.js
git commit -m "feat(tutorial): GS.licaoAtual le a licao pendente do meu heroi

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Cliente — o quadro da lição no HUD

**Files:**
- Modify: `game.js` (`renderMyPanel`)
- Modify: `src/lang/interface.js`
- Test: `tools/test_interface.py` (só rodar; o placar não pode subir)

- [ ] **Step 1: Acrescentar a chave de idioma**

Em `src/lang/interface.js`, acrescente:

```javascript
  "ui.hud.banner_licao": { pt: "LIÇÃO", en: "LESSON" },
```

- [ ] **Step 2: Escrever o quadro no HUD**

O spec falava num elemento `#licao-atual`. Ele vira um **banner dentro de `renderMyPanel`**, na mesma família visual dos banners de SACIADO, EXAUSTÃO e ÚLTIMO ESFORÇO: `renderMyPanel` já roda a cada `game_state`, é agnóstico de classe e não exige ponto de montagem novo. Menos código e sem risco de o quadro ficar preso quando a lição termina.

Em `game.js`, dentro de `renderMyPanel`, **imediatamente antes** do bloco que renderiza os banners de fome e sede (o `${(() => { const f = me.fome ?? 100, s = me.sede ?? 100;`), acrescente:

```javascript
    ${(() => {
      // Tutorial: a tarefa pendente fica sempre à vista, para ninguém ficar
      // perdido depois que o balão de fala some. `texto_curto` é conteúdo
      // autoral (português), então não passa por t().
      const lic = GS.licaoAtual();
      if (!lic) return '';
      const prog = lic.vezes > 1 ? ` (${lic.feito}/${lic.vezes})` : '';
      return `<div style="margin-top:4px; padding:5px 8px; background:rgba(240,200,103,0.12); border:1px solid #f0c86766; border-radius:3px; display:flex; align-items:center; justify-content:center; gap:8px; font-family:'Cinzel',serif;">
        <span style="color:#f0c867; font-weight:bold; font-size:.95rem;">⚑</span>
        <span style="color:#f0c867; font-size:.6rem; letter-spacing:1px;">${t('ui.hud.banner_licao')}</span>
        <span style="color:#e8d8a0; font-size:.62rem;">${_esc(lic.texto_curto)}${prog}</span>
      </div>`;
    })()}
```

- [ ] **Step 3: Verificar a sintaxe do arquivo**

```bash
node --check game.js
```

Esperado: sem saída (sintaxe válida). **Se o write anterior falhou por `OSError: Errno 22`, este comando valida o arquivo antigo e dá falso verde** — confirme que a sua edição está no arquivo antes de confiar:

```bash
grep -c "ui.hud.banner_licao" game.js
```

Esperado: `1`.

- [ ] **Step 4: Confirmar que o placar de interface não subiu**

```bash
python tools/test_interface.py
node tools/test_idioma_cliente.js
```

Esperado: `0 falharam` nos dois. O texto novo no `game.js` é `t('ui.hud.banner_licao')`, não um literal em português, então o placar não sobe.

- [ ] **Step 5: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: game.js src/lang/interface.js — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git commit -m "feat(tutorial): quadro da licao atual no HUD

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Editor — os campos da lição no painel da fala

**Files:**
- Modify: `tools/editor.js` (painel `k === "fala"`, `placeEntity`, serialização, carga, validação)

- [ ] **Step 1: Acrescentar o vocabulário no topo do módulo**

Em `tools/editor.js`, logo depois do bloco `const HERO_SPAWN_META = [...]`, acrescente:

```javascript
  // Tutorial: verbos que uma tarefa de lição pode cobrar. Espelha
  // LICAO_VERBOS no server.py — mudar um exige mudar o outro.
  const LICAO_VERBOS = [
    { v: "mover_ate", nome: "chegar a uma casa" },
    { v: "abrir_porta", nome: "abrir uma porta" },
    { v: "atacar", nome: "acertar um ataque" },
    { v: "matar", nome: "derrotar um monstro" },
    { v: "pegar_item", nome: "pegar um item" },
    { v: "equipar", nome: "equipar um item" },
    { v: "encerrar_turno", nome: "encerrar o turno" },
  ];
  const LICAO_VERBOS_CASA = new Set(["mover_ate", "abrir_porta"]);
```

- [ ] **Step 2: Estender o painel da fala**

Em `tools/editor.js`, no ramo `} else if (k === "fala") {`, substitua o `panel.innerHTML` e os handlers por:

```javascript
    } else if (k === "fala") {
      const tg = ref.trigger || (ref.trigger = { tipo: "proximidade", raio: 2 });
      const fal = ref.falante || (ref.falante = { nome: "", emoji: "🧙" });
      const tar = ref.tarefa || null;
      const ehCasa = tar && LICAO_VERBOS_CASA.has(tar.tipo);
      panel.innerHTML = `<b>💬 Fala / lição</b>
        <label>emoji do falante</label><input id="f-emoji" value="${(fal.emoji || "").replace(/"/g, "&quot;")}" maxlength="4" style="width:60px">
        <label>nome do falante</label><input id="f-nome" value="${(fal.nome || "").replace(/"/g, "&quot;")}" placeholder="(opcional)">
        <label>texto</label><textarea id="f-texto" rows="3" style="width:100%">${(ref.texto || "").replace(/</g, "&lt;")}</textarea>
        <label>gatilho</label><select id="f-tipo">
          <option value="proximidade"${tg.tipo === "proximidade" ? " selected" : ""}>proximidade (raio)</option>
          <option value="sala"${tg.tipo === "sala" ? " selected" : ""}>entrar na sala</option>
          <option value="manual"${tg.tipo === "manual" ? " selected" : ""}>manual (mestre)</option>
        </select>
        ${tg.tipo === "proximidade" ? `<label>raio (casas)</label><input id="f-raio" type="number" min="1" max="20" value="${tg.raio || 2}" style="width:60px">` : ""}
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>🎓 Lição de tutorial</b>
          <label>para a classe</label>
          <select id="f-classe">
            <option value=""${!ref.classe ? " selected" : ""}>todas as classes</option>
            ${HERO_SPAWN_META.map(h => `<option value="${h.id}"${ref.classe === h.id ? " selected" : ""}>${h.emoji} ${h.name}</option>`).join("")}
          </select>
          <label>ordem na trilha (vazio = sem ordem)</label>
          <input id="f-ordem" type="number" min="1" value="${ref.ordem ?? ""}" style="width:70px">
          <label><input type="checkbox" id="f-tem-tarefa"${tar ? " checked" : ""}> cobra uma tarefa</label>
          ${tar ? `
            <label>tarefa</label>
            <select id="f-tarefa-tipo">${LICAO_VERBOS.map(o => `<option value="${o.v}"${tar.tipo === o.v ? " selected" : ""}>${o.nome}</option>`).join("")}</select>
            <label>alvo ${ehCasa ? "(casa x,y — vazio = qualquer)" : "(tipo do monstro ou id do item — vazio = qualquer)"}</label>
            <input id="f-tarefa-alvo" value="${ehCasa ? (Array.isArray(tar.alvo) ? tar.alvo.join(",") : "") : (typeof tar.alvo === "string" ? tar.alvo : "")}" placeholder="${ehCasa ? "12,5" : "goblin"}">
            <label>vezes</label><input id="f-tarefa-vezes" type="number" min="1" value="${tar.vezes || 1}" style="width:70px">
            <label>texto curto (aparece no HUD)</label>
            <input id="f-tarefa-curto" value="${(tar.texto_curto || "").replace(/"/g, "&quot;")}" placeholder="Ataque o boneco de treino">
          ` : ""}
        </div>
        <div style="margin-top:8px;color:#8a7a5a;font-size:11px">Dispara uma vez por herói. Lição não aceita gatilho manual.</div>`;
      document.getElementById("f-emoji").onchange = e => { fal.emoji = e.target.value; render(); };
      document.getElementById("f-nome").onchange = e => { fal.nome = e.target.value; };
      document.getElementById("f-texto").onchange = e => { ref.texto = e.target.value; };
      document.getElementById("f-tipo").onchange = e => { tg.tipo = e.target.value; if (tg.tipo === "proximidade" && !tg.raio) tg.raio = 2; renderPanel(); };
      const fr = document.getElementById("f-raio");
      if (fr) fr.onchange = e => { tg.raio = Math.max(1, parseInt(e.target.value, 10) || 2); };
      document.getElementById("f-classe").onchange = e => { ref.classe = e.target.value || null; renderPanel(); };
      document.getElementById("f-ordem").onchange = e => {
        const n = parseInt(e.target.value, 10);
        ref.ordem = Number.isFinite(n) && n >= 1 ? n : null;
      };
      document.getElementById("f-tem-tarefa").onchange = e => {
        ref.tarefa = e.target.checked
          ? { tipo: "encerrar_turno", alvo: null, vezes: 1, texto_curto: "" }
          : null;
        renderPanel();
      };
      const tt = document.getElementById("f-tarefa-tipo");
      if (tt) tt.onchange = e => { ref.tarefa.tipo = e.target.value; ref.tarefa.alvo = null; renderPanel(); };
      const ta = document.getElementById("f-tarefa-alvo");
      if (ta) ta.onchange = e => {
        const v = e.target.value.trim();
        if (!v) { ref.tarefa.alvo = null; return; }
        ref.tarefa.alvo = LICAO_VERBOS_CASA.has(ref.tarefa.tipo)
          ? v.split(",").map(n => parseInt(n, 10) || 0).slice(0, 2)
          : v;
      };
      const tv = document.getElementById("f-tarefa-vezes");
      if (tv) tv.onchange = e => { ref.tarefa.vezes = Math.max(1, parseInt(e.target.value, 10) || 1); };
      const tc = document.getElementById("f-tarefa-curto");
      if (tc) tc.onchange = e => { ref.tarefa.texto_curto = e.target.value; };
    } else if (k === "room") {
```

- [ ] **Step 3: Nascer com os campos**

Em `tools/editor.js`, no `placeEntity`, a linha do caso `"fala"` passa a criar os campos novos como nulos:

```javascript
      case "fala": S.falas.push({ id: "fala_" + S.nextFalaId++, pos: [x, y], falante: { nome: "", emoji: "🧙" }, texto: "", trigger: { tipo: "proximidade", raio: 2 }, classe: null, ordem: null, tarefa: null }); break;
```

- [ ] **Step 4: Salvar e carregar**

Em `tools/editor.js`, a serialização de `falas` no `buildJSON` passa a levar os campos só quando existem — assim uma masmorra sem lição salva exatamente o mesmo JSON de antes:

```javascript
      falas: S.falas.map(f => {
        const tg = f.trigger || {};
        const t = { tipo: tg.tipo || "proximidade" };
        if (t.tipo === "proximidade") t.raio = tg.raio || 2;
        const out = { id: f.id, pos: f.pos.slice(), falante: { nome: (f.falante || {}).nome || "", emoji: (f.falante || {}).emoji || "" }, texto: f.texto || "", trigger: t };
        if (f.classe) out.classe = f.classe;
        if (f.ordem != null) out.ordem = f.ordem;
        if (f.tarefa && f.tarefa.tipo) out.tarefa = {
          tipo: f.tarefa.tipo,
          ...(f.tarefa.alvo != null && f.tarefa.alvo !== "" ? { alvo: f.tarefa.alvo } : {}),
          vezes: Math.max(1, parseInt(f.tarefa.vezes, 10) || 1),
          texto_curto: f.tarefa.texto_curto || "",
        };
        return out;
      }),
```

E a carga:

```javascript
    S.falas = (obj.falas || []).map((f, i) => {
      const tg = f.trigger || {};
      const tipo = ["proximidade", "sala", "manual"].includes(tg.tipo) ? tg.tipo : "proximidade";
      const trigger = { tipo };
      if (tipo === "proximidade") trigger.raio = Math.max(1, parseInt(tg.raio, 10) || 2);
      const tar = f.tarefa && f.tarefa.tipo ? {
        tipo: f.tarefa.tipo,
        alvo: f.tarefa.alvo ?? null,
        vezes: Math.max(1, parseInt(f.tarefa.vezes, 10) || 1),
        texto_curto: f.tarefa.texto_curto || "",
      } : null;
      return { id: f.id || ("fala_" + i), pos: f.pos.slice(), falante: { nome: (f.falante || {}).nome || "", emoji: (f.falante || {}).emoji || "🧙" }, texto: f.texto || "", trigger,
               classe: f.classe || null, ordem: f.ordem ?? null, tarefa: tar };
    });
```

- [ ] **Step 5: Validar no editor**

Em `tools/editor.js`, o laço de validação das falas passa a ser:

```javascript
    const ordensLicao = new Set();
    for (const f of S.falas) {
      if (isWall(f.pos)) e.push(`fala de NPC em parede: ${f.pos}`);
      if (!(f.texto || "").trim()) e.push("fala de NPC sem texto");
      const tipo = (f.trigger || {}).tipo;
      if (!["proximidade", "sala", "manual"].includes(tipo)) e.push(`fala de NPC com gatilho inválido: ${tipo}`);
      const ehLicao = !!(f.classe || f.tarefa);
      if (!ehLicao) continue;
      if (tipo === "manual") e.push(`lição ${f.id} não pode ter gatilho manual`);
      if (f.classe && !HERO_SPAWN_META.some(h => h.id === f.classe)) e.push(`lição ${f.id} com classe inválida: ${f.classe}`);
      if (f.ordem != null) {
        const chave = `${f.classe || ""}#${f.ordem}`;
        if (ordensLicao.has(chave)) e.push(`duas lições com a mesma ordem ${f.ordem} para ${f.classe || "todas as classes"}`);
        ordensLicao.add(chave);
      }
      if (f.tarefa) {
        if (!LICAO_VERBOS.some(o => o.v === f.tarefa.tipo)) e.push(`lição ${f.id} com tarefa inválida: ${f.tarefa.tipo}`);
        if (!(f.tarefa.texto_curto || "").trim()) e.push(`lição ${f.id} sem texto curto`);
        if (LICAO_VERBOS_CASA.has(f.tarefa.tipo) && f.tarefa.alvo && !Array.isArray(f.tarefa.alvo)) e.push(`lição ${f.id}: alvo deveria ser uma casa x,y`);
      }
    }
```

- [ ] **Step 6: Verificar a sintaxe**

```bash
node --check tools/editor.js
grep -c "LICAO_VERBOS" tools/editor.js
```

Esperado: sem saída no primeiro; `4` ou mais no segundo (prova que a edição está no arquivo).

- [ ] **Step 7: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: tools/editor.js — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git commit -m "feat(tutorial): editor autora classe, ordem e tarefa na fala

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: Editor — a porta condicionada a uma lição

**Files:**
- Modify: `tools/editor.js` (painel da porta e serialização de `door_conditions`)

- [ ] **Step 1: Acrescentar a opção no painel da porta**

Em `tools/editor.js`, no painel `🚪 Porta`, o `<select id="door-condition-type">` ganha uma opção e o corpo ganha o seletor de lição. Substitua o bloco do `select` e o `${condition?.type === "item" ...}` por:

```javascript
          <select id="door-condition-type">
            <option value="none"${!condition ? " selected" : ""}>Sem condição</option>
            <option value="item"${condition?.type === "item" ? " selected" : ""}>Item-chave</option>
            <option value="decor"${condition?.type === "decor" ? " selected" : ""}>Objeto-chave ativado</option>
            <option value="licao"${condition?.type === "licao" ? " selected" : ""}>Lição cumprida</option>
          </select>
          ${condition?.type === "licao" ? (() => {
            const licoes = S.falas.filter(f => f.tarefa && f.tarefa.tipo);
            if (!licoes.length) return '<small style="color:#d8a0a0">Crie primeiro uma fala com tarefa.</small>';
            return `<label>lição necessária</label><select id="door-condition-licao">${licoes.map(l => `<option value="${l.id}"${condition.licao_id === l.id ? " selected" : ""}>${l.id} — ${(l.tarefa.texto_curto || "").slice(0, 30)}</option>`).join("")}</select>`;
          })() : ""}
          ${condition?.type === "item" ? `<label>item necessário</label><select id="door-condition-item">${opt(keyItems, condition.item_id || "", o => o.v + " — " + o.name)}</select>` : ""}
```

E, nos handlers logo abaixo, o `onchange` do tipo passa a criar a condição de lição, mais o handler do novo `select`:

```javascript
      document.getElementById("door-condition-type").onchange = e => {
        if (e.target.value === "none") delete S.doorConditions[conditionKey];
        else if (e.target.value === "item") S.doorConditions[conditionKey] = { type: "item", item_id: keyItems[0]?.v || "" };
        else if (e.target.value === "licao") S.doorConditions[conditionKey] = { type: "licao", licao_id: (S.falas.find(f => f.tarefa && f.tarefa.tipo) || {}).id || "" };
        else S.doorConditions[conditionKey] = { type: "decor", key_decor_ids: [], keys_mode: "any" };
        renderPanel(); render();
      };
      const conditionLicao = document.getElementById("door-condition-licao");
      if (conditionLicao) conditionLicao.onchange = e => { S.doorConditions[conditionKey].licao_id = e.target.value; };
```

- [ ] **Step 2: Salvar e carregar a condição**

Em `tools/editor.js`, a serialização de `door_conditions` no `buildJSON`:

```javascript
      door_conditions: Object.fromEntries(Object.entries(S.doorConditions).map(([key, c]) => [key,
        c.type === "item" ? { type: "item", item_id: c.item_id || "" }
        : c.type === "licao" ? { type: "licao", licao_id: c.licao_id || "" }
        : { type: "decor", key_decor_ids: (c.key_decor_ids || []).slice(), keys_mode: c.keys_mode === "all" ? "all" : "any" }])),
```

E a carga, no laço `for (const [key, c] of Object.entries(obj.door_conditions || {}))`, acrescente o ramo antes do de `decor`:

```javascript
      else if (c.type === "licao" && typeof c.licao_id === "string") S.doorConditions[key] = { type: "licao", licao_id: c.licao_id };
```

- [ ] **Step 3: Validar a porta no editor**

Em `tools/editor.js`, no laço que valida `S.doorConditions`, acrescente:

```javascript
      if (c.type === "licao" && !S.falas.some(f => f.id === c.licao_id && f.tarefa && f.tarefa.tipo))
        e.push(`porta ${key} aponta para uma lição que não existe ou não tem tarefa`);
```

- [ ] **Step 4: Verificar a sintaxe**

```bash
node --check tools/editor.js
grep -c "door-condition-licao" tools/editor.js
```

Esperado: sem saída no primeiro; `3` no segundo.

- [ ] **Step 5: Commit**

```bash
# ARQUIVO COM WIP DO AUTOR: tools/editor.js — NÃO use `git add` nele.
# Encene só as suas linhas pela receita "Como commitar" no topo do plano.
git commit -m "feat(tutorial): editor condiciona a porta a uma licao cumprida

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: O mapa mínimo e a verificação no jogo

**Files:**
- Create: `dungeons/campo_de_treinamento.json`
- Test: verificação no app (o motor já está coberto pelas suítes)

Este mapa é a fatia vertical: átrio comum com quatro lições sem classe, um portão de lição, e a sala A do Guerreiro com duas lições de classe. As alas das outras cinco classes e as salas B–E entram nas Fases 2 e 3. O alvo de treino é um `goblin` — o `boneco_treino` chega na Fase 3.

- [ ] **Step 1: Escrever o mapa**

Crie `dungeons/campo_de_treinamento.json`:

```json
{
  "schema_version": 1,
  "id": "campo_de_treinamento",
  "name": "Campo de Treinamento",
  "ambiente": "masmorra",
  "saida_permitida": false,
  "start_mode": "hero_spawns",
  "grid": { "w": 20, "h": 12 },
  "tiles": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
  ],
  "rooms": [
    { "id": 0, "x": 1, "y": 1, "w": 6, "h": 6, "role": "entrance", "locked": false, "doors": [] },
    { "id": 1, "x": 13, "y": 1, "w": 6, "h": 6, "role": "monster", "locked": true, "doors": [[12, 3]] }
  ],
  "door_conditions": {
    "12,3": { "type": "licao", "licao_id": "atrio_04" }
  },
  "entrance": null,
  "hero_spawns": [
    { "class_id": "warrior", "pos": [2, 2], "room_id": 0 },
    { "class_id": "mage",    "pos": [3, 2], "room_id": 0 },
    { "class_id": "rogue",   "pos": [4, 2], "room_id": 0 },
    { "class_id": "cleric",  "pos": [2, 5], "room_id": 0 },
    { "class_id": "bard",    "pos": [3, 5], "room_id": 0 },
    { "class_id": "paladin", "pos": [4, 5], "room_id": 0 }
  ],
  "exit": { "x": 18, "y": 3 },
  "monsters": [
    { "type": "goblin", "pos": [16, 3], "room_id": 1, "boss": false, "target": false }
  ],
  "chests": [
    { "pos": [5, 5], "gold": 0, "items": [{ "id": "sword" }], "key_objective": false }
  ],
  "traps": [],
  "decorations": [],
  "secret_passages": [],
  "master_reinforcements": [],
  "expected_party": { "heroes": 1, "level": 1 },
  "prisoner": null,
  "materiais": {},
  "falas": [
    {
      "id": "atrio_01", "pos": [3, 3],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "Bem-vindo ao Campo de Treinamento. Comece andando: clique numa casa iluminada. Seu herói tem um número de passos por turno — quando eles acabam, só o próximo turno devolve.",
      "trigger": { "tipo": "proximidade", "raio": 9 },
      "ordem": 1,
      "tarefa": { "tipo": "mover_ate", "alvo": [5, 3], "vezes": 1, "texto_curto": "Ande até a marca à sua direita" }
    },
    {
      "id": "atrio_02", "pos": [5, 4],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "Naquele baú há uma espada. Fique ao lado dele e pegue o que tem dentro: todo item adquirido vai primeiro para a sua bolsa, não direto para a mão.",
      "trigger": { "tipo": "proximidade", "raio": 3 },
      "ordem": 2,
      "tarefa": { "tipo": "pegar_item", "alvo": "sword", "vezes": 1, "texto_curto": "Pegue a espada do baú" }
    },
    {
      "id": "atrio_03", "pos": [5, 4],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "Na bolsa a espada não serve de nada. Abra o inventário e equipe-a: equipar é ação livre, não custa o seu turno.",
      "trigger": { "tipo": "proximidade", "raio": 3 },
      "ordem": 3,
      "tarefa": { "tipo": "equipar", "alvo": "sword", "vezes": 1, "texto_curto": "Equipe a espada" }
    },
    {
      "id": "atrio_04", "pos": [6, 3],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "O combate é por turnos. Quando terminar o que quer fazer, encerre o turno e deixe os outros agirem. Encerre o seu agora — a porta ao fundo destranca em seguida.",
      "trigger": { "tipo": "proximidade", "raio": 2 },
      "ordem": 4,
      "tarefa": { "tipo": "encerrar_turno", "vezes": 1, "texto_curto": "Encerre o seu turno" }
    },
    {
      "id": "atrio_05", "pos": [11, 3],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "Portas trancadas se abrem com um clique quando você está ao lado delas. Abrir é de graça: não gasta movimento nem ação.",
      "trigger": { "tipo": "proximidade", "raio": 2 },
      "ordem": 5,
      "tarefa": { "tipo": "abrir_porta", "alvo": [12, 3], "vezes": 1, "texto_curto": "Abra a porta ao fundo" }
    },
    {
      "id": "guerreiro_01", "pos": [14, 3],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "Todo ataque rola 1d20 e soma o seu acerto contra a Classe de Armadura do alvo. Empatar ou passar acerta; abaixo disso, erra. Ataque aquela criatura e observe o dado.",
      "trigger": { "tipo": "proximidade", "raio": 3 },
      "classe": "warrior",
      "ordem": 1,
      "tarefa": { "tipo": "atacar", "alvo": "goblin", "vezes": 1, "texto_curto": "Acerte um ataque na criatura" }
    },
    {
      "id": "guerreiro_02", "pos": [14, 3],
      "falante": { "nome": "Mestre de Armas", "emoji": "🛡️" },
      "texto": "Um acerto raramente basta. Continue até derrubá-la — e repare que um 20 natural dobra o dano.",
      "trigger": { "tipo": "proximidade", "raio": 3 },
      "classe": "warrior",
      "ordem": 2,
      "tarefa": { "tipo": "matar", "alvo": "goblin", "vezes": 1, "texto_curto": "Derrote a criatura" }
    }
  ],
  "objectives": {
    "primary": { "type": "all_heroes_at_exit", "xp": 0, "reward": { "gold": 0, "items": [] } },
    "secondary": []
  }
}
```

- [ ] **Step 2: Validar o mapa pelo próprio validador do servidor**

```bash
python -c "import json,sys; sys.path.insert(0,'.'); import server as S; print(S.validar_dungeon(json.load(open('dungeons/campo_de_treinamento.json',encoding='utf-8'))))"
```

Esperado: `(True, 'ok')`. Se vier `False`, a mensagem diz exatamente o que corrigir.

- [ ] **Step 3: Subir o servidor e jogar a fatia**

```bash
python server.py
```

Abra `http://localhost:8765/index.html`, crie uma sala, escolha o **Guerreiro**, e no lobby selecione a masmorra `campo_de_treinamento`. Confirme, na ordem:

1. O balão do Mestre de Armas aparece no primeiro passo, e o quadro `⚑ LIÇÃO — Ande até a marca à sua direita` fica no HUD.
2. Chegar em (5,3) apaga o quadro; andar até o baú traz a lição do item.
3. Pegar e equipar a espada avançam as lições.
4. **Antes** de encerrar o turno, tente abrir a porta em (12,3): tem de recusar com "Esta porta só abre quando você cumprir a lição atual."
5. Encerrar o turno destranca; abrir a porta cumpre a quinta lição.
6. Dentro da sala, as duas lições do Guerreiro aparecem — e **só** para o Guerreiro.
7. Derrotar o goblin e pisar na saída em (18,3) encerra a missão.

- [ ] **Step 4: Confirmar o roteamento por classe com dois clientes**

Com o servidor no ar, abra uma segunda aba, entre na mesma sala como **Mago** e repita o começo. Confirme que o Mago recebe as lições do átrio (que não têm classe) e **não** recebe nenhuma das duas do Guerreiro — nem o balão, nem o quadro no HUD.

- [ ] **Step 5: Rodar a bateria completa**

```bash
python tools/test_tutorial.py
node tools/test_tutorial_cliente.js
python tools/test_modo_mestre.py
python tools/test_roteamento_itens.py
python tools/test_interface.py
node tools/test_idioma_cliente.js
```

Esperado: `0 falharam` em todas.

- [ ] **Step 6: Commit**

```bash
git add dungeons/campo_de_treinamento.json
git commit -m "feat(tutorial): mapa minimo do Campo de Treinamento (atrio + ala do Guerreiro)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Dois bugs achados em revisão e já corrigidos (commit `1c222e1`)

**Uma tarefa pendente por vez.** Duas lições da mesma classe sem `ordem` que satisfizessem o gatilho no mesmo passo faziam a segunda sobrescrever `licao_atual`, e a primeira ficava órfã para sempre — invisível no painel e impossível de cumprir. `_fala_elegivel` passou a recusar uma lição com tarefa enquanto já há uma pendente. Com gatilho `proximidade` a segunda dispara no passo seguinte; com gatilho `sala`, ao reentrar.

**Recarregar a masmorra zera o progresso do jogador.** O estado de lição pertence à execução da masmorra, não à carreira do personagem. Sem isso, o tutorial revisitável da Fase 3 ficaria mudo na segunda visita, e dois mapas que reusassem um id de lição se atrapalhariam.

## Um desvio consciente do spec

O spec pedia que a validação recusasse "tarefa com `alvo` que não casa com nenhuma entidade do mapa". O plano valida **a forma** do alvo (casa dentro do grid para `mover_ate`/`abrir_porta`, texto para os demais), e **não** confere se o tipo de monstro ou o id de item existe. Motivo: os monstros autorados não têm id no arquivo, e tanto o catálogo de monstros quanto o de itens só ficam completos depois do merge dos personalizados no boot — uma checagem de existência dentro de `validar_dungeon` recusaria masmorra legítima que use conteúdo do editor. O erro de digitar `"gobin"` aparece na hora de jogar, com a lição que não avança, e é barato de achar.

## O que a Fase 1 deixa de fora, de propósito

- Os verbos de kit, sobrevivência e perigo, e o campo `efeito` que zera fome e sede — **Fase 2**.
- As salas B a E do Guerreiro e as outras cinco alas — **Fases 2 e 3**.
- O monstro `boneco_treino` — **Fase 3**; a Fase 1 treina num `goblin`.
- O ponto na cidade e o destino revisitável — **Fase 3**; até lá a masmorra é escolhida no lobby.
- A lista de progresso com todas as lições da ala; o HUD mostra só a atual.
