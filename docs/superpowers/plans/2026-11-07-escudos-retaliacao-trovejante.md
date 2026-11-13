# Escudos da Retaliação Trovejante — Implementation Plan

> Plano para executar o design aprovado pelo usuário; sem adicionar testes automatizados nesta tarefa.

**Objetivo:** Adicionar três escudos mágicos com +1 CA sobre o modelo base, Manto de Raios por 5 rodadas, recarga de 20 rodadas e retaliação de 1d6 elétrico por ataque recebido que acertar.

**Abordagem:** Reutilizar os catálogos e habilidades concedidas por equipamento existentes. Persistir duração e recarga na instância do escudo equipado; integrar a reação no fluxo central de ataques de monstros e expor ativação/menu para o herói. Criar PNGs separados para os três formatos.

**Decisões aprovadas:** Escudo pequeno (1.400 moedas), escudo grande metálico (1.800) e escudo grande de madeira (1.650); classes permitidas e redução de dano seguem os modelos-base; habilidade usa ação principal e custo padrão de 1 fome/1 sede.

**Arquivos:** `server.py` (catálogo, compra/equipamento, ativação, habilidade e retaliação), `game.js` (botão e ação), `src/lang/catalogo.js` (nomes/descrições PT/EN), `tools/export_catalog.py` e `tools/editor_catalog.js` (catálogo do editor), `CLAUDE.md` (documentação), e três PNGs novos em `assets/itens/`.

**Verificação:** Conferir diferenças, sintaxe Python/JavaScript e consistência do catálogo gerado; não executar testes, pois o usuário não pediu teste nesta etapa.
