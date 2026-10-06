# Cinto de Utilidades — design

**Data:** 2026-10-06
**Status:** aguardando revisão da especificação atualizada; desenho conversacional aprovado.
**Escopo:** dois itens equipáveis com compartimentos próprios para consumíveis, armazenamento persistente e transferência do conteúdo junto com cada cinto.

## 1. Objetivo

Criar duas versões do item associadas à imagem `assets/itens/cinto_e_bolsos.png` e disponíveis no mercador e como saque de masmorra:

- **Cinto de Utilidades** — custa 80 moedas e oferece quatro espaços.
- **Cinto com Bolsos** — custa 30 moedas e oferece dois espaços.

Equipado, cada versão disponibiliza compartimentos separados da bolsa normal para agrupar consumíveis iguais. O inventário atual apresenta e opera esses compartimentos junto da bolsa, sem abrir uma janela extra.

A descrição do item deve explicar a capacidade, o agrupamento e que o acesso aos itens guardados exige o cinto equipado.

## 2. Decisões aprovadas

1. Cada cinto ocupa um espaço geral de equipamento. O personagem pode equipar até dois cintos nos espaços gerais, inclusive uma combinação dos dois modelos. Cada Cinto de Utilidades concede quatro espaços e cada Cinto com Bolsos concede dois; a capacidade total é a soma dos cintos equipados, até oito.
2. Os compartimentos aparecem numa seção da janela de inventário já existente.
3. Cada compartimento guarda até quatro unidades do mesmo consumível. A quantidade aparece no espaço.
4. Os espaços têm tom marrom. O ícone do item é menor que o ícone normal da bolsa, mas a área clicável permanece do tamanho normal.
5. São aceitos todos os tipos citados: bombas incendiárias, fogo grego, ácido, cola, frascos de veneno e poções.
6. O jogador pode arrastar itens entre a bolsa normal e os compartimentos. A movimentação manual transfere uma unidade por vez.
7. Itens coletados vão automaticamente para um compartimento do cinto equipado quando houver espaço adequado. Se não houver, vão para a bolsa normal. Se a bolsa também estiver cheia, a coleta é recusada e o item continua na origem.
8. Ao desequipar um cinto, seu conteúdo permanece guardado nele. O conteúdo fica inacessível até o cinto ser equipado novamente, e o jogador recebe uma mensagem explicando isso.
9. O conteúdo é parte do próprio item. Encontrar, pegar, largar ou transferir qualquer versão move também tudo que estiver guardado nela.
10. O mercador vende o Cinto de Utilidades por 80 moedas e o Cinto com Bolsos por 30 moedas. O catálogo de saque permite encontrar ambas as versões vazias ou pré-carregadas.

## 3. Capacidade e identidade dos itens

Cada cinto possui uma lista estável de posições: quatro, numeradas de 0 a 3, no Cinto de Utilidades; duas, numeradas de 0 a 1, no Cinto com Bolsos. Cada posição contém zero ou uma pilha. Uma pilha representa um item elegível e uma quantidade inteira de 1 a 4. Os dois cintos são compartimentos independentes.

Cada item guarda essas posições no campo serializável `utility_belt_slots`, cujo comprimento é determinado pelo ID do modelo equipado: quatro entradas para `cinto_utilidades`, duas para `cinto_com_bolsos`. Cada entrada é `null` ou `{ "item": <dicionário completo do item>, "quantity": <1..4> }`. Cada dicionário de cinto tem sua própria lista, sem lista global no personagem.

Itens iguais são identificados pelo mesmo ID de item elegível. Dentro de cada cinto, um tipo ocupa no máximo uma pilha. O outro cinto pode ter uma pilha independente do mesmo tipo, também com até quatro unidades. Dois Cintos de Utilidades permitem oito tipos e até oito unidades de um tipo; duas versões com bolsos permitem quatro tipos e até oito unidades de um tipo; uma unidade de cada modelo permite seis tipos e até oito unidades de um tipo.

A elegibilidade é restrita aos consumíveis dos grupos aprovados: arremessáveis e frascos de efeito, poções e venenos. Armas, equipamento, munição, pergaminhos e outros itens não entram nos cintos.

## 4. Coleta automática

Com um ou mais cintos equipados, o servidor roteia uma aquisição nesta ordem:

1. Procurar uma pilha incompleta do mesmo ID nos cintos equipados, na ordem do espaço geral 1 e depois 2. Acrescentar uma unidade à primeira encontrada.
2. Se não houver pilha incompleta e algum cinto equipado ainda não tiver uma pilha daquele ID, criar uma pilha com uma unidade no primeiro espaço vazio desse cinto. A ordem de busca é o espaço geral 1 e depois 2, e a ordem das posições dentro de cada modelo. Isso permite uma pilha igual independente no segundo cinto quando a do primeiro já chegou a quatro.
3. Se todo cinto equipado já tiver uma pilha daquele ID cheia, ou se não houver espaço vazio para uma nova pilha, encaminhar o item para a bolsa normal.
4. Se a bolsa normal também não tiver espaço, recusar a aquisição sem remover o item do chão, baú ou outra origem.

Sem cinto equipado, itens elegíveis seguem o roteamento normal para a bolsa.

## 5. Movimentação manual

As operações de arrastar e soltar são validadas pelo servidor e aplicadas como transações, para impedir perda ou duplicação de itens.

### Bolsa normal para cinto

- Arrastar para uma posição vazia transfere uma unidade e cria uma pilha, desde que aquele cinto ainda não tenha uma pilha do mesmo ID.
- Arrastar um item igual para a pilha existente acrescenta uma unidade, até o limite quatro.
- Arrastar item diferente para uma posição com exatamente uma unidade troca a unidade do cinto com a unidade da bolsa.
- Uma troca não pode criar uma segunda pilha do mesmo ID no mesmo cinto; nesse caso, a jogada é recusada e os itens permanecem nas origens.
- Se a posição de destino contiver mais de uma unidade de outro item, a operação é recusada e os itens permanecem nas origens.
- Uma pilha cheia não aceita outra unidade. O segundo cinto pode manter sua própria pilha daquele ID, conforme a regra de compartimentos independentes.

### Cinto para bolsa normal

- Cada operação transfere exatamente uma unidade.
- A quantidade da pilha do cinto diminui em um; a posição fica vazia ao chegar a zero.
- Se não houver espaço na bolsa normal, a operação é recusada sem alterar o cinto.

## 6. Usar e arremessar consumíveis

Quando equipado, cada espaço do cinto oferece os mesmos comandos de usar e arremessar que um consumível equivalente na bolsa normal. O servidor resolve o efeito pela definição autoritativa do item. Quando o fluxo atual consome o item, a quantidade no cinto diminui em um e a posição é esvaziada quando a quantidade chega a zero. Recusas que hoje não consomem o item continuam sem consumi-lo.

Quando o cinto não está equipado, seus itens não aparecem como itens utilizáveis e não podem ser usados nem arremessados. Equipar novamente restaura acesso às mesmas posições e quantidades.

## 7. Equipar e desequipar

Qualquer versão pode ser equipada em um espaço geral disponível da ficha. Dois cintos podem coexistir, inclusive uma combinação de versões, cada qual com seu próprio conteúdo e a quantidade de posições definida pelo modelo. Os efeitos de inventário pertencem ao cinto equipado; não são perdidos ao desequipar.

Ao desequipar um cinto com conteúdo, o conteúdo continua vinculado a esse objeto e fica inacessível enquanto ele estiver desequipado. O jogo envia uma mensagem localizada com o nome do modelo, por exemplo: “Os itens continuam guardados no {nome do cinto} e ficarão inacessíveis até ele ser equipado novamente.”

## 8. Transferência e persistência

Os compartimentos e suas quantidades fazem parte do dicionário do próprio item, não de uma lista global do jogador. Consequentemente:

- salvar e carregar um personagem preserva o conteúdo de cada cinto;
- largar um cinto no chão mantém o conteúdo nele;
- pegar ou receber um cinto transfere o cinto e o conteúdo como uma única peça;
- baús e outras origens de saque preservam o conteúdo pré-carregado quando o item já o possuir;
- desequipar, mover para a bolsa, transferir ou deixar cair o cinto não esvazia nem duplica seus compartimentos.

Os dados devem ser serializáveis em JSON. Itens antigos sem campo de compartimentos são tratados como cintos vazios.

O editor de masmorra deve preservar o conteúdo pré-carregado de um cinto em itens de baú e loot de decoração. Um item de loot do tipo cinto permite configurar as posições daquela versão (quatro ou duas); cada posição recebe um consumível elegível e quantidade de 1 a 4. Cintos pré-carregados continuam sendo uma única peça de loot; ao pegá-la, o jogador recebe o cinto com seus compartimentos intactos.

## 9. Interface e texto

Na janela de inventário:

- cada cinto equipado tem uma seção identificada visualmente;
- cada seção desenha dois espaços para Cinto com Bolsos ou quatro para Cinto de Utilidades, em tom marrom;
- o ícone fica visualmente menor, mantendo a área clicável padrão;
- espaços ocupados mostram o número de unidades;
- ferramentas de seleção, foco, teclado, toque, tooltip e ações continuam acessíveis.

Nomes: **Cinto de Utilidades** e **Cinto com Bolsos**.

Descrições sugeridas:

- **Cinto de Utilidades:** “Equipado, oferece quatro bolsos para consumíveis. Cada bolso guarda até quatro unidades iguais. Os itens permanecem no cinto quando ele é desequipado e ficam inacessíveis até ser equipado novamente.”
- **Cinto com Bolsos:** “Equipado, oferece dois bolsos para consumíveis. Cada bolso guarda até quatro unidades iguais. Os itens permanecem no cinto quando ele é desequipado e ficam inacessíveis até ser equipado novamente.”

## 10. Autoridade, protocolo e arquivos envolvidos

O servidor continua sendo a autoridade sobre capacidade, elegibilidade, pilhas, movimentação, coleta e consumo. O cliente envia operações referenciando o cinto e a posição, e renderiza a resposta do estado sincronizado.

Áreas previstas para implementação:

- `server.py`: dois itens/equipamentos, vendas por 80 e 30 moedas, catálogo de saque, dados dos compartimentos, roteamento de aquisição, validação de movimentação, consumo, aviso ao desequipar e persistência/loot;
- `src/gameState.js`: ações e mensagens do cliente para transferir, usar e arremessar itens dos compartimentos;
- `src/ui/inventoryModal.js`: seções dos cintos, contadores, ícones compactos e arrastar/soltar;
- `game.js` e `src/lang/*`: integração visual, aviso e textos localizados, conforme o padrão existente;
- `tools/editor.js` e catálogo/exportador do editor: configurar e preservar compartimentos pré-carregados em baús e loot de decoração;
- catálogos e testes correspondentes: registrar o item, a imagem e cobrir regras autoritativas, interface, autoria de loot e transferência.

## 11. Verificação da implementação

O plano de implementação deverá incluir verificações para:

- equipamento dos dois modelos em qualquer combinação, limites de capacidade e persistência ao desequipar;
- limite de quatro por pilha, pilhas independentes do mesmo tipo em cada cinto e até oito unidades do mesmo tipo com dois cintos;
- coleta em pilha existente, espaço vazio, cinto cheio, bolsa cheia e ausência de cinto equipado;
- arrastar itens iguais, movimentação unitária, troca com pilha de uma unidade, recusa com pilha maior e recusa por falta de espaço;
- uso e arremesso consumindo uma unidade exatamente nos casos em que o fluxo atual consome;
- salvar/carregar e pegar/largar/saquear um cinto com conteúdo;
- editar, exportar e reabrir baú ou decoração com cinto pré-carregado;
- compra no mercador pelos preços de 80 e 30 moedas;
- apresentação e interação no inventário em layouts suportados.

## 12. Fora do escopo

- alterar o limite ou a capacidade da bolsa normal;
- permitir outros grupos de itens além dos consumíveis aprovados;
- conceder bônus de combate, atributos ou efeitos diferentes do armazenamento;
- consumir todos os itens de uma pilha numa única ação;
- criar um sistema genérico de contêineres para outros equipamentos.
