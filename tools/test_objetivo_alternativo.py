"""Conclusão alternativa: com o resgate falho, matar o alvo (Ferrão) encerra a missão com final amargo.
Roda da raiz: python -X utf8 tools/test_objetivo_alternativo.py"""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402

DEFN = {"schema_version": 1, "grid": {"w": 10, "h": 10}, "tiles": [[1] * 10 for _ in range(10)],
        "entrance": {"x": 1, "y": 1},
        "rooms": [{"id": "r1", "role": "entrance", "x": 0, "y": 0, "w": 10, "h": 10}],
        "prisoner": {"pos": [4, 4], "room_id": "r1"},
        "objectives": {
            "primary": {"type": "rescue_prisoner", "xp": 100, "se_falhar": {"renome": -5, "fato": "charcos_criancas_mortas"}},
            "secondary": [{"type": "kill_target", "xp": 60, "reward": {"gold": 40, "items": []}}],
            "alternativo": {"type": "kill_target", "xp": 30, "reward": {"gold": 0, "items": []}, "renome": 1}}}


def sala():
    r = S.GameRoom("ALT")
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.msgs = []

    async def noop(*a, **k): pass

    async def send(pid, m, *a, **k): r.msgs.append(m)
    r.gm_say = noop; r.broadcast = noop; r.send_to = send; r.push_state = noop
    r.load_authored_dungeon(deepcopy(DEFN))
    r.phase = "playing"
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "goblin")
    m = S.make_monster(mdef, r.rooms[0])
    m.update({"id": "ferrao", "pos": [7, 7], "authored_target": True, "room_id": "r1"})
    r.monsters["ferrao"] = m
    r.alvo = m
    r.world_adventure_id = "charcos_aldeia"; r.world_adventure_index = 1
    r.world_adventure_progress = {}
    return r


def checar(r): asyncio.run(r._check_objectives())
def morrer_refem(r): asyncio.run(r._prisioneiro_morre())
def matar(r): r.alvo["hp"] = 0


class AlternativoTests(unittest.TestCase):
    def test_sem_falha_usa_o_principal(self):
        r = sala(); checar(r)
        self.assertEqual(r._objetivo_principal_efetivo()["type"], "rescue_prisoner")
        self.assertEqual(r.objective_status["alternativo"]["status"], "pending")
        self.assertEqual(r.objective_status["primary"]["status"], "pending")

    def test_falha_ativa_o_alternativo(self):
        r = sala(); morrer_refem(r); checar(r)
        self.assertEqual(r.objective_status["primary"]["status"], "failed")
        self.assertEqual(r.objective_status["alternativo"]["status"], "pending")
        self.assertEqual(r._objetivo_principal_efetivo()["type"], "kill_target")
        self.assertFalse(r.mission_complete_pending)

    def test_matar_o_alvo_habilita_encerrar_missao_com_xp_reduzido(self):
        r = sala(); morrer_refem(r); checar(r)
        xp0 = r.players["p1"]["xp"]
        matar(r); checar(r)
        self.assertTrue(r.mission_complete_pending)
        self.assertEqual(r.players["p1"]["xp"] - xp0, 30, "só o XP do alternativo")

    def test_nao_paga_o_bonus_secundario_em_dobro(self):
        r = sala(); morrer_refem(r); checar(r)
        ouro0 = r.players["p1"].get("gold", 0)
        matar(r); checar(r)
        self.assertEqual(r.players["p1"].get("gold", 0), ouro0, "o secundário kill_target não paga junto")

    def test_nao_paga_renome_da_rota_no_final_amargo(self):
        r = sala(); r.renome = 10
        S.WORLD_ADVENTURES["charcos_aldeia"] = {"id": "charcos_aldeia", "nome": "x", "renome_recompensa": 4,
                                                "dungeons": ["a.json", "b.json"]}
        try:
            morrer_refem(r); checar(r)          # -5
            matar(r); checar(r)                 # +1 do alternativo
            antes = r.renome

            async def go():
                async def volta(*a, **k): pass
                r._voltar_para_cidade = volta
                await r.handle_encerrar_missao("p1")
            asyncio.run(go())
            self.assertEqual(r.renome, antes, "final amargo não soma renome da rota")
        finally:
            S.WORLD_ADVENTURES.pop("charcos_aldeia", None)

    def test_refem_morre_com_o_alvo_ja_morto_conclui_na_hora(self):
        r = sala(); matar(r); checar(r)         # principal ainda pendente; secundário pago
        morrer_refem(r); checar(r)
        self.assertTrue(r.mission_complete_pending)

    def test_fugir_pela_escada_nao_conclui(self):
        r = sala(); morrer_refem(r); checar(r)
        self.assertFalse(r._objetivo_concluido)
        self.assertEqual(r.world_adventure_progress.get("charcos_aldeia", 0), 0)
        self.assertIn("charcos_criancas_mortas", r.fatos)

    def test_slides_do_final_pelo_marcador(self):
        r = sala(); morrer_refem(r)
        slides = [{"text": "amargo", "requisito": {"fato": "charcos_criancas_mortas"}},
                  {"text": "doce", "requisito": {"sem_fato": "charcos_criancas_mortas"}}]
        beat = S._story_beat("fim:x", [{"slides": slides}], r._requisito_do_slide)
        self.assertEqual([s["text"] for s in beat["slides"]], ["amargo"])

    def test_grupo_todo_fora_nao_trava(self):
        r = sala(); morrer_refem(r)
        r.players["p1"]["fora_masmorra"] = {"rodadas_restantes": 2}
        matar(r); checar(r)
        self.assertTrue(r._objetivo_concluido)


if __name__ == "__main__":
    unittest.main()
