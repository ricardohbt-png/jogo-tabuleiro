# O Resgate de Elara — Plano 3: Ramo B (Gilo: Adhadal → Corvin)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o Ramo B da campanha (quem escolheu perseguir o Gilo): a Floresta de Adhadal como travessia difícil e sem descanso, as conversas de chegada em Corvin, a caçada e o combate com o Gilo Dedos Sujos (que o grupo vence, mas que escapa com a ajuda de um bardo da rede) e a pista que leva a Graciero. O plano termina deixando gravados os fatos que Graciero (plano 4) vai ler.

**Architecture:** Mesmo molde dos planos 1 e 2: um gerador idempotente (`tools/gerar_elara_gilo.py`) grava destinos, conversas da taverna de Corvin e os mapas; os mapas de Adhadal são **cópias ajustadas** dos protótipos do autor (`floresta.json`, `floresta_2.json`), para nunca alterar o que ele montou; os de Corvin são novos (construtor `Cena` de `tools/charcos_mapas.py`). O Gilo é uma ficha personalizada nova, derivada do `soldado`. A fuga dele usa a peça `fuga_chefe` do plano 1 (nenhuma peça de motor nova neste plano).

**Tech Stack:** Python (`server.py`, unittest), JSON de dados.

**Spec:** `docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md` (seção "Ramo B")
**Depende de:** planos 1 e 2 já na master (`fuga_chefe`, `relogio`, `heroi_no_grupo`, `efeito.fatos`, fato `elara_ramo_b`, padrão de gerador e de mapas).

## Global Constraints

- Português em todo texto de jogo; conteúdo autoral não leva chave de idioma.
- Nunca citar Ferdinand, Vael'mon nem "rede de bardos" por nome: o bardo que ajuda o Gilo a fugir é só "um bardo", e o grupo percebe que ele não está sozinho.
- Nunca alterar os protótipos do autor (`floresta.json`, `floresta_2.json`, nem o destino "Ad´Hadal"/"Profundezas de Ad´Hadal" de `world_adventures.json`): as etapas de Adhadal da campanha usam **cópias** `elara_adhadal_1.json` e `elara_adhadal_2.json`.
- Mapas `elara_*.json` são do Claude; o gerador recusa sobrescrever um que o autor editou depois (assinatura, como `gerar_elara_riacho.py`) sem `--forcar`.
- A Floresta é a travessia dura: as duas etapas de Adhadal são **emendadas** (nada se recupera entre elas) e usam `marcador_entrada: "poste"`. Nunca a campanha pode ficar sem saída: a segunda etapa de Adhadal não pode ter `saida_permitida: false` sem uma saída autorada (`exit`) alcançável.
- O grupo derrota o Gilo de verdade (XP e objetivo contam) e ele **sempre** escapa; não existe caminho em que ele morra em Corvin.
- Fichas e textos novos não repetem mecânicas já existentes: o Gilo reaproveita ataques e habilidades do catálogo (`soldado`, `goblin_assassino`).
- Nível esperado: Adhadal `expected_party {heroes: 4, level: 3}`; Corvin `{4, 3}`. ND total de cada mapa de Adhadal ≤ 0,9 × poder (poder = 12).

## Fatos (contrato com o plano 4 — nomes estáveis)

| Fato | Quem grava | Significa |
|---|---|---|
| `elara_adhadal_vencida` | objetivo da 2ª etapa de Adhadal | o grupo atravessou a floresta |
| `elara_corvin_chegada` | conversa de chegada em Corvin | o grupo falou com a vila e soube do rastro |
| `elara_cacada_vencida` | objetivo da caçada | o grupo achou o esconderijo do Gilo |
| `elara_gilo_fugiu` | `fuga_chefe` do Gilo | ele foi vencido e fugiu (levando o Olho) |
| `elara_pista_graciero` | objetivo do confronto | a pista aponta para Graciero (o Leonel) |
| `elara_corvin_concluida` | derivado (rota concluída) | usar `aventura_id: elara_corvin` em requisitos de Graciero |

Leitura em Graciero (plano 4): ramo B + `elara_gilo_fugiu` + `elara_pista_graciero` = o Gilo chega a Graciero com o Olho.

## Review Focus

- O grupo que chega a Corvin sem ter falado com ninguém ainda acha o destino da caçada (a conversa de chegada **não** é pré-requisito do destino; só enriquece).
- Adhadal copiado do protótipo: a entrada e a saída existem e são alcançáveis; nenhuma decoração ou monstro nasce em cima da saída.
- O Gilo morto por **qualquer** tipo de dano (arma, magia, armadilha, veneno) ainda foge, e nunca deixa cadáver nem loot (testado também no mapa real, não só na peça de motor).
- Reexecutar o gerador não duplica conversas, não regrava mapa editado e não move destino que o autor reposicionou.
- Nenhum texto menciona a rede, Ferdinand ou Vael'mon; o bardo que ajuda o Gilo aparece só no texto da fuga.
- O destino de Corvin só aparece depois de concluir Adhadal; Adhadal só aparece para quem escolheu o ramo B.

---

### Task 1: Ficha do Gilo Dedos Sujos

**Files:**
- Modify (pelo gerador, Task 3): `monstros_personalizados.json`, `tools/editor_monsters_custom.js`
- Create: `tools/elara_gilo_ficha.py` com `ficha_gilo()` (dict no formato do editor de criaturas)
- Test: `tools/test_elara_gilo_ficha.py`

**Interfaces:**
- Produces: `ficha_gilo() -> dict` com `type: "gilo_dedos_sujos"`, `name: "Gilo Dedos Sujos"`, base copiada de `soldado` (leia a ficha dele em `monstros_personalizados.json`), `cr: 2`, `base_hp` suficiente para uma luta de chefe (≈ 40 PV), CA 14, dois ataques de adaga (`1d6`, +4), um ataque furtivo e uma saída de fumaça já existentes no catálogo de habilidades (`goblin_assassino` serve de modelo), `image: "soldado"` (arte provisória), `ai_type: "agressivo"`. Passa em `S._validate_custom_monster`.

- [ ] **Step 1: Write the failing test** `tools/test_elara_gilo_ficha.py`: `ficha_gilo()` valida (`S._validate_custom_monster` devolve ok), tem `type == "gilo_dedos_sujos"`, `cr == 2`, dois ataques, nenhuma habilidade fora do catálogo; `S.monster_cr` da ficha validada é 2; nenhum texto cita rede/Ferdinand/Vael.
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_gilo_ficha.py` — Expected: FAIL (módulo inexistente).
- [ ] **Step 3: Implement** `ficha_gilo()` a partir de uma cópia profunda da ficha do `soldado`, trocando só o que o plano diz.
- [ ] **Step 4: Run** o teste da tarefa e `test_modo_mestre.py` (fichas personalizadas). Expected: PASS (falhas pré-existentes inalteradas).
- [ ] **Step 5: Commit** `feat(elara): ficha do Gilo Dedos Sujos`.

---

### Task 2: Os mapas do Ramo B

**Files:**
- Create: `tools/elara_gilo_mapas.py` com `masmorra_adhadal_1()`, `masmorra_adhadal_2()`, `masmorra_corvin_cacada()`, `masmorra_corvin_gilo()`
- Create (pelo gerador, Task 3): `dungeons/elara_adhadal_1.json`, `elara_adhadal_2.json`, `elara_corvin_cacada.json`, `elara_corvin_gilo.json`
- Test: `tools/test_elara_gilo_mapas.py`

**Interfaces:**
- Consumes: `ficha_gilo` (Task 1), `Cena`/`obj` de `tools/charcos_mapas.py`, `carregar_dungeon` para ler os protótipos.
- Produces:
  - `masmorra_adhadal_1()` — cópia profunda de `floresta.json` com: `id: "elara_adhadal_1"`, `name: "Floresta de Adhadal — Entrada"`, `marcador_entrada: "poste"`, `expected_party {4, 3}`, 3 armadilhas de caça (urso, rede, buraco) em casas livres do caminho, 2 falas de rastro (pegadas do Gilo, um acampamento abandonado), objetivo principal `reach_exit` mantido.
  - `masmorra_adhadal_2()` — cópia profunda de `floresta_2.json`, **desbastada** (remove monstros em ordem determinística até o ND total ficar ≤ 10,8), com `exit` autorado no canto oposto à entrada (casa de chão alcançável, escolhida por busca em largura), objetivo principal `reach_exit` com `fato: "elara_adhadal_vencida"`, `marcador_entrada: "poste"`, `saida_permitida: false`, `expected_party {4, 3}`, 1 fala (os rastros se separam) e 2 armadilhas de caça.
  - `masmorra_corvin_cacada()` — **Os Arredores de Corvin** (ambiente `ar_livre`, 3 salas: beco, galpão, armazém; ND por sala "Equilibrada/Difícil" para poder 12; capangas do Gilo, armadilhas, baú-chave com o bilhete do esconderijo); objetivo `open_key_chest` com `fato: "elara_cacada_vencida"`.
  - `masmorra_corvin_gilo()` — **O Esconderijo do Gilo** (2 salas: antecâmara com capangas e sala do chefe); o `gilo_dedos_sujos` é `target` com `fuga_chefe {fato: "elara_gilo_fugiu", texto: "Derrotado, o Gilo ri entre os dentes. Uma melodia estridente vem de uma janela, o ar se enche de fumaça e, quando ela baixa, ele sumiu — e um bardo, no telhado, já fugia."}`; objetivo principal `kill_target` com `fato: "elara_pista_graciero"`; um baú com a carta que cita o nome "Graciero" e um vendedor ("o nobre das esposas") **sem** dizer Leonel nem nomes da rede.

- [ ] **Step 1: Write the failing test** `tools/test_elara_gilo_mapas.py`: os quatro validam (`validar_dungeon`); todas as salas dos mapas novos alcançáveis; Adhadal 1 e 2 têm `exit`/`entrance` alcançáveis um do outro (busca em largura), ND total do Adhadal 2 ≤ 10,8 e `saida_permitida False` com `exit` válido; Adhadal 1 e 2 diferem dos protótipos **apenas** nos campos citados (compare o JSON sem esses campos) e o protótipo em disco não mudou (hash do arquivo igual ao do `git`); Corvin-Gilo: o monstro `gilo_dedos_sujos` existe, é `target` e tem `fuga_chefe` com o fato certo; cada mapa novo é determinístico; nenhum texto cita Ferdinand/Vael/rede.
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_gilo_mapas.py` — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/elara_gilo_mapas.py`. Para o desbaste do Adhadal 2, ordene os monstros por (`cr` decrescente, `id` estável) e remova os primeiros até o ND total caber, mantendo ao menos 1 de cada tipo que sobrar.
- [ ] **Step 4: Run** o teste da tarefa, `test_campanha_charcos_mapas.py`, `test_preview_editor.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): mapas de Adhadal e de Corvin (Ramo B)`.

---

### Task 3: Conversas de Corvin, destinos e registro da ficha

**Files:**
- Create: `tools/gerar_elara_gilo.py`
- Modify (pelo gerador): `city_scenes.json` (conversas `elara_*` nos slots **ativos** da taverna de Corvin: `barman`, `patrono_fundo` (Bardo Misterioso), `npc_ms2e74bw` (Garçonete), `npc_ms2e85ew` (Homem sombrio); recuse slot `removed`), `world_adventures.json` (destinos `elara_adhadal`, `elara_corvin`), `monstros_personalizados.json` + `tools/editor_monsters_custom.js` (ficha do Gilo, idempotente), `dungeons/elara_*.json`
- Test: `tools/test_elara_gilo_dados.py`, `tools/test_elara_gilo_fluxo.py`

**Interfaces:**
- Consumes: mapas (Task 2), ficha (Task 1), fato `elara_ramo_b` (plano 1), `efeito.fatos` (plano 2).
- Produces (destinos):
  - `elara_adhadal`: etapas `elara_adhadal_1.json` (`encadear` true) e `elara_adhadal_2.json`; requisito `fato: elara_ramo_b`; fome/sede 2; oculto até liberar; `ocultar_apos_concluir`; `renome_recompensa` 1; posição no mapa-múndi entre Alva e Luz e Corvin.
  - `elara_corvin`: etapas `elara_corvin_cacada.json` (`encadear` true) e `elara_corvin_gilo.json`; requisito `aventura_id: elara_adhadal`; fome/sede 1; oculto até liberar; `ocultar_apos_concluir`; `renome_recompensa` 2; posição perto de `vila_corvin`.
- Produces (conversas de Corvin, todas com requisito `fato: elara_ramo_b`; texto autoral):
  - `elara_corvin_barman` (o Gilo passou por aqui, pagou caro e saiu à noite; grava `elara_corvin_chegada`), `elara_corvin_garconete` (viu um homem de dedos sujos de tinta e de lama), `elara_corvin_bardo` (o "Bardo Misterioso": evasivo, toca uma melodia estridente, diz que não viu ninguém; não grava fato), `elara_corvin_sombrio` (o "Homem sombrio": avisa que quem procura o Gilo "chega tarde ou não chega").
- O gerador é idempotente, só toca em ids `elara_*` e na ficha `gilo_dedos_sujos`, preserva a posição que o autor deu aos destinos, e registra a ficha pela mesma validação do editor (`S._validate_custom_monster`).

- [ ] **Step 1: Write the failing tests.** `test_elara_gilo_dados.py`: destinos e conversas existem; requisitos certos (Adhadal só com `elara_ramo_b`; Corvin só com `aventura_id: elara_adhadal`); cada conversa só com o ramo B e só em slot ativo; nada cita Ferdinand/Vael/rede; `elara_adhadal_1` emenda com a 2ª etapa; ficha gravada em `monstros_personalizados.json` e espelhada em `editor_monsters_custom.js`; conversas do autor em Corvin preservadas. `test_elara_gilo_fluxo.py` (motor real, molde de `test_elara_riacho_fluxo.py`): sem o ramo B nada aparece; com ele aparecem as conversas e o destino Adhadal (não o de Corvin); com Adhadal concluído (`world_adventure_progress`) o destino de Corvin aparece e o de Adhadal some; vencer a 2ª etapa de Adhadal e a caçada grava os fatos pelos objetivos (carregando os mapas reais, como a prova do plano 2); o Gilo derrotado por dano de arma, de fogo (`_aplicar_dano_alvo`) e de veneno (`_dano_em_alvo`) foge, grava `elara_gilo_fugiu` e não deixa cadáver nem baú de loot novo; o objetivo `kill_target` do confronto conta como cumprido e grava `elara_pista_graciero`.
- [ ] **Step 2: Run** os dois — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/gerar_elara_gilo.py` no molde de `gerar_elara_riacho.py` (`--simular`, `--forcar`, assinaturas em `tools/.elara_gilo_assinaturas.json`; registra a ficha antes de validar os mapas, porque o Gilo precisa existir em `S.MONSTER_DEFS`).
- [ ] **Step 4: Run** o gerador (`--simular`, depois de verdade, e uma terceira vez para provar a idempotência); confira `git status` (só `elara_*`, `city_scenes.json`, `world_adventures.json`, `monstros_personalizados.json`, `tools/editor_monsters_custom.js`, `tools/editor_dungeons.js`, assinaturas).
- [ ] **Step 5: Run** `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_campanha_elara_parte1.py`, `test_elara_fluxo.py`, `test_elara_riacho_fluxo.py`, `test_fuga_chefe.py`, `test_masmorra_sequenciada.py`, `test_editor_monsters*.py`, `test_vocabulario.py`, `test_export_catalog.py`. Expected: PASS (instáveis conhecidos inalterados).
- [ ] **Step 6: Commit** `feat(elara): Ramo B (Adhadal e Corvin): destinos, conversas e Gilo`.

---

### Task 4: Documentação e prova final

**Files:**
- Modify: `CLAUDE.md` (seção "O Resgate de Elara — Ramo B (Gilo)" com a tabela de fatos, os destinos, a ficha do Gilo e os testes)
- Test: suítes das tarefas 1–3 e `tools/dividas.py --strict`

- [ ] **Step 1:** Documentar em `CLAUDE.md` os destinos, os mapas (incluindo que Adhadal usa cópias dos protótipos), a ficha do Gilo e a tabela de fatos com a regra de leitura em Graciero.
- [ ] **Step 2:** Rodar todas as suítes das tarefas e `dividas.py --strict`; anotar quais falhas já existiam na base.
- [ ] **Step 3: Prova com o motor real:** sala com o ramo B escolhido: conversas de Corvin, vencer Adhadal 2 (fato), vencer a caçada (fato) e o confronto (Gilo fugiu + pista); repetir derrotando o Gilo por dano de arma, magia e veneno.
- [ ] **Step 4: Commit** `docs: Ramo B (Gilo) da campanha de Elara`.
