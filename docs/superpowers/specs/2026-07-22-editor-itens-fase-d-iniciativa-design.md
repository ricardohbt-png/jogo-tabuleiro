# Editor de Itens — Fase D: Bônus de iniciativa (design)

Data: 2026-07-22
Status: aprovado (aguardando revisão da spec escrita)

## Objetivo

Permitir que equipamentos concedam um **bônus fixo de iniciativa** ao herói,
independente de atributo. É um efeito **escalar puro** que encaixa no motor de
multi-efeito exatamente como `spd`/`maxhp` — o mais simples das fases B/C/D. Fecha o
trio B (atributos) / C (resistências) / D (iniciativa).

## Decisões de brainstorming (fixadas)

1. Efeito escalar `initiative` (campo `p["initiative_bonus"]`, lido em
   `initiative_value`).
2. Valor pode ser **negativo** (ex.: armadura pesada −2), como `spd`.

## Contexto do motor (verificado)

- `initiative_value(entity) = _initiative_attribute(entity,"dex") +
  mod(_initiative_attribute(entity,"int_"))` (server.py:7419). Recomputada em
  `_rebuild_initiative` (entrada da masmorra, reforços). O bônus via DES/INT já entra
  sozinho (Fase B muda o atributo bruto).
- Motor de multi-efeito: `_apply_single_effect(self, p, effect, value, equipping)`
  computa `v = value * (1 if equipping else -1)` e trata `atk`/`def_`/`maxhp`/`spd`/
  `bagslots`/`str_`/`dex`/`con_`/`int_`. `_apply_gear_effect` chama-o p/ o primário +
  cada `bonuses` (efeitos escalares; `resist` é roteado à parte).
- `_ITEM_BONUS_EFFECTS = {"def_","maxhp","spd","str_","dex","con_","int_","resist"}`
  (validação de `bonuses`). Cliente: `BONUS_EFFECTS` (editor_items_logic.js) + dropdown
  `.ie-abonus-eff` no editor.

## Componentes

### 1. Servidor — efeito escalar `initiative`
- Em `_apply_single_effect`, ramo novo (junto de `spd`):
  ```python
      elif e == "initiative":
          p["initiative_bonus"] = p.get("initiative_bonus", 0) + v
  ```
  (`v` já é o delta com sinal; simétrico ao equipar/desequipar; empilha naturalmente.)
- `initiative_value` passa a somar o campo:
  ```python
      def initiative_value(self, entity):
          return (self._initiative_attribute(entity, "dex")
                  + mod(self._initiative_attribute(entity, "int_"))
                  + int(entity.get("initiative_bonus", 0) or 0))
  ```
  (Não colide com `_initiative_attribute`, que só recebe `dex`/`int_`.)

### 2. Servidor — validação
- Adicionar `"initiative"` a `_ITEM_BONUS_EFFECTS` (entra como bônus escalar
  `{effect,value}`, sem tratamento especial).

### 3. Cliente
- `BONUS_EFFECTS` (editor_items_logic.js) ganha `"initiative"` (o `.map` escalar já
  cobre — só entradas `resist` têm caminho especial).
- O `.ie-abonus-eff` do editor (`editor_items_editor.js`) ganha
  `<option value="initiative">Iniciativa</option>`.

### 4. Testes
`tools/test_editor_itens.py`:
- equipar item com `{effect:"initiative",value:3}` → `initiative_value(p)` sobe 3;
  desequipar reverte; empilhar dois → +6, remover um → +3;
- valor negativo (−2) reduz;
- validação: `bonuses` com `initiative` preservado como `{effect,value}`.

`tools/test_editor_items_logic.js` (node): `serializeArmor` mantém o bônus
`initiative` (cai no caminho escalar).

## Fora de escopo

- Iniciativa recomputada ao vivo mid-encontro (o bônus vale no próximo
  `_rebuild_initiative`, por encontro — igual ao efeito de atributo da Fase B; limitação
  conhecida e aceita);
- as outras sub-abas (anéis/botas/poções/arremessáveis/venenos) — o motor já fica pronto.
