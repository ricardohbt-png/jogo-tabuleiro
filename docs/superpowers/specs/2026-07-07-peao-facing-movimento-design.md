# Peão vira na direção do movimento — Design

## Contexto

O peão GLB 3D do paladino (Richard), implementado no dia anterior, sempre
renderiza com `rotY=0` fixo — não gira conforme o herói se move. O usuário
pediu que a frente do peão fique sempre alinhada com a direção do último
passo dado, virando em incrementos de 90°.

O protocolo de movimento já é estritamente ortogonal: `server.py` rejeita
qualquer mensagem `move` em que `abs(dx) + abs(dy) != 1`
(`if room and abs(dx) + abs(dy) == 1: await room.handle_move(...)`). Ou
seja, todo passo é exatamente um dos 4 vetores cardeais — não existe
movimento diagonal a resolver, e não há ambiguidade de desempate.

Existe precedente direto no código: monstros "orientados" (crocodilo,
lagarto) já guardam um campo `facing: [dx, dy]` server-side
(`m["facing"]`), atualizado a cada passo (`_monster_move_step`) ou ao
encarar um alvo (`_face_toward`), e o cliente já usa esse campo pra
orientar a criatura (`mFacing` → `build3DFig` → `_buildOrientedCreature3D`).
Esta feature replica o mesmo mecanismo para jogadores.

## Escopo

Só peões que usam GLB 3D real (hoje: só `paladin`, via
`_GLB_ENABLED_CLASSES`). Classes em billboard 2D (as outras 5) não são
afetadas — o billboard já sempre encara a câmera, então a direção do
passo não muda nada visualmente para elas.

## Mudanças

### `server.py`

Em `handle_move` (por volta da linha 5623, onde `p["pos"] = [nx, ny]` é
confirmado), gravar:

```python
p["facing"] = [dx, dy]
```

`dx`/`dy` aqui já são exatamente um vetor cardeal unitário (garantido pelo
gate `abs(dx) + abs(dy) == 1` antes de chamar `handle_move`), então não
precisa de nenhuma lógica de eixo dominante — é uma atribuição direta,
mais simples até que o `_face_toward` dos monstros (que lida com alvos a
qualquer distância).

Esse campo vai automaticamente no `game_state`, porque `push_state` já
serializa o dicionário inteiro do jogador (`"players": list(self.players.values())`,
sem view filtrada) — mesmo mecanismo que já expõe `m["facing"]` pros
monstros.

**Reset ao entrar em masmorra nova:** o código que reseta a posição do
jogador ao entrar numa masmorra (ou reentrar após a cidade) precisa
limpar `facing` também (`p.pop("facing", None)`), senão o peão herdaria a
última direção da masmorra anterior. Isso garante que todo início de
masmorra começa olhando pro Sul (padrão do cliente quando `facing` está
ausente).

### `game.js`

1. **`build3DFig`** ganha um parâmetro `pFacing` (mesmo padrão de
   `mFacing`, já existente pros monstros). No loop que constrói os peões
   de jogadores (por volta da linha 14001-14014), passar `p.facing` pra
   `build3DFig` e incluir no `JSON.stringify(...)` da chave de cache do
   `obterFig` — exatamente como já acontece com `m.facing` na linha 14042
   pros monstros. Isso faz o peão ser reconstruído (com a nova rotação)
   sempre que a direção mudar, e **não** ser reconstruído à toa quando não
   muda (mesma otimização de cache que já existe).

2. **Novo helper puro `_facingToRotY(facing)`**: converte um vetor
   `[dx,dy]` (ou `undefined`/ausente, quando o jogador ainda não se moveu)
   num ângulo em radianos, múltiplo de `Math.PI/2`. `facing` ausente cai no
   padrão Sul (mesmo valor que `rotY=0` já produz hoje — sem mudança
   visual pra quem nunca se moveu). Os outros 3 valores (Norte/Leste/Oeste)
   são ajustados empiricamente: como a orientação exata depende de como o
   grid (`gx`→X, `gy`→Z) se relaciona com a câmera isométrica e com o eixo
   "frente" do modelo GLB (definido por quem modelou), a forma confiável de
   acertar é testar cada direção ao vivo no navegador (mover o Richard nos
   4 sentidos, comparar visualmente) e ajustar as 4 constantes até baterem
   — não dá pra garantir por dedução geométrica sem ver o modelo girando.

3. **`_makeCharacterPawn`** ganha um parâmetro `rotY`, repassado pra
   `_makeCharacterPawn3D` no lugar do `0` fixo de hoje. Chamadores fora do
   caminho GLB (billboard) ignoram o parâmetro — billboards não giram.

4. Rotação **instantânea**: o novo `rotY` é aplicado direto na construção
   do peão (via `wrap.rotation.y = rotY` dentro de `_makeCharacterPawn3D`,
   já existente) — sem interpolação/animação entre frames.

## Fora de escopo

- Classes em billboard 2D (as 5 que não são paladino) — inalteradas.
- Orientação de monstros/animados/prisioneiro — já resolvida por outro
  mecanismo (`mOriented`/`mFacing`), não tocada aqui.
- Qualquer suporte a movimento diagonal — o protocolo já não permite.
- Animação suave de giro — decidido explicitamente que é instantâneo.

## Teste manual

1. Subir o servidor num worktree isolado, entrar na masmorra como Richard
   (paladino), modo 3D.
2. Mover nas 4 direções (uma de cada vez) e conferir visualmente, via
   screenshot, que a frente do peão (a "cara"/peito do modelo) aponta pro
   lado que ele andou. Ajustar as 4 constantes de `_facingToRotY` até
   bater nos 4 casos.
3. Confirmar que o peão começa olhando pro Sul antes do primeiro passo
   (estado inicial, `facing` ausente).
4. Confirmar que reentrar numa masmorra nova reseta a direção pro Sul
   (mesmo que o jogador tenha terminado a masmorra anterior olhando pra
   outro lado).
5. Confirmar, com outra classe (ex: warrior), que nada muda visualmente —
   segue billboard normal, sem rotação.
