# SP1 — Modo público: segurança antes de abrir o cadastro — Design

**Data:** 2026-08-30
**Pertence a:** hospedagem online (`2026-08-28-hospedagem-online-design.md`)
**Depende de:** SP0 (`plans/2026-08-28-sp0-resultados.md`) e da troca da camada de
rede (`2026-08-29-camada-de-rede-aiohttp-design.md`), ambos concluídos.

---

## Por que isto existe

O jogo já sobe numa hospedagem gratuita e responde pela internet. **Falta o que
impede que abrir o cadastro seja irresponsável.** São os bloqueadores B1, B2, B7
e B9 do desenho de hospedagem, todos medidos, nenhum resolvido.

Nada aqui é otimização. É a diferença entre um link privado entre amigos e um
endereço que qualquer pessoa pode achar.

## O que está errado hoje, medido

**B1 — 17 handlers gravam em disco sem autenticação nenhuma.** Despachados em
`server.py` **antes de qualquer noção de sala ou conta**:

```
upload_story  upload_scene_media  save_scenes  upload_tavern_art  upload_city_art
upload_refugio_art  save_world_cities  save_city_shops  save_world_adventures
upload_dungeon  upload_campaign  upload_custom_monster  upload_custom_item
upload_item_art  upload_monster_art  upload_prisoner  objeto_upload
```

Aceitam até 25 MB por arquivo e sobrescrevem conteúdo do jogo.

**B2 — credencial fraca e sem freio.** PIN de 4 dígitos (10.000 combinações),
sem limite de tentativas, sem atraso, sem bloqueio. Pior: o PBKDF2 de 100k
iterações roda **no laço de eventos**, então uma rajada de tentativas também
trava a partida de todos os outros jogadores.

**B7 — vazamentos.** Salas vazias nunca saem do dict `rooms`; `groups/` tem
**745 arquivos** para 15 savegames.

**B9 — o servidor não valida o header `Origin`.** Nenhuma ocorrência no arquivo.

## Decisões do autor

| Pergunta | Resposta |
|---|---|
| Credencial | **Senha de verdade**, mínimo **8 caracteres**, sem exigir maiúscula/número/símbolo |
| Contas existentes | **Apagar.** Serão criadas novas para teste |
| Editores online | **Não.** Só locais |

**Por que 8 caracteres e nada de composição:** exigir maiúscula, número e
símbolo empurra as pessoas para `Senha1!` e para reusar a senha de outro site. O
comprimento protege mais do que a variedade forçada.

**Por que apagar as contas simplifica tudo:** sem migração, o código tem um
caminho só. É o que permite renomear o campo `pin_hash` → `password_hash` em vez
de conviver com dois formatos.

**Quando apagar:** *junto* com a entrada da senha, não antes. Apagar agora
deixaria o autor sem conseguir entrar em nada até o SP1 ficar pronto — os 15
savegames viram inalcançáveis, porque não há como logar numa conta que não
existe. É uma troca só, num momento só.

---

## Desenho

### 1. Senha no lugar do PIN

`hash_pin`/`verify_pin` já são PBKDF2-SHA256 com salt por conta e **aceitam
qualquer texto** — a única barreira é a regra de formato em `create_account`
(`re.fullmatch(r"\d{4}", …)`).

- Servidor: regra passa a ser comprimento ≥ 8; campo `pin_hash` →
  `password_hash`; funções renomeadas para `hash_password`/`verify_password`.
- Cliente: **3 pontos** em `game.js` — o rótulo (`ui.connect.pin_label`), o
  `<input id="input-pin">` (saem `inputmode="numeric"` e `maxlength="4"`) e a
  validação `/^\d{4}$/`. Mais as chaves de idioma correspondentes.
- Dados: `accounts/*.json`, `savegames/*.json` (e `.bak`) e `groups/*.json` são
  apagados na mesma mudança. Todos são dados de teste — os savegames se chamam
  `twste`, `Teste Bau Refugio`, `Diag Lobby`.

### 2. PBKDF2 fora do laço de eventos

`hash_password` e `verify_password` passam a ser chamados por
`asyncio.to_thread`. **É pré-requisito do item 3**: sem isso, o próprio limite de
tentativas viraria uma arma — cada tentativa recusada ainda custaria ~100 ms de
laço travado para todos.

Com o cálculo fora do laço, o número de iterações deixa de penalizar os outros
jogadores e pode subir sem medo. Não faz parte deste escopo definir o número
novo; o que importa aqui é tirar do caminho crítico.

### 3. Limite de tentativas, por conta e por IP

Contador em memória com janela deslizante e espera crescente. Por conta **e** por
origem, porque cada um cobre um ataque diferente: por conta impede insistir numa
vítima; por origem impede varrer muitas contas com uma senha comum.

**O endereço do cliente precisa chegar até lá, e hoje não chega.** O `handler`
recebe o `_WS`, que não conhece o peer. A solução é **estender o `_WS` para
expor o endereço** — é exatamente para isso que ele existe, isolar a biblioteca
do resto do código. A alternativa (passar o `request` do aiohttp adiante)
espalharia a biblioteca justamente onde acabamos de contê-la.

**Armadilha que quase passou:** atrás do proxy da hospedagem,
`request.remote` é o **IP do proxy**, não o do jogador. Usá-lo cru faria todos os
jogadores compartilharem um único balde — e o primeiro atacante trancaria o jogo
inteiro. O endereço real vem em `X-Forwarded-For`.

Mas `X-Forwarded-For` é um header, e **header é forjável**: fora de um proxy
confiável, qualquer cliente pode inventar um IP diferente a cada tentativa e
anular o limite. Portanto: **confiar no `X-Forwarded-For` apenas no modo
público** (onde sabemos que há um proxy na frente) e usar `request.remote`
localmente. É o modo público, do item 4, que autoriza essa confiança.

### 4. Modo público

Variável de ambiente `LFH_PUBLIC=1`. Quando ligada:

- os **17 handlers de escrita** são recusados;
- o `Origin` é validado (item 5);
- o `X-Forwarded-For` passa a ser confiável (item 3).

Desligada — o padrão, e o que vale na máquina do autor — **nada muda**: os
editores funcionam como hoje. O modo é um portão único, e não uma flag por
handler, para que não exista a possibilidade de esquecer um.

### 5. `Origin` restrito

No modo público, o handshake de WebSocket só é aceito de uma lista de origens
(variável `LFH_ORIGINS`). Sem a lista, o servidor recusa em vez de aceitar
qualquer origem — falhar fechado, não aberto.

Isto impede que outro site abra conexões contra o servidor em nome de quem
estiver visitando. Com os editores desligados o impacto cai muito, mas a
restrição é barata.

### 6. Limpeza

- Sala sem nenhum conectado sai do dict `rooms`.
- Arquivo de grupo sem savegame que o referencie é removido; os 745 atuais somem
  junto com a limpeza de dados do item 1.

---

## O que NÃO pode mudar

- **O jogo local.** Sem `LFH_PUBLIC`, o comportamento é o de hoje, editores
  inclusive. É o que as suítes existentes provam.
- **O protocolo.** Nenhuma mensagem nova além do que a senha exige.
- **A camada de rede.** O SP1 não encosta no que a troca para `aiohttp` fez.

## Critérios de aceitação

1. Sem `LFH_PUBLIC`: `test_rede_local`, `test_http_camada`, `test_deploy_config`,
   `test_savegames`, `test_modo_mestre` verdes, e os editores respondendo.
2. Com `LFH_PUBLIC=1`: cada um dos 17 handlers recusado; teste que **enumera a
   lista** e falha se um handler novo aparecer sem passar pelo portão.
3. Senha < 8 caracteres recusada na criação; senha correta entra; senha errada
   não entra.
4. Após N tentativas erradas, a conta é barrada por um tempo — e uma tentativa
   correta na mesma janela **também** é barrada (senão o limite não limita).
5. O limite por origem não confunde dois jogadores atrás do mesmo proxy quando
   `X-Forwarded-For` está presente e o modo é público.
6. Login não bloqueia o laço: com uma tentativa em curso, outra conexão continua
   recebendo resposta.
7. `Origin` fora da lista é recusado no modo público; aceito fora dele.
8. Sala que perde o último jogador sai de `rooms`.

## Fora de escopo

- Recuperação de senha, e-mail, verificação de conta — não há e-mail no jogo.
- Papéis/permissões entre jogadores.
- UGC multi-autor (projeto próprio).
- Escolher o novo número de iterações do PBKDF2 (só tirar do laço).
- SP2 (estáticos no CDN), SP3 (Postgres), SP4 (empacotamento e warm-up).

## Riscos

1. **Apagar dados é irreversível.** São dados de teste e o autor autorizou, mas a
   remoção deve acontecer num passo explícito e anunciado, nunca como efeito
   colateral de outra mudança.
2. **O portão dos 17 handlers pode ser furado por esquecimento.** Por isso o
   critério 2 exige um teste que enumere a lista: um handler de escrita novo,
   criado no futuro, deve **falhar o teste** até ser incluído.
3. **`X-Forwarded-For` confiado no lugar errado** anula o limite por origem.
   Confiar apenas no modo público é o que separa os dois casos.
4. **Limite agressivo demais tranca jogadores legítimos.** Amigo que erra a senha
   três vezes não pode ficar de fora da partida. A janela e o número de
   tentativas devem ser generosos — o objetivo é impedir 10.000 tentativas, não
   punir três.
