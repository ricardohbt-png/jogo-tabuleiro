# Ficha do monstro para o Mestre — design

Data: 2026-08-04
Branch de origem: `feat/instrumentos-bardo-fase5`

## Problema

No Modo Mestre, quando um monstro entra na janela Manual, o mestre opera dois
painéis flutuantes separados: o `#hud-mestre` (topo-direita) tem mover, atacar e
encerrar; a `#ficha-monstro` (baixo-direita) tem habilidades, itens e leitura.
No mesmo turno o mestre pula entre as duas caixas, e nenhuma delas mostra o que
já foi gasto.

Três lacunas de regra, além da organização:

1. **Ataques.** `handle_mestre_atacar_monstro` usa sempre `attacks[0]` e permite
   um ataque por turno. A IA (`_monster_execute_attacks`, server.py:20306)
   executa **toda** a lista `attacks[]`, cada entrada repetida `num_attacks`
   vezes. O Lobisomem rola 3 vezes no automático e 1 vez no Manual — o monstro
   do mestre é mais fraco que o mesmo monstro sob IA.
2. **Habilidades.** O gate `_habilidade_ativavel_manual` (server.py:20778) libera
   10 habilidades e barra 16 nas fichas do jogo. O mestre não lança Silêncio,
   Amaldiçoar, Abençoar, Bola de Fogo, Medo, Manto de Escuridão nem Dominar
   Morto-Vivo — todas já implementadas.
3. **Relógio.** O timeout anti-AFK de 60 s corre invisível e, ao estourar, chama
   `gm_phase` cheio mesmo se o mestre já moveu e atacou: **turno duplo**.

## Decisões

| Tema | Decisão |
|---|---|
| Escopo | UI + as regras faltantes (cliente e servidor) |
| Layout | Caixa flutuante única à direita com 3 abas |
| Ataques | Granulares por golpe, com `num_attacks` como cargas, alvos separáveis |
| Habilidades | Todas ativáveis, exceto as 3 `encantar_*` (ver "Fora de escopo") |
| Economia | Respeita o `action_type` de cada ficha |
| Relógio | Inatividade visível, reiniciado a cada ação do mestre |

## Levantamento das 13 habilidades "IA apenas"

Verificado uma a uma:

- **7 são magias e todas já estão implementadas** (`GRIMORIO_IMPLEMENTADAS`):
  `silencio`, `amaldicoar`, `abencoar`, `bola_fogo`, `medo`, `manto_escuridao`,
  `dominar_morto_vivo`. Caminho genérico já existente:
  `monster_spells` → `_monster_try_spell` → `_executar_magia_grimorio`.
- **2 são blocos embutidos na rotina de IA do monstro**, extraíveis:
  `golpe_brutal` (Ogro, server.py:22432) e `desaparecer_nas_sombras`
  (Bugbear, server.py:22334).
- **1 já é alcançável por outro caminho:** `arremesso` (Goblin Combatente) é
  arremessar um item de bolsa, que o mestre já faz pela seção Itens
  (`mestre_usar_item`). Precisa só ficar óbvio na UI.
- **3 não existem em lugar nenhum:** `encantar_vampirico`,
  `encantar_area_vampirico`, `encantar_supremo_vampirico`. Não há implementação
  nem para a IA — são dados inertes nas fichas dos vampiros.

## Layout

Uma caixa flutuante à direita, ~300px, substituindo `#hud-mestre` e
`#ficha-monstro`. Três abas:

- **🎯 Ativo** — a ficha do monstro em foco.
- **📋 Monstros** — lista, seleção em lote, botões de modo, alvo do Semi.
- **⚠️ Mestre** — reforços e falas.

### Aba Ativo, de cima para baixo

1. Cabeçalho: emoji, nome, sala/ND, selo do modo, relógio.
2. **Barra de recursos** (só na janela Manual): Movimento `n/max`, Ação, Bônus.
3. Vitais: barra de PV, CA, movimento, bônus de ataque base.
4. **Condições**: envenenado, amedrontado, atordoado, movimento reduzido.
5. Atributos e saves numa linha.
6. **Ataques** — uma linha por entrada de `attacks[]`, com as cargas
   (`num_attacks`) como bolinhas.
7. **Magias e Habilidades** — uma linha cada, com usos e recarga.
8. **Itens** — bolsa (`equipment_consumables`).
9. **Equipado** e **Passivas** — colapsados.
10. Rodapé fixo: **Encerrar monstro**.

### Regras visuais

- Cor por família: vermelho ataque, roxo magia/habilidade, azul item.
- Selo de custo por linha (AÇÃO / BÔNUS / LIVRE), derivado do `action_type`.
- Linha indisponível fica visível, esmaecida, com o motivo ("recarga: 2
  rodadas", "sem usos", "ação já gasta", "não implementada").
- Monstro que não é o da vez abre a mesma aba em leitura: sem barra de
  recursos, sem botões, sem rodapé.
- Monstro dormente aparece na lista em itálico e não é selecionável.

## Servidor

### Economia de ação

`_master_acted` (bool) → `master_acao`: `None` | `"ataque"` | `"habilidade"` |
`"item"`. `_master_bonus_acted` → `master_bonus` (bool).

Helper novo `_custo_acao_ability(ab)`:

| `action_type` | custo |
|---|---|
| `acao`, `magia`, `ataque` | principal |
| `acao_bonus` | bônus |
| `acao_livre` | nenhum |

Comprometer a ação principal com ataques bloqueia habilidades de ação principal
e vice-versa. As cargas restantes seguem gastáveis.

### Ataques granulares

`_master_manual_window` monta `master_attack_charges = {índice: num_attacks}` a
partir de `attacks[]`.

`mestre_atacar_monstro` ganha o campo **`attack_index`** (ausente = 0, então
cliente antigo não quebra). Cada uso debita uma carga daquele índice e marca
`master_acao = "ataque"`.

Mira: clique num herói direto no tabuleiro usa o **primeiro golpe com carga**
(caminho rápido, comportamento atual); clique na linha do golpe na ficha arma
aquele golpe e o próximo clique escolhe o alvo.

### Habilidades

`_habilidade_ativavel_manual` passa a aceitar `action_type == "magia"` com id em
`GRIMORIO_IMPLEMENTADAS`, mais `golpe_brutal` e `desaparecer_nas_sombras`.

Três extrações, seguindo o precedente de `_ativar_editor_ability` (SP2):

| extrair de | para | usado por |
|---|---|---|
| trecho de `_monster_try_spell` que debita `spell_uses`/`spell_cooldowns` e chama `_executar_magia_grimorio` | `_lancar_magia_monstro(m, sid, data)` | IA (escolhe alvo) + mestre (alvo escolhido) |
| bloco do Ogro (server.py:22432) | `_ativar_golpe_brutal(m)` | IA + mestre |
| bloco do Bugbear (server.py:22334) | `_ativar_desaparecer_sombras(m)` | IA + mestre |

As 3 `encantar_*` viajam no payload marcadas `nao_implementada`.

### Relógio de inatividade

`_master_manual_timeout` deixa de ser um sono único: cada handler do mestre
chama `_reiniciar_timer_manual()` ao terminar. O `game_state` leva o `deadline`
para o cliente desenhar o contador.

**Correção do turno duplo:** no timeout, chamar `gm_phase` apenas se o monstro
não fez nada; se o mestre já moveu ou agiu, a janela só fecha. Mesma regra em
`_on_master_disconnect`.

### Payload

Bloco novo em `game_state`, agregando o que hoje são campos soltos:

```
master_manual: { mid, moves_left, moves_max, acao, bonus, deadline, attack_charges }
```

`master_manual_mid` e `master_manual_reach` continuam no payload como estão —
o bloco novo é aditivo, para não quebrar leitores existentes.

As condições já viajam no dict do monstro (`push_state` serializa o dict
inteiro) — o cliente só precisa lê-las.

## Invariante

Sem mestre conectado, ou com o monstro em modo `auto`, o comportamento tem de
permanecer **byte-idêntico** ao jogo sem Modo Mestre. É a premissa de todas as
camadas anteriores e a razão de as extrações serem compartilhadas em vez de
duplicadas.

## Testes

Servidor, em `tools/test_modo_mestre.py` (hoje vai até a seção `[28]`):

- **`[29]` Ataques granulares** — `attacks[]` de duas entradas com `num_attacks`
  2 e 1: confirma 3 cargas, débito por ataque, golpes em heróis diferentes,
  recusa da 4ª tentativa.
- **`[30]` Economia por `action_type`** — magia após atacar recusada; item
  `acao_bonus` após atacar aceito; `acao_livre` não gasta; atacar após magia
  recusado.
- **`[31]` Magias do mestre** — Silêncio no alvo escolhido; débito de
  `spell_uses`; recarga bloqueia o segundo lançamento; alvo fora de alcance
  recusa sem gastar.
- **`[32]` Extrações** — `_ativar_golpe_brutal` e `_ativar_desaparecer_sombras`
  com efeito idêntico via IA e via mestre; monstro `auto` sem mestre
  byte-idêntico.
- **`[33]` Relógio** — cada ação empurra o `deadline`; timeout sem ação chama a
  IA; timeout **com** ação do mestre apenas fecha a janela.

Cliente: sem harness no projeto. Verificação é smoke in-app com dois
navegadores (um herói, um mestre), como nas camadas anteriores do Modo Mestre.

## Fora de escopo

- **As 3 habilidades `encantar_*`** dos vampiros. Não existem nem para a IA;
  torná-las ativáveis é projetar a mecânica do zero (efeito, save, duração, o
  que um herói encantado faz). Trabalho separado. A ficha passa a rotulá-las
  "não implementada", que é a verdade.
- Redesenho do fluxo de iniciativa ou dos modos Auto/Semi.
- Multiataque para heróis.
