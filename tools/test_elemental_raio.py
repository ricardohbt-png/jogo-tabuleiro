"""Regressões da mira em linha do Raio do Elemental Elétrico."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom


def check(nome, condicao):
    if not condicao:
        raise AssertionError(nome)
    print("  ✅", nome)


def criar_sala():
    sala = GameRoom("ELEMENTAL_RAIO_TEST")
    sala.phase = "playing"
    sala.round_num = 1
    sala.map_w = sala.map_h = 9
    sala.tiles = [[S.FLOOR] * sala.map_w for _ in range(sala.map_h)]
    sala.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 9, "h": 9,
                   "cx": 4, "cy": 4, "locked": False}]
    sala.players = {}
    sala.monsters = {}
    sala.prisoner = None
    sala._blocks_tile = lambda x, y: not (0 <= x < sala.map_w and 0 <= y < sala.map_h) or sala.tiles[y][x] == S.WALL
    sala._tem_linha_de_visao = lambda _a, _b: True
    sala._monster_tiles = lambda monstro: [monstro["pos"]]
    return sala


async def main():
    print("\n[1] Identificação e linha válida")
    sala = criar_sala()
    elemental = {
        "id": "servo-raio", "tipo": "elemental", "tipo_elemental": "eletrico",
        "name": "Elemental Elétrico", "pos": [4, 4], "vida_atual": 20,
        "attacks": [{"name": "Raio", "range": 4, "atk_bonus": 6,
                     "damage": "1d10", "damage_types": [S.DMG_LIGHTNING]}],
    }
    check("reconhece somente o Raio elétrico da ficha", sala._elemental_raio_eletrico(elemental))
    check("recusa elemental de outro elemento", not sala._elemental_raio_eletrico({**elemental, "tipo_elemental": "ar"}))
    check("aceita mira em casa vazia da linha", sala._elemental_raio_linha(elemental, [4, 2]) == [[4, 3], [4, 2], [4, 1], [4, 0]])
    check("recusa diagonal", sala._elemental_raio_linha(elemental, [5, 3]) == [])
    check("recusa fora do alcance", sala._elemental_raio_linha(elemental, [4, -1]) == [])
    sala.tiles[2][4] = S.WALL
    check("parede interrompe a descarga", sala._elemental_raio_linha(elemental, [4, 1]) == [])
    check("quadrado antes da parede ainda pode orientar a descarga", sala._elemental_raio_linha(elemental, [4, 3]) == [[4, 3]])

    print("\n[2] Atinge toda criatura alinhada, inclusive aliados")
    sala = criar_sala()
    elemental["pos"] = [4, 4]
    heroi = {"id": "heroi", "name": "Herói", "pos": [4, 3], "alive": True, "hp": 20, "max_hp": 20}
    monstro = {"id": "monstro", "name": "Monstro", "pos": [4, 2], "hp": 20, "max_hp": 20, "ca": 10}
    aliado = {"id": "aliado", "name": "Servo aliado", "pos": [4, 1], "vida_atual": 10, "vida_max": 10}
    prisioneiro = {"id": "prisioneiro", "name": "Prisioneiro", "pos": [4, 0], "alive": True, "hp": 8, "max_hp": 8}
    sala.players = {"p1": heroi}
    sala.monsters = {"m1": monstro}
    sala._all_animados = lambda: [elemental, aliado]
    sala.prisoner = prisioneiro
    linha = sala._elemental_raio_linha(elemental, [4, 0])
    alvos = sala._elemental_raio_alvos(elemental, linha)
    check("herói, monstro, servo aliado e prisioneiro entram na área",
          [tipo for tipo, _ in alvos] == ["player", "monster", "animado", "prisoner"])
    check("alvos são processados da origem para o fim da linha",
          [obj["id"] for _, obj in alvos] == ["heroi", "monstro", "aliado", "prisioneiro"])

    print("\n[3] Um ataque independente por alvo e um efeito visual da descarga")
    chamadas = []
    eventos = []
    async def executar(_atacante, alvo):
        chamadas.append(alvo["kind"] + ":" + alvo["obj"]["id"])
    async def broadcast(evento):
        eventos.append(evento)
    sala._face_toward = lambda *_args: None
    sala._monster_register_attack_alert = lambda *_args: None
    sala._monster_execute_attacks = executar
    sala.broadcast = broadcast
    await sala._elemental_raio_atacar(elemental, linha, alvos, "p1")
    check("o executor comum é chamado uma vez para cada criatura", chamadas == ["player:heroi", "monster:monstro", "animado:aliado", "prisoner:prisioneiro"])
    animacao = next((e for e in eventos if e.get("spell_id") == "elemental_raio"), None)
    check("emite animação com caminho completo", animacao and animacao["path"] == [[4, 4], *linha])

    print("\n[4] Fluxo manual aceita casa vazia como direção")
    sala = criar_sala()
    elemental["pos"] = [4, 4]
    elemental["acted"] = False
    heroi = {"id": "p1", "name": "Herói", "pos": [4, 3], "alive": True, "hp": 20, "max_hp": 20,
             "animados": [elemental]}
    sala.players = {"p1": heroi}
    sala.player_order = ["p1"]
    sala.turn_index = 0
    sala.animados_phase_pid = "p1"
    sala._all_animados = lambda: [elemental]
    erros = []
    async def capturar_envio(_pid, evento):
        if evento.get("type") == "error":
            erros.append(evento)
    sala.send_to = capturar_envio
    sala.push_state = lambda: asyncio.sleep(0)
    disparos = []
    async def capturar_disparo(_elemental, linha, alvos, _pid):
        disparos.append((linha, alvos))
    sala._elemental_raio_atacar = capturar_disparo
    await sala.handle_atacar_animado("p1", elemental["id"], None, [4, 3])
    check("clique em casa vazia dispara a linha e atinge o herói alinhado",
          len(disparos) == 1 and [tipo for tipo, _ in disparos[0][1]] == ["player"])
    check("disparo consome a ação do servo", elemental.get("acted") is True)
    elemental["acted"] = False
    await sala.handle_atacar_animado("p1", elemental["id"], None, [5, 3])
    check("mira diagonal é recusada sem consumir a ação", bool(erros) and elemental.get("acted") is False)

    print("\n=== Raio do Elemental Elétrico: passou ===")


if __name__ == "__main__":
    asyncio.run(main())
