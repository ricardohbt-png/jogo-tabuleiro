# Tutorial como primeira missão — design

Data: 2026-10-09. Estado: implementado e revisado (2026-10-09).

## Objetivo

Transformar a trilha inicial do Campo de Treinamento numa primeira missão de RPG com objetivo narrativo claro, mantendo o mapa e os exercícios úteis que já existem. O jogador deve entender o motivo de avançar pelas salas, aprender os menus essenciais — incluindo H (habilidades) e M (magias) — e concluir a missão reunindo o grupo na saída. As lições avançadas continuam disponíveis nas trilhas próprias de cada classe.

O Mestre de Armas será o professor da ilustração `assets/tela de transição/guilda_dos_herois.png`: o mesmo guerreiro, com o capelo, em retratos e cenas ilustradas no estilo cartoon da referência. A imagem de referência serve para identidade e direção de arte; seus textos e elementos de interface não serão reutilizados como conteúdo de jogo.

## Entendimento confirmado

- Preservar o Campo de Treinamento, seus espaços, portas, baús, inimigos e exercícios que ensinam regras reais.
- Manter o objetivo mecânico de reunir todos os heróis na saída; dar a ele um propósito na história da missão.
- Tornar a trilha comum uma missão inicial curta, com 6–8 objetivos práticos e claros.
- Apresentar ficha, vida, objetivos, inventário, habilidades (H) e, quando aplicável, magias (M) em contexto e com interação real com os menus.
- Preservar a prática avançada por classe, progresso salvo, possibilidade de repetição, isolamento por herói e recompensas atuais.
- Usar o guerreiro-professor com capelo como identidade recorrente. Novas imagens devem preservar rosto, roupa, capelo e paleta; podem variar expressão e pose.
- Ilustrar novas cenas do tutorial no estilo cartoon pintado da referência e das cenas de armadilhas, sem texto incorporado nas imagens.

## Conceito narrativo recomendado

Enquadrar o Campo de Treinamento como uma avaliação prática da Guilda que se transforma numa pequena missão de reconhecimento: o grupo precisa confirmar a ameaça dos esqueletos na ala de treino e voltar reunido à saída. O Mestre de Armas apresenta o chamado, acompanha a orientação inicial e comenta a descoberta e o retorno. A saída atual funciona como extração; não é necessário criar um item de relatório nem mudar o tipo do objetivo principal.

## Fluxo da missão

1. **Briefing:** o Mestre de Armas explica o chamado, mostra o objetivo e apresenta vida e ficha.
2. **Preparação:** o jogador aprende a câmera e o movimento, abre o inventário, pega uma arma compatível e a equipa.
3. **Conhecer o herói:** antes do primeiro combate, abrir H, identificar uma habilidade disponível e fechar o menu. Para heróis com magia utilizável, abrir M, conferir uma magia e fechar o grimório. A lição de M é omitida ou adaptada para classes sem magia disponível.
4. **Primeiro combate:** atravessar a porta, atacar o alvo de treino e encerrar o turno, aproveitando os exercícios existentes de acerto e dano.
5. **Confirmar a ameaça:** enfrentar os esqueletos e usar as lições existentes de resistência e vulnerabilidade como parte da descoberta da missão.
6. **Retirada:** conduzir todos os heróis à saída. O Mestre de Armas encerra a missão e indica as salas de classe como treinamento opcional.

Os passos já existentes de câmera, movimento, baú, equipamento, combate, resistência e vulnerabilidade serão reorganizados e reescritos para servir a esse fluxo. Orientações como R para recentralizar e Esc para cancelar podem permanecer como dicas de consulta, sem competir com os objetivos principais.

## Trilhas de classe

As salas exclusivas e seus exercícios continuam no Campo de Treinamento, mas são apresentadas como aprofundamento voluntário depois da primeira missão. O jogador pode voltar a elas, repeti-las e manter o histórico como funciona hoje. Exercícios dependentes de classe, habilidade, magia, nível ou metamagia não entram no caminho obrigatório da missão comum.

O refém e os exercícios de proteção/cura continuam ligados às trilhas em que suas regras podem ser ensinadas sem exigir de todas as classes uma habilidade que não possuem.

## Retratos e cenas

- Usar `assets/portraits/mestre_de_armas.png` como retrato-base do instrutor.
- Criar variações do mesmo personagem para briefing, explicação, alerta e conclusão. Todas preservam o capelo, os traços faciais, a roupa e os detalhes dourados.
- Criar ilustrações de cena para os principais momentos da missão, usando a referência da Guilda para o traço, as cores quentes, a iluminação e as proporções expressivas.
- Manter texto, balões e objetivos como elementos da interface localizados; as imagens não carregam texto.
- Exibir o retrato maior na abertura e em cenas importantes; usar apresentação mais compacta nos passos de ação para preservar o tabuleiro.
- Não alterar retroativamente a arte de cenas de outras aventuras ou do restante do jogo. Esta direção se aplica às imagens novas do tutorial e às cenas que forem explicitamente escolhidas para ele.

## Limites

- Não mudar regras de combate, objetivos mecânicos, recompensas, persistência, multiplayer ou limpeza de itens emprestados.
- Não remover as lições atuais de classe nem as lições avançadas de consumíveis, armadilhas, venenos, servos e sobrevivência; elas permanecem como conteúdo opcional.
- Não converter a missão numa sequência de cenas que bloqueie a ação. O guia continua destacando e explicando, e o jogador mantém controle livre.
- Não editar diretamente `src/lang/tutorial_guia.js`, que é gerado. Textos-fonte e scripts autoritativos devem permanecer nos arquivos de autoria existentes.
- Preservar alterações locais não relacionadas em `server.py` e o retrato já criado.

## Critérios de aceitação

1. O briefing explica quem orienta o grupo, por que ele entrou na ala e o que significa completar a missão.
2. A trilha comum tem entre seis e oito objetivos de missão, em ordem compreensível; cada passo pede uma ação de cada vez.
3. H é apresentado antes do primeiro uso de habilidade e o jogador abre o menu de fato. M é apresentado e aberto quando o herói tem magia disponível.
4. C (ficha), I/inventário, objetivo e vida continuam visíveis no contexto adequado; mouse/teclado e gamepad recebem instruções compatíveis com os controles ativos.
5. A conclusão continua usando o objetivo `all_heroes_at_exit`; os exercícios avançados por classe continuam acessíveis e repetíveis sem se tornarem pré-requisito da missão.
6. O Mestre de Armas das imagens é reconhecivelmente o professor da referência, sempre com capelo e no estilo cartoon aprovado.
7. Os textos localizados ficam fora das imagens, e as imagens de cena deixam espaço para a interface.
8. As alterações de conteúdo usam os arquivos-fonte e scripts idempotentes apropriados; o mapa salvo continua carregável e editável.

## Riscos e decisões

- **A trilha atual é extensa:** o mapa contém 85 falas e 13 salas. A missão curta depende de separar objetivos comuns de exercícios opcionais sem apagar conteúdo ou frustrar o progresso atual dos heróis.
- **Atalhos variam por dispositivo:** H e M são atalhos de teclado; a interface precisa continuar oferecendo equivalentes visíveis para controle/gamepad.
- **Classes sem magia:** a apresentação de M deve refletir os recursos realmente disponíveis ao personagem e não criar um exercício impossível.
- **Consistência do instrutor:** variações geradas em momentos diferentes podem divergir. A imagem aprovada e a referência da Guilda serão fornecidas como referências em cada geração.
- **Integração visual:** o retrato deve acompanhar o diálogo sem cobrir HUD, tabuleiro ou alvos destacados, especialmente em telas estreitas.

## Fora de escopo

- Alterar ou substituir as cenas de armadilhas que já existem fora do tutorial.
- Reestilizar todos os retratos, peões, miniaturas, mapas ou interfaces do jogo.
- Criar animação labial, dublagem, música ou bloqueio de controles.
- Reformular os exercícios avançados por classe além dos ajustes necessários para deixá-los opcionais após a missão comum.
