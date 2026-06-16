#!/usr/bin/env bash
# ============================================================
#   LEGENDS FOR HIRE — iniciar.sh  (Mac / Linux)
#   Inicia o servidor WebSocket (porta 8765) +
#   servidor HTTP (porta 8000) e abre o navegador.
# ============================================================
set -e

# Muda para a pasta do script, independente de onde foi chamado
cd "$(dirname "$0")"

echo "============================================================"
echo "   LEGENDS FOR HIRE"
echo "============================================================"
echo ""

# ── 1. Detecta Python ─────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo " ERRO: Python nao encontrado."
    echo " Instale em: https://python.org"
    exit 1
fi

echo " Python encontrado: $($PY --version)"

# ── 2. Verifica / instala a dependencia websockets ────────────
if ! $PY -c "import websockets" &>/dev/null; then
    echo " Instalando dependencia: websockets..."
    $PY -m pip install websockets
    echo ""
fi

# ── 3. Encerra processos antigos nas portas 8765 e 8000 ───────
echo " Encerrando processos antigos nas portas 8765 e 8000..."
for PORT in 8765 8000; do
    # lsof disponivel na maioria dos sistemas Unix
    if command -v lsof &>/dev/null; then
        lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null || true
    # fuser como fallback (comum no Linux)
    elif command -v fuser &>/dev/null; then
        fuser -k ${PORT}/tcp 2>/dev/null || true
    fi
done
sleep 1

# ── 4. Inicia o servidor WebSocket (porta 8765) ───────────────
echo " Iniciando servidor WebSocket (porta 8765)..."
$PY server.py &
WS_PID=$!

# ── 5. Aguarda o WebSocket abrir a porta ──────────────────────
echo " Aguardando servidor WebSocket..."
RETRIES=0
while ! (echo "" | $PY -c "
import socket, sys
s = socket.socket()
s.settimeout(0.5)
sys.exit(0 if s.connect_ex(('127.0.0.1', 8765)) == 0 else 1)
" 2>/dev/null); do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge 20 ]; then
        echo ""
        echo " ERRO: o servidor WebSocket nao iniciou."
        echo " Verifique se server.py esta correto."
        kill $WS_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo " Servidor WebSocket pronto!"

# ── 6. Inicia o servidor HTTP (porta 8000) ────────────────────
echo " Iniciando servidor HTTP (porta 8000)..."
$PY -m http.server 8000 &
HTTP_PID=$!
sleep 2

# ── 7. Detecta o comando para abrir o navegador ───────────────
if command -v xdg-open &>/dev/null; then
    OPEN_CMD="xdg-open"          # Linux (GNOME, KDE, etc.)
elif command -v open &>/dev/null; then
    OPEN_CMD="open"              # macOS
elif command -v wslview &>/dev/null; then
    OPEN_CMD="wslview"           # WSL (Windows Subsystem for Linux)
else
    OPEN_CMD=""
fi

# ── 8. Abre o navegador ───────────────────────────────────────
echo " Abrindo o jogo no navegador..."
echo ""
echo " Endereco: http://localhost:8000/index.html"
echo ""
if [ -n "$OPEN_CMD" ]; then
    $OPEN_CMD "http://localhost:8000/index.html"
else
    echo " (Abra manualmente: http://localhost:8000/index.html)"
fi

echo "============================================================"
echo "  Jogo iniciado! Servidor rodando..."
echo ""
echo "  PIDs em execucao:"
echo "    WebSocket (8765): $WS_PID"
echo "    HTTP      (8000): $HTTP_PID"
echo ""
echo "  Para parar: pressione Ctrl+C"
echo "============================================================"
echo ""

# ── 9. Mantém o script vivo; mata filhos ao sair ─────────────
trap "echo ''; echo ' Encerrando servidores...'; kill $WS_PID $HTTP_PID 2>/dev/null; exit 0" INT TERM

# Aguarda qualquer filho morrer (indica erro)
wait $WS_PID $HTTP_PID
