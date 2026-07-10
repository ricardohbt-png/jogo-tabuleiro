# Instrumentos do Bardo — Fase 1 (Framework + Primeiras Habilidades)

**Data:** 2026-07-10
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** design aprovado no brainstorm; pendente revisão do spec.

---

## 1. Visão geral

Instrumentos musicais são um novo tipo de **equipamento exclusivo do bardo**. Cada
instrumento ocupa um **slot dedicado** (separado da arma) e concede **uma habilidade
fixa de assinatura** (Harpa → Nota Cortante, Tambor → Acorde Trovejante, etc.). A
mesma habilidade escala por **três eixos independentes e livremente combináveis**:

- **Qualidade** — Velho, Rústico, Padrão, Refinado (define o nível básico dos números).
- **Origem** — Humana, Élfica, Anã (afixo cultural).
- **Encantamento** — Nenhum, Rúnico (efeito secundário único por instrumento).

"Lendário" **não é um valor de eixo** — é só o rótulo de um instrumento com os três
eixos no máximo (Refinado + uma Origem + Rúnico).

**Esta Fase 1 entrega o framework completo + 4 habilidades**, cobrindo toda a
variedade de modo/economia de ação. Origens não-Humanas, Encantamento Rúnico, as
demais habilidades, o Réquiem Final e a Gaita/Improviso ficam para as Fases 2–5. O
modelo de dados já inclui os campos `origem`/`encantamento` desde o dia 1, então as
fases seguintes são **puramente aditivas** (popular tabelas de modificadores).

### Decisões-chave do brainstorm

| Tema | Decisão |
|---|---|
| Progressão | 3 eixos combináveis (Qualidade × Origem × Encantamento); "Lendário" = rótulo do máximo |
| Instrumento→habilidade | 1 instrumento = 1 habilidade fixa; tiers só escalam números |
| Afixos "Escolha 1" | **Pré-fixados** no item na geração (como afixo de item mágico) |
| Recarga | **Nenhuma** — só o custo 🍖/💧 limita o reuso |
| 1 vs 2 mãos | Só economia de ação; sempre 1 slot |
| Aquisição | Loja da cidade + loot/baús/drops (sem Guilda, sem craft) |
| Loadout inicial | Henrique ganha arma real + instrumento inicial de baixa qualidade |
| Representação de stats | Tabela-base + camadas de modificador, computadas on-the-fly |

---

## 2. Modelo de dados

### 2.1 Instância de instrumento (item)

Um instrumento é um item comum (vai na bolsa, pode ser largado/lootado), com estes
campos além dos de item padrão (`id`, `nome`, `icon`, `buy_price`, …):

```python
{
    "id": "instrumento",          # categoria de item (todos compartilham; ver §5)
    "tipo_item": "instrumento",   # marca a categoria de slot
    "base": "harpa",              # harpa|tambor|sino|alaude (+ demais nas fases 2-5)
    "qualidade": "refinado",      # velho|rustico|padrao|refinado
    "origem": "humana",           # humana|elfica|ana  (Fase 1: sempre humana)
    "encantamento": "nenhum",     # nenhum|runico       (Fase 1: sempre nenhum)
    "refinado_bonus": "alcance",  # afixo pré-rolado, só se qualidade=refinado
    "origem_bonus": None,         # afixo pré-rolado, só se origem in (elfica, ana)
    "nome": "Harpa Refinada",     # derivado na geração (ver §2.4)
    "icon": "🎵",
}
```

Os **números efetivos** (alcance, dado de dano, custo, duração, raio, push, CD do
save) **não** são armazenados — são derivados por `_instrumento_stats(item)` (§2.3).
Isso é a decisão de arquitetura A: uma única fonte de verdade, sem explosão de
catálogo, rebalanceável por edição de tabela.

### 2.2 Tabela-base — `INSTRUMENTOS_BASE`

Novo dicionário autoritativo em `server.py`, no estilo de `GRIMORIO`/`GUILD_CATALOG`.
Cada base define a habilidade, o modo, as mãos, o custo-base (Padrão) e os stats-core
por qualidade **Velho/Rústico/Padrão** (Refinado = Padrão + afixo).

```python
INSTRUMENTOS_BASE = {
    "harpa": {
        "nome": "Harpa", "icon": "🎵", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Nota Cortante",
        "efeito": {"tipo": "nota_cortante", "save": "reflexos", "meia_no_sucesso": True},
        "custo_fome": 3, "custo_sede": 3,
        "afixos_validos": ["fome", "sede", "alcance"],   # filtro de afixos aplicáveis
        "stats": {
            "velho":   {"alcance": 3, "dano": "1d4"},
            "rustico": {"alcance": 4, "dano": "1d6"},
            "padrao":  {"alcance": 5, "dano": "2d6"},
        },
    },
    "tambor": {
        "nome": "Tambor de Guerra", "icon": "🥁", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Acorde Trovejante",
        "efeito": {"tipo": "acorde_trovejante", "save": "reflexos", "meia_no_sucesso": True},
        "custo_fome": 4, "custo_sede": 4,
        "afixos_validos": ["fome", "sede", "alcance"],   # "alcance" => +1 raio
        "stats": {
            "velho":   {"raio": 1, "dano": "1d2", "push": 0},  # falha: -1 movimento (sem push)
            "rustico": {"raio": 2, "dano": "1d4", "push": 1},
            "padrao":  {"raio": 2, "dano": "2d4", "push": 2},
        },
    },
    "sino": {
        "nome": "Sino", "icon": "🔔", "maos": 1, "modo": "ativada",
        "habilidade_nome": "Ecos Dolorosos",
        "efeito": {"tipo": "ecos_dolorosos"},
        "custo_fome": 2, "custo_sede": 2,
        "afixos_validos": ["fome", "sede", "duracao"],
        "stats": {
            "velho":   {"dano": "1",   "duracao": 2},   # "1" = 1 ponto fixo
            "rustico": {"dano": "1d3", "duracao": 2},
            "padrao":  {"dano": "1d4", "duracao": 3},
        },
    },
    "alaude": {
        "nome": "Alaúde", "icon": "🪕", "maos": 2, "modo": "passiva",
        "habilidade_nome": "Sinfonia Heroica",
        "efeito": {"tipo": "sinfonia_heroica"},
        "custo_fome": 0, "custo_sede": 0,   # herda o custo da Canção Heroica
        "afixos_validos": ["fome", "sede"], # afixo aplicado à manutenção da Canção
        "stats": {
            # quais atributos da Canção recebem o +1 extra
            "velho":   {"atributos": ["ataque"]},
            "rustico": {"atributos": ["ataque", "dano"]},
            "padrao":  {"atributos": ["movimento", "ataque", "dano", "defesa", "resistencia"]},
        },
    },
}
```

### 2.3 Derivação — `_instrumento_stats(item)`

Helper puro que devolve os números efetivos, aplicando as camadas na ordem
Qualidade → Refinado → Origem → Encantamento:

1. **Qualidade:** copia `stats[q]`, onde `q = "padrao"` se `qualidade == "refinado"`,
   senão a própria qualidade.
2. **Refinado:** se `qualidade == "refinado"`, aplica `refinado_bonus`
   (`fome`→−1 custo_fome; `sede`→−1 custo_sede; `alcance`→+1 alcance/raio;
   `duracao`→+1 duração).
3. **Origem (Fase 4, já plumbada):** aplica `origem_bonus` de forma análoga
   (`cd`→+1 CD do save; `alcance`/`duracao` como acima; Anã pode dar −1 fome **e** −1
   sede). Fase 1 nunca gera origem ≠ humana, então este passo é no-op.
4. **Encantamento (Fase 4, já plumbada):** anexa a flag do efeito Rúnico ao dict de
   stats (o dispatch da habilidade lê essa flag). Fase 1 nunca gera Rúnico.

Retorna um dict achatado: `{alcance?, raio?, dano, push?, duracao?, custo_fome,
custo_sede, save?, cd?, ...}`. `custo_fome`/`custo_sede` nunca descem abaixo de 0.

**CD do save:** `cd` = convenção de save de habilidade do bardo já existente
(base ~10 + modificador). O valor exato é fixado no plano de implementação, reusando
o helper de CD que as magias/habilidades usam. Origem Élfica soma +1 (Fase 4).

### 2.4 Nome derivado

`_instrumento_nome(item)` = `"{nome_base} {Qualidade}"` + sufixo de origem quando não
Humana + " Rúnica/o" quando Rúnico. Se os três eixos estão no máximo (Refinado +
origem ≠ humana + Rúnico), o rótulo vira **"{nome_base} Lendária/o {Origem}"** (ex.
"Harpa Lendária Élfica"). Fase 1 só produz "Harpa Velha/Rústica/Padrão/Refinada".

---

## 3. Slot e economia de ação

### 3.1 Novo slot de gear `"instrumento"`

O instrumento é um item físico com afixos — encaixa no sistema de **gear** existente,
não no de técnicas. Adicionamos `"instrumento"` a `GEAR_SLOTS`:

```python
GEAR_SLOTS = (..., "item2", "instrumento")
```

`p["gear"]["instrumento"]` guarda a instância equipada (ou `None`). Isso dá de graça:
persistência, o paperdoll/ficha, drag-and-drop e o roteamento de equipar/desequipar.

- **Bard-only:** equipar em `"instrumento"` é recusado para outras classes.
  `_slot_category_for_item` mapeia `tipo_item == "instrumento"` → slot `"instrumento"`.
- A ficha da cidade renderiza o slot de instrumento **apenas para o bardo**.
- Desequipar reverte via o caminho de gear existente (instrumento não tem
  `_apply_gear_effect` — a habilidade é lida ao vivo do slot, ver §4).

### 3.2 Economia de ação

O bardo tem `action_done` (ação principal) e `bonus_action_used`. Introduzimos um
flag por-turno **`instrumento_usado`** (resetado no início do turno, junto de
`action_done`):

| Mãos | Regra | Efeito no estado |
|---|---|---|
| **2 mãos** (`maos: 2`) | Atacar **OU** tocar (não ambos) | ativação exige `not action_done`; **marca** `action_done` **e** `instrumento_usado` |
| **1 mão** (`maos: 1`) | Atacar **E** tocar no mesmo turno | ativação exige só `not instrumento_usado`; **marca** só `instrumento_usado` (ação principal fica livre p/ atacar) |
| **passiva** (`modo: passiva`) | Sem ativação | não consome nada; efeito sempre-ligado enquanto equipado |

O flag `instrumento_usado` garante **no máximo 1 habilidade de instrumento por turno**
mesmo sem cooldown — o limitador de balanceamento junto do custo 🍖/💧.

O ataque com arma continua marcando `action_done` como hoje; logo, com instrumento de
2 mãos, atacar bloqueia tocar e vice-versa, automaticamente.

---

## 4. Handler de ativação — `handle_usar_instrumento`

Espelha `handle_usar_tecnica`. Mensagem nova cliente→servidor:
`usar_instrumento { target_id?, tx?, ty? }` (alvo conforme a habilidade).

Fluxo:

1. Fase = `playing`; `_is_turn(pid)`; jogador vivo; `class_id == "bard"`.
2. `inst = p["gear"].get("instrumento")`; existe e tem `modo == "ativada"`
   (passivas nunca chegam aqui).
3. Economia de ação conforme §3.2 (2 mãos: `not action_done`; 1 mão:
   `not instrumento_usado`).
4. `st = _instrumento_stats(inst)`; checa `fome >= st["custo_fome"]` e
   `sede >= st["custo_sede"]`; debita.
5. Marca os flags de ação (§3.2).
6. Despacha por `inst["base"]`/`efeito.tipo`:

### 4.1 `nota_cortante` (Harpa, 2 mãos)

Alvo único (`target_id`, monstro) até `st["alcance"]` casas (Chebyshev). Dano
`roll_dice(st["dano"])` sonoro; alvo faz save de Reflexos vs `st["cd"]`; **sucesso =
metade**. Reusa a maquinaria de save/`dice_roll` das magias de alvo único
(ex. `_executar_raio_congelante`). Mata via `_monster_dies` se `hp <= 0`.

### 4.2 `acorde_trovejante` (Tambor, 2 mãos)

AoE centrada no bardo, raio `st["raio"]` (Chebyshev). Todo monstro na área faz save
de Reflexos vs `st["cd"]`:
- **Falha:** dano cheio + empurrão de `st["push"]` casas para longe do bardo
  (reusa a lógica de empurrão existente; se `push == 0`, aplica −1 movimento até o
  próximo turno em vez de empurrar).
- **Sucesso:** metade do dano, sem empurrão.

Cada alvo atingido pode receber seu próprio `dice_roll`/narração (padrão das AoE).

### 4.3 `ecos_dolorosos` (Sino, 1 mão) — aura de retaliação

**Reinterpretação explícita** (as notas diziam "enquanto o bardo mantiver uma música
ativa"): modelado como **aura ativada com duração própria**, para caber no modelo
uniforme "habilidade ativada custa 🍖/💧" e no "sem cooldown" (a duração
autolimita). Ativa por `st["duracao"]` rodadas:
`p["ecos_ate"] = round_num + st["duracao"]`, `p["ecos_dano"] = st["dano"]`.
Enquanto ativa, todo monstro que **acertar o bardo em corpo a corpo** sofre
`roll_dice(st["dano"])` sonoro. Hook no ponto onde o dano de ataque de monstro
vs jogador é aplicado (`_execute_one_monster_attack` e o loop legado), condicionado a
`p["ecos_ate"] >= round_num`. Como é 1 mão, o bardo ainda pode atacar no mesmo turno.

> **Ponto para a revisão do spec:** se você preferir a leitura literal (Ecos só
> vale enquanto a Canção Heroica/uma música está ativa, sem ativação própria nem
> custo separado), digo e ajustamos — é uma troca pequena.

### 4.4 `sinfonia_heroica` (Alaúde, 2 mãos, **passiva**)

Não passa pelo handler. É lida ao vivo por `_cancao_nivel_atributo(bardo, attr_id)`:
se o bardo tem Alaúde equipado e `attr_id` está em `st["atributos"]`, soma +1 ao nível
daquele atributo da Canção (empilhando com a especialização Canção da Fase 1e). O
custo é o da própria Canção; o afixo Refinado (−1 fome/sede) reduz a **manutenção da
Canção** via o caminho `_cancao_custo_reducao` já existente.

---

## 5. Aquisição (loja + loot)

Fase 1 usa **instâncias pré-definidas** (SKUs autorados), não rolagem aleatória —
rolagem procedural de loot é um conforto da Fase 4. Cada SKU é uma instância fixa
(base + qualidade + humana + nenhum + afixo pré-rolado).

- **Loja da cidade:** algumas entradas de instrumento adicionadas ao catálogo da
  loja, com preço por qualidade (Velho < Rústico < Padrão < Refinado). Reusa
  `handle_shop_buy` → `_route_acquired_item` (bolsa-primeiro; instrumentos **não**
  auto-equipam — vão para a bolsa e o jogador equipa na ficha). Valores exatos de
  preço definidos no plano.
- **Loot/baús/recompensa:** instrumentos podem ser colocados em baús/decorações ou
  como `reward.items` de objetivos, referenciados por um id de SKU. Reusa
  `handle_take_from_chest`/`handle_take_from_decor` → `_route_acquired_item`.

`_route_acquired_item`/`_slot_category_for_item` reconhecem `tipo_item ==
"instrumento"` → categoria/slot `instrumento`; o passo de "resgate-equipa" trata o
slot de instrumento como bard-only (não-bardos nunca recebem resgate-equipa nesse
slot; o item fica na bolsa). Para simplicidade da Fase 1, instrumentos **sempre
roteiam para a bolsa** (sem auto-equipar), e o jogador equipa manualmente.

---

## 6. Loadout inicial de Henrique

Hoje: `weapon="instrumento"` (sem dano) + `off_hand="adaga"`. Novo:

- **Arma principal:** a adaga (ou outra arma leve) vira a arma real de dano.
- **Slot de instrumento:** um instrumento inicial de baixa qualidade (ex. **Sino
  Rústico** ou **Gaita Velha** — mas Gaita é Fase 5; então um dos 4 da Fase 1, ex.
  **Sino Rústico** 1 mão, para ele já poder atacar E tocar).
- `off_hand`: livre (pode receber a 2ª arma/escudo por compra).

Isso é uma **mudança de gameplay** (Henrique fica mais forte: passa a ter dano de
arma real + uma habilidade de instrumento). Intencional e aprovado.

Ajustar a criação do personagem (`CLASSES`/gear inicial em `server.py`) e as imagens
de ficha se necessário.

---

## 7. Cliente (`gameState.js` + `game.js`)

Seguindo a regra de arquitetura (estado primeiro, visual depois):

- **`gameState.js`:** `GS.usarInstrumento(target)`; getters
  `GS.instrumentoEquipado()`, `GS.instrumentoStats()` (espelho leve de
  `_instrumento_stats` para rótulos/descrições — o servidor é autoritativo),
  `GS.instrumentoDisponivel()` (economia de ação para habilitar o botão).
- **`game.js`:** 4º/novo botão no HUD do bardo "🎵 {Habilidade}" (só quando há
  instrumento ativado equipado e disponível); abre `openTargetModal` para
  `nota_cortante` (monstro no alcance) e é auto-centrado para `acorde_trovejante`
  (raio ao redor) e `ecos_dolorosos` (self). Rótulo mostra dano/alcance/custo
  derivados. Slot de instrumento na ficha da cidade (só bardo), com o drag-and-drop
  de gear existente.
- Passivas (Alaúde) não têm botão — o efeito aparece nos números da Canção.

---

## 8. Testes

`tools/test_instrumentos_bardo.py` (padrão dos outros `test_*` do servidor):

- `_instrumento_stats` por qualidade (Velho/Rústico/Padrão) e com afixo Refinado,
  para os 4 bases; custos nunca < 0.
- Economia de ação: 2 mãos bloqueia atacar↔tocar; 1 mão permite ambos; no máx. 1
  instrumento/turno; passiva não consome ação.
- Nota Cortante: dano cheio na falha, metade no sucesso; respeita alcance; mata.
- Acorde Trovejante: AoE + empurrão na falha, meia sem empurrão no sucesso; `push=0`
  aplica −1 movimento.
- Ecos Dolorosos: retaliação enquanto `ecos_ate` válido; expira; 1 mão não gasta a
  ação principal.
- Sinfonia Heroica: +1 nos atributos certos da Canção por qualidade; afixo Refinado
  reduz a manutenção; empilha com a espec. Canção (Fase 1e).
- Bard-only: outras classes não equipam nem ativam.
- Custo 🍖/💧: recusa sem recursos; debita no acerto.

---

## 9. Fora de escopo (Fases 2–5)

- **Fase 2:** Chamado do General (Trompa), Dueto Marcial (Lira), Dueto Fantasma (Flauta).
- **Fase 3:** Réquiem Final (Violino) — DoT escalonado + quebra de concentração.
- **Fase 4:** Origens Élfica/Anã (tabelas de afixo) + 9 efeitos Rúnicos + rótulo
  Lendário + rolagem procedural de loot.
- **Fase 5:** Improviso/Gaita (tabela 2d6 meta) + Encore/Grande Encore.

---

## 10. Questões em aberto (para a revisão do spec)

1. **Ecos Dolorosos:** aura ativada com duração (default deste spec) **ou** passiva
   condicionada a "música ativa" sem ativação/custo próprios? (§4.3)
2. **Instrumento inicial exato** de Henrique (§6): Sino Rústico? Outro dos 4?
3. **Preços de loja** por qualidade — a definir no plano.
