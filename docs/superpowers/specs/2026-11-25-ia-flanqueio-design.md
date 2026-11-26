# IA de flanqueio dos monstros espertos — design e plano

## Intenção
Fazer a direção do herói importar de verdade: monstros "espertos" contornam o herói para
atacar pelas costas ou pelo flanco, em vez de parar na primeira casa adjacente. Continuação
da spec `2026-11-25-direcao-flanco-costas-altura-design.md` (a IA era não-objetivo dela).

## Regras (aprovadas pelo autor)
- **Quando age:** antes da IA normal do monstro (`_run_monster_ai`), só para monstro esperto,
  1×1, corpo a corpo com alcance 1, contra herói ou servo (alvo prioritário da própria IA).
- **Escolha:** entre as casas adjacentes ao alvo que o monstro alcança com o movimento que
  ainda tem (BFS cardinal, sem casas ocupadas, perigosas ou reservadas), pontua costas 2,
  flanco 1, frente 0; maior pontuação, desempate pelo caminho mais curto.
- **Nunca perde o ataque:** só reposiciona se a melhor casa for alcançável neste turno, melhor
  que a atual e não for "frente". Senão a IA normal segue como hoje. O passo gasta o orçamento
  de movimento compartilhado (`_water_moves_left`), então não há movimento em dobro.
- **Quem é esperto:** `bandido`, `goblin_assassino`, `lobo_cinzento` (e o Alfa
  `lobo_cinzento_customizado`), `bugbear_sombras`; fichas personalizadas com perfil `tatico`,
  `emboscador` ou `cacador`; qualquer ficha com `flanqueia: true` (`false` desliga).
  Brutos e mortos-vivos ficam de fora, assim como quem ataca à distância e criaturas grandes.

## Não-objetivos
Cooperação entre monstros, fugir de ser flanqueado, opção no editor de criaturas (a ficha já
aceita `flanqueia` por código/JSON), seta de intenção refletir a casa de flanqueio.

## Testes
`tools/test_ia_flanqueio.py`: costas alcançável, não esperto não move, melhor casa fora do
orçamento, já nas costas, flanco→costas, casa ocupada/perigosa, à distância, 2×2, `flanqueia`
liga/desliga, perfil personalizado, e o ataque real do bandido pelas costas (+2).
