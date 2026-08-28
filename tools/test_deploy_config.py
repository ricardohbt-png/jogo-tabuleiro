"""Configuração de escuta para deploy. Roda da raiz: python tools/test_deploy_config.py"""
import sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    # [1] porta de escuta
    print("\n[1] _listen_port — precedência e sanidade")
    check("sem env nenhuma → 8765 (o padrão do jogo em casa)",
          S._listen_port({}) == 8765)
    check("PORT injetada pela plataforma vale",
          S._listen_port({"PORT": "10000"}) == 10000)
    check("LFH_PORT (testes locais) vale",
          S._listen_port({"LFH_PORT": "9999"}) == 9999)
    check("LFH_PORT vence PORT — teste local não é sequestrado pela plataforma",
          S._listen_port({"LFH_PORT": "9999", "PORT": "10000"}) == 9999)
    check("espaços em volta não quebram",
          S._listen_port({"PORT": "  10000  "}) == 10000)
    check("valor não numérico cai no padrão em vez de estourar",
          S._listen_port({"PORT": "lixo"}) == 8765)
    check("string vazia cai no padrão",
          S._listen_port({"PORT": ""}) == 8765)
    check("porta 0 é recusada",
          S._listen_port({"PORT": "0"}) == 8765)
    check("porta acima de 65535 é recusada",
          S._listen_port({"PORT": "70000"}) == 8765)
    check("PORT inválida não impede LFH_PORT válida de valer",
          S._listen_port({"LFH_PORT": "lixo", "PORT": "10000"}) == 10000)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
