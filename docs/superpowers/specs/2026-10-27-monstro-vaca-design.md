# Monstro Vaca Arisca e alimentos bovinos — design

## Intenção

Adicionar uma vaca jogável como criatura de encontro, com miniatura 3D/arte 2D, comportamento defensivo e itens de alimento que podem ser comprados na taverna ou obtidos como loot. A carne e o leite também tornam a vaca uma fonte de provisões num celeiro.

## Abordagens consideradas

- **IA passiva própria + quantidade variável no formato de loot (escolhida):** `ai_type` próprio impede que a IA agressiva comum ataque uma vaca intacta. Um campo inclusivo `quantity_range` em `loot_drops` expressa as quantidades sem duplicar entradas e pode servir a outros drops no futuro.
- **Exceções na IA agressiva + entradas de loot duplicadas:** altera comportamento compartilhado de monstros e representa quantidades por várias rolagens independentes, com distribuição indireta. Foi descartada porque amplia risco de regressão e obscurece os limites pedidos.
- **Caso especial no código de morte da vaca:** satisfaz o loot sem generalizar o formato, mas vincula a mecânica ao ID do monstro. Foi descartada em favor de metadados reutilizáveis.

## Decisões aprovadas

- Nome exibido: **Vaca Arisca**; ID do monstro: `vaca`; subtipo `animal`; ND 1/4.
- Ficha proposta e aprovada na conversa: 16 PV, CA 11, movimento 6 e uma Cabeçada +3 (`1d6+1`). Sem ouro. Não aparece em encontros aleatórios (`spawn_min`/`spawn_max` iguais a 0), mas pode ser colocada em mapas pelo editor.
- A vaca não inicia ataques. Qualquer ação ofensiva de herói direcionada a ela (arma ou magia) marca a vaca como provocada, mesmo se errar; dano ambiental não provoca. Em cada turno da vaca, rola 50% para tentar fugir; no sucesso, move uma casa para longe do herói vivo mais próximo e não ataca nesse turno. Se a fuga não ocorrer, só ataca quando provocada, priorizando o último herói que a atacou; se ele não estiver disponível, usa o alvo vivo mais próximo. Se não encontrar uma casa livre para fugir, fica onde está e ainda consome o turno.
- Ao morrer, cada vaca gera uma quantidade aleatória inclusiva de 1–3 itens `carne_bovina` e 1–4 itens `leite`. Uma faixa de quantidade uniforme e inclusiva será representada por `quantity_range` em cada `loot_drops`.
- **Carne Bovina:** item consumível de bolsa, `effect: food`, +25 fome, +0 sede, preço 3 moedas, ícone `assets/itens/carne_bovina.png`.
- **Leite:** item consumível de bolsa, `effect: food`, +5 fome e +5 sede, preço 1 moeda, ícone `assets/itens/leite.png`.
- Ambos ficam à venda na Taverna e podem vir no loot da Vaca Arisca. A resolução de loot inclui itens de `SHOP_TAVERN`.
- A miniatura usa `assets/models3d/monstros/vaca.glb`; arte 2D e fallback usam `assets/pawns/monstros/vaca/vaca.png`. O projeto editável permanece `assets/models3d/monstros/vaca.blend`.

## Integração e limites

- `server.py`: ficha nativa, IA passiva, marcação de agressor, rolagens do loot variável e os dois itens em `SHOP_TAVERN`.
- `game.js`: registro do GLB pela imagem `vaca` e orientação/footprint necessários ao modelo.
- `src/lang/catalogo.js`: nomes e descrições PT/EN; regenerar o catálogo do editor pelo exportador autoritativo existente.
- `CLAUDE.md`: registrar ficha, comportamento, economia e assets.
- Não adicionar a vaca a rotas, mapas ou encontros existentes; o autor escolhe onde colocá-la.

## Chamadas de implementação

- O comportamento de fuga aproveita o movimento de afastamento já existente; uma fuga bem-sucedida não encerra o combate nem remove o monstro do mapa.
- A ordem dos drops e das fichas individuais não é relevante; cada quantidade é rolada independentemente.
- Não criar novo efeito de consumo: os itens usam o fluxo atual `effect: food`.
- A definição de ação que provoca foi tratada como chamada de implementação: armas e magias ofensivas contam; dano ambiental não conta.
- Não adicionar nem executar testes nesta tarefa, salvo pedido do usuário.
