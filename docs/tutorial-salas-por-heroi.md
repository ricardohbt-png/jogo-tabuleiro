# Campo de Treinamento — roteiro das seis salas

Preparado em 2026-10-01 a partir do mapa atual e dos handlers de habilidades de `server.py`.

Implementado em 2026-10-01 no mapa, servidor, cliente e editor. As regras de arquitetura continuam em `CLAUDE.md`. As seções abaixo registram o roteiro; o resumo de entrega distingue o comportamento implementado das extensões propostas.

## Resumo de entrega

- As seis salas usam `allowed_class`. Movimento, abertura, voo, teleporte e servos respeitam a classe. O editor preserva a configuração.
- Lições iniciais e variantes das habilidades mapeadas na Guilda; magias conhecidas com círculo utilizável recebem exercícios adicionais. Metamagias incompatíveis são puladas. Combinações de técnicas e cenários específicos para cada magia permanecem extensões do roteiro.
- Lewis tem dois aliados de treinamento, Henrique tem um. São alvos de habilidades, não jogadores ou membros da campanha.
- Richard liberta o refém, ativa Protetor, encerra sua vez para receber o golpe controlado de 8 de dano e cura o mesmo refém. A cura antecipada ou em outro alvo não conclui o exercício.
- Bonecos privados se recompõem sem recompensa. A armadilha de desarme pode ser restaurada; veneno emprestado e servo de treino são retirados na saída.
- `tutorial_history` guarda lições concluídas na ficha; a foto da masmorra preserva os exercícios em andamento e os NPCs. O botão de repetição aparece ao terminar as lições da sala.
- Fotos anteriores à atualização conservam o mapa antigo da execução. Para receber as salas novas, iniciar uma nova execução do Campo de Treinamento.

Verificação: `tools/test_tutorial_salas.py` cobre os fluxos reais e as restrições; `test_tutorial_cliente.js`, `test_dungeon_loader.py`, `test_savegames.py` e `test_salvar_masmorra.py` cobrem os contratos compartilhados. O antigo `test_tutorial.py` contém IDs e conteúdo do mapa anterior e já falhava com o mapa reorganizado antes desta implementação.

## Decisão do jogador

Ensinar as habilidades disponíveis no nível inicial. Acrescentar exercícios quando o herói aprender magias, técnicas ou especializações, sem conceder poderes temporários. A liberação deve consultar a habilidade realmente disponível na ficha: nível sozinho não representa compras da Guilda nem magias conhecidas.

## Aproveitamento do mapa atual

Preservar as seis salas desenhadas pelo autor, os corredores e as salas comuns.

| Herói | Sala | Retângulo atual (x, y, largura, altura) | Porta | Nome proposto |
|---|---|---|---|---|
| Guerreiro Anão | 40 | 19, 1, 6, 6 | 22, 7 | Pátio de Armas |
| Pedro | 41 | 21, 22, 6, 6 | 22, 21 | Laboratório Arcano |
| Luccas | 42 | 8, 5, 6, 6 | 14, 7 | Câmara das Sombras |
| Lewis | 35 | 31, 4, 7, 5 | 30, 6 | Santuário de Cura |
| Henrique | 43 | 9, 21, 6, 6 | 15, 23 | Salão da Música |
| Richard | 38 | 32, 23, 7, 5 | 31, 25 | Câmara do Juramento |

As lições existentes já indicam essa distribuição. Corrigir os `room_id` de `boneco_mira`, `boneco_golpe` e `boneco_furia`: suas posições estão na sala 40, mas os três apontam para 20. Isso interfere em dormência, abertura da sala e objetivos.

## Entrada exclusiva

Adicionar uma opção **Herói permitido** no painel da sala do editor: Todos ou uma das seis classes. Persistir uma propriedade opcional `allowed_class` da sala; ausência significa entrada livre.

```json
{"id": 40, "allowed_class": "warrior"}
```

O servidor deve recusar a entrada do herói incompatível no retângulo da sala e na sua porta de acesso. A restrição continua valendo após a porta ser aberta e deve cobrir movimento comum, caminhos, voo e teleporte. O cliente usa a mesma restrição no cálculo do caminho para evitar que o peão tente atravessar a sala alheia.

Mostrar o nome do dono na entrada e, ao tentar entrar com outro herói, a mensagem: **“Esta sala é destinada a Pedro. Procure a sala do seu herói.”** O nome deve vir da classe configurada, sem ficar fixo no código. O herói permitido pode entrar e sair a qualquer momento; conclusão do tutorial não prende ninguém na sala.

Servos controlados obedecem à classe do controlador. NPCs de treinamento pertencem à própria sala e permanecem nela. A restrição não interfere nos corredores nem nas salas comuns.

## Forma de cada lição

1. Explicar uma habilidade em poucas frases, incluindo onde clicar.
2. Exibir uma tarefa concreta no painel do jogador.
3. Preparar os alvos e os recursos necessários.
4. Confirmar a ação pelo handler do servidor após sua validação.
5. Mostrar a consequência e liberar a próxima tarefa.

Ativar um botão não basta quando a habilidade modifica um ataque ou uma magia: o exercício precisa registrar a utilização efetiva. Um teste que falhe pode ser repetido. Os alvos necessários não podem se esgotar antes das lições seguintes.

## Guerreiro — Pátio de Armas

Usar os três alvos já desenhados: Mira em 20,1; Golpe em 22,1; Fúria em 24,1. Eles precisam de reposição por exercício ou resistência suficiente para permitir tentativas.

| Lição | Instrução para o jogador | Conclusão |
|---|---|---|
| Mira Certeira | “Selecione Mira Certeira e ataque o alvo ⚔️. Observe o bônus no teste de acerto. Armar a habilidade prepara o golpe; ela só será usada quando você atacar.” | Ataque validado com Mira Certeira aplicada; não concluir apenas ao armar. |
| Golpe Devastador | “No seu próximo turno, arme Golpe Devastador e ataque o alvo 💥. Compare os dados de dano com o golpe comum.” | Golpe com o modificador aplicado. |
| Fúria Berserker | “Arme Fúria Berserker e ataque o alvo 🔥. Depois faça o ataque extra antes de encerrar o turno.” | Registrar o primeiro ataque com Fúria e o ataque adicional daquele turno. |
| Recursos e encerramento | “Confira os custos de comida e água. No começo você arma uma habilidade por turno. Termine sua vez e confira o que foi renovado.” | Encerrar turno após os exercícios. |

Novas lições: combinação de duas ou três habilidades quando a especialização permitir; variantes de Mira, Golpe e Fúria quando adquiridas. As explicações e os resultados devem usar os valores calculados pelo motor.

## Pedro — Laboratório Arcano

Colocar um alvo de dano, dois alvos alinhados e um alvo com teste de resistência. Disponibilizar um cadáver apropriado para treinar Reviver os Mortos e um ponto de comando do servo. Alvos e cadáver são exclusivos do treinamento.

| Lição | Instrução para o jogador | Conclusão |
|---|---|---|
| Grimório e círculos | “Abra o Grimório e escolha uma magia que você conhece e pode lançar. Selecione o alvo indicado. Confira o círculo e o slot gasto.” | Magia conhecida lançada com sucesso no exercício adequado ao seu tipo. |
| Renovação | “Encerre o turno e observe a renovação dos slots disponíveis.” | Novo turno iniciado e slots atualizados. |
| Aprimorar Magia | “Arme Aprimorar Magia e lance uma magia que exija teste de resistência. Observe a dificuldade do teste.” | Metamagia realmente aplicada a uma magia compatível. |
| Estender Magia | “Arme Estender Magia e lance uma magia com duração. Observe por quantos turnos o efeito permanece.” | Metamagia aplicada a efeito com duração. |
| Fortalecer Magia | “Arme Fortalecer Magia e lance uma magia de dano. Compare os dados com o lançamento comum.” | Metamagia aplicada ao dano. |
| Reviver e comandar | “Anime o cadáver de treinamento. Encerre a ação do herói e use a fase do servo para movê-lo e atacar o alvo.” | Animação bem-sucedida, movimento e ataque do servo. |

Exibir somente exercícios compatíveis com as magias conhecidas e os slots atuais. Se Pedro não conhece magia de dano, duração ou resistência, a metamagia correspondente fica indicada como exercício futuro e não bloqueia o curso inicial. Nunca pedir uma magia específica que o jogador não aprendeu.

Novas lições: magias recém-aprendidas, novos círculos utilizáveis, combinação de metamagias e evolução de Reviver os Mortos. O guia atual da sala não pode ensinar um multiplicador fixo de Fortalecer Magia: o helper `_fortalecer_mult` calcula o valor da ficha e sua base atual é 1,25.

## Luccas — Câmara das Sombras

Criar uma faixa de armadilhas controladas, um alvo de baixa percepção e um baú de provisões contendo veneno e recursos suficientes para fabricar a armadilha disponível. O veneno do exercício deve ser utilizável pela regra real da habilidade.

| Lição | Instrução para o jogador | Conclusão |
|---|---|---|
| Detectar Armadilhas | “Ative Detectar Armadilhas e aproxime-se da faixa marcada. Observe as armadilhas reveladas e o custo de manutenção.” | Detecção ativa e revelação de uma armadilha de treinamento. |
| Desarmar | “Pare ao lado da armadilha revelada e use Desarmar Armadilha. Se falhar, recupere-se e tente novamente.” | Desarme bem-sucedido. |
| Esconder nas Sombras | “Aproxime-se do boneco e use Esconder nas Sombras. Ainda pode usar sua ação principal depois da ação bônus.” | Ocultação bem-sucedida. |
| Ataque Furtivo | “Enquanto estiver escondido, ataque o boneco. O Ataque Furtivo é uma consequência da situação, não um botão para armar.” | Ataque com dano furtivo registrado. |
| Veneno Rápido | “Pegue o veneno do baú, use Veneno Rápido e ataque com a arma untada.” | Aplicação na arma e golpe que utilize o veneno; explicar a resistência do alvo sem exigir que ele falhe no teste. |
| Criar Armadilha | “Selecione uma armadilha que você já pode construir e uma casa válida. Faça o alvo móvel passar por ela.” | Colocação validada e disparo do mecanismo criado. |

Novas lições: armadilhas, venenos e especializações realmente adquiridos. Não remover da sala um mecanismo que uma lição posterior ainda necessita; restaurar os componentes após cada exercício.

## Lewis — Santuário de Cura

Preparar dois **aliados de treinamento**: um ferido e outro que pode receber um status controlado e uma condição de morte simulada. Precisam funcionar em solo; outros jogadores não devem entrar para servir de alvo.

| Lição | Instrução para o jogador | Conclusão |
|---|---|---|
| Cura | “Selecione o aliado ferido e use Cura com um dado. Observe a vida recuperada e o custo de água.” | Cura validada que restaure vida. |
| Cura em Área | “Fique próximo dos dois aliados feridos e use Cura em Área. Confira quais alvos estão dentro do raio.” | Cura aplicada a ambos os aliados do exercício. |
| Purificação | “Selecione o aliado com o efeito indicado e use o tipo correspondente de Purificação.” | Remoção real do efeito pelo handler. |
| Ressurreição | “Aproxime-se do aliado caído e use Ressurreição. Confira a vida com que ele retorna.” | Aliado do exercício revivido. |
| Magias conhecidas | “Abra seu Grimório e pratique uma magia disponível no alvo indicado.” | Lançamento validado, quando a ficha tiver uma magia utilizável. |

Os NPCs devem receber os mesmos testes de alcance e os efeitos das habilidades, mas não ocupar vagas de classe, participar da fila de jogadores, conceder recompensas ou ser salvos como membros da campanha. Não reutilizar automaticamente `test_hero`: o recurso atual foi feito para controle do Mestre e possui contratos diferentes.

Novas lições: evolução das curas, novos tipos de purificação habilitados, variantes de ressurreição e magias aprendidas. Simular somente efeitos que o Lewis atual consegue remover.

## Henrique — Salão da Música

Preparar um aliado de treino, um alvo inimigo e o instrumento já disponível na ficha. A sala precisa permitir observar o aliado dentro e fora do alcance musical.

| Lição | Instrução para o jogador | Conclusão |
|---|---|---|
| Canção Heroica | “Ative a Canção Heroica e escolha um benefício disponível. Confira o efeito em você e no aliado próximo.” | Canção ativa com o benefício aplicado. |
| Alcance e manutenção | “Observe o aliado fora do alcance, depois volte para perto dele. Encerre uma rodada e confira o consumo de comida e água.” | Demonstração da saída e retorno ao raio e uma manutenção processada. |
| Encerrar a canção | “Desative a canção quando terminar. Confira que o efeito e a manutenção cessaram.” | Desativação validada. |
| Provocação | “Selecione o alvo e use Provocação. Observe o resultado do teste e o efeito sobre o inimigo.” | Uso validado; não travar o jogador se o inimigo resistir. |
| Instrumento | “Use o instrumento equipado no exercício indicado e observe sua ação e seu efeito.” | Uso efetivo do instrumento disponível. |

Novas lições: benefícios musicais, instrumentos, técnicas e canções recém-adquiridos. Cada exercício usa o instrumento possuído; não exigir compra para concluir o treinamento inicial.

## Richard — Câmara do Juramento

Preparar um refém e um atacante de treinamento com dano controlado. Richard primeiro liberta o refém, usa Protetor nele, observa o dano compartilhado e depois usa Imposição das Mãos no mesmo aliado. Manter espaço para os dois ficarem adjacentes.

O prisioneiro existente já é aceito por `handle_protetor` e `handle_imposicao_maos`, desde que esteja vivo e liberto. Reutilizar esse contrato para o refém de Richard; a implementação atual comporta um prisioneiro por masmorra, portanto os aliados de treino de Lewis continuam sendo NPCs próprios. O refém permanece na sala durante o exercício.

| Lição | Instrução para o jogador | Conclusão |
|---|---|---|
| Libertar o refém | “Aproxime-se do refém e liberte-o. Agora ele é um aliado que você pode proteger.” | Prisioneiro liberto por Richard. |
| Protetor | “Use Protetor no refém e encerre o turno para iniciar o ataque de treinamento. Observe quanto dano cada um recebeu.” | Vínculo com o refém correto e um ataque cujo dano tenha sido repartido pelo fluxo real de Protetor, com ambos vivos. |
| Imposição das Mãos | “O refém sobreviveu, mas ficou ferido. Fique ao lado dele e use Imposição das Mãos para recuperar sua vida.” | Cura efetiva maior que zero no mesmo refém após a demonstração de Protetor. Curar Richard ou outro alvo não conclui o exercício. |
| Golpe Sagrado | “Ative o nível de Golpe Sagrado disponível e ataque o alvo. Observe o dano acrescentado.” | Ativação e ataque com o efeito aplicado. |
| Regeneração Divina | “Com vida faltando, ative Regeneração Divina e encerre o turno. Observe a vida recuperada na rodada seguinte.” | Recuperação efetiva por manutenção. |
| Guerreiro da Luz | “Ative Guerreiro da Luz e compare seus atributos antes e depois. Desative ao terminar.” | Ativação e encerramento validados. |

O atacante só começa depois que Protetor estiver vinculado ao refém, realiza a demonstração e pausa enquanto Richard aprende a cura. Calibrar o dano máximo, incluindo crítico e arredondamentos, para deixar o refém ferido e vivo após a divisão, sem risco de matar Richard. Mostrar na conclusão os valores reais: dano recebido pelo refém, parcela recebida por Richard e redução aplicada. O resgate não pode disparar encerramento da missão nem recompensa durante essa sequência. Restaurar o exercício quando necessário sem duplicar o prisioneiro nem modificar a campanha.

Novas lições: níveis efetivamente adquiridos de cada habilidade, combinação de efeitos sustentados e custos de manutenção. Não aplicar dano letal só para demonstrar proteção.

## Progresso e retorno

Salvar a conclusão por conta/personagem, identificador estável da lição e versão da variante ensinada. Não usar posição no mapa nem ID temporário de monstro como identidade do curso.

Ao voltar, mostrar as lições novas e permitir repetir exercícios concluídos. Cada lição avançada tem requisitos explícitos de nível, magia conhecida, habilidade ou compra da Guilda. Lições indisponíveis não entram no denominador do curso atual e não bloqueiam as lições disponíveis. Uma ordem linear com uma lição bloqueada no meio não basta para essa progressão.

Cada herói encerra seu próprio curso. Nenhum jogador fica aguardando uma classe ausente. O objetivo atual `all_heroes_at_exit` continua exigindo reunir os participantes para encerrar a masmorra; não confundir essa saída do grupo com a conclusão individual das salas.

## Pontos a resolver na implementação

- O motor atual já tem fala dirigida por classe, ordem, tarefa e progresso. Aproveitar esses contratos e acrescentar requisitos e sequências de ações.
- Implementar e persistir a restrição de sala no servidor, cliente e editor, incluindo copiar/colar e mover regiões.
- Criar os aliados de treinamento e integrar seleção, cura, proteção, status e morte simulada em 2D/3D.
- Acrescentar eventos que faltam: detecção, purificação, ressurreição, Protetor, cancelamentos e efeitos reais de manutenção.
- Preparar e restaurar cenários por jogador/etapa; reservar os alvos ao dono da sala para ataques à distância de colegas não consumirem o exercício.
- Garantir recursos suficientes e um meio explícito de restaurar o exercício sem ganhar ouro, XP ou itens exportáveis.
- Corrigir os alvos do Guerreiro associados à sala errada e preencher as demais salas antes de colocar portões de conclusão.

## Critérios de aceitação

- Cada uma das seis classes entra na própria sala e é impedida de entrar nas outras cinco, com portas fechadas e abertas.
- Caminhos, voo, teleporte e servos respeitam a exclusividade; sair da própria sala continua possível.
- As seis trilhas podem ser concluídas em solo com uma ficha inicial real.
- Multiplayer mantém tarefas independentes; um colega não conclui nem destrói o exercício do outro.
- Ação inválida, cancelada ou incompatível não conclui a tarefa. Falhas de dado permitem nova tentativa.
- Escolhas diferentes de magias iniciais não criam tarefas impossíveis.
- Salvar e retomar preserva o progresso; voltar depois de desbloquear uma habilidade apresenta a lição nova.
- NPCs, cadáveres, provisões e alvos do treinamento não se tornam membros nem recompensas da campanha.
- O editor conserva todos os campos novos após carregar, salvar, copiar e mover uma sala.
