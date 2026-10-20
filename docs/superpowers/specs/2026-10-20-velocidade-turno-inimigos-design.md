# Velocidade do turno dos inimigos — desenho

Data: 2026-10-20. Estado: aguardando aprovação do autor.

## Intenção

O turno dos inimigos acontece rápido demais: o jogador não consegue ler quem
atacou, se acertou, quanto de dano causou e se houve habilidade especial. O
autor quer **controlar o ritmo** e **ver um resumo de cada ataque**, monstro
por monstro, sabendo sempre de quem é a vez.

## Objetivos

- Opção em "Configurações de jogo" (painel ⚙️) para escolher a velocidade do
  turno dos inimigos.
- Cada monstro age um de cada vez; o monstro que age fica marcado no tabuleiro.
- Depois de um monstro que **atacou ou usou habilidade**, uma faixa de resumo
  mostra: quem atacou, em quem, se acertou (com a jogada contra a CA), o dano e
  o tipo, e a habilidade especial usada, quando houver.
- Modo passo a passo (só Solo): o jogo espera o clique do jogador.

## Não objetivos / anti-objetivos

- Não alterar nenhuma regra de combate, ordem de iniciativa, IA ou dano.
- Não travar a partida: nenhum modo pode deixar o jogo esperando sem saída.
- No multiplayer não existe espera por clique (evita travar o grupo).
- Não revelar pela faixa o que a névoa esconde (ver "Visibilidade").
- Não pausar por monstro que apenas se moveu.

## Decisões do autor

1. **Quatro níveis**, na ordem:

   | Nível | Quem escolhe | Comportamento |
   |---|---|---|
   | Atual | Solo e anfitrião | Como hoje: sem pausa, sem faixa. É o padrão. |
   | Lento | Solo e anfitrião | Faixa visível por ~3 s, depois o próximo monstro. |
   | Muito lento | Solo e anfitrião | Faixa visível por ~6 s. |
   | Passo a passo | **Só Solo** (inclui Solo com grupo) | Faixa fica até o clique em "Continuar". Tempo automático opcional. |

   Os tempos de 3 s e 6 s foram sugeridos por Claude e aceitos como ponto de
   partida; devem ficar em constantes fáceis de ajustar.
2. **No multiplayer** só o anfitrião escolhe, apenas entre Atual, Lento e Muito
   lento, e a escolha vale para a sala toda. O passo a passo não aparece.
3. **Passo a passo**: a faixa fica até o clique, com um tempo automático
   **opcional** (desligado por padrão) que a fecha sozinha.
4. **Faixa fixa no alto da tela** (opção B do mockup), com o botão
   "Continuar" quando o modo exige clique, mais um **anel vermelho** no monstro
   que está agindo. Monstros que ainda vão agir ficam com contorno tracejado.
5. **Uma faixa por monstro**, resumindo tudo o que ele fez, e **só se atacou ou
   usou habilidade**. Monstro que só andou segue sem pausa e sem faixa (o anel
   vermelho aparece enquanto ele se move).
6. **Monstros fora de combate** (dormentes: sala trancada ou não avistados) são
   pulados: sem anel, sem faixa, sem espera. Monstros **em combate mas fora da
   visão do jogador** agem normalmente e entram no ritmo escolhido.

## Escolhas de Claude (marcar para revisão)

- **Padrão = Atual.** Quem não mexer em nada não percebe mudança.
- **Onde a escolha mora:** campo da sala (como `atravessar_aliados`), gravado no
  jogo salvo, enviado no `game_state`. No Solo, o jogador é o anfitrião e usa o
  mesmo controle. Mensagem nova: `set_velocidade_inimigos`.
- **Tempo automático do passo a passo:** campo da sala, em segundos, 0 =
  desligado; opções 3, 6 e 10 s.
- **Segurança contra travamento (Solo):** a espera por clique tem um teto de
  **90 s**; passado isso o jogo segue sozinho. Se o jogador se desconecta, a
  espera é encerrada na hora. Valores sugeridos, ajustáveis.
- **Visibilidade da faixa:** monstro em combate que o jogador **não vê** age
  com faixa genérica ("Um inimigo atacou Pedro: acertou, 5 de dano"), sem nome,
  tipo nem habilidade do monstro. Alvo e dano são do próprio herói, então não
  revelam nada. Se o alvo também não é do jogador, a faixa não aparece.
- **Habilidade especial** aparece pelo nome que o ataque já carrega
  (`attack_name`), sem tabela nova.

## Como funciona (alto nível)

**Servidor** (autoritativo; o cliente sozinho não consegue segurar a fila, pois
o servidor resolve o turno inteiro sem esperar):

- Em `_activate_initiative_actor`, o `monster_step` hoje roda o turno do monstro
  e chama `_advance_initiative()` direto. Entre os dois entra um passo
  "ritmo do inimigo":
  1. Antes do turno do monstro em combate: envia ao cliente a marca "monstro
     agindo agora" (id) para o anel vermelho. Dormentes não enviam nada.
  2. Durante o turno: registra os ataques do monstro numa lista temporária
     (a partir do ponto onde `attack_feedback` é emitido por
     `_emitir_feedback_ataque`, que já conhece atacante, alvo, nome do ataque e
     resultado).
  3. Depois do turno: se a lista não está vazia e o nível não é "Atual", envia
     `resumo_ataque_inimigo` (um por monstro) e espera: o tempo do nível, ou o
     clique (`continuar_turno_inimigo`) no passo a passo.
  4. Só então chama `_advance_initiative()`.
- A espera usa o mesmo cuidado da cadeia de turnos existente: dentro de
  `_isolar`, para uma falha nunca matar a iniciativa, e cancelável. Mudar o
  nível ou sair do jogo cancela a espera pendente.
- Nível "Atual": o passo 1 e 3 não fazem nada; o comportamento fica
  byte-idêntico ao de hoje (teste de regressão obrigatório).
- Mestre jogador (Modo Mestre) e janelas manuais/Comando/Dominar Mente: o
  ritmo só se aplica ao turno **automático** do monstro. Janelas controladas por
  jogador ou mestre ficam como estão.
- Fila de iniciativa descartável do simulador do editor não muda.

**Cliente** (`game.js` renderiza; `gameState.js` guarda estado):

- `gameState.js`: guarda `velocidade_inimigos`, `passo_auto_segundos`, o
  monstro agindo e o resumo atual; expõe `GS.setVelocidadeInimigos(nivel)` e
  `GS.continuarTurnoInimigo()`. Regra: um único `GS.on` por evento.
- `game.js`: renderiza a faixa fixa no alto, o anel vermelho em 2D e 3D, o
  tracejado nos que ainda vão agir, e o seletor nas configurações do jogo.
  Textos em PT/EN em `src/lang/interface.js` (`ui.turno_inimigo.*`).
- A faixa fecha no clique, na tecla de confirmação já usada nos avisos, ou pelo
  tempo. Controle/gamepad usa o botão de confirmar existente.

## Casos de borda a cobrir

- Monstro morre no próprio turno (reação) antes de a faixa sair.
- Monstro com vários ataques ou habilidade seguida de ataque: uma faixa só.
- Monstro que ataca outro monstro (hostilidade): faixa só se o jogador vê a ação.
- Ataque que mata o herói e termina a partida: a faixa não pode atrasar o fim
  de jogo; a espera é pulada.
- Troca de nível no meio de um turno: vale a partir do próximo monstro.
- Reconexão/rejoin durante a espera: o cliente recebe o estado e a espera
  continua ou expira pelo teto.
- Salvar e sair durante a espera: gravar normalmente; a espera não é salva.
- Último Esforço e janelas de reação (Bomba de Fumaça/Flash) que já pausam o
  ataque: a faixa só vem depois que a janela termina.

## Testes sugeridos

- Servidor: nível Atual idêntico ao comportamento atual; Lento/Muito lento
  esperam e depois avançam; passo a passo espera o clique e respeita o teto;
  monstro dormente pulado; monstro que só andou não gera faixa; multiplayer
  recusa passo a passo e recusa escolha de quem não é anfitrião; desconexão do
  Solo encerra a espera; falha dentro da espera não congela a iniciativa.
- Cliente (node): faixa, anel e botão; um `GS.on` por evento; textos PT/EN sem
  chave órfã (`tools/test_interface.py`, `tools/dividas.py`).
- Prova em partida real no navegador com a faixa e o anel nos quatro níveis.

## Fora de escopo

- Histórico navegável de turnos anteriores.
- Acelerar/pular a espera com tecla especial além do "Continuar".
- Alterar animações de ataque, tempo de dados ou sons.
