# Campanha dos Charcos em cadeia, sem descanso — desenho e plano

Data: 2026-10-21. Pedido do autor: as missões da Vila dos Charcos devem ser uma seguida da
outra, sem descanso até o fim; os locais somem do mapa-múndi depois de concluídos; e a
escada, que não faz sentido em pântano/floresta, pode ser trocada por um poste de entrada
(opção nova no editor de masmorras).

## Decisões (do autor, 2026-10-21)

1. A 1ª masmorra (Bordas) **mantém** a volta à cidade; as outras quatro **bloqueiam** a saída
   (`saida_permitida: false`).
2. **Marcador de entrada**: campo novo da masmorra, `marcador_entrada`: `"escada"` (padrão,
   igual a hoje) ou `"poste"` (poste de madeira com pano, sem a escada). Opção no editor.
3. O save em andamento (`sg_v2mqxv`, dentro de `charcos_4a_arredores`) é **migrado**, com backup.

## Escolhas de Claude

- As quatro aventuras viram **uma só**, `charcos_mare` ("A Maré do Charco"), com 5 etapas
  encadeadas (`encadear`): bordas → palafitas → travessia → arredores → aldeia. É o único
  jeito de o motor (emenda de etapas) impedir descanso: nada se recupera entre etapas.
- `ocultar_apos_concluir: true` no destino (já existe no motor): some do mapa-múndi ao
  concluir a aventura inteira. Visibilidade inicial continua pelo fato do gancho.
- Custo de fome/sede do destino = soma dos antigos (1+2+2+3 = 8); `renome_recompensa` = 5.
- `zumbra_ferrao` deixa de exigir a Travessia (não dá para voltar à vila no meio da cadeia):
  passa a exigir só o gancho aceito. `charcos_gratidao` (Ysa) usa `charcos_mare`.
- O aviso "daqui até o fim os lugares se emendam" sobe para a abertura da 1ª etapa.
- O final de **fuga** (sair pela escada na Aldeia) deixa de existir: a Aldeia bloqueia a saída.
- Migração do save (`migrar_charcos_cadeia`, pura e idempotente): progresso, progresso de rota,
  `story_beats_done`, diário, foto da masmorra e pontos de salvamento. Reaproveita em
  `ensure_campaign_schema`, `carregar_ponto_no_jogo` e `_foto_aplicar_sala`. Efeito colateral
  aceito: quem já ganhou +1 de renome por etapa antiga ganha +5 de novo no fim da cadeia.

## Tarefas

1. **Motor** `marcador_entrada`: `validar_dungeon`, `load_authored_dungeon`,
   `FOTO_SALA_CATEGORIAS` ("foto"), `game_state`. Teste `tools/test_marcador_entrada.py`.
2. **Editor**: seletor "marcador de entrada" no painel da masmorra (`m-marcador`), `buildJSON`/
   `loadJSON`/`save`, textos PT/EN. Teste `tools/test_marcador_entrada_editor.js`.
3. **Cliente**: poste em 2D e 3D no lugar da escada, tooltip "Poste de entrada" com e sem
   retorno. Teste `tools/test_marcador_entrada_cliente.js`.
4. **Dados da campanha**: gerador (`tools/gerar_campanha_charcos.py`, só `destinos()` e as
   conversas), `world_adventures.json`, as 5 masmorras (cirúrgico), conversas da Ysa e da
   Zumbra (gerador da Zumbra). Teste `tools/test_charcos_cadeia.py`.
5. **Migração do save**: função pura + ganchos. Teste `tools/test_charcos_migracao.py`.
6. **Docs e prova**: `CLAUDE.md`, suítes relacionadas, prova em navegador do poste e do
   destino único que some ao concluir.
