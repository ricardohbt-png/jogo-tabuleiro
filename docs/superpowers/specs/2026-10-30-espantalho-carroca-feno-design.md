# Espantalho e carroça carregada de feno

## Intenção

Adicionar duas decorações rurais ao tabuleiro: um espantalho e uma variante da carroça existente carregada de feno. A carroça deve reagir ao fogo em estágios para contar visualmente sua queima durante cinco rodadas.

## Abordagens consideradas

1. **Nova decoração composta `carroca_feno` com estados próprios de queima (escolhida).** Reutiliza a miniatura atual da carroça como base, acrescenta fardos como carga e permite trocar o estado visual e consumir o conjunto como uma peça só.
2. **Sobrepor `carroca` e `monte_feno`.** Reaproveita os dois tipos, mas conflita com footprints sólidos e não controla bem a transição para a carroça inteira em chamas.

## Regras e conteúdo

- `espantalho`: peça 1×1, alta, sólida, girável e sem interação ou efeito de combate; PNG transparente, GLB e fonte Blender.
- `carroca_feno`: nova decoração 2×2, alta, sólida e girável; conserva a silhueta/material da miniatura existente `assets/objetos/carroca.glb` e adiciona fardos de feno como carga. Criar PNG transparente, GLB e fonte Blender.
- O contato de qualquer fonte de fogo com qualquer casa do footprint inicia a queima. A rodada em que o fogo acerta conta como rodada 1:
  - Rodadas 1 e 2: as chamas ficam visualmente nos fardos.
  - Rodadas 3 e 4: as chamas cobrem a carga e a carroça inteira.
  - Início da rodada 5: a carroça é consumida e resta a marca de fuligem no chão, seguindo o efeito de fuligem existente.
- Enquanto queima, a carroça conserva o bloqueio de passagem e a área de fogo usa o dano de contato de 1d4 já empregado pelo feno. O fogo não se espalha para além do footprint 2×2.
- A queima é estado autoritativo do servidor e deve sobreviver à sincronização/salvamento da sala. Os estágios visuais precisam aparecer em 2D e 3D.

## Integração

Registrar os dois tipos no catálogo autoritativo de decorações e exportá-los para o editor. Mapear os PNGs e GLBs no cliente. A reação ao fogo deve avançar os estágios por rodada, encerrar a decoração na rodada 5 e emitir a fuligem já reconhecida pelo cliente. Adicionar textos de catálogo/localização conforme o padrão atual.

## Fora de escopo

Não mudar o comportamento do `monte_feno` existente, não fazer o espantalho ganhar vida ou disparar armadilhas e não espalhar as chamas para objetos ou casas vizinhas.

## Decisões deixadas à implementação

- Usar variantes visuais estáticas de cada estágio ou uma camada de chamas animada, desde que o relógio e a aparência descritos acima sejam preservados.
- Preservar rotação, escala de chão e leitura visual da carroça atual no editor e na partida.
