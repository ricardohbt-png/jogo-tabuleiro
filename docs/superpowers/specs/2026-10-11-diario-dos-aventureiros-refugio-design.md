# Diário dos Aventureiros no Refúgio dos Heróis

## Objetivo

Criar um livro interativo na sala compartilhada do Refúgio dos Heróis, na Fazenda do Leste em Alva e Luz. O diário reúne o histórico da campanha e oferece um bestiário cujo conhecimento continua sendo individual para cada conta.

## Experiência

- O jogador encontra o livro como objeto clicável na sala compartilhada. Ele deve aparecer integrado à arte do cômodo, sobre a mesa ou na estante, e abrir o diário sem substituir o acesso ao baú ou ao quarto. A interação deve funcionar com mouse, teclado e gamepad.
- O diário tem três páginas: **Missões**, **Itens importantes** e **Bestiário**. A navegação entre páginas não fecha o livro; fechar e reabrir mantém uma apresentação consistente, sem alterar o progresso.
- A sala é compartilhada, mas o conteúdo exibido combina duas fontes: histórico da campanha para missões e itens, e perfil da conta atual para o bestiário. Conhecimento de monstros de um jogador nunca é enviado aos demais.

## Página Missões

- Registrar uma etapa somente quando o servidor confirmar o encerramento da missão em `handle_encerrar_missao`, após objetivos e condições de saída exigidos estarem satisfeitos.
- Cada registro usa identificadores estáveis da aventura, etapa e saída descoberta. Apresentar nome localizado, resumo curto e estado compreensível: concluída, saída encontrada ou etapa ainda incompleta.
- Para aventuras com rotas alternativas, registrar cada saída encontrada separadamente. Uma etapa que exige mais de uma saída não aparece como totalmente concluída até que todas as saídas obrigatórias sejam descobertas. Reentrar ou repetir uma saída já registrada não cria duplicatas.
- O histórico é compartilhado pela campanha. Uma conclusão feita por qualquer integrante aparece para o grupo.
- Em campanhas antigas, construir o histórico inicial a partir do progresso de etapas e rotas já persistido. Não inventar datas ou detalhes que os dados antigos não comprovem; registros reconstruídos sem data podem aparecer sem data.

## Página Itens importantes

- Registrar apenas itens marcados explicitamente como importantes para missão ou história. Equipamento comum, consumíveis de rotina e saque não entram automaticamente.
- Registrar no evento autoritativo de aquisição, usando o ID estável do item e texto/nome localizado no catálogo. O registro continua no diário se o item for depois consumido, vendido ou guardado.
- A lista é compartilhada pela campanha e não concede novamente o item. Registros repetidos do mesmo item na mesma campanha são deduplicados; se a narrativa exigir várias aquisições, o conteúdo deve usar eventos distintos e explicitamente configurados.
- Não reconstruir aquisições antigas sem uma evidência persistida confiável.

## Página Bestiário

- O livro mostra apenas conhecimento já adquirido pela conta que o abriu. A contagem pessoal de criaturas derrotadas continua sendo a fonte dos marcos **15, 30 e 50**.
- A progressão e os campos revelados devem seguir as mesmas regras e a mesma função de apresentação usadas pela inspeção de monstro com botão direito. O diário não pode revelar ficha, resistências, vulnerabilidades ou outras informações antes do marco correspondente.
- Antes da implementação, auditar a política atual de campos revelados por marco e corrigir qualquer campo que esteja escapando do nível de conhecimento — incluindo resistências, imunidades, vulnerabilidades e redução de dano. Definir uma única política canônica usada pelo inspetor e pelo diário.
- O servidor fornece os dados pessoais do bestiário apenas ao jogador solicitante quando ele abre a página. Não incluir esse conteúdo em payload compartilhado da campanha ou em broadcast da sala.
- Monstros sem conhecimento registrado não devem revelar dados como spoiler. A página pode exibir uma entrada ainda desconhecida com nome genérico, sem ficha, ou omitir a entrada até o primeiro encontro; escolher uma apresentação simples durante a implementação sem alterar os marcos aprovados.

## Dados e persistência

- Manter separados os dados compartilhados da campanha (histórico de missões e itens importantes) e os dados privados da conta (contagens e nível de conhecimento do bestiário).
- Usar uma estrutura própria para o diário em vez de reutilizar `journal`, que já guarda eventos técnicos e de campanha. Persistir a nova estrutura nos pontos de salvamento, checkpoint e migração de esquema pertinentes.
- IDs de aventura, etapa, saída e item são a identidade persistida; nomes e descrições são resolvidos pelos catálogos de idioma para permitir português e inglês sem duplicar registros por tradução.
- Migrações devem aceitar saves sem o novo campo e inicializar o diário vazio antes de qualquer reconstrução segura a partir do progresso existente.

## Limites e riscos

- A inclusão do livro precisa de um objeto/interação de cenário reutilizável no editor de cenas; não usar um slot de NPC nem substituir os controles atuais do baú e do quarto.
- O encerramento de missão e a aquisição de item precisam continuar autoritativos no servidor para evitar registros duplicados ou concedidos pelo cliente.
- Rotas alternativas podem deixar uma aventura parcialmente concluída. O diário deve refletir a descoberta de cada saída sem marcar prematuramente a masmorra inteira como completa.
- O bestiário é individual mesmo dentro de uma sala compartilhada. Qualquer payload de sala deve preservar esse limite de privacidade.
- Datas de eventos antigos e aquisições anteriores só aparecem quando houver dados que as confirmem.

## Arquivos e áreas prováveis

- `server.py`: esquema/migração do histórico da campanha, registro no encerramento de missão e na aquisição de item, e entrega privada do bestiário solicitado.
- `game.js` e `src/gameState.js`: abrir o livro, navegar pelas páginas, renderizar os registros e consumir os dados pessoais do bestiário.
- `game.css`: aparência do livro, páginas e estados responsivos.
- `city_scenes.json` e `tools/editor_scenes.js`: posicionar e editar o hotspot/objeto interativo da sala compartilhada.
- Arquivos de idioma em `src/lang/`: títulos, nomes, mensagens vazias e conteúdo localizado.
- Testes de servidor e cliente: deduplicação, rotas alternativas, migração, privacidade do bestiário e consistência das regras de revelação.
- `CLAUDE.md`: documentar os novos contratos de persistência, eventos e privacidade após a implementação.
