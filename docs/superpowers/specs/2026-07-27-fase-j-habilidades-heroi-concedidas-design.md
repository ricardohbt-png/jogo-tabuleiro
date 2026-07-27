# Fase J: as habilidades de herói restantes concedidas por item

**Data:** 2026-07-27
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Antecessora direta:** Fase I (habilidades concedidas por item — Guilda completa + amostra de 3 habilidades de herói)

## Objetivo

Estender a concessão por item às **11 habilidades de herói restantes que são viáveis**,
completando o padrão validado na Fase I. Ao fim, 14 habilidades de herói (3 da amostra + 11)
podem ser concedidas por um item equipado, além de todas as técnicas e especializações da Guilda.

## Contexto

A Fase I estabeleceu o mecanismo:

- `_habilidades_concedidas(player)` — ids de `granted_ability` do `gear` equipado;
- travas de classe relaxadas de `class_id != X` para
  `class_id != X and <id> not in _habilidades_concedidas(p)`;
- `GameRoom.GRANTED_HERO_SKILLS` (mapa `id → (classe, skill_id)`) + `_granted_hero_skills(p)`
  injetado no `push_state`, que manda a **definição real** da skill ao cliente;
- o cliente renderiza o botão da classe de origem (`_rogueSkillBtn`/`_paladinSkillBtn`);
- `_granted_ability_valida` rejeita ids não suportados;
- o editor lista as opções suportadas (`GRANTED_HERO_IDS`).

Verificado nesta análise: os **quatro** helpers de botão do cliente
(`_rogueSkillBtn`, `_paladinSkillBtn`, `_clericSkillBtn`, `_bardSkillBtn`) **não leem
`class_id`** — são agnósticos de classe, então o mecanismo escala sem adaptação.

### Classificação das habilidades restantes

**Tier 1 — trava única, lógica genérica (6):** Cura, Cura em Área, Purificação e Ressurreição
(clérigo — custo é fome/sede, e os tetos `_cura_teto`/`_purif_tipos` caem para o base);
Criar Armadilha e Veneno Rápido (ladino — as fórmulas da Guilda e a capacidade de cargas já
gateiam sozinhas).

**Tier 2 — trava + desativar/upkeep (5):** Golpe Sagrado, Protetor, Regeneração Divina e
Guerreiro da Luz (paladino — sustentadas, com handler de desativar e/ou upkeep também
gateados); Provocação (bardo).

**Tier 3 — acoplado a maquinário próprio (fora de escopo):** Canção Heroica (buffs + upkeep +
interação com instrumentos), Animar Mortos (slots de controle, ND, fase de servos), metamagias
(atadas ao lançamento de magia), Usar Instrumento (exige um instrumento no `off_hand`, item
bard-only), Mira Certeira / Golpe Devastador / Fúria Berserker (não têm handler — são armadas no
cliente e aplicadas em `handle_attack` via a lista `buffs`), Ataque Furtivo (passiva) e as três
magias de MP legadas (`fireball`/`ice_lance`/`magic_shield`, inertes).

### Lacuna da Fase I encontrada nesta análise

`_processar_inicio_turno_luccas` — o upkeep de Detectar Armadilhas e Esconder nas Sombras — é
travado por `class_id != "rogue"`. Um herói de outra classe com essas habilidades **concedidas**
(Fase I) as ativa normalmente, mas **nunca paga a manutenção** (💧-1 / 🍖-1 por turno) e nunca é
interrompido por falta de recursos. É um bug favorável ao jogador, corrigido nesta fase.

## Decisões de design (aprovadas)

1. **Escopo = Tier 1 + Tier 2** (11 habilidades). Tier 3 fica de fora, com os motivos acima.
2. **Helper DRY**: extrair `_pode_hab_heroi(player, cls_id, aid)` e **retrofitar** as 3 travas da
   Fase I — um único padrão no código inteiro, em vez da condição de duas linhas repetida 14×.
3. **Gate por habilidade em `handle_acao_livre_richard`**: esse handler tem UMA trava cobrindo
   duas habilidades (Regeneração Divina e Guerreiro da Luz), despachadas depois por
   `habilidade_id`. A trava passa a ser lida **após** o `habilidade_id`, usando
   `hero_paladin_<habilidade_id>` — conceder uma não libera a outra.
4. **Sem exportar a lista pelo catálogo**: `tools/editor_catalog.js` (gerado, ~200 KB) está no WIP
   do usuário; regenerá-lo colidiria. A lista do editor (`GRANTED_HERO_IDS`) continua explícita, e
   um **teste de sincronia** garante que ela não divirja de `GRANTED_HERO_SKILLS`.

## Arquitetura

### 1. Servidor (`server.py`) — *partial staging* obrigatório

O usuário reworka `server.py` em paralelo. **Nunca** `git add server.py`. Esta fase toca **muitas
regiões espalhadas**; extrair hunk a hunk conferindo a vizinhança, e — quando um hunk misturar
código do WIP — **escrever o patch à mão contra o HEAD** e validar a versão staged
(`git show :server.py` + `ast.parse`). Foi assim que a Fase I foi commitada.

**Helper novo** (junto de `_habilidades_concedidas`):

```python
def _pode_hab_heroi(player, cls_id, aid):
    """True se o jogador é da classe dona da habilidade OU se um item equipado a
    concede (Fase I/J). Portão único de todas as habilidades de herói concedíveis."""
    return player.get("class_id") == cls_id or aid in _habilidades_concedidas(player)
```

**Retrofit das 3 travas da Fase I** (`handle_detectar_armadilhas`, `handle_esconder_sombras`,
`handle_imposicao_maos`) para `if not _pode_hab_heroi(p, "<classe>", "<id>"):`.

**Travas relaxadas (14 sites):**

| Site | Habilidade concedida |
|---|---|
| `handle_cura` | `hero_cleric_cura` |
| `handle_cura_area` | `hero_cleric_cura_area` |
| `handle_purificacao` | `hero_cleric_purificacao` |
| `handle_ressurreicao` | `hero_cleric_ressurreicao` |
| `handle_criar_armadilha` | `hero_rogue_criar_armadilha` |
| `handle_veneno_rapido` | `hero_rogue_veneno_rapido` |
| `_processar_inicio_turno_luccas` | qualquer das 4 sustentadas do ladino (ver abaixo) |
| `handle_golpe_sagrado` | `hero_paladin_golpe_sagrado` |
| `handle_desativar_golpe_sagrado` | idem |
| `handle_protetor` | `hero_paladin_protetor` |
| `handle_desativar_protetor` | idem |
| `handle_acao_livre_richard` | `hero_paladin_regeneracao_divina` \| `hero_paladin_guerreiro_luz` (por `habilidade_id`) |
| `_processar_manutencao_richard` | qualquer das sustentadas do paladino |
| `handle_provocacao` | `hero_bard_provocacao` |

**Upkeep (os dois `_processar_*`)** não são "uma habilidade": rodam no início do turno e cobram a
manutenção de várias. A trava passa a ser "é da classe **ou** tem alguma das habilidades
sustentadas daquela classe concedida". Helper auxiliar:

```python
def _tem_alguma_hab_heroi(player, cls_id, aids):
    """True se o jogador é da classe OU tem qualquer um dos ids concedidos.
    Usado pelos upkeeps, que cobrem várias habilidades sustentadas de uma vez."""
    if player.get("class_id") == cls_id:
        return True
    return bool(set(aids) & _habilidades_concedidas(player))
```

- `_processar_inicio_turno_luccas` → `("rogue", {detectar_armadilhas, esconder_sombras})`
- `_processar_manutencao_richard` → `("paladin", {golpe_sagrado, protetor, regeneracao_divina, guerreiro_luz})`

**`_provocador`** (usado pelos bônus da Provocação) exige hoje `class_id == "bard"`. Passa a
aceitar também quem tem `hero_bard_provocacao` concedida — senão a provocação concedida
aplicaria a desvantagem mas perderia os bônus associados.

**`GRANTED_HERO_SKILLS`** cresce de 3 para 14 entradas (as 3 da Fase I + as 11 desta).
`_granted_hero_skills` e `_granted_ability_valida` derivam do mapa — **não mudam**.

### 2. Cliente (`game.js`) — 2 linhas

O bloco da Fase I ganha os dois despachos que faltam:

```javascript
    else if(sk.granted_origem === 'cleric')  sl.appendChild(_clericSkillBtn(me, sk));
    else if(sk.granted_origem === 'bard')    sl.appendChild(_bardSkillBtn(me, sk));
```

### 3. Editor (`tools/editor_items_editor.js`)

`GRANTED_HERO_IDS` cresce de 3 para 14 ids. Nenhuma outra mudança (o filtro/agrupamento da Fase I
já cobre).

### 4. Testes

**`tools/test_editor_itens.py`** — seção `[J1]`–`[J6]`:

- [J1] **clérigo**: um guerreiro com cada um dos 4 milagres concedidos consegue usá-los (cura sobe
  o HP do alvo; purificação remove veneno; ressurreição revive) e é recusado sem o item.
- [J2] **ladino**: criar armadilha e veneno rápido funcionam para outra classe com o item, e são
  recusados sem ele.
- [J3] **paladino**: Golpe Sagrado e Protetor ativam **e desativam** com o item; Regeneração
  Divina e Guerreiro da Luz pelo `handle_acao_livre_richard`; conceder **uma** não libera a outra.
- [J4] **bardo**: Provocação funciona com o item; `_provocador` reconhece o provocador não-bardo.
- [J5] **upkeep (fix da Fase I)**: um não-ladino com Detectar concedido **paga** a manutenção no
  início do turno; um não-paladino com uma sustentada concedida idem.
- [J6] **sincronia**: `GRANTED_HERO_IDS` (lido de `tools/editor_items_editor.js`) == as chaves de
  `GameRoom.GRANTED_HERO_SKILLS`; e `_granted_ability_valida` aceita os 14 ids.

Rodar da raiz; verificar o estado **committado** em worktree isolado — foi a verificação isolada
que revelou o gate inline na Fase I.

**Estado conhecido do working tree (NÃO é regressão desta fase):** com o WIP do usuário,
`tools/test_editor_itens.py` aborta na seção `[7]` (lojas por cidade). Verificar seções novas
importando o módulo e chamando as funções diretamente. Também pré-existentes:
`tools/test_roteamento_itens.py` e 1 teste flaky em `tools/test_devorador.py`.

## Fora de escopo

- **Tier 3** (listado acima) — exigiria refatorar o maquinário de cada classe.
- Conceder habilidades a monstros (o mestre tem o próprio caminho).
- Rebalanceamento: um item que concede Ressurreição é forte por definição; o equilíbrio é
  responsabilidade do autor do item, como no resto do Editor de Itens.

## Critérios de aceite

- As 11 habilidades funcionam para heróis de outra classe quando concedidas por item, e seguem
  bloqueadas sem o item.
- As sustentadas (paladino) podem ser desativadas e **pagam upkeep**; o mesmo vale para as duas do
  ladino concedidas na Fase I (lacuna corrigida).
- Conceder Regeneração Divina não libera Guerreiro da Luz (e vice-versa).
- O HUD mostra o botão correto para as 4 classes de origem.
- O editor lista as 14 habilidades; o teste de sincronia passa.
- Testes `[J1]`–`[J6]` verdes no estado committado isolado, sem regressão em `test_guilda.py` nem
  nas seções `[I*]`.
