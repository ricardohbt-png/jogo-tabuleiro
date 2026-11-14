# Assassino da Serra: armas e Veneno Rápido

**Objetivo:** Equipar O Assassino da Serra com Espada Longa de Aço Damasco na mão principal, Adaga de Obsidiana de Ferro na secundária, quatro frascos de Agonia Sufocante e Veneno Rápido com recarga de quatro rodadas.

**Desenho:** A ficha autoral permanece em `monstros_personalizados.json`, espelhada em `tools/editor_monsters_custom.js`. Um configurador específico de spawn materializa as duas armas e os quatro frascos; a IA aplica uma dose a uma arma sem veneno antes de atacar, respeitando o cooldown aprovado. A mecânica existente de três cargas e Agonia Sufocante é reutilizada.

**Restrições:** Cada arma realiza um ataque por turno; Veneno Rápido consome uma dose, cobre uma arma por três acertos e recarrega em quatro rodadas. Nenhuma outra ficha de monstro deve mudar.

**Verificação:** Conferir sincronização JSON/JS, IDs dos itens no catálogo e sintaxe dos arquivos modificados. Não adicionar nem executar testes automatizados nesta tarefa.

## Etapas

- [x] Atualizar ficha e espelho do editor com os ataques, habilidade, armas e quantidade de veneno.
- [x] Materializar o loadout no servidor e adicionar uso automático de Veneno Rápido à IA exclusiva do assassino.
- [x] Atualizar `CLAUDE.md` e validar dados/sintaxe/diff.
