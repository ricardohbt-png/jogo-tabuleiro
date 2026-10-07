# Tutorial guiado — Fatia 2 (halo no tabuleiro, dicas por erro, resultado) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estender o guia do tutorial para o tabuleiro 2D e 3D (casa, monstro, porta com caminho tracejado, item da bolsa, slot de equipamento), avisar o jogador quando ele erra a ação do exercício (`licao_dica`) e mostrar o resultado do ataque em uma frase (`licao_resultado`).

**Architecture:** Continua a fatia 1. O servidor decide: um ponto único (`send_to`) converte recusas conhecidas em `licao_dica`, e o ataque básico do herói emite `licao_resultado` com os números reais. O cliente decide só o desenho: o módulo puro `src/guiaTutorial.js` ganha `alvoTabuleiro` e `caminhoAbsoluto`, e o `game.js` desenha um anel pulsante com seta na casa alvo (2D no canvas, 3D com malhas), mais uma linha tracejada até a porta.

**Tech Stack:** Python (`server.py`, `unittest`), JavaScript sem bundler (`src/guiaTutorial.js`, `src/gameState.js`, `game.js`, `src/ui/inventoryModal.js`), testes em node.

**Spec:** `docs/superpowers/specs/2026-10-07-tutorial-guiado-design.md`, seções 2 (dica por erro, resultado), 3.1, 4.2 e 4.5. **Plano anterior:** `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia1-mecanismo.md` (já executado; a fatia 1 está em `master`).

**Fora desta fatia:** seta na borda do tabuleiro para alvo fora da visão (o halo simplesmente não aparece nesse caso), halo de `hud:<id>` (medidores de fome e sede), glossário, reescrita das 62 lições, editor de masmorras, dica `habilidade_nao_armada` (armar é ação só do cliente e um ataque comum com Mira arma emite `atacar` e `usar_habilidade` juntos, o que geraria falso aviso).

## Regras do repositório que valem para todas as tarefas

- `game.js`, `server.py` e `CLAUDE.md` usam **CRLF**. Edite com a ferramenta Edit; um script Python com `replace("...\n...")` não casa. Use `PYTHONIOENCODING=utf-8` ao rodar Python.
- O autor e outras sessões editam arquivos em paralelo. **Antes de cada commit:** `git status --short`, `git diff --stat <arquivos>`, `git diff --cached --stat` (o índice deve estar vazio antes do seu `git add`) e confirme que `.git/MERGE_HEAD` **não existe**. Commite com caminhos explícitos: `git commit -m ... -- <arquivos>`. Nunca commite `src/soundBank.js` nem `tools/editor.js` (WIP do autor). Se o diff de um arquivo tiver trechos que não são seus, pare e reporte BLOCKED.
- Nunca toque em `savegames/`, `accounts/`, `groups/` reais. Não faça push.
- Um `GS.on('evento')` substitui o ouvinte anterior do mesmo evento: registre um só por evento.
- Em `game.js`, não declare variável local chamada `t` e não chame `t()` no nível de módulo.
- Texto de interface novo sempre por `t('ui.tutorial.<slug>')`, com `pt` e `en` em `src/lang/tutorial.js`. O servidor lê `src/lang/*.js` como JSON estrito (sem vírgula antes de `};`).
- Cada commit termina com `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `server.py` | Tabela de motivos, `_guia_dica`, `_guia_dica_por_erro`, gancho em `send_to`, `alvo_errado` em `_licao_evento`, `_guia_resultado_ataque` e a chamada em `handle_attack` |
| `src/gameState.js` | Encaminha `licao_dica` e `licao_resultado` |
| `src/guiaTutorial.js` | Puro: `seletor` ganha `bolsa`/`slot`; novos `alvoTabuleiro` e `caminhoAbsoluto` |
| `src/ui/inventoryModal.js` | `data-item-id` nos espaços da bolsa |
| `src/lang/tutorial.js` | Textos das dicas de erro e do resultado |
| `game.js` | `data-guia` no botão da mochila; aviso temporário na janela; desenho 2D e 3D do alvo; caminho tracejado |
| `game.css` | `.licao-aviso` |
| `tools/test_tutorial_guia.py` | Testes do servidor (classes novas) |
| `tools/test_guia_tutorial_cliente.js` | Testes node (seções novas) |
| `CLAUDE.md` | Atualizar o parágrafo do guia |

---

### Task 1: Dicas por erro no servidor (`licao_dica`)

**Files:**
- Modify: `server.py` (constantes perto de `GUIA_UI_RE`; métodos junto de `_guia_avancar`; início de `GameRoom.send_to`; `_licao_evento`)
- Test: `tools/test_tutorial_guia.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_tutorial_guia.py`, acrescente antes do `if __name__`:

```python
class DicaErroTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        S._GUIA_DICA_ULTIMA.clear()

    def dicas(self, r):
        return [m for m in r.messages if m.get('type') == 'licao_dica']

    async def test_nao_e_o_seu_turno_vira_fora_da_vez(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        d = self.dicas(r)
        self.assertEqual(len(d), 1)
        self.assertEqual((d[0]['motivo'], d[0]['licao_id']), ('fora_da_vez', 'treino_mira'))

    async def test_acao_ja_usada_vira_sem_acao(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.acao_principal_ja_usada_neste_turno'))
        self.assertEqual(self.dicas(r)[0]['motivo'], 'sem_acao')

    async def test_alvo_fora_de_alcance_vira_longe_do_alvo(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')                 # tarefa: atacar boneco_treino
        await r._guia_dica_por_erro('hero', S.T('erro.alvo_fora_de_alcance'))
        self.assertEqual(self.dicas(r)[0]['motivo'], 'longe_do_alvo')

    async def test_alvo_invalido_vira_alvo_errado(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._guia_dica_por_erro('hero', S.T('erro.alvo_invalido'))
        self.assertEqual(self.dicas(r)[0]['motivo'], 'alvo_errado')

    async def test_erro_desconhecido_nao_gera_dica(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.sala_nao_encontrada'))
        await r._guia_dica_por_erro('hero', "texto cru")
        await r._guia_dica_por_erro('hero', None)
        self.assertEqual(self.dicas(r), [])

    async def test_sem_licao_pendente_nao_gera_dica(self):
        r, p = room('warrior')
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        await r._guia_dica_por_erro('nao_existe', S.T('erro.nao_e_o_seu_turno'))
        self.assertEqual(self.dicas(r), [])

    async def test_alvo_errado_so_em_tarefa_com_alvo(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_0')                 # tarefa: mover_ate (sem alvo de combate)
        await r._guia_dica_por_erro('hero', S.T('erro.alvo_invalido'))
        self.assertEqual(self.dicas(r), [])

    async def test_intervalo_minimo_entre_dicas(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        self.assertEqual(len(self.dicas(r)), 1)
        S._GUIA_DICA_ULTIMA['hero'] -= S.GUIA_DICA_INTERVALO_S + 1
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        self.assertEqual(len(self.dicas(r)), 2)

    async def test_send_to_real_chama_o_gancho_so_para_erros(self):
        r, p = room('warrior')
        vistos = []

        async def espia(pid, texto): vistos.append((pid, getattr(texto, 'key', texto)))
        r._guia_dica_por_erro = espia
        r.connections = {}
        await S.GameRoom.send_to(r, 'hero', {"type": "error", "msg": S.T('erro.nao_e_o_seu_turno')})
        await S.GameRoom.send_to(r, 'hero', {"type": "gm_narration", "text": "oi"})
        self.assertEqual(vistos, [('hero', 'erro.nao_e_o_seu_turno')])

    async def test_alvo_errado_quando_acerta_outro_tipo(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._licao_evento(p, 'atacar', alvo='esqueleto_humano')
        d = self.dicas(r)
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]['motivo'], 'alvo_errado')
        self.assertEqual(p['licao_atual'], 'fala_5')       # não concluiu
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_tutorial_guia.py DicaErroTests -v`
Expected: `AttributeError` para `_GUIA_DICA_ULTIMA`, `GUIA_DICA_INTERVALO_S`, `_guia_dica_por_erro`.

- [ ] **Step 3: Constantes**

Em `server.py`, logo depois do bloco `GUIA_UI_RE = re.compile(...)` (use Edit), acrescente:

```python
# Dica por erro: recusas que o servidor já emite viram um motivo curto que o cliente
# traduz (ui.tutorial.dica_erro.<motivo>). Mapa por chave exata e por prefixo.
GUIA_DICA_POR_ERRO = {
    "erro.nao_e_o_seu_turno": "fora_da_vez",
    "erro.acao_principal_ja_usada_neste_turno": "sem_acao",
    "erro.alvo_invalido": "alvo_errado",
}
GUIA_DICA_POR_PREFIXO = (("erro.alvo_fora_", "longe_do_alvo"),)
# Estes dois motivos só fazem sentido quando a tarefa pendente tem um alvo de combate.
GUIA_DICA_EXIGE_ALVO = ("alvo_errado", "longe_do_alvo")
GUIA_TAREFAS_COM_ALVO = ("atacar", "matar", "usar_habilidade", "usar_tecnica",
                         "arremessar_item", "usar_instrumento", "proteger", "libertar_refem",
                         "desarmar_armadilha")
GUIA_DICA_INTERVALO_S = 5.0
_GUIA_DICA_ULTIMA = {}      # pid -> time.monotonic() da última dica (fora da sala e da foto)
```

Confirme `import time` no topo do `server.py` (`grep -n "^import time" server.py`); se faltar, acrescente.

- [ ] **Step 4: Métodos**

Em `server.py`, logo depois de `handle_avancar_passo` (use Edit), acrescente:

```python
    async def _guia_dica(self, pid, motivo):
        """Avisa o herói que errou o exercício. Uma dica a cada GUIA_DICA_INTERVALO_S."""
        p = self.players.get(pid)
        if not p or not getattr(self, "licoes", None):
            return
        lic = next((l for l in self.licoes if l["id"] == p.get("licao_atual")), None)
        tar = (lic or {}).get("tarefa")
        if not lic or not tar:
            return
        if motivo in GUIA_DICA_EXIGE_ALVO and tar.get("tipo") not in GUIA_TAREFAS_COM_ALVO:
            return
        agora = time.monotonic()
        if agora - _GUIA_DICA_ULTIMA.get(pid, -1e9) < GUIA_DICA_INTERVALO_S:
            return
        _GUIA_DICA_ULTIMA[pid] = agora
        await self.send_to(pid, {"type": "licao_dica", "licao_id": lic["id"], "motivo": motivo})

    async def _guia_dica_por_erro(self, pid, texto):
        """Converte uma recusa conhecida (T com chave) em dica; o resto passa em silêncio."""
        chave = getattr(texto, "key", None)
        if not isinstance(chave, str):
            return
        motivo = GUIA_DICA_POR_ERRO.get(chave) or next(
            (m for pre, m in GUIA_DICA_POR_PREFIXO if chave.startswith(pre)), None)
        if motivo:
            await self._guia_dica(pid, motivo)
```

- [ ] **Step 5: Gancho em `send_to`**

Em `GameRoom.send_to` (`async def send_to(self, pid, msg):`), logo na primeira linha do corpo (antes de `ws = self.connections.get(pid)`), acrescente:

```python
        if isinstance(msg, dict) and msg.get("type") == "error" and getattr(self, "licoes", None):
            await self._guia_dica_por_erro(pid, msg.get("msg"))
```

- [ ] **Step 6: `alvo_errado` em `_licao_evento`**

Em `_licao_evento`, troque

```python
        if not self._licao_alvo_ok(tar.get("alvo"), alvo):
            return
```

por

```python
        if not self._licao_alvo_ok(tar.get("alvo"), alvo):
            await self._guia_dica(p["id"], "alvo_errado")
            return
```

(Há apenas um `if not self._licao_alvo_ok(tar.get("alvo"), alvo)` dentro de `_licao_evento`; o outro uso é `cond.get("alvo")` em `_guia_evento` e não muda.)

- [ ] **Step 7: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_tutorial_guia.py -v`
Expected: todos `ok` (os da fatia 1 mais os 10 novos).

- [ ] **Step 8: Regressão**

Run: `PYTHONIOENCODING=utf-8 python tools/test_tutorial_salas.py && PYTHONIOENCODING=utf-8 python tools/test_dungeon_loader.py`
Expected: sem falhas novas.

- [ ] **Step 9: Commit**

```bash
git status --short server.py tools/test_tutorial_guia.py
git diff --stat server.py
git diff --cached --stat
git commit -m "feat(tutorial): dica por erro (licao_dica) no servidor" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- server.py tools/test_tutorial_guia.py
```

(Rode `git add server.py tools/test_tutorial_guia.py` antes do `git commit` se o git reclamar de arquivos não rastreados no pathspec.)

---

### Task 2: Resultado do ataque (`licao_resultado`)

**Files:**
- Modify: `server.py` (método junto de `_guia_dica`; chamada em `handle_attack`)
- Test: `tools/test_tutorial_guia.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
class ResultadoTests(unittest.IsolatedAsyncioTestCase):
    def resultados(self, r):
        return [m for m in r.messages if m.get('type') == 'licao_resultado']

    async def test_acerto(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._guia_resultado_ataque(p, roll=14, total=17, ca=12, hit=True, crit=False)
        m = self.resultados(r)[0]
        self.assertEqual((m['chave'], m['roll'], m['bonus'], m['total'], m['ca']),
                         ('acerto', 14, 3, 17, 12))
        self.assertEqual(m['licao_id'], 'fala_5')

    async def test_critico_e_erro(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._guia_resultado_ataque(p, roll=20, total=23, ca=12, hit=True, crit=True)
        await r._guia_resultado_ataque(p, roll=3, total=6, ca=12, hit=False, crit=False)
        self.assertEqual([m['chave'] for m in self.resultados(r)], ['critico', 'erro'])

    async def test_sem_licao_pendente_nao_envia(self):
        r, p = room('warrior')
        await r._guia_resultado_ataque(p, roll=14, total=17, ca=12, hit=True, crit=False)
        self.assertEqual(self.resultados(r), [])

    def test_handle_attack_chama_o_resultado(self):
        import inspect
        fonte = inspect.getsource(S.GameRoom.handle_attack)
        self.assertIn('_guia_resultado_ataque(', fonte)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_tutorial_guia.py ResultadoTests -v`
Expected: `AttributeError: ... '_guia_resultado_ataque'` e falha do teste estático.

- [ ] **Step 3: Método**

Em `server.py`, logo depois de `_guia_dica_por_erro`, acrescente:

```python
    async def _guia_resultado_ataque(self, p, roll, total, ca, hit, crit):
        """Uma frase com os números do ataque, só para quem está numa lição."""
        lic_id = p.get("licao_atual") if p else None
        if not lic_id or not getattr(self, "licoes", None):
            return
        chave = "critico" if (hit and crit) else ("acerto" if hit else "erro")
        await self.send_to(p["id"], {
            "type": "licao_resultado", "licao_id": lic_id, "chave": chave,
            "roll": int(roll), "bonus": int(total) - int(roll),
            "total": int(total), "ca": int(ca)})
```

- [ ] **Step 4: Chamar em `handle_attack`**

Em `handle_attack`, localize a chamada `await self._emitir_feedback_ataque("result", p, target, attack_name, attack_mode, attack_id=attack_feedback_id, roll=roll, total=total, hit=bool(hit), crit=bool(crit), natural=int(roll), ...)` (`grep -n 'attack_id=attack_feedback_id, roll=roll, total=total' server.py`; há mais de uma ocorrência em outros handlers, use a que está dentro de `handle_attack`, a que tem `sneak_attack=bool(hit and furtivo_planejado))`). Logo **depois** dela, acrescente:

```python
            await self._guia_resultado_ataque(p, roll, total, eff_target_ac, hit, crit)
```

mantendo a indentação da chamada acima. Confirme com `grep -n "eff_target_ac" server.py` que o nome está em escopo nesse ponto (ele é passado a `_rolar_ataque` logo antes); se o nome real for outro, use o CA efetivo que o mesmo bloco usa para decidir `hit`.

- [ ] **Step 5: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_tutorial_guia.py -v && PYTHONIOENCODING=utf-8 python tools/test_tutorial_salas.py`
Expected: `OK` nos dois.

- [ ] **Step 6: Commit**

```bash
git status --short server.py tools/test_tutorial_guia.py
git diff --stat server.py
git diff --cached --stat
git commit -m "feat(tutorial): resultado do ataque (licao_resultado)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- server.py tools/test_tutorial_guia.py
```

---

### Task 3: `gameState.js` encaminha dica e resultado

**Files:**
- Modify: `src/gameState.js` (junto do `case 'licao_passo':`)
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_guia_tutorial_cliente.js`, antes do resumo final, acrescente:

```javascript
console.log("\n[7] gameState encaminha licao_dica e licao_resultado");
{
  const visto = {};
  GS.on('licaoDica', m => { visto.dica = m; });
  GS.on('licaoResultado', m => { visto.res = m; });
  const gsSrc = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
  check("case licao_dica emite licaoDica", /case 'licao_dica':\s*\n\s*_emit\('licaoDica'/.test(gsSrc));
  check("case licao_resultado emite licaoResultado", /case 'licao_resultado':\s*\n\s*_emit\('licaoResultado'/.test(gsSrc));
}
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: 2 checks da seção [7] falham.

- [ ] **Step 3: Implementar**

Em `src/gameState.js`, depois do bloco `case 'licao_passo': ... break;` (use Edit), acrescente:

```javascript
      case 'licao_dica':
        _emit('licaoDica', msg);        // {licao_id, motivo}
        break;

      case 'licao_resultado':
        _emit('licaoResultado', msg);   // {licao_id, chave, roll, bonus, total, ca}
        break;
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_guia_tutorial_cliente.js && node tools/test_tutorial_cliente.js`
Expected: `0 falha(s)`.

- [ ] **Step 5: Commit**

```bash
git status --short src/gameState.js
git diff --cached --stat
git commit -m "feat(tutorial): gameState encaminha licao_dica e licao_resultado" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- src/gameState.js tools/test_guia_tutorial_cliente.js
```

---

### Task 4: Módulo puro — alvo no tabuleiro, caminho e seletores da bolsa

**Files:**
- Modify: `src/guiaTutorial.js`
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_guia_tutorial_cliente.js`, antes do resumo final, acrescente:

```javascript
console.log("\n[8] seletor: bolsa e slot (DOM do inventário)");
s = G.seletor("bolsa:racao_viagem");
check("bolsa acha o espaço pelo item", s && s.css === '.inv-bagslot[data-item-id="racao_viagem"]' && s.ancestral === null);
check("bolsa cai no botão da mochila se o inventário está fechado",
      s && s.alternativa === '[data-guia="botao:inventario"]');
s = G.seletor("slot:main_hand");
check("slot acha o espaço de equipamento", s && s.css === '.inv-slot[data-slot-key="main_hand"]');
s = G.seletor("botao:inventario");
check("botão da mochila usa data-guia", s && s.css === '[data-guia="botao:inventario"]');
check("alternativa só existe na bolsa", G.seletor("botao:encerrar_turno").alternativa === undefined
      || G.seletor("botao:encerrar_turno").alternativa === null);

console.log("\n[9] alvoTabuleiro");
const estado = { monsters: [
  { id: "m1", type: "boneco_treino", pos: [5, 5], hp: 5 },
  { id: "m2", type: "boneco_treino", pos: [9, 9], hp: 5 },
  { id: "m3", type: "esqueleto_humano", pos: [1, 1], hp: 5 },
  { id: "m4", type: "boneco_treino", pos: [4, 5], hp: 0 },
] };
const todos = () => true;
let a = G.alvoTabuleiro("casa:[3,14]", estado, [0, 0], todos);
check("casa devolve a posição", a && a.tipo === "casa" && a.pos[0] === 3 && a.pos[1] === 14);
a = G.alvoTabuleiro("porta:[10,2]", estado, [0, 0], todos);
check("porta devolve a posição e marca caminho", a && a.tipo === "porta" && a.pos[0] === 10 && a.caminho === true);
a = G.alvoTabuleiro("casa:[3,14]", estado, [0, 0], () => false);
check("casa fora da visão: null", a === null);
a = G.alvoTabuleiro("monstro:boneco_treino", estado, [4, 4], todos);
check("monstro: o mais próximo vivo", a && a.tipo === "monstro" && a.id === "m1");
a = G.alvoTabuleiro("monstro:boneco_treino", estado, [4, 4], (x, y) => !(x === 5 && y === 5));
check("monstro: ignora quem está fora da visão", a && a.id === "m2");
a = G.alvoTabuleiro("monstro:boneco_treino", estado, [4, 4], () => false);
check("monstro: nenhum visível = null", a === null);
a = G.alvoTabuleiro("monstro:troll", estado, [4, 4], todos);
check("monstro: tipo que não existe = null", a === null);
a = G.alvoTabuleiro("monstro:boneco_treino", estado, null, todos);
check("monstro sem posição minha: pega o primeiro vivo", a && a.id === "m1");
check("botão não é alvo de tabuleiro", G.alvoTabuleiro("botao:encerrar_turno", estado, [0, 0], todos) === null);
check("lixo devolve null", G.alvoTabuleiro("xyz", estado, [0, 0], todos) === null
      && G.alvoTabuleiro(null, estado, [0, 0], todos) === null
      && G.alvoTabuleiro("monstro:boneco_treino", null, [0, 0], todos) === null);

console.log("\n[10] caminhoAbsoluto");
let c = G.caminhoAbsoluto([[1, 0], [1, 0], [0, 1]], 2, 3);
check("converte passos em casas", JSON.stringify(c) === "[[3,3],[4,3],[4,4]]");
check("passos vazios: vazio", G.caminhoAbsoluto([], 1, 1).length === 0);
check("não-lista: vazio", G.caminhoAbsoluto(null, 1, 1).length === 0);
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: falhas nas seções [8], [9], [10] (funções inexistentes, `seletor('bolsa:...')` ainda devolve null).

- [ ] **Step 3: Implementar**

Em `src/guiaTutorial.js`, substitua a função `seletor` por:

```javascript
  // Seletor CSS do elemento de DOM correspondente. Devolve null para o que
  // é desenhado no tabuleiro (casa, monstro, porta) — para esses, alvoTabuleiro.
  // `ancestral`: o achado é um filho; o halo vai no ancestral indicado.
  // `alternativa`: seletor de reserva quando o primeiro não existe na tela
  // (a bolsa só existe com o inventário aberto; o botão da mochila sempre).
  function seletor(ui) {
    const a = parseUi(ui);
    if (!a) return null;
    if (a.tipo === 'botao' || a.tipo === 'hud')
      return { css: '[data-guia="' + a.tipo + ':' + a.id + '"]', ancestral: null, alternativa: null };
    if (a.tipo === 'habilidade')
      return { css: '[data-ability-id="' + a.id + '"]', ancestral: 'button', alternativa: null };
    if (a.tipo === 'bolsa')
      return { css: '.inv-bagslot[data-item-id="' + a.id + '"]', ancestral: null,
               alternativa: '[data-guia="botao:inventario"]' };
    if (a.tipo === 'slot')
      return { css: '.inv-slot[data-slot-key="' + a.id + '"]', ancestral: null, alternativa: null };
    return null;
  }

  // Alvo desenhado NO TABULEIRO: {tipo:'casa'|'porta'|'monstro', pos, id?, caminho?}.
  // `minhaPos` [x,y] escolhe o monstro mais próximo; `visivel(x,y)` filtra o que o
  // jogador não enxerga (o halo nunca revela o que a névoa esconde).
  function alvoTabuleiro(ui, estado, minhaPos, visivel) {
    const a = parseUi(ui);
    if (!a || !estado) return null;
    const ve = typeof visivel === 'function' ? visivel : () => true;
    if (a.tipo === 'casa' || a.tipo === 'porta') {
      if (!ve(a.pos[0], a.pos[1])) return null;
      return a.tipo === 'porta' ? { tipo: 'porta', pos: a.pos, caminho: true }
                                : { tipo: 'casa', pos: a.pos };
    }
    if (a.tipo !== 'monstro') return null;
    let melhor = null, melhorD = Infinity;
    for (const m of (estado.monsters || [])) {
      if (!m || m.type !== a.id || !(m.hp > 0) || !m.pos || !ve(m.pos[0], m.pos[1])) continue;
      const d = minhaPos ? Math.max(Math.abs(m.pos[0] - minhaPos[0]), Math.abs(m.pos[1] - minhaPos[1])) : 0;
      if (d < melhorD) { melhorD = d; melhor = m; }
    }
    return melhor ? { tipo: 'monstro', pos: [melhor.pos[0], melhor.pos[1]], id: melhor.id } : null;
  }

  // [[dx,dy],...] a partir de (fx,fy) -> [[x,y],...] com as casas pisadas.
  function caminhoAbsoluto(passos, fx, fy) {
    if (!Array.isArray(passos)) return [];
    const out = []; let x = fx, y = fy;
    for (const p of passos) { x += p[0]; y += p[1]; out.push([x, y]); }
    return out;
  }
```

e troque a última linha do módulo por:

```javascript
  window.GuiaTutorial = { parseUi, seletor, alvoTabuleiro, caminhoAbsoluto, nivelDica, textoDica };
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: `0 falha(s)` (os testes da fatia 1 em [2] continuam valendo: `casa` e `monstro` seguem sem seletor de DOM).

- [ ] **Step 5: Commit**

```bash
git status --short src/guiaTutorial.js
git diff --cached --stat
git commit -m "feat(tutorial): alvo no tabuleiro, caminho e seletores da bolsa no módulo do guia" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- src/guiaTutorial.js tools/test_guia_tutorial_cliente.js
```

---

### Task 5: Marcas no DOM e textos

**Files:**
- Modify: `src/ui/inventoryModal.js` (~linha 769), `game.js` (botão `#fab-inventario`, ~linha 450), `src/lang/tutorial.js`
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever os testes que falham**

Antes do resumo final de `tools/test_guia_tutorial_cliente.js`:

```javascript
console.log("\n[11] marcas no DOM e textos");
const invSrc = fs.readFileSync(path.join(raiz, "src", "ui", "inventoryModal.js"), "utf8");
check("espaço da bolsa leva o id do item", /dataset\.itemId\s*=/.test(invSrc));
check("botão da mochila tem data-guia", /id="fab-inventario"[^>]*data-guia="botao:inventario"|data-guia="botao:inventario"[^>]*id="fab-inventario"/.test(gameSrc));
const langSrc = fs.readFileSync(path.join(raiz, "src", "lang", "tutorial.js"), "utf8");
for (const k of ["dica_erro.fora_da_vez", "dica_erro.sem_acao", "dica_erro.longe_do_alvo",
                 "dica_erro.alvo_errado", "resultado.acerto", "resultado.critico", "resultado.erro"])
  check("chave ui.tutorial." + k, langSrc.includes('"ui.tutorial.' + k + '"'));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: os 9 checks da seção [11] falham.

- [ ] **Step 3: Marcar a bolsa**

Em `src/ui/inventoryModal.js`, logo depois de `slot.dataset.bagIndex = String(i);` (~linha 770), acrescente:

```javascript
      if(item && item.id) slot.dataset.itemId = String(item.id);
```

- [ ] **Step 4: Marcar o botão da mochila**

Em `game.js`, na linha do `<button id="fab-inventario" onclick="if(GS.myPid) InventoryModal.toggle(GS.myPid)" ...>` (~450) use Edit para inserir ` data-guia="botao:inventario"` logo depois de `id="fab-inventario"`.

- [ ] **Step 5: Textos**

Em `src/lang/tutorial.js`, acrescente estas entradas dentro de `window.LANG_TUTORIAL = {` (depois da chave `"ui.tutorial.dica"`, com vírgula entre elas e **sem** vírgula depois da última):

```javascript
  "ui.tutorial.dica_erro.fora_da_vez": {
    "en": "It is not your turn yet. Wait for the others to act.",
    "pt": "Ainda não é a sua vez. Espere os outros agirem."
  },
  "ui.tutorial.dica_erro.sem_acao": {
    "en": "You already used your main action this turn. End your turn to get it back.",
    "pt": "Você já usou sua ação principal neste turno. Encerre o turno para recuperá-la."
  },
  "ui.tutorial.dica_erro.longe_do_alvo": {
    "en": "The target is too far. Walk closer and try again.",
    "pt": "O alvo está longe. Ande até ficar perto dele e tente de novo."
  },
  "ui.tutorial.dica_erro.alvo_errado": {
    "en": "That is not the exercise target. Look for the highlighted one.",
    "pt": "Esse não é o alvo do exercício. Procure o que está destacado na tela."
  },
  "ui.tutorial.resultado.acerto": {
    "en": "You rolled {roll} + {bonus} = {total} against AC {ca}: hit!",
    "pt": "Você rolou {roll} + {bonus} = {total} contra CA {ca}: acertou!"
  },
  "ui.tutorial.resultado.critico": {
    "en": "You rolled {roll} + {bonus} = {total} against AC {ca}: critical hit!",
    "pt": "Você rolou {roll} + {bonus} = {total} contra CA {ca}: acerto crítico!"
  },
  "ui.tutorial.resultado.erro": {
    "en": "You rolled {roll} + {bonus} = {total} against AC {ca}: miss. Try again.",
    "pt": "Você rolou {roll} + {bonus} = {total} contra CA {ca}: errou. Tente de novo."
  }
```

- [ ] **Step 6: Rodar tudo**

Run:
```bash
node tools/test_guia_tutorial_cliente.js
PYTHONIOENCODING=utf-8 python tools/test_idioma.py
node tools/test_idioma_cliente.js
PYTHONIOENCODING=utf-8 python tools/dividas.py
node --check game.js
PYTHONIOENCODING=utf-8 python -c "import server as S; print('ui.tutorial.dica_erro.sem_acao' in S._load_lang())"
```
Expected: `0 falha(s)`, idioma sem falhas, `nada pendente`, e `True`.

- [ ] **Step 7: Commit**

```bash
git status --short src/ui/inventoryModal.js game.js src/lang/tutorial.js
git diff --stat src/ui/inventoryModal.js game.js
git diff --cached --stat
git commit -m "feat(tutorial): marcas do guia no inventário e textos de dica e resultado" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- src/ui/inventoryModal.js game.js src/lang/tutorial.js tools/test_guia_tutorial_cliente.js
```

---

### Task 6: Aviso temporário na janela e alternativa de seletor

**Files:**
- Modify: `game.js` (bloco do guia, onde está `_guiaAplicarHalo`/`_mostrarJanelaLicao`), `game.css`
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever os testes que falham**

Antes do resumo final:

```javascript
console.log("\n[12] fiação do aviso e da alternativa no game.js");
check("um único GS.on('licaoDica')", (gameSrc.match(/GS\.on\('licaoDica'/g) || []).length === 1);
check("um único GS.on('licaoResultado')", (gameSrc.match(/GS\.on\('licaoResultado'/g) || []).length === 1);
check("aviso usa as chaves de dica de erro", /ui\.tutorial\.dica_erro\./.test(gameSrc));
check("aviso usa as chaves de resultado", /ui\.tutorial\.resultado\./.test(gameSrc));
check("janela tem o elemento licao-aviso", /id="licao-aviso"/.test(gameSrc));
check("halo usa a alternativa do seletor", /sel\.alternativa/.test(gameSrc));
check("CSS do aviso existe", /\.licao-aviso\b/.test(cssSrc));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: os 7 checks da seção [12] falham.

- [ ] **Step 3: Alternativa no halo**

Em `game.js`, em `_guiaAplicarHalo`, troque

```javascript
  let el = document.querySelector(sel.css);
  if(el && sel.ancestral) el = el.closest(sel.ancestral);
  if(!el) return;
```

por

```javascript
  let el = document.querySelector(sel.css);
  if(el && sel.ancestral) el = el.closest(sel.ancestral);
  if(!el && sel.alternativa) el = document.querySelector(sel.alternativa);
  if(!el) return;
```

- [ ] **Step 4: Elemento do aviso e função**

Em `_mostrarJanelaLicao`, no template, logo **depois** da linha ``<div class="licao-dica" id="licao-dica" style="display:none"></div>` +`` acrescente:

```javascript
    `<div class="licao-aviso" id="licao-aviso" style="display:none"></div>` +
```

Logo antes de `function _guiaMostrar(){...}`, acrescente:

```javascript
let _guiaAvisoTimer = null;
// Aviso curto (dica de erro ou resultado do ataque): na janela da lição se ela está
// aberta, senão no toast — quem fechou a janela também precisa saber.
function _guiaAviso(texto){
  if(!texto) return;
  const host = $('licao-aviso');
  if(host && $('licao-janela')?.classList.contains('open')){
    host.textContent = texto;
    host.style.display = 'block';
    if(_guiaAvisoTimer) clearTimeout(_guiaAvisoTimer);
    _guiaAvisoTimer = setTimeout(() => { host.style.display = 'none'; }, 7000);
  } else {
    toast(texto, '#f0c867');
  }
}
```

- [ ] **Step 5: Ouvintes**

Logo depois do bloco `GS.on('licaoPasso', ...)`, acrescente:

```javascript
GS.on('licaoDica', msg => {
  if(!msg || !/^[a-z_]+$/.test(msg.motivo || '')) return;
  const chave = 'ui.tutorial.dica_erro.' + msg.motivo;
  const texto = t(chave);
  if(texto && texto !== chave) _guiaAviso(texto);
});

GS.on('licaoResultado', msg => {
  if(!msg || !/^[a-z_]+$/.test(msg.chave || '')) return;
  const chave = 'ui.tutorial.resultado.' + msg.chave;
  const texto = t(chave, {roll: msg.roll, bonus: msg.bonus, total: msg.total, ca: msg.ca});
  if(texto && texto !== chave) _guiaAviso(texto);
});
```

- [ ] **Step 6: CSS**

Em `game.css`, depois da regra `#licao-janela .licao-dica{...}`, acrescente:

```css
#licao-janela .licao-aviso{ margin-top:8px; padding:6px 8px; border-left:3px solid #e8d8a0;
  background:#ffffff14; font-size:.82rem; line-height:1.35; }
```

- [ ] **Step 7: Rodar**

Run: `node --check game.js && node tools/test_guia_tutorial_cliente.js && PYTHONIOENCODING=utf-8 python tools/test_interface.py`
Expected: sem erro de sintaxe, `0 falha(s)`, `test_interface` sem literal novo em português.

- [ ] **Step 8: Commit**

```bash
git status --short game.js game.css
git diff --stat game.js game.css
git diff --cached --stat
git commit -m "feat(tutorial): aviso temporário de dica e resultado na janela da lição" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- game.js game.css tools/test_guia_tutorial_cliente.js
```

---

### Task 7: Halo no tabuleiro 2D (casa, monstro, porta com caminho)

**Files:**
- Modify: `game.js` (`_guiaTick`; nova função `_guiaDesenhar2D`; chamada em `renderMap` perto de `_drawDefeatVisuals2D`)
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever os testes que falham**

```javascript
console.log("\n[13] halo 2D no game.js");
check("função _guiaDesenhar2D existe", /function _guiaDesenhar2D\(/.test(gameSrc));
check("renderMap 2D chama _guiaDesenhar2D", /_guiaDesenhar2D\(ctx, state, visionSet\)/.test(gameSrc));
check("o desenho usa alvoTabuleiro e caminhoAbsoluto",
      /GuiaTutorial\.alvoTabuleiro\(/.test(gameSrc) && /GuiaTutorial\.caminhoAbsoluto\(/.test(gameSrc));
check("o halo 2D mantém a animação por _agendarChamas2D", /_guiaDesenhar2D[\s\S]{0,1800}_agendarChamas2D\(\)/.test(gameSrc));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: os 4 checks da seção [13] falham.

- [ ] **Step 3: Implementar**

Em `game.js`, logo depois de `_guiaMostrar` (e do `_guiaAviso` da tarefa anterior), acrescente:

```javascript
// ── Halo no tabuleiro ─────────────────────────────────────────────────────
// Alvo (casa, porta ou monstro) do passo atual, ou null. `visivel(x,y)` impede o
// halo de revelar o que a névoa esconde.
function _guiaAlvoTabuleiro(state, visivel){
  if(!_guiaPasso || !_guiaPasso.ui || !state) return null;
  const me = (state.players || []).find(p => p.id === GS.myPid);
  return GuiaTutorial.alvoTabuleiro(_guiaPasso.ui, state, me ? me.pos : null, visivel);
}

// Caminho até a porta, com cache por (minha casa, porta, rodada): o BFS não pode
// rodar a cada quadro.
let _guiaCaminhoChave = '', _guiaCaminhoCache = [];
function _guiaCaminhoAteAlvo(state, alvo){
  if(!alvo || !alvo.caminho) return [];
  const me = (state.players || []).find(p => p.id === GS.myPid);
  if(!me || !me.pos) return [];
  const chave = `${me.pos[0]},${me.pos[1]}>${alvo.pos[0]},${alvo.pos[1]}@${state.round}`;
  if(chave === _guiaCaminhoChave) return _guiaCaminhoCache;
  const exp = new Set((state.explored || []).map(([x, y]) => `${x},${y}`));
  for(const [rx, ry] of (state.revealed || [])) exp.add(`${rx},${ry}`);
  const passos = GS.findPath(state.tiles, exp, me.pos[0], me.pos[1], alvo.pos[0], alvo.pos[1], 60, true);
  _guiaCaminhoChave = chave;
  _guiaCaminhoCache = GuiaTutorial.caminhoAbsoluto(passos, me.pos[0], me.pos[1]);
  return _guiaCaminhoCache;
}

function _guiaForte(){
  return GuiaTutorial.nivelDica(_guiaDesde, performance.now(), _guiaCfg()) >= 1;
}

// 2D: anel pulsante + seta dourada sobre a casa; porta ganha linha tracejada.
function _guiaDesenhar2D(ctx, state, visionSet){
  const alvo = _guiaAlvoTabuleiro(state, (x, y) => visionSet.has(`${x},${y}`));
  if(!alvo) return;
  const agora = performance.now();
  const forte = _guiaForte();
  const pulso = 0.5 + 0.5 * Math.sin(agora / (forte ? 260 : 420));
  const cx = alvo.pos[0] * CELL + CELL / 2, cy = alvo.pos[1] * CELL + CELL / 2;
  ctx.save();
  const trilha = _guiaCaminhoAteAlvo(state, alvo);
  if(trilha.length){
    ctx.strokeStyle = 'rgba(240,200,103,.85)'; ctx.lineWidth = 3;
    ctx.setLineDash([CELL * 0.14, CELL * 0.16]);
    ctx.lineDashOffset = -(agora / 60) % 100;
    ctx.beginPath();
    const me = (state.players || []).find(p => p.id === GS.myPid);
    ctx.moveTo(me.pos[0] * CELL + CELL / 2, me.pos[1] * CELL + CELL / 2);
    for(const [x, y] of trilha) ctx.lineTo(x * CELL + CELL / 2, y * CELL + CELL / 2);
    ctx.stroke();
    ctx.setLineDash([]);
  }
  ctx.shadowColor = 'rgba(255,200,60,.95)'; ctx.shadowBlur = 14 + 10 * pulso;
  ctx.strokeStyle = '#f0c867'; ctx.lineWidth = (forte ? 5 : 3.5) + 2 * pulso;
  ctx.beginPath(); ctx.arc(cx, cy, CELL * (0.40 + 0.07 * pulso), 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
  _desenharSetaVez2D(ctx, cx, alvo.pos[1] * CELL - CELL * 0.02 - CELL * 0.08 * pulso);
  _agendarChamas2D();   // o 2D só redesenha quando algo muda; isto mantém o pulso (~12 quadros/s)
}
```

Em `_guiaTick`, depois de `_guiaAplicarHalo();`, acrescente (só quando o passo tem alvo de tabuleiro, para o 2D não redesenhar o mapa à toa durante a lição):

```javascript
  if(!(mode3D && g3) && GS.gameState && _guiaPasso.ui && !GuiaTutorial.seletor(_guiaPasso.ui)
     && GuiaTutorial.parseUi(_guiaPasso.ui)) _agendarChamas2D();
```

Em `renderMap` (2D), logo antes de `_drawDefeatVisuals2D(ctx, state, _agoraRelampago);` (fim da função), acrescente:

```javascript
  _guiaDesenhar2D(ctx, state, visionSet);
```

- [ ] **Step 4: Rodar**

Run: `node --check game.js && node tools/test_guia_tutorial_cliente.js && PYTHONIOENCODING=utf-8 python tools/test_interface.py`
Expected: sem erro de sintaxe, `0 falha(s)`, interface sem literal novo.

- [ ] **Step 5: Commit**

```bash
git status --short game.js
git diff --stat game.js
git diff --cached --stat
git commit -m "feat(tutorial): halo no tabuleiro 2D (casa, monstro, porta com caminho)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- game.js tools/test_guia_tutorial_cliente.js
```

---

### Task 8: Halo no tabuleiro 3D

**Files:**
- Modify: `game.js` (nova função `_guiaAtualizar3D`; chamada no laço de `startLoop3D` junto de `g3.setaVez`; descarte em `dispose3D`)
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever os testes que falham**

```javascript
console.log("\n[14] halo 3D no game.js");
check("função _guiaAtualizar3D existe", /function _guiaAtualizar3D\(/.test(gameSrc));
check("o laço 3D chama _guiaAtualizar3D", /startLoop3D[\s\S]{0,40000}_guiaAtualizar3D\(\)/.test(gameSrc));
check("dispose3D libera a marca do guia", /function dispose3D[\s\S]{0,6000}guiaMarca/.test(gameSrc));
check("a marca 3D usa topoSuperficie3D", /_guiaAtualizar3D[\s\S]{0,2500}topoSuperficie3D\(/.test(gameSrc));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: os 4 checks da seção [14] falham.

- [ ] **Step 3: Implementar**

Em `game.js`, logo depois de `_guiaDesenhar2D`, acrescente:

```javascript
// 3D: uma única marca reutilizável (anel no chão + seta + até 48 pontos de trilha),
// criada na primeira vez e escondida quando não há alvo. Nunca cria nada por quadro.
const GUIA_TRILHA_MAX = 48;
function _guiaMarca3D(){
  if(g3.guiaMarca) return g3.guiaMarca;
  const T = g3.T;
  const mat = new T.MeshBasicMaterial({ color: 0xf0c867, transparent: true, opacity: .95,
    side: T.DoubleSide, depthTest: false, depthWrite: false, toneMapped: false });
  const anel = new T.Mesh(new T.RingGeometry(0.33, 0.45, 40), mat);
  anel.rotation.x = -Math.PI / 2; anel.renderOrder = 81; anel.raycast = () => {};
  const seta = _criarSetaVez3D(T); seta.visible = true;
  const grupoTrilha = new T.Group();
  const geoPonto = new T.CircleGeometry(0.07, 10);
  const pontos = [];
  for(let i = 0; i < GUIA_TRILHA_MAX; i++){
    const p = new T.Mesh(geoPonto, mat);
    p.rotation.x = -Math.PI / 2; p.renderOrder = 80; p.visible = false; p.raycast = () => {};
    grupoTrilha.add(p); pontos.push(p);
  }
  const grupo = new T.Group();
  grupo.add(anel); grupo.add(seta); grupo.add(grupoTrilha);
  grupo.visible = false;
  g3.scene.add(grupo);
  g3.guiaMarca = { grupo, anel, seta, pontos, mat, geoAnel: anel.geometry, geoPonto };
  return g3.guiaMarca;
}

// Visão do jogador, recalculada só quando o estado muda.
let _guiaVisaoRef = null, _guiaVisaoSet = null;
function _guiaVisao3D(state){
  if(_guiaVisaoRef !== state){
    const me = (state.players || []).find(p => p.id === GS.myPid && p.alive);
    _guiaVisaoSet = (GS.isMaster() || state.test_mode)
      ? null : computeVisionSet(state, me);
    _guiaVisaoRef = state;
  }
  return _guiaVisaoSet;
}

function _guiaAtualizar3D(){
  if(!g3) return;
  const st = GS.gameState;
  let alvo = null;
  if(st && _guiaPasso && _guiaPasso.ui){
    const vis = _guiaVisao3D(st);
    alvo = _guiaAlvoTabuleiro(st, vis ? ((x, y) => vis.has(`${x},${y}`)) : (() => true));
  }
  if(!alvo){ if(g3.guiaMarca) g3.guiaMarca.grupo.visible = false; return; }
  const m = _guiaMarca3D();
  const agora = performance.now();
  const forte = _guiaForte();
  const pulso = 0.5 + 0.5 * Math.sin(agora / (forte ? 260 : 420));
  let x = alvo.pos[0], z = alvo.pos[1];
  if(alvo.tipo === 'monstro'){
    const mesh = getMonsterMesh(alvo.id);
    if(mesh){ x = mesh.position.x; z = mesh.position.z; }
  }
  const y = topoSuperficie3D(st, alvo.pos[0], alvo.pos[1]) + 0.04;
  m.anel.position.set(x, y, z);
  m.anel.scale.setScalar(1 + 0.18 * pulso);
  m.mat.opacity = 0.65 + 0.35 * pulso;
  m.seta.position.set(x, y + 1.0 + 0.1 * pulso, z);
  const trilha = _guiaCaminhoAteAlvo(st, alvo);
  for(let i = 0; i < m.pontos.length; i++){
    const c = trilha[i];
    const p = m.pontos[i];
    if(!c || i === trilha.length - 1){ p.visible = false; continue; }   // a última casa é o próprio anel
    p.visible = ((i + Math.floor(agora / 220)) % 2) === 0;              // pontos alternados "andam"
    p.position.set(c[0], topoSuperficie3D(st, c[0], c[1]) + 0.05, c[1]);
  }
  m.grupo.visible = true;
}
```

No laço de `startLoop3D`, logo **depois** do bloco `if(g3.setaVez){ ... }` (o que posiciona `g3.setaVez`, ~linha 44735), acrescente:

```javascript
    _guiaAtualizar3D();
```

Em `dispose3D`, logo depois do bloco que libera `g3.setaVez`, acrescente:

```javascript
  if(g3.guiaMarca){
    const m = g3.guiaMarca;
    g3.scene.remove(m.grupo);
    m.seta.material.map?.dispose(); m.seta.material.dispose();
    m.geoAnel.dispose(); m.geoPonto.dispose(); m.mat.dispose();
    g3.guiaMarca = null;
  }
```

- [ ] **Step 4: Rodar**

Run: `node --check game.js && node tools/test_guia_tutorial_cliente.js && PYTHONIOENCODING=utf-8 python tools/test_interface.py`
Expected: `0 falha(s)`.

- [ ] **Step 5: Commit**

```bash
git status --short game.js
git diff --stat game.js
git diff --cached --stat
git commit -m "feat(tutorial): halo no tabuleiro 3D (anel, seta e trilha até a porta)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- game.js tools/test_guia_tutorial_cliente.js
```

---

### Task 9: Prova no navegador e documentação

**Files:**
- Modify: `CLAUDE.md` (CRLF; use Edit)

- [ ] **Step 1: Servidor isolado**

```bash
TMP="$TEMP/lfh_guia2"; rm -rf "$TMP"; mkdir -p "$TMP"
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro" && git archive HEAD | tar -x -C "$TMP"
cd "$TMP" && (LFH_PORT=8790 PYTHONIOENCODING=utf-8 nohup python server.py > server.log 2>&1 &)
```

Aguarde ~6 s e confirme `curl -s -o /dev/null -w "%{http_code}" "http://[::1]:8790/index.html"` = 200. Não use a 8765.

- [ ] **Step 2: Entrar no Campo de Treinamento**

No navegador do app, abra `http://[::1]:8790/index.html?v=guia2`, clique para começar, e no console execute `window.confirm = () => true;` (o navegador do app bloqueia `confirm()`). Crie uma conta de teste local (apelido `TesteGuia`, senha `teste1234`) com "Acessar minha conta", crie um jogo solo ("Criar jogo"), e então no console:

```javascript
send({type:'select_class', class_id:'warrior'}); await new Promise(r=>setTimeout(r,800)); startGame(); await new Promise(r=>setTimeout(r,2500));
GS.worldAdventure('treinamento'); await new Promise(r=>setTimeout(r,5000)); 'ok'
```

- [ ] **Step 3: Halo de casa (2D) e porta com caminho**

A primeira lição (`fala_0`) é `mover_ate [5,15]`: o servidor já deriva `ui: "casa:[5,15]"`. No modo 2D (botão 2D/3D do HUD), confirme por captura de tela que o anel dourado com seta aparece na casa (5,15) e pulsa. Para a porta, no console:

```javascript
_mostrarJanelaLicao({licao_id:'fala_0', falante:{nome:'T',emoji:'🧪'}, texto:'x', passo:{i:0,n:1,texto:'Vá até a porta.',ui:'porta:[13,15]',auto:false,informativo:false,dica:[]}}); 'ok'
```

Esperado: anel na porta (13,15) e linha tracejada saindo do herói até ela.

- [ ] **Step 4: 3D**

Alterne para o 3D. Repita os dois passos acima. Esperado: anel dourado no chão, seta flutuando e pontos da trilha até a porta. Troque para um alvo de monstro:

```javascript
_mostrarJanelaLicao({licao_id:'fala_0', falante:{nome:'T',emoji:'🧪'}, texto:'x', passo:{i:0,n:1,texto:'Ataque o boneco.',ui:'monstro:boneco_treino',auto:false,informativo:false,dica:[]}}); 'ok'
```

Só deve aparecer se o boneco estiver à vista; ande até a sala dos bonecos para ver o halo no boneco. Com a janela do app oculta o `requestAnimationFrame` não roda: se a captura sair parada, use um polyfill (`window.requestAnimationFrame = f => setTimeout(() => f(performance.now()), 16)`) ou meça pelo estado (`g3.guiaMarca.grupo.visible`).

- [ ] **Step 5: Bolsa**

Pegue uma arma do baú (lição `fala_1`), abra a mochila (🎒) e injete `ui:'bolsa:<id da arma>'`: o espaço da bolsa com aquele item deve ganhar o halo; com a mochila fechada, o halo vai para o botão 🎒.

- [ ] **Step 6: Dica por erro e resultado**

Com a lição de atacar (`fala_5`, sala do guerreiro), tente encerrar fora da vez ou atacar o esqueleto em vez do boneco: o aviso "Esse não é o alvo do exercício…" aparece na janela por ~7 s. Acerte um boneco: o aviso "Você rolou … contra CA …: acertou!" aparece. Feche a janela da lição e repita: o aviso vem em toast.

- [ ] **Step 7: Console limpo**

`read_console_messages` com `onlyErrors`. Esperado: nenhum erro.

- [ ] **Step 8: Encerrar**

Pare o servidor da 8790 (`Get-NetTCPConnection -LocalPort 8790` e `Stop-Process`) e apague `$TEMP/lfh_guia2`.

- [ ] **Step 9: Atualizar o `CLAUDE.md`**

No parágrafo "Tutorial guiado — fatia 1 (2026-10-07)" (Edit), troque a frase "Nesta fatia o halo só existe para HUD (`botao`, `habilidade`, `hud`); `casa`, `monstro`, `porta`, `bolsa` e `slot` são aceitos e ainda não desenhados." por:

```
O halo existe para HUD (`botao`, `habilidade`), para a bolsa e os slots do inventário (`data-item-id`/`data-slot-key`, com o botão 🎒 como alternativa quando o inventário está fechado) e para o tabuleiro (`casa`, `monstro`, `porta`: anel + seta no 2D e no 3D, linha tracejada até a porta; `GuiaTutorial.alvoTabuleiro` filtra pela visão do jogador, então nunca revela o que a névoa esconde); `hud:<id>` ainda não é desenhado. **Dica por erro:** `send_to` converte recusas conhecidas (`GUIA_DICA_POR_ERRO`/`GUIA_DICA_POR_PREFIXO`) e acertar o tipo errado de alvo em `_licao_evento` na mensagem `licao_dica {motivo}` (no máximo uma a cada `GUIA_DICA_INTERVALO_S`; `alvo_errado` e `longe_do_alvo` só em tarefa com alvo de combate); o cliente traduz `ui.tutorial.dica_erro.<motivo>`. **Resultado:** `handle_attack` emite `licao_resultado {chave, roll, bonus, total, ca}` (`_guia_resultado_ataque`) para quem tem lição pendente; o cliente mostra `ui.tutorial.resultado.<chave>` na janela ou em toast.
```

e acrescente ao fim do mesmo parágrafo: ` Plano da fatia 2: \`docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia2-tabuleiro.md\`.`

- [ ] **Step 10: Suítes finais**

Run:
```bash
PYTHONIOENCODING=utf-8 python tools/test_tutorial_guia.py
PYTHONIOENCODING=utf-8 python tools/test_tutorial_salas.py
PYTHONIOENCODING=utf-8 python tools/test_salvar_masmorra.py
PYTHONIOENCODING=utf-8 python tools/test_idioma.py
PYTHONIOENCODING=utf-8 python tools/test_interface.py
PYTHONIOENCODING=utf-8 python tools/dividas.py
node tools/test_guia_tutorial_cliente.js
node tools/test_tutorial_cliente.js
node tools/test_idioma_cliente.js
```
Expected: tudo verde, `nada pendente`.

- [ ] **Step 11: Commit**

```bash
git status --short CLAUDE.md
git diff --cached --stat
git commit -m "docs: guia do tutorial (fatia 2) no CLAUDE.md" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -- CLAUDE.md
```

---

## Auto-revisão contra a spec

| Item da spec | Onde está |
|---|---|
| 2 Servidor: dica por erro (motivos, rate limit) | Task 1 (`alvo_errado`, `longe_do_alvo`, `fora_da_vez`, `sem_acao`; `habilidade_nao_armada` ficou fora, ver "Fora desta fatia") |
| 2 Servidor: `licao_resultado` | Task 2 |
| 3.1 `bolsa:`, `slot:`, `casa:`, `porta:`, `monstro:` | Tasks 4 e 5 (seletores de DOM), 7 e 8 (tabuleiro) |
| 4.2 Halo 2D e 3D, porta com caminho tracejado | Tasks 7 e 8 |
| 4.2 Seta na borda para alvo fora da visão | Adiado (o halo não aparece); registrado em "Fora desta fatia" |
| 4.5 Resultado da ação (janela ou toast) | Tasks 5 e 6 |
| 6 Parâmetros (`DICA_*`, intervalo de 5 s) | `GUIA_DICA_INTERVALO_S` (Task 1); `VC.tutorial` já existe |
| 8 Testes | Tasks 1 a 8; prova no navegador na Task 9 |

Consistência de nomes: `GUIA_DICA_POR_ERRO`, `GUIA_DICA_POR_PREFIXO`, `GUIA_DICA_EXIGE_ALVO`, `GUIA_TAREFAS_COM_ALVO`, `GUIA_DICA_INTERVALO_S`, `_GUIA_DICA_ULTIMA`, `_guia_dica`, `_guia_dica_por_erro`, `_guia_resultado_ataque`, mensagens `licao_dica`/`licao_resultado`, eventos `licaoDica`/`licaoResultado`, `GuiaTutorial.{seletor,alvoTabuleiro,caminhoAbsoluto}`, `_guiaAlvoTabuleiro`, `_guiaCaminhoAteAlvo`, `_guiaForte`, `_guiaDesenhar2D`, `_guiaMarca3D`, `_guiaAtualizar3D`, `_guiaAviso`, `g3.guiaMarca`. Os mesmos nomes aparecem nos testes e na implementação.
