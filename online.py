#!/usr/bin/env python3
"""
Legends for Hire — Jogar pela INTERNET (link único)

Sobe o servidor (que serve a página + WebSocket na porta 8765) e abre um túnel
HTTPS público. Imprime UM link para você mandar aos amigos — eles só abrem,
escolhem o nome e entram pelo código da sala. Nada de digitar endereço.

Detecta automaticamente um destes túneis (instale qualquer um):
  • cloudflared  →  recomendado (sem conta, sem página de aviso)
        https://github.com/cloudflare/cloudflared/releases  (ou: winget install cloudflare.cloudflared)
  • ngrok        →  alternativa (requer conta grátis + `ngrok config add-authtoken ...`)
        https://ngrok.com/download

Uso:  python online.py     (ou dê duplo-clique em iniciar-online.bat)
Pare com Ctrl+C.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser

PORT = 8765


def _find_exe(name):
    """Localiza um executável mesmo que o PATH ainda não tenha sido atualizado
    (ex.: logo após instalar via winget, sem reabrir o terminal)."""
    p = shutil.which(name)
    if p:
        return p
    la = os.environ.get("LOCALAPPDATA", "")
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates = []
    if la:
        candidates.append(os.path.join(la, "Microsoft", "WinGet", "Links", name + ".exe"))
        candidates += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Packages", "*" + name + "*", "**", name + ".exe"), recursive=True)
        candidates.append(os.path.join(la, name, name + ".exe"))
    candidates.append(os.path.join(pf, name, name + ".exe"))
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None
URL_RE = re.compile(r"https://[A-Za-z0-9.\-]+\.(?:trycloudflare\.com|ngrok[A-Za-z0-9.\-]*\.\w+|ngrok\.io)")


def _start_server():
    print(f"[1] Iniciando servidor (jogo + WebSocket) na porta {PORT}...")
    proc = subprocess.Popen([sys.executable, "server.py"])
    # dá um tempo pro socket abrir
    time.sleep(2.5)
    if proc.poll() is not None:
        print("    ERRO: o servidor encerrou logo ao iniciar. Rode 'python server.py' para ver o erro.")
        sys.exit(1)
    print("    Servidor no ar.")
    return proc


def _scan_stream(proc, found):
    """Lê a saída do túnel procurando a URL pública e ecoa as linhas."""
    for line in iter(proc.stdout.readline, ""):
        if not line:
            break
        m = URL_RE.search(line)
        if m and not found["url"]:
            found["url"] = m.group(0)
        # ecoa logs do túnel (ajuda a diagnosticar se algo falhar)
        sys.stdout.write("    [tunnel] " + line if line.strip() else line)


def _ngrok_api_url():
    """ngrok publica os túneis ativos em http://127.0.0.1:4040/api/tunnels."""
    import json
    import urllib.request
    for _ in range(20):
        try:
            with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=1) as r:
                data = json.load(r)
            for t in data.get("tunnels", []):
                pub = t.get("public_url", "")
                if pub.startswith("https://"):
                    return pub
        except Exception:
            pass
        time.sleep(0.7)
    return None


def _start_tunnel():
    found = {"url": None}

    cf = _find_exe("cloudflared")
    if cf:
        print("[2] Abrindo túnel com cloudflared...")
        proc = subprocess.Popen(
            [cf, "tunnel", "--url", f"http://localhost:{PORT}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding="utf-8", errors="replace",
        )
        threading.Thread(target=_scan_stream, args=(proc, found), daemon=True).start()
        for _ in range(40):              # ~20 s p/ a URL aparecer
            if found["url"]:
                break
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        return proc, found["url"]

    ng = _find_exe("ngrok")
    if ng:
        print("[2] Abrindo túnel com ngrok...")
        proc = subprocess.Popen(
            [ng, "http", str(PORT), "--log", "stdout"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding="utf-8", errors="replace",
        )
        threading.Thread(target=_scan_stream, args=(proc, found), daemon=True).start()
        url = _ngrok_api_url() or found["url"]
        return proc, url

    print("\n  Nenhum túnel encontrado (cloudflared ou ngrok).")
    print("  Instale um deles e rode de novo:")
    print("    cloudflared (recomendado): winget install cloudflare.cloudflared")
    print("    ngrok:                     https://ngrok.com/download")
    sys.exit(1)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        import websockets  # noqa: F401
    except ImportError:
        print("Instalando dependência: websockets...")
        subprocess.run([sys.executable, "-m", "pip", "install", "websockets"])

    print("=" * 64)
    print("  LEGENDS FOR HIRE — Jogar pela internet")
    print("=" * 64)

    server = _start_server()
    tunnel, url = _start_tunnel()

    if not url:
        print("\n  Não consegui ler o link público do túnel automaticamente.")
        print("  Veja os logs [tunnel] acima: a URL https do túnel + /index.html")
        print("  é o que você compartilha. (Ctrl+C para parar.)")
    else:
        link = url.rstrip("/") + "/index.html"
        print("\n" + "=" * 64)
        print("  PRONTO! Compartilhe ESTE link com seus amigos:")
        print("    " + link)
        print("  Eles só abrem, escolhem o nome e entram pelo código da sala.")
        print("  (O jogo fica no ar enquanto esta janela estiver aberta.)")
        print("=" * 64 + "\n")
        try:
            webbrowser.open(link)
        except Exception:
            pass

    try:
        while True:
            if server.poll() is not None:
                print("\n  O servidor encerrou. Saindo.")
                break
            if tunnel.poll() is not None:
                print("\n  O túnel encerrou. Saindo.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        for p in (tunnel, server):
            try:
                p.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
