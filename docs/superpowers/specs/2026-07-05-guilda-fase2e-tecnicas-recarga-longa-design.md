# Guilda dos Heróis — Fase 2e: Técnicas de Recarga Longa (10 rodadas)

**Data:** 2026-07-05
**Status:** Design aprovado — pronto para escrever a spec (este arquivo) e seguir para writing-plans
**Fase:** 2e — novo lote na faixa de recarga 10 (hoje só ocupada pela Oportunidade,
Fase 2d, mergeada em `dffa1de`). Substitui o rótulo "2d passivas" citado no roadmap
antigo (2d já foi usado para Oportunidade).
**Depende de:** infra `GUILD_CATALOG`/`handle_usar_tecnica`/`technique_cooldowns`
(2a), o padrão de reroll do Sangue Frio e o padrão de reação síncrona da Fase 2c,
e o ramo `regen_ressurge` já existente em `_player_dies` (Regeneração do Paladino).

---

## 1. Visão geral

Quatro técnicas novas, todas tier 10 (preço 350, recarga 10 rodadas — salvo
indicado), todas `categoria:"tecnica"`, `classe:None`, ocupando o 4º slot normal
(mutuamente exclusivas com as demais técnicas já existentes):

| Técnica | Gatilho | Resumo do efeito | Custo | Recarga |
|---|---|---|---|---|
| **Instinto de Sobrevivência** | Automático — dano zeraria o HP | HP fica em 1 em vez de morrer | 6🍖/6💧 | 10 |
| **Último Esforço** | Automático — dano zeraria o HP | HP=1 + 2 turnos-bônus seguidos com vantagem e crítico automático em todo acerto (nat20 → triplo); proibido curar a si mesmo; ao fim, morre normalmente (revivível) | 6🍖/6💧 | 10 |
| **Golpe Decisivo** | Manual (`usar_tecnica`) | Arma o próximo ataque básico (corpo a corpo ou à distância): se acertar, crítico automático (nat20 enquanto armado → triplo em vez de dobro) | 6🍖/6💧 | 10 |
| **Sorte** | Reativo — jogador escolhe após ver um erro | Rerola o último ataque que errou (mesmo alvo); independente e não substitui o Sangue Frio (2c), que continua igual | 2🍖/2💧 | 10 |

Duas das quatro (Instinto/Último Esforço) competem pelo mesmo gatilho (HP zeraria) —
como ocupam o mesmo 4º slot, nunca estão as duas equipadas ao mesmo tempo; não há
conflito de precedência entre elas. A prioridade de resolução em `_player_dies`
continua: Regeneração do Paladino (já existe) → Instinto de Sobrevivência → Último
Esforço → morte normal.

---

## 2. Catálogo (`GUILD_CATALOG`)

```python
# ── Técnicas de Recarga Longa (Fase 2e) ─────────────────────────────────
"tecnica_instinto_sobrevivencia": {
    "id": "tecnica_instinto_sobrevivencia", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
    "nome": "Instinto de Sobrevivência", "icon": "🍀",
    "desc": "Automática. Se um dano zeraria seu HP, você fica com 1 em vez de "
            "morrer. Depois disso, entra em recarga.",
    "efeito": {"tipo": "passiva_evitar_morte"},
},
"tecnica_ultimo_esforco": {
    "id": "tecnica_ultimo_esforco", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
    "nome": "Último Esforço", "icon": "🔥",
    "desc": "Automática. Se um dano zeraria seu HP, você fica com 1 e ganha 2 "
            "turnos seguidos: todo ataque tem vantagem e todo acerto é crítico "
            "(nat20 → dano TRIPLICADO). Não pode se curar. Ao final, cai como se "
            "tivesse morrido normalmente (pode ser reerguido por Ressurreição).",
    "efeito": {"tipo": "passiva_ultimo_esforco"},
},
"tecnica_golpe_decisivo": {
    "id": "tecnica_golpe_decisivo", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
    "nome": "Golpe Decisivo", "icon": "💥",
    "desc": "Arma o próximo ataque básico (corpo a corpo ou à distância): se "
            "acertar, é crítico automático (dano dobrado); num natural 20 "
            "enquanto armado, o dano é TRIPLICADO. Consumida no próximo ataque, "
            "acerte ou erre.",
    "efeito": {"tipo": "golpe_decisivo"},
},
"tecnica_sorte": {
    "id": "tecnica_sorte", "categoria": "tecnica", "classe": None,
    "linha": None, "nivel": None, "requer": None, "exclusiva": False,
    "preco": 350, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 10,
    "nome": "Sorte", "icon": "🎲",
    "desc": "Depois de errar um ataque, você pode gastar esta técnica para "
            "rolá-lo novamente contra o mesmo alvo. Independente do Sangue Frio.",
    "efeito": {"tipo": "sorte"},
},
```

A aba de Técnicas da Guilda já agrupa por faixa de recarga (2a) — a faixa 10r passa
a ter 5 itens (Oportunidade + estas 4).

---

## 3. Instinto de Sobrevivência (a mais simples)

Novo ramo em `_player_dies`, no mesmo ponto do `regen_ressurge` existente, checado
**depois** dele (Regeneração do Paladino tem prioridade se ambos estiverem
disponíveis — cenário raro, mas mantém o comportamento pré-existente intocado):

```python
if p.get("regen_ressurge") and p.get("regen_pool", 0) > 0:
    ...            # já existe, inalterado
    return
if (tem_tecnica_equipada(p, "tecnica_instinto_sobrevivencia")
        and self.tecnica_restante(p, "tecnica_instinto_sobrevivencia") == 0):
    p["hp"] = 1
    p["technique_cooldowns"]["tecnica_instinto_sobrevivencia"] = self.round_num + 10
    await self.gm_say(f"🍀 **{p['name']}** recorre ao **Instinto de Sobrevivência** e resiste com 1 HP!")
    return
```

`tem_tecnica_equipada(p, tecnica_id)` é um helper novo e pequeno (não existe
ainda): `return tecnica_id in (p["guild_equip"].get("tecnica"), p["guild_equip"].get("tecnica_exclusiva"))`
— fatora a checagem que hoje está inline em `handle_usar_tecnica` (linha ~4346),
reaproveitada aqui e no Último Esforço/Golpe Decisivo/Sorte (nenhum deles é
ativado via `usar_tecnica` do jeito normal para Instinto/Último Esforço, então
precisam checar "está equipada" sem passar pelo fluxo de ação/turno daquele
handler).

Sem UI dedicada — dispara silenciosamente (só narração do GM), igual à Regeneração.

---

## 4. Último Esforço (a complexa — "turno de glória")

### 4.1 Gatilho e novo estado

Mesmo ponto de `_player_dies`, mas **sem `return` imediato** — abre uma sub-fase e
só then cai no fluxo normal de finalizar a morte:

```python
if (tem_tecnica_equipada(p, "tecnica_ultimo_esforco")
        and self.tecnica_restante(p, "tecnica_ultimo_esforco") == 0):
    p["hp"] = 1
    p["technique_cooldowns"]["tecnica_ultimo_esforco"] = self.round_num + 10
    await self._abrir_ultimo_esforco(p)
# (sem elif/return — cai para o fluxo de morte normal abaixo, que agora finaliza de verdade)
p["alive"] = False
p["hp"] = 0
...
```

Novo estado por jogador: `ultimo_esforco_ativo` (bool), `ultimo_esforco_turnos_restantes` (int).
Novo estado da sala: `self.last_stand_pid` (None normalmente), `self.last_stand_event`
(`asyncio.Event`), `self.last_stand_timer_task` (mesmo padrão do timer de turno de
30s, mas dedicado — o timer normal usa `current_pid()`, que continua sendo outro
jogador durante a janela).

### 4.2 A sub-fase (pausa a rodada, mesmo padrão de animados/prisioneiro)

```python
async def _abrir_ultimo_esforco(self, p):
    pid = p["id"]
    p["ultimo_esforco_ativo"] = True
    p["ultimo_esforco_turnos_restantes"] = 2
    p["moves_left"] = p.get("spd", 0)
    p["action_done"] = False
    self.last_stand_pid = pid
    self.last_stand_event = asyncio.Event()
    await self.gm_say(f"🔥 **{p['name']}** recusa a morte — **ÚLTIMO ESFORÇO**! Dois turnos de fúria antes de cair.")
    await self.push_state()
    self._iniciar_timer_ultimo_esforco(pid)
    await self.last_stand_event.wait()
    p["ultimo_esforco_ativo"] = False
    p.pop("ultimo_esforco_turnos_restantes", None)
```

Como as **17 chamadas** a `_player_dies` hoje já são `await`adas, o `await
self.last_stand_event.wait()` pausa naturalmente qualquer loop de monstro/turno
que a chamou — sem tocar nesses 17 pontos. Isso funciona porque o `websockets`
roda cada handler de mensagem recebida como sua própria task asyncio: enquanto a
coroutine que chamou `_player_dies` está bloqueada no `await`, o event loop
continua livre para processar as mensagens (`move`/`attack`/`end_turn`) que o
herói em último esforço mandar — é exatamente esse processamento concorrente que
faz o Event ser sinalizado e a pausa terminar.

`_is_turn` ganha um segundo caminho válido (mudança mínima, 1 linha):

```python
def _is_turn(self, pid):
    if self.phase != "playing":
        return False
    return self.current_pid() == pid or self.last_stand_pid == pid
```

Isso libera `handle_move`/`handle_attack`/`handle_usar_tecnica`/etc. — que já
checam `_is_turn` — para aceitar ações do herói em último esforço mesmo sem ser
oficialmente sua vez, reaproveitando os handlers normais (nenhuma duplicação de
lógica de movimento/ataque).

### 4.3 Fechar cada um dos 2 mini-turnos

`handle_end_turn` ganha um branch no topo:

```python
async def handle_end_turn(self, pid):
    if not self._is_turn(pid): return
    if self.last_stand_pid == pid:
        await self._fechar_mini_turno_ultimo_esforco(pid)
        return
    ...   # fluxo normal, inalterado
```

```python
async def _fechar_mini_turno_ultimo_esforco(self, pid):
    p = self.players[pid]
    p["ultimo_esforco_turnos_restantes"] -= 1
    if p["ultimo_esforco_turnos_restantes"] > 0:
        p["moves_left"] = p.get("spd", 0)
        p["action_done"] = False
        await self.gm_say(f"⚔️ **{p['name']}** continua o Último Esforço — mais um turno!")
        await self.push_state()
        self._iniciar_timer_ultimo_esforco(pid)
    else:
        self._cancelar_timer_ultimo_esforco()
        self.last_stand_pid = None
        self.last_stand_event.set()
```

Também fecha quando os 2 créditos de ação/movimento se esgotam sem `end_turn`
explícito (mesma lógica de "ação feita + sem movimento" que already existe para
turnos normais) — chamando o mesmo `_fechar_mini_turno_ultimo_esforco`.

**Timer de segurança:** `_iniciar_timer_ultimo_esforco(pid)`/`_cancelar_timer_ultimo_esforco`
espelham `_iniciar_timer_turno`/`_cancelar_timer_turno` (mesmos 30s), mas mirando
`last_stand_pid` em vez de `current_pid()`. Ao expirar, chama
`_fechar_mini_turno_ultimo_esforco(pid)` como se o jogador tivesse mandado
`end_turn` — evita travar o jogo se o cliente cair no meio da janela.
**Desconexão:** se o jogador em último esforço desconectar, fecha a janela
imediatamente (zera `ultimo_esforco_turnos_restantes`), mesmo tratamento.

### 4.4 Vantagem + crítico automático nos ataques

Em `handle_attack`, dois pontos:

1. **Vantagem** (linha ~5771, onde `vantagem = (...)`): adiciona
   `or bool(p.get("ultimo_esforco_ativo"))` à disjunção existente.
2. **Multiplicador de crítico** (hoje `if crit: dmg *= 2`, nos dois lugares — arma
   e desarmado, linhas ~5835 e ~5855): generaliza para uma variável de
   multiplicador computada uma vez, reaproveitada por Golpe Decisivo (seção 5):

```python
_forca_critico = bool(p.get("ultimo_esforco_ativo")) or bool(p.get("tecnica_golpe_decisivo_armado"))
...
hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
if hit and _forca_critico:
    crit = True
if p.get("tecnica_golpe_decisivo_armado"):
    p["tecnica_golpe_decisivo_armado"] = False   # consumida no próximo ataque, acerte ou erre
...
# nos dois sites de dano (arma e desarmado), troca "if crit: dmg *= 2" por:
if crit:
    dmg *= 3 if (_forca_critico and roll == 20) else 2
```

Sem técnica ativa, `_forca_critico=False` → comportamento de hoje intocado (nat20
sempre foi ×2). Com Último Esforço ou Golpe Decisivo ativos: qualquer acerto vira
×2, e um natural 20 vira ×3.

### 4.5 Proibição de auto-cura

Enquanto `p.get("ultimo_esforco_ativo")`:
- `handle_use_item`: recusa consumir item de cura (poção) direcionado a si mesmo.
- `handle_cura` / `handle_imposicao_maos`: recusa se `target_id == pid`.
- `handle_cura_area`: o herói em último esforço pode conjurar normalmente (caso
  seja Lewis), mas **não recebe** o próprio benefício de cura — os demais aliados
  no raio continuam curados normalmente (checagem pontual pulando `pid==caster`
  na iteração de alvos).

Fora de escopo: `purificacao`/`ressurreicao` não curam HP diretamente (removem
status ou reerguem um morto) — não se aplicam aqui.

### 4.6 Cliente

- `game_state` ganha `last_stand_pid` (espelha `animados_phase_pid`/
  `mission_complete_pending` — mesmo padrão de "flag de sub-fase" já usado).
- Quando `last_stand_pid === meu pid`: HUD mostra banner "🔥 ÚLTIMO ESFORÇO — Xª de 2
  turno(s)" e libera os botões de mover/atacar mesmo fora da vez normal (o
  indicador de "vez de fulano" no topo continua mostrando o jogador realmente
  interrompido — evita confundir os outros jogadores sobre de quem "era" a vez).
- Botão de fim de turno normal já dispara `end_turn` — nenhuma mensagem nova
  necessária no cliente para fechar o mini-turno.

---

## 5. Golpe Decisivo

Ativação manual, padrão idêntico à Mira Perfeita (buff-and-act, não consome ação):

```python
elif ef.get("tipo") == "golpe_decisivo":
    p["tecnica_golpe_decisivo_armado"] = True
```

Consumo e multiplicador de dano: já cobertos pela seção 4.4 (`_forca_critico`
soma as duas fontes — Último Esforço e Golpe Decisivo — no mesmo ponto de
`handle_attack`; nunca as duas ativas ao mesmo tempo no mesmo jogador, já que
ocupam o mesmo 4º slot, mas o código não precisa presumir isso). Aplica-se a
qualquer ataque básico (corpo a corpo ou à distância) — sem restrição de `w_range`,
ao contrário da Mira Perfeita.

Novo campo no template do jogador: `"tecnica_golpe_decisivo_armado": False`
(perto de `tecnica_mira_perfeita`).

Expira no fim do turno sem uso — mesmo padrão do `p["tecnica_mira_perfeita"] = False`
em `handle_end_turn` (linha ~11147): adiciona `p["tecnica_golpe_decisivo_armado"] = False`
ao lado.

---

## 6. Sorte

### 6.1 Armazenar o último erro

Em `handle_attack`, no ponto onde o Sangue Frio já intercepta um erro (linha
~5776-5779), **sem interferir no fluxo do Sangue Frio** (são independentes —
ambos podem estar equipados? Não: mesmo 4º slot, mutuamente exclusivos, mas o
código de cada um não presume isso):

```python
hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
if not hit and self._sangue_frio_consumir(p):
    ...   # já existe, inalterado
if not hit and tem_tecnica_equipada(p, "tecnica_sorte"):
    p["ultimo_ataque_perdido"] = {
        "target_id": target_id, "eff_atk": eff_atk, "eff_target_ac": eff_target_ac,
        "vantagem": vantagem, "desvantagem": desvantagem,
    }
```

(Se o Sangue Frio já rerolou e ainda assim errou, `hit` continua `False` nesse
ponto — o Sorte armazena o resultado FINAL, já pós-Sangue Frio, que é o
comportamento correto já que só um dos dois pode estar equipado.)

### 6.2 Ativação reativa (`usar_tecnica`)

```python
elif ef.get("tipo") == "sorte":
    perdido = p.get("ultimo_ataque_perdido")
    if not perdido:
        await self.send_to(pid, {"type": "error", "msg": "Nenhum ataque recente para rerolar."})
        return
    alvo = self.monsters.get(perdido["target_id"])
    if not alvo or alvo.get("hp", 0) <= 0:
        await self.send_to(pid, {"type": "error", "msg": "O alvo não está mais disponível."})
        return
    hit, roll, total, crit, _desc = self._rolar_ataque(
        perdido["eff_atk"], perdido["eff_target_ac"], perdido["vantagem"], perdido["desvantagem"])
    await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                           "label": "🎲 Sorte (nova rolagem)", "hit": hit, "crit": crit})
    if hit:
        dmg = self._resolver_dano_ataque_basico(p, alvo, crit)   # helper extraído do handle_attack
        alvo["hp"] -= dmg
        await self.gm_say(f"🎲 **{p['name']}** força a Sorte e acerta **{alvo['name']}** por **{dmg}**!")
        if alvo["hp"] <= 0:
            await self._monster_dies(alvo, pid)
    else:
        await self.gm_say(f"🎲 **{p['name']}** tenta a Sorte de novo, mas erra outra vez!")
    p.pop("ultimo_ataque_perdido", None)
```

`_resolver_dano_ataque_basico(p, alvo, crit)` é um **helper extraído** da lógica
de dano de arma/desarmado que hoje vive inline em `handle_attack` (linhas
~5822-5860: rola o dado da arma, aplica `_golpe_raw`, bônus de atributo, dobra/
triplica em crítico, aplica modificadores de sobrevivência/canção/etc.) — extraído
para ser reaproveitado aqui sem duplicar ~40 linhas. **Fora de escopo** desse
reroll: consumo de munição, veneno na arma, Ataque Furtivo, projétil incendiário
e reação de Ataque Coordenado — todos esses já foram resolvidos (ou não) na
tentativa ORIGINAL que errou; o reroll do Sorte cobre só "acerta ou não, e quanto
de dano físico base".

### 6.3 Validade e limpeza

`ultimo_ataque_perdido` é limpo em `handle_end_turn` (início do fluxo normal, antes
de qualquer outra coisa) e sobrescrito automaticamente se um novo ataque errar de
novo (não deveria acontecer no mesmo turno, já que atacar consome a ação, mas o
código não precisa presumir isso).

Nenhuma UI dedicada de mira — o botão de usar técnica (4º slot) já mostra "Sorte"
disponível; ativa sem alvo (usa o `target_id` armazenado internamente).

---

## 7. Estado novo no template do jogador (resumo)

```python
"tecnica_golpe_decisivo_armado": False,   # Golpe Decisivo: próximo ataque básico
"ultimo_ataque_perdido": None,            # Sorte: {target_id, eff_atk, eff_target_ac, vantagem, desvantagem}
"ultimo_esforco_ativo": False,            # True durante a sub-fase do Último Esforço
"ultimo_esforco_turnos_restantes": 0,     # 2 → 1 → 0 (fecha a sub-fase)
```

Estado novo na sala (`GameRoom`/classe do servidor): `last_stand_pid` (None),
`last_stand_event` (None até abrir), `last_stand_timer_task` (None).

---

## 8. Testes (`tools/test_tecnicas_espec.py`)

Novas seções:

1. **Catálogo:** as 4 entradas com preço 350/recarga 10; Sorte com custo 2/2
   (diferente das outras 3, que são 6/6).
2. **Instinto de Sobrevivência:** dano que zeraria o HP resulta em HP=1 (não
   morre); recarga ativada; se HP zerar de novo dentro da recarga, morre
   normalmente; prioridade correta quando o jogador tem Regeneração do Paladino
   E a técnica (Regeneração vence).
3. **Último Esforço — abertura:** dano que zeraria o HP abre a sub-fase (`hp=1`,
   `last_stand_pid=pid`, `ultimo_esforco_turnos_restantes=2`), NÃO finaliza a
   morte imediatamente.
4. **Último Esforço — `_is_turn`:** durante a janela, `_is_turn(pid)` é `True`
   para o herói em último esforço mesmo com `current_pid()` sendo outro jogador.
5. **Último Esforço — combate:** ataques do herói em último esforço têm vantagem
   e todo acerto é crítico; um roll forçado de nat20 resulta em dano ×3 (mock do
   RNG).
6. **Último Esforço — auto-cura bloqueada:** `handle_use_item`/`handle_cura`/
   `handle_imposicao_maos` recusam quando `target_id==pid` e `ultimo_esforco_ativo`.
7. **Último Esforço — fechamento:** 2 `end_turn` seguidos (ou esgotar ações 2x)
   fecha a sub-fase, `last_stand_pid=None`, e a morte É finalizada
   (`p["alive"]=False`) — inclusive efeitos colaterais de `_player_dies` (bardo
   incapacitado, animados viram pó, etc.) continuam disparando.
8. **Último Esforço — timer de segurança:** simula timeout/desconexão durante a
   janela e confirma que ela fecha sozinha (sem travar o teste/jogo).
9. **Golpe Decisivo:** arma o flag; próximo ataque que acerta é crítico (mesmo
   sem nat20); nat20 enquanto armado → ×3; consumido acerte ou erre; expira no
   fim do turno sem uso.
10. **Sorte:** erro com a técnica equipada guarda `ultimo_ataque_perdido`; usar a
    técnica rerola contra o mesmo alvo e aplica dano se acertar; recusa sem erro
    recente ou com alvo morto/inexistente; independente do Sangue Frio (nenhuma
    interferência entre os dois quando ambos simulados, mesmo que na prática só
    um esteja equipado por vez).

---

## 9. Fronteiras (NÃO neste lote)

- Sangue Frio (2c) não é alterado nem removido — Sorte é uma técnica paralela e
  independente.
- Golpe Decisivo/Último Esforço não afetam magias com resolução por save (Bola de
  Fogo, Relâmpago, etc.) — só ataques básicos com rolagem de acerto vs CA.
- O reroll do Sorte não re-dispara munição/veneno/furtivo/projétil
  incendiário/Ataque Coordenado — esses já resolveram (ou não) na tentativa
  original.
- Nenhuma migração de save necessária (`saves/` é dev-only, gitignored).
- Exclusivas Mago/Clérigo continuam para a Fase 3.

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| `await` dentro de `_player_dies` pausando uma coroutine no meio de um loop de ataque de monstro pode ter efeitos colaterais inesperados em algum dos 17 call sites (ex: side effects que deveriam rodar ANTES da morte já rodaram; nada depende de rodar DEPOIS antes do `_player_dies` retornar hoje) | Auditar os 17 call sites na implementação — confirmar que nenhum lê `p["alive"]` logo após o `await self._player_dies(...)` esperando `False` imediatamente (ex: continuar loop de monstros olhando outros alvos, não este pid). |
| Sub-fase travando o jogo se o timer de segurança falhar | Timer dedicado (`_iniciar_timer_ultimo_esforco`) + fechamento também no handler de desconexão do jogador. |
| Duplicar lógica de dano entre `handle_attack` e o reroll do Sorte diverge com o tempo (ex: alguém adiciona um bônus de dano só num lugar) | Extrair `_resolver_dano_ataque_basico` como helper único, chamado dos dois lugares — não duas cópias. |
| `_forca_critico`/multiplicador ×3 misturado com outras fontes de crítico (Sono, que já força `hit,crit=True,True`) | O multiplicador só sobe pra ×3 se `_forca_critico AND roll==20` — Sono não seta `roll`, então nunca dispara o ×3 por acidente; continua ×2 como hoje. |
| `_is_turn` liberado para `last_stand_pid` sendo mal utilizado por OUTRO handler que não deveria aceitar ações fora de vez (ex: `handle_start_game`, ações de loja) | `last_stand_pid` só é setado durante `phase=="playing"` e dentro da janela; handlers de loja/cidade já checam `phase` separadamente (não usam `_is_turn`). |
