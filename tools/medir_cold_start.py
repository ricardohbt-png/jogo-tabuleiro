"""Mede o custo de acordar um servidor hospedado. Roda da raiz:

    python tools/medir_cold_start.py wss://SEU-SPIKE.onrender.com

Mede DUAS conexoes seguidas, e nao uma. Uma conexao sozinha nao diz se o
servico estava dormindo: contra um servico ja acordado o numero sai baixo e
parecido com o de um cold start que nao aconteceu -- registrar "cold start =
0,3 s" e concluir que a hibernacao nao e problema seria o erro mais facil de
cometer aqui. Com duas, a 2a e o piso quente do MESMO servico, e a diferenca e
o cold start de verdade. Diferenca perto de zero significa que ele nao estava
dormindo: espere mais de 15 min sem nenhum trafego e meca de novo.

  1a conexao  handshake completo; inclui o cold start SE estava dormindo
  2a conexao  o mesmo, com o servico comprovadamente acordado
  cold start  a diferenca entre as duas
  eco         ida e volta da sonda (rede + o I/O de disco que a sonda provoca
              no servidor; num conteiner recem-acordado o cache esta frio)

A sonda e `list_savegames`. Ela responde sempre (`savegames_list`) e nao exige
login. Sem conta autenticada ela e somente-leitura, porque `list_savegames`
retorna cedo quando nao ha usuario -- mas a funcao NAO e inocua em geral: numa
sessao logada ela pode gravar, migrando o schema de um savegame antigo. Nao
reuse esta sonda autenticado achando que nao escreve nada.
"""
import asyncio, json, sys, time
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import websockets

SONDA = json.dumps({"type": "list_savegames"})
TENTATIVAS = 4          # bordas de PaaS recusam o upgrade enquanto a instancia sobe
ESPERA_ENTRE = 5.0      # segundos


async def medir_conexao(url, tentativas=TENTATIVAS):
    """Uma medida. Devolve (conexao_s, eco_s, tipo_da_resposta, tentativas_gastas).

    O cronometro comeca na PRIMEIRA tentativa e atravessa as recusas. Algumas
    bordas de PaaS devolvem 502/503 ao upgrade de WebSocket enquanto a instancia
    ainda sobe, em vez de segurar a requisicao -- e essa espera faz parte do
    custo de acordar. Reiniciar o cronometro a cada tentativa mediria so o
    ultimo pedaco, e desistir na primeira recusa queimaria o ciclo de
    hibernacao sem produzir dado (recuperar a janela custa outros 15 min).
    """
    t0 = time.monotonic()
    for tentativa in range(1, tentativas + 1):
        try:
            async with websockets.connect(url, open_timeout=300, ping_interval=None,
                                          max_size=34 * 1024 * 1024) as ws:
                conexao_s = time.monotonic() - t0
                t1 = time.monotonic()
                await ws.send(SONDA)
                bruto = await asyncio.wait_for(ws.recv(), timeout=60)
                eco_s = time.monotonic() - t1
            return conexao_s, eco_s, json.loads(bruto).get("type", "?"), tentativa
        except Exception as e:
            if tentativa == tentativas:
                raise
            print(f"  tentativa {tentativa} recusada ({type(e).__name__}), "
                  f"repetindo em {ESPERA_ENTRE:.0f}s -- o cronometro segue correndo")
            await asyncio.sleep(ESPERA_ENTRE)


async def medir_par(url):
    fria = await medir_conexao(url)
    quente = await medir_conexao(url)
    return fria, quente


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    url = sys.argv[1]
    print(f"medindo {url}")
    try:
        (c1, eco1, tipo1, t1), (c2, eco2, tipo2, t2) = asyncio.run(medir_par(url))
    except Exception as e:
        print(f"  FALHOU: {type(e).__name__}: {e}")
        sys.exit(1)

    cold = c1 - c2
    print(f"  1a conexao  = {c1:8.2f} s   (inclui o cold start, se estava dormindo)")
    print(f"  2a conexao  = {c2:8.2f} s   (piso quente do mesmo servico)")
    print(f"  cold start  = {cold:8.2f} s   (a diferenca)")
    print(f"  eco         = {eco1 * 1000:8.0f} ms  (1a)   {eco2 * 1000:.0f} ms (2a)")
    print(f"  resposta    = {tipo1}")
    if t1 > 1 or t2 > 1:
        print(f"  tentativas  = {t1} na 1a, {t2} na 2a (a borda recusou o upgrade)")

    if tipo1 != "savegames_list" or tipo2 != "savegames_list":
        print("  ATENCAO: resposta inesperada -- a sonda mudou?")
        sys.exit(1)
    if cold < 1.0:
        print("  ATENCAO: cold start perto de zero -- o servico NAO estava dormindo.")
        print("           Deixe mais de 15 min sem nenhum trafego (nem abrir a URL")
        print("           no navegador, que ja acorda) e meca de novo.")


if __name__ == "__main__":
    main()
