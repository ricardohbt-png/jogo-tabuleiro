# Grade de esgoto — desenho

## Objetivo

Adicionar uma decoração de escotilha que abre uma entrada vertical no piso de
uma masmorra. Fechada, a grade é uma casa de piso caminhável. Ao ativá-la, a
casa correspondente da ponte vira um buraco; qualquer herói que estiver sobre
ela cai imediatamente para o piso inferior no mesmo mapa.

## Contrato de jogo

- A grade é colocada sobre uma casa de ponte que cobre `FLOOR` e tenha piso
  inferior mais baixo.
- A interação usa o fluxo existente de mecanismo de decoração e pede a
  confirmação atual antes de abrir.
- A abertura é permanente durante a visita e persiste no save através do buraco
  da ponte e do estado da decoração.
- Qualquer personagem que esteja sobre a grade quando ela abre cai; quem entrar
  depois pelo buraco desce conforme as regras de movimento e voo do mapa.
- Personagens que entrarem depois na casa aberta também descem por ela. O
  movimento voluntário para esse buraco será explicitamente permitido e
  continuará bloqueado para quedas comuns.
- A queda termina no `FLOOR` sob a ponte, na mesma coordenada. O mapa continua
  sendo uma grade 2D; não há transferência automática para outro mapa.
- Quando aberta, a grade some e a ponte deixa de cobrir sua casa, revelando o
  piso inferior existente.

## Fora de escopo

- Refechar ou remover a grade depois da abertura.
- Construir um segundo mapa conectado ou um sistema geral de andares.
- Fazer o jogador cair ao simplesmente atravessar qualquer desnível.

## Validação de autoria

O editor e o servidor só aceitam a grade quando sua casa está sobre uma ponte,
tem `FLOOR` diretamente abaixo e a altura da ponte excede a do piso inferior.
O editor deve deixar a decoração ocupar a casa da ponte sem torná-la sólida.
