# Mini Aljava — desenho

## Intenção

Adicionar `mini_aljava`, equipamento de 30 moedas vendido no ferreiro. Usa `assets/itens/aljava.png` e ocupa um dos espaços `item1`/`item2`, sem ocupar a mão secundária. Equipada, permite pilhas de até 20 flechas e até 20 virotes na bolsa.

## Regras e limites

- Aplicar a capacidade a todos os tipos de flecha e virote já reconhecidos pelas aljavas, incluindo munições especiais.
- Como as demais aljavas, permitir que armas à distância usem munição compatível guardada na bolsa quando a mini aljava estiver equipada em `item1` ou `item2`.
- Equipar duas mini aljavas não acumula capacidade: o limite permanece 20 para cada família.
- Não mudar capacidades nem funcionamento das aljavas pequena e grande existentes.
- Manter validação autoritativa no servidor para juntar, mover, coletar e consumir pilhas; cliente e catálogo devem espelhar a regra existente.
- Incluir o item no estoque de munições do ferreiro e no catálogo exportado do editor.

## Abordagem

Reaproveitar `effect: "quiver"` e a lógica central de limite de pilha, reconhecendo esse efeito nos slots `off_hand`, `item1` e `item2`. A mini aljava declara capacidade 20/20; ao localizar múltiplas aljavas equipadas, usar o maior limite declarado, sem somar capacidades. Isso evita duplicar as regras de pilha e preserva a aljava atual.

## Decisões aprovadas

- Limite: 20 flechas e 20 virotes por pilha.
- Variantes especiais contam na família correspondente.
- Duas mini aljavas não acumulam capacidade.
- Preço: 30 moedas; venda no ferreiro.
