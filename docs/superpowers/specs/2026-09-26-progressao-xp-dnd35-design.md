# Progressão de XP no modelo D&D 3.5 — design

**Data:** 2026-09-26
**Status:** aprovado em brainstorming
**Motivo:** a curva atual dispara. A campanha "Sombras sob Alva e Luz", desenhada para os
níveis 1→2→3, leva o grupo do nível 1 ao 38 (`tools/test_campanha_sombras.py`, seção [7]).

## Diagnóstico

- Prêmio por monstro (`_calc_monster_xp`): `150 × nível_médio × 2^(ND−1) ÷ vivos`.
- Custo de subir (`_check_level_up`): `nível × 30`, e o XP zera a cada nível.

O prêmio cresce com o nível do grupo e o custo cresce devagar, então quanto mais alto, mais
rápido se sobe. Além disso, a escala é dezenas de vezes mais generosa que a do D&D.
`_check_level_up` sobe no máximo 1 nível por concessão, mesmo quando o XP cobriria vários.

## Decisões (brainstorming)

| Tema | Escolha |
|---|---|
| Modelo | 3.5: o prêmio depende do ND do desafio e do nível de quem recebe |
| Ritmo | 3.5 fiel: limiares originais, cerca de 13 encontros de mesmo ND por nível |
| Teto | nível 20 |
| Nível usado | o nível **próprio** de cada herói (quem está atrás alcança os outros sozinho) |
| Queda | a do 3.5: o monstro fraco perde valor devagar e zera 8 NDs abaixo |
| Campanha Sombras | recalibrada nesta mesma entrega, via XP nos objetivos principais |

## 1. Regras — funções puras (module-level em `server.py`, ao lado de `monster_cr`/`trap_cr`)

```
XP_NIVEL_MAX = 20

xp_premio(nivel, nd) -> int      # prêmio TOTAL do desafio para um herói daquele nível
    L = clamp(nivel, 1, XP_NIVEL_MAX)
    nd <= 0            -> 0
    nd < 1             -> round(nd × xp_premio(L, 1))        # ND fracionário: fração do ND 1
    nd <= L − 8        -> 0                                   # fácil demais
    nd >  L + 7        -> usa nd = L + 7                      # teto da tabela
    senão              -> round(300 × L × 2^((nd − L) / 2))

xp_limiar(n) -> int              # XP ACUMULADO exigido para estar no nível n
    500 × n × (n − 1)            # 0, 1000, 3000, 6000, 10000 … 190000 (n=20)

nivel_por_xp(xp) -> int          # maior n ≤ XP_NIVEL_MAX com xp_limiar(n) ≤ xp
```

Cada herói vivo recebe `xp_premio(seu nível, ND) // nº de heróis vivos`, com mínimo 1 quando
o prêmio é positivo. Um ND 3 vale 3× um ND 1 para um herói de nível 1, e um ND 5 vale 6×.

A fórmula gera a tabela 2-6 do DMG 3.5 de forma aproximada. A irregularidade dos níveis 1–3
do livro não é reproduzida.

## 2. XP acumulado e porta única de concessão

- `p["xp"]` passa a ser o **total acumulado**, como no 3.5; nunca é subtraído. O nível é
  consequência: `nivel_por_xp(p["xp"])`.
- `_conceder_xp(p, qtd)` (async) é a única porta: soma `qtd` e chama `_subir_um_nivel(p)`
  enquanto `p["level"] < nivel_por_xp(p["xp"])`. Um chefe grande pode render vários níveis
  de uma vez.
- `_subir_um_nivel(p)` é o corpo atual de `_check_level_up`, sem a comparação e sem o
  `p["xp"] -= threshold`. Ganhos por nível ficam iguais: PV, ataque, saves, fome/sede, slots
  e magia nova.
- `_check_level_up` é removido. Os 5 pontos que faziam `p["xp"] += …` passam por
  `_conceder_xp`:
  1. **Monstro** (`_monster_dies`): prêmio por herói com o nível dele. O ND vem sempre de
     `monster_cr(m)`, então os 6 legados e as fichas do editor usam a mesma regra. O campo
     `xp` fixo da ficha deixa de valer para a recompensa; o editor continua aceitando-o.
     `_calc_monster_xp` e `_avg_level` saem, se não tiverem outro leitor.
  2. **Armadilha** (`_conceder_xp_armadilha`): `xp_premio(nível, trap_cr(meta))` por herói,
     dividido pelos vivos. `trap_xp`/`TRAP_XP_POR_CR` saem, se não tiverem outro leitor. A
     narração passa a informar o XP do herói que a recebe, ou uma frase sem número se os
     valores diferirem entre heróis.
  3. **Objetivos** (`_conceder_objetivo_reward`): o XP escrito pelo autor continua sendo um
     total absoluto dividido pelos vivos. Os valores atuais (50–500) já estão na escala 3.5.
  4. **Herói "experiente"** (entrada aprovada na campanha): em vez do laço que forjava XP,
     recebe `_conceder_xp(fresh, xp_limiar(alvo))`.
- No nível 20 o XP continua acumulando e nada mais sobe.

## 3. Saves antigos

- `_DURABLE_FIELDS` ganha `xp_modelo`. `make_player` nasce com `xp_modelo: 2`.
- Em `restore_character`, uma ficha **sem** `xp_modelo` é convertida mantendo o nível e a
  fração de progresso:
  `xp = xp_limiar(L) + round(min(1, xp_antigo / (L × 30)) × (xp_limiar(L+1) − xp_limiar(L)))`,
  com `xp_modelo = 2`. No nível 20 a fração é ignorada.
- Ninguém perde nível nem progresso. O nível salvo é preservado mesmo acima do que o XP
  convertido justificaria (fichas infladas pela curva antiga continuam no nível que têm).

## 4. Cliente

- O servidor anexa a cada jogador do `game_state`/`city_state` o `xp_nivel`
  (`xp_limiar(level)`, início da barra) e o `xp_proximo` (`xp_limiar(level+1)`, ou `null` no
  nível 20). O cliente não duplica a tabela.
- A ficha (`game.js`, ao lado de `ui.ficha.experiencia`) mostra "4.500 / 6.000 XP" com uma
  barra fina, ou só o total no nível máximo. Textos novos entram em `src/lang/interface.js`
  (pt/en).
- O painel do mestre e a ficha do monstro deixam de mostrar o `xp` fixo, que não tem mais
  significado, e continuam mostrando o ND.

## 5. Campanha Sombras — recalibração

Com o 3.5 fiel, só os monstros deixam o grupo por volta do nível 1–2 ao fim da campanha. A
meta de ritmo é ao fim de cada destino (grupo de 4, todos vivos):

| Ao encerrar | Nível alvo | XP acumulado mínimo |
|---|---|---|
| Vau | 2 | 1000 |
| Minas | 3 | 3000 |
| Covil (Salões + Trono) | 4 | 6000 |

- O gerador (`tools/gerar_campanha_sombras.py`) passa a pôr XP no objetivo principal de cada
  masmorra. Esse XP cobre a diferença entre a meta e o que os monstros rendem num percurso
  completo sem o chefe secreto, arredondada para cima em múltiplos de 100.
- O cálculo usa as próprias `xp_premio`/`xp_limiar` importadas do `server`, não uma cópia.
- A seção [7] de `tools/test_campanha_sombras.py` deixa de ser só relatório e passa a
  **cobrar** a tabela acima. Ela simula a sequência com as funções reais: monstros
  obrigatórios, depois o objetivo, e o nível resultante de cada etapa como entrada da próxima.
- Depois, o gerador é reexecutado e o conteúdo commitado. As masmorras mudam, então as
  assinaturas em `tools/.sombras_assinaturas.json` são regravadas pelo próprio gerador.

## 6. Testes

- `tools/test_xp_progressao.py` (novo):
  - `xp_premio`: pontos da tabela (nível 1 × ND 1 = 300; ND = nível → 300 × nível), ND
    fracionário, zero 8 NDs abaixo e o teto em nível + 7;
  - `xp_limiar`/`nivel_por_xp`: limites exatos, incluindo o nível 20;
  - vários níveis de uma vez;
  - nível próprio: dois heróis de níveis diferentes recebendo valores diferentes pelo mesmo
    monstro;
  - armadilha e objetivo passando por `_conceder_xp`;
  - migração de save (nível 2 com 30/60 vira 2000; ficha já marcada fica intacta);
  - `xp_proximo` no payload.
- Suítes que mexem com XP e nível precisam continuar verdes; onde cravarem os números
  antigos, o número é atualizado, não a regra. Entre elas: `test_modo_mestre` (XP de
  armadilha), `test_campanha_sombras`, `test_tutorial`, `test_masmorra_sequenciada`,
  `test_jogos_salvos*`/campanha e as de especialização que forçam nível. A lista final vem de
  um `grep` por `"xp"`/`level` nos testes.
- `tools/dividas.py` sem pendências.

## Fora de escopo

- Tabela literal do DMG (é aproximada pela fórmula).
- XP por encontro (grupo de monstros) em vez de por monstro.
- Mudar o que cada nível dá ao herói.
- Revisar o XP autoral das outras masmorras.
