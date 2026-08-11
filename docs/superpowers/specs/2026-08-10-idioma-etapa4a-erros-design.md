# Etapa 4a do idioma — Mensagens de erro do servidor — Design

**Data:** 2026-08-10
**Depende de:** etapas 1 (motor PT/EN), 2 (vocabulário) e 3 (alcance + descrições), todas
implementadas e verificadas. Specs em `docs/superpowers/specs/2026-08-10-idioma-*`.

---

## Onde isto se encaixa

A tradução foi decomposta em cinco sub-projetos. O quarto — texto do servidor — tem ~1.000
pontos de edição e foi dividido em dois:

1. Motor PT/EN ✅
2. Vocabulário — 397 nomes ✅
3. Alcance dos nomes + 189 descrições ✅
4. **a) Erros (462 ocorrências)** ← este · b) Narração (544)
5. Interface do cliente (~1.000)

**Erros antes da narração** porque é o lote mais seguro para assentar o método: 382 das 462
ocorrências não têm parâmetro nenhum, são curtas (37 caracteres em média), e cada uma é uma
recusa isolada — errar uma não corrompe uma frase longa nem uma sequência de combate.

## A superfície, medida

| | Ocorrências | Observação |
|---|---:|---|
| `"msg": "texto fixo"` | 382 | **298 textos distintos** — há repetição pesada |
| `"msg": f"texto {com} parâmetro"` | 80 | exigem escolher o nome de cada parâmetro |
| **Total** | **462** | |

A repetição é o dado que muda o desenho: "Alvo inválido." aparece **18 vezes**, "Ação
principal já usada neste turno." **12 vezes**, "Aliado inválido." **10 vezes**. Deduplicar
não é só economia de chaves — garante que a mesma recusa saia sempre com a mesma frase em
inglês, o que hoje não é garantido nem em português.

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Nome da chave | Slug derivado do texto em português (`erro.alvo_invalido`) |
| Dedup | Por construção: mesmo texto → mesmo slug |
| Migração dos 382 de texto fixo | Script determinístico, diff conferível |
| Migração dos 80 com parâmetro | À mão |
| Onde mora o dicionário | Arquivo novo `src/lang/erros.js`, mantido à mão |

---

## Arquitetura

### Chaves derivadas do texto

`erro.<slug>`, onde o slug vem do texto em português: sem acentos, minúsculas, não-alfanumérico
vira `_`, truncado em 40 caracteres.

```
"Alvo inválido."                        → erro.alvo_invalido
"Ação principal já usada neste turno."  → erro.acao_principal_ja_usada_neste_turno
```

A dedup cai de graça: dois sites com o mesmo texto geram o mesmo slug e compartilham a chave.
Colisão depois do truncamento (dois textos longos diferentes com o mesmo prefixo) ganha sufixo
numérico, e o script **relata** cada uma para revisão humana — nunca resolve em silêncio.

### Migração em duas velocidades

**Os 382 de texto fixo, por script.** Um script varre `server.py`, e para cada literal
`"msg": "…"` gera o slug, reescreve a chamada para `"msg": T("erro.…")` e acumula a entrada
do dicionário. É uma substituição de literal exato, determinística e reversível; o diff mostra
uma linha alterada por site e pode ser lido em bloco.

**Os 80 com parâmetro, à mão.** Cada um exige decidir o nome do parâmetro
(`f"Requer antes: {nome_req}."` → `T("erro.requer_antes", requer=nome_req)`), e alguns
carregam expressão em vez de variável (`{CLASSES[cls_id]['name']}`). É exatamente onde um
script erraria em silêncio, produzindo um parâmetro com nome sem sentido ou perdendo a
expressão. São 80 — cabe na mão.

### Onde o dicionário mora

Arquivo novo `src/lang/erros.js`, declarando `window.LANG_ERROS` e fundindo em
`window.LANG_STRINGS`, no mesmo formato dos dois que já existem. O carregador do servidor já
funde **todos** os `.js` de `src/lang/` (etapa 3), e o `index.html` ganha uma tag `<script>`.

Separar mantém o `strings.js` (interface, à mão) e o `catalogo.js` (gerado) intocados, e deixa
este lote revisável sozinho.

**Diferente do catálogo, aqui não fica um gerador rodando.** Depois da migração, o
`server.py` não contém mais o texto em português — só a chave. Não há de onde derivar de
novo, e o arquivo passa a ser mantido à mão, como o `strings.js`. O script de migração é de
uso único.

## Testes

Dois destes são novos e valem além desta etapa.

`tools/test_erros.py`:

1. **Nenhum literal `"msg": "…"` sobrou no `server.py`.** É a prova de migração completa —
   e falha alto se alguém acrescentar uma mensagem crua depois.
2. **Toda chave `T("erro.…")` usada no `server.py` existe no dicionário.** A varredura
   estática que já existe em `tools/test_vocabulario.py` cobre isso para todo `T(`; aqui ela
   é reafirmada para o prefixo `erro.`.
3. **Chave do `erros.js` não usada em lugar nenhum é relatada** (não falha — um texto pode
   ser reintroduzido depois; mas o relatório evita o arquivo virar depósito).
4. **Paridade de parâmetros entre `pt` e `en`**, em TODAS as chaves de TODOS os arquivos de
   idioma. Verificado agora nas 630 chaves atuais: nenhuma divergente. Como teste permanente,
   protege as 80 desta etapa e as 399 da narração — é a falha mais provável numa tradução em
   lote, e a mais visível para o jogador (o `{nome}` aparece cru na tela).
5. Um erro migrado chega traduzido a quem está em inglês e em português a quem está em
   português, pelo `send_to` real — o mesmo teste ponta a ponta das etapas anteriores,
   aplicado a uma mensagem deste lote.

## Fora de escopo

- A **narração** (544) — etapa 4b.
- A interface do cliente — etapa 5.
- Mensagens de erro que o cliente gera sozinho (toasts locais) — etapa 5.
- Rever o **conteúdo** das mensagens. Se uma recusa é confusa em português, ela continua
  confusa; melhorar texto é trabalho de design, não de tradução.

## Tradução

Entre 298 e 378 chaves curtas — 298 vêm do texto fixo já deduplicado, e as parametrizadas
somam no máximo 80, provavelmente menos porque também se repetem. O número exato sai do
script de migração; não o crave em teste (a lição da etapa 3).

As exigências:

- **Registro consistente.** São recusas do sistema ao jogador. Direto e impessoal:
  "Not your turn.", não "It appears it may not be your turn right now."
- **Termos do glossário** já fixado nas etapas 2 e 3: ação principal = main action, ação
  bônus = bonus action, recarga = cooldown, alcance = range, 🍖 fome = hunger, 💧 sede =
  thirst, e os nomes de habilidade conforme o `"en"` das chaves `.nome`.
- **Emojis e marcação sobrevivem.** Várias mensagens começam com emoji (🗿, ⚔️) e usam
  `**negrito**`; isso é formatação, não texto, e passa intacto.
