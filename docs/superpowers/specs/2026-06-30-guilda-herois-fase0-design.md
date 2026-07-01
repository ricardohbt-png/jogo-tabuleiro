# Guilda dos Heróis — Fase 0: Fundação

**Data:** 2026-06-30
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 0 de N (Fundação). Fases seguintes: 1 (Especializações), 2 (Técnicas), 3 (Técnicas exclusivas Mago/Clérigo).

---

## 1. Contexto e visão geral

O projeto adiciona um novo prédio na cidade — a **Guilda dos Heróis** — onde cada
herói compra dois tipos de aprimoramento permanente:

- **Especializações:** upgrades **permanentes e sempre ativos** que **aprimoram no
  lugar** as 3 habilidades-base que a classe já tem. Comprar um nível superior
  torna a habilidade-base melhor. Não ocupam slot, não têm passo de "equipar" e
  **não** têm limite de "uma ativa".
- **Técnicas da Guilda:** habilidades **novas** que entram num **4º slot extra**
  (vazio por padrão). O herói pode **possuir várias** (compradas), mas só **1 fica
  equipada por vez** (para trocar, "esquece" a atual). Mago e Clérigo têm 2 slots
  (1 genérica + 1 exclusiva). Técnicas têm **tempo de recarga** (em rodadas) e
  **custo extra de fome/sede**.

> **Nota de reconciliação:** o texto original de referência dizia "cada herói pode
> deixar apenas uma Especialização ativa". Isso foi **descartado** — o limite de
> "uma ativa" vale apenas para as **Técnicas** (4º slot). Especializações são
> sempre ativas e cumulativas.

Esta **Fase 0** entrega a *fundação*: o prédio, o protocolo de compra genérico, a
persistência, o 4º slot, o motor de recarga e **uma técnica real de referência
(Brutalidade)** que valida o fluxo ponta-a-ponta. O conteúdo de balanceamento
(rework das habilidades-base; as ~30 técnicas restantes) vem nas fases seguintes.

### Fatos do código atual (confirmados)

- **6 personagens fixos**, um por `class_id`, único por sala (`select_class`,
  server.py:3303; recusa `class_id` já tomado na sala em :3307): `warrior` (Victor),
  `mage` (Pedro), `rogue` (Luccas), `cleric` (Lewis), `paladin` (Richard),
  `bard` (Henrique).
- Habilidades das classes em `CLASSES[cls_id]["skills"]` (server.py:206+).
- Sistema de **fome/sede** unificado (0–100) já existe (server.py:89+); ações
  debitam custo. **Não há sistema de recarga/cooldown para heróis** — é novo.
- Existe `self.round_num` (server.py:3221, começa em 1) que incrementa a cada volta
  completa em `handle_end_turn` (server.py:9896). O idioma
  `pronta_em = round_num + N` já é usado para os slots de magia
  (`slots_cooldown`, server.py:7051-7076). **Reusamos esse idioma.**
- Cidade é uma imagem com hotspots (`_CTY_BLDGS` no game.js; render em :1058-1074;
  clique em `_cityHotspotClick`, :1084). Já existe um hotspot `guilda` que hoje só
  mostra um toast "em breve" (game.js:1086).
- Lojas atuais broadcast em `broadcast_city_state` (server.py:3445) e compra em
  `handle_shop_buy` (server.py:3484).
- `make_player` (server.py:2822) monta o dict do jogador.
- Ficha da cidade: `abrirFichaCidade`/`renderFichaCidadeBody`/`_updateCityHeroBar`
  (game.js). O jogo NÃO tem persistência em arquivo hoje — o estado vive na sala.

---

## 2. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Recarga | `pronta_em = round_num + recarga_rodadas`; mesmo idioma dos slots de magia. Uma "rodada" = todos os heróis agirem uma vez. |
| Ouro | Cada herói compra com o próprio ouro (já é por-jogador). |
| Persistência | **Save em arquivo por personagem** (chave = `class_id`), global no servidor. Um JSON por personagem em `saves/`. Guarda só posse+equipar; ouro/HP/nível continuam por-sessão. |
| Personagem em uso | **Trava global:** se um personagem já está numa sala ativa, bloqueia escolhê-lo em outra sala. *(Implicação aceita: só um grupo joga cada personagem por vez em todo o servidor.)* |
| Unidade "1 técnica ativa" | Vale para as **Técnicas** (4º slot). Mago/Clérigo: 2 slots (genérica + exclusiva); demais: 1. |
| Especializações | Sempre ativas, cumulativas; sem passo de equipar; sem limite. |
| Arquitetura de efeitos | **Catálogo declarativo** (estilo `GRIMORIO`/`DECOR_TYPES`); casos complexos viram hook nomeado. Slice fino: Fase 0 tem 1 técnica real (Brutalidade). |
| Reembolso | Não haverá. |
| Trocar técnica equipada | Só na cidade (antes da aventura). Travado dentro da masmorra. |
| Reset de recarga | Zera ao voltar para a cidade (recarga total, como o descanso dos slots de magia). |

---

## 3. Modelo de dados (server.py, no `make_player`)

Adicionar ao dict do jogador:

```python
"guild_owned": {
    "especializacoes": [],   # ids de upgrades comprados (semântica na Fase 1)
    "tecnicas": [],          # ids de técnicas possuídas
},
"guild_equip": {
    "tecnica": None,             # id da técnica no 4º slot (genérica)
    "tecnica_exclusiva": None,   # 2º slot — só mage/cleric
},
"technique_cooldowns": {},   # { tecnica_id: pronta_em_round } — RUNTIME, zera na cidade
```

- `guild_owned` e `guild_equip` são **persistidos** (ver §5).
- `technique_cooldowns` é volátil (não persiste; zera na cidade).
- `especializacoes` e `tecnicas` são **listas de ids possuídos** — deliberadamente
  genéricas. A semântica de níveis/linhas das especializações é definida na Fase 1;
  a Fase 0 só precisa saber "possui / não possui".

---

## 4. Catálogo declarativo (server.py)

No estilo de `GRIMORIO`/`ARMADILHAS`/`DECOR_TYPES`:

```python
GUILD_CATALOG = {
    "brutalidade": {
        "categoria": "tecnica",        # "tecnica" | "especializacao"
        "classe": None,                # None = todas; ou "warrior", etc.
        "linha": None,                 # agrupa upgrades de especialização (Fase 1)
        "nivel": None,                 # I/II/III de especialização (Fase 1)
        "requer": None,                # id de pré-requisito (None = livre)
        "exclusiva": False,            # técnica exclusiva Mago/Clérigo (2º slot)
        "preco": 120,                  # ouro (placeholder p/ Fase 0)
        "custo_fome": 2,
        "custo_sede": 2,
        "recarga_rodadas": 3,
        "nome": "Brutalidade",
        "desc": "Até o fim do turno, ataques físicos com arma causam +2 de dano.",
        "icon": "🪓",
        "efeito": {"tipo": "buff_turno", "bonus_dano_arma": 2},
    },
    # … Fases 1-2 acrescentam aqui.
}
```

- **Efeito declarativo** sempre que possível; um resolvedor genérico o aplica.
  Casos que não cabem no vocabulário declarativo ganham um **hook nomeado**
  (`efeito: {"tipo": "hook", "handler": "nome"}`), como as magias já fazem.
- **Preço por nível** (Especializações, Fase 1): Nível I = 100, II = 150, III =
  200. As técnicas terão preço próprio por faixa de recarga (definido na Fase 2);
  a Fase 0 usa o `preco` placeholder de Brutalidade.
- Exportável para o cliente (padrão `tools/export_catalog.py`) ou embutido no
  `city_state` (ver §7). **Decisão:** embutir no `city_state` para evitar gerar
  arquivo novo nesta fase.

### Validação de compra
`handle_guild_buy` valida, em ordem: item existe no catálogo; classe compatível
(`classe` None ou == a do jogador); pré-requisito `requer` já possuído; ainda não
possuído; ouro suficiente. Debita ouro, adiciona à lista `owned` correta, **salva**
(§5), re-broadcast `city_state`.

---

## 5. Persistência (nova pasta `saves/`)

- Um arquivo JSON por personagem: `saves/warrior.json`, `saves/mage.json`, …
  Conteúdo:
  ```json
  { "class_id": "mage", "especializacoes": [], "tecnicas": ["brutalidade"],
    "equip": { "tecnica": "brutalidade", "tecnica_exclusiva": null } }
  ```
  Guarda **apenas** `guild_owned` + `guild_equip`. Ouro/HP/nível NÃO persistem
  (continuam por-sessão). Racional: o herói pagou uma vez; a posse fica salva,
  mesmo começando cada sessão com ouro/estado padrão.
- **Carregar:** em `select_class`, após o `class_id` ser aceito, ler
  `saves/<class_id>.json` (se existir) e popular `guild_owned`/`guild_equip` do
  jogador. Ausente/corrompido → começa vazio (log de aviso, sem crash).
- **Gravar:** a cada compra e a cada troca de equipar. Escrita atômica
  (grava em `.tmp` e renomeia) para evitar corrupção.
- Funções sugeridas: `guild_save_path(class_id)`, `load_guild_save(class_id)`,
  `write_guild_save(player)`.

### Trava de personagem em uso
- Registro global no processo: `CHARACTERS_IN_USE: dict[class_id -> room_code]`.
- `select_class`: se `class_id` presente em `CHARACTERS_IN_USE` e a sala referida
  ainda está ativa → recusa com `error` ("Pedro já está em uso em outra sala").
  Senão, registra `CHARACTERS_IN_USE[class_id] = self.code`.
- **Liberar:** no disconnect do jogador, ao ele trocar de personagem, e ao fim/
  esvaziamento da sala. Reinício do servidor limpa o registro (aceitável).
- Escopo: cross-room, global ao processo do servidor.

---

## 6. Motor de recarga

- Reusa `self.round_num`.
- Ao usar a técnica: `player["technique_cooldowns"][tid] = self.round_num + recarga`.
- **Pronta** se `tid` ausente ou `round_num >= pronta_em`.
- **Restante** exibido = `max(0, pronta_em - round_num)` (em "rodadas").
- **Voltar à cidade zera** `technique_cooldowns` (recarga total — espelha
  `_reset_slots_descanso`). Ponto de gancho: onde a fase muda para "city"
  (`_voltar_para_cidade`, server.py:6516).
- Usar a técnica também debita `custo_fome`/`custo_sede` via o caminho de
  fome/sede já existente.

---

## 7. Protocolo WebSocket

### Cliente → Servidor
| Mensagem | Campos | Efeito |
|---|---|---|
| `guild_buy` | `item_id` | Compra um item do `GUILD_CATALOG` (valida §4). Só na cidade. |
| `guild_equip` | `slot` (`"tecnica"`\|`"tecnica_exclusiva"`), `item_id` (ou `null` p/ desequipar) | Equipa/troca a técnica no slot. Só na cidade. Valida posse; `tecnica_exclusiva` só mage/cleric e só técnicas `exclusiva:true`. Salva + re-broadcast. |
| `usar_tecnica` | `tecnica_id`, alvo conforme o efeito | Ativa a técnica equipada na masmorra. Valida: equipada, fora de recarga, fome/sede suficientes, turno do jogador. Aplica efeito, seta recarga, debita custo. |

### Servidor → Cliente
- **`city_state`** ganha bloco `guild`:
  ```
  "guild": {
    "catalog": [ …itens do GUILD_CATALOG… ],
    "players": { pid: { "owned": {...}, "equip": {...} } }
  }
  ```
- **`game_state`** por jogador: técnica(s) equipada(s) + `technique_cooldowns`
  (restante por técnica) para o HUD.
- Erros via `error` (já existe).

---

## 8. UI (cliente, game.js/game.css)

### Prédio da Guilda
- `_cityHotspotClick('guilda')` (game.js:1086) deixa de dar o toast e abre o
  **painel da Guilda**.
- Painel: abas **Especializações | Técnicas**, filtradas pela classe do herói que
  abre. Cada item: nome, ícone, descrição, custo (fome/sede/recarga quando
  técnica), preço, e estado — *comprável* (botão comprar → `guild_buy`),
  *possuído*, ou *bloqueado* (pré-requisito faltando, com dica do que falta).
- Reusa estética das lojas atuais quando possível.

### Equipar na ficha
- `renderFichaCidadeBody` ganha a seção **"Técnica da Guilda"**: 1 slot (Mago/
  Clérigo: 2 — genérica + exclusiva). Mostra a equipada e um seletor das técnicas
  possuídas (+ opção "vazio"). Trocar → `guild_equip`. Editável só na cidade.

### HUD em jogo
- A técnica equipada aparece como **4º botão** ao lado das 3 habilidades-base, com:
  ícone, custo (fome/sede), e **overlay de recarga** ("3r" e desabilitado quando
  em cooldown). Clique → `usar_tecnica`. Mago/Clérigo mostram os 2 slots.

---

## 9. Técnica de referência — Brutalidade (slice fino)

Único conteúdo real da Fase 0, para validar o fluxo inteiro:

- **Efeito:** até o fim do turno, ataques físicos com arma causam +2 de dano
  (não afeta magias).
- **Recarga:** 3 rodadas. **Custo extra:** +2 fome / +2 sede. **Preço:** 120
  (placeholder). **Classe:** todas.
- **Aplicação:** buff de turno lido no cálculo de dano de `handle_attack`
  (server.py:4492) — some no fim do turno do jogador.

Isso exercita: comprar → persistir → equipar (ficha) → aparecer no HUD → ativar →
aplicar efeito no ataque → entrar em recarga → bloquear reuso → debitar fome/sede →
zerar recarga ao voltar à cidade.

---

## 10. Testes (`tools/test_guilda.py`)

Cobrir, sem depender de UI:

1. **Compra válida:** debita ouro, adiciona a `owned`, persiste.
2. **Compra inválida:** ouro insuficiente; classe incompatível; pré-requisito
   faltando; já possuído — todas recusadas sem efeito colateral.
3. **Persistência round-trip:** `write_guild_save` → `load_guild_save` reconstrói
   `owned`/`equip` idênticos; arquivo ausente → vazio; corrompido → vazio + aviso.
4. **Trava de em-uso:** 2ª sala não pode escolher personagem já em uso; libera no
   disconnect.
5. **Equipar:** Mago/Clérigo aceitam 2 slots (genérica + exclusiva); demais só 1;
   `tecnica_exclusiva` recusa técnica não-exclusiva e classe não mago/cleric;
   desequipar com `null`.
6. **Ativação da técnica:** aplica efeito, seta `technique_cooldowns`, debita
   fome/sede.
7. **Recarga:** reuso bloqueado até `round_num` alcançar `pronta_em`; avançar
   rodadas libera.
8. **Reset na cidade:** voltar à cidade zera `technique_cooldowns`.

---

## 11. Fronteiras explícitas (NÃO fazer na Fase 0)

- **Não** reformular/enfraquecer nenhuma habilidade-base (Fase 1).
- **Não** implementar as ~30 técnicas restantes nem seus efeitos (Fase 2).
- **Não** implementar a tabela de "custo extra de progressão" baixo/médio/alto
  (Fase 1).
- **Não** implementar reembolso.
- **Não** gerar arquivo de catálogo exportado separado (embutir no `city_state`).

---

## 12. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Trava global muda comportamento multiplayer (só 1 grupo por personagem) | Aceito explicitamente pelo usuário; documentado no CLAUDE.md ao concluir. |
| Escrita de save corrompendo em crash | Escrita atômica (`.tmp` + rename). |
| Infra não encaixar quando o conteúdo das Fases 1-2 chegar | Slice fino com Brutalidade valida o contrato completo agora. |
| Persistir só posse (não ouro) confundir | Documentar: pagou uma vez, posse é permanente; ouro é por-sessão. |
| `round_num` semântica de "rodada" divergir da expectativa | Reusa contador já existente e testado; teste 7 fixa o comportamento. |
