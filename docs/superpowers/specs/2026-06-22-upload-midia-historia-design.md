# Upload de mídia da história (imagens/áudio) via WebSocket

**Data:** 2026-06-22
**Status:** Design aprovado — pronto para plano de implementação

## Problema

No editor de campanhas, ao adicionar uma imagem e uma música a um slide de
história (abertura/final de campanha ou de fase), tudo funciona na
pré-visualização do editor, mas **não aparece quando o jogo roda**.

### Causa raiz

O editor é uma página de browser. Quando o usuário escolhe um arquivo:

- guarda um **blob temporário em memória** (`s._url` / `st._audioUrl` =
  `URL.createObjectURL(f)`) — é o que a pré-visualização usa;
- grava no JSON apenas o **caminho** `assets/story/<nome-do-arquivo>`
  (`s.image` / `st.audio`).

O arquivo em si **nunca é copiado** para `assets/story/`. A pré-visualização
funciona porque usa o blob (`s._url || s.image`); o jogo carrega pelo caminho
real e recebe **404**, pois a pasta `assets/story/` está vazia (só `.gitkeep`).

Referências no código atual:
- Editor escolhe imagem: `tools/editor_campaign.js:168`
- Editor escolhe áudio: `tools/editor_campaign.js:137`
- Pré-visualização usa blob primeiro: `tools/editor_campaign.js:297` e `:310`
- Editor salva via download de blob (sem servidor): `tools/editor_campaign.js:267`

## Restrição técnica decisiva

Um endpoint HTTP `POST` clássico **não é viável**. Na versão `websockets 16.0`
o hook `process_request(connection, request)` que serve os arquivos estáticos
(`server.py:12674`) só expõe `request.path` e `request.headers` — **o corpo da
requisição não é acessível**. Portanto os bytes do arquivo precisam trafegar
pelo **WebSocket** (mesmo canal do jogo). Isso funciona mesmo com o editor
aberto como `file://`, pois conexões `ws://` não sofrem a mesma política de
mesma-origem.

## Decisões (confirmadas com o usuário)

- **Momento do upload:** ao escolher o arquivo (imediato), não ao salvar.
- **Conflito de nome:** sobrescrever o arquivo existente.
- **Servidor rodando:** requisito aceito — o editor avisa se não conectar.
- **Limite por arquivo:** 25 MB (validado por upload isolado; não há teto
  somado por campanha/masmorra).

## Visão geral do fluxo

1. Usuário escolhe imagem/áudio no editor de história.
2. Editor abre (ou reaproveita) `ws://localhost:8765`, envia o arquivo em
   base64 numa mensagem `upload_story`.
3. Servidor valida, decodifica e grava em `assets/story/<nome>` (sobrescreve).
4. Servidor responde `upload_result` (ok/erro); o editor mostra ✓ / ✗ no card.
5. O JSON salvo continua guardando só o caminho `assets/story/<nome>` — formato
   inalterado. O jogo passa a encontrar o arquivo no lugar certo.

## Protocolo (novo)

### Client → Server: `upload_story`
```json
{ "type": "upload_story", "upload_id": 7, "name": "foto.jpeg", "data": "<base64 sem prefixo data:>" }
```

### Server → Client: `upload_result`
```json
{ "type": "upload_result", "upload_id": 7, "ok": true,  "name": "foto.jpeg" }
{ "type": "upload_result", "upload_id": 7, "ok": false, "error": "extensão não permitida" }
```

`upload_id` é um contador do editor que casa a resposta com o pedido (suporta
uploads paralelos). Tratado em `server.py` no dispatch de mensagens
(`server.py:12371`) como novo `t == "upload_story"`, **antes** da lógica de
sala — não exige room nem player.

## Servidor (`server.py`)

### Handler `upload_story`
Validação, em ordem:
- **Nome:** reduzir a basename (`os.path.basename`) — bloqueia `../` e caminhos
  absolutos. Rejeitar nome vazio.
- **Extensão (allow-list, case-insensitive):**
  - imagens: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
  - áudio: `.mp3`, `.ogg`, `.wav`, `.m4a`
  - qualquer outra → erro "extensão não permitida".
- **Tamanho:** rejeitar se o base64 decodificado passar de 25 MB
  (`25 * 1024 * 1024`). Calcular o tamanho a partir do comprimento do base64
  antes de decodificar quando possível.
- Decodificar base64 (erro → "dados inválidos").
- Escrever em `assets/story/<basename>` (sobrescreve). Erro de I/O → "falha ao
  gravar".
- Sempre responder `upload_result` (ok ou erro). Nunca silencioso.

### `max_size` do WebSocket
Em `websockets.serve(...)` (`server.py:12707`) definir `max_size = 34 * 1024 *
1024` (34 MB). O default é 1 MB e derrubaria a conexão em áudios/imagens
maiores: o base64 infla ~33%, então um arquivo de 25 MB vira ~33 MB de
mensagem — 34 MB dá folga suficiente.

### MIME types
Adicionar ao mapa em `server.py:12625` para o jogo servir os novos formatos com
Content-Type correto (hoje só `.jpg` está presente):
`.jpeg → image/jpeg`, `.gif → image/gif`, `.mp3 → audio/mpeg`,
`.ogg → audio/ogg`, `.wav → audio/wav`, `.m4a → audio/mp4`.

## Editor (`tools/editor_campaign.js`)

### Módulo de upload
- Abre 1 WebSocket sob demanda (lazy), reaproveitado entre uploads.
- Contador `upload_id`; mapa de pendências `upload_id → resolve/reject`.
- Cada upload retorna uma Promise resolvida pelo `upload_result` correspondente.
- Timeout razoável (ex. 30 s) e tratamento de conexão fechada → rejeita com
  mensagem clara.

### Integração nos handlers de escolha
- Em escolher imagem (`tools/editor_campaign.js:168`) e áudio (`:137`): além de
  setar `s._url`/`s.image` (imagem) ou `st._audioUrl`/`st.audio` (áudio),
  disparar o upload.
- Manter o blob (`_url`/`_audioUrl`) para a pré-visualização continuar
  instantânea.
- Mostrar estado no card: "enviando…" → "✓ enviado" ou "✗ <motivo>".
- Sanitização do nome no cliente (mesma allow-list) para feedback imediato
  antes mesmo de enviar.

### Falha de conexão
Se o WebSocket não conectar (servidor desligado), exibir aviso claro:
"não foi possível enviar — o servidor está rodando?" sem travar o editor (a
pré-visualização via blob continua funcionando).

## Tratamento de erros (resumo)

| Situação | Resposta |
|---|---|
| Extensão fora da allow-list | `ok:false, error:"extensão não permitida"` |
| Arquivo > 25 MB | `ok:false, error:"arquivo grande demais"` |
| Base64 inválido | `ok:false, error:"dados inválidos"` |
| Nome com `../` / absoluto | reduzido a basename; se vazio → erro |
| Falha de escrita em disco | `ok:false, error:"falha ao gravar"` |
| Servidor offline (editor) | aviso no card; preview via blob mantida |

## Testes

`tools/test_story_upload.py` (sem framework; roda da raiz):
- Sobe o handler / chama a função de upload diretamente.
- **Caso feliz:** envia imagem pequena válida (PNG base64) → confere que o
  arquivo aparece em `assets/story/` com o conteúdo correto.
- **Sobrescrita:** envia duas vezes o mesmo nome com conteúdos diferentes →
  confere que o segundo prevalece.
- **Casos inválidos:** extensão proibida (`.exe`), nome com `../`, base64
  quebrado, arquivo acima do limite → confere rejeição com o erro esperado e
  que nada é gravado.
- Limpa os arquivos de teste de `assets/story/` no fim.

## Fora de escopo (YAGNI)

- Teto somado de mídia por campanha/masmorra (apenas mencionado como possível
  aviso futuro, não implementado).
- Servir o editor pelo servidor (continua `file://`).
- Upload em chunks / streaming (o limite por arquivo cabe numa mensagem só).
- Remoção de arquivos órfãos de `assets/story/`.
