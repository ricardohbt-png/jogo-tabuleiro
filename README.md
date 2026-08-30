# Legends for Hire — RPG Multiplayer Online

Um jogo de RPG de tabuleiro multiplayer em estilo HeroQuest/D&D para até 6 jogadores.

## Requisitos

- Python 3.x (instalado)
- Dependências Python: `python -m pip install -r requirements.txt`
- Navegador moderno (Chrome, Firefox, Edge)

## Como Rodar o Jogo

> O `server.py` serve a página **e** o WebSocket na **mesma porta (8765)** —
> não é mais preciso um servidor HTTP separado.

### Opção 1: Script Automático (Windows)

Duplo-clique em `iniciar.bat` — encerra servidores antigos, inicia o servidor e
abre o jogo no navegador.

### Opção 2: Script Python

python start.py

### Opção 3: Manual

python server.py

Navegador:
http://localhost:8765/index.html

## Jogar pela Internet (link único)

Duplo-clique em `iniciar-online.bat` (ou `python online.py`). Ele sobe o servidor
e abre um túnel HTTPS, imprimindo **um link** para você mandar aos amigos — eles
só abrem, escolhem o nome e entram pelo código da sala (não digitam endereço).

Requer um túnel instalado:
- **cloudflared** (recomendado, sem conta): `winget install cloudflare.cloudflared`
- **ngrok** (alternativa): https://ngrok.com/download

O jogo fica no ar enquanto a janela estiver aberta.

## Estrutura do Projeto

legends-for-hire/
├── index.html              # Cliente principal
├── server.py               # Servidor WebSocket
├── src/
│   ├── visualConfig.js     # Configuracao visual
│   ├── gameState.js        # Estado do jogo
│   ├── main.js             # Orquestrador
│   └── ui/theme.js         # Injetor CSS
└── assets/portraits/       # Fotos de personagens

## Troubleshooting

Se "Porta 8765 ja esta em uso":
1. Feche python.exe
2. Ou altere server.py porta

Se "Conexao recusada":
1. Verifique que server.py esta rodando
2. Verifique firewall (porta 8765)

Se "Letras erradas":
1. Recarregue pagina (Ctrl+Shift+R)
2. Limpe cache do navegador

## Como Jogar

1. Digite seu nome
2. Escolha classe (Guerreiro, Mago, etc)
3. Aguarde outros jogadores
4. Comece jogo
5. Explore masmorra, colete tesouro, mate inimigos

## Versao

Legends for Hire v1.0 — 2026-05-30
