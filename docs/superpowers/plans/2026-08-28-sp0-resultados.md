# SP0 — Resultados medidos

**Data da medição:** 2026-08-29/30
**Plataforma:** Render free, plano `free`, branch `spike/deploy-render`
**Commits testados:** `770ce39` (1º deploy) e `eb89cf7` (2º, com `healthCheckPath`)

---

## Veredito

**O spike cumpriu seu papel e derrubou uma suposição que não estava na lista.**
Três das quatro perguntas foram respondidas; a quarta ficou bloqueada por um
achado novo, que é mais importante do que ela.

> **A biblioteca `websockets` não pode servir de servidor HTTP no Render.**
> A detecção de porta da plataforma sonda com `HEAD` a cada 1 segundo. A lib
> recusa todo método diferente de `GET` dentro de `http11.py`, **antes** do
> nosso `process_request` — o servidor fecha a conexão sem responder nada, e o
> deploy morre em `==> Timed Out` após 15 minutos.

Isto **não é contornável no nosso código** e **não é resolvido pelo SP2**: mesmo
virando só-WebSocket, a sonda de porta continua vindo antes de qualquer conexão
de jogo. A camada de serviço precisa mudar, independentemente de onde a gente
hospede.

---

## Suposições testadas

| Suposição do spec | Resultado | Consequência |
|---|---|---|
| A plataforma roda este Python | ✅ **Passou.** `server.py` importou e rodou sob **3.13**, com `websockets==16.0` instalado pelo `pip` | O código não depende de 3.14. Fixar 3.13 no SP4 é seguro |
| `["::"]` basta no Linux | ✅ **Passou.** O servidor aceitou conexões — é por isso que ele conseguiu reclamar delas | `LFH_HOSTS=0.0.0.0` fica como válvula de escape, não como padrão |
| Cold start é disfarçável | ⛔ **Não medido.** O serviço nunca ficou `live` | Pendente. Só medível depois que o bloqueio de HTTP for resolvido |
| Não pedem cartão | ✅ **Passou.** Nenhum cartão foi exigido no cadastro nem no deploy | A premissa de US$ 0 estrito se mantém |

## Achado não previsto: a sonda HEAD

**Reproduzido localmente**, para confirmar o mecanismo em vez de deduzir do
traceback:

```
GET      -> HTTP/1.1 200 OK
HEAD     -> (conexão fechada SEM RESPOSTA NENHUMA)
OPTIONS  -> (conexão fechada SEM RESPOSTA NENHUMA)
```

Para um verificador de saúde, "conexão fechada sem resposta" é indistinguível de
serviço morto.

**`healthCheckPath` não resolve.** A documentação do Render diz que o health
check nesse caminho usa `GET`, e por isso a hipótese era razoável — mas o 2º
deploy (`eb89cf7`, com `healthCheckPath: /index.html`) falhou igual. A cadência
de relógio das sondas, de 1 em 1 segundo, mostra que quem está sondando é a
**detecção de porta** do deploy, que roda antes e é independente do health check
configurado.

O `CLAUDE.md` já registrava a limitação como curiosidade — *"o servidor não
responde a HEAD, então sondar status por HEAD não é opção"*. Ela virou um
bloqueador de hospedagem.

---

## Opções para desbloquear

**A. Porta de entrada TCP.** Um processo mínimo escuta na porta pública, espia a
primeira linha da requisição, responde ele mesmo aos métodos que a lib recusa, e
repassa o resto (inclusive o `GET` do handshake de WebSocket) para o servidor
real numa porta interna. Não toca no `server.py` nem em internos da biblioteca.

*Prova de conceito verificada localmente*: `HEAD`/`GET`/`OPTIONS` todos
respondem `200`, e o jogo continua funcionando através dela
(`resposta = savegames_list`). **Ressalva medida:** a conexão pelo proxy levou
**2,04 s** contra **0,05 s** direto. Essa latência precisa ser resolvida antes
de virar solução — é protótipo, não código pronto.

**B. Trocar a camada de serviço.** Substituir o `websockets.serve` por um
servidor que fale HTTP de verdade e também aceite WebSocket. Refatora só a
camada de rede; a lógica de jogo fica intocada. Mais trabalho que A, mas sem
proxy no caminho e sem penalidade de latência.

**C. Trocar de plataforma.** Procurar uma hospedagem gratuita cuja detecção de
porta não use `HEAD`. Não resolve o problema, contorna — e amarra o projeto a um
detalhe não documentado de um fornecedor.

---

## Achados para os sub-projetos seguintes

- **SP2 não basta.** O plano assumia que remover o servir-estático só exigiria
  "um endpoint de saúde mínimo". Está provado que o problema é anterior: a
  plataforma não consegue nem detectar a porta. O SP2 precisa incorporar a
  decisão A/B/C acima.
- **SP4** pode fixar `PYTHON_VERSION` em 3.13 com segurança.
- **SP4** não precisa de `LFH_HOSTS` como padrão no Linux.
- O `healthCheckPath` sozinho é inútil para este servidor; só passa a fazer
  sentido depois que algo responder HTTP corretamente.

## Contenção

O serviço `lfh-spike` deve ser **destruído** no painel do Render — naquele
ambiente os 17 handlers de escrita seguem sem autenticação (bloqueador B1 do
spec, escopo do SP1). A URL nunca foi divulgada e nenhuma conta real foi criada.
