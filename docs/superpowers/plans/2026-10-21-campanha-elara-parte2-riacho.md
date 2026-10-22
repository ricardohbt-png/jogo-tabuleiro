# O Resgate de Elara — Plano 2: Ramo A (Vila do Riacho)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o Ramo A da campanha (quem escolheu seguir as moças): as conversas de sondagem na Vila do Riacho, a masmorra da casa do morador comprado, a escolha do grupo sobre o bardo da rede (matar, interrogar ou poupar) com tratamento que o jogo lembra, e a masmorra do celeiro onde as moças são resgatadas. O plano termina deixando gravados os fatos que Graciero (plano 3) vai ler.

**Architecture:** Mesmo molde do plano 1: um gerador idempotente (`tools/gerar_elara_riacho.py`) grava conversas nas cenas de taverna do Riacho e os destinos do mapa-múndi; os dois mapas novos saem de um construtor determinístico no estilo de `tools/charcos_mapas.py` (classe `Cena`). Uma única peça de motor é necessária: uma conversa precisa poder gravar **mais de um fato** (hoje grava um só), porque cada escolha do bardo precisa gravar o próprio fato e o fato de "decidido" que esconde as outras opções.

**Tech Stack:** Python (`server.py`, unittest), JS vanilla (editor de cidades, teste em node), JSON de dados.

**Spec:** `docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md` (seção "Ramo A")
**Depende de:** plano 1 já na master (`heroi_no_grupo`, fatos `elara_*`, `elara_ramo_a`).

## Global Constraints

- Português em todo texto de jogo; conteúdo autoral não leva chave de idioma.
- Nunca citar Ferdinand, Vael'mon nem "rede de bardos" por nome nos textos: o jogador só sente que o bardo "avisa gente de fora" e que há "alguém maior".
- `server.py`, `game.js`, `CLAUDE.md` e os `.js` de `tools/` têm quebra de linha própria: edite por ferramenta ou script que preserve.
- Nada de arte nova: retratos e fundos reaproveitam `assets/` (o autor sobe a arte depois). Os monstros são fichas existentes; o monstro `bandido` está sendo criado em outra frente: use a constante `TIPO_BANDIDO = "goblin_combatente"` num só lugar do gerador de mapas, para trocar depois.
- Os mapas do Riacho são **novos** e do Claude (`elara_riacho_*.json`); ao reexecutar, o gerador recusa sobrescrever um mapa que o autor editou depois (assinatura, como `gerar_campanha_sombras.assinatura`/`Conflito`) sem `--forcar`.
- O grupo **sempre** salva as moças no Ramo A; o que muda são as consequências do bardo.
- O trio matar/interrogar/poupar e os momentos de tratamento são **exclusivos** entre si e nunca ficam todos bloqueados nem todos abertos de novo.
- Nível esperado do grupo: 2 (`expected_party {heroes: 4, level: 2}`); relatório de ND por sala deve cair em Equilibrada/Difícil.

## Fatos (contrato com o plano 3 — nomes estáveis)

| Fato | Quem grava | Significa |
|---|---|---|
| `elara_t1_gentil` / `elara_t1_ameaca` / `elara_t1_ignorou` | conversa do bardo na sondagem | como o grupo tratou o bardo no 1º encontro (exclusivos, um só) |
| `elara_t1_feito` | cada opção do 1º encontro (junto do seu fato) | o 1º encontro com o bardo acabou; esconde as outras opções |
| `elara_bardo_final` | cada ação final do poupado (junto do seu fato) | a ação final foi escolhida; esconde a outra |
| `elara_bardo_exposto` | objetivo da casa | o grupo provou a cumplicidade do bardo |
| `elara_bardo_decidido` | cada opção do confronto (junto do seu fato) | o confronto acabou; esconde as outras opções |
| `elara_bardo_morto` / `elara_bardo_interrogado` / `elara_bardo_poupado` | opção do confronto | o que o grupo fez |
| `elara_bardo_gentil` / `elara_bardo_maltratado` | ações finais do bardo poupado | tratamento (só no ramo "poupado") |
| `elara_vila_abalada` | opção "interrogado" | a vila perdeu a lealdade ao grupo |
| `elara_leonel_cauteloso` | opção "morto" | o Leonel foi avisado; Graciero fica mais difícil (plano 3) |
| `elara_mocas_salvas` | objetivo do celeiro | as moças foram resgatadas; a Elara já está em Graciero |

Regra de leitura em Graciero (plano 3): **ajuda** = `elara_bardo_poupado` + `elara_bardo_gentil` e **sem** `elara_bardo_maltratado`; **trai** = `elara_bardo_maltratado`.

## Review Focus

- Escolher uma opção do confronto esconde as outras duas **e** a própria (uso único); recarregar o jogo salvo depois da escolha não a oferece de novo.
- Grupo que ignora o bardo na sondagem e escolhe poupar sem nenhuma ação final: o fato de tratamento fica ausente e o plano 3 trata como "hesita" (nem ajuda nem trai).
- Grupo sem o bardo da taverna no caminho (vai direto à casa): a casa ainda abre e o confronto ainda existe.
- Mapa do celeiro: as moças (`prisoner`) só saem pela saída; morrer não encerra a campanha (sem `se_falhar` letal neste ramo).
- Nenhuma conversa do Riacho aparece para quem **não** escolheu o Ramo A (sem `elara_ramo_a`).
- Reexecutar o gerador duas vezes não duplica conversas nem muda mapas já gravados.

---

### Task 1: Conversa que grava vários fatos

**Files:**
- Modify: `server.py` (`_clean_scene_conversations` ~897; `handle_scene_npc` ~18060: onde lê `effect.get("fato")`)
- Modify: `tools/editor_city.js` (campo "Fatos adicionais (separe por vírgula)" na conversa)
- Test: `tools/test_conversa_fatos.py`, `tools/test_conversa_fatos_editor.js`

**Interfaces:**
- Produces: `efeito.fatos: list[str]` (até 6 itens de até 100 caracteres, opcional), gravada junto de `efeito.fato`; `_clean_scene_conversations` só inclui a chave quando houver itens (conversas antigas ficam idênticas byte a byte).

- [ ] **Step 1: Write the failing test** `tools/test_conversa_fatos.py`: `test_limpa_e_limita` (lista suja → só textos válidos, no máximo 6, sem a chave quando vazia, conversa antiga inalterada); `test_conversa_grava_todos_os_fatos` (sala na cidade com cena de teste montada em `S.CITY_SCENES`, `handle_scene_npc` grava `fato` e cada item de `fatos`); `test_uso_unico_ainda_vale`.
- [ ] **Step 2: Run** `python -X utf8 tools/test_conversa_fatos.py` — Expected: FAIL.
- [ ] **Step 3: Implement** em `_clean_scene_conversations` (campo `fatos` dentro de `efeito`) e em `handle_scene_npc` (adiciona cada fato a `self.fatos`, antes do `push` que já existe).
- [ ] **Step 4: Editor** — input de texto no formulário da conversa em `editor_city.js`, lido/gravado como lista; `test_conversa_fatos_editor.js` confere o roundtrip estático (carregar → salvar mantém `fatos`).
- [ ] **Step 5: Run** `test_conversa_fatos.py`, `node tools/test_conversa_fatos_editor.js`, `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_zumbra_charcos.py`, `test_campanha_charcos.py`, `test_elara_fluxo.py`. Expected: PASS (falhas pré-existentes inalteradas).
- [ ] **Step 6: Commit** `feat(cenas): conversa pode gravar varios fatos`.

---

### Task 2: Os dois mapas do Riacho

**Files:**
- Create: `tools/elara_riacho_mapas.py` com `masmorra_casa()` e `masmorra_celeiro()` (retornam dicts de masmorra prontos), `TIPO_BANDIDO`
- Create (pelo gerador da Task 3): `dungeons/elara_riacho_casa.json`, `dungeons/elara_riacho_celeiro.json`
- Test: `tools/test_elara_riacho_mapas.py`

**Interfaces:**
- Consumes: `Cena`, `Mapa`, `masmorra` de `tools/charcos_mapas.py` / `tools/gerar_campanha_sombras.py` (leia o `masmorra_aldeia` dos Charcos para o padrão de refém único, mecanismo e objetivo).
- Produces: `masmorra_casa()` — **A casa do morador comprado** (id `elara_riacho_casa`, ambiente `masmorra`, 3 salas: sala da frente, quarto, porão): armadilhas leves (dardos, urso), 2 `TIPO_BANDIDO` de emboscada, um baú-chave com a carta que prova a cumplicidade, objetivo principal `open_key_chest` com `fato: "elara_bardo_exposto"`. `masmorra_celeiro()` — **O celeiro** (id `elara_riacho_celeiro`, ambiente `ar_livre`, 4 salas: pátio, curral, celeiro, palheiro): 4–6 bandidos (um deles `target`), armadilhas leves, **refém único "As Moças"** (`prisoner`), objetivo principal `rescue_prisoner` com `fato: "elara_mocas_salvas"`, xp de objetivo; sem `se_falhar` letal.
- Cada mapa: `expected_party {heroes: 4, level: 2}`, `marcador_entrada: "poste"` no celeiro (ar livre), `saida_permitida: true`, todas as salas alcançáveis (`salas_alcancaveis`).

- [ ] **Step 1: Write the failing test** `tools/test_elara_riacho_mapas.py`: ambos validam (`S.validar_dungeon`); todas as salas alcançáveis da entrada; o objetivo e o `fato` certos em cada um; o celeiro tem `prisoner` e o `target` é um bandido; a casa tem pelo menos 2 armadilhas e um baú-chave; `nd_por_sala`/`faixa` não classificam nenhuma sala como "Mortal"; determinismo (chamar duas vezes devolve dicts iguais); nenhum texto de fala/baú cita "Ferdinand" ou "Vael".
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_riacho_mapas.py` — Expected: FAIL (módulo inexistente).
- [ ] **Step 3: Implement** `tools/elara_riacho_mapas.py`. Fale com o jogador por `fala` e pelo texto do baú: a carta da casa cita "o bardo da taverna" como quem paga e avisa (sem nomes de rede); a fala final do celeiro diz que "a moça do Templo, a irmã do mago, já seguiu viagem para Graciero".
- [ ] **Step 4: Run** o teste da tarefa e `test_campanha_charcos_mapas.py`, `test_preview_editor.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): mapas da casa do morador e do celeiro (Riacho)`.

---

### Task 3: Conversas, tratamento do bardo e destinos do Riacho

**Files:**
- Create: `tools/gerar_elara_riacho.py`
- Modify (pelo gerador): `city_scenes.json` (conversas `elara_*` nos slots `barman`, `mesa_fundo`, `serva_centro` e `bardo` da taverna da `vila_riacho`), `world_adventures.json` (destinos `elara_riacho_casa`, `elara_riacho_celeiro`), `dungeons/elara_riacho_*.json`
- Test: `tools/test_elara_riacho_dados.py`, `tools/test_elara_riacho_fluxo.py`

**Interfaces:**
- Consumes: `fatos` por conversa (Task 1), mapas (Task 2), fatos do plano 1 (`elara_ramo_a`).
- Produces (conversas, todas só com `elara_ramo_a`, texto autoral, `uma_vez` salvo indicado):
  - **Sondagem:** `elara_riacho_barman` (medo da vila), `elara_riacho_mesa` (um homem nervoso aponta a casa do Tomé), `elara_riacho_serva` (rumor: "tropeiros" no celeiro, só depois de `elara_bardo_exposto`).
  - **Tratamento 1** (slot `bardo`, uma escolha por vez, exclusivas pelo fato `elara_t1_feito` que cada opção também grava via `fatos`): `elara_t1_gentil` ("pagar-lhe uma bebida"), `elara_t1_ameaca` ("ameaçá-lo"), `elara_t1_ignorou` ("deixá-lo em paz"), cada uma gravando o próprio fato.
  - **Confronto** (slot `bardo`, só com `elara_bardo_exposto` e sem `elara_bardo_decidido`): `elara_bardo_matar` (fatos `elara_bardo_morto`, `elara_leonel_cauteloso`, `elara_bardo_decidido`), `elara_bardo_interrogar` (`elara_bardo_interrogado`, `elara_vila_abalada`, `elara_bardo_decidido`), `elara_bardo_poupar` (`elara_bardo_poupado`, `elara_bardo_decidido`).
  - **Ações finais do poupado** (slot `barman`, só com `elara_bardo_poupado` e sem `elara_bardo_final`, cada opção grava também `elara_bardo_final`): `elara_bardo_escoltar` (fato `elara_bardo_gentil`) e `elara_bardo_entregar` (fato `elara_bardo_maltratado`).
- Produces (destinos): `elara_riacho_casa` (requisito `elara_ramo_a`, oculto até liberar, `ocultar_apos_concluir`, fome/sede 1) e `elara_riacho_celeiro` (requisito `elara_bardo_decidido`, oculto até liberar, `ocultar_apos_concluir`, fome/sede 1, `renome_recompensa` 1); posições perto de `vila_riacho` no mapa-múndi.
- O gerador preserva conversas do autor (só reescreve as de id `elara_*`), preserva a posição dos destinos e protege mapas editados por assinatura (`tools/.elara_riacho_assinaturas.json`).

- [ ] **Step 1: Write the failing tests.** `test_elara_riacho_dados.py` (conversas e destinos de `G.conversas_*()`/`G.destinos()`: ids acima existem; as três opções do confronto exigem `sem_fato: elara_bardo_decidido`; cada opção do confronto grava o próprio fato **e** `elara_bardo_decidido`; escoltar/entregar são exclusivos por `elara_bardo_final`; nenhum texto cita Ferdinand/Vael; nenhuma conversa aparece sem `elara_ramo_a`). `test_elara_riacho_fluxo.py` (motor real, mesmo molde de `test_elara_fluxo.py`): sem o ramo nada aparece; com o ramo aparecem sondagem e as três opções de tratamento; escolher uma de tratamento esconde as outras; sem `elara_bardo_exposto` o confronto não aparece, com ele aparecem as três; escolher "poupar" esconde as três, grava `elara_bardo_decidido` e abre as duas ações finais; escolher uma ação final esconde a outra; os destinos aparecem na ordem certa (`_aventura_visivel`: casa com o ramo A; celeiro só com `elara_bardo_decidido`); um save recarregado (`_relogios_de_save`-style: fatos viajam em `sg["fatos"]`) não reoferece o que já foi usado.
- [ ] **Step 2: Run** os dois — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/gerar_elara_riacho.py` no molde de `gerar_campanha_elara.py` (`--simular`, só toca em ids `elara_*` e nos dois mapas novos; `aplicar_mapas` grava os dois JSON via `masmorra_casa()`/`masmorra_celeiro()` respeitando a assinatura).
- [ ] **Step 4: Run** o gerador (`--simular`, depois de verdade) e os dois testes; confira `git status` (só `elara_*`, `city_scenes.json`, `world_adventures.json`, `tools/editor_dungeons.js`, assinaturas).
- [ ] **Step 5: Run** `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_campanha_elara_parte1.py`, `test_elara_fluxo.py`, `test_masmorra_sequenciada.py`, `test_zumbra_charcos.py`. Expected: PASS (instáveis conhecidos inalterados).
- [ ] **Step 6: Commit** `feat(elara): Ramo A (Vila do Riacho): conversas, bardo e destinos`.

---

### Task 4: Documentação e prova final

**Files:**
- Modify: `CLAUDE.md` (seção "O Resgate de Elara — Ramo A (Riacho)" com os fatos, os destinos, o `efeito.fatos` e os testes)
- Test: suítes das tarefas 1–3 e `tools/dividas.py --strict`

- [ ] **Step 1:** Documentar em `CLAUDE.md` o `efeito.fatos`, a tabela de fatos do Ramo A e o contrato de leitura para Graciero.
- [ ] **Step 2:** Rodar todas as suítes das tarefas e `dividas.py --strict`; anotar quais falhas já existiam na base.
- [ ] **Step 3: Prova com o motor real:** sala com Pedro e o bardo da taverna no grupo: aceitar o pedido (plano 1), escolher o Ramo A, conversar, vencer a casa (objetivo grava `elara_bardo_exposto`), decidir "poupar", escoltar, abrir o celeiro e vencer (grava `elara_mocas_salvas`); repetir com "matar" e "interrogar" e conferir os fatos de cada caminho.
- [ ] **Step 4: Commit** `docs: Ramo A (Riacho) da campanha de Elara`.
