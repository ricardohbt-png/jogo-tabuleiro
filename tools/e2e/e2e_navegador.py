"""Teste de ponta a ponta no navegador (Playwright + Chromium).

Sobe um servidor ISOLADO, abre o cliente de verdade e percorre o fluxo que um
jogador faz: criar conta -> criar jogo -> escolher heroi -> cidade -> entrar no
Campo de Treinamento -> jogar alguns turnos. Falha se aparecer qualquer erro de
JavaScript no console, ou se um passo do fluxo nao acontecer.

ISOLAMENTO: o servidor grava contas e saves ao lado do server.py. No GitHub
Actions (CI=true) o checkout e descartavel e roda direto; na sua maquina o teste
cria um checkout temporario do HEAD (git worktree) para NAO sujar as suas contas
e saves reais, e o remove no fim. Nunca aponta para o servidor de jogo (8765).

Requisitos: pip install playwright && python -m playwright install chromium
Uso (da raiz):  python -X utf8 tools/e2e/e2e_navegador.py [--ver]   # --ver mostra o navegador
"""
import argparse
import atexit
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FALHAS = []
ETAPAS = []


def etapa(nome, ok, detalhe=""):
    ETAPAS.append((nome, ok))
    print(("  ok   " if ok else "  FALHA ") + nome + (f"  [{detalhe}]" if detalhe and not ok else ""), flush=True)
    if not ok:
        FALHAS.append(nome)


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def preparar_raiz():
    """Raiz de onde o servidor roda: o proprio checkout no CI; temporario fora dele."""
    if os.environ.get("CI"):
        return RAIZ, lambda: None
    tmp = os.path.join(tempfile.gettempdir(), f"lfh_e2e_{os.getpid()}")
    subprocess.run(["git", "worktree", "add", "-q", "--detach", tmp, "HEAD"], cwd=RAIZ, check=True)

    def limpar():
        subprocess.run(["git", "worktree", "remove", "--force", tmp], cwd=RAIZ, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
        subprocess.run(["git", "worktree", "prune"], cwd=RAIZ, capture_output=True)
    return tmp, limpar


def subir_servidor(raiz, porta):
    env = dict(os.environ, PORT=str(porta), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([sys.executable, "-X", "utf8", "server.py"], cwd=raiz, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(100):
        try:
            if urllib.request.urlopen(f"http://127.0.0.1:{porta}/index.html", timeout=1).status == 200:
                return proc
        except Exception:
            time.sleep(0.3)
        if proc.poll() is not None:
            break
    proc.kill()
    raise SystemExit("o servidor de teste nao subiu:\n" + (proc.stderr.read() or b"").decode("utf8", "replace")[-800:])


# Erros que nao indicam bug do jogo (autoplay de audio bloqueado, 404 de favicon).
def erro_ignoravel(msg):
    return any(x in msg for x in ("favicon", "NotAllowedError", "play() failed", "AudioContext"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", action="store_true", help="mostra o navegador")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    raiz, limpar = preparar_raiz()
    atexit.register(limpar)
    porta = porta_livre()
    srv = subir_servidor(raiz, porta)
    atexit.register(srv.kill)
    url = f"http://127.0.0.1:{porta}/index.html"
    print(f"servidor isolado em {url} (raiz {raiz})\n")

    erros = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch(headless=not a.ver)
        pg = nav.new_context(viewport={"width": 1280, "height": 800}).new_page()
        pg.on("console", lambda m: erros.append("console.error: " + m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: erros.append("pageerror: " + str(e)))
        pg.on("dialog", lambda d: d.accept())            # "criar conta?" e confirmacoes

        def tela():
            return pg.evaluate("[...document.querySelectorAll('[id^=screen-]')].filter(e=>e.classList.contains('active')).map(e=>e.id)[0]")

        def esperar_tela(nome, t=15000):
            try:
                pg.wait_for_function("n => document.querySelector('#'+n)?.classList.contains('active')", arg=nome, timeout=t)
                return True
            except Exception:
                return False

        print("[1] login e conta")
        pg.goto(url)
        etapa("a tela de conexao carrega", esperar_tela("screen-connect", 8000))
        pg.click("#cover-splash")                         # "Clique para comecar" (libera o audio)
        pg.wait_for_timeout(600)                         # a capa some em fade
        pg.fill("#input-name", "TesterE2E")
        pg.fill("#input-server", f"ws://127.0.0.1:{porta}")
        pg.fill("#input-senha", "senha-de-teste-123")
        pg.click("text=Acessar minha conta")
        etapa("criar conta leva a Meus Jogos", esperar_tela("screen-savegames"), tela())

        print("[2] novo jogo e escolha de heroi")
        pg.fill("#sg-name", "Jogo E2E")
        pg.click("text=Criar jogo")
        etapa("criar jogo leva a escolha de heroi", esperar_tela("screen-class-select"), tela())
        pg.select_option("select:has(option[value='campo_de_treinamento.json'])", "campo_de_treinamento.json")
        pg.click("[aria-label='Selecionar Guerreiro Anão']")
        pg.click("text=Adicionar ao grupo")
        pg.click("#cs-btn-start")
        etapa("iniciar o jogo leva a cidade", esperar_tela("screen-city"), tela())

        print("[2b] Esc fecha as janelas da cidade")
        for ponto, janela in (("Templo", "#shop-modal.open"), ("Ferraria", "#shop-modal.open"),
                              ("Taverna", "#shop-modal.open"), ("Mercado", "#shop-modal.open"),
                              ("Guilda dos Heróis", ".guild-modal.open")):
            pg.click(f"button:has-text('{ponto}')")
            pg.wait_for_selector(janela, timeout=5000)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(300)
            etapa(f"Esc fecha a janela de {ponto}", pg.query_selector(janela) is None)
            if pg.query_selector(janela):                  # nao deixa a janela aberta travar o resto
                pg.evaluate("typeof closeShop==='function' && closeShop(); typeof closeGuild==='function' && closeGuild()")

        print("[3] masmorra")
        pg.click("button:has-text('Campo de Treinamento')")
        pg.click("button:has-text('Entrar em Campo de Treinamento')")
        etapa("entrar leva ao tabuleiro", esperar_tela("screen-game", 20000), tela())
        try:
            pg.wait_for_function("GS.gameState && GS.gameState.monsters && GS.gameState.monsters.length > 0", timeout=15000)
            etapa("o estado da masmorra chegou com monstros", True)
        except Exception:
            etapa("o estado da masmorra chegou com monstros", False)
        etapa("o tabuleiro tem canvas", pg.evaluate("!!document.querySelector('#screen-game canvas')"))

        print("[4] bonecos de treino ficam parados durante os turnos")
        tipos = "['boneco_mira','boneco_golpe','boneco_furia']"
        pos = lambda: pg.evaluate(f"GS.gameState.monsters.filter(m=>{tipos}.includes(m.type)).map(m=>m.id+':'+m.pos)")
        antes = pos()
        etapa("os tres alvos do Guerreiro existem", len(antes) == 3, str(antes))
        for i in range(3):
            try:
                pg.wait_for_function("GS.isMyTurn === true", timeout=25000)
            except Exception:
                etapa(f"a vez do heroi chegou (rodada {i + 1})", False)
                break
            pg.evaluate("GS.endTurn()")
        etapa("os alvos nao se mexeram", pos() == antes, f"{antes} -> {pos()}")

        print("[5] idioma e tela sem erro")
        pg.evaluate("I18N.setLang('en')")
        pg.wait_for_timeout(800)
        etapa("trocar para ingles nao quebra o jogo", tela() == "screen-game")
        pg.evaluate("I18N.setLang('pt')")
        pg.wait_for_timeout(300)

        if os.environ.get("E2E_INJETAR_ERRO"):             # autoteste: o teste TEM de falhar
            pg.evaluate("setTimeout(() => { throw new Error('erro-injetado') }, 20)")
        pg.wait_for_timeout(700)                           # deixa chegar os eventos pendentes
        pg.evaluate("0")                                   # ida e volta: descarrega a fila de eventos
        relevantes = [e for e in erros if not erro_ignoravel(e)]
        etapa(f"nenhum erro de JavaScript no console ({len(relevantes)})", not relevantes, "; ".join(relevantes[:3]))
        nav.close()

    srv.kill()
    print(f"\n=== {len(ETAPAS) - len(FALHAS)} passaram, {len(FALHAS)} falharam ===")
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
