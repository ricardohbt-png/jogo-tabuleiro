"""SP3 — persistência. Roda da raiz: python tools/test_persistencia.py

Contas, jogos salvos e grupos precisam sobreviver ao redeploy. No plano gratuito
o disco é efêmero, então a fonte de verdade em execução passa a ser um cache em
memória (1,3 MB, cabe com folga) e o armazenamento é alcançado depois.
"""
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
    loja = S.LojaDocumentos(S.AdaptadorArquivo(tmp))
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
        # O diretorio mantem o nome ANTIGO de proposito: o .gitignore aponta
        # para accounts/, savegames/ e groups/, e renomear orfanaria a regra.
        check("gravou em accounts/, o nome que o .gitignore já conhece",
              os.path.exists(os.path.join(tmp, "accounts", "ana.json")))

        loja2 = S.LojaDocumentos(S.AdaptadorArquivo(tmp))
        loja2.carregar()
        check("outra loja sobre o mesmo diretório vê o que a primeira gravou",
              loja2.ler("contas", "ana") == {"username": "ana", "x": 1})

        loja.apagar("contas", "ana")
        check("apagar some do cache na hora", loja.ler("contas", "ana") is None)
        loja.descarregar()
        check("apagar some do disco",
              not os.path.exists(os.path.join(tmp, "accounts", "ana.json")))

        check("ler chave inexistente devolve None",
              loja.ler("contas", "ninguem") is None)
        check("ler coleção inexistente não estoura",
              loja.ler("inventada", "x") is None)

        check("as três coleções existem", set(S.COLECOES) ==
              {"contas", "savegames", "grupos"})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def secao_contas():
    print("\n[2] contas saem do disco e vão para a loja")
    import asyncio
    tmp = tempfile.mkdtemp(); velho = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        acc, err = asyncio.run(S.create_account("ana", "senha bem longa"))
        check("cria conta", acc is not None, str(err))
        check("a conta está na loja", S.LOJA.ler("contas", "ana") is not None)
        check("load_account lê da loja (e normaliza o apelido)",
              S.load_account("ANA") is not None)
        # Conta é IDENTIDADE: write_account agenda a descarga na hora, em vez de
        # esperar um ponto seguro do jogo. Perder uma significaria o jogador não
        # conseguir entrar — e write_account é raro (criação e migração de
        # perfil), então não acorda o banco à toa.
        S.LOJA.descarregar()
        check("a conta chega ao disco sem esperar ponto seguro do jogo",
              os.path.exists(os.path.join(tmp, "accounts", "ana.json")))

        check("conta inexistente devolve None", S.load_account("fantasma") is None)
        check("apelido inválido devolve None", S.load_account("../evil") is None)

        # o que prova a persistencia: uma loja NOVA sobre o mesmo diretorio
        S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
        check("uma loja nova (como se o processo tivesse reiniciado) acha a conta",
              S.load_account("ana") is not None)
    finally:
        S.LOJA = velho; shutil.rmtree(tmp, ignore_errors=True)


def secao_grupos():
    print("\n[3] grupos")
    tmp = tempfile.mkdtemp(); velho = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        g = S.create_group("Meu Grupo", "ana")
        check("cria grupo", isinstance(g, dict) and bool(g.get("id")))
        check("grupo está na loja", S.LOJA.ler("grupos", g["id"]) is not None)
        check("load_group lê da loja", S.load_group(g["id"]) is not None)
        check("id inválido devolve None", S.load_group("nao_e_id") is None)
        check("id válido inexistente devolve None",
              S.load_group("grp_zzzzzz") is None)

        # _new_group_id usava os.path.exists: o id so iria a disco na descarga,
        # entao dois grupos da MESMA sessao poderiam colidir.
        ids = {S.create_group(f"G{i}", "ana")["id"] for i in range(20)}
        check("20 grupos seguidos têm ids distintos (id livre vem do cache)",
              len(ids) == 20)

        S.LOJA.descarregar()
        S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
        check("depois de reiniciar, o grupo continua lá",
              S.load_group(g["id"]) is not None)
    finally:
        S.LOJA = velho; shutil.rmtree(tmp, ignore_errors=True)


def secao_savegames():
    print("\n[4] savegames")
    tmp = tempfile.mkdtemp(); velho = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        sg = S.create_savegame("Campanha", "ana", "campaign", "c.json", False)
        sid = sg["id"]
        check("cria savegame", S.load_savegame(sid) is not None)
        check("está na loja", S.LOJA.ler("savegames", sid) is not None)
        check("list_savegames acha o jogo da conta",
              any(x.get("id") == sid for x in S.list_savegames("ana")))
        check("list_savegames NÃO vaza para outra conta", not S.list_savegames("beto"))
        check("id inválido devolve None", S.load_savegame("../fora") is None)

        # o que o SP3 existe para garantir
        S.LOJA.descarregar()
        S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
        recarregado = S.load_savegame(sid)
        check("depois de reiniciar, o savegame continua lá", recarregado is not None)
        check("e com o conteúdo certo",
              (recarregado or {}).get("name") == "Campanha")

        S.delete_savegame(sid, "ana")
        check("apagar some da loja", S.load_savegame(sid) is None)
    finally:
        S.LOJA = velho; shutil.rmtree(tmp, ignore_errors=True)


def secao_sem_disco():
    """[5] ninguém pode ler o disco pelas costas da loja.

    Com o cache como fonte de verdade, um caminho que ainda abra o arquivo
    direto passa a ler **dado velho** — e isso não estoura, só devolve o errado.
    É o tipo de defeito que só aparece semanas depois, como "o jogo esqueceu
    minha compra".
    """
    print("\n[5] ninguém lê o disco pelas costas da loja")
    import re
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonte = open(os.path.join(raiz, "server.py"), encoding="utf-8").read()
    padroes = {
        "open() num caminho de dados":
            r"open\([^)]*(?:account_path|group_path|savegame_path)",
        "listdir num diretório de dados":
            r"os\.listdir\([^)]*(?:ACCOUNTS_DIR|SAVEGAMES_DIR|GROUPS_DIR)",
        "exists/isdir num caminho de dados":
            r"os\.path\.(?:exists|isdir)\([^)]*(?:account_path|group_path|"
            r"savegame_path|ACCOUNTS_DIR|SAVEGAMES_DIR|GROUPS_DIR)",
    }
    for rotulo, p in padroes.items():
        achados = re.findall(p, fonte)
        check(f"nenhum {rotulo} ({achados or 'nenhum'})", not achados,
              "com o cache como fonte de verdade, isso leria dado VELHO em silêncio")

    check("as funções de caminho estão marcadas como legado",
          fonte.count("LEGADO. A partir do SP3") == 3,
          "elas divergem do adaptador e enganam quem as usar como sonda")


def main():
    secao_loja()
    secao_contas()
    secao_grupos()
    secao_savegames()
    secao_sem_disco()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
