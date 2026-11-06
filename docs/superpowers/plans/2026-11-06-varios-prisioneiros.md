# Vários prisioneiros e resgate por faixas — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** permitir vários reféns por mapa, com modo guiar/seguir, chegada que tira o refém do mapa e recompensa por quantidade salva, e usar isso nas 6 crianças dos Charcos.

**Architecture:** `GameRoom.prisoners` vira a fonte da verdade (lista de dicts com `id` estável); `prisoner` fica como propriedade de compatibilidade (primeiro refém), o que mantém o jogo e as ~30 suítes de pé enquanto os 114 pontos do servidor migram. O modo por faixas só liga quando o objetivo principal traz `faixas`; sem isso, nada muda.

**Tech Stack:** Python 3 (`server.py`, unittest), JS sem bundler (`src/gameState.js`, `game.js`, `tools/editor.js`), testes em node.

**Spec:** `docs/superpowers/specs/2026-11-06-varios-prisioneiros-design.md`

## Global Constraints

- Mapa com um refém e objetivo sem `faixas` se comporta e se grava como hoje.
- `server.py`, `game.js` e `CLAUDE.md` são CRLF: edite com a ferramenta de edição; script com `\n` no `replace` não casa.
- `gameState.js` não toca em DOM/THREE/window. `GS.on` tem um ouvinte por evento. `GS.isMyTurn` é propriedade.
- Texto novo vai por `T("chave")` no servidor e `t("chave")` no cliente, com `pt` e `en` (`src/lang/narracao.js`, `erros.js`, `interface.js`, `editor.js`). `python -X utf8 tools/dividas.py` não pode ganhar dívida.
- Campo novo em `GameRoom` entra em `FOTO_SALA_CATEGORIAS`.
- Pare o servidor na 8765 antes de gravar `server.py`/`game.js` por script, e reinicie antes de provar mudança no navegador.
- Limite: 12 reféns por mapa. PV 7, CA 10, movimento 6 (`PRIS_HP`/`PRIS_AC`/`PRIS_MOVE`).

## Review Focus

1. Refém salvo continua na lista: não pode ocupar casa, levar dano de área nem ser alvo (teste na Task 3).
2. Herói controlador morre com reféns em Seguir: o controle passa ao herói vivo mais próximo, e eles seguem o novo dono (Task 3).
3. Vários reféns seguindo o mesmo herói: nunca dois na mesma casa, nem em cima de herói (Task 3).
4. Solo com grupo: o refém pertence ao herói extra que libertou, não à conexão (Task 3).
5. Foto salva com vários reféns, alguns salvos, retomada no meio: ids, modos, contagem e janela intactos (Task 1 e Task 4).

---

### Task 1: Lista de reféns com compatibilidade

**Files:**
- Modify: `server.py` (`validar_dungeon` ~8871, `GameRoom.__init__` ~13448, `load_authored_dungeon` ~18872, `FOTO_SALA_CATEGORIAS` ~3749, `_foto_aplicar_sala` ~30134, payload ~57835)
- Test: `tools/test_varios_refens.py` (criar)

**Interfaces:**
- Produces: `GameRoom.prisoners: list[dict]`; propriedade `GameRoom.prisoner` (get: primeiro refém não salvo, senão o primeiro, senão `None`; set: `None` esvazia a lista, dict vira lista de um com `setdefault("id", "refem_0")`); `_novo_refem(pr: dict, i: int) -> dict` (módulo; campos de hoje + `id=f"refem_{i}"`, `modo="guiar"`, `salvo=False`, `nome=pr.get("nome") or "Prisioneiro"`); `_refens_da_definicao(defn) -> list[dict]` (módulo; aceita `prisoner` ou `prisoners`); `GameRoom._refem_por_id(rid) -> dict|None` (aceita `refem_N`; `None`, `"prisoner"` e `"__prisioneiro__"` devolvem `self.prisoner`); `GameRoom._eh_refem(x) -> bool` (por identidade na lista); `GameRoom._refens_no_mapa() -> list[dict]` (vivos e não salvos).
- `game_state` passa a mandar `prisoners` (lista) no lugar de `prisoner`.

- [ ] **Step 1: Teste falhando** em `tools/test_varios_refens.py` (unittest, com o helper `sala(defn)` de `test_elara_leonel_mansao.py`):

```python
def test_mapa_antigo_vira_lista_de_um(self):
    r = sala(mapa(prisoner={"pos": [3, 3], "room_id": None}))
    self.assertEqual([p["id"] for p in r.prisoners], ["refem_0"])
    self.assertIs(r.prisoner, r.prisoners[0])
    self.assertEqual(r.prisoner["nome"], "Prisioneiro")
def test_varios_com_ids_e_nomes(self):
    r = sala(mapa(prisoners=[{"pos": [3, 3], "nome": "Tico"}, {"pos": [4, 3]}]))
    self.assertEqual([p["id"] for p in r.prisoners], ["refem_0", "refem_1"])
    self.assertEqual(r.prisoners[1]["nome"], "Prisioneiro")
def test_setter_de_compatibilidade(self):
    r = sala(mapa()); r.prisoner = {"pos": [1, 1], "alive": True}
    self.assertEqual(r.prisoners[0]["id"], "refem_0"); r.prisoner = None
    self.assertEqual(r.prisoners, [])
def test_validador(self):  # 13 reféns, casa repetida, as duas chaves juntas: recusados
def test_foto_antiga_e_nova(self):  # sala com "prisoner" na foto vira lista; "prisoners" volta com ids, modo e salvo
```

`mapa(**extra)` é um dict mínimo válido em tiles de chão, definido no próprio teste.

- [ ] **Step 2:** `python -X utf8 tools/test_varios_refens.py`. Expected: falha com `AttributeError: prisoners`.
- [ ] **Step 3: Implementar** o que está em Interfaces. No validador, `prisoners` aplica as checagens de `prisoner` a cada item; recusa as duas chaves juntas, mais de 12 e casas repetidas. Em `FOTO_SALA_CATEGORIAS`, troque `"prisoner"` por `"prisoners": "foto"`. `_foto_aplicar_sala` converte `sala["prisoner"]` antigo por `_novo_refem`, preservando os campos gravados. O `__init__` usa `self.prisoners = []`.
- [ ] **Step 4:** a suíte nova, `test_salvar_masmorra.py`, `test_dungeon_loader.py`, `test_tutorial_refem.py` e `test_objetivos.py`. Expected: todas passam.
- [ ] **Step 5: Commit** `feat(reféns): lista de reféns no mapa e na foto`.

### Task 2: Migrar os pontos do servidor

**Files:**
- Modify: `server.py`, `tutorial_training.py`
- Test: `tools/test_varios_refens.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: `_entidade_key` de refém vira `pr:<id>` (hoje `pr:singleton`); `_protetor_target_id(alvo)` devolve o `id` do refém; `_protetor_target("__prisioneiro__")` segue valendo para foto antiga; `PROTETOR_PRISIONEIRO_ID` só como alias; alvo de armadilha/aviso usa `pr["id"]` onde hoje usa `"__prisioneiro__"`.

- [ ] **Step 1: Testes falhando:**

```python
def test_sem_uso_direto_de_prisoner_no_servidor(self):
    # AST: atributo .prisoner de self só nas linhas da propriedade e nas listadas em PERMITIDOS
def test_area_atinge_cada_refem_liberto(self):
    # 2 reféns libertos na mesma área: _alvos em área devolve os dois
def test_casa_ocupada_por_qualquer_refem(self):
    # herói não entra na casa do 2º refém; _tile_livre_para_animado recusa
def test_dano_nao_confunde_refens(self):
    # dano letal no 2º refém: só ele morre; rescuer e estado do 1º intactos
def test_protetor_no_segundo_refem(self):
    # vínculo com refem_1 divide o dano dele, e não o de refem_0
```

- [ ] **Step 2:** rodar. Expected: FAIL nos cinco.
- [ ] **Step 3: Migrar** por padrão, usando `grep -n "self\.prisoner"`: `alvo is self.prisoner` vira `self._eh_refem(alvo)`; `if self.prisoner: X.append(self.prisoner)` vira laço em `self._refens_no_mapa()`, mantendo o filtro `freed` onde existe; `_prisioneiro_morre()` passa a receber o refém (`_prisioneiro_morre(pr)`), e os sítios passam o `alvo`. A lista `PERMITIDOS` fica com a propriedade, o tutorial do refém único (`tutorial_training.py`) e o payload de compatibilidade, e deve ser curta.
- [ ] **Step 4:** a suíte nova e todas as listadas por `grep -ln prisoner tools/test_*.py`. Expected: passam. Teste que cravar `"pr:singleton"` ou `"__prisioneiro__"` passa a usar o id.
- [ ] **Step 5: Commit** `refactor(reféns): servidor trata cada refém pela lista`.

### Task 3: Libertar, janela, seguir e chegada

**Files:**
- Modify: `server.py` (`handle_libertar_prisioneiro` ~57023, `handle_mover_prisioneiro*` ~57043, `_animados_atual` ~45026, `handle_end_turn` ~45278, encerrar peça ~45096/45128, despacho ~59041/59204), `FOTO_SALA_CATEGORIAS`
- Test: `tools/test_varios_refens.py`

**Interfaces:**
- Consumes: Tasks 1 e 2.
- Produces: mensagens `libertar_prisioneiro {refem_id?}`, `mover_prisioneiro {refem_id?, dx, dy}`, `mover_prisioneiro_caminho {refem_id?, path}`, `set_modo_refem {refem_id, modo}`. `animados_atual[pid]` e `animados_done` usam o id do refém. `self.prisioneiros_done: set[str]` substitui `prisioneiro_done` (categoria `janela`). `_passo_refem(pr, dx, dy) -> bool` (o miolo de `handle_mover_prisioneiro`, sem as recusas ao jogador). `_preparar_refem_turno(pr) -> None`. `_mover_refens_seguindo(pid) -> None` (async). `_refem_chegou(pr) -> bool` (async). `_destino_resgate() -> list|None`.

- [ ] **Step 1: Testes falhando:**

```python
def test_libertar_escolhe_e_gasta_acao(self):      # refem_id livra só aquele; 2º no mesmo turno recusado por ação
def test_libertar_sem_id_pega_o_adjacente(self):
def test_janela_so_com_guiados_em_ordem(self):     # 2 guiados: animados_atual = refem_0, depois refem_1; refém em seguir fica fora
def test_modo_so_do_dono(self):                    # outro herói recusado; dono troca fora do turno, sem gastar ação
def test_seguir_anda_sem_abrir_janela(self):       # só seguidores: end_turn não abre janela e o refém fica adjacente ao herói
def test_seguir_nao_empilha(self):                 # 3 seguidores: casas distintas, nenhuma de herói
def test_seguir_sem_caminho_fica_parado(self):
def test_seguir_dispara_armadilha(self):
def test_chegada_tira_do_mapa(self):               # com faixas: salvo=True, some de _refens_no_mapa; área não atinge; a casa fica livre
def test_mapa_sem_faixas_nao_some(self):           # Elara continua no mapa ao chegar
def test_controle_passa_ao_mais_proximo(self):     # dono morto: rescuer_pid muda e o refém segue o novo dono
def test_solo_grupo_refem_do_extra(self):          # herói extra liberta: janela e seguir usam o pid dele
```

- [ ] **Step 2:** rodar. Expected: FAIL.
- [ ] **Step 3: Implementar.** Com `refem_id` ausente, `handle_libertar_prisioneiro` pega o primeiro cativo adjacente. `_animados_atual` percorre `self.prisoners` depois dos servos, só com `modo == "guiar"`, livres, em `_refens_no_mapa()`, sem estar em `prisioneiros_done`. `handle_end_turn` chama `_mover_refens_seguindo(pid)` uma vez, ao abrir, antes de decidir a janela; a janela abre se restar guiado. `_mover_refens_seguindo`: ordena do mais perto ao mais longe; `_preparar_refem_turno`; BFS em 8 direções por `_tile_livre_para_animado(x, y, pr["id"], origem)` até uma casa a Chebyshev 1 do herói; anda por `_passo_refem` até faltar movimento e emite `entity_step` com `kind:"prisoner"` e o id. `_refem_chegou` roda após cada passo, nos dois modos, e só age com `faixas` no objetivo: adjacente ao destino marca `salvo`, zera `pos` para `[-1, -1]`, narra e chama `_check_objectives`. `_destino_resgate` lê `primary["destino"]` (`saida`→`exit_pos`, `entrada`→`stairs_pos`). `"prisoner"` em `encerrar_animado` segue como alias.
- [ ] **Step 4:** a suíte nova, `test_atravessar_aliados.py`, `test_janela_servos_bloqueia_mago.py`, `test_tutorial_refem.py`, `test_solo_grupo.py`. Expected: passam.
- [ ] **Step 5: Commit** `feat(reféns): libertar por refém, modos guiar e seguir, chegada`.

### Task 4: Resgate por faixas

**Files:**
- Modify: `server.py` (`_objetivo_cumprido` ~56627, `_check_objectives` ~56835, `handle_encerrar_missao` ~56892, `_prisioneiro_morre` ~57151, validador, payload)
- Test: `tools/test_varios_refens.py`

**Interfaces:**
- Consumes: Tasks 1 a 3.
- Produces: no objetivo principal `{"type":"rescue_prisoner","destino":"saida"|"entrada","meta":int,"faixas":[{"de":int,"ate":int,"xp":int,"gold":int,"renome":int,"fato":str}]}`. `_resgate_faixas() -> list|None`; `_resgate_contagem() -> dict {salvos, mortos, total, meta, destino}`; `_faixa_atual() -> dict`; `_pagar_faixa_resgate() -> None` (async); `self._secundarios_pagos: set[int]` (categoria `foto`). `game_state.resgate` = contagem ou `None`.

- [ ] **Step 1: Testes falhando:**

```python
def test_faixas_pagam_o_valor_certo(self):      # subTest salvos 0..6: xp, ouro, renome e fato da tabela do spec, no Encerrar
def test_botao_na_meta(self):                   # 3 salvas: sem pending; 4: pending; o pagamento ainda não aconteceu
def test_quinta_depois_da_meta_conta(self):     # meta atingida, salva a 6ª, encerra: paga a faixa de 6
def test_sem_vivos_no_mapa_abre_encerrar(self): # 2 salvas e 4 mortas: pending, faixa de 2
def test_morte_nao_falha_o_resgate(self):       # rescue_failed False, se_falhar não roda
def test_secundario_depois_da_meta(self):       # Ferrão morto após a meta: paga na hora, com baú antes de encerrar
def test_renome_negativo_tem_piso_zero(self):
def test_validador_de_faixas(self):             # buraco, sobreposição, meta > total, destino sem exit, 2 reféns sem faixas: recusados
def test_foto_com_salvos(self):                 # salva e retoma: contagem igual e nada pago duas vezes
```

- [ ] **Step 2:** rodar. Expected: FAIL.
- [ ] **Step 3: Implementar.** Com faixas, `_objetivo_cumprido` de `rescue_prisoner` é `salvos >= meta or not _refens_no_mapa()`, e `_check_objectives` liga `_objetivo_concluido`/`mission_complete_pending` sem conceder. Secundários: em modo faixas, cada `_check_objectives` paga o secundário recém-cumprido por `_conceder_objetivo_reward` e o marca em `_secundarios_pagos`, largando o baú como hoje (**ajuste do spec:** pagar no Encerrar perderia o item do baú, que nasce no mapa que está fechando). `handle_encerrar_missao` chama `_pagar_faixa_resgate` logo após as guardas, montando `{"xp","reward":{"gold","items":[]},"renome","fato"}` para `_conceder_objetivo_reward`. `_prisioneiro_morre(pr)` com faixas não mexe em `rescue_failed` nem em `se_falhar`.
- [ ] **Step 4:** a suíte nova, `test_refem_consequencia.py`, `test_objetivo_alternativo.py`, `test_objetivo_renome.py`, `test_elara_leonel_mansao.py`, `test_salvar_masmorra.py`. Expected: passam.
- [ ] **Step 5: Commit** `feat(reféns): recompensa por quantidade salva`.

### Task 5: Cliente com vários reféns

**Files:**
- Modify: `src/gameState.js` (~1107, ~2479–2535, ~3297–3309), `game.js` (2D ~12480, ~13195; 3D ~51551, ~52132, ~52278; chaves ~16545, ~17134, ~29240, ~48729; `getPrisonerMesh` ~50055; `_prisSel` ~19020; cliques ~57513; alvos ~20422; `_posicionarBotaoLibertar` ~6147)
- Test: `tools/test_varios_refens_cliente.js` (criar)

**Interfaces:**
- Consumes: Tasks 1 a 3.
- Produces: `GS.prisoners` (só os do mapa), `GS.prisoner` (primeiro), `GS.refensLibertaveis() -> array`, `GS.libertarPrisioneiro(refemId)`, `GS.moverPrisioneiro(dx, dy, refemId)`, `GS.moverPrisioneiroCaminho(path, refemId)`, `GS.ehRefemId(id) -> bool`. `_prisSel` guarda o id do refém ou `null`. `getPrisonerMesh(id)`. Chave de entidade `pr:<id>`.

- [ ] **Step 1: Teste falhando** com o `gameState.js` real: `refensLibertaveis` devolve só cativos vivos adjacentes; `_occupiedSet` marca a casa de todos; `animadoSelecaoValida('refem_1')` vale na vez dele; `pecaControlada` devolve `{kind:'prisoner', id:'refem_1'}`; `game.js` sem `pr:singleton`.
- [ ] **Step 2:** `node tools/test_varios_refens_cliente.js`. Expected: FAIL.
- [ ] **Step 3: Implementar** o que está em Interfaces. No 3D, `obterFig('prisoner:'+id, …)`, um peão por refém. Com um cativo adjacente, `#btn-libertar` chama direto; com mais de um, abre `openTargetModal` com os nomes. `GS.prisoners` filtra `salvo`, e assim o peão some sozinho.
- [ ] **Step 4:** a suíte nova, `test_refem_caminho_cliente.js`, `test_fila_animados_cliente.js`, `test_janela_servos_clique.js`, `test_interface.py`. Expected: passam.
- [ ] **Step 5: Commit** `feat(reféns): cliente desenha e controla vários reféns`.

### Task 6: Modo no HUD e contador

**Files:**
- Modify: `src/gameState.js`, `game.js` (`renderMyPanel`, `_objRow`/`renderObjectivesHUD`), `src/lang/interface.js`
- Test: `tools/test_varios_refens_cliente.js`

**Interfaces:**
- Consumes: Tasks 3 a 5.
- Produces: `GS.setModoRefem(refemId, modo)`, `GS.refensMeus() -> array`, `GS.resgate -> object|null`.

- [ ] **Step 1: Teste falhando:** `refensMeus` só lista os do `myPid` em foco; `setModoRefem` envia `set_modo_refem`; o texto do contador com `{salvos:3,total:6,meta:4,mortos:1}` sai "3/6 salvas, meta 4" e leva os mortos.
- [ ] **Step 2:** rodar. Expected: FAIL.
- [ ] **Step 3: Implementar** em `renderMyPanel` uma seção "Reféns", com nome, PV e um botão Guiar/Seguir por refém, e a linha de contagem no HUD de objetivos. Chaves `ui.refem.*`.
- [ ] **Step 4:** a suíte nova, `test_interface.py`, `python -X utf8 tools/dividas.py`. Expected: passam, sem dívida nova.
- [ ] **Step 5: Commit** `feat(reféns): modo no painel e contagem no HUD`.

### Task 7: Editor

**Files:**
- Modify: `tools/editor.js` (`S.prisoner` em ~455, 1175, 1223, 2405–2598, 4050, 4543–4686, 5093, 5264, 5561; painel do objetivo ~3290), `src/lang/editor.js`
- Test: `tools/test_varios_refens_editor.js` (criar), `tools/test_editor_idioma.py`

**Interfaces:**
- Consumes: formato do mapa das Tasks 1 e 4.
- Produces: `S.prisoners: array`. `buildJSON` grava `prisoner` com um refém e `prisoners` com dois ou mais, sem chave vazia nova.

- [ ] **Step 1: Teste falhando:** colocar 3 mantém 3; o 13º é recusado; apagar remove só o da casa; ida e volta conserva nome, imagem, modelo, `destino`, `meta` e `faixas`; mapa de um refém volta idêntico; validação acusa meta > total e buraco nas faixas.
- [ ] **Step 2:** `node tools/test_varios_refens_editor.js`. Expected: FAIL.
- [ ] **Step 3: Implementar.** Painel do refém com campo Nome. Painel do objetivo `rescue_prisoner` com destino, meta e tabela de faixas (`de`, `até`, `XP`, `ouro`, `renome`, `fato`, adicionar e remover). Copiar/colar e mover por seleção tratam a lista como `monsters`.
- [ ] **Step 4:** a suíte nova, `test_editor_idioma.py`, `test_editor_objetivo.js`, `test_decor_roundtrip.py`. Expected: passam.
- [ ] **Step 5: Commit** `feat(editor): vários reféns e faixas de resgate`.

### Task 8: As 6 crianças dos Charcos

**Files:**
- Create: `tools/aplicar_charcos_seis_criancas.py` (idempotente, só altera o combinado)
- Modify: `dungeons/charcos_4b_aldeia.json`, `tools/charcos_mapas.py`, `tools/gerar_campanha_charcos.py`, `world_adventures.json`, `city_scenes.json`, `tools/editor_dungeons.js` (regenerado)
- Test: `tools/test_campanha_charcos.py`, `test_campanha_charcos_mapas.py`, `test_charcos_fluxo.py`

**Interfaces:**
- Consumes: Tasks 1 a 4.
- Produces: fatos `charcos_criancas_todas`, `charcos_criancas_salvas`, `charcos_criancas_perdidas`, e `charcos_criancas_mortas` só com 0 salvas.

- [ ] **Step 1: Testes falhando:**

```python
def test_seis_criancas_na_cela(self):      # 6 em prisoners, todas na sala 2 (x42..52, y12..23), em casa livre, nomes e artes do spec
def test_tabela_da_aldeia(self):           # faixas iguais à tabela do spec; meta 4; destino "saida"; sem "alternativo"
def test_rota_sem_renome_proprio(self):    # charcos_mare.renome_recompensa == 0
def test_ferrao_continua_opcional(self):   # secundário kill_target com a recompensa de hoje
def test_vila_hostil_so_com_zero(self):    # 3 salvas sem charcos_criancas_mortas; preço +50% só com ele
def test_final_por_faixa(self):            # subTest pelos fatos: slide certo, e o amargo só com zero
def test_luto_na_taverna(self):            # conversa aparece com charcos_criancas_perdidas
```

- [ ] **Step 2:** rodar. Expected: FAIL.
- [ ] **Step 3: Implementar.** O script troca `prisoner` por `prisoners` com as 6 crianças: `Tico/garoto_loiro`, `Bento/garoto_medieval`, `Davi/garoto_pele_escura`, `Lina/menina_cabelos_castanhos`, `Maia/menina_pele_escura`, `Rosa/menina_ruiva` (só `image`), com `image` `<arte>.png` e `model3d` `<arte>.glb`, em casas livres da sala 2. Tabela do spec no primário, que perde `se_falhar`; remove `alternativo`. No gerador: `renome_recompensa` 0, slides de fim e a conversa de luto. Regenere `editor_dungeons.js` e atualize a assinatura sem tocar no resto do mapa.
- [ ] **Step 4:** as três suítes, `test_charcos_cadeia.py`, `test_preco_por_fato.py`, `test_zumbra_charcos.py`. Expected: passam.
- [ ] **Step 5: Commit** `feat(charcos): seis crianças e final por quantidade salva`.

### Task 9: Prova no jogo real e documentação

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1:** reiniciar o servidor. No navegador, com a mesa de teste ou um jogo Solo com grupo na Aldeia, em 2D e 3D, conferir: seis peões distintos, libertar com dois adjacentes, Guiar e Seguir, chegada que some, contador, Encerrar na meta, faixa paga, Salvar e sair com continuação no meio. Console sem erro.
- [ ] **Step 2:** rodar toda a bateria (`tools/test_*.py` e `tools/test_*.js`, conferindo o texto de falha, não só o código de saída). Expected: nenhuma falha nova.
- [ ] **Step 3:** seção em `CLAUDE.md`, atualizando no protocolo `libertar_prisioneiro`, `mover_prisioneiro` e `set_modo_refem`, e a campanha dos Charcos.
- [ ] **Step 4: Commit** `docs: vários reféns e resgate por faixas`.
