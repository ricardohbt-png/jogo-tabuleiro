import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import GameRoom, validar_dungeon
from tools.test_decor_roundtrip import _defn_base

definition = _defn_base()
definition['decorations'] = [
    {'id':'wide', 'type':'caminho_pedras_terra', 'pos':[2,2], 'road_wide':True},
    {'id':'old', 'type':'caminho_pedras_terra', 'pos':[3,2]},
]
ok, reason = validar_dungeon(definition)
assert ok, reason
room = GameRoom('ROAD_TEST')
room.load_authored_dungeon(definition)
payload = {d['id']:d for d in room._serializar_decoracoes()}
assert payload['wide']['road_wide'] is True
assert payload['wide']['pisavel'] is True
assert 'road_wide' not in payload['old']
print('wide road survives dungeon loading and client serialization; legacy path unchanged')
