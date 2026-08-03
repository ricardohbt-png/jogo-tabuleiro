# Maldições Fase B — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tirar do inerte as 4 maldições progressivas restantes (Fome Eterna, Sede Infinita, Tocado pela Morte, Corrupção Crescente) e fazer o estágio significar algo em todas elas, não só na Licantropia.

**Architecture:** Cada progressiva declara suas rampas como tuplas de 5 no catálogo (`estagios`), e um helper único `_maldicao_estagio_cfg(p, mid)` resolve o estágio atual — mesma filosofia do `mods` da Fase A. A Licantropia, escrita à mão pelo autor, migra para essa camada sob teste de caracterização. Tocado pela Morte exige extrair um funil de cura (`_curar_hp`), que hoje não existe: são 10 sites repetindo o mesmo cálculo.

**Tech Stack:** Python 3 + `websockets` (server.py, sem framework). Testes são scripts que rodam da raiz e imprimem ✅/❌, saindo com código 1 se algo falhar.

**Spec:** `docs/superpowers/specs/2026-08-03-maldicoes-fase-b-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta entrega |
|---|---|
| `server.py` | campo `estagios`, `_maldicao_estagio_cfg`, dreno de turno, funil `_curar_hp`, geração da Corrupção |
| `tools/test_maldicoes.py` | cresce de 67 para ~100 checks |

**Convenções:**
- Testes rodam da raiz: `python tools/test_maldicoes.py`.
- Commits em português: `feat(maldicoes)` / `refactor(maldicoes)`.
- **O usuário edita `server.py` em paralelo.** Rodar `git status` e `git diff server.py` antes de cada `git add`; conferir que todo hunk é seu. Nunca `git add -A`, `git add .` ou `git add -u`.
- `tools/test_maldicoes.py` já tem helpers `sala()`, `check()`, `anel()`, `equipar()`. Ler o arquivo antes; reusar `sala()`, não inventar fixture nova.

---

## Task 1: Camada de estágio e migração da Licantropia

**Files:**
- Modify: `server.py` — `MALDICOES`, `_licantropia_config` (~14488)
- Test: `tools/test_maldicoes.py`

Esta é a **única task perigosa**: troca código recém-escrito pelo autor e validado em jogo. Os testes são de caracterização — passam ANTES e DEPOIS.

- [ ] **Step 1: Escrever a caracterização dos 35 números**

Adicionar em `tools/test_maldicoes.py`, antes de `def main():`

```python
# Os 35 parâmetros da Licantropia (7 chaves × 5 estágios), extraídos do código
# ANTES da migração. Se um só mudar depois, a migração quebrou.
LICANTROPIA_ESPERADO = {
    "chance":          (1, 2, 3, 4, 4),
    "for":             (2, 3, 4, 4, 4),
    "con":             (2, 3, 3, 3, 3),
    "des":             (1, 1, 2, 2, 2),
    "reducao":         (1, 2, 2, 3, 3),
    "regen":           (1, 2, 2, 3, 3),
    "intervalo_regen": (3, 3, 2, 2, 2),
}

def test_licantropia_caracterizacao():
    print("\n[18] Licantropia — os 35 números não mudam")
    r, p = sala()
    p["maldicoes"] = [{"id": "licantropia", "aventuras": 0}]
    for estagio in range(1, 6):
        p["maldicoes"][0]["aventuras"] = (estagio - 1) * 2
        cfg = r._licantropia_config(p)
        check(f"estágio {estagio} reportado", cfg["estagio"] == estagio)
        for chave, rampa in LICANTROPIA_ESPERADO.items():
            check(f"E{estagio} {chave} = {rampa[estagio-1]}", cfg[chave] == rampa[estagio - 1])
    r2, p2 = sala()
    check("sem a maldição devolve None", r2._licantropia_config(p2) is None)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que PASSA**

```bash
python tools/test_maldicoes.py
```

Esperado: **0 falharam**. Isto é caracterização, não TDD vermelho: o
comportamento já existe e o teste o fixa. Se algum número não bater, **pare e
reporte** — significa que o código divergiu do que o plano leu.

- [ ] **Step 3: Declarar as rampas no catálogo**

Em `MALDICOES`, acrescentar `estagios` à Licantropia:

```python
    "licantropia": {"nome":"Licantropia","categoria":"grave","progressiva":True,
                    "desc":"transformação bestial",
                    "estagios": {"chance": (1, 2, 3, 4, 4), "for": (2, 3, 4, 4, 4),
                                 "con": (2, 3, 3, 3, 3), "des": (1, 1, 2, 2, 2),
                                 "reducao": (1, 2, 2, 3, 3), "regen": (1, 2, 2, 3, 3),
                                 "intervalo_regen": (3, 3, 2, 2, 2)}},
```

Logo abaixo de `MALDICAO_MOD_CHAVES`, documentar:

```python
# `estagios`: rampas das maldições PROGRESSIVAS, uma tupla de 5 por parâmetro
# (índice = estágio-1). Lido só por _maldicao_estagio_cfg. Acrescentar uma
# progressiva nova é declarar aqui e ler o parâmetro onde ele importa.
```

- [ ] **Step 4: Criar o helper genérico**

Em `GameRoom`, logo depois de `_maldicao_estagio`:

```python
    def _maldicao_estagio_cfg(self, p, maldicao_id):
        """Parâmetros da progressiva no estágio atual do herói, ou None se ele
        não a carrega. Único ponto que sabe ler o campo `estagios`."""
        entrada = next((m for m in self._maldicoes(p) if m["id"] == maldicao_id), None)
        if not entrada:
            return None
        estagio = self._maldicao_estagio(entrada)
        rampas = MALDICOES[maldicao_id].get("estagios", {})
        cfg = {chave: valores[estagio - 1] for chave, valores in rampas.items()}
        cfg["estagio"] = estagio
        return cfg
```

- [ ] **Step 5: `_licantropia_config` vira casca fina**

Substituir o corpo inteiro por:

```python
    def _licantropia_config(self, p):
        """Parâmetros efetivos da Licantropia para o estágio atual do herói.
        As rampas moram em MALDICOES['licantropia']['estagios']."""
        return self._maldicao_estagio_cfg(p, "licantropia")
```

Não mexer em nenhum consumidor — todos continuam chamando `_licantropia_config`
e recebendo o mesmo dicionário.

- [ ] **Step 6: Rodar e confirmar que continua passando**

```bash
python tools/test_maldicoes.py
python tools/test_modo_mestre.py
python tools/test_masmorra_sequenciada.py
```

Esperado: os três com **0 falharam**. Se um dos 35 números mudou, a migração
está errada — **não** "ajustar o teste".

- [ ] **Step 7: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "refactor(maldicoes): camada declarativa de estagio"
```

---

## Task 2: Fome Eterna e Sede Infinita

**Files:**
- Modify: `server.py` — `MALDICOES`, o gancho de início de turno (~9459)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_dreno_fome_sede():
    print("\n[19] Fome Eterna e Sede Infinita")
    r, p = sala()
    p["fome"] = p["sede"] = 50
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("sem maldição, não drena", p["fome"] == 50 and p["sede"] == 50)

    asyncio.run(r._aplicar_maldicao(p, "fome_eterna"))
    p["fome"] = p["sede"] = 50
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("estágio I drena 1 de fome", p["fome"] == 49)
    check("Fome Eterna não mexe na sede", p["sede"] == 50)

    # estágio V: aventuras >= 8
    p["maldicoes"][0]["aventuras"] = 8
    p["fome"] = 50
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("estágio V drena 3 de fome", p["fome"] == 47)

    r2, p2 = sala()
    asyncio.run(r2._aplicar_maldicao(p2, "sede_infinita"))
    p2["fome"] = p2["sede"] = 50
    asyncio.run(r2._processar_dreno_maldicoes(p2))
    check("Sede Infinita drena a sede", p2["sede"] == 49)
    check("Sede Infinita não mexe na fome", p2["fome"] == 50)

    r3, p3 = sala()
    asyncio.run(r3._aplicar_maldicao(p3, "fome_eterna"))
    p3["fome"] = 0
    asyncio.run(r3._processar_dreno_maldicoes(p3))
    check("piso de 0 respeitado", p3["fome"] == 0)

    r4, p4 = sala()
    asyncio.run(r4._aplicar_maldicao(p4, "fome_eterna"))
    p4["alive"] = False; p4["fome"] = 50
    asyncio.run(r4._processar_dreno_maldicoes(p4))
    check("herói morto não drena", p4["fome"] == 50)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_processar_dreno_maldicoes'`.

- [ ] **Step 3: Declarar as rampas**

```python
    "fome_eterna": {"nome":"Fome Eterna","categoria":"grave","progressiva":True,
                    "desc":"consumo sobrenatural de fome",
                    "estagios": {"dreno_fome": (1, 2, 2, 3, 3)}},
    "sede_infinita": {"nome":"Sede Infinita","categoria":"grave","progressiva":True,
                      "desc":"consumo sobrenatural de sede",
                      "estagios": {"dreno_sede": (1, 2, 2, 3, 3)}},
```

- [ ] **Step 4: Criar o processador de turno**

Em `GameRoom`, junto de `_processar_regeneracao_licantropia`:

```python
    async def _processar_dreno_maldicoes(self, p):
        """Fome Eterna e Sede Infinita drenam por RODADA, só por existir — é o
        que as distingue do Corpo Exausto, que sobretaxa ações. Roda no início
        do turno do herói, ao lado da regeneração da Licantropia."""
        if not p.get("alive"):
            return
        for mid, recurso, chave in (("fome_eterna", "fome", "dreno_fome"),
                                     ("sede_infinita", "sede", "dreno_sede")):
            cfg = self._maldicao_estagio_cfg(p, mid)
            if not cfg:
                continue
            perda = min(cfg[chave], p.get(recurso, 0))
            if perda <= 0:
                continue
            p[recurso] = max(0, p.get(recurso, 0) - perda)
            await self.gm_say(f"☠️ **{MALDICOES[mid]['nome']}** consome "
                              f"**{perda}** de {recurso} de **{p['name']}**.")
```

- [ ] **Step 5: Ligar no início do turno**

Na linha onde a Licantropia já regenera (`await self._processar_regeneracao_licantropia(p)`, ~9459), acrescentar logo abaixo:

```python
        await self._processar_dreno_maldicoes(p)
```

- [ ] **Step 6: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
python tools/test_masmorra_sequenciada.py
```

Esperado: os dois com **0 falharam**.

- [ ] **Step 7: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Fome Eterna e Sede Infinita"
```

---

## Task 3: Funil de cura `_curar_hp`

**Files:**
- Modify: `server.py` — 10 sites de cura
- Test: `tools/test_maldicoes.py`

Refatoração pura: **nenhuma mudança de comportamento**. A maldição entra na Task 4.

**Os 10 sites** (as linhas mudam conforme você edita — localize pela função):

| Função | O que cura |
|---|---|
| `_apply_skill` | habilidade legada |
| `handle_cura` | Cura do clérigo |
| `handle_cura_area` | Cura em Massa |
| `handle_imposicao_maos` | Imposição das Mãos |
| `_processar_manutencao_richard` | Regeneração Divina (próprio) |
| `_processar_manutencao_richard` | Regeneração Divina (aliados no raio) |
| `_processar_regeneracao_licantropia` | regeneração da Licantropia |
| `_processar_buffs_magicos_turno` | regeneração mágica |
| `handle_use_item` | poção de cura |
| `_processar_regeneracao_pocao_turno` | poção de regeneração (tick) |

**NÃO migrar** (não são cura, são ajuste de teto — e os dois primeiros já têm a
trava do Último Esforço): `_apply_single_effect` (top-up de `maxhp` ao equipar),
`_apply_attribute_delta` (top-up por CON) e o ganho de nível. **Nem a
Ressurreição**, que define o HP para um valor fixo em vez de somar cura.

- [ ] **Step 1: Escrever a caracterização**

```python
def test_curar_hp_funil():
    print("\n[20] Funil de cura — comportamento inalterado")
    r, p = sala()
    p["max_hp"] = 20; p["hp"] = 5
    check("cura normal soma", r._curar_hp(p, 7) == 7 and p["hp"] == 12)
    p["hp"] = 18
    check("respeita o teto", r._curar_hp(p, 10) == 2 and p["hp"] == 20)
    p["hp"] = 20
    check("no teto cura 0", r._curar_hp(p, 5) == 0 and p["hp"] == 20)
    p["hp"] = 10
    check("cura 0 não muda nada", r._curar_hp(p, 0) == 0 and p["hp"] == 10)
    check("cura negativa não tira HP", r._curar_hp(p, -5) == 0 and p["hp"] == 10)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_curar_hp'`.

- [ ] **Step 3: Criar o funil**

Em `GameRoom`, junto dos helpers de maldição:

```python
    def _curar_hp(self, alvo, cura, fonte=""):
        """Cura HP respeitando o teto. Ponto ÚNICO de cura de herói — é aqui
        que Tocado pela Morte reduz a recuperação (Task 4) e onde qualquer regra
        futura sobre cura vai morar. Devolve o quanto realmente curou.

        NÃO passam por aqui, de propósito: top-up de max_hp ao equipar item,
        top-up por CON, ganho de nível e Ressurreição — nenhum é cura."""
        cura = max(0, int(cura))
        if cura <= 0:
            return 0
        antes = alvo.get("hp", 0)
        alvo["hp"] = min(alvo.get("max_hp", antes), antes + cura)
        return alvo["hp"] - antes
```

- [ ] **Step 4: Migrar os 10 sites**

Cada um vira uma chamada ao funil. Exemplo de `handle_cura`:

```python
        alvo["hp"] = min(alvo["max_hp"], alvo["hp"] + cura)
```

vira

```python
        self._curar_hp(alvo, cura, "Cura")
```

Onde a narração usa o valor curado, capturar o retorno:

```python
        curado = self._curar_hp(alvo, cura, "Cura")
```

> **Cuidado nos dois sites de `_processar_manutencao_richard`**: um cura o
> próprio Richard e o outro varre aliados no raio, e o segundo monta a lista
> `curados` para a narração. Preservar a lista — só trocar o cálculo.

> **`_processar_regeneracao_licantropia`** já faz
> `cura = min(cfg["regen"], max(0, max_hp - hp))` antes de somar. Com o funil, o
> clamp vira redundante mas **inofensivo**; deixe como está e apenas troque o
> `p["hp"] += cura` por `self._curar_hp(p, cura, "Licantropia")`. Mudar o cálculo
> anterior está fora do escopo desta task.

- [ ] **Step 5: Rodar a bateria**

```bash
python tools/test_maldicoes.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_guilda.py
python tools/test_editor_itens.py
python tools/test_modo_mestre.py
```

Esperado: todas com **0 falharam**. Estas cobrem Cura, Cura em Massa, Imposição
das Mãos, Regeneração Divina e poções — se a migração mudou algum número, é aqui
que aparece.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "refactor(maldicoes): funil unico de cura de HP"
```

---

## Task 4: Tocado pela Morte

**Files:**
- Modify: `server.py` — `MALDICOES`, `_curar_hp`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_tocado_morte():
    print("\n[21] Tocado pela Morte")
    r, p = sala()
    p["max_hp"] = 100; p["hp"] = 10
    check("sem maldição, cura cheia", r._curar_hp(p, 10) == 10)

    asyncio.run(r._aplicar_maldicao(p, "tocado_morte"))
    p["hp"] = 10
    check("estágio I corta 20%", r._curar_hp(p, 10) == 8)
    p["maldicoes"][0]["aventuras"] = 8   # estágio V
    p["hp"] = 10
    check("estágio V corta 60%", r._curar_hp(p, 10) == 4)
    # Arredonda para baixo: estágio I corta 20% de 7 → (7*20)//100 = 1, cura 6.
    p["maldicoes"][0]["aventuras"] = 0
    p["hp"] = 10
    check("arredonda para baixo", r._curar_hp(p, 7) == 6)
    # Piso de 1: cura de 1 no estágio V não pode virar 0
    p["maldicoes"][0]["aventuras"] = 8
    p["hp"] = 10
    check("piso de 1 com cura de 1", r._curar_hp(p, 1) == 1)
    p["hp"] = 10
    check("cura 0 continua 0", r._curar_hp(p, 0) == 0)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: falha em "estágio I corta 20%".

- [ ] **Step 3: Declarar a rampa**

```python
    "tocado_morte": {"nome":"Tocado pela Morte","categoria":"grave","progressiva":True,
                     "desc":"recuperação cada vez menos eficaz",
                     "estagios": {"reducao_cura_pct": (20, 30, 40, 50, 60)}},
```

- [ ] **Step 4: Aplicar a redução no funil**

Em `_curar_hp`, entre a normalização e a soma:

```python
        cura = max(0, int(cura))
        if cura <= 0:
            return 0
        cfg = self._maldicao_estagio_cfg(alvo, "tocado_morte") if self._eh_jogador(alvo) else None
        if cfg:
            # Piso de 1: sem ele, uma poção de 1 HP no estágio V curaria zero e
            # o jogador acharia que está bugado.
            cura = max(1, cura - (cura * cfg["reducao_cura_pct"]) // 100)
        antes = alvo.get("hp", 0)
```

> A guarda `_eh_jogador` é obrigatória: `_maldicao_estagio_cfg` chama
> `_maldicoes`, que MUTA o dict do alvo. Sem ela, curar um monstro escreveria
> campos de maldição nele.

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
```

Esperado: todas com **0 falharam**.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Tocado pela Morte"
```

---

## Task 5: Corrupção Crescente

**Files:**
- Modify: `server.py` — `MALDICOES`, `_progredir_maldicoes_missao` (~14689), e os dois sorteios duplicados (~17552 e ~20554)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_corrupcao_crescente():
    print("\n[22] Corrupção Crescente")
    # O sorteio compartilhado nunca devolve progressiva. 40 tentativas por
    # categoria: com 5 progressivas no catálogo, um filtro quebrado apareceria.
    r, p = sala()
    for cat in ("leve", "media", "grave"):
        sorteadas = [r._sortear_maldicao(cat) for _ in range(40)]
        check(f"sorteio '{cat}' nunca devolve progressiva",
              not any(S.MALDICOES[m].get("progressiva") for m in sorteadas))
        check(f"sorteio '{cat}' respeita a categoria",
              all(S.MALDICOES[m]["categoria"] == cat for m in sorteadas))

    # Avançar para II gera doença leve.
    r2, p2 = sala()
    asyncio.run(r2._aplicar_maldicao(p2, "corrupcao_crescente"))
    p2["maldicoes"][0]["aventuras"] = 1   # próxima missão leva a 2 → estágio II
    asyncio.run(r2._progredir_maldicoes_missao())
    check("→ II adoece", p2.get("doente") is True)
    check("→ II é doença leve", (p2.get("doenca") or {}).get("sintomas") == ["leve"])

    # Avançar para III agrava para pesada.
    p2["maldicoes"][0]["aventuras"] = 3
    asyncio.run(r2._progredir_maldicoes_missao())
    check("→ III agrava a doença",
          (p2.get("doenca") or {}).get("sintomas") == ["leve", "medio"])

    # Avançar para IV gera maldição média.
    r3, p3 = sala()
    asyncio.run(r3._aplicar_maldicao(p3, "corrupcao_crescente"))
    p3["maldicoes"][0]["aventuras"] = 5
    asyncio.run(r3._progredir_maldicoes_missao())
    novas = [m["id"] for m in r3._maldicoes(p3) if m["id"] != "corrupcao_crescente"]
    check("→ IV gera uma maldição", len(novas) == 1)
    check("→ IV gera uma MÉDIA", novas and S.MALDICOES[novas[0]]["categoria"] == "media")

    # Teto de 3: com a cota cheia, a geração é recusada sem quebrar.
    r4, p4 = sala()
    asyncio.run(r4._aplicar_maldicao(p4, "corrupcao_crescente"))
    asyncio.run(r4._aplicar_maldicao(p4, "maos_tremulas"))
    asyncio.run(r4._aplicar_maldicao(p4, "passos_pesados"))
    p4["maldicoes"][0]["aventuras"] = 5
    asyncio.run(r4._progredir_maldicoes_missao())
    check("com 3 maldições, não estoura o teto", len(r4._maldicoes(p4)) == 3)

    # Sem avanço de estágio, não gera nada.
    r5, p5 = sala()
    asyncio.run(r5._aplicar_maldicao(p5, "corrupcao_crescente"))
    p5["maldicoes"][0]["aventuras"] = 0   # 0 → 1 não muda de estágio
    asyncio.run(r5._progredir_maldicoes_missao())
    check("sem avanço de estágio, nada é gerado",
          not p5.get("doente") and len(r5._maldicoes(p5)) == 1)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_sortear_maldicao'`.

- [ ] **Step 3: Extrair o sorteio compartilhado**

Os dois sites que hoje duplicam a mesma compreensão de lista (`~17552` na
armadilha de maldição e `~20554` no Amaldiçoar de monstro) passam a chamar um
helper. Em `GameRoom`:

```python
    def _sortear_maldicao(self, categoria, padrao="maos_tremulas"):
        """Sorteia uma maldição da categoria, NUNCA progressiva — progressivas
        só entram por fonte explícita. Usado pela armadilha, pelo Amaldiçoar e
        pela Corrupção Crescente."""
        categoria = _maldicao_categoria(categoria)
        opcoes = [mid for mid, dados in MALDICOES.items()
                  if dados["categoria"] == categoria and not dados.get("progressiva")]
        return random.choice(opcoes) if opcoes else padrao
```

Nos dois sites, substituir o bloco

```python
                    categoria = _maldicao_categoria(arm.get("curse_category", "leve"))
                    opcoes = [mid for mid, dados in MALDICOES.items()
                              if dados["categoria"] == categoria and not dados.get("progressiva")]
                    mid = random.choice(opcoes) if opcoes else "maos_tremulas"
```

por

```python
                    mid = self._sortear_maldicao(arm.get("curse_category", "leve"))
```

(no site do Amaldiçoar, a variável é `maldicao_id` e a origem é
`ability.get("curse_category", "leve")` — adapte os nomes, a chamada é a mesma).

- [ ] **Step 4: Declarar a maldição e gerar no avanço**

```python
    "corrupcao_crescente": {"nome":"Corrupção Crescente","categoria":"grave","progressiva":True,
                            "desc":"gera doenças e maldições"},
```

Em `_progredir_maldicoes_missao`, dentro do `if depois > antes:`, logo após o
`gm_say` do avanço:

```python
                if depois > antes:
                    await self.gm_say(f"☠️ **{mal['nome']}** de **{p['name']}** avança ao estágio {depois}.")
                    if entrada["id"] == "corrupcao_crescente":
                        await self._corrupcao_gerar(p, depois)
```

E o gerador, junto dos outros helpers de maldição:

```python
    # O que a Corrupção Crescente cria em cada avanço de estágio. Só há quatro
    # avanços na vida do personagem (II a V), então a geração é GARANTIDA — uma
    # rolagem por cima poderia fazer a maldição nunca gerar nada.
    # Atenção: DOENCA_SEVERIDADE aceita leve/pesada/grave e cai em "leve" em
    # silêncio se a chave estiver errada — não existe "media".
    _CORRUPCAO_POR_ESTAGIO = {2: ("doenca", "leve"), 3: ("doenca", "pesada"),
                              4: ("maldicao", "media"), 5: ("maldicao", "grave")}

    async def _corrupcao_gerar(self, p, estagio):
        """Corrupção Crescente cria uma doença ou uma maldição ao subir de
        estágio. Nunca gera outra progressiva (o sorteio já as exclui), então
        não há risco de laço."""
        receita = self._CORRUPCAO_POR_ESTAGIO.get(estagio)
        if not receita:
            return
        tipo, valor = receita
        if tipo == "doenca":
            await self.gm_say(f"☠️ A **Corrupção Crescente** de **{p['name']}** apodrece a carne.")
            await self._aplicar_doenca(p, valor)
        else:
            await self._aplicar_maldicao(p, self._sortear_maldicao(valor),
                                          "a Corrupção Crescente", origem="monstro")
```

> O teto de 3 maldições por herói já é aplicado por `_aplicar_maldicao`, que
> narra "resistiu: já carrega o máximo de 3" e devolve False. Não replicar a
> checagem aqui.

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
python tools/test_modo_mestre.py
python tools/test_masmorra_sequenciada.py
```

Esperado: todas com **0 falharam**.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Corrupcao Crescente"
```

---

## Task 6: Regressão e cobertura

**Files:** nenhum (verificação)

- [ ] **Step 1: Bateria completa**

```bash
python tools/test_maldicoes.py
python tools/test_editor_itens.py
python tools/test_devorador.py
python tools/test_guilda.py
python tools/test_modo_mestre.py
python tools/test_savegames.py
python tools/test_masmorra_sequenciada.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_bardo_espec.py
python tools/test_ladino_espec.py
python tools/test_cenas_conversa.py
```

Esperado: todas com **0 falharam**.

- [ ] **Step 2: Conferir a cobertura do catálogo**

```bash
python -c "
import io, sys; sys.path.insert(0,'.')
import server as S
src = io.open('server.py', encoding='utf-8', errors='ignore').read()
inertes = [m for m, d in S.MALDICOES.items()
           if not d.get('mods') and not d.get('estagios') and src.count(f'\"{m}\"') <= 1]
print(f'{25-len(inertes)}/25 com efeito | inertes: {inertes}')
"
```

Esperado: **18/25**, e os 7 inertes devem ser exatamente as não-progressivas da
Fase C: `fraqueza_arcana`, `carne_fragil`, `sangramento_profano`,
`dor_constante`, `alma_quebrada`, `maldicao_ferrugem`, `eco_morte`.

- [ ] **Step 3: Prova ponta a ponta**

Rodar um script que aplica as progressivas num herói de verdade e confirma que
os efeitos compõem sem quebrar — o mesmo formato usado ao fechar a Fase A:

```bash
python - <<'EOF'
import asyncio, sys
sys.path.insert(0, '.')
import server as S
r = S.GameRoom("FASEB")
async def noop(*a, **k): pass
r.gm_say=noop; r.broadcast=noop; r.push_state=noop
r._checkpoint_savegame=lambda *a,**k: None
r.phase="playing"
p = S.make_player("p1","Victor","warrior",0); p["pos"]=[5,5]; r.players["p1"]=p
p["max_hp"]=100; p["hp"]=10; p["fome"]=p["sede"]=50
asyncio.run(r._aplicar_maldicao(p, "tocado_morte"))
asyncio.run(r._aplicar_maldicao(p, "fome_eterna"))
print("cura de 10 com Tocado I:", r._curar_hp(p, 10), "(esperado 8)")
asyncio.run(r._processar_dreno_maldicoes(p))
print("fome apos o dreno:", p["fome"], "(esperado 49)")
EOF
```

- [ ] **Step 4: Commit final (se sobrou ajuste)**

```bash
git status
git add server.py tools/test_maldicoes.py
git commit -m "test(maldicoes): ajustes da verificacao da Fase B"
```

Se nada mudou, pular.

---

## Notas para quem implementar

- **Duas tasks são migrações** (1 e 3) e são as únicas que podem quebrar o que
  já funciona. Se um teste de caracterização mudar de resultado, o erro está na
  migração — nunca no teste.
- **`_maldicoes()` MUTA o dict do alvo.** Todo helper que a chama
  (`_maldicao_estagio_cfg`, `_tem_maldicao`) só pode receber jogador. A guarda
  `_eh_jogador` em `_curar_hp` é obrigatória, não decorativa.
- **`DOENCA_SEVERIDADE` não tem `"media"`** — as chaves são `leve`, `pesada` e
  `grave`, e `_aplicar_doenca` cai em `leve` em silêncio se a chave estiver
  errada. Por isso o teste afirma os **sintomas**, não só o flag `doente`.
- **O usuário edita `server.py` em paralelo.** Ver as convenções no topo.
