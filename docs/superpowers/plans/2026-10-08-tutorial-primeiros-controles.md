# Tutorial dos Primeiros Controles — Plano de Implementação

**Objetivo:** Ensinar uma pessoa sem experiência a ajustar a câmera, mover o herói pelas casas alcançáveis e encerrar o turno, com falas diretas, alvos em destaque e instruções que acompanham o controle ativo.

**Abordagem:** Reordenar a introdução do Campo de Treinamento para colocar a orientação de câmera antes do primeiro movimento. Usar frases curtas no imperativo e destacar o alvo durante cada instrução: tabuleiro e ícones do gesto para câmera, casa alcançável para movimento, botão para fim de turno. Reutilizar as lições guiadas e o sistema existente de instruções por dispositivo, acrescentando somente a detecção mínima de interações de câmera necessária para confirmar os exercícios em 3D. Instruções de gamepad só aparecem enquanto o jogo identificar um gamepad ativo; sem ele, os controles explicados são apenas mouse e teclado. A janela acompanha conexão e desconexão. O conteúdo diferencia gesto de câmera de movimento do personagem e explica o significado das casas azuis.

**Arquivos previstos:**
- `dungeons/campo_de_treinamento.json` — ordem e tarefas iniciais da trilha.
- `tools/tutorial_guia_comum.py` — texto autoritativo do guia, português e inglês.
- `tools/gerar_guia_comum.py` e `src/lang/tutorial_guia.js` — regeneração do catálogo de textos.
- `src/guiaTutorial.js` — marcadores de instrução adaptáveis ao modo de entrada.
- `game.js` — reconhecer gestos de câmera no mouse e no gamepad, destacar o tabuleiro durante as instruções de câmera e redesenhar o guia quando o dispositivo mudar.
- `game.css` — aparência de alto contraste para os destaques da câmera e instruções de controle.
- `src/lang/tutorial.js` — rótulos localizados de zoom, rotação, deslocamento e avanço de turno para controle.

## Etapas

1. Colocar uma lição curta de câmera antes da tarefa inicial de movimento. Em 3D, praticar zoom para perto e para longe, rotação e deslocamento da câmera; no mouse usar roda, arrastar com botão esquerdo e arrastar com botão direito. Destacar a área do tabuleiro e exibir um ícone claro do gesto em cada passo. Somente se `_gamepadInput.active` estiver verdadeiro, mostrar instruções de gamepad: analógico direito e gatilhos para rotação e zoom, e deixar explícito quando uma ação não existe nesse esquema. Em 2D, explicar que esses gestos de câmera só estão disponíveis ao alternar para 3D, sem bloquear o tutorial.
2. Reutilizar `avancar_passo` para confirmar os gestos reconhecidos pelo cliente nos passos informativos existentes. O servidor já confere lição atual e impede avanço se o passo for final; a proteção contra repetição fica no cliente. Não alterar o protocolo de movimento nem controles de câmera fora dessa lição.
3. Reescrever a lição de movimento com uma instrução direta: casas azuis são destinos alcançáveis neste turno; clique na casa destacada para mover o herói. Preservar e reforçar o halo no destino e o indicador de caminho.
4. Reescrever o fim de turno em comando curto, destacar o botão e dizer Enter por padrão. Somente com gamepad ativo, incluir o rótulo do botão atualmente vinculado. Manter a atualização dinâmica da janela quando o controle conecta ou desconecta.
5. Regenerar os textos do guia e atualizar o JSON do Campo de Treinamento pela fonte autoritativa, preservando as outras falas e ordens.

## Revisão

- O modo 2D não exige executar gestos que não suporta nem impede o progresso.
- Cada gesto só avança o passo correspondente; repetir um gesto concluído não pula lições.
- A mensagem distingue explicitamente deslocar a câmera de caminhar com o herói.
- Cada fala usa uma instrução direta por vez e destaca visualmente o controle ou local que o jogador deve usar/observar.
- Sem gamepad ativo, não aparece nenhuma instrução exclusiva de gamepad; com gamepad ativo, os textos usam os comandos correspondentes e acompanham conexão/desconexão.
- Textos e rótulos estão localizados em português e inglês e refletem o dispositivo conectado.
- Não executar nem acrescentar testes nesta tarefa; validar a alteração por revisão do diff e inspeção da lição no mapa/editor quando a execução for aprovada.

## Decisão durante a implementação

- **Ruling:** Reusar `avancar_passo` em vez de criar novo evento no servidor — todos os exercícios de câmera são informativos e já permitem avanço manual; a mesma validação mantém o passo final protegido e evita protocolo de rede desnecessário. Custo se a decisão estiver errada: um cliente modificado pode pular uma etapa informativa, como já pode fazer ao clicar em Entendi.
