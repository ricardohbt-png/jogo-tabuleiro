# Tutorial guiado — design

Data: 2026-10-07. Estado: proposto, aguardando revisão.

## Problema

Um jogador sem experiência em RPG teve muita dificuldade no Campo de Treinamento. O servidor já entrega cada lição só ao herói que a recebeu e só a conclui quando valida a ação (`_licao_evento`, `tutorial_training.py`). A falha está em como a lição chega ao jogador:

1. A lição descreve, mas não aponta. "Selecione Mira Certeira e ataque o alvo" não mostra qual botão nem qual boneco.
2. Cada lição é um parágrafo na janela do canto (`#licao-janela`), com explicação, instrução e contexto misturados.
3. O jargão (1d20, Classe de Armadura, ação bônus, slots, fome, sede, resistência, "armar") aparece cedo e junto, sem definição. São 18 lições comuns antes da sala do herói.
4. Não há ajuda quando o jogador trava ou age fora do esperado.
5. "Procure a porta da sala do seu herói" não mostra caminho.
6. Fechar a janela deixa o jogador sem a instrução na tela (só o quadro ⚑ do HUD a reabre).

## Decisões já tomadas

- **Condução:** o guia destaca e deixa o jogador livre. Nada é bloqueado.
- **Conteúdo:** as 62 lições são reescritas em passos curtos, para quem nunca jogou RPG, com o jargão explicado na primeira vez em que aparece.
- **Modelagem:** híbrida. O guia é derivado da tarefa por padrão; a lição pode declarar `guia` com passos próprios.

## Fora de escopo

- Bloquear a interface ou liberar ações uma a uma ("mãos guiadas").
- Voz, narração gravada ou animação de personagem instrutor.
- Mudar as regras das lições, os requisitos, a persistência de `tutorial_history` ou o contrato das salas exclusivas.
- Tutorial fora do Campo de Treinamento.

## Visão geral

```
servidor (autoritativo)                 cliente
  lição + guia ─ fala{licao_id,passo} ─> janela da lição (passo i de n)
  _licao_evento ── avança passo ───────> licao_passo ─> guiaTutorial.js ─> halo/seta
  ação fora do esperado ── licao_dica ─> dica contextual
```

O servidor continua decidindo o que conta. O cliente só mostra.

## 1. Modelo de dados

### Passo

```json
{
  "id": "mira_1",
  "texto": "Clique em Mira Certeira.",
  "porque": "Ela prepara o próximo golpe: você soma +2 no teste de acerto.",
  "ui": "habilidade:mira_certeira",
  "dica": ["O botão está na barra de baixo.", "Procure o ícone da mira, ao lado de Golpe Devastador."],
  "conclui_com": {"tipo": "armar_habilidade", "alvo": "mira_certeira"}
}
```

- `texto`: uma frase, uma ação.
- `porque`: opcional, letra menor.
- `ui`: alvo do destaque (ver seção 3). Opcional.
- `dica`: lista escalonada. A 1ª sai depois de `DICA_1_S` sem progresso, a 2ª depois de `DICA_2_S`.
- `conclui_com`: condição do passo, no mesmo vocabulário de `tarefa`. Se ausente, o passo conclui junto com a lição (passo informativo, com botão "Entendi").

### Lição

O campo novo `guia` é uma lista de passos. A lição só termina quando a `tarefa` existente for cumprida; os passos são o caminho até lá.

Sem `guia`, o servidor gera um passo único a partir de `tarefa` (tabela da seção 3.2). As lições atuais continuam funcionando sem migração.

Campos de texto de passo (`texto`, `porque`, `dica`) aceitam chave de idioma (`ui.tutorial.<slug>`), como o resto da interface.

### Estado por jogador

`p["licao_passo"]` guarda o índice do passo atual da lição pendente. Entra na ficha da sala (foto da masmorra) e é zerado quando a lição conclui. `tutorial_history` não muda.

## 2. Servidor

- `_disparar_fala` (lição): o payload `fala` ganha `passo`, `passo_i`, `passo_n`, `ui`, `porque`.
- Avanço de passo: dentro de `_licao_evento`, após validar o evento, compara-se com `conclui_com` do passo atual. Se bater, `licao_passo` avança e o servidor envia `licao_passo` ao herói. Se era o último e a tarefa foi cumprida, segue o fluxo atual de `_licao_concluir`.
- **Dica por erro:** nos pontos onde o servidor já recusa uma ação por não servir ao exercício (alvo errado, fora da sala, fora de turno, habilidade sem armar), envia `licao_dica {motivo}` com uma chave de idioma. Motivos iniciais: `alvo_errado`, `habilidade_nao_armada`, `fora_da_vez`, `sem_acao`, `longe_do_alvo`. Rate limit de uma dica de erro por 5 s por herói.
- **Dica por tempo:** quem mede é o cliente (seção 4), porque o servidor não tem relógio ocioso por herói. O servidor só entrega o texto das dicas no payload do passo.
- **Resultado da ação:** `licao_resultado {texto}` emitido após a ação do exercício, montado de valores que já existem (`attack_feedback`, `dice_roll`, custo de fome e sede). Textos por chave de idioma com parâmetros.
- Validação (`validar_dungeon`): `guia` é lista de objetos; `ui` segue o formato da seção 3.1; `conclui_com.tipo` pertence ao vocabulário de tarefas; texto não vazio; no máximo 8 passos por lição.

## 3. Alvos de destaque

### 3.1 Vocabulário de `ui`

| `ui` | Destaca |
|---|---|
| `botao:<id>` | Botão fixo do HUD (`encerrar_turno`, `bolsa`, `grimorio`, `ficha`) |
| `habilidade:<id>` | Botão da habilidade na barra do herói |
| `bolsa:<item_id>` | Item na bolsa do inventário aberto |
| `slot:<slot>` | Slot de equipamento |
| `casa:[x,y]` | Casa do tabuleiro |
| `monstro:<tipo>` | Monstro daquele tipo à vista, o mais próximo |
| `porta:[x,y]` | Porta, com caminho tracejado até ela |
| `hud:<id>` | Medidor (`fome`, `sede`, `vida`) |

Os botões do HUD recebem `data-guia="<id>"` para o cliente achar o elemento sem depender de texto. Isso evita o defeito já visto neste projeto de casar por texto em português.

### 3.2 Alvo padrão derivado da tarefa

| `tarefa.tipo` | `ui` gerada |
|---|---|
| `mover_ate` | `casa:alvo` |
| `pegar_item` | `casa` do baú mais próximo |
| `equipar` | `bolsa:<alvo>` |
| `encerrar_turno` | `botao:encerrar_turno` |
| `atacar`, `matar` | `monstro:<alvo>` |
| `usar_habilidade`, `usar_tecnica` | `habilidade:<alvo>` |
| `usar_item`, `arremessar_item` | `bolsa:<alvo>` |
| `abrir_porta` | `porta:alvo` |

## 4. Cliente

### 4.1 Módulo `src/guiaTutorial.js`

Puro, sem DOM, THREE ou `window`, como o `gameState.js`. Recebe o estado e o passo e devolve uma descrição do destaque `{tipo, alvo, intensidade}`. Contém a máquina de dicas por tempo: `tick(agora)` devolve o nível de dica (0, 1 ou 2) a partir do último progresso. O `game.js` registra o ouvinte em `GS.on('licaoPasso', ...)`.

`gameState.js` encaminha as mensagens `licao_passo`, `licao_dica` e `licao_resultado` como eventos, sem tocar em DOM. Cada evento tem um único `GS.on` (um segundo apagaria o primeiro).

### 4.2 Renderização (`game.js`)

- **Elemento de HUD:** classe `guia-halo` (anel pulsante via CSS) e uma seta presa ao elemento. Removidos ao avançar o passo.
- **Casa ou monstro, 2D:** anel no canvas, redesenhado a cada quadro de render.
- **Casa ou monstro, 3D:** anel no chão e seta flutuante acima da casa ou da miniatura, no mesmo padrão dos marcadores de turno. Acompanha a miniatura se ela anda.
- **Porta:** anel na porta e linha tracejada no chão pelo caminho `findPath` já existente, só entre casas visíveis.
- Alvo fora da tela ou da visão: uma seta na borda do tabuleiro aponta a direção.
- Intensidade: nível 0 é um pulso suave, nível 1 pulsa mais forte, nível 2 pulsa e mostra um balão com a dica.

### 4.3 Janela da lição

- Passa a mostrar "Passo i de n" e uma barra de progresso.
- Instrução em uma frase; `porque` em letra menor, recolhido por padrão.
- Botão "Me mostra" repete o destaque. Botão "Entendi" nos passos informativos.
- Fechar a janela não apaga o destaque na tela: o halo continua até o passo avançar.
- O quadro ⚑ do HUD mostra o texto curto do passo atual, não só o da lição.

### 4.4 Glossário

Termos marcados no texto como `[[ca]]`, `[[acao_bonus]]`, `[[slot]]`, `[[d20]]`, `[[fome]]` etc. viram sublinhado pontilhado. Tocar abre uma explicação curta em balão. As definições ficam em `src/lang/tutorial.js`, na chave `ui.tutorial.glossario.<termo>`. O termo só é sublinhado na primeira vez em que aparece na sessão do tutorial; depois sai como texto simples.

### 4.5 Resultado da ação

`licao_resultado` aparece como linha na janela da lição, por alguns segundos, por exemplo: "Você rolou 14 + 3 = 17 contra CA 12: acertou!". Se a janela está fechada, aparece no `#toast`.

## 5. Conteúdo

- As 62 lições do `dungeons/campo_de_treinamento.json` (a trilha comum, as de cada herói e as geradas por `_training_add_unlocked_lessons`) são reescritas em passos.
- Regras de redação:
  1. Uma ação por passo.
  2. Verbo no imperativo, frase de até 15 palavras.
  3. Nenhum termo do glossário sem marcação na primeira ocorrência.
  4. O "porquê" vem depois da ação, nunca antes.
  5. O texto nomeia o botão ou o alvo, além do destaque.
- A trilha comum é dividida em blocos pequenos: mover, pegar e equipar, atacar, encerrar turno, comer e beber, usar itens, armas contra resistências. Cada bloco tem um ou dois passos.
- Lições geradas (`treino_guild_*`, `treino_magia_*`) usam modelos de passo parametrizados pelo nome da habilidade ou magia.
- Texto em português e inglês. `tools/dividas.py` continua sendo o placar de idioma.
- A ferramenta `tools/configurar_tutorial_salas.py` passa a gravar `guia`. A edição manual do JSON continua possível.
- Editor de masmorras: o painel de fala ganha a lista de passos (texto, porquê, `ui`, dicas). Fica para uma etapa posterior; o JSON é a fonte da verdade.

## 6. Parâmetros

| Constante | Valor inicial |
|---|---|
| `DICA_1_S` | 12 |
| `DICA_2_S` | 30 |
| Intervalo mínimo entre dicas de erro | 5 s |
| Máximo de passos por lição | 8 |

Os tempos ficam em `VC.tutorial` (`src/visualConfig.js`), ajustáveis sem mexer na lógica.

## 7. Persistência e multiplayer

- `licao_passo` é por herói. Dois jogadores na mesma sala têm passos independentes.
- Salvar e continuar restaura o passo (foto da masmorra). Foto sem o campo começa no passo 0 da lição pendente.
- O contador de tempo das dicas é do cliente e reinicia ao carregar.
- Nada disso afeta XP, ouro, itens ou a ficha durável além do `tutorial_history` atual.

## 8. Testes

- `tools/test_guia_tutorial_cliente.js` (node): tradução de `ui` em alvo, alvo padrão por tipo de tarefa, máquina de dicas por tempo, glossário (primeira ocorrência).
- `tools/test_tutorial_guia.py` (servidor): `guia` válido e inválido em `validar_dungeon`; avanço de passo só com `conclui_com` correto; ação recusada não avança; `licao_dica` por motivo e rate limit; passo restaurado pela foto; dois heróis com passos independentes.
- `tools/test_tutorial_salas.py`: adaptar; os fluxos das seis salas continuam valendo.
- `tools/test_tutorial.py` está obsoleto desde o mapa novo (falha em [10b]). Remover as seções [10]+ e manter só o que ainda vale.
- Idioma: `tools/test_idioma.py` e `tools/dividas.py` cobrem chaves órfãs e paridade de parâmetros.
- Prova no navegador, com dados isolados (porta própria): guerreiro, mago e ladino completando a primeira habilidade, verificando o halo, as dicas por tempo e a retomada depois de salvar e sair.

## 9. Riscos

- **Alvo some da tela** (monstro morto, item usado): o guia cai no passo seguinte ou no destaque do botão mais próximo. Cobrir no teste.
- **Halo 3D com a janela oculta:** o rAF não roda; usar o mesmo recurso de prova dos outros efeitos 3D.
- **Texto reescrito diverge das regras:** os valores citados vêm do motor (`licao_resultado`), nunca de números fixos na prosa.
- **Escala do conteúdo:** 62 lições. Entregar por fatias: primeiro a trilha comum e o guerreiro, depois as outras classes.

## 10. Entrega em fatias

1. Mecanismo: `guia` no servidor e no validador, `guiaTutorial.js`, halo no HUD, janela com passos. Alvo padrão por tarefa.
2. Halo no tabuleiro (2D e 3D), porta com caminho, dicas por tempo e por erro, resultado da ação.
3. Glossário e reescrita da trilha comum.
4. Reescrita das seis salas por herói e das lições geradas.
5. Editor de masmorras: lista de passos no painel de fala (opcional).
