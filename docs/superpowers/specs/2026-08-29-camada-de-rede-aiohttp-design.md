# Camada de rede — trocar `websockets` por `aiohttp` — Design

**Data:** 2026-08-29
**Depende de:** SP0 — spike de deploy (`docs/superpowers/plans/2026-08-28-sp0-resultados.md`)
**Pertence a:** hospedagem online (`docs/superpowers/specs/2026-08-28-hospedagem-online-design.md`)

---

## Por que isto existe

O SP0 provou que **a biblioteca `websockets` não pode servir de servidor HTTP no
Render**. A detecção de porta da plataforma sonda com `HEAD` a cada segundo; a
lib recusa todo método diferente de `GET` dentro de `http11.py`, **antes** do
nosso `process_request` — o servidor fecha a conexão sem responder nada e o
deploy morre em `==> Timed Out`.

Isso **não é contornável no nosso código**, e o SP2 (mover estáticos para o CDN)
**não resolve**: mesmo virando só-WebSocket, a sonda de porta chega antes de
qualquer conexão de jogo.

Das três saídas levantadas no SP0, o autor escolheu a **B — trocar a camada de
serviço**. A **A** (porta de entrada TCP) tinha prova de conceito funcionando,
mas custou **2,04 s** por conexão contra 0,05 s direto; a **C** (trocar de
plataforma) contorna em vez de resolver, e amarra o projeto a um detalhe não
documentado de um fornecedor.

## Raio de impacto, medido

35.522 linhas de `server.py`, e a camada de rede toca menos de 50 pontos:

| Ponto de contato | Quantidade |
|---|---|
| Referências a `websockets.` | **4** (2 imports de HTTP, 1 `ConnectionClosed`, 1 `serve()`) |
| Laço de mensagens | **1**, em `server.py:31941` |
| Assinatura de handler | **1** (`async def handler(ws)`, `server.py:31930`) |
| Chamadas `ws.send(...)` | 41 |
| Mudanças no cliente | **nenhuma** |

As chamadas de envio já passam por dois funis (`GameRoom.send_to` e
`GameRoom.broadcast`), ambos com `try/except` em volta do `ws.send`. A lógica de
jogo não é tocada.

## Escolha da biblioteca

**`aiohttp`.** Três motivos concretos para este código:

1. É **uma** dependência. Starlette+uvicorn seriam duas mais uma camada ASGI no
   meio; Quart traz o modelo do Flask, que não tem nada a ver com o resto daqui.
2. Fala **HTTP e WebSocket no mesmo servidor** — que é exatamente o formato de
   porta única que o projeto já adotou, e a razão de um túnel HTTPS só cobrir
   página e `wss` sem mixed content.
3. O mapeamento é quase um para um: `process_request` vira rota, e
   `async for raw in ws` continua sendo `async for`.

## Mapeamento

| Hoje (`websockets`) | Depois (`aiohttp`) |
|---|---|
| `websockets.serve(handler, hosts, porta, process_request=…, max_size=34MB)` | `web.Application()` + `web.AppRunner` + `web.TCPSite` |
| `process_request` decide upgrade × estático | handler da rota decide, pelo mesmo header `Upgrade` |
| `async def handler(ws)` | `async def handler(request)` que cria `web.WebSocketResponse` |
| `async for raw in ws` | `async for msg in ws`, filtrando `msg.type == WSMsgType.TEXT` → `msg.data` |
| `await ws.send(txt)` (41×) | `await ws.send_str(txt)` |
| `except websockets.exceptions.ConnectionClosed` | conexão fechada encerra o `async for`; o `except` é ajustado |
| `_http(...)` com `Response`/`Headers` da lib | `web.Response(...)` |
| `max_size=34 * 1024 * 1024` | `WebSocketResponse(max_msg_size=34 * 1024 * 1024)` |
| `"Connection": "close"` em toda resposta | **removido** — ver abaixo |

### A rota `/` atende as duas coisas

O cliente conecta em `wss://<host>` **sem caminho** — `defaultServerUrl()`
(`game.js`) monta apenas protocolo + host. Portanto a rota `/` precisa atender
**tanto** o upgrade de WebSocket **quanto** o `GET` que devolve o `index.html`
(hoje `_serve_static` faz `rel = raw.lstrip("/") or "index.html"`).

O handler de `/` decide pelo header `Upgrade`, espelhando exatamente o que
`process_request` já faz. **Colocar o WebSocket num caminho próprio quebraria o
cliente** — e essa é justamente a mudança que "parece mais limpa" e não pode ser
feita aqui.

### O `Connection: close` sai, e isso conserta o B4

Aquele cabeçalho existia só para contornar o fato de a `websockets` fechar o
socket depois de responder — sem ele o navegador supunha keep-alive, guardava o
socket no pool e reusava numa requisição posterior que morria na rede. Com HTTP
de verdade, conexões persistentes voltam a funcionar.

Isso **resolve o bloqueador B4** do desenho de hospedagem: as dezenas de arquivos
de uma entrada de masmorra param de pagar um handshake TLS cada uma.

**Consequência para o programa:** o **SP2 deixa de ser urgente**. Ele continua
valendo pelos 535 MB dentro do contêiner (B5), mas o motivo de desempenho some.

## O que NÃO pode mudar

Esta é uma troca de encanamento. Nada observável pode se mexer:

- **Protocolo**: as mesmas mensagens JSON, no mesmo formato. Cliente intocado.
- **Estáticos**: mesma allow-list (`_STATIC_FILES`/`_STATIC_ROOTS` + extensões do
  editor), mesma proteção contra path traversal, mesmo gzip com memo, mesmo
  ETag/Last-Modified/304.
- **Escuta**: `_listen_port()` e `_listen_hosts()` continuam valendo — inclusive
  o ramo do Windows que liga nas duas famílias por causa do `IPV6_V6ONLY`, e a
  válvula `LFH_HOSTS`.
- **Idioma**: o `default=` do `json.dumps` que resolve os objetos `T` por conexão
  atravessa a troca sem alteração.

## Critérios de aceitação

1. **`python tools/test_rede_local.py` → `FAIL=0`.** Este teste já existe e já
   verifica IPv4, IPv6, o nome `localhost`, gzip do `.js`, PNG não recomprimido e
   coerência de cache. É ele que prova que a troca não mudou nada observável.
2. **`python tools/test_deploy_config.py` → 18/18.**
3. **`HEAD` e `OPTIONS` passam a receber resposta HTTP** — hoje a conexão fecha
   sem responder nada. Teste novo, derivado do achado do SP0.
4. **Keep-alive funciona**: duas requisições na MESMA conexão TCP devem receber
   duas respostas. Hoje a segunda morre. Teste novo — é a prova do B4.
5. **O jogo roda**: subir, abrir o cliente, criar sala, entrar numa masmorra.
6. **Prova final no Render**: redeploy do spike sem `==> Timed Out`, e o
   `tools/medir_cold_start.py` respondendo `savegames_list` contra a URL pública.

## Escopo

**Dentro:** a camada de rede do `server.py` — `main()`, `process_request`,
`_serve_static`, `_http`, a assinatura de `handler`, o laço de mensagens, as 41
chamadas de envio, o `except` de conexão fechada. Mais `requirements.txt`, e a
instrução de instalação para quem roda em casa (`iniciar.bat` / README).

**Fora:**
- toda a lógica de jogo;
- os 17 handlers de escrita sem autenticação (**SP1**);
- mover estáticos para o CDN (**SP2**, agora sem urgência);
- trocar arquivo por Postgres (**SP3**);
- medir o cold start (volta a ser possível depois desta etapa).

## Riscos

1. **Segunda dependência de runtime.** Hoje o projeto instala só `websockets`.
   Quem roda em casa vai precisar de `aiohttp` — `requirements.txt`, `iniciar.bat`
   e o README precisam dizer isso, senão o jogo simplesmente não sobe na máquina
   de quem atualizar.
2. **As 41 chamadas de envio.** A troca é mecânica, mas é onde um erro de
   digitação passa despercebido: um `send_str` esquecido só falha quando aquela
   mensagem específica é disparada em jogo. Mitigação: os dois funis
   (`send_to`/`broadcast`) cobrem a maioria; as demais são handlers de editor que
   respondem inline, e devem ser conferidas por varredura, não por leitura.
3. **`web.TCPSite` e a lista de hosts.** `_listen_hosts()` devolve uma lista.
   Confirmar na implementação como o `aiohttp` aceita múltiplos endereços — se
   não aceitar direto, criar um `TCPSite` por endereço.
4. **Um `except` largo demais.** Hoje o `finally` do handler libera trava de
   conta, idioma e personagem. Se a troca de exceção deixar um caminho de saída
   sem passar por ali, ficam travas penduradas — o sintoma seria "personagem já
   escolhido" sem ninguém jogando.
