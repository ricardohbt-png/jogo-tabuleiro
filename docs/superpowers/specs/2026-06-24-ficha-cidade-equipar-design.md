# Ficha do personagem na cidade (equipar compras) — Design

**Data:** 2026-06-24
**Branch base:** master

## Problema

Na tela da cidade (`screen-city`) o jogador compra equipamentos nas lojas, mas
não há nenhuma forma de **equipar** o que comprou antes de entrar na masmorra.
O ato de equipar/desequipar só existe dentro da masmorra, no painel lateral
(`renderPurchasedItems` → `equiparComprado`/`desequiparComprado`).

## Objetivo

Permitir abrir a **ficha do personagem** durante a tela da cidade, mostrando
atributos + equipamento, e equipar/desequipar/usar os itens comprados na loja.

## Decisões (definidas no brainstorming)

| Tópico | Decisão |
|---|---|
| Acesso | Clicar no **meu** card de herói na barra de heróis (topo). Sem botão novo. |
| Conteúdo | **Equipamento + atributos** (ficha completa). |
| Escopo | **Só o meu** herói abre/edita. Cards dos outros permanecem não-interativos. |

## Restrições de arquitetura

- Equipar é **client-side** (modelo `GS.getHeroiAtivo().equipado` / `.inventario`),
  **não** autoritativo no servidor — consistente com o estado atual
  (VISUAL_CONTRACT). **Sem mudanças em `server.py` nem no protocolo WebSocket.**
- Lógica de equipar já vive em `gameState.js` (`equiparItemComprado`,
  `desequiparItemComprado`, `aplicarConsumivel`). A ficha da cidade é **só
  renderização** em `game.js` e chama esses métodos de `GS` — respeita a
  separação lógica vs. renderização.

## Componentes reaproveitados

- `renderConteudoAtributosFichaJogo(heroi, estadoServidor)` (game.js:2296) — bloco
  de HP/CA/atributos já usado pela ficha em jogo. Será alimentado com o registro
  do jogador vindo de `cityState` (HP/nível atuais) em vez de `GS.me`.
- Padrão de `renderPurchasedItems` (game.js:9545) — render dos slots equipados
  (com ✕ Remover) e da lista "Comprados na Loja" (⚙ Equipar / ▶ Usar).
- `_TIPO_ITEM_EMOJI`, `_TIPO_ITEM_LABEL`, `_EQUIPADO_SLOTS`, `aplicarTooltipAoItem`
  — constantes/helpers existentes de render de item.

Não reaproveitar `abrirFichaEmJogo` diretamente: é somente-leitura (sem botões de
equipar) e lê `GS.me` (estado de masmorra), não o estado da cidade.

## Design

### 1. Ponto de entrada — card de herói clicável

Em `_updateCityHeroBar(msg)` (game.js:918): apenas o card do próprio jogador
(`isMe`) recebe:
- `cursor:pointer` e um afeto de hover (classe/estilo),
- uma dica visual discreta (ex.: "🎒") indicando que abre a ficha,
- `onclick` → `abrirFichaCidade()`.

Cards dos outros heróis ficam inalterados (não-clicáveis).

### 2. Overlay `abrirFichaCidade()`

Modal escuro no mesmo estilo gold-on-black de `abrirFichaEmJogo`
(`position:fixed; inset:0; z-index:300`), contendo:

1. **Cabeçalho:** retrato, nome, classe, nível — do registro do jogador em
   `cityState.players` (lookup por `GS.myPid`) com fallback para `HERO_DATA`.
2. **Atributos:** `renderConteudoAtributosFichaJogo(heroi, cityPlayer)` — HP/CA/
   atributos atuais.
3. **Equipamento** (`<div>` com id próprio para refresh isolado):
   - Equipado (Loja): slots de `heroi.equipado` via `_EQUIPADO_SLOTS`, cada um
     com botão **✕ Remover** → `GS.desequiparItemComprado(key)` + refresh.
   - Comprados na Loja: `heroi.inventario`, cada item com:
     - **⚙ Equipar** (gear) → `GS.equiparItemComprado(idx)` + refresh,
     - **▶ Usar** (consumível) → `GS.aplicarConsumivel(item)` + consome slot + refresh,
     - munição: sem botão (igual ao in-dungeon).
4. **Rodapé:** botão ✕ Fechar; clicar fora também fecha.

### 3. Refresh isolado

`_refreshFichaCidade()` re-renderiza **apenas** a seção de equipamento (pelo id
do container) após equipar/desequipar/usar. Não usa `renderMyPanel(GS.gameState)`
(que falharia: `gameState` é `null` na cidade).

Também atualiza a barra de heróis se o HP mudou por uso de consumível? Não —
consumível só altera fome/sede (não HP); a barra de heróis da cidade mostra HP,
então não precisa atualizar. (Se no futuro consumível curar HP, ligar
`_updateCityHeroBar`.)

## Fluxo de dados

```
clique no meu card → abrirFichaCidade()
  └─ lê cityState.players[me] (HP/nível) + GS.getHeroiAtivo() (equipado/inventario)
  └─ monta overlay (atributos + equipamento)
        botão Equipar/Remover/Usar → GS.<método> → _refreshFichaCidade()
```

`GS.getHeroiAtivo()` já cai para `cityState.players` quando não há `gameState`
(gameState.js:619), e `_sincronizarHeroiComServidor` (chamado no `cityState`)
mantém ouro/inventário sincronizados com o servidor.

## Tratamento de erros / casos de borda

- `cityState` ainda não chegou: a barra de heróis só existe depois do
  `cityState`, então o card só é clicável quando há estado — sem caso degenerado.
- Inventário cheio ao desequipar: `desequiparItemComprado` já loga a recusa e
  retorna `false`; o refresh não muda nada (feedback via log existente).
- Restrição de classe ao equipar: `equiparItemComprado`/`podeEquipar` já recusa e
  loga; refresh sem mudança.
- Reabrir overlay: remover qualquer overlay anterior pelo id antes de criar
  (mesmo padrão de `abrirFichaEmJogo`).

## Testes

Mudança puramente de UI client-side, sem caminho de servidor testável por
`tools/test_*.py`. Verificação manual no app:
1. Entrar na cidade, comprar um equipamento na loja.
2. Clicar no próprio card → ficha abre com atributos + equipamento.
3. Equipar o item comprado → move para "Equipado", refletido no overlay.
4. Remover → volta para "Comprados".
5. Usar um consumível → some da lista.
6. Clicar no card de outro herói → nada acontece.
7. Entrar na masmorra → equipamento equipado na cidade persiste (mesmo modelo
   client-side `GS.getHeroiAtivo`).

## Fora de escopo (YAGNI)

- Persistência autoritativa de equipamento no servidor.
- Ver/editar a ficha de outros heróis.
- Abas de magias na ficha da cidade.
