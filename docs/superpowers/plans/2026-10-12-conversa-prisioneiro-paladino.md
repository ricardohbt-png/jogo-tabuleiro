# Conversa e desabamento no treinamento do Paladino — plano

> **Execução:** plano executado inline após aprovação explícita do usuário.

**Objetivo:** narrar o resgate, a proteção contra o teto desabando e a cura do refém no tutorial do Paladino, sem alterar a progressão nem o dano existente.

**Abordagem:** integrar falas privadas nos eventos já existentes de início de lição, dano protegido e cura efetiva. Associar uma cena sem texto à lição Protetor e disparar um efeito visual de rochas sobre o refém usando evento privado, sem aplicar dano adicional.

**Arquivos:** `tutorial_training.py`, `server.py`, `src/gameState.js`, `game.js`, `src/lang/narracao.js`, `dungeons/campo_de_treinamento.json`, `tools/test_tutorial_refem.py`, e novo PNG em `assets/tela de transição/tutorial/`.

**Restrições:** não mudar ordem, gatilhos nem alvos das lições; o refém continua sobrevivendo ao dano controlado; a fala de agradecimento requer PV efetivamente recuperados; o efeito visual só ocorre no exercício do Paladino e não causa dano.

**Verificação:** executar primeiro testes de regressão que falhem antes da implementação, depois `python -X utf8 tools/test_tutorial_refem.py` e `python -X utf8 tools/test_tutorial_salas.py`; verificar compilação Python, validade do mapa e existência/carga dos novos recursos do cliente.

## Tarefas

### Tarefa 1 — Diálogo, cena e impacto visual privado

- [x] Adicionar testes de conteúdo e fluxo para pedido de ajuda, fala de ferimento, agradecimento após cura real e evento visual privado sem mudança adicional de PV.
- [x] Executar os testes e registrar falhas esperadas antes da implementação.
- [x] Adicionar falas localizadas para o prisioneiro e os gatilhos nos pontos de transição atuais.
- [x] Adicionar a cena ilustrada à fala do Mestre na lição Protetor.
- [x] Enviar o evento `training_rockfall` somente quando a demonstração protegida aplicar dano ao refém; encaminhá-lo ao cliente como animação 2D/3D sem alterar a simulação de dano.
- [x] Executar os testes listados e as verificações de sintaxe e dados.
