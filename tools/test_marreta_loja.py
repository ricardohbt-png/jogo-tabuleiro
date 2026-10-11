"""A Marreta e a variante de prata chegam ao estoque do ferreiro."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

ids = {item['id'] for item in S._city_shop_items('alva_e_luz', 'ferreiro_weapon')}
assert {'marreta', 'marreta_prata'} <= ids, ids
for item_id in ('marreta', 'marreta_prata'):
    item = next(i for i in S._city_shop_items('alva_e_luz', 'ferreiro_weapon') if i['id'] == item_id)
    assert item['allowed_classes'] == ['paladin', 'warrior']
    assert item['die'] == '2d8'
    assert item['two_handed'] is True
assert next(i for i in S.SHOP_WEAPONS if i['id'] == 'marreta_prata')['silver'] is True
print('OK: Marreta e Marreta de Prata aparecem no ferreiro de Alva e Luz.')
