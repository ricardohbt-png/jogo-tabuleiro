# O Resgate de Elara — Plano 1: peças do motor + Parte 1 (Alva e Luz)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar as três peças novas de motor que a campanha exige (requisito por herói no grupo, relógio de rodadas entre masmorras, fuga do chefe) e a **Parte 1** da campanha jogável de ponta a ponta: cena do Templo, casa do bardo, fazenda, volta ao Templo e a escolha entre os ramos.

**Architecture:** Cada peça de motor entra pelo caminho que o jogo já usa para algo parecido: o requisito novo é mais um campo de `_clean_requirement`/`_avaliar_requisito` (como `sem_fato`); o relógio é um contador no jogo salvo avançado por `_virada_de_rodada` que grava fatos; a fuga do chefe é um desvio dentro de `_monster_dies_impl` (como o Troll que regenera). A campanha em si é gerada por um script idempotente, `tools/gerar_campanha_elara.py`, no molde de `gerar_campanha_charcos.py`, que só toca em ids `elara_*`.

**Tech Stack:** Python (`server.py`, unittest), JS vanilla (editores em `tools/`, testes em node), arquivos JSON de dados.

**Spec:** `docs/superpowers/specs/2026-10-21-campanha-resgate-de-elara-design.md`

**Escopo (importante):** este plano cobre só motor + Parte 1. O Ramo A (Riacho), o Ramo B (Adhadal/Corvin), Graciero e a rota das montanhas ganham planos próprios depois que a Parte 1 estiver jogável.

## Global Constraints

- Português em todo texto de jogo; conteúdo autoral não tem chave de idioma (como a Maré do Charco). Textos novos de **motor** (motivos de recusa) usam `T("erro...")` com chaves em `src/lang/erros.js` (pt e en).
- `server.py`, `game.js`, `CLAUDE.md` e os `.js` de `tools/` estão em **CRLF**: edite por ferramenta de edição ou script que preserve CRLF.
- Nome do demônio: sempre **Vael'mon**. Nunca citar Ferdinand nem Vael'mon em texto que o jogador veja.
- Nunca sobrescrever os mapas do autor. Os arquivos `dungeons/*.json` são editados por ele no editor; o gerador só grava mapa novo se `--forcar`, e a rotina de assinatura do `gerar_campanha_sombras.py` (`assinatura`, `Conflito`) vale aqui.
- Heróis são identidades fixas por classe: **Pedro = `mage`**, **Henrique = `bard`**.
- A Elara é **sempre** salva; o relógio **nunca** bloqueia a campanha.
- Cada tarefa roda a suíte que toca (lista no fim da tarefa) e confere que as falhas conhecidas da base não aumentaram.

## Review Focus

- Salvar e carregar no meio da Parte 1 (casa → fazenda) preserva o contador do relógio e os fatos; um ponto de salvamento antigo sem o campo `relogios` carrega sem erro.
- Grupo **sem** Pedro e **sem** Henrique vê a campanha completa e coerente, sem opção nem fala "órfã".
- `_clean_requirement` ganha um campo: conversas e destinos **antigos** (sem o campo) continuam passando exatamente como antes, e os testes que comparam o dicionário do requisito inteiro não quebram.
- Chefe com `fuga_chefe` morto por **qualquer** caminho de dano (arma, magia, armadilha, veneno, arremesso) foge do mesmo jeito; chefe sem o campo morre como sempre.
- Relógio em masmorra sem o campo `relogio` não faz nada; uma masmorra com relógio visitada duas vezes não zera nem dobra o contador.
- O editor de masmorras, ao abrir e salvar a casa e a fazenda, **não perde** `relogio`, `fuga_chefe`, `relogio_desconto` nem o `requisito` das falas.

---

### Task 1: Requisito "herói no grupo"

**Files:**
- Modify: `server.py` (`_clean_requirement` ~656; `_avaliar_requisito` ~17632; `_fala_elegivel` ~20992; `validar_dungeon` bloco das falas ~8472/8573)
- Modify: `src/lang/erros.js` (chave `erro.requisito.heroi_no_grupo`, pt e en)
- Modify: `tools/editor_world.js`, `tools/editor_story.js`, `tools/editor_city.js` (campo "Herói no grupo", ao lado de "Sem o fato"), `tools/editor.js` (painel da fala: preservar e editar `requisito`)
- Test: `tools/test_requisito_heroi.py`, `tools/test_requisito_heroi_editor.js`

**Interfaces:**
- Produces: campo `heroi_no_grupo: str` no requisito (`""` = sem exigência; senão um id de `CLASSES`); `_avaliar_requisito` o cobra; falas de masmorra aceitam `requisito` (mesmo formato) e `_fala_elegivel` o consulta para falas comuns.

- [ ] **Step 1: Write the failing test** `tools/test_requisito_heroi.py`:
  - `test_clean_requirement_conserva_heroi`: `S._clean_requirement({"heroi_no_grupo":" mage "})["heroi_no_grupo"] == "mage"`; sem o campo = `""`; id que não está em `CLASSES` vira `""`.
  - `test_avalia_com_e_sem_o_heroi`: sala com `players` contendo um `class_id:"mage"` → `_avaliar_requisito({"heroi_no_grupo":"mage"})[0]` é True; sem mago, False com 1 motivo; o mestre (`is_master`) não conta como herói.
  - `test_requisitos_antigos_inalterados`: `_avaliar_requisito({})` e `_avaliar_requisito({"fato":"x"})` dão o mesmo resultado de antes.
  - `test_fala_de_masmorra_respeita_requisito`: uma fala `{"id":"f","trigger":{...},"requisito":{"heroi_no_grupo":"bard"}}` só é elegível quando há bardo no grupo.
- [ ] **Step 2: Run** `python -X utf8 tools/test_requisito_heroi.py` — Expected: FAIL (campo inexistente).
- [ ] **Step 3: Implement** em `server.py`: `_clean_requirement` devolve também `"heroi_no_grupo"` (validado contra `CLASSES`); `_avaliar_requisito` soma `T("erro.requisito.heroi_no_grupo", heroi=<nome da classe>)` quando falta; `_fala_elegivel` passa a exigir `self._avaliar_requisito(fala.get("requisito"))[0]` só para fala comum (lição fica como está). Ajuste o validador das falas para aceitar `requisito` e limpá-lo com `_clean_requirement`.
- [ ] **Step 4: Editores** — nos três editores de requisito, adicione um `<select>` "Herói no grupo" (vazio + as 6 classes) que lê e grava `heroi_no_grupo`; no `editor.js`, o painel da fala preserva `requisito` no `loadJSON`/`buildJSON` (hoje a fala é copiada campo a campo). `test_requisito_heroi_editor.js`: roundtrip estático que a fala com `requisito` sai igual ao entrar.
- [ ] **Step 5: Run** `python -X utf8 tools/test_requisito_heroi.py`, `node tools/test_requisito_heroi_editor.js`, e as suítes `test_requisito_sem_fato.py`, `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_editor_story_condicao.js`, `test_modo_mestre.py` (seção 24, falas), `test_erros.py`, `test_idioma.py`. Expected: PASS (falhas pré-existentes inalteradas).
- [ ] **Step 6: Commit** `feat(requisito): heroi_no_grupo em conversas, destinos, slides e falas`.

---

### Task 2: Relógio de rodadas entre masmorras

**Files:**
- Modify: `server.py` (`GameRoom.__init__`; `load_authored_dungeon`; `_virada_de_rodada` ~18815; `FOTO_SALA_CATEGORIAS`; `_checkpoint_savegame` e o carregamento do save ~3823; `CAMPOS_DO_PONTO` ~2840; `validar_dungeon`; abertura de passagem secreta ~43373)
- Modify: `tools/editor.js` (painel de nível da masmorra: campos do relógio; roundtrip de `relogio` e de `relogio_desconto` na passagem secreta)
- Test: `tools/test_relogio_campanha.py`, `tools/test_relogio_editor.js`

**Interfaces:**
- Produces (masmorra): campo opcional `relogio: {"id": str, "limite": int, "fato_ao_passar": str, "avisos": [{"em": int, "texto": str}]}`; passagem secreta aceita `relogio_desconto: int` (rodadas subtraídas uma vez ao abrir).
- Produces (sala): `GameRoom.relogios: dict[str,int]` (categoria `jogo_salvo`, vai no `sg["relogios"]` e em `CAMPOS_DO_PONTO`), `GameRoom.relogio_def: dict|None` (categoria `foto`, derivado da masmorra carregada).
- Produces (método): `async GameRoom._relogio_tick()` — chamado dentro de `_virada_de_rodada`, isolado por `_isolar`; incrementa `relogios[id]`, narra cada aviso quando o contador **cruza** `em`, e ao passar de `limite` adiciona `fato_ao_passar` aos `fatos` uma única vez.

- [ ] **Step 1: Write the failing test** `tools/test_relogio_campanha.py` (sala montada como os outros testes, sem navegador):
  - `test_conta_so_com_relogio_na_masmorra`: sem `relogio_def`, `_virada_de_rodada` não cria `relogios`.
  - `test_soma_entre_duas_masmorras`: carregar masmorra A (relógio `p1`), 5 viradas; carregar masmorra B (mesmo id), 4 viradas → `relogios["p1"] == 9`.
  - `test_aviso_dispara_uma_vez_ao_cruzar`: `avisos=[{"em":3,"texto":"X"}]` → `gm_say` com o texto na 3ª virada e nunca mais.
  - `test_fato_ao_passar_do_limite`: com `limite=4`, `"fato_ao_passar"` entra em `fatos` na 5ª virada, uma vez.
  - `test_desconto_da_passagem_secreta`: abrir passagem com `relogio_desconto=2` desconta 2 (piso 0), uma vez só.
  - `test_persiste_no_save_e_no_ponto`: gravar e recarregar o jogo salvo e um ponto antigo (sem `relogios`) preserva/aceita o campo.
- [ ] **Step 2: Run** `python -X utf8 tools/test_relogio_campanha.py` — Expected: FAIL.
- [ ] **Step 3: Implement** o contador, a leitura de `relogio` em `load_authored_dungeon` (validado em `validar_dungeon`: `id` `[a-z0-9_]{1,40}`, `limite` ≥ 1, avisos com `em` ≥ 1 e texto ≤ 300), a categoria nova em `FOTO_SALA_CATEGORIAS` e o desconto na abertura da passagem. `relogios` salva em `_checkpoint_savegame`, lida no carregamento do save e incluída em `CAMPOS_DO_PONTO`.
- [ ] **Step 4: Editor** — seção "Relógio da campanha" no painel de nível da masmorra (id, limite, fato ao passar, lista de avisos) e campo "desconto do relógio" na passagem secreta; `buildJSON` só grava quando o id está preenchido. `test_relogio_editor.js` cobre o roundtrip estático.
- [ ] **Step 5: Run** `test_relogio_campanha.py`, `test_relogio_editor.js`, `test_salvar_masmorra.py` (seção [2] varre atributos sem categoria), `test_pontos_salvamento.py`, `test_continuar_jogo.py`, `test_simulador_turno.py`. Expected: PASS (pré-existentes inalteradas).
- [ ] **Step 6: Commit** `feat(motor): relogio de rodadas da campanha (soma entre masmorras, avisos, fato ao passar, desconto)`.

---

### Task 3: Fuga do chefe

**Files:**
- Modify: `server.py` (`_monster_dies_impl` ~50780; carga do monstro autorado em `load_authored_dungeon`; `validar_dungeon`)
- Modify: `tools/editor.js` (painel do monstro: "Foge ao ser derrotado" com fato e texto; roundtrip)
- Test: `tools/test_fuga_chefe.py`, `tools/test_fuga_chefe_editor.js`

**Interfaces:**
- Produces: campo do monstro colocado `fuga_chefe: {"fato": str, "texto": str}`. Quando o monstro receberia a morte (hp ≤ 0, sem `force`) e ainda não fugiu, `_monster_dies_impl` marca `m["fugiu"] = True`, narra `texto`, adiciona `fato` a `fatos` e conclui o resto do fluxo **sem** cadáver, sem loot e sem ouro (ele leva tudo); XP e contagem do objetivo seguem como numa morte comum. `_objetivo_cumprido` (`kill_target`) já enxerga `hp <= 0`, então o objetivo conta como cumprido.

- [ ] **Step 1: Write the failing test** `tools/test_fuga_chefe.py`:
  - `test_chefe_com_fuga_nao_deixa_cadaver_nem_loot_e_cumpre_o_objetivo`: monstro `authored_target` com `fuga_chefe`; `hp=0`; `_monster_dies` → sem entrada em `corpses`, sem baú de loot, `fatos` ganhou o fato, `_objetivo_cumprido({"type":"kill_target"})` é True, XP dado.
  - `test_morre_do_mesmo_jeito_por_caminhos_diferentes`: dano por arma, magia (`bola_fogo`), armadilha e veneno resolvem na mesma função e todos geram a fuga.
  - `test_chefe_sem_o_campo_morre_normal` e `test_so_foge_uma_vez` (segundo `_monster_dies` com `fugiu` já marcado não repete a narração).
  - `test_validador_recusa_fuga_malformada`.
- [ ] **Step 2: Run** `python -X utf8 tools/test_fuga_chefe.py` — Expected: FAIL.
- [ ] **Step 3: Implement** o desvio no começo de `_monster_dies_impl` (depois da guarda `hp > 0`, antes dos casos Troll/Lobisomem Alfa) e o gate de cadáver/loot/ouro por `m.get("fugiu")`. Leia o corpo de `_monster_dies_impl` inteiro antes de editar para achar onde cadáver, loot e ouro são criados. Validação e carga do campo em `load_authored_dungeon`.
- [ ] **Step 4: Editor** — campo no painel do monstro; `buildJSON`/`loadJSON` preservam `fuga_chefe`. `test_fuga_chefe_editor.js`: roundtrip.
- [ ] **Step 5: Run** `test_fuga_chefe.py`, `test_fuga_chefe_editor.js`, `test_objetivo_alternativo.py`, `test_objetivo_renome.py`, `test_charcos_fluxo.py`, `test_modo_mestre.py`, `test_tirano.py`. Expected: PASS (pré-existentes inalteradas).
- [ ] **Step 6: Commit** `feat(motor): fuga do chefe ao ser derrotado (fato, sem loot, objetivo cumprido)`.

---

### Task 4: Auditoria dos protótipos do autor

**Files:**
- Read: `world_adventures.json` (destinos `destino_1` "casa suspeita", `destino_2` "esconderijo de Leonel", `destino_3`/`destino_4` "Ad´Hadal"), `dungeons/casa_secreta.json`, `dungeons/floresta.json`, `dungeons/gustavo.json`, `dungeons/resgate de elara.json`, `dungeons/Introducao.json`, `city_scenes.json`
- Create: `docs/superpowers/specs/2026-10-21-elara-auditoria-prototipos.md`

**Interfaces:**
- Produces: um relatório curto (uma tabela: arquivo, tamanho do grid, nº de monstros/armadilhas/baús/passagens, objetivo, se serve para casa do bardo / fazenda / esconderijo do Leonel / Adhadal, o que falta) que decide quais mapas a Parte 1 reaproveita. **Nenhum arquivo do autor é alterado.**

- [ ] **Step 1: Para cada protótipo**, carregar com `carregar_dungeon`, rodar `validar_dungeon` e `nd_por_sala`/`faixa` (de `gerar_campanha_sombras`) e anotar os números na tabela.
- [ ] **Step 2: Decidir e registrar** no relatório, por candidato, uma das três saídas: "serve como está", "serve com ajustes feitos pelo autor no editor (lista exata)" ou "mapa novo necessário". Para "casa do bardo" e "fazenda", se nenhum protótipo servir, a Task 5 gera o mapa pelo molde de `tools/charcos_mapas.py`.
- [ ] **Step 3: Commit** `docs: auditoria dos prototipos da campanha de Elara`.

---

### Task 5: Parte 1 jogável — gerador, cena do Templo, destino e escolha

**Files:**
- Create: `tools/gerar_campanha_elara.py`
- Create (só se a Task 4 disser "mapa novo"): `tools/elara_mapas.py` com `masmorra_casa_bardo()` e `masmorra_fazenda()`
- Modify (pelo gerador): `city_scenes.json` (cena `templo_alva` de `alva_e_luz`), `city_map_points.json` (ponto `templo` ganha `scene: "templo_alva"`), `world_adventures.json` (destino `elara_parte1`), `dungeons/elara_*.json` (só mapas novos)
- Test: `tools/test_campanha_elara_parte1.py`, `tools/test_elara_fluxo.py`

**Interfaces:**
- Consumes: `heroi_no_grupo` (Task 1), `relogio` e `relogio_desconto` (Task 2), `fuga_chefe` (Task 3, não usado na Parte 1), arquivos escolhidos na Task 4.
- Produces (fatos): `elara_pediu` (Templo deu a missão), `elara_casa_vencida`, `elara_fazenda_vencida`, `elara_lento` (relógio passou do limite), `elara_ramo_a`, `elara_ramo_b`.
- Produces (destino): `elara_parte1` — 2 etapas emendadas: casa do bardo → fazenda; oculto até o fato `elara_pediu`; `ocultar_apos_concluir`; relógio `elara_p1` declarado nas duas masmorras (limite generoso, avisos do Templo; a fazenda e a casa carregam o mesmo `id`).
- Produces (cena `templo_alva`): NPC "Exequiel" (retrato/cena: arte do autor, se subida; senão provisória) com conversas:
  - `elara_pedido` (sem `elara_pediu`): pedido do resgate, recompensa, concede `elara_pediu`.
  - `elara_pedro_irma` (herói `mage`, uma vez): falas extras sobre a Elara.
  - `elara_henrique_pilheria` (herói `bard`, uma vez): "a irmã deve ser tão feia quanto ele".
  - `elara_pos_fazenda` (`elara_fazenda_vencida`, sem `elara_ramo_a`/`elara_ramo_b`): Exequiel em desordem, pressiona sem explicar o Olho.
  - `elara_escolher_mocas` (concede `elara_ramo_a`, exige `sem_fato: elara_ramo_b`) e `elara_escolher_gilo` (concede `elara_ramo_b`, exige `sem_fato: elara_ramo_a`), mutuamente exclusivas.
- Regras de texto: nada de Ferdinand/Vael'mon; o Templo "sabe e não diz" o que é o Olho.

- [ ] **Step 1: Write the failing test** `tools/test_campanha_elara_parte1.py` sobre `destinos()`/`conversas_templo()`:
  - o destino existe, tem 2 etapas e a primeira com `encadear` verdadeiro, é oculto até `elara_pediu`;
  - as 6 conversas existem, as duas de escolha são mutuamente exclusivas por `sem_fato`;
  - nenhuma conversa contém "Ferdinand" nem "Vael" (varredura de texto);
  - sem Pedro/Henrique no grupo, `_cenas_payload` mostra `elara_pedido` e nenhuma das falas de herói; com mago/bardo mostra a respectiva.
- [ ] **Step 2: Write the failing test** `tools/test_elara_fluxo.py` com o motor real: aceitar o pedido concede `elara_pediu` e revela o destino; vencer fazenda concede `elara_fazenda_vencida` e libera `elara_pos_fazenda`; escolher um ramo some a outra opção; com o relógio passando do limite, `elara_lento` aparece e a conversa pós-fazenda ainda oferece as duas escolhas (nunca bloqueia).
- [ ] **Step 3: Run** os dois — Expected: FAIL.
- [ ] **Step 4: Implement** `tools/gerar_campanha_elara.py` no molde de `gerar_campanha_charcos.py`: `--simular` relata ND/artes/avisos, `--cadeia`-like opção para aplicar sobre mapas já gravados, assinaturas em `tools/.elara_assinaturas.json`, só toca em ids `elara_*` e na cena `templo_alva`. Os dois fatos de vitória vêm do objetivo da casa e da fazenda (`fato` no objetivo principal, que `_aplicar_renome_fato` já grava).
- [ ] **Step 5: Run** os dois testes novos e `test_cenas_conversa.py`, `test_cidades_editor.py`, `test_campanha_charcos.py`, `test_masmorra_sequenciada.py`. Expected: PASS.
- [ ] **Step 6: Rodar o gerador** com `--simular` e depois de verdade; conferir `git status` (só arquivos `elara_*`, `city_scenes.json`, `city_map_points.json`, `world_adventures.json`, `tools/editor_dungeons.js`).
- [ ] **Step 7: Commit** `feat(elara): Parte 1 jogavel (Templo, casa do bardo, fazenda, volta e escolha)`.

---

### Task 6: Documentação e prova final

**Files:**
- Modify: `CLAUDE.md` (seção "Campanha O Resgate de Elara — Parte 1" com as três peças de motor, os fatos, o gerador e os testes)
- Test: suítes citadas nas tarefas 1–5

- [ ] **Step 1:** Documentar em `CLAUDE.md` (CRLF) o requisito `heroi_no_grupo`, o relógio (`relogio`, `relogios`, `relogio_desconto`), a fuga do chefe (`fuga_chefe`), os fatos `elara_*` e o gerador.
- [ ] **Step 2:** Rodar todas as suítes das tarefas 1–5 e `tools/dividas.py --strict`; registrar no relatório do PR quais falhas já existiam na base.
- [ ] **Step 3: Prova em jogo real** (servidor isolado numa porta própria): criar sala com Pedro e Henrique, aceitar o pedido no Templo, ver as duas falas extras, entrar na casa e na fazenda, deixar passar o relógio e conferir `elara_lento`, voltar ao Templo e escolher um ramo.
- [ ] **Step 4: Commit** `docs: Parte 1 da campanha de Elara`.
