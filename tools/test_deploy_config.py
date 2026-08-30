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
    check("LFH_PORT inválida não impede PORT válida de valer",
          S._listen_port({"LFH_PORT": "lixo", "PORT": "10000"}) == 10000)

    # [2] endereços de escuta
    print("\n[2] _listen_hosts — padrão por plataforma e válvula de escape")
    check("padrão liga nas DUAS famílias, em qualquer sistema — o asyncio força "
          "IPV6_V6ONLY, então '::' sozinho RECUSA IPv4 (custou um deploy)",
          S._listen_hosts({}) == ["0.0.0.0", "::"])
    check("não depende mais da plataforma (a distinção era falsa)",
          "plataforma" not in S._listen_hosts.__code__.co_varnames)
    check("LFH_HOSTS sobrepõe o padrão — contêiner sem IPv6",
          S._listen_hosts({"LFH_HOSTS": "0.0.0.0"}) == ["0.0.0.0"])
    check("LFH_HOSTS aceita lista com espaços, preservando a ordem",
          S._listen_hosts({"LFH_HOSTS": "::, 0.0.0.0"}) == ["::", "0.0.0.0"])
    check("LFH_HOSTS só com espaços cai no padrão",
          S._listen_hosts({"LFH_HOSTS": "   "}) == ["0.0.0.0", "::"])
    check("LFH_HOSTS só com vírgulas cai no padrão",
          S._listen_hosts({"LFH_HOSTS": " , , "}) == ["0.0.0.0", "::"])
    check("sem argumento nenhum lê os.environ e devolve lista não vazia",
          isinstance(S._listen_hosts(), list) and len(S._listen_hosts()) >= 1)

    # [3] adaptador de WebSocket
    print("\n[3] _WS — adaptador que isola a biblioteca do resto do código")

    class _FakeMsg:
        def __init__(self, tipo, dado): self.type = tipo; self.data = dado

    class _FakeWS:
        """Dublê do WebSocketResponse do aiohttp."""
        def __init__(self, mensagens): self.enviadas = []; self._msgs = mensagens
        async def send_str(self, texto): self.enviadas.append(texto)
        def __aiter__(self):
            async def gen():
                for m in self._msgs: yield m
            return gen()

    import asyncio as _aio
    from aiohttp import WSMsgType as _T

    falso = _FakeWS([_FakeMsg(_T.TEXT, '{"a":1}'),
                     _FakeMsg(_T.BINARY, b'\x00'),
                     _FakeMsg(_T.TEXT, '{"b":2}')])
    ad = S._WS(falso)

    _aio.run(ad.send("ola"))
    check("send() delega para send_str() do aiohttp",
          falso.enviadas == ["ola"])

    async def _colher():
        return [raw async for raw in ad]
    colhido = _aio.run(_colher())
    check("itera devolvendo o TEXTO das mensagens (o que o laço do jogo espera)",
          colhido == ['{"a":1}', '{"b":2}'])
    check("mensagem BINARY é ignorada — o cliente só manda texto",
          b'\x00' not in colhido)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
