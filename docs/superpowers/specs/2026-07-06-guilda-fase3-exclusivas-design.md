# Guilda dos Heróis — Fase 3: Técnicas Exclusivas (Mago/Clérigo)

## Contexto

Continuação do roteiro da Guilda dos Heróis (ver memória
`guilda-especializacoes-roadmap.md`). Fases 0, 1a-1g e 2a-2e já mergeadas em
`master`. Esta fase introduz o **2º slot** de técnica (`tecnica_exclusiva`),
reservado a Mago (Pedro) e Clérigo (Lewis) — infraestrutura já existente desde
a Fase 0 (`handle_guild_equip`, campo `exclusiva` no catálogo) mas nunca usada
por nenhum item até agora.

7 técnicas, todas com `categoria:"tecnica"`, `classe:["mage","cleric"]`,
`exclusiva:True`, agrupadas nas faixas de recarga já existentes na UI (5/8/10
rodadas). Cada personagem só pode ter **uma** técnica exclusiva equipada por
vez (regra já garantida pelo slot único `tecnica_exclusiva`).

IDs internos com prefixo `tec_ex_` — deliberadamente distinto tanto da
Metamagia do Mago (Fase 1f: `aprimorar_ativo`/`estender_ativo`/
`fortalecer_ativo`, toggle permanente e gratuito, só Mago) quanto das técnicas
genéricas (`tecnica_*`). Os nomes de exibição colidem de propósito com os da
Metamagia (mesma inspiração de D&D 5e/Metamagia de Feiticeiro), mas são
sistemas independentes — ver decisão abaixo.

## Decisões de design (resolvidas em brainstorming)

1. **Convivência com a Metamagia do Mago (Fase 1f):** sistemas totalmente
   independentes. Se o Mago tiver o toggle gratuito `aprimorar_ativo` ligado E
   a técnica `tec_ex_aprimorar_magia` armada, os dois bônus de CD **se somam**
   no mesmo lançamento (mesmo raciocínio pra Estender e pra Empoderar/
   Fortalecer, que multiplicam em cadeia). Não há checagem de exclusividade
   entre os dois blocos de código.
2. **Preço em ouro:** reusa a mesma tabela por faixa de recarga já usada nas
   Fases 2b-2e — 5r=180, 8r=280, 10r=350 (mesmo custo de ouro de uma técnica
   genérica; a exclusividade de classe já é a limitação).
3. **Magia Geminada** vale para qualquer magia de alvo único (ofensiva OU
   buff em aliado), não só ofensiva. O 2º alvo é escolhido **na ativação**
   (`usar_tecnica`), não na hora de lançar a magia — modal combinado de
   aliados+monstros vivos (novo `alvo:"qualquer_vivo"`), exceto o próprio
   caster.
4. **Canalização Arcana** — "não pode ser interrompida" fica **inerte**: o
   jogo não tem hoje nenhum mecanismo de interromper um lançamento de magia
   (sem contramagia de monstro, sem reação de interrupção). A parte mecânica
   real implementada é só "ignora Silêncio". Documentar essa lacuna aqui, não
   criar mecanismo de interrupção novo.
5. **Magia Acelerada** — o lançamento **não marca `action_done`**: o jogador
   pode agir normalmente depois (atacar, lançar outra magia, etc.) no mesmo
   turno. Espelha o padrão já usado por Velocidade/Oportunidade
   (`_acao_bloqueada`), mas ao contrário daqueles (que dão crédito
   retroativo depois que a ação principal já foi gasta), aqui a própria
   magia acelerada é que não consome a ação — a checagem de bloqueio
   continua normal (`_acao_bloqueada`), só o `p["action_done"] = True` de
   depois é condicionado a não ter usado a técnica neste lançamento.
6. **Interação com Último Esforço (Fase 2e):** havia um TODO em `game.js`
   (perto de `podeUsar`, linhas ~9997-10000) perguntando se uma técnica
   exclusiva deveria ficar bloqueada durante os 2 mini-turnos do Último
   Esforço. Decisão: **não bloquear** — `GS.isMyTurn` já cobre a janela do
   Último Esforço, então a técnica exclusiva funciona normalmente ali, sem
   checagem extra. O TODO é removido (resolvido, não implementado).

## Data model

### `GUILD_CATALOG` (server.py) — 7 novas entradas

```python
"tec_ex_aprimorar_magia": {
    "id": "tec_ex_aprimorar_magia", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True,
    "linha": None, "nivel": None, "requer": None,
    "preco": 180, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 5,
    "nome": "Aprimorar Magia", "icon": "🎯",
    "desc": "A próxima magia recebe +1 na CD do teste de resistência "
            "(vale p/ magias de área também).",
    "efeito": {"tipo": "tec_ex_aprimorar"},
},
"tec_ex_estender_magia": {
    "id": "tec_ex_estender_magia", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True,
    "linha": None, "nivel": None, "requer": None,
    "preco": 180, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 5,
    "nome": "Estender Magia", "icon": "⏱️",
    "desc": "A próxima magia tem +1 rodada de duração, ou +1 quadrado de "
            "alcance se não tiver duração.",
    "efeito": {"tipo": "tec_ex_estender"},
},
"tec_ex_canalizacao_arcana": {
    "id": "tec_ex_canalizacao_arcana", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True,
    "linha": None, "nivel": None, "requer": None,
    "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
    "nome": "Canalização Arcana", "icon": "🌀",
    "desc": "A próxima magia ignora os efeitos de Silêncio.",
    "efeito": {"tipo": "tec_ex_canalizacao_arcana"},
},
"tec_ex_empoderar_magia": {
    "id": "tec_ex_empoderar_magia", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True,
    "linha": None, "nivel": None, "requer": None,
    "preco": 280, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 8,
    "nome": "Empoderar Magia", "icon": "💥",
    "desc": "A próxima magia ofensiva causa 50% a mais de dano (×1,5).",
    "efeito": {"tipo": "tec_ex_empoderar"},
},
"tec_ex_magia_geminada": {
    "id": "tec_ex_magia_geminada", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True, "alvo": "qualquer_vivo",
    "linha": None, "nivel": None, "requer": None,
    "preco": 280, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 8,
    "nome": "Magia Geminada", "icon": "👯",
    "desc": "Escolha um 2º alvo agora; a próxima magia de alvo único também "
            "o afeta, se estiver no alcance da magia. Não funciona em "
            "magias de área.",
    "efeito": {"tipo": "tec_ex_geminada"},
},
"tec_ex_canalizacao_perfeita": {
    "id": "tec_ex_canalizacao_perfeita", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True,
    "linha": None, "nivel": None, "requer": None,
    "preco": 280, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 8,
    "nome": "Canalização Perfeita", "icon": "🎴",
    "desc": "Na próxima magia de alvo único, o alvo testa resistência com "
            "desvantagem.",
    "efeito": {"tipo": "tec_ex_canalizacao_perfeita"},
},
"tec_ex_magia_acelerada": {
    "id": "tec_ex_magia_acelerada", "categoria": "tecnica",
    "classe": ["mage", "cleric"], "exclusiva": True,
    "linha": None, "nivel": None, "requer": None,
    "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
    "nome": "Magia Acelerada", "icon": "⚡",
    "desc": "A próxima magia é lançada como Ação Bônus — não gasta sua "
            "ação principal.",
    "efeito": {"tipo": "tec_ex_acelerada"},
},
```

### Flags no jogador (inicializadas em `False`/`None`, junto das demais técnicas)

```python
"tec_ex_aprimorar_armado": False,
"tec_ex_estender_armado": False,
"tec_ex_canalizacao_armado": False,
"tec_ex_empoderar_armado": False,
"tec_ex_geminada_alvo2_id": None,
"tec_ex_canalizacao_perfeita_armado": False,
"tec_ex_acelerada_armado": False,
```

Todas resetadas no bloco de fim de turno onde `aprimorar_ativo` etc. já são
zeradas (~server.py:11372-11374) — expiram se não usadas no turno em que
foram armadas, igual às demais técnicas "arma e age".

## Protocolo

Nenhuma mensagem nova. `usar_tecnica` já aceita `target_id` opcional — a
Magia Geminada o usa para o 2º alvo (any living player/monster id, validado
como "vivo e não é você mesmo" no momento da ativação). As outras 6 técnicas
não passam `target_id` (flags simples).

### Generalização necessária: `classe` como lista

Hoje `classe` no catálogo é `None` ou um `class_id` único, checado por
igualdade em dois lugares. Ambos precisam aceitar lista:

- **Servidor** `handle_guild_buy` (server.py:4132):
  `item["classe"] is not None and item["classe"] != p.get("class_id")`
  → passa a tratar `classe` como `None`, string ou lista/tupla.
- **Cliente** `guildCatalogFor` (src/gameState.js:1123):
  `i.classe == null || i.classe === classId`
  → mesmo ajuste (`Array.isArray` + `includes`).

Comportamento para entradas existentes (classe como string única ou `None`)
fica byte-idêntico.

## Lógica de servidor (`handle_magia`)

Hoje o bloco de Metamagia (dc_bonus/dur_bonus/dmg_mult) só roda para
`is_mage`. As técnicas exclusivas precisam rodar pra **mage e cleric** — vira
um bloco novo, paralelo ao da Metamagia, sem tocar no bloco existente.

1. **Silêncio:** `if self._em_silencio(p) and not p.get("tec_ex_canalizacao_armado")` na checagem já existente no topo de `handle_magia`.
2. **Ação bloqueada:** checagem de `_acao_bloqueada(p)` continua idêntica. No
   fim de `handle_magia`, `p["action_done"] = True` só roda
   `if not usou_acelerada` (captura o valor do flag ANTES de limpá-lo).
3. **CD (Aprimorar):** se `tec_ex_aprimorar_armado` e a magia tem `"save"`,
   soma +1 em `p["_mm_dc_bonus"]` (mesmo campo temporário que o Aprimorar do
   1f já usa — os dois bônus se somam naturalmente, já que é só um
   acumulador lido por `_dif_magia`).
4. **Duração/Alcance (Estender):** se `tec_ex_estender_armado`: se a magia
   tem `"duracao"`, soma +1 em `dur_bonus` (mesma variável que o Estender do
   1f já popula — soma). Senão (magia sem duração, ex. Bola de
   Fogo/Relâmpago/Raio Congelante), soma +1 num novo `alcance_bonus`,
   passado para `_executar_magia_grimorio`.
5. **Dano (Empoderar):** se `tec_ex_empoderar_armado` e
   `self._magia_tem_dano(magia)`: `dmg_mult *= 1.5` (multiplica em cadeia
   com o Fortalecer do 1f, se ambos ativos).
6. **Geminada:** após a execução normal (`_executar_magia_grimorio` com o
   alvo principal), se `tec_ex_geminada_alvo2_id` setado e
   `magia.get("tipo") in ("alvo", "alvo_aliado", "buff_aliado")`, valida o
   2º alvo (`_geminada_alvo2_valido`) e, se válido, reexecuta
   `_executar_magia_grimorio` com `data` clonado e `target_id` trocado pelo
   2º alvo — sem cobrar slot/fome/sede de novo (já pago uma vez).
7. **Desvantagem no save (Canalização Perfeita):** seta uma flag temporária
   (`p["_tec_save_desvantagem"] = True`) antes de `_executar_magia_grimorio`,
   igual ao padrão do `_mm_dc_bonus`; os executores de magia de alvo único
   que chamam `_save_mostrado`/`_testar_save` passam
   `desvantagem=caster.get("_tec_save_desvantagem", False)`. Hoje só
   `_executar_raio_congelante` precisa desse fio (única magia de alvo único
   com save implementada); os demais executores de alvo único que vierem a
   ser implementados devem seguir o mesmo padrão.
8. Limpa todos os 7 flags no fim de `handle_magia` (consumidos, usados ou
   não aplicáveis à magia lançada).

### Novo parâmetro `desvantagem` em `_testar_save`/`_save_mostrado`

```python
def _testar_save(self, alvo, tipo_save, dificuldade, extra_mod=0, fonte=None, desvantagem=False):
    bonus = (...)  # inalterado
    d20 = min(random.randint(1, 20), random.randint(1, 20)) if desvantagem else random.randint(1, 20)
    total = d20 + bonus
    return (total >= dificuldade), d20, bonus, total
```

`desvantagem=False` por padrão — todos os outros ~15 call sites existentes
ficam byte-idênticos.

### Novo parâmetro `alcance_bonus` em 3 executores

`_executar_magia_grimorio`, `_executar_bola_fogo`, `_executar_relampago`,
`_executar_raio_congelante` ganham `alcance_bonus=0`, somado à fórmula de
alcance já existente em cada um (`alcance_base + alcance_escala*(nivel-1) +
alcance_bonus`).

### Helper novo

```python
def _geminada_alvo2_valido(self, caster, magia, alvo2):
    """True se o 2º alvo da Magia Geminada é elegível: vivo, no alcance da
    magia a partir do caster, e do tipo certo (monstro p/ magia ofensiva,
    aliado p/ magia de buff)."""
```

## Cliente (`game.js`)

- Nenhuma seção nova na UI da Guilda — `_renderGuild`/`_secTecnicas` já
  agrupam por `recarga_rodadas`; as 7 técnicas caem nas faixas 5/8/10 ao
  lado das genéricas. Adicionar um selo "Mago/Clérigo" em `_guildItemRow`
  quando `i.exclusiva` for `true` (cosmético).
- No dispatch de clique do botão do 4º slot (~game.js:10018-10041), novo
  branch `cat.alvo === 'qualquer_vivo'`: lista combinada de
  `state.players` vivos (exceto eu) + `state.monsters` vivos, abre
  `openTargetModal(...)` (o parâmetro `kind` já não é usado internamente
  pela função — sem mudança necessária ali).
- Remove o TODO resolvido em game.js (~linhas 9997-10000): não há
  restrição de Último Esforço a implementar.

## Testes

Novo arquivo `tools/test_guilda_fase3_espec.py` (harness custom, mesmo
padrão dos demais `test_*_espec.py`), cobrindo:

- Cada uma das 7 técnicas isoladamente (compra, equipe no slot exclusivo,
  ativação, efeito no próximo lançamento de magia, consumo do flag).
- Restrição de classe: guerreiro não pode comprar nem equipar; Mago e
  Clérigo podem ambos comprar a mesma técnica (prova do `classe` como
  lista, nos dois lados — compra no servidor e catálogo no cliente
  indiretamente via `guildCatalogFor` se houver teste de integração
  client-side, senão só servidor).
- Empilhamento Aprimorar/Estender/Empoderar da Fase 3 com a Metamagia do
  1f no mesmo lançamento (Mago).
- Estender: caminho de duração (Visão no Escuro/Manto de Escuridão) e
  caminho de alcance (Raio Congelante/Bola de Fogo/Relâmpago).
- Geminada: aplica no 2º alvo válido; não aplica se fora de alcance, alvo
  morto, tipo errado (ex. arma numa magia de área), ou sem 2º alvo escolhido.
- Canalização Perfeita: prova estatística/determinística (mock de dados) de
  que o save do alvo usa a pior de 2 rolagens.
- Canalização Arcana: lança normalmente numa zona de Silêncio.
- Magia Acelerada: `action_done` permanece `False` após o lançamento,
  permitindo atacar/lançar de novo no mesmo turno.
- Recarga/custo de 🍖💧/ouro por técnica batendo com a tabela.
- Técnica exclusiva utilizável durante o Último Esforço (sem regressão).

Suíte completa do projeto roda ao final para garantir zero regressão (em
especial `test_mago_espec.py`, `test_tecnicas_espec.py`, `test_guilda.py`).
