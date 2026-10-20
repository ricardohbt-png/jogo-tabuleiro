# Ignus Fatus e Fata Morgana — especificação de design

## Problema

O jogo tem arte e preço planejados para dois consumíveis de ilusão, mas ainda não
os oferece no mercado nem possui uma entidade que possa atrair a IA dos monstros.
O objetivo é transformar essas imagens em iscas móveis ou estacionárias que
desviem monstros automáticos dos heróis por um período curto.

## Decisões aprovadas

- `Ignus Fatus`: preço base de 45 moedas, ação bônus para usar, duração de 2
  rodadas e imagem fantasmagórica do herói. A ilusão permanece parada.
- `Fata Morgana`: preço base de 120 moedas, ação bônus para usar, duração de 4
  rodadas e imagem mais realista do herói. O jogador pode movê-la.
- A ilusão é uma entidade temporária separada de jogadores e monstros. Ela não
  tem vida, não ataca, não interage com objetos e não bloqueia movimento.
- A criação exige uma casa livre e visível a até 6 casas do herói. A posição
  inválida deve ser recusada antes de consumir o item ou a ação bônus.
- Cada herói pode manter no máximo uma ilusão ativa. Tentar usar outro item
  enquanto a sua ilusão existir é recusado antes de consumir item ou ação bônus.
- A Fata Morgana recebe, no início de cada turno de seu dono e antes das ações
  do herói, uma ordem de movimento de até 6 casas pelo caminho válido. Isso não
  gasta o movimento do herói. Há no máximo uma ordem por turno; se o dono
  começar as ações do herói sem mover a ilusão, ela fica parada naquele turno.
  O Ignus Fatus não recebe ordens de movimento.
- Monstros com IA que percebam a ilusão passam a persegui-la, mesmo que também
  possam perceber heróis. Monstros sob controle manual do Mestre não têm sua
  escolha substituída pela isca.
- Quando um monstro alcança a ilusão e tenta atacá-la, o primeiro ataque a
  dissipa sem rolagem de dano ou efeito sobre qualquer herói; o turno desse
  monstro termina. Outros monstros ainda podem escolher a mesma ilusão enquanto
  ela existir.
- Ao expirar ou ser dissipada, os monstros deixam de considerá-la e retomam a
  busca normal por alvos.
- Ícones já existentes: `assets/itens/ignus_fatus.png` e
  `assets/itens/fata_morgana.png`.

## Fluxo de uso

1. O herói escolhe o item e uma casa livre dentro do alcance e da linha de
   visão.
2. O servidor valida o turno, a ação bônus, o item, a casa, o alcance e a linha
   de visão. Só depois remove uma unidade da bolsa e marca a ação bônus como
   usada.
3. O servidor cria a entidade com identificador próprio, dono, sala, posição,
   tipo da ilusão, rodada de criação e rodada de expiração.
4. Para Fata Morgana, no início dos turnos subsequentes do dono, o cliente
   oferece mover ou deixar a ilusão parada. O jogador pode indicar um destino,
   limitado a 6 casas e às regras de caminho do tabuleiro. O servidor revalida o
   caminho e aceita no máximo uma ordem por turno. Se o jogador começar as
   ações do herói sem dar uma ordem, a ilusão fica parada naquele turno.
5. A IA inclui ilusões ativas como alvos percebidos. O alvo da ilusão tem
   prioridade para monstros automáticos que a percebem; seus movimentos e
   decisões continuam limitados à sala e às regras de percepção já existentes.
6. Uma tentativa de ataque contra a ilusão a remove antes da resolução normal
   de ataque e encerra o turno do monstro que a atacou.
7. A expiração remove a ilusão e publica o estado atualizado. A IA volta a
   selecionar alvos usando o comportamento normal.

## Loja

Os dois itens entram no catálogo `SHOP_MERCHANT`, usando `item_slot: "bag"`, o
efeito próprio de criação de ilusão, os ícones já existentes e os preços base
aprovados. Também entram na allowlist de estoque dos mercadores em
`city_shops.json`; cadastrar só no catálogo não os torna compráveis nas cidades.

## Estado e apresentação

- As entidades vivem em coleção efêmera da sala e são incluídas em `game_state`
  para renderização e seleção de movimento. Não entram no save durável da
  campanha; após carregar uma sessão, não há isca antiga em execução.
- A apresentação usa os PNGs dos itens como referência visual. A miniatura no
  tabuleiro usa a imagem correspondente ao tipo, com opacidade reduzida no
  Ignus Fatus e aparência mais sólida na Fata Morgana.
- Quando a entidade expira ou se dissipa, é removida do estado publicado e da
  interface sem deixar bloqueio de casa, alvo residual ou seleção ativa.
- A descrição dos itens informa ação bônus, alcance, duração e comportamento de
  movimento de cada versão.

## Limites e casos de borda

- Uma ilusão só afeta monstros que a percebam pela verificação de visão e linha
  de visão existentes; ela não revela monstros nem ignora ocultação.
- A isca não substitui comandos manuais do Mestre e não atrai monstros de outra
  sala.
- A expiração é autoritativa no servidor. A entidade deixa de ser alvo assim que
  a rodada de expiração é alcançada, inclusive se o dono desconectar.
- Uma segunda ilusão do mesmo herói é recusada antes de cobrar item ou ação
  bônus, conforme a regra de uma ativa por herói.
- Ataques em área ou efeitos sem alvo direto não escolhem a ilusão como centro
  automaticamente; somente a decisão de alvo da IA e ataques diretos entram
  nesta primeira versão.

## Fora de escopo

- Controle de monstros manuais pelo Mestre por meio da isca.
- Ataques, interações, bloqueio de passagem, dano ou condições sobre a ilusão.
- Mudança nas regras gerais de percepção, iniciativa ou movimentação de heróis.
- Persistir ilusões em saves.

## Verificação planejada

Cobertura de servidor para compra, uso, consumo atômico, posição inválida,
expiração, movimento, seleção de alvo, dissipação sem dano e exclusão de monstros
manuais. Cobertura de cliente para exibição da arte, seleção e movimento da Fata
Morgana, atualização após expiração/dissipação e controles de teclado/gamepad.
Uma verificação de fluxo real no tabuleiro deve confirmar que a ilusão aparece,
é controlável e atrai um monstro automático.
