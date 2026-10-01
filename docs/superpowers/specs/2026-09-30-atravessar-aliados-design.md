# Atravessar aliados — design

## Objetivo

Opção da sala que permite aos peões do grupo **cruzar** a casa de outro aliado
(herói, servo animado, elemental invocado, prisioneiro liberto) sem **nunca
terminar** o movimento na mesma casa de outro.

## Decisões (brainstorming 2026-09-30)

1. **Quem liga:** só o anfitrião, valendo para a sala toda; desligada por padrão;
   salva no jogo salvo (molde do limite de tempo / visão compartilhada).
2. **Quem atravessa:** todos os aliados se atravessam — heróis, servos e o
   prisioneiro, no movimento manual e no "comandar" automático dos servos.
3. **Mecânica:** atravessar só **dentro de um caminho**. O caminho pode passar por
   casa de aliado, mas a última casa precisa estar livre (conferido antes de
   andar). Passo isolado (setas) para dentro de um aliado segue recusado. Nunca
   há dois peões na mesma casa entre mensagens.

## Servidor

- Campo `GameRoom.atravessar_aliados` (False); `game_state`/`city_state`; jogo
  salvo; `set_atravessar_aliados {enabled}` só do anfitrião
  (`erro.somente_o_anfitriao_pode_alterar_atravessar`).
- `handle_move(..., _atravessar)`: com a flag, herói/servo/prisioneiro liberto
  não bloqueiam o passo. O prisioneiro passa a bloquear o herói sempre (antes não
  bloqueava); o preso nunca é atravessável.
- `handle_move_path`, `handle_mover_animado_caminho`,
  `handle_mover_prisioneiro_caminho` (mensagens novas `mover_animado_caminho` /
  `mover_prisioneiro_caminho`): `_destino_livre_ou_avisa` recusa o caminho cujo
  destino tem aliado (`erro.o_destino_esta_ocupado`); se o caminho é interrompido
  em cima de alguém, `_recuar_para` devolve o peão à última casa livre.
- `handle_comandar_animados`: o servo só entra em casa de aliado se ainda tiver
  mais de 1 de movimento; terminando em cima de alguém, recua.
- Monstros (inclusive sob Comando/Dominar) bloqueiam sempre.

## Cliente

- `_occupiedSet` separa as casas de aliado em `occ.aliados` quando a opção está
  ligada: `_walkable` deixa cruzá-las, `bfsReachable` não as marca de azul e
  `findPath` nunca termina nelas (nem no caminho parcial).
- Cliques de servo e prisioneiro mandam o caminho inteiro numa mensagem.
- Painel ⚙️: botão "🚶 Atravessar aliados" (só o anfitrião aciona).

## Testes

`tools/test_atravessar_aliados.py` e `tools/test_atravessar_aliados_cliente.js`.
