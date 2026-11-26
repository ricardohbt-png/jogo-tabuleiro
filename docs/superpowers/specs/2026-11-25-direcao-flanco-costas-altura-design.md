# Direção, flanco, costas e altura — design

## Intenção
Fazer o posicionamento importar, como no FFT: atacar pelas costas, pelo flanco ou de
cima dá vantagem, e o jogador escolhe para onde o herói olha ao encerrar o turno. O
Ataque Furtivo do Ladino passa a depender da direção. A regra é **simétrica**: monstros
também têm direção e também ganham os bônus contra os heróis (decisão do autor).

## Objetivos
- Direção autoritativa, cardinal, para heróis e monstros; regra única de setores.
- Bônus de acerto por costas, flanco e altura, aplicados em todo ataque com jogada de
  acerto (herói e monstro), inclusive na prévia de chance.
- Ataque Furtivo: base = oculto OU costas; nível II acrescenta flanco (e mantém o aliado
  adjacente); nível III (reação) não muda.
- Escolha da direção ao encerrar o turno, por bússola; direção visível no peão.
- Explicação ao jogador: marca de frente no peão, tooltip "Costas +2 / Flanco +1 / Altura +N".

## Não-objetivos
- IA de monstro que busca flanco ou evita ficar de costas (fica para depois).
- Ataque de oportunidade, bônus de dano ou crítico por posição, penalidade por atacar de baixo.
- Magias e saves (só jogadas de ataque); voo não conta como altura.
- Escolha de direção para servos, refém ou animais.

## Regras (decididas com o autor)
**Setores.** Seja `rel` = atacante − alvo (centros dos footprints; 1×1 = a própria casa) e
`f` a direção do alvo. `dot = rel·f`, `cruz = |rel×f|`.
- **costas**: `dot < 0` e `|dot| >= cruz` · **flanco**: `cruz > |dot|` · **frente**: o resto.
- Adjacente 1×1 dá 3 casas de costas, 2 de flanco e 3 de frente. Vale à distância pelo ângulo.

**Bônus de acerto do atacante:** costas +2, flanco +1, altura +1 por nível de terreno acima
do alvo (máx. +2). Soma limitada a +4. Voo e altura de magia não contam; sem penalidade
por estar abaixo. Soma-se à meia cobertura já existente sem interferir nela.

**Alvo incapaz** (dormindo, paralisado, petrificado, preso por rede/teia, monstro ainda
dormente/não alertado) conta como **costas** para o atacante. *(Decisão do desenho; fácil de remover.)*

**Direção padrão.** Herói sem direção (entrada na masmorra) e monstro não orientado sem
direção: `[0,1]` (sul). Monstro orientado mantém `[-1,0]` (regra de footprint existente).

**Quem altera a direção.** Passo: direção do passo. Atacar: `_face_toward` (já existe, em
heróis e monstros). **Fim de turno do herói: escolha do jogador (nova).** Monstro: termina
voltado para quem atacou, pelo mesmo `_face_toward`. Ser atingido não vira o alvo.

**Ataque Furtivo** (`_verificar_ataque_furtivo`, ponto único de decisão):
- nível base: oculto/oculto_vela **ou** atacante pelas costas do alvo;
- `ladino_furtivo_2`: acrescenta atacante pelo flanco; mantém "aliado adjacente ao alvo";
- `ladino_furtivo_3` (reação): inalterado. `defesa_impecavel` continua imunizando.
- Descrição do nível II passa a citar flanco; textos PT/EN.

## Abordagens consideradas
1. **Escolha da direção.** (a) `end_turn` carrega `facing` opcional, a bússola aparece no cliente
   antes de enviar. (b) Fase nova no servidor que espera a escolha. **Escolhida: (a)** — sem
   estado novo nem espera no servidor (a iniciativa já travou por esse tipo de espera); cliente
   antigo, auto-encerrar e timeout continuam válidos e mantêm a direção atual.
2. **Onde aplicar o bônus.** (a) Subtrair da CA do alvo nos pontos que já aplicam cobertura.
   (b) Somar ao bônus de ataque. **Escolhida: (b)** em `_modificadores_ataque_heroi` e no
   executor de ataque de monstro (a prévia herda); arremesso e reações que já chamam
   `_cobertura_baixa_bonus` ganham a mesma chamada.
3. **Cliente.** (a) Só mostrar o resultado do servidor. (b) Espelho puro em `gameState.js` com
   teste de paridade (padrão do projeto). **Escolhida: (b)**, para o tooltip e a bússola
   mostrarem as zonas sem ir ao servidor.

## Escopo de construção
Servidor (`server.py`): `_setor_ataque(atacante, alvo)`, `_bonus_posicional`, hooks de ataque,
`_verificar_ataque_furtivo`, `handle_end_turn` aceitando `facing`. Cliente: espelho em
`gameState.js`; bússola e marca de frente no peão (2D e 3D); tooltip. Textos em `src/lang/`.
Ajuda/tutorial: uma linha na ajuda; lição própria fica para depois.

## Validação do `facing` no `end_turn`
Aceita só `[±1,0]`/`[0,±1]`; aplicada **depois** das recusas existentes (escolha de magia
pendente, não é a vez, tempestade pendente) e uma vez por turno; ausente ou inválido = mantém.

## Testes
Servidor: tabela dos 3/2/3 setores nas 4 direções, footprint 2×2, altura (+1/+2/teto), soma e
teto de +4, alvo incapaz, furtivo nos níveis base/II/III, ataque de monstro simétrico,
`end_turn` com e sem `facing`, `facing` inválido. Cliente: paridade do classificador contra o
servidor, bússola (escolher, cancelar, confirmar, teclado).

## Riscos
- Equilíbrio: bônus simétricos mudam a letalidade; por isso o teto de +4 e nenhum bônus de dano.
- Monstros sem direção prévia: o padrão sul pode dar costas "de graça"; mitigado porque quem
  ataca/anda já se vira.
- Alvo incapaz = costas pode favorecer demais o Ladino; é uma decisão isolada num ponto.

## Deixado ao construtor
Valores visuais da marca de frente, textos exatos, atalhos além de setas/WASD/Enter/Esc.
