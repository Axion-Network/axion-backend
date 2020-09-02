import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hex2x_backend.settings')
import django

django.setup()

from hex2x_backend.snapshot.contracts_interaction import check_snapshot_contract_amounts
from hex2x_backend.snapshot.models import HexUser

if __name__ == '__main__':
    # pall_users = HexUser.objects.all().order_by('id')
    start = 65900
    all_users = HexUser.objects.filter(id__gte=start).order_by('id')
    check_snapshot_contract_amounts(all_users)
