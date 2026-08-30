# SP1 — Modo público — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar seguro abrir o cadastro: senha de verdade com freio contra força bruta, editores desligados no modo público, `Origin` restrito e os vazamentos fechados — sem mudar nada do jogo local.

**Architecture:** Um portão único (`LFH_PUBLIC`) governa tudo que só vale online. A credencial vira senha; o cálculo do hash sai do laço de eventos, o que é pré-requisito do limite de tentativas. O endereço do cliente chega ao limite pelo `_WS`, o adaptador criado na troca de camada.

**Tech Stack:** Python 3.14 local / 3.13 no Render, `aiohttp` 3.14.3.

**Spec:** `docs/superpowers/specs/2026-08-30-sp1-modo-publico-design.md`

---

## AVISO — o autor edita `server.py` em paralelo

Ele tem trabalho não commitado em 14 arquivos, `server.py` incluído. **NUNCA**
rode `git add server.py`, `git add .` ou `git add -A`.

Para commitar `server.py` sem levar o WIP junto, use a técnica validada quatro
vezes nesta série:

```bash
git show HEAD:server.py > SCRATCH/head_server.py
# aplique a MESMA edição nos dois (o de trabalho, para os testes rodarem, e a cópia)
BLOB=$(git hash-object -w SCRATCH/head_server.py)
git update-index --cacheinfo 100644,$BLOB,server.py
git commit -m "..."
```

**Antes:** confirme que a região a editar é byte-idêntica entre `HEAD` e a cópia
de trabalho. **Depois:** compare os hunks `@@` de `git diff server.py` com um
snapshot de antes. Edite em **binário** (a região está em LF; o repo converte
para CRLF).

`game.js` também está no WIP dele — vale a mesma regra.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `server.py` | Senha, limite, modo público, `Origin`, TTL de sala |
| `game.js` | Campo de senha no login (3 pontos) |
| `src/lang/strings.js`, `src/lang/interface.js` | Textos do campo e dos erros |
| `tools/test_modo_publico.py` | **Criar.** Toda a suíte do SP1 |
| `accounts/`, `savegames/`, `groups/` | Dados de teste, apagados na Task 3 |

---

### Task 1: Senha no servidor

**Files:** Modify `server.py`; Create `tools/test_modo_publico.py`

- [ ] **Step 1: Escrever o teste que falha**

Create `tools/test_modo_publico.py`:

```python
"""SP1 — modo público. Roda da raiz: python tools/test_modo_publico.py"""
import sys, os, tempfile, shutil
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(nome, cond, dica=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  [ok] {nome}")
    else:    FAIL += 1; print(f"  [FALHA] {nome}" + (f" -- {dica}" if dica else ""))

def main():
    print("\n[1] senha substitui o PIN")
    tmp = tempfile.mkdtemp(); velho = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    try:
        acc, err = S.create_account("jogador", "1234")
        check("PIN de 4 dígitos é RECUSADO", acc is None and err,
              f"aceitou: {acc}")

        acc, err = S.create_account("jogador", "curta1")
        check("senha de 6 caracteres é recusada", acc is None and err)

        acc, err = S.create_account("jogador", "cavalo bateria grampo")
        check("senha longa com espaços é aceita", acc is not None, str(err))
        check("o campo gravado se chama password_hash",
              acc is not None and "password_hash" in acc and "pin_hash" not in acc)

        acc2, err2 = S.create_account("jogador2", "12345678")
        check("8 caracteres é o mínimo, e passa", acc2 is not None, str(err2))

        check("verify_password aceita a senha certa",
              S.verify_password("cavalo bateria grampo", acc["password_hash"]))
        check("verify_password recusa a errada",
              not S.verify_password("cavalo bateria grampos", acc["password_hash"]))
        check("verify_password recusa hash vazio",
              not S.verify_password("qualquer", ""))
    finally:
        S.ACCOUNTS_DIR = velho; shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_modo_publico.py`
Expected: FALHA — `AttributeError: module 'server' has no attribute 'verify_password'`, e o PIN `"1234"` ainda sendo aceito.

- [ ] **Step 3: Implementar no `server.py`**

Renomeie `hash_pin` → `hash_password` e `verify_pin` → `verify_password` (o corpo
das duas **não muda**: já são PBKDF2-SHA256 com salt por conta e aceitam qualquer
texto). Atualize os dois pontos de chamada, em `create_account` e `try_login`.

Em `create_account`, troque a regra de formato:

```python
    if not re.fullmatch(r"\d{4}", str(pin or "")):
        return None, "O PIN deve ter 4 dígitos."
```

por:

```python
    senha = str(password or "")
    # So comprimento, de proposito. Exigir maiuscula/numero/simbolo empurra as
    # pessoas para "Senha1!" e para reusar a senha de outro site; o comprimento
    # protege mais que a variedade forcada.
    if len(senha) < SENHA_MIN:
        return None, T("erro.senha_curta", minimo=SENHA_MIN)
```

Renomeie o parâmetro `pin` → `password` em `create_account` e `try_login`, e o
campo gravado `pin_hash` → `password_hash` (em `create_account`, em `try_login`
e na validação de `load_account`, que hoje checa `data.get("pin_hash")`).

Acrescente perto das outras constantes:

```python
SENHA_MIN = 8
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_modo_publico.py`
Expected: `=== 8 passaram, 0 falharam ===`

- [ ] **Step 5: Confirmar que nada mais quebrou**

Run: `python tools/test_savegames.py`
Expected: pode FALHAR nas seções que criam conta com PIN — isso é esperado e
**faz parte desta task**. Atualize as chamadas de `create_account`/`try_login`
naquele arquivo para usar senhas de 8+ caracteres, e rode de novo até verde.

- [ ] **Step 6: Commit (técnica do blob — ver AVISO)**

```
feat(seguranca): senha de 8+ caracteres substitui o PIN de 4 digitos

10.000 combinacoes nao sustentam cadastro aberto. So comprimento, sem exigir
composicao: "Senha1!" e reuso de senha de outro site sao piores que uma senha
longa. hash_pin/verify_pin viram hash_password/verify_password -- o corpo nao
muda, ja era PBKDF2 com salt por conta.
```

---

### Task 2: Senha no cliente

**Files:** Modify `game.js`, `src/lang/strings.js`, `src/lang/interface.js`

- [ ] **Step 1: Trocar o campo**

Em `game.js`, o `<input>` do PIN (procure por `id="input-pin"`):

```html
      <label data-i18n="ui.connect.pin_label">PIN (4 dígitos) — para jogos salvos</label>
      <input id="input-pin" type="password" inputmode="numeric" maxlength="4" placeholder="••••">
```

vira:

```html
      <label data-i18n="ui.connect.senha_label">Senha — para jogos salvos</label>
      <input id="input-senha" type="password" autocomplete="current-password" placeholder="••••••••">
```

Saem `inputmode="numeric"` e `maxlength="4"`; entra `autocomplete`, para o
gerenciador de senhas do navegador funcionar.

- [ ] **Step 2: Trocar a validação**

A função `entrarComConta()`:

```javascript
  const pin  = (document.getElementById('input-pin').value || '').trim();
  ...
  if (!name) { alert('Escolha um apelido.'); return; }
  if (!/^\d{4}$/.test(pin)) { alert(t('ui.conta.pin_4_digitos')); return; }
  window._contaCtx = { url, name, pin };
  GS.loginConta(url, name, pin);
```

vira:

```javascript
  const senha = document.getElementById('input-senha').value || '';
  ...
  if (!name) { alert(t('ui.conta.escolha_apelido')); return; }
  if (senha.length < 8) { alert(t('ui.conta.senha_curta')); return; }
  window._contaCtx = { url, name, pin: senha };
  GS.loginConta(url, name, senha);
```

Três detalhes que não são estilo:

- **sem `.trim()` na senha.** Espaço no começo ou no fim é parte da senha; cortar
  silenciosamente faria o login falhar sem explicação.
- **`alert('Escolha um apelido.')` estava em português cru** — literal solto num
  jogo que é PT/EN inteiro. Como esta task reescreve a linha, entra a chave.
- `_contaCtx` mantém a chave `pin` para não mexer em quem a lê; só o conteúdo
  muda. Se preferir renomear, é uma busca por `_contaCtx` — mas fora do escopo.

- [ ] **Step 3: Chaves de idioma**

Em `src/lang/strings.js`, substituir `ui.connect.pin_label` por:

```javascript
  "ui.connect.senha_label": { "pt": "Senha — para jogos salvos",
                              "en": "Password — for saved games" },
```

Em `src/lang/interface.js`, substituir `ui.conta.pin_4_digitos` por:

```javascript
    "ui.conta.senha_curta": { "pt": "A senha precisa ter pelo menos 8 caracteres.",
                              "en": "The password must be at least 8 characters." },
    "ui.conta.escolha_apelido": { "pt": "Escolha um apelido.",
                                  "en": "Choose a nickname." },
```

- [ ] **Step 4: Verificar que não sobrou chave órfã**

Run: `python tools/test_idioma.py`
Expected: verde. Este teste varre chaves órfãs — se `ui.connect.pin_label` ficou
referenciada em algum lugar, ele acusa.

Run: `node tools/test_idioma_cliente.js`
Expected: verde.

- [ ] **Step 5: Commit (`game.js` também está no WIP — técnica do blob)**

```
feat(seguranca): campo de senha no login, no lugar do PIN

Sai inputmode=numeric e maxlength=4; entra autocomplete, para o gerenciador
de senhas do navegador funcionar. A senha NAO passa por trim(): espaco nas
pontas e parte dela, e cortar em silencio faria o login falhar sem explicacao.

De quebra, o alert('Escolha um apelido.') -- portugues cru num jogo PT/EN --
ganhou chave.
```

---

### Task 3: Apagar os dados de teste

**Passo explícito e anunciado.** Nunca como efeito colateral de outra mudança.

**Files:** apaga `accounts/*.json`, `savegames/*.json*`, `groups/*.json`

- [ ] **Step 1: Confirmar que é só dado de teste**

Run:

```bash
python -c "
import json,glob,os
for p in sorted(glob.glob('savegames/*.json')):
    sg=json.load(open(p,encoding='utf-8'))
    print(os.path.basename(p), '|', sg.get('name'), '| dono:', sg.get('owner'))
"
```

Expected: nomes como `twste`, `Teste Bau Refugio`, `Diag Lobby`,
`teste multiplayer`. **Se aparecer algo que pareça uma campanha de verdade,
PARE e pergunte ao autor.**

- [ ] **Step 2: Apagar**

```bash
rm -f accounts/*.json savegames/*.json savegames/*.bak groups/*.json
```

- [ ] **Step 3: Confirmar**

```bash
for d in accounts savegames groups; do echo "$d: $(ls $d 2>/dev/null | wc -l)"; done
```

Expected: `0` nos três.

- [ ] **Step 4: Nada a commitar**

Os três diretórios estão no `.gitignore` (linhas 21–28). Confirme com
`git status --short` que nada apareceu — se aparecer, **pare**: significa que
dado de conta estava versionado, o que seria um problema por si só.

---

### Task 4: PBKDF2 fora do laço de eventos

Pré-requisito da Task 5: sem isto, cada tentativa recusada ainda travaria o laço
por ~100 ms, e o próprio limite viraria a arma.

**Files:** Modify `server.py`, `tools/test_modo_publico.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente ao `tools/test_modo_publico.py`, antes do `print` final:

```python
    print("\n[2] o hash não pode travar o laço de eventos")
    import asyncio, time, inspect

    check("try_login é uma corrotina (pode aguardar a thread)",
          inspect.iscoroutinefunction(S.try_login))

    async def _mede():
        tmp2 = tempfile.mkdtemp(); v = S.ACCOUNTS_DIR; S.ACCOUNTS_DIR = tmp2
        try:
            # create_account também vira corrotina neste Step; por isso o await.
            await S.create_account("alvo", "senha bem longa")
            batendo = [True]
            marcas = []
            async def _pulso():
                # Se o laço travar, o intervalo entre pulsos estoura.
                while batendo[0]:
                    t = time.monotonic()
                    await asyncio.sleep(0.005)
                    marcas.append(time.monotonic() - t)
            p = asyncio.create_task(_pulso())
            for _ in range(6):
                await S.try_login("pid-x", "alvo", "senha errada aqui")
            batendo[0] = False
            await p
            return max(marcas) if marcas else 9.99
        finally:
            S.ACCOUNTS_DIR = v; shutil.rmtree(tmp2, ignore_errors=True)

    pior = asyncio.run(_mede())
    check(f"o laço nunca ficou preso (pior pausa {pior*1000:.0f} ms, teto 60 ms)",
          pior < 0.060,
          "o PBKDF2 está rodando no laço: 6 tentativas travaram todos os jogadores")
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_modo_publico.py`
Expected: FALHA na pausa do laço (o PBKDF2 síncrono segura o laço por ~100 ms
por tentativa) e possivelmente em `try_login é uma corrotina`.

- [ ] **Step 3: Implementar**

Torne `try_login` uma corrotina e mande os dois cálculos para uma thread:

```python
async def try_login(pid, username, password):
    ...
    ok = await asyncio.to_thread(verify_password, password, acc.get("password_hash", ""))
    if not ok:
        return False, T("erro.senha_incorreta")
```

Faça o mesmo em `create_account` (que chama `hash_password`), tornando-a
corrotina, e ajuste os pontos de chamada no `handler` — as duas já são chamadas
de dentro de código `async`, então basta `await`.

**Isto quebra a seção `[1]` do próprio teste**, escrita na Task 1, que chama
`S.create_account(...)` de forma síncrona: ela passa a devolver uma corrotina em
vez do par `(acc, err)`, e as checagens viram falso-positivos silenciosos. Envolva
aquele bloco num `asyncio.run(...)` na mesma passada. Mesma coisa em
`tools/test_savegames.py`, que usa as duas funções.

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_modo_publico.py`
Expected: verde, com a pior pausa bem abaixo de 60 ms.

- [ ] **Step 5: Regressão**

Run: `python tools/test_savegames.py`
Expected: verde (pode exigir `await` nas chamadas do próprio teste).

- [ ] **Step 6: Commit (técnica do blob)**

```
fix(seguranca): PBKDF2 sai do laco de eventos

Cada tentativa de login travava o laco por ~100 ms -- uma rajada de forca
bruta era, sozinha, negacao de servico contra todos os jogadores. E era
pre-requisito do limite de tentativas: sem isto, o proprio freio viraria a
arma. Medido por teste: pior pausa do laco sob 6 tentativas seguidas.
```

---

### Task 5: Limite de tentativas, por conta e por origem

**Files:** Modify `server.py`, `tools/test_modo_publico.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[3] limite de tentativas")
    S._LOGIN_TENTATIVAS.clear()

    ok, _ = S._login_permitido("ana", "1.1.1.1")
    check("contador zerado começa liberado", ok)

    for i in range(S.LOGIN_MAX_TENTATIVAS):
        S._registrar_falha_login("ana", "1.1.1.1")
    ok, _ = S._login_permitido("ana", "1.1.1.1")
    check("após o teto de tentativas, a conta é barrada", not ok)

    ok, _ = S._login_permitido("ana", "2.2.2.2")
    check("a MESMA conta é barrada mesmo vindo de outra origem", not ok,
          "senão trocar de IP anula o limite por conta")

    ok, _ = S._login_permitido("beto", "1.1.1.1")
    check("a MESMA origem é barrada mesmo para outra conta", not ok,
          "senão varrer muitas contas de um IP só anula o limite")

    S._LOGIN_TENTATIVAS.clear()
    for i in range(S.LOGIN_MAX_TENTATIVAS - 1):
        S._registrar_falha_login("carla", "3.3.3.3")
    ok, _ = S._login_permitido("carla", "3.3.3.3")
    check("abaixo do teto continua liberado — três erros não punem ninguém", ok)

    S._limpar_falhas_login("carla", "3.3.3.3")
    ok, _ = S._login_permitido("carla", "3.3.3.3")
    check("acerto limpa o contador", ok)

    print("\n[4] endereço do cliente")
    class _Req:
        def __init__(self, remote, headers): self.remote = remote; self.headers = headers
    r = _Req("10.0.0.1", {"X-Forwarded-For": "203.0.113.9, 10.0.0.1"})
    check("modo público confia no X-Forwarded-For (o IP real do jogador)",
          S._ip_do_cliente(r, publico=True) == "203.0.113.9",
          "sem isso, todos os jogadores atrás do proxy caem no mesmo balde")
    check("fora do modo público, ignora o header (é forjável)",
          S._ip_do_cliente(r, publico=False) == "10.0.0.1")
    r2 = _Req("10.0.0.1", {})
    check("sem o header, cai no remote", S._ip_do_cliente(r2, publico=True) == "10.0.0.1")
```

Note que este bloco é **síncrono**: as funções de limite não tocam em disco nem
em hash, então não precisam de thread nem de `await`. Só `try_login` e
`create_account` viraram corrotinas na Task 4.

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_modo_publico.py`
Expected: `AttributeError` em `_LOGIN_TENTATIVAS`.

- [ ] **Step 3: Implementar**

```python
# Freio contra forca bruta. Generoso de proposito: o objetivo e impedir 10.000
# tentativas, NAO punir um amigo que errou tres vezes.
LOGIN_MAX_TENTATIVAS = 8
LOGIN_JANELA_S = 15 * 60
_LOGIN_TENTATIVAS = {}       # chave -> [instantes das falhas]

def _login_chaves(username, ip):
    """Duas chaves, porque cobrem ataques diferentes: por CONTA impede insistir
    numa vitima; por ORIGEM impede varrer muitas contas com uma senha comum."""
    return (f"u:{_norm_username(username)}", f"i:{ip or '?'}")

def _login_permitido(username, ip):
    agora = time.time()
    for chave in _login_chaves(username, ip):
        marcas = [t for t in _LOGIN_TENTATIVAS.get(chave, ()) if agora - t < LOGIN_JANELA_S]
        _LOGIN_TENTATIVAS[chave] = marcas
        if len(marcas) >= LOGIN_MAX_TENTATIVAS:
            return False, int(LOGIN_JANELA_S - (agora - marcas[0]))
    return True, 0

def _registrar_falha_login(username, ip):
    agora = time.time()
    for chave in _login_chaves(username, ip):
        _LOGIN_TENTATIVAS.setdefault(chave, []).append(agora)

def _limpar_falhas_login(username, ip):
    for chave in _login_chaves(username, ip):
        _LOGIN_TENTATIVAS.pop(chave, None)

def _ip_do_cliente(request, publico):
    """Endereco do jogador.

    Atras do proxy da hospedagem, `request.remote` e o IP do PROXY -- usa-lo cru
    faria TODOS os jogadores compartilharem um balde so, e o primeiro atacante
    trancaria o jogo inteiro. O IP real vem em X-Forwarded-For.

    Mas header e FORJAVEL: fora de um proxy confiavel, qualquer cliente inventa
    um IP a cada tentativa e anula o limite. Por isso so confiamos no header no
    modo publico, onde sabemos que ha um proxy na frente."""
    if publico:
        xff = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        if xff:
            return xff
    return getattr(request, "remote", None) or "?"
```

O `_WS` ganha o endereço, para que o `handler` o alcance sem conhecer o
`aiohttp`:

```python
    __slots__ = ("_ws", "ip")

    def __init__(self, ws, ip=None):
        self._ws = ws
        self.ip = ip
```

Em `_rota`, passe `_WS(ws, _ip_do_cliente(request, _modo_publico()))`.

No `handler`, os ramos `login` e `create_account` consultam `_login_permitido`
antes, registram falha em erro e limpam em acerto.

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_modo_publico.py`
Expected: verde.

- [ ] **Step 5: Commit (técnica do blob)**

---

### Task 6: Modo público e o portão dos 17 handlers

**Files:** Modify `server.py`, `tools/test_modo_publico.py`

- [ ] **Step 1: Escrever o teste que falha — e que ENUMERA**

```python
    print("\n[5] modo público desliga os editores")
    ESCRITA = [
        "upload_story", "upload_scene_media", "save_scenes", "upload_tavern_art",
        "upload_city_art", "upload_refugio_art", "save_world_cities",
        "save_city_shops", "save_world_adventures", "upload_dungeon",
        "upload_campaign", "upload_custom_monster", "upload_custom_item",
        "upload_item_art", "upload_monster_art", "upload_prisoner",
        "objeto_upload",
    ]
    check("a lista tem os 17 handlers de escrita", len(ESCRITA) == 17)
    for t in ESCRITA:
        check(f"{t} é recusado no modo público", S._handler_bloqueado_no_publico(t))
    check("um handler de leitura NÃO é bloqueado",
          not S._handler_bloqueado_no_publico("load_scenes"))
    check("uma mensagem de jogo NÃO é bloqueada",
          not S._handler_bloqueado_no_publico("move"))

    # Rede de seguranca: um handler de escrita NOVO, criado no futuro, tem de
    # falhar este teste ate ser incluido no portao.
    import re as _re
    fonte = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
    achados = set(_re.findall(r'if t == "((?:upload|save)_[a-z_]+)"', fonte))
    achados |= set(_re.findall(r'if t == "(objeto_upload)"', fonte))
    novos = achados - set(ESCRITA) - {"save_scenes"}
    check(f"nenhum handler de escrita novo ficou fora do portão ({sorted(novos)})",
          not novos,
          "acrescente-o a ESCRITA e ao portão, ou o modo público não o cobre")
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_modo_publico.py`
Expected: `AttributeError: _handler_bloqueado_no_publico`.

- [ ] **Step 3: Implementar**

```python
def _modo_publico():
    """Liga o que so vale online: portao dos editores, Origin restrito e a
    confianca no X-Forwarded-For. DESLIGADO por padrao -- na maquina do autor
    nada muda."""
    return (os.environ.get("LFH_PUBLIC") or "").strip() not in ("", "0", "false")

# Um portao UNICO, e nao uma checagem por handler: com 17 pontos, esquecer um
# seria questao de tempo, e o esquecimento e invisivel ate alguem explora-lo.
HANDLERS_ESCRITA = frozenset({
    "upload_story", "upload_scene_media", "save_scenes", "upload_tavern_art",
    "upload_city_art", "upload_refugio_art", "save_world_cities",
    "save_city_shops", "save_world_adventures", "upload_dungeon",
    "upload_campaign", "upload_custom_monster", "upload_custom_item",
    "upload_item_art", "upload_monster_art", "upload_prisoner", "objeto_upload",
})

def _handler_bloqueado_no_publico(t):
    return t in HANDLERS_ESCRITA
```

No `handler`, **antes** do despacho dos editores:

```python
                if _modo_publico() and _handler_bloqueado_no_publico(t):
                    await err(T("erro.editor_indisponivel"))
                    continue
```

- [ ] **Step 4: Rodar para ver passar** — e conferir que o jogo local segue igual

Run: `python tools/test_modo_publico.py` → verde
Run: `python tools/test_rede_local.py` → `FAIL=0`

- [ ] **Step 5: Commit (técnica do blob)**

---

### Task 7: `Origin` restrito

**Files:** Modify `server.py`, `tools/test_modo_publico.py`

- [ ] **Step 1: Teste**

```python
    print("\n[6] Origin")
    check("fora do modo público, qualquer origem entra",
          S._origem_aceita("https://qualquer.site", publico=False, permitidas=""))
    check("no modo público, origem da lista entra",
          S._origem_aceita("https://meu.jogo", publico=True,
                           permitidas="https://meu.jogo"))
    check("no modo público, origem fora da lista é recusada",
          not S._origem_aceita("https://outro.site", publico=True,
                               permitidas="https://meu.jogo"))
    check("no modo público SEM lista, recusa — falha fechado, não aberto",
          not S._origem_aceita("https://meu.jogo", publico=True, permitidas=""))
```

- [ ] **Step 2: Ver falhar, implementar, ver passar**

```python
def _origem_aceita(origem, publico=None, permitidas=None):
    """No modo publico, so origens da lista LFH_ORIGINS. SEM lista, RECUSA:
    falhar fechado. Uma lista vazia significando 'aceita todos' seria um
    default inseguro esperando um esquecimento de configuracao."""
    publico = _modo_publico() if publico is None else publico
    if not publico:
        return True
    if permitidas is None:
        permitidas = os.environ.get("LFH_ORIGINS") or ""
    lista = [o.strip().rstrip("/") for o in permitidas.split(",") if o.strip()]
    return bool(lista) and (origem or "").strip().rstrip("/") in lista
```

Em `_rota`, no ramo do upgrade, recuse com `web.Response(status=403)` quando
`not _origem_aceita(request.headers.get("Origin"))`.

- [ ] **Step 3: Commit (técnica do blob)**

---

### Task 8: Limpeza — salas e grupos órfãos

- [ ] **Step 1: Teste**

```python
    print("\n[7] sala vazia não fica presa na memória")
    check("sala vazia tem prazo, e não morre na hora",
          S.SALA_VAZIA_TTL_S > 0,
          "apagar na hora destruiria partidas: o rejoin depende da sala existir")
    check("o prazo é generoso o bastante para uma reconexão (≥ 5 min)",
          S.SALA_VAZIA_TTL_S >= 300)
```

- [ ] **Step 2: Implementar**

**NÃO apague a sala assim que a última conexão cair.** O `rejoin` religa um
jogador que caiu, e depende de a sala ainda existir — apagar na hora destruiria
partidas em andamento a cada oscilação de rede.

Espelhe o padrão que o projeto já usa para sessões de teste
(`TEST_DUNGEON_TTL_S`, `_descartar_sala_teste`): marque o instante em que a sala
ficou vazia e recolha-a depois do prazo.

```python
SALA_VAZIA_TTL_S = 15 * 60   # generoso: o rejoin tenta 8x a cada 2,5 s
```

No `finally` do `handler`, onde já existe `room.connections.pop(pid, None)`,
registre `room.vazia_desde = time.time()` quando `not room.connections` (e limpe
o marcador quando alguém entrar). Uma varredura periódica descarta as vencidas.

- [ ] **Step 3: Ver passar; rodar `test_savegames` e `test_modo_mestre`**

- [ ] **Step 4: Commit (técnica do blob)**

---

## Critérios de conclusão

- [ ] `tools/test_modo_publico.py` verde
- [ ] `test_rede_local`, `test_http_camada`, `test_deploy_config` verdes
- [ ] `test_savegames`, `test_modo_mestre` verdes
- [ ] `test_idioma` e `test_idioma_cliente.js` verdes
- [ ] Sem `LFH_PUBLIC`: os editores funcionam como hoje
- [ ] Com `LFH_PUBLIC=1`: os 17 recusados, `Origin` exigido
- [ ] Conta criada com senha de 8+; senha curta recusada
- [ ] O WIP do autor em `server.py` e `game.js` intacto
- [ ] `accounts/`, `savegames/`, `groups/` vazios

## Fora de escopo

- Recuperação de senha, e-mail, verificação de conta
- Escolher o novo número de iterações do PBKDF2
- SP2 (estáticos no CDN), SP3 (Postgres), SP4 (empacotamento e warm-up)
