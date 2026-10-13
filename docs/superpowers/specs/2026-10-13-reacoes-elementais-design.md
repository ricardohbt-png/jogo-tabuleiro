# Reações elementais (terreno × elemento) — design

Data: 2026-10-13. Estado: aguardando revisão do autor.

## Objetivo

Hoje água, lava, gelo, fogo, eletricidade e frio agem isolados. O jogador deve poder olhar o mapa e pensar "tem água ali, o mago pode usar raio", e o autor de masmorras deve poder montar armadilhas e puzzles com esses elementos. Valem as mesmas regras para heróis, monstros e armadilhas (um Elemental Elétrico dentro d'água é um perigo real).

Decisões do autor (brainstorming):
- Memória elemental via **tabela de reações** sobre o que já existe (não camada de superfícies nem estados em criaturas).
- Reações da v1: **⚡ água + eletricidade**, **🔥 piche + fogo**, **❄️ água + frio**, **❄️ lava + frio**.
- **Piche** nos dois formatos: terreno pintável no editor e **frasco de piche** (item arremessável), compartilhando o mesmo mecanismo de mancha temporária.
- Lava apagada vira **crosta temporária de 3 rodadas**.
- **Qualquer fonte elementar** dispara reações, com a mesma regra para todos.
- Criatura **em chamas que entra em piche** inflama a mancha.

## Fora de escopo (registrado)

- Água profunda e redemoinho (não conduzem choque nem congelam na v1).
- Fogo + gelo (linha pronta na tabela, desligada) e fogo + gás.
- Destaque de mira das casas que reagirão; lição de tutorial.
- Alterar o frasco de óleo atual (o tutorial depende dele).

## 1. Motor e tabela (servidor)

Mixin novo `terrain_reactions.py` (`TerrainReactions`, herdado por `GameRoom`, mesmo padrão de `monster_intent.py`).

```
async def reagir(self, elemento, casas, origem, profundidade=0)
```
- `elemento`: `DMG_FIRE`, `DMG_COLD` ou `DMG_LIGHTNING`.
- `casas`: casas atingidas pela fonte, inclusive vazias.
- `origem`: `{tipo: magia|item|armadilha|monstro|arma|reacao, id, caster_id, dano, cd, evento}`.

Tabela de reações em dados puros: `{id, elemento, estado_da_casa, efeito, params}`, onde o estado é um predicado sobre o material/terreno da casa (`_water_tile_kind`, `MATERIAIS[...]["terreno"]`).

| Elemento | Casa | Efeito |
|---|---|---|
| lightning | água rasa (`agua`) | choque na poça |
| fire | piche | inflama a mancha |
| cold | água rasa | congela temporariamente |
| cold | lava | crosta temporária |
| fire | gelo (`piso_congelado`/`planicie_nevada`) | derrete — linha presente, **desligada** |

Resolução: casas testadas em ordem fixa (determinística); reações que se espalham usam busca por região conectada com teto; cada reação é aplicada uma vez por evento e por região; reação pode gerar outra (cadeia) até **profundidade 2**.

## 2. Piche

- Material `piche` em `MATERIAIS`: piso escuro, `terreno="piche"`, `custo_mov=1` (mesmo mecanismo do pântano). Aparece no editor pelo catálogo exportado (`export_catalog.py`); nome PT/EN via `gerar_vocabulario.py`.
- **Frasco de piche:** arremessável, mira em casa, área 3×3, sem dano e sem teste; pinta piche temporário por **4 rodadas** pelo registro de camadas do Chamado do Inverno (`_aplicar_camadas_terreno_inverno` / `_expirar_terrenos_inverno`), que restaura o material original. Vai ao mercador e ao catálogo de arremessáveis. O frasco de óleo não muda.
- **Fogo no piche:** qualquer fonte de fogo numa casa de piche inflama toda a mancha conectada (teto **40 casas**) e cria uma zona nova `chamas_piche` com a **lista de casas** (a zona da Bola de Fogo é só quadrada), duração 3 rodadas; só no piso (voadores não são atingidos). Ao acabar, o piche é consumido: mancha temporária volta ao material original; piche autoral vira `pedra_negra`.
- **Gancho:** criatura com `em_chamas_rodadas > 0` que termina um passo em casa de piche inflama a mancha (ponto onde o movimento já aplica lava/fogueira).

## 3. Números e regras

| Reação | Quem sofre | Efeito |
|---|---|---|
| Choque na poça | todos na água conectada à atingida, aliados incluídos | dano elétrico = **metade do dano da fonte** (mín. 1), Reflexos para metade (CD da fonte, ou 12); quem já tomou o golpe original não toma o choque; passa pelo funil de dano (resistências/vulnerabilidades e cores) |
| Chamas de piche | quem entra ou está na mancha, só no piso | 1d6 de fogo ao entrar e no início do turno + status "em chamas" |
| Água congelada | quem está em água rasa na área do frio | vira `piso_congelado` por 3 rodadas; Reflexos (CD da fonte, ou 12): falha → imobilizado por 1 rodada |
| Lava solidificada | ninguém sofre dano | lava → material novo `lava_solidificada` (transitável) por 3 rodadas |

Regras comuns: poça = região de água rasa conectada, teto **24 casas**, raio 6 do impacto; quando a crosta acaba, quem estiver sobre ela sofre o dano normal de lava no início do próximo turno; fontes sem dano rolado (armadilha, monstro) usam o dano efetivamente aplicado ao alvo principal como base do choque.

**Risco a conferir antes do plano:** como a Ira da Rocha Ardente representa sua lava (zona vs material). Se não for material, a v1 apaga só a lava pintada no editor.

## 4. Pontos de ligação das fontes

Três camadas:
1. **Funis de dano** (`_aplicar_dano_alvo`, `_dano_em_alvo`): com `elemento` fogo/frio/eletricidade, chamam `reagir` com as casas da criatura atingida, após aplicar o dano.
2. **Fontes de casa**, sem criatura: Bola de Fogo, Prisão de Chamas, Ira da Rocha, Tempestade, Relâmpago, Raio Congelante, `_throw_item_area`, armadilha incendiária — chamada explícita com as casas da área.
3. **Ataques fora dos funis:** armas com dano elemental (`extra_damages`, flecha incendiária) e ataques de monstros com tipo elemental (raio do Elemental Elétrico).

Travas: **um evento, uma reação** (id de evento = `animation_id`/`attack_id`, senão contador; o motor ignora a mesma reação na mesma região para o mesmo evento); dano de reação passa pelo funil com `origem.tipo = "reacao"` e **não reentra** no motor (cadeias só pelas regras explícitas, até profundidade 2).

## 5. Feedback ao jogador (cliente)

- Aparência (2D e 3D, paleta do cliente): `piche` preto brilhante com bolhas lentas; `lava_solidificada` com crosta e fissuras alaranjadas que apagam; `piso_congelado` reaproveitado.
- Mensagem pública `reacao_elemental {tipo, casas, origem}` (molde de `armadilha_disparo`); o cliente anima só casas visíveis: raios em zigue-zague (choque), labaredas (incêndio, reutilizando as chamas vivas), geada (congelar), lava escurecendo e rachando (crosta). Sons reaproveitam `relampago`, `incendio` e o do gelo via `sfx()` (recua à síntese).
- Narração com uma linha por reação (chaves PT/EN) e tooltip de casa por material ("Piche: inflamável, +1 de movimento", "Água: conduz eletricidade", "Lava solidificada: volta em N rodadas").
- **Aviso da crosta:** com 1 rodada para acabar, a casa pulsa em laranja e o log avisa.

## 6. Testes e critério de pronto

`tools/test_terrain_reactions.py`: tabela exercitada linha a linha; choque (região, teto 24/raio 6, dano ½, Reflexos, aliados, sem dupla aplicação); piche (custo de movimento, frasco 3×3/4 rodadas e restauração, incêndio da mancha com teto 40, zona 3 rodadas 1d6 + em chamas, voadores imunes, destino autoral × temporário, gancho da criatura em chamas); frio (água rasa 3 rodadas, Reflexos/imobilização, lava→crosta 3 rodadas, dano de lava na volta); travas (dedupe por evento, reação não reentra, profundidade 2); **uma fonte por teste** para cada fonte elementar listada na seção 4; sem consumo de RNG fora da reação; persistência dos novos campos (categoria em `FOTO_SALA_CATEGORIAS`, `test_salvar_masmorra`).

`tools/test_reacoes_cliente.js`: `reacao_elemental` só anima casas visíveis; tooltip por material; aviso da crosta; chaves PT/EN e `dividas.py` limpo.

Editor: `piche` na paleta de materiais, salva e relê sem perda; `test_editor_idioma` e a sincronia do catálogo continuam verdes.

Prova no navegador em servidor isolado, **depois da última correção**: raio em poça, fogo em piche com e sem criatura, frio em água e em lava; medir FPS.

Critério de pronto: testes novos verdes, `dividas.py`/`test_interface` sem piora, `test_protocolo_robustez` verde, prova sem erros no console e tabela de fontes completa.
