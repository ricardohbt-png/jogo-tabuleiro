# Bardo Inimigo — especificação de design

## Objetivo

Adicionar ao Bestiário um monstro Bardo baseado no personagem Bardo do jogo. Ele deve manter os atributos e características de nível 1 do personagem, sortear armadura, arma e instrumento, apoiar monstros aliados com a Canção Heroica e usar Provocação e as habilidades do instrumento durante o combate. A ficha deve usar a miniatura já criada em `assets/pawns/monstros/bardo/bardo.png`.

## Ficha e equipamento

- Atributos: Força 10, Destreza 16, Constituição 12 e Inteligência 12.
- Valores derivados do Bardo nível 1: 9 PV, movimento 6, ataque +3, Fortitude +0, Reflexos +2 e Vontade +2.
- Uma armadura escolhida uniformemente entre Manto, Armadura de Couro e Armadura de Couro e Placas. A CA resultante será 13, 14 ou 15, respectivamente.
- Uma arma escolhida uniformemente entre Besta de Mão, Bordão, Cajado de Madeira, Chicote, Adaga e Besta. Cada opção usa uma mão e pode coexistir com o instrumento na mão secundária.
- Besta de Mão e Besta têm 20 virotes. No sorteio da munição, o conjunto inteiro será incendiário com chance de 10% para Besta de Mão ou 5% para Besta; caso contrário, será comum.
- Um instrumento sorteado uniformemente entre Harpa, Tambor de Guerra, Sino, Alaúde, Trompa de Guerra, Lira, Flauta, Violino e Gaita.
- Qualidade sorteada independentemente: Velho 40%, Rústico 30%, Padrão 25%, Refinado 5%.
- Origem sorteada independentemente: Humana 99%, Élfica 0,5%, Anã 0,5%. Os bônus da origem e da qualidade serão gerados pelo sistema atual de instrumentos.
- Ao morrer, deixa uma quantidade inteira uniforme de 5 a 15 moedas de ouro.

## Habilidades e IA

### Canção Heroica

- Uma vez por combate, o bardo pode iniciar a Canção.
- Rola `1d4+1` para determinar quantos atributos recebem bônus. Seleciona-os pela ordem fixa: Acerto, Dano, CA, Movimento e Resistência.
- Cada atributo selecionado concede +1 aos monstros aliados dentro do alcance da Canção por `1d4+2` rodadas. O alcance reutiliza a regra atual da Canção Heroica (5 casas).
- O Alaúde aplica sua habilidade passiva conforme a qualidade quando a Canção estiver ativa.

### Provocação

- Recarga de 4 rodadas; escolhe um herói dentro do alcance atual da Provocação (3 casas).
- O efeito dura até 3 turnos do herói. Em cada turno, ele faz um teste de Vontade CD 11. Sucesso encerra a Provocação.
- Em caso de falha, o jogo conduz o herói por um caminho válido em direção ao bardo e executa um ataque básico contra ele assim que houver alcance. Após esse ataque, devolve ao jogador o controle do movimento restante e das ações bônus disponíveis.
- Se ainda não for possível alcançar o bardo, o herói avança pelo caminho disponível; o ataque é realizado assim que houver uma posição válida e o efeito ainda estiver ativo.

### Habilidade do instrumento

- Instrumentos ativos podem usar sua habilidade uma vez a cada 4 rodadas, usando os efeitos, estatísticas e alvos existentes para cada instrumento.
- A IA tenta usar a habilidade quando ela puder produzir um efeito válido; se não houver situação ou alvo válido, mantém a habilidade disponível e segue para outra ação.
- O Alaúde é passivo e se integra à Canção; não recebe ativação ou recarga independente.
- Ordem de decisão: Canção se ainda não usada e houver aliados para beneficiar; Provocação se pronta e houver herói válido; habilidade do instrumento se pronta e útil; caso contrário, ataque básico.
- O bardo executa no máximo uma dessas ações especiais por turno.

## Nível de Desafio e saque

- ND inicial: 1, alinhado aos valores básicos do Bardo e ao patamar do Bandido; os efeitos de suporte entram na avaliação do encontro em grupo.
- Saque de ouro: `5–15` (inclusive), distribuído uniformemente.
- O monstro usará o registro de imagem `bardo` para renderizar a miniatura no tabuleiro.

## Integração

A ficha será registrada no Bestiário com um `ai_type` próprio. O servidor gerará equipamento e munição no nascimento do monstro e cuidará dos estados temporários, recargas, buffs e Provocação. A IA dos monstros aliados receberá os bônus da Canção; o fluxo de turno do herói será adaptado para a movimentação e o ataque compulsórios da Provocação, devolvendo o controle depois. O editor e o catálogo de monstros devem preservar esses campos ao salvar e exportar.

## Critérios de aceite

1. O Bardo aparece no Bestiário com os atributos, salvamentos, movimento, PV e imagem especificados.
2. Seus sorteios de armadura, arma, instrumento, qualidade, origem e munição obedecem às probabilidades acima.
3. A Canção e a habilidade do instrumento concedem os efeitos e durações descritos e respeitam suas recargas.
4. A Provocação aplica o salvamento a cada um dos três turnos e, em falha, conduz o herói até o bardo, executa o ataque e devolve o controle do restante do turno.
5. Ao derrotar o Bardo, o saque de ouro fica entre 5 e 15 moedas.
