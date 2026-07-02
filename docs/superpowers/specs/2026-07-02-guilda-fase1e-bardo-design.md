# Guilda dos Heróis — Fase 1e: Especializações do Bardo

**Data:** 2026-07-02
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 1e (Bardo). Fase 1 decomposta por classe. Feito: 1a (Guerreiro), 1b
(Clérigo), 1c (Paladino), 1d (Ladino). Próxima: Mago (1f).
**Depende de:** Fase 0 + padrão das Fases 1a-1d (`tem_espec`, entradas
`categoria:"especializacao"` no `GUILD_CATALOG`, `handle_guild_buy`, e o padrão
de **catálogo gerado** dos nós — igual às Fórmulas de Armadilha do Ladino).

---

## 1. Visão geral

Cobre o **Bardo** (Henrique, `class_id:"bard"`) em **3 linhas**: Canção Heroica,
Provocação e Lendas. A Lendas é uma mecânica **nova** (bônus permanente por
espécie de monstro), construída de forma **extensível** — um nó de compra por
tipo em `MONSTER_DEFS`, gerado dinamicamente (monstros futuros entram sozinhos).

### Estado atual confirmado no código
- **Canção Heroica** (`handle_ativar_cancao`, ~6444): o bardo escolhe atributos de
  `CANCAO_ATRIBUTOS` (`acerto/dano/ca/movimento/resistencia`); cada um dá **+1** aos
  aliados no raio 5 (`_aplicar_buffs_cancao`, ~6489: `buffs[attr["efeito"]] = 1`).
  Custo de manutenção = 1 fome/sede por atributo (`_calcular_custo_cancao`, ~146;
  upkeep `_cobrar_manutencao_cancao`, ~6506).
- **Provocação** (`handle_provocacao`, ~6539): ação bônus; marca no monstro
  `provocado=True`, `provocado_turnos=PROVOCACAO_TURNOS(4)`,
  `provocado_turno_efeito=True` (desvantagem no **próximo** ataque),
  `provocado_por=pid`. A desvantagem é consumida e **zerada** após um ataque do
  monstro (`provocado_turno_efeito=False` em ~11176, 12906). `provocado_por` marca
  o alvo forçado.
- **Combate:** `_rolar_ataque(atk_bonus, target_ac, vantagem=False, desvantagem=False)`
  (~9371) já suporta vantagem/desvantagem. `_player_effective_ac(p)` (~10642)
  calcula a CA efetiva do jogador ao ser atacado; a CA nos sites de ataque de
  monstro é montada inline (ex.: `effective_ac`, ~12744/12908).
- **Saves:** `_testar_save(alvo, tipo_save, dificuldade, extra_mod=0)` (~9485) — a
  **fonte** do save NÃO é passada hoje; há um `extra_mod` reutilizável.
- **Monstros:** `MONSTER_DEFS` (~810) é o registro único (cada um com `type`,
  `name`, `emoji`, `tier`). `{m["type"] for m in MONSTER_DEFS}` já é usado (~1979).

---

## 2. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Modelo | Base = comportamento atual; compras aprimoram. III exige II quando houver. |
| Canção Heroica II | 5 nós, um por atributo (`acerto/dano/ca/movimento/resistencia`); cada um sobe o bônus daquele atributo de +1 para **+2** na canção. Compra única por atributo (não empilha além de +2). |
| Canção Suprema | 1 nó: manutenção da canção custa **-1🍖 e -1💧** (mínimo 0 em cada). |
| Provocação II | Enquanto durar: desvantagem persiste a **duração toda** (não só o 1º ataque); Henrique **+2 CA** contra o alvo; Henrique ataca o alvo com **vantagem**. |
| Provocação III | Além do II: **todos os aliados** atacam o alvo com vantagem por **1 rodada** (a partir da provocação). |
| Lendas Avançadas | 1 nó por tipo de `MONSTER_DEFS` (gerado); cada compra dá **+1 de ataque E +1 nos saves** contra aquela espécie. Só Henrique se beneficia (base). |
| Lendas Supremas | 1 nó global: todos os bônus de Lenda possuídos passam a valer para **todos os aliados vivos** (enquanto Henrique estiver vivo). |
| Preços | Canção II 100/atributo; Canção Suprema 200; Provocação II 150 / III 200 (III exige II); Lendas por tier: T1 60, T2 90, T3 120, T4 200; Lendas Supremas 300. |
| Custo de uso | Ouro é o custo das compras; habilidades mantêm o custo atual (a Canção Suprema reduz a manutenção). |
| Arquitetura | Imperativa; catálogo literal (Canção/Provocação/Supremas) + gerado (Lendas por tipo); efeitos inline via `tem_espec` + helpers. |
| Autoridade | Servidor autoritativo. |

---

## 3. Catálogo (`GUILD_CATALOG`, server.py)

### 3.1 Nós literais (8)
```python
"bardo_cancao_acerto":      {..., "linha":"bardo_cancao","classe":"bard","requer":None,"preco":100,
    "nome":"Canção: Acerto +1","icon":"🎵","desc":"O bônus de Acerto da Canção Heroica sobe para +2." },
"bardo_cancao_dano":        {... "preco":100, "nome":"Canção: Dano +1", "desc":"O bônus de Dano da Canção sobe para +2." },
"bardo_cancao_ca":          {... "preco":100, "nome":"Canção: Armadura +1", "desc":"O bônus de Armadura da Canção sobe para +2." },
"bardo_cancao_movimento":   {... "preco":100, "nome":"Canção: Movimento +1", "desc":"O bônus de Movimento da Canção sobe para +2." },
"bardo_cancao_resistencia": {... "preco":100, "nome":"Canção: Resistência +1", "desc":"O bônus de Resistência da Canção sobe para +2." },
"bardo_cancao_suprema":     {... "preco":200, "nome":"Canção Heroica Suprema", "requer":None,
    "desc":"A manutenção da Canção Heroica custa -1🍖 e -1💧 (mínimo 0)." },
"bardo_provocacao_2":       {... "linha":"bardo_provocacao","preco":150,"requer":None,
    "nome":"Provocação II","icon":"😤","desc":"A desvantagem dura toda a provocação; Henrique ganha +2 CA e ataca o alvo com vantagem." },
"bardo_provocacao_3":       {... "linha":"bardo_provocacao","preco":200,"requer":"bardo_provocacao_2",
    "nome":"Provocação III","icon":"😤","desc":"Todos os aliados atacam o alvo provocado com vantagem por 1 rodada." },
"bardo_lendas_supremas":    {... "linha":"bardo_lendas","preco":300,"requer":None,
    "nome":"Lendas Supremas","icon":"📖","desc":"Todos os bônus de Lenda beneficiam o grupo inteiro (enquanto Henrique vivo)." },
```
(Todos com `categoria:"especializacao"`, `classe:"bard"`, `exclusiva:False`,
`nivel` conforme conveniência.)

### 3.2 Lendas Avançadas — geradas de `MONSTER_DEFS` (extensível)
Cada tipo em `MONSTER_DEFS` vira um nó `lenda_<type>` com preço por tier:
```python
_LENDA_PRECO_TIER = {1: 60, 2: 90, 3: 120, 4: 200}

def _gerar_catalogo_lendas():
    entradas = {}
    for mdef in MONSTER_DEFS:
        gid = f"lenda_{mdef['type']}"
        entradas[gid] = {
            "id": gid, "categoria": "especializacao", "classe": "bard",
            "linha": "bardo_lendas", "nivel": None, "requer": None, "exclusiva": False,
            "preco": _LENDA_PRECO_TIER.get(mdef.get("tier", 1), 90),
            "nome": f"Lenda: {mdef['name']}", "icon": mdef.get("emoji", "📖"),
            "desc": f"+1 de ataque e +1 nos saves contra {mdef['name']}.",
            "lenda_tipo": mdef["type"],
        }
    return entradas

GUILD_CATALOG.update(_gerar_catalogo_lendas())
```
Colocado **após** a definição de `MONSTER_DEFS` (que fica ~linha 810, depois do
`GUILD_CATALOG` literal). Monstros futuros aparecem na Guilda automaticamente.

> **Nota de UI:** ~30 nós de Lenda aparecem na aba Especializações da Guilda —
> lista longa, mas aceitável (mesmo padrão das Fórmulas de Armadilha). Agrupar por
> tier fica como melhoria futura, fora de escopo.

---

## 4. Gating no servidor (helpers + handlers)

Helpers como métodos de `GameRoom`, perto dos helpers das fases anteriores.

### 4.1 Canção Heroica
```python
    def _cancao_nivel_atributo(self, p, attr_id):
        """Bônus daquele atributo na canção: 2 se comprado, senão 1."""
        return 2 if tem_espec(p, f"bardo_cancao_{attr_id}") else 1

    def _cancao_custo_reducao(self, p):
        return 1 if tem_espec(p, "bardo_cancao_suprema") else 0
```
- `_aplicar_buffs_cancao`: trocar `buffs[attr["efeito"]] = 1` por
  `buffs[attr["efeito"]] = self._cancao_nivel_atributo(bardo, attr_id)`.
- Custo com Suprema: aplicar a redução no cálculo do custo. Como
  `_calcular_custo_cancao` é função de módulo (sem acesso ao jogador), o modo mais
  limpo é reduzir **onde o custo é debitado** (ativação e upkeep): custo efetivo =
  `max(0, custo["fome"] - red)` / `max(0, custo["sede"] - red)`, com
  `red = self._cancao_custo_reducao(p)`. Aplicar em `handle_ativar_cancao` (débito
  e mensagem), `_cobrar_manutencao_cancao` (checagem, débito e mensagem) e no
  `cancao_custo` guardado (guardar o custo JÁ reduzido, para o upkeep reusar).

### 4.2 Provocação II/III
Na `handle_provocacao`, após marcar o monstro, registrar quem provocou e (III) a
janela de vantagem dos aliados:
```python
        alvo["provocado_por"] = pid
        if tem_espec(p, "bardo_provocacao_3"):
            alvo["provocado_aliados_vantagem_round"] = self.round_num
```
Helpers:
```python
    def _provocador(self, monstro):
        """Retorna o bardo (vivo) que provocou este monstro, ou None."""
        pid = monstro.get("provocado_por")
        b = self.players.get(pid) if pid else None
        return b if (b and b.get("alive") and b.get("class_id") == "bard"
                     and monstro.get("provocado_turnos", 0) > 0) else None

    def _provocacao_ca_bonus(self, alvo_player, monstro):
        """+2 CA do alvo quando o monstro que ele provocou (com Provocação II) o ataca."""
        b = self._provocador(monstro)
        return 2 if (b and b["id"] == alvo_player.get("id") and tem_espec(b, "bardo_provocacao_2")) else 0

    def _provocacao_atk_vantagem(self, atacante, monstro):
        """Vantagem ao atacar o monstro provocado: o bardo (Provocação II) sempre;
        qualquer aliado se Provocação III e dentro da janela de 1 rodada."""
        b = self._provocador(monstro)
        if not b:
            return False
        if atacante.get("id") == b["id"] and tem_espec(b, "bardo_provocacao_2"):
            return True
        if tem_espec(b, "bardo_provocacao_3") and \
           monstro.get("provocado_aliados_vantagem_round") == self.round_num:
            return True
        return False
```
- **Desvantagem persistente (II):** onde hoje `provocado_turno_efeito` é zerado após
  o ataque do monstro (sites ~11176, 12906), NÃO zerar se o provocador tem
  `bardo_provocacao_2` e `provocado_turnos > 0` — a desvantagem continua valendo.
  (O `provocado_turnos` decai normalmente e encerra tudo ao chegar a 0.)
- **+2 CA (II):** somar `self._provocacao_ca_bonus(alvo, m)` ao `effective_ac` do
  jogador nos sites de ataque de monstro (onde `m` e o alvo jogador estão em escopo).
- **Vantagem do bardo / aliados (II/III):** em `handle_attack`, incluir
  `self._provocacao_atk_vantagem(p, target)` no cálculo de `vantagem`.

### 4.3 Lendas (extensível)
```python
    def _bardo_lendas(self):
        """Retorna o bardo vivo (dono das Lendas), ou None."""
        return next((q for q in self.players.values()
                     if q.get("class_id") == "bard" and q.get("alive")), None)

    def _lenda_atk_bonus(self, atacante, monstro):
        """+1 de ataque vs a espécie estudada. Base: só o próprio bardo. Com
        Lendas Supremas: qualquer aliado (enquanto o bardo estiver vivo)."""
        b = self._bardo_lendas()
        if not b or not tem_espec(b, f"lenda_{monstro.get('type','')}"):
            return 0
        if atacante.get("id") == b["id"] or tem_espec(b, "bardo_lendas_supremas"):
            return 1
        return 0

    def _lenda_resist_bonus(self, alvo_player, fonte_monstro):
        """+1 nos saves contra as habilidades daquela espécie (mesma regra de grupo)."""
        if not fonte_monstro:
            return 0
        b = self._bardo_lendas()
        if not b or not tem_espec(b, f"lenda_{fonte_monstro.get('type','')}"):
            return 0
        if alvo_player.get("id") == b["id"] or tem_espec(b, "bardo_lendas_supremas"):
            return 1
        return 0
```
- **Ataque (+1):** em `handle_attack`, somar `self._lenda_atk_bonus(p, target)` ao
  `eff_atk` (bônus de acerto) quando o alvo é monstro.
- **Resistência (+1) — a parte mais envolvida:** adicionar um param opcional
  `fonte=None` a `_testar_save`; quando `fonte` for um monstro e o `alvo` for
  jogador, somar `self._lenda_resist_bonus(alvo, fonte)` ao `bonus`. Depois, passar
  `fonte=m` **apenas** nos `_testar_save` disparados por **habilidade de monstro**
  (o subset de call sites onde o monstro-fonte `m` está em escopo — ex.: ~11286,
  11761, 11827, 12293). Traps/venenos/ambiente ficam sem `fonte` (não é
  "habilidade de criatura"). Isolar numa task própria.

---

## 5. Cliente (`game.js` + `gameState.js`)

Getters em `gameState.js` (lidos da posse; caem para o player do `game_state`):
`bardoCancaoNivel(attr)`, `bardoCancaoSuprema()`, `bardoProvocacaoNivel()`,
`bardoLendasComprado(tipo)` (ou a lista), `bardoLendasSupremas()`.
- **Painel da Canção:** cada atributo mostra +1 ou +2 conforme a posse; o custo de
  manutenção exibido reflete a redução da Suprema.
- **Descrições:** Provocação reflete o nível (II/III); as Lendas aparecem na aba
  Especializações da Guilda (geradas). Sem UI nova em jogo além de descrições.

> Robustez na masmorra: `guildOwnedOf` já cai para o player do `game_state`. O
> servidor é autoritativo.

---

## 6. Testes (`tools/test_bardo_espec.py`)

Harness do projeto; helper `bard(**owned)` + `monster(type=...)`. Cobrir:
1. **Canção:** `_cancao_nivel_atributo` = 1/2 por atributo; buffs aplicados usam o
   nível; `_cancao_custo_reducao` = 0/1; ativação/upkeep debitam o custo reduzido
   (mín 0) com a Suprema.
2. **Provocação:** `_provocacao_ca_bonus` = +2 só quando o monstro provocado ataca
   o bardo dono com `provocacao_2`; `_provocacao_atk_vantagem` True para o bardo
   (II) e para aliados (III, na janela de 1 rodada); desvantagem persiste com II.
3. **Lendas:** catálogo gerado tem `lenda_<tipo>` para tipos de `MONSTER_DEFS`, com
   preço por tier; `_lenda_atk_bonus` = +1 só p/ o bardo (base) e p/ aliados com
   Supremas; `_lenda_resist_bonus` idem; `_testar_save(..., fonte=monstro)` soma o
   bônus para jogador-alvo.
4. **Compra:** `bardo_provocacao_3` recusado sem `_2`.

---

## 7. Fronteiras (NÃO fazer nesta sub-fase)

- Outras classes (Mago).
- Agrupamento visual das ~30 Lendas na Guilda (melhoria de UI futura).
- Bônus de resistência em saves NÃO causados por habilidade de monstro (traps,
  venenos, ambiente) — fora do conceito "habilidades daquela criatura".
- Reembolso; tabela de custo extra genérica.

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Threading da fonte-monstro nos saves (resistência) é invasivo | Param opcional `fonte=None` em `_testar_save` (um ponto), passado só nos sites de habilidade de monstro; task isolada + testes. |
| Desvantagem persistente da Provocação II vazar para além da duração | Só persiste enquanto `provocado_turnos > 0`; o decaimento existente encerra tudo. Teste dedicado. |
| Catálogo gerado de Lendas conflitar com ids | Prefixo `lenda_` único por tipo; `GUILD_CATALOG.update(...)` após `MONSTER_DEFS`, sem colisão de nomes. |
| Custo da Canção Suprema dar negativo | `max(0, ...)` em fome e sede. |
| Bardo morto ainda conceder Lenda ao grupo | `_bardo_lendas`/`_provocador` exigem `alive`. |
| ~30 nós de Lenda incharem o `city_state` | São dados leves (dict pequeno por nó); mesmo padrão já usado para Fórmulas. |
