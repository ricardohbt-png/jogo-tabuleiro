# Bestas Repetidoras — Plano de Implementação

> Implementação da proposta aprovada pelo usuário nesta conversa.

**Objetivo:** Registrar duas bestas repetidoras mundanas, com arte, lojas e disparo duplo ativo.

**Regras:** `besta_repetidora_patrulha`: 1d6, alcance ortogonal 6, 70 moedas. `besta_repetidora_guerra`: 1d8, alcance ortogonal 8, 120 moedas. Ambas exigem duas mãos, aceitam todos os virotes e podem ser usadas por Guerreiro, Paladino, Bardo e Ladino. O Disparo Duplo custa a ação principal, faz dois ataques independentes contra o mesmo alvo, consome dois virotes e recarrega em 10 rodadas; requer dois virotes disponíveis antes de ativar.

**Abordagem:** Reutilizar `RANGED_AMMO`, o cálculo autoritativo de ataque/dano e o sistema de habilidades concedidas por armas. A habilidade aparece no menu com cooldown e mira ortogonal/linha de visão.

**Arquivos:** `server.py`, `src/gameState.js`, `game.js`, `src/lang/catalogo.js`, `src/lang/interface.js`, `tools/export_catalog.py`, `tools/editor_catalog.js` (gerado), `city_shops.json`, `CLAUDE.md`, `assets/itens/besta_repetidora_media.png`, `assets/itens/besta_repetidora_poderosa.png`.

**Verificação:** Sintaxe e integridade estática de catálogo, classes, estoques, munição, alcance, cooldown e imagens. Não executar testes de jogo nesta alteração.
