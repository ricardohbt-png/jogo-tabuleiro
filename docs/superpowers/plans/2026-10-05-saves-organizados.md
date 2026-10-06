# Jogos salvos organizados — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cada jogo salvo vira um cartão único com capítulos e vários pontos de salvamento (automáticos rotativos + manuais), com "salvar e continuar jogando", carregar ponto anterior (só o anfitrião), arquivar e abas Solo/Multiplayer em "Meus Jogos".

**Architecture:** O documento do jogo (`savegames/<sid>`) continua sendo o estado vivo e ganha o **índice** `capitulos[].pontos[]`; o conteúdo de cada ponto vai para uma coleção nova da loja (`pontos`, chave `<sid>_<ptid>`) com a cópia de `CAMPOS_DO_PONTO`. Funções module-level no `server.py` (bloco dos jogos salvos) fazem registrar/carregar/apagar/capítulo/arquivar; a `GameRoom` só chama `_ponto_automatico` nos pontos de gravação que já existem. No cliente, `GS.agruparJogos` (puro, em `src/gameState.js`) decide abas/grupos e `game.js` desenha.

**Tech Stack:** Python 3 (`server.py`, aiohttp/WebSocket), JS vanilla (`src/gameState.js`, `game.js`), dicionários `src/lang/*.js`.

Spec: `docs/superpowers/specs/2026-10-05-saves-organizados-design.md`.

---

## Regras de trabalho neste repo (ler antes)

- **Trabalhe num worktree** a partir do `master` atual (o checkout principal tem trabalho em andamento do autor em `server.py`, `game.js`, `src/gameState.js`, `src/lang/*.js`): `git worktree add -b feat/saves-organizados ../jogo-tabuleiro-saves master`. A volta ao `master` é feita no fim por quem coordena (reaplicando o diff sobre o trabalho do autor), **não** por `git merge` com o checkout sujo.
- `server.py`, `game.js`, `src/gameState.js` e os `src/lang/*.js` usam **CRLF**. A ferramenta Edit normaliza o arquivo inteiro; se usá-la, confira depois que só as suas linhas mudaram (`git diff --stat` deve mostrar só as linhas esperadas). Script Python com `replace("...\n...")` não casa em CRLF.
- Rode Python com `PYTHONIOENCODING=utf-8` quando a saída for para pipe.
- Testes deste projeto são scripts: `python tools/<teste>.py` (sai 1 se houver ❌), `node tools/<teste>.js`.
- Texto novo que o jogador vê: chave `T("erro.<slug>")` no servidor e `t('ui.<…>')` no cliente, com `pt` e `en`. Nunca guarde `T(...)` em documento gravado em disco (o JSON da loja não serializa `T`) — guarde um **código** (`rotulo`) e traduza no cliente.
- Não faça push.

---

## Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `server.py` (bloco "Loja de documentos", ~1733) | `"pontos"` em `COLECOES` e em `_PASTA_DA_COLECAO` |
| `server.py` (bloco dos jogos salvos, após `list_savegames` ~2335) | constantes + `garantir_capitulos`, `capitulo_atual`, `registrar_ponto`, `carregar_ponto_no_jogo`, `apagar_ponto_do_jogo`, `try_carregar_ponto`, `try_apagar_ponto`, `try_novo_capitulo`, `try_arquivar_jogo`, `migrar_continuacoes_para_capitulos`; `list_savegames` e `delete_savegame` estendidos; `create_savegame` cria o capítulo 1 |
| `server.py` `ensure_campaign_schema` (~2135) | chama `garantir_capitulos` e garante `arquivado_por` |
| `server.py` `GameRoom` | `_ponto_automatico`, `handle_salvar_ponto`; ganchos em `_voltar_para_cidade`, `_gravar_foto_rodada`, `handle_salvar_e_sair` |
| `server.py` `handler` (~46757) e `MENSAGENS_DA_CONEXAO` (~46345) | despacho das 5 mensagens novas |
| `server.py` boot (~50591) | `migrar_continuacoes_para_capitulos()` depois de `LOJA.carregar()` |
| `.gitignore` | pasta `savegame_points/` |
| `src/lang/erros.js`, `src/lang/interface.js` | chaves novas |
| `src/gameState.js` | `agruparJogos`, `salvarPonto`, `carregarPonto`, `apagarPonto`, `novoCapitulo`, `arquivarJogo`, caso `ponto_salvo` |
| `game.js` | botão "💾 Salvar agora" no ⚙️; `_renderMeusJogos`/`_cartaoJogo`/`_rotuloPonto` substituem o laço de categorias do `savegamesList` |
| `tools/test_pontos_salvamento.py` (novo) | servidor |
| `tools/test_pontos_salvamento_cliente.js` (novo) | `agruparJogos` + fiação do cliente |
| `CLAUDE.md` | parágrafo da feature |

---

### Task 1: Coleção `pontos` + núcleo de capítulos e pontos

**Files:**
- Modify: `server.py` (`COLECOES`, `_PASTA_DA_COLECAO`, bloco após `list_savegames`, `create_savegame`)
- Modify: `.gitignore`
- Create: `tools/test_pontos_salvamento.py`

- [ ] **Step 1: Escrever o teste (seções [1]–[4])**

Crie `tools/test_pontos_salvamento.py`:

```python
"""Capítulos e pontos de salvamento. Roda da raiz: python tools/test_pontos_salvamento.py"""
import asyncio, sys, os, tempfile, shutil, copy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name} {extra}")

_PILHA = []
def loja_tmp():
    raiz = tempfile.mkdtemp()
    _PILHA.append((S.LOJA, raiz))
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(raiz))
    S.LOJA.carregar()
def loja_volta():
    loja, raiz = _PILHA.pop()
    S.LOJA = loja
    shutil.rmtree(raiz, ignore_errors=True)

def jogo(owner="ana", membros=("ana",), play_mode="solo", has_master=False):
    sg = S.create_savegame("Teste", owner, "procedural", None, has_master, play_mode=play_mode)
    for m in membros:
        sg["members"][m] = {"class_id": "warrior", "status": "active"}
    sg["characters"]["warrior"] = {"gold": 10}
    S.write_savegame(sg)
    return sg

def docs_de(sid):
    return [k for k in S.LOJA.listar("pontos") if k.startswith(sid + "_")]

def secao_nucleo():
    print("\n[1] Jogo novo nasce com o capítulo 1 vazio")
    sg = jogo()
    caps = sg.get("capitulos")
    check("um capítulo", isinstance(caps, list) and len(caps) == 1)
    check("capítulo 1 sem pontos", caps[0]["n"] == 1 and caps[0]["pontos"] == [])
    check("capitulo_atual = 1", sg.get("capitulo_atual") == 1)
    check("arquivado_por vazio", sg.get("arquivado_por") == [])

    print("\n[2] Automáticos rodam: ficam só os 3 mais recentes")
    ids = []
    for i in range(4):
        meta, e = S.registrar_ponto(sg, "auto", rotulo="cidade")
        ids.append(meta["id"])
    autos = [p for p in S.capitulo_atual(sg)["pontos"] if p["tipo"] == "auto"]
    check("3 automáticos no índice", len(autos) == 3, len(autos))
    check("o mais antigo saiu do índice", ids[0] not in [p["id"] for p in autos])
    check("e o documento dele foi apagado", len(docs_de(sg["id"])) == 3)
    check("o mais novo vem primeiro", autos[0]["id"] == ids[-1])

    print("\n[3] Manuais: teto de 10 por capítulo")
    for i in range(S.PONTOS_MANUAIS_MAX):
        meta, e = S.registrar_ponto(sg, "manual", nome=f"m{i}", por="ana")
        if e: break
    check("10 manuais aceitos", e is None)
    meta, e = S.registrar_ponto(sg, "manual", nome="demais", por="ana")
    check("o 11º é recusado", meta is None and e is not None)
    check("manual guarda nome e autor",
          any(p["nome"] == "m0" and p["por"] == "ana" for p in S.capitulo_atual(sg)["pontos"]))

    print("\n[4] O ponto é uma cópia profunda do estado")
    sg2 = jogo(owner="bia", membros=("bia",))
    meta, _ = S.registrar_ponto(sg2, "manual", nome="antes", por="bia")
    sg2["characters"]["warrior"]["gold"] = 999
    doc = S.LOJA.ler("pontos", f"{sg2['id']}_{meta['id']}")
    check("mudar o jogo não muda o ponto", doc["estado"]["characters"]["warrior"]["gold"] == 10)
    check("ponto lembra o capítulo", doc["capitulo"] == 1)
    check("local da cidade vem do nome do mundo", meta["onde"] == "cidade" and meta["local"] == "Alva e Luz")

def main():
    loja_tmp()
    try:
        secao_nucleo()
    finally:
        loja_volta()
    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: `❌ um capítulo` (e `AttributeError: module 'server' has no attribute 'registrar_ponto'`).

- [ ] **Step 3: Coleção nova na loja**

Em `server.py`, troque:

```python
COLECOES = ("contas", "savegames", "grupos")
```
por
```python
COLECOES = ("contas", "savegames", "grupos", "pontos")
```
e
```python
_PASTA_DA_COLECAO = {"contas": "accounts", "savegames": "savegames",
                     "grupos": "groups"}
```
por
```python
_PASTA_DA_COLECAO = {"contas": "accounts", "savegames": "savegames",
                     "grupos": "groups", "pontos": "savegame_points"}
```

No `.gitignore`, logo abaixo da linha `savegames/`, acrescente `savegame_points/`.

- [ ] **Step 4: Núcleo de capítulos e pontos**

Em `server.py`, logo **depois** da função `list_savegames` (e antes de `def delete_savegame`), insira:

```python
# ─── Capítulos e pontos de salvamento ─────────────────────────────────────────
# O documento do jogo é o estado VIVO ("Continuar" parte dele). Cada capítulo
# guarda só o ÍNDICE dos pontos; o conteúdo de cada ponto mora na coleção
# "pontos" (chave <sid>_<ptid>), para o histórico não pesar na gravação que a
# masmorra faz a cada rodada. Nada aqui grava T(...): o documento vai a disco;
# o texto do ponto automático é um código (`rotulo`) traduzido no cliente.
PONTOS_AUTO_MAX = 3
PONTOS_MANUAIS_MAX = 10
PONTO_AUTO_RODADAS = 5
# Tudo o que muda durante o jogo e precisa voltar ao carregar um ponto. É a
# mesma lista que a continuação copiava, mais o que o checkpoint grava.
CAMPOS_DO_PONTO = (
    "campaign_file", "campaign_phase", "world_location", "world_adventure_progress",
    "renome", "fatos", "scene_conversations_done", "scene_triggers_done",
    "story_beats_done", "active_scene", "scene_variables", "members",
    "characters", "slots", "shortcut_slots", "refugio", "hero_rooms",
    "dungeon_snapshot",
)


def _ponto_chave(sid, ptid):
    return f"{sid}_{ptid}"


def _new_ponto_id(sid):
    while True:
        ptid = "pt_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        if LOJA.ler("pontos", _ponto_chave(sid, ptid)) is None:
            return ptid


def _novo_capitulo_dict(n, nome, campaign_file):
    return {"n": n, "nome": str(nome or "")[:40], "campaign_file": campaign_file,
            "criado": _now_iso(), "pontos": []}


def capitulo_atual(sg):
    caps = sg.get("capitulos") or []
    if not caps:
        return None
    n = sg.get("capitulo_atual")
    return next((c for c in caps if c.get("n") == n), caps[-1])


def _local_do_estado(sg):
    """(onde, local, rodada) do estado vivo, para o índice do ponto."""
    foto = sg.get("dungeon_snapshot") or {}
    if foto.get("onde") == "masmorra":
        return "masmorra", foto.get("masmorra_nome") or "", foto.get("rodada")
    loc = sg.get("world_location") or ""
    nome = (WORLD_LOCATIONS.get(loc) or {}).get("nome") or loc
    return ("cidade_com_masmorra" if foto.get("onde") else "cidade"), nome, None


def _achar_ponto(sg, ptid):
    for cap in sg.get("capitulos") or []:
        for p in cap.get("pontos") or []:
            if p.get("id") == ptid:
                return cap, p
    return None, None


def garantir_capitulos(sg):
    """Jogo sem capítulos (salvo antes desta versão) ganha o capítulo 1 com um
    ponto automático do estado atual. Devolve True se mudou algo."""
    mudou = False
    if not isinstance(sg.get("arquivado_por"), list):
        sg["arquivado_por"] = []
        mudou = True
    if isinstance(sg.get("capitulos"), list) and sg["capitulos"]:
        return mudou
    sg["capitulos"] = [_novo_capitulo_dict(1, "", sg.get("campaign_file"))]
    sg["capitulo_atual"] = 1
    registrar_ponto(sg, "auto", rotulo="migrado")
    return True


def registrar_ponto(sg, tipo, nome=None, rotulo=None, por=None, preservar=None):
    """Copia o estado vivo do jogo num ponto novo do capítulo atual.
    tipo: "auto" (roda, fica só PONTOS_AUTO_MAX) ou "manual" (teto
    PONTOS_MANUAIS_MAX). `preservar` = id que a rotação não pode apagar.
    Não grava o jogo: quem chama faz write_savegame. Devolve (meta, erro)."""
    garantir_capitulos(sg)
    cap = capitulo_atual(sg)
    if tipo == "manual" and sum(1 for p in cap["pontos"]
                                if p.get("tipo") == "manual") >= PONTOS_MANUAIS_MAX:
        return None, T("erro.limite_de_pontos_manuais", n=PONTOS_MANUAIS_MAX)
    ptid = _new_ponto_id(sg["id"])
    onde, local, rodada = _local_do_estado(sg)
    meta = {"id": ptid, "tipo": tipo, "nome": str(nome or "")[:40], "rotulo": rotulo,
            "onde": onde, "local": local, "rodada": rodada,
            "criado": _now_iso(), "por": por}
    estado = {k: deepcopy(sg[k]) for k in CAMPOS_DO_PONTO if k in sg}
    LOJA.gravar("pontos", _ponto_chave(sg["id"], ptid),
                {"sid": sg["id"], "id": ptid, "capitulo": cap["n"], "estado": estado})
    cap["pontos"].insert(0, meta)
    if tipo == "auto":
        autos = [p for p in cap["pontos"] if p.get("tipo") == "auto" and p["id"] != preservar]
        for velho in autos[PONTOS_AUTO_MAX:]:
            cap["pontos"].remove(velho)
            LOJA.apagar("pontos", _ponto_chave(sg["id"], velho["id"]))
    return meta, None
```

Em `create_savegame`, no dicionário `sg = {...}`, logo depois de `"hero_rooms": {},` acrescente:

```python
        "capitulos": [_novo_capitulo_dict(1, "", campaign_file if is_campaign else None)],
        "capitulo_atual": 1,
        "arquivado_por": [],
```

(`garantir_capitulos` vê a lista e não cria ponto — um jogo novo não tem estado a guardar.)

- [ ] **Step 5: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: todas ✅ em [1]–[4], `0 falha(s)`.

- [ ] **Step 6: Commit**

```bash
git add server.py .gitignore tools/test_pontos_salvamento.py
git commit -m "feat(saves): capítulos e pontos de salvamento (núcleo e coleção pontos)"
```

---

### Task 2: Carregar, apagar, novo capítulo, arquivar (funções de conta)

**Files:**
- Modify: `server.py` (bloco da Task 1; `list_savegames`; `delete_savegame`)
- Modify: `src/lang/erros.js`
- Test: `tools/test_pontos_salvamento.py`

- [ ] **Step 1: Acrescentar as seções [5]–[9] ao teste**

Em `tools/test_pontos_salvamento.py`, acrescente esta função antes de `def main()` e chame-a em `main()` logo após `secao_nucleo()`:

```python
def secao_conta():
    print("\n[5] Carregar devolve o estado e guarda o de antes")
    sg = jogo()
    alvo, _ = S.registrar_ponto(sg, "auto", rotulo="cidade")      # gold 10
    S.registrar_ponto(sg, "auto", rotulo="cidade")
    S.registrar_ponto(sg, "auto", rotulo="cidade")                  # alvo é o mais antigo
    sg["characters"]["warrior"]["gold"] = 99
    sg["dungeon_snapshot"] = {"onde": "masmorra", "rodada": 3, "masmorra_nome": "Minas"}
    S.write_savegame(sg)
    ok, e = S.try_carregar_ponto("ana", sg["id"], alvo["id"])
    sg = S.load_savegame(sg["id"])
    check("carregou", ok, e)
    check("ouro voltou a 10", sg["characters"]["warrior"]["gold"] == 10)
    check("foto que não existia no ponto saiu", "dungeon_snapshot" not in sg)
    antes = next((p for p in S.capitulo_atual(sg)["pontos"] if p.get("rotulo") == "antes_de_carregar"), None)
    check("ponto 'antes de carregar' criado", antes is not None)
    doc = S.LOJA.ler("pontos", f"{sg['id']}_{antes['id']}")
    check("ele guarda o estado substituído (99)", doc["estado"]["characters"]["warrior"]["gold"] == 99)
    check("o ponto carregado não foi apagado pela rotação",
          S._achar_ponto(sg, alvo["id"])[1] is not None)

    print("\n[6] Só o anfitrião carrega/apaga; jogo aberto recusa")
    mp = jogo(owner="ana", membros=("ana", "bia"), play_mode="multiplayer")
    p, _ = S.registrar_ponto(mp, "manual", nome="x", por="bia"); S.write_savegame(mp)
    ok, e = S.try_carregar_ponto("bia", mp["id"], p["id"])
    check("convidado não carrega", not ok)
    ok, e = S.try_apagar_ponto("bia", mp["id"], p["id"])
    check("convidado não apaga", not ok)
    check("estranho não carrega", not S.try_carregar_ponto("zé", mp["id"], p["id"])[0])
    S.SAVEGAMES_IN_USE[mp["id"]] = "ABCD"
    try:
        check("jogo aberto recusa carregar", not S.try_carregar_ponto("ana", mp["id"], p["id"])[0])
    finally:
        S.SAVEGAMES_IN_USE.pop(mp["id"], None)
    ok, e = S.try_apagar_ponto("ana", mp["id"], p["id"])
    check("anfitrião apaga", ok and S._achar_ponto(S.load_savegame(mp["id"]), p["id"])[1] is None)
    check("documento do ponto apagado", S.LOJA.ler("pontos", f"{mp['id']}_{p['id']}") is None)
    com_mestre = jogo(owner="ana", membros=("bia",), play_mode="multiplayer", has_master=True)
    q, _ = S.registrar_ponto(com_mestre, "manual", nome="y"); S.write_savegame(com_mestre)
    check("com Mestre, o anfitrião é o Mestre", S._anfitriao_do_jogo(com_mestre) == "ana")

    print("\n[7] Novo capítulo no mesmo jogo")
    sg = jogo()
    sg["campaign_phase"] = 3
    sg["dungeon_snapshot"] = {"onde": "masmorra", "rodada": 2}
    S.write_savegame(sg)
    ok, e = S.try_novo_capitulo("ana", sg["id"], "Parte dois", None)
    sg = S.load_savegame(sg["id"])
    check("criou", ok, e)
    check("dois capítulos, atual = 2", len(sg["capitulos"]) == 2 and sg["capitulo_atual"] == 2)
    check("fase zerada e foto limpa", sg["campaign_phase"] == 0 and "dungeon_snapshot" not in sg)
    check("heróis mantidos", sg["characters"]["warrior"]["gold"] == 10)
    check("capítulo 1 fechou com 'fim do capítulo'",
          sg["capitulos"][0]["pontos"][0].get("rotulo") == "fim_capitulo")
    check("convidado não cria capítulo", not S.try_novo_capitulo("zé", sg["id"], "x", None)[0])

    print("\n[8] Arquivar é por conta")
    mp = jogo(owner="ana", membros=("ana", "bia"), play_mode="multiplayer")
    ok, e = S.try_arquivar_jogo("bia", mp["id"], True)
    check("arquivou", ok, e)
    da_bia = next(s for s in S.list_savegames("bia") if s["id"] == mp["id"])
    da_ana = next(s for s in S.list_savegames("ana") if s["id"] == mp["id"])
    check("para a bia está arquivado", da_bia["arquivado"] is True)
    check("para a ana não", da_ana["arquivado"] is False)
    check("lista leva anfitrião e capítulos",
          da_ana["anfitriao"] == "ana" and da_ana["capitulos"][0]["n"] == 1 and da_ana["capitulo_atual"] == 1)
    S.try_arquivar_jogo("bia", mp["id"], False)
    check("desarquivar volta", next(s for s in S.list_savegames("bia") if s["id"] == mp["id"])["arquivado"] is False)

    print("\n[9] Apagar o jogo apaga os pontos")
    sg = jogo()
    S.registrar_ponto(sg, "manual", nome="a"); S.write_savegame(sg)
    check("tem ponto", len(docs_de(sg["id"])) == 1)
    ok, _ = S.delete_savegame(sg["id"], "ana")
    check("apagou jogo e pontos", ok and docs_de(sg["id"]) == [])
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: `AttributeError: ... 'try_carregar_ponto'`.

- [ ] **Step 3: Implementar as funções de conta**

No `server.py`, logo após `registrar_ponto` (Task 1), acrescente:

```python
def _anfitriao_do_jogo(sg):
    """Quem gerencia pontos e capítulos: o Mestre num jogo com Mestre, senão o dono."""
    return sg.get("master_account") if sg.get("has_master") else sg.get("owner")


def _jogo_gerenciavel(conta, sid):
    """(sg, None) se `conta` pode gerenciar pontos/capítulos de `sid` agora;
    senão (None, erro). Exige o jogo FECHADO: uma sala aberta tem o mesmo dict
    em memória e sobrescreveria a mudança na próxima gravação."""
    conta = _norm_username(conta)
    sg = load_savegame(sid) if isinstance(sid, str) else None
    if not sg or not _conta_participa(sg, conta):
        return None, T("erro.jogo_salvo_indisponivel")
    if conta != _anfitriao_do_jogo(sg):
        return None, T("erro.so_o_anfitriao_gerencia_pontos")
    if sid in SAVEGAMES_IN_USE:
        return None, T("erro.feche_o_jogo_antes")
    garantir_capitulos(sg)
    return sg, None


def carregar_ponto_no_jogo(sg, ptid):
    """Copia o ponto para o estado vivo. O estado substituído vira o ponto
    automático "antes de carregar" (desfazível). Devolve o erro ou None."""
    cap, meta = _achar_ponto(sg, ptid)
    doc = LOJA.ler("pontos", _ponto_chave(sg["id"], ptid)) if meta else None
    if not doc:
        return T("erro.ponto_nao_encontrado")
    registrar_ponto(sg, "auto", rotulo="antes_de_carregar", preservar=ptid)
    estado = doc.get("estado") or {}
    for k in CAMPOS_DO_PONTO:
        if k in estado:
            sg[k] = deepcopy(estado[k])
        else:
            sg.pop(k, None)
    sg["capitulo_atual"] = doc.get("capitulo") or cap["n"]
    sg["status"] = "active"
    return None


def apagar_ponto_do_jogo(sg, ptid):
    cap, meta = _achar_ponto(sg, ptid)
    if not meta:
        return T("erro.ponto_nao_encontrado")
    cap["pontos"].remove(meta)
    LOJA.apagar("pontos", _ponto_chave(sg["id"], ptid))
    return None


def try_carregar_ponto(conta, sid, ptid):
    sg, e = _jogo_gerenciavel(conta, sid)
    if e:
        return False, e
    e = carregar_ponto_no_jogo(sg, ptid)
    if e:
        return False, e
    write_savegame(sg)
    return True, None


def try_apagar_ponto(conta, sid, ptid):
    sg, e = _jogo_gerenciavel(conta, sid)
    if e:
        return False, e
    e = apagar_ponto_do_jogo(sg, ptid)
    if e:
        return False, e
    write_savegame(sg)
    return True, None


def try_novo_capitulo(conta, sid, nome, campaign_file):
    """"Continuar em sequência" dentro do mesmo jogo: fecha o capítulo atual com
    um ponto e abre o próximo com a fase zerada, mantendo heróis e mundo."""
    sg, e = _jogo_gerenciavel(conta, sid)
    if e:
        return False, e
    if campaign_file and campaign_file not in {c["file"] for c in listar_campanhas()}:
        return False, T("erro.escolha_uma_campanha_valida")
    registrar_ponto(sg, "auto", rotulo="fim_capitulo")
    n = max(c["n"] for c in sg["capitulos"]) + 1
    arquivo = campaign_file or sg.get("campaign_file")
    sg["capitulos"].append(_novo_capitulo_dict(n, nome, arquivo))
    sg["capitulo_atual"] = n
    sg["campaign_file"] = arquivo
    sg["campaign_phase"] = 0
    sg.pop("dungeon_snapshot", None)
    sg["status"] = "active"
    sg.setdefault("journal", []).append({"at": _now_iso(), "kind": "chapter_created",
                                         "text": f"Capítulo {n}"})
    write_savegame(sg)
    return True, None


def try_arquivar_jogo(conta, sid, arquivado):
    """Arquivar esconde o jogo só para QUEM arquivou."""
    conta = _norm_username(conta)
    sg = load_savegame(sid) if isinstance(sid, str) else None
    if not sg or not _conta_participa(sg, conta):
        return False, T("erro.jogo_salvo_indisponivel")
    garantir_capitulos(sg)
    lista = sg["arquivado_por"]
    if arquivado and conta not in lista:
        lista.append(conta)
    elif not arquivado and conta in lista:
        lista.remove(conta)
    write_savegame(sg)
    return True, None
```

Em `list_savegames`, no `out.append({...})`, depois de `"foto": _resumo_foto(sg.get("dungeon_snapshot")),` acrescente:

```python
                "capitulos": [{"n": c.get("n"), "nome": c.get("nome", ""),
                               "pontos": list(c.get("pontos") or [])}
                              for c in sg.get("capitulos") or []],
                "capitulo_atual": sg.get("capitulo_atual", 1),
                "arquivado": u in (sg.get("arquivado_por") or []),
                "anfitriao": _anfitriao_do_jogo(sg),
```

Em `delete_savegame`, troque

```python
    LOJA.apagar("savegames", sid)
    return True, None
```
por
```python
    for cap in sg.get("capitulos") or []:
        for p in cap.get("pontos") or []:
            LOJA.apagar("pontos", _ponto_chave(sid, p.get("id")))
    LOJA.apagar("savegames", sid)
    return True, None
```

- [ ] **Step 4: Chaves de erro**

Em `src/lang/erros.js`, acrescente (mesmo formato das demais, `pt` e `en`, mantendo a ordem alfabética do arquivo se houver):

```js
  "erro.feche_o_jogo_antes": {
    "en": "Close this game first (everyone must leave it).",
    "pt": "Feche o jogo antes (todos precisam sair dele)."
  },
  "erro.jogo_salvo_indisponivel": {
    "en": "This saved game isn't available.",
    "pt": "Este jogo salvo não está disponível."
  },
  "erro.limite_de_pontos_manuais": {
    "en": "This chapter already has {n} manual saves. Delete one first.",
    "pt": "Este capítulo já tem {n} salvamentos manuais. Apague um antes."
  },
  "erro.ponto_nao_encontrado": {
    "en": "Save point not found.",
    "pt": "Ponto de salvamento não encontrado."
  },
  "erro.so_o_anfitriao_gerencia_pontos": {
    "en": "Only the host can load or delete save points and start chapters.",
    "pt": "Só o anfitrião carrega ou apaga pontos e cria capítulos."
  },
  "erro.escolha_uma_campanha_valida": {
    "en": "Choose a valid campaign.",
    "pt": "Escolha uma campanha válida."
  },
```

- [ ] **Step 5: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: [1]–[9] todas ✅.

- [ ] **Step 6: Commit**

```bash
git add server.py src/lang/erros.js tools/test_pontos_salvamento.py
git commit -m "feat(saves): carregar/apagar ponto, novo capítulo e arquivar por conta"
```

---

### Task 3: Migração dos jogos existentes

**Files:**
- Modify: `server.py` (`ensure_campaign_schema`; bloco da Task 1; boot ~`LOJA.carregar()`)
- Test: `tools/test_pontos_salvamento.py`

- [ ] **Step 1: Acrescentar a seção [10]**

Acrescente e chame em `main()` após `secao_conta()`:

```python
def secao_migracao():
    print("\n[10] Jogo antigo ganha capítulo 1 com 1 ponto, uma vez só")
    sg = jogo()
    for k in ("capitulos", "capitulo_atual", "arquivado_por"):
        sg.pop(k, None)
    S.write_savegame(sg)
    check("ensure migra", S.ensure_campaign_schema(sg) is True)
    pontos = sg["capitulos"][0]["pontos"]
    check("1 ponto 'migrado'", len(pontos) == 1 and pontos[0]["rotulo"] == "migrado")
    S.ensure_campaign_schema(sg)
    check("idempotente", len(sg["capitulos"]) == 1 and len(sg["capitulos"][0]["pontos"]) == 1)

    print("\n[11] Continuação antiga vira capítulo do jogo de origem")
    pai = jogo(owner="ana")
    filho = jogo(owner="ana")
    filho["parent_campaign_id"] = pai["id"]
    filho["characters"]["warrior"]["gold"] = 77
    S.registrar_ponto(filho, "manual", nome="do filho"); S.write_savegame(filho)
    orfao = jogo(owner="ana")
    orfao["parent_campaign_id"] = "sg_zzzzzz"; S.write_savegame(orfao)
    S.migrar_continuacoes_para_capitulos()
    pai = S.load_savegame(pai["id"])
    check("filho sumiu", S.load_savegame(filho["id"]) is None)
    check("pai tem 2 capítulos, atual = 2", len(pai["capitulos"]) == 2 and pai["capitulo_atual"] == 2)
    check("estado vivo do pai = o do filho", pai["characters"]["warrior"]["gold"] == 77)
    manual = next(p for p in pai["capitulos"][1]["pontos"] if p["nome"] == "do filho")
    doc = S.LOJA.ler("pontos", f"{pai['id']}_{manual['id']}")
    check("ponto do filho mudou de dono", doc is not None and doc["sid"] == pai["id"] and doc["capitulo"] == 2)
    check("nenhum documento do filho sobrou", docs_de(filho["id"]) == [])
    check("órfão ficou como jogo próprio", S.load_savegame(orfao["id"]) is not None)
    S.migrar_continuacoes_para_capitulos()
    check("rodar de novo não muda nada", len(S.load_savegame(pai["id"])["capitulos"]) == 2)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: `❌ ensure migra` e `AttributeError ... migrar_continuacoes_para_capitulos`.

- [ ] **Step 3: Implementar**

Em `ensure_campaign_schema`, troque o final

```python
    if "parent_campaign_id" not in sg:
        sg["parent_campaign_id"] = None; changed = True
    return changed
```
por
```python
    if "parent_campaign_id" not in sg:
        sg["parent_campaign_id"] = None; changed = True
    if garantir_capitulos(sg):
        changed = True
    return changed
```

(`garantir_capitulos` é definido mais abaixo no arquivo; tudo bem, é chamado só em runtime.)

No bloco da Task 1, ao final, acrescente:

```python
def migrar_continuacoes_para_capitulos():
    """Jogos criados por "Continuar em sequência" (antes desta versão) viram o
    capítulo seguinte do jogo de origem. O pai é gravado ANTES de o filho ser
    apagado. Pai inexistente ou de outro dono: o filho fica como jogo próprio.
    Roda no boot; idempotente (o filho some depois da 1ª vez)."""
    todos = LOJA.listar("savegames")
    for sid, filho in sorted(todos.items(), key=lambda kv: kv[1].get("created") or ""):
        if not _savegame_valid_shape(filho):
            continue
        pai_id = filho.get("parent_campaign_id")
        pai = load_savegame(pai_id) if pai_id else None
        if not pai or pai.get("owner") != filho.get("owner") or pai_id == sid:
            continue
        garantir_capitulos(pai)
        garantir_capitulos(filho)
        base = max(c["n"] for c in pai["capitulos"])
        renumero = {}
        for i, cap in enumerate(filho["capitulos"], start=1):
            renumero[cap["n"]] = base + i
            novo = dict(cap, n=base + i)
            novo["pontos"] = list(cap.get("pontos") or [])
            pai["capitulos"].append(novo)
        for cap in filho["capitulos"]:
            for p in cap.get("pontos") or []:
                doc = LOJA.ler("pontos", _ponto_chave(sid, p["id"]))
                if doc:
                    doc = dict(doc, sid=pai["id"], capitulo=renumero[cap["n"]])
                    LOJA.gravar("pontos", _ponto_chave(pai["id"], p["id"]), doc)
        for k in CAMPOS_DO_PONTO:
            if k in filho:
                pai[k] = deepcopy(filho[k])
            else:
                pai.pop(k, None)
        pai["capitulo_atual"] = renumero.get(filho.get("capitulo_atual"), base + len(filho["capitulos"]))
        pai["status"] = "active"
        write_savegame(pai)
        for cap in filho["capitulos"]:
            for p in cap.get("pontos") or []:
                LOJA.apagar("pontos", _ponto_chave(sid, p["id"]))
        LOJA.apagar("savegames", sid)
```

No boot, troque

```python
    LOJA.carregar()
    print(f"  dados: {sum(len(LOJA.listar(c)) for c in COLECOES)} documentos carregados")
```
por
```python
    LOJA.carregar()
    migrar_continuacoes_para_capitulos()
    _agendar_descarga()
    print(f"  dados: {sum(len(LOJA.listar(c)) for c in COLECOES)} documentos carregados")
```

Confira antes que `_agendar_descarga()` pode ser chamado fora de um laço rodando (leia a função em `server.py` ~1916). Se exigir laço, troque por `LOJA.descarregar()`.

- [ ] **Step 4: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: [1]–[11] todas ✅.

- [ ] **Step 5: Regressão das suítes de jogo salvo**

Run: `PYTHONIOENCODING=utf-8 python tools/test_savegames.py`, `python tools/test_salvar_masmorra.py`, `python tools/test_continuar_jogo.py`, `python tools/test_solo_grupo.py`
Expected: todas `0 falha(s)` (antes de mudar, rode-as uma vez no `master` para anotar vermelhas pré-existentes).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_pontos_salvamento.py
git commit -m "feat(saves): migra jogos antigos para capítulos e continuações para capítulos do jogo de origem"
```

---

### Task 4: Pontos automáticos e "salvar agora" na sala

**Files:**
- Modify: `server.py` (`GameRoom`: novo método perto de `_avisar_salvo` ~23136; `_voltar_para_cidade` ~23016; `_gravar_foto_rodada` ~23184; `handle_salvar_e_sair` ~23219; `handler` ~47318; `MENSAGENS_DA_CONEXAO` ~46345)
- Modify: `src/lang/erros.js`
- Test: `tools/test_pontos_salvamento.py`

- [ ] **Step 1: Acrescentar a seção [12] (assíncrona)**

```python
async def secao_sala():
    print("\n[12] Pontos gravados pela sala")
    sg = jogo(owner="ana")
    r = S.GameRoom("PONTO")
    enviados = []
    async def broadcast(msg, skip=None): enviados.append(msg)
    async def send_to(pid, msg): enviados.append(msg)
    async def push_state(): pass
    r.broadcast = broadcast; r.send_to = send_to; r.push_state = push_state
    r.savegame = sg; r.savegame_id = sg["id"]
    r.players["p0"] = S.make_player("p0", "Ana", "warrior", 0)
    r.player_order = ["p0"]; r.host_pid = "p0"; r.phase = "city"
    r.account_by_pid["p0"] = "ana"
    await r.enter_dungeon("p0")
    r._liberar_intro_masmorra(True)
    r._ultima_foto = None
    rotulos = lambda: [p.get("rotulo") for p in S.capitulo_atual(sg)["pontos"]]
    check("1ª foto da visita grava ponto de entrada", r._gravar_foto_rodada() and "entrada_masmorra" in rotulos())
    r.round_num = S.PONTO_AUTO_RODADAS
    r._gravar_foto_rodada()
    check("a cada 5 rodadas grava ponto 'rodada'", "rodada" in rotulos())
    r.round_num = S.PONTO_AUTO_RODADAS + 1
    antes = len(S.capitulo_atual(sg)["pontos"])
    r._gravar_foto_rodada()
    check("rodada que não é múltipla de 5 não grava ponto", len(S.capitulo_atual(sg)["pontos"]) == antes)
    await r.handle_salvar_ponto("p0", "Antes do Troll")
    manual = next((p for p in S.capitulo_atual(sg)["pontos"] if p["tipo"] == "manual"), None)
    check("salvar agora grava ponto manual com nome e autor",
          manual and manual["nome"] == "Antes do Troll" and manual["por"] == "ana")
    check("e responde ponto_salvo", any(m.get("type") == "ponto_salvo" for m in enviados))
    check("o ponto manual da masmorra guarda a rodada", manual["onde"] == "masmorra")
    await r.handle_salvar_e_sair("p0")
    check("salvar e sair grava ponto 'sair'", "sair" in rotulos())
    r.test_mode = True
    antes = len(S.capitulo_atual(sg)["pontos"])
    r._ponto_automatico("cidade")
    check("sala de teste não grava ponto", len(S.capitulo_atual(sg)["pontos"]) == antes)
```

Em `main()`, depois de `secao_migracao()`, acrescente `asyncio.run(secao_sala())`.

Antes de escrever, confira os nomes usados contra o código: `GameRoom.account_by_pid` (~10268), `_liberar_intro_masmorra` (procure `def _liberar_intro_masmorra`) e `round_num`. Ajuste o teste se algum diferir.

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: `❌ 1ª foto da visita grava ponto de entrada` e `AttributeError: ... handle_salvar_ponto`.

- [ ] **Step 3: Implementar na `GameRoom`**

Logo depois do método `_avisar_salvo`, acrescente:

```python
    def _ponto_automatico(self, rotulo):
        """Ponto automático do capítulo atual a partir do estado vivo JÁ gravado
        (chame depois do checkpoint/foto). Mesmas guardas da foto."""
        if self.savegame is None or getattr(self, "test_mode", False):
            return None
        meta, _ = registrar_ponto(self.savegame, "auto", rotulo=rotulo)
        write_savegame(self.savegame)
        _agendar_descarga()
        return meta

    async def handle_salvar_ponto(self, pid, nome):
        """"💾 Salvar agora": ponto manual sem sair. Na masmorra vale a foto do
        início da rodada (como no Salvar e sair), nunca o meio de uma ação."""
        if self.savegame is None:
            await self.send_to(pid, {"type": "error", "msg": T("erro.esta_partida_nao_tem_jogo_salvo")}); return
        if self.phase not in ("city", "playing"):
            await self.send_to(pid, {"type": "error", "msg": T("erro.so_da_para_salvar_em_jogo")}); return
        if self.phase == "playing" and self._ultima_foto is None:
            self._gravar_foto_rodada()
        self._checkpoint_savegame()
        meta, e = registrar_ponto(self.savegame, "manual",
                                  nome=str(nome or "").strip()[:40] or None,
                                  por=self.account_by_pid.get(pid))
        if e:
            await self.send_to(pid, {"type": "error", "msg": e}); return
        write_savegame(self.savegame)
        _agendar_descarga()
        await self.send_to(pid, {"type": "ponto_salvo", "ponto": meta})
```

Em `_gravar_foto_rodada`, troque

```python
        if primeira:
            self._avisar_salvo("masmorra")
        return True
```
por
```python
        if primeira:
            self._avisar_salvo("masmorra")
            self._ponto_automatico("entrada_masmorra")
        elif self.round_num % PONTO_AUTO_RODADAS == 0:
            self._ponto_automatico("rodada")
        return True
```

Em `_voltar_para_cidade`, troque o final

```python
        await self.broadcast_city_state()
        await self._trigger_campaign_scene("city_enter")
        self._checkpoint_savegame()
```
por
```python
        await self.broadcast_city_state()
        await self._trigger_campaign_scene("city_enter")
        self._checkpoint_savegame()
        self._ponto_automatico("cidade")
```

Em `handle_salvar_e_sair`, logo depois de `self._checkpoint_savegame()` acrescente `self._ponto_automatico("sair")`.

No `handler`, logo depois do ramo `elif t == "salvar_e_sair": ...`, acrescente:

```python
                elif t == "salvar_ponto":
                    if room: await room.handle_salvar_ponto(pid, msg.get("nome"))
```

Em `MENSAGENS_DA_CONEXAO`, acrescente `"salvar_ponto",` ao lado de `"salvar_e_sair",` (é a conexão que salva, não um herói).

Em `src/lang/erros.js`:

```js
  "erro.so_da_para_salvar_em_jogo": {
    "en": "You can only save during a game (town or dungeon).",
    "pt": "Só dá para salvar durante o jogo (cidade ou masmorra)."
  },
```

- [ ] **Step 4: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: [1]–[12] todas ✅.

- [ ] **Step 5: Regressão**

Run: `python tools/test_salvar_masmorra.py` (a seção [2] confere que a `GameRoom` não ganhou atributo sem categoria — este plano não cria nenhum), `python tools/test_continuar_jogo.py`, `python tools/test_handler_smoke.py`.
Expected: `0 falha(s)`.

- [ ] **Step 6: Commit**

```bash
git add server.py src/lang/erros.js tools/test_pontos_salvamento.py
git commit -m "feat(saves): pontos automáticos (entrada, a cada 5 rodadas, cidade, sair) e salvar agora"
```

---

### Task 5: Despacho das mensagens de conta no `handler`

**Files:**
- Modify: `server.py` (`handler`, depois do bloco `if t == "abandon_master_campaign": ... continue` ~46785; `MENSAGENS_DA_CONEXAO`)
- Test: `tools/test_pontos_salvamento.py`

- [ ] **Step 1: Teste estático da fiação**

Acrescente a `tools/test_pontos_salvamento.py` e chame em `main()`:

```python
def secao_fiacao():
    print("\n[13] Mensagens de conta despachadas no handler")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"),
               encoding="utf-8").read()
    for t, fn in (("carregar_ponto", "try_carregar_ponto"), ("apagar_ponto", "try_apagar_ponto"),
                  ("novo_capitulo", "try_novo_capitulo"), ("arquivar_jogo", "try_arquivar_jogo")):
        check(f"{t} → {fn}", f'"{t}"' in src and f"{fn}(account[\"name\"]" in src)
        check(f"{t} é mensagem da conexão", t in S.MENSAGENS_DA_CONEXAO)
    check("salvar_ponto é mensagem da conexão", "salvar_ponto" in S.MENSAGENS_DA_CONEXAO)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: `❌ carregar_ponto → try_carregar_ponto`.

- [ ] **Step 3: Implementar**

No `handler`, logo depois do bloco `if t == "abandon_master_campaign": ... continue`, acrescente:

```python
                if t in ("carregar_ponto", "apagar_ponto", "novo_capitulo", "arquivar_jogo"):
                    if t == "carregar_ponto":
                        ok, e = try_carregar_ponto(account["name"], msg.get("id"), msg.get("ponto_id"))
                    elif t == "apagar_ponto":
                        ok, e = try_apagar_ponto(account["name"], msg.get("id"), msg.get("ponto_id"))
                    elif t == "novo_capitulo":
                        ok, e = try_novo_capitulo(account["name"], msg.get("id"),
                                                  str(msg.get("nome") or "")[:40], msg.get("campaign_file"))
                    else:
                        ok, e = try_arquivar_jogo(account["name"], msg.get("id"), msg.get("arquivado") is True)
                    if ok:
                        _agendar_descarga()
                        await ws.send(json.dumps({"type": "savegames_list",
                                                  "savegames": list_savegames(account["name"]),
                                                  "campaigns": listar_campanhas()}))
                    else:
                        await err(e)
                    continue
```

Em `MENSAGENS_DA_CONEXAO`, acrescente `"carregar_ponto", "apagar_ponto", "novo_capitulo", "arquivar_jogo",`.

- [ ] **Step 4: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_pontos_salvamento.py`
Expected: todas ✅.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_pontos_salvamento.py
git commit -m "feat(saves): despacho de carregar/apagar ponto, novo capítulo e arquivar"
```

---

### Task 6: Cliente — estado e envio (`src/gameState.js`)

**Files:**
- Modify: `src/gameState.js` (funções perto de `createSavegame` ~3513; `case 'savegame_created'` ~2101; objeto exportado ~3655/3735)
- Create: `tools/test_pontos_salvamento_cliente.js`

- [ ] **Step 1: Teste node**

Crie `tools/test_pontos_salvamento_cliente.js`:

```js
// Agrupamento de "Meus Jogos" e fiação do cliente.
// Roda da raiz: node tools/test_pontos_salvamento_cliente.js
const fs = require('fs');
const path = require('path');
const gs = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');

let ok = 0, falhas = 0;
function check(nome, cond){ if(cond){ ok++; console.log('  ✅ ' + nome); } else { falhas++; console.log('  ❌ ' + nome); } }

function extrair(src, nome){
  const i = src.indexOf('function ' + nome + '(');
  if(i < 0) throw new Error('função não encontrada: ' + nome);
  let j = src.indexOf('{', i), prof = 0;
  for(; j < src.length; j++){ if(src[j] === '{') prof++; else if(src[j] === '}' && --prof === 0) break; }
  return src.slice(i, j + 1);
}
const agruparJogos = new Function(extrair(gs, 'agruparJogos') + '; return agruparJogos;')();

console.log('\n[1] Abas e grupos');
const lista = [
  { id: 'a', play_mode: 'solo', members: { ana: {} }, anfitriao: 'ana' },
  { id: 'b', play_mode: 'multiplayer', members: { ana: {}, bia: {} }, anfitriao: 'ana' },
  { id: 'c', play_mode: 'multiplayer', members: { ana: {}, bia: {} }, anfitriao: 'bia' },
  { id: 'd', play_mode: 'solo', members: { ana: {} }, anfitriao: 'ana', arquivado: true },
  { id: 'e', members: { ana: {}, bia: {} }, anfitriao: 'bia' },           // sem play_mode → multi
  { id: 'f', has_master: true, members: { ana: {} }, anfitriao: 'ana' },  // Mestre → multi
];
const g = agruparJogos(lista, 'ana');
check('solo: só os não arquivados', g.solo.ativos.map(s => s.id).join() === 'a');
check('solo: arquivados à parte', g.solo.arquivados.map(s => s.id).join() === 'd');
check('multi: que eu hospedo', g.multiplayer.hospedo.map(s => s.id).join() === 'b,f');
check('multi: que eu participo', g.multiplayer.participo.map(s => s.id).join() === 'c,e');
check('contagem da aba ignora arquivados', g.solo.total === 1 && g.multiplayer.total === 4);
check('lista vazia não quebra', agruparJogos(null, 'ana').solo.total === 0);

console.log('\n[2] Fiação');
for (const f of ['salvarPonto', 'carregarPonto', 'apagarPonto', 'novoCapitulo', 'arquivarJogo', 'agruparJogos'])
  check(`GS exporta ${f}`, new RegExp('\\b' + f + '\\b[,\\s]').test(gs.slice(gs.lastIndexOf('return {'))));
check("trata ponto_salvo", gs.includes("case 'ponto_salvo'"));
check('aba lembrada em lfh_aba_jogos', game.includes("'lfh_aba_jogos'"));
check('⚙️ tem Salvar agora', game.includes('cfg-salvar-ponto'));
check('render novo de Meus Jogos', game.includes('function _renderMeusJogos('));
check('continuação não cria jogo novo', !game.includes('continue_from: sg.id'));

console.log(`\n${ok} ok, ${falhas} falha(s)`);
process.exit(falhas ? 1 : 0);
```

Antes de rodar, confira como o `gameState.js` exporta (procure o objeto retornado/atribuído que lista `loginConta, criarConta, listSavegames, …` ~3655). Se não for `return {`, ajuste o `lastIndexOf` da checagem [2] para o início desse objeto.

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_pontos_salvamento_cliente.js`
Expected: `Error: função não encontrada: agruparJogos`.

- [ ] **Step 3: Implementar**

Em `src/gameState.js`, logo depois de `function deleteSavegame(id) { ... }` (~3517):

```js
  function salvarPonto(nome)              { send({ type: 'salvar_ponto', nome }); }
  function carregarPonto(id, ponto_id)    { send({ type: 'carregar_ponto', id, ponto_id }); }
  function apagarPonto(id, ponto_id)      { send({ type: 'apagar_ponto', id, ponto_id }); }
  function novoCapitulo(id, nome, campaign_file) { send({ type: 'novo_capitulo', id, nome, campaign_file }); }
  function arquivarJogo(id, arquivado)    { send({ type: 'arquivar_jogo', id, arquivado: !!arquivado }); }

  // "Meus Jogos": aba (solo/multiplayer) e grupo de cada jogo. Puro — o
  // renderer só desenha. Saves antigos sem play_mode: Mestre ou mais de um
  // membro = multiplayer (mesma regra do servidor).
  function agruparJogos(lista, conta) {
    const out = { solo: { ativos: [], arquivados: [], total: 0 },
                  multiplayer: { hospedo: [], participo: [], arquivados: [], total: 0 } };
    for (const sg of (lista || [])) {
      const membros = Object.keys(sg.members || {}).length;
      const tipo = (sg.play_mode === 'solo' || sg.play_mode === 'multiplayer') && !sg.has_master
        ? sg.play_mode
        : (sg.has_master || membros > 1 ? 'multiplayer' : 'solo');
      const g = out[tipo];
      if (sg.arquivado) { g.arquivados.push(sg); continue; }
      g.total++;
      if (tipo === 'solo') g.ativos.push(sg);
      else if (sg.anfitriao === conta) g.hospedo.push(sg);
      else g.participo.push(sg);
    }
    return out;
  }
```

No `switch` de mensagens, logo depois de `case 'savegame_created': ... break;`:

```js
      case 'ponto_salvo':
        // Resposta ao "💾 Salvar agora": o renderer confirma com um aviso.
        _emit('pontoSalvo', msg.ponto);
        break;
```

No objeto exportado, ao lado de `loginConta, criarConta, listSavegames, createSavegame, loadSavegame, deleteSavegame,` acrescente `salvarPonto, carregarPonto, apagarPonto, novoCapitulo, arquivarJogo, agruparJogos,`.

- [ ] **Step 4: Rodar (parcial)**

Run: `node tools/test_pontos_salvamento_cliente.js`
Expected: [1] e as checagens de `gameState.js` em [2] ✅; as de `game.js` ainda ❌ (Task 7).

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js tools/test_pontos_salvamento_cliente.js
git commit -m "feat(saves): cliente agrupa Meus Jogos e envia as mensagens de pontos"
```

---

### Task 7: Cliente — botão "Salvar agora" e tela "Meus Jogos"

**Files:**
- Modify: `game.js` (menu ⚙️ ~32578/32597/32604; `GS.on('savegamesList')` ~53011)
- Modify: `src/lang/interface.js`

- [ ] **Step 1: Botão no ⚙️**

Na montagem do menu, logo **antes** da linha que monta `'<button id="cfg-salvar-sair" ...'`, acrescente um botão irmão com o mesmo estilo:

```js
    +     '<button id="cfg-salvar-ponto" data-i18n="ui.menu.salvar_ponto" style="display:none;width:100%;padding:8px;margin-bottom:6px;background:rgba(20,48,30,.7);'
    +       'border:1px solid #6dbd8a88;border-radius:6px;color:#d7f8e0;font-family:inherit;font-size:.8rem;cursor:pointer;">'+t('ui.menu.salvar_ponto')+'</button>'
```

Onde o menu decide mostrar `#cfg-salvar-sair`, troque

```js
    if(salvarSair) salvarSair.style.display = (emJogo && estadoSala && estadoSala.tem_jogo_salvo) ? 'block' : 'none';
```
por
```js
    const podeSalvar = emJogo && estadoSala && estadoSala.tem_jogo_salvo;
    if(salvarSair) salvarSair.style.display = podeSalvar ? 'block' : 'none';
    const salvarPonto = wrap.querySelector('#cfg-salvar-ponto');
    if(salvarPonto) salvarPonto.style.display = podeSalvar ? 'block' : 'none';
```

Logo antes de `wrap.querySelector('#cfg-salvar-sair').onclick = () => {`, acrescente:

```js
  wrap.querySelector('#cfg-salvar-ponto').onclick = () => {
    pop.style.display='none';
    const gs = GS.gameState;
    const sugestao = gs
      ? t('ui.save.ponto.rodada', {local: gs.dungeon_name || t('ui.save.masmorra_generica'), n: Number(gs.round ?? gs.round_num ?? 1) || 1})
      : t('ui.save.ponto.cidade', {local: (GS.cityState && GS.cityState.world && GS.cityState.world.location_name) || ''});
    const nome = prompt(t('ui.save.nome_ponto_prompt'), sugestao);
    if (nome === null) return;
    GS.salvarPonto(nome);
  };
```

Confira os nomes `gs.dungeon_name` e `GS.cityState.world.location_name` no payload real (procure `"dungeon_name"` em `_game_state_payload` e o bloco `world` de `_city_state_payload` no `server.py`); use o campo que existir, ou deixe a sugestão sem local.

Perto dos outros `GS.on(...)` de salvamento (procure `GS.on('salvoParaSair'`), acrescente — cuidando para NÃO criar um segundo `GS.on('pontoSalvo'` (cada `GS.on` substitui o anterior):

```js
GS.on('pontoSalvo', (p) => {
  toast(t('ui.save.ponto_salvo', {nome: _rotuloPonto(p || {})}), 'var(--green)');
});
```

- [ ] **Step 2: Render de "Meus Jogos"**

No `GS.on('savegamesList', (list) => { ... })`, substitua o trecho que vai de

```js
  box.innerHTML = '';
  const porTipo = { solo: [], multiplayer: [] };
```
até o fim do laço
```js
    box.appendChild(secao);
  }
```
(inclusive) por:

```js
  _renderMeusJogos(box, list);
```

Mantenha o resto do handler (o preenchimento de `#sg-campaign` depois do laço). Antes do `GS.on('savegamesList'`, acrescente:

```js
let _abaJogos = (() => { try { return localStorage.getItem('lfh_aba_jogos') || 'solo'; } catch (e) { return 'solo'; } })();
const _jogosAbertos = new Set();   // cartões com os pontos expandidos

// Nome do ponto: o do jogador (manual) ou o código do automático traduzido.
function _rotuloPonto(p) {
  if (p.tipo === 'manual' && p.nome) return p.nome;
  return t('ui.save.ponto.' + (p.rotulo || 'migrado'),
           { local: p.local || t('ui.save.masmorra_generica'), n: p.rodada || 1 });
}

function _quandoJogo(iso) {
  try { return iso ? new Date(iso).toLocaleString() : ''; } catch (e) { return ''; }
}

function _btnJogo(rotulo, onclick, titulo) {
  const b = document.createElement('button');
  b.className = 'btn-secondary btn-sm';
  b.textContent = rotulo;
  if (titulo) b.title = titulo;
  b.onclick = onclick;
  return b;
}

function _linhaPonto(sg, p, podeGerir) {
  const li = document.createElement('div');
  li.className = 'savegame-ponto';
  li.style.cssText = 'display:flex;gap:6px;align-items:center;font-size:.72rem;padding:3px 0;';
  const nome = document.createElement('span');
  nome.style.flex = '1';
  nome.textContent = (p.tipo === 'manual' ? '🔖 ' : '🕑 ') + _rotuloPonto(p);
  const quando = document.createElement('span');
  quando.style.color = '#8ab88a';
  quando.textContent = _quandoJogo(p.criado);
  li.append(nome, quando);
  if (podeGerir) {
    li.appendChild(_btnJogo(t('ui.save.carregar'), () => {
      if (confirm(t('ui.save.carregar_confirm', {nome: _rotuloPonto(p)}))) GS.carregarPonto(sg.id, p.id);
    }));
    li.appendChild(_btnJogo('🗑', () => {
      if (confirm(t('ui.save.apagar_ponto_confirm', {nome: _rotuloPonto(p)}))) GS.apagarPonto(sg.id, p.id);
    }));
  }
  return li;
}

function _cartaoJogo(sg, redesenhar) {
  const conta = GS.getAccount();
  const anfitriao = sg.anfitriao === conta;
  const el = document.createElement('div');
  el.className = 'savegame-card';
  el.dataset.savegameId = sg.id;
  const resumo = document.createElement('div');
  const nome = document.createElement('b');
  nome.textContent = sg.name || t('ui.save.campanha');
  resumo.appendChild(nome);
  const meta = document.createElement('span');
  meta.style.cssText = 'display:block;font-size:.7rem;color:#8ab88a;';
  const membros = Object.keys(sg.members || {});
  meta.textContent = [
    t('ui.save.capitulo', {n: sg.capitulo_atual || 1}),
    membros.join(', '),
    (!anfitriao && sg.anfitriao) ? t('ui.save.anfitriao', {nome: sg.anfitriao}) : '',
    _quandoJogo(sg.updated),
  ].filter(Boolean).join(' · ');
  resumo.appendChild(meta);
  const local = document.createElement('span');
  local.innerHTML = _ondeParouHTML(sg.foto);
  resumo.appendChild(local);
  const encerrado = sg.status && sg.status !== 'active';
  if (encerrado) {
    const aviso = document.createElement('span');
    aviso.style.cssText = 'display:block;font-size:.7rem;color:#e8b66d;margin-top:3px;';
    aviso.textContent = t('ui.save.campanha_encerrada');
    resumo.appendChild(aviso);
  }
  const btns = document.createElement('div');
  btns.className = 'savegame-actions';
  const cont = _btnJogo(anfitriao || sg.play_mode === 'solo' ? t('ui.save.continuar') : t('ui.save.entrar'),
                        () => GS.loadSavegame(sg.id));
  cont.disabled = !!encerrado && !anfitriao;
  btns.appendChild(cont);
  const aberto = _jogosAbertos.has(sg.id);
  btns.appendChild(_btnJogo((aberto ? '▴ ' : '▾ ') + t('ui.save.pontos'), () => {
    if (aberto) _jogosAbertos.delete(sg.id); else _jogosAbertos.add(sg.id);
    redesenhar();
  }));
  if (anfitriao) {
    btns.appendChild(_btnJogo(t('ui.save.novo_capitulo'), () => {
      const n = (sg.capitulo_atual || 1) + 1;
      const nomeCap = prompt(t('ui.save.nome_capitulo_prompt'), t('ui.save.capitulo', {n}));
      if (nomeCap !== null) GS.novoCapitulo(sg.id, nomeCap, sg.campaign_file);
    }, t('ui.save.sequel_title')));
  }
  btns.appendChild(_btnJogo(sg.arquivado ? t('ui.save.desarquivar') : t('ui.save.arquivar'),
                            () => GS.arquivarJogo(sg.id, !sg.arquivado)));
  if (sg.has_master && sg.master_account === conta) {
    btns.appendChild(_btnJogo(t('ui.save.encerrar'), () => {
      if (confirm(t('ui.save.encerrar_confirm'))) GS.abandonMasterCampaign(sg.id);
    }, t('ui.save.encerrar_title')));
  }
  if (sg.owner === conta) {
    btns.appendChild(_btnJogo('🗑', () => {
      if (confirm(t('ui.save.apagar_confirm', {nome: sg.name}))) GS.deleteSavegame(sg.id);
    }));
  }
  el.appendChild(resumo); el.appendChild(btns);
  if (aberto) {
    const lista = document.createElement('div');
    lista.className = 'savegame-pontos';
    lista.style.cssText = 'width:100%;border-top:1px solid #2a4a2a;margin-top:6px;padding-top:4px;';
    const caps = (sg.capitulos || []).slice().sort((a, b) => b.n - a.n);
    for (const cap of caps) {
      const atual = cap.n === (sg.capitulo_atual || 1);
      const alvo = atual ? lista : document.createElement('details');
      if (!atual) {
        const s = document.createElement('summary');
        s.style.cssText = 'font-size:.72rem;color:#8ab88a;cursor:pointer;';
        s.textContent = t('ui.save.capitulo_anterior', {n: cap.n, q: (cap.pontos || []).length});
        alvo.appendChild(s);
        lista.appendChild(alvo);
      }
      if (!(cap.pontos || []).length && atual) {
        const v = document.createElement('div');
        v.style.cssText = 'font-size:.72rem;color:#8ab88a;';
        v.textContent = t('ui.save.sem_pontos');
        alvo.appendChild(v);
      }
      for (const p of cap.pontos || []) alvo.appendChild(_linhaPonto(sg, p, anfitriao));
    }
    el.appendChild(lista);
  }
  return el;
}

function _renderMeusJogos(box, list) {
  const g = GS.agruparJogos(list, GS.getAccount());
  const redesenhar = () => _renderMeusJogos(box, list);
  box.innerHTML = '';
  const abas = document.createElement('div');
  abas.className = 'savegames-tabs';
  abas.style.cssText = 'display:flex;gap:6px;margin-bottom:8px;';
  for (const [id, chave] of [['solo', 'ui.savegames.secao_solo'], ['multiplayer', 'ui.savegames.secao_multiplayer']]) {
    const b = _btnJogo(`${t(chave)} (${g[id].total})`, () => {
      _abaJogos = id;
      try { localStorage.setItem('lfh_aba_jogos', id); } catch (e) {}
      redesenhar();
    });
    b.dataset.aba = id;
    if (_abaJogos === id) { b.classList.add('ativa'); b.style.borderColor = '#e8d9a8'; b.style.color = '#e8d9a8'; }
    abas.appendChild(b);
  }
  box.appendChild(abas);
  if (!g[_abaJogos]) _abaJogos = 'solo';
  const aba = g[_abaJogos];
  const secao = document.createElement('section');
  secao.className = 'savegames-category';
  secao.dataset.playMode = _abaJogos;
  const grupos = _abaJogos === 'solo'
    ? [[null, aba.ativos]]
    : [['ui.savegames.grupo_hospedo', aba.hospedo], ['ui.savegames.grupo_participo', aba.participo]];
  if (!aba.total) {
    const vazio = document.createElement('div');
    vazio.style.cssText = 'color:#8ab88a;font-size:.78rem;padding:0 4px 4px;';
    vazio.textContent = t(_abaJogos === 'solo' ? 'ui.savegames.vazio_solo' : 'ui.savegames.vazio_multiplayer');
    secao.appendChild(vazio);
  }
  for (const [titulo, jogos] of grupos) {
    if (!jogos.length) continue;
    if (titulo) {
      const h = document.createElement('h3');
      h.style.cssText = 'margin:6px 0 2px;color:#d8c995;font-size:.85rem;';
      h.textContent = t(titulo);
      secao.appendChild(h);
    }
    for (const sg of jogos) secao.appendChild(_cartaoJogo(sg, redesenhar));
  }
  if (aba.arquivados.length) {
    const arq = document.createElement('details');
    const s = document.createElement('summary');
    s.style.cssText = 'font-size:.78rem;color:#8ab88a;cursor:pointer;margin-top:8px;';
    s.textContent = t('ui.savegames.arquivados', {n: aba.arquivados.length});
    arq.appendChild(s);
    for (const sg of aba.arquivados) arq.appendChild(_cartaoJogo(sg, redesenhar));
    secao.appendChild(arq);
  }
  box.appendChild(secao);
}
```

Atenção: dentro dessas funções o tradutor é `t`; não declare variável local chamada `t`.

- [ ] **Step 3: Chaves de interface**

Em `src/lang/interface.js` (mesmo formato do arquivo), acrescente:

```js
  "ui.menu.salvar_ponto": { "en": "💾 Save now", "pt": "💾 Salvar agora" },
  "ui.save.nome_ponto_prompt": { "en": "Name this save:", "pt": "Nome deste salvamento:" },
  "ui.save.ponto_salvo": { "en": "💾 Saved: {nome}", "pt": "💾 Salvo: {nome}" },
  "ui.save.entrar": { "en": "Join", "pt": "Entrar" },
  "ui.save.pontos": { "en": "Saves", "pt": "Salvamentos" },
  "ui.save.sem_pontos": { "en": "No saves yet in this chapter.", "pt": "Ainda não há salvamentos neste capítulo." },
  "ui.save.carregar": { "en": "Load", "pt": "Carregar" },
  "ui.save.carregar_confirm": { "en": "Load \"{nome}\"? The current state is kept as an automatic save.", "pt": "Carregar \"{nome}\"? O estado atual fica guardado como um salvamento automático." },
  "ui.save.apagar_ponto_confirm": { "en": "Delete the save \"{nome}\"?", "pt": "Apagar o salvamento \"{nome}\"?" },
  "ui.save.capitulo": { "en": "Chapter {n}", "pt": "Capítulo {n}" },
  "ui.save.capitulo_anterior": { "en": "Chapter {n} — {q} saves kept", "pt": "Capítulo {n} — {q} salvamentos guardados" },
  "ui.save.novo_capitulo": { "en": "New chapter", "pt": "Novo capítulo" },
  "ui.save.nome_capitulo_prompt": { "en": "Name of the new chapter:", "pt": "Nome do novo capítulo:" },
  "ui.save.anfitriao": { "en": "host: {nome}", "pt": "anfitrião: {nome}" },
  "ui.save.arquivar": { "en": "Archive", "pt": "Arquivar" },
  "ui.save.desarquivar": { "en": "Unarchive", "pt": "Desarquivar" },
  "ui.savegames.grupo_hospedo": { "en": "Games I host", "pt": "Que eu hospedo" },
  "ui.savegames.grupo_participo": { "en": "Games I'm in", "pt": "Que eu participo" },
  "ui.savegames.arquivados": { "en": "Archived ({n})", "pt": "Arquivados ({n})" },
  "ui.save.ponto.cidade": { "en": "Town · {local}", "pt": "Cidade · {local}" },
  "ui.save.ponto.cidade_com_masmorra": { "en": "Town · {local}", "pt": "Cidade · {local}" },
  "ui.save.ponto.entrada_masmorra": { "en": "Entering {local}", "pt": "Entrada · {local}" },
  "ui.save.ponto.rodada": { "en": "{local}, round {n}", "pt": "{local}, rodada {n}" },
  "ui.save.ponto.sair": { "en": "On leaving · {local}", "pt": "Ao sair · {local}" },
  "ui.save.ponto.antes_de_carregar": { "en": "Before loading", "pt": "Antes de carregar" },
  "ui.save.ponto.fim_capitulo": { "en": "End of chapter", "pt": "Fim do capítulo" },
  "ui.save.ponto.migrado": { "en": "Saved state", "pt": "Estado salvo" },
```

(Se o arquivo usa uma chave por bloco de várias linhas, siga esse formato. As chaves `ui.save.continuar`, `ui.save.campanha`, `ui.save.masmorra_generica`, `ui.savegames.secao_*`, `ui.savegames.vazio_*`, `ui.save.encerrar*`, `ui.save.apagar_confirm`, `ui.save.sequel_title`, `ui.save.campanha_encerrada` já existem.)

Remova as chaves que ficaram órfãs com a troca do botão de sequência (`ui.save.continuar_sequencia`, `ui.save.nome_nova_campanha`, `ui.save.sufixo_continuacao`) **só se** `grep` não achar outro uso em `game.js`/`src/`.

- [ ] **Step 4: Testes do cliente e de idioma**

Run: `node --check game.js && node tools/test_pontos_salvamento_cliente.js`
Expected: `0 falha(s)`.

Run: `PYTHONIOENCODING=utf-8 python tools/test_idioma.py`, `python tools/test_interface.py`, `node tools/test_idioma_cliente.js`, `python tools/dividas.py`
Expected: todas verdes; `dividas.py` sem dívida nova (compare com a saída no `master`).

- [ ] **Step 5: Commit**

```bash
git add game.js src/lang/interface.js
git commit -m "feat(saves): Meus Jogos com abas, cartão por jogo, pontos, capítulos e arquivar; Salvar agora no ⚙️"
```

---

### Task 8: Prova no navegador

**Files:** nenhum (só verificação). Use um servidor **isolado** do worktree numa porta livre (ex.: 8781), com dados copiados para uma pasta temporária, para não mexer nos saves do autor. Confira em `server.py` como a porta e a raiz de dados são escolhidas (procure `8765` e `BASE_DIR`); se não houver variável de ambiente, rode a cópia do worktree inteira numa pasta temporária.

- [ ] **Step 1:** Suba o servidor isolado e abra `http://localhost:8781/index.html?v=saves1` no navegador embutido (com `?v=` para fugir do cache).
- [ ] **Step 2:** Crie conta, crie um jogo **Solo**, entre na cidade, use "💾 Salvar agora" com nome "teste 1". Volte a Meus Jogos: aba Solo com 1 cartão; expandido mostra "teste 1" e "Cidade · Alva e Luz".
- [ ] **Step 3:** Entre numa masmorra, ande algumas rodadas, "Salvar e sair". Expandido: "Entrada · …", "Ao sair · …". Mude o ouro (compre algo), saia, carregue "teste 1", Continuar: ouro voltou; existe "Antes de carregar".
- [ ] **Step 4:** Crie um jogo **Multiplayer** com outra conta (segunda aba do navegador); confira "Que eu hospedo" numa conta e "Que eu participo" na outra; o convidado não vê "Carregar"/🗑. Arquive na conta convidada: some só para ela.
- [ ] **Step 5:** Novo capítulo: cartão continua único; "Capítulo 2"; o capítulo 1 aparece recolhido com "Fim do capítulo".
- [ ] **Step 6:** Troque o idioma para English no ⚙️ e confira os rótulos. Console sem erros (`read_console_messages` com `onlyErrors`).
- [ ] **Step 7:** Screenshot da tela final como prova.

---

### Task 9: Documentação

**Files:**
- Modify: `CLAUDE.md` (no fim do bloco "Foto da masmorra", antes de "Solo com grupo")

- [ ] **Step 1:** Acrescente o parágrafo:

```markdown
> **Capítulos e pontos de salvamento (2026-10-05):** cada jogo salvo é UM cartão em "Meus Jogos",
> com abas Solo | Multiplayer (`GS.agruparJogos`; aba em `localStorage["lfh_aba_jogos"]`) e, em
> Multiplayer, "Que eu hospedo"/"Que eu participo". O documento do jogo segue sendo o estado vivo e
> guarda só o ÍNDICE `capitulos[].pontos[]`; o conteúdo de cada ponto vai para a coleção `pontos`
> da loja (`<sid>_<ptid>`, pasta `savegame_points/`) com a cópia de `CAMPOS_DO_PONTO`. Automáticos
> (`registrar_ponto(..., "auto", rotulo=…)`) na 1ª foto de cada visita à masmorra, a cada
> `PONTO_AUTO_RODADAS` (5) rodadas, ao voltar à cidade e no "Salvar e sair"; ficam os 3 mais
> recentes por capítulo. Manuais: `salvar_ponto {nome}` ("💾 Salvar agora" no ⚙️), teto 10 por
> capítulo. Carregar/apagar ponto e "Novo capítulo" (o antigo "Continuar em sequência") só pelo
> cartão, com o jogo FECHADO (`SAVEGAMES_IN_USE`) e só pelo anfitrião (`_anfitriao_do_jogo`: Mestre
> se houver, senão o dono); carregar guarda o estado substituído como "Antes de carregar".
> Arquivar é por conta (`arquivado_por`). Documento gravado nunca leva `T(...)`: o automático guarda
> um `rotulo` traduzido no cliente (`ui.save.ponto.<rotulo>`). Migração: `garantir_capitulos` (em
> `ensure_campaign_schema`) dá capítulo 1 + ponto "migrado" a jogo antigo; no boot,
> `migrar_continuacoes_para_capitulos` funde continuações antigas no jogo de origem (pai gravado
> antes de o filho ser apagado). Fora de escopo: a Guilda segue por classe, sem voltar no tempo.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-10-05-saves-organizados*`. Testes:
> `tools/test_pontos_salvamento.py` e `tools/test_pontos_salvamento_cliente.js`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(saves): capítulos e pontos de salvamento no CLAUDE.md"
```

---

## Self-review (feito ao escrever)

- **Cobertura do spec:** modelo de dados (T1), automáticos/manuais (T1, T4), carregar com backup e permissões (T2), capítulos (T2), arquivar por conta (T2), lista estendida (T2), apagar pontos com o jogo (T2), migração + continuações (T3), handler (T4, T5), cliente/abas/cartão/⚙️ (T6, T7), idioma (T2, T4, T7), testes servidor/cliente/navegador (todas), CLAUDE.md (T9).
- **Desvio consciente do spec:** o teste ponta a ponta "pelo `server.handler` real" virou a prova no navegador (T8) + a checagem estática de despacho (T5); as funções de conta são testadas diretamente.
- **Nomes consistentes:** `registrar_ponto`, `capitulo_atual`, `garantir_capitulos`, `_achar_ponto`, `_anfitriao_do_jogo`, `_jogo_gerenciavel`, `try_carregar_ponto/try_apagar_ponto/try_novo_capitulo/try_arquivar_jogo`, `migrar_continuacoes_para_capitulos`, `_ponto_automatico`, `handle_salvar_ponto`; cliente `agruparJogos`, `salvarPonto`, `carregarPonto`, `apagarPonto`, `novoCapitulo`, `arquivarJogo`, `_renderMeusJogos`, `_cartaoJogo`, `_linhaPonto`, `_rotuloPonto`.
