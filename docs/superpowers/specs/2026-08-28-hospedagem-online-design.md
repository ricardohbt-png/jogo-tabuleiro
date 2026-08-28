# Hospedagem online — contas, progresso e campanhas na internet — Design

**Data:** 2026-08-28
**Estado:** desenho aprovado; SP0 é o próximo trabalho.
**Depende de:** sistema de jogos salvos (fases 1–3, implementadas e verificadas —
ver `2026-07-18-jogos-salvos-campanhas-persistentes-design.md`).

---

## Objetivo

Tirar o jogo de "roda na máquina do autor e os amigos entram por túnel" e colocá-lo
numa hospedagem pública, com **cadastro aberto**: qualquer pessoa cria conta, guarda
o progresso dos seus personagens e joga campanhas com outras pessoas.

**Restrição dura escolhida pelo autor: custo US$ 0 estrito, sem cartão de crédito.**
Isso não é preferência — é o eixo que determina a arquitetura inteira.

---

## O que já existe (medido, não estimado)

O pedido original do autor foi "cada jogador ter sua conta e salvar seus itens e o
progresso dos personagens". **Isso já está construído.** As fases 1–3 dos jogos
salvos entregaram:

| Peça | Onde | Estado |
|---|---|---|
| Contas | `accounts/*.json` — apelido + PIN com PBKDF2-SHA256, 100k iterações | 11 contas |
| Jogos salvos | `savegames/*.json` — escrita atômica + `.bak` | 14 jogos, 188 KB |
| Grupos | `groups/*.json` | 745 arquivos, 1,1 MB |
| Progressão durável | `savegame.characters` via `snapshot_character`/`restore_character` | ouro, HP, nível, XP, bolsa, gear, guilda |
| Identidade por conta | `ensure_account_profile` — 6 heróis-identidade | **só cosmético/histórico**, por decisão explícita |
| Reconexão | `rejoin` + sessão em `localStorage` | funciona enquanto o processo vive |
| Porta única | `process_request` serve estáticos + WebSocket em 8765 | um domínio cobre página e `wss` |
| Cache HTTP | gzip com memo + ETag/Last-Modified/304 | implementado |

**Conclusão:** o que falta não é a feature de contas. É tudo que separa "roda em
casa" de "exposto na internet".

---

## O que falta, medido

### Bloqueadores duros

**B1 — Os handlers do editor não têm autenticação nenhuma.**
O dispatch em `server.py:31853` trata, **antes de qualquer noção de sala ou conta**,
17 handlers que gravam em disco:

```
upload_story  upload_scene_media  save_scenes  upload_tavern_art  upload_city_art
upload_refugio_art  save_world_cities  save_city_shops  save_world_adventures
upload_dungeon  upload_campaign  upload_custom_monster  upload_custom_item
upload_item_art  upload_monster_art  upload_prisoner  objeto_upload
```

Mais 5 de leitura/auxiliares (`load_scenes`, `load_city_shops`,
`load_world_adventures`, `list_objetos`, `preview_dungeon`). Qualquer pessoa que
abra um WebSocket pode gravar arquivos em `assets/` e sobrescrever os JSON de
conteúdo. `websockets.serve(max_size=34 MB)` e `STORY_UPLOAD_MAX = 25 MB` definem o
tamanho por mensagem. Isso é escrita remota de arquivo, sem credencial.

**B2 — PIN de 4 dígitos, sem limite de tentativas.**
`create_account` exige `\d{4}` — 10.000 combinações. `try_login` não tem throttle,
lockout nem atraso progressivo. Pior: o PBKDF2 de 100k iterações roda **no loop de
eventos**, então uma tentativa de força bruta também é um vetor de negação de
serviço contra todas as partidas em andamento.

**B3 — O estado mora em disco local, e o plano gratuito tem disco efêmero.**
`accounts/`, `savegames/` e `groups/` são arquivos. No Render free não há disco
persistente: cada redeploy ou reciclagem apaga as contas e as campanhas.

### Degradações

**B4 — `Connection: close` em toda resposta estática** (`server.py:34940`). Está lá
de propósito, contornando o fato de a lib `websockets` fechar o socket após
responder. Em `localhost` custava 0,7 ms. Atrás de TLS na internet, cada arquivo
paga um handshake completo — e entrar numa masmorra pede dezenas de arquivos.

**B5 — 535 MB de `assets/`** (720 arquivos; o maior tem 6,6 MB; `models3d` sozinho
são 218 MB). Fora do deploy ficam `assets_originais/` (737 MB) e `.git` (1,4 GB) —
o diretório de trabalho inteiro dá 3,2 GB.

**B6 — Reinício do processo mata todas as partidas.** As salas vivem só em memória.
O `rejoin` só funciona enquanto o processo vive.

**B7 — Salas vazias nunca saem do dict `rooms`** (achado diferido da fase 3). E
`groups/` tem 745 arquivos para 14 savegames — parece criar um por sala sem nunca
limpar. Irrelevante em casa; num processo de longa duração, não.

**B8 — Nada de deploy existe.** Sem `requirements.txt`, `Dockerfile` ou `Procfile`.
`LFH_PORT` existe (bom — PaaS injeta `PORT`), mas `SERVER_HOSTS = ["0.0.0.0", "::"]`
foi escrito para o Windows e o duplo bind precisa ser testado no Linux.

**B9 — O servidor não valida o header `Origin`.** Nenhuma ocorrência no arquivo.
Com os editores desligados o impacto cai muito, mas a restrição é barata.

---

## Decisões tomadas

| Pergunta | Resposta do autor |
|---|---|
| Quem pode abrir o jogo? | **Cadastro aberto** — qualquer pessoa cria conta |
| Orçamento | **US$ 0 estrito, sem cartão** |
| Editores online na 1ª versão? | **Não — só local.** O autor cria conteúdo no PC e publica junto com o deploy |

**Visão de longo prazo declarada** (fora do escopo deste desenho): jogadores criam
suas próprias masmorras e aventuras e publicam para outros jogarem; pessoas se
encontram online, formam grupos e enfrentam as aventuras.

---

## Arquitetura alvo

```
Navegador
   │
   ├── HTTPS ──→ Cloudflare Pages         index.html, game.js, game.css, src/, assets/
   │                                       HTTP/2 com keep-alive, banda ilimitada
   │
   └── WSS  ──→ Render free (server.py)   só WebSocket. Zero disco.
                      │                    Origin restrito ao domínio do Pages.
                      │
                      └── SQL ──→ Neon Postgres free   contas, savegames, grupos
```

### Por que esta forma, e não o monolito

Mover os estáticos para o CDN **resolve B4 e B5 de uma vez**: o `server.py` para de
servir arquivo, então o `Connection: close` deixa de existir e os 535 MB saem da
imagem do contêiner. As dezenas de requisições de uma entrada de masmorra passam a
ir para o CDN com conexão reaproveitada, em vez de abrir handshakes TLS contra um
contêiner que pode estar hibernando.

Manter o monolito (servir tudo pelo `server.py` no Render) foi considerado e
descartado: menos código a mexer, mas build lento com risco de estourar, cold start
pior, handshake por arquivo mantido e essa banda contando contra a cota do Render.
Mais fácil de construir, pior de jogar.

Cloudflare Workers + Durable Objects também foi considerado — tecnicamente é o
encaixe perfeito para salas de jogo, com estado persistente e sem hibernação — e
descartado: são 35.522 linhas de Python.

### Os limites cabem com folga

| | O que temos | Limite do plano grátis | Folga |
|---|---|---|---|
| Estáticos | 720 arquivos, maior = 6,6 MB | Cloudflare Pages: 20.000 arquivos, 25 MiB/arquivo | 27× |
| Dados persistentes | **1,3 MB** (30 KB contas + 188 KB savegames + 1,1 MB grupos) | Neon: 0,5 GB, sem cartão | 380× |

Os 535 MB assustam, mas são 535 MB de **arquivos estáticos** — exatamente o que um
CDN gratuito serve de graça. E o estado que precisa sobreviver a reinício é
minúsculo.

### As três mudanças no `server.py`

1. **Deixa de servir arquivo.** `process_request` e `_serve_static` só existem no
   modo local. Somem junto o `Connection: close` e o cache gzip.
2. **Deixa de escrever em disco.** `accounts/`, `savegames/` e `groups/` passam por
   uma interface de documentos com dois adaptadores: arquivo (local, o que existe
   hoje) e Postgres (online). O resto do código não sabe a diferença.
3. **Ganha um modo público.** Um flag desliga os 17 handlers de escrita, aperta o
   login e restringe a origem. O modo local continua exatamente como está hoje.

### O imposto do US$ 0, que não é negociável

O Render free **hiberna após 15 minutos sem tráfego** e leva **cerca de 1 minuto**
para acordar. Enquanto uma partida corre, as mensagens do WebSocket seguram o
servidor acordado; o problema é o primeiro jogador do dia. Com os estáticos no CDN
dá para tornar isso digno — a página carrega instantânea e mostra o progresso do
warm-up — mas não dá para eliminar.

**Risco nomeado: com cadastro aberto, sucesso quebra o plano gratuito.** São 750
horas de instância no Render e 100 compute-hours de banco no Neon por mês. Se o
jogo pegar, a conta trava — não degrada, trava. Por isso a camada de storage do SP3
deve ser desenhada de modo que trocar de provedor seja uma troca de adaptador.

---

## Decomposição

Isto não cabe num spec só. Cinco sub-projetos; cada um dos SP1–SP4 ganha spec, plano
e implementação próprios, **informados pelo resultado do SP0**.

| | Sub-projeto | Fecha |
|---|---|---|
| **SP0** | **Spike de deploy** — subir o `server.py` como está no Render, sem dados, e medir | — |
| **SP1** | **Modo público** — editores off, rate-limit/lockout no login, PIN mais forte, PBKDF2 fora do loop, `Origin` restrito, limpeza de salas e grupos órfãos | B1, B2, B7, B9 |
| **SP2** | **Estáticos fora** — cliente descobre o WS por configuração, `server.py` para de servir arquivo, assets no Pages | B4, B5 |
| **SP3** | **Storage abstrato** — interface de documentos + adaptador Postgres | B3 |
| **SP4** | **Empacotamento e subida real** — `requirements.txt`, comando de start, `PORT`, health check, UX de warm-up | B8 |

**B6 (reinício mata partidas em andamento) fica aceito como limitação conhecida**
desta rodada. Persistir uma masmorra em curso é um projeto próprio e não é
pré-requisito para abrir o cadastro.

Projetos separados, depois: **grupos públicos / matchmaking** (hoje só existe código
de sala por código) e **UGC multi-autor** (que precisa do conteúdo-com-dono
substituindo o estado global de módulo, e que não cabe nos 0,5 GB grátis se autores
subirem arte).

---

## SP0 — Spike de deploy (o próximo trabalho)

### Por que antes da segurança

A ordem óbvia seria começar pelo bloqueador mais grave (B1). O spike vem antes
porque **três suposições do desenho podem estar erradas**, e cada uma muda o plano
inteiro:

- O ambiente local roda **Python 3.14.5** e **websockets 16.0**. A plataforma pode
  não oferecer 3.14; a versão do Python pode precisar ser fixada mais baixa.
- `SERVER_HOSTS = ["0.0.0.0", "::"]` existe por causa de uma particularidade do
  Windows (`IPV6_V6ONLY`). No Linux, onde `bindv6only` costuma ser 0, ligar nos dois
  pode conflitar.
- O cold start de "cerca de um minuto" é o que a documentação diz. Quero o número
  **medido** com este módulo de 35.522 linhas e seus catálogos JSON, não o número da
  brochura.

Se o cold start real for de três minutos, ou se a lib não subir, o desenho muda — e
é melhor descobrir isso antes de investir nos SP1–SP4.

### Escopo

Subir o `server.py` **como está**, no Render free, e medir. Sem banco, sem CDN, sem
mudanças de segurança. É deliberadamente descartável.

O único trabalho de código admitido é o mínimo para o processo subir:

- `requirements.txt` com `websockets`
- ler a porta de `PORT` além de `LFH_PORT`
- se o duplo bind falhar no Linux, escolher a família de escuta por ambiente

**Nada além disso.** Qualquer outra correção que o spike revele vira item de SP1–SP4,
não trabalho do SP0.

### Segurança durante o spike

O ambiente do spike expõe os 17 handlers de escrita (B1) — é exatamente o estado que
o SP1 vai consertar. Mitigação: **a URL não é divulgada, nenhuma conta real é criada,
nenhum dado real sobe, e o serviço é destruído ao fim da medição.** O spike não deve
durar mais que uma sessão.

### O que medir

| Medida | Como | Por que importa |
|---|---|---|
| O processo sobe? | log do deploy | valida Python + `websockets` na plataforma |
| Bind funciona? | conexão externa | valida `SERVER_HOSTS` no Linux |
| WebSocket completa handshake e troca mensagens? | cliente mínimo | é o requisito central |
| **Cold start real** | cronometrar após 15+ min ocioso, repetido 3× | define a UX de warm-up do SP4 |
| Tempo até o 1º byte com o servidor quente | idem | separa hibernação de lentidão de rede |
| Memória em repouso | painel da plataforma | o free tem teto; o módulo carrega catálogos grandes |
| Cartão foi exigido em algum ponto? | observação | é a restrição declarada do autor |

### Critérios

**Sucesso:** o processo sobe, aceita WebSocket de fora, e o cold start medido fica
dentro de uma faixa que o SP4 consiga disfarçar com UX de warm-up.

**Falha que muda o desenho:** a plataforma não roda o Python necessário; o WebSocket
não passa; o cold start é grande demais para disfarçar; ou pedem cartão. Nesse caso
o desenho volta à mesa — e a alternativa mais provável é reabrir a conversa de
orçamento, porque as outras opções US$ 0 estritas são estruturalmente piores.

### Entregável

Um registro do que foi medido — números, não impressões — que vira a base dos specs
de SP1–SP4. O serviço é destruído depois.

---

## Fora de escopo

- **UGC multi-autor.** Conteúdo hoje é estado global e mutável de módulo
  (`MONSTER_DEFS`, `WORLD_ADVENTURES`, `CITY_SHOPS`, `dungeons/`,
  `itens_personalizados.json`) — existe *um* mundo, sem dono. UGC precisa de
  conteúdo com autor, versão e visibilidade, mais moderação e cotas. É um projeto
  inteiro.
- **Grupos públicos / matchmaking.** Hoje só existe entrada por código de sala.
- **Progressão de herói entre grupos.** Os 6 heróis da conta são explicitamente só
  cosméticos; o poder vive em `savegame.characters`, uma instância por campanha.
  Mudar isso é decisão de design de jogo, não de infraestrutura.
- **Persistir masmorra em andamento através de reinício** (B6).
- **Tradução do editor.** Continua fora, como já registrado no roadmap de idioma.

---

## O que pode invalidar este desenho

1. **O SP0 falhar.** Ver critérios acima.
2. **Termos de plano gratuito mudarem.** Os limites citados foram verificados em
   2026-08-28 na documentação dos próprios provedores; planos gratuitos mudam com
   frequência. Reverificar antes do SP4.
3. **O autor reabrir o orçamento.** Um VPS de ~US$ 5/mês tornaria SP2 e SP3
   opcionais e deixaria o trabalho quase todo em SP1. Se em qualquer momento os
   US$ 0 estritos deixarem de ser obrigatórios, este desenho encolhe muito.

---

## Fontes

- [Render — free tier](https://render.com/docs/free)
- [Cloudflare Pages — limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Neon — free tier FAQ](https://neon.com/faqs/managed-postgres-databases-free-tier)
