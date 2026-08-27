# -*- coding: utf-8 -*-
r"""
Guarda de regressao da LATENCIA DE CONEXAO do servidor.

CAUSA RAIZ (medida em 2026-08-25, Windows 11):
`websockets.serve(handler, "0.0.0.0", 8765)` escuta SO em IPv4. No Windows o
nome `localhost` resolve para `::1` (IPv6) ANTES de 127.0.0.1, entao o
navegador tenta IPv6, leva recusa, e so depois cai para IPv4 -- o atraso de
"Happy Eyeballs". Medido com curl:

    localhost   -> connect 207 ms   (total 216 ms)
    127.0.0.1   -> connect 0,7 ms   (total 1,7 ms)
    [::1]       -> recusado

Como `_http` manda `Connection: close` (obrigatorio: a lib fecha o socket
depois de responder), CADA arquivo estatico abre uma conexao NOVA -- e paga os
207 ms de novo. Uma entrada de masmorra baixa ~60 arquivos: com 6 conexoes em
paralelo sao ~10 ondas, ~2 s so de espera de conexao, antes de qualquer byte.
E `iniciar.bat` abre justamente http://localhost:8765/index.html.

Correcao: escutar em IPv4 E IPv6 (lista de hosts em SERVER_HOSTS).

Roda da raiz:  python tools/test_rede_local.py
"""
import os
import socket
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8799          # porta propria: nao briga com o servidor de jogo em 8765

PASS = 0
FAIL = 0


def check(nome, cond, detalhe=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  [ok] " + nome)
    else:
        FAIL += 1
        print("  [FALHA] " + nome + ((" -- " + detalhe) if detalhe else ""))


def conecta(familia, endereco, timeout=3.0):
    """Devolve (ok, segundos) para um connect TCP cru."""
    s = socket.socket(familia, socket.SOCK_STREAM)
    s.settimeout(timeout)
    t0 = time.perf_counter()
    try:
        s.connect((endereco, PORTA))
        return True, time.perf_counter() - t0
    except OSError:
        return False, time.perf_counter() - t0
    finally:
        s.close()


def espera_subir(prazo=25.0):
    fim = time.time() + prazo
    while time.time() < fim:
        ok, _ = conecta(socket.AF_INET, "127.0.0.1", timeout=0.5)
        if ok:
            return True
        time.sleep(0.3)
    return False


print("[0] sobe o servidor numa porta propria")
env = dict(os.environ, LFH_PORT=str(PORTA))
proc = subprocess.Popen([sys.executable, "server.py"], cwd=RAIZ, env=env,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    if not espera_subir():
        print("  [FALHA] servidor nao subiu na porta %d" % PORTA)
        print("\nPASS=0 FAIL=1")
        sys.exit(1)
    print("  [ok] servidor no ar")

    print("[1] IPv4 responde (nao pode regredir)")
    ok4, t4 = conecta(socket.AF_INET, "127.0.0.1")
    check("127.0.0.1 aceita conexao", ok4)
    check("127.0.0.1 conecta rapido (<50 ms), medido %.1f ms" % (t4 * 1000), t4 < 0.050)

    print("[2] IPv6 responde -- e o que tira os ~207 ms do 'localhost'")
    if not socket.has_ipv6:
        check("maquina tem IPv6", False, "socket.has_ipv6 e False")
    else:
        ok6, t6 = conecta(socket.AF_INET6, "::1")
        check("::1 aceita conexao", ok6,
              "servidor escutando so em IPv4: 'localhost' cai para IPv4 apos o atraso de fallback")
        if ok6:
            check("::1 conecta rapido (<50 ms), medido %.1f ms" % (t6 * 1000), t6 < 0.050)

    print("[3] o nome 'localhost' (o que iniciar.bat abre) conecta rapido")
    infos = socket.getaddrinfo("localhost", PORTA, 0, socket.SOCK_STREAM)
    fam_primeira = infos[0][0]
    print("       'localhost' resolve primeiro para %s" %
          ("IPv6" if fam_primeira == socket.AF_INET6 else "IPv4"))
    melhor = None
    for fam, _t, _p, _c, sa in infos:
        s = socket.socket(fam, socket.SOCK_STREAM)
        s.settimeout(3.0)
        t0 = time.perf_counter()
        try:
            s.connect(sa[:2])
            dt = time.perf_counter() - t0
            melhor = dt if melhor is None else min(melhor, dt)
        except OSError:
            pass
        finally:
            s.close()
    check("alguma familia de 'localhost' conecta", melhor is not None)
    if melhor is not None:
        check("a PRIMEIRA familia de 'localhost' aceita conexao",
              conecta(fam_primeira, "::1" if fam_primeira == socket.AF_INET6 else "127.0.0.1")[0],
              "se a primeira recusa, o navegador espera o fallback (~207 ms) a CADA arquivo")
    print("[4] compressao dos estaticos (gzip) -- 50% no .glb, 75% no .js")
    import gzip as _gz
    import urllib.request as _u

    def pega(caminho, aceita_gzip):
        req = _u.Request("http://127.0.0.1:%d/%s" % (PORTA, caminho))
        if aceita_gzip:
            req.add_header("Accept-Encoding", "gzip")
        with _u.urlopen(req, timeout=20) as r:
            return r.read(), (r.headers.get("Content-Encoding") or "")

    # .js: texto puro, o maior ganho relativo
    bruto, enc0 = pega("game.js", False)
    comp, enc1 = pega("game.js", True)
    check("sem Accept-Encoding o corpo vai cru (cliente antigo continua servido)", enc0 == "")
    check("com Accept-Encoding o .js vem gzipado", enc1 == "gzip")
    if enc1 == "gzip":
        check("gzip do .js encolhe pelo menos 50%% (foi %.0f%%)"
              % (100 * (1 - len(comp) / len(bruto))), len(comp) < len(bruto) * 0.5)
        check("o .js descomprime byte-identico ao original",
              _gz.decompress(comp) == bruto)

    # PNG ja vem comprimido: gastar CPU nele nao rende -- tem de ficar de fora
    _, encpng = pega("assets/habilidades/cura.png", True)
    check("PNG NAO e recomprimido (ja e um formato comprimido)", encpng == "")

    # o cache nao pode devolver corpo trocado entre dois pedidos iguais
    c1, _ = pega("game.js", True)
    c2, _ = pega("game.js", True)
    check("dois pedidos seguidos devolvem o mesmo corpo (cache coerente)", c1 == c2)

finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

print("")
print("PASS=%d FAIL=%d" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
