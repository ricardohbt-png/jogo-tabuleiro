"""Ajuda para testes de combate que NÃO querem bônus de costas/flanco.

Desde a regra de direção (2026-11-25) quem ataca ao lado ou atrás de um alvo ganha +1/+2 no acerto.
Num teste que mede outra coisa (dano, saves, recarga), vire o alvo para o atacante com `virar_para`
em vez de repetir `facing` à mão.
"""


def virar_para(entidade, pos):
    """Vira `entidade` (herói/monstro) para a casa `pos` (eixo dominante) e devolve a direção."""
    dx, dy = pos[0] - entidade["pos"][0], pos[1] - entidade["pos"][1]
    if abs(dx) >= abs(dy):
        f = [1 if dx > 0 else -1, 0] if dx else [0, 1]
    else:
        f = [0, 1 if dy > 0 else -1]
    entidade["facing"] = f
    return f
