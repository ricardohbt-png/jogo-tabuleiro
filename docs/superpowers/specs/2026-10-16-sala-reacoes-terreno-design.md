# Sala das Reações de Terreno (Campo de Treinamento) — design

Data: 2026-10-16. Estado: **proposta aguardando aprovação** (nada construído).

## Intenção

O jogo ganhou reações entre elementos e terreno (fogo + gás, fogo + piche,
água que protege do fogo, destaque de mira). O Campo de Treinamento ainda não
ensina nenhuma. O objetivo é uma sala nova, entre o corredor de armadilhas e a
saída, em que **todo herói, de qualquer classe, aprenda fazendo** as duas
reações que qualquer um consegue provocar: gás + fogo e piche + fogo, e de
quebra "água protege do fogo".

Por que só essas: fogo vem de itens que as 6 classes usam (Frasco de Óleo, já
ensinado na sala 22), enquanto frio e eletricidade só existem em magia de Mago e
Clérigo. A trilha comum não pode exigir o que nem todos têm.

## Objetivos

- Uma sala longa, em duas partes, entre a sala 50 (armadilhas) e a saída.
- Parte 1 (gás + água): um gás permanente ocupa a sala e a porta de saída fica
  selada até ele ser detonado. O Frasco de Óleo só existe num baú numa ilha de
  água dentro do gás: o herói entra, pega o frasco, fica na água e detona. A
  água corta o dano da explosão pela metade, e a lição mostra isso.
- Parte 2 (piche + fogo): lição **opcional**; o herói joga o Frasco de Piche e
  depois o de Óleo num boneco e vê o fogo se espalhar.
- Funcionar para as 6 classes, sozinho ou em grupo, sem nenhum caminho que trave
  o grupo nem mate um herói.

## Não-objetivos

- Ensinar frio/eletricidade na trilha comum (ficam para lições opcionais nas
  salas do Mago e do Clérigo, fora deste design).
- Ensinar fogo + gelo, água profunda e redemoinho.
- Mexer nas lições que já funcionam (ordens 1–35) ou no objetivo
  `all_heroes_at_exit`.
- Dar ao editor de masmorras suporte para criar esse gás: o conteúdo nasce de
  script, como as fatias anteriores.

## Anti-objetivos (falhas mesmo que "funcione")

- Qualquer ordem de ações deixar o grupo sem poder terminar o treinamento.
- Um herói de nível 1 morrer por causa da sala (o Mago tem 7 PV).
- Quebrar os testes do tutorial atual ou o idempotente `configurar_tutorial_salas`.
- Salvar o mapa pelo editor apagar a sala (o script precisa ser reexecutável).

## A experiência, passo a passo

1. Fim do corredor de armadilhas (`fala_armadilhas`, ordem 35). O herói chega à
   porta `[51,25]` e a sala 49 já está **cheia de gás** (nuvem visível). Nova
   fala `fala_gas` (ordem 36) explica: o gás é inflamável, o fogo o detona, e
   água protege do fogo.
2. Ele nota que não há como atirar de fora: não tem frasco. O baú com 3 Frascos
   de Óleo está numa ilha de água no meio da sala. Atravessar custa pouco veneno
   (1 de dano, Fortitude CD 10, no início de cada turno dentro do gás).
3. Na ilha, em casa de água, ele pega os frascos e joga um numa casa de gás
   próxima. A mira mostra "💥 Explosão" antes do arremesso. O gás explode, o
   herói leva metade do dano por estar na água, a porta de baixo destranca e a
   lição conclui.
4. Parte 2 (`fala_piche`, ordem 37, opcional): sala logo abaixo, com baú de
   2 Frascos de Piche + 2 de Óleo e um boneco. Jogar cada frasco é uma ação
   principal, então o herói joga o piche num turno e o óleo no seguinte (o piche
   dura 4 rodadas), e vê a ignição. Pode ser ignorada.
5. `fala_retirada` (ordem 38, antes 36) reúne o grupo na saída nova. Seu
   `continua_sem` ganha `fala_piche`, para a lição opcional nunca bloqueá-la.

Quem tem fogo em magia (Bola de Fogo) pode detonar de longe: permitido, a
lição conclui do mesmo jeito.

## Geometria

O grid sobe de 57×33 para **57×40**. A sala 49 **não muda de lugar**:

| Elemento | Antes | Depois |
|---|---|---|
| Sala 49 | `x48..53, y26..31`, saída | mesma geometria, vira a **sala do gás** |
| Porta de baixo | — | `[51,32]` (nova, com condição `gas`) |
| Sala 51 (nova) | — | `x48..53, y33..38`, parte 2 |
| Saída (`exit`) | `[51,29]` | `[51,36]` |
| Linha 39 | — | parede |

Sala do gás: lago raso (material `agua`) em `x50..52, y28..29`; baú em `[51,29]`
(casa de água); porta de entrada `[51,25]` já existe. Sala 51: baú em `[49,35]`,
boneco em `[52,36]` (a ≤4 casas do herói perto da porta). Coordenadas finas são do
construtor, desde que o baú fique **dentro** do gás e **em água**.

As duas salas nascem `locked: true`, como as demais.

## Mecânica (servidor)

1. **Zona de gás permanente.** A `camara_gas` ganha o campo `permanente`: os dois
   pontos que reduzem `duracao` (câmara e nuvem) o respeitam. A zona da sala 49 é
   criada na preparação do treinamento, por id (`gas_tutorial`), de forma
   idempotente, com `dificuldade: 10`, `dano: "1"` e novo campo
   `dano_explosao: "1d4"`. Ela já persiste na foto da masmorra.
2. **Dano da explosão por zona.** `_rx_explodir_gas` usa `zona.get("dano_explosao")`
   quando existir; senão, os 2d6 de hoje. Isso mantém o jogo normal idêntico.
3. **Porta com condição `gas`.** Tipo novo de `door_conditions`:
   `{"type":"gas","zona_id":"gas_tutorial"}`, satisfeito quando a zona não está
   mais ativa. Entra em `validar_dungeon`, no carregador, em
   `_door_condition_satisfied`/`_door_condition_message` (chave nova em
   `erros.js`) e no serializador. **Não** usar a condição `licao` existente: lição
   pulada não entra em `licoes_feitas` e poderia prender o grupo.
4. **Dois verbos de lição novos:** `explodir_gas` e `incendiar_piche`, em
   `LICAO_VERBOS` e no módulo do editor (`editor_guia_logic.js`, que o teste de
   sincronia compara). São emitidos por `_rx_explodir_gas` e `_rx_incendiar_piche`.
5. **Lição de estado compartilhado.** O gás é um só: quando explode, o evento vai
   a **todos** os heróis do treinamento cuja lição ativa é a `fala_gas`. Se um herói
   dispara a `fala_gas` com o gás já consumido, a lição é marcada como pulada (sem
   prêmio), como em `_pular_etapas_abandonadas`.
6. **Rede de segurança de frascos.** No início do turno de um herói do treinamento,
   se o gás ainda está ativo, ele não tem Frasco de Óleo e o baú da ilha está vazio,
   o servidor coloca 1 frasco emprestado (`tutorial_loan`) na bolsa, com narração. É o
   que impede o travamento por frascos perdidos.

## Dados e script

- Novo `tools/aplicar_fatia20_tutorial.py`, cirúrgico e idempotente, chamado
  também por `configurar_tutorial_salas.py`: amplia o grid, move a sala/saída,
  cria sala 51, lago, baús, porta `[51,32]` com condição, boneco, as falas
  `fala_gas` e `fala_piche`, reordena `fala_retirada` (36 → 38) e ajusta o alvo.
- Textos pt/en em `tools/tutorial_guia_comum.py` (+ `gerar_guia_comum.py` gera
  `src/lang/tutorial_guia.js`). Glossário: `reacao`, `inflamavel`. Regra de ouro:
  nenhum `conclui_com` para algo que o herói possa ter feito antes.
- `tools/editor_dungeons.js` regenerado depois de validar a masmorra.
- O `CLAUDE.md` ganha o registro da fatia.

## Testes

- Servidor: gás permanente não dissipa; `dano_explosao` respeitado; porta fecha e
  abre conforme a zona; explosão por óleo jogado da ilha; a água reduz o dano pela metade
  (4 → 2); evento chega a todos; lição pulada quando o gás já acabou; frasco de
  socorro; **nenhum herói das 6 classes morre** no pior caso (dano máximo, no
  gás, com veneno); idempotência do script duas vezes seguidas.
- Fluxo real com iniciativa e `push_state` (padrão `FluxoRealTests`), incluindo
  grupo de 2 heróis.
- Cliente: o aviso da porta selada; prévia "💥 Explosão" na mira (já coberta).
- Ajustar os testes existentes que citam a saída ou a ordem 36
  (`test_tutorial_conteudo`, `test_tutorial_fatia8`, `test_tutorial_resistencia`;
  este último já espera uma saída antiga, `[51,24]`, e precisa ser revisto).
- Provar no navegador (servidor isolado) o caminho completo, como a fatia 13.

## Riscos conhecidos

- **Partidas de treinamento salvas no meio do caminho** perdem a foto da
  masmorra: `_foto_conferir_arquivo` descarta a foto quando a grade do mapa muda
  (aviso `erro.foto_masmorra_descartada`). O progresso da ficha não se perde; o
  herói recomeça o Campo de Treinamento. Aceito porque é um tutorial curto.
- **Salvar o mapa pelo editor** apaga a sala nova se o arquivo for reescrito sem
  rodar o script (mesmo cuidado das fatias 7 a 13). O editor precisa preservar o
  tipo de condição de porta `gas`; verificar no roundtrip.
- **Baú em casa de água:** confirmar que o validador de masmorra aceita; se não,
  o baú vai numa casa de chão colada ao lago.

## Decisões minhas (para você conferir)

- Dano de veneno 1 / CD 10 e explosão 1d4 só no tutorial: com 7 PV o Mago
  morreria com os números normais.
- Três frascos no baú + frasco de socorro, em vez de um barril infinito.
- A parte 2 é opcional e a parte 1 é obrigatória só pelo bloqueio da porta.
- Sala do gás **reaproveita a sala 49**; a saída desce em vez de a sala nova ficar
  no caminho entre 49 e a saída.

## Fica para o construtor

Coordenadas finas dos lagos/baús/boneco; redação dos textos; se o gás nasce na
preparação do treinamento ou no primeiro `game_state` (o resultado visível é o
mesmo); onde exatamente fica o hook do frasco de socorro.
