# Editor de Itens — Fase I: Habilidades concedidas por item

**Data:** 2026-07-27
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Antecessoras:** Fases 1/2a/B/C/D (armas, defesa, motor de efeitos), E (anéis+botas), F (poções), G (arremessáveis), H (venenos — fecha as 8 sub-abas)

## Objetivo

Fazer o campo **`granted_ability`** — hoje só metadado — virar poder real: um item equipado
concede uma habilidade ao herói enquanto estiver equipado. Vale para os 5 tipos de item
equipáveis do editor: **armas, armaduras, escudos, anéis e botas**.

Três famílias de habilidade:

| Família | Id no catálogo | Comportamento |
|---|---|---|
| **Técnica da Guilda** | `guild_<id>` (`categoria:"tecnica"`) | **Ativável**: botão no HUD com efeito, recarga, custo e mira reais |
| **Especialização da Guilda** | `guild_<id>` (`categoria:"especializacao"`) | **Passiva** sempre-ativa enquanto equipado |
| **Habilidade de herói (amostra)** | `hero_<classe>_<skill>` | 3 habilidades: Detectar Armadilhas, Esconder nas Sombras, Imposição das Mãos |

## Contexto

### `granted_ability` hoje

O campo é gravado pela validação de armas/armaduras/acessórios e preservado nas cópias de
compra/equipar, mas **nunca é lido** para efeito de jogo. No editor, o seletor "Habilidade
concedida" existe **apenas no formulário de armas**.

As opções vêm de `_base_ability_library()` (server.py ~21490), exportado ao editor como
`EDITOR_CATALOG.monster_abilities`. Esse catálogo já prefixa os ids por origem:

- `hero_<cls>_<skill>` — habilidades de classe (`source:"heroi"`, com `source_id`);
- `guild_<gid>` — entradas do `GUILD_CATALOG` (`source:"guilda"`, com `source_id` e
  `guild_category` = `tecnica`|`especializacao`);
- ids crus — habilidades nativas de monstro (`source:"monstro"`).

### Por que a Guilda é o reuso certo

O motor de Técnicas da Guilda (`handle_usar_tecnica`, server.py ~6563) já resolve tudo o que
uma habilidade ativável precisa: despacho de efeito por `efeito.tipo` (dezenas de efeitos
implementados), recarga (`technique_cooldowns` / `tecnica_restante`), custo de fome/sede
(`_custo_fome_sede_efetivo`), mira (campo `alvo` lido pelo cliente) e botão de HUD. O portão de
acesso é **uma função de uma linha**: `tem_tecnica_equipada(player, tecnica_id)`.

O mesmo vale para as especializações: o portão é `tem_espec(player, espec_id)`, também de uma
linha, consultado em todos os pontos do motor onde a especialização importa.

### Por que as habilidades de herói são só uma amostra

**`handle_skill` é legado e inerte**: retorna cedo (`if "mp" not in skill: return`) porque o
guerreiro "arma" as habilidades no cliente e o efeito acontece dentro de `handle_attack` (lista
`buffs`); o resto é o sistema de MP desativado. Cada habilidade de classe é, na prática, uma
**mensagem própria + handler próprio + trava de classe + painel próprio no cliente** — há **24**
checagens `class_id != "..."` no servidor. Várias são acopladas ao maquinário da classe
(Ressurreição usa slots de clérigo; a Canção depende do estado do bardo; Fúria é armada pela
lista `buffs`).

Por isso esta fase adapta **3 habilidades vetadas como viáveis** (cada uma tem uma única trava
de classe e miolo genérico), validando o padrão para uma Fase J futura:

| Habilidade | Classe | Forma | Por que é viável |
|---|---|---|---|
| Detectar Armadilhas | rogue | Ação bônus, toggle | O miolo já é genérico (`_revelar_armadilhas_raio`, compartilhado com o Guerreiro da Luz) |
| Esconder nas Sombras | rogue | Ação bônus, toggle | A flag `invisivel_sombras` já é lida genericamente no combate |
| Imposição das Mãos | paladin | Ação principal, com alvo | Usa só helpers genéricos (`_acao_bloqueada`, `_custo_fome_sede_efetivo`, `_no_raio`); valida a forma "mirada" |

## Decisões de design (aprovadas)

1. **Escopo:** Guilda completa (técnicas ativáveis + especializações passivas) + amostra de 3
   habilidades de herói.
2. **Varredura de slots:** `_habilidades_concedidas` varre **todos** os slots de `gear`, não uma
   allow-list. Hoje só arma/armadura/escudo/anel/botas carregam o campo; assim elmo e acessórios
   futuros passam a funcionar sem mexer aqui.
3. **Restrição de classe da técnica é respeitada** (uma técnica exclusiva de mago concedida a um
   guerreiro não funciona) — consistente com a Guilda.
4. **Sem uso duplo:** `technique_cooldowns` é indexado pelo id da técnica, então ter a técnica no
   slot da Guilda **e** num item compartilha a mesma recarga. Sai de graça.
5. **Validação de `granted_ability`:** passa a ser validado contra o conjunto suportado; ids
   desconhecidos são rejeitados (hoje qualquer string é aceita, gerando metadado morto).

## Arquitetura

### 1. Servidor (`server.py`) — *partial staging* obrigatório

O usuário reworka `server.py` em paralelo (WIP "Barreira Arcana" + lojas por cidade). **Nunca**
`git add server.py`; stage só os hunks desta fase via `git apply --cached`, conferindo com
`git diff --cached -- server.py`. Esta fase toca **5 regiões** distintas (helper+portões perto de
`tem_espec` ~1672; 3 handlers de herói ~15601/~15646/~11653; validação e catálogo na região de
itens custom ~22000+) — extrair com cuidado, conferindo a vizinhança de cada uma.

**Helper novo** (module-level, junto de `tem_espec`):

```python
def _habilidades_concedidas(player):
    """Ids de granted_ability dos itens equipados (Fase I)."""
```
Varre `player.get("gear", {})`, coleta `it.get("granted_ability")` não-vazio de cada peça
equipada, devolve um `set`. Robusto a `gear` ausente e a slots vazios.

**Portões estendidos** (2 funções de uma linha):

- `tem_tecnica_equipada(player, tecnica_id)` → aceita também
  `f"guild_{tecnica_id}" in _habilidades_concedidas(player)`.
- `tem_espec(player, espec_id)` → idem com o prefixo `guild_`.

**3 travas de herói relaxadas** — padrão único, aplicado nos três handlers:

```python
if p.get("class_id") != "<classe>" and f"hero_<classe>_<skill>" not in _habilidades_concedidas(p):
    <erro atual>
```
Em `handle_detectar_armadilhas` (`hero_rogue_detectar_armadilhas`),
`handle_esconder_sombras` (`hero_rogue_esconder_sombras`) e
`handle_imposicao_maos` (`hero_paladin_imposicao_maos`).

Na Imposição das Mãos, as mensagens que citam **"Richard"** literalmente passam a usar o nome do
herói (`p['name']`) — com outra classe elas mentiriam. As mensagens de erro das travas também
deixam de citar "Luccas"/"Richard" como donos exclusivos.

**Validação** (região de itens custom): novo helper
`_granted_ability_valida(aid)` → `True` se o id está em `_base_ability_library()` E é suportado
(prefixo `guild_` com `guild_category` em `{tecnica, especializacao}`, ou um dos 3
`hero_*` da amostra). Os três validadores que hoje fazem
`(str(raw["granted_ability"]) if raw.get("granted_ability") else None)`
(`_validate_custom_weapon`, `_validate_custom_armor`, `_validate_custom_accessory`) passam a
descartar ids não suportados (grava `None`) em vez de aceitar qualquer string.

### 2. Editor (`tools/editor_items_editor.js` + `tools/editor_items_logic.js`)

- `abilityOptions()` passa a **filtrar** para o conjunto suportado e **agrupar** em três blocos
  (`<optgroup>`): "Técnicas da Guilda", "Especializações da Guilda" e "Habilidades de Herói".
- O seletor "Habilidade concedida" — hoje só no form de armas — é extraído para um helper
  compartilhado e incluído também em **armaduras/escudos** (`renderArmorForm`) e
  **anéis/botas** (`renderAccessoryForm`), lendo/gravando `draft.granted_ability`.
- `serializeArmor` e `serializeAccessory` já preservam `granted_ability`; nada a mudar na
  serialização.

### 3. Cliente (`game.js`) — 2 pontos cirúrgicos

- **Técnicas** (~11969): o laço do 4º slot monta a lista como
  `equipadas ∪ concedidas por item`. As concedidas são rotuladas **"ITEM"** em vez de "GUILDA".
  Toda a maquinaria de mira/custo/recarga é reusada sem mudança. Um getter novo em
  `src/gameState.js` (`tecnicasConcedidasPorItem(player)`) lê `player.gear` e devolve os ids sem
  o prefixo `guild_`.
- **Herói** (~11854 paladino, ~11860 ladino): os painéis passam a aparecer também para quem
  recebeu a habilidade por item, mostrando **apenas** os botões concedidos (não o painel inteiro
  da classe).

### 4. Testes

**`tools/test_editor_itens.py`** — seção `[I1]`–`[I6]`:

- [I1] `_habilidades_concedidas`: coleta de vários slots; ignora slots vazios/itens sem o campo;
  `gear` ausente não quebra.
- [I2] portões: `tem_tecnica_equipada`/`tem_espec` passam a aceitar o item; sem o item voltam a
  recusar (desequipar remove o acesso).
- [I3] técnica concedida ponta-a-ponta: `handle_usar_tecnica` com a técnica **só** no item
  aplica o efeito, debita fome/sede e entra em recarga; a 2ª ativação é recusada pela recarga.
- [I4] especialização concedida altera o efeito real (usar uma spec com efeito observável, ex.:
  bônus de dano do guerreiro, comparando o dano com e sem o item).
- [I5] as 3 habilidades de herói: funcionam para a classe errada **com** o item; continuam
  recusadas **sem** o item; a mensagem da Imposição usa o nome do herói (não "Richard").
- [I6] validação: id suportado é preservado; id desconhecido vira `None`; nos 3 tipos de item
  (arma/armadura/acessório).

**`tools/test_editor_items_logic.js`**: filtro/agrupamento das opções de habilidade (se a lógica
de filtro morar no módulo puro).

Rodar da raiz; verificar o estado **committado** em worktree isolado.

**Estado conhecido do working tree (NÃO é regressão desta fase):** com o WIP do usuário,
`tools/test_editor_itens.py` aborta na seção `[7]` (lojas por cidade). Para verificar seções
novas no working tree, importar o módulo de teste e chamar as funções diretamente. Também
pré-existentes: `tools/test_roteamento_itens.py` e 1 teste flaky em `tools/test_devorador.py`.

## Fora de escopo

- As demais ~17 habilidades de herói (**Fase J**, com o padrão validado por esta amostra).
- Habilidades nativas de monstro como `granted_ability` (o mestre já tem o próprio caminho via
  `_ativar_editor_ability`).
- Conceder habilidades por itens **não equipáveis** (poções/arremessáveis/venenos são consumíveis
  de bolsa, sem slot).
- Elmo e acessórios (`head`/`item1`/`item2`): o helper já os varre, mas não há sub-aba de editor
  que produza esses itens.

## Critérios de aceite

- Um item com técnica da Guilda concedida mostra o botão no HUD (rótulo "ITEM") e a técnica
  funciona com efeito, recarga e custo reais; desequipar remove o botão.
- Um item com especialização concedida altera o comportamento do motor enquanto equipado.
- As 3 habilidades de herói funcionam para heróis de outra classe quando concedidas por item, e
  seguem bloqueadas sem o item.
- O seletor de habilidade aparece nos 5 tipos de item (arma/armadura/escudo/anel/bota), com as
  opções filtradas e agrupadas.
- Ids não suportados são rejeitados na validação.
- Testes `[I1]`–`[I6]` e node verdes no estado committado isolado.
