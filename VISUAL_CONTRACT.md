# LEGENDS FOR HIRE — Contrato Visual
## LEIA ESTE ARQUIVO ANTES DE QUALQUER ALTERAÇÃO VISUAL

### Iluminação
- AmbientLight: intensidade 0.7, cor #fff5e0
- DirectionalLight principal: intensidade 1.8, cor #fffaf0
- DirectionalLight preenchimento: intensidade 0.6, cor #e8f0ff
- Fog máximo: FogExp2 density 0.02

### Chão
- Cor base tiles: #888888
- Rejunte: #444444
- emissive: #222222

### Paredes
- Cor base: #5a5a6a
- emissive: #111120
- Rejunte: #2a2a3a

### Dados
- Material: MeshLambertMaterial (emissive garante cor independente da iluminação da cena)
- emissiveIntensity: 0.4
- D4: #FFE000 | D6: #FF1111 | D8: #0055FF
- D10: #00DD44 | D12: #CC00FF | D20: #FF5500
- Números: preto #000000 com stroke branco #FFFFFF 12px, fonte Arial Black 140px
- D20 (faces triangulares): fontSize 90px (1 dígito) e 68px (2 dígitos), centralizado em y=155, canvas clipado ao triângulo [[128,20],[236,210],[20,210]]
- Escala: 1.30× (30% maior que a geometria base)
- Iluminação exclusiva: PointLight principal intensidade 3.0 dist 3.0 (acima y+2) + fill 1.5 dist 2.0 (abaixo y-1), ambas dentro do diceGroup

### Peões
- emissive: 10% da cor principal de cada herói
- Base: #111111 com borda emissive
- SpotLight individual sobre peão ativo: intensidade 1.2

### Peões — Acabamento de Miniatura de Plástico Pintada
- **Materiais (plástico satinado)**: roughness baixa-média define o volume
  - Tecido (`_mClth`/`_cClth`): roughness 0.52, metalness 0.02
  - Couro (`_mLeather`/`_cLth`): roughness 0.46, metalness 0.04
  - Pele (`_mSkin`/`_cSkin`): roughness 0.42, metalness 0.02
  - Madeira (`_mWood`/`_cWood`): roughness 0.62
  - Metal/armadura (`_mMtl`/`_cArmr`): roughness 0.18–0.26, metalness 0.86–0.92
- **Resolução de geometria** via `_withSmoothGeo(T, fn)` — envolve a construção de
  cada peão e força mínimos: Cylinder 24, Sphere 28×20, Cone 24, Torus 16×36.
  Box NÃO é afetado (faces planas devem ficar nítidas). Aplicado em `_cHero`
  (seleção) e `build3DFig` (tabuleiro).
- **Iluminação de estúdio (tela de seleção)**: Ambient 0xfff2e6 0.62 +
  HemisphereLight 0.55 + Key DirectionalLight 1.25 (com sombra) + Fill 0.42 +
  Rim 0.55 + SpotLight 1.4 sobre o selecionado.

### Tipografia
- Títulos: Cinzel Decorative
- Textos: Cinzel
- Cor dourada: #c8a951

### Personagens

**Victor Coice Bravo**
- Classe no tabuleiro: `ranger`; na seleção: `warrior`
- Nome canônico: **Victor Coice Bravo**
- Plaquinha da base: **VICTOR**
- Identificadores de código: `victorCoiceBravo`, `victor_coice_bravo`
- Foto para tela de seleção: `assets/portraits/victor.jpeg`

**Richard, o Cavaleiro**
- Classe no tabuleiro: `paladin`; na seleção: `paladin`
- Nome canônico: **Richard, o Cavaleiro**
- Plaquinha da base: **RICHARD**
- Identificadores de código: `richardCavaleiro`, `richard_cavaleiro`
- Foto para tela de seleção e ficha: `assets/portraits/richard.jpeg` (mesmo modelo do Victor)
- `_CSD.paladin.cls` = `'RICHARD'` (não `'PALADINO'` — renomeado por instrução explícita)

**Luccas, o Astuto**
- Classe no tabuleiro: `rogue`; na seleção: `rogue`
- Nome canônico: **Luccas, o Astuto** (substituiu "Ladino")
- Plaquinha da base: **LUCCAS**
- Foto para tela de seleção e ficha: `assets/portraits/luccas.jpeg` (mesmo modelo do Victor)
- `_CSD.rogue.cls` = `'LUCCAS'`; `server.py` CLASSES["rogue"]["name"] = "Luccas, o Astuto"

**Frade Lewis**
- Classe no tabuleiro: `cleric`; na seleção: `cleric`
- Nome canônico: **Frade Lewis** (substituiu "Clérigo")
- Plaquinha da base: **FRADE LEWIS**
- Foto para tela de seleção e ficha: `assets/portraits/lewis.jpeg` (mesmo modelo do Victor)
- `_CSD.cleric.cls` = `'FRADE LEWIS'`; `server.py` CLASSES["cleric"]["name"] = "Frade Lewis"

**Henrique, o Bardo**
- Classe no tabuleiro: `bard`; na seleção: `bard`
- Nome canônico: **Henrique, o Bardo** (substituiu "Bardo")
- Plaquinha da base: **HENRIQUE**
- Foto para tela de seleção e ficha: `assets/portraits/henrique.jpeg` (mesmo modelo do Victor)
- `_CSD.bard.cls` = `'HENRIQUE'`; `server.py` CLASSES["bard"]["name"] = "Henrique, o Bardo"

**Pedro, o Tímido**
- Classe no tabuleiro: `mage`; na seleção: `mage`
- Nome canônico: **Pedro, o Tímido** (substituiu "Mago"/"Mago Negro")
- Plaquinha da base: **PEDRO**
- Foto para tela de seleção e ficha: `assets/portraits/pedro.jpeg` (mesmo modelo do Victor)
- `_CSD.mage.cls` = `'PEDRO'`; `server.py` CLASSES["mage"]["name"] = "Pedro, o Tímido"
- NÃO confundir com o monstro `dark_mage` ("Mago das Trevas") — inalterado

**Richard — Cores da Miniatura 3D**
- Armadura prata polida: `#b8b8c0` roughness 0.20 metalness 0.90
- Armadura prata highlight: `#d0d4e0` roughness 0.14 metalness 0.96
- Entalhes e detalhes dourados: `#c8a951` roughness 0.28 metalness 0.82
- Capa azul real: `#1a3a8f` roughness 0.92 (DoubleSide)
- Escudo face azul: `#1a3a8f` roughness 0.70 metalness 0.04
- Lâmina da espada: `#d4dce8` roughness 0.14 metalness 0.96
- Pele: `#c8956a` (via `_mSkin`)
- Cabelo castanho: `#4a2e10`
- Escala: `scale(1.0, 1.0, 1.0)` — herói mais alto, referência de escala do grupo
- Iluminação especial: SpotLight branca intensidade 1.8 (topo) + PointLight azul `#1a3a8f` intensidade 0.4 (capa)

### Retratos de Heróis — Regra Obrigatória
- Retratos são **exclusivos da tela de seleção de personagem**, implementados em HTML puro
- O painel de retrato existe dentro de `#cs-portrait-frame` no `#cs-panel`
- Ao entrar no tabuleiro (`destroyClassSelectFull`), a imagem é zerada (`img.src = ''`)
- **NUNCA** adicionar mesh, sprite ou PlaneGeometry sobre o tabuleiro para retratos
- **NUNCA** usar `THREE.TextureLoader` ou `CanvasTexture` de retrato em `g3.scene`
- Para adicionar retrato de novo herói: inserir campo `portrait:` no objeto `_CSD[classId]`

### Atributos de Personagens — Regra Obrigatória
**Os únicos atributos exibidos são:** Força, Destreza, Inteligência, Constituição (nesta ordem)
- Escala: 1–25 (sistema D20 — mapeado para 0–100% na barra)
- Nenhum outro atributo (Magia, Sorte, Agilidade, etc.) deve ser exibido na tela de seleção
- Renderização: barra dourada (#c8a951) com label + valor numérico à direita
- Estrutura de dados: `stats: { forca, destreza, inteligencia, constituicao }`
- Valores espelham os campos `str_`, `dex`, `int_`, `con_` do `CLASSES` em server.py

### REGRA PRINCIPAL
Nunca altere valores deste arquivo sem instrução explícita.
Ao fazer qualquer mudança no projeto, preserve todos os valores acima.
