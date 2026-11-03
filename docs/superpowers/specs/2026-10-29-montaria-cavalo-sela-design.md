# Montaria do Cavalo de Sela — desenho

## Intenção

Permitir que um herói monte um Cavalo de Sela durante uma masmorra e use sua velocidade sem ganhar um segundo turno ou um ataque gratuito. O usuário escolheu a abordagem de montaria em combate, com deslocamento do cavalo substituindo o movimento normal do herói.

## Estado atual do projeto

O servidor controla o movimento autoritativamente em `handle_move`/`handle_move_path`. Cada casa consome o orçamento `moves_left`, cujo custo aumenta em certos terrenos. `_moves_base` combina a velocidade do herói com bônus e penalidades; classes têm velocidade-base entre 5 e 7, enquanto o cavalo tem 8. Heróis já têm uma ação bônus por turno (`bonus_action_used`). O cavalo tem uma entidade própria de monstro e PNG 2D, mas ainda não existe vínculo entre herói e montaria.

## Desenho proposto

- Só um Cavalo de Sela vivo e não provocado pode ser montado. O herói deve estar numa casa adjacente, e cada cavalo aceita um único cavaleiro. Montar custa a ação bônus; não exige teste de perícia porque é um cavalo de sela treinado.
- Desmontar também custa ação bônus e exige escolher uma casa ortogonal adjacente livre. Enquanto montado, cavalo e cavaleiro compartilham posição e contam como um único ocupante para movimento e colisões.
- O movimento-base do herói passa a ser 8, substituindo seu `spd` de classe. Bônus e penalidades atuais do herói continuam se aplicando; custos de terreno, obstáculos, armadilhas e demais validações continuam iguais.
- Enquanto montado, o cavalo não executa sua IA nem seu ataque. O herói conserva suas ações normais de ataque, magia e habilidade; a montaria não concede ações extras.
- **Alvo de ataques:** um ataque de alvo único mantém a identidade escolhida: se mirou o herói, atinge o cavaleiro; se mirou o Cavalo de Sela, atinge o cavalo. Ataques de área atingem ambos por ocuparem a mesma casa. A IA hostil mantém o alvo que já escolheu; ela continua selecionando o herói como alvo normal.
- **Disparada** é ativada pelo cavaleiro com a ação bônus, antes de se mover. Nesse turno, dobra o movimento-base da montaria de 8 para 16; bônus e penalidades do herói são aplicados uma vez depois desse valor. Recarga de quatro rodadas guardada no cavalo, para trocar de cavaleiro não reiniciar a recarga. Não se acumula multiplicativamente com outros efeitos que dobrem movimento.
- O cavalo continua com PV próprios e pode ser atacado. Se morrer, o herói é desmontado automaticamente na mesma casa, sem dano de queda. Se o herói morrer ou a partida sair da masmorra, o vínculo é encerrado; a montaria não segue para outra sala/campanha nesta primeira versão.
- O PNG do cavalo aparece sob o peão do herói enquanto montado; não será criado um GLB ou uma pose de cavaleiro por classe nesta etapa.

## Abordagens

1. **Montaria em combate com velocidade substituída (escolhida).** O cavaleiro usa 8 de movimento, e Disparada eleva para 16 sob ação bônus e recarga. Dá uso tático ao cavalo sem somar o movimento do herói nem os ataques do animal.
2. **Disparada fora de combate.** O herói poderia usar o cavalo durante lutas, mas só dobraria a velocidade fora do combate. Reduz o risco de atravessar salas num turno, porém separa a habilidade da ficha de combate.
3. **Montaria só em exploração.** Mais simples para colisão e ação, mas não oferece o uso tático que o usuário escolheu.

## Objetivos e limites

- Estado de montaria autoritativo e sincronizado para Solo e Multiplayer, incluindo reconexão durante a masmorra.
- Preservar movimento por caminho, custos de terreno, armadilhas e bloqueios existentes.
- Não somar velocidade de cavalo e velocidade do herói; não dar turno, ataque ou ação adicional ao cavalo montado.
- Nesta versão, não há domesticação, inventário de montarias, compra/venda de cavalos, viagem entre salas montado, outras espécies montáveis, animação de cavaleiro ou modelo 3D.

## Decisões de implementação

- Comandos autoritativos: `montar_cavalo {monster_id}`, `desmontar_cavalo {tx,ty}` e `disparada_cavalo`.
- Os botões aparecem na lista de habilidades do painel do herói; desmontar abre escolhas entre as casas ortogonais adjacentes.
- O estado usa `cavalo_montado_id` no herói e `cavaleiro_id` no cavalo, ambos enviados no estado de sala para reconexão.
- `moves_left` recebido pelo cliente alimenta a prévia de movimento; o início do turno usa `_moves_base` com base 8 (ou 16 durante Disparada), depois preserva os modificadores atuais.
- O verificador de movimento ignora apenas o cavalo ligado ao próprio herói; demais entidades e bloqueios continuam usando as validações existentes.
