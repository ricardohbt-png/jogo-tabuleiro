# Campanha "A Maré do Charco" — Plano de implementação

> **Para quem for executar:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recomendado)
> ou superpowers:executing-plans. Os passos usam caixas (`- [ ]`) para acompanhar o andamento.

**Objetivo:** entregar a campanha da Vila dos Charcos (4 destinos, 5 masmorras) e o motor novo que
ela pede: renome/marcador em objetivos, consequência da morte do refém, conclusão alternativa
pelo Ferrão, requisito "sem marcador" e preço por marcador nas lojas da cidade.

**Arquitetura:** o motor ganha cinco peças pequenas e testadas em `server.py` (objetivo com
`renome`/`fato`; `se_falhar`; `alternativo`; `sem_fato`; modificador de preço da cidade). O conteúdo
sai de um gerador reexecutável, `tools/gerar_campanha_charcos.py`, no molde de
`tools/gerar_campanha_sombras.py` (reusa suas ferramentas `Mapa`, `monstro`, `decor`, `fala`,
`masmorra`, `nd_por_sala`, `faixa`, `salas_alcancaveis`).

**Tecnologia:** Python 3 (servidor, gerador, testes `unittest`/scripts de `tools/test_*.py`), JS
vanilla (`tools/editor*.js`, node para os testes de editor).

**Spec:** `docs/superpowers/specs/2026-10-17-campanha-mare-do-charco-design.md`

## Restrições globais

- Rodar tudo da raiz do projeto: `python -X utf8 tools/<teste>.py` e `node tools/<teste>.js`.
- `server.py`, `game.js` e `CLAUDE.md` estão em **CRLF** no diretório de trabalho: edite com a
  ferramenta de edição, ou com script Python que normalize `\r\n`→`\n` e restaure ao gravar.
- **Nunca** rodar `tools/gerar_campanha_sombras.py` sem `--simular` (regrava arquivos); o novo gerador
  só toca em `charcos_*` (masmorras, destinos, conversas, item `ferrao_do_brejo`, modificadores).
- Todo texto de interface novo em editor usa `t("ui.editor....")` (chaves em `src/lang/editor.js`,
  pt + en); texto novo de servidor usa `T("chave")` com pt + en em `src/lang/*.js`
  (`tools/dividas.py` e `test_idioma.py` ficam limpos). Conteúdo autoral da campanha (slides,
  falas, conversas, nomes de masmorra) fica em português, como na campanha anterior.
- Campo novo de sala guardado na foto entra em `FOTO_SALA_CATEGORIAS` (`test_salvar_masmorra` [2]).
- Salvar o editor não pode apagar campo novo: todo campo novo de objetivo/requisito/slide precisa
  sobreviver ao `buildJSON`/`loadJSON` dos editores (teste node onde houver lógica pura).
- Falhas que já existiam e **não** são desta entrega: `test_vocabulario`, `test_idioma_cliente`,
  `test_editor_idioma` (1), `test_campanha_sombras`, `test_masmorra_sequenciada`, `test_interface`,
  `test_salvar_masmorra` (2), `test_simulador_turno` (4), `test_tutorial_resistencia` (2),
  `test_tutorial_fatia8` (4), `test_tutorial_hostilidade` (2), `test_tutorial_fatia20` (pipeline).
- Cada tarefa termina com um commit; mensagens terminam com
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Revisão: o que os testes das tarefas não cobrem sozinhos

Cada linha vira um teste na tarefa dona (indicada entre parênteses).

1. O refém morre **depois** de o Ferrão já ter morrido, **antes** de ser libertado, ou com o grupo
   inteiro fora da masmorra pela escada: a missão ainda precisa fechar ou deixar sair (Tarefa 4).
2. A consequência da morte aplicada **duas vezes** (retomar jogo salvo, foto, `push_state` repetido)
   (Tarefa 3).
3. Preço da vila: o que aparece é o que se cobra, a venda **não** sobe, outra cidade e o mercador de
   outra cidade não mudam, e tirar o marcador volta ao normal (Tarefa 5).
4. O Ferrão preso por parede não ataca; solto, ataca monstros **da mesma sala** e os bruxos revidam
   (Tarefa 6d).
5. Impasse: chave só com o necromante-chefe (cai no saque se ele morrer), alavanca acessível, fuga
   sempre possível, nova tentativa restaura a etapa (Tarefa 6d/6f).

---

## Pré-requisito: trabalho não commitado

O plano assume no repositório (e commitado) o que já foi feito nesta sessão e ainda está só no
diretório de trabalho: slides de história condicionais (`_story_beat(..., avaliar)`, `requisito` e
`negar` por slide, painel do editor de história), preço/descrição do Anel da Garra Negra, banquete
nas tavernas, remoção do Dente da fera (cópia) e da Maçã de Treino. **Pergunte ao usuário** se pode
commitá-los (e o que vai para o master) antes da Tarefa 1; o diretório também tem trabalho
em andamento de outra frente (machadinha, piche) que **não** deve entrar nesses commits — separe por
arquivo ou por hunk (`git add -p`) e confira `git status` antes de cada `git add`.

---

### Tarefa 1: requisito negado `sem_fato`

**Arquivos:**
- Modificar: `server.py` (`_clean_requirement` perto da linha 656; `GameRoom._avaliar_requisito`)
- Modificar: `src/lang/erros.js` (chave `erro.requisito.sem_informacao`, pt + en)
- Modificar: `tools/editor_world.js` (linhas ~42, 72, 88 reconstroem o `requisito` campo a campo),
  `tools/editor_story.js` (objeto padrão de `requisito`), `tools/editor_city.js` (conversa)
- Criar: `tools/test_requisito_sem_fato.py`, `tools/test_requisito_sem_fato.js`

**Interfaces:**
- Produz: `_clean_requirement(raw)` devolve também `"sem_fato": str` (≤100); `_avaliar_requisito(raw)
  -> (bool, [T])` falha com o motivo `T("erro.requisito.sem_informacao", fato=...)` quando o marcador
  existe em `self.fatos`.
- Consome: nada de tarefas anteriores.

- [ ] **Passo 1: teste que falha** — `tools/test_requisito_sem_fato.py`:
  `test_clean_requirement_conserva_sem_fato` (`_clean_requirement({"sem_fato":" x "})["sem_fato"] == "x"`),
  `test_avalia_negado` (sala com `fatos={"a"}`: `{"sem_fato":"a"}` → `False` com um motivo;
  `{"sem_fato":"b"}` → `True`), `test_combina_com_outros_campos` (`fato:"a"` e `sem_fato:"b"` juntos),
  `test_conversa_e_destino_usam_o_mesmo_requisito` (`_clean_scene_conversations` mantém `sem_fato`).
  Em node: `tools/test_requisito_sem_fato.js` carrega `editor_world.js`/`editor_story.js` e confere que
  o roundtrip de um destino com `requisito.sem_fato` não o perde.
- [ ] **Passo 2:** rodar os dois — Esperado: FALHAM (chave ausente).
- [ ] **Passo 3:** implementar `sem_fato` em `_clean_requirement`/`_avaliar_requisito` (uma linha em
  cada; o motivo é `T`, nunca texto cru) e a chave de idioma; fazer os três editores conservarem o
  campo (acrescentar `sem_fato:""` nos objetos padrão e no ramo que reconstrói o requisito).
- [ ] **Passo 4:** rodar — Esperado: PASSAM. Rodar também `test_cidades_editor`, `test_idioma`,
  `test_erros`, `test_masmorra_sequenciada` [18] (destino oculto) para provar que nada mudou.
- [ ] **Passo 5: commit** — `feat: requisito sem_fato (marcador que NÃO existe)`

### Tarefa 2: objetivo com `renome` e `fato`, e validação dos campos novos de objetivo

**Arquivos:**
- Modificar: `server.py` (`_conceder_objetivo_reward` ~linha 49279; `validar_dungeon` onde lê
  `defn["objectives"]` ~linha 8219)
- Modificar: `tools/editor.js` (`objDefaults`/`normalizeObjective`/`rewardFieldsHTML`/
  `wireRewardFields` ~linhas 2430–2457; `buildJSON` ~4372; `loadJSON` ~4954)
- Modificar: `src/lang/editor.js` (`ui.editor.masmorra.recompensa.renome` e `.fato`), `src/lang/narracao.js`
  (`narracao.obj_renome`)
- Criar: `tools/test_objetivo_renome.py`, `tools/test_editor_objetivo.js`

**Interfaces:**
- Consome: nada.
- Produz: um objetivo (`primary`, `secondary[i]`, e os novos `alternativo`/`se_falhar`) aceita
  `renome` (inteiro −9999..9999) e `fato` (str ≤100). `validar_dungeon` recusa tipo errado.
  `await self._conceder_objetivo_reward(obj, is_primary, loot_acc)` soma `renome` com piso zero no total
  do grupo, grava `fato` em `self.fatos` e narra os ganhos/perdas.

- [ ] **Passo 1: teste que falha** — `test_objetivo_renome.py`: `test_concede_renome_e_fato`
  (renome 3 + `{"renome":2}` → 5; `fato` em `self.fatos`), `test_renome_negativo_tem_piso_zero`
  (renome 2, objetivo −5 → 0), `test_sem_campos_nao_muda_nada` (objetivo antigo igual a antes),
  `test_validar_dungeon_recusa_renome_nao_inteiro_e_fato_nao_texto`. Em node,
  `test_editor_objetivo.js`: `normalizeObjective`/`buildJSON` conservam `renome`, `fato`, `se_falhar`,
  `alternativo`.
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar em `_conceder_objetivo_reward` (somar `self.renome`, `self.fatos.add`,
  `T("narracao.obj_renome", n=...)`); validar os campos em `validar_dungeon` para `primary`,
  `secondary[]`, `alternativo` e `se_falhar`; no editor, inputs de renome/fato nos objetivos e
  preservar os quatro campos novos em `buildJSON`/`loadJSON` (hoje o `buildJSON` reconstrói só
  `type/xp/reward`).
- [ ] **Passo 4:** rodar — Esperado: PASSAM, mais `test_modo_mestre` (23), `test_editor_idioma`
  (nenhuma regressão além da falha antiga), `test_idioma`.
- [ ] **Passo 5: commit** — `feat: objetivo concede renome e marcador`

### Tarefa 3: consequência da morte do refém (`se_falhar`)

**Arquivos:**
- Modificar: `server.py` (`_prisioneiro_morre` ~linha 49821; reset de `rescue_failed` nas linhas ~11597,
  ~16213, ~17370; `FOTO_SALA_CATEGORIAS` ~linha 3550)
- Modificar: `src/lang/narracao.js` (`narracao.refem_morto_consequencia`)
- Criar: `tools/test_refem_consequencia.py`

**Interfaces:**
- Consome: os campos validados na Tarefa 2. `objectives.primary.se_falhar = {"renome": -5, "fato": "..."}`
  — `renome` é um **delta com sinal** (negativo = perda), como o `renome` dos objetivos.
- Produz: `GameRoom._consequencia_refem_aplicada: bool` (categoria `foto`);
  `async def _aplicar_consequencia_refem(self) -> None` chamada no fim de `_prisioneiro_morre`;
  idempotente.

- [ ] **Passo 1: teste que falha** — `test_refem_consequencia.py`: `test_morte_aplica_renome_e_fato_uma_vez`
  (chamar `_prisioneiro_morre` duas vezes: renome cai uma vez, fato gravado), `test_piso_zero`,
  `test_nao_encerra_a_missao` (`phase == "playing"`, `world_adventure_id` mantido, nenhuma troca de
  tela), `test_sem_se_falhar_nada_muda` (masmorras antigas), `test_foto_inclui_o_campo`
  (`foto_campos_sala("foto")` traz `_consequencia_refem_aplicada`), `test_nova_tentativa_reseta`
  (recarregar a masmorra volta o campo para `False`, o refém volta vivo e o renome perdido **não**
  volta).
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar. A função só altera estado e narra (`gm_say`); nada de trocar de
  tela nem de `await` longo, porque roda no meio do turno dos monstros.
- [ ] **Passo 4:** rodar — Esperado: PASSAM, mais `test_salvar_masmorra` [2] sem falhas novas,
  `test_resgate*`/`test_prisioneiro*` existentes.
- [ ] **Passo 5: commit** — `feat: consequência imediata da morte do refém (renome e marcador)`

### Tarefa 4: conclusão alternativa (`alternativo`)

**Arquivos:**
- Modificar: `server.py` (`_check_objectives` ~49515, `_objetivo_payload` ~49376, `handle_encerrar_missao`
  ~49580, o ramo `reward = ...renome_recompensa` ~49627)
- Modificar: `game.js` (HUD de objetivos: mostrar o `alternativo` quando o principal está falhado)
  e `src/lang/interface.js` (rótulo `ui.objetivo.alternativo`)
- Criar: `tools/test_objetivo_alternativo.py`

**Interfaces:**
- Consome: `rescue_failed`, `objectives.alternativo` (campos validados na Tarefa 2).
- Produz: `GameRoom._objetivo_principal_efetivo(self) -> dict | None` (o `alternativo` quando
  `rescue_failed` e ele existe; senão o principal); `objective_status["alternativo"]` no estado
  quando definido; no caminho alternativo **não** se pagam secundários do mesmo `type` do
  alternativo e **não** se paga `renome_recompensa` da rota (final amargo).

- [ ] **Passo 1: teste que falha** — `test_objetivo_alternativo.py` (sala com `kill_target` no
  Ferrão): `test_sem_falha_usa_o_principal`, `test_falha_ativa_o_alternativo` (principal
  `failed`, alternativo `pending`), `test_matar_o_alvo_habilita_encerrar_missao_com_xp_reduzido`,
  `test_nao_paga_o_bonus_secundario_em_dobro`, `test_nao_paga_renome_da_rota_no_final_amargo`,
  `test_refem_morre_com_o_alvo_ja_morto_conclui_na_hora`, `test_fugir_pela_escada_nao_conclui`
  (rota sem progresso, consequência mantida), `test_slides_do_final_pelo_marcador`
  (`charcos_criancas_mortas` + `sem_fato`), `test_grupo_todo_fora_nao_trava`.
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar `_objetivo_principal_efetivo` e usá-lo nos pontos de `_check_objectives`
  (conclusão, recompensas, `mission_complete_pending`); acrescentar a linha do alternativo no payload e
  no HUD do cliente; em `handle_encerrar_missao`, pular `renome_recompensa` quando `self.rescue_failed`.
- [ ] **Passo 4:** rodar — Esperado: PASSAM, mais `test_modo_mestre`, `test_aventura_retomada` (15),
  `test_final_condicional`, testes de objetivos existentes (`test_objetivos*`, `test_resgate*`).
- [ ] **Passo 5: commit** — `feat: objetivo alternativo quando o resgate falha`

### Tarefa 5: preço da cidade por marcador

**Arquivos:**
- Modificar: `server.py` (carregador novo ao lado de `_load_city_shops` ~linha 9770; `_city_shop_items`
  ~9789; `_city_state_payload` ~13027–13032; `handle_shop_buy` ~15608–15619 e as 14 ocorrências de
  `buy_price` dentro dele; `handle_shop_sell` não muda)
- Criar: `cidade_modificadores.json` (vazio `{}`), `tools/test_preco_por_fato.py`

**Interfaces:**
- Produz: `CITY_PRICE_MODS: dict[str, list[{"fato": str, "preco_mult": float}]]` carregado de
  `cidade_modificadores.json` (cidade inexistente ou multiplicador fora de 0,1–5 é descartado);
  `_city_price_mult(city_id, fatos) -> float` (produto dos modificadores cujo `fato` está em
  `fatos`); `GameRoom._itens_da_loja(shop_id) -> list[dict]` (cópias com `price` ajustado,
  arredondado, e `preco_base` com o original). A venda continua baseada no preço **base**:
  `buy_price` guarda `preco_base`.

- [ ] **Passo 1: teste que falha** — `test_preco_por_fato.py`: `test_sem_marcador_preco_normal`,
  `test_com_marcador_o_payload_ja_traz_o_preco_novo` (taverna e ferreiro de `vila_dos_charcos`),
  `test_compra_cobra_o_preco_mostrado`, `test_venda_nao_sobe` (comprar com marcador e vender em
  seguida rende `preco_base // 3`), `test_outra_cidade_nao_muda`, `test_tirar_o_marcador_volta`,
  `test_arquivo_invalido_nao_derruba_o_boot` (JSON quebrado/campo errado ignorado),
  `test_mercador_e_pergaminhos_tambem_seguem_a_regra`.
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar o carregador, `_city_price_mult`, `_itens_da_loja`; trocar as chamadas
  de `_city_shop_items(self.world_location, ...)` nas 12 chamadas (6 no estado da cidade, 6 no `handle_shop_buy`) por `self._itens_da_loja(...)`;
  guardar `preco_base` nos itens ajustados e usá-lo nos `buy_price`.
- [ ] **Passo 4:** rodar — Esperado: PASSAM, mais `test_roteamento_itens`, `test_cidades_editor` (92),
  `test_editor_itens` (462), `test_banquete_viagem_na_taverna`, `test_ficha_cidade`.
- [ ] **Passo 5: commit** — `feat: preço das lojas da cidade por marcador`

---

## Conteúdo: o gerador da campanha

Reaproveitar do gerador antigo (importar, não copiar): `from gerar_campanha_sombras import Mapa, monstro,
decor, fala, masmorra, nd_por_sala, faixa, salas_alcancaveis, historia, _etapa, _ler_json, _gravar_json`.
Constantes novas: `FATO_GANCHO="charcos_criancas_sumidas"`, `FATO_MORTE="charcos_criancas_mortas"`,
`FATO_FERRAO="charcos_ferrao_morto"`, `ITEM_TROFEU="ferrao_do_brejo"`.

### Tarefa 6a: esqueleto do gerador, destinos, história, conversas, modificador e item-troféu

**Arquivos:**
- Criar: `tools/gerar_campanha_charcos.py`, `tools/test_campanha_charcos.py`
- Gera/atualiza (só entradas `charcos_*`): `world_adventures.json`, `city_scenes.json`
  (`vila_dos_charcos/taverna`), `itens_personalizados.json` (+ espelho `tools/editor_items_custom.js`),
  `cidade_modificadores.json`, `dungeons/charcos_*.json`

**Interfaces:**
- Consome: Tarefas 1–5 (requisito `sem_fato`, objetivo com `renome`/`fato`/`se_falhar`/`alternativo`,
  modificador de preço).
- Produz: `destinos() -> dict` (4 destinos: `charcos_bordas`, `charcos_palafitas`,
  `charcos_travessia`, `charcos_aldeia`; o último com 2 etapas, a primeira `encadear=True`;
  `oculto_ate_liberar`; requisitos em cadeia: gancho por `fato`, depois `aventura_id` do anterior);
  `conversas_taverna() -> dict[slot_id, list[conversa]]`; `modificadores() -> dict`; `trofeu_bruto()
  -> dict`; `preparar()`, `aplicar(artefatos, caminhos=None, forcar=False)`, `relatorio()`, `main()`
  (modos `--simular`, `--forcar`, como o gerador antigo); `ARQUIVOS` com os 5 nomes.

- [ ] **Passo 1: teste que falha** — `test_campanha_charcos.py`: `test_ids_e_cadeia_de_requisitos`,
  `test_destinos_ocultos_ate_liberar`, `test_ultimo_destino_tem_duas_etapas_emendadas`,
  `test_conversa_do_gancho_so_antes_da_tragedia` (`sem_fato: FATO_MORTE`, `efeito.fato = FATO_GANCHO`),
  `test_conversas_hostis_exigem_o_marcador_da_morte`, `test_conversa_calorosa_so_sem_tragedia_e_com_rota`,
  `test_modificador_da_vila_so_para_o_marcador_da_morte` (1,5), `test_trofeu_valida_como_item_custom`,
  `test_final_tem_slides_condicionais_por_marcador` (ferrão morto / crianças mortas / `sem_fato`),
  `test_aplicar_so_toca_em_charcos_e_e_idempotente` (rodar duas vezes em diretório temporário, outras
  entradas intactas), `test_conflito_se_masmorra_foi_editada` (`Conflito` sem `--forcar`).
- [ ] **Passo 2:** rodar — Esperado: FALHAM (módulo inexistente).
- [ ] **Passo 3:** implementar os artefatos acima. As masmorras ficam, por ora, como funções que
  levantam `NotImplementedError` (cada uma é a tarefa seguinte); o resto do gerador roda com um
  parâmetro `so_dados=True`.
  **Texto (autoral, pt):** gancho e descrição dos NPCs da taverna (a mãe Ysa e dois frequentadores:
  um pescador e um velho), três finais (fuga, vitória e final amargo), fala de fracasso, falas das
  masmorras. A mãe é o NPC do slot `npc_ms42peq8`; os outros dois, `npc_ms42qx5t` e `npc_ms42snq6`
  (renomear os slots; hoje são "Novo NPC" sem conversa).
  **Troféu `ferrao_do_brejo`:** arma de uma mão perfurante, acuidade, 1d6, +1 de acerto, sem
  classe restrita, preço 400, `disponibilidade` só de baú; entra como recompensa do objetivo
  secundário da Tarefa 6d.
- [ ] **Passo 4:** rodar `test_campanha_charcos.py` — Esperado: PASSA (parte de dados).
- [ ] **Passo 5: commit** — `feat: gerador da campanha Maré do Charco — dados, história e conversas`

### Tarefa 6b: masmorras 1 e 2 — Bordas da Mata e Palafitas

**Arquivos:** `tools/gerar_campanha_charcos.py` (funções `masmorra_bordas`, `masmorra_palafitas`),
`tools/test_campanha_charcos.py`

**Interfaces:** `masmorra_bordas() -> dict` e `masmorra_palafitas() -> dict`, ambas passando em
`S.validar_dungeon`; usam `masmorra(...)` com `ambiente="ar_livre"` e `expected_party` nível 2.

- [ ] **Passo 1: testes que falham** — `test_bordas_valida_e_alcancavel` (`validar_dungeon`,
  `salas_alcancaveis` = todas as salas), `test_bordas_tem_os_inimigos_pedidos` (lobos + um Lobo Alfa
  como `target`, ratos e ratos gigantes, aranha sombria, escorpião de pedra, escorpião pequeno, cobra
  venenosa), `test_bordas_nd_por_sala_dentro_da_faixa` (nenhuma sala `mortal` para poder 2×4=8 de
  heróis nível 2; `faixa(nd, poder)`), `test_bordas_pistas` (decor `sapatinho` ou carta, ossos),
  `test_palafitas_inimigos` (crocodilo jovem, jacaré como alvo secundário, cobra constritora e venenosa,
  devorador orgânico, escorpiões), `test_palafitas_tem_agua_pontes_e_chao_ilusorio` (material `agua`,
  pelo menos uma `ponte` e uma armadilha `chao_illusorio` ligada a ela), `test_palafitas_deposito_com_
  oleo_e_piche_e_carta` (baú com 2 `frasco_oleo`, 2 `frasco_piche` e uma `carta` com `texto`),
  `test_objetivos` (primário `all_heroes_at_exit`/`reach_exit`; secundário `kill_target` quando há alvo).
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar os dois mapas com `Mapa` (grade ~40×28 cada; floresta com `grama`,
  árvores, `capim_alto`, `moita_espinhosa`, `tronco_musgo`; palafitas com `agua`/`agua_profunda`,
  `pontes`, `cabana_rustica`, `tocos_alagados`, `juncos`, `monte_ossos`). Calibrar com `--simular`.
- [ ] **Passo 4:** rodar — Esperado: PASSAM; `python tools/gerar_campanha_charcos.py --simular` mostra
  ND por sala e artes pedidas.
- [ ] **Passo 5: commit** — `feat: masmorras Bordas da Mata e Palafitas dos Pescadores`

### Tarefa 6c: masmorras 3 e 4A — Travessia do Pântano e Arredores da Aldeia

**Arquivos:** `tools/gerar_campanha_charcos.py` (`masmorra_travessia`, `masmorra_arredores`),
`tools/test_campanha_charcos.py`

**Interfaces:** `masmorra_travessia()`, `masmorra_arredores()` → `dict` válidos; a travessia termina
com a saída à vista da aldeia; os arredores terminam no portão (saída, etapa emendada).

- [ ] **Passo 1: testes que falham** — `test_travessia_pantano_e_agua` (material `pantano` em
  grande parte do chão, `agua` e `agua_profunda`), `test_travessia_inimigos` (crocodilo jovem, cobras,
  ratos gigantes, escorpiões, 2 zumbis infectados), `test_arredores_inimigos` (esqueletos humanos e
  animais, 1 xamã goblin, zumbis), `test_arredores_paliçada_e_portao` (decor `cerca_reta`/`porteira_*`
  e uma `saida` no portão), `test_nd_dentro_da_faixa_nivel_3`, `test_alcancavel`.
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar e calibrar com `--simular`.
- [ ] **Passo 4:** rodar — Esperado: PASSAM.
- [ ] **Passo 5: commit** — `feat: masmorras Travessia do Pântano e Arredores da Aldeia`

### Tarefa 6d: masmorra 4B — A Aldeia (cercado, chave, alavanca e o Ferrão)

**Arquivos:** `tools/gerar_campanha_charcos.py` (`masmorra_aldeia`), `tools/test_campanha_charcos.py`,
`tools/test_charcos_fluxo.py` (novo, motor real)

**Interfaces:** `masmorra_aldeia() -> dict` com: sala "praça" (uma só `room_id`) contendo os
bruxos **e** uma cela murada com o Ferrão adulto (`ferrao_charcos_adulto`, `target: True`,
`hostility_override` todos os monstros); passagem secreta de uma casa de parede da cela com
`key_decor_ids=[<alavanca>]`; o cercado (decor `grades_prisao`/`gaiola` + porta `door_conditions`
do tipo `decor` ligada à `Chave do Cercado`, ou baú-chave com a chave com o necromante-chefe);
`prisoner` = "As Crianças" (`room_id` do cercado); objetivos:
`primary = {"type":"rescue_prisoner","xp":150,"reward":{"gold":60},"se_falhar":{"renome":-5,
"fato":FATO_MORTE}}`, `secondary=[{"type":"kill_target","xp":600,"renome":3,"fato":FATO_FERRAO,
"reward":{"gold":250,"items":[{"id":"ferrao_do_brejo"}]}}]`, `alternativo={"type":"kill_target",
"xp":150,"reward":{"gold":0,"items":[]},"fato":FATO_FERRAO}`; bruxos com `hostility_override`
só contra `ferrao_charcos_adulto`; poças de piche (material `piche`) e barris perto da cova e dos
totens; saída no portão; `saida_permitida` verdadeira.

- [ ] **Passo 1: testes que falham** — em `test_campanha_charcos.py`: `test_aldeia_valida`,
  `test_aldeia_ferrao_e_alvo_hostil_a_todos`, `test_bruxos_revidam_so_o_ferrao`,
  `test_cela_do_ferrao_na_mesma_sala_dos_bruxos`, `test_alavanca_abre_a_passagem_da_cela`,
  `test_chave_do_cercado_com_o_necromante_chefe_e_cai_no_saque`, `test_ha_piche_perto_da_cova`,
  `test_objetivos_e_recompensas` (os campos acima), `test_alcancavel_com_passagem_aberta`,
  `test_nd_sem_o_ferrao_dentro_da_faixa`. Em `test_charcos_fluxo.py` (motor real, com iniciativa
  e `push_state`): `test_cela_fechada_ferrao_nao_ataca`, `test_alavanca_solta_e_ele_ataca_monstros_da_
  mesma_sala` (hostilidade monstro×monstro), `test_bruxos_revidam`, `test_criancas_mortas_aplica_a_
  consequencia_e_a_missao_segue`, `test_matar_o_ferrao_com_criancas_vivas_paga_o_secundario`,
  `test_matar_com_criancas_mortas_so_xp_reduzido`, `test_fugir_pela_escada_com_criancas_mortas_nao_
  conclui`.
- [ ] **Passo 2:** rodar — Esperado: FALHAM.
- [ ] **Passo 3:** implementar o mapa (grade ~56×36), a lógica dos dados e a calibração; a cova do
  Ferrão usa a passagem secreta (casa de `WALL` que vira `FLOOR` ao ativar a alavanca).
- [ ] **Passo 4:** rodar — Esperado: PASSAM; `--simular` limpo (todas as salas alcançáveis, ND coerente).
- [ ] **Passo 5: commit** — `feat: masmorra A Aldeia dos Bruxos e o Ferrão como arma`

### Tarefa 6e: calibração de nível, XP e dificuldade

**Arquivos:** `tools/gerar_campanha_charcos.py`, `tools/test_campanha_charcos.py`

**Interfaces:** `relatorio(artefatos) -> str` inclui ND por sala e a **soma de XP prevista por
masmorra** para um grupo de 4 (usando `XP_MONSTRO_POR_ND` e o modificador de nível do servidor).

- [ ] **Passo 1: teste que falha** — `test_xp_acumulado_leva_do_nivel_2_ao_4` (soma de XP de
  monstros + objetivos até o fim da campanha fica entre o custo de chegar ao nível 4 e o de chegar
  ao nível 5, com a regra `XP_POR_NIVEL`), `test_nenhuma_sala_mortal_exceto_a_cova`.
- [ ] **Passo 2:** rodar — Esperado: FALHA (relatório sem XP).
- [ ] **Passo 3:** implementar o cálculo no relatório e ajustar quantidades de monstros e XP dos
  objetivos até o teste passar; **registrar a tabela final no cabeçalho do gerador**.
- [ ] **Passo 4:** rodar — Esperado: PASSA.
- [ ] **Passo 5: commit** — `chore: calibra nível, XP e dificuldade da Maré do Charco`

### Tarefa 6f: integração ponta a ponta, gravação e documentação

**Arquivos:** `tools/test_charcos_fluxo.py`, `CLAUDE.md`, `dungeons/charcos_*.json`,
`world_adventures.json`, `city_scenes.json`, `cidade_modificadores.json`,
`itens_personalizados.json`, `tools/editor_items_custom.js`, `tools/editor_dungeons.js`

**Interfaces:** nenhuma nova; roda `python tools/gerar_campanha_charcos.py` de verdade (sem `--simular`).

- [ ] **Passo 1: testes que falham** — `test_charcos_fluxo.py`: `test_cadeia_de_destinos_pelo_motor_real`
  (gancho → bordas → palafitas → travessia → aldeia, cada um só aparece após o anterior, via
  `_aventura_visivel`), `test_final_fuga_vitoria_e_amargo` (quatro combinações dos marcadores
  produzem os slides certos, sem frases trocadas), `test_hostilidade_da_vila_sobe_os_precos_e_muda_as_
  conversas` (depois do marcador: conversa do gancho some, hostis aparecem, preços da taverna ×1,5),
  `test_retomar_jogo_salvo_nao_reaplica_a_consequencia`, `test_gerador_idempotente_no_repositorio`.
- [ ] **Passo 2:** rodar — Esperado: FALHAM até gravar os artefatos.
- [ ] **Passo 3:** rodar `python tools/gerar_campanha_charcos.py`; conferir `git status` (só `charcos_*`
  e os índices gerados); rodar `python tools/export_catalog.py` e `python tools/gerar_vocabulario.py`
  (nome do troféu); acrescentar o parágrafo da campanha e dos cinco motores novos ao `CLAUDE.md`
  (junto da campanha anterior); registrar na memória do projeto (um arquivo curto de projeto).
- [ ] **Passo 4:** rodar a bateria: todos os testes novos + `test_masmorra_sequenciada` [18]/[19],
  `test_cidades_editor`, `test_modo_mestre`, `test_idioma`, `test_erros`, `test_narracao`,
  `test_export_catalog`, `test_editor_itens`; conferir que as falhas são só as listadas nas restrições.
- [ ] **Passo 5: commit** — `feat: campanha A Maré do Charco (Vila dos Charcos)`

**Prova no navegador (depois do commit, antes de fechar):** servidor isolado em porta própria
(`LFH_PORT`), conferir a conversa do gancho, a entrada dos destinos e a Aldeia 2D/3D (cela, alavanca,
grades, piche), usando a prévia do editor (`?preview=1`) para a masmorra e uma sala de teste para o fluxo.
