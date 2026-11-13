# Estrada de pedras conectável — Plano de implementação

> **For agentic workers:** implement inline in this workspace and preserve unrelated local changes.

**Goal:** Fazer o piso `caminho_pedras_terra` conectar automaticamente em retas, pontas, curvas, T e cruzamentos quando o autor pinta ou apaga tiles no editor.

**Architecture:** `tools/editor.js` deriva o formato pelo conjunto de estradas ortogonalmente adjacentes e guarda a imagem canônica e a rotação no próprio decal. Editor 2D e cliente 2D/3D aplicam a rotação armazenada; o servidor conserva os campos existentes de decoração, sem regra de movimento nova.

**Tech Stack:** JavaScript do editor/cliente, PNGs top-down sob `assets/objetos`.

**Spec:** `docs/superpowers/specs/2026-11-02-estrada-pedras-conexoes-design.md`

## Global Constraints

- Só conexões ortogonais contam; diagonais não conectam.
- A topologia deriva das peças presentes e é recalculada ao editar/abrir o mapa.
- A estrada permanece uma camada `special:"floor"`, caminhável, sobre material `terra`.
- Não adicionar nem executar testes automatizados neste trabalho.

## Review Focus

- Tile isolado continua legível como piso de pedras.
- Ponta, reta, curva, T e cruzamento apontam para exatamente os vizinhos presentes.
- Apagar ou substituir um tile atualiza seus vizinhos imediatamente.
- Vizinhos diagonais não criam uma conexão falsa.
- A rotação se mantém igual no editor 2D, jogo 2D e jogo 3D.

---

### Task 1: Variantes visuais

**Files:**
- Create: `assets/objetos/caminho_pedras_terra_{isolado,ponta,curva,T,cruzamento}.png`
- Preserve: `assets/objetos/caminho_pedras_terra.png` como variante reta norte-sul

- [x] Criar as cinco formas canônicas com terra e pedras no mesmo estilo da textura atual: isolado, uma saída ao norte, curva norte-leste, T norte-leste-oeste e cruzamento.
- [x] Conferir as imagens e ajustar ponta, largura e continuidade nas bordas.

### Task 2: Topologia e editor

**Files:**
- Modify: `tools/editor.js`

- [x] Implementar a derivação do mask N/E/S/W para cada `caminho_pedras_terra`, escolher a imagem canônica e calcular rotações de 90°.
- [x] Recalcular antes da prévia e da serialização/salvamento do mapa, de forma que pintar, apagar, mover ou reabrir atualize todos os trechos conectados.

### Task 3: Renderização do piso

**Files:**
- Modify: `tools/editor.js`
- Modify: `game.js`
- Modify: `CLAUDE.md`

- [x] Aplicar a rotação do decal em cada tile no editor 2D e no jogo 2D/3D sem alterar a rotação de outros pisos.
- [x] Registrar o contrato de conexão no histórico de arquitetura.
- [x] Verificar `node --check tools/editor.js`, `node --check game.js` e `git diff --check`; inspeção visual das seis variantes.
