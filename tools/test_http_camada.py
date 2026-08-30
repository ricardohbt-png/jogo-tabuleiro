"""Camada HTTP do servidor. Roda da raiz: python tools/test_http_camada.py

Nasce do SP0 (docs/superpowers/plans/2026-08-28-sp0-resultados.md): o Render
sonda a porta com HEAD de 1 em 1 segundo, e a lib websockets recusa todo metodo
!= GET dentro de http11.py -- ANTES do nosso process_request. O servidor fecha a
conexao sem responder nada, e o deploy morre em "==> Timed Out".

Estes testes FALHAM antes da troca de camada e passam depois.
"""
import os, socket, subprocess, sys, time

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8788

PASS = 0; FAIL = 0
def check(nome, cond, dica=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  [ok] {nome}")
    else:
        FAIL += 1; print(f"  [FALHA] {nome}" + (f" -- {dica}" if dica else ""))


def _pedido(metodo, caminho="/index.html", conexao="close"):
    return (f"{metodo} {caminho} HTTP/1.1\r\n"
            f"Host: localhost:{PORTA}\r\n"
            f"Connection: {conexao}\r\n\r\n").encode()


def _ler_resposta(sock):
    """Le UMA resposta HTTP (cabecalhos + corpo por Content-Length).
    Devolve (linha_de_status, corpo) ou (None, b'') se nada veio."""
    dados = b""
    while b"\r\n\r\n" not in dados:
        try:
            pedaco = sock.recv(4096)
        except Exception:
            return None, b""
        if not pedaco:
            return None, b""
        dados += pedaco
    cab, _, resto = dados.partition(b"\r\n\r\n")
    linha = cab.split(b"\r\n")[0].decode("latin1")
    tam = 0
    for l in cab.split(b"\r\n")[1:]:
        if l.lower().startswith(b"content-length:"):
            tam = int(l.split(b":", 1)[1].strip())
    while len(resto) < tam:
        try:
            pedaco = sock.recv(4096)
        except Exception:
            break
        if not pedaco:
            break
        resto += pedaco
    return linha, resto[:tam]


def espera_subir(prazo=25.0):
    fim = time.time() + prazo
    while time.time() < fim:
        try:
            s = socket.create_connection(("127.0.0.1", PORTA), timeout=0.5)
            s.close(); return True
        except Exception:
            time.sleep(0.3)
    return False


print("[0] sobe o servidor numa porta propria")
env = dict(os.environ, LFH_PORT=str(PORTA))
proc = subprocess.Popen([sys.executable, "server.py"], cwd=RAIZ, env=env,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    if not espera_subir():
        print(f"  [FALHA] servidor nao subiu na porta {PORTA}")
        print("\nPASS=0 FAIL=1")
        sys.exit(1)
    print("  [ok] servidor no ar")

    print("[1] GET continua funcionando (nao pode regredir)")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("GET"))
    linha, corpo = _ler_resposta(s); s.close()
    check("GET /index.html responde 200", linha is not None and "200" in linha,
          f"veio: {linha!r}")
    check("GET devolve corpo nao vazio", len(corpo) > 0)

    print("[2] HEAD recebe resposta -- e a sonda que o Render usa")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("HEAD"))
    linha, _ = _ler_resposta(s); s.close()
    check("HEAD recebe uma resposta HTTP", linha is not None,
          "a conexao fechou sem responder nada -- e assim que o deploy morre")
    check("HEAD responde 200", linha is not None and "200" in linha,
          f"veio: {linha!r}")

    print("[3] metodo desconhecido nao derruba a conexao em silencio")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("OPTIONS"))
    linha, _ = _ler_resposta(s); s.close()
    check("OPTIONS recebe alguma resposta HTTP", linha is not None,
          "qualquer status serve; o que nao pode e fechar mudo")

    print("[4] keep-alive -- DOIS pedidos na MESMA conexao TCP")
    s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
    s.sendall(_pedido("GET", conexao="keep-alive"))
    linha1, _ = _ler_resposta(s)
    s.sendall(_pedido("GET", "/game.css", conexao="keep-alive"))
    linha2, _ = _ler_resposta(s)
    s.close()
    check("1o pedido responde 200", linha1 is not None and "200" in linha1)
    check("2o pedido na MESMA conexao responde 200",
          linha2 is not None and "200" in linha2,
          "hoje a lib fecha o socket apos responder; era isso que obrigava "
          "'Connection: close' e fazia cada arquivo pagar um handshake TLS")

    print(f"\nPASS={PASS} FAIL={FAIL}")
    sys.exit(1 if FAIL else 0)
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except Exception: proc.kill()
