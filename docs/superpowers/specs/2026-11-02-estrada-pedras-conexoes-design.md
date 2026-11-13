# Estrada de pedras conectável — desenho

## Intenção

Ao pintar `caminho_pedras_terra` com a ferramenta **Chão**, os trechos devem se
ligar automaticamente como estradas de SimCity. O autor desenha o trajeto; o
editor cuida das juntas e curvas.

## Abordagens consideradas

- **Variantes por conexão (escolhida):** classificar as quatro ligações
  ortogonais de cada tile e mostrar a variante visual correspondente. Dá curvas
  e entroncamentos previsíveis e permite que a prévia do editor e o jogo usem
  as mesmas imagens.
- **Desenho procedural:** compor os braços da estrada em tempo de renderização
  a partir da textura atual. Reduz arquivos, mas amplia a lógica visual em 2D e
  3D e torna mais difícil manter as duas prévias idênticas.

## Regras

- Dois tiles conectam quando são ortogonalmente adjacentes e ambos têm a
  decoração `caminho_pedras_terra`; diagonais não conectam.
- Cada tile escolhe uma variante para isolado, ponta, reta, curva, T ou
  cruzamento. As rotações da mesma forma cobrem as direções.
- Pintar ou apagar um caminho recalcula o tile afetado e os vizinhos imediatos.
- A ferramenta segue a interação de estradas do SimCity 2013: clicar define o
  início, arrastar mostra uma prévia e soltar constrói. Esc/botão direito cancela.
  Na grade, o eixo dominante entre início e cursor define um trecho horizontal
  ou vertical. Mover o cursor ajusta o segmento inteiro sem deixar sobras; todas
  as casas são preenchidas só na confirmação. Outro segmento pode seguir outro
  eixo; os segmentos se conectam e formam a curva automaticamente.
- A topologia é derivada das peças presentes, não de uma imagem gravada
  permanentemente; reabrir um mapa mantém as conexões corretas.
- A estrada continua como camada de piso caminhável, assentada sobre o material
  `terra`, podendo passar sob objetos.

## Fora de escopo

- Conexão diagonal, estradas de largura variável ou regras de tráfego.
- Alterar o material de piso global para simular a estrada.
