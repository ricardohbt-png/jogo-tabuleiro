"""Fluxo do Ramo A pelo motor real: sondagem, tratamento, confronto, ações finais e destinos.
Roda da raiz: python -X utf8 tools/test_elara_riacho_fluxo.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_riacho as R

CENA = "taverna"


def sala(fatos=(), classes=("warrior",)):
    r = S.GameRoom("RIACHO")
    for i, c in enumerate(classes):
        r.players[f"p{i}"] = S.make_player(f"p{i}", f"H{i}", c, i)
    r.host_pid = "p0"; r.phase = "city"; r.world_location = "vila_riacho"
    r.fatos = set(fatos)
    r.enviados = []

    async def send_to(pid, msg): r.enviados.append(msg)

    async def broadcast(msg, skip=None, personalize=None): pass

    async def push(): pass
    r.send_to = send_to; r.broadcast = broadcast; r.push_state_or_city = push
    r._checkpoint_savegame = lambda: None
    return r


def conversas(r):
    cena = r._city_state_payload()["scenes"].get(CENA) or {}
    return {c["id"] for s in cena.get("slots", []) for c in s.get("conversations", [])}


def falar(r, cid):
    slot = next(s for s, convs in R.conversas().items() if any(c["id"] == cid for c in convs))
    asyncio.run(r.handle_scene_npc("p0", CENA, slot, cid))


T1 = {"elara_t1_gentil", "elara_t1_ameaca", "elara_t1_ignorou"}
CONFRONTO = {"elara_bardo_matar", "elara_bardo_interrogar", "elara_bardo_poupar"}
FINAIS = {"elara_bardo_escoltar", "elara_bardo_entregar"}


class FluxoTests(unittest.TestCase):
    def test_sem_o_ramo_a_nada_do_riacho_aparece(self):
        vistos = conversas(sala())
        self.assertFalse(vistos & (T1 | CONFRONTO | FINAIS | {"elara_riacho_barman", "elara_riacho_mesa", "elara_riacho_serva"}))

    def test_com_o_ramo_a_aparecem_sondagem_e_tratamento(self):
        vistos = conversas(sala({R.F_RAMO_A}))
        self.assertIn("elara_riacho_barman", vistos)
        self.assertFalse(vistos & (T1 | {"elara_riacho_mesa", "elara_riacho_rua", "elara_riacho_endereco"}),
                         "pistas e bardo só depois de o barman receber o grupo")
        r = sala({R.F_RAMO_A})
        falar(r, "elara_riacho_barman")
        vistos = conversas(r)
        self.assertNotIn("elara_riacho_barman", vistos, "a chegada acontece uma vez")
        self.assertTrue({"elara_riacho_mesa", "elara_riacho_rua"} <= vistos)
        self.assertNotIn("elara_riacho_endereco", vistos, "o endereço só depois das duas pistas")
        self.assertTrue(T1 <= vistos)
        self.assertNotIn("elara_riacho_serva", vistos, "o rumor do celeiro só depois de expor o bardo")
        self.assertFalse(vistos & CONFRONTO)

    def test_escolher_um_tratamento_esconde_os_outros(self):
        r = sala({R.F_RAMO_A, R.F_SONDOU})
        falar(r, "elara_t1_ameaca")
        self.assertTrue({R.F_T1_AMEACA, R.F_T1_FEITO, R.F_MALTRATADO} <= r.fatos)
        self.assertFalse(conversas(r) & T1)

    def test_confronto_so_depois_de_expor_o_bardo_e_esconde_o_resto(self):
        r = sala({R.F_RAMO_A, R.F_EXPOSTO})
        vistos = conversas(r)
        self.assertTrue(CONFRONTO <= vistos and "elara_riacho_dica_bardo" in vistos)
        self.assertNotIn("elara_riacho_serva", vistos, "a pista do celeiro só depois de decidir sobre o bardo")
        falar(r, "elara_riacho_dica_bardo")
        self.assertNotIn("elara_riacho_dica_bardo", conversas(r), "uso único")
        falar(r, "elara_bardo_poupar")
        self.assertNotIn("elara_riacho_dica_bardo", conversas(r))
        self.assertIn("elara_riacho_serva", conversas(r))
        self.assertTrue({R.F_POUPADO, R.F_DECIDIDO} <= r.fatos)
        self.assertFalse(conversas(r) & CONFRONTO, "as três opções somem (a escolhida é de uso único)")

    def test_matar_e_interrogar_gravam_as_consequencias(self):
        r = sala({R.F_RAMO_A, R.F_EXPOSTO})
        falar(r, "elara_bardo_matar")
        self.assertTrue({R.F_MORTO, R.F_LEONEL_CAUTELOSO, R.F_DECIDIDO} <= r.fatos)
        self.assertFalse(conversas(r) & FINAIS, "ações finais são só do poupado")
        r2 = sala({R.F_RAMO_A, R.F_EXPOSTO})
        falar(r2, "elara_bardo_interrogar")
        self.assertTrue({R.F_INTERROGADO, R.F_VILA_ABALADA, R.F_DECIDIDO} <= r2.fatos)

    def test_acoes_finais_do_poupado_sao_exclusivas(self):
        r = sala({R.F_RAMO_A, R.F_EXPOSTO})
        falar(r, "elara_bardo_poupar")
        self.assertEqual(conversas(r) & FINAIS, FINAIS)
        falar(r, "elara_bardo_escoltar")
        self.assertIn(R.F_GENTIL, r.fatos)
        self.assertFalse(conversas(r) & FINAIS)

    def test_a_casa_exige_as_duas_pistas_e_o_endereco(self):
        r = sala({R.F_RAMO_A})
        falar(r, "elara_riacho_barman")
        falar(r, "elara_riacho_mesa")
        self.assertIn(R.F_PISTA_BOLSA, r.fatos)
        self.assertNotIn("elara_riacho_mesa", conversas(r), "a pista se esgota depois de ouvida")
        self.assertNotIn("elara_riacho_endereco", conversas(r), "uma pista só não basta")
        falar(r, "elara_riacho_rua")
        self.assertIn(R.F_PISTA_RUA, r.fatos)
        self.assertNotIn(R.F_CASA_DESCOBERTA, r.fatos)
        self.assertIn("elara_riacho_endereco", conversas(r))
        falar(r, "elara_riacho_endereco")
        self.assertIn(R.F_CASA_DESCOBERTA, r.fatos)
        self.assertNotIn("elara_riacho_endereco", conversas(r), "uso único")

    def test_a_ordem_das_pistas_nao_importa(self):
        r = sala({R.F_RAMO_A})
        falar(r, "elara_riacho_barman")
        falar(r, "elara_riacho_rua")
        falar(r, "elara_riacho_mesa")
        self.assertIn("elara_riacho_endereco", conversas(r))

    def test_ponto_da_casa_so_aparece_depois_do_endereco(self):
        S.WORLD_ADVENTURES.update(R.destinos())
        antes = {k: dict(v) for k, v in S.CITY_MAP_POINTS.get(R.CIDADE, {}).items()}
        S.CITY_MAP_POINTS.setdefault(R.CIDADE, {}).update(R.pontos())
        try:
            r = sala({R.F_RAMO_A, R.F_SONDOU, R.F_PISTA_BOLSA, R.F_PISTA_RUA})
            pontos = lambda: r._city_points_payload().get(R.CIDADE, {})
            self.assertNotIn(R.PONTO_CASA, pontos())
            self.assertNotIn(R.PONTO_CELEIRO, pontos())
            falar(r, "elara_riacho_endereco")
            self.assertIn(R.PONTO_CASA, pontos())
            self.assertNotIn(R.PONTO_CELEIRO, pontos())
            r.world_adventure_progress["elara_riacho_casa"] = 1
            self.assertNotIn(R.PONTO_CASA, pontos(), "concluída, o ponto some")
        finally:
            S.CITY_MAP_POINTS[R.CIDADE] = antes
            for k in R.destinos():
                S.WORLD_ADVENTURES.pop(k, None)

    def test_o_celeiro_exige_a_decisao_e_a_pista_da_servente(self):
        S.WORLD_ADVENTURES.update(R.destinos())
        try:
            celeiro = S.WORLD_ADVENTURES["elara_riacho_celeiro"]
            r = sala({R.F_RAMO_A, R.F_EXPOSTO})
            falar(r, "elara_bardo_poupar")
            self.assertFalse(r._aventura_visivel(celeiro), "decidiu o bardo, mas ainda não ouviu a servente")
            self.assertIn("elara_riacho_serva", conversas(r))
            falar(r, "elara_riacho_serva")
            self.assertNotIn("elara_riacho_serva", conversas(r))
            self.assertIn(R.F_CELEIRO_DESCOBERTO, r.fatos)
            self.assertTrue(r._aventura_visivel(celeiro))
        finally:
            for k in R.destinos():
                S.WORLD_ADVENTURES.pop(k, None)

    def test_destinos_na_ordem_certa(self):
        S.WORLD_ADVENTURES.update(R.destinos())
        try:
            casa, celeiro = S.WORLD_ADVENTURES["elara_riacho_casa"], S.WORLD_ADVENTURES["elara_riacho_celeiro"]
            r = sala()
            self.assertFalse(r._aventura_visivel(casa))
            r.fatos.add(R.F_RAMO_A)
            self.assertFalse(r._aventura_visivel(casa), "o ramo A sozinho não abre a casa: falta a descoberta")
            r.fatos.add(R.F_CASA_DESCOBERTA)
            self.assertTrue(r._aventura_visivel(casa))
            self.assertFalse(r._aventura_visivel(celeiro))
            r.fatos.update({R.F_DECIDIDO, R.F_CELEIRO_DESCOBERTO})
            self.assertTrue(r._aventura_visivel(celeiro))
            r.world_adventure_progress["elara_riacho_casa"] = 1
            self.assertFalse(r._aventura_visivel(casa), "concluída, some do mapa")
        finally:
            for k in R.destinos():
                S.WORLD_ADVENTURES.pop(k, None)

    def test_fatos_viajam_no_save(self):
        r = sala({R.F_RAMO_A, R.F_EXPOSTO})
        falar(r, "elara_bardo_poupar")
        guardados = sorted(r.fatos)
        r2 = sala(set(guardados))
        self.assertFalse(conversas(r2) & CONFRONTO, "recarregar não reoferece o que já foi usado")


if __name__ == "__main__":
    unittest.main()
