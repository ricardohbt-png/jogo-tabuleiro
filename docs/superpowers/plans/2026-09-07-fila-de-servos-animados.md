# Fila de servos animados — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Na janela pós-turno do mago, os servos animados são selecionados
automaticamente um a um na ordem de iniciativa (prisioneiro por último), e a peça
da vez é a peça que o joystick controla.

**Architecture:** O servidor ganha a noção de "servo da vez" (`animados_atual`,
derivado de `animados_order` menos `animados_done`) e uma mensagem
`encerrar_animado` que avança a fila; quando a fila esvazia ela delega a
`handle_end_turn`, que já sabe fechar a janela. O cliente espelha `animados_atual`
na seleção que já existe (`_animadoSel`), e o joystick troca a "peça ancorada" do
herói para a peça da vez.

**Tech Stack:** Python 3 + `websockets` (servidor autoritativo), JavaScript vanilla
(cliente: `game.js` = render/UI, `src/gameState.js` = estado/lógica pura),
dicionários pt/en em `src/lang/*.js`, testes em `tools/test_*.py` rodados da raiz.

**Spec:** `docs/superpowers/specs/2026-09-07-fila-de-servos-animados-design.md`

---

## ⚠️ BASELINE DE TESTES — leia antes de rodar qualquer suíte

**Esta branch já está vermelha antes desta implementação.** As falhas abaixo são
dívida de i18n do trabalho em andamento do autor (literais em português novos no
`server.py` e no `game.js`), **não** são regressões suas e **não são para você
consertar**. Elas foram medidas no worktree limpo, no commit `135229a`:

| Suíte | Baseline | Falhas pré-existentes |
|---|---|---|
| `python tools/test_reviver_mortos.py` | **32 PASS / 0 FAIL** | — (limpa) |
| `python tools/test_idioma.py` | **36 / 0** | — (limpa) |
| `python tools/test_vocabulario.py` | **38 / 0** | — (limpa) |
| `python tools/test_narracao.py` | **70 / 2** | 28 `gm_say` de uma linha com literal; 43 `gm_say` com texto em português |
| `python tools/test_erros.py` | **19 / 1** | literal de erro de texto fixo no `server.py` |
| `python tools/test_interface.py` | **31 / 5** | 206 literais em português no `game.js`; sobra proposital; 58 funções fechadas; `trapImages` `sopro_dragao`; texto acentuado fora de `data-i18n` |
| `node tools/test_idioma_cliente.js` | **31 / 1** | chave `data-i18n` órfã (95 usadas) |
| `node tools/test_vocabulario_cliente.js` | **54 / 1** | descrição sem chave `.desc` |

**A regra de aceitação de cada task é "não piorou", não "está verde":**

- As três suítes limpas (`test_reviver_mortos`, `test_idioma`, `test_vocabulario`)
  **devem continuar com FAIL=0**. Qualquer falha nelas é sua e precisa de conserto.
- Nas cinco vermelhas, o número de falhas **não pode subir**, e os contadores
  citados acima **não podem crescer**. Em particular: se `test_interface` passar de
  **206** literais, você deixou texto cru em vez de `t('ui....')` — conserte.
  Se `test_narracao` passar de **28/43**, você escreveu um `gm_say` com string em
  português em vez de `T("narracao....")` — conserte.
- **Nunca** conserte as falhas pré-existentes para "deixar verde". Elas são de
  outro trabalho e mexer nelas polui este branch.

---

## Contexto que o implementador precisa saber

**Rode tudo da raiz do projeto** (`C:\Users\RICARDO\Desktop\jogo tabuleiro`).

**PARE O SERVIDOR antes de editar `server.py` ou `game.js`.** Com o servidor
rodando na porta 8765 o Windows trava a escrita desses arquivos e o editor falha
com `OSError: Errno 22`. Um `python -c "import server"` depois de uma escrita que
falhou valida o arquivo ANTIGO e dá falso verde.

**O autor edita `server.py` e `game.js` em paralelo.** Nunca use `git add .` nem
`git add server.py` inteiro sem antes conferir `git status` e `git diff`. Nos
passos de commit deste plano, adicione apenas os arquivos listados — e mesmo
assim confira o diff antes.

**Regra de arquitetura do projeto (`CLAUDE.md`):** `src/gameState.js` NUNCA
referencia `document`, `canvas`, `THREE` ou `window`. Lógica pura e estado vão
lá; render e DOM ficam em `game.js`.

**Idioma:** toda string visível ao jogador precisa de chave pt+en. Narração do
servidor usa `T("narracao.<slug>")` com o dicionário em `src/lang/narracao.js`;
recusas usam `T("erro.<slug>")` em `src/lang/erros.js`; interface do cliente usa
`t('ui.<área>.<slug>')` em `src/lang/interface.js`. Uma chave sem uso é apontada
como órfã pelos testes de idioma, e uma chave usada sem existir devolve a própria
chave na tela.

**`T` não é `str`.** Ele se disfarça de string (`__eq__`, `__contains__`,
`__len__`, `__getattr__`), mas **não tem `__add__` e não funciona em
`str.join`**. Nunca concatene um `T` com `+`; para juntar vários, passe uma
**lista** como parâmetro — o motor junta com o separador do idioma de quem lê.

**Como o estado atual funciona (leia antes da Task 1):**

- `handle_end_turn` (`server.py`, procure por `async def handle_end_turn`) tem
  duas metades. A primeira **abre** a janela dos servos: monta `animados_vivos`,
  ordena por iniciativa, grava `self.animados_order`, seta
  `self.animados_phase_pid = pid` e **retorna**. Essa metade é guardada por
  `self.animados_phase_pid != pid`, então a segunda pressão do botão cai na
  segunda metade, que **fecha** a janela (`animados_phase_pid = None`,
  `animados_order = []`) e avança a iniciativa.
- `_is_turn(pid)` já devolve `True` durante a janela (`or self.animados_phase_pid
  == pid`), então mover/atacar servo passa nas guardas normais de turno.
- O timer anti-AFK (`_turn_timer_expira`) keya em `current_pid()`, que durante a
  janela ainda é o mago. Ele chama `_forcar_fim_turno` → `handle_end_turn`, que
  fecha a janela inteira. **Esse caminho não pode ser tocado.**

---

## File Structure

| Arquivo | Responsabilidade nesta mudança |
|---|---|
| `server.py` | Estado da fila (`animados_done`, `prisioneiro_done`), derivação de `animados_atual`, `handle_encerrar_animado`, entrada no dispatch WS, campo novo no payload de `game_state`. |
| `src/gameState.js` | Lógica pura e estado do cliente: `encerrarAnimado` (sender), `animadoPendenteParaEncerrar` (predicado de despacho), `animadoAttackTargetTiles` (regra única de alcance do servo), `pecaControlada` (quem o controle dirige agora). |
| `game.js` | Render e UI: espelhar `animados_atual` em `_animadoSel`, rótulo dinâmico do botão, e a camada de joystick (cursor, prévia, mira, contexto). |
| `src/lang/narracao.js` | Chaves pt/en dos saltos de servo travado. |
| `src/lang/interface.js` | Chaves pt/en do rótulo do botão e do contexto do joystick. |
| `tools/test_reviver_mortos.py` | Testes do servidor: fila, saltos, prisioneiro, recusas, rede de segurança do `end_turn`. |

---

## Task 1: Estado da fila e o servo da vez (servidor)

**Files:**
- Modify: `server.py` (init do `GameRoom`; `enter_dungeon`; abertura e fechamento da janela em `handle_end_turn`; payload de `game_state`)
- Test: `tools/test_reviver_mortos.py`

- [ ] **Step 1: Escreva o teste que falha**

Abra `tools/test_reviver_mortos.py`. Logo ANTES da linha
`    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")`, insira:

```python
    # ── Helpers da fila de servos (Tasks 1–4) ────────────────────────────────
    def servo(sid, dex, pos=(1, 0), **extra):
        a = {"id": sid, "nome": f"Servo {sid}", "tipo": "zombie",
             "pos": list(pos), "vida_atual": 8, "vida_max": 8,
             "movimento": 3, "moves_left": 3, "acted": False,
             "dex": dex, "int_": 10, "ca": 10}
        a.update(extra)
        return a

    def sala_com_servos(*servos):
        """Sala com o mago já DENTRO da janela dos servos."""
        r = setup()
        p = mage()
        p["animados"] = list(servos)
        r.players = {"m": p}
        r.animados_phase_pid = "m"
        for a in servos:
            a["initiative"] = r.initiative_value(a)
        ordenados = sorted(servos, key=lambda a: (-a["initiative"], -a["dex"], a["id"]))
        r.animados_order = [a["id"] for a in ordenados]
        r.animados_done = set()
        r.prisioneiro_done = False
        return r, p

    # [8] O servo da vez é o de maior iniciativa
    print("\n[8] animados_atual — ordem por iniciativa")
    r, p = sala_com_servos(servo("s_lento", 8), servo("s_rapido", 18), servo("s_medio", 12))
    check("fila começa no de maior iniciativa",
          r._animados_atual("m") == "s_rapido")
    check("ordem completa por iniciativa",
          r.animados_order == ["s_rapido", "s_medio", "s_lento"])

    # [9] Servo encerrado sai da vez
    print("\n[9] animados_done tira o servo da vez")
    r.animados_done.add("s_rapido")
    check("passa ao segundo da ordem", r._animados_atual("m") == "s_medio")
    r.animados_done.add("s_medio")
    r.animados_done.add("s_lento")
    check("fila vazia devolve None", r._animados_atual("m") is None)

    # [10] Fila só existe dentro da janela deste jogador
    print("\n[10] animados_atual fora da janela")
    r2, _ = sala_com_servos(servo("s1", 14))
    r2.animados_phase_pid = None
    check("sem janela aberta devolve None", r2._animados_atual("m") is None)
    r2.animados_phase_pid = "outro"
    check("janela de outro jogador devolve None", r2._animados_atual("m") is None)
```

- [ ] **Step 2: Rode o teste e confirme que falha**

```bash
python tools/test_reviver_mortos.py
```

Esperado: FALHA com `AttributeError: 'GameRoom' object has no attribute '_animados_atual'`.

- [ ] **Step 3: Declare o estado novo no `__init__` do `GameRoom`**

Em `server.py`, ache a linha:

```python
        self.animados_order = []        # ids dos servos na ordem de iniciativa da janela atual
```

Acrescente logo abaixo:

```python
        self.animados_done = set()      # ids dos servos que já encerraram a vez nesta janela
        self.prisioneiro_done = False   # o prisioneiro já encerrou a vez nesta janela
```

- [ ] **Step 4: Escreva os dois helpers da fila**

Em `server.py`, imediatamente ANTES de `async def handle_end_turn(self, pid):`,
insira:

```python
    def _animado_pode_agir(self, a):
        """Um servo só entra na fila se tiver como fazer alguma coisa na vez dele.

        Morto, adormecido por magia ou preso pelo rodamoinho com o turno
        bloqueado: a fila salta, para o jogador não gastar um clique numa peça
        travada. O motivo é narrado por _avancar_fila_animados.
        """
        if not a or a.get("vida_atual", 0) <= 0:
            return False
        if a.get("dormindo"):
            return False
        if a.get("_rodamoinho_bloqueado_turno") or a.get("_rodamoinho_profundo_bloqueado_turno"):
            return False
        return True

    def _animados_atual(self, pid):
        """Quem este jogador controla AGORA na janela pós-turno.

        Derivado, nunca armazenado: o primeiro de animados_order que ainda não
        encerrou e consegue agir; esgotados os servos, o prisioneiro liberto que
        ele resgatou; esgotado tudo, None (a janela pode fechar).
        """
        if self.animados_phase_pid != pid:
            return None
        p = self.players.get(pid)
        if not p:
            return None
        por_id = {a.get("id"): a for a in p.get("animados", [])}
        for aid in self.animados_order:
            if aid in self.animados_done:
                continue
            a = por_id.get(aid)
            if a and not a.get("dominado_por_monstro") and self._animado_pode_agir(a):
                return aid
        pr = self.prisoner
        if (not self.prisioneiro_done and pr and pr.get("freed") and pr.get("alive")
                and pr.get("rescuer_pid") == pid):
            return "prisoner"
        return None
```

- [ ] **Step 5: Rode o teste e confirme que passa**

```bash
python tools/test_reviver_mortos.py
```

Esperado: PASS nas seções `[8]`, `[9]` e `[10]`; `FAIL=0`.

- [ ] **Step 6: Zere a fila junto com `animados_order`**

Ainda em `server.py`, há **três** lugares que precisam limpar os campos novos.

(a) Na ABERTURA da janela, ache:

```python
            self.animados_phase_pid = pid
            self.animados_order = [a["id"] for a in animados_vivos]
```

e acrescente logo abaixo:

```python
            self.animados_done = set()
            self.prisioneiro_done = False
```

(b) No FECHAMENTO da janela, ache:

```python
        self.animados_phase_pid = None
        self.animados_order = []
```

e acrescente logo abaixo:

```python
        self.animados_done = set()
        self.prisioneiro_done = False
```

(c) Em `enter_dungeon`, ache:

```python
        self.animados_phase_pid = None   # ponteiro de turno transitÃ³rio (zera em qualquer entrada)
```

e acrescente logo abaixo:

```python
        self.animados_order = []         # idem — a fila nunca sobrevive a uma entrada
        self.animados_done = set()
        self.prisioneiro_done = False
```

- [ ] **Step 7: Publique `animados_atual` no `game_state`**

Ache no payload:

```python
            "animados_order": self.animados_order,
```

e acrescente logo abaixo:

```python
            # Quem o jogador controla agora na janela pós-turno (id do servo,
            # "prisoner", ou None). O cliente espelha isto na seleção.
            "animados_atual": self._animados_atual(pid),
```

**Atenção — confirme que `pid` está no escopo dessa função.** Verifique com:

```bash
grep -n "\"animados_order\": self.animados_order" server.py
```

e leia as ~60 linhas acima para achar a assinatura da função que monta o payload.

**RESOLVIDO NA EXECUÇÃO:** `_game_state_payload` NÃO recebe `pid` — é montado uma
vez para a sala e transmitido a todos. Portanto o campo publicado é o **dict por
jogador**, e as Tasks 5 e 6 abaixo já vêm com a leitura indexada por `GS.myPid`:

```python
            "animados_atual": {pid_: self._animados_atual(pid_) for pid_ in self.players},
```

e então **todo leitor no cliente passa a indexar por `GS.myPid`**. São exatamente
quatro sítios, todos criados neste plano — troque `state.animados_atual` /
`msg.animados_atual` por `…?.[GS.myPid]` em cada um:

1. `animadoAtual()` em `src/gameState.js` (Task 5, Step 1)
2. `_atualServo` no gancho de `gameState` em `game.js` (Task 5, Step 3)
3. `naFila` e `idx` em `_atualizarBotaoEncerrarTurno` (Task 6, Step 3)
4. nenhum outro — `pecaControlada` e o joystick leem através de `animadoAtual()`

O caminho mais simples, se a função não tiver `pid`, é adicionar o campo no ponto
por jogador em que a mensagem é enviada, mantendo o valor escalar. Prefira isso.

- [ ] **Step 8: Rode o teste e confirme que continua verde**

```bash
python tools/test_reviver_mortos.py
```

Esperado: `FAIL=0`.

- [ ] **Step 9: Commit**

```bash
git add server.py tools/test_reviver_mortos.py
git commit -m "feat(animados): estado da fila e o servo da vez na janela pos-turno

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: Mensagem `encerrar_animado` (servidor)

**Files:**
- Modify: `server.py` (novo handler + entrada no dispatch WS)
- Modify: `src/lang/erros.js`
- Test: `tools/test_reviver_mortos.py`

- [ ] **Step 1: Escreva o teste que falha**

Em `tools/test_reviver_mortos.py`, logo ANTES da linha do `print(f"\n{'='*40}...`,
acrescente:

```python
    # [11] encerrar_animado avança a fila
    print("\n[11] handle_encerrar_animado — avanço")
    r, p = sala_com_servos(servo("s_rapido", 18), servo("s_medio", 12))
    fechou = []
    async def fake_end_turn(pid): fechou.append(pid)
    r.handle_end_turn = fake_end_turn
    await r.handle_encerrar_animado("m", "s_rapido")
    check("primeiro servo marcado como encerrado", "s_rapido" in r.animados_done)
    check("fila passa ao segundo", r._animados_atual("m") == "s_medio")
    check("janela NÃO fechou ainda", fechou == [])
    await r.handle_encerrar_animado("m", "s_medio")
    check("fila vazia delega a handle_end_turn", fechou == ["m"])

    # [12] Recusas
    print("\n[12] handle_encerrar_animado — recusas")
    r, p = sala_com_servos(servo("s1", 14))
    r.handle_end_turn = fake_end_turn
    r.animados_phase_pid = None
    r._errs.clear()
    await r.handle_encerrar_animado("m", "s1")
    check("recusa fora da janela", len(r._errs) == 1)
    check("não marcou nada", r.animados_done == set())

    r, p = sala_com_servos(servo("s1", 14))
    r.handle_end_turn = fake_end_turn
    r._errs.clear()
    await r.handle_encerrar_animado("m", "id_que_nao_existe")
    check("recusa id fora da fila", len(r._errs) == 1)

    r, p = sala_com_servos(servo("s1", 14), servo("s2", 10))
    r.handle_end_turn = fake_end_turn
    r._errs.clear()
    await r.handle_encerrar_animado("m", "s1")
    await r.handle_encerrar_animado("m", "s1")
    check("recusa encerrar o mesmo servo duas vezes", len(r._errs) == 1)
    check("a vez do seguinte foi preservada", r._animados_atual("m") == "s2")

    # [13] end_turn continua fechando tudo de uma vez (rede do timer anti-AFK)
    print("\n[13] end_turn na janela fecha tudo")
    r, p = sala_com_servos(servo("s1", 14), servo("s2", 10))
    avancou = []
    async def fake_advance(): avancou.append(True)
    r._advance_initiative = fake_advance
    r.initiative_active = True
    await r.handle_end_turn("m")
    check("janela fechada", r.animados_phase_pid is None)
    check("fila limpa", r.animados_order == [] and r.animados_done == set())
    check("iniciativa avançou", avancou == [True])
```

- [ ] **Step 2: Rode o teste e confirme que falha**

```bash
python tools/test_reviver_mortos.py
```

Esperado: FALHA com `AttributeError: 'GameRoom' object has no attribute 'handle_encerrar_animado'`.

- [ ] **Step 3: Escreva o handler**

Em `server.py`, imediatamente APÓS o helper `_animados_atual` que você criou na
Task 1, insira:

```python
    async def handle_encerrar_animado(self, pid, animado_id):
        """Encerra a vez de UMA peça da janela pós-turno e passa à seguinte.

        Espelha o mestre_encerrar_monstro do Modo Mestre. Quando não sobra
        ninguém, delega a handle_end_turn: como animados_phase_pid já é este
        jogador, o bloco de abertura da janela é pulado pela própria condição
        que já está lá e a execução cai direto no fechamento.
        """
        if self.animados_phase_pid != pid:
            await self.send_to(pid, {"type": "error",
                "msg": T("erro.nao_ha_servo_seu_para_encerrar_agora")}); return
        if animado_id == "prisoner":
            pr = self.prisoner
            if (self.prisioneiro_done or not pr or not pr.get("freed")
                    or not pr.get("alive") or pr.get("rescuer_pid") != pid):
                await self.send_to(pid, {"type": "error",
                    "msg": T("erro.esta_peca_nao_esta_na_sua_fila")}); return
            self.prisioneiro_done = True
        else:
            if animado_id not in self.animados_order or animado_id in self.animados_done:
                await self.send_to(pid, {"type": "error",
                    "msg": T("erro.esta_peca_nao_esta_na_sua_fila")}); return
            self.animados_done.add(animado_id)
        if self._animados_atual(pid) is None:
            await self.handle_end_turn(pid)
            return
        await self.push_state()
```

- [ ] **Step 4: Registre a mensagem no dispatch WS**

Ache no dispatch:

```python
                elif t == "atacar_animado":
```

e insira ANTES desse bloco:

```python
                elif t == "encerrar_animado":
                    if room: await room.handle_encerrar_animado(pid, msg.get("animado_id"))

```

- [ ] **Step 5: Acrescente as duas chaves de recusa**

Em `src/lang/erros.js`, acrescente ao objeto (mantendo o estilo das entradas
vizinhas):

```javascript
  "erro.nao_ha_servo_seu_para_encerrar_agora": {
    pt: "Não há servo seu para encerrar agora.",
    en: "You have no minion to end right now."
  },
  "erro.esta_peca_nao_esta_na_sua_fila": {
    pt: "Esta peça não está na sua fila.",
    en: "That piece is not in your queue."
  },
```

- [ ] **Step 6: Rode o teste e confirme que passa**

```bash
python tools/test_reviver_mortos.py
```

Esperado: PASS nas seções `[11]`, `[12]`, `[13]`; `FAIL=0`.

- [ ] **Step 7: Rode a suíte de idioma para provar que não há chave órfã**

```bash
python tools/test_idioma.py
```

Esperado: `FAIL=0`. Se acusar chave órfã, você escreveu uma chave em `erros.js`
que nenhum `T(...)` usa — confira a grafia dos dois lados.

- [ ] **Step 8: Commit**

```bash
git add server.py src/lang/erros.js tools/test_reviver_mortos.py
git commit -m "feat(animados): mensagem encerrar_animado encadeia a fila de servos

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 3: Pular servo travado, narrando o motivo (servidor)

**Files:**
- Modify: `server.py` (`handle_encerrar_animado`, abertura da janela)
- Modify: `src/lang/narracao.js`
- Test: `tools/test_reviver_mortos.py`

- [ ] **Step 1: Escreva o teste que falha**

Em `tools/test_reviver_mortos.py`, antes do `print(f"\n{'='*40}...`, acrescente:

```python
    # [14] Servo travado é pulado com narração
    print("\n[14] saltos de servo travado")
    r, p = sala_com_servos(servo("s_rapido", 18),
                           servo("s_dorme", 14, dormindo=True),
                           servo("s_medio", 12))
    ditos = []
    async def cap_say(msg): ditos.append(msg)
    r.gm_say = cap_say
    async def fake_end_turn(pid): pass
    r.handle_end_turn = fake_end_turn
    check("dormindo não pode agir", r._animado_pode_agir(p["animados"][1]) is False)
    await r.handle_encerrar_animado("m", "s_rapido")
    check("pulou o adormecido", r._animados_atual("m") == "s_medio")
    check("adormecido marcado como encerrado", "s_dorme" in r.animados_done)
    check("narrou o salto", len(ditos) == 1)

    # [15] Servo que morre no meio da janela sai da fila
    print("\n[15] servo morto sai da fila")
    r, p = sala_com_servos(servo("s_a", 18), servo("s_b", 14), servo("s_c", 10))
    r.gm_say = cap_say
    r.handle_end_turn = fake_end_turn
    p["animados"][1]["vida_atual"] = 0     # s_b morreu por lava/retaliação
    await r.handle_encerrar_animado("m", "s_a")
    check("morto é pulado", r._animados_atual("m") == "s_c")

    # [16] Servo dominado por necromante não obedece
    print("\n[16] servo dominado sai da fila")
    r, p = sala_com_servos(servo("s_a", 18), servo("s_b", 14, dominado_por_monstro="mX"))
    r.gm_say = cap_say
    r.handle_end_turn = fake_end_turn
    await r.handle_encerrar_animado("m", "s_a")
    check("dominado não entra na vez", r._animados_atual("m") is None)
```

- [ ] **Step 2: Rode o teste e confirme que falha**

```bash
python tools/test_reviver_mortos.py
```

Esperado: FALHA em "adormecido marcado como encerrado" e em "narrou o salto" — o
`_animados_atual` já pula o adormecido (Task 1), mas ninguém o marca nem narra.

- [ ] **Step 3: Escreva o método que consome os travados**

Em `server.py`, imediatamente ANTES de `async def handle_encerrar_animado`,
insira:

```python
    async def _consumir_animados_travados(self, pid):
        """Tira da fila, narrando, todo servo que não tem como agir.

        Chamado ao abrir a janela e depois de cada encerramento, para o jogador
        só ser levado a peças jogáveis. Marcar em animados_done (em vez de só
        pular na derivação) mantém a contagem "servo N de M" honesta.
        """
        p = self.players.get(pid)
        if not p:
            return
        por_id = {a.get("id"): a for a in p.get("animados", [])}
        for aid in self.animados_order:
            if aid in self.animados_done:
                continue
            a = por_id.get(aid)
            if a is None or a.get("dominado_por_monstro"):
                self.animados_done.add(aid)
                continue
            if self._animado_pode_agir(a):
                break              # achou o da vez: para de consumir
            self.animados_done.add(aid)
            if a.get("vida_atual", 0) <= 0:
                motivo = T("narracao.servo_salto_morto")
            elif a.get("dormindo"):
                motivo = T("narracao.servo_salto_dormindo")
            else:
                motivo = T("narracao.servo_salto_preso")
            await self.gm_say(T("narracao.servo_perde_a_vez",
                                servo=a.get("nome") or a.get("tipo") or "?",
                                motivo=motivo))
```

- [ ] **Step 4: Chame-o nos dois pontos**

(a) Em `handle_encerrar_animado`, troque:

```python
        if self._animados_atual(pid) is None:
```

por:

```python
        await self._consumir_animados_travados(pid)
        if self._animados_atual(pid) is None:
```

(b) Na ABERTURA da janela em `handle_end_turn`, ache o par que você criou na
Task 1:

```python
            self.animados_done = set()
            self.prisioneiro_done = False
```

e acrescente logo abaixo:

```python
            await self._consumir_animados_travados(pid)
```

- [ ] **Step 5: Acrescente as quatro chaves de narração**

Em `src/lang/narracao.js`:

```javascript
  "narracao.servo_perde_a_vez": {
    pt: "💀 {servo} perde a vez — {motivo}.",
    en: "💀 {servo} loses its turn — {motivo}."
  },
  "narracao.servo_salto_morto": { pt: "está destruído", en: "is destroyed" },
  "narracao.servo_salto_dormindo": { pt: "está dormindo", en: "is asleep" },
  "narracao.servo_salto_preso": { pt: "está preso pelo rodamoinho", en: "is caught in the whirlpool" },
```

**Atenção:** o nome do parâmetro `{motivo}` tem de ser idêntico em `pt` e `en` —
há um teste que exige paridade de parâmetros entre os dois idiomas em TODAS as
chaves.

- [ ] **Step 6: Rode os testes**

```bash
python tools/test_reviver_mortos.py && python tools/test_idioma.py
```

Esperado: `FAIL=0` nos dois.

- [ ] **Step 7: Commit**

```bash
git add server.py src/lang/narracao.js tools/test_reviver_mortos.py
git commit -m "feat(animados): fila pula servo travado narrando o motivo

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 4: O prisioneiro fecha a fila (servidor)

**Files:**
- Modify: `server.py` (nada novo — só validação; o suporte já entrou nas Tasks 1–2)
- Test: `tools/test_reviver_mortos.py`

- [ ] **Step 1: Escreva o teste que falha**

Em `tools/test_reviver_mortos.py`, antes do `print(f"\n{'='*40}...`:

```python
    # [17] Prisioneiro é o último da fila
    print("\n[17] prisioneiro no fim da fila")
    r, p = sala_com_servos(servo("s_a", 18), servo("s_b", 12))
    r.prisoner = {"freed": True, "alive": True, "rescuer_pid": "m",
                  "pos": [2, 2], "moves_left": 6}
    fechou = []
    async def fake_end_turn(pid): fechou.append(pid)
    r.handle_end_turn = fake_end_turn
    await r.handle_encerrar_animado("m", "s_a")
    check("ainda em servo", r._animados_atual("m") == "s_b")
    await r.handle_encerrar_animado("m", "s_b")
    check("servos esgotados → prisioneiro", r._animados_atual("m") == "prisoner")
    check("janela ainda aberta", fechou == [])
    await r.handle_encerrar_animado("m", "prisoner")
    check("prisioneiro encerrado fecha a janela", fechou == ["m"])

    # [18] Prisioneiro de OUTRO resgatador não entra na minha fila
    print("\n[18] prisioneiro alheio")
    r, p = sala_com_servos(servo("s_a", 18))
    r.prisoner = {"freed": True, "alive": True, "rescuer_pid": "outro",
                  "pos": [2, 2], "moves_left": 6}
    r.handle_end_turn = fake_end_turn
    r._errs.clear()
    check("não aparece na minha vez",
          (r.animados_done.add("s_a"), r._animados_atual("m"))[1] is None)
    await r.handle_encerrar_animado("m", "prisoner")
    check("recusa encerrar prisioneiro alheio", len(r._errs) == 1)

    # [19] Prisioneiro morto no meio da janela não trava o fechamento
    print("\n[19] prisioneiro morto")
    r, p = sala_com_servos(servo("s_a", 18))
    r.prisoner = {"freed": True, "alive": True, "rescuer_pid": "m",
                  "pos": [2, 2], "moves_left": 6}
    fechou2 = []
    async def fake_end_turn2(pid): fechou2.append(pid)
    r.handle_end_turn = fake_end_turn2
    r.prisoner["alive"] = False
    await r.handle_encerrar_animado("m", "s_a")
    check("prisioneiro morto não segura a janela", fechou2 == ["m"])
```

- [ ] **Step 2: Rode o teste**

```bash
python tools/test_reviver_mortos.py
```

Esperado: PASS na seção `[17]`, `[18]` e `[19]` **sem escrever código novo** — o
ramo do prisioneiro já entrou em `_animados_atual` (Task 1) e em
`handle_encerrar_animado` (Task 2). Se alguma falhar, o bug está numa dessas duas
tasks e é aqui que ele aparece; conserte no lugar de origem.

- [ ] **Step 3: Commit**

```bash
git add tools/test_reviver_mortos.py
git commit -m "test(animados): prisioneiro fecha a fila da janela pos-turno

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 5: O cliente espelha a fila (`gameState.js` + `game.js`)

**Files:**
- Modify: `src/gameState.js` (novo sender `encerrarAnimado`, novo predicado `animadoPendenteParaEncerrar`, exports)
- Modify: `game.js` (gancho de `gameState`)

- [ ] **Step 1: Escreva o sender em `src/gameState.js`**

Ache a função `endTurn()` (procure por `function endTurn()       {`) e insira
IMEDIATAMENTE ANTES dela:

```javascript
  // ── Janela pós-turno do mago: a fila de servos ─────────────────────────────
  // O servidor é quem manda: `animados_atual` no game_state diz quem eu controlo
  // agora (id do servo, "prisoner", ou null). Estes dois helpers são a única
  // fonte da decisão "encerrar servo vs. encerrar turno" no cliente.
  function encerrarAnimado(animadoId) {
    return send({ type: 'encerrar_animado', animado_id: animadoId });
  }

  function animadoAtual() {
    // DICT POR PID, não escalar: o game_state é montado UMA vez para a sala
    // inteira (_game_state_payload não recebe pid), então cada jogador lê a
    // própria entrada. Ver Task 1, Step 7.
    return gameState?.animados_atual?.[myPid] ?? null;
  }

  // Devolve a peça cuja vez o botão de encerrar deve fechar, ou null quando o
  // botão significa "encerrar o turno do herói". `selId` é a seleção visual do
  // renderer (o jogador pode ter clicado noutro servo, e a fila respeita isso).
  function animadoPendenteParaEncerrar(selId) {
    if (!gameState || gameState.animados_turn !== myPid) return null;
    const atual = animadoAtual();
    if (atual == null) return null;
    if (selId == null) return atual;
    if (selId === 'prisoner') return 'prisoner';
    const me = (gameState.players || []).find(p => p.id === myPid);
    const vivo = (me?.animados || []).some(
      a => a && a.id === selId && a.vida_atual > 0 && !a.dominado_por_monstro);
    return vivo ? selId : atual;
  }
```

- [ ] **Step 2: Exporte os três no objeto público**

Ache no bloco de exports:

```javascript
    endTurn,
```

e insira ANTES dessa linha:

```javascript
    encerrarAnimado,
    animadoAtual,
    animadoPendenteParaEncerrar,
```

- [ ] **Step 3: Faça a seleção do cliente seguir `animados_atual`**

Em `game.js`, ache no gancho `GS.on('gameState', ...)` o bloco que começa com:

```javascript
  // Entrou na minha janela de controle (servos e/ou prisioneiro) → dica única.
  if (msg.animados_turn === GS.myPid && _lastAnimadosTurn !== GS.myPid) {
```

Substitua o bloco INTEIRO (da linha do comentário até a chave `}` que fecha esse
`if`, logo depois da linha `if (mode3D && g3) renderMap3D(msg); else renderMap(msg);`)
por:

```javascript
  // A fila é do servidor: `animados_atual` diz quem eu controlo agora. Espelhar
  // isso na seleção é o que faz o próximo servo ser escolhido sozinho quando o
  // anterior encerra — antes isso só acontecia na abertura da janela.
  const _entrouNaJanela = (msg.animados_turn === GS.myPid && _lastAnimadosTurn !== GS.myPid);
  const _atualServo = (msg.animados_turn === GS.myPid) ? (msg.animados_atual?.[GS.myPid] ?? null) : null;
  if (_atualServo !== _lastAnimadosAtual || _entrouNaJanela) {
    if (_atualServo === 'prisoner') {
      _animadoSel = null;
      _prisSel = true;
      toast(t('ui.hud.mova_prisioneiro'));
    } else if (_atualServo != null) {
      _animadoSel = _atualServo;
      _prisSel = false;
      const nome = (msg.players.find(p => p.id === GS.myPid)?.animados || [])
        .find(a => a.id === _atualServo)?.nome || '';
      toast(t('ui.animar.turno_servos') + ' ' + t('ui.animar.servo_selecionado', {nome}));
    }
    if (mode3D && g3) renderMap3D(msg); else renderMap(msg);
  }
  _lastAnimadosAtual = _atualServo;
```

- [ ] **Step 4: Declare a variável nova ao lado das irmãs**

Ache em `game.js`:

```javascript
let _animadoSel = null;
```

e acrescente logo abaixo:

```javascript
let _lastAnimadosAtual = null;   // último `animados_atual` visto (espelha a fila do servidor)
```

- [ ] **Step 5: Limpe a variável no fechamento da janela**

Ache o bloco:

```javascript
  // Janela de controle encerrou → limpa seleções.
  if (_lastAnimadosTurn === GS.myPid && msg.animados_turn !== GS.myPid) {
    _animadoSel = null;
    _prisSel = false;
  }
```

e acrescente `_lastAnimadosAtual = null;` dentro do `if`, depois de `_prisSel = false;`.

- [ ] **Step 6: Verifique a sintaxe dos dois arquivos**

```bash
node --check game.js && node --check src/gameState.js
```

Esperado: nenhuma saída (sucesso). **Se você editou com o servidor rodando, a
escrita pode ter falhado em silêncio e o `node --check` valida o arquivo antigo**
— confirme com `git diff --stat game.js src/gameState.js` que as mudanças estão
mesmo lá.

- [ ] **Step 7: Commit**

```bash
git add game.js src/gameState.js
git commit -m "feat(animados): cliente espelha a fila do servidor na selecao

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 6: O botão de encerrar encadeia a fila

**Files:**
- Modify: `game.js` (`endTurn`, `_atualizarBotaoEncerrarTurno`, tecla Enter)
- Modify: `src/lang/interface.js`

- [ ] **Step 1: Faça `endTurn()` despachar para a fila**

Em `game.js`, ache:

```javascript
function endTurn(){
  const btn = $('btn-end-turn');
  // A validação visual continua sendo feita em renderMyPanel; esta guarda evita
  // que um clique atrasado envie um turno fora da vez do jogador.
  if(!btn || btn.disabled) return;
  getAudioContext();
  if(!GS.endTurn()) toast(t('ui.conexao.sem_servidor'), 'var(--red)');
}
```

e troque por:

```javascript
function endTurn(){
  const btn = $('btn-end-turn');
  // A validação visual continua sendo feita em renderMyPanel; esta guarda evita
  // que um clique atrasado envie um turno fora da vez do jogador.
  if(!btn || btn.disabled) return;
  getAudioContext();
  // Na janela pós-turno do mago, este botão encerra a vez de UMA peça e o
  // servidor seleciona a próxima. Só a última fecha a janela. A decisão mora em
  // gameState.js; aqui só passamos a seleção visual atual.
  const peca = GS.animadoPendenteParaEncerrar(_prisSel ? 'prisoner' : _animadoSel);
  const ok = (peca != null) ? GS.encerrarAnimado(peca) : GS.endTurn();
  if(!ok) toast(t('ui.conexao.sem_servidor'), 'var(--red)');
}
```

- [ ] **Step 2: Faça a tecla Enter usar o mesmo caminho**

Ache:

```javascript
    case 'Enter': if(GS.isMyTurn) GS.endTurn();           break;
```

e troque por:

```javascript
    case 'Enter': if(GS.isMyTurn) endTurn();              break;
```

**Por quê:** `GS.endTurn()` direto pularia o despacho da fila, e a tecla passaria
a fechar a janela inteira enquanto o botão encadeia — dois comportamentos para o
mesmo gesto.

- [ ] **Step 3: Dê ao botão um rótulo que conte a fila**

Ache:

```javascript
function _atualizarBotaoEncerrarTurno(state){
  const btn = document.getElementById('btn-end-turn');
  if(!btn) return;
  const me = (state?.players || []).find(p => p.id === GS.myPid);
  const podeEncerrar = !!(me && me.alive !== false && state?.phase === 'playing'
    && (GS.isMyTurn || state.current_turn === GS.myPid
        || state.last_stand_pid === GS.myPid
        || state.animados_turn === GS.myPid));
  btn.disabled = !podeEncerrar;
}
```

e troque por:

```javascript
function _atualizarBotaoEncerrarTurno(state){
  const btn = document.getElementById('btn-end-turn');
  if(!btn) return;
  const me = (state?.players || []).find(p => p.id === GS.myPid);
  const podeEncerrar = !!(me && me.alive !== false && state?.phase === 'playing'
    && (GS.isMyTurn || state.current_turn === GS.myPid
        || state.last_stand_pid === GS.myPid
        || state.animados_turn === GS.myPid));
  btn.disabled = !podeEncerrar;

  // Rótulo dinâmico durante a janela dos servos: "⏭ Encerrar servo (2/3)".
  // `_i18nApply` sobrescreve o textContent de todo [data-i18n], então o atributo
  // SAI enquanto o texto é calculado e VOLTA quando não é mais. Esta função roda
  // a cada game_state, e a troca de idioma reenvia o estado — então o rótulo
  // acompanha o idioma sozinho, sem entrar na lista do _setLang.
  const span = btn.querySelector('span');
  if(!span) return;
  // Dict por pid (ver Task 1, Step 7): cada jogador lê a própria entrada.
  const atual = state?.animados_atual?.[GS.myPid] ?? null;
  const naFila = state?.animados_turn === GS.myPid && atual !== null;
  if(naFila){
    const ordem = state.animados_order || [];
    const total = ordem.length + (_temPrisioneiroNaFila(state) ? 1 : 0);
    // A posição é o índice do servo da vez na ordem de iniciativa. O prisioneiro
    // não está em `animados_order`: ele é sempre o último da fila.
    const idx = ordem.indexOf(atual);
    const pos = (idx >= 0) ? idx + 1 : total;
    span.removeAttribute('data-i18n');
    span.textContent = atual === 'prisoner'
      ? t('ui.hud.encerrar_prisioneiro')
      : t('ui.hud.encerrar_servo', {pos, total});
  } else if(!span.hasAttribute('data-i18n')){
    span.setAttribute('data-i18n', 'ui.hud.encerrar_turno');
    span.textContent = t('ui.hud.encerrar_turno');
  }
}

// O prisioneiro liberto ocupa a última posição da fila da janela pós-turno.
function _temPrisioneiroNaFila(state){
  const pr = state?.prisoner;
  return !!(pr && pr.alive && pr.freed && pr.rescuer_pid === GS.myPid);
}
```

- [ ] **Step 4: Acrescente as duas chaves de interface**

Em `src/lang/interface.js`:

```javascript
  "ui.hud.encerrar_servo": {
    pt: "⏭ Encerrar servo ({pos}/{total})",
    en: "⏭ End minion ({pos}/{total})"
  },
  "ui.hud.encerrar_prisioneiro": {
    pt: "⏭ Encerrar prisioneiro",
    en: "⏭ End prisoner"
  },
```

- [ ] **Step 5: Verifique a sintaxe e as suítes de idioma do cliente**

```bash
node --check game.js && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: **baseline inalterado** — `test_idioma_cliente` 31/1 e
`test_vocabulario_cliente` 54/1 (ver a tabela de baseline no topo). Se o número
de falhas subir, a chave nova é sua.

- [ ] **Step 6: Rode o placar de interface**

```bash
python tools/test_interface.py
```

Esperado: **baseline inalterado** — 31/5, com o contador de literais em
`game.js` ainda em **206**. Se o contador subir, você deixou texto cru em vez de
`t('ui....')`; conserte só o que você acrescentou. As 5 falhas pré-existentes
não são suas.

- [ ] **Step 7: Commit**

```bash
git add game.js src/lang/interface.js
git commit -m "feat(animados): botao de encerrar encadeia a fila de servos

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 7: Uma regra só para o alcance de ataque do servo

**Files:**
- Modify: `src/gameState.js` (nova função pura + export)
- Modify: `game.js` (render 2D, render 3D, `handleTileClick`)

**Por que esta task existe:** o alcance de ataque de um servo está escrito em
**três** lugares no cliente hoje, e eles já divergem entre si e do servidor:

| Lugar | Regra atual | Confere com o servidor? |
|---|---|---|
| `handleTileClick` (ramo de servo) | honra `attacks[0].range`/`range_shape`; corpo a corpo = Chebyshev (aceita diagonal) | **não** — o servidor usa `_cardinal_adjacent` (só as 4 ortogonais) |
| render 2D (`atkRefAnimado2D`) | cardinal, alcance 1 (ou 3 se `especial === 'linha_3q'`) | só para servos não-elementais |
| render 3D (`atkRefAnimado3D`) | idem 2D | idem |

Resultado hoje: o realce mente para servo elemental de alcance maior, e clicar
num monstro na diagonal com servo corpo a corpo manda uma mensagem que o
servidor recusa. O joystick seria a quarta cópia.

- [ ] **Step 1: Escreva a função pura em `src/gameState.js`**

Ache `function attackTargetTiles() {` e insira IMEDIATAMENTE ANTES dela:

```javascript
  // Casas que o servo animado/elemental selecionado pode atacar.
  //
  // Fonte ÚNICA da regra no cliente — consumida pelo render 2D, pelo render 3D,
  // pelo clique do tabuleiro e pelo joystick. Espelha os três ramos que o
  // servidor valida em handle_atacar_animado:
  //   1. elemental com ficha completa  → _animado_attack_in_range
  //   2. legado `especial: 'linha_3q'` → _em_linha_cardinal(..., 3)
  //   3. o resto (corpo a corpo)       → _cardinal_adjacent (só as 4 ortogonais)
  //
  // Simplificação conhecida e aceita: não modela custo vertical de terreno nem
  // footprint 2×2 (o servidor modela). O realce pode oferecer uma casa que o
  // servidor recusa; a recusa chega como erro normal e nada fica inconsistente.
  function animadoAttackTargetTiles(animado) {
    if (!gameState || !animado || !animado.pos || animado.vida_atual <= 0) return [];
    const [ax, ay] = animado.pos;
    const atk = (animado.attacks || [])[0] || {};
    const alcance = Number(atk.range || 0);
    const emLinha = !!atk.range_shape;
    const out = [], seen = new Set();
    const push = (x, y, targetId) => {
      const key = `${x},${y}`;
      if (seen.has(key)) return;
      seen.add(key);
      out.push({ x, y, targetId });
    };
    for (const monster of gameState.monsters || []) {
      if (!monster || monster.hp <= 0) continue;
      for (const [tx, ty] of monsterTiles(monster)) {
        const dx = Math.abs(ax - tx), dy = Math.abs(ay - ty);
        const dist = Math.max(dx, dy);
        const cardinal = (dx === 0 || dy === 0);
        let ok;
        if (animado.especial === 'linha_3q' && !alcance) {
          ok = cardinal && dist >= 1 && dist <= 3;
        } else if (alcance) {
          ok = emLinha ? (cardinal && dist >= 1 && dist <= alcance)
                       : (dist >= 1 && dist <= alcance);
          if (ok) ok = hasLineOfSight(gameState, ax, ay, tx, ty);
        } else {
          ok = cardinal && dist === 1;
        }
        if (ok) push(tx, ty, monster.id);
      }
    }
    return out;
  }
```

- [ ] **Step 2: Exporte-a**

No bloco de exports, ache a linha `    encerrarAnimado,` (criada na Task 5) e
acrescente logo abaixo:

```javascript
    animadoAttackTargetTiles,
```

- [ ] **Step 3: Faça o render 2D usar a função**

Em `game.js`, ache:

```javascript
  const atkRefAnimado2D = selAnimado2D || window._animadoHover;
  if(atkRefAnimado2D && atkRefAnimado2D.pos){
    const [ax,ay]=atkRefAnimado2D.pos;
    const isElec2D = atkRefAnimado2D.especial === 'linha_3q';
    const atkRange2D = isElec2D ? 3 : 1;
    for(const [ddx,ddy] of [[1,0],[-1,0],[0,1],[0,-1]])
      for(let r=1; r<=atkRange2D; r++)
        attackable.add(`${ax+ddx*r},${ay+ddy*r}`);
  }
```

e troque por:

```javascript
  // Regra única em GS.animadoAttackTargetTiles — antes esta cópia cravava
  // "cardinal, alcance 1 (ou 3)" e mentia para servos elementais de alcance maior.
  const atkRefAnimado2D = selAnimado2D || window._animadoHover;
  for(const alvo of GS.animadoAttackTargetTiles(atkRefAnimado2D))
    attackable.add(`${alvo.x},${alvo.y}`);
```

- [ ] **Step 4: Faça o render 3D usar a função**

Ache:

```javascript
  const atkRefAnimado3D = selAnimado3D || window._animadoHover;
  if(atkRefAnimado3D && atkRefAnimado3D.pos){
    const [ax3,ay3] = atkRefAnimado3D.pos;
    const isElec3D = atkRefAnimado3D.especial === 'linha_3q';
    const atkRange3D = isElec3D ? 3 : 1;
    for(const [ddx,ddy] of [[1,0],[-1,0],[0,1],[0,-1]])
      for(let r=1; r<=atkRange3D; r++)
        attackable3d.add(`${ax3+ddx*r},${ay3+ddy*r}`);
  }
```

e troque por:

```javascript
  // Mesma fonte do 2D — ver GS.animadoAttackTargetTiles.
  const atkRefAnimado3D = selAnimado3D || window._animadoHover;
  for(const alvo of GS.animadoAttackTargetTiles(atkRefAnimado3D))
    attackable3d.add(`${alvo.x},${alvo.y}`);
```

- [ ] **Step 5: Faça o clique do tabuleiro usar a função**

Em `handleTileClick`, ache:

```javascript
            const dx_a = Math.abs(a.pos[0]-mon.pos[0]), dy_a = Math.abs(a.pos[1]-mon.pos[1]);
            const ataqueA = (a.attacks || [])[0] || {};
            const alcanceA = Number(ataqueA.range || 0);
            const distA = Math.max(dx_a, dy_a);
            const emLinhaA = (dx_a === 0 || dy_a === 0) && distA >= 1 && distA <= alcanceA;
            const emAlcanceA = alcanceA
              ? (ataqueA.range_shape ? emLinhaA : distA >= 1 && distA <= alcanceA)
              : distA === 1;
            if(emAlcanceA) GS.atacarAnimado(a.id, mon.id);
```

e troque por:

```javascript
            const ataqueA = (a.attacks || [])[0] || {};
            const alcanceA = Number(ataqueA.range || 0);
            // Mesma regra do realce (e do servidor): corpo a corpo é CARDINAL.
            // Antes esta cópia aceitava a diagonal e mandava um ataque que o
            // servidor recusava com "servo não está adjacente ao alvo".
            const emAlcanceA = GS.animadoAttackTargetTiles(a)
              .some(alvo => alvo.x === mon.pos[0] && alvo.y === mon.pos[1]);
            if(emAlcanceA) GS.atacarAnimado(a.id, mon.id);
```

- [ ] **Step 6: Verifique a sintaxe**

```bash
node --check game.js && node --check src/gameState.js
```

Esperado: nenhuma saída.

- [ ] **Step 7: Commit**

```bash
git add game.js src/gameState.js
git commit -m "refactor(animados): regra unica de alcance de ataque do servo

Corrige o realce que mentia para servos elementais de alcance maior e o
clique que aceitava diagonal em corpo a corpo, que o servidor recusa.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 8: O joystick ancora na peça da vez

**Files:**
- Modify: `src/gameState.js` (`pecaControlada` + export)
- Modify: `game.js` (`_gamepadEnsureCursor`)

- [ ] **Step 1: Escreva `pecaControlada` em `src/gameState.js`**

Insira logo abaixo de `animadoPendenteParaEncerrar` (Task 5):

```javascript
  // Quem o controle dirige AGORA: a peça da vez na janela pós-turno, ou o herói
  // fora dela. Devolve { kind, id, pos, moves_left, ref } ou null.
  // `kind` é 'hero' | 'animado' | 'prisoner'.
  function pecaControlada() {
    if (!gameState || !isMyTurn) return null;
    const me = (gameState.players || []).find(p => p.id === myPid && p.alive);
    if (gameState.animados_turn === myPid) {
      const atual = animadoAtual();
      if (atual === 'prisoner') {
        const pr = gameState.prisoner;
        if (!pr || !pr.alive) return null;
        return { kind: 'prisoner', id: 'prisoner', pos: pr.pos,
                 moves_left: pr.moves_left || 0, ref: pr };
      }
      const a = (me?.animados || []).find(x => x && x.id === atual);
      if (!a) return null;
      return { kind: 'animado', id: a.id, pos: a.pos,
               moves_left: a.moves_left || 0, ref: a };
    }
    if (!me) return null;
    return { kind: 'hero', id: me.id, pos: me.pos,
             moves_left: me.moves_left || 0, ref: me };
  }
```

- [ ] **Step 2: Exporte-a**

Acrescente `pecaControlada,` logo abaixo de `animadoAttackTargetTiles,` no bloco
de exports.

- [ ] **Step 3: Faça o cursor ancorar nessa peça**

Em `game.js`, ache a função inteira:

```javascript
function _gamepadEnsureCursor(state){
  if(!state?.tiles?.length) return null;
  const W = state.tiles[0].length, H = state.tiles.length;
  const me = state.players?.find(p => p.id === GS.myPid && p.alive);
  const board = _gamepadBoard(state);
  const playerKey = me?.pos ? `${board}:${me.id}:${me.pos[0]},${me.pos[1]}` : '';
  const valid = Array.isArray(_gamepadInput.cursor)
    && _gamepadInput.cursor[0] >= 0 && _gamepadInput.cursor[1] >= 0
    && _gamepadInput.cursor[0] < W && _gamepadInput.cursor[1] < H;
  // Todo deslocamento do herói reinicia o cursor sobre ele. O jogador pode
  // então explorar com o analógico direito sem o cursor ficar esquecido fora
  // da tela após uma caminhada longa.
  if(!valid || _gamepadInput.cursorBoard !== board || _gamepadInput.cursorPlayerKey !== playerKey){
    _gamepadInput.cursor = me?.pos ? [...me.pos] : [0, 0];
    _gamepadInput.cursorBoard = board;
    _gamepadInput.cursorPlayerKey = playerKey;
  }
  return _gamepadInput.cursor;
}
```

e troque por:

```javascript
function _gamepadEnsureCursor(state){
  if(!state?.tiles?.length) return null;
  const W = state.tiles[0].length, H = state.tiles.length;
  // A âncora é a PEÇA CONTROLADA, não o herói: na janela pós-turno do mago ela
  // é o servo (ou o prisioneiro) da vez. Como o id entra na chave, trocar de
  // servo joga o cursor sobre o servo novo — é isso que faz o encadeamento
  // parecer automático no controle.
  const peca = GS.pecaControlada();
  const me = state.players?.find(p => p.id === GS.myPid && p.alive);
  const ancora = peca || (me ? {id: me.id, pos: me.pos} : null);
  const board = _gamepadBoard(state);
  const playerKey = ancora?.pos ? `${board}:${ancora.id}:${ancora.pos[0]},${ancora.pos[1]}` : '';
  const valid = Array.isArray(_gamepadInput.cursor)
    && _gamepadInput.cursor[0] >= 0 && _gamepadInput.cursor[1] >= 0
    && _gamepadInput.cursor[0] < W && _gamepadInput.cursor[1] < H;
  if(!valid || _gamepadInput.cursorBoard !== board || _gamepadInput.cursorPlayerKey !== playerKey){
    _gamepadInput.cursor = ancora?.pos ? [...ancora.pos] : [0, 0];
    _gamepadInput.cursorBoard = board;
    _gamepadInput.cursorPlayerKey = playerKey;
  }
  return _gamepadInput.cursor;
}
```

- [ ] **Step 4: Verifique a sintaxe**

```bash
node --check game.js && node --check src/gameState.js
```

Esperado: nenhuma saída.

- [ ] **Step 5: Commit**

```bash
git add game.js src/gameState.js
git commit -m "feat(joystick): cursor ancora na peca da vez, nao no heroi

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 9: Prévia de rota do servo no joystick

**Files:**
- Modify: `game.js` (`_selecionarPreviaMovimento`, `_gamepadAtualizarPreviaMovimento`, ramo de servo do `handleTileClick`)

- [ ] **Step 1: Parametrize `_selecionarPreviaMovimento`**

Em `game.js`, ache:

```javascript
function _selecionarPreviaMovimento(action, tx, ty, notify=true){
  const st = GS.gameState;
  const me = st?.players?.find(p => p.id === GS.myPid && p.alive);
  if(!me || !action?.path?.length) return false;
  GS.pendingMove = {
    target: [tx, ty],
    path: action.path.map(step => [step[0], step[1]]),
    stopAtDoor: !!action.stopAtDoor,
    origin: [me.pos[0], me.pos[1]],
    moves_left: Number(me.moves_left) || 0
  };
  renderMap(st);
  if(notify) toast('👣 Clique novamente na casa para confirmar · Esc cancela', 'var(--gold)');
  return true;
}
```

e troque por:

```javascript
// `peca` opcional: quando vem preenchida (GS.pecaControlada()), a prévia é da
// peça controlada — o servo da vez na janela pós-turno — em vez do herói.
function _selecionarPreviaMovimento(action, tx, ty, notify=true, peca=null){
  const st = GS.gameState;
  const me = st?.players?.find(p => p.id === GS.myPid && p.alive);
  const origem = peca || me;
  if(!origem?.pos || !action?.path?.length) return false;
  GS.pendingMove = {
    target: [tx, ty],
    path: action.path.map(step => [step[0], step[1]]),
    stopAtDoor: !!action.stopAtDoor,
    origin: [origem.pos[0], origem.pos[1]],
    moves_left: Number(origem.moves_left) || 0,
    animadoId: (peca && peca.kind !== 'hero') ? peca.id : null
  };
  renderMap(st);
  if(notify) toast(t('ui.tabuleiro.clique_novamente_para_confirmar'), 'var(--gold)');
  return true;
}
```

**Atenção:** se `ui.tabuleiro.clique_novamente_para_confirmar` já não existir em
`src/lang/interface.js`, acrescente:

```javascript
  "ui.tabuleiro.clique_novamente_para_confirmar": {
    pt: "👣 Clique novamente na casa para confirmar · Esc cancela",
    en: "👣 Click the tile again to confirm · Esc cancels"
  },
```

Verifique antes com:

```bash
grep -n "clique_novamente_para_confirmar" src/lang/interface.js
```

- [ ] **Step 2: Faça a prévia do joystick usar a peça da vez**

Ache:

```javascript
function _gamepadAtualizarPreviaMovimento(state){
  if(!GS.isMyTurn || _gamepadInput.attackMode || _aimAlgumModoAtivo()
    || window._modoInstrumento || window._modoMagia || window._modoAnimarMortos
    || window._modoThrowItem || window._modoPlacementArmadilha
    || GS.pendingSkill || GS.pendingInstrumento || GS.pendingThrow) return;
  const cursor = _gamepadEnsureCursor(state);
  if(!cursor) return;
  const action = GS.resolveTileClick(cursor[0], cursor[1]);
  if(action?.type === 'move'){
    _selecionarPreviaMovimento(action, cursor[0], cursor[1], false);
  } else if(GS.pendingMove){
    GS.pendingMove = null;
    _clearMovePreviewVisual();
  }
}
```

e troque por:

```javascript
function _gamepadAtualizarPreviaMovimento(state){
  if(!GS.isMyTurn || _gamepadInput.attackMode || _aimAlgumModoAtivo()
    || window._modoInstrumento || window._modoMagia || window._modoAnimarMortos
    || window._modoThrowItem || window._modoPlacementArmadilha
    || GS.pendingSkill || GS.pendingInstrumento || GS.pendingThrow) return;
  const cursor = _gamepadEnsureCursor(state);
  if(!cursor) return;
  const peca = GS.pecaControlada();
  // Servo/prisioneiro: GS.resolveTileClick é do HERÓI e não serve aqui. A rota
  // sai do mesmo GS.findPath sobre o orçamento da peça que o clique do mouse já
  // usa no ramo de servo do handleTileClick.
  if(peca && peca.kind !== 'hero'){
    const exp = new Set((state.explored || []).map(([x, y]) => `${x},${y}`));
    for(const [rx, ry] of (state.revealed || [])) exp.add(`${rx},${ry}`);
    const passos = GS.findPath(state.tiles, exp, peca.pos[0], peca.pos[1],
                               cursor[0], cursor[1], peca.moves_left);
    if(passos && passos.length){
      _selecionarPreviaMovimento({type:'move', path:passos}, cursor[0], cursor[1], false, peca);
    } else if(GS.pendingMove){
      GS.pendingMove = null;
      _clearMovePreviewVisual();
    }
    return;
  }
  const action = GS.resolveTileClick(cursor[0], cursor[1]);
  if(action?.type === 'move'){
    _selecionarPreviaMovimento(action, cursor[0], cursor[1], false);
  } else if(GS.pendingMove){
    GS.pendingMove = null;
    _clearMovePreviewVisual();
  }
}
```

- [ ] **Step 3: Limpe a prévia ao mover o servo pelo clique**

O ramo de servo do `handleTileClick` roda **antes** da leitura de
`GS.pendingMove`. Sem isto, uma prévia confirmada por A move o servo e deixa a
prévia pendurada na tela.

Em `handleTileClick`, ache as duas chamadas de movimento do ramo de servo e
limpe a prévia antes de cada uma.

(a) Prisioneiro — ache:

```javascript
      if(passosP && passosP.length){ _animarEEnviarMoverPrisioneiroCaminho(_prisC, passosP); return; }
```

e troque por:

```javascript
      if(passosP && passosP.length){
        GS.pendingMove = null; _clearMovePreviewVisual();
        _animarEEnviarMoverPrisioneiroCaminho(_prisC, passosP); return;
      }
```

(b) Servo — ache:

```javascript
          if(passosMin && passosMin.length){ _animarEEnviarMoverCaminhoMinino(a, passosMin); return; }
```

e troque por:

```javascript
          if(passosMin && passosMin.length){
            GS.pendingMove = null; _clearMovePreviewVisual();
            _animarEEnviarMoverCaminhoMinino(a, passosMin); return;
          }
```

- [ ] **Step 4: Verifique a sintaxe e o placar de interface**

```bash
node --check game.js && python tools/test_interface.py
```

Esperado: nenhuma saída do `node`; `test_interface` no baseline 31/5 com o
contador de literais ainda em **206**.

- [ ] **Step 5: Commit**

```bash
git add game.js src/lang/interface.js
git commit -m "feat(joystick): previa de rota do servo da vez

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 10: Mira, encerramento e contexto do joystick na janela

**Files:**
- Modify: `game.js` (`_gamepadAttackTargets`, `_gamepadEnterAttackMode`, `_gamepadRequestEndTurn`, `_gamepadAccept`, `_gamepadUsefulTargetTiles`, `_gamepadContexto`)
- Modify: `src/lang/interface.js`

- [ ] **Step 1: Faça a mira usar os alvos do servo**

Em `game.js`, ache:

```javascript
function _gamepadAttackTargets(){
  return GS.attackTargetTiles?.() || [];
}
```

e troque por:

```javascript
function _gamepadAttackTargets(){
  // Na janela pós-turno o alvo é do SERVO da vez, pela mesma regra do realce.
  const peca = GS.pecaControlada();
  if(peca?.kind === 'animado') return GS.animadoAttackTargetTiles(peca.ref) || [];
  if(peca?.kind === 'prisoner') return [];   // o prisioneiro só se move
  return GS.attackTargetTiles?.() || [];
}
```

- [ ] **Step 2: Corrija a âncora do modo de ataque**

Em `_gamepadEnterAttackMode`, ache:

```javascript
  const cursor = _gamepadEnsureCursor(state);
  const me = state.players?.find(p => p.id === GS.myPid && p.alive);
  const [ox, oy] = cursor || me?.pos || [0, 0];
```

e troque por:

```javascript
  const cursor = _gamepadEnsureCursor(state);
  const peca = GS.pecaControlada();
  const [ox, oy] = cursor || peca?.pos || [0, 0];
```

- [ ] **Step 3: Tire a dupla-pressão de confirmação durante a fila**

Ache:

```javascript
function _gamepadRequestEndTurn(now){
  if(now <= _gamepadEndTurnConfirmUntil){
```

e troque por:

```javascript
function _gamepadRequestEndTurn(now){
  // Encerrar a vez de UM servo não é destrutivo — só passa a peça adiante. Pedir
  // dupla-pressão aqui dobraria os apertos de uma fila de 3 servos para 6.
  if(GS.animadoPendenteParaEncerrar(_prisSel ? 'prisoner' : _animadoSel) != null){
    _clearGamepadEndTurnConfirm();
    _gamepadRumble('endTurn');
    endTurn();
    return;
  }
  if(now <= _gamepadEndTurnConfirmUntil){
```

- [ ] **Step 4: Deixe inertes os atalhos que só servem ao herói**

(a) Em `_gamepadAccept`, ache:

```javascript
  if(_gamepadInteractAtCursor(state)) return;
  if(_gamepadEnterAttackMode(state)) return;
```

e troque por:

```javascript
  // Baú, item no chão e ciclo de alvos são do HERÓI e ancoram em me.pos: na
  // janela pós-turno eles agiriam pela peça errada.
  const _naJanelaServos = state?.animados_turn === GS.myPid;
  if(!_naJanelaServos && _gamepadInteractAtCursor(state)) return;
  if(_gamepadEnterAttackMode(state)) return;
```

(b) Em `_gamepadUsefulTargetTiles`, ache a primeira linha do corpo:

```javascript
  const me = state?.players?.find(p => p.id === GS.myPid && p.alive);
  if(!state || !me || !GS.isMyTurn) return [];
```

e troque por:

```javascript
  const me = state?.players?.find(p => p.id === GS.myPid && p.alive);
  if(!state || !me || !GS.isMyTurn) return [];
  if(state.animados_turn === GS.myPid) return [];   // fila de servos: sem ciclo do herói
```

- [ ] **Step 5: Rotule a peça da vez no HUD do controle**

Ache a função `_gamepadContexto` (procure por
`if(!GS.isMyTurn) return label('ui.joystick.contexto_aguarde', '⏳');`) e insira
IMEDIATAMENTE APÓS essa linha:

```javascript
  const _pecaCtx = GS.pecaControlada();
  if(_pecaCtx && _pecaCtx.kind !== 'hero' && !_gamepadInput.attackMode){
    return { icon: _pecaCtx.kind === 'prisoner' ? '🔗' : '☠️',
             text: t('ui.joystick.contexto_peca_da_vez', {
               nome: _pecaCtx.kind === 'prisoner'
                 ? t('ui.hud.prisioneiro')
                 : (_pecaCtx.ref.nome || _pecaCtx.ref.tipo || ''),
               mov: _pecaCtx.moves_left }) };
  }
```

- [ ] **Step 6: Acrescente a chave do contexto**

Em `src/lang/interface.js`:

```javascript
  "ui.joystick.contexto_peca_da_vez": {
    pt: "{nome} · {mov} mov",
    en: "{nome} · {mov} mov"
  },
```

Confira se `ui.hud.prisioneiro` já existe:

```bash
grep -n "\"ui.hud.prisioneiro\"" src/lang/interface.js
```

Se não existir, acrescente:

```javascript
  "ui.hud.prisioneiro": { pt: "Prisioneiro", en: "Prisoner" },
```

- [ ] **Step 7: Rode a verificação do cliente**

```bash
node --check game.js && node tools/test_idioma_cliente.js && python tools/test_interface.py
```

Esperado: nenhuma saída do `node --check`; `test_idioma_cliente` 31/1 e
`test_interface` 31/5 (206 literais) — baseline inalterado.

- [ ] **Step 8: Commit**

```bash
git add game.js src/lang/interface.js
git commit -m "feat(joystick): mira, encerramento e contexto da peca da vez

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 11: Verificação final

**Files:** nenhum (só execução)

- [ ] **Step 1: Rode as suítes tocadas por esta mudança**

```bash
python tools/test_reviver_mortos.py && python tools/test_idioma.py && python tools/test_narracao.py && python tools/test_erros.py && python tools/test_interface.py && python tools/test_vocabulario.py
```

Esperado, comparando com a tabela de baseline do topo:

| Suíte | Tem de ficar |
|---|---|
| `test_reviver_mortos` | **FAIL=0** (e com mais checks que os 32 do baseline) |
| `test_idioma` | **FAIL=0** |
| `test_vocabulario` | **FAIL=0** |
| `test_narracao` | 2 falhas, contadores ainda **28** e **43** |
| `test_erros` | 1 falha |
| `test_interface` | 5 falhas, contador ainda **206** |

- [ ] **Step 2: Rode as suítes de cliente**

```bash
node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `test_idioma_cliente` 31/1 e `test_vocabulario_cliente` 54/1 —
baseline inalterado.

- [ ] **Step 3: Confirme que o servidor sobe**

Pare qualquer servidor rodando, então:

```bash
python -c "import server; print('import OK')"
```

Esperado: `import OK`. Um `NameError: T` aqui significa que você pôs um `T(...)`
dentro de uma estrutura avaliada no carregamento do módulo, não dentro de uma
função.

- [ ] **Step 4: Smoke test no jogo (manual — precisa do autor)**

Suba `iniciar.bat`, crie uma sala com o mago (Pedro), anime dois ou mais
cadáveres e encerre o turno. Confirme, nesta ordem:

1. O primeiro servo (maior iniciativa) aparece selecionado sozinho, com o
   realce azul de movimento sobre ele.
2. O botão diz "⏭ Encerrar servo (1/N)".
3. Mover e atacar com ele funciona pelo mouse.
4. Apertar encerrar seleciona o segundo servo sozinho e o botão vira "(2/N)".
5. Encerrar o último fecha a janela e a rodada avança.
6. Com o joystick: o cursor nasce sobre o servo da vez, a rota azul é do servo,
   A confirma o passo dele, o botão de ataque mira os monstros no alcance DELE,
   e o botão de encerrar turno passa ao servo seguinte com um aperto só.
7. Trocando o idioma para English no painel ⚙️, o rótulo do botão e a narração
   dos saltos saem em inglês.

**Se algo do cliente não mudar, recarregue com cache-buster** (`?v=2`) — o
navegador serve o `game.js` do cache e a prova sai falsa.

- [ ] **Step 5: Commit final (se algo foi ajustado no smoke test)**

```bash
git status
git add <apenas os arquivos que você mesmo mudou>
git commit -m "fix(animados): ajustes do smoke test da fila de servos

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Notas de escopo

**Fora desta implementação, por decisão do spec:**

- Navegação pelo joystick no painel de **habilidades ativas** do servo (Senhor
  da Morte / elemental) — continuam só no mouse.
- Qualquer mudança nas regras de movimento, ataque ou custo dos servos.
- O `comandar_animados` automático (todos os servos agem sozinhos) permanece
  exatamente como está.

**Simplificação aceita:** `GS.animadoAttackTargetTiles` não modela custo vertical
de terreno nem footprint 2×2 (o servidor modela). O realce pode oferecer uma casa
que o servidor recusa; a recusa chega como erro normal.
