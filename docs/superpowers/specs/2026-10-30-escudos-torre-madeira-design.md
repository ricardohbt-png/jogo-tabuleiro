# Escudo Torre e Escudo Grande de Madeira — design

## Objetivo

Adicionar dois escudos nativos usando ícones PNG novos: um Escudo Torre Romano de metal para o Paladino e um Escudo Grande de Madeira Reforçado acessível também ao Clérigo.

## Regras

- Escudo Pequeno (`escudo_p`): preço 20 moedas; +1 CA e redução 1.
- Escudo Grande (`escudo_g`): preço 50 moedas; +2 CA e redução 2.
- `escudo_torre`: +3 CA, redução 2 por instância de dano, apenas Paladino, preço 70 moedas, material metálico e corroível pelo Devorador de Metal.
- `escudo_madeira_grande`: +2 CA, redução 1 por instância, Clérigo/Guerreiro/Paladino, preço 35 moedas, madeira e corroível pelo Devorador Orgânico.
- Ambos ocupam a mão secundária e usam a Guarda Máxima existente do Paladino, sem habilidade ou exceção nova.
- Usar `assets/itens/escudo_torre.png` e `assets/itens/escudo_madeira_grande.png`.

## Abordagem

Registrar ambos em `SHOP_ARMORS`, adicionar seus IDs às cinco lojas de armaduras, localizar nomes e descrições, regenerar o catálogo do editor e documentar material, preço, classe e bônus. A corrosão usa `corrosion_materials` existente.

## Fora de escopo e verificação

Não mudar a Guarda Máxima, corrosão global, regras de movimento, ou criar habilidade ativa. Verificar arquivos PNG com alpha, sintaxe Python/JavaScript, JSON das lojas, catálogo exportado e `git diff --check`; não executar testes automatizados sem pedido.
