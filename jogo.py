import sys
import random

sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

TAMANHO_TABULEIRO = 10

def criar_tabuleiro():
    return [["." for _ in range(TAMANHO_TABULEIRO)] for _ in range(TAMANHO_TABULEIRO)]

def exibir_tabuleiro(tabuleiro, posicoes):
    copia = [linha[:] for linha in tabuleiro]
    for i, (linha, col) in enumerate(posicoes):
        copia[linha][col] = str(i + 1)
    print("  " + " ".join(str(i) for i in range(TAMANHO_TABULEIRO)))
    for i, linha in enumerate(copia):
        print(f"{i} " + " ".join(linha))

def mover_jogador(pos, dado):
    linha, col = pos
    col += dado
    if col >= TAMANHO_TABULEIRO:
        linha += col // TAMANHO_TABULEIRO
        col = col % TAMANHO_TABULEIRO
    return (min(linha, TAMANHO_TABULEIRO - 1), col)

def jogar():
    tabuleiro = criar_tabuleiro()
    posicoes = [(0, 0), (0, 0)]
    jogadores = ["Jogador 1", "Jogador 2"]
    turno = 0

    print("Bem-vindo ao Jogo de Tabuleiro!")
    print(f"Objetivo: chegar à posição ({TAMANHO_TABULEIRO-1}, {TAMANHO_TABULEIRO-1})\n")

    while True:
        jogador_atual = jogadores[turno % 2]
        input(f"{jogador_atual}, pressione Enter para rolar o dado...")
        dado = random.randint(1, 6)
        print(f"Você tirou: {dado}")

        posicoes[turno % 2] = mover_jogador(posicoes[turno % 2], dado)
        exibir_tabuleiro(tabuleiro, posicoes)

        linha, col = posicoes[turno % 2]
        if linha >= TAMANHO_TABULEIRO - 1 and col >= TAMANHO_TABULEIRO - 1:
            print(f"\n{jogador_atual} venceu!")
            break

        turno += 1

if __name__ == "__main__":
    jogar()
