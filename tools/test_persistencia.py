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


def main():
    secao_loja()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
