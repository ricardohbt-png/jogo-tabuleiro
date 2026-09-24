# Sons e Efeitos Sonoros — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tocar amostras gravadas (CC0) para combate físico, exploração/loot, criaturas, interface e ambiente, com abafamento na névoa, mantendo a síntese atual como recuo.

**Architecture:** Um módulo puro `src/soundBank.js` (catálogo + regras: audibilidade, variante, limitador, eventos por diferença de estado) testável em node; um motor fino no `game.js` (`sfx()`, cache de `AudioBuffer`, filtro/pan, loop de ambiente) pendurado nos pontos que já existem (`CombatScene`, `_capturarDerrotas…`, handlers de `gameState`/`cityState`/`enterDungeon`/`serverError`); e um único campo novo no servidor, `impacto`, no `attack_feedback start`.

**Tech Stack:** Python 3 (`server.py`), Vanilla JS + Web Audio API, Three.js r128 (só para projetar a posição na câmera), ffmpeg 8.1 (preparação de arquivos), node (testes).

**Spec:** `docs/superpowers/specs/2026-09-23-sons-efeitos-sonoros-design.md`

---

## Antes de começar — regras deste repositório

- **`server.py`, `game.js` e `CLAUDE.md` têm trabalho do autor em andamento (não commitado).** Não faça `git add` neles: o commit levaria o WIP junto. Nas tarefas que os tocam, o passo de commit inclui **só os arquivos novos ou limpos** (`src/soundBank.js`, `src/combatScene.js`, `index.html`, testes, `assets/sfx/`). As mudanças em `server.py`/`game.js`/`CLAUDE.md` ficam no working tree para o autor commitar junto com o WIP dele. Antes de cada commit rode `git status` e `git diff --cached --name-only` e confira a lista.
- `server.py`, `game.js` e `CLAUDE.md` estão em **CRLF**: use a ferramenta Edit, não `replace()` de script Python com `\n`.
- O autor edita `game.js` em paralelo: localize trechos pelo **texto**, nunca pelo número de linha deste plano.
- **Servidor rodando trava a escrita** de `server.py`/`game.js` (`OSError: Errno 22`): pare o preview antes de editar.
- `GS.on(evento, fn)` **substitui** o ouvinte anterior (não soma). Nunca registre um segundo `GS.on` para um evento que já tem um; acrescente dentro do existente.
- Nenhum download sem aprovação explícita do autor (Tarefa 8).
- Após editar `game.js`/`src/*.js`, a prova no navegador exige recarregar com cache-buster; o `index.html` já usa `?v=Date.now()`.

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/soundBank.js` | criar | Catálogo `SFX`, `familiaDe`, `audibilidade`, `escolherVariante`, `criarLimitador`, `diffSons`, `eventoAmbiente` — puro |
| `tools/test_sound_bank.js` | criar | Testes node do módulo puro |
| `server.py` | modificar | `_impacto_de` + campo `impacto` nos 3 `attack_feedback start` |
| `tools/test_sons_impacto.py` | criar | Testes do `impacto` |
| `src/combatScene.js` | modificar | Carregar `impacto` da mensagem até o comando `impact` |
| `tools/test_combat_scene.js` | modificar | Seção nova para o `impacto` |
| `index.html` | modificar | Incluir `src/soundBank.js` antes do `game.js` |
| `game.js` | modificar | Motor `sfx()`, ambiente, ganchos de combate/morte/estado/interface |
| `tools/test_sons_cliente.js` | criar | Testes node das funções de gancho do `game.js` (extraídas) + fiação estática |
| `assets/sfx/**` | criar | Arquivos `.ogg` preparados + `LICENCAS.md` |
| `tools/preparar_sfx.py` | criar | Conversão ffmpeg (corte, loudness, mono/estéreo, loop) |
| `tools/test_sfx_arquivos.js` | criar | Catálogo × pasta: nada faltando, nada órfão, orçamento de tamanho |
| `CLAUDE.md` | modificar | Seção de documentação da feature |

---

### Task 1: Campo `impacto` no `attack_feedback` (servidor)

**Files:**
- Modify: `server.py` (ao lado de `def _projetil_de`, e as 3 chamadas `_emitir_feedback_ataque("start", …)`)
- Modify: `server.py` (`_emitir_feedback_ataque`, descarte de `None`)
- Test: `tools/test_sons_impacto.py`

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_sons_impacto.py`:

```python
"""Campo `impacto` do attack_feedback (sons do golpe). Spec:
docs/superpowers/specs/2026-09-23-sons-efeitos-sonoros-design.md"""
import sys, os, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
with contextlib.redirect_stdout(io.StringIO()):
    import server as S

PASS = FAIL = 0
def check(nome, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {nome}")
    else:    FAIL += 1; print(f"  ❌ {nome}")

print("\n[1] Herói: pela categoria da arma")
check("espada longa → cortante", S._impacto_de({"id": "espada2m", "categoria": "cortante"}) == "cortante")
check("adaga → perfurante", S._impacto_de(S.WEAPONS["dagger"]) == "perfurante")
check("categoria contundente", S._impacto_de({"categoria": "contundente"}) == "contundente")
check("herói desarmado (None) → None", S._impacto_de(None) is None)
check("arma de herói sem categoria → None", S._impacto_de({"id": "x", "name": "Garra"}) is None)

print("\n[2] Monstro: nome natural vence a categoria")
check("Mordida perfurante → natural",
      S._impacto_de({"name": "Mordida", "categoria": "perfurante", "damage_types": ["physical"]}, monstro=True) == "natural")
check("Garras → natural", S._impacto_de({"name": "Garras"}, monstro=True) == "natural")
check("Ferrão (acento) → natural", S._impacto_de({"name": "Ferrão"}, monstro=True) == "natural")
check("Pinça → natural", S._impacto_de({"name": "Pinça"}, monstro=True) == "natural")
check("Chifrada → natural", S._impacto_de({"name": "Chifrada"}, monstro=True) == "natural")

print("\n[3] Monstro: arma pela categoria ou pelo nome")
check("Espada Curta com categoria", S._impacto_de({"name": "Espada Curta", "categoria": "cortante"}, monstro=True) == "cortante")
check("Clava Pesada sem categoria → contundente", S._impacto_de({"name": "Clava Pesada"}, monstro=True) == "contundente")
check("Lança Curta sem categoria → perfurante", S._impacto_de({"name": "Lança Curta"}, monstro=True) == "perfurante")
check("Machado sem categoria → cortante", S._impacto_de({"name": "Machado"}, monstro=True) == "cortante")

print("\n[4] Monstro: elemental e desconhecido não têm impacto")
check("Chama (fire) → None", S._impacto_de({"name": "Chama", "damage_types": ["fire"]}, monstro=True) is None)
check("Garra Congelante (cold) → None",
      S._impacto_de({"name": "Garra Congelante", "damage_types": ["cold"]}, monstro=True) is None)
check("'Ataque' genérico → None", S._impacto_de({"name": "Ataque"}, monstro=True) is None)

print("\n[5] Todo ataque físico de MONSTER_DEFS tem impacto ou é genérico conhecido")
sem = sorted({a.get("name") for d in S.MONSTER_DEFS for a in (d.get("attacks") or [])
              if (a.get("damage_types") or ["physical"]) == ["physical"]
              and S._impacto_de(a, monstro=True) is None})
print("     sem impacto:", sem)
check("só nomes genéricos ficam sem impacto", set(sem) <= {"Ataque", "Golpe", "Toque Corrosivo"})

print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_sons_impacto.py`
Expected: termina com `AttributeError: module 'server' has no attribute '_impacto_de'`.

- [ ] **Step 3: Implementar `_impacto_de`**

Em `server.py`, logo **depois** do fim de `def _projetil_de(...)` (a linha `    return None` que fecha a função, antes do bloco `# ─── GUILDA DOS HERÓIS`), acrescente:

```python

# ── Som do golpe (sons e efeitos sonoros — só afeta o áudio do cliente) ──
# Devolve "cortante" | "perfurante" | "contundente" | "natural" ou None.
# Herói: só a `categoria` da arma. Monstro: nome natural (mordida, garra…)
# vence a categoria; depois a categoria; depois o nome da arma. Ataque com
# dano elemental não tem impacto físico (o cliente usa o som do elemento).
_IMPACTOS = ("cortante", "perfurante", "contundente")
_IMPACTO_NATURAL = ("mordida", "garra", "ferrao", "ferroes", "pinca", "chifr",
                    "tentaculo", "cauda", "cabecada", "cobras")
_IMPACTO_POR_NOME = (("espada", "cortante"), ("machado", "cortante"),
                     ("alabarda", "cortante"), ("adaga", "perfurante"),
                     ("lanca", "perfurante"), ("arco", "perfurante"),
                     ("besta", "perfurante"), ("clava", "contundente"),
                     ("martelo", "contundente"), ("cajado", "contundente"),
                     ("rocha", "contundente"))

def _impacto_de(defn, monstro=False):
    if not defn or not isinstance(defn, dict):
        return None
    cat = defn.get("categoria")
    if not monstro:
        return cat if cat in _IMPACTOS else None
    tipos = defn.get("damage_types") or ["physical"]
    if any(t != "physical" for t in tipos):
        return None
    nome = unicodedata.normalize("NFKD", str(defn.get("name") or "")) \
        .encode("ascii", "ignore").decode().lower()
    if any(p in nome for p in _IMPACTO_NATURAL):
        return "natural"
    if cat in _IMPACTOS:
        return cat
    for palavra, impacto in _IMPACTO_POR_NOME:
        if palavra in nome:
            return impacto
    return None
```

- [ ] **Step 4: Rodar o teste**

Run: `PYTHONIOENCODING=utf-8 python tools/test_sons_impacto.py`
Expected: `=== 18 passaram, 0 falharam ===`. Se a seção [5] listar um nome físico fora do conjunto genérico, acrescente a palavra ao `_IMPACTO_NATURAL` ou ao `_IMPACTO_POR_NOME` (não afrouxe o teste).

- [ ] **Step 5: Emitir o campo nos 3 `start`**

Em `_emitir_feedback_ataque`, logo abaixo das duas linhas existentes

```python
        if resultado.get("projectile") is None:
            resultado.pop("projectile", None)      # só o start com projétil leva a chave
```

acrescente:

```python
        if resultado.get("impacto") is None:
            resultado.pop("impacto", None)          # sem impacto: payload idêntico ao antigo
```

Nas três chamadas `"start"`, acrescente o argumento `impacto=` na linha seguinte à do `projectile=` (use Edit com o texto exato):

- herói (`handle_attack`): `projectile=_projetil_de(weapon_here),` → acrescentar logo abaixo `impacto=_impacto_de(weapon_here),`
- servo animado: `projectile=_projetil_de(ataque, monstro=True))` → trocar por
  ```python
              projectile=_projetil_de(ataque, monstro=True),
              impacto=_impacto_de(ataque, monstro=True))
  ```
- monstro: `projectile=_projetil_de(atk_def, monstro=True))` → trocar por
  ```python
              projectile=_projetil_de(atk_def, monstro=True),
              impacto=_impacto_de(atk_def, monstro=True))
  ```

- [ ] **Step 6: Teste de emissão**

Acrescente ao fim de `tools/test_sons_impacto.py`, **antes** do `print(f"\n=== …")`:

```python
print("\n[6] _emitir_feedback_ataque: sem impacto a chave some")
import asyncio
r = S.GameRoom("TEST")
enviados = []
async def cap(msg, *a, **k): enviados.append(msg)
r.broadcast = cap
atacante = {"id": "a", "name": "A", "pos": [0, 0]}
alvo = {"id": "b", "name": "B", "pos": [1, 0]}
asyncio.run(r._emitir_feedback_ataque("start", atacante, alvo, "Espada", impacto="cortante"))
asyncio.run(r._emitir_feedback_ataque("start", atacante, alvo, "Soco", impacto=None))
check("com impacto a chave vai", enviados[0].get("impacto") == "cortante")
check("sem impacto a chave NÃO vai", "impacto" not in enviados[1])
```

Run: `PYTHONIOENCODING=utf-8 python tools/test_sons_impacto.py`
Expected: `=== 20 passaram, 0 falharam ===`

- [ ] **Step 7: Não quebrar vizinhos**

Run:
```bash
for f in test_projeteis test_modo_mestre test_handler_smoke test_furia_bestial; do PYTHONIOENCODING=utf-8 python tools/$f.py 2>&1 | tail -1; done
```
Expected: todas com `0 falharam`.

- [ ] **Step 8: Commit (só o teste novo)**

```bash
git add tools/test_sons_impacto.py
git diff --cached --name-only
git commit -m "test(sons): impacto do golpe no attack_feedback

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
(`server.py` fica no working tree — tem WIP do autor.)

---

### Task 2: `CombatScene` carrega o `impacto`

**Files:**
- Modify: `src/combatScene.js` (`novaCena` e `emitirImpacto`)
- Test: `tools/test_combat_scene.js`

- [ ] **Step 1: Teste que falha**

Em `tools/test_combat_scene.js`, antes da linha final que imprime o total (procure `console.log(\`\n=== ` ou equivalente no fim do arquivo), acrescente:

```js
console.log("\n[S1] impacto viaja da mensagem ao comando impact (sons)");
{
  CS.reset(); CS.configure({ waitDieMs: 0 });
  CS.start({ ...START, attack_id: "snd1", impacto: "cortante" }, 0);
  CS.result({ ...RESULT_HIT, attack_id: "snd1" }, 1);
  let imp = null;
  for (let t = 0; t < 3000 && !imp; t += 16) for (const c of CS.tick(t)) if (c.cmd === "impact") imp = c;
  check("impact traz impacto=cortante", imp && imp.impacto === "cortante");

  CS.reset(); CS.configure({ waitDieMs: 0 });
  CS.start({ ...START, attack_id: "snd2", impacto: "lixo" }, 0);
  CS.result({ ...RESULT_HIT, attack_id: "snd2" }, 1);
  imp = null;
  for (let t = 0; t < 3000 && !imp; t += 16) for (const c of CS.tick(t)) if (c.cmd === "impact") imp = c;
  check("impacto inválido vira null", imp && imp.impacto === null);
  CS.reset(); CS.configure({});
}
```

- [ ] **Step 2: Ver falhar**

Run: `node tools/test_combat_scene.js 2>&1 | grep -E "S1|impacto|passaram"`
Expected: os dois checks do `[S1]` com ❌.

- [ ] **Step 3: Implementar**

Em `src/combatScene.js`, dentro de `novaCena`, no objeto `const s = {`, logo abaixo da linha `projectile: pj, distCasas,` acrescente:

```js
      impacto: IMPACTOS.indexOf(msg.impacto) >= 0 ? msg.impacto : null,
```

No topo do IIFE, logo abaixo de `'use strict';`, acrescente:

```js
  // Som do golpe (spec 2026-09-23-sons): só viaja da mensagem até o `impact`.
  const IMPACTOS = ['cortante', 'perfurante', 'contundente', 'natural'];
```

Em `emitirImpacto`, no objeto `const c = {`, logo abaixo da linha `projectile: s.projectile ? s.projectile.kind : null,` acrescente:

```js
      impacto: s.impacto,
```

- [ ] **Step 4: Rodar**

Run: `node tools/test_combat_scene.js 2>&1 | tail -2`
Expected: `0 falharam` (total = anterior + 2).

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git diff --cached --name-only
git commit -m "feat(sons): CombatScene carrega o impacto do golpe até o comando impact

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Módulo puro `src/soundBank.js`

**Files:**
- Create: `src/soundBank.js`
- Test: `tools/test_sound_bank.js`

- [ ] **Step 1: Teste que falha**

Crie `tools/test_sound_bank.js`:

```js
// tools/test_sound_bank.js — node tools/test_sound_bank.js
// Regras puras do banco de sons. Spec: 2026-09-23-sons-efeitos-sonoros-design.md
const fs = require('fs');
const path = require('path');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
global.window = {};
eval(fs.readFileSync(path.join(__dirname, '..', 'src', 'soundBank.js'), 'utf8'));
const SB = global.window.SoundBank;

console.log('\n[1] Catálogo');
const eventos = Object.keys(SB.SFX);
for (const e of ['golpe_cortante','golpe_perfurante','golpe_contundente','golpe_natural','golpe_critico',
                 'golpe_erro','escudo_bloqueio','dor_heroi','dor_criatura','porta_abre','moedas','item_pegar',
                 'equipar','beber','escada','sua_vez','nivel','objetivo','clique','recusa',
                 'amb_masmorra','amb_penumbra','amb_ar_livre'])
  check('tem ' + e, eventos.includes(e));
for (const f of SB.FAMILIAS) check('rugido e morte de ' + f, !!SB.SFX['rugido_' + f] && !!SB.SFX['morte_' + f]);
check('todo evento tem lista de arquivos, volume e canal válido', eventos.every(e => {
  const d = SB.SFX[e];
  return Array.isArray(d.arquivos) && d.volume > 0 && d.volume <= 1 && (d.canal === 'efeitos' || d.canal === 'ambiente');
}));
check('só os amb_* são do canal ambiente', eventos.every(e => (SB.SFX[e].canal === 'ambiente') === e.startsWith('amb_')));

console.log('\n[2] familiaDe');
const fam = t => SB.familiaDe({ type: t });
check('goblin_arqueiro → humanoide', fam('goblin_arqueiro') === 'humanoide');
check('lobo_cinzento_customizado → fera', fam('lobo_cinzento_customizado') === 'fera');
check('esqueleto_humano → morto_vivo', fam('esqueleto_humano') === 'morto_vivo');
check('zumbi_infectado → morto_vivo', fam('zumbi_infectado') === 'morto_vivo');
check('cobra_venenosa → reptil_inseto', fam('cobra_venenosa') === 'reptil_inseto');
check('tirano_da_mata → grande', fam('tirano_da_mata') === 'grande');
check('grande_medusa → grande (antes de medusa)', fam('grande_medusa') === 'grande');
check('medusa → humanoide', fam('medusa') === 'humanoide');
check('elemental_fogo → null (sem voz)', fam('elemental_fogo') === null);
check('boneco_treino → null', fam('boneco_treino') === null);
check('desconhecido 1×1 → humanoide', SB.familiaDe({ type: 'coisa_nova', size: [1, 1] }) === 'humanoide');
check('desconhecido 2×2 → grande', SB.familiaDe({ type: 'coisa_nova', size: [2, 2] }) === 'grande');
check('sem type → humanoide', SB.familiaDe({}) === 'humanoide');

console.log('\n[3] audibilidade');
const vis = new Set(['5,5', '6,5', '17,5']);
let a = SB.audibilidade({});
check('sem pos: ganho 1, sem abafar, sem pan', a.ganho === 1 && !a.abafado && !a.panLivre);
a = SB.audibilidade({ pos: [5, 5], visao: vis, mePos: [5, 5] });
check('visível na mesma casa: ganho 1', a.ganho === 1 && !a.abafado && a.panLivre);
a = SB.audibilidade({ pos: [17, 5], visao: vis, mePos: [5, 5] });
check('visível a 12 casas: ganho 0.4', Math.abs(a.ganho - 0.4) < 1e-9);
a = SB.audibilidade({ pos: [11, 5], visao: new Set(['11,5']), mePos: [5, 5] });
check('visível a 6 casas: ganho 0.7', Math.abs(a.ganho - 0.7) < 1e-9);
a = SB.audibilidade({ pos: [9, 9], visao: vis, mePos: [5, 5] });
check('na névoa: 0.35, abafado, SEM pan', a.ganho === 0.35 && a.abafado && !a.panLivre);
a = SB.audibilidade({ pos: [9, 9], visao: vis, mePos: [5, 5], mestre: true });
check('mestre nunca ouve abafado', a.ganho === 1 && !a.abafado);
a = SB.audibilidade({ pos: [9, 9], visao: null, mePos: [5, 5] });
check('sem conjunto de visão (cidade): trata como visível', !a.abafado);
a = SB.audibilidade({ pos: [5.4, 4.6], visao: vis, mePos: [5, 5] });
check('posição fracionária arredonda para a casa', !a.abafado);

console.log('\n[4] escolherVariante');
check('lista vazia → -1', SB.escolherVariante(0, -1) === -1);
check('uma variante → 0', SB.escolherVariante(1, 0) === 0);
let repetiu = false, ult = -1;
for (let i = 0; i < 200; i++) { const v = SB.escolherVariante(3, ult); if (v === ult) repetiu = true; if (v < 0 || v > 2) repetiu = true; ult = v; }
check('3 variantes: nunca repete a anterior e fica no intervalo', !repetiu);
check('rnd injetável e determinístico', SB.escolherVariante(3, 0, () => 0) === 1 && SB.escolherVariante(3, 2, () => 0) === 0);

console.log('\n[5] criarLimitador');
const L = SB.criarLimitador(3);
check('primeiro toca', L.pode('moedas', 0, 0.5));
L.registrar('moedas', 0, 400, 0.5);
check('mesmo evento dentro do intervalo NÃO toca', !L.pode('moedas', 100, 0.5));
check('depois do intervalo toca', L.pode('moedas', SB.SFX.moedas.intervaloMs + 1, 0.5));
L.reset();
L.registrar('golpe_cortante', 0, 1000, 0.5); L.registrar('golpe_perfurante', 0, 1000, 0.5); L.registrar('clique', 0, 1000, 0.1);
check('teto cheio: descarta o novo', !L.pode('porta_abre', 10, 0.9));
check('teto libera quando os sons terminam', L.pode('porta_abre', 1001, 0.9));
check('evento desconhecido nunca toca', !L.pode('nao_existe', 5000, 1));

console.log('\n[6] diffSons');
const base = { portas: ['3,4'], me: { ouro: 10, bag: [{ id: 'x' }, null], gear: { weapon: { id: 'dagger' } }, nivel: 1 },
               meuTurno: false, missao: false, monstros: [{ id: 'm1', type: 'goblin', pos: [2, 2] }] };
let r = SB.diffSons(null, base);
check('primeiro estado só semeia (sem eventos)', r.eventos.length === 0);
check('monstros já visíveis no primeiro estado ficam ouvidos', r.snap.ouvidos.has('m1'));
const ev = (prev, atual) => SB.diffSons(prev, atual).eventos.map(e => e.evento);
const s0 = r.snap;
check('nada mudou → nada toca', ev(s0, base).length === 0);
r = SB.diffSons(s0, { ...base, portas: ['3,4', '7,8'] });
check('porta nova aberta → porta_abre com pos', r.eventos.length === 1 && r.eventos[0].evento === 'porta_abre' && r.eventos[0].pos[0] === 7 && r.eventos[0].pos[1] === 8);
check('ouro subiu → moedas', ev(s0, { ...base, me: { ...base.me, ouro: 25 } }).join() === 'moedas');
check('ouro caiu → nada', ev(s0, { ...base, me: { ...base.me, ouro: 5 } }).length === 0);
check('bolsa cresceu → item_pegar', ev(s0, { ...base, me: { ...base.me, bag: [{ id: 'x' }, { id: 'y' }] } }).join() === 'item_pegar');
check('gear mudou → só equipar (sem item_pegar)', ev(s0, { ...base, me: { ...base.me, bag: [{ id: 'x' }, { id: 'dagger' }], gear: {} } }).join() === 'equipar');
const comPocao = { ...base, me: { ...base.me, bag: [{ id: 'p', effect: 'heal', uses_left: 2 }] } };
const sP = SB.diffSons(null, comPocao).snap;
check('dose de poção gasta → beber', ev(sP, { ...base, me: { ...base.me, bag: [{ id: 'p', effect: 'heal', uses_left: 1 }] } }).join() === 'beber');
check('nível subiu → nivel', ev(s0, { ...base, me: { ...base.me, nivel: 2 } }).join() === 'nivel');
check('turno virou meu → sua_vez', ev(s0, { ...base, meuTurno: true }).join() === 'sua_vez');
check('missão cumprida → objetivo', ev(s0, { ...base, missao: true }).join() === 'objetivo');
r = SB.diffSons(s0, { ...base, monstros: [...base.monstros, { id: 'm2', type: 'lobo_cinzento', pos: [4, 4] }, { id: 'm3', type: 'goblin', pos: [5, 4] }] });
check('monstros novos visíveis → UM rugido só', r.eventos.filter(e => e.evento.startsWith('rugido_')).length === 1);
check('rugido do primeiro novo, com família e pos', r.eventos[0].evento === 'rugido_fera' && r.eventos[0].pos[0] === 4);
check('os dois novos ficam ouvidos', r.snap.ouvidos.has('m2') && r.snap.ouvidos.has('m3'));
check('monstro já ouvido não ruge de novo', ev(r.snap, { ...base, monstros: [{ id: 'm2', type: 'lobo_cinzento', pos: [4, 4] }] }).length === 0);
check('monstro sem voz (elemental) não ruge', ev(s0, { ...base, monstros: [{ id: 'e1', type: 'elemental_fogo', pos: [1, 1] }] }).length === 0);
check('sem herói (mestre): não quebra, só eventos globais', ev(s0, { ...base, me: null, missao: true }).join() === 'objetivo');

console.log('\n[7] eventoAmbiente');
check('preset conhecido', SB.eventoAmbiente('penumbra') === 'amb_penumbra');
check('preset desconhecido → masmorra', SB.eventoAmbiente('lua') === 'amb_masmorra');
check('ausente → masmorra', SB.eventoAmbiente(undefined) === 'amb_masmorra');
{
  const guardado = SB.SFX.amb_penumbra.arquivos;
  SB.SFX.amb_penumbra.arquivos = [];
  check('preset sem arquivo → masmorra', SB.eventoAmbiente('penumbra') === 'amb_masmorra');
  SB.SFX.amb_penumbra.arquivos = guardado;
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Ver falhar**

Run: `node tools/test_sound_bank.js`
Expected: erro `ENOENT … src/soundBank.js`.

- [ ] **Step 3: Implementar o módulo**

Crie `src/soundBank.js`:

```js
// src/soundBank.js
// Banco de sons: catálogo declarativo + regras PURAS (audibilidade, variante,
// limitador, eventos por diferença de estado). Sem DOM, sem Web Audio.
// Exposto como window.SoundBank (browser) / global.SoundBank (node).
// Spec: docs/superpowers/specs/2026-09-23-sons-efeitos-sonoros-design.md
(function (root) {
  'use strict';

  const GANHO_NEVOA = 0.35;       // fora da visão: mais baixo e abafado
  const GANHO_LONGE = 0.4;        // piso de algo visível e distante
  const DIST_LONGE = 12;          // casas até chegar ao piso
  const TETO_SIMULTANEOS = 8;

  const FAMILIAS = ['humanoide', 'fera', 'morto_vivo', 'reptil_inseto', 'grande'];

  // `arquivos` são relativos a assets/sfx/. Lista vazia = sem amostra: o
  // chamador toca a síntese antiga (ou fica em silêncio se não houver).
  const E = (arquivos, volume, intervaloMs, extra) => Object.assign(
    { arquivos, volume, intervaloMs, pitchJitter: 0.05, volJitter: 0.08, canal: 'efeitos' }, extra || {});
  const n = (base, qtd) => Array.from({ length: qtd }, (_, i) => `${base}_${i + 1}.ogg`);
  const AMB = (arq) => E([arq], 0.5, 0, { canal: 'ambiente', pitchJitter: 0, volJitter: 0 });

  const SFX = {
    // combate
    golpe_cortante:    E(n('combate/golpe_cortante', 3), 0.80, 60),
    golpe_perfurante:  E(n('combate/golpe_perfurante', 3), 0.80, 60),
    golpe_contundente: E(n('combate/golpe_contundente', 3), 0.80, 60),
    golpe_natural:     E(n('combate/golpe_natural', 3), 0.80, 60),
    golpe_critico:     E(n('combate/golpe_critico', 2), 0.70, 60),
    golpe_erro:        E(n('combate/golpe_erro', 3), 0.55, 60),
    escudo_bloqueio:   E(n('combate/escudo_bloqueio', 2), 0.75, 60),
    dor_heroi:         E(n('combate/dor_heroi', 3), 0.60, 120),
    dor_criatura:      E(n('combate/dor_criatura', 3), 0.60, 120),
    // exploração e loot
    porta_abre:        E(n('exploracao/porta_abre', 3), 0.70, 150),
    moedas:            E(n('exploracao/moedas', 2), 0.60, 250),
    item_pegar:        E(n('exploracao/item_pegar', 2), 0.50, 200),
    equipar:           E(n('exploracao/equipar', 3), 0.50, 200),
    beber:             E(n('exploracao/beber', 2), 0.55, 300),
    escada:            E(n('exploracao/escada', 2), 0.60, 500),
    // interface e ritmo do turno
    sua_vez:           E(n('interface/sua_vez', 1), 0.50, 1000),
    nivel:             E(n('interface/nivel', 1), 0.80, 1000),
    objetivo:          E(n('interface/objetivo', 1), 0.80, 1000),
    clique:            E(n('interface/clique', 2), 0.25, 60, { pitchJitter: 0.03 }),
    recusa:            E(n('interface/recusa', 1), 0.35, 300),
    // ambiente (loop; canal próprio)
    amb_masmorra:      AMB('ambiente/amb_masmorra.ogg'),
    amb_penumbra:      AMB('ambiente/amb_penumbra.ogg'),
    amb_ar_livre:      AMB('ambiente/amb_ar_livre.ogg'),
  };
  for (const f of FAMILIAS) {
    SFX['rugido_' + f] = E(n('criaturas/rugido_' + f, 2), 0.75, 400);
    SFX['morte_' + f] = E(n('criaturas/morte_' + f, 2), 0.70, 150);
  }

  // Ordem importa: a 1ª regra que casar decide. `null` = criatura sem voz.
  const REGRAS_FAMILIA = [
    [/^(boneco_|sentinela_teste$|vela_de_fogo$|elemental_)/, null],
    [/^(skeleton|esqueleto_|zumbi_)/, 'morto_vivo'],
    [/^(dragon|tirano_|tiranossauro|troll|ogro_|gigante_|ciclope|minotauro|grande_)/, 'grande'],
    [/^(aranha_|cobra_|crocodilo_|escorpiao_|ferrao_charcos|lagarto_|grotao|devorador_|estrangulador|lacralion_|molochus_)/, 'reptil_inseto'],
    [/^(lobo_|urso_|gato$|rato|pombo$|ovelha$|garaloux_|lobisomem|harpia)/, 'fera'],
    [/^(goblin|orc|kobold_|bugbear_|dark_mage|necromante|soldado|xama_|medusa|lorde_vampiro|vampiro_|escravo_vampirico)/, 'humanoide'],
  ];

  function familiaDe(m) {
    const tipo = String((m && m.type) || '');
    for (const [re, fam] of REGRAS_FAMILIA) if (re.test(tipo)) return fam;
    const s = m && Array.isArray(m.size) ? m.size : [1, 1];
    return (Number(s[0]) || 1) * (Number(s[1]) || 1) > 1 ? 'grande' : 'humanoide';
  }

  // o = { pos, visao: Set('x,y')|null, mePos, mestre }
  function audibilidade(o) {
    o = o || {};
    const pos = o.pos;
    if (!Array.isArray(pos)) return { ganho: 1, abafado: false, panLivre: false };
    if (o.mestre) return { ganho: 1, abafado: false, panLivre: true };
    const k = Math.round(pos[0]) + ',' + Math.round(pos[1]);
    if (o.visao && !o.visao.has(k)) return { ganho: GANHO_NEVOA, abafado: true, panLivre: false };
    if (!Array.isArray(o.mePos)) return { ganho: 1, abafado: false, panLivre: true };
    const d = Math.max(Math.abs(pos[0] - o.mePos[0]), Math.abs(pos[1] - o.mePos[1]));
    return { ganho: 1 - (1 - GANHO_LONGE) * Math.min(1, d / DIST_LONGE), abafado: false, panLivre: true };
  }

  function escolherVariante(qtd, ultimo, rnd) {
    if (!(qtd > 0)) return -1;
    if (qtd === 1) return 0;
    let i = Math.floor((rnd || Math.random)() * (qtd - 1));
    if (ultimo >= 0 && i >= ultimo) i++;
    return i;
  }

  function criarLimitador(teto) {
    const max = teto || TETO_SIMULTANEOS;
    const ultimo = new Map();
    let ativos = [];
    return {
      pode(evento, agora) {
        const def = SFX[evento];
        if (!def) return false;
        const u = ultimo.get(evento);
        if (u != null && agora - u < (def.intervaloMs || 0)) return false;
        ativos = ativos.filter(a => a.fim > agora);
        return ativos.length < max;
      },
      registrar(evento, agora, duracaoMs, ganho) {
        ultimo.set(evento, agora);
        ativos.push({ fim: agora + (duracaoMs || 0), ganho });
      },
      reset() { ultimo.clear(); ativos = []; },
    };
  }

  const POCAO_EFEITOS = new Set(['heal', 'regeneration', 'atk_bonus', 'cure_poison', 'cure_petrification', 'cure_disease']);
  function dosesDePocao(bag) {
    let d = 0;
    for (const it of bag) if (it && POCAO_EFEITOS.has(it.effect)) d += (it.uses_left != null ? Number(it.uses_left) || 0 : 1);
    return d;
  }
  function assinaturaGear(gear) {
    if (!gear || typeof gear !== 'object') return '';
    return Object.keys(gear).sort().map(k => k + ':' + ((gear[k] && gear[k].id) || '')).join('|');
  }
  function snapMe(me) {
    if (!me) return null;
    const bag = Array.isArray(me.bag) ? me.bag.filter(Boolean) : [];
    return { ouro: Number(me.ouro) || 0, bagN: bag.length, doses: dosesDePocao(bag),
             gear: assinaturaGear(me.gear), nivel: Number(me.nivel) || 0 };
  }

  // atual = { portas:['x,y'], me:{ouro,bag,gear,nivel}|null, meuTurno, missao,
  //           monstros:[{id,type,size,pos}] (só os VISÍVEIS para mim) }
  // Devolve { eventos:[{evento,pos?}], snap } — o snap vira o `prev` seguinte.
  function diffSons(prev, atual) {
    atual = atual || {};
    const eventos = [];
    const portas = new Set(atual.portas || []);
    const me = snapMe(atual.me);
    const ouvidos = new Set(prev ? prev.ouvidos : []);
    const visiveis = atual.monstros || [];
    const snap = { portas, me, meuTurno: !!atual.meuTurno, missao: !!atual.missao, ouvidos };
    if (!prev) {
      for (const m of visiveis) ouvidos.add(String(m.id));
      return { eventos, snap };
    }
    for (const k of portas) {
      if (prev.portas.has(k)) continue;
      const [x, y] = k.split(',').map(Number);
      eventos.push({ evento: 'porta_abre', pos: [x, y] });
    }
    if (me && prev.me) {
      if (me.gear !== prev.me.gear) eventos.push({ evento: 'equipar' });
      else {
        if (me.bagN > prev.me.bagN) eventos.push({ evento: 'item_pegar' });
        if (me.doses < prev.me.doses) eventos.push({ evento: 'beber' });
      }
      if (me.ouro > prev.me.ouro) eventos.push({ evento: 'moedas' });
      if (me.nivel > prev.me.nivel) eventos.push({ evento: 'nivel' });
    }
    if (snap.meuTurno && !prev.meuTurno) eventos.push({ evento: 'sua_vez' });
    if (snap.missao && !prev.missao) eventos.push({ evento: 'objetivo' });
    let rugiu = false;
    for (const m of visiveis) {
      const id = String(m.id);
      if (ouvidos.has(id)) continue;
      ouvidos.add(id);
      const fam = familiaDe(m);
      if (fam && !rugiu) { eventos.push({ evento: 'rugido_' + fam, pos: m.pos }); rugiu = true; }
    }
    return { eventos, snap };
  }

  // Preset sem loop próprio (desconhecido OU sem arquivo) usa o da masmorra.
  function eventoAmbiente(preset) {
    const e = 'amb_' + preset;
    return (SFX[e] && SFX[e].canal === 'ambiente' && SFX[e].arquivos.length) ? e : 'amb_masmorra';
  }

  root.SoundBank = {
    SFX, FAMILIAS, familiaDe, audibilidade, escolherVariante, criarLimitador,
    diffSons, eventoAmbiente,
    GANHO_NEVOA, GANHO_LONGE, DIST_LONGE, TETO_SIMULTANEOS,
  };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
```

- [ ] **Step 4: Rodar**

Run: `node tools/test_sound_bank.js`
Expected: `0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add src/soundBank.js tools/test_sound_bank.js
git diff --cached --name-only
git commit -m "feat(sons): banco de sons puro (catálogo, audibilidade, limitador, diff de estado)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Motor de reprodução e ambiente no cliente

**Files:**
- Modify: `index.html` (linha do loader de scripts)
- Modify: `game.js` (logo depois de `function _setDiceVol(v){ … }`; e `_setAmbienceVol`)
- Test: `tools/test_sons_cliente.js`

- [ ] **Step 1: Incluir o módulo no `index.html`**

Na linha do loader que contém `document.write('<script src="src/combatScene.js?v='+v+'"><\/script>');`, acrescente logo depois dela, na mesma string:

```
document.write('<script src="src/soundBank.js?v='+v+'"><\/script>');
```

(o `soundBank.js` precisa carregar antes do `game.js`, que vem mais adiante na mesma linha).

- [ ] **Step 2: Teste do motor (falha)**

Crie `tools/test_sons_cliente.js`:

```js
// tools/test_sons_cliente.js — node tools/test_sons_cliente.js
// Ganchos de som do game.js: extrai as funções REAIS e roda com stubs.
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
const GAME = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
global.window = {};
eval(fs.readFileSync(path.join(raiz, 'src', 'soundBank.js'), 'utf8'));
const SB = global.window.SoundBank;

function extrair(nome) {
  const ini = GAME.indexOf('\nfunction ' + nome + '(');
  if (ini < 0) throw new Error('função não encontrada: ' + nome);
  const fim = GAME.indexOf('\n}', ini);
  return GAME.slice(ini, fim + 2);
}
// Monta as funções pedidas num escopo com os stubs dados; devolve {nome: fn}.
function montar(nomes, stubs) {
  const corpo = nomes.map(extrair).join('\n') + '\nreturn {' + nomes.join(',') + '};';
  return new Function(...Object.keys(stubs), corpo)(...Object.values(stubs));
}

console.log('\n[1] index.html carrega o soundBank antes do game.js');
const html = fs.readFileSync(path.join(raiz, 'index.html'), 'utf8');
check('soundBank.js incluído', html.includes('src/soundBank.js'));
check('antes do game.js', html.indexOf('src/soundBank.js') < html.indexOf('"game.js?v=') || html.indexOf('src/soundBank.js') < html.indexOf("game.js?v="));

console.log('\n[2] Motor: funções existem');
for (const f of ['sfx', '_sfxCarregar', '_sfxPreCarregar', '_sfxPan', '_ambienceBus', '_ambienciaGarantir', '_ambienciaParar'])
  check('game.js define ' + f, GAME.includes('\nfunction ' + f + '('));
check('_setAmbienceVol atualiza o canal', /function _setAmbienceVol\(v\)\{[\s\S]{0,200}_ambBusNode/.test(GAME));

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
```

Run: `node tools/test_sons_cliente.js`
Expected: `[2]` com ❌ (funções ainda não existem).

- [ ] **Step 3: Implementar o motor**

Em `game.js`, localize a função

```js
function _setDiceVol(v){
  _diceVol = Math.max(0, Math.min(1, v));
  if (_diceBusNode) _diceBusNode.gain.value = _diceVol;
  _audioSavePrefs();
}
```

e acrescente **logo depois** dela:

```js

// ══ SONS GRAVADOS — banco de amostras (spec 2026-09-23-sons) ══════════════
// `sfx(evento, {pos})` devolve true quando o som foi TRATADO (tocou ou foi
// descartado pelo limitador) — o chamador então NÃO toca a síntese antiga.
// false = sem amostra pronta: o chamador usa o recuo sintetizado. O
// carregamento é assíncrono; o 1º pedido de um arquivo dispara o fetch.
const _SFX_BASE = 'assets/sfx/';
const _sfxBuffers = new Map();         // caminho -> AudioBuffer | 'carregando' | 'erro'
const _sfxUltimaVariante = new Map();  // evento -> índice tocado por último
const _sfxLimitador = window.SoundBank ? SoundBank.criarLimitador() : null;
const _sfxContagem = {};               // evento -> vezes tocado (só p/ verificação)
window._sfxContagem = _sfxContagem;
let _sfxVisaoCache = { state: null, set: null };

function _sfxCarregar(caminho){
  if(_sfxBuffers.has(caminho)) return;
  const ctx = getAudioContext(); if(!ctx) return;
  _sfxBuffers.set(caminho, 'carregando');
  fetch(_assetURL(_SFX_BASE + caminho))
    .then(r => { if(!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); })
    .then(b => ctx.decodeAudioData(b))
    .then(buf => { _sfxBuffers.set(caminho, buf); })
    .catch(e => { _sfxBuffers.set(caminho, 'erro'); console.warn('sfx:', caminho, e && e.message); });
}
function _sfxPreCarregar(){
  if(!window.SoundBank) return;
  for(const def of Object.values(SoundBank.SFX)) for(const a of def.arquivos) _sfxCarregar(a);
}
function _sfxMe(){
  const st = GS.gameState;
  return st ? ((st.players || []).find(p => String(p.id) === String(GS.myPid)) || null) : null;
}
function _sfxVisaoDe(state, me){
  if(!state) return null;
  if(_sfxVisaoCache.state === state) return _sfxVisaoCache.set;
  const set = computeVisionSet(state, me);
  _sfxVisaoCache = { state, set };
  return set;
}
// Panorâmica pela TELA, não pelo mundo: a câmera orbita, então "direita" é
// a projeção da casa na câmera. No 2D o eixo X do canvas é o X do mundo.
function _sfxPan(pos){
  let x = 0;
  if(mode3D && g3 && g3.camera && g3.T){
    x = new g3.T.Vector3(pos[0], 0, pos[1]).project(g3.camera).x;
  } else {
    const me = _sfxMe();
    if(me && Array.isArray(me.pos)) x = (pos[0] - me.pos[0]) / 12;
  }
  return Math.max(-0.6, Math.min(0.6, x * 0.6));
}
function sfx(evento, opts = {}){
  const SB = window.SoundBank;
  if(!SB || !_sfxLimitador) return false;
  const def = SB.SFX[evento];
  if(!def || def.canal !== 'efeitos' || !def.arquivos.length) return false;
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return false;
  const ultimo = _sfxUltimaVariante.has(evento) ? _sfxUltimaVariante.get(evento) : -1;
  const idx = SB.escolherVariante(def.arquivos.length, ultimo);
  const caminho = def.arquivos[idx];
  const buf = _sfxBuffers.get(caminho);
  if(!(buf instanceof AudioBuffer)){ _sfxCarregar(caminho); return false; }
  const me = _sfxMe();
  const aud = SB.audibilidade({ pos: opts.pos, visao: _sfxVisaoDe(GS.gameState, me),
    mePos: me && Array.isArray(me.pos) ? me.pos : null, mestre: GS.isMaster() });
  const jit = a => 1 + (Math.random() * 2 - 1) * (a || 0);
  const ganho = Math.max(0, def.volume * aud.ganho * jit(def.volJitter));
  const agora = performance.now();
  if(!_sfxLimitador.pode(evento, agora)) return true;
  try{
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = jit(def.pitchJitter);
    let no = src;
    if(aud.abafado){
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 900;
      no.connect(f); no = f;
    }
    if(aud.panLivre && Array.isArray(opts.pos) && ctx.createStereoPanner){
      const p = ctx.createStereoPanner(); p.pan.value = _sfxPan(opts.pos);
      no.connect(p); no = p;
    }
    const g = ctx.createGain(); g.gain.value = ganho;
    no.connect(g); g.connect(_sfxBus());
    src.start();
    _sfxUltimaVariante.set(evento, idx);
    _sfxLimitador.registrar(evento, agora, buf.duration * 1000 / src.playbackRate.value, ganho);
    _sfxContagem[evento] = (_sfxContagem[evento] || 0) + 1;
    return true;
  }catch(e){ return false; }
}

// ── Ambiente: um loop por preset da masmorra, canal "ambiente" ──────────────
let _ambBusNode = null, _ambBusCtx = null;
let _amb = null;                       // { evento, src, gain }
const _AMB_FADE_S = 2;
function _ambienceBus(){
  const ctx = getAudioContext();
  if(!ctx) return null;
  if(_ambBusCtx !== ctx || !_ambBusNode){
    _ambBusNode = ctx.createGain();
    _ambBusNode.gain.value = _ambienceVol;
    _ambBusNode.connect(ctx.destination);
    _ambBusCtx = ctx;
  }
  return _ambBusNode;
}
// Idempotente: chamado a cada game_state; só (re)começa quando o preset muda
// ou quando o arquivo terminou de carregar desde a última tentativa.
function _ambienciaGarantir(state){
  const SB = window.SoundBank;
  if(!SB || !state || GS.isPreview) return;
  const evento = SB.eventoAmbiente(state.ambiente || 'masmorra');
  if(_amb && _amb.evento === evento) return;
  const caminho = (SB.SFX[evento].arquivos || [])[0];
  if(!caminho) return;
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  const buf = _sfxBuffers.get(caminho);
  if(!(buf instanceof AudioBuffer)){ _sfxCarregar(caminho); return; }
  _ambienciaParar();
  const src = ctx.createBufferSource(); src.buffer = buf; src.loop = true;
  const g = ctx.createGain(), t = ctx.currentTime;
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(SB.SFX[evento].volume, t + _AMB_FADE_S);
  src.connect(g); g.connect(_ambienceBus()); src.start();
  _amb = { evento, src, gain: g };
}
function _ambienciaParar(){
  if(!_amb) return;
  const { src, gain } = _amb;
  _amb = null;
  const ctx = getAudioContext();
  if(!ctx) return;
  try{
    const t = ctx.currentTime;
    gain.gain.cancelScheduledValues(t);
    gain.gain.setValueAtTime(Math.max(0.0001, gain.gain.value), t);
    gain.gain.linearRampToValueAtTime(0.0001, t + _AMB_FADE_S);
    src.stop(t + _AMB_FADE_S + 0.05);
  }catch(e){}
}
```

E troque `_setAmbienceVol` inteira por:

```js
function _setAmbienceVol(v){
  _ambienceVol = Math.max(0, Math.min(1, v));
  if (_ambBusNode) _ambBusNode.gain.value = _ambienceVol;
  _audioSavePrefs();
}
```

- [ ] **Step 4: Rodar**

Run: `node --check game.js && node tools/test_sons_cliente.js`
Expected: `0 falharam`.

- [ ] **Step 5: Commit (só os arquivos limpos)**

```bash
git add index.html tools/test_sons_cliente.js
git diff --cached --name-only
git commit -m "feat(sons): carrega o banco de sons e testa o motor do cliente

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Ganchos de combate (golpe, erro, escudo, dor)

**Files:**
- Modify: `game.js` (`_receiveAttackFeedback`, `_executarComandoCena`; funções novas logo depois de `sfx`)
- Test: `tools/test_sons_cliente.js`

- [ ] **Step 1: Teste (falha)**

Em `tools/test_sons_cliente.js`, antes do `console.log(\`\n=== …`, acrescente:

```js
console.log('\n[3] _somGolpe / _somDor');
{
  const tocados = [];
  const estado = { players: [
    { id: 'h1', gear: { off_hand: { id: 'escudo_p', kind: 'shield' } } },
    { id: 'h2', gear: { off_hand: null } },
  ] };
  const f = montar(['_jogadorDaChave', '_temEscudo', '_somGolpe', '_somDor'], {
    GS: { gameState: estado },
    sfx: (e, o) => { tocados.push([e, o && o.pos]); return true; },
    _combatPrimaryDamageType: t => Array.isArray(t) ? t[0] : t,
  });
  const golpe = (c) => { tocados.length = 0; const r = f._somGolpe(c); return [r, tocados.map(x => x[0])]; };
  let [r, t] = golpe({ hit: true, impacto: 'cortante', targetPos: [1, 1], targetKey: 'm:9' });
  check('acerto cortante → golpe_cortante', r && t.join() === 'golpe_cortante');
  [r, t] = golpe({ hit: true, crit: true, impacto: 'natural', targetPos: [1, 1], targetKey: 'm:9' });
  check('crítico soma golpe_critico', t.join() === 'golpe_natural,golpe_critico');
  [r, t] = golpe({ hit: true, impacto: null, targetPos: [1, 1], targetKey: 'm:9' });
  check('sem impacto → contundente', t.join() === 'golpe_contundente');
  [r, t] = golpe({ hit: false, targetPos: [1, 1], targetKey: 'p:h1' });
  check('erro em herói com escudo → escudo_bloqueio', t.join() === 'escudo_bloqueio');
  [r, t] = golpe({ hit: false, fumble: true, targetPos: [1, 1], targetKey: 'p:h1' });
  check('falha crítica não é bloqueio → golpe_erro', t.join() === 'golpe_erro');
  [r, t] = golpe({ hit: false, targetPos: [1, 1], targetKey: 'p:h2' });
  check('erro sem escudo → golpe_erro', t.join() === 'golpe_erro');
  [r, t] = golpe({ hit: true, area: true, targetPos: [1, 1] });
  check('arremesso de área não toca golpe', r === false && t.length === 0);
  check('pos do alvo vai junto', (golpe({ hit: true, impacto: 'cortante', targetPos: [4, 5], targetKey: 'm:9' }), tocados[0][1][0] === 4));

  tocados.length = 0;
  check('dor física em herói → dor_heroi', f._somDor({ hit: true, targetKey: 'p:h1', targetPos: [1, 1] }, { damageType: ['physical'] }) && tocados[0][0] === 'dor_heroi');
  tocados.length = 0;
  check('dor física em monstro → dor_criatura', f._somDor({ hit: true, targetKey: 'm:9', targetPos: [1, 1] }, { damageType: 'physical' }) && tocados[0][0] === 'dor_criatura');
  tocados.length = 0;
  check('dano de fogo não usa dor (fica a síntese)', f._somDor({ hit: true, targetKey: 'm:9' }, { damageType: ['fire'] }) === false && tocados.length === 0);
}

console.log('\n[4] Fiação de combate');
check('base da cena leva impacto', /attacker_pos:msg\.attacker_pos, target_pos:msg\.target_pos, projectile: msg\.projectile \|\| null, impacto: msg\.impacto \|\| null/.test(GAME));
check('impact chama _somGolpe antes do cue adiado', /const tocouGolpe = !c\.tardio && _somGolpe\(c\);/.test(GAME));
check('cue adiado só toca sem amostra', /if\(f\.cueAdiado\)\{ if\(!tocouGolpe\) _playCombatCue\(f\.cueAdiado\.kind, f\.cueAdiado\.opts\); f\.cueAdiado = null; \}/.test(GAME));
check('dor tenta amostra antes da síntese', /if\(fb\.cue && !_somDor\(c, fb\)\) _playCombatCue\('damage', fb\.cue\);/.test(GAME));
check('2D (sem cena) também tenta amostra', /const tocou = _somGolpe\(\{/.test(GAME));
```

Run: `node tools/test_sons_cliente.js`
Expected: `[3]` falha com `função não encontrada: _jogadorDaChave`.

- [ ] **Step 2: Funções de gancho**

Em `game.js`, logo depois da função `sfx` (antes do comentário `// ── Ambiente:`), acrescente:

```js
function _jogadorDaChave(key){
  const k = String(key || '');
  if(!k.startsWith('p:')) return null;
  const id = k.slice(2);
  return ((GS.gameState && GS.gameState.players) || []).find(p => String(p.id) === id) || null;
}
function _temEscudo(p){
  const oh = p && p.gear && p.gear.off_hand;
  return !!oh && (oh.kind === 'shield' || oh.item_type === 'shield');
}
// c = comando `impact` da CombatScene (ou o equivalente montado no 2D).
function _somGolpe(c){
  if(!c || c.area) return false;
  const pos = Array.isArray(c.targetPos) ? c.targetPos : undefined;
  if(!c.hit){
    const bloqueio = !c.fumble && _temEscudo(_jogadorDaChave(c.targetKey));
    return sfx(bloqueio ? 'escudo_bloqueio' : 'golpe_erro', {pos});
  }
  const tocou = sfx('golpe_' + (c.impacto || 'contundente'), {pos});
  if(c.crit) sfx('golpe_critico', {pos});
  return tocou;
}
function _somDor(c, fb){
  if(!c || !c.hit) return false;
  if(_combatPrimaryDamageType(fb && fb.damageType || 'physical') !== 'physical') return false;
  const heroi = String(c.targetKey || '').startsWith('p:');
  return sfx(heroi ? 'dor_heroi' : 'dor_criatura', {pos: Array.isArray(c.targetPos) ? c.targetPos : undefined});
}
```

- [ ] **Step 3: Ligar em `_receiveAttackFeedback`**

(a) Troque

```js
      attacker_pos:msg.attacker_pos, target_pos:msg.target_pos, projectile: msg.projectile || null};
```

por

```js
      attacker_pos:msg.attacker_pos, target_pos:msg.target_pos, projectile: msg.projectile || null, impacto: msg.impacto || null};
```

(b) No objeto `const f={id, attackerName:…` da fase `start`, troque a linha

```js
      area:!!(msg.projectile && msg.projectile.area),
```

por

```js
      area:!!(msg.projectile && msg.projectile.area), impacto: msg.impacto || null,
```

(c) Troque

```js
    } else if(cue){
      _playCombatCue(cue.kind, cue.opts);
    }
    _drawAttackFeedbackTexture3D(f);
```

por

```js
    } else {
      // Sem cena (2D ou cena desligada): o golpe soa no resultado.
      const tocou = _somGolpe({ hit: !!msg.hit, crit: !!(msg.crit || msg.natural_critical),
        fumble: !!msg.natural_fumble, impacto: f.impacto, area: f.area,
        targetPos: msg.target_pos, targetKey: _entityKeyById(msg.target_id) });
      if(!tocou && cue) _playCombatCue(cue.kind, cue.opts);
    }
    _drawAttackFeedbackTexture3D(f);
```

- [ ] **Step 4: Ligar em `_executarComandoCena`**

(a) Troque

```js
  if(c.cmd !== 'impact') return;
  const now = performance.now();
  if(!c.tardio){
```

por

```js
  if(c.cmd !== 'impact') return;
  const now = performance.now();
  const tocouGolpe = !c.tardio && _somGolpe(c);
  if(!c.tardio){
```

(b) Dentro desse bloco, troque

```js
      if(f.cueAdiado){ _playCombatCue(f.cueAdiado.kind, f.cueAdiado.opts); f.cueAdiado = null; }
    }
  }
  const feedbacks = Array.isArray(c.feedbacks) ? c.feedbacks : [];
```

por

```js
      if(f.cueAdiado){ if(!tocouGolpe) _playCombatCue(f.cueAdiado.kind, f.cueAdiado.opts); f.cueAdiado = null; }
    }
  }
  const feedbacks = Array.isArray(c.feedbacks) ? c.feedbacks : [];
```

(c) Troque

```js
    if(fb.cue) _playCombatCue('damage', fb.cue);
```

por

```js
    if(fb.cue && !_somDor(c, fb)) _playCombatCue('damage', fb.cue);
```

- [ ] **Step 5: Rodar**

Run: `node --check game.js && node tools/test_sons_cliente.js && node tools/test_combat_scene.js 2>&1 | tail -1`
Expected: `0 falharam` nos dois.

- [ ] **Step 6: Commit (só o teste)**

```bash
git add tools/test_sons_cliente.js
git commit -m "test(sons): ganchos de golpe, erro, escudo e dor

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Morte de criatura, diferença de estado, escada e ambiente

**Files:**
- Modify: `game.js` (`_capturarDerrotasERessurreicoes` — 2 pontos; handlers `gameState`, `enterDungeon`, `cityState`; funções novas depois de `_somDor`)
- Test: `tools/test_sons_cliente.js`

- [ ] **Step 1: Teste (falha)**

Acrescente em `tools/test_sons_cliente.js`, antes do resumo final:

```js
console.log('\n[5] _somMorteMonstro');
{
  const tocados = [], sintese = [];
  const f = montar(['_somMorteMonstro'], {
    SoundBank: SB,
    sfx: (e) => { tocados.push(e); return true; },
    _playDefeatSound: k => sintese.push(k),
  });
  f._somMorteMonstro({ type: 'goblin', pos: [1, 1] }, 'common');
  check('goblin → morte_humanoide, sem síntese', tocados.join() === 'morte_humanoide' && sintese.length === 0);
  tocados.length = 0;
  f._somMorteMonstro({ type: 'elemental_fogo', pos: [1, 1] }, 'magic');
  check('sem família → síntese antiga', tocados.length === 0 && sintese.join() === 'magic');
}
{
  const sintese = [];
  const f = montar(['_somMorteMonstro'], { SoundBank: SB, sfx: () => false, _playDefeatSound: k => sintese.push(k) });
  f._somMorteMonstro({ type: 'goblin', pos: [1, 1] }, 'boss');
  check('amostra ausente → síntese antiga', sintese.join() === 'boss');
}

console.log('\n[6] _capturarSonsDeEstado');
{
  const tocados = [];
  const stubs = {
    SoundBank: SB,
    GS: { myPid: 'h1', doorSets: st => ({ open: new Set(st.abertas || []) }) },
    sfx: (e, o) => { tocados.push([e, o && o.pos]); return true; },
    _sfxVisaoDe: () => new Set(['2,2', '4,4']),
  };
  // O snapshot `_sonsSnap` é estado de módulo do game.js: recriado aqui, com reset.
  const src = extrair('_capturarSonsDeEstado');
  const f = new Function(...Object.keys(stubs),
    'let _sonsSnap = null;\n' + src + '\nreturn { _capturarSonsDeEstado, reset(){ _sonsSnap = null; } };')(...Object.values(stubs));
  const st = (extra) => Object.assign({ players: [{ id: 'h1', pos: [0, 0], gold: 5, bag: [], gear: {}, level: 1 }],
    monsters: [{ id: 'm1', type: 'goblin', hp: 5, pos: [2, 2] }], current_turn: 'x', abertas: [] }, extra);
  f.reset();
  f._capturarSonsDeEstado(st());
  check('1º estado não toca', tocados.length === 0);
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'] }));
  const nomes = tocados.map(x => x[0]);
  check('porta aberta e sua vez', nomes.includes('porta_abre') && nomes.includes('sua_vez'));
  check('porta leva a posição', tocados.find(x => x[0] === 'porta_abre')[1][0] === 4);
  tocados.length = 0;
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'],
    monsters: [{ id: 'm1', type: 'goblin', hp: 5, pos: [2, 2] }, { id: 'm2', type: 'lobo_cinzento', hp: 5, pos: [9, 9] }] }));
  check('monstro fora da visão NÃO ruge', tocados.length === 0);
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'],
    monsters: [{ id: 'm1', type: 'goblin', hp: 5, pos: [2, 2] }, { id: 'm2', type: 'lobo_cinzento', hp: 5, pos: [4, 4] }] }));
  check('ao entrar na visão ruge', tocados.map(x => x[0]).join() === 'rugido_fera');
  tocados.length = 0;
  f._capturarSonsDeEstado(st({ current_turn: 'h1', abertas: ['4,4'],
    monsters: [{ id: 'm3', type: 'goblin', hp: 0, pos: [2, 2] }] }));
  check('monstro morto não ruge', tocados.length === 0);
}

console.log('\n[7] Fiação de estado, morte e ambiente');
check('morte sem cena usa _somMorteMonstro', /_spawnDefeatVisual\(anterior, kind\);\s*_somMorteMonstro\(anterior, kind\);/.test(GAME));
check('morte com cena usa _somMorteMonstro', /onImpact: \[\(\) => \{ _spawnDefeatVisual\(anterior, kind\); _somMorteMonstro\(anterior, kind\); \}\]/.test(GAME));
check('gameState chama _capturarSonsDeEstado', /_detectHpChanges\(msg\);[^\n]*\n\s*_capturarSonsDeEstado\(msg\);/.test(GAME));
check('gameState garante o ambiente', /_capturarSonsDeEstado\(msg\);\s*\n\s*_ambienciaGarantir\(msg\);/.test(GAME));
check('enterDungeon zera sons e toca escada', /GS\.on\('enterDungeon'[\s\S]{0,3000}_sonsReset\(\);\s*sfx\('escada'\);/.test(GAME));
check('cityState para o ambiente e pré-carrega', /GS\.on\('cityState'[\s\S]{0,1500}_ambienciaParar\(\);\s*_sonsReset\(\);\s*_sfxPreCarregar\(\);/.test(GAME));
```

Run: `node tools/test_sons_cliente.js`
Expected: `[5]` falha com `função não encontrada: _somMorteMonstro`.

- [ ] **Step 2: Funções**

Em `game.js`, logo depois de `function _somDor(c, fb){ … }`, acrescente:

```js
function _somMorteMonstro(m, kind){
  const fam = window.SoundBank ? SoundBank.familiaDe(m) : null;
  if(fam && sfx('morte_' + fam, {pos: m && Array.isArray(m.pos) ? m.pos : undefined})) return;
  _playDefeatSound(kind);
}

// Diferença entre estados → sons de exploração/interface/rugido. A regra mora
// no SoundBank (puro); aqui só se monta a entrada a partir do game_state.
let _sonsSnap = null;
function _sonsReset(){ _sonsSnap = null; }
function _capturarSonsDeEstado(state){
  if(!window.SoundBank || !state) return;
  const me = (state.players || []).find(p => String(p.id) === String(GS.myPid)) || null;
  const visao = _sfxVisaoDe(state, me);
  const monstros = (state.monsters || [])
    .filter(m => m && m.hp > 0 && Array.isArray(m.pos) && (!visao || visao.has(`${m.pos[0]},${m.pos[1]}`)))
    .map(m => ({ id: m.id, type: m.type, size: m.size, pos: m.pos }));
  const r = SoundBank.diffSons(_sonsSnap, {
    portas: [...GS.doorSets(state).open],
    me: me ? { ouro: me.gold, bag: me.bag, gear: me.gear, nivel: me.level } : null,
    meuTurno: state.current_turn === GS.myPid,
    missao: !!state.mission_complete_pending,
    monstros,
  });
  _sonsSnap = r.snap;
  for(const e of r.eventos) sfx(e.evento, e.pos ? { pos: e.pos } : {});
}
```

- [ ] **Step 3: Trocar o som de morte nos 2 pontos de monstro**

Em `_capturarDerrotasERessurreicoes` (procure pelo texto), troque

```js
    if(!comCena){
      _spawnDefeatVisual(anterior, kind);
      _playDefeatSound(kind);
    }
```

por

```js
    if(!comCena){
      _spawnDefeatVisual(anterior, kind);
      _somMorteMonstro(anterior, kind);
    }
```

e troque

```js
        onImpact: [() => { _spawnDefeatVisual(anterior, kind); _playDefeatSound(kind); }],
```

por

```js
        onImpact: [() => { _spawnDefeatVisual(anterior, kind); _somMorteMonstro(anterior, kind); }],
```

(As chamadas com `'hero'` e `'magic'` ficam como estão.)

- [ ] **Step 4: Handlers**

(a) Em `GS.on('gameState', msg => {`, troque

```js
  _detectHpChanges(msg);   // som de dano/cura por variação de HP entre estados
```

por

```js
  _detectHpChanges(msg);   // som de dano/cura por variação de HP entre estados
  _capturarSonsDeEstado(msg);
  _ambienciaGarantir(msg);
```

(b) Em `GS.on('enterDungeon', (msg) => {`, troque

```js
  _hpSnapshot.clear();   // novo cenário: zera HP base (1º game_state não dispara som)
```

por

```js
  _hpSnapshot.clear();   // novo cenário: zera HP base (1º game_state não dispara som)
  _sfxPreCarregar();
  _sonsReset(); sfx('escada');
```

(c) Em `GS.on('cityState', msg => {`, troque

```js
  _hpSnapshot.clear();   // de volta à cidade: zera HP base p/ a próxima masmorra
```

por

```js
  _hpSnapshot.clear();   // de volta à cidade: zera HP base p/ a próxima masmorra
  _ambienciaParar(); _sonsReset(); _sfxPreCarregar();
```

e, no mesmo handler, logo depois da linha `if(vindoDaMasmorra) _resetTrapPopup();`, acrescente:

```js
  if(vindoDaMasmorra) sfx('escada');
```

- [ ] **Step 5: Rodar**

Run: `node --check game.js && node tools/test_sons_cliente.js`
Expected: `0 falharam`.

- [ ] **Step 6: Commit (só o teste)**

```bash
git add tools/test_sons_cliente.js
git commit -m "test(sons): morte de criatura, diferença de estado, escada e ambiente

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Interface — recusa, clique e o `serverError` duplicado

**Contexto:** `GS.on` substitui o ouvinte. Hoje existem dois `GS.on('serverError', …)` no `game.js`; o primeiro (só `if(window._ataqueGiratorioPreview) _limparPreviewAtaqueGiratorio();`) **nunca roda** — bug existente: a prévia do Ataque Giratório fica presa quando o servidor recusa a técnica. Esta tarefa funde os dois e acrescenta o som de recusa.

**Files:**
- Modify: `game.js`
- Test: `tools/test_sons_cliente.js`

- [ ] **Step 1: Teste (falha)**

Acrescente antes do resumo final:

```js
console.log('\n[8] Interface');
const regs = GAME.match(/GS\.on\('serverError'/g) || [];
check('um único GS.on(serverError)', regs.length === 1);
check('o ouvinte único limpa a prévia do Ataque Giratório',
  /GS\.on\('serverError', msg  => \{[\s\S]{0,300}_limparPreviewAtaqueGiratorio\(\)/.test(GAME));
check('o ouvinte único toca recusa', /GS\.on\('serverError', msg  => \{[\s\S]{0,400}sfx\('recusa'\)/.test(GAME));
check('clique delegado em botões', /closest\('button'\)[\s\S]{0,80}sfx\('clique'\)/.test(GAME));
console.log('\n[9] Nenhum GS.on duplicado no game.js');
const nomes = [...GAME.matchAll(/^GS\.on\('([A-Za-z_]+)'/gm)].map(m => m[1]);
const dup = nomes.filter((n, i) => nomes.indexOf(n) !== i);
check('sem duplicatas (GS.on substitui o anterior): ' + (dup.join(',') || 'ok'), dup.length === 0);
```

Run: `node tools/test_sons_cliente.js`
Expected: `[8]`/`[9]` com ❌ (há 2 registros).

- [ ] **Step 2: Fundir os ouvintes**

Apague o bloco

```js
GS.on('serverError', () => {
  if(window._ataqueGiratorioPreview) _limparPreviewAtaqueGiratorio();
});

```

e, no outro, troque

```js
GS.on('serverError', msg  => {
  if(window._modoInstrumento) _encerrarMiraInstrumento();
```

por

```js
GS.on('serverError', msg  => {
  // ÚNICO ouvinte: GS.on substitui o anterior (um 2º registro apagava este).
  if(window._ataqueGiratorioPreview) _limparPreviewAtaqueGiratorio();
  sfx('recusa');
  if(window._modoInstrumento) _encerrarMiraInstrumento();
```

- [ ] **Step 3: Clique delegado**

Logo depois de `function _ambienciaParar(){ … }`, acrescente:

```js
// Clique de botão: um ouvinte só, em captura, para toda a interface.
document.addEventListener('click', e => {
  const b = e.target && e.target.closest && e.target.closest('button');
  if(b && !b.disabled) sfx('clique');
}, true);
```

- [ ] **Step 4: Rodar**

Run: `node --check game.js && node tools/test_sons_cliente.js`
Expected: `0 falharam`.

- [ ] **Step 5: Commit (só o teste)**

```bash
git add tools/test_sons_cliente.js
git commit -m "test(sons): recusa, clique e ouvinte único de serverError

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Pacotes CC0 — aprovação, download e preparação

**GATE:** nenhum download antes de o autor aprovar a lista no chat.

**Files:**
- Create: `tools/preparar_sfx.py`, `tools/test_sfx_arquivos.js`, `assets/sfx/**`, `assets/sfx/LICENCAS.md`
- Modify: `src/soundBank.js` (listas `arquivos` para o que foi de fato produzido)

- [ ] **Step 1: Levantar tamanho e licença (sem baixar)**

Para cada pacote, abra a página com WebFetch e anote licença, nome do ZIP e tamanho:
- https://kenney.nl/assets/rpg-audio
- https://kenney.nl/assets/impact-sounds
- https://kenney.nl/assets/interface-sounds
- https://kenney.nl/assets/music-jingles
- https://opengameart.org/content/80-cc0-creature-sfx
- https://opengameart.org/content/80-cc0-creture-sfx-2
- https://opengameart.org/content/monster-sound-pack-volume-1
- https://opengameart.org/content/loopable-dungeon-ambience
- Busca por CC0 em opengameart.org para: "fire crackling loop" (penumbra), "forest ambience loop" (ar livre), "sword swish/whoosh" (golpe_erro), "male grunt pain" (dor_heroi), "drink potion gulp" (beber).

Só entra pacote cuja página diga **CC0** explicitamente.

- [ ] **Step 2: Pedir aprovação**

Mostre ao autor uma tabela `pacote | licença | arquivo | tamanho | para quê` e pergunte se pode baixar. **Pare aqui até o "sim".**

- [ ] **Step 3: Baixar para o scratchpad (fora do repositório)**

Para cada pacote aprovado (ex.: Kenney usa `https://kenney.nl/media/pages/assets/<pacote>/…/kenney_<pacote>.zip` — pegue o link real da página):

```bash
mkdir -p "$SCRATCH/sfx_src" && cd "$SCRATCH/sfx_src"
curl -L -o kenney_rpg-audio.zip "<link real>"
unzip -o -q kenney_rpg-audio.zip -d rpg-audio
```

(`$SCRATCH` = o scratchpad da sessão.) Liste o conteúdo com `find . -name "*.ogg" -o -name "*.wav" | sort`.

- [ ] **Step 4: Script de preparação**

Crie `tools/preparar_sfx.py`:

```python
"""Prepara um som para assets/sfx/ (spec 2026-09-23-sons).
Uso: python tools/preparar_sfx.py <origem> <destino relativo a assets/sfx> [--loop] [--stereo]
- efeito: corta silêncio nas pontas, loudness -18 LUFS, mono, .ogg q4
- --loop: sem corte; loudness -26 LUFS; emenda com crossfade de 1 s (o fim
  funde no começo), estéreo."""
import os, subprocess, sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def preparar(origem, destino, loop=False, stereo=False):
    saida = os.path.join(RAIZ, "assets", "sfx", destino)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    if loop:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", origem, "-filter_complex",
               "[0]atrim=0:1,asetpts=PTS-STARTPTS[cab];[0]atrim=1,asetpts=PTS-STARTPTS[corpo];"
               "[corpo][cab]acrossfade=d=1,loudnorm=I=-26:TP=-3:LRA=11[o]",
               "-map", "[o]", "-ac", "2", "-c:a", "libvorbis", "-q:a", "3", saida]
    else:
        filtro = ("silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                  "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                  "loudnorm=I=-18:TP=-2:LRA=7")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", origem, "-af", filtro,
               "-ac", "2" if stereo else "1", "-c:a", "libvorbis", "-q:a", "4", saida]
    subprocess.run(cmd, check=True)
    return os.path.getsize(saida)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    tam = preparar(args[0], args[1], loop="--loop" in sys.argv, stereo="--stereo" in sys.argv)
    print(f"{args[1]}  {tam/1024:.1f} KB")
```

- [ ] **Step 5: Escolher e converter**

Para cada evento do catálogo, escolha no pacote os arquivos pelo nome (ponto de partida, **confira os nomes reais** na listagem do Step 3):

| Evento | Pacote | Candidatos |
|---|---|---|
| golpe_cortante | RPG Audio | `knifeSlice`, `knifeSlice2`, `chop` |
| golpe_perfurante | Impact Sounds | `impactSoft_medium_000..002` |
| golpe_contundente | Impact Sounds | `impactPunch_heavy_000..002` |
| golpe_natural | Impact Sounds | `impactSoft_heavy_000..002` |
| golpe_critico | Impact Sounds | `impactPlate_heavy_000..001` |
| escudo_bloqueio | Impact Sounds | `impactMetal_heavy_000..001` |
| golpe_erro / dor_heroi / beber | busca CC0 do Step 1 | — |
| dor_criatura | 80 CC0 creature SFX | gemidos curtos |
| porta_abre | RPG Audio | `doorOpen_1`, `doorOpen_2`, `creak1` |
| moedas | RPG Audio | `handleCoins`, `handleCoins2` |
| item_pegar | RPG Audio | `handleSmallLeather`, `dropLeather` |
| equipar | RPG Audio | `cloth1`, `cloth2`, `metalLatch` |
| escada | RPG Audio | `footstep00`, `footstep01` |
| rugido_* / morte_* | creature SFX / Monster Sound Pack | 2 por família |
| sua_vez / clique / recusa | Interface Sounds | `confirmation_001`, `click_002`/`click_003`, `error_004` |
| nivel / objetivo | Music Jingles | um jingle curto cada |
| amb_masmorra | Loopable Dungeon Ambience | `dungeon_ambient_1.ogg` (já é loop: use `--loop` mesmo assim só se houver clique na emenda) |
| amb_penumbra / amb_ar_livre | busca CC0 do Step 1 | 1 loop cada, `--loop` |

Converta cada um, nomeando **exatamente** como no catálogo (`combate/golpe_cortante_1.ogg`, …):

```bash
python tools/preparar_sfx.py "$SCRATCH/sfx_src/rpg-audio/Audio/knifeSlice.ogg" combate/golpe_cortante_1.ogg
```

Se um evento ficar com menos arquivos do que o catálogo prevê (ou nenhum), **ajuste a lista `arquivos` desse evento em `src/soundBank.js`** para os arquivos que existem (lista vazia é permitida: o evento cai na síntese ou fica em silêncio). Não crie arquivo de enchimento.

- [ ] **Step 6: Registrar licenças**

Crie `assets/sfx/LICENCAS.md` com uma linha por arquivo: `arquivo | pacote | autor | licença | URL | arquivo original`.

- [ ] **Step 7: Teste de consistência**

Crie `tools/test_sfx_arquivos.js`:

```js
// tools/test_sfx_arquivos.js — catálogo × pasta assets/sfx/.
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
global.window = {};
eval(fs.readFileSync(path.join(raiz, 'src', 'soundBank.js'), 'utf8'));
const SB = global.window.SoundBank;
const base = path.join(raiz, 'assets', 'sfx');

const noCatalogo = new Set();
for (const def of Object.values(SB.SFX)) for (const a of def.arquivos) noCatalogo.add(a);
const naPasta = new Set();
(function varrer(dir, rel) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const r = rel ? rel + '/' + e.name : e.name;
    if (e.isDirectory()) varrer(path.join(dir, e.name), r); else naPasta.add(r);
  }
})(base, '');
naPasta.delete('LICENCAS.md');

const faltando = [...noCatalogo].filter(a => !naPasta.has(a));
const orfaos = [...naPasta].filter(a => !noCatalogo.has(a));
check('todo arquivo do catálogo existe: ' + (faltando.join(', ') || 'ok'), faltando.length === 0);
check('nenhum arquivo órfão na pasta: ' + (orfaos.join(', ') || 'ok'), orfaos.length === 0);
check('tudo é .ogg', [...naPasta].every(a => a.endsWith('.ogg')));
const licencas = fs.readFileSync(path.join(base, 'LICENCAS.md'), 'utf8');
const semLicenca = [...naPasta].filter(a => !licencas.includes(a));
check('todo arquivo está no LICENCAS.md: ' + (semLicenca.join(', ') || 'ok'), semLicenca.length === 0);
let efeitos = 0;
for (const a of naPasta) if (!a.startsWith('ambiente/')) efeitos += fs.statSync(path.join(base, a)).size;
check(`efeitos < 3 MB (${(efeitos / 1048576).toFixed(2)} MB)`, efeitos < 3 * 1048576);
for (const a of naPasta) if (a.startsWith('ambiente/'))
  check(`${a} < 2 MB`, fs.statSync(path.join(base, a)).size < 2 * 1048576);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
```

Run: `node tools/test_sfx_arquivos.js && node tools/test_sound_bank.js`
Expected: `0 falharam` nos dois.

- [ ] **Step 8: Commit**

```bash
git add assets/sfx tools/preparar_sfx.py tools/test_sfx_arquivos.js src/soundBank.js
git diff --cached --name-only
git commit -m "feat(sons): amostras CC0 preparadas + registro de licenças

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Verificação no navegador, documentação e bateria

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Subir e abrir**

Reinicie o servidor (um servidor antigo na 8765 mostra código velho) e abra o jogo com `preview_start` (`iniciar` do `.claude/launch.json`, ou crie a entrada: `python server.py`, porta 8765). Recarregue com `?v=<algo>` e confirme no console que `typeof SoundBank === 'object'` e `typeof sfx === 'function'`.

- [ ] **Step 2: Roteiro**

Crie sala, escolha um guerreiro com escudo, entre numa masmorra e, via `javascript_tool`, leia `window._sfxContagem` depois de cada ação:

| Ação | Esperado em `_sfxContagem` |
|---|---|
| entrar na masmorra | `escada` +1 (a partir da 2ª entrada — na 1ª o buffer ainda carrega) |
| andar até ver um monstro | `rugido_<familia>` +1, uma vez só |
| abrir porta | `porta_abre` +1 |
| atacar e acertar | `golpe_<impacto>` +1 e `dor_criatura` +1 |
| atacar e errar | `golpe_erro` +1 |
| ser atacado e o monstro errar (com escudo) | `escudo_bloqueio` +1 |
| matar o monstro | `morte_<familia>` +1 |
| abrir baú e pegar ouro | `moedas` +1 |
| turno volta para você | `sua_vez` +1 |
| clicar num botão | `clique` +1 |
| ação recusada (ex.: atacar fora do turno) | `recusa` +1 |

Ambiente: confirme `_amb.evento === 'amb_masmorra'` (ou o preset da masmorra) e que `_amb` fica `null` ao voltar à cidade. Névoa: numa sessão com dois clientes, um herói abre porta fora da visão do outro; no outro, verifique com um `console.log` temporário em `sfx` que `aud.abafado === true` (remova o log depois).

Confira `read_console_messages` sem erros e `read_network_requests` sem 404 em `assets/sfx/`.

- [ ] **Step 3: Documentar no CLAUDE.md**

Acrescente ao fim do `CLAUDE.md` (Edit — arquivo em CRLF):

```markdown
> **Sons e efeitos sonoros (2026-09-23):** amostras CC0 em `assets/sfx/<grupo>/` para
> combate físico, exploração/loot, criaturas, interface e ambiente; as magias seguem
> sintetizadas. **`src/soundBank.js`** (puro, `window.SoundBank`) guarda o catálogo `SFX`
> (`evento → {arquivos, volume, intervaloMs, pitchJitter, volJitter, canal}`), `familiaDe`
> (tipo de monstro → humanoide/fera/morto_vivo/reptil_inseto/grande; `null` = sem voz),
> `audibilidade` (fora da visão: 0,35, abafado, sem pan; mestre nunca abafado),
> `escolherVariante`, `criarLimitador` (intervalo por evento, teto 8 simultâneos) e
> `diffSons` (porta/ouro/bolsa/equipar/poção/nível/turno/objetivo/rugido por diferença de
> estado). No `game.js`, **`sfx(evento, {pos})`** devolve `true` quando tratou o som e
> `false` quando não há amostra pronta — nesse caso o chamador toca a síntese antiga
> (`_playCombatCue`, `_playDefeatSound`): nada fica mudo. O pan é pela projeção na câmera
> (a câmera orbita). Ambiente: `_ambienciaGarantir(state)` (idempotente, a cada
> `game_state`) toca o loop do preset `ambiente` no canal "ambiente"; `_ambienciaParar` na
> cidade. Servidor: só o campo opcional **`impacto`** (`cortante|perfurante|contundente|
> natural`) no `attack_feedback start`, por `_impacto_de` ao lado de `_projetil_de`.
> **`GS.on` substitui o ouvinte anterior** — havia dois `GS.on('serverError')` e o primeiro
> (limpar a prévia do Ataque Giratório) nunca rodava; foram fundidos, e
> `tools/test_sons_cliente.js` [9] proíbe `GS.on` duplicado. Trocar um som = trocar o
> arquivo; mudar volume = número no catálogo. Testes: `tools/test_sound_bank.js`,
> `tools/test_sons_cliente.js`, `tools/test_sons_impacto.py`, `tools/test_sfx_arquivos.js`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-09-23-sons-efeitos-sonoros*`.
```

- [ ] **Step 4: Bateria**

```bash
for f in tools/test_*.py; do PYTHONIOENCODING=utf-8 timeout 400 python "$f" > /dev/null 2>&1 || echo "FALHOU $f"; done
for f in tools/test_*.js; do node "$f" > /dev/null 2>&1 || echo "FALHOU $f"; done
python tools/dividas.py | grep TOTAL
```

Expected: nenhuma falha nova. (Falhas já existentes antes deste plano: `test_interface.py` com os 2 rótulos de GLB do WIP e `test_mira_joystick.js` com o `rangeFill` do WIP — confira se continuam sendo só essas.)

- [ ] **Step 5: Entregar ao autor**

Diga ao autor que `game.js`, `server.py` e `CLAUDE.md` ficaram no working tree (misturados com o WIP dele) e que a avaliação de ouvido é dele: trocar arquivo em `assets/sfx/` ou volume em `src/soundBank.js`.
