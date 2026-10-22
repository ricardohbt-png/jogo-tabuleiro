# Campanha "O Resgate de Elara" — desenho

Data: 2026-10-21. Autor da história: o dono do projeto (brainstorm em conversa). Este documento
descreve o QUE a campanha é e como ela se comporta; não escolhe mapas nem monstros (isso é do
plano de implementação). Onde Claude decidiu algo que o autor não disse, vem marcado como
**(escolha de Claude)**.

## Intenção

Uma campanha longa, com missões em três cidades (Alva e Luz → Vila do Riacho / Corvin → Graciero),
cujo centro é uma **escolha real**: depois da fazenda, o grupo decide entre perseguir as moças
sequestradas ou perseguir o mercenário que roubou uma relíquia do Templo. Os dois ramos mostram
cidades diferentes, divergem na Parte 2 e voltam a se encontrar em **Graciero**, onde o final
reage ao que o grupo escolheu, ao que salvou e a quão rápido foi.

O vilão aparente é pequeno (um mercenário, um traficante); os vilões verdadeiros nunca aparecem:
o grupo só sente que "algo muito maior, muito irritado" se move por trás. A campanha deve
terminar deixando esse rastro aberto, sem revelar Ferdinand nem Vael'mon.

## Metas

- Escolha de ramo que mude de verdade o que o jogador vê (cidades, missões, cenas, final).
- Relógio de urgência **suave**: quem joga com eficiência ganha um desfecho melhor; quem demora
  perde uma informação, nunca a campanha.
- A Elara é sempre salva; o peso das escolhas cai em outras coisas (o Olho, as outras moças, o
  bardo, a informação do Gilo).
- Falas extras por herói presente (Pedro, Henrique) sem exigir esses heróis no grupo.
- Reaproveitar o que o jogo já tem (cenas de taverna, bardos, mecanismos de fato, poste de
  entrada, cadeia de etapas sem descanso).

## Não-metas e anti-metas

- Revelar Ferdinand, Vael'mon ou o que é o Olho de Arveluz. (Anti-meta: se um jogador conseguir
  identificá-los só pelo jogo, a campanha falhou em manter o mistério.)
- Punir demais: nenhum caminho termina a campanha ou deixa o grupo sem avanço.
- Exigir um herói específico no grupo.
- Duplicar a campanha inteira em dois ramos independentes.

## A história (spoilers)

- **Vael'mon** é a designação dos demônios deste mundo (grafia exata: Vael'mon, sempre). Ele
  encomendou o **Olho de Arveluz**, relíquia sagrada do Templo de Alva e Luz. Mora numa região
  remota e nunca aparece.
- **Ferdinand "Mãos Puras"**, nobre elfo de **Porto Saledo**, é o chefe secreto de uma rede
  criminosa que atua em várias cidades principalmente por meio de **bardos**. Contratou o
  mercenário para um serviço que devia ser discreto. Nunca aparece; só suas ordens.
- **Gilo "Dedos Sujos"** é o mercenário. Para lucrar mais, aproveitou o serviço para sequestrar
  servas do Templo e vendê-las ao **Leonel**. Isso estraga a discrição: Ferdinand se irrita com
  ele, e o Vael'mon planeja vingança e punição contra o Gilo.
- **Leonel** é um nobre respeitado de Graciero, cidade grande, e lidera o tráfico de moças
  ("traficante de esposas"). De dia, respeitável; de noite, o chefe da rede de tráfico.
- **Elara** é irmã do Pedro (mago) e uma das servas sequestradas.
- **Exequiel** é o sacerdote do Templo: careca, manto de veludo vermelho bordado em ouro e pedras,
  anéis, dedo em riste, postura de quem manda. Sabe o que é o Olho e não conta; pressiona o
  grupo. **(escolha de Claude)** Em público demonstra preocupação com as moças; em privado só fala
  do Olho. (O autor ainda não confirmou esta nuance.) Há uma imagem de referência do personagem
  fornecida pelo autor, usável como arte da cena do Templo.

## Estrutura

### Parte 1 — Alva e Luz (comum a todos os grupos)

1. **Cena no Templo** (ponto `templo` de Alva e Luz, hoje sem cena de conversa; precisa ser
   criada e vinculada). Exequiel pede o resgate das servas, com recompensa. É o gatilho da
   campanha.
2. **A casa do bardo** (dentro de Alva e Luz): o bardo da rede é o dono, está **morto, calado pelo
   Gilo**. Armadilhas múltiplas, instrumentos, partituras com anotações estranhas e uma
   **passagem secreta** com o endereço de uma fazenda.
3. **A fazenda** (fora da cidade, no mapa-múndi): bandidos e armadilhas. O grupo percebe a
   distração pelo cenário (estábulos vazios, rastros de carroça, camas feitas às pressas, celas
   vazias) e um bandido ferido confirma: as moças já foram pela estrada e o líder voltou à
   cidade.
4. **Volta ao Templo:** o roubo do Olho **já aconteceu** enquanto o grupo estava fora; o Templo
   está em desordem. Exequiel pressiona sem explicar a relíquia.
5. **A escolha:** seguir as moças (ramo A) ou seguir o Gilo (ramo B).

**Relógio suave.** Conta as rodadas gastas na casa e na fazenda somadas, com limite **generoso**
(quase todo grupo cuidadoso fica dentro). Dentro do limite o grupo pode salvar as duas coisas
(moças e Olho); fora dele precisa escolher uma. Sinais de urgência por mensagens do Templo em
momentos fixos, sem contador na tela. Achar a passagem secreta cedo ou desarmar uma armadilha-chave
reduz o relógio. Nunca bloqueia: pelo menos uma das duas coisas é sempre salva.
**(escolha de Claude)** O limite exato e os sinais são ajustes de implementação e se calibram
jogando.

### Ramo A — as moças: Riacho → Graciero

**Vila do Riacho** (pequena; as moças presas num celeiro). Parte da vila foi paga pela rede; o
**bardo da taverna** é o olho da rede e avisa os bandidos de quem chega. Esqueleto de missões
(aprovado):

1. Chegada e sondagem (conversas na vila e na taverna; o grupo sente que algo está errado).
2. A casa de um morador comprado (investigação com armadilhas ou emboscada leve; prova a
   cumplicidade e expõe o bardo).
3. O confronto com o bardo: **escolha do grupo** — matar, interrogar ou poupar.
4. O celeiro: combate com os bandidos e resgate das moças. Elara já foi levada para Graciero.

**Escolha sobre o bardo e consequências:**

- **Matar:** a rede perde o olho no Riacho; o Leonel é avisado e fica mais cauteloso em Graciero.
- **Interrogar:** dá uma pista sobre Graciero; a vila fica abalada, sem lealdade ao grupo.
- **Poupar:** vira informante em Graciero; pode ajudar ou trair conforme **como foi tratado no
  caminho**. O tratamento vem de **escolhas de fala** (menus de conversa que gravam fatos) e de
  **ações no mundo** (por exemplo, entregá-lo à vila ou protegê-lo).

### Ramo B — o Gilo: Adhadal → Corvin → Graciero

1. **Floresta de Adhadal:** travessia difícil, duas missões ao ar livre, sem cidade no meio e sem
   descanso entre elas (estilo da Maré do Charco; usa o poste de entrada).
2. **Chegada a Corvin:** o grupo chega atrás do Gilo; as tavernas (bardo misterioso, homem
   sombrio) mostram que a rede o ajudou.
3. **A caçada em Corvin** (cidade e arredores): **o grupo luta com o Gilo e vence o combate**, mas
   ele **escapa para Graciero com a ajuda de um bardo da rede que aparece na hora**. Tecnicamente
   exige uma regra de fuga do chefe: ao atingir certa vida, ele sai do mapa e o objetivo conta
   como cumprido.
4. Pista em Corvin aponta que ele foi vender as moças ao Leonel.

### Graciero (final, comum aos dois ramos)

Esqueleto (rascunho aprovado em linhas gerais):

1. **Chegada e rumores** (taverna: homem nobre, elfo suspeito, gnomo). O relógio da demora volta a
   contar aqui.
2. **Pistas em duas frentes** na cidade que apontam para o Leonel. O bardo poupado aparece aqui,
   se foi tratado bem.
3. **A morte do Gilo:** ele chega fugindo e é morto por **escorpiões gigantes** em plena cidade,
   completando o castigo do Vael'mon. No **ramo A**, só se o grupo chegar rápido; se demorar,
   encontra apenas o corpo e menos informação.
4. **O esconderijo do Leonel** (masmorra final): a Elara está presa (sempre é salva); confronto
   com o Leonel.
5. **O final:** muda com as escolhas (ver tabela). Deixa no ar que "algo maior" continua.

**Onde está o Olho em cada ramo:**

- **Ramo B (Gilo):** o Gilo está com o Olho até morrer; o grupo o recupera do corpo.
- **Ramo A (moças):** o Gilo já entregou o Olho a uma **caravana da rede**, que sobe as montanhas
  acima de Graciero em direção a Porto Saledo.

### Rota opcional do Olho (só no ramo A)

Abre se **qualquer uma** destas condições valer (basta uma):

- o grupo **poupou o bardo e o tratou bem** no Riacho (ele dá a dica); ou
- o grupo foi **rápido em Graciero** e viu o Gilo morrer (ele diz a pista antes de morrer).

Trajeto pelas **montanhas acima de Graciero** (sentido Porto Saledo), algumas missões até
**interceptar a caravana** (guardas e um bardo agente da rede), mais difícil que o resto.
Com a via do bardo, ele guia o grupo e é **morto por um assassino no caminho, sem que o grupo
possa impedir**; o assassinato é **obviamente encomendado**, mas não se sabe por quem.
**(escolha de Claude)** O assassino pode reaparecer no fim da rota como testemunha/obstáculo.
Com a via do Gilo, o grupo sobe sem o bardo e perde essa cena.

## Resultados por escolha (resumo)

| Condição | Efeito |
|---|---|
| Rápido na Parte 1 | Pode salvar moças **e** Olho |
| Lento na Parte 1 | Escolhe uma das duas |
| Elara | Sempre salva, em Graciero |
| Bardo do Riacho morto | Leonel mais cauteloso em Graciero |
| Bardo interrogado | Pista sobre Graciero; vila abalada |
| Bardo poupado e bem tratado | Informante; abre a rota do Olho; morre no trajeto |
| Bardo poupado e mal tratado | Pode trair em Graciero |
| Rápido em Graciero (ramo A) | Vê o Gilo morrer; pista para o Olho |
| Lento em Graciero (ramo A) | Só o corpo; sem pista do Gilo |
| Ramo B | Recupera o Olho do corpo do Gilo |

## Falas por herói

Se o **Pedro** está no grupo: falas extras sobre a irmã. Se o **Henrique** está no grupo: zomba do
Pedro ("a irmã deve ser tão feia quanto ele"); ao conhecer a Elara se apaixona, e ela tem ranço
dele, mais ainda ao saber que ele ridiculariza o irmão. Com os dois, a cena tem tensão a três.
Sem eles, a história é a mesma. O momento do encontro com a Elara é o resgate em Graciero.

## O que o jogo já tem e o que falta

**Já existe:** as quatro cidades com taverna e NPCs (há "Bardo da taverna" em todas; Corvin tem
"Bardo Misterioso" e "Homem sombrio"; Graciero tem "Elfo Suspeito", "Homem nobre", "Gnomo");
requisito por fato, conversas que dão fato, slides de história condicionais, destinos ocultos em
cadeia, etapas emendadas sem descanso, `ocultar_apos_concluir`, `marcador_entrada` poste.

**Rascunhos do autor já no projeto (verificar antes de construir; não sobrescrever):**
no `world_adventures.json` há destinos "casa suspeita" (floresta, casa_secreta, gustavo),
"esconderijo de Leonel" (arquivos `resgate de elara.json` e `Introducao.json`), "Ad´Hadal" e
"Profundezas de Ad´Hadal" (`floresta.json`, `floresta_2.json`). Parecem protótipos desta mesma
história e devem ser avaliados para reaproveitamento no plano.

**Falta (peças novas do motor):**

1. Requisito por **herói presente no grupo** (para as falas do Pedro e do Henrique).
2. **Relógio de rodadas** somado entre duas masmorras (guardado no jogo salvo), com gatilho de
   fato "rápido"/"lento".
3. **Fuga do chefe** com objetivo cumprido (Gilo em Corvin).
4. **Escorpiões gigantes** como evento de cena (morte do Gilo), usando fichas existentes se
   possível.
5. Fatos e conversas para o bardo (tratamento) e para o assassinato inevitável.
6. Cena de conversa do **Templo** de Alva e Luz (hoje o ponto não tem cena).

## Pendências para o autor

- O destino "esconderijo de Leonel" existente é o mesmo desta campanha? (Pergunta feita, sem
  resposta direta.)
- O Exequiel deve agir de forma diferente em público e em privado (proposta de Claude).
- Nível esperado: **(escolha de Claude)** nível 1–2 na Parte 1, subindo até ~4–5 em Graciero;
  ajustar com o termômetro do editor.
- Recompensa do Templo: **(escolha de Claude)** valor a definir no plano.
- Quantas missões em Adhadal, Corvin e Graciero (os esqueletos acima são rascunho).

## Próximo passo

Plano de implementação em etapas: Parte 1 primeiro (cena do Templo, casa, fazenda, volta ao
Templo, relógio), depois Ramo A, Ramo B e Graciero, deixando por último a rota opcional do Olho.
