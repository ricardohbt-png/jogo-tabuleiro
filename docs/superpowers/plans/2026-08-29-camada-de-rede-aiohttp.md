# Camada de rede — `websockets` → `aiohttp` — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a camada de rede do `server.py` para que o servidor fale HTTP de verdade — respondendo a `HEAD` e mantendo conexões persistentes — sem que nada observável do jogo mude.

**Architecture:** O `aiohttp` passa a ser o servidor. `process_request` vira uma rota única em `/` que decide entre upgrade de WebSocket e arquivo estático, exatamente como hoje. Um adaptador de dez linhas faz o objeto WebSocket do `aiohttp` parecer o de hoje, evitando tocar nos 41 pontos de envio. A lógica de jogo não é tocada.

**Tech Stack:** Python 3.14 local / 3.13 no Render, `aiohttp` 3.14.3 (já instalado).

**Spec:** `docs/superpowers/specs/2026-08-29-camada-de-rede-aiohttp-design.md`
**Origem:** `docs/superpowers/plans/2026-08-28-sp0-resultados.md`

---

## Desvio do spec, deliberado

O spec previa trocar as **41** chamadas `ws.send(...)` por `ws.send_str(...)`, e
apontou isso como o risco nº 2 — "onde um erro de digitação passa despercebido:
um `send_str` esquecido só falha quando aquela mensagem específica é disparada em
jogo".

Medição posterior mostrou que **`ws.send` é o ÚNICO método que o `server.py` usa**
do objeto WebSocket (`grep -oE '\bws\.[a-z_]+'` devolve 41 ocorrências, todas
`ws.send`). Não há `close`, `ping`, `remote_address` — nada.

Portanto: um adaptador com `send()` e `__aiter__()` cobre 100% da superfície.
Isso **elimina as 41 edições** e isola a biblioteca do resto do código. É menos
risco e melhor separação, pelo mesmo resultado.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `tools/test_http_camada.py` | **Criar.** Testes que falham hoje e passam depois: `HEAD` responde, keep-alive funciona |
| `requirements.txt` | **Modificar.** Acrescentar `aiohttp` |
| `README.md` / `iniciar.bat` | **Modificar.** Instrução de instalação |
| `server.py` — adaptador | **Criar** classe `_WS`, perto do `handler` |
| `server.py` — camada HTTP | **Modificar** imports, `_http`, `process_request`, `main` |

**Nada mais.** `_serve_static`, `_aceita_gzip`, `_cliente_ja_tem`, `_talvez_gzip`,
`_http_date` e toda a lógica de jogo ficam intocados.

`_aceita_gzip` e `_cliente_ja_tem` recebem o objeto de requisição e só chamam
`request.headers.get(...)` — o `web.Request` do `aiohttp` também tem `.headers`,
então **atravessam a troca sem alteração**. Isso foi verificado lendo as duas
funções, não suposto.

---

## AVISO — o autor tem trabalho não commitado em `server.py`

Ele edita `server.py` em paralelo (hoje: armadilhas, em `validar_dungeon`,
`make_authored_trap`, `ARMADILHAS` e `GameRoom`). **NUNCA** rode `git add
server.py`, `git add .` ou `git add -A`.

Para commitar `server.py` sem levar o WIP junto, use a técnica já validada duas
vezes nesta série:

```bash
git show HEAD:server.py > /caminho/scratchpad/head_server.py
# aplique a MESMA edição nos dois arquivos (o de trabalho e a cópia)
BLOB=$(git hash-object -w /caminho/scratchpad/head_server.py)
git update-index --cacheinfo 100644,$BLOB,server.py
git commit -m "..."
```

**Antes:** confirme que a região a editar é byte-idêntica entre `HEAD` e a cópia
de trabalho. **Depois:** compare os cabeçalhos `@@` de `git diff server.py` com um
snapshot tirado antes — devem ser idênticos. Edite em **binário**, para não
converter fim de linha.

---

### Task 1: Testes que provam o problema

Estes testes **falham de propósito** antes da troca. São os critérios de
aceitação 3 e 4 do spec, e nascem direto do que o SP0 descobriu.

**Files:**
- Create: `tools/test_http_camada.py`

- [ ] **Step 1: Escrever o teste**

```python
"""Camada HTTP do servidor. Roda da raiz: python tools/test_http_camada.py

Nasce do SP0 (docs/superpowers/plans/2026-08-28-sp0-resultados.md): o Render
sonda a porta com HEAD de 1 em 1 segundo, e a lib websockets recusa todo metodo
!= GET dentro de http11.py -- ANTES do nosso process_request. O servidor fecha a
conexao sem responder nada, e o deploy morre em "==> Timed Out".

Estes testes FALHAM antes da troca de camada e passam depois.
"""
import os, socket, subprocess, sys, time

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8788

PASS = 0; FAIL = 0
def check(nome, cond, dica=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  [ok] {nome}")
    else:
        FAIL += 1; print(f"  [FALHA] {nome}" + (f" -- {dica}" if dica else ""))


def _pedido(metodo, caminho="/index.html", conexao="close"):
    return (f"{metodo} {caminho} HTTP/1.1\r\n"
            f"Host: localhost:{PORTA}\r\n"
            f"Connection: {conexao}\r\n\r\n").encode()


def _ler_resposta(sock):
    """Le UMA resposta HTTP (cabecalhos + corpo por Content-Length).
    Devolve (linha_de_status, corpo) ou (None, b'') se nada veio."""
    dados = b""
    while b"\r\n\r\n" not in dados:
        try:
            pedaco = sock.recv(4096)
        except Exception:
            return None, b""
        if not pedaco:
            return None, b""
        dados += pedaco
    cab, _, resto = dados.partition(b"\r\n\r\n")
    linha = cab.split(b"\r\n")[0].decode("latin1")
    tam = 0
    for l in cab.split(b"\r\n")[1:]:
        if l.lower().startswith(b"content-length:"):
            tam = int(l.split(b":", 1)[1].strip())
    while len(resto) < tam:
        try:
            pedaco = sock.recv(4096)
        except Exception:
            break
        if not pedaco:
            break
        resto += pedaco
    return linha, resto[:tam]


def espera_subir(prazo=25.0):
    fim = time.time() + prazo
    while time.time() < fim:
        try:
            s = socket.create_connection(("127.0.0.1", PORTA), timeout=0.5)
            s.close(); return True
        except Exception:
            time.sleep(0.3)
    return False


print("[0] sobe o servidor numa porta propria")
env = dict(os.environ, LFH_PORT=str(PORTA))
proc = subprocess.Popen([sys.executable, "server.py"], cwd=RAIZ, env=env,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    if not espera_subir():
        print(f"  [FALHA] servidor nao subiu na porta {PORTA}")
        print("\nPASS=0 FAIL=1")
        sys.exit(1)
    print("  [ok] servidor no ar")

    print("[1] GET continua funcionando (nao pode regredir)")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("GET"))
    linha, corpo = _ler_resposta(s); s.close()
    check("GET /index.html responde 200", linha is not None and "200" in linha,
          f"veio: {linha!r}")
    check("GET devolve corpo nao vazio", len(corpo) > 0)

    print("[2] HEAD recebe resposta -- e a sonda que o Render usa")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("HEAD"))
    linha, _ = _ler_resposta(s); s.close()
    check("HEAD recebe uma resposta HTTP", linha is not None,
          "a conexao fechou sem responder nada -- e assim que o deploy morre")
    check("HEAD responde 200", linha is not None and "200" in linha,
          f"veio: {linha!r}")

    print("[3] metodo desconhecido nao derruba a conexao em silencio")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("OPTIONS"))
    linha, _ = _ler_resposta(s); s.close()
    check("OPTIONS recebe alguma resposta HTTP", linha is not None,
          "qualquer status serve; o que nao pode e fechar mudo")

    print("[4] keep-alive -- DOIS pedidos na MESMA conexao TCP")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("GET", conexao="keep-alive"))
    linha1, _ = _ler_resposta(s)
    s.sendall(_pedido("GET", "/game.css", conexao="keep-alive"))
    linha2, _ = _ler_resposta(s)
    s.close()
    check("1o pedido responde 200", linha1 is not None and "200" in linha1)
    check("2o pedido na MESMA conexao responde 200",
          linha2 is not None and "200" in linha2,
          "hoje a lib fecha o socket apos responder; era isso que obrigava "
          "'Connection: close' e fazia cada arquivo pagar um handshake TLS")

    print(f"\nPASS={PASS} FAIL={FAIL}")
    sys.exit(1 if FAIL else 0)
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except Exception: proc.kill()
```

- [ ] **Step 2: Rodar e confirmar que FALHA nos pontos certos**

Run: `python tools/test_http_camada.py`

Expected: as seções `[1]` passam, e **falham** `[2]` (HEAD sem resposta), `[3]`
(OPTIONS sem resposta) e a segunda checagem de `[4]` (keep-alive).

Se `[2]` já passasse, o diagnóstico do SP0 estaria errado e o plano inteiro
precisaria ser revisto — **pare e avise**.

- [ ] **Step 3: Commit**

```bash
git add tools/test_http_camada.py
git commit -m "test(rede): HEAD e keep-alive -- falham hoje, passam apos a troca"
```

---

### Task 2: Dependência e instruções de instalação

**Files:**
- Modify: `requirements.txt`
- Modify: `README.md` (se existir uma seção de instalação; senão, criar uma linha)

- [ ] **Step 1: Conferir a versão instalada**

Run: `python -c "import aiohttp; print(aiohttp.__version__)"`
Expected: `3.14.3` ou maior.

- [ ] **Step 2: Atualizar `requirements.txt`**

```
websockets==16.0
aiohttp>=3.14.3
```

`websockets` **continua na lista** por enquanto: a Task 4 é que remove o uso, e
até lá o servidor precisa das duas. A limpeza é da Task 5.

`aiohttp` usa `>=` e não `==` porque, ao contrário do `websockets` (cuja versão
exata importa para o comportamento do parser que descobrimos), aqui queremos
correções de segurança sem intervenção.

- [ ] **Step 3: Documentar a instalação**

Localize a seção de "como rodar" do `README.md` (ou crie uma) e acrescente,
antes das instruções de execução:

```markdown
### Dependências

Antes de rodar pela primeira vez (ou depois de atualizar):

    python -m pip install -r requirements.txt
```

**Isto não é opcional:** quem atualizar o projeto sem instalar o `aiohttp` verá o
servidor não subir, com `ModuleNotFoundError`.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt README.md
git commit -m "chore(deps): aiohttp + instrucao de instalacao"
```

---

### Task 3: O adaptador de WebSocket

Unidade pura e isolada. Não muda comportamento nenhum ainda — só passa a existir.

**Files:**
- Modify: `server.py` (acrescentar a classe logo ANTES de `async def handler`)
- Modify: `tools/test_deploy_config.py` (nova seção `[3]`)

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_deploy_config.py`, inserir antes do
`print(f"\n=== {PASS} passaram...")`:

```python
    # [3] adaptador de WebSocket
    print("\n[3] _WS — adaptador que isola a biblioteca do resto do código")

    class _FakeMsg:
        def __init__(self, tipo, dado): self.type = tipo; self.data = dado

    class _FakeWS:
        """Dublê do WebSocketResponse do aiohttp."""
        def __init__(self, mensagens): self.enviadas = []; self._msgs = mensagens
        async def send_str(self, texto): self.enviadas.append(texto)
        def __aiter__(self):
            async def gen():
                for m in self._msgs: yield m
            return gen()

    import asyncio as _aio
    from aiohttp import WSMsgType as _T

    falso = _FakeWS([_FakeMsg(_T.TEXT, '{"a":1}'),
                     _FakeMsg(_T.BINARY, b'\x00'),
                     _FakeMsg(_T.TEXT, '{"b":2}')])
    ad = S._WS(falso)

    _aio.run(ad.send("ola"))
    check("send() delega para send_str() do aiohttp",
          falso.enviadas == ["ola"])

    async def _colher():
        return [raw async for raw in ad]
    colhido = _aio.run(_colher())
    check("itera devolvendo o TEXTO das mensagens (o que o laço do jogo espera)",
          colhido == ['{"a":1}', '{"b":2}'])
    check("mensagem BINARY é ignorada — o cliente só manda texto",
          b'\x00' not in colhido)
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_deploy_config.py`
Expected: FALHA com `AttributeError: module 'server' has no attribute '_WS'`

- [ ] **Step 3: Implementar**

Em `server.py`, inserir imediatamente ANTES da linha `async def handler(ws):`:

```python
class _WS:
    """Faz o WebSocketResponse do aiohttp parecer o objeto que o jogo ja usa.

    O resto do server.py toca no socket por apenas DOIS caminhos: `await
    ws.send(texto)`, em 41 pontos, e `async for raw in ws`, em um. Medido:
    `grep -oE '\\bws\\.[a-z_]+' server.py` devolve 41 ocorrencias, todas
    `ws.send` -- nao ha close, ping nem remote_address.

    Por isso um adaptador de dez linhas cobre 100% da superficie. Ele evita
    reescrever os 41 pontos (onde um esquecimento so apareceria quando aquela
    mensagem especifica fosse disparada em jogo) e isola a biblioteca: numa
    proxima troca de camada, so este bloco se mexe."""
    __slots__ = ("_ws",)

    def __init__(self, ws):
        self._ws = ws

    async def send(self, texto):
        await self._ws.send_str(texto)

    def __aiter__(self):
        return self._iterar()

    async def _iterar(self):
        # So TEXT interessa: o cliente manda JSON. BINARY e CLOSE/ERROR saem do
        # laco, que e exatamente o que o `async for raw in ws` de hoje faz
        # quando a conexao cai.
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                yield msg.data
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break
```

E acrescentar aos imports do topo do arquivo (junto de `from copy import deepcopy`):

```python
import aiohttp
from aiohttp import web
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_deploy_config.py`
Expected: `=== 21 passaram, 0 falharam ===`

- [ ] **Step 5: O servidor ainda sobe (o adaptador ainda não é usado)**

Run: `python tools/test_rede_local.py`
Expected: `PASS=12 FAIL=0`

- [ ] **Step 6: Commit — use a técnica do blob (ver AVISO no topo)**

```
feat(rede): adaptador _WS isola a biblioteca de WebSocket

ws.send e o UNICO metodo que o server.py usa do socket (41 ocorrencias,
medidas). Um adaptador com send() e __aiter__() cobre a superficie inteira,
evita reescrever os 41 pontos e deixa a proxima troca de camada mexendo
so aqui.
```

---

### Task 4: A troca

Task atômica: o servidor não funciona pela metade. Todos os passos vão num
commit só.

**Files:**
- Modify: `server.py` — imports, `_http`, `process_request`, `handler`, `main`

- [ ] **Step 1: Snapshot do WIP do autor, antes de qualquer edição**

```bash
git diff server.py > SCRATCHPAD/wip_antes.patch
grep -c '^@@' SCRATCHPAD/wip_antes.patch
```

Anote o número. No fim da task ele tem de ser o mesmo.

- [ ] **Step 2: `_http` devolve uma resposta do aiohttp**

Substituir a função `_http` inteira (localize por `def _http(status, reason,`)
por:

```python
def _http(status, reason, body, ctype="text/plain; charset=utf-8", extra=None):
    """Resposta HTTP estatica.

    NAO ha mais "Connection: close". Ele existia so para contornar a lib
    websockets, que FECHAVA o socket depois de responder: sem o cabecalho, o
    navegador supunha keep-alive, guardava o socket no pool e reusava numa
    requisicao posterior que morria na rede -- aparecia como falha intermitente
    nos .glb carregados sob demanda. Com HTTP de verdade, conexoes persistentes
    voltam a funcionar, e as dezenas de arquivos de uma entrada de masmorra
    param de pagar um handshake TLS cada uma."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    resp = web.Response(status=status, reason=reason, body=body)
    resp.headers["Content-Type"] = ctype
    # no-cache = "pode guardar, mas revalide sempre". Com ETag/Last-Modified a
    # revalidacao de um arquivo inalterado custa um 304 vazio.
    resp.headers["Cache-Control"] = "no-cache"
    for k, v in (extra or {}).items():
        resp.headers[k] = v
    return resp
```

**Atenção:** o `aiohttp` define `Content-Type` sozinho ao receber `body=`.
Sobrescrever pelo dicionário de headers **depois** de construir é o que preserva
o comportamento atual (inclusive o `; charset=utf-8` que `_serve_static` monta).

- [ ] **Step 3: `process_request` vira a rota única**

Substituir a função `process_request` inteira por:

```python
async def _rota(request):
    """Rota unica do servidor. Decide pelo header `Upgrade`, exatamente como o
    process_request antigo fazia.

    A rota e "/" com cauda livre, e NAO um caminho proprio para o WebSocket,
    porque o cliente conecta em wss://<host> SEM CAMINHO -- defaultServerUrl()
    em game.js monta so protocolo + host. Mover o WebSocket para /ws quebraria
    todos os clientes."""
    if request.headers.get("Upgrade", "").lower() == "websocket":
        ws = web.WebSocketResponse(max_msg_size=34 * 1024 * 1024)
        await ws.prepare(request)
        await handler(_WS(ws))
        return ws

    if request.method not in ("GET", "HEAD"):
        # Antes isto fechava a conexao sem responder nada, e era o que fazia o
        # deploy morrer: a sonda de porta do Render usa HEAD.
        return _http(405, "Method Not Allowed", "405 Method Not Allowed")

    # _serve_static le o arquivo INTEIRO do disco, e alguns .glb passam de 5 MB.
    # No laco de eventos isso bloquearia o servidor todo -- inclusive as outras
    # conexoes chegando na mesma rajada. Numa thread, o laco segue atendendo.
    resp = await asyncio.to_thread(_serve_static, request)
    if request.method == "HEAD":
        # HEAD nao leva corpo. O que importa e a linha de status: e so isso que
        # a sonda da plataforma le.
        resp.body = b""
    return resp
```

- [ ] **Step 4: `main()` sobe o aiohttp**

No fim de `main()`, substituir o bloco `async with websockets.serve(...)` por:

```python
    app = web.Application()
    app.router.add_route("*", "/{cauda:.*}", _rota)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()

    # Um site por endereco. No Windows sao DOIS (o socket IPv6 nao aceita IPv4
    # por causa do IPV6_V6ONLY, e escutar so em "::" deixaria 127.0.0.1 sem
    # servidor -- os ~207 ms de fallback do nome "localhost" que o
    # tools/test_rede_local.py trava). No Linux e so "::".
    subiu = []
    for host in SERVER_HOSTS:
        try:
            site = web.TCPSite(runner, host, SERVER_PORT)
            await site.start()
            subiu.append(host)
        except OSError as e:
            print(f"  [aviso] nao consegui escutar em {host}: {e}", file=sys.stderr)
    if not subiu:
        print("  [ERRO] nenhum endereco de escuta funcionou. "
              "Tente LFH_HOSTS=0.0.0.0", file=sys.stderr)
        return
    print(f"  escutando em: {', '.join(subiu)}")
    await asyncio.Future()
```

O `print` dos endereços é deliberado: no SP0 o log da plataforma foi a única
janela para diagnosticar o bind, e não havia nada impresso.

- [ ] **Step 5: Ajustar o `except` de conexão fechada**

Localize `except websockets.exceptions.ConnectionClosed:` (dentro de `handler`) e
troque por:

```python
    except ConnectionResetError:
```

**NÃO acrescente `asyncio.CancelledError` a esse `except`.** Engolir
`CancelledError` quebra o encerramento do processo e o cancelamento de tasks — o
servidor pararia de responder a Ctrl+C e a task ficaria pendurada. Com o
adaptador, uma desconexão normal simplesmente **encerra o `async for`**, sem
exceção nenhuma; o `ConnectionResetError` cobre a queda abrupta.

**Verifique que o `finally` logo abaixo continua intacto.** É ele que libera a
trava de conta (`ACCOUNTS_ONLINE`), o idioma (`LANG_BY_PID`) e o personagem. Um
caminho de saída que escape dele deixa travas penduradas, e o sintoma seria
"personagem já escolhido" sem ninguém jogando.

- [ ] **Step 6: Remover os imports mortos**

Apagar do topo do arquivo:

```python
from websockets.http11 import Response
from websockets.datastructures import Headers
```

- [ ] **Step 7: O servidor sobe e responde**

Run: `python tools/test_http_camada.py`
Expected: **todas** as seções passam agora — `PASS=7 FAIL=0`. Especialmente
`[2]` (HEAD) e a segunda checagem de `[4]` (keep-alive), que falhavam na Task 1.

- [ ] **Step 8: Nada observável mudou**

Run: `python tools/test_rede_local.py`
Expected: `PASS=12 FAIL=0`. Este é o teste que importa: ele cobre IPv4, IPv6, o
nome `localhost`, gzip do `.js`, PNG não recomprimido e coerência de cache. Se
algo aqui quebrar, a troca mudou comportamento e **não** está pronta.

Run: `python tools/test_deploy_config.py`
Expected: `=== 21 passaram, 0 falharam ===`

- [ ] **Step 9: O jogo funciona ponta a ponta**

Run: `python tools/medir_cold_start.py ws://localhost:8765` (com o servidor de pé)
Expected: `resposta = savegames_list`

- [ ] **Step 10: O WIP do autor sobreviveu**

```bash
git diff server.py > SCRATCHPAD/wip_depois.patch
grep -c '^@@' SCRATCHPAD/wip_depois.patch
```

Expected: o mesmo número do Step 1. Confirme também que toda linha adicionada
pelo `wip_antes.patch` ainda existe no `server.py` atual.

- [ ] **Step 11: Commit — use a técnica do blob (ver AVISO no topo)**

```
feat(rede): aiohttp substitui websockets na camada de servico

O SP0 provou que a lib websockets nao pode servir HTTP no Render: a
deteccao de porta sonda com HEAD, e a lib recusa todo metodo != GET no
parser, antes do nosso codigo. Deploy morria em "==> Timed Out".

A rota e "/" com cauda livre, e nao um caminho proprio para o WebSocket:
o cliente conecta em wss://<host> SEM caminho.

Sai o "Connection: close" -- keep-alive volta a funcionar, e as dezenas
de arquivos de uma entrada de masmorra param de pagar handshake TLS cada
uma. Protocolo, estaticos, gzip, ETag e idioma inalterados.
```

---

### Task 5: Limpeza

**Files:**
- Modify: `requirements.txt`
- Modify: `server.py` (só se sobrar referência)

- [ ] **Step 1: Confirmar que `websockets` não é mais usado pelo servidor**

Run: `grep -n 'websockets' server.py`
Expected: nenhuma linha. Se aparecer alguma, ela precisa sair antes de seguir.

- [ ] **Step 2: Ver quem mais depende de `websockets`**

Run: `grep -rln 'websockets' tools/ *.py`

`tools/medir_cold_start.py` **usa `websockets` como CLIENTE** e vai continuar
usando — a dependência não pode sair do `requirements.txt` por causa dele.

- [ ] **Step 3: Atualizar `requirements.txt` com o motivo explícito**

```
# Servidor HTTP + WebSocket.
aiohttp>=3.14.3
# Cliente de WebSocket, usado por tools/medir_cold_start.py. O SERVIDOR nao
# usa mais: ver docs/superpowers/specs/2026-08-29-camada-de-rede-aiohttp-design.md
websockets==16.0
```

- [ ] **Step 4: Suíte completa**

```bash
python tools/test_http_camada.py
python tools/test_rede_local.py
python tools/test_deploy_config.py
python tools/test_savegames.py
python tools/test_modo_mestre.py
```

Expected: todas verdes. As duas últimas são regressão de jogo — se a troca de
rede quebrou algo no protocolo, é ali que aparece.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore(deps): websockets fica so como cliente do medidor"
```

---

## Critérios de conclusão

- [ ] `tools/test_http_camada.py` → `FAIL=0` (HEAD responde, keep-alive funciona)
- [ ] `tools/test_rede_local.py` → `FAIL=0` (nada observável mudou)
- [ ] `tools/test_deploy_config.py` → 21/21
- [ ] `tools/test_savegames.py` e `tools/test_modo_mestre.py` verdes
- [ ] O jogo abre no navegador, cria sala e entra numa masmorra
- [ ] O WIP do autor em `server.py` intacto (mesmos hunks do snapshot)
- [ ] `grep -n 'websockets' server.py` → vazio

## Prova final, que exige o autor

Redeploy do spike no Render (branch `spike/deploy-render`, que continua no
GitHub) e confirmação de que:

1. o deploy chega a **live**, sem `==> Timed Out`;
2. `python tools/medir_cold_start.py wss://<url>` responde `savegames_list`;
3. o **cold start** é finalmente medido — a pergunta que o SP0 não conseguiu
   responder.

Só depois disso a branch `spike/deploy-render` e o `render.yaml` podem ser
apagados.

## Fora de escopo

- os 17 handlers de escrita sem autenticação → **SP1**
- mover estáticos para o CDN → **SP2** (sem urgência: esta task resolve o B4)
- trocar arquivo por Postgres → **SP3**
- qualquer mudança na lógica de jogo
