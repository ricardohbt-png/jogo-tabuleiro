# Guilda dos Heróis — Fase 1f: Especializações do Mago (Metamagia)

**Data:** 2026-07-02
**Status:** Design aprovado — pronto para plano de implementação
**Fase:** 1f (Mago) — **última** classe das Especializações. Feito: 1a (Guerreiro),
1b (Clérigo), 1c (Paladino), 1d (Ladino), 1e (Bardo).
**Depende de:** Fase 0 + padrão das Fases 1a-1e (`tem_espec`, entradas
`categoria:"especializacao"` no `GUILD_CATALOG`, `handle_guild_buy`, e o teto de
combinação do Guerreiro como referência de truncamento).

---

## 1. Visão geral

Cobre o **Mago** (Pedro, `class_id:"mage"`) via **Metamagia** — as 3 ações livres
que modificam a magia lançada no turno: 🎯 Aprimorar (+CD do save), ⏱️ Estender
(+duração), 💥 Fortalecer (×dano). As Especializações enfraquecem o baseline e
revendem os upgrades como II/III, incluindo um **cap de empilhamento** (estilo teto
de combinação do Guerreiro).

### Estado atual confirmado no código
- **Metamagia** são toggles (`aprimorar_ativo`/`estender_ativo`/`fortalecer_ativo`),
  ligados por `handle_aprimorar_magia`/`handle_estender_magia`/`handle_fortalecer_magia`
  (→ `_toggle_metamagia`, ~6495-6514).
- **Aplicação** em `handle_magia` (~7897-7921): monta `dmg_mult`/`dur_bonus`/`dc_bonus`:
  ```python
  dmg_mult, dur_bonus, dc_bonus = 1, 0, 0
  if is_mage:
      tem_dano    = self._magia_tem_dano(magia)
      tem_duracao = "duracao" in magia
      tem_save    = "save" in magia
      mm_fome = mm_sede = 0
      partes = []
      if p.get("fortalecer_ativo") and tem_dano:
          dmg_mult = 1.5; mm_fome += 6; mm_sede += 6; partes.append("Fortalecer (dano ×1,5)")
      if p.get("estender_ativo") and tem_duracao:
          dur_bonus = 1; mm_fome += 3; mm_sede += 3; partes.append("Estender (+1 turno)")
      if p.get("aprimorar_ativo") and tem_save:
          dc_bonus = 1; mm_fome += 3; partes.append("Aprimorar (+1 CD)")
      # cobra mm_fome/mm_sede, valida recursos, gm_say
  ```
  Hoje as 3 empilham livremente; cada uma cobra o próprio custo (🍖-6💧-6 / 🍖-3💧-3 / 🍖-3).
- **Teto de combinação do Guerreiro** (referência): em `handle_attack`, `sel = sel[:teto]`
  trunca as habilidades armadas ao `_teto_combinacao(p)` — mesmo padrão a espelhar.
- **Metamagia gravada em pergaminho** (`gerar_pergaminho`/`preview_pergaminho`,
  ~3507-3520): usa +1 CD / ×1,5 dano / +duração fixos com bump de preço próprio.
  **FORA DE ESCOPO** — não muda.

---

## 2. Decisões de design (fechadas)

| Tema | Decisão |
|---|---|
| Escopo | Só a Metamagia (não mexe nas magias em si nem em slots). |
| Baseline enfraquecido | (a) **Empilhamento** ilimitado → **1 metamagia por lançamento**; (b) **Fortalecer** ×1,5 → **×1,25**. Aprimorar (+1 CD) e Estender (+1 rodada) mantêm a base. |
| Tecelagem Arcana | Empilhar 2 (II) / 3 (III). |
| Fortalecer | ×1,25 (base) → ×1,5 (II) → ×2 (III). |
| Aprimorar | +1 (base) → +2 (II) → +3 (III) de CD. |
| Estender | +1 (base) → +2 (II) → +3 (III) rodadas. |
| Preços (escalonado por poder) | Fortalecer 200/250; Aprimorar 150/200; Estender 150/200; Tecelagem 150/300. III exige II em todas. |
| Custo de uso | Ouro é o custo das compras; os custos 🍖/💧 de cada metamagia ficam como estão. |
| Truncamento | Ordem fixa de prioridade: **Fortalecer → Estender → Aprimorar**; aplica só as `_teto_metamagia(p)` primeiras (armadas E aplicáveis à magia); as excedentes não aplicam nem cobram. |
| Autoridade | Servidor autoritativo. |

---

## 3. Catálogo (`GUILD_CATALOG`, server.py) — 8 nós literais

Todos com `categoria:"especializacao"`, `classe:"mage"`, `exclusiva:False`.

```python
"mago_tecelagem_2":  {... "linha":"mago_tecelagem","nivel":2,"requer":None,"preco":150,
    "nome":"Tecelagem Arcana II","icon":"🧵","desc":"Permite empilhar 2 metamagias no mesmo lançamento." },
"mago_tecelagem_3":  {... "linha":"mago_tecelagem","nivel":3,"requer":"mago_tecelagem_2","preco":300,
    "nome":"Tecelagem Arcana III","icon":"🧵","desc":"Permite empilhar as 3 metamagias no mesmo lançamento." },
"mago_fortalecer_2": {... "linha":"mago_fortalecer","nivel":2,"requer":None,"preco":200,
    "nome":"Fortalecer II","icon":"💥","desc":"Fortalecer Magia multiplica o dano por 1,5 (era ×1,25)." },
"mago_fortalecer_3": {... "linha":"mago_fortalecer","nivel":3,"requer":"mago_fortalecer_2","preco":250,
    "nome":"Fortalecer III","icon":"💥","desc":"Fortalecer Magia multiplica o dano por 2." },
"mago_aprimorar_2":  {... "linha":"mago_aprimorar","nivel":2,"requer":None,"preco":150,
    "nome":"Aprimorar II","icon":"🎯","desc":"Aprimorar Magia dá +2 na CD do save (era +1)." },
"mago_aprimorar_3":  {... "linha":"mago_aprimorar","nivel":3,"requer":"mago_aprimorar_2","preco":200,
    "nome":"Aprimorar III","icon":"🎯","desc":"Aprimorar Magia dá +3 na CD do save." },
"mago_estender_2":   {... "linha":"mago_estender","nivel":2,"requer":None,"preco":150,
    "nome":"Estender II","icon":"⏱️","desc":"Estender Magia dá +2 rodadas de duração (era +1)." },
"mago_estender_3":   {... "linha":"mago_estender","nivel":3,"requer":"mago_estender_2","preco":200,
    "nome":"Estender III","icon":"⏱️","desc":"Estender Magia dá +3 rodadas de duração." },
```

---

## 4. Gating no servidor (helpers + `handle_magia`)

Helpers como métodos de `GameRoom`, perto de `_teto_combinacao`.

```python
    def _teto_metamagia(self, p):
        """Quantas metamagias podem empilhar no mesmo lançamento (base 1)."""
        if tem_espec(p, "mago_tecelagem_3"): return 3
        if tem_espec(p, "mago_tecelagem_2"): return 2
        return 1

    def _fortalecer_mult(self, p):
        if tem_espec(p, "mago_fortalecer_3"): return 2.0
        if tem_espec(p, "mago_fortalecer_2"): return 1.5
        return 1.25

    def _aprimorar_bonus(self, p):
        if tem_espec(p, "mago_aprimorar_3"): return 3
        if tem_espec(p, "mago_aprimorar_2"): return 2
        return 1

    def _estender_bonus(self, p):
        if tem_espec(p, "mago_estender_3"): return 3
        if tem_espec(p, "mago_estender_2"): return 2
        return 1
```

**Reescrita do bloco de metamagia em `handle_magia`** (~7900-7921) — junta as
metamagias aplicáveis numa lista ordenada por prioridade, trunca ao teto, e só então
cobra/aplica:

```python
        dmg_mult, dur_bonus, dc_bonus = 1, 0, 0
        if is_mage:
            tem_dano    = self._magia_tem_dano(magia)
            tem_duracao = "duracao" in magia
            tem_save    = "save" in magia
            # candidatas: (kind, custo_fome, custo_sede) — só metamagias armadas E aplicáveis
            candidatas = []
            if p.get("fortalecer_ativo") and tem_dano:
                candidatas.append(("fortalecer", 6, 6))
            if p.get("estender_ativo") and tem_duracao:
                candidatas.append(("estender", 3, 3))
            if p.get("aprimorar_ativo") and tem_save:
                candidatas.append(("aprimorar", 3, 0))
            teto = self._teto_metamagia(p)
            aplicadas = candidatas[:teto]          # ordem: Fortalecer > Estender > Aprimorar
            mm_fome = mm_sede = 0
            partes = []
            for kind, cf, cs in aplicadas:
                if kind == "fortalecer":
                    dmg_mult = self._fortalecer_mult(p); mm_fome += cf; mm_sede += cs
                    partes.append(f"Fortalecer (dano ×{dmg_mult:g})")
                elif kind == "estender":
                    dur_bonus = self._estender_bonus(p); mm_fome += cf; mm_sede += cs
                    partes.append(f"Estender (+{dur_bonus} turno{'s' if dur_bonus != 1 else ''})")
                elif kind == "aprimorar":
                    dc_bonus = self._aprimorar_bonus(p); mm_fome += cf; mm_sede += cs
                    partes.append(f"Aprimorar (+{dc_bonus} CD)")
            if len(candidatas) > teto:
                await self.gm_say(f"🧵 **{p['name']}** só pode empilhar {teto} metamagia(s) por lançamento — as demais foram ignoradas.")
            if (mm_fome or mm_sede):
                if p["fome"] < mm_fome or p["sede"] < mm_sede:
                    await self.send_to(pid, {"type": "error",
                        "msg": f"Recursos insuficientes p/ metamagia 🍖-{mm_fome} 💧-{mm_sede}."}); return
                p["fome"] = max(0, p["fome"] - mm_fome)
                p["sede"] = max(0, p["sede"] - mm_sede)
            if partes:
                custo_txt = (f" | 🍖-{mm_fome}" + (f" 💧-{mm_sede}" if mm_sede else "")) if (mm_fome or mm_sede) else ""
                await self.gm_say(f"🔮 **{p['name']}** — metamagia: {', '.join(partes)}{custo_txt}.")
```

> **Nota de fidelidade:** o comportamento anterior era `dmg_mult=1.5`, `dur_bonus=1`,
> `dc_bonus=1`, sem teto. A reescrita preserva a semântica "cobra só se aplicável" e
> "custo pago agora", mudando apenas: baseline (×1,25, teto 1) e as magnitudes via
> helpers. `dmg_mult` continua float aplicado ao dano; `dur_bonus`/`dc_bonus` ints.

> **Isolamento do pergaminho:** o caminho de metamagia gravada em pergaminho
> (`gerar_pergaminho`, ~3507-3520) **não** chama esses helpers — permanece +1/×1,5/+1
> com o bump de preço atual. Não tocar.

---

## 5. Cliente (`game.js` + `gameState.js`)

Getters em `gameState.js` (lidos da posse; caem para o player do `game_state`):
`magoTecelagemCap()` (1/2/3), `magoFortalecerMult()` (1.25/1.5/2.0),
`magoAprimorarBonus()` (1/2/3), `magoEstenderBonus()` (1/2/3).
- **Botões de metamagia** (Aprimorar/Estender/Fortalecer no HUD do Pedro): a descrição
  reflete a magnitude possuída (ex.: "dano ×2", "+3 CD") e o **teto de empilhamento**
  atual (ex.: "empilha até 2"). Texto informativo; o servidor é autoritativo.

> Robustez na masmorra: `guildOwnedOf` já cai para o player do `game_state`.

---

## 6. Testes (`tools/test_mago_espec.py`)

Harness do projeto; helper `mage(**owned)`. Cobrir:
1. **Helpers:** `_teto_metamagia` = 1/2/3; `_fortalecer_mult` = 1.25/1.5/2.0;
   `_aprimorar_bonus` = 1/2/3; `_estender_bonus` = 1/2/3 conforme posse.
2. **Truncamento:** com as 3 metamagias armadas numa magia que tem dano+duração+save,
   com teto 1 aplica só Fortalecer (e cobra só 🍖-6💧-6); com teto 2 aplica Fortalecer+Estender;
   com teto 3 aplica as três. Verifica `dmg_mult`/`dur_bonus`/`dc_bonus` e o débito de 🍖/💧
   resultantes (via `handle_magia` numa magia real, ex.: `bola_fogo`/`raio_congelante`).
3. **Magnitude:** Fortalecer III → `dmg_mult` 2.0; Aprimorar III → `dc_bonus` 3; Estender III → `dur_bonus` 3.
4. **Compra:** `mago_tecelagem_3` recusado sem `_2` (idem para as outras linhas).

---

## 7. Fronteiras (NÃO fazer)

- Magias em si (dano base, alcance, área) — inalteradas.
- Economia de slots (`SLOTS_POR_NIVEL`, regen) — inalterada.
- Metamagia gravada em **pergaminho** — inalterada (fixo +1/×1,5/+1 + preço atual).
- Sem capstone "Suprema"; sem catálogo gerado (metamagia é conjunto fixo de 3).

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Reescrita do bloco de metamagia quebrar a semântica de custo/aplicabilidade | Preserva "cobra só se aplicável" e "custo agora"; testes dirigem `handle_magia` com magias reais e conferem `dmg_mult`/`dur_bonus`/`dc_bonus` + débito. |
| Ordem de truncamento arbitrária confundir o jogador | Ordem fixa documentada (Fortalecer > Estender > Aprimorar) + `gm_say` avisando quando excede o teto. |
| `dmg_mult` ×1,25 gerar dano fracionário inesperado | Já é float aplicado ao dano como hoje (×1,5); o arredondamento segue o mesmo caminho existente. |
| Afetar pergaminhos por engano | Helpers só entram em `handle_magia` (lançamento ao vivo); o caminho de pergaminho não os chama. Teste garante `dmg_mult` do pergaminho inalterado se houver cobertura; senão, revisão de diff. |
| Baseline nerf (×1,25 + teto 1) surpreender o usuário em jogo | É a mudança de gameplay aprovada, documentada na CLAUDE.md como nas fases 1a-1e. |
