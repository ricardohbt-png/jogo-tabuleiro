# Vaca Arisca e alimentos bovinos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Integrar ao jogo a Vaca Arisca com IA passiva e fuga, loot variável de carne e leite, e os dois consumíveis à venda na taverna.

**Architecture:** A ficha nativa fica em `MONSTER_DEFS`; uma IA dedicada e um estado de provocação mantêm o comportamento isolado dos demais monstros. O fluxo de `loot_drops` recebe faixa de quantidade e resolve também itens da taverna. Os consumíveis usam `effect: food`; imagem 2D e miniatura GLB são ligadas pelo identificador visual `vaca`.

**Tech Stack:** Python (`server.py`), JavaScript (`game.js`), catálogo de traduções (`src/lang/catalogo.js`), exportador Python do catálogo, PNG e GLB.

**Spec:** `docs/superpowers/specs/2026-10-27-monstro-vaca-design.md`

## Global Constraints

- Vaca Arisca: ID `vaca`, subtipo `animal`, ND 1/4, 16 PV, CA 11, movimento 6, Cabeçada +3 (`1d6+1`), sem ouro.
- A vaca nunca inicia ataque; uma ação ofensiva de herói contra ela a provoca mesmo se errar. Dano ambiental não provoca.
- Em cada turno da vaca, há 50% de chance de tentar fugir uma casa para longe do herói vivo mais próximo; a fuga consome o turno e não encerra o combate.
- Loot garantido por vaca: quantidade inteira uniforme e inclusiva de 1–3 `carne_bovina` e 1–4 `leite`.
- `carne_bovina`: preço 3 moedas, +25 fome, +0 sede; `leite`: preço 1 moeda, +5 fome e +5 sede. Ambos são itens consumíveis de bolsa vendidos na Taverna.
- Arte: `assets/pawns/monstros/vaca/vaca.png`; GLB: `assets/models3d/monstros/vaca.glb`; ícones de itens: `assets/itens/carne_bovina.png` e `assets/itens/leite.png`.
- Não incluir a vaca em encontros aleatórios nem em mapas já existentes.
- Não adicionar nem executar testes automatizados. Usar inspeção de diff, verificações de sintaxe e conferência da importação do GLB.

## Review Focus

- A IA não deve atacar uma vaca não provocada, inclusive quando um herói está perto; conferir o ramo de despacho anterior à IA agressiva.
- Ataques válidos que erram devem provocar; dano ambiental não deve provocar; revisar os pontos de entrada de ataque de armas e magias.
- Uma fuga bem-sucedida gasta a ação e desloca a vaca uma casa; sem casa livre, ela não deve atacar nesse turno.
- As faixas de loot devem ser inclusivas, uniformes e garantidas uma vez cada; inventário cheio deve seguir o fluxo de saque no chão já existente.
- O editor e o cliente devem resolver `vaca` para PNG e GLB sem modificar a aparência/orientação das outras espécies.

---

### Task 1: Cadastrar Carne Bovina e Leite

**Files:**
- Modify: `server.py` (`SHOP_TAVERN`)
- Modify: `src/lang/catalogo.js`
- Regenerate: `tools/editor_catalog.js` pelo exportador autoritativo
- Existing assets: `assets/itens/carne_bovina.png`, `assets/itens/leite.png`

**Interfaces:**
- Produces: definições `carne_bovina` e `leite` em `SHOP_TAVERN`, ambas `item_slot: "bag"` e `effect: "food"`.

- [x] Inserir `carne_bovina` com nome, emoji 🍖, preço 3, `fome: 25`, `sede: 0` e ícone correspondente.
- [x] Inserir `leite` com nome, emoji 🥛, preço 1, `fome: 5`, `sede: 5` e ícone correspondente.
- [x] Adicionar nomes e descrições PT/EN em `src/lang/catalogo.js` e regenerar o catálogo do editor sem descartar alterações locais preexistentes.
- [x] Conferir visualmente as duas entradas em um diff focalizado e revisar `git diff --check`.

### Task 2: Registrar Vaca Arisca e loot com quantidade variável

**Files:**
- Modify: `server.py` (`MONSTER_DEFS`, resolução de `loot_drops`, morte de monstros)
- Modify: `src/lang/catalogo.js` (rótulo e descrição da ficha, se usados pelo bestiário)
- Existing assets: `assets/pawns/monstros/vaca/vaca.png`, `assets/models3d/monstros/vaca.glb`

**Interfaces:**
- Consumes: `SHOP_TAVERN` e os itens da Task 1.
- Produces: `MONSTER_DEFS` com `type: "vaca"`, `ai_type: "vaca_passiva"` e dois `loot_drops` garantidos usando `quantity_range: [min, max]`.

- [x] Estender a resolução de item de `loot_drops` para aceitar `SHOP_TAVERN` e criar uma cópia do item por unidade sorteada.
- [x] Ler `quantity_range` inclusiva para drops de item, aplicando `random.randint(min, max)`; quando ausente, preservar quantidade padrão 1.
- [x] Adicionar a ficha aprovada: Vaca Arisca, ND 1/4, 16 PV, CA 11, movimento 6, FOR/atributos e salvamentos compatíveis com animal médio, uma Cabeçada +3 (`1d6+1`), `subtipo: "animal"`, sem ouro e spawn aleatório 0.
- [x] Configurar drops com 100% de chance: `carne_bovina` quantidade `[1,3]` e `leite` `[1,4]`.
- [x] Não alterar o fluxo existente de loot de outros monstros; a ausência de `quantity_range` mantém exatamente um item por drop bem-sucedido.
- [x] Revisar o trecho de morte para confirmar que quantidade maior que a bolsa disponível continua indo para o baú no chão.

### Task 3: IA passiva e provocação

**Files:**
- Modify: `server.py` (marcação de ataque, `_run_monster_ai`, nova `_ai_vaca_passiva`)
- Existing: `src/lang/narracao.js` fornece as duas mensagens reutilizadas por `_fugir_monstro(m)`; não precisa de novas falas.

**Interfaces:**
- Consumes: monstro `vaca` da Task 2 e o helper existente `_fugir_monstro(m)` para um passo de afastamento.
- Produces: campos runtime `vaca_provocada` e `vaca_agressor_id`; despacho antecipado de `ai_type: "vaca_passiva"`.

- [x] Marcar a vaca provocada para ação ofensiva de herói direcionada a ela, incluindo uma rolagem que erre; não marcar por dano ambiental.
- [x] Rolar 50% uma vez por turno de IA da vaca; sucesso chama o afastamento de uma casa e encerra sua ação, mesmo sem caminho livre.
- [x] Em falha da rolagem, atacar apenas se `vaca_provocada`; priorizar `vaca_agressor_id` se ainda vivo e disponível, senão o alvo vivo mais próximo.
- [x] Se não provocada e a rolagem de fuga falhar, permanecer parada e não atacar.
- [x] Despachar a IA dedicada antes das tentativas e ações agressivas compartilhadas, sem alterar os outros tipos de monstro.
- [x] Conferir manualmente o fluxo de estado e o diff para as quatro condições de Review Focus relacionadas à IA.

### Task 4: Ligar imagem 2D, GLB e documentação

**Files:**
- Modify: `game.js` (`_MONSTER_GLB_MODELS` e, se necessário, orientação/footprint)
- Existing assets: `assets/pawns/monstros/vaca/vaca.png`, `assets/models3d/monstros/vaca.glb`, `assets/models3d/monstros/vaca.blend`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: ficha `image: "vaca"` da Task 2.
- Produces: cliente resolve o nome de imagem `vaca` ao PNG de monstro e ao GLB correspondente; contrato durável documentado.

- [x] Adicionar `vaca: 'assets/models3d/monstros/vaca.glb'` no mapa do cliente e acertar a orientação/footprint da miniatura, respeitando o eixo frontal do GLB.
- [x] Manter o PNG no caminho `assets/pawns/monstros/vaca/vaca.png` para visão 2D e fallback do carregamento 3D.
- [x] Documentar ficha, IA, drops, preços e caminhos dos assets em `CLAUDE.md`.
- [x] Rodar `node --check game.js`, `node --check src/lang/catalogo.js` e `python -c "import ast, pathlib; ast.parse(pathlib.Path('server.py').read_text(encoding='utf-8'))"`.
- [x] Reimportar `assets/models3d/monstros/vaca.glb` em Blender 5.1 e confirmar malhas, materiais e limites; encerrar com `git diff --check` e revisão do status/diff sem tocar em mudanças locais não relacionadas.

