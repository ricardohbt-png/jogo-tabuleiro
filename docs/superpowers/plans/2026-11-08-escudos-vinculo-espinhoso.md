# Escudos do Vínculo Espinhoso — Plano de Implementação

**Objetivo:** Adicionar uma variante mágica para cada perfil nativo de escudo: pequeno (2.400 moedas), grande metálico (2.800), torre metálico (3.300) e grande de madeira (2.650).

**Regras comuns:** +1 CA sobre o modelo-base; preserva redução de dano, classes permitidas e materiais de corrosão. Enquanto equipado, concede uma ação principal que lança Vínculo Maldito da Dor sem consumir slot, com teste de Vontade normal, um alvo por ativação, duração fixa de 5 rodadas e recarga de 25 rodadas desde a ativação; custo de ativação segue a magia (1 fome/1 sede). Máximo de quatro vínculos e penalidade de −1 no próximo ataque seguem as regras existentes da magia.

**Abordagem:** Reutilizar o catálogo `SHOP_ARMORS`, o executor existente de Vínculo Maldito da Dor e o padrão de habilidades concedidas por equipamento. Armazenar recarga na instância equipada; criar quatro PNGs transparentes usando os escudos nativos como referência; adicionar os quatro itens aos ferreiros e aos catálogos/localizações.

**Arquivos:** `server.py`, `game.js`, `src/lang/catalogo.js`, `tools/export_catalog.py`, `tools/editor_catalog.js`, `city_shops.json`, `CLAUDE.md`, quatro ícones em `assets/itens/`.

**Verificação:** Sintaxe, diff, estoque/catálogo e transparência dos ícones. Sem testes de jogo nesta etapa.
