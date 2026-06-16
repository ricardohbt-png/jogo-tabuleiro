@echo off
title Legends for Hire - Online (link unico)
cd /d "%~dp0"

REM Sobe o servidor + tunel HTTPS e mostra UM link para mandar aos amigos.
REM Precisa de cloudflared (recomendado) ou ngrok instalado. Ver online.py.

python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado! Instale em https://python.org
    pause
    exit /b 1
)

python online.py
pause
