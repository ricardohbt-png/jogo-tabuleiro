# O Resgate de Elara — Plano 5: a rota opcional do Olho (as montanhas)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a rota opcional do Olho de Arveluz, só para quem seguiu as moças (ramo A): três etapas emendadas pelas montanhas acima de Graciero, mais difíceis que o resto, até interceptar a caravana que leva a relíquia. Quem tem a dica pelo bardo poupado sobe guiado por ele e o vê ser morto por um assassino que o grupo não consegue impedir; quem a tem pelo Gilo moribundo sobe sem ele. Recuperar o Olho muda o final de Graciero (o slide já existe).

**Architecture:** Mesmo molde dos planos 3 e 4: gerador idempotente (`tools/gerar_elara_montanha.py`), mapas determinísticos pelo construtor `Cena`, fichas pelo caminho do editor. **Nenhuma peça de motor nova:** a diferença entre as duas vias é feita por `requisito` nas falas do mapa (já suportado desde o plano 1), a recompensa do Olho é o item de recompensa do objetivo principal (`reward.items`), e a fuga do assassino reusa `fuga_chefe`.

**Tech Stack:** Python (`server.py`, unittest), JSON de dados.

**Spec:** `docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md` (seção "Rota opcional do Olho")
**Depende de:** planos 1–4 na master (fatos `elara_dica_montanha`, `elara_bardo_ajudou`, `elara_ramo_a`, item `olho_de_arveluz`, `tambem_fato`, `fuga_chefe`, falas com `requisito`, `outro_rota` condicional).

## Global Constraints

- Português em todo texto de jogo; conteúdo autoral não leva chave de idioma.
- Nunca citar Ferdinand, Vael'mon, "rede de bardos" nem Porto Saledo como mandante: o assassinato é **obviamente encomendado** (moeda de prata sem cunho no peito do bardo, flecha de ponta tingida), mas não se sabe por quem. O destino da caravana é só "o norte", "as montanhas".
- Rota só do ramo A: nunca visível para o ramo B (o ramo B já tem o Olho dos pertences do Gilo).
- A rota nunca é obrigatória: Graciero termina sem ela; ela some quando o Leonel é vencido (`elara_leonel_vencido`) para não abrir depois do final.
- O bardo guia é **morto sem que o grupo possa impedir**: a cena é de falas (nenhum monstro, nenhum teste); nenhuma ação do jogador a altera.
- Nada de a rota deixar o grupo sem saída: só a etapa 1 permite sair pela escada; as outras duas são emendadas sem retorno e sem poste de saída (como a Maré do Charco). A etapa 3 tem `exit` e objetivo alcançável.
- Mapas `elara_montanha_*` são do Claude; o gerador recusa sobrescrever um que o autor editou depois (assinatura) sem `--forcar`. Conversas do autor em Graciero ficam intactas.
- Nível esperado: `expected_party {heroes: 4, level: 5}` (poder 20). Rota "mais difícil": ND por sala entre 9 e 14, nunca acima de 0,8 × poder × 1,0 = 16.

## Fatos (contrato)

| Fato | Quem grava | Significa |
|---|---|---|
| `elara_dica_montanha` | planos 4 (Praça viva ou bardo que ajuda) | a caravana sobe a serra (abre a rota, junto com `elara_ramo_a`) |
| `elara_montanha_trilha` / `elara_montanha_desfiladeiro` | objetivos das etapas 1 e 2 | trechos vencidos |
| `elara_assassino_fugiu` | `fuga_chefe` do assassino | o assassino foi vencido e sumiu |
| `elara_rota_olho_vencida` | `fatos` do objetivo da etapa 3 | a caravana foi interceptada |
| `elara_olho_recuperado` | `fatos` do objetivo da etapa 3 | o Olho está com o grupo (item `olho_de_arveluz` no baú de recompensa) |

## Review Focus

- A rota só aparece para quem tem `elara_dica_montanha` **e** `elara_ramo_a`, e deixa de aparecer com `elara_leonel_vencido`; o ramo B com a dica da Praça viva nunca a vê.
- Com `elara_bardo_ajudou`, as falas do guia e da morte dele aparecem; sem, nenhuma delas e nenhuma menção ao bardo; as falas comuns aparecem nos dois casos.
- O Olho vai para o baú de recompensa mesmo se o assassino fugir (e só então); concluir a rota e depois o Leonel mostra o slide "Olho volta ao Templo"; sem a rota, "não está aqui".
- Nenhuma fala da cena do bardo morto dá a entender que o grupo poderia ter agido.
- Reexecutar o gerador não duplica a conversa nova de Graciero, não regrava mapa editado e preserva a posição que o autor deu ao destino.

---

### Task 1: Fichas da rota

**Files:**
- Create: `tools/elara_montanha_fichas.py` com `ficha_assassino()` e `ficha_bardo_agente()`
- Modify (pelo gerador, Task 3): `monstros_personalizados.json`, `tools/editor_monsters_custom.js`, `src/lang/catalogo.js` (via `gerar_vocabulario.py`)
- Test: `tools/test_elara_montanha_fichas.py`

**Interfaces:**
- Produces: `assassino_da_caravana` — derivada de `elara_gilo_ficha.ficha_gilo()` (como `elara_graciero_fichas`), `cr 3`, ~45 PV, CA 16, dois ataques furtivos de adaga, `boss`; `bardo_da_caravana` — derivada do `soldado`, `cr 2`, ~30 PV, ataque à distância se a base permitir (senão corpo a corpo), sem texto que cite a rede. Ambas passam em `S._validate_custom_monster`; `S.monster_cr` dá 3 e 2.

- [ ] **Step 1: Write the failing test** `test_elara_montanha_fichas.py`: as duas validam, `monster_cr` 3 e 2, o assassino é `boss`, nenhum texto cita Ferdinand/Vael/rede/Porto Saledo.
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_montanha_fichas.py` — Expected: FAIL.
- [ ] **Step 3: Implement** o módulo (molde: `tools/elara_graciero_fichas.py`).
- [ ] **Step 4: Run** o teste — Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): fichas do assassino e do bardo da caravana`.

---

### Task 2: Os mapas das montanhas

**Files:**
- Create: `tools/elara_montanha_mapas.py` com `masmorra_trilha()`, `masmorra_desfiladeiro()`, `masmorra_caravana()`
- Create (pelo gerador, Task 3): `dungeons/elara_montanha_1.json`, `elara_montanha_2.json`, `elara_montanha_3.json`
- Test: `tools/test_elara_montanha_mapas.py`

**Interfaces:**
- Consumes: `Cena`/`montar_fila`/`obj` de `tools/charcos_mapas.py`, fichas da Task 1, `SOLDADO`/`ORC`/`DUAL`/`ARQUEIRO` de `elara_graciero_mapas.py`.
- Produces (ambiente `ar_livre`, piso/parede de montanha — confira os nomes em `S.MATERIAIS`: piso de pedra clara e parede `rocha`/`rocha_marrom` —, `marcador_entrada: "poste"`, `expected_party {4, 5}`, 3 salas cada):
  - **Trilha do Contrabando** (`elara_montanha_1`): guardas e arqueiros de emboscada, armadilhas de montanha (`fosso_estacas`, `rede`, `armadilha_urso`), `saida_permitida` verdadeiro; objetivo `reach_exit` com `fato: elara_montanha_trilha`. Falas: comum ("a trilha de quem não quer ser visto"); **do guia** (`requisito {fato: elara_bardo_ajudou}`): o bardo indica o caminho e avisa onde a caravana descansa; **sem guia** (`requisito {sem_fato: elara_bardo_ajudou}`): marcas deixadas pelo Gilo nas pedras.
  - **O Desfiladeiro** (`elara_montanha_2`): `saida_permitida: false`, ND no teto da rota; objetivo `reach_exit` com `fato: elara_montanha_desfiladeiro`. Falas do guia: ele avança à frente, ouve-se um zumbido seco e ele cai com uma flecha de ponta tingida e uma moeda de prata sem cunho no peito, sem que ninguém tenha tempo de reagir ("não houve tempo"); sem guia: o grupo acha, mais à frente, o rastro de alguém que também subiu e foi calado antes.
  - **A Caravana** (`elara_montanha_3`): `saida_permitida: false`; sala 0 guardas, sala 1 o `bardo_da_caravana` e músicos (soldados), sala 2 o `assassino_da_caravana` como `target` e `boss`, com `fuga_chefe {fato: elara_assassino_fugiu, texto}` (o texto diz que ele some "como quem tem mais uma ordem a cumprir", sem nomes). Objetivo principal `kill_target` com `itens=["olho_de_arveluz"]` na recompensa e `fatos: [elara_rota_olho_vencida, elara_olho_recuperado]`; falas finais: comum (o baú do Olho, pesado e quente) e, com `elara_bardo_ajudou`, uma homenagem curta ao guia.
- Todos: ND por sala entre 9 e 14 (nunca acima de 16); determinísticos (sementes 5101–5103).

- [ ] **Step 1: Write the failing test** `test_elara_montanha_mapas.py`: os três validam, determinísticos, salas alcançáveis (`salas_alcancaveis`), ND por sala na faixa, `expected_party`, poste, `saida_permitida` (só a 1ª verdadeira); objetivos e fatos exatos; Olho só como `reward.items` da etapa 3; assassino único, `target`, `boss`, com `fuga_chefe`; as falas do guia têm `requisito.fato == elara_bardo_ajudou`, as "sem guia" têm `sem_fato` e as comuns nenhum, e nenhuma fala do guia contém verbo que sugira que o grupo agiu ("salvar", "impedir"); nenhum texto cita Ferdinand/Vael/rede/Porto Saledo.
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_montanha_mapas.py` — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/elara_montanha_mapas.py` (molde: `elara_graciero_mapas.py`).
- [ ] **Step 4: Run** o teste da tarefa e `test_preview_editor.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): mapas das montanhas (rota do Olho)`.

---

### Task 3: Gerador, destino e dica em Graciero

**Files:**
- Create: `tools/gerar_elara_montanha.py`
- Modify: `tools/gerar_elara_graciero.py` (nova conversa `elara_graciero_serra` no slot `npc_ms2ef8oi`, o Elfo Suspeito) e `tools/test_elara_graciero_dados.py` (a lista de conversas e o porteiro); reexecutar os dois geradores
- Modify (pelo gerador): `city_scenes.json`, `world_adventures.json`, `dungeons/elara_montanha_*.json`, `monstros_personalizados.json`, `tools/editor_dungeons.js`, `tools/editor_monsters_custom.js`; rodar `python tools/gerar_vocabulario.py` e traduzir os nomes novos
- Test: `tools/test_elara_montanha_dados.py`, `tools/test_elara_montanha_fluxo.py`

**Interfaces:**
- Produces (destino `elara_montanha`, `oculto_ate_liberar`, `ocultar_apos_concluir`, posição acima de Graciero no mapa-múndi, fome/sede 2, etapas `elara_montanha_1` (encadear), `_2` (encadear), `_3`): requisito `fato elara_dica_montanha`, `tambem_fato elara_ramo_a`, `sem_fato elara_leonel_vencido`; renome +2; `outro_rota` com slides condicionais: base (a caravana interceptada, o Olho recuperado, o baú pesado e quente), guia (`fato elara_bardo_ajudou`: o grupo enterra o guia sob uma pilha de pedras), sem guia (`sem_fato elara_bardo_ajudou`: lembram que subiram sozinhos), assassino (`fato elara_assassino_fugiu`: "alguém que sabia o caminho de volta desapareceu pela serra") e a volta a Graciero.
- Produces (conversa em Graciero, slot `npc_ms2ef8oi`): `elara_graciero_serra` — requisito `fato elara_dica_montanha` + `tambem_fato elara_ramo_a` + `sem_fato elara_leonel_vencido`; o elfo diz, a meia-voz, que uma caravana subiu a serra com "uma carga que ninguém queria ver" e que ainda dá tempo; sem efeito de jogo (a rota aparece pelo fato, não pela conversa). Texto sem nomes da rede.
- O gerador segue `aplicar(simular, forcar, caminhos)` de `gerar_elara_graciero.py`, registra as fichas antes de validar os mapas e só toca em ids `elara_montanha*`, nas fichas desta rota e na conversa nova.

- [ ] **Step 1: Write the failing tests.** `test_elara_montanha_dados.py`: destino, etapas, requisito e slides exatos; conversa só em slot ativo, gateada; conversas do autor em Graciero preservadas; fichas e mapas gravados validam; nada da rede por nome. `test_elara_montanha_fluxo.py` (motor real, molde de `test_elara_graciero_fluxo.py`): (a) visibilidade: sem a dica nada; dica sem `elara_ramo_a` nada (ramo B); dica + ramo A aparece; com `elara_leonel_vencido` some; concluída, some; (b) falas: com `elara_bardo_ajudou` as falas do guia são elegíveis (`_fala_elegivel`) e as "sem guia" não; sem ele o contrário; as comuns sempre; (c) objetivos: etapa 1 e 2 gravam os fatos ao pisar na saída; etapa 3: ao derrotar o assassino por arma, fogo e veneno ele foge, grava `elara_assassino_fugiu`, e o objetivo grava `elara_rota_olho_vencida` e `elara_olho_recuperado` e deixa o baú de recompensa com `olho_de_arveluz`; (d) a matriz do final de Graciero: ramo A com o Olho no baú depois da rota mostra "volta ao Templo" no `outro_rota` do Leonel, sem a rota mostra "não está aqui".
- [ ] **Step 2: Run** os dois — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/gerar_elara_montanha.py` (molde: `gerar_elara_graciero.py`; assinaturas em `tools/.elara_montanha_assinaturas.json`) e a conversa em `gerar_elara_graciero.py`.
- [ ] **Step 4: Run** os geradores (`--simular`, depois de verdade e uma terceira vez para provar idempotência) e `git status` (só ids deste plano); rodar `test_elara_montanha_*`, `test_elara_graciero_*`, `test_elara_ponte.py`, `test_elara_gilo_*`, `test_elara_riacho_*`, `test_campanha_elara_parte1.py`, `test_elara_fluxo.py`, `test_tambem_fato.py`, `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_vocabulario.py`, `test_export_catalog.py`, `test_editor_itens.py`, `dividas.py --strict`. Expected: PASS (instáveis conhecidos inalterados; dívidas no baseline).
- [ ] **Step 5: Commit** `feat(elara): rota do Olho nas montanhas`.

---

### Task 4: Documentação e prova final

**Files:**
- Modify: `CLAUDE.md` (seção "O Resgate de Elara — rota do Olho" com a tabela de fatos, as duas vias, as falas com requisito, a recompensa em `reward.items` e os testes)
- Test: suítes das tarefas 1–3 e `tools/dividas.py --strict`

- [ ] **Step 1:** Documentar no `CLAUDE.md`, incluindo que a campanha está completa (planos 1–5) e o que fica para o autor (arte, texto final, calibragem por jogo).
- [ ] **Step 2:** Rodar todas as suítes da campanha (planos 1–5) e `dividas.py --strict`; anotar as falhas que já existiam na base.
- [ ] **Step 3: Prova com o motor real:** percurso do ramo A rápido (Praça viva, dica, rota, Olho, final com "volta ao Templo"), do ramo A lento com bardo que ajuda (dica pelo bardo) e do ramo B (rota invisível).
- [ ] **Step 4: Commit** `docs: rota do Olho da campanha de Elara`.
