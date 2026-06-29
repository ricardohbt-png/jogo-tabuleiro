# Iluminação por ambiente no 3D — Design

**Data:** 2026-06-29
**Branch:** feat/miniatura-png-objetos (ou nova branch)
**Status:** aprovado para planejamento

## Problema

As masmorras no modo 3D estão muito escuras; as imagens (peões, objetos PNG,
decorações) ficam difíceis de ver. O usuário quer:

1. Deixar o 3D **bem claro e iluminado**, com contraste forte, **mantendo a
   névoa de guerra** (tiles não explorados continuam pretos).
2. Poder escolher, **por mapa no editor**, um ambiente **ainda mais claro** para
   mapas ao ar livre.

Escopo: **somente o 3D da masmorra** (`init3D`). Não tocar no 2D, nem no 3D da
cidade, nem em nenhuma lógica de fog of war / revelação / combate. Mudança é
puramente visual.

## Solução: presets de iluminação por ambiente

Cada mapa ganha um campo `ambiente` que seleciona um preset de iluminação no
cliente. Três presets, do mais escuro ao mais claro:

`penumbra` < `masmorra` (padrão) < `ar_livre`

A névoa de guerra é idêntica nos três (não-explorado = mesh `visible=false` →
fundo escuro). O preset só altera luz, fog atmosférico e exposição dos tiles
**já explorados**.

## Modelo de dados

Novo campo opcional no topo do JSON da masmorra (`schema_version: 1`):

```json
"ambiente": "masmorra"   // "penumbra" | "masmorra" | "ar_livre"
```

- Ausente ou inválido → `"masmorra"` (mapas antigos e procedurais não mudam).

## Componentes e mudanças

### 1. `src/visualConfig.js` — fonte única de verdade

Adicionar `VC.ambientes` com os três presets. Cada preset contém tudo que o
`init3D` precisa: `bgColor`, `fog {color, density}`, `exposure`, e as cinco luzes
(`ambient`, `dirMain`, `dirFill`, `rimLight`, `dirPawn`), cada uma com
`color`/`intensity` e (para as direcionais) `pos`.

`VC.lighting` e `VC.scene` passam a ser **aliases** de `VC.ambientes.masmorra`
(retrocompat — hoje só o `init3D` os referencia; nada mais quebra).

Valores propostos (afináveis depois numa rodada de ver-no-jogo):

| Parâmetro            | penumbra | masmorra | ar_livre |
|----------------------|----------|----------|----------|
| ambient.intensity    | 0.55     | 1.05     | 1.55     |
| dirMain.intensity    | 1.50     | 2.10     | 2.70     |
| dirFill.intensity    | 0.50     | 0.90     | 1.10     |
| rimLight.intensity   | 0.28     | 0.35     | 0.40     |
| dirPawn.intensity    | 0.90     | 1.15     | 1.30     |
| fog.density          | 0.014    | 0.006    | 0.003    |
| exposure             | 1.30     | 1.55     | 1.65     |

Cores: `masmorra`/`penumbra` mantêm o tom quente atual (ambient `0xfff5e0`,
dirMain `0xfffaf0`, fill `0xe8f0ff`, rim `0xffe0b0`, pawn `0xfff0d8`); `ar_livre`
usa luz de dia mais neutra (ambient `0xfff6ea`, dirMain `0xffffff` (sol), fill
`0xdfeaff` (céu), pawn `0xfff8ee`). Posições das direcionais iguais às atuais.
`bgColor`/`fog.color` permanecem **escuros** nos três (preserva o preto do
não-explorado): penumbra `0x141016`, masmorra `0x1c1810`, ar_livre `0x141414`.

### 2. `server.py`

- `load_authored_dungeon(defn)`: `self.ambiente = defn.get("ambiente", "masmorra")`
  (normaliza valor desconhecido para `"masmorra"`).
- Inicialização procedural / reset: `self.ambiente = "masmorra"`.
- `push_state`: incluir `"ambiente": getattr(self, "ambiente", "masmorra")`.
- `validar_dungeon`: aceitar `ambiente` opcional; se presente e fora do conjunto,
  normalizar para `"masmorra"` (não falhar a validação).

### 3. `game.js` — `init3D`

- Resolver o preset: `const amb = VC.ambientes[state.ambiente] || VC.ambientes.masmorra;`
- Aplicar `scene.background`, `scene.fog` (FogExp2), `renderer.toneMappingExposure`
  e as cinco luzes a partir de `amb` (substitui as leituras hardcoded de
  `VC.scene`/`VC.lighting` e o `toneMappingExposure = 1.35` fixo).

### 4. Editor (`tools/editor.html` + `tools/editor.js`)

- `editor.html`: dropdown ao lado de "nome":
  `<label>ambiente <select id="m-ambiente">` com opções Masmorra / Penumbra /
  Ar livre.
- `editor.js`:
  - `S.meta.ambiente` (default `"masmorra"`).
  - `buildJSON` (linha ~724): emitir `ambiente: S.meta.ambiente`.
  - `loadDungeon` (linha ~823): `ambiente: obj.ambiente || "masmorra"`.
  - Sync da UI: setar o `<select>` ao carregar; ler no change/salvar (junto de
    `m-id`/`m-name`, linhas ~848 e ~878).

## Fluxo de dados

Editor (dropdown) → JSON `ambiente` → `carregar_dungeon` →
`load_authored_dungeon` → `self.ambiente` → `push_state` `game_state.ambiente` →
`init3D` escolhe `VC.ambientes[ambiente]` → luz/fog/exposição aplicadas.

## Fora de escopo (YAGNI)

- Iluminação dinâmica dia/noite na masmorra.
- Ambiente por sala (é por mapa).
- Mudar raio de visão / revelar mais cedo no ar livre (névoa fica igual).
- Texturas de chão/parede específicas de ar livre (grama etc.) — outra feature.

## Verificação

- Mapa sem `ambiente` (ex.: procedural e dungeons antigas) → idêntico ao preset
  `masmorra` (mais claro que hoje, conforme Abordagem A aprovada).
- Editar um mapa, escolher "Ar livre", salvar, jogar → 3D visivelmente mais claro;
  não-explorado continua preto.
- "Penumbra" → mais escuro/sombrio que masmorra.
- 2D e cidade inalterados.
