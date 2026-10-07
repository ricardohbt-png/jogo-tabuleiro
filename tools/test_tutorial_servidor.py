"""Confere a versão em execução pela prévia WebSocket, sem contas ou saves."""
import asyncio
import json
from pathlib import Path
import websockets


async def main():
    definition = json.loads((Path(__file__).resolve().parents[1] /
                             'dungeons/campo_de_treinamento.json').read_text(encoding='utf-8'))
    async with websockets.connect('ws://localhost:8765', max_size=10_000_000) as ws:
        await ws.send(json.dumps({'type': 'preview_dungeon', 'defn': definition}))
        while True:
            result = json.loads(await asyncio.wait_for(ws.recv(), 15))
            if result.get('type') == 'preview_state':
                break
        assert result.get('ok'), result.get('error')
        state = result['state']
        assert len([r for r in state['rooms'] if r.get('allowed_class')]) == 6
        assert state['tutorial']['training'] is True
        allies = [p for p in state['players'] if p.get('training_ally')]
        assert len(allies) == 3
        print('Servidor ativo: seis salas exclusivas, tutorial e três aliados de treino confirmados.')


if __name__ == '__main__':
    asyncio.run(main())
