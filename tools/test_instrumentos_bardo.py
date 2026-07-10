"""Testes do sistema de Instrumentos do Bardo — Fase 1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def test_stats_por_qualidade():
    for q, alc, dano in [("velho", 3, "1d4"), ("rustico", 4, "1d6"), ("padrao", 5, "2d6")]:
        inst = server.criar_instrumento("harpa", q)
        st = server.GameRoom._instrumento_stats(inst)
        assert st["alcance"] == alc, (q, st)
        assert st["dano"] == dano, (q, st)
        assert st["custo_fome"] == 3 and st["custo_sede"] == 3, st

def test_refinado_afixo_alcance():
    inst = server.criar_instrumento("harpa", "refinado", refinado_bonus="alcance")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["alcance"] == 6, st
    assert st["dano"] == "2d6", st

def test_refinado_afixo_custo_nunca_negativo():
    inst = server.criar_instrumento("sino", "refinado", refinado_bonus="fome")
    st = server.GameRoom._instrumento_stats(inst)
    assert st["custo_fome"] == 1, st
    assert st["custo_sede"] == 2, st
    # cruza o zero: alaude tem custo_fome 0 → clamp em 0
    inst0 = server.criar_instrumento("alaude", "refinado", refinado_bonus="fome")
    assert server.GameRoom._instrumento_stats(inst0)["custo_fome"] == 0

def test_nome_derivado():
    assert server.criar_instrumento("harpa", "velho")["name"] == "Harpa Velha"
    assert server.criar_instrumento("tambor", "padrao")["name"] == "Tambor de Guerra Padrão"

def test_tipo_item_e_maos():
    inst = server.criar_instrumento("harpa", "padrao")
    assert inst["tipo_item"] == "instrumento"
    assert server.INSTRUMENTOS_BASE["harpa"]["maos"] == 2
    assert server.INSTRUMENTOS_BASE["sino"]["maos"] == 1

if __name__ == "__main__":
    import inspect
    fns = [f for n, f in sorted(globals().items()) if n.startswith("test_") and inspect.isfunction(f)]
    for f in fns:
        f(); print("ok", f.__name__)
    print(f"\n{len(fns)} testes passaram.")
