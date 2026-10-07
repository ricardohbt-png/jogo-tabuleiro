# Ícones de magia que faltam — prompts para gerar

13 magias do `GRIMORIO` não têm `assets/magias/<id>.png`; o jogo mostra o emoji no lugar
(e o console registra um erro de arquivo não encontrado). Os prompts abaixo seguem o estilo dos
27 ícones que já existem.

## Como usar

1. Num gerador de imagem (Firefly, Midjourney, ChatGPT, etc.), cole o **estilo comum** seguido da
   **cena** da magia. Peça formato quadrado (1:1).
2. Salve cada imagem numa pasta com o **id** da magia como nome: `voo.png`, `teleporte.jpg`… (png,
   jpg ou webp).
3. Na raiz do projeto:

   ```bash
   python tools/importar_icones_magia.py <pasta>
   ```

   O script recorta o quadrado central, reduz para 256×256, grava em `assets/magias/<id>.png` e
   lista o que ainda falta. Ícone existente só é substituído com `--substituir`.

## Estilo comum (cole antes de cada cena)

> Fantasy RPG spell icon, square 1:1, digital painting. A circular medallion centered on a pure
> black background: a thick dark bronze ring engraved with small glowing runes, with four small
> four-pointed star gems at the top, bottom, left and right of the ring, the gems colored like the
> spell. Inside the circle, a dramatic glowing scene in one dominant color with deep shadows,
> high contrast, painterly detail, small faint magical sigils floating around the main figure. No
> text, no letters, no border outside the medallion.

## Cenas (uma por magia)

| id | Magia | Cor dominante / joias |
|---|---|---|
| `voo` | Voo | azul-celeste e branco |
| `maldicao_corpo_pesado` | Maldição do Corpo Pesado | violeta |
| `vinculo_maldito_da_dor` | Vínculo Maldito da Dor | carmim e violeta |
| `chamado_inverno` | Chamado do Inverno | azul-gelo e branco |
| `desnutricao` | Desnutrição | verde-amarelado doentio |
| `definhar` | Definhar | verde-acinzentado doentio |
| `senhor_das_aguas` | Senhor das Águas | azul profundo e turquesa |
| `ira_rocha_ardente` | Ira da Rocha Ardente | laranja e vermelho (lava) |
| `tempestade_ciclones` | Tempestade de Ciclones | cinza-azulado com raios brancos |
| `teleporte` | Teleporte | violeta e azul arcano |
| `prisao_chamas` | Prisão de Chamas | laranja (fogo) |
| `olhar_petrificante` | Olhar Petrificante | cinza-pedra com olhos verde-esmeralda |
| `metamorfose` | Metamorfose | violeta e verde |

**`voo`** — Spell color: sky blue and white, sky-blue gems. Scene: a hooded adventurer lifted off
the ground by spiraling gusts of luminous wind, translucent wings of air unfolding from the
shoulders, small clouds and feathers of light swirling below the feet.

**`maldicao_corpo_pesado`** — Spell color: violet, purple gems. Scene: a cursed figure bent
forward under invisible weight, glowing violet chains hanging an iron anvil from the back, an empty
bowl and a dried, empty waterskin at the feet, a faint curse sigil above the head.

**`vinculo_maldito_da_dor`** — Spell color: crimson and violet, crimson gems. Scene: two silhouettes
facing each other, a robed caster and a monstrous enemy, joined chest to chest by a thorned chain of
crimson light; a crack of pain runs along the chain from the caster toward the enemy, who recoils.

**`chamado_inverno`** — Spell color: ice blue and white, ice-blue gems. Scene: a cleric raising a
staff as a blizzard pours down, the ground in front freezing into a square of cracked ice and deep
snow, snowflakes and frost runes spiraling around the staff.

**`desnutricao`** — Spell color: sickly yellow-green, olive gems. Scene: a gaunt, starving figure
with visible ribs clutching the stomach, a sickly green mist being drawn out of the body, a moldy
loaf of bread crumbling to dust beside them.

**`definhar`** — Spell color: sickly gray-green, olive gems. Scene: a wave of withering energy
spreading in a square over the ground, grass and crops wilting and turning to ash, several small
figures doubled over in hunger and thirst, a dried-up well in the background.

**`senhor_das_aguas`** — Spell color: deep blue and turquoise, turquoise gems. Scene: a cleric with
arms raised commanding water that floods the ground around them, two swirling whirlpools opening in
the water, waves curling upward like hands.

**`ira_rocha_ardente`** — Spell color: orange and red, orange gems. Scene: the ground split open into
a square pool of glowing lava, molten rock erupting upward, several living flames with tiny burning
eyes rising from the lava, ember sparks everywhere.

**`tempestade_ciclones`** — Spell color: storm gray-blue with white lightning, pale blue gems.
Scene: several small tornadoes spinning across a stormy field, a dark cloud above throwing lightning
bolts down between them, a flying creature being knocked out of the air by the wind.

**`teleporte`** — Spell color: violet and arcane blue, violet gems. Scene: a robed mage dissolving
into sparkling motes inside one glowing rune circle on the left and reappearing from motes inside a
second rune circle on the right, a thin arc of light connecting the two circles.

**`prisao_chamas`** — Spell color: orange fire, orange gems. Scene: a square cage made of four walls
of roaring flame seen at an angle, a trapped monster crouching inside, heat haze rising, the floor
inside the square untouched while the borders burn.

**`olhar_petrificante`** — Spell color: stone gray with glowing emerald green, emerald gems. Scene: a
pair of large glowing emerald eyes in the upper half staring down at a warrior below, the warrior's
legs and lower body already turned to cracked gray stone, the stone creeping upward.

**`metamorfose`** — Spell color: violet and green, violet gems. Scene: a figure caught in the middle
of a transformation into a wolf, the human half on the left and the beast half on the right, arcane
violet and green energy spiraling around the body, faint silhouettes of other creatures in the swirl.
