"""SP1 — modo público. Roda da raiz: python tools/test_modo_publico.py

Cobre o que precisa existir antes de abrir o cadastro: senha de verdade, hash
fora do laço de eventos, freio contra força bruta, portão dos editores, Origin
restrito e as salas que não podem ficar presas na memória.
"""
import asyncio, os, shutil, sys, tempfile, time
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(nome, cond, dica=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  [ok] {nome}")
    else:    FAIL += 1; print(f"  [FALHA] {nome}" + (f" -- {dica}" if dica else ""))


async def secao_senha():
    """[1] senha substitui o PIN.

    É `async` porque create_account virou corrotina na Task 4 (o PBKDF2 foi para
    uma thread). Chamá-la sem `await` devolveria um objeto corrotina em vez do
    par (conta, erro) — e as checagens virariam falso-positivo SILENCIOSO, não
    erro.
    """
    print("\n[1] senha substitui o PIN")
    tmp = tempfile.mkdtemp(); velho = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    try:
        acc, err = await S.create_account("jogador", "1234")
        check("PIN de 4 dígitos é RECUSADO", acc is None and err, f"aceitou: {acc}")

        acc, err = await S.create_account("jogador", "curta1")
        check("senha de 6 caracteres é recusada", acc is None and err)

        acc, err = await S.create_account("jogador", "cavalo bateria grampo")
        check("senha longa com espaços é aceita", acc is not None, str(err))
        check("o campo gravado se chama password_hash",
              acc is not None and "password_hash" in acc and "pin_hash" not in acc)

        acc2, err2 = await S.create_account("jogador2", "12345678")
        check("8 caracteres é o mínimo, e passa", acc2 is not None, str(err2))

        check("verify_password aceita a senha certa",
              S.verify_password("cavalo bateria grampo", acc["password_hash"]))
        check("verify_password recusa a errada",
              not S.verify_password("cavalo bateria grampos", acc["password_hash"]))
        check("verify_password recusa hash vazio",
              not S.verify_password("qualquer", ""))
    finally:
        S.ACCOUNTS_DIR = velho; shutil.rmtree(tmp, ignore_errors=True)


async def secao_laco():
    """[2] o hash não pode travar o laço de eventos."""
    print("\n[2] o hash não pode travar o laço de eventos")
    import inspect
    check("try_login é corrotina (pode aguardar a thread)",
          inspect.iscoroutinefunction(S.try_login))
    check("create_account é corrotina",
          inspect.iscoroutinefunction(S.create_account))

    tmp = tempfile.mkdtemp(); velho = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    try:
        await S.create_account("alvo", "senha bem longa")
        batendo = [True]; marcas = []

        async def pulso():
            # Se o laço travar, o intervalo entre pulsos estoura. É a medida
            # direta do que importa: enquanto alguém tenta senha, os OUTROS
            # jogadores continuam sendo atendidos?
            while batendo[0]:
                t = time.monotonic()
                await asyncio.sleep(0.005)
                marcas.append(time.monotonic() - t)

        p = asyncio.create_task(pulso())
        for _ in range(6):
            await S.try_login("pid-x", "alvo", "senha errada aqui")
        batendo[0] = False
        await p
        pior = max(marcas) if marcas else 9.99
        check(f"o laço nunca ficou preso (pior pausa {pior*1000:.0f} ms, teto 60 ms)",
              pior < 0.060,
              "o PBKDF2 está no laço: 6 tentativas travaram todos os jogadores")
    finally:
        S.ACCOUNTS_DIR = velho; shutil.rmtree(tmp, ignore_errors=True)


async def main():
    await secao_senha()
    await secao_laco()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
