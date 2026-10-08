"""Fatia 10: a placa da sala do herói fica em evidência até as lições de habilidade da classe."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))
import server as S
from test_tutorial_salas import room, D
from test_tutorial_fatia8 import com_estado_real


def placa_do_estado(r, cls):
    est = [m for m in r.messages if m.get("type") == "game_state"][-1]
    return ((est.get("tutorial") or {}).get("por_classe", {}).get(cls) or {}).get("placa")


def lic_habilidade(r, cls):
    return [l["id"] for l in r.licoes if l.get("classe") == cls and l["id"].startswith("treino_")
            and "guia_modelo" not in l]


class PlacaEmEvidenciaTests(unittest.IsolatedAsyncioTestCase):
    async def test_cada_classe_ve_a_propria_placa_ate_cumprir(self):
        for cls in ("warrior", "paladin", "mage"):
            r, p = room(cls)
            com_estado_real(r)
            ids = lic_habilidade(r, cls)
            self.assertTrue(ids, cls)
            decor = next(d for d in r.decorations if d["id"] == "placa_" + cls)
            await r.push_state()
            pl = placa_do_estado(r, cls)
            self.assertEqual(pl, {"id": "placa_" + cls, "pos": list(decor["pos"])}, cls)
            # cumpriu todas menos a última: ainda acesa
            p["licoes_feitas"] = ids[:-1]
            r.messages.clear(); await r.push_state()
            self.assertIsNotNone(placa_do_estado(r, cls), cls)
            p["licoes_feitas"] = list(ids)
            r.messages.clear(); await r.push_state()
            self.assertIsNone(placa_do_estado(r, cls), cls)

    async def test_pulada_conta_como_cumprida(self):
        r, p = room("warrior"); com_estado_real(r)
        ids = lic_habilidade(r, "warrior")
        p["licoes_feitas"] = list(ids); p["licoes_puladas"] = list(ids)   # pular grava nas duas listas
        await r.push_state()
        self.assertIsNone(placa_do_estado(r, "warrior"))

    async def test_pontes_e_comuns_nao_seguram_a_placa(self):
        r, p = room("warrior"); com_estado_real(r)
        p["licoes_feitas"] = lic_habilidade(r, "warrior")   # sem fala_5/6 nem porta_/volta_
        await r.push_state()
        self.assertIsNone(placa_do_estado(r, "warrior"))

    async def test_repetir_tutorial_acende_de_novo(self):
        r, p = room("warrior"); com_estado_real(r)
        ids = lic_habilidade(r, "warrior")
        p["licoes_feitas"] = list(ids)
        sala = next(x for x in r.rooms if x.get("allowed_class") == "warrior")
        p["pos"] = [sala["x"] + 1, sala["y"] + 1]
        await r.handle_repetir_tutorial(p["id"])
        r.messages.clear(); await r.push_state()
        self.assertIsNotNone(placa_do_estado(r, "warrior"))

    async def test_sem_placa_no_mapa_nao_quebra(self):
        r, p = room("warrior"); com_estado_real(r)
        r.decorations = [d for d in r.decorations if d["id"] != "placa_warrior"]
        await r.push_state()
        self.assertIsNone(placa_do_estado(r, "warrior"))

    async def test_fora_do_treinamento_nao_ha_campo(self):
        r, p = room("warrior"); com_estado_real(r)
        r.training_mode = False
        await r.push_state()
        est = [m for m in r.messages if m.get("type") == "game_state"][-1]
        self.assertFalse(((est.get("tutorial") or {}).get("por_classe") or {}).get("warrior", {}).get("placa"))


if __name__ == "__main__":
    unittest.main()
