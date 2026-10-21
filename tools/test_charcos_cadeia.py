"""A Maré do Charco como UMA cadeia sem descanso (dados gravados + motor real).

Roda da raiz:  python -X utf8 tools/test_charcos_cadeia.py

REGRA
  • Um só destino (`charcos_mare`) com 5 etapas emendadas; nada se recupera entre elas.
  • Só a 1ª etapa deixa voltar à vila; as outras bloqueiam a saída pela escada.
  • Todas marcam a entrada com poste (pântano/mata não têm escada).
  • O destino some do mapa-múndi quando a cadeia termina.
"""
import asyncio, json, os, sys, unittest
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_campanha_charcos as G


def ler(nome):
    with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
        return json.load(f)


class DadosGravados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.av = ler("world_adventures.json")

    def test_um_destino_e_nenhum_antigo(self):
        ids = [k for k in self.av if k.startswith("charcos_")]
        self.assertEqual(ids, [G.AVENTURA])
        for antigo in G.ANTIGAS:
            self.assertNotIn(antigo, self.av)

    def test_cadeia_de_cinco_etapas(self):
        d = self.av[G.AVENTURA]
        self.assertEqual([e["file"] for e in d["dungeons"]], list(G.ARQUIVOS))
        self.assertEqual([e["encadear"] for e in d["dungeons"]], [True] * 4 + [False])
        self.assertEqual((d["fome"], d["sede"]), (8, 8))
        self.assertTrue(d["ocultar_apos_concluir"])
        self.assertTrue(d["oculto_ate_liberar"])
        self.assertFalse(d["revisitavel"])
        self.assertEqual(d["renome_recompensa"], 5)
        self.assertEqual(d["requisito"]["fato"], G.FATO_GANCHO)

    def test_o_aviso_de_emenda_abre_a_primeira_etapa(self):
        et = self.av[G.AVENTURA]["dungeons"]
        txt = lambda e: " ".join(s["text"] for s in e["intro"]["slides"])
        self.assertIn("se emendam", txt(et[0]))
        self.assertNotIn("se emendam", txt(et[3]))

    def test_so_a_primeira_masmorra_deixa_voltar_e_todas_tem_poste(self):
        for i, arq in enumerate(G.ARQUIVOS):
            d = ler(os.path.join("dungeons", arq))
            ok, msg = S.validar_dungeon(d)
            self.assertTrue(ok, f"{arq}: {msg}")
            self.assertEqual(d["saida_permitida"], i == 0, arq)
            self.assertEqual(d["marcador_entrada"], "poste", arq)

    def test_gerador_e_idempotente_nos_dois_campos(self):
        for arq in G.ARQUIVOS:
            d = ler(os.path.join("dungeons", arq))
            self.assertEqual(G.aplicar_cadeia(d, arq), d, arq)

    def test_conversas_apontam_para_a_cadeia(self):
        cenas = ler("city_scenes.json")
        texto = json.dumps(cenas, ensure_ascii=False)
        for antigo in G.ANTIGAS:
            self.assertNotIn(f'"aventura_id": "{antigo}"', texto)
        zum = next(cv for cs in cenas["vila_dos_charcos"].values() if isinstance(cs, dict)
                   for sl in cs.get("slots", []) for cv in sl.get("conversations", []) if cv.get("id") == "zumbra_ferrao")
        self.assertEqual(zum["requisito"].get("fato"), G.FATO_GANCHO)
        self.assertFalse(zum["requisito"].get("aventura_id"))


class MotorReal(unittest.TestCase):
    def sala(self, fatos=()):
        r = S.GameRoom("CAD"); r.fatos = set(fatos)
        return r

    def test_visibilidade_do_destino(self):
        S.WORLD_ADVENTURES[G.AVENTURA] = ler("world_adventures.json")[G.AVENTURA]
        try:
            r = self.sala()
            adv = S.WORLD_ADVENTURES[G.AVENTURA]
            self.assertFalse(r._aventura_visivel(adv), "oculto até o gancho")
            r.fatos.add(G.FATO_GANCHO)
            self.assertTrue(r._aventura_visivel(adv))
            r.world_adventure_progress[G.AVENTURA] = 4
            self.assertTrue(r._aventura_visivel(adv), "meia cadeia ainda aparece")
            r.world_adventure_progress[G.AVENTURA] = 5
            self.assertFalse(r._aventura_visivel(adv), "concluída a cadeia, some do mapa")
        finally:
            S.WORLD_ADVENTURES.pop(G.AVENTURA, None)

    def test_a_sala_carrega_o_poste_nas_cinco_etapas(self):
        for arq in G.ARQUIVOS:
            r = S.GameRoom("CAD")
            r.load_authored_dungeon(ler(os.path.join("dungeons", arq)))
            self.assertEqual(r.marcador_entrada, "poste", arq)
            self.assertEqual(r._game_state_payload()["marcador_entrada"], "poste", arq)


if __name__ == "__main__":
    unittest.main(verbosity=1)
