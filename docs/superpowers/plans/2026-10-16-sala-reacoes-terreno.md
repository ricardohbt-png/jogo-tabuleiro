# Sala das Reações de Terreno — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Acrescentar ao Campo de Treinamento uma sala longa, depois do corredor de armadilhas, que ensina gás + fogo + água (obrigatória pela porta) e piche + fogo (opcional) para as 6 classes.

**Architecture:** O gás é uma `camara_gas` já existente, criada na preparação do treinamento com os campos novos `permanente` e `dano_explosao`. Uma condição nova de porta (`gas`) tranca a passagem até o gás explodir. Dois verbos de lição novos recebem eventos dos hooks das reações. Mapa, baús, falas e textos nascem de um script idempotente (`aplicar_fatia20_tutorial.py`), como as fatias anteriores.

**Tech Stack:** Python (`server.py`, `terrain_reactions.py`, `tutorial_training.py`), JS vanilla (`src/gameState.js` não muda), JSON de masmorra, dicionários `src/lang/*.js`, testes `unittest`/scripts `check()` em `tools/`.

**Spec:** `docs/superpowers/specs/2026-10-16-sala-reacoes-terreno-design.md`

## Global Constraints

- Grid `57×40` (antes `57×33`); linha 39 é parede.
- Sala 49 **não muda** (`x48..53, y26..31`, `locked: true`); passa a ser a sala do gás. Porta nova em `[51,32]`; sala 51 nova em `x48..53, y33..38`, `locked: true`; saída `exit = {x:51, y:36}`.
- Zona de gás id `gas_tutorial`: `tipo "camara_gas"`, `room_id 49`, `permanente true`, `dificuldade 10`, `dano "1"`, `dano_explosao "1d4"`. Fora do treinamento nada muda (explosão segue `2d6`, câmara segue dissipando).
- Baú do gás: 3 `frasco_oleo`, numa casa de água do lago `x50..52, y28..29`. Baú da parte 2: 2 `frasco_piche` + 2 `frasco_oleo`. Boneco da parte 2 a ≤4 casas de quem está perto da porta `[51,32]`.
- Lições: `fala_armadilhas` 35 (não muda), `fala_gas` 36, `fala_piche` 37 (opcional), `fala_retirada` 38 com `continua_sem` acrescido de `fala_piche`.
- Nenhum herói das 6 classes pode morrer por causa da sala (Mago: 7 PV).
- `server.py`, `game.js` e `CLAUDE.md` estão em CRLF: edite com a ferramenta de edição, não com `replace` multilinha em script.
- Commite só caminhos explícitos; nunca `git add -A`. Não rode `configurar_tutorial_salas.py` inteiro para validar (reordena chaves do JSON); aplique a fatia 20 sozinha.
- Toda mensagem nova de servidor usa `T("chave")` com `pt` e `en` e paridade de `{parâmetros}`.

## Review Focus

- Herói que chega à `fala_gas` depois de outro já ter detonado: a lição vira "pulada" (sem prêmio), a porta já está aberta, nada trava (Task 4, Task 8).
- Dois heróis, um detona com o outro dentro do gás em terra firme (Mago de 7 PV, pior caso de dado + 1 de veneno): ninguém morre (Task 8).
- Herói joga o óleo fora do gás ou erra e fica sem frasco no baú e na bolsa: o frasco de socorro aparece e a porta ainda abre (Task 5, Task 8).
- O gás sobrevive a `enter_dungeon`, a 10+ rodadas parado e ao salvar/retomar a foto (Task 1, Task 6).
- Mago/Clérigo detonando de fora com Bola de Fogo também conclui a lição e abre a porta (Task 3, Task 8).
- Rodar a fatia 20 duas vezes, ou depois do `configurar_tutorial_salas.py`, não duplica sala, baú, fala nem porta (Task 7).

---

### Task 1: Zona de gás permanente e dano de explosão por zona

**Files:**
- Modify: `server.py` (`_processar_zonas_turno_impl`, ramos `camara_gas` e `nuvem_gas`, por volta da linha 34936)
- Modify: `terrain_reactions.py` (`_rx_explodir_gas`)
- Create: `tools/test_sala_reacoes_tutorial.py` (seções [1]–[6] ao longo do plano)

**Interfaces:**
- Produces: campos opcionais de zona `permanente: bool` (não dissipa) e `dano_explosao: str` (expressão de dado; ausente = `RX_GAS_DANO`).

- [ ] **Step 1: Write the failing tests** (seção [1]) reaproveitando `sala()`, `heroi()`, `camara()`, `fixa()` de `tools/test_fogo_gas.py` (copie as definições; o arquivo não é importável sem rodar):
  - `test_permanente_nao_dissipa`: zona com `duracao 2, permanente True`; chame `_processar_zonas_turno_impl()` 5 vezes; `z["ativa"] is True`.
  - `test_sem_permanente_dissipa`: mesma zona sem a marca; depois de 2 chamadas `z["ativa"] is False`.
  - `test_dano_explosao_da_zona`: `r._rolar_dado` grava a expressão pedida; zona com `dano_explosao "1d4"`; explosão registra `"1d4"` e nunca `"2d6"`.
  - `test_dano_explosao_padrao`: zona sem o campo pede `"2d6"`.
- [ ] **Step 2: Run** `python -X utf8 tools/test_sala_reacoes_tutorial.py` — Expected: FAIL (permanente dissipa; explosão pede `2d6`).
- [ ] **Step 3: Implement.** Nos dois ramos de dissipação (`camara_gas`, `nuvem_gas`), pule o decremento quando `z.get("permanente")`. Em `_rx_explodir_gas`, a expressão do dado é `z["dano_explosao"]` da primeira zona tocada que o tiver, senão `RX_GAS_DANO`.
- [ ] **Step 4: Run** o arquivo novo e `python -X utf8 tools/test_fogo_gas.py` — Expected: tudo passa (o legado não regride).
- [ ] **Step 5: Commit** `git add server.py terrain_reactions.py tools/test_sala_reacoes_tutorial.py && git commit -m "feat: gas permanente e dano de explosao por zona"`.

### Task 2: Condição de porta `gas`

**Files:**
- Modify: `server.py` — `validar_dungeon` (~8405, lista de tipos), carregador `load_authored_dungeon` (~15990), `_door_condition_satisfied` (~18150), `_door_condition_message` (~18166), serializador de `door_conditions` (~41340)
- Modify: `src/lang/erros.js` (chave `erro.porta_exige_gas_consumido`, `pt`+`en`)
- Test: `tools/test_sala_reacoes_tutorial.py` (seção [2])

**Interfaces:**
- Consumes: `self.zonas_especiais` (Task 1).
- Produces: condição `{"type":"gas","zona_id":str}`; `_door_condition_satisfied((x,y))` é `True` quando nenhuma zona com esse `id` está `ativa`; payload `door_conditions[chave]` ganha `zona_id`.

- [ ] **Step 1: Write the failing tests** (seção [2]): `validar_dungeon` aceita `{"type":"gas","zona_id":"gas_tutorial"}` e recusa `zona_id` vazio ou ausente; após `load_authored_dungeon`, `r._door_condition_satisfied((51,32))` é `False` com a zona ativa, `True` com `ativa=False` e `True` sem zona nenhuma; `handle_open_door` numa porta não satisfeita responde com a chave `erro.porta_exige_gas_consumido`; o payload `_game_state_payload()["door_conditions"]["51,32"]` traz `satisfied` e `zona_id`. Use uma masmorra mínima com porta em `[51,32]` (padrão de `dungeon()` em `tools/test_altura_parede.py`).
- [ ] **Step 2: Run** — Expected: FAIL (tipo `gas` inválido).
- [ ] **Step 3: Implement** nos cinco pontos listados; a validação **não** checa se a zona existe (ela nasce em tempo de execução, Task 6). Chave de idioma com `pt` "🚪 O gás selou esta porta. Detone-o com fogo." e `en` equivalente.
- [ ] **Step 4: Run** a seção [2], `python -X utf8 tools/test_idioma.py` e `python -X utf8 tools/test_erros.py` — Expected: passam.
- [ ] **Step 5: Commit** os arquivos acima com `feat: condicao de porta gas`.

### Task 3: Verbos `explodir_gas` e `incendiar_piche` e seus eventos

**Files:**
- Modify: `server.py` (`LICAO_VERBOS`, linha 47)
- Modify: `tools/editor_guia_logic.js` (mesma lista de verbos)
- Modify: `tutorial_training.py` (dois métodos novos)
- Modify: `terrain_reactions.py` (`_rx_explodir_gas`, `_rx_incendiar_piche`: chamar os métodos)
- Test: `tools/test_sala_reacoes_tutorial.py` (seção [3]) e `tools/test_editor_guia.py` (já compara as listas)

**Interfaces:**
- Produces: `async def _training_gas_consumido(self, zona: dict) -> None` — em `training_mode`, chama `_licao_evento(p, "explodir_gas", alvo=zona["id"])` para **cada** herói de `self.players`; `async def _training_piche_aceso(self, caster_id) -> None` — chama `_licao_evento(self.players.get(caster_id), "incendiar_piche")` só para o autor. Ambos são no-op fora do treinamento.

- [ ] **Step 1: Write the failing tests** (seção [3]): em sala com `training_mode True` e duas lições montadas à mão em `r.licoes` (`tarefa.tipo` `explodir_gas`/`incendiar_piche`), (a) detonar o gás por `_rx_registrar` fogo conclui a lição `fala_gas` de **dois** heróis; (b) acender piche conclui `fala_piche` só do `caster_id`; (c) fora do treinamento nada é emitido; (d) detonar com `Bola de Fogo` (origem `{"tipo":"magia","id":"bola_fogo"}`) também conclui.
- [ ] **Step 2: Run** — Expected: FAIL (verbo inválido).
- [ ] **Step 3: Implement.** Acrescente os dois verbos a `LICAO_VERBOS` e à lista do `editor_guia_logic.js`; implemente os métodos; chame-os ao fim de `_rx_explodir_gas` (depois de consumir as zonas, uma vez por zona tocada) e de `_rx_incendiar_piche` (depois de criar a zona de chamas, com `origem.get("caster_id")`).
- [ ] **Step 4: Run** a seção [3] e `python -X utf8 tools/test_editor_guia.py` — Expected: passam.
- [ ] **Step 5: Commit** com `feat: verbos de licao explodir_gas e incendiar_piche`.

### Task 4: Lição de estado pulada quando o gás já foi consumido

**Files:**
- Modify: `tutorial_training.py` (método novo)
- Modify: `server.py` (`_verificar_falas`, ~20048: uma chamada)
- Test: `tools/test_sala_reacoes_tutorial.py` (seção [4])

**Interfaces:**
- Produces: `async def _pular_licao_de_estado(self, p, fala) -> bool` — `True` e marca a lição como pulada (mesmo efeito de `_pular_etapas_abandonadas`: `licoes_feitas`, `licoes_puladas`, `licao_progresso`, mensagem `licao_pulada`, **sem** `tutorial_history` nem prêmio) quando `fala.tarefa.tipo == "explodir_gas"` e a zona `tarefa.alvo` não existe ou não está `ativa`.

- [ ] **Step 1: Write the failing tests** (seção [4]): herói B chega à `fala_gas` (proximidade) com `gas_tutorial` inativa → `licao_atual` não vira `fala_gas`, `fala_gas in B["licoes_puladas"]`, `fala_gas not in B["tutorial_history"]`, ouro e XP inalterados; com a zona ativa a lição abre normalmente; a seguinte (`fala_piche`) fica liberada depois da pulada.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** o método e, em `_verificar_falas`, chame-o logo depois de confirmado o gatilho e antes de `_disparar_fala`; se devolver `True`, `continue`.
- [ ] **Step 4: Run** a seção [4] e `python -X utf8 tools/test_tutorial_fatia8.py` — Expected: passam (pular etapas segue igual).
- [ ] **Step 5: Commit** com `feat: licao de estado pulada se o gas ja foi consumido`.

### Task 5: Frasco de socorro

**Files:**
- Modify: `tutorial_training.py` (método novo)
- Modify: `server.py` (`_start_initiative_player_turn`, ~17630, logo depois de `_processar_camara_gas_inicio_turno`)
- Modify: `src/lang/narracao.js` (chave `narracao.frasco_de_socorro_do_treinamento`, `pt`/`en`, parâmetro `{heroi}`)
- Test: `tools/test_sala_reacoes_tutorial.py` (seção [5])

**Interfaces:**
- Produces: `async def _training_frasco_socorro(self, p) -> bool` — dá 1 `frasco_oleo` com `tutorial_loan True` quando: `training_mode`, `gas_tutorial` ativa, `p` está em `training`, sem `frasco_oleo` na bolsa, nenhum baú da sala 49 ainda contém `frasco_oleo`, e a bolsa tem espaço. Devolve `True` se deu.

- [ ] **Step 1: Write the failing tests** (seção [5]): dá o frasco quando todas as condições valem; **não** dá com óleo na bolsa, com óleo ainda no baú, com gás inativo, com bolsa cheia, nem fora do treinamento; chamado duas vezes seguidas dá só um (a segunda já tem óleo).
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** usando `hidratar_itens_bau([{"id":"frasco_oleo"}])[0]` (padrão de `veneno_rapido` em `_training_prepare`) e narre com `gm_say(T(...))`. Chame o método no início do turno.
- [ ] **Step 4: Run** a seção [5] e `python -X utf8 tools/test_idioma.py` — Expected: passam.
- [ ] **Step 5: Commit** com `feat: frasco de socorro no treinamento`.

### Task 6: Criar o gás na preparação do treinamento

**Files:**
- Modify: `tutorial_training.py` (`_training_init`, ~115; constantes `TREINO_GAS_ID`, `TREINO_GAS_SALA`; método novo)
- Test: `tools/test_sala_reacoes_tutorial.py` (seção [6])

**Interfaces:**
- Produces: `TREINO_GAS_ID = "gas_tutorial"`, `TREINO_GAS_SALA = 49`; `def _training_criar_gas(self) -> None` — idempotente por id; só cria se a sala 49 existir.

- [ ] **Step 1: Write the failing tests** (seção [6]) carregando `dungeons/campo_de_treinamento.json` (já com a fatia 20, Task 7; se rodar antes, monte uma masmorra mínima com `tutorial_training: true` e sala 49): depois de `load_authored_dungeon` **e** de `enter_dungeon`, existe exatamente 1 zona `gas_tutorial` com os campos das Global Constraints; chamar `_training_criar_gas()` de novo não duplica; mapa sem sala 49 não cria nada; 10 chamadas de `_processar_zonas_turno_impl` não a desativam; `foto_empacotar`/aplicação da foto devolve a zona intacta (`zonas_especiais` é categoria `foto`). **Se `enter_dungeon` limpar a zona** (há `self.zonas_especiais = []` em ~17305), crie-a depois dessa limpeza.
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** a seção [6] e `python -X utf8 tools/test_salvar_masmorra.py` (compare com a base: a falha preexistente é a mesma).
- [ ] **Step 5: Commit** com `feat: gas permanente na sala do treinamento`.

### Task 7: Dados — mapa, baús, porta, falas e textos (fatia 20)

**Files:**
- Create: `tools/aplicar_fatia20_tutorial.py` (função `aplicar(d)` idempotente + `main()` no padrão de `aplicar_fatia13_tutorial.py`)
- Modify: `tools/configurar_tutorial_salas.py` (importar e chamar `_F20.aplicar(d)` logo depois de `_F19.aplicar(d)`)
- Modify: `tools/aplicar_tutorial_missao.py` (a ala final: `exit` e a fala `fala_retirada` passam a ser derivados da fatia 20, para o patch antigo não desfazer o novo)
- Modify: `tools/tutorial_guia_comum.py` (guia de `fala_gas` e `fala_piche`; termos de glossário `reacao` e `inflamavel`), regenerar `src/lang/tutorial_guia.js` com `tools/gerar_guia_comum.py`
- Modify: `dungeons/campo_de_treinamento.json`, `tools/editor_dungeons.js` (regenerado)
- Test: `tools/test_tutorial_fatia20.py`

**Interfaces:**
- Consumes: condição de porta (Task 2), verbos (Task 3).
- Produces: `aplicar(d: dict) -> dict` (muta e devolve a definição); constantes `GRID_H = 40`, `SALA_GAS = 49`, `SALA_PICHE = 51`, `PORTA = [51,32]`, `SAIDA = [51,36]`.

- [ ] **Step 1: Write the failing tests** (`tools/test_tutorial_fatia20.py`, `unittest`), todos sobre `aplicar(copia)` da definição atual:
  - grid `h == 40`, todas as linhas de `tiles` com `len == 57`, linha 39 toda parede; `tiles[32][51] == DOOR`; sala 51 em `x48 y33 w6 h6 locked`; sala 49 inalterada e com `doors == [[51,25],[51,32]]`; `exit == {x:51,y:36}`.
  - `door_conditions["51,32"] == {"type":"gas","zona_id":"gas_tutorial"}`.
  - lago: `materiais` `agua` em `x50..52, y28..29`; baú de 3 `frasco_oleo` numa dessas casas; baú da sala 51 com 2 `frasco_piche` + 2 `frasco_oleo`; 1 `boneco_treino` na sala 51 a ≤4 casas de `[51,33]`.
  - lições: `fala_gas` (36, `tarefa.tipo explodir_gas`, `alvo "gas_tutorial"`), `fala_piche` (37, `incendiar_piche`), `fala_retirada` (38, `pos`/`alvo` `[51,36]`, `continua_sem` contém `fala_piche`); ordens 35..38 sem repetição.
  - `validar_dungeon(d)` devolve `(True, _)`.
  - idempotência: `aplicar(aplicar(c)) == aplicar(c)`; e após `_F19.aplicar` + `aplicar_tutorial_missao.aplicar` + `aplicar` o resultado é o mesmo (a ordem do `configurar_tutorial_salas` não desfaz nada).
  - guia: `fala_gas` e `fala_piche` têm `guia` com chaves `ui.tutorial.*` existentes em pt e en; nenhum passo usa `conclui_com` de evento que o herói possa ter feito antes (use "Entendi" nos informativos).
- [ ] **Step 2: Run** — Expected: FAIL (módulo inexistente).
- [ ] **Step 3: Implement** a fatia 20 de forma cirúrgica (só acrescenta/ajusta; não reordena chaves do JSON). Confirme no validador se um baú em casa de água é aceito; se não, mova o baú para uma casa de chão **colada ao lago** e ajuste o teste e o design. Os textos pt/en seguem o guia do tutorial: verbo de ação no texto, passo informativo "Entendi", último passo encerrado pela tarefa.
- [ ] **Step 4: Run** `python tools/aplicar_fatia20_tutorial.py`, regenere o snapshot do editor com `python -X utf8 -c "import server; server._regen_dungeons_index()"` (só o `tools/editor_dungeons.js`; não rode `export_catalog.py` inteiro), depois `python -X utf8 tools/test_tutorial_fatia20.py`, `tools/test_tutorial_conteudo.py`, `tools/test_tutorial_guia.py`, `tools/test_editor_guia.py`, `tools/test_editor_guia_logic.js` — Expected: passam. Se `test_tutorial_conteudo`/`test_tutorial_fatia8` citarem a ordem 36 da retirada, atualize-os para 38; `test_tutorial_resistencia` espera uma saída antiga (`[51,24]`): leia-o e corrija a expectativa para `[51,36]`, anotando no commit.
- [ ] **Step 5: Commit** os arquivos acima (caminhos explícitos) com `feat(tutorial): fatia 20 - sala das reacoes de terreno`.

### Task 8: Fluxo real, com grupo e pior caso

**Files:**
- Create: `tools/test_sala_reacoes_fluxo.py`

**Interfaces:**
- Consumes: tudo acima. Siga o padrão de `FluxoRealTests` e `_sala_real()` de `tools/test_tutorial_refem.py` (iniciativa e `push_state` reais).

- [ ] **Step 1: Write the tests** (devem passar; se falharem, o defeito é das tasks anteriores):
  - `test_heroi_solo_completa_a_sala`: guerreiro anda até `[51,24]` (conclui `fala_armadilhas`), recebe `fala_gas`; a porta `[51,32]` recusa abrir (`erro.porta_exige_gas_consumido`); entra no gás (1 de veneno só no início do turno), pega os frascos no baú do lago, joga um numa casa de gás estando em água; o gás some, `fala_gas in licoes_feitas`, a porta abre.
  - `test_agua_reduz_a_explosao`: com dado fixo no máximo (4), o herói em água perde 2 e o em terra firme perde 4.
  - `test_grupo_nao_morre_no_pior_caso`: Mago (7 PV) em terra firme dentro do gás, 1 de veneno já aplicado, dado no máximo e Reflexos falhando: PV final ≥ 1. Repita para as 6 classes.
  - `test_chegada_tardia`: o herói B só chega à `fala_gas` depois da explosão de A: lição pulada, porta aberta, B segue para a retirada.
  - `test_sem_frasco_nao_trava`: herói gasta os 3 frascos fora do gás; no início do turno seguinte recebe o de socorro; consegue detonar.
  - `test_mago_detona_de_fora`: Mago em `[51,25]` lança Bola de Fogo numa casa do gás; lição concluída para todos.
  - `test_parte_2_opcional`: piche num turno, óleo no seguinte, `fala_piche` concluída para o autor; pular a parte 2 não impede a retirada (`fala_retirada` abre e conclui em `[51,36]`).
- [ ] **Step 2: Run** `python -X utf8 tools/test_sala_reacoes_fluxo.py` — Expected: todos passam.
- [ ] **Step 3: Commit** com `test: fluxo real da sala das reacoes de terreno`.

### Task 9: Prova no navegador, regressão e documentação

**Files:**
- Modify: `CLAUDE.md` (registro da fatia 20 no bloco do Campo de Treinamento; mencionar a zona `permanente`, `dano_explosao` e a condição de porta `gas`)
- Modify: `docs/superpowers/specs/2026-10-16-sala-reacoes-terreno-design.md` (trocar `aplicar_fatia18` por `aplicar_fatia20`)

- [ ] **Step 1: Prova visual.** Suba um servidor isolado numa porta própria a partir de uma cópia limpa (nunca a 8765), gere um `game_state` da sala com o gás ativo (`_game_state_payload()`), abra `index.html?preview=1` e injete com `GS.injectPreviewState`. Confira, sem erro no console: nuvem de gás na sala 49, lago, baú, porta `[51,32]` fechada e a sala 51. Repita com o gás consumido: porta aberta. Registre na resposta o que viu.
- [ ] **Step 2: Regressão.** Rode `python -X utf8 tools/test_*.py` nos testes de tutorial, reações, gás, idioma e `test_preview_editor`; compare com a base (`git worktree` do commit anterior) e trate como regressão só o que passa na base e falha agora. Rode `python -X utf8 tools/dividas.py --strict`.
- [ ] **Step 3: Documentar** em `CLAUDE.md` e corrigir o nome do script no design.
- [ ] **Step 4: Commit** `CLAUDE.md` e o design com `docs: registra a fatia 20 do tutorial`.
