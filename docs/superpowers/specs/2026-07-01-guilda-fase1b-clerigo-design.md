# Guilda dos Heróis — Fase 1b: Especializações do Clérigo

**Data:** 2026-07-01
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 1b (Clérigo). Fase 1 decomposta por classe. Feito: 1a (Guerreiro).
Próximas: Paladino, Ladino, Bardo, Mago.
**Depende de:** Fase 0 (infra da Guilda) + padrão estabelecido na Fase 1a
(`tem_espec`, entradas `categoria:"especializacao"` no `GUILD_CATALOG`,
`handle_guild_buy` valida classe/`requer`/posse/ouro).

---

## 1. Visão geral

Especializações = upgrades permanentes e sempre-ativos das habilidades-base
(sem slot, sem "equipar"). Esta sub-fase cobre o **Clérigo** (Frade Lewis,
`class_id: "cleric"`), cujos 4 milagres hoje estão no poder máximo. A Fase 1b
**enfraquece o baseline gratuito** e vende os níveis II/III na Guilda.

### Estado atual (confirmado no código)
Os 4 milagres são ações principais dedicadas (não passam pelo fluxo genérico de
`skill`; sem `mp`); INT modifica a cura; alcance via `_no_raio` (Chebyshev):
- **`handle_cura`** (server.py ~6303): `num_dados = max(1, min(3, pedido))` — jogador
  escolhe **1–3 d8**; `custo_sede = num_dados` (💧-1/dado); `alcance_extra` 0–2
  (🍖-1/ext; 1/4/7q). Já é poder máximo.
- **`handle_cura_area`** (~6354): `num_dados = max(1, min(3, pedido))`; `custo = num_dados*4`
  🍖 e 💧; **`raio = 5` fixo**.
- **`handle_purificacao`** (~6424): aceita `tipo` em `PURIFICACAO_CUSTOS` =
  `{veneno:🍖1, doenca:🍖2💧1, maldicao:🍖3💧2, petrificacao:🍖5💧5}` — hoje **todos os 4**.
- **`handle_ressurreicao`** (~6502): `custo_fome, custo_sede = 10, 10`; `alvo["hp"] = 1`
  (sempre 1 HP).

> **"Custo crescente de fome/sede" do spec já existe** via escala por dado (Cura/
> Massa) e por tipo (Purificação). Portanto **NÃO** há mecanismo de custo novo nesta
> sub-fase; a Ressurreição ganha custo por nível (definido abaixo).

---

## 2. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Modelo | Base grátis fraco; comprar Nível II/III sobe o teto. III exige II (linear por linha; sem portão cruzado). Preços II=150, III=200. |
| Cura | Base máx **1d8**; II → máx 2d8; III → máx 3d8. Jogador escolhe ≤ teto (menos dados = menos 💧). |
| Cura em Massa | Base **1d8, raio 2**; II → 2d8/raio 4; III → 3d8/raio 6. Dados e raio sobem juntos com o nível. |
| Purificação | Base **venenos**; II → +doenças; III → +maldições **e petrificação**. |
| Ressurreição | Base **1 HP** (🍖10💧10); II → **metade** dos PV (🍖15💧15); III → **PV cheio** (🍖20💧20). |
| Custo crescente | Já coberto pela escala existente (por dado/tipo); Ressurreição por nível (acima). Sem tabela baixo/médio/alto. |
| Arquitetura | Imperativa: catálogo p/ exibição/compra; gating inline nos 4 handlers via `tem_espec` + helpers. |
| Autoridade | Servidor autoritativo: mesmo se o cliente pedir mais dados/tipo não destravado, o servidor limita/recusa. |

---

## 3. Catálogo (`GUILD_CATALOG`, server.py)

Oito entradas `categoria:"especializacao"`, `classe:"cleric"`, `exclusiva:false`.
Especializações não têm `custo_fome`/`custo_sede`/`recarga_rodadas`.

```python
"clerigo_cura_2": {
    "id": "clerigo_cura_2", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_cura", "nivel": 2, "requer": None, "exclusiva": False,
    "preco": 150, "nome": "Cura II", "icon": "🙌",
    "desc": "Cura pode usar até 2d8 + INT.",
},
"clerigo_cura_3": {
    "id": "clerigo_cura_3", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_cura", "nivel": 3, "requer": "clerigo_cura_2", "exclusiva": False,
    "preco": 200, "nome": "Cura III", "icon": "🙌",
    "desc": "Cura pode usar até 3d8 + INT.",
},
"clerigo_massa_2": {
    "id": "clerigo_massa_2", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_massa", "nivel": 2, "requer": None, "exclusiva": False,
    "preco": 150, "nome": "Cura em Massa II", "icon": "🌟",
    "desc": "Cura em Massa: até 2d8 + INT, raio 4.",
},
"clerigo_massa_3": {
    "id": "clerigo_massa_3", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_massa", "nivel": 3, "requer": "clerigo_massa_2", "exclusiva": False,
    "preco": 200, "nome": "Cura em Massa III", "icon": "🌟",
    "desc": "Cura em Massa: até 3d8 + INT, raio 6.",
},
"clerigo_purif_2": {
    "id": "clerigo_purif_2", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_purif", "nivel": 2, "requer": None, "exclusiva": False,
    "preco": 150, "nome": "Purificação II", "icon": "✨",
    "desc": "Purificação também remove doenças.",
},
"clerigo_purif_3": {
    "id": "clerigo_purif_3", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_purif", "nivel": 3, "requer": "clerigo_purif_2", "exclusiva": False,
    "preco": 200, "nome": "Purificação III", "icon": "✨",
    "desc": "Purificação também remove maldições e petrificação.",
},
"clerigo_ressur_2": {
    "id": "clerigo_ressur_2", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_ressur", "nivel": 2, "requer": None, "exclusiva": False,
    "preco": 150, "nome": "Ressurreição II", "icon": "💫",
    "desc": "Ressurreição traz o aliado com metade dos PV (🍖15 💧15).",
},
"clerigo_ressur_3": {
    "id": "clerigo_ressur_3", "categoria": "especializacao", "classe": "cleric",
    "linha": "clerigo_ressur", "nivel": 3, "requer": "clerigo_ressur_2", "exclusiva": False,
    "preco": 200, "nome": "Ressurreição III", "icon": "💫",
    "desc": "Ressurreição traz o aliado com PV cheio (🍖20 💧20).",
},
```

`handle_guild_buy` (Fase 0) já valida classe/`requer`/posse/ouro e persiste. Sem
mudança no handler. Painel da Guilda já renderiza a aba Especializações.

---

## 4. Gating no servidor (helpers + os 4 handlers)

Helpers como métodos de `GameRoom` (perto dos helpers do Guerreiro
`_teto_combinacao`/`_golpe_raw`), usando `tem_espec(p, id)`:

```python
    def _cura_teto(self, p):
        """Máx. de d8 da Cura pela posse (1 base / 2 / 3)."""
        if tem_espec(p, "clerigo_cura_3"): return 3
        if tem_espec(p, "clerigo_cura_2"): return 2
        return 1

    def _massa_nivel(self, p):
        """Nível da Cura em Massa (1/2/3) — define teto de dados E raio."""
        if tem_espec(p, "clerigo_massa_3"): return 3
        if tem_espec(p, "clerigo_massa_2"): return 2
        return 1

    def _purif_tipos(self, p):
        """Tipos de purificação destravados pela posse."""
        tipos = {"veneno"}
        if tem_espec(p, "clerigo_purif_2"): tipos.add("doenca")
        if tem_espec(p, "clerigo_purif_3"): tipos |= {"maldicao", "petrificacao"}
        return tipos

    def _ressur_nivel(self, p):
        if tem_espec(p, "clerigo_ressur_3"): return 3
        if tem_espec(p, "clerigo_ressur_2"): return 2
        return 1
```

### 4.1 `handle_cura`
Trocar `num_dados = max(1, min(3, ...))` por:
```python
        num_dados = max(1, min(self._cura_teto(p), int((data or {}).get("num_dados", 1))))
```
(Resto inalterado — custo/alcance seguem por dado.)

### 4.2 `handle_cura_area`
Trocar `num_dados = max(1, min(3, ...))` e `raio = 5` por:
```python
        nivel = self._massa_nivel(p)
        num_dados = max(1, min(nivel, int((data or {}).get("num_dados", 1))))
        ...
        raio = 2 * nivel   # 2 / 4 / 6
```
(Custo `num_dados*4` inalterado.)

### 4.3 `handle_purificacao`
Após validar que `tipo in self.PURIFICACAO_CUSTOS`, adicionar checagem de posse:
```python
        if tipo not in self._purif_tipos(p):
            await self.send_to(pid, {"type": "error",
                "msg": "Você ainda não aprendeu a purificar este mal — evolua a Purificação na Guilda."}); return
```
(Custo por tipo em `PURIFICACAO_CUSTOS` inalterado.)

### 4.4 `handle_ressurreicao`
Trocar o custo fixo e o `alvo["hp"] = 1` por lógica de nível:
```python
        nivel = self._ressur_nivel(p)
        custo_fome = custo_sede = {1: 10, 2: 15, 3: 20}[nivel]
        ...
        alvo["hp"] = {1: 1, 2: max(1, alvo["max_hp"] // 2), 3: alvo["max_hp"]}[nivel]
```
(Ajustar a mensagem `gm_say` para refletir o HP concedido. `custo` já é validado
antes de aplicar, como hoje.)

---

## 5. Cliente (`game.js` — renderer dedicado do Lewis)

O Lewis tem UI própria (`_clericSkillBtn` e a família de painéis de cura/
purificação/ressurreição). Ajustes (lendo `GS.guildOwnedOf(me.id).especializacoes`):
- **Cura / Cura em Massa:** o seletor de número de dados fica limitado ao teto
  possuído (1 base / 2 / 3); a Massa também mostra o raio atual (2/4/6).
- **Purificação:** só oferece os tipos destravados (venenos base; +doenças; +maldições/
  petrificação); tipos bloqueados aparecem desabilitados com dica.
- **Ressurreição:** mostra o efeito e o custo do nível atual (1 HP/10 · metade/15 ·
  cheio/20).
- Descrições refletem o nível possuído.

> **Robustez na masmorra:** `guildOwnedOf` já cai para o player do `game_state`
> quando `cityState=null` (Fase 0). O servidor é autoritativo de qualquer forma.

---

## 6. Testes (`tools/test_clerigo_espec.py`)

Harness do projeto (`main()` + `check()`; sem pytest). Helper `cleric(**owned)`
análogo ao `warrior(...)` da Fase 1a. Cobrir:
1. **Cura teto:** `_cura_teto` = 1/2/3 conforme posse; `handle_cura` com `num_dados=3`
   sem `cura_3` cura no máximo 2 (ou 1) dados — validar via mock de `random.randint`
   para dado fixo e conferir o total curado.
2. **Massa:** `_massa_nivel` = 1/2/3; raio resultante 2/4/6; teto de dados idem.
3. **Purificação:** `_purif_tipos` = `{veneno}` base; `+doenca` com II; `+maldicao,
   petrificacao` com III. `handle_purificacao` recusa tipo não destravado.
4. **Ressurreição:** `_ressur_nivel` = 1/2/3; HP concedido 1 / `max_hp//2` / `max_hp`;
   custo 10/15/20. (Montar um alvo morto adjacente e conferir `alvo["hp"]` + débito.)
5. **Compra:** `clerigo_cura_3` recusado sem `clerigo_cura_2` (idem cada linha).

> Mockar `random.randint`/`roll_dice` para tornar a cura determinística.

---

## 7. Fronteiras (NÃO fazer nesta sub-fase)

- Outras classes.
- Tabela de custo extra de progressão baixo/médio/alto (a escala atual já cobre).
- Reembolso.
- Técnicas (4º slot) — é Fase 2.

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Nerf real (cura cai de 3d8 p/ 1d8; raio da Massa 5→2) surpreende quem já jogava | Intencional e documentado no CLAUDE.md; níveis restauram/superam. |
| Cliente e servidor divergirem no teto/tipo | Servidor autoritativo (limita dados, recusa tipo/nível); cliente só melhora UX. Testes 1-4 fixam o servidor. |
| `max_hp//2` = 0 em alvo de 1 PV máx | `max(1, max_hp//2)` garante ≥1. |
| Regressão nos 4 handlers | Sem novo teste de cleric existente; criar `test_clerigo_espec.py`; rodar suíte geral (guilda/guerreiro/devorador). |
