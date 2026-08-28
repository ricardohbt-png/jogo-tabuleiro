"""Mede o custo de acordar um servidor hospedado. Roda da raiz:

    python tools/medir_cold_start.py wss://SEU-SPIKE.onrender.com

Duas medidas, porque têm causas diferentes:
  conexao_s  tempo até o handshake do WebSocket fechar — INCLUI o cold start
  eco_s      ida e volta de uma mensagem com o servidor já quente — é rede

A sonda é `list_savegames`: sempre responde (`savegames_list`), não exige login
e é estritamente somente-leitura.
"""
import asyncio, json, sys, time
import websockets

SONDA = json.dumps({"type": "list_savegames"})

async def medir(url):
    """Devolve (conexao_s, eco_s, tipo_da_resposta). Levanta em caso de falha."""
    t0 = time.monotonic()
    async with websockets.connect(url, open_timeout=300, ping_interval=None,
                                  max_size=34 * 1024 * 1024) as ws:
        conexao_s = time.monotonic() - t0
        t1 = time.monotonic()
        await ws.send(SONDA)
        bruto = await asyncio.wait_for(ws.recv(), timeout=60)
        eco_s = time.monotonic() - t1
    tipo = json.loads(bruto).get("type", "?")
    return conexao_s, eco_s, tipo

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    url = sys.argv[1]
    print(f"medindo {url}")
    try:
        conexao_s, eco_s, tipo = asyncio.run(medir(url))
    except Exception as e:
        print(f"  FALHOU: {type(e).__name__}: {e}")
        sys.exit(1)
    print(f"  conexao_s = {conexao_s:7.2f}   (inclui cold start)")
    print(f"  eco_s     = {eco_s:7.2f}   (rede, servidor ja quente)")
    print(f"  resposta  = {tipo}")
    if tipo != "savegames_list":
        print("  ATENCAO: resposta inesperada -- a sonda mudou?")
        sys.exit(1)

if __name__ == "__main__":
    main()
