# Peão GLB 3D do Richard (paladino) — Design

## Contexto

Em 2026-06-13 o GLB 3D dos peões foi desativado a pedido ("ficou ruim") e
substituído por billboards 2D (`frente.png`) — ver comentário em
`game.js:14419`. Os arquivos `.glb` de todas as 6 classes continuam em
`assets/models3d/`, mas `_makeCharacterPawn3D`/`_loadHeroGLB` viraram código
morto (nunca chamados). O usuário modelou um novo GLB do Richard (paladino),
fora do pipeline antigo, e quer reativar o peão 3D real **só para essa
classe**, mantendo os outros 5 heróis em billboard 2D até terem modelos
novos.

## Escopo

Só o peão dentro da masmorra em modo 3D (`_makeCharacterPawn`, chamado pelo
construtor de figura 3D da masmorra). A tela de seleção de personagem
(`_cHeroPNG`) permanece 2D — fora de escopo.

## Mudanças

**Arquivo do modelo:** `Downloads/richard.glb` substitui
`assets/models3d/paladin.glb` (convenção existente é por `classId`, não por
nome de personagem — Richard = paladino).

**`game.js`:**

1. `const _GLB_ENABLED_CLASSES = new Set(['paladin'])` — lista de classes que
   usam peão GLB real em vez de billboard. Adicionar uma classe no futuro é
   só incluir o id aqui.
2. `_makeCharacterPawn3D` ganha um parâmetro opcional `onMissing` (callback).
   Hoje, se o GLB falhar ao carregar (`cached === 'erro'` ou erro assíncrono
   do `GLTFLoader`), a função não desenha nada — peão fica invisível. Com
   `onMissing`, esse caso passa a acionar um fallback.
3. `_makeCharacterPawn` passa a checar `_GLB_ENABLED_CLASSES`:
   - Se `classId` estiver na lista: chama `_makeCharacterPawn3D(...)`
     passando o billboard 2D (`_makeBillboardSprite` com o mesmo
     `frente.png`) como `onMissing`.
   - Senão: comportamento atual — billboard direto, sem tentar GLB.
4. Escala/altura: reaproveita `_BB_H_ALVO = 2.05` (mesma altura-alvo dos
   billboards) para o GLB ficar consistente em tamanho com os outros peões
   na mesa (a lógica de escala por bounding box já existe em
   `_makeCharacterPawn3D`, só precisa receber essa altura).
5. Rotação (`rotY`): começa em `0`. Este parâmetro nunca teve um call site
   ativo no histórico deste repo (código morto desde o commit baseline), não
   há valor de referência — vai precisar de ajuste visual depois de ver o
   modelo renderizado.

## Fallback / robustez

Se o `paladin.glb` novo tiver qualquer problema (arquivo corrompido, erro de
parse, 404), o Richard cai automaticamente no billboard 2D — nunca fica sem
peão visível. Isso corrige de quebra uma lacuna do código morto original
(`onMissing` ausente = peão invisível em caso de erro).

## Teste manual

1. Subir o servidor, entrar na masmorra como Richard (paladino).
2. Alternar para o modo 3D e conferir: escala, proporção, orientação
   (frente/costas) do peão na tile.
3. Forçar erro de carga (ex. renomear temporariamente `paladin.glb`) e
   confirmar que cai no billboard 2D sem quebrar o render.
4. Confirmar que as outras 5 classes continuam usando billboard normalmente
   (nenhuma regressão).

## Fora de escopo

- Tela de seleção de personagem (`_cHeroPNG`) — continua 2D.
- Modelos GLB novos para as outras 5 classes.
- Reativar preload de GLB (removido deliberadamente antes — "era trabalho
  inútil").
