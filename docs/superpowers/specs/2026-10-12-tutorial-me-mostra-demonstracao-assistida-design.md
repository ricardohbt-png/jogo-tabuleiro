# Tutorial “Me mostra” — demonstração assistida

Data: 2026-10-12. Estado: especificação proposta, aguardando revisão do usuário.

## Objetivo

Fazer o botão **Me mostra** conduzir o jogador pelo passo atual de forma visível:
preparar interfaces seguras, apontar o controle ou alvo relevante e parar antes
de uma ação que altere a partida. O jogador confirma essa ação usando a mesma
interface que usaria sem a demonstração.

O recurso atende jogadores que não sabem onde começar, mantendo o tutorial como
prática real. O sucesso significa que o botão produz uma demonstração perceptível,
que o jogador entende qual ação deve fazer e que nenhuma ação de jogo ocorre antes
da confirmação explícita.

## Diagnóstico atual

O cliente mostra **Me mostra** para passos que declaram `ui`. `_guiaMostrar()` em
`game.js` reinicia o relógio das dicas e chama `_guiaTick()`, que reaplica o halo,
a seta e a dica conforme o tempo. O passo já recebe esses destaques ao abrir;
portanto o botão raramente produz uma mudança visível.

O guia existente é orientativo. `ui` descreve um alvo, enquanto o servidor só
avança `licao_passo` quando recebe o evento descrito em `conclui_com` ou uma ação
informativa autorizada por **Entendi**. Esse contrato deve continuar valendo.

## Decisões

- **Demonstração assistida, não piloto automático:** executar apenas preparações
  seguras de interface e apresentação visual. Parar antes de movimento, ataque,
  magia, uso de item, gasto de recurso, encerramento de turno ou qualquer ação
  equivalente.
- **Ação real continua manual:** o jogador confirma pela interface normal. Só o
  evento validado pelo servidor pode cumprir `conclui_com` e avançar a lição.
- **Script declarativo e limitado:** os passos podem ter uma sequência opcional
  de operações de demonstração de uma lista permitida; não aceitam JavaScript,
  seletores arbitrários nem chamadas livres a handlers de ação.
- **Sem estado de jogo paralelo:** não criar personagem fantasma ou simulação
  duplicada. A demonstração usa a interface e o estado visíveis da partida.
- **Disponibilidade gradual:** passos sem roteiro específico ainda oferecem uma
  animação curta de foco no `ui` atual e explicam que a próxima ação cabe ao
  jogador. O conteúdo pode ganhar roteiros mais ricos por fatias.

## Alternativas avaliadas

1. **Roteiro declarativo no passo — escolhido.** Reutiliza o modelo do guia,
   admite operações explícitas e seguras e mantém progresso autoritativo no
   servidor. Custa validar novos tipos de operação, mas limita o risco e é
   extensível às lições comuns e às seis classes.
2. **Autoplay acionando as APIs reais do jogo.** Poderia concluir passos sem
   interação, mas um botão de ajuda passaria a mover, atacar, consumir itens ou
   encerrar turnos em nome do jogador. Também acoplaria a demonstração aos
   detalhes internos de cada ação. Não será adotado.
3. **Replay simulado fora da partida.** Evitaria efeitos colaterais, mas
   duplicaria tabuleiro, HUD e regras de interação; o jogador ainda precisaria
   aprender a interface real depois. Não será adotado.

## Experiência do jogador

1. O jogador aciona **Me mostra** no passo atual.
2. A janela anuncia que a demonstração começou; uma animação de foco conduz o
   olhar pelo alvo atual. Quando o roteiro inclui uma preparação segura, ela
   acontece pela interface real, como abrir um menu ou inventário.
3. Para passos com alvo, o cliente destaca uma escolha válida e pode exibi-la
   como prévia. A prévia não envia mensagem de ação ao servidor. Se a interface
   existente não suportar seleção pendente sem confirmar a ação, o cliente usa
   apenas halo/seta e deixa o clique no alvo como confirmação explícita.
4. A demonstração pausa na fronteira de ação e diz claramente o que o jogador
   precisa fazer. Não dispara clique sintético no alvo nem invoca o handler de
   movimento, ataque, magia, item ou turno.
5. O jogador executa a ação pelos controles existentes. O evento normal chega
   ao servidor e o fluxo atual avança ou conclui a lição.
6. O jogador pode cancelar a demonstração a qualquer momento; isso não cancela
   uma ação já confirmada nem altera o progresso do guia.

Repetir **Me mostra** recomeça apenas a demonstração do passo atual. Não muda o
passo, recompensa, histórico ou estado do combate.

## Modelo de dados

Adicionar campo opcional `demonstracao` a cada passo do `guia`. Ele será uma lista
curta de operações de um vocabulário validado pelo servidor. Exemplos conceituais:

```json
{
  "id": "abrir_bolsa",
  "texto": "Abra sua bolsa para localizar a poção.",
  "ui": "botao:inventario",
  "demonstracao": [
    {"acao": "focar", "alvo": "botao:inventario"},
    {"acao": "abrir_interface", "alvo": "inventario"},
    {"acao": "focar", "alvo": "bolsa:pocao_cura"}
  ],
  "conclui_com": {"tipo": "usar_item", "alvo": "pocao_cura"}
}
```

O exemplo define apenas a forma dos dados, não é uma lição já escolhida para
alteração. A lista permitida inicial deve conter somente ações de apresentação
e abertura de interface comprovadamente sem custo de jogo. `focar` aceita apenas
alvos válidos no vocabulário `GUIA_UI_RE`; `abrir_interface` aceita uma lista
fechada de painéis do jogador. Nenhuma operação do esquema pode representar
“confirmar ação”.

O payload do passo (`_guia_payload`) entrega `demonstracao` ao cliente. O validador
do servidor rejeita listas longas, operações desconhecidas, alvos inválidos,
interfaces fora da lista permitida e qualquer campo com conteúdo executável.
Passos antigos, modelos de lição gerados e guias sem o campo continuam válidos.

## Arquitetura e fluxo

```text
fonte do guia (tools/tutorial_guia_*.py / autoria comum)
       ↓ gera guia no JSON
validador e _guia_payload (server.py)
       ↓ passo atual em fala/licao_passo
controlador da demonstração (cliente)
       ├─ operações seguras permitidas → UI real / foco visual
       └─ fronteira de ação → aguarda input normal do jogador
                                      ↓ evento real
                         validação/progresso atual do servidor
```

- O cliente recebe o campo junto ao passo existente; não é necessário criar um
  novo evento WebSocket para cada animação. `gameState.js` continua encaminhando
  o payload sem renderização ou lógica de tutorial.
- `game.js` controla a sessão visual: início, execução por etapas, pausa na
  confirmação, cancelamento e encerramento quando o passo ou a lição muda.
- `src/guiaTutorial.js` pode validar/normalizar a descrição pura das operações;
  não acessa DOM, canvas ou Three.js.
- As operações são interpretadas por uma tabela explícita no renderer. Para
  abrir menus, são chamadas somente as funções públicas de abertura já usadas
  por mouse, teclado ou controle; handlers de ações de jogo ficam fora dessa
  tabela.
- A autoria permanece nas fontes `tools/tutorial_guia_comum.py` e
  `tools/tutorial_guia_<classe>.py`; geradores e `configurar_tutorial_salas.py`
  atualizam JSON e textos derivados. Arquivos gerados não são editados à mão.
- Não alterar a tarefa, os requisitos, as recompensas, `tutorial_history`, os
  eventos `conclui_com` nem o isolamento existente por herói.

## Estado, cancelamento e falhas

- A sessão é local ao cliente e identificada por lição, passo e herói atual.
- Ao receber outro passo/lição, trocar o herói em foco, sair do tutorial ou
  fechar explicitamente a demonstração, interromper timers, cursor e foco
  temporário. Não enviar ações compensatórias ao servidor.
- Se um alvo sumir, ficar inválido, invisível ou fora do alcance, interromper a
  sequência antes de qualquer ação e voltar ao destaque normal com uma dica
  explicando o que falta. Nunca revelar informação escondida pela névoa.
- Se o jogador interagir durante uma etapa preparatória, pausar a sequência e
  preservar a entrada dele; não repetir automaticamente a operação. Se ele
  realizar a ação correta, o evento normal pode avançar o passo.
- Um erro de elemento/UI indisponível deve cair no halo e nas dicas atuais, sem
  travar a janela nem impedir o tutorial de continuar.

## Controles e multiplayer

- O botão **Me mostra**, cancelar e a confirmação da ação devem continuar
  acessíveis por mouse, teclado e gamepad.
- Foco de teclado/controle acompanha o mesmo alvo da demonstração; animação de
  cursor não é a única indicação.
- A demonstração é privada ao herói que recebeu aquela lição, como a janela e
  as dicas atuais. Ela não dá foco nem executa comandos em nome de outro jogador.
- Ação continua sujeita ao turno e às regras autoritativas existentes. O roteiro
  nunca contorna permissões nem antecipa um passo do servidor.

## Fatias de implementação propostas

1. **Motor seguro:** esquema opcional, validação no servidor, inclusão no payload
   e controlador cliente com foco animado, cancelamento e fallback. Nenhuma
   operação de jogo automática.
2. **Preparação de interface:** incluir apenas aberturas de painéis seguras e
   roteiro em poucas lições representativas, incluindo uma da trilha comum e uma
   de classe.
3. **Alvos e expansão:** adicionar prévias apenas onde o seletor existente
   permitir cancelar antes de enviar a ação; ampliar os roteiros por família de
   tarefa depois de validar o fluxo no jogo.

Cada fatia é validada antes de ampliar o conteúdo. A lista de operações não deve
ser expandida com ações reais durante este trabalho sem nova revisão de design.

## Critérios de aceitação

- Clicar em **Me mostra** produz uma sequência visível distinta do halo estático
  e identifica explicitamente a ação que o jogador deve confirmar.
- Repetir e cancelar a demonstração não consome ação, turno, PV, slots, fome,
  sede, item, ouro ou recompensa, nem altera posição/combate.
- Abrir uma interface permitida não fecha ou substitui indevidamente a lição e
  funciona por mouse, teclado e gamepad.
- Uma prévia de alvo nunca envia ataque, magia, uso de item ou movimento. O clique
  ou comando confirmador do jogador é o único que inicia a ação real.
- Somente eventos reais aceitos pelo servidor avançam `conclui_com`; passos
  informativos ainda avançam pelo fluxo atual de **Entendi**.
- Uma lição sem `demonstracao` segue funcionando e usa a apresentação visual de
  reserva.
- Dois heróis mantêm sessões de demonstração isoladas; reconexão ou troca de
  lição encerra a sequência antiga sem alterar o progresso salvo.

## Validação prevista

- Testes unitários do esquema e das operações permitidas: ações desconhecidas,
  alvos malformados e listas excessivas devem ser rejeitados.
- Testes cliente de estados da sequência: início, repetição, cancelamento,
  pausa, alvo desaparecido, troca de passo, fallback e confirmação manual.
- Regressões do guia atual: `tools/test_tutorial_guia.py`,
  `tools/test_guia_tutorial_cliente.js`, validação de conteúdo e testes das salas
  de classe afetadas.
- Teste manual no jogo em 2D e 3D, mouse e gamepad: observar que nada muda no
  tabuleiro nem nos recursos antes da confirmação; depois confirmar a ação e
  verificar o avanço autoritativo.

## Fora de escopo

- Autoplay de movimento, ataque, magia, uso de item, encerramento de turno ou
  qualquer ação que mude a partida.
- Gravação/reprodução integral de uma partida, ator fantasma, arena simulada ou
  segunda cópia do estado do jogo.
- Alterar a regra de conclusão das lições ou conceder progresso/recompensas por
  assistir à demonstração.
- Reescrever os textos de todas as lições antes de validar o motor e as primeiras
  demonstrações representativas.
