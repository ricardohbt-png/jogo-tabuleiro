# Tutorial guiado — fatia 6 (feedback do Lucas) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Textos de passo que dizem o que fazer, sinal visível de passo/lição concluída, recompensa pequena (ouro+XP) uma vez por personagem, e duas lições novas (atalhos; resistência e vulnerabilidade).

**Architecture:** Mesmo molde das fatias 3–5. Servidor: `_guia_avancar` e `_licao_concluir` (em `server.py`) passam a emitir `licao_passo_ok`/`licao_concluida`; `_licao_concluir` paga a recompensa só na 1ª conclusão (guarda `tutorial_history`). Cliente: `src/gameState.js` repassa as mensagens, `game.js` desenha ✓/selo. Conteúdo novo em `tools/tutorial_guia_comum.py` → `tools/gerar_guia_comum.py` → `src/lang/tutorial_guia.js`; lições novas autoradas em `tools/configurar_tutorial_salas.py`.

**Tech Stack:** Python (server.py, unittest), JS vanilla (game.js, node para testes), JSON de masmorra.

**Spec:** `docs/superpowers/specs/2026-10-07-tutorial-guiado-fatia6-design.md`. **Desvio do spec:** sem campo `recompensa` por lição (YAGNI; evitaria tocar `tools/editor.js`, que tem WIP do autor). Só as constantes globais.

## Regras do repositório (valem para TODAS as tarefas)

- `game.js`, `server.py`, `CLAUDE.md` estão em **CRLF**: use a ferramenta Edit, nunca `replace` multilinha em script.
- **Não toque** o WIP do autor: `src/soundBank.js`, `tools/editor.js`, e os demais `M` do `git status` que não forem seus. `git add` **só com caminhos explícitos**; para arquivo com WIP do autor no mesmo arquivo (`game.js`, `server.py`, `src/gameState.js`, `src/lang/*.js`), confira `git diff -U0 <arquivo>` e commite só seus trechos (índice = HEAD + seus hunks; veja a nota do Task 4 da fatia 5 em `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia5-editor.md`: o `git apply` falha com CRLF no stdin do Windows, monte o índice por outro caminho).
- Nunca toque `savegames/`, `accounts/`, `groups/` reais. Prova no navegador: servidor isolado (porta 8794) com cópia dos dados em `%TEMP%` e `LFH_PORT`; não pare o servidor do usuário na 8765.
- Commits terminam com `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Sem push.
- Não crave contagens de catálogo em teste. `t` local sombreia o tradutor em `game.js`: nunca declare `const t`.
- O sistema de cores de dano (RESISTIDO/VULNERÁVEL…) está no worktree `codex/ceu-abismo`, **fora do master**. Esta fatia não depende dele (Task 6).

## Mapa de arquivos

| Arquivo | Mudança |
|---|---|
| `server.py` | constantes de recompensa; `_licao_concluir` paga e avisa; `_guia_avancar` avisa `licao_passo_ok` |
| `src/gameState.js` | `case 'licao_passo_ok'` / `'licao_concluida'` → `_emit` |
| `game.js`, `game.css` | ✓ animado, selo da lição, sons; `GS.on('licaoPassoOk'/'licaoConcluida')` |
| `src/lang/tutorial.js` | textos do ✓/selo/recompensa; glossário `vulnerabilidade` (cat. do glossário fica em `tutorial_guia.js`, gerado) |
| `tools/tutorial_guia_comum.py` | reescrita dos passos vagos; 3 lições novas; glossário |
| `tools/configurar_tutorial_salas.py` | falas novas + 2º esqueleto |
| `tools/test_tutorial_conteudo.py`, `test_tutorial_guia.py`, `test_guia_tutorial_cliente.js` | testes novos |
| `dungeons/campo_de_treinamento.json`, `src/lang/tutorial_guia.js` | gerados |

---

### Task 1: Auditoria dos textos vagos e teste de redação

**Files:**
- Modify: `tools/test_tutorial_conteudo.py`
- Modify: `tools/tutorial_guia_comum.py`, `tools/tutorial_guia_{guerreiro,mago,ladino,clerigo,bardo,paladino}.py`, `src/lang/tutorial.js` (`ui.tutorial.modelo.*`)

O "Me mostra" só destaca o elemento: o **texto** do passo precisa trazer o verbo de ação e o alvo. Passo informativo (não-último, sem `conclui`) pode explicar, mas se tem `ui` também precisa de verbo.

- [ ] **Step 1: Escrever o teste (vai falhar)**

Em `tools/test_tutorial_conteudo.py`, acrescentar antes de `if __name__` (ou no fim da classe `ConteudoTests`):

```python
VERBOS_PT = ("clique", "ande", "ataque", "equipe", "abra", "use", "beba", "coma", "pegue",
             "arraste", "selecione", "escolha", "encerre", "aperte", "pressione", "lance",
             "arremesse", "unte", "ative", "desative", "fique", "aproxime", "toque", "arme",
             "cure", "derrube", "acerte", "esconda", "desarme", "crie", "comande", "liberte",
             "proteja", "passe", "confira", "leia", "mova", "gire", "cancele", "troque")
VAGOS_PT = ("mostre-me", "me mostra", "mostre", "demonstre", "veja como", "observe")


def _primeira_palavra(pt):
    return re.sub(r"\[\[[a-z0-9_]+\]\]", "x", pt).strip().lower().split()[0].strip(".,:;!?")


class RedacaoAcionavelTests(unittest.TestCase):
    def _todos(self):
        for modulo in G.modulos_de_guia():           # {lid: [passos]}
            for lid, passos in modulo.items():
                for p in passos:
                    yield lid, p

    def test_todo_passo_com_ui_comeca_por_verbo_de_acao(self):
        ruins = [f"{lid}/{p['id']}: {p['texto'][0]!r}" for lid, p in self._todos()
                 if p.get("ui") and _primeira_palavra(p["texto"][0]) not in VERBOS_PT]
        self.assertEqual(ruins, [], "\n".join(ruins))

    def test_nenhum_texto_pede_para_so_mostrar(self):
        ruins = [f"{lid}/{p['id']}: {p['texto'][0]!r}" for lid, p in self._todos()
                 if any(p["texto"][0].lower().startswith(v) for v in VAGOS_PT)]
        self.assertEqual(ruins, [], "\n".join(ruins))
```

`G.modulos_de_guia()` não existe: abrir `tools/gerar_guia_comum.py`, ver como `guia_todos()` junta os módulos (`tutorial_guia_comum.GUIA` + `tutorial_guia_<classe>.GUIA`) e **extrair** a lista de dicts para uma função `modulos_de_guia()` que `guia_todos()` passa a usar (refactor sem mudar comportamento).

- [ ] **Step 2: Rodar e ver a lista de ofensores**

Run: `python tools/test_tutorial_conteudo.py -v 2>&1 | tail -60`
Expected: FAIL com a lista `lição/passo: 'texto'`. Essa lista é o trabalho do Step 3.

- [ ] **Step 3: Reescrever cada ofensor**

Para cada linha da lista, editar o texto `(pt, en)` no módulo da lição: começar por um verbo da lista com o alvo concreto, ≤15 palavras (regra existente), mantendo `[[termos]]` e paridade pt/en. Exemplos do padrão:
`"Veja seu [[movimento]]…"` → `"Confira seu [[movimento]] no painel: são os passos deste [[turno]]."`;
`"Observe o resultado…"` → `"Leia o resultado do ataque no quadro de dados."`.
Não altere `id`, `ui`, `conclui`. Para as lições geradas, editar `ui.tutorial.modelo.*` em `src/lang/tutorial.js` pelo mesmo critério (`guild.repita`, `magia.abrir`, `magia.lancar`, `guild.aprendeu` devem começar por verbo de ação).

- [ ] **Step 4: Regerar e rodar tudo**

```bash
python tools/gerar_guia_comum.py
python tools/test_tutorial_conteudo.py
python tools/test_tutorial_classes.py
python tools/test_tutorial_modelos.py
python tools/test_idioma.py
```
Expected: todos OK (inclui `test_arquivo_gerado_esta_em_dia`).

- [ ] **Step 5: Commit**

```bash
git add tools/test_tutorial_conteudo.py tools/gerar_guia_comum.py tools/tutorial_guia_*.py src/lang/tutorial_guia.js src/lang/tutorial.js dungeons/campo_de_treinamento.json
git commit -m "feat(tutorial): passos com verbo de ação (fim do 'mostre-me' sem instrução)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
(Conferir antes que `src/lang/tutorial.js` e os outros não têm WIP do autor: `git diff -U0 <arquivo>`.)

---

### Task 2: Servidor — recompensa e mensagens de conclusão

**Files:**
- Modify: `server.py` (constantes perto de `LICAO_VERBOS`, linha ~44; `_licao_concluir` ~18138; `_guia_avancar` ~18150)
- Test: `tools/test_tutorial_guia.py`

- [ ] **Step 1: Escrever os testes (falham)**

Acrescentar em `tools/test_tutorial_guia.py` (usa `room`, `abrir_licao` já existentes):

```python
class RecompensaTests(unittest.TestCase):
    def _concluir(self, r, p, ident):
        lic = next(f for f in r.licoes if f['id'] == ident)
        asyncio.run(r._licao_concluir(p, lic))
        return lic

    def test_primeira_conclusao_paga_e_avisa(self):
        r, p = room()
        ouro, xp = p['gold'], p['xp']
        self._concluir(r, p, 'treino_mira')
        self.assertEqual(p['gold'], ouro + S.TUTORIAL_RECOMPENSA_OURO)
        msg = next(m for m in r.messages if m['type'] == 'licao_concluida')
        self.assertEqual(msg['licao_id'], 'treino_mira')
        self.assertEqual(msg['recompensa']['ouro'], S.TUTORIAL_RECOMPENSA_OURO)
        self.assertEqual(msg['recompensa']['xp'], S.TUTORIAL_RECOMPENSA_XP)

    def test_repetir_nao_paga_de_novo(self):
        r, p = room()
        self._concluir(r, p, 'treino_mira')
        ouro = p['gold']; r.messages.clear()
        self._concluir(r, p, 'treino_mira')
        self.assertEqual(p['gold'], ouro)
        msg = next(m for m in r.messages if m['type'] == 'licao_concluida')
        self.assertEqual(msg['recompensa'], {'ouro': 0, 'xp': 0, 'trilha': False})

    def test_fora_do_modo_treino_nao_paga(self):
        r, p = room()
        r.training_mode = False
        ouro = p['gold']
        self._concluir(r, p, 'treino_mira')
        self.assertEqual(p['gold'], ouro)

    def test_bonus_de_trilha_quando_fecha_a_ultima_licao_da_classe(self):
        r, p = room()
        lics = [f for f in r.licoes if f.get('classe') == 'warrior']
        for f in lics[:-1]:
            self._concluir(r, p, f['id'])
        ouro = p['gold']; r.messages.clear()
        self._concluir(r, p, lics[-1]['id'])
        msg = next(m for m in r.messages if m['type'] == 'licao_concluida')
        self.assertTrue(msg['recompensa']['trilha'])
        self.assertEqual(p['gold'], ouro + S.TUTORIAL_RECOMPENSA_OURO + S.TUTORIAL_BONUS_TRILHA_OURO)


class PassoOkTests(unittest.TestCase):
    def test_avancar_avisa_o_passo_concluido(self):
        r, p = room(guia=GUIA_MIRA)
        asyncio.run(abrir_licao(r, p, 'treino_mira'))
        r.messages.clear()
        lic = next(f for f in r.licoes if f['id'] == 'treino_mira')
        asyncio.run(r._guia_avancar(p, lic))
        tipos = [m['type'] for m in r.messages]
        self.assertEqual(tipos, ['licao_passo_ok', 'licao_passo'])
        ok = r.messages[0]
        self.assertEqual((ok['licao_id'], ok['passo'], ok['total']), ('treino_mira', 0, 3))
```

Run: `python tools/test_tutorial_guia.py -v 2>&1 | tail -20` — Expected: FAIL (`TUTORIAL_RECOMPENSA_OURO` não existe).

- [ ] **Step 2: Constantes**

Após a tupla `LICAO_VERBOS` em `server.py`:

```python
# Recompensa por lição do Campo de Treinamento: paga uma vez por personagem
# (a guarda é o `tutorial_history`, que sobrevive ao `repetir_tutorial`).
TUTORIAL_RECOMPENSA_OURO = 5
TUTORIAL_RECOMPENSA_XP = 10
TUTORIAL_BONUS_TRILHA_OURO = 25
TUTORIAL_BONUS_TRILHA_XP = 50
```

- [ ] **Step 3: `_licao_concluir` paga e avisa**

Substituir o método (Edit; manter CRLF) por:

```python
    async def _licao_concluir(self, p, lic):
        """Marca a lição como cumprida por este jogador e pela sala; na 1ª vez
        deste personagem (tutorial_history) paga a recompensa."""
        feitas = p.setdefault("licoes_feitas", [])
        if lic["id"] not in feitas:
            feitas.append(lic["id"])
        self.licoes_feitas.add(lic["id"])
        premio = {"ouro": 0, "xp": 0, "trilha": False}
        if self.training_mode:
            history = p.setdefault("tutorial_history", [])
            if lic["id"] not in history:
                history.append(lic["id"])
                premio["ouro"] = TUTORIAL_RECOMPENSA_OURO
                premio["xp"] = TUTORIAL_RECOMPENSA_XP
                cls = lic.get("classe")
                if cls and cls == p.get("class_id"):
                    da_classe = [l["id"] for l in self.licoes if l.get("classe") == cls]
                    if all(i in feitas for i in da_classe):
                        premio["trilha"] = True
                        premio["ouro"] += TUTORIAL_BONUS_TRILHA_OURO
                        premio["xp"] += TUTORIAL_BONUS_TRILHA_XP
                p["gold"] = int(p.get("gold", 0) or 0) + premio["ouro"]
                p["xp"] = int(p.get("xp", 0) or 0) + premio["xp"]
                await self._check_level_up(p)
        if p.get("licao_atual") == lic["id"]:
            p["licao_atual"] = None
            p["licao_passo"] = 0
        if self.training_mode and lic.get("tarefa"):
            await self.send_to(p["id"], {"type": "licao_concluida",
                                         "licao_id": lic["id"], "recompensa": premio})
```

- [ ] **Step 4: `_guia_avancar` avisa o passo concluído**

```python
    async def _guia_avancar(self, p, lic):
        passos = _guia_passos(lic)
        antes = int(p.get("licao_passo", 0) or 0)
        p["licao_passo"] = min(antes + 1, len(passos) - 1)
        await self.send_to(p["id"], {"type": "licao_passo_ok", "licao_id": lic["id"],
                                     "passo": antes, "total": len(passos)})
        await self.send_to(p["id"], {"type": "licao_passo", "licao_id": lic["id"],
                                     "passo": _guia_payload(lic, p["licao_passo"])})
```

- [ ] **Step 5: Rodar**

```bash
python tools/test_tutorial_guia.py
python tools/test_tutorial_salas.py
python tools/test_tutorial_classes.py
```
Expected: OK (se um teste antigo contava `messages` exatos, ajuste-o para ignorar `licao_passo_ok`).

- [ ] **Step 6: Commit** (só os trechos seus em `server.py`; veja as regras)

```bash
git commit -m "feat(tutorial): recompensa por lição (uma vez por personagem) e avisos de passo/lição concluídos

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- server.py tools/test_tutorial_guia.py
```
(Use o procedimento de commit parcial se `git diff -U0 server.py` mostrar WIP do autor.)

---

### Task 3: Cliente — ✓ animado, selo da lição e sons

**Files:**
- Modify: `src/gameState.js` (junto de `case 'licao_passo'`, ~1876), `game.js` (junto de `GS.on('licaoPasso'…)`, ~54178), `game.css` (junto de `#licao-janela`, ~1823), `src/lang/tutorial.js`
- Test: `tools/test_guia_tutorial_cliente.js`

A barra "Passo i de n" **já existe** em `_mostrarJanelaLicao`; falta o ✓ no passo concluído e o selo no fim.

- [ ] **Step 1: Textos** (em `src/lang/tutorial.js`, dentro de `window.LANG_TUTORIAL`)

```js
  "ui.tutorial.passo_ok": { "pt": "Passo concluído!", "en": "Step complete!" },
  "ui.tutorial.licao_concluida": { "pt": "Lição concluída!", "en": "Lesson complete!" },
  "ui.tutorial.recompensa": { "pt": "+{ouro} ouro · +{xp} XP", "en": "+{ouro} gold · +{xp} XP" },
  "ui.tutorial.recompensa_trilha": { "pt": "Trilha completa! Bônus incluído.", "en": "Track complete! Bonus included." },
```

- [ ] **Step 2: Teste primeiro** — em `tools/test_guia_tutorial_cliente.js` acrescentar (antes do resumo final; siga o estilo `check(...)` do arquivo) uma seção que lê `src/gameState.js` e `game.js` como texto e confere a fiação:

```js
console.log("\n[18] conclusão visível (fiação)");
const gsSrc = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
const gjSrc = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("gameState repassa licao_passo_ok", /case 'licao_passo_ok':[\s\S]{0,80}_emit\('licaoPassoOk'/.test(gsSrc));
check("gameState repassa licao_concluida", /case 'licao_concluida':[\s\S]{0,80}_emit\('licaoConcluida'/.test(gsSrc));
check("game.js trata licaoPassoOk", /GS\.on\('licaoPassoOk'/.test(gjSrc));
check("game.js trata licaoConcluida", /GS\.on\('licaoConcluida'/.test(gjSrc));
const langT = fs.readFileSync(path.join(raiz, "src", "lang", "tutorial.js"), "utf8");
for (const k of ["passo_ok", "licao_concluida", "recompensa", "recompensa_trilha"])
  check("chave ui.tutorial." + k + " em pt e en",
        new RegExp('"ui\\.tutorial\\.' + k + '":\\s*\\{[^}]*"pt"[^}]*"en"|"ui\\.tutorial\\.' + k + '":\\s*\\{[^}]*"en"[^}]*"pt"').test(langT));
```
Run: `node tools/test_guia_tutorial_cliente.js 2>&1 | tail -15` — Expected: ❌ nas 4 primeiras.

- [ ] **Step 3: `src/gameState.js`** — após `case 'licao_passo'`:

```js
      case 'licao_passo_ok':
        _emit('licaoPassoOk', msg);     // {licao_id, passo, total}
        break;

      case 'licao_concluida':
        _emit('licaoConcluida', msg);   // {licao_id, recompensa:{ouro,xp,trilha}}
        break;
```

- [ ] **Step 4: `game.js`** — após o `GS.on('licaoPasso'…)`:

```js
// ✓ no passo que acabou de fechar. Dura ~1,2 s por cima da janela da lição.
function _guiaPassoOk(){
  const host = $('licao-janela');
  if(!host || !host.classList.contains('open')) return;
  host.querySelector('.licao-ok')?.remove();
  const el = document.createElement('div');
  el.className = 'licao-ok';
  el.textContent = '✓ ' + t('ui.tutorial.passo_ok');
  host.appendChild(el);
  setTimeout(() => el.remove(), 1200);
  sfx('moedas');
}
GS.on('licaoPassoOk', msg => {
  if(!msg || !_licaoUltima || msg.licao_id !== _licaoUltima.licao_id) return;
  _guiaPassoOk();
});

// Selo ao fim da lição, com o ganho (só na 1ª vez do personagem).
GS.on('licaoConcluida', msg => {
  if(!msg) return;
  const r = msg.recompensa || {};
  const host = $('licao-janela');
  if(!host) return;
  host.classList.add('open');
  const premio = (r.ouro || r.xp)
    ? `<div class="licao-selo-premio">${_esc(t('ui.tutorial.recompensa', {ouro: r.ouro || 0, xp: r.xp || 0}))}</div>` : '';
  const trilha = r.trilha ? `<div class="licao-selo-trilha">${_esc(t('ui.tutorial.recompensa_trilha'))}</div>` : '';
  host.querySelector('.licao-selo')?.remove();
  const selo = document.createElement('div');
  selo.className = 'licao-selo';
  selo.innerHTML = `<div class="licao-selo-titulo">🏅 ${_esc(t('ui.tutorial.licao_concluida'))}</div>${premio}${trilha}`;
  host.appendChild(selo);
  _guiaEncerrar?.();            // some o halo da lição que acabou
  sfx(r.trilha ? 'nivel' : 'objetivo');
  setTimeout(() => selo.remove(), 4500);
});
```
Antes de usar `_guiaEncerrar?.()`: confirmar com `grep -n "function _guiaEncerrar" game.js` que existe; se ela também fecha a janela, **não** a chame aqui (o selo precisa da janela aberta) — nesse caso troque por `_guiaLimparHalo` equivalente ou remova a linha.

- [ ] **Step 5: CSS** (`game.css`, junto de `#licao-janela .licao-barra`)

```css
#licao-janela .licao-ok{ position:absolute; top:6px; right:30px; padding:2px 8px; border-radius:10px;
  background:#2e7d32; color:#fff; font-size:.72rem; font-weight:700; animation:licaoOk 1.2s ease-out forwards; pointer-events:none; }
@keyframes licaoOk{ 0%{ transform:scale(.6); opacity:0 } 15%{ transform:scale(1.1); opacity:1 } 80%{ opacity:1 } 100%{ opacity:0; transform:translateY(-6px) } }
#licao-janela .licao-selo{ margin-top:8px; padding:8px; border:1px solid #f0c867; border-radius:6px; background:#f0c8671f; text-align:center; }
#licao-janela .licao-selo-titulo{ font-weight:700; color:#f0c867; }
#licao-janela .licao-selo-premio{ font-size:.8rem; margin-top:2px; }
#licao-janela .licao-selo-trilha{ font-size:.72rem; opacity:.85; margin-top:2px; }
```
(Conferir que `#licao-janela` tem `position:relative/fixed`; senão adicionar `position:relative` à regra base se ela for `static`.)

- [ ] **Step 6: Rodar**

```bash
node tools/test_guia_tutorial_cliente.js
python tools/test_idioma.py
python tools/test_interface.py
python tools/dividas.py
node --check game.js && node --check src/gameState.js
```
Expected: tudo verde; `dividas.py` "nada pendente".

- [ ] **Step 7: Commit** (só seus trechos de `game.js`, `src/gameState.js`, `game.css`; arquivos `src/lang/tutorial.js`, `tools/test_guia_tutorial_cliente.js` inteiros se limpos).

---

### Task 4: Lição "Seus atalhos"

**Files:**
- Modify: `tools/configurar_tutorial_salas.py`, `tools/tutorial_guia_comum.py`, `tools/test_tutorial_conteudo.py`
- Generated: `dungeons/campo_de_treinamento.json`, `src/lang/tutorial_guia.js`

Antes de escrever: ler `game.js` ~linhas 842–860 e 27531/28154 (barra `ATALHOS`, `ui.atalhos.titulo`) e 28526 (`R` = câmera) para citar as teclas **reais** no texto (as teclas de habilidade/magia são configuráveis: o texto manda abrir o menu e olhar o painel ATALHOS, não crava tecla).

- [ ] **Step 1: Teste (falha)** — em `test_tutorial_conteudo.py`: acrescentar `"fala_atalhos"` a `IDS_ESPERADOS` (e `"fala_res"`, `"fala_vuln"` — Task 5) e um teste:

```python
    def test_licao_de_atalhos_cobre_os_quatro_atalhos(self):
        txt = " ".join(p["texto"][0].lower() for p in C.GUIA["fala_atalhos"])
        for palavra in ("atalho", "r", "esc", "clique"):
            self.assertIn(palavra, txt.replace(".", " ").split() + [txt], palavra)
```
(Simplifique para `assertIn(palavra, txt)`; a intenção é só garantir que os quatro temas aparecem.)

- [ ] **Step 2: Fala no JSON** — em `configurar_tutorial_salas.py`, **antes** da linha `import sys as _sys`:

```python
# Lição comum: atalhos. Fica no átrio logo depois da trilha comum inicial.
if not any(f['id'] == 'fala_atalhos' for f in d['falas']):
    d['falas'].append({
        'id': 'fala_atalhos', 'pos': [8, 15], 'falante': {'nome': 'Instrutor de Treinamento', 'emoji': '🎓'},
        'texto': 'Atalhos: a barra ATALHOS liga habilidades e magias a teclas; R recentraliza a câmera 3D; Esc cancela uma mira; clicar numa casa anda até ela.',
        'trigger': {'tipo': 'proximidade', 'raio': 4}, 'ordem': 5,
        'tarefa': {'tipo': 'encerrar_turno', 'vezes': 1, 'texto_curto': 'Encerre o turno para concluir'}})
```
Observação: as falas comuns são preservadas pelo filtro do topo (`not f.get('classe') or ordem<=2`), então a nova precisa ser (re)adicionada a cada execução — por isso o `if not any`. Ajustar `ordem` para ficar entre `fala_3` (4) e `fala_4` (5) **somente se** o campo for apenas ordenação; conferir com `grep -n "'ordem'\|\"ordem\"" server.py` como `_verificar_falas` ordena. Se a ordem for estrita por inteiro, usar `ordem: 19` e `pos` perto de `fala_38` ([43,15]→[42,16]).

- [ ] **Step 3: Conteúdo** — em `tutorial_guia_comum.py`, dentro de `GUIA = {…}`:

```python
    "fala_atalhos": [
        P("barra", ("Abra o menu de habilidades ✨ e confira o painel [[atalho]]: cada tecla dispara uma habilidade.",
                    "Open the abilities menu ✨ and check the [[atalho]] panel: each key fires an ability."),
          ui="botao:magias"),
        P("camera", ("Aperte R no tabuleiro 3D para recentralizar a câmera.",
                     "Press R on the 3D board to re-center the camera.")),
        P("cancelar", ("Aperte Esc para cancelar uma mira ou fechar um painel.",
                       "Press Esc to cancel an aim or close a panel.")),
        P("andar", ("Clique numa casa do mapa para andar até ela; depois encerre o turno.",
                    "Click a map square to walk there; then end your turn."),
          ui="botao:encerrar_turno"),
    ],
```
E em `GLOSSARIO` o termo:

```python
    "atalho": {"nome": ("atalho", "shortcut"),
               "texto": ("Uma tecla ligada a uma habilidade ou magia. Você configura as teclas no painel ATALHOS.",
                         "A key bound to an ability or spell. You set the keys in the SHORTCUTS panel.")},
```
Confirmar com `grep -n "botao:magias\|data-guia=\"botao:encerrar_turno\"" game.js` que os dois alvos `ui` existem (existem: `botao:magias` na fatia 4, `botao:encerrar_turno` na fatia 1). Passos 1–3 são informativos ("Entendi"); o último (`andar`) encerra por `encerrar_turno`. **Todo passo começa por verbo da lista do Task 1** (Abra/Aperte/Clique).

- [ ] **Step 4: Gerar e testar**

```bash
python tools/configurar_tutorial_salas.py
python tools/gerar_guia_comum.py
python tools/test_tutorial_conteudo.py && python tools/test_tutorial_guia.py && python tools/test_tutorial_salas.py && python tools/test_idioma.py
```
Expected: OK. Se `test_tutorial_salas` acusar contagem de falas, ajuste a asserção para relação (não cravar número).

- [ ] **Step 5: Commit** (`tools/configurar_tutorial_salas.py tools/tutorial_guia_comum.py tools/test_tutorial_conteudo.py dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js`).

---

### Task 5: Lições de resistência e de vulnerabilidade

**Files:** os mesmos do Task 4.

O `esqueleto_humano` (sala 23) **já** tem as duas coisas no bestiário: resistência a perfurante (−2) e cortante (−1), vulnerabilidade a contundente (+2) e a sagrado (×2). Um 2º esqueleto em [44,17] serve às lições novas sem consumir o da `fala_38`.

- [ ] **Step 1: Teste (falha)** — em `test_tutorial_conteudo.py`, junto aos IDs do Task 4, e:

```python
    def test_licoes_de_dano_usam_o_esqueleto_e_o_glossario(self):
        for lid in ("fala_res", "fala_vuln"):
            self.assertTrue(any(p.get("ui") == "monstro:esqueleto_humano" for p in C.GUIA[lid]), lid)
        self.assertIn("vulnerabilidade", C.GLOSSARIO)
        self.assertIn("resistencia", C.GLOSSARIO)
```
Ver em `UI_OK` (regex no topo do arquivo) que `monstro:[a-z0-9_]+` já é aceito.

- [ ] **Step 2: Falas e monstro** — em `configurar_tutorial_salas.py` antes de `import sys as _sys`:

```python
# Lições de dano: o 2º esqueleto da sala 23 (o 1º é da lição de derrubar com a maça).
if not any(m['pos'] == [44, 17] for m in d['monsters']):
    d['monsters'].append({'type': 'esqueleto_humano', 'pos': [44, 17], 'room_id': 23, 'boss': False, 'target': False})
for fid, ordem, texto, curto, verbo in [
    ('fala_res', 19, 'Esqueletos resistem a golpes cortantes e perfurantes: espada e adaga causam menos dano. Ataque o esqueleto e compare o dano.',
     'Ataque o esqueleto do fundo', 'atacar'),
    ('fala_vuln', 20, 'Esqueletos são vulneráveis a impacto: a maça causa dano extra. Equipe a maça e ataque o mesmo esqueleto.',
     'Ataque o esqueleto com a maça', 'atacar')]:
    if not any(f['id'] == fid for f in d['falas']):
        d['falas'].append({'id': fid, 'pos': [43, 17], 'falante': {'nome': 'Instrutor de Treinamento', 'emoji': '🎓'},
                           'texto': texto, 'trigger': {'tipo': 'proximidade', 'raio': 4}, 'ordem': ordem,
                           'tarefa': {'tipo': verbo, 'alvo': 'esqueleto_humano', 'vezes': 1, 'texto_curto': curto}})
```
Conferir `ordem` contra a lição de atalhos (Step 2 do Task 4): usar números inteiros distintos e crescentes depois de 18 (`fala_38`); se o Task 4 usou 19, use 20 e 21 aqui e ajuste a lista acima. Verificar que `fala_38`, ao matar o esqueleto de [44,15], não consome o de [44,17] (alvo é o tipo `esqueleto_humano`: a lição `matar` conta qualquer um — se isso encerrar a lição com o 2º, aceitável).

- [ ] **Step 3: Conteúdo** — em `tutorial_guia_comum.py`:

```python
    "fala_res": [
        P("ler", ("Ataque o esqueleto e leia o dano: a [[resistencia]] corta golpes cortantes e perfurantes.",
                  "Attack the skeleton and read the damage: [[resistencia]] cuts slashing and piercing hits."),
          ui="monstro:esqueleto_humano", conclui=None),
        P("bate", ("Clique no esqueleto de novo e compare: menos dano é sinal de resistência.",
                   "Click the skeleton again and compare: less damage means resistance."),
          ui="monstro:esqueleto_humano"),
    ],
    "fala_vuln": [
        P("maca", ("Abra a bolsa e equipe a maça: impacto é o ponto fraco do esqueleto.",
                   "Open the bag and equip the mace: impact is the skeleton's weak point."),
          ui="botao:mochila"),
        P("bate", ("Ataque o esqueleto: a [[vulnerabilidade]] soma dano extra ao golpe.",
                   "Attack the skeleton: [[vulnerabilidade]] adds extra damage to the hit."),
          ui="monstro:esqueleto_humano"),
    ],
```
**Regra de ouro:** `equipar` não pode ser `conclui_com` (pode ter ocorrido antes: o passo `maca` fica informativo, com "Entendi"). Verificar que o `ui` `botao:mochila` existe (`grep -n 'data-guia="botao:' game.js index.html`); se o id real for outro, usar o real.
Glossário: atualizar `resistencia` para cobrir o dano reduzido por tipo e acrescentar:

```python
    "vulnerabilidade": {"nome": ("vulnerabilidade", "vulnerability"),
                        "texto": ("A criatura sofre dano extra de certo tipo de golpe, como impacto ou sagrado.",
                                  "The creature takes extra damage from a type of hit, such as impact or holy.")},
```
Em `test_tutorial_conteudo.py` o teste `test_glossario_completo` cobra o conjunto de termos: acrescente `atalho` e `vulnerabilidade` ao conjunto esperado.

- [ ] **Step 4: Gerar e testar**

```bash
python tools/configurar_tutorial_salas.py && python tools/gerar_guia_comum.py
python tools/test_tutorial_conteudo.py && python tools/test_tutorial_guia.py && python tools/test_tutorial_salas.py && python tools/test_idioma.py && python tools/dividas.py
```

- [ ] **Step 5: Commit** (mesmos arquivos do Task 4).

---

### Task 6: Cores de dano (condicional) e prova no navegador

**Files:** `tools/tutorial_guia_comum.py` (só se a branch `codex/ceu-abismo` já estiver no `master`); `CLAUDE.md`.

- [ ] **Step 1: Checar a integração**

Run: `git log --oneline master | head -20; grep -n "ui.menu.damage.status.resisted" src/lang/*.js | head -2`
Se a chave **não** estiver no `master`: manter a redação neutra do Task 5 (nada a fazer). Se estiver: no passo `ler` de `fala_res`, acrescentar ao texto "…o número aparece em azul com RESISTIDO" (e `vuln`: "em vermelho com VULNERÁVEL"; en: "RESISTED"/"VULNERABLE"), respeitando ≤15 palavras; regerar e testar como no Task 5.

- [ ] **Step 2: Prova no navegador** (servidor isolado)

Copiar `accounts/`, `savegames/`, `groups/` para `%TEMP%\lfh8794`, subir `LFH_PORT=8794` apontando para a cópia (veja como a fatia 5 fez em `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia5-editor.md`, Task de prova), criar conta de teste local, entrar no Campo de Treinamento e conferir por DOM (`read_page`/`javascript_tool`; screenshot não funciona com a janela oculta): (a) o texto do 1º passo da `fala_0` começa por verbo; (b) ao clicar Entendi aparece `.licao-ok` e o `moedas` toca (`SoundBank`); (c) ao concluir a lição aparece `.licao-selo` com "+5 ouro · +10 XP" na 1ª vez e **sem** premio ao `repetir_tutorial`; (d) `fala_atalhos`, `fala_res`, `fala_vuln` abrem nos locais certos. Parar e apagar o servidor/cópias ao fim.

- [ ] **Step 3: Documentar** — em `CLAUDE.md` (Edit, CRLF), no fim do parágrafo "Tutorial guiado", acrescentar **Fatia 6 (2026-10-07):** passos com verbo de ação (teste `RedacaoAcionavelTests`), `licao_passo_ok`/`licao_concluida`, recompensa `TUTORIAL_RECOMPENSA_*` paga uma vez por personagem (guarda `tutorial_history`), lições `fala_atalhos`/`fala_res`/`fala_vuln`, glossário `atalho`/`vulnerabilidade`, e que o texto das cores RESISTIDO/VULNERÁVEL depende da integração de `codex/ceu-abismo`. Commit só do `CLAUDE.md` (e do plano).

- [ ] **Step 4: Suítes finais**

```bash
python tools/test_tutorial_conteudo.py && python tools/test_tutorial_guia.py && python tools/test_tutorial_classes.py && python tools/test_tutorial_modelos.py && python tools/test_tutorial_salas.py
node tools/test_guia_tutorial_cliente.js && node tools/test_editor_guia_logic.js && python tools/test_editor_guia.py
python tools/test_idioma.py && python tools/test_interface.py && python tools/dividas.py
```
Expected: verdes. Falhas conhecidas e **não suas**: `test_editor_idioma.py` (36 literais do WIP do autor em `tools/editor.js`), `tools/test_tutorial.py` (obsoleto), `test_tempestade_ciclones` (instável).

---

## Self-review

- **Spec §1 (instrução)** → Task 1. **§2 (conclusão visível)** → Tasks 2–3 (a barra "passo i/n" já existia). **§3 (recompensa)** → Task 2 (sem campo por lição: desvio declarado). **§4 (atalhos)** → Task 4. **§5 (resistência)** → Tasks 5–6.
- Nomes consistentes: `TUTORIAL_RECOMPENSA_OURO/XP`, `TUTORIAL_BONUS_TRILHA_OURO/XP`, mensagens `licao_passo_ok`/`licao_concluida`, eventos de cliente `licaoPassoOk`/`licaoConcluida`, ids `fala_atalhos`/`fala_res`/`fala_vuln`.
- Pontos a **verificar no código** (marcados nos passos): ordem/`ordem` das falas comuns novas, ids de `ui` `botao:mochila`, comportamento de `_guiaEncerrar`, contagens em `test_tutorial_salas`.
