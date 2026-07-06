# Popup de resultado de armadilha — Design

## Contexto

Hoje, quando um personagem cai numa armadilha (das duas fontes existentes —
o buraco genérico de sala procedural `self.traps`, ou o catálogo rico
`self.armadilhas` com 8 tipos: Buraco, Armadilha de Urso, Fosso de Estacas,
Rede, Incendiária, Mina Terrestre, Fosso Envenenado, Nuvem de Gás) o único
feedback é uma linha no log de texto do Mestre (`gm_say`, visível a todos) +
a animação do dado (`dice_roll`, broadcast a todos). Não há nenhuma janela
dedicada — o jogador precisa ler o log pra saber o que aconteceu.

## Objetivo

Ao cair numa armadilha, o jogador **afetado** vê uma caixa de texto (popup)
dizendo: o tipo/nome da armadilha, se escapou ou não, e — em caso de falha
(ou sucesso parcial, quando a armadilha reduz o dano à metade em vez de
evitar por completo) — a descrição do efeito e o dano/efeitos sofridos.
Fecha por botão "Fechar", clique fora da caixa, ou Esc.

## Decisões de escopo (via brainstorming)

- **Só a vítima vê o popup.** Os demais jogadores continuam vendo só o log
  do Mestre, como hoje (broadcast de `gm_say`/`dice_roll` inalterado).
- **As duas fontes de armadilha entram no popup**: o buraco procedural
  genérico (`self.traps`, sem nome próprio hoje) recebe um nome/ícone fixo
  de exibição (`🕳️ Buraco Escondido`); as 8 armadilhas do catálogo usam seu
  próprio `nome`/`icone`/`descricao` já existentes em `ARMADILHAS`.
- **Armadilhas de área** (Mina Terrestre, Nuvem de Gás) — cada jogador
  atingido no raio recebe **seu próprio** popup com seu próprio resultado.
- **Prisioneiro resgatado**: se ele cair numa armadilha colocável, o popup
  vai para quem o controla no momento (`self.prisoner["rescuer_pid"]`).
- **Timing**: o popup abre ~1.2s depois do evento chegar ao cliente — dá
  tempo da animação do dado (2D/3D, ~750–1050ms + assentamento) terminar
  antes de tomar a tela.
- **Dano progressivo (Incendiária)**: cada tick de dano nos rounds
  seguintes (sem novo teste, ver `_processar_efeitos_armadilha_turno`)
  também abre um popup — simplificado, sem banner de sucesso/falha (já que
  não há teste), só "a armadilha continua queimando: X de dano".
- **Visual**: tema de perigo (borda vermelha/laranja), diferente do dourado
  já usado no `#chest-overlay`.
- **Som**: reaproveita a infra WebAudio existente (`_sfxBus`); um efeito
  curto de impacto ao abrir popup de falha, e algo mais neutro/nenhum som
  extra no popup de sucesso (o som do dado já cobre o "clímax").

## Protocolo — nova mensagem `trap_result`

Enviada via `send_to(pid, ...)` (nunca broadcast) em 4 pontos do
`server.py`:

1. **Buraco procedural** (`self.traps`, dentro do loop de `handle_move`
   perto da linha 5644) — após resolver o teste de Reflexos CD13 existente.
2. **`_disparar_armadilha`** (armadilha de 1 alvo, não-área) — após resolver
   save + aplicar efeitos. Só envia se o alvo for jogador (`_eh_jogador`) ou
   o prisioneiro (nesse caso, para `rescuer_pid`); monstro/servo animado não
   recebem (sem cliente).
3. **`_aplicar_armadilha_area`** (Mina Terrestre, Nuvem de Gás) — mesma
   lógica de destinatário, para cada alvo elegível no loop existente.
4. **`_processar_efeitos_armadilha_turno`** (tick de dano progressivo da
   Incendiária) — envia versão simplificada por tick.

### Forma da mensagem

```
{
  "type": "trap_result",
  "nome": "Armadilha de Urso",
  "icone": "🪤",
  "sucesso": false,          // true = evitou por completo
  "dano": 3,                 // 0 se não houve dano
  "metade": false,           // true = save reduziu à metade (armadilhas de área)
  "descricao": "1d4 de dano + perde movimento. Some após ativar.",
  "efeitos_extra": ["Perdeu o movimento"],   // strings prontas p/ exibir
  "tick": false              // true = mensagem de dano progressivo (Incendiária), sem banner de sucesso/falha
}
```

`efeitos_extra` é construído a partir dos efeitos realmente aplicados
naquele disparo (perder_movimento, perder_rodada, veneno, reduzir_con) —
requer que `_aplicar_efeito_armadilha` (server.py ~10828) passe a devolver
uma string descritiva por efeito aplicado, em vez de só mandar `gm_say`,
para que o chamador (`_disparar_armadilha`/`_aplicar_armadilha_area`) possa
acumular essas strings e montar a mensagem.

### Cliente — `src/gameState.js`

Novo `case 'trap_result':` no switch de mensagens (perto de `gm_narration`/
`dice_roll`, linha ~1030), que só repassa: `_emit('trapResult', msg)`. Zero
lógica de jogo aqui — é puramente repasse de evento, igual aos outros casos
próximos.

### Cliente — `game.js`

- Novo overlay HTML `#trap-overlay` / `.trap-box` no template injetado
  (mesmo padrão de `#chest-overlay`, perto da linha 204).
- `GS.on('trapResult', msg => { ...enfileira e agenda setTimeout(1200ms)... })`.
- Fila simples (array) para o caso raro de 2 armadilhas disparando na mesma
  casa andada (buraco procedural + armadilha colocável sobrepostos) — mostra
  uma de cada vez, avança a fila ao fechar.
- Fechar por: botão, clique no fundo (fora de `.trap-box`), tecla Esc.
- CSS novo em `game.css` no tema de perigo (borda vermelha/laranja),
  reaproveitando a estrutura de `#chest-overlay`/`#target-modal` já
  existente (overlay fixo + box central).
- Som curto via `_sfxBus()` ao abrir popup de falha (efeito de impacto);
  popup de sucesso não tem som extra dedicado.

## Fora de escopo

- Não mexe no `gm_say`/log de texto existente — continua broadcast pra
  todos, inalterado.
- Não adiciona popup para armadilhas que atingem monstros/servos animados
  (sem cliente correspondente).
- Não adiciona timer de auto-fechamento — só fecha por ação do jogador.
- Não retroalimenta o design das 8 armadilhas em si (dano, DC, efeitos) —
  só a camada de apresentação do resultado.

## Testes

Novo `tools/test_armadilha_popup.py` cobrindo os 4 pontos de disparo:
buraco procedural, armadilha de 1 alvo, armadilha de área (múltiplos
alvos recebendo mensagens individuais), tick progressivo da Incendiária, e
o caso do prisioneiro (mensagem indo para `rescuer_pid`).

## Documentação

Atualizar `CLAUDE.md` com a nova mensagem `trap_result` na tabela de
protocolo Server → Client, seguindo o padrão de descrição das outras
entradas documentadas (ex.: `decor_loot`, `animar_result`).
