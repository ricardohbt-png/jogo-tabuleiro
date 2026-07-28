# Destino oculto no mapa-múndi — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um destino de aventura marcado como oculto some do mapa-múndi até o requisito dele ser cumprido, e aparece sozinho quando for.

**Architecture:** O filtro é do servidor: `_city_state_payload` deixa de enviar o destino oculto e ainda bloqueado, então o cliente não muda em nada. O handler de entrada passa a responder como se o destino não existisse, para a mensagem de erro não vazar o requisito escondido. O editor ganha um checkbox no bloco de requisitos.

**Tech Stack:** Python 3 + `websockets` (servidor autoritativo), JS vanilla sem bundler (`tools/editor_world.js`), testes em scripts `asyncio` (`tools/test_*.py`).

**Spec:** `docs/superpowers/specs/2026-07-29-destino-oculto-ate-liberar-design.md`

---

## Contexto que o implementador precisa

**Rodar um teste:** da raiz, `python tools/test_masmorra_sequenciada.py`. Imprime `=== N passou, M falhou ===`. Não há pytest — cada suíte é um script com `check(nome, condição)`. Hoje a suíte está em **95 passou, 0 falhou**.

**Como um destino é bloqueado hoje:** `_avaliar_requisito(raw)` (server.py) devolve `(ok, motivos)` avaliando renome, nível mínimo do grupo, item-chave, fato de taverna e rota anterior concluída — todos opcionais e acumulativos (AND). Um requisito **vazio passa** (`ok=True`).

**Onde os destinos vão para o cliente:** `_city_state_payload` monta `world.adventures` a partir de `WORLD_ADVENTURES.values()`. O cliente (`game.js`, `showWorldMap`) desenha um marcador para cada item dessa lista — não há filtro no cliente.

**Onde o destino é salvo:** `_save_world_adventures_upload(raw_locations, raw_adventures)` valida e grava `world_adventures.json`; o dict final de cada destino é montado em `cleaned[aid] = {...}`.

**Convenção de commit:** mensagens em português, prefixo `feat(...)`/`test(...)`/`docs(...)`. **Faça `git add` só dos arquivos que você tocou** — nunca `git add -A`; o usuário mantém arquivos de dados e arte não commitados.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta feature |
|---|---|
| `server.py` | Campo `oculto_ate_liberar`, helper `_aventura_visivel`, filtro no `city_state`, guarda no handler |
| `tools/editor_world.js` | Checkbox "🕵️ ocultar no mapa até liberar" no bloco de requisitos |
| `tools/test_masmorra_sequenciada.py` | Seção [18] |

---

### Task 1: O destino oculto some do mapa

**Files:**
- Modify: `server.py` (`_save_world_adventures_upload`, helper novo, `_city_state_payload`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_masmorra_sequenciada.py`, ADICIONE antes de `async def main()`:

```python
def _aventura_oculta(oculto, renome_min=5):
    return {"id": "test_oculto", "nome": "Ruínas Esquecidas", "x": 20, "y": 30,
            "fome": 0, "sede": 0, "renome_recompensa": 1,
            "oculto_ate_liberar": oculto,
            "requisito": {"renome_min": renome_min, "nivel_grupo_min": 0,
                          "item_id": "", "fato": "", "aventura_id": ""},
            "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
            "dungeons": [{"file": "test_camp_a.json", "encadear": False,
                          "intro": "", "outro": ""}]}

def _ids_no_mapa(r):
    return [a["id"] for a in r._city_state_payload()["world"]["adventures"]]

async def test_destino_oculto():
    print("\n[18] destino oculto no mapa-múndi")
    salvos = server.WORLD_ADVENTURES
    try:
        # oculto + requisito não cumprido → some do mapa
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(True)}
        r = setup_room(); r.renome = 0
        check("oculto e bloqueado não aparece", "test_oculto" not in _ids_no_mapa(r))
        # requisito cumprido → aparece
        r.renome = 5
        check("oculto e liberado aparece", "test_oculto" in _ids_no_mapa(r))
        # sem o flag, bloqueado continua visível (não-regressão)
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(False)}
        r2 = setup_room(); r2.renome = 0
        check("sem o flag, bloqueado continua visível", "test_oculto" in _ids_no_mapa(r2))
        # o editor enxerga o destino oculto
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(True)}
        pay = server._world_adventures_editor_payload()
        check("editor lista o destino oculto",
              any(a["id"] == "test_oculto" for a in pay["adventures"]))
        # helper direto
        r3 = setup_room(); r3.renome = 0
        check("_aventura_visivel False quando oculto e bloqueado",
              r3._aventura_visivel(server.WORLD_ADVENTURES["test_oculto"]) is False)
        r3.renome = 5
        check("_aventura_visivel True quando liberado",
              r3._aventura_visivel(server.WORLD_ADVENTURES["test_oculto"]) is True)
    finally:
        server.WORLD_ADVENTURES = salvos

def test_flag_persistida():
    print("\n[18b] o flag sobrevive ao salvar")
    row = {"id": "rota_oculta", "nome": "Rota", "x": 10, "y": 20, "fome": 0, "sede": 0,
           "oculto_ate_liberar": True,
           "requisito": {"renome_min": 3},
           "dungeons": ["test_camp_a.json"]}
    salvos = server.WORLD_ADVENTURES
    try:
        ok, res = server._save_world_adventures_upload([], [row])
        check(f"salvou ({res if not ok else 'ok'})", ok is True)
        check("flag preservado",
              server.WORLD_ADVENTURES["rota_oculta"]["oculto_ate_liberar"] is True)
        # ausente vira False (rotas antigas continuam visíveis)
        row2 = dict(row, id="rota_normal"); row2.pop("oculto_ate_liberar")
        server._save_world_adventures_upload([], [row2])
        check("ausente vira False",
              server.WORLD_ADVENTURES["rota_normal"]["oculto_ate_liberar"] is False)
    finally:
        server.WORLD_ADVENTURES = salvos
        server._save_world_adventures()
```

E em `main()`, chame as duas logo após `test_slides_na_aventura()`:

```python
    test_flag_persistida()
```

e, junto das demais corrotinas (depois de `await test_beat_encerramento()`):

```python
    await test_destino_oculto()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_aventura_visivel'`

- [ ] **Step 3: Persistir o campo**

Em `server.py`, em `_save_world_adventures_upload`, no dict `cleaned[aid]`, SUBSTITUA:

```python
        cleaned[aid] = {"id": aid, "nome": name[:80], "x": x, "y": y,
                        "fome": fome, "sede": sede, "dungeons": etapas,
                        "espera_retorno": _clean_espera(row.get("espera_retorno")),
                        "requisito": req, "renome_recompensa": renome_reward}
```

por:

```python
        cleaned[aid] = {"id": aid, "nome": name[:80], "x": x, "y": y,
                        "fome": fome, "sede": sede, "dungeons": etapas,
                        "espera_retorno": _clean_espera(row.get("espera_retorno")),
                        "oculto_ate_liberar": bool(row.get("oculto_ate_liberar")),
                        "requisito": req, "renome_recompensa": renome_reward}
```

- [ ] **Step 4: Criar o helper de visibilidade**

Em `server.py`, LOGO APÓS o fim do método `_avaliar_requisito` (a linha `return not reasons, reasons`), INSIRA:

```python
    def _aventura_visivel(self, adventure):
        """Destino oculto some do mapa até o requisito ser cumprido. Sem o flag,
        o destino é sempre visível (bloqueado ou não), como sempre foi.
        Cuidado: requisito vazio passa em _avaliar_requisito — o flag sozinho,
        sem nenhum requisito, não esconde nada."""
        if not adventure.get("oculto_ate_liberar"):
            return True
        return self._avaliar_requisito(adventure.get("requisito"))[0]
```

- [ ] **Step 5: Filtrar o payload da cidade**

Em `_city_state_payload`, SUBSTITUA:

```python
                "adventures": [{**adventure,
                                "progresso": self.world_adventure_progress.get(adventure["id"], 0)}
                               for adventure in WORLD_ADVENTURES.values()],
```

por:

```python
                # Destino oculto e ainda bloqueado nem entra no payload — não há
                # o que espiar no cliente.
                "adventures": [{**adventure,
                                "progresso": self.world_adventure_progress.get(adventure["id"], 0)}
                               for adventure in WORLD_ADVENTURES.values()
                               if self._aventura_visivel(adventure)],
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 104 passou, 0 falhou ===`

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(mapa-mundi): destino oculto some do mapa ate o requisito ser cumprido"
```

---

### Task 2: A recusa não vaza o requisito escondido

`handle_world_adventure` hoje responde `"Destino bloqueado: requer renome 5, item-chave: …"`. Para um destino oculto isso entrega exatamente o que se quer esconder.

**Files:**
- Modify: `server.py` (`handle_world_adventure`)
- Test: `tools/test_masmorra_sequenciada.py`

- [ ] **Step 1: Escrever o teste que falha**

ADICIONE em `tools/test_masmorra_sequenciada.py`:

```python
async def test_oculto_recusa_generica():
    print("\n[18c] entrar num destino oculto responde como id inexistente")
    salvos = server.WORLD_ADVENTURES
    try:
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(True)}
        r = setup_room(); r.renome = 0
        erros = []
        async def cap(pid, msg):
            if msg.get("type") == "error": erros.append(msg["msg"])
        r.send_to = cap
        await r.handle_world_adventure("p1", "test_oculto")
        check("não entrou na masmorra", r.phase == "city")
        check("erro genérico de id inválido",
              erros and erros[-1] == "Destino de aventura inválido.")
        check("não vaza o requisito", all("renome" not in e for e in erros))
        # destino NÃO oculto mantém a mensagem detalhada (útil ao jogador)
        server.WORLD_ADVENTURES = {"test_oculto": _aventura_oculta(False)}
        r2 = setup_room(); r2.renome = 0
        erros2 = []
        async def cap2(pid, msg):
            if msg.get("type") == "error": erros2.append(msg["msg"])
        r2.send_to = cap2
        await r2.handle_world_adventure("p1", "test_oculto")
        check("visível mantém a mensagem detalhada",
              erros2 and "renome" in erros2[-1])
    finally:
        server.WORLD_ADVENTURES = salvos
```

E em `main()`, junto das demais corrotinas:

```python
    await test_oculto_recusa_generica()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: falha em "erro genérico de id inválido" (hoje vem `"Destino bloqueado: requer renome 5."`).

- [ ] **Step 3: Implementar a guarda**

Em `server.py`, em `handle_world_adventure`, SUBSTITUA:

```python
        allowed, reasons = self._avaliar_requisito(adventure.get("requisito"))
        if not allowed:
            await self.send_to(pid, {"type": "error", "msg": "Destino bloqueado: requer " + ", ".join(reasons) + "."})
            return
```

por:

```python
        allowed, reasons = self._avaliar_requisito(adventure.get("requisito"))
        if not allowed:
            # Destino oculto responde como id inexistente: a mensagem detalhada
            # entregaria justamente o requisito que se quis esconder.
            msg = ("Destino de aventura inválido." if adventure.get("oculto_ate_liberar")
                   else "Destino bloqueado: requer " + ", ".join(reasons) + ".")
            await self.send_to(pid, {"type": "error", "msg": msg})
            return
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_masmorra_sequenciada.py`
Expected: `=== 108 passou, 0 falhou ===`

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_masmorra_sequenciada.py
git commit -m "feat(mapa-mundi): recusa de destino oculto nao revela o requisito"
```

---

### Task 3: Checkbox no editor de mapa-múndi

**Files:**
- Modify: `tools/editor_world.js` (destino novo, formulário, sync)

- [ ] **Step 1: Destino novo nasce visível**

Em `tools/editor_world.js`, no `push` do botão `#worlded-add`, SUBSTITUA:

```javascript
config.adventures.push({id:id,nome:'Novo destino',x:50,y:50,fome:0,sede:0,dungeons:[],espera_retorno:{modo:'fixa',rodadas:0,dados:''},requisito:{tipo:'nenhum',valor:''}});selected=id;render();};
```

por:

```javascript
config.adventures.push({id:id,nome:'Novo destino',x:50,y:50,fome:0,sede:0,dungeons:[],espera_retorno:{modo:'fixa',rodadas:0,dados:''},oculto_ate_liberar:false,requisito:{tipo:'nenhum',valor:''}});selected=id;render();};
```

- [ ] **Step 2: Checkbox no bloco de requisitos**

Na função `form`, dentro do `host.innerHTML=...`, o bloco de requisitos termina com:

```javascript
<label>Rota anterior concluída (id)<input id="we-req-adventure" value="'+esc(req.aventura_id||'')+'"></label></div>
```

SUBSTITUA esse trecho por:

```javascript
<label>Rota anterior concluída (id)<input id="we-req-adventure" value="'+esc(req.aventura_id||'')+'"></label><label title="'+(temReq?'O ponto só aparece no mapa quando o requisito for cumprido.':'Preencha um requisito para poder ocultar.')+'"><input type="checkbox" id="we-hidden"'+(a.oculto_ate_liberar?' checked':'')+(temReq?'':' disabled')+'> 🕵️ ocultar no mapa até liberar</label></div>
```

E, LOGO ANTES da linha `host.innerHTML=...`, INSIRA o cálculo de `temReq`:

```javascript
    // Sem nenhum requisito preenchido, ocultar não faria efeito: requisito vazio
    // passa em _avaliar_requisito, então o ponto continuaria visível.
    const temReq = Number(req.renome_min)>0 || Number(req.nivel_grupo_min)>0
                || !!(req.item_id||'').trim() || !!(req.fato||'').trim()
                || !!(req.aventura_id||'').trim();
```

- [ ] **Step 3: Sincronizar o campo**

Na função `sync`, ACRESCENTE ao final (depois da linha que grava `a.espera_retorno`):

```javascript
      const cbH=$('#we-hidden',host); a.oculto_ate_liberar=!!(cbH&&cbH.checked&&!cbH.disabled);
```

E, para o checkbox habilitar/desabilitar assim que o autor preenche um requisito, ACRESCENTE logo após a linha `host.querySelectorAll('input').forEach(x=>x.onchange=sync);`:

```javascript
    ['#we-req-renome','#we-req-level','#we-req-item','#we-req-fact','#we-req-adventure']
      .forEach(sel=>{const el=$(sel,host); if(el) el.onchange=()=>{sync();render();};});
```

- [ ] **Step 4: Verificar no editor real**

Com o servidor no ar (`python server.py`), abra `http://localhost:8765/tools/editor.html` → aba **Mapa do Mundo** → selecione um destino. Confirme:

```
- sem requisito preenchido, o checkbox "🕵️ ocultar no mapa até liberar" está desabilitado
- ao digitar 5 em "Renome mínimo" e sair do campo, o checkbox habilita
- marcar o checkbox e salvar grava oculto_ate_liberar: true no destino
- recarregar a página traz o checkbox marcado
```

Confira o arquivo:

```bash
python -c "import json;d=json.load(open('world_adventures.json',encoding='utf-8'));print({k:(v.get('oculto_ate_liberar'),v.get('requisito',{}).get('renome_min')) for k,v in d.items()})"
```

- [ ] **Step 5: Desfazer o destino de teste**

Se você usou um destino real do usuário para testar, desmarque o checkbox, devolva o requisito ao valor original e salve de novo. Confirme com o comando acima que nada ficou alterado.

- [ ] **Step 6: Commit**

```bash
git add tools/editor_world.js
git commit -m "feat(editor): opcao de ocultar o destino no mapa ate liberar"
```

---

## Verificação final

- [ ] `python tools/test_masmorra_sequenciada.py` → `0 falhou`
- [ ] `python tools/test_campanha.py` → `0 falhou`
- [ ] `python tools/test_cidades_editor.py` → `0 falharam`
- [ ] `python tools/test_modo_mestre.py` → `0 falharam`
- [ ] Aba Mapa do Mundo conferida no navegador (Task 3, Step 4)
- [ ] `world_adventures.json` sem resíduo de teste
- [ ] Acrescentar ao bloco da feature no `CLAUDE.md`: o campo `oculto_ate_liberar`, o filtro em `_city_state_payload` via `_aventura_visivel` e a recusa genérica no `handle_world_adventure`
