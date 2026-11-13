# Bandido no Bestiário — desenho

**Status:** desenho aprovado em conversa; aguardando revisão desta especificação.

## Objetivo

Adicionar ao Bestiário um monstro humanoide Bandido que use furtividade, ataque
furtivo, armadilhas e veneno. A ficha deve aproveitar os valores do Ladino e a
arte já criada para o inimigo e sua miniatura 2D.

## Ficha e balanceamento

- Tipo nativo: `bandido`; ND 1.
- Atributos: FOR 10, DES 18, CON 12 e INT 10.
- PV: 9; CA base: 14; movimento: 7.
- Salvamentos e bônus de ataque iguais aos do Ladino; ataque principal com
  bônus +4.
- Sempre equipa o item `cloak` (Manto), que concede +1 CA: a CA efetiva deve
  ser 15. A ficha e o cálculo de equipamento não podem somar o bônus duas vezes.
- Arma principal sorteada em partes iguais entre adaga e bordão. Quando a
  principal for adaga, há 50% de chance de equipar uma segunda adaga. O ataque
  com duas adagas conserva o padrão de dois ataques da arma secundária, sem
  duplicar o bônus do Manto.
- Reutilizar `assets/retratos/monstros/bandido.png` como retrato e
  `assets/pawns/monstros/bandido/bandido.png` como miniatura 2D.

## Habilidades e IA

- **Esconder-se 1:** a IA pode tentar se esconder, usando percepção dos
  observadores como dificuldade. Sucesso oculta o bandido até o ataque; uso
  fica em recarga por 3 rodadas.
- **Ataque Furtivo 1:** o primeiro ataque ao sair da ocultação recebe vantagem
  e +2d4 de dano extra. A ocultação é consumida no ataque.
- **Preparar Armadilha:** no nascimento, cada instância sorteia uma única
  fórmula entre `lamina_escondida`, `armadilha_incendiaria` e `rede`. A IA pode
  preparar essa fórmula novamente quando o cooldown de 3 rodadas permitir.
  Colocação usa uma casa caminhável e livre ao lado do bandido; não requer
  jogador, ouro, fome ou sede. A ação de preparar substitui o ataque daquele
  turno, mas não impede o movimento normal da IA. O bandido evita disparar sua
  própria armadilha; heróis continuam podendo ativá-la ao pisar na casa.
- **Veneno Fungo Acre:** em 20% dos nascimentos, a bolsa recebe 1 ou 2 frascos
  (`veneno_fungo_acre`), com quantidade sorteada igualmente. Se não houver uma
  dose ativa na arma, a IA pode consumir um frasco para envenená-la; um acerto
  consome a dose aplicada.

## Equipamento e saque

- O Manto é garantido em toda instância; arma principal e segunda adaga seguem
  as rolagens descritas acima.
- A morte concede uma quantidade sorteada uniformemente de 2 a 10 moedas de
  ouro (inclusive).
- Armas e Manto equipados seguem o fluxo existente de saque de equipamento.
- O saque adicional garantido nesta proposta é o ouro; não se adiciona uma regra
  especial de drop para frascos de veneno.

## Integração

- Adicionar uma definição nativa de monstro e uma rotina de inicialização por
  instância para sorteios de arma, armadilha, veneno e ouro.
- Criar um tipo de IA nativo para coordenar esconder-se, ataque furtivo,
  preparação da armadilha e uso de veneno sem alterar a IA dos outros monstros.
- Usar os cooldowns autoritativos do monstro e o catálogo global `ARMADILHAS`;
  armadilhas do bandido devem manter os efeitos, salvamentos, efeitos visuais e
  sincronização já existentes.
- Marcar a autoria/facção da armadilha de modo que o bandido não a dispare ao
  se mover. A autoria também não deve creditar ouro/XP como se o ID do monstro
  fosse um jogador.
- Fazer a ficha do Bestiário exibir as habilidades, equipamento e ND 1; usar
  os assets de retrato e peão acima.
- Preservar definição, loot, cooldown, equipamentos e estado das demais
  criaturas.

## Critérios de aceitação

1. Uma instância nova tem PV 9, atributos 10/18/12/10, CA efetiva 15, movimento
   7, salvamentos do Ladino e ND 1.
2. A arma sorteada é adaga ou bordão; a segunda adaga só aparece conforme a
   chance de 50% definida para a adaga principal, e os ataques usam o bônus +4
   previsto.
3. A ocultação respeita recarga de 3 rodadas e o ataque furtivo de nível 1 só
   recebe vantagem e +2d4 ao sair dela.
4. Cada instância conhece exatamente uma das três armadilhas; ela pode ser
   preparada respeitando o cooldown, aciona o efeito existente quando um herói
   pisa nela e não acerta o próprio bandido.
5. Só 20% das instâncias recebem 1–2 frascos de Fungo Acre; o veneno aplicado
   consome uma dose após um acerto.
6. Cada morte deixa entre 2 e 10 moedas; arte de retrato e miniatura aparecem
   no Bestiário e no tabuleiro 2D.

## Fora do escopo

- Novas fórmulas, efeitos ou assets de armadilhas.
- Mudanças nas regras do Ladino, no Manto ou no veneno Fungo Acre.
- Novas variantes visuais do Bandido ou modelos 3D.

## Pontos de atenção para implementação

- `make_monster` normaliza CA a partir de DES e armadura natural; o bônus de
  equipamento precisa ser aplicado uma vez, resultando em CA final 15.
- Movimento de monstro usa 6 como padrão se a ficha não declarar exceção; a
  configuração do Bandido deve preservar 7.
- A regra genérica de ataque furtivo e a IA do Assassino Goblin são referências
  de comportamento, não devem ser alteradas em conjunto com o Bandido.
- A IA precisa respeitar limites do mapa, footprint, ocupação, armadilhas já
  existentes e validade do turno antes de preparar a sua armadilha.
