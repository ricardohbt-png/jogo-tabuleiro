# Guilda dos Heróis — Fase 2d: Oportunidade

**Data:** 2026-07-04
**Status:** Design aprovado — pronto para review do spec escrito
**Fase:** 2d — mini-lote próprio, adiado da Fase 2c (que cobriu Ataque Coordenado,
Sangue Frio, Resistência Absoluta e Contra-Ataque). **Não** é mais uma reação de
"sai do alcance de ameaça" (conceito original) — foi redesenhada em brainstorming
para: conceder a um aliado uma ação extra reservada para o próprio turno dele.
**Depende de:** infra `handle_usar_tecnica` (2a/2b/2c) + o helper `_acao_bloqueada`
já existente (usado hoje pela magia Velocidade).

---

## 1. Visão geral

**Oportunidade** é uma técnica de suporte (não uma reação que auto-dispara): ao
ativar, o jogador escolhe um aliado vivo (nunca a si mesmo). Esse aliado ganha um
**crédito de ação extra**, utilizável **no próprio turno dele** (reservado, não
imediato) — mover mais, atacar de novo, usar a habilidade de classe de novo, ou
lançar mais uma magia. É um único crédito (booleano): o que for gasto primeiro
consome-o; não empilha (não dá as duas coisas). Se o aliado não usar o crédito
antes do fim da rodada em que foi concedido, ele expira sozinho.

Tier 10 — a técnica mais cara/rara até agora (recarga maior que Contra-Ataque, T8).

---

## 2. Catálogo (`GUILD_CATALOG`)

```python
"tecnica_oportunidade": {
    "id": "tecnica_oportunidade", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
    "nome": "Oportunidade", "icon": "⏳", "alvo": "aliado",
    "desc": "Escolha um aliado (não pode ser você); no PRÓPRIO turno dele, ganha uma "
            "ação extra — mover mais, atacar de novo, usar a habilidade de classe de "
            "novo, ou lançar mais uma magia. Expira no fim desta rodada se não for usada.",
    "efeito": {"tipo": "oportunidade"},
},
```

A aba de Técnicas da Guilda já agrupa por faixa de recarga (2a); 10r abre uma nova
faixa (acima da faixa "Longa" de 8r do Contra-Ataque).

---

## 3. Estado no jogador

Dois campos novos no template do jogador (junto aos demais campos de técnica, perto
de `technique_cooldowns`/`sangue_frio_armado`):

```python
"oportunidade_credito": False,   # crédito de ação extra concedido, ainda não gasto
"oportunidade_round": 0,         # round_num em que foi concedido — expira se round_num avançar
```

Não precisa de reset explícito no fim de turno/rodada: a checagem sempre compara
`oportunidade_round == self.round_num`, então um crédito de uma rodada anterior já
é tratado como inválido onde for lido (sem precisar zerar em `handle_end_turn`).

---

## 4. Concessão (`handle_usar_tecnica`, novo branch)

Segue exatamente o padrão de validação do `ataque_coordenado` (aliado vivo, não pode
ser o próprio ativador):

```python
elif ef.get("tipo") == "oportunidade":
    alvo = self.players.get(target_id) if target_id else None
    if not alvo or not alvo.get("alive") or alvo["id"] == pid:
        await self.send_to(pid, {"type": "error",
            "msg": "Escolha um aliado vivo (não pode ser você)."}); return
    alvo["oportunidade_credito"] = True
    alvo["oportunidade_round"] = self.round_num
```

O restante do fluxo comum de `handle_usar_tecnica` (checagem de equipada/recarga/
fome-sede, débito de recursos, `technique_cooldowns[tecnica_id] = round_num +
recarga_rodadas`, narração) já é compartilhado por todas as técnicas — nenhuma
mudança adicional ali.

---

## 5. Consumo do crédito — duas vias mutuamente exclusivas

### 5.1 Via "ação principal extra" (unifica o gate com a Velocidade)

Hoje `_acao_bloqueada(p)` já concede 1 ação principal extra para a magia
Velocidade (`velocidade_rodadas`/`velocidade_extra_usada`). Acrescento um branch
análogo para Oportunidade:

```python
def _acao_bloqueada(self, p):
    """True se p não pode fazer outra ação principal. Velocidade e Oportunidade
    concedem 1 ação extra por turno/crédito: ao tentar agir já tendo agido,
    consomem o crédito disponível e liberam a ação."""
    if p.get("perde_turno"):
        return True
    if not p.get("action_done"):
        return False
    if p.get("velocidade_rodadas", 0) > 0 and not p.get("velocidade_extra_usada"):
        p["velocidade_extra_usada"] = True
        p["action_done"] = False
        return False
    if p.get("oportunidade_credito") and p.get("oportunidade_round") == self.round_num:
        p["oportunidade_credito"] = False
        p["action_done"] = False
        return False
    return True
```

`handle_attack` (linha ~5568), `handle_magia` (~8319) e o uso de pergaminho mágico
(~10973) **já chamam `_acao_bloqueada`** — ganham a cobertura de graça, sem tocar
neles.

Os pontos abaixo hoje checam `action_done` **cru** (`if p.get("action_done"): ...`)
— trocar cada um para `if self._acao_bloqueada(p): ...` (mesma semântica de
bloqueio, só que agora honrando os créditos de Velocidade/Oportunidade):

| Handler | Linha aprox. |
|---|---|
| `handle_animar_mortos` | 6336 |
| `handle_cura` | 7173 |
| `handle_cura_area` | 7224 |
| `handle_purificacao` | 7295 |
| `handle_ressurreicao` | 7378 |
| `handle_imposicao_maos` | 7428 |
| `handle_criar_armadilha` | 10279 |
| `handle_desarmar_armadilha` | 10492 |
| `handle_libertar_prisioneiro` | 14042 (`or p.get("action_done")` dentro de um `if` maior) |

**Fora de escopo:** `handle_arremesso_lanca` (~6265) e o bloco de magias legadas por
MP (~6669) — código legado/inerte, não tocar.

**Efeito colateral aceito (já aprovado):** a magia Velocidade passa a valer também
nessas 9 ações (hoje só valia em ataque/magia) — correção de uma inconsistência
pré-existente, não uma mudança de escopo do Oportunidade em si.

### 5.2 Via "movimento extra"

Novo handler, sem payload adicional (aplica ao remetente):

```python
async def handle_usar_oportunidade_movimento(self, pid):
    if not self._is_turn(pid): return
    p = self.players.get(pid)
    if not p or not p.get("alive"): return
    if not (p.get("oportunidade_credito") and p.get("oportunidade_round") == self.round_num):
        await self.send_to(pid, {"type": "error", "msg": "Sem crédito de Oportunidade disponível."})
        return
    p["oportunidade_credito"] = False
    p["moves_left"] = p.get("moves_left", 0) + p.get("spd", 0)
    await self.gm_say(f"⏳ **{p['name']}** aproveita a Oportunidade para se mover mais!")
    await self.push_state()
```

Mensagem client→server nova: `usar_oportunidade_movimento` (sem campos).

### 5.3 Exclusividade

O crédito é um único booleano (`oportunidade_credito`). Qualquer uma das duas vias
que disparar primeiro o consome; a outra deixa de estar disponível depois (a
checagem em ambas exige o crédito `True` e `round` batendo). Não há como somar
movimento extra E ação extra com um único crédito.

---

## 6. Cliente (`game.js`)

- `alvo: "aliado"` no catálogo → `usar_tecnica` abre `openTargetModal` (padrão já
  usado por Ataque Coordenado/Tática Defensiva), listando aliados vivos (sem
  restrição de raio).
- Quando o **próprio jogador** tem `oportunidade_credito` ativo (visível só no seu
  turno, via `game_state`/`city_state` do jogador — mesmo padrão de outros flags
  de turno), mostra um botão/indicativo "⏳ Usar Oportunidade em Movimento" que
  dispara `usar_oportunidade_movimento`. Usar qualquer ação principal normalmente
  (atacar, curar, etc.) também consome o crédito silenciosamente no servidor — sem
  necessidade de UI extra para essa via (a ação simplesmente não é bloqueada por
  "já usada").

---

## 7. Testes (`tools/test_tecnicas_espec.py`)

Novas seções:

1. **Catálogo:** `tecnica_oportunidade` com preço 350/recarga 10/custo 6-6, `alvo:"aliado"`.
2. **Concessão:** recusa alvo = si mesmo; recusa alvo morto/inexistente; concede
   `oportunidade_credito=True` + `oportunidade_round=round_num` no aliado válido.
3. **Expiração:** crédito concedido na rodada N deixa de valer se checado com
   `round_num` != N (simula rodada seguinte sem uso).
4. **Consumo via ação principal:** com `action_done=True` e crédito válido,
   `_acao_bloqueada` retorna `False` (libera) e consome o crédito (`False` depois);
   sem crédito válido, retorna `True` (bloqueia) como hoje.
5. **Consumo via movimento:** `handle_usar_oportunidade_movimento` soma `spd` a
   `moves_left` e consome o crédito; falha educadamente sem crédito ou fora do
   próprio turno.
6. **Exclusividade mútua:** gastar por uma via impede o uso da outra no mesmo crédito.
7. **Coexistência com Velocidade:** os dois créditos (Velocidade e Oportunidade)
   funcionam independentemente — ter um não desarma o outro; `_acao_bloqueada`
   testa Velocidade primeiro, Oportunidade depois, cada um consumido separadamente.
8. **Handlers migrados:** cada um dos 9 handlers da tabela da seção 5.1 aceita a
   ação quando `_acao_bloqueada` libera via crédito (smoke test simples por handler
   já existente no arquivo de testes, reaproveitando os stubs atuais).

---

## 8. Fronteiras (NÃO neste lote)

- Nenhuma reação nova de "ordem de turno"/attack-of-opportunity clássico — esse
  conceito original foi descartado no brainstorming em favor do design acima.
- `handle_arremesso_lanca` e o sistema legado de magias por MP não são tocados.
- Passivas (Último Esforço, Instinto de Sobrevivência) — lote 2e/2d separado, fora
  deste spec.
- Exclusivas Mago/Clérigo — Fase 3.

---

## 9. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Ampliar o escopo de `_acao_bloqueada` muda o comportamento de Velocidade em 9 handlers que hoje ignoram esse crédito | Efeito colateral revisado e aprovado explicitamente com o usuário — é uma correção de inconsistência, não regressão. |
| Crédito "vazando" para a rodada errada (usado depois de expirado) | Checagem sempre compara `oportunidade_round == self.round_num` no momento do uso, não apenas no momento da concessão. |
| Aliado gasta o crédito duas vezes (ataque + movimento) | Único flag booleano consumido atomicamente na primeira via que disparar; segunda tentativa já encontra `oportunidade_credito=False`. |
| Handlers migrados (`action_done` cru → `_acao_bloqueada`) mudarem mensagem de erro ou comportamento de `perde_turno` | `_acao_bloqueada` já trata `perde_turno` (bloqueia sempre) — mesma semântica que os handlers já esperavam implicitamente ao checar `action_done` (jogadores com `perde_turno` já não deveriam chegar lá, mas a checagem fica mais estrita/correta). |
| Ancorar os 9 pontos de edição em linhas erradas após possíveis mudanças no arquivo | Localizar cada site pelo nome da função (`async def handle_X`) + a linha `if p.get("action_done"):` logo após a checagem de classe, não por número de linha absoluto. |
