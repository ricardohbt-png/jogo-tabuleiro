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
| Cold start é disfarçável | ⚠️ **Medido em 2026-08-30, depois da troca para aiohttp: 21 s e 62 s** | Ver abaixo — é disfarçável, mas exige UX dedicada |
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

## Medições finais (2026-08-30, serviço `live` com a camada `aiohttp`)

URL do spike: `https://lfh-spike.onrender.com`, porta 10000 injetada em `PORT`.

| Medida | Rodada 1 | Rodada 2 |
|---|---|---|
| 1ª conexão (fria) | 62,80 s | 21,84 s |
| 2ª conexão (piso quente) | 0,71 s | 0,69 s |
| **Cold start** | **62,09 s** | **21,15 s** |
| Eco (ida e volta da sonda) | 199 ms | 208 ms |

Cada rodada foi precedida de **16,5 minutos de silêncio absoluto**. `GET
/index.html` → 200; `HEAD /index.html` → **200** (era o que matava o deploy).

**Leitura dos números:**

- **O piso quente é excelente e estável**: 0,70 s para abrir a conexão, ~200 ms
  de ida e volta. Para um jogo de turnos, o jogador não sente. Partida em
  andamento não sofre — o tráfego do próprio jogo mantém o serviço acordado.
- **O cold start varia 3× entre medições consecutivas**, nas mesmas condições.
  Não dá para prometer um número; dá para dizer que o **teto observado é ~60 s**.
- **Limitação honesta:** n=2. Escolhi duas rodadas em vez das três do plano para
  encurtar a exposição dos 17 handlers de escrita sem autenticação. A dispersão
  encontrada seria argumento para MAIS medições, não menos — então o que temos é
  a faixa, não a distribuição. Se o número típico vier a importar (por exemplo,
  para prometer algo a jogadores), vale repetir com a segurança do SP1 já feita.

**Consequência para o SP4:** a UX de warm-up tem de aguentar **até ~60 s** sem
parecer travada, e não pode prometer um tempo fixo. Com os estáticos no CDN
(SP2) a página abre instantânea, então o que o jogador vê é uma tela nossa com
progresso — não um navegador em branco. É disfarçável, mas exige trabalho
dedicado: não é "só um spinner".

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

✅ **Cumprida.** O serviço `lfh-spike` foi destruído no painel do Render pelo
autor em 2026-08-29, encerrando a exposição dos 17 handlers de escrita sem
autenticação (bloqueador B1 do spec, escopo do SP1). A URL nunca foi divulgada e
nenhuma conta real foi criada.

A branch `spike/deploy-render` continua no GitHub, com o `render.yaml`
descartável. Ela pode ser reusada para a prova final da troca de camada de rede
(critério de aceitação 6 do spec do `aiohttp`) e só então apagada.
