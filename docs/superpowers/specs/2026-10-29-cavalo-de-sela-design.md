# Cavalo de Sela — desenho

## Intenção

Adicionar ao jogo um cavalo comum, de ND baixo, que possa servir futuramente como base para a regra de montaria. Nesta etapa entram a ficha nativa, seu comportamento em combate e a miniatura PNG; a regra para personagens montados fica para uma etapa posterior.

## Ficha aprovada

- Tipo `cavalo_sela`, nome `Cavalo de Sela`, ND 1/4, 16 PV, CA 11 e deslocamento 8.
- Atributos: Força 16, Destreza 12, Constituição 14 e Inteligência 2; salvamentos Fortitude +4, Reflexos +3 e Vontade +1.
- Um ataque de Coice +4, `1d6+2` de dano físico.
- Animal médio, sem spawn aleatório e sem recompensa de ouro.
- Miniatura PNG transparente em `assets/pawns/monstros/cavalo_sela/cavalo_sela.png`; não exige um modelo GLB próprio.
- Comportamento passivo: não inicia ataques; tenta fugir quando ameaçado e só reage com coice após ser provocado.

## Habilidade especial

`Disparada` dobra o deslocamento do cavalo naquele turno e tem recarga de quatro rodadas. Enquanto estiver solto, a IA pode ativá-la ao fugir de uma ameaça. Se estiver montado, o jogador escolhe quando ativá-la; essa interface depende da futura regra de montaria e não faz parte desta etapa. A habilidade não concede ataque extra nem bônus de dano.

Ao fugir, o deslocamento dobrado permite dois passos de afastamento. O servidor anuncia a habilidade quando ela é usada e mantém perigos de terreno aplicados em cada casa atravessada.

## Abordagens

1. Reutilizar a IA da vaca. Não cobre o deslocamento maior nem a Disparada e mistura estados de espécies diferentes.
2. Criar ficha e IA passiva próprias para o Cavalo de Sela (escolhida). Mantém a vaca intacta, permite a fuga acelerada e deixa espaço para a regra futura de montaria.
3. Criar já uma montaria controlável completa. Isso exigiria resolver ações, ocupação de casas e movimento do cavaleiro, além da ficha; fica fora do escopo aprovado.

## Restrições e critérios

- Não alterar ficha, IA, arte ou drops da vaca.
- Não incluir o cavalo em encontros aleatórios nem em mapas existentes.
- Não criar GLB, sistema de domesticação, loot ou montagem de personagem nesta etapa.
- Registrar a ficha e a recarga em `CLAUDE.md`, fonte de arquitetura do projeto.
