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


def secao_limite():
    """[3] freio contra força bruta. Síncrono: as funções de limite não tocam
    em disco nem em hash, então não precisam de thread nem de await."""
    print("\n[3] limite de tentativas")
    S._LOGIN_TENTATIVAS.clear()

    ok, _ = S._login_permitido("ana", "1.1.1.1")
    check("contador zerado começa liberado", ok)

    for _ in range(S.LOGIN_MAX_TENTATIVAS):
        S._registrar_falha_login("ana", "1.1.1.1")
    ok, _ = S._login_permitido("ana", "1.1.1.1")
    check("após o teto de tentativas, é barrado", not ok)

    ok, _ = S._login_permitido("ana", "2.2.2.2")
    check("a MESMA conta é barrada mesmo vindo de outra origem", not ok,
          "senão trocar de IP anula o limite por conta")

    ok, _ = S._login_permitido("beto", "1.1.1.1")
    check("a MESMA origem é barrada mesmo para outra conta", not ok,
          "senão varrer muitas contas de um IP só anula o limite")

    S._LOGIN_TENTATIVAS.clear()
    for _ in range(S.LOGIN_MAX_TENTATIVAS - 1):
        S._registrar_falha_login("carla", "3.3.3.3")
    ok, _ = S._login_permitido("carla", "3.3.3.3")
    check("abaixo do teto continua liberado — três erros não punem ninguém", ok)

    S._limpar_falhas_login("carla", "3.3.3.3")
    ok, _ = S._login_permitido("carla", "3.3.3.3")
    check("acerto limpa o contador", ok)
    check("o teto é generoso (≥ 5): o objetivo é impedir 10.000 tentativas, "
          "não punir três", S.LOGIN_MAX_TENTATIVAS >= 5)


def secao_ip():
    """[4] o endereço do cliente precisa ser o do JOGADOR, não o do proxy."""
    print("\n[4] endereço do cliente")

    class _Req:
        def __init__(self, remote, headers):
            self.remote = remote; self.headers = headers

    r = _Req("10.0.0.1", {"X-Forwarded-For": "203.0.113.9, 10.0.0.1"})
    check("modo público confia no X-Forwarded-For (o IP real do jogador)",
          S._ip_do_cliente(r, publico=True) == "203.0.113.9",
          "sem isso, todos atrás do proxy caem no mesmo balde e o primeiro "
          "atacante tranca o jogo inteiro")
    check("fora do modo público, ignora o header (é forjável)",
          S._ip_do_cliente(r, publico=False) == "10.0.0.1")
    r2 = _Req("10.0.0.1", {})
    check("sem o header, cai no remote",
          S._ip_do_cliente(r2, publico=True) == "10.0.0.1")


async def main():
    await secao_senha()
    await secao_laco()
    secao_limite()
    secao_ip()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
