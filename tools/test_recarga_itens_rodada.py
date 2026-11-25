"""A recarga das armas (Clarão Solar, Pulso do Trovão, etc.) guarda uma rodada
ABSOLUTA no item. O contador de rodadas volta a 1 em sala nova, então a marca
antiga deixava a habilidade indisponível por dezenas de rodadas."""
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, restore_character, snapshot_character


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    print(f"  ✅ {name}")


def heroi_com_marcas():
    p = make_player("p1", "Herói", "warrior", 0)
    arma = dict(server.WEAPONS["mangual_sol_cativo"])
    arma.update(solar_flare_ready_round=40, thunder_pulse_ready_round=38,
                lightning_line_pronta_em=35, bronze_serpent_ready_round=33)
    p["gear"]["armor"] = {"id": "manto_das_sombras", "manto_escuridao_pronto_em": 30}
    p["gear"]["off_hand"] = {"id": "escudo_g_retalhacao_trovejante",
                             "thunder_reaction_ready_round": 44, "thunder_reaction_active_until": 42}
    p["gear"]["weapon"] = arma
    p["weapon"] = dict(arma)
    p["bag"] = [dict(server.WEAPONS["choque_do_trovao"], thunder_pulse_ready_round=50)]
    return p


def marcas(p):
    achadas = []
    def varre(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and (k.endswith(server._SUFIXOS_RECARGA_ITEM)) and v:
                    achadas.append(k)
                varre(v)
        elif isinstance(x, list):
            for v in x:
                varre(v)
    varre(p.get("gear")); varre(p.get("weapon")); varre(p.get("bag"))
    return achadas


def main():
    print("\n[1] Ficha salva com recarga alta + sala nova (rodada 1)")
    p = heroi_com_marcas()
    check("a marca de recarga está no item salvo", "solar_flare_ready_round" in marcas(p))
    novo = make_player("p1", "Herói", "warrior", 0)
    restore_character(novo, snapshot_character(p))
    check("ao restaurar a ficha, nenhuma recarga de item sobrevive (rodada reinicia em 1)",
          marcas(novo) == [])
    check("Manto das Sombras e escudo Retalhação (outros sufixos) também zeram",
          "manto_escuridao_pronto_em" not in novo["gear"]["armor"]
          and "thunder_reaction_active_until" not in novo["gear"]["off_hand"])
    check("o item continua equipado e com suas regras",
          novo["gear"]["weapon"].get("solar_flare") is True
          and novo["gear"]["weapon"].get("solar_flare_cooldown") == 10)

    print("\n[2] Descanso na cidade recarrega as armas, como as técnicas")
    src = inspect.getsource(GameRoom._voltar_para_cidade)
    check("_voltar_para_cidade limpa as recargas dos itens",
          "_limpar_recargas_de_itens" in src)

    print("\n[3] O helper só mexe em recarga")
    q = heroi_com_marcas()
    server._limpar_recargas_de_itens(q)
    check("remove as marcas do equipamento, da cópia de combate e da bolsa", marcas(q) == [])
    check("preserva dano, bônus e flags", q["gear"]["weapon"].get("die") == "1d8"
          and q["gear"]["weapon"].get("atk_bonus") == 1)


if __name__ == "__main__":
    main()
    print("\nOK")
