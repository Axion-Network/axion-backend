import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import check_snapshot_contract_amounts
from hex2x_backend.snapshot.models import HexUser

if __name__ == '__main__':
    all_users_count = 0
    while all_users_count > 0:
        try:
            all_users = HexUser.objects.filter(tx_checked=False).order_by('id')
            all_users_count = all_users.count()
            check_snapshot_contract_amounts(all_users)
        except Exception as e:
            print('process exited with error:', e, flush=True)
            print('restarting', flush=True)
