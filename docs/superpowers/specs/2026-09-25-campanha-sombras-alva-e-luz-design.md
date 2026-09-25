# Campanha "Sombras sob Alva e Luz"

Data: 2026-09-25
Status: design aprovado em brainstorming, aguardando revisão da spec

## Problema

O jogo tem sistemas ricos (classes com especializações, armadilhas, prisioneiro, magias de
área, passagens secretas, chefes com mecânica própria, história em slides, mapa-múndi com
destinos encadeados), mas quase nenhum **conteúdo jogável**: das 27 masmorras de
`dungeons/`, a maioria é de teste, e os 9 destinos de `world_adventures.json` são provas de
conceito. Um jogador que termina o tutorial (Campo de Treinamento) não tem para onde ir.

## O que estamos construindo

Uma campanha curta e caprichada, pensada para ser **a primeira depois do tutorial**:
3 destinos no mapa-múndi, 4 masmorras, grupo esperado de **4 heróis**, do nível 1 ao 3.

Decisões tomadas no brainstorming:

- **História nova e independente** (não continua "Resgate de Elara").
- **Estrutura:** 3 destinos; entre os dois primeiros o grupo volta à cidade; o último tem
  **2 andares emendados** (`encadear`), sem recuperar HP/fome/magias entre eles.
- **Chefe final: Troll.** O **Bugbear das Sombras** vira **chefe secreto opcional** no último
  andar, guardando um item de valor.
- **Imagens:** só texto agora; cada slide anota a arte que pede, para o autor subir depois.
- **Construção por script gerador** (reexecutável), não à mão nem pelo editor.
- **Campanha primeiro, curva de XP depois** (ver "Curva de XP" abaixo).

## Pré-requisito: salas obrigatórias perdidas no carregador (defeito do jogo)

Achado ao prototipar os Salões: `GameRoom.load_authored_dungeon` monta cada sala só com
`id`/posição/`role`/`locked`/`doors`/`door_orientations` e **descarta `required` e
`required_mode`**. Com nenhuma sala marcada, `_objetivo_cumprido("salas_obrigatorias")` faz
`all([])` e o objetivo **se cumpre no instante em que o grupo entra**. O objetivo nunca
funcionou numa masmorra real — o teste da Camada C ([23] de `test_modo_mestre.py`) monta
`r.rooms` à mão e não passa pelo carregador. Correção (primeira tarefa do plano): o
carregador preserva os dois campos, e uma lista vazia de salas obrigatórias passa a
**não** cumprir o objetivo (o validador já recusa `salas_obrigatorias` sem sala marcada;
a guarda é defesa em profundidade).

## Curva de XP — pré-condição conhecida, fora desta spec

A curva atual dispara: o XP por monstro é `150 × nível_médio × 2^(ND−1)` dividido entre os
vivos, e subir custa só `nível × 30` — quanto mais alto o nível, mais fácil subir o próximo.
Simulado para esta campanha com 4 heróis (um nível por abate, como `_check_level_up`), o
grupo sai do Vau no **nível 6** e termina no **nível 23**.

Esta spec **não** conserta a curva (subprojeto seguinte, a pedido do autor). Ela fixa uma
**curva-alvo explícita** que o conserto deve atender:

| Destino | Nível esperado na entrada |
|---|---|
| 1 · Emboscada no Vau | 1 |
| 2 · Minas de Pedra-Funda | 2 |
| 3 · Covil da Garra Negra (os dois andares) | 3 |

Cada masmorra grava esse nível em `expected_party {heroes: 4, level: N}`. Até o conserto, a
campanha fica fácil depois do Vau — é conhecido e aceito.

## História

**Gancho.** Em Alva e Luz, o **Bartender** da taverna ganha a conversa "As caravanas do
Vau": as caravanas que saem pela Estrada do Vau não chegam, e o último cocheiro, **Tomé**,
sumiu com a carga. Efeito da conversa: fato `sombras_caravanas`.

**1 · Emboscada no Vau.** A caravana tombada numa estrada de floresta, goblins
entrincheirados e lobos. Os heróis soltam Tomé, que conta que os goblins levavam a carga
para as velhas minas de Pedra-Funda.

**2 · Minas de Pedra-Funda.** Túneis de kobolds cheios de armadilhas; aranhas nas galerias
fundas; um ogro guardando o cofre da companhia de caravanas. Dentro do cofre, frascos de
ácido e de óleo que os kobolds nunca entenderam, e um bilhete com o sinal do bando — uma
garra negra — que fala do "guardião que não morre" (item `carta` com texto, que já existe).

**3 · Covil da Garra Negra.**
- **Salões de Cima:** a guarnição do bando (goblins veteranos, orcs mercenários, um mago
  sombrio).
- **O Trono de Pedra:** o **Troll** que o bando serve. Regenera 4 PV por turno e volta com
  1 PV depois de "morrer", exceto se o golpe final for de fogo ou se o ácido tiver bloqueado
  a regeneração — o kit do cofre das Minas é a resposta.
- **Esconderijo (secreto):** atrás de uma estante-mecanismo, o **Bugbear das Sombras** — o
  verdadeiro dono da garra negra —, que conjura o Manto da Escuridão e some nas trevas.
  Opcional; guarda o **Anel da Garra Negra**.

**Fim da rota.** Alva e Luz recupera as caravanas; o grupo ganha renome.

O texto é **conteúdo autoral** e fica em português, como as demais masmorras, falas e cenas
(regra do projeto: conteúdo do editor não passa pelo dicionário de idioma).

## Destinos no mapa-múndi (`world_adventures.json`)

Três entradas novas, todas `oculto_ate_liberar: true`, `revisitavel: false`, fome/sede de
viagem baixos (1/1, 2/2, 3/3):

| id | nome | requisito | etapas | renome |
|---|---|---|---|---|
| `sombras_vau` | Emboscada no Vau | `fato: sombras_caravanas` | `sombras_1_vau.json` | 1 |
| `sombras_minas` | Minas de Pedra-Funda | `aventura_id: sombras_vau` | `sombras_2_minas.json` | 1 |
| `sombras_covil` | Covil da Garra Negra | `aventura_id: sombras_minas` | `sombras_3a_saloes.json` (`encadear: true`) → `sombras_3b_trono.json` | 2 |

Posições `x/y` no mapa: próximas de Alva e Luz, afastando-se a cada destino (o autor pode
arrastar depois no editor do mapa-múndi).

História em slides (formato `{slides:[{text, image, fit}], audio}`):

- `intro` de cada etapa: 2–3 slides de texto;
- `outro` da etapa 1 do Covil + `intro` da etapa 2: a transição da escada;
- `outro` de cada destino e `outro_rota` do Covil: encerramento e fim da campanha;
- áudio: `assets/story/a_song_of_old_stones.mp3` nas aberturas;
  `assets/story/the_kraken_s_overture.mp3` na abertura do Trono;
- `image` vazio em todos os slides; o texto de cada slide que pede arte leva, no gerador,
  um comentário `# arte: <descrição>` — a lista de artes a produzir sai da execução do
  gerador (ver "Gerador").

## Masmorras

Régua de dificuldade: o termômetro do jogo (`src/difficulty.js`) — poder = heróis × nível;
faixa pela razão ND da sala ÷ poder (Fácil < 0,4 ≤ Equilibrada < 0,8 ≤ Difícil < 1,2).
ND da sala = soma de `monster_cr` dos monstros + `trap_cr` das armadilhas autoradas dela.

### 1 · Emboscada no Vau — `sombras_1_vau.json`

`ambiente: ar_livre` · `expected_party {4,1}` (poder 4) · objetivo `rescue_prisoner`
(xp 0, reward: 40 ouro) · `saida_permitida: true`. **O objetivo é uma escolta:** o servidor só
o dá por cumprido quando Tomé, já solto, está a 1 casa da **saída** — que fica na borda leste
do Acampamento ("a estrada segue para a vila").

| Sala | Conteúdo | ND | Faixa |
|---|---|---|---|
| Trilha (entrada) | 2 `goblin_arqueiro`, 1 `goblin_combatente`; armadilha `armadilha_urso` no caminho | 0,75 + trap | Fácil |
| Carroça tombada | 3 `goblin_combatente`, 1 `lobo_cinzento_customizado`; decoração `carroca`; baú com carga saqueada (ouro pequeno) | 1,25 | Fácil |
| Acampamento | 2 `goblin_combatente`, 2 `goblin_arqueiro`, 1 `goblin_dual`; `prisoner` (Tomé) | 2,0 | Equilibrada |

Falas: Tomé por proximidade no Acampamento ("Aqui! Tirem-me destas cordas!").
Decorações de ar livre (`arvore`, `arvore_grande`, `arvore_seca`) moldam a estrada.

### 2 · Minas de Pedra-Funda — `sombras_2_minas.json`

`ambiente: masmorra` · `expected_party {4,2}` (poder 8) · objetivo `open_key_chest`
(xp 0, reward: 60 ouro).

| Sala | Conteúdo | ND | Faixa |
|---|---|---|---|
| Boca da mina (entrada) | 3 `kobold_lanceiro`, 2 `kobold_besteiro` | 1,25 | Fácil |
| Ponte das estacas | 2 `kobold_besteiro` do outro lado; armadilhas `fosso_estacas` e `buraco` no caminho | ~1,1 | Fácil |
| Galerias fundas | 4 `aranha_sombria`, 1 `cobra_venenosa` | 2,0 | Fácil |
| Depósito | `ogro_clava`, 1 `goblin_dual`, 2 `kobold_lanceiro`; baú `key_objective: true` com 2 `frasco_acido` + 1 `frasco_oleo` | 3,5 | Equilibrada |

Fala: um kobold ferido perto da Ponte ("Cuidado com as estacas… o chefe manda pisar nas
pedras escuras").

### 3a · Covil — Salões de Cima — `sombras_3a_saloes.json`

`ambiente: masmorra` · `expected_party {4,3}` (poder 12) · objetivo `salas_obrigatorias`
(3 salas `required` em modo `clear`) · etapa com `encadear: true`.

| Sala | Conteúdo | ND |
|---|---|---|
| Guarita (obrigatória) | 2 `goblin_dual`, 2 `goblin_arqueiro` | 2,5 |
| Salão de armas (obrigatória) | 2 `orc_guerreiro`, 2 `goblin_combatente` | 2,5 |
| Escadaria (obrigatória) | 1 `orc_guerreiro`, 1 `dark_mage`, 2 `goblin_dual` | 3,5 |

Todas Fácil (0,21–0,29) de propósito: o peso do Covil é não recuperar antes do andar 2.

### 3b · Covil — O Trono de Pedra — `sombras_3b_trono.json`

`ambiente: masmorra` · `expected_party {4,3}` · objetivo `kill_target` (o Troll com
`target: true`; xp 0, reward: 120 ouro) · o `outro_rota` do destino encerra a campanha.

| Sala | Conteúdo | ND | Faixa |
|---|---|---|---|
| Poço antigo (entrada, `role: entrance`) | vazia; decoração `fonte` (água) | 0 | descanso |
| Trono (`role: boss`) | `troll` (`target: true`), 1 `orc_guerreiro`, 2 `goblin_arqueiro`; decorações `fogueira` (braseiros) | 5,5 | Equilibrada |
| Esconderijo (secreto) | `bugbear_sombras`, 2 `aranha_sombria`; baú com o **Anel da Garra Negra** | 2,5 | Fácil no número (luta no escuro) |

**Passagem secreta:** `type: mechanism`, na parede entre o Poço antigo e o Esconderijo,
aberta pela decoração `estante_livros` do Poço. A estante **não** leva `key_objective` (esse
campo só é exigido de decorações que abrem *portas*; numa decoração sem passagem ligada ele
marcaria o objetivo de baú-chave). A estante fica **ao lado** da casa que dá acesso à
passagem — nunca em cima dela, senão a passagem aberta seria inalcançável. O Esconderijo não é `required` nem contém o alvo:
enfrentar o Bugbear é opcional, antes ou depois do Troll (o jogo deixa explorar até alguém
clicar "Encerrar missão").

Fala-pista no Poço, por proximidade: "O vento assobia atrás da estante… como se houvesse
um corredor do outro lado." O Detectar Armadilhas do ladino também revela a passagem.

### Validador de design do editor

Os avisos do validador de design moram no `tools/editor.js` (JavaScript, dependente do
estado do editor), então o teste automático cobre a **conectividade** em Python (toda sala
alcançável a pé da entrada; o Esconderijo só depois de abrir a passagem) e os avisos do
editor são conferidos abrindo cada masmorra nele. As 4 masmorras devem sair sem aviso de conectividade (R4), de descanso antes do chefe no
Trono (R5 — satisfeito pelo Poço antigo, ND 0, vizinho do Trono) e de picos bruscos entre
salas obrigatórias (R3). **Avisos esperados e aceitos:** R2 no Trono (só 2 salas entre a
entrada e o chefe — o andar é a continuação dos Salões, emendado) e R1 (rota alternativa)
em todas, porque masmorras curtas e lineares são intencionais aqui. A conferência final no
editor registra que os avisos emitidos são exatamente esses.

## Itens

- **`frasco_acido` ×2 e `frasco_oleo` ×1** (arremessáveis que já existem) no cofre das Minas.
- **Anel da Garra Negra** — item personalizado novo, `item_type: "ring"`, salvo em
  `itens_personalizados.json` pelo mesmo validador do Editor de Itens
  (`_validate_custom_item`):
  - `bonuses`: `atk_bonus +1`, `vision +1`;
  - `granted_ability: "hero_rogue_esconder_sombras"` (Esconder nas Sombras para qualquer
    classe — Fase I/J do Editor de Itens);
  - disponibilidade: **só baús** (`loja: false`, `baus: true`, `loot: false`), sem
    estoque em cidade nenhuma;
  - preço de referência pelo `suggestPriceAccessory`.

## Cidade

Conversa nova no slot `barman` da cena `taverna` de Alva e Luz (`city_scenes.json`):
id `sombras_caravanas`, texto do gancho, requisito vazio, efeito
`{fato: "sombras_caravanas"}`, `uma_vez: true`. As conversas existentes do Bartender não
são tocadas.

## Gerador — `tools/gerar_campanha_sombras.py`

Rodado da raiz: `python tools/gerar_campanha_sombras.py [--forcar] [--simular]`.

**Escreve:**
- `dungeons/sombras_1_vau.json`, `sombras_2_minas.json`, `sombras_3a_saloes.json`,
  `sombras_3b_trono.json`;
- em `world_adventures.json`: as 3 entradas `sombras_*`;
- em `city_scenes.json`: a conversa `sombras_caravanas` do Bartender;
- em `itens_personalizados.json` (+ índice `tools/editor_items_custom.js`): o anel;
- `tools/editor_dungeons.js` regenerado, para as masmorras aparecerem no editor.

**Regras:**
- **Só toca no que é dele.** Nos arquivos compartilhados, acrescenta ou substitui apenas as
  entradas com ids `sombras_*` / o id do anel; todo o resto é relido e regravado intacto.
- **Não atropela edição manual.** Grava em `tools/.sombras_assinaturas.json` o hash de
  cada masmorra gerada. Se o arquivo em disco não bate com o hash (o autor mexeu no
  editor), recusa sem `--forcar` e diz qual arquivo.
- **Valida antes de gravar, tudo ou nada.** Cada masmorra por `validar_dungeon`, o anel por
  `_validate_custom_item`, os destinos pelo mesmo formato que `_world_adventures_editor`
  aceita. Qualquer falha aborta sem gravar arquivo nenhum.
- **Mapas por código.** Salas retangulares separadas por UMA parede, com a porta entre duas
  salas vizinhas nessa parede (listada nas duas salas; salas começam trancadas, exceto a
  entrada e o Esconderijo, que só se alcança pela passagem); monstros, armadilhas, baús,
  falas e decorações em posições fixas relativas ao canto de cada sala — sem sorteio, então
  a regeneração produz o mesmo mapa.
- **`--simular`** imprime, sem gravar: ND e faixa por sala e a lista de artes pedidas pelos
  slides.

## Testes — `tools/test_campanha_sombras.py`

1. As 4 masmorras passam em `validar_dungeon` e carregam pelo **mesmo caminho do jogo**
   (`handle_world_adventure` → `enter_dungeon`).
2. **Corrente de requisitos:** sem o fato, `sombras_vau` não aparece no
   `city_state.world.adventures`; a conversa do Bartender grava o fato e o libera;
   `sombras_minas` exige `sombras_vau` concluído; `sombras_covil` exige `sombras_minas`.
3. **Objetivos:**
   - Vau: libertar o prisioneiro cumpre;
   - Minas: abrir o baú `key_objective` cumpre;
   - Salões: limpar as 3 salas obrigatórias cumpre; encerrar a missão **emenda** no Trono
     sem recuperar HP (HP antes = HP depois);
   - Trono: matar o Troll cumpre; o Bugbear vivo não impede.
4. **Dificuldade:** ND e faixa de cada sala batem com as tabelas desta spec, calculados com
   `monster_cr`/`trap_cr` e as faixas de `src/difficulty.js`.
5. **Segredo:** interagir com a `estante_livros` abre a passagem; o baú do Esconderijo tem o
   Anel; equipar o Anel concede Esconder nas Sombras a um herói que não é ladino.
6. **Troll:** com ácido aplicado, a regeneração não ocorre no turno seguinte.
7. **Não destrutivo:** rodar o gerador duas vezes produz arquivos idênticos; conversas,
   destinos e itens que não são `sombras_*` saem byte-idênticos; uma masmorra alterada à
   mão faz o gerador recusar sem `--forcar`.
8. **Régua da curva de XP (relatório, não cobrança):** simula os abates planejados com
   4 heróis e imprime o nível ao fim de cada destino, contra a curva-alvo 1 → 2 → 3.

**Verificação dentro do jogo:** jogar o Trono pelo simulador do editor ("Testar como
Mestre") e conferir no navegador: o Troll regenera; o Frasco de Ácido a bloqueia; a estante
abre o Esconderijo; o Bugbear conjura a nuvem de sombras.

## Fora de escopo

- O conserto da curva de XP (subprojeto seguinte).
- Ilustrações dos slides e retratos (o autor sobe pelo editor depois).
- Tradução do conteúdo autoral.
- Cena de conversa nova na cidade (a campanha usa o Bartender que já existe).
- Balanceamento por tamanho de grupo em runtime (o jogo não tem).
