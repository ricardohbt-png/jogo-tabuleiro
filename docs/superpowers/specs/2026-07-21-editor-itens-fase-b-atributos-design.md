# Editor de Itens — Fase B: Motor de bônus de atributo (design)

Data: 2026-07-21
Status: aprovado (aguardando revisão da spec escrita)

## Objetivo

Tornar **funcionais** os bônus de atributo (Força/Destreza/Constituição/Inteligência)
que equipamentos podem conceder. Estende o **motor de multi-efeito** da Fase 2a (a
lista `bonuses:[{effect,value}]` já aplicada por `_apply_single_effect` ao
equipar/desequipar) com quatro novos tipos de efeito — `str_`, `dex`, `con_`, `int_`
— que aplicam um bônus de atributo **bruto** com **cascata** nos derivados,
espelhando o padrão delta que o veneno já usa (`_reduzir_con_temporario`). Assim
qualquer equipamento que declare esses efeitos (armadura/escudo agora; anéis/poções
em fases futuras) funciona sem novo mecanismo por-slot.

## Decisões de brainstorming (fixadas)

1. **Reusar a lista `bonuses`** do motor de multi-efeito (não um campo novo).
2. **Cascata completa**, incluindo a jogada de **ataque (acerto)** — via um mapa
   classe→atributo-de-ataque.
3. **Bônus = pontos de atributo brutos** (ex.: +2 Força), com recomputação do
   modificador (`mod = (score−10)//2`); consistente com o sistema de veneno e com o
   dano lido ao vivo. A não-linearidade do modificador é intencional.
4. **Visão e iniciativa NÃO precisam de delta** — são lidas ao vivo dos atributos
   brutos, então se atualizam sozinhas quando a cascata altera o bruto.

## Contexto do motor (explorado)

- `mod(score) = (score − 10) // 2` (server.py:47). `get_bonus_constituicao(con)` é
  uma tabela D20 (server.py:49) usada para HP/Fortitude.
- **Derivados ARMAZENADOS** (precisam de ajuste por delta ao mudar atributo):
  - `atk_bonus`/`base_atk_bonus` (acerto) — **fixo por classe** (o modificador de
    atributo está embutido no `atk_bonus` inicial da classe; ver os comentários em
    CLASSES: Victor "FOR mod(18)", Pedro "FOR mod(8)", Luccas "DES mod(18)"…).
  - `ac`/`ac_base` (CA = 10 + mod(DES) + armadura), `ref_` (Reflexos = base +
    mod(DES) + nível), `will` (Vontade = base + mod(INT) + nível),
    `fort` (Fortitude = base + get_bonus_constituicao(CON) + nível),
    `max_hp` (CON embutido; delta = Δget_bonus_constituicao × nível).
- **Derivados LIDOS AO VIVO** (automáticos — nada a ajustar, só alterar o bruto):
  - **dano**: `_resolver_dano_ataque_basico` lê `mod(p[arma.stat])` no momento do
    ataque.
  - **visão**: `_get_raio_visao(p)` = `spd + (mod(INT)+mod(DES))//2 + bônus` (lê os
    brutos; docstring confirma que alterações nos atributos afetam a visão sem bônus
    separado).
  - **iniciativa**: `initiative_value` = `DES + mod(INT)`, recomputada em
    `_rebuild_initiative` (lê os brutos; efetiva no próximo rebuild).
- **Padrão delta de referência**: `_reduzir_con_temporario` (server.py:14681) já
  muda `p["con_"]` e ajusta `max_hp` (×nível) e `fort` por delta de
  `get_bonus_constituicao`.

## Componente central — `_apply_attribute_delta(p, attr, delta)`

Um helper único, chamado por `_apply_single_effect` para os efeitos `str_`/`dex`/
`con_`/`int_` (com `delta = value` ao equipar e `−value` ao desequipar). Passos:

1. `antes = p[attr]`; `p[attr] = max(1, antes + delta)`; `depois = p[attr]`.
2. Calcular o delta do modificador: para `con_`, `Δ = get_bonus_constituicao(depois)
   − get_bonus_constituicao(antes)`; para os demais, `Δ = mod(depois) − mod(antes)`.
3. Aplicar aos derivados armazenados:

| Atributo | Ajuste (por Δ) |
|---|---|
| `str_` | `atk_bonus += Δ; base_atk_bonus += Δ` **se** `_CLASS_ATK_ATTR[class_id] == "str_"` |
| `dex`  | `ac += Δ; ac_base += Δ`; `ref_ += Δ`; e `atk_bonus/base_atk_bonus += Δ` **se** a classe ataca por DES |
| `con_` | `max_hp += Δ × p["level"]` (com HP atual ajustado, ver abaixo); `fort += Δ` |
| `int_` | `will += Δ` |

- **HP no CON**: ao equipar (delta>0) e `Δ>0`, `hp = min(max_hp, hp + Δ×level)` — mas
  **suprimir o top-up imediato se `p.get("ultimo_esforco_ativo")`** (mesma trava do
  efeito `maxhp` no `_apply_single_effect`). Ao desequipar, `max_hp` cai e
  `hp = min(hp, max_hp)`. `max_hp` nunca abaixo de 1.
- **Mapa** `_CLASS_ATK_ATTR = {"warrior":"str_","paladin":"str_","cleric":"str_",
  "mage":"str_","rogue":"dex","ranger":"dex","bard":"dex"}` — derivado do atributo
  já embutido no `atk_bonus` de cada classe (o plano deve **verificar** cada classe
  em CLASSES ao implementar).

### Corretude & simetria
Apply e reverse são **inversos exatos** e **independentes de ordem** no resultado
líquido: cada operação calcula `Δmod` a partir do valor bruto real naquele instante,
então empilhar dois itens (+2 FOR cada) e removê-los em qualquer ordem sempre
retorna ao estado inicial (a soma dos Δ telescópica: `Σ(mod(depois_i) −
mod(antes_i)) = mod(final) − mod(inicial)` quando as operações formam uma pilha).
Vale para acerto/CA/saves; para `max_hp` idem (com `×level`).

## Onde pluga

- `_apply_single_effect(self, p, effect, value, equipping)` ganha 4 ramos novos que
  chamam `self._apply_attribute_delta(p, effect, value if equipping else -value)`.
  Nenhuma outra parte do motor de multi-efeito muda — armaduras/escudos (e futuros
  anéis/poções) passam a suportar bônus de atributo automaticamente pela lista
  `bonuses`.

## Validação + editor

- **Servidor**: adicionar `str_`, `dex`, `con_`, `int_` ao `_ITEM_BONUS_EFFECTS`
  (o allowlist de `bonuses` em `_validate_custom_armor`; e o equivalente para armas
  se a lista for compartilhada — verificar). Sem isso a validação descarta os bônus
  de atributo.
- **Cliente**: adicionar as 4 opções ao dropdown de "Bônus adicionais" do formulário
  de armadura/escudo (`editor_items_editor.js`) e ao `BONUS_EFFECTS` de
  `editor_items_logic.js` (para o filtro de `serializeArmor`).

## Testes — `tools/test_editor_itens.py`

Harness `GameRoom` + `make_player` (como as seções [A3]/[A5] da Fase 2a). Um item é
um dict com `bonuses:[{effect,value}]` aplicado via `_apply_gear_effect`.
- **Força** (guerreiro): equipar +2 FOR sobe `atk_bonus` por `Δmod`; desequipar
  reverte exato. Ladino: +2 FOR **não** muda o acerto (classe ataca por DES) mas o
  dano muda ao vivo (verificar via `mod(p["str_"])`).
- **Destreza** (ladino): +2 DES sobe `ac`/`ac_base`, `ref_`, e o acerto; guerreiro:
  +2 DES sobe CA/Reflexos mas **não** o acerto.
- **Constituição**: +2 CON sobe `max_hp` (Δ × nível) e `fort`; HP atual sobe no
  equipar (respeitando a trava do Último Esforço) e cai/clampa no desequipar.
- **Inteligência**: +2 INT sobe `will`.
- **Simetria/empilhamento**: dois itens +2 FOR aplicados e removidos em qualquer
  ordem voltam `atk_bonus`/`str_` ao valor inicial.
- **Ao vivo**: `_get_raio_visao` e `initiative_value` refletem o novo DES/INT (checar
  antes/depois de equipar um item de +DES/+INT, sem chamar helper de cascata para
  eles).

## Fora de escopo

- Fase C (resistências de dano do herói) e Fase D (iniciativa como campo/efeito
  próprio — o efeito automático via DES/INT já entra aqui);
- as outras sub-abas (anéis/botas/poções/arremessáveis/venenos) — mas o motor já
  fica pronto para elas usarem `bonuses` de atributo;
- **nível mudando com o item equipado** (o delta de `max_hp` foi calculado no nível
  L; se subir de nível usando o item, pode dessincronizar) — limitação conhecida e
  aceita, idêntica ao sistema de veneno existente;
- habilidades ativáveis concedidas por item.
