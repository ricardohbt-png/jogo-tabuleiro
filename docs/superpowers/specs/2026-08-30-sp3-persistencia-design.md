# SP3 — Persistência que sobrevive ao redeploy — Design

**Data:** 2026-08-30
**Pertence a:** hospedagem online (`2026-08-28-hospedagem-online-design.md`)
**Depende de:** SP1 (modo público), concluído. Fecha o bloqueador **B3**.

---

## Por que isto existe

Contas, jogos salvos e grupos são **arquivos em disco**. No plano gratuito o
disco é **efêmero**: cada redeploy ou reciclagem do contêiner apaga tudo.

Sem isto, tudo que o SP1 construiu — senha, freio contra força bruta, portão dos
editores — protege dados que **somem sozinhos no próximo deploy**.

## O que a medição mostrou

Duas medidas conduziram o desenho, e a segunda inverteu a escolha óbvia:

| | |
|---|---|
| Dados que precisam sobreviver | **1,3 MB** (30 KB contas + 188 KB savegames + 1,1 MB grupos) |
| Camada de dados | 13 funções, todas juntas; toda escrita passa por `_atomic_write_json` |
| Chamadas de escrita em função **async** | 5 |
| Chamadas de escrita em função **síncrona** | **13**, espalhadas por 11 funções |

**1,3 MB cabe na memória com folga.** É isso que torna possível manter as
escritas síncronas — e é por isso que a solução "correta no papel" foi
descartada.

## Decisão do autor

> Perder **alguns segundos** de progresso numa queda do servidor é aceitável.

Isso é menos grave do que parece: o jogo só grava em **pontos seguros** — volta
à cidade, fim de fase — e nunca no meio de uma masmorra. Na prática, perder a
janela significa refazer no máximo uma compra na loja ou reentrar numa masmorra.

Essa decisão é o que libera a abordagem pequena.

---

## Alternativas consideradas

**Escrita assíncrona direta** (a gravação só termina quando o banco confirma):
correta no papel, nada se perde. Descartada porque cascatearia por 11 funções
síncronas e por tudo que as chama, num arquivo de 35.522 linhas onde o autor tem
trabalho em aberto. Compra uma garantia que o autor disse não precisar.

**Arquivo local como área de trabalho, banco como espelho**: diff ainda menor,
mas cria **duas fontes de verdade**. Se a sincronização falhar, o arquivo fica à
frente do banco e descobrir isso é difícil. Ambiguidade não vale o desconto.

---

## Desenho

### 1. Interface de documentos

Três operações, e nada mais:

```
carregar_tudo()               -> {colecao: {chave: doc}}
gravar(colecao, chave, doc)
apagar(colecao, chave)
```

Coleções: `contas`, `savegames`, `grupos`.

### 2. Dois adaptadores

**Arquivo** — o que existe hoje, com escrita atômica via `.tmp`. É o padrão
local, e é o que os testes usam. Nada de banco na máquina de quem só quer jogar.

**Postgres** — uma tabela só:

```sql
CREATE TABLE documentos (
  colecao       text  NOT NULL,
  chave         text  NOT NULL,
  json          jsonb NOT NULL,
  atualizado_em timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (colecao, chave)
);
```

Uma tabela de documentos, e não um modelo relacional, porque **os dados já são
documentos JSON**. Modelar em tabelas seria reescrever o que funciona — e cada
campo novo de savegame viraria uma migração.

O adaptador é escolhido por variável de ambiente (`LFH_DB_URL`): presente →
Postgres; ausente → arquivo. **A string de conexão nunca entra no repositório.**

### 3. Cache autoritativo em memória

Carregado na subida; **toda leitura sai dele**. Isso mantém `load_account`,
`load_savegame`, `load_group` e `list_savegames` síncronos e com a mesma
assinatura — e é o que faz as 21 chamadas de escrita não mudarem.

De quebra, elimina a leitura de disco que hoje acontece a cada `list_savegames`,
que abre e parseia **todos** os savegames a cada chamada.

### 4. Descarga em segundo plano

`gravar` atualiza o cache e marca a chave como suja. Uma tarefa descarrega as
sujas a cada poucos segundos, e também **antes de encerrar** numa saída limpa.

É aqui que mora a janela de perda que o autor aceitou.

---

## Os dois modos de falha que precisam de desenho

**Banco inalcançável na subida: falhar ALTO, e não subir vazio.**
Se o servidor subisse com o cache vazio, todo jogador veria "conta não
encontrada", tentaria criar a conta de novo, e quando o banco voltasse haveria
duas verdades em conflito. O servidor **recusa subir** e diz por quê. Sumiço
silencioso de contas é pior que indisponibilidade honesta.

**Duas instâncias corrompem os dados.**
Cada uma teria seu próprio cache, e a última a descarregar venceria — apagando o
trabalho da outra em silêncio. O plano gratuito roda **uma instância**, e isso
deixa de ser detalhe de infraestrutura para virar **restrição do desenho**:
precisa estar escrito no código, não só no painel do provedor.

## Provedor

**Neon** (Postgres gerenciado): 0,5 GB, sem cartão, hiberna em 5 min e acorda em
centenas de milissegundos. Nossos 1,3 MB cabem 380×. A hibernação não incomoda
porque a descarga é de fundo — ninguém espera por ela.

Verificado em 2026-08-30; planos gratuitos mudam, então reconfirmar antes de
implantar.

## O que NÃO pode mudar

- **O jogo local.** Sem `LFH_DB_URL`, tudo funciona como hoje, com arquivos.
- **As assinaturas da camada de dados.** As 13 funções continuam síncronas.
- **O formato dos documentos.** O JSON gravado é o mesmo — o que permite
  exportar de volta para arquivos a qualquer momento.

## Critérios de aceitação

1. Sem `LFH_DB_URL`: suíte inteira verde, jogo funciona com arquivos.
2. Com `LFH_DB_URL`: criar conta, logar, criar savegame, checkpoint e reabrir
   funcionam — e os dados sobrevivem a **reiniciar o processo**.
3. Banco inalcançável na subida → o servidor **não sobe**, e a mensagem diz por
   quê.
4. Uma escrita marcada como suja chega ao banco sem ninguém pedir.
5. Saída limpa descarrega o que estava pendente.
6. Nenhuma chamada de `write_savegame`/`write_account`/`write_group` precisou
   virar `await`.
7. A string de conexão não aparece em nenhum arquivo versionado.

## Fora de escopo

- Múltiplas instâncias (é restrição declarada, não problema a resolver).
- Migrar os dados atuais: foram apagados no SP1, por decisão do autor.
- Backup e restauração além do que o próprio provedor oferece.
- SP2 (estáticos no CDN) e SP4 (empacotamento e warm-up).

## Riscos

1. **A janela de perda é real.** Aceita, mas precisa ser curta e medida — não
   estimada. O teste deve provar que uma escrita chega ao banco.
2. **Segredo em variável de ambiente.** Fácil vazar num log ou numa mensagem de
   erro. A string de conexão nunca deve ser impressa, nem em diagnóstico.
3. **Dependência nova** (driver de Postgres). Terceira do projeto, depois de
   `aiohttp` e `websockets` — e precisa entrar nos três pontos de instalação que
   o SP1 já mapeou: `requirements.txt`, `iniciar.bat` e `online.py`.
4. **O cache em memória vira a fonte de verdade em execução.** Um caminho de
   código que ainda leia do disco direto passaria a ler dado velho. A busca por
   leituras remanescentes faz parte do trabalho, não é opcional.
