# Variantes de materiais para escudos — plano de implementação

**Meta:** Criar 12 variantes mundanas de escudos com efeitos, preços, imagens próprias e venda nos cinco ferreiros.

**Abordagem:** Gerar variantes dinamicamente em `SHOP_ARMORS` para preservar os dados/classes da base; etiquetar explicitamente a corrosão orgânica/metálica das bases; registrar IDs em `city_shops.json`; gerar PNGs transparentes por edição das artes-base; atualizar vocabulário, catálogo do editor e `CLAUDE.md`.

**Escopo aprovado:** Escudo Pequeno orgânico recebe Freixo Negro, Cedro Rubro e Cerne de Titã; Escudo Grande metálico e Escudo Torre recebem Aço Damasco, Obsidiana de Ferro e Liga de Titânio; Escudo Grande de Madeira recebe as três ligas de madeira. Escudos mágicos ficam fora.

**Regras:** Freixo/Aço Damasco = N=1/M=2, sem mudança de CA/redução, preço 1,5×. Cedro/Obsidiana = +1 CA, destruição no primeiro golpe corrosivo, preço 2×. Cerne/Titânio = N=2/M=3, preço 3×; adicionam +1 de redução física por instância aos modelos grandes/metálicos e de madeira, acumulável; o Escudo Pequeno não recebe redução adicional. Preços arredondados para cima a moeda inteira.

**Verificação:** Conferir carregamento dos 12 itens, campos, imagens com alfa, estoque nas cinco lojas, exportação do catálogo, sintaxe Python e integridade do diff; não criar nem executar testes automatizados.
