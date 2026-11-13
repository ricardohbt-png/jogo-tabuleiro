# Refeições para o grupo na taverna — plano de implementação

> **Execução:** implementação nativa nesta sessão.

**Objetivo:** Adicionar duas refeições de balcão que cobram por herói e restauram fome e sede de todo o grupo.

**Arquitetura:** O catálogo da taverna define os efeitos individuais e o preço unitário. O servidor valida a disponibilidade global da refeição, calcula o total pelo número de heróis, cobra o comprador e aplica a restauração a todos; o cliente calcula o mesmo total para exibição e habilita/desabilita a compra conforme o ouro do comprador.

**Stack:** Python (`server.py`), JavaScript (`game.js`), JSON (`city_shops.json`) e catálogo de traduções (`src/lang/catalogo.js`).

**Design:** `docs/superpowers/specs/2026-10-27-refeicoes-grupo-taverna-design.md`.

## Restrições

- Banquete de Comemoração: +40 fome e +40 sede por herói; 5 moedas por herói.
- Grande Celebração: +75 fome e +75 sede por herói; 12 moedas por herói.
- Cada opção pode ser comprada uma vez por visita para o grupo inteiro.
- A compra afeta as fichas de herói de `self.players` com `class_id`, excluindo Mestre e heróis de teste; procurações do Solo contam individualmente e a restauração respeita o máximo normal.
- Os preços unitários são fixos e ignoram modificadores de preço da cidade.
- Não alterar os efeitos das refeições existentes nem as provisões de mochila.
- Não adicionar nem executar testes nesta tarefa, conforme a instrução de trabalho vigente.

## Arquivos

- `server.py`: catálogo, preço fixo por herói, validação e efeito autoritativo de grupo.
- `game.js`: preço total, estado de uso global e texto de efeito na loja.
- `city_shops.json`: disponibilidade das duas refeições em todas as tavernas existentes.
- `src/lang/catalogo.js`: nomes e descrições em português e inglês.
- `CLAUDE.md`: registrar o contrato final da mecânica sem alterar os trechos locais preexistentes.

## Foco da revisão

- Comprador sem ouro para o total: compra recusada sem débito ou efeito.
- Refeição já usada nesta visita: compra bloqueada tanto no cliente quanto no servidor.
- Grupo com mais de um herói: preço e recuperação escalam pelo número de heróis, não pelo número de conexões.
- Herói perto do máximo: a recuperação respeita o limite normal de fome e sede.
- Visita seguinte à cidade: ambas as opções tornam-se disponíveis novamente pelo reset já existente.

## Tarefas

### 1. Catálogo, estoque e traduções

Editar `SHOP_TAVERN` com IDs estáveis `banquete_comemoracao` e `grande_celebracao`, cada um com metadados de refeição de grupo, preço unitário fixo de 5/12 (sem modificador de cidade), e recuperação 40/40 ou 75/75. Incluir ambos nas cinco listas de `city_shops.json`. Acrescentar nomes e descrições PT/EN ao catálogo de traduções.

### 2. Compra autoritativa do grupo e apresentação

Em `server.py`, antes do débito normal, identificar refeição de grupo, usar todas as fichas de herói de `self.players` (com `class_id`, sem Mestre ou herói de teste), multiplicar preço unitário pelo tamanho do grupo, recusar compra repetida ou ouro insuficiente sem alterar estado, e só então debitar, restaurar cada herói e marcar o ID como usado em cada membro. Preservar o efeito de clamp de `_restaurar_sobrevivencia` e o reset existente em nova visita.

Em `game.js`, mostrar restauração individual e preço total pelo tamanho de `GS.cityState.players`; usar a marcação compartilhada para desabilitar a linha para todos os membros da sala, e manter a comparação de ouro do comprador contra o total. O servidor permanece autoritativo.

### 3. Registro e revisão do escopo

Adicionar em `CLAUDE.md` a regra final, revisar o diff para confirmar que só os arquivos desta feature foram alterados pela implementação e deixar as modificações locais preexistentes intactas. Não rodar testes nesta tarefa.
