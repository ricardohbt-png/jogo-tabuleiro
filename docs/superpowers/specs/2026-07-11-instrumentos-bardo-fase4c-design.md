# Instrumentos do Bardo — Fase 4c (Encantamento Rúnico — efeitos bespoke)

**Data:** 2026-07-11
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** design aprovado no brainstorm; pendente revisão do spec.
**Depende de:** Fases 1–4b (framework + Rúnico simples, em master).

---

## 1. Visão geral

Fecha o Encantamento Rúnico com os **3 efeitos bespoke** que a Fase 4b deixou para cá —
mudanças reais de lógica (não stat-based). Cada um reusa um mecanismo existente:

1. **Harpa Rúnica** — Nota Cortante vira uma **linha reta direcional** (`_caminho_relampago`).
2. **Tambor Rúnico** — Acorde ganha **Atordoar** (`perde_turno`) na falha e **−1 Ataque** no sucesso.
3. **Alaúde Rúnico** — a Canção Heroica dá **+1 em Fortitude & Vontade** aos aliados sob ela.

Não há mudança de framework. A camada `runico` de `_instrumento_stats` (Fase 4b) **não** é
usada por estas 3 bases (efeitos são lógica de handler/hook).

### Decisões do brainstorm

| Tema | Decisão |
|---|---|
| Harpa Rúnica | Nota Cortante sempre em **linha direcional** quando Rúnica; cada alvo faz seu Reflexos-meia |
| Tambor Rúnico | **Soma** ao Acorde: falha → `perde_turno`; sucesso → −1 Ataque até o próximo turno |
| Alaúde Rúnico | **Amplo** — +1 em **Fortitude e Vontade** para aliados sob a Canção (cobre medo/doença/veneno) |

---

## 2. Harpa Rúnica — Nota Cortante em linha

**Servidor** (`_instr_nota_cortante`): se `inst.get("encantamento") == "runico"`, ramo linha:
- Lê a direção `data["dir"]` (normaliza dx/dy = −1/0/+1 como no Chamado); recusa se `[0,0]`.
- `tiles = self._caminho_relampago(p["pos"], dx, dy, st["alcance"])` (a mesma reta do Relâmpago).
- Para cada monstro vivo numa dessas casas: dano `roll_dice(st["dano"])` sonoro; Reflexos vs
  `_instrumento_cd`; sucesso = metade; aplica; mata via `_monster_dies`. Se nenhum monstro na
  linha → recusa sem custo (retorna False). Narra "em linha".
- Senão (não-Rúnica): comportamento atual (alvo único). Assinatura/retorno inalterados.

**Cliente** (`acionarInstrumento`, ramo `nota_cortante`): se a Harpa equipada é Rúnica
(`inst.encantamento === 'runico'`), abre `escolherDirecaoInstrumento(b, (dx,dy) =>
GS.usarInstrumento(null, [dx,dy]))` (o mesmo seletor de 8 direções do Chamado); senão, o modal
de alvo único de sempre. `handle_usar_instrumento` já repassa `data` (`target_id` **ou** `dir`).

---

## 3. Tambor Rúnico — Atordoar / −1 Ataque

**Servidor** (`_instr_acorde_trovejante`): mantém o efeito base (dano + empurrão na falha,
metade no sucesso). Se `inst.get("encantamento") == "runico"`, por alvo, **além** do base:
- **Falha no save:** `m["perde_turno"] = True` (Atordoado — perde a próxima rodada; reusa o
  mecanismo já existente, narrado como "atordoado").
- **Sucesso no save:** `m["acorde_atk_pen_ate"] = self.round_num + 1` (−1 de Ataque até o
  próximo turno).

**Leitura da penalidade** — helper `_acorde_atk_pen(m)` → `-1` se `m.get("acorde_atk_pen_ate",
0) >= self.round_num`, senão `0`. Somado ao bônus de ataque do monstro em
`_execute_one_monster_attack` (o `m_atk`), **mesmo padrão round-stamped** do `_pressao_ca_pen`
(Pressão Constante, Fase 2b, que reduz a CA do monstro). Expira sozinho (sem processador de
limpeza) por comparação de rodada.

---

## 4. Alaúde Rúnico — +1 Fortitude & Vontade

**Servidor** — helper `_alaude_runico_resist(alvo, tipo_save)`:
- Retorna `0` se `tipo_save` ∉ {`fortitude`,`vontade`}, ou o alvo não é jogador, ou não está
  sob a Canção (`alvo.get("buffs_cancao")` ausente).
- Senão, se existe um bardo com `cancao_ativa` empunhando um Alaúde Rúnico no `off_hand`
  (`base=="alaude"` e `encantamento=="runico"`), retorna `1`; senão `0`.

Somado em `_testar_save` no mesmo ponto de `_lenda_resist_bonus`/`_resistencia_saves_bonus`:
```python
        bonus = (... + self._lenda_resist_bonus(alvo, fonte)
                 + self._resistencia_saves_bonus(alvo)
                 + self._alaude_runico_resist(alvo, tipo_save))
```
`_testar_save` é síncrono; o helper também. Cobre medo (Vontade) + doença/veneno (Fortitude)
exatamente, e alguns outros Fort/Vontade (aceito — a decisão foi o escopo amplo).

---

## 5. Cliente

Só o §2 muda o cliente (seletor de direção para a Harpa Rúnica). Tambor/Alaúde Rúnicos não têm
UI nova. O tooltip já mostra "Rúnica/o" no nome (Fase 4b).

---

## 6. Testes (`tools/test_instrumentos_bardo.py`)

- **Harpa Rúnica:** com `dir`, atinge TODOS os monstros na linha (cada um com seu Reflexos —
  falha dano cheio, sucesso metade); monstro fora da linha intacto; sem `dir` recusa sem custo.
  Harpa **não**-Rúnica continua alvo único (regressão).
- **Tambor Rúnico:** falha → alvo com `perde_turno`; sucesso → `_acorde_atk_pen(alvo) == -1` na
  rodada atual e `0` depois (expira). Tambor não-Rúnico não atordoa nem penaliza.
- **Alaúde Rúnico:** `_alaude_runico_resist` = 1 p/ aliado com `buffs_cancao` quando um bardo
  tem Alaúde Rúnico + `cancao_ativa`, em Fortitude e Vontade; `0` em Reflexos, `0` sem Alaúde
  Rúnico, `0` sem `buffs_cancao`. E o total de `_testar_save` sobe 1 nesse caso.
- Regressão: `test_instrumentos_bardo`, `test_bardo_espec`, `test_tecnicas_espec` verdes.

---

## 7. Fora de escopo (Fase 5)

- **5:** Improviso/Gaita (tabela 2d6 meta + Encore) — última peça do sistema de instrumentos.

---

## 8. Questões resolvidas

1. Harpa Rúnica — linha direcional (reusa `_caminho_relampago`); cada alvo Reflexos-meia. §2.
2. Tambor Rúnico — soma ao base (falha `perde_turno`; sucesso −1 Ataque round-stamped). §3.
3. Alaúde Rúnico — amplo (+1 Fort & Vontade p/ aliados sob a Canção). §4.
