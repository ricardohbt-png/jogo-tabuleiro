from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

root = Path(__file__).resolve().parents[1]
decor = server.DECOR_TYPES['mansao_medieval']
assert decor['size'] == [4, 4]
assert decor['gira'] and decor['alto'] and not decor['pisavel']
assert decor['image'] == 'mansao_medieval.png'
assert server.DECOR_MODEL3D['mansao_medieval'] == 'assets/objetos/mansao_medieval.glb'
for p in ('assets/objetos/mansao_medieval.png', 'assets/objetos/mansao_medieval.glb'):
    assert (root / p).is_file(), p
print('Mansão registrada com PNG, GLB, tamanho, giro e bloqueio.')
