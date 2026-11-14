# Absinto — design

## Objetivo

Adicionar à taverna uma bebida de cinco doses que restaura fome e sede, mas aplica penalidades cumulativas enquanto cada dose estiver ativa.

## Regras aprovadas

- Preço: 45 moedas; imagem: `assets/itens/absinto.png`; ícone de fallback: 🍸.
- Cinco usos por garrafa; cada uso restaura 15 de fome e 15 de sede.
- Cada dose ativa aplica −1 no ataque e −1 na CA por 10 rodadas, com temporizador independente.
- Com 3 ou 4 doses ativas, o movimento total diminui em 1; com 5 ou mais, diminui em 2.
- Ao expirar uma dose, remove apenas as penalidades dela e recalcula o movimento conforme as doses restantes.
- Não recupera PV. A garrafa desaparece após o quinto uso.
- Disponível nas cinco tavernas e elegível ao sorteio adicional de comida dos monstros, como Rum e Hidromel.

## Abordagens

- **Recomendado — movimento derivado das doses ativas:** calcular o redutor em `_moves_base`; isso evita alterar `spd` e evita deixar movimento preso depois que as doses expiram.
- **Alternativa descartada — mudar `spd` diretamente a cada dose:** cria risco de não restaurar corretamente velocidade-base, buffs ou efeitos simultâneos.

## Limites

Não muda Rum, Hidromel, PV, fome/sede de outros itens ou regras globais de movimento. Em 5 ou mais doses ativas, a redução de movimento fica limitada a 2; penalidades de ataque e CA continuam acumulando por dose.
