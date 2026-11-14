# Besta Pesada — Plano de Implementação

> Plano para executar nesta sessão a partir da especificação aprovada pelo usuário.

**Objetivo:** Adicionar ao jogo uma besta mundana de duas mãos, 1d10 perfurante, alcance reto de 12 casas, exclusiva de Guerreiro, Paladino, Clérigo e Ladino, por 100 moedas, com arte PNG própria e venda nos cinco ferreiros.

**Abordagem:** Seguir o contrato existente da `besta`: ataque por Destreza, virotes, alcance ortogonal, integração autoritativa no servidor e espelho no cliente. Criar `besta_pesada` com metadados explícitos e adicionar o ID aos fluxos genéricos de munição, projétil e interface.

**Arquivos previstos:** `server.py`, `src/gameState.js`, `game.js`, `city_shops.json`, `src/lang/catalogo.js`, `tools/editor_catalog.js` (gerado), `CLAUDE.md` e `assets/itens/besta_pesada.png`.

**Escopo:** Arma mundana; `1d10` perfurante; `stat: dex`; alcance `12` em linha ortogonal; duas mãos; classes `warrior`, `paladin`, `cleric`, `rogue`; preço `100`; aceita todos os virotes já aceitos pela Besta.

**Verificação:** Verificar sintaxe, exportação do catálogo, cinco estoques, presença de todos os tipos de virote, regras de alcance e assinatura/alpha da imagem. Não executar testes de jogo nesta alteração.
