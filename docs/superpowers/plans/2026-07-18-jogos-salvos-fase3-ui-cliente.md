# Jogos Salvos — Fase 3: UI do Cliente — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao jogador as telas para usar os jogos salvos: login (apelido+PIN), "Novo jogo" × "Continuar jogo", e um lobby que mostra o vínculo conta↔personagem e trava a classe de quem já está vinculado.

**Architecture:** Uma pequena adição no servidor (enriquecer `lobby_state` com contexto de savegame/conta), senders + roteamento de mensagens em `src/gameState.js`, e telas novas em `game.js` (HTML embutido + funções globais + callbacks `GS.on`). Reusa toda a camada das Fases 1–2.

**Tech Stack:** Vanilla JS (sem framework/bundler), WebSocket, HTML/CSS embutidos em `game.js`. Testes: automated para o servidor (`tools/test_savegames.py`); a UI é verificada **in-app** pela Browser preview (não há harness de UI no projeto).

**Spec:** `docs/superpowers/specs/2026-07-18-jogos-salvos-campanhas-persistentes-design.md`
**Depende de:** Fases 1 e 2 (backend completo e testado).

---

## ⚠️ COORDENAÇÃO OBRIGATÓRIA (ler antes de começar)

O usuário edita `game.js` e `game.css` **em paralelo**. As Tasks 3–5 mexem em `game.js`.
Antes de executar qualquer task de `game.js`:
1. Rodar `git status` e confirmar com o usuário se `game.js`/`game.css` têm WIP não commitado.
2. Se tiverem, **pedir ao usuário para commitar/guardar** o WIP dele primeiro (a Fase 3 não pode
   sobrescrever edições em andamento).
3. Ao commitar, **sempre** `git add` só os arquivos da task (`game.js`/`game.css`/`src/gameState.js`),
   NUNCA `git add -A`/`git add .` — o usuário tem outros arquivos em WIP (`dungeons/`,
   `monstros_personalizados.json`, `tools/editor_monsters_custom.js`, assets). Ver a memória
   `git-add-arquivo-inteiro-varre-wip`.
4. Localizar tudo por **âncoras de texto** (nomes de função, ids de elemento), NUNCA por número de
   linha — o `game.js` do usuário muda de tamanho constantemente.

## Fluxo alvo (uma única conexão WebSocket)

```
tela connect → [login/criar conta]  --login-->  login_result{ok}
   → tela "Meus Jogos" (lista via savegames_list)
       ├─ Novo jogo  --create_savegame-->  savegame_created{id}  --load_savegame{id}-->  lobby_state
       └─ Continuar  --load_savegame{id}-->  lobby_state
   → lobby (mostra vínculo conta↔personagem; classe travada p/ vinculados) → start_game → ...
```

A MESMA conexão faz login → (criar) → carregar → lobby (o `account` do servidor vive na conexão).
O fluxo legado "Criar Sala / Entrar por código" (sem conta, sem save) **permanece** para jogo rápido.

## Estrutura de arquivos

- **Modificar `server.py`** (Task 1): `broadcast_lobby` — adicionar contexto de savegame + conta por jogador.
- **Modificar `src/gameState.js`** (Task 2): senders novos, `connect(...,'login')`, roteamento de `login_result`/`savegames_list`/`savegame_created`, estado `account`/`savegames`, getters.
- **Modificar `game.js`** (Tasks 3–5): painel de login no `#screen-connect`, tela `#screen-savegames`, ajustes no lobby.

---

## Task 1 (servidor): `lobby_state` carrega contexto de savegame + conta

**Files:**
- Modify: `server.py` — `broadcast_lobby` (~5472)
- Test: `tools/test_savegames.py`

Para o cliente travar a classe de um jogador vinculado e mostrar de quem é cada personagem, o `lobby_state` precisa expor: (a) `savegame` = `{id, name}` ou `None`; (b) por jogador, o `account` (apelido) e `bound` (bool — se a conta já tem classe fixada no savegame).

- [ ] **Step 1: Escrever o teste que falha.** Adicionar bloco `[15]` em `tools/test_savegames.py` (após `[14]`, antes do summary). Testa o payload via um capturador do `broadcast`:

```python
    # [15] lobby_state carrega savegame + conta por jogador
    print("\n[15] Lobby com contexto de savegame")
    tmp = tempfile.mkdtemp(); olds = S.SAVEGAMES_DIR; S.SAVEGAMES_DIR = tmp
    try:
        r = GameRoom("LOBS")
        cap = {}
        async def _capb(msg, *a, **k): cap.update(msg)
        r.broadcast = _capb
        sg = S.create_savegame("Jogo", "ricardo", "campaign", "elara.json", False)
        sg["members"]["joao"] = {"class_id": "warrior"}; S.write_savegame(sg)
        r.savegame_id = sg["id"]; r.savegame = sg
        r.players["j1"] = {"id": "j1", "name": "Joao", "class_id": "warrior", "ready": True, "connected": True, "slot": 0}
        r.account_by_pid["j1"] = "joao"
        r.players["j2"] = {"id": "j2", "name": "Maria", "class_id": None, "ready": False, "connected": True, "slot": 1}
        r.account_by_pid["j2"] = "maria"
        _aio.run(r.broadcast_lobby())
        check("payload traz savegame {id,name}", cap.get("savegame", {}).get("id") == sg["id"] and cap["savegame"]["name"] == "Jogo")
        pj = {p["id"]: p for p in cap["players"]}
        check("jogador vinculado marcado bound", pj["j1"].get("account") == "joao" and pj["j1"].get("bound") is True)
        check("jogador não-vinculado bound=False", pj["j2"].get("account") == "maria" and pj["j2"].get("bound") is False)
        # sala SEM savegame → savegame None e sem bound
        r2 = GameRoom("LOB2"); cap2 = {}
        async def _capb2(msg, *a, **k): cap2.update(msg)
        r2.broadcast = _capb2
        r2.players["a"] = {"id": "a", "name": "X", "class_id": None, "ready": False, "connected": True, "slot": 0}
        _aio.run(r2.broadcast_lobby())
        check("sem savegame → savegame None", cap2.get("savegame") is None)
    finally:
        S.SAVEGAMES_DIR = olds; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha.** `python tools/test_savegames.py` → FAIL (payload sem `savegame`/`account`/`bound`).

- [ ] **Step 3: Implementar.** Em `broadcast_lobby`, antes do `await self.broadcast({...})`, montar os dados enriquecidos e usá-los no payload. Substituir o corpo por:

```python
    async def broadcast_lobby(self):
        membros = (self.savegame or {}).get("members", {}) if self.savegame else {}
        jogadores = []
        for p in self.players.values():
            pj = dict(p)
            conta = self.account_by_pid.get(p["id"])
            pj["account"] = conta
            pj["bound"] = bool(conta and membros.get(conta, {}).get("class_id"))
            jogadores.append(pj)
        sg_ctx = {"id": self.savegame["id"], "name": self.savegame.get("name")} if self.savegame else None
        await self.broadcast({
            "type": "lobby_state",
            "code": self.code,
            "host": self.host_pid,
            "players": jogadores,
            "classes": {k: {"name": v["name"], "emoji": v["emoji"], "color": v["color"], "desc": v["desc"]} for k, v in CLASSES.items()},
            "can_start": self._can_start(),
            "master_pid": self.master_pid,
            "dungeons": listar_dungeons(),
            "campaigns": listar_campanhas(),
            "mode": self.mode,
            "selected_dungeon": self.selected_dungeon,
            "selected_campaign": self.selected_campaign,
            "savegame": sg_ctx,
        })
```

- [ ] **Step 4: Rodar e confirmar que passa.** `python tools/test_savegames.py` → [1]–[15] passam.

- [ ] **Step 5: Regressão.** `python tools/test_guilda.py`, `python tools/test_modo_mestre.py` → verdes (sem savegame, `savegame=None` e `players` ganham `account=None`/`bound=False`, campos aditivos inofensivos).

- [ ] **Step 6: Commit.**
```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): lobby_state carrega contexto de savegame + conta/bound por jogador"
```

---

## Task 2 (`src/gameState.js`): senders + roteamento + estado de conta

**Files:**
- Modify: `src/gameState.js`
- Verify: `node -e "require('./src/gameState.js')"` não se aplica (é IIFE de browser); validar sintaxe com `node --check src/gameState.js`.

`gameState.js` é o módulo de lógica (sem DOM). Localizar por âncora: a função `connect(url, name, mode, code)` (a `ws.onopen` despacha por `mode`), a função interna `_handle(msg)` (switch por `msg.type`, cada caso chama `_emit(...)`), o helper `send(obj)`, e a lista de métodos exportados no `return {...}` do IIFE.

- [ ] **Step 1: Adicionar estado de conta.** Perto das outras variáveis de módulo (onde ficam `myName`, `lobbyState`, etc.), adicionar:

```javascript
  let account   = null;   // apelido logado (ou null)
  let savegames = [];     // último savegames_list recebido
```

- [ ] **Step 2: Modo de conexão 'login'.** Na `ws.onopen` dentro de `connect`, trocar o despacho para cobrir o modo novo. Localizar:

```javascript
    ws.onopen = () => {
      if (mode === 'create') send({ type: 'create_room', name });
      else                   send({ type: 'join_room',   name, code });
    };
```
Substituir por:

```javascript
    ws.onopen = () => {
      if      (mode === 'create') send({ type: 'create_room', name });
      else if (mode === 'join')   send({ type: 'join_room',   name, code });
      // mode 'login': não cria/entra em sala aqui; a UI dispara login/create_account.
    };
```

- [ ] **Step 3: Rotear as mensagens novas.** No `_handle`, adicionar casos (junto dos outros `case`):

```javascript
      case 'login_result':
        if (msg.ok) account = msg.username;
        _emit('loginResult', msg);   // {ok, username, error}
        break;

      case 'savegames_list':
        savegames = msg.savegames || [];
        _emit('savegamesList', savegames);
        break;

      case 'savegame_created':
        _emit('savegameCreated', msg.savegame);
        break;
```

- [ ] **Step 4: Adicionar os senders + getters.** Antes do `return {...}` do IIFE, definir as funções:

```javascript
  function loginConta(url, name, pin) {
    // abre a conexão em modo 'login' e, no open, envia login
    connect(url, name, 'login');
    const trySend = () => {
      if (ws && ws.readyState === 1) send({ type: 'login', username: name, pin });
      else setTimeout(trySend, 60);
    };
    trySend();
  }
  function criarConta(url, name, pin) {
    connect(url, name, 'login');
    const trySend = () => {
      if (ws && ws.readyState === 1) send({ type: 'create_account', username: name, pin });
      else setTimeout(trySend, 60);
    };
    trySend();
  }
  function listSavegames()            { send({ type: 'list_savegames' }); }
  function createSavegame(opts)       { send({ type: 'create_savegame', ...opts }); } // {name, mode, campaign_file, has_master}
  function loadSavegame(id)           { send({ type: 'load_savegame', id }); }
  function deleteSavegame(id)         { send({ type: 'delete_savegame', id }); }
```
E no objeto `return { ... }`, adicionar as chaves:

```javascript
    loginConta, criarConta, listSavegames, createSavegame, loadSavegame, deleteSavegame,
    getAccount: () => account,
    getSavegames: () => savegames,
```

- [ ] **Step 5: Validar sintaxe.** `node --check src/gameState.js` → sem erro.

- [ ] **Step 6: Commit.**
```bash
git add src/gameState.js
git commit -m "feat(saves): senders de conta/savegame + estado no gameState"
```

Nota: `loginConta`/`criarConta` reusam `connect(...,'login')`; se já houver conexão aberta e logada, a UI pode chamar `listSavegames`/`createSavegame`/`loadSavegame` direto (mesma ws).

---

## Task 3 (`game.js`): painel de login no `#screen-connect`

**Files:**
- Modify: `game.js` (bloco HTML do `#screen-connect` + funções globais)

**Verificação:** in-app (Browser preview) — não há teste automatizado de UI.

- [ ] **Step 0: Coordenação.** Ver a seção "COORDENAÇÃO OBRIGATÓRIA" acima. Confirmar WIP de `game.js` com o usuário.

- [ ] **Step 1: Adicionar o painel de conta.** No HTML do `#screen-connect` (âncora: `<div class="connect-panel">` … `<h2>Entrar na Aventura</h2>`), acrescentar ACIMA do botão "⚔ Criar Nova Sala" um bloco de conta (seguindo as classes existentes `field`/`btn-primary`/`btn-secondary`):

```html
    <div class="field">
      <label>PIN (4 dígitos) — para jogos salvos</label>
      <input id="input-pin" type="password" inputmode="numeric" maxlength="4" placeholder="••••">
    </div>
    <button class="btn-primary" onclick="entrarComConta()">🎲 Entrar com minha conta</button>
    <div style="font-size:.7rem;color:#8ab88a;margin-top:4px;">
      Primeira vez? O apelido acima vira sua conta. Use o mesmo apelido + PIN para voltar aos seus jogos.
    </div>
    <div class="divider">ou jogo rápido (sem salvar)</div>
```
(O botão "⚔ Criar Nova Sala" e o "Entrar por código" existentes permanecem abaixo, como jogo rápido legado.)

- [ ] **Step 2: Funções globais de login.** Perto de `createRoom()`/`joinRoom()` (âncora: `function createRoom()`), adicionar:

```javascript
function entrarComConta() {
  const name = (document.getElementById('input-name').value || '').trim();
  const pin  = (document.getElementById('input-pin').value || '').trim();
  const url  = (document.getElementById('input-server').value || 'ws://localhost:8765').trim();
  if (!name) { alert('Escolha um apelido.'); return; }
  if (!/^\d{4}$/.test(pin)) { alert('O PIN deve ter 4 dígitos.'); return; }
  // tenta login; se a conta não existir, o servidor recusa e nós oferecemos criar.
  window._contaCtx = { url, name, pin };
  GS.loginConta(url, name, pin);
}
```

- [ ] **Step 3: Reagir ao `login_result`.** Onde os callbacks `GS.on(...)` são registrados (âncora: `GS.on('lobbyState'`), adicionar:

```javascript
GS.on('loginResult', (msg) => {
  if (msg.ok) {
    GS.listSavegames();
    showScreen('screen-savegames');
  } else if ((msg.error || '').includes('não encontrada')) {
    const c = window._contaCtx || {};
    if (confirm('Conta não existe. Criar agora com esse apelido e PIN?')) {
      GS.criarConta(c.url, c.name, c.pin);
    }
  } else {
    alert(msg.error || 'Falha no login.');
  }
});
```

- [ ] **Step 4: Verificar in-app.** Subir o servidor (`python server.py`), abrir `http://localhost:8765/index.html` na Browser preview. Digitar apelido + PIN, "Entrar com minha conta" → primeira vez oferece criar → após criar, cai na tela `screen-savegames` (que ainda não existe → Task 4). Conferir o console por erros. (Nesta task, basta ver o `login_result{ok:true}` no Network/console; a tela vem na Task 4.)

- [ ] **Step 5: Commit.**
```bash
git add game.js
git commit -m "feat(saves): painel de login (apelido+PIN) na tela inicial"
```

---

## Task 4 (`game.js`): tela "Meus Jogos" (novo / continuar / apagar)

**Files:**
- Modify: `game.js` (nova `<div id="screen-savegames">` + funções + callbacks) e opcionalmente `game.css`.

**Verificação:** in-app.

- [ ] **Step 0: Coordenação** (ver seção obrigatória).

- [ ] **Step 1: Adicionar a tela.** Após o `#screen-connect` no HTML embutido, acrescentar:

```html
<div id="screen-savegames" class="screen">
  <div class="connect-panel">
    <h2>Meus Jogos</h2>
    <div id="savegames-list" style="display:flex;flex-direction:column;gap:8px;max-height:40vh;overflow:auto;"></div>
    <div class="divider">criar novo</div>
    <div class="field"><label>Nome do jogo</label>
      <input id="sg-name" type="text" maxlength="40" placeholder="Ex: A Sociedade do Anel"></div>
    <div class="field"><label>Campanha</label>
      <select id="sg-campaign"></select></div>
    <label style="display:flex;gap:6px;align-items:center;font-size:.8rem;">
      <input id="sg-master" type="checkbox"> Este jogo terá um Mestre humano</label>
    <button class="btn-primary" onclick="criarJogoSalvo()">➕ Criar jogo</button>
    <button class="btn-secondary" onclick="showScreen('screen-connect')" style="margin-top:8px;">← Voltar</button>
  </div>
</div>
```

- [ ] **Step 2: Renderizar a lista + popular campanhas.** Adicionar funções globais e o callback. O `savegames_list` traz `{id,name,mode,campaign_file,campaign_phase,members,has_master,owner,updated}`. As campanhas disponíveis vêm do `lobby_state.campaigns` — como aqui ainda não há lobby, buscá-las de um `lobby_state` não é possível; em vez disso, reusar a lista que o servidor manda no `savegames`? Não. Para o dropdown de campanhas, dispare `list_savegames` já traz o suficiente para a lista, mas para CRIAR precisamos das campanhas. Solução: o servidor já expõe `listar_campanhas()` no `lobby_state`; para a tela de criação, adicionar um fetch simples — reusar o handler `list_savegames` para também devolver as campanhas OU (mais simples) incluir as campanhas na resposta `savegames_list`.

  Sub-passo servidor (pequeno): no handler `list_savegames` (server.py), incluir as campanhas disponíveis:
  ```python
                if t == "list_savegames":
                    await ws.send(json.dumps({"type": "savegames_list",
                                              "savegames": list_savegames(account["name"]),
                                              "campaigns": listar_campanhas()}))
                    continue
  ```
  E em `gameState.js`, no `case 'savegames_list'`, guardar as campanhas: `campaignsCache = msg.campaigns || []` e exportar `getCampaigns: () => campaignsCache`. (Declarar `let campaignsCache = []` junto do estado.)

  Client (`game.js`):
```javascript
GS.on('savegamesList', (list) => {
  const box = document.getElementById('savegames-list');
  if (!box) return;
  box.innerHTML = list.length ? '' : '<div style="color:#8ab88a;">Nenhum jogo salvo ainda.</div>';
  for (const sg of list) {
    const membros = Object.keys(sg.members || {}).length;
    const el = document.createElement('div');
    el.className = 'savegame-row';
    el.style.cssText = 'display:flex;justify-content:space-between;align-items:center;gap:8px;background:#0d1a0d;border:1px solid #2a4a2a;border-radius:6px;padding:8px 10px;';
    el.innerHTML = `<div><b>${sg.name}</b><br><span style="font-size:.7rem;color:#8ab88a;">`
      + `${sg.mode === 'campaign' ? 'Campanha' : 'Avulso'} · fase ${(sg.campaign_phase||0)+1} · ${membros} herói(s)</span></div>`;
    const btns = document.createElement('div');
    const cont = document.createElement('button'); cont.className='btn-secondary btn-sm'; cont.textContent='Continuar';
    cont.onclick = () => GS.loadSavegame(sg.id);
    btns.appendChild(cont);
    if (sg.owner === GS.getAccount()) {
      const del = document.createElement('button'); del.className='btn-secondary btn-sm'; del.textContent='🗑';
      del.style.marginLeft='6px';
      del.onclick = () => { if (confirm(`Apagar "${sg.name}"? Isso é permanente.`)) GS.deleteSavegame(sg.id); };
      btns.appendChild(del);
    }
    el.appendChild(btns); box.appendChild(el);
  }
  // popular dropdown de campanhas
  const sel = document.getElementById('sg-campaign');
  if (sel) {
    sel.innerHTML = '';
    for (const c of GS.getCampaigns()) {
      const o = document.createElement('option'); o.value = c.file; o.textContent = c.name; sel.appendChild(o);
    }
  }
});
```

- [ ] **Step 3: Criar jogo + reagir a `savegame_created`.**
```javascript
function criarJogoSalvo() {
  const name = (document.getElementById('sg-name').value || '').trim();
  const campaign_file = document.getElementById('sg-campaign').value || null;
  const has_master = document.getElementById('sg-master').checked;
  if (!name) { alert('Dê um nome ao jogo.'); return; }
  GS.createSavegame({ name, mode: 'campaign', campaign_file, has_master });
}
GS.on('savegameCreated', (sg) => { GS.loadSavegame(sg.id); });  // recém-criado → abre o lobby
```
(Ao chegar `lobby_state` — já tratado no fluxo existente —, o cliente troca para a tela do lobby; garantir que o handler de `lobbyState` chame `showScreen` para o lobby como já faz hoje.)

- [ ] **Step 4: Verificar in-app.** Login → tela Meus Jogos → criar um jogo com uma campanha → deve cair no lobby (mesma conexão). Sair e voltar: o jogo aparece na lista → "Continuar" → lobby. Testar "apagar". Conferir console/Network.

- [ ] **Step 5: Commit.**
```bash
git add game.js src/gameState.js server.py
git commit -m "feat(saves): tela Meus Jogos (novo/continuar/apagar) + campanhas no savegames_list"
```

---

## Task 5 (`game.js`): lobby mostra vínculo e trava classe do vinculado

**Files:**
- Modify: `game.js` (render do lobby)

**Verificação:** in-app.

- [ ] **Step 0: Coordenação** (ver seção obrigatória).

- [ ] **Step 1: Mostrar o nome do jogo salvo.** No render do lobby (âncora: o callback `GS.on('lobbyState', ...)` ou a função que desenha `#screen-lobby`), quando `msg.savegame` existir, exibir um cabeçalho "Jogo: {savegame.name}".

- [ ] **Step 2: Travar a classe de quem está vinculado.** Ao renderizar o seletor de classes / o card de cada jogador, usar os campos novos do `lobby_state.players[]`: `account` e `bound`. Regras:
  - Para o MEU jogador (`p.id === GS.getMyPid?.()` — usar o getter de pid existente): se `bound` é true, mostrar a classe fixa e **desabilitar** a troca de classe (o servidor já força, mas a UI deve refletir).
  - Para os OUTROS: mostrar "personagem de {account}" quando `account` presente.
  - Se `msg.savegame` é null (jogo rápido), comportamento atual inalterado.

  Exemplo de guarda ao montar os botões de classe (adaptar ao código real do lobby):
```javascript
  const meu = msg.players.find(p => p.id === /* getter de pid */);
  const travado = msg.savegame && meu && meu.bound;
  // se travado: não renderizar os botões de seleção de classe; mostrar a classe fixa.
```

- [ ] **Step 3: Verificar in-app.** Com um jogo salvo e um herói já vinculado (rode uma vez, escolha warrior, saia, continue): ao voltar, o lobby deve mostrar o warrior fixado e não permitir trocar. Um 2º jogador (outra conta, use outra aba/nome+PIN) vê "personagem de {conta}" nos cards alheios.

- [ ] **Step 4: Commit.**
```bash
git add game.js
git commit -m "feat(saves): lobby mostra jogo salvo e trava classe do jogador vinculado"
```

---

## Self-Review (Fase 3)

- **Cobertura do spec §Cliente:** login (Task 3), Novo/Continuar/Apagar (Task 4), lobby com auto-vínculo (Task 5), suporte de dados no servidor (Task 1) + senders (Task 2). ✔
- **Byte-identidade do jogo rápido:** o fluxo legado create/join permanece; os campos novos de `lobby_state` são aditivos e `savegame=None` sem jogo salvo. ✔
- **Sem placeholders:** Tasks 1–2 têm código completo + teste/checagem; Tasks 3–5 têm HTML/JS concretos e verificação in-app explícita (a UI não tem harness automatizado no projeto — verificação por Browser preview é o padrão do repo). ✔
- **Consistência de nomes:** mensagens (`login`/`create_account`/`list_savegames`/`create_savegame`/`load_savegame`/`delete_savegame`) e respostas (`login_result`/`savegames_list`/`savegame_created`) batem com os handlers da Fase 1; campos `savegame`/`account`/`bound` do `lobby_state` (Task 1) são consumidos nas Tasks 4–5. ✔

## Pendências herdadas (achados Minor das Fases 1–2, tratar aqui se sobrar tempo)

- Sala vazia não é removida de `rooms` no teardown (pré-existente; benigno — o `load_savegame` recria do disco).
- `pending_spell_pick` de mago/clérigo não é durável — se subir de nível e desconectar antes de escolher a magia, a escolha se perde. Considerar persistir ou resolver antes do checkpoint.
- Mensagens amigáveis para as recusas de trava: `SAVEGAMES_IN_USE` ("jogo em uso em outra sessão") e `ACCOUNTS_ONLINE` ("conta já logada") — já chegam como `error`; garantir que a UI as mostre de forma clara.
