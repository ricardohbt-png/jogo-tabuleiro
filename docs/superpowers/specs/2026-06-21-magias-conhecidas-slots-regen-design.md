# Magias conhecidas + slots com regeneração (Pedro & Lewis)

**Data:** 2026-06-21
**Classes afetadas:** `mage` (Pedro), `cleric` (Lewis)
**Escopo:** apenas magias do `GRIMORIO`. O kit de cura dedicado do Lewis
(`cura`, `cura_area`, `purificacao`, `ressurreicao`, `imposicao_maos`) **não** é
afetado — continua com custo 💧/🍖 e sempre disponível.

---

## 1. Objetivo

Substituir o sistema atual de slots (contador por círculo resetado a cada turno,
em modo de teste com folga 9/9/9 para o clérigo e magias livres para o mago) por
um sistema de **magias conhecidas escolhidas pelo jogador** + **slots discretos
que regeneram por rodadas**.

Resumo das regras pedidas:
- Ao escolher Pedro/Lewis, o jogador escolhe **2 magias de 1º círculo**. Só essas
  ficam lançáveis.
- O personagem começa com **2 slots de 1º círculo**. Cada lançamento gasta 1 slot.
- Cada slot gasto regenera após um tempo fixo (timer **independente por slot**):
  - 1º círculo: **10 rodadas**
  - 2º círculo: **15 rodadas**
  - 3º círculo: **20 rodadas**
- Progressão por nível (ver tabela). Slot novo ganho ao subir de nível entra **cheio**.
- A cada nível com ganho, o jogador escolhe **1 nova magia conhecida** do círculo
  correspondente.

## 2. Definições acordadas

- **"Rodada"** = uma volta completa da mesa (todos os jogadores jogam 1 turno).
  Já existe `self.round_num` no servidor, incrementado quando a volta fecha
  (`server.py` ~9424). Os timers de regeneração se ancoram nele.
- **Regeneração** = **timer independente por slot**: cada slot gasto registra o
  `round_num` em que volta a ficar pronto. Visível na ficha (contagem regressiva).
- **Descanso/cidade** = ao voltar para a cidade entre masmorras, **todos** os
  slots recarregam 100% (cooldowns zerados).
- **Escolha ao subir de nível** = overlay aparece **na hora**, mas **bloqueia só o
  jogador que subiu** (os demais seguem). Level-ups múltiplos entram em fila.
- **Círculo x slot** = **estrito**: magia de Nº círculo só usa slot do mesmo círculo.
- **Modo teste** = desligado para ambas as classes; escolher magias é **obrigatório**
  (sem escolha = sem magias disponíveis).
- **Nível 6+** = **cap** no nível 5 (sem novas magias/slots; bônus normais de
  HP/ataque/CA/resistências continuam). Deixar TODO para estender depois.

## 3. Modelo de dados (servidor, por jogador)

Substitui `p["magias_usadas_hoje"]` por:

```python
p["magias_conhecidas"]  # [ids do GRIMORIO] — campo já existe; passa a ser obrigatório
p["slots_max"]      = {"primeiro": N1, "segundo": N2, "terceiro": N3}   # derivado do nível
p["slots_cooldown"] = {"primeiro": [r, ...], "segundo": [r, ...], "terceiro": [r, ...]}
```

- `slots_cooldown[c]` guarda, para cada slot **gasto**, o `round_num` em que ele
  volta a ficar pronto.
- **Disponíveis** `c` = `slots_max[c] - len(slots_cooldown[c])` (após podar vencidos).
- Ao lançar: `slots_cooldown[c].append(round_num + REGEN[c])`.
- `REGEN = {"primeiro": 10, "segundo": 15, "terceiro": 20}`.
- Poda: entradas com `ready_at <= round_num` são removidas (poda sob demanda na
  leitura; opcionalmente também ao incrementar `round_num`).

## 4. Progressão por nível

Tabela única para mago e clérigo (reaproveita a `MAGE_SLOTS_POR_NIVEL` atual,
renomeada para uso compartilhado, ex.: `SLOTS_POR_NIVEL`):

| Nível | slots 1º | slots 2º | slots 3º | escolha ao chegar |
|---|---|---|---|---|
| 1 (criação) | 2 | 0 | 0 | **2 magias de 1º círculo** |
| 2 | 3 | 0 | 0 | +1 magia de 1º círculo |
| 3 | 3 | 1 | 0 | +1 magia de 2º círculo |
| 4 | 3 | 2 | 0 | +1 magia de 2º círculo |
| 5 | 3 | 2 | 1 | +1 magia de 3º círculo |
| 6+ | (cap) | (cap) | (cap) | — (sem novas magias/slots) |

- Total ao nível 5: **6 magias conhecidas** (3/2/1).
- Slot novo ganho num nível entra **cheio** (não nasce em cooldown).
- Escolhas filtradas por classe (`classe` inclui a classe do jogador) e excluindo
  magias já conhecidas.

## 5. Fluxos de escolha de magia

### 5.1 Criação (nível 1) — lobby
- O cliente já tem `renderSelecaoMagias(heroiKey, 'primeiro')` (game.js ~8065),
  hoje sem persistência. Estender para **Pedro e Lewis** (cartas vêm do GRIMÓRIO
  filtrado pela classe).
- Nova mensagem **client → server** `set_known_spells { ids }`:
  - Validar: exatamente 2 ids, todos de 1º círculo, todos da classe do jogador.
  - Guardar em `p["magias_conhecidas"]`.
- **Obrigatório** antes de `start_game` para mago/clérigo: bloquear início se algum
  mago/clérigo não escolheu.

### 5.2 Level-up em jogo (níveis 2/3/4/5)
- Em `_check_level_up`, ao subir mago/clérigo para um nível com ganho:
  - Atualiza `slots_max` pela tabela; slot novo entra cheio.
  - Define `p["pending_spell_pick"]` (fila) com `{circulo, count}` do nível.
  - Envia prompt ao jogador (novo tipo de mensagem server → client, ex.:
    `spell_pick_prompt`).
- Nova mensagem **client → server** `escolher_magia_nivel { magia_id }`:
  - Validar círculo correto, classe, não já conhecida.
  - Adiciona a `magias_conhecidas`; remove o item da fila `pending_spell_pick`.
- **Bloqueio:** enquanto houver `pending_spell_pick` para o jogador, o servidor
  **recusa `end_turn`** dele (mensagem orientando a escolher). Os demais jogadores
  não são afetados. Fila processa um item por vez.

## 6. Lançamento (`handle_magia`)

- Remover o bypass de modo-teste (`MAGE_TESTE_LIVRE` / `livre`).
- Exigir `magia_id in p["magias_conhecidas"]` (senão erro).
- Pelo `circulo` da magia: podar cooldowns vencidos; se `disponíveis <= 0` → erro
  "Sem slot de Nº círculo (volta em X rodadas)" (X = menor `ready_at - round_num`).
- Senão, gasta: `slots_cooldown[circulo].append(round_num + REGEN[circulo])`.
- Mantém 🍖-1 / 💧-1 de sobrevivência e o limite de 1 ação principal por turno.
- Metamagia do mago continua sem consumir slot extra (só custo em 🍖/💧).

## 7. Descanso / cidade

- Na transição para a cidade (entre masmorras), zerar `slots_cooldown` de todos os
  mago/clérigo (recarga total). Localizar o hook de entrada em `city_state`.

## 8. Remoção do reset por turno

- Remover o bloco que zera `magias_usadas_hoje` a cada turno (server.py ~9453-9456).
  A disponibilidade passa a ser governada exclusivamente pelos timers de rodada.

## 9. Estado → cliente

- `game_state` (push_state) passa a incluir, para mago/clérigo:
  `magias_conhecidas`, `slots_max`, `slots_cooldown` e o `round_num` atual.
- O cliente calcula, por slot gasto, "volta em N rodadas" = `ready_at - round_num`.

## 10. Renderização da ficha (`renderMagiasFichaEmJogo`)

- Usar `magias_conhecidas` reais (remover fallback `MAGE_TESTE_LIVRE`).
- Limites = `slots_max` por nível para **ambas** as classes (remover o `9/9/9` do
  clérigo).
- Pips: verde = disponível. Cada slot gasto mostra **contagem regressiva**
  (`volta em N rodadas`). Mostrar os menores timers primeiro.
- Renderizar apenas cartas das magias conhecidas, agrupadas por círculo.

## 11. Limpeza de flags de teste

- Servidor: `MAGE_TESTE_LIVRE` já `False`. Remover `CLERIC_SLOTS`; substituir
  `slots_por_circulo` pela tabela por nível compartilhada (`SLOTS_POR_NIVEL`).
- Cliente: `const MAGE_TESTE_LIVRE = true` → `false` (e simplificar o uso, já que
  a lógica de slots muda de "limite por círculo" para "pool com cooldown").

## 12. Protocolo WebSocket — novas mensagens

### Client → Server
| Mensagem | Campos | Quando |
|---|---|---|
| `set_known_spells` | `ids` (2 magias de 1º círculo) | lobby, antes de `start_game` |
| `escolher_magia_nivel` | `magia_id` | ao responder ao prompt de level-up |

### Server → Client
| Mensagem | Campos | Quando |
|---|---|---|
| `spell_pick_prompt` | `circulo`, `count`, `opcoes` (ids elegíveis) | jogador subiu de nível |

`game_state` ganha os campos da seção 9.

## 13. Casos de borda

- Mago/clérigo entra numa partida já iniciada (rejoin): `slots_cooldown` e
  `magias_conhecidas` vêm do estado persistido; nada a recriar.
- Múltiplos level-ups no mesmo evento (ex.: bônus de objetivo concede XP em massa):
  empilhar prompts na fila `pending_spell_pick`, processados um a um.
- Jogador atinge nível com ganho mas a fila já tem item pendente: novo item entra
  na fila; o `end_turn` segue bloqueado até esvaziar.
- Sem magias elegíveis restantes num círculo (todas já conhecidas): não deve
  ocorrer dentro do cap (há magias suficientes por círculo no GRIMÓRIO), mas o
  servidor deve degradar com segurança (pular a escolha) se acontecer.

## 14. Verificação

- Teste de servidor (estilo `tools/test_*.py`) cobrindo:
  - `set_known_spells` valida contagem/círculo/classe.
  - Gastar slot adiciona cooldown correto; lançar sem slot é recusado.
  - Regeneração: após `REGEN[c]` rodadas, o slot volta.
  - Recarga total ao entrar na cidade.
  - Level-up concede slot cheio + enfileira escolha; `end_turn` bloqueado até escolher.
  - Cap no nível 5 (nível 6 não concede novas magias/slots).
- Verificação visual no cliente: ficha mostra magias conhecidas e a contagem
  regressiva dos slots gastos.
