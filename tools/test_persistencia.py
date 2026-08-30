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
        check("nada foi a disco ainda — só na descarga",
              not os.path.exists(os.path.join(tmp, "accounts", "ana.json")))

        S.LOJA.descarregar()
        check("depois da descarga, está em disco",
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


def main():
    secao_loja()
    secao_contas()
    secao_grupos()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
