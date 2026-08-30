@echo off
title Legends for Hire - Iniciando...
echo ============================================================
echo    LEGENDS FOR HIRE
echo ============================================================
echo.

REM Mudar para a pasta do jogo (suporta caminhos com espacos)
cd /d "%~dp0"

REM --- 1. Verifica Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado!
    echo  Instale em: https://python.org
    echo.
    pause
    exit /b 1
)

REM --- 2. Verifica/instala a dependencia do servidor ---
REM O servidor NAO usa mais websockets: a camada de servico e o aiohttp.
REM A lib websockets segue no requirements.txt, mas so como CLIENTE de
REM tools/medir_cold_start.py -- nao e pre-requisito para jogar.
python -c "import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo  Instalando dependencia: aiohttp...
    python -m pip install aiohttp
    echo.
)

REM --- 3. Encerra servidores antigos nas portas 8765 e 8000 ---
echo  Encerrando processos antigos nas portas 8765 e 8000...
for %%P in (8765 8000) do (
    for /f "tokens=5" %%K in ('netstat -aon ^| findstr ":%%P "') do (
        taskkill /PID %%K /F >nul 2>&1
    )
)

REM Aguarda as portas serem liberadas
ping -n 3 127.0.0.1 >nul

REM --- 4. Inicia o servidor WebSocket (porta 8765) ---
REM (os processos filhos herdam a pasta atual definida pelo cd acima)
echo  Iniciando servidor WebSocket (porta 8765)...
start "Legends for Hire - Servidor" cmd /k python server.py

REM --- 5. Aguarda o servidor WebSocket abrir a porta 8765 ---
echo  Aguardando servidor WebSocket...
set RETRIES=0
:WAIT_WS
REM So considera pronto quando a porta esta em LISTENING (ignora TIME_WAIT
REM residual do processo antigo, que daria falso-positivo).
netstat -aon 2>nul | findstr ":8765 " | findstr "LISTENING" >nul
if not errorlevel 1 goto WS_READY
set /a RETRIES+=1
if %RETRIES% geq 20 goto SERVER_FAILED
ping -n 2 127.0.0.1 >nul
goto WAIT_WS
:WS_READY
echo  Servidor pronto!

REM --- 6. Abre o jogo no navegador (a propria porta 8765 serve a pagina) ---
echo  Abrindo o jogo no navegador...
echo.
echo  Endereco: http://localhost:8765/index.html
echo.
start "" "http://localhost:8765/index.html"

echo ============================================================
echo   Jogo iniciado!
echo.
echo   Para jogar na internet, abra um tunel para a porta 8765:
echo     cloudflared tunnel --url http://localhost:8765
echo     ^(ou: ngrok http 8765^)  e compartilhe o link https + /index.html
echo.
echo   Para parar, feche a janela:
echo     "Legends for Hire - Servidor"  (jogo + WebSocket - porta 8765)
echo ============================================================
echo.
pause
exit /b 0

:SERVER_FAILED
echo.
echo ============================================================
echo  ERRO: o servidor WebSocket nao iniciou.
echo.
echo  Possiveis causas:
echo    - Porta 8765 ocupada por outro processo
echo    - Erro no server.py (veja a janela do Servidor)
echo.
echo  Feche todas as janelas e tente novamente.
echo ============================================================
echo.
pause
exit /b 1
