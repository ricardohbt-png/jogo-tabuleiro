# Sub-projeto B — Arremessáveis de Área (com save)

**Data:** 2026-07-09
**Status:** aprovado (brainstorming)

## Contexto

Segundo sub-projeto da família de arremessáveis do mercado (ver
[decomposição](2026-07-09-arremessaveis-fogo-design.md) e memória
`arremessaveis-roadmap`). O **Sub-projeto A** (framework de bolsa→mira→arremesso,
teste de ataque single-target, status "em chamas") já está mergeado em `master`.

Este spec cobre os quatro itens de **área**: Bomba Incendiária, Granada Explosiva,
Granada Superior e Bomba de Fumaça. Eles exercitam o modo `alvo:"area"` que o
catálogo `ARREMESSAVEIS` já reserva desde A.

## Infraestrutura existente reaproveitada

- **`ARREMESSAVEIS`** (catálogo do Sub-projeto A) + `handle_throw_item`
  (ação principal, consome o item, LOS) — extensível por `defn["alvo"]`.
- **`_alvos_na_area(cx, cy, raio)`** — retorna todos os entes (jogadores, monstros,
  animados) no raio; base do fogo amigo.
- **`_save_mostrado(alvo, "reflexos", cd)`** — teste de Reflexos com animação de
  dado; retorna `(save_ok, ...)`.
- **`_aplicar_dano_area_fogo` / `_executar_bola_fogo`** — molde exato de dano de
  área com sombra de parede a partir do centro e save de metade.
- **`_aplicar_em_chamas(alvo, rodadas, agua_apaga)`** (Sub-projeto A) — status
  "em chamas".
- **`_aplicar_escuridao(caster, raio, duracao)`** — cria uma zona de escuridão
  (hoje centrada no conjurador); será generalizada para aceitar um centro `(cx,cy)`.
- **Cliente:** `_recomputarAreaMagia` + `window._spellHL.area` (prévia verde de
  área que segue o cursor), `_addCheb`, `_aplicarSpellHL` (2D e 3D). `pendingThrow`
  e `resolveTileClick` do Sub-projeto A.

## Decisões de design

1. **Fogo amigo:** as bombas/granadas de área atingem **todos** no raio (heróis,
   o próprio arremessador, monstros), como a Bola de Fogo. Save de Reflexos dá a
   cada um a chance de metade do dano. (A Fumaça, sem dano, não tem esse efeito.)
2. **Bomba de Fumaça = zona de escuridão** (2 rodadas) centrada no tile escolhido.
   A "vantagem em Furtividade" vem embutida na escuridão (inimigos sem visão-no-escuro
   não enxergam através dela; o Ladino pode se esconder ali). **Sem** subsistema
   novo de teste de furtividade (YAGNI).
3. **Ação principal** para os quatro (uniforme com A; a Fumaça também — é o custo
   do turno para criar cobertura).
4. **Sem zona de dano persistente** (diferente da Bola de Fogo, que aplica R2/R3
   em rodadas seguintes): a Incendiária põe o status "em chamas" em quem foi
   atingido, não deixa fogo no chão.
5. Granadas usam elemento genérico `"explosao"` (sem resistência específica hoje).
6. **Sem jogada de ataque** nos itens de área — só o save de Reflexos do alvo.

## Componentes

### 1. Mira de área (cliente — `game.js`)

- O modo de mira do arremesso (`_iniciarMiraArremesso`, Sub-projeto A) passa a
  ramificar por `catDef.alvo`:
  - `"ataque_alvo"` (A): alcance em tiles vermelhos, alvo = monstro.
  - `"area"` (B): pinta o **alcance** (onde o centro pode cair, Chebyshev ≤ `alcance`
    a partir do jogador) **e** uma **prévia verde da explosão** (`area_raio`) que
    segue o cursor, reusando `_recomputarAreaMagia`/`window._spellHL.area`.
- Clique numa casa dentro do alcance (com LOS até o centro) → dispara. Sem
  alvo-monstro. ESC / clique-fora cancela (mesma teardown de A).
- `on3DClick` e `handleTileClick` roteiam o clique de área pelo mesmo
  `GS.resolveTileClick`.

### 2. Estado do cliente (`src/gameState.js`)

- `CATALOGO_ITENS`: quatro entradas novas com `arremessavel:true`, `alvo:"area"`,
  `alcance:4`, `area_raio:1` (e `dano`/descrição para tooltip).
- `resolveTileClick`: o ramo `pendingThrow` passa a distinguir `alvo`:
  - `"ataque_alvo"` → comportamento de A (`{type:'throw', itemId, targetId}`).
  - `"area"` → valida alcance (Chebyshev ≤ `alcance`) + LOS até `(tx,ty)` e retorna
    `{type:'throw_area', itemId, tx, ty}` (ou `{type:'throw_blocked'}`).
- Sender: `throwItemArea(id, tx, ty)` → `send({type:'throw_item', item_id, tx, ty})`.
  (Mantém `throwItem(id, targetId)` de A para o modo single-target.)
- ZERO DOM/THREE (regra de arquitetura).

### 3. Servidor (`server.py`)

- Catálogo `ARREMESSAVEIS`: quatro entradas novas (`alvo:"area"`), com:
  `alcance`, `area_raio`, `dano` (opcional), `elemento`, `save` (`{tipo:"reflexos",
  cd:N}`, opcional), `em_chamas` (bool) + `chamas_agua_apaga`, e `zona` (opcional,
  ex. `{tipo:"escuridao", duracao:2}`).
- Itens correspondentes em `SHOP_MERCHANT` (`effect:"throwable"`).
- `handle_throw_item(pid, data)` passa a ler `defn["alvo"]` e despachar:
  - `"ataque_alvo"` → caminho de A (usa `target_id`), inalterado.
  - `"area"` → novo caminho: lê `tx`/`ty` de `data`, valida alcance (Chebyshev ≤
    `alcance` a partir do jogador) + `_tem_linha_de_visao(pos, [tx,ty])`, consome o
    item, marca ação principal, e chama `_throw_item_area`.
  - **Refactor:** a assinatura vira `handle_throw_item(pid, data)` (recebe o dict da
    mensagem) para carregar `target_id` OU `tx`/`ty`; o dispatch WS passa `msg`.
- `_throw_item_area(pid, defn, cx, cy)`:
  - Se `defn` tem `dano`: rola o dado, aplica a TODOS em `_alvos_na_area(cx,cy,raio)`
    com sombra de parede a partir do centro; para cada um, `_save_mostrado(alvo,
    "reflexos", cd)` → metade no sucesso; aplica via `_dano_em_alvo`. Se `em_chamas`
    e o dano final > 0, `_aplicar_em_chamas(alvo, rolar(chamas_dur), chamas_agua_apaga)`.
  - Se `defn` tem `zona` (`escuridao`): chama o `_aplicar_escuridao` generalizado
    centrado em `(cx,cy)` com a duração da zona.
- `_aplicar_escuridao` ganha parâmetro de centro opcional `pos=None` (default = casa
  do caster, para não quebrar a magia Manto de Escuridão).

### 4. Render (`game.js`)

- Prévia de alcance + área verde reusando `_spellHL` (2D e 3D).
- Dano/among usam o feedback existente; o 🔥 dos que pegaram fogo já vem de A
  (`em_chamas_rodadas`). Animação de projétil/explosão elaborada é opcional (YAGNI).

### 5. Itens (loja/mercado)

| Item | id | Emoji | Alcance | Área | Dano | Save | Extra | Preço |
|---|---|---|---|---|---|---|---|---|
| Bomba Incendiária | `bomba_incendiaria` | 💣 | 4 | raio 1 | 2d6 fogo | Reflexos CD 12 (½) | atingidos pegam fogo (1/rod, 1d4 rod, água apaga) | 45 🪙 |
| Granada Explosiva | `granada` | 💣 | 4 | raio 1 | 2d6 explosão | Reflexos CD 12 (½) | — | 40 🪙 |
| Granada Superior | `granada_superior` | 💥 | 4 | raio 1 | 3d6 explosão | Reflexos CD 15 (½) | — | 70 🪙 |
| Bomba de Fumaça | `bomba_fumaca` | 💨 | 4 | raio 1 | — | — | zona de escuridão 2 rodadas | 30 🪙 |

### 6. Testes (`tools/test_arremessaveis_area.py`)

- Dano de área a TODOS no raio (fogo amigo): herói E monstro atingidos.
- Save de Reflexos: sucesso = metade, falha = cheio (semente controlada).
- Incendiária: quem terminou com dano > 0 fica `em_chamas`.
- Granada Superior: 3d6 / CD 15.
- Fumaça: cria zona `escuridao` no tile escolhido; expira após 2 rodadas
  (`_processar_zonas_turno`).
- Alcance/LOS até o centro: fora do alcance ou parede → recusa, item NÃO consumido.
- Item consumido no disparo válido; ação principal marcada.
- Regressão: o modo `ataque_alvo` de A continua funcionando após o refactor de
  assinatura (`handle_throw_item(pid, data)`).

## Fora de escopo (deste sub-projeto)

- Corrosão de equipamento / frascos de ácido (Sub-projeto C).
- Cola/Rede — controle (Sub-projeto D).
- Veneno Agonia Sufocante (Sub-projeto E).
- Zona de dano persistente no chão (a Incendiária só aplica status nos atingidos).
- Subsistema genérico de teste de Furtividade.
- Animação 3D elaborada de projétil/explosão.
