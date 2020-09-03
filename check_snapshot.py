import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import check_snapshot_contract_amounts
from hex2x_backend.snapshot.models import HexUser

if __name__ == '__main__':
    all_users = HexUser.objects.filter(tx_checked=False).order_by('id')
    while all_users.count() > 0:
        check_snapshot_contract_amounts(all_users)
