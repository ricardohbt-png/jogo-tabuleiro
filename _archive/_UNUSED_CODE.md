# Código Não Utilizado — Arquivo de Referência

Este arquivo documenta o código que foi removido de game.html durante a limpeza do projeto.

## Função: `_miniRanger(g, clr, Y)`

**Localização original**: game.html, linha 7995
**Status**: ❌ Não referenciada
**Motivo**: Victor (classe `ranger`) usa `_miniVictor()` desde a implementação customizada

### Código removido:

```javascript
function _miniRanger(g, clr, Y){
  // Miniatura genérica do Ranger
  // Nunca foi chamada após o Ranger ser substituído por Victor
}
```

### Por que existe:

- Quando o projeto começou, tinha 6 classes genéricas (Warrior, Mage, Rogue, Cleric, Ranger, Bard, Paladin)
- Ranger tinha uma miniatura genérica em `_miniRanger()`
- Depois, Victor (classe `ranger`) ganhou uma miniatura customizada em `_miniVictor()`
- O switch statement em `_buildPawnMesh()` (linha ~7377) foi atualizado para usar `_miniVictor()` ao invés de `_miniRanger()`
- A função `_miniRanger()` ficou órfã

### Recuperação:

Se precisar recuperar esta função, consulte o git history ou pesquise a próxima versão de game.html no repositório.

---

## Imagens Não Referenciadas

4 imagens de retrato foram movidas para _archive/:

- `pedro.jpeg` — Nunca foi referenciado em HERO_PORTRAIT_PATHS ou _CSD
- `lewis.jpeg` — Nunca foi referenciado em HERO_PORTRAIT_PATHS ou _CSD
- `luccas.jpeg` — Nunca foi referenciado em HERO_PORTRAIT_PATHS ou _CSD
- `henrique.jpeg` — Nunca foi referenciado em HERO_PORTRAIT_PATHS ou _CSD

Provavelmente são protótipos de personagens que não chegaram a ser implementados.
