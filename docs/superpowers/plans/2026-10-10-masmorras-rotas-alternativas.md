# Plano de implementação: rotas alternativas em masmorras reutilizadas

Spec: `docs/superpowers/specs/2026-10-10-masmorras-rotas-alternativas-design.md`

## Brief

Implementar o modo opcional de exploração por saídas para uma etapa do mapa-múndi. Uma etapa aponta para um único arquivo de masmorra; saídas marcadas registram descobertas sem teletransportar o grupo. A aventura só libera o botão atual de conclusão depois de cumprir o objetivo principal e todas as saídas obrigatórias. A escada atual continua sendo a saída individual para a cidade. O mapa e o estado de cada incursão parcial precisam sobreviver a retornar à cidade, abrir outro destino e voltar depois.

## Decisões e limites

- Manter `world_adventure_progress` como inteiro e sem mudança de significado para saves e aventuras lineares.
- Guardar `world_adventure_route_progress["<adventure_id>:<stage_index>"] = {found_exit_ids:[], visited_route_ids:[], objective_completed:false, rewarded_source_ids:[]}`; migração de save antigo não altera cursores lineares.
- Guardar snapshots de masmorras incompletas por aventura/etapa, mantendo o campo legado `dungeon_snapshot` compatível com saves antigos e com masmorras fora do modo novo.
- Modo de conclusão configurado dentro da etapa existente no editor do mapa-múndi; não duplicar uma referência de arquivo na sequência linear.
- O editor de masmorras terá rotas estáveis, saídas de descoberta, grupos de monstros por rota e política de retorno `reaparecer` ou `persistir derrotas`.
- Portas/passagens condicionais usarão `_clean_requirement` com `fato`, `item_id`, `aventura_id`, `renome_min` e `nivel_grupo_min` (campos preenchidos são AND). Histórico genérico de locais visitados fica fora desta entrega.
- Descobrir uma saída nunca desloca jogador. Usar a escada segue o fluxo atual de saída individual.
- A conclusão continua manual pelo botão existente; o servidor exige objetivo principal e saídas obrigatórias e impede recompensa/progresso duplicados.
- Monstros reaparecidos recuperam estado de combate, mas não dão XP/loot repetidos. Estado de loot já obtido permanece gravado.
- Os testes previstos cobrem schema, roundtrip dos dois editores, migração de saves, salvamento/restauração de snapshots, descoberta e conclusão idempotente, além do comportamento linear legado.

## Arquivos e interfaces principais

- `tools/editor.js`: estados, validação, importação e exportação da autoria de rotas/saídas/monstros.
- `server.py`: validação de masmorra; catálogo de saídas para o editor do mapa-múndi; sanitização de aventuras; progresso persistido; snapshots; carregamento de monstros; descoberta e condição de conclusão.
- `tools/editor_world.js`: campos da etapa, descoberta de saídas da masmorra selecionada, escolhas obrigatórias e roundtrip.
- `game.js` e traduções em `src/lang/interface.js`: mostrar objetivo/progresso das saídas e preservar UX linear quando o modo estiver desligado.
- Novos testes focados em `tools/test_*rotas*` sem alterar os dados das missões atuais.

## Tasks

### Task 1 — Schema autoral e edição da masmorra

1. Criar `tools/test_dungeon_routes.py` com `test_validar_rotas_e_saidas_validas`, `test_rejeita_ids_e_referencias_invalidas` e `test_masmorra_legada_sem_rotas_continua_valida`: aceitar schema válido; rejeitar IDs duplicados, coordenadas fora do mapa/em parede, rota inexistente e saída sem posição válida; aceitar arquivos antigos sem campos novos.
2. Adicionar estado `routes` e `route_exits` ao editor de masmorras. A rota guarda `{id, name, monster_policy}`; a saída guarda `{id, name, pos, route_id}`. Preservar dados no `loadJSON`, `buildJSON`, duplicação/remoção e validação antes do save.
3. Atribuir `route_id` e `source_id` estável a cada monstro autorado. Gerar ID quando o objeto antigo não tiver um e preservá-lo em edição/duplicação sem colisões.
4. Separar visualmente marcador de saída de rota da escada e de `exit_pos`; impedir colocação em parede, sobre spawn/escada/saída incompatível ou fora da grade.
5. Verificar: executar testes de schema/editor novos e salvar/reabrir um mapa antigo sem mutar campos que o editor já preserva.

### Task 2 — Modo de exploração no editor do mapa-múndi

1. Criar `tools/test_world_adventure_routes.py` com `test_etapa_linear_roundtrip`, `test_etapa_por_saidas_roundtrip` e `test_saida_obrigatoria_obsoleta_recusada`: preservar `file`, `encadear`, `intro`, `outro` e `scene_trigger`; manter modo e IDs ao salvar/reabrir; recusar IDs removidos.
2. Expor no payload do catálogo do servidor saídas válidas por arquivo de masmorra sem alterar o payload legado consumido por outras telas.
3. No `editor_world.js`, adicionar seletor de modo à etapa existente e lista de saídas obrigatórias do arquivo selecionado. Não permitir referência duplicada à mesma masmorra na sequência.
4. No upload, validar que cada ID obrigatório existe no arquivo atual e rejeitar com erro visível referências apagadas/obsoletas, em vez de descartá-las silenciosamente.
5. Verificar: testar roundtrip nos dois modos, arquivo trocado/removido e etapa linear legada.

### Task 3 — Save de campanha e snapshots por etapa

1. Acrescentar a `tools/test_world_adventure_routes.py` `test_migracao_snapshot_legado` e `test_snapshots_por_etapa_isolados`: save antigo com `dungeon_snapshot` e `world_adventure_progress` numérico carrega sem mudança; save novo carrega a coleção de exploração/snapshots e mantém snapshots de outras etapas.
2. Adicionar coleção de snapshot keyed por `adventure_id:stage_index`. Salvar a foto da masmorra incompleta sob essa chave ao retornar à cidade; restaurar a foto correspondente ao reentrar na mesma etapa.
3. Manter `dungeon_snapshot` singular para saves antigos e modos sem exploração por saídas. Migrar para a chave por etapa apenas quando o contexto autoral identificar aventura e etapa válidas.
4. Preservar estado de saídas, passagens abertas, baús, itens coletados, névoa e derrotas dentro do snapshot. Ao iniciar outro destino, não apagar snapshots de etapas incompletas.
5. Definir a limpeza: apagar snapshot/progresso da etapa somente após confirmação de conclusão; manter outros saves de aventura intactos.
6. Verificar: salvar na cidade com uma incursão parcial, mudar de destino, reabrir a etapa e comparar estado explorado/loot/passagens/saídas; completar etapa e confirmar limpeza só dela.

### Task 4 — Runtime de saídas, portões e política de monstros

1. Acrescentar testes de runtime `test_descobrir_saida_nao_move_heroi_nem_muda_fase`, `test_descoberta_compartilhada_e_idempotente` e `test_gate_requisito_fato_item_aventura`: registrar `route_exit_id` uma vez, compartilhar com grupo sem alterar posição/turno/fase; bloquear/reliberar passagem conforme o requisito validado no servidor.
2. Hidratar rotas/saídas no servidor; validar IDs e posições novamente no carregamento e enviar estado de descobertas no `game_state`.
3. Vincular requisitos condicionais às passagens autoradas com validação no servidor para fato/item/aventura concluída; bloquear tentativa sem requisito com mensagem localizada e liberar quando requisito existir.
4. Ao restaurar snapshot, aplicar política da rota: `persistir derrotas` mantém instâncias mortas; `reaparecer` restaura monstros daquele `route_id` e posição usando `source_id`, sem recriar rotas ainda não visitadas.
5. Registrar `source_id` recompensado para impedir XP/loot repetidos; manter baús e loot já obtidos no snapshot. Objetivos de combate mantêm seus critérios de estado sem transformar a descoberta em teleporte.
6. Verificar casos de dois monstros iguais, IDs de runtime diferentes após reload, derrota parcial, respawn sem duplicação de loot e passagem condicional reavaliada após adquirir requisito.

### Task 5 — Conclusão, UI e regressão linear

1. Acrescentar testes `test_objetivo_sem_saidas_nao_libera_conclusao`, `test_saidas_sem_objetivo_nao_liberam_conclusao` e `test_conclusao_recompensa_idempotente`: só ambos os critérios liberam o botão; repetir encerramento não dá renome/recompensa duplicados.
2. Separar recompensa do objetivo principal da conclusão final de etapa quando necessário: conceder objetivo uma vez e só avançar cursor/conceder renome/fim de rota após ambos os critérios.
3. Mostrar no HUD a lista/progresso das saídas obrigatórias, sem substituir objetivo principal, e manter comportamento visual atual em etapas lineares.
4. Garantir que o handler `encerrar_missao` revalide condições no servidor mesmo que cliente envie a ação manualmente.
5. Rodar cobertura focal e suíte relevante; revisar diff para confirmar que etapas lineares não mudaram e nenhuma alteração local preexistente foi incluída.

## Interfaces entre tarefas

- Task 1 produz `routes`, `route_exits`, `monsters[].source_id` e `monsters[].route_id`; Tasks 2 e 4 consomem os IDs de saída/rota e o catálogo validado.
- Task 2 produz etapa `{completion_mode, required_exit_ids}`; Tasks 3, 4 e 5 usam a mesma normalização, preservando o índice inteiro legado.
- Task 3 fornece a restauração da sala por `adventure_id:stage_index`; Task 4 aplica as regras por rota após restaurar o snapshot.
- Task 4 publica descobertas e objetiva completada no estado autoritativo; Task 5 consome esses campos sem confiar em estado apenas do cliente.

## Review Focus

- Migração sem perda de saves antigos nem alteração no significado do inteiro `world_adventure_progress`.
- Saída obrigatória apagada do arquivo depois de escolhida no mapa-múndi: erro explícito e sem concluir a missão por conjunto vazio.
- Reentrada após usar outro destino não apaga snapshot da incursão parcial.
- Monster `source_id` duplicado ou ausente não pode matar, premiar ou reaparecer o monstro de rota diferente.
- Desconexão após alcançar uma saída persiste exatamente uma descoberta; reenvio não duplica recompensa.
- Cliente adulterado não pode encerrar missão ignorando saídas obrigatórias.
- Respawn não duplica XP, baú/loot ou avanço de missão.
- Modo linear e destinos revisitáveis preservam o comportamento atual.

## Handoff

O checkout atual está em `master` e já contém alterações locais em `server.py`, `tools/editor.js`, `game.js`, traduções e outros arquivos. O usuário autorizou trabalhar neste diretório. Preservar integralmente essas mudanças preexistentes e separar os próprios edits por hunks; não fazer reset, checkout, stash ou commit que inclua arquivos que não pertençam a esta feature.
