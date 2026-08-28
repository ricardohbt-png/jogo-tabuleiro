# SP0 — Spike de deploy — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subir o `server.py` como está numa hospedagem gratuita e **medir** três coisas que podem invalidar o desenho da hospedagem online: se a plataforma roda este Python, se o bind funciona no Linux, e quanto custa de verdade acordar do sono.

**Architecture:** O spike não muda a arquitetura do jogo. Ele adiciona duas funções puras (`_listen_port`, `_listen_hosts`) que substituem duas constantes de módulo, um `requirements.txt`, um `render.yaml` descartável e um medidor. Tudo que não for estritamente necessário para o processo subir fica de fora — os achados viram itens de SP1–SP4.

**Tech Stack:** Python 3.14 local, `websockets` 16.0, Render free (WebSocket, sem cartão), GitHub como fonte do deploy.

**Spec:** `docs/superpowers/specs/2026-08-28-hospedagem-online-design.md`

---

## Pré-requisitos que exigem VOCÊ no teclado

Estes três passos eu não posso executar. Criar contas e autenticar são suas.

- [ ] **P1.** Criar conta no Render (https://render.com). O desenho assume que **não pedem cartão**. Se pedirem, **pare aqui e me avise** — isso invalida a restrição de US$ 0 estrito e o desenho volta à mesa.
- [ ] **P2.** Autorizar o push da branch de spike para o GitHub. O `origin` está desatualizado (`origin/master` = `7a8e3e6`); a branch do spike vai levar código novo para um repositório público. **Confirme antes**, e confirme também se o repositório `ricardohbt-png/jogo-tabuleiro` é público ou privado — isso muda quem enxerga o conteúdo do jogo.
- [ ] **P3.** Conectar o Render ao repositório do GitHub (fluxo OAuth na interface do Render).

---

## Regra de contenção do spike

O ambiente do spike expõe os **17 handlers de escrita sem autenticação** (bloqueador B1 do spec). Isso é aceito de propósito — consertá-los é o SP1. A contenção é operacional, e é obrigatória:

- A URL do serviço **não é divulgada** a ninguém.
- **Nenhuma conta real** é criada; nenhum dado real sobe.
- O serviço é **destruído** ao fim da medição (Task 7).
- Tudo dentro de **uma sessão**. Se ficar para o dia seguinte, destrua o serviço e recrie depois.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `requirements.txt` | **Criar.** Única dependência de runtime do servidor |
| `server.py:34914-34920` | **Modificar.** As duas constantes de escuta viram funções puras |
| `tools/test_deploy_config.py` | **Criar.** Testa as duas funções sem subir servidor nem tocar em `os.environ` |
| `tools/medir_cold_start.py` | **Criar.** Mede conexão e ida-e-volta contra uma URL `wss://` |
| `render.yaml` | **Criar.** Config do serviço descartável. Removido na Task 7 |
| `docs/superpowers/plans/2026-08-28-sp0-resultados.md` | **Criar na Task 7.** O entregável real do spike |

**Por que funções e não constantes:** `tools/test_*.py` faz `import server as S`, o que executa o código de módulo. Uma constante avaliada no import só pode ser testada mexendo em `os.environ` antes de importar — frágil e com efeito colateral entre testes. Funções puras com `env` injetável testam as precedências direto. É a mesma lição do `CLAUDE.md` sobre constantes de módulo que chamam `t()` no carregamento.

---

### Task 1: `requirements.txt`

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Confirmar a versão instalada localmente**

Run: `python -c "import websockets; print(websockets.__version__)"`
Expected: `16.0`

- [ ] **Step 2: Criar o arquivo**

```
websockets==16.0
```

Uma dependência só, fixada. `server.py` não importa mais nada fora da biblioteca padrão — se a instalação na plataforma reclamar de outro pacote, isso é um achado do spike, não algo a corrigir por antecipação.

- [ ] **Step 3: Verificar que a instalação limpa resolve**

Run: `python -m pip install --dry-run -r requirements.txt`
Expected: sai sem erro, indicando `websockets==16.0` já satisfeito ou instalável.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore(deploy): requirements.txt com a unica dependencia de runtime"
```

---

### Task 2: Porta de escuta lê `PORT` além de `LFH_PORT`

Plataformas PaaS injetam a porta na variável `PORT`. Hoje o servidor só lê `LFH_PORT`, então subiria em 8765 e a plataforma não acharia o processo.

**Files:**
- Create: `tools/test_deploy_config.py`
- Modify: `server.py:34914-34917`

- [ ] **Step 1: Escrever o teste que falha**

Create `tools/test_deploy_config.py`:

```python
"""Configuração de escuta para deploy. Roda da raiz: python tools/test_deploy_config.py"""
import sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    # [1] porta de escuta
    print("\n[1] _listen_port — precedência e sanidade")
    check("sem env nenhuma → 8765 (o padrão do jogo em casa)",
          S._listen_port({}) == 8765)
    check("PORT injetada pela plataforma vale",
          S._listen_port({"PORT": "10000"}) == 10000)
    check("LFH_PORT (testes locais) vale",
          S._listen_port({"LFH_PORT": "9999"}) == 9999)
    check("LFH_PORT vence PORT — teste local não é sequestrado pela plataforma",
          S._listen_port({"LFH_PORT": "9999", "PORT": "10000"}) == 9999)
    check("espaços em volta não quebram",
          S._listen_port({"PORT": "  10000  "}) == 10000)
    check("valor não numérico cai no padrão em vez de estourar",
          S._listen_port({"PORT": "lixo"}) == 8765)
    check("string vazia cai no padrão",
          S._listen_port({"PORT": ""}) == 8765)
    check("porta 0 é recusada",
          S._listen_port({"PORT": "0"}) == 8765)
    check("porta acima de 65535 é recusada",
          S._listen_port({"PORT": "70000"}) == 8765)
    check("PORT inválida não impede LFH_PORT válida de valer",
          S._listen_port({"LFH_PORT": "lixo", "PORT": "10000"}) == 10000)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_deploy_config.py`
Expected: FALHA com `AttributeError: module 'server' has no attribute '_listen_port'`

- [ ] **Step 3: Implementar**

Em `server.py`, substituir as linhas 34914–34917:

```python
# Porta e enderecos de escuta. Duas familias de proposito: ver o comentario do
# websockets.serve() em main(). LFH_PORT existe para os testes subirem o
# servidor numa porta propria, sem brigar com o jogo em 8765.
SERVER_PORT = int(os.environ.get("LFH_PORT", "8765"))
```

por:

```python
# Porta e enderecos de escuta. Sao FUNCOES, e nao constantes de modulo, porque
# tools/test_deploy_config.py precisa exercitar as precedencias sem mexer em
# os.environ antes do import -- os testes fazem "import server as S", entao uma
# constante avaliada no carregamento so seria testavel com efeito colateral.
def _listen_port(env=None):
    """Porta de escuta.

    LFH_PORT (os testes locais sobem numa porta propria, sem brigar com o jogo
    em 8765) vence PORT (injetada pelas plataformas de hospedagem). Sem nenhuma
    das duas, 8765 -- o padrao do jogo em casa, que iniciar.bat abre.

    Valor invalido e IGNORADO em vez de estourar: um PORT com lixo derrubaria o
    processo no boot, e na plataforma isso aparece como 'deploy falhou' sem
    dizer por que."""
    env = os.environ if env is None else env
    for chave in ("LFH_PORT", "PORT"):
        bruto = env.get(chave)
        if bruto is None:
            continue
        try:
            porta = int(str(bruto).strip())
        except ValueError:
            continue
        if 1 <= porta <= 65535:
            return porta
    return 8765

SERVER_PORT = _listen_port()
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_deploy_config.py`
Expected: `=== 10 passaram, 0 falharam ===`

- [ ] **Step 5: Regressão — o servidor ainda sobe na porta dos testes**

Run: `python tools/test_rede_local.py`
Expected: PASS em todas as seções, `FAIL=0`. Este teste sobe o `server.py` num subprocesso com `LFH_PORT` e mede IPv4, IPv6 e `localhost` — é a prova de que a mudança não quebrou o boot.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_deploy_config.py
git commit -m "feat(deploy): porta de escuta le PORT alem de LFH_PORT"
```

---

### Task 3: Endereços de escuta escolhidos por plataforma, com válvula de escape

`SERVER_HOSTS = ["0.0.0.0", "::"]` existe por causa do Windows: lá o socket IPv6 não aceita IPv4 (`IPV6_V6ONLY` ligado por padrão), então escutar só em `::` deixaria `127.0.0.1` sem servidor — foi o que causou os ~207 ms de fallback que o `test_rede_local.py` trava.

No Linux o padrão é `bindv6only=0`: um socket em `::` já atende IPv4 mapeado, e ligar nas **duas** famílias no mesmo port pode falhar com `EADDRINUSE`. É exatamente a suposição que o spike existe para testar.

**Files:**
- Modify: `server.py:34918-34920`
- Modify: `tools/test_deploy_config.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_deploy_config.py`, inserir antes do `print(f"\n=== {PASS} passaram...")`:

```python
    # [2] endereços de escuta
    print("\n[2] _listen_hosts — padrão por plataforma e válvula de escape")
    check("Windows liga nas DUAS famílias (IPV6_V6ONLY: '::' não cobre 127.0.0.1)",
          S._listen_hosts({}, "win32") == ["0.0.0.0", "::"])
    check("Linux liga só em '::' (bindv6only=0 já cobre IPv4 mapeado)",
          S._listen_hosts({}, "linux") == ["::"])
    check("darwin segue a regra do não-Windows",
          S._listen_hosts({}, "darwin") == ["::"])
    check("LFH_HOSTS sobrepõe o padrão — contêiner sem IPv6",
          S._listen_hosts({"LFH_HOSTS": "0.0.0.0"}, "linux") == ["0.0.0.0"])
    check("LFH_HOSTS aceita lista com espaços",
          S._listen_hosts({"LFH_HOSTS": "0.0.0.0, ::"}, "linux") == ["0.0.0.0", "::"])
    check("LFH_HOSTS só com espaços cai no padrão da plataforma",
          S._listen_hosts({"LFH_HOSTS": "   "}, "win32") == ["0.0.0.0", "::"])
    check("LFH_HOSTS só com vírgulas cai no padrão da plataforma",
          S._listen_hosts({"LFH_HOSTS": " , , "}, "linux") == ["::"])
    check("sem argumento de plataforma usa sys.platform e devolve lista não vazia",
          isinstance(S._listen_hosts({}), list) and len(S._listen_hosts({})) >= 1)
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_deploy_config.py`
Expected: FALHA com `AttributeError: module 'server' has no attribute '_listen_hosts'`

- [ ] **Step 3: Implementar**

Em `server.py`, substituir as linhas 34918–34920:

```python
# Uma entrada por familia: no Windows o socket IPv6 nao aceita IPv4 por padrao
# (IPV6_V6ONLY), entao ligar so em "::" deixaria 127.0.0.1 sem servidor.
SERVER_HOSTS = ["0.0.0.0", "::"]
```

por:

```python
def _listen_hosts(env=None, plataforma=None):
    """Enderecos de escuta.

    WINDOWS liga nas DUAS familias: o socket IPv6 nao aceita IPv4 por padrao
    (IPV6_V6ONLY), entao escutar so em "::" deixaria 127.0.0.1 sem servidor. O
    nome "localhost" -- que e o que iniciar.bat abre -- resolveria primeiro para
    ::1, levaria recusa, e o navegador so entao cairia para 127.0.0.1: os ~207 ms
    perdidos antes do primeiro byte que o tools/test_rede_local.py trava.

    LINUX liga so em "::": o padrao do kernel e bindv6only=0, entao um socket em
    "::" ja atende IPv4 mapeado -- e ligar nas duas familias no mesmo port pode
    falhar com EADDRINUSE.

    LFH_HOSTS ("0.0.0.0" ou "0.0.0.0,::") sobrepoe tudo. E a valvula de escape
    para um conteiner sem IPv6, onde ligar em "::" falha no boot."""
    env = os.environ if env is None else env
    bruto = (env.get("LFH_HOSTS") or "").strip()
    if bruto:
        hosts = [h.strip() for h in bruto.split(",") if h.strip()]
        if hosts:
            return hosts
    plataforma = sys.platform if plataforma is None else plataforma
    if plataforma.startswith("win"):
        return ["0.0.0.0", "::"]
    return ["::"]

SERVER_HOSTS = _listen_hosts()
```

- [ ] **Step 4: Rodar para ver passar**

Run: `python tools/test_deploy_config.py`
Expected: `=== 18 passaram, 0 falharam ===`

- [ ] **Step 5: Regressão — o comportamento no Windows não pode mudar**

Run: `python tools/test_rede_local.py`
Expected: PASS em todas as seções, `FAIL=0`. Especificamente a seção `[2]` (`::1` aceita conexão) e a `[3]` (`localhost` conecta rápido) — são elas que provam que o ramo Windows continua ligando nas duas famílias.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_deploy_config.py
git commit -m "feat(deploy): enderecos de escuta por plataforma, com LFH_HOSTS de escape"
```

---

### Task 4: Medidor de cold start

O número que o spike existe para produzir. A documentação do Render diz "cerca de um minuto"; queremos o número **medido** com este módulo de 35.522 linhas e seus catálogos JSON.

Duas medidas separadas, porque têm causas diferentes: **conexão** (inclui acordar o contêiner) e **eco** (ida e volta com o servidor já quente — é latência de rede, não hibernação).

A sonda é `list_savegames`: sempre responde, não exige login e é **estritamente somente-leitura**. Verificado em execução: sem conta autenticada, `account["name"]` é `None`, `_norm_username(None)` devolve `""` e `list_savegames` retorna `[]` **antes** de entrar no laço — então nem chega no `write_savegame` que existe lá dentro. Nada é lido nem gravado em `savegames/`.

**Files:**
- Create: `tools/medir_cold_start.py`

- [ ] **Step 1: Criar o medidor**

```python
"""Mede o custo de acordar um servidor hospedado. Roda da raiz:

    python tools/medir_cold_start.py wss://SEU-SPIKE.onrender.com

Duas medidas, porque têm causas diferentes:
  conexao_s  tempo até o handshake do WebSocket fechar — INCLUI o cold start
  eco_s      ida e volta de uma mensagem com o servidor já quente — é rede

A sonda é `list_savegames`: sempre responde (`savegames_list`), não exige login
e não escreve nada no servidor.
"""
import asyncio, json, sys, time
import websockets

SONDA = json.dumps({"type": "list_savegames"})

async def medir(url):
    """Devolve (conexao_s, eco_s, tipo_da_resposta). Levanta em caso de falha."""
    t0 = time.monotonic()
    async with websockets.connect(url, open_timeout=300, ping_interval=None,
                                  max_size=34 * 1024 * 1024) as ws:
        conexao_s = time.monotonic() - t0
        t1 = time.monotonic()
        await ws.send(SONDA)
        bruto = await asyncio.wait_for(ws.recv(), timeout=60)
        eco_s = time.monotonic() - t1
    tipo = json.loads(bruto).get("type", "?")
    return conexao_s, eco_s, tipo

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    url = sys.argv[1]
    print(f"medindo {url}")
    try:
        conexao_s, eco_s, tipo = asyncio.run(medir(url))
    except Exception as e:
        print(f"  FALHOU: {type(e).__name__}: {e}")
        sys.exit(1)
    print(f"  conexao_s = {conexao_s:7.2f}   (inclui cold start)")
    print(f"  eco_s     = {eco_s:7.2f}   (rede, servidor ja quente)")
    print(f"  resposta  = {tipo}")
    if tipo != "savegames_list":
        print("  ATENCAO: resposta inesperada -- a sonda mudou?")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

> **A implementação final divergiu deste bloco, por causa da revisão.** Três mudanças,
> todas para proteger a medição que justifica o spike: (1) mede **duas conexões
> seguidas** — uma sozinha não distingue frio de quente, e o erro fácil seria registrar
> "cold start = 0,3 s" e concluir que a hibernação não é problema; a 2ª é o piso quente
> do mesmo serviço e a diferença é o cold start real, com aviso explícito quando dá
> perto de zero; (2) **repete até 4× no handshake** mantendo o cronômetro correndo,
> porque bordas de PaaS devolvem 502/503 ao upgrade enquanto a instância sobe e
> desistir queimaria o ciclo de hibernação sem produzir dado; (3) ganhou o preâmbulo
> `sys.stdout.reconfigure(encoding="utf-8")` do resto de `tools/` — sem ele, uma
> mensagem de `OSError` acentuada podia estourar dentro do próprio `except` e trocar o
> diagnóstico por um traceback. O `eco` passou a sair em milissegundos.
> Ver `tools/medir_cold_start.py` para o código vigente.

- [ ] **Step 2: Validar contra o servidor local, antes de existir qualquer nuvem**

Em um terminal:

```bash
python server.py
```

Em outro:

```bash
python tools/medir_cold_start.py ws://localhost:8765
```

Expected: `resposta = savegames_list`, com `conexao_s` e `eco_s` ambos abaixo de `0,10`. Se a resposta vier diferente, a sonda está errada e o medidor mediria a coisa errada na nuvem — conserte aqui, não lá.

- [ ] **Step 3: Parar o servidor local**

Ctrl+C no terminal do `server.py`. **Isto é obrigatório:** o repositório já registrou que um servidor rodando trava a escrita de `server.py` no Windows (`OSError: Errno 22`).

- [ ] **Step 4: Commit**

```bash
git add tools/medir_cold_start.py
git commit -m "feat(deploy): medidor de cold start via sonda list_savegames"
```

---

### Task 5: Config do serviço e branch do spike

**Files:**
- Create: `render.yaml`

- [ ] **Step 1: Criar a branch do spike**

```bash
git checkout -b spike/deploy-render
```

A branch isola o experimento. Nada daqui é mergeado sem passar pelo SP1.

- [ ] **Step 2: Criar `render.yaml`**

```yaml
# Config DESCARTAVEL do spike SP0. Removida na Task 7, junto com o servico.
# Ver docs/superpowers/specs/2026-08-28-hospedagem-online-design.md
services:
  - type: web
    name: lfh-spike
    runtime: python
    plan: free
    branch: spike/deploy-render
    buildCommand: pip install -r requirements.txt
    startCommand: python server.py
    # LFH_HOSTS fica DE FORA de proposito: o spike existe para descobrir se o
    # padrao do Linux ("::") funciona neste conteiner. Se o bind falhar, a
    # Task 6 manda acrescentar LFH_HOSTS=0.0.0.0 e reimplantar -- e esse e um
    # dos resultados que o spike procura.
    envVars:
      - key: PYTHON_VERSION
        value: "3.13.4"
```

**Sobre `PYTHON_VERSION`:** o ambiente local é 3.14.5. Fixar 3.13.4 é deliberado — se o `server.py` não importar sob 3.13, isso é um achado do spike (a plataforma pode não oferecer 3.14) e vira restrição do SP4. Não "conserte" mudando o código: **registre**.

- [ ] **Step 3: Commit**

```bash
git add render.yaml
git commit -m "chore(spike): render.yaml descartavel para o SP0"
```

- [ ] **Step 4: Pedir autorização e empurrar**

**PARE.** Isto publica código num repositório remoto. Confirme com o autor (pré-requisito P2) antes de rodar:

```bash
git push -u origin spike/deploy-render
```

---

### Task 6: Subir e medir

Esta task é **procedimento, não código**, e exige o autor no teclado (interface do Render, OAuth). Registre cada número — impressões não servem.

- [ ] **Step 1: Criar o serviço**

No painel do Render: **New → Blueprint**, apontando para o repositório e a branch `spike/deploy-render`. O `render.yaml` preenche o resto.

Registre: **pediram cartão em algum momento?** Se sim, pare e avise — invalida a restrição de US$ 0.

- [ ] **Step 2: Registrar o resultado do build**

Do log de deploy, anote:
- versão do Python que a plataforma usou de fato
- se `pip install -r requirements.txt` resolveu `websockets==16.0`
- se o `import server` passou, ou o traceback exato se não passou

- [ ] **Step 3: Registrar o resultado do bind**

Se o log mostrar erro de bind (`EADDRINUSE`, `Cannot assign requested address`, ou o Render reclamando que não detectou porta aberta):

1. acrescente a variável de ambiente `LFH_HOSTS=0.0.0.0` no painel do serviço
2. reimplante
3. **anote que o padrão `["::"]` do Linux não serviu neste contêiner** — é uma restrição do SP4

Se subir de primeira, anote que `["::"]` funcionou.

- [ ] **Step 4: Medir com o servidor quente**

```bash
python tools/medir_cold_start.py wss://SEU-SPIKE.onrender.com
```

Expected: `resposta = savegames_list`. Anote `conexao_s` e `eco_s`.

Se falhar aqui mas a página abrir no navegador, o WebSocket não está passando — é o achado mais grave possível, porque é o requisito central. Anote o erro exato.

- [ ] **Step 5: Medir o cold start, três vezes**

Para cada uma das três medições:

1. deixe o serviço **mais de 15 minutos** sem nenhum tráfego — nada de abrir a URL no navegador, porque uma requisição HTTP já acorda o contêiner
2. rode `python tools/medir_cold_start.py wss://SEU-SPIKE.onrender.com`
3. anote a linha **`cold start`** (a diferença entre a 1ª e a 2ª conexão), e também as duas conexões

Se sair `ATENCAO: cold start perto de zero`, a medição **não vale** — o serviço estava acordado. Espere de novo. É por isso que o medidor faz duas conexões: sem a segunda, esse caso passaria despercebido como um cold start baixo.

Três medições porque uma só não distingue cold start de um pico de rede.

- [ ] **Step 6: Registrar memória em repouso**

No painel do Render, anote a memória usada com o serviço quente e ocioso. O plano free tem teto, e este módulo carrega catálogos grandes no import.

---

### Task 7: Registrar os resultados e destruir o serviço

O entregável do spike é o registro. O serviço é descartável; os números não.

**Files:**
- Create: `docs/superpowers/plans/2026-08-28-sp0-resultados.md`
- Delete: `render.yaml`

- [ ] **Step 1: Escrever o registro**

Create `docs/superpowers/plans/2026-08-28-sp0-resultados.md`, preenchendo com os números medidos na Task 6:

```markdown
# SP0 — Resultados medidos

**Data da medição:** <preencher>
**Plataforma:** Render free, plano `free`, branch `spike/deploy-render`

## Suposições testadas

| Suposição do spec | Resultado | Consequência |
|---|---|---|
| A plataforma roda este Python | <versão usada; import passou?> | <restrição para o SP4> |
| `["::"]` basta no Linux | <subiu de primeira? precisou de LFH_HOSTS?> | <default do SP4> |
| Cold start ~1 min é disfarçável | <3 medições de conexao_s> | <UX de warm-up do SP4> |
| Não pedem cartão | <sim/não> | <mantém ou invalida o US$ 0 estrito> |

## Medições

| Medida | Valor |
|---|---|
| conexao_s, servidor quente | |
| eco_s, servidor quente | |
| conexao_s, cold start #1 | |
| conexao_s, cold start #2 | |
| conexao_s, cold start #3 | |
| memória em repouso | |

## Veredito

<sucesso: seguir para SP1 — ou — falha: qual suposição caiu e o que muda no desenho>

## Achados para os sub-projetos seguintes

- **SP2:** hoje o serviço passa na detecção de porta do Render porque
  `process_request` responde a `GET /` com o `index.html`. Quando o SP2 remover o
  servir-estático, **isso quebra** — a plataforma precisa de alguma resposta HTTP
  para considerar o serviço vivo. O SP2 tem de manter um endpoint de health mínimo.
- <outros achados do log>
```

- [ ] **Step 2: Destruir o serviço no Render**

No painel: **Settings → Delete Service**. A regra de contenção do spike exige isto — o ambiente expõe os 17 handlers de escrita sem autenticação.

- [ ] **Step 3: Remover a config descartável**

```bash
git rm render.yaml
```

- [ ] **Step 4: Commit e voltar para a branch de trabalho**

```bash
git add docs/superpowers/plans/2026-08-28-sp0-resultados.md
git commit -m "docs(spike): resultados medidos do SP0 e remocao do render.yaml"
git checkout feat/instrumentos-bardo-fase5
```

As Tasks 1–4 (`requirements.txt`, as duas funções de escuta, o medidor) são úteis independentemente do resultado e serão levadas adiante pelo SP4. Só o `render.yaml` é descartado.

---

## Critérios de conclusão do SP0

- [ ] `python tools/test_deploy_config.py` → `18 passaram, 0 falharam`
- [ ] `python tools/test_rede_local.py` → `FAIL=0` (nenhuma regressão no Windows)
- [ ] `docs/superpowers/plans/2026-08-28-sp0-resultados.md` com **todos** os campos preenchidos por números medidos
- [ ] Serviço destruído no Render
- [ ] Veredito escrito: seguir para o SP1, ou qual suposição caiu

---

## Fora de escopo deste plano

Qualquer coisa que o spike revele e que não seja necessária para o processo subir. Em particular, **não conserte durante o SP0**:

- os 17 handlers de escrita sem autenticação → **SP1**
- rate-limit e lockout no login, PIN mais forte, PBKDF2 fora do loop de eventos → **SP1**
- validação de `Origin` → **SP1**
- salas vazias em `rooms` e os 745 arquivos em `groups/` → **SP1**
- remover o servir-estático e apontar o cliente para outro host → **SP2**
- trocar arquivo por Postgres → **SP3**
- UX de warm-up e health check → **SP4**
