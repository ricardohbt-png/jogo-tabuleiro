# O Resgate de Elara — Plano 4: Graciero (o desfecho comum aos dois ramos)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar Graciero: a ponte que leva os dois ramos até lá, os rumores e as duas pistas, a morte do Gilo pelos escorpiões (vista ou só o corpo, conforme o relógio), o esconderijo do Leonel com a Elara e o final em slides que reage a tudo o que o grupo fez. O plano deixa gravados os fatos que a rota opcional do Olho (plano 5) vai ler.

**Architecture:** Mesmo molde dos planos 2 e 3 (gerador idempotente `tools/gerar_elara_graciero.py`, mapas determinísticos pelo construtor `Cena`, fichas pelo caminho do editor). Duas peças pequenas de motor, calcadas em precedentes já feitos: requisito `tambem_fato` (segundo fato exigido, como `heroi_no_grupo`) e `fatos` no objetivo (como `efeito.fatos` da conversa). Nenhuma outra peça de motor.

**Tech Stack:** Python (`server.py`, unittest), JS do editor (testes node), JSON de dados.

**Spec:** `docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md` (seção "Graciero" e tabela de resultados)
**Depende de:** planos 1–3 na master (`relogio`, `heroi_no_grupo`, `fuga_chefe`, `efeito.fatos`, destinos encadeados, fatos do Riacho e de Corvin).
**Fora deste plano:** a rota opcional do Olho nas montanhas (plano 5). Este plano só grava os fatos de entrada dela.

## Global Constraints

- Português em todo texto de jogo; conteúdo autoral não leva chave de idioma.
- Nunca citar Ferdinand, Vael'mon, "rede de bardos" nem Porto Saledo como origem de ordens: o grupo só sente "algo maior". Pode-se dizer "o Olho segue para o norte, para as montanhas".
- A Elara é sempre salva: nenhum caminho (nem relógio lento, nem bardo traidor) a deixa de fora. Ela não é unidade que possa morrer: a cela dela é um baú-chave.
- Nenhum caminho termina a campanha ou deixa o grupo sem avanço: o relógio lento só tira a cena da morte e a dica; o bardo traidor só deixa o Leonel alerta.
- Os mapas `elara_graciero_*`/`elara_leonel_*` são do Claude; o gerador recusa sobrescrever um que o autor editou depois (assinatura) sem `--forcar`. As conversas do autor em Graciero (`barman`: `inicial`, `fala_mulr73l3`, `fala_mulrbvne`; Elfo Suspeito: `inicial` e seis `fala_*`) ficam intactas.
- Só slots ativos recebem conversa: `barman`, `npc_ms2ee41a` (garçonete), `npc_ms2ef8oi` (Elfo Suspeito), `npc_ms2egify` (Homem nobre), `npc_ms2ej3o7` (Gnomo). Slot `removed` é recusado.
- Nível esperado de Graciero: `expected_party {heroes: 4, level: 4}`; esconderijo `{4, 5}`. ND por sala ≤ 0,8 × poder (Equilibrada ou menos), chefe incluído.
- Relógio de Graciero: id `elara_graciero`, limite 30 rodadas, `fato_ao_passar: elara_graciero_lento`, só nos mapas da Frente 1 e da Frente 2.

## Fatos (contrato com o plano 5 — nomes estáveis)

| Fato | Quem grava | Significa |
|---|---|---|
| `elara_rumo_graciero` | conversa-ponte (Riacho após `elara_mocas_salvas`; Corvin após `elara_pista_graciero`) | o grupo decidiu seguir para Graciero |
| `elara_beco_vencido` / `elara_cais_vencido` | objetivos das duas frentes | pistas achadas |
| `elara_graciero_lento` | relógio | passaram do limite nas duas frentes |
| `elara_gilo_morreu` | objetivo da Praça (as duas versões) | o Gilo morreu pelos escorpiões |
| `elara_viu_gilo_morrer` | `fatos` do objetivo da Praça viva | o grupo viu (e ouviu) |
| `elara_dica_montanha` | `fatos` da Praça viva **ou** conversa do bardo poupado e bem tratado | a caravana sobe as montanhas (abre a rota do plano 5, só ramo A) |
| `elara_bardo_ajudou` / `elara_bardo_traiu` | conversas do bardo poupado, por tratamento | ajudou ou traiu |
| `elara_leonel_cauteloso` | já existe (bardo morto); passa a vir também da traição | o Leonel está alerta |
| `elara_olho_recuperado` | conversa dos pertences do Gilo (ramo B) | o Olho está com o grupo (também o item `olho_de_arveluz`) |
| `elara_elara_salva` | baú-chave da cela | a Elara foi encontrada |

Leitura no plano 5: rota do Olho abre com `elara_dica_montanha` e `elara_ramo_a`.

## Review Focus

- Os dois ramos chegam a Graciero e a nenhum outro lugar: sem `elara_rumo_graciero` nada de Graciero aparece, e o destino da Frente 1 aparece sozinho depois.
- Relógio: grupo rápido vê a Praça viva; grupo lento vê só a Praça morta; nunca as duas, nunca nenhuma.
- Ramo B recebe o Olho mesmo com relógio lento; ramo A nunca recebe o Olho aqui.
- O bardo poupado só ajuda quando foi tratado bem e só trai quando foi maltratado; sem ter sido poupado, não aparece.
- Bardo morto ou traidor: o esconderijo é a variante alerta; senão, a normal. Nunca as duas visíveis.
- Final: toda combinação de ramo × Olho × bardo × Pedro/Henrique produz slides coerentes, sem texto contraditório (ex.: "o Olho voltou" e "o Olho segue para o norte" juntos).
- Reexecutar o gerador não duplica conversas, não regrava mapa editado e preserva a posição que o autor deu aos destinos.

---

### Task 1: Peças de motor — requisito `tambem_fato` e objetivo `fatos`

**Files:**
- Modify: `server.py` (`_clean_requirement`, `_avaliar_requisito`, `_aplicar_renome_fato`, `validar_dungeon` nos campos de objetivo, `load_authored_dungeon` se copiar campos de objetivo), `tools/editor_world.js`, `tools/editor_city.js`, `tools/editor_story.js`, `tools/editor.js` (preservar os campos como `heroi_no_grupo` e `fato` fazem hoje)
- Test: `tools/test_tambem_fato.py`, `tools/test_tambem_fato_editor.js`

**Interfaces:**
- Produces: `_clean_requirement` aceita `tambem_fato` (texto até 100) e só inclui a chave quando preenchido (requisitos gravados ficam idênticos byte a byte); `_avaliar_requisito` exige o fato **além** de `fato`/`sem_fato`. Objetivo (primário ou secundário) aceita `fatos: [str]` (até 6, cada até 100), gravados junto de `fato` por `_aplicar_renome_fato`; `validar_dungeon` rejeita `fatos` que não seja lista de textos válidos.
- Modelo a copiar: o commit `7c0e41f9` (heroi_no_grupo em conversas, destinos, slides e falas) para o requisito, e `efeito.fatos` da conversa (plano 2) para o objetivo.

- [ ] **Step 1: Write the failing tests.** `test_tambem_fato.py`: requisito com `fato` e `tambem_fato` só passa com os dois; só um dos dois não passa; sem o campo, o resultado de `_clean_requirement` é o de antes (compare com um requisito antigo); `tambem_fato` vale em conversa, destino (`_aventura_visivel`) e slide (`_story_beat`); objetivo `kill_target` com `fato: "a"` e `fatos: ["b","c"]` grava os três ao ser cumprido (via `_check_objectives`); `fatos` inválido (não lista, item vazio, mais de 6, texto de 101 caracteres) recusado por `validar_dungeon`. `test_tambem_fato_editor.js`: as três abas e o editor de masmorras preservam `tambem_fato` e `fatos` no ida-e-volta (molde: `test_requisito_heroi_editor.js`).
- [ ] **Step 2: Run** `python -X utf8 tools/test_tambem_fato.py` e `node tools/test_tambem_fato_editor.js` — Expected: FAIL.
- [ ] **Step 3: Implement** nos pontos listados, no mesmo estilo dos precedentes (chave só quando preenchida; mensagens de erro com chave `erro.*` em `src/lang/erros.js`, pt e en, se o validador usar `T`).
- [ ] **Step 4: Run** os dois testes e `test_requisito_heroi.py`, `test_requisito_sem_fato.py`, `test_objetivo_renome.py`, `test_editor_objetivo.js`, `test_conversa_fatos.py`, `test_erros.py`, `test_idioma.py`. Expected: PASS (falhas pré-existentes inalteradas).
- [ ] **Step 5: Commit** `feat(requisito): tambem_fato e fatos no objetivo`.

---

### Task 2: Fichas, item e hostilidade

**Files:**
- Create: `tools/elara_graciero_fichas.py` com `ficha_gilo_fugitivo()`, `ficha_escorpiao_gigante()`, `ficha_leonel()`, `item_olho()`, `hostilidade()`
- Modify (pelo gerador, Task 5): `monstros_personalizados.json` + `tools/editor_monsters_custom.js`, `itens_personalizados.json` + `tools/editor_items_custom.js`, `monster_hostility.json`
- Test: `tools/test_elara_graciero_fichas.py`

**Interfaces:**
- Produces:
  - `gilo_fugitivo`: derivada de `elara_gilo_ficha.ficha_gilo()`, `cr 0.25`, 4 PV, sem ataques, movimento 0 (o Gilo ferido da Praça viva).
  - `escorpiao_gigante`: derivada de `escorpiao_de_pedra_customizado`, `cr 1`, porte pequeno ou médio, ataque forte o bastante para matar o `gilo_fugitivo` em um golpe; arte reaproveitada.
  - `leonel`: derivada do `soldado` (como o Gilo), `cr 3`, ~55 PV, CA 15, `boss`, dois ataques; texto sem nomes da rede.
  - `item_olho()`: item `olho_de_arveluz` (👁️, "Olho de Arveluz"), tipo aceito pelo Editor de Itens que não dê bônus, fora de loja/baús/loot, preço 0; descrição que **não** diz o que ele é ("Uma relíquia pesada do Templo de Alva e Luz. Está quente ao toque.").
  - `hostilidade()`: `escorpiao_gigante` hostil ao tipo `gilo_fugitivo` (formato de `monster_hostility.json`).
- Todas passam em `S._validate_custom_monster`/`S._validate_custom_item`; a hostilidade passa em `S._validate_monster_hostility`.

- [ ] **Step 1: Write the failing test** `test_elara_graciero_fichas.py`: cada ficha valida; `monster_cr` de cada uma (0,25 / 1 / 3); `gilo_fugitivo` sem ataques e movimento 0; o dano mínimo do escorpião mata o `gilo_fugitivo`; o item valida e não aparece em nenhuma lista de loja nem de loot; a hostilidade valida; nenhum texto cita Ferdinand/Vael/rede/Porto Saledo.
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_graciero_fichas.py` — Expected: FAIL.
- [ ] **Step 3: Implement** o módulo copiando fichas por `copy.deepcopy` e trocando só o necessário (molde: `tools/elara_gilo_ficha.py`).
- [ ] **Step 4: Run** o teste da tarefa e `test_editor_itens.py`, `test_monster_hostility.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): fichas, Olho de Arveluz e hostilidade de Graciero`.

---

### Task 3: Os mapas de Graciero

**Files:**
- Create: `tools/elara_graciero_mapas.py` com `masmorra_beco()`, `masmorra_cais()`, `masmorra_praca_viva()`, `masmorra_praca_morta()`, `masmorra_leonel_1()`, `masmorra_leonel_1_alerta()`, `masmorra_leonel_2()`
- Create (pelo gerador, Task 5): `dungeons/elara_graciero_beco.json`, `elara_graciero_cais.json`, `elara_graciero_praca_viva.json`, `elara_graciero_praca_morta.json`, `elara_leonel_1.json`, `elara_leonel_1_alerta.json`, `elara_leonel_2.json`
- Test: `tools/test_elara_graciero_mapas.py`

**Interfaces:**
- Consumes: `Cena`/`montar_fila`/`obj` de `tools/charcos_mapas.py`, `fala` de `gerar_campanha_sombras`, fichas da Task 2, constantes de monstros de `elara_gilo_mapas.py` (`SOLDADO`, `ORC`, `DUAL`, `ARQUEIRO`).
- Produces (todos com `expected_party` conforme as Global Constraints, ambiente de cidade/`ar_livre`, sem poste):
  - **Beco** e **Cais** (Frentes 1 e 2): 3 salas cada, `relogio` de Graciero (avisos em 12, 22 e 30 com texto de urgência sem nomes), armadilhas de cidade (rede, dardos), objetivo `open_key_chest` com baú-chave e carta; fatos `elara_beco_vencido` / `elara_cais_vencido`. As cartas apontam para o "nobre das esposas" e para uma casa de leilões, **sem** dizer o nome do Leonel antes da Frente 2; a do Cais cita "Leonel".
  - **Praça viva**: 1 sala ampla; `gilo_fugitivo` a 1 casa de 2 `escorpiao_gigante`, grupo a ≥ 6 casas; fala na entrada com as últimas palavras do Gilo (menciona que a pedra foi entregue "aos que sobem a montanha" e que "o outro nobre paga"); objetivo `kill_all` primário com `fato: elara_gilo_morreu` e `fatos: [elara_viu_gilo_morrer, elara_dica_montanha]`.
  - **Praça morta**: mesma planta e escorpiões, sem Gilo vivo; decoração de corpo (`monte_ossos`) onde ele cairia e fala curta ("o que sobrou do mercenário"); objetivo `kill_all` com `fato: elara_gilo_morreu`, sem `fatos`.
  - **Esconderijo do Leonel**: `masmorra_leonel_1` (A Casa de Leilões: 3 salas, guardas, armadilhas, chave da cela) e `masmorra_leonel_1_alerta` (a mesma planta e sementes, com 2 guardas a mais e uma armadilha extra, ND ainda ≤ 0,8×poder); `masmorra_leonel_2` (Os Porões): sala das outras moças + sala do `leonel` (alvo, `boss`), baú-chave da cela da Elara com `fato: elara_elara_salva` como objetivo secundário e `kill_target` do Leonel como primário.

- [ ] **Step 1: Write the failing test** `test_elara_graciero_mapas.py`: os sete validam e são determinísticos; todas as salas alcançáveis (`salas_alcancaveis`); Beco/Cais têm o `relogio` com o id e o fato certos e o objetivo com o fato certo; Praça viva tem exatamente 1 `gilo_fugitivo` e 2 escorpiões, o Gilo a 1 casa de um escorpião e ≥ 6 de qualquer entrada, objetivo com `fatos` exatos; Praça morta não tem `gilo_fugitivo`; alerta tem mais guardas que a normal e as demais características iguais (compare sem monstros/armadilhas); ND por sala ≤ 0,8×poder; Leonel é `target`; nenhum texto cita Ferdinand/Vael/rede/Porto Saledo; as cartas do Beco não citam "Leonel".
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_graciero_mapas.py` — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/elara_graciero_mapas.py` (molde: `elara_gilo_mapas.py`), com sementes fixas próprias (4101–4107).
- [ ] **Step 4: Run** o teste da tarefa, `test_campanha_charcos_mapas.py`, `test_preview_editor.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): mapas de Graciero e do esconderijo do Leonel`.

---

### Task 4: A ponte — conversas que levam os dois ramos a Graciero

**Files:**
- Modify: `tools/gerar_elara_riacho.py` (`conversas()`: nova conversa no slot `barman`), `tools/gerar_elara_gilo.py` (`conversas()`: nova conversa no slot `barman`); reexecutar os dois geradores
- Modify: `tools/test_elara_riacho_dados.py` (a regra "só aparece com o ramo A" aceita o fato `elara_mocas_salvas`), `tools/test_elara_gilo_dados.py`
- Test: `tools/test_elara_ponte.py`

**Interfaces:**
- Produces: `elara_riacho_rumo_graciero` (slot `barman` do Riacho): `requisito {fato: elara_mocas_salvas}`, `efeito.fato: elara_rumo_graciero`, uma vez; `elara_corvin_rumo_graciero` (slot `barman` de Corvin): `requisito {fato: elara_pista_graciero}`, mesmo efeito. Textos: o grupo decide partir para Graciero atrás da irmã do mago (Riacho) / do Gilo (Corvin).

- [ ] **Step 1: Write the failing test** `test_elara_ponte.py` (motor real, molde de `test_elara_riacho_fluxo.py`): sem o fato do ramo a conversa não aparece; com `elara_mocas_salvas` aparece no Riacho e grava `elara_rumo_graciero`; com `elara_pista_graciero` aparece em Corvin e grava o mesmo; uma vez só; as conversas do autor e as dos planos 2 e 3 seguem presentes.
- [ ] **Step 2: Run** `python -X utf8 tools/test_elara_ponte.py` — Expected: FAIL.
- [ ] **Step 3: Implement** a conversa em cada `conversas()`, ajustar os dois testes de dados que enumeram as conversas e rodar os dois geradores (`--simular` e depois de verdade).
- [ ] **Step 4: Run** `test_elara_ponte.py`, `test_elara_riacho_dados.py`, `test_elara_riacho_fluxo.py`, `test_elara_gilo_dados.py`, `test_elara_gilo_fluxo.py`, `test_cenas_conversa.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(elara): conversas-ponte do Riacho e de Corvin para Graciero`.

---

### Task 5: Gerador de Graciero — conversas, destinos e final

**Files:**
- Create: `tools/gerar_elara_graciero.py`
- Modify (pelo gerador): `city_scenes.json` (conversas `elara_*` nos slots ativos de Graciero), `world_adventures.json`, `dungeons/elara_graciero_*.json`, `dungeons/elara_leonel_*.json`, `monstros_personalizados.json`, `itens_personalizados.json`, `monster_hostility.json`, `tools/editor_dungeons.js`, `tools/editor_monsters_custom.js`, `tools/editor_items_custom.js`
- Test: `tools/test_elara_graciero_dados.py`, `tools/test_elara_graciero_fluxo.py`

**Interfaces:**
- Consumes: mapas (Task 3), fichas/item/hostilidade (Task 2), `tambem_fato` e `fatos` (Task 1), fatos dos planos 1–3.
- Produces (destinos, todos `oculto_ate_liberar` e `ocultar_apos_concluir`, posições perto de `graciero` no mapa-múndi):
  - `elara_graciero_beco` (Frente 1): requisito `fato elara_rumo_graciero`; fome/sede 1.
  - `elara_graciero_cais` (Frente 2): requisito `aventura_id elara_graciero_beco`.
  - `elara_graciero_praca_viva`: `aventura_id elara_graciero_cais` + `sem_fato elara_graciero_lento`. `elara_graciero_praca_morta`: `aventura_id elara_graciero_cais` + `fato elara_graciero_lento`.
  - `elara_leonel_casa` (etapas `elara_leonel_1` encadeada → `elara_leonel_2`): `fato elara_gilo_morreu` + `sem_fato elara_leonel_cauteloso`. `elara_leonel_casa_alerta` (etapas `elara_leonel_1_alerta` encadeada → `elara_leonel_2`): `fato elara_gilo_morreu` + `tambem_fato elara_leonel_cauteloso`. Os dois com o mesmo `outro_rota` (slides finais).
- Produces (conversas em Graciero, texto autoral, todas com `fato elara_rumo_graciero`, salvo onde dito):
  - rumores: `elara_graciero_garconete`, `elara_graciero_nobre` ("um senhor respeitável que compra esposas" — sem nome), `elara_graciero_gnomo`, `elara_graciero_elfo` (o Elfo Suspeito, que já tem conversas do autor: a nova convive com elas);
  - bardo poupado: `elara_graciero_bardo_ajuda` (`fato elara_bardo_poupado`, `tambem_fato elara_bardo_gentil`; grava `elara_bardo_ajudou` e `elara_dica_montanha`) e `elara_graciero_bardo_traicao` (`fato elara_bardo_poupado`, `tambem_fato elara_bardo_maltratado`; grava `elara_bardo_traiu` e `elara_leonel_cauteloso`);
  - heróis: `elara_graciero_pedro` (`heroi_no_grupo mage`) e `elara_graciero_henrique` (`heroi_no_grupo bard`), falas extras sobre a irmã / a zombaria (gravam fato próprio, sem efeito de jogo);
  - Olho: `elara_gilo_pertences` (`fato elara_gilo_morreu`, `sem_fato elara_ramo_a`; `efeito.item_id olho_de_arveluz`, grava `elara_olho_recuperado`): a guarda da cidade entrega ao grupo os pertences do Gilo.
- Produces (`outro_rota` dos dois destinos do Leonel): slides com `requisito`/`negar` — base (Elara salva, Leonel vencido); Pedro (`heroi_no_grupo mage`); Henrique (`heroi_no_grupo bard`); moças do Riacho salvas (`fato elara_mocas_salvas`) / moças dos porões (`fato elara_ramo_b`); Olho de volta (`item_id olho_de_arveluz`) / Olho segue para o norte (mesmo requisito com `negar`); bardo ajudou / traiu; fecho de mistério sempre ("alguma coisa maior continua se movendo, irritada, longe daqui").
- O gerador é idempotente, só toca em ids `elara_*`/`gilo_fugitivo`/`escorpiao_gigante`/`leonel`/`olho_de_arveluz`, preserva a posição que o autor deu aos destinos, registra fichas e item pelos caminhos do editor e segue o padrão `aplicar(simular, forcar, caminhos)` de `gerar_elara_gilo.py`.

- [ ] **Step 1: Write the failing tests.** `test_elara_graciero_dados.py`: destinos, requisitos e etapas exatos; conversas só em slots ativos e todas gateadas; nenhum nome da rede nos textos; conversas do autor preservadas; slides com requisitos válidos (`S._clean_requirement`); fichas, item e hostilidade gravados; mapas gravados validam. `test_elara_graciero_fluxo.py` (motor real, `masmorra()` como em `test_elara_gilo_fluxo.py`): (a) sem `elara_rumo_graciero` nada aparece; com ele, só o Beco; concluir Beco libera o Cais, concluir o Cais libera **uma** Praça (viva se o relógio não passou, morta se `elara_graciero_lento`); (b) objetivo da Praça viva grava `gilo_morreu`, `viu_gilo_morrer` e `dica_montanha`, a morta só `gilo_morreu`; (c) Praça viva: após uma fase de monstros o `gilo_fugitivo` está morto e o grupo ileso (rodar a IA real); (d) bardo: poupado+gentil → só a conversa de ajuda e `dica_montanha`; poupado+maltratado → só a de traição e `leonel_cauteloso`; sem `bardo_poupado` nenhuma; (e) Olho: ramo B com `gilo_morreu` recebe o item, ramo A não; (f) esconderijo normal sem `cauteloso`, alerta com ele, nunca os dois; (g) a matriz do final: para ramo A/B × Olho × bardo × Pedro/Henrique, monta o beat `fim:` e confere que slides contraditórios nunca coexistem e que o fecho de mistério sempre sai.
- [ ] **Step 2: Run** os dois — Expected: FAIL.
- [ ] **Step 3: Implement** `tools/gerar_elara_graciero.py` (molde: `gerar_elara_gilo.py`; assinaturas em `tools/.elara_graciero_assinaturas.json`; `garantir_fichas` registra Gilo fugitivo, escorpião, Leonel e o Olho antes de validar os mapas). Se o teste (c) mostrar que a IA ataca o grupo e não o Gilo, aproxime os escorpiões do Gilo e afaste o grupo (ajuste de mapa), sem mudar o motor; ledgerar como ruling.
- [ ] **Step 4: Run** o gerador (`--simular`, depois de verdade e uma terceira vez para provar idempotência); confira `git status` (só ids deste plano); rodar `test_elara_graciero_dados.py`, `test_elara_graciero_fluxo.py`, `test_elara_ponte.py`, `test_elara_gilo_*`, `test_elara_riacho_*`, `test_campanha_elara_parte1.py`, `test_elara_fluxo.py`, `test_final_condicional.py`, `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_masmorra_sequenciada.py`, `test_vocabulario.py`, `test_export_catalog.py`, `test_editor_itens.py`; rodar `python tools/gerar_vocabulario.py` e traduzir os nomes novos; `python tools/dividas.py --strict`. Expected: PASS (instáveis conhecidos inalterados; dívidas no baseline).
- [ ] **Step 5: Commit** `feat(elara): Graciero: pistas, morte do Gilo, esconderijo do Leonel e final`.

---

### Task 6: Documentação e prova final

**Files:**
- Modify: `CLAUDE.md` (seção "O Resgate de Elara — Graciero" com a tabela de fatos, a ponte, o relógio, as duas Praças, as variantes do esconderijo, o Olho e os testes)
- Test: suítes das tarefas 1–5 e `tools/dividas.py --strict`

- [ ] **Step 1:** Documentar em `CLAUDE.md` o que o plano entrega e o que fica para o plano 5 (fatos de entrada da rota do Olho).
- [ ] **Step 2:** Rodar todas as suítes das tarefas e `dividas.py --strict`; anotar as falhas que já existiam na base.
- [ ] **Step 3: Prova com o motor real** (sem navegador): percurso completo do ramo A rápido e lento e do ramo B, do `elara_rumo_graciero` ao beat final, conferindo fatos, item e slides em cada caso.
- [ ] **Step 4: Commit** `docs: Graciero da campanha de Elara`.
