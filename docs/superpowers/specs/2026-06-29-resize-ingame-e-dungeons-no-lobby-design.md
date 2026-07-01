# Redimensionamento valendo no jogo + dungeons colocadas aparecem no lobby

**Data:** 2026-06-29
**Arquivos:** `server.py`, `game.js` (`src/gameState.js` já lê `d.tiles` do servidor).

Duas correções independentes que fazem o que o editor produz funcionar no jogo:

- **Parte A** — `size`/`vscale` por decoração (gravados pelo editor) passam a valer
  no jogo: render 2D + 3D e colisão/névoa.
- **Parte B** — masmorras colocadas em `dungeons/` que têm monstro/prisioneiro fora
  de sala deixam de ser rejeitadas e aparecem no lobby.

## Decisões (do brainstorming)

- Footprint maior (`size`) **ocupa e bloqueia** as casas no jogo (colisão + névoa),
  não só aparência.
- Escala visual (`vscale`) é aplicada **na miniatura 3D** (visão principal) e no 2D
  de cima: largura no plano, altura esticando **para cima ancorada no chão**.
- Validação: o **servidor passa a aceitar** `room_id` vazio/None para monstros e
  prisioneiro (espelha o editor). Sem mexer nos arquivos existentes — eles passam a
  validar como estão.
- Escopo de "aparecer": **lobby do jogo** apenas. A aba Campanha do editor (lista
  estática `editor_dungeons.js`) fica fora.

## Contexto verificado (read-only)

- `listar_dungeons()` (server.py:1882) já varre `dungeons/` ao vivo e vai em
  `lobby_state.dungeons` (server.py:3290); o lobby tem o seletor (game.js:18201).
- Causa real da Parte B: `validar_dungeon` rejeita `room_id` None em monstro
  (server.py:1729) e prisioneiro (server.py:1768). Confirmado rodando
  `listar_dungeons()`: só `gustavo.json` e `gustavo (1).json` caem, com a mensagem
  "monstro com room_id inexistente: None".
- `_serializar_decoracoes` (server.py:10244) hoje envia `"size": meta["size"]`
  (catálogo) e **não** envia `vscale`. `_decor_tiles`/`_decor_eff_size`
  (server.py:10120-10133) usam só o catálogo.
- 3D: `game.js:12963` deriva o footprint de `GS.decorTilesOf(d)` (= `d.tiles` do
  servidor) → o footprint "se ajusta sozinho" quando o servidor resolver o override;
  falta aplicar `vscale` ao mesh. 2D: `game.js:4970`.
- `gameState.decorTilesOf` (src/gameState.js:1128) já usa `d.tiles` — sem mudança.

## Parte A — Pipeline do redimensionamento

### Servidor (`server.py`)

1. **Load** (`load_authored_dungeon`, ~3744): ao montar `dec`, copiar override:
   - `size` se for lista de 2 inteiros ≥1 → `dec["size"]`.
   - `vscale` se for lista de 2 números > 0 → `dec["vscale"]` (clamp 0.2–4).
2. **Footprint efetivo:** `_decor_tiles(d)` passa a usar `d.get("size")` (com troca
   por `facing`) quando presente, senão o catálogo. Implementar via helper
   `_decor_base_size(d)` (override-ou-catálogo, pré-facing) e usá-lo em
   `_decor_eff_size`/`_decor_tiles`. Colisão (`_blocks_tile`/`_decor_block_tiles`) e
   névoa (`_reveal_around`/`_tall_oclui_caminho`) derivam de `_decor_tiles` → footprint
   maior bloqueia e ocupa automaticamente.
3. **Serializar** (`_serializar_decoracoes`): enviar `"size": _decor_base_size(d)`
   (efetivo) e `"vscale": d.get("vscale")` (ou `[1,1]`). `tiles` já sai correto.
4. **Validar** (`validar_dungeon`, seção decorações ~1801): calcular `ew,eh` a partir
   do `size` override quando presente (senão catálogo), para footprint e o set de
   sobreposição `ocupadas`.

### Cliente (`game.js`)

5. **2D** (render de cima, ~4970): ao desenhar a imagem/emoji da decoração, aplicar
   `d.vscale`: `dw = pw*sx`, `dh = ph*sy`, ancorado base-centro (cresce p/ cima e
   centralizado). Mesma fórmula do editor.
6. **3D** (~12963): footprint já vem por `tiles`. Após posicionar o mesh, aplicar
   `vscale`:
   - largura/profundidade × `sx`, altura × `sy`;
   - **âncora no chão (y=0)**: reposicionar para a base ficar no piso após o scale
     (miniatura PNG já assenta a base em y=0; procedural reposiciona
     `position.y = spec.h*sy/2`).
   - Aplicar tanto no caminho `d.image` (miniatura) quanto no procedural.

`src/gameState.js`: sem mudança (já usa `d.tiles`).

## Parte B — Dungeons no lobby

7. `validar_dungeon`: trocar as duas checagens estritas por uma que aceita ausência:
   - monstro (1729): rejeitar só se `room_id` **não-nulo** e fora de `room_ids`.
   - prisioneiro (1768): idem.
   `room_id` None/ausente passa a ser válido (entidade "sem sala"), como o editor já
   permite. `load_authored_dungeon` já trata `room_id` ausente.

## Não-objetivos (YAGNI)

- Nada na aba Campanha do editor / `editor_dungeons.js`.
- Sem novos campos no editor (já grava `size`/`vscale`).
- Sem migração dos arquivos existentes — passam a validar/rodar como estão.

## Testes

- **Python:**
  - `validar_dungeon(gustavo.json)` retorna OK e ambos aparecem em
    `listar_dungeons()` (Parte B). Adicionar caso em
    `tools/test_dungeon_loader.py` (ou novo `tools/test_validacao_room_id.py`).
  - Round-trip: carregar uma dungeon com decoração `size`/`vscale`, conferir que
    `_decor_tiles` reflete o footprint maior e que `_serializar_decoracoes` envia
    `size`/`vscale`. Estender `tools/test_decor_roundtrip.py`.
- **Manual no jogo:** abrir uma dungeon com objeto redimensionado → aparece maior no
  3D e no 2D, e bloqueia as casas extras; abrir `gustavo` no lobby e jogar.
