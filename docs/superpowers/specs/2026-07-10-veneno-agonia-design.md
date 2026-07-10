# Sub-projeto E — Veneno Agonia Sufocante (Lendário)

**Data:** 2026-07-10
**Status:** aprovado (brainstorming)

## Contexto

Quinto e último sub-projeto da família de itens de mercado (ver memória
`arremessaveis-roadmap`). **A–D** (arremessáveis de fogo/área/ácido/táticos) já
estão mergeados. Este é o único que **não** é arremessável: a **Agonia Sufocante**
é um veneno **untado na arma** (`coat_poison`), como os 5 venenos já existentes.

## Infraestrutura existente reaproveitada

- **Catálogo `VENENOS`** + `_aplicar_veneno` + `_processar_venenos_turno`: os 5
  venenos atuais reduzem atributo / aplicam penalidade / petrificam / cegam, com
  save **só na aplicação** (`anula`). A entrega (untar na arma → golpe envenena) já
  é genérica: `SHOP_MERCHANT` (`effect:"coat_poison"`), `handle_use_item` →
  `weapon_poison`/`weapon_poison_hits`, e `_aplicar_veneno` no acerto corpo a corpo.
- **`_dano_em_alvo`**: aplica dano a jogador/monstro/animado/prisioneiro tratando
  morte (usado para o dano por rodada).
- **`_testar_save`**: resolve Fortitude para jogador e monstro.

## O que é novo (não existe hoje)

1. **`operacao: "dano"`** — dano-por-rodada (nenhum veneno atual causa dano direto).
2. **Save por rodada que neutraliza** — os atuais salvam só na aplicação; a Agonia
   testa Fortitude no início de cada rodada e o sucesso encerra o veneno na hora.

Ambos ficam **genéricos** (reusáveis por venenos futuros), não hard-coded para a
Agonia.

## Decisões de design

1. **Untada na arma** (`coat_poison`), como os outros 5 venenos — 1 golpe certeiro
   envenena (arma à distância herda as 3 cargas via a regra atual, sem mudança).
2. **Sem save na aplicação** — o save é só o loop por rodada (fiel à spec: "no
   início de cada rodada"). O veneno de dano pula a lógica de `anula`.
3. Dano por rodada via `_dano_em_alvo`, elemento `"veneno"`; funciona em jogador
   **e** monstro. Mortos-vivos/constructos seguem **imunes** a veneno (checagem já
   existente em `_aplicar_veneno`).
4. **Preço 40** (Lendário).

## Componentes

### 1. Catálogo `VENENOS` + loja (`server.py`)

Nova entrada em `VENENOS`:

```python
"veneno_agonia_sufocante": {
    "nome": "Agonia Sufocante", "icone": "💀",
    "operacao": "dano", "dano": "1d4", "duracao": "1d4",
    "save": "fortitude", "dificuldade": 14,
    "save_neutraliza_por_rodada": True, "anula": False,
},
```

Nova entrada em `SHOP_MERCHANT` (junto dos outros venenos):

```python
{"id": "veneno_agonia_sufocante", "name": "Agonia Sufocante", "emoji": "💀", "price": 40, "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_agonia_sufocante"},
```

### 2. `_aplicar_veneno` — ramo `operacao == "dano"` (`server.py`)

- Manter a checagem de imunidade (morto-vivo/constructo) já existente.
- Para `operacao == "dano"`: **pular** o save de aplicação/`anula` (o veneno de dano
  não é negado ao aplicar). Registrar em `alvo["efeitos_veneno"]` um efeito:
  ```python
  {"nome": nome, "operacao": "dano", "dano": veneno["dano"],
   "duracao": self._rolar_dado(veneno.get("duracao", "1d4")),
   "save": veneno.get("save", "fortitude"), "dificuldade": veneno.get("dificuldade", 10),
   "save_neutraliza_por_rodada": bool(veneno.get("save_neutraliza_por_rodada"))}
  ```
  (A duplicação de magnitude por "sensível a venenos" já existente pode continuar
  valendo para a duração, mantendo o padrão dos outros venenos.)

### 3. `_processar_venenos_turno` — tick de dano + save-por-rodada (`server.py`)

No loop sobre `efeitos_veneno`, ANTES do decremento genérico de duração, tratar o
efeito de dano:

```python
if efeito.get("operacao") == "dano":
    # Save por rodada que neutraliza imediatamente (Agonia Sufocante).
    if efeito.get("save_neutraliza_por_rodada"):
        ok, d20, sb, stot = self._testar_save(
            alvo, efeito.get("save", "fortitude"), efeito.get("dificuldade", 10))
        if ok:
            await self.gm_say(f"☑️ **{alvo_nome}** neutraliza **{efeito.get('nome','veneno')}**!")
            continue   # remove o efeito (não entra em `restantes`)
    dano = self._rolar_dado(efeito.get("dano", "1d4"))
    await self.gm_say(f"💀 **{efeito.get('nome','Veneno')}** corrói **{alvo_nome}**: {dano} de dano!")
    await self._dano_em_alvo(alvo, dano, "veneno", None)
    efeito["duracao"] -= 1
    if efeito["duracao"] > 0 and (alvo.get("alive") or alvo.get("hp", 0) > 0):
        restantes.append(efeito)
    continue
```

> O efeito de dano tem seu próprio ramo (save → neutraliza; senão dano + decremento
> de duração), separado do decremento/reversão genérico dos efeitos de atributo. A
> `duracao` limita a no máximo 1d4 rodadas mesmo falhando sempre.

### 4. Cliente (`src/gameState.js`)

- Uma entrada em `CATALOGO_ITENS` no formato dos outros venenos (`effect: 'coat_poison'`,
  `veneno_id`, `permitidoPara:['todos']`, tooltip do efeito). **Sem UI nova.**

### 5. Imagem

- `assets/itens/veneno_agonia_sufocante.png` (fallback emoji 💀).

### 6. Item (loja/mercado)

| Item | id | Emoji | Entrega | Efeito | Preço |
|---|---|---|---|---|---|
| Agonia Sufocante | `veneno_agonia_sufocante` | 💀 | untar na arma | 1d4 dano/rodada por até 1d4 rodadas; Fortitude CD 14 por rodada neutraliza | 40 🪙 |

### 7. Testes (`tools/test_veneno_agonia.py`)

- **Aplicação:** `_aplicar_veneno` registra o efeito de dano em `efeitos_veneno`
  (sem save de aplicação); imunidade morto-vivo/constructo continua (não registra).
- **Tick — falha:** com `_testar_save` forçado a falhar, `_processar_venenos_turno`
  aplica 1d4 de dano e mantém o efeito (duração > 0).
- **Tick — sucesso:** com `_testar_save` forçado a passar, o efeito é removido sem
  dano.
- **Duração:** falhando sempre, o efeito expira em no máximo `duracao` (1d4) rodadas.
- **Regressão:** os venenos existentes seguem funcionando (o novo ramo `operacao ==
  "dano"` não pode afetar `reduzir`/`penalidade`/`petrificar`/`cegar`).

## Fora de escopo (deste sub-projeto)

- Tornar a Agonia arremessável (a spec a define como veneno de arma).
- Indicador visual do status de veneno-de-dano sobre o alvo (YAGNI).
- Novos venenos além da Agonia (o `operacao:"dano"` fica genérico para o futuro).
