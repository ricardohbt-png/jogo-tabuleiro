# Opção de Idioma + motor de tradução (PT/EN) — Design

**Data:** 2026-08-10
**Etapa:** 1 de 2. Esta etapa entrega a opção no menu, o motor de tradução e uma
amostra traduzida ponta a ponta. A tradução em massa (~1.000 frases do servidor +
a interface do cliente) é a etapa seguinte, e usa o motor definido aqui.

---

## Problema

O jogo é inteiramente em português. Queremos uma opção **Idioma** no menu geral
(painel ⚙️) que troque o idioma do jogo, e uma base sobre a qual a tradução para
inglês possa ser feita depois, em lotes, sem deixar o jogo quebrado no meio.

O que torna isso não-trivial: **metade do texto que o jogador lê é gerado no
servidor**. `server.py` tem ~546 chamadas de narração (`gm_say`) e ~470 mensagens
de erro, além dos nomes de itens, monstros, habilidades e classes. Trocar o
idioma não é uma questão só de cliente.

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Escopo desta etapa | Menu + motor + amostra pequena traduzida |
| Alcance | **Idioma por jogador** — dois jogadores na mesma sala podem estar em idiomas diferentes |
| Conteúdo autoral (masmorras, campanhas, falas de NPC, história, itens/monstros custom) | **Fora de escopo.** Só texto de sistema (código do cliente e do servidor). Aparece no idioma em que foi escrito. |
| Quem traduz o texto do servidor | O **servidor**, por conexão, com fallback para português |
| Idioma padrão na primeira visita | Português, sempre |

Justificativa das duas mais relevantes:

- **Idioma por jogador** (e não um idioma por sala) porque a opção vive num
  painel que já é por navegador, e porque um idioma único de sala deixaria de
  fora quem não fala aquele idioma — a opção só funcionaria para o anfitrião.
- **Servidor traduz** (e não "servidor manda chave, cliente traduz") porque
  permite migração incremental: uma frase migrada é uma frase envolvida em
  `T(...)`; frase não migrada continua saindo em português. A alternativa exigiria
  mudar o protocolo em ~1.000 pontos de uma vez, sem meio-termo.

## Fora de escopo

- Traduzir o conteúdo criado no editor (JSON de masmorras, campanhas, cenas,
  itens e monstros personalizados). O motor não lê `{pt, en}` de JSON autoral.
- Traduzir a interface dos editores (`tools/editor*.html|js`).
- Traduzir em massa. Esta etapa entrega a amostra listada abaixo; o resto é a
  etapa 2.
- Detecção automática de idioma pelo navegador.

---

## Arquitetura

### Dicionário: um arquivo, os dois idiomas

Fonte única em `src/lang/strings.js` (dentro de `src/` porque a allow-list de arquivos estáticos do servidor é `("src", "assets")` — uma pasta `lang/` na raiz daria 404 no navegador):

```js
window.LANG_STRINGS = {
  "ui.menu.idioma":  { pt: "Idioma", en: "Language" },
  "narracao.acerto": { pt: "{nome} acertou {dano} de dano!",
                       en: "{nome} hit for {dano} damage!" },
};
```

- O **cliente** carrega por `<script>` em `index.html`, antes de `game.js`.
  Síncrono: não há um instante de português antes do inglês, e não depende de
  `fetch` (que falharia se a página fosse aberta por `file://`).
- O **servidor** lê o mesmo arquivo em disco, remove o prefixo
  `window.LANG_STRINGS =` e o `;` final, e faz `json.loads` do miolo. É o mesmo
  padrão que `tools/editor_catalog.js` já usa hoje, lido do Python pelo teste
  `[J6]` de `tools/test_editor_itens.py`.

Consequência do formato: os dois idiomas ficam na mesma linha, o que torna a
tradução da etapa 2 revisável, e torna impossível o dicionário do cliente
divergir do dicionário do servidor.

Dividir em vários arquivos por assunto depois é barato: o servidor lê e funde
todos os `.js` da pasta `src/lang/`, e o cliente ganha uma tag `<script>` a mais em
`index.html` (cada arquivo acrescenta as suas chaves a `window.LANG_STRINGS`).
Começamos com um arquivo só.

**Parâmetros** são marcados com `{nome}` no texto e substituídos por nome (não
por posição), nos dois lados.

### Cliente

Respeitando a separação estrita do CLAUDE.md (lógica sem DOM × renderização):

| Arquivo | Responsabilidade |
|---|---|
| `src/lang/strings.js` | Dados: o dicionário. |
| `src/i18n.js` (novo) | Motor **puro**: `I18N.lang`, `I18N.t(chave, params)`, `I18N.setLang(código)`, `I18N.on(fn)`. **Zero** referência a `document`. |
| `game.js` | Aplica no DOM (`_i18nApply(root)`), monta o seletor no painel ⚙️ e re-renderiza a tela ativa ao trocar. |

### Servidor

O núcleo é um objeto `T` que representa "texto ainda não traduzido":

```python
await self.gm_say(T("narracao.acerto", nome=p["name"], dano=dano))
await self.send_to(pid, {"type": "error", "msg": T("erro.nao_e_seu_turno")})
```

As mensagens continuam saindo pelos mesmos caminhos de hoje. A tradução acontece
**num lugar só**: `broadcast()` e `send_to()` serializam o payload com um encoder
que resolve cada `T` no idioma daquele jogador. Como `json.dumps` já percorre a
mensagem inteira, o custo extra é desprezível.

`broadcast()` agrupa as conexões por idioma e faz um `json.dumps` por idioma
presente na sala (com duas pessoas em inglês, um só). Isso cobre de graça o
`gm_log`, que viaja dentro do payload de `game_state` e passa a guardar objetos
`T` em vez de strings.

**Regra de migração:** string crua continua string crua e sai em português para
todos. Migrar uma frase é envolvê-la em `T(...)` e acrescentar a chave ao
dicionário. Não há passo intermediário quebrado.

### Protocolo

Uma mensagem nova, cliente → servidor:

| Mensagem | Campos |
|---|---|
| `set_lang` | `lang` (`"pt"` \| `"en"`) — enviada ao conectar e a cada troca no menu. |

O servidor guarda num dicionário `LANG_BY_PID` de **módulo**, não em
`self.players` nem na sala. Duas razões: o Mestre é extraído de `players` no
`start_game` e ficaria sem idioma; e o `pid` vem de `new_id()`, um contador
global, portanto é único entre todas as conexões. Guardar fora da sala faz o
idioma valer **antes** de entrar em qualquer sala e dispensa plumbing nos quatro
caminhos de entrada (`create_room`, `join_room`, `rejoin`, `join_test_dungeon`).
A entrada é removida no `finally` do `handler`, junto da limpeza que já existe.

Ao receber `set_lang`, o servidor reenvia o estado àquele jogador, então o log de
narração já impresso reaparece retraduzido na hora.

---

## Interface

Uma linha nova no painel ⚙️ (`_audioPanelEnsure`, `game.js:14920`), acima dos
sliders de áudio:

```
🌐 Idioma   [ Português ▾ ]
```

Um `<select>` com Português / English. Escolher aplica imediatamente:

1. `I18N.setLang(código)`
2. salva em `localStorage` na chave `lfh_lang` (espelhando `lfh_audio`)
3. `_i18nApply(document.body)` retraduz o DOM
4. envia `set_lang` ao servidor, se conectado — o reenvio de estado que o
   servidor dispara em resposta cai no caminho normal de render (`GS.on('gameState')`),
   então a tela se redesenha traduzida sem nenhuma função de re-render nova

Sem recarregar a página e sem diálogo de confirmação.

## Como um texto vira traduzível

**HTML estático** (o template dentro de `game.js`) — por atributo:

```html
<h2 data-i18n="ui.connect.titulo">Entrar na Aventura</h2>
<input data-i18n-ph="ui.connect.nome_ph" placeholder="Ex: Thorin">
<button data-i18n-title="ui.menu.audio_title" title="Áudio">⚙️</button>
```

`_i18nApply(root)` varre `[data-i18n]`, `[data-i18n-ph]` e `[data-i18n-title]` e
troca `textContent`, `placeholder` e `title`. O português continua escrito no
código, o que mantém o arquivo legível.

**Texto montado em JS** — por chamada: `t('ui.hud.atacar')` no lugar da string
literal.

**Servidor** — por `T(...)`, como descrito acima.

## Amostra desta etapa

Pequena de propósito, escolhida para exercitar todos os caminhos:

| Alvo | Caminho que prova |
|---|---|
| Painel ⚙️ inteiro, incluindo a linha nova | HTML estático + JS do cliente |
| Tela inicial (`screen-connect`) | HTML estático |
| Tela Meus Jogos (`screen-savegames`) | HTML estático + JS do cliente |
| **Uma** narração do mestre | `T` → `gm_say` → `broadcast` por idioma |
| **Uma** mensagem de erro | `T` → `send_to` por idioma |

As duas últimas são as que importam: com elas dá para pôr dois jogadores na mesma
sala, um em cada idioma, e ver a mesma narração chegar traduzida para cada um.

## Erros e casos-limite

| Situação | Comportamento |
|---|---|
| Chave existe, falta o `en` | Cai no português. É o que sustenta a migração em lotes. |
| Chave não existe no dicionário | Devolve a própria chave e avisa no console. Aparece na tela, mas nada quebra. |
| Jogador nunca mandou `set_lang` (cliente antigo, Mestre reconectando) | Tratado como português. |
| Entradas antigas do `gm_log` (strings cruas) | Continuam em português para todos. |
| Reconexão (`rejoin`) | O cliente reenvia `set_lang` ao conectar, sempre. |
| Troca de idioma no meio da partida | Aplica na hora; o `push_state` disparado pelo `set_lang` retraduz o log. |
| `src/lang/strings.js` ausente ou ilegível no servidor | O servidor sobe e todo `T` resolve para a chave; registra o erro no log de boot. Não impede jogar. |

## Testes

Seguindo a convenção `tools/test_*.py` do projeto.

`tools/test_idioma.py`:

1. O servidor consegue ler e parsear `src/lang/strings.js`.
2. `t()` devolve inglês quando existe e cai no português quando falta o `en`.
3. `T` com parâmetros formata corretamente nos dois idiomas.
4. **Dois jogadores com idiomas diferentes recebem a mesma narração, cada um no
   seu idioma** — o teste que vale por todos.
5. Jogador sem `set_lang` recebe português.
6. Varredura estática: toda chave usada em `T(...)` no `server.py` existe no
   dicionário.

`tools/test_idioma_cliente.js` (node, como `tools/test_editor_items_logic.js`):

1. Motor `t()`: acerto, fallback e chave inexistente.
2. Substituição de parâmetros por nome.
3. Toda chave `data-i18n*` do template de `game.js` existe no dicionário.

## Etapa 2 (contexto, não escopo)

Com o motor no lugar, a tradução vira trabalho de lote e revisão: envolver as
frases do `server.py` em `T(...)`, marcar o HTML do `game.js` com `data-i18n`,
trocar as strings de JS por `t()`, e preencher a coluna `en` do dicionário. A
varredura estática do teste 6 e a do teste 3 dizem, a qualquer momento, o que
ainda falta.
