# Editor de Itens — Fase 1: Armas (design)

Data: 2026-07-20
Status: aprovado (aguardando revisão da spec escrita)

## Objetivo

Adicionar ao editor de masmorras (`tools/editor.html`) uma nova aba **"Editor de
itens"** que permite criar itens personalizados, salvos num catálogo global vivo e
mesclados no jogo — no mesmo padrão do "Editor de criaturas". Esta primeira fase é
um **piloto que implementa apenas a aba de Armas** ponta-a-ponta, validando todo o
padrão (formulário → validação → persistência → merge no jogo → disponibilidade →
efeitos passivos funcionais). As demais 7 abas (armaduras, escudos, anéis, botas,
poções, arremessáveis, venenos) são fases seguintes.

## Decisões de brainstorming (fixadas)

1. **Destino do item:** catálogo global vivo (JSON próprio, mesclado no jogo). Cada
   item declara na própria ficha **onde pode ser encontrado**: loja(s), baús/
   recompensas de masmorra, loot de monstro.
2. **Habilidade de Guilda/herói no item:** nesta fase só efeitos **passivos** são
   funcionais; a habilidade **ativável** concedida pelo item é apenas **gravada
   (metadado)**, para ligar numa fase futura.
3. **Itens base:** o editor pode **copiar** um item base como modelo, mas salva
   sempre como item **novo** (id próprio). Os itens base do jogo **nunca** são
   alterados/sobrescritos.
4. **Imagem:** **upload de PNG**. Emoji permanece só como fallback automático.
5. **Fases:** **só armas primeiro** (piloto).
6. **Preço:** **manual com valor sugerido** a partir dos stats.

## Arquitetura

- Nova aba de topo **"Editor de itens"** em `tools/editor.html`, como *view*
  própria (div mostrada/ocultada) + módulo `tools/editor_items_editor.js`,
  espelhando `editor_monster_editor.js` / `#monster-editor-view`.
- Dentro da view, uma barra de sub-abas por tipo de item: **Armas, Armaduras,
  Escudos, Anéis, Botas, Poções, Arremessáveis, Venenos**. Nesta fase **só "Armas"
  é funcional**; as outras 7 aparecem **visíveis mas desabilitadas** ("em breve"),
  para a estrutura já existir.
- **Persistência (espelha os monstros personalizados):**
  - Dados: `itens_personalizados.json` (na raiz, ao lado de
    `monstros_personalizados.json`). Gitignore: seguir o mesmo tratamento do
    arquivo de monstros (versionado hoje — manter versionado por consistência).
  - Índice regenerado: `tools/editor_items_custom.js` exportando
    `window.EDITOR_CUSTOM_ITEMS = [...]`, carregado por `editor.html` (e pelo
    catálogo do editor) via a lista de scripts com cache-buster.
  - No server: `_read_custom_items` / `_validate_custom_item` / `_save_custom_item`
    / `_apply_custom_items` / `_regen_custom_items_index`, análogos aos de monstro
    (`server.py` ~linha 20456+). `_apply_custom_items(_read_custom_items())` roda no
    boot para mesclar no catálogo vivo.
- **Copiar-como-modelo:** dropdown "Basear em…" lista as armas base (`WEAPONS` via
  `EDITOR_CATALOG`); ao selecionar, pré-preenche o formulário. Salvar gera item novo
  com `id` = slug do `name` (com desambiguação se já existir).

## Modelo de dados da arma custom

```
id                 slug auto a partir do name (editável; único no catálogo custom)
name               string
emoji              string (fallback visual)
img                bool/derivado — PNG enviado fica em assets/itens/<id>.png
die                "NdX" montado por (quantidade, dado); ex. 2 × d6 → "2d6"
categoria          "cortante" | "contundente" | "perfurante"
stat               "str_" | "dex"
finesse            bool (dano usa o melhor modificador entre FOR e DES)
manejo             "corpo" | "lanca" | "cajado" | "distancia" | "arremessavel"
                     → serializa para os campos reais do jogo:
                       corpo        → (nada extra)
                       lanca        → reach:"lanca"
                       cajado       → reach:"cajado"
                       distancia    → range:N (N configurável)
                       arremessavel → throw_range:N (N configurável); pode combinar
                                      com corpo (arma corpo-a-corpo arremessável)
two_handed         bool (não pode com escudo/2ª arma)
atk_bonus          int  (bônus fixo "no ataque")   — mutuamente exclusivo com
damage_bonus       int  (bônus fixo "no dano")       damage_bonus na UI (um alvo só)
extra_damages      lista de { die:"NdX", type } com type ∈
                     {fire, cold, lightning, acid, holy}
                     (some cada linha no dano do acerto)
granted_ability    id de habilidade de Guilda/herói (só metadado nesta fase) | null
allowed_classes    lista ⊆ {warrior, mage, rogue, cleric, ranger, paladin, bard};
                     vazio = todas
disponibilidade    { loja: bool, baus: bool, loot_monstro: bool }
price              int ≥ 0 (manual; UI mostra sugestão)
custom             true  (marca de item personalizado)
```

Observação sobre `extra_damages`: o modelo de jogo hoje tem um único
`extra_damage`/`extra_damage_types` (usado por munição incendiária). A Fase 1
introduz a **lista** `extra_damages`; a serialização para o jogo pode manter também
`extra_damage`/`extra_damage_types` da primeira linha por compatibilidade, mas a
soma em combate itera a lista completa.

## Formulário (seções empilhadas)

Ordem das seções no painel da sub-aba Armas:
1. **Identidade** — name, emoji, dropdown "Basear em…", id (auto/editável).
2. **Dano base** — quantidade + dado (d4/d6/d8/d10/d12) + categoria (cortante/
   contundente/perfurante).
3. **Atributo/manejo** — stat (FOR/DES) + finesse; manejo/alcance (corpo/lança/
   cajado/distância N/arremessável N) + `two_handed`.
4. **Bônus fixo** — magnitude + alvo (ataque **ou** dano).
5. **Dano elemental adicional** — quadro com linhas { quantidade, dado, tipo },
   botão "+ linha" e remover.
6. **Habilidade concedida** — dropdown de habilidade de Guilda/herói (grava só o
   id; rótulo "liga em fase futura").
7. **Restrição de classe** — multiseleção das classes (vazio = todas).
8. **Disponibilidade** — checkboxes loja / baús / loot de monstro.
9. **Preço** — campo editável + valor sugerido exibido ao lado.
10. **Imagem** — botão de upload de PNG (envia via WebSocket).
11. **Prévia** — card do item como no inventário + resumo textual do dano total
    (ex.: "1d8 cortante + 1d6 fogo, +1 no dano").

## Efeitos: funcional (passivo) vs. metadado nesta fase

**Funcionais em combate agora** (precisam valer de verdade):
- dado base, categoria, stat/finesse, manejo/alcance, `two_handed`;
- bônus fixo de **ataque** (`atk_bonus`) ou de **dano** (`damage_bonus`);
- **dano elemental extra** (lista `extra_damages`): ligado espelhando o caminho já
  existente de munição no `handle_attack` do jogador
  (`_ammo_extra_dmg`/`_ammo_extra_types`/`_ammo_damage_bonus`, `server.py` ~8737+ e
  a aplicação de dano logo abaixo), para que valha também em **corpo-a-corpo**, não
  só em ataque à distância. `_apply_damage_types` já existe e trata os tipos.

**Só gravado (liga em fase futura):**
- `granted_ability` (a habilidade de Guilda/herói concedida pelo item).

## Disponibilidade & integração

- **Loja (Ferreiro):** armas com `disponibilidade.loja=true` entram na lista de
  armas do ferreiro (`SHOP_WEAPONS` mesclado no boot), respeitando `allowed_classes`
  (o filtro por classe já existe na loja).
- **Baús/recompensas de masmorra:** armas com `disponibilidade.baus=true` passam a
  aparecer no **seletor de itens de baú/recompensa** do editor de masmorras. O
  catálogo de itens de baú (`_DUNGEON_ITEM_CATALOG`, hoje só `CHEST_ITEMS`) e o
  catálogo do editor passam a **incluir as armas custom**.
- **Loot de monstro:** armas com `disponibilidade.loot_monstro=true` entram no pool
  de loot procedural mesclado (o loot já resolve pelo catálogo mesclado). Wiring por
  **caminho simples** nesta fase: incluir o item no pool com peso/chance fixa. Se
  durante a implementação esse hook se mostrar mais custoso que o previsto, cai para
  "só gravado" (a flag persiste) e liga junto com as demais abas — decisão a
  confirmar na implementação, sem re-brainstorm.

## Imagem

- Novo handler WebSocket `upload_item_art` (espelha `upload_monster_art` →
  `_save_monster_art`, `server.py` ~19995 / ~20971), salvando o PNG em
  `assets/itens/<id>.png`.
- Render no jogo já funciona: `itemIconHTML` (`game.js` ~1669) procura
  `assets/itens/<id>.png` e cai no emoji em `onerror`. Nada a mudar no cliente do
  jogo para a imagem aparecer.

## Preço sugerido

- Fórmula transparente, isolada numa constante/função única no módulo do editor,
  fácil de recalibrar. Esboço (ajustável na implementação):
  `sugestao = round(base_por_dado_medio(die) + K_bonus*(|atk_bonus|+|damage_bonus|)
  + K_elem*soma_dos_dados_medios(extra_damages) + K_2m*two_handed)`.
- Exibida ao lado do campo `price`; o campo é sempre editável (manual vence).

## Validação (server, antes de salvar) — espelha `_validate_custom_monster`

- `id` slug válido e único entre os custom (não colidir com base → desambiguar);
- `name` não-vazio;
- `die` no formato `NdX` (N≥1, X ∈ {4,6,8,10,12});
- `categoria` ∈ {cortante, contundente, perfurante};
- `stat` ∈ {str_, dex};
- `manejo` válido; `range`/`throw_range` inteiros ≥1 quando aplicável;
- cada linha de `extra_damages`: `die` válido e `type` ∈ {fire,cold,lightning,acid,holy};
- `allowed_classes` ⊆ 6 classes;
- `price` inteiro ≥ 0;
- `granted_ability` (se presente) referencia uma habilidade conhecida.

## Testes — `tools/test_editor_itens.py` (server)

- validação aceita/rejeita casos limítrofes;
- persistência + `_apply_custom_items` mescla a arma no catálogo vivo;
- arma com `loja=true` aparece na lista do ferreiro e respeita `allowed_classes`;
- **principal (maior risco de regressão):** uma arma custom com `extra_damages`
  **soma o dano elemental** no `handle_attack` do jogador, em corpo-a-corpo, e o
  `_apply_damage_types` respeita resistências/fraquezas;
- bônus fixo de ataque e de dano aplicam no `handle_attack`;
- arma base **não** é alterada ao salvar um item copiado dela.

## Fora de escopo (fases seguintes)

- As outras 7 sub-abas (armaduras, escudos, anéis, botas, poções, arremessáveis,
  venenos);
- habilidades **ativáveis** concedidas por item, funcionais em combate;
- balanceador automático de itens;
- edição/sobrescrita de itens base do jogo.
