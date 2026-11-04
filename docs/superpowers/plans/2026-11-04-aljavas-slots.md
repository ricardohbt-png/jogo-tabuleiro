# Aljavas com slots — plano de implementação

**Objetivo:** Implementar o desenho aprovado em `docs/superpowers/specs/2026-11-04-aljavas-slots-design.md`.

**Arquitetura:** Cada aljava guarda suas pilhas de munição; o servidor valida movimentações e consumo, e a ficha apresenta os slots. A bolsa conserva seu limite padrão e pilhas legadas não são descartadas.

**Tecnologia:** Python, WebSocket e JavaScript existentes.

1. Acrescentar testes de capacidades, validação de munição, preservação ao desequipar e movimentação de pilhas, inclusive pilhas legadas; executá-los antes da implementação.
2. Implementar slots no servidor, movimentação segura, seleção e consumo durante ataques, preservando propriedades da munição e itens em jogos salvos.
3. Integrar os slots à ficha e atualizar limites, descrições, traduções e catálogo exportado.
4. Executar testes direcionados e verificações aplicáveis, incluindo combate, transferências, compatibilidade e sintaxe.
