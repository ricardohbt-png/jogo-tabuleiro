"""Aventura do mapa-múndi sobrevive à retomada da masmorra.

Roda da raiz:  python tools/test_aventura_retomada.py

O bug: `world_adventure_id`/`_index`/`_revisit` só existiam na sala. Depois de
"Salvar e sair" → Continuar dentro de uma etapa, eles voltavam como None e
"Encerrar missão" na última etapa caía no ramo antigo — `end_game(victory=True)`
— em vez de mostrar o fim da rota e voltar à cidade.

  [1] Os três campos estão na foto.
  [2] Foto nova: a retomada devolve a aventura.
  [3] Foto antiga (sem os campos): a aventura é deduzida pelo arquivo.
  [4] Encerrar a última etapa depois da retomada volta à cidade com o fim da rota.
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))

AVENTURA = "teste_rota"
S.WORLD_ADVENTURES[AVENTURA] = {
    "id": AVENTURA, "nome": "Rota de Teste", "renome_recompensa": 2,
    "dungeons": [{"file": "teste_a.json", "encadear": True},
                 {"file": "teste_b.json", "encadear": False,
                  "outro": {"slides": [{"text": "fim da etapa"}]}}],
    "outro_rota": {"slides": [{"text": "Parabéns, heróis!"}]},
}


def sala_retomada(campos_sala):
    r = S.GameRoom("TST1")
    r.world_adventure_progress = {}
    r._foto_aplicar_sala({"sala": dict(campos_sala), "pids": {}}, {}, None)
    return r


print("\n[1] Os campos da aventura vão na foto")
foto = S.foto_campos_sala("foto")
for campo in ("world_adventure_id", "world_adventure_index", "world_adventure_revisit"):
    check(campo, campo in foto)

print("\n[2] Foto nova devolve a aventura")
r = sala_retomada({"mode": "authored", "selected_dungeon": "teste_b.json",
                   "world_adventure_id": AVENTURA, "world_adventure_index": 1,
                   "world_adventure_revisit": False})
check("id", r.world_adventure_id == AVENTURA, repr(r.world_adventure_id))
check("índice", r.world_adventure_index == 1)

print("\n[3] Foto antiga: deduz pelo arquivo da masmorra")
r = sala_retomada({"mode": "authored", "selected_dungeon": "teste_b.json"})
check("id deduzido", r.world_adventure_id == AVENTURA, repr(r.world_adventure_id))
check("índice deduzido", r.world_adventure_index == 1, repr(r.world_adventure_index))
check("não é revisita", r.world_adventure_revisit is False)
r = sala_retomada({"mode": "authored", "selected_dungeon": "fora_de_aventura.json"})
check("masmorra avulsa segue sem aventura", r.world_adventure_id is None)
r = sala_retomada({"mode": "procedural", "selected_dungeon": None})
check("procedural segue sem aventura", r.world_adventure_id is None)


print("\n[4] Encerrar a última etapa após retomar volta à cidade")
async def encerrar():
    r = sala_retomada({"mode": "authored", "selected_dungeon": "teste_b.json"})
    r.players = {"p1": {"name": "Ana", "alive": True}}
    r.phase = "playing"
    r.mission_complete_pending = True
    r.renome = 0
    chamadas = {}
    async def nada(*a, **k): pass
    async def voltar(story=None): chamadas["cidade"] = story
    async def fim(victory, story=None): chamadas["fim"] = victory
    r.gm_say = nada
    r._progredir_maldicoes_missao = nada
    r._trigger_campaign_scene = nada
    r._voltar_para_cidade = voltar
    r.end_game = fim
    await r.handle_encerrar_missao("p1")
    return r, chamadas

r, ch = asyncio.run(encerrar())
check("não encerra o jogo", "fim" not in ch, repr(ch))
check("volta à cidade", "cidade" in ch)
textos = [s.get("text") for s in ((ch.get("cidade") or {}).get("slides") or [])]
check("com o encerramento da etapa e o fim da rota", textos == ["fim da etapa", "Parabéns, heróis!"], repr(textos))
check("rota marcada como concluída", r.world_adventure_progress.get(AVENTURA) == 2)
check("renome concedido", r.renome == 2)

print(f"\n{PASS} ok, {FAIL} falha(s)")
sys.exit(1 if FAIL else 0)
