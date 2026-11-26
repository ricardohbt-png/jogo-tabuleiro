# Direção, flanco, costas e altura — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (execução nativa, na própria sessão). Passos com checkbox.

**Goal:** posição do atacante (costas/flanco/altura) vira bônus de acerto simétrico; Ataque Furtivo usa costas/flanco; jogador escolhe a direção ao encerrar o turno.
**Architecture:** classificador puro `_setor_ataque` no servidor + espelho em `gameState.js`; bônus somado ao acerto nos 3 pontos de ataque; `end_turn` aceita `facing`; bússola e marca de frente no cliente.
**Tech Stack:** Python (server.py), JS vanilla (game.js, src/gameState.js), testes `tools/test_*.py|js`.
**Spec:** `docs/superpowers/specs/2026-11-25-direcao-flanco-costas-altura-design.md`

## Global Constraints
- Setor: `rel = atacante − alvo` (centros dos footprints), `dot = rel·f`, `cruz = |rel×f|`; costas se `dot<0 e |dot|>=cruz`; flanco se `cruz>|dot|`; senão frente.
- Bônus de acerto: costas +2, flanco +1, altura +1/nível de terreno acima (máx +2); soma máx **+4**. Sem bônus de dano/crítico; voo não conta.
- Alvo incapaz (dormindo, paralisado, petrificado, enredado, perde_turno, monstro não ativo em combate) = costas.
- Direção padrão `[0,1]` (monstro orientado sem direção: `[-1,0]`).
- Furtivo: base = oculto/oculto_vela OU costas; II = + flanco + aliado adjacente (mantido); III e Defesa Impecável inalterados.
- `end_turn.facing` só `[±1,0]`/`[0,±1]`, aplicado após as recusas existentes; ausente/inválido = mantém.
- game.js/server.py/CLAUDE.md são CRLF: editar com Edit ou script que normaliza `\r\n`. `GS.on` tem 1 callback por evento. `t` não pode ser sombreado.

## Review Focus
1. Alvo 2×2 (centro do footprint) e atacante adjacente em diagonal (empate costas/flanco) → costas, como 1×1.
2. Herói sem `facing` (entrada na masmorra) → frente para o sul, sem erro.
3. `end_turn` recusado (magia pendente, fora da vez) não pode mudar a direção.
4. Prévia de ataque (`prever_ataque`) tem de bater com o ataque real.
5. Encerrar com servos/janela pós-turno: bússola só no 1º encerrar; auto-encerrar e timeout mantêm direção.

---

### Task 1: Classificador de posição (servidor)
**Files:** Modify `server.py` (junto de `_cobertura_baixa_bonus`); Create `tools/test_direcao_flanco.py`.
**Interfaces — Produces:**
- `GameRoom._facing_de(ent) -> [int,int]` (padrão `[0,1]`; orientado sem direção `[-1,0]`).
- `GameRoom._alvo_incapaz(alvo) -> bool`.
- `GameRoom._setor_ataque(atacante, alvo) -> "frente"|"flanco"|"costas"` (usa centros dos footprints via `_monster_tiles` se for monstro).
- `GameRoom._bonus_altura(atacante, alvo) -> int` (0..2, por `_elevacao_terreno` das casas).
- `GameRoom._bonus_posicional(atacante, alvo) -> {"setor","costas","flanco","altura","total"}` com total ≤ 4.
- [ ] Teste (RED): tabela 3/2/3 nas 4 direções (alvo em (5,5), atacantes nas 8 casas), 2×2, alvo incapaz → costas, altura +1/+2/teto, soma limitada a 4, herói sem `facing` → sul. Rodar: `python -X utf8 tools/test_direcao_flanco.py` → falha (funções inexistentes).
- [ ] Implementar as 5 funções; rodar até passar.

### Task 2: Aplicar o bônus nos ataques e no Furtivo (servidor)
**Files:** Modify `server.py` (`_modificadores_ataque_heroi`, `handle_throw_item` bloco de acerto, `_execute_one_monster_attack_impl`, `_verificar_ataque_furtivo`, `handle_end_turn`, descrição de `ladino_furtivo_2`); Test `tools/test_direcao_flanco.py`.
**Interfaces — Consumes:** Task 1. **Produces:** chave `posicional` no retorno de `_modificadores_ataque_heroi`; `end_turn` aceita `facing`.
- [ ] Testes (RED): ataque de herói pelas costas sobe `eff_atk` em 2 (e a prévia igual); monstro atacando herói de costas sobe `m_atk`; arremesso soma; Furtivo: base dispara por costas e não por flanco, II dispara por flanco e por aliado adjacente, sem espec nem posição não dispara, `defesa_impecavel` bloqueia; `end_turn` com `facing` válido grava, inválido/ausente mantém, e recusa (fora da vez / magia pendente) não grava.
- [ ] Implementar; narrar o bônus como a cobertura (`narracao.posicao_costas/flanco/altura`, PT/EN em `src/lang/narracao.js`).
- [ ] Rodar o arquivo + `test_ladino_espec.py`, `test_previsao_ataque.py`, `test_cobertura*`/`test_sombra_objetos.py`, `test_guilda.py`.

### Task 3: Espelho no cliente e protocolo
**Files:** Modify `src/gameState.js` (`setorAtaque`, `bonusPosicional`, `endTurn(facing)`, exports); Create `tools/test_direcao_flanco_cliente.js`.
**Interfaces — Produces:** `GS.setorAtaque(state, atacante, alvo)`, `GS.bonusPosicional(state, atacante, alvo)` (mesmo contrato da Task 1), `GS.endTurn(facing=null)`.
- [ ] Teste (RED): paridade com a tabela da Task 1 e `endTurn([0,-1])` envia `{type:'end_turn', facing:[0,-1]}`; sem argumento não envia `facing`.
- [ ] Implementar; rodar o teste.

### Task 4: Bússola, marca de frente e tooltip (cliente)
**Files:** Modify `game.js`, `game.css`, `src/lang/interface.js`; Create `tools/test_bussola_direcao.js`.
- [ ] Teste (RED): `endTurn()` na vez do herói abre `#bussola-direcao` (não envia); setas/WASD mudam a escolha, Enter confirma e envia `facing`, Esc cancela sem enviar; `endTurn({semBussola:true})` (auto-encerrar) envia sem `facing`; com peça de servo pendente não abre.
- [ ] Implementar bússola (4 setas + diagrama frente/flanco/costas, atalhos), troca em `endTurn`, `_autoTurn...` usa `semBussola`.
- [ ] Marca de frente: cunha no chão de cada herói/monstro vivo e visível, 2D (`drawHeroSprite` vizinhança/laço de monstros) e 3D (pool atualizado a cada quadro, sem entrar na assinatura do peão); herói em escolha usa a direção em prévia.
- [ ] Tooltip do monstro: linha "Costas +2 / Flanco +1 / Altura +N" ao lado da cobertura (`_coberturaTooltipHTML`).
- [ ] Textos PT/EN (`ui.direcao.*`), linha na ajuda; `tools/test_interface.py`, `tools/dividas.py`, `tools/test_peao_sem_reconstrucao.js` verdes.

### Task 5: Documentação e suíte final
- [ ] Nota em `CLAUDE.md`; rodar `tools/test_direcao_flanco.py`, `tools/test_direcao_flanco_cliente.js`, `tools/test_bussola_direcao.js`, `test_handler_smoke.py`, `test_solo_grupo.py`, `test_tutorial_salas.py`, `tools/dividas.py --strict`; revisão final do diff.
