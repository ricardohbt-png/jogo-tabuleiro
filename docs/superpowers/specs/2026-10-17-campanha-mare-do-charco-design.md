# Campanha "A Maré do Charco" (Vila dos Charcos) — design

Data: 2026-10-17. Estado: **proposta aguardando aprovação** (nada construído).
Nome provisório; independente da campanha "Sombras sob Alva e Luz".

## Intenção

Uma campanha de pântano e floresta para grupos que chegam ao **nível 2 (ou perto dele)** e
terminam por volta do **nível 4**. Crianças somem da Vila dos Charcos; os heróis seguem os rastros
das bordas da mata até as palafitas abandonadas, atravessam o pântano e chegam a uma aldeia de
bruxos (xamãs goblins e necromantes) que usa como **arma** uma criatura que não consegue
controlar: um **Ferrão dos Charcos Adulto**, mais forte que o grupo. O jogador decide como lidar com ele.

O que torna a campanha diferente: o chefe final **não é um combate de frente**. É um recurso
tático — soltar o Ferrão contra os bruxos, ferir de longe com fogo, ou fugir.

## Objetivos

- Quatro destinos, cinco masmorras, em escalada, com o final mudando conforme o desfecho.
- Dois desfechos legítimos, com recompensas diferentes: **fugir** com as crianças (recompensa
  menor) ou **matar o Ferrão** (renome e recompensa maiores, final diferente).
- As crianças precisam sobreviver. Se morrerem, **a missão continua** (é preciso derrotar o Ferrão ou fugir por onde vieram), mas há **consequências**: grande perda de renome e hostilidade da Vila dos Charcos.
- Reaproveitar o que o jogo já tem: monstros existentes, hostilidade entre monstros, reações de
  terreno (fogo + piche), slides de história condicionais, destinos ocultos por requisito.

## Não-objetivos

- Várias crianças como peões separados (o motor tem **um** refém por masmorra; ver "Reféns").
- Monstro novo, arte nova ou sistema novo de combate. Artes de slides saem como pedido
  (`ARTES_PEDIDAS`), como na campanha anterior.
- A continuação (o Ferrão Ancião, ND 8, fica só como gancho no texto final).
- Modo Mestre (o desenho vale sem Mestre; com Mestre, o comportamento é o já existente).

## Anti-objetivos (falhas mesmo que "funcione")

- Impasse: o grupo perder a chave, o Ferrão ou as crianças de um jeito que impeça terminar.
- O Ferrão tratar só os heróis como inimigos (a graça é ele ferir os bruxos).
- Mapa que depende de o jogador adivinhar a alavanca: cada mecanismo precisa de pista.
- A consequência da morte das crianças disparar no meio de uma ação e corromper o turno, ou ser aplicada duas vezes.
- Nenhum jeito de sair quando as crianças morrem: sempre há a saída de entrada, e matar o Ferrão conclui a missão.
- Salvar o mapa no editor apagar a campanha: o gerador precisa ser reexecutável, como
  `tools/gerar_campanha_sombras.py`.

## A história, destino a destino

**Gancho (taverna da Vila dos Charcos).** A cena da taverna já existe com 3 NPCs sem nome e sem
conversa. Um deles vira uma mãe aflita: nas últimas noites sumiram crianças; a aldeia de palafitas
dos pescadores, rio abaixo, foi abandonada depois de ataques de "algo desconhecido". A conversa
dá o fato `charcos_criancas_sumidas`, que revela o primeiro destino. A vila contrata o grupo.

1. **Bordas da Mata** (nível 2). Floresta fechada, trilha de lama e mato alto.
   Inimigos: lobos (Lobo Cinzento), **Lobo Alfa** como mini-chefe da matilha, ratos e ratos
   gigantes, aranhas sombrias, escorpião de pedra, escorpião pequeno, cobra venenosa.
   O grupo acha só vestígios: ossos roídos, marcas de arrasto e um sapatinho enlameado. O rastro
   leva a uma ponte quebrada; é a saída. Secundário opcional: matar o Lobo Alfa.

2. **Palafitas dos Pescadores** (nível 2–3). Casas sobre estacas, passarelas, água e margem.
   Inimigos: crocodilo jovem, **jacaré** como mini-chefe, cobra constritora e venenosa, devorador
   orgânico (corrói equipamento), escorpiões. Ninguém no local; pilhas de ossos; tábuas podres
   (armadilha de Chão Ilusório nas passarelas). Uma **carta do pescador** conta de homens
   encapuzados e de "algo" que tem medo de fogo. Um depósito traz **Frascos de Óleo e de Piche**,
   a pista de como ferir o Ferrão. Os rastros arrastados seguem para o pântano.

3. **Travessia do Pântano** (nível 3). Terreno de pântano (movimento lento), ilhotas e água.
   Inimigos: crocodilos, cobras, ratos gigantes, escorpiões e dois **zumbis infectados** (primeiro
   sinal dos necromantes). Termina com a aldeia à vista.

4. **Aldeia dos Bruxos** (nível 3–4), duas masmorras **emendadas** (nada se recupera entre elas):
   - **4A — Os Arredores:** paliçada, vigias, esqueletos humanos e animais, um xamã goblin, zumbis.
     Termina no portão.
   - **4B — A Aldeia:** a praça, o cercado das crianças e a cova do Ferrão (ver abaixo).

## A Aldeia (4B), o coração da campanha

- **Zonas:** portão (saída de volta ao pântano), praça (goblins combatentes, xamãs, necromantes,
  esqueletos, zumbis), cercado com as crianças e a cova do **Ferrão dos Charcos Adulto**.
- **As crianças** são **um único peão, "As Crianças"** (o grupo). É o refém do motor: livre depois
  de aberto o cercado, controlado por quem o abriu, e **se morrer a missão falha**. O objetivo
  principal é levá-lo até a saída.
- **O cercado** abre com a **Chave do Cercado**, que o **necromante-chefe** (Necromante, ND 2,
  marcado como alvo secundário opcional) carrega; se ele morrer a chave cai no saque dele.
  Condição de porta já existente (decoração-chave/baú-chave), sem criar mecanismo novo.
- **A cova** é uma cela murada **dentro da mesma sala da praça**. Uma **alavanca** (decoração com
  mecanismo, a passagem secreta da parede da cela) abre a cela. Quem puxa é o grupo: é a escolha.
- **Hostil a todos.** O Ferrão leva `hostility_override` com todos os monstros. A hostilidade entre
  monstros só vale para criaturas **da mesma sala** — por isso a cela fica na sala da praça. Os
  bruxos (xamãs e necromantes) levam uma regra própria contra o tipo `ferrao_charcos_adulto`, para
  revidarem e tentarem contê-lo; sem isso ele os massacraria sem resistência.
- **Ferramentas do grupo:** Frascos de Óleo e Piche do depósito das palafitas; poças de piche (e
  barris) espalhadas perto dos totens e da cova; água e pântano ao redor. Fogo no piche acende
  uma mancha que queima o Ferrão (reações de terreno existentes).
- **Fuga:** com o cercado aberto, as crianças vão até o portão com o Ferrão no encalço.

## Desfechos e recompensas

| | Fugir | Matar o Ferrão |
|---|---|---|
| Objetivo | Principal: o grupo de crianças chega à saída | Secundário opcional: alvo `kill_target` no Ferrão |
| Renome | o da rota (`renome_recompensa`, proposta: 2) | + renome extra do objetivo secundário (proposta: +3) |
| XP e ouro | pequenos (proposta: XP 150, ouro 60) | grandes (proposta: XP 600, ouro 250) + item |
| Item | — | arma única "troféu" do Ferrão (a definir; ver "Fica para o construtor") |
| Final | slides comuns | + slide extra e sem a frase de "fugiram da fera" |
| Crianças mortas (a missão segue) | consequência imediata: renome −5 e a vila hostil. Depois: **matar o Ferrão** conclui a missão com XP reduzido, sem ouro nem renome, e final amargo; **fugir** pela escada deixa a rota sem concluir | — |

Números são propostas; a simulação de ND (`--simular`) calibra antes de fixar.
**Se as crianças morrerem (decisão do autor):** a missão **não termina**. O Ferrão continua sendo a
ameaça: o grupo pode derrotá-lo, ou fugir por onde veio (a escada de entrada). Mas a morte tem
**consequências imediatas e permanentes**, aplicadas uma única vez no instante em que acontece:
- **Perda de renome grande** (proposta: −5, nunca abaixo de zero).
- **A Vila dos Charcos fica hostil:** marcador `charcos_criancas_mortas`. A vila reage na cidade
  (ver "Hostilidade da vila").
- **Como terminar:** se o Ferrão for derrotado, a missão pode ser encerrada normalmente, com um
  **final amargo** (o monstro tomba, mas as crianças não voltam) e só XP reduzido; a rota conta como
  concluída. Se o grupo fugir, a rota **não** é concluída: as consequências ficam, e uma nova
  tentativa recomeça a etapa com tudo restaurado (refém vivo de novo) — a vila continua hostil.
- Se o Ferrão já tiver morrido quando as crianças morrerem (por exemplo, por fogo no piche), a
  missão já pode ser encerrada na hora.

### Hostilidade da vila

**Decidido pelo autor: opção B.** Enquanto o marcador `charcos_criancas_mortas` existir:
- **Diálogos:** a conversa do gancho some e as da taverna mudam — a mãe e os outros NPCs falam com
  raiva, recusam ajuda e acusam o grupo.
- **Preços:** tudo o que se compra na Vila dos Charcos (taverna e ferreiro) custa **50% mais**. A
  venda (o que o grupo recebe) não muda.
- **Mecanismo novo:** um modificador de preço por marcador nas lojas da cidade, num arquivo
  próprio, `cidade_modificadores.json` (`{cidade: [{"fato": "...", "preco_mult": 1.5}]}`) — separado
  de `city_shops.json` para o editor de cidades não o apagar ao salvar. É aplicado no servidor na
  compra e no estoque enviado ao cliente (o preço mostrado tem de ser o cobrado); a venda continua
  pelo preço base. Sem tela no editor nesta entrega.
Redenção (recuperar a confiança da vila) fica para uma campanha posterior.

## O que precisa mudar no motor

1. **Recompensa de objetivo com `renome` e `fato`.** `_conceder_objetivo_reward` passa a somar
   `renome` (inteiro, pode ser negativo, piso do total em zero) e a gravar `fato` em `self.fatos`;
   `validar_dungeon` valida; o painel de objetivos do editor ganha os campos (preservados no
   roundtrip). O marcador `charcos_ferrao_morto` alimenta o final.
2. **Consequência da morte do refém.** O objetivo principal `rescue_prisoner` aceita
   `se_falhar: {renome, fato}`. Quando `_prisioneiro_morre` marca `rescue_failed`, o servidor aplica
   **uma vez** (guarda `_consequencia_refem_aplicada`, na foto) a perda de renome, grava o marcador e
   narra — e **não** encerra a missão. Como roda no meio do turno dos monstros, só modifica
   estado e narra; nada de trocar de tela ali.
3. **Conclusão alternativa.** `objectives.alternativo` (um `kill_target`, com XP/recompensa reduzidos)
   só vale depois de `rescue_failed`: `_check_objectives` passa a tratá-lo como objetivo efetivo
   (cumprindo-o habilita "Encerrar missão"); o bônus secundário de matar o Ferrão **não** é pago
   nesse caminho para não duplicar. O HUD mostra o principal como falhado e o alternativo como o
   novo objetivo. O final de `handle_encerrar_missao` escolhe os slides pelos marcadores.
4. **Requisito negado `sem_fato`** em `_clean_requirement`/`_avaliar_requisito` (o marcador NÃO existe),
   para a conversa do gancho sumir depois da tragédia e para slides do final.
5. **Hostilidade da vila (cidade):** diálogos por marcador (já existe `fato`) e o modificador de
   preço por marcador nas lojas da cidade (opção B, decidida).
6. Nada mais: reféns em grupo, hostilidade monstro×monstro, piche/fogo, destinos ocultos, etapas
   emendadas e slides condicionais **já existem**.

## Dados e geração

- Gerador reexecutável `tools/gerar_campanha_charcos.py`, no molde do da campanha anterior:
  cria as 5 masmorras (grade, salas, monstros, decoração, materiais, objetivos), os 4 destinos em
  `world_adventures.json` (ocultos, encadeados por `requisito`), a conversa do NPC da taverna e os
  itens custom. Modo `--simular` relata ND por sala e as artes pedidas.
- Posições dos destinos no mapa-múndi perto da Vila dos Charcos (58,6; 66,6), com custo 1–3 de fome e sede.
- IDs previstos: `charcos_bordas`, `charcos_palafitas`, `charcos_travessia`, `charcos_aldeia`
  (duas etapas); masmorras `charcos_1_bordas`, `charcos_2_palafitas`, `charcos_3_travessia`,
  `charcos_4a_arredores`, `charcos_4b_aldeia`.

## Testes

- Servidor: objetivo com `renome`/`fato` concede e grava; validação rejeita valores inválidos;
  idempotência do gerador; as cinco masmorras passam em `validar_dungeon`; cada destino só
  aparece após o anterior; a conversa do NPC revela o primeiro destino.
- Fluxo do Ferrão com o motor real: cela fechada = sem ataque; alavanca aberta = ataca monstros da
  mesma sala; bruxos revidam.
- Crianças mortas: a perda de renome e o marcador são aplicados **uma vez** (piso em zero) e a
  missão **segue**; o objetivo principal fica falhado e o alternativo vira o ativo; matar o Ferrão
  habilita "Encerrar missão" com o final amargo e XP reduzido, sem pagar o bônus secundário; fugir
  pela escada deixa a rota sem concluir e mantém as consequências; a conversa do gancho some e as
  da taverna mudam (`sem_fato` e `fato`); morte das crianças com o Ferrão já morto conclui na hora;
  a morte no meio da cadeia de iniciativa não deixa turno pendurado; nova tentativa recomeça a etapa.
- Simulação de ND por sala dentro da faixa pretendida por nível.
- Final: os slides certos para fuga e para morte do Ferrão.

## Riscos

- O Ferrão (ND 5) contra um grupo de nível 3–4 pode matar rápido: calibrar pontos de vida do
  entorno, distância e tempo até a fuga. Mantê-lo mais lento que o grupo não é possível sem
  mexer na ficha dele; resolver com desenho de mapa (portão estreito, obstáculos, pântano que o
  retarda — ele ignora pântano, os heróis não, então a fuga tem de ser curta).
- A hostilidade monstro×monstro exige a mesma sala; um desenho errado deixa o Ferrão preso e inofensivo.
- Reféns como um único peão: o texto e a arte precisam deixar claro que representa o grupo todo.
- A conclusão alternativa mexe no coração de `_check_objectives` (principal/secundário, recompensas e "Encerrar missão"): é o ponto de maior risco técnico; testar com a fila real e com os dois desfechos.
- Nova tentativa depois de fugir restaura as crianças vivas (a masmorra recarrega), mas mantém renome perdido e vila hostil: aceitável, e precisa estar claro no texto.

## Decisões minhas (para você conferir)

- Quatro destinos e cinco masmorras; níveis 2 → 4.
- A Aldeia em duas etapas emendadas (Arredores + Aldeia) para dar tensão sem descanso.
- Chave do cercado com o necromante-chefe; alavanca separada para a cela do Ferrão.
- Hostilidade dos bruxos só contra o Ferrão.
- Valores de renome, XP e ouro acima (o autor escolheu a hostilidade B: preços +50%).
- O NPC da taverna é uma mãe das crianças desaparecidas (nome a escolher).

## Fica para o construtor

Mapas e coordenadas finas; nomes dos NPCs, da aldeia e do necromante-chefe; texto e quantidade
dos slides; o item-troféu (arma única, sugestão: perfurante, acuidade, +1 acerto, dano de veneno
leve; preço sugerido em torno de 400); quantas cabanas/totens e onde ficam as poças de piche;
a calibragem final de ND e de XP.
