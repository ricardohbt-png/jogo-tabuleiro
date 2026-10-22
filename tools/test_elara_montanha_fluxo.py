"""Fluxo da rota do Olho pelo motor real: visibilidade, falas por via, objetivos, fuga do assassino e o Olho.
Roda da raiz: python -X utf8 tools/test_elara_montanha_fluxo.py"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_montanha as R
import gerar_elara_graciero as GG
import elara_montanha_fichas as F
import elara_montanha_mapas as M

R.garantir_registros(gravar=False)


def sala(fatos=(), classes=("warrior",), cidade="graciero"):
    r = S.GameRoom("MONTANHA")
    for i, c in enumerate(classes):
        r.players[f"p{i}"] = S.make_player(f"p{i}", f"H{i}", c, i)
    r.host_pid = "p0"; r.phase = "city"; r.world_location = cidade
    r.fatos = set(fatos)

    async def nada(*a, **k): pass
    r.send_to = nada; r.broadcast = nada; r.push_state_or_city = nada; r.push_state = nada; r.gm_say = nada
    r._checkpoint_savegame = lambda: None
    return r


def masmorra(arq, fatos=()):
    r = sala(fatos)
    r.load_authored_dungeon(S.carregar_dungeon(arq))
    r.phase = "playing"
    return r


class VisibilidadeTests(unittest.TestCase):
    def setUp(self):
        S.WORLD_ADVENTURES.update(R.destinos())

    def tearDown(self):
        S.WORLD_ADVENTURES.pop("elara_montanha", None)

    def vis(self, fatos, progresso=0):
        r = sala(fatos)
        if progresso:
            r.world_adventure_progress["elara_montanha"] = progresso
        return r._aventura_visivel(S.WORLD_ADVENTURES["elara_montanha"])

    def test_so_ramo_a_com_a_dica(self):
        self.assertFalse(self.vis(set()))
        self.assertFalse(self.vis({"elara_dica_montanha"}), "sem ramo A (ramo B com a Praca viva) nao ve")
        self.assertFalse(self.vis({"elara_ramo_a"}), "sem a dica nao ve")
        self.assertTrue(self.vis({"elara_dica_montanha", "elara_ramo_a"}))

    def test_some_depois_do_leonel_e_depois_de_concluida(self):
        base = {"elara_dica_montanha", "elara_ramo_a"}
        self.assertFalse(self.vis(base | {"elara_leonel_vencido"}))
        self.assertFalse(self.vis(base, progresso=3))


class FalasTests(unittest.TestCase):
    def elegiveis(self, arq, fatos):
        r = masmorra(arq, fatos)
        p = r.players["p0"]
        return {f["id"] for f in r.falas if r._fala_elegivel(p, f)}

    def test_via_do_bardo_e_via_do_gilo(self):
        for arq, guia, sem in (("elara_montanha_1.json", "trilha_guia", "trilha_marcas"),
                               ("elara_montanha_2.json", "desfil_morte", "desfil_rastro")):
            com = self.elegiveis(arq, {"elara_bardo_ajudou"})
            ausente = self.elegiveis(arq, set())
            self.assertIn(guia, com); self.assertNotIn(sem, com)
            self.assertIn(sem, ausente); self.assertNotIn(guia, ausente)
        self.assertIn("carav_guia", self.elegiveis("elara_montanha_3.json", {"elara_bardo_ajudou"}))
        self.assertNotIn("carav_guia", self.elegiveis("elara_montanha_3.json", set()))

    def test_falas_comuns_sempre(self):
        for arq, fid in (("elara_montanha_1.json", "trilha_chegada"), ("elara_montanha_2.json", "desfil_chegada"),
                         ("elara_montanha_3.json", "carav_bau")):
            for fatos in (set(), {"elara_bardo_ajudou"}):
                self.assertIn(fid, self.elegiveis(arq, fatos))


class ObjetivosTests(unittest.IsolatedAsyncioTestCase):
    async def test_trilha_e_desfiladeiro_gravam_ao_chegar_na_saida(self):
        for arq, fato in (("elara_montanha_1.json", M.F_TRILHA), ("elara_montanha_2.json", M.F_DESFILADEIRO)):
            r = masmorra(arq)
            r.players["p0"]["pos"] = list(r.exit_pos); r.players["p0"]["alive"] = True
            await r._check_objectives()
            self.assertIn(fato, r.fatos, arq)

    async def _caravana(self):
        r = masmorra("elara_montanha_3.json")
        a = next(m for m in r.monsters.values() if m["type"] == F.TIPO_ASSASSINO)
        return r, a, set(r.chests)

    async def _conclui(self, r, a, baus0):
        self.assertTrue(a.get("fugiu"))
        self.assertIn(M.F_ASSASSINO_FUGIU, r.fatos)
        self.assertNotIn(a["id"], r.corpses)
        await r._check_objectives()
        self.assertTrue({M.F_ROTA, M.F_OLHO} <= r.fatos)
        novos = [r.chests[i] for i in set(r.chests) - baus0]
        ids = [it.get("id") for b in novos for it in (b.get("items") or [])]
        self.assertIn("olho_de_arveluz", ids)

    async def test_assassino_foge_por_arma(self):
        r, a, baus0 = await self._caravana()
        a["hp"] = 0
        await r._monster_dies(a, "p0")
        await self._conclui(r, a, baus0)

    async def test_assassino_foge_por_fogo_e_por_veneno(self):
        r, a, baus0 = await self._caravana()
        await r._aplicar_dano_alvo(a, a["hp"] + 5, "fire", killer_pid="p0")
        await self._conclui(r, a, baus0)
        r2, a2, _ = await self._caravana()
        await r2._dano_em_alvo(a2, a2["hp"] + 5, "poison", killer_pid="p0")
        self.assertTrue(a2.get("fugiu"))

    async def test_sem_vencer_o_assassino_nao_ha_olho_nem_fatos(self):
        r, a, baus0 = await self._caravana()
        await r._check_objectives()
        self.assertFalse(r.fatos & {M.F_ROTA, M.F_OLHO})
        self.assertEqual(set(r.chests), baus0)


class FinalComRotaTests(unittest.TestCase):
    def texto(self, com_olho):
        r = sala({"elara_ramo_a", "elara_mocas_salvas"})
        if com_olho:
            r.players["p0"]["bag"].append(dict(S._DUNGEON_ITEM_CATALOG["olho_de_arveluz"]))
        b = S._story_beat("fim:x", [GG.outro_rota()], r._requisito_do_slide)
        return " || ".join(sl.get("text", "") for sl in b["slides"])

    def test_com_a_rota_o_olho_volta_ao_templo_sem_ela_nao(self):
        self.assertIn("volta ao Templo", self.texto(True))
        self.assertNotIn("não está aqui", self.texto(True))
        self.assertIn("não está aqui", self.texto(False))


if __name__ == "__main__":
    unittest.main()
