# Veneno independente por arma — Plano de implementação

> **Para agentes executores:** executar este plano tarefa por tarefa no checkout nativo. As etapas usam caixas de seleção para acompanhamento.

**Objetivo:** Permitir que jogador e Mestre escolham uma arma específica para receber cada frasco, mantendo cargas independentes e consumindo-as apenas quando a arma correspondente acerta.

**Arquitetura:** Heróis armazenam as cargas no próprio item equipado (`gear.weapon` ou `gear.off_hand`), usando a arma principal como fonte de verdade compatível com saves atuais. Monstros armazenam cargas em cada entrada de `attacks[]`, separadas do `on_hit` original; os fluxos manual e de IA aplicam e consomem as cargas da entrada correta.

**Stack:** Python, JavaScript, JSON de estado do jogo, arquivos de localização em JavaScript.

**Especificação:** `docs/superpowers/specs/2026-10-22-veneno-por-arma-dupla-design.md`

## Restrições globais

- Uma aplicação de frasco envenena uma arma; envenenar duas armas exige dois frascos.
- Herói seleciona explicitamente `weapon` ou `off_hand`; Mestre seleciona explicitamente o índice de `attacks[]`.
- Cada arma/ataque tem fila FIFO independente; veneno dura 3 acertos, ou 6 com `ladino_veneno_2`; `ladino_veneno_3` permite dois venenos distintos enfileirados por arma.
- O erro não consome carga; um acerto consome uma carga somente da arma que atacou.
- Manter ações, bônus de ação, custos de sobrevivência, venenos nativos e decisão da IA conforme a especificação.
- Não adicionar nem executar testes automatizados nesta alteração. Fazer revisão estática e `git diff --check`.
- Preservar todas as mudanças locais preexistentes; editar e versionar somente os arquivos descritos neste plano.

## Foco de revisão

- A arma principal mantém cargas antigas após carregar ou salvar uma partida; conferir migração e persistência sem transferir veneno ao item que substituiu a arma.
- Ataque secundário não consome carga da principal, e ataque principal não consome carga da secundária; conferir ambas as mãos e acerto/erro.
- Ataques múltiplos do monstro gastam no máximo uma carga por acerto e só da entrada de ataque executada; conferir ataque manual e IA.
- Ataques com `on_hit` próprio do monstro preservam esse efeito e também aplicam o veneno de frasco.
- Aplicação com slot, índice, arma ou frasco inválido não remove o frasco nem altera ação/sede; validar antes de confirmar o consumo.

---

### Tarefa 1: Estado e resolução de veneno por arma

**Arquivos:**
- Modificar: `server.py` — `_weapon_poison_slots`, `_set_weapon_poison_slots`, `_capacidade_poison_arma`, `_aplicar_veneno_na_arma`, `handle_attack_impl`, `_execute_one_monster_attack_impl`, `_monster_execute_attacks`.

**Interfaces:**
- `weapon`/`off_hand`: cada item equipado armazena `poison_slots` como lista FIFO de IDs válidos; `_weapon_poison_slots(p)` e `_set_weapon_poison_slots(p, slots)` continuam compatíveis com a arma principal e com saves legados.
- Implementar `_poison_slots_do_item(p, slot) -> list[str]`, `_set_poison_slots_do_item(p, slot, slots) -> None` e `_aplicar_veneno_na_arma(p, veneno_id, slot="weapon") -> tuple[bool, int]`. `slot` aceita somente `weapon` ou `off_hand`; validar elegibilidade e capacidade para o item-alvo antes de gravar.
- Em `attacks[]`, armazenar a fila da arma como `poison_slots`; usar o índice do ataque para localizar o estado, sem escrever o veneno em `on_hit`.
- A resolução do ataque consome uma carga somente no acerto e aplica o veneno daquela carga, preservando o `on_hit` original do monstro. A IA escolhe a primeira entrada com fila disponível; o ataque manual recebe índice já selecionado pelo painel.

- [x] **Etapa 1: Adaptar persistência da arma principal e adicionar acesso validado à arma secundária.** Preservar a migração legada e a gravação no objeto equipado; calcular capacidade por arma, respeitando Veneno II/III.
- [x] **Etapa 2: Fazer cada resolvedor de ataque do herói ler a fila da arma que desferiu o golpe.** Ataque principal usa `weapon`; ataque bônus secundário usa `off_hand`; em erro nenhuma fila muda.
- [x] **Etapa 3: Separar filas envenenadas dos ataques de monstros e aplicar no acerto.** Atualizar execução manual e IA sem sobrescrever `on_hit`; limitar o consumo a um por acerto e à entrada executada.
- [x] **Etapa 4: Revisar caminhos de capacidade cheia, re aplicação do mesmo veneno e dois venenos distintos.** Aplicar as regras FIFO da especificação independentemente em cada item/ataque.

### Tarefa 2: Escolha explícita na interface e validação dos consumíveis

**Arquivos:**
- Modificar: `server.py` — mensagens `handle_use_item`, handler de `veneno_rapido`, `handle_mestre_usar_item` e dispatch `use_item`/`mestre_usar_item`.
- Modificar: `game.js` — `abrirPainelVenenoRapido`, fluxo de uso de frasco corpo a corpo e painel de consumíveis do Mestre.
- Modificar: `src/lang/interface.js`, `src/lang/erros.js`, `src/lang/narracao.js` — rótulos, confirmação e mensagens de resultado/erro.

**Interfaces:**
- Aplicação de herói envia `weapon_slot: "weapon" | "off_hand"` junto do frasco. O servidor revalida slot, arma, capacidade, item e custo antes de consumir.
- Aplicação do Mestre envia `attack_index: int` junto do `item_id`. O servidor valida que índice exista em `attacks[]` e aceite veneno antes de remover o frasco.
- A interface identifica arma/ataque, venenos ativos e cargas restantes; erros de validação mantêm o painel aberto para nova escolha.

- [x] **Etapa 1: Acrescentar seletor de arma ao painel de aplicação do herói.** Mostrar principal e secundária elegíveis com nome e cargas; desabilitar ou omitir slots vazios/incompatíveis; enviar `weapon_slot` escolhido.
- [x] **Etapa 2: Enviar o slot pela rota de uso de item comum.** Manter os fluxos existentes de arco/besta e munição; nenhuma aplicação de projétil deve ser redirecionada à mão secundária.
- [x] **Etapa 3: Acrescentar seletor de ataque ao uso manual de item do Mestre.** Listar ataques pelo nome, enviar `attack_index`, e só confirmar/consumir o frasco após validação autoritativa.
- [x] **Etapa 4: Atualizar mensagens de confirmação e falha.** Informar arma/ataque, veneno e duração (3/6 acertos); comunicar ausência de alvo elegível ou fila cheia sem consumir recursos.
- [x] **Etapa 5: Revisar a economia de ação e sede nos dois handlers.** Comparar com o comportamento atual do frasco e de Veneno Rápido; erros não podem deixar custo parcialmente aplicado.

### Tarefa 3: Atualizar contrato do sistema e revisar o diff

**Arquivos:**
- Modificar: `CLAUDE.md` — seção atual de venenos/`poison_slots`.

**Interfaces:**
- Documentar a fonte de verdade por arma, formato de `attacks[].poison_slots`, comportamento de acerto/erro e parâmetros `weapon_slot`/`attack_index` (preservando `gear_slot` como origem do frasco).

- [x] **Etapa 1: Atualizar a documentação do sistema de veneno.** Registrar que a seleção é explícita e as filas são independentes, incluindo Veneno II/III e compatibilidade com saves.
- [x] **Etapa 2: Fazer revisão estática dos fluxos alterados e `git diff --check`.** Confirmar que não há mudanças fora dos arquivos listados, nem substituição de `on_hit`, e inspecionar a ordem de validação antes do consumo.

## Revisão de cobertura

O plano cobre a escolha explícita de alvo, um frasco por arma/ataque, duração e capacidade de Veneno II/III, ataques primários/secundários, fila FIFO, acertos e erros, ataques múltiplos e manuais de monstros, escolha de IA, preservação de efeitos `on_hit`, ações/custos, falhas sem consumo, feedback de interface e documentação. As exceções de inputs inválidos e estado persistido estão no foco de revisão e nas tarefas proprietárias.


