# Instrumentos do Bardo — Fase 3 (Réquiem Final / Violino)

**Data:** 2026-07-11
**Classe alvo:** `bard` (Henrique) — exclusivo.
**Status:** design aprovado no brainstorm; pendente revisão do spec.
**Depende de:** Fases 1–2 (framework de instrumentos, em master).

---

## 1. Visão geral

O **Violino** adiciona o **Réquiem Final**: uma habilidade sustentada de alvo único que
combina 4 subsistemas novos, todos reusando padrões existentes:

1. **DoT escalonado** por turno do alvo (padrão de `_processar_paralisacao_turno`).
2. **Concentração** — o bardo testa Vontade ao sofrer dano ou o Réquiem termina.
3. **Aura de provocação** — o alvo e os monstros a ≤3 do bardo são forçados a atacá-lo
   (reusa o mecanismo `provocado_por` da Provocação).
4. **Manutenção por rodada** (padrão de `_cobrar_manutencao_cancao`).

É de **2 mãos** (atacar OU tocar). **Um Réquiem por bardo**; recastar encerra o anterior.
Set-and-forget: sem ação por turno para sustentar (só a manutenção de recursos).

### Decisões do brainstorm

| Tema | Decisão |
|---|---|
| Save do alvo | Sucesso = **sem dano** naquela rodada; a escalada continua pelo nº da rodada |
| Teto da escalada | **Por qualidade** (velho 3 / rústico 4 / padrão 5 dados) |
| Quebra de concentração | **Qualquer dano** ao bardo (ataques + armadilhas + venenos + chamas) |
| Custo | **-4🍖/-4💧 ativar** + **-2🍖/-2💧 manutenção por rodada** (sem recursos → encerra) |
| Efeito colateral | **Taunt**: alvo (qualquer distância) + monstros a ≤3 do bardo forçados a atacá-lo |
| Desativação | **Manual** (clicar na habilidade com o Réquiem ativo desliga — toggle) |

---

## 2. `INSTRUMENTOS_BASE["violino"]`

```python
    "violino": {
        "nome": "Violino", "icon": "🎻", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Réquiem Final",
        "desc": "Inicia uma melodia mortal sobre um alvo. A cada turno dele, faz Vontade ou sofre dano crescente (1d, 2d, 3d…). Enquanto toca, o alvo e inimigos a ≤3 do bardo são forçados a atacá-lo, e o bardo testa concentração ao sofrer dano. Manutenção -2🍖/-2💧 por rodada.",
        "efeito": {"tipo": "requiem_final", "save": "vontade"},
        "custo_fome": 4, "custo_sede": 4,          # ativação (afixos fome/sede reduzem)
        "manutencao_fome": 2, "manutencao_sede": 2, # por rodada (flat)
        "afixos_validos": ["fome", "sede", "alcance"],
        "stats": {
            "velho":   {"dado": "d2", "teto": 3, "alcance": 4},
            "rustico": {"dado": "d4", "teto": 4, "alcance": 5},
            "padrao":  {"dado": "d6", "teto": 5, "alcance": 6},
        },
    },
```

`_instrumento_stats` já cobre `alcance` (afixo). `dado`/`teto`/`manutencao_*` são lidos do
base/stats diretamente. `_instrumento_cd` dá o CD do save do alvo.

---

## 3. Ativação — `_instr_requiem_final(p, inst, st, data)`

- **Toggle:** se o bardo já tem `requiem_alvo`, esta ativação **desliga** o Réquiem
  (`_encerrar_requiem(p, "desativado")`) e retorna `False` (não cobra custo de novo — a
  economia de ação/`instrumento_usado` é tratada no `handle_usar_instrumento`; ver nota).
- **Alvo:** `data["target_id"]` (monstro vivo). Exige `_no_raio(p, m, st["alcance"])` e
  linha de visão (`_tem_linha_de_visao(p["pos"], m["pos"])`).
- Grava no bardo: `requiem_alvo = m["id"]`, `requiem_contador = 0`. No alvo:
  `m["requiem_por"] = p["id"]` (back-ref para o hook de turno). Aplica o taunt inicial
  (§5). Narra.
- Custo de ativação (-4/-4, já reduzido por afixos) é debitado pelo `handle_usar_instrumento`
  no fluxo comum **após** o handler retornar `True`.

> **Nota de economia de ação/toggle:** desligar manualmente NÃO deve cobrar custo nem
> exigir os recursos de ativação. O `handle_usar_instrumento` cobra custo só quando o
> handler retorna `True`. Portanto o ramo de toggle-off chama `_encerrar_requiem` e
> retorna `False` — mas precisa **não** enviar erro (não é falha). Solução: o handler
> faz o toggle-off e a cobrança/erro é pulada; detalhe fixado no plano (um retorno
> especial ou um flag `_requiem_desativado` para o `handle_usar_instrumento` não tratar
> como erro). Ver plano.

---

## 4. DoT escalonado — `_processar_requiem_turno(m)`

Chamado no **início do turno do monstro** (junto de `_processar_paralisacao_turno` etc.).
Se `m.get("requiem_por")`:
- Acha o bardo; valida Réquiem ativo (bardo vivo, `requiem_alvo == m["id"]`, Violino ainda
  no `off_hand`). Se inválido → limpa `requiem_por` e retorna.
- `bardo["requiem_contador"] = min(bardo["requiem_contador"] + 1, st["teto"])`.
- Save de Vontade do alvo vs `_instrumento_cd(bardo, inst)`:
  - **Falha:** `dano = roll_dice(f"{contador}{st['dado']}")` (ex.: `3d6`); `m["hp"] -= dano`;
    narra; mata via `_monster_dies` (encerra o Réquiem no `_monster_dies`/limpeza).
  - **Sucesso:** sem dano; narra "resiste".

> Escala pelo **contador de ticks** (nº de turnos do alvo sob o Réquiem), com teto — não
> pelo `round_num`, para robustez se o alvo pular turnos.

---

## 5. Aura de provocação — `_requiem_forca_bardo(m)`

Em vez de re-carimbar `provocado` (que tem decremento/expiração próprios), a IA de alvo do
monstro consulta um helper: `_requiem_forca_bardo(m)` retorna o **bardo** a ser atacado
(ou None) se:
- `m` é o alvo do Réquiem (`m.get("requiem_por")` aponta um bardo com Réquiem ativo), **ou**
- existe um bardo com Réquiem ativo e `_distancia_chebyshev(m["pos"], bardo["pos"]) <= 3`.

Integra nos **mesmos pontos** onde o `provocado`/`self.taunted` já força alvo: a resolução
de alvo forçado (~server.py 13339) e os booleanos `forcado` (~14134/14212/14476). Dinâmico
(avaliado quando o monstro escolhe alvo), então cobre monstros que entram no raio 3.

---

## 6. Concentração — `_concentracao_requiem(bardo, dano)`

Chamado sempre que um **bardo** sofre dano. Se `bardo.get("requiem_alvo")` e `dano > 0`:
- Save de Vontade vs **CD 8 + dano** (origem Anã: +2, plumbado — lê `origem_bonus == "concentracao"`; Fase 4 popula).
- **Falha** → `_encerrar_requiem(bardo, "concentração quebrada")`.

**Sites de dano ao bardo** (hook após aplicar o dano):
- `_execute_one_monster_attack` (ataque de monstro — melee/ranged; mesmo site do Ecos).
- `_processar_efeitos_armadilha_turno` (tick de armadilha) e o disparo de armadilha.
- `_processar_venenos_turno` (tick de veneno).
- `_processar_em_chamas_turno` (tick de chamas).

> Cada site chama `await self._concentracao_requiem(p, dano_aplicado)` só quando o alvo do
> dano é um jogador com `requiem_alvo`. Um helper único mantém a regra num lugar só.

---

## 7. Manutenção — `_cobrar_manutencao_requiem(bardo)`

Espelha `_cobrar_manutencao_cancao`. No **início do turno do bardo**:
- Se sem `requiem_alvo`, retorna.
- Se `fome < 2` ou `sede < 2` → `_encerrar_requiem(bardo, "recursos insuficientes")`.
- Senão debita -2🍖/-2💧, reaplica o taunt (garante persistência), narra.

---

## 8. Fim do Réquiem — `_encerrar_requiem(bardo, motivo)`

Helper único que limpa o estado e narra. Limpa `bardo["requiem_alvo"]`,
`bardo["requiem_contador"]`, e no alvo `m.pop("requiem_por")` (se o alvo ainda existe).
Chamado em: alvo morre (`_monster_dies` do alvo do Réquiem), bardo morre (`_player_dies`),
concentração quebra (§6), manutenção sem recursos (§7), desequipar o Violino
(checado no `_processar_requiem_turno`/manutenção via off_hand), recast (§3), desativação
manual (§3). Idempotente.

---

## 9. Cliente (`gameState.js` + `game.js`)

- `acionarInstrumento` (`requiem_final`): se o bardo já tem Réquiem ativo → chama
  `GS.usarInstrumento(null)` (toggle-off, sem alvo); senão abre `openTargetModal` (1 monstro
  no alcance, como Nota Cortante) → `GS.usarInstrumento(alvo)`.
- **Banner de status** em `renderMyPanel` (família dos banners de status já existente):
  "🎻 Réquiem — alvo {nome} — {contador}{dado} (manut. 🍖-2 💧-2)". Lido de
  `me.requiem_alvo`/`me.requiem_contador` + stats do Violino.
- Tooltip já mostra `desc`/stats (Fase 1).
- `game_state` já serializa os campos do jogador crus (`requiem_alvo`/`requiem_contador`
  vão automaticamente) e dos monstros (`requiem_por`).

---

## 10. Testes (`tools/test_instrumentos_bardo.py`)

- **Ativação/toggle:** ativa (grava `requiem_alvo`/`requiem_por`, alcance/LOS validados);
  reativar com Réquiem ativo desliga; recast troca de alvo.
- **DoT:** contador sobe 1→2→3, respeita o teto por qualidade; falha no save = `contador×dado`;
  sucesso = sem dano; alvo morto encerra o Réquiem.
- **Taunt:** `_requiem_forca_bardo` retorna o bardo para o alvo e para um monstro a ≤3;
  None para um monstro a >3 sem ser o alvo.
- **Concentração:** `_concentracao_requiem` falha (CD 8+dano alto) → encerra; passa → segue;
  disparada nos 4 sites (ataque/armadilha/veneno/chamas — ao menos o site de ataque testado
  ponta-a-ponta, os demais via chamada direta do helper).
- **Manutenção:** debita -2/-2 no turno do bardo; sem recursos → encerra.
- **Fim:** desequipar o Violino encerra no próximo tick; bardo morto encerra.
- **Economia de ação:** 2 mãos (atacar OU tocar); o toggle-off não cobra custo nem gasta a
  ação indevidamente.
- Regressão: `test_bardo_espec`, `test_tecnicas_espec`, `test_guilda`, `test_arremessaveis_tatico`
  (provocado/taunt e Cola) seguem verdes.

---

## 11. Fora de escopo (Fases 4–5)

- **Fase 4:** Origens Élfica/Anã (a **Anã** dá +2 na concentração do Réquiem — plumbado
  aqui) + Encantamento Rúnico (Violino Rúnico: alvo sofre -1 em Vontade sob o Réquiem) +
  Lendário + loot procedural.
- **Fase 5:** Improviso/Gaita.

---

## 12. Questões resolvidas

1. Save do alvo — sucesso = sem dano, escalada continua. §4.
2. Teto — por qualidade (3/4/5). §2/§4.
3. Concentração — qualquer dano; 4 sites. §6.
4. Custo — ativação -4/-4 + manutenção -2/-2 por rodada. §2/§7.
5. Taunt — alvo + raio 3 do bardo, reusa `provocado_por`/AI de alvo forçado. §5.
6. Desativação — toggle manual. §3/§9.
