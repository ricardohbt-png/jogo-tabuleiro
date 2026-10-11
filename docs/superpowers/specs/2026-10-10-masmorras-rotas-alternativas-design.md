# Masmorras com rotas alternativas e exploração persistente

## Estado

Proposta para revisão do usuário. Nenhuma implementação está autorizada por este documento até que ele seja revisado e aprovado.

## Objetivo

Permitir que uma aventura reutilize o mesmo arquivo de masmorra em várias incursões. O grupo pode encontrar uma saída, continuar explorando sem ser retirado do mapa, retornar à cidade e voltar depois para descobrir outras rotas. A missão só fica concluída quando todas as saídas obrigatórias forem encontradas.

O autor pode combinar duas formas de progressão: uma rota liberada por condição externa e uma rota acessível, porém guardada por inimigos muito perigosos.

## Comportamento desejado

1. O grupo entra na mesma masmorra e explora um caminho.
2. Ao alcançar uma saída marcada, o servidor registra essa saída para a aventura. Encontrá-la não força o grupo a sair nem interrompe o turno ou a exploração.
3. O grupo pode seguir pelo mapa e encontrar outras saídas na mesma incursão.
4. Se retornar à cidade antes de encontrar todas as saídas, a aventura continua incompleta e o mesmo destino permite uma nova incursão na mesma masmorra. O estado de exploração deve sobreviver à troca entre cidade e masmorra, sem depender apenas da foto temporária usada para retomar uma sessão.
5. Portas ou passagens podem liberar um trecho por requisito externo. Uma rota de risco pode permanecer aberta, mas conter encontros fortes que recomendem evitá-la até o grupo estar preparado.
6. Cada rota pode definir se os monstros associados reaparecem quando o grupo retornar ou permanecem derrotados.
7. Ao encontrar todas as saídas obrigatórias, a aventura fica pronta para ser concluída. Recompensa de conclusão e encerramento de rota são concedidos uma única vez.

## Abordagens consideradas

### Recomendada: uma masmorra, várias rotas e saídas identificadas

O destino da aventura continua apontando para um único arquivo de masmorra. O arquivo define rotas, portões e marcadores de saída com IDs estáveis. A aventura referencia as saídas que contam para sua conclusão. O progresso persistido usa esses IDs, sem duplicar o mapa.

Isso mantém o mapa autoral em um lugar só e permite combinar saídas obrigatórias, caminhos opcionais, requisitos e encontros perigosos.

### Alternativas descartadas

- **Duplicar o arquivo da masmorra por caminho:** facilita isolar mapas, mas duplica manutenção e dificulta compartilhar o progresso das saídas.
- **Criar um destino separado por caminho:** reaproveita os destinos existentes, mas divide uma única missão em destinos independentes e não expressa bem a conclusão conjunta.

## Experiência no editor

### Editor de masmorras

- Adicionar uma ferramenta de **saída de rota**, separada da escada de entrada/retorno atual e dos objetivos existentes.
- Cada saída tem ID estável, nome visível e posição. A chegada de um herói à casa da saída registra a descoberta para o grupo.
- Adicionar rotas nomeadas, como “Ala fácil”, “Passagem secreta” e “Galeria dos mortos”.
- Associar monstros a uma rota. Criaturas sem rota atribuída pertencem à área comum e seguem uma política padrão configurada para a masmorra.
- Adicionar condições a portões/passagens que levam a uma rota. Os tipos iniciais propostos são: sempre aberta, fato narrativo, item, aventura concluída e local externo visitado.
- Uma rota sem condição pode continuar fisicamente acessível e ser protegida apenas por encontros perigosos; o editor não deve transformar automaticamente perigo em bloqueio.
- Definir por rota a política de monstros na revisita: **reaparecem** ou **continuam derrotados**.

### Editor do mapa-múndi

- Uma etapa de aventura pode ativar o modo **exploração por saídas**, mantendo referência ao arquivo único da masmorra.
- Listar as saídas existentes no arquivo selecionado e permitir escolher quais são obrigatórias para concluir a aventura.
- Mostrar claramente se o destino permite retorno enquanto incompleto e se exige todas as saídas ou apenas um conjunto selecionado.
- Manter a configuração linear atual como padrão para aventuras existentes.

## Dados e autoridade

- O servidor continua autoritativo para descoberta de saída, condição de portão, derrota de monstros, conclusão e recompensa.
- A definição da masmorra armazena IDs estáveis para rotas, saídas e vínculos entre monstros e rotas. As posições permanecem no arquivo da masmorra.
- A etapa da aventura armazena o modo de conclusão e os IDs de saídas obrigatórias. A missão não depende da ordem em que as saídas forem encontradas.
- O save da aventura registra saídas descobertas, rotas visitadas, estado dos monstros por rota e se a recompensa final já foi concedida.
- O progresso das rotas é compartilhado pelo grupo, seguindo o escopo atual de `world_adventure_progress`.
- Saves e aventuras existentes no formato de índice linear continuam sendo lidos sem migração manual. A nova estrutura só é usada quando o modo por saídas é explicitamente ativado.

## Regras de conclusão e retorno

- Descobrir saída significa alcançar seu marcador dentro da masmorra; a descoberta é persistida imediatamente.
- Descobrir uma saída não equivale a usá-la. O grupo pode continuar no mapa e procurar outras saídas.
- Retornar à cidade encerra a incursão atual, mas não a aventura incompleta. Ao iniciar outra incursão, o jogo carrega a mesma masmorra e o estado persistido.
- Uma saída passa a contar para a conclusão somente se estiver marcada como obrigatória pelo editor.
- Ao completar o conjunto obrigatório **e cumprir o objetivo principal normal da masmorra**, o jogo habilita o encerramento da missão e registra a conclusão/recompensa uma vez. Revisitar depois não concede recompensas repetidas.

## Persistência de monstros

- Cada rota escolhe entre `reaparecer` e `persistir derrotas` na próxima incursão.
- Rotas ainda não visitadas começam com os monstros autorados intactos.
- A política de uma rota não altera o estado de monstros de outras rotas.
- Monstros comuns sem rota explícita seguem a política padrão da masmorra, para que mapas antigos possam ativar o modo com pouca configuração.
- O estado de portas/passagens e demais objetos não é automaticamente redefinido pela política de monstros; sua persistência deve seguir as regras atuais ou receber configuração própria em uma etapa futura.

## Condições externas e rotas perigosas

- Fatos narrativos e conclusão de outra aventura já são conceitos presentes no sistema de requisitos do mapa-múndi e podem ser reaproveitados no avaliador de portões.
- Para oferecer “visitar local externo” diretamente no editor, será necessário persistir histórico de locais visitados; `world_location` representa a localização atual e não basta, sozinho, para comprovar uma visita anterior.
- A opção “local visitado” só libera o portão; não deve teletransportar o grupo nem abrir uma etapa diferente da aventura automaticamente.
- Encontros perigosos permanecem conteúdo normal da masmorra. O jogo pode oferecer um aviso autorado antes da rota, mas os jogadores continuam livres para entrar, recuar ou tentar passar.

## Compatibilidade e limites

- O modo linear atual, suas sequências, encadeamentos, histórias de entrada/saída e destinos revisitáveis permanecem com o comportamento atual quando o modo por saídas está desligado.
- A escada usada para sair individualmente da masmorra continua distinta das saídas de rota e dos objetivos existentes. A implementação deverá definir claramente se usar uma saída de rota retorna apenas o herói ativo ou o grupo inteiro, respeitando os contratos atuais de multiplayer.
- A descoberta da saída é compartilhada pelo grupo. Não se criam progresso ou cópias de masmorra por personagem.
- IDs removidos ou renomeados no editor precisam gerar validação explícita para referências de saída, rota, monstro e condição.

## Auditoria de compatibilidade e falhas a evitar

Esta revisão inspecionou os ciclos atuais do editor de masmorras, editor do mapa-múndi, carregamento da sala, salvamento e conclusão da missão. Os itens abaixo são requisitos de segurança para o futuro plano; nenhum produto foi alterado.

### Riscos bloqueadores

1. **O editor atual não representa o mesmo arquivo duas vezes na sequência.** `editor_world.js` remove do catálogo arquivos já usados na aventura. A rota alternativa precisa ser uma configuração explícita da etapa existente, e não uma segunda etapa duplicada. Caso contrário, o editor ou a API rejeitam/removem a associação e as saídas não compartilham progresso.
2. **A configuração nova seria apagada ao salvar.** O editor do mapa-múndi normaliza e serializa somente campos conhecidos; `_etapa_obj` e `_save_world_adventures_upload` também constroem objetos com lista permitida. Modo de conclusão e IDs de saídas obrigatórias precisam atravessar leitura, UI, serialização, validação, payload e persistência. Se algum elo faltar, o editor pode aparentar salvar enquanto a regra desaparece.
3. **O índice linear atual não pode virar objeto de progresso.** `world_adventure_progress` é convertido para inteiro, comparado com o número de etapas e exibido como índice. Preservá-lo como cursor linear evita quebrar campanhas, requisitos, destinos e saves existentes. A exploração por saída deve ter armazenamento aditivo, separado e com migração segura.
4. **A foto da masmorra não é o progresso persistente das incursões.** Ao iniciar uma aventura pelo mapa, `handle_world_adventure` chama `_apagar_foto()` e zera `dungeon_generated`; logo, um snapshot de retorno à cidade é descartado ao partir. Ele serve para retomar uma sessão suspensa, mas não pode ser a única cópia de saídas descobertas, rotas e monstros entre incursões. Esses dados precisam de estado de campanha próprio. Retorno enquanto incompleto deve preservar o progresso mesmo quando a sala for recriada.
5. **A missão pode ser liberada cedo e recompensada antes das saídas.** `_check_objectives` concede recompensas e define `mission_complete_pending` assim que o objetivo principal termina; `handle_encerrar_missao` avança a etapa e concede renome. No modo novo, o botão de conclusão, as recompensas e o avanço só podem acontecer quando o objetivo normal E todas as saídas obrigatórias estiverem concluídos. Não basta esconder o botão no cliente: a validação precisa ser autoritativa no servidor.
6. **IDs de monstros em runtime não são referências de autoria confiáveis.** `load_authored_dungeon` instancia cada criatura via `make_monster`, que gera identidade para a instância. Persistência por rota precisa de `source_id` estável no JSON do editor e na instância carregada; sem isso, uma revisita pode associar derrotas ao monstro errado ou reaparecer monstros de outra rota.
7. **Reaparecimento pode duplicar recompensa/loot.** Se um monstro morto reaparecer mas seu baú ou item derrubado continuar persistido, matá-lo novamente pode gerar recompensa duplicada. A política precisa definir junto com cada monstro o ciclo de loot/XP/objetivos: resetar o encontro também precisa resetar ou impedir duplicação de recompensas; persistir derrota precisa manter o crédito já dado.
8. **Objetivo `kill_all` pode tornar a rota impossível ou contraditória.** Masmorras antigas recebem `kill_all` como objetivo padrão. Ao ligar modo por saídas, a validação/editor precisa deixar explícito que conclusão exige objetivo principal existente E conjunto de saídas, e explicar combinações impossíveis, como saída obrigatória dentro de uma sala trancada pelo mesmo objetivo que só libera ao concluir a missão.

### Outros pontos que precisam de contrato explícito

- `secret_passages` hoje só suporta mecanismo/ilusão e decoração-chave. Trava por fato, item ou local externo exige integração na validação, ativação, sincronização, feedback e serialização do servidor; acrescentar um campo visual no editor não libera a passagem.
- `world_location` armazena onde o grupo está agora, não o histórico de lugares visitados. Para requisito “visitou local”, é necessário histórico persistido ou usar, inicialmente, um fato narrativo já existente.
- Saídas de rota devem ser uma coleção nova e distinta de `stairs_pos` (retorno individual) e `exit_pos` (objetivos atuais). Validar IDs únicos, posições caminháveis, colisão com spawn/escada/saída, referência obrigatória existente e rota/monstros sem referência órfã. Arquivos antigos sem essa coleção devem continuar carregando como antes.
- Estado de descoberta compartilhado deve ser escrito imediatamente após alcançar a saída e salvo também no save de campanha; queda de conexão/restart não pode desfazer a descoberta nem marcá-la duas vezes.
- A regra de saída individual atual não resolve se “usar saída de rota” retira um herói ou o grupo. A descoberta permanece independente dessa escolha: alcançar o marcador não pode teletransportar ninguém.
- A política de persistência cobre apenas monstros? Portas, passagens, baús, armadilhas, loot, neblina e consumíveis do mapa hoje vivem no estado/foto da sala. A primeira versão precisa declarar quais desses estados são preservados entre incursões ou redefinidos, evitando um híbrido acidental. Recomendação: preservar o mapa e resetar somente encontros configurados para reaparecer, com loot protegido contra duplicação.
- A interface do mapa-múndi deve apresentar o modo linear/exploração por saídas na própria etapa, permitir escolher saídas obrigatórias do arquivo e mostrar erros quando o arquivo muda e remove IDs escolhidos. O payload de catálogo atual lista arquivo/nome, portanto a lista de saídas exige metadados validados do arquivo selecionado.

### Correção ao desenho de retorno

O avanço da etapa linear só ocorre em `handle_encerrar_missao`. Portanto, numa aventura incompleta, o cursor já tende a continuar na mesma etapa; não é necessário criar um novo “revisitável enquanto incompleto” apenas para isso. O que falta é não apagar o progresso específico de exploração quando o grupo volta ao mapa e inicia outra incursão. O fluxo precisa testar separadamente: retomar uma sessão suspensa via snapshot e iniciar nova incursão parcial preservando saídas, portões e estados de encontro conforme a política configurada.

## Critérios de aceitação

1. Uma aventura pode apontar para uma masmorra uma única vez e exigir duas saídas em incursões distintas.
2. Alcançar uma saída registra sua descoberta sem tirar o grupo do mapa.
3. Depois de voltar à cidade com a aventura incompleta, o destino permite retornar à mesma masmorra.
4. Uma rota pode permanecer bloqueada até um requisito externo e outra pode estar aberta com inimigos muito perigosos.
5. A política de reaparecimento é independente por rota.
6. A aventura e a recompensa final só concluem uma vez quando todas as saídas obrigatórias forem descobertas.
7. Aventuras antigas no modo linear continuam válidas e mantêm o comportamento atual.
8. Um snapshot descartado ao iniciar nova incursão não apaga o progresso de saídas da aventura.
9. Completar o objetivo normal sem descobrir as saídas obrigatórias não habilita conclusão nem paga recompensa final.
10. Reaparecer monstros não duplica XP, loot, progresso de objetivo nem recompensas de missão.
11. Salvar, reabrir e editar a aventura mantém o modo e todas as referências válidas; uma referência removida mostra erro antes de publicar.

## Questões para fechar antes do plano de implementação

1. Quando alguém usar uma saída de rota para encerrar a incursão, isso deve retirar apenas o herói que a usou, como a escada atual, ou retornar o grupo inteiro à cidade?
2. A condição “local externo visitado” deve ser um requisito direto selecionável no editor ou, inicialmente, o autor pode usar um fato narrativo concedido por uma cena naquele local?
3. Ao encontrar todas as saídas, a missão deve apenas liberar o botão atual de conclusão, ou deve concluir automaticamente e iniciar o retorno?
