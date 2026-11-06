# Vários prisioneiros por mapa e resgate por faixas

Data: 2026-11-06. Estado: aguardando aprovação do autor.

## Por que

Hoje cada mapa tem um único refém. Isso obriga a representar um grupo por uma peça só ("As Crianças", nos Charcos), e a missão vira tudo ou nada: ou o refém sobrevive, ou tudo se perde. O autor quer colocar vários reféns no mesmo mapa, juntos ou espalhados, e fazer o resultado da missão depender de quantos foram salvos. O primeiro uso é o resgate da Aldeia dos Charcos, com 6 crianças de aparências diferentes.

## Objetivos

- O editor de masmorras permite colocar vários prisioneiros num mapa, em qualquer lugar, cada um com nome e arte próprios.
- Uma missão pode pedir que os reféns sejam levados à saída ou à entrada do mapa.
- O autor define, por mapa, a meta de reféns e o que cada quantidade salva rende ou custa.
- O herói que liberta um refém o controla e pode alternar entre guiá-lo à mão e deixá-lo seguir sozinho.
- A Aldeia dos Charcos passa a usar tudo isso.

## Fora de escopo

- Reféns que andam sozinhos até a saída sem herói, ou que lutam.
- Controle dos reféns pelo Mestre, além do que ele já faz hoje com o refém único.
- Mudar a história de outras missões. A Elara e os demais mapas seguem com um refém e o comportamento atual.
- Arte 3D nova. O garoto ruivo e a menina ruiva, que só têm PNG, não ganham GLB aqui.

## O que não pode acontecer

- Um mapa antigo, com um refém, mudar de comportamento ao carregar ou ao salvar pelo editor.
- Uma partida salva dentro de uma masmorra se perder ou travar por causa da mudança.
- A missão ficar sem saída: sempre tem de existir um jeito de encerrar enquanto houver herói vivo.
- O turno ficar arrastado com 6 reféns seguindo o grupo: quem segue não pode pedir clique nem abrir vez própria.

## Como funciona no jogo

**Cativo.** Cada refém tem 7 PV, CA 10 e 6 de movimento, como hoje. Enquanto preso, não é alvo de monstros. Armadilhas e áreas seguem a regra atual do refém preso.

**Libertar.** Um herói adjacente liberta um refém por vez e isso gasta a ação principal, como hoje. Com mais de um refém adjacente, ele escolhe qual.

**Controle.** Quem libertou controla aquele refém. Se esse herói morrer, o controle passa ao herói vivo mais próximo, como hoje.

**Guiar ou seguir.** O herói alterna o modo de cada refém a qualquer momento, sem gastar ação.
- **Guiar (padrão):** o refém se move à mão na vez pós-turno do herói, junto da fila dos servos e na mesma ordem estrita.
- **Seguir:** ao fim do turno do herói, o refém anda sozinho até 6 casas, pelo terreno e com as mesmas regras de movimento, buscando ficar adjacente ao herói. Não abre vez nem pede clique. Sem caminho, fica parado.

Nos dois modos ele ocupa casa, pode ser atacado e dispara armadilhas ao pisar. Morre ao chegar a 0 PV.

**Chegada.** O refém que alcança o destino (a casa ou uma vizinha, como o resgate atual) some do mapa e conta como salvo na hora. A partir daí não pode mais ser atingido. O destino é a saída ou a entrada do mapa, conforme a missão. Vale para os dois modos.

**Contagem.** O resultado só olha quantos foram salvos. Refém deixado para trás conta como não salvo, igual ao morto. O HUD de objetivos mostra salvos, mortos, total e meta (por exemplo, "3/6 salvas, meta 4").

**Fim da missão.** O botão "Encerrar missão" aparece quando uma destas condições vale:
- os salvos atingiram a meta;
- não resta nenhum refém vivo no mapa (nem preso, nem liberto).

Com a meta atingida, o grupo pode encerrar ou arriscar buscar os demais. **A recompensa é calculada ao clicar em Encerrar**, não ao atingir a meta, para contar quem foi salvo depois e os objetivos secundários cumpridos até ali. Hoje os secundários são pagos no instante em que o principal se cumpre, e isso precisa mudar para este tipo de objetivo.

**Faixas.** A missão lista faixas por quantidade de salvos. Cada faixa dá XP, ouro, renome (positivo ou negativo) e pode gravar um fato. Vale a faixa correspondente à quantidade no encerramento. Toda quantidade de 0 ao total precisa cair em exatamente uma faixa. O XP e o ouro seguem as regras normais de divisão entre heróis vivos.

## No editor

- A ferramenta de prisioneiro passa a adicionar: cada clique coloca mais um, até 12 por mapa.
- O painel de cada refém edita nome, imagem e modelo 3D, com a escolha de arte que já existe. Selecionar, mover, apagar, copiar e colar funcionam em cada um.
- O nome do refém é opcional. Sem nome, segue "Prisioneiro".
- O objetivo de resgate ganha: destino (saída ou entrada), meta e a tabela de faixas (de, até, XP, ouro, renome, fato).
- A validação avisa: meta maior que o total, faixas com buraco ou sobreposição, destino ausente no mapa.
- Abrir e salvar um mapa de um refém não pode mudar o arquivo além do que muda hoje.

## Os Charcos

Etapa `charcos_4b_aldeia.json`. As 6 crianças ficam juntas na cela que já existe, com a mesma forma de abrir. O destino é a saída do mapa. O Ferrão vira objetivo apenas opcional: o `alternativo` sai e o secundário `kill_target` fica, com a recompensa atual.

| Salvas | Renome | XP | Ouro | Fato | Vila |
|---|---|---|---|---|---|
| 6 | +8 | 225 | 90 | `charcos_criancas_todas` | agradecida |
| 4 ou 5 | +5 | 150 | 60 | `charcos_criancas_salvas` | agradecida |
| 3 | 0 | 90 | 36 | `charcos_criancas_perdidas` | de luto |
| 2 | −2 | 60 | 24 | `charcos_criancas_perdidas` | de luto |
| 1 | −4 | 30 | 12 | `charcos_criancas_perdidas` | de luto |
| 0 | −8 | 0 | 0 | `charcos_criancas_mortas` | hostil, preços +50% |

A coluna de renome foi confirmada pelo autor. XP e ouro são a escala do autor aplicada aos valores atuais do objetivo (150 XP, 60 de ouro).

- O destino `charcos_mare` passa a ter `renome_recompensa: 0`, porque as faixas já dão o renome. Sem isso, o +5 da rota somaria com a tabela.
- A hostilidade continua presa a `charcos_criancas_mortas`, que agora só é gravado ao encerrar com 0 salvas.
- Com faixas, a morte de um refém não dispara `se_falhar` nem marca o resgate como falho: a consequência vem só da faixa, no encerramento. Derrota total dos heróis segue a regra atual.
- O final da rota ganha slides por fato: todas salvas, meta atingida, perdas, e o final amargo atual para zero. Os slides do Ferrão seguem como estão, condicionados a `charcos_ferrao_morto`.
- Uma conversa de luto na taverna da vila aparece com `charcos_criancas_perdidas`.

Crianças, arte e nome (nomes são escolha provisória, o autor pode trocar no editor):

| Nome | Modelo |
|---|---|
| Tico | `garoto_loiro` |
| Bento | `garoto_medieval` |
| Davi | `garoto_pele_escura` |
| Lina | `menina_cabelos_castanhos` |
| Maia | `menina_pele_escura` |
| Rosa | `menina_ruiva` (só imagem 2D, aparece como figura plana no 3D) |

As casas exatas dentro da cela ficam para quem constrói, em piso livre. O autor pode reposicionar depois no editor.

## Compatibilidade

- Mapa com a chave `prisoner` continua válido e carrega como lista de um refém. Objetivo `rescue_prisoner` sem faixas funciona exatamente como hoje, inclusive `se_falhar`, `alternativo` e as etapas da mansão.
- Partida salva dentro de masmorra antiga precisa continuar: foto com o formato antigo de refém é convertida ao carregar, e os objetivos gravados nela seguem como foram gravados.
- O refém de treinamento do Paladino segue funcionando.

## Testes que precisam existir

- Mapa de um refém igual ao de antes: Elara, celeiro, tutorial do Paladino.
- Seis reféns: libertar um por vez, alternar modo, seguir sem abrir vez, chegar e sumir, morrer.
- Efeitos de área, Protetor, armadilhas e reações atingindo o refém certo, sem confundir um com outro.
- Fim da missão: meta atingida, todos mortos, parte morta e parte salva, herói controlador morto.
- Faixas: cada quantidade de 0 a 6 paga o valor certo, e o secundário cumprido depois da meta também é pago.
- Foto antiga retomada; foto nova com vários reféns salva e retomada no meio.
- Editor: salvar e reabrir com vários reféns, conservando nome, arte, faixas e destino.
- Cliente real, em 2D e 3D: seis peões distintos, botão de modo, contador no HUD.

## Decisões tomadas sem o autor (para conferir)

1. Libertar continua custando a ação principal, um refém por vez. Com 6 crianças, um grupo de 4 heróis leva cerca de 2 rodadas só soltando.
2. Quem segue anda ao fim do turno do herói, até 6 casas.
3. Teto de 12 reféns por mapa.
4. O modo é por refém, e todo refém começa em Guiar.
5. Nos Charcos, o destino é a saída do mapa, a mesma de hoje.
6. Reféns presos continuam fora do alcance dos monstros.
7. Os nomes e a escolha de arte das 6 crianças.

## Fica para quem constrói

- Formato exato dos campos no mapa, desde que o arquivo de um refém não mude.
- Identificador estável de cada refém, substituindo o `__prisioneiro__`/`pr:singleton` de hoje, que aparece em cerca de 160 pontos de servidor e cliente.
- Forma da mensagem que alterna o modo e da que escolhe o refém ao libertar.
- Textos novos em PT e EN.
