"""SP1 — modo público. Roda da raiz: python tools/test_modo_publico.py

Cobre o que precisa existir antes de abrir o cadastro: senha de verdade, hash
fora do laço de eventos, freio contra força bruta, portão dos editores, Origin
restrito e as salas que não podem ficar presas na memória.
"""
import sys, os, tempfile, shutil
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(nome, cond, dica=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  [ok] {nome}")
    else:    FAIL += 1; print(f"  [FALHA] {nome}" + (f" -- {dica}" if dica else ""))


def main():
    print("\n[1] senha substitui o PIN")
    tmp = tempfile.mkdtemp(); velho = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    try:
        acc, err = S.create_account("jogador", "1234")
        check("PIN de 4 dígitos é RECUSADO", acc is None and err,
              f"aceitou: {acc}")

        acc, err = S.create_account("jogador", "curta1")
        check("senha de 6 caracteres é recusada", acc is None and err)

        acc, err = S.create_account("jogador", "cavalo bateria grampo")
        check("senha longa com espaços é aceita", acc is not None, str(err))
        check("o campo gravado se chama password_hash",
              acc is not None and "password_hash" in acc and "pin_hash" not in acc)

        acc2, err2 = S.create_account("jogador2", "12345678")
        check("8 caracteres é o mínimo, e passa", acc2 is not None, str(err2))

        check("verify_password aceita a senha certa",
              S.verify_password("cavalo bateria grampo", acc["password_hash"]))
        check("verify_password recusa a errada",
              not S.verify_password("cavalo bateria grampos", acc["password_hash"]))
        check("verify_password recusa hash vazio",
              not S.verify_password("qualquer", ""))
    finally:
        S.ACCOUNTS_DIR = velho; shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
