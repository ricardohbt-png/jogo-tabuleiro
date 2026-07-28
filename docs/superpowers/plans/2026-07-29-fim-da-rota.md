# Fim da rota — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** O destino de aventura ganha uma história própria de fim de rota, exibida logo após o encerramento da última etapa, antes de o grupo chegar à cidade.

**Architecture:** Um campo `outro_rota` no destino, salvo pelo mesmo `_clean_story_field` dos demais campos de história. No servidor, o beat de encerramento passa a ser montado com duas partes e `_story_beat` faz o resto — ele já concatena na ordem e descarta o que estiver vazio. No editor, mais um botão que abre o painel de slides compartilhado.

**Tech Stack:** Python 3 + `websockets` (servidor autoritativo), JS vanilla sem bundler (`tools/editor_world.js`, `tools/editor_story.js`), testes em scripts `asyncio` (`tools/test_*.py`).

**Spec:** `docs/superpowers/specs/2026-07-29-fim-da-rota-design.md`

---

## Contexto que o implementador precisa

**Rodar um teste:** da raiz, `python tools/test_masmorra_sequenciada.py`. Imprime `=== N passou, M falhou ===`. Não há pytest — cada suíte é um script com `check(nome, condição)`. Hoje a suíte está em **108 passou, 0 falhou**.

**O sistema de história:** `_story_beat(key, parts)` (server.py) normaliza cada parte com `_story_norm` (aceita string ou `{slides:[{text,image,fit}], audio}`), concatena os slides **na ordem das partes**, pega o primeiro áudio não-vazio e devolve `None` se não sobrar slide nenhum. `_clean_story_field(raw)` é a versão de persistência: aceita os mesmos formatos e restringe mídia a `assets/story/`.

**Onde o encerramento é montado hoje** (`handle_encerrar_missao`, ramo `if self.world_adventure_id:`):

```python
            fim = _story_beat(f"fim:{adventure_id}:{completed_index}",
                              [etapa.get("outro")])
```

`etapa` é `_etapa_obj(stages[completed_index])` e `stages` é `list(adventure.get("dungeons") or [])`, ambos já definidos algumas linhas acima nesse mesmo ramo.

**O editor de slides compartilhado:** `window.EDITOR_STORY` (`tools/editor_story.js`) expõe `emptyStory`, `storyFromSaved`, `storyToSaved`, `storyCount`, `histButtonHTML`, `pickFile`, `openHistoryEditor`, `previewStory`. O padrão já usado nas etapas: guardar o objeto normalizado em memória (`_introSt`/`_outroSt`), renderizar o botão com `histButtonHTML`, abrir com `openHistoryEditor(st, rótulo, render)` e serializar com `storyToSaved` no salvar.

**Convenção de commit:** mensagens em português, prefixo `feat(...)`/`docs(...)`. **Faça `git add` só dos arquivos que você tocou** — nunca `git add -A`; o usuário edita `server.py`, `game.js` e `tools/editor.js` em paralelo e mantém dados/arte não commitados.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta feature |
|---|---|
| `server.py` | Campo `outro_rota` persistido; beat com a parte de fim de rota |
| `tools/editor_world.js` | Botão "🏁 fim da rota" no painel do destino |
| `tools/test_masmorra_sequenciada.py` | Seção [19] |

---

### Task 1: O beat de fim de rota

**Files:**
- Modify: `server.py` (`_save_world_adventures_upload`, `handle_encerrar_missao`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_masmorra_sequenciada.py`, ADICIONE antes de `async def main()`:

```python
def _textos(beat):
    return [s.get("text") for s in beat["slides"]] if beat else None

async def test_fim_da_rota():
    print("\n[19] fim da rota ao concluir a última etapa")
    # rota de 2 etapas, nenhuma encadeada, com fim de rota autorado
    r = setup_room(encadear=False)
    server.WORLD_ADVENTURES["test_seq"]["outro_rota"] = "FIM-DA-ROTA"
    await r.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r)
    check("etapa intermediária: só o encerramento dela",
          _textos(r._story_encadeada) == ["FECHA-1"])
    # segunda (e última) etapa
    await r.handle_world_adventure("p1", "test_seq")
    check("entrou na etapa 2", r.world_adventure_index == 1)
    server.WORLD_ADVENTURES["test_seq"]["dungeons"][1]["outro"] = "FECHA-2"
    await _concluir_etapa(r)
    check("última etapa: encerramento da etapa + fim da rota, nessa ordem",
          _textos(r._story_encadeada) == ["FECHA-2", "FIM-DA-ROTA"])
    check("key continua a da etapa concluída",
          r._story_encadeada["key"] == "fim:test_seq:1")
    # sem outro_rota, o comportamento é o de antes
    r2 = setup_room(encadear=False)
    server.WORLD_ADVENTURES["test_seq"].pop("outro_rota", None)
    await r2.handle_world_adventure("p1", "test_seq")
    await _concluir_etapa(r2)
    check("sem fim de rota, só o encerramento da etapa",
          _textos(r2._story_encadeada) == ["FECHA-1"])

def test_fim_da_rota_persistido():
    print("\n[19b] fim da rota sobrevive ao salvar")
    row = {"id": "rota_fim", "nome": "Rota", "x": 10, "y": 20, "fome": 0, "sede": 0,
           "outro_rota": {"slides": [{"text": "acabou", "image": "assets/story/f.png"}],
                          "audio": "assets/story/tema.mp3"},
           "dungeons": ["test_camp_a.json"]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou ({res if not ok else 'ok'})", ok is True)
        av = server.WORLD_ADVENTURES["rota_fim"]
        check("outro_rota preservado como objeto", isinstance(av["outro_rota"], dict))
        check("slide preservado",
              av["outro_rota"]["slides"][0] == {"text": "acabou",
                                                "image": "assets/story/f.png"})
        check("áudio preservado", av["outro_rota"]["audio"] == "assets/story/tema.mp3")
        # destino sem o campo fica com string vazia (nada a exibir)
        row2 = dict(row, id="rota_sem"); row2.pop("outro_rota")
        server._save_world_adventures_upload([], [row2])
        check("ausente vira vazio",
              server.WORLD_ADVENTURES["rota_sem"]["outro_rota"] == "")
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()
```

E em `main()`, ACRESCENTE as chamadas — a síncrona junto das demais síncronas
(depois de `test_flag_persistida()`):

```python
    test_fim_da_rota_persistido()
```

e a corrotina junto das demais (depois de `await test_oculto_recusa_generica()`):

```python
    await test_fim_da_rota()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "última etapa: encerramento da etapa + fim da rota, nessa ordem" (vem só `["FECHA-2"]`) e em "outro_rota preservado como objeto" (`KeyError`/`None`).

- [ ] **Step 3: Persistir o campo**

Em `server.py`, em `_save_world_adventures_upload`, no dict `cleaned[aid]`, SUBSTITUA:

```python
                        "oculto_ate_liberar": bool(row.get("oculto_ate_liberar")),
                        "requisito": req, "renome_recompensa": renome_reward}
```

por:

```python
                        "oculto_ate_liberar": bool(row.get("oculto_ate_liberar")),
                        "outro_rota": _clean_story_field(row.get("outro_rota")),
                        "requisito": req, "renome_recompensa": renome_reward}
```

- [ ] **Step 4: Emendar o fim da rota no beat**

Em `server.py`, em `handle_encerrar_missao`, SUBSTITUA:

```python
            fim = _story_beat(f"fim:{adventure_id}:{completed_index}",
                              [etapa.get("outro")])
```

por:

```python
            # A última etapa fecha a rota: o encerramento dela e o fim da rota saem
            # no mesmo slideshow, nessa ordem. _story_beat descarta as partes vazias.
            partes = [etapa.get("outro")]
            if completed_index + 1 >= len(stages):
                partes.append(adventure.get("outro_rota"))
            fim = _story_beat(f"fim:{adventure_id}:{completed_index}", partes)
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 118 passou, 0 falhou ===` (108 de hoje + 10 checagens novas)

- [ ] **Step 6: Não-regressão**

Run: `python tools/test_campanha.py`
Expected: `0 falhou`

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(mapa-mundi): historia de fim de rota ao concluir a ultima etapa"
```

---

### Task 2: Botão "🏁 fim da rota" no editor

**Files:**
- Modify: `tools/editor_world.js` (destino novo, normalização, formulário, handler, salvar)

- [ ] **Step 1: Destino novo nasce com o campo**

Em `tools/editor_world.js`, no `push` do botão `#worlded-add`, SUBSTITUA:

```javascript
espera_retorno:{modo:'fixa',rodadas:0,dados:''},oculto_ate_liberar:false,requisito:{tipo:'nenhum',valor:''}});selected=id;render();};
```

por:

```javascript
espera_retorno:{modo:'fixa',rodadas:0,dados:''},oculto_ate_liberar:false,outro_rota:'',requisito:{tipo:'nenhum',valor:''}});selected=id;render();};
```

- [ ] **Step 2: Normalizar a história do destino em memória**

Na função `form`, LOGO APÓS a linha que normaliza `a.espera_retorno`:

```javascript
    a.espera_retorno=Object.assign({modo:'fixa',rodadas:0,dados:''},a.espera_retorno||{});
```

INSIRA:

```javascript
    // História de fim de rota: objeto de slides em memória, forma mínima ao salvar.
    if(!a._outroRotaSt) a._outroRotaSt=ES.storyFromSaved(a.outro_rota);
```

**Atenção:** a linha `const ES=window.EDITOR_STORY;` é declarada logo acima, na
normalização das etapas — o `ES` já está em escopo aqui.

- [ ] **Step 3: Botão no formulário**

Ainda em `form`, dentro do `host.innerHTML=...`, SUBSTITUA:

```javascript
<label>Renome por etapa concluída<input id="we-renome-reward" type="number" min="0" value="'+Number(a.renome_recompensa==null?1:a.renome_recompensa)+'"></label>
```

por:

```javascript
<label>Renome por etapa concluída<input id="we-renome-reward" type="number" min="0" value="'+Number(a.renome_recompensa==null?1:a.renome_recompensa)+'"></label><div class="worlded-cost"><span title="Aparece ao concluir a última etapa, depois do encerramento dela.">'+ES.histButtonHTML('we-outro-rota', a._outroRotaSt).replace('história','fim da rota').replace('📖','🏁')+'</span></div>
```

- [ ] **Step 4: Ligar o botão ao painel de slides**

Ainda em `form`, LOGO APÓS a linha que liga o seletor de espera:

```javascript
    $('#we-wait-mode',host).onchange=sync;
```

INSIRA:

```javascript
    const bFim=host.querySelector('.we-outro-rota');
    if(bFim) bFim.onclick=()=>ES.openHistoryEditor(a._outroRotaSt, 'fim da rota — '+(a.nome||''), render);
```

- [ ] **Step 5: Serializar ao salvar**

No handler `$('#worlded-save',root).onclick=...`, o `map` que monta `aventuras` hoje é:

```javascript
      const aventuras=config.adventures.map(av=>Object.assign({},av,{dungeons:(av.dungeons||[]).map(s=>{
```

SUBSTITUA essa linha por:

```javascript
      const aventuras=config.adventures.map(av=>Object.assign({},av,{
        outro_rota: av._outroRotaSt ? (ES.storyToSaved(av._outroRotaSt)||'') : (av.outro_rota||''),
        dungeons:(av.dungeons||[]).map(s=>{
```

- [ ] **Step 6: Verificar sintaxe**

Run: `node -e "global.window={};global.document={addEventListener(){}};require('./tools/editor_world.js');console.log('ok')"`
Expected: `ok`

- [ ] **Step 7: Verificar no editor real**

Com o servidor no ar (`python server.py`), abra `http://localhost:8765/tools/editor.html` → aba **Mapa do Mundo** → crie um destino de teste (botão "+ Adicionar destino"), adicione uma masmorra à sequência e confirme:

```
- o botão "🏁 fim da rota" aparece no painel do destino
- clicar abre o painel de slides; "＋ adicionar slide" e "escolher imagem" funcionam
- ao fechar, o contador aparece no botão (ex.: "🏁 fim da rota (1)")
- salvar grava outro_rota no destino
- recarregar a página traz os slides de volta
```

Confira o arquivo:

```bash
python -c "import json;d=json.load(open('world_adventures.json',encoding='utf-8'));print({k:v.get('outro_rota') for k,v in d.items()})"
```

- [ ] **Step 8: Remover o destino de teste**

Selecione o destino de teste, clique em "Remover destino" e salve. Confirme com o comando
do passo anterior que só os destinos originais do usuário permaneceram.

- [ ] **Step 9: Commit**

```bash
git add tools/editor_world.js
git commit -m "feat(editor): campo de fim da rota no painel do destino"
```

---

## Verificação final

- [ ] `python tools/test_masmorra_sequenciada.py` → `0 falhou`
- [ ] `python tools/test_campanha.py` → `0 falhou`
- [ ] `python tools/test_cidades_editor.py` → `0 falharam`
- [ ] Aba Mapa do Mundo conferida no navegador (Task 2, Step 7)
- [ ] `world_adventures.json` sem resíduo de teste
- [ ] Acrescentar ao bloco da história em slides no `CLAUDE.md`: o campo `outro_rota` do destino e a emenda no beat `fim:` quando a etapa concluída é a última
