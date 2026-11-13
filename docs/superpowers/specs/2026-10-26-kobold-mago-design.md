# Kobold Mago — especificação

Adicionar ao bestiário um conjurador kobold ND 0,75, movimento 6, com 3 slots de magia de 1º círculo. Cada instância sorteia duas magias distintas entre Bola de Fogo, Relâmpago, Sono, Raio Congelante e Barreira Arcana.

No spawn, sortear um único item de cabeça: 10% Chapéu do Bruxo, 5% Tiara da Expansão Arcana, 1% Chapéu do Arquimago e 84% sem item. O item equipado integra o saque e seus efeitos devem funcionar para o monstro quando compatíveis.

No saque, deixar de 5 a 20 moedas e continuar participando da chance padrão de 10% de deixar alimento transportável dos kobolds. Usar o modelo GLB colorido já criado para `kobold_mago.glb`, preservando os originais do Desktop, e vinculá-lo ao tipo novo no cliente 3D. Criar uma miniatura PNG 2D transparente em `assets/pawns/monstros/kobold_mago/kobold_mago.png`, vinculada pelo mesmo identificador `image`.

Não adicionar spawn automático nem alterar os kobolds existentes.
