"""A ponte: as conversas que levam os dois ramos a Graciero. Roda da raiz: python -X utf8 tools/test_elara_ponte.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_riacho as RI
import gerar_elara_gilo as GI

CENA = "taverna"


def sala(cidade, fatos=()):
    r = S.GameRoom("PONTE")
    r.players["p0"] = S.make_player("p0", "H0", "warrior", 0)
    r.host_pid = "p0"; r.phase = "city"; r.world_location = cidade
    r.fatos = set(fatos)

    async def nada(*a, **k): pass
    r.send_to = nada; r.broadcast = nada; r.push_state_or_city = nada
    r._checkpoint_savegame = lambda: None
    return r


def conversas(r):
    cena = r._city_state_payload()["scenes"].get(CENA) or {}
    return {c["id"] for s in cena.get("slots", []) for c in s.get("conversations", [])}


class PonteTests(unittest.TestCase):
    def _confere(self, cidade, cid, fato_requerido):
        self.assertNotIn(cid, conversas(sala(cidade)))
        r = sala(cidade, {fato_requerido})
        self.assertIn(cid, conversas(r))
        asyncio.run(r.handle_scene_npc("p0", CENA, "barman", cid))
        self.assertIn("elara_rumo_graciero", r.fatos)
        self.assertNotIn(cid, conversas(r), "uma vez só")

    def test_riacho(self):
        self._confere("vila_riacho", "elara_riacho_rumo_graciero", RI.F_MOCAS)

    def test_corvin(self):
        self._confere("vila_corvin", "elara_corvin_rumo_graciero", GI.F_PISTA)

    def test_conversas_dos_planos_anteriores_seguem(self):
        self.assertIn("elara_bardo_escoltar", conversas(sala("vila_riacho", {RI.F_POUPADO})))
        self.assertIn("elara_corvin_barman", conversas(sala("vila_corvin", {GI.F_RAMO_B})))

    def test_nada_da_rede_por_nome(self):
        import json
        t = json.dumps([RI.conversas(), GI.conversas()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
