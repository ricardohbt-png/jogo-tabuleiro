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

### 4. Descarga dirigida por EVENTO, não por relógio

`gravar` atualiza o cache e marca a chave como suja. A descarga acontece:

- **nos pontos seguros do próprio jogo** — volta à cidade, fim de fase — que é
  onde o jogo já grava hoje, agrupando tudo que estiver sujo numa ida só;
- **antes de encerrar**, numa saída limpa;
- e, como rede de segurança, num intervalo **longo** (não segundos) para o caso
  de uma marca suja não coincidir com nenhum ponto seguro.

**Por que não um temporizador curto** (era o que este spec dizia numa versão
anterior): bancos gerenciados gratuitos cobram por *tempo de computação*, e o
banco fica acordado enquanto recebe consultas. Descarregar a cada poucos
segundos manteria o banco ligado **durante a sessão inteira de jogo** — duas
horas jogando virariam duas horas de computação, e o teto mensal do plano
gratuito sumiria com pouco mais de três horas de jogo por dia.

Dirigida por evento, a mesma sessão custa **minutos**: o banco acorda em cada
ponto seguro e volta a dormir. A diferença não é otimização — é o que decide se
o plano gratuito aguenta ou não.

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

## Provedor: deliberadamente NÃO fixado

Ambos os candidatos são Postgres — mesmo driver, mesma tabela, mesmas consultas.
**Trocar de um para outro é trocar a string de conexão**, não reescrever código.
Fixar um no desenho seria abrir mão de graça da folga que a interface já dá.

| | Neon | Supabase |
|---|---|---|
| Espaço | 0,5 GB (380× de folga) | 500 MB (mesma folga) |
| O que realmente aperta | **100 h de computação/mês** | 7 dias parado → pausa manual |
| Cartão | não pede | não pede |

**A dimensão que aperta é diferente em cada um, e o nosso perfil é de rajadas.**
No espaço temos folga enorme nos dois. O Neon cobra tempo de computação, que é
justamente o que um jogo consome ao manter o banco acordado durante a partida —
por isso a descarga por evento (seção 4) importa mais lá. O Supabase não tem esse
teto, mas pausa o projeto após 7 dias sem uso, com despausa manual.

**Recomendação: Supabase**, porque cobra numa dimensão que quase não nos atinge e
dá folga onde a gente gasta. Mas a escolha não bloqueia nada: o desenvolvimento
local não usa banco nenhum, e o adaptador é o mesmo.

Verificado em 2026-08-30; planos gratuitos mudam, então reconfirmar antes de
implantar.

### Nota: o plano pago do Render tornaria isto desnecessário

Levantado durante o desenho e **descartado por decisão do autor**, que preferiu
manter o SP3: um plano pago do Render oferece **disco persistente**, o que faria
os arquivos sobreviverem ao redeploy sem banco nenhum — e de quebra removeria a
hibernação (os 21–62 s medidos no SP0) e daria snapshots diários. A limitação de
"uma instância só" que ele impõe é exatamente a restrição que este desenho já
declarava.

Fica registrado porque, se o projeto vier a pagar hospedagem, **este
sub-projeto inteiro pode ser aposentado** — e é melhor saber disso de antemão
do que descobrir depois de mantê-lo por anos.

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
