# Ensino da direção e seta de intenção do flanqueio — design

Continuação das specs de direção/flanco e de IA de flanqueio (2026-11-25).

## Item 2 — seta de intenção
`_monster_flank_plan` (só leitura) é a fonte única da casa de flanqueio; IA e `monster_intent`
a usam. A intenção ganha `setor` e `casa_ataque` passa a ser a casa de costas/flanco; `facing`
do alvo e `flanqueia` do monstro entram na assinatura do cache. Tooltip: "pelas costas (+2)".

## Item 1 — ensinar a direção
- Lição única `fala_direcao` (ordem 34): o validador recusa duas lições com a mesma ordem.
  Guia de 4 passos (olhar a cunha, ir às costas, atacar por trás, encerrar escolhendo a direção).
  Passo 3 só avança com `requer_setor: costas`; a tarefa é `escolher_direcao` (verbo novo).
- Dica de primeira vez na bússola (localStorage); helper `tools/posicao_util.virar_para` para testes.

## Fora
Lição por classe (Ladino e o Furtivo), renumerar a trilha, campo `flanqueia` no editor.
