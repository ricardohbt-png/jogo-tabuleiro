# Solo com grupo (1 a 6 heróis) — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No jogo salvo Solo, o jogador marca de 1 a 6 classes na tela de seleção e controla todos esses heróis numa só conexão.

**Architecture:** "Heróis por procuração": o 1º herói tem o pid da conexão; os demais são entradas completas de `self.players` com pid próprio (`new_id()`) e o campo `controlador` = pid da conexão. Um resolvedor único na entrada do `handler` (`GameRoom.heroi_da_acao`) escolhe qual herói executa cada mensagem; `send_to` entrega mensagens de herói extra na conexão do controlador. No cliente, `myPid` passa a ser o **herói em foco** e `connPid` a conexão.

**Tech Stack:** Python 3 + `websockets` (server.py), JS vanilla (src/gameState.js, game.js), testes Python dirigindo `server.handler` com WebSocket falso e testes node que carregam `src/gameState.js` com `eval`.

**Spec:** `docs/superpowers/specs/2026-10-01-solo-com-grupo-design.md`

---

## Antes de começar (obrigatório)

- **Trabalhe numa worktree** (`superpowers:using-git-worktrees`), branch `feat/solo-com-grupo` a partir do `master`. O checkout principal tem trabalho em andamento do autor em `server.py`, `game.js`, `src/gameState.js`, `src/lang/*.js` e `CLAUDE.md` — **nunca** faça `git add` de arquivo inteiro lá.
- **`server.py`, `game.js`, `src/gameState.js`, `src/lang/*.js` e `CLAUDE.md` estão em CRLF.** Use a ferramenta de edição (Edit). Script Python com `"\n"` dentro do texto procurado não casa. `sed -i` converte o arquivo para LF — não use.
- **Servidor rodando trava a escrita** de `server.py` no Windows (`OSError: Errno 22`). Pare o preview antes de editar.
- Os números de linha deste plano podem ter mudado; ache os trechos pelo nome da função.
- Rodar Python sempre da raiz da worktree: `python tools/<teste>.py`.

## Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `server.py` | helpers de procuração (`_conexao_de`, `_herois_da_conexao`, `_herois_extras_de`, `_eh_anfitriao`, `heroi_da_acao`, `_casca_extra`); `send_to`; `handler` (tradução + `finally`); `handle_select_party` + `_pode_montar_grupo_solo` + `_dono_grupo_solo`; `broadcast_lobby` (`grupo_solo`); `add_player`/`entrar_com_jogo_em_andamento` (Solo fechado); `start_game` + `_vincular_grupo_solo`; `_montar_heroi` (`controlador`); `_continuar_jogo_salvo` + `_recriar_grupo_solo`; `_retomar_masmorra` (manter `controlador`); `_conexao_toda_fora`/`_conexoes_fora` em `push_state`, `push_state_or_city`, `handle_exit_dungeon`, `_reentrar_masmorra`, `_em_cidade`; `religar_heroi` + `_religar_extras` + `_entrada_para_religar` |
| `src/gameState.js` | `connPid`, `meusHerois`, foco automático na vez, `focarHeroi`, `heroi` nas mensagens, sessão pelo `connPid`, `selectParty`, `setKnownSpells(ids, heroi)`, `cascaDaClasse`, `ehMeuHeroi`, `temGrupo` |
| `game.js` | seleção em modo grupo; cartões do HUD e da cidade focam o herói; câmera no foco; visão compartilhada forçada |
| `game.css` | marca "no grupo" na grade de seleção e "na vez" no cartão |
| `src/lang/erros.js`, `src/lang/interface.js` | chaves novas |
| `tools/test_solo_grupo.py` | **novo** — servidor, pelo `server.handler` real |
| `tools/test_solo_grupo_cliente.js` | **novo** — foco no cliente |
| `CLAUDE.md` | seção "Solo com grupo" + linha `select_party` no protocolo |

---

### Task 1: Helpers de procuração no servidor

**Files:**
- Modify: `server.py` (classe `GameRoom`, logo antes de `def _classe_vinculada`)
- Create: `tools/test_solo_grupo.py`

- [ ] **Step 1: Criar o arquivo de teste com a estrutura e a seção [0]**

Crie `tools/test_solo_grupo.py`:

```python
"""Solo com grupo (1 a 6 heróis numa conexão) — servidor.

Roda da raiz:  python tools/test_solo_grupo.py

Seções:
  [0] helpers de procuração (GameRoom direto, sem handler)
  [1] select_party no lobby
  [2] início: vínculo no jogo salvo, magias por herói, XP dividido
  [3] masmorra: a vez passa entre os heróis; ação alheia/fora da vez recusada
  [4] escada: herói fora só espera enquanto o grupo está dentro
  [5] queda e volta religam todos os heróis
  [6] Continuar na cidade recria o grupo
  [7] Continuar com foto da masmorra recria o grupo dentro dela
"""
import asyncio, json, os, sys, tempfile, shutil
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


class FakeWS:
    """Conexão falsa (modelo de test_handler_smoke). Itens do roteiro: dict
    (mensagem) ou callable (passo; pode ser async e devolver um dict)."""
    def __init__(self, roteiro):
        self.roteiro = list(roteiro); self.sent = []
    def __aiter__(self): return self
    async def __anext__(self):
        while self.roteiro:
            item = self.roteiro.pop(0)
            if callable(item):
                r = item()
                if asyncio.iscoroutine(r): r = await r
                if isinstance(r, dict): return json.dumps(r)
                continue
            return json.dumps(item)
        raise StopAsyncIteration
    async def send(self, data): self.sent.append(data)
    async def close(self, *a, **k): pass
    def msgs(self, tipo=None):
        out = []
        for raw in self.sent:
            try: d = json.loads(raw)
            except Exception: continue
            if tipo is None or d.get("type") == tipo: out.append(d)
        return out
    def erros(self): return [str(d.get("msg", "")) for d in self.msgs("error")]


SENHA = "senha longa 1"

def login(nome):
    return {"type": "login", "username": nome, "password": SENHA}

def txt(chave, lang="pt"):
    """Texto de uma chave de idioma, como o cliente recebe."""
    return S._t_render(S.T(chave), lang)

async def esperar(cond, timeout=8.0):
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        try:
            if cond(): return True
        except Exception:
            pass
        await asyncio.sleep(0.03)
    return False

def sala_do_jogo(sid):
    return next((r for r in S.rooms.values() if r.savegame_id == sid), None)

def limpar_salas():
    for k in list(S.rooms):
        S.rooms.pop(k, None)
    S.SAVEGAMES_IN_USE.clear()

def duas_magias(cls):
    return [k for k, m in S.GRIMORIO.items()
            if cls in m.get("classe", []) and m.get("circulo") == "primeiro"][:2]

def casca(sid, cls):
    r = sala_do_jogo(sid)
    return next((p["id"] for p in r.players.values() if p.get("class_id") == cls), None)


class WSFalso:
    """Só para a seção [0]: guarda o que o send_to entregou."""
    def __init__(self): self.sent = []
    async def send(self, data): self.sent.append(json.loads(data))


def secao_helpers():
    print("\n[0] helpers de procuração")
    r = S.GameRoom("TESTE0")
    r.players = {
        "c1": {"id": "c1", "name": "Ana", "class_id": "warrior"},
        "x1": {"id": "x1", "name": "Pedro", "class_id": "mage", "controlador": "c1"},
        "x2": {"id": "x2", "name": "Luccas", "class_id": "rogue", "controlador": "c1"},
        "c2": {"id": "c2", "name": "Bia", "class_id": "cleric"},
    }
    r.host_pid = "c1"
    check("_conexao_de: extra → controlador", r._conexao_de("x1") == "c1")
    check("_conexao_de: principal → ele mesmo", r._conexao_de("c1") == "c1")
    check("_herois_da_conexao: extras primeiro, principal por último",
          r._herois_da_conexao("c1") == ["x1", "x2", "c1"], r._herois_da_conexao("c1"))
    check("_herois_da_conexao: jogador sem grupo", r._herois_da_conexao("c2") == ["c2"])
    check("_eh_anfitriao: extra do anfitrião conta como anfitrião", r._eh_anfitriao("x1"))
    check("_eh_anfitriao: outro jogador não", not r._eh_anfitriao("c2"))
    check("heroi_da_acao: `heroi` próprio é aceito", r.heroi_da_acao("c1", {"heroi": "x2"}) == "x2")
    check("heroi_da_acao: `heroi` de outro controlador é recusado",
          r.heroi_da_acao("c2", {"heroi": "x1"}) is None)
    check("heroi_da_acao: `heroi` inexistente é recusado",
          r.heroi_da_acao("c1", {"heroi": "id_999999"}) is None)
    check("heroi_da_acao: sem `heroi` fora da masmorra → a própria conexão",
          r.heroi_da_acao("c1", {}) == "c1")
    r.phase = "playing"
    r.current_pid = lambda: "x2"   # simula a vez do herói extra
    check("heroi_da_acao: sem `heroi`, na vez de um extra meu → o extra",
          r.heroi_da_acao("c1", {}) == "x2")
    check("heroi_da_acao: a vez de um extra alheio não vale para outra conexão",
          r.heroi_da_acao("c2", {}) == "c2")
    casca_nova = r._casca_extra("c1", "paladin", ["x"])
    check("_casca_extra: controlador, nome do herói e magias",
          casca_nova["controlador"] == "c1" and casca_nova["name"] == "Richard"
          and casca_nova["magias_conhecidas"] == ["x"] and casca_nova["class_id"] == "paladin")


async def main():
    tmp = tempfile.mkdtemp()
    velha = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        for conta in ("solo1", "solo2", "solo3", "solo4", "solo5", "solo6", "intruso", "multi"):
            acc, e = await S.create_account(conta, SENHA)
            assert acc, e
        secao_helpers()
    finally:
        limpar_salas()
        S.LOJA = velha
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 62); print("  SOLO COM GRUPO — servidor"); print("=" * 62)
    asyncio.run(main())
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_conexao_de'`.

- [ ] **Step 3: Implementar os helpers**

Em `server.py`, logo **antes** de `def _classe_vinculada(self, conta):`, acrescente:

```python
    # ── Solo com grupo: heróis por procuração ─────────────────────────────
    # No Solo com grupo, UMA conexão controla vários heróis. O 1º herói tem o
    # pid da própria conexão; os demais têm pid próprio (new_id()) e
    # `controlador` = pid da conexão. Tudo que percorre self.players continua
    # igual; só a fronteira muda: quem age (heroi_da_acao, no handler) e para
    # onde vai a resposta (send_to).
    def _conexao_de(self, pid):
        """Pid da conexão que controla este herói (ele mesmo, se não é extra)."""
        return (self.players.get(pid) or {}).get("controlador") or pid

    def _herois_extras_de(self, conexao):
        return [q for q in self.players.values() if q.get("controlador") == conexao]

    def _herois_da_conexao(self, conexao):
        """Pids dos heróis desta conexão: extras primeiro, principal por último.
        A ordem importa na queda: o principal sai por último para o anfitrião
        não ser passado a um extra que ainda consta como conectado."""
        pids = [q["id"] for q in self._herois_extras_de(conexao)]
        if conexao in self.players:
            pids.append(conexao)
        return pids

    def _eh_anfitriao(self, pid):
        # Escrito sem "pid == self.host_pid" de propósito: a Task 2 troca esse
        # padrão em massa por chamadas a este método.
        return self.host_pid in (pid, self._conexao_de(pid))

    def heroi_da_acao(self, conexao, msg):
        """Herói que executa a mensagem desta conexão. None = recusada.
        1) `msg.heroi` de um herói desta conexão → ele;
        2) sem `heroi`, um extra desta conexão na vez (turno, servos, Último
           Esforço) → ele;
        3) senão a própria conexão (comportamento de sempre)."""
        pedido = msg.get("heroi") if isinstance(msg, dict) else None
        if pedido is not None:
            pedido = str(pedido)
            if pedido == conexao:
                return conexao
            if pedido in self.players and self.players[pedido].get("controlador") == conexao:
                return pedido
            return None
        vez_turno = self.current_pid() if self.phase == "playing" else None
        for vez in (vez_turno, self.animados_phase_pid, self.last_stand_pid):
            if (vez and vez != conexao and vez in self.players
                    and self.players[vez].get("controlador") == conexao):
                return vez
        return conexao

    def _casca_extra(self, conexao, cls, magias=None):
        """Casca de lobby de um herói extra (mesmo formato da casca comum)."""
        pid = new_id()
        return {"id": pid, "name": HERO_IDENTITIES.get(cls, CLASSES[cls]["name"]),
                "class_id": cls, "ready": True, "connected": True,
                "slot": len(self.players), "controlador": conexao,
                "magias_conhecidas": list(magias or [])}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py`
Expected: `=== 13 passaram, 0 falharam ===`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): helpers de procuração no servidor"
```

---

### Task 2: `send_to` entrega ao controlador; o handler traduz o herói

**Files:**
- Modify: `server.py` — `send_to`, `handler` (definição de `err`, topo do laço, após `t = msg.get("type")`, `finally`), todos os `pid != self.host_pid` / `pid == self.host_pid` da classe e o `start_scene` do handler
- Modify: `src/lang/erros.js`
- Test: `tools/test_solo_grupo.py`

- [ ] **Step 1: Teste do `send_to`**

Em `tools/test_solo_grupo.py`, acrescente ao fim de `secao_helpers()` (ela vira `async`):

Troque `def secao_helpers():` por `async def secao_helpers():` e, no `main`, `secao_helpers()` por `await secao_helpers()`. Acrescente ao fim da função:

```python
    ws_ana = WSFalso()
    r.connections = {"c1": ws_ana}
    S.LANG_BY_PID["c1"] = "en"
    await r.send_to("x1", {"type": "error", "msg": S.T("erro.nao_e_o_seu_turno")})
    check("send_to(extra) chega na conexão do controlador", len(ws_ana.sent) == 1)
    check("…no idioma do controlador",
          ws_ana.sent and ws_ana.sent[0]["msg"] == txt("erro.nao_e_o_seu_turno", "en"),
          ws_ana.sent)
    S.LANG_BY_PID.pop("c1", None)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: `❌ send_to(extra) chega na conexão do controlador`.

- [ ] **Step 3: `send_to` roteia pelo controlador**

Em `async def send_to(self, pid, msg):`, troque a primeira linha

```python
        ws = self.connections.get(pid)
```

por

```python
        ws = self.connections.get(pid)
        if not ws:
            # Solo com grupo: herói extra não tem conexão própria; a mensagem
            # vai para quem o controla, no idioma dessa conexão.
            dono = (self.players.get(pid) or {}).get("controlador")
            if dono and dono in self.connections:
                ws, pid = self.connections[dono], dono
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py`
Expected: `=== 15 passaram, 0 falharam ===`.

- [ ] **Step 5: Lista de mensagens da conexão**

Em `server.py`, logo **acima** de `async def handler(ws):`, acrescente:

```python
# Mensagens que falam pela CONEXÃO, não por um herói: nunca são traduzidas
# para um herói extra do Solo com grupo (ver GameRoom.heroi_da_acao).
MENSAGENS_DA_CONEXAO = frozenset({
    "set_lang", "login", "logout", "create_account", "create_savegame",
    "load_savegame", "list_savegames", "create_room", "join_room", "rejoin",
    "join_test_dungeon", "select_class", "select_party", "campaign_vote",
    "claim_role", "start_game", "select_dungeon", "select_campaign",
    "salvar_e_sair", "set_turn_timer", "set_visao_compartilhada",
    "set_atravessar_aliados", "start_scene",
})
_PREFIXOS_DA_CONEXAO = ("mestre_", "teste_", "upload_", "save_", "load_")
```

- [ ] **Step 6: Tradução no handler**

Em `async def handler(ws):`, troque

```python
    async def err(msg):
        await ws.send(json.dumps({"type": "error", "msg": msg},
                                 default=lambda o: _t_render(o, _lang_de(pid))))
```

por

```python
    # Solo com grupo: enquanto uma mensagem é despachada em nome de um herói
    # extra, `pid` aponta para ele e `_traduzido` guarda o pid da conexão.
    _traduzido = None

    async def err(msg):
        dono = _traduzido if _traduzido is not None else pid
        await ws.send(json.dumps({"type": "error", "msg": msg},
                                 default=lambda o: _t_render(o, _lang_de(dono))))
```

Logo depois de `async for raw in ws:`, como **primeira** linha do laço:

```python
            if _traduzido is not None:
                pid, _traduzido = _traduzido, None
```

Logo depois de `t = msg.get("type")` (antes do bloco `_ability_types`):

```python
            if (room and t not in MENSAGENS_DA_CONEXAO
                    and not str(t).startswith(_PREFIXOS_DA_CONEXAO)):
                ator = room.heroi_da_acao(pid, msg)
                if ator is None:
                    await err(T("erro.esse_heroi_nao_e_seu"))
                    continue
                if ator != pid:
                    _traduzido, pid = pid, ator
```

No `finally:` do handler, como **primeira** linha:

```python
        if _traduzido is not None:
            pid = _traduzido
```

- [ ] **Step 7: Checagens de anfitrião cientes do grupo**

Pare o servidor se estiver rodando. Rode da raiz (troca só linhas inteiras; preserva CRLF por ler/gravar em bytes):

```bash
python - <<'EOF'
import re
src = open("server.py", "rb").read()
antes = src
src = src.replace(b"pid != self.host_pid", b"not self._eh_anfitriao(pid)")
src = src.replace(b"pid == self.host_pid", b"self._eh_anfitriao(pid)")
src = src.replace(b"if room and pid == room.host_pid:", b"if room and room._eh_anfitriao(pid):")
print("trocas:", antes.count(b"pid != self.host_pid") + antes.count(b"pid == self.host_pid")
      + antes.count(b"if room and pid == room.host_pid:"))
open("server.py", "wb").write(src)
EOF
```

Expected: `trocas:` entre 14 e 16. Confira com `git diff --stat server.py` e `git diff server.py | grep "_eh_anfitriao"` que só foram tocadas comparações de anfitrião (`handle_select_dungeon`, `handle_select_campaign`, `_continuar_jogo_salvo`, `start_game`, `handle_story_complete`, `handle_scene_end`, `handle_set_turn_timer`, `handle_set_visao_compartilhada`, `handle_set_atravessar_aliados`, `handle_world_travel`, `handle_world_map_points`, `handle_world_adventure`, `handle_city_map_points`, `enter_dungeon`, `start_scene`). A definição de `_eh_anfitriao` (Task 1) não contém o padrão e não é tocada — confira com `grep -n "def _eh_anfitriao" -A3 server.py`.

- [ ] **Step 8: Chave de erro**

Em `src/lang/erros.js`, antes do `};` final (use Edit; arquivo CRLF), acrescente uma vírgula na entrada anterior e:

```js
  "erro.esse_heroi_nao_e_seu": {
    "en": "That hero isn't yours.",
    "pt": "Esse herói não é seu."
  }
```

- [ ] **Step 9: Rodar a suíte do grupo e as do laço de conexão**

Run: `python tools/test_solo_grupo.py && python tools/test_handler_smoke.py && python tools/test_continuar_jogo.py`
Expected: as três terminam com `0 falharam`.

- [ ] **Step 10: Commit**

```bash
git add server.py src/lang/erros.js tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): handler traduz o herói da ação; send_to entrega ao controlador"
```

---

### Task 3: `select_party` no lobby e Solo fechado

**Files:**
- Modify: `server.py` — novos `_pode_montar_grupo_solo`, `_dono_grupo_solo`, `handle_select_party`; `broadcast_lobby`; `add_player`; `entrar_com_jogo_em_andamento`; despacho no `handler`; `finally` do handler (lobby)
- Modify: `src/lang/erros.js`
- Test: `tools/test_solo_grupo.py`

- [ ] **Step 1: Teste da seção [1]**

Acrescente a `tools/test_solo_grupo.py` (antes de `async def main`):

```python
async def criar_solo(conta, nome_jogo, passos, play_mode="solo"):
    """Cria um jogo salvo, abre o lobby e roda `passos(caixa)` (lista de
    itens de roteiro) na MESMA conexão. Devolve (sid, ws)."""
    caixa = {}
    def criado():
        sg = next((d["savegame"] for d in caixa["ws"].msgs("savegame_created")), None)
        caixa["sid"] = sg and sg["id"]
        return {"type": "load_savegame", "id": caixa["sid"]}
    async def esperar_lobby():
        await esperar(lambda: caixa.get("sid") and sala_do_jogo(caixa["sid"]))
    roteiro = [login(conta),
               {"type": "create_savegame", "name": nome_jogo, "mode": "procedural",
                "play_mode": play_mode},
               lambda: asyncio.sleep(0.05), criado, esperar_lobby]
    caixa["ws"] = FakeWS(roteiro)
    caixa["ws"].roteiro.extend(passos(caixa))
    await S.handler(caixa["ws"])
    return caixa["sid"], caixa["ws"]

def pausa():
    return lambda: asyncio.sleep(0.03)


async def secao_lobby():
    print("\n[1] select_party monta o grupo no lobby")
    obs = {}
    def foto(rotulo):
        def f(caixa):
            r = sala_do_jogo(caixa["sid"])
            obs[rotulo] = {p["id"]: dict(p) for p in r.players.values()}
            obs[rotulo + "_lobby"] = caixa["ws"].msgs("lobby_state")[-1]
            obs["conexao"] = next(p["id"] for p in r.players.values() if not p.get("controlador"))
        return f
    sid, ws = await criar_solo("solo1", "Grupo", lambda c: [
        lambda: foto("antes")(c),
        {"type": "select_party", "classes": ["warrior", "mage", "rogue"]}, pausa(),
        lambda: foto("tres")(c),
        {"type": "select_party", "classes": ["warrior", "rogue"]}, pausa(),
        lambda: foto("dois")(c),
        {"type": "select_party", "classes": []}, pausa(),
        {"type": "select_party", "classes": ["dragao"]}, pausa(),
    ])
    check("lobby_state avisa que dá para montar grupo (grupo_solo)",
          obs["antes_lobby"].get("grupo_solo") is True, obs["antes_lobby"].get("grupo_solo"))
    tres = obs["tres"]
    extras = [p for p in tres.values() if p.get("controlador")]
    check("3 heróis no lobby, 2 extras", len(tres) == 3 and len(extras) == 2, list(tres.values()))
    check("extras controlados pela conexão",
          all(p["controlador"] == obs["conexao"] for p in extras))
    check("extras com nome do herói (Pedro, Luccas)",
          sorted(p["name"] for p in extras) == ["Luccas", "Pedro"])
    check("o lobby_state leva o `controlador`",
          sum(1 for p in obs["tres_lobby"]["players"] if p.get("controlador")) == 2)
    dois = obs["dois"]
    check("tirar o mago remove a casca dele",
          sorted(p.get("class_id") for p in dois.values()) == ["rogue", "warrior"])
    rogue_antes = next(q for q, p in tres.items() if p.get("class_id") == "rogue")
    check("o ladino continua com o mesmo pid", rogue_antes in dois)
    check("lista vazia é recusada", txt("erro.grupo_de_1_a_6_herois") in ws.erros(), ws.erros())
    check("classe inexistente sozinha também", ws.erros().count(txt("erro.grupo_de_1_a_6_herois")) == 2)
    check("a conexão do lobby caiu: os extras saíram junto",
          not sala_do_jogo(sid) or not any(p.get("controlador")
                                           for p in sala_do_jogo(sid).players.values()))
    limpar_salas()

    print("\n[1b] Multiplayer não monta grupo")
    _, ws_m = await criar_solo("multi", "Mesa", lambda c: [
        {"type": "select_party", "classes": ["warrior", "mage"]}, pausa()],
        play_mode="multiplayer")
    check("select_party recusado no Multiplayer",
          txt("erro.grupo_so_no_solo") in ws_m.erros(), ws_m.erros())
    limpar_salas()

    print("\n[1c] Solo com grupo é fechado para outra conta")
    caixa_dono = {}
    async def intruso_entra():
        await esperar(lambda: caixa_dono.get("pronto"))
        r = sala_do_jogo(caixa_dono["sid"])
        return {"type": "join_room", "name": "intruso", "code": r.code}
    async def dono_espera_intruso():
        caixa_dono["pronto"] = True
        await esperar(lambda: ws_intruso.msgs("error"), timeout=3)
    ws_intruso = FakeWS([login("intruso"), intruso_entra, pausa()])
    def passos_dono(c):
        caixa_dono.update(c)
        return [{"type": "select_party", "classes": ["warrior", "cleric"]}, pausa(),
                lambda: caixa_dono.update(sid=c["sid"]), dono_espera_intruso]
    await asyncio.gather(criar_solo("solo2", "Fechado", passos_dono), S.handler(ws_intruso))
    check("outra conta é recusada",
          txt("erro.jogo_solo_com_grupo_fechado") in ws_intruso.erros(), ws_intruso.erros())
    limpar_salas()
```

No `main`, depois de `await secao_helpers()`: `await secao_lobby()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: `❌ lobby_state avisa que dá para montar grupo (grupo_solo)` e as demais de [1].

- [ ] **Step 3: Helpers e handler do grupo**

Em `server.py`, logo depois de `_casca_extra` (Task 1), acrescente:

```python
    def _pode_montar_grupo_solo(self, pid):
        """Lobby de jogo salvo Solo, sem Mestre, só com esta conta na sala e
        ainda sem personagem vinculado: o anfitrião pode montar o grupo."""
        sg = self.savegame
        if (sg is None or self.phase != "lobby" or sg.get("has_master")
                or _savegame_play_mode(sg) != "solo" or not self._eh_anfitriao(pid)):
            return False
        p = self.players.get(pid)
        if not p or p.get("is_master") or p.get("controlador"):
            return False
        if any(q["id"] != pid and q.get("controlador") != pid for q in self.players.values()):
            return False
        conta = self.account_by_pid.get(pid)
        return bool(conta) and not self._classe_vinculada(conta)

    def _dono_grupo_solo(self):
        """Conta dona de um Solo com grupo (montado no lobby ou já vinculado),
        ou None. Num Solo com grupo outra conta não entra; um Solo de 1 herói
        continua aceitando quem chega (comportamento antigo)."""
        for q in self.players.values():
            if q.get("controlador"):
                return self.account_by_pid.get(q["controlador"])
        for conta, m in ((self.savegame or {}).get("members") or {}).items():
            if isinstance(m, dict) and len(m.get("class_ids") or []) > 1:
                return conta
        return None

    async def handle_select_party(self, pid, classes):
        """Solo com grupo: o anfitrião marca de 1 a 6 classes, e a escolha
        SUBSTITUI a anterior. O 1º herói fica na casca da conexão; os outros
        ganham casca própria (`_casca_extra`). Nada vai ao jogo salvo aqui — o
        vínculo é gravado no start_game (_vincular_grupo_solo)."""
        if not self._pode_montar_grupo_solo(pid):
            await self.send_to(pid, {"type": "error", "msg": T("erro.grupo_so_no_solo")})
            return
        lista = list(dict.fromkeys(c for c in (classes if isinstance(classes, list) else [])
                                   if isinstance(c, str) and c in CLASSES))
        if not 1 <= len(lista) <= 6:
            await self.send_to(pid, {"type": "error", "msg": T("erro.grupo_de_1_a_6_herois")})
            return
        principal = self.players[pid]
        if principal.get("class_id") in lista:
            lista.remove(principal["class_id"])
            lista.insert(0, principal["class_id"])
        else:
            principal["class_id"] = lista[0]
            principal["magias_conhecidas"] = []
        principal["ready"] = True
        extras = {q.get("class_id"): q["id"] for q in self._herois_extras_de(pid)}
        for cls, q in extras.items():
            if cls not in lista[1:]:
                self.players.pop(q, None)
        for cls in lista[1:]:
            if cls not in extras:
                nova = self._casca_extra(pid, cls)
                self.players[nova["id"]] = nova
        await self.broadcast_lobby()
```

- [ ] **Step 4: `grupo_solo` no lobby_state**

Em `broadcast_lobby`, no dict do `self.broadcast({...})`, logo depois de `"host": self.host_pid,`:

```python
            "grupo_solo": bool(self.host_pid and self._pode_montar_grupo_solo(self.host_pid)),
```

- [ ] **Step 5: Solo fechado**

Em `add_player`, logo depois do bloco do Mestre (o `if (self.savegame and self.savegame.get("has_master") ...): ... return True`) e antes de `heroes = sum(...)`:

```python
        dono = self._dono_grupo_solo()
        if dono and account != dono:
            await ws.send(json.dumps(
                {"type": "error", "msg": T("erro.jogo_solo_com_grupo_fechado")},
                default=lambda o: _t_render(o, _lang_de(pid))))
            return False
```

Em `entrar_com_jogo_em_andamento`, como primeiras linhas do corpo (depois da docstring):

```python
        dono = self._dono_grupo_solo()
        if dono and conta != dono:
            return False, T("erro.jogo_solo_com_grupo_fechado")
```

- [ ] **Step 6: Despacho e limpeza do lobby no handler**

No `handler`, logo depois do ramo `elif t == "select_class": ...`:

```python
                elif t == "select_party":
                    if room: await room.handle_select_party(pid, msg.get("classes"))
```

No `finally` do handler, dentro de `if pid in room.players and room.phase == "lobby":`, antes de `room.release_character(pid)`:

```python
                for extra in [q["id"] for q in room._herois_extras_de(pid)]:
                    room.players.pop(extra, None)
```

- [ ] **Step 7: Chaves de erro**

Em `src/lang/erros.js`, antes do `};` final:

```js
  "erro.grupo_so_no_solo": {
    "en": "A party of heroes can only be put together in a new Solo game.",
    "pt": "Só dá para montar um grupo de heróis num jogo Solo novo."
  },
  "erro.grupo_de_1_a_6_herois": {
    "en": "Pick from 1 to 6 different heroes.",
    "pt": "Escolha de 1 a 6 heróis diferentes."
  },
  "erro.jogo_solo_com_grupo_fechado": {
    "en": "This is a Solo game with a party: no one else can join.",
    "pt": "Este é um jogo Solo com grupo: ninguém mais pode entrar."
  }
```

- [ ] **Step 8: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py && python tools/test_continuar_jogo.py`
Expected: as duas com `0 falharam` (a [7] do `test_continuar_jogo`, jogador novo num Solo de 1 herói, continua passando).

- [ ] **Step 9: Commit**

```bash
git add server.py src/lang/erros.js tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): select_party no lobby; Solo com grupo fechado"
```

---

### Task 4: Início — vínculo no jogo salvo, magias por herói, ficha completa

**Files:**
- Modify: `server.py` — `_vincular_grupo_solo` (novo), `start_game`, `_montar_heroi`
- Test: `tools/test_solo_grupo.py`

- [ ] **Step 1: Teste da seção [2]**

Acrescente a `tools/test_solo_grupo.py`:

```python
def esperar_fase(caixa, fase):
    async def f():
        await esperar(lambda: sala_do_jogo(caixa["sid"]).phase == fase)
        await asyncio.sleep(0.05)
    return f

def montar_e_iniciar(classes, depois=lambda c: []):
    """Passos: monta o grupo, escolhe magias de mago/clérigo e inicia."""
    def passos(c):
        p = [{"type": "select_party", "classes": classes}, pausa()]
        for cls in classes:
            if cls in ("mage", "cleric"):
                p.append(lambda cls=cls: {"type": "set_known_spells", "ids": duas_magias(cls),
                                          "heroi": casca(c["sid"], cls)})
                p.append(pausa())
        p += [{"type": "start_game"}, esperar_fase(c, "city")]
        return p + depois(c)
    return passos


async def secao_inicio():
    print("\n[2] início: vínculo, magias por herói, XP dividido")
    obs = {}
    def antes_das_magias(c):
        return [{"type": "select_party", "classes": ["warrior", "mage", "rogue"]}, pausa(),
                {"type": "start_game"}, pausa()]
    _, ws0 = await criar_solo("solo3", "SemMagia", antes_das_magias)
    check("iniciar sem as magias do mago é recusado",
          txt("erro.magos_e_clerigos_devem_escolher_2_magias") in ws0.erros(), ws0.erros())
    limpar_salas()

    def olhar(c):
        def f():
            r = sala_do_jogo(c["sid"])
            obs["players"] = {p["id"]: dict(p) for p in r.players.values()}
            obs["xp"] = r._calc_monster_xp({"cr": 1})
        return [f]
    sid, ws = await criar_solo("solo4", "Trio", montar_e_iniciar(["warrior", "mage", "rogue"], olhar))
    ps = obs["players"]
    mago = next(p for p in ps.values() if p.get("class_id") == "mage")
    principal = next(p for p in ps.values() if not p.get("controlador"))
    check("3 heróis na cidade", len(ps) == 3, list(ps))
    check("o mago (extra) tem as magias escolhidas para ele",
          sorted(mago.get("magias_conhecidas") or [])[:2] == sorted(duas_magias("mage")),
          mago.get("magias_conhecidas"))
    check("os extras guardam o controlador após o start_game",
          sum(1 for p in ps.values() if p.get("controlador") == principal["id"]) == 2)
    check("city_state leva os 3 heróis", len(ws.msgs("city_state")[-1]["players"]) == 3)
    check("XP de monstro dividido por 3", obs["xp"][1] == 3, obs["xp"])
    sg = S.load_savegame(sid)
    m = sg["members"]["solo4"]
    check("jogo salvo: class_id é o principal", m.get("class_id") == "warrior", m)
    check("jogo salvo: class_ids guarda o grupo", m.get("class_ids") == ["warrior", "mage", "rogue"], m)
    check("jogo salvo: uma ficha por classe",
          all(c in sg.get("characters", {}) for c in ("warrior", "mage", "rogue")))
    check("jogo salvo: a ficha do mago tem as magias",
          sorted(sg["characters"]["mage"].get("magias_conhecidas") or [])[:2] == sorted(duas_magias("mage")))
    limpar_salas()
    return sid
```

No `main`, depois de `await secao_lobby()`: `sid_trio = await secao_inicio()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: falhas em [2] (`class_ids`, `controlador`, ficha do mago).

- [ ] **Step 3: `_vincular_grupo_solo`**

Em `server.py`, logo depois de `handle_select_party`:

```python
    def _vincular_grupo_solo(self, conexao):
        """1º início de um Solo montado pelo select_party: grava o grupo no
        jogo salvo. A conta fica com `class_id` (o principal — campo lido em
        todo lugar) e `class_ids` (o grupo, em ordem); cada classe ganha slot
        e ficha. As magias escolhidas no lobby entram pelo _montar_heroi."""
        conta = self.account_by_pid.get(conexao)
        principal = self.players.get(conexao) or {}
        if not conta or not principal.get("class_id"):
            return
        classes = [principal["class_id"]] + [q["class_id"] for q in self._herois_extras_de(conexao)]
        ensure_campaign_schema(self.savegame)
        self.savegame.setdefault("members", {})[conta] = {
            "class_id": classes[0], "class_ids": classes, "status": "active",
            "joined": _now_iso(), "hero_id": f"hero_{conta}_{classes[0]}"}
        register_campaign_member_in_group(self.savegame, conta)
        chars = self.savegame.setdefault("characters", {})
        for q in [principal] + self._herois_extras_de(conexao):
            cls = q["class_id"]
            self.savegame["slots"][cls] = _campaign_slot(cls, conta, "active")
            if cls not in chars:
                chars[cls] = snapshot_character(make_player(q["id"], q["name"], cls, q.get("slot", 0)))
        self.savegame.setdefault("journal", []).append({"at": _now_iso(), "kind": "member_joined",
            "text": f"{conta} montou o grupo: " + ", ".join(HERO_IDENTITIES.get(c, c) for c in classes)})
        write_savegame(self.savegame)
```

- [ ] **Step 4: Chamar no `start_game`**

Em `start_game`, logo **depois** do laço que recusa mago/clérigo sem 2 magias e **antes** de `full_players = {}`:

```python
        # Solo montado pelo select_party: o vínculo da conta é gravado agora.
        if self._pode_montar_grupo_solo(pid):
            self._vincular_grupo_solo(pid)
```

- [ ] **Step 5: `_montar_heroi` preserva o controlador**

Em `_montar_heroi`, logo antes de `return novo`:

```python
        if p.get("controlador"):
            novo["controlador"] = p["controlador"]   # Solo com grupo
```

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py`
Expected: `0 falharam`.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): start_game vincula o grupo ao jogo salvo"
```

---

### Task 5: Masmorra — vez por herói, ação alheia recusada, escada

**Files:**
- Modify: `server.py` — `_conexao_toda_fora`/`_conexoes_fora` (novos), `_em_cidade`, `push_state`, `push_state_or_city`, `handle_exit_dungeon`, `_reentrar_masmorra`
- Test: `tools/test_solo_grupo.py`

- [ ] **Step 1: Teste das seções [3] e [4]**

Acrescente a `tools/test_solo_grupo.py`:

```python
def na_masmorra(c):
    """Passos: entra na masmorra e libera a transição de 3 s."""
    async def liberar():
        r = sala_do_jogo(c["sid"])
        await esperar(lambda: r.phase == "playing")
        await r._liberar_intro_masmorra(True)
    return [{"type": "enter_dungeon"}, liberar, pausa()]


async def secao_masmorra():
    print("\n[3] masmorra: a vez passa entre os heróis")
    obs = {"vezes": [], "ultimo": None}

    def meus(r):
        return {p["id"] for p in r.players.values()}

    def roteiro(c):
        # Cada passo é uma função que ESPERA e DEVOLVE a próxima mensagem: o
        # FakeWS só entrega uma mensagem quando o passo anterior termina, então
        # não dá para mandar mensagens de dentro de um passo que ainda espera.
        async def fora_da_vez():
            r = sala_do_jogo(c["sid"])
            await esperar(lambda: r.current_pid() in meus(r), timeout=6)
            vez = r.current_pid()
            outro = next(q for q in meus(r) if q != vez)
            obs["vez"], obs["outro"] = vez, outro
            obs["pos_vez"] = list(r.players[vez]["pos"])
            obs["pos_outro"] = list(r.players[outro]["pos"])
            obs["arma_outro"] = (r.players[outro].get("gear") or {}).get("weapon")
            obs["chao_antes"] = len(r.ground_items)
            return {"type": "move", "dx": 1, "dy": 0, "heroi": outro}
        def conferir():
            r = sala_do_jogo(c["sid"])
            obs["pos_vez_depois"] = list(r.players[obs["vez"]]["pos"])
            obs["pos_outro_depois"] = list(r.players[obs["outro"]]["pos"])
        def largar():
            return {"type": "drop_item", "source": "gear", "slot_key": "weapon",
                    "heroi": obs["outro"]}
        def conferir_largar():
            r = sala_do_jogo(c["sid"])
            obs["chao_depois"] = len(r.ground_items)
            obs["arma_outro_depois"] = (r.players[obs["outro"]].get("gear") or {}).get("weapon")
        async def proxima_vez():
            # Espera a vez de um herói meu diferente do último, anota e o faz
            # encerrar o turno SEM `heroi` (regra 2 do heroi_da_acao).
            if len(obs["vezes"]) == 3:
                return None
            r = sala_do_jogo(c["sid"])
            ok = await esperar(lambda: r.current_pid() in meus(r)
                               and r.current_pid() != obs["ultimo"], timeout=6)
            if not ok:
                return None
            vez = r.current_pid()
            if vez not in obs["vezes"]:
                obs["vezes"].append(vez)
            obs["ultimo"] = vez
            return {"type": "end_turn"}
        def escada():
            r = sala_do_jogo(c["sid"])
            conexao = next(p["id"] for p in r.players.values() if not p.get("controlador"))
            extra = next(p for p in r.players.values() if p.get("controlador"))
            extra["fora_masmorra"] = {"rodadas_restantes": 2}
            obs["em_cidade_extra"] = r._em_cidade(extra["id"])
            obs["conexao_fora_um"] = conexao in r._conexoes_fora()
            for p in r.players.values():
                p["fora_masmorra"] = {"rodadas_restantes": 2}
            obs["em_cidade_todos"] = r._em_cidade(extra["id"])
            obs["conexao_fora_todos"] = conexao in r._conexoes_fora()
            for p in r.players.values():
                p.pop("fora_masmorra", None)
        return (na_masmorra(c)
                + [fora_da_vez, pausa(), conferir, largar, pausa(), conferir_largar]
                + [proxima_vez, pausa()] * 8
                + [escada])

    await criar_solo("solo5", "Masmorra", montar_e_iniciar(["warrior", "mage", "rogue"], roteiro))
    check("herói fora da vez não anda", obs["pos_outro_depois"] == obs["pos_outro"])
    check("e o da vez também não (a mensagem era do outro)", obs["pos_vez_depois"] == obs["pos_vez"])
    if obs.get("arma_outro"):
        check("ação livre fora da vez vale (largar a arma)",
              obs["chao_depois"] == obs["chao_antes"] + 1 and not obs["arma_outro_depois"])
    check("a vez passou pelos 3 heróis (end_turn sem `heroi` encerra quem está na vez)",
          len(obs["vezes"]) == 3, obs["vezes"])

    print("\n[4] escada: herói fora só espera enquanto o grupo está dentro")
    check("1 extra fora, grupo dentro: sem lojas", obs["em_cidade_extra"] is False)
    check("…e a conexão segue recebendo game_state", obs["conexao_fora_um"] is False)
    check("todos fora: lojas liberadas", obs["em_cidade_todos"] is True)
    check("…e a conexão passa a receber city_state", obs["conexao_fora_todos"] is True)
    limpar_salas()
```

No `main`, depois de `sid_trio = await secao_inicio()`: `await secao_masmorra()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: `AttributeError: ... '_conexoes_fora'` em [4] (as checagens de [3] já podem passar: a tradução veio na Task 2).

- [ ] **Step 3: Helpers de "conexão toda fora"**

Em `server.py`, logo depois de `def _pids_fora(self):` (e do `return` dela):

```python
    def _conexao_toda_fora(self, conexao):
        """Todos os heróis desta conexão estão na cidade (saíram pela escada).
        Sem grupo é o mesmo que o `fora_masmorra` do próprio herói."""
        herois = [self.players[q] for q in self._herois_da_conexao(conexao) if q in self.players]
        return bool(herois) and all(h.get("fora_masmorra") for h in herois)

    def _conexoes_fora(self):
        """Conexões que estão na cidade com a sala em jogo: recebem city_state,
        nunca game_state. No Solo com grupo, basta um herói dentro para a
        conexão continuar na masmorra."""
        return {c for c in self.connections if self._conexao_toda_fora(c)}
```

- [ ] **Step 4: Usar nos quatro pontos**

`_em_cidade` — troque o `return` por:

```python
        return self.phase == "city" or (self._fora_da_masmorra(pid)
                                        and self._conexao_toda_fora(self._conexao_de(pid)))
```

`push_state` — troque `await self.broadcast(msg_state, skip=self._pids_fora())` por:

```python
        await self.broadcast(msg_state, skip=self._conexoes_fora())
```

`push_state_or_city` — troque `for pid in self._pids_fora():` por `for pid in self._conexoes_fora():`.

`handle_exit_dungeon` — troque a linha `await self.send_city_state_to(pid)` (logo antes do `await self.push_state()` final) por:

```python
        if self._conexao_toda_fora(self._conexao_de(pid)):
            await self.send_city_state_to(pid)
```

`_reentrar_masmorra` — logo depois do `if not p or not p.get("fora_masmorra"): return` e **antes** de `p.pop("fora_masmorra", None)`:

```python
        # Solo com grupo: se outro herói da conexão está lá dentro, o cliente
        # nunca saiu da masmorra — mandar enter_dungeon o faria recarregar.
        avisar_cliente = self._conexao_toda_fora(self._conexao_de(pid))
```

e troque `await self.send_to(pid, {"type": "enter_dungeon"})` por:

```python
        if avisar_cliente:
            await self.send_to(pid, {"type": "enter_dungeon"})
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py && python tools/test_masmorra_sequenciada.py`
Expected: as duas com `0 falharam` (a sequenciada cobre a saída individual de sempre).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): masmorra com grupo numa conexão; escada só espera"
```

---

### Task 6: Queda e volta religam todos os heróis

**Files:**
- Modify: `server.py` — `finally` do handler (ramo em jogo), `religar_heroi`, `_entrada_para_religar` e `_religar_extras` (novos)
- Test: `tools/test_solo_grupo.py`

- [ ] **Step 1: Teste da seção [5]**

```python
async def secao_queda():
    print("\n[5] queda e volta religam todos os heróis")
    obs = {}
    def guardar(c):
        def f():
            r = sala_do_jogo(c["sid"])
            obs["code"] = r.code
        return [f]
    sid, _ = await criar_solo("solo6", "Queda",
        montar_e_iniciar(["warrior", "cleric", "bard"], lambda c: na_masmorra(c) + guardar(c)))
    r = sala_do_jogo(sid)
    check("ao cair, os 3 ficam desconectados",
          all(p.get("connected") is False for p in r.players.values()),
          [(p["name"], p.get("connected")) for p in r.players.values()])
    check("…e fora do tabuleiro", all(list(p["pos"]) == [-1, -1] for p in r.players.values()))
    principal = next(p["id"] for p in r.players.values() if not p.get("controlador"))
    def olhar_religados():
        # Lido DURANTE a 2ª conexão: ao fim do roteiro ela também cai.
        obs["religados"] = [(p.get("connected"), list(p["pos"])) for p in r.players.values()]
    ws2 = FakeWS([login("solo6"), {"type": "rejoin", "code": obs["code"], "name": "solo6"},
                  pausa(), olhar_religados])
    await S.handler(ws2)
    check("ao religar, os 3 voltam conectados e no tabuleiro",
          obs.get("religados") and all(c and pos != [-1, -1] for c, pos in obs["religados"]),
          obs.get("religados"))
    check("os extras continuam ligados à mesma identidade",
          all(p.get("controlador") == principal for p in r.players.values() if p.get("controlador")))
    check("o rejoin trouxe o estado da masmorra", bool(ws2.msgs("game_state")))
    limpar_salas()
```

No `main`: `await secao_queda()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: `❌ ao cair, os 3 ficam desconectados` (só o principal cai hoje).

- [ ] **Step 3: Queda de todos**

No `finally` do handler, troque

```python
            elif pid in room.players:
                # Caiu/saiu durante a partida: personagem deixa a masmorra,
                # turno avanÃ§a se for o caso, os outros continuam jogando.
                await room.handle_disconnect_em_jogo(pid)
```

por (o comentário pode ficar como está; troque só a última linha):

```python
                for heroi in room._herois_da_conexao(pid):
                    await room.handle_disconnect_em_jogo(heroi)
```

- [ ] **Step 4: Volta de todos**

Em `server.py`, logo antes de `async def religar_heroi`:

```python
    def _entrada_para_religar(self, p):
        """Casa por onde um herói religado reentra na masmorra (None = fica)."""
        if self.start_mode == "hero_spawns":
            start = self._start_point_for_player(p)
            return list(start) if start else None
        ent = next((r for r in self.rooms if r["role"] == "entrance"),
                   (self.rooms[0] if self.rooms else None))
        return [ent["cx"], ent["cy"]] if ent else None

    def _religar_extras(self, conexao):
        """Solo com grupo: os heróis extras voltam junto com o principal. Na
        masmorra, cada um volta à casa da foto (retomada) ou à entrada, numa
        casa livre."""
        for h in self._herois_extras_de(conexao):
            h["connected"] = True
            casa = None
            if self.phase == "playing" and h.get("alive") and not h.get("fora_masmorra"):
                casa = h.pop("_pos_retomada", None) or self._entrada_para_religar(h)
            h.pop("_pos_ao_cair", None)
            if casa:
                h["pos"] = self._casa_livre_retomada(list(casa), h["id"])
                h.pop("facing", None)
```

Em `religar_heroi`, logo depois de `alvo.pop("_pos_ao_cair", None)`:

```python
        self._religar_extras(pid)
```

E no ramo final (`else:   # playing — o personagem REENTRA pela escada de entrada`), troque o bloco

```python
            if self.start_mode == "hero_spawns":
                start = self._start_point_for_player(alvo)
                if start:
                    alvo["pos"] = list(start)
            else:
                ent = next((r for r in self.rooms if r["role"] == "entrance"),
                           (self.rooms[0] if self.rooms else None))
                if ent:
                    alvo["pos"] = [ent["cx"], ent["cy"]]
```

por

```python
            casa = self._entrada_para_religar(alvo)
            if casa:
                alvo["pos"] = casa
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py && python tools/test_handler_smoke.py && python tools/test_continuar_jogo.py`
Expected: as três com `0 falharam`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): queda e volta levam o grupo inteiro"
```

---

### Task 7: Continuar — cidade e foto da masmorra recriam o grupo

**Files:**
- Modify: `server.py` — `_recriar_grupo_solo` (novo), `_continuar_jogo_salvo`, `_retomar_masmorra`
- Test: `tools/test_solo_grupo.py`

- [ ] **Step 1: Teste das seções [6] e [7]**

```python
async def continuar(conta, sid, fase):
    obs = {}
    async def esperar_fase_e_olhar():
        await esperar(lambda: sala_do_jogo(sid) and sala_do_jogo(sid).phase == fase)
        await asyncio.sleep(0.05)
        r = sala_do_jogo(sid)
        obs["players"] = {p["id"]: dict(p) for p in r.players.values()}
    ws = FakeWS([login(conta), {"type": "load_savegame", "id": sid}, esperar_fase_e_olhar])
    await S.handler(ws)
    return obs.get("players") or {}, ws


async def secao_continuar(sid_trio):
    print("\n[6] Continuar na cidade recria o grupo")
    ps, ws = await continuar("solo4", sid_trio, "city")
    principal = next((p for p in ps.values() if not p.get("controlador")), {})
    check("os 3 heróis voltam", sorted(p["class_id"] for p in ps.values()) == ["mage", "rogue", "warrior"],
          [p.get("class_id") for p in ps.values()])
    check("os extras apontam para a conexão nova",
          sum(1 for p in ps.values() if p.get("controlador") == principal.get("id")) == 2)
    mago = next((p for p in ps.values() if p.get("class_id") == "mage"), {})
    check("o mago volta com as magias salvas",
          sorted(mago.get("magias_conhecidas") or [])[:2] == sorted(duas_magias("mage")))
    check("pula a tela de herói (auto_start)",
          ws.msgs("lobby_state") and all(l.get("auto_start") for l in ws.msgs("lobby_state")))
    limpar_salas()

    print("\n[7] Continuar com foto da masmorra")
    antes = {}
    def fotografar(c):
        def f():
            r = sala_do_jogo(c["sid"])
            antes.update({p["class_id"]: list(p["pos"]) for p in r.players.values()})
            antes["gravou"] = r._gravar_foto_rodada()
        return [f]
    sid, _ = await criar_solo("solo1", "Foto",
        montar_e_iniciar(["warrior", "rogue", "paladin"], lambda c: na_masmorra(c) + fotografar(c)))
    check("a foto foi gravada", antes.get("gravou") is True)
    limpar_salas()
    ps, _ = await continuar("solo1", sid, "playing")
    principal = next((p for p in ps.values() if not p.get("controlador")), {})
    check("retomou dentro da masmorra com os 3",
          sorted(p["class_id"] for p in ps.values()) == ["paladin", "rogue", "warrior"])
    check("extras religados à conexão nova",
          sum(1 for p in ps.values() if p.get("controlador") == principal.get("id")) == 2)
    check("cada herói na casa da foto",
          all(list(p["pos"]) == antes[p["class_id"]] for p in ps.values()),
          {p["class_id"]: p["pos"] for p in ps.values()})
    limpar_salas()
```

No `main`: `await secao_continuar(sid_trio)`.

> A conta `solo1` foi usada na [1], mas lá o jogo nunca começou (nada vinculado); criar outro jogo com ela é válido.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_solo_grupo.py`
Expected: `❌ os 3 heróis voltam` (só o principal volta).

- [ ] **Step 3: Recriar as cascas no Continuar**

Em `server.py`, logo depois de `_vincular_grupo_solo`:

```python
    def _recriar_grupo_solo(self, conexao, conta):
        """Continuar um Solo com grupo: as cascas dos heróis extras voltam ao
        lobby, controladas por esta conexão, com as magias salvas."""
        m = ((self.savegame or {}).get("members") or {}).get(conta) or {}
        chars = (self.savegame or {}).get("characters") or {}
        presentes = {q.get("class_id") for q in self.players.values()}
        for cls in (m.get("class_ids") or [])[1:]:
            if cls in CLASSES and cls not in presentes:
                magias = (chars.get(cls) or {}).get("magias_conhecidas")
                nova = self._casca_extra(conexao, cls, magias)
                self.players[nova["id"]] = nova
```

Em `_continuar_jogo_salvo`, logo depois de `await self.select_class(pid, cls, anunciar=False)`:

```python
        self._recriar_grupo_solo(pid, conta)
```

- [ ] **Step 4: A foto mantém o controlador novo**

Em `_retomar_masmorra`, troque

```python
                manter = {k: p[k] for k in ("id", "name", "slot") if k in p}
```

por

```python
                manter = {k: p[k] for k in ("id", "name", "slot", "controlador") if k in p}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_solo_grupo.py && python tools/test_salvar_masmorra.py && python tools/test_continuar_jogo.py`
Expected: as três com `0 falharam`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_solo_grupo.py
git commit -m "feat(solo-grupo): Continuar recria o grupo na cidade e na masmorra"
```

---

### Task 8: Cliente — conexão, herói em foco e `heroi` nas mensagens

**Files:**
- Modify: `src/gameState.js`
- Create: `tools/test_solo_grupo_cliente.js`

- [ ] **Step 1: Teste node**

Crie `tools/test_solo_grupo_cliente.js`:

```js
// Solo com grupo — cliente. Roda da raiz:
//   node tools/test_solo_grupo_cliente.js
// `myPid` é o herói EM FOCO; `connPid` é a conexão. O foco pula sozinho para
// o herói meu que está na vez, e toda mensagem leva `heroi` quando há grupo.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

const enviados = [];
let sock = null;
const guardado = {};
global.WebSocket = class {
  constructor() { this.readyState = 1; sock = this; }
  send(s) { enviados.push(JSON.parse(s)); }
  close() {}
};
global.window = {};
global.localStorage = { getItem: k => guardado[k] ?? null,
                        setItem: (k, v) => { guardado[k] = v; }, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chega = m => sock.onmessage({ data: JSON.stringify(m) });

const focos = [];
GS.on("focoHeroi", ev => focos.push(ev));

console.log("\n[1] Lobby: aprende a conexão e os heróis dela");
chega({ type: "lobby_state", code: "ABCD", host: "c", players: [
  { id: "c", name: "Ana", class_id: "warrior" },
  { id: "m", name: "Pedro", class_id: "mage", controlador: "c" },
  { id: "o", name: "Bia", class_id: "rogue" } ] });
check("connPid = principal", GS.connPid === "c");
check("myPid começa no principal", GS.myPid === "c");
check("meusHerois = principal + extra", JSON.stringify(GS.meusHerois.slice().sort()) === '["c","m"]');
check("temGrupo", GS.temGrupo === true);
check("ehMeuHeroi: extra sim, alheio não", GS.ehMeuHeroi("m") && !GS.ehMeuHeroi("o"));
check("cascaDaClasse('mage') = extra", GS.cascaDaClasse("mage") === "m");
check("sessão grava a CONEXÃO", JSON.parse(guardado.lfh_session).pid === "c");

console.log("\n[2] Foco segue a vez");
const estado = vez => ({ type: "game_state", current_turn: vez, players: [
  { id: "c", name: "Ana", pos: [1, 1], alive: true },
  { id: "m", name: "Pedro", pos: [2, 1], alive: true, controlador: "c" } ],
  monsters: [], tiles: [[1]], explored: [], rooms: [] });
chega(estado("m"));
check("vez do extra → foco nele", GS.myPid === "m");
check("isMyTurn verdadeiro", GS.isMyTurn === true);
check("evento focoHeroi automático", focos.length === 1 && focos[0].pid === "m" && focos[0].auto === true);
chega(estado("m"));
check("mesmo turno não repete o evento", focos.length === 1);

console.log("\n[3] Troca manual de foco");
check("focarHeroi recusa pid alheio", GS.focarHeroi("o") === false && GS.myPid === "m");
check("focarHeroi no principal", GS.focarHeroi("c") === true && GS.myPid === "c");
check("fora da vez dele → isMyTurn falso", GS.isMyTurn === false);
check("evento manual", focos[focos.length - 1].auto === false);
chega(estado("m"));
check("um novo game_state do mesmo turno NÃO rouba o foco manual", GS.myPid === "c");

console.log("\n[4] Mensagens levam o herói em foco");
enviados.length = 0;
GS.endTurn();
check("end_turn leva heroi = foco", enviados[0] && enviados[0].heroi === "c");
GS.setKnownSpells(["a", "b"], "m");
check("setKnownSpells com herói explícito", enviados[1] && enviados[1].heroi === "m");
GS.selectParty(["warrior", "mage"]);
check("selectParty manda a lista", enviados[2] && enviados[2].type === "select_party"
      && enviados[2].classes.length === 2);

console.log("\n[5] Sem grupo, nada muda");
GS.connect("ws://x", "Leo", "create");
chega({ type: "lobby_state", code: "EFGH", host: "z", players: [{ id: "z", name: "Leo" }] });
enviados.length = 0;
GS.endTurn();
check("sem grupo: mensagem sem heroi", enviados[0] && enviados[0].heroi === undefined);
check("sem grupo: temGrupo falso", GS.temGrupo === false);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_solo_grupo_cliente.js`
Expected: `❌ connPid = principal` e outras.

- [ ] **Step 3: Estado novo**

Em `src/gameState.js`, logo depois de `let myPid           = null;`:

```js
  // Solo com grupo: `connPid` é a CONEXÃO; `myPid` passa a ser o herói EM FOCO
  // (todo leitor de myPid quer dizer "o herói que estou vendo"). `meusHerois`
  // são os pids que esta conexão controla. Com 1 herói, myPid === connPid.
  let connPid         = null;
  let meusHerois      = [];
  let _focoTurno      = null;   // último herói meu que recebeu a vez
```

- [ ] **Step 4: Funções do foco**

Em `src/gameState.js`, logo **antes** de `function _handle(msg) {`:

```js
  // ── Solo com grupo: herói em foco ──────────────────────────────────────────
  function _aprenderConexao(players) {
    if (!connPid && myPid) connPid = myPid;
    meusHerois = connPid ? (players || [])
      .filter(p => p && (p.id === connPid || p.controlador === connPid)).map(p => p.id) : [];
    if (myPid && connPid && meusHerois.length && !meusHerois.includes(myPid)) myPid = connPid;
  }
  // A vez de um herói meu puxa o foco para ele UMA vez por turno: depois disso
  // o jogador pode olhar outro herói sem ter o foco roubado a cada game_state.
  function _focarVez(msg) {
    const vez = [msg.current_turn, msg.last_stand_pid, msg.animados_turn]
      .find(id => id && meusHerois.includes(id)) || null;
    if (vez && vez !== _focoTurno) { myPid = vez; _emit('focoHeroi', { pid: vez, auto: true }); }
    _focoTurno = vez;
  }
  function _calcIsMyTurn(msg) {
    return msg.test_mode ? msg.master_pid === myPid
      : msg.current_turn === myPid || msg.last_stand_pid === myPid || msg.animados_turn === myPid;
  }
  function focarHeroi(pid) {
    if (!meusHerois.includes(pid) || pid === myPid) return false;
    myPid = pid;
    if (gameState) isMyTurn = _calcIsMyTurn(gameState);
    _emit('focoHeroi', { pid, auto: false });
    return true;
  }
  function ehMeuHeroi(pid) {
    return meusHerois.length ? meusHerois.includes(pid) : pid === myPid;
  }
  function cascaDaClasse(cls) {
    const p = ((lobbyState && lobbyState.players) || [])
      .find(q => q && q.class_id === cls && meusHerois.includes(q.id));
    return p ? p.id : undefined;
  }
  function selectParty(classes) { send({ type: 'select_party', classes }); }
```

- [ ] **Step 5: Ligar nos handlers de mensagem**

No `case 'lobby_state':`, logo depois do bloco `if (!myPid) { ... }`:

```js
        _aprenderConexao(msg.players);
```

No `case 'city_state':`, logo depois do bloco `if (!myPid) { ... }`:

```js
        _aprenderConexao(msg.players);
```

No `case 'game_state':`, troque

```js
        isMyTurn = msg.test_mode ? msg.master_pid === myPid
          : msg.current_turn === myPid || msg.last_stand_pid === myPid
            || msg.animados_turn === myPid;
```

por

```js
        _aprenderConexao(msg.players);
        if (!msg.test_mode) _focarVez(msg);
        isMyTurn = _calcIsMyTurn(msg);
```

- [ ] **Step 6: Sessão, reset e `send`**

Em `_saveSession`, troque `pid: myPid` por `pid: connPid || myPid`.

Na retomada de sessão (`if (s.pid) myPid = s.pid;`), troque por:

```js
    if (s.pid) { myPid = s.pid; connPid = s.pid; }
```

Em **todo** lugar que faz `myPid = null` (são 3: a limpeza de sessão, o `connect` e a troca de sala), acrescente na mesma posição:

```js
    connPid = null; meusHerois = []; _focoTurno = null;
```

Em `function send(obj) {`, logo depois do `if (!ws || ws.readyState !== 1) return false;`:

```js
    // Solo com grupo: a ação é do herói em foco. O servidor ignora `heroi` nas
    // mensagens da conexão (lobby, conta, Mestre…).
    if (meusHerois.length > 1 && myPid && obj && obj.heroi === undefined)
      obj = Object.assign({}, obj, { heroi: myPid });
```

Troque `function setKnownSpells(ids)       { send({ type: 'set_known_spells', ids }); }` por:

```js
  function setKnownSpells(ids, heroi) {
    send(heroi ? { type: 'set_known_spells', ids, heroi } : { type: 'set_known_spells', ids });
  }
```

- [ ] **Step 7: Exportar**

No objeto exportado, junto de `get myPid()           { return myPid; },`:

```js
    get connPid()         { return connPid; },
    get meusHerois()      { return meusHerois.slice(); },
    get temGrupo()        { return meusHerois.length > 1; },
```

E junto de `setKnownSpells,`:

```js
    focarHeroi,
    ehMeuHeroi,
    cascaDaClasse,
    selectParty,
```

- [ ] **Step 8: Rodar e ver passar**

Run: `node tools/test_solo_grupo_cliente.js && node tools/test_atravessar_aliados_cliente.js && node tools/test_visao_compartilhada_cliente.js`
Expected: as três com `0 falharam`.

- [ ] **Step 9: Commit**

```bash
git add src/gameState.js tools/test_solo_grupo_cliente.js
git commit -m "feat(solo-grupo): cliente com herói em foco e heroi nas mensagens"
```

---

### Task 9: Tela de seleção em modo grupo

**Files:**
- Modify: `game.js` — `handleLobby`, `_csHeroGridSync`, `csConfirmClass`, `_confirmarMagiasCriacao`, novas `_csAlternarNoGrupo`/`_csAtualizarBotaoGrupo`
- Modify: `game.css`, `src/lang/interface.js`

- [ ] **Step 1: Chaves de interface**

Em `src/lang/interface.js`, antes do `};` final (acrescente vírgula na entrada anterior):

```js
  "ui.selecao.adicionar_ao_grupo": {
    "en": "➕ Add to party",
    "pt": "➕ Adicionar ao grupo"
  },
  "ui.selecao.remover_do_grupo": {
    "en": "➖ Remove from party",
    "pt": "➖ Remover do grupo"
  },
  "ui.selecao.grupo_minimo": {
    "en": "The party needs at least 1 hero.",
    "pt": "O grupo precisa de pelo menos 1 herói."
  },
  "ui.selecao.grupo_dica": {
    "en": "Solo: pick from 1 to 6 heroes — you control them all.",
    "pt": "Solo: marque de 1 a 6 heróis — você controla todos."
  },
  "ui.hud.na_vez": {
    "en": "⚔️ their turn",
    "pt": "⚔️ na vez"
  },
  "ui.hud.clique_para_focar": {
    "en": "Click to control this hero",
    "pt": "Clique para controlar este herói"
  }
```

- [ ] **Step 2: `handleLobby` em modo grupo**

Em `handleLobby`, dentro do `if(csf){`, troque

```js
    const meP = msg.players.find(p=>p.id===GS.myPid);
    const myClass = meP?.class_id;
    csf.selectedId = myClass ?? csf.selectedId;
```

por

```js
    const meP = msg.players.find(p=>p.id===GS.myPid);
    const myClass = meP?.class_id;
    // Solo com grupo: o jogador marca várias classes; a seleção do carrossel
    // é só "qual estou olhando", e não volta ao principal a cada lobby_state.
    csf.partyMode = !!msg.grupo_solo;
    csf.partyIds = new Set(csf.partyMode
      ? msg.players.filter(p => GS.ehMeuHeroi(p.id) && p.class_id).map(p => p.class_id) : []);
    if(!csf.partyMode) csf.selectedId = myClass ?? csf.selectedId;
```

e troque

```js
    csf.takenIds = new Set(
      msg.players.filter(p => p.id !== GS.myPid && p.class_id).map(p => p.class_id));
```

por

```js
    csf.takenIds = new Set(
      msg.players.filter(p => !GS.ehMeuHeroi(p.id) && p.class_id).map(p => p.class_id));
```

No fim de `handleLobby`, depois do bloco `if(msg.entrada_tardia){...}`:

```js
  if(csf && csf.partyMode){
    const hint = document.getElementById('cs-hint');
    if(hint) hint.textContent = t('ui.selecao.grupo_dica');
  }
  _csHeroGridSync();
```

- [ ] **Step 3: Grade e botão**

Em `_csHeroGridSync`, dentro do `forEach`, depois de `tile.classList.toggle('taken', !!taken);`:

```js
    tile.classList.toggle('no-grupo', !!(csf.partyMode && csf.partyIds && csf.partyIds.has(id)));
```

e no fim da função (depois do `forEach`):

```js
  _csAtualizarBotaoGrupo();
```

Logo depois de `_csHeroGridSync`, acrescente:

```js
// Solo com grupo: o botão de confirmar vira "adicionar/remover do grupo".
// A chave vai no data-i18n para a troca de idioma não desfazer o rótulo.
function _csAtualizarBotaoGrupo(){
  const btn = document.getElementById('cs-btn-confirm');
  if(!btn || !csf) return;
  const chave = !csf.partyMode ? 'ui.selecao.partir_aventura'
    : (csf.partyIds && csf.partyIds.has(csf.selectedId)) ? 'ui.selecao.remover_do_grupo'
    : 'ui.selecao.adicionar_ao_grupo';
  btn.setAttribute('data-i18n', chave);
  btn.textContent = t(chave);
}

function _csAlternarNoGrupo(cls){
  const atual = [...(csf.partyIds || [])];
  const tinha = atual.includes(cls);
  const lista = tinha ? atual.filter(c => c !== cls) : atual.concat(cls);
  if(!lista.length){ toast(t('ui.selecao.grupo_minimo'), 'var(--orange)'); return; }
  if(lista.length > 6) return;
  GS.selectParty(lista);
  if(!tinha && (cls === 'mage' || cls === 'cleric')){
    window._magiasCriacaoClasseGrupo = cls;
    mostrarOverlaySelecaoMagiasCriacao(cls);
  }
}
```

- [ ] **Step 4: Confirmar e magias**

Em `csConfirmClass`, logo depois do bloco do `takenIds` (o `if(csf.takenIds && ...){ ... return; }`):

```js
  if(csf.partyMode){ _csAlternarNoGrupo(csf.selectedId); return; }
```

Em `window._confirmarMagiasCriacao`, troque `GS.setKnownSpells(sel);` por:

```js
  // Solo com grupo: as magias são do herói daquela classe, não do principal.
  const clsGrupo = window._magiasCriacaoClasseGrupo;
  window._magiasCriacaoClasseGrupo = null;
  GS.setKnownSpells(sel, clsGrupo ? GS.cascaDaClasse(clsGrupo) : undefined);
```

- [ ] **Step 5: CSS**

Em `game.css`, ao fim:

```css
/* Solo com grupo: heróis marcados na grade de seleção */
.cs-hero-tile.no-grupo { outline: 2px solid var(--gold, #c8a951); outline-offset: -2px; }
.cs-hero-tile.no-grupo::after {
  content: "✓"; position: absolute; top: 6px; right: 8px;
  color: var(--gold, #c8a951); font-weight: 700; font-size: 18px;
  text-shadow: 0 1px 3px #000;
}
/* Cartão do herói meu que está na vez (Solo com grupo) */
.pcard-vez { font-size: 11px; color: #ffd36b; }
```

Confira se `.cs-hero-tile` já tem `position: relative` (`grep -n "cs-hero-tile" game.css`); se não tiver, acrescente `.cs-hero-tile.no-grupo { position: relative; }`.

- [ ] **Step 6: Verificar sintaxe e placares de idioma**

Run: `node --check game.js && python tools/test_interface.py && python tools/test_idioma.py && python tools/dividas.py`
Expected: sem erro de sintaxe; `0 falharam` nos testes; o `dividas.py` não lista nada novo destas tarefas.

- [ ] **Step 7: Commit**

```bash
git add game.js game.css src/lang/interface.js
git commit -m "feat(solo-grupo): tela de seleção marca de 1 a 6 heróis"
```

---

### Task 10: HUD — cartões focam o herói, câmera e visão

**Files:**
- Modify: `game.js` — `renderPlayers`, `_updateCityHeroBar`, `visaoCompartilhadaAtiva`, novo `GS.on('focoHeroi', …)`

- [ ] **Step 1: Cartões da masmorra**

Em `renderPlayers`, logo depois de `const isMe=p.id===GS.myPid, isCur=p.id===state.current_turn;`:

```js
    const meu = GS.temGrupo && GS.ehMeuHeroi(p.id);   // Solo com grupo
```

No template, logo depois da linha do `${fora ? ...}`:

```js
      ${meu && isCur ? `<div class="pcard-vez">${t('ui.hud.na_vez')}</div>` : ''}
```

E troque

```js
    div.title        = t('ui.hud.clique_para_ver_a_ficha');
    div.onclick      = () => {
      const key = _classIdParaHeroiKey(p.cls || p.class_id || p.key);
      abrirFichaEmJogo(key);
    };
```

por

```js
    div.title        = t(meu && !isMe ? 'ui.hud.clique_para_focar' : 'ui.hud.clique_para_ver_a_ficha');
    div.onclick      = () => {
      // Solo com grupo: 1º clique num herói meu passa o controle para ele;
      // clicar no herói já em foco abre a ficha, como sempre.
      if(meu && !isMe){ GS.focarHeroi(p.id); return; }
      const key = _classIdParaHeroiKey(p.cls || p.class_id || p.key);
      abrirFichaEmJogo(key);
    };
```

- [ ] **Step 2: Cartões da cidade**

Em `_updateCityHeroBar`, troque

```js
    card.onclick = () => abrirFichaCidade(card.getAttribute('data-pid'));
```

por

```js
    card.onclick = () => {
      const pid = card.getAttribute('data-pid');
      // Solo com grupo: a ficha de um herói meu abre editável (o foco é ele).
      if(GS.temGrupo && GS.ehMeuHeroi(pid)) GS.focarHeroi(pid);
      abrirFichaCidade(pid);
    };
```

- [ ] **Step 3: Reação à troca de foco**

Em `game.js`, logo depois do bloco `GS.on('gameState', msg => { ... });` (procure o fim dele), acrescente:

```js
// Solo com grupo: o foco mudou de herói. Automático (chegou a vez dele): o
// render do game_state já acontece; só a câmera vai até ele. Manual: redesenha
// a tela com o herói novo (HUD, alcance, visão) e centraliza a câmera.
GS.on('focoHeroi', ev => {
  const st = GS.gameState;
  if(st){
    if(!ev.auto) handleGameState(st);
    const h = (st.players || []).find(p => p.id === ev.pid);
    if(h && Array.isArray(h.pos) && h.pos[0] >= 0) centralizarCamera3DNoPeao(h.pos);
  } else if(GS.cityState){
    _updateCityHeroBar(GS.cityState);
  }
});
```

Confira antes que não existe outro `GS.on('focoHeroi'` (`grep -n "focoHeroi" game.js` deve mostrar só este) — um segundo `GS.on` do mesmo evento apaga o primeiro em silêncio.

- [ ] **Step 4: Visão sempre compartilhada no grupo**

Troque o corpo de `visaoCompartilhadaAtiva`:

```js
function visaoCompartilhadaAtiva(state){
  // Solo com grupo: todos os heróis são do mesmo jogador — esconder o que um
  // vê do outro não faz sentido.
  if(GS.temGrupo) return true;
  return _visaoCompPref && visaoCompartilhadaPermitida(state);
}
```

- [ ] **Step 5: Verificar**

Run: `node --check game.js && node tools/test_visao_compartilhada_cliente.js && node tools/test_sons_cliente.js && python tools/test_interface.py`
Expected: sem erro; `0 falharam` em todos (o `test_sons_cliente` [10] proíbe `GS.on` duplicado).

- [ ] **Step 6: Commit**

```bash
git add game.js
git commit -m "feat(solo-grupo): cartões trocam o herói em foco; câmera e visão do grupo"
```

---

### Task 11: Prova no navegador

**Files:** nenhum (só verificação). Use o servidor da worktree numa porta isolada.

- [ ] **Step 1: Subir o servidor da worktree**

No `.claude/launch.json` do **checkout principal** (o `preview_start` lê esse), acrescente temporariamente:

```json
    {
      "name": "solo-grupo",
      "runtimeExecutable": "python",
      "runtimeArgs": ["<CAMINHO ABSOLUTO DA WORKTREE>/server.py"],
      "env": { "LFH_PORT": "8779" },
      "port": 8779,
      "autoPort": false
    }
```

Antes, confira que a 8779 está livre. Se algo ocupa a porta, veja a linha de comando do processo antes de matar qualquer coisa (pode ser de outra sessão). `preview_start {name:"solo-grupo"}`, abra `http://localhost:8779/index.html?v=solo1` (cache-buster).

- [ ] **Step 2: Roteiro**

Numa aba só (os passos `GS.*` podem ser feitos pelo `javascript_tool`):
1. Criar conta de teste, criar jogo **Solo**, abrir. Conferir a dica "Solo: marque de 1 a 6 heróis".
2. Marcar Guerreiro, Mago (escolher 2 magias) e Ladino. Conferir ✓ nos três e o botão alternando "Adicionar/Remover".
3. Iniciar. Na cidade, clicar no cartão do Mago: a ficha abre editável (botões de equipar ativos).
4. Entrar na masmorra. Conferir: o foco pula para cada herói na vez dele (HUD e câmera); a faixa de cartões marca "⚔️ na vez".
5. Na vez do Guerreiro, clicar no cartão do Ladino: HUD do Ladino com ações apagadas; largar um item dele (arrastar para fora do inventário) funciona. Clicar de volta no Guerreiro e encerrar o turno.
6. ⚙️ → "💾 Salvar e sair", entrar de novo e Continuar: volta à masmorra com os três, na mesma casa.
7. `read_console_messages` sem erros. Trocar o idioma para English com a tela de seleção aberta: o botão mantém "Add to party".

- [ ] **Step 3: Evidência**

Capture uma screenshot da masmorra com os três cartões (renderizar com `renderer.render()` + `toDataURL()` se o painel estiver oculto — com ele oculto o `requestAnimationFrame` não roda).

- [ ] **Step 4: Desfazer o servidor de teste**

`preview_stop` e remova a entrada `solo-grupo` do `.claude/launch.json` do checkout principal (deixe só a `game`).

---

### Task 12: Documentação, bateria completa e merge

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: CLAUDE.md**

Na tabela "Client → Server", logo depois da linha `select_class`:

```markdown
| `select_party` | `classes:[…]` — **Solo com grupo**: o anfitrião de um jogo salvo Solo novo marca de 1 a 6 classes; substitui a seleção anterior. Os heróis além do 1º nascem com `controlador` (pid da conexão). Ver "Solo com grupo". |
```

E, depois do bloco "Foto da masmorra", um bloco novo:

```markdown
> **Solo com grupo (2026-10-01):** no jogo salvo **Solo**, a tela de seleção marca de 1 a 6
> classes (`select_party`, só no lobby de um Solo novo, sem Mestre, só com a conta do dono) e
> o jogador controla todos. **Heróis por procuração:** o 1º herói tem o pid da conexão; os
> outros são entradas completas de `self.players` com pid próprio e `controlador` = pid da
> conexão — iniciativa, XP (já dividido pelos vivos), derrota, checkpoint e foto seguem sem
> mudança. **Quem age:** `GameRoom.heroi_da_acao(conexão, msg)`, chamado no `handler` antes do
> despacho: `msg.heroi` de herói desta conexão → ele; senão um extra desta conexão na vez →
> ele; senão a própria conexão. `heroi` de outro controlador → `erro.esse_heroi_nao_e_seu`.
> `MENSAGENS_DA_CONEXAO` (+ prefixos `mestre_`/`teste_`/`upload_`/`save_`/`load_`) nunca são
> traduzidas. Enquanto despacha, `pid` aponta para o herói e `_traduzido` guarda a conexão
> (restaurada no topo do laço e no `finally`). Checagem de anfitrião: `_eh_anfitriao(pid)`.
> **Resposta:** `send_to(herói extra)` entrega na conexão do controlador, no idioma dela.
> **Jogo salvo:** `members[conta]` mantém `class_id` (principal) e ganha `class_ids` (o grupo),
> gravados no `start_game` (`_vincular_grupo_solo`); `_continuar_jogo_salvo` recria as cascas
> (`_recriar_grupo_solo`) e a foto mantém o `controlador` novo. **Solo com grupo é fechado**
> (`_dono_grupo_solo`): outra conta não entra; Solo de 1 herói continua aceitando quem chega.
> **Queda/volta:** o `finally` derruba todos os heróis da conexão (extras primeiro); o `rejoin`
> do principal religa os extras (`_religar_extras`). **Escada:** o herói que sai só espera —
> `_em_cidade` e o `skip` do `push_state` usam `_conexao_toda_fora` (todos os heróis da
> conexão fora). **Cliente:** `connPid` = conexão; `myPid` = **herói em foco** (pula sozinho
> para o herói meu na vez, uma vez por turno; `GS.focarHeroi(pid)` troca à mão);
> `GS.meusHerois`/`temGrupo`/`ehMeuHeroi`; com grupo, `send` acrescenta `heroi: myPid`; a sessão
> grava o `connPid`. Cartões do HUD/cidade de heróis meus focam o herói (2º clique abre a
> ficha); evento `focoHeroi` centraliza a câmera; visão compartilhada sempre ligada no grupo.
> Seleção: `msg.grupo_solo` liga o modo grupo (`_csAlternarNoGrupo`, magias por herói via
> `setKnownSpells(ids, heroi)`). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-10-01-solo-com-grupo*`. Testes:
> `tools/test_solo_grupo.py` e `tools/test_solo_grupo_cliente.js`.
```

- [ ] **Step 2: Bateria completa**

Rode todas as suítes Python e node de `tools/test_*.py` / `tools/test_*.js` (veja a memória "Laço de testes com exit code falso": conte as falhas pelo texto `❌`/`falharam`, não pelo `$?` de um pipe). Compare com o `master` antes da mudança: qualquer vermelha nova é regressão.

Run (exemplo, Git Bash):

```bash
for f in tools/test_*.py; do out=$(python "$f" 2>&1); echo "$out" | grep -q "❌\|Traceback" && echo "VERMELHO: $f"; done
for f in tools/test_*.js; do out=$(node "$f" 2>&1); echo "$out" | grep -q "❌\|Error" && echo "VERMELHO: $f"; done
```

Expected: nenhuma linha `VERMELHO:` que também não esteja vermelha no `master`.

- [ ] **Step 3: Commit da documentação**

```bash
git add CLAUDE.md
git commit -m "docs(solo-grupo): CLAUDE.md"
```

- [ ] **Step 4: Merge no master com o WIP do autor intacto**

O checkout principal tem trabalho não commitado. Siga o procedimento já usado nesta sessão:
1. Backup de cópia dos arquivos modificados do checkout principal em `%TEMP%` (por nome).
2. `git stash push -m solo-grupo-merge` no checkout principal; anote o SHA do stash.
3. `git merge --ff-only feat/solo-com-grupo` (ou merge normal se o master andou).
4. `git stash apply <SHA>`; resolver conflitos (o `CLAUDE.md` costuma conflitar: manter os dois textos); `git reset` para tirar do índice.
5. Conferir que o diff do WIP do autor é o mesmo de antes (multiconjunto de linhas +/-) e restaurar os bytes exatos dos arquivos com finais de linha mistos a partir do backup quando o git os normalizar.
6. Remover o stash pelo SHA.
7. **Não fazer push** sem o autor pedir.
```
