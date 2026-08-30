# SP3 — Persistência que sobrevive ao redeploy — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Contas, jogos salvos e grupos sobreviverem ao redeploy, sem que nenhuma das 21 chamadas de escrita do jogo precise mudar.

**Architecture:** Uma loja de documentos em memória vira a fonte de verdade em execução (1,3 MB cabe com folga). Leituras saem do cache — síncronas, com as mesmas assinaturas. Escritas marcam a chave como suja; a descarga acontece nos pontos seguros que o jogo já usa. Dois adaptadores: arquivo (local, padrão) e Postgres (online).

**Tech Stack:** Python 3.14 local / 3.13 no Render, `aiohttp`, driver de Postgres (`psycopg`).

**Spec:** `docs/superpowers/specs/2026-08-30-sp3-persistencia-design.md`

---

## AVISO — o autor edita `server.py` em paralelo

Ele tem trabalho não commitado em 14 arquivos, `server.py` incluído (206 linhas).
**NUNCA** rode `git add server.py`, `git add .` ou `git add -A`.

Para commitar sem levar o WIP junto, use a técnica validada dez vezes nesta série:

```bash
git show HEAD:server.py > SCRATCH/head_server.py
# aplique a MESMA edição nos dois (o de trabalho e a cópia)
BLOB=$(git hash-object -w SCRATCH/head_server.py)
git update-index --cacheinfo 100644,$BLOB,server.py
git commit -m "..."
```

**Antes:** snapshot de `git diff server.py`. **Depois:** confirme que toda linha
`+` do snapshot ainda existe no arquivo. Edite em **binário**; `troca()` deve
tentar LF **e** CRLF (`src/lang/interface.js` e `src/gameState.js` são CRLF).

**E calcule o resultado ANTES de abrir para escrita.** `open(a,'wb')` trunca no
momento em que abre: `open(a,'wb').write(f(d))` com `f` que aborta deixa o
arquivo com ZERO bytes. Foi assim que o SP1 destruiu `src/lang/interface.js`.

---

## As quatro sutilezas que vão morder

Levantadas lendo a camada atual. Cada uma muda de natureza quando a fonte de
verdade sai do disco:

| Onde | Hoje | Depois |
|---|---|---|
| `_new_group_id` | `os.path.exists(group_path(gid))` para achar id livre | consultar o **cache** |
| `list_savegames` | `os.listdir` + abre e parseia **todos** os savegames | iterar o cache (some a leitura de disco repetida) |
| `load_savegame` | tenta o `.json`, e no erro cai para o `.bak` | o `.bak` vira detalhe **só do adaptador de arquivo** |
| `write_savegame` | rotaciona o atual para `.bak` antes de gravar | idem — o cache não tem duas versões |

---

### Task 1: A loja de documentos e o adaptador de arquivo

Unidade nova e isolada. **Nenhuma função existente muda ainda.**

**Files:** Modify `server.py`; Create `tools/test_persistencia.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
"""SP3 — persistência. Roda da raiz: python tools/test_persistencia.py"""
import os, shutil, sys, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(nome, cond, dica=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  [ok] {nome}")
    else:    FAIL += 1; print(f"  [FALHA] {nome}" + (f" -- {dica}" if dica else ""))


def secao_loja():
    print("\n[1] loja de documentos, adaptador de arquivo")
    tmp = tempfile.mkdtemp()
    ad = S.AdaptadorArquivo(tmp)
    loja = S.LojaDocumentos(ad)
    try:
        loja.carregar()
        check("loja vazia começa vazia", loja.listar("contas") == {})

        loja.gravar("contas", "ana", {"username": "ana", "x": 1})
        check("grava e lê do cache na hora",
              loja.ler("contas", "ana") == {"username": "ana", "x": 1})
        check("a chave fica suja até descarregar",
              ("contas", "ana") in loja.sujos())

        loja.descarregar()
        check("descarregar limpa as sujas", not loja.sujos())
        check("o arquivo existe em disco",
              os.path.exists(os.path.join(tmp, "contas", "ana.json")))

        # uma loja NOVA sobre o mesmo diretorio tem de ver o que foi gravado
        loja2 = S.LojaDocumentos(S.AdaptadorArquivo(tmp))
        loja2.carregar()
        check("outra loja carrega o que a primeira gravou",
              loja2.ler("contas", "ana") == {"username": "ana", "x": 1})

        loja.apagar("contas", "ana")
        check("apagar some do cache na hora", loja.ler("contas", "ana") is None)
        loja.descarregar()
        check("apagar some do disco",
              not os.path.exists(os.path.join(tmp, "contas", "ana.json")))

        check("ler chave inexistente devolve None",
              loja.ler("contas", "ninguem") is None)
        check("ler coleção inexistente não estoura",
              loja.ler("inventada", "x") is None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    secao_loja()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_persistencia.py`
Expected: `AttributeError: module 'server' has no attribute 'AdaptadorArquivo'`

- [ ] **Step 3: Implementar, logo depois de `_atomic_write_json`**

```python
# ─── Loja de documentos ───────────────────────────────────────────────────────
# Contas, jogos salvos e grupos somam 1,3 MB -- cabem na memoria com folga. E e
# isso que permite manter as 21 chamadas de escrita do jogo SINCRONAS: o cache e
# a fonte de verdade em execucao, e a ida ao armazenamento acontece depois.
COLECOES = ("contas", "savegames", "grupos")


class AdaptadorArquivo:
    """Um arquivo JSON por documento, como sempre foi. Padrao local: quem so
    quer jogar em casa nao instala banco nenhum."""

    def __init__(self, raiz):
        self.raiz = raiz

    def _caminho(self, colecao, chave):
        return os.path.join(self.raiz, colecao, f"{chave}.json")

    def carregar_tudo(self):
        fora = {c: {} for c in COLECOES}
        for colecao in COLECOES:
            pasta = os.path.join(self.raiz, colecao)
            if not os.path.isdir(pasta):
                continue
            for fn in os.listdir(pasta):
                if not fn.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(pasta, fn), encoding="utf-8") as f:
                        fora[colecao][fn[:-5]] = json.load(f)
                except Exception as e:
                    print(f"[loja] {colecao}/{fn} ilegivel ({e}) -- ignorado")
        return fora

    def gravar(self, colecao, chave, doc):
        _atomic_write_json(self._caminho(colecao, chave), doc)

    def apagar(self, colecao, chave):
        for p in (self._caminho(colecao, chave), self._caminho(colecao, chave) + ".bak"):
            try:
                os.remove(p)
            except OSError:
                pass


class LojaDocumentos:
    """Cache autoritativo + marcacao de sujos.

    Leituras saem do cache, o que mantem load_account/load_savegame/load_group
    SINCRONOS e com a mesma assinatura -- e de quebra elimina a leitura de disco
    que list_savegames fazia a cada chamada, abrindo TODOS os savegames."""

    def __init__(self, adaptador):
        self.adaptador = adaptador
        self._docs = {c: {} for c in COLECOES}
        self._sujos = set()
        self._carregada = False

    def carregar(self):
        self._docs = self.adaptador.carregar_tudo()
        for c in COLECOES:
            self._docs.setdefault(c, {})
        self._sujos.clear()
        self._carregada = True

    def ler(self, colecao, chave):
        return self._docs.get(colecao, {}).get(chave)

    def listar(self, colecao):
        return dict(self._docs.get(colecao, {}))

    def gravar(self, colecao, chave, doc):
        self._docs.setdefault(colecao, {})[chave] = doc
        self._sujos.add((colecao, chave))

    def apagar(self, colecao, chave):
        self._docs.get(colecao, {}).pop(chave, None)
        self._sujos.add((colecao, chave))

    def sujos(self):
        return set(self._sujos)

    def descarregar(self):
        """Manda as sujas para o armazenamento. Uma chave que falhar CONTINUA
        suja: some do lote atual mas volta no proximo, em vez de sumir calada."""
        for colecao, chave in sorted(self._sujos):
            doc = self._docs.get(colecao, {}).get(chave)
            try:
                if doc is None:
                    self.adaptador.apagar(colecao, chave)
                else:
                    self.adaptador.gravar(colecao, chave, doc)
            except Exception as e:
                print(f"[loja] falha ao gravar {colecao}/{chave}: {e}")
                continue
            self._sujos.discard((colecao, chave))
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_persistencia.py`
Expected: `=== 9 passaram, 0 falharam ===`

- [ ] **Step 5: Nada mais mudou**

Run: `python tools/test_savegames.py` → 94/94
Run: `python tools/test_modo_publico.py` → 40/40

- [ ] **Step 6: Commit (técnica do blob)**

---

### Task 2: A loja global e a migração das contas

**Files:** Modify `server.py`, `tools/test_persistencia.py`

- [ ] **Step 1: Teste**

```python
def secao_contas():
    print("\n[2] contas saem do disco e vão para a loja")
    tmp = tempfile.mkdtemp(); velho = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        import asyncio
        acc, err = asyncio.run(S.create_account("ana", "senha bem longa"))
        check("cria conta", acc is not None, str(err))
        check("a conta está na loja, não só em disco",
              S.LOJA.ler("contas", "ana") is not None)
        check("load_account lê da loja", S.load_account("ANA") is not None)
        check("nenhum arquivo foi escrito ainda (só na descarga)",
              not os.path.exists(os.path.join(tmp, "contas", "ana.json")))
        S.LOJA.descarregar()
        check("depois da descarga, está em disco",
              os.path.exists(os.path.join(tmp, "contas", "ana.json")))
        check("conta inexistente continua devolvendo None",
              S.load_account("fantasma") is None)
    finally:
        S.LOJA = velho; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Ver falhar, implementar**

Criar a loja global, perto de `ACCOUNTS_DIR`:

```python
# Loja global. O adaptador e escolhido no boot (ver escolher_armazenamento()).
LOJA = LojaDocumentos(AdaptadorArquivo(BASE_DIR))
```

**Atenção ao layout:** o adaptador de arquivo grava em
`<raiz>/<colecao>/<chave>.json`. As coleções se chamam `contas`, `savegames` e
`grupos`, então os diretórios passam a ser `contas/` (e não `accounts/`). Ou
mapeie coleção→diretório no adaptador para preservar os nomes atuais — **decida
e deixe explícito**, porque um `.gitignore` aponta para os nomes antigos.

Reescrever as três funções de conta:

```python
def write_account(account):
    """Grava o perfil permanente da conta, sem dados de campanha."""
    username = _norm_username((account or {}).get("username"))
    if not _username_valido(username):
        return
    LOJA.gravar("contas", username, account)


def load_account(username):
    """Lê a conta; ausente/forma inesperada → None (sem crash)."""
    u = _norm_username(username)
    if not _username_valido(u):
        return None
    data = LOJA.ler("contas", u)
    if not isinstance(data, dict) or not isinstance(data.get("password_hash"), str):
        return None
    if ensure_account_profile(data):
        write_account(data)
    return data
```

`account_path` deixa de ser usada pela camada de dados. **Confira quem mais a
chama** antes de remover — os testes chamam.

- [ ] **Step 3: Ver passar; rodar `test_savegames` e `test_modo_publico`**

- [ ] **Step 4: Commit (técnica do blob)**

---

### Task 3: Grupos

**Files:** Modify `server.py`, `tools/test_persistencia.py`

- [ ] **Step 1: Teste — com a sutileza do id livre**

```python
def secao_grupos():
    print("\n[3] grupos")
    tmp = tempfile.mkdtemp(); velho = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        g = S.create_group("Meu Grupo", "ana")
        check("cria grupo", isinstance(g, dict) and g.get("id"))
        check("grupo está na loja", S.LOJA.ler("grupos", g["id"]) is not None)
        check("load_group lê da loja", S.load_group(g["id"]) is not None)
        check("id inválido devolve None", S.load_group("nao_e_id") is None)

        # _new_group_id usava os.path.exists; agora tem de olhar o CACHE, senão
        # sortearia um id ja usado que ainda nao foi descarregado.
        usados = {S.create_group(f"G{i}", "ana")["id"] for i in range(20)}
        check("20 grupos seguidos têm ids distintos (id livre vem do cache)",
              len(usados) == 20)
    finally:
        S.LOJA = velho; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Implementar**

```python
def _new_group_id():
    while True:
        gid = "grp_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        # Antes: os.path.exists(group_path(gid)). Com a loja, o id so seria
        # visto em disco DEPOIS da descarga -- dois grupos criados na mesma
        # sessao poderiam colidir.
        if LOJA.ler("grupos", gid) is None:
            return gid


def load_group(gid):
    if not _gid_valido(gid):
        return None
    group = LOJA.ler("grupos", gid)
    return group if isinstance(group, dict) and group.get("id") == gid else None
```

E `write_group` grava na loja.

- [ ] **Step 3: Ver passar; suítes; commit (blob)**

---

### Task 4: Savegames — a maior, por causa do `.bak`

**Files:** Modify `server.py`, `tools/test_persistencia.py`

- [ ] **Step 1: Teste**

```python
def secao_savegames():
    print("\n[4] savegames")
    tmp = tempfile.mkdtemp(); velho = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        sg = S.create_savegame("Campanha", "ana", "campaign", None, False)
        sid = sg["id"]
        check("cria savegame", S.load_savegame(sid) is not None)
        check("está na loja", S.LOJA.ler("savegames", sid) is not None)

        vistos = S.list_savegames("ana")
        check("list_savegames encontra o jogo da conta",
              any(x.get("id") == sid for x in vistos))
        check("list_savegames NÃO lista jogo de outra conta",
              not S.list_savegames("beto"))

        S.delete_savegame(sid, "ana")
        check("apagar some da loja", S.load_savegame(sid) is None)
        check("id inválido devolve None", S.load_savegame("../fora") is None)
    finally:
        S.LOJA = velho; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Implementar**

```python
def load_savegame(sid):
    """Carrega o savegame da loja.

    O fallback para .bak saiu daqui: com a loja, o backup de um nivel e detalhe
    do ADAPTADOR DE ARQUIVO -- e o cache nunca tem duas versoes do mesmo
    documento. Um .bak so entra em jogo se o .json principal estiver ilegivel na
    CARGA, e e la que ele deve ser tentado."""
    if not _sid_valido(sid):
        return None
    d = LOJA.ler("savegames", sid)
    return d if _savegame_valid_shape(d) else None


def write_savegame(sg):
    sid = sg.get("id")
    if not _sid_valido(sid):
        return
    LOJA.gravar("savegames", sid, sg)


def list_savegames(username):
    """Resumo dos jogos onde a conta é dona, membro ou mestre.

    Antes fazia listdir e abria TODOS os savegames a cada chamada. Agora itera o
    cache."""
    u = _norm_username(username)
    out = []
    if not u:
        return out
    for sid, sg in LOJA.listar("savegames").items():
        if not _savegame_valid_shape(sg):
            continue
        if ensure_campaign_schema(sg):
            write_savegame(sg)
        ...  # o resto do corpo atual, inalterado
```

**A rotação de `.bak`** passa para `AdaptadorArquivo.gravar`: antes de escrever,
renomeia o atual para `.bak`. Assim o backup de um nível continua existindo em
disco, sem que a loja precise saber dele.

- [ ] **Step 3: Ver passar; suítes; commit (blob)**

---

### Task 5: Caçar leituras remanescentes de disco

**O passo que evita o bug silencioso.** Com o cache virando fonte de verdade,
qualquer caminho que ainda abra o arquivo direto passa a ler **dado velho** — e
isso não estoura, só devolve o errado.

- [ ] **Step 1: Varredura**

```bash
grep -nE "open\(.*(account_path|group_path|savegame_path)|os\.listdir\(.*(ACCOUNTS|SAVEGAMES|GROUPS)|os\.path\.exists\(.*(account_path|group_path|savegame_path)" server.py
```

Expected: nenhuma linha. Cada ocorrência é uma leitura que ficou para trás.

- [ ] **Step 2: Teste que trava a regra**

```python
def secao_sem_disco():
    print("\n[5] ninguém lê o disco pelas costas da loja")
    import re
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonte = open(os.path.join(raiz, "server.py"), encoding="utf-8").read()
    padroes = [
        r"open\([^)]*(?:account_path|group_path|savegame_path)",
        r"os\.listdir\([^)]*(?:ACCOUNTS_DIR|SAVEGAMES_DIR|GROUPS_DIR)",
        r"os\.path\.exists\([^)]*(?:account_path|group_path|savegame_path)",
    ]
    achados = [m for p in padroes for m in re.findall(p, fonte)]
    check(f"nenhuma leitura direta de disco fora do adaptador ({achados or 'nenhuma'})",
          not achados,
          "com o cache como fonte de verdade, isso leria dado VELHO em silêncio")
```

- [ ] **Step 3: Commit (blob)**

---

### Task 6: Adaptador Postgres, e falhar alto na subida

**Files:** Modify `server.py`, `requirements.txt`, `iniciar.bat`, `online.py`

- [ ] **Step 1: Dependência nos três pontos**

`requirements.txt` ganha `psycopg[binary]`. `iniciar.bat` e `online.py` ganham a
verificação — **os mesmos três pontos de entrada que o SP1 mapeou.** Sem isso, o
servidor não sobe na máquina de quem atualizar, com `ModuleNotFoundError` cru.

- [ ] **Step 2: Implementar o adaptador**

```python
class AdaptadorPostgres:
    """Uma tabela de documentos, porque os dados JA sao documentos JSON.
    Modelar em tabelas seria reescrever o que funciona -- e cada campo novo de
    savegame viraria uma migracao."""

    DDL = """
    CREATE TABLE IF NOT EXISTS documentos (
      colecao       text  NOT NULL,
      chave         text  NOT NULL,
      json          jsonb NOT NULL,
      atualizado_em timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (colecao, chave)
    );
    """
    ...
```

**A string de conexão NUNCA pode ser impressa**, nem em mensagem de erro nem em
diagnóstico — ela contém a senha do banco.

- [ ] **Step 3: A escolha do adaptador, e a falha alta**

```python
def escolher_armazenamento():
    """Postgres quando LFH_DB_URL existe; arquivo quando nao.

    Se o banco estiver inalcancavel, o servidor NAO SOBE. Subir com o cache
    vazio faria todo jogador ver "conta nao encontrada", tentar criar a conta de
    novo, e -- quando o banco voltasse -- haveria duas verdades em conflito.
    Sumico silencioso de contas e pior que indisponibilidade honesta."""
```

- [ ] **Step 4: Teste da falha alta**

Verifique que, com `LFH_DB_URL` apontando para um banco inexistente, o processo
**termina com mensagem clara** em vez de subir vazio.

- [ ] **Step 5: Commit (blob)**

---

### Task 7: Descarga por evento, e saída limpa

- [ ] **Step 1: Implementar**

A descarga acontece:

1. **nos pontos seguros do jogo** — onde `_checkpoint_savegame` e o retorno à
   cidade já gravam. Agrupa tudo que estiver sujo numa ida só;
2. **antes de encerrar**, numa saída limpa;
3. e, como rede de segurança, num intervalo **longo** — minutos, não segundos.

**Por que não um temporizador curto:** banco gerenciado gratuito cobra por tempo
de computação e fica acordado enquanto recebe consultas. Descarregar a cada
poucos segundos manteria o banco ligado **a sessão inteira** — duas horas de
jogo virariam duas horas de computação, e o teto mensal sumiria com pouco mais
de três horas de jogo por dia. Por evento, a mesma sessão custa minutos.

- [ ] **Step 2: Teste**

Que uma escrita marcada suja chega ao armazenamento **sem ninguém pedir**, e que
a saída limpa descarrega o pendente.

- [ ] **Step 3: Commit (blob)**

---

### Task 8: Restrição de instância única

- [ ] **Step 1: Escrever no código, não só no painel**

Duas instâncias teriam caches separados, e a última a descarregar venceria —
apagando o trabalho da outra em silêncio. Isso deixa de ser detalhe de
infraestrutura e vira **restrição do desenho**: registre no `README.md` e num
comentário na loja, ao lado da declaração da `LOJA` global.

- [ ] **Step 2: Commit**

---

## Critérios de conclusão

- [ ] `tools/test_persistencia.py` verde
- [ ] `test_savegames` 94, `test_modo_publico` 40, `test_modo_mestre` 337, rede e
      http verdes
- [ ] Sem `LFH_DB_URL`: o jogo funciona com arquivos, como hoje
- [ ] Com `LFH_DB_URL`: criar conta, logar, criar savegame e **reiniciar o
      processo** — os dados continuam lá
- [ ] Banco inalcançável na subida → o servidor não sobe, e diz por quê
- [ ] Nenhuma chamada de `write_savegame`/`write_account`/`write_group` virou `await`
- [ ] A string de conexão não aparece em arquivo versionado nem em log
- [ ] O WIP do autor em `server.py` intacto

## Fora de escopo

- Múltiplas instâncias (restrição declarada, não problema a resolver)
- Migrar dados antigos (foram apagados no SP1)
- SP2 (estáticos no CDN) e SP4 (empacotamento e warm-up)
