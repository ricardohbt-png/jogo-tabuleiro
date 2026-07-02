# Guilda dos Heróis — Fase 1d: Especializações do Ladino

**Data:** 2026-07-01
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 1d (Ladino). Fase 1 decomposta por classe. Feito: 1a (Guerreiro), 1b
(Clérigo), 1c (Paladino). Próximas: Bardo, Mago.
**Depende de:** Fase 0 + padrão das Fases 1a/1b/1c (`tem_espec`, entradas
`categoria:"especializacao"` no `GUILD_CATALOG`, `handle_guild_buy`).

---

## 1. Visão geral

Especializações = upgrades permanentes e sempre-ativos das habilidades-base
(sem slot, sem "equipar"). Esta sub-fase cobre o **Ladino** (Luccas,
`class_id:"rogue"`) em **5 linhas**: Ataque Furtivo, Fórmulas de Armadilha,
Desarme, Veneno Rápido e Esconder nas Sombras.

Ao contrário das fases anteriores, aqui **duas mecânicas hoje não batem com o
texto de referência** e precisam de redesign real (não só números):

1. **Ataque Furtivo** hoje dispara com "qualquer aliado adjacente ao alvo"
   (`_verificar_ataque_furtivo`, server.py) — mais permissivo que o Nível I
   descrito ("só quando oculto"). Esse comportamento de hoje vira o **Nível II**
   (compra); o Nível III (Supremo) é uma mecânica nova de reação.
2. **Fórmulas de Armadilha**: hoje as 8 armadilhas de `ARMADILHAS` já são todas
   fabricáveis de graça. Precisam ser gateadas — e de forma **extensível**, para
   que armadilhas futuras entrem no sistema de compra sem mudança de código além
   de 2 campos na própria definição.

---

## 2. Estado atual confirmado no código

- `_verificar_ataque_furtivo(luccas, alvo)`: true se `invisivel_sombras`/
  `oculto_vela`, OU há qualquer aliado vivo adjacente (Chebyshev 1) ao alvo.
- `_dados_furtivo(nivel)`: 2d4 (níveis 1-2), 3d4 (3-4), 4d4 (5+).
- O dano furtivo é somado direto em `dmg` dentro de `handle_attack`, sem rolagem
  de acerto própria (usa o mesmo hit do ataque de Luccas).
- `ARMADILHAS` (dict de 8 tipos: `buraco`, `armadilha_urso`, `fosso_estacas`,
  `rede`, `armadilha_incendiaria`, `mina_terrestre`, `fosso_envenenado`,
  `nuvem_gas`) — `handle_criar_armadilha` aceita qualquer tipo, sem gate.
- `handle_desarmar_armadilha`: `total = d20 + mod(DES)` vs `tipo["dificuldade"]`;
  sucesso remove a armadilha (sem recuperação); nat 1 dispara nele mesmo.
- `weapon_poison`/`weapon_poison_hits` (escalares): Veneno Rápido/`coat_poison`
  untam 1 veneno; melee dura 1 golpe certeiro; à distância dura `VENENO_CARGAS`
  disparos (acerto ou erro).
- `handle_esconder_sombras`: ação bônus (`bonus_action_used`), 🍖2💧1,
  `d20+mod(DES)` vs `percepção do monstro mais atento + nº de monstros na sala`.
  `_quebrar_invisibilidade(p, motivo)` só é chamado **ao atacar** (não ao mover)
  — hoje mover já não quebra a invisibilidade.
- `self.temp_def` (dict `pid -> bônus de CA`) já existe e **expira sozinho em 1
  turno** (server.py:3468, decremento em ~10376-10382) — mecanismo pronto para
  reusar no bônus de CA do Esconder III.

---

## 3. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Modelo geral | Base = comportamento enfraquecido/atual conforme a linha; compra II/III; III exige II por linha (exceto Fórmulas, que não tem níveis). II=150, III=200 (Fórmulas têm preço próprio por tipo). |
| Ataque Furtivo I (grátis) | Só dispara oculto (`invisivel_sombras`/`oculto_vela`). |
| Ataque Furtivo II | Também dispara com aliado adjacente ao alvo (= comportamento atual, agora exige compra). |
| Ataque Furtivo III (Supremo) | Reação automática e imediata: quando **qualquer aliado que não seja Luccas** acerta um inimigo vivo, Luccas desfere um ataque furtivo automático nele também — **1×/inimigo/rodada** (reseta por `round_num`). Só dispara em **acerto** do aliado; **bloqueado se Luccas estiver petrificado, paralisado ou imobilizado** (`perde_turno`) — ele precisa estar capaz de reagir. Não existe "controle mental" sobre jogadores no jogo hoje (`dominado` só se aplica a mortos-vivos do Pedro), então esse caso não se aplica. |
| Fórmulas de Armadilha | **Extensível**: cada entrada de `ARMADILHAS` ganha campos opcionais `formula_guild_id`/`formula_preco`; o catálogo da Guilda é **gerado a partir desses dados**. `buraco` não tem esses campos → sempre grátis. As outras 7 recebem preço: `armadilha_urso` 100, `fosso_estacas` 120, `fosso_envenenado` 130, `rede` 150, `armadilha_incendiaria` 180, `mina_terrestre` 220, `nuvem_gas` 250. |
| Desarme II | +2 no teste (`d20+DES+2` vs dificuldade). |
| Desarme III | Mantém +2 (não soma mais) + após sucesso, um **2º teste** (mesma fórmula/dificuldade) que, se passar, devolve o `custo_ouro` da armadilha desarmada. |
| Veneno Rápido base | Melee: 1 golpe certeiro. À distância: `VENENO_CARGAS` disparos (inalterado em todos os níveis). |
| Veneno Rápido II | Melee dura **2 golpes** certeiros (era 1). Só afeta corpo a corpo. |
| Veneno Rápido III | Luccas pode manter **2 venenos diferentes** na arma simultaneamente (só melee): um 2º slot é preenchido em vez de sobrescrever o 1º; cada golpe aplica **ambos**, cada um gastando suas próprias cargas independentemente. |
| Esconder nas Sombras II | +2 no teste de esconder-se (`d20+DES+2` vs dificuldade). |
| Esconder nas Sombras III | Mantém +2 do II. Ativar a habilidade **deixa de gastar a ação bônus** do turno. **Adicional:** ao quebrar a invisibilidade (ataque), Luccas ganha **+2 de CA por 1 rodada** (via `self.temp_def`, que já expira sozinho em 1 turno). |
| Custo de uso | Ouro é o único custo das compras. As habilidades continuam com o custo de fome/sede atual (sem tabela de custo extra genérica). |
| Arquitetura | Imperativa: catálogo gerado (Fórmulas) + literal (demais linhas); gating inline nos handlers via `tem_espec` + helpers. |
| Autoridade | Servidor autoritativo em tudo (recusa tipo de armadilha não destravado, aplica teto de furtivo/veneno). |

---

## 4. Catálogo (`GUILD_CATALOG`, server.py)

### 4.1 Ataque Furtivo, Desarme, Veneno Rápido, Esconder nas Sombras (8 nós literais)

```python
"ladino_furtivo_2": { "id":"ladino_furtivo_2","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_furtivo","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Ataque Furtivo II","icon":"🗡️",
    "desc":"Ataque Furtivo também dispara se há aliado adjacente ao alvo." },
"ladino_furtivo_3": { "id":"ladino_furtivo_3","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_furtivo","nivel":3,"requer":"ladino_furtivo_2","exclusiva":False,"preco":200,
    "nome":"Ataque Furtivo Supremo","icon":"🗡️",
    "desc":"1×/inimigo/rodada: quando um aliado acerta um inimigo, Luccas reage com um Ataque Furtivo nele." },
"ladino_desarme_2": { "id":"ladino_desarme_2","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_desarme","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Desarme II","icon":"🔧","desc":"+2 na chance de desarmar armadilhas." },
"ladino_desarme_3": { "id":"ladino_desarme_3","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_desarme","nivel":3,"requer":"ladino_desarme_2","exclusiva":False,"preco":200,
    "nome":"Desarme III","icon":"🔧","desc":"Chance extra de recuperar o ouro da armadilha desarmada." },
"ladino_veneno_2": { "id":"ladino_veneno_2","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_veneno","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Veneno Rápido II","icon":"☠️","desc":"O veneno na arma (corpo a corpo) dura 2 golpes certeiros." },
"ladino_veneno_3": { "id":"ladino_veneno_3","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_veneno","nivel":3,"requer":"ladino_veneno_2","exclusiva":False,"preco":200,
    "nome":"Veneno Rápido III","icon":"☠️","desc":"Pode manter 2 venenos diferentes na arma ao mesmo tempo." },
"ladino_esconder_2": { "id":"ladino_esconder_2","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_esconder","nivel":2,"requer":None,"exclusiva":False,"preco":150,
    "nome":"Esconder nas Sombras II","icon":"🌑","desc":"+2 na chance de se esconder nas sombras." },
"ladino_esconder_3": { "id":"ladino_esconder_3","categoria":"especializacao","classe":"rogue",
    "linha":"ladino_esconder","nivel":3,"requer":"ladino_esconder_2","exclusiva":False,"preco":200,
    "nome":"Esconder nas Sombras III","icon":"🌑",
    "desc":"Ativar não gasta mais a ação bônus. Ao ser revelado, +2 de CA por 1 rodada." },
```

### 4.2 Fórmulas de Armadilha (extensível — geradas a partir de `ARMADILHAS`)

Adicionar a cada entrada de `ARMADILHAS` (exceto `buraco`) os campos:
```python
"armadilha_urso":         {..., "formula_guild_id": "ladino_armadilha_urso",         "formula_preco": 100},
"fosso_estacas":          {..., "formula_guild_id": "ladino_fosso_estacas",          "formula_preco": 120},
"fosso_envenenado":       {..., "formula_guild_id": "ladino_fosso_envenenado",       "formula_preco": 130},
"rede":                   {..., "formula_guild_id": "ladino_rede",                   "formula_preco": 150},
"armadilha_incendiaria":  {..., "formula_guild_id": "ladino_armadilha_incendiaria",  "formula_preco": 180},
"mina_terrestre":         {..., "formula_guild_id": "ladino_mina_terrestre",         "formula_preco": 220},
"nuvem_gas":              {..., "formula_guild_id": "ladino_nuvem_gas",              "formula_preco": 250},
```
`buraco` não recebe esses campos (permanece sempre grátis).

Função geradora (chamada uma vez, no carregamento do módulo, para popular
`GUILD_CATALOG` com uma entrada por tipo que tiver `formula_guild_id`):
```python
def _gerar_catalogo_formulas_armadilha():
    entradas = {}
    for tipo_id, tipo in ARMADILHAS.items():
        gid = tipo.get("formula_guild_id")
        if not gid:
            continue
        entradas[gid] = {
            "id": gid, "categoria": "especializacao", "classe": "rogue",
            "linha": "ladino_armadilhas", "nivel": None, "requer": None, "exclusiva": False,
            "preco": tipo.get("formula_preco", 100),
            "nome": f"Fórmula: {tipo['nome']}", "icon": tipo.get("icone", "🪤"),
            "desc": f"Desbloqueia permanentemente a fabricação de {tipo['nome']}.",
        }
    return entradas
```
`GUILD_CATALOG.update(_gerar_catalogo_formulas_armadilha())` — chamado logo após
a definição literal de `GUILD_CATALOG` (que já contém os nós do Guerreiro/
Clérigo/Paladino/os 8 nós §4.1 do Ladino).

> **Extensibilidade futura:** para adicionar uma nova armadilha ao sistema de
> venda, basta acrescentar `"formula_guild_id"`/`"formula_preco"` à nova entrada
> de `ARMADILHAS` — ela aparece automaticamente na Guilda, sem tocar em
> `GUILD_CATALOG`, `handle_criar_armadilha` ou no cliente.

---

## 5. Gating no servidor (helpers + handlers)

Helpers como métodos de `GameRoom`, perto dos helpers das fases anteriores:

```python
    def _armadilhas_desbloqueadas(self, p):
        """Tipos de armadilha que o Ladino pode fabricar: buraco sempre grátis;
        os demais exigem a Fórmula correspondente (extensível via ARMADILHAS)."""
        tipos = set()
        for tipo_id, tipo in ARMADILHAS.items():
            gid = tipo.get("formula_guild_id")
            if gid is None or tem_espec(p, gid):
                tipos.add(tipo_id)
        return tipos

    def _desarme_bonus(self, p):
        return 2 if (tem_espec(p, "ladino_desarme_2") or tem_espec(p, "ladino_desarme_3")) else 0

    def _veneno_rapido_max_hits(self, p):
        """Golpes que o veneno melee dura (1 base / 2 com ladino_veneno_2)."""
        return 2 if tem_espec(p, "ladino_veneno_2") else 1

    def _veneno_rapido_2_slots(self, p):
        return tem_espec(p, "ladino_veneno_3")

    def _esconder_bonus(self, p):
        return 2 if (tem_espec(p, "ladino_esconder_2") or tem_espec(p, "ladino_esconder_3")) else 0
```

### 5.1 Ataque Furtivo

`_verificar_ataque_furtivo`: o ramo "aliado adjacente" passa a exigir
`tem_espec(luccas, "ladino_furtivo_2")`:
```python
    def _verificar_ataque_furtivo(self, luccas, alvo):
        if luccas.get("invisivel_sombras") or luccas.get("oculto_vela"):
            return True
        if not tem_espec(luccas, "ladino_furtivo_2"):
            return False
        ax, ay = alvo["pos"]
        for pid2, aliado in self.players.items():
            if pid2 == luccas["id"] or not aliado["alive"]:
                continue
            if max(abs(aliado["pos"][0] - ax), abs(aliado["pos"][1] - ay)) <= 1:
                return True
        return False
```

Novo helper `_furtivo_reativo`, chamado dentro de `handle_attack` logo após
`target["hp"] -= dmg` (antes da checagem de morte), para o ataque de **qualquer
jogador**:
```python
    async def _furtivo_reativo(self, atacante, target):
        """Ataque Furtivo Supremo (ladino_furtivo_3): reage ao acerto de um aliado
        contra um inimigo, 1x por inimigo por rodada. Não dispara no próprio
        ataque de Luccas, nem se Luccas estiver incapaz de reagir (petrificado,
        paralisado ou imobilizado — perde_turno)."""
        if atacante.get("class_id") == "rogue" or target.get("hp", 0) <= 0:
            return
        luccas = next((q for q in self.players.values()
                       if q.get("class_id") == "rogue" and q.get("alive")
                       and q["id"] != atacante["id"]), None)
        if not luccas or not tem_espec(luccas, "ladino_furtivo_3"):
            return
        if luccas.get("petrificado") or luccas.get("paralisado") or luccas.get("perde_turno"):
            return
        if luccas.get("furtivo_reativo_round") != self.round_num:
            luccas["furtivo_reativo_round"] = self.round_num
            luccas["furtivo_reativo_alvos"] = set()
        if target["id"] in luccas.get("furtivo_reativo_alvos", set()):
            return
        luccas["furtivo_reativo_alvos"].add(target["id"])
        nd4 = self._dados_furtivo(luccas.get("level", 1))
        dano = sum(random.randint(1, 4) for _ in range(nd4))
        await self.broadcast({"type": "dice_roll", "die": "d4", "value": dano,
                               "label": "Ataque Furtivo (reação)"})
        target["hp"] -= dano
        await self.gm_say(f"🗡️ **{luccas['name']}** reage ao ataque de **{atacante['name']}** — "
                          f"Ataque Furtivo Supremo! +{dano} de dano [{nd4}d4] em **{target['name']}**.")
```
Chamada em `handle_attack`, logo após `target["hp"] -= dmg`:
```python
                target["hp"] -= dmg
                await self._furtivo_reativo(p, target)
```
(A checagem de morte já existente, logo abaixo, opera sobre o HP já atualizado
— se a reação matar o alvo, `_monster_dies` dispara normalmente.)

### 5.2 Fórmulas de Armadilha

Em `handle_criar_armadilha`, logo após `tipo = ARMADILHAS.get(tipo_id)`:
```python
        if tipo_id not in self._armadilhas_desbloqueadas(p):
            await self.send_to(pid, {"type": "error",
                "msg": f"Você ainda não aprendeu a fórmula de {tipo['nome']} — compre na Guilda."}); return
```

### 5.3 Desarme

Em `handle_desarmar_armadilha`, trocar `total = d20 + bonus` por
`total = d20 + bonus + self._desarme_bonus(p)`. Após sucesso
(`elif total >= dif:`), antes de remover a armadilha, adicionar o teste de
recuperação:
```python
        elif total >= dif:
            custo_ouro_arm = tipo.get("custo_ouro", 0)
            recuperou = False
            if tem_espec(p, "ladino_desarme_3") and custo_ouro_arm > 0:
                d20r = random.randint(1, 20)
                totalr = d20r + bonus + self._desarme_bonus(p)
                await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20r,
                                       "label": f"{p['name']} — Recuperar"})
                if totalr >= dif:
                    p["gold"] += custo_ouro_arm
                    recuperou = True
            self.armadilhas = [a for a in self.armadilhas if a["id"] != arm["id"]]
            msg_recover = f" Recuperou 🪙{custo_ouro_arm}!" if recuperou else ""
            await self.gm_say(f"✅ Armadilha desarmada com sucesso!{msg_recover}")
```

### 5.4 Veneno Rápido

Novos campos em `make_player`: `"weapon_poison_2": None`, `"weapon_poison_2_hits": 0`.

Em `handle_veneno_rapido`, para o ramo melee (`not _is_ranged`): trocar
`cargas = VENENO_CARGAS if _is_ranged else 1` por
`cargas = VENENO_CARGAS if _is_ranged else self._veneno_rapido_max_hits(p)`, e
decidir o slot:
```python
        if not _is_ranged and p.get("weapon_poison") and self._veneno_rapido_2_slots(p) and not p.get("weapon_poison_2"):
            p["weapon_poison_2"]      = vid
            p["weapon_poison_2_hits"] = cargas
        else:
            p["weapon_poison"]      = vid
            p["weapon_poison_hits"] = cargas
```
(Ranged mantém o comportamento atual — sempre sobrescreve o slot único.)

No hit melee em `handle_attack` (~5249-5254), após aplicar o slot 1 como hoje,
aplicar também o slot 2 se presente:
```python
                    elif p.get("weapon_poison"):
                        await self._aplicar_veneno(target, p["weapon_poison"], fonte="ataque")
                        p["weapon_poison_hits"] = p.get("weapon_poison_hits", 1) - 1
                        if p["weapon_poison_hits"] <= 0:
                            p["weapon_poison"] = None
                            await self.gm_say(f"🧴 O veneno da arma de **{p['name']}** acabou.")
                    if p.get("weapon_poison_2"):
                        await self._aplicar_veneno(target, p["weapon_poison_2"], fonte="ataque")
                        p["weapon_poison_2_hits"] = p.get("weapon_poison_2_hits", 1) - 1
                        if p["weapon_poison_2_hits"] <= 0:
                            p["weapon_poison_2"] = None
                            await self.gm_say(f"🧴 O 2º veneno da arma de **{p['name']}** acabou.")
```
(Nota: o `elif` do slot 1 vira `if` separado para o slot 2, para que ambos possam
aplicar no mesmo golpe quando os dois estiverem ativos.)

> **Fora de escopo:** o efeito genérico `coat_poison` (item de uso geral, não
> exclusivo de Luccas) permanece com o comportamento atual (1 golpe/`VENENO_CARGAS`
> disparos), sem os bônus de nível — essas melhorias são específicas da habilidade
> Veneno Rápido do Ladino.

### 5.5 Esconder nas Sombras

Em `handle_esconder_sombras`, trocar `total = d20 + bonus_dex` por
`total = d20 + bonus_dex + self._esconder_bonus(p)`. Trocar
`p["bonus_action_used"] = True` por (só marca se NÃO tiver o Nível III):
```python
        if not tem_espec(p, "ladino_esconder_3"):
            p["bonus_action_used"] = True
```
Em `_quebrar_invisibilidade`, antes do `return True`, adicionar o bônus de CA
(reusando `self.temp_def`, que já expira em 1 turno):
```python
    async def _quebrar_invisibilidade(self, p, motivo="ao agir"):
        if not p.get("invisivel_sombras"):
            return False
        p["invisivel_sombras"] = False
        await self.gm_say(f"🌑 **{p['name']}** revela-se ({motivo}).")
        if tem_espec(p, "ladino_esconder_3"):
            self.temp_def[p["id"]] = self.temp_def.get(p["id"], 0) + 2
            await self.gm_say(f"🌀 **{p['name']}** ganha +2 de CA por 1 rodada ao se revelar!")
        return True
```

---

## 6. Cliente (`game.js` + `gameState.js`)

- **Criar armadilha:** o painel de escolha de tipo (`ARMADILHAS_LUCCAS` no
  cliente) passa a filtrar pelos tipos destravados
  (`GS.ladinoArmadilhasDesbloqueadas()`), desabilitando/ocultando os não
  comprados com dica de preço.
- **Ataque Furtivo:** descrição reflete o nível possuído (base "só oculto" / II
  "+ aliado adjacente" / III "+ reação automática").
- **Desarme:** mostra o bônus atual (+0/+2) e, com `_3`, menciona a chance de
  recuperação.
- **Veneno Rápido:** painel mostra quantos golpes o veneno dura e, com `_3`,
  permite untar um 2º veneno sem descartar o 1º.
- **Esconder nas Sombras:** mostra o bônus atual e, com `_3`, indica que não
  gasta ação bônus.

> Robustez na masmorra: `guildOwnedOf` já cai para o player do `game_state`
> quando `cityState=null` (Fase 0). Servidor é autoritativo em todos os casos.

---

## 7. Testes (`tools/test_ladino_espec.py`)

Harness do projeto; helper `rogue(**owned)` análogo aos das fases anteriores.
Cobrir:
1. **Furtivo:** base só dispara oculto; com `_2` também dispara com aliado
   adjacente; `_furtivo_reativo` aplica dano 1×/alvo/rodada, não dispara se o
   atacante é o próprio Luccas, não dispara se o alvo já está com HP≤0, reseta
   ao avançar `round_num`, **e não dispara se Luccas estiver petrificado,
   paralisado ou com `perde_turno`** (incapaz de reagir).
2. **Fórmulas:** `_armadilhas_desbloqueadas` cresce por compra; `buraco` sempre
   presente; `handle_criar_armadilha` recusa tipo bloqueado e aceita o
   destravado.
3. **Desarme:** bônus +2 aplicado ao teste; recuperação só dispara com `_3` e só
   quando o 2º teste passa; sem `_3`, nunca recupera.
4. **Veneno Rápido:** melee dura 1 golpe base / 2 com `_2`; com `_3`, uma 2ª
   aplicação preenche o slot 2 sem apagar o slot 1; um hit aplica os dois
   venenos quando ambos presentes; ranged inalterado em qualquer nível.
5. **Esconder nas Sombras:** bônus +2 no teste com `_2`/`_3`; com `_3`, não seta
   `bonus_action_used`; ao quebrar invisibilidade com `_3`, `self.temp_def`
   ganha +2 para aquele pid.

---

## 8. Fronteiras (NÃO fazer nesta sub-fase)

- Outras classes (Bardo, Mago).
- Bônus de nível para o efeito genérico `coat_poison` (item, não exclusivo de
  Luccas).
- Tabela de custo extra de progressão genérica (nenhuma linha desta sub-fase
  precisa).
- Reembolso de compras.
- Novas armadilhas de fato (só a infraestrutura extensível para recebê-las).

---

## 9. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Redesign do Ataque Furtivo nerfa quem já joga (base fica mais restrito) | Intencional e documentado; Furtivo II restaura o comportamento de hoje. |
| Reação do Furtivo Supremo disparar em duplicidade ou fora de hora | `_furtivo_reativo` checa `atacante.class_id != rogue`, `target.hp>0`, e o set por rodada; chamada num único ponto de `handle_attack`. |
| Reação disparar com Luccas incapaz de agir (petrificado/paralisado/imobilizado) | `_furtivo_reativo` checa `petrificado`/`paralisado`/`perde_turno` de Luccas antes de aplicar o dano; testado explicitamente (§7.1). Não há mecânica de controle mental sobre jogadores no jogo hoje. |
| Refactor de veneno (2 slots) quebrar o fluxo ranged/`coat_poison` | Ranged e `coat_poison` explicitamente fora do escopo do gating; só o ramo melee de `handle_veneno_rapido`/hit muda. |
| Catálogo gerado (Fórmulas) conflitar com ids literais | `formula_guild_id` usa prefixo `ladino_` único por tipo; `GUILD_CATALOG.update(...)` roda após os literais, sem sobrescrever nós existentes (nomes não colidem). |
| `self.temp_def` já ser usado por outros sistemas (mago/canção) | Reuso aditivo (`+=`), como os demais usos já fazem; não zera nem substitui bônus existentes. |
